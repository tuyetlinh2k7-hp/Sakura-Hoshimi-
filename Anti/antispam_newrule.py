import discord
from discord.ext import commands
import datetime
import os
import json
import hashlib
from collections import defaultdict
import typing

CONFIG_FILE = "antispam_config.json"
SPAM_THRESHOLD_COUNT = 3
SPAM_INTERVAL_SECONDS = 10
MUTE_DURATION_MINUTES = 5
MAX_USER_MENTIONS = 4


class AntiSpam(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.user_message_history = defaultdict(lambda: defaultdict(list))
        self.config = self._load_config()

    def _load_config(self) -> dict:
        if os.path.exists(CONFIG_FILE):
            try:
                with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                return {}
        return {}

    def _save_config(self):
        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump(self.config, f, indent=4, ensure_ascii=False)

    def _get_guild_channels(self, guild_id: int):
        """Lấy ID kênh spam và kênh log (hỗ trợ tương thích ngược dữ liệu cũ)."""
        data = self.config.get(str(guild_id))
        if isinstance(data, dict):
            return data.get("spam_channel_id"), data.get("log_channel_id")
        elif isinstance(data, int):
            return data, None
        return None, None

    def _get_message_signature(self, message: discord.Message) -> str:
        """Tạo mã hash MD5 phân biệt nội dung (văn bản, tệp, stickers, role tags)."""
        components = []

        cleaned_text = message.content.strip().lower()
        if cleaned_text:
            components.append(f"text:{cleaned_text}")

        if message.attachments:
            att_signatures = sorted([f"{att.filename}_{att.size}" for att in message.attachments])
            components.append(f"attachments:{','.join(att_signatures)}")

        if message.stickers:
            sticker_ids = sorted([str(s.id) for s in message.stickers])
            components.append(f"stickers:{','.join(sticker_ids)}")

        if message.role_mentions:
            role_ids = sorted([str(r.id) for r in message.role_mentions])
            components.append(f"roles:{','.join(role_ids)}")

        combined = "|".join(components) if components else f"empty:{message.id}"
        return hashlib.md5(combined.encode("utf-8")).hexdigest()

    async def _send_dm(self, member: discord.Member, content: str):
        try:
            await member.send(content)
        except (discord.Forbidden, discord.HTTPException):
            pass

    @commands.command(name="setup_antispam")
    @commands.has_permissions(administrator=True)
    async def setup_antispam(
        self,
        ctx: commands.Context,
        spam_channel: typing.Optional[discord.TextChannel] = None,
        log_channel: typing.Optional[discord.TextChannel] = None
    ):
        """
        Thiết lập kênh cách ly spam và kênh lưu log xử phạt.
        Cú pháp:
          !setup_antispam #kênh-cách-ly #kênh-log
          !setup_antispam (tự động tạo kênh nếu không tag)
        """
        guild = ctx.guild
        created_spam = False
        created_log = False

        if not spam_channel:
            spam_channel = discord.utils.get(guild.text_channels, name="canh-bao-spam")
            if not spam_channel:
                overwrites = {
                    guild.default_role: discord.PermissionOverwrite(view_channel=True, send_messages=True),
                    guild.me: discord.PermissionOverwrite(
                        view_channel=True,
                        send_messages=True,
                        manage_messages=True,
                        embed_links=True
                    )
                }
                spam_channel = await guild.create_text_channel(
                    name="canh-bao-spam",
                    overwrites=overwrites,
                    topic="Khu vực cách ly spam. Mọi tin nhắn (user & bot) sẽ tự hủy sau 30 giây."
                )
                created_spam = True

        embed_warning = discord.Embed(
            title="🚫 KHU VỰC CÁCH LY & GIÁM SÁT SPAM",
            description=(
                "Kênh này dùng để thử nghiệm và cách ly các nội dung rác.\n\n"
                "**⚠️ NỘI QUY BẮT BUỘC:**\n"
                "• **KHÔNG** nhắn tin tán gẫu hoặc gửi bot commands vào đây.\n"
                "• Mọi tin nhắn (**cả người dùng lẫn Bot**) sẽ **tự hủy sau 30 giây**.\n"
                "• Cố tình spam liên tục tại kênh này vẫn bị **TIMEOUT 5 PHÚT** như bình thường."
            ),
            color=discord.Color.dark_red(),
            timestamp=datetime.datetime.now(datetime.timezone.utc)
        )
        embed_warning.set_footer(text="Hệ thống Anti-Spam • Giữ trật tự chung")

        try:
            pinned = await spam_channel.send(embed=embed_warning)
            await pinned.pin(reason="Ghim bảng nội quy phòng spam")

            async for sys_msg in spam_channel.history(limit=5):
                if sys_msg.type == discord.MessageType.pins_add:
                    await sys_msg.delete()
                    break
        except (discord.Forbidden, discord.HTTPException):
            pass

        if not log_channel:
            log_channel = discord.utils.get(guild.text_channels, name="log-xu-phat")
            if not log_channel:
                overwrites = {
                    guild.default_role: discord.PermissionOverwrite(view_channel=True, send_messages=False),
                    guild.me: discord.PermissionOverwrite(
                        view_channel=True,
                        send_messages=True,
                        embed_links=True
                    )
                }
                log_channel = await guild.create_text_channel(
                    name="log-xu-phat",
                    overwrites=overwrites,
                    topic="Nhật ký ghi nhận xử phạt và cảnh báo Anti-Spam."
                )
                created_log = True

        self.config[str(guild.id)] = {
            "spam_channel_id": spam_channel.id,
            "log_channel_id": log_channel.id
        }
        self._save_config()

        status_spam = "Đã tạo mới" if created_spam else "Đã liên kết"
        status_log = "Đã tạo mới" if created_log else "Đã liên kết"

        embed_success = discord.Embed(
            title="✅ Thiết Lập Hệ Thống Anti-Spam Thành Công",
            description=(
                f"• **Kênh cách ly spam:** {spam_channel.mention} `({status_spam})`\n"
                f"• **Kênh nhật ký phạt:** {log_channel.mention} `({status_log})`\n\n"
                "*(Tin nhắn tại kênh cách ly sẽ tự hủy sau 30s. Lịch sử phạt sẽ được lưu vĩnh viễn tại kênh log)*"
            ),
            color=discord.Color.green(),
            timestamp=datetime.datetime.now(datetime.timezone.utc)
        )
        await ctx.send(embed=embed_success)

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if not message.guild:
            return

        guild = message.guild
        member = message.author
        now = datetime.datetime.now(datetime.timezone.utc)
        spam_channel_id, log_channel_id = self._get_guild_channels(guild.id)

        if spam_channel_id and message.channel.id == spam_channel_id:
            if message.is_system() or message.pinned:
                return

            try:
                await message.delete(delay=30)
            except (discord.NotFound, discord.Forbidden, discord.HTTPException):
                pass

            if member.bot:
                return

        if member.bot:
            return

        user_records = self.user_message_history[guild.id][member.id]
        cutoff = now - datetime.timedelta(seconds=SPAM_INTERVAL_SECONDS)
        user_records[:] = [r for r in user_records if r["time"] > cutoff]

        has_mention_spam = (
            message.mention_everyone
            or len(message.role_mentions) >= 3
            or len(message.mentions) >= MAX_USER_MENTIONS
        )
        msg_sig = self._get_message_signature(message)

        user_records.append({
            "time": now,
            "sig": msg_sig,
            "msg": message,
            "is_mention": has_mention_spam
        })

        match_count = sum(1 for r in user_records if r["sig"] == msg_sig)
        mention_count = sum(1 for r in user_records if r["is_mention"])

        if match_count < SPAM_THRESHOLD_COUNT and mention_count < 2:
            return

        is_mod = (
            member.guild_permissions.manage_messages
            or member.guild_permissions.kick_members
            or member.guild_permissions.ban_members
            or member.guild_permissions.administrator
            or member.id == guild.owner_id
        )

        if match_count >= SPAM_THRESHOLD_COUNT:
            violating_messages = [r["msg"] for r in user_records if r["sig"] == msg_sig]
        else:
            violating_messages = [r["msg"] for r in user_records if r["is_mention"]]

        user_records.clear()

        for msg in violating_messages:
            try:
                await msg.delete()
            except (discord.NotFound, discord.Forbidden):
                pass

        target_log_channel = (
            guild.get_channel(log_channel_id) if log_channel_id else None
        ) or (
            guild.get_channel(spam_channel_id) if spam_channel_id else None
        )

        if is_mod:
            await self._send_dm(
                member,
                f"⚠️ **[CẢNH BÁO QUẢN TRỊ VIÊN]** Tại server **{guild.name}**:\n"
                f"Hệ thống phát hiện bạn gửi tin lặp lại liên tục hoặc lạm dụng Mention. "
                f"Các tin nhắn này đã được xóa tự động để bảo đảm trật tự."
            )
            if target_log_channel:
                await target_log_channel.send(
                    f"🛡️ **[Cảnh báo Mod]** Quản trị viên {member.mention} vừa bị dọn dẹp tin nhắn trùng lặp/spam tag."
                )
        else:
            timeout_success = False
            try:
                mute_time = datetime.timedelta(minutes=MUTE_DURATION_MINUTES)
                await member.timeout(mute_time, reason="Anti-Spam: Gửi tin nhắn trùng lặp hoặc lạm dụng Mention")
                timeout_success = True
            except (discord.Forbidden, discord.HTTPException):
                timeout_success = False

            if timeout_success:
                await self._send_dm(
                    member,
                    f"🚫 **[THÔNG BÁO XỬ PHẠT]** Bạn đã bị tạm khóa (timeout) **{MUTE_DURATION_MINUTES} phút** tại server **{guild.name}**.\n"
                    f"**Lý do:** Gửi tin nhắn trùng lặp nhiều lần hoặc liên tục tag @everyone/role/thành viên.\n"
                    f"Tin nhắn vi phạm đã được tự động dọn dẹp."
                )
            else:
                await self._send_dm(
                    member,
                    f"⚠️ **[CẢNH BÁO SPAM]** Tin nhắn spam của bạn tại server **{guild.name}** đã bị xóa tự động."
                )

            if target_log_channel:
                status_note = f"Đã timeout {MUTE_DURATION_MINUTES} phút" if timeout_success else "Không thể timeout (Bot thiếu quyền hoặc Role thấp hơn)"
                embed = discord.Embed(
                    title="🚨 Bắt Giữ & Xử Phạt Spam",
                    description=f"**Thành viên:** {member.mention} (`{member.id}`)\n"
                                f"**Trạng thái:** {status_note}\n"
                                f"**Hành động:** Đã xóa toàn bộ tin nhắn vi phạm.",
                    color=discord.Color.red() if timeout_success else discord.Color.orange(),
                    timestamp=datetime.datetime.now(datetime.timezone.utc)
                )
                embed.add_field(
                    name="Hành vi vi phạm",
                    value="Spam lặp lại nội dung" if match_count >= SPAM_THRESHOLD_COUNT else "Lạm dụng Mention (@everyone / Role / User)",
                    inline=False
                )
                await target_log_channel.send(embed=embed)


async def setup(bot: commands.Bot):
    await bot.add_cog(AntiSpam(bot))
