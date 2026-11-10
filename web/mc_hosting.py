import os
import shutil
import time
import re
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
import psutil

_prev_net_io = None
_prev_net_time = 0

def get_server_dir(server_id: str, base_dir: Path) -> Optional[Path]:
    """Lấy thư mục server an toàn, ngăn chặn directory traversal."""
    if not server_id or not re.match(r'^[a-zA-Z0-9_\-\.]+$', server_id):
        return None
    target = (base_dir / server_id).resolve()
    base_res = base_dir.resolve()
    try:
        if not target.is_relative_to(base_res):
            return None
    except AttributeError:
        if not str(target).startswith(str(base_res)):
            return None
    if target.exists() and target.is_dir():
        return target
    return None

def scan_mc_servers(base_dir: Path) -> List[Dict[str, Any]]:
    """Quét các thư mục máy chủ Minecraft trong thư mục gốc của bot."""
    servers = []
    base_res = base_dir.resolve()
    if not base_res.exists():
        return []

    ignored_dirs = {"cache", "downloads", "node_modules", "venv", ".git", ".paper", "logs", "plugin", "libraries", "view", "project"}

    for entry in base_res.iterdir():
        if not entry.is_dir() or entry.name.startswith(".") or entry.name.lower() in ignored_dirs:
            continue
        has_props = (entry / "server.properties").exists()
        has_server_jar = (entry / "server.jar").exists()
        is_server_named = entry.name.lower() == "server" or entry.name.lower().startswith("server_") or entry.name.lower().startswith("mc_")

        if (has_props and has_server_jar) or is_server_named or (has_props and (entry / "bukkit.yml").exists()):
            srv_info = get_server_summary(entry)
            servers.append(srv_info)

    return servers

def parse_properties_file(props_path: Path) -> Tuple[Dict[str, str], str]:
    """Đọc và phân tích file server.properties."""
    props = {}
    raw_content = ""
    if props_path.exists():
        try:
            with open(props_path, "r", encoding="utf-8", errors="ignore") as f:
                raw_content = f.read()
            for line in raw_content.splitlines():
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    key, val = line.split("=", 1)
                    props[key.strip()] = val.strip()
        except Exception:
            pass
    return props, raw_content

def get_server_process(server_dir: Path) -> Optional[psutil.Process]:
    """Tìm tiến trình Java đang chạy server Minecraft này."""
    dir_str = str(server_dir.resolve()).lower()
    for proc in psutil.process_iter(['pid', 'name', 'cmdline', 'cwd']):
        try:
            cmd = proc.info.get('cmdline') or []
            cwd = str(proc.info.get('cwd') or '').lower()
            cmd_str = " ".join(cmd).lower()
            if "server.jar" in cmd_str or "paper" in cmd_str or "spigot" in cmd_str or "minecraft" in cmd_str:
                if dir_str in cwd or any(dir_str in arg.lower() for arg in cmd):
                    return proc
                if server_dir.name.lower() == "server":
                    return proc
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue
    return None

def get_server_summary(server_dir: Path) -> Dict[str, Any]:
    """Lấy tóm tắt trạng thái của một máy chủ."""
    props_path = server_dir / "server.properties"
    props, _ = parse_properties_file(props_path)

    proc = get_server_process(server_dir)
    is_online = proc is not None

    cpu_percent = 0.0
    mem_mb = 0.0
    pid = None

    if proc:
        try:
            pid = proc.pid
            cpu_percent = round(proc.cpu_percent(interval=None), 1)
            mem_info = proc.memory_info()
            mem_mb = round(mem_info.rss / (1024 * 1024), 1)
        except Exception:
            pass

    dir_size_mb = 0.0
    try:
        total_b = 0
        for root, _, files in os.walk(server_dir):
            for f in files:
                try:
                    total_b += os.path.getsize(os.path.join(root, f))
                except Exception:
                    pass
        dir_size_mb = round(total_b / (1024 * 1024), 1)
    except Exception:
        pass

    try:
        disk_usage = shutil.disk_usage(server_dir)
        disk_total_gb = round(disk_usage.total / (1024 ** 3), 1)
        disk_free_gb = round(disk_usage.free / (1024 ** 3), 1)
    except Exception:
        disk_total_gb = 0.0
        disk_free_gb = 0.0

    motd = props.get("motd", "Sakura Minecraft Server")
    clean_motd = re.sub(r'§[0-9a-fk-or]', '', motd)
    port = int(props.get("server-port", 25565))
    ip = props.get("server-ip", "") or "127.0.0.1"

    version = "1.20.1 (Paper/Spigot)"
    ver_file = server_dir / "version_history.json"
    if ver_file.exists():
        try:
            with open(ver_file, "r", encoding="utf-8") as f:
                ver_text = f.read()
                m = re.search(r'([0-9]+\.[0-9]+(\.[0-9]+)?)', ver_text)
                if m:
                    version = f"{m.group(1)} (Paper)"
        except Exception:
            pass

    return {
        "id": server_dir.name,
        "name": props.get("server-name") or clean_motd or server_dir.name,
        "folder": server_dir.name,
        "path": str(server_dir),
        "is_online": is_online,
        "pid": pid,
        "ip": ip,
        "port": port,
        "motd": clean_motd,
        "version": version,
        "gamemode": props.get("gamemode", "survival"),
        "difficulty": props.get("difficulty", "normal"),
        "online_mode": props.get("online-mode", "true").lower() == "true",
        "max_players": int(props.get("max-players", 20)),
        "players_online": 0,
        "cpu_percent": cpu_percent,
        "memory_mb": mem_mb,
        "dir_size_mb": dir_size_mb,
        "disk_total_gb": disk_total_gb,
        "disk_free_gb": disk_free_gb,
    }

def get_system_metrics(server_dir: Path) -> Dict[str, Any]:
    """Lấy dữ liệu giám sát tài nguyên phần cứng thời gian thực."""
    global _prev_net_io, _prev_net_time

    sys_cpu = round(psutil.cpu_percent(interval=None), 1)
    vm = psutil.virtual_memory()
    sys_ram_used_mb = round(vm.used / (1024 * 1024), 1)
    sys_ram_total_mb = round(vm.total / (1024 * 1024), 1)
    sys_ram_percent = vm.percent

    try:
        du = shutil.disk_usage(server_dir)
        disk_used_gb = round(du.used / (1024 ** 3), 1)
        disk_total_gb = round(du.total / (1024 ** 3), 1)
        disk_percent = round((du.used / du.total) * 100, 1)
    except Exception:
        disk_used_gb = 0.0
        disk_total_gb = 0.0
        disk_percent = 0.0

    net_io = psutil.net_io_counters()
    now = time.time()
    net_up_speed_kb = 0.0
    net_down_speed_kb = 0.0
    if _prev_net_io and (now - _prev_net_time) > 0:
        dt = now - _prev_net_time
        net_up_speed_kb = round((net_io.bytes_sent - _prev_net_io.bytes_sent) / (1024 * dt), 1)
        net_down_speed_kb = round((net_io.bytes_recv - _prev_net_io.bytes_recv) / (1024 * dt), 1)
    _prev_net_io = net_io
    _prev_net_time = now

    proc = get_server_process(server_dir)
    srv_cpu = 0.0
    srv_ram_mb = 0.0
    srv_uptime = 0
    if proc:
        try:
            srv_cpu = round(proc.cpu_percent(interval=None), 1)
            srv_ram_mb = round(proc.memory_info().rss / (1024 * 1024), 1)
            srv_uptime = int(time.time() - proc.create_time())
        except Exception:
            pass

    return {
        "is_online": proc is not None,
        "sys_cpu": sys_cpu,
        "sys_ram_used_mb": sys_ram_used_mb,
        "sys_ram_total_mb": sys_ram_total_mb,
        "sys_ram_percent": sys_ram_percent,
        "disk_used_gb": disk_used_gb,
        "disk_total_gb": disk_total_gb,
        "disk_percent": disk_percent,
        "net_up_speed_kb": net_up_speed_kb,
        "net_down_speed_kb": net_down_speed_kb,
        "srv_cpu": srv_cpu,
        "srv_ram_mb": srv_ram_mb,
        "srv_uptime_sec": srv_uptime,
        "timestamp": int(now)
    }

def read_console_tail(server_dir: Path, max_lines: int = 150) -> List[str]:
    """Đọc các dòng log cuối cùng từ logs/latest.log."""
    log_path = server_dir / "logs" / "latest.log"
    if not log_path.exists():
        return ["[Sakura MC] Chưa tìm thấy file logs/latest.log. Server chưa khởi động hoặc chưa tạo log."]

    try:
        with open(log_path, "r", encoding="utf-8", errors="ignore") as f:
            lines = f.readlines()
            return [l.rstrip("\r\n") for l in lines[-max_lines:]]
    except Exception as e:
        return [f"[Sakura MC Error] Không thể đọc log: {e}"]

def format_size(bytes_val: int) -> str:
    """Định dạng byte sang KB, MB, GB dễ đọc."""
    if bytes_val < 1024:
        return f"{bytes_val} B"
    elif bytes_val < 1024 ** 2:
        return f"{bytes_val / 1024:.1f} KB"
    elif bytes_val < 1024 ** 3:
        return f"{bytes_val / (1024 ** 2):.1f} MB"
    else:
        return f"{bytes_val / (1024 ** 3):.2f} GB"

def get_dir_size_recursive(path: Path) -> int:
    """Tính tổng dung lượng thư mục."""
    total = 0
    if not path.exists():
        return 0
    if path.is_file():
        return path.stat().st_size
    for entry in path.rglob('*'):
        if entry.is_file():
            try:
                total += entry.stat().st_size
            except Exception:
                pass
    return total

def get_files_in_dir(server_dir: Path, rel_path: str = "") -> Tuple[bool, Any]:
    """Lấy danh sách các tệp và thư mục con một cách an toàn."""
    clean_rel = rel_path.strip().lstrip("/\\")
    target = (server_dir / clean_rel).resolve()
    srv_res = server_dir.resolve()

    try:
        if not target.is_relative_to(srv_res):
            return False, "Truy cập trái phép: Đường dẫn nằm ngoài thư mục máy chủ"
    except AttributeError:
        if not str(target).startswith(str(srv_res)):
            return False, "Truy cập trái phép: Đường dẫn nằm ngoài thư mục máy chủ"

    if not target.exists():
        return False, f"Đường dẫn không tồn tại: {clean_rel}"
    if not target.is_dir():
        return False, f"Đường dẫn không phải thư mục: {clean_rel}"

    items = []
    try:
        for entry in sorted(target.iterdir(), key=lambda x: (not x.is_dir(), x.name.lower())):
            entry_rel = str(entry.relative_to(srv_res)).replace("\\", "/")
            stat = entry.stat()
            is_dir = entry.is_dir()
            size_b = stat.st_size if not is_dir else 0
            ext = entry.suffix.lower().lstrip(".")

            items.append({
                "name": entry.name,
                "rel_path": entry_rel,
                "is_dir": is_dir,
                "size": size_b,
                "size_formatted": format_size(size_b) if not is_dir else "--",
                "modified": int(stat.st_mtime),
                "extension": ext
            })
    except Exception as e:
        return False, f"Lỗi đọc thư mục: {e}"

    disk_analysis = {}
    try:
        total_server_b = 0
        for entry in srv_res.iterdir():
            s = get_dir_size_recursive(entry)
            total_server_b += s
            disk_analysis[entry.name] = {
                "size": s,
                "formatted": format_size(s),
                "is_dir": entry.is_dir()
            }
        disk_analysis["_total"] = {
            "size": total_server_b,
            "formatted": format_size(total_server_b)
        }
    except Exception:
        pass

    return True, {
        "current_path": clean_rel,
        "items": items,
        "disk_analysis": disk_analysis
    }

def read_file_safe(server_dir: Path, rel_path: str) -> Tuple[bool, Any]:
    """Đọc nội dung file text/code trong thư mục server."""
    clean_rel = rel_path.strip().lstrip("/\\")
    target = (server_dir / clean_rel).resolve()
    srv_res = server_dir.resolve()

    try:
        if not target.is_relative_to(srv_res):
            return False, "Truy cập trái phép: Vượt khỏi thư mục máy chủ"
    except AttributeError:
        if not str(target).startswith(str(srv_res)):
            return False, "Truy cập trái phép: Vượt khỏi thư mục máy chủ"

    if not target.exists() or not target.is_file():
        return False, "File không tồn tại"

    if target.stat().st_size > 4 * 1024 * 1024:
        return False, "File quá lớn để chỉnh sửa trên trình duyệt (giới hạn 4MB)"

    try:
        with open(target, "r", encoding="utf-8", errors="ignore") as f:
            content = f.read()
        return True, {
            "name": target.name,
            "rel_path": clean_rel,
            "size": target.stat().st_size,
            "extension": target.suffix.lower().lstrip("."),
            "content": content
        }
    except Exception as e:
        return False, f"Lỗi đọc file: {e}"

def save_file_safe(server_dir: Path, rel_path: str, content: str) -> Tuple[bool, str]:
    """Lưu nội dung file an toàn, tự động tạo backup .bak."""
    clean_rel = rel_path.strip().lstrip("/\\")
    target = (server_dir / clean_rel).resolve()
    srv_res = server_dir.resolve()

    try:
        if not target.is_relative_to(srv_res):
            return False, "Truy cập trái phép: Vượt khỏi thư mục máy chủ"
    except AttributeError:
        if not str(target).startswith(str(srv_res)):
            return False, "Truy cập trái phép: Vượt khỏi thư mục máy chủ"

    try:
        if target.exists() and target.is_file():
            bak_path = target.with_suffix(target.suffix + ".bak")
            try:
                shutil.copy2(target, bak_path)
            except Exception:
                pass

        target.parent.mkdir(parents=True, exist_ok=True)
        with open(target, "w", encoding="utf-8") as f:
            f.write(content)
        return True, "Đã lưu tệp thành công!"
    except Exception as e:
        return False, f"Lỗi ghi file: {e}"

def create_item_safe(server_dir: Path, rel_path: str, name: str, is_folder: bool) -> Tuple[bool, str]:
    """Tạo file mới hoặc thư mục mới an toàn."""
    clean_rel = rel_path.strip().lstrip("/\\")
    clean_name = name.strip()
    if not clean_name or "/" in clean_name or "\\" in clean_name or clean_name in (".", ".."):
        return False, "Tên tệp hoặc thư mục không hợp lệ"

    parent_dir = (server_dir / clean_rel).resolve()
    srv_res = server_dir.resolve()

    try:
        if not parent_dir.is_relative_to(srv_res):
            return False, "Đường dẫn không hợp lệ"
    except AttributeError:
        if not str(parent_dir).startswith(str(srv_res)):
            return False, "Đường dẫn không hợp lệ"

    target = parent_dir / clean_name
    if target.exists():
        return False, f"Tệp hoặc thư mục '{clean_name}' đã tồn tại"

    try:
        if is_folder:
            target.mkdir(parents=True, exist_ok=True)
            return True, f"Đã tạo thư mục '{clean_name}' thành công"
        else:
            target.touch()
            return True, f"Đã tạo tệp '{clean_name}' thành công"
    except Exception as e:
        return False, f"Lỗi tạo tệp/thư mục: {e}"

def delete_item_safe(server_dir: Path, rel_path: str) -> Tuple[bool, str]:
    """Xóa file hoặc thư mục an toàn."""
    clean_rel = rel_path.strip().lstrip("/\\")
    if not clean_rel or clean_rel in (".", ".."):
        return False, "Không thể xóa thư mục gốc"

    target = (server_dir / clean_rel).resolve()
    srv_res = server_dir.resolve()

    try:
        if not target.is_relative_to(srv_res) or target == srv_res:
            return False, "Truy cập trái phép: Không thể xóa thư mục máy chủ"
    except AttributeError:
        if not str(target).startswith(str(srv_res)) or target == srv_res:
            return False, "Truy cập trái phép: Không thể xóa thư mục máy chủ"

    if not target.exists():
        return False, "Tệp hoặc thư mục không tồn tại"

    try:
        if target.is_dir():
            shutil.rmtree(target)
            return True, f"Đã xóa thư mục '{target.name}'"
        else:
            target.unlink()
            return True, f"Đã xóa tệp '{target.name}'"
    except Exception as e:
        return False, f"Lỗi xóa: {e}"

def rename_item_safe(server_dir: Path, rel_path: str, new_name: str) -> Tuple[bool, str]:
    """Đổi tên file hoặc thư mục an toàn."""
    clean_rel = rel_path.strip().lstrip("/\\")
    clean_new_name = new_name.strip()
    if not clean_new_name or "/" in clean_new_name or "\\" in clean_new_name or clean_new_name in (".", ".."):
        return False, "Tên mới không hợp lệ"

    target = (server_dir / clean_rel).resolve()
    srv_res = server_dir.resolve()

    try:
        if not target.is_relative_to(srv_res) or target == srv_res:
            return False, "Truy cập trái phép"
    except AttributeError:
        if not str(target).startswith(str(srv_res)) or target == srv_res:
            return False, "Truy cập trái phép"

    if not target.exists():
        return False, "Tệp hoặc thư mục không tồn tại"

    dest = target.parent / clean_new_name
    if dest.exists():
        return False, f"Tên '{clean_new_name}' đã tồn tại"

    try:
        target.rename(dest)
        return True, f"Đã đổi tên thành '{clean_new_name}'"
    except Exception as e:
        return False, f"Lỗi đổi tên: {e}"

def update_server_properties(server_dir: Path, updates: Optional[Dict[str, Any]] = None, raw_content: Optional[str] = None) -> Tuple[bool, str]:
    """Cập nhật file server.properties."""
    props_path = server_dir / "server.properties"
    try:
        if props_path.exists():
            shutil.copy2(props_path, props_path.with_suffix(".properties.bak"))

        if raw_content is not None:
            with open(props_path, "w", encoding="utf-8") as f:
                f.write(raw_content)
            return True, "Đã lưu cài đặt server.properties thành công!"

        if updates:
            lines = []
            existing_keys = set()
            if props_path.exists():
                with open(props_path, "r", encoding="utf-8", errors="ignore") as f:
                    lines = f.readlines()

            new_lines = []
            for line in lines:
                raw_line = line.strip()
                if raw_line and not raw_line.startswith("#") and "=" in raw_line:
                    k, _ = raw_line.split("=", 1)
                    k = k.strip()
                    existing_keys.add(k)
                    if k in updates:
                        new_lines.append(f"{k}={updates[k]}\n")
                    else:
                        new_lines.append(line)
                else:
                    new_lines.append(line)

            for k, v in updates.items():
                if k not in existing_keys:
                    new_lines.append(f"{k}={v}\n")

            with open(props_path, "w", encoding="utf-8") as f:
                f.writelines(new_lines)

            return True, "Đã cập nhật cài đặt server.properties thành công!"

        return False, "Không có nội dung cập nhật"
    except Exception as e:
        return False, f"Lỗi lưu server.properties: {e}"


def update_server_icon(server_dir: Path, image_bytes: bytes) -> Tuple[bool, str]:
    """Cập nhật icon server Minecraft (chuẩn 64x64 PNG)."""
    try:
        from PIL import Image
        import io
        img = Image.open(io.BytesIO(image_bytes))
        img = img.resize((64, 64), Image.Resampling.LANCZOS)
        if img.mode != 'RGBA':
            img = img.convert('RGBA')
        dest = server_dir / "server-icon.png"
        img.save(dest, format="PNG")
        return True, "Đã cập nhật icon máy chủ (64x64 PNG) thành công!"
    except Exception as e:
        return False, f"Lỗi xử lý hình ảnh icon: {e}"


def get_mc_permissions(data_dir: Path) -> Dict[str, Any]:
    """Lấy danh sách người dùng và quyền hạn MC hosting."""
    perm_file = data_dir / "mc_permissions.json"
    if not perm_file.exists():
        return {"users": {}}
    try:
        import json
        with open(perm_file, "r", encoding="utf-8") as f:
            data = json.load(f)
            if not isinstance(data, dict):
                return {"users": {}}
            if "users" not in data or not isinstance(data["users"], dict):
                data["users"] = {}
            return data
    except Exception:
        return {"users": {}}

def save_mc_permissions_data(data_dir: Path, data: Dict[str, Any]) -> bool:
    """Lưu dữ liệu quyền hạn."""
    try:
        import json
        perm_file = data_dir / "mc_permissions.json"
        perm_file.parent.mkdir(parents=True, exist_ok=True)
        with open(perm_file, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        return True
    except Exception:
        return False

def save_mc_user_permission(data_dir: Path, user_info: Dict[str, Any]) -> Tuple[bool, str]:
    """Lưu hoặc cập nhật quyền của một user."""
    raw_uid = str(user_info.get("user_id") or user_info.get("discord_id") or "").strip()
    if not raw_uid:
        return False, "Thiếu Discord User ID"

    data = get_mc_permissions(data_dir)
    default_perms = {
        "can_view_console": True,
        "can_send_command": False,
        "can_manage_power": False,
        "can_manage_files": False,
        "can_manage_properties": False,
        "can_view_players": True
    }
    cur_user = data["users"].get(raw_uid, {})
    user_perms = user_info.get("permissions") or cur_user.get("permissions") or default_perms

    data["users"][raw_uid] = {
        "user_id": raw_uid,
        "username": str(user_info.get("username") or cur_user.get("username") or f"User_{raw_uid[-4:]}"),
        "avatar": str(user_info.get("avatar") or cur_user.get("avatar") or "https://cdn.discordapp.com/embed/avatars/0.png"),
        "role": str(user_info.get("role") or cur_user.get("role") or "viewer"),
        "permissions": {
            "can_view_console": bool(user_perms.get("can_view_console", False)),
            "can_send_command": bool(user_perms.get("can_send_command", False)),
            "can_manage_power": bool(user_perms.get("can_manage_power", False)),
            "can_manage_files": bool(user_perms.get("can_manage_files", False)),
            "can_manage_properties": bool(user_perms.get("can_manage_properties", False)),
            "can_view_players": bool(user_perms.get("can_view_players", False))
        },
        "updated_at": int(time.time())
    }

    ok = save_mc_permissions_data(data_dir, data)
    if ok:
        return True, f"Đã lưu quyền cho người dùng {data['users'][raw_uid]['username']}!"
    return False, "Không thể lưu tệp quyền hạn mc_permissions.json"

def delete_mc_user_permission(data_dir: Path, user_id: str) -> Tuple[bool, str]:
    """Xóa quyền hạn của một user."""
    raw_uid = str(user_id).strip()
    data = get_mc_permissions(data_dir)
    if raw_uid in data["users"]:
        del data["users"][raw_uid]
        save_mc_permissions_data(data_dir, data)
        return True, "Đã xóa phân quyền người dùng!"
    return False, "Không tìm thấy người dùng này trong danh sách phân quyền"

def check_mc_permission_access(data_dir: Path, sess: Optional[Dict[str, Any]], perm_name: str) -> bool:
    """Kiểm tra quyền hạn của session người dùng hiện tại."""
    if not sess:
        return False
    did = str(sess.get("discord_id") or sess.get("user_id") or "")
    u = (sess.get("username") or "").lower()
    tag = (sess.get("tag") or "").lower()
    try:
        from config import OWNER_ID
        owner_str = str(OWNER_ID)
    except Exception:
        owner_str = "1144785664458637394"

    if did == owner_str or did == "1144785664458637394" or "linhxinh_dev" in u or "linhxinh_dev" in tag or u in ("linhxinh", "owner"):
        return True
    if sess.get("is_owner") or sess.get("extra", {}).get("is_owner") or sess.get("role") == "admin" or sess.get("user_role") == "admin":
        return True

    data = get_mc_permissions(data_dir)
    user_entry = data.get("users", {}).get(did)
    if not user_entry:
        return False
    if user_entry.get("role") == "admin":
        return True
    perms = user_entry.get("permissions", {})
    return bool(perms.get(perm_name, False))


def parse_nbt_stream(data: bytes) -> Dict[str, Any]:
    """Bộ giải mã NBT thuần Python (Named Binary Tag) hỗ trợ đầy đủ Minecraft Dat."""
    import struct
    offset = 0
    dlen = len(data)

    def read_byte() -> int:
        nonlocal offset
        if offset >= dlen: return 0
        v = data[offset]
        offset += 1
        return v

    def read_short() -> int:
        nonlocal offset
        if offset + 2 > dlen: return 0
        v = struct.unpack('>h', data[offset:offset+2])[0]
        offset += 2
        return v

    def read_int() -> int:
        nonlocal offset
        if offset + 4 > dlen: return 0
        v = struct.unpack('>i', data[offset:offset+4])[0]
        offset += 4
        return v

    def read_long() -> int:
        nonlocal offset
        if offset + 8 > dlen: return 0
        v = struct.unpack('>q', data[offset:offset+8])[0]
        offset += 8
        return v

    def read_float() -> float:
        nonlocal offset
        if offset + 4 > dlen: return 0.0
        v = struct.unpack('>f', data[offset:offset+4])[0]
        offset += 4
        return v

    def read_double() -> float:
        nonlocal offset
        if offset + 8 > dlen: return 0.0
        v = struct.unpack('>d', data[offset:offset+8])[0]
        offset += 8
        return v

    def read_string() -> str:
        nonlocal offset
        l = read_short()
        if l <= 0 or offset + l > dlen: return ""
        s = data[offset:offset+l].decode('utf-8', errors='replace')
        offset += l
        return s

    def parse_payload(tag_type: int) -> Any:
        nonlocal offset
        if tag_type == 0:
            return None
        elif tag_type == 1:
            return read_byte()
        elif tag_type == 2:
            return read_short()
        elif tag_type == 3:
            return read_int()
        elif tag_type == 4:
            return read_long()
        elif tag_type == 5:
            return round(read_float(), 2)
        elif tag_type == 6:
            return round(read_double(), 2)
        elif tag_type == 7:
            length = read_int()
            if length <= 0 or offset + length > dlen: return []
            res = list(data[offset:offset+length])
            offset += length
            return res
        elif tag_type == 8:
            return read_string()
        elif tag_type == 9:
            elem_type = read_byte()
            length = read_int()
            if length <= 0: return []
            return [parse_payload(elem_type) for _ in range(length)]
        elif tag_type == 10:
            compound = {}
            while offset < dlen:
                ttype = read_byte()
                if ttype == 0:
                    break
                tname = read_string()
                compound[tname] = parse_payload(ttype)
            return compound
        elif tag_type == 11:
            length = read_int()
            if length <= 0: return []
            return [read_int() for _ in range(length)]
        elif tag_type == 12:
            length = read_int()
            if length <= 0: return []
            return [read_long() for _ in range(length)]
        return None

    if dlen == 0:
        return {}
    root_type = read_byte()
    if root_type != 10:
        return {}
    read_string()
    return parse_payload(10) or {}

def _extract_text_component(comp: Any) -> str:
    """Trích xuất chuỗi văn bản sạch từ Minecraft JSON text component."""
    if isinstance(comp, str):
        return comp
    if isinstance(comp, dict):
        text = str(comp.get("text", ""))
        extra = comp.get("extra", [])
        if isinstance(extra, list):
            for part in extra:
                text += _extract_text_component(part)
        return text
    return str(comp)

def parse_mc_item(it: Dict[str, Any]) -> Dict[str, Any]:
    """Phân tích một vật phẩm Minecraft (Inventory, EnderChest, ShulkerBox) sang dạng hiển thị."""
    if not isinstance(it, dict):
        return {"id": "air", "name": "Không có", "count": 0, "lore": [], "enchantments": [], "is_shulker": False, "shulker_items": []}

    raw_id = str(it.get("id") or "")
    clean_id = raw_id.replace("minecraft:", "").lower()
    count = int(it.get("count") or it.get("Count") or 1)
    slot = int(it.get("Slot") if it.get("Slot") is not None else (it.get("slot") or 0))
    components = it.get("components") if isinstance(it.get("components"), dict) else {}
    tag = it.get("tag") if isinstance(it.get("tag"), dict) else {}

    name = ""
    raw_name = components.get("minecraft:custom_name") or tag.get("display", {}).get("Name")
    if raw_name:
        name = _extract_text_component(raw_name)
    if not name:
        name = clean_id.replace("_", " ").title()

    lore = []
    raw_lore = components.get("minecraft:lore") or tag.get("display", {}).get("Lore", [])
    if isinstance(raw_lore, list):
        for line in raw_lore:
            cleaned_line = _extract_text_component(line).strip()
            if cleaned_line:
                lore.append(cleaned_line)

    enchants = []
    raw_ench = components.get("minecraft:enchantments") or tag.get("Enchantments", [])
    if isinstance(raw_ench, dict):
        for ek, ev in raw_ench.items():
            en_name = str(ek).replace("minecraft:", "").replace("_", " ").title()
            enchants.append(f"{en_name} {ev}")
    elif isinstance(raw_ench, list):
        for e in raw_ench:
            if isinstance(e, dict):
                eid = str(e.get("id", "")).replace("minecraft:", "").replace("_", " ").title()
                lvl = e.get("lvl", 1)
                enchants.append(f"{eid} {lvl}")

    is_shulker = "shulker_box" in clean_id
    shulker_items = []
    if is_shulker:
        cont = components.get("minecraft:container", [])
        if isinstance(cont, list):
            for c_entry in cont:
                if isinstance(c_entry, dict) and "item" in c_entry:
                    c_slot = int(c_entry.get("slot", 0))
                    c_item = c_entry.get("item", {})
                    if isinstance(c_item, dict):
                        sub_parsed = parse_mc_item(dict(c_item, slot=c_slot))
                        shulker_items.append(sub_parsed)
        bet = tag.get("BlockEntityTag", {}).get("Items", [])
        if isinstance(bet, list):
            for b_it in bet:
                if isinstance(b_it, dict):
                    shulker_items.append(parse_mc_item(b_it))

    return {
        "slot": slot,
        "id": clean_id,
        "raw_id": raw_id,
        "name": name,
        "count": count,
        "lore": lore,
        "enchantments": enchants,
        "is_shulker": is_shulker,
        "shulker_items": shulker_items,
        "icon_url": f"https://raw.githubusercontent.com/PrismarineJS/minecraft-assets/master/data/1.20.4/items/{clean_id}.png"
    }

def find_player_dat_files(server_dir: Path) -> Dict[str, Path]:
    """Tìm tất cả các tệp playerdata .dat trong server."""
    candidate_dirs = [
        server_dir / "world" / "players" / "data",
        server_dir / "world" / "playerdata",
        server_dir / "world" / "players",
        server_dir / "playerdata"
    ]
    for w in server_dir.glob("world*"):
        if w.is_dir():
            candidate_dirs.append(w / "playerdata")
            candidate_dirs.append(w / "players" / "data")

    found = {}
    for d in candidate_dirs:
        if d.exists() and d.is_dir():
            for f in d.glob("*.dat"):
                if f.stem.lower() not in ("level", "session", "stats"):
                    found[f.stem.lower()] = f
    return found

def get_server_players(server_dir: Path) -> List[Dict[str, Any]]:
    """Lấy danh sách người chơi đã từng tham gia máy chủ cùng thông tin cơ bản."""
    import json
    import gzip

    cache_users = {}
    uc_path = server_dir / "usercache.json"
    if uc_path.exists():
        try:
            with open(uc_path, "r", encoding="utf-8") as f:
                raw_users = json.load(f)
                if isinstance(raw_users, list):
                    for u in raw_users:
                        uuid_str = str(u.get("uuid", "")).lower()
                        if uuid_str:
                            cache_users[uuid_str] = {
                                "uuid": uuid_str,
                                "name": u.get("name", "Unknown"),
                                "expiresOn": u.get("expiresOn", "")
                            }
        except Exception:
            pass

    dat_files = find_player_dat_files(server_dir)

    ess_dir = server_dir / "plugins" / "Essentials" / "userdata"
    ess_data = {}
    if ess_dir.exists():
        for yml_file in ess_dir.glob("*.yml"):
            u_key = yml_file.stem.lower()
            try:
                content = yml_file.read_text(encoding="utf-8", errors="ignore")
                money = "0"
                last_logout = 0
                acc_name = ""
                for line in content.splitlines():
                    line = line.strip()
                    if line.startswith("money:"):
                        money = line.split(":", 1)[1].strip().strip("'\"")
                    elif line.startswith("logout:"):
                        try:
                            last_logout = int(line.split(":", 1)[1].strip())
                        except Exception:
                            pass
                    elif line.startswith("last-account-name:"):
                        acc_name = line.split(":", 1)[1].strip().strip("'\"")
                ess_data[u_key] = {
                    "money": money,
                    "last_logout": last_logout,
                    "account_name": acc_name
                }
            except Exception:
                pass

    all_uuids = set(cache_users.keys()) | set(dat_files.keys()) | set(ess_data.keys())
    results = []

    for uuid_str in all_uuids:
        name = ""
        if uuid_str in cache_users:
            name = cache_users[uuid_str]["name"]
        elif uuid_str in ess_data and ess_data[uuid_str].get("account_name"):
            name = ess_data[uuid_str]["account_name"]
        else:
            name = f"Player_{uuid_str[:8]}"

        has_dat = uuid_str in dat_files
        dat_mtime = int(dat_files[uuid_str].stat().st_mtime) if has_dat else 0

        health = 20.0
        food = 20
        level = 0
        gamemode = 0

        if has_dat:
            try:
                with gzip.open(dat_files[uuid_str], "rb") as gf:
                    raw_bytes = gf.read()
                pdata = parse_nbt_stream(raw_bytes)
                health = float(pdata.get("Health", 20.0))
                food = int(pdata.get("foodLevel", 20))
                level = int(pdata.get("XpLevel", 0))
                gamemode = int(pdata.get("playerGameType", 0))
            except Exception:
                pass

        money_str = ess_data.get(uuid_str, {}).get("money", "0")
        logout_ts = ess_data.get(uuid_str, {}).get("last_logout", 0)
        if logout_ts > 0:
            last_seen_sec = logout_ts // 1000
        else:
            last_seen_sec = dat_mtime

        gm_labels = {0: "Sinh Tồn (Survival)", 1: "Sáng Tạo (Creative)", 2: "Phiêu Lưu (Adventure)", 3: "Khán Giả (Spectator)"}

        results.append({
            "uuid": uuid_str,
            "name": name,
            "has_dat": has_dat,
            "health": round(health, 1),
            "food": food,
            "level": level,
            "gamemode": gamemode,
            "gamemode_label": gm_labels.get(gamemode, "Sinh Tồn"),
            "money": money_str,
            "last_seen": last_seen_sec,
            "avatar_url": f"https://mc-heads.net/avatar/{uuid_str}/64",
            "body_url": f"https://mc-heads.net/body/{uuid_str}/right"
        })

    results.sort(key=lambda x: x["last_seen"], reverse=True)
    return results

def get_player_detail(server_dir: Path, uuid_or_name: str) -> Optional[Dict[str, Any]]:
    """Lấy chi tiết dữ liệu người chơi: túi đồ, trang bị, rương Ender, Shulker box."""
    import gzip
    target = uuid_or_name.strip().lower()
    dat_files = find_player_dat_files(server_dir)

    matched_uuid = None
    target_dat = None

    if target in dat_files:
        matched_uuid = target
        target_dat = dat_files[target]
    else:
        players = get_server_players(server_dir)
        for p in players:
            if p["name"].lower() == target or p["uuid"] == target:
                matched_uuid = p["uuid"]
                if matched_uuid in dat_files:
                    target_dat = dat_files[matched_uuid]
                break

    if not target_dat or not target_dat.exists():
        return None

    try:
        with gzip.open(target_dat, "rb") as gf:
            raw_bytes = gf.read()
        pdata = parse_nbt_stream(raw_bytes)
    except Exception:
        return None

    players = get_server_players(server_dir)
    p_info = next((p for p in players if p["uuid"] == matched_uuid), None)
    player_name = p_info["name"] if p_info else f"Player_{matched_uuid[:8]}"

    raw_inv = pdata.get("Inventory", [])
    hotbar = [None] * 9
    main_inv = [None] * 27
    armor = {"helmet": None, "chestplate": None, "leggings": None, "boots": None}
    offhand = None

    for it in raw_inv:
        parsed = parse_mc_item(it)
        s = parsed["slot"]
        if 0 <= s <= 8:
            hotbar[s] = parsed
        elif 9 <= s <= 35:
            main_inv[s - 9] = parsed
        elif s == 103:
            armor["helmet"] = parsed
        elif s == 102:
            armor["chestplate"] = parsed
        elif s == 101:
            armor["leggings"] = parsed
        elif s == 100:
            armor["boots"] = parsed
        elif s == -106:
            offhand = parsed

    raw_ender = pdata.get("EnderItems", [])
    ender_chest = [None] * 27
    for it in raw_ender:
        parsed = parse_mc_item(it)
        s = parsed["slot"]
        if 0 <= s < 27:
            ender_chest[s] = parsed

    pos = pdata.get("Pos", [0.0, 0.0, 0.0])
    rot = pdata.get("Rotation", [0.0, 0.0])
    dim = str(pdata.get("Dimension", "minecraft:overworld")).replace("minecraft:", "").title()

    gm = int(pdata.get("playerGameType", 0))
    gm_labels = {0: "Sinh Tồn (Survival)", 1: "Sáng Tạo (Creative)", 2: "Phiêu Lưu (Adventure)", 3: "Khán Giả (Spectator)"}

    return {
        "uuid": matched_uuid,
        "name": player_name,
        "health": round(float(pdata.get("Health", 20.0)), 1),
        "food": int(pdata.get("foodLevel", 20)),
        "level": int(pdata.get("XpLevel", 0)),
        "xp_progress": round(float(pdata.get("XpP", 0.0)) * 100, 1),
        "gamemode": gm,
        "gamemode_label": gm_labels.get(gm, "Sinh Tồn"),
        "dimension": dim,
        "position": {
            "x": round(pos[0], 2) if len(pos) > 0 else 0,
            "y": round(pos[1], 2) if len(pos) > 1 else 0,
            "z": round(pos[2], 2) if len(pos) > 2 else 0,
            "yaw": round(rot[0], 1) if len(rot) > 0 else 0,
            "pitch": round(rot[1], 1) if len(rot) > 1 else 0
        },
        "inventory": {
            "hotbar": hotbar,
            "main": main_inv,
            "armor": armor,
            "offhand": offhand
        },
        "ender_chest": ender_chest,
        "avatar_url": f"https://mc-heads.net/avatar/{matched_uuid}/64",
        "body_url": f"https://mc-heads.net/body/{matched_uuid}/right"
    }

