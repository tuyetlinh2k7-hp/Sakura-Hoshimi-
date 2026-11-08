import asyncio
import json
import os
import re
import discord
from discord.ext import commands

from Checks_vi.i18n import t
from Checks_vi.mod import has_admin_role

GLOBAL_CHAT_FILE = "data/global_chat.json"
INVITE_REGEX = re.compile(r"(?:https?://)?(?:www\.)?(?:discord\.(?:gg|io|me|li)|discordapp\.com/invite|discord\.com/invite)/[a-zA-Z0-9-]+", re.IGNORECASE)


def load_global_chat_channels() -> set[int]:
    if os.path.exists(GLOBAL_CHAT_FILE):
        with open(GLOBAL_CHAT_FILE, "r", encoding="utf-8") as f:
            try:
                data = json.load(f)
                return set(data.get("channels", []))
            except json.JSONDecodeError:
                return set()
    return set()


def save_global_chat_channels(channels_set: set[int]) -> None:
    os.makedirs(os.path.dirname(GLOBAL_CHAT_FILE), exist_ok=True)
    with open(GLOBAL_CHAT_FILE, "w", encoding="utf-8") as f:
        json.dump({"channels": list(channels_set)}, f, indent=4)


class GlobalChatCog(commands.Cog, name="Global Chat"):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.global_channels: set[int] = load_global_chat_channels()
        # Cooldown chống spam: Tối đa 1 tin nhắn mỗi 2.5 giây cho mỗi người dùng
        self._cd = commands.CooldownMapping.from_cooldown(1, 2.5, commands.BucketType.user)

    def _extract_reply_info(self, replied_msg: discord.Message) -> tuple[str, str]:
        """Trích xuất tên tác giả và nội dung thực sự (hỗ trợ cả tin nhắn thường và Embed Global Chat)."""
        # Nếu reply lại chính tin nhắn Embed của bot trong Global Chat
        if replied_msg.author.id == self.bot.user.id and replied_msg.embeds:
            emb = replied_msg.embeds[0]
            author_name = emb.author.name.split(" (")[0] if emb.author and emb.author.name else replied_msg.author.display_name
            raw_desc = emb.description or ""
            # Loại bỏ phần quote cũ ở đầu description nếu có
            lines = [line for line in raw_desc.split("\n") if not line.startswith("> [**Trả lời")]
            clean_content = "\n".join(lines).strip()
            return author_name, clean_content

        return replied_msg.author.display_name, replied_msg.content

    async def _send_to_channel(self, channel_id: int, embed: discord.Embed, invalid_channels: set[int]) -> None:
        """Hàm phụ trợ gửi tin nhắn bất đồng bộ tới từng kênh."""
        try:
            target_channel = self.bot.get_channel(channel_id) or await self.bot.fetch_channel(channel_id)
            if isinstance(target_channel, discord.abc.Messageable):
                await target_channel.send(embed=embed)
        except (discord.NotFound, discord.Forbidden):
            print(f"Global Chat: Không thể gửi đến kênh {channel_id}. Sẽ thêm vào danh sách xóa.")
            invalid_channels.add(channel_id)
        except Exception as e:
            print(f"Lỗi khi gửi tin nhắn global chat đến kênh {channel_id}: {e}")

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        # 1. Bộ lọc cơ bản
        if message.author.bot or not message.guild:
            return
        if message.channel.id not in self.global_channels:
            return

        # 2. Bỏ qua nếu là lệnh của bot
        prefix = await self.bot.get_prefix(message)
        if isinstance(prefix, str) and message.content.startswith(prefix):
            return
        if isinstance(prefix, (list, tuple)) and any(message.content.startswith(p) for p in prefix):
            return

        # 3. Kiểm tra Cooldown chống spam
        bucket = self._cd.get_bucket(message)
        if bucket and bucket.update_rate_limit():
            try:
                await message.add_reaction("⏳")
            except discord.HTTPException:
                pass
            return

        # 4. Chặn link mời Discord
        if INVITE_REGEX.search(message.content):
            try:
                await message.delete()
                await message.channel.send(
                    f"⚠️ {message.author.mention}, không được phép gửi link mời máy chủ trên kênh Global Chat!",
                    delete_after=5
                )
            except discord.HTTPException:
                pass
            return

        content = message.content
        image_url = None

        # 5. Xử lý Sticker (Tránh lỗi với Lottie Sticker định dạng .json)
        if message.stickers:
            sticker = message.stickers[0]
            if sticker.format != discord.StickerFormatType.lottie:
                image_url = sticker.url
            if not content:
                content = f"*{message.author.display_name} đã gửi sticker **{sticker.name}**.*"

        # 6. Xử lý File đính kèm (An toàn với content_type = None)
        if message.attachments:
            first_att = message.attachments[0]
            if first_att.content_type and first_att.content_type.startswith("image/"):
                if not image_url:
                    image_url = first_att.url
            else:
                # Nếu đính kèm file không phải ảnh (video, tài liệu...)
                file_links = " | ".join(f"[📎 {att.filename}]({att.url})" for att in message.attachments)
                content = f"{content}\n{file_links}".strip()

        # Nếu tin nhắn hoàn toàn không có nội dung lẫn hình ảnh thì bỏ qua
        if not content and not image_url:
            return

        # 7. Xử lý Reply thông minh (Đọc được cả Embed của Global Chat)
        reply_text = ""
        if message.reference and isinstance(message.reference.resolved, discord.Message):
            replied_author, original_content = self._extract_reply_info(message.reference.resolved)
            if len(original_content) > 70:
                original_content = original_content[:67] + "..."
            display_quote = original_content if original_content else "*Tin nhắn chứa ảnh/sticker*"
            reply_text = f"> [**Trả lời {replied_author}:** {display_quote}]({message.reference.resolved.jump_url})\n\n"

        # 8. Khởi tạo Embed
        embed = discord.Embed(
            description=f"{reply_text}{content}",
            color=message.author.color if message.author.color != discord.Color.default() else discord.Color.blue(),
            timestamp=message.created_at
        )
        embed.set_author(
            name=f"{message.author.display_name} ({message.guild.name})",
            icon_url=message.author.display_avatar.url
        )
        embed.set_footer(
            text=f"Server ID: {message.guild.id} • User ID: {message.author.id}",
            icon_url=message.guild.icon.url if message.guild.icon else None
        )
        if image_url:
            embed.set_image(url=image_url)

        # 9. Phát tán tin nhắn đồng loạt tới các kênh bằng asyncio.gather
        channels_to_send = [cid for cid in self.global_channels if cid != message.channel.id]
        invalid_channels: set[int] = set()

        tasks = [self._send_to_channel(cid, embed, invalid_channels) for cid in channels_to_send]
        if tasks:
            await asyncio.gather(*tasks)

        # 10. Dọn dẹp các kênh không còn tồn tại hoặc mất quyền
        if invalid_channels:
            self.global_channels.difference_update(invalid_channels)
            save_global_chat_channels(self.global_channels)
            print(f"Global Chat: Đã xóa {len(invalid_channels)} kênh không hợp lệ.")

    @commands.hybrid_group(name="globalchat", aliases=["glc"], description="Thiết lập kênh chat toàn cầu.")
    @has_admin_role()
    async def globalchat(self, ctx: commands.Context):
        if ctx.invoked_subcommand is None:
            await ctx.send_help(ctx.command)

    @globalchat.command(name="set", description="Thiết lập kênh hiện tại làm kênh chat toàn cầu.")
    async def set_channel(self, ctx: commands.Context):
        if ctx.channel.id in self.global_channels:
            return await ctx.send(t(ctx.guild, "GLOBALCHAT_ALREADY", mention=ctx.channel.mention), ephemeral=True)

        # Gỡ kênh cũ trong cùng server (nếu có) để tránh 1 server có 2 kênh Global Chat
        for ch in ctx.guild.text_channels:
            if ch.id in self.global_channels:
                self.global_channels.discard(ch.id)

        self.global_channels.add(ctx.channel.id)
        save_global_chat_channels(self.global_channels)
        await ctx.send(t(ctx.guild, "GLOBALCHAT_CONNECTED", mention=ctx.channel.mention), ephemeral=True)

    @globalchat.command(name="unset", description="Gỡ bỏ kênh hiện tại khỏi hệ thống chat toàn cầu.")
    async def unset_channel(self, ctx: commands.Context):
        if ctx.channel.id not in self.global_channels:
            return await ctx.send(t(ctx.guild, "GLOBALCHAT_NOT_GLOBAL", mention=ctx.channel.mention), ephemeral=True)
        self.global_channels.discard(ctx.channel.id)
        save_global_chat_channels(self.global_channels)
        await ctx.send(t(ctx.guild, "GLOBALCHAT_DISCONNECTED", mention=ctx.channel.mention), ephemeral=True)


async def setup(bot: commands.Bot):
    await bot.add_cog(GlobalChatCog(bot))
