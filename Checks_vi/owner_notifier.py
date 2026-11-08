"""
🌸 SakuraBot - Live Console & Owner Notifier System
Hệ thống giám sát vận hành trực tiếp, bắt lỗi runtime, chuyển tiếp log console
và gửi thông báo Discord Embed đẹp mắt trực tiếp tới Owner (DM).
"""

import sys
import os
import re
import io
import time
import asyncio
import datetime
import traceback
import platform
from typing import Optional, Dict, Any, Union

import discord
from discord.ext import commands
import psutil

# Cấu hình Owner
try:
    from config import OWNER_ID, PREFIX, WEB_PORT
except Exception:
    OWNER_ID = 1144785664458637394
    PREFIX = "s!"
    WEB_PORT = 10272

# Thời điểm bot bắt đầu chạy để tính Uptime
BOT_BOOT_TIME = time.time()

# Bảng mã màu Embed Sakura
COLOR_SAKURA_PINK = 0xFF79C6
COLOR_ONLINE_GREEN = 0x2ECC71
COLOR_RESTART_ORANGE = 0xF39C12
COLOR_ERROR_RED = 0xED4245
COLOR_INFO_BLUE = 0x3498DB

__all__ = [
    "notify_owner_guild_join",
    "notify_owner_guild_remove",
    "notify_owner_error",
    "notify_owner_boot",
    "notify_owner_restart",
    "notify_owner_command_error",
    "notify_owner_command_used",
    "notify_owner_ready",
    "send_owner_dm",
    "get_owner_user",
    "setup_live_console",
]

# Anti-Spam / Debounce Cache cho lỗi lặp lại
# Key: error_hash -> { "first_seen": float, "last_sent": float, "count": int, "suppressed": int }
_ERROR_DEBOUNCE_CACHE: Dict[str, Dict[str, Any]] = {}
ERROR_COOLDOWN_SECONDS = 45.0  # Chặn spam cùng 1 lỗi trong 45 giây

# Regex loại bỏ mã màu ANSI khỏi log
ANSI_REGEX = re.compile(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])')

def strip_ansi(text: str) -> str:
    """Xóa bỏ các ký tự màu ANSI trong chuỗi."""
    if not text:
        return ""
    return ANSI_REGEX.sub('', text)

def get_vietnam_time_str() -> str:
    """Lấy thời gian định dạng Việt Nam hiện tại."""
    now = datetime.datetime.now()
    return now.strftime("%d/%m/%Y %H:%M:%S")

def format_uptime(seconds: float) -> str:
    """Đổi số giây sang định dạng D ngày H giờ M phút S giây."""
    s = int(seconds)
    days, s = divmod(s, 86400)
    hours, s = divmod(s, 3600)
    minutes, s = divmod(s, 60)
    parts = []
    if days > 0:
        parts.append(f"{days}d")
    if hours > 0:
        parts.append(f"{hours}h")
    if minutes > 0:
        parts.append(f"{minutes}m")
    parts.append(f"{s}s")
    return " ".join(parts) if parts else "0s"

def get_system_metrics() -> Dict[str, str]:
    """Lấy số liệu tài nguyên hệ thống (RAM, CPU)."""
    try:
        proc = psutil.Process()
        mem_mb = proc.memory_info().rss / (1024 * 1024)
        cpu_percent = proc.cpu_percent(interval=None)
        return {
            "ram": f"{mem_mb:.1f} MB",
            "cpu": f"{cpu_percent:.1f}%"
        }
    except Exception:
        return {"ram": "N/A", "cpu": "N/A"}

async def get_owner_user(bot: commands.Bot) -> Optional[discord.User]:
    """Lấy đối tượng User của Owner bot."""
    if not OWNER_ID:
        return None
    user = bot.get_user(OWNER_ID)
    if user is None:
        try:
            user = await bot.fetch_user(OWNER_ID)
        except Exception as e:
            print(f"[OwnerNotifier] Không thể tìm thấy Owner ID {OWNER_ID}: {e}")
            return None
    return user


# ==============================================================================
# 1. LIVE CONSOLE STDOUT / STDERR TEE STREAM
# ==============================================================================
class ConsoleStreamTee:
    """Tee stream: Vừa in ra màn hình terminal thật, vừa chuyển tiếp vào Live Console Web."""
    def __init__(self, original_stream, level: str = "INFO"):
        self.original_stream = original_stream
        self.level = level
        self._buffer = ""

    def write(self, s: str):
        try:
            self.original_stream.write(s)
            self.original_stream.flush()
        except Exception:
            pass

        self._buffer += s
        while "\n" in self._buffer:
            line, self._buffer = self._buffer.split("\n", 1)
            clean_line = strip_ansi(line).strip()
            if clean_line:
                try:
                    from web.server import add_log
                    add_log(self.level, clean_line)
                except Exception:
                    pass

    def flush(self):
        try:
            self.original_stream.flush()
        except Exception:
            pass

    def fileno(self):
        return self.original_stream.fileno()

    def isatty(self):
        return getattr(self.original_stream, 'isatty', lambda: False)()

_is_tee_installed = False

def install_live_console_tee():
    """Gắn Tee Stream cho sys.stdout và sys.stderr để đẩy log vào Live Console Web."""
    global _is_tee_installed
    if _is_tee_installed:
        return
    sys.stdout = ConsoleStreamTee(sys.stdout, level="INFO")
    sys.stderr = ConsoleStreamTee(sys.stderr, level="ERROR")
    _is_tee_installed = True
    print("[LiveConsole] ✅ Đã kích hoạt hệ thống Live Console Stream thời gian thực.")


# ==============================================================================
# 2. GỬI THÔNG BÁO DM ĐẾN OWNER
# ==============================================================================
async def send_owner_dm(bot: commands.Bot, embed: discord.Embed, file: Optional[discord.File] = None):
    """Gửi DM an toàn tới Owner kèm Embed và file đính kèm nếu có."""
    owner = await get_owner_user(bot)
    if not owner:
        return False
    try:
        kwargs = {"embed": embed}
        if file:
            kwargs["file"] = file
        await owner.send(**kwargs)
        return True
    except discord.Forbidden:
        print(f"[OwnerNotifier] ⚠️ Không thể gửi DM cho Owner {OWNER_ID} (Chặn tin nhắn từ người lạ / Direct Messages disabled).")
        return False
    except Exception as e:
        print(f"[OwnerNotifier] ❌ Lỗi khi gửi DM cho Owner: {e}")
        return False


# ------------------------------------------------------------------------------
# A. THÔNG BÁO BOT ONLINE (KHỞI ĐỘNG THÀNH CÔNG)
# ------------------------------------------------------------------------------
async def notify_owner_bot_online(bot: commands.Bot):
    """Gửi thông báo DM tới Owner khi bot đã kết nối và sẵn sàng hoạt động."""
    guilds_count = len(bot.guilds)
    total_users = sum(g.member_count or 0 for g in bot.guilds)
    latency_ms = bot.latency * 1000.0
    metrics = get_system_metrics()
    web_p = getattr(bot, "web_port", WEB_PORT)

    embed = discord.Embed(
        title="🌸 SAKURABOT ĐÃ TRỰC TUYẾN THÀNH CÔNG!",
        description="Bot đã hoàn tất nạp dữ liệu, đồng bộ hóa slash command và sẵn sàng phục vụ.",
        color=COLOR_SAKURA_PINK,
        timestamp=datetime.datetime.now(datetime.timezone.utc)
    )

    if bot.user and bot.user.display_avatar:
        embed.set_thumbnail(url=bot.user.display_avatar.url)

    embed.add_field(
        name="🤖 Thông Tin Bot",
        value=f"• Tên: **{bot.user}**\n• ID: `{bot.user.id if bot.user else 'N/A'}`\n• Prefix: `{PREFIX}`",
        inline=True
    )
    embed.add_field(
        name="⚡ Kết Nối & Quy Mô",
        value=f"• Độ trễ: `{latency_ms:.1f} ms`\n• Máy chủ: **{guilds_count:,}**\n• Thành viên: **{total_users:,}**",
        inline=True
    )
    embed.add_field(
        name="💻 Môi Trường Vận Hành",
        value=f"• Python: `{platform.python_version()}`\n• Discord.py: `{discord.__version__}`\n• HĐH: `{platform.system()} {platform.release()}`",
        inline=False
    )
    embed.add_field(
        name="📊 Tài Nguyên & Bảng Điều Khiển",
        value=f"• RAM: `{metrics['ram']}` | CPU: `{metrics['cpu']}`\n• Web Panel: [http://localhost:{web_p}](http://localhost:{web_p})\n• Khởi động lúc: `{get_vietnam_time_str()}`",
        inline=False
    )

    embed.set_footer(
        text="🌸 SakuraBot Live Console • Hệ thống giám sát vận hành tự động",
        icon_url=bot.user.display_avatar.url if bot.user else None
    )

    sent = await send_owner_dm(bot, embed)
    if sent:
        print("[OwnerNotifier] 📨 Đã gửi thông báo Bot Online đến DM của Owner thành công.")


# ------------------------------------------------------------------------------
# B. THÔNG BÁO BOT RESTART / SHUTDOWN
# ------------------------------------------------------------------------------
async def notify_owner_bot_lifecycle(bot: commands.Bot, action: str = "restart", source: str = "Lệnh Owner"):
    """Gửi thông báo DM tới Owner khi có tín hiệu Restart hoặc Shutdown."""
    uptime_str = format_uptime(time.time() - BOT_BOOT_TIME)
    is_restart = (action == "restart")

    color = COLOR_RESTART_ORANGE if is_restart else COLOR_ERROR_RED
    icon = "🔄" if is_restart else "🔴"
    action_text = "Khởi Động Lại (Restart)" if is_restart else "Tắt Hệ Thống (Shutdown)"

    embed = discord.Embed(
        title=f"{icon} SAKURABOT: TÍN HIỆU {action_text.upper()}",
        description=f"Hệ thống bot nhận được lệnh thực hiện **{action_text}**.",
        color=color,
        timestamp=datetime.datetime.now(datetime.timezone.utc)
    )

    if bot.user and bot.user.display_avatar:
        embed.set_thumbnail(url=bot.user.display_avatar.url)

    embed.add_field(name="👤 Nguồn Yêu Cầu", value=f"`{source}`", inline=True)
    embed.add_field(name="⏱️ Thời Gian Hoạt Động (Uptime)", value=f"`{uptime_str}`", inline=True)
    embed.add_field(name="🕒 Thời Điểm Kích Hoạt", value=f"`{get_vietnam_time_str()}`", inline=False)

    if is_restart:
        embed.add_field(
            name="💡 Ghi Chú",
            value="Bot sẽ tự khởi chạy lại tiến trình ngay lập tức. Sau khi online bot sẽ tự động gửi lại thông báo.",
            inline=False
        )

    embed.set_footer(text="🌸 SakuraBot Live Notifier • Bảo vệ tiến trình")

    await send_owner_dm(bot, embed)
    # Nghỉ 0.5s để đảm bảo request gửi đi thành công trước khi process bị tắt/restart
    await asyncio.sleep(0.5)


# ------------------------------------------------------------------------------
# C. THÔNG BÁO RUNTIME ERROR / EXCEPTION (CÓ EMBED ĐẸP & CHỐNG SPAM)
# ------------------------------------------------------------------------------
async def notify_owner_bot_error(
    bot: commands.Bot,
    error: BaseException,
    source: str = "Hệ thống",
    ctx: Optional[commands.Context] = None,
    interaction: Optional[discord.Interaction] = None,
    extra_info: Optional[str] = None
):
    """
    Gửi thông báo DM chi tiết cho Owner khi phát sinh Exception hoặc Lỗi vận hành.
    Tích hợp cơ chế Debounce / Anti-spam tránh bị Discord rate-limit nếu có lỗi lặp lại.
    """
    now = time.time()
    err_type = type(error).__name__
    err_msg = str(error) or "Không có thông báo lỗi cụ thể."

    # Lấy traceback hoàn chỉnh
    if hasattr(error, '__traceback__') and error.__traceback__:
        tb_lines = traceback.format_exception(type(error), error, error.__traceback__)
        full_tb = "".join(tb_lines)
    else:
        full_tb = traceback.format_exc()
        if not full_tb or "NoneType: None" in full_tb:
            full_tb = f"{err_type}: {err_msg}"

    # Tạo signature băm lỗi để chống spam lặp
    error_signature = f"{source}:{err_type}:{err_msg[:80]}"
    cached = _ERROR_DEBOUNCE_CACHE.get(error_signature)

    if cached:
        elapsed = now - cached["last_sent"]
        cached["count"] += 1
        if elapsed < ERROR_COOLDOWN_SECONDS:
            cached["suppressed"] += 1
            # Bỏ qua gửi DM trùng lặp để không làm phiền Owner liên tục
            return False
        else:
            # Hết cooldown, ghi nhận gửi lần tiếp
            suppressed_count = cached["suppressed"]
            cached["last_sent"] = now
            cached["suppressed"] = 0
    else:
        _ERROR_DEBOUNCE_CACHE[error_signature] = {
            "first_seen": now,
            "last_sent": now,
            "count": 1,
            "suppressed": 0
        }
        suppressed_count = 0

    # Xác định người gọi và vị trí lỗi
    invoker_text = "Hệ Thống Tự Động / Task"
    location_text = "Hậu Đài (Background Task / Console)"

    if ctx:
        invoker_text = f"**{ctx.author}** (`{ctx.author.id}`)"
        if ctx.guild:
            location_text = f"**{ctx.guild.name}** (`{ctx.guild.id}`) • Kênh: `#{getattr(ctx.channel, 'name', 'Direct')}`"
        else:
            location_text = "Tin nhắn riêng (Direct Message)"
        if ctx.command:
            source = f"Lệnh Prefix: `{ctx.prefix}{ctx.command.qualified_name}`"

    elif interaction:
        invoker_text = f"**{interaction.user}** (`{interaction.user.id}`)"
        if interaction.guild:
            location_text = f"**{interaction.guild.name}** (`{interaction.guild.id}`) • Kênh: `#{getattr(interaction.channel, 'name', 'Direct')}`"
        else:
            location_text = "Tương tác DM (Direct Interaction)"
        if interaction.command:
            source = f"Slash Command: `/{interaction.command.name}`"

    embed = discord.Embed(
        title="🚨 SAKURABOT: PHÁT HIỆN LỖI VẬN HÀNH (ERROR ALERT)",
        description=f"Đã xảy ra ngoại lệ không được xử lý trong quá trình chạy bot tại **{source}**.",
        color=COLOR_ERROR_RED,
        timestamp=datetime.datetime.now(datetime.timezone.utc)
    )

    if bot.user and bot.user.display_avatar:
        embed.set_thumbnail(url=bot.user.display_avatar.url)

    embed.add_field(name="📍 Nguồn Phát Sinh", value=f"`{source}`", inline=True)
    embed.add_field(name="⚠️ Phân Loại Lỗi", value=f"`{err_type}`", inline=True)
    embed.add_field(name="👤 Người Thực Hiện", value=invoker_text, inline=True)
    embed.add_field(name="🌐 Vị Trí Xảy Ra", value=location_text, inline=False)
    embed.add_field(name="💬 Nội Dung Lỗi", value=f"```{err_msg[:500]}```", inline=False)

    # Hiển thị Traceback (tối đa 900 ký tự để không vượt quá giới hạn 1024 của field Embed)
    tb_file = None
    if len(full_tb) > 900:
        tb_snippet = full_tb[-900:]
        embed.add_field(
            name="📋 Traceback (Đoạn Cuối)",
            value=f"```py\n... [Đã rút gọn - Xem file đính kèm]\n{tb_snippet}\n```",
            inline=False
        )
        # Tạo file đính kèm traceback đầy đủ
        tb_bytes = io.BytesIO(full_tb.encode("utf-8"))
        tb_file = discord.File(tb_bytes, filename=f"traceback_{int(now)}.txt")
    else:
        embed.add_field(
            name="📋 Traceback Chi Tiết",
            value=f"```py\n{full_tb}\n```",
            inline=False
        )

    if suppressed_count > 0:
        embed.add_field(
            name="🛡️ Chống Spam",
            value=f"⚠️ Lỗi này đã lặp lại **{suppressed_count} lần** trong vòng {int(ERROR_COOLDOWN_SECONDS)} giây qua.",
            inline=False
        )

    if extra_info:
        embed.add_field(name="ℹ️ Thông Tin Bổ Sung", value=f"`{extra_info}`", inline=False)

    embed.set_footer(
        text=f"Thời gian: {get_vietnam_time_str()} • SakuraBot Error Sentinel",
        icon_url=bot.user.display_avatar.url if bot.user else None
    )

    await send_owner_dm(bot, embed, file=tb_file)
    return True


# ------------------------------------------------------------------------------
# D. THÔNG BÁO BOT THAM GIA MÁY CHỦ MỚI (GUILD JOIN)
# ------------------------------------------------------------------------------
async def notify_owner_guild_join(bot: commands.Bot, guild: discord.Guild) -> bool:
    """
    Gửi thông báo DM chi tiết cho Bot Owner khi SakuraBot được mời/thêm vào một server mới.
    Bao gồm thông tin server, chủ server (Owner), người mời bot (Inviter) và quy mô mạng lưới.
    """
    now = datetime.datetime.now(datetime.timezone.utc)
    guilds_count = len(bot.guilds)
    total_users = sum(g.member_count or 0 for g in bot.guilds)

    # 1. Tìm thông tin Chủ sở hữu máy chủ (Server Owner)
    owner_str = "Không rõ"
    owner_mention = f"<@{guild.owner_id}>" if guild.owner_id else "N/A"
    owner_obj = guild.owner
    if not owner_obj and guild.owner_id:
        try:
            owner_obj = bot.get_user(guild.owner_id) or await bot.fetch_user(guild.owner_id)
        except Exception:
            owner_obj = None

    if owner_obj:
        owner_str = f"**{owner_obj}** (`{owner_obj.id}`)\n• Tag: {owner_mention}"
    elif guild.owner_id:
        owner_str = f"ID: `{guild.owner_id}` ({owner_mention})"

    # 2. Tìm người đã mời bot vào server (qua Audit Log nếu có quyền)
    inviter_str = "Không rõ (Thiếu quyền Audit Log hoặc cache Discord)"
    try:
        if guild.me and guild.me.guild_permissions.view_audit_log:
            async for entry in guild.audit_logs(action=discord.AuditLogAction.bot_add, limit=5):
                if entry.target and bot.user and entry.target.id == bot.user.id:
                    inviter_str = f"**{entry.user}** (`{entry.user.id}`)\n• Tag: <@{entry.user.id}>"
                    break
    except Exception:
        pass

    # 3. Ngày tạo máy chủ
    created_ts = int(guild.created_at.timestamp()) if guild.created_at else 0
    created_str = f"<t:{created_ts}:F> (<t:{created_ts}:R>)" if created_ts else "N/A"

    embed = discord.Embed(
        title="📥 SAKURABOT: THAM GIA MÁY CHỦ MỚI!",
        description=f"Bot vừa được thêm vào một máy chủ mới: **{guild.name}**",
        color=COLOR_ONLINE_GREEN,
        timestamp=now
    )

    if guild.icon:
        embed.set_thumbnail(url=guild.icon.url)
    elif bot.user and bot.user.display_avatar:
        embed.set_thumbnail(url=bot.user.display_avatar.url)

    embed.add_field(
        name="🏠 Thông Tin Máy Chủ",
        value=(
            f"• Tên: **{guild.name}**\n"
            f"• ID: `{guild.id}`\n"
            f"• Ngày tạo: {created_str}"
        ),
        inline=False
    )

    embed.add_field(
        name="👑 Chủ Sở Hữu (Server Owner)",
        value=owner_str,
        inline=True
    )

    embed.add_field(
        name="👤 Người Thêm Bot (Inviter)",
        value=inviter_str,
        inline=True
    )

    # 4. Chi tiết quy mô máy chủ
    members_count = guild.member_count or len(guild.members)
    text_count = len(guild.text_channels)
    voice_count = len(guild.voice_channels)
    roles_count = len(guild.roles)

    embed.add_field(
        name="👥 Quy Mô Máy Chủ",
        value=(
            f"• Tổng thành viên: **{members_count:,}**\n"
            f"• Kênh văn bản: `{text_count}` | Kênh thoại: `{voice_count}`\n"
            f"• Vai trò (Roles): `{roles_count}`"
        ),
        inline=False
    )

    embed.add_field(
        name="📊 Mạng Lưới Sau Khi Thêm",
        value=f"• Đang phục vụ: **{guilds_count:,}** máy chủ\n• Tiếp cận: **{total_users:,}** người dùng",
        inline=False
    )

    embed.set_footer(
        text=f"🌸 SakuraBot Guild Sentinel • {get_vietnam_time_str()}",
        icon_url=bot.user.display_avatar.url if bot.user else None
    )

    sent = await send_owner_dm(bot, embed)
    if sent:
        print(f"[OwnerNotifier] 📨 Đã gửi DM thông báo Bot tham gia server '{guild.name}' tới Owner.")
    return sent


# ------------------------------------------------------------------------------
# E. THÔNG BÁO BOT RỜI KHỎI MÁY CHỦ (GUILD REMOVE / KICK)
# ------------------------------------------------------------------------------
async def notify_owner_guild_remove(bot: commands.Bot, guild: discord.Guild) -> bool:
    """
    Gửi thông báo DM chi tiết cho Bot Owner khi SakuraBot bị kick hoặc rời khỏi một server.
    Bao gồm tên server, ID, chủ sở hữu và số lượng máy chủ còn lại.
    """
    now = datetime.datetime.now(datetime.timezone.utc)
    guilds_count = len(bot.guilds)
    total_users = sum(g.member_count or 0 for g in bot.guilds)

    owner_str = f"ID: `{guild.owner_id}` (<@{guild.owner_id}>)" if guild.owner_id else "N/A"
    owner_obj = guild.owner
    if not owner_obj and guild.owner_id:
        try:
            owner_obj = bot.get_user(guild.owner_id)
        except Exception:
            owner_obj = None

    if owner_obj:
        owner_str = f"**{owner_obj}** (`{owner_obj.id}`)\n• Tag: <@{owner_obj.id}>"

    created_ts = int(guild.created_at.timestamp()) if guild.created_at else 0
    created_str = f"<t:{created_ts}:F>" if created_ts else "N/A"

    embed = discord.Embed(
        title="📤 SAKURABOT: RỜI KHỎI MÁY CHỦ!",
        description=f"Bot đã rời khỏi hoặc bị kick khỏi máy chủ: **{guild.name}**",
        color=COLOR_ERROR_RED,
        timestamp=now
    )

    if guild.icon:
        embed.set_thumbnail(url=guild.icon.url)
    elif bot.user and bot.user.display_avatar:
        embed.set_thumbnail(url=bot.user.display_avatar.url)

    embed.add_field(
        name="🏠 Thông Tin Máy Chủ",
        value=(
            f"• Tên: **{guild.name}**\n"
            f"• ID: `{guild.id}`\n"
            f"• Ngày tạo: {created_str}"
        ),
        inline=False
    )

    embed.add_field(
        name="👑 Chủ Sở Hữu (Server Owner)",
        value=owner_str,
        inline=True
    )

    members_str = f"**{guild.member_count:,}**" if guild.member_count else "Không xác định"
    embed.add_field(
        name="👥 Thành Viên Khi Rời",
        value=members_str,
        inline=True
    )

    embed.add_field(
        name="📊 Mạng Lưới Sau Khi Rời",
        value=f"• Còn phục vụ: **{guilds_count:,}** máy chủ\n• Tiếp cận: **{total_users:,}** người dùng",
        inline=False
    )

    embed.set_footer(
        text=f"🌸 SakuraBot Guild Sentinel • {get_vietnam_time_str()}",
        icon_url=bot.user.display_avatar.url if bot.user else None
    )

    sent = await send_owner_dm(bot, embed)
    if sent:
        print(f"[OwnerNotifier] 📨 Đã gửi DM thông báo Bot rời khỏi server '{guild.name}' tới Owner.")
    return sent


# ==============================================================================
# 3. TRÌNH XỬ LÝ LỆNH LIVE CONSOLE TỪ WEB DASHBOARD
# ==============================================================================
async def process_live_console_command(cmd_text: str, bot: Optional[commands.Bot]) -> str:
    """Xử lý các câu lệnh tương tác gõ từ giao diện Live Console trên Web."""
    cmd_text = cmd_text.strip()
    if not cmd_text:
        return "Vui lòng nhập lệnh hợp lệ."

    parts = cmd_text.split()
    cmd = parts[0].lower()
    args = parts[1:]

    from web.server import add_log

    if cmd in ("help", "?"):
        help_msg = (
            "📌 CÁC LỆNH LIVE CONSOLE HỖ TRỢ:\n"
            "• status / info     : Xem tài nguyên bot (RAM, CPU, Ping, Uptime, Servers)\n"
            "• testdm            : Gửi thử nghiệm 1 Embed DM tới Owner\n"
            "• dm <tin_nhắn>     : Gửi trực tiếp 1 tin nhắn DM tới Owner\n"
            "• say <kênh_id> <nd>: Gửi tin nhắn bot đến 1 kênh Discord bất kỳ\n"
            "• reload [ext]      : Tải lại toàn bộ hoặc 1 extension cụ thể\n"
            "• rates             : Xem trạng thái thao túng tỉ lệ game hiện tại\n"
            "• eval <code_py>    : Thực thi mã Python trực tiếp trên bot\n"
            "• cls / clear       : Xóa màn hình console web\n"
            "• restart           : Gửi cảnh báo DM và khởi động lại bot an toàn"
        )
        add_log("INFO", help_msg)
        return help_msg

    elif cmd in ("status", "info"):
        if not bot:
            res = "Bot chưa khởi tạo hoặc đang ngoại tuyến."
        else:
            uptime_str = format_uptime(time.time() - BOT_BOOT_TIME)
            metrics = get_system_metrics()
            latency = bot.latency * 1000.0
            res = (
                f"🌸 TRẠNG THÁI SAKURABOT:\n"
                f"• Bot: {bot.user} (ID: {bot.user.id if bot.user else 'N/A'})\n"
                f"• Độ trễ (Ping): {latency:.1f}ms\n"
                f"• Uptime: {uptime_str}\n"
                f"• Máy chủ: {len(bot.guilds):,} guilds | Người dùng: {sum(g.member_count or 0 for g in bot.guilds):,} users\n"
                f"• RAM: {metrics['ram']} | CPU: {metrics['cpu']}"
            )
        add_log("SUCCESS", res)
        return res

    elif cmd == "testdm":
        if not bot:
            return "Bot chưa sẵn sàng."
        add_log("INFO", "Đang gửi Embed DM thử nghiệm tới Owner...")
        embed = discord.Embed(
            title="🌸 SAKURABOT: THỬ NGHIỆM THỐNG KÊ LIVE CONSOLE",
            description="Tin nhắn thử nghiệm liên kết Live Console đến DM Owner thành công!",
            color=COLOR_SAKURA_PINK,
            timestamp=datetime.datetime.now(datetime.timezone.utc)
        )
        embed.add_field(name="🕒 Thời Gian", value=f"`{get_vietnam_time_str()}`", inline=True)
        embed.add_field(name="💻 Nguồn", value="`Web Live Console (testdm)`", inline=True)
        embed.set_footer(text="SakuraBot Live Console • Kiểm tra kết nối")
        ok = await send_owner_dm(bot, embed)
        res = "✅ Đã gửi DM thử nghiệm tới Owner thành công!" if ok else "❌ Gửi DM thất bại. Vui lòng kiểm tra cài đặt DM của Owner."
        add_log("SUCCESS" if ok else "WARN", res)
        return res

    elif cmd in ("testguild", "testjoin"):
        if not bot or not bot.guilds:
            return "Bot chưa kết nối máy chủ nào."
        g = bot.guilds[0]
        add_log("INFO", f"Đang gửi thử nghiệm DM tham gia server ({g.name}) tới Owner...")
        ok = await notify_owner_guild_join(bot, g)
        res = f"✅ Đã gửi DM thử nghiệm tham gia server '{g.name}' tới Owner!" if ok else "❌ Gửi DM thất bại."
        add_log("SUCCESS" if ok else "WARN", res)
        return res

    elif cmd == "dm":
        if not bot or not args:
            return "Cách dùng: dm <nội dung tin nhắn>"
        text = " ".join(args)
        owner = await get_owner_user(bot)
        if not owner:
            return "Không tìm thấy Owner."
        try:
            await owner.send(f"📬 **[Live Console]** {text}")
            res = f"✅ Đã gửi tin nhắn đến Owner: {text}"
            add_log("SUCCESS", res)
            return res
        except Exception as e:
            res = f"❌ Gửi thất bại: {e}"
            add_log("ERROR", res)
            return res

    elif cmd == "say":
        if not bot or len(args) < 2:
            return "Cách dùng: say <channel_id> <nội dung>"
        channel_id = args[0]
        text = " ".join(args[1:])
        try:
            channel = bot.get_channel(int(channel_id))
            if not channel:
                channel = await bot.fetch_channel(int(channel_id))
            if channel and hasattr(channel, "send"):
                await channel.send(text)
                res = f"✅ Đã gửi tin nhắn vào #{channel.name}: {text}"
                add_log("SUCCESS", res)
                return res
            return "❌ Kênh không hợp lệ hoặc không có quyền gửi."
        except Exception as e:
            res = f"❌ Lỗi gửi tin nhắn: {e}"
            add_log("ERROR", res)
            return res

    elif cmd == "rates":
        try:
            from data.game_rates import get_game_rates
            r = get_game_rates()
            res = (
                f"🎛️ CẤU HÌNH TỈ LỆ GAME HIỆN TẠI:\n"
                f"• Cường hóa (+150): {r.get('refine_multiplier', 1.0)}x | God Mode: {'BẬT' if r.get('refine_always_success') else 'TẮT'}\n"
                f"• Tiến cấp sao: {r.get('star_multiplier', 1.0)}x | God Mode: {'BẬT' if r.get('star_always_success') else 'TẮT'}\n"
                f"• Câu cá: May mắn {r.get('fishing_luck_mult')}x | Đột biến {r.get('fishing_mutation_mult')}x | Rương {r.get('fishing_chest_mult')}x\n"
                f"• Đào mỏ: May mắn {r.get('mining_luck_mult')}x | Quặng hiếm {r.get('mining_rare_mult')}x | Đột biến {r.get('mining_mutation_mult')}x"
            )
            add_log("INFO", res)
            return res
        except Exception as e:
            return f"Lỗi đọc tỉ lệ: {e}"

    elif cmd == "eval":
        if not bot or not args:
            return "Cách dùng: eval <code python>"
        code_str = " ".join(args)
        add_log("INFO", f"Đang thực thi: {code_str}")
        try:
            import inspect
            eval_globals = {"bot": bot, "discord": discord, "commands": commands, "asyncio": asyncio, "sys": sys, "os": os}
            result = eval(code_str, eval_globals)
            if inspect.isawaitable(result):
                result = await result
            res = f"📤 Kết quả: {result}"
            add_log("SUCCESS", res)
            return res
        except Exception as e:
            res = f"❌ Lỗi thực thi eval: {e}"
            add_log("ERROR", res)
            return res

    elif cmd == "restart":
        if not bot:
            return "Bot chưa sẵn sàng."
        add_log("WARN", "⚠️ Đang gửi cảnh báo và tiến hành Restart Bot từ Live Console...")
        await notify_owner_bot_lifecycle(bot, action="restart", source="Live Console Web")
        os.execv(sys.executable, [sys.executable] + sys.argv)
        return "Đang khởi động lại..."

    else:
        res = f"Lệnh không xác định: '{cmd}'. Gõ 'help' để xem danh sách lệnh."
        add_log("WARN", res)
        return res

