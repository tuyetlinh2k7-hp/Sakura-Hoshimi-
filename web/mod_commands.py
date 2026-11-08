"""
Quét lệnh mod - đã phân loại, loại trừ MC (is_mc_admin), sẵn sàng add lên web
"""
from pathlib import Path
import json

# Đường dẫn lưu config per-guild
BASE_DIR = Path(__file__).resolve().parent.parent
CONFIG_PATH = BASE_DIR / "data" / "mod_web_config.json"

# Danh mục lệnh Mod đã quét - KHÔNG bao gồm MC (minecraft.py)
MOD_COMMANDS = [
    # === Nhóm A: Thành viên (Member) ===
    {"id": "ban", "name": "Ban", "category": "member", "desc": "Cấm thành viên (có xác nhận)", "perm": "ban_members", "slash": "/ban", "prefix": "s!mod ban", "file": "mod.py"},
    {"id": "kick", "name": "Kick", "category": "member", "desc": "Đuổi thành viên (có xác nhận)", "perm": "kick_members", "slash": "/kick", "prefix": "s!mod kick", "file": "mod.py"},
    {"id": "mute", "name": "Mute (Timeout)", "category": "member", "desc": "Cấm chat tạm thời (phút)", "perm": "moderate_members", "slash": "/mute", "prefix": "s!mod mute", "file": "mod.py"},
    {"id": "unban", "name": "Unban", "category": "member", "desc": "Gỡ cấm theo ID", "perm": "ban_members", "slash": "/unban", "prefix": "s!unban", "file": "mod.py"},
    {"id": "unmute", "name": "Unmute", "category": "member", "desc": "Gỡ timeout", "perm": "moderate_members", "slash": "/unmute", "prefix": "s!mod unmute", "file": "mod.py"},
    {"id": "warn", "name": "Warn", "category": "member", "desc": "Cảnh cáo thành viên", "perm": "has_admin_role", "slash": "—", "prefix": "s!mod warn", "file": "command_manager.py"},
    {"id": "clear", "name": "Clear", "category": "member", "desc": "Xóa tin nhắn kênh (all/số lượng)", "perm": "manage_messages", "slash": "—", "prefix": "s!mod clear", "file": "command_manager.py"},
    # === Nhóm B: Voice ===
    {"id": "mute_voice", "name": "Mute Voice", "category": "voice", "desc": "Tắt mic trong voice", "perm": "mute_members", "slash": "/mute_voice", "prefix": "—", "file": "mod.py"},
    {"id": "unmute_voice", "name": "Unmute Voice", "category": "voice", "desc": "Mở mic trong voice", "perm": "mute_members", "slash": "/unmute_voice", "prefix": "—", "file": "mod.py"},
    {"id": "deaf_voice", "name": "Deaf Voice", "category": "voice", "desc": "Tắt tai nghe cưỡng chế", "perm": "deafen_members", "slash": "/deaf_voice", "prefix": "—", "file": "mod.py"},
    {"id": "undeaf_voice", "name": "Undeaf Voice", "category": "voice", "desc": "Mở tai nghe", "perm": "deafen_members", "slash": "/undeaf_voice", "prefix": "—", "file": "mod.py"},
    {"id": "move", "name": "Move", "category": "voice", "desc": "Kéo 1 user sang kênh voice khác", "perm": "move_members", "slash": "/move", "prefix": "—", "file": "mod.py"},
    {"id": "move_all", "name": "Move All", "category": "voice", "desc": "Gom toàn bộ voice về 1 kênh", "perm": "move_members", "slash": "/move_all", "prefix": "—", "file": "mod.py"},
    {"id": "move_user", "name": "Move User", "category": "voice", "desc": "Di chuyển cả phòng bạn đang ngồi", "perm": "move_members", "slash": "/move_user", "prefix": "—", "file": "mod.py"},
    # === Nhóm C: Quản lý & Thông tin (mod có thể cấu hình) ===
    {"id": "members", "name": "Members List", "category": "utility", "desc": "Xuất danh sách thành viên", "perm": "has_admin_role", "slash": "—", "prefix": "s!mod members", "file": "command_manager.py"},
    {"id": "say", "name": "Say", "category": "utility", "desc": "Cho bot nói vào kênh chỉ định", "perm": "has_admin_role", "slash": "—", "prefix": "s!say", "file": "say.py"},
    {"id": "setprefix", "name": "Set Prefix", "category": "utility", "desc": "Đổi prefix per-server (đã có panel riêng)", "perm": "has_admin_role", "slash": "—", "prefix": "s!setprefix", "file": "prefix.py"},
    {"id": "ticket_setup", "name": "Ticket Setup", "category": "utility", "desc": "Cấu hình kênh ticket (admin)", "perm": "administrator", "slash": "/ticket setup", "prefix": "—", "file": "ticket.py"},
]

# Loại trừ MC: đã kiểm tra không có is_mc_admin trong danh sách trên
# minecraft.py các lệnh: mc panel, mc status, mc command, mc admin add/remove, start/stop/restart, logchannel -> KHÔNG cho lên web

CATEGORIES = {
    "member": {"label": "👤 Thành viên", "color": "#ff79c6"},
    "voice": {"label": "🔊 Voice", "color": "#8be9fd"},
    "utility": {"label": "🛠️ Tiện ích", "color": "#bd93f9"},
}

def load_config():
    if not CONFIG_PATH.exists():
        return {}
    try:
        with open(CONFIG_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}

def save_config(data):
    CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(CONFIG_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def get_guild_mod_config(guild_id: str):
    cfg = load_config()
    # mặc định tất cả bật
    guild_cfg = cfg.get(str(guild_id), {})
    # fill defaults
    for cmd in MOD_COMMANDS:
        if cmd["id"] not in guild_cfg:
            guild_cfg[cmd["id"]] = True  # enabled mặc định
    return guild_cfg

def set_guild_command(guild_id: str, cmd_id: str, enabled: bool):
    cfg = load_config()
    gid = str(guild_id)
    if gid not in cfg:
        cfg[gid] = {}
    cfg[gid][cmd_id] = bool(enabled)
    save_config(cfg)
    return True

def get_all_with_status(guild_id: str):
    guild_cfg = get_guild_mod_config(guild_id)
    out = []
    for cmd in MOD_COMMANDS:
        c = dict(cmd)
        c["enabled"] = guild_cfg.get(cmd["id"], True)
        out.append(c)
    return out
