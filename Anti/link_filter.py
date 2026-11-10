import discord
from discord.ext import commands
from discord import app_commands
import json
import os
from datetime import timedelta
import re
from urllib.parse import urlparse
from typing import Literal
from Check.i18n import t


from config import OWNER_ID
from Check.mod import has_admin_role, admin_roles, is_owner

ALLOWED_LINKS_FILE = "data/allowed_links.json"
LINK_WARNINGS_FILE = "data/link_warnings.json"
LINK_SETTINGS_FILE = "data/link_filter_settings.json"

DEFAULT_ALLOWED_LINKS = {
    "tenor.com", "discord.com", "cdn.discordapp.com", "media.discordapp.net",
    "youtube.com", "youtu.be", "imgur.com", "giphy.com", "google.com",
    "facebook.com", "twitter.com", "instagram.com", "tiktok.com", "douyin.com"
}

allowed_links = {}
link_warnings = {}
link_settings = {}
global_link_filter_enabled = False

def load_link_data():
    """Tải tất cả dữ liệu liên quan đến link filter."""
    global allowed_links, link_warnings, link_settings, global_link_filter_enabled
    
    if os.path.exists(ALLOWED_LINKS_FILE):
        with open(ALLOWED_LINKS_FILE, 'r') as f:
            try:
                loaded_data = json.load(f)
                allowed_links = {guild_id: set(domains) for guild_id, domains in loaded_data.items()}
            except (json.JSONDecodeError, AttributeError):
                allowed_links = {}

    if os.path.exists(LINK_WARNINGS_FILE):
        with open(LINK_WARNINGS_FILE, 'r') as f:
            try: link_warnings = json.load(f)
            except json.JSONDecodeError: link_warnings = {}
    
    if os.path.exists(LINK_SETTINGS_FILE):
        with open(LINK_SETTINGS_FILE, 'r') as f:
            try: link_settings = json.load(f)
            except json.JSONDecodeError: link_settings = {}
    
    global_link_filter_enabled = link_settings.get("__global__", {}).get("enabled", False)

def save_allowed_links():
    """Lưu danh sách các tên miền được phép vào file JSON."""
    os.makedirs(os.path.dirname(ALLOWED_LINKS_FILE), exist_ok=True)
    with open(ALLOWED_LINKS_FILE, 'w') as f:
        data_to_save = {guild_id: list(domains) for guild_id, domains in allowed_links.items()}
        json.dump(data_to_save, f, indent=4)

def save_link_warnings():
    """Lưu dữ liệu cảnh cáo người dùng."""
    os.makedirs(os.path.dirname(LINK_WARNINGS_FILE), exist_ok=True)
    with open(LINK_WARNINGS_FILE, 'w') as f:
        json.dump(link_warnings, f, indent=4)

def save_link_settings():
    """Lưu cài đặt của bộ lọc link."""
    os.makedirs(os.path.dirname(LINK_SETTINGS_FILE), exist_ok=True)
    if "__global__" not in link_settings:
        link_settings["__global__"] = {}
    link_settings["__global__"]["enabled"] = global_link_filter_enabled
    
    with open(LINK_SETTINGS_FILE, 'w') as f:
        json.dump(link_settings, f, indent=4)


class AddDomainModal(discord.ui.Modal):
    """Cửa sổ popup để nhập tên miền muốn cho phép."""
    def __init__(self, guild=None):
        super().__init__(title=t(guild, "ANTI_LINK_MODAL_TITLE"))
        self.guild_ref = guild
        self.domain_input = discord.ui.TextInput(
            label=t(guild, "ANTI_LINK_MODAL_LABEL"),
            placeholder=t(guild, "ANTI_LINK_MODAL_PLACEHOLDER"),
            style=discord.TextStyle.short,
            required=True
        )
        self.add_item(self.domain_input)

    async def on_submit(self, interaction: discord.Interaction):
        guild_id_str = str(interaction.guild.id)
        domain = self.domain_input.value.lower().strip()

        guild_allowed_links = allowed_links.get(guild_id_str, DEFAULT_ALLOWED_LINKS.copy())

        if domain in guild_allowed_links:
            return await interaction.response.send_message(t(interaction.guild, "ANTI_LINK_DOMAIN_EXISTS", domain=domain), ephemeral=True)
        
        guild_allowed_links.add(domain)
        allowed_links[guild_id_str] = guild_allowed_links
        save_allowed_links()
        await interaction.response.send_message(t(interaction.guild, "ANTI_LINK_DOMAIN_ADDED", domain=domain), ephemeral=True)

class LinkFilterControlView(discord.ui.View):
    """View chứa các nút điều khiển cho bộ lọc link."""
    def __init__(self, author_id: int, guild=None):
        super().__init__(timeout=120)
        self.author_id = author_id
        self.guild_ref = guild
        for child in self.children:
            if isinstance(child, discord.ui.Button):
                cid = child.custom_id or child.label
                if child.style == discord.ButtonStyle.success:
                    child.label = t(guild, "ANTI_LINK_BTN_ON")
                elif child.style == discord.ButtonStyle.danger:
                    child.label = t(guild, "ANTI_LINK_BTN_OFF")

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id != self.author_id:
            await interaction.response.send_message(t(interaction.guild, "ANTI_LINK_NOT_YOURS"), ephemeral=True)
            return False
        return True

    @discord.ui.button(label="Bật", style=discord.ButtonStyle.success, emoji="🟢")
    async def toggle_on(self, interaction: discord.Interaction, button: discord.ui.Button):
        guild_id_str = str(interaction.guild.id)
        if guild_id_str not in link_settings:
            link_settings[guild_id_str] = {}
        link_settings[guild_id_str]["enabled_guild"] = True
        save_link_settings()
        await interaction.response.send_message(t(interaction.guild, "ANTI_LINK_TOGGLE_ON_SUCCESS"), ephemeral=True)

    @discord.ui.button(label="Tắt", style=discord.ButtonStyle.danger, emoji="🔴")
    async def toggle_off(self, interaction: discord.Interaction, button: discord.ui.Button):
        guild_id_str = str(interaction.guild.id)
        if guild_id_str not in link_settings:
            link_settings[guild_id_str] = {}
        link_settings[guild_id_str]["enabled_guild"] = False
        save_link_settings()
        await interaction.response.send_message(t(interaction.guild, "ANTI_LINK_TOGGLE_OFF_SUCCESS"), ephemeral=True)

    @discord.ui.button(label="Thêm Link", style=discord.ButtonStyle.primary, emoji="➕")
    async def add_link(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(AddDomainModal(guild=interaction.guild))

    @discord.ui.button(label="Xem Link", style=discord.ButtonStyle.secondary, emoji="📜")
    async def list_links(self, interaction: discord.Interaction, button: discord.ui.Button):
        guild_id_str = str(interaction.guild.id)
        guild_allowed_links = allowed_links.get(guild_id_str, DEFAULT_ALLOWED_LINKS)

        if not guild_allowed_links:
            return await interaction.response.send_message(t(interaction.guild, "ANTI_LINK_NO_DOMAINS"), ephemeral=True)
        
        description = "\n".join(f"• `{domain}`" for domain in sorted(list(guild_allowed_links)))
        embed = discord.Embed(title=t(interaction.guild, "ANTI_LINK_LIST_TITLE"), description=description, color=discord.Color.blue())
        
        if guild_id_str not in allowed_links:
            embed.set_footer(text=t(interaction.guild, "ANTI_LINK_LIST_FOOTER_DEFAULT"))
            
        await interaction.response.send_message(embed=embed, ephemeral=True)

    def _set_labels(self, guild):
        for child in self.children:
            if hasattr(child, 'label'):
                if child.label in ["Bật", "Tắt", "Thêm Link", "Xem Link", t(None, "ANTI_LINK_BTN_ON"), t(None, "ANTI_LINK_BTN_OFF")]:
                    pass
        for item in self.children:
            if isinstance(item, discord.ui.Button):
                if item.emoji and str(item.emoji) == "🟢":
                    item.label = t(guild, "ANTI_LINK_BTN_ON")
                elif item.emoji and str(item.emoji) == "🔴":
                    item.label = t(guild, "ANTI_LINK_BTN_OFF")
                elif str(item.emoji) == "➕":
                    item.label = t(guild, "ANTI_LINK_BTN_ADD")
                elif str(item.emoji) == "📜":
                    item.label = t(guild, "ANTI_LINK_BTN_LIST")

class LinkFilterCog(commands.Cog, name="Link Filter"):
    """Cog để kiểm duyệt và lọc các liên kết không hợp lệ."""

    def __init__(self, bot: commands.Bot):
        self.bot = bot
        load_link_data()

    async def handle_violation(self, message: discord.Message, reason: str):
        """Hàm chung để xử lý khi phát hiện vi phạm về link."""
        guild_id_str = str(message.guild.id)
        user_id_str = str(message.author.id)

        await message.delete()

        warning_limit = link_settings.get(guild_id_str, {}).get("warning_limit", 5)
        if guild_id_str not in link_warnings: link_warnings[guild_id_str] = {}
        user_warnings = link_warnings[guild_id_str].get(user_id_str, 0)
        user_warnings += 1

        if warning_limit > 0 and user_warnings >= warning_limit:
            try:
                duration = timedelta(minutes=5)
                await message.author.timeout(duration, reason=f"Vi phạm quy định về link ({reason}) quá nhiều lần.")
                mute_embed = discord.Embed(title=t(message.guild, "ANTI_LINK_AUTOMUTE_TITLE"), description=t(message.guild, "ANTI_LINK_AUTOMUTE_DESC", mention=message.author.mention, limit=warning_limit), color=discord.Color.dark_red())
                await message.channel.send(embed=mute_embed)
                link_warnings[guild_id_str][user_id_str] = 0
            except discord.Forbidden:
                await message.channel.send(t(message.guild, "ANTI_LINK_MUTE_FORBIDDEN", mention=message.author.mention), delete_after=10)
        else:
            warning_desc = t(message.guild, "ANTI_LINK_WARN_DESC", mention=message.author.mention, reason=reason)
            if warning_limit > 0:
                warning_desc += t(message.guild, "ANTI_LINK_WARN_COUNT", cur=user_warnings, limit=warning_limit)
            
            warning_embed = discord.Embed(title=t(message.guild, "ANTI_LINK_WARN_TITLE"), description=warning_desc, color=discord.Color.orange())
            await message.channel.send(embed=warning_embed, delete_after=15)
            link_warnings[guild_id_str][user_id_str] = user_warnings
        
        save_link_warnings()

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if not message.guild or message.author.bot or not message.content:
            return

        if not global_link_filter_enabled:
            return
        guild_setting = link_settings.get(str(message.guild.id), {}).get("enabled_guild", False)
        if not guild_setting:
            return

        if message.author.id == OWNER_ID:
            return
        
        guild_admin_roles = admin_roles.get(str(message.guild.id), [])
        user_role_ids = {role.id for role in message.author.roles}
        if any(admin_role_id in user_role_ids for admin_role_id in guild_admin_roles):
            return

        urls = re.findall(r'https?://[^\s/$.?#].[^\s]*', message.content)
        if not urls:
            return

        for url in urls:
            try:
                guild_id_str = str(message.guild.id)
                domain = urlparse(url).netloc.lower()
                if domain.startswith('www.'):
                    domain = domain[4:]
                
                guild_allowed_links = allowed_links.get(guild_id_str, DEFAULT_ALLOWED_LINKS)

                if domain not in guild_allowed_links:
                    if domain == "discord.gg":
                        continue
                    await self.handle_violation(message, t(message.guild, "ANTI_LINK_REASON_FORBIDDEN"))
                    return
            except Exception as e:
                print(f"[Link Filter] Lỗi khi phân tích URL '{url}': {e}")

    @commands.group(name="linkfilter", aliases=["antilink"], description="Quản lý danh sách các tên miền được phép gửi link.")
    @has_admin_role()
    async def linkfilter(self, ctx: commands.Context):
        """Lệnh gốc cho nhóm quản lý link."""
        if ctx.invoked_subcommand is None:
            global_status_text = t(ctx.guild, "ANTI_LINK_STATUS_ON") if global_link_filter_enabled else t(ctx.guild, "ANTI_LINK_STATUS_OFF")
            guild_setting = link_settings.get(str(ctx.guild.id), {}).get("enabled_guild", False)
            guild_status_text = t(ctx.guild, "ANTI_LINK_STATUS_ON") if guild_setting else t(ctx.guild, "ANTI_LINK_STATUS_OFF")

            color = discord.Color.green() if global_link_filter_enabled and guild_setting else discord.Color.red()
            warning_limit = link_settings.get(str(ctx.guild.id), {}).get("warning_limit", 5)
            limit_text = t(ctx.guild, "ANTI_LINK_LIMIT_OFF", limit=warning_limit) if warning_limit == 0 else t(ctx.guild, "ANTI_LINK_LIMIT_ON", limit=warning_limit)
            prefix = ctx.prefix

            embed = discord.Embed(
                title=t(ctx.guild, "ANTI_LINK_DASHBOARD_TITLE"),
                description=t(ctx.guild, "ANTI_LINK_DASHBOARD_DESC", global_status=global_status_text, guild_status=guild_status_text, limit_text=limit_text),
                color=color
            )
            embed.add_field(
                name=t(ctx.guild, "ANTI_LINK_FIELD_MANAGE"),
                value=t(ctx.guild, "ANTI_LINK_FIELD_MANAGE_VALUE", prefix=prefix),
                inline=False
            )
            embed.set_footer(text=t(ctx.guild, "ANTI_LINK_FOOTER_ADMIN_ONLY"))
            view = LinkFilterControlView(ctx.author.id, guild=ctx.guild)
            for item in view.children:
                if isinstance(item, discord.ui.Button):
                    if item.emoji and str(item.emoji) == "🟢":
                        item.label = t(ctx.guild, "ANTI_LINK_BTN_ON")
                    elif item.emoji and str(item.emoji) == "🔴":
                        item.label = t(ctx.guild, "ANTI_LINK_BTN_OFF")
                    elif str(item.emoji) == "➕":
                        item.label = t(ctx.guild, "ANTI_LINK_BTN_ADD")
                    elif str(item.emoji) == "📜":
                        item.label = t(ctx.guild, "ANTI_LINK_BTN_LIST")
            await ctx.send(embed=embed, view=view, ephemeral=True)

    @linkfilter.command(name="toggle", description="Bật hoặc tắt hệ thống lọc link cho server này.")
    @has_admin_role()
    async def toggle_filter(self, ctx: commands.Context):
        """Mở bảng điều khiển bật/tắt cho server hiện tại."""
        guild_setting = link_settings.get(str(ctx.guild.id), {}).get("enabled_guild", False)
        status_text = t(ctx.guild, "ANTI_LINK_STATUS_ON") if guild_setting else t(ctx.guild, "ANTI_LINK_STATUS_OFF")
        embed = discord.Embed(title=t(ctx.guild, "ANTI_LINK_TOGGLE_TITLE"), description=t(ctx.guild, "ANTI_LINK_TOGGLE_DESC", status=status_text), color=discord.Color.blue())
        view = LinkFilterControlView(ctx.author.id, guild=ctx.guild)
        for item in view.children:
            if isinstance(item, discord.ui.Button):
                if item.emoji and str(item.emoji) == "🟢":
                    item.label = t(ctx.guild, "ANTI_LINK_BTN_ON")
                elif item.emoji and str(item.emoji) == "🔴":
                    item.label = t(ctx.guild, "ANTI_LINK_BTN_OFF")
                elif str(item.emoji) == "➕":
                    item.label = t(ctx.guild, "ANTI_LINK_BTN_ADD")
                elif str(item.emoji) == "📜":
                    item.label = t(ctx.guild, "ANTI_LINK_BTN_LIST")
        await ctx.send(embed=embed, view=view, ephemeral=True)

    @linkfilter.command(name="global", description="[Owner] Bật hoặc tắt lọc link trên toàn bộ bot.")
    @is_owner()
    async def toggle_global(self, ctx: commands.Context, status: Literal["on", "off"]):
        """Bật hoặc tắt hệ thống lọc link trên toàn cục."""
        global global_link_filter_enabled
        if status.lower() == "on":
            global_link_filter_enabled = True
            msg = t(ctx.guild, "ANTI_LINK_GLOBAL_ON")
        else:
            global_link_filter_enabled = False
            msg = t(ctx.guild, "ANTI_LINK_GLOBAL_OFF")
        save_link_settings()
        await ctx.send(msg, ephemeral=True)

    @linkfilter.command(name="setlimit", description="Cài đặt số lần cảnh cáo link trước khi tự động mute.")
    @has_admin_role()
    @app_commands.describe(limit="Số lần vi phạm tối đa. Nhập 0 để tắt tính năng tự động mute.")
    async def set_limit(self, ctx: commands.Context, limit: int):
        if limit < 0:
            return await ctx.send(t(ctx.guild, "ANTI_LINK_LIMIT_NEGATIVE"), ephemeral=True)

        guild_id_str = str(ctx.guild.id)
        if guild_id_str not in link_settings:
            link_settings[guild_id_str] = {}
        
        link_settings[guild_id_str]["warning_limit"] = limit
        save_link_settings()

        await ctx.send(t(ctx.guild, "ANTI_LINK_LIMIT_UPDATED", limit=limit), ephemeral=True)

    @linkfilter.command(name="add", description="Thêm một tên miền vào danh sách cho phép.")
    @has_admin_role()
    @app_commands.describe(domain="Tên miền bạn muốn cho phép (ví dụ: youtube.com)")
    async def add_domain(self, ctx: commands.Context, domain: str):
        guild_id_str = str(ctx.guild.id)
        domain = domain.lower().strip()

        guild_allowed_links = allowed_links.get(guild_id_str, DEFAULT_ALLOWED_LINKS.copy())

        if domain in guild_allowed_links:
            return await ctx.send(t(ctx.guild, "ANTI_LINK_DOMAIN_EXISTS", domain=domain), ephemeral=True)
        
        guild_allowed_links.add(domain)
        allowed_links[guild_id_str] = guild_allowed_links
        save_allowed_links()
        await ctx.send(t(ctx.guild, "ANTI_LINK_DOMAIN_ADDED", domain=domain), ephemeral=True)

    @linkfilter.command(name="remove", description="Xóa một tên miền khỏi danh sách cho phép.")
    @has_admin_role()
    @app_commands.describe(domain="Tên miền bạn muốn xóa (ví dụ: facebook.com)")
    async def remove_domain(self, ctx: commands.Context, domain: str):
        guild_id_str = str(ctx.guild.id)
        domain = domain.lower().strip()

        guild_allowed_links = allowed_links.get(guild_id_str, DEFAULT_ALLOWED_LINKS.copy())

        if domain not in guild_allowed_links:
            return await ctx.send(t(ctx.guild, "ANTI_LINK_DOMAIN_NOT_FOUND", domain=domain), ephemeral=True)
            
        guild_allowed_links.remove(domain)
        allowed_links[guild_id_str] = guild_allowed_links
        save_allowed_links()
        await ctx.send(t(ctx.guild, "ANTI_LINK_DOMAIN_REMOVED", domain=domain), ephemeral=True)

    @linkfilter.command(name="list", description="Hiển thị tất cả các tên miền được phép.")
    @has_admin_role()
    async def list_domains(self, ctx: commands.Context):
        guild_id_str = str(ctx.guild.id)
        guild_allowed_links = allowed_links.get(guild_id_str, DEFAULT_ALLOWED_LINKS)

        if not guild_allowed_links:
            return await ctx.send(t(ctx.guild, "ANTI_LINK_NO_DOMAINS"), ephemeral=True)
        
        description = "\n".join(f"• `{domain}`" for domain in sorted(list(guild_allowed_links)))
        embed = discord.Embed(title=t(ctx.guild, "ANTI_LINK_LIST_TITLE"), description=description, color=discord.Color.blue())
        if guild_id_str not in allowed_links:
            embed.set_footer(text=t(ctx.guild, "ANTI_LINK_LIST_FOOTER_CMD"))
        await ctx.send(embed=embed, ephemeral=True)

async def setup(bot: commands.Bot):
    await bot.add_cog(LinkFilterCog(bot))
