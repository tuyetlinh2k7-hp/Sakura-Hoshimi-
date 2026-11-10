import discord
from discord.ext import commands
from discord import app_commands
import json
import os
from datetime import timedelta
import re
from typing import Optional
from Check.i18n import t

from config import OWNER_ID
from Check.mod import has_admin_role, is_owner
from Check.data import groq_client

INSULT_SETTINGS_FILE = "data/insult_filter_settings.json"
INSULT_VIOLATIONS_FILE = "data/insult_violations.json"

DEFAULT_INSULT_PATTERNS = [
    r"\bbot\b.*\bngu\b", r"\bbot\b.*\bdở\b", r"\bbot\b.*\bcùi\b", r"\bbot\b.*\blởm\b", r"\bbot\b.*\bóc chó\b",
    r"\bsakura\b.*\bngu\b", r"\bsakura\b.*\bdở\b", r"\bsakura\b.*\bxấu\b",
    r"con bot này", r"con sakura này",
    r"\bchủ\b.*\bngu\b", r"\bowner\b.*\bngu\b", r"thằng chủ", r"con chủ", r"\bchủ\b.*\bóc chó\b",
    r"địt mẹ bot", r"địt mẹ sakura", r"đm bot", r"dcm bot", r"dmm bot", r"đmm bot",
    r"bot lồn", r"bot cặc", r"bot ngu lồn",
    r"sakura lồn", r"sakura cặc",
    r"chủ lồn", r"chủ cặc", r"owner lồn", r"owner cặc"
]

insult_settings = {}
insult_violations = {}

def load_insult_data():
    """Tải cài đặt và dữ liệu vi phạm từ file JSON."""
    global insult_settings, insult_violations

    if os.path.exists(INSULT_SETTINGS_FILE):
        with open(INSULT_SETTINGS_FILE, 'r', encoding='utf-8') as f:
            try: insult_settings = json.load(f)
            except json.JSONDecodeError: insult_settings = {}

    if os.path.exists(INSULT_VIOLATIONS_FILE):
        with open(INSULT_VIOLATIONS_FILE, 'r', encoding='utf-8') as f:
            try: insult_violations = json.load(f)
            except json.JSONDecodeError: insult_violations = {}

def save_insult_settings():
    """Lưu cài đặt của bộ lọc."""
    os.makedirs(os.path.dirname(INSULT_SETTINGS_FILE), exist_ok=True)
    with open(INSULT_SETTINGS_FILE, 'w', encoding='utf-8') as f:
        json.dump(insult_settings, f, indent=4, ensure_ascii=False)

def save_insult_violations():
    """Lưu dữ liệu vi phạm của người dùng."""
    os.makedirs(os.path.dirname(INSULT_VIOLATIONS_FILE), exist_ok=True)
    with open(INSULT_VIOLATIONS_FILE, 'w', encoding='utf-8') as f:
        json.dump(insult_violations, f, indent=4, ensure_ascii=False)

class InsultFilterCog(commands.Cog, name="Anti-Insult"):
    """Cog để phát hiện và xử lý các hành vi xúc phạm bot hoặc chủ bot."""

    def __init__(self, bot: commands.Bot):
        self.bot = bot
        load_insult_data()

    async def _generate_ai_rebuttal(self, member: discord.Member, violation_count: int, insult: str) -> str:
        """Sử dụng AI để tạo ra một lời phản bác thông minh và tự nhiên."""
        try:
            if violation_count == 1:
                mood = "buồn và thất vọng một chút"
            elif violation_count == 2:
                mood = "bực mình và nghiêm khắc hơn"
            else:
                mood = "rất tức giận và cảnh cáo mạnh mẽ"

            prompt = (
                f"Bạn là Sakura, một AI bot trên Discord. Người dùng '{member.display_name}' vừa nói một câu xúc phạm bạn: '{insult}'. "
                f"Đây là lần vi phạm thứ {violation_count} của họ. "
                f"Hãy đóng vai Sakura và viết một lời phản bác. "
                f"Tâm trạng của bạn bây giờ là {mood}. "
                f"Lời phản bác phải ngắn gọn, trực tiếp, và thể hiện cảm xúc phù hợp. "
                "Không cần thêm emoji, lời chào, hay nhắc đến hình phạt (nó sẽ được thêm vào sau)."
            )

            chat_completion = groq_client.chat.completions.create(
                messages=[
                    {"role": "system", "content": "Bạn là một AI bot Discord tên Sakura, đang phản hồi lại một lời xúc phạm."},
                    {"role": "user", "content": prompt}
                ],
                model="llama-3.3-70b-versatile",
                temperature=0.8,
                max_tokens=150,
            )
            return chat_completion.choices[0].message.content
        except Exception as e:
            print(f"[Anti-Insult AI] Lỗi khi tạo phản hồi: {e}")
            return t(member.guild, "ANTI_INSULT_FALLBACK", mention=member.mention)

    async def handle_insult_violation(self, message: discord.Message, found_insult: str):
        """Xử lý khi phát hiện vi phạm, với hình phạt tăng dần."""
        guild_id_str = str(message.guild.id)
        user_id_str = str(message.author.id)

        await message.delete()

        if guild_id_str not in insult_violations:
            insult_violations[guild_id_str] = {}
        
        user_violations = insult_violations[guild_id_str].get(user_id_str, 0) + 1
        insult_violations[guild_id_str][user_id_str] = user_violations
        save_insult_violations()

        mute_duration_minutes = 0
        embed_title = ""
        embed_color = discord.Color.default()
        
        if user_violations == 1:
            mute_duration_minutes = 5
            embed_title = t(message.guild, "ANTI_INSULT_TITLE_WARN1")
            embed_color = discord.Color.yellow()
        elif user_violations == 2:
            mute_duration_minutes = 30
            embed_title = t(message.guild, "ANTI_INSULT_TITLE_WARN2")
            embed_color = discord.Color.orange()
        else:
            mute_duration_minutes = 60
            embed_title = t(message.guild, "ANTI_INSULT_TITLE_SEVERE")
            embed_color = discord.Color.dark_red()

        ai_rebuttal = await self._generate_ai_rebuttal(message.author, user_violations, message.content)
        
        full_rebuttal_message = (
            f"{t(message.guild, 'ANTI_INSULT_REBUTTAL_HEADER', mention=message.author.mention)}\n"
            f"{ai_rebuttal}\n\n"
            f"{t(message.guild, 'ANTI_INSULT_PUNISHMENT', minutes=mute_duration_minutes)}\n"
            f"{t(message.guild, 'ANTI_INSULT_VIOLATION_COUNT', count=user_violations)}"
        )

        try:
            duration = timedelta(minutes=mute_duration_minutes)
            await message.author.timeout(duration, reason=f"Xúc phạm bot/chủ bot (lần {user_violations})")
            
            embed = discord.Embed(
                title=embed_title,
                description=full_rebuttal_message,
                color=embed_color
            )
            await message.channel.send(embed=embed)

        except discord.Forbidden:
            await message.channel.send(t(message.guild, "ANTI_INSULT_MUTE_FORBIDDEN", mention=message.author.mention), delete_after=10)
        except Exception as e:
            print(f"[Anti-Insult] Lỗi khi xử lý vi phạm: {e}")

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if not message.guild or message.author.bot or not message.content:
            return

        if message.author.id == OWNER_ID or message.author.guild_permissions.administrator:
            return

        guild_id_str = str(message.guild.id)
        guild_settings = insult_settings.get(guild_id_str, {})
        enabled_channels = guild_settings.get("enabled_channels", [])

        if message.channel.id not in enabled_channels:
            return

        content_lower = message.content.lower()
        patterns = guild_settings.get("patterns", DEFAULT_INSULT_PATTERNS)

        for pattern in patterns:
            try:
                if re.search(pattern, content_lower):
                    await self.handle_insult_violation(message, pattern)
                    return
            except re.error as e:
                print(f"[Anti-Insult] Lỗi regex: {e} với mẫu: {pattern}")
                continue

    @commands.group(name="antiinsult", aliases=["antixp"], description="Quản lý hệ thống chống xúc phạm bot/chủ bot.")
    @has_admin_role()
    async def antiinsult(self, ctx: commands.Context):
        """Lệnh gốc cho nhóm quản lý chống xúc phạm."""
        if ctx.invoked_subcommand is None:
            guild_id_str = str(ctx.guild.id)
            guild_settings = insult_settings.get(guild_id_str, {})
            enabled_channels = guild_settings.get("enabled_channels", [])
            
            channels_mention = [f"<#{cid}>" for cid in enabled_channels]
            status_text = ", ".join(channels_mention) if channels_mention else t(ctx.guild, "ANTI_INSULT_NO_CHANNEL")

            embed = discord.Embed(
                title=t(ctx.guild, "ANTI_INSULT_DASHBOARD_TITLE"),
                description=t(ctx.guild, "ANTI_INSULT_DASHBOARD_DESC", channels=status_text),
                color=discord.Color.blue()
            )

            guild_violations = insult_violations.get(guild_id_str, {})
            if guild_violations:
                sorted_violations = sorted(guild_violations.items(), key=lambda item: item[1], reverse=True)[:10]
                
                violation_list = []
                for user_id, count in sorted_violations:
                    violation_list.append(t(ctx.guild, "ANTI_INSULT_HISTORY_ENTRY", user_id=user_id, count=count))
                
                violation_text = "\n".join(violation_list)
                embed.add_field(name=t(ctx.guild, "ANTI_INSULT_HISTORY_FIELD_NAME"), value=violation_text, inline=False)

            embed.add_field(
                name=t(ctx.guild, "ANTI_INSULT_MANAGE_FIELD_NAME"),
                value=t(ctx.guild, "ANTI_INSULT_MANAGE_FIELD_VALUE"),
                inline=False
            )
            await ctx.send(embed=embed, ephemeral=True)

    @antiinsult.group(name="channel", description="Bật hoặc tắt tính năng chống xúc phạm cho một kênh.")
    @has_admin_role()
    async def channel(self, ctx: commands.Context):
        if ctx.invoked_subcommand is None:
            await ctx.send(t(ctx.guild, "ANTI_INSULT_NEED_SUBCOMMAND"), ephemeral=True)

    @channel.command(name="on", description="Bật tính năng cho kênh này hoặc kênh được chỉ định.")
    @app_commands.describe(channel="Kênh bạn muốn bật (mặc định là kênh hiện tại).")
    async def channel_on(self, ctx: commands.Context, channel: Optional[discord.TextChannel]):
        target_channel = channel or ctx.channel
        guild_id_str = str(ctx.guild.id)

        if guild_id_str not in insult_settings:
            insult_settings[guild_id_str] = {"enabled_channels": [], "patterns": DEFAULT_INSULT_PATTERNS}
        
        if target_channel.id in insult_settings[guild_id_str]["enabled_channels"]:
            return await ctx.send(t(ctx.guild, "ANTI_INSULT_CHANNEL_ALREADY_ON", channel=target_channel.mention), ephemeral=True)

        insult_settings[guild_id_str]["enabled_channels"].append(target_channel.id)
        save_insult_settings()
        await ctx.send(t(ctx.guild, "ANTI_INSULT_CHANNEL_ON_SUCCESS", channel=target_channel.mention), ephemeral=True)

    @channel.command(name="off", description="Tắt tính năng cho kênh này hoặc kênh được chỉ định.")
    @app_commands.describe(channel="Kênh bạn muốn tắt (mặc định là kênh hiện tại).")
    async def channel_off(self, ctx: commands.Context, channel: Optional[discord.TextChannel]):
        target_channel = channel or ctx.channel
        guild_id_str = str(ctx.guild.id)

        if guild_id_str not in insult_settings or target_channel.id not in insult_settings[guild_id_str].get("enabled_channels", []):
            return await ctx.send(t(ctx.guild, "ANTI_INSULT_CHANNEL_ALREADY_OFF", channel=target_channel.mention), ephemeral=True)

        insult_settings[guild_id_str]["enabled_channels"].remove(target_channel.id)
        save_insult_settings()
        await ctx.send(t(ctx.guild, "ANTI_INSULT_CHANNEL_OFF_SUCCESS", channel=target_channel.mention), ephemeral=True)

    @antiinsult.command(name="reset", description="Reset số lần vi phạm của một thành viên.")
    @has_admin_role()
    @app_commands.describe(member="Thành viên bạn muốn reset.")
    async def reset(self, ctx: commands.Context, member: discord.Member):
        guild_id_str = str(ctx.guild.id)
        user_id_str = str(member.id)

        if guild_id_str in insult_violations and user_id_str in insult_violations[guild_id_str]:
            del insult_violations[guild_id_str][user_id_str]
            save_insult_violations()
            await ctx.send(t(ctx.guild, "ANTI_INSULT_RESET_SUCCESS", mention=member.mention), ephemeral=True)
        else:
            await ctx.send(t(ctx.guild, "ANTI_INSULT_RESET_NO_HISTORY", mention=member.mention), ephemeral=True)

async def setup(bot: commands.Bot):
    await bot.add_cog(InsultFilterCog(bot))
