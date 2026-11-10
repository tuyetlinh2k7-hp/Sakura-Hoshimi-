import io
import asyncio
import discord
from discord.ext import commands
from Check.data import delete_log_channels
from Check.i18n import t


class ChatDeleteLog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.delete_queues: dict[int, list[dict]] = {}
        self.queue_tasks: dict[int, asyncio.Task] = {}
        self.QUEUE_DELAY = 4.0
        self.MAX_FILE_SIZE = 8 * 1024 * 1024

    def cog_unload(self):
        for task in self.queue_tasks.values():
            task.cancel()

    async def get_deleter(self, message: discord.Message) -> discord.abc.User | None:
        """Kiểm tra Audit Log để xác định ai đã xóa tin nhắn của người khác."""
        if not message.guild or not message.guild.me.guild_permissions.view_audit_log:
            return None

        await asyncio.sleep(1.0)
        now = discord.utils.utcnow()

        try:
            async for entry in message.guild.audit_logs(
                limit=5, action=discord.AuditLogAction.message_delete
            ):
                if (
                    entry.target
                    and entry.target.id == message.author.id
                    and entry.extra.channel.id == message.channel.id
                ):
                    if (now - entry.created_at).total_seconds() < 60:
                        return entry.user
        except (discord.Forbidden, discord.HTTPException):
            pass

        return None

    async def extract_attachments(self, message: discord.Message) -> list[discord.File]:
        """
        Tải ngay các tệp đính kèm từ proxy cache của Discord thành discord.File
        trước khi link CDN bị vô hiệu hóa sau khi xóa.
        """
        files = []
        for att in message.attachments[:5]:
            if att.size <= self.MAX_FILE_SIZE:
                try:
                    file_obj = await att.to_file(use_cached=True)
                    files.append(file_obj)
                except (discord.HTTPException, discord.NotFound):
                    pass
        return files

    @commands.Cog.listener()
    async def on_raw_message_delete(self, payload: discord.RawMessageDeleteEvent):
        if payload.guild_id is None:
            return

        guild_id = str(payload.guild_id)
        if guild_id not in delete_log_channels:
            return

        guild = self.bot.get_guild(payload.guild_id)
        if not guild:
            return

        log_channel = guild.get_channel(delete_log_channels[guild_id])
        if not log_channel:
            return

        message = payload.cached_message

        if message and message.author.bot:
            return

        saved_files = []
        deleter = None
        if message:
            saved_files, deleter = await asyncio.gather(
                self.extract_attachments(message),
                self.get_deleter(message)
            )

        channel_id = payload.channel_id
        if channel_id not in self.delete_queues:
            self.delete_queues[channel_id] = []

        self.delete_queues[channel_id].append({
            "cached": message is not None,
            "message": message,
            "message_id": payload.message_id,
            "channel_id": payload.channel_id,
            "deleter": deleter,
            "files": saved_files,
            "deleted_at": discord.utils.utcnow()
        })

        if channel_id in self.queue_tasks and not self.queue_tasks[channel_id].done():
            self.queue_tasks[channel_id].cancel()

        self.queue_tasks[channel_id] = asyncio.create_task(
            self._process_delete_queue(guild, log_channel, channel_id)
        )

    async def _process_delete_queue(
        self,
        guild: discord.Guild,
        log_channel: discord.TextChannel,
        channel_id: int
    ):
        try:
            await asyncio.sleep(self.QUEUE_DELAY)
        except asyncio.CancelledError:
            return

        items = self.delete_queues.pop(channel_id, [])
        self.queue_tasks.pop(channel_id, None)

        if not items:
            return

        if len(items) == 1:
            await self._send_single_delete_log(guild, log_channel, items[0])
        else:
            await self._send_grouped_delete_log(guild, log_channel, items)

    async def _send_single_delete_log(
        self,
        guild: discord.Guild,
        log_channel: discord.TextChannel,
        item: dict
    ):
        if not item["cached"]:
            embed = discord.Embed(
                title=t(guild, "LOG_DELETE_TITLE"),
                description=(
                    f"⚠️ **Tin nhắn cũ nằm ngoài bộ nhớ đệm vừa bị xóa.**\n"
                    f"• **Kênh:** <#{item['channel_id']}>\n"
                    f"• **ID Tin nhắn:** `{item['message_id']}`"
                ),
                color=discord.Color.dark_grey(),
                timestamp=item["deleted_at"]
            )
            try:
                await log_channel.send(embed=embed)
            except (discord.Forbidden, discord.HTTPException):
                pass
            return

        message: discord.Message = item["message"]
        deleter: discord.abc.User | None = item["deleter"]
        files: list[discord.File] = item["files"]

        embed = discord.Embed(
            title=t(guild, "LOG_DELETE_TITLE"),
            color=discord.Color.red(),
            timestamp=item["deleted_at"]
        )

        embed.set_author(
            name=f"{message.author} ({message.author.id})",
            icon_url=message.author.display_avatar.url
        )

        embed.add_field(
            name=t(guild, "LOG_DELETE_FIELD_USER"),
            value=f"{message.author.mention} (`{message.author.id}`)",
            inline=True
        )

        embed.add_field(
            name=t(guild, "LOG_DELETE_FIELD_CHANNEL"),
            value=message.channel.mention,
            inline=True
        )

        if deleter and deleter.id != message.author.id:
            deleter_str = f"{deleter.mention} (`{deleter.id}`)"
        else:
            deleter_str = t(guild, "LOG_CHAT_DEL_SELF_OR_UNKNOWN", mention=message.author.mention)

        embed.add_field(
            name=t(guild, "LOG_CHAT_FIELD_DELETER"),
            value=deleter_str,
            inline=False
        )

        if message.reference and message.reference.message_id:
            ref_url = f"https://discord.com/channels/{guild.id}/{message.channel.id}/{message.reference.message_id}"
            embed.add_field(
                name=t(guild, "LOG_CHAT_FIELD_REPLY"),
                value=f"[Nhấn để xem tin nhắn gốc (`{message.reference.message_id}`)]({ref_url})",
                inline=False
            )

        content = (
            message.content[:1000]
            if message.content
            else t(guild, "LOG_DELETE_NO_CONTENT")
        )
        embed.add_field(
            name=t(guild, "LOG_DELETE_FIELD_CONTENT"),
            value=content,
            inline=False
        )

        if message.stickers:
            sticker_info = "\n".join(
                [f"• **{s.name}** (`{s.id}`) - [Link ảnh]({s.url})" for s in message.stickers]
            )
            embed.add_field(
                name=t(guild, "LOG_CHAT_FIELD_STICKERS"),
                value=sticker_info[:1024],
                inline=False
            )
            if not files:
                embed.set_thumbnail(url=message.stickers[0].url)

        if message.attachments:
            att_lines = []
            for att in message.attachments[:5]:
                status = t(guild, "LOG_CHAT_ATT_REUPLOADED") if any(f.filename == att.filename for f in files) else t(guild, "LOG_CHAT_ATT_FALLBACK")
                att_lines.append(f"• [{att.filename}]({att.proxy_url}) ({status})")

            embed.add_field(
                name=t(guild, "LOG_CHAT_FIELD_ATTACHMENTS"),
                value="\n".join(att_lines)[:1024],
                inline=False
            )

            if files and files[0].filename.lower().endswith((".png", ".jpg", ".jpeg", ".gif", ".webp")):
                embed.set_image(url=f"attachment://{files[0].filename}")

        try:
            await log_channel.send(embed=embed, files=files if files else None)
        except (discord.Forbidden, discord.HTTPException):
            pass

    async def _send_grouped_delete_log(
        self,
        guild: discord.Guild,
        log_channel: discord.TextChannel,
        items: list[dict]
    ):
        """Gộp chung khi xóa nhiều tin nhắn liên tiếp trong thời gian ngắn."""
        channel_id = items[0]["channel_id"]

        embed = discord.Embed(
            title=t(guild, "LOG_DELETE_BULK_TITLE"),
            color=discord.Color.orange(),
            timestamp=discord.utils.utcnow()
        )

        embed.add_field(
            name=t(guild, "LOG_DELETE_BULK_FIELD_CHANNEL"),
            value=f"<#{channel_id}>",
            inline=True
        )

        embed.add_field(
            name=t(guild, "LOG_DELETE_BULK_FIELD_COUNT"),
            value=f"**{len(items)}**",
            inline=True
        )

        cached_items = [i for i in items if i["cached"]]
        uncached_count = len(items) - len(cached_items)

        users = {i["message"].author for i in cached_items if i["message"].author}
        embed.add_field(
            name=t(guild, "LOG_DELETE_BULK_FIELD_USERS"),
            value=f"{len(users)}" + (f" (+{uncached_count} tin cũ)" if uncached_count else ""),
            inline=True
        )

        deleters = {
            i["deleter"]
            for i in cached_items
            if i["deleter"] and i["deleter"].id != i["message"].author.id
        }
        if deleters:
            embed.add_field(
                name=t(guild, "LOG_CHAT_PURGE_MOD_FIELD"),
                value=", ".join(f"{d.mention} (`{d.id}`)" for d in deleters)[:1024],
                inline=False
            )

        preview = []
        current_length = 0

        for item in items[:10]:
            if not item["cached"]:
                entry = f"*(Tin nhắn ngoài bộ nhớ đệm - ID: `{item['message_id']}`)*"
            else:
                msg: discord.Message = item["message"]
                deleter: discord.abc.User | None = item["deleter"]

                content = msg.content or t(guild, "LOG_DELETE_BULK_NO_CONTENT")
                if len(content) > 65:
                    content = content[:62] + "..."

                extras = []
                if msg.reference:
                    extras.append("↩️Reply")
                if msg.stickers:
                    extras.append(f"🏷️Sticker: {msg.stickers[0].name}")
                if msg.attachments:
                    extras.append(f"📎{len(msg.attachments)} file")

                extra_str = f" `[{' | '.join(extras)}]`" if extras else ""
                by_mod = f" *(xóa bởi {deleter})*" if (deleter and deleter.id != msg.author.id) else ""

                entry = f"**{msg.author}** (`{msg.author.id}`){by_mod}{extra_str}\n{content}"

            if current_length + len(entry) + 2 > 1020:
                break

            preview.append(entry)
            current_length += len(entry) + 2

        if preview:
            embed.add_field(
                name=t(guild, "LOG_DELETE_BULK_FIELD_PREVIEW"),
                value="\n\n".join(preview),
                inline=False
            )

        if len(items) > len(preview):
            embed.set_footer(
                text=t(guild, "LOG_DELETE_BULK_FOOTER", remaining=len(items) - len(preview))
            )

        log_lines = []
        upload_files = []

        for item in items:
            if not item["cached"]:
                log_lines.append(f"[Uncached Message] ID: {item['message_id']} in Channel ID: {item['channel_id']}")
                continue

            msg: discord.Message = item["message"]
            deleter: discord.abc.User | None = item["deleter"]
            time_str = msg.created_at.strftime("%Y-%m-%d %H:%M:%S")
            deleter_info = f" [Deleted by: {deleter} ({deleter.id})]" if deleter else ""
            reply_info = f" [Reply to ID: {msg.reference.message_id}]" if (msg.reference and msg.reference.message_id) else ""
            sticker_info = f" | Stickers: {[s.name for s in msg.stickers]}" if msg.stickers else ""
            att_info = f" | Attachments: {[a.proxy_url for a in msg.attachments]}" if msg.attachments else ""
            msg_content = msg.content or "[No Content]"

            log_lines.append(
                f"[{time_str}] {msg.author} ({msg.author.id}){deleter_info}{reply_info}: "
                f"{msg_content}{sticker_info}{att_info}"
            )

            for f in item["files"]:
                if len(upload_files) < 9:
                    upload_files.append(f)

        log_txt = discord.File(
            fp=io.BytesIO("\n".join(log_lines).encode("utf-8")),
            filename=f"rapid_delete_{channel_id}.txt"
        )
        upload_files.insert(0, log_txt)

        try:
            await log_channel.send(embed=embed, files=upload_files)
        except (discord.Forbidden, discord.HTTPException):
            pass

    @commands.Cog.listener()
    async def on_bulk_message_delete(self, messages: list[discord.Message]):
        if not messages:
            return

        guild = messages[0].guild
        if guild is None:
            return

        guild_id = str(guild.id)
        if guild_id not in delete_log_channels:
            return

        log_channel = guild.get_channel(delete_log_channels[guild_id])
        if log_channel is None:
            return

        embed = discord.Embed(
            title=t(guild, "LOG_DELETE_BULK_TITLE"),
            color=discord.Color.red(),
            timestamp=discord.utils.utcnow()
        )

        embed.add_field(
            name=t(guild, "LOG_DELETE_BULK_FIELD_CHANNEL"),
            value=messages[0].channel.mention,
            inline=False
        )

        embed.add_field(
            name=t(guild, "LOG_DELETE_BULK_FIELD_COUNT"),
            value=f"**{len(messages)}**",
            inline=True
        )

        users = {msg.author for msg in messages if msg.author}
        embed.add_field(
            name=t(guild, "LOG_DELETE_BULK_FIELD_USERS"),
            value=str(len(users)),
            inline=True
        )

        preview = []
        current_length = 0

        for msg in messages[:10]:
            content = msg.content or t(guild, "LOG_DELETE_BULK_NO_CONTENT")
            if len(content) > 70:
                content = content[:67] + "..."

            extras = []
            if msg.reference:
                extras.append("↩️Reply")
            if msg.stickers:
                extras.append(f"🏷️{msg.stickers[0].name}")
            if msg.attachments:
                extras.append(f"📎{len(msg.attachments)} file")
            extra_str = f" `[{' | '.join(extras)}]`" if extras else ""

            entry = f"**{msg.author}** (`{msg.author.id}`){extra_str}\n{content}"

            if current_length + len(entry) + 2 > 1020:
                break

            preview.append(entry)
            current_length += len(entry) + 2

        if preview:
            embed.add_field(
                name=t(guild, "LOG_DELETE_BULK_FIELD_PREVIEW"),
                value="\n\n".join(preview),
                inline=False
            )

        if len(messages) > len(preview):
            embed.set_footer(
                text=t(guild, "LOG_DELETE_BULK_FOOTER", remaining=len(messages) - len(preview))
            )

        log_lines = []
        for msg in messages:
            time_str = msg.created_at.strftime("%Y-%m-%d %H:%M:%S")
            reply_info = f" [Reply to ID: {msg.reference.message_id}]" if (msg.reference and msg.reference.message_id) else ""
            sticker_info = f" | Stickers: {[s.name for s in msg.stickers]}" if msg.stickers else ""
            att_info = f" | Attachments: {[a.proxy_url for a in msg.attachments]}" if msg.attachments else ""
            msg_content = msg.content or "[No Content]"

            log_lines.append(
                f"[{time_str}] {msg.author} ({msg.author.id}){reply_info}: "
                f"{msg_content}{sticker_info}{att_info}"
            )

        log_file = discord.File(
            fp=io.BytesIO("\n".join(log_lines).encode("utf-8")),
            filename=f"bulk_delete_{messages[0].channel.id}.txt"
        )

        try:
            await log_channel.send(embed=embed, file=log_file)
        except (discord.Forbidden, discord.HTTPException):
            pass


async def setup(bot: commands.Bot):
    await bot.add_cog(ChatDeleteLog(bot))
