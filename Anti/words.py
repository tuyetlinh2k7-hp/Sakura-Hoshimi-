import discord
from discord.ext import commands
from discord import app_commands
import json
import os
from datetime import timedelta
import re
from typing import Literal
from Check.i18n import t

from config import OWNER_ID
from Check.mod import has_admin_role, is_owner, admin_roles
from Anti.link_filter import link_warnings, link_settings, save_link_warnings, load_link_data

WORD_SETTINGS_FILE = "data/word_filter_settings.json"
FORBIDDEN_WORDS_FILE = "data/forbidden_words.json"

word_settings = {}
forbidden_words = {}
global_word_filter_enabled = False

def load_word_data():
    """Tải cài đặt và danh sách từ cấm từ file JSON."""
    global word_settings, global_word_filter_enabled, forbidden_words

    if os.path.exists(WORD_SETTINGS_FILE):
        with open(WORD_SETTINGS_FILE, 'r', encoding='utf-8') as f:
            try: word_settings = json.load(f)
            except json.JSONDecodeError: word_settings = {}
    global_word_filter_enabled = word_settings.get("__global__", {}).get("enabled", False)

    if os.path.exists(FORBIDDEN_WORDS_FILE):
        with open(FORBIDDEN_WORDS_FILE, 'r', encoding='utf-8') as f:
            try: forbidden_words = json.load(f)
            except json.JSONDecodeError: forbidden_words = {}

    load_link_data()

def save_word_settings():
    """Lưu cài đặt của bộ lọc từ cấm."""
    os.makedirs(os.path.dirname(WORD_SETTINGS_FILE), exist_ok=True)
    if "__global__" not in word_settings:
        word_settings["__global__"] = {}
    word_settings["__global__"]["enabled"] = global_word_filter_enabled
    with open(WORD_SETTINGS_FILE, 'w', encoding='utf-8') as f:
        json.dump(word_settings, f, indent=4, ensure_ascii=False)

def save_forbidden_words():
    """Lưu danh sách từ cấm vào file."""
    os.makedirs(os.path.dirname(FORBIDDEN_WORDS_FILE), exist_ok=True)
    with open(FORBIDDEN_WORDS_FILE, 'w', encoding='utf-8') as f:
        json.dump(forbidden_words, f, indent=4, ensure_ascii=False)

class WordModal(discord.ui.Modal):
    def __init__(self, title: str, current_word: str = "", guild=None):
        super().__init__(title=title)
        self.guild_ref = guild
        self.word_input = discord.ui.TextInput(
            label=t(guild, "ANTI_WORD_MODAL_LABEL"),
            placeholder=t(guild, "ANTI_WORD_MODAL_PLACEHOLDER"),
            default=current_word,
            required=True
        )
        self.add_item(self.word_input)

    async def on_submit(self, interaction: discord.Interaction):
        guild_id_str = str(interaction.guild.id)
        word = self.word_input.value.lower().strip()

        if not word:
            return await interaction.response.send_message(t(interaction.guild, "ANTI_WORD_EMPTY"), ephemeral=True)

        if guild_id_str not in forbidden_words:
            forbidden_words[guild_id_str] = []

        if word in forbidden_words[guild_id_str]:
            return await interaction.response.send_message(t(interaction.guild, "ANTI_WORD_EXISTS", word=word), ephemeral=True)

        forbidden_words[guild_id_str].append(word)
        save_forbidden_words()
        await interaction.response.send_message(t(interaction.guild, "ANTI_WORD_ADDED", word=word), ephemeral=True)

class WordFilterControlView(discord.ui.View):
    def __init__(self, author_id: int, cog_instance, guild=None):
        super().__init__(timeout=180)
        self.author_id = author_id
        self.cog = cog_instance
        for item in self.children:
            if isinstance(item, discord.ui.Button):
                if item.emoji and str(item.emoji) == "🟢":
                    item.label = t(guild, "ANTI_WORD_BTN_ON")
                elif item.emoji and str(item.emoji) == "🔴":
                    item.label = t(guild, "ANTI_WORD_BTN_OFF")
                elif str(item.emoji) == "➕":
                    item.label = t(guild, "ANTI_WORD_BTN_ADD")
                elif str(item.emoji) == "📜":
                    item.label = t(guild, "ANTI_WORD_BTN_LIST")

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id != self.author_id:
            await interaction.response.send_message(t(interaction.guild, "ANTI_WORD_NOT_YOURS"), ephemeral=True)
            return False
        return True

    async def update_embed(self, interaction: discord.Interaction):
        prefix = await self.cog.bot.get_prefix(interaction.message) if interaction.message else "!"
        new_embed = self.cog._create_status_embed(interaction.guild, prefix)
        await interaction.response.edit_message(embed=new_embed, view=self)

    @discord.ui.button(label="Bật cho Server", style=discord.ButtonStyle.success, emoji="🟢")
    async def toggle_on(self, interaction: discord.Interaction, button: discord.ui.Button):
        guild_id_str = str(interaction.guild.id)
        if guild_id_str not in word_settings: word_settings[guild_id_str] = {}
        word_settings[guild_id_str]["enabled_guild"] = True
        save_word_settings()
        await self.update_embed(interaction)

    @discord.ui.button(label="Tắt cho Server", style=discord.ButtonStyle.danger, emoji="🔴")
    async def toggle_off(self, interaction: discord.Interaction, button: discord.ui.Button):
        guild_id_str = str(interaction.guild.id)
        if guild_id_str not in word_settings: word_settings[guild_id_str] = {}
        word_settings[guild_id_str]["enabled_guild"] = False
        save_word_settings()
        await self.update_embed(interaction)

    @discord.ui.button(label="Thêm Từ", style=discord.ButtonStyle.primary, emoji="➕", row=1)
    async def add_word(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(WordModal(title=t(interaction.guild, "ANTI_WORD_BTN_ADD"), guild=interaction.guild))

    @discord.ui.button(label="Xem/Xóa Từ", style=discord.ButtonStyle.secondary, emoji="📜", row=1)
    async def list_words(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer(ephemeral=True)
        await self.cog.list_words(interaction)

class WordFilterCog(commands.Cog, name="Anti-Word"):
    """Cog để lọc các từ ngữ nhạy cảm, bị cấm."""

    def __init__(self, bot: commands.Bot):
        self.bot = bot
        load_word_data()

    def _create_status_embed(self, guild: discord.Guild, prefix: str) -> discord.Embed:
        guild_id_str = str(guild.id)
        settings = word_settings.get(guild_id_str, {})
        
        global_status = t(guild, "ANTI_LINK_STATUS_ON") if global_word_filter_enabled else t(guild, "ANTI_LINK_STATUS_OFF")
        guild_status = t(guild, "ANTI_LINK_STATUS_ON") if settings.get("enabled_guild", False) else t(guild, "ANTI_LINK_STATUS_OFF")
        
        word_count = len(forbidden_words.get(guild_id_str, []))

        embed = discord.Embed(
            title=t(guild, "ANTI_WORD_DASHBOARD_TITLE"),
            description=t(guild, "ANTI_WORD_DASHBOARD_DESC", global_status=global_status, guild_status=guild_status, count=word_count),
            color=discord.Color.from_rgb(231, 76, 60)
        )
        embed.add_field(
            name=t(guild, "ANTI_WORD_FIELD_MANAGE"),
            value=t(guild, "ANTI_WORD_FIELD_MANAGE_VALUE", prefix=prefix),
            inline=False
        )
        return embed

    async def handle_word_violation(self, message: discord.Message, found_word: str):
        guild_id_str = str(message.guild.id)
        user_id_str = str(message.author.id)

        await message.delete()

        warning_limit = link_settings.get(guild_id_str, {}).get("warning_limit", 5)
        if guild_id_str not in link_warnings: link_warnings[guild_id_str] = {}
        user_warnings = link_warnings[guild_id_str].get(user_id_str, 0) + 1

        if warning_limit > 0 and user_warnings >= warning_limit:
            try:
                duration = timedelta(minutes=5)
                await message.author.timeout(duration, reason=f"Vi phạm quy định về từ ngữ quá nhiều lần.")
                mute_embed = discord.Embed(title=t(message.guild, "ANTI_WORD_AUTOMUTE_TITLE"), description=t(message.guild, "ANTI_WORD_AUTOMUTE_DESC", mention=message.author.mention, limit=warning_limit), color=discord.Color.dark_red())
                await message.channel.send(embed=mute_embed)
                link_warnings[guild_id_str][user_id_str] = 0
            except discord.Forbidden:
                await message.channel.send(t(message.guild, "ANTI_WORD_MUTE_FORBIDDEN", mention=message.author.mention), delete_after=10)
        else:
            warning_desc = t(message.guild, "ANTI_WORD_WARN_DESC", mention=message.author.mention, word=found_word)
            if warning_limit > 0:
                warning_desc += t(message.guild, "ANTI_WORD_WARN_COUNT", cur=user_warnings, limit=warning_limit)
            warning_embed = discord.Embed(title=t(message.guild, "ANTI_WORD_WARN_TITLE"), description=warning_desc, color=discord.Color.orange())
            await message.channel.send(embed=warning_embed, delete_after=15)
            link_warnings[guild_id_str][user_id_str] = user_warnings
        
        save_link_warnings()

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if not message.guild or message.author.bot or not message.content:
            return

        if not global_word_filter_enabled: return
        
        guild_id_str = str(message.guild.id)
        if not word_settings.get(guild_id_str, {}).get("enabled_guild", False): return

        if message.author.id == OWNER_ID: return
        guild_admin_roles = admin_roles.get(guild_id_str, [])
        user_role_ids = {role.id for role in message.author.roles}
        if any(admin_role_id in user_role_ids for admin_role_id in guild_admin_roles): return

        words_to_check = forbidden_words.get(guild_id_str, [])
        if not words_to_check: return

        content_lower = message.content.lower()
        for word in words_to_check:
            pattern = r'\b' + re.escape(word) + r'\b'
            if re.search(pattern, content_lower):
                await self.handle_word_violation(message, word)
                return

    @commands.group(name="antiword", aliases=["wordfilter"], description="Quản lý hệ thống lọc từ cấm.")
    @has_admin_role()
    async def antiword(self, ctx: commands.Context):
        if ctx.invoked_subcommand is None:
            embed = self._create_status_embed(ctx.guild, ctx.prefix)
            view = WordFilterControlView(ctx.author.id, self, guild=ctx.guild)
            await ctx.send(embed=embed, view=view, ephemeral=True)

    @antiword.command(name="global", description="[Owner] Bật hoặc tắt lọc từ cấm trên toàn bộ bot.")
    @is_owner()
    async def toggle_global(self, ctx: commands.Context, status: Literal["on", "off"]):
        global global_word_filter_enabled
        global_word_filter_enabled = (status.lower() == "on")
        save_word_settings()
        status_text = t(ctx.guild, "ANTI_WORD_GLOBAL_ON") if global_word_filter_enabled else t(ctx.guild, "ANTI_WORD_GLOBAL_OFF")
        await ctx.send(status_text, ephemeral=True)

    @antiword.command(name="add", description="Thêm một từ/cụm từ vào danh sách cấm.")
    @has_admin_role()
    @app_commands.describe(word="Từ bạn muốn cấm.")
    async def add_word_cmd(self, ctx: commands.Context, *, word: str):
        guild_id_str = str(ctx.guild.id)
        word_lower = word.lower().strip()
        if not word_lower: return await ctx.send(t(ctx.guild, "ANTI_WORD_EMPTY"), ephemeral=True)

        if guild_id_str not in forbidden_words: forbidden_words[guild_id_str] = []
        if word_lower in forbidden_words[guild_id_str]: return await ctx.send(t(ctx.guild, "ANTI_WORD_EXISTS", word=word_lower), ephemeral=True)

        forbidden_words[guild_id_str].append(word_lower)
        save_forbidden_words()
        await ctx.send(t(ctx.guild, "ANTI_WORD_ADDED", word=word_lower), ephemeral=True)

    @antiword.command(name="remove", description="Xóa một từ/cụm từ khỏi danh sách cấm.")
    @has_admin_role()
    @app_commands.describe(word="Từ bạn muốn xóa.")
    async def remove_word_cmd(self, ctx: commands.Context, *, word: str):
        guild_id_str = str(ctx.guild.id)
        word_lower = word.lower().strip()
        
        server_words = forbidden_words.get(guild_id_str, [])
        if word_lower not in server_words:
            return await ctx.send(t(ctx.guild, "ANTI_WORD_NOT_FOUND", word=word_lower), ephemeral=True)

        server_words.remove(word_lower)
        save_forbidden_words()
        await ctx.send(t(ctx.guild, "ANTI_WORD_REMOVED", word=word_lower), ephemeral=True)

    @antiword.command(name="list", description="Hiển thị danh sách các từ bị cấm trong server.")
    @has_admin_role()
    async def list_words_cmd(self, ctx: commands.Context):
        await self.list_words(ctx.interaction or ctx)

    async def list_words(self, interaction_or_ctx):
        """Hàm logic để hiển thị danh sách từ cấm, có thể gọi từ lệnh hoặc nút."""
        guild = interaction_or_ctx.guild
        guild_id_str = str(guild.id)
        server_words = forbidden_words.get(guild_id_str, [])

        if not server_words:
            embed = discord.Embed(title=t(guild, "ANTI_WORD_LIST_TITLE"), description=t(guild, "ANTI_WORD_LIST_EMPTY"), color=discord.Color.blue())
            if isinstance(interaction_or_ctx, discord.Interaction):
                await interaction_or_ctx.followup.send(embed=embed, ephemeral=True)
            else:
                await interaction_or_ctx.send(embed=embed, ephemeral=True)
            return

        options = [discord.SelectOption(label=word[:100], value=word) for word in sorted(server_words)]
        select = discord.ui.Select(placeholder=t(guild, "ANTI_WORD_SELECT_PLACEHOLDER"), options=options, min_values=1, max_values=1)

        async def select_callback(interaction: discord.Interaction):
            word_to_remove = interaction.data['values'][0]
            server_words.remove(word_to_remove)
            save_forbidden_words()
            await interaction.response.send_message(t(interaction.guild, "ANTI_WORD_REMOVED_SELECT", word=word_to_remove), ephemeral=True)

        select.callback = select_callback
        view = discord.ui.View(timeout=180)
        view.add_item(select)

        description = " - ".join(f"`{word}`" for word in sorted(server_words))
        embed = discord.Embed(title=t(guild, "ANTI_WORD_LIST_TITLE_COUNT", count=len(server_words)), description=description, color=discord.Color.blue())
        embed.set_footer(text=t(guild, "ANTI_WORD_LIST_FOOTER"))
        
        if isinstance(interaction_or_ctx, discord.Interaction):
            await interaction_or_ctx.followup.send(embed=embed, view=view, ephemeral=True)
        else:
            await interaction_or_ctx.send(embed=embed, view=view, ephemeral=True)

async def setup(bot: commands.Bot):
    await bot.add_cog(WordFilterCog(bot))
