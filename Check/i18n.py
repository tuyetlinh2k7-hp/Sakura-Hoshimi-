"""
i18n - Per-guild scalable multi-language system for Sakura Bot
- Supports vi / en and dynamically detects any new languages in languages/*.json (e.g. ja, ko, fr, zh)
- Default language inferred from guild.preferred_locale
- Storage: data/server_language.json  { "guild_id_str": "vi"|"en"|... }
- Translation files: languages/{lang}.json
"""
import json
import os
import re
import discord
from pathlib import Path
from typing import Optional, Dict, Any, Set

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
LANG_DIR = BASE_DIR / "languages"
SERVER_LANG_FILE = DATA_DIR / "server_language.json"

server_language: dict[str, str] = {}
language_cache: dict[str, dict] = {}
_lang_file_mtimes: dict[str, float] = {}
_server_lang_mtime: float | None = None

DEFAULT_LANG = "vi"

DEFAULT_META = {
    "vi": {"name": "Tiếng Việt", "native": "Tiếng Việt", "flag": "🇻🇳"},
    "en": {"name": "English", "native": "English", "flag": "🇬🇧"},
    "ja": {"name": "Japanese", "native": "日本語", "flag": "🇯🇵"},
    "ko": {"name": "Korean", "native": "한국어", "flag": "🇰🇷"},
    "zh": {"name": "Chinese", "native": "中文", "flag": "🇨🇳"},
    "cn": {"name": "Chinese", "native": "中文", "flag": "🇨🇳"},
    "fr": {"name": "French", "native": "Français", "flag": "🇫🇷"},
    "es": {"name": "Spanish", "native": "Español", "flag": "🇪🇸"},
    "de": {"name": "German", "native": "Deutsch", "flag": "🇩🇪"},
    "ru": {"name": "Russian", "native": "Русский", "flag": "🇷🇺"},
}

_ESCAPED_NEWLINE_RE = re.compile(r"(?:\\+r)?\\+n")
_AROUND_NEWLINE_SPACE_RE = re.compile(r"[ \t]*\n[ \t]*")
_EDGE_CLEAN_RE = re.compile(r"^(?:[\s\r\n]|\\+n|\\+r)+|(?:[\s\r\n]|\\+n|\\+r)+$")


def _clean_text(val):
    """
    Làm sạch triệt để chuỗi từ JSON:
    - Biến mọi kiểu '\\n', ' \\n ', '\\\n' ở giữa câu thành xuống dòng thật '\n'.
    - Cắt sạch sẽ mọi dấu '\n', '\\n', ' \n' thừa ở đầu và cuối câu.
    """
    if isinstance(val, str):
        text = _ESCAPED_NEWLINE_RE.sub("\n", val)
        text = text.replace("\r\n", "\n").replace("\r", "\n")
        text = _AROUND_NEWLINE_SPACE_RE.sub("\n", text)
        return _EDGE_CLEAN_RE.sub("", text)

    if isinstance(val, dict):
        return {k: _clean_text(v) for k, v in val.items()}
    if isinstance(val, list):
        return [_clean_text(item) for item in val]
    return val


def get_supported_languages() -> Set[str]:
    """Tự động phát hiện các ngôn ngữ có sẵn từ thư mục languages/*.json"""
    langs = {"vi", "en"}
    if LANG_DIR.exists():
        for p in LANG_DIR.glob("*.json"):
            langs.add(p.stem.lower())
    return langs


class _SupportedLanguagesSet(set):
    """Lớp proxy kế thừa set để biến SUPPORTED tự động đồng bộ khi quét thư mục"""
    def __contains__(self, item):
        return str(item).lower() in get_supported_languages()

    def __iter__(self):
        return iter(get_supported_languages())

    def __len__(self):
        return len(get_supported_languages())


SUPPORTED = _SupportedLanguagesSet(["vi", "en"])


def get_languages_metadata() -> Dict[str, Dict[str, str]]:
    """Lấy danh sách thông tin và cờ biểu tượng của các ngôn ngữ được hỗ trợ."""
    metadata = {}
    for code in get_supported_languages():
        data = _load_lang_file(code)
        if isinstance(data, dict) and "_meta" in data and isinstance(data["_meta"], dict):
            metadata[code] = data["_meta"]
        elif code in DEFAULT_META:
            metadata[code] = DEFAULT_META[code]
        else:
            metadata[code] = {"name": code.upper(), "native": code.upper(), "flag": "🌐"}
    return metadata


def _load_server_language():
    global server_language, _server_lang_mtime
    if not SERVER_LANG_FILE.exists():
        server_language = {}
        return

    try:
        mtime = os.path.getmtime(SERVER_LANG_FILE)
        if _server_lang_mtime is None or mtime > _server_lang_mtime:
            with open(SERVER_LANG_FILE, "r", encoding="utf-8") as f:
                server_language = json.load(f)
            _server_lang_mtime = mtime
    except Exception:
        pass


def _save_server_language():
    global _server_lang_mtime
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    with open(SERVER_LANG_FILE, "w", encoding="utf-8") as f:
        json.dump(server_language, f, indent=4, ensure_ascii=False)
    _server_lang_mtime = os.path.getmtime(SERVER_LANG_FILE)


_load_server_language()


def _load_lang_file(lang: str) -> dict:
    """Tải file ngôn ngữ và tự động làm sạch ngay khi nạp vào bộ nhớ đệm."""
    lang = lang.lower()
    path = LANG_DIR / f"{lang}.json"
    if not path.exists():
        return _load_lang_file(DEFAULT_LANG) if lang != DEFAULT_LANG else {}

    try:
        current_mtime = os.path.getmtime(path)
        if lang not in language_cache or current_mtime > _lang_file_mtimes.get(lang, 0):
            with open(path, "r", encoding="utf-8") as f:
                raw_data = json.load(f)
                language_cache[lang] = _clean_text(raw_data)
            _lang_file_mtimes[lang] = current_mtime
        return language_cache[lang]
    except (json.JSONDecodeError, OSError):
        return language_cache.get(lang, {})


def reload_languages():
    """Xóa cache ngôn ngữ thủ công khi cần làm mới ngay lập tức."""
    language_cache.clear()
    _lang_file_mtimes.clear()
    _load_server_language()


def get_guild_language(guild_or_id) -> str:
    """
    Xác định ngôn ngữ cho server:
    1. Ưu tiên cấu hình riêng trong server_language.json
    2. Ngôn ngữ Discord preferred_locale của server nếu khớp
    3. Mặc định 'vi' (Tiếng Việt)
    """
    _load_server_language()
    supported = get_supported_languages()

    if guild_or_id is None:
        return DEFAULT_LANG

    if isinstance(guild_or_id, str) and guild_or_id.lower().strip() in supported:
        return guild_or_id.lower().strip()

    guild = None
    if isinstance(guild_or_id, discord.Interaction):
        guild = guild_or_id.guild
        gid = str(guild.id) if guild else None
    elif hasattr(guild_or_id, "guild"):
        guild = guild_or_id.guild
        gid = str(guild.id) if guild else None
    elif isinstance(guild_or_id, (int, str)):
        gid = str(guild_or_id)
    else:
        guild = guild_or_id
        gid = str(getattr(guild, "id", ""))

    if gid and gid in server_language and server_language[gid] in supported:
        return server_language[gid]

    if guild is not None:
        locale = getattr(guild, "preferred_locale", None)
        if locale is not None:
            locale_str = str(getattr(locale, "value", locale)).lower()
            if locale_str.startswith(('zh', 'cn')) and 'cn' in supported:
                return 'cn'
            for s in supported:
                if locale_str.startswith(s):
                    return s

    return DEFAULT_LANG


def is_vietnamese(guild_or_id) -> bool:
    """Kiểm tra nhanh xem server có đang sử dụng Tiếng Việt hay không"""
    return get_guild_language(guild_or_id) == "vi"


def set_guild_language(guild_id: int | str, lang: str):
    """Lưu cấu hình ngôn ngữ cho server"""
    lang = lang.lower().strip()
    supported = get_supported_languages()
    if lang not in supported:
        raise ValueError(f"Unsupported language: {lang}. Supported: {list(supported)}")
    server_language[str(guild_id)] = lang
    _save_server_language()


def t(guild_or_id, key: str, default: Optional[str] = None, **kwargs) -> str:
    """
    Dịch chuỗi theo khóa (key) cho server tương ứng.
    - Hỗ trợ truyền vào: Guild, Interaction, Context, ID (int/str) hoặc None.
    - Nếu key không tồn tại ở ngôn ngữ hiện tại, tự động fallback sang Tiếng Việt ('vi').
    - Nếu vẫn không có, trả về default (nếu truyền) hoặc key gốc.
    - Hỗ trợ định dạng biến {variable} linh hoạt.
    """
    lang = get_guild_language(guild_or_id)
    data = _load_lang_file(lang)
    text = data.get(key)

    if text is None and lang != DEFAULT_LANG:
        vi_data = _load_lang_file(DEFAULT_LANG)
        text = vi_data.get(key)

    if text is None:
        text = default if default is not None else key

    if isinstance(text, str):
        if kwargs:
            try:
                text = text.format(**kwargs)
            except Exception:
                pass
        text = _clean_text(text)

    return text


def get_lang_string(guild_id: int | str, key: str, **kwargs) -> str:
    """Hàm tương thích ngược."""
    return t(guild_id, key, **kwargs)
