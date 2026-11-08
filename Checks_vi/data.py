import json
import os
from pathlib import Path
from groq import Groq
from config import GROQ_API_KEY

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
DATA_FILE = DATA_DIR / "data.json"
_data_mtime = None

# --- KHỞI TẠO CÁC BIẾN TOÀN CỤC (ĐÃ LỌC BỎ BIẾN DƯ THỪA) ---
levels = {}
gain = {}
user_coins = {}
user_inventory = {}

chat_log_channels = {}
edit_log_channels = {}
delete_log_channels = {}
voice_log_channels = {}
server_log_channels = {}
user_log_channels = {}
member_log_channels = {}
join_log_channels = {}
automod_log_channels = {}
invite_log_channels = {}
command_log_channels = {}

MOD_ROLES = {}
LOG_CHANNEL_ID = {}
MUTE_ROLE_ID = {}
CREATE_CHANNEL_ID = {}
voice_stats = {}
guild_settings = {}

# Ánh xạ giữa khóa trong JSON và biến dict trong Python để code gọn gàng, dễ bảo trì
_STATE_MAP = {
    "xp": gain,
    "level": levels,
    "coins": user_coins,
    "inventory": user_inventory,
    "chat_log_channels": chat_log_channels,
    "edit_log_channels": edit_log_channels,
    "delete_log_channels": delete_log_channels,
    "voice_log_channels": voice_log_channels,
    "server_log_channels": server_log_channels,
    "user_log_channels": user_log_channels,
    "member_log_channels": member_log_channels,
    "join_log_channels": join_log_channels,
    "automod_log_channels": automod_log_channels,
    "invite_log_channels": invite_log_channels,
    "command_log_channels": command_log_channels,
    "mod_roles": MOD_ROLES,
    "log_channel": LOG_CHANNEL_ID,
    "mute_role": MUTE_ROLE_ID,
    "create_channel": CREATE_CHANNEL_ID,
    "voice": voice_stats,
    "guild_settings": guild_settings,
}


def save_data():
    """Lưu toàn bộ dữ liệu cấu hình vào data/data.json với chuẩn UTF-8."""
    global _data_mtime
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    data = {json_key: target_dict for json_key, target_dict in _STATE_MAP.items()}

    try:
        with open(DATA_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4, ensure_ascii=False)
        _data_mtime = os.path.getmtime(DATA_FILE)
    except Exception as e:
        print(f"[DATA] Lỗi khi lưu file JSON: {e}")


def load_data():
    """Tải và làm mới dữ liệu từ file JSON mà vẫn giữ nguyên tham chiếu bộ nhớ."""
    global _data_mtime
    if not DATA_FILE.exists():
        return

    try:
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)

        for json_key, target_dict in _STATE_MAP.items():
            target_dict.clear()
            loaded_val = data.get(json_key, {})
            if isinstance(loaded_val, dict):
                target_dict.update(loaded_val)

        _data_mtime = os.path.getmtime(DATA_FILE)
        print("[DATA] Đã làm mới dữ liệu từ file JSON thành công!")
    except Exception as e:
        print(f"[DATA] Lỗi khi đọc file JSON: {e}")


def get_guild_settings(guild_id: int | str) -> dict:
    """Lấy hoặc khởi tạo cài đặt cho một server."""
    global _data_mtime
    try:
        if DATA_FILE.exists():
            current_mtime = os.path.getmtime(DATA_FILE)
            if _data_mtime is None or current_mtime > _data_mtime:
                load_data()
    except OSError:
        pass

    guild_id_str = str(guild_id)
    settings = guild_settings.setdefault(guild_id_str, {})

    defaults = {
        "welcome": True,
        "goodbye": True,
        "welcome_channel": None,
        "leave_channel": None,
        "boost_message": True,
        "boost_channel": None,
        "boost_message_text": "Cảm ơn {user} đã boost server! 💖"
    }

    for key, value in defaults.items():
        settings.setdefault(key, value)

    return settings


# Tải dữ liệu lần đầu khi khởi động
load_data()

groq_client = Groq(api_key=GROQ_API_KEY)
