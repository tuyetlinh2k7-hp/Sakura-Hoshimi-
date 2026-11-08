from Checks_vi.i18n import t, is_vietnamese
import io
import os
import asyncio
import aiosqlite
import discord
from discord import app_commands
from discord.ext import commands
from deep_translator import GoogleTranslator
from openai import AsyncOpenAI

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
    api_key=API_KEY or "missing-api-key",
    base_url="https://api.xkiro.com/v1",
)

try:
    from config import AI_MODEL
except ImportError:
    AI_MODEL = "sensenova/sensenova-6.8-flash-lite"

# Ánh xạ Emoji cờ -> Ngôn ngữ đích
FLAG_TO_LANG = {
    "🇻🇳": {"name": "Tiếng Việt", "target": "Vietnamese", "iso": "vi"},
    "🇺🇸": {"name": "Tiếng Anh", "target": "English", "iso": "en"},
    "🇬🇧": {"name": "Tiếng Anh", "target": "English", "iso": "en"},
    "🇯🇵": {"name": "Tiếng Nhật", "target": "Japanese", "iso": "ja"},
    "🇨🇳": {"name": "Tiếng Trung", "target": "Simplified Chinese", "iso": "zh-CN"},
    "🇰🇷": {"name": "Tiếng Hàn", "target": "Korean", "iso": "ko"},
    "🇫🇷": {"name": "Tiếng Pháp", "target": "French", "iso": "fr"},
    "🇩🇪": {"name": "Tiếng Đức", "target": "German", "iso": "de"},
    "🇷🇺": {"name": "Tiếng Nga", "target": "Russian", "iso": "ru"},
    "🇹🇭": {"name": "Tiếng Thái", "target": "Thai", "iso": "th"},
    "🇪🇸": {"name": "Tiếng Tây Ban Nha", "target": "Spanish", "iso": "es"}
}

DB_PATH = "data/server_glossary.db"


class DeleteMessageView(discord.ui.View):
    """View chứa nút bấm xóa tin nhắn dịch nhanh"""
    def __init__(self, requester_id: int, guild=None):
        super().__init__(timeout=120)
        self.requester_id = requester_id
        vi = is_vietnamese(guild)
        self.delete_btn.label = "Xóa" if vi else "Delete"

    @discord.ui.button(label="Xóa", style=discord.ButtonStyle.secondary, emoji="🗑️")
    async def delete_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id == self.requester_id or (interaction.guild and interaction.user.guild_permissions.manage_messages):
            await interaction.message.delete()
        else:
            vi = is_vietnamese(interaction.guild)
            msg = "❌ Chỉ người yêu cầu dịch mới được xóa tin này!" if vi else "❌ Only the requester can delete this message!"
            await interaction.response.send_message(msg, ephemeral=True)


class AdvancedTranslatorCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        # Khởi tạo bảng dữ liệu khi load cog
        self.bot.loop.create_task(self.init_database())

    async def init_database(self):
        os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
        async with aiosqlite.connect(DB_PATH) as db:
            await db.execute("""
                CREATE TABLE IF NOT EXISTS glossary (
                    guild_id INTEGER,
                    source_term TEXT,
                    target_term TEXT,
                    PRIMARY KEY (guild_id, source_term)
                )
            """)
            await db.commit()

    async def get_server_glossary(self, guild_id: int) -> dict:
        """Lấy toàn bộ từ điển tùy chỉnh của một server"""
        if not guild_id:
            return {}
        async with aiosqlite.connect(DB_PATH) as db:
            async with db.execute(
                "SELECT source_term, target_term FROM glossary WHERE guild_id = ?", 
                (guild_id,)
            ) as cursor:
                rows = await cursor.fetchall()
                return {row[0]: row[1] for row in rows}

    async def translate_with_ai(self, text: str, target_lang: str, glossary: dict = None) -> str:
        """Dịch bằng mistralai/mistral-large-4-0 qua xKiro có áp dụng luật từ điển riêng (Custom Glossary)"""
        glossary_prompt = ""
        if glossary:
            terms = "\n".join([f'- "{k}" must be translated or kept as "{v}"' for k, v in glossary.items()])
            glossary_prompt = (
                f"\nSTRICT GLOSSARY RULES:\n{terms}\n"
                "Never deviate from these glossary translations."
            )

        system_instruction = (
            f"You are a professional translator. Translate the text into {target_lang}. "
            "Preserve tone, formatting, and markdown tags. "
            "OUTPUT ONLY THE TRANSLATED TEXT without explanations, backticks, or quotes."
            f"{glossary_prompt}"
        )

        response = await xkiro_client.chat.completions.create(
            model=AI_MODEL,
            messages=[
                {"role": "system", "content": system_instruction},
                {"role": "user", "content": text},
            ],
            temperature=0.1,
            max_tokens=1500,
        )

        if response.choices and response.choices[0].message.content:
            return response.choices[0].message.content.strip()
        raise ValueError("Empty response from xKiro API")

    async def execute_translation(self, text: str, lang_info: dict, guild_id: int = None) -> str:
        """Quy trình dịch kép: xKiro AI kèm Glossary -> Fallback Google Translate"""
        glossary = await self.get_server_glossary(guild_id) if guild_id else {}
        try:
            return await self.translate_with_ai(text, lang_info["target"], glossary)
        except Exception as e:
            print(f"[Translator] xKiro AI lỗi ({e}), fallback Google...")
            # Fallback Google Translate trên thread riêng
            return await asyncio.to_thread(
                lambda: GoogleTranslator(source='auto', target=lang_info["iso"]).translate(text)
            )

    # ================= KHU VỰC REACTION TRANSLATE =================
    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload: discord.RawReactionActionEvent):
        if payload.user_id == self.bot.user.id:
            return

        emoji_str = str(payload.emoji)
        if emoji_str not in FLAG_TO_LANG:
            return

        channel = self.bot.get_channel(payload.channel_id)
        if not channel:
            try:
                channel = await self.bot.fetch_channel(payload.channel_id)
            except Exception:
                return

        try:
            target_msg = await channel.fetch_message(payload.message_id)
        except discord.NotFound:
            return

        if not target_msg.content or not target_msg.content.strip():
            return

        user = self.bot.get_user(payload.user_id) or await self.bot.fetch_user(payload.user_id)
        lang_info = FLAG_TO_LANG[emoji_str]

        async with channel.typing():
            translated = await self.execute_translation(
                target_msg.content, 
                lang_info, 
                payload.guild_id
            )

        safe_text = translated.replace("```", "'''")
        if len(safe_text) > 1000:
            safe_text = safe_text[:1000] + "..."

        embed = discord.Embed(
            description=f"**{emoji_str} Bản dịch sang {lang_info['name']}:**\n{safe_text}",
            color=0x3498DB
        )
        embed.set_footer(
            text=f"Yêu cầu bởi {user.display_name} • Nhấn 🗑️ để gỡ tin nhắn",
            icon_url=user.display_avatar.url
        )

        view = DeleteMessageView(requester_id=payload.user_id)
        await target_msg.reply(embed=embed, view=view, mention_author=False)

    # ================= KHU VỰC QUẢN LÝ TỪ ĐIỂN (GLOSSARY) =================
    glossary_group = app_commands.Group(name="glossary", description="Quản lý thuật ngữ dịch thuật riêng của Server")

    @glossary_group.command(name="add", description="Thêm hoặc cập nhật thuật ngữ vào từ điển Server")
    @app_commands.describe(
        source_term="Từ hoặc cụm từ gốc (ví dụ: nerf, gank, burst damage)",
        target_term="Cách dịch hoặc ghi chú (ví dụ: giảm sức mạnh, giữ nguyên, sốc sát thương)"
    )
    @app_commands.checks.has_permissions(manage_guild=True)
    async def glossary_add(self, interaction: discord.Interaction, source_term: str, target_term: str):
        src = source_term.strip()
        tgt = target_term.strip()

        async with aiosqlite.connect(DB_PATH) as db:
            await db.execute("""
                INSERT INTO glossary (guild_id, source_term, target_term)
                VALUES (?, ?, ?)
                ON CONFLICT(guild_id, source_term) 
                DO UPDATE SET target_term = excluded.target_term
            """, (interaction.guild_id, src, tgt))
            await db.commit()

        await interaction.response.send_message(
            f"✅ Đã thêm thuật ngữ vào từ điển máy chủ:\n"
            f"🔹 **{src}** ➔ **{tgt}**",
            ephemeral=True
        )

    @glossary_group.command(name="remove", description="Xóa một thuật ngữ khỏi từ điển Server")
    @app_commands.describe(source_term="Thuật ngữ cần xóa")
    @app_commands.checks.has_permissions(manage_guild=True)
    async def glossary_remove(self, interaction: discord.Interaction, source_term: str):
        src = source_term.strip()
        async with aiosqlite.connect(DB_PATH) as db:
            cursor = await db.execute(
                "DELETE FROM glossary WHERE guild_id = ? AND source_term = ?",
                (interaction.guild_id, src)
            )
            await db.commit()
            deleted = cursor.rowcount > 0

        if deleted:
            await interaction.response.send_message(f"🗑️ Đã xóa thuật ngữ **{src}** khỏi từ điển.", ephemeral=True)
        else:
            await interaction.response.send_message(f"❌ Không tìm thấy thuật ngữ **{src}** trong từ điển của Server.", ephemeral=True)

    @glossary_group.command(name="list", description="Xem toàn bộ danh sách thuật ngữ tùy chỉnh của Server")
    async def glossary_list(self, interaction: discord.Interaction):
        glossary = await self.get_server_glossary(interaction.guild_id)
        if not glossary:
            return await interaction.response.send_message("📖 Từ điển của Server hiện đang trống.", ephemeral=True)

        lines = [f"• **{k}** ➔ `{v}`" for k, v in glossary.items()]
        content = "\n".join(lines)

        embed = discord.Embed(
            title=f"📖 Từ điển thuật ngữ riêng - {interaction.guild.name}",
            description=content[:4000],
            color=0xF1C40F
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)


async def setup(bot: commands.Bot):
    await bot.add_cog(AdvancedTranslatorCog(bot))
