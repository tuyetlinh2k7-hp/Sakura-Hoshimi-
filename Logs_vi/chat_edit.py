import io
import asyncio
import difflib
from collections import OrderedDict
import discord
from discord.ext import commands
from Check.data import edit_log_channels
from Check.i18n import t


class JumpToMessageView(discord.ui.View):
    """Tạo nút bấm dẫn trực tiếp tới vị trí tin nhắn vừa bị chỉnh sửa."""
    def __init__(self, jump_url: str):
        super().__init__()
        self.add_item(
            discord.ui.Button(
                label="Jump to message",
                url=jump_url,
                style=discord.ButtonStyle.link,
                emoji="🔗"
            )
        )


class ChatEditLog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        # Quản lý hàng đợi chống spam sửa liên tiếp theo message_id
        self.edit_queues: dict[int, dict] = {}
        self.edit_tasks: dict[int, asyncio.Task] = {}
        self.EDIT_DELAY = 4.0
        self.MAX_FILE_SIZE = 8 * 1024 * 1024  # Giới hạn 8MB khi tải lại file bị gỡ

        # Bộ nhớ đệm phụ trợ lưu trạng thái tin nhắn để đối chiếu trong on_raw_message_edit
        # Giới hạn 5000 tin nhắn gần nhất để không tốn RAM
        self.local_cache: OrderedDict[int, dict] = OrderedDict()
        self.MAX_CACHE_SIZE = 5000

    def cog_unload(self):
        for task in self.edit_tasks.values():
            task.cancel()

    def _snapshot_message(self, message: discord.Message) -> dict:
        """Tạo bản chụp trạng thái của tin nhắn (nội dung + tệp đính kèm)."""
        return {
            "content": message.content or "",
            "attachments": list(message.attachments),
            "author": message.author,
            "channel_id": message.channel.id,
            "guild_id": message.guild.id if message.guild else None,
            "jump_url": message.jump_url
        }

    def _save_to_local_cache(self, message: discord.Message):
        if message.guild is None or message.author.bot:
            return
        self.local_cache[message.id] = self._snapshot_message(message)
        if len(self.local_cache) > self.MAX_CACHE_SIZE:
            self.local_cache.popitem(last=False)

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        """Lưu trạng thái gốc khi tin nhắn vừa được gửi."""
        self._save_to_local_cache(message)

    @commands.Cog.listener()
    async def on_message_edit(self, before: discord.Message, after: discord.Message):
        """
        Bắt sự kiện chỉnh sửa đối với tin nhắn đang nằm trong bộ nhớ đệm của discord.py.
        """
        if before.author.bot or before.guild is None:
            return

        guild_id = str(before.guild.id)
        if guild_id not in edit_log_channels:
            return

        log_channel = before.guild.get_channel(edit_log_channels[guild_id])
        if log_channel is None:
            return

        # Kiểm tra sự thay đổi về văn bản VÀ sự thay đổi về tệp đính kèm (gỡ ảnh/file)
        before_att_ids = {a.id for a in before.attachments}
        after_att_ids = {a.id for a in after.attachments}

        content_changed = before.content != after.content
        attachments_changed = before_att_ids != after_att_ids

        # Bỏ qua nếu không đổi chữ và cũng không gỡ file (ví dụ Discord tự nhúng link preview)
        if not content_changed and not attachments_changed:
            return

        # Cập nhật lại cache nội bộ
        self._save_to_local_cache(after)

        # Xác định các tệp đính kèm vừa bị người dùng gỡ bỏ trong lần sửa này
        removed_atts = [a for a in before.attachments if a.id not in after_att_ids]
        saved_files = await self._extract_removed_attachments(removed_atts)

        msg_id = before.id
        now = discord.utils.utcnow()

        if msg_id not in self.edit_queues:
            self.edit_queues[msg_id] = {
                "cached": True,
                "guild": before.guild,
                "channel_id": before.channel.id,
                "message_id": msg_id,
                "author": before.author,
                "jump_url": after.jump_url,
                "initial_content": before.content or "",
                "latest_content": after.content or "",
                "history": [before.content or "", after.content or ""],
                "removed_attachments": list(removed_atts),
                "saved_files": list(saved_files),
                "edit_count": 1,
                "last_edited_at": now
            }
        else:
            # Nếu người dùng tiếp tục sửa tin nhắn này khi đang trong thời gian chờ
            q = self.edit_queues[msg_id]
            q["latest_content"] = after.content or ""
            if not q["history"] or q["history"][-1] != (after.content or ""):
                q["history"].append(after.content or "")
            q["edit_count"] += 1
            q["last_edited_at"] = now

            # Gom thêm các file bị gỡ (nếu có)
            existing_att_ids = {a.id for a in q["removed_attachments"]}
            for a in removed_atts:
                if a.id not in existing_att_ids:
                    q["removed_attachments"].append(a)
            for f in saved_files:
                if len(q["saved_files"]) < 9:
                    q["saved_files"].append(f)

        # Reset bộ đếm Debounce 4 giây
        if msg_id in self.edit_tasks and not self.edit_tasks[msg_id].done():
            self.edit_tasks[msg_id].cancel()

        self.edit_tasks[msg_id] = asyncio.create_task(
            self._process_edit_queue(log_channel, msg_id)
        )

    @commands.Cog.listener()
    async def on_raw_message_edit(self, payload: discord.RawMessageUpdateEvent):
        """
        Xử lý trường hợp tin nhắn cũ nằm ngoài bộ nhớ đệm (Uncached) bị chỉnh sửa.
        (Nếu có cached_message thì on_message_edit ở trên đã tự động xử lý).
        """
        if payload.cached_message is not None or payload.guild_id is None:
            return

        guild_id = str(payload.guild_id)
        if guild_id not in edit_log_channels:
            return

        guild = self.bot.get_guild(payload.guild_id)
        if not guild:
            return

        log_channel = guild.get_channel(edit_log_channels[guild_id])
        if not log_channel:
            return

        data = payload.data
        # Bỏ qua nếu là sự kiện cập nhật embed tự động của Discord (không có trường content mới)
        if "content" not in data:
            return

        author_data = data.get("author", {})
        if author_data.get("bot", False):
            return

        new_content = data.get("content") or ""
        msg_id = payload.message_id
        channel_id = payload.channel_id
        jump_url = f"https://discord.com/channels/{guild.id}/{channel_id}/{msg_id}"

        # Tìm thông tin người gửi
        author_id = int(author_data.get("id", 0)) if author_data.get("id") else None
        author = guild.get_member(author_id) if author_id else None

        now = discord.utils.utcnow()

        if msg_id not in self.edit_queues:
            self.edit_queues[msg_id] = {
                "cached": False,
                "guild": guild,
                "channel_id": channel_id,
                "message_id": msg_id,
                "author": author,
                "author_data": author_data,
                "jump_url": jump_url,
                "initial_content": None,
                "latest_content": new_content,
                "history": [new_content],
                "removed_attachments": [],
                "saved_files": [],
                "edit_count": 1,
                "last_edited_at": now
            }
        else:
            q = self.edit_queues[msg_id]
            if q["latest_content"] == new_content:
                return
            q["latest_content"] = new_content
            q["history"].append(new_content)
            q["edit_count"] += 1
            q["last_edited_at"] = now

        if msg_id in self.edit_tasks and not self.edit_tasks[msg_id].done():
            self.edit_tasks[msg_id].cancel()

        self.edit_tasks[msg_id] = asyncio.create_task(
            self._process_edit_queue(log_channel, msg_id)
        )

    async def _extract_removed_attachments(self, attachments: list[discord.Attachment]) -> list[discord.File]:
        """Tải lại ngay các file vừa bị người dùng gỡ khỏi tin nhắn từ bộ nhớ đệm."""
        files = []
        for att in attachments[:5]:
            if att.size <= self.MAX_FILE_SIZE:
                try:
                    f = await att.to_file(use_cached=True)
                    files.append(f)
                except (discord.HTTPException, discord.NotFound):
                    pass
        return files

    def _generate_diff_text(self, before_text: str, after_text: str) -> str | None:
        """Tạo đoạn văn bản so sánh trực quan (Diff) giữa nội dung cũ và mới."""
        if not before_text or not after_text or before_text == after_text:
            return None

        before_lines = before_text.splitlines()
        after_lines = after_text.splitlines()

        diff = list(difflib.ndiff(before_lines, after_lines))
        changes = [line for line in diff if line.startswith(("- ", "+ "))]

        if not changes:
            return None

        diff_str = "\n".join(changes)
        if len(diff_str) > 950:
            diff_str = diff_str[:947] + "..."

        return f"```diff\n{diff_str}\n```"

    async def _process_edit_queue(self, log_channel: discord.TextChannel, msg_id: int):
        try:
            await asyncio.sleep(self.EDIT_DELAY)
        except asyncio.CancelledError:
            return

        item = self.edit_queues.pop(msg_id, None)
        self.edit_tasks.pop(msg_id, None)

        if not item:
            return

        # Nếu sau khi sửa qua lại mà nội dung cuối cùng quay về y hệt ban đầu và không mất file nào -> Bỏ qua
        if (
            item["cached"]
            and item["initial_content"] == item["latest_content"]
            and not item["removed_attachments"]
        ):
            return

        guild: discord.Guild = item["guild"]
        view = JumpToMessageView(item["jump_url"])

        # TRƯỜNG HỢP 1: Tin nhắn cũ ngoài bộ nhớ đệm (Uncached)
        if not item["cached"]:
            author = item["author"]
            a_data = item.get("author_data", {})
            author_mention = author.mention if author else f"<@{a_data.get('id', 'Unknown')}>"
            author_id = author.id if author else a_data.get("id", "Unknown")

            embed = discord.Embed(
                title=t(guild, "LOG_EDIT_TITLE"),
                description=t(guild, "LOG_CHAT_EDIT_UNCACHED_DESC"),
                color=discord.Color.orange(),
                timestamp=item["last_edited_at"]
            )

            if author:
                embed.set_author(
                    name=f"{author} ({author.id})",
                    icon_url=author.display_avatar.url
                )
                embed.set_thumbnail(url=author.display_avatar.url)

            embed.add_field(
                name=t(guild, "LOG_EDIT_FIELD_USER"),
                value=f"{author_mention} (`{author_id}`)",
                inline=True
            )
            embed.add_field(
                name=t(guild, "LOG_EDIT_FIELD_CHANNEL"),
                value=f"<#{item['channel_id']}>",
                inline=True
            )
            embed.add_field(
                name=t(guild, "LOG_EDIT_FIELD_MESSAGE_ID"),
                value=f"[`{msg_id}`]({item['jump_url']})",
                inline=True
            )
            embed.add_field(
                name=t(guild, "LOG_EDIT_FIELD_AFTER"),
                value=item["latest_content"][:1000] if item["latest_content"] else t(guild, "LOG_EDIT_NO_CONTENT"),
                inline=False
            )
            embed.set_footer(text=t(guild, "LOG_EDIT_FOOTER", id=author_id))

            try:
                await log_channel.send(embed=embed, view=view)
            except (discord.Forbidden, discord.HTTPException):
                pass
            return

        # TRƯỜNG HỢP 2: Tin nhắn nằm trong bộ nhớ đệm (Cached đầy đủ)
        author: discord.Member | discord.User = item["author"]
        before_text: str = item["initial_content"]
        after_text: str = item["latest_content"]
        edit_count: int = item["edit_count"]
        removed_atts: list[discord.Attachment] = item["removed_attachments"]
        upload_files: list[discord.File] = list(item["saved_files"])

        embed = discord.Embed(
            title=t(guild, "LOG_EDIT_TITLE"),
            color=discord.Color.orange(),
            timestamp=item["last_edited_at"]
        )

        embed.set_author(
            name=f"{author} ({author.id})",
            icon_url=author.display_avatar.url
        )
        embed.set_thumbnail(url=author.display_avatar.url)

        embed.add_field(
            name=t(guild, "LOG_EDIT_FIELD_USER"),
            value=f"{author.mention} (`{author.id}`)",
            inline=True
        )
        embed.add_field(
            name=t(guild, "LOG_EDIT_FIELD_CHANNEL"),
            value=f"<#{item['channel_id']}>",
            inline=True
        )
        embed.add_field(
            name=t(guild, "LOG_EDIT_FIELD_MESSAGE_ID"),
            value=f"[`{msg_id}`]({item['jump_url']})" + (f" *(Sửa {edit_count} lần)*" if edit_count > 1 else ""),
            inline=True
        )

        # Nếu cả nội dung cũ và mới đều ngắn (< 200 ký tự), đặt cạnh nhau (inline=True) để dễ nhìn
        is_short = len(before_text) < 200 and len(after_text) < 200

        embed.add_field(
            name=t(guild, "LOG_EDIT_FIELD_BEFORE"),
            value=before_text[:1000] if before_text else t(guild, "LOG_EDIT_NO_CONTENT"),
            inline=is_short
        )
        embed.add_field(
            name=t(guild, "LOG_EDIT_FIELD_AFTER"),
            value=after_text[:1000] if after_text else t(guild, "LOG_EDIT_NO_CONTENT"),
            inline=is_short
        )

        # Hiển thị khung Diff làm nổi bật thay đổi
        diff_block = self._generate_diff_text(before_text, after_text)
        if diff_block:
            embed.add_field(
                name=t(guild, "LOG_CHAT_DIFF_FIELD"),
                value=diff_block,
                inline=False
            )

        # Báo cáo các tệp đính kèm bị gỡ bỏ trong lúc sửa tin nhắn
        if removed_atts:
            att_lines = []
            for att in removed_atts[:5]:
                status = t(guild, "LOG_CHAT_ATT_REUPLOADED") if any(f.filename == att.filename for f in upload_files) else t(guild, "LOG_CHAT_ATT_FALLBACK")
                att_lines.append(f"• [{att.filename}]({att.proxy_url}) ({status})")

            embed.add_field(
                name=t(guild, "LOG_CHAT_REMOVED_ATT_FIELD"),
                value="\n".join(att_lines)[:1024],
                inline=False
            )

            if upload_files and upload_files[0].filename.lower().endswith((".png", ".jpg", ".jpeg", ".gif", ".webp")):
                embed.set_image(url=f"attachment://{upload_files[0].filename}")

        embed.set_footer(text=t(guild, "LOG_EDIT_FOOTER", id=author.id))

        # Xuất file .txt đính kèm nếu tin nhắn dài quá 1000 ký tự hoặc người dùng sửa liên tiếp nhiều lần
        if len(before_text) > 1000 or len(after_text) > 1000 or edit_count > 1:
            txt_lines = [
                f"=== LỊCH SỬ CHỈNH SỬA TIN NHẮN (ID: {msg_id}) ===",
                f"Người gửi: {author} ({author.id})",
                f"Kênh ID: {item['channel_id']}",
                f"Số lần sửa liên tiếp: {edit_count}",
                "=" * 50,
                "\n[NỘI DUNG GỐC BAN ĐẦU]:",
                before_text or "[Trống]",
            ]

            if edit_count > 1:
                for idx, step_text in enumerate(item["history"][1:-1], start=1):
                    txt_lines.append(f"\n--- [Lần sửa trung gian #{idx}] ---")
                    txt_lines.append(step_text or "[Trống]")

            txt_lines.append("\n[NỘI DUNG CUỐI CÙNG]:")
            txt_lines.append(after_text or "[Trống]")

            if removed_atts:
                txt_lines.append("\n[TỆP ĐÍNH KÈM BỊ GỠ BỎ]:")
                for a in removed_atts:
                    txt_lines.append(f"- {a.filename}: {a.proxy_url}")

            history_file = discord.File(
                fp=io.BytesIO("\n".join(txt_lines).encode("utf-8")),
                filename=f"edit_history_{msg_id}.txt"
            )
            upload_files.insert(0, history_file)

        try:
            await log_channel.send(
                embed=embed,
                files=upload_files[:10] if upload_files else None,
                view=view
            )
        except (discord.Forbidden, discord.HTTPException):
            pass


async def setup(bot: commands.Bot):
    await bot.add_cog(ChatEditLog(bot))
