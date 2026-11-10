import asyncio
import base64
from collections import defaultdict, deque
import os
import time
from typing import Literal, Optional

import discord
from discord.ext import commands
from openai import AsyncOpenAI

from Check.i18n import t
from Check.mod import has_admin_role, is_owner

# --- CẤU HÌNH XKIRO API ---
API_KEY = None
try:
    from config import XKIRO_API_KEY as API_KEY
except ImportError:
    try:
        from config import GEMINI_API_KEY as API_KEY
    except ImportError:
        API_KEY = os.getenv("XKIRO_API_KEY") or os.getenv("GEMINI_API_KEY")

xkiro_client = AsyncOpenAI(
    base_url="https://api.xkiro.com/v1",
    api_key=API_KEY or "missing-api-key",
)

# Sử dụng model qua xKiro
try:
    from config import AI_MODEL as MODEL_NAME
except ImportError:
    MODEL_NAME = "sensenova/sensenova-6.8-flash-lite"

# --- CẤU HÌNH & QUẢN LÝ TRẠNG THÁI ---
GEMINI_SETTINGS_FILE = "data/gemini_settings.json"
active_ai_channels = set()
disabled_guilds = set()  
global_ai_enabled = True  

def load_gemini_settings():
    global active_ai_channels, disabled_guilds, global_ai_enabled
    if not os.path.exists(GEMINI_SETTINGS_FILE):
        return
    try:
        import json
        with open(GEMINI_SETTINGS_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
            active_ai_channels = set(data.get("active_ai_channels", []))
            disabled_guilds = set(data.get("disabled_guilds", []))
            global_ai_enabled = bool(data.get("global_ai_enabled", True))
    except Exception as e:
        print(f"[GeminiSettings] Lỗi nạp settings: {e}")

def save_gemini_settings():
    try:
        import json
        os.makedirs(os.path.dirname(GEMINI_SETTINGS_FILE), exist_ok=True)
        with open(GEMINI_SETTINGS_FILE, "w", encoding="utf-8") as f:
            json.dump({
                "active_ai_channels": list(active_ai_channels),
                "disabled_guilds": list(disabled_guilds),
                "global_ai_enabled": global_ai_enabled
            }, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"[GeminiSettings] Lỗi lưu settings: {e}")

load_gemini_settings()

conversation_histories: dict[int, deque] = {}

channel_locks: dict[int, asyncio.Lock] = defaultdict(asyncio.Lock)
last_message_timestamps: dict[int, float] = {}
CHANNEL_COOLDOWN_SECONDS = 1.5


def build_system_instruction(guild: discord.Guild) -> str:
    server_lang = getattr(guild, "preferred_locale", "vi")
    return f"""
Bạn là một thành viên thân thiết, vui tính và thông minh trong server Discord "{guild.name}".
Ngôn ngữ mặc định của server: {server_lang}.

Quy tắc ứng xử và phong cách:
1. Tính cách:
   - Nói chuyện như bạn bè trên Discord: tự nhiên, thoải mái, cởi mở, có cá tính và biết đùa.
   - Tuyệt đối TRÁNH phong cách chatbot dịch vụ/chăm sóc khách hàng (không mở đầu bằng "Tôi có thể giúp gì...", "Chào bạn...").
   - Xưng hô thân mật, phù hợp theo ngữ cảnh đối thoại (tớ - cậu, mình - bạn, ông - tôi,...).
   - Biết dùng tiếng lóng (slang), meme văn hóa mạng và emoji Discord một cách tự nhiên.
2. Ngôn ngữ & Đa phương thức:
   - Luôn phản hồi theo ngôn ngữ mà thành viên vừa dùng (tiếng Việt, tiếng Anh,...).
   - Khi thành viên gửi ảnh, hãy quan sát và bình luận, chém gió hoặc giải đáp nội dung trong ảnh một cách tự nhiên.
3. Độ dài phản hồi:
   - Giữ câu trả lời ngắn gọn, cô đọng (1-3 câu) giống thói quen chat Discord, trừ khi được yêu cầu giải thích sâu hoặc viết nội dung dài.
4. Thông tin cập nhật:
   - Phản hồi nhanh nhạy, tự nhiên với bối cảnh trò chuyện của nhóm.
"""


def split_message(text: str, limit: int = 1900) -> list[str]:
    chunks = []
    while len(text) > limit:
        split_index = text.rfind("\n", 0, limit)
        if split_index == -1:
            split_index = limit
        chunks.append(text[:split_index].strip())
        text = text[split_index:].strip()
    if text:
        chunks.append(text)
    return chunks


class GeminiConfigView(discord.ui.View):
    def __init__(self, author: discord.Member, channel_id: int):
        super().__init__(timeout=60)
        self.author = author
        self.channel_id = channel_id

    async def update_embed(self, interaction: discord.Interaction):
        is_active = self.channel_id in active_ai_channels
        status = "🟢 **Đang Bật**" if is_active else "🔴 **Đang Tắt**"
        color = discord.Color.green() if is_active else discord.Color.red()

        embed = discord.Embed(
            title="⚙️ Cài đặt Gemini AI Chat (xKiro)",
            description=f"Trạng thái tại kênh {interaction.channel.mention}: {status}\nModel: `{MODEL_NAME}`",
            color=color
        )
        embed.set_footer(
            text=f"Yêu cầu bởi {self.author.display_name}",
            icon_url=self.author.display_avatar.url
        )

        self.children[0].disabled = is_active
        self.children[1].disabled = not is_active

        await interaction.response.edit_message(embed=embed, view=self)

    @discord.ui.button(label="Bật AI Chat", style=discord.ButtonStyle.success, emoji="✅")
    async def turn_on(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user != self.author:
            return await interaction.response.send_message("Bạn không có quyền bấm nút này!", ephemeral=True)

        if self.channel_id not in active_ai_channels:
            active_ai_channels.add(self.channel_id)
            conversation_histories[self.channel_id] = deque(maxlen=12)
            save_gemini_settings()

        await self.update_embed(interaction)

    @discord.ui.button(label="Tắt AI Chat", style=discord.ButtonStyle.danger, emoji="❌")
    async def turn_off(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user != self.author:
            return await interaction.response.send_message("Bạn không có quyền bấm nút này!", ephemeral=True)

        if self.channel_id in active_ai_channels:
            active_ai_channels.remove(self.channel_id)
            conversation_histories.pop(self.channel_id, None)
            last_message_timestamps.pop(self.channel_id, None)
            save_gemini_settings()

        await self.update_embed(interaction)

    @discord.ui.button(label="Xóa Trí Nhớ", style=discord.ButtonStyle.secondary, emoji="🧹")
    async def clear_memory(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user != self.author:
            return await interaction.response.send_message("Bạn không có quyền bấm nút này!", ephemeral=True)

        if self.channel_id in conversation_histories:
            conversation_histories[self.channel_id].clear()
            await interaction.response.send_message("🧹 *Trí nhớ hội thoại của kênh đã được làm mới!*", ephemeral=True)
        else:
            await interaction.response.send_message("Kênh này chưa có lịch sử trò chuyện nào.", ephemeral=True)

    async def on_timeout(self):
        for item in self.children:
            item.disabled = True


class AIChatChannelCog(commands.Cog, name="AI Channel Chat"):
    """Cog quản lý phòng chat AI tự động sử dụng google/gemini-2.5-flash qua xKiro API."""

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    async def _generate_with_retry(
        self,
        messages: list[dict],
        max_retries: int = 4
    ) -> str:
        last_error = None

        for attempt in range(max_retries):
            try:
                response = await xkiro_client.chat.completions.create(
                    model=MODEL_NAME,
                    messages=messages,
                    temperature=0.85,
                    max_tokens=600,
                )
                if response.choices and response.choices[0].message.content:
                    return response.choices[0].message.content.strip()
                return "..."
            except Exception as e:
                last_error = e
                error_str = str(e).lower()
                status_code = getattr(e, "status_code", None)

                is_transient = (
                    status_code in (429, 500, 502, 503, 504)
                    or "503" in error_str
                    or "429" in error_str
                    or "overloaded" in error_str
                    or "unavailable" in error_str
                    or "rate limit" in error_str
                )

                if is_transient and attempt < max_retries - 1:
                    wait_time = 1.5 * (attempt + 1)
                    await asyncio.sleep(wait_time)
                    continue

                raise e

        if last_error is not None:
            raise last_error
        raise RuntimeError("Không thể tạo phản hồi từ AI.")

    @commands.group(name="gemini", invoke_without_command=True, description="Trò chuyện trực tiếp hoặc quản lý Gemini AI.")
    async def gemini(self, ctx: commands.Context, *, prompt: Optional[str] = None):
        """
        Dùng trực tiếp: `!gemini <nội dung>` (có thể đính kèm ảnh).
        Hoặc gõ không có nội dung để xem bảng điều khiển trạng thái.
        """
        if prompt or ctx.message.attachments:
            if not global_ai_enabled or ctx.guild.id in disabled_guilds:
                return await ctx.send("❌ Tính năng Gemini AI hiện đang bị tắt ở máy chủ này hoặc toàn cục.", ephemeral=True)

            user_content = []
            if prompt:
                user_content.append({
                    "type": "text",
                    "text": f"{ctx.author.display_name}: {prompt}"
                })

            valid_image_types = ("image/png", "image/jpeg", "image/webp", "image/gif")
            for attachment in ctx.message.attachments:
                if attachment.content_type in valid_image_types and attachment.size <= 8 * 1024 * 1024:
                    try:
                        img_bytes = await attachment.read()
                        b64_img = base64.b64encode(img_bytes).decode("utf-8")
                        user_content.append({
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:{attachment.content_type};base64,{b64_img}"
                            }
                        })
                    except Exception as err:
                        print(f"[GeminiCommand] Lỗi đọc ảnh: {err}")

            if not user_content:
                return await ctx.send("⚠️ Vui lòng nhập nội dung hoặc đính kèm hình ảnh để trò chuyện với Gemini!", delete_after=5)

            messages = [
                {"role": "system", "content": build_system_instruction(ctx.guild)},
                {"role": "user", "content": user_content}
            ]

            async with ctx.typing():
                try:
                    ai_reply = await self._generate_with_retry(messages=messages)
                    chunks = split_message(ai_reply)
                    for index, chunk in enumerate(chunks):
                        if index == 0:
                            await ctx.reply(chunk, mention_author=False)
                        else:
                            await ctx.send(chunk)
                except Exception as e:
                    print(f"[GeminiCommand] Lỗi xKiro API: {e}")
                    await ctx.send("😅 *Tớ đang hơi quá tải một xíu, lát nữa thử lại nha!*")
            return

        # Bảng trạng thái khi chỉ gõ `!gemini`
        is_active = ctx.channel.id in active_ai_channels
        server_disabled = ctx.guild.id in disabled_guilds
        
        status = "🔴 **Đang Tắt**" if server_disabled else ("🟢 **Đang Bật (Kênh này)**" if is_active else "🟡 **Sẵn sàng**")
        global_status = "🟢 Đang Bật" if global_ai_enabled else "🔴 Đang Tắt"

        embed = discord.Embed(
            title="✨ Gemini AI Chat Control Panel (xKiro)",
            description=(
                f"Model: `{MODEL_NAME}`\n"
                f"Trạng thái server: {status}\n"
                f"Trạng thái toàn cục: {global_status}"
            ),
            color=discord.Color.blue()
        )
        embed.add_field(
            name="Cách sử dụng",
            value=(
                f"• **Chat trực tiếp:** `{ctx.prefix}gemini <nội dung>` (hỗ trợ kèm ảnh)\n"
                f"• **Bật chat tự động kênh:** `{ctx.prefix}gemini on`\n"
                f"• **Tắt chat tự động kênh:** `{ctx.prefix}gemini off`\n"
                f"• **Bật/tắt server:** `{ctx.prefix}gemini server on/off` (Admin)\n"
                f"• **Bật/tắt toàn cục:** `{ctx.prefix}gemini global on/off` (Owner)\n"
                f"• **Xóa trí nhớ kênh:** `{ctx.prefix}gemini clear`\n"
                f"• **Bảng nút bấm:** `{ctx.prefix}gemini config`"
            ),
            inline=False
        )
        await ctx.send(embed=embed)

    @gemini.command(name="on", description="Bật chế độ AI tự động chat tại kênh hiện tại.")
    @has_admin_role()
    async def gemini_on(self, ctx: commands.Context):
        if ctx.guild.id in disabled_guilds:
            return await ctx.send("❌ Máy chủ này hiện đang bị tắt hoàn toàn tính năng Gemini AI bởi quản trị viên!", ephemeral=True)

        if ctx.channel.id in active_ai_channels:
            return await ctx.send("⚠️ Kênh này đã được bật Gemini AI từ trước rồi ạ!", ephemeral=True)

        active_ai_channels.add(ctx.channel.id)
        conversation_histories[ctx.channel.id] = deque(maxlen=12)
        save_gemini_settings()
        await ctx.send(f"✅ Đã bật tính năng Gemini AI (`{MODEL_NAME}`) chat tự động cho kênh này!")

    @gemini.command(name="off", description="Tắt chế độ AI tự động chat tại kênh hiện tại.")
    @has_admin_role()
    async def gemini_off(self, ctx: commands.Context):
        if ctx.channel.id not in active_ai_channels:
            return await ctx.send("⚠️ Kênh này hiện chưa bật Gemini AI.", ephemeral=True)

        active_ai_channels.remove(ctx.channel.id)
        conversation_histories.pop(ctx.channel.id, None)
        last_message_timestamps.pop(ctx.channel.id, None)
        save_gemini_settings()
        await ctx.send("🔴 Đã tắt tính năng Gemini AI chat cho kênh này.")

    @gemini.command(name="server", description="Bật hoặc tắt toàn bộ tính năng Gemini AI của server này.")
    @has_admin_role()
    async def gemini_server(self, ctx: commands.Context, status: Literal["on", "off"]):
        if status.lower() == "on":
            if ctx.guild.id in disabled_guilds:
                disabled_guilds.remove(ctx.guild.id)
            save_gemini_settings()
            await ctx.send(f"✅ Đã **BẬT** toàn bộ tính năng Gemini AI cho server `{ctx.guild.name}`.")
        else:
            disabled_guilds.add(ctx.guild.id)
            save_gemini_settings()
            await ctx.send(f"🔴 Đã **TẮT** hoàn toàn tính năng Gemini AI cho server `{ctx.guild.name}`.")

    @gemini.command(name="global", description="[Owner] Bật hoặc tắt tính năng Gemini AI trên toàn bộ hệ thống bot.")
    @is_owner()
    async def gemini_global(self, ctx: commands.Context, status: Literal["on", "off"]):
        global global_ai_enabled
        global_ai_enabled = (status.lower() == "on")
        save_gemini_settings()
        state_text = "BẬT" if global_ai_enabled else "TẮT"
        await ctx.send(f"✅ [Toàn cục] Đã chuyển trạng thái hệ thống Gemini AI sang **{state_text}**.", ephemeral=True)

    @gemini.command(name="clear", description="Xóa trí nhớ hội thoại của kênh hiện tại.")
    @has_admin_role()
    async def gemini_clear(self, ctx: commands.Context):
        if ctx.channel.id in conversation_histories:
            conversation_histories[ctx.channel.id].clear()
            await ctx.send("🧹 *Trí nhớ của kênh đã được đặt lại thành công!*")
        else:
            await ctx.send("Kênh này chưa có dữ liệu lịch sử nào cần xóa.", ephemeral=True)

    @gemini.command(name="config", description="Mở bảng điều khiển cài đặt giao diện nút bấm cho kênh.")
    @has_admin_role()
    async def gemini_config(self, ctx: commands.Context):
        is_active = ctx.channel.id in active_ai_channels
        status = "🟢 **Đang Bật**" if is_active else "🔴 **Đang Tắt**"
        color = discord.Color.green() if is_active else discord.Color.red()

        embed = discord.Embed(
            title="⚙️ Cài đặt Gemini AI Chat (xKiro)",
            description=f"Trạng thái tại kênh {ctx.channel.mention}: {status}\nModel: `{MODEL_NAME}`",
            color=color
        )
        embed.set_footer(text=f"Yêu cầu bởi {ctx.author.display_name}", icon_url=ctx.author.display_avatar.url)

        view = GeminiConfigView(ctx.author, ctx.channel.id)
        view.children[0].disabled = is_active
        view.children[1].disabled = not is_active

        await ctx.send(embed=embed, view=view)

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if message.author.bot or not message.guild:
            return

        if not global_ai_enabled or message.guild.id in disabled_guilds:
            return

        prefix = await self.bot.get_prefix(message)
        if isinstance(prefix, (list, tuple)):
            if any(message.content.startswith(p) for p in prefix if p):
                return
        elif isinstance(prefix, str) and prefix and message.content.startswith(prefix):
            return

        if message.channel.id not in active_ai_channels:
            return

        async with channel_locks[message.channel.id]:
            now = time.time()
            last_time = last_message_timestamps.get(message.channel.id, 0.0)
            if now - last_time < CHANNEL_COOLDOWN_SECONDS:
                await asyncio.sleep(CHANNEL_COOLDOWN_SECONDS - (now - last_time))
            last_message_timestamps[message.channel.id] = time.time()

            reply_context = ""
            if message.reference and message.reference.message_id:
                try:
                    ref_msg = await message.channel.fetch_message(message.reference.message_id)
                    if ref_msg and ref_msg.content:
                        clean_ref = ref_msg.clean_content.replace("\n", " ")
                        reply_context = f"[Đang trả lời {ref_msg.author.display_name}: \"{clean_ref[:150]}\"]\n"
                except (discord.NotFound, discord.HTTPException):
                    pass

            user_content = []
            author_text = f"{reply_context}{message.author.display_name}: {message.clean_content}".strip()
            if author_text:
                user_content.append({
                    "type": "text",
                    "text": author_text
                })

            valid_image_types = ("image/png", "image/jpeg", "image/webp", "image/gif")
            image_count = 0
            for attachment in message.attachments:
                if attachment.content_type in valid_image_types and attachment.size <= 8 * 1024 * 1024:
                    try:
                        img_bytes = await attachment.read()
                        b64_img = base64.b64encode(img_bytes).decode("utf-8")
                        user_content.append({
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:{attachment.content_type};base64,{b64_img}"
                            }
                        })
                        image_count += 1
                    except Exception as err:
                        print(f"[GeminiChat] Lỗi khi đọc file ảnh: {err}")

            if not user_content:
                return

            history = conversation_histories.setdefault(message.channel.id, deque(maxlen=12))
            
            request_messages = [{"role": "system", "content": build_system_instruction(message.guild)}]
            request_messages.extend(list(history))
            request_messages.append({"role": "user", "content": user_content})

            try:
                async with message.channel.typing():
                    ai_reply = await self._generate_with_retry(messages=request_messages)

                history_user_text = author_text
                if image_count > 0:
                    history_user_text = f"{author_text} [Đã gửi {image_count} hình ảnh]".strip()

                history.append({"role": "user", "content": history_user_text})
                history.append({"role": "assistant", "content": ai_reply})

                chunks = split_message(ai_reply)
                for index, chunk in enumerate(chunks):
                    if index == 0:
                        await message.reply(chunk, mention_author=False)
                    else:
                        await message.channel.send(chunk)

            except Exception as e:
                print(f"[GeminiChat] Lỗi xử lý xKiro API: {e}")
                await message.channel.send("😅 *Tớ đang hơi quá tải một xíu, lát nữa tụi mình nói tiếp nha!*")


async def setup(bot: commands.Bot):
    await bot.add_cog(AIChatChannelCog(bot))
