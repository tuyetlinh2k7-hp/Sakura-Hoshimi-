import re
import asyncio
import os
import json
from pathlib import Path
from datetime import datetime, timedelta
from typing import Literal, Optional

import aiohttp
import discord
from discord.ext import commands
from discord import app_commands

from config import OWNER_ID
from Check.mod import has_admin_role
from Check.i18n import t, is_vietnamese, set_guild_language
from Check.data import LOG_CHANNEL_ID, get_guild_settings, save_data
from Check.server_config import is_feature_enabled, is_admin_only, save_server_config

BASE_DIR = Path(__file__).resolve().parent.parent
WARNINGS_FILE = BASE_DIR / "data" / "warnings.json"

try:
    from Command.checks import warnings
except ImportError:
    warnings = {}


def load_warnings():
    if WARNINGS_FILE.exists():
        try:
            with open(WARNINGS_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                if isinstance(data, dict):
                    warnings.clear()
                    warnings.update(data)
        except Exception:
            pass


_warnings_lock: Optional[asyncio.Lock] = None


def get_warnings_lock() -> asyncio.Lock:
    global _warnings_lock
    if _warnings_lock is None:
        _warnings_lock = asyncio.Lock()
    return _warnings_lock


def _save_warnings_sync(data_snapshot: dict):
    WARNINGS_FILE.parent.mkdir(parents=True, exist_ok=True)
    try:
        with open(WARNINGS_FILE, "w", encoding="utf-8") as f:
            json.dump(data_snapshot, f, indent=4, ensure_ascii=False)
    except Exception:
        pass
    try:
        save_data()
    except Exception:
        pass


async def _save_warnings_task():
    """Khóa tuần tự hóa bằng asyncio.Lock() để tránh xung đột ghi tệp (I/O Collision) khi nhiều admin cùng thao tác."""
    async with get_warnings_lock():
        data_snapshot = {k: list(v) if isinstance(v, list) else v for k, v in warnings.items()}
        await asyncio.to_thread(_save_warnings_sync, data_snapshot)


def save_warnings():
    """Lưu cảnh cáo an toàn, không block Event Loop và tránh nghẽn I/O khi lưu đồng thời."""
    try:
        loop = asyncio.get_running_loop()
        loop.create_task(_save_warnings_task())
    except RuntimeError:
        data_snapshot = {k: list(v) if isinstance(v, list) else v for k, v in warnings.items()}
        _save_warnings_sync(data_snapshot)


load_warnings()


def check_hierarchy(guild: discord.Guild, author: discord.Member, target: discord.Member) -> Optional[str]:
    if target.id == author.id:
        return t(guild, "MOD_ERR_CANNOT_PUNISH_SELF", default="❌ Bạn không thể tự thực hiện hình phạt lên chính mình!")
    if target.id == guild.owner_id:
        return t(guild, "MOD_ERR_CANNOT_PUNISH_OWNER", default="❌ Không thể thực hiện hình phạt lên Chủ sở hữu máy chủ (Server Owner)!")
    if author.id not in (guild.owner_id, OWNER_ID) and target.top_role >= author.top_role:
        return t(guild, "MOD_ERR_HIERARCHY_USER", default="❌ Bạn không thể phạt người có vai trò (Role) cao hơn hoặc ngang bằng bạn!")
    if guild.me and target.top_role >= guild.me.top_role:
        return t(guild, "MOD_ERR_HIERARCHY_BOT", default="❌ Vai trò của Bot đang thấp hơn hoặc ngang bằng người này, không thể thực thi!")
    return None


async def send_mod_log(
    guild: discord.Guild,
    action_title: str,
    moderator: discord.abc.User,
    target_str: str,
    reason: str,
    color: discord.Color,
    extra_info: Optional[str] = None
):
    log_ch_id = LOG_CHANNEL_ID.get(str(guild.id))
    if not log_ch_id:
        return
    log_channel = guild.get_channel(int(log_ch_id))
    if not log_channel or not isinstance(log_channel, discord.TextChannel):
        return

    embed = discord.Embed(
        title=f"🛡️ Nhật Ký Kiểm Duyệt: {action_title}",
        color=color,
        timestamp=discord.utils.utcnow()
    )
    embed.add_field(name="👤 Đối tượng", value=target_str, inline=True)
    embed.add_field(name="🔨 Người thực hiện", value=f"{moderator.mention} (`{moderator.id}`)", inline=True)
    if extra_info:
        embed.add_field(name="⏱️ Chi tiết", value=extra_info, inline=True)
    embed.add_field(name="📝 Lý do", value=reason, inline=False)
    embed.set_footer(text=f"Server: {guild.name}", icon_url=guild.icon.url if guild.icon else None)

    try:
        await log_channel.send(embed=embed)
    except (discord.Forbidden, discord.HTTPException):
        pass


async def notify_target_dm(
    member: discord.abc.User,
    guild: discord.Guild,
    action_vi: str,
    reason: str,
    extra: Optional[str] = None
):
    if getattr(member, "bot", False):
        return
    if not is_feature_enabled(guild.id, "mod_dm_notifications", default=True):
        return
    embed = discord.Embed(
        title=f"⚠️ Thông Báo Kiểm Duyệt từ {guild.name}",
        description=f"Bạn vừa nhận quyết định **{action_vi}** tại máy chủ **{guild.name}**.",
        color=discord.Color.red(),
        timestamp=discord.utils.utcnow()
    )
    if extra:
        embed.add_field(name="⏱️ Thời hạn / Ghi chú", value=extra, inline=False)
    embed.add_field(name="📝 Lý do", value=reason, inline=False)
    try:
        await member.send(embed=embed)
    except (discord.Forbidden, discord.HTTPException):
        pass



def parse_duration_to_seconds(raw_str: str) -> Optional[int]:
    """Chuyển đổi chuỗi thời gian như '10m', '2h', '1d', '30s', '1w' hoặc số phút thuần thành giây."""
    if not raw_str:
        return None
    s = str(raw_str).strip().lower()
    if not s:
        return None
    if s.isdigit():
        return int(s) * 60

    units = {'s': 1, 'm': 60, 'h': 3600, 'd': 86400, 'w': 604800}
    matches = re.findall(r'(\d+)\s*([smhdw])', s)
    if not matches:
        return None

    total = 0
    for val, unit in matches:
        total += int(val) * units[unit]
    return total if total > 0 else None

class ClearModal(discord.ui.Modal):
    def __init__(self, guild: Optional[discord.Guild] = None):
        super().__init__(title=t(guild, "MODM_CLEAR_MODAL_TITLE") if guild else "🗑️ Xóa Tin Nhắn Channel")
        self.amount = discord.ui.TextInput(
            label=t(guild, "MODM_CLEAR_LABEL") if guild else "Số lượng cần xóa (Hoặc ghi 'all')",
            placeholder=t(guild, "MODM_CLEAR_PLACEHOLDER") if guild else "Ví dụ: 10, 50 hoặc all",
            required=True
        )
        self.add_item(self.amount)

    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        val = self.amount.value.strip().lower()
        try:
            if val == "all":
                deleted = await interaction.channel.purge(limit=1000, bulk=True)
                await interaction.followup.send(
                    t(interaction.guild, "MODM_CLEAR_SUCCESS_ALL", count=len(deleted)),
                    ephemeral=True
                )
            else:
                num = int(val)
                if num <= 0:
                    raise ValueError
                deleted = await interaction.channel.purge(limit=num, bulk=True)
                await interaction.followup.send(
                    t(interaction.guild, "MODM_CLEAR_SUCCESS", count=len(deleted)),
                    ephemeral=True
                )
        except ValueError:
            await interaction.followup.send(t(interaction.guild, "MODM_CLEAR_INVALID"), ephemeral=True)
        except discord.Forbidden:
            await interaction.followup.send("❌ Bot không có quyền **Quản lý tin nhắn (Manage Messages)**!", ephemeral=True)
        except discord.HTTPException as e:
            if getattr(e, "code", None) == 50034:
                await interaction.followup.send("⚠️ Không thể xóa các tin nhắn cũ hơn 14 ngày (giới hạn của Discord)!", ephemeral=True)
            else:
                await interaction.followup.send(f"❌ Lỗi từ Discord khi xóa: `{e}`", ephemeral=True)


class SlowmodeModal(discord.ui.Modal, title="⏱️ Chỉnh Chế Độ Chậm (Slowmode)"):
    seconds_input = discord.ui.TextInput(
        label="Số giây chờ giữa 2 tin nhắn (0 - 21600)",
        placeholder="Nhập 0 để tắt, hoặc số giây (vd: 5, 10, 60)...",
        required=True,
        max_length=5
    )

    async def on_submit(self, interaction: discord.Interaction):
        try:
            sec = int(self.seconds_input.value.strip())
            if sec < 0 or sec > 21600:
                raise ValueError
            await interaction.channel.edit(slowmode_delay=sec, reason=f"Slowmode by {interaction.user}")
            if sec == 0:
                await interaction.response.send_message("✅ Đã **tắt** chế độ chậm (Slowmode) cho kênh này!", ephemeral=True)
            else:
                await interaction.response.send_message(f"⏱️ Đã đặt chế độ chậm của kênh thành **{sec} giây**!", ephemeral=True)
        except ValueError:
            await interaction.response.send_message("⚠️ Vui lòng nhập một số nguyên hợp lệ từ `0` đến `21600`!", ephemeral=True)
        except discord.Forbidden:
            await interaction.response.send_message("❌ Bot thiếu quyền **Quản lý kênh (Manage Channels)**!", ephemeral=True)


class PunishModal(discord.ui.Modal):
    def __init__(self, action_type: str, prefilled_user: str = "", guild: Optional[discord.Guild] = None):
        super().__init__(
            title=t(guild, "MODM_PUNISH_TITLE", action=action_type.upper())
            if guild else f"🔨 Thực Thi Quyết Định: {action_type.upper()}"
        )
        self.action_type = action_type
        self.guild = guild

        self.user_id = discord.ui.TextInput(
            label=t(guild, "MODM_PUNISH_LABEL_USER") if guild else "ID Người dùng hoặc Tag Người dùng",
            placeholder=t(guild, "MODM_PUNISH_PLACEHOLDER_USER") if guild else "Dán ID hoặc @user vào đây...",
            default=prefilled_user if prefilled_user else None,
            required=True
        )
        self.add_item(self.user_id)

        if action_type == "mute":
            self.duration = discord.ui.TextInput(
                label=t(guild, "MODM_PUNISH_LABEL_DURATION") if guild else "Thời gian cấm chat (vd: 10m, 2h, 1d...)",
                placeholder=t(guild, "MODM_PUNISH_PLACEHOLDER_DURATION") if guild else "Ví dụ: 10m, 2h, 1d... (Nhập số thuần tính theo phút)",
                required=True
            )
            self.add_item(self.duration)

        self.reason = discord.ui.TextInput(
            label=t(guild, "MODM_PUNISH_LABEL_REASON") if guild else "Lý do xử lý",
            style=discord.TextStyle.paragraph,
            placeholder=t(guild, "MODM_PUNISH_PLACEHOLDER_REASON") if guild else "Nhập lý do vi phạm tại đây...",
            required=False,
            max_length=500
        )
        self.add_item(self.reason)

    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        guild = interaction.guild
        reason_str = self.reason.value.strip() if self.reason.value else t(guild, "MODM_DEFAULT_REASON")

        raw_id = self.user_id.value.replace("<@", "").replace(">", "").replace("!", "").strip()
        try:
            member_id = int(raw_id)
            member = guild.get_member(member_id) or await guild.fetch_member(member_id)
        except (ValueError, discord.NotFound, discord.HTTPException):
            return await interaction.followup.send(t(guild, "MODM_USER_NOT_FOUND"), ephemeral=True)

        await execute_punishment(interaction, member, self.action_type, reason_str, getattr(self, "duration", None))


async def execute_punishment(
    interaction_or_ctx: discord.Interaction | commands.Context,
    member: discord.Member,
    action_type: str,
    reason_str: str,
    duration_input=None
):
    guild = interaction_or_ctx.guild
    author = interaction_or_ctx.user if isinstance(interaction_or_ctx, discord.Interaction) else interaction_or_ctx.author

    async def send_reply(text: str, ephemeral: bool = True):
        if isinstance(interaction_or_ctx, discord.Interaction):
            if interaction_or_ctx.response.is_done():
                try:
                    await interaction_or_ctx.edit_original_response(content=text, embed=None, view=None)
                except Exception:
                    await interaction_or_ctx.followup.send(text, ephemeral=ephemeral)
            else:
                await interaction_or_ctx.response.send_message(text, ephemeral=ephemeral)
        else:
            await interaction_or_ctx.send(text, ephemeral=ephemeral if getattr(interaction_or_ctx, "interaction", None) else False)

    hierarchy_err = check_hierarchy(guild, author, member)
    if hierarchy_err:
        return await send_reply(hierarchy_err)

    audit_reason = f"{reason_str} (Bởi: {author} | ID: {author.id})"

    if action_type == "warn":
        guild_key = f"{guild.id}_{member.id}"
        if guild_key not in warnings or not isinstance(warnings[guild_key], list):
            warnings[guild_key] = []
        warnings[guild_key].append({
            "reason": reason_str,
            "by": author.id,
            "time": discord.utils.utcnow().isoformat()
        })
        save_warnings()
        total_warns = len(warnings[guild_key])

        embed = discord.Embed(title=t(guild, "MODM_WARN_TITLE"), color=discord.Color.yellow())
        embed.add_field(name=t(guild, "MODM_WARN_FIELD_TARGET"), value=f"{member.mention} (`{member.id}`)", inline=True)
        embed.add_field(name=t(guild, "MODM_WARN_FIELD_MOD"), value=author.mention, inline=True)
        embed.add_field(name="📊 Tổng lần cảnh cáo", value=f"**{total_warns}** lần", inline=True)
        embed.add_field(name=t(guild, "MODM_WARN_FIELD_REASON"), value=reason_str, inline=False)

        await interaction_or_ctx.channel.send(embed=embed)
        await notify_target_dm(member, guild, f"Cảnh cáo (Lần thứ {total_warns})", reason_str)
        await send_mod_log(
            guild, "Cảnh Cáo (Warn)", author,
            f"{member.mention} (`{member.id}`)", reason_str,
            discord.Color.yellow(), f"Cảnh cáo lần thứ {total_warns}"
        )
        await send_reply(t(guild, "MODM_WARN_SUCCESS"))

    elif action_type == "mute":
        try:
            raw_duration = duration_input.value if hasattr(duration_input, "value") else str(duration_input or "")
            raw_duration = raw_duration.strip()
            if not raw_duration:
                return await send_reply("⚠️ Vui lòng nhập thời gian cấm chat!")

            if raw_duration.startswith("-") or raw_duration in ("0", "0s", "0m", "0h", "0d"):
                return await send_reply("⚠️ Thời gian cấm chat phải lớn hơn **0 giây**!")

            total_sec = parse_duration_to_seconds(raw_duration)
            if total_sec is None:
                return await send_reply("⚠️ Định dạng thời gian không hợp lệ! Ví dụ: `10m`, `2h`, `1d` hoặc nhập số phút.")

            if total_sec <= 0:
                return await send_reply("⚠️ Thời gian cấm chat phải lớn hơn **0 giây**!")

            if total_sec > 2419200:
                return await send_reply("⚠️ Thời gian cấm chat tối đa là **28 ngày** (2419200 giây theo quy định Discord)!")

            until = discord.utils.utcnow() + timedelta(seconds=total_sec)
            await member.timeout(until, reason=audit_reason)

            mins = total_sec // 60
            hrs = mins // 60
            days = hrs // 24
            if days > 0:
                dur_text = f"{days} ngày {hrs % 24} giờ"
            elif hrs > 0:
                dur_text = f"{hrs} giờ {mins % 60} phút"
            elif mins > 0:
                dur_text = f"{mins} phút"
            else:
                dur_text = f"{total_sec} giây"

            embed = discord.Embed(title=t(guild, "MODM_MUTE_TITLE"), color=discord.Color.orange())
            embed.add_field(name=t(guild, "MODM_MUTE_FIELD_TARGET"), value=member.mention, inline=True)
            embed.add_field(name=t(guild, "MODM_MUTE_FIELD_DURATION"), value=f"`{dur_text}`", inline=True)
            embed.add_field(name=t(guild, "MODM_WARN_FIELD_REASON"), value=reason_str, inline=False)

            await interaction_or_ctx.channel.send(embed=embed)
            await notify_target_dm(member, guild, "Cấm chat (Timeout)", reason_str, dur_text)
            await send_mod_log(
                guild, "Cấm Chat (Mute)", author,
                f"{member.mention} (`{member.id}`)", reason_str,
                discord.Color.orange(), dur_text
            )
            await send_reply(t(guild, "MODM_MUTE_SUCCESS"))
        except (ValueError, discord.HTTPException):
            await send_reply(t(guild, "MODM_MUTE_ERROR"))

    elif action_type == "unmute":
        try:
            await member.timeout(None, reason=f"Được gỡ cấm chat bởi {author} ({author.id}) | Lý do: {reason_str}")
            await interaction_or_ctx.channel.send(t(guild, "MODM_UNMUTE_MSG", mention=member.mention))
            await send_mod_log(
                guild, "Gỡ Cấm Chat (Unmute)", author,
                f"{member.mention} (`{member.id}`)", reason_str,
                discord.Color.green()
            )
            await send_reply(t(guild, "MODM_UNMUTE_SUCCESS"))
        except discord.HTTPException:
            await send_reply(t(guild, "MODM_UNMUTE_ERROR"))

    elif action_type == "kick":
        try:
            await notify_target_dm(member, guild, "Trục xuất khỏi máy chủ (Kick)", reason_str)
            await member.kick(reason=audit_reason)
            await interaction_or_ctx.channel.send(t(guild, "MODM_KICK_MSG", member=member, reason=reason_str))
            await send_mod_log(
                guild, "Trục Xuất (Kick)", author,
                f"{member} (`{member.id}`)", reason_str,
                discord.Color.red()
            )
            await send_reply(t(guild, "MODM_KICK_SUCCESS"))
        except discord.HTTPException:
            await send_reply(t(guild, "MODM_KICK_ERROR"))

    elif action_type == "ban":
        try:
            await notify_target_dm(member, guild, "Cấm vĩnh viễn (Ban)", reason_str)
            await member.ban(reason=audit_reason)
            await interaction_or_ctx.channel.send(t(guild, "MODM_BAN_MSG", member=member, reason=reason_str))
            await send_mod_log(
                guild, "Cấm Vĩnh Viễn (Ban)", author,
                f"{member} (`{member.id}`)", reason_str,
                discord.Color.dark_red()
            )
            await send_reply(t(guild, "MODM_BAN_SUCCESS"))
        except discord.HTTPException:
            await send_reply(t(guild, "MODM_BAN_ERROR"))


class ConfirmationView(discord.ui.View):
    def __init__(
        self,
        author: discord.Member,
        action_type: str,
        prefilled_user: str = "",
        guild: Optional[discord.Guild] = None,
        direct_member: Optional[discord.Member] = None,
        direct_reason: Optional[str] = None,
        direct_duration: Optional[str] = None
    ):
        super().__init__(timeout=30)
        self.author = author
        self.action_type = action_type
        self.prefilled_user = prefilled_user
        self.guild = guild
        self.direct_member = direct_member
        self.direct_reason = direct_reason
        self.direct_duration = direct_duration

        if guild:
            for child in self.children:
                if isinstance(child, discord.ui.Button):
                    if child.label == "ĐỒNG Ý VÀ TIẾP TỤC":
                        child.label = t(guild, "MODM_CONFIRM_YES")
                    elif child.label == "HỦY THAO TÁC":
                        child.label = t(guild, "MODM_CONFIRM_NO")

    @discord.ui.button(label="ĐỒNG Ý VÀ TIẾP TỤC", style=discord.ButtonStyle.green, emoji="✅")
    async def confirm(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user != self.author:
            return await interaction.response.send_message(t(interaction.guild, "MODM_CONFIRM_NO_PERM"), ephemeral=True)

        if self.direct_member is not None:
            if self.action_type == "mute" and not self.direct_duration:
                await interaction.response.send_modal(
                    PunishModal(action_type=self.action_type, prefilled_user=str(self.direct_member.id), guild=interaction.guild)
                )
                return
            await interaction.response.edit_message(content=t(interaction.guild, "MODM_CONFIRM_OPENING"), embed=None, view=None)
            reason = self.direct_reason or t(interaction.guild, "MODM_DEFAULT_REASON")
            await execute_punishment(interaction, self.direct_member, self.action_type, reason, self.direct_duration)
            return

        await interaction.response.send_modal(
            PunishModal(action_type=self.action_type, prefilled_user=self.prefilled_user, guild=interaction.guild)
        )

    @discord.ui.button(label="HỦY THAO TÁC", style=discord.ButtonStyle.danger, emoji="❌")
    async def cancel(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user != self.author:
            return await interaction.response.send_message(t(interaction.guild, "MODM_CONFIRM_NO_PERM"), ephemeral=True)

        await interaction.response.edit_message(content=t(interaction.guild, "MODM_CONFIRM_CANCELLED"), embed=None, view=None)


class ChannelResetConfirmView(discord.ui.View):
    def __init__(self, author: discord.Member, channel: discord.TextChannel):
        super().__init__(timeout=30)
        self.author = author
        self.channel = channel
        vi = is_vietnamese(channel.guild)
        self.confirm_reset.label = "Xác nhận làm mới kênh" if vi else "Confirm Reset Channel"
        self.cancel_reset.label = "Hủy thao tác" if vi else "Cancel" 

    @discord.ui.button(label="Xác nhận làm mới kênh", style=discord.ButtonStyle.danger, emoji="♻️")
    async def confirm_reset(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.author.id:
            return await interaction.response.send_message(t(interaction.guild, "MODM_CONFIRM_NO_PERM"), ephemeral=True)

        await interaction.response.defer(ephemeral=True)
        try:
            pos = self.channel.position
            cat = self.channel.category
            topic = getattr(self.channel, "topic", None)
            nsfw = getattr(self.channel, "nsfw", False)
            slowmode = getattr(self.channel, "slowmode_delay", 0)
            overwrites = self.channel.overwrites

            reset_reason = f"Channel reset by {interaction.user} ({interaction.user.id})"
            new_ch = await self.channel.clone(name=self.channel.name, reason=reset_reason)
            await new_ch.edit(
                category=cat,
                position=pos,
                topic=topic,
                nsfw=nsfw,
                slowmode_delay=slowmode,
                overwrites=overwrites
            )
            await self.channel.delete(reason=reset_reason)

            embed = discord.Embed(
                title="♻️ Kênh đã được làm mới sạch sẽ!",
                description=f"Toàn bộ lịch sử trò chuyện cũ đã được dọn sạch bởi {interaction.user.mention}.",
                color=discord.Color.green(),
                timestamp=discord.utils.utcnow()
            )
            await new_ch.send(embed=embed)
        except discord.Forbidden:
            await interaction.followup.send("❌ Bot không có đủ quyền **Quản lý Kênh (Manage Channels)**!", ephemeral=True)
        except Exception as e:
            await interaction.followup.send(f"❌ Lỗi khi làm mới kênh: `{e}`", ephemeral=True)

    @discord.ui.button(label="Hủy thao tác", style=discord.ButtonStyle.secondary, emoji="✖️")
    async def cancel_reset(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.author.id:
            return await interaction.response.send_message(t(interaction.guild, "MODM_CONFIRM_NO_PERM"), ephemeral=True)
        await interaction.response.edit_message(content="✅ Đã hủy thao tác làm mới kênh.", embed=None, view=None)


NukeConfirmView = ChannelResetConfirmView


class MemberListPaginatorView(discord.ui.View):
    def __init__(self, author: discord.User | discord.Member, chunks: list[str], guild: discord.Guild):
        super().__init__(timeout=180)
        self.author = author
        self.chunks = chunks
        self.guild = guild
        self.page = 0
        self.total_pages = len(chunks)
        self.message: Optional[discord.Message] = None
        self._update_buttons()

    def _update_buttons(self):
        vi = is_vietnamese(self.guild)
        self.prev_btn.disabled = (self.page == 0)
        self.next_btn.disabled = (self.page >= self.total_pages - 1)
        self.page_indicator.label = f"{'Trang' if vi else 'Page'} {self.page + 1}/{self.total_pages}"

    def get_embed(self) -> discord.Embed:
        embed = discord.Embed(
            title=t(self.guild, "MODM_MEMBERS_TITLE", cur=self.page + 1, total=self.total_pages),
            description=f"```{self.chunks[self.page]}```",
            color=discord.Color.blue()
        )
        embed.set_footer(text=f"Total: {self.guild.member_count or len(self.chunks)} members")
        return embed

    async def on_timeout(self):
        for item in self.children:
            if isinstance(item, (discord.ui.Button, discord.ui.Select)):
                item.disabled = True
        if self.message:
            try:
                await self.message.edit(view=self)
            except Exception:
                pass

    @discord.ui.button(label="◀ Trước", style=discord.ButtonStyle.secondary)
    async def prev_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.author.id:
            return await interaction.response.send_message(t(interaction.guild, "VIEW_OTHER_USER_DENIED"), ephemeral=True)
        if self.page > 0:
            self.page -= 1
            self._update_buttons()
            await interaction.response.edit_message(embed=self.get_embed(), view=self)

    @discord.ui.button(label="Trang 1/1", style=discord.ButtonStyle.secondary, disabled=True)
    async def page_indicator(self, interaction: discord.Interaction, button: discord.ui.Button):
        pass

    @discord.ui.button(label="Sau ▶", style=discord.ButtonStyle.primary)
    async def next_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.author.id:
            return await interaction.response.send_message(t(interaction.guild, "VIEW_OTHER_USER_DENIED"), ephemeral=True)
        if self.page < self.total_pages - 1:
            self.page += 1
            self._update_buttons()
            await interaction.response.edit_message(embed=self.get_embed(), view=self)


async def send_members_list(target: discord.Interaction | commands.Context):
    guild = target.guild
    author = target.user if isinstance(target, discord.Interaction) else target.author

    if (not getattr(guild, 'chunked', True) or len(guild.members) < (guild.member_count or 0)) and hasattr(guild, 'chunk'):
        try:
            await guild.chunk()
        except Exception:
            pass

    member_list = [f"{'🤖 Bot' if m.bot else '👤 User'} | {m.name} | ID: {m.id}" for m in guild.members]
    if not member_list:
        member_list = [f"👤 {author.name} | ID: {author.id}"]

    chunks, current_chunk = [], ""
    for line in member_list:
        if len(current_chunk) + len(line) > 1800:
            chunks.append(current_chunk)
            current_chunk = ""
        current_chunk += line + "\n"
    if current_chunk:
        chunks.append(current_chunk)

    if not chunks:
        chunks = ["Không có dữ liệu thành viên."]

    view = MemberListPaginatorView(author, chunks, guild)
    embed = view.get_embed()

    if isinstance(target, discord.Interaction):
        if target.response.is_done():
            msg = await target.followup.send(embed=embed, view=view, ephemeral=True)
            view.message = msg
        else:
            await target.response.send_message(embed=embed, view=view, ephemeral=True)
            try:
                view.message = await target.original_response()
            except Exception:
                pass
    else:
        msg = await target.send(embed=embed, view=view)
        view.message = msg


class ModControlView(discord.ui.View):
    def __init__(self, author: discord.Member, guild: Optional[discord.Guild] = None):
        super().__init__(timeout=180)
        self.author = author
        self.guild = guild

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user != self.author:
            await interaction.response.send_message(t(interaction.guild, "MODM_VIEW_NO_PERM"), ephemeral=True)
            return False
        return True

    @discord.ui.button(label="Clear Chat", style=discord.ButtonStyle.secondary, emoji="🗑️", row=0)
    async def btn_clear(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(ClearModal(guild=interaction.guild))

    @discord.ui.button(label="Warn User", style=discord.ButtonStyle.primary, emoji="⚠️", row=0)
    async def btn_warn(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(PunishModal(action_type="warn", guild=interaction.guild))

    @discord.ui.button(label="Mute User", style=discord.ButtonStyle.danger, emoji="🔇", row=0)
    async def btn_mute(self, interaction: discord.Interaction, button: discord.ui.Button):
        embed = discord.Embed(
            title=t(interaction.guild, "MODM_VIEW_MUTE_CONFIRM_TITLE"),
            description=t(interaction.guild, "MODM_VIEW_MUTE_CONFIRM_DESC"),
            color=discord.Color.dark_orange()
        )
        await interaction.response.send_message(
            embed=embed,
            view=ConfirmationView(self.author, "mute", guild=interaction.guild),
            ephemeral=True
        )

    @discord.ui.button(label="Unmute User", style=discord.ButtonStyle.success, emoji="🔊", row=0)
    async def btn_unmute(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(PunishModal(action_type="unmute", guild=interaction.guild))

    @discord.ui.button(label="Kick User", style=discord.ButtonStyle.danger, emoji="👢", row=1)
    async def btn_kick(self, interaction: discord.Interaction, button: discord.ui.Button):
        embed = discord.Embed(
            title=t(interaction.guild, "MODM_VIEW_MUTE_CONFIRM_TITLE"),
            description=t(interaction.guild, "MODM_VIEW_KICK_CONFIRM_DESC"),
            color=discord.Color.red()
        )
        await interaction.response.send_message(
            embed=embed,
            view=ConfirmationView(self.author, "kick", guild=interaction.guild),
            ephemeral=True
        )

    @discord.ui.button(label="Ban User", style=discord.ButtonStyle.danger, emoji="🔨", row=1)
    async def btn_ban(self, interaction: discord.Interaction, button: discord.ui.Button):
        embed = discord.Embed(
            title=t(interaction.guild, "MODM_VIEW_BAN_TITLE"),
            description=t(interaction.guild, "MODM_VIEW_BAN_DESC"),
            color=discord.Color.red()
        )
        await interaction.response.send_message(
            embed=embed,
            view=ConfirmationView(self.author, "ban", guild=interaction.guild),
            ephemeral=True
        )

    @discord.ui.button(label="Members List", style=discord.ButtonStyle.secondary, emoji="👥", row=1)
    async def btn_members(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer(ephemeral=True)
        await send_members_list(interaction)

    @discord.ui.button(label="Lock / Unlock Channel", style=discord.ButtonStyle.primary, emoji="🔒", row=2)
    async def btn_toggle_lock(self, interaction: discord.Interaction, button: discord.ui.Button):
        ch = interaction.channel
        if not isinstance(ch, discord.TextChannel):
            return await interaction.response.send_message("⚠️ Chỉ hỗ trợ khóa kênh văn bản!", ephemeral=True)

        if not interaction.guild.me.guild_permissions.manage_roles:
            return await interaction.response.send_message("❌ Bot cần quyền **Quản lý Vai trò (`Manage Roles`)** để thực hiện thao tác này!", ephemeral=True)

        default_role = interaction.guild.default_role
        overwrite = ch.overwrites_for(default_role)
        is_locked = overwrite.send_messages is False

        try:
            overwrite.send_messages = None if is_locked else False
            overwrite.create_public_threads = None if is_locked else False
            overwrite.create_private_threads = None if is_locked else False
            await ch.set_permissions(default_role, overwrite=overwrite, reason=f"Toggled lock by {interaction.user}")
            if is_locked:
                await interaction.response.send_message(f"🔓 Đã **mở khóa** kênh {ch.mention}!")
            else:
                await interaction.response.send_message(f"🔒 Đã **khóa** kênh {ch.mention} (Chặn `@everyone` gửi tin nhắn)!")
        except discord.Forbidden:
            await interaction.response.send_message("❌ Bot không có quyền **Quản lý Vai trò (Manage Roles)** trên kênh này!", ephemeral=True)
        except discord.HTTPException as e:
            await interaction.response.send_message(f"❌ Lỗi kết nối Discord: `{e}`", ephemeral=True)

    @discord.ui.button(label="Slowmode", style=discord.ButtonStyle.secondary, emoji="⏱️", row=2)
    async def btn_slowmode(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(SlowmodeModal())


class Manager(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_guild_remove(self, guild: discord.Guild):
        """Tự động dọn sạch dữ liệu cảnh cáo khi bot rời khỏi hoặc bị kick khỏi máy chủ (Tuân thủ Data Retention / Top.gg ToS)."""
        prefix = f"{guild.id}_"
        keys_to_delete = [k for k in warnings.keys() if k.startswith(prefix)]
        if keys_to_delete:
            for k in keys_to_delete:
                warnings.pop(k, None)
            save_warnings()

    async def _send_control_panel(self, ctx: commands.Context):
        embed = discord.Embed(
            title=t(ctx.guild, "MODM_PANEL_TITLE"),
            description=t(ctx.guild, "MODM_PANEL_DESC", prefix=ctx.prefix),
            color=discord.Color.dark_red(),
            timestamp=discord.utils.utcnow()
        )
        embed.set_thumbnail(url=ctx.guild.icon.url if ctx.guild.icon else ctx.author.display_avatar.url)
        embed.set_footer(text=t(ctx.guild, "MODM_PANEL_FOOTER", name=ctx.author.name), icon_url=ctx.author.display_avatar.url)

        view = ModControlView(ctx.author, ctx.guild)
        await ctx.send(embed=embed, view=view)

    @commands.hybrid_group(
        name="mod",
        aliases=["moderator", "admin"],
        description="🛡️ Hệ thống bảng điều khiển kiểm duyệt, quản lý kênh và cài đặt máy chủ."
    )
    @commands.guild_only()
    @has_admin_role()
    async def mod_group(self, ctx: commands.Context):
        await self._send_control_panel(ctx)

    @mod_group.command(name="panel", description="🎛️ Mở bảng điều khiển quản trị bằng nút bấm trực quan.")
    @has_admin_role()
    async def mod_panel(self, ctx: commands.Context):
        await self._send_control_panel(ctx)

    @mod_group.command(name="clear", aliases=["purge"], description="🗑️ Xóa tin nhắn hàng loạt (Hỗ trợ lọc riêng theo thành viên).")
    @app_commands.describe(
        amount="Số lượng tin nhắn cần xóa (ví dụ: 10, 50) hoặc nhập 'all'",
        member="Chỉ xóa tin nhắn của thành viên này (tùy chọn)"
    )
    @commands.has_permissions(manage_messages=True)
    @has_admin_role()
    async def mod_clear(
        self,
        ctx: commands.Context,
        amount: Optional[str] = None,
        member: Optional[discord.Member] = None
    ):
        if not amount:
            return await ctx.send(t(ctx.guild, "MODM_NEED_AMOUNT", prefix=ctx.prefix), ephemeral=True)

        if ctx.interaction:
            await ctx.interaction.response.defer(ephemeral=True)
        else:
            try:
                await ctx.message.delete()
            except (discord.Forbidden, discord.HTTPException):
                pass

        check_fn = (lambda m: m.author.id == member.id) if member else (lambda m: True)

        try:
            if amount.lower() == "all":
                deleted = await ctx.channel.purge(limit=1000, check=check_fn)
                reply_text = t(ctx.guild, "MODM_PURGE_ALL", count=len(deleted))
            else:
                num = int(amount)
                if num <= 0:
                    raise ValueError
                deleted = await ctx.channel.purge(limit=num, check=check_fn)
                reply_text = t(ctx.guild, "MODM_PURGE_SUCCESS", count=len(deleted))

            if ctx.interaction:
                await ctx.interaction.followup.send(reply_text, ephemeral=True)
            else:
                msg = await ctx.channel.send(reply_text)
                await msg.delete(delay=4)
        except ValueError:
            msg = t(ctx.guild, "MODM_CLEAR_INVALID")
            if ctx.interaction:
                await ctx.interaction.followup.send(msg, ephemeral=True)
            else:
                await ctx.send(msg, ephemeral=True)
        except discord.Forbidden:
            msg = "❌ Bot không có quyền **Quản lý tin nhắn (Manage Messages)**!"
            if ctx.interaction:
                await ctx.interaction.followup.send(msg, ephemeral=True)
            else:
                await ctx.send(msg, ephemeral=True)
        except discord.HTTPException as e:
            msg = "⚠️ Không thể xóa các tin nhắn cũ hơn 14 ngày (giới hạn Discord)!" if getattr(e, 'code', None) == 50034 else f"❌ Lỗi từ Discord khi xóa tin nhắn: `{e}`"
            if ctx.interaction:
                await ctx.interaction.followup.send(msg, ephemeral=True)
            else:
                await ctx.send(msg, ephemeral=True)

    @mod_group.command(name="warn", description="⚠️ Cảnh cáo một thành viên vi phạm.")
    @app_commands.describe(member="Thành viên cần cảnh cáo", reason="Lý do cảnh cáo")
    @has_admin_role()
    async def mod_warn(self, ctx: commands.Context, member: Optional[discord.Member] = None, *, reason: Optional[str] = None):
        if not member:
            return await ctx.send(t(ctx.guild, "MODM_SYNTAX_WARN", prefix=ctx.prefix), ephemeral=True)
        reason = reason or t(ctx.guild, "MODM_DEFAULT_REASON")
        await execute_punishment(ctx, member, "warn", reason)

    @mod_group.command(name="warnings", aliases=["warnlist", "warns"], description="📋 Xem lịch sử cảnh cáo của một thành viên.")
    @app_commands.describe(member="Thành viên cần kiểm tra lịch sử cảnh cáo")
    @has_admin_role()
    async def mod_warnings(self, ctx: commands.Context, member: discord.Member):
        guild_key = f"{ctx.guild.id}_{member.id}"
        user_warns = warnings.get(guild_key, [])

        if not user_warns:
            return await ctx.send(f"✅ Thành viên {member.mention} hiện không có bất kỳ cảnh cáo nào!", ephemeral=True)

        lines = []
        for idx, item in enumerate(user_warns, start=1):
            mod_id = item.get("by")
            reason_txt = item.get("reason", "Không rõ")
            time_iso = item.get("time", "")[:10]
            lines.append(f"**#{idx}** • `{time_iso}` — Bởi <@{mod_id}>\n└ Lý do: *{reason_txt}*")

        embed = discord.Embed(
            title=f"📋 Lịch sử cảnh cáo: {member.display_name} ({len(user_warns)} lần)",
            description="\n\n".join(lines)[:4000],
            color=discord.Color.yellow(),
            timestamp=discord.utils.utcnow()
        )
        embed.set_thumbnail(url=member.display_avatar.url)
        await ctx.send(embed=embed)

    @mod_group.command(name="unwarn", aliases=["clearwarn", "delwarn"], description="🧹 Xóa 1 cảnh cáo theo số thứ tự hoặc xóa toàn bộ cảnh cáo của thành viên.")
    @app_commands.describe(
        member="Thành viên cần xóa cảnh cáo",
        index="Số thứ tự cảnh cáo muốn xóa (Bỏ trống nếu muốn xóa sạch toàn bộ)"
    )
    @has_admin_role()
    async def mod_unwarn(self, ctx: commands.Context, member: discord.Member, index: Optional[int] = None):
        guild_key = f"{ctx.guild.id}_{member.id}"
        user_warns = warnings.get(guild_key, [])

        if not user_warns:
            return await ctx.send(f"ℹ️ Thành viên {member.mention} hiện không có cảnh cáo nào để xóa.", ephemeral=True)

        if index is None:
            count = len(user_warns)
            warnings.pop(guild_key, None)
            save_warnings()
            return await ctx.send(f"🧹 Đã xóa toàn bộ **{count}** cảnh cáo của {member.mention}!")

        if index < 1 or index > len(user_warns):
            return await ctx.send(f"⚠️ Số thứ tự không hợp lệ! Thành viên này đang có từ `#1` đến `#{len(user_warns)}`.", ephemeral=True)

        removed = user_warns.pop(index - 1)
        save_warnings()
        await ctx.send(f"✅ Đã xóa cảnh cáo **#{index}** (*{removed.get('reason')}*) của {member.mention}!")

    @mod_group.command(name="mute", aliases=["timeout"], description="🔇 Cấm chat (Timeout) một thành viên.")
    @app_commands.describe(member="Thành viên cần cấm chat", duration="Thời gian cấm chat (vd: 10m, 2h, 1d...)", reason="Lý do cấm chat")
    @has_admin_role()
    async def mod_mute(
        self,
        ctx: commands.Context,
        member: Optional[discord.Member] = None,
        duration: Optional[str] = None,
        *,
        reason: Optional[str] = None
    ):
        if not member or not duration:
            return await ctx.send(t(ctx.guild, "MODM_SYNTAX_MUTE", prefix=ctx.prefix), ephemeral=True)
        reason = reason or t(ctx.guild, "MODM_DEFAULT_REASON")
        await execute_punishment(ctx, member, "mute", reason, duration)

    @mod_group.command(name="unmute", aliases=["untimeout"], description="🔊 Gỡ cấm chat cho một thành viên.")
    @app_commands.describe(member="Thành viên cần gỡ cấm chat")
    @has_admin_role()
    async def mod_unmute(self, ctx: commands.Context, member: Optional[discord.Member] = None):
        if not member:
            return await ctx.send(t(ctx.guild, "MODM_SYNTAX_UNMUTE", prefix=ctx.prefix), ephemeral=True)
        await execute_punishment(ctx, member, "unmute", t(ctx.guild, "MODM_DEFAULT_REASON"))

    @mod_group.command(name="kick", description="👢 Trục xuất một thành viên khỏi máy chủ.")
    @app_commands.describe(member="Thành viên cần trục xuất", reason="Lý do trục xuất")
    @has_admin_role()
    async def mod_kick(self, ctx: commands.Context, member: Optional[discord.Member] = None, *, reason: Optional[str] = None):
        if not member:
            return await ctx.send(t(ctx.guild, "MODM_SYNTAX_KICK", prefix=ctx.prefix), ephemeral=True)
        reason = reason or t(ctx.guild, "MODM_DEFAULT_REASON")

        hierarchy_err = check_hierarchy(ctx.guild, ctx.author, member)
        if hierarchy_err:
            return await ctx.send(hierarchy_err, ephemeral=True)

        embed = discord.Embed(
            title=t(ctx.guild, "MODM_KICK_CONFIRM_TITLE"),
            description=t(ctx.guild, "MODM_KICK_CONFIRM_DESC", mention=member.mention),
            color=discord.Color.red()
        )
        view = ConfirmationView(ctx.author, "kick", guild=ctx.guild, direct_member=member, direct_reason=reason)
        await ctx.send(embed=embed, view=view)

    @mod_group.command(name="ban", description="🔨 Cấm vĩnh viễn một thành viên khỏi máy chủ.")
    @app_commands.describe(member="Thành viên cần cấm", reason="Lý do cấm")
    @has_admin_role()
    async def mod_ban(self, ctx: commands.Context, member: Optional[discord.Member] = None, *, reason: Optional[str] = None):
        if not member:
            return await ctx.send(t(ctx.guild, "MODM_SYNTAX_BAN", prefix=ctx.prefix), ephemeral=True)
        reason = reason or t(ctx.guild, "MODM_DEFAULT_REASON")

        hierarchy_err = check_hierarchy(ctx.guild, ctx.author, member)
        if hierarchy_err:
            return await ctx.send(hierarchy_err, ephemeral=True)

        embed = discord.Embed(
            title=t(ctx.guild, "MODM_BAN_CONFIRM_TITLE2"),
            description=t(ctx.guild, "MODM_BAN_CONFIRM_DESC2", mention=member.mention),
            color=discord.Color.red()
        )
        view = ConfirmationView(ctx.author, "ban", guild=ctx.guild, direct_member=member, direct_reason=reason)
        await ctx.send(embed=embed, view=view)

    @mod_group.command(name="unban", description="🔓 Gỡ lệnh cấm (Unban) cho người dùng bằng ID.")
    @app_commands.describe(user_id="Nhập ID của người dùng cần gỡ lệnh cấm", reason="Lý do gỡ cấm")
    @has_admin_role()
    async def mod_unban(self, ctx: commands.Context, user_id: str, *, reason: Optional[str] = None):
        clean_id = user_id.replace("<@", "").replace(">", "").replace("!", "").strip()
        try:
            uid = int(clean_id)
            user_obj = await self.bot.fetch_user(uid)
            await ctx.guild.unban(user_obj, reason=f"{reason or 'Unbanned'} (Bởi: {ctx.author} | ID: {ctx.author.id})")

            embed = discord.Embed(
                title="🔓 Đã gỡ lệnh cấm (Unban) thành công!",
                description=f"Người dùng **{user_obj}** (`{user_obj.id}`) đã có thể tham gia lại máy chủ.",
                color=discord.Color.green()
            )
            await ctx.send(embed=embed)
            await send_mod_log(
                ctx.guild, "Gỡ Cấm (Unban)", ctx.author,
                f"{user_obj} (`{user_obj.id}`)", reason or "Được gỡ cấm bởi Quản trị viên",
                discord.Color.green()
            )
        except ValueError:
            await ctx.send("⚠️ ID người dùng không hợp lệ!", ephemeral=True)
        except discord.NotFound:
            await ctx.send("⚠️ Không tìm thấy người dùng này trong danh sách đang bị Ban của máy chủ!", ephemeral=True)
        except discord.Forbidden:
            await ctx.send("❌ Bot không có quyền **Ban Members** để gỡ cấm!", ephemeral=True)

    @mod_group.command(
        name="channel",
        description="📺 Thay đổi nhanh các chức năng của kênh (Khóa, Ẩn, Slowmode, NSFW, Đổi tên, Nuke)."
    )
    @app_commands.describe(
        action="Chọn thao tác muốn thực hiện lên kênh",
        channel="Chọn kênh cần áp dụng (Bỏ trống sẽ áp dụng cho kênh hiện tại)",
        value="Giá trị đi kèm: Số giây (nếu chọn slowmode) hoặc Tên mới (nếu chọn rename)"
    )
    @has_admin_role()
    async def mod_channel(
        self,
        ctx: commands.Context,
        action: Literal["lock", "unlock", "hide", "unhide", "slowmode", "nsfw", "rename", "reset", "recreate", "nuke"],
        channel: Optional[discord.TextChannel] = None,
        *,
        value: Optional[str] = None
    ):
        target_ch = channel or ctx.channel
        if not isinstance(target_ch, discord.TextChannel):
            return await ctx.send("⚠️ Lệnh này chỉ áp dụng cho các kênh văn bản (Text Channel)!", ephemeral=True)

        act = action.lower()
        if act in ("lock", "unlock", "hide", "unhide"):
            if not ctx.guild.me.guild_permissions.manage_roles:
                return await ctx.send("❌ Bot cần quyền **Quản lý Vai trò (`Manage Roles`)** để thực hiện thao tác này!", ephemeral=True)
        else:
            if not ctx.guild.me.guild_permissions.manage_channels:
                return await ctx.send("❌ Bot cần quyền **Quản lý Kênh (`Manage Channels`)** để thực hiện thao tác này!", ephemeral=True)

        default_role = ctx.guild.default_role
        overwrite = target_ch.overwrites_for(default_role)

        try:
            if act == "lock":
                overwrite.send_messages = False
                overwrite.create_public_threads = False
                overwrite.create_private_threads = False
                await target_ch.set_permissions(default_role, overwrite=overwrite, reason=f"Locked by {ctx.author}")
                embed = discord.Embed(
                    title="🔒 Đã khóa kênh thành công",
                    description=f"Kênh {target_ch.mention} đã bị khóa đối với `@everyone`.",
                    color=discord.Color.red()
                )
                return await ctx.send(embed=embed)

            if act == "unlock":
                overwrite.send_messages = None
                overwrite.create_public_threads = None
                overwrite.create_private_threads = None
                await target_ch.set_permissions(default_role, overwrite=overwrite, reason=f"Channel unlocked by {ctx.author} ({ctx.author.id})")
                embed = discord.Embed(
                    title="🔓 Đã mở khóa kênh",
                    description=f"Thành viên đã có thể nhắn tin trở lại tại {target_ch.mention}.",
                    color=discord.Color.green()
                )
                return await ctx.send(embed=embed)

            if act == "hide":
                overwrite.view_channel = False
                await target_ch.set_permissions(default_role, overwrite=overwrite, reason=f"Channel hidden by {ctx.author} ({ctx.author.id})")
                return await ctx.send(f"🙈 Đã **ẩn** kênh {target_ch.mention} khỏi `@everyone`!")

            if act == "unhide":
                overwrite.view_channel = None
                await target_ch.set_permissions(default_role, overwrite=overwrite, reason=f"Channel unhidden by {ctx.author} ({ctx.author.id})")
                return await ctx.send(f"👁️ Đã **hiển thị** lại kênh {target_ch.mention} cho mọi người!")

            if act == "slowmode":
                seconds = 0
                if value:
                    try:
                        seconds = int(value.strip().lower().replace("s", ""))
                    except ValueError:
                        return await ctx.send("⚠️ Vui lòng nhập số giây hợp lệ từ `0` đến `21600` (6 giờ)!", ephemeral=True)
                if seconds < 0 or seconds > 21600:
                    return await ctx.send("⚠️ Thời gian Slowmode phải nằm trong khoảng `0` đến `21600` giây!", ephemeral=True)

                await target_ch.edit(slowmode_delay=seconds, reason=f"Slowmode changed by {ctx.author} ({ctx.author.id})")
                if seconds == 0:
                    return await ctx.send(f"✅ Đã **tắt** chế độ chậm (Slowmode) tại {target_ch.mention}!")
                return await ctx.send(f"⏱️ Đã đặt chế độ chậm tại {target_ch.mention} thành **{seconds} giây**!")

            if act == "nsfw":
                new_state = not target_ch.nsfw
                await target_ch.edit(nsfw=new_state, reason=f"NSFW toggled by {ctx.author} ({ctx.author.id})")
                status_str = "🔞 **BẬT**" if new_state else "✅ **TẮT**"
                return await ctx.send(f"Đã chuyển chế độ giới hạn độ tuổi (NSFW) của {target_ch.mention} sang: {status_str}!")

            if act == "rename":
                if not value or not value.strip():
                    return await ctx.send("⚠️ Vui lòng nhập **tên mới** vào ô `value` khi chọn `rename`!", ephemeral=True)
                old_name = target_ch.name
                await target_ch.edit(name=value.strip(), reason=f"Channel renamed by {ctx.author} ({ctx.author.id})")
                return await ctx.send(f"✏️ Đã đổi tên kênh từ `{old_name}` thành {target_ch.mention}!")

            if act in ("reset", "recreate", "nuke"):
                if not ctx.author.guild_permissions.administrator and ctx.author.id != ctx.guild.owner_id:
                    return await ctx.send(
                        "⛔ Thao tác làm mới kênh yêu cầu quyền **Administrator** hoặc **Chủ sở hữu máy chủ** để đảm bảo an toàn!",
                        ephemeral=True
                    )
                view = ChannelResetConfirmView(ctx.author, target_ch)
                return await ctx.send(
                    f"♻️ **XÁC NHẬN:** Bạn có chắc chắn muốn **Làm mới kênh (Clone & Xóa lịch sử cũ)** của kênh {target_ch.mention} không?\n*Thao tác này chỉ tái tạo kênh sạch sẽ, toàn bộ phân quyền vai trò và danh mục sẽ được giữ nguyên vẹn.*",
                    view=view,
                    ephemeral=True
                )

        except discord.Forbidden:
            needed_perm = "Quản lý Vai trò (Manage Roles)" if act in ("lock", "unlock", "hide", "unhide") else "Quản lý Kênh (Manage Channels)"
            await ctx.send(f"❌ Bot bị thiếu quyền hạn **{needed_perm}** trên kênh này để thực hiện thay đổi!", ephemeral=True)
        except discord.HTTPException as e:
            await ctx.send(f"❌ Lỗi kết nối Discord: `{e}`", ephemeral=True)

    @mod_group.command(
        name="server",
        description="🏠 Thay đổi cài đặt Máy chủ Discord hoặc Bật/Tắt các hệ thống của Bot trên Server."
    )
    @app_commands.describe(
        action="Chọn mục cài đặt Server cần xem hoặc thay đổi",
        value="Giá trị mới: on/off (tính năng), tên/mô tả, mức bảo mật (low/high), hoặc URL ảnh",
        attachment="Đính kèm file ảnh trực tiếp nếu muốn đổi Icon hoặc Banner cho Server"
    )
    @has_admin_role()
    async def mod_server(
        self,
        ctx: commands.Context,
        action: Literal[
            "status", "name", "description", "icon", "banner",
            "verification", "afk_timeout", "lockdown", "unlockdown",
            "automod", "leveling", "economy", "admin_only", "welcome", "goodbye", "mod_dm"
        ] = "status",
        value: Optional[str] = None,
        attachment: Optional[discord.Attachment] = None
    ):
        guild = ctx.guild
        act = action.lower()
        g_settings = get_guild_settings(guild.id)

        if act == "status":
            embed = discord.Embed(
                title=f"🏠 Bảng Cấu Hình Máy Chủ: {guild.name}",
                color=discord.Color.blurple(),
                timestamp=discord.utils.utcnow()
            )
            if guild.icon:
                embed.set_thumbnail(url=guild.icon.url)

            embed.add_field(
                name="⚙️ Cài đặt Discord của Server",
                value=(
                    f"• **Tên máy chủ:** `{guild.name}`\n"
                    f"• **Mức xác minh (Verification):** `{guild.verification_level.name.upper()}`\n"
                    f"• **Kênh AFK:** {guild.afk_channel.mention if guild.afk_channel else '`Không có`'} (`{guild.afk_timeout // 60} phút`)\n"
                    f"• **Cấp độ Boost:** `Cấp {guild.premium_tier}` ({guild.premium_subscription_count} Boosts)\n"
                    f"• **Mô tả:** {guild.description or '*(Chưa có mô tả)*'}"
                ),
                inline=False
            )

            def fmt_flag(flag: bool) -> str:
                return "🟢 `Đang Bật`" if flag else "🔴 `Đang Tắt`"

            embed.add_field(
                name="🤖 Trạng thái Tính năng Bot trên Server",
                value=(
                    f"• **Tự động kiểm duyệt (`automod`):** {fmt_flag(is_feature_enabled(guild.id, 'automod_enabled'))}\n"
                    f"• **Hệ thống Cấp độ (`leveling`):** {fmt_flag(is_feature_enabled(guild.id, 'leveling_enabled'))}\n"
                    f"• **Hệ thống Kinh tế (`economy`):** {fmt_flag(is_feature_enabled(guild.id, 'economy_enabled'))}\n"
                    f"• **Chỉ Admin dùng lệnh (`admin_only`):** {fmt_flag(is_admin_only(guild.id))}\n"
                    f"• **Chào mừng thành viên (`welcome`):** {fmt_flag(g_settings.get('welcome', True))}\n"
                    f"• **Tạm biệt thành viên (`goodbye`):** {fmt_flag(g_settings.get('goodbye', True))}\n"f"• **Gửi DM khi xử phạt (`mod_dm`):** {fmt_flag(is_feature_enabled(guild.id, 'mod_dm_notifications', default=True))}"
                ),
                inline=False
            )
            embed.set_footer(text=f"Mẹo: Dùng {ctx.prefix}mod server <tính_năng> <on/off> để bật hoặc tắt nhanh.")
            return await ctx.send(embed=embed)

        bot_features_map = {
            "automod": ("automod_enabled", "Tự động kiểm duyệt (AutoMod)"),
            "leveling": ("leveling_enabled", "Hệ thống Cấp độ (Leveling)"),
            "economy": ("economy_enabled", "Hệ thống Kinh tế (Economy)"),
            "admin_only": ("admin_only", "Chế độ Chỉ Admin dùng Bot (Admin Only)"),
            "mod_dm": ("mod_dm_notifications", "Gửi DM khi xử phạt (Mod DM Notifications)"),
        }

        if act in bot_features_map:
            cfg_key, label_vi = bot_features_map[act]
            current_state = is_admin_only(guild.id) if cfg_key == "admin_only" else is_feature_enabled(guild.id, cfg_key)

            if not value:
                new_state = not current_state
            elif value.lower() in ("on", "true", "bat", "1", "enable"):
                new_state = True
            elif value.lower() in ("off", "false", "tat", "0", "disable"):
                new_state = False
            else:
                return await ctx.send("⚠️ Giá trị `value` không hợp lệ! Hãy nhập `on` (Bật) hoặc `off` (Tắt).", ephemeral=True)

            save_server_config(guild.id, {cfg_key: new_state})
            state_str = "🟢 **BẬT**" if new_state else "🔴 **TẮT**"
            return await ctx.send(f"⚙️ Đã chuyển **{label_vi}** sang trạng thái: {state_str}!")

        if act in ("welcome", "goodbye", "mod_dm"):
            current_state = bool(g_settings.get(act, True))
            if not value:
                new_state = not current_state
            elif value.lower() in ("on", "true", "bat", "1", "enable"):
                new_state = True
            elif value.lower() in ("off", "false", "tat", "0", "disable"):
                new_state = False
            else:
                return await ctx.send("⚠️ Hãy nhập `on` (Bật) hoặc `off` (Tắt)!", ephemeral=True)

            g_settings[act] = new_state
            save_data()
            label_vi = "Tin nhắn Chào mừng (Welcome)" if act == "welcome" else "Tin nhắn Tạm biệt (Goodbye)"
            state_str = "🟢 **BẬT**" if new_state else "🔴 **TẮT**"
            return await ctx.send(f"⚙️ Đã chuyển **{label_vi}** sang trạng thái: {state_str}!")

        if act in ("lockdown", "unlockdown"):
            if not guild.me.guild_permissions.manage_roles:
                return await ctx.send("❌ Bot cần quyền **Quản lý Vai trò (`Manage Roles`)** để thực hiện lockdown máy chủ!", ephemeral=True)
        elif not guild.me.guild_permissions.manage_guild:
            return await ctx.send("❌ Bot cần quyền **Quản lý Máy chủ (`Manage Server`)** để thay đổi cài đặt này!", ephemeral=True)

        try:
            if act == "name":
                if not value or not value.strip():
                    return await ctx.send("⚠️ Vui lòng nhập **tên mới** cho máy chủ vào ô `value`!", ephemeral=True)
                old_name = guild.name
                await guild.edit(name=value.strip(), reason=f"Server renamed by {ctx.author} ({ctx.author.id})")
                return await ctx.send(f"🏠 Đã đổi tên máy chủ từ `{old_name}` thành **`{guild.name}`**!")

            if act == "description":
                new_desc = None if (not value or value.lower() in ("reset", "clear", "none")) else value.strip()
                await guild.edit(description=new_desc, reason=f"Description updated by {ctx.author} ({ctx.author.id})")
                return await ctx.send(f"📝 Đã cập nhật mô tả máy chủ thành: `{new_desc or 'Đã xóa mô tả'}`!")

            if act in ("icon", "banner"):
                img_url = attachment.url if attachment else (value.strip() if value else None)
                if not img_url:
                    return await ctx.send(f"⚠️ Vui lòng **đính kèm file ảnh** hoặc dán **URL ảnh** vào `value` để đổi `{act}`!", ephemeral=True)

                await ctx.defer()
                try:
                    async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=15)) as session:
                        async with session.get(img_url) as resp:
                            if resp.status != 200:
                                return await ctx.send("❌ Không thể tải hình ảnh từ đường dẫn đã cung cấp!", ephemeral=True)

                            content_type = resp.headers.get("Content-Type", "").lower()
                            if not any(t in content_type for t in ("image/png", "image/jpeg", "image/jpg", "image/gif", "image/webp")):
                                return await ctx.send("❌ Tệp không phải là định dạng hình ảnh hợp lệ (chỉ chấp nhận PNG, JPEG, GIF, WEBP)!", ephemeral=True)

                            content_length = resp.headers.get("Content-Length")
                            if content_length and int(content_length) > 10 * 1024 * 1024:
                                return await ctx.send("❌ Dung lượng ảnh vượt quá giới hạn cho phép (tối đa 10MB)!", ephemeral=True)

                            img_bytes = await resp.read()
                            if len(img_bytes) > 10 * 1024 * 1024:
                                return await ctx.send("❌ Dung lượng ảnh tải về vượt quá 10MB!", ephemeral=True)
                except Exception as e:
                    return await ctx.send(f"❌ Lỗi khi tải ảnh: `{e}`", ephemeral=True)

                admin_audit = f"{act.title()} changed by {ctx.author} ({ctx.author.id})"
                if act == "icon":
                    await guild.edit(icon=img_bytes, reason=admin_audit)
                    return await ctx.send("✅ Đã cập nhật **Ảnh đại diện (Icon)** mới cho máy chủ!")
                else:
                    if guild.premium_tier < 2 and "BANNER" not in guild.features:
                        return await ctx.send("⚠️ Máy chủ cần đạt **Boost Cấp 2** trở lên để cài đặt Ảnh bìa (Banner)!", ephemeral=True)
                    await guild.edit(banner=img_bytes, reason=admin_audit)
                    return await ctx.send("✅ Đã cập nhật **Ảnh bìa (Banner)** mới cho máy chủ!")

            if act == "verification":
                level_map = {
                    "none": discord.VerificationLevel.none,
                    "low": discord.VerificationLevel.low,
                    "medium": discord.VerificationLevel.medium,
                    "high": discord.VerificationLevel.high,
                    "highest": discord.VerificationLevel.highest,
                }
                if not value or value.lower() not in level_map:
                    return await ctx.send(
                        "⚠️ Vui lòng nhập mức xác minh hợp lệ vào `value`: `none`, `low`, `medium`, `high`, hoặc `highest`!",
                        ephemeral=True
                    )
                await guild.edit(verification_level=level_map[value.lower()], reason=f"Verification changed by {ctx.author}")
                return await ctx.send(f"🛡️ Đã đổi mức độ xác minh bảo mật của máy chủ thành: **`{value.upper()}`**!")

            if act == "afk_timeout":
                valid_timeouts = {60, 300, 900, 1800, 3600}
                try:
                    sec = int(value.strip().lower().replace("s", "")) if value else 0
                except ValueError:
                    sec = 0
                if sec not in valid_timeouts:
                    return await ctx.send("⚠️ Thời gian chờ AFK của Discord chỉ hỗ trợ các mốc: `60`, `300`, `900`, `1800`, hoặc `3600` (giây)!", ephemeral=True)
                await guild.edit(afk_timeout=sec, reason=f"AFK timeout changed by {ctx.author}")
                return await ctx.send(f"💤 Đã đặt thời gian chờ chuyển vào kênh AFK thành **{sec // 60} phút**!")

            if act in ("lockdown", "unlockdown"):
                if ctx.interaction and not ctx.interaction.response.is_done():
                    await ctx.interaction.response.defer()
                is_locking = (act == "lockdown")
                action_word = "khóa" if is_locking else "mở khóa"
                default_role = guild.default_role
                changed_count = 0
                skipped_perm_count = 0
                total_channels = len(guild.text_channels)

                extra_warning = f" (Máy chủ lớn gồm {total_channels} kênh, dự kiến mất ~{int(total_channels * 0.4)}s...)" if total_channels > 50 else ""
                start_msg_text = f"⏳ **Đang tiến hành {action_word} các kênh công khai, vui lòng đợi trong giây lát...**{extra_warning}"
                progress_msg = None
                if ctx.interaction:
                    progress_msg = await ctx.interaction.followup.send(start_msg_text)
                else:
                    progress_msg = await ctx.send(start_msg_text)

                for idx, ch in enumerate(guild.text_channels, 1):
                    if not ch.permissions_for(guild.me).manage_permissions:
                        skipped_perm_count += 1
                        continue

                    if ch.permissions_for(default_role).view_channel:
                        ow = ch.overwrites_for(default_role)
                        target_val = False if is_locking else None
                        if ow.send_messages != target_val:
                            ow.send_messages = target_val
                            try:
                                await ch.set_permissions(default_role, overwrite=ow, reason=f"Server {act} by {ctx.author} ({ctx.author.id})")
                                changed_count += 1
                                await asyncio.sleep(0.4)
                            except (discord.Forbidden, discord.HTTPException):
                                pass

                    if total_channels > 50 and idx % 15 == 0 and progress_msg:
                        try:
                            await progress_msg.edit(content=f"⏳ **Đang {action_word}... ({idx}/{total_channels} kênh)**")
                        except Exception:
                            pass

                skip_text = f" *(Bỏ qua {skipped_perm_count} kênh do bot thiếu quyền Quản lý Quyền hạn)*" if skipped_perm_count > 0 else ""
                final_text = (
                    f"🚨 **LOCKDOWN TOÀN MÁY CHỦ:** Đã khóa quyền nhắn tin của `@everyone` trên **{changed_count}** kênh công khai!{skip_text}"
                    if is_locking else
                    f"🔓 **MỞ KHÓA TOÀN MÁY CHỦ:** Đã khôi phục quyền nhắn tin trên **{changed_count}** kênh công khai!{skip_text}"
                )
                if progress_msg:
                    try:
                        return await progress_msg.edit(content=final_text)
                    except Exception:
                        pass
                return await ctx.send(final_text)

        except discord.Forbidden:
            await ctx.send("❌ Bot không có đủ quyền hạn để thay đổi cài đặt máy chủ này!", ephemeral=True)
        except discord.HTTPException as e:
            await ctx.send(f"❌ Lỗi từ Discord khi cập nhật máy chủ: `{e}`", ephemeral=True)


    @mod_group.command(
        name="purgedata",
        description="🛡️ Xóa sạch dữ liệu cảnh cáo của người dùng theo ID (Tuân thủ GDPR / Quyền riêng tư)."
    )
    @app_commands.describe(user_id="ID của người dùng cần xóa sạch dữ liệu khỏi hệ thống")
    @has_admin_role()
    async def mod_purge_data(self, ctx: commands.Context, user_id: str):
        clean_id = user_id.replace("<@", "").replace(">", "").replace("!", "").strip()
        guild_key = f"{ctx.guild.id}_{clean_id}"
        deleted_count = len(warnings.pop(guild_key, []))
        save_warnings()

        embed = discord.Embed(
            title="🛡️ Tuân Thủ Quyền Riêng Tư (GDPR / Data Privacy)",
            description=f"✅ Đã xóa sạch toàn bộ **{deleted_count}** bản ghi dữ liệu cảnh cáo liên quan đến User ID `{clean_id}` trên máy chủ này theo yêu cầu.",
            color=discord.Color.green(),
            timestamp=discord.utils.utcnow()
        )
        await ctx.send(embed=embed)
        await send_mod_log(
            ctx.guild, "Xóa Dữ Liệu Riêng Tư (GDPR Purge)", ctx.author,
            f"ID `{clean_id}`", f"Xóa dữ liệu người dùng tuân thủ GDPR bởi {ctx.author} ({ctx.author.id})",
            discord.Color.blue()
        )

    @mod_group.command(name="members", description="👥 Xem danh sách thành viên trong máy chủ.")
    @has_admin_role()
    async def mod_members(self, ctx: commands.Context):
        if ctx.interaction:
            await ctx.interaction.response.defer(ephemeral=True)
        await send_members_list(ctx.interaction if ctx.interaction else ctx)

    @mod_group.command(name="setlang", description="🌐 Cài đặt ngôn ngữ hiển thị cho bot trên máy chủ này.")
    @app_commands.describe(language="Chọn ngôn ngữ bạn muốn sử dụng (vi / en)")
    @has_admin_role()
    async def set_server_language_cmd(self, ctx: commands.Context, language: Literal["vi", "en"]):
        lang_names = {"vi": "Tiếng Việt 🇻🇳", "en": "English 🇬🇧"}
        lang_display = lang_names.get(language, language)

        set_guild_language(ctx.guild.id, language)

        embed = discord.Embed(
            title=t(ctx.guild, "MODM_LANG_SET_TITLE", name=lang_display),
            description=t(ctx.guild, "MODM_LANG_SET_DESC", name=lang_display),
            color=discord.Color.green()
        )
        await ctx.send(embed=embed)


async def setup(bot: commands.Bot):
    await bot.add_cog(Manager(bot))
