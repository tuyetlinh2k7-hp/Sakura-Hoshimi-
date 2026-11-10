import os
import re
import json
import time
import asyncio
import logging
from pathlib import Path
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List, Union

import discord
from discord.ext import commands, tasks
from discord import app_commands

from config import OWNER_ID
from Check.mod import has_admin_role, _check_is_admin, admin_roles
from Check.i18n import t, is_vietnamese, get_guild_language
from Check.data import LOG_CHANNEL_ID, save_data
from Command.command_manager import send_mod_log, notify_target_dm, parse_duration_to_seconds

logger = logging.getLogger("SakuraBot.Jail")

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
JAIL_CONFIG_FILE = DATA_DIR / "jail_config.json"
JAIL_RECORDS_FILE = DATA_DIR / "jail_records.json"

# In-memory caches
jail_config: Dict[str, Dict[str, Any]] = {}
jail_records: Dict[str, Dict[str, Dict[str, Any]]] = {}

_jail_lock = asyncio.Lock()

# Multi-language dictionary for localized role names and default texts
JAIL_ROLE_NAMES = {
    "vi": "Tù Nhân",
    "en": "Prisoner",
    "ja": "囚人",
    "cn": "囚犯"
}

JAIL_CHANNEL_NAMES = {
    "vi": "phòng-giam",
    "en": "jail-cell",
    "ja": "監房",
    "cn": "牢房"
}

MESSAGES = {
    "vi": {
        "ROLE_NAME": "Tù Nhân",
        "CHANNEL_NAME": "phòng-giam",
        "CHANNEL_TOPIC": "🔒 Phòng giam SakuraBot - Kênh dành riêng cho tù nhân thụ án.",
        "JAIL_TITLE": "🚨 Quyết Định Tống Giam",
        "UNJAIL_TITLE": "🔓 Quyết Định Phóng Thích (Ân Xá)",
        "AUTO_UNJAIL_TITLE": "🔓 Tự Động Phóng Thích (Hết Hạn Án Phạt)",
        "FIELD_TARGET": "👤 Tù Nhân",
        "FIELD_MOD": "🔨 Người Thực Hiện",
        "FIELD_REASON": "📝 Lý Do",
        "FIELD_DURATION": "⏱️ Thời Hạn",
        "FIELD_CELL": "🔒 Phòng Giam",
        "FIELD_RESTORED_ROLES": "🔄 Vai Trò Khôi Phục",
        "PERMANENT": "Vĩnh viễn (Cho đến khi có lệnh ân xá)",
        "NO_INMATES": "🕊️ Hiện tại không có tù nhân nào đang bị giam giữ trong máy chủ.",
        "ERR_NO_PERM": "❌ Bạn không có quyền quản lý nhà tù!",
        "ERR_HIERARCHY_USER": "❌ Bạn không thể tống giam người có vai trò cao hơn hoặc bằng bạn!",
        "ERR_HIERARCHY_BOT": "❌ Bot không thể tống giam người này vì vai trò của họ cao hơn hoặc bằng Bot!",
        "ERR_CANNOT_JAIL_OWNER": "❌ Không thể tống giam Chủ sở hữu máy chủ (Server Owner)!",
        "ERR_CANNOT_JAIL_SELF": "❌ Bạn không thể tự tống giam chính mình!",
        "ERR_CANNOT_JAIL_BOT": "❌ Không thể tống giam Bot!",
        "ERR_ALREADY_JAILED": "⚠️ Thành viên này hiện đã đang ở trong tù! (Thời gian còn lại: {remaining})",
        "ERR_NOT_JAILED": "⚠️ Thành viên này hiện không bị tống giam!",
        "JAIL_SUCCESS": "✅ Đã tống giam {target} thành công!",
        "UNJAIL_SUCCESS": "✅ Đã phóng thích {target} thành công! Đã khôi phục {count} vai trò.",
        "SETUP_SUCCESS": "✅ Thiết lập hệ thống nhà tù thành công!\n- **Vai trò tù nhân**: {role}\n- **Kênh phòng giam**: {channel}\n- **Số kênh/danh mục đã cách ly**: {isolated_count}",
        "ISOLATE_SUCCESS": "✅ Đã quét và cập nhật quyền cách ly cho **{count}** kênh/danh mục.",
        "CONFIG_TITLE": "⚙️ Cấu Hình Hệ Thống Nhà Tù",
        "INMATES_TITLE": "📋 Danh Sách Tù Nhân Đang Thụ Án ({count})",
        "INMATE_PROFILE_TITLE": "📋 Hồ Sơ Phạm Nhân: {name}",
        "CELL_WELCOME": "🚨 {mention} Bạn đã bị tống giam vào phòng giam!\nTrong thời gian thụ án, toàn bộ các kênh khác đã bị ẩn. Vui lòng chấp hành nội quy và chờ hết hạn hoặc quản trị viên xử lý."
    },
    "en": {
        "ROLE_NAME": "Prisoner",
        "CHANNEL_NAME": "jail-cell",
        "CHANNEL_TOPIC": "🔒 SakuraBot Jail Cell - Dedicated channel for inmates serving sentence.",
        "JAIL_TITLE": "🚨 Incarceration Notice",
        "UNJAIL_TITLE": "🔓 Release / Pardon Notice",
        "AUTO_UNJAIL_TITLE": "🔓 Automatic Release (Sentence Expired)",
        "FIELD_TARGET": "👤 Inmate",
        "FIELD_MOD": "🔨 Moderator",
        "FIELD_REASON": "📝 Reason",
        "FIELD_DURATION": "⏱️ Duration",
        "FIELD_CELL": "🔒 Jail Cell",
        "FIELD_RESTORED_ROLES": "🔄 Restored Roles",
        "PERMANENT": "Permanent (Until pardoned)",
        "NO_INMATES": "🕊️ There are currently no prisoners in jail.",
        "ERR_NO_PERM": "❌ You do not have permission to manage the jail!",
        "ERR_HIERARCHY_USER": "❌ You cannot jail a member with a role equal to or higher than yours!",
        "ERR_HIERARCHY_BOT": "❌ The bot cannot jail this member because their role is equal to or higher than the bot's!",
        "ERR_CANNOT_JAIL_OWNER": "❌ Cannot jail the Server Owner!",
        "ERR_CANNOT_JAIL_SELF": "❌ You cannot jail yourself!",
        "ERR_CANNOT_JAIL_BOT": "❌ Cannot jail the bot!",
        "ERR_ALREADY_JAILED": "⚠️ This member is already in jail! (Remaining: {remaining})",
        "ERR_NOT_JAILED": "⚠️ This member is not currently jailed!",
        "JAIL_SUCCESS": "✅ Successfully jailed {target}!",
        "UNJAIL_SUCCESS": "✅ Successfully released {target}! Restored {count} roles.",
        "SETUP_SUCCESS": "✅ Jail system set up successfully!\n- **Prisoner Role**: {role}\n- **Jail Cell**: {channel}\n- **Isolated channels/categories**: {isolated_count}",
        "ISOLATE_SUCCESS": "✅ Scanned and isolated **{count}** channels/categories.",
        "CONFIG_TITLE": "⚙️ Jail System Configuration",
        "INMATES_TITLE": "📋 Current Inmates Roster ({count})",
        "INMATE_PROFILE_TITLE": "📋 Inmate File: {name}",
        "CELL_WELCOME": "🚨 {mention} You have been incarcerated in the jail cell!\nDuring your sentence, all other channels are hidden. Please comply with server rules and wait for sentence completion or moderator review."
    }
}


def get_msg(guild: Optional[discord.Guild], key: str, **kwargs) -> str:
    lang = "vi"
    if guild:
        gl = get_guild_language(guild.id)
        if gl in ("en", "ja", "cn"):
            lang = "en"
    text = MESSAGES.get(lang, MESSAGES["vi"]).get(key, MESSAGES["vi"].get(key, key))
    if kwargs:
        try:
            return text.format(**kwargs)
        except Exception:
            return text
    return text


def load_jail_data():
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    if JAIL_CONFIG_FILE.exists():
        try:
            with open(JAIL_CONFIG_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                if isinstance(data, dict):
                    jail_config.clear()
                    jail_config.update(data)
        except Exception as e:
            logger.error(f"Error loading jail_config.json: {e}")

    if JAIL_RECORDS_FILE.exists():
        try:
            with open(JAIL_RECORDS_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                if isinstance(data, dict):
                    jail_records.clear()
                    jail_records.update(data)
        except Exception as e:
            logger.error(f"Error loading jail_records.json: {e}")


def save_jail_config():
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    try:
        with open(JAIL_CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump(jail_config, f, indent=4, ensure_ascii=False)
    except Exception as e:
        logger.error(f"Error saving jail_config.json: {e}")


def save_jail_records():
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    try:
        with open(JAIL_RECORDS_FILE, "w", encoding="utf-8") as f:
            json.dump(jail_records, f, indent=4, ensure_ascii=False)
    except Exception as e:
        logger.error(f"Error saving jail_records.json: {e}")


# Tải dữ liệu khi import module
load_jail_data()


def get_guild_jail_config(guild_id: int) -> Dict[str, Any]:
    g_key = str(guild_id)
    if g_key not in jail_config:
        jail_config[g_key] = {"role_id": None, "channel_id": None}
    return jail_config[g_key]


def get_guild_jail_records(guild_id: int) -> Dict[str, Dict[str, Any]]:
    g_key = str(guild_id)
    if g_key not in jail_records:
        jail_records[g_key] = {}
    return jail_records[g_key]


async def configure_jail_cell(guild: discord.Guild, jail_role: discord.Role, jail_channel: discord.TextChannel):
    """Cấu hình quyền cho Kênh Phòng Giam (chỉ tù nhân, bot và admin thấy/chat)."""
    everyone_overwrite = discord.PermissionOverwrite(
        view_channel=False,
        send_messages=False
    )
    prisoner_overwrite = discord.PermissionOverwrite(
        view_channel=True,
        send_messages=True,
        read_message_history=True,
        attach_files=False,
        embed_links=False,
        add_reactions=False,
        use_external_emojis=False,
        create_public_threads=False,
        create_private_threads=False,
        send_messages_in_threads=False
    )
    bot_overwrite = discord.PermissionOverwrite(
        view_channel=True,
        send_messages=True,
        read_message_history=True,
        manage_channels=True,
        manage_messages=True,
        embed_links=True,
        attach_files=True
    )

    try:
        await jail_channel.set_permissions(guild.default_role, overwrite=everyone_overwrite, reason="Jail Cell: Ẩn với @everyone")
        await jail_channel.set_permissions(jail_role, overwrite=prisoner_overwrite, reason="Jail Cell: Quyền cho Tù Nhân")
        if guild.me:
            await jail_channel.set_permissions(guild.me, overwrite=bot_overwrite, reason="Jail Cell: Quyền cho Bot")

        guild_admin_roles = admin_roles.get(str(guild.id), [])
        admin_overwrite = discord.PermissionOverwrite(view_channel=True, send_messages=True, read_message_history=True)
        for r_id in guild_admin_roles:
            role = guild.get_role(int(r_id))
            if role:
                await jail_channel.set_permissions(role, overwrite=admin_overwrite, reason="Jail Cell: Quyền cho Admin")
    except (discord.Forbidden, discord.HTTPException) as e:
        logger.warning(f"Error configuring jail cell permissions in {guild.name}: {e}")


async def isolate_guild_channels(
    guild: discord.Guild,
    jail_role: discord.Role,
    jail_channel: Optional[discord.TextChannel] = None
) -> int:
    """
    Quét và đặt overwrite view_channel=False, send_messages=False, connect=False
    trên tất cả Categories và Channels (ngoại trừ Kênh Phòng Giam).
    Tối ưu hóa: ưu tiên xử lý Category trước để con thừa hưởng, tránh spam Discord API rate limits.
    """
    if not guild.me.guild_permissions.manage_roles or not guild.me.guild_permissions.manage_channels:
        return 0

    isolated_count = 0
    jail_channel_id = jail_channel.id if jail_channel else None

    deny_overwrite = discord.PermissionOverwrite(
        view_channel=False,
        send_messages=False,
        connect=False,
        speak=False
    )

    # 1. Cập nhật Category trước
    for category in guild.categories:
        try:
            current = category.overwrites.get(jail_role)
            if current is None or current.view_channel is not False or current.connect is not False:
                await category.set_permissions(jail_role, overwrite=deny_overwrite, reason="SakuraBot: Cách ly Category với Tù Nhân")
                isolated_count += 1
                await asyncio.sleep(0.15)
        except (discord.Forbidden, discord.HTTPException):
            continue

    # 2. Cập nhật Channels không đồng bộ hoặc không thuộc Category nào
    for ch in guild.channels:
        if ch.id == jail_channel_id:
            continue
        if isinstance(ch, discord.CategoryChannel):
            continue
        # Nếu channel đã thừa hưởng từ Category đã deny view_channel thì bỏ qua
        if ch.category and ch.permissions_synced:
            cat_ov = ch.category.overwrites.get(jail_role)
            if cat_ov and cat_ov.view_channel is False and cat_ov.connect is False:
                continue

        try:
            current = ch.overwrites.get(jail_role)
            if current is None or current.view_channel is not False or current.connect is not False:
                await ch.set_permissions(jail_role, overwrite=deny_overwrite, reason="SakuraBot: Cách ly Kênh với Tù Nhân")
                isolated_count += 1
                await asyncio.sleep(0.15)
        except (discord.Forbidden, discord.HTTPException):
            continue

    return isolated_count


async def ensure_jail_setup(guild: discord.Guild) -> tuple[Optional[discord.Role], Optional[discord.TextChannel], int]:
    """Tự động đảm bảo Role Tù Nhân và Kênh Phòng Giam đã tồn tại và được cấu hình chuẩn."""
    cfg = get_guild_jail_config(guild.id)
    role_id = cfg.get("role_id")
    channel_id = cfg.get("channel_id")

    jail_role = guild.get_role(int(role_id)) if role_id else None
    jail_channel = guild.get_channel(int(channel_id)) if channel_id else None

    lang = get_guild_language(guild.id)
    default_role_name = JAIL_ROLE_NAMES.get(lang, "Tù Nhân")
    default_channel_name = JAIL_CHANNEL_NAMES.get(lang, "phòng-giam")

    # 1. Tìm hoặc tạo Role Tù Nhân
    if not jail_role:
        for r in guild.roles:
            if r.name.lower() in [default_role_name.lower(), "tù nhân", "prisoner", "jail", "tu nhan"]:
                jail_role = r
                break

        if not jail_role and guild.me.guild_permissions.manage_roles:
            try:
                jail_role = await guild.create_role(
                    name=default_role_name,
                    color=discord.Color.dark_grey(),
                    reason="SakuraBot: Tự động khởi tạo Role Tù Nhân"
                )
            except discord.Forbidden:
                return None, None, 0

        if jail_role:
            cfg["role_id"] = jail_role.id

    # 2. Tìm hoặc tạo Kênh Phòng Giam
    if not jail_channel or not isinstance(jail_channel, discord.TextChannel):
        for ch in guild.text_channels:
            if ch.name.lower() in [default_channel_name.lower(), "phòng-giam", "phong-giam", "jail-cell", "jail"]:
                jail_channel = ch
                break

        if not jail_channel and guild.me.guild_permissions.manage_channels:
            try:
                jail_channel = await guild.create_text_channel(
                    name=default_channel_name,
                    topic=get_msg(guild, "CHANNEL_TOPIC"),
                    reason="SakuraBot: Tự động khởi tạo Kênh Phòng Giam"
                )
            except discord.Forbidden:
                pass

        if jail_channel:
            cfg["channel_id"] = jail_channel.id

    save_jail_config()

    # 3. Phân quyền cho Kênh Phòng Giam
    if jail_channel and jail_role and guild.me.guild_permissions.manage_roles and guild.me.guild_permissions.manage_channels:
        await configure_jail_cell(guild, jail_role, jail_channel)

    # 4. Cách ly các kênh còn lại
    isolated_count = 0
    if jail_role:
        isolated_count = await isolate_guild_channels(guild, jail_role, jail_channel)

    return jail_role, jail_channel, isolated_count


class JailDashboardView(discord.ui.View):
    def __init__(self, cog: "JailCog", author: discord.Member, guild: discord.Guild):
        super().__init__(timeout=120)
        self.cog = cog
        self.author = author
        self.guild = guild

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id != self.author.id:
            await interaction.response.send_message("❌ Bạn không thể thao tác trên bảng điều khiển của người khác!", ephemeral=True)
            return False
        return True

    @discord.ui.button(label="⚡ Tự Động Thiết Lập (Auto Setup)", style=discord.ButtonStyle.primary, emoji="🛠️")
    async def btn_setup(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer(ephemeral=True)
        role, channel, count = await ensure_jail_setup(self.guild)
        if not role:
            return await interaction.followup.send("❌ Bot thiếu quyền `Manage Roles` hoặc `Manage Channels`!", ephemeral=True)

        msg = get_msg(
            self.guild, "SETUP_SUCCESS",
            role=role.mention,
            channel=channel.mention if channel else "Chưa tạo",
            isolated_count=count
        )
        await interaction.followup.send(msg, ephemeral=True)

    @discord.ui.button(label="🔒 Quét Cách Ly Kênh", style=discord.ButtonStyle.secondary, emoji="🛡️")
    async def btn_isolate(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer(ephemeral=True)
        cfg = get_guild_jail_config(self.guild.id)
        role = self.guild.get_role(int(cfg.get("role_id") or 0))
        ch = self.guild.get_channel(int(cfg.get("channel_id") or 0))
        if not role:
            return await interaction.followup.send("⚠️ Chưa có Role tù nhân! Vui lòng bấm `Tự Động Thiết Lập` trước.", ephemeral=True)

        count = await isolate_guild_channels(self.guild, role, ch if isinstance(ch, discord.TextChannel) else None)
        await interaction.followup.send(get_msg(self.guild, "ISOLATE_SUCCESS", count=count), ephemeral=True)

    @discord.ui.button(label="📋 Danh Sách Tù Nhân", style=discord.ButtonStyle.success, emoji="👥")
    async def btn_list(self, interaction: discord.Interaction, button: discord.ui.Button):
        records = get_guild_jail_records(self.guild.id)
        if not records:
            return await interaction.response.send_message(get_msg(self.guild, "NO_INMATES"), ephemeral=True)

        embed = discord.Embed(
            title=get_msg(self.guild, "INMATES_TITLE", count=len(records)),
            color=discord.Color.dark_orange(),
            timestamp=discord.utils.utcnow()
        )
        for u_id, rec in list(records.items())[:25]:
            target_str = f"<@{u_id}> (`{u_id}`)"
            exp = rec.get("expires_at")
            time_str = f"<t:{int(exp)}:R>" if exp else get_msg(self.guild, "PERMANENT")
            mod_str = f"<@{rec.get('jailed_by_id')}>"
            embed.add_field(
                name=f"👤 {rec.get('user_name', u_id)}",
                value=f"• **Lý do**: {rec.get('reason', 'N/A')}\n• **Thời hạn**: {time_str}\n• **Người phạt**: {mod_str}",
                inline=False
            )
        await interaction.response.send_message(embed=embed, ephemeral=True)


class JailCog(commands.Cog, name="Jail"):
    """Hệ thống Quản Lý Nhà Tù (Jail System) chuyên nghiệp cho SakuraBot."""

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    async def cog_load(self):
        load_jail_data()
        self.check_jail_expiry.start()
        logger.info("JailCog loaded and check_jail_expiry task started.")

    async def cog_unload(self):
        self.check_jail_expiry.cancel()
        logger.info("JailCog unloaded and check_jail_expiry task stopped.")

    # --- BACKGROUND TASK: TỰ ĐỘNG PHÓNG THÍCH KHI HẾT HẠN ---
    @tasks.loop(seconds=15)
    async def check_jail_expiry(self):
        now_ts = time.time()
        to_unjail = []

        async with _jail_lock:
            for g_id_str, users in list(jail_records.items()):
                for u_id_str, rec in list(users.items()):
                    exp = rec.get("expires_at")
                    if exp and now_ts >= exp:
                        to_unjail.append((int(g_id_str), int(u_id_str), rec))

        for g_id, u_id, rec in to_unjail:
            guild = self.bot.get_guild(g_id)
            if not guild:
                continue

            member = guild.get_member(u_id)
            moderator = self.bot.user

            try:
                await self.execute_unjail(
                    guild=guild,
                    member=member,
                    user_id=u_id,
                    moderator=moderator,
                    reason=get_msg(guild, "AUTO_UNJAIL_TITLE")
                )
                logger.info(f"Auto-unjailed user {u_id} in guild {guild.name} ({guild.id})")
            except Exception as e:
                logger.error(f"Error auto-unjailing user {u_id} in {guild.name}: {e}")

    @check_jail_expiry.before_loop
    async def before_check_jail_expiry(self):
        try:
            await self.bot.wait_until_ready()
        except (RuntimeError, asyncio.CancelledError):
            pass

    # --- EVENT LISTENERS: CHỐNG TRỐN TÙ VÀ CÁCH LY KÊNH MỚI ---
    @commands.Cog.listener()
    async def on_guild_channel_create(self, channel: discord.abc.GuildChannel):
        """Tự động đặt quyền ẩn với Role tù nhân trên các kênh mới được tạo."""
        guild = channel.guild
        cfg = get_guild_jail_config(guild.id)
        role_id = cfg.get("role_id")
        if not role_id:
            return
        jail_role = guild.get_role(int(role_id))
        if not jail_role:
            return

        jail_channel_id = cfg.get("channel_id")
        if channel.id == jail_channel_id:
            return

        try:
            deny_overwrite = discord.PermissionOverwrite(
                view_channel=False,
                send_messages=False,
                connect=False,
                speak=False
            )
            await channel.set_permissions(jail_role, overwrite=deny_overwrite, reason="SakuraBot: Tự động cách ly kênh mới đối với Tù Nhân")
        except (discord.Forbidden, discord.HTTPException):
            pass

    @commands.Cog.listener()
    async def on_member_join(self, member: discord.Member):
        """Chống trốn tù: Nếu người dùng rời server rồi vào lại, tự động tống giam lại ngay."""
        guild = member.guild
        records = get_guild_jail_records(guild.id)
        u_key = str(member.id)
        if u_key not in records:
            return

        cfg = get_guild_jail_config(guild.id)
        role_id = cfg.get("role_id")
        jail_role = guild.get_role(int(role_id)) if role_id else None
        if not jail_role:
            jail_role, _, _ = await ensure_jail_setup(guild)

        if jail_role and guild.me.guild_permissions.manage_roles:
            try:
                # Tước bất kỳ autorole nào vừa được cấp
                strip_roles = [
                    r for r in member.roles
                    if not r.is_default() and not r.managed and r < guild.me.top_role and r != jail_role
                ]
                if strip_roles:
                    await member.remove_roles(*strip_roles, reason="Chống trốn tù: Tước vai trò mới cấp")
                await member.add_roles(jail_role, reason="Chống trốn tù: Thành viên đang trong thời gian thụ án")
                logger.info(f"Re-jailed returning inmate {member} in {guild.name}")
            except Exception as e:
                logger.error(f"Error handling rejoined inmate {member} in {guild.name}: {e}")

    # --- CORE LOGIC: EXECUTE JAIL & UNJAIL ---
    async def execute_jail(
        self,
        guild: discord.Guild,
        member: discord.Member,
        moderator: discord.abc.User,
        duration_seconds: Optional[int],
        reason: str
    ) -> tuple[bool, str, Optional[discord.Embed]]:
        """Thực thi tống giam: Tước vai trò, cấp vai trò tù nhân, lưu dữ liệu, gửi log."""
        jail_role, jail_channel, _ = await ensure_jail_setup(guild)
        if not jail_role:
            return False, "❌ Bot thiếu quyền `Manage Roles` hoặc `Manage Channels` để thiết lập nhà tù!", None

        # Thu thập các vai trò hiện có cần tạm tước (giữ lại default, managed, booster và roles cao hơn bot)
        saved_role_ids = []
        roles_to_remove = []
        for r in member.roles:
            if r.is_default() or r.managed:
                continue
            if hasattr(r, "is_premium_subscriber") and r.is_premium_subscriber():
                continue
            if r >= guild.me.top_role:
                continue
            saved_role_ids.append(r.id)
            roles_to_remove.append(r)

        # 1. Tước vai trò cũ & cấp Role Tù Nhân
        try:
            if roles_to_remove and guild.me.guild_permissions.manage_roles:
                await member.remove_roles(*roles_to_remove, reason=f"Tống giam bởi {moderator}: Tạm giữ vai trò")
            await member.add_roles(jail_role, reason=f"Tống giam bởi {moderator}: {reason}")
        except discord.Forbidden:
            return False, "❌ Bot không đủ quyền quản lý vai trò của thành viên này!", None

        # 2. Ngắt kết nối Voice nếu đang trong kênh thoại
        if member.voice and member.voice.channel and guild.me.guild_permissions.move_members:
            try:
                await member.move_to(None, reason=f"Tống giam bởi {moderator}")
            except Exception:
                pass

        # 3. Tính toán thời gian
        now_ts = time.time()
        expires_at = (now_ts + duration_seconds) if duration_seconds else None

        if duration_seconds:
            dur_display = f"<t:{int(expires_at)}:R> (<t:{int(expires_at)}:F>)"
            dur_extra = f"Hết hạn: <t:{int(expires_at)}:R>"
        else:
            dur_display = get_msg(guild, "PERMANENT")
            dur_extra = "Vô thời hạn"

        # 4. Lưu hồ sơ phạm nhân
        async with _jail_lock:
            g_records = get_guild_jail_records(guild.id)
            g_records[str(member.id)] = {
                "user_name": str(member),
                "jailed_at": now_ts,
                "expires_at": expires_at,
                "duration_seconds": duration_seconds,
                "reason": reason,
                "jailed_by_id": moderator.id,
                "jailed_by_name": str(moderator),
                "saved_roles": saved_role_ids
            }
            save_jail_records()

        # 5. Gửi log vào Mod/Warn Log Channel
        try:
            await send_mod_log(
                guild=guild,
                action_title=get_msg(guild, "JAIL_TITLE"),
                moderator=moderator,
                target_str=f"{member.mention} (`{member.id}`)",
                reason=reason,
                color=discord.Color.dark_orange(),
                extra_info=f"⏱️ Thời hạn: {dur_extra}\n🔒 Phòng giam: {jail_channel.mention if jail_channel else 'N/A'}"
            )
        except Exception as e:
            logger.warning(f"Failed to send mod log for jail: {e}")

        # 6. Gửi DM cho đối tượng
        try:
            await notify_target_dm(
                member=member,
                guild=guild,
                action_vi="Tống Giam (Jail)",
                reason=reason,
                extra=f"Thời hạn: {dur_extra} | Toàn bộ các kênh thông thường đã bị ẩn."
            )
        except Exception:
            pass

        # 7. Gửi thông báo chào mừng trong Kênh Phòng Giam
        if jail_channel:
            try:
                cell_embed = discord.Embed(
                    title="🔒 Bạn Đã Bị Đưa Vào Phòng Giam",
                    description=get_msg(guild, "CELL_WELCOME", mention=member.mention),
                    color=discord.Color.red(),
                    timestamp=discord.utils.utcnow()
                )
                cell_embed.add_field(name=get_msg(guild, "FIELD_TARGET"), value=member.mention, inline=True)
                cell_embed.add_field(name=get_msg(guild, "FIELD_MOD"), value=moderator.mention, inline=True)
                cell_embed.add_field(name=get_msg(guild, "FIELD_DURATION"), value=dur_display, inline=False)
                cell_embed.add_field(name=get_msg(guild, "FIELD_REASON"), value=reason, inline=False)
                await jail_channel.send(f"{member.mention}", embed=cell_embed)
            except Exception:
                pass

        # 8. Tạo Embed phản hồi kết quả
        res_embed = discord.Embed(
            title=get_msg(guild, "JAIL_TITLE"),
            color=discord.Color.dark_orange(),
            timestamp=discord.utils.utcnow()
        )
        res_embed.add_field(name=get_msg(guild, "FIELD_TARGET"), value=f"{member.mention} (`{member.id}`)", inline=True)
        res_embed.add_field(name=get_msg(guild, "FIELD_MOD"), value=moderator.mention, inline=True)
        res_embed.add_field(name=get_msg(guild, "FIELD_DURATION"), value=dur_display, inline=False)
        res_embed.add_field(name=get_msg(guild, "FIELD_REASON"), value=reason, inline=False)
        if jail_channel:
            res_embed.add_field(name=get_msg(guild, "FIELD_CELL"), value=jail_channel.mention, inline=True)

        return True, get_msg(guild, "JAIL_SUCCESS", target=member.mention), res_embed

    async def execute_unjail(
        self,
        guild: discord.Guild,
        member: Optional[discord.Member],
        user_id: int,
        moderator: discord.abc.User,
        reason: str
    ) -> tuple[bool, str, int]:
        """Thực thi phóng thích: Gỡ role tù nhân, khôi phục vai trò cũ, xóa hồ sơ."""
        rec = None
        async with _jail_lock:
            g_records = get_guild_jail_records(guild.id)
            rec = g_records.pop(str(user_id), None)
            save_jail_records()

        cfg = get_guild_jail_config(guild.id)
        role_id = cfg.get("role_id")
        jail_role = guild.get_role(int(role_id)) if role_id else None

        restored_count = 0
        if member and guild.me.guild_permissions.manage_roles:
            # Gỡ Role Tù Nhân
            if jail_role and jail_role in member.roles:
                try:
                    await member.remove_roles(jail_role, reason=f"Phóng thích bởi {moderator}")
                except Exception:
                    pass

            # Khôi phục vai trò đã lưu
            if rec and "saved_roles" in rec:
                roles_to_restore = []
                for r_id in rec["saved_roles"]:
                    r = guild.get_role(int(r_id))
                    if r and not r.managed and r < guild.me.top_role and r not in member.roles:
                        roles_to_restore.append(r)
                if roles_to_restore:
                    try:
                        await member.add_roles(*roles_to_restore, reason=f"Phóng thích bởi {moderator}: Khôi phục vai trò")
                        restored_count = len(roles_to_restore)
                    except Exception as e:
                        logger.warning(f"Error restoring roles for {member}: {e}")

        # Gửi log vào Mod/Warn Log Channel
        target_str = member.mention if member else f"<@{user_id}>"
        try:
            await send_mod_log(
                guild=guild,
                action_title=get_msg(guild, "UNJAIL_TITLE"),
                moderator=moderator,
                target_str=f"{target_str} (`{user_id}`)",
                reason=reason,
                color=discord.Color.green(),
                extra_info=f"🔄 Đã khôi phục {restored_count} vai trò"
            )
        except Exception as e:
            logger.warning(f"Failed to send mod log for unjail: {e}")

        # Gửi DM cho đối tượng nếu còn trong server
        if member:
            try:
                await notify_target_dm(
                    member=member,
                    guild=guild,
                    action_vi="Phóng Thích (Unjail)",
                    reason=reason,
                    extra=f"Bạn đã được thả tự do và khôi phục {restored_count} vai trò tại {guild.name}."
                )
            except Exception:
                pass

        # Thông báo vào Kênh Phòng Giam nếu có
        ch_id = cfg.get("channel_id")
        if ch_id:
            jail_channel = guild.get_channel(int(ch_id))
            if jail_channel and isinstance(jail_channel, discord.TextChannel):
                try:
                    await jail_channel.send(f"🔓 {target_str} đã được phóng thích tự do! (Lý do: {reason})")
                except Exception:
                    pass

        return True, get_msg(guild, "UNJAIL_SUCCESS", target=target_str, count=restored_count), restored_count

    # --- HYBRID COMMAND GROUP (TỐI ƯU HÓA SLASH COMMANDS) ---

    @commands.hybrid_group(
        name="jail",
        aliases=["giam", "tonggiam"],
        description="🚨 Hệ thống quản lý nhà tù và phạm nhân."
    )
    @commands.guild_only()
    async def jail_group(self, ctx: commands.Context):
        """Mở bảng điều khiển nhà tù nếu không truyền lệnh con."""
        if ctx.invoked_subcommand is None:
            await self._send_dashboard(ctx)

    async def _send_dashboard(self, ctx: commands.Context):
        cfg = get_guild_jail_config(ctx.guild.id)
        role = ctx.guild.get_role(int(cfg.get("role_id") or 0))
        channel = ctx.guild.get_channel(int(cfg.get("channel_id") or 0))

        embed = discord.Embed(
            title=get_msg(ctx.guild, "CONFIG_TITLE"),
            description="Bảng điều khiển quản lý và phân quyền hệ thống nhà tù SakuraBot.",
            color=discord.Color.dark_theme(),
            timestamp=discord.utils.utcnow()
        )
        embed.add_field(name="🏷️ Role Tù Nhân", value=role.mention if role else "`Chưa thiết lập (Tự tạo khi setup)`", inline=True)
        embed.add_field(name="🔒 Kênh Phòng Giam", value=channel.mention if channel else "`Chưa thiết lập (Tự tạo khi setup)`", inline=True)
        embed.add_field(name="👥 Tù Nhân Đang Thụ Án", value=f"**{len(get_guild_jail_records(ctx.guild.id))}** người", inline=True)
        embed.set_footer(text="Dùng các nút bên dưới hoặc lệnh slash con /jail <add|release|status|setup|isolate>")

        view = JailDashboardView(self, ctx.author, ctx.guild)
        await ctx.send(embed=embed, view=view)

    @jail_group.command(
        name="add",
        aliases=["user", "send"],
        description="🚨 Tống giam một thành viên vào nhà tù (Ẩn mọi kênh, chỉ thấy phòng giam)."
    )
    @app_commands.describe(
        member="Thành viên cần tống giam",
        duration="Thời hạn giam (Ví dụ: 10m, 2h, 1d, 7d). Để trống để phạt vô thời hạn.",
        reason="Lý do tống giam"
    )
    @has_admin_role()
    async def jail_add(
        self,
        ctx: commands.Context,
        member: discord.Member,
        duration: Optional[str] = None,
        *,
        reason: Optional[str] = "Vi phạm quy định máy chủ"
    ):
        await self._process_jail(ctx, member, duration, reason)

    @jail_group.command(
        name="release",
        aliases=["unjail", "free"],
        description="🔓 Phóng thích thành viên khỏi nhà tù và khôi phục lại các vai trò cũ."
    )
    @app_commands.describe(
        member="Thành viên cần phóng thích",
        reason="Lý do phóng thích"
    )
    @has_admin_role()
    async def jail_release(
        self,
        ctx: commands.Context,
        member: discord.Member,
        *,
        reason: Optional[str] = "Được ân xá / Hết hạn phạt"
    ):
        await self._process_unjail(ctx, member, reason)

    @jail_group.command(
        name="status",
        aliases=["list"],
        description="📋 Xem danh sách các tù nhân đang thụ án hoặc tra cứu hồ sơ phạm nhân."
    )
    @app_commands.describe(member="Thành viên cần tra cứu hồ sơ (để trống để xem tất cả)")
    async def jail_status(self, ctx: commands.Context, member: Optional[discord.Member] = None):
        await self._process_status(ctx, member)

    @jail_group.command(
        name="panel",
        description="🎛️ Mở bảng điều khiển nhà tù trực quan với các nút bấm thao tác nhanh."
    )
    @has_admin_role()
    async def jail_panel(self, ctx: commands.Context):
        await self._send_dashboard(ctx)

    @jail_group.command(
        name="setup",
        description="🛠️ Tự động tạo Role Tù Nhân, Kênh Phòng Giam và cách ly tất cả các kênh."
    )
    @has_admin_role()
    async def jail_setup(self, ctx: commands.Context):
        await ctx.defer()
        role, channel, count = await ensure_jail_setup(ctx.guild)
        if not role:
            return await ctx.send("❌ Bot thiếu quyền `Manage Roles` hoặc `Manage Channels`!", ephemeral=True)

        msg = get_msg(
            ctx.guild, "SETUP_SUCCESS",
            role=role.mention,
            channel=channel.mention if channel else "Chưa tạo",
            isolated_count=count
        )
        await ctx.send(msg)

    @jail_group.command(
        name="role",
        description="🏷️ Chỉ định một Role có sẵn làm vai trò tù nhân."
    )
    @app_commands.describe(role="Vai trò muốn dùng làm Role tù nhân")
    @has_admin_role()
    async def jail_role(self, ctx: commands.Context, role: discord.Role):
        cfg = get_guild_jail_config(ctx.guild.id)
        cfg["role_id"] = role.id
        save_jail_config()
        await ctx.send(f"✅ Đã thiết lập Role tù nhân là: {role.mention}")

    @jail_group.command(
        name="channel",
        description="🔒 Chỉ định một Kênh văn bản có sẵn làm Kênh Phòng Giam."
    )
    @app_commands.describe(channel="Kênh văn bản muốn làm phòng giam")
    @has_admin_role()
    async def jail_channel(self, ctx: commands.Context, channel: discord.TextChannel):
        cfg = get_guild_jail_config(ctx.guild.id)
        cfg["channel_id"] = channel.id
        save_jail_config()

        role = ctx.guild.get_role(int(cfg.get("role_id") or 0))
        if role:
            await configure_jail_cell(ctx.guild, role, channel)

        await ctx.send(f"✅ Đã thiết lập Kênh phòng giam là: {channel.mention}")

    @jail_group.command(
        name="isolate",
        description="🛡️ Quét và cập nhật quyền cách ly (ẩn kênh) trên toàn bộ máy chủ."
    )
    @has_admin_role()
    async def jail_isolate(self, ctx: commands.Context):
        await ctx.defer()
        cfg = get_guild_jail_config(ctx.guild.id)
        role_id = cfg.get("role_id")
        role = ctx.guild.get_role(int(role_id or 0))
        if not role:
            return await ctx.send("⚠️ Chưa có Role tù nhân! Vui lòng chạy `/jail setup` hoặc `/jail role` trước.", ephemeral=True)

        ch = ctx.guild.get_channel(int(cfg.get("channel_id") or 0))
        count = await isolate_guild_channels(ctx.guild, role, ch if isinstance(ch, discord.TextChannel) else None)
        await ctx.send(get_msg(ctx.guild, "ISOLATE_SUCCESS", count=count))

    # --- PREFIX SHORTCUTS (GIỮ NGUYÊN TIỆN ÍCH DÙNG DẤU CHẤM THAN) ---

    @commands.command(name="unjail", aliases=["phongthich", "tha", "anxa"])
    @commands.guild_only()
    @has_admin_role()
    async def prefix_unjail(self, ctx: commands.Context, member: discord.Member, *, reason: Optional[str] = "Được ân xá"):
        await self._process_unjail(ctx, member, reason)

    @commands.command(name="jailstatus", aliases=["jaillist", "danhsachtu"])
    @commands.guild_only()
    async def prefix_jailstatus(self, ctx: commands.Context, member: Optional[discord.Member] = None):
        await self._process_status(ctx, member)

    # --- SHARED PROCESSORS ---

    async def _process_jail(
        self,
        ctx: commands.Context,
        member: discord.Member,
        duration: Optional[str] = None,
        reason: Optional[str] = "Vi phạm quy định máy chủ"
    ):
        await ctx.defer()
        guild = ctx.guild

        if member.id == guild.owner_id:
            return await ctx.send(get_msg(guild, "ERR_CANNOT_JAIL_OWNER"), ephemeral=True)
        if member.id == ctx.author.id:
            return await ctx.send(get_msg(guild, "ERR_CANNOT_JAIL_SELF"), ephemeral=True)
        if member.id == self.bot.user.id:
            return await ctx.send(get_msg(guild, "ERR_CANNOT_JAIL_BOT"), ephemeral=True)

        if ctx.author.id != guild.owner_id and member.top_role >= ctx.author.top_role:
            return await ctx.send(get_msg(guild, "ERR_HIERARCHY_USER"), ephemeral=True)

        if guild.me and member.top_role >= guild.me.top_role:
            return await ctx.send(get_msg(guild, "ERR_HIERARCHY_BOT"), ephemeral=True)

        g_records = get_guild_jail_records(guild.id)
        if str(member.id) in g_records:
            existing = g_records[str(member.id)]
            exp = existing.get("expires_at")
            rem = f"<t:{int(exp)}:R>" if exp else get_msg(guild, "PERMANENT")
            return await ctx.send(get_msg(guild, "ERR_ALREADY_JAILED", remaining=rem), ephemeral=True)

        duration_seconds = None
        if duration:
            dur_clean = duration.strip().lower()
            if dur_clean not in ("perm", "permanent", "vinhvien", "vô thời hạn"):
                duration_seconds = parse_duration_to_seconds(dur_clean)
                if not duration_seconds or duration_seconds <= 0:
                    return await ctx.send("⚠️ Định dạng thời gian không hợp lệ! Ví dụ hợp lệ: `30m`, `2h`, `1d`, `7d`", ephemeral=True)

        success, msg, embed = await self.execute_jail(
            guild=guild,
            member=member,
            moderator=ctx.author,
            duration_seconds=duration_seconds,
            reason=reason or "Vi phạm quy định máy chủ"
        )

        if success and embed:
            await ctx.send(embed=embed)
        else:
            await ctx.send(msg, ephemeral=True)

    async def _process_unjail(
        self,
        ctx: commands.Context,
        member: discord.Member,
        reason: Optional[str] = "Được ân xá / Hết hạn phạt"
    ):
        await ctx.defer()
        guild = ctx.guild
        g_records = get_guild_jail_records(guild.id)

        cfg = get_guild_jail_config(guild.id)
        role_id = cfg.get("role_id")
        has_role = bool(role_id and guild.get_role(int(role_id)) in member.roles)

        if str(member.id) not in g_records and not has_role:
            return await ctx.send(get_msg(guild, "ERR_NOT_JAILED"), ephemeral=True)

        success, msg, count = await self.execute_unjail(
            guild=guild,
            member=member,
            user_id=member.id,
            moderator=ctx.author,
            reason=reason or "Được ân xá bởi Quản trị viên"
        )

        embed = discord.Embed(
            title=get_msg(guild, "UNJAIL_TITLE"),
            color=discord.Color.green(),
            timestamp=discord.utils.utcnow()
        )
        embed.add_field(name=get_msg(guild, "FIELD_TARGET"), value=f"{member.mention} (`{member.id}`)", inline=True)
        embed.add_field(name=get_msg(guild, "FIELD_MOD"), value=ctx.author.mention, inline=True)
        embed.add_field(name=get_msg(guild, "FIELD_RESTORED_ROLES"), value=f"**{count}** vai trò", inline=True)
        embed.add_field(name=get_msg(guild, "FIELD_REASON"), value=reason, inline=False)
        await ctx.send(embed=embed)

    async def _process_status(self, ctx: commands.Context, member: Optional[discord.Member] = None):
        guild = ctx.guild
        records = get_guild_jail_records(guild.id)

        if member:
            u_key = str(member.id)
            if u_key not in records:
                return await ctx.send(get_msg(guild, "ERR_NOT_JAILED"), ephemeral=True)

            rec = records[u_key]
            exp = rec.get("expires_at")
            time_str = f"<t:{int(exp)}:R> (<t:{int(exp)}:F>)" if exp else get_msg(guild, "PERMANENT")
            jailed_since = f"<t:{int(rec['jailed_at'])}:F> (<t:{int(rec['jailed_at'])}:R>)"

            embed = discord.Embed(
                title=get_msg(guild, "INMATE_PROFILE_TITLE", name=member.display_name),
                color=discord.Color.dark_orange(),
                timestamp=discord.utils.utcnow()
            )
            embed.set_thumbnail(url=member.display_avatar.url)
            embed.add_field(name=get_msg(guild, "FIELD_TARGET"), value=f"{member.mention} (`{member.id}`)", inline=True)
            embed.add_field(name=get_msg(guild, "FIELD_MOD"), value=f"<@{rec.get('jailed_by_id')}>", inline=True)
            embed.add_field(name="📅 Bắt Đầu Giam", value=jailed_since, inline=False)
            embed.add_field(name=get_msg(guild, "FIELD_DURATION"), value=time_str, inline=False)
            embed.add_field(name=get_msg(guild, "FIELD_REASON"), value=rec.get("reason", "N/A"), inline=False)
            embed.add_field(name="📦 Vai Trò Tạm Giữ", value=f"**{len(rec.get('saved_roles', []))}** vai trò", inline=True)
            return await ctx.send(embed=embed)

        if not records:
            return await ctx.send(get_msg(guild, "NO_INMATES"))

        embed = discord.Embed(
            title=get_msg(guild, "INMATES_TITLE", count=len(records)),
            description="Danh sách các thành viên hiện đang thụ án giam giữ tại máy chủ.",
            color=discord.Color.dark_orange(),
            timestamp=discord.utils.utcnow()
        )

        for u_id, rec in list(records.items())[:25]:
            exp = rec.get("expires_at")
            time_str = f"<t:{int(exp)}:R>" if exp else get_msg(guild, "PERMANENT")
            mod_str = f"<@{rec.get('jailed_by_id')}>"
            embed.add_field(
                name=f"👤 {rec.get('user_name', u_id)}",
                value=f"• **Thành viên**: <@{u_id}>\n• **Thời hạn**: {time_str}\n• **Lý do**: {rec.get('reason', 'N/A')}\n• **Người phạt**: {mod_str}",
                inline=False
            )

        if len(records) > 25:
            embed.set_footer(text=f"Và {len(records) - 25} phạm nhân khác...")

        await ctx.send(embed=embed)


async def setup(bot: commands.Bot):
    await bot.add_cog(JailCog(bot))
