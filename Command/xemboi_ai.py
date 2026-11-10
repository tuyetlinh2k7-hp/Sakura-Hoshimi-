import asyncio
import os
import random
import discord
from discord.ext import commands
from discord import app_commands
from openai import AsyncOpenAI

from Check.i18n import t

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
    base_url="[https://api.xkiro.com/v1](https://api.xkiro.com/v1)",
)

try:
    from config import AI_MODEL
except ImportError:
    AI_MODEL = "sensenova/sensenova-6.8-flash-lite"


class XemBoiView(discord.ui.View):
    def __init__(self, user: discord.User, cau_hoi: str, guild=None):
        super().__init__(timeout=60)
        self.user = user
        self.cau_hoi = cau_hoi
        self.guild = guild
        if guild:
            self.giai_ma_callback.label = t(guild, "XEMBOI_BUTTON_LABEL")

    @discord.ui.button(label="Giải Mã Quẻ Xăm 🔮", style=discord.ButtonStyle.primary, custom_id="giai_ma_boi")
    async def giai_ma_callback(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.user.id:
            await interaction.response.send_message(t(interaction.guild, "XEMBOI_NOT_YOURS"), ephemeral=True)
            return

        button.disabled = True
        button.label = t(interaction.guild, "XEMBOI_BUTTON_DRAWING")
        button.style = discord.ButtonStyle.secondary
        await interaction.message.edit(view=self)
        
        await interaction.response.defer()

        que_list = ["Đại Cát 🌟", "Thượng Cát 📈", "Trung Cát 🌤️", "Tiểu Cát 🌱", "Bình Hòa 🍃", "Hạ Hung 🌧️"]
        que_da_tieu = random.choice(que_list)

        try:
            chat_completion = await xkiro_client.chat.completions.create(
                model=AI_MODEL,
                messages=[
                    {
                        "role": "system",
                        "content": (
                            "Bạn là một thầy bói ảo vui tính, thông thái, chuyên giải quẻ bằng phong cách cổ trang "
                            "pha chút hài hước hiện đại. Hãy giải quẻ dựa trên câu hỏi của người dùng và quẻ xăm họ bốc được. "
                            "Trả lời ngắn gọn, súc tích dưới 200 từ, có kèm lời khuyên."
                        )
                    },
                    {
                        "role": "user",
                        "content": f"Người dùng hỏi: '{self.cau_hoi}'. Họ bốc được quẻ: '{que_da_tieu}'. Hãy luận giải quẻ này cho họ."
                    }
                ],
                temperature=0.85,
                max_tokens=350,
            )
            ai_reply = (
                chat_completion.choices[0].message.content.strip()
                if (chat_completion.choices and chat_completion.choices[0].message.content)
                else "..."
            )
        except Exception as e:
            ai_reply = t(interaction.guild, "XEMBOI_AI_ERROR", error=e)

        embed_ket_qua = discord.Embed(
            title=t(interaction.guild, "XEMBOI_RESULT_TITLE"),
            description=t(interaction.guild, "XEMBOI_RESULT_DESC", mention=self.user.mention, question=self.cau_hoi, fortune=que_da_tieu),
            color=discord.Color.purple()
        )
        embed_ket_qua.add_field(name=t(interaction.guild, "XEMBOI_FIELD_READING"), value=ai_reply[:1024], inline=False)
        embed_ket_qua.set_footer(text=f"{t(interaction.guild, 'XEMBOI_FOOTER')} • Model: {AI_MODEL}")

        await interaction.followup.send(embed=embed_ket_qua)
        await interaction.message.edit(view=None)


class XemBoiCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(name="xemboi", description="Xin quẻ và nhờ AI giải mã tương lai cho bạn")
    @app_commands.describe(cau_hoi="Nội dung bạn muốn xin quẻ (Ví dụ: Tình duyên, học hành...)")
    @app_commands.checks.cooldown(1, 20.0, key=lambda i: i.user.id)
    async def xemboi(self, interaction: discord.Interaction, cau_hoi: str):
        from Command.vote import require_vote_or_notify
        if not await require_vote_or_notify(interaction, "/xemboi (AI Xin Quẻ & Giải Mã)"):
            return

        embed_bat_dau = discord.Embed(
            title=t(interaction.guild, "XEMBOI_START_TITLE"),
            description=t(interaction.guild, "XEMBOI_START_DESC", mention=interaction.user.mention, question=cau_hoi),
            color=discord.Color.gold()
        )
        embed_bat_dau.set_thumbnail(url=interaction.user.display_avatar.url)
        
        view = XemBoiView(user=interaction.user, cau_hoi=cau_hoi, guild=interaction.guild)
        await interaction.response.send_message(embed=embed_bat_dau, view=view)

    @xemboi.error
    async def xemboi_error(self, interaction: discord.Interaction, error: app_commands.AppCommandError):
        if isinstance(error, app_commands.CommandOnCooldown):
            try:
                await interaction.response.send_message(
                    t(interaction.guild, "XEMBOI_COOLDOWN", retry=error.retry_after),
                    ephemeral=True
                )
            except Exception:
                await interaction.followup.send(t(interaction.guild, "XEMBOI_COOLDOWN", retry=error.retry_after), ephemeral=True)
        else:
            try:
                await interaction.response.send_message(t(interaction.guild, "XEMBOI_ERROR_GENERIC"), ephemeral=True)
            except Exception:
                await interaction.followup.send(t(interaction.guild, "XEMBOI_ERROR_GENERIC"), ephemeral=True)


async def setup(bot: commands.Bot):
    await bot.add_cog(XemBoiCog(bot))
