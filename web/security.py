"""
Sakura Security — hardening cho không gian mạng
- Rate limiter per-IP + per-endpoint (in-memory, trượt cửa sổ)
- Security headers middleware
- Input sanitizers, XSS escape, file validation
- Brute-force lockout cho login
"""
import time
import re
import html
from collections import defaultdict, deque
from pathlib import Path
from aiohttp import web

class RateLimiter:
    def __init__(self):
        self.buckets = defaultdict(deque)
        self.lockouts = {}

    def is_limited(self, key: str, limit: int, window: int):
        now = time.time()
        unlock = self.lockouts.get(key)
        if unlock and now < unlock:
            return True, int(unlock - now)
        dq = self.buckets[key]
        while dq and now - dq[0] > window:
            dq.popleft()
        if len(dq) >= limit:
            return True, int(window - (now - dq[0])) + 1
        dq.append(now)
        return False, 0

    def lock(self, key: str, seconds: int):
        self.lockouts[key] = time.time() + seconds

limiter = RateLimiter()

LIMITS = {
    "login": (5, 60),
    "chat": (20, 60),
    "global": (15, 60),
    "game_score": (30, 60),
    "default": (60, 60),
}

def check_rate(request: web.Request, name: str = "default"):
    ip = request.headers.get("X-Forwarded-For", request.remote or "0.0.0.0").split(",")[0].strip()
    key = f"{name}:{ip}"
    limit, window = LIMITS.get(name, LIMITS["default"])
    limited, retry = limiter.is_limited(key, limit, window)
    return limited, retry, key

SECURITY_HEADERS = {
    "X-Frame-Options": "DENY",
    "X-Content-Type-Options": "nosniff",
    "X-XSS-Protection": "1; mode=block",
    "Referrer-Policy": "strict-origin-when-cross-origin",
    "Permissions-Policy": "camera=(), microphone=(), geolocation=()",
    "Content-Security-Policy": "default-src 'self'; script-src 'self' 'unsafe-inline' https://cdnjs.cloudflare.com https://cdn.jsdelivr.net; style-src 'self' 'unsafe-inline' https://fonts.googleapis.com; font-src https://fonts.gstatic.com; img-src 'self' data: https: https://cdn.discordapp.com https://mc-heads.net; connect-src 'self' wss: https://api.groq.com; frame-src https://www.youtube.com https://www.youtube-nocookie.com",
}

@web.middleware
async def security_headers_middleware(request, handler):
    if request.content_length and request.content_length > 6 * 1024 * 1024:
        return web.json_response({"ok": False, "error": "Payload quá lớn (>6MB)"}, status=413)
    try:
        host = request.headers.get("Host","")
    except: pass
    resp = await handler(request)
    for k,v in SECURITY_HEADERS.items():
        resp.headers.setdefault(k, v)
    return resp

def sanitize_text(s: str, max_len: int = 500) -> str:
    if not isinstance(s, str): s = str(s)
    s = s.strip()[:max_len]
    s = re.sub(r"[\x00-\x08\x0B\x0C\x0E-\x1F]", "", s)
    return s

def sanitize_html(s: str) -> str:
    return html.escape(s)

def is_valid_prefix(p: str) -> bool:
    return 1 <= len(p) <= 5 and re.match(r"^[!@#$%^&*?/\\+\-_=~.]+$", p) is not None or p in ["s!","!","?",".",","]

ALLOWED_EXT = {".png",".jpg",".jpeg",".gif",".webp"}
ALLOWED_MIME = {"image/png","image/jpeg","image/gif","image/webp"}

def validate_avatar(filename: str, content_type: str, size: int) -> str:
    ext = Path(filename).suffix.lower()
    if ext not in ALLOWED_EXT:
        return "Chỉ hỗ trợ png/jpg/jpeg/gif/webp"
    if content_type and content_type not in ALLOWED_MIME and not content_type.startswith("image/"):
        return "MIME không hợp lệ"
    if size > 5*1024*1024:
        return "File quá lớn (>5MB)"
    if ".." in filename or "/" in filename or "\\" in filename:
        return "Tên file không hợp lệ"
    return ""

failed_logins = defaultdict(lambda: {"count":0, "first":0})

def record_failed(ip: str):
    now=time.time()
    rec=failed_logins[ip]
    if now - rec["first"] > 600:
        rec["count"]=1; rec["first"]=now
    else:
        rec["count"]+=1
    if rec["count"] >= 5:
        limiter.lock(f"login:{ip}", 300)
        return True
    return False

def clear_failed(ip: str):
    failed_logins.pop(ip, None)
