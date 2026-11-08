import os
import sys
import json
import time
import hashlib
import secrets
import aiohttp
from pathlib import Path
from typing import Optional, Dict, Any, List

BASE_DIR = Path(__file__).resolve().parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))
DATA_DIR = BASE_DIR / "data"
USERS_FILE = DATA_DIR / "web_users.json"
SESSIONS_FILE = DATA_DIR / "web_sessions.json"

MANAGE_GUILD_BIT = 0x20  
ADMINISTRATOR_BIT = 0x8  

SESSION_TTL = 7 * 24 * 3600  
_sessions_cache: Dict[str, Dict[str, Any]] = {}

def _hash_password(password: str) -> str:
    salt = secrets.token_hex(16)
    h = hashlib.sha256((salt + password).encode()).hexdigest()
    return f"{salt}${h}"

def _verify_password(password: str, stored: str) -> bool:
    try:
        salt, h = stored.split("$", 1)
        check = hashlib.sha256((salt + password).encode()).hexdigest()
        return secrets.compare_digest(check, h)
    except Exception:
        return False

def load_users() -> Dict[str, Any]:
    if not USERS_FILE.exists():
        return {}
    try:
        with open(USERS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}

def save_users(users: Dict[str, Any]) -> bool:
    try:
        USERS_FILE.parent.mkdir(parents=True, exist_ok=True)
        with open(USERS_FILE, "w", encoding="utf-8") as f:
            json.dump(users, f, ensure_ascii=False, indent=2)
        return True
    except Exception as e:
        print(f"[Auth] Lỗi lưu users: {e}")
        return False

def ensure_default_admin():
    # Hệ thống hiện sử dụng xác thực bảo mật Discord OAuth
    return load_users()

def load_sessions() -> Dict[str, Any]:
    global _sessions_cache
    if _sessions_cache:
        return _sessions_cache
    if not SESSIONS_FILE.exists():
        return {}
    try:
        with open(SESSIONS_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
            _sessions_cache = data
            return data
    except Exception:
        return {}

def save_sessions(sessions: Dict[str, Any]):
    global _sessions_cache
    _sessions_cache = sessions
    try:
        SESSIONS_FILE.parent.mkdir(parents=True, exist_ok=True)
        with open(SESSIONS_FILE, "w", encoding="utf-8") as f:
            json.dump(sessions, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"[Auth] Lỗi lưu sessions: {e}")

def create_session(username: str, role: str = "user", discord_id: Optional[str] = None, extra: Dict[str, Any] = None) -> str:
    token = secrets.token_urlsafe(32)
    sessions = load_sessions()
    now = time.time()
    sessions = {k: v for k, v in sessions.items() if v.get("expires_at", 0) > now}
    sessions[token] = {
        "username": username,
        "role": role,
        "discord_id": discord_id,
        "created_at": int(now),
        "expires_at": int(now + SESSION_TTL),
        "extra": extra or {}
    }
    save_sessions(sessions)
    return token

def verify_session(token: str) -> Optional[Dict[str, Any]]:
    if not token:
        return None
    sessions = load_sessions()
    sess = sessions.get(token)
    if not sess:
        return None
    if sess.get("expires_at", 0) < time.time():
        # expired
        sessions.pop(token, None)
        save_sessions(sessions)
        return None
    return sess

def destroy_session(token: str):
    sessions = load_sessions()
    if token in sessions:
        sessions.pop(token)
        save_sessions(sessions)

def register_user(username: str, password: str, discord_id: Optional[str] = None) -> Dict[str, Any]:
    users = load_users()
    if username in users:
        return {"ok": False, "error": "Tên đăng nhập đã tồn tại"}
    if len(username) < 3 or len(password) < 4:
        return {"ok": False, "error": "Username >=3 ký tự, password >=4 ký tự"}
    users[username] = {
        "username": username,
        "password_hash": _hash_password(password),
        "role": "admin" if username == "owner" else "user",
        "discord_id": discord_id,
        "discord_tag": None,
        "avatar": None,
        "created_at": int(time.time()),
        "guilds_filter": None if username == "owner" else []
    }
    save_users(users)
    return {"ok": True}

def authenticate_local(username: str, password: str) -> Optional[Dict[str, Any]]:
    users = load_users()
    u = users.get(username)
    if not u:
        return None
    if not _verify_password(password, u.get("password_hash", "")):
        return None
    return u

def get_discord_oauth_config():
    try:
        import config
        client_id = getattr(config, "DISCORD_CLIENT_ID", "") or os.getenv("DISCORD_CLIENT_ID", "")
        client_secret = getattr(config, "DISCORD_CLIENT_SECRET", "") or os.getenv("DISCORD_CLIENT_SECRET", "")
        return client_id, client_secret
    except Exception:
        return "", ""

async def exchange_code_for_token(code: str, redirect_uri: str) -> Optional[Dict[str, Any]]:
    client_id, client_secret = get_discord_oauth_config()
    if not client_id or not client_secret:
        return {
            "_error": "missing_credentials",
            "_error_description": "Chưa cấu hình DISCORD_CLIENT_ID hoặc DISCORD_CLIENT_SECRET trong config.py"
        }
    data = {
        "client_id": client_id,
        "client_secret": client_secret,
        "grant_type": "authorization_code",
        "code": code,
        "redirect_uri": redirect_uri
    }
    headers = {"Content-Type": "application/x-www-form-urlencoded"}
    try:
        async with aiohttp.ClientSession() as sess:
            async with sess.post("https://discord.com/api/oauth2/token", data=data, headers=headers) as resp:
                if resp.status != 200:
                    txt = await resp.text()
                    print(f"[OAuth] Token exchange failed {resp.status} (redirect_uri='{redirect_uri}'): {txt}")
                    try:
                        err_json = json.loads(txt)
                        return {
                            "_error": err_json.get("error", "http_error"),
                            "_error_description": err_json.get("error_description", txt),
                            "_status": resp.status
                        }
                    except Exception:
                        return {"_error": f"http_{resp.status}", "_error_description": txt, "_status": resp.status}
                return await resp.json()
    except Exception as e:
        print(f"[OAuth] exchange error: {e}")
        return {"_error": "network_error", "_error_description": str(e)}

async def fetch_discord_user(access_token: str) -> Optional[Dict[str, Any]]:
    try:
        async with aiohttp.ClientSession() as sess:
            async with sess.get("https://discord.com/api/users/@me",
                                headers={"Authorization": f"Bearer {access_token}"}) as resp:
                if resp.status != 200:
                    return None
                return await resp.json()
    except Exception as e:
        print(f"[OAuth] fetch user error: {e}")
        return None

async def fetch_discord_user_guilds(access_token: str) -> List[Dict[str, Any]]:
    try:
        async with aiohttp.ClientSession() as sess:
            async with sess.get("https://discord.com/api/users/@me/guilds",
                                headers={"Authorization": f"Bearer {access_token}"}) as resp:
                if resp.status != 200:
                    txt = await resp.text()
                    print(f"[OAuth] guilds fetch {resp.status}: {txt}")
                    return []
                return await resp.json()
    except Exception as e:
        print(f"[OAuth] fetch guilds error: {e}")
        return []

def has_manage_permission(permissions: int) -> bool:
    try:
        perm = int(permissions)
    except Exception:
        return False
    return bool((perm & MANAGE_GUILD_BIT) or (perm & ADMINISTRATOR_BIT))

def filter_manage_guilds(guilds: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    return [g for g in guilds if has_manage_permission(g.get("permissions", 0))]

ensure_default_admin()
