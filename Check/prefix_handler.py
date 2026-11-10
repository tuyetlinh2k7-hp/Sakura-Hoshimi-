import json
import os
from config import PREFIX as DEFAULT_PREFIX

PREFIXES_FILE = "data/prefixes.json"
prefixes = {}

def load_prefixes():
    """Tải danh sách prefix tùy chỉnh từ file JSON."""
    global prefixes
    if os.path.exists(PREFIXES_FILE):
        with open(PREFIXES_FILE, 'r') as f:
            try:
                prefixes = json.load(f)
            except json.JSONDecodeError:
                prefixes = {}

def save_prefixes():
    """Lưu danh sách prefix vào file JSON."""
    os.makedirs(os.path.dirname(PREFIXES_FILE), exist_ok=True)
    with open(PREFIXES_FILE, 'w') as f:
        json.dump(prefixes, f, indent=4)

def get_prefix(bot, message):
    """Hàm callable để bot lấy prefix động cho từng server."""
    if not message.guild:
        return DEFAULT_PREFIX

    guild_prefix = prefixes.get(str(message.guild.id))

    if guild_prefix and guild_prefix != DEFAULT_PREFIX:
        return (guild_prefix, DEFAULT_PREFIX)

    return DEFAULT_PREFIX
