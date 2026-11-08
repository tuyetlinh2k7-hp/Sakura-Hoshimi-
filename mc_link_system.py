import json
import random
import string
import time
from pathlib import Path

from aiohttp import web

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
LINKS_FILE = DATA_DIR / "mc_links.json"
PENDING_LINKS = {}


def ensure_data_dir():
    DATA_DIR.mkdir(parents=True, exist_ok=True)


def load_links():
    ensure_data_dir()
    if not LINKS_FILE.exists():
        return {}
    try:
        with LINKS_FILE.open("r", encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, OSError):
        return {}


def save_links(data):
    ensure_data_dir()
    with LINKS_FILE.open("w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)


def create_link_code(discord_id: int) -> str:
    code = "".join(random.choice(string.ascii_uppercase + string.digits) for _ in range(6))
    PENDING_LINKS[code] = {
        "discord_id": int(discord_id),
        "created_at": int(time.time()),
        "expires_at": int(time.time()) + 600,
    }
    return code


def get_linked_account(discord_id: int):
    links = load_links()
    return links.get(str(discord_id))


def get_linked_discord(minecraft_uuid: str):
    links = load_links()
    uuid_target = str(minecraft_uuid).strip().lower()
    for discord_id, data in links.items():
        if isinstance(data, dict) and str(data.get("minecraft_uuid", "")).lower() == uuid_target:
            return int(discord_id)
    return None


async def handle_link_request(request: web.Request):
    try:
        data = await request.json()
    except Exception:
        return web.json_response({"ok": False, "error": "JSON không hợp lệ"}, status=400)

    code = str(data.get("code", "")).strip().upper()
    minecraft_uuid = str(data.get("minecraft_uuid", "")).strip()
    minecraft_name = str(data.get("minecraft_name", "")).strip()

    if not code or not minecraft_uuid:
        return web.json_response({"ok": False, "error": "Thiếu code hoặc minecraft_uuid"}, status=400)

    pending = PENDING_LINKS.get(code)
    if not pending:
        return web.json_response({"ok": False, "error": "Mã liên kết không tồn tại hoặc đã hết hạn"}, status=400)

    if time.time() > pending["expires_at"]:
        PENDING_LINKS.pop(code, None)
        return web.json_response({"ok": False, "error": "Mã liên kết đã hết hạn"}, status=400)

    discord_id = int(pending["discord_id"])
    links = load_links()
    links[str(discord_id)] = {
        "discord_id": discord_id,
        "minecraft_uuid": minecraft_uuid.lower(),
        "minecraft_name": minecraft_name,
        "linked_at": int(time.time()),
    }
    save_links(links)
    PENDING_LINKS.pop(code, None)

    return web.json_response({
        "ok": True,
        "discord_id": discord_id,
        "minecraft_uuid": minecraft_uuid.lower(),
        "minecraft_name": minecraft_name,
        "message": "Liên kết thành công"
    })


async def start_link_server(host: str = "snow.pikamc.vn", port: int = 25365):
    app = web.Application()
    app.router.add_post("/api/link", handle_link_request)
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, host, port)
    await site.start()
    print(f"[MC Link] API đang chạy tại http://{host}:{port}/api/link")
    return runner
