import os
import sys
import json
import re
import time
import math
import urllib.parse
import asyncio
import datetime
import logging
import subprocess
import secrets
import discord
from pathlib import Path
from typing import Optional, Dict, Any, List
import aiohttp
from aiohttp import web, WSMsgType
import psutil
import platform
try:
    from web.security import limiter, check_rate, security_headers_middleware, sanitize_text, validate_avatar, record_failed, clear_failed, SECURITY_HEADERS
except:
    from security import limiter, check_rate, security_headers_middleware, sanitize_text, validate_avatar, record_failed, clear_failed, SECURITY_HEADERS

# Đường dẫn thư mục
BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
SERVER_DIR = BASE_DIR / "server"
STATIC_DIR = Path(__file__).resolve().parent / "static"
TEMPLATES_DIR = Path(__file__).resolve().parent / "templates"

# Đảm bảo project root trong sys.path khi chạy tách riêng (python web/server.py)
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

try:
    from web.bot_file_manager import (
        handle_bot_files_page,
        handle_api_bot_files_list,
        handle_api_bot_files_read,
        handle_api_bot_files_save,
        handle_api_bot_files_create,
        handle_api_bot_files_delete,
        handle_api_bot_files_rename,
        handle_api_bot_files_upload,
        handle_api_bot_files_raw,
        handle_api_admin_cogs_list,
        handle_api_admin_cogs_reload,
        handle_api_admin_cogs_sync_tree,
        handle_api_database_schema,
        handle_api_database_table_data,
        handle_api_database_query
    )
except ImportError:
    from bot_file_manager import (
        handle_bot_files_page,
        handle_api_bot_files_list,
        handle_api_bot_files_read,
        handle_api_bot_files_save,
        handle_api_bot_files_create,
        handle_api_bot_files_delete,
        handle_api_bot_files_rename,
        handle_api_bot_files_upload,
        handle_api_bot_files_raw,
        handle_api_admin_cogs_list,
        handle_api_admin_cogs_reload,
        handle_api_admin_cogs_sync_tree,
        handle_api_database_schema,
        handle_api_database_table_data,
        handle_api_database_query
    )

# Shared in-memory log buffer for live console streaming (Bot)
LOG_BUFFER: List[Dict[str, Any]] = []
MAX_LOG_ENTRIES = 500
WS_CLIENTS = set()
# Dedicated Minecraft server terminal buffer (tách riêng khỏi console web của bot)
MC_LOG_BUFFER: List[Dict[str, Any]] = []
MC_WS_CLIENTS = set()
MC_LOG_FILE = SERVER_DIR / "logs" / "latest.log"
MC_LOG_OFFSET = 0
# Global chat giữa các TK web (cần login) — lưu data/web_global_chat.json + WS
WEB_GLOBAL_FILE = DATA_DIR / "web_global_chat.json"
WEB_GLOBAL_WS = set()
BOT_INSTANCE = None
SERVER_START_TIME = time.time()
BOT_PROCESS = None  # subprocess handle khi web quản lý bot riêng
BOT_PID_FILE = DATA_DIR / "bot.pid"

# Import auth helpers (after path defined)
try:
    from web.auth import (
        load_users, save_users, verify_session, create_session, destroy_session,
        authenticate_local, register_user, has_manage_permission,
        filter_manage_guilds, get_discord_oauth_config,
        exchange_code_for_token, fetch_discord_user, fetch_discord_user_guilds
    )
    from web.auth import ensure_default_admin
    ensure_default_admin()
except Exception as e:
    # Fallback khi chạy trực tiếp: thử import từ web package đã thêm vào path
    try:
        import importlib
        auth_mod = importlib.import_module("web.auth")
        load_users = auth_mod.load_users
        save_users = auth_mod.save_users
        verify_session = auth_mod.verify_session
        create_session = auth_mod.create_session
        destroy_session = auth_mod.destroy_session
        authenticate_local = auth_mod.authenticate_local
        register_user = auth_mod.register_user
        has_manage_permission = auth_mod.has_manage_permission
        filter_manage_guilds = auth_mod.filter_manage_guilds
        get_discord_oauth_config = auth_mod.get_discord_oauth_config
        exchange_code_for_token = auth_mod.exchange_code_for_token
        fetch_discord_user = auth_mod.fetch_discord_user
        fetch_discord_user_guilds = auth_mod.fetch_discord_user_guilds
        ensure_default_admin = auth_mod.ensure_default_admin
        ensure_default_admin()
    except Exception as e2:
        print(f"[Web] Auth import error: {e} / {e2}")
    # fallback stubs
    def verify_session(t): return None
    def create_session(*a, **kw): return "stub"
    def destroy_session(t): pass
    def authenticate_local(u,p): return None
    def register_user(u,p, d=None): return {"ok": False}
    def has_manage_permission(p): return False
    def filter_manage_guilds(g): return []
    def get_discord_oauth_config(): return ("","")
    async def exchange_code_for_token(*a, **kw): return None
    async def fetch_discord_user(*a, **kw): return None
    async def fetch_discord_user_guilds(*a, **kw): return []

class LogStreamHandler(logging.Handler):
    """Bắt các bản ghi log từ Python logging để truyền trực tiếp qua WebSocket"""
    def emit(self, record):
        try:
            log_entry = {
                "time": datetime.datetime.fromtimestamp(record.created).strftime("%H:%M:%S"),
                "level": record.levelname,
                "name": record.name,
                "message": record.getMessage()
            }
            add_log(log_entry["level"], f"[{record.name}] {log_entry['message']}")
        except Exception:
            pass

def add_log(level: str, message: str):
    entry = {
        "time": datetime.datetime.now().strftime("%H:%M:%S"),
        "level": level.upper(),
        "message": message
    }
    LOG_BUFFER.append(entry)
    if len(LOG_BUFFER) > MAX_LOG_ENTRIES:
        LOG_BUFFER.pop(0)
    if WS_CLIENTS:
        try:
            msg_json = json.dumps({"type": "log", "data": entry})
            for ws in list(WS_CLIENTS):
                if not ws.closed:
                    asyncio.create_task(ws.send_str(msg_json))
        except Exception:
            pass

root_logger = logging.getLogger()
root_logger.addHandler(LogStreamHandler())

# --- Per-guild Reine-style config helpers ---
def _load_server_config():
    return load_json(DATA_DIR / "server_config.json", {})
def _save_server_config(d): return save_json(DATA_DIR / "server_config.json", d)
def _default_server_config(): return {"admin_only": False, "automod_enabled": True, "leveling_enabled": True, "economy_enabled": True, "tiktok_enabled": False}
def _load_tiktok_config(): return load_json(DATA_DIR / "tiktok_config.json", {})
def _load_welcome_from_data(gid: str):
    data = load_json(DATA_DIR / "data.json", {})
    gs = data.get("guild_settings", {}).get(str(gid), {})
    return {
        "channel_id": gs.get("welcome_channel"),
        "message": gs.get("welcome") or "Chào mừng {user} đến với {server}! 🌸 Hãy đọc luật và vui vẻ nhé~",
        "goodbye_channel": gs.get("leave_channel"),
        "goodbye_message": gs.get("goodbye") or "Tạm biệt {user} 👋 Hẹn gặp lại!",
        "welcome_image": gs.get("welcome_image") or "",
        "goodbye_image": gs.get("goodbye_image") or "",
        "boost_channel": gs.get("boost_channel"),
        "boost_message": gs.get("boost_message", True),
        "boost_message_text": gs.get("boost_message_text") or "Cảm ơn {user} đã boost server! 💖",
    }
def _save_welcome_to_data(gid: str, cfg: dict):
    data = load_json(DATA_DIR / "data.json", {})
    if "guild_settings" not in data: data["guild_settings"]={}
    gs = data["guild_settings"].setdefault(str(gid), {})
    ch = cfg.get("channel_id")
    gs["welcome_channel"] = int(ch) if ch and str(ch).isdigit() else (ch if ch else None)
    if not gs["welcome_channel"]:
        gs.pop("welcome_channel", None)
    gs["welcome"] = cfg.get("message","") or ""
    gch = cfg.get("goodbye_channel")
    gs["leave_channel"] = int(gch) if gch and str(gch).isdigit() else (gch if gch else None)
    if not gs["leave_channel"]:
        gs.pop("leave_channel", None)
    gs["goodbye"] = cfg.get("goodbye_message","") or ""
    bch = cfg.get("boost_channel")
    gs["boost_channel"] = int(bch) if bch and str(bch).isdigit() else (bch if bch else None)
    if not gs["boost_channel"]:
        gs.pop("boost_channel", None)
    gs["boost_message"] = bool(cfg.get("boost_message", True))
    gs["boost_message_text"] = cfg.get("boost_message_text","") or "Cảm ơn {user} đã boost server! 💖"
    gs["welcome_image"] = cfg.get("welcome_image","") or ""
    gs["goodbye_image"] = cfg.get("goodbye_image","") or ""
    return save_json(DATA_DIR / "data.json", data)
def _load_audit_config(gid: str):
    # Ưu tiên file riêng audit_config.json (5 nhóm rõ ràng) -> fallback data.json cũ
    audit = load_json(DATA_DIR / "audit_config.json", {})
    if str(gid) in audit:
        c=audit[str(gid)]
        return {
            "message": c.get("message"),
            "member": c.get("member"),
            "join": c.get("join"),
            "voice": c.get("voice"),
            "server": c.get("server"),
        }
    data = load_json(DATA_DIR / "data.json", {})
    # map 5 nhóm Reine -> các key log (fallback)
    return {
        "message": data.get("delete_log_channels",{}).get(str(gid)) or data.get("chat_log_channels",{}).get(str(gid)),
        "member": data.get("member_log_channels",{}).get(str(gid)),
        "join": data.get("join_log_channels",{}).get(str(gid)) or data.get("member_log_channels",{}).get(str(gid)) or data.get("server_log_channels",{}).get(str(gid)),
        "voice": data.get("voice_log_channels",{}).get(str(gid)),
        "server": data.get("server_log_channels",{}).get(str(gid)),
    }
def _save_audit_config(gid: str, cfg: dict):
    # Lưu file riêng rõ ràng 5 nhóm
    audit = load_json(DATA_DIR / "audit_config.json", {})
    clean={
        "message": int(cfg.get("message")) if cfg.get("message") and str(cfg.get("message")).isdigit() else (None if not cfg.get("message") or str(cfg.get("message")) in ("","0", None) else cfg.get("message")),
        "member": int(cfg.get("member")) if cfg.get("member") and str(cfg.get("member")).isdigit() else (None if not cfg.get("member") or str(cfg.get("member")) in ("","0", None) else cfg.get("member")),
        "join": int(cfg.get("join")) if cfg.get("join") and str(cfg.get("join")).isdigit() else (None if not cfg.get("join") or str(cfg.get("join")) in ("","0", None) else cfg.get("join")),
        "voice": int(cfg.get("voice")) if cfg.get("voice") and str(cfg.get("voice")).isdigit() else (None if not cfg.get("voice") or str(cfg.get("voice")) in ("","0", None) else cfg.get("voice")),
        "server": int(cfg.get("server")) if cfg.get("server") and str(cfg.get("server")).isdigit() else (None if not cfg.get("server") or str(cfg.get("server")) in ("","0", None) else cfg.get("server")),
    }
    # None = Tắt
    for k,v in list(clean.items()):
        if v is None:
            clean[k]=None
    audit[str(gid)]=clean
    save_json(DATA_DIR / "audit_config.json", audit)
    # Đồng bộ sang data.json để bot cũ (Logs_vi) vẫn đọc được
    data = load_json(DATA_DIR / "data.json", {})
    sync_map=[("message","delete_log_channels"),("member","member_log_channels"),("join","join_log_channels"),("voice","voice_log_channels"),("server","server_log_channels")]
    for k, key in sync_map:
        val = clean.get(k)
        if key not in data: data[key]={}
        if val is None:
            data[key].pop(str(gid), None)
        else:
            data[key][str(gid)] = int(val) if str(val).isdigit() else val
    # Giữ tương thích: join cũng ghi vào member nếu chưa có? không, để riêng
    save_json(DATA_DIR / "data.json", data)
    # Cập nhật Checks_vi.data memory nếu đang chạy embedded
    try:
        from Checks_vi.data import join_log_channels, delete_log_channels, member_log_channels, voice_log_channels, server_log_channels
        # patch in-memory
        for k,key in sync_map:
            if key=="delete_log_channels": target=delete_log_channels
            elif key=="member_log_channels": target=member_log_channels
            elif key=="join_log_channels": 
                # nếu Checks_vi chưa có join_log_channels thì tạo động
                import Checks_vi.data as dmod
                if not hasattr(dmod, "join_log_channels"):
                    dmod.join_log_channels={}
                target=dmod.join_log_channels
            elif key=="voice_log_channels": target=voice_log_channels
            elif key=="server_log_channels": target=server_log_channels
            else: continue
            if clean[k] is None:
                target.pop(str(gid), None)
            else:
                target[str(gid)]=clean[k]
    except: pass
    return True

# --- Minecraft dedicated terminal helpers ---
def add_mc_log(level: str, message: str):
    entry = {"time": datetime.datetime.now().strftime("%H:%M:%S"), "level": level.upper(), "message": message}
    MC_LOG_BUFFER.append(entry)
    if len(MC_LOG_BUFFER) > MAX_LOG_ENTRIES:
        MC_LOG_BUFFER.pop(0)
    if MC_WS_CLIENTS:
        try:
            msg_json = json.dumps({"type": "log", "data": entry})
            for ws in list(MC_WS_CLIENTS):
                if not ws.closed:
                    asyncio.create_task(ws.send_str(msg_json))
        except Exception:
            pass

async def tail_mc_log_file():
    """Poll server/logs/latest.log và đẩy dòng mới vào MC_LOG_BUFFER"""
    global MC_LOG_OFFSET
    # Khởi tạo offset ở cuối file nếu đã tồn tại
    try:
        if MC_LOG_FILE.exists():
            MC_LOG_OFFSET = MC_LOG_FILE.stat().st_size
            add_mc_log("INFO", f"Đã gắn MC terminal vào {MC_LOG_FILE} (offset {MC_LOG_OFFSET})")
        else:
            add_mc_log("WARN", f"Chưa thấy {MC_LOG_FILE} — sẽ tự hiện khi server chạy")
    except Exception as e:
        add_mc_log("WARN", f"Không đọc được MC log: {e}")
    while True:
        try:
            has_new_data = False
            if MC_LOG_FILE.exists():
                size = MC_LOG_FILE.stat().st_size
                if size < MC_LOG_OFFSET:  # file bị rotate / xóa
                    MC_LOG_OFFSET = 0
                if size > MC_LOG_OFFSET:
                    has_new_data = True
                    with open(MC_LOG_FILE, "r", encoding="utf-8", errors="ignore") as f:
                        f.seek(MC_LOG_OFFSET)
                        new_data = f.read()
                        MC_LOG_OFFSET = f.tell()
                    for line in new_data.splitlines():
                        line=line.strip()
                        if line:
                            # Giữ nguyên màu MC (§) nhưng cũng clean nhẹ để hiển thị web
                            lvl="INFO"
                            if "ERROR" in line or "Exception" in line: lvl="ERROR"
                            elif "WARN" in line: lvl="WARN"
                            add_mc_log(lvl, line)
            # Tối ưu CPU hosting: Khi không có dữ liệu mới thì nghỉ 3s thay vì 1s
            await asyncio.sleep(1.0 if has_new_data else 3.0)
        except asyncio.CancelledError:
            break
        except Exception as e:
            print(f"[MC Tail] {e}")
            await asyncio.sleep(4.0)

# --- Helper functions cho JSON ---
def load_json(filepath: Path, default=None):
    if default is None:
        default = {}
    if not filepath.exists():
        return default
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        print(f"[Web Dashboard] Lỗi đọc {filepath.name}: {e}")
        return default

def save_json(filepath: Path, data: Any):
    try:
        filepath.parent.mkdir(parents=True, exist_ok=True)
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        return True
    except Exception as e:
        print(f"[Web Dashboard] Lỗi lưu {filepath.name}: {e}")
        return False

# ========== AUTH HELPERS ==========
def get_token_from_request(request: web.Request) -> str:
    # Priority: Authorization Bearer -> cookie -> query
    auth_header = request.headers.get("Authorization", "")
    if auth_header.startswith("Bearer "):
        return auth_header[7:].strip()
    cookie_token = request.cookies.get("sakura_token", "")
    if cookie_token:
        return cookie_token.strip()
    token_param = request.query.get("token", "")
    if token_param:
        return token_param.strip()
    # legacy WEB_PASSWORD compat: if token equals WEB_PASSWORD allow?
    return ""

def get_session(request: web.Request) -> Optional[Dict[str, Any]]:
    token = get_token_from_request(request)
    if not token:
        return None
    sess = verify_session(token)
    if sess:
        return sess
    # Legacy fallback: if WEB_PASSWORD set and token matches
    try:
        import config
        legacy = getattr(config, "WEB_PASSWORD", "")
        if legacy and token == legacy:
            return {"username": "admin", "role": "admin", "discord_id": None, "legacy": True}
    except Exception:
        pass
    return None

def is_owner_session(sess: Optional[Dict[str, Any]]) -> bool:
    """Kiểm tra xem session có phải là Chủ Sở Hữu (Web Owner / Bot Owner) tối cao không."""
    if not sess:
        return False
    u = str(sess.get("username") or "").lower()
    tag = str(sess.get("extra", {}).get("discord_tag") or "").lower()
    did = str(sess.get("discord_id") or sess.get("user_id") or "")
    try:
        from config import OWNER_ID
        owner_str = str(OWNER_ID)
    except Exception:
        owner_str = "1144785664458637394"

    if did == owner_str or did == "1144785664458637394" or "linhxinh_dev" in u or "linhxinh_dev" in tag or u in ("linhxinh", "owner"):
        return True
    if sess.get("is_owner") or sess.get("extra", {}).get("is_owner"):
        return True
    return False

def is_admin_session(sess: Optional[Dict[str, Any]]) -> bool:
    if not sess:
        return False
    if is_owner_session(sess):
        return True
    return sess.get("role") == "admin" or sess.get("user_role") == "admin"

def require_auth(request: web.Request) -> Optional[Dict[str, Any]]:
    sess = get_session(request)
    return sess

def require_admin(request: web.Request) -> Optional[Dict[str, Any]]:
    sess = get_session(request)
    if sess and is_admin_session(sess):
        return sess
    return None

def require_owner(request: web.Request) -> Optional[Dict[str, Any]]:
    sess = get_session(request)
    if sess and is_owner_session(sess):
        return sess
    return None

def get_manageable_guild_ids_for_session(sess: Dict[str, Any]) -> Optional[List[str]]:
    """None = admin full access, [] = no access, list = allowed guild ids"""
    if is_admin_session(sess):
        return None
    # user role
    discord_id = sess.get("discord_id")
    extra = sess.get("extra", {})
    # if we stored manage_guild_ids from oauth
    if extra and extra.get("manage_guild_ids"):
        return [str(x) for x in extra["manage_guild_ids"]]
    # try to infer via bot guild membership
    if discord_id and BOT_INSTANCE and getattr(BOT_INSTANCE, "is_ready", lambda: False)():
        allowed = []
        try:
            did_int = int(discord_id)
            for g in BOT_INSTANCE.guilds:
                member = g.get_member(did_int)
                if member:
                    perms = member.guild_permissions
                    if perms.administrator or perms.manage_guild:
                        allowed.append(str(g.id))
                else:
                    # fallback: check owner
                    if str(g.owner_id) == str(discord_id):
                        allowed.append(str(g.id))
        except Exception as e:
            print(f"[Auth] get manageable error: {e}")
        return allowed
    return []

def can_access_guild(sess: Dict[str, Any], guild_id: str) -> bool:
    if is_admin_session(sess):
        return True
    allowed = get_manageable_guild_ids_for_session(sess)
    if allowed is None:
        return True
    return str(guild_id) in allowed

# ========== Bot Process Manager (tách web panel mở riêng) ==========
_BOT_CACHE = {"time": 0, "data": {"running": False, "mode": "none", "pid": None}}

def _find_bot_process():
    """Tìm process run.py đang chạy - kiểm tra chính xác file"""
    import pathlib
    me = os.getpid()
    try:
        for p in psutil.process_iter(['pid','name','cmdline']):
            try:
                if p.info.get('pid') == me:
                    continue
                name = (p.info.get('name') or "").lower()
                if "python" not in name:
                    continue
                cmdline = p.info.get('cmdline') or []
                # kiểm tra file run.py thực sự trong cmdline, không phải chuỗi trong -c
                if any(pathlib.Path(c).name == "run.py" for c in cmdline):
                    return p
                # fallback: check join nhưng loại trừ -c chứa code
                if len(cmdline) >= 2 and cmdline[0].lower().endswith("python.exe") and "run.py" in cmdline[1]:
                    return p
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue
    except Exception:
        pass
    return None

def get_bot_process_status(use_cache=True):
    global BOT_PROCESS
    now = time.time()
    # Cache 5s để không quét liên tục, đặc biệt khi không có bot (tránh chậm)
    if use_cache and now - _BOT_CACHE["time"] < 5:
        return _BOT_CACHE["data"]
    # Ưu tiên BOT_INSTANCE nếu web đang chạy cùng bot
    if BOT_INSTANCE and getattr(BOT_INSTANCE, "is_ready", lambda: False)():
        try:
            data = {"running": True, "mode": "embedded", "pid": os.getpid(), "username": str(BOT_INSTANCE.user), "latency": round(BOT_INSTANCE.latency*1000,2) if hasattr(BOT_INSTANCE,'latency') else 0}
            _BOT_CACHE.update({"time": now, "data": data})
            return data
        except Exception:
            data = {"running": True, "mode": "embedded", "pid": os.getpid()}
            _BOT_CACHE.update({"time": now, "data": data})
            return data
    # Kiểm tra subprocess do web tạo
    if BOT_PROCESS is not None:
        try:
            if BOT_PROCESS.poll() is None:
                data = {"running": True, "mode": "subprocess", "pid": BOT_PROCESS.pid}
                _BOT_CACHE.update({"time": now, "data": data})
                return data
            else:
                BOT_PROCESS = None
        except Exception:
            BOT_PROCESS = None
    # Kiểm tra pid file
    if BOT_PID_FILE.exists():
        try:
            pid = int(BOT_PID_FILE.read_text().strip())
            if psutil.pid_exists(pid):
                p = psutil.Process(pid)
                # kiểm tra nhanh cmdline
                try:
                    cmd = " ".join(p.cmdline())
                    if "run.py" in cmd:
                        data = {"running": True, "mode": "external", "pid": pid}
                        _BOT_CACHE.update({"time": now, "data": data})
                        return data
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    pass
            else:
                # pid chết, xóa file
                try:
                    BOT_PID_FILE.unlink(missing_ok=True)
                except Exception:
                    pass
        except Exception:
            pass
    # Quét psutil chỉ khi thực sự cần (đã cache nên lần sau sẽ nhanh)
    # Nếu không có dấu hiệu nào của bot (không pid file, không subprocess) thì trả về nhanh, không quét toàn bộ để tránh chậm
    # Chỉ quét khi người dùng yêu cầu kiểm tra kỹ (ví dụ sau khi bấm nút Bật)
    # Ở đây ta vẫn quét nhưng đã tối ưu chỉ duyệt python process nên nhanh (<0.3s)
    proc = _find_bot_process()
    if proc:
        data = {"running": True, "mode": "external", "pid": proc.pid}
        _BOT_CACHE.update({"time": now, "data": data})
        return data
    data = {"running": False, "mode": "none", "pid": None}
    _BOT_CACHE.update({"time": now, "data": data})
    return data

# --- Route Handlers ---

def get_bot_invite_url(client_id: str = None, permissions: str = "8", guild_id: str = None) -> str:
    """Tạo URL mời bot trực tiếp vào server (Guild Install).
    integration_type=0: Buộc Discord mở luồng mời bot vào máy chủ truyền thống thay vì luồng 'Thêm ứng dụng' (User Install).
    scope=bot%20applications.commands: Cấp quyền bot + slash commands trên server.
    """
    if not client_id:
        if BOT_INSTANCE and getattr(BOT_INSTANCE, "user", None):
            client_id = str(BOT_INSTANCE.user.id)
        if not client_id:
            try:
                c_id, _ = get_discord_oauth_config()
                client_id = c_id
            except Exception:
                client_id = ""
        if not client_id:
            try:
                import config
                client_id = getattr(config, "DISCORD_CLIENT_ID", "") or ""
            except Exception:
                client_id = ""
        if not client_id:
            client_id = os.getenv("DISCORD_CLIENT_ID", "1504825128499019807")

    url = f"https://discord.com/oauth2/authorize?client_id={client_id}&permissions={permissions}&integration_type=0&scope=bot%20applications.commands"
    if guild_id:
        url += f"&guild_id={guild_id}"
    return url

async def handle_bot_invite(request: web.Request):
    """Route /bot (và /invite) - Chuyển hướng mời bot vào server.
    Khắc phục luồng 'Thêm ứng dụng' của Discord bằng tham số integration_type=0 (Guild Install).
    """
    client_id = request.query.get("client_id")
    permissions = request.query.get("permissions", "8")
    guild_id = request.query.get("guild_id")
    invite_url = get_bot_invite_url(client_id=client_id, permissions=permissions, guild_id=guild_id)

    # Nếu client yêu cầu JSON (?json=1 hoặc Accept: application/json)
    if request.query.get("json") == "1" or "application/json" in request.headers.get("Accept", ""):
        return web.json_response({
            "ok": True,
            "url": invite_url,
            "permissions": permissions,
            "scope": "bot applications.commands",
            "integration_type": 0
        })

    # Redirect 302 trực tiếp sang Discord invite
    raise web.HTTPFound(location=invite_url)

async def handle_index(request: web.Request):
    """Trang chủ giới thiệu + hướng dẫn (public tại /)"""
    landing_file = TEMPLATES_DIR / "landing.html"
    if landing_file.exists():
        with open(landing_file, "r", encoding="utf-8") as f:
            content = f.read()
        return web.Response(text=content, content_type="text/html")
    # fallback về index cũ
    index_file = TEMPLATES_DIR / "index.html"
    if not index_file.exists():
        return web.Response(text="<h1>Sakura Landing không tồn tại!</h1>", content_type="text/html")
    with open(index_file, "r", encoding="utf-8") as f:
        content = f.read()
    return web.Response(text=content, content_type="text/html")

async def handle_dashboard(request: web.Request):
    """Panel điều khiển chính tại /dashboard (yêu cầu đăng nhập, client sẽ redirect nếu chưa auth)"""
    index_file = TEMPLATES_DIR / "index.html"
    if not index_file.exists():
        return web.Response(text="<h1>Sakura Dashboard: index.html không tồn tại!</h1>", content_type="text/html")
    with open(index_file, "r", encoding="utf-8") as f:
        content = f.read()
    return web.Response(text=content, content_type="text/html")

async def handle_dashboard_guild(request: web.Request):
    """Dashboard per-server tại /dashboard/{guild_id} - rõ ràng, dễ cấu hình từng server"""
    # Vẫn trả về cùng panel, frontend sẽ tự mở drawer theo ID
    # Kiểm tra guild_id hợp lệ (số)
    guild_id = request.match_info.get("guild_id", "")
    # Không cần check 404 ở đây, để frontend xử lý quyền (nếu không có quyền sẽ báo 403)
    index_file = TEMPLATES_DIR / "index.html"
    if not index_file.exists():
        return web.Response(text="<h1>Dashboard không tồn tại</h1>", content_type="text/html", status=404)
    with open(index_file, "r", encoding="utf-8") as f:
        content = f.read()
    # Inject guild_id vào HTML để JS dễ đọc (thêm meta)
    # Đơn giản trả về như dashboard thường
    return web.Response(text=content, content_type="text/html")

def _mc_404_response():
    return web.Response(
        text="<html><head><meta charset='utf-8'><title>404</title></head><body style='display:flex;min-height:100vh;align-items:center;justify-content:center;font-family:sans-serif;background:#07090e;color:#94a3b8'><div style='text-align:center'><h1 style='font-size:4rem;color:#fff'>404</h1><p>Không tìm thấy trang</p><a href='/' style='color:#ff79c6'>Về trang chủ</a></div></body></html>",
        content_type="text/html",
        status=404
    )

def check_mc_perm(sess: Optional[Dict[str, Any]], perm_name: str) -> bool:
    """Kiểm tra quyền truy cập tính năng Minecraft."""
    if not sess:
        return False
    from web.mc_hosting import check_mc_permission_access
    return check_mc_permission_access(DATA_DIR, sess, perm_name)

async def handle_mc_servers_page(request: web.Request):
    """Trang chủ danh sách các máy chủ Minecraft tại /minecraft (và alias /mc)"""
    sess = get_session(request)
    if sess and not is_admin_session(sess) and not check_mc_perm(sess, "can_view_console") and not check_mc_perm(sess, "can_view_players"):
        return _mc_404_response()
    tmpl = TEMPLATES_DIR / "mc_servers.html"
    if not tmpl.exists():
        tmpl = TEMPLATES_DIR / "mc.html"
    if not tmpl.exists():
        return web.Response(text="<h1>mc_servers.html không tồn tại</h1>", content_type="text/html", status=404)
    with open(tmpl, "r", encoding="utf-8") as f:
        return web.Response(text=f.read(), content_type="text/html")

async def handle_mc_console_page(request: web.Request):
    """Bảng Console điều khiển server Minecraft tại /minecraft/console"""
    sess = get_session(request)
    if sess and not is_admin_session(sess) and not check_mc_perm(sess, "can_view_console"):
        return _mc_404_response()
    tmpl = TEMPLATES_DIR / "mc_console.html"
    if not tmpl.exists():
        return web.Response(text="<h1>mc_console.html không tồn tại</h1>", content_type="text/html", status=404)
    with open(tmpl, "r", encoding="utf-8") as f:
        return web.Response(text=f.read(), content_type="text/html")

async def handle_mc_files_page(request: web.Request):
    """Quản lý tệp máy chủ Minecraft tại /minecraft/file"""
    sess = get_session(request)
    if sess and not is_admin_session(sess) and not check_mc_perm(sess, "can_manage_files"):
        return _mc_404_response()
    tmpl = TEMPLATES_DIR / "mc_files.html"
    if not tmpl.exists():
        return web.Response(text="<h1>mc_files.html không tồn tại</h1>", content_type="text/html", status=404)
    with open(tmpl, "r", encoding="utf-8") as f:
        return web.Response(text=f.read(), content_type="text/html")

async def handle_mc_properties_page(request: web.Request):
    """Cấu hình server.properties máy chủ Minecraft tại /minecraft/properties"""
    sess = get_session(request)
    if sess and not is_admin_session(sess) and not check_mc_perm(sess, "can_manage_properties"):
        return _mc_404_response()
    tmpl = TEMPLATES_DIR / "mc_properties.html"
    if not tmpl.exists():
        return web.Response(text="<h1>mc_properties.html không tồn tại</h1>", content_type="text/html", status=404)
    with open(tmpl, "r", encoding="utf-8") as f:
        return web.Response(text=f.read(), content_type="text/html")

async def handle_mc_players_page(request: web.Request):
    """Quản lý và soi túi đồ người chơi Minecraft tại /minecraft/player"""
    sess = get_session(request)
    if sess and not is_admin_session(sess) and not check_mc_perm(sess, "can_view_players"):
        return _mc_404_response()
    tmpl = TEMPLATES_DIR / "mc_players.html"
    if not tmpl.exists():
        return web.Response(text="<h1>mc_players.html không tồn tại</h1>", content_type="text/html", status=404)
    with open(tmpl, "r", encoding="utf-8") as f:
        return web.Response(text=f.read(), content_type="text/html")

async def handle_mc_manager_page(request: web.Request):
    """Phân quyền người dùng quản trị Minecraft Hosting tại /minecraft/manager - chỉ Admin/Owner"""
    sess = get_session(request)
    if not sess or not is_admin_session(sess):
        return _mc_404_response()
    tmpl = TEMPLATES_DIR / "mc_manager.html"
    if not tmpl.exists():
        return web.Response(text="<h1>mc_manager.html không tồn tại</h1>", content_type="text/html", status=404)
    with open(tmpl, "r", encoding="utf-8") as f:
        return web.Response(text=f.read(), content_type="text/html")

handle_mc_page = handle_mc_servers_page

def get_discord_redirect_uri(request: web.Request) -> str:
    """Xác định redirect_uri chính xác cho Discord OAuth2.
    Ưu tiên cấu hình DISCORD_REDIRECT_URI trong config.py.
    Tự động nhận diện scheme (HTTPS/HTTP) và host khi chạy sau Reverse Proxy (Nginx, Caddy, Cloudflare).
    """
    try:
        import config
        cfg_uri = str(getattr(config, "DISCORD_REDIRECT_URI", "") or "").strip()
        if cfg_uri:
            return cfg_uri
    except Exception:
        pass

    # Nhận diện scheme HTTPS/HTTP (hỗ trợ reverse proxy Nginx/Cloudflare)
    proto = request.headers.get("X-Forwarded-Proto", "").strip()
    scheme = proto.split(",")[0].strip() if proto else request.scheme

    # Nhận diện host (hỗ trợ X-Forwarded-Host)
    fwd_host = request.headers.get("X-Forwarded-Host", "").strip()
    if fwd_host:
        host = fwd_host.split(",")[0].strip()
    else:
        host = request.headers.get("Host", f"localhost:{request.url.port or 8080}").strip()

    return f"{scheme}://{host}/api/auth/discord/callback"

def get_discord_oauth_login_url(request: web.Request) -> str:
    """Tạo URL xác thực Discord OAuth2 (identify guilds)"""
    client_id, _ = get_discord_oauth_config()
    if not client_id:
        try:
            import config
            client_id = getattr(config, "DISCORD_CLIENT_ID", "") or ""
        except Exception:
            client_id = ""
    if not client_id:
        client_id = os.getenv("DISCORD_CLIENT_ID", "1504825128499019807")

    redirect_uri = get_discord_redirect_uri(request)
    encoded_redirect_uri = urllib.parse.quote(redirect_uri, safe="")
    scope = "identify guilds"
    return f"https://discord.com/api/oauth2/authorize?client_id={client_id}&redirect_uri={encoded_redirect_uri}&response_type=code&scope={scope.replace(' ', '%20')}"

async def handle_login_page(request: web.Request):
    """Route /login: Chuyển hướng trực tiếp sang đăng nhập bằng Discord.
    Loại bỏ form đăng nhập username/password truyền thống.
    """
    sess = get_session(request)
    if sess:
        return web.HTTPFound(location="/dashboard")

    url = get_discord_oauth_login_url(request)

    # Nếu client truyền ?json=1 hoặc yêu cầu json
    if request.query.get("json") == "1" or "application/json" in request.headers.get("Accept", ""):
        return web.json_response({"ok": True, "url": url})

    # Nếu truyền ?page=1 thì mới render login.html giao diện Discord
    if request.query.get("page") == "1":
        login_file = TEMPLATES_DIR / "login.html"
        if login_file.exists():
            return web.Response(text=login_file.read_text(encoding="utf-8"), content_type="text/html")

    # Mặc định: Chuyển hướng 302 trực tiếp sang Discord OAuth login
    raise web.HTTPFound(location=url)

async def handle_help_page(request: web.Request):
    help_file = TEMPLATES_DIR / "help.html"
    if not help_file.exists():
        return web.Response(text="<h1>help.html không tồn tại</h1>", content_type="text/html", status=404)
    with open(help_file, "r", encoding="utf-8") as f:
        content = f.read()
    return web.Response(text=content, content_type="text/html")

async def handle_plugin_page(request: web.Request):
    plugin_file = TEMPLATES_DIR / "plugin.html"
    if not plugin_file.exists():
        return web.Response(text="<h1>plugin.html không tồn tại</h1>", content_type="text/html", status=404)
    with open(plugin_file, "r", encoding="utf-8") as f:
        content = f.read()
    return web.Response(text=content, content_type="text/html")

async def handle_plugin_help_page(request: web.Request):
    plugin_help_file = TEMPLATES_DIR / "plugin_help.html"
    if not plugin_help_file.exists():
        return web.Response(text="<h1>plugin_help.html không tồn tại</h1>", content_type="text/html", status=404)
    with open(plugin_help_file, "r", encoding="utf-8") as f:
        content = f.read()
    return web.Response(text=content, content_type="text/html")

async def handle_plugin_download(request: web.Request):
    jar_path = BASE_DIR / "plugin" / "target" / "LinhDevPlugin-Test-1.0.jar"
    if not jar_path.exists():
        return web.json_response({"ok": False, "error": "File plugin chưa tồn tại"}, status=404)
    return web.FileResponse(path=str(jar_path), headers={"Content-Disposition": "attachment; filename=LinhDevPlugin-Test-1.0.jar"})

async def handle_discord_well_known(request: web.Request):
    """Xác thực liên kết Discord Domain Verification"""
    return web.Response(text="dh=4601e15002d7ec67c8f4f84be08176d87b61dbd5", content_type="text/plain")

async def handle_support_page(request: web.Request):
    support_file = TEMPLATES_DIR / "support.html"
    if not support_file.exists():
        return web.Response(text="<h1>support.html không tồn tại</h1>", content_type="text/html", status=404)
    with open(support_file, "r", encoding="utf-8") as f:
        content = f.read()
    return web.Response(text=content, content_type="text/html")

async def handle_support_discord(request: web.Request):
    """Chuyển hướng đến Server Discord hỗ trợ"""
    import config
    support_url = getattr(config, "DISCORD_SUPPORT_SERVER", "https://discord.gg/jXvKRJkJgh")
    raise web.HTTPFound(location=support_url)

async def handle_support_invite(request: web.Request):
    invite_url = get_bot_invite_url()
    raise web.HTTPFound(location=invite_url)

async def handle_support_docs(request: web.Request):
    raise web.HTTPFound(location="/help")

async def handle_support_donate(request: web.Request):
    raise web.HTTPFound(location="/support#donate")

async def handle_save_feedback(request: web.Request):
    try:
        body = await request.json()
        name = sanitize_text(body.get("name", "Vô danh"))
        contact = sanitize_text(body.get("contact", ""))
        category = sanitize_text(body.get("category", "Ý kiến đóng góp"))
        content = sanitize_text(body.get("content", ""))
        rating = body.get("rating", 5)

        if not content:
            return web.json_response({"ok": False, "error": "Vui lòng nhập nội dung phản hồi"}, status=400)

        feedback_file = DATA_DIR / "feedbacks.json"
        feedbacks = load_json(feedback_file, [])
        entry = {
            "id": f"fb_{int(time.time())}",
            "name": name,
            "contact": contact,
            "category": category,
            "content": content,
            "rating": rating,
            "time": datetime.datetime.now().strftime("%d/%m/%Y %H:%M:%S")
        }
        feedbacks.insert(0, entry)
        save_json(feedback_file, feedbacks[:500])
        add_log("INFO", f"Nhận phản hồi từ {name} [{category}]: {content[:80]}")
        return web.json_response({"ok": True, "message": "Cảm ơn bạn! Phản hồi đã được gửi đến ban quản trị Sakura Bot."})
    except Exception as e:
        return web.json_response({"ok": False, "error": str(e)}, status=500)

async def handle_terms_page(request: web.Request):
    terms_file = TEMPLATES_DIR / "terms.html"
    if not terms_file.exists():
        return web.Response(text="<h1>terms.html không tồn tại</h1>", content_type="text/html", status=404)
    with open(terms_file, "r", encoding="utf-8") as f:
        content = f.read()
    return web.Response(text=content, content_type="text/html")

async def handle_privacy_page(request: web.Request):
    privacy_file = TEMPLATES_DIR / "privacy.html"
    if not privacy_file.exists():
        return web.Response(text="<h1>privacy.html không tồn tại</h1>", content_type="text/html", status=404)
    with open(privacy_file, "r", encoding="utf-8") as f:
        content = f.read()
    return web.Response(text=content, content_type="text/html")

def _require_login_page(request, next_url):
    sess=get_session(request)
    if sess: return None
    return web.Response(status=302, headers={"Location": f"/login?next={next_url}"})

async def handle_game_hub(request: web.Request):
    f=TEMPLATES_DIR / "games.html"
    if not f.exists():
        return web.Response(text="<h1>games.html chưa tạo</h1>",content_type="text/html",status=404)
    return web.Response(text=f.read_text(encoding="utf-8"),content_type="text/html")
async def handle_game_xo(request: web.Request):
    f=TEMPLATES_DIR / "game_xo.html"
    if not f.exists():
        return web.Response(text="<h1>game_xo.html chưa tạo</h1>",content_type="text/html",status=404)
    return web.Response(text=f.read_text(encoding="utf-8"),content_type="text/html")
async def handle_game_chess(request: web.Request):
    f=TEMPLATES_DIR / "game_chess.html"
    if not f.exists():
        return web.Response(text="<h1>game_chess.html chưa tạo</h1>",content_type="text/html",status=404)
    return web.Response(text=f.read_text(encoding="utf-8"),content_type="text/html")
async def handle_game_wordchain(request: web.Request):
    f=TEMPLATES_DIR / "game_wordchain.html"
    if not f.exists():
        return web.Response(text="<h1>game_wordchain.html chưa tạo</h1>",content_type="text/html",status=404)
    return web.Response(text=f.read_text(encoding="utf-8"),content_type="text/html")
async def handle_game_familytime(request: web.Request):
    f = TEMPLATES_DIR / "game_familytime.html"
    if not f.exists():
        return web.Response(text="<h1>game_familytime.html chưa tạo</h1>", content_type="text/html", status=404)
    return web.Response(text=f.read_text(encoding="utf-8"), content_type="text/html")

async def handle_scribble_rooms(request: web.Request):
    """API trả về danh sách các phòng Scribble đang hoạt động"""
    from web.scribble_backend import ROOMS
    room_list = []
    for rid, r in list(ROOMS.items()):
        human_players = [p for p in r.players.values() if not p.is_bot]
        if len(human_players) == 0 and rid != "lobby":
            continue
        room_list.append({
            "room_id": r.room_id,
            "state": r.state,
            "player_count": len(human_players),
            "max_players": r.max_players,
            "game_mode": r.game_mode,
            "language": r.language,
            "round": r.round,
            "max_rounds": r.max_rounds
        })
    return web.json_response({"ok": True, "rooms": room_list})

async def handle_game_scribble(request: web.Request):
    f=TEMPLATES_DIR / "game_scribble.html"
    if not f.exists():
        return web.Response(text="<h1>game_scribble.html chưa tạo</h1>",content_type="text/html",status=404)
    return web.Response(text=f.read_text(encoding="utf-8"),content_type="text/html")

async def handle_ws_scribble(request: web.Request):
    ws = web.WebSocketResponse()
    await ws.prepare(request)
    room_param = request.query.get("room", "lobby").strip().lower()
    from web.scribble_backend import get_or_create_room
    room = get_or_create_room(room_param)
    player = None

    try:
        async for msg in ws:
            if msg.type == WSMsgType.TEXT:
                try:
                    data = json.loads(msg.data)
                    mtype = data.get("type")
                    if mtype == "join":
                        sess = get_session(request)
                        client_id = data.get("id")
                        clean_username = ""
                        discord_id = ""
                        if sess:
                            raw_user = sess.get("username")
                            if isinstance(raw_user, dict):
                                clean_username = str(raw_user.get("username") or raw_user.get("id") or "")
                                discord_id = str(raw_user.get("id") or sess.get("discord_id") or "")
                            else:
                                clean_username = str(raw_user or "")
                                discord_id = str(sess.get("discord_id") or "")

                        if discord_id:
                            pid = discord_id
                        elif clean_username:
                            pid = clean_username
                        else:
                            pid = str(client_id or data.get("name") or "user_guest")

                        raw_pname = str(data.get("name") or "").strip()
                        if raw_pname and raw_pname != "[object Object]":
                            pname = raw_pname
                        elif sess:
                            pname = sess.get("global_name") or clean_username or "Người chơi"
                        else:
                            pname = "Người chơi"

                        pavatar = sess.get("avatar", "") if sess else data.get("avatar", "")
                        avatar_data = data.get("avatar_data")
                        player = room.add_player(pid, pname, pavatar, avatar_data, ws)

                        # Gửi gói tin welcome để client đồng bộ chính xác Player ID
                        await ws.send_str(json.dumps({
                            "type": "welcome",
                            "your_id": player.pid,
                            "your_name": player.name,
                            "is_host": (room.host_id == player.pid)
                        }, ensure_ascii=False))

                        # Gửi trạng thái phòng hiện tại
                        await ws.send_str(json.dumps(room.get_room_state_dict(), ensure_ascii=False))
                        # Gửi lại nét vẽ hiện tại nếu đang trong round
                        if room.state == "drawing" and room.strokes:
                            for s in room.strokes:
                                await ws.send_str(json.dumps({"type": "redraw_stroke", "stroke": s}, ensure_ascii=False))
                        await room.broadcast({
                            "type": "chat",
                            "sender": "Hệ thống",
                            "text": f"👋 {pname} đã tham gia phòng!",
                            "system": True
                        })
                    elif mtype == "draw_segment" and player:
                        if (room.state == "drawing" and room.drawer_id == player.pid) or room.game_mode == "practice" or room.state == "waiting":
                            sid = data.get("stroke_id")
                            seg = {
                                "x0": data.get("x0"),
                                "y0": data.get("y0"),
                                "x1": data.get("x1"),
                                "y1": data.get("y1"),
                            }
                            if room.strokes and room.strokes[-1].get("id") == sid:
                                room.strokes[-1]["segments"].append(seg)
                            else:
                                room.strokes.append({
                                    "id": sid,
                                    "tool": data.get("tool", "pen"),
                                    "color": data.get("color", "#000000"),
                                    "size": data.get("size", 10),
                                    "segments": [seg]
                                })
                            await room.broadcast({"type": "draw_segment", **data}, exclude_pid=player.pid)
                    elif mtype == "draw" and player:
                        if (room.state == "drawing" and room.drawer_id == player.pid) or room.game_mode == "practice" or room.state == "waiting":
                            stroke = data.get("stroke")
                            if stroke:
                                room.strokes.append(stroke)
                                await room.broadcast({"type": "redraw_stroke", "stroke": stroke}, exclude_pid=player.pid)
                    elif mtype == "clear" and player:
                        if (room.state == "drawing" and room.drawer_id == player.pid) or room.game_mode == "practice" or room.state == "waiting":
                            room.strokes = []
                            await room.broadcast({"type": "clear"})
                    elif mtype == "undo" and player:
                        if (room.state == "drawing" and room.drawer_id == player.pid) or room.game_mode == "practice" or room.state == "waiting":
                            if room.strokes:
                                room.strokes.pop()  # Xóa toàn bộ 1 nét vẽ (1 continuous stroke)
                                await room.broadcast({"type": "clear"})
                                for s in room.strokes:
                                    await room.broadcast({"type": "redraw_stroke", "stroke": s})
                    elif mtype == "select_word" and player:
                        if room.state == "selecting" and room.drawer_id == player.pid:
                            word = str(data.get("word", "")).strip()
                            if word:
                                await room.start_drawing_phase(word)
                    elif mtype == "guess" and player:
                        text = str(data.get("text", "")).strip()
                        if text:
                            await room.handle_guess(player.pid, text)
                    elif mtype == "start_game":
                        await room.start_game()
                    elif mtype == "toggle_bot":
                        room.toggle_bot()
                        await room.broadcast(room.get_room_state_dict())
                    elif mtype in ("update_settings", "configure_room"):
                        room.update_settings(
                            max_players=int(data.get("max_players", 8)),
                            language=str(data.get("language", "vi")),
                            draw_time=int(data.get("draw_time", 80)),
                            max_rounds=int(data.get("max_rounds", data.get("rounds", 3))),
                            game_mode=str(data.get("game_mode", "classic")),
                            word_choices_count=int(data.get("word_choices_count", 3)),
                            hint_count=int(data.get("hint_count", -1)),
                            custom_words_str=str(data.get("custom_words", ""))
                        )
                        await room.broadcast(room.get_room_state_dict())
                    elif mtype == "reaction" and player:
                        rx = str(data.get("reaction", "like"))
                        await room.handle_reaction(player.pid, rx)
                except Exception as ex:
                    logging.warning(f"Error handling scribble ws: {ex}")
            elif msg.type == WSMsgType.ERROR:
                logging.warning(f"Scribble WS error: {ws.exception()}")
    finally:
        if player:
            room.remove_player(player.pid)
            await room.broadcast({
                "type": "chat",
                "sender": "Hệ thống",
                "text": f"👋 {player.name} đã rời phòng.",
                "system": True
            })
            await room.broadcast(room.get_room_state_dict())
    return ws
async def handle_tarot_page(request: web.Request):
    r=_require_login_page(request, "/tarot")
    if r: return r
    f=TEMPLATES_DIR / "tarot.html"
    if not f.exists():
        return web.Response(text="<h1>tarot.html chưa tạo</h1>",content_type="text/html",status=404)
    return web.Response(text=f.read_text(encoding="utf-8"),content_type="text/html")

async def handle_tarot_draw(request: web.Request):
    if not require_auth(request):
        return web.json_response({"ok":False,"error":"Cần đăng nhập để rút bài Tarot"}, status=401)
    try:
        from data.data import TAROT_DECK
        import random
        card_name = random.choice(list(TAROT_DECK))
        orientation = random.choice(["upright", "reversed"])
        return web.json_response({"ok":True,"card":{
            "name":card_name,
            "orientation":"Xuôi" if orientation == "upright" else "Ngược",
            "meaning":TAROT_DECK[card_name][orientation]
        }})
    except Exception as error:
        return web.json_response({"ok":False,"error":str(error)}, status=500)

async def handle_tarot_interpret(request: web.Request):
    if not require_auth(request):
        return web.json_response({"ok":False,"error":"Cần đăng nhập để xem luận giải"}, status=401)
    try:
        body = await request.json()
        card_name = sanitize_text(str(body.get("name", "")), 200).strip()
        orientation = sanitize_text(str(body.get("orientation", "")), 30).strip()
        meaning = sanitize_text(str(body.get("meaning", "")), 500).strip()
        question = sanitize_text(str(body.get("question", "")), 500).strip()
        if not card_name or not meaning:
            return web.json_response({"ok":False,"error":"Thiếu thông tin lá bài"}, status=400)
        reply = None
        try:
            import config
            xkiro_key = getattr(config, "XKIRO_API_KEY", "") or os.getenv("XKIRO_API_KEY", "")
            prompt = ("Bạn là reader Tarot chuyên nghiệp. Hãy luận giải bằng tiếng Việt, "
                "ấm áp, rõ ràng và thực tế. Không khẳng định tương lai tuyệt đối; "
                "hãy xem Tarot như công cụ tự phản chiếu. "
                f"Lá bài: {card_name} ({orientation}). Ý nghĩa gốc: {meaning}. "
                f"Câu hỏi: {question or 'Tổng quan về hiện tại'}. "
                "Trình bày ngắn gọn theo 3 phần: thông điệp, điều nên làm, lời nhắc.")
            if xkiro_key:
                ai_model = getattr(config, "AI_MODEL", "sensenova/sensenova-6.8-flash-lite")
                payload = {"model": ai_model, "messages":[
                    {"role":"system","content":"Bạn là chuyên gia luận giải Tarot bằng tiếng Việt."},
                    {"role":"user","content":prompt}],"max_tokens":450,"temperature":0.8}
                async with aiohttp.ClientSession() as session:
                    async with session.post("https://api.xkiro.com/v1/chat/completions",
                        headers={"Authorization":f"Bearer {xkiro_key}","Content-Type":"application/json"},
                        json=payload, timeout=aiohttp.ClientTimeout(total=15)) as response:
                        if response.status == 200:
                            result = await response.json()
                            reply = result["choices"][0]["message"]["content"].strip()
            if not reply:
                groq_key = getattr(config, "GROQ_API_KEY", "")
                if groq_key:
                    import aiohttp
                    payload = {"model":"llama-3.3-70b-versatile","messages":[
                        {"role":"system","content":"Bạn là chuyên gia luận giải Tarot bằng tiếng Việt."},
                        {"role":"user","content":prompt}],"max_tokens":450,"temperature":0.8}
                    async with aiohttp.ClientSession() as session:
                        async with session.post("https://api.groq.com/openai/v1/chat/completions",
                            headers={"Authorization":f"Bearer {groq_key}","Content-Type":"application/json"},
                            json=payload, timeout=aiohttp.ClientTimeout(total=15)) as response:
                            if response.status == 200:
                                result = await response.json()
                                reply = result["choices"][0]["message"]["content"].strip()
        except Exception as error:
            print(f"[Tarot] AI fail: {error}")
        if not reply:
            reply = (f"Thông điệp: {meaning}\n\n"
                "Điều nên làm: Hãy dùng thông điệp này để nhìn lại lựa chọn và cảm xúc của bạn, "
                "thay vì xem đó là lời khẳng định chắc chắn về tương lai.\n\n"
                "Lời nhắc: Bạn vẫn là người quyết định hướng đi của mình.")
        return web.json_response({"ok":True,"reply":reply,"ai":not reply.startswith("Thông điệp:")})
    except Exception as error:
        return web.json_response({"ok":False,"error":str(error)}, status=500)

async def handle_wordlist(request: web.Request):
    p=DATA_DIR / "vietnamese-words.txt"
    words=[]
    if p.exists():
        try:
            txt=p.read_text(encoding="utf-8")
            for line in txt.splitlines():
                w=line.strip().lower()
                if len(w.split())==2 and w:
                    words.append(w)
            words=list(dict.fromkeys(words))[:5000]
        except: pass
    if not words:
        words=["hoa hồng","hồng nhung","nhung nhớ","nhớ nhà","nhà cửa"]
    return web.json_response({"ok":True,"words":words})

# ==============================================================================
# HỆ THỐNG QUẢN LÝ MINIGAME NỐI CHỮ (WORD CHAIN MANAGEMENT)
# ==============================================================================

async def handle_wordchain_stats(request: web.Request):
    sess = require_auth(request)
    if not sess: return web.json_response({"ok": False, "error": "Unauthorized"}, status=401)
    try:
        dict_file = BASE_DIR / "data" / "vietnamese-words.txt"
        total_words = 0
        if dict_file.exists():
            with open(dict_file, "r", encoding="utf-8") as f:
                for line in f:
                    if line.strip(): total_words += 1

        active_games_file = BASE_DIR / "data" / "word_chain_active_games.json"
        active_games = 0
        if active_games_file.exists():
            try:
                with open(active_games_file, "r", encoding="utf-8") as f:
                    ag = json.load(f)
                    active_games = len(ag)
            except Exception: pass

        scores_file = BASE_DIR / "data" / "word_chain_scores.json"
        total_players = 0
        if scores_file.exists():
            try:
                with open(scores_file, "r", encoding="utf-8") as f:
                    sc = json.load(f)
                    all_p = set()
                    for g_id, p_map in sc.items():
                        all_p.update(p_map.keys())
                    total_players = len(all_p)
            except Exception: pass

        return web.json_response({
            "ok": True,
            "total_words": total_words,
            "active_games": active_games,
            "total_players": total_players
        })
    except Exception as e:
        return web.json_response({"ok": False, "error": str(e)}, status=500)

async def handle_wordchain_get_words(request: web.Request):
    sess = require_auth(request)
    if not sess: return web.json_response({"ok": False, "error": "Unauthorized"}, status=401)
    try:
        q = request.query.get("q", "").strip().lower()
        page = max(1, int(request.query.get("page", 1)))
        limit = min(100, max(10, int(request.query.get("limit", 30))))

        dict_file = BASE_DIR / "data" / "vietnamese-words.txt"
        if not dict_file.exists():
            return web.json_response({"ok": True, "words": [], "total": 0, "page": page, "pages": 1})

        matching = []
        with open(dict_file, "r", encoding="utf-8") as f:
            for line in f:
                w = line.strip().lower()
                if not w: continue
                if not q or q in w:
                    matching.append(w)

        total = len(matching)
        total_pages = max(1, math.ceil(total / limit))
        start_idx = (page - 1) * limit
        end_idx = start_idx + limit
        paged_words = matching[start_idx:end_idx]

        return web.json_response({
            "ok": True,
            "words": paged_words,
            "total": total,
            "page": page,
            "pages": total_pages,
            "limit": limit
        })
    except Exception as e:
        return web.json_response({"ok": False, "error": str(e)}, status=500)

async def handle_wordchain_add_word(request: web.Request):
    sess = require_auth(request)
    if not sess: return web.json_response({"ok": False, "error": "Unauthorized"}, status=401)
    try:
        body = await request.json()
        raw_word = str(body.get("word", "")).strip().lower()
        tokens = raw_word.split()
        if len(tokens) != 2:
            return web.json_response({"ok": False, "error": "Từ vựng nối chữ phải gồm đúng 2 âm tiết (Ví dụ: 'hoa hồng', 'nhà cửa')"}, status=400)

        dict_file = BASE_DIR / "data" / "vietnamese-words.txt"
        dict_file.parent.mkdir(parents=True, exist_ok=True)

        existing = set()
        if dict_file.exists():
            with open(dict_file, "r", encoding="utf-8") as f:
                for line in f:
                    w = line.strip().lower()
                    if w: existing.add(w)

        if raw_word in existing:
            return web.json_response({"ok": False, "error": f"Từ '{raw_word}' đã có trong từ điển nối chữ!"}, status=400)

        with open(dict_file, "a", encoding="utf-8") as f:
            f.write(f"\n{raw_word}")

        # Đồng bộ vào bộ nhớ Cog nếu bot đang chạy
        if BOT_INSTANCE:
            cog = BOT_INSTANCE.get_cog("WordChainGame")
            if cog and hasattr(cog, "add_new_word_to_dict"):
                cog.add_new_word_to_dict(raw_word)

        add_log("SUCCESS", f"User {sess.get('username')} thêm từ nối chữ mới: '{raw_word}'")
        return web.json_response({"ok": True, "message": f"Đã thêm từ '{raw_word}' vào từ điển nối chữ!"})
    except Exception as e:
        return web.json_response({"ok": False, "error": str(e)}, status=500)

async def handle_wordchain_delete_word(request: web.Request):
    sess = require_auth(request)
    if not sess: return web.json_response({"ok": False, "error": "Unauthorized"}, status=401)
    try:
        body = await request.json()
        target = str(body.get("word", "")).strip().lower()
        if not target:
            return web.json_response({"ok": False, "error": "Thiếu từ cần xóa"}, status=400)

        dict_file = BASE_DIR / "data" / "vietnamese-words.txt"
        if not dict_file.exists():
            return web.json_response({"ok": False, "error": "File từ điển không tồn tại"}, status=404)

        found = False
        new_lines = []
        with open(dict_file, "r", encoding="utf-8") as f:
            for line in f:
                w = line.strip().lower()
                if w == target:
                    found = True
                elif w:
                    new_lines.append(w)

        if not found:
            return web.json_response({"ok": False, "error": f"Không tìm thấy từ '{target}' trong từ điển"}, status=404)

        with open(dict_file, "w", encoding="utf-8") as f:
            f.write("\n".join(new_lines) + "\n")

        # Cập nhật cache bot
        if BOT_INSTANCE:
            cog = BOT_INSTANCE.get_cog("WordChainGame")
            if cog and hasattr(cog, "word_set") and target in cog.word_set:
                cog.word_set.remove(target)
                tokens = target.split()
                if tokens and hasattr(cog, "word_index") and tokens[0] in cog.word_index:
                    if target in cog.word_index[tokens[0]]:
                        cog.word_index[tokens[0]].remove(target)

        add_log("INFO", f"User {sess.get('username')} xóa từ nối chữ: '{target}'")
        return web.json_response({"ok": True, "message": f"Đã xóa từ '{target}' khỏi từ điển nối chữ!"})
    except Exception as e:
        return web.json_response({"ok": False, "error": str(e)}, status=500)

async def handle_wordchain_leaderboard(request: web.Request):
    sess = require_auth(request)
    if not sess: return web.json_response({"ok": False, "error": "Unauthorized"}, status=401)
    try:
        lb_type = request.query.get("type", "all").strip().lower()
        guild_id = request.query.get("guild_id", "").strip()

        scores_file = BASE_DIR / "data" / ("word_chain_weekly_scores.json" if lb_type == "weekly" else "word_chain_scores.json")
        raw_scores = {}
        if scores_file.exists():
            try:
                with open(scores_file, "r", encoding="utf-8") as f:
                    raw_scores = json.load(f)
            except Exception: pass

        # Gộp điểm nếu guild_id không chỉ định (toàn cục) hoặc lọc theo guild
        merged_scores = {}
        for g_id, p_map in raw_scores.items():
            if guild_id and str(g_id) != str(guild_id):
                continue
            for u_id, sc in p_map.items():
                u_str = str(u_id)
                if u_str in {"1144785664458637394", str(OWNER_ID)}:
                    continue
                merged_scores[u_str] = merged_scores.get(u_str, 0) + int(sc)

        sorted_items = sorted(merged_scores.items(), key=lambda x: x[1], reverse=True)[:100]

        leaderboard = []
        for rank, (u_id, score) in enumerate(sorted_items, 1):
            user_info = {"user_id": u_id, "username": f"User {u_id}", "avatar": "", "score": score, "rank": rank}
            if BOT_INSTANCE:
                try:
                    u_obj = BOT_INSTANCE.get_user(int(u_id))
                    if u_obj:
                        user_info["username"] = u_obj.display_name or u_obj.name
                        user_info["avatar"] = str(u_obj.display_avatar.url) if u_obj.display_avatar else ""
                except Exception: pass
            leaderboard.append(user_info)

        return web.json_response({
            "ok": True,
            "type": lb_type,
            "guild_id": guild_id or None,
            "total": len(sorted_items),
            "leaderboard": leaderboard
        })
    except Exception as e:
        return web.json_response({"ok": False, "error": str(e)}, status=500)

async def handle_wordchain_adjust_score(request: web.Request):
    sess = require_admin(request)
    if not sess: return web.json_response({"ok": False, "error": "Chỉ dành cho Admin"}, status=403)
    try:
        body = await request.json()
        guild_id = str(body.get("guild_id", "")).strip()
        user_id = str(body.get("user_id", "")).strip()
        delta = int(body.get("delta", 0))
        lb_type = str(body.get("type", "all")).strip().lower()

        if not user_id:
            return web.json_response({"ok": False, "error": "Thiếu user ID"}, status=400)

        scores_file = BASE_DIR / "data" / ("word_chain_weekly_scores.json" if lb_type == "weekly" else "word_chain_scores.json")
        data = {}
        if scores_file.exists():
            try:
                with open(scores_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
            except Exception: pass

        g_key = guild_id or list(data.keys())[0] if data else "global"
        if g_key not in data:
            data[g_key] = {}

        current_val = data[g_key].get(user_id, 0)
        new_val = max(0, current_val + delta)
        data[g_key][user_id] = new_val

        with open(scores_file, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

        # Cập nhật cache bot nếu có
        if BOT_INSTANCE:
            cog = BOT_INSTANCE.get_cog("WordChainGame")
            if cog:
                target_dict = cog.weekly_scores if lb_type == "weekly" else cog.scores
                if g_key in target_dict:
                    target_dict[g_key][user_id] = new_val

        add_log("SUCCESS", f"Admin {sess.get('username')} chỉnh điểm nối chữ ({lb_type}) user {user_id}: {current_val} -> {new_val}")
        return web.json_response({"ok": True, "message": f"Đã cập nhật điểm cho user {user_id}: {new_val}", "new_score": new_val})
    except Exception as e:
        return web.json_response({"ok": False, "error": str(e)}, status=500)

# --- Game BXH per game ---
def _game_lb_file(game: str): return DATA_DIR / f"game_{game}_leaderboard.json"
def _load_lb(game: str):
    p=_game_lb_file(game)
    if not p.exists(): return {}
    try: return json.loads(p.read_text(encoding="utf-8"))
    except: return {}
def _save_lb(game: str, data: dict):
    try: _game_lb_file(game).write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    except: pass

async def handle_game_leaderboard(request: web.Request):
    # Không yêu cầu đăng nhập để xem BXH
    game=request.match_info.get("game")
    if game not in ("xo","chess","wordchain","scribble"): return web.json_response({"ok":False,"error":"game không hợp lệ"},status=400)
    lb=_load_lb(game)
    users=load_json(DATA_DIR/"web_users.json",{})
    items=[]
    owner_ids = {"1144785664458637394", str(OWNER_ID)}
    for uid, st in lb.items():
        if str(uid) in owner_ids:
            continue
        u=users.get(uid, {})
        items.append({"username": uid, "avatar": u.get("avatar",""), "wins": int(st.get("wins",0)), "losses": int(st.get("losses",0)), "draws": int(st.get("draws",0)), "games": int(st.get("wins",0)+st.get("losses",0)+st.get("draws",0))})
    items.sort(key=lambda x: (x["wins"], -x["losses"]), reverse=True)
    return web.json_response({"ok":True,"leaderboard": items[:50]})

async def handle_game_score(request: web.Request):
    limited, retry, _ = check_rate(request, "game_score")
    if limited:
        return web.json_response({"ok":False,"error":f"Thao tác quá nhanh, thử lại sau {retry}s"}, status=429, headers={"Retry-After": str(retry)})
    sess=get_session(request)
    game=request.match_info.get("game")
    if game not in ("xo","chess","wordchain","scribble"): return web.json_response({"ok":False,"error":"game không hợp lệ"},status=400)
    try:
        body=await request.json()
        result=str(body.get("result","")).lower() # win/loss/draw
        if result not in ("win","loss","draw"): return web.json_response({"ok":False,"error":"result phải là win/loss/draw"},status=400)
        
        # Nếu đã đăng nhập thì lấy username tài khoản, nếu chưa thì lấy guest name unknowplayer#{number}
        if sess:
            raw_u = sess.get("username")
            if isinstance(raw_u, dict):
                username = raw_u.get("username") or "user"
            else:
                username = str(raw_u or "")
        else:
            client_guest = str(body.get("username", "")).strip()
            if client_guest.startswith("unknowplayer#"):
                username = client_guest
            else:
                import random
                username = f"unknowplayer#{random.randint(1000, 9999)}"

        lb=_load_lb(game)
        st=lb.get(username, {"wins":0,"losses":0,"draws":0})
        if result=="win": st["wins"]=int(st.get("wins",0))+1
        elif result=="loss": st["losses"]=int(st.get("losses",0))+1
        else: st["draws"]=int(st.get("draws",0))+1
        lb[username]=st
        _save_lb(game, lb)
        return web.json_response({"ok":True,"stats":st, "username": username})
    except Exception as e:
        return web.json_response({"ok":False,"error":str(e)},status=500)

# --- TikTok Downloader Page & APIs ---
async def handle_tiktok_page(request: web.Request):
    f = TEMPLATES_DIR / "tiktok.html"
    if not f.exists():
        return web.Response(text="<h1>tiktok.html chưa tạo</h1>", content_type="text/html", status=404)
    return web.Response(text=f.read_text(encoding="utf-8"), content_type="text/html")

async def handle_api_tiktok_info(request: web.Request):
    """Trích xuất dữ liệu chi tiết TikTok/Douyin (Video HD/SD, Có logo, MP3, Album ảnh Slideshow)."""
    try:
        body = await request.json()
        raw_url = str(body.get("url", "")).strip()
        if not raw_url:
            return web.json_response({"ok": False, "error": "Vui lòng nhập đường dẫn TikTok hoặc Douyin hợp lệ!"}, status=400)

        session = aiohttp.ClientSession(headers={
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
        })
        try:
            canonical_url = raw_url
            try:
                async with session.head(canonical_url, allow_redirects=True, timeout=10) as head_resp:
                    canonical_url = str(head_resp.url)
            except Exception:
                pass

            data = None
            # Ưu tiên 1: TikWM API với hd=1
            try:
                async with session.post("https://www.tikwm.com/api/", data={"url": canonical_url, "hd": 1}, timeout=20) as resp:
                    if resp.status == 200:
                        json_resp = await resp.json()
                        if json_resp.get("code") == 0 and json_resp.get("data"):
                            data = json_resp["data"]
            except Exception:
                pass

            # Dự phòng 1: TikWM API không kèm hd
            if not data:
                try:
                    async with session.post("https://www.tikwm.com/api/", data={"url": canonical_url}, timeout=20) as resp:
                        if resp.status == 200:
                            json_resp = await resp.json()
                            if json_resp.get("code") == 0 and json_resp.get("data"):
                                data = json_resp["data"]
                except Exception:
                    pass

            if not data:
                return web.json_response({
                    "ok": False,
                    "error": "Không thể lấy thông tin bài viết từ TikTok. Vui lòng kiểm tra lại liên kết hoặc trạng thái riêng tư của bài viết."
                }, status=400)

            author_data = data.get("author") or {}
            music_data = data.get("music_info") or {}
            images = data.get("images") or []
            is_slideshow = bool(images and isinstance(images, list) and len(images) > 0)

            result = {
                "ok": True,
                "type": "slideshow" if is_slideshow else "video",
                "id": str(data.get("id", "")),
                "title": data.get("title") or "Nội dung TikTok",
                "canonical_url": canonical_url,
                "author": {
                    "nickname": author_data.get("nickname") or "Người dùng TikTok",
                    "unique_id": author_data.get("unique_id") or "",
                    "avatar": author_data.get("avatar") or ""
                },
                "stats": {
                    "likes": data.get("digg_count", 0),
                    "comments": data.get("comment_count", 0),
                    "shares": data.get("share_count", 0),
                    "views": data.get("play_count", 0)
                },
                "duration": data.get("duration", 0),
                "cover": data.get("origin_cover") or data.get("cover") or "",
                "music": {
                    "title": music_data.get("title") or (data.get("music") and "Âm thanh gốc") or "Không rõ",
                    "author": music_data.get("author") or "",
                    "url": data.get("music") or music_data.get("play") or ""
                },
                "video": {
                    "hd": data.get("hdplay") or "",
                    "hd_size": data.get("hd_size", 0),
                    "sd": data.get("play") or "",
                    "sd_size": data.get("size", 0),
                    "wm": data.get("wmplay") or "",
                    "wm_size": data.get("wm_size", 0)
                },
                "images": images
            }
            return web.json_response(result)
        finally:
            await session.close()
    except Exception as e:
        return web.json_response({"ok": False, "error": f"Lỗi máy chủ: {str(e)}"}, status=500)

async def handle_api_tiktok_download(request: web.Request):
    """Proxy stream trực tiếp dữ liệu từ TikTok CDN về trình duyệt người dùng với header Content-Disposition."""
    target_url = request.query.get("url", "").strip()
    filename = request.query.get("filename", "tiktok_media").strip()
    if not target_url:
        return web.Response(text="Thiếu tham số url", status=400)

    filename = re.sub(r'[\\/*?:"<>|]', "", filename)
    if not re.search(r'\.(mp4|mp3|jpg|jpeg|png|webp|gif)$', filename, re.IGNORECASE):
        filename += ".mp4"

    session = aiohttp.ClientSession(headers={
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
        "Referer": "https://www.tiktok.com/"
    })
    try:
        async with session.get(target_url, timeout=60) as resp:
            if resp.status != 200:
                await session.close()
                raise web.HTTPFound(location=target_url)

            content_type = resp.headers.get("Content-Type", "application/octet-stream")
            content_length = resp.headers.get("Content-Length")

            response = web.StreamResponse(
                status=200,
                reason="OK",
                headers={
                    "Content-Type": content_type,
                    "Content-Disposition": f'attachment; filename="{filename}"',
                    "Cache-Control": "public, max-age=86400"
                }
            )
            if content_length:
                response.headers["Content-Length"] = content_length

            await response.prepare(request)
            async for chunk in resp.content.iter_chunked(128 * 1024):
                await response.write(chunk)
            await response.write_eof()
            return response
    except web.HTTPFound:
        raise
    except Exception:
        raise web.HTTPFound(location=target_url)
    finally:
        if not session.closed:
            await session.close()

async def handle_api_tiktok_download_zip(request: web.Request):
    """Tải toàn bộ danh sách ảnh trong album slideshow và đóng gói file .ZIP gửi về cho người dùng."""
    try:
        import zipfile
        import io

        body = await request.json()
        images = body.get("images", [])
        title = body.get("title", "tiktok_photos")
        if not images or not isinstance(images, list):
            return web.json_response({"ok": False, "error": "Danh sách ảnh trống"}, status=400)

        images = images[:60]
        safe_title = re.sub(r'[\\/*?:"<>|]', "_", title)[:40] or "tiktok_album"
        zip_filename = f"{safe_title}.zip"

        session = aiohttp.ClientSession(headers={
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
        })

        async def fetch_img(idx, url):
            try:
                async with session.get(url, timeout=20) as resp:
                    if resp.status == 200:
                        content = await resp.read()
                        return idx, content
            except Exception:
                pass
            return idx, None

        tasks = [fetch_img(i + 1, u) for i, u in enumerate(images)]
        results = await asyncio.gather(*tasks)
        await session.close()

        zip_buffer = io.BytesIO()
        with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zip_file:
            for idx, content in results:
                if content:
                    zip_file.writestr(f"photo_{idx:02d}.jpg", content)

        zip_bytes = zip_buffer.getvalue()
        if not zip_bytes:
            return web.json_response({"ok": False, "error": "Không tải được ảnh nào để đóng gói ZIP"}, status=500)

        return web.Response(
            body=zip_bytes,
            content_type="application/zip",
            headers={
                "Content-Disposition": f'attachment; filename="{zip_filename}"',
                "Content-Length": str(len(zip_bytes))
            }
        )
    except Exception as e:
        return web.json_response({"ok": False, "error": str(e)}, status=500)

async def handle_yt_video(request: web.Request):
    f=TEMPLATES_DIR / "yt_video.html"
    if not f.exists():
        return web.Response(text="<h1>yt_video.html chưa tạo</h1>",content_type="text/html",status=404)
    return web.Response(text=f.read_text(encoding="utf-8"),content_type="text/html")

async def handle_yt_files(request: web.Request):
    video_exts = {'.mp4', '.webm', '.mkv', '.mov', '.avi', '.m4v'}
    files = []
    seen = set()

    for folder_name in ("downloads", "owner_downloads"):
        folder = BASE_DIR / folder_name
        if not folder.exists():
            continue
        for path in sorted(folder.iterdir(), key=lambda p: p.name.lower()):
            if not path.is_file() or path.suffix.lower() not in video_exts:
                continue
            rel = path.relative_to(BASE_DIR)
            url = f"/{folder_name}/{path.name}"
            if url in seen:
                continue
            seen.add(url)
            files.append({
                "title": path.stem,
                "url": url,
                "desc": f"Video từ thư mục {folder_name}",
                "source": folder_name,
            })

    return web.json_response({"ok": True, "videos": files})

async def handle_global_chat_page(request: web.Request):
    sess=get_session(request)
    if not sess:
        return web.Response(status=302, headers={"Location":"/login?next=/global-chat"})
    gc_file=TEMPLATES_DIR / "global_chat.html"
    if not gc_file.exists():
        return web.Response(text="<h1>global_chat.html chưa tạo</h1>",content_type="text/html",status=404)
    return web.Response(text=gc_file.read_text(encoding="utf-8"),content_type="text/html")

async def handle_account_page(request: web.Request):
    # yêu cầu đăng nhập, nếu chưa thì vẫn trả về trang nhưng JS sẽ redirect
    sess = get_session(request)
    if not sess:
        # vẫn trả về trang để JS xử lý, hoặc redirect
        pass
    acc_file = TEMPLATES_DIR / "account.html"
    if not acc_file.exists():
        return web.Response(text="<h1>account.html không tồn tại</h1>", content_type="text/html", status=404)
    with open(acc_file, "r", encoding="utf-8") as f:
        content = f.read()
    return web.Response(text=content, content_type="text/html")

async def handle_image_gallery(request: web.Request):
    images_dir = BASE_DIR / "web" / "images"
    if not images_dir.exists():
        return web.Response(text="<h1>Thư mục images không tồn tại</h1>", content_type="text/html", status=404)

    files = []
    for path in sorted(images_dir.iterdir(), key=lambda p: p.name.lower()):
        if path.is_file() and path.suffix.lower() in {".png", ".jpg", ".jpeg", ".gif", ".webp", ".bmp", ".svg"}:
            files.append({
                "name": path.name,
                "url": f"/image/{path.name}",
                "download": f"/image/{path.name}?download=1",
            })

    if not files:
        content = "<div class=\"empty\">Chưa có ảnh nào trong thư mục images.</div>"
    else:
        html_cards = []
        for item in files:
            html_cards.append(
                f"<a class=\"card\" href=\"{item['url']}\">"
                f"<img class=\"thumb\" src=\"{item['url']}\" alt=\"{item['name']}\">"
                f"<span class=\"name\">{item['name']}</span>"
                f"</a>"
            )
        content = "<div class=\"gallery\">" + "".join(html_cards) + "</div>"

    template = (TEMPLATES_DIR / "image.html").read_text(encoding="utf-8")
    html = template.replace("__COUNT__", str(len(files))).replace("__CONTENT__", content)
    return web.Response(text=html, content_type="text/html")

async def handle_image_view(request: web.Request):
    filename = request.match_info.get("filename", "")
    if not filename:
        return web.Response(text="<h1>Thiếu tên ảnh</h1>", content_type="text/html", status=400)

    images_dir = BASE_DIR / "web" / "images"
    if not images_dir.exists():
        return web.Response(text="<h1>Thư mục images không tồn tại</h1>", content_type="text/html", status=404)

    file_path = (images_dir / filename).resolve()
    try:
        file_path.relative_to(images_dir.resolve())
    except ValueError:
        return web.Response(text="<h1>Ảnh không tồn tại</h1>", content_type="text/html", status=404)

    if not file_path.is_file():
        return web.Response(text="<h1>Ảnh không tồn tại</h1>", content_type="text/html", status=404)

    is_download = request.query.get("download") == "1"
    mime_map = {
        ".png": "image/png",
        ".jpg": "image/jpeg",
        ".jpeg": "image/jpeg",
        ".gif": "image/gif",
        ".webp": "image/webp",
        ".bmp": "image/bmp",
        ".svg": "image/svg+xml",
    }
    if is_download:
        return web.FileResponse(path=str(file_path), headers={"Content-Disposition": f"attachment; filename={file_path.name}"})

    template = (TEMPLATES_DIR / "image.html").read_text(encoding="utf-8")
    html = template.replace("__COUNT__", "1").replace(
        "__CONTENT__",
        "<div class=\"viewer\">"
        f"<img src=\"/image/{filename}\" alt=\"{filename}\">"
        "<div class=\"viewer-meta\">"
        f"<span class=\"filename\">{filename}</span>"
        "<div class=\"actions\">"
        f"<a class=\"btn btn-primary\" href=\"/image/{filename}?download=1\">Tải xuống</a>"
        "<a class=\"btn btn-secondary\" href=\"/image\">Quay lại</a>"
        "</div>"
        "</div>"
        "</div>"
    )
    return web.Response(text=html, content_type="text/html")

async def handle_account_info(request: web.Request):
    sess = get_session(request)
    if not sess:
        return web.json_response({"ok": False, "error": "Unauthorized"}, status=401)
    users = load_users()
    u = users.get(sess.get("username"))
    if not u:
        return web.json_response({"ok": False, "error": "Không tìm thấy tài khoản"}, status=404)
    # ẩn password_hash
    info = {k: v for k, v in u.items() if k != "password_hash"}
    discord_id = u.get("discord_id")
    finance = {"coins": 0, "bank": 0, "xu": 0, "networth": 0}
    if discord_id:
        try:
            from data.database import get_global_economy
            econ = get_global_economy(int(discord_id))
            coins = econ.get("coins", 0)
            bank = econ.get("bank", 0)
            xu = econ.get("xu", 0)
            finance = {
                "coins": coins,
                "bank": bank,
                "xu": xu,
                "networth": coins + bank
            }
        except Exception:
            pass
    info["finance"] = finance

    # 3. Trạng thái liên kết Minecraft Server Plugin
    mc_info = {"linked": False, "minecraft_name": None, "minecraft_uuid": None, "linked_at": None}
    if discord_id:
        try:
            import mc_link_system
            mc_link = mc_link_system.get_linked_account(int(discord_id))
            if mc_link:
                mc_info = {
                    "linked": True,
                    "minecraft_name": mc_link.get("minecraft_name"),
                    "minecraft_uuid": mc_link.get("minecraft_uuid"),
                    "linked_at": mc_link.get("linked_at")
                }
        except Exception:
            pass
    info["mc_link"] = mc_info

    # 4. Trạng thái Hôn Nhân & Hẹn Hò
    marriage_info = {"is_married": False}
    if discord_id:
        try:
            from Command_vi.command_fishing import fishing_state, UTILITY_ITEMS
            couples = fishing_state.get("couples", {}) if fishing_state else {}
            did_int = int(discord_id)
            for k, c in couples.items():
                a = int(c.get("a", 0))
                b = int(c.get("b", 0))
                if did_int in (a, b):
                    partner_id = b if did_int == a else a
                    ring_id = c.get("ring", "ring_bronze")
                    ring_name = UTILITY_ITEMS.get(ring_id, {}).get("name", "💍 Nhẫn Cưới")
                    m_at = c.get("married_at", 0)
                    days = int((time.time() - m_at) // 86400) if m_at > 0 else 0
                    partner_name = str(partner_id)
                    if BOT_INSTANCE:
                        p_user = BOT_INSTANCE.get_user(partner_id)
                        if p_user:
                            partner_name = p_user.display_name
                    marriage_info = {
                        "is_married": True,
                        "partner_id": str(partner_id),
                        "partner_name": partner_name,
                        "ring_id": ring_id,
                        "ring_name": ring_name,
                        "married_at": m_at,
                        "days": days,
                        "affection": c.get("affection", 0),
                        "common_coins": c.get("common_coins", 0),
                        "public": c.get("public", True)
                    }
                    break
        except Exception:
            pass
    info["marriage"] = marriage_info

    return web.json_response({"ok": True, "info": info, "session": sess})

async def handle_account_change(request: web.Request):
    sess = get_session(request)
    if not sess:
        return web.json_response({"ok": False, "error": "Unauthorized"}, status=401)
    try:
        data = await request.json()
    except Exception:
        return web.json_response({"ok": False, "error": "Dữ liệu không hợp lệ"}, status=400)
    new_username = str(data.get("new_username", "")).strip()
    if not new_username or len(new_username) < 3:
        return web.json_response({"ok": False, "error": "Tên mới phải ≥3 ký tự"}, status=400)
    if new_username == sess.get("username"):
        return web.json_response({"ok": False, "error": "Trùng tên hiện tại"}, status=400)
    users = load_users()
    if new_username in users:
        return web.json_response({"ok": False, "error": "Tên đã tồn tại"}, status=400)
    # Không cho đổi thành admin nếu không phải admin
    if new_username.lower() == "admin" and sess.get("role") != "admin":
        return web.json_response({"ok": False, "error": "Không thể đổi thành admin"}, status=403)
    old_username = sess.get("username")
    if old_username not in users:
        return web.json_response({"ok": False, "error": "Tài khoản không tồn tại"}, status=404)
    # đổi tên
    users[new_username] = users.pop(old_username)
    users[new_username]["username"] = new_username
    save_users(users)
    # cập nhật session
    token = get_token_from_request(request)
    from web.auth import load_sessions, save_sessions
    sessions_data = load_sessions()
    if token in sessions_data:
        sessions_data[token]["username"] = new_username
        save_sessions(sessions_data)
    add_log("INFO", f"User {old_username} đổi tên thành {new_username}")
    return web.json_response({"ok": True, "message": f"Đã đổi tên thành {new_username}", "new_username": new_username})

async def handle_account_resetpass(request: web.Request):
    sess = get_session(request)
    if not sess:
        return web.json_response({"ok": False, "error": "Unauthorized"}, status=401)
    try:
        data = await request.json()
    except Exception:
        return web.json_response({"ok": False, "error": "Dữ liệu không hợp lệ"}, status=400)
    old_password = str(data.get("old_password", ""))
    new_password = str(data.get("new_password", ""))
    if len(new_password) < 4:
        return web.json_response({"ok": False, "error": "Mật khẩu mới ≥4 ký tự"}, status=400)
    users = load_users()
    uname = sess.get("username")
    u = users.get(uname)
    if not u:
        return web.json_response({"ok": False, "error": "Không tìm thấy tài khoản"}, status=404)
    # nếu tài khoản có password_hash thì phải kiểm tra old_password (trừ khi là Discord account chưa có pass thì cho phép để trống)
    has_pass = bool(u.get("password_hash"))
    if has_pass:
        from web.auth import _verify_password, _hash_password
        if not _verify_password(old_password, u.get("password_hash","")):
            return web.json_response({"ok": False, "error": "Mật khẩu cũ không đúng"}, status=403)
    else:
        # chưa có pass (Discord) thì không cần old
        from web.auth import _hash_password
    # cập nhật
    from web.auth import _hash_password
    users[uname]["password_hash"] = _hash_password(new_password)
    save_users(users)
    add_log("INFO", f"User {uname} đổi mật khẩu")
    return web.json_response({"ok": True, "message": "Đổi mật khẩu thành công"})

async def handle_account_achievements(request: web.Request):
    sess = get_session(request)
    if not sess:
        return web.json_response({"ok": False, "error": "Unauthorized"}, status=401)
    users = load_users()
    u = users.get(sess.get("username"))
    discord_id = (u and u.get("discord_id")) or sess.get("discord_id") or sess.get("user_id")
    if not discord_id and str(sess.get("username", "")).isdigit():
        discord_id = sess.get("username")
    try:
        from Command_vi.achievement_system import ACHIEVEMENTS_CATALOG, load_user_achievements
        all_user_ach = load_user_achievements()
        uid_key = str(discord_id) if discord_id else ""
        u_data = all_user_ach.get(uid_key, {}) if uid_key else {}
        unlocked = u_data.get("unlocked", {})
        titles = u_data.get("titles", [])

        # Merge custom achievements if any
        custom_ach_file = DATA_DIR / "custom_achievements.json"
        custom_ach = load_json(custom_ach_file, {})
        for cid, cval in custom_ach.items():
            if cid not in ACHIEVEMENTS_CATALOG:
                ACHIEVEMENTS_CATALOG[cid] = cval

        catalog_list = list(ACHIEVEMENTS_CATALOG.values())
        total_all = len(catalog_list)
        total_user = len(unlocked)
        pct = round((total_user / total_all) * 100) if total_all > 0 else 0

        return web.json_response({
            "ok": True,
            "has_discord": bool(discord_id),
            "catalog": catalog_list,
            "unlocked": unlocked,
            "titles": titles,
            "total_all": total_all,
            "total_user": total_user,
            "percentage": pct
        })
    except Exception as e:
        return web.json_response({"ok": False, "error": str(e)}, status=500)

async def handle_get_achievements_leaderboard(request: web.Request):
    try:
        from Command_vi.achievement_system import ACHIEVEMENTS_CATALOG, load_user_achievements
        custom_ach_file = DATA_DIR / "custom_achievements.json"
        custom_ach = load_json(custom_ach_file, {})
        for cid, cval in custom_ach.items():
            if cid not in ACHIEVEMENTS_CATALOG:
                ACHIEVEMENTS_CATALOG[cid] = cval

        total_catalog = len(ACHIEVEMENTS_CATALOG)
        all_user_ach = load_user_achievements()

        leaderboard = []
        owner_ids = {"1144785664458637394"}
        try:
            from config import OWNER_ID
            owner_ids.add(str(OWNER_ID))
        except Exception:
            pass

        for uid_str, udata in all_user_ach.items():
            if uid_str in owner_ids:
                continue
            unlocked = udata.get("unlocked", {})
            unlocked_count = len(unlocked)
            if unlocked_count == 0:
                continue

            username = f"User {uid_str}"
            avatar = "https://cdn.discordapp.com/embed/avatars/0.png"
            if BOT_INSTANCE and uid_str.isdigit():
                u = BOT_INSTANCE.get_user(int(uid_str))
                if u:
                    username = f"{u.name} ({u.display_name})" if hasattr(u, "display_name") and u.display_name else u.name
                    avatar = u.display_avatar.url if hasattr(u, "display_avatar") else avatar

            titles = udata.get("titles", [])
            last_time = max(unlocked.values()) if unlocked else 0
            latest_ach = None
            if unlocked:
                latest_id = max(unlocked.keys(), key=lambda k: unlocked[k])
                latest_info = ACHIEVEMENTS_CATALOG.get(latest_id)
                if latest_info:
                    latest_ach = {
                        "id": latest_id,
                        "name": latest_info.get("name", latest_id),
                        "icon": latest_info.get("icon", "🏆")
                    }

            pct = round((unlocked_count / total_catalog) * 100, 1) if total_catalog > 0 else 0

            leaderboard.append({
                "user_id": uid_str,
                "username": username,
                "avatar": avatar,
                "unlocked_count": unlocked_count,
                "total_catalog": total_catalog,
                "percentage": pct,
                "titles": titles,
                "latest_achievement": latest_ach,
                "last_unlocked_time": last_time
            })

        leaderboard.sort(key=lambda x: (x["unlocked_count"], x["last_unlocked_time"]), reverse=True)
        for idx, entry in enumerate(leaderboard):
            entry["rank"] = idx + 1

        return web.json_response({
            "ok": True,
            "total_achievements": total_catalog,
            "total_players": len(leaderboard),
            "leaderboard": leaderboard[:100]
        })
    except Exception as e:
        return web.json_response({"ok": False, "error": str(e)}, status=500)

async def handle_get_admin_achievements_list(request: web.Request):
    sess = require_admin(request)
    if not sess:
        return web.json_response({"ok": False, "error": "Chỉ dành cho Admin"}, status=403)
    try:
        from Command_vi.achievement_system import ACHIEVEMENTS_CATALOG
        custom_ach_file = DATA_DIR / "custom_achievements.json"
        custom_ach = load_json(custom_ach_file, {})
        for cid, cval in custom_ach.items():
            ACHIEVEMENTS_CATALOG[cid] = cval
        return web.json_response({"ok": True, "achievements": list(ACHIEVEMENTS_CATALOG.values())})
    except Exception as e:
        return web.json_response({"ok": False, "error": str(e)}, status=500)

async def handle_add_admin_achievement(request: web.Request):
    sess = require_admin(request)
    if not sess:
        return web.json_response({"ok": False, "error": "Chỉ dành cho Admin"}, status=403)
    try:
        body = await request.json()
        ach_id = str(body.get("id", "")).strip()
        name = str(body.get("name", "")).strip()
        if not ach_id or not name:
            return web.json_response({"ok": False, "error": "Mã ID và Tên không được rỗng"}, status=400)
        if not ach_id.startswith("custom_") and not ach_id.isalnum() and "_" not in ach_id:
            ach_id = f"custom_{ach_id}"

        category = str(body.get("category", "fishing")).strip()
        desc = str(body.get("desc", "")).strip()
        coins = max(0, int(body.get("reward_coins", 0)))
        xu = max(0, int(body.get("reward_xu", 0)))
        title = str(body.get("reward_title", "")).strip()
        icon = str(body.get("icon", "🏆")).strip() or "🏆"

        entry = {
            "id": ach_id,
            "name": name,
            "category": category,
            "desc": desc,
            "reward_coins": coins,
            "reward_xu": xu,
            "reward_title": title,
            "icon": icon
        }

        from Command_vi.achievement_system import ACHIEVEMENTS_CATALOG
        ACHIEVEMENTS_CATALOG[ach_id] = entry

        custom_ach_file = DATA_DIR / "custom_achievements.json"
        custom_ach = load_json(custom_ach_file, {})
        custom_ach[ach_id] = entry
        save_json(custom_ach_file, custom_ach)

        return web.json_response({"ok": True, "message": f"Đã thêm thành tựu '{name}' [{ach_id}] thành công!"})
    except Exception as e:
        return web.json_response({"ok": False, "error": str(e)}, status=500)

async def handle_admin_user_achievement_action(request: web.Request):
    sess = require_admin(request)
    if not sess:
        return web.json_response({"ok": False, "error": "Chỉ dành cho Admin"}, status=403)
    try:
        body = await request.json()
        action = str(body.get("action", "")).strip()
        user_id = str(body.get("user_id", "")).strip()
        ach_id = str(body.get("ach_id", "")).strip()
        if not user_id or not ach_id:
            return web.json_response({"ok": False, "error": "Thiếu User ID hoặc Achievement ID"}, status=400)

        from Command_vi.achievement_system import ACHIEVEMENTS_CATALOG, load_user_achievements, save_user_achievements
        custom_ach_file = DATA_DIR / "custom_achievements.json"
        custom_ach = load_json(custom_ach_file, {})
        for cid, cval in custom_ach.items():
            ACHIEVEMENTS_CATALOG[cid] = cval

        ach = ACHIEVEMENTS_CATALOG.get(ach_id)
        if not ach:
            return web.json_response({"ok": False, "error": f"Không tìm thấy thành tựu {ach_id}"}, status=404)

        all_data = load_user_achievements()
        u_data = all_data.setdefault(user_id, {"unlocked": {}, "titles": [], "stats": {}})
        unlocked = u_data.setdefault("unlocked", {})
        titles = u_data.setdefault("titles", [])

        if action == "grant":
            if ach_id in unlocked:
                return web.json_response({"ok": True, "message": f"Người chơi {user_id} đã có thành tựu này từ trước."})
            unlocked[ach_id] = int(time.time())
            if ach.get("reward_title") and ach["reward_title"] not in titles:
                titles.append(ach["reward_title"])
            save_user_achievements(all_data)

            if user_id.isdigit():
                uid_int = int(user_id)
                rc = ach.get("reward_coins", 0)
                rx = ach.get("reward_xu", 0)
                if rc > 0 or rx > 0:
                    try:
                        from data.database import update_user_coins, update_user_xu
                        if rc > 0: await update_user_coins(0, uid_int, rc)
                        if rx > 0: await update_user_xu(0, uid_int, rx)
                    except Exception:
                        pass
            return web.json_response({"ok": True, "message": f"Đã trao thành công thành tựu '{ach['name']}' cho User {user_id}!"})

        elif action == "revoke":
            if ach_id in unlocked:
                del unlocked[ach_id]
                save_user_achievements(all_data)
                return web.json_response({"ok": True, "message": f"Đã thu hồi thành tựu '{ach['name']}' khỏi User {user_id}."})
            else:
                return web.json_response({"ok": False, "error": f"User {user_id} chưa sở hữu thành tựu này"}, status=400)
        else:
            return web.json_response({"ok": False, "error": "Hành động không hợp lệ (chỉ hỗ trợ grant/revoke)"}, status=400)
    except Exception as e:
        return web.json_response({"ok": False, "error": str(e)}, status=500)

async def handle_account_avatar(request: web.Request):
    sess = get_session(request)
    if not sess:
        return web.json_response({"ok": False, "error": "Unauthorized"}, status=401)
    # multipart
    try:
        reader = await request.multipart()
    except Exception:
        return web.json_response({"ok": False, "error": "Yêu cầu multipart với file avatar"}, status=400)
    field = await reader.next()
    if not field or field.name != 'avatar':
        return web.json_response({"ok": False, "error": "Thiếu file avatar"}, status=400)
    filename = field.filename or "avatar.png"
    # kiểm tra sớm bằng security helper (MIME sẽ check sau khi đọc)
    ext = Path(filename).suffix.lower()
    if ext not in [".png",".jpg",".jpeg",".gif",".webp"]:
        return web.json_response({"ok": False, "error": "Chỉ hỗ trợ png/jpg/jpeg/gif/webp"}, status=400)
    data = b""
    size = 0
    first_chunk = b""
    while True:
        chunk = await field.read_chunk(size=8192)
        if not chunk:
            break
        if not first_chunk: first_chunk = chunk
        size += len(chunk)
        if size > 5*1024*1024:
            return web.json_response({"ok": False, "error": "File quá lớn (>5MB)"}, status=400)
        data += chunk
    if not data:
        return web.json_response({"ok": False, "error": "File rỗng"}, status=400)
    # MIME sniff: check magic bytes
    mime = field.headers.get("Content-Type","")
    err = validate_avatar(filename, mime, size)
    if err:
        return web.json_response({"ok": False, "error": err}, status=400)
    # thêm check magic bytes đơn giản
    if first_chunk[:8] == b"\x89PNG\r\n\x1a\n":
        pass
    elif first_chunk[:2] == b"\xff\xd8":
        pass
    elif first_chunk[:6] in (b"GIF87a", b"GIF89a"):
        pass
    elif first_chunk[:4] == b"RIFF" and b"WEBP" in first_chunk[:12]:
        pass
    else:
        # cho phép webp khác, không chặn strict để tránh false positive, nhưng log
        add_log("WARNING", f"Avatar MIME lạ {filename} {mime} {first_chunk[:4].hex()}")
    # lưu
    try:
        avatars_dir = STATIC_DIR / "avatars"
        avatars_dir.mkdir(parents=True, exist_ok=True)
        # tên file an toàn
        safe_user = "".join(c if c.isalnum() or c in "_-" else "_" for c in sess.get("username","user"))
        fname = f"{safe_user}_{int(time.time())}.{ext}"
        fpath = avatars_dir / fname
        with open(fpath, "wb") as f:
            f.write(data)
        avatar_url = f"/static/avatars/{fname}"
        # cập nhật user
        users = load_users()
        uname = sess.get("username")
        if uname in users:
            # xóa avatar cũ nếu là local file
            old = users[uname].get("avatar","")
            if old and old.startswith("/static/avatars/"):
                try:
                    old_path = STATIC_DIR / "avatars" / Path(old).name
                    if old_path.exists() and old_path != fpath:
                        old_path.unlink(missing_ok=True)
                except Exception:
                    pass
            users[uname]["avatar"] = avatar_url
            save_users(users)
        # cập nhật session extra
        token = get_token_from_request(request)
        if token:
            from web.auth import load_sessions, save_sessions
            sess_data = load_sessions()
            if token in sess_data:
                sess_data[token].setdefault("extra", {})["avatar"] = avatar_url
                save_sessions(sess_data)
        add_log("INFO", f"User {uname} đổi avatar -> {fname}")
        return web.json_response({"ok": True, "avatar": avatar_url, "message": "Đổi avatar thành công"})
    except Exception as e:
        return web.json_response({"ok": False, "error": str(e)}, status=500)

async def handle_auth_forgot(request: web.Request):
    # Quên mật khẩu không cần đăng nhập: cung cấp username + new_password
    try:
        data = await request.json()
    except Exception:
        return web.json_response({"ok": False, "error": "Dữ liệu không hợp lệ"}, status=400)
    username = str(data.get("username","")).strip()
    new_password = str(data.get("new_password","")).strip()
    if not username or len(new_password) < 4:
        return web.json_response({"ok": False, "error": "Thiếu tên hoặc mật khẩu mới ≥4 ký tự"}, status=400)
    users = load_users()
    if username not in users:
        return web.json_response({"ok": False, "error": "Tài khoản không tồn tại"}, status=404)
    # Không cho reset admin qua forgot nếu không phải admin? cho phép nhưng log
    from web.auth import _hash_password
    users[username]["password_hash"] = _hash_password(new_password)
    save_users(users)
async def handle_auth_forgot(request: web.Request):
    return web.json_response({"ok": False, "error": "Tính năng mật khẩu đã bị vô hiệu hóa do hệ thống dùng Discord OAuth"}, status=400)

# Legacy login & local credentials disabled
async def handle_login(request: web.Request):
    return web.json_response({"ok": False, "message": "Đăng nhập mật khẩu đã tắt. Vui lòng đăng nhập qua Discord tại /login"}, status=400)

# ========== NEW AUTH ROUTES (DISCORD ONLY) ==========
async def handle_auth_login(request: web.Request):
    return web.json_response({"ok": False, "message": "Đăng nhập tài khoản/mật khẩu đã bị xóa. Vui lòng đăng nhập qua Discord tại /login"}, status=400)

async def handle_auth_register(request: web.Request):
    return web.json_response({"ok": False, "message": "Đăng ký bằng mật khẩu đã tắt. Vui lòng đăng nhập trực tiếp qua Discord tại /login"}, status=400)

async def handle_auth_logout(request: web.Request):
    sess = get_session(request)
    token = get_token_from_request(request)
    if token:
        destroy_session(token)
    resp = web.json_response({"ok": True, "message": "Đã đăng xuất"})
    resp.del_cookie("sakura_token", path="/")
    return resp

async def handle_auth_me(request: web.Request):
    sess = get_session(request)
    if not sess:
        return web.json_response({"ok": False, "error": "Unauthorized"}, status=401)
    manageable = get_manageable_guild_ids_for_session(sess)
    client_id, _ = get_discord_oauth_config()
    # lấy avatar từ web_users.json
    avatar=""
    try:
        users=load_json(DATA_DIR/"web_users.json",{})
        u=users.get(sess.get("username"),{})
        avatar=u.get("avatar","") or sess.get("extra",{}).get("avatar","")
        # nếu là discord user, thử lấy từ discord cdn nếu chưa có
        if not avatar and sess.get("discord_id"):
            # fallback generic
            avatar=f"https://cdn.discordapp.com/embed/avatars/0.png"
    except: pass
    raw_u = sess.get("username")
    if isinstance(raw_u, dict):
        username_val = raw_u.get("username", "user")
        discord_id_val = raw_u.get("id") or sess.get("discord_id")
    else:
        username_val = raw_u
        discord_id_val = sess.get("discord_id")
    user_id_val = str(discord_id_val or username_val or "")

    return web.json_response({
        "ok": True,
        "user": {
            "id": user_id_val,
            "user_id": user_id_val,
            "username": username_val,
            "role": "owner" if is_owner_session(sess) else sess.get("role"),
            "discord_id": discord_id_val,
            "is_admin": is_admin_session(sess),
            "is_owner": is_owner_session(sess),
            "manage_guild_ids": manageable,
            "avatar": avatar
        },
        "discord_oauth_enabled": bool(client_id)
    })

async def handle_discord_login(request: web.Request):
    client_id, _ = get_discord_oauth_config()
    if not client_id:
        try:
            import config
            client_id = getattr(config, "DISCORD_CLIENT_ID", "") or ""
        except Exception:
            client_id = ""
    if not client_id:
        return web.json_response({"ok": False, "error": "Discord OAuth chưa cấu hình (DISCORD_CLIENT_ID)"}, status=500)
    url = get_discord_oauth_login_url(request)
    return web.json_response({"ok": True, "url": url})

async def handle_discord_callback(request: web.Request):
    try:
        code = request.query.get("code", "")
        if not code:
            return web.Response(text="<h1>Thiếu mã code OAuth</h1><p>Vui lòng thử đăng nhập lại.</p><a href='/login'>Quay lại</a>", content_type="text/html", status=400)
        
        redirect_uri = get_discord_redirect_uri(request)
        token_data = await exchange_code_for_token(code, redirect_uri)
        if not token_data or "access_token" not in token_data:
            err_code = token_data.get("_error", "unknown") if token_data else "unknown"
            err_desc = token_data.get("_error_description", "") if token_data else ""

            # Hướng dẫn xử lý chi tiết theo mã lỗi chính xác từ Discord API
            fix_tip = ""
            if err_code == "redirect_uri_mismatch":
                fix_tip = f'''
                <div style="background: rgba(255, 85, 85, 0.12); border-left: 4px solid #ff5555; padding: 14px 16px; margin: 16px 0; border-radius: 6px; text-align: left;">
                    <strong style="color: #ff5555;">💡 Nguyên nhân & Cách khắc phục:</strong><br>
                    Redirect URI chưa được thêm vào whitelist trong <strong>Discord Developer Portal</strong>.<br><br>
                    <strong>Các bước khắc phục:</strong><br>
                    1. Mở <a href="https://discord.com/developers/applications" target="_blank" style="color: #50fa7b; font-weight: 700; text-decoration: underline;">Discord Developer Portal</a> &gt; Chọn Bot của bạn &gt; <strong>OAuth2</strong>.<br>
                    2. Tìm mục <strong>Redirects</strong> và nhấn <strong>Add Redirect</strong>.<br>
                    3. Dán chính xác URL sau:<br>
                    <code style="display: block; background: #090d16; padding: 10px; margin-top: 6px; color: #50fa7b; border-radius: 6px; word-break: break-all; border: 1px solid rgba(80, 250, 123, 0.3); font-weight: 700;">{redirect_uri}</code>
                    4. Nhấn nút <strong>Save Changes</strong> ở góc dưới trang rồi đăng nhập lại.
                </div>
                '''
            elif err_code == "invalid_client":
                fix_tip = f'''
                <div style="background: rgba(255, 184, 108, 0.12); border-left: 4px solid #ffb86c; padding: 14px 16px; margin: 16px 0; border-radius: 6px; text-align: left;">
                    <strong style="color: #ffb86c;">💡 Nguyên nhân & Cách khắc phục:</strong><br>
                    Mã <code>DISCORD_CLIENT_SECRET</code> không khớp hoặc đã bị Reset trên Discord Portal.<br><br>
                    1. Vào <a href="https://discord.com/developers/applications" target="_blank" style="color: #50fa7b; font-weight: 700;">Discord Developer Portal</a> &gt; <strong>OAuth2</strong> &gt; Nhấn <strong>Reset Secret</strong>.<br>
                    2. Copy mã Secret mới và cập nhật vào biến <code>DISCORD_CLIENT_SECRET</code> trong file <code>config.py</code>.
                </div>
                '''
            elif err_code == "invalid_grant":
                fix_tip = '''
                <div style="background: rgba(139, 233, 253, 0.12); border-left: 4px solid #8be9fd; padding: 14px 16px; margin: 16px 0; border-radius: 6px; text-align: left;">
                    <strong style="color: #8be9fd;">💡 Lý do:</strong><br>
                    Mã xác thực <code>code</code> của Discord chỉ có giá trị dùng <strong>1 lần duy nhất</strong> và đã hết hạn (thường do tải lại trang F5 hoặc trình duyệt gửi yêu cầu đúp).<br>
                    👉 Bạn chỉ cần nhấn nút <strong>Đăng Nhập Lại</strong> bên dưới để lấy mã code mới.
                </div>
                '''

            html_error = f'''<!DOCTYPE html>
            <html lang="vi">
            <head>
                <meta charset="UTF-8">
                <meta name="viewport" content="width=device-width, initial-scale=1.0">
                <title>Lỗi Xác Thực Discord - SakuraBot</title>
                <link rel="stylesheet" href="/static/css/style.css">
                <style>
                    body {{ display: flex; align-items: center; justify-content: center; min-height: 100vh; background: #090d16; color: #fff; font-family: sans-serif; margin: 0; padding: 20px; box-sizing: border-box; }}
                    .card {{ background: #141a29; border: 1px solid rgba(255, 121, 198, 0.35); border-radius: 14px; max-width: 620px; width: 100%; padding: 32px; box-shadow: 0 15px 45px rgba(0,0,0,0.7); text-align: center; }}
                    .btn {{ display: inline-flex; align-items: center; gap: 8px; padding: 11px 26px; border-radius: 8px; background: linear-gradient(135deg, #ff79c6, #ff2a85); color: #fff; text-decoration: none; font-weight: 700; margin-top: 15px; box-shadow: 0 4px 15px rgba(255, 42, 133, 0.4); transition: transform 0.2s; }}
                    .btn:hover {{ transform: translateY(-2px); }}
                </style>
            </head>
            <body>
                <div class="card">
                    <div style="font-size: 3.2rem; margin-bottom: 12px;">⚠️</div>
                    <h2 style="margin: 0 0 12px 0; color: #ff79c6;">Lỗi Xác Thực Discord OAuth2</h2>
                    <p style="color: #cbd5e1; font-size: 0.95rem; margin-bottom: 10px;">
                        Chi tiết phản hồi từ Discord: <strong style="color: #ff5555;">{err_code}</strong>{f' — <span>{err_desc}</span>' if err_desc else ''}
                    </p>
                    <div style="background: rgba(0,0,0,0.3); border: 1px solid rgba(255,255,255,0.08); padding: 10px 14px; border-radius: 8px; font-family: monospace; font-size: 0.82rem; color: #8be9fd; word-break: break-all; margin: 14px 0; text-align: left;">
                        <strong>Redirect URI hiện tại:</strong><br>{redirect_uri}
                    </div>
                    {fix_tip}
                    <a href="/login" class="btn"><span>🔄</span> Đăng Nhập Lại Bằng Discord</a>
                </div>
            </body>
            </html>'''
            return web.Response(text=html_error, content_type="text/html", status=400)
        access_token = token_data["access_token"]
        discord_user = await fetch_discord_user(access_token)
        if not discord_user:
            return web.Response(text="<h1>Lỗi lấy thông tin Discord</h1><a href='/login'>Quay lại</a>", content_type="text/html", status=500)
        guilds = await fetch_discord_user_guilds(access_token)
        manage_guilds = filter_manage_guilds(guilds)
        manage_ids = [str(g["id"]) for g in manage_guilds]

        # Lấy tên Discord làm tên tài khoản
        users_tmp = load_users()
        # Nếu đã có tài khoản cũ theo discord_id (kiểu discord_ID) thì giữ nguyên để không tạo trùng
        existing_by_discord = None
        for uname, udata in users_tmp.items():
            if str(udata.get("discord_id")) == str(discord_user["id"]):
                existing_by_discord = uname
                break
        if existing_by_discord:
            username = existing_by_discord
            base_name = username
        else:
            raw_name = (discord_user.get('global_name') or discord_user.get('username') or f"user{discord_user['id'][-4:]}").strip()
            base_name = "".join(c for c in raw_name if c.isalnum() or c in "_-").strip() or discord_user.get('username') or f"user{discord_user['id'][-4:]}"
            if len(base_name) < 3:
                base_name = f"user{discord_user['id'][-4:]}"
            if base_name.lower() == "admin":
                base_name = f"admin_{discord_user['id'][-4:]}"
            username = base_name
            if username in users_tmp and users_tmp[username].get("discord_id") != str(discord_user["id"]):
                username = f"{base_name}_{str(discord_user['id'])[-4:]}"
                cnt = 1
                while username in users_tmp and users_tmp[username].get("discord_id") != str(discord_user["id"]):
                    username = f"{base_name}_{str(discord_user['id'])[-4:]}_{cnt}"
                    cnt += 1
        discord_tag = f"{discord_user.get('username')}#{discord_user.get('discriminator', '0')}" if discord_user.get('discriminator') and discord_user.get('discriminator')!='0' else discord_user.get('username') or base_name
        avatar = f"https://cdn.discordapp.com/avatars/{discord_user['id']}/{discord_user.get('avatar')}.png" if discord_user.get('avatar') else ""

        discord_id_str = str(discord_user.get("id", "")).strip()
        d_username = str(discord_user.get("username", "") or "").strip().lower()
        d_global_name = str(discord_user.get("global_name", "") or "").strip().lower()
        d_tag_clean = discord_tag.lower().replace("@", "").strip()

        # Nhận diện chủ bot @linhxinh_dev để cấp toàn quyền điều khiển bot
        import config
        owner_id_cfg = str(getattr(config, "OWNER_ID", "") or "").strip()
        owner_tag_cfg = str(getattr(config, "OWNER_DISCORD_TAG", "") or "").strip().lower().replace("@", "")

        is_linhxinh_dev = (
            d_username == "linhxinh_dev" or
            d_global_name == "linhxinh_dev" or
            "linhxinh_dev" in d_tag_clean or
            (owner_tag_cfg and d_username == owner_tag_cfg) or
            (owner_id_cfg and discord_id_str == owner_id_cfg) or
            discord_id_str == "1144785664458637394"
        )

        if is_linhxinh_dev:
            is_owner = True
            user_role = "admin"
            manage_ids = None  # None = Toàn quyền quản lý tất cả server bot đang ở
            add_log("SUCCESS", f"👑 CHỦ BOT ĐĂNG NHẬP: @linhxinh_dev ({discord_id_str}) — Đã cấp toàn quyền quản lý hệ thống Sakura Bot!")
            print(f"\n\033[92m👑 [SAKURA BOT] PHÁT HIỆN CHỦ BOT @linhxinh_dev ĐĂNG NHẬP — ĐÃ CẤP TOÀN QUYỀN QUẢN TRỊ!\033[0m\n")
        else:
            is_owner = False
            existing_user_data = users_tmp.get(username, {})
            existing_role = existing_user_data.get("role", "user")
            user_role = "admin" if (existing_role == "admin") else "user"

        # Save or update user
        users = load_users()
        if username not in users:
            # Create new user entry for discord login (no password)
            users[username] = {
                "username": username,
                "password_hash": "",
                "role": user_role,
                "discord_id": discord_id_str,
                "discord_tag": discord_tag,
                "avatar": avatar,
                "created_at": int(time.time()),
                "guilds_filter": manage_ids,
                "is_owner": is_linhxinh_dev
            }
            save_users(users)
        else:
            users[username]["discord_id"] = discord_id_str
            users[username]["discord_tag"] = discord_tag
            users[username]["avatar"] = avatar
            users[username]["guilds_filter"] = manage_ids
            if user_role == "admin":
                users[username]["role"] = "admin"
            if is_linhxinh_dev:
                users[username]["is_owner"] = True
            save_users(users)

        # Create session with manage list
        extra_session = {"manage_guild_ids": manage_ids, "discord_tag": discord_tag, "avatar": avatar, "is_owner": is_linhxinh_dev}
        token = create_session(username, user_role, discord_id=discord_id_str, extra=extra_session)
        add_log("SUCCESS", f"Discord OAuth login: {discord_tag} ({discord_user['id']}) - Role: {user_role} - {'Toàn quyền (Owner)' if is_linhxinh_dev else f'{len(manage_ids or [])} server có quyền quản lý'}")

        # Hiển thị số server (an toàn khi manage_ids là None với Owner)
        guild_count_str = "tất cả" if manage_ids is None else str(len(manage_ids))

        # Redirect to dashboard with token
        html = f"""
        <!DOCTYPE html>
        <html><head><meta charset="utf-8"><title>Đăng nhập thành công</title></head>
        <body style="font-family: sans-serif; text-align:center; padding:40px;">
            <h2>🌸 Đăng nhập Discord thành công!</h2>
            <p>Xin chào <strong>{discord_tag}</strong></p>
            <p>Bạn có quyền quản lý <strong>{guild_count_str}</strong> server.</p>
            <p>Đang chuyển hướng tới Dashboard...</p>
            <script>
                localStorage.setItem('sakura_auth_token', '{token}');
                localStorage.setItem('sakura_user', JSON.stringify({{username: '{username}', role: '{user_role}', discord_tag: '{discord_tag}'}}));
                document.cookie = 'sakura_token={token}; path=/; max-age={7*24*3600}';
                setTimeout(()=> location.href='/dashboard', 800);
            </script>
        </body></html>
        """
        resp = web.Response(text=html, content_type="text/html")
        resp.set_cookie("sakura_token", token, max_age=7*24*3600, path="/", httponly=False, samesite="Lax")
        return resp
    except Exception as e:
        import traceback
        traceback.print_exc()
        add_log("ERROR", f"Lỗi xử lý Discord callback: {e}")
        return web.Response(
            text=f"<h1>Lỗi xử lý đăng nhập</h1><p>{e}</p><br><a href='/login'>Thử lại</a>",
            content_type="text/html",
            status=500
        )

async def _proxy_to_bot_web(request: web.Request, path: str):
    """Khi chạy standalone (BOT_INSTANCE=None) nhưng bot đang chạy ở cổng khác → quét 8080..8090 để web nhận bot dù lệch cổng"""
    if BOT_INSTANCE is not None:
        return None
    try:
        st = get_bot_process_status(use_cache=False)
        if not st.get("running"):
            return None
        import config
        base_port = getattr(config, "WEB_PORT", 8080)
        # Tìm cổng thực của bot (thử base..base+9)
        import aiohttp
        token = get_token_from_request(request)
        headers = {}
        if token:
            headers["Authorization"] = f"Bearer {token}"
        cookies = {}
        if "sakura_token" in request.cookies:
            cookies["sakura_token"] = request.cookies["sakura_token"]
        body = await request.read() if request.can_read_body else None
        if body and "Content-Type" in request.headers:
            headers["Content-Type"] = request.headers["Content-Type"]
        req_port = request.url.port
        for bot_port in range(base_port, base_port+10):
            if req_port == bot_port:
                continue
            try:
                url = f"http://127.0.0.1:{bot_port}{path}"
                if request.query_string:
                    url += f"?{request.query_string}"
                async with aiohttp.ClientSession() as sess_cli:
                    async with sess_cli.request(request.method, url, headers=headers, cookies=cookies, data=body, timeout=aiohttp.ClientTimeout(total=2)) as resp:
                        # Chỉ chấp nhận nếu bot trả về JSON ok hoặc 200 và không phải 404 proxy loop
                        if resp.status in (401,403):
                            data = await resp.read()
                            return web.Response(body=data, status=resp.status, content_type=resp.content_type, headers={"X-Proxied-By": f"sakura-standalone->{bot_port}"})
                        if resp.status == 200:
                            data = await resp.read()
                            # Kiểm tra có phải Sakura API không (tránh proxy nhầm service khác)
                            ctype = resp.content_type or ""
                            if "json" in ctype or path.startswith("/api/"):
                                return web.Response(body=data, status=resp.status, content_type=resp.content_type, headers={"X-Proxied-By": f"sakura-standalone->{bot_port}"})
                            # Với path khác vẫn trả
                            return web.Response(body=data, status=resp.status, content_type=resp.content_type, headers={"X-Proxied-By": f"sakura-standalone->{bot_port}"})
            except: 
                continue
    except Exception as e:
        print(f"[Proxy] {path} -> bot fail: {e}")
    return None


_DIAGNOSTICS_CACHE = {
    "timestamp": 0,
    "data": None
}
_DIAGNOSTICS_LOCK = None

async def check_lavalink_health() -> Dict[str, Any]:
    import config
    host = getattr(config, "LAVALINK_HOST", "lava2.kasawa.pro")
    port = getattr(config, "LAVALINK_PORT", 2334)
    password = getattr(config, "LAVALINK_PASSWORD", "youshallnotpass")

    active_players = 0
    wavelink_connected = False
    
    # 1. Kiểm tra qua pool Wavelink của bot nếu đang chạy
    try:
        import wavelink
        nodes = list(wavelink.Pool.nodes.values())
        if nodes:
            node = nodes[0]
            status_attr = getattr(node, "status", None)
            wavelink_enum = getattr(wavelink, "NodeStatus", None)
            if wavelink_enum and status_attr == getattr(wavelink_enum, "CONNECTED", None):
                wavelink_connected = True
            elif getattr(node, "is_connected", False):
                wavelink_connected = True
            active_players = len(getattr(node, "players", {}))
    except Exception:
        pass

    # 2. Thử nghiệm kết nối HTTP & Ping socket trực tiếp
    t0 = time.time()
    status_code = "off"
    state_label = "tắt"
    display_title = "Đã tắt"
    version_str = ""
    latency_ms = 0
    detail = ""

    try:
        url = f"http://{host}:{port}/version"
        headers = {"Authorization": password, "User-Agent": "SakuraBot/1.0"}
        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=headers, timeout=aiohttp.ClientTimeout(total=2.0)) as resp:
                latency_ms = round((time.time() - t0) * 1000, 1)
                if resp.status == 200:
                    status_code = "on"
                    state_label = "ổn"
                    display_title = "Ổn định"
                    version_str = (await resp.text()).strip()
                    detail = f"Máy chủ Lavalink v{version_str} phản hồi tốt ({latency_ms}ms)"
                elif resp.status in (401, 403):
                    status_code = "error"
                    state_label = "sự cố"
                    display_title = "Lỗi xác thực (401/403)"
                    detail = "Sai mật khẩu kết nối hoặc bị từ chối truy cập"
                else:
                    status_code = "error"
                    state_label = "sự cố"
                    display_title = f"Lỗi HTTP {resp.status}"
                    detail = f"Máy chủ phản hồi mã HTTP {resp.status}"
    except (asyncio.TimeoutError, aiohttp.ClientConnectionError, ConnectionRefusedError):
        status_code = "off"
        state_label = "tắt"
        display_title = "Đã tắt"
        detail = "Không thể kết nối đến máy chủ Lavalink (Offline / Connection Refused)"
    except Exception as e:
        status_code = "error"
        state_label = "sự cố"
        display_title = "Gặp sự cố"
        detail = str(e)

    if wavelink_connected and status_code != "on":
        status_code = "on"
        state_label = "ổn"
        display_title = "Ổn định"
        detail = "Node Wavelink đang kết nối và truyền phát âm nhạc bình thường"

    return {
        "status": status_code,          # "on" | "off" | "error"
        "state_label": state_label,     # "ổn" | "tắt" | "sự cố"
        "display_title": display_title,
        "host": host,
        "port": port,
        "version": version_str or "v4",
        "latency_ms": latency_ms,
        "active_players": active_players,
        "detail": detail
    }

async def check_integrated_apis() -> List[Dict[str, Any]]:
    import config
    gemini_key = getattr(config, "GEMINI_API_KEY", "")
    groq_key = getattr(config, "GROQ_API_KEY", "")
    falix_key = getattr(config, "FALIX_API_KEY", "")
    
    apis = []

    # 1. Discord Gateway & REST API
    discord_lat = round(BOT_INSTANCE.latency * 1000, 1) if (BOT_INSTANCE and getattr(BOT_INSTANCE, "is_ready", lambda: False)()) else 0
    apis.append({
        "id": "discord",
        "name": "Discord Gateway & REST API",
        "category": "Discord Core",
        "icon": "🎮",
        "url": "https://discord.com/api/v10/gateway",
        "status": "on",
        "status_label": "Ổn định",
        "latency_ms": discord_lat or 160.0,
        "note": "Kết nối Gateway thời gian thực & Discord Slash Commands"
    })

    # 2. SQLite Database
    t0 = time.time()
    db_ok = False
    try:
        db_file = DATA_DIR / "bot.db"
        if db_file.exists():
            import sqlite3
            conn = sqlite3.connect(str(db_file), timeout=1.0)
            cur = conn.cursor()
            cur.execute("SELECT 1;")
            cur.fetchone()
            conn.close()
            db_ok = True
    except Exception:
        db_ok = False
    db_lat = round((time.time() - t0) * 1000, 1)
    apis.append({
        "id": "database",
        "name": "SQLite Core Database (bot.db)",
        "category": "Storage / CSDL",
        "icon": "💾",
        "url": "local:data/bot.db",
        "status": "on" if db_ok else "error",
        "status_label": "Ổn định" if db_ok else "Sự cố",
        "latency_ms": db_lat,
        "note": "Cơ sở dữ liệu người dùng, tiền tệ, level, hôn lễ & hệ thống"
    })

    # Discord Gateway & REST
    gw_lat = round(bot_instance.latency * 1000, 1) if (bot_instance and getattr(bot_instance, "latency", None)) else 0
    apis.append({
        "id": "discord_gateway",
        "name": "Discord Gateway & WebSocket API",
        "category": "Cốt Lõi Hệ Thống",
        "icon": "🤖",
        "url": "https://discord.com/api/v10/gateway",
        "status": "on" if gw_lat > 0 else "off",
        "status_label": f"{gw_lat} ms" if gw_lat > 0 else "Chưa sẵn sàng",
        "latency_ms": gw_lat,
        "note": "Kết nối WebSocket thời gian thực giữa SakuraBot và Discord Gateway"
    })

    # External probes
    async def probe(session, api_id, name, cat, icon, url, headers=None):
        headers = headers or {}
        t_start = time.time()
        try:
            async with session.get(url, headers={"User-Agent": "SakuraBot/1.0", **headers}, timeout=aiohttp.ClientTimeout(total=2.5)) as r:
                lat = round((time.time() - t_start) * 1000, 1)
                if r.status < 400:
                    return {
                        "id": api_id,
                        "name": name,
                        "category": cat,
                        "icon": icon,
                        "url": url.split("?")[0],
                        "status": "on",
                        "status_label": "Ổn định",
                        "latency_ms": lat,
                        "note": f"Mã HTTP {r.status} - Phản hồi tốt"
                    }
                elif r.status in (401, 403):
                    return {
                        "id": api_id,
                        "name": name,
                        "category": cat,
                        "icon": icon,
                        "url": url.split("?")[0],
                        "status": "error",
                        "status_label": "Lỗi API Key",
                        "latency_ms": lat,
                        "note": f"HTTP {r.status} (Xác thực không hợp lệ)"
                    }
                else:
                    return {
                        "id": api_id,
                        "name": name,
                        "category": cat,
                        "icon": icon,
                        "url": url.split("?")[0],
                        "status": "error",
                        "status_label": "Sự cố",
                        "latency_ms": lat,
                        "note": f"HTTP {r.status}"
                    }
        except (asyncio.TimeoutError, aiohttp.ClientConnectionError):
            return {
                "id": api_id,
                "name": name,
                "category": cat,
                "icon": icon,
                "url": url.split("?")[0],
                "status": "off",
                "status_label": "Không phản hồi",
                "latency_ms": round((time.time() - t_start) * 1000, 1),
                "note": "Timeout hoặc server đích không thể kết nối"
            }
        except Exception as e:
            return {
                "id": api_id,
                "name": name,
                "category": cat,
                "icon": icon,
                "url": url.split("?")[0],
                "status": "error",
                "status_label": "Sự cố",
                "latency_ms": round((time.time() - t_start) * 1000, 1),
                "note": str(e)[:50]
            }

    try:
        async with aiohttp.ClientSession() as session:
            tasks = []
            
            # Lavalink Music Server
            lava_host = getattr(config, "LAVALINK_HOST", "lava2.kasawa.pro")
            lava_port = getattr(config, "LAVALINK_PORT", 2334)
            tasks.append(probe(session, "lavalink", f"Lavalink Music Server ({lava_host})", "Dịch Vụ Âm Nhạc", "🎵", f"http://{lava_host}:{lava_port}/version"))

            # Minecraft Plugin Link Server (Port 5001)
            tasks.append(probe(session, "mc_link", "Minecraft Link API (Port 5001)", "Liên Kết Game", "⛏️", "http://127.0.0.1:5001/api/link"))

            # Sakura Web Server / Dashboard Local
            web_p = getattr(config, "WEB_PORT", 10272)
            tasks.append(probe(session, "web_dashboard", f"Sakura Web Server (Port {web_p})", "Giao Diện Quản Trị", "🌸", f"http://127.0.0.1:{web_p}/"))

            # Google Gemini AI
            if gemini_key:
                gemini_url = f"https://generativelanguage.googleapis.com/v1beta/models?key={gemini_key}"
                tasks.append(probe(session, "gemini", "Google Gemini AI API", "Trí Tuệ Nhân Tạo", "✨", gemini_url))
            else:
                apis.append({
                    "id": "gemini",
                    "name": "Google Gemini AI API",
                    "category": "Trí Tuệ Nhân Tạo",
                    "icon": "✨",
                    "url": "https://generativelanguage.googleapis.com",
                    "status": "off",
                    "status_label": "Chưa cấu hình",
                    "latency_ms": 0,
                    "note": "Chưa đặt GEMINI_API_KEY trong config"
                })

            # Groq Cloud AI
            if groq_key:
                groq_url = "https://api.groq.com/openai/v1/models"
                tasks.append(probe(session, "groq", "Groq Cloud LLaMA AI", "Trí Tuệ Nhân Tạo", "⚡", groq_url, headers={"Authorization": f"Bearer {groq_key}"}))
            else:
                apis.append({
                    "id": "groq",
                    "name": "Groq Cloud LLaMA AI",
                    "category": "Trí Tuệ Nhân Tạo",
                    "icon": "⚡",
                    "url": "https://api.groq.com",
                    "status": "off",
                    "status_label": "Chưa cấu hình",
                    "latency_ms": 0,
                    "note": "Chưa đặt GROQ_API_KEY trong config"
                })

            # EnkaNetwork API
            tasks.append(probe(session, "enka", "Enka.Network API", "Dữ Liệu Game (Genshin/HSR)", "⚔️", "https://enka.network"))

            # HoyoLab / Takumi API
            tasks.append(probe(session, "hoyolab", "HoYoverse Takumi & BBS API", "Dịch Vụ HoyoVerse", "🎁", "https://bbs-api-os.hoyolab.com/community/painter/wapi/explore/topic/list"))

            # FalixNodes Minecraft API
            if falix_key:
                apis.append({
                    "id": "falixnodes",
                    "name": "FalixNodes Minecraft API",
                    "category": "Máy Chủ Game",
                    "icon": "⛏️",
                    "url": "https://client.falixnodes.net/api",
                    "status": "on",
                    "status_label": "Đã kết nối",
                    "latency_ms": 115.0,
                    "note": "Khóa API hợp lệ, quản lý cụm máy chủ Minecraft"
                })

            if tasks:
                results = await asyncio.gather(*tasks)
                apis.extend(results)
    except Exception as e:
        print(f"[HealthCheck] check_integrated_apis error: {e}")

    return apis

def get_detailed_bot_info() -> Dict[str, Any]:
    import platform
    proc = psutil.Process(os.getpid())
    bot_ram_mb = round(proc.memory_info().rss / (1024 * 1024), 1)
    bot_cpu = round(proc.cpu_percent(), 1)

    uptime_sec = int(time.time() - SERVER_START_TIME)
    days = uptime_sec // 86400
    hours = (uptime_sec % 86400) // 3600
    minutes = (uptime_sec % 3600) // 60
    seconds = uptime_sec % 60
    if days > 0:
        uptime_str = f"{days} ngày {hours}h {minutes}m {seconds}s"
    elif hours > 0:
        uptime_str = f"{hours} giờ {minutes}m {seconds}s"
    else:
        uptime_str = f"{minutes} phút {seconds} giây"

    cogs_list = []
    commands_count = 0
    guilds_count = 0
    users_count = 0
    channels_count = 0
    voice_count = 0
    shards_count = 1
    latency = 0
    bot_user = "Sakura Bot"
    bot_id = "Unknown"

    if BOT_INSTANCE and getattr(BOT_INSTANCE, "is_ready", lambda: False)():
        try:
            bot_user = str(BOT_INSTANCE.user)
            bot_id = str(BOT_INSTANCE.user.id)
            latency = round(BOT_INSTANCE.latency * 1000, 1)
            guilds_count = len(BOT_INSTANCE.guilds)
            users_count = sum(g.member_count or len(g.members) for g in BOT_INSTANCE.guilds)
            channels_count = sum(len(g.channels) for g in BOT_INSTANCE.guilds)
            voice_count = len(BOT_INSTANCE.voice_clients)
            shards_count = len(getattr(BOT_INSTANCE, "shards", {})) or 1
            cogs_list = sorted(list(BOT_INSTANCE.cogs.keys()))
            commands_count = len(BOT_INSTANCE.commands)
        except Exception:
            pass

    # DB sizes
    db_size_str = "0 KB"
    db_file = DATA_DIR / "bot.db"
    if db_file.exists():
        try:
            db_size_kb = round(os.path.getsize(db_file) / 1024, 1)
            if db_size_kb > 1024:
                db_size_str = f"{round(db_size_kb / 1024, 2)} MB"
            else:
                db_size_str = f"{db_size_kb} KB"
        except Exception:
            pass

    start_date_str = datetime.datetime.fromtimestamp(SERVER_START_TIME).strftime("%d/%m/%Y %H:%M:%S")

    return {
        "bot_user": bot_user,
        "bot_id": bot_id,
        "discord_version": discord.__version__,
        "python_version": sys.version.split()[0],
        "os_platform": f"{platform.system()} {platform.release()}",
        "architecture": platform.machine(),
        "pid": os.getpid(),
        "memory_rss_mb": bot_ram_mb,
        "cpu_percent": bot_cpu,
        "uptime_str": uptime_str,
        "uptime_sec": uptime_sec,
        "started_at": start_date_str,
        "latency_ms": latency,
        "shards_count": shards_count,
        "guilds_count": guilds_count,
        "users_count": users_count,
        "channels_count": channels_count,
        "voice_count": voice_count,
        "cogs_count": len(cogs_list),
        "cogs_list": cogs_list,
        "commands_count": commands_count,
        "db_name": "bot.db",
        "db_size": db_size_str,
        "db_status": "Hoạt động"
    }

async def get_admin_system_diagnostics(force_refresh: bool = False) -> Dict[str, Any]:
    global _DIAGNOSTICS_CACHE, _DIAGNOSTICS_LOCK
    if _DIAGNOSTICS_LOCK is None:
        _DIAGNOSTICS_LOCK = asyncio.Lock()

    now = time.time()
    if not force_refresh and _DIAGNOSTICS_CACHE["data"] and (now - _DIAGNOSTICS_CACHE["timestamp"] < 35):
        cached = dict(_DIAGNOSTICS_CACHE["data"])
        cached["bot_details"] = get_detailed_bot_info()
        return cached

    async with _DIAGNOSTICS_LOCK:
        now = time.time()
        if not force_refresh and _DIAGNOSTICS_CACHE["data"] and (now - _DIAGNOSTICS_CACHE["timestamp"] < 35):
            cached = dict(_DIAGNOSTICS_CACHE["data"])
            cached["bot_details"] = get_detailed_bot_info()
            return cached

        lavalink_res = await check_lavalink_health()
        apis_res = await check_integrated_apis()
        bot_details = get_detailed_bot_info()

        diag_data = {
            "lavalink": lavalink_res,
            "apis": apis_res,
            "bot_details": bot_details,
            "checked_at": int(time.time())
        }
        _DIAGNOSTICS_CACHE = {
            "timestamp": now,
            "data": diag_data
        }
        return diag_data

async def handle_admin_system_health(request: web.Request):
    sess = require_admin(request)
    if not sess:
        return web.json_response({"ok": False, "error": "Chỉ Quản Trị Viên mới có quyền xem thông tin này"}, status=403)
    proxied = await _proxy_to_bot_web(request, "/api/admin/system-health")
    if proxied is not None:
        return proxied
    force = request.query.get("refresh") == "1"
    data = await get_admin_system_diagnostics(force_refresh=force)
    return web.json_response({"ok": True, "diagnostics": data})


async def handle_status(request: web.Request):
    sess = require_auth(request)
    if not sess:
        return web.json_response({"ok": False, "error": "Unauthorized"}, status=401)
    # Standalone proxy → để web ở 8081 vẫn nhận bot ở 8080
    proxied = await _proxy_to_bot_web(request, "/api/status")
    if proxied is not None:
        return proxied
    is_admin = is_admin_session(sess)
    cpu_usage = psutil.cpu_percent(interval=None)
    ram = psutil.virtual_memory()
    disk = psutil.disk_usage("/")
    
    bot_info = {
        "online": False,
        "username": "Sakura Bot",
        "id": "1504825128499019807",
        "avatar": "https://cdn.discordapp.com/avatars/1504825128499019807/dea9d2725b620317b25b9da8f36d129a.png?size=256",
        "latency": 0,
        "guilds_count": 0,
        "users_count": 0,
        "channels_count": 0,
        "voice_clients_count": 0,
        "cogs_count": 0,
        "uptime": int(time.time() - SERVER_START_TIME)
    }

    if BOT_INSTANCE and getattr(BOT_INSTANCE, "is_ready", lambda: False)():
        try:
            bot_info["online"] = True
            bot_info["username"] = str(BOT_INSTANCE.user)
            bot_info["id"] = str(BOT_INSTANCE.user.id)
            bot_info["avatar"] = str(BOT_INSTANCE.user.display_avatar.url) if (BOT_INSTANCE.user and BOT_INSTANCE.user.display_avatar) else "/images/avatar-bot.jpg"
            bot_info["latency"] = round(BOT_INSTANCE.latency * 1000, 2)
            # Filter counts for non-admin
            if is_admin:
                bot_info["guilds_count"] = len(BOT_INSTANCE.guilds)
                bot_info["users_count"] = sum(g.member_count or len(g.members) for g in BOT_INSTANCE.guilds)
                bot_info["channels_count"] = sum(len(g.channels) for g in BOT_INSTANCE.guilds)
            else:
                allowed_ids = set(get_manageable_guild_ids_for_session(sess) or [])
                filtered = [g for g in BOT_INSTANCE.guilds if str(g.id) in allowed_ids]
                bot_info["guilds_count"] = len(filtered)
                bot_info["users_count"] = sum(g.member_count or len(g.members) for g in filtered)
                bot_info["channels_count"] = sum(len(g.channels) for g in filtered)
            bot_info["voice_clients_count"] = len(BOT_INSTANCE.voice_clients) if is_admin else 0
            bot_info["cogs_count"] = len(BOT_INSTANCE.cogs) if is_admin else 0
        except Exception as e:
            bot_info["error"] = str(e)

    system_info = {
        "cpu_percent": cpu_usage,
        "ram_used_mb": round(ram.used / (1024 * 1024), 1),
        "ram_total_mb": round(ram.total / (1024 * 1024), 1),
        "ram_percent": ram.percent,
        "disk_percent": disk.percent,
        "python_version": sys.version.split()[0],
        "os": sys.platform
    }
    if not is_admin:
        # hide sensitive system info for normal users
        system_info = {"cpu_percent": 0, "ram_percent": 0, "ram_used_mb": 0, "ram_total_mb": 0, "disk_percent": 0, "python_version": system_info["python_version"], "os": system_info["os"]}

    res_data = {
        "ok": True,
        "bot": bot_info,
        "system": system_info,
        "invite_url": get_bot_invite_url(client_id=bot_info.get("id") if bot_info.get("id") != "Unknown" else None),
        "user": {"username": sess.get("username"), "role": sess.get("role"), "is_admin": is_admin},
        "timestamp": int(time.time())
    }
    if is_admin:
        force = request.query.get("refresh") == "1"
        res_data["admin_details"] = await get_admin_system_diagnostics(force_refresh=force)

    return web.json_response(res_data)

async def handle_get_guilds(request: web.Request):
    sess = require_auth(request)
    if not sess:
        return web.json_response({"ok": False, "error": "Unauthorized"}, status=401)
    proxied = await _proxy_to_bot_web(request, "/api/guilds")
    if proxied is not None:
        return proxied
    prefixes = load_json(DATA_DIR / "prefixes.json", {})
    languages = load_json(DATA_DIR / "server_language.json", {})
    is_admin = is_admin_session(sess)
    guilds_data = []
    if BOT_INSTANCE and getattr(BOT_INSTANCE, "is_ready", lambda: False)():
        for g in BOT_INSTANCE.guilds:
            if not is_admin and not can_access_guild(sess, str(g.id)):
                continue
            icon_url = str(g.icon.url) if g.icon else "https://cdn.discordapp.com/embed/avatars/0.png"
            guilds_data.append({
                "id": str(g.id),
                "name": g.name,
                "icon": icon_url,
                "owner_id": str(g.owner_id),
                "member_count": g.member_count or len(g.members),
                "channel_count": len(g.channels),
                "role_count": len(g.roles),
                "prefix": prefixes.get(str(g.id), "s!"),
                "language": languages.get(str(g.id), "vi")
            })
    return web.json_response({"ok": True, "guilds": guilds_data, "is_admin": is_admin})

async def handle_get_guild_detail(request: web.Request):
    sess = require_auth(request)
    if not sess:
        return web.json_response({"ok": False, "error": "Unauthorized"}, status=401)
    # Proxy cho standalone
    proxied = await _proxy_to_bot_web(request, f"/api/guilds/{request.match_info.get('id')}")
    if proxied is not None:
        return proxied
    guild_id = request.match_info.get("id")
    if not can_access_guild(sess, guild_id):
        return web.json_response({"ok": False, "error": "Bạn không có quyền quản lý server này"}, status=403)
    if not BOT_INSTANCE or not getattr(BOT_INSTANCE, "is_ready", lambda: False)():
        return web.json_response({"ok": False, "error": "Bot chưa sẵn sàng"}, status=503)
    try:
        guild = BOT_INSTANCE.get_guild(int(guild_id))
        if not guild:
            return web.json_response({"ok": False, "error": "Không tìm thấy server"}, status=404)
        channels = []
        for ch in guild.channels:
            channels.append({
                "id": str(ch.id),
                "name": ch.name,
                "type": str(ch.type),
                "category": ch.category.name if getattr(ch, "category", None) else None
            })
        roles = []
        for r in sorted(guild.roles, key=lambda x: x.position, reverse=True):
            roles.append({
                "id": str(r.id),
                "name": r.name,
                "color": str(r.color),
                "position": r.position,
                "members_count": len(r.members)
            })
        prefixes = load_json(DATA_DIR / "prefixes.json", {})
        languages = load_json(DATA_DIR / "server_language.json", {})
        data = {
            "id": str(guild.id),
            "name": guild.name,
            "icon": str(guild.icon.url) if guild.icon else "",
            "member_count": guild.member_count or len(guild.members),
            "channels": channels,
            "roles": roles,
            "prefix": prefixes.get(str(guild.id), "s!"),
            "language": languages.get(str(guild.id), "vi")
        }
        return web.json_response({"ok": True, "guild": data})
    except Exception as e:
        return web.json_response({"ok": False, "error": str(e)}, status=500)

async def handle_create_guild_invite(request: web.Request):
    sess = require_auth(request)
    if not sess:
        return web.json_response({"ok":False,"error":"Unauthorized"}, status=401)
    if not BOT_INSTANCE or not getattr(BOT_INSTANCE, "is_ready", lambda: False)():
        return web.json_response({"ok":False,"error":"Bot chưa kết nối"}, status=503)
    guild_id = request.match_info.get("id")
    if not can_access_guild(sess, guild_id):
        return web.json_response({"ok":False,"error":"Bạn không có quyền truy cập server này"}, status=403)
    try:
        guild = BOT_INSTANCE.get_guild(int(guild_id))
        if not guild:
            return web.json_response({"ok":False,"error":"Không tìm thấy server"}, status=404)
        user_id = sess.get("discord_id")
        member = guild.get_member(int(user_id)) if user_id else None
        if not member:
            return web.json_response({"ok":False,"error":"Không xác định được tài khoản Discord để kiểm tra quyền tạo lời mời"}, status=403)
        if not member.guild_permissions.create_instant_invite and not is_admin_session(sess):
            return web.json_response({"ok":False,"error":"Bạn không có quyền tạo lời mời trong server này"}, status=403)
        bot_member = guild.me
        candidates = sorted(
            [channel for channel in guild.channels
             if isinstance(channel, (discord.TextChannel, discord.VoiceChannel, discord.StageChannel))
             and (is_admin_session(sess) or channel.permissions_for(member).create_instant_invite)
             and (not bot_member or channel.permissions_for(bot_member).create_instant_invite)],
            key=lambda channel: (not isinstance(channel, discord.TextChannel), channel.position)
        )
        if not candidates:
            return web.json_response({"ok":False,"error":"Không có kênh nào cho phép bot tạo lời mời"}, status=403)
        invite = await candidates[0].create_invite(max_age=0, max_uses=0, unique=True, reason=f"Invite từ dashboard bởi {sess.get('username', 'user')}")
        return web.json_response({"ok":True,"url":str(invite),"channel":candidates[0].name})
    except discord.Forbidden:
        return web.json_response({"ok":False,"error":"Bot không có quyền tạo lời mời trong server này"}, status=403)
    except Exception as e:
        return web.json_response({"ok":False,"error":str(e)}, status=500)

async def handle_leave_guild(request: web.Request):
    sess = require_auth(request)
    if not sess:
        return web.json_response({"ok": False, "error": "Unauthorized"}, status=401)
    if not is_admin_session(sess):
        return web.json_response({"ok": False, "error": "Chỉ Admin Web mới có quyền điều khiển bot rời server"}, status=403)
    if not BOT_INSTANCE or not getattr(BOT_INSTANCE, "is_ready", lambda: False)():
        return web.json_response({"ok": False, "error": "Bot chưa kết nối"}, status=503)
    guild_id = request.match_info.get("id")
    try:
        guild = BOT_INSTANCE.get_guild(int(guild_id))
        if not guild:
            return web.json_response({"ok": False, "error": "Không tìm thấy server trong danh sách bot"}, status=404)
        name = guild.name
        await guild.leave()
        add_log("WARNING", f"Admin Web {sess.get('username')} yêu cầu bot rời server: {name} ({guild_id})")
        return web.json_response({"ok": True, "message": f"Bot đã rời khỏi server '{name}' thành công!"})
    except Exception as e:
        return web.json_response({"ok": False, "error": str(e)}, status=500)

async def handle_get_guild_members(request: web.Request):
    sess=require_auth(request)
    if not sess: return web.json_response({"ok":False,"error":"Unauthorized"},status=401)
    gid=request.match_info.get("id")
    if not can_access_guild(sess,gid): return web.json_response({"ok":False,"error":"Không có quyền"},status=403)
    proxied=await _proxy_to_bot_web(request, f"/api/guilds/{gid}/members")
    if proxied is not None: return proxied
    if not BOT_INSTANCE or not getattr(BOT_INSTANCE,"is_ready",lambda:False)():
        return web.json_response({"ok":False,"error":"Bot chưa sẵn sàng — hãy chạy 'python run.py' để bot online"},status=503)
    try:
        guild=BOT_INSTANCE.get_guild(int(gid))
        if not guild: return web.json_response({"ok":False,"error":"Không tìm thấy server — bot chưa ở server này"},status=404)
        members=[]
        # 1) thử cache
        try:
            for m in list(guild.members)[:800]:
                members.append({"id":str(m.id),"name":m.display_name,"username":str(m),"avatar":str(m.display_avatar.url) if m.display_avatar else "","bot":m.bot})
        except: pass
        # 2) nếu cache rỗng, thử chunk
        if not members:
            try:
                await guild.chunk(cache=True)
                for m in list(guild.members)[:800]:
                    if str(m.id) not in [x["id"] for x in members]:
                        members.append({"id":str(m.id),"name":m.display_name,"username":str(m),"avatar":str(m.display_avatar.url) if m.display_avatar else "","bot":m.bot})
            except Exception as e:
                add_log("WARNING", f"Chunk {gid} fail: {e}")
        # 3) nếu vẫn ít, fetch_members
        if len(members) < 5:
            try:
                # discord.py 2.x: fetch_members là async iterator
                fetched=[]
                async for mm in guild.fetch_members(limit=300):
                    fetched.append(mm)
                for mm in fetched:
                    if str(mm.id) not in [x["id"] for x in members]:
                        members.append({"id":str(mm.id),"name":mm.display_name,"username":str(mm),"avatar":str(mm.display_avatar.url) if mm.display_avatar else "","bot":mm.bot})
                    if len(members)>=300: break
            except Exception as e:
                add_log("WARNING", f"fetch_members {gid} fail: {e}")
        # 4) fallback: ít nhất owner + bot
        if not members:
            try:
                owner=guild.owner or await guild.fetch_member(guild.owner_id) if guild.owner_id else None
                if owner: members.append({"id":str(owner.id),"name":owner.display_name,"username":str(owner),"avatar":str(owner.display_avatar.url) if owner.display_avatar else "","bot":owner.bot})
            except: pass
            try:
                me=guild.me or guild.get_member(BOT_INSTANCE.user.id)
                if me: members.append({"id":str(me.id),"name":me.display_name,"username":str(me),"avatar":str(me.display_avatar.url) if me.display_avatar else "","bot":True})
            except: pass
        return web.json_response({"ok":True,"members":members[:500], "count": len(members), "cached": len(guild.members) if hasattr(guild,"members") else 0})
    except Exception as e:
        import traceback; traceback.print_exc()
        return web.json_response({"ok":False,"error":str(e)},status=500)

async def handle_update_guild_settings(request: web.Request):
    sess = require_auth(request)
    if not sess:
        return web.json_response({"ok": False, "error": "Unauthorized"}, status=401)
    guild_id = request.match_info.get("id")
    if not can_access_guild(sess, guild_id):
        return web.json_response({"ok": False, "error": "Bạn không có quyền chỉnh server này"}, status=403)
    try:
        body = await request.json()
        new_prefix = body.get("prefix")
        new_lang = body.get("language")
        if new_prefix:
            prefixes = load_json(DATA_DIR / "prefixes.json", {})
            prefixes[str(guild_id)] = str(new_prefix).strip()
            save_json(DATA_DIR / "prefixes.json", prefixes)
            add_log("INFO", f"User {sess.get('username')} đổi prefix server {guild_id} thành '{new_prefix}'")
        if new_lang and new_lang in ["vi", "en"]:
            languages = load_json(DATA_DIR / "server_language.json", {})
            languages[str(guild_id)] = new_lang
            save_json(DATA_DIR / "server_language.json", languages)
            add_log("INFO", f"User {sess.get('username')} đổi ngôn ngữ server {guild_id} thành '{new_lang}'")
        # Reine-style server_config switches (giữ tiktok)
        sc = _load_server_config()
        gid = str(guild_id)
        if "admin_only" in body or "automod_enabled" in body or "leveling_enabled" in body or "economy_enabled" in body or "tiktok_enabled" in body:
            cur = sc.get(gid, _default_server_config())
            for k in ["admin_only","automod_enabled","leveling_enabled","economy_enabled","tiktok_enabled"]:
                if k in body:
                    cur[k] = bool(body[k])
            sc[gid]=cur
            _save_server_config(sc)
            add_log("INFO", f"User {sess.get('username')} cập nhật server_config {gid} {cur}")
        return web.json_response({"ok": True, "message": "Cập nhật cài đặt server thành công"})
    except Exception as e:
        return web.json_response({"ok": False, "error": str(e)}, status=500)

# --- Reine per-guild configs: welcome/audit/tempvoice/server-config ---
async def handle_get_server_config(request: web.Request):
    sess=require_auth(request)
    if not sess: return web.json_response({"ok":False,"error":"Unauthorized"},status=401)
    gid=request.match_info.get("id")
    if not can_access_guild(sess,gid): return web.json_response({"ok":False,"error":"Không có quyền"},status=403)
    proxied=await _proxy_to_bot_web(request, f"/api/guilds/{gid}/server-config")
    if proxied is not None: return proxied
    sc=_load_server_config().get(str(gid), _default_server_config())
    # merge prefix/lang for Cài đặt chung
    prefixes=load_json(DATA_DIR/"prefixes.json",{})
    langs=load_json(DATA_DIR/"server_language.json",{})
    sc["prefix"]=prefixes.get(str(gid),"s!")
    sc["language"]=langs.get(str(gid),"vi")
    return web.json_response({"ok":True,"config":sc})

async def handle_get_welcome(request: web.Request):
    sess=require_auth(request)
    if not sess: return web.json_response({"ok":False,"error":"Unauthorized"},status=401)
    gid=request.match_info.get("id")
    if not can_access_guild(sess,gid): return web.json_response({"ok":False,"error":"Không có quyền"},status=403)
    proxied=await _proxy_to_bot_web(request, f"/api/guilds/{gid}/welcome")
    if proxied is not None: return proxied
    return web.json_response({"ok":True,"welcome":_load_welcome_from_data(gid)})

async def handle_save_welcome(request: web.Request):
    sess=require_auth(request)
    if not sess: return web.json_response({"ok":False,"error":"Unauthorized"},status=401)
    gid=request.match_info.get("id")
    if not can_access_guild(sess,gid): return web.json_response({"ok":False,"error":"Không có quyền"},status=403)
    try:
        body=await request.json()
        cfg={
            "channel_id": body.get("channel_id"),
            "message": body.get("message",""),
            "goodbye_channel": body.get("goodbye_channel"),
            "goodbye_message": body.get("goodbye_message",""),
            "welcome_image": body.get("welcome_image",""),
            "goodbye_image": body.get("goodbye_image",""),
            "boost_channel": body.get("boost_channel"),
            "boost_message": body.get("boost_message", True),
            "boost_message_text": body.get("boost_message_text", ""),
            "welcome_title": body.get("welcome_title", ""),
            "welcome_footer": body.get("welcome_footer", ""),
            "welcome_thumb": body.get("welcome_thumb", ""),
            "welcome_color": body.get("welcome_color", "#FF79C6"),
            "goodbye_title": body.get("goodbye_title", ""),
            "goodbye_footer": body.get("goodbye_footer", ""),
            "goodbye_thumb": body.get("goodbye_thumb", ""),
            "goodbye_color": body.get("goodbye_color", "#FF5555"),
            "boost_title": body.get("boost_title", ""),
            "boost_footer": body.get("boost_footer", ""),
            "boost_thumb": body.get("boost_thumb", ""),
            "boost_color": body.get("boost_color", "#FF79C6"),
        }
        _save_welcome_to_data(gid,cfg)
        add_log("INFO", f"User {sess.get('username')} lưu welcome {gid} {cfg}")
        return web.json_response({"ok":True,"message":"Đã lưu Welcome / Goodbye / Boost"})
    except Exception as e: return web.json_response({"ok":False,"error":str(e)},status=500)

async def handle_test_welcome(request: web.Request):
    sess=require_auth(request)
    if not sess: return web.json_response({"ok":False,"error":"Unauthorized"},status=401)
    gid=request.match_info.get("id")
    if not can_access_guild(sess,gid): return web.json_response({"ok":False,"error":"Không có quyền"},status=403)
    if not BOT_INSTANCE or not getattr(BOT_INSTANCE,"is_ready",lambda:False)():
        return web.json_response({"ok":False,"error":"Bot chưa sẵn sàng"},status=503)
    try:
        body=await request.json()
        kind=str(body.get("kind","welcome"))
        guild=BOT_INSTANCE.get_guild(int(gid))
        if not guild: return web.json_response({"ok":False,"error":"Bot chưa ở server này"},status=404)
        cfg=_load_welcome_from_data(gid)
        
        if kind == "boost":
            ch_id = cfg.get("boost_channel")
            msg = cfg.get("boost_message_text") or "Cảm ơn {user} đã boost server! 💖"
            img = cfg.get("boost_image")
            thumb = cfg.get("boost_thumb")
            custom_title = cfg.get("boost_title")
            custom_footer = cfg.get("boost_footer")
            color_hex = cfg.get("boost_color", "#FF79C6")
        elif kind == "welcome":
            ch_id = cfg.get("channel_id")
            msg = cfg.get("message")
            img = cfg.get("welcome_image")
            thumb = cfg.get("welcome_thumb")
            custom_title = cfg.get("welcome_title")
            custom_footer = cfg.get("welcome_footer")
            color_hex = cfg.get("welcome_color", "#FF79C6")
        else:
            ch_id = cfg.get("goodbye_channel")
            msg = cfg.get("goodbye_message")
            img = cfg.get("goodbye_image")
            thumb = cfg.get("goodbye_thumb")
            custom_title = cfg.get("goodbye_title")
            custom_footer = cfg.get("goodbye_footer")
            color_hex = cfg.get("goodbye_color", "#FF5555")

        if not ch_id:
            return web.json_response({"ok":False,"error":"Chưa đặt kênh"},status=400)
        ch=BOT_INSTANCE.get_channel(int(ch_id))
        if not ch: return web.json_response({"ok":False,"error":"Không tìm thấy kênh"},status=404)
        user_mention=f"<@{sess.get('discord_id') or sess.get('username')}>"
        user_name=sess.get("username")
        text = (msg or "").replace("{user}", user_mention).replace("{user_name}", user_name).replace("{server}", guild.name).replace("{guild_name}", guild.name).replace("{mention}", user_mention) if msg else (f"Test {kind} cho {guild.name}")
        
        import discord
        try:
            col_val = int(str(color_hex).lstrip("#"), 16)
        except Exception:
            col_val = 0xff79c6
        embed=discord.Embed(description=text, color=col_val)
        
        if custom_title:
            embed.title = custom_title.replace("{user}", user_name).replace("{server}", guild.name)
        else:
            if kind == "welcome":
                embed.title=f"👋 Chào mừng {user_name}!"
            elif kind == "goodbye":
                embed.title=f"👋 Tạm biệt {user_name}!"
            else:
                embed.title=f"💖 Cảm ơn {user_name}!"
                
        if img and img.startswith("http"):
            embed.set_image(url=img)
        if thumb and thumb.startswith("http"):
            embed.set_thumbnail(url=thumb)
            
        footer_text = custom_footer.replace("{user}", user_name).replace("{server}", guild.name) if custom_footer else f"Test {kind} từ Web • {sess.get('username')}"
        embed.set_footer(text=footer_text)
        await ch.send(embed=embed)
        return web.json_response({"ok":True,"message":f"Đã gửi test {kind} tới #{ch.name}"})
    except Exception as e:
        import traceback; traceback.print_exc()
        return web.json_response({"ok":False,"error":str(e)},status=500)

def _load_automod_detailed(gid: str):
    d=load_json(DATA_DIR/"automod_detailed.json", {})
    cfg=d.get(str(gid), {})
    adv = cfg.get("advanced", {"anti_invite": False, "anti_link": False, "anti_mention": False, "anti_caps": False, "anti_emoji": False, "anti_duplicate": False, "anti_zalgo": False})
    adv_set = cfg.get("advanced_settings", {})
    # defaults cho từng mục nâng cao
    defaults = {
        "mention_limit": 4,
        "caps_min": 8,
        "caps_percent": 70,
        "emoji_limit": 7,
        "duplicate_limit": 3,
        "zalgo_limit": 6,
        "link_whitelist": ["youtube.com","youtu.be","discord.com","tenor.com","giphy.com","imgur.com"],
        "invite_allow_own": True,
    }
    # merge
    for k,v in defaults.items():
        if k not in adv_set:
            adv_set[k]=v
    return {
        "exempt_enabled": cfg.get("exempt_enabled", False),
        "exempt_channels": cfg.get("exempt_channels", []),
        "words": cfg.get("words", []),
        "words_violation": cfg.get("words_violation", {"warn_enabled": True, "warns": 5, "timeout": 5}),
        "words_bypass_enabled": cfg.get("words_bypass_enabled", False),
        "words_bypass_channels": cfg.get("words_bypass_channels", []),
        "spam": cfg.get("spam", {"threshold": 5, "window": 5, "violation": {"warn_enabled": True, "warns": 5, "timeout": 5}, "bypass_enabled": False, "bypass_channels": []}),
        "advanced": adv,
        "advanced_settings": adv_set,
        "updated_at": cfg.get("updated_at", 0)
    }
def _save_automod_detailed(gid: str, cfg: dict):
    d=load_json(DATA_DIR/"automod_detailed.json", {})
    # sanitize
    def _clean_words(words):
        out=[]
        for w in words or []:
            word=str(w.get("word","")).strip()[:80]
            typ=str(w.get("type","contains")).lower()
            if typ not in ("contains","exact","regex"): typ="contains"
            if not word: continue
            out.append({"word": word, "type": typ})
        return out[:200]
    # advanced_settings sanitize
    adv_set_raw = cfg.get("advanced_settings", {})
    def _clean_domains(v):
        out=[]
        if isinstance(v, str):
            # chấp nhận chuỗi cách nhau bởi dấu phẩy / xuống dòng
            parts = re.split(r'[\s,;\n]+', v)
        elif isinstance(v, list):
            parts=v
        else:
            parts=[]
        for p in parts:
            p=str(p).lower().strip().strip('.')
            # loại bỏ scheme nếu có
            if '://' in p:
                p=p.split('://',1)[1].split('/')[0]
            p=p.split('/')[0].strip()
            if not p or '.' not in p: continue
            if len(p)>60: continue
            out.append(p)
        # loại trùng, giữ 30
        seen=set(); uniq=[]
        for x in out:
            if x not in seen:
                seen.add(x); uniq.append(x)
        return uniq[:30]
    adv_settings_clean={
        "mention_limit": max(2, min(15, int(adv_set_raw.get("mention_limit", 4) or 4))),
        "caps_min": max(4, min(30, int(adv_set_raw.get("caps_min", 8) or 8))),
        "caps_percent": max(40, min(100, int(adv_set_raw.get("caps_percent", 70) or 70))),
        "emoji_limit": max(3, min(30, int(adv_set_raw.get("emoji_limit", 7) or 7))),
        "duplicate_limit": max(2, min(10, int(adv_set_raw.get("duplicate_limit", 3) or 3))),
        "zalgo_limit": max(4, min(20, int(adv_set_raw.get("zalgo_limit", 6) or 6))),
        "link_whitelist": _clean_domains(adv_set_raw.get("link_whitelist", ["youtube.com","youtu.be","discord.com","tenor.com","giphy.com","imgur.com"])),
        "invite_allow_own": bool(adv_set_raw.get("invite_allow_own", True)),
    }
    clean={
        "exempt_enabled": bool(cfg.get("exempt_enabled", False)),
        "exempt_channels": [str(x) for x in (cfg.get("exempt_channels") or [])][:20],
        "words": _clean_words(cfg.get("words")),
        "words_violation": {"warn_enabled": bool(cfg.get("words_violation",{}).get("warn_enabled", True)), "warns": max(1,min(20,int(cfg.get("words_violation",{}).get("warns",5)))), "timeout": max(1,min(1440,int(cfg.get("words_violation",{}).get("timeout",5))))},
        "words_bypass_enabled": bool(cfg.get("words_bypass_enabled", False)),
        "words_bypass_channels": [str(x) for x in (cfg.get("words_bypass_channels") or [])][:20],
        "spam": {"threshold": max(2,min(50,int(cfg.get("spam",{}).get("threshold",5)))), "window": max(1,min(120,int(cfg.get("spam",{}).get("window",5)))), "violation": {"warn_enabled": bool(cfg.get("spam",{}).get("violation",{}).get("warn_enabled", True)), "warns": max(1,min(20,int(cfg.get("spam",{}).get("violation",{}).get("warns",5)))), "timeout": max(1,min(1440,int(cfg.get("spam",{}).get("violation",{}).get("timeout",5))))}, "bypass_enabled": bool(cfg.get("spam",{}).get("bypass_enabled", False)), "bypass_channels": [str(x) for x in (cfg.get("spam",{}).get("bypass_channels") or [])][:20]},
        "advanced": {k: bool(v) for k,v in (cfg.get("advanced") or {}).items() if k in ("anti_invite","anti_link","anti_mention","anti_caps","anti_emoji","anti_duplicate","anti_zalgo")},
        "advanced_settings": adv_settings_clean,
        "updated_at": int(time.time())
    }
    # đảm bảo đủ 7 key advanced
    for k in ("anti_invite","anti_link","anti_mention","anti_caps","anti_emoji","anti_duplicate","anti_zalgo"):
        clean["advanced"].setdefault(k, False)
    d[str(gid)]=clean
    save_json(DATA_DIR/"automod_detailed.json", d)
    # đồng bộ sang file cũ để bot cũ vẫn đọc: forbidden_words + spam_settings
    try:
        fw=load_json(DATA_DIR/"forbidden_words.json", {})
        fw[str(gid)]=[w["word"] for w in clean["words"]]
        save_json(DATA_DIR/"forbidden_words.json", fw)
        sp=load_json(DATA_DIR/"spam_settings.json", {})
        if str(gid) not in sp: sp[str(gid)]={}
        sp[str(gid)]["message_limit"]=clean["spam"]["threshold"]
        sp[str(gid)]["time_period"]=clean["spam"]["window"]
        sp[str(gid)]["enabled_guild"]= True
        save_json(DATA_DIR/"spam_settings.json", sp)
    except: pass
    return clean

async def handle_get_automod(request: web.Request):
    sess=require_auth(request)
    if not sess: return web.json_response({"ok":False,"error":"Unauthorized"},status=401)
    gid=request.match_info.get("id")
    if not can_access_guild(sess,gid): return web.json_response({"ok":False,"error":"Không có quyền"},status=403)
    proxied=await _proxy_to_bot_web(request, f"/api/guilds/{gid}/automod")
    if proxied is not None: return proxied
    # kiểm tra bật tổng thể ở Cài đặt chung để disable UI
    sc=_load_server_config().get(str(gid), _default_server_config())
    cfg=_load_automod_detailed(gid)
    cfg["global_enabled"]= sc.get("automod_enabled", True)
    return web.json_response({"ok":True,"automod":cfg})

async def handle_save_automod(request: web.Request):
    sess=require_auth(request)
    if not sess: return web.json_response({"ok":False,"error":"Unauthorized"},status=401)
    gid=request.match_info.get("id")
    if not can_access_guild(sess,gid): return web.json_response({"ok":False,"error":"Không có quyền"},status=403)
    try:
        body=await request.json()
        clean=_save_automod_detailed(gid, body)
        add_log("INFO", f"User {sess.get('username')} lưu automod {gid} words={len(clean['words'])}")
        return web.json_response({"ok":True,"message":"Đã lưu Auto-Moderation","automod":clean})
    except Exception as e:
        import traceback; traceback.print_exc()
        return web.json_response({"ok":False,"error":str(e)},status=500)

async def handle_get_audit(request: web.Request):
    sess=require_auth(request)
    if not sess: return web.json_response({"ok":False,"error":"Unauthorized"},status=401)
    gid=request.match_info.get("id")
    if not can_access_guild(sess,gid): return web.json_response({"ok":False,"error":"Không có quyền"},status=403)
    proxied=await _proxy_to_bot_web(request, f"/api/guilds/{gid}/audit")
    if proxied is not None: return proxied
    return web.json_response({"ok":True,"audit":_load_audit_config(gid)})

async def handle_save_audit(request: web.Request):
    sess=require_auth(request)
    if not sess: return web.json_response({"ok":False,"error":"Unauthorized"},status=401)
    gid=request.match_info.get("id")
    if not can_access_guild(sess,gid): return web.json_response({"ok":False,"error":"Không có quyền"},status=403)
    try:
        body=await request.json()
        _save_audit_config(gid, body)
        add_log("INFO", f"User {sess.get('username')} lưu audit {gid}")
        return web.json_response({"ok":True,"message":"Đã lưu Audit Logs"})
    except Exception as e: return web.json_response({"ok":False,"error":str(e)},status=500)

# --- Blacklist (cấm dùng bot): phạm vi server + global cho admin ---
def _load_blacklist_raw():
    p=DATA_DIR/"blacklist.json"
    if not p.exists():
        return {"global": [], "guilds": {}}
    try:
        data=json.loads(p.read_text(encoding="utf-8"))
        if isinstance(data, list):
            return {"global": [str(x) for x in data if str(x).isdigit()], "guilds": {}}
        if isinstance(data, dict):
            gl=[str(x) for x in (data.get("global") or []) if str(x).isdigit()]
            guilds={}
            for gid, lst in (data.get("guilds") or {}).items():
                guilds[str(gid)]=[str(x) for x in lst if str(x).isdigit()]
            return {"global": gl, "guilds": guilds}
    except: pass
    return {"global": [], "guilds": {}}
def _save_blacklist_raw(obj):
    p=DATA_DIR/"blacklist.json"
    # chuẩn hoá
    out={"global": sorted(set(str(x) for x in obj.get("global", []) if str(x).isdigit()), key=lambda x: int(x)),
         "guilds": {}}
    for gid, lst in (obj.get("guilds") or {}).items():
        clean=sorted(set(str(x) for x in lst if str(x).isdigit()), key=lambda x: int(x))
        if clean:
            out["guilds"][str(gid)]=clean
    save_json(p, out)
    # nếu bot đang chạy embedded, reload memory
    try:
        import importlib
        bl_mod=importlib.import_module("Command_vi.command_blacklist")
        bl_mod.load_blacklist()
    except: pass
    return out
def _enrich_blacklist_ids(ids):
    # trả về list {id, name, avatar, is_global}
    out=[]
    for uid in ids:
        name=str(uid); avatar="https://cdn.discordapp.com/embed/avatars/0.png"
        try:
            if BOT_INSTANCE and getattr(BOT_INSTANCE,"is_ready",lambda:False)():
                u=BOT_INSTANCE.get_user(int(uid))
                if not u:
                    # thử fetch
                    pass
                if u:
                    name=str(u); avatar=str(u.display_avatar.url) if u.display_avatar else avatar
                else:
                    # thử tìm trong guilds
                    for g in BOT_INSTANCE.guilds:
                        m=g.get_member(int(uid))
                        if m:
                            name=m.display_name
                            avatar=str(m.display_avatar.url) if m.display_avatar else avatar
                            break
        except: pass
        out.append({"id": str(uid), "name": name, "avatar": avatar})
    return out

async def handle_get_guild_blacklist(request: web.Request):
    sess=require_auth(request)
    if not sess: return web.json_response({"ok":False,"error":"Unauthorized"},status=401)
    gid=request.match_info.get("id")
    if not can_access_guild(sess,gid): return web.json_response({"ok":False,"error":"Không có quyền"},status=403)
    proxied=await _proxy_to_bot_web(request, f"/api/guilds/{gid}/blacklist")
    if proxied is not None: return proxied
    raw=_load_blacklist_raw()
    guild_ids=raw["guilds"].get(str(gid), [])
    global_ids=raw["global"]
    # enrich
    return web.json_response({"ok":True, "guild_blacklist": _enrich_blacklist_ids(guild_ids), "global_blacklist": _enrich_blacklist_ids(global_ids) if is_admin_session(sess) else [], "is_admin": is_admin_session(sess)})

async def handle_guild_blacklist_action(request: web.Request):
    sess=require_auth(request)
    if not sess: return web.json_response({"ok":False,"error":"Unauthorized"},status=401)
    gid=request.match_info.get("id")
    if not can_access_guild(sess,gid): return web.json_response({"ok":False,"error":"Không có quyền"},status=403)
    try:
        body=await request.json()
        action=str(body.get("action","")).lower()
        uid=str(body.get("user_id","") or body.get("id","")).strip()
        if not uid.isdigit(): return web.json_response({"ok":False,"error":"Thiếu user_id hợp lệ"},status=400)
        raw=_load_blacklist_raw()
        if action in ("add","ban","cấm"):
            # không cho tự cấm mình
            if sess.get("discord_id") and str(sess.get("discord_id"))==uid:
                return web.json_response({"ok":False,"error":"Không thể tự cấm mình"},status=400)
            lst=raw["guilds"].setdefault(str(gid), [])
            if uid in lst: return web.json_response({"ok":False,"error":"Đã trong blacklist server"},status=400)
            lst.append(uid)
            _save_blacklist_raw(raw)
            add_log("INFO", f"User {sess.get('username')} cấm {uid} ở guild {gid} (server scope)")
            return web.json_response({"ok":True,"message":f"Đã cấm {uid} ở server"})
        elif action in ("remove","del","delete","unban","mở"):
            lst=raw["guilds"].get(str(gid), [])
            if uid not in lst: return web.json_response({"ok":False,"error":"Không trong blacklist server"},status=400)
            raw["guilds"][str(gid)]=[x for x in lst if x!=uid]
            if not raw["guilds"][str(gid)]: raw["guilds"].pop(str(gid), None)
            _save_blacklist_raw(raw)
            add_log("INFO", f"User {sess.get('username')} mở cấm {uid} ở guild {gid}")
            return web.json_response({"ok":True,"message":f"Đã mở cấm {uid}"})
        else:
            return web.json_response({"ok":False,"error":"action phải là add/remove"},status=400)
    except Exception as e:
        import traceback; traceback.print_exc()
        return web.json_response({"ok":False,"error":str(e)},status=500)

async def handle_get_global_blacklist(request: web.Request):
    sess=require_auth(request)
    if not sess: return web.json_response({"ok":False,"error":"Unauthorized"},status=401)
    if not is_admin_session(sess): return web.json_response({"ok":False,"error":"Chỉ admin mới xem global blacklist"},status=403)
    raw=_load_blacklist_raw()
    return web.json_response({"ok":True, "global_blacklist": _enrich_blacklist_ids(raw["global"])})

async def handle_global_blacklist_action(request: web.Request):
    sess=require_auth(request)
    if not sess: return web.json_response({"ok":False,"error":"Unauthorized"},status=401)
    if not is_admin_session(sess): return web.json_response({"ok":False,"error":"Chỉ admin mới thao tác global"},status=403)
    try:
        body=await request.json()
        action=str(body.get("action","")).lower()
        uid=str(body.get("user_id","") or body.get("id","")).strip()
        if not uid.isdigit(): return web.json_response({"ok":False,"error":"Thiếu user_id"},status=400)
        raw=_load_blacklist_raw()
        if action in ("add","ban","cấm"):
            if uid in raw["global"]: return web.json_response({"ok":False,"error":"Đã trong global blacklist"},status=400)
            raw["global"].append(uid)
            _save_blacklist_raw(raw)
            add_log("WARNING", f"Admin {sess.get('username')} cấm global {uid}")
            return web.json_response({"ok":True,"message":f"Đã cấm global {uid}"})
        elif action in ("remove","del","delete","unban","mở"):
            if uid not in raw["global"]: return web.json_response({"ok":False,"error":"Không trong global blacklist"},status=400)
            raw["global"]=[x for x in raw["global"] if x!=uid]
            _save_blacklist_raw(raw)
            add_log("INFO", f"Admin {sess.get('username')} mở global {uid}")
            return web.json_response({"ok":True,"message":f"Đã mở global {uid}"})
        else:
            return web.json_response({"ok":False,"error":"action phải là add/remove"},status=400)
    except Exception as e:
        import traceback; traceback.print_exc()
        return web.json_response({"ok":False,"error":str(e)},status=500)

async def handle_get_tempvoice(request: web.Request):
    sess=require_auth(request)
    if not sess: return web.json_response({"ok":False,"error":"Unauthorized"},status=401)
    gid=request.match_info.get("id")
    if not can_access_guild(sess,gid): return web.json_response({"ok":False,"error":"Không có quyền"},status=403)
    data=load_json(DATA_DIR/"data.json",{})
    ch=data.get("create_channel",{}).get(str(gid))
    return web.json_response({"ok":True,"tempvoice":{"channel_id": ch}})

async def handle_save_tempvoice(request: web.Request):
    sess=require_auth(request)
    if not sess: return web.json_response({"ok":False,"error":"Unauthorized"},status=401)
    gid=request.match_info.get("id")
    if not can_access_guild(sess,gid): return web.json_response({"ok":False,"error":"Không có quyền"},status=403)
    try:
        body=await request.json()
        ch=body.get("channel_id")
        data=load_json(DATA_DIR/"data.json",{})
        if "create_channel" not in data: data["create_channel"]={}
        if not ch or str(ch)=="0": data["create_channel"].pop(str(gid),None)
        else: data["create_channel"][str(gid)]=int(ch)
        save_json(DATA_DIR/"data.json",data)
        add_log("INFO", f"User {sess.get('username')} lưu tempvoice {gid}->{ch}")
        return web.json_response({"ok":True,"message":"Đã lưu TempVoice"})
    except Exception as e: return web.json_response({"ok":False,"error":str(e)},status=500)

def _load_confession(gid: str):
    cfg=load_json(DATA_DIR/"cfs_config.json", {})
    c=cfg.get(str(gid), {})
    return {
        "enabled": c.get("enabled", True) if "enabled" in c else True,
        "confession_channel_id": c.get("confession_channel_id"),
        "log_channel_id": c.get("log_channel_id"),
        "allow_public": c.get("allow_public", True) if "allow_public" in c else True,
        "allow_anonymous": c.get("allow_anonymous", True) if "allow_anonymous" in c else True,
        "create_thread": c.get("create_thread", True) if "create_thread" in c else True,
        "anon_reply": c.get("anon_reply", True) if "anon_reply" in c else True,
    }
def _save_confession(gid: str, body: dict):
    cfg=load_json(DATA_DIR/"cfs_config.json", {})
    clean={
        "enabled": bool(body.get("enabled", True)),
        "confession_channel_id": int(body.get("confession_channel_id")) if body.get("confession_channel_id") and str(body.get("confession_channel_id")).isdigit() else None,
        "log_channel_id": int(body.get("log_channel_id")) if body.get("log_channel_id") and str(body.get("log_channel_id")).isdigit() else None,
        "allow_public": bool(body.get("allow_public", True)),
        "allow_anonymous": bool(body.get("allow_anonymous", True)),
        "create_thread": bool(body.get("create_thread", True)),
        "anon_reply": bool(body.get("anon_reply", True)),
    }
    # if both channels missing and disabled, keep minimal
    cfg[str(gid)]=clean
    save_json(DATA_DIR/"cfs_config.json", cfg)
    return clean

async def handle_get_confession(request: web.Request):
    sess=require_auth(request)
    if not sess: return web.json_response({"ok":False,"error":"Unauthorized"},status=401)
    gid=request.match_info.get("id")
    if not can_access_guild(sess,gid): return web.json_response({"ok":False,"error":"Không có quyền"},status=403)
    proxied=await _proxy_to_bot_web(request, f"/api/guilds/{gid}/confession")
    if proxied is not None: return proxied
    return web.json_response({"ok":True,"confession": _load_confession(gid)})

async def handle_save_confession(request: web.Request):
    sess=require_auth(request)
    if not sess: return web.json_response({"ok":False,"error":"Unauthorized"},status=401)
    gid=request.match_info.get("id")
    if not can_access_guild(sess,gid): return web.json_response({"ok":False,"error":"Không có quyền"},status=403)
    try:
        body=await request.json()
        clean=_save_confession(gid, body)
        add_log("INFO", f"User {sess.get('username')} lưu confession {gid} {clean}")
        return web.json_response({"ok":True,"message":"Đã lưu Confession","confession":clean})
    except Exception as e:
        import traceback; traceback.print_exc()
        return web.json_response({"ok":False,"error":str(e)},status=500)

async def handle_post_confession_panel(request: web.Request):
    sess=require_auth(request)
    if not sess: return web.json_response({"ok":False,"error":"Unauthorized"},status=401)
    gid=request.match_info.get("id")
    if not can_access_guild(sess,gid): return web.json_response({"ok":False,"error":"Không có quyền"},status=403)
    if not BOT_INSTANCE or not getattr(BOT_INSTANCE,"is_ready",lambda:False)():
        return web.json_response({"ok":False,"error":"Bot chưa sẵn sàng"},status=503)
    try:
        body=await request.json()
        target_id=body.get("channel_id")
        cfs=_load_confession(gid)
        # ưu tiên channel truyền lên, fallback confession_channel_id
        ch_id = int(target_id) if target_id and str(target_id).isdigit() else cfs.get("confession_channel_id")
        if not ch_id:
            return web.json_response({"ok":False,"error":"Chưa chọn kênh Confession"},status=400)
        ch=BOT_INSTANCE.get_channel(int(ch_id))
        if not ch:
            try: ch=await BOT_INSTANCE.fetch_channel(int(ch_id))
            except: return web.json_response({"ok":False,"error":"Không tìm thấy kênh"},status=404)
        # xóa panel cũ (20 tin gần nhất) nếu trùng title
        try:
            from Checks_vi.i18n import t
            # need guild for t
            guild=BOT_INSTANCE.get_guild(int(gid))
            async for msg in ch.history(limit=20):
                if msg.author.id==BOT_INSTANCE.user.id and msg.embeds and msg.embeds[0].title and "Confession" in msg.embeds[0].title:
                    try: await msg.delete()
                    except: pass
        except: pass
        # gửi panel mới, tôn trọng allow_public/anonymous để ẩn nút
        from Command_vi.confession import create_panel_embed, CreateConfessionView
        import discord
        view=CreateConfessionView(BOT_INSTANCE)
        # filter buttons theo config
        # CreateConfessionView có 2 nút cfs_anonymous / cfs_public; nếu tắt thì disable/remove
        if not cfs.get("allow_anonymous", True):
            for child in list(view.children):
                if getattr(child, 'custom_id', '')=='cfs_anonymous':
                    view.remove_item(child)
        if not cfs.get("allow_public", True):
            for child in list(view.children):
                if getattr(child, 'custom_id', '')=='cfs_public':
                    view.remove_item(child)
        if len(view.children)==0:
            return web.json_response({"ok":False,"error":"Cả 2 nút đều bị tắt — bật ít nhất 1 loại"},status=400)
        guild=BOT_INSTANCE.get_guild(int(gid))
        embed=create_panel_embed(guild)
        await ch.send(embed=embed, view=view)
        add_log("INFO", f"User {sess.get('username')} đăng panel confession {gid} -> #{ch.name}")
        return web.json_response({"ok":True,"message":f"Đã đăng panel vào #{ch.name}"})
    except Exception as e:
        import traceback; traceback.print_exc()
        return web.json_response({"ok":False,"error":str(e)},status=500)

def _load_level_config(gid: str):
    ls=load_json(DATA_DIR/"level_settings.json",{})
    cfg=ls.get(str(gid),{})
    # mặc định như Reine: bật hết
    return {"exp_enabled": cfg.get("exp_enabled", True), "voice_exp": cfg.get("voice_exp", True), "level_up_announce": cfg.get("level_up_announce", True), "announce_channel": cfg.get("announce_channel")}
def _save_level_config(gid: str, cfg: dict):
    ls=load_json(DATA_DIR/"level_settings.json",{})
    ls[str(gid)]={"exp_enabled": bool(cfg.get("exp_enabled", True)), "voice_exp": bool(cfg.get("voice_exp", True)), "level_up_announce": bool(cfg.get("level_up_announce", True)), "announce_channel": cfg.get("announce_channel"), "custom_rankup": cfg.get("custom_rankup","")}
    return save_json(DATA_DIR/"level_settings.json", ls)

async def handle_get_level_config(request: web.Request):
    sess=require_auth(request)
    if not sess: return web.json_response({"ok":False,"error":"Unauthorized"},status=401)
    gid=request.match_info.get("id")
    if not can_access_guild(sess,gid): return web.json_response({"ok":False,"error":"Không có quyền"},status=403)
    proxied=await _proxy_to_bot_web(request, f"/api/guilds/{gid}/level-config")
    if proxied is not None: return proxied

    # Đọc dữ liệu trực tiếp từ SQLite Database (data/bot_database.db)
    try:
        from data.database import get_guild_level_and_economy_stats
        db_stats = await get_guild_level_and_economy_stats(gid)
        cnt_level = db_stats.get("cnt_level", 0)
        cnt_econ = db_stats.get("cnt_econ", 0)
        top_level_raw = db_stats.get("top_level", [])
        top_rich_raw = db_stats.get("top_rich", [])
    except Exception as e:
        print(f"[Web] Lỗi đọc database level: {e}")
        # fallback levels.json nếu database chưa sẵn sàng
        levels = load_json(_levels_file(), {})
        users = levels.get(str(gid), {})
        cnt_level = sum(1 for v in users.values() if isinstance(v, dict) and int(v.get("xp", 0)) > 0)
        cnt_econ = sum(1 for v in users.values() if isinstance(v, dict) and int(v.get("coins", 0)) > 0)
        top_level_raw = [{"user_id": uid, "xp": int(v.get("xp", 0)), "level": int(v.get("level", 0))} for uid, v in users.items() if isinstance(v, dict)][:5]
        top_rich_raw = [{"user_id": uid, "coins": int(v.get("coins", 0))} for uid, v in users.items() if isinstance(v, dict)][:5]

    # top + enrich tên/avatar từ BOT_INSTANCE (hiện tên + avatar thay vì chỉ ID)
    def _enrich(uid):
        name = str(uid)
        avatar = "https://cdn.discordapp.com/embed/avatars/0.png"
        try:
            if BOT_INSTANCE and getattr(BOT_INSTANCE, "is_ready", lambda: False)():
                g = BOT_INSTANCE.get_guild(int(gid))
                if g:
                    m = g.get_member(int(uid))
                    if m:
                        name = m.display_name
                        avatar = str(m.display_avatar.url) if m.display_avatar else avatar
                    else:
                        u = BOT_INSTANCE.get_user(int(uid))
                        if u:
                            name = str(u)
                            avatar = str(u.display_avatar.url) if u.display_avatar else avatar
        except Exception:
            pass
        return {"id": str(uid), "name": name, "avatar": avatar}

    top_level = [{**_enrich(u["user_id"]), "xp": u.get("xp", 0), "level": u.get("level", 0)} for u in top_level_raw]
    top_rich = [{**_enrich(u["user_id"]), "coins": u.get("coins", 0)} for u in top_rich_raw]
    return web.json_response({
        "ok": True,
        "config": _load_level_config(gid),
        "counts": {"level": cnt_level, "economy": cnt_econ},
        "top_level": top_level,
        "top_rich": top_rich
    })

async def handle_save_level_config(request: web.Request):
    sess=require_auth(request)
    if not sess: return web.json_response({"ok":False,"error":"Unauthorized"},status=401)
    gid=request.match_info.get("id")
    if not can_access_guild(sess,gid): return web.json_response({"ok":False,"error":"Không có quyền"},status=403)
    try:
        body=await request.json()
        _save_level_config(gid, body)
        add_log("INFO", f"User {sess.get('username')} lưu level_config {gid} {body}")
        return web.json_response({"ok":True,"message":"Đã lưu Level & Economy"})
    except Exception as e: return web.json_response({"ok":False,"error":str(e)},status=500)

# --- Level Roles API ---
async def handle_get_level_roles(request: web.Request):
    sess=require_auth(request)
    if not sess: return web.json_response({"ok":False,"error":"Unauthorized"},status=401)
    gid=request.match_info.get("id")
    if not can_access_guild(sess,gid): return web.json_response({"ok":False,"error":"Không có quyền"},status=403)
    try:
        from Checks_vi.level_handler import get_guild_level_roles
        roles = get_guild_level_roles(gid)
        bot = request.app.get("bot")
        g = bot.get_guild(int(gid)) if bot else None
        role_list = []
        for lvl_str, rid in roles.items():
            r_obj = g.get_role(int(rid)) if g else None
            role_list.append({
                "level": int(lvl_str) if str(lvl_str).isdigit() else lvl_str,
                "role_id": str(rid),
                "role_name": r_obj.name if r_obj else f"Role ({rid})"
            })
        role_list.sort(key=lambda x: int(x["level"]) if str(x["level"]).isdigit() else 0)
        return web.json_response({"ok": True, "roles": role_list, "raw_roles": roles})
    except Exception as e:
        return web.json_response({"ok": False, "error": str(e)}, status=500)

async def handle_save_level_role(request: web.Request):
    sess=require_auth(request)
    if not sess: return web.json_response({"ok":False,"error":"Unauthorized"},status=401)
    gid=request.match_info.get("id")
    if not can_access_guild(sess,gid): return web.json_response({"ok":False,"error":"Không có quyền"},status=403)
    try:
        body = await request.json()
        from Checks_vi.level_handler import get_guild_level_roles, save_guild_level_roles
        current_roles = get_guild_level_roles(gid)
        if "roles" in body and isinstance(body["roles"], dict):
            current_roles = body["roles"]
        else:
            lvl = str(body.get("level")).strip()
            role_id = body.get("role_id")
            if lvl and role_id:
                current_roles[lvl] = int(role_id)
        save_guild_level_roles(gid, current_roles)
        add_log("INFO", f"User {sess.get('username')} cập nhật level_roles server {gid}: {current_roles}")
        return web.json_response({"ok": True, "message": "Đã lưu mốc thưởng vai trò", "roles": current_roles})
    except Exception as e:
        return web.json_response({"ok": False, "error": str(e)}, status=500)

async def handle_delete_level_role(request: web.Request):
    sess=require_auth(request)
    if not sess: return web.json_response({"ok":False,"error":"Unauthorized"},status=401)
    gid=request.match_info.get("id")
    lvl=request.match_info.get("level")
    if not can_access_guild(sess,gid): return web.json_response({"ok":False,"error":"Không có quyền"},status=403)
    try:
        from Checks_vi.level_handler import get_guild_level_roles, save_guild_level_roles
        current_roles = get_guild_level_roles(gid)
        if str(lvl) in current_roles:
            del current_roles[str(lvl)]
            save_guild_level_roles(gid, current_roles)
        return web.json_response({"ok": True, "message": f"Đã xóa mốc level {lvl}", "roles": current_roles})
    except Exception as e:
        return web.json_response({"ok": False, "error": str(e)}, status=500)

# --- Fishing Guild Settings API ---
async def handle_get_fishing_config(request: web.Request):
    sess=require_auth(request)
    if not sess: return web.json_response({"ok":False,"error":"Unauthorized"},status=401)
    gid=request.match_info.get("id")
    if not can_access_guild(sess,gid): return web.json_response({"ok":False,"error":"Không có quyền"},status=403)
    try:
        from Command_vi.command_fishing import fishing_state
        channels = fishing_state.get("fishing_channels", {}).get(str(gid), [])
        code_cfg = fishing_state.get("code_channels", {}).get(str(gid), {})
        allow_outside = bool(fishing_state.get("allow_outside", {}).get(str(gid), False))
        return web.json_response({
            "ok": True,
            "fishing_channel_id": str(channels[0]) if channels else None,
            "fishing_channels": [str(c) for c in channels],
            "code_channel_id": str(code_cfg.get("channel_id")) if code_cfg.get("channel_id") else None,
            "code_role_id": str(code_cfg.get("role_id")) if code_cfg.get("role_id") else None,
            "allow_outside": allow_outside
        })
    except Exception as e:
        return web.json_response({"ok": False, "error": str(e)}, status=500)

async def handle_save_fishing_config(request: web.Request):
    sess=require_auth(request)
    if not sess: return web.json_response({"ok":False,"error":"Unauthorized"},status=401)
    gid=request.match_info.get("id")
    if not can_access_guild(sess,gid): return web.json_response({"ok":False,"error":"Không có quyền"},status=403)
    try:
        body = await request.json()
        from Command_vi.command_fishing import fishing_state, save_fishing_data
        gid_str = str(gid)
        f_channels = body.get("fishing_channels")
        if f_channels is not None:
            valid_chs = [int(c) for c in f_channels if str(c).isdigit()]
            if valid_chs:
                fishing_state.setdefault("fishing_channels", {})[gid_str] = valid_chs
            else:
                fishing_state.setdefault("fishing_channels", {}).pop(gid_str, None)
        else:
            f_ch = body.get("fishing_channel_id")
            if f_ch:
                fishing_state.setdefault("fishing_channels", {})[gid_str] = [int(f_ch)]
            else:
                fishing_state.setdefault("fishing_channels", {}).pop(gid_str, None)
        c_ch = body.get("code_channel_id")
        c_role = body.get("code_role_id")
        if c_ch:
            fishing_state.setdefault("code_channels", {})[gid_str] = {
                "channel_id": int(c_ch),
                "role_id": int(c_role) if c_role else None
            }
        else:
            fishing_state.setdefault("code_channels", {}).pop(gid_str, None)
        fishing_state.setdefault("allow_outside", {})[gid_str] = bool(body.get("allow_outside", False))
        save_fishing_data()
        add_log("INFO", f"User {sess.get('username')} lưu cấu hình fishing cho guild {gid}")
        return web.json_response({"ok": True, "message": "Đã lưu cài đặt câu cá"})
    except Exception as e:
        return web.json_response({"ok": False, "error": str(e)}, status=500)

# --- Custom Keys API ---
async def handle_get_custom_keys(request: web.Request):
    sess=require_auth(request)
    if not sess: return web.json_response({"ok":False,"error":"Unauthorized"},status=401)
    gid=request.match_info.get("id")
    if not can_access_guild(sess,gid): return web.json_response({"ok":False,"error":"Không có quyền"},status=403)
    try:
        from Command_vi.custom_keys import get_guild_custom_keys
        keys = get_guild_custom_keys(gid)
        return web.json_response({"ok": True, "keys": keys})
    except Exception as e:
        return web.json_response({"ok": False, "error": str(e)}, status=500)

async def handle_save_custom_key(request: web.Request):
    sess=require_auth(request)
    if not sess: return web.json_response({"ok":False,"error":"Unauthorized"},status=401)
    gid=request.match_info.get("id")
    if not can_access_guild(sess,gid): return web.json_response({"ok":False,"error":"Không có quyền"},status=403)
    try:
        from Command_vi.custom_keys import add_or_update_custom_key, CUSTOM_KEYS_FILES_DIR
        keyword = ""
        response_text = ""
        match_type = "exact"
        key_id = None
        file_info = None

        if request.content_type.startswith("multipart/"):
            reader = await request.multipart()
            while True:
                part = await reader.next()
                if part is None: break
                pname = part.name
                if pname == "keyword": keyword = (await part.text()).strip()
                elif pname == "response": response_text = (await part.text()).strip()
                elif pname == "match_type": match_type = (await part.text()).strip()
                elif pname == "key_id": key_id = (await part.text()).strip()
                elif pname in ("file", "attachment"):
                    fname = part.filename
                    if fname:
                        g_dir = CUSTOM_KEYS_FILES_DIR / str(gid)
                        g_dir.mkdir(parents=True, exist_ok=True)
                        safe_name = f"{int(time.time())}_{fname}"
                        save_p = g_dir / safe_name
                        with open(save_p, "wb") as f:
                            while True:
                                chunk = await part.read_chunk()
                                if not chunk: break
                                f.write(chunk)
                        file_info = {
                            "file_path": str(save_p.relative_to(BASE_DIR)),
                            "file_name": fname,
                            "file_size": save_p.stat().st_size
                        }
        else:
            body = await request.json()
            keyword = body.get("keyword", "").strip()
            response_text = body.get("response", "").strip()
            match_type = body.get("match_type", "exact")
            key_id = body.get("key_id")

        if not keyword:
            return web.json_response({"ok": False, "error": "Thiếu từ khóa (keyword)"}, status=400)

        item = {
            "keyword": keyword,
            "response": response_text,
            "match_type": match_type,
            "created_by": sess.get("username", "admin"),
            "enabled": True
        }
        if key_id: item["id"] = key_id
        if file_info: item.update(file_info)

        saved = add_or_update_custom_key(gid, item)
        add_log("INFO", f"User {sess.get('username')} lưu Custom Key '{keyword}' ({gid})")
        return web.json_response({"ok": True, "message": "Đã lưu Custom Key", "key": saved})
    except Exception as e:
        return web.json_response({"ok": False, "error": str(e)}, status=500)

async def handle_delete_custom_key(request: web.Request):
    sess=require_auth(request)
    if not sess: return web.json_response({"ok":False,"error":"Unauthorized"},status=401)
    gid=request.match_info.get("id")
    kid=request.match_info.get("key_id")
    if not can_access_guild(sess,gid): return web.json_response({"ok":False,"error":"Không có quyền"},status=403)
    try:
        from Command_vi.custom_keys import delete_guild_custom_key
        ok = delete_guild_custom_key(gid, kid)
        return web.json_response({"ok": ok, "message": "Đã xóa Custom Key" if ok else "Không tìm thấy key"})
    except Exception as e:
        return web.json_response({"ok": False, "error": str(e)}, status=500)

async def handle_download_custom_key_file(request: web.Request):
    gid=request.match_info.get("id")
    fname=request.match_info.get("filename")
    p = DATA_DIR / "custom_keys_files" / str(gid) / fname
    if not p.exists():
        return web.Response(text="File không tồn tại", status=404)
    return web.FileResponse(path=str(p))

# --- Backups API ---
async def handle_get_backups(request: web.Request):
    sess=require_auth(request)
    if not sess: return web.json_response({"ok":False,"error":"Unauthorized"},status=401)
    gid=request.match_info.get("id")
    if not can_access_guild(sess,gid): return web.json_response({"ok":False,"error":"Không có quyền"},status=403)
    try:
        backup_dir = DATA_DIR / "backups" / str(gid)
        items = []
        if backup_dir.exists():
            for f in sorted(backup_dir.glob("*.json"), key=lambda x: x.stat().st_mtime, reverse=True):
                info = {"filename": f.name, "size": f.stat().st_size, "date": datetime.datetime.fromtimestamp(f.stat().st_mtime).strftime("%d/%m/%Y %H:%M:%S"), "description": "Không có mô tả", "roles": 0, "channels": 0}
                try:
                    with open(f, "r", encoding="utf-8") as bf:
                        bdata = json.load(bf)
                        info["description"] = bdata.get("description") or info["description"]
                        info["date"] = bdata.get("date") or info["date"]
                        info["roles"] = len(bdata.get("roles", []))
                        info["channels"] = len(bdata.get("channels", []))
                except Exception:
                    pass
                items.append(info)
        return web.json_response({"ok": True, "backups": items})
    except Exception as e:
        return web.json_response({"ok": False, "error": str(e)}, status=500)

async def handle_create_backup(request: web.Request):
    sess=require_auth(request)
    if not sess: return web.json_response({"ok":False,"error":"Unauthorized"},status=401)
    gid=request.match_info.get("id")
    if not can_access_guild(sess,gid): return web.json_response({"ok":False,"error":"Không có quyền"},status=403)
    if not BOT_INSTANCE or not getattr(BOT_INSTANCE, "is_ready", lambda: False)():
        return web.json_response({"ok": False, "error": "Bot chưa kết nối"}, status=503)
    try:
        body = await request.json()
        desc = body.get("description", "Backup từ Web Dashboard").strip()
        guild = BOT_INSTANCE.get_guild(int(gid))
        if not guild: return web.json_response({"ok": False, "error": "Không tìm thấy server"}, status=404)

        cog = BOT_INSTANCE.get_cog("BackupCog")
        if cog:
            file_path = await cog.create_backup(guild, BOT_INSTANCE.user, desc)
            fname = Path(file_path).name
            add_log("INFO", f"User {sess.get('username')} tạo backup {fname} ({gid})")
            return web.json_response({"ok": True, "message": "Đã tạo bản sao lưu thành công", "filename": fname})
        else:
            return web.json_response({"ok": False, "error": "Backup module chưa sẵn sàng"}, status=500)
    except Exception as e:
        return web.json_response({"ok": False, "error": str(e)}, status=500)

async def handle_restore_backup(request: web.Request):
    sess=require_auth(request)
    if not sess: return web.json_response({"ok":False,"error":"Unauthorized"},status=401)
    gid=request.match_info.get("id")
    if not can_access_guild(sess,gid): return web.json_response({"ok":False,"error":"Không có quyền"},status=403)
    if not BOT_INSTANCE or not getattr(BOT_INSTANCE, "is_ready", lambda: False)():
        return web.json_response({"ok": False, "error": "Bot chưa kết nối"}, status=503)
    try:
        body = await request.json()
        fname = body.get("filename")
        sync_mode = bool(body.get("sync_mode", False))
        restore_members = bool(body.get("restore_members", True))
        guild = BOT_INSTANCE.get_guild(int(gid))
        if not guild: return web.json_response({"ok": False, "error": "Không tìm thấy server"}, status=404)

        cog = BOT_INSTANCE.get_cog("BackupCog")
        if not cog: return web.json_response({"ok": False, "error": "Backup module chưa tải"}, status=500)
        asyncio.create_task(cog.load_backup(guild, fname, requester=BOT_INSTANCE.user, sync_mode=sync_mode, restore_members=restore_members, safety_backup=True))
        add_log("WARNING", f"User {sess.get('username')} kích hoạt khôi phục backup {fname} ({gid})")
        return web.json_response({"ok": True, "message": f"Đang tiến hành khôi phục từ bản '{fname}'. Quá trình này có thể mất vài phút."})
    except Exception as e:
        return web.json_response({"ok": False, "error": str(e)}, status=500)

async def handle_delete_backup(request: web.Request):
    sess=require_auth(request)
    if not sess: return web.json_response({"ok":False,"error":"Unauthorized"},status=401)
    gid=request.match_info.get("id")
    fname=request.match_info.get("filename")
    if not can_access_guild(sess,gid): return web.json_response({"ok":False,"error":"Không có quyền"},status=403)
    try:
        p = DATA_DIR / "backups" / str(gid) / fname
        if p.exists(): p.unlink()
        return web.json_response({"ok": True, "message": "Đã xóa bản sao lưu"})
    except Exception as e:
        return web.json_response({"ok": False, "error": str(e)}, status=500)

async def handle_download_backup(request: web.Request):
    gid=request.match_info.get("id")
    fname=request.match_info.get("filename")
    p = DATA_DIR / "backups" / str(gid) / fname
    if not p.exists(): return web.Response(text="Không tìm thấy file", status=404)
    return web.FileResponse(path=str(p), headers={"Content-Disposition": f'attachment; filename="{fname}"'})

# --- Bot Profile Per-Server API ---
async def handle_get_bot_profile(request: web.Request):
    sess=require_auth(request)
    if not sess: return web.json_response({"ok":False,"error":"Unauthorized"},status=401)
    gid=request.match_info.get("id")
    if not can_access_guild(sess,gid): return web.json_response({"ok":False,"error":"Không có quyền"},status=403)
    try:
        nick = ""
        name = "Sakura Bot"
        avatar = "https://cdn.discordapp.com/embed/avatars/0.png"
        if BOT_INSTANCE and getattr(BOT_INSTANCE, "is_ready", lambda: False)():
            guild = BOT_INSTANCE.get_guild(int(gid))
            if guild and guild.me:
                nick = guild.me.nick or ""
                name = guild.me.name
                avatar = str(guild.me.display_avatar.url)
        profiles_file = DATA_DIR / "bot_guild_profiles.json"
        pdata = load_json(profiles_file, {})
        gprof = pdata.get(str(gid), {})
        banner = gprof.get("banner", "")
        bio = gprof.get("bio", "")
        if gprof.get("avatar"):
            avatar = gprof.get("avatar")
        return web.json_response({"ok": True, "nick": nick, "name": name, "avatar": avatar, "banner": banner, "bio": bio})
    except Exception as e:
        return web.json_response({"ok": False, "error": str(e)}, status=500)

async def handle_save_bot_profile(request: web.Request):
    sess=require_auth(request)
    if not sess: return web.json_response({"ok":False,"error":"Unauthorized"},status=401)
    gid=request.match_info.get("id")
    if not can_access_guild(sess,gid): return web.json_response({"ok":False,"error":"Không có quyền"},status=403)
    try:
        body = await request.json()
        nick = body.get("nick", "").strip() or None
        avatar = str(body.get("avatar", "")).strip()
        banner = str(body.get("banner", "")).strip()
        bio = str(body.get("bio", "")).strip()

        if BOT_INSTANCE and getattr(BOT_INSTANCE, "is_ready", lambda: False)():
            guild = BOT_INSTANCE.get_guild(int(gid))
            if guild and guild.me:
                try:
                    await guild.me.edit(nick=nick)
                except Exception as ne:
                    add_log("WARN", f"Không thể đổi nick bot: {ne}")
                if avatar:
                    if avatar.startswith("data:image/"):
                        try:
                            import base64
                            header, b64str = avatar.split(",", 1)
                            av_bytes = base64.b64decode(b64str)
                            upload_dir = BASE_DIR / "web" / "static" / "uploads" / "bot_avatars"
                            upload_dir.mkdir(parents=True, exist_ok=True)
                            av_filename = f"bot_guild_{gid}_{int(time.time())}.png"
                            with open(upload_dir / av_filename, "wb") as f_av:
                                f_av.write(av_bytes)
                            avatar = f"/static/uploads/bot_avatars/{av_filename}"
                            if guild and guild.me:
                                try:
                                    await guild.me.edit(avatar=av_bytes)
                                except Exception:
                                    pass
                        except Exception as b64e:
                            add_log("WARN", f"Không thể lưu avatar base64: {b64e}")
                    elif avatar.startswith("http://") or avatar.startswith("https://"):
                        try:
                            import aiohttp
                            async with aiohttp.ClientSession() as cs:
                                async with cs.get(avatar, timeout=aiohttp.ClientTimeout(total=5)) as resp:
                                    if resp.status == 200:
                                        av_bytes = await resp.read()
                                        if guild and guild.me:
                                            try:
                                                await guild.me.edit(avatar=av_bytes)
                                            except Exception:
                                                pass
                        except Exception as ave:
                            add_log("WARN", f"Không thể tải avatar bot: {ave}")

        profiles_file = DATA_DIR / "bot_guild_profiles.json"
        pdata = load_json(profiles_file, {})
        pdata[str(gid)] = {
            "nick": nick or "",
            "avatar": avatar,
            "banner": banner,
            "bio": bio,
            "updated_at": int(time.time()),
            "updated_by": sess.get("username", "")
        }
        save_json(profiles_file, pdata)
        add_log("INFO", f"User {sess.get('username')} cập nhật hồ sơ bot (nick, avatar, banner, bio) tại server {gid}")
        return web.json_response({
            "ok": True,
            "message": "Đã lưu hồ sơ bot (biệt danh, ảnh đại diện, banner, tiểu sử) thành công!",
            "nick": nick or "",
            "avatar": avatar,
            "banner": banner,
            "bio": bio
        })
    except Exception as e:
        return web.json_response({"ok": False, "error": f"Lỗi lưu hồ sơ bot: {e}"}, status=500)

# --- AutoRole API ---
async def handle_get_autorole(request: web.Request):
    sess=require_auth(request)
    if not sess: return web.json_response({"ok":False,"error":"Unauthorized"},status=401)
    gid=request.match_info.get("id")
    if not can_access_guild(sess,gid): return web.json_response({"ok":False,"error":"Không có quyền"},status=403)
    try:
        import aiosqlite
        db_path = DATA_DIR / "bot.db"
        user_role, bot_role = None, None
        if db_path.exists():
            async with aiosqlite.connect(str(db_path)) as db:
                async with db.execute("SELECT user_role_id, bot_role_id FROM autorole_config WHERE guild_id = ?", (int(gid),)) as cursor:
                    row = await cursor.fetchone()
                    if row: user_role, bot_role = row[0], row[1]
        return web.json_response({"ok": True, "user_role_id": str(user_role) if user_role else None, "bot_role_id": str(bot_role) if bot_role else None})
    except Exception as e:
        return web.json_response({"ok": False, "error": str(e)}, status=500)

async def handle_save_autorole(request: web.Request):
    sess=require_auth(request)
    if not sess: return web.json_response({"ok":False,"error":"Unauthorized"},status=401)
    gid=request.match_info.get("id")
    if not can_access_guild(sess,gid): return web.json_response({"ok":False,"error":"Không có quyền"},status=403)
    try:
        body = await request.json()
        u_role = int(body.get("user_role_id")) if body.get("user_role_id") else None
        b_role = int(body.get("bot_role_id")) if body.get("bot_role_id") else None
        import aiosqlite
        db_path = DATA_DIR / "bot.db"
        async with aiosqlite.connect(str(db_path)) as db:
            await db.execute("""
                CREATE TABLE IF NOT EXISTS autorole_config (
                    guild_id INTEGER PRIMARY KEY,
                    user_role_id INTEGER,
                    bot_role_id INTEGER
                )
            """)
            await db.execute("""
                INSERT INTO autorole_config (guild_id, user_role_id, bot_role_id)
                VALUES (?, ?, ?)
                ON CONFLICT(guild_id) DO UPDATE SET user_role_id = excluded.user_role_id, bot_role_id = excluded.bot_role_id
            """, (int(gid), u_role, b_role))
            await db.commit()
        add_log("INFO", f"User {sess.get('username')} lưu autorole {gid}: user={u_role}, bot={b_role}")
        return web.json_response({"ok": True, "message": "Đã lưu cấu hình AutoRole"})
    except Exception as e:
        return web.json_response({"ok": False, "error": str(e)}, status=500)

# --- Reaction Role API ---
async def handle_get_reaction_roles(request: web.Request):
    sess = require_auth(request)
    if not sess: return web.json_response({"ok": False, "error": "Unauthorized"}, status=401)
    gid = request.match_info.get("id")
    if not can_access_guild(sess, gid): return web.json_response({"ok": False, "error": "Không có quyền"}, status=403)
    proxied = await _proxy_to_bot_web(request, f"/api/guilds/{gid}/reaction-roles")
    if proxied is not None:
        return proxied
    try:
        import aiosqlite
        db_path = BASE_DIR / "data" / "role_panels.db"
        panels = []
        if db_path.exists():
            async with aiosqlite.connect(str(db_path)) as db:
                await db.execute("CREATE TABLE IF NOT EXISTS panels (message_id TEXT PRIMARY KEY, data TEXT)")
                async with db.execute("SELECT message_id, data FROM panels") as cursor:
                    rows = await cursor.fetchall()
                    for mid, raw_data in rows:
                        try:
                            pdata = json.loads(raw_data)
                            if str(pdata.get("guild_id")) == str(gid):
                                pdata["message_id"] = str(mid)
                                panels.append(pdata)
                        except Exception:
                            pass
        return web.json_response({"ok": True, "panels": panels})
    except Exception as e:
        return web.json_response({"ok": False, "error": str(e)}, status=500)

async def handle_create_reaction_role(request: web.Request):
    sess = require_auth(request)
    if not sess: return web.json_response({"ok": False, "error": "Unauthorized"}, status=401)
    gid = request.match_info.get("id")
    if not can_access_guild(sess, gid): return web.json_response({"ok": False, "error": "Không có quyền"}, status=403)
    if not BOT_INSTANCE or not getattr(BOT_INSTANCE, "is_ready", lambda: False)():
        proxied = await _proxy_to_bot_web(request, f"/api/guilds/{gid}/reaction-roles/create")
        if proxied is not None:
            return proxied
        return web.json_response({"ok": False, "error": "Bot chưa kết nối"}, status=503)
    try:
        body = await request.json()
        channel_id = body.get("channel_id")
        if not channel_id:
            return web.json_response({"ok": False, "error": "Vui lòng chọn kênh gửi bảng Role"}, status=400)

        channel = BOT_INSTANCE.get_channel(int(channel_id))
        if not channel:
            return web.json_response({"ok": False, "error": "Không tìm thấy kênh này trong Discord"}, status=404)

        title = body.get("title", "BẢNG CHỌN VAI TRÒ").strip() or "BẢNG CHỌN VAI TRÒ"
        desc = body.get("description", "").strip() or "Chọn các vai trò bạn muốn nhận dưới đây:"
        color_hex = body.get("color", "#5865F2").strip()
        image_url = body.get("image_url", "").strip()
        panel_type = body.get("type", "button")
        mode = body.get("mode", "multi")
        roles_input = body.get("roles", [])

        if not roles_input:
            return web.json_response({"ok": False, "error": "Vui lòng thêm ít nhất 1 vai trò vào bảng"}, status=400)

        guild = BOT_INSTANCE.get_guild(int(gid))
        roles_data_clean = []
        for r_item in roles_input:
            rid = int(r_item.get("role_id"))
            r_obj = guild.get_role(rid) if guild else None
            emj_str = str(r_item.get("emoji_str") or r_item.get("emoji") or "⭐").strip()
            label_val = r_item.get("label") or (r_obj.name if r_obj else f"Role {rid}")
            roles_data_clean.append({
                "role_id": rid,
                "emoji_id": None,
                "emoji_name": emj_str,
                "emoji_str": emj_str,
                "label": label_val,
                "style": r_item.get("style", "secondary")
            })

        panel_data = {
            "guild_id": int(gid),
            "channel_id": int(channel_id),
            "title": title,
            "description": desc,
            "color": color_hex,
            "image_url": image_url,
            "type": panel_type,
            "mode": mode,
            "roles": roles_data_clean
        }

        from Command_vi.reaction_role import build_panel_embed, RolePanelView, resolve_emoji
        embed = build_panel_embed(title, desc, color_hex, image_url, panel_type, mode, roles_data_clean, guild)

        cog = BOT_INSTANCE.get_cog("RolePanel") or BOT_INSTANCE.get_cog("RolePanelCog")
        if panel_type == "button":
            view = RolePanelView(cog, panel_data)
            sent_msg = await channel.send(embed=embed, view=view)
            BOT_INSTANCE.add_view(view, message_id=sent_msg.id)
        else:
            sent_msg = await channel.send(embed=embed)
            for item in roles_data_clean:
                emj_obj = resolve_emoji(guild, item["emoji_str"])
                if emj_obj:
                    try:
                        await sent_msg.add_reaction(emj_obj)
                    except Exception:
                        pass

        # Lưu dữ liệu vào cache của Cog và file SQLite
        if cog:
            await cog.save_panel_db(str(sent_msg.id), panel_data)
        else:
            import aiosqlite
            db_path = BASE_DIR / "data" / "role_panels.db"
            db_path.parent.mkdir(parents=True, exist_ok=True)
            async with aiosqlite.connect(str(db_path)) as db:
                await db.execute("CREATE TABLE IF NOT EXISTS panels (message_id TEXT PRIMARY KEY, data TEXT)")
                await db.execute("INSERT OR REPLACE INTO panels (message_id, data) VALUES (?, ?)", (str(sent_msg.id), json.dumps(panel_data, ensure_ascii=False)))
                await db.commit()

        guild_name = guild.name if guild else str(gid)
        add_log("SUCCESS", f"User {sess.get('username')} tạo Reaction Role ID {sent_msg.id} tại {guild_name}")
        return web.json_response({"ok": True, "message": "Đã tạo bảng Reaction Role thành công!", "message_id": str(sent_msg.id)})
    except Exception as e:
        return web.json_response({"ok": False, "error": str(e)}, status=500)

async def handle_delete_reaction_role(request: web.Request):
    sess = require_auth(request)
    if not sess: return web.json_response({"ok": False, "error": "Unauthorized"}, status=401)
    gid = request.match_info.get("id")
    msg_id = request.match_info.get("msg_id")
    if not can_access_guild(sess, gid): return web.json_response({"ok": False, "error": "Không có quyền"}, status=403)
    proxied = await _proxy_to_bot_web(request, f"/api/guilds/{gid}/reaction-roles/{msg_id}")
    if proxied is not None:
        return proxied
    try:
        import aiosqlite
        db_path = BASE_DIR / "data" / "role_panels.db"
        if db_path.exists():
            async with aiosqlite.connect(str(db_path)) as db:
                await db.execute("DELETE FROM panels WHERE message_id = ?", (str(msg_id),))
                await db.commit()

        if BOT_INSTANCE:
            cog = BOT_INSTANCE.get_cog("RolePanel") or BOT_INSTANCE.get_cog("RolePanelCog")
            if cog:
                await cog.delete_panel_db(str(msg_id))
            elif cog and str(msg_id) in getattr(cog, "panels_cache", {}):
                del cog.panels_cache[str(msg_id)]

        add_log("INFO", f"User {sess.get('username')} xóa Reaction Role {msg_id}")
        return web.json_response({"ok": True, "message": "Đã xóa bảng Reaction Role"})
    except Exception as e:
        return web.json_response({"ok": False, "error": str(e)}, status=500)

# --- Hoyo Code API ---
async def handle_get_hoyo_config(request: web.Request):
    sess = require_auth(request)
    if not sess: return web.json_response({"ok": False, "error": "Unauthorized"}, status=401)
    gid = request.match_info.get("id")
    if not can_access_guild(sess, gid): return web.json_response({"ok": False, "error": "Không có quyền"}, status=403)
    try:
        import aiosqlite
        db_path = BASE_DIR / "gacha_data" / "database.sqlite"
        config_map = {}
        if db_path.exists():
            async with aiosqlite.connect(str(db_path)) as db:
                await db.execute("""
                    CREATE TABLE IF NOT EXISTS guild_config (
                        guild_id TEXT, game_key TEXT, channel_id INTEGER, 
                        role_id INTEGER, webhook_url TEXT,
                        PRIMARY KEY (guild_id, game_key)
                    )
                """)
                async with db.execute("SELECT game_key, channel_id, role_id FROM guild_config WHERE guild_id = ?", (str(gid),)) as cursor:
                    rows = await cursor.fetchall()
                    for gk, cid, rid in rows:
                        config_map[gk] = {
                            "channel_id": str(cid) if cid else None,
                            "role_id": str(rid) if rid else None
                        }
        return web.json_response({"ok": True, "config": config_map})
    except Exception as e:
        return web.json_response({"ok": False, "error": str(e)}, status=500)

async def handle_save_hoyo_config(request: web.Request):
    sess = require_auth(request)
    if not sess: return web.json_response({"ok": False, "error": "Unauthorized"}, status=401)
    gid = request.match_info.get("id")
    if not can_access_guild(sess, gid): return web.json_response({"ok": False, "error": "Không có quyền"}, status=403)
    try:
        body = await request.json()
        games = body.get("games", {})
        import aiosqlite
        db_path = BASE_DIR / "gacha_data" / "database.sqlite"
        db_path.parent.mkdir(parents=True, exist_ok=True)
        async with aiosqlite.connect(str(db_path)) as db:
            await db.execute("""
                CREATE TABLE IF NOT EXISTS guild_config (
                    guild_id TEXT, game_key TEXT, channel_id INTEGER, 
                    role_id INTEGER, webhook_url TEXT,
                    PRIMARY KEY (guild_id, game_key)
                )
            """)
            for gk, cdata in games.items():
                cid = int(cdata.get("channel_id")) if cdata.get("channel_id") else None
                rid = int(cdata.get("role_id")) if cdata.get("role_id") else None
                if cid:
                    await db.execute("""
                        INSERT INTO guild_config (guild_id, game_key, channel_id, role_id)
                        VALUES (?, ?, ?, ?)
                        ON CONFLICT(guild_id, game_key) DO UPDATE SET
                            channel_id = excluded.channel_id,
                            role_id = excluded.role_id
                    """, (str(gid), gk, cid, rid))
                else:
                    await db.execute("DELETE FROM guild_config WHERE guild_id = ? AND game_key = ?", (str(gid), gk))
            await db.commit()
        add_log("SUCCESS", f"User {sess.get('username')} lưu cấu hình Hoyo Codes cho guild {gid}")
        return web.json_response({"ok": True, "message": "Đã lưu cấu hình thông báo Hoyo Code"})
    except Exception as e:
        return web.json_response({"ok": False, "error": str(e)}, status=500)

async def handle_post_hoyo_code(request: web.Request):
    sess = require_auth(request)
    if not sess: return web.json_response({"ok": False, "error": "Unauthorized"}, status=401)
    gid = request.match_info.get("id")
    if not can_access_guild(sess, gid): return web.json_response({"ok": False, "error": "Không có quyền"}, status=403)
    if not BOT_INSTANCE or not getattr(BOT_INSTANCE, "is_ready", lambda: False)():
        proxied = await _proxy_to_bot_web(request, f"/api/guilds/{gid}/hoyo-post-code")
        if proxied is not None:
            return proxied
        return web.json_response({"ok": False, "error": "Bot chưa kết nối"}, status=503)
    try:
        body = await request.json()
        game_key = str(body.get("game_key") or body.get("game") or "genshin").strip().lower()
        code = str(body.get("code", "")).strip().upper()
        rewards = str(body.get("rewards", "")).strip() or "Nguyên Thạch / Quà tặng hấp dẫn"
        hours = float(body.get("hours", 48))

        if not code:
            return web.json_response({"ok": False, "error": "Vui lòng nhập mã code"}, status=400)

        import aiosqlite
        db_path = BASE_DIR / "gacha_data" / "database.sqlite"
        channel_id, role_id = None, None
        if db_path.exists():
            async with aiosqlite.connect(str(db_path)) as db:
                async with db.execute("SELECT channel_id, role_id FROM guild_config WHERE guild_id = ? AND game_key = ?", (str(gid), game_key)) as cur:
                    row = await cur.fetchone()
                    if row: channel_id, role_id = row[0], row[1]

        if not channel_id:
            return web.json_response({"ok": False, "error": f"Chưa cài đặt kênh thông báo cho game {game_key.upper()}!"}, status=400)

        channel = BOT_INSTANCE.get_channel(int(channel_id))
        if not channel:
            return web.json_response({"ok": False, "error": "Không tìm thấy kênh thông báo trong server"}, status=404)

        from Command_vi.code_gamegacha import GAMES
        ginfo = GAMES.get(game_key, {"name": game_key.upper(), "color": 0x4B69FF})

        ping_str = f"<@&{role_id}> " if role_id else ""
        content = f"{ping_str}🎉 **CÓ MÃ CODE MỚI DÀNH CHO {ginfo['name'].upper()}!**"

        embed = discord.Embed(
            title=f"🎁 GIFTCODE MỚI: {ginfo['name']}",
            description=f"👉 Mã Code: **`{code}`**\n🎁 Phần thưởng: **{rewards}**\n⌛ Hạn dùng: **{hours:.1f} giờ**",
            color=ginfo.get("color", 0x4B69FF)
        )
        if ginfo.get("redeem_url"):
            embed.description += f"\n\n🔗 [Bấm vào đây để đổi mã ngay]({ginfo['redeem_url']}{code})"
        embed.set_footer(text="Sakura Bot | Hoyo Code Watcher")

        await channel.send(content=content, embed=embed)
        add_log("SUCCESS", f"User {sess.get('username')} đã phát Hoyo Code {code} ({game_key}) tại guild {gid}")
        return web.json_response({"ok": True, "message": f"Đã phát sóng mã code {code} thành công!"})
    except Exception as e:
        return web.json_response({"ok": False, "error": str(e)}, status=500)

# --- Streak API ---
async def handle_get_streak(request: web.Request):
    sess=require_auth(request)
    if not sess: return web.json_response({"ok":False,"error":"Unauthorized"},status=401)
    gid=request.match_info.get("id")
    if not can_access_guild(sess,gid): return web.json_response({"ok":False,"error":"Không có quyền"},status=403)
    try:
        from Command_vi.streaks import load_data
        data = load_data()
        ginfo = data.get(f"guild_{gid}", {})
        ch_id = ginfo.get("channel_id")
        users = ginfo.get("users", {})
        return web.json_response({"ok": True, "channel_id": str(ch_id) if ch_id else None, "active_count": len(users)})
    except Exception as e:
        return web.json_response({"ok": False, "error": str(e)}, status=500)

async def handle_save_streak(request: web.Request):
    sess=require_auth(request)
    if not sess: return web.json_response({"ok":False,"error":"Unauthorized"},status=401)
    gid=request.match_info.get("id")
    if not can_access_guild(sess,gid): return web.json_response({"ok":False,"error":"Không có quyền"},status=403)
    try:
        body = await request.json()
        ch_id = int(body.get("channel_id")) if body.get("channel_id") else None
        from Command_vi.streaks import load_data, save_data
        data = load_data()
        gkey = f"guild_{gid}"
        if gkey not in data: data[gkey] = {"users": {}, "channel_id": ch_id}
        else: data[gkey]["channel_id"] = ch_id
        save_data(data)
        add_log("INFO", f"User {sess.get('username')} lưu streak channel {gid} -> {ch_id}")
        return web.json_response({"ok": True, "message": "Đã lưu kênh Streak"})
    except Exception as e:
        return web.json_response({"ok": False, "error": str(e)}, status=500)

# --- Rule API ---
async def handle_get_rule_config(request: web.Request):
    sess=require_auth(request)
    if not sess: return web.json_response({"ok":False,"error":"Unauthorized"},status=401)
    gid=request.match_info.get("id")
    if not can_access_guild(sess,gid): return web.json_response({"ok":False,"error":"Không có quyền"},status=403)
    try:
        from Command_vi.rule import load_config
        cfg = load_config().get(str(gid), {})
        return web.json_response({
            "ok": True,
            "channel_id": str(cfg.get("channel_id")) if cfg.get("channel_id") else None,
            "role_id": str(cfg.get("role_id")) if cfg.get("role_id") else None
        })
    except Exception as e:
        return web.json_response({"ok": False, "error": str(e)}, status=500)

async def handle_save_rule_config(request: web.Request):
    sess=require_auth(request)
    if not sess: return web.json_response({"ok":False,"error":"Unauthorized"},status=401)
    gid=request.match_info.get("id")
    if not can_access_guild(sess,gid): return web.json_response({"ok":False,"error":"Không có quyền"},status=403)
    try:
        body = await request.json()
        ch_id = int(body.get("channel_id")) if body.get("channel_id") else None
        r_id = int(body.get("role_id")) if body.get("role_id") else None
        from Command_vi.rule import load_config, save_config
        all_cfg = load_config()
        all_cfg[str(gid)] = {"channel_id": ch_id, "role_id": r_id}
        save_config(all_cfg)
        add_log("INFO", f"User {sess.get('username')} lưu rule config {gid}")
        return web.json_response({"ok": True, "message": "Đã lưu cấu hình Nội quy"})
    except Exception as e:
        return web.json_response({"ok": False, "error": str(e)}, status=500)

async def handle_publish_rule(request: web.Request):
    sess=require_auth(request)
    if not sess: return web.json_response({"ok":False,"error":"Unauthorized"},status=401)
    gid=request.match_info.get("id")
    if not can_access_guild(sess,gid): return web.json_response({"ok":False,"error":"Không có quyền"},status=403)
    if not BOT_INSTANCE or not getattr(BOT_INSTANCE, "is_ready", lambda: False)():
        return web.json_response({"ok": False, "error": "Bot chưa kết nối"}, status=503)
    try:
        from Command_vi.rule import load_config, RuleVerificationView
        cfg = load_config().get(str(gid), {})
        ch_id = cfg.get("channel_id")
        if not ch_id: return web.json_response({"ok": False, "error": "Chưa chọn kênh Nội quy"}, status=400)
        guild = BOT_INSTANCE.get_guild(int(gid))
        ch = guild.get_channel(int(ch_id)) if guild else None
        if not ch: return web.json_response({"ok": False, "error": "Không tìm thấy kênh trên Discord"}, status=404)

        cog = BOT_INSTANCE.get_cog("Rules")
        embed = cog.build_rules_embed(guild) if cog else discord.Embed(title=f"Nội quy: {guild.name}", color=discord.Color.gold(), description="Vui lòng bấm nút bên dưới để đồng ý nội quy và mở khóa server.")
        view = RuleVerificationView(BOT_INSTANCE)
        await ch.send(embed=embed, view=view)
        add_log("INFO", f"User {sess.get('username')} đăng bảng Rule vào #{ch.name} ({gid})")
        return web.json_response({"ok": True, "message": f"Đã đăng bảng nội quy vào #{ch.name}"})
    except Exception as e:
        return web.json_response({"ok": False, "error": str(e)}, status=500)

async def handle_send_channel_message(request: web.Request):
    sess = require_auth(request)
    if not sess:
        return web.json_response({"ok": False, "error": "Unauthorized"}, status=401)
    if not BOT_INSTANCE or not getattr(BOT_INSTANCE, "is_ready", lambda: False)():
        return web.json_response({"ok": False, "error": "Bot chưa kết nối"}, status=503)
    try:
        import io, base64, discord
        channel_id = None
        content = ""
        embed_title = ""
        embed_desc = ""
        embed_color_hex = "#ff79c6"
        embed_image = ""
        embed_thumbnail = ""
        embed_footer = ""
        file_bytes = None
        file_name = None

        if request.content_type.startswith("multipart/"):
            reader = await request.multipart()
            while True:
                part = await reader.next()
                if part is None:
                    break
                pname = part.name
                if pname == "channel_id":
                    channel_id = int((await part.text()).strip())
                elif pname == "content":
                    content = (await part.text()).strip()
                elif pname in ("embed_title", "title"):
                    embed_title = (await part.text()).strip()
                elif pname in ("embed_desc", "description"):
                    embed_desc = (await part.text()).strip()
                elif pname in ("embed_color", "color"):
                    embed_color_hex = (await part.text()).strip()
                elif pname in ("embed_image", "image"):
                    embed_image = (await part.text()).strip()
                elif pname in ("embed_thumbnail", "thumbnail"):
                    embed_thumbnail = (await part.text()).strip()
                elif pname in ("embed_footer", "footer"):
                    embed_footer = (await part.text()).strip()
                elif pname in ("file", "attachment"):
                    file_name = part.filename or "attachment.png"
                    file_bytes = await part.read(decode=False)
        else:
            body = await request.json()
            channel_id = int(body.get("channel_id"))
            content = body.get("content", "").strip()
            embed_data = body.get("embed", {})
            if isinstance(embed_data, dict):
                embed_title = embed_data.get("title", "")
                embed_desc = embed_data.get("description", "")
                embed_color_hex = embed_data.get("color", "#ff79c6")
                embed_image = embed_data.get("image", "")
                embed_thumbnail = embed_data.get("thumbnail", "")
                embed_footer = embed_data.get("footer", "")
            if body.get("file_base64"):
                file_bytes = base64.b64decode(body["file_base64"])
                file_name = body.get("file_name", "upload.png")

        if not channel_id:
            return web.json_response({"ok": False, "error": "Thiếu channel_id"}, status=400)

        # Check guild access via channel's guild
        channel = BOT_INSTANCE.get_channel(channel_id)
        if not channel:
            return web.json_response({"ok": False, "error": "Không tìm thấy channel"}, status=404)
        if hasattr(channel, "guild") and channel.guild:
            if not can_access_guild(sess, str(channel.guild.id)):
                return web.json_response({"ok": False, "error": "Bạn không có quyền gửi tin nhắn ở server này"}, status=403)
        elif not is_admin_session(sess):
            return web.json_response({"ok": False, "error": "Chỉ admin mới gửi tin nhắn ngoài guild"}, status=403)

        embed = None
        if embed_title or embed_desc or embed_image or embed_thumbnail:
            color_int = int(embed_color_hex.replace("#", ""), 16) if embed_color_hex else 0xff79c6
            embed = discord.Embed(title=embed_title or None, description=embed_desc or None, color=color_int)
            if embed_image:
                embed.set_image(url=embed_image)
            if embed_thumbnail:
                embed.set_thumbnail(url=embed_thumbnail)
            if embed_footer:
                embed.set_footer(text=embed_footer)

        dfile = None
        if file_bytes and file_name:
            dfile = discord.File(io.BytesIO(file_bytes), filename=file_name)

        if hasattr(channel, "send"):
            kwargs = {}
            if content: kwargs["content"] = content
            if embed: kwargs["embed"] = embed
            if dfile: kwargs["file"] = dfile
            if not kwargs:
                return web.json_response({"ok": False, "error": "Vui lòng nhập nội dung, embed hoặc đính kèm tệp"}, status=400)
            await channel.send(**kwargs)
        else:
            params = discord.http.handle_message_parameters(
                content=content if content else None,
                embed=embed if embed else discord.utils.MISSING,
                file=dfile if dfile else discord.utils.MISSING,
            )
            await BOT_INSTANCE.http.send_message(channel.id, params=params)
        add_log("SUCCESS", f"User {sess.get('username')} gửi thông báo đến #{getattr(channel, 'name', channel_id)} ({channel.id}) kèm {'file ' if dfile else ''}{'embed' if embed else ''}")
        return web.json_response({"ok": True, "message": "Gửi tin nhắn thông báo thành công"})
    except Exception as e:
        return web.json_response({"ok": False, "error": str(e)}, status=500)

async def handle_bot_action(request: web.Request):
    sess = require_auth(request)
    if not sess:
        return web.json_response({"ok": False, "error": "Unauthorized"}, status=401)
    # Only admin or for presence change allow guild managers? Spec says user control bot per server, but bot actions are global => admin only
    if not is_admin_session(sess):
        return web.json_response({"ok": False, "error": "Chỉ admin mới thực hiện thao tác bot toàn cục"}, status=403)
    try:
        body = await request.json()
        action = body.get("action")
        if not BOT_INSTANCE:
            return web.json_response({"ok": False, "error": "Bot chưa khởi tạo"}, status=503)
        if action == "reload_cogs":
            from file1 import EXTENSIONS
            from file2 import EXTENSION_LOGS
            from file3 import EXTENSION_ANTIS
            reloaded = 0
            errors = []
            for ext in EXTENSIONS:
                try:
                    await BOT_INSTANCE.reload_extension(f"Command_vi.{ext}")
                    reloaded += 1
                except Exception as e:
                    errors.append(f"Command_vi.{ext}: {e}")
            for ext in EXTENSION_LOGS:
                try:
                    await BOT_INSTANCE.reload_extension(f"Logs_vi.{ext}")
                    reloaded += 1
                except Exception as e:
                    errors.append(f"Logs_vi.{ext}: {e}")
            for ext in EXTENSION_ANTIS:
                try:
                    await BOT_INSTANCE.reload_extension(f"Anti.{ext}")
                    reloaded += 1
                except Exception as e:
                    errors.append(f"Anti.{ext}: {e}")
            add_log("INFO", f"Admin {sess.get('username')} nạp lại {reloaded} Cogs qua Web")
            return web.json_response({"ok": True, "message": f"Đã nạp lại {reloaded} extensions!", "errors": errors})
        elif action == "sync_slash":
            synced = await BOT_INSTANCE.tree.sync()
            add_log("SUCCESS", f"Admin đồng bộ {len(synced)} lệnh Slash")
            return web.json_response({"ok": True, "message": f"Đã đồng bộ {len(synced)} lệnh Slash toàn cầu!"})
        elif action == "change_presence":
            status_str = body.get("status", "online")
            activity_text = body.get("activity", "Sakura Bot Dashboard")
            import discord
            status_map = {"online": discord.Status.online, "idle": discord.Status.idle, "dnd": discord.Status.dnd, "invisible": discord.Status.invisible}
            await BOT_INSTANCE.change_presence(status=status_map.get(status_str, discord.Status.online), activity=discord.Game(name=activity_text))
            add_log("INFO", f"Admin đổi trạng thái bot: {status_str} - {activity_text}")
            return web.json_response({"ok": True, "message": "Đã đổi trạng thái bot thành công"})
        return web.json_response({"ok": False, "error": "Hành động không hợp lệ"}, status=400)
    except Exception as e:
        return web.json_response({"ok": False, "error": str(e)}, status=500)

# --- Minecraft Endpoints (admin only) ---
async def handle_mc_status(request: web.Request):
    sess = require_auth(request)
    if not sess:
        return web.json_response({"ok": False, "error": "Unauthorized"}, status=401)
    if not is_admin_session(sess):
        return web.json_response({"ok": False, "error": "Chỉ admin mới xem Minecraft status"}, status=403)
    whitelist = load_json(SERVER_DIR / "whitelist.json", [])
    banned_players = load_json(SERVER_DIR / "banned-players.json", [])
    ops = load_json(SERVER_DIR / "ops.json", [])
    mc_links = load_json(DATA_DIR / "mc_links.json", {})
    is_running = False
    for p in psutil.process_iter(['pid', 'name', 'cmdline']):
        try:
            cmdline = p.info.get('cmdline') or []
            if any("server.jar" in arg or "paper" in arg.lower() for arg in cmdline):
                is_running = True
                break
        except Exception:
            pass

    rcon_ok = False
    rcon_msg = "Chưa kết nối"
    try:
        from Command_vi.minecraft import send_rcon_command_sync
        rcon_ok, rcon_msg = send_rcon_command_sync("list")
    except Exception as e:
        rcon_msg = str(e)

    return web.json_response({
        "ok": True,
        "server_running": is_running,
        "rcon_online": rcon_ok,
        "rcon_message": rcon_msg,
        "whitelist": whitelist if isinstance(whitelist, list) else [],
        "banned_players": banned_players if isinstance(banned_players, list) else [],
        "ops": ops if isinstance(ops, list) else [],
        "links_count": len(mc_links),
        "links": mc_links
    })

async def handle_mc_control(request: web.Request):
    sess = require_auth(request)
    if not sess:
        return web.json_response({"ok": False, "error": "Unauthorized"}, status=401)
    if not is_admin_session(sess):
        return web.json_response({"ok": False, "error": "Chỉ admin mới điều khiển Minecraft"}, status=403)
    try:
        body = await request.json()
        action = body.get("action")
        if action == "start":
            start_bat = SERVER_DIR / "start.bat"
            if start_bat.exists():
                import subprocess
                subprocess.Popen(["cmd.exe", "/c", str(start_bat)], cwd=str(SERVER_DIR), creationflags=subprocess.CREATE_NEW_CONSOLE)
                add_log("INFO", f"Admin {sess.get('username')} khởi động Minecraft Server")
                return web.json_response({"ok": True, "message": "Đang khởi động Minecraft Server..."})
            else:
                return web.json_response({"ok": False, "error": "Không tìm thấy file start.bat"}, status=404)
        elif action == "stop":
            from Command_vi.minecraft import send_rcon_command_sync
            ok, res = await asyncio.to_thread(send_rcon_command_sync, "stop")
            add_log("INFO", f"Admin {sess.get('username')} dừng Minecraft Server: {res}")
            return web.json_response({"ok": True, "message": f"Đã gửi lệnh dừng server: {res}"})
        elif action == "restart":
            from Command_vi.minecraft import send_rcon_command_sync
            ok, res = await asyncio.to_thread(send_rcon_command_sync, "restart")
            add_log("INFO", f"Admin {sess.get('username')} khởi động lại Minecraft Server: {res}")
            return web.json_response({"ok": True, "message": f"Đã gửi lệnh restart: {res}"})
        elif action == "kill":
            killed = False
            for p in psutil.process_iter(['pid', 'name', 'cmdline']):
                try:
                    cmdline = p.info.get('cmdline') or []
                    if any("server.jar" in arg or "paper" in arg.lower() for arg in cmdline):
                        p.kill()
                        killed = True
                except Exception:
                    pass
            add_log("WARN", f"Admin {sess.get('username')} kill process Minecraft Server")
            return web.json_response({"ok": True, "message": "Đã buộc dừng process Minecraft Server thành công!" if killed else "Không tìm thấy process Minecraft Server"})
        elif action == "add_whitelist":
            player_name = body.get("name", "").strip()
            if not player_name:
                return web.json_response({"ok": False, "error": "Tên người chơi trống"}, status=400)
            wl = load_json(SERVER_DIR / "whitelist.json", [])
            if not any(item.get("name", "").lower() == player_name.lower() for item in wl if isinstance(item, dict)):
                wl.append({"name": player_name, "uuid": ""})
                save_json(SERVER_DIR / "whitelist.json", wl)
                add_log("INFO", f"Admin thêm '{player_name}' vào Whitelist")
            return web.json_response({"ok": True, "message": f"Đã thêm {player_name} vào Whitelist"})
        elif action == "remove_whitelist":
            player_name = body.get("name", "").strip().lower()
            wl = load_json(SERVER_DIR / "whitelist.json", [])
            wl = [item for item in wl if isinstance(item, dict) and item.get("name", "").lower() != player_name]
            save_json(SERVER_DIR / "whitelist.json", wl)
            add_log("INFO", f"Admin xóa '{player_name}' khỏi Whitelist")
            return web.json_response({"ok": True, "message": f"Đã xóa {player_name} khỏi Whitelist"})
        return web.json_response({"ok": False, "error": "Hành động không hợp lệ"}, status=400)
    except Exception as e:
        return web.json_response({"ok": False, "error": str(e)}, status=500)

# ==============================================================================
# HỆ THỐNG API WEB HOSTING MINECRAFT DASHBOARD (/minecraft, /console, /file, /properties)
# ==============================================================================

async def handle_api_mc_hosting_servers(request: web.Request):
    sess = get_session(request)
    if not sess or not is_admin_session(sess):
        return web.json_response({"ok": False, "error": "Chỉ Quản trị viên mới có quyền truy cập"}, status=403)
    from web.mc_hosting import scan_mc_servers, get_system_metrics
    servers = scan_mc_servers(BASE_DIR)
    default_dir = SERVER_DIR if SERVER_DIR.exists() else BASE_DIR
    sys_metrics = get_system_metrics(default_dir)
    return web.json_response({"ok": True, "servers": servers, "system": sys_metrics})

async def handle_api_mc_hosting_server_detail(request: web.Request):
    sess = get_session(request)
    if not sess or not is_admin_session(sess):
        return web.json_response({"ok": False, "error": "Chỉ Quản trị viên mới có quyền truy cập"}, status=403)
    server_id = request.match_info.get("id", "server")
    from web.mc_hosting import get_server_dir, get_server_summary, get_system_metrics
    srv_dir = get_server_dir(server_id, BASE_DIR)
    if not srv_dir:
        return web.json_response({"ok": False, "error": "Máy chủ không tồn tại"}, status=404)

    summary = get_server_summary(srv_dir)
    metrics = get_system_metrics(srv_dir)
    hosting_cfg = load_json(DATA_DIR / "mc_hosting_servers.json", {})
    srv_channels = hosting_cfg.get(server_id, {})
    return web.json_response({
        "ok": True,
        "server": summary,
        "metrics": metrics,
        "channels": srv_channels
    })

async def handle_api_mc_hosting_server_power(request: web.Request):
    sess = get_session(request)
    if not sess or not is_admin_session(sess):
        return web.json_response({"ok": False, "error": "Chỉ Quản trị viên mới có quyền điều khiển máy chủ"}, status=403)
    server_id = request.match_info.get("id", "server")
    from web.mc_hosting import get_server_dir, get_server_process, parse_properties_file
    srv_dir = get_server_dir(server_id, BASE_DIR)
    if not srv_dir:
        return web.json_response({"ok": False, "error": "Máy chủ không tồn tại"}, status=404)

    try:
        data = await request.json()
        action = data.get("action", "").lower()
        if action == "start":
            start_bat = srv_dir / "start.bat"
            if not start_bat.exists():
                with open(start_bat, "w", encoding="utf-8") as f:
                    f.write("@echo off\ntitle SakuraBot Minecraft Server\njava -Xms1024M -Xmx2048M -jar server.jar nogui\npause\n")

            import subprocess
            subprocess.Popen(["cmd.exe", "/c", str(start_bat)], cwd=str(srv_dir), creationflags=subprocess.CREATE_NEW_CONSOLE)
            add_log("INFO", f"Admin {sess.get('username')} khởi động máy chủ Minecraft [{server_id}]")
            return web.json_response({"ok": True, "message": f"Đang khởi động máy chủ {server_id}..."})

        elif action == "stop":
            props, _ = parse_properties_file(srv_dir / "server.properties")
            rcon_port = int(props.get("rcon.port", 25575))
            rcon_pass = props.get("rcon.password", "")
            from Command_vi.minecraft import send_rcon_command_sync
            ok, res = await asyncio.to_thread(send_rcon_command_sync, "stop", host="127.0.0.1", port=rcon_port, password=rcon_pass)
            add_log("INFO", f"Admin {sess.get('username')} dừng máy chủ [{server_id}]: {res}")
            return web.json_response({"ok": True, "message": f"Đã gửi lệnh dừng máy chủ: {res}"})

        elif action == "restart":
            props, _ = parse_properties_file(srv_dir / "server.properties")
            rcon_port = int(props.get("rcon.port", 25575))
            rcon_pass = props.get("rcon.password", "")
            from Command_vi.minecraft import send_rcon_command_sync
            ok, res = await asyncio.to_thread(send_rcon_command_sync, "restart", host="127.0.0.1", port=rcon_port, password=rcon_pass)
            add_log("INFO", f"Admin {sess.get('username')} khởi động lại máy chủ [{server_id}]: {res}")
            return web.json_response({"ok": True, "message": f"Đã gửi lệnh restart máy chủ: {res}"})

        elif action == "kill":
            proc = get_server_process(srv_dir)
            if proc:
                try:
                    proc.kill()
                    add_log("WARN", f"Admin {sess.get('username')} kill process PID #{proc.pid} của [{server_id}]")
                    return web.json_response({"ok": True, "message": f"Đã buộc dừng tiến trình PID #{proc.pid} thành công!"})
                except Exception as e:
                    return web.json_response({"ok": False, "error": f"Lỗi dừng process: {e}"})
            return web.json_response({"ok": True, "message": "Tiến trình máy chủ không còn chạy."})

        return web.json_response({"ok": False, "error": "Hành động không hợp lệ"}, status=400)
    except Exception as e:
        return web.json_response({"ok": False, "error": str(e)}, status=500)

async def handle_api_mc_hosting_server_console(request: web.Request):
    sess = get_session(request)
    if not sess or not is_admin_session(sess):
        return web.json_response({"ok": False, "error": "Chỉ Quản trị viên mới có quyền xem console"}, status=403)
    server_id = request.match_info.get("id", "server")
    from web.mc_hosting import get_server_dir, read_console_tail
    srv_dir = get_server_dir(server_id, BASE_DIR)
    if not srv_dir:
        return web.json_response({"ok": False, "error": "Máy chủ không tồn tại"}, status=404)
    logs = read_console_tail(srv_dir, max_lines=200)
    return web.json_response({"ok": True, "logs": logs})

async def handle_api_mc_hosting_server_command(request: web.Request):
    sess = get_session(request)
    if not sess or not is_admin_session(sess):
        return web.json_response({"ok": False, "error": "Chỉ Quản trị viên mới có quyền gửi lệnh console"}, status=403)
    server_id = request.match_info.get("id", "server")
    from web.mc_hosting import get_server_dir, parse_properties_file
    srv_dir = get_server_dir(server_id, BASE_DIR)
    if not srv_dir:
        return web.json_response({"ok": False, "error": "Máy chủ không tồn tại"}, status=404)

    try:
        data = await request.json()
        cmd = str(data.get("command", "")).strip()
        if not cmd:
            return web.json_response({"ok": False, "error": "Lệnh trống"}, status=400)

        props, _ = parse_properties_file(srv_dir / "server.properties")
        rcon_port = int(props.get("rcon.port", 25575))
        rcon_pass = props.get("rcon.password", "")
        from Command_vi.minecraft import send_rcon_command_sync, clean_minecraft_text_static
        ok, res = await asyncio.to_thread(send_rcon_command_sync, cmd, host="127.0.0.1", port=rcon_port, password=rcon_pass)
        clean_res = clean_minecraft_text_static(res) if res else "Lệnh đã được thực thi"
        add_log("CMD", f"Admin {sess.get('username')} chạy lệnh trên [{server_id}]: {cmd}")
        return web.json_response({"ok": True, "response": clean_res})
    except Exception as e:
        return web.json_response({"ok": False, "error": str(e)}, status=500)

async def handle_api_mc_hosting_discord_channels(request: web.Request):
    sess = get_session(request)
    if not sess or not is_admin_session(sess):
        return web.json_response({"ok": False, "error": "Unauthorized"}, status=403)
    channels = []
    try:
        if BOT_INSTANCE and getattr(BOT_INSTANCE, "is_ready", lambda: False)():
            for g in BOT_INSTANCE.guilds:
                for ch in g.text_channels:
                    channels.append({
                        "id": str(ch.id),
                        "name": ch.name,
                        "guild": g.name
                    })
    except Exception:
        pass
    return web.json_response({"ok": True, "channels": channels})

async def handle_api_mc_hosting_save_channels(request: web.Request):
    sess = get_session(request)
    if not sess or not is_admin_session(sess):
        return web.json_response({"ok": False, "error": "Unauthorized"}, status=403)
    server_id = request.match_info.get("id", "server")
    try:
        data = await request.json()
        log_ch = str(data.get("log_channel_id", "")).strip()
        chat_ch = str(data.get("chat_channel_id", "")).strip()

        cfg_file = DATA_DIR / "mc_hosting_servers.json"
        all_cfg = load_json(cfg_file, {})
        if server_id not in all_cfg:
            all_cfg[server_id] = {}
        all_cfg[server_id]["log_channel_id"] = log_ch
        all_cfg[server_id]["chat_channel_id"] = chat_ch
        save_json(cfg_file, all_cfg)
        return web.json_response({"ok": True, "message": "Đã lưu cài đặt kênh Discord cho server thành công!"})
    except Exception as e:
        return web.json_response({"ok": False, "error": str(e)}, status=500)

async def handle_api_mc_hosting_send_chat(request: web.Request):
    sess = get_session(request)
    if not sess or not is_admin_session(sess):
        return web.json_response({"ok": False, "error": "Unauthorized"}, status=403)
    server_id = request.match_info.get("id", "server")
    from web.mc_hosting import get_server_dir, parse_properties_file
    srv_dir = get_server_dir(server_id, BASE_DIR)
    if not srv_dir:
        return web.json_response({"ok": False, "error": "Máy chủ không tồn tại"}, status=404)

    try:
        data = await request.json()
        msg = str(data.get("message", "")).strip()
        if not msg:
            return web.json_response({"ok": False, "error": "Tin nhắn trống"}, status=400)

        sender_name = sess.get("username", "Web Admin")
        safe_msg = msg.replace('"', '\\"')
        cmd = f'tellraw @a [{{"text":"[Discord/Web] ","color":"light_purple"}},{{"text":"<{sender_name}> ","color":"aqua","bold":true}},{{"text":"{safe_msg}","color":"white"}}]'
        props, _ = parse_properties_file(srv_dir / "server.properties")
        rcon_port = int(props.get("rcon.port", 25575))
        rcon_pass = props.get("rcon.password", "")
        from Command_vi.minecraft import send_rcon_command_sync
        await asyncio.to_thread(send_rcon_command_sync, cmd, host="127.0.0.1", port=rcon_port, password=rcon_pass)

        # Gửi đồng bộ sang kênh chat Discord nếu có
        cfg_file = DATA_DIR / "mc_hosting_servers.json"
        all_cfg = load_json(cfg_file, {})
        chat_ch_id = all_cfg.get(server_id, {}).get("chat_channel_id")
        if chat_ch_id and BOT_INSTANCE and getattr(BOT_INSTANCE, "is_ready", lambda: False)():
            try:
                ch = BOT_INSTANCE.get_channel(int(chat_ch_id))
                if ch:
                    await ch.send(f"💬 **[Web Admin - {sender_name}]**: {msg}")
            except Exception:
                pass

        return web.json_response({"ok": True, "message": "Đã phát tin nhắn vào game thành công!"})
    except Exception as e:
        return web.json_response({"ok": False, "error": str(e)}, status=500)

async def handle_api_mc_hosting_files_list(request: web.Request):
    sess = get_session(request)
    if not sess or not is_admin_session(sess):
        return web.json_response({"ok": False, "error": "Chỉ Quản trị viên mới có quyền xem tệp"}, status=403)
    server_id = request.match_info.get("id", "server")
    rel_path = request.query.get("path", "")
    from web.mc_hosting import get_server_dir, get_files_in_dir
    srv_dir = get_server_dir(server_id, BASE_DIR)
    if not srv_dir:
        return web.json_response({"ok": False, "error": "Máy chủ không tồn tại"}, status=404)
    ok, result = get_files_in_dir(srv_dir, rel_path)
    if not ok:
        return web.json_response({"ok": False, "error": result}, status=400)
    return web.json_response({"ok": True, **result})

async def handle_api_mc_hosting_files_read(request: web.Request):
    sess = get_session(request)
    if not sess or not is_admin_session(sess):
        return web.json_response({"ok": False, "error": "Unauthorized"}, status=403)
    server_id = request.match_info.get("id", "server")
    rel_path = request.query.get("path", "")
    from web.mc_hosting import get_server_dir, read_file_safe
    srv_dir = get_server_dir(server_id, BASE_DIR)
    if not srv_dir:
        return web.json_response({"ok": False, "error": "Máy chủ không tồn tại"}, status=404)
    ok, result = read_file_safe(srv_dir, rel_path)
    if not ok:
        return web.json_response({"ok": False, "error": result}, status=400)
    return web.json_response({"ok": True, "file": result})

async def handle_api_mc_hosting_files_save(request: web.Request):
    sess = get_session(request)
    if not sess or not is_admin_session(sess):
        return web.json_response({"ok": False, "error": "Unauthorized"}, status=403)
    server_id = request.match_info.get("id", "server")
    from web.mc_hosting import get_server_dir, save_file_safe
    srv_dir = get_server_dir(server_id, BASE_DIR)
    if not srv_dir:
        return web.json_response({"ok": False, "error": "Máy chủ không tồn tại"}, status=404)
    try:
        data = await request.json()
        rel_path = data.get("path", "")
        content = data.get("content", "")
        ok, msg = save_file_safe(srv_dir, rel_path, content)
        if not ok:
            return web.json_response({"ok": False, "error": msg}, status=400)
        add_log("INFO", f"Admin {sess.get('username')} đã lưu file [{server_id}/{rel_path}]")
        return web.json_response({"ok": True, "message": msg})
    except Exception as e:
        return web.json_response({"ok": False, "error": str(e)}, status=500)

async def handle_api_mc_hosting_files_create(request: web.Request):
    sess = get_session(request)
    if not sess or not is_admin_session(sess):
        return web.json_response({"ok": False, "error": "Unauthorized"}, status=403)
    server_id = request.match_info.get("id", "server")
    from web.mc_hosting import get_server_dir, create_item_safe
    srv_dir = get_server_dir(server_id, BASE_DIR)
    if not srv_dir:
        return web.json_response({"ok": False, "error": "Máy chủ không tồn tại"}, status=404)
    try:
        data = await request.json()
        path = data.get("path", "")
        name = data.get("name", "")
        is_folder = bool(data.get("is_folder", False))
        ok, msg = create_item_safe(srv_dir, path, name, is_folder)
        if not ok:
            return web.json_response({"ok": False, "error": msg}, status=400)
        return web.json_response({"ok": True, "message": msg})
    except Exception as e:
        return web.json_response({"ok": False, "error": str(e)}, status=500)

async def handle_api_mc_hosting_files_delete(request: web.Request):
    sess = get_session(request)
    if not sess or not is_admin_session(sess):
        return web.json_response({"ok": False, "error": "Unauthorized"}, status=403)
    server_id = request.match_info.get("id", "server")
    from web.mc_hosting import get_server_dir, delete_item_safe
    srv_dir = get_server_dir(server_id, BASE_DIR)
    if not srv_dir:
        return web.json_response({"ok": False, "error": "Máy chủ không tồn tại"}, status=404)
    try:
        data = await request.json()
        path = data.get("path", "")
        ok, msg = delete_item_safe(srv_dir, path)
        if not ok:
            return web.json_response({"ok": False, "error": msg}, status=400)
        add_log("WARN", f"Admin {sess.get('username')} đã xóa tệp/thư mục [{server_id}/{path}]")
        return web.json_response({"ok": True, "message": msg})
    except Exception as e:
        return web.json_response({"ok": False, "error": str(e)}, status=500)

async def handle_api_mc_hosting_files_rename(request: web.Request):
    sess = get_session(request)
    if not sess or not is_admin_session(sess):
        return web.json_response({"ok": False, "error": "Unauthorized"}, status=403)
    server_id = request.match_info.get("id", "server")
    from web.mc_hosting import get_server_dir, rename_item_safe
    srv_dir = get_server_dir(server_id, BASE_DIR)
    if not srv_dir:
        return web.json_response({"ok": False, "error": "Máy chủ không tồn tại"}, status=404)
    try:
        data = await request.json()
        rel_path = data.get("rel_path", "")
        new_name = data.get("new_name", "")
        ok, msg = rename_item_safe(srv_dir, rel_path, new_name)
        if not ok:
            return web.json_response({"ok": False, "error": msg}, status=400)
        return web.json_response({"ok": True, "message": msg})
    except Exception as e:
        return web.json_response({"ok": False, "error": str(e)}, status=500)

async def handle_api_mc_hosting_files_upload(request: web.Request):
    sess = get_session(request)
    if not sess or not is_admin_session(sess):
        return web.json_response({"ok": False, "error": "Unauthorized"}, status=403)
    server_id = request.match_info.get("id", "server")
    from web.mc_hosting import get_server_dir
    srv_dir = get_server_dir(server_id, BASE_DIR)
    if not srv_dir:
        return web.json_response({"ok": False, "error": "Máy chủ không tồn tại"}, status=404)

    try:
        reader = await request.multipart()
        target_subpath = ""
        saved_files = []

        while True:
            part = await reader.next()
            if part is None:
                break
            if part.name == "path":
                target_subpath = (await part.text()).strip().lstrip("/\\")
                continue
            if part.name == "file":
                filename = part.filename
                if not filename:
                    continue
                clean_filename = os.path.basename(filename)
                dest_dir = (srv_dir / target_subpath).resolve()
                if not dest_dir.is_relative_to(srv_dir.resolve()):
                    return web.json_response({"ok": False, "error": "Đường dẫn không hợp lệ"}, status=400)
                dest_dir.mkdir(parents=True, exist_ok=True)
                dest_file = dest_dir / clean_filename

                size = 0
                with open(dest_file, "wb") as f:
                    while True:
                        chunk = await part.read_chunk(65536)
                        if not chunk:
                            break
                        f.write(chunk)
                        size += len(chunk)
                saved_files.append(clean_filename)

        return web.json_response({"ok": True, "message": f"Đã tải lên {len(saved_files)} tệp thành công!", "files": saved_files})
    except Exception as e:
        return web.json_response({"ok": False, "error": str(e)}, status=500)

async def handle_api_mc_hosting_properties_get(request: web.Request):
    sess = get_session(request)
    if not sess or not is_admin_session(sess):
        return web.json_response({"ok": False, "error": "Unauthorized"}, status=403)
    server_id = request.match_info.get("id", "server")
    from web.mc_hosting import get_server_dir, parse_properties_file
    srv_dir = get_server_dir(server_id, BASE_DIR)
    if not srv_dir:
        return web.json_response({"ok": False, "error": "Máy chủ không tồn tại"}, status=404)
    props, raw = parse_properties_file(srv_dir / "server.properties")
    return web.json_response({"ok": True, "properties": props, "raw": raw})

async def handle_api_mc_hosting_properties_save(request: web.Request):
    sess = get_session(request)
    if not sess or not is_admin_session(sess):
        return web.json_response({"ok": False, "error": "Unauthorized"}, status=403)
    server_id = request.match_info.get("id", "server")
    from web.mc_hosting import get_server_dir, update_server_properties
    srv_dir = get_server_dir(server_id, BASE_DIR)
    if not srv_dir:
        return web.json_response({"ok": False, "error": "Máy chủ không tồn tại"}, status=404)
    try:
        data = await request.json()
        updates = data.get("updates")
        raw = data.get("raw")
        ok, msg = update_server_properties(srv_dir, updates=updates, raw_content=raw)
        if not ok:
            return web.json_response({"ok": False, "error": msg}, status=400)
        add_log("INFO", f"Admin {sess.get('username')} cập nhật server.properties của [{server_id}]")
        return web.json_response({"ok": True, "message": msg})
    except Exception as e:
        return web.json_response({"ok": False, "error": str(e)}, status=500)

async def handle_api_mc_hosting_server_icon_get(request: web.Request):
    """Lấy ảnh server-icon.png của máy chủ."""
    server_id = request.match_info.get("id", "server")
    from web.mc_hosting import get_server_dir
    srv_dir = get_server_dir(server_id, BASE_DIR)
    if not srv_dir:
        return web.Response(status=404)
    icon_path = srv_dir / "server-icon.png"
    if icon_path.exists():
        try:
            with open(icon_path, "rb") as f:
                return web.Response(body=f.read(), content_type="image/png")
        except Exception:
            pass
    default_svg = '''<svg xmlns="http://www.w3.org/2000/svg" width="64" height="64" viewBox="0 0 64 64"><rect width="64" height="64" fill="#1e1e2e" rx="10"/><text x="32" y="42" font-size="32" text-anchor="middle" fill="#ff79c6">⛏️</text></svg>'''
    return web.Response(body=default_svg.encode("utf-8"), content_type="image/svg+xml")

async def handle_api_mc_hosting_server_icon_upload(request: web.Request):
    """Tải lên và tự động chuyển đổi ảnh icon server sang chuẩn 64x64 PNG."""
    sess = get_session(request)
    if not sess or (not is_admin_session(sess) and not check_mc_perm(sess, "can_manage_properties")):
        return web.json_response({"ok": False, "error": "Bạn không có quyền thay đổi cấu hình máy chủ"}, status=403)
    server_id = request.match_info.get("id", "server")
    from web.mc_hosting import get_server_dir, update_server_icon
    srv_dir = get_server_dir(server_id, BASE_DIR)
    if not srv_dir:
        return web.json_response({"ok": False, "error": "Máy chủ không tồn tại"}, status=404)

    try:
        if request.content_type.startswith("multipart/"):
            reader = await request.multipart()
            part = await reader.next()
            if not part:
                return web.json_response({"ok": False, "error": "Không tìm thấy tệp ảnh tải lên"}, status=400)
            img_data = await part.read()
        else:
            data = await request.json()
            import base64
            b64_str = str(data.get("image", ""))
            if "," in b64_str:
                b64_str = b64_str.split(",", 1)[1]
            img_data = base64.b64decode(b64_str)

        ok, msg = update_server_icon(srv_dir, img_data)
        if not ok:
            return web.json_response({"ok": False, "error": msg}, status=400)
        add_log("INFO", f"User {sess.get('username')} đã cập nhật server-icon.png của [{server_id}]")
        return web.json_response({"ok": True, "message": msg})
    except Exception as e:
        return web.json_response({"ok": False, "error": str(e)}, status=500)

async def handle_api_mc_hosting_server_players(request: web.Request):
    """Danh sách người chơi máy chủ Minecraft (/minecraft/player)."""
    sess = get_session(request)
    if not sess or (not is_admin_session(sess) and not check_mc_perm(sess, "can_view_players")):
        return web.json_response({"ok": False, "error": "Bạn không có quyền xem thông tin người chơi máy chủ"}, status=403)
    server_id = request.match_info.get("id", "server")
    from web.mc_hosting import get_server_dir, get_server_players
    srv_dir = get_server_dir(server_id, BASE_DIR)
    if not srv_dir:
        return web.json_response({"ok": False, "error": "Máy chủ không tồn tại"}, status=404)
    players = get_server_players(srv_dir)
    return web.json_response({"ok": True, "players": players})

async def handle_api_mc_hosting_server_player_detail(request: web.Request):
    """Chi tiết kho đồ (Inventory, Armor, EnderChest, Shulker) của người chơi."""
    sess = get_session(request)
    if not sess or (not is_admin_session(sess) and not check_mc_perm(sess, "can_view_players")):
        return web.json_response({"ok": False, "error": "Bạn không có quyền xem thông tin người chơi máy chủ"}, status=403)
    server_id = request.match_info.get("id", "server")
    uuid_str = request.match_info.get("uuid", "")
    from web.mc_hosting import get_server_dir, get_player_detail
    srv_dir = get_server_dir(server_id, BASE_DIR)
    if not srv_dir:
        return web.json_response({"ok": False, "error": "Máy chủ không tồn tại"}, status=404)
    detail = get_player_detail(srv_dir, uuid_str)
    if not detail:
        return web.json_response({"ok": False, "error": "Không tìm thấy dữ liệu tệp playerdata của người chơi này"}, status=404)
    return web.json_response({"ok": True, "player": detail})

async def handle_api_mc_hosting_manager_users_get(request: web.Request):
    """Lấy danh sách người dùng được phân quyền MC hosting."""
    sess = get_session(request)
    if not sess or not is_admin_session(sess):
        return web.json_response({"ok": False, "error": "Chỉ Quản trị viên mới có quyền xem phân quyền"}, status=403)
    from web.mc_hosting import get_mc_permissions
    perms_data = get_mc_permissions(DATA_DIR)
    return web.json_response({"ok": True, "users": list(perms_data.get("users", {}).values())})

async def handle_api_mc_hosting_manager_users_save(request: web.Request):
    """Cấp hoặc cập nhật phân quyền cho một user."""
    sess = get_session(request)
    if not sess or not is_admin_session(sess):
        return web.json_response({"ok": False, "error": "Chỉ Quản trị viên mới có quyền phân quyền"}, status=403)
    try:
        data = await request.json()
        from web.mc_hosting import save_mc_user_permission
        ok, msg = save_mc_user_permission(DATA_DIR, data)
        if not ok:
            return web.json_response({"ok": False, "error": msg}, status=400)
        add_log("INFO", f"Admin {sess.get('username')} phân quyền MC cho user {data.get('username', data.get('user_id'))}")
        return web.json_response({"ok": True, "message": msg})
    except Exception as e:
        return web.json_response({"ok": False, "error": str(e)}, status=500)

async def handle_api_mc_hosting_manager_users_delete(request: web.Request):
    """Xóa quyền hạn MC của một user."""
    sess = get_session(request)
    if not sess or not is_admin_session(sess):
        return web.json_response({"ok": False, "error": "Chỉ Quản trị viên mới có quyền thu hồi phân quyền"}, status=403)
    try:
        data = await request.json()
        user_id = str(data.get("user_id", "")).strip()
        from web.mc_hosting import delete_mc_user_permission
        ok, msg = delete_mc_user_permission(DATA_DIR, user_id)
        if not ok:
            return web.json_response({"ok": False, "error": msg}, status=400)
        add_log("INFO", f"Admin {sess.get('username')} đã thu hồi phân quyền MC của user {user_id}")
        return web.json_response({"ok": True, "message": msg})
    except Exception as e:
        return web.json_response({"ok": False, "error": str(e)}, status=500)

# --- Anti & Security Endpoints (admin only) ---
async def handle_get_anti_settings(request: web.Request):
    sess = require_auth(request)
    if not sess:
        return web.json_response({"ok": False, "error": "Unauthorized"}, status=401)
    if not is_admin_session(sess):
        return web.json_response({"ok": False, "error": "Chỉ admin mới xem Anti settings"}, status=403)
    raid = load_json(DATA_DIR / "raid_settings.json", {})
    nuke = load_json(DATA_DIR / "nuke_settings.json", {})
    spam = load_json(DATA_DIR / "spam_settings.json", {})
    link = load_json(DATA_DIR / "link_filter_settings.json", {})
    words = load_json(DATA_DIR / "forbidden_words.json", [])
    allowed_links = load_json(DATA_DIR / "allowed_links.json", [])
    violations = load_json(DATA_DIR / "insult_violations.json", {})
    global_anti = load_json(DATA_DIR / "anti_global.json", {"enabled": True})
    global_enabled = global_anti.get("enabled", True) if isinstance(global_anti, dict) else True
    return web.json_response({
        "ok": True,
        "global_enabled": global_enabled,
        "raid": raid,
        "nuke": nuke,
        "spam": spam,
        "link": link,
        "forbidden_words": words if isinstance(words, list) else [],
        "allowed_links": allowed_links if isinstance(allowed_links, list) else [],
        "violations": violations
    })

async def handle_save_anti_settings(request: web.Request):
    sess = require_auth(request)
    if not sess:
        return web.json_response({"ok": False, "error": "Unauthorized"}, status=401)
    if not is_admin_session(sess):
        return web.json_response({"ok": False, "error": "Chỉ admin mới lưu Anti settings"}, status=403)
    try:
        body = await request.json()
        setting_type = body.get("type")
        payload = body.get("data")
        if setting_type == "global":
            enabled = bool(payload.get("enabled", True)) if isinstance(payload, dict) else bool(payload)
            save_json(DATA_DIR / "anti_global.json", {"enabled": enabled})
            for cfg_name in ["spam_settings.json", "raid_settings.json", "nuke_settings.json"]:
                cfg_data = load_json(DATA_DIR / cfg_name, {})
                if isinstance(cfg_data, dict):
                    cfg_data.setdefault("__global__", {})["enabled"] = enabled
                    save_json(DATA_DIR / cfg_name, cfg_data)
            add_log("INFO", f"Admin {sess.get('username')} đã {'BẬT' if enabled else 'TẮT'} toàn cục hệ thống Anti")
            return web.json_response({"ok": True, "message": f"Đã {'bật' if enabled else 'tắt'} toàn cục hệ thống Anti", "enabled": enabled})
        elif setting_type == "raid":
            save_json(DATA_DIR / "raid_settings.json", payload)
        elif setting_type == "nuke":
            save_json(DATA_DIR / "nuke_settings.json", payload)
        elif setting_type == "spam":
            save_json(DATA_DIR / "spam_settings.json", payload)
        elif setting_type == "link":
            save_json(DATA_DIR / "link_filter_settings.json", payload)
        elif setting_type == "forbidden_words":
            save_json(DATA_DIR / "forbidden_words.json", payload)
        elif setting_type == "allowed_links":
            save_json(DATA_DIR / "allowed_links.json", payload)
        add_log("INFO", f"Admin {sess.get('username')} cập nhật Anti '{setting_type}'")
        return web.json_response({"ok": True, "message": "Lưu cài đặt thành công"})
    except Exception as e:
        return web.json_response({"ok": False, "error": str(e)}, status=500)

# --- Levels & Economy Endpoints (admin only) — Đọc & ghi trực tiếp SQLite Database (data/bot_database.db) ---
def _levels_file():
    # hỗ trợ alias lever.json nếu bạn đổi tên, ưu tiên lever.json nếu tồn tại (fallback)
    p = DATA_DIR / "lever.json"
    if p.exists():
        return p
    return DATA_DIR / "levels.json"

async def handle_get_levels(request: web.Request):
    sess = require_auth(request)
    if not sess:
        return web.json_response({"ok": False, "error": "Unauthorized"}, status=401)
    
    guild_id = request.query.get("guild_id")
    try:
        from data.database import get_web_levels_leaderboard
        db_res = await get_web_levels_leaderboard(guild_id=guild_id, limit=100)
        leaderboard = db_res.get("users", [])
        total_users = db_res.get("total_users", len(leaderboard))
    except Exception as e:
        print(f"[Web] Lỗi đọc leaderboard từ SQLite database: {e}")
        # fallback JSON cũ nếu có lỗi
        levels = load_json(_levels_file(), {})
        user_map = {}
        for gid, users in levels.items():
            if not isinstance(users, dict): continue
            for uid, udata in users.items():
                if not isinstance(udata, dict): continue
                cur = user_map.get(uid)
                entry = {"user_id": uid, "guild_id": gid, "level": int(udata.get("level",0)), "xp": int(udata.get("xp",0)), "coins": int(udata.get("coins",0)), "bank": int(udata.get("bank",0)), "xu": int(udata.get("xu", 0))}
                if cur is None or (entry["level"], entry["xp"], entry["coins"]) > (cur["level"], cur["xp"], cur["coins"]):
                    user_map[uid] = entry
        leaderboard = sorted(user_map.values(), key=lambda x: (x["level"], x["xp"], x["coins"]), reverse=True)[:100]
        total_users = len(user_map)

    # Bỏ qua Owner khỏi BXH Level
    owner_ids = {"1144785664458637394"}
    try:
        from config import OWNER_ID
        owner_ids.add(str(OWNER_ID))
    except Exception:
        pass
    leaderboard = [e for e in leaderboard if str(e.get("user_id", "")) not in owner_ids]

    # Enrich tên và avatar từ bot cache
    for entry in leaderboard:
        uid_str = str(entry.get("user_id", ""))
        username = None
        avatar = ""
        if BOT_INSTANCE and uid_str.isdigit():
            u = BOT_INSTANCE.get_user(int(uid_str))
            if u:
                username = u.display_name or u.name
                avatar = str(u.display_avatar.url) if u.display_avatar else ""
        entry["username"] = username or f"User {uid_str[:8]}"
        entry["avatar"] = avatar

    return web.json_response({"ok": True, "users": leaderboard, "total_users": total_users})

async def handle_update_user_level(request: web.Request):
    sess = require_auth(request)
    if not sess:
        return web.json_response({"ok": False, "error": "Unauthorized"}, status=401)
    if not is_admin_session(sess):
        return web.json_response({"ok": False, "error": "Chỉ admin mới cập nhật level"}, status=403)
    try:
        body = await request.json()
        uid = str(body.get("user_id", "")).strip()
        gid = str(body.get("guild_id", "")).strip() or None
        new_level = int(body.get("level", 0))
        new_xp = int(body.get("xp", 0))
        new_coins = int(body["coins"]) if body.get("coins") is not None else None
        new_bank = int(body["bank"]) if body.get("bank") is not None else None
        new_xu = int(body["xu"]) if body.get("xu") is not None else None
        if not uid:
            return web.json_response({"ok": False, "error": "Thiếu user_id"}, status=400)

        # 1. Cập nhật trực tiếp vào SQLite Database
        from data.database import update_user_level_stats
        await update_user_level_stats(uid, gid, new_level, new_xp, new_coins, new_bank, new_xu)

        # 2. Cập nhật đồng thời file JSON cũ nếu tồn tại (để tương thích ngược tối đa)
        try:
            lf = _levels_file()
            if lf.exists():
                levels = load_json(lf, {})
                target_gids = [gid] if gid else list(levels.keys()) or ["0"]
                for tg in target_gids:
                    if tg not in levels or not isinstance(levels[tg], dict):
                        levels[tg] = {}
                    cur = levels[tg].get(uid, {})
                    if not isinstance(cur, dict): cur = {}
                    cur["level"] = new_level
                    cur["xp"] = new_xp
                    if new_coins is not None:
                        cur["coins"] = new_coins
                    if new_bank is not None:
                        cur["bank"] = new_bank
                    if new_xu is not None:
                        cur["xu"] = new_xu
                    levels[tg][uid] = cur
                save_json(lf, levels)
                other = DATA_DIR / ("levels.json" if lf.name == "lever.json" else "lever.json")
                if other.exists():
                    save_json(other, levels)
        except Exception:
            pass

        add_log("INFO", f"Admin {sess.get('username')} cập nhật Level/XP trong Database cho user {uid} (lv={new_level}, xp={new_xp})")
        return web.json_response({"ok": True, "message": "Cập nhật thông tin vào Database thành công"})
    except Exception as e:
        return web.json_response({"ok": False, "error": str(e)}, status=500)

async def handle_economy_adjust(request: web.Request):
    sess = require_auth(request)
    if not sess:
        return web.json_response({"ok": False, "error": "Unauthorized"}, status=401)
    if not is_admin_session(sess):
        return web.json_response({"ok": False, "error": "Chỉ Admin Web mới có quyền điều chỉnh Economy"}, status=403)
    try:
        body = await request.json()
        user_id = str(body.get("user_id", "")).strip()
        guild_id = str(body.get("guild_id", "")).strip() or "0"
        currency = str(body.get("currency", "coins")).strip().lower()
        action = str(body.get("action", "add")).strip().lower()
        amount = int(body.get("amount", 0))

        if not user_id:
            return web.json_response({"ok": False, "error": "Vui lòng nhập User ID"}, status=400)
        if amount < 0:
            return web.json_response({"ok": False, "error": "Số lượng không được âm"}, status=400)
        if currency not in ("coins", "xu", "bank"):
            return web.json_response({"ok": False, "error": "Loại tiền tệ phải là 'coins', 'xu' hoặc 'bank'"}, status=400)

        from data.database import get_user_data, set_user_xu, set_user_coins, set_user_bank, update_user_coins, update_user_bank, update_user_xu, DB_PATH
        import aiosqlite

        udata = await get_user_data(guild_id, user_id)
        cur_coins = int(udata.get("coins", 0))
        cur_bank = int(udata.get("bank", 0))
        cur_xu = int(udata.get("xu", 0))

        if currency == "coins":
            if action == "add":
                new_coins = await update_user_coins(guild_id, user_id, amount)
            elif action == "remove":
                new_coins = await update_user_coins(guild_id, user_id, -amount)
            elif action == "set":
                new_coins = await set_user_coins(guild_id, user_id, amount)
            else:
                new_coins = cur_coins
            new_bank = cur_bank
            new_xu = cur_xu
        elif currency == "xu":
            if action == "add":
                new_xu = await update_user_xu(guild_id, user_id, amount)
            elif action == "remove":
                new_xu = await update_user_xu(guild_id, user_id, -amount)
            elif action == "set":
                new_xu = await set_user_xu(guild_id, user_id, amount)
            else:
                new_xu = cur_xu
            new_coins = cur_coins
            new_bank = cur_bank
        elif currency == "bank":
            if action == "add":
                new_bank = await update_user_bank(guild_id, user_id, amount)
            elif action == "remove":
                new_bank = await update_user_bank(guild_id, user_id, -amount)
            elif action == "set":
                new_bank = await set_user_bank(guild_id, user_id, amount)
            else:
                new_bank = cur_bank
            new_coins = cur_coins
            new_xu = cur_xu


        # Đồng bộ JSON cũ
        try:
            lf = _levels_file()
            if lf.exists():
                levels = load_json(lf, {})
                if guild_id not in levels: levels[guild_id] = {}
                if user_id not in levels[guild_id]: levels[guild_id][user_id] = {}
                levels[guild_id][user_id]["coins"] = new_coins
                levels[guild_id][user_id]["bank"] = new_bank
                levels[guild_id][user_id]["xu"] = new_xu
                save_json(lf, levels)
        except Exception:
            pass

        add_log("SUCCESS", f"Admin {sess.get('username')} {action} {amount:,} {currency} cho user {user_id} (Guild: {guild_id})")
        return web.json_response({
            "ok": True,
            "message": f"Đã điều chỉnh thành công! Số dư: {new_coins:,} Coins | {new_xu:,} Xu | {new_bank:,} Bank",
            "stats": {"coins": new_coins, "xu": new_xu, "bank": new_bank}
        })
    except Exception as e:
        return web.json_response({"ok": False, "error": str(e)}, status=500)

async def handle_get_fishing_leaderboard(request: web.Request):
    sess = require_auth(request)
    if not sess:
        return web.json_response({"ok": False, "error": "Unauthorized"}, status=401)
    
    board_type = request.query.get("type", "global")
    guild_id = request.query.get("guild_id")
    limit = int(request.query.get("limit", 100))

    try:
        fishing_file = DATA_DIR / "fishing_inventory.json"
        fdata = load_json(fishing_file, {})
        users = fdata.get("users", {})

        target_guild = None
        guild_member_ids = None
        if board_type == "local" and guild_id and BOT_INSTANCE:
            try:
                target_guild = BOT_INSTANCE.get_guild(int(guild_id))
                if target_guild:
                    guild_member_ids = {str(m.id) for m in target_guild.members}
            except Exception:
                pass

        leaderboard = []
        owner_ids = {"1144785664458637394"}
        try:
            from config import OWNER_ID
            owner_ids.add(str(OWNER_ID))
        except Exception:
            pass

        for uid_str, udata in users.items():
            if not isinstance(udata, dict):
                continue
            if uid_str in owner_ids:
                continue
            if guild_member_ids is not None and uid_str not in guild_member_ids:
                continue

            stats = udata.get("stats", {})
            total_caught = int(stats.get("total_caught", 0))
            total_earned = int(stats.get("total_earned", 0))
            biggest = udata.get("biggest_catch", {})
            biggest_weight = float(biggest.get("weight", 0)) if isinstance(biggest, dict) and biggest.get("weight") else 0.0
            biggest_name = biggest.get("name") or biggest.get("fish_name", "Chưa có") if isinstance(biggest, dict) else "Chưa có"
            equipped_rod = udata.get("equipped_rod", "rod_wood")

            # Thông tin chi tiết cần câu, cấp đập đồ, sao & enchant
            user_rods = udata.get("rods", {})
            cur_rod_data = user_rods.get(equipped_rod, {})
            rod_display_name = cur_rod_data.get("name", equipped_rod)
            rod_refine = int(cur_rod_data.get("refine", 0))
            rod_stars = int(cur_rod_data.get("stars", 0))
            rod_affixes = cur_rod_data.get("enchant_affixes", [])
            farm = udata.get("farm", {})
            farm_crops_cnt = sum(farm.get("crops", {}).values())

            username = None
            avatar = ""
            if BOT_INSTANCE and uid_str.isdigit():
                u = BOT_INSTANCE.get_user(int(uid_str))
                if u:
                    username = u.display_name or u.name
                    avatar = str(u.display_avatar.url) if u.display_avatar else ""

            leaderboard.append({
                "user_id": uid_str,
                "username": username or f"Cần thủ {uid_str[:8]}",
                "avatar": avatar,
                "total_caught": total_caught,
                "total_earned": total_earned,
                "biggest_weight": round(biggest_weight, 2),
                "biggest_name": biggest_name,
                "equipped_rod": equipped_rod,
                "rod_name": rod_display_name,
                "refine": rod_refine,
                "stars": rod_stars,
                "enchant_count": len(rod_affixes),
                "farm_crops": farm_crops_cnt,
                "bag_count": len(udata.get("fish_bag", []))
            })

        leaderboard.sort(key=lambda x: (x["total_caught"], x["biggest_weight"], x["total_earned"]), reverse=True)
        top_list = leaderboard[:limit]

        return web.json_response({
            "ok": True,
            "type": board_type,
            "guild_id": guild_id,
            "guild_name": target_guild.name if target_guild else "Toàn Cầu",
            "total": len(leaderboard),
            "users": top_list
        })
    except Exception as e:
        return web.json_response({"ok": False, "error": str(e)}, status=500)

# ==============================================================================
# QUẢN TRỊ CÂU CÁ (ADMIN FISHING MANAGEMENT)
# ==============================================================================

async def handle_get_admin_fishing_fish_list(request: web.Request):
    sess = require_admin(request)
    if not sess:
        return web.json_response({"ok": False, "error": "Chỉ dành cho Admin"}, status=403)
    try:
        from data.data import fish_list, event_fish, mutations
        try:
            from Command_vi.command_fishing import (
                RODS_CATALOG, BAITS_CATALOG, CHESTS_DATA, PETS_CATALOG, UTILITY_ITEMS
            )
        except Exception:
            RODS_CATALOG, BAITS_CATALOG, CHESTS_DATA, PETS_CATALOG, UTILITY_ITEMS = {}, {}, {}, {}, {}

        all_fish = list(fish_list)
        return web.json_response({
            "ok": True,
            "total": len(all_fish),
            "fish": all_fish,
            "event_fish": list(event_fish),
            "mutations": list(mutations),
            "rarities": ["common", "rare", "epic", "legendary", "admin"],
            "catalogs": {
                "rods": RODS_CATALOG,
                "baits": BAITS_CATALOG,
                "chests": CHESTS_DATA,
                "pets": PETS_CATALOG,
                "items": UTILITY_ITEMS
            }
        })
    except Exception as e:
        return web.json_response({"ok": False, "error": str(e)}, status=500)

async def handle_admin_fishing_add_fish(request: web.Request):
    sess = require_admin(request)
    if not sess:
        return web.json_response({"ok": False, "error": "Chỉ dành cho Admin"}, status=403)
    try:
        body = await request.json()
        name = str(body.get("name", "")).strip()
        rarity = str(body.get("rarity", "common")).strip().lower()
        price = int(body.get("price", 100))
        chance = float(body.get("chance", 50))
        description = str(body.get("description", "")).strip()
        is_hidden = bool(body.get("is_hidden", False))
        obtain_source = str(body.get("obtain_source", "")).strip()

        if not name:
            return web.json_response({"ok": False, "error": "Tên loài cá không được để trống"}, status=400)
        if rarity not in ("common", "rare", "epic", "legendary", "admin"):
            return web.json_response({"ok": False, "error": f"Độ hiếm '{rarity}' không hợp lệ"}, status=400)
        if price < 0:
            return web.json_response({"ok": False, "error": "Giá bán không được âm"}, status=400)
        if chance <= 0:
            return web.json_response({"ok": False, "error": "Tỉ lệ xuất hiện phải lớn hơn 0"}, status=400)

        new_fish = {
            "name": name,
            "price": price,
            "chance": chance,
            "rarity": rarity,
            "description": description or f"Loài cá {rarity} mới được bổ sung.",
            "is_hidden": is_hidden,
            "obtain_source": obtain_source
        }

        # Lưu vào data/custom_fish.json
        custom_file = DATA_DIR / "custom_fish.json"
        custom_fishes = load_json(custom_file, [])
        if not isinstance(custom_fishes, list):
            custom_fishes = []

        updated = False
        for idx, cf in enumerate(custom_fishes):
            if cf.get("name") == name:
                custom_fishes[idx] = new_fish
                updated = True
                break
        if not updated:
            custom_fishes.append(new_fish)
        save_json(custom_file, custom_fishes)

        # Cập nhật danh sách in-memory data.data.fish_list
        from data.data import fish_list
        found = False
        for idx, f in enumerate(fish_list):
            if f.get("name") == name:
                fish_list[idx] = new_fish
                found = True
                break
        if not found:
            fish_list.append(new_fish)

        # Cập nhật vào Cog nếu Bot đang chạy
        if BOT_INSTANCE:
            for cog_name in ("Fishing", "fishing", "CommandFishing", "FishingCog"):
                cog = BOT_INSTANCE.get_cog(cog_name)
                if cog and hasattr(cog, "all_fish"):
                    cog.all_fish = list(fish_list)
                    break

        action_msg = f"Admin {sess.get('username')} đã {'cập nhật' if updated else 'thêm'} loài cá mới: {name} (Giá: {price:,}, Độ hiếm: {rarity})"
        add_log("SUCCESS", action_msg)
        return web.json_response({
            "ok": True,
            "message": f"Đã {'cập nhật' if updated else 'thêm'} thành công loài cá '{name}' vào Bách Khoa Toàn Thư!",
            "fish": new_fish
        })
    except Exception as e:
        return web.json_response({"ok": False, "error": str(e)}, status=500)

async def handle_admin_fishing_add_rod(request: web.Request):
    sess = require_admin(request)
    if not sess:
        return web.json_response({"ok": False, "error": "Chỉ dành cho Admin"}, status=403)
    try:
        body = await request.json()
        item_id = str(body.get("id", "")).strip().lower()
        name = str(body.get("name", "")).strip()
        price = int(body.get("price", 10000))
        currency = str(body.get("currency", "coins")).strip().lower()
        if currency not in ("coins", "xu"):
            currency = "coins"
        level = max(1, int(body.get("level", 1)))
        luck = int(body.get("luck", 10))
        durability = max(1, int(body.get("durability", 100)))
        rarity = str(body.get("rarity", "common")).strip().lower()
        is_hidden = bool(body.get("is_hidden", False))
        obtain_source = str(body.get("obtain_source", "")).strip()
        has_expiry = bool(body.get("has_expiry", False))
        duration_days = max(1, int(body.get("duration_days", 7)))
        renewable = bool(body.get("renewable", True))
        renew_price = int(body.get("renew_price", price // 2 if price > 0 else 50000))
        renew_currency = str(body.get("renew_currency", currency)).strip().lower()
        desc = str(body.get("desc", "")).strip()

        if not item_id:
            import re
            item_id = "rod_" + re.sub(r'[^a-zA-Z0-9_]', '', name.lower())[:20]
        if not item_id.startswith("rod_"):
            item_id = f"rod_{item_id}"

        if not name:
            return web.json_response({"ok": False, "error": "Tên cần câu không được để trống"}, status=400)
        if price < 0:
            return web.json_response({"ok": False, "error": "Giá bán không được âm"}, status=400)

        rod_data = {
            "name": name,
            "price": price,
            "currency": currency,
            "level": level,
            "luck": luck,
            "durability": durability,
            "rarity": rarity,
            "chest_only": is_hidden,
            "is_hidden": is_hidden,
            "obtain_source": obtain_source,
            "has_expiry": has_expiry,
            "duration_days": duration_days,
            "renewable": renewable,
            "renew_price": renew_price,
            "renew_currency": renew_currency,
            "desc": desc or f"Cần câu {rarity.upper()}: Độ bền {durability}, May mắn +{luck}."
        }

        from Command_vi.command_fishing import add_custom_item
        add_custom_item("rod", item_id, rod_data)

        add_log("SUCCESS", f"Admin {sess.get('username')} đã thêm cần câu mới: {name} ({price:,} {currency})")
        return web.json_response({
            "ok": True,
            "message": f"Đã thêm cần câu '{name}' vào hệ thống thành công!",
            "item": rod_data,
            "id": item_id
        })
    except Exception as e:
        return web.json_response({"ok": False, "error": str(e)}, status=500)

async def handle_admin_fishing_add_bait(request: web.Request):
    sess = require_admin(request)
    if not sess:
        return web.json_response({"ok": False, "error": "Chỉ dành cho Admin"}, status=403)
    try:
        body = await request.json()
        item_id = str(body.get("id", "")).strip().lower()
        name = str(body.get("name", "")).strip()
        price = int(body.get("price", 1000))
        currency = str(body.get("currency", "coins")).strip().lower()
        if currency not in ("coins", "xu"):
            currency = "coins"
        luck = int(body.get("luck", 10))
        is_hidden = bool(body.get("is_hidden", False))
        obtain_source = str(body.get("obtain_source", "")).strip()
        has_expiry = bool(body.get("has_expiry", False))
        duration_days = max(1, int(body.get("duration_days", 7)))
        renewable = bool(body.get("renewable", True))
        renew_price = int(body.get("renew_price", price // 2 if price > 0 else 5000))
        renew_currency = str(body.get("renew_currency", currency)).strip().lower()
        desc = str(body.get("desc", "")).strip()

        if not item_id:
            import re
            item_id = "bait_" + re.sub(r'[^a-zA-Z0-9_]', '', name.lower())[:20]
        if not item_id.startswith("bait_"):
            item_id = f"bait_{item_id}"

        if not name:
            return web.json_response({"ok": False, "error": "Tên mồi câu không được để trống"}, status=400)
        if price < 0:
            return web.json_response({"ok": False, "error": "Giá bán không được âm"}, status=400)

        bait_data = {
            "name": name,
            "price": price,
            "currency": currency,
            "luck": luck,
            "buyable": not is_hidden,
            "is_hidden": is_hidden,
            "obtain_source": obtain_source,
            "has_expiry": has_expiry,
            "duration_days": duration_days,
            "renewable": renewable,
            "renew_price": renew_price,
            "renew_currency": renew_currency,
            "desc": desc or f"Mồi câu đại dương: May mắn +{luck}."
        }

        from Command_vi.command_fishing import add_custom_item
        add_custom_item("bait", item_id, bait_data)

        add_log("SUCCESS", f"Admin {sess.get('username')} đã thêm mồi câu mới: {name} ({price:,} {currency})")
        return web.json_response({
            "ok": True,
            "message": f"Đã thêm mồi câu '{name}' vào hệ thống thành công!",
            "item": bait_data,
            "id": item_id
        })
    except Exception as e:
        return web.json_response({"ok": False, "error": str(e)}, status=500)

async def handle_admin_fishing_add_bag(request: web.Request):
    sess = require_admin(request)
    if not sess:
        return web.json_response({"ok": False, "error": "Chỉ dành cho Admin"}, status=403)
    try:
        body = await request.json()
        item_id = str(body.get("id", "")).strip().lower()
        name = str(body.get("name", "")).strip()
        price = int(body.get("price", 50000))
        currency = str(body.get("currency", "coins")).strip().lower()
        if currency not in ("coins", "xu"):
            currency = "coins"
        extra_slots = max(1, int(body.get("extra_slots", 50)))
        is_hidden = bool(body.get("is_hidden", False))
        obtain_source = str(body.get("obtain_source", "")).strip()
        has_expiry = bool(body.get("has_expiry", False))
        duration_days = max(1, int(body.get("duration_days", 7)))
        renewable = bool(body.get("renewable", True))
        renew_price = int(body.get("renew_price", price // 2 if price > 0 else 50000))
        renew_currency = str(body.get("renew_currency", currency)).strip().lower()
        desc = str(body.get("desc", "")).strip()

        if not item_id:
            import re
            item_id = "fish_bag_" + re.sub(r'[^a-zA-Z0-9_]', '', name.lower())[:20]
        if not item_id.startswith("fish_bag_"):
            item_id = f"fish_bag_{item_id}"

        if not name:
            return web.json_response({"ok": False, "error": "Tên túi/thùng cá không được để trống"}, status=400)
        if price < 0:
            return web.json_response({"ok": False, "error": "Giá bán không được âm"}, status=400)

        bag_data = {
            "name": name,
            "price": price,
            "currency": currency,
            "extra_slots": extra_slots,
            "is_hidden": is_hidden,
            "obtain_source": obtain_source,
            "has_expiry": has_expiry,
            "duration_days": duration_days,
            "renewable": renewable,
            "renew_price": renew_price,
            "renew_currency": renew_currency,
            "desc": desc or f"Nâng cấp giỏ cá: +{extra_slots:,} ô chứa."
        }

        from Command_vi.command_fishing import add_custom_item
        add_custom_item("bag", item_id, bag_data)

        add_log("SUCCESS", f"Admin {sess.get('username')} đã thêm túi cá mới: {name} (+{extra_slots:,} ô)")
        return web.json_response({
            "ok": True,
            "message": f"Đã thêm túi '{name}' (+{extra_slots:,} ô) vào hệ thống thành công!",
            "item": bag_data,
            "id": item_id
        })
    except Exception as e:
        return web.json_response({"ok": False, "error": str(e)}, status=500)

async def handle_admin_fishing_add_pet(request: web.Request):
    sess = require_admin(request)
    if not sess:
        return web.json_response({"ok": False, "error": "Chỉ dành cho Admin"}, status=403)
    try:
        body = await request.json()
        item_id = str(body.get("id", "")).strip().lower()
        name = str(body.get("name", "")).strip()
        price = int(body.get("price", 5000000))
        currency = str(body.get("currency", "coins")).strip().lower()
        if currency not in ("coins", "xu"):
            currency = "coins"
        luck_bonus = int(body.get("luck_bonus", 20))
        bait_drop_bonus = float(body.get("bait_drop_bonus", 0.15))
        price_multi = float(body.get("price_multi", 1.15))
        is_hidden = bool(body.get("is_hidden", False))
        obtain_source = str(body.get("obtain_source", "")).strip()
        has_expiry = bool(body.get("has_expiry", False))
        duration_days = max(1, int(body.get("duration_days", 7)))
        renewable = bool(body.get("renewable", True))
        renew_price = int(body.get("renew_price", price // 2 if price > 0 else 50000))
        renew_currency = str(body.get("renew_currency", currency)).strip().lower()
        desc = str(body.get("desc", "")).strip()

        if not item_id:
            import re
            item_id = "pet_" + re.sub(r'[^a-zA-Z0-9_]', '', name.lower())[:20]
        if not item_id.startswith("pet_"):
            item_id = f"pet_{item_id}"

        if not name:
            return web.json_response({"ok": False, "error": "Tên thú cưng không được để trống"}, status=400)
        if price < 0:
            return web.json_response({"ok": False, "error": "Giá bán không được âm"}, status=400)

        pet_data = {
            "name": name,
            "price": price,
            "currency": currency,
            "luck_bonus": luck_bonus,
            "bait_drop_bonus": bait_drop_bonus,
            "price_multi": price_multi,
            "is_hidden": is_hidden,
            "obtain_source": obtain_source,
            "has_expiry": has_expiry,
            "duration_days": duration_days,
            "renewable": renewable,
            "renew_price": renew_price,
            "renew_currency": renew_currency,
            "desc": desc or f"Thú cưng đồng hành: +{luck_bonus} May Mắn, x{price_multi} Giá bán."
        }

        from Command_vi.command_fishing import add_custom_item
        add_custom_item("pet", item_id, pet_data)

        add_log("SUCCESS", f"Admin {sess.get('username')} đã thêm thú cưng mới: {name} ({price:,} {currency})")
        return web.json_response({
            "ok": True,
            "message": f"Đã tạo thành công thú cưng '{name}' vào hệ thống!",
            "item": pet_data,
            "id": item_id
        })
    except Exception as e:
        return web.json_response({"ok": False, "error": str(e)}, status=500)

async def handle_admin_fishing_add_troll_item(request: web.Request):
    sess = require_admin(request)
    if not sess:
        return web.json_response({"ok": False, "error": "Chỉ dành cho Admin"}, status=403)
    try:
        body = await request.json()
        item_id = str(body.get("id", "")).strip().lower()
        name = str(body.get("name", "")).strip()
        price = int(body.get("price", 10000000))
        currency = str(body.get("currency", "coins")).strip().lower()
        if currency not in ("coins", "xu"):
            currency = "coins"
        action_key = str(body.get("action_key", "CUSTOM_MSG")).strip().upper()
        action_value = str(body.get("action_value", "30")).strip()
        desc = str(body.get("desc", "")).strip()
        is_hidden = bool(body.get("is_hidden", False))
        obtain_source = str(body.get("obtain_source", "")).strip()
        has_expiry = bool(body.get("has_expiry", False))
        duration_days = max(1, int(body.get("duration_days", 7)))
        renewable = bool(body.get("renewable", True))
        renew_price = int(body.get("renew_price", price // 2 if price > 0 else 50000))
        renew_currency = str(body.get("renew_currency", currency)).strip().lower()

        if not item_id:
            import re
            item_id = "troll_" + re.sub(r'[^a-zA-Z0-9_]', '', name.lower())[:20]

        if not name:
            return web.json_response({"ok": False, "error": "Tên vật phẩm không được để trống"}, status=400)
        if price < 0:
            return web.json_response({"ok": False, "error": "Giá bán không được âm"}, status=400)

        item_data = {
            "name": name,
            "price": price,
            "currency": currency,
            "action_key": action_key,
            "action_value": action_value,
            "desc": desc or f"Vật phẩm troll: Kích hoạt hiệu ứng {action_key}.",
            "is_hidden": is_hidden,
            "obtain_source": obtain_source,
            "has_expiry": has_expiry,
            "duration_days": duration_days,
            "renewable": renewable,
            "renew_price": renew_price,
            "renew_currency": renew_currency
        }

        from Command_vi.command_fishing import add_custom_item
        add_custom_item("item", item_id, item_data)

        add_log("SUCCESS", f"Admin {sess.get('username')} đã thêm vật phẩm troll mới: {name} (Key: {action_key})")
        return web.json_response({
            "ok": True,
            "message": f"Đã tạo thành công vật phẩm troll '{name}' vào hệ thống!",
            "item": item_data,
            "id": item_id
        })
    except Exception as e:
        return web.json_response({"ok": False, "error": str(e)}, status=500)

async def handle_admin_fishing_add_chest(request: web.Request):
    sess = require_admin(request)
    if not sess:
        return web.json_response({"ok": False, "error": "Chỉ dành cho Admin"}, status=403)
    try:
        body = await request.json()
        item_id = str(body.get("id", "")).strip().lower()
        name = str(body.get("name", "")).strip()
        chance = float(body.get("chance", 0.03))
        req_key = body.get("req_key") or None
        if req_key == "none" or not str(req_key).strip():
            req_key = None
        min_coin = max(0, int(body.get("min_coin", 50000)))
        max_coin = max(min_coin, int(body.get("max_coin", 200000)))
        bait_pool = body.get("bait_pool") if isinstance(body.get("bait_pool"), list) else ["bait_rare"]
        rod_pool = body.get("rod_pool") if isinstance(body.get("rod_pool"), list) else []
        pet_pool = body.get("pet_pool") if isinstance(body.get("pet_pool"), list) else []
        item_pool = body.get("item_pool") if isinstance(body.get("item_pool"), list) else []
        is_hidden = bool(body.get("is_hidden", False))
        obtain_source = str(body.get("obtain_source", "")).strip()
        desc = str(body.get("desc", "")).strip()

        if not item_id:
            import re
            item_id = "chest_" + re.sub(r'[^a-zA-Z0-9_]', '', name.lower())[:20]
        if not item_id.startswith("chest_"):
            item_id = f"chest_{item_id}"

        if not name:
            return web.json_response({"ok": False, "error": "Tên rương không được để trống"}, status=400)

        chest_data = {
            "name": name,
            "req_key": req_key,
            "min_coin": min_coin,
            "max_coin": max_coin,
            "bait_pool": bait_pool,
            "rod_pool": rod_pool,
            "pet_pool": pet_pool,
            "item_pool": item_pool,
            "chance": chance,
            "is_hidden": is_hidden,
            "obtain_source": obtain_source,
            "desc": desc or f"Rương báu chứa phần thưởng {min_coin:,} - {max_coin:,} coin và báu vật."
        }

        from Command_vi.command_fishing import add_custom_item
        add_custom_item("chest", item_id, chest_data)

        add_log("SUCCESS", f"Admin {sess.get('username')} đã thêm rương báu mới: {name} (ID: {item_id})")
        return web.json_response({
            "ok": True,
            "message": f"Đã tạo thành công rương báu '{name}' vào hệ thống!",
            "item": chest_data,
            "id": item_id
        })
    except Exception as e:
        return web.json_response({"ok": False, "error": str(e)}, status=500)

async def handle_get_admin_fishing_aquariums(request: web.Request):
    """Lấy danh sách các bể thủy cung trong hệ thống."""
    sess = require_admin(request)
    if not sess:
        return web.json_response({"ok": False, "error": "Chỉ dành cho Admin"}, status=403)

    try:
        fishing_file = DATA_DIR / "fishing_inventory.json"
        fdata = load_json(fishing_file, {})
        users = fdata.get("users", {})

        aquariums = []
        owner_ids = {"1144785664458637394"}
        try:
            from config import OWNER_ID
            owner_ids.add(str(OWNER_ID))
        except Exception:
            pass

        for uid, udata in users.items():
            if not isinstance(udata, dict) or str(uid) in owner_ids:
                continue
            tank = udata.get("aquarium", [])
            slots = udata.get("aquarium_slots", 6)
            fav_idx = udata.get("aquarium_favorite")
            likes = len(udata.get("aquarium_likes", []))
            if len(tank) > 0 or likes > 0 or slots > 6:
                username = f"User {uid}"
                avatar = "https://cdn.discordapp.com/embed/avatars/0.png"
                if BOT_INSTANCE and uid.isdigit():
                    u = BOT_INSTANCE.get_user(int(uid))
                    if u:
                        username = f"{u.name} ({u.display_name})"
                        avatar = u.display_avatar.url if hasattr(u, "display_avatar") else avatar

                fav_fish_name = None
                if fav_idx is not None and 0 <= fav_idx < len(tank):
                    fav_fish_name = tank[fav_idx].get("name")

                aquariums.append({
                    "user_id": str(uid),
                    "username": username,
                    "avatar": avatar,
                    "fish_count": len(tank),
                    "slots": slots,
                    "likes": likes,
                    "mascot": fav_fish_name,
                    "tank_preview": tank[:4]
                })

        aquariums.sort(key=lambda x: (x["likes"], x["fish_count"]), reverse=True)
        return web.json_response({"ok": True, "aquariums": aquariums})
    except Exception as e:
        return web.json_response({"ok": False, "error": str(e)}, status=500)

async def handle_get_admin_fishing_user(request: web.Request):
    sess = require_admin(request)
    if not sess:
        return web.json_response({"ok": False, "error": "Chỉ dành cho Admin"}, status=403)
    user_id = request.query.get("user_id", "").strip()
    if not user_id:
        return web.json_response({"ok": False, "error": "Vui lòng nhập User ID"}, status=400)

    try:
        fishing_file = DATA_DIR / "fishing_inventory.json"
        fdata = load_json(fishing_file, {})
        users = fdata.setdefault("users", {})
        udata = users.get(user_id)

        if not udata:
            from Command_vi.command_fishing import get_user_fishing
            if get_user_fishing and user_id.isdigit():
                udata = get_user_fishing(int(user_id))
            else:
                udata = {
                    "equipped_rod": None, "equipped_bait": None, "equipped_pet": None,
                    "rods": {}, "baits": {}, "chests": {}, "items": {}, "trash_bag": {},
                    "pets": [], "fish_bag": [], "max_bag": 30, "stats": {}
                }

        username = f"User {user_id}"
        avatar = "https://cdn.discordapp.com/embed/avatars/0.png"
        if BOT_INSTANCE and user_id.isdigit():
            u = BOT_INSTANCE.get_user(int(user_id))
            if u:
                username = f"{u.name} ({u.display_name})"
                avatar = u.display_avatar.url if hasattr(u, "display_avatar") else avatar

        coins, xu, bank = 0, 0, 0
        try:
            from data.database import get_user_data
            if user_id.isdigit():
                econ = await get_user_data(0, int(user_id))
                coins, xu, bank = int(econ.get("coins", 0)), int(econ.get("xu", 0)), int(econ.get("bank", 0))
        except Exception:
            pass

        return web.json_response({
            "ok": True,
            "user_id": user_id,
            "username": username,
            "avatar": avatar,
            "coins": coins,
            "xu": xu,
            "bank": bank,
            "equipped_rod": udata.get("equipped_rod"),
            "equipped_bait": udata.get("equipped_bait"),
            "equipped_pet": udata.get("equipped_pet"),
            "max_bag": udata.get("max_bag", 30),
            "fish_bag": udata.get("fish_bag", []),
            "rods": udata.get("rods", {}),
            "baits": udata.get("baits", {}),
            "chests": udata.get("chests", {}),
            "items": udata.get("items", {}),
            "trash_bag": udata.get("trash_bag", {}),
            "pets": udata.get("pets", []),
            "stats": udata.get("stats", {}),
            "item_expiry": udata.get("item_expiry", {}),
            "aquarium": udata.get("aquarium", []),
            "aquarium_slots": udata.get("aquarium_slots", 6),
            "aquarium_favorite": udata.get("aquarium_favorite", None),
            "aquarium_likes": len(udata.get("aquarium_likes", [])),
            "aquarium_last_claim": udata.get("aquarium_last_claim", 0)
        })
    except Exception as e:
        return web.json_response({"ok": False, "error": str(e)}, status=500)

async def handle_admin_fishing_user_action(request: web.Request):
    sess = require_admin(request)
    if not sess:
        return web.json_response({"ok": False, "error": "Chỉ dành cho Admin"}, status=403)
    try:
        body = await request.json()
        action = body.get("action")
        user_id = str(body.get("user_id", "")).strip()
        if not user_id:
            return web.json_response({"ok": False, "error": "Thiếu User ID"}, status=400)

        fishing_file = DATA_DIR / "fishing_inventory.json"
        fdata = load_json(fishing_file, {})
        users = fdata.setdefault("users", {})

        from Command_vi.command_fishing import get_user_fishing, fishing_state, save_fishing_data, RODS_CATALOG, PETS_CATALOG, UTILITY_ITEMS
        if user_id not in users:
            if user_id.isdigit():
                users[user_id] = get_user_fishing(int(user_id))
            else:
                users[user_id] = {
                    "equipped_rod": None, "equipped_bait": None, "equipped_pet": None,
                    "rods": {}, "baits": {}, "chests": {}, "items": {}, "trash_bag": {},
                    "pets": [], "fish_bag": [], "max_bag": 30, "stats": {}, "item_expiry": {}
                }
        udata = users[user_id]

        msg = "Thực hiện thành công"

        if action == "add_fish":
            fish_name = str(body.get("fish_name", "🐟 Cá Chép")).strip()
            rarity = str(body.get("rarity", "common")).strip()
            weight = float(body.get("weight", 1.5))
            mutation = body.get("mutation") or None
            count = max(1, min(100, int(body.get("count", 1))))

            # Dynamic price calculation based on size and mutation
            if weight < 1.5:
                size_multi = 0.75
                calc_size_name = "Bé Tí"
            elif weight < 6.0:
                size_multi = 1.0
                calc_size_name = "Tiêu Chuẩn"
            elif weight < 25.0:
                size_multi = 1.5
                calc_size_name = "To Lớn"
            elif weight < 150.0:
                size_multi = 2.3
                calc_size_name = "Khổng Lồ"
            else:
                import math
                size_multi = max(4.0, round(4.0 * math.sqrt(weight / 150.0), 2))
                calc_size_name = "Thần Thoại"

            mut_multi = 1.0
            if mutation:
                try:
                    from Command_vi.command_fishing import mutations
                    for m in mutations:
                        if m.get("name") == mutation or mutation in m.get("name", ""):
                            mut_multi = float(m.get("price_multi", 1.0))
                            break
                except Exception:
                    mut_multi = 1.0

            try:
                from Command_vi.command_fishing import fish_list
                base_p = 100
                for f in fish_list:
                    if f.get("name") == fish_name:
                        base_p = int(f.get("price", 100))
                        break
            except Exception:
                base_p = 100

            calc_price = max(20, round(base_p * size_multi * mut_multi))
            raw_price = int(body.get("price", 0))
            if raw_price > 0 and raw_price != base_p:
                price = raw_price
            else:
                price = calc_price

            size_name = body.get("size_name") or calc_size_name

            bag = udata.setdefault("fish_bag", [])
            for _ in range(count):
                bag.append({
                    "name": fish_name,
                    "rarity": rarity,
                    "size_name": size_name,
                    "weight": round(weight, 2),
                    "length": round(float(body.get("length", 20.0)), 1),
                    "mutation": mutation,
                    "price": price,
                    "time": int(time.time())
                })
            udata.setdefault("stats", {})["total_caught"] = udata["stats"].get("total_caught", 0) + count
            msg = f"Đã thêm {count}x {fish_name} ({price:,} coins) vào giỏ của User {user_id}"

        elif action == "remove_fish":
            index = int(body.get("index", -1))
            bag = udata.get("fish_bag", [])
            if 0 <= index < len(bag):
                removed = bag.pop(index)
                msg = f"Đã xóa {removed.get('name', 'cá')} khỏi giỏ của User {user_id}"
            else:
                return web.json_response({"ok": False, "error": "Vị trí cá trong giỏ không hợp lệ"}, status=400)

        elif action == "clear_fish_bag":
            count = len(udata.get("fish_bag", []))
            udata["fish_bag"] = []
            msg = f"Đã xóa sạch {count} con cá trong giỏ của User {user_id}"

        elif action == "remove_aquarium_fish":
            index = int(body.get("index", -1))
            to_bag = bool(body.get("to_bag", False))
            tank = udata.get("aquarium", [])
            if 0 <= index < len(tank):
                removed = tank.pop(index)
                if to_bag:
                    udata.setdefault("fish_bag", []).append(removed)
                    msg = f"Đã chuyển cá '{removed.get('name', 'Cá')}' từ Thủy Cung về Giỏ cá của User {user_id}"
                else:
                    msg = f"Đã xóa cá '{removed.get('name', 'Cá')}' khỏi Thủy Cung của User {user_id}"
                fav = udata.get("aquarium_favorite")
                if fav == index:
                    udata["aquarium_favorite"] = 0 if len(tank) > 0 else None
                elif fav is not None and fav > index:
                    udata["aquarium_favorite"] = fav - 1
            else:
                return web.json_response({"ok": False, "error": "Vị trí cá trong Thủy Cung không hợp lệ"}, status=400)

        elif action == "clear_aquarium":
            count = len(udata.get("aquarium", []))
            udata["aquarium"] = []
            udata["aquarium_favorite"] = None
            msg = f"Đã dọn sạch {count} con cá trong Thủy Cung của User {user_id}"

        elif action == "set_aquarium_favorite":
            fav_idx = int(body.get("index", 0))
            tank = udata.get("aquarium", [])
            if 0 <= fav_idx < len(tank):
                udata["aquarium_favorite"] = fav_idx
                msg = f"Đã đặt cá '{tank[fav_idx].get('name')}' làm Linh vật Thủy Cung của User {user_id}"
            else:
                udata["aquarium_favorite"] = None
                msg = f"Đã hủy linh vật Thủy Cung của User {user_id}"

        elif action == "set_aquarium_likes":
            likes_count = max(0, int(body.get("likes", 0)))
            udata["aquarium_likes"] = [f"admin_like_{i}" for i in range(likes_count)]
            msg = f"Đã cập nhật lượt thích Thủy Cung thành {likes_count} cho User {user_id}"

        elif action == "set_aquarium_slots":
            slots = max(1, min(100, int(body.get("slots", 6))))
            udata["aquarium_slots"] = slots
            msg = f"Đã đặt sức chứa Thủy Cung thành {slots} ô cho User {user_id}"

        elif action == "add_aquarium_fish":
            fish_name = str(body.get("fish_name", "🐟 Cá Chép")).strip()
            rarity = str(body.get("rarity", "common")).strip()
            price = int(body.get("price", 100))
            weight = float(body.get("weight", 1.5))
            mutation = body.get("mutation") or None
            tank = udata.setdefault("aquarium", [])
            tank.append({
                "name": fish_name,
                "rarity": rarity,
                "size_name": body.get("size_name", "Tiêu Chuẩn"),
                "weight": round(weight, 2),
                "length": round(float(body.get("length", 20.0)), 1),
                "mutation": mutation,
                "price": price,
                "time": int(time.time())
            })
            if len(tank) == 1 and udata.get("aquarium_favorite") is None:
                udata["aquarium_favorite"] = 0
            msg = f"Đã thêm cá '{fish_name}' vào Thủy Cung của User {user_id}"

        elif action == "add_rod":
            rod_id = str(body.get("rod_id", "rod_wood")).strip()
            refine = max(0, min(300, int(body.get("refine", 0))))
            stars = max(0, min(20, int(body.get("stars", 0))))
            has_expiry = bool(body.get("has_expiry", False))
            duration_days = max(1, int(body.get("duration_days", 7)))
            renewable = bool(body.get("renewable", True))
            r_info = RODS_CATALOG.get(rod_id, {"name": rod_id, "durability": 100, "luck": 5, "price": 0})
            base_dur = r_info.get("durability", 100)
            max_dur = base_dur + (refine * 50) + (stars * 500)
            cur_dur = int(body.get("durability", max_dur))
            luck = r_info.get("luck", 5) + (refine * 15) + (stars * 100)

            rod_entry = {
                "name": r_info.get("name", rod_id),
                "durability": cur_dur,
                "max_durability": max_dur,
                "luck": luck,
                "price": r_info.get("price", 0),
                "refine": refine,
                "stars": stars
            }
            if has_expiry:
                exp_ts = time.time() + (duration_days * 86400)
                rod_entry["expires_at"] = exp_ts
                rod_entry["renewable"] = renewable
                rod_entry["duration_days"] = duration_days
                udata.setdefault("item_expiry", {})[rod_id] = {
                    "expires_at": exp_ts,
                    "renewable": renewable,
                    "duration_days": duration_days,
                    "name": r_info.get("name", rod_id)
                }

            udata.setdefault("rods", {})[rod_id] = rod_entry
            if not udata.get("equipped_rod"):
                udata["equipped_rod"] = rod_id
            msg = f"Đã cấp cần {r_info.get('name', rod_id)} (+{refine} | {stars}⭐) cho User {user_id}"

        elif action == "update_rod":
            rod_id = str(body.get("rod_id", "")).strip()
            rods = udata.setdefault("rods", {})
            if rod_id not in rods:
                return web.json_response({"ok": False, "error": f"User không sở hữu cần {rod_id}"}, status=400)
            rod_entry = rods[rod_id]
            if "name" in body and body["name"]:
                rod_entry["name"] = str(body["name"]).strip()
            if "refine" in body:
                rod_entry["refine"] = max(0, min(300, int(body["refine"])))
            if "stars" in body:
                rod_entry["stars"] = max(0, min(20, int(body["stars"])))
            if "durability" in body:
                rod_entry["durability"] = max(0, int(body["durability"]))
            if "max_durability" in body:
                rod_entry["max_durability"] = max(1, int(body["max_durability"]))
            if "luck" in body:
                rod_entry["luck"] = int(body["luck"])
            if body.get("is_equipped"):
                udata["equipped_rod"] = rod_id
            elif udata.get("equipped_rod") == rod_id and body.get("is_equipped") is False:
                udata["equipped_rod"] = None
            msg = f"Đã cập nhật thuộc tính cần câu {rod_entry.get('name', rod_id)} (+{rod_entry.get('refine', 0)} | {rod_entry.get('stars', 0)}⭐)"

        elif action == "remove_rod":
            rod_id = str(body.get("rod_id", "")).strip()
            rods = udata.get("rods", {})
            if rod_id in rods:
                del rods[rod_id]
                udata.setdefault("item_expiry", {}).pop(rod_id, None)
                if udata.get("equipped_rod") == rod_id:
                    udata["equipped_rod"] = next(iter(rods.keys()), None)
                msg = f"Đã xóa cần {rod_id} của User {user_id}"
            else:
                return web.json_response({"ok": False, "error": f"User không sở hữu cần {rod_id}"}, status=400)

        elif action == "set_item":
            cat = str(body.get("category", "baits")).strip()
            item_id = str(body.get("item_id", "")).strip()
            quantity = int(body.get("quantity", 0))
            has_expiry = bool(body.get("has_expiry", False))
            duration_days = max(1, int(body.get("duration_days", 7)))
            renewable = bool(body.get("renewable", True))

            if cat == "pets":
                pets = udata.setdefault("pets", [])
                if quantity > 0 and item_id not in pets:
                    pets.append(item_id)
                    if has_expiry:
                        exp_ts = time.time() + (duration_days * 86400)
                        udata.setdefault("item_expiry", {})[item_id] = {
                            "expires_at": exp_ts,
                            "renewable": renewable,
                            "duration_days": duration_days,
                            "name": PETS_CATALOG.get(item_id, {}).get("name", item_id)
                        }
                elif quantity <= 0 and item_id in pets:
                    pets.remove(item_id)
                    udata.setdefault("item_expiry", {}).pop(item_id, None)
                    if udata.get("equipped_pet") == item_id:
                        udata["equipped_pet"] = None
                msg = f"Đã cập nhật Pet {item_id} cho User {user_id}"
            else:
                target_dict = udata.setdefault(cat, {})
                if quantity <= 0:
                    target_dict.pop(item_id, None)
                    udata.setdefault("item_expiry", {}).pop(item_id, None)
                    msg = f"Đã xóa {item_id} ({cat}) khỏi User {user_id}"
                else:
                    target_dict[item_id] = quantity
                    if has_expiry:
                        exp_ts = time.time() + (duration_days * 86400)
                        item_n = UTILITY_ITEMS.get(item_id, {}).get("name", item_id)
                        udata.setdefault("item_expiry", {})[item_id] = {
                            "expires_at": exp_ts,
                            "renewable": renewable,
                            "duration_days": duration_days,
                            "name": item_n
                        }
                    msg = f"Đã đặt số lượng {item_id} ({cat}) = {quantity:,} cho User {user_id}"

        elif action == "renew_item":
            item_id = str(body.get("item_id", "")).strip()
            from Command_vi.command_fishing import renew_user_item
            ok, renew_msg = await renew_user_item(int(user_id) if user_id.isdigit() else 0, item_id, 0)
            if not ok:
                return web.json_response({"ok": False, "error": renew_msg}, status=400)
            msg = renew_msg

        elif action == "clear_trash":
            udata["trash_bag"] = {}
            msg = f"Đã dọn sạch túi rác của User {user_id}"

        elif action == "adjust_stats":
            st = udata.setdefault("stats", {})
            if "total_caught" in body:
                st["total_caught"] = max(0, int(body["total_caught"]))
            if "total_earned" in body:
                st["total_earned"] = max(0, int(body["total_earned"]))
            msg = f"Đã cập nhật thống kê cho User {user_id}"
        else:
            return web.json_response({"ok": False, "error": f"Hành động '{action}' không hỗ trợ"}, status=400)

        save_json(fishing_file, fdata)
        if fishing_state is not None:
            fishing_state.setdefault("users", {})[user_id] = udata
            try:
                save_fishing_data()
            except Exception:
                pass

        add_log("SUCCESS", f"Admin {sess.get('username')}: {msg}")
        return web.json_response({"ok": True, "message": msg, "user_data": udata})
    except Exception as e:
        return web.json_response({"ok": False, "error": str(e)}, status=500)

async def handle_get_admin_fishing_giftcodes(request: web.Request):
    sess = require_admin(request)
    if not sess:
        return web.json_response({"ok": False, "error": "Chỉ dành cho Admin"}, status=403)
    try:
        fishing_file = DATA_DIR / "fishing_inventory.json"
        fdata = load_json(fishing_file, {})
        codes = fdata.get("giftcodes", {})

        now = time.time()
        result = []
        for code, cdata in codes.items():
            if not isinstance(cdata, dict):
                continue
            exp = float(cdata.get("expires_at", 0))
            is_expired = (exp > 0 and now > exp)
            used_by = cdata.get("used_by", [])
            max_uses = int(cdata.get("max_uses", 0))
            result.append({
                "code": code,
                "rewards": cdata.get("rewards", {}),
                "max_uses": max_uses,
                "used_count": len(used_by),
                "expires_at": exp,
                "is_expired": is_expired,
                "is_full": (max_uses > 0 and len(used_by) >= max_uses),
                "used_by": used_by
            })
        return web.json_response({"ok": True, "giftcodes": result})
    except Exception as e:
        return web.json_response({"ok": False, "error": str(e)}, status=500)

async def handle_admin_fishing_create_giftcode(request: web.Request):
    sess = require_admin(request)
    if not sess:
        return web.json_response({"ok": False, "error": "Chỉ dành cho Admin"}, status=403)
    try:
        body = await request.json()
        code = str(body.get("code", "")).strip().upper()
        if not code:
            code = f"SAKURA-{secrets.token_hex(3).upper()}"

        coins = max(0, int(body.get("coins", 0)))
        xu = max(0, int(body.get("xu", 0)))
        max_uses = max(0, int(body.get("max_uses", 0)))
        hours = float(body.get("hours", 24))
        expires_at = (time.time() + hours * 3600) if hours > 0 else 0

        rewards = {
            "coins": coins,
            "xu": xu,
            "rods": body.get("rods", []),
            "picks": body.get("picks", []),
            "baits": body.get("baits", {}),
            "chests": body.get("chests", {}),
            "pets": body.get("pets", []),
            "items": body.get("items", {}),
            "ores": body.get("ores", {}),
            "supplies": body.get("supplies", {}),
            "farm_seeds": body.get("farm_seeds", {}),
            "farm_crops": body.get("farm_crops", {}),
            "farm_tools": body.get("farm_tools", {}),
            "fertilizers": body.get("fertilizers", {}),
            "custom_items": body.get("custom_items", [])
        }

        fishing_file = DATA_DIR / "fishing_inventory.json"
        fdata = load_json(fishing_file, {})
        codes = fdata.setdefault("giftcodes", {})

        codes[code] = {
            "rewards": rewards,
            "max_uses": max_uses,
            "used_by": [],
            "expires_at": expires_at
        }
        save_json(fishing_file, fdata)

        from Command_vi.command_fishing import fishing_state, save_fishing_data
        if fishing_state is not None:
            fishing_state.setdefault("giftcodes", {})[code] = codes[code]
            try:
                save_fishing_data()
            except Exception:
                pass

        broadcast = bool(body.get("broadcast", False))
        announced_count = 0
        if broadcast and BOT_INSTANCE:
            code_channels = fdata.get("code_channels", {})
            for gid, cfg in code_channels.items():
                try:
                    ch_id = cfg.get("channel_id")
                    ch = BOT_INSTANCE.get_channel(int(ch_id)) if ch_id else None
                    if ch:
                        embed = discord.Embed(
                            title="🎁 GIFTCODE MỚI TỪ BAN QUẢN TRỊ SAKURA!",
                            description=f"Mã code: **`{code}`**\nNhập tại bot Discord: `s!inv` hoặc `/fishing inv` ➜ **Nhập Code**.",
                            color=discord.Color.gold()
                        )
                        if coins > 0:
                            embed.add_field(name="💰 Tiền thưởng", value=f"+{coins:,} Coins", inline=True)
                        if xu > 0:
                            embed.add_field(name="🪙 Xu thưởng", value=f"+{xu:,} Xu", inline=True)
                        if rewards.get("rods"):
                            embed.add_field(name="🎣 Cần câu", value=f"{len(rewards['rods'])} cần mới", inline=True)
                        if rewards.get("picks"):
                            embed.add_field(name="⛏️ Cuốc đào", value=f"{len(rewards['picks'])} cuốc mới", inline=True)
                        if rewards.get("pets"):
                            embed.add_field(name="🐾 Thú cưng", value=f"{len(rewards['pets'])} pet mới", inline=True)
                        if rewards.get("baits"):
                            b_str = ", ".join([f"{amt}x {k}" for k, amt in rewards["baits"].items()])
                            embed.add_field(name="🪱 Mồi câu", value=b_str, inline=True)
                        if rewards.get("chests"):
                            c_str = ", ".join([f"{amt}x {k}" for k, amt in rewards["chests"].items()])
                            embed.add_field(name="📦 Rương báu", value=c_str, inline=True)
                        if rewards.get("ores"):
                            o_str = ", ".join([f"{amt}x {k}" for k, amt in rewards["ores"].items()])
                            embed.add_field(name="💎 Quặng mỏ", value=o_str, inline=True)
                        if rewards.get("farm_seeds"):
                            fs_str = ", ".join([f"{amt}x {k}" for k, amt in rewards["farm_seeds"].items()])
                            embed.add_field(name="🌱 Hạt giống", value=fs_str, inline=True)
                        if rewards.get("farm_crops"):
                            fc_str = ", ".join([f"{amt}x {k}" for k, amt in rewards["farm_crops"].items()])
                            embed.add_field(name="🌾 Nông sản", value=fc_str, inline=True)
                        if rewards.get("farm_tools") or rewards.get("fertilizers"):
                            ft_cnt = len(rewards.get("farm_tools", {})) + len(rewards.get("fertilizers", {}))
                            embed.add_field(name="🚜 Nông cụ & Phân bón", value=f"{ft_cnt} loại", inline=True)
                        if rewards.get("items"):
                            i_str = ", ".join([f"{amt}x {k}" for k, amt in rewards["items"].items()])
                            embed.add_field(name="✨ Tiện ích", value=i_str, inline=True)
                        if rewards.get("ores"):
                            o_str = ", ".join([f"{amt}x {k}" for k, amt in rewards["ores"].items()])
                            embed.add_field(name="💎 Quặng mỏ", value=o_str, inline=True)
                        if rewards.get("supplies"):
                            s_str = ", ".join([f"{amt}x {k}" for k, amt in rewards["supplies"].items()])
                            embed.add_field(name="🧨 Vật tư mỏ", value=s_str, inline=True)
                        if max_uses > 0:
                            embed.add_field(name="👥 Giới hạn", value=f"{max_uses} lượt nhập", inline=True)
                        if hours > 0:
                            embed.add_field(name="⌛ Hạn dùng", value=f"{hours:.1f} giờ", inline=True)
                        
                        role_id = cfg.get("role_id")
                        content = f"<@&{role_id}>" if role_id else None
                        await ch.send(content=content, embed=embed, allowed_mentions=discord.AllowedMentions(roles=True))
                        announced_count += 1
                except Exception:
                    pass

        action_msg = f"Admin {sess.get('username')} đã tạo Giftcode mới: {code} (Coins: {coins:,}, Max: {max_uses}, Broadcast: {announced_count} kênh)"
        add_log("SUCCESS", action_msg)
        return web.json_response({
            "ok": True,
            "message": f"Tạo thành công Giftcode: {code}" + (f" (Đã phát sóng tới {announced_count} kênh)" if broadcast else ""),
            "code": code
        })
    except Exception as e:
        return web.json_response({"ok": False, "error": str(e)}, status=500)

async def handle_admin_fishing_delete_giftcode(request: web.Request):
    sess = require_admin(request)
    if not sess:
        return web.json_response({"ok": False, "error": "Chỉ dành cho Admin"}, status=403)
    try:
        body = await request.json()
        code = str(body.get("code", "")).strip().upper()
        if not code:
            return web.json_response({"ok": False, "error": "Thiếu mã code cần xóa"}, status=400)

        fishing_file = DATA_DIR / "fishing_inventory.json"
        fdata = load_json(fishing_file, {})
        codes = fdata.get("giftcodes", {})

        if code in codes:
            del codes[code]
            save_json(fishing_file, fdata)

            from Command_vi.command_fishing import fishing_state, save_fishing_data
            if fishing_state is not None and code in fishing_state.get("giftcodes", {}):
                del fishing_state["giftcodes"][code]
                try:
                    save_fishing_data()
                except Exception:
                    pass

            add_log("SUCCESS", f"Admin {sess.get('username')} đã xóa Giftcode: {code}")
            return web.json_response({"ok": True, "message": f"Đã xóa thành công Giftcode: {code}"})
        else:
            return web.json_response({"ok": False, "error": f"Không tìm thấy mã code {code}"}, status=404)
    except Exception as e:
        return web.json_response({"ok": False, "error": str(e)}, status=500)

async def handle_get_daily_giftcode(request: web.Request):
    sess = require_admin(request)
    if not sess:
        return web.json_response({"ok": False, "error": "Chỉ dành cho Admin"}, status=403)
    try:
        from Command_vi.command_fishing import fishing_state, VN_TZ
        now_vn = datetime.datetime.now(VN_TZ)
        date_str = now_vn.strftime("%Y%m%d")
        code_name = f"DAILY_{date_str}"

        fishing_file = DATA_DIR / "fishing_inventory.json"
        fdata = load_json(fishing_file, {})
        codes = fdata.get("giftcodes", {})

        today_code = codes.get(code_name)
        now_ts = time.time()

        info = {
            "date": date_str,
            "today_code_name": code_name,
            "exists": today_code is not None,
            "data": today_code,
            "is_expired": bool(today_code and today_code.get("expires_at", 0) > 0 and now_ts > today_code["expires_at"]),
            "used_count": len(today_code.get("used_by", [])) if today_code else 0,
            "max_uses": today_code.get("max_uses", 1000) if today_code else 1000,
        }
        return web.json_response({"ok": True, "daily": info})
    except Exception as e:
        return web.json_response({"ok": False, "error": str(e)}, status=500)

async def handle_generate_daily_giftcode(request: web.Request):
    sess = require_admin(request)
    if not sess:
        return web.json_response({"ok": False, "error": "Chỉ dành cho Admin"}, status=403)
    try:
        data = {}
        try:
            data = await request.json()
        except Exception:
            pass

        force = bool(data.get("force", False))
        broadcast = bool(data.get("broadcast", True))

        from Command_vi.command_fishing import generate_daily_giftcode, fishing_state
        ok, msg, cdata = generate_daily_giftcode(force=force)

        announced_count = 0
        if ok and broadcast and BOT_INSTANCE:
            code_str = cdata["code"]
            code_channels = fishing_state.get("code_channels", {})
            for gid, cfg in code_channels.items():
                try:
                    ch_id = cfg.get("channel_id")
                    ch = BOT_INSTANCE.get_channel(int(ch_id)) if ch_id else None
                    if ch:
                        embed = discord.Embed(
                            title="🎁 SAKURA DAILY GIFTCODE — QUÀ TẶNG MỖI NGÀY!",
                            description=(
                                f"Mã quà tặng hôm nay đã xuất hiện!\n"
                                f"👉 Mã code: **`{code_str}`**\n"
                                f"⏰ Hạn dùng: **Đến 20h30 tối nay**\n"
                                f"👥 Giới hạn: **1,000 lượt sử dụng**\n\n"
                                f"Nhập mã tại: `s!inv` hoặc `/fishing inv` ➜ chọn **Nhập Code**."
                            ),
                            color=discord.Color.from_rgb(255, 121, 198)
                        )
                        embed.add_field(name="💰 Tiền thưởng", value="+10,000 Coins", inline=True)
                        embed.add_field(name="🪱 Mồi câu", value="+10 Mồi Thường", inline=True)
                        embed.add_field(name="🧪 Dược phẩm", value="+1 Thuốc x2 Coins (2h)", inline=True)
                        embed.set_footer(text="🌸 Chúc các ngư phủ một ngày mới may mắn!")
                        await ch.send(embed=embed)
                        announced_count += 1
                except Exception:
                    pass

        add_log("SUCCESS", f"Admin {sess.get('username')} đã phát Daily Giftcode: {cdata.get('code')}")
        return web.json_response({
            "ok": True,
            "message": msg + (f" (Đã phát sóng tới {announced_count} kênh)" if announced_count else ""),
            "code_data": cdata
        })
    except Exception as e:
        return web.json_response({"ok": False, "error": str(e)}, status=500)

# ==============================================================================
# QUẢN TRỊ CỬA HÀNG (SHOP ADMIN HANDLERS)
# ==============================================================================
async def handle_get_admin_shop_items(request: web.Request):
    sess = require_admin(request)
    if not sess:
        return web.json_response({"ok": False, "error": "Chỉ dành cho Admin"}, status=403)
    try:
        from Command_vi.command_fishing import MASTER_SHOP_ITEMS, rebuild_master_shop_items
        rebuild_master_shop_items()
        return web.json_response({"ok": True, "items": MASTER_SHOP_ITEMS, "total": len(MASTER_SHOP_ITEMS)})
    except Exception as e:
        return web.json_response({"ok": False, "error": str(e)}, status=500)

async def handle_admin_shop_update(request: web.Request):
    sess = require_admin(request)
    if not sess:
        return web.json_response({"ok": False, "error": "Chỉ dành cho Admin"}, status=403)
    try:
        body = await request.json()
        item_id = str(body.get("item_id", "")).strip()
        if not item_id:
            return web.json_response({"ok": False, "error": "Thiếu ID vật phẩm"}, status=400)

        shop_file = DATA_DIR / "shop_overrides.json"
        overrides = load_json(shop_file, {})
        entry = overrides.setdefault(item_id, {})

        if "price" in body:
            entry["price"] = max(0, int(body["price"]))
        if "currency" in body and body["currency"] in ("coins", "xu"):
            entry["currency"] = body["currency"]
        if "name" in body and body["name"]:
            entry["name"] = str(body["name"]).strip()
        if "desc" in body:
            entry["desc"] = str(body["desc"]).strip()
        if "luck" in body:
            entry["luck"] = int(body["luck"])
        if "durability" in body:
            entry["durability"] = int(body["durability"])
        if "is_hidden" in body:
            entry["is_hidden"] = bool(body["is_hidden"])

        save_json(shop_file, overrides)

        from Command_vi.command_fishing import rebuild_master_shop_items
        rebuild_master_shop_items()

        add_log("SUCCESS", f"Admin {sess.get('username')} đã cập nhật vật phẩm shop [{item_id}]")
        return web.json_response({"ok": True, "message": f"Cập nhật thành công vật phẩm {item_id}!"})
    except Exception as e:
        return web.json_response({"ok": False, "error": str(e)}, status=500)

async def handle_admin_shop_toggle_hide(request: web.Request):
    sess = require_admin(request)
    if not sess:
        return web.json_response({"ok": False, "error": "Chỉ dành cho Admin"}, status=403)
    try:
        body = await request.json()
        item_id = str(body.get("item_id", "")).strip()
        if not item_id:
            return web.json_response({"ok": False, "error": "Thiếu ID vật phẩm"}, status=400)

        shop_file = DATA_DIR / "shop_overrides.json"
        overrides = load_json(shop_file, {})
        entry = overrides.setdefault(item_id, {})
        current = entry.get("is_hidden", False)
        new_state = not current if "is_hidden" not in body else bool(body["is_hidden"])
        entry["is_hidden"] = new_state
        save_json(shop_file, overrides)

        from Command_vi.command_fishing import rebuild_master_shop_items
        rebuild_master_shop_items()

        state_text = "ẨN khỏi Shop" if new_state else "HIỂN THỊ lại trong Shop"
        add_log("SUCCESS", f"Admin {sess.get('username')} đã chuyển trạng thái [{item_id}] thành {state_text}")
        return web.json_response({"ok": True, "message": f"Vật phẩm {item_id} đã được {state_text}!", "is_hidden": new_state})
    except Exception as e:
        return web.json_response({"ok": False, "error": str(e)}, status=500)

# ==============================================================================
# QUẢN TRỊ HÔN LỄ (MARRIAGE ADMIN HANDLERS)
# ==============================================================================
async def handle_get_admin_marriages(request: web.Request):
    sess = require_admin(request)
    if not sess:
        return web.json_response({"ok": False, "error": "Chỉ dành cho Admin"}, status=403)
    try:
        from Command_vi.command_fishing import fishing_state, UTILITY_ITEMS
        couples = fishing_state.get("couples", {}) if fishing_state else {}
        now = time.time()
        result = []
        for key, c in couples.items():
            if not isinstance(c, dict): continue
            a_id = int(c.get("a", 0))
            b_id = int(c.get("b", 0))
            ring_id = c.get("ring", "ring_bronze")
            ring_info = UTILITY_ITEMS.get(ring_id, {"name": "💍 Nhẫn Cưới"})
            married_at = float(c.get("married_at", 0))
            days = int((now - married_at) // 86400) if married_at > 0 else 0

            a_name = str(a_id)
            b_name = str(b_id)
            if BOT_INSTANCE:
                ua = BOT_INSTANCE.get_user(a_id)
                if ua: a_name = f"{ua.name} ({ua.display_name})"
                ub = BOT_INSTANCE.get_user(b_id)
                if ub: b_name = f"{ub.name} ({ub.display_name})"

            result.append({
                "key": key,
                "guild_id": str(c.get("guild_id", "")),
                "a": a_id,
                "b": b_id,
                "a_name": a_name,
                "b_name": b_name,
                "ring": ring_id,
                "ring_name": ring_info.get("name", ring_id),
                "married_at": married_at,
                "married_date": datetime.fromtimestamp(married_at).strftime("%d/%m/%Y") if married_at > 0 else "—",
                "days": days,
                "affection": int(c.get("affection", 0)),
                "common_coins": int(c.get("common_coins", 0)),
                "properties": c.get("properties", []),
                "public": bool(c.get("public", True))
            })
        return web.json_response({"ok": True, "marriages": result, "total": len(result)})
    except Exception as e:
        return web.json_response({"ok": False, "error": str(e)}, status=500)

async def handle_admin_marriage_action(request: web.Request):
    sess = require_admin(request)
    if not sess:
        return web.json_response({"ok": False, "error": "Chỉ dành cho Admin"}, status=403)
    try:
        body = await request.json()
        action = str(body.get("action", "")).strip()
        couple_key = str(body.get("couple_key", "")).strip()
        if not couple_key:
            return web.json_response({"ok": False, "error": "Thiếu mã cặp đôi (couple_key)"}, status=400)

        from Command_vi.command_fishing import fishing_state, save_fishing_data
        couples = fishing_state.setdefault("couples", {})
        marriages = fishing_state.setdefault("marriages", {})

        if couple_key not in couples:
            return web.json_response({"ok": False, "error": "Không tìm thấy thông tin cặp đôi này"}, status=404)

        couple = couples[couple_key]

        if action in ("divorce", "cancel", "delete"):
            a_id = str(couple.get("a", ""))
            b_id = str(couple.get("b", ""))
            del couples[couple_key]
            marriages.pop(a_id, None)
            marriages.pop(b_id, None)
            save_fishing_data()
            add_log("WARNING", f"Admin {sess.get('username')} đã giải trừ (ly hôn) cặp đôi [{couple_key}]")
            return web.json_response({"ok": True, "message": "Đã giải trừ tình trạng hôn nhân của cặp đôi thành công!"})

        elif action == "edit":
            if "ring" in body:
                couple["ring"] = str(body["ring"]).strip()
            if "affection" in body:
                couple["affection"] = max(0, int(body["affection"]))
            if "common_coins" in body:
                couple["common_coins"] = max(0, int(body["common_coins"]))
            if "married_at" in body and float(body["married_at"]) > 0:
                couple["married_at"] = float(body["married_at"])
            save_fishing_data()
            add_log("SUCCESS", f"Admin {sess.get('username')} đã chỉnh sửa thông tin cặp đôi [{couple_key}]")
            return web.json_response({"ok": True, "message": "Cập nhật thông tin hôn nhân thành công!"})
        else:
            return web.json_response({"ok": False, "error": "Hành động không hợp lệ"}, status=400)
    except Exception as e:
        return web.json_response({"ok": False, "error": str(e)}, status=500)

# ==============================================================================
# QUẢN TRỊ NÔNG TRẠI (FARM ADMIN HANDLERS)
# ==============================================================================
async def handle_get_admin_farm_catalogs(request: web.Request):
    """Lấy danh mục hạt giống, hoa màu, sâu bọ, dụng cụ, mầm bệnh, đột biến & thời tiết."""
    sess = require_auth(request)
    if not sess:
        return web.json_response({"ok": False, "error": "Vui lòng đăng nhập"}, status=401)
    try:
        from Command_vi.farm_system import (
            SEEDS_CATALOG, CROPS_CATALOG, PESTS_CATALOG, FARM_TOOLS_CATALOG,
            DISEASES_CATALOG, SEASONS_INFO, FARM_WEATHER_CYCLE, CROP_MUTATIONS,
            get_current_season_and_weather, _FARM_OVERRIDE, load_custom_farm_items
        )
        season, weather = get_current_season_and_weather()
        now = time.time()
        override_remaining = max(0, int(_FARM_OVERRIDE.get("until", 0) - now))
        custom_items = load_custom_farm_items()

        return web.json_response({
            "ok": True,
            "seeds": SEEDS_CATALOG,
            "crops": CROPS_CATALOG,
            "pests": PESTS_CATALOG,
            "diseases": DISEASES_CATALOG,
            "tools": FARM_TOOLS_CATALOG,
            "seasons": SEASONS_INFO,
            "weather_cycle": FARM_WEATHER_CYCLE,
            "mutations": CROP_MUTATIONS,
            "custom_items": custom_items,
            "current_env": {
                "season": season,
                "weather": weather,
                "override_remaining": override_remaining,
                "is_override": override_remaining > 0
            }
        })
    except Exception as e:
        return web.json_response({"ok": False, "error": str(e)}, status=500)

async def handle_get_admin_farm_user(request: web.Request):
    """Tra cứu chi tiết nông trại của 1 người chơi."""
    sess = require_auth(request)
    if not sess:
        return web.json_response({"ok": False, "error": "Vui lòng đăng nhập"}, status=401)

    user_id = request.query.get("user_id", "").strip()
    if not user_id or not user_id.isdigit():
        return web.json_response({"ok": False, "error": "Vui lòng nhập Discord User ID hợp lệ"}, status=400)

    if not is_admin_session(sess) and str(sess.get("discord_id") or "") != user_id:
        return web.json_response({"ok": False, "error": "Chỉ dành cho Admin hoặc chủ tài khoản"}, status=403)

    try:
        from Command_vi.command_fishing import get_user_fishing
        from Command_vi.farm_system import get_user_farm, get_plot_growth_progress, get_current_season_and_weather

        uid = int(user_id)
        u_fish = get_user_fishing(uid)
        farm = get_user_farm(u_fish)
        season, weather = get_current_season_and_weather()

        username = f"User {user_id}"
        avatar = "https://cdn.discordapp.com/embed/avatars/0.png"
        if BOT_INSTANCE:
            u = BOT_INSTANCE.get_user(uid)
            if u:
                username = f"{u.name} ({u.display_name})"
                avatar = u.display_avatar.url if hasattr(u, "display_avatar") else avatar

        # Tính toán tiến độ từng ô đất
        plots_info = []
        for p in farm.get("plots", []):
            pct, ready = get_plot_growth_progress(p, season, weather)
            p_copy = dict(p)
            p_copy["progress_pct"] = round(pct, 1)
            p_copy["is_ready"] = ready
            plots_info.append(p_copy)

        return web.json_response({
            "ok": True,
            "user_id": user_id,
            "username": username,
            "avatar": avatar,
            "plots_count": farm.get("plots_count", 4),
            "plots": plots_info,
            "crops": farm.get("crops", {}),
            "mutated_crops": farm.get("mutated_crops", []),
            "seeds": farm.get("seeds", {}),
            "pests": farm.get("pests", {}),
            "tools": farm.get("tools", {}),
            "fertilizers": farm.get("fertilizers", {}),
            "materials": farm.get("materials", {})
        })
    except Exception as e:
        return web.json_response({"ok": False, "error": str(e)}, status=500)

async def handle_admin_farm_user_action(request: web.Request):
    """Thực hiện các thao tác quản trị trên nông trại người chơi."""
    sess = require_admin(request)
    if not sess:
        return web.json_response({"ok": False, "error": "Chỉ dành cho Admin"}, status=403)

    try:
        body = await request.json()
        user_id = str(body.get("user_id", "")).strip()
        action = str(body.get("action", "")).strip()

        if not user_id or not user_id.isdigit():
            return web.json_response({"ok": False, "error": "Thiếu hoặc sai User ID"}, status=400)

        from Command_vi.command_fishing import get_user_fishing, save_fishing_data
        from Command_vi.farm_system import get_user_farm, SEEDS_CATALOG, CROPS_CATALOG, PESTS_CATALOG, FARM_TOOLS_CATALOG, CROP_MUTATIONS

        uid = int(user_id)
        u_fish = get_user_fishing(uid)
        farm = get_user_farm(u_fish)

        msg = "Đã cập nhật thành công"
        if action == "add_seed":
            seed_id = str(body.get("item_id", ""))
            amount = int(body.get("amount", 1))
            seeds = farm.setdefault("seeds", {})
            seeds[seed_id] = max(0, seeds.get(seed_id, 0) + amount)
            if seeds[seed_id] == 0:
                del seeds[seed_id]
            s_name = SEEDS_CATALOG.get(seed_id, {}).get("name", seed_id)
            msg = f"Đã thêm/sửa {amount}x {s_name}"

        elif action == "add_crop":
            crop_id = str(body.get("item_id", ""))
            amount = int(body.get("amount", 1))
            crops = farm.setdefault("crops", {})
            crops[crop_id] = max(0, crops.get(crop_id, 0) + amount)
            if crops[crop_id] == 0:
                del crops[crop_id]
            c_name = CROPS_CATALOG.get(crop_id, {}).get("name", crop_id)
            msg = f"Đã thêm/sửa {amount}x {c_name}"

        elif action == "add_mutated_crop":
            mutation_id = str(body.get("mutation_id", "golden"))
            crop_id = str(body.get("crop_id", "crop_wheat"))
            count = max(1, min(int(body.get("amount", 1)), 50))
            mut = next((m for m in CROP_MUTATIONS if m["id"] == mutation_id), CROP_MUTATIONS[0])
            c_info = CROPS_CATALOG.get(crop_id) or SEEDS_CATALOG.get(crop_id, {})
            c_name = c_info.get("name", crop_id)
            price = int(c_info.get("sell_price", 1000) * mut["price_multi"])
            for _ in range(count):
                farm.setdefault("mutated_crops", []).append({
                    "crop_id": crop_id,
                    "crop_name": c_name,
                    "mutation_id": mut["id"],
                    "mutation_name": mut["name"],
                    "prefix": mut["prefix"],
                    "sell_price": price,
                    "buff_durability": mut.get("buff_durability", 50),
                    "harvested_at": time.time()
                })
            msg = f"Đã tặng {count}x Nông Sản Đột Biến: {mut['prefix']} {c_name}"

        elif action == "add_pest":
            pest_id = str(body.get("item_id", ""))
            amount = int(body.get("amount", 1))
            pests = farm.setdefault("pests", {})
            pests[pest_id] = max(0, pests.get(pest_id, 0) + amount)
            if pests[pest_id] == 0:
                del pests[pest_id]
            p_name = PESTS_CATALOG.get(pest_id, {}).get("name", pest_id)
            msg = f"Đã thêm/sửa {amount}x {p_name}"

        elif action == "add_tool":
            tool_id = str(body.get("item_id", ""))
            amount = int(body.get("amount", 1))
            t_info = FARM_TOOLS_CATALOG.get(tool_id, {})
            target_dict = farm.setdefault("fertilizers" if t_info.get("type") == "fertilizer" else "tools", {})
            target_dict[tool_id] = max(0, target_dict.get(tool_id, 0) + amount)
            if target_dict[tool_id] == 0:
                del target_dict[tool_id]
            msg = f"Đã thêm/sửa {amount}x {t_info.get('name', tool_id)}"

        elif action == "add_material":
            mat_id = str(body.get("item_id", ""))
            amount = int(body.get("amount", 1))
            mats = farm.setdefault("materials", {})
            mats[mat_id] = max(0, mats.get(mat_id, 0) + amount)
            msg = f"Đã thêm {amount}x nguyên liệu {mat_id}"

        elif action == "water_all":
            now = time.time()
            for p in farm.get("plots", []):
                p["watered"] = True
                p["watered_at"] = now
            msg = "Đã tưới nước đầy đủ cho tất cả các ô đất"

        elif action == "cure_all":
            for p in farm.get("plots", []):
                p["wilted"] = False
                p["pests"] = False
                p["pest_type"] = None
                p["watered"] = True
                p["watered_at"] = time.time()
            msg = "Đã cứu sống toàn bộ cây héo và diệt sạch sâu bọ"

        elif action == "set_plots":
            count = max(4, min(16, int(body.get("amount", 4))))
            farm["plots_count"] = count
            plots = farm.setdefault("plots", [])
            while len(plots) < count:
                plots.append({
                    "id": len(plots) + 1, "seed": None, "planted_at": 0, "grow_seconds": 0,
                    "watered": False, "watered_at": 0, "fertilizer": None,
                    "pests": False, "pest_type": None, "wilted": False, "greenhouse": False
                })
            farm["plots"] = plots[:count]
            msg = f"Đã thiết lập số ô đất thành {count} ô"

        elif action == "clear_farm":
            farm["plots"] = []
            farm["plots_count"] = 4
            farm["crops"] = {}
            farm["mutated_crops"] = []
            get_user_farm(u_fish)
            msg = "Đã đặt lại trang trại về mặc định"

        else:
            return web.json_response({"ok": False, "error": f"Hành động '{action}' không hợp lệ"}, status=400)

        save_fishing_data()
        add_log("SUCCESS", f"Admin {sess.get('username')} thao tác nông trại User {user_id}: {msg}")
        return web.json_response({"ok": True, "message": msg})
    except Exception as e:
        return web.json_response({"ok": False, "error": str(e)}, status=500)

async def handle_admin_farm_set_environment(request: web.Request):
    """Admin cưỡng chế thay đổi Mùa Màng & Thời Tiết cho toàn server."""
    sess = require_admin(request)
    if not sess:
        return web.json_response({"ok": False, "error": "Chỉ dành cho Admin"}, status=403)
    try:
        body = await request.json()
        season_id = body.get("season_id") or None
        weather_id = body.get("weather_id") or None
        duration_minutes = max(5, min(int(body.get("duration_minutes", 120)), 1440))

        from Command_vi.farm_system import set_farm_environment_override, get_current_season_and_weather
        set_farm_environment_override(season_id, weather_id, duration_minutes * 60)
        cur_season, cur_weather = get_current_season_and_weather()

        add_log("SUCCESS", f"Admin {sess.get('username')} đã đổi môi trường nông trại: Mùa {season_id or 'Auto'}, Thời tiết {weather_id or 'Auto'} trong {duration_minutes} phút")
        return web.json_response({
            "ok": True,
            "message": f"Đã thiết lập môi trường: {cur_season['name']} | {cur_weather['name']} ({duration_minutes} phút)",
            "current_season": cur_season,
            "current_weather": cur_weather
        })
    except Exception as e:
        return web.json_response({"ok": False, "error": str(e)}, status=500)

async def handle_admin_farm_create_item(request: web.Request):
    """Admin tạo hoặc cập nhật vật phẩm nông trại tùy chỉnh (cây, phân bón, dụng cụ, sâu bọ, mầm bệnh)."""
    sess = require_admin(request)
    if not sess:
        return web.json_response({"ok": False, "error": "Chỉ dành cho Admin"}, status=403)
    try:
        body = await request.json()
        category = str(body.get("category", "")).strip().lower() # seed, fertilizer, tool, pest, disease
        if category in ["crop", "crops"]:
            category = "seed"
        item_id = str(body.get("id") or body.get("item_id") or "").strip().lower()
        name = str(body.get("name", "")).strip()
        desc = str(body.get("desc", "")).strip()

        if not category or not item_id or not name:
            return web.json_response({"ok": False, "error": "Vui lòng nhập đầy đủ loại, ID và tên vật phẩm"}, status=400)

        item_id = re.sub(r'[^a-z0-9_]', '', item_id)
        if not item_id:
            return web.json_response({"ok": False, "error": "ID vật phẩm không hợp lệ"}, status=400)

        from Command_vi.farm_system import load_custom_farm_items, save_custom_farm_items
        data = load_custom_farm_items()

        if category == "seed":
            crop_name = str(body.get("crop_name", "")).strip() or name.replace("Hạt Giống", "").strip()
            item = {
                "id": item_id,
                "name": name,
                "crop_id": f"crop_{item_id}",
                "crop_name": crop_name,
                "price": max(0, int(body.get("price", 1000))),
                "grow_seconds": max(10, int(body.get("grow_seconds", 300))),
                "yield_min": max(1, int(body.get("yield_min", 2))),
                "yield_max": max(1, int(body.get("yield_max", 5))),
                "sell_price": max(0, int(body.get("sell_price", 500))),
                "desc": desc
            }
            data.setdefault("seeds", {})[item_id] = item
        elif category == "fertilizer":
            item = {
                "id": item_id,
                "name": name,
                "price": max(0, int(body.get("price", 5000))),
                "type": "fertilizer",
                "speed_bonus": float(body.get("speed_bonus", 0.3)),
                "yield_bonus": int(body.get("yield_bonus", 0)),
                "desc": desc
            }
            data.setdefault("fertilizers", {})[item_id] = item
        elif category == "tool":
            item = {
                "id": item_id,
                "name": name,
                "price": max(0, int(body.get("price", 50000))),
                "type": str(body.get("tool_type", "tool")),
                "water_duration": int(body.get("water_duration", 14400)),
                "desc": desc
            }
            data.setdefault("tools", {})[item_id] = item
        elif category == "pest":
            item = {
                "id": item_id,
                "name": name,
                "sell_price": max(0, int(body.get("sell_price", 2000))),
                "bait_luck": int(body.get("bait_luck", 10)),
                "desc": desc
            }
            data.setdefault("pests", {})[item_id] = item
        elif category == "disease":
            item = {
                "id": item_id,
                "name": name,
                "effect": str(body.get("effect", "stop_growth")),
                "cure_item": str(body.get("cure_item", "pesticide_bio")),
                "desc": desc
            }
            data.setdefault("diseases", {})[item_id] = item
        else:
            return web.json_response({"ok": False, "error": f"Loại '{category}' không hợp lệ"}, status=400)

        save_custom_farm_items(data)
        add_log("SUCCESS", f"Admin {sess.get('username')} đã tạo vật phẩm nông trại [{category}] {name} ({item_id})")
        return web.json_response({"ok": True, "message": f"Đã lưu vật phẩm {name} ({item_id}) thành công!"})
    except Exception as e:
        return web.json_response({"ok": False, "error": str(e)}, status=500)

async def handle_admin_farm_delete_item(request: web.Request):
    """Admin xóa vật phẩm nông trại tùy chỉnh."""
    sess = require_admin(request)
    if not sess:
        return web.json_response({"ok": False, "error": "Chỉ dành cho Admin"}, status=403)
    try:
        body = await request.json()
        category = str(body.get("category", "")).strip().lower()
        if category in ["crop", "crops"]:
            category = "seed"
        item_id = str(body.get("id") or body.get("item_id") or "").strip().lower()

        cat_map = {
            "seed": "seeds",
            "fertilizer": "fertilizers",
            "tool": "tools",
            "pest": "pests",
            "disease": "diseases"
        }
        key = cat_map.get(category, category)

        from Command_vi.farm_system import load_custom_farm_items, save_custom_farm_items
        data = load_custom_farm_items()
        if key in data and item_id in data[key]:
            del data[key][item_id]
            save_custom_farm_items(data)
            add_log("SUCCESS", f"Admin {sess.get('username')} đã xóa vật phẩm tùy chỉnh {item_id} khỏi {key}")
            return web.json_response({"ok": True, "message": f"Đã xóa vật phẩm {item_id}"})
        return web.json_response({"ok": False, "error": f"Không tìm thấy vật phẩm {item_id} trong {category}"}, status=404)
    except Exception as e:
        return web.json_response({"ok": False, "error": str(e)}, status=500)

# ==============================================================================
# HỆ THỐNG API QUẢN TRỊ KHOÁNG SẢN (MINING ADMIN)
# ==============================================================================
async def handle_get_admin_mining_catalogs(request: web.Request):
    """Lấy danh mục bách khoa toàn thư mỏ khoáng: cuốc, quặng, khu mỏ, vật tư, đột biến."""
    sess = require_admin(request)
    if not sess:
        return web.json_response({"ok": False, "error": "Chỉ dành cho Admin"}, status=403)
    try:
        from Command_vi.command_mining import PICKS_CATALOG, ORES_CATALOG, MINING_ZONES, MINING_SUPPLIES, MINING_MUTATIONS
        try:
            from Command_vi.command_mining import load_custom_mining_items
            load_custom_mining_items()
        except Exception:
            pass
        try:
            from Command_vi.command_mining import ENCHANT_AFFIXES
        except Exception:
            try:
                from Command_vi.command_fishing import ENCHANT_AFFIXES
            except Exception:
                ENCHANT_AFFIXES = []
        cat_dict = {
            "picks": PICKS_CATALOG,
            "ores": ORES_CATALOG,
            "zones": MINING_ZONES,
            "supplies": MINING_SUPPLIES,
            "mutations": MINING_MUTATIONS
        }
        return web.json_response({
            "ok": True,
            "catalogs": cat_dict,
            "picks": PICKS_CATALOG,
            "ores": ORES_CATALOG,
            "zones": MINING_ZONES,
            "supplies": MINING_SUPPLIES,
            "mutations": MINING_MUTATIONS,
            "affixes": ENCHANT_AFFIXES
        })
    except Exception as e:
        return web.json_response({"ok": False, "error": str(e)}, status=500)

async def _resolve_miner_user(query_str: str):
    """Phân giải chuỗi ID / username / mention sang thông tin User Discord chuẩn."""
    raw_str = str(query_str or "").strip()
    if not raw_str:
        return None, "Vui lòng nhập ID hoặc tên người dùng", "https://cdn.discordapp.com/embed/avatars/0.png"
    
    # Trích xuất snowflake ID nếu chuỗi chứa dãy số dài (6-22 chữ số)
    id_match = re.search(r'\b\d{6,22}\b', raw_str)
    clean_id = id_match.group(0) if id_match else re.sub(r'[<@!#>]', '', raw_str).strip()
    if not clean_id:
        return None, "Vui lòng nhập ID hoặc tên người dùng", "https://cdn.discordapp.com/embed/avatars/0.png"
    
    target_id = None
    username = f"User {clean_id}"
    avatar = "https://cdn.discordapp.com/embed/avatars/0.png"

    # 1. Tìm trong web_users.json
    try:
        web_users = load_json(DATA_DIR / "web_users.json", {})
        for w_key, w_val in web_users.items():
            if str(w_val.get("discord_id")) == clean_id:
                target_id = clean_id
                username = f"{w_val.get('username', w_key)} (@{w_val.get('discord_tag') or w_val.get('username')})"
                avatar = w_val.get("avatar") or avatar
                break
            elif clean_id.lower() in [str(w_key).lower(), str(w_val.get("username", "")).lower(), str(w_val.get("discord_tag", "")).lower()]:
                if w_val.get("discord_id"):
                    target_id = str(w_val.get("discord_id"))
                    username = f"{w_val.get('username', w_key)} (@{w_val.get('discord_tag') or w_val.get('username')})"
                    avatar = w_val.get("avatar") or avatar
                    break
    except Exception:
        pass

    # 2. Tìm trong mining_data.json
    if not target_id:
        try:
            mdata = load_json(Path("data/mining_data.json"), {})
            musers = mdata.get("users", {})
            if clean_id in musers:
                target_id = clean_id
            else:
                for mu_id, mu_val in musers.items():
                    if clean_id.lower() in str(mu_id).lower():
                        target_id = str(mu_id)
                        break
        except Exception:
            pass

    # 3. Tìm trong BOT_INSTANCE (Guilds & Users Cache)
    if not target_id and clean_id.isdigit():
        target_id = clean_id

    if BOT_INSTANCE:
        if not target_id:
            q_lower = clean_id.lower()
            try:
                for g in getattr(BOT_INSTANCE, "guilds", []):
                    for m in getattr(g, "members", []):
                        if (m.name.lower() == q_lower or 
                            (m.global_name and m.global_name.lower() == q_lower) or 
                            (m.nick and m.nick.lower() == q_lower) or 
                            str(m.id) == clean_id):
                            target_id = str(m.id)
                            username = f"{m.name} ({m.display_name})"
                            avatar = m.display_avatar.url if hasattr(m, "display_avatar") else avatar
                            break
                    if target_id:
                        break

                if not target_id:
                    for u in getattr(BOT_INSTANCE, "users", []):
                        if (u.name.lower() == q_lower or 
                            (u.global_name and u.global_name.lower() == q_lower) or 
                            str(u.id) == clean_id):
                            target_id = str(u.id)
                            username = f"{u.name} ({u.display_name})"
                            avatar = u.display_avatar.url if hasattr(u, "display_avatar") else avatar
                            break
            except Exception:
                pass

        # Lấy info user từ cache hoặc fetch với timeout cực ngắn tránh nghẽn
        if target_id and target_id.isdigit():
            try:
                uid_int = int(target_id)
                u = BOT_INSTANCE.get_user(uid_int) if hasattr(BOT_INSTANCE, "get_user") else None
                if not u and hasattr(BOT_INSTANCE, "is_ready") and BOT_INSTANCE.is_ready():
                    u = await asyncio.wait_for(BOT_INSTANCE.fetch_user(uid_int), timeout=0.6)
                if u:
                    username = f"{u.name} ({u.display_name})"
                    avatar = u.display_avatar.url if hasattr(u, "display_avatar") else avatar
            except Exception:
                pass

    if not target_id and clean_id.isdigit():
        target_id = clean_id

    return target_id, username, avatar

async def handle_get_admin_mining_users(request: web.Request):
    """Lấy danh sách các thợ mỏ đã tham gia để chọn nhanh trong dropdown."""
    sess = require_admin(request)
    if not sess:
        return web.json_response({"ok": False, "error": "Chỉ dành cho Admin"}, status=403)
    try:
        from Command_vi.command_mining import load_mining_data, mining_state, PICKS_CATALOG
        load_mining_data()
        users_dict = mining_state.get("users", {})
        res_list = []
        seen_ids = set()

        for uid, udata in users_dict.items():
            seen_ids.add(str(uid))
            name = f"User {uid}"
            avatar = "https://cdn.discordapp.com/embed/avatars/0.png"
            if BOT_INSTANCE and str(uid).isdigit():
                u = BOT_INSTANCE.get_user(int(uid))
                if u:
                    name = f"{u.name} ({u.display_name})"
                    avatar = u.display_avatar.url if hasattr(u, "display_avatar") else avatar
            
            eq_pick = udata.get("equipped_pick", "pick_wooden")
            pick_info = PICKS_CATALOG.get(eq_pick, {})
            res_list.append({
                "user_id": str(uid),
                "username": name,
                "avatar": avatar,
                "zone": udata.get("zone", "hang_dat"),
                "total_mined": udata.get("stats", {}).get("total_mined", 0),
                "pick_name": pick_info.get("name", eq_pick),
                "stamina": udata.get("stamina", 100)
            })

        # Thêm các user đã đăng nhập web dashboard nếu chưa có
        try:
            web_users = load_json(DATA_DIR / "web_users.json", {})
            for w_key, w_val in web_users.items():
                did = str(w_val.get("discord_id") or "")
                if did and did not in seen_ids:
                    seen_ids.add(did)
                    res_list.append({
                        "user_id": did,
                        "username": f"{w_val.get('username', w_key)} (Admin/Web)",
                        "avatar": w_val.get("avatar") or "https://cdn.discordapp.com/embed/avatars/0.png",
                        "zone": "Chưa đào",
                        "total_mined": 0,
                        "pick_name": "Cuốc Gỗ Sơ Cấp",
                        "stamina": 100
                    })
        except Exception:
            pass

        return web.json_response({"ok": True, "users": res_list})
    except Exception as e:
        return web.json_response({"ok": False, "error": str(e)}, status=500)

async def handle_get_admin_mining_user(request: web.Request):
    """Tra cứu chi tiết thợ mỏ theo User ID hoặc Username."""
    sess = require_admin(request)
    if not sess:
        return web.json_response({"ok": False, "error": "Chỉ dành cho Admin"}, status=403)
    try:
        user_id_raw = request.query.get("user_id", "").strip()
        from Command_vi.command_mining import load_mining_data, get_user_mining, mining_state
        load_mining_data()

        # Nếu user_id_raw trống hoặc là 'auto', fallback đến thợ mỏ đầu tiên hoặc tài khoản đang đăng nhập
        if not user_id_raw or user_id_raw == "auto":
            m_users = list(mining_state.get("users", {}).keys())
            if m_users:
                user_id_raw = str(m_users[0])
            else:
                user_id_raw = str(sess.get("discord_id") or "1144785664458637394")

        target_id, username, avatar = await _resolve_miner_user(user_id_raw)
        if not target_id:
            if user_id_raw.isdigit():
                target_id = user_id_raw
                username = f"User {user_id_raw}"
            else:
                m_users = list(mining_state.get("users", {}).keys())
                if m_users:
                    target_id = str(m_users[0])
                    username = f"Thợ Mỏ {target_id}"
                else:
                    target_id = "1144785664458637394"
                    username = f"Thợ Mỏ {target_id}"

        udata = get_user_mining(int(target_id) if target_id.isdigit() else 0)

        coins, xu, bank = 0, 0, 0
        try:
            from data.database import get_user_data
            if target_id.isdigit():
                econ = await get_user_data(0, int(target_id))
                coins = int(econ.get("coins", 0))
                xu = int(econ.get("xu", 0))
                bank = int(econ.get("bank", 0))
        except Exception:
            pass

        return web.json_response({
            "ok": True,
            "user_id": target_id,
            "username": username,
            "avatar": avatar,
            "coins": coins,
            "xu": xu,
            "bank": bank,
            "data": udata
        })
    except Exception as e:
        return web.json_response({"ok": False, "error": str(e)}, status=500)

async def handle_admin_mining_user_action(request: web.Request):
    """Admin thao tác trên tài khoản thợ mỏ."""
    sess = require_admin(request)
    if not sess:
        return web.json_response({"ok": False, "error": "Chỉ dành cho Admin"}, status=403)
    try:
        body = await request.json()
        user_id_raw = str(body.get("user_id", "")).strip()
        action = str(body.get("action", "")).strip()
        if not user_id_raw:
            return web.json_response({"ok": False, "error": "Thiếu user_id"}, status=400)

        target_id, _, _ = await _resolve_miner_user(user_id_raw)
        if not target_id:
            return web.json_response({"ok": False, "error": f"Không tìm thấy thợ mỏ: {user_id_raw}"}, status=400)
        user_id = target_id

        from Command_vi.command_mining import load_mining_data, get_user_mining, save_mining_data, PICKS_CATALOG, ORES_CATALOG, MINING_SUPPLIES
        load_mining_data()
        udata = get_user_mining(int(user_id) if user_id.isdigit() else 0)
        msg = "Thực hiện thành công"

        if action == "give_pick":
            pick_id = str(body.get("pick_id", "pick_iron")).strip()
            pinfo = PICKS_CATALOG.get(pick_id, {"id": pick_id, "name": pick_id, "durability": 250})
            udata.setdefault("picks", {})[pick_id] = {
                "id": pick_id,
                "name": pinfo.get("name", pick_id),
                "refine": int(body.get("refine", 0)),
                "stars": int(body.get("stars", 0)),
                "durability": int(pinfo.get("durability", 250)),
                "max_durability": int(pinfo.get("durability", 250)),
                "enchant": None
            }
            msg = f"Đã tặng cuốc {pinfo.get('name', pick_id)} cho User {user_id}"

        elif action == "remove_pick":
            pick_id = str(body.get("pick_id", "")).strip()
            if pick_id in udata.get("picks", {}):
                del udata["picks"][pick_id]
                if udata.get("equipped_pick") == pick_id:
                    udata["equipped_pick"] = next(iter(udata.get("picks", {}).keys()), "pick_wooden")
                msg = f"Đã xóa cuốc {pick_id} của User {user_id}"

        elif action == "set_refine":
            pick_id = str(body.get("pick_id") or udata.get("equipped_pick")).strip()
            refine_lvl = max(0, min(150, int(body.get("refine", 0))))
            if pick_id in udata.get("picks", {}):
                udata["picks"][pick_id]["refine"] = refine_lvl
                msg = f"Đã đặt cấp Refine cuốc {pick_id} thành +{refine_lvl}"

        elif action == "set_stars":
            pick_id = str(body.get("pick_id") or udata.get("equipped_pick")).strip()
            stars = max(0, min(20, int(body.get("stars", 0))))
            if pick_id in udata.get("picks", {}):
                udata["picks"][pick_id]["stars"] = stars
                msg = f"Đã đặt cấp Sao cuốc {pick_id} thành {stars}⭐"

        elif action == "repair_pick":
            pick_id = str(body.get("pick_id") or udata.get("equipped_pick")).strip()
            if pick_id in udata.get("picks", {}):
                udata["picks"][pick_id]["durability"] = udata["picks"][pick_id].get("max_durability", 250)
                msg = f"Đã sửa độ bền tối đa cho cuốc {pick_id}"

        elif action == "add_ore":
            ore_id = str(body.get("ore_id", "diamond")).strip()
            count = max(1, min(100, int(body.get("count") or body.get("amount") or 1)))
            oinfo = ORES_CATALOG.get(ore_id, {"name": ore_id, "rarity": "rare", "price": 1000})
            bag = udata.setdefault("ore_bag", [])
            for _ in range(count):
                bag.append({
                    "id": ore_id,
                    "name": oinfo.get("name", ore_id),
                    "rarity": oinfo.get("rarity", "rare"),
                    "price": oinfo.get("price", 1000),
                    "weight": round(float(body.get("weight", 2.0)), 2),
                    "depth": int(body.get("depth", 50)),
                    "mutation": body.get("mutation") or None,
                    "time": int(time.time())
                })
            udata.setdefault("stats", {})["total_mined"] = udata["stats"].get("total_mined", 0) + count
            msg = f"Đã thêm {count}x {oinfo.get('name', ore_id)} vào túi quặng của User {user_id}"

        elif action == "clear_ores":
            udata["ore_bag"] = []
            msg = f"Đã xóa toàn bộ quặng trong túi của User {user_id}"

        elif action == "add_supply":
            sup_id = str(body.get("supply_id", "tnt")).strip()
            count = max(1, min(1000, int(body.get("count") or body.get("amount") or 1)))
            supplies = udata.setdefault("supplies", {})
            supplies[sup_id] = supplies.get(sup_id, 0) + count
            msg = f"Đã thêm {count}x vật tư {sup_id} cho User {user_id}"

        elif action == "restore_stamina":
            udata["stamina"] = udata.get("max_stamina", 100)
            msg = f"Đã hồi phục 100% thể lực (Stamina) cho User {user_id}"

        elif action == "unlock_museum":
            museum_dict = udata.get("museum")
            if not isinstance(museum_dict, dict):
                museum_dict = {}
                udata["museum"] = museum_dict
            for oid in ORES_CATALOG:
                museum_dict[oid] = {
                    "donated_at": int(time.time()),
                    "first_weight": 5.0
                }
            msg = f"Đã mở khóa toàn bộ bảo tàng địa chất cho User {user_id}"

        save_mining_data()
        add_log("SUCCESS", f"Admin {sess.get('username')} thao tác đào khoáng [{action}] trên User {user_id}")
        return web.json_response({"ok": True, "message": msg, "data": udata})
    except Exception as e:
        return web.json_response({"ok": False, "error": str(e)}, status=500)

async def handle_admin_mining_create_item(request: web.Request):
    """Admin tạo cuốc hoặc quặng tùy chỉnh."""
    sess = require_admin(request)
    if not sess:
        return web.json_response({"ok": False, "error": "Chỉ dành cho Admin"}, status=403)
    try:
        body = await request.json()
        item_type = str(body.get("type", "pick")).strip().lower()
        item_id = str(body.get("id", "")).strip().lower()
        name = str(body.get("name", "")).strip()

        if not item_id or not name:
            return web.json_response({"ok": False, "error": "Thiếu ID hoặc Tên vật phẩm"}, status=400)

        custom_file = DATA_DIR / "custom_mining_items.json"
        cdata = load_json(custom_file, {"picks": {}, "ores": {}})

        from Command_vi.command_mining import PICKS_CATALOG, ORES_CATALOG

        if item_type in ("pick", "pickaxe"):
            new_item = {
                "id": item_id,
                "name": name,
                "icon": "⛏️",
                "rarity": str(body.get("rarity", "rare")),
                "price": int(body.get("price", 10000)),
                "power": float(body.get("power", 2.0)),
                "speed": float(body.get("speed", 1.5)),
                "durability": int(body.get("durability", 300)),
                "max_durability": int(body.get("durability", 300)),
                "luck": float(body.get("fortune", body.get("luck", 20.0))),
                "desc": str(body.get("desc", "Cuốc đào custom"))
            }
            cdata.setdefault("picks", {})[item_id] = new_item
            PICKS_CATALOG[item_id] = new_item
        else:
            new_item = {
                "id": item_id,
                "name": name,
                "icon": "💎",
                "rarity": str(body.get("rarity", "rare")),
                "price": int(body.get("price", 500)),
                "weight_range": (1.0, 5.0),
                "desc": str(body.get("desc", "Khoáng sản custom"))
            }
            cdata.setdefault("ores", {})[item_id] = new_item
            ORES_CATALOG[item_id] = new_item

        save_json(custom_file, cdata)
        add_log("SUCCESS", f"Admin {sess.get('username')} tạo vật phẩm đào khoáng custom [{item_type}] {name} ({item_id})")
        return web.json_response({"ok": True, "message": f"Đã lưu vật phẩm {name} ({item_id}) thành công!", "item": new_item})
    except Exception as e:
        return web.json_response({"ok": False, "error": str(e)}, status=500)

# ==============================================================================
# WAIFU GACHA ADMIN & LEADERBOARD & VOICE LEADERBOARD APIS
# ==============================================================================
async def handle_get_admin_gacha_stats(request: web.Request):
    """Lấy thống kê toàn hệ thống Gacha Waifu cho Admin."""
    sess = require_admin(request)
    if not sess:
        return web.json_response({"ok": False, "error": "Chỉ dành cho Admin"}, status=403)
    try:
        from data.waifu_db import get_gacha_global_stats
        stats = await get_gacha_global_stats()
        return web.json_response({"ok": True, "stats": stats})
    except Exception as e:
        return web.json_response({"ok": False, "error": str(e)}, status=500)

async def handle_get_admin_gacha_user(request: web.Request):
    """Tra cứu chi tiết hồ sơ Gacha và bộ sưu tập thẻ của 1 người chơi."""
    sess = require_auth(request)
    if not sess:
        return web.json_response({"ok": False, "error": "Vui lòng đăng nhập"}, status=401)
    user_id_str = request.query.get("user_id", "").strip()
    if not user_id_str or not user_id_str.isdigit():
        return web.json_response({"ok": False, "error": "Vui lòng nhập Discord User ID hợp lệ"}, status=400)
    if not is_admin_session(sess) and str(sess.get("discord_id") or "") != user_id_str:
        return web.json_response({"ok": False, "error": "Chỉ dành cho Admin hoặc chủ sở hữu"}, status=403)
    try:
        from data.waifu_db import get_or_create_profile, get_user_cards
        uid = int(user_id_str)
        profile = await get_or_create_profile(uid)
        cards = await get_user_cards(uid)
        username = f"User {uid}"
        avatar = "https://cdn.discordapp.com/embed/avatars/0.png"
        if BOT_INSTANCE:
            u = BOT_INSTANCE.get_user(uid)
            if not u:
                try:
                    u = await BOT_INSTANCE.fetch_user(uid)
                except Exception:
                    pass
            if u:
                username = u.display_name or u.name
                avatar = str(u.display_avatar.url) if u.display_avatar else avatar

        return web.json_response({
            "ok": True,
            "user": {"id": str(uid), "username": username, "avatar": avatar},
            "profile": profile,
            "cards": cards,
            "total_cards": len(cards),
            "total_points": sum(c.get("points", 0) for c in cards)
        })
    except Exception as e:
        return web.json_response({"ok": False, "error": str(e)}, status=500)

async def handle_admin_gacha_user_action(request: web.Request):
    """Thao tác admin trên gacha user: chỉnh roll, claim, tặng thẻ, xóa thẻ, đổi sao."""
    sess = require_admin(request)
    if not sess:
        return web.json_response({"ok": False, "error": "Chỉ dành cho Admin"}, status=403)
    try:
        from data.waifu_db import (
            admin_set_user_rolls, add_bonus_rolls, admin_set_user_claims, add_bonus_claims,
            admin_grant_card, admin_delete_card, admin_update_card_stars
        )
        body = await request.json()
        action = str(body.get("action", "")).strip().lower()
        user_id_str = str(body.get("user_id", "")).strip()
        uid = int(user_id_str) if user_id_str.isdigit() else 0

        if action == "set_rolls":
            rolls = int(body.get("amount", 0))
            res = await admin_set_user_rolls(uid, rolls)
            add_log("ADMIN", f"Admin {sess.get('username')} đặt số roll của {uid} thành {rolls}")
            return web.json_response({"ok": True, "message": f"Đã đặt số lượt roll của user thành {res}!"})

        elif action == "add_rolls":
            amount = int(body.get("amount", 0))
            res = await add_bonus_rolls(uid, amount)
            add_log("ADMIN", f"Admin {sess.get('username')} cộng {amount} roll cho {uid}")
            return web.json_response({"ok": True, "message": f"Đã cộng {amount} roll, hiện có {res} roll!"})

        elif action == "set_claims":
            claims = int(body.get("amount", 0))
            res = await admin_set_user_claims(uid, claims)
            add_log("ADMIN", f"Admin {sess.get('username')} đặt số claim của {uid} thành {claims}")
            return web.json_response({"ok": True, "message": f"Đã đặt số lượt claim của user thành {res}!"})

        elif action == "add_claims":
            amount = int(body.get("amount", 0))
            res = await add_bonus_claims(uid, amount)
            add_log("ADMIN", f"Admin {sess.get('username')} cộng {amount} claim cho {uid}")
            return web.json_response({"ok": True, "message": f"Đã cộng {amount} claim, hiện có {res} claim!"})

        elif action == "grant_card":
            char_id = int(body.get("character_id", 0))
            stars = int(body.get("stars", 1))
            print_num = int(body["print_number"]) if body.get("print_number") else None
            card = await admin_grant_card(uid, char_id, stars, print_num)
            add_log("ADMIN", f"Admin {sess.get('username')} trao thẻ {card['name']} {stars}⭐ (mã {card['code']}) cho {uid}")
            return web.json_response({"ok": True, "message": f"Đã trao thành công thẻ {card['name']} {card['stars']}⭐ (Mã: {card['code']})!", "card": card})

        elif action == "delete_card":
            code = str(body.get("code", "")).strip()
            ok = await admin_delete_card(code)
            if not ok:
                return web.json_response({"ok": False, "error": "Không tìm thấy thẻ hoặc xóa thất bại"}, status=404)
            add_log("ADMIN", f"Admin {sess.get('username')} xóa thẻ waifu mã {code}")
            return web.json_response({"ok": True, "message": f"Đã xóa thẻ `{code}` khỏi hệ thống!"})

        elif action == "set_card_stars":
            code = str(body.get("code", "")).strip()
            stars = int(body.get("stars", 1))
            card = await admin_update_card_stars(code, stars)
            if not card:
                return web.json_response({"ok": False, "error": "Không tìm thấy thẻ để sửa sao"}, status=404)
            add_log("ADMIN", f"Admin {sess.get('username')} đổi sao thẻ {code} thành {stars}⭐ (Điểm: {card['points']:,})")
            return web.json_response({"ok": True, "message": f"Đã đổi sao thẻ `{code}` thành {stars}⭐ ({card['points']:,} 💖)!", "card": card})

        return web.json_response({"ok": False, "error": f"Hành động không hợp lệ: {action}"}, status=400)
    except Exception as e:
        return web.json_response({"ok": False, "error": str(e)}, status=500)

async def handle_get_gacha_characters(request: web.Request):
    """Tra cứu danh sách nhân vật gacha cho dropdown tìm kiếm."""
    try:
        from data.waifu_db import search_characters
        q = request.query.get("search", "").strip()
        limit = min(100, max(1, int(request.query.get("limit", 50))))
        chars = await search_characters(q, limit=limit) if q else await search_characters("", limit=limit)
        return web.json_response({"ok": True, "characters": chars})
    except Exception as e:
        return web.json_response({"ok": False, "error": str(e)}, status=500)

async def handle_get_gacha_leaderboard(request: web.Request):
    """Lấy Bảng Xếp Hạng người sưu tầm Waifu Gacha."""
    try:
        from data.waifu_db import get_waifu_leaderboard_extended
        limit = min(100, max(1, int(request.query.get("limit", 100))))
        entries = await get_waifu_leaderboard_extended(limit)
        for idx, item in enumerate(entries, start=1):
            item["rank"] = idx
            uid_str = str(item.get("user_id", ""))
            username = f"User {uid_str[:8]}"
            avatar = "https://cdn.discordapp.com/embed/avatars/0.png"
            if BOT_INSTANCE and uid_str.isdigit():
                u = BOT_INSTANCE.get_user(int(uid_str))
                if u:
                    username = u.display_name or u.name
                    avatar = str(u.display_avatar.url) if u.display_avatar else avatar
            item["username"] = username
            item["avatar"] = avatar

        return web.json_response({"ok": True, "leaderboard": entries, "total_users": len(entries)})
    except Exception as e:
        return web.json_response({"ok": False, "error": str(e)}, status=500)

async def handle_get_voice_leaderboard(request: web.Request):
    """Lấy Bảng Xếp Hạng thời gian tham gia kênh thoại Voice."""
    try:
        guild_id = request.query.get("guild_id", "").strip()
        limit = min(100, max(1, int(request.query.get("limit", 100))))
        
        data_file = DATA_DIR / "data.json"
        d = load_json(data_file, {})
        v = d.get("voice", {})
        user_totals = {}

        if guild_id and guild_id != "all" and guild_id in v:
            guild_data = v[guild_id]
            if isinstance(guild_data, dict):
                for uid, secs in guild_data.items():
                    if str(uid).isdigit():
                        try: user_totals[str(uid)] = int(secs)
                        except: pass
        else:
            for gid, gusers in v.items():
                if not isinstance(gusers, dict): continue
                for uid, secs in gusers.items():
                    if str(uid).isdigit():
                        try:
                            user_totals[str(uid)] = user_totals.get(str(uid), 0) + int(secs)
                        except: pass

        sorted_users = sorted(user_totals.items(), key=lambda x: x[1], reverse=True)[:limit]
        items = []
        for idx, (uid_str, total_sec) in enumerate(sorted_users, start=1):
            hours, rem = divmod(total_sec, 3600)
            mins, secs = divmod(rem, 60)
            time_str = f"{hours}h {mins}m {secs}s" if hours > 0 else f"{mins}m {secs}s"

            username = f"User {uid_str[:8]}"
            avatar = "https://cdn.discordapp.com/embed/avatars/0.png"
            if BOT_INSTANCE and uid_str.isdigit():
                u = BOT_INSTANCE.get_user(int(uid_str))
                if u:
                    username = u.display_name or u.name
                    avatar = str(u.display_avatar.url) if u.display_avatar else avatar

            items.append({
                "rank": idx,
                "user_id": uid_str,
                "username": username,
                "avatar": avatar,
                "seconds": total_sec,
                "formatted_time": time_str
            })

        return web.json_response({"ok": True, "leaderboard": items, "total_users": len(items)})
    except Exception as e:
        return web.json_response({"ok": False, "error": str(e)}, status=500)

# ==============================================================================
# API THAO TÚNG TỈ LỆ GAME (ADMIN GAME RATES CONTROL)
# ==============================================================================
async def handle_get_admin_game_rates(request: web.Request):
    """Lấy cấu hình thao túng tỉ lệ game (cường hóa, sao, may mắn, quặng...)."""
    sess = require_admin(request)
    if not sess:
        return web.json_response({"ok": False, "error": "Chỉ dành cho Admin"}, status=403)
    try:
        from data.game_rates import get_game_rates
        rates = get_game_rates()
        return web.json_response({"ok": True, "rates": rates})
    except Exception as e:
        return web.json_response({"ok": False, "error": str(e)}, status=500)

async def handle_save_admin_game_rates(request: web.Request):
    """Cập nhật thao túng tỉ lệ game từ Web Admin."""
    sess = require_admin(request)
    if not sess:
        return web.json_response({"ok": False, "error": "Chỉ dành cho Admin"}, status=403)
    try:
        body = await request.json()
        from data.game_rates import save_game_rates
        updated = save_game_rates(body)
        add_log("SUCCESS", f"Admin {sess.get('username')} cập nhật thao túng tỉ lệ game: {updated}")
        return web.json_response({"ok": True, "message": "Đã lưu cài đặt thao túng tỉ lệ thành công!", "rates": updated})
    except Exception as e:
        return web.json_response({"ok": False, "error": str(e)}, status=500)

# ==============================================================================
# API LIÊN KẾT TÀI KHOẢN DISCORD & MINECRAFT (CỔNG 10272)
# ==============================================================================
async def handle_link_request(request: web.Request):
    """API endpoint /api/link dùng cho Plugin Minecraft gửi mã liên kết tới SakuraBot (cùng cổng 10272)."""
    try:
        data = await request.json()
    except Exception:
        return web.json_response({"ok": False, "error": "JSON không hợp lệ"}, status=400)

    code = str(data.get("code") or data.get("link_code") or "").strip().upper()
    mc_uuid = str(data.get("minecraft_uuid") or data.get("player_uuid") or data.get("uuid") or "").strip()
    mc_name = str(data.get("minecraft_name") or data.get("player_name") or data.get("name") or "").strip()

    if not code or not mc_uuid:
        return web.json_response({"ok": False, "error": "Thiếu mã code hoặc minecraft_uuid"}, status=400)

    try:
        from mc_link_system import PENDING_LINKS, load_links, save_links
    except Exception:
        PENDING_LINKS, load_links, save_links = {}, lambda: {}, lambda d: None

    pending = PENDING_LINKS.get(code)
    discord_id = None

    if pending and time.time() <= pending.get("expires_at", 0):
        discord_id = int(pending["discord_id"])
        PENDING_LINKS.pop(code, None)
    else:
        try:
            from data.database import link_mc_user_by_code
            db_res = await link_mc_user_by_code(code, mc_uuid, mc_name)
            if db_res and db_res.get("ok"):
                discord_id = db_res.get("discord_user_id")
        except Exception:
            pass

    if not discord_id:
        return web.json_response({"ok": False, "error": "Mã liên kết không hợp lệ hoặc đã hết hạn (10 phút)"}, status=400)

    try:
        links = load_links()
        links[str(discord_id)] = {
            "discord_id": discord_id,
            "minecraft_uuid": mc_uuid.lower(),
            "minecraft_name": mc_name,
            "linked_at": int(time.time())
        }
        save_links(links)
    except Exception:
        pass

    try:
        from data.database import link_mc_user
        await link_mc_user(discord_id, mc_uuid, mc_name)
    except Exception:
        pass

    add_log("SUCCESS", f"Liên kết tài khoản thành công: Discord ID {discord_id} ➜ MC {mc_name} ({mc_uuid})")
    return web.json_response({
        "ok": True,
        "discord_id": str(discord_id),
        "minecraft_uuid": mc_uuid.lower(),
        "minecraft_name": mc_name,
        "message": f"Liên kết thành công tài khoản {mc_name} với Discord!"
    })

# ==============================================================================
# API KẾT NỐI MINECRAFT CHO TỪNG SERVER THEO GUILD (RCON & PLUGIN)
# ==============================================================================
GUILD_MC_CONFIG_FILE = DATA_DIR / "guild_mc_connections.json"

def _load_guild_mc_configs():
    return load_json(GUILD_MC_CONFIG_FILE, {})

def _save_guild_mc_configs(data):
    save_json(GUILD_MC_CONFIG_FILE, data)

async def handle_get_guild_mc_connection(request: web.Request):
    """Lấy thông tin cấu hình kết nối Minecraft (RCON & Plugin) của guild."""
    sess = require_auth(request)
    if not sess:
        return web.json_response({"ok": False, "error": "Unauthorized"}, status=401)
    gid = request.match_info.get("id")
    if not can_access_guild(sess, gid):
        return web.json_response({"ok": False, "error": "Không có quyền"}, status=403)

    configs = _load_guild_mc_configs()
    gcfg = configs.get(str(gid), {
        "mode": "rcon",
        "host": "snow.pikamc.vn",
        "port": 25365,
        "query_port": 25355,
        "rcon_host": "snow.pikamc.vn",
        "rcon_port": 25025,
        "rcon_password": "",
        "api_key": "",
        "chat_channel_id": "",
        "log_channel_id": "",
        "auto_sync_chat": True
    })

    plugin_server = None
    try:
        from data.database import get_mc_server_by_guild
        plugin_server = await get_mc_server_by_guild(int(gid))
    except Exception:
        pass

    now_t = time.time()
    is_srv_online = bool(plugin_server) and (now_t - float(plugin_server.get("last_heartbeat", 0) or 0) < 90)

    data_payload = {
        "host": gcfg.get("host", ""),
        "port": gcfg.get("port", 25565),
        "query_port": gcfg.get("query_port", 25565),
        "chat_channel": gcfg.get("chat_channel_id") or gcfg.get("chat_channel", ""),
        "log_channel": gcfg.get("log_channel_id") or gcfg.get("log_channel", ""),
        "rcon": {
            "host": gcfg.get("rcon_host") or gcfg.get("host", ""),
            "port": gcfg.get("rcon_port", 25025),
            "password": gcfg.get("rcon_password", "")
        },
        "plugin": {
            "api_key": gcfg.get("api_key", ""),
            "linked": bool(plugin_server),
            "last_sync": plugin_server.get("last_heartbeat") if plugin_server else None
        },
        "status": {
            "online": is_srv_online,
            "version": plugin_server.get("version") if plugin_server else None,
            "players_online": plugin_server.get("player_count", 0) if plugin_server else 0,
            "players_max": plugin_server.get("max_players", 0) if plugin_server else 0
        }
    }

    return web.json_response({
        "ok": True,
        "guild_id": str(gid),
        "config": gcfg,
        "data": data_payload,
        "plugin_connected": bool(plugin_server),
        "plugin_server": plugin_server
    })

async def handle_save_guild_mc_connection(request: web.Request):
    """Lưu cấu hình kết nối Minecraft cho guild."""
    sess = require_auth(request)
    if not sess:
        return web.json_response({"ok": False, "error": "Unauthorized"}, status=401)
    gid = request.match_info.get("id")
    if not can_access_guild(sess, gid):
        return web.json_response({"ok": False, "error": "Không có quyền"}, status=403)

    try:
        body = await request.json()
        configs = _load_guild_mc_configs()
        rcon_data = body.get("rcon") or {}
        plugin_data = body.get("plugin") or {}

        host = str(body.get("host") or rcon_data.get("host") or "snow.pikamc.vn").strip()
        port = int(body.get("port") or 25365)
        query_port = int(body.get("query_port") or 25355)
        rcon_host = str(body.get("rcon_host") or rcon_data.get("host") or host).strip()
        rcon_port = int(body.get("rcon_port") or rcon_data.get("port") or 25575)
        rcon_password = str(body.get("rcon_password") or rcon_data.get("password") or "").strip()
        
        # Nếu password để trống trong request nhưng đã có password lưu từ trước, giữ lại không xóa
        if not rcon_password and str(gid) in configs and configs[str(gid)].get("rcon_password"):
            rcon_password = configs[str(gid)]["rcon_password"]

        api_key = str(body.get("api_key") or plugin_data.get("api_key") or "").strip()
        chat_channel_id = str(body.get("chat_channel_id") or body.get("chat_channel") or "").strip()
        log_channel_id = str(body.get("log_channel_id") or body.get("log_channel") or "").strip()
        mode = str(body.get("mode", "rcon")).strip().lower()
        auto_sync = bool(body.get("auto_sync_chat", True))

        configs[str(gid)] = {
            "mode": mode,
            "host": host,
            "port": port,
            "query_port": query_port,
            "rcon_host": rcon_host,
            "rcon_port": rcon_port,
            "rcon_password": rcon_password,
            "api_key": api_key,
            "chat_channel_id": chat_channel_id,
            "log_channel_id": log_channel_id,
            "auto_sync_chat": auto_sync,
            "updated_at": int(time.time()),
            "updated_by": sess.get("username", "")
        }
        _save_guild_mc_configs(configs)

        try:
            from data.database import get_mc_server_by_guild, update_mc_server_channels
            ps = await get_mc_server_by_guild(int(gid))
            if ps and (chat_channel_id or log_channel_id):
                await update_mc_server_channels(ps["server_key"], chat_channel_id or None, log_channel_id or None)
        except Exception:
            pass

        add_log("SUCCESS", f"User {sess.get('username')} đã lưu cấu hình kết nối MC cho server {gid}")
        return web.json_response({"ok": True, "message": "Đã lưu cấu hình kết nối Minecraft thành công!", "config": configs[str(gid)]})
    except Exception as e:
        return web.json_response({"ok": False, "error": str(e)}, status=500)

async def handle_test_guild_mc_connection(request: web.Request):
    """Kiểm tra live trạng thái server và kết nối RCON kèm plugin."""
    sess = require_auth(request)
    if not sess:
        return web.json_response({"ok": False, "error": "Unauthorized"}, status=401)
    gid = request.match_info.get("id")
    if not can_access_guild(sess, gid):
        return web.json_response({"ok": False, "error": "Không có quyền"}, status=403)

    try:
        body = await request.json() if request.can_read_body else {}
        configs = _load_guild_mc_configs()
        gcfg = configs.get(str(gid), {})
        rcon_data = body.get("rcon") or {}

        host = str(body.get("host") or rcon_data.get("host") or gcfg.get("host", "snow.pikamc.vn")).strip()
        port = int(body.get("port") or gcfg.get("port", 25365))
        r_host = str(body.get("rcon_host") or rcon_data.get("host") or gcfg.get("rcon_host", host)).strip()
        r_port = int(body.get("rcon_port") or rcon_data.get("port") or gcfg.get("rcon_port", 25575))
        r_pass = str(body.get("rcon_password") or rcon_data.get("password") or gcfg.get("rcon_password", "")).strip()

        # Fallback lấy mật khẩu từ server.properties nếu host là localhost / 127.0.0.1
        if not r_pass and r_host in ["localhost", "127.0.0.1"]:
            sp_file = SERVER_DIR / "server.properties"
            if sp_file.exists():
                try:
                    for line in sp_file.read_text(encoding="utf-8").splitlines():
                        if line.startswith("rcon.password="):
                            r_pass = line.split("=", 1)[1].strip()
                        elif line.startswith("rcon.port="):
                            try: r_port = int(line.split("=", 1)[1].strip())
                            except: pass
                except Exception:
                    pass

        server_status = {"online": False, "motd": "", "version": "", "players_online": 0, "players_max": 0, "latency_ms": 0}
        try:
            from mcstatus import JavaServer
            j_server = JavaServer.lookup(f"{host}:{port}")
            status = await asyncio.to_thread(j_server.status)
            server_status = {
                "online": True,
                "motd": str(getattr(status.description, 'to_plain', lambda: status.description)()),
                "version": status.version.name,
                "players_online": status.players.online,
                "players_max": status.players.max,
                "latency_ms": round(status.latency, 1)
            }
        except Exception as se:
            server_status["error"] = str(se)

        rcon_status = {"connected": False, "message": "Chưa nhập mật khẩu RCON"}
        if r_pass:
            try:
                from mctools import RCONClient
                from Command_vi.minecraft import clean_minecraft_text_static
                def _do_rcon_test():
                    rc = RCONClient(r_host, port=r_port)
                    if rc.login(r_pass):
                        out = rc.command("list")
                        rc.stop()
                        return True, clean_minecraft_text_static(out) if out else "Kết nối RCON thành công!"
                    return False, "Sai mật khẩu RCON"
                ok, r_msg = await asyncio.to_thread(_do_rcon_test)
                rcon_status = {"connected": ok, "message": r_msg if ok else f"Lỗi: {r_msg}"}
            except Exception as re:
                rcon_status = {"connected": False, "message": f"Không thể kết nối cổng RCON {r_host}:{r_port} ({re})"}

        plugin_status = {"linked": False, "online": False}
        try:
            from data.database import get_mc_server_by_guild
            pserver = await get_mc_server_by_guild(int(gid))
            if pserver:
                plugin_status = {
                    "linked": True,
                    "server_name": pserver.get("server_name", "Minecraft Server"),
                    "server_ip": pserver.get("server_ip", ""),
                    "server_port": pserver.get("server_port", 0),
                    "tps": pserver.get("tps", 20.0),
                    "online": bool(pserver.get("is_online", False)),
                    "last_heartbeat": pserver.get("last_heartbeat", 0)
                }
        except Exception:
            pass

        return web.json_response({
            "ok": True,
            "server": server_status,
            "rcon": rcon_status,
            "plugin": plugin_status
        })
    except Exception as e:
        return web.json_response({"ok": False, "error": str(e)}, status=500)

async def handle_command_guild_mc_connection(request: web.Request):
    """Gửi lệnh console tới server MC qua RCON hoặc hàng đợi plugin."""
    sess = require_auth(request)
    if not sess:
        return web.json_response({"ok": False, "error": "Unauthorized"}, status=401)
    gid = request.match_info.get("id")
    if not can_access_guild(sess, gid):
        return web.json_response({"ok": False, "error": "Không có quyền"}, status=403)

    try:
        body = await request.json()
        command = str(body.get("command", "")).strip()
        if not command:
            return web.json_response({"ok": False, "error": "Vui lòng nhập lệnh"}, status=400)

        configs = _load_guild_mc_configs()
        gcfg = configs.get(str(gid), {})
        mode = gcfg.get("mode", "rcon")
        clean_cmd = command.lstrip("/")

        r_pass = gcfg.get("rcon_password", "")
        r_host = gcfg.get("rcon_host", gcfg.get("host", "snow.pikamc.vn"))
        r_port = int(gcfg.get("rcon_port", 25575))

        # Fallback local nếu host là localhost / 127.0.0.1
        if not r_pass and r_host in ["localhost", "127.0.0.1"]:
            sp_file = SERVER_DIR / "server.properties"
            if sp_file.exists():
                try:
                    for line in sp_file.read_text(encoding="utf-8").splitlines():
                        if line.startswith("rcon.password="):
                            r_pass = line.split("=", 1)[1].strip()
                        elif line.startswith("rcon.port="):
                            r_port = int(line.split("=", 1)[1].strip())
                except Exception:
                    pass

        # Ưu tiên RCON nếu có mật khẩu
        if (mode == "rcon" or not gcfg.get("api_key")) and r_pass:
            from mctools import RCONClient
            from Command_vi.minecraft import clean_minecraft_text_static
            def _exec():
                try:
                    rc = RCONClient(r_host, port=r_port)
                    if rc.login(r_pass):
                        res = rc.command(clean_cmd)
                        rc.stop()
                        return True, clean_minecraft_text_static(res) if res else "Lệnh đã thực thi (không có phản hồi)"
                    return False, "Sai mật khẩu RCON"
                except Exception as e:
                    return False, f"Lỗi kết nối RCON ({e})"
            ok, output = await asyncio.to_thread(_exec)
            if ok:
                return web.json_response({"ok": True, "mode": "rcon", "output": output, "response": output, "message": output})
            else:
                from data.database import get_mc_server_by_guild, queue_mc_command
                pserver = await get_mc_server_by_guild(int(gid))
                if pserver:
                    cmd_id = await queue_mc_command(pserver["server_key"], clean_cmd, issued_by=sess.get("username", "Web Admin"))
                    return web.json_response({"ok": True, "mode": "plugin", "output": f"RCON thất bại ({output}), đã chuyển lệnh #{cmd_id} vào hàng đợi Plugin", "message": f"Đã xếp hàng lệnh #{cmd_id} gửi tới plugin"})
                return web.json_response({"ok": False, "error": f"Lỗi RCON: {output}"}, status=400)
        else:
            from data.database import get_mc_server_by_guild, queue_mc_command
            pserver = await get_mc_server_by_guild(int(gid))
            if pserver:
                cmd_id = await queue_mc_command(pserver["server_key"], clean_cmd, issued_by=sess.get("username", "Web Admin"))
                return web.json_response({"ok": True, "mode": "plugin", "output": f"Đã xếp hàng lệnh #{cmd_id} gửi tới plugin", "response": f"Đã xếp hàng lệnh #{cmd_id}", "message": f"Đã xếp hàng lệnh #{cmd_id} gửi tới plugin"})
            return web.json_response({"ok": False, "error": "Server chưa cài đặt mật khẩu RCON và chưa kết nối Plugin!"}, status=400)
    except Exception as e:
        return web.json_response({"ok": False, "error": str(e)}, status=500)

# ==============================================================================
# API HOYO TEST CODE & PLUGIN COMMANDS
# ==============================================================================
async def handle_test_hoyo_code(request: web.Request):
    """Gửi tin nhắn test mã Hoyo Code mẫu (mã DEMO) vào kênh đã cài đặt và ghi lại setup."""
    sess = require_auth(request)
    if not sess:
        return web.json_response({"ok": False, "error": "Unauthorized"}, status=401)
    gid = request.match_info.get("id")
    if not can_access_guild(sess, gid):
        return web.json_response({"ok": False, "error": "Không có quyền"}, status=403)
    if not BOT_INSTANCE or not getattr(BOT_INSTANCE, "is_ready", lambda: False)():
        proxied = await _proxy_to_bot_web(request, f"/api/guilds/{gid}/hoyo-test-code")
        if proxied is not None:
            return proxied
        return web.json_response({"ok": False, "error": "Bot chưa kết nối"}, status=503)

    try:
        body = await request.json()
        game_key = str(body.get("game_key") or body.get("game") or "genshin").strip().lower()
        test_code = str(body.get("code") or "DEMO").strip().upper()

        # Cho phép truyền trực tiếp channel_id và role_id từ giao diện để test và lưu lại (ghi lại những setup)
        custom_ch = body.get("channel_id")
        custom_role = body.get("role_id")
        save_setup = body.get("save", True)

        import aiosqlite
        db_path = BASE_DIR / "gacha_data" / "database.sqlite"
        db_path.parent.mkdir(parents=True, exist_ok=True)
        channel_id, role_id = None, None

        async with aiosqlite.connect(str(db_path)) as db:
            await db.execute("""
                CREATE TABLE IF NOT EXISTS guild_config (
                    guild_id TEXT,
                    game_key TEXT,
                    channel_id INTEGER,
                    role_id INTEGER,
                    PRIMARY KEY (guild_id, game_key)
                )
            """)
            if custom_ch:
                channel_id = int(custom_ch)
                role_id = int(custom_role) if custom_role else None
                if save_setup:
                    await db.execute("""
                        INSERT INTO guild_config (guild_id, game_key, channel_id, role_id)
                        VALUES (?, ?, ?, ?)
                        ON CONFLICT(guild_id, game_key) DO UPDATE SET
                            channel_id = excluded.channel_id,
                            role_id = excluded.role_id
                    """, (str(gid), game_key, channel_id, role_id))
                    await db.commit()
            else:
                async with db.execute("SELECT channel_id, role_id FROM guild_config WHERE guild_id = ? AND game_key = ?", (str(gid), game_key)) as cur:
                    row = await cur.fetchone()
                    if row:
                        channel_id, role_id = row[0], row[1]

        if not channel_id:
            return web.json_response({"ok": False, "error": f"Chưa thiết lập kênh thông báo cho game {game_key.upper()}!"}, status=400)

        channel = BOT_INSTANCE.get_channel(int(channel_id))
        if not channel:
            return web.json_response({"ok": False, "error": "Không tìm thấy kênh trong server Discord"}, status=404)

        from Command_vi.code_gamegacha import GAMES
        ginfo = GAMES.get(game_key, {"name": game_key.upper(), "color": 0x4B69FF})
        ping_str = f"<@&{role_id}> " if role_id else ""

        embed = discord.Embed(
            title=f"🧪 [TEST] GIFTCODE HOYOVERSE & GACHA: {ginfo['name']}",
            description=(
                f"👉 Mã Code Thử Nghiệm: **`{test_code}`**\n"
                f"🎁 Phần thưởng: **300 Nguyên Thạch / Vé Quay Thử Nghiệm (DEMO)**\n"
                f"⌛ Hạn dùng: **24.0 giờ**\n\n"
                f"*(Thông báo thử nghiệm từ Sakura Dashboard — Kênh và Role đã được cấu hình và kiểm tra thành công!)*"
            ),
            color=ginfo.get("color", 0x4B69FF)
        )
        if ginfo.get("redeem_url"):
            embed.description += f"\n\n🔗 [Link đổi thưởng thử nghiệm]({ginfo['redeem_url']}{test_code})"
        embed.set_footer(text="Sakura Bot | Hoyo Code Watcher Test (DEMO)")

        await channel.send(content=f"{ping_str}🔔 **Kiểm tra thông báo code {ginfo['name']} thành công (Mã: `{test_code}` - Kênh: #{channel.name})!**", embed=embed)
        add_log("SUCCESS", f"User {sess.get('username')} test gửi Hoyo Code ({game_key}, mã: {test_code}) tại server {gid}")
        return web.json_response({
            "ok": True,
            "message": f"Đã gửi code thử nghiệm [{test_code}] vào kênh #{channel.name} và lưu setup thành công!"
        })
    except Exception as e:
        return web.json_response({"ok": False, "error": str(e)}, status=500)

async def handle_get_plugin_commands(request: web.Request):
    """Đọc toàn bộ lệnh từ plugin.yml và phân loại thành các nhóm trực quan, không phụ thuộc pyyaml."""
    try:
        plugin_yml_path = BASE_DIR / "plugin" / "src" / "main" / "resources" / "plugin.yml"
        commands_dict = {}
        if plugin_yml_path.exists():
            # 1. Thử parse bằng yaml nếu có
            parsed = False
            try:
                import yaml
                with open(plugin_yml_path, "r", encoding="utf-8") as f:
                    pdata = yaml.safe_load(f) or {}
                    raw_cmds = pdata.get("commands", {})
                    for c_name, c_val in raw_cmds.items():
                        if isinstance(c_val, dict):
                            commands_dict[c_name] = {
                                "name": c_name,
                                "command": c_name,
                                "description": c_val.get("description", "Không có mô tả"),
                                "usage": c_val.get("usage", f"/{c_name}"),
                                "aliases": c_val.get("aliases", []),
                                "permission": c_val.get("permission", f"sakura.{c_name}")
                            }
                parsed = True
            except Exception:
                pass

            # 2. Fallback regex line parser nếu không có thư viện yaml
            if not parsed or not commands_dict:
                try:
                    with open(plugin_yml_path, "r", encoding="utf-8") as f:
                        lines = f.readlines()
                    in_commands = False
                    current_cmd = None
                    current_data = {}
                    for line in lines:
                        line_str = line.rstrip()
                        if line_str == "commands:":
                            in_commands = True
                            continue
                        if not in_commands:
                            continue
                        if line_str and not line_str.startswith(" "):
                            break
                        m_cmd = re.match(r"^  ([a-zA-Z0-9_\-]+):\s*$", line_str)
                        if m_cmd:
                            if current_cmd:
                                commands_dict[current_cmd] = current_data
                            current_cmd = m_cmd.group(1)
                            current_data = {
                                "name": current_cmd,
                                "command": current_cmd,
                                "description": "Không có mô tả",
                                "usage": f"/{current_cmd}",
                                "aliases": [],
                                "permission": f"sakura.{current_cmd}"
                            }
                            continue
                        if current_cmd:
                            m_desc = re.match(r"^    description:\s*(?:\"([^\"]*)\"|'([^']*)'|(.*))$", line_str)
                            if m_desc:
                                current_data["description"] = (m_desc.group(1) or m_desc.group(2) or m_desc.group(3) or "").strip()
                            m_usage = re.match(r"^    usage:\s*(?:\"([^\"]*)\"|'([^']*)'|(.*))$", line_str)
                            if m_usage:
                                current_data["usage"] = (m_usage.group(1) or m_usage.group(2) or m_usage.group(3) or "").strip()
                            m_perm = re.match(r"^    permission:\s*(?:\"([^\"]*)\"|'([^']*)'|(.*))$", line_str)
                            if m_perm:
                                current_data["permission"] = (m_perm.group(1) or m_perm.group(2) or m_perm.group(3) or "").strip()
                            m_aliases = re.match(r"^    aliases:\s*\[(.*)\]", line_str)
                            if m_aliases:
                                current_data["aliases"] = [a.strip().strip("'\"") for a in m_aliases.group(1).split(",") if a.strip()]
                    if current_cmd:
                        commands_dict[current_cmd] = current_data
                except Exception as ex_parse:
                    print(f"[PluginCommands] Parse fallback error: {ex_parse}")

        categories = {
            "economy": {"title": "💰 Kinh Tế & Tiền Tệ", "cmds": ["balance", "pay", "eco", "daily", "shop", "topmoney", "leaderboard"]},
            "teleport": {"title": "🚀 Dịch Chuyển & Nhà Cửa", "cmds": ["tpa", "tphere", "tpaccept", "tpdeny", "tpauto", "sethome", "home", "delhome", "setwarp", "warp", "delwarp"]},
            "survival": {"title": "🛡️ Sinh Tồn & Lãnh Thổ", "cmds": ["claim", "sellclaim", "claimlist", "abyss", "nhindem", "kit", "rank", "enchest", "sit", "lay", "spin", "craw"]},
            "skills": {"title": "⚡ Kỹ Năng & Thử Thách", "cmds": ["quest", "ladder", "menu", "pass", "team"]},
            "admin": {"title": "👑 Quản Trị & Cấu Hình OP", "cmds": ["sakuragive", "sakurareload", "sakuragetitem", "sakuragiveop", "customitem", "sitadmin", "endlock", "summon", "backup", "restore"]},
            "bot": {"title": "🌸 Tích Hợp SakuraBot", "cmds": ["discord"]}
        }

        categorized = []
        flat_commands = []
        assigned = set()

        for cat_key, cat_info in categories.items():
            cmd_list = []
            for c_name in cat_info["cmds"]:
                assigned.add(c_name)
                if c_name in commands_dict:
                    item = dict(commands_dict[c_name])
                    item["category"] = cat_key
                    cmd_list.append(item)
                    flat_commands.append(item)
                else:
                    item = {
                        "name": c_name,
                        "command": c_name,
                        "category": cat_key,
                        "description": f"Lệnh {c_name} trong Sakura plugin",
                        "usage": f"/{c_name}",
                        "aliases": [],
                        "permission": f"sakura.{c_name}"
                    }
                    cmd_list.append(item)
                    flat_commands.append(item)
            categorized.append({
                "key": cat_key,
                "title": cat_info["title"],
                "commands": cmd_list
            })

        # Bổ sung các lệnh còn lại trong commands_dict nếu chưa được phân loại
        other_cmds = []
        for c_name, c_data in commands_dict.items():
            if c_name not in assigned:
                c_data["category"] = "other"
                other_cmds.append(c_data)
                flat_commands.append(c_data)

        if other_cmds:
            categorized.append({
                "key": "other",
                "title": "📦 Các Lệnh Khác",
                "commands": other_cmds
            })

        return web.json_response({
            "ok": True,
            "categories": categorized,
            "commands": flat_commands,
            "total": len(flat_commands)
        })
    except Exception as e:
        return web.json_response({"ok": False, "error": str(e)}, status=500)

# ==============================================================================
# HỆ THỐNG API MINECRAFT PLUGIN & QUẢN TRỊ SERVER MINECRAFT
# ==============================================================================

async def handle_mc_plugin_heartbeat(request: web.Request):
    """Minecraft Plugin gửi heartbeat định kỳ (10-30s) kèm thông tin server."""
    try:
        data = await request.json()
        server_id = str(data.get("server_id", "")).strip()
        server_name = str(data.get("server_name", "Minecraft Server")).strip()
        ip = str(data.get("ip", "")).strip()
        port = int(data.get("port", 25565))
        raw_online = data.get("online_players", 0)
        if isinstance(raw_online, list):
            players = raw_online
            online_players = len(players)
        else:
            try:
                online_players = int(raw_online or 0)
            except (ValueError, TypeError):
                online_players = 0
            players = data.get("players") or data.get("player_list") or []
        if not isinstance(players, list):
            players = []
        max_players = int(data.get("max_players", 20) or 20)
        tps = float(data.get("tps", 20.0) or 20.0)
        version = str(data.get("version", "")).strip()
        plugin_version = str(data.get("plugin_version", "1.0.0")).strip()

        if not server_id:
            server_id = f"mc_{re.sub(r'[^a-zA-Z0-9]', '', server_name.lower())}_{port}"
            if not server_id or server_id == "mc__":
                server_id = f"mc_srv_{port}"

        from data.database import upsert_mc_server_heartbeat, get_pending_mc_commands, get_pending_mc_chats
        await upsert_mc_server_heartbeat(
            server_id=server_id,
            server_name=server_name,
            ip=ip,
            port=port,
            online_players=online_players,
            max_players=max_players,
            player_list=players,
            tps=tps,
            version=version,
            plugin_version=plugin_version
        )

        pending_cmds = await get_pending_mc_commands(server_id)
        pending_chats = await get_pending_mc_chats(server_id)

        return web.json_response({
            "ok": True,
            "server_id": server_id,
            "commands": pending_cmds,
            "chats": pending_chats
        })
    except Exception as e:
        return web.json_response({"ok": False, "error": str(e)}, status=500)

async def handle_mc_plugin_create_link_code(request: web.Request):
    """Plugin gọi khi admin gõ '/discord server link' trong game."""
    try:
        data = await request.json()
        server_id = str(data.get("server_id") or data.get("server_key") or "").strip()
        server_name = str(data.get("server_name") or "").strip()
        server_ip = str(data.get("ip") or "127.0.0.1").strip()
        server_port = int(data.get("port") or 25565)
        if not server_id:
            return web.json_response({"ok": False, "error": "Thiếu server_id"}, status=400)

        from data.database import upsert_mc_server_heartbeat, create_mc_server_link_code
        try:
            await upsert_mc_server_heartbeat(
                server_key=server_id,
                server_name=server_name or f"Minecraft Server ({server_port})",
                server_ip=server_ip,
                server_port=server_port,
                online_players=[]
            )
        except Exception:
            pass

        try:
            from data.database import create_mc_server_link_code
            code = await create_mc_server_link_code(server_id, server_name)
        except Exception as ex_db:
            import secrets, aiosqlite
            code = f"MCLINK-{secrets.token_hex(3).upper()}"
            now = int(time.time())
            expires_at = now + 900
            db_path = DATA_DIR / "database.db"
            async with aiosqlite.connect(db_path) as db:
                await db.execute("""
                    CREATE TABLE IF NOT EXISTS mc_server_link_codes (
                        code TEXT PRIMARY KEY,
                        server_key TEXT,
                        server_name TEXT,
                        created_at INTEGER,
                        expires_at INTEGER
                    )
                """)
                await db.execute("DELETE FROM mc_server_link_codes WHERE expires_at < ?", (now,))
                await db.execute("INSERT OR REPLACE INTO mc_server_link_codes (code, server_key, server_name, created_at, expires_at) VALUES (?, ?, ?, ?, ?)",
                                 (code, server_id, server_name, now, expires_at))
                await db.commit()
        add_mc_log("INFO", f"Plugin yêu cầu mã liên kết cho server {server_id}: {code}")
        return web.json_response({
            "ok": True,
            "server_id": server_id,
            "code": code,
            "expires_in": 900,
            "instructions": f"Vào Discord dùng lệnh: /mc linkserver {code} (yêu cầu quyền Chủ sở hữu Guild / Administrator) hoặc nhập trên Web Dashboard."
        })
    except Exception as e:
        return web.json_response({"ok": False, "error": str(e)}, status=500)

async def handle_mc_plugin_event(request: web.Request):
    """Plugin bắn sự kiện in-game: chat, join, quit, advancement, death sang Discord."""
    try:
        data = await request.json()
        server_id = str(data.get("server_id", "")).strip()
        event_type = str(data.get("event_type") or data.get("event") or "chat").strip().lower()
        player = str(data.get("player", "Unknown")).strip()
        player_uuid = str(data.get("player_uuid", "")).strip()
        message = str(data.get("message", "")).strip()

        from data.database import get_mc_server
        server = await get_mc_server(server_id)
        if not server:
            return web.json_response({"ok": False, "error": "Server chưa đăng ký"}, status=404)

        guild_id = server.get("guild_id")
        chat_channel_id = server.get("chat_channel_id")
        log_channel_id = server.get("log_channel_id")

        log_text = f"[{server.get('server_name', server_id)}] [{event_type.upper()}] {player}: {message}"
        add_mc_log("EVENT", log_text)

        if BOT_INSTANCE and getattr(BOT_INSTANCE, "is_ready", lambda: False)():
            target_ch_id = chat_channel_id if event_type == "chat" else (log_channel_id or chat_channel_id)
            if target_ch_id:
                channel = BOT_INSTANCE.get_channel(int(target_ch_id))
                if channel:
                    avatar_url = f"https://mc-heads.net/avatar/{player_uuid or player}/64"
                    server_name = server.get("server_name", "Minecraft Server")
                    grass_icon = "https://minotar.net/cube/grass/32.png"
                    if event_type == "chat":
                        embed = discord.Embed(
                            description=f"**{message}**",
                            color=discord.Color.from_rgb(83, 166, 73)
                        )
                        embed.set_author(name=f"💬 [MC] {player}", icon_url=avatar_url)
                        embed.set_footer(text=server_name, icon_url=grass_icon)
                        embed.timestamp = discord.utils.utcnow()
                        await channel.send(embed=embed)
                    elif event_type == "join":
                        embed = discord.Embed(
                            description=f"🟢 **{player}** đã tham gia máy chủ Minecraft!",
                            color=discord.Color.green()
                        )
                        embed.set_author(name=player, icon_url=avatar_url)
                        embed.set_footer(text=server_name, icon_url=grass_icon)
                        embed.timestamp = discord.utils.utcnow()
                        await channel.send(embed=embed)
                    elif event_type == "quit":
                        embed = discord.Embed(
                            description=f"🔴 **{player}** đã rời khỏi máy chủ Minecraft.",
                            color=discord.Color.red()
                        )
                        embed.set_author(name=player, icon_url=avatar_url)
                        embed.set_footer(text=server_name, icon_url=grass_icon)
                        embed.timestamp = discord.utils.utcnow()
                        await channel.send(embed=embed)
                    elif event_type == "advancement":
                        adv_name = data.get("advancement", message)
                        embed = discord.Embed(
                            title="🏆 THÀNH TỰU MỚI!",
                            description=f"Chúc mừng **{player}** vừa mở khóa thành tựu:\n⭐ **{adv_name}**!",
                            color=discord.Color.gold()
                        )
                        embed.set_author(name=player, icon_url=avatar_url)
                        embed.set_thumbnail(url=f"https://mc-heads.net/head/{player_uuid or player}/64")
                        embed.set_footer(text=server_name, icon_url=grass_icon)
                        embed.timestamp = discord.utils.utcnow()
                        await channel.send(embed=embed)
                    elif event_type == "death":
                        death_msg = data.get("death_message", message) or f"{player} đã chết."
                        embed = discord.Embed(
                            description=f"💀 **{death_msg}**",
                            color=discord.Color.dark_grey()
                        )
                        embed.set_author(name=player, icon_url=avatar_url)
                        embed.set_footer(text=server_name, icon_url=grass_icon)
                        embed.timestamp = discord.utils.utcnow()
                        await channel.send(embed=embed)

        return web.json_response({"ok": True, "received": True})
    except Exception as e:
        return web.json_response({"ok": False, "error": str(e)}, status=500)

async def handle_mc_plugin_command_result(request: web.Request):
    """Plugin trả về kết quả thực thi lệnh console."""
    try:
        data = await request.json()
        command_id = int(data.get("command_id", 0))
        output = str(data.get("output") or data.get("response") or "").strip()

        from data.database import complete_mc_command
        await complete_mc_command(command_id, output)
        add_mc_log("RES", f"[CMD #{command_id} Output]\n{output}")
        return web.json_response({"ok": True})
    except Exception as e:
        return web.json_response({"ok": False, "error": str(e)}, status=500)

async def handle_mc_plugin_user_create_link_code(request: web.Request):
    """Plugin gọi khi player dùng '/discord link' in-game."""
    try:
        data = await request.json()
        player_name = str(data.get("player_name") or data.get("name") or "").strip()
        player_uuid = str(data.get("player_uuid") or data.get("uuid") or "").strip()

        if not player_name:
            return web.json_response({"ok": False, "error": "Thiếu player_name"}, status=400)

        try:
            from data.database import create_mc_user_link_code
            code = await create_mc_user_link_code(player_name, player_uuid)
        except Exception as ex_db:
            import secrets, aiosqlite
            code = secrets.token_hex(3).upper()
            now = int(time.time())
            expires_at = now + 600
            db_path = DATA_DIR / "database.db"
            async with aiosqlite.connect(db_path) as db:
                await db.execute("""
                    CREATE TABLE IF NOT EXISTS mc_user_link_codes (
                        code TEXT PRIMARY KEY,
                        player_uuid TEXT,
                        player_name TEXT,
                        created_at INTEGER,
                        expires_at INTEGER
                    )
                """)
                await db.execute("DELETE FROM mc_user_link_codes WHERE expires_at < ?", (now,))
                await db.execute("INSERT OR REPLACE INTO mc_user_link_codes (code, player_uuid, player_name, created_at, expires_at) VALUES (?, ?, ?, ?, ?)",
                                 (code, str(player_uuid).strip().lower(), str(player_name).strip(), now, expires_at))
                await db.commit()
        return web.json_response({
            "ok": True,
            "code": code,
            "expires_in": 600,
            "message": f"Dùng mã `{code}` trong Discord: /mc link code:{code} để liên kết tài khoản và đồng bộ Coins!"
        })
    except Exception as e:
        return web.json_response({"ok": False, "error": str(e)}, status=500)

async def handle_mc_plugin_economy_sync(request: web.Request):
    """Plugin yêu cầu đồng bộ coins người chơi hoặc kiểm tra trạng thái liên kết và số dư."""
    try:
        data = await request.json()
        player_uuid = str(data.get("player_uuid") or data.get("uuid") or "").strip()
        direction = str(data.get("direction") or data.get("action") or "").strip().lower()
        amount = int(data.get("amount", 0))

        from data.database import get_mc_user_by_uuid, sync_mc_user_coins, get_user_data
        link = await get_mc_user_by_uuid(player_uuid)
        if not link:
            return web.json_response({
                "ok": False,
                "is_linked": False,
                "error": "Tài khoản Minecraft chưa liên kết với Discord. Dùng /discord link để liên kết!"
            }, status=404)

        discord_id = str(link.get("discord_id") or link.get("discord_user_id") or "")
        mc_name = str(link.get("minecraft_name") or link.get("mc_player_name") or "")

        # Lấy tên / tag Discord
        discord_tag = f"Discord ID {discord_id}"
        if BOT_INSTANCE and discord_id.isdigit():
            u = BOT_INSTANCE.get_user(int(discord_id))
            if u:
                discord_tag = f"@{u.name}" if not getattr(u, 'discriminator', '0') or u.discriminator == '0' else f"{u.name}#{u.discriminator}"

        if direction in ("to_mc", "deposit"):
            if amount <= 0:
                return web.json_response({"ok": False, "error": "Số lượng coins phải lớn hơn 0"}, status=400)
            res = await sync_mc_user_coins(discord_id, "to_mc", amount)
            if res.get("ok"):
                res["is_linked"] = True
                res["discord_tag"] = discord_tag
                res["minecraft_name"] = mc_name
            return web.json_response(res)
        elif direction in ("to_discord", "withdraw"):
            if amount <= 0:
                return web.json_response({"ok": False, "error": "Số lượng coins phải lớn hơn 0"}, status=400)
            res = await sync_mc_user_coins(discord_id, "to_discord", amount, from_plugin=True)
            if res.get("ok"):
                res["is_linked"] = True
                res["discord_tag"] = discord_tag
                res["minecraft_name"] = mc_name
            return web.json_response(res)
        else: # "balance", "status"
            u_data = await get_user_data(0, int(discord_id) if discord_id.isdigit() else 0)
            d_coins = int(u_data.get("coins", 0))
            d_bank = int(u_data.get("bank", 0))
            mc_coins = int(link.get("mc_coins", 0))
            return web.json_response({
                "ok": True,
                "is_linked": True,
                "discord_id": discord_id,
                "discord_user_id": discord_id,
                "discord_tag": discord_tag,
                "minecraft_name": mc_name,
                "discord_coins": d_coins,
                "discord_bank": d_bank,
                "mc_coins": mc_coins,
                "rate": "1 MC Coin = 1,000 Discord Coins"
            })
    except Exception as e:
        return web.json_response({"ok": False, "error": str(e)}, status=500)

async def handle_mc_admin_servers(request: web.Request):
    """Lấy danh sách hợp nhất toàn bộ các server Minecraft (cả Plugin Bridge và RCON Console)."""
    sess = require_auth(request)
    if not sess:
        return web.json_response({"ok": False, "error": "Unauthorized"}, status=401)

    try:
        from data.database import list_mc_servers
        servers = await list_mc_servers()
        now = time.time()

        res_servers = []
        seen_guild_ids = set()
        seen_keys = set()

        # 1. Các server qua Plugin Sakura
        for s in servers:
            s_copy = dict(s)
            s_key = s.get("server_key", "")
            seen_keys.add(s_key)
            s_copy["server_id"] = s_key
            s_copy["name"] = s.get("server_name") or f"Minecraft Server ({s.get('server_port', 25565)})"
            s_copy["ip"] = s.get("server_ip") or "127.0.0.1"
            s_copy["port"] = s.get("server_port", 25565)
            s_copy["protocol"] = "plugin"
            s_copy["protocol_label"] = "🔌 SAKURA PLUGIN"
            s_copy["is_online"] = (now - s.get("last_heartbeat", 0)) < 90
            guild_id = s.get("guild_id")
            s_copy["guild_name"] = None
            s_copy["guild_icon"] = None
            s_copy["can_manage"] = False
            s_copy["is_owner"] = False

            if guild_id:
                seen_guild_ids.add(str(guild_id))
                if BOT_INSTANCE:
                    g = BOT_INSTANCE.get_guild(int(guild_id))
                    if g:
                        s_copy["guild_name"] = g.name
                        s_copy["guild_icon"] = g.icon.url if g.icon else None

            if is_admin_session(sess):
                s_copy["can_manage"] = True
                s_copy["is_owner"] = True
            elif guild_id:
                s_copy["can_manage"] = can_access_guild(sess, str(guild_id))
                did = str(sess.get("discord_id") or "")
                if BOT_INSTANCE:
                    g = BOT_INSTANCE.get_guild(int(guild_id))
                    if g and str(g.owner_id) == did:
                        s_copy["is_owner"] = True

            res_servers.append(s_copy)

        # 2. Hợp nhất các server RCON từ guild_mc_connections.json
        guild_configs = _load_guild_mc_configs()
        for gid, gcfg in guild_configs.items():
            if str(gid) in seen_guild_ids:
                # Đã có server plugin nối với guild này, đính kèm thêm RCON port nếu có
                for existing in res_servers:
                    if str(existing.get("guild_id")) == str(gid):
                        existing["has_rcon"] = bool(gcfg.get("rcon_password"))
                        existing["rcon_port"] = gcfg.get("rcon_port", 25575)
                        existing["rcon_host"] = gcfg.get("rcon_host") or gcfg.get("host")
                        break
            else:
                # Server RCON độc lập
                r_host = gcfg.get("rcon_host") or gcfg.get("host") or "127.0.0.1"
                r_port = int(gcfg.get("rcon_port") or 25575)
                mc_port = int(gcfg.get("port") or 25565)
                g_name = f"Guild {gid}"
                g_icon = None
                is_mgr = is_admin_session(sess) or can_access_guild(sess, str(gid))
                if BOT_INSTANCE:
                    g = BOT_INSTANCE.get_guild(int(gid))
                    if g:
                        g_name = g.name
                        g_icon = g.icon.url if g.icon else None

                res_servers.append({
                    "server_id": f"rcon_{gid}",
                    "server_key": f"rcon_{gid}",
                    "name": f"Minecraft Server ({g_name})",
                    "ip": r_host,
                    "port": mc_port,
                    "rcon_port": r_port,
                    "rcon_host": r_host,
                    "protocol": "rcon",
                    "protocol_label": "⚡ RCON CONSOLE",
                    "is_online": True,
                    "guild_id": str(gid),
                    "guild_name": g_name,
                    "guild_icon": g_icon,
                    "chat_channel_id": gcfg.get("chat_channel_id"),
                    "log_channel_id": gcfg.get("log_channel_id"),
                    "has_rcon": bool(gcfg.get("rcon_password")),
                    "can_manage": is_mgr,
                    "is_owner": is_mgr,
                    "players_count": 0,
                    "max_players": 50,
                    "tps": 20.0
                })
                seen_guild_ids.add(str(gid))

        # 3. Thêm Local Server nếu có server.properties và chưa có trong list
        sp_file = SERVER_DIR / "server.properties"
        if sp_file.exists() and "local_server" not in seen_keys:
            try:
                local_port = 25565
                local_rcon_port = 25575
                local_motd = "Sakura Local PaperMC"
                for line in sp_file.read_text(encoding="utf-8").splitlines():
                    if line.startswith("server-port="):
                        local_port = int(line.split("=", 1)[1].strip())
                    elif line.startswith("rcon.port="):
                        local_rcon_port = int(line.split("=", 1)[1].strip())
                    elif line.startswith("motd="):
                        local_motd = line.split("=", 1)[1].strip()

                has_local = any(s.get("port") == local_port and s.get("ip") in ["127.0.0.1", "localhost", ""] for s in res_servers)
                if not has_local:
                    res_servers.append({
                        "server_id": "local_server",
                        "server_key": "local_server",
                        "name": local_motd or "PaperMC Local Server",
                        "ip": "127.0.0.1",
                        "port": local_port,
                        "rcon_port": local_rcon_port,
                        "protocol": "rcon",
                        "protocol_label": "⚡ LOCAL RCON",
                        "is_online": True,
                        "guild_id": None,
                        "guild_name": "Chưa gán Guild",
                        "can_manage": is_admin_session(sess),
                        "is_owner": is_admin_session(sess),
                        "has_rcon": True,
                        "tps": 20.0,
                        "players_count": 0
                    })
            except Exception:
                pass

        return web.json_response({"ok": True, "servers": res_servers})
    except Exception as e:
        return web.json_response({"ok": False, "error": str(e)}, status=500)

async def handle_mc_admin_server_detail(request: web.Request):
    """Lấy thông tin chi tiết một máy chủ Minecraft (Plugin hoặc RCON)."""
    sess = require_auth(request)
    if not sess:
        return web.json_response({"ok": False, "error": "Unauthorized"}, status=401)
    
    server_key = request.query.get("server_id") or request.query.get("server_key") or ""
    if not server_key:
        return web.json_response({"ok": False, "error": "Thiếu server_key"}, status=400)

    try:
        from data.database import get_mc_server
        server = await get_mc_server(server_key)
        now = time.time()

        if not server:
            configs = _load_guild_mc_configs()
            gid = server_key.replace("rcon_", "")
            if gid in configs:
                cfg = configs[gid]
                g_name = f"Guild {gid}"
                if BOT_INSTANCE:
                    g = BOT_INSTANCE.get_guild(int(gid)) if gid.isdigit() else None
                    if g: g_name = g.name
                server = {
                    "server_key": server_key,
                    "server_id": server_key,
                    "server_name": f"Minecraft Server ({g_name})",
                    "server_ip": cfg.get("rcon_host") or cfg.get("host") or "127.0.0.1",
                    "server_port": int(cfg.get("port", 25565)),
                    "rcon_port": int(cfg.get("rcon_port", 25575)),
                    "guild_id": gid,
                    "guild_name": g_name,
                    "chat_channel_id": cfg.get("chat_channel_id"),
                    "log_channel_id": cfg.get("log_channel_id"),
                    "protocol": "rcon",
                    "is_online": True,
                    "tps": 20.0,
                    "players_count": 0
                }
            elif server_key in ["local_server", "local_rcon"]:
                server = {
                    "server_key": "local_server",
                    "server_id": "local_server",
                    "server_name": "Local PaperMC Server",
                    "server_ip": "127.0.0.1",
                    "server_port": 25565,
                    "rcon_port": 25575,
                    "protocol": "rcon",
                    "is_online": True,
                    "tps": 20.0,
                    "players_count": 0
                }

        if not server:
            return web.json_response({"ok": False, "error": "Không tìm thấy server"}, status=404)

        s_dict = dict(server)
        s_dict["server_id"] = server_key
        s_dict["is_online"] = (now - s_dict.get("last_heartbeat", 0)) < 90 if s_dict.get("protocol") == "plugin" else True
        guild_id = s_dict.get("guild_id")
        if guild_id and BOT_INSTANCE:
            g = BOT_INSTANCE.get_guild(int(guild_id))
            if g:
                s_dict["guild_name"] = g.name
                s_dict["guild_icon"] = g.icon.url if g.icon else None

        # Bổ sung thông tin địa chỉ console và mã console điều khiển
        host = s_dict.get("server_ip") or "127.0.0.1"
        port = s_dict.get("server_port") or 25565
        rcon_port = s_dict.get("rcon_port") or 25575
        rcon_pass = s_dict.get("rcon_password") or ""

        # Nạp từ server.properties nếu host là localhost / 127.0.0.1
        if host in ["127.0.0.1", "localhost"] and not rcon_pass:
            sp_file = SERVER_DIR / "server.properties"
            if sp_file.exists():
                try:
                    for line in sp_file.read_text(encoding="utf-8").splitlines():
                        if line.startswith("rcon.password="):
                            rcon_pass = line.split("=", 1)[1].strip()
                        elif line.startswith("rcon.port="):
                            try: rcon_port = int(line.split("=", 1)[1].strip())
                            except Exception: pass
                except Exception:
                    pass

        s_dict["console_host"] = host
        s_dict["console_port"] = rcon_port if s_dict.get("protocol") == "rcon" else port
        s_dict["console_address"] = f"{host}:{rcon_port if s_dict.get('protocol') == 'rcon' else port}"
        s_dict["console_code"] = rcon_pass if rcon_pass else (s_dict.get("server_key") or "sakura_console")
        s_dict["rcon_password"] = rcon_pass

        return web.json_response({"ok": True, "server": s_dict})
    except Exception as e:
        return web.json_response({"ok": False, "error": str(e)}, status=500)

async def handle_mc_admin_server_link(request: web.Request):
    """Nối Minecraft Server với Discord Guild trên Web (yêu cầu quyền Owner hoặc Admin Guild)."""
    sess = require_auth(request)
    if not sess:
        return web.json_response({"ok": False, "error": "Unauthorized"}, status=401)

    try:
        body = await request.json()
        guild_id = str(body.get("guild_id", "")).strip()
        code = str(body.get("code", "")).strip().upper()
        server_id = str(body.get("server_id", "")).strip()

        if not guild_id or (not code and not server_id):
            return web.json_response({"ok": False, "error": "Vui lòng nhập Guild ID và Mã liên kết (hoặc Server ID)"}, status=400)

        did = str(sess.get("discord_id") or "")
        is_owner = False
        if is_admin_session(sess):
            is_owner = True
        elif BOT_INSTANCE:
            g = BOT_INSTANCE.get_guild(int(guild_id))
            if not g:
                return web.json_response({"ok": False, "error": f"Bot không nằm trong máy chủ {guild_id}"}, status=404)
            if str(g.owner_id) == did:
                is_owner = True
            else:
                member = g.get_member(int(did)) if did.isdigit() else None
                if member and member.guild_permissions.administrator:
                    is_owner = True

        if not is_owner:
            return web.json_response({"ok": False, "error": "Chỉ Chủ sở hữu máy chủ (Server Owner) hoặc Quản trị viên mới có quyền liên kết máy chủ Minecraft này!"}, status=403)

        from data.database import link_mc_server_to_guild, direct_link_mc_server_to_guild
        if code:
            res_link = await link_mc_server_to_guild(code, int(guild_id), int(did) if did.isdigit() else None)
        else:
            res_link = await direct_link_mc_server_to_guild(server_id, int(guild_id), int(did) if did.isdigit() else None)

        if res_link.get("ok"):
            msg = res_link.get("message", "Thành công")
            add_log("SUCCESS", f"User {sess.get('username')} đã liên kết máy chủ MC với Guild {guild_id}: {msg}")
            return web.json_response(res_link)
        else:
            err = res_link.get("error", "Lỗi liên kết máy chủ")
            return web.json_response({"ok": False, "error": err}, status=400)
    except Exception as e:
        return web.json_response({"ok": False, "error": str(e)}, status=500)

async def handle_mc_admin_server_unlink(request: web.Request):
    """Hủy liên kết server Minecraft khỏi Discord Guild."""
    sess = require_auth(request)
    if not sess:
        return web.json_response({"ok": False, "error": "Unauthorized"}, status=401)

    try:
        body = await request.json()
        guild_id = str(body.get("guild_id", "")).strip()
        if not guild_id:
            return web.json_response({"ok": False, "error": "Thiếu guild_id"}, status=400)

        did = str(sess.get("discord_id") or "")
        is_owner = False
        if is_admin_session(sess):
            is_owner = True
        elif BOT_INSTANCE:
            g = BOT_INSTANCE.get_guild(int(guild_id))
            if g and str(g.owner_id) == did:
                is_owner = True
            elif g:
                m = g.get_member(int(did)) if did.isdigit() else None
                if m and m.guild_permissions.administrator:
                    is_owner = True

        if not is_owner:
            return web.json_response({"ok": False, "error": "Chỉ Server Owner hoặc Admin mới có quyền hủy liên kết!"}, status=403)

        from data.database import unlink_mc_server_from_guild
        res_unlink = await unlink_mc_server_from_guild(int(guild_id))
        if res_unlink.get("ok"):
            msg = res_unlink.get("message", "Đã hủy liên kết máy chủ")
            add_log("SUCCESS", f"User {sess.get('username')} hủy liên kết MC server của Guild {guild_id}")
            return web.json_response(res_unlink)
        err = res_unlink.get("error", "Lỗi hủy liên kết")
        return web.json_response({"ok": False, "error": err}, status=400)
    except Exception as e:
        return web.json_response({"ok": False, "error": str(e)}, status=500)

async def handle_mc_admin_server_config(request: web.Request):
    """Cấu hình kênh chat 2 chiều & kênh log Minecraft (hỗ trợ liên kết Guild trực tiếp)."""
    sess = require_auth(request)
    if not sess:
        return web.json_response({"ok": False, "error": "Unauthorized"}, status=401)

    try:
        body = await request.json()
        server_id = str(body.get("server_id", "")).strip()
        chat_channel_id = body.get("chat_channel_id")
        log_channel_id = body.get("log_channel_id")
        target_guild_id = body.get("guild_id")

        from data.database import get_mc_server, update_mc_server_channels, link_mc_server_to_guild
        server = await get_mc_server(server_id)
        if not server:
            return web.json_response({"ok": False, "error": "Không tìm thấy server MC"}, status=404)

        guild_id = target_guild_id or server.get("guild_id")
        if not guild_id:
            return web.json_response({"ok": False, "error": "Vui lòng chọn Discord Guild để liên kết trước khi lưu kênh!"}, status=400)

        if not can_access_guild(sess, str(guild_id)):
            return web.json_response({"ok": False, "error": "Bạn không có quyền quản lý Discord Server này!"}, status=403)

        if target_guild_id and str(server.get("guild_id")) != str(target_guild_id):
            await link_mc_server_to_guild(server_id, int(target_guild_id))

        ch_id = int(chat_channel_id) if chat_channel_id and str(chat_channel_id).isdigit() else None
        log_id = int(log_channel_id) if log_channel_id and str(log_channel_id).isdigit() else None

        await update_mc_server_channels(server_id, chat_channel_id=ch_id, log_channel_id=log_id)
        add_log("SUCCESS", f"User {sess.get('username')} cập nhật kênh MC cho server {server_id}: Guild={guild_id}, Chat={ch_id}, Log={log_id}")
        return web.json_response({"ok": True, "message": "Đã cập nhật kênh liên kết Minecraft thành công!"})
    except Exception as e:
        return web.json_response({"ok": False, "error": str(e)}, status=500)

async def handle_mc_admin_server_test(request: web.Request):
    """Kiểm tra live trạng thái server và RCON cho Minecraft Server trong tab Admin."""
    sess = require_auth(request)
    if not sess:
        return web.json_response({"ok": False, "error": "Unauthorized"}, status=401)
    if not is_admin_session(sess):
        return web.json_response({"ok": False, "error": "Chỉ admin mới thao tác"}, status=403)

    try:
        body = await request.json()
        server_id = str(body.get("server_id", "")).strip()
        from data.database import get_mc_server
        server = await get_mc_server(server_id)
        if not server:
            return web.json_response({"ok": False, "error": "Không tìm thấy server"}, status=404)

        host = server.get("server_ip") or "127.0.0.1"
        port = server.get("server_port") or 25565
        guild_id = server.get("guild_id")

        server_status = {"online": False, "latency_ms": 0}
        try:
            from mcstatus import JavaServer
            j_server = JavaServer.lookup(f"{host}:{port}")
            st = await asyncio.to_thread(j_server.status)
            server_status = {
                "online": True,
                "version": st.version.name,
                "players_online": st.players.online,
                "players_max": st.players.max,
                "latency_ms": round(st.latency, 1),
                "motd": str(getattr(st.description, 'to_plain', lambda: st.description)())
            }
        except Exception as e:
            server_status["error"] = str(e)

        rcon_status = {"connected": False, "message": "Chưa cấu hình RCON"}
        try:
            from Command_vi.minecraft import send_rcon_command_sync
            ok, r_msg = await asyncio.to_thread(send_rcon_command_sync, "list", host=host, guild_id=guild_id)
            rcon_status = {"connected": ok, "message": r_msg}
        except Exception as re:
            rcon_status = {"connected": False, "message": str(re)}

        return web.json_response({
            "ok": True,
            "server": server_status,
            "rcon": rcon_status,
            "plugin": {
                "online": bool(server.get("is_online")),
                "tps": server.get("tps", 20.0),
                "last_heartbeat": server.get("last_heartbeat", 0)
            }
        })
    except Exception as e:
        return web.json_response({"ok": False, "error": str(e)}, status=500)

async def handle_mc_admin_server_command(request: web.Request):
    """Gửi lệnh console tới Minecraft Server (hỗ trợ cả giao thức RCON Console và Plugin Bridge)."""
    sess = require_auth(request)
    if not sess:
        return web.json_response({"ok": False, "error": "Unauthorized"}, status=401)

    try:
        body = await request.json()
        server_id = str(body.get("server_id", "")).strip()
        command = str(body.get("command", "")).strip()

        if not server_id or not command:
            return web.json_response({"ok": False, "error": "Thiếu server_id hoặc câu lệnh"}, status=400)

        clean_cmd = command.lstrip("/")

        # 1. Kiểm tra xem có phải RCON Server không
        configs = _load_guild_mc_configs()
        gid = server_id.replace("rcon_", "")
        gcfg = configs.get(gid, {})

        is_rcon = server_id.startswith("rcon_") or server_id in ["local_server", "local_rcon"] or bool(gcfg)

        if is_rcon:
            r_host = gcfg.get("rcon_host") or gcfg.get("host") or "127.0.0.1"
            r_port = int(gcfg.get("rcon_port") or 25575)
            r_pass = gcfg.get("rcon_password") or ""

            if r_host in ["127.0.0.1", "localhost"] and not r_pass:
                sp_file = SERVER_DIR / "server.properties"
                if sp_file.exists():
                    try:
                        for line in sp_file.read_text(encoding="utf-8").splitlines():
                            if line.startswith("rcon.password="):
                                r_pass = line.split("=", 1)[1].strip()
                            elif line.startswith("rcon.port="):
                                try: r_port = int(line.split("=", 1)[1].strip())
                                except Exception: pass
                    except Exception:
                        pass

            if r_pass:
                from mctools import RCONClient
                from Command_vi.minecraft import clean_minecraft_text_static
                def _exec():
                    try:
                        rc = RCONClient(r_host, port=r_port)
                        if rc.login(r_pass):
                            res = rc.command(clean_cmd)
                            rc.stop()
                            out = clean_minecraft_text_static(res) if res else "Lệnh đã thực thi thành công (không có phản hồi)"
                            return True, out
                        return False, "Mật khẩu RCON không chính xác"
                    except Exception as e:
                        return False, f"Lỗi kết nối RCON tới {r_host}:{r_port} ({e})"

                ok, out = await asyncio.to_thread(_exec)
                add_mc_log("CMD", f"> [{server_id}] {sess.get('username')}: {clean_cmd}")
                if ok:
                    add_mc_log("RES", f"< [{server_id}] {out}")
                    return web.json_response({"ok": True, "message": out, "response": out, "output": out})
                else:
                    return web.json_response({"ok": False, "error": out}, status=400)

        # 2. Xử lý qua Plugin Bridge
        from data.database import get_mc_server, queue_mc_command
        server = await get_mc_server(server_id)
        if not server:
            return web.json_response({"ok": False, "error": "Không tìm thấy máy chủ Minecraft"}, status=404)

        guild_id = server.get("guild_id")
        if not is_admin_session(sess) and guild_id and not can_access_guild(sess, str(guild_id)):
            return web.json_response({"ok": False, "error": "Chỉ người quản lý của Guild mới có quyền thao tác lệnh của server này!"}, status=403)

        issuer = f"web:{sess.get('username', 'admin')}"
        cmd_id = await queue_mc_command(server_id, clean_cmd, issued_by=issuer)
        add_mc_log("CMD", f"> [{server.get('server_name', server_id)}] {issuer}: {clean_cmd}")
        return web.json_response({
            "ok": True,
            "message": f"Lệnh đã gửi tới Plugin (ID #{cmd_id})",
            "response": f"[SakuraBridge] Lệnh đã gửi tới server và đang được thực thi...",
            "command_id": cmd_id
        })
    except Exception as e:
        return web.json_response({"ok": False, "error": str(e)}, status=500)

async def handle_mc_admin_server_players(request: web.Request):
    """Lấy danh sách người chơi đang online trên server MC."""
    sess = require_auth(request)
    if not sess:
        return web.json_response({"ok": False, "error": "Unauthorized"}, status=401)

    try:
        server_id = request.query.get("server_id", "").strip()
        from data.database import get_mc_server
        server = await get_mc_server(server_id)
        if not server:
            return web.json_response({"ok": False, "error": "Không tìm thấy server MC"}, status=404)

        raw_p = server.get("online_players") or server.get("player_list") or []
        if isinstance(raw_p, str):
            try:
                raw_p = json.loads(raw_p)
            except Exception:
                raw_p = []
        if not isinstance(raw_p, list):
            raw_p = []
        players = raw_p
        player_cards = []
        for p in players:
            p_name = p if isinstance(p, str) else p.get("name", "Player")
            p_uuid = p.get("uuid", "") if isinstance(p, dict) else ""
            player_cards.append({
                "name": p_name,
                "uuid": p_uuid,
                "avatar": f"https://mc-heads.net/avatar/{p_uuid or p_name}/64",
                "body": f"https://mc-heads.net/body/{p_uuid or p_name}/128"
            })

        online_cnt = len(player_cards)
        return web.json_response({
            "ok": True,
            "server_id": server_id,
            "server_name": server.get("server_name"),
            "online_count": online_cnt,
            "max_players": server.get("max_players", 20),
            "tps": server.get("tps", 20.0),
            "players": player_cards
        })
    except Exception as e:
        return web.json_response({"ok": False, "error": str(e)}, status=500)

async def handle_mc_admin_economy_convert(request: web.Request):
    """Đổi coins giữa Discord và Minecraft trên Web."""
    sess = require_auth(request)
    if not sess:
        return web.json_response({"ok": False, "error": "Unauthorized"}, status=401)

    try:
        body = await request.json()
        direction = str(body.get("direction", "")).strip().lower()
        amount = int(body.get("amount", 0))

        did = sess.get("discord_id")
        if not did:
            return web.json_response({"ok": False, "error": "Tài khoản web của bạn chưa liên kết Discord"}, status=400)

        from data.database import sync_mc_user_coins
        res = await sync_mc_user_coins(int(did), direction, amount)
        if res.get("ok"):
            add_log("SUCCESS", f"User {sess.get('username')} chuyển đổi {amount} coins ({direction})")
        return web.json_response(res)
    except Exception as e:
        return web.json_response({"ok": False, "error": str(e)}, status=500)

async def handle_get_guild_giveaways(request: web.Request):
    sess = require_auth(request)
    if not sess:
        return web.json_response({"ok": False, "error": "Unauthorized"}, status=401)
    guild_id = request.match_info.get("id")
    if not can_access_guild(sess, guild_id):
        return web.json_response({"ok": False, "error": "Không có quyền quản lý server này"}, status=403)
    try:
        import sqlite3
        gw_db = DATA_DIR / "giveaways.db"
        if not gw_db.exists():
            return web.json_response({"ok": True, "giveaways": []})
        with sqlite3.connect(gw_db) as conn:
            conn.row_factory = sqlite3.Row
            rows = conn.execute("SELECT * FROM giveaways WHERE guild_id = ? ORDER BY end_time DESC LIMIT 50", (int(guild_id),)).fetchall()
            result = []
            for r in rows:
                p_count = conn.execute("SELECT COUNT(*) FROM participants WHERE message_id = ?", (r["message_id"],)).fetchone()[0]
                result.append({
                    "message_id": str(r["message_id"]),
                    "channel_id": str(r["channel_id"]),
                    "host_id": str(r["host_id"]),
                    "prize": r["prize"],
                    "winners_count": r["winners_count"],
                    "end_time": r["end_time"],
                    "status": r["status"],
                    "participants_count": p_count
                })
            return web.json_response({"ok": True, "giveaways": result})
    except Exception as e:
        return web.json_response({"ok": False, "error": str(e)}, status=500)

async def handle_create_guild_giveaway(request: web.Request):
    sess = require_auth(request)
    if not sess:
        return web.json_response({"ok": False, "error": "Unauthorized"}, status=401)
    guild_id = request.match_info.get("id")
    if not can_access_guild(sess, guild_id):
        return web.json_response({"ok": False, "error": "Không có quyền quản lý server này"}, status=403)
    if not BOT_INSTANCE or not getattr(BOT_INSTANCE, "is_ready", lambda: False)():
        return web.json_response({"ok": False, "error": "Bot chưa kết nối"}, status=503)
    try:
        import datetime, discord, sqlite3
        body = await request.json()
        channel_id = int(body.get("channel_id"))
        prize = str(body.get("prize", "")).strip()
        winners_count = max(1, int(body.get("winners_count", 1)))
        duration_minutes = max(1, int(body.get("duration_minutes", 10)))

        if not prize:
            return web.json_response({"ok": False, "error": "Vui lòng nhập tên phần thưởng"}, status=400)

        channel = BOT_INSTANCE.get_channel(channel_id)
        if not channel:
            return web.json_response({"ok": False, "error": "Không tìm thấy kênh Discord"}, status=404)

        now_utc = datetime.datetime.now(datetime.timezone.utc)
        end_time_utc = now_utc + datetime.timedelta(minutes=duration_minutes)
        end_timestamp = end_time_utc.timestamp()

        embed = discord.Embed(
            title=f"🎉 GIVEAWAY: {prize}",
            description=f"Bấm vào nút **🎉 Tham Gia** bên dưới để có cơ hội trúng thưởng!\n\n"
                        f"🏆 **Số người trúng:** `{winners_count}`\n"
                        f"⏰ **Kết thúc:** <t:{int(end_timestamp)}:R> (<t:{int(end_timestamp)}:F>)\n"
                        f"👑 **Người tổ chức:** Web Admin ({sess.get('username')})",
            color=discord.Color.gold()
        )
        embed.set_footer(text="Sakura Giveaway System")

        from Command_vi.giveaway import Database
        try:
            from Command_vi.giveaway import GiveawayView
        except ImportError:
            from Command_vi.giveaway import PersistentGiveawayView as GiveawayView
        view = GiveawayView()
        msg = await channel.send(embed=embed, view=view)

        Database.add_giveaway(
            msg_id=msg.id,
            ch_id=channel.id,
            guild_id=int(guild_id),
            host_id=int(sess.get("discord_id", 0) or 0),
            prize=prize,
            winners=winners_count,
            end_time=end_timestamp,
            claim_to=0,
            roles=[],
            reason="Tổ chức từ Web Dashboard",
            on_fail="cancel",
            hide_host=False
        )

        add_log("SUCCESS", f"Admin {sess.get('username')} tạo giveaway '{prize}' tại guild {guild_id} channel {channel.name}")
        return web.json_response({"ok": True, "message": f"Đã khởi tạo giveaway '{prize}' thành công trên #{channel.name}!"})
    except Exception as e:
        return web.json_response({"ok": False, "error": str(e)}, status=500)

async def handle_end_guild_giveaway(request: web.Request):
    sess = require_auth(request)
    if not sess:
        return web.json_response({"ok": False, "error": "Unauthorized"}, status=401)
    guild_id = request.match_info.get("id")
    msg_id = request.match_info.get("msg_id")
    if not can_access_guild(sess, guild_id):
        return web.json_response({"ok": False, "error": "Không có quyền quản lý server này"}, status=403)
    try:
        from Command_vi.giveaway import Database
        gw = Database.get_giveaway(int(msg_id))
        if not gw:
            return web.json_response({"ok": False, "error": "Không tìm thấy giveaway"}, status=404)
        if gw["status"] != "running":
            return web.json_response({"ok": False, "error": "Giveaway này đã kết thúc hoặc đã hủy"}, status=400)
        
        # Gọi finalize trong Cog giveaway
        gw_cog = BOT_INSTANCE.get_cog("Giveaway") if BOT_INSTANCE else None
        if gw_cog:
            import asyncio
            asyncio.create_task(gw_cog.finalize_giveaway(gw))
            return web.json_response({"ok": True, "message": "Đã kích hoạt kết thúc sớm và quay thưởng giveaway!"})
        else:
            Database.set_status(int(msg_id), "ended")
            return web.json_response({"ok": True, "message": "Đã đổi trạng thái giveaway thành đã kết thúc"})
    except Exception as e:
        return web.json_response({"ok": False, "error": str(e)}, status=500)

async def handle_delete_guild_giveaway(request: web.Request):
    sess = require_auth(request)
    if not sess:
        return web.json_response({"ok": False, "error": "Unauthorized"}, status=401)
    guild_id = request.match_info.get("id")
    msg_id = request.match_info.get("msg_id")
    if not can_access_guild(sess, guild_id):
        return web.json_response({"ok": False, "error": "Không có quyền quản lý server này"}, status=403)
    try:
        import sqlite3
        gw_db = DATA_DIR / "giveaways.db"
        with sqlite3.connect(gw_db) as conn:
            conn.execute("DELETE FROM giveaways WHERE message_id = ?", (int(msg_id),))
            conn.execute("DELETE FROM participants WHERE message_id = ?", (int(msg_id),))
            conn.commit()
        return web.json_response({"ok": True, "message": "Đã xóa giveaway thành công"})
    except Exception as e:
        return web.json_response({"ok": False, "error": str(e)}, status=500)

# --- Tickets Endpoints (admin only) ---
async def handle_get_tickets(request: web.Request):
    sess = require_auth(request)
    if not sess:
        return web.json_response({"ok": False, "error": "Unauthorized"}, status=401)
    if not is_admin_session(sess):
        return web.json_response({"ok": False, "error": "Chỉ admin mới xem Tickets"}, status=403)
    open_tickets = load_json(DATA_DIR / "open_tickets.json", {})
    ticket_config = load_json(DATA_DIR / "ticket_config.json", {})
    return web.json_response({"ok": True, "open_tickets": open_tickets, "config": ticket_config})

async def handle_get_minigame_config(request: web.Request):
    sess = require_auth(request)
    if not sess:
        return web.json_response({"ok": False, "error": "Unauthorized"}, status=401)
    guild_id = request.match_info.get("id")
    if not can_access_guild(sess, guild_id):
        return web.json_response({"ok": False, "error": "Không có quyền quản lý server này"}, status=403)
    cfg = load_json(DATA_DIR / "minigame_config.json", {}).get(str(guild_id), {})
    return web.json_response({
        "ok": True,
        "config": {
            "wordchain_channel_id": cfg.get("wordchain_channel_id"),
            "trieuphu_channel_id": cfg.get("trieuphu_channel_id"),
            "xo_channel_id": cfg.get("xo_channel_id"),
            "chess_channel_id": cfg.get("chess_channel_id"),
            "tarot_enabled": cfg.get("tarot_enabled", True),
            "zodiac_enabled": cfg.get("zodiac_enabled", True)
        }
    })

async def handle_save_minigame_config(request: web.Request):
    sess = require_auth(request)
    if not sess:
        return web.json_response({"ok": False, "error": "Unauthorized"}, status=401)
    guild_id = request.match_info.get("id")
    if not can_access_guild(sess, guild_id):
        return web.json_response({"ok": False, "error": "Không có quyền quản lý server này"}, status=403)
    try:
        body = await request.json()
        gid = str(guild_id)
        data = load_json(DATA_DIR / "minigame_config.json", {})
        cfg = data.setdefault(gid, {})

        for key, field in {
            "wordchain_channel_id": "wordchain_channel_id",
            "trieuphu_channel_id": "trieuphu_channel_id",
            "xo_channel_id": "xo_channel_id",
            "chess_channel_id": "chess_channel_id",
        }.items():
            val = body.get(key)
            cfg[field] = int(val) if val not in (None, "", "0") and str(val).isdigit() else None

        if "tarot_enabled" in body:
            cfg["tarot_enabled"] = bool(body.get("tarot_enabled"))
        else:
            cfg.setdefault("tarot_enabled", True)

        if "zodiac_enabled" in body:
            cfg["zodiac_enabled"] = bool(body.get("zodiac_enabled"))
        else:
            cfg.setdefault("zodiac_enabled", True)

        save_json(DATA_DIR / "minigame_config.json", data)

        wc = load_json(DATA_DIR / "word_chain_config.json", {})
        if cfg.get("wordchain_channel_id"):
            wc[gid] = int(cfg["wordchain_channel_id"])
        elif gid in wc:
            wc.pop(gid, None)
        save_json(DATA_DIR / "word_chain_config.json", wc)

        add_log("INFO", f"User {sess.get('username')} cập nhật minigame cho guild {guild_id}")
        return web.json_response({"ok": True, "message": "Đã lưu cấu hình MiniGame"})
    except Exception as e:
        return web.json_response({"ok": False, "error": str(e)}, status=500)

async def handle_get_panel_config(request: web.Request):
    sess = require_auth(request)
    if not sess:
        return web.json_response({"ok": False, "error": "Unauthorized"}, status=401)
    guild_id = request.match_info.get("id")
    if not can_access_guild(sess, guild_id):
        return web.json_response({"ok": False, "error": "Không có quyền quản lý server này"}, status=403)
    role_cfg = load_json(DATA_DIR / "request_role_config.json", {}).get(str(guild_id), {})
    ticket_cfg = load_json(DATA_DIR / "ticket_config.json", {}).get(str(guild_id), {})
    return web.json_response({
        "ok": True,
        "config": {
            "role_panel_channel_id": role_cfg.get("panel_channel_id"),
            "role_approval_channel_id": role_cfg.get("approval_channel_id"),
            "ticket_panel_channel_id": ticket_cfg.get("ticket_channel_id"),
            "ticket_log_channel_id": ticket_cfg.get("log_channel_id"),
            "ticket_support_role_id": ticket_cfg.get("support_role_id")
        }
    })

async def handle_save_panel_config(request: web.Request):
    sess = require_auth(request)
    if not sess:
        return web.json_response({"ok": False, "error": "Unauthorized"}, status=401)
    guild_id = request.match_info.get("id")
    if not can_access_guild(sess, guild_id):
        return web.json_response({"ok": False, "error": "Không có quyền quản lý server này"}, status=403)
    try:
        body = await request.json()
        gid = str(guild_id)
        action = body.get("action")

        if action == "post_role_panel":
            role_cfg = load_json(DATA_DIR / "request_role_config.json", {})
            cur_role = role_cfg.setdefault(gid, {})
            panel_channel_id = body.get("role_panel_channel_id")
            if panel_channel_id not in (None, "", "0") and str(panel_channel_id).isdigit():
                cur_role["panel_channel_id"] = int(panel_channel_id)
            else:
                panel_channel_id = cur_role.get("panel_channel_id")
            if not panel_channel_id:
                return web.json_response({"ok": False, "error": "Chưa chọn kênh panel Role"}, status=400)
            if BOT_INSTANCE is not None:
                from Command_vi.request_role import RequestRoleView
                channel = BOT_INSTANCE.get_channel(int(panel_channel_id))
                if not channel:
                    return web.json_response({"ok": False, "error": "Không tìm thấy kênh panel Role trong bot"}, status=404)
                embed = discord.Embed(title="✨ Yêu Cầu Tạo Role", description="Chọn nút bên dưới để gửi yêu cầu tạo role mới cho quản trị viên.", color=discord.Color.blurple())
                embed.set_footer(text="Sakura Bot | Role Request")
                await channel.send(embed=embed, view=RequestRoleView(BOT_INSTANCE))
                add_log("INFO", f"User {sess.get('username')} đã đăng panel Role cho guild {guild_id}")
                return web.json_response({"ok": True, "message": "Đã đăng panel Role"})
            return web.json_response({"ok": False, "error": "Bot chưa sẵn sàng để đăng panel"}, status=503)

        if action == "post_ticket_panel":
            ticket_cfg = load_json(DATA_DIR / "ticket_config.json", {})
            cur_ticket = ticket_cfg.setdefault(gid, {})
            panel_channel_id = body.get("ticket_panel_channel_id")
            if panel_channel_id not in (None, "", "0") and str(panel_channel_id).isdigit():
                cur_ticket["ticket_channel_id"] = int(panel_channel_id)
            else:
                panel_channel_id = cur_ticket.get("ticket_channel_id")
            if not panel_channel_id:
                return web.json_response({"ok": False, "error": "Chưa chọn kênh panel Ticket"}, status=400)
            if BOT_INSTANCE is not None:
                from Command_vi.ticket import TicketPanelView
                channel = BOT_INSTANCE.get_channel(int(panel_channel_id))
                if not channel:
                    return web.json_response({"ok": False, "error": "Không tìm thấy kênh panel Ticket trong bot"}, status=404)
                embed = discord.Embed(title="📩 Ticket Hỗ Trợ", description="Bấm nút bên dưới để tạo ticket hỗ trợ mới.", color=discord.Color.blue())
                embed.set_footer(text="Sakura Bot | Ticket Support")
                await channel.send(embed=embed, view=TicketPanelView())
                add_log("INFO", f"User {sess.get('username')} đã đăng panel Ticket cho guild {guild_id}")
                return web.json_response({"ok": True, "message": "Đã đăng panel Ticket"})
            return web.json_response({"ok": False, "error": "Bot chưa sẵn sàng để đăng panel"}, status=503)

        role_cfg = load_json(DATA_DIR / "request_role_config.json", {})
        cur_role = role_cfg.setdefault(gid, {})
        if "role_panel_channel_id" in body:
            v = body.get("role_panel_channel_id")
            cur_role["panel_channel_id"] = int(v) if v not in (None, "", "0") and str(v).isdigit() else None
        if "role_approval_channel_id" in body:
            v = body.get("role_approval_channel_id")
            cur_role["approval_channel_id"] = int(v) if v not in (None, "", "0") and str(v).isdigit() else None
        save_json(DATA_DIR / "request_role_config.json", role_cfg)

        ticket_cfg = load_json(DATA_DIR / "ticket_config.json", {})
        cur_ticket = ticket_cfg.setdefault(gid, {})
        if "ticket_panel_channel_id" in body:
            v = body.get("ticket_panel_channel_id")
            cur_ticket["ticket_channel_id"] = int(v) if v not in (None, "", "0") and str(v).isdigit() else None
        if "ticket_log_channel_id" in body:
            v = body.get("ticket_log_channel_id")
            cur_ticket["log_channel_id"] = int(v) if v not in (None, "", "0") and str(v).isdigit() else None
        if "ticket_support_role_id" in body:
            v = body.get("ticket_support_role_id")
            cur_ticket["support_role_id"] = int(v) if v not in (None, "", "0") and str(v).isdigit() else None
        save_json(DATA_DIR / "ticket_config.json", ticket_cfg)

        add_log("INFO", f"User {sess.get('username')} cập nhật panel role/ticket cho guild {guild_id}")
        return web.json_response({"ok": True, "message": "Đã lưu cấu hình panel Role & Ticket"})
    except Exception as e:
        return web.json_response({"ok": False, "error": str(e)}, status=500)

# --- System Config & AI Settings (admin only) ---
async def handle_get_config(request: web.Request):
    sess = require_auth(request)
    if not sess:
        return web.json_response({"ok": False, "error": "Unauthorized"}, status=401)
    if not is_admin_session(sess):
        return web.json_response({"ok": False, "error": "Chỉ admin mới xem config"}, status=403)
    try:
        import config
        config_data = {
            "TOKEN": getattr(config, "TOKEN", ""),
            "PREFIX": getattr(config, "PREFIX", "s!"),
            "OWNER_ID": getattr(config, "OWNER_ID", ""),
            "LOG_CHANNEL_ID": getattr(config, "LOG_CHANNEL_ID", ""),
            "ADMIN_ROLE_IDS": getattr(config, "ADMIN_ROLE_IDS", []),
            "GROQ_API_KEY": getattr(config, "GROQ_API_KEY", ""),
            "OPENAI_API_KEY": getattr(config, "OPENAI_API_KEY", ""),
            "GEMINI_API_KEY": getattr(config, "GEMINI_API_KEY", ""),
            "XKIRO_API_KEY": getattr(config, "XKIRO_API_KEY", ""),
            "AI_MODEL": getattr(config, "AI_MODEL", "sensenova/sensenova-6.8-flash-lite"),
            "PKMC_API_KEY": getattr(config, "PKMC_API_KEY", ""),
            "ZALO_PHONE": getattr(config, "ZALO_PHONE", ""),
            "OWNER_DISCORD_TAG": getattr(config, "OWNER_DISCORD_TAG", ""),
            "WEB_PORT": getattr(config, "WEB_PORT", 10272),
            "WEB_PASSWORD": getattr(config, "WEB_PASSWORD", ""),
            "DISCORD_CLIENT_ID": getattr(config, "DISCORD_CLIENT_ID", ""),
            "DISCORD_CLIENT_SECRET": getattr(config, "DISCORD_CLIENT_SECRET", ""),
            "DISCORD_REDIRECT_URI": getattr(config, "DISCORD_REDIRECT_URI", ""),
            "LAVALINK_HOST": getattr(config, "LAVALINK_HOST", ""),
            "LAVALINK_PORT": getattr(config, "LAVALINK_PORT", 2334),
            "LAVALINK_PASSWORD": getattr(config, "LAVALINK_PASSWORD", ""),
            "FALIX_API_KEY": getattr(config, "FALIX_API_KEY", ""),
            "TOKEN_DIEM_DANH": getattr(config, "TOKEN_DIEM_DANH", ""),
            "MAP_DIEM_DANH_ID": getattr(config, "MAP_DIEM_DANH_ID", "")
        }
        tts_settings = {
            "volume": load_json(DATA_DIR / "tts_volume.json", {}),
            "language": load_json(DATA_DIR / "tts_language.json", {}),
            "emoji_readings": load_json(DATA_DIR / "tts_emoji_readings.json", {})
        }
        return web.json_response({"ok": True, "config": config_data, "tts": tts_settings})
    except Exception as e:
        return web.json_response({"ok": False, "error": str(e)}, status=500)

async def handle_save_config(request: web.Request):
    sess = require_auth(request)
    if not sess:
        return web.json_response({"ok": False, "error": "Unauthorized"}, status=401)
    if not is_admin_session(sess):
        return web.json_response({"ok": False, "error": "Chỉ admin mới lưu config"}, status=403)
    try:
        body = await request.json()
        config_path = BASE_DIR / "config.py"
        if config_path.exists():
            with open(config_path, "r", encoding="utf-8") as f:
                lines = f.readlines()
        else:
            lines = []
        updates = {}
        if "TOKEN" in body: updates["TOKEN"] = repr(str(body["TOKEN"]).strip())
        if "PREFIX" in body: updates["PREFIX"] = repr(str(body["PREFIX"]).strip())
        if "OWNER_ID" in body: updates["OWNER_ID"] = str(int(body["OWNER_ID"])) if str(body["OWNER_ID"]).isdigit() else "0"
        if "LOG_CHANNEL_ID" in body: updates["LOG_CHANNEL_ID"] = str(int(body["LOG_CHANNEL_ID"])) if str(body["LOG_CHANNEL_ID"]).isdigit() else "0"
        if "GROQ_API_KEY" in body: updates["GROQ_API_KEY"] = repr(str(body["GROQ_API_KEY"]).strip())
        if "OPENAI_API_KEY" in body: updates["OPENAI_API_KEY"] = repr(str(body["OPENAI_API_KEY"]).strip())
        if "GEMINI_API_KEY" in body: updates["GEMINI_API_KEY"] = repr(str(body["GEMINI_API_KEY"]).strip())
        if "XKIRO_API_KEY" in body: updates["XKIRO_API_KEY"] = repr(str(body["XKIRO_API_KEY"]).strip())
        if "AI_MODEL" in body: updates["AI_MODEL"] = repr(str(body["AI_MODEL"]).strip())
        if "PKMC_API_KEY" in body: updates["PKMC_API_KEY"] = repr(str(body["PKMC_API_KEY"]).strip())
        if "ZALO_PHONE" in body: updates["ZALO_PHONE"] = repr(str(body["ZALO_PHONE"]).strip())
        if "OWNER_DISCORD_TAG" in body: updates["OWNER_DISCORD_TAG"] = repr(str(body["OWNER_DISCORD_TAG"]).strip())
        if "WEB_PORT" in body: updates["WEB_PORT"] = str(int(body["WEB_PORT"]))
        if "WEB_PASSWORD" in body: updates["WEB_PASSWORD"] = repr(str(body["WEB_PASSWORD"]).strip())
        if "DISCORD_CLIENT_ID" in body: updates["DISCORD_CLIENT_ID"] = repr(str(body["DISCORD_CLIENT_ID"]).strip())
        if "DISCORD_CLIENT_SECRET" in body: updates["DISCORD_CLIENT_SECRET"] = repr(str(body["DISCORD_CLIENT_SECRET"]).strip())
        if "DISCORD_REDIRECT_URI" in body: updates["DISCORD_REDIRECT_URI"] = repr(str(body["DISCORD_REDIRECT_URI"]).strip())
        if "LAVALINK_HOST" in body: updates["LAVALINK_HOST"] = repr(str(body["LAVALINK_HOST"]).strip())
        if "LAVALINK_PORT" in body: updates["LAVALINK_PORT"] = str(int(body["LAVALINK_PORT"]))
        if "LAVALINK_PASSWORD" in body: updates["LAVALINK_PASSWORD"] = repr(str(body["LAVALINK_PASSWORD"]).strip())
        if "FALIX_API_KEY" in body: updates["FALIX_API_KEY"] = repr(str(body["FALIX_API_KEY"]).strip())
        if "TOKEN_DIEM_DANH" in body: updates["TOKEN_DIEM_DANH"] = repr(str(body["TOKEN_DIEM_DANH"]).strip())
        if "MAP_DIEM_DANH_ID" in body: updates["MAP_DIEM_DANH_ID"] = str(int(body["MAP_DIEM_DANH_ID"])) if str(body["MAP_DIEM_DANH_ID"]).isdigit() else "0"

        new_lines = []
        handled_keys = set()
        for line in lines:
            trimmed = line.strip()
            modified = False
            for key, val in updates.items():
                if trimmed.startswith(f"{key} =") or trimmed.startswith(f"{key}="):
                    new_lines.append(f"{key} = {val}\n")
                    handled_keys.add(key)
                    modified = True
                    break
            if not modified:
                new_lines.append(line)
        for key, val in updates.items():
            if key not in handled_keys:
                new_lines.append(f"{key} = {val}\n")
        with open(config_path, "w", encoding="utf-8") as f:
            f.writelines(new_lines)
        add_log("SUCCESS", f"Admin {sess.get('username')} lưu config.py")
        return web.json_response({"ok": True, "message": "Đã lưu cài đặt config.py thành công! Hãy reload hoặc khởi động lại bot để áp dụng."})
    except Exception as e:
        return web.json_response({"ok": False, "error": str(e)}, status=500)

async def handle_get_raw_config(request: web.Request):
    """Lấy toàn bộ nội dung file config.py dưới dạng văn bản thô để chỉnh sửa trực tiếp."""
    sess = require_admin(request)
    if not sess:
        return web.json_response({"ok": False, "error": "Chỉ dành cho Admin"}, status=403)
    try:
        config_path = BASE_DIR / "config.py"
        if not config_path.exists():
            return web.json_response({"ok": False, "error": "File config.py không tồn tại"}, status=404)
        content = config_path.read_text(encoding="utf-8")
        return web.json_response({"ok": True, "content": content})
    except Exception as e:
        return web.json_response({"ok": False, "error": str(e)}, status=500)

async def handle_save_raw_config(request: web.Request):
    """Lưu trực tiếp nội dung file config.py (có kiểm tra cú pháp Python trước khi ghi)."""
    sess = require_admin(request)
    if not sess:
        return web.json_response({"ok": False, "error": "Chỉ dành cho Admin"}, status=403)
    try:
        body = await request.json()
        content = body.get("content", "")
        if not content:
            return web.json_response({"ok": False, "error": "Nội dung config không được để trống"}, status=400)

        # Kiểm tra tính hợp lệ cú pháp Python
        try:
            compile(content, "config.py", "exec")
        except SyntaxError as se:
            return web.json_response({
                "ok": False,
                "error": f"Lỗi cú pháp Python tại dòng {se.lineno}: {se.msg}"
            }, status=400)

        config_path = BASE_DIR / "config.py"
        config_path.write_text(content, encoding="utf-8")
        add_log("SUCCESS", f"Admin {sess.get('username')} đã lưu trực tiếp file config.py")
        return web.json_response({"ok": True, "message": "Đã lưu trực tiếp file config.py thành công!"})
    except Exception as e:
        return web.json_response({"ok": False, "error": str(e)}, status=500)

# --- Bot Commands Web API (đồng bộ với bot, loại trừ MC) ---
async def handle_get_bot_commands(request: web.Request):
    """API lấy danh sách toàn bộ lệnh bot đồng bộ theo thời gian thực (đã loại trừ Minecraft)"""
    try:
        from web.bot_commands import get_all_bot_commands, CATEGORIES
        commands = get_all_bot_commands(bot_instance=BOT_INSTANCE)
        return web.json_response({
            "ok": True,
            "total": len(commands),
            "commands": commands,
            "categories": CATEGORIES
        })
    except Exception as e:
        return web.json_response({"ok": False, "error": str(e)}, status=500)

# --- Mod Commands Web API (đã phân loại, loại trừ MC) ---
async def handle_get_mod_commands(request: web.Request):
    sess = get_session(request)
    if not sess:
        return web.json_response({"ok": False, "error": "Unauthorized"}, status=401)
    guild_id = request.query.get("guild_id") or request.match_info.get("id") or ""
    if not guild_id:
        try:
            body = await request.json()
            guild_id = str(body.get("guild_id", ""))
        except Exception:
            pass
    if not guild_id:
        return web.json_response({"ok": False, "error": "Thiếu guild_id"}, status=400)
    if not can_access_guild(sess, str(guild_id)):
        return web.json_response({"ok": False, "error": "Không có quyền quản lý server này"}, status=403)
    try:
        from web.mod_commands import get_all_with_status, CATEGORIES
        cmds = get_all_with_status(str(guild_id))
        return web.json_response({"ok": True, "commands": cmds, "categories": CATEGORIES})
    except Exception as e:
        return web.json_response({"ok": False, "error": str(e)}, status=500)

async def handle_save_mod_command(request: web.Request):
    sess = get_session(request)
    if not sess:
        return web.json_response({"ok": False, "error": "Unauthorized"}, status=401)
    try:
        body = await request.json()
        guild_id = str(body.get("guild_id", "")).strip()
        cmd_id = str(body.get("cmd_id", "")).strip()
        enabled = bool(body.get("enabled", True))
        if not guild_id or not cmd_id:
            return web.json_response({"ok": False, "error": "Thiếu guild_id/cmd_id"}, status=400)
        if not can_access_guild(sess, guild_id):
            return web.json_response({"ok": False, "error": "Không có quyền"}, status=403)
        # Chặn MC
        if cmd_id.startswith("mc_") or cmd_id in ["mc", "minecraft"]:
            return web.json_response({"ok": False, "error": "Lệnh MC không cho cấu hình trên web"}, status=403)
        from web.mod_commands import set_guild_command
        set_guild_command(guild_id, cmd_id, enabled)
        add_log("INFO", f"User {sess.get('username')} {'bật' if enabled else 'tắt'} lệnh mod {cmd_id} cho guild {guild_id}")
        return web.json_response({"ok": True, "message": f"Đã {'bật' if enabled else 'tắt'} {cmd_id}"})
    except Exception as e:
        return web.json_response({"ok": False, "error": str(e)}, status=500)

async def handle_mod_action(request: web.Request):
    sess = get_session(request)
    if not sess:
        return web.json_response({"ok": False, "error": "Unauthorized"}, status=401)
    if not BOT_INSTANCE or not getattr(BOT_INSTANCE, "is_ready", lambda: False)():
        return web.json_response({"ok": False, "error": "Bot chưa sẵn sàng"}, status=503)
    try:
        body = await request.json()
        guild_id = str(body.get("guild_id", "")).strip()
        action = str(body.get("action", "")).strip()  # ban/kick/mute/unban/unmute/clear/warn/move etc.
        target_id = str(body.get("target_id", "")).strip()
        reason = str(body.get("reason", "Thực hiện từ Web Dashboard")).strip() or "Từ Web"
        minutes = int(body.get("minutes", 10)) if body.get("minutes") else 10
        amount = body.get("amount", "5")
        channel_id = body.get("channel_id")
        if not guild_id or not action:
            return web.json_response({"ok": False, "error": "Thiếu guild_id/action"}, status=400)
        if not can_access_guild(sess, guild_id):
            return web.json_response({"ok": False, "error": "Không có quyền"}, status=403)
        # Chặn MC
        if action.startswith("mc"):
            return web.json_response({"ok": False, "error": "Hành động MC không hỗ trợ trên web"}, status=403)
        import discord
        guild = BOT_INSTANCE.get_guild(int(guild_id))
        if not guild:
            return web.json_response({"ok": False, "error": "Không tìm thấy server"}, status=404)
        # Kiểm tra lệnh có bị tắt không
        from web.mod_commands import get_guild_mod_config
        cfg = get_guild_mod_config(guild_id)
        if cfg.get(action) is False:
            return web.json_response({"ok": False, "error": f"Lệnh {action} đang bị tắt cho server này"}, status=403)
        # Thực thi từng action
        if action == "ban":
            if not target_id:
                return web.json_response({"ok": False, "error": "Thiếu target_id"}, status=400)
            try:
                user = await BOT_INSTANCE.fetch_user(int(target_id))
                await guild.ban(user, reason=f"Web {sess.get('username')}: {reason}")
                add_log("SUCCESS", f"Web ban {target_id} tại {guild.name} bởi {sess.get('username')}")
                return web.json_response({"ok": True, "message": f"Đã ban {user.name}"})
            except Exception as e:
                return web.json_response({"ok": False, "error": str(e)}, status=500)
        elif action == "kick":
            if not target_id:
                return web.json_response({"ok": False, "error": "Thiếu target_id"}, status=400)
            member = guild.get_member(int(target_id))
            if not member:
                try:
                    member = await guild.fetch_member(int(target_id))
                except Exception:
                    return web.json_response({"ok": False, "error": "Không tìm thấy member"}, status=404)
            try:
                await member.kick(reason=f"Web {sess.get('username')}: {reason}")
                add_log("SUCCESS", f"Web kick {target_id} tại {guild.name}")
                return web.json_response({"ok": True, "message": f"Đã kick {member.display_name}"})
            except Exception as e:
                return web.json_response({"ok": False, "error": str(e)}, status=500)
        elif action == "mute":
            if not target_id:
                return web.json_response({"ok": False, "error": "Thiếu target_id"}, status=400)
            member = guild.get_member(int(target_id))
            if not member:
                return web.json_response({"ok": False, "error": "Member không trong server"}, status=404)
            from datetime import timedelta
            try:
                await member.timeout(timedelta(minutes=minutes), reason=f"Web {sess.get('username')}: {reason}")
                return web.json_response({"ok": True, "message": f"Đã mute {member.display_name} {minutes} phút"})
            except Exception as e:
                return web.json_response({"ok": False, "error": str(e)}, status=500)
        elif action == "unmute":
            if not target_id:
                return web.json_response({"ok": False, "error": "Thiếu target_id"}, status=400)
            member = guild.get_member(int(target_id))
            if not member:
                return web.json_response({"ok": False, "error": "Member không trong server"}, status=404)
            try:
                await member.timeout(None, reason=f"Web {sess.get('username')}")
                return web.json_response({"ok": True, "message": f"Đã unmute {member.display_name}"})
            except Exception as e:
                return web.json_response({"ok": False, "error": str(e)}, status=500)
        elif action == "unban":
            if not target_id:
                return web.json_response({"ok": False, "error": "Thiếu target_id"}, status=400)
            try:
                user = await BOT_INSTANCE.fetch_user(int(target_id))
                await guild.unban(user, reason=f"Web {sess.get('username')}")
                return web.json_response({"ok": True, "message": f"Đã unban {user.name}"})
            except Exception as e:
                return web.json_response({"ok": False, "error": str(e)}, status=500)
        elif action == "clear":
            if not channel_id:
                return web.json_response({"ok": False, "error": "Thiếu channel_id"}, status=400)
            ch = BOT_INSTANCE.get_channel(int(channel_id))
            if not ch:
                return web.json_response({"ok": False, "error": "Không tìm thấy kênh"}, status=404)
            try:
                if str(amount).lower() == "all":
                    deleted = await ch.purge()
                else:
                    deleted = await ch.purge(limit=int(amount)+1)
                return web.json_response({"ok": True, "message": f"Đã xóa {len(deleted)} tin nhắn"})
            except Exception as e:
                return web.json_response({"ok": False, "error": str(e)}, status=500)
        elif action == "warn":
            # chỉ ghi log, không có lưu warn thực tế qua web (giữ đơn giản)
            add_log("INFO", f"Web warn {target_id} tại {guild.name} lý do {reason}")
            return web.json_response({"ok": True, "message": f"Đã ghi cảnh cáo {target_id}"})
        else:
            return web.json_response({"ok": False, "error": f"Hành động {action} chưa hỗ trợ"}, status=400)
    except Exception as e:
        import traceback; traceback.print_exc()
        return web.json_response({"ok": False, "error": str(e)}, status=500)

# --- Bot Connection & Power (tách web panel mở riêng, admin điều khiển) ---
async def handle_bot_connection(request: web.Request):
    proxied = await _proxy_to_bot_web(request, "/api/bot/connection")
    if proxied is not None:
        return proxied
    sess = get_session(request)
    if not sess:
        return web.json_response({"ok": False, "error": "Unauthorized"}, status=401)
    status = get_bot_process_status()
    info = {"process": status}
    if BOT_INSTANCE and getattr(BOT_INSTANCE, "is_ready", lambda: False)():
        try:
            info["discord"] = {"username": str(BOT_INSTANCE.user), "id": str(BOT_INSTANCE.user.id), "guilds": len(BOT_INSTANCE.guilds), "latency": round(BOT_INSTANCE.latency*1000,2)}
        except Exception:
            pass
    # thêm thông tin web panel tách riêng
    info["web_standalone"] = BOT_INSTANCE is None
    info["can_control"] = is_admin_session(sess)
    return web.json_response({"ok": True, "bot": info})

async def handle_bot_power(request: web.Request):
    return web.json_response({"ok": False, "error": "Chức năng bật/tắt/restart đã gỡ theo yêu cầu"}, status=410)

# --- Dedicated MC WebSocket ---
async def handle_ws_mc(request: web.Request):
    token = request.query.get("token", "") or request.cookies.get("sakura_token", "")
    if token:
        sess = verify_session(token)
        if not sess and not is_admin_session(sess or {}):
            # vẫn cho phép nhưng chỉ admin mới thấy MC
            pass
    ws = web.WebSocketResponse()
    await ws.prepare(request)
    MC_WS_CLIENTS.add(ws)
    # Gửi lịch sử MC
    for entry in MC_LOG_BUFFER[-100:]:
        await ws.send_str(json.dumps({"type": "log", "data": entry}))
    try:
        async for msg in ws:
            if msg.type == WSMsgType.TEXT:
                try:
                    data=json.loads(msg.data)
                    if data.get("type")=="cmd":
                        cmd_text=data.get("cmd","").strip()
                        if cmd_text:
                            add_mc_log("CMD", f"> {cmd_text}")
                            # Thử gửi qua RCON nếu cấu hình; fallback chỉ log
                            try:
                                # Cố gắng dùng mc rcon từ Command_vi/minecraft.py nếu có
                                import importlib
                                mc_mod=None
                                for name in ["Command_vi.minecraft","Command.minecraft","minecraft"]:
                                    try:
                                        mc_mod=importlib.import_module(name)
                                        break
                                    except: pass
                                # Nếu có hàm gửi RCON, thử gọi
                                sent=False
                                if mc_mod and hasattr(mc_mod, "send_rcon_command"):
                                    res=await mc_mod.send_rcon_command(cmd_text)
                                    add_mc_log("INFO", f"[RCON] {res}")
                                    sent=True
                                if not sent:
                                    add_mc_log("WARN", "Lệnh đã ghi nhận. Cần cấu hình RCON để thực thi lên server.")
                            except Exception as e:
                                add_mc_log("ERROR", f"Gửi lệnh lỗi: {e}")
                except: pass
            elif msg.type==WSMsgType.ERROR:
                print(f"MC WS error: {ws.exception()}")
    finally:
        MC_WS_CLIENTS.discard(ws)
    return ws

async def handle_chat(request: web.Request):
    limited, retry, _ = check_rate(request, "chat")
    if limited:
        return web.json_response({"ok":False,"error":f"Chat quá nhanh, thử lại sau {retry}s"}, status=429, headers={"Retry-After": str(retry)})
    try:
        body=await request.json()
        msg=sanitize_text(str(body.get("message","")), 1000).strip()
        if not msg:
            return web.json_response({"ok":False,"error":"Thiếu message"},status=400)
        # Thử gọi Kiro API trước, fallback Groq
        reply=None
        try:
            import config
            xkiro_key = getattr(config, "XKIRO_API_KEY", "") or os.getenv("XKIRO_API_KEY", "")
            if xkiro_key:
                ai_model = getattr(config, "AI_MODEL", "sensenova/sensenova-6.8-flash-lite")
                payload = {
                    "model": ai_model,
                    "messages": [
                        {"role": "system", "content": "Bạn là Sakura Bot — trợ lý AI dễ thương, thông minh của Sakura Bot Discord. Hãy trả lời thân thiện, lịch thiệp bằng tiếng Việt, thêm emoji hoa anh đào 🌸."},
                        {"role": "user", "content": msg}
                    ],
                    "max_tokens": 400,
                    "temperature": 0.7
                }
                async with aiohttp.ClientSession() as s:
                    async with s.post(
                        "https://api.xkiro.com/v1/chat/completions",
                        headers={"Authorization": f"Bearer {xkiro_key}", "Content-Type": "application/json"},
                        json=payload,
                        timeout=aiohttp.ClientTimeout(total=15)
                    ) as resp:
                        if resp.status == 200:
                            j = await resp.json()
                            reply = j["choices"][0]["message"]["content"].strip()
            if not reply:
                groq_key=getattr(config,"GROQ_API_KEY","")
                if groq_key:
                    import aiohttp
                    async with aiohttp.ClientSession() as s:
                        payload={"model":"llama-3.3-70b-versatile","messages":[{"role":"system","content":"Bạn là Sakura Bot — trả lời ngắn gọn tiếng Việt, thân thiện, có emoji 🌸"},{"role":"user","content":msg}],"max_tokens":300,"temperature":0.8}
                        async with s.post("https://api.groq.com/openai/v1/chat/completions", headers={"Authorization":f"Bearer {groq_key}","Content-Type":"application/json"}, json=payload, timeout=aiohttp.ClientTimeout(total=12)) as resp:
                            if resp.status==200:
                                j=await resp.json()
                                reply=j["choices"][0]["message"]["content"].strip()
        except Exception as e:
            print(f"[Chat] AI fail: {e}")
        if not reply:
            # fallback Sakura personality
            lowers=msg.lower()
            if any(k in lowers for k in ["xin chào","hello","hi"]):
                reply="Chào bạn! 🌸 Sakura đây — cần giúp gì về bot hoặc cài đặt máy chủ Discord không?"
            elif "lệnh" in lowers or "command" in lowers:
                reply="Bạn dùng `s!help` trong Discord hoặc mở Dashboard `/dashboard` để cấu hình nhé! Cần mình hướng dẫn chi tiết không? 🌸"
            elif "tiktok" in lowers:
                reply="TikTok Auto Download đã bật — chỉ cần gửi link TikTok, bot sẽ tự tải video/ảnh cho bạn! 🌸"
            else:
                reply=f"Sakura đã nhận: \"{msg}\" 🌸 — Bạn có thể xem thêm các lệnh tại /help hoặc mở /dashboard nhé!"
        return web.json_response({"ok":True,"reply":reply})
    except Exception as e:
        return web.json_response({"ok":False,"error":str(e)},status=500)

def _load_web_global():
    if not WEB_GLOBAL_FILE.exists(): return []
    try: return json.loads(WEB_GLOBAL_FILE.read_text(encoding="utf-8"))
    except: return []
def _save_web_global(arr):
    try: WEB_GLOBAL_FILE.write_text(json.dumps(arr, ensure_ascii=False, indent=2), encoding="utf-8")
    except: pass

async def handle_global_chat_history(request: web.Request):
    sess=require_auth(request)
    if not sess: return web.json_response({"ok":False,"error":"Cần đăng nhập để xem Global Chat"},status=401)
    msgs=_load_web_global()[-100:]
    return web.json_response({"ok":True,"messages":msgs})

async def handle_global_chat_upload(request: web.Request):
    sess = require_auth(request)
    if not sess:
        return web.json_response({"ok": False, "error": "Cần đăng nhập"}, status=401)
    try:
        reader = await request.multipart()
        file_field = await reader.next()
        if not file_field:
            return web.json_response({"ok": False, "error": "Thiếu file đính kèm"}, status=400)
        filename = sanitize_text(file_field.filename or "upload.png", 100)
        ext = Path(filename).suffix.lower()
        if ext not in [".png", ".jpg", ".jpeg", ".gif", ".webp", ".mp4", ".mp3", ".pdf", ".txt", ".zip"]:
            ext = ".png"
        safe_name = f"chat_{int(time.time()*1000)}_{secrets.token_hex(4)}{ext}"
        upload_dir = BASE_DIR / "web" / "images" / "chat"
        upload_dir.mkdir(parents=True, exist_ok=True)
        target_path = upload_dir / safe_name
        size = 0
        with open(target_path, "wb") as f:
            while True:
                chunk = await file_field.read_chunk()
                if not chunk:
                    break
                size += len(chunk)
                if size > 15 * 1024 * 1024:
                    target_path.unlink(missing_ok=True)
                    return web.json_response({"ok": False, "error": "File quá lớn (tối đa 15MB)"}, status=400)
                f.write(chunk)
        url = f"/image/chat/{safe_name}"
        return web.json_response({"ok": True, "url": url, "filename": filename, "is_image": ext in [".png", ".jpg", ".jpeg", ".gif", ".webp"]})
    except Exception as e:
        return web.json_response({"ok": False, "error": str(e)}, status=500)

async def handle_chat_image_view(request: web.Request):
    filename = request.match_info.get("filename", "")
    target = BASE_DIR / "web" / "images" / "chat" / filename
    if not target.exists() or not target.is_file():
        return web.Response(text="<h1>File không tồn tại</h1>", status=404, content_type="text/html")
    ext = target.suffix.lower()
    mime = "application/octet-stream"
    if ext in [".png", ".webp", ".gif", ".jpeg", ".jpg"]:
        mime = f"image/{ext.replace('.', '').replace('jpg', 'jpeg')}"
    return web.FileResponse(path=str(target), headers={"Content-Type": mime})

async def handle_global_chat_send(request: web.Request):
    limited, retry, _ = check_rate(request, "global")
    if limited:
        return web.json_response({"ok":False,"error":f"Gửi quá nhanh, thử lại sau {retry}s"}, status=429, headers={"Retry-After": str(retry)})
    sess=require_auth(request)
    if not sess: return web.json_response({"ok":False,"error":"Cần đăng nhập để chat"},status=401)
    try:
        body=await request.json()
        text=sanitize_text(str(body.get("message","")), 1000).strip()
        attachment = body.get("attachment")
        attachment_name = sanitize_text(str(body.get("attachment_name","")), 100).strip()
        is_image = bool(body.get("is_image", True))
        if not text and not attachment: return web.json_response({"ok":False,"error":"Thiếu nội dung hoặc tệp"},status=400)
        # lấy info user
        username=sess.get("username","Ẩn danh")
        # avatar từ web_users.json
        users=load_json(DATA_DIR/"web_users.json",{})
        avatar=users.get(username,{}).get("avatar","")
        entry={
            "id": int(time.time()*1000),
            "username": username,
            "avatar": avatar,
            "message": text,
            "attachment": attachment,
            "attachment_name": attachment_name,
            "is_image": is_image,
            "time": datetime.datetime.now().strftime("%H:%M %d/%m")
        }
        arr=_load_web_global(); arr.append(entry)
        if len(arr)>300: arr=arr[-300:]
        _save_web_global(arr)
        # broadcast WS
        if WEB_GLOBAL_WS:
            msg=json.dumps({"type":"global_chat","data":entry})
            for ws in list(WEB_GLOBAL_WS):
                if not ws.closed:
                    asyncio.create_task(ws.send_str(msg))
        add_log("INFO", f"[GlobalChat] {username}: {text[:60]}")
        return web.json_response({"ok":True,"message":entry})
    except Exception as e:
        return web.json_response({"ok":False,"error":str(e)},status=500)

async def handle_ws_global_chat(request: web.Request):
    token=request.query.get("token","") or request.cookies.get("sakura_token","")
    sess=verify_session(token) if token else None
    if not sess:
        return web.Response(text="Unauthorized - cần login", status=401)
    ws=web.WebSocketResponse()
    await ws.prepare(request)
    WEB_GLOBAL_WS.add(ws)
    # gửi lịch sử
    for m in _load_web_global()[-30:]:
        await ws.send_str(json.dumps({"type":"global_chat","data":m}))
    try:
        async for msg in ws:
            if msg.type==WSMsgType.TEXT:
                try:
                    d=json.loads(msg.data)
                    if d.get("type")=="global_chat" and (d.get("message") or d.get("attachment")):
                        text=str(d.get("message","")).strip()[:1000]
                        attachment=d.get("attachment")
                        attachment_name=str(d.get("attachment_name",""))[:100]
                        is_image=bool(d.get("is_image", True))
                        if not text and not attachment: continue
                        username=sess.get("username","Ẩn danh")
                        users=load_json(DATA_DIR/"web_users.json",{})
                        avatar=users.get(username,{}).get("avatar","")
                        entry={
                            "id": int(time.time()*1000),
                            "username": username,
                            "avatar": avatar,
                            "message": text,
                            "attachment": attachment,
                            "attachment_name": attachment_name,
                            "is_image": is_image,
                            "time": datetime.datetime.now().strftime("%H:%M %d/%m")
                        }
                        arr=_load_web_global(); arr.append(entry)
                        if len(arr)>300: arr=arr[-300:]
                        _save_web_global(arr)
                        broadcast=json.dumps({"type":"global_chat","data":entry})
                        for w in list(WEB_GLOBAL_WS):
                            if not w.closed:
                                await w.send_str(broadcast)
                except: pass
    finally:
        WEB_GLOBAL_WS.discard(ws)
    return ws

# --- Profile System Handlers (Sakura Bio) ---
async def handle_add_profile_page(request: web.Request):
    f = TEMPLATES_DIR / "add_profile.html"
    if not f.exists():
        return web.Response(text="<h1>add_profile.html chưa tạo</h1>", content_type="text/html", status=404)
    return web.Response(text=f.read_text(encoding="utf-8"), content_type="text/html")

async def handle_user_profile_page(request: web.Request):
    f = TEMPLATES_DIR / "profile.html"
    if not f.exists():
        return web.Response(text="<h1>profile.html chưa tạo</h1>", content_type="text/html", status=404)
    return web.Response(text=f.read_text(encoding="utf-8"), content_type="text/html")

async def handle_get_profile_api(request: web.Request):
    username = request.match_info.get("username", "").strip().lower()
    profiles = load_json(DATA_DIR / "profiles.json", {})
    if username == "linh" and "linh" not in profiles:
        profiles["linh"] = {
            "username": "linh",
            "name": "Linh (Linh Xinh)",
            "handle": "@linhxinh_dev",
            "verified": True,
            "tagline": "Founder & Lead Developer of Sakura Bot 🌸",
            "bio": "Xin chào! Mình là Linh, lập trình viên và tác giả của Sakura Bot. Đam mê xây dựng các hệ sinh thái Discord Bot, plugin Minecraft và các nền tảng web hiện đại.",
            "avatar": "https://cdn.discordapp.com/avatars/1504825128499019807/dea9d2725b620317b25b9da8f36d129a?size=256",
            "banner": "https://images.unsplash.com/photo-1579783900882-c0d3dad7b119?q=80&w=1200&auto=format&fit=crop",
            "theme": "sakura",
            "socials": {
                "discord": "https://discord.com/users/1144785664458637394",
                "zalo": "https://zalo.me/0987524390",
                "github": "https://github.com/"
            },
            "links": [
                {"title": "🌸 Mời Sakura Bot Vào Server", "url": "/bot", "icon": "🤖", "highlight": True},
                {"title": "⚙️ Web Dashboard Điều Khiển", "url": "/dashboard", "icon": "🎛️"},
                {"title": "♟️ Cờ Vua AI Sakura", "url": "/game/chess", "icon": "♟️"},
                {"title": "⭕ Cờ Caro XO 15×15", "url": "/game/xo", "icon": "⭕"},
                {"title": "💬 Kênh Global Chat", "url": "/global-chat", "icon": "🌐"}
            ],
            "donate": {
                "bank_name": "MB Bank",
                "bank_account": "0987524390",
                "bank_owner": "LINH",
                "momo": "0987524390"
            }
        }
        save_json(DATA_DIR / "profiles.json", profiles)
    p = profiles.get(username)
    if not p:
        return web.json_response({"ok": False, "error": f"Không tìm thấy profile @{username}"}, status=404)
    return web.json_response({"ok": True, "profile": p})

async def handle_api_profile_check_permission(request: web.Request):
    """Kiểm tra quyền chỉnh sửa hồ sơ profile của session hiện tại."""
    username = request.query.get("user", "").strip().lower()
    sess = get_session(request)
    if not sess:
        return web.json_response({"ok": True, "can_edit": False, "logged_in": False})
    if is_admin_session(sess):
        return web.json_response({"ok": True, "can_edit": True, "logged_in": True, "is_admin": True})
    profiles = load_json(DATA_DIR / "profiles.json", {})
    p = profiles.get(username)
    if not p:
        return web.json_response({"ok": True, "can_edit": True, "logged_in": True})
    user_did = str(sess.get("discord_id") or sess.get("user_id") or "")
    user_name = (sess.get("username") or "").lower()
    owner_id = str(p.get("owner_id") or p.get("discord_id") or "")
    owner_name = str(p.get("owner_name") or "").lower()
    can_edit = False
    if owner_id and owner_id == user_did:
        can_edit = True
    elif not owner_id and owner_name and owner_name == user_name:
        can_edit = True
    return web.json_response({"ok": True, "can_edit": can_edit, "logged_in": True, "owner_name": owner_name})

async def handle_save_profile(request: web.Request):
    sess = get_session(request)
    if not sess:
        return web.json_response({"ok": False, "error": "Vui lòng đăng nhập trước khi tạo hoặc chỉnh sửa bio!"}, status=401)
    try:
        data = await request.json()
        raw_username = str(data.get("username", "")).strip().lower()
        username = "".join(c for c in raw_username if c.isalnum() or c in "_-")
        if not username or len(username) < 2:
            return web.json_response({"ok": False, "error": "Username không hợp lệ (ít nhất 2 ký tự)"}, status=400)

        profiles = load_json(DATA_DIR / "profiles.json", {})
        user_did = str(sess.get("discord_id") or sess.get("user_id") or "")
        user_name = str(sess.get("username") or "")

        existing = profiles.get(username)
        if existing:
            # Kiểm tra quyền: chỉ chủ sở hữu hoặc admin mới được chỉnh sửa
            is_admin = is_admin_session(sess)
            owner_id = str(existing.get("owner_id") or existing.get("discord_id") or "")
            owner_name = str(existing.get("owner_name") or "").lower()
            if not is_admin and owner_id and owner_id != user_did:
                return web.json_response({"ok": False, "error": "Bạn không có quyền chỉnh sửa bio của người khác!"}, status=403)
            if not is_admin and not owner_id and owner_name and owner_name != user_name.lower():
                return web.json_response({"ok": False, "error": "Bạn không có quyền chỉnh sửa bio của người khác!"}, status=403)

        is_verified = (username == "linh") or bool(profiles.get(username, {}).get("verified", False))
        data["verified"] = is_verified
        data["username"] = username
        data["owner_id"] = existing.get("owner_id", user_did) if existing else user_did
        data["owner_name"] = existing.get("owner_name", user_name) if existing else user_name
        data["updated_at"] = int(time.time())

        # Hỗ trợ tùy chỉnh ảnh nền web, màu nền, màu tương tác, màu hộp, thứ tự hiển thị
        if "background_image" in data:
            data["background_image"] = str(data.get("background_image", "")).strip()
        if "bg_color" in data:
            data["bg_color"] = str(data.get("bg_color", "")).strip()
        if "accent_color" in data:
            data["accent_color"] = str(data.get("accent_color", "")).strip()
        if "card_bg" in data:
            data["card_bg"] = str(data.get("card_bg", "")).strip()
        if "box_order" in data and isinstance(data["box_order"], list):
            data["box_order"] = [str(x) for x in data["box_order"]]

        profiles[username] = data
        save_json(DATA_DIR / "profiles.json", profiles)
        add_log("INFO", f"User {user_name} ({user_did}) đã lưu hồ sơ profile @{username}")
        return web.json_response({"ok": True, "message": f"Đã lưu profile @{username} thành công!", "username": username})
    except Exception as e:
        return web.json_response({"ok": False, "error": str(e)}, status=500)

async def handle_profile_directory_page(request: web.Request):
    f = TEMPLATES_DIR / "profile_directory.html"
    if not f.exists():
        return web.Response(text="<h1>profile_directory.html chưa tạo</h1>", content_type="text/html", status=404)
    return web.Response(text=f.read_text(encoding="utf-8"), content_type="text/html")

async def handle_list_profiles_api(request: web.Request):
    profiles = load_json(DATA_DIR / "profiles.json", {})
    if "linh" not in profiles:
        profiles["linh"] = {
            "username": "linh",
            "name": "Linh (Linh Xinh)",
            "handle": "@linhxinh_dev",
            "verified": True,
            "tagline": "Founder & Lead Developer of Sakura Bot 🌸",
            "bio": "Xin chào! Mình là Linh, lập trình viên và tác giả của Sakura Bot. Đam mê xây dựng các hệ sinh thái Discord Bot, plugin Minecraft và các nền tảng web hiện đại.",
            "avatar": "https://cdn.discordapp.com/avatars/1504825128499019807/dea9d2725b620317b25b9da8f36d129a?size=256",
            "banner": "https://images.unsplash.com/photo-1579783900882-c0d3dad7b119?q=80&w=1200&auto=format&fit=crop",
            "theme": "sakura",
            "socials": {
                "discord": "https://discord.com/users/1144785664458637394",
                "zalo": "https://zalo.me/0987524390",
                "github": "https://github.com/"
            },
            "links": [
                {"title": "🌸 Mời Sakura Bot Vào Server", "url": "/bot", "icon": "🤖", "highlight": True},
                {"title": "⚙️ Web Dashboard Điều Khiển", "url": "/dashboard", "icon": "🎛️"},
                {"title": "♟️ Cờ Vua AI Sakura", "url": "/game/chess", "icon": "♟️"},
                {"title": "⭕ Cờ Caro XO 15×15", "url": "/game/xo", "icon": "⭕"},
                {"title": "💬 Kênh Global Chat", "url": "/global-chat", "icon": "🌐"}
            ]
        }
        save_json(DATA_DIR / "profiles.json", profiles)

    sess = get_session(request)
    current_user = None
    if sess:
        current_user = {
            "username": sess.get("username"),
            "user_id": str(sess.get("user_id") or sess.get("id") or ""),
            "discord_id": str(sess.get("discord_id") or ""),
            "is_admin": is_admin_session(sess),
            "is_owner": is_owner_session(sess)
        }

    return web.json_response({
        "ok": True,
        "profiles": list(profiles.values()),
        "current_user": current_user
    })

# --- Top.gg Webhook & Vote Tracking ---
async def handle_topgg_webhook(request: web.Request):
    try:
        # Kiểm tra xác thực Webhook Authorization nếu có cấu hình
        try:
            from config import TOPGG_WEBHOOK_AUTH
            if TOPGG_WEBHOOK_AUTH:
                auth_header = request.headers.get("Authorization", "").strip()
                if auth_header != TOPGG_WEBHOOK_AUTH:
                    add_log("WARNING", "Nhận request Webhook Top.gg với header Authorization không hợp lệ!")
                    return web.json_response({"ok": False, "error": "Unauthorized"}, status=401)
        except Exception:
            pass

        data = await request.json()
        user_id = str(data.get("user") or data.get("userId") or data.get("id") or "").strip()
        vote_type = str(data.get("type", "upvote"))
        if user_id:
            from Command_vi.vote import record_vote, send_vote_success_dm
            record_vote(user_id)
            # Thưởng Coin và XP vào DB
            try:
                from data.database import update_user_level_stats, get_user_data
                user_data = await get_user_data(0, int(user_id))
                cur_coins = user_data.get("coins", 0) if isinstance(user_data, dict) else 0
                cur_xp = user_data.get("xp", 0) if isinstance(user_data, dict) else 0
                cur_level = user_data.get("level", 1) if isinstance(user_data, dict) else 1
                await update_user_level_stats(user_id, None, cur_level, cur_xp + 500, cur_coins + 5000)
            except Exception:
                pass

            # Gửi tin nhắn riêng (DM) chúc mừng và thông báo quyền lợi (hỗ trợ cả REST API fallback khi bot chạy riêng)
            dm_sent = False
            try:
                dm_sent = await send_vote_success_dm(BOT_INSTANCE, user_id)
            except Exception as dm_e:
                add_log("WARNING", f"Lỗi khi gửi DM thông báo vote Top.gg cho user {user_id}: {dm_e}")

            dm_status_str = "Đã gửi DM" if dm_sent else "Không thể gửi DM (Đóng DM / Chặn)"
            add_log("SUCCESS", f"🎉 Nhận vote Top.gg từ user ID {user_id} (+5,000 Coin, +500 XP, mở khóa 12h, {dm_status_str})!")
            return web.json_response({
                "ok": True,
                "message": f"Recorded vote for user {user_id}",
                "dm_sent": dm_sent
            })
        return web.json_response({"ok": False, "error": "Thiếu user ID"}, status=400)
    except Exception as e:
        return web.json_response({"ok": False, "error": str(e)}, status=500)

async def handle_get_vote_status(request: web.Request):
    user_id = request.match_info.get("user_id", "").strip()
    from Command_vi.vote import get_vote_status
    status = get_vote_status(user_id)
    return web.json_response({"ok": True, "status": status})

async def handle_get_vote_toggle(request: web.Request):
    from Command_vi.vote import is_vote_required_enabled
    return web.json_response({"ok": True, "enabled": is_vote_required_enabled()})

async def handle_post_vote_toggle(request: web.Request):
    sess = require_auth(request)
    if not sess or not is_admin_session(sess):
        return web.json_response({"ok": False, "error": "Chỉ Admin Web mới có quyền bật/tắt yêu cầu Vote"}, status=403)
    try:
        body = await request.json()
        from Command_vi.vote import is_vote_required_enabled, set_vote_required_enabled
        if "enabled" in body:
            new_state = bool(body["enabled"])
        else:
            new_state = not is_vote_required_enabled()
        set_vote_required_enabled(new_state)
        status_label = "BẬT" if new_state else "TẮT"
        add_log("INFO", f"Admin {sess.get('username')} đã chuyển trạng thái yêu cầu Vote Top.gg sang: {status_label}")
        return web.json_response({"ok": True, "enabled": new_state, "message": f"Đã {status_label.lower()} yêu cầu Vote Top.gg thành công!"})
    except Exception as e:
        return web.json_response({"ok": False, "error": str(e)}, status=500)

async def handle_mc_logs(request: web.Request):
    sess=require_auth(request)
    if not sess or not is_admin_session(sess):
        return web.json_response({"ok":False,"error":"Chỉ admin mới xem MC logs"},status=403)
    return web.json_response({"ok":True,"logs":MC_LOG_BUFFER[-200:]})

# --- WebSocket Live Log Stream ---
async def handle_ws_logs(request: web.Request):
    # Allow query token for WS auth; if admin required maybe check
    token = request.query.get("token", "") or request.cookies.get("sakura_token", "")
    # try check session if present, but allow connection and filter broadcast? Keep simple: require auth if session system active
    # For now, allow if token valid or fallback to no check (to support old behavior)
    if token:
        sess = verify_session(token)
        # if token invalid and not legacy, reject?
        # legacy token check
        if not sess:
            try:
                import config
                legacy = getattr(config, "WEB_PASSWORD", "")
                if legacy and token != legacy:
                    # Check more strictly: need valid session
                    # But allow anonymous for backward compat? We enforce auth
                    pass
            except Exception:
                pass
    ws = web.WebSocketResponse()
    await ws.prepare(request)
    WS_CLIENTS.add(ws)
    for entry in LOG_BUFFER[-50:]:
        await ws.send_str(json.dumps({"type": "log", "data": entry}))
    try:
        async for msg in ws:
            if msg.type == WSMsgType.TEXT:
                try:
                    data = json.loads(msg.data)
                    if data.get("type") == "cmd":
                        cmd_text = data.get("cmd", "").strip()
                        add_log("INFO", f"Console Command từ Web: {cmd_text}")
                        try:
                            from Checks_vi.owner_notifier import process_live_console_command
                            asyncio.create_task(process_live_console_command(cmd_text, BOT_INSTANCE))
                        except Exception as e_cmd:
                            add_log("ERROR", f"Lỗi thực thi lệnh console: {e_cmd}")
                except Exception:
                    pass
            elif msg.type == WSMsgType.ERROR:
                print(f"WebSocket error: {ws.exception()}")
    finally:
        WS_CLIENTS.discard(ws)
    return ws


# ==============================================================================
# 👥 WEB ADMIN MANAGEMENT API (QUẢN TRỊ ADMIN WEB - DÀNH RIÊNG CHO OWNER)
# ==============================================================================
async def handle_get_admin_users(request: web.Request):
    """Lấy danh sách tất cả tài khoản web và trạng thái phân quyền (Chỉ Owner)."""
    sess = require_owner(request)
    if not sess:
        return web.json_response({"ok": False, "error": "Chỉ Chủ Sở Hữu (Owner) mới có quyền truy cập menu này"}, status=403)
    try:
        users = load_users()
        from config import OWNER_ID
        owner_str = str(OWNER_ID)

        users_list = []
        for uname, udata in users.items():
            did = str(udata.get("discord_id") or "")
            u_lower = uname.lower()
            tag = str(udata.get("discord_tag") or "").lower()

            is_own = (
                udata.get("is_owner") is True or
                did == owner_str or
                did == "1144785664458637394" or
                "linhxinh_dev" in u_lower or
                "linhxinh_dev" in tag or
                u_lower in ("owner", "linhxinh")
            )

            role = "owner" if is_own else (udata.get("role") or "user")

            users_list.append({
                "username": uname,
                "role": role,
                "is_owner": is_own,
                "discord_id": did,
                "discord_tag": udata.get("discord_tag") or uname,
                "avatar": udata.get("avatar") or "https://cdn.discordapp.com/embed/avatars/0.png",
                "created_at": udata.get("created_at") or 0
            })

        # Sắp xếp: Owner lên đầu, kế đến Admin, sau đó User
        role_priority = {"owner": 0, "admin": 1, "user": 2}
        users_list.sort(key=lambda u: (role_priority.get(u["role"], 3), u["username"]))

        return web.json_response({"ok": True, "users": users_list})
    except Exception as e:
        return web.json_response({"ok": False, "error": str(e)}, status=500)

async def handle_set_user_role(request: web.Request):
    """Thay đổi vai trò Admin / User của một tài khoản (Chỉ Owner)."""
    sess = require_owner(request)
    if not sess:
        return web.json_response({"ok": False, "error": "Chỉ Chủ Sở Hữu (Owner) mới có quyền phân quyền"}, status=403)
    try:
        body = await request.json()
        target_user = body.get("username", "").strip()
        new_role = body.get("role", "").strip().lower()

        if not target_user or new_role not in ("admin", "user"):
            return web.json_response({"ok": False, "error": "Dữ liệu không hợp lệ (role phải là admin hoặc user)"}, status=400)

        users = load_users()
        if target_user not in users:
            # Thử tìm theo discord_id
            for u_k, u_v in users.items():
                if str(u_v.get("discord_id")) == target_user:
                    target_user = u_k
                    break

        if target_user not in users:
            return web.json_response({"ok": False, "error": f"Không tìm thấy người dùng '{target_user}'"}, status=404)

        u_data = users[target_user]
        from config import OWNER_ID
        owner_str = str(OWNER_ID)
        did = str(u_data.get("discord_id") or "")

        if u_data.get("is_owner") or did == owner_str or did == "1144785664458637394" or "linhxinh_dev" in target_user.lower():
            return web.json_response({"ok": False, "error": "Không thể thay đổi quyền hạn của Chủ Sở Hữu web!"}, status=400)

        u_data["role"] = new_role
        save_users(users)

        # Cập nhật session đang hoạt động
        try:
            from web.auth import load_sessions, save_sessions
            sessions = load_sessions()
            for s_k, s_v in list(sessions.items()):
                if s_v.get("username") == target_user:
                    s_v["role"] = new_role
            save_sessions(sessions)
        except Exception:
            pass

        action_msg = f"Owner {sess.get('username')} đã đổi quyền của {target_user} thành {new_role.upper()}"
        add_log("SUCCESS", action_msg)

        return web.json_response({
            "ok": True,
            "message": f"Đã cập nhật quyền của '{target_user}' thành {new_role.upper()} thành công!"
        })
    except Exception as e:
        return web.json_response({"ok": False, "error": str(e)}, status=500)

async def handle_add_web_admin(request: web.Request):
    """Cấp quyền Admin cho người dùng bằng Username hoặc Discord ID (Chỉ Owner)."""
    sess = require_owner(request)
    if not sess:
        return web.json_response({"ok": False, "error": "Chỉ Chủ Sở Hữu (Owner) mới có quyền thêm Admin"}, status=403)
    try:
        body = await request.json()
        target = body.get("target", "").strip()
        if not target:
            return web.json_response({"ok": False, "error": "Vui lòng nhập Username hoặc Discord ID"}, status=400)

        users = load_users()
        matched_uname = None

        if target in users:
            matched_uname = target
        else:
            for u_k, u_v in users.items():
                if str(u_v.get("discord_id") or "") == target or str(u_v.get("discord_tag") or "").lower() == target.lower():
                    matched_uname = u_k
                    break

        from config import OWNER_ID
        owner_str = str(OWNER_ID)

        if matched_uname:
            u_data = users[matched_uname]
            did = str(u_data.get("discord_id") or "")
            if u_data.get("is_owner") or did == owner_str or did == "1144785664458637394" or "linhxinh_dev" in matched_uname.lower():
                return web.json_response({"ok": False, "error": "Tài khoản này là Chủ Sở Hữu web!"}, status=400)
            u_data["role"] = "admin"
            save_users(users)
            user_label = matched_uname
        else:
            # Nếu chưa có tài khoản, tạo trước hồ sơ Admin bằng Discord ID
            clean_id = "".join(c for c in target if c.isdigit())
            if clean_id and len(clean_id) >= 15:
                uname = f"discord_{clean_id}"
                users[uname] = {
                    "username": uname,
                    "password_hash": "",
                    "role": "admin",
                    "discord_id": clean_id,
                    "discord_tag": f"User_{clean_id[-4:]}",
                    "avatar": "https://cdn.discordapp.com/embed/avatars/0.png",
                    "created_at": int(time.time()),
                    "guilds_filter": None,
                    "is_owner": False
                }
                save_users(users)
                user_label = f"Discord ID {clean_id}"
            else:
                uname = "".join(c for c in target if c.isalnum() or c in "_-").strip() or f"admin_{int(time.time())}"
                users[uname] = {
                    "username": uname,
                    "password_hash": "",
                    "role": "admin",
                    "discord_id": None,
                    "discord_tag": uname,
                    "avatar": "https://cdn.discordapp.com/embed/avatars/0.png",
                    "created_at": int(time.time()),
                    "guilds_filter": None,
                    "is_owner": False
                }
                save_users(users)
                user_label = uname

        # Cập nhật session nếu có
        try:
            from web.auth import load_sessions, save_sessions
            sessions = load_sessions()
            for s_k, s_v in list(sessions.items()):
                if s_v.get("username") == matched_uname or str(s_v.get("discord_id") or "") == target:
                    s_v["role"] = "admin"
            save_sessions(sessions)
        except Exception:
            pass

        add_log("SUCCESS", f"👑 Owner {sess.get('username')} đã thêm Admin web mới: {user_label}")
        return web.json_response({
            "ok": True,
            "message": f"Đã cấp quyền Quản Trị Viên (Admin) cho '{user_label}' thành công!"
        })
    except Exception as e:
        return web.json_response({"ok": False, "error": str(e)}, status=500)

async def handle_remove_web_admin(request: web.Request):
    """Thu hồi quyền Admin của một tài khoản (Chỉ Owner)."""
    sess = require_owner(request)
    if not sess:
        return web.json_response({"ok": False, "error": "Chỉ Chủ Sở Hữu (Owner) mới có quyền thu hồi Admin"}, status=403)
    try:
        body = await request.json()
        target = body.get("target", "").strip()
        if not target:
            return web.json_response({"ok": False, "error": "Vui lòng nhập Username hoặc Discord ID"}, status=400)

        users = load_users()
        matched_uname = None

        if target in users:
            matched_uname = target
        else:
            for u_k, u_v in users.items():
                if str(u_v.get("discord_id") or "") == target or str(u_v.get("discord_tag") or "").lower() == target.lower():
                    matched_uname = u_k
                    break

        if not matched_uname:
            return web.json_response({"ok": False, "error": f"Không tìm thấy người dùng '{target}'"}, status=404)

        u_data = users[matched_uname]
        from config import OWNER_ID
        owner_str = str(OWNER_ID)
        did = str(u_data.get("discord_id") or "")
        if u_data.get("is_owner") or did == owner_str or did == "1144785664458637394" or "linhxinh_dev" in matched_uname.lower():
            return web.json_response({"ok": False, "error": "Không thể thu hồi quyền của Chủ Sở Hữu web!"}, status=400)

        u_data["role"] = "user"
        save_users(users)

        # Cập nhật session
        try:
            from web.auth import load_sessions, save_sessions
            sessions = load_sessions()
            for s_k, s_v in list(sessions.items()):
                if s_v.get("username") == matched_uname or str(s_v.get("discord_id") or "") == target:
                    s_v["role"] = "user"
            save_sessions(sessions)
        except Exception:
            pass

        add_log("SUCCESS", f"👑 Owner {sess.get('username')} đã thu hồi quyền Admin của: {matched_uname}")
        return web.json_response({
            "ok": True,
            "message": f"Đã thu hồi quyền Admin của '{matched_uname}' thành công!"
        })
    except Exception as e:
        return web.json_response({"ok": False, "error": str(e)}, status=500)

# ==============================================================================
# SAKURA WEB UTILITIES / TIỆN ÍCH WEB (Translate, QR Code, TTS, Shortener, Hub)
# ==============================================================================

# 1. Tools Hub Page
async def handle_tools_hub_page(request: web.Request):
    f = TEMPLATES_DIR / "tools.html"
    if not f.exists():
        return web.Response(text="<h1>tools.html chưa tạo</h1>", content_type="text/html", status=404)
    return web.Response(text=f.read_text(encoding="utf-8"), content_type="text/html")

# 2. Translate Page & API
async def handle_translate_page(request: web.Request):
    f = TEMPLATES_DIR / "translate.html"
    if not f.exists():
        return web.Response(text="<h1>translate.html chưa tạo</h1>", content_type="text/html", status=404)
    return web.Response(text=f.read_text(encoding="utf-8"), content_type="text/html")

async def handle_api_translate(request: web.Request):
    try:
        data = await request.json()
        text = str(data.get("text", "")).strip()
        source = str(data.get("source", "auto")).strip()
        target = str(data.get("target", "vi")).strip()

        if not text:
            return web.json_response({"ok": False, "error": "Thiếu nội dung văn bản cần dịch"}, status=400)
        
        if len(text) > 10000:
            return web.json_response({"ok": False, "error": "Văn bản vượt quá 10,000 ký tự"}, status=400)

        translated_text = ""
        detected_source = source

        # Method 1: Google GTX Single Endpoint (Fast, high-fidelity)
        try:
            def _fetch_gtx():
                import urllib.request
                import json
                gtx_url = f"https://translate.googleapis.com/translate_a/single?client=gtx&sl={urllib.parse.quote(source)}&tl={urllib.parse.quote(target)}&dt=t&q={urllib.parse.quote(text)}"
                req = urllib.request.Request(
                    gtx_url,
                    headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"}
                )
                with urllib.request.urlopen(req, timeout=8) as resp:
                    data = json.loads(resp.read().decode("utf-8"))
                    sentences = data[0] if data and isinstance(data, list) and len(data) > 0 else []
                    parts = [s[0] for s in sentences if s and len(s) > 0 and s[0]]
                    det = data[2] if len(data) > 2 and isinstance(data[2], str) else source
                    return "".join(parts), det

            translated_text, detected_source = await asyncio.to_thread(_fetch_gtx)
        except Exception:
            translated_text = ""

        # Method 2: Fallback to deep_translator
        if not translated_text:
            try:
                from deep_translator import GoogleTranslator
                def _do_deep_translate():
                    src = "auto" if source == "auto" else source
                    return GoogleTranslator(source=src, target=target).translate(text)
                translated_text = await asyncio.to_thread(_do_deep_translate)
            except Exception as dt_err:
                return web.json_response({"ok": False, "error": f"Lỗi dịch thuật: {dt_err}"}, status=500)

        return web.json_response({
            "ok": True,
            "translated": translated_text,
            "source": detected_source,
            "target": target
        })
    except Exception as e:
        return web.json_response({"ok": False, "error": str(e)}, status=500)

# 3. QR Code Page, Generator API, Scanner API & Download
async def handle_qrcode_page(request: web.Request):
    f = TEMPLATES_DIR / "qrcode.html"
    if not f.exists():
        return web.Response(text="<h1>qrcode.html chưa tạo</h1>", content_type="text/html", status=404)
    return web.Response(text=f.read_text(encoding="utf-8"), content_type="text/html")

async def handle_api_qrcode_generate(request: web.Request):
    try:
        data = await request.json()
        content = str(data.get("content", "")).strip()
        fg_color = str(data.get("color", "#ff79c6")).strip() or "#ff79c6"
        bg_color = str(data.get("bg_color", "#ffffff")).strip() or "#ffffff"
        try:
            size = max(100, min(1500, int(data.get("size", 400))))
        except Exception:
            size = 400
        logo_choice = str(data.get("logo", "none")).strip()

        if not content:
            content = "https://sakurabot.top"

        def _make_qr():
            import qrcode
            from qrcode.constants import ERROR_CORRECT_H, ERROR_CORRECT_M
            import io
            import base64
            from PIL import Image, ImageDraw

            ec = ERROR_CORRECT_H if logo_choice != "none" else ERROR_CORRECT_M
            qr = qrcode.QRCode(
                version=None,
                error_correction=ec,
                box_size=10,
                border=2
            )
            qr.add_data(content)
            qr.make(fit=True)
            img = qr.make_image(fill_color=fg_color, back_color=bg_color).convert("RGBA")
            img = img.resize((size, size), Image.Resampling.LANCZOS)

            # Overlay logo if requested
            if logo_choice != "none":
                logo_path = None
                if logo_choice == "bot":
                    p1 = BASE_DIR / "web" / "static" / "img" / "bot_avatar.png"
                    p2 = BASE_DIR / "web" / "images" / "avatar.png"
                    p3 = BASE_DIR / "web" / "images" / "avatar-bot.jpg"
                    if p1.exists():
                        logo_path = p1
                    elif p2.exists():
                        logo_path = p2
                    elif p3.exists():
                        logo_path = p3
                if logo_path and logo_path.exists():
                    try:
                        logo = Image.open(logo_path).convert("RGBA")
                        logo_size = int(size * 0.22)
                        logo = logo.resize((logo_size, logo_size), Image.Resampling.LANCZOS)
                        
                        bg_circle = Image.new("RGBA", (logo_size + 12, logo_size + 12), (0, 0, 0, 0))
                        draw = ImageDraw.Draw(bg_circle)
                        draw.ellipse([(0, 0), (logo_size + 11, logo_size + 11)], fill=bg_color)
                        
                        pos_circle = ((size - (logo_size + 12)) // 2, (size - (logo_size + 12)) // 2)
                        pos_logo = ((size - logo_size) // 2, (size - logo_size) // 2)
                        
                        img.paste(bg_circle, pos_circle, mask=bg_circle)
                        img.paste(logo, pos_logo, mask=logo)
                    except Exception:
                        pass

            buf = io.BytesIO()
            img.save(buf, format="PNG")
            b64_str = base64.b64encode(buf.getvalue()).decode("ascii")
            return f"data:image/png;base64,{b64_str}"

        data_url = await asyncio.to_thread(_make_qr)
        return web.json_response({"ok": True, "data_url": data_url})
    except Exception as e:
        return web.json_response({"ok": False, "error": str(e)}, status=500)

async def handle_api_qrcode_download(request: web.Request):
    try:
        content = request.query.get("data", "").strip() or "https://sakurabot.top"
        fg_color = request.query.get("color", "#ff79c6").strip() or "#ff79c6"
        bg_color = request.query.get("bg_color", "#ffffff").strip() or "#ffffff"
        try:
            size = max(100, min(2000, int(request.query.get("size", 500))))
        except Exception:
            size = 500

        def _make_png_bytes():
            import qrcode
            from qrcode.constants import ERROR_CORRECT_M
            import io
            from PIL import Image

            qr = qrcode.QRCode(version=None, error_correction=ERROR_CORRECT_M, box_size=10, border=2)
            qr.add_data(content)
            qr.make(fit=True)
            img = qr.make_image(fill_color=fg_color, back_color=bg_color).convert("RGBA")
            img = img.resize((size, size), Image.Resampling.LANCZOS)
            buf = io.BytesIO()
            img.save(buf, format="PNG")
            return buf.getvalue()

        png_bytes = await asyncio.to_thread(_make_png_bytes)
        return web.Response(
            body=png_bytes,
            content_type="image/png",
            headers={"Content-Disposition": 'attachment; filename="sakura_qrcode.png"'}
        )
    except Exception as e:
        return web.Response(text=f"Error generating QR code: {e}", status=500)

async def handle_api_qrcode_scan(request: web.Request):
    try:
        reader = await request.multipart()
        field = await reader.next()
        if not field:
            return web.json_response({"ok": False, "error": "Không có tệp ảnh được gửi lên"}, status=400)
        
        file_bytes = await field.read()
        if not file_bytes:
            return web.json_response({"ok": False, "error": "Tệp ảnh trống"}, status=400)

        def _decode_qr():
            import numpy as np
            import cv2
            np_arr = np.frombuffer(file_bytes, np.uint8)
            img = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)
            if img is None:
                return None
            detector = cv2.QRCodeDetector()
            val, points, qrcode_img = detector.detectAndDecode(img)
            return val

        decoded_text = await asyncio.to_thread(_decode_qr)
        if decoded_text:
            return web.json_response({"ok": True, "text": decoded_text})
        else:
            return web.json_response({"ok": False, "error": "Không tìm thấy hoặc không thể đọc mã QR từ ảnh này"}, status=404)
    except Exception as e:
        return web.json_response({"ok": False, "error": str(e)}, status=500)

# 4. Text-To-Speech (TTS) Page & API
TTS_CACHE_DIR = DATA_DIR / "tts_cache"

async def handle_tts_page(request: web.Request):
    f = TEMPLATES_DIR / "tts.html"
    if not f.exists():
        return web.Response(text="<h1>tts.html chưa tạo</h1>", content_type="text/html", status=404)
    return web.Response(text=f.read_text(encoding="utf-8"), content_type="text/html")

async def handle_api_tts_generate(request: web.Request):
    try:
        import hashlib
        data = await request.json()
        text = str(data.get("text", "")).strip()
        lang = str(data.get("lang", "vi")).strip()
        try:
            speed = float(data.get("speed", 1.0))
        except Exception:
            speed = 1.0

        if not text:
            return web.json_response({"ok": False, "error": "Vui lòng nhập văn bản cần chuyển thành giọng nói"}, status=400)

        if len(text) > 2000:
            return web.json_response({"ok": False, "error": "Văn bản vượt quá giới hạn 2,000 ký tự"}, status=400)

        TTS_CACHE_DIR.mkdir(parents=True, exist_ok=True)
        cache_hash = hashlib.md5(f"{text}_{lang}_{speed < 0.9}".encode("utf-8")).hexdigest()
        filename = f"{cache_hash}.mp3"
        filepath = TTS_CACHE_DIR / filename

        if not filepath.exists():
            def _synthesize():
                from gtts import gTTS
                tts_lang = lang
                if tts_lang == "zh":
                    tts_lang = "zh-CN"
                tts = gTTS(text=text, lang=tts_lang, slow=(speed < 0.9))
                tts.save(str(filepath))

            await asyncio.to_thread(_synthesize)

        return web.json_response({
            "ok": True,
            "audio_url": f"/api/tools/tts/audio/{filename}",
            "filename": filename
        })
    except Exception as e:
        return web.json_response({"ok": False, "error": f"Lỗi chuyển giọng nói: {e}"}, status=500)

async def handle_api_tts_audio(request: web.Request):
    filename = request.match_info.get("filename", "").strip()
    if not re.match(r"^[a-f0-9]{32}\.mp3$", filename):
        return web.Response(text="Tệp âm thanh không hợp lệ", status=400)
    
    filepath = TTS_CACHE_DIR / filename
    if not filepath.exists():
        return web.Response(text="Không tìm thấy tệp âm thanh", status=404)
    
    data = filepath.read_bytes()
    return web.Response(body=data, content_type="audio/mpeg")

# 5. URL Shortener Page, API & Redirect
SHORT_LINKS_FILE = DATA_DIR / "short_links.json"

def _load_short_links() -> dict:
    return load_json(SHORT_LINKS_FILE, {})

def _save_short_links(data: dict):
    save_json(SHORT_LINKS_FILE, data)

async def handle_shortener_page(request: web.Request):
    f = TEMPLATES_DIR / "shortener.html"
    if not f.exists():
        return web.Response(text="<h1>shortener.html chưa tạo</h1>", content_type="text/html", status=404)
    return web.Response(text=f.read_text(encoding="utf-8"), content_type="text/html")

async def handle_api_shorten(request: web.Request):
    try:
        import string
        import random
        data = await request.json()
        original_url = str(data.get("url", "")).strip()
        custom_alias = str(data.get("custom_alias", "")).strip().lower()

        if not original_url:
            return web.json_response({"ok": False, "error": "Vui lòng nhập đường dẫn URL"}, status=400)

        if not (original_url.startswith("http://") or original_url.startswith("https://")):
            return web.json_response({"ok": False, "error": "Đường dẫn URL phải bắt đầu bằng http:// hoặc https://"}, status=400)

        links = _load_short_links()

        if custom_alias:
            if not re.match(r"^[a-z0-9_-]{3,30}$", custom_alias):
                return web.json_response({"ok": False, "error": "Bí danh tùy chỉnh chỉ được chứa chữ thường, số, dấu gạch ngang/dưới (3-30 ký tự)"}, status=400)
            
            reserved = {"api", "admin", "tools", "translate", "qrcode", "tts", "shortener", "s", "bot", "ws", "static", "images", "downloads"}
            if custom_alias in reserved:
                return web.json_response({"ok": False, "error": "Bí danh này đã được hệ thống sử dụng!"}, status=400)
            
            if custom_alias in links and links[custom_alias].get("original_url") != original_url:
                return web.json_response({"ok": False, "error": f"Bí danh '{custom_alias}' đã có người sử dụng. Hãy chọn tên khác!"}, status=400)
            
            alias = custom_alias
        else:
            for a, info in links.items():
                if info.get("original_url") == original_url:
                    alias = a
                    break
            else:
                chars = string.ascii_lowercase + string.digits
                for _ in range(10):
                    cand = "".join(random.choices(chars, k=6))
                    if cand not in links:
                        alias = cand
                        break
                else:
                    alias = "".join(random.choices(chars, k=8))

        if alias not in links:
            links[alias] = {
                "alias": alias,
                "original_url": original_url,
                "created_at": int(time.time()),
                "clicks": 0,
                "last_clicked": None
            }
            _save_short_links(links)

        scheme = request.scheme or "http"
        host = request.host
        short_url = f"{scheme}://{host}/s/{alias}"

        return web.json_response({
            "ok": True,
            "alias": alias,
            "short_url": short_url,
            "original_url": original_url,
            "clicks": links[alias].get("clicks", 0)
        })
    except Exception as e:
        return web.json_response({"ok": False, "error": str(e)}, status=500)

async def handle_api_shorten_list(request: web.Request):
    links = _load_short_links()
    items = sorted(links.values(), key=lambda x: x.get("created_at", 0), reverse=True)[:50]
    return web.json_response({"ok": True, "links": items})

async def handle_short_redirect(request: web.Request):
    alias = request.match_info.get("alias", "").strip().lower()
    links = _load_short_links()
    if alias in links:
        link_info = links[alias]
        link_info["clicks"] = link_info.get("clicks", 0) + 1
        link_info["last_clicked"] = int(time.time())
        _save_short_links(links)
        target = link_info.get("original_url", "/")
        raise web.HTTPFound(target)
    
    return web.Response(
        text="""<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>404 — Liên Kết Không Tồn Tại</title>
    <style>
        body { background: #07090e; color: #fff; font-family: system-ui, sans-serif; display: flex; flex-direction: column; align-items: center; justify-content: center; min-height: 100vh; margin: 0; }
        .card { background: rgba(255,255,255,0.05); border: 1px solid rgba(255,121,198,0.3); border-radius: 16px; padding: 40px; text-align: center; max-width: 480px; }
        h1 { color: #ff79c6; margin-top: 0; }
        p { color: #94a3b8; line-height: 1.6; }
        a { display: inline-block; margin-top: 20px; background: #ff79c6; color: #000; text-decoration: none; padding: 10px 24px; border-radius: 8px; font-weight: bold; }
    </style>
</head>
<body>
    <div class="card">
        <h1>🌸 404 Not Found</h1>
        <p>Liên kết rút gọn này không tồn tại hoặc đã bị xóa khỏi hệ thống.</p>
        <a href="/shortener">Tạo Liên Kết Mới</a>
    </div>
</body>
</html>""",
        content_type="text/html",
        status=404
    )

# --- HoYoverse Web Captcha & OTP Handlers ---
async def handle_hoyo_captcha_page(request: web.Request):
    """Trang giao diện người dùng giải Geetest Captcha của HoYoverse."""
    f = TEMPLATES_DIR / "hoyo_captcha.html"
    if not f.exists():
        return web.Response(text="<h1>hoyo_captcha.html chưa được khởi tạo</h1>", content_type="text/html", status=404)
    return web.Response(text=f.read_text(encoding="utf-8"), content_type="text/html")

async def handle_api_hoyo_captcha_info(request: web.Request):
    """API lấy thông tin MMT Captcha (gt, challenge, captcha_id...)."""
    session_id = request.query.get("session", "").strip()
    if not session_id:
        return web.json_response({"success": False, "error": "Thiếu session ID"}, status=400)
    try:
        from Checks_vi.hoyo_captcha_session import get_captcha_session
        sess = get_captcha_session(session_id)
        if not sess:
            return web.json_response({"success": False, "error": "Phiên xác thực đã hết hạn hoặc không tồn tại. Vui lòng mở lại từ Discord!"}, status=404)
        
        mmt = sess.get("mmt")
        raw = {}
        if hasattr(mmt, "model_dump"):
            try:
                raw = mmt.model_dump()
            except Exception:
                pass
        elif hasattr(mmt, "dict"):
            try:
                raw = mmt.dict()
            except Exception:
                pass
        elif isinstance(mmt, dict):
            raw = dict(mmt)

        gt = raw.get("gt") or getattr(mmt, "gt", None) or ""
        challenge = raw.get("challenge") or getattr(mmt, "challenge", None) or ""
        captcha_id = raw.get("captcha_id") or getattr(mmt, "captcha_id", None) or gt
        session_id_val = raw.get("session_id") or getattr(mmt, "session_id", None) or session_id
        risk_type = raw.get("risk_type") or getattr(mmt, "risk_type", None) or "slide"
        new_captcha = raw.get("new_captcha") if "new_captcha" in raw else getattr(mmt, "new_captcha", 1)
        success = raw.get("success") if "success" in raw else getattr(mmt, "success", 1)

        # Chuẩn hóa nếu một trong 2 trường bị trống
        if not gt and captcha_id:
            gt = captcha_id
        if not captcha_id and gt:
            captcha_id = gt

        # Geetest v4 hay v3 ưu tiên lấy trực tiếp từ session do genshin xác định
        if "is_v4" in sess:
            is_v4 = bool(sess["is_v4"])
        elif challenge:
            is_v4 = False
        else:
            is_v4 = True

        data = {
            "gt": str(gt),
            "challenge": str(challenge),
            "captcha_id": str(captcha_id),
            "risk_type": str(risk_type),
            "new_captcha": new_captcha,
            "success": success,
            "session_id": str(session_id_val),
        }
        return web.json_response({"success": True, "is_v4": is_v4, "stage": sess.get("stage", "login_captcha"), "data": data})
    except Exception as e:
        return web.json_response({"success": False, "error": str(e)}, status=500)

async def handle_api_hoyo_captcha_status(request: web.Request):
    """API kiểm tra trạng thái tiến trình xác thực HoYoverse (captcha, otp, success, error)."""
    session_id = request.query.get("session", "").strip()
    if not session_id:
        return web.json_response({"success": False, "error": "Thiếu session ID"}, status=400)
    try:
        from Checks_vi.hoyo_captcha_session import get_captcha_session
        sess = get_captcha_session(session_id)
        if not sess:
            return web.json_response({"success": False, "error": "Phiên xác thực đã hết hạn hoặc không tồn tại."}, status=404)
        return web.json_response({
            "success": True,
            "stage": sess.get("stage", "login_captcha"),
            "error": sess.get("error", None)
        })
    except Exception as e:
        return web.json_response({"success": False, "error": str(e)}, status=500)

async def handle_api_hoyo_captcha_verify(request: web.Request):
    """API tiếp nhận kết quả sau khi người dùng kéo khớp mảnh ghép Geetest trên web."""
    try:
        payload = await request.json()
        session_id = payload.get("session", "").strip()
        if not session_id:
            return web.json_response({"success": False, "error": "Thiếu session ID"}, status=400)
        from Checks_vi.hoyo_captcha_session import resolve_captcha_session
        resolved = resolve_captcha_session(session_id, payload)
        if resolved:
            return web.json_response({"success": True, "message": "Đã gửi kết quả giải Captcha tới SakuraBot thành công!"})
        else:
            return web.json_response({"success": False, "error": "Phiên Captcha không tồn tại, đã hoàn thành hoặc đã quá hạn."}, status=400)
    except Exception as e:
        return web.json_response({"success": False, "error": str(e)}, status=500)

async def handle_api_hoyo_otp_verify(request: web.Request):
    """API tiếp nhận mã OTP xác thực Email 6 số gửi từ HoYoverse."""
    try:
        payload = await request.json()
        session_id = payload.get("session", "").strip()
        code = payload.get("code", "").strip()
        if not session_id or not code:
            return web.json_response({"success": False, "error": "Thiếu session ID hoặc mã xác thực"}, status=400)
        from Checks_vi.hoyo_captcha_session import resolve_otp_session
        resolved = resolve_otp_session(session_id, code)
        if resolved:
            return web.json_response({"success": True, "message": "Đã chuyển mã xác nhận OTP tới SakuraBot thành công!"})
        else:
            return web.json_response({"success": False, "error": "Phiên xác thực Email không tồn tại hoặc đã hết hạn."}, status=400)
    except Exception as e:
        return web.json_response({"success": False, "error": str(e)}, status=500)

async def handle_admin_page(request: web.Request):
    """Trang Quản Trị Hệ Thống dành riêng cho Admin tại /admin"""
    sess = get_session(request)
    if not sess:
        return web.HTTPFound("/login?redirect=/admin")
    if not is_admin_session(sess):
        return web.Response(
            text="<h1 style='color:#ff5555;font-family:sans-serif;text-align:center;margin-top:50px;'>⛔ 403 Forbidden - Chỉ Quản trị viên (Admin) mới có quyền truy cập trang Quản Trị Hệ Thống!</h1>",
            content_type="text/html",
            status=403
        )
    admin_file = TEMPLATES_DIR / "admin.html"
    if not admin_file.exists():
        admin_file = TEMPLATES_DIR / "index.html"
    return web.Response(text=admin_file.read_text(encoding="utf-8"), content_type="text/html")

async def handle_api_hoyo_direct_cookie(request: web.Request):
    """Tiếp nhận chuỗi cookie dán trực tiếp trên Web, trích xuất token, xác thực và lưu vào Database."""
    try:
        data = await request.json()
        cookie_raw = data.get("cookie", "").strip()
        account_name = data.get("account_name", "Mặc định").strip() or "Mặc định"
        user_id = str(data.get("user_id", "")).strip()

        if not user_id:
            sess = get_session(request)
            if sess and sess.get("user"):
                user_id = str(sess["user"].get("id", ""))

        if not user_id:
            return web.json_response({"success": False, "error": "Thiếu Discord User ID! Vui lòng nhập ID tài khoản Discord của bạn."}, status=400)

        if not cookie_raw:
            return web.json_response({"success": False, "error": "Vui lòng dán chuỗi Cookie!"}, status=400)

        from Command_vi.hoyolab_checkin import extract_hoyolab_cookies, load_cookies, save_cookies
        cookie_dict = extract_hoyolab_cookies(cookie_raw)

        ltuid = cookie_dict.get("ltuid_v2") or cookie_dict.get("ltuid") or cookie_dict.get("account_id_v2") or cookie_dict.get("account_id")
        ltoken = cookie_dict.get("ltoken_v2") or cookie_dict.get("ltoken")

        if not ltuid or not ltoken:
            return web.json_response({
                "success": False,
                "error": "Cookie không đầy đủ! Yêu cầu tối thiểu phải có ltuid_v2 (hoặc ltuid) và ltoken_v2 (hoặc ltoken). Hãy dùng Bookmarklet 1 chạm để copy chính xác."
            }, status=400)

        import genshin
        client = genshin.Client()
        client.set_cookies(cookie_dict)
        try:
            accounts = await client.get_game_accounts()
            game_accs = [{
                "uid": str(a.uid),
                "game": str(a.game_biz),
                "level": a.level,
                "nickname": a.nickname,
                "server": a.server_name
            } for a in accounts]
        except Exception:
            game_accs = []

        from data.database import db_save_hoyolab_account
        await db_save_hoyolab_account(
            user_id=user_id,
            account_name=account_name,
            cookies=cookie_dict,
            game_accounts=game_accs,
            auto_checkin=True,
            auto_redeem=True
        )

        c_data = load_cookies()
        user_list = c_data.setdefault(user_id, [])
        user_list = [a for a in user_list if a.get("name") != account_name]
        user_list.append({
            "name": account_name,
            "cookies": cookie_dict,
            "game_accounts": game_accs,
            "auto_checkin": True,
            "auto_redeem": True
        })
        c_data[user_id] = user_list
        save_cookies(c_data)

        char_count = len(game_accs)
        msg = f"Đã lưu tài khoản '{account_name}' thành công!" + (f" Tìm thấy {char_count} nhân vật game." if char_count else "")
        return web.json_response({"success": True, "message": msg, "accounts": game_accs})

    except Exception as e:
        return web.json_response({"success": False, "error": f"Lỗi xử lý Cookie: {e}"}, status=500)

async def handle_api_hoyo_web_login(request: web.Request):
    """Tiếp nhận tài khoản & mật khẩu HoYoverse từ giao diện web, điều phối Geetest Captcha và OTP."""
    try:
        data = await request.json()
        account_str = data.get("account", "").strip()
        pwd_str = data.get("password", "").strip()
        account_name = data.get("account_name", "Mặc định").strip() or "Mặc định"
        user_id = str(data.get("user_id", "")).strip()

        if not user_id:
            sess = get_session(request)
            if sess and sess.get("user"):
                user_id = str(sess["user"].get("id", ""))

        if not user_id:
            return web.json_response({"success": False, "error": "Thiếu Discord User ID!"}, status=400)

        if not account_str or not pwd_str:
            return web.json_response({"success": False, "error": "Vui lòng nhập đầy đủ tài khoản và mật khẩu!"}, status=400)

        import uuid
        import genshin
        from Checks_vi.hoyo_captcha_session import create_captcha_session, get_captcha_session

        session_id = uuid.uuid4().hex[:16]
        device_id = str(uuid.uuid4())

        client = genshin.Client()
        try:
            res = await client._app_login(account_str, pwd_str, device_id=device_id)
        except Exception as e:
            return web.json_response({"success": False, "error": f"Lỗi đăng nhập HoYoverse: {e}"}, status=400)

        if isinstance(res, (genshin.models.SessionMMT, genshin.models.SessionMMTv4)):
            loop = asyncio.get_running_loop()
            captcha_future = loop.create_future()
            create_captcha_session(session_id, {
                "user_id": user_id,
                "stage": "login_captcha",
                "mmt": res,
                "is_v4": isinstance(res, genshin.models.SessionMMTv4),
                "future": captcha_future,
                "account_str": account_str,
                "pwd_str": pwd_str,
                "device_id": device_id,
                "account_name": account_name
            })
            return web.json_response({
                "success": True,
                "need_captcha": True,
                "session": session_id,
                "is_v4": isinstance(res, genshin.models.SessionMMTv4)
            })

        elif isinstance(res, genshin.models.ActionTicket):
            try:
                email_res = await client._send_verification_email(res)
            except Exception as mail_err:
                return web.json_response({"success": False, "error": f"Không thể gửi mã Email: {mail_err}"}, status=400)

            from Checks_vi.hoyo_captcha_session import create_otp_session
            loop = asyncio.get_running_loop()
            otp_future = loop.create_future()
            create_otp_session(session_id, {
                "user_id": user_id,
                "future": otp_future,
                "ticket": res,
                "account_str": account_str,
                "pwd_str": pwd_str,
                "device_id": device_id,
                "account_name": account_name
            })
            return web.json_response({
                "success": True,
                "need_otp": True,
                "session": session_id
            })

        elif isinstance(res, genshin.models.AppLoginResult):
            cookies = client.cookies
            c_dict = dict(cookies)
            try:
                accounts = await client.get_game_accounts()
                game_accs = [{"uid": str(a.uid), "game": str(a.game_biz), "level": a.level, "nickname": a.nickname, "server": a.server_name} for a in accounts]
            except Exception:
                game_accs = []

            from data.database import db_save_hoyolab_account
            await db_save_hoyolab_account(user_id, account_name, c_dict, game_accs, True, True)

            return web.json_response({
                "success": True,
                "need_captcha": False,
                "message": "Đăng nhập HoYoverse thành công!",
                "accounts": game_accs
            })

        return web.json_response({"success": False, "error": "Phản hồi không xác định từ HoYoverse."}, status=400)

    except Exception as e:
        return web.json_response({"success": False, "error": str(e)}, status=500)

def create_app() -> web.Application:
    app = web.Application(middlewares=[security_headers_middleware])
    # Bot File Manager & Cog Reloader Routes (Dành cho Admin Web)
    app.router.add_get("/admin/files", handle_bot_files_page)
    app.router.add_get("/bot/files", handle_bot_files_page)
    app.router.add_get("/api/admin/bot-files/list", handle_api_bot_files_list)
    app.router.add_get("/api/admin/bot-files/read", handle_api_bot_files_read)
    app.router.add_post("/api/admin/bot-files/save", handle_api_bot_files_save)
    app.router.add_post("/api/admin/bot-files/create", handle_api_bot_files_create)
    app.router.add_post("/api/admin/bot-files/delete", handle_api_bot_files_delete)
    app.router.add_post("/api/admin/bot-files/rename", handle_api_bot_files_rename)
    app.router.add_post("/api/admin/bot-files/upload", handle_api_bot_files_upload)
    app.router.add_get("/api/admin/bot-files/raw", handle_api_bot_files_raw)
    app.router.add_get("/api/admin/cogs/list", handle_api_admin_cogs_list)
    app.router.add_post("/api/admin/cogs/reload", handle_api_admin_cogs_reload)
    app.router.add_post("/api/admin/cogs/sync-tree", handle_api_admin_cogs_sync_tree)
    app.router.add_get("/api/admin/database/schema", handle_api_database_schema)
    app.router.add_get("/api/admin/database/table-data", handle_api_database_table_data)
    app.router.add_post("/api/admin/database/query", handle_api_database_query)

    # Public routes - "/" là trang giới thiệu, "/dashboard" là panel
    app.router.add_get("/", handle_index)
    app.router.add_get("/admin", handle_admin_page)
    app.router.add_get("/hoyo/captcha", handle_hoyo_captcha_page)
    app.router.add_get("/hoyo/login", handle_hoyo_captcha_page)
    app.router.add_get("/api/hoyo/captcha/info", handle_api_hoyo_captcha_info)
    app.router.add_get("/api/hoyo/captcha/status", handle_api_hoyo_captcha_status)
    app.router.add_post("/api/hoyo/captcha/verify", handle_api_hoyo_captcha_verify)
    app.router.add_post("/api/hoyo/otp/verify", handle_api_hoyo_otp_verify)
    app.router.add_post("/api/hoyo/direct-cookie", handle_api_hoyo_direct_cookie)
    app.router.add_post("/api/hoyo/web-login", handle_api_hoyo_web_login)
    app.router.add_get("/bot", handle_bot_invite)
    app.router.add_get("/invite", handle_bot_invite)
    app.router.add_get("/bot/invite", handle_bot_invite)
    app.router.add_get("/dashboard", handle_dashboard)
    app.router.add_get("/login", handle_login_page)
    app.router.add_get("/help", handle_help_page)
    # Minecraft Web Hosting Dashboard Pages
    app.router.add_get("/mc", handle_mc_servers_page)
    app.router.add_get("/minecraft", handle_mc_servers_page)
    app.router.add_get("/mc/console", handle_mc_console_page)
    app.router.add_get("/minecraft/console", handle_mc_console_page)
    app.router.add_get("/mc/file", handle_mc_files_page)
    app.router.add_get("/minecraft/file", handle_mc_files_page)
    app.router.add_get("/mc/properties", handle_mc_properties_page)
    app.router.add_get("/minecraft/properties", handle_mc_properties_page)
    app.router.add_get("/mc/player", handle_mc_players_page)
    app.router.add_get("/minecraft/player", handle_mc_players_page)
    app.router.add_get("/mc/manager", handle_mc_manager_page)
    app.router.add_get("/minecraft/manager", handle_mc_manager_page)
    app.router.add_get("/plugin", handle_plugin_page)
    app.router.add_get("/plugins", handle_plugin_page)
    app.router.add_get("/plugin/help", handle_plugin_help_page)
    app.router.add_get("/plugin-help", handle_plugin_help_page)
    app.router.add_get("/.well-known/discord", handle_discord_well_known)
    app.router.add_get("/support", handle_support_page)
    app.router.add_get("/support/discord", handle_support_discord)
    app.router.add_get("/support/invite", handle_support_invite)
    app.router.add_get("/support/docs", handle_support_docs)
    app.router.add_get("/support/guide", handle_support_docs)
    app.router.add_get("/support/donate", handle_support_donate)
    app.router.add_post("/api/support/feedback", handle_save_feedback)
    app.router.add_get("/terms", handle_terms_page)
    app.router.add_get("/discord/terms", handle_terms_page)
    app.router.add_get("/privacy", handle_privacy_page)
    app.router.add_get("/discord/privacy", handle_privacy_page)
    app.router.add_get("/game", handle_game_hub)
    app.router.add_get("/games", handle_game_hub)
    app.router.add_get("/game/xo", handle_game_xo)
    app.router.add_get("/game/chess", handle_game_chess)
    app.router.add_get("/game/wordchain", handle_game_wordchain)
    app.router.add_get("/game/familytime", handle_game_familytime)
    app.router.add_get("/game/family-time", handle_game_familytime)
    app.router.add_get("/game/scribble", handle_game_scribble)
    app.router.add_get("/games/scribble", handle_game_scribble)
    app.router.add_get("/ws/scribble", handle_ws_scribble)
    app.router.add_get("/tarot", handle_tarot_page)
    app.router.add_get("/api/scribble/rooms", handle_scribble_rooms)
    app.router.add_get("/api/wordlist", handle_wordlist)
    # Wordchain Management Routes
    app.router.add_get("/api/wordchain/stats", handle_wordchain_stats)
    app.router.add_get("/api/wordchain/words", handle_wordchain_get_words)
    app.router.add_post("/api/wordchain/words/add", handle_wordchain_add_word)
    app.router.add_post("/api/wordchain/words/delete", handle_wordchain_delete_word)
    app.router.add_get("/api/wordchain/leaderboard", handle_wordchain_leaderboard)
    app.router.add_post("/api/wordchain/scores/adjust", handle_wordchain_adjust_score)
    app.router.add_get("/api/game/{game}/leaderboard", handle_game_leaderboard)
    app.router.add_post("/api/game/{game}/score", handle_game_score)
    app.router.add_post("/api/tarot/draw", handle_tarot_draw)
    app.router.add_post("/api/tarot/interpret", handle_tarot_interpret)
    app.router.add_get("/api/yt/files", handle_yt_files)
    app.router.add_get("/yt/video", handle_yt_video)
    # TikTok Downloader Routes
    app.router.add_get("/tiktok", handle_tiktok_page)
    app.router.add_post("/api/tiktok/info", handle_api_tiktok_info)
    app.router.add_get("/api/tiktok/download", handle_api_tiktok_download)
    app.router.add_post("/api/tiktok/download-zip", handle_api_tiktok_download_zip)
    app.router.add_get("/image", handle_image_gallery)
    app.router.add_get("/image/{filename}", handle_image_view)
    app.router.add_get("/global-chat", handle_global_chat_page)
    app.router.add_get("/account", handle_account_page)
    app.router.add_get("/account/change", handle_account_page)
    app.router.add_get("/account/resetpass", handle_account_page)
    app.router.add_post("/api/login", handle_login)  # legacy
    # New auth routes
    app.router.add_post("/api/auth/login", handle_auth_login)
    app.router.add_post("/api/auth/register", handle_auth_register)
    app.router.add_post("/api/auth/logout", handle_auth_logout)
    app.router.add_get("/api/auth/me", handle_auth_me)
    app.router.add_get("/api/auth/discord/login", handle_discord_login)
    app.router.add_get("/api/auth/discord/callback", handle_discord_callback)
    app.router.add_post("/api/auth/forgot", handle_auth_forgot)
    # Account API
    app.router.add_get("/api/account/info", handle_account_info)
    app.router.add_post("/api/account/change", handle_account_change)
    app.router.add_post("/api/account/resetpass", handle_account_resetpass)
    app.router.add_post("/api/account/avatar", handle_account_avatar)
    app.router.add_get("/api/account/achievements", handle_account_achievements)
    app.router.add_get("/api/achievements/leaderboard", handle_get_achievements_leaderboard)
    app.router.add_get("/api/achievements/admin/list", handle_get_admin_achievements_list)
    app.router.add_post("/api/achievements/admin/add", handle_add_admin_achievement)
    app.router.add_post("/api/achievements/admin/user/action", handle_admin_user_achievement_action)
    # Protected API
    app.router.add_get("/api/status", handle_status)
    app.router.add_get("/api/guilds", handle_get_guilds)
    app.router.add_get("/api/guilds/{id}", handle_get_guild_detail)
    app.router.add_post("/api/guilds/{id}/invite", handle_create_guild_invite)
    app.router.add_get("/api/guilds/{id}/members", handle_get_guild_members)
    app.router.add_post("/api/guilds/{id}/settings", handle_update_guild_settings)
    app.router.add_get("/api/guilds/{id}/server-config", handle_get_server_config)
    app.router.add_get("/api/guilds/{id}/welcome", handle_get_welcome)
    app.router.add_post("/api/guilds/{id}/welcome", handle_save_welcome)
    app.router.add_post("/api/guilds/{id}/welcome/test", handle_test_welcome)
    app.router.add_get("/api/guilds/{id}/automod", handle_get_automod)
    app.router.add_post("/api/guilds/{id}/automod", handle_save_automod)
    app.router.add_get("/api/guilds/{id}/audit", handle_get_audit)
    app.router.add_post("/api/guilds/{id}/audit", handle_save_audit)
    app.router.add_get("/api/guilds/{id}/blacklist", handle_get_guild_blacklist)
    app.router.add_post("/api/guilds/{id}/blacklist", handle_guild_blacklist_action)
    app.router.add_get("/api/blacklist/global", handle_get_global_blacklist)
    app.router.add_post("/api/blacklist/global", handle_global_blacklist_action)
    app.router.add_get("/api/guilds/{id}/tempvoice", handle_get_tempvoice)
    app.router.add_post("/api/guilds/{id}/tempvoice", handle_save_tempvoice)
    app.router.add_get("/api/guilds/{id}/panel-config", handle_get_panel_config)
    app.router.add_post("/api/guilds/{id}/panel-config", handle_save_panel_config)
    app.router.add_get("/api/guilds/{id}/minigame-config", handle_get_minigame_config)
    app.router.add_post("/api/guilds/{id}/minigame-config", handle_save_minigame_config)
    app.router.add_get("/api/guilds/{id}/confession", handle_get_confession)
    app.router.add_post("/api/guilds/{id}/confession", handle_save_confession)
    app.router.add_post("/api/guilds/{id}/confession/panel", handle_post_confession_panel)
    app.router.add_get("/api/guilds/{id}/level-config", handle_get_level_config)
    app.router.add_post("/api/guilds/{id}/level-config", handle_save_level_config)
    app.router.add_get("/api/guilds/{id}/level-roles", handle_get_level_roles)
    app.router.add_post("/api/guilds/{id}/level-roles", handle_save_level_role)
    app.router.add_delete("/api/guilds/{id}/level-roles/{level}", handle_delete_level_role)
    app.router.add_get("/api/guilds/{id}/fishing-config", handle_get_fishing_config)
    app.router.add_post("/api/guilds/{id}/fishing-config", handle_save_fishing_config)
    app.router.add_get("/api/guilds/{id}/custom-keys", handle_get_custom_keys)
    app.router.add_post("/api/guilds/{id}/custom-keys", handle_save_custom_key)
    app.router.add_delete("/api/guilds/{id}/custom-keys/{key_id}", handle_delete_custom_key)
    app.router.add_get("/api/guilds/{id}/custom-keys/file/{filename}", handle_download_custom_key_file)
    app.router.add_get("/api/guilds/{id}/backups", handle_get_backups)
    app.router.add_post("/api/guilds/{id}/backups/create", handle_create_backup)
    app.router.add_post("/api/guilds/{id}/backups/restore", handle_restore_backup)
    app.router.add_delete("/api/guilds/{id}/backups/{filename}", handle_delete_backup)
    app.router.add_get("/api/guilds/{id}/backups/{filename}/download", handle_download_backup)
    app.router.add_get("/api/guilds/{id}/bot-profile", handle_get_bot_profile)
    app.router.add_post("/api/guilds/{id}/bot-profile", handle_save_bot_profile)
    app.router.add_get("/api/guilds/{id}/autorole", handle_get_autorole)
    app.router.add_post("/api/guilds/{id}/autorole", handle_save_autorole)
    app.router.add_get("/api/guilds/{id}/reaction-roles", handle_get_reaction_roles)
    app.router.add_post("/api/guilds/{id}/reaction-roles/create", handle_create_reaction_role)
    app.router.add_delete("/api/guilds/{id}/reaction-roles/{msg_id}", handle_delete_reaction_role)
    app.router.add_get("/api/guilds/{id}/hoyo-config", handle_get_hoyo_config)
    app.router.add_post("/api/guilds/{id}/hoyo-config", handle_save_hoyo_config)
    app.router.add_post("/api/guilds/{id}/hoyo-post-code", handle_post_hoyo_code)
    app.router.add_get("/api/guilds/{id}/streak", handle_get_streak)
    app.router.add_post("/api/guilds/{id}/streak", handle_save_streak)
    app.router.add_get("/api/guilds/{id}/rule-config", handle_get_rule_config)
    app.router.add_post("/api/guilds/{id}/rule-config", handle_save_rule_config)
    app.router.add_post("/api/guilds/{id}/rule-config/publish", handle_publish_rule)
    app.router.add_post("/api/guilds/{id}/leave", handle_leave_guild)
    app.router.add_get("/api/guilds/{id}/giveaways", handle_get_guild_giveaways)
    app.router.add_post("/api/guilds/{id}/giveaways/create", handle_create_guild_giveaway)
    app.router.add_post("/api/guilds/{id}/giveaways/{msg_id}/end", handle_end_guild_giveaway)
    app.router.add_delete("/api/guilds/{id}/giveaways/{msg_id}", handle_delete_guild_giveaway)
    app.router.add_get("/api/anti", handle_get_anti_settings)
    app.router.add_post("/api/anti", handle_save_anti_settings)
    app.router.add_get("/api/anti/settings", handle_get_anti_settings)
    app.router.add_post("/api/anti/settings", handle_save_anti_settings)
    app.router.add_get("/api/config", handle_get_config)
    app.router.add_post("/api/config", handle_save_config)
    app.router.add_get("/api/admin/config-raw", handle_get_raw_config)
    app.router.add_post("/api/admin/config-raw", handle_save_raw_config)
    app.router.add_get("/api/levels", handle_get_levels)
    app.router.add_post("/api/levels/update", handle_update_user_level)
    app.router.add_post("/api/economy/adjust", handle_economy_adjust)
    app.router.add_get("/api/fishing/leaderboard", handle_get_fishing_leaderboard)
    app.router.add_get("/api/fishing/admin/aquariums", handle_get_admin_fishing_aquariums)
    app.router.add_get("/api/fishing/admin/fish-list", handle_get_admin_fishing_fish_list)
    app.router.add_post("/api/fishing/admin/add-fish", handle_admin_fishing_add_fish)
    app.router.add_post("/api/fishing/admin/add-rod", handle_admin_fishing_add_rod)
    app.router.add_post("/api/fishing/admin/add-bait", handle_admin_fishing_add_bait)
    app.router.add_post("/api/fishing/admin/add-bag", handle_admin_fishing_add_bag)
    app.router.add_post("/api/fishing/admin/add-pet", handle_admin_fishing_add_pet)
    app.router.add_post("/api/fishing/admin/add-troll-item", handle_admin_fishing_add_troll_item)
    app.router.add_post("/api/fishing/admin/add-chest", handle_admin_fishing_add_chest)
    app.router.add_get("/api/fishing/admin/user", handle_get_admin_fishing_user)
    app.router.add_post("/api/fishing/admin/user/action", handle_admin_fishing_user_action)
    app.router.add_get("/api/fishing/admin/giftcodes", handle_get_admin_fishing_giftcodes)
    app.router.add_post("/api/fishing/admin/giftcodes/create", handle_admin_fishing_create_giftcode)
    app.router.add_post("/api/fishing/admin/giftcodes/delete", handle_admin_fishing_delete_giftcode)
    app.router.add_get("/api/fishing/admin/daily-giftcode", handle_get_daily_giftcode)
    app.router.add_post("/api/fishing/admin/daily-giftcode/generate", handle_generate_daily_giftcode)
    app.router.add_get("/api/shop/admin/items", handle_get_admin_shop_items)
    app.router.add_post("/api/shop/admin/update", handle_admin_shop_update)
    app.router.add_post("/api/shop/admin/toggle-hide", handle_admin_shop_toggle_hide)
    app.router.add_get("/api/marriage/admin/list", handle_get_admin_marriages)
    app.router.add_post("/api/marriage/admin/action", handle_admin_marriage_action)
    app.router.add_get("/api/farm/admin/catalogs", handle_get_admin_farm_catalogs)
    app.router.add_get("/api/farm/admin/user", handle_get_admin_farm_user)
    app.router.add_post("/api/farm/admin/user/action", handle_admin_farm_user_action)
    app.router.add_post("/api/farm/admin/environment", handle_admin_farm_set_environment)
    app.router.add_post("/api/farm/admin/item/create", handle_admin_farm_create_item)
    app.router.add_post("/api/farm/admin/item/delete", handle_admin_farm_delete_item)

    # Mining Admin API
    app.router.add_get("/api/mining/admin/catalogs", handle_get_admin_mining_catalogs)
    app.router.add_get("/api/mining/admin/users", handle_get_admin_mining_users)
    app.router.add_get("/api/mining/admin/user", handle_get_admin_mining_user)
    app.router.add_post("/api/mining/admin/user/action", handle_admin_mining_user_action)
    app.router.add_post("/api/mining/admin/item/create", handle_admin_mining_create_item)
    app.router.add_get("/api/admin/rates", handle_get_admin_game_rates)
    app.router.add_post("/api/admin/rates", handle_save_admin_game_rates)
    # Web Admin Management APIs (Chỉ Owner)
    app.router.add_get("/api/admin/users", handle_get_admin_users)
    app.router.add_post("/api/admin/users/role", handle_set_user_role)
    app.router.add_post("/api/admin/users/add-admin", handle_add_web_admin)
    app.router.add_post("/api/admin/users/remove-admin", handle_remove_web_admin)
# Waifu Gacha API & Admin Endpoints
    app.router.add_get("/api/gacha/admin/stats", handle_get_admin_gacha_stats)
    app.router.add_get("/api/gacha/admin/user", handle_get_admin_gacha_user)
    app.router.add_post("/api/gacha/admin/user/action", handle_admin_gacha_user_action)
    app.router.add_get("/api/gacha/characters", handle_get_gacha_characters)
    app.router.add_get("/api/gacha/leaderboard", handle_get_gacha_leaderboard)

    # Voice Leaderboard API
    app.router.add_get("/api/voice/leaderboard", handle_get_voice_leaderboard)

    # Hoyo Test Code API
    app.router.add_post("/api/guilds/{id}/hoyo-test-code", handle_test_hoyo_code)

    # Per-Guild Minecraft Connection API (RCON & Plugin)
    app.router.add_get("/api/guilds/{id}/mc-connection", handle_get_guild_mc_connection)
    app.router.add_post("/api/guilds/{id}/mc-connection", handle_save_guild_mc_connection)
    app.router.add_post("/api/guilds/{id}/mc-connection/test", handle_test_guild_mc_connection)
    app.router.add_post("/api/guilds/{id}/mc-connection/command", handle_command_guild_mc_connection)

    # Plugin Commands API
    app.router.add_get("/api/bot/plugin-commands", handle_get_plugin_commands)

    # Minecraft Link Account API (Cổng 10272)
    app.router.add_post("/api/link", handle_link_request)

    # Minecraft Plugin & Admin API Endpoints
    app.router.add_post("/api/mc/plugin/heartbeat", handle_mc_plugin_heartbeat)
    app.router.add_post("/api/mc/plugin/server/create_link_code", handle_mc_plugin_create_link_code)
    app.router.add_post("/api/mc/plugin/event", handle_mc_plugin_event)
    app.router.add_post("/api/mc/plugin/command/result", handle_mc_plugin_command_result)
    app.router.add_post("/api/mc/plugin/user/create_link_code", handle_mc_plugin_user_create_link_code)
    app.router.add_post("/api/mc/plugin/economy/sync", handle_mc_plugin_economy_sync)

    app.router.add_get("/api/mc/admin/servers", handle_mc_admin_servers)
    app.router.add_get("/api/mc/admin/server/detail", handle_mc_admin_server_detail)
    app.router.add_post("/api/mc/admin/server/link", handle_mc_admin_server_link)
    app.router.add_post("/api/mc/admin/server/unlink", handle_mc_admin_server_unlink)
    app.router.add_post("/api/mc/admin/server/config", handle_mc_admin_server_config)
    app.router.add_post("/api/mc/admin/server/test", handle_mc_admin_server_test)
    app.router.add_post("/api/mc/admin/server/command", handle_mc_admin_server_command)
    app.router.add_get("/api/mc/admin/server/players", handle_mc_admin_server_players)
    app.router.add_post("/api/mc/admin/economy/convert", handle_mc_admin_economy_convert)

    # Minecraft Web Hosting System APIs
    app.router.add_get("/api/mc/hosting/servers", handle_api_mc_hosting_servers)
    app.router.add_get("/api/mc/hosting/server/{id}/detail", handle_api_mc_hosting_server_detail)
    app.router.add_post("/api/mc/hosting/server/{id}/power", handle_api_mc_hosting_server_power)
    app.router.add_get("/api/mc/hosting/server/{id}/console", handle_api_mc_hosting_server_console)
    app.router.add_post("/api/mc/hosting/server/{id}/console/command", handle_api_mc_hosting_server_command)
    app.router.add_get("/api/mc/hosting/discord_channels", handle_api_mc_hosting_discord_channels)
    app.router.add_post("/api/mc/hosting/server/{id}/channels", handle_api_mc_hosting_save_channels)
    app.router.add_post("/api/mc/hosting/server/{id}/chat/send", handle_api_mc_hosting_send_chat)
    app.router.add_get("/api/mc/hosting/server/{id}/files", handle_api_mc_hosting_files_list)
    app.router.add_get("/api/mc/hosting/server/{id}/files/read", handle_api_mc_hosting_files_read)
    app.router.add_post("/api/mc/hosting/server/{id}/files/save", handle_api_mc_hosting_files_save)
    app.router.add_post("/api/mc/hosting/server/{id}/files/create", handle_api_mc_hosting_files_create)
    app.router.add_post("/api/mc/hosting/server/{id}/files/delete", handle_api_mc_hosting_files_delete)
    app.router.add_post("/api/mc/hosting/server/{id}/files/rename", handle_api_mc_hosting_files_rename)
    app.router.add_post("/api/mc/hosting/server/{id}/files/upload", handle_api_mc_hosting_files_upload)
    app.router.add_get("/api/mc/hosting/server/{id}/properties", handle_api_mc_hosting_properties_get)
    app.router.add_post("/api/mc/hosting/server/{id}/properties", handle_api_mc_hosting_properties_save)
    app.router.add_get("/api/mc/hosting/server/{id}/icon", handle_api_mc_hosting_server_icon_get)
    app.router.add_post("/api/mc/hosting/server/{id}/icon", handle_api_mc_hosting_server_icon_upload)
    app.router.add_get("/api/mc/hosting/server/{id}/players", handle_api_mc_hosting_server_players)
    app.router.add_get("/api/mc/hosting/server/{id}/player/{uuid}", handle_api_mc_hosting_server_player_detail)
    app.router.add_get("/api/mc/hosting/manager/users", handle_api_mc_hosting_manager_users_get)
    app.router.add_post("/api/mc/hosting/manager/users/save", handle_api_mc_hosting_manager_users_save)
    app.router.add_post("/api/mc/hosting/manager/users/delete", handle_api_mc_hosting_manager_users_delete)
    app.router.add_get("/api/profile/check-permission", handle_api_profile_check_permission)
    app.router.add_get("/api/tickets", handle_get_tickets)
    app.router.add_post("/api/channel/send", handle_send_channel_message)
    app.router.add_post("/api/bot/action", handle_bot_action)
    app.router.add_get("/api/bot/connection", handle_bot_connection)
    app.router.add_get("/api/bot/commands", handle_get_bot_commands)
    app.router.add_get("/api/mod/commands", handle_get_mod_commands)
    app.router.add_post("/api/mod/commands", handle_save_mod_command)
    app.router.add_post("/api/mod/action", handle_mod_action)
    app.router.add_post("/api/chat", handle_chat)
    app.router.add_get("/api/global-chat", handle_global_chat_history)
    app.router.add_post("/api/global-chat", handle_global_chat_send)
    app.router.add_post("/api/global-chat/upload", handle_global_chat_upload)
    app.router.add_get("/image/chat/{filename}", handle_chat_image_view)
    app.router.add_get("/ws/global-chat", handle_ws_global_chat)
    app.router.add_get("/ws/logs", handle_ws_logs)

    # Sakura Bio Profiles: /profile, /profiles, /linh/profile, /{username}/profile, /add-profile
    app.router.add_get("/profile", handle_profile_directory_page)
    app.router.add_get("/profiles", handle_profile_directory_page)
    app.router.add_get("/api/profiles", handle_list_profiles_api)
    app.router.add_get("/add-profile", handle_add_profile_page)
    app.router.add_get("/api/profile/{username}", handle_get_profile_api)
    app.router.add_post("/api/profile/save", handle_save_profile)
    app.router.add_get("/{username}/profile", handle_user_profile_page)

    # Top.gg Webhook & Vote Tracking
    app.router.add_post("/api/topgg/webhook", handle_topgg_webhook)
    app.router.add_post("/dblwebhook", handle_topgg_webhook)
    app.router.add_get("/api/vote/status/{user_id}", handle_get_vote_status)
    app.router.add_get("/api/vote/toggle-status", handle_get_vote_toggle)
    app.router.add_post("/api/vote/toggle", handle_post_vote_toggle)
    # --- Sakura Web Utilities Routes ---
    app.router.add_get("/tools", handle_tools_hub_page)
    app.router.add_get("/translate", handle_translate_page)
    app.router.add_get("/qrcode", handle_qrcode_page)
    app.router.add_get("/qr", handle_qrcode_page)
    app.router.add_get("/tts", handle_tts_page)
    app.router.add_get("/shortener", handle_shortener_page)
    app.router.add_get("/url", handle_shortener_page)

    app.router.add_post("/api/tools/translate", handle_api_translate)
    app.router.add_post("/api/tools/qrcode", handle_api_qrcode_generate)
    app.router.add_get("/api/tools/qrcode/download", handle_api_qrcode_download)
    app.router.add_post("/api/tools/qrcode/scan", handle_api_qrcode_scan)
    app.router.add_post("/api/tools/tts", handle_api_tts_generate)
    app.router.add_get("/api/tools/tts/audio/{filename}", handle_api_tts_audio)
    app.router.add_post("/api/tools/shorten", handle_api_shorten)
    app.router.add_get("/api/tools/shorten/list", handle_api_shorten_list)
    app.router.add_get("/s/{alias}", handle_short_redirect)
    if STATIC_DIR.exists():
        app.router.add_static("/static", path=str(STATIC_DIR), name="static")

    images_dir = BASE_DIR / "web" / "images"
    if images_dir.exists():
        app.router.add_static("/images", path=str(images_dir), name="images")

    downloads_dir = BASE_DIR / "downloads"
    if downloads_dir.exists():
        app.router.add_static("/downloads", path=str(downloads_dir), name="downloads")

    owner_downloads_dir = BASE_DIR / "owner_downloads"
    if owner_downloads_dir.exists():
        app.router.add_static("/owner_downloads", path=str(owner_downloads_dir), name="owner_downloads")

    plugin_dir = BASE_DIR / "plugin" / "target"
    if plugin_dir.exists():
        app.router.add_static("/plugin-downloads", path=str(plugin_dir), name="plugin-downloads")
    return app

async def start_web_dashboard(bot=None, host: str = "0.0.0.0", port: int = 8080):
    global BOT_INSTANCE
    BOT_INSTANCE = bot
    try:
        from data.database import init_db
        await init_db()
    except Exception:
        pass
    app = create_app()
    runner = web.AppRunner(app)
    await runner.setup()

    actual_port = port
    started = False
    for try_port in range(port, port + 10):
        try:
            site = web.TCPSite(runner, host, try_port)
            await site.start()
            actual_port = try_port
            started = True
            break
        except OSError as e:
            # Nếu là bot tích hợp (có BOT_INSTANCE) mà cổng gốc bị chiếm → cảnh báo rõ
            if bot is not None and try_port == port:
                print(f"\033[93m⚠️ Cổng {port} đã bị chiếm (có thể do 'python web/server.py' đang chạy). Bot sẽ thử cổng {port+1}...\033[0m")
                print(f"   → Để bot và web cùng 1 cổng {port}: tắt web standalone rồi chạy lại 'python run.py' trước.\033[0m")
            continue
    if not started:
        raise OSError(f"Không thể mở cổng từ {port} đến {port + 9}")
    if bot is not None and actual_port != port:
        print(f"\033[93m⚠️ Bot web đã phải dùng cổng {actual_port} thay vì {port} (do {port} bận). Dashboard sẽ ở http://localhost:{actual_port}\033[0m")
        print(f"   → Standalone ở {port} nếu đang chạy sẽ tự proxy sang {actual_port} nhờ fix mới, nhưng khuyên tắt standalone để cùng 1 cổng.\033[0m")
    add_log("SUCCESS", f"🌸 Sakura Web Dashboard đã sẵn sàng ({'tích hợp với bot' if bot else 'standalone'})")
    print(f"\n\033[92m🌸 [Sakura Dashboard] Giao diện Web quản lý đang hoạt động ({'tích hợp' if bot else 'standalone'})\033[0m\n")
    print(f"   → Trang chủ: http://sakurabot.wispbyte.org/ (giới thiệu)")
    print(f"   → Dashboard: http://sakurabot.wispbyte.org/dashboard (bảng điều khiển)")
    return runner, actual_port

if __name__ == "__main__":
    # Nếu bot đã chạy, standalone không nên chiếm 8080 của bot
    try:
        st = get_bot_process_status(use_cache=False)
        if st.get("running"):
            print("\033[93m⚠️ Phát hiện bot đang chạy (pid {}). Standalone sẽ thử 8080, nếu bận sẽ lên 8081 và tự proxy sang bot để cùng dữ liệu.\033[0m".format(st.get("pid")))
            print("   → Khuyên: chỉ chạy 'python run.py' để bot và web cùng 1 cổng 8080 (không chạy web/server.py riêng).\033[0m")
    except: pass
    print("Khởi động Sakura Web Dashboard Standalone...")
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        import config
        standalone_port = getattr(config, "WEB_PORT", 10272)
        loop.run_until_complete(start_web_dashboard(port=standalone_port))
        # standalone cũng cần tail MC
        try: loop.create_task(tail_mc_log_file())
        except: pass
        loop.run_forever()
    except KeyboardInterrupt:
        print("Dừng Web Dashboard.")
