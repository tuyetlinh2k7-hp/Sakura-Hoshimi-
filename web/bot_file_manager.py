import math
import sqlite3
import re
import os
import sys
import json
import time
import shutil
import asyncio
from pathlib import Path
from typing import Optional, Dict, Any, List, Tuple
from aiohttp import web
import discord
from discord.ext import commands

# Thư mục gốc dự án
BASE_DIR = Path(__file__).resolve().parent.parent
TEMPLATES_DIR = Path(__file__).resolve().parent / "templates"

# Danh sách thư mục/tệp bị giới hạn hoặc bảo vệ
IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".gif", ".webp", ".svg", ".ico", ".bmp", ".avif"}
VIDEO_EXTENSIONS = {".mp4", ".webm", ".mov", ".mkv", ".avi", ".flv"}
AUDIO_EXTENSIONS = {".mp3", ".wav", ".ogg", ".m4a", ".flac", ".aac"}
MEDIA_EXTENSIONS = IMAGE_EXTENSIONS | VIDEO_EXTENSIONS | AUDIO_EXTENSIONS
RESTRICTED_PARTS = {".git", ".venv", "node_modules", "__pycache__"}


def resolve_safe_bot_path(rel_path: str, base_dir: Path = BASE_DIR) -> Optional[Path]:
    """Phân giải đường dẫn an toàn tương đối với base_dir để chống path traversal."""
    cleaned = str(rel_path or "").replace("\\", "/").strip().lstrip("/")
    target = (base_dir / cleaned).resolve()
    base_resolved = base_dir.resolve()
    try:
        target.relative_to(base_resolved)
        return target
    except ValueError:
        return None


def get_extension_from_path(rel_path: str) -> Optional[str]:
    """Chuyển đổi đường dẫn file code thành tên module Extension của discord.py nếu hợp lệ."""
    norm = str(rel_path or "").replace("\\", "/").strip().lstrip("/")
    if norm.endswith(".py"):
        norm = norm[:-3]
    parts = norm.split("/")
    if len(parts) == 2 and parts[0] in ("Command", "Anti", "Logs_vi"):
        return f"{parts[0]}.{parts[1]}"
    return None


def get_bot_files_list(base_dir: Path, rel_path: str = "") -> Tuple[bool, Any]:
    """Liệt kê danh sách thư mục và tệp con trong thư mục chỉ định."""
    target_dir = resolve_safe_bot_path(rel_path, base_dir)
    if not target_dir or not target_dir.exists():
        return False, "Thư mục không tồn tại hoặc không hợp lệ"
    if not target_dir.is_dir():
        return False, "Đường dẫn không phải là thư mục"

    dirs_list = []
    files_list = []

    try:
        for entry in sorted(target_dir.iterdir(), key=lambda p: (not p.is_dir(), p.name.lower())):
            # Bỏ qua các thư mục nội bộ
            if entry.name in RESTRICTED_PARTS:
                continue

            entry_rel = str(entry.relative_to(base_dir)).replace("\\", "/")
            stat = entry.stat()
            mtime_str = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(stat.st_mtime))

            if entry.is_dir():
                # Đếm số lượng item con (trừ cache)
                child_count = 0
                try:
                    child_count = len([c for c in entry.iterdir() if c.name not in RESTRICTED_PARTS])
                except Exception:
                    pass
                dirs_list.append({
                    "name": entry.name,
                    "path": entry_rel,
                    "mtime": mtime_str,
                    "item_count": child_count
                })
            else:
                ext = entry.suffix.lower()
                cog_mod = get_extension_from_path(entry_rel)
                is_db = ext in (".db", ".sqlite", ".sqlite3")
                is_img = ext in IMAGE_EXTENSIONS
                is_vid = ext in VIDEO_EXTENSIONS
                is_aud = ext in AUDIO_EXTENSIONS
                media_type = "image" if is_img else ("video" if is_vid else ("audio" if is_aud else None))
                files_list.append({
                    "name": entry.name,
                    "path": entry_rel,
                    "size": stat.st_size,
                    "mtime": mtime_str,
                    "ext": ext,
                    "is_cog": bool(cog_mod),
                    "cog_module": cog_mod,
                    "is_database": is_db,
                    "is_media": bool(media_type),
                    "media_type": media_type
                })

        parent_rel = ""
        if rel_path.strip().lstrip("/\\"):
            p_obj = Path(rel_path.strip().lstrip("/\\")).parent
            parent_rel = str(p_obj).replace("\\", "/") if str(p_obj) != "." else ""

        return True, {
            "current_path": rel_path.replace("\\", "/").strip().lstrip("/"),
            "parent_path": parent_rel,
            "directories": dirs_list,
            "files": files_list
        }
    except Exception as e:
        return False, f"Lỗi đọc thư mục: {e}"


def read_bot_file(base_dir: Path, rel_path: str) -> Tuple[bool, Any]:
    """Đọc nội dung văn bản của một tệp."""
    target_file = resolve_safe_bot_path(rel_path, base_dir)
    if not target_file or not target_file.exists():
        return False, "Tệp không tồn tại"
    if not target_file.is_file():
        return False, "Đường dẫn không phải là tệp tin"

    # Giới hạn kích thước tệp mở trên web (tối đa 5MB)
    stat = target_file.stat()
    norm_rel = str(target_file.relative_to(base_dir)).replace("\\", "/")
    ext = target_file.suffix.lower()
    if ext in (".db", ".sqlite", ".sqlite3"):
        # Trả về cờ tệp cơ sở dữ liệu SQLite
        return True, {
            "path": norm_rel,
            "name": target_file.name,
            "size": stat.st_size,
            "mtime": time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(stat.st_mtime)),
            "content": "",
            "is_cog": False,
            "cog_module": None,
            "is_database": True,
            "is_media": False
        }

    if ext in MEDIA_EXTENSIONS:
        # Trả về cờ tệp Media (Ảnh, GIF, Video, Audio)
        media_type = "image" if ext in IMAGE_EXTENSIONS else ("video" if ext in VIDEO_EXTENSIONS else "audio")
        return True, {
            "path": norm_rel,
            "name": target_file.name,
            "size": stat.st_size,
            "mtime": time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(stat.st_mtime)),
            "content": "",
            "is_cog": False,
            "cog_module": None,
            "is_database": False,
            "is_media": True,
            "media_type": media_type,
            "raw_url": f"/api/admin/bot-files/raw?path={norm_rel}"
        }

    if stat.st_size > 5 * 1024 * 1024:
        return False, "Tệp quá lớn (> 5MB) để chỉnh sửa trực tiếp trên trình duyệt"

    content = ""
    try:
        with open(target_file, "r", encoding="utf-8") as f:
            content = f.read()
    except UnicodeDecodeError:
        try:
            with open(target_file, "r", encoding="latin-1") as f:
                content = f.read()
        except Exception as e:
            return False, f"Không thể giải mã tệp văn bản: {e}"
    except Exception as e:
        return False, f"Lỗi đọc tệp: {e}"

    norm_rel = str(target_file.relative_to(base_dir)).replace("\\", "/")
    cog_mod = get_extension_from_path(norm_rel)

    return True, {
        "path": norm_rel,
        "name": target_file.name,
        "size": stat.st_size,
        "mtime": time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(stat.st_mtime)),
        "content": content,
        "is_cog": bool(cog_mod),
        "cog_module": cog_mod
    }


def save_bot_file(base_dir: Path, rel_path: str, content: str) -> Tuple[bool, str, Optional[dict]]:
    """Lưu nội dung vào tệp. Tự động kiểm tra cú pháp Python nếu là file .py."""
    target_file = resolve_safe_bot_path(rel_path, base_dir)
    if not target_file:
        return False, "Đường dẫn tệp không hợp lệ hoặc nằm ngoài thư mục Bot", None

    norm_rel = str(rel_path).replace("\\", "/").strip().lstrip("/")

    # 1. Kiểm tra lỗi cú pháp Python trước khi ghi
    if norm_rel.endswith(".py"):
        try:
            compile(content, target_file.name, "exec")
        except SyntaxError as syn_err:
            return False, f"Phát hiện lỗi cú pháp Python tại dòng {syn_err.lineno}: {syn_err.msg}", {
                "line": syn_err.lineno,
                "offset": syn_err.offset,
                "text": syn_err.text
            }

    # 2. Ghi tệp an toàn
    try:
        target_file.parent.mkdir(parents=True, exist_ok=True)
        with open(target_file, "w", encoding="utf-8") as f:
            f.write(content)

        return True, "Đã lưu tệp thành công!", None
    except Exception as e:
        return False, f"Lỗi khi ghi tệp: {e}", None


# ==============================================================================
# HỆ THỐNG COG / EXTENSION RELOADER CHO ADMIN WEB
# ==============================================================================

def get_registered_extensions(bot=None) -> List[Dict[str, Any]]:
    """Thu thập danh sách tất cả Cogs và Extensions của Bot."""
    loaded_extensions = set()
    if bot and hasattr(bot, "extensions"):
        loaded_extensions = set(bot.extensions.keys())

    # Lấy danh sách định nghĩa sẵn trong file1, file2, file3
    defined_exts = set()
    try:
        import file1
        for e in getattr(file1, "EXTENSIONS", ()):
            defined_exts.add(f"Command.{e}")
    except Exception:
        pass

    try:
        import file2
        for e in getattr(file2, "EXTENSION_LOGS", ()):
            defined_exts.add(f"Logs_vi.{e}")
    except Exception:
        pass

    try:
        import file3
        for e in getattr(file3, "EXTENSION_ANTIS", ()):
            defined_exts.add(f"Anti.{e}")
    except Exception:
        pass

    all_ext_names = sorted(defined_exts | loaded_extensions)

    result = []
    for ext_name in all_ext_names:
        is_loaded = ext_name in loaded_extensions
        # Đếm số lượng cogs / commands thuộc extension này nếu bot đang online
        cog_names = []
        cmd_count = 0
        if bot and is_loaded:
            ext_module = bot.extensions.get(ext_name)
            if ext_module:
                # Quét cogs
                for cog_name, cog_instance in bot.cogs.items():
                    if cog_instance.__module__ == ext_module.__name__:
                        cog_names.append(cog_name)
                        cmd_count += len(cog_instance.get_commands())

        result.append({
            "name": ext_name,
            "loaded": is_loaded,
            "cogs": cog_names,
            "commands_count": cmd_count,
            "category": ext_name.split(".")[0] if "." in ext_name else "Core"
        })

    return result


async def reload_extension_action(bot, ext_name: str, sync_tree: bool = False) -> Dict[str, Any]:
    """Thực hiện reload một Extension hoặc toàn bộ Extensions."""
    if not bot:
        return {"ok": False, "error": "Bot hiện chưa được khởi chạy cùng Web Server!"}

    if ext_name == "all":
        # Nạp lại toàn bộ
        all_exts = get_registered_extensions(bot)
        reloaded = []
        failed = []

        for item in all_exts:
            e = item["name"]
            try:
                if e in bot.extensions:
                    await bot.reload_extension(e)
                else:
                    await bot.load_extension(e)
                reloaded.append(e)
            except Exception as exc:
                failed.append({"extension": e, "error": str(exc)})

        tree_synced = False
        sync_err = None
        if sync_tree:
            try:
                await bot.tree.sync()
                tree_synced = True
            except Exception as exc:
                sync_err = str(exc)

        return {
            "ok": len(failed) == 0,
            "reloaded_count": len(reloaded),
            "reloaded": reloaded,
            "failed_count": len(failed),
            "failed": failed,
            "tree_synced": tree_synced,
            "sync_error": sync_err,
            "message": f"Đã nạp lại {len(reloaded)} extensions!" + (f" ({len(failed)} thất bại)" if failed else "")
        }

    else:
        # Nạp lại 1 extension cụ thể
        try:
            if ext_name in bot.extensions:
                await bot.reload_extension(ext_name)
                action_word = "nạp lại (reload)"
            else:
                await bot.load_extension(ext_name)
                action_word = "nạp mới (load)"

            tree_synced = False
            sync_err = None
            if sync_tree:
                try:
                    await bot.tree.sync()
                    tree_synced = True
                except Exception as exc:
                    sync_err = str(exc)

            return {
                "ok": True,
                "extension": ext_name,
                "message": f"✅ Đã {action_word} thành công `{ext_name}`!",
                "tree_synced": tree_synced,
                "sync_error": sync_err
            }
        except Exception as e:
            return {
                "ok": False,
                "extension": ext_name,
                "error": f"Lỗi khi nạp extension `{ext_name}`: {e}"
            }


# ==============================================================================
# ROUTE HANDLERS
# ==============================================================================

async def handle_bot_files_page(request: web.Request):
    """Trang giao diện quản lý tệp tin và nạp lại Cogs của Bot (/admin/files)."""
    # Import hàm kiểm tra session từ server
    from web.server import get_session, is_admin_session
    sess = get_session(request)
    if not sess:
        return web.HTTPFound("/login?redirect=/admin/files")
    if not is_admin_session(sess):
        return web.Response(
            text="<h1 style='color:#ff5555;font-family:sans-serif;text-align:center;margin-top:50px;'>⛔ 403 Forbidden - Chỉ Quản trị viên (Admin) mới có quyền truy cập trang Quản Lý Tệp!</h1>",
            content_type="text/html",
            status=403
        )

    tmpl = TEMPLATES_DIR / "bot_files.html"
    if not tmpl.exists():
        return web.Response(text="<h1>bot_files.html không tồn tại</h1>", content_type="text/html", status=404)

    return web.Response(text=tmpl.read_text(encoding="utf-8"), content_type="text/html")


async def handle_api_bot_files_list(request: web.Request):
    from web.server import get_session, is_admin_session
    sess = get_session(request)
    if not sess or not is_admin_session(sess):
        return web.json_response({"ok": False, "error": "Chỉ Quản trị viên (Admin) mới có quyền truy cập!"}, status=403)

    rel_path = request.query.get("path", "")
    ok, result = get_bot_files_list(BASE_DIR, rel_path)
    if not ok:
        return web.json_response({"ok": False, "error": result}, status=400)
    return web.json_response({"ok": True, **result})


async def handle_api_bot_files_read(request: web.Request):
    from web.server import get_session, is_admin_session
    sess = get_session(request)
    if not sess or not is_admin_session(sess):
        return web.json_response({"ok": False, "error": "Chỉ Quản trị viên (Admin) mới có quyền truy cập!"}, status=403)

    rel_path = request.query.get("path", "")
    ok, result = read_bot_file(BASE_DIR, rel_path)
    if not ok:
        return web.json_response({"ok": False, "error": result}, status=400)
    return web.json_response({"ok": True, "file": result})


async def handle_api_bot_files_save(request: web.Request):
    from web.server import get_session, is_admin_session
    sess = get_session(request)
    if not sess or not is_admin_session(sess):
        return web.json_response({"ok": False, "error": "Chỉ Quản trị viên (Admin) mới có quyền truy cập!"}, status=403)

    try:
        data = await request.json()
        rel_path = data.get("path", "")
        content = data.get("content", "")

        ok, msg, syntax_info = save_bot_file(BASE_DIR, rel_path, content)
        if not ok:
            return web.json_response({"ok": False, "error": msg, "syntax_error": bool(syntax_info), "details": syntax_info}, status=400)

        # Trả về kèm thông tin có phải Cog không để client gợi ý reload
        norm_rel = rel_path.replace("\\", "/").strip().lstrip("/")
        cog_mod = get_extension_from_path(norm_rel)

        return web.json_response({
            "ok": True,
            "message": msg,
            "is_cog": bool(cog_mod),
            "cog_module": cog_mod
        })
    except Exception as e:
        return web.json_response({"ok": False, "error": str(e)}, status=500)


async def handle_api_bot_files_create(request: web.Request):
    from web.server import get_session, is_admin_session
    sess = get_session(request)
    if not sess or not is_admin_session(sess):
        return web.json_response({"ok": False, "error": "Chỉ Quản trị viên (Admin) mới có quyền truy cập!"}, status=403)

    try:
        data = await request.json()
        rel_path = data.get("path", "")
        name = data.get("name", "").strip()
        is_dir = bool(data.get("is_dir", False))

        if not name:
            return web.json_response({"ok": False, "error": "Tên không được để trống"}, status=400)

        target_parent = resolve_safe_bot_path(rel_path, BASE_DIR)
        if not target_parent or not target_parent.exists():
            return web.json_response({"ok": False, "error": "Thư mục cha không tồn tại"}, status=404)

        clean_name = os.path.basename(name)
        new_target = target_parent / clean_name

        if new_target.exists():
            return web.json_response({"ok": False, "error": "Tệp hoặc thư mục đã tồn tại"}, status=400)

        if is_dir:
            new_target.mkdir(parents=True, exist_ok=True)
            msg = f"Đã tạo thư mục `{clean_name}` thành công!"
        else:
            new_target.touch()
            msg = f"Đã tạo tệp `{clean_name}` thành công!"

        return web.json_response({"ok": True, "message": msg, "path": str(new_target.relative_to(BASE_DIR)).replace("\\", "/")})
    except Exception as e:
        return web.json_response({"ok": False, "error": str(e)}, status=500)


async def handle_api_bot_files_delete(request: web.Request):
    from web.server import get_session, is_admin_session
    sess = get_session(request)
    if not sess or not is_admin_session(sess):
        return web.json_response({"ok": False, "error": "Chỉ Quản trị viên (Admin) mới có quyền truy cập!"}, status=403)

    try:
        data = await request.json()
        rel_path = data.get("path", "")
        target = resolve_safe_bot_path(rel_path, BASE_DIR)

        if not target or not target.exists():
            return web.json_response({"ok": False, "error": "Mục cần xóa không tồn tại"}, status=404)

        # Chặn xóa thư mục gốc của bot
        if target.resolve() == BASE_DIR.resolve():
            return web.json_response({"ok": False, "error": "Không thể xóa thư mục gốc của Bot!"}, status=400)

        # Chặn xóa các thư mục cốt lõi trực tiếp
        if target.parent.resolve() == BASE_DIR.resolve() and target.name in ("Command", "Anti", "Logs_vi", "Check", "web", "data"):
            return web.json_response({"ok": False, "error": f"Không được phép xóa thư mục cốt lõi `{target.name}`!"}, status=400)

        if target.is_dir():
            shutil.rmtree(target)
            msg = f"Đã xóa thư mục `{target.name}`"
        else:
            target.unlink()
            msg = f"Đã xóa tệp `{target.name}`"

        return web.json_response({"ok": True, "message": msg})
    except Exception as e:
        return web.json_response({"ok": False, "error": str(e)}, status=500)


async def handle_api_bot_files_rename(request: web.Request):
    from web.server import get_session, is_admin_session
    sess = get_session(request)
    if not sess or not is_admin_session(sess):
        return web.json_response({"ok": False, "error": "Chỉ Quản trị viên (Admin) mới có quyền truy cập!"}, status=403)

    try:
        data = await request.json()
        rel_path = data.get("path", "")
        new_name = data.get("new_name", "").strip()

        target = resolve_safe_bot_path(rel_path, BASE_DIR)
        if not target or not target.exists():
            return web.json_response({"ok": False, "error": "Mục cần đổi tên không tồn tại"}, status=404)

        if target.resolve() == BASE_DIR.resolve():
            return web.json_response({"ok": False, "error": "Không thể đổi tên thư mục gốc!"}, status=400)

        clean_new_name = os.path.basename(new_name)
        new_target = target.parent / clean_new_name

        if new_target.exists():
            return web.json_response({"ok": False, "error": "Tên mới đã tồn tại"}, status=400)

        target.rename(new_target)
        return web.json_response({
            "ok": True,
            "message": f"Đã đổi tên thành `{clean_new_name}`",
            "path": str(new_target.relative_to(BASE_DIR)).replace("\\", "/")
        })
    except Exception as e:
        return web.json_response({"ok": False, "error": str(e)}, status=500)


async def handle_api_bot_files_upload(request: web.Request):
    from web.server import get_session, is_admin_session
    sess = get_session(request)
    if not sess or not is_admin_session(sess):
        return web.json_response({"ok": False, "error": "Chỉ Quản trị viên (Admin) mới có quyền truy cập!"}, status=403)

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
                dest_dir = resolve_safe_bot_path(target_subpath, BASE_DIR)
                if not dest_dir or not dest_dir.exists():
                    return web.json_response({"ok": False, "error": "Thư mục đích không tồn tại"}, status=400)

                dest_file = dest_dir / clean_filename
                with open(dest_file, "wb") as f:
                    while True:
                        chunk = await part.read_chunk(65536)
                        if not chunk:
                            break
                        f.write(chunk)
                saved_files.append(clean_filename)

        return web.json_response({"ok": True, "message": f"Đã tải lên {len(saved_files)} tệp thành công!", "files": saved_files})
    except Exception as e:
        return web.json_response({"ok": False, "error": str(e)}, status=500)


async def handle_api_bot_files_raw(request: web.Request):
    """Phục vụ tệp nhị phân (ảnh, gif, video, âm thanh) trực tiếp qua FileResponse với streaming & range requests."""
    from web.server import get_session, is_admin_session
    sess = get_session(request)
    if not sess or not is_admin_session(sess):
        return web.json_response({"ok": False, "error": "Chỉ Quản trị viên mới có quyền xem tệp media!"}, status=403)

    rel_path = request.query.get("path", "")
    target = resolve_safe_bot_path(rel_path, BASE_DIR)
    if not target or not target.exists() or not target.is_file():
        return web.Response(text="Tệp media không tồn tại", status=404)

    return web.FileResponse(target)


# ==============================================================================
# COGS API HANDLERS
# ==============================================================================

async def handle_api_admin_cogs_list(request: web.Request):
    from web.server import get_session, is_admin_session, BOT_INSTANCE
    sess = get_session(request)
    if not sess or not is_admin_session(sess):
        return web.json_response({"ok": False, "error": "Chỉ Quản trị viên (Admin) mới có quyền xem Cogs!"}, status=403)

    cogs_list = get_registered_extensions(BOT_INSTANCE)
    bot_online = bool(BOT_INSTANCE and getattr(BOT_INSTANCE, "is_ready", lambda: False)())
    loaded_count = sum(1 for c in cogs_list if c["loaded"])

    return web.json_response({
        "ok": True,
        "bot_online": bot_online,
        "total_cogs": len(cogs_list),
        "loaded_count": loaded_count,
        "cogs": cogs_list
    })


async def handle_api_admin_cogs_reload(request: web.Request):
    from web.server import get_session, is_admin_session, BOT_INSTANCE
    sess = get_session(request)
    if not sess or not is_admin_session(sess):
        return web.json_response({"ok": False, "error": "Chỉ Quản trị viên (Admin) mới có quyền nạp lại Cogs!"}, status=403)

    try:
        data = await request.json()
        extension = data.get("extension", "").strip()
        sync_tree = bool(data.get("sync_tree", False))

        if not extension:
            return web.json_response({"ok": False, "error": "Vui lòng chọn extension hoặc chọn 'all' để nạp lại"}, status=400)

        # Nếu user truyền đường dẫn tệp (vd: "Command/bank.py"), chuyển đổi sang tên extension
        converted = get_extension_from_path(extension)
        if converted:
            extension = converted

        result = await reload_extension_action(BOT_INSTANCE, extension, sync_tree=sync_tree)
        status_code = 200 if result.get("ok") else 400
        return web.json_response(result, status=status_code)
    except Exception as e:
        return web.json_response({"ok": False, "error": str(e)}, status=500)


async def handle_api_admin_cogs_sync_tree(request: web.Request):
    from web.server import get_session, is_admin_session, BOT_INSTANCE
    sess = get_session(request)
    if not sess or not is_admin_session(sess):
        return web.json_response({"ok": False, "error": "Chỉ Quản trị viên (Admin) mới có quyền đồng bộ Slash Commands!"}, status=403)

    if not BOT_INSTANCE:
        return web.json_response({"ok": False, "error": "Bot hiện chưa online để đồng bộ cây lệnh!"}, status=503)

    try:
        synced = await BOT_INSTANCE.tree.sync()
        return web.json_response({
            "ok": True,
            "message": f"✅ Đã đồng bộ thành công {len(synced)} lệnh Slash Commands toàn cầu!",
            "commands_count": len(synced)
        })
    except Exception as e:
        return web.json_response({"ok": False, "error": f"Lỗi đồng bộ Slash Commands: {e}"}, status=500)



# ==============================================================================
# HỆ THỐNG ĐỌC CƠ SỞ DỮ LIỆU SQLITE (DATABASE VIEWER)
# ==============================================================================

def get_sqlite_schema(base_dir: Path, rel_path: str) -> Tuple[bool, Any]:
    """Lấy danh sách các bảng, view và cấu trúc cột của tệp SQLite."""
    target_file = resolve_safe_bot_path(rel_path, base_dir)
    if not target_file or not target_file.exists():
        return False, "Tệp cơ sở dữ liệu không tồn tại"
    if not target_file.is_file():
        return False, "Đường dẫn không phải là tệp tin"

    try:
        conn = sqlite3.connect(f"file:{target_file.resolve()}?mode=ro", uri=True)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        cursor.execute("SELECT name, type FROM sqlite_master WHERE type IN ('table', 'view') AND name NOT LIKE 'sqlite_%' ORDER BY name;")
        tables_meta = cursor.fetchall()

        tables_data = []
        for row in tables_meta:
            table_name = row["name"]
            table_type = row["type"]

            # Lấy thông tin các cột
            cursor.execute(f'PRAGMA table_info("{table_name}");')
            columns_info = [
                {
                    "cid": col["cid"],
                    "name": col["name"],
                    "type": col["type"] or "TEXT",
                    "notnull": bool(col["notnull"]),
                    "default_value": col["dflt_value"],
                    "pk": bool(col["pk"])
                }
                for col in cursor.fetchall()
            ]

            # Đếm số bản ghi
            row_count = 0
            try:
                cursor.execute(f'SELECT COUNT(*) FROM "{table_name}";')
                row_count = cursor.fetchone()[0]
            except Exception:
                pass

            tables_data.append({
                "name": table_name,
                "type": table_type,
                "columns": columns_info,
                "row_count": row_count
            })

        conn.close()
        stat = target_file.stat()
        return True, {
            "path": str(target_file.relative_to(base_dir)).replace("\\", "/"),
            "name": target_file.name,
            "size": stat.st_size,
            "mtime": time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(stat.st_mtime)),
            "tables": tables_data,
            "total_tables": len(tables_data)
        }
    except Exception as e:
        return False, f"Lỗi đọc cơ sở dữ liệu SQLite: {e}"


def get_sqlite_table_data(base_dir: Path, rel_path: str, table_name: str, limit: int = 50, offset: int = 0, search: str = "") -> Tuple[bool, Any]:
    """Lấy dữ liệu các dòng trong một bảng có phân trang và tìm kiếm."""
    target_file = resolve_safe_bot_path(rel_path, base_dir)
    if not target_file or not target_file.exists():
        return False, "Tệp cơ sở dữ liệu không tồn tại"

    try:
        conn = sqlite3.connect(f"file:{target_file.resolve()}?mode=ro", uri=True)
        cursor = conn.cursor()

        # Kiểm tra bảng có tồn tại trong sqlite_master không (ngăn chặn SQL Injection)
        cursor.execute("SELECT name FROM sqlite_master WHERE type IN ('table', 'view') AND name = ?;", (table_name,))
        if not cursor.fetchone():
            conn.close()
            return False, f"Bảng `{table_name}` không tồn tại trong cơ sở dữ liệu"

        # Lấy thông tin cột & schema
        cursor.execute(f'PRAGMA table_info("{table_name}");')
        cols = cursor.fetchall()
        col_names = [c[1] for c in cols]
        schema_info = [
            {
                "cid": c[0],
                "name": c[1],
                "type": c[2] or "TEXT",
                "notnull": bool(c[3]),
                "default_value": c[4],
                "pk": bool(c[5])
            }
            for c in cols
        ]

        where_clause = ""
        params = []
        if search and search.strip():
            kw = f"%{search.strip()}%"
            or_parts = [f'CAST("{c.replace('"', '""')}" AS TEXT) LIKE ?' for c in col_names]
            if or_parts:
                where_clause = " WHERE " + " OR ".join(or_parts)
                params = [kw] * len(or_parts)

        # Đếm tổng số dòng
        count_query = f'SELECT COUNT(*) FROM "{table_name}"{where_clause};'
        cursor.execute(count_query, params)
        total_rows = cursor.fetchone()[0]

        # Truy vấn dữ liệu
        data_query = f'SELECT * FROM "{table_name}"{where_clause} LIMIT ? OFFSET ?;'
        cursor.execute(data_query, params + [max(1, min(limit, 500)), max(0, offset)])
        raw_rows = cursor.fetchall()

        # Format các kiểu dữ liệu an toàn cho JSON serialization
        formatted_rows = []
        for r in raw_rows:
            row_dict = {}
            for idx, col_name in enumerate(col_names):
                val = r[idx]
                if isinstance(val, (bytes, bytearray, memoryview)):
                    row_dict[col_name] = f"<BLOB ({len(val)} bytes)>"
                elif isinstance(val, float) and (math.isnan(val) or math.isinf(val)):
                    row_dict[col_name] = str(val)
                elif val is not None and not isinstance(val, (int, float, str, bool)):
                    row_dict[col_name] = str(val)
                else:
                    row_dict[col_name] = val
            formatted_rows.append(row_dict)

        conn.close()
        return True, {
            "table": table_name,
            "columns": col_names,
            "schema": schema_info,
            "rows": formatted_rows,
            "total_rows": total_rows,
            "limit": limit,
            "offset": offset,
            "has_next": (offset + len(formatted_rows)) < total_rows
        }
    except Exception as e:
        return False, f"Lỗi truy vấn dữ liệu bảng `{table_name}`: {e}"


def execute_sqlite_query(base_dir: Path, rel_path: str, query: str) -> Tuple[bool, Any]:
    """Thực thi câu truy vấn SQL đọc dữ liệu (SELECT) an toàn."""
    target_file = resolve_safe_bot_path(rel_path, base_dir)
    if not target_file or not target_file.exists():
        return False, "Tệp cơ sở dữ liệu không tồn tại"

    q_strip = query.strip()
    if not q_strip:
        return False, "Câu truy vấn SQL không được để trống"

    upper_q = q_strip.upper()
    allowed_prefixes = ("SELECT", "PRAGMA", "EXPLAIN", "WITH")
    if not any(upper_q.startswith(prefix) for prefix in allowed_prefixes):
        return False, "Chỉ cho phép thực thi các truy vấn ĐỌC DỮ LIỆU (SELECT, PRAGMA, EXPLAIN) để bảo vệ toàn vẹn dữ liệu!"

    forbidden_keywords = ("INSERT", "UPDATE", "DELETE", "DROP", "ALTER", "CREATE", "TRUNCATE", "ATTACH", "DETACH", "VACUUM")
    for fb in forbidden_keywords:
        if re.search(r'\b' + fb + r'\b', upper_q):
            return False, f"Từ khóa `{fb}` bị cấm trong chế độ xem dữ liệu an toàn!"

    try:
        start_time = time.time()
        conn = sqlite3.connect(f"file:{target_file.resolve()}?mode=ro", uri=True)
        cursor = conn.cursor()

        cursor.execute(q_strip)
        col_names = [desc[0] for desc in cursor.description] if cursor.description else []
        raw_rows = cursor.fetchmany(500)
        elapsed_ms = round((time.time() - start_time) * 1000, 2)

        formatted_rows = []
        for r in raw_rows:
            row_dict = {}
            for idx, col_name in enumerate(col_names):
                val = r[idx]
                if isinstance(val, bytes):
                    row_dict[col_name] = f"<BLOB ({len(val)} bytes)>"
                else:
                    row_dict[col_name] = val
            formatted_rows.append(row_dict)

        conn.close()
        return True, {
            "columns": col_names,
            "rows": formatted_rows,
            "row_count": len(formatted_rows),
            "execution_time_ms": elapsed_ms
        }
    except Exception as e:
        return False, f"Lỗi thực thi SQL: {e}"


# Handlers cho Database APIs
async def handle_api_database_schema(request: web.Request):
    from web.server import get_session, is_admin_session
    sess = get_session(request)
    if not sess or not is_admin_session(sess):
        return web.json_response({"ok": False, "error": "Chỉ Quản trị viên mới có quyền đọc cơ sở dữ liệu!"}, status=403)

    rel_path = request.query.get("path", "")
    ok, result = get_sqlite_schema(BASE_DIR, rel_path)
    if not ok:
        return web.json_response({"ok": False, "error": result}, status=400)
    return web.json_response({"ok": True, **result})


async def handle_api_database_table_data(request: web.Request):
    from web.server import get_session, is_admin_session
    sess = get_session(request)
    if not sess or not is_admin_session(sess):
        return web.json_response({"ok": False, "error": "Chỉ Quản trị viên mới có quyền đọc cơ sở dữ liệu!"}, status=403)

    rel_path = request.query.get("path", "")
    table_name = request.query.get("table", "")
    limit = int(request.query.get("limit", 50))
    offset = int(request.query.get("offset", 0))
    search = request.query.get("search", "")

    ok, result = get_sqlite_table_data(BASE_DIR, rel_path, table_name, limit, offset, search)
    if not ok:
        return web.json_response({"ok": False, "error": result}, status=400)
    return web.json_response({"ok": True, **result})


async def handle_api_database_query(request: web.Request):
    from web.server import get_session, is_admin_session
    sess = get_session(request)
    if not sess or not is_admin_session(sess):
        return web.json_response({"ok": False, "error": "Chỉ Quản trị viên mới có quyền truy vấn cơ sở dữ liệu!"}, status=403)

    try:
        data = await request.json()
        rel_path = data.get("path", "")
        query = data.get("query", "")

        ok, result = execute_sqlite_query(BASE_DIR, rel_path, query)
        if not ok:
            return web.json_response({"ok": False, "error": result}, status=400)
        return web.json_response({"ok": True, **result})
    except Exception as e:
        return web.json_response({"ok": False, "error": str(e)}, status=500)
