import json
import os
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent
DATA = BASE / "data" / "server_config.json"

_config_cache: dict = {}
_config_mtime: float | None = None

DEFAULT_FEATURES = {
    "automod_enabled": True,
    "leveling_enabled": True,
    "economy_enabled": True,
    "tiktok_enabled": False,
    "mod_dm_notifications": True
}


def _load() -> dict:
    """Chỉ đọc lại file JSON nếu file vừa có sự thay đổi trên ổ cứng."""
    global _config_cache, _config_mtime
    if not DATA.exists():
        _config_cache = {}
        return _config_cache

    try:
        current_mtime = os.path.getmtime(DATA)
        if _config_mtime is None or current_mtime > _config_mtime:
            _config_cache = json.loads(DATA.read_text(encoding="utf-8"))
            _config_mtime = current_mtime
    except (OSError, json.JSONDecodeError):
        pass

    return _config_cache


def save_server_config(guild_id: int | str, new_settings: dict):
    """Lưu hoặc cập nhật cấu hình cho 1 server."""
    global _config_mtime
    data = _load()
    gid = str(guild_id)
    if gid not in data:
        data[gid] = DEFAULT_FEATURES.copy()
    data[gid].update(new_settings)

    DATA.parent.mkdir(parents=True, exist_ok=True)
    DATA.write_text(json.dumps(data, indent=4, ensure_ascii=False), encoding="utf-8")
    _config_mtime = os.path.getmtime(DATA)


def is_admin_only(guild_id: int | str) -> bool:
    d = _load()
    return bool(d.get(str(guild_id), {}).get("admin_only", False))


def is_feature_enabled(guild_id: int | str, feature: str, default: bool | None = None) -> bool:
    d = _load()
    cfg = d.get(str(guild_id), {})
    default_val = default if default is not None else DEFAULT_FEATURES.get(feature, True)
    return bool(cfg.get(feature, default_val))
