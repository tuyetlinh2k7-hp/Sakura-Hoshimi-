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
from Check.mod import admin_roles, has_admin_role, is_owner

LINK_WARNINGS_FILE = "data/link_warnings.json"
LINK_SETTINGS_FILE = "data/link_filter_settings.json"

link_warnings = {}
link_settings = {}
global_invite_filter_enabled = False

def load_invite_data():
    """Tải dữ liệu cảnh cáo và cài đặt."""
    global link_warnings, link_settings, global_invite_filter_enabled

    if os.path.exists(LINK_WARNINGS_FILE):
        with open(LINK_WARNINGS_FILE, 'r') as f:
            try: link_warnings = json.load(f)
            except json.JSONDecodeError: link_warnings = {}
    
    if os.path.exists(LINK_SETTINGS_FILE):
        with open(LINK_SETTINGS_FILE, 'r') as f:
            try: link_settings = json.load(f)
            except json.JSONDecodeError: link_settings = {}

    global_invite_filter_enabled = link_settings.get("__global__", {}).get("invite_enabled", False)

def save_link_warnings():
    """Lưu dữ liệu cảnh cáo người dùng."""
    os.makedirs(os.path.dirname(LINK_WARNINGS_FILE), exist_ok=True)
    with open(LINK_WARNINGS_FILE, 'w') as f:
        json.dump(link_warnings, f, indent=4)

def save_settings():
    """Lưu toàn bộ cài đặt (cả global và guild) vào file."""
    os.makedirs(os.path.dirname(LINK_SETTINGS_FILE), exist_ok=True)
    if "__global__" not in link_settings:
        link_settings["__global__"] = {}
    link_settings["__global__"]["invite_enabled"] = global_invite_filter_enabled
    
    with open(LINK_SETTINGS_FILE, 'w') as f:
        json.dump(link_settings, f, indent=4)

class AntiInviteControlView(discord.ui.View):
    """View chứa các nút bật/tắt cho bộ lọc link mời."""
    def __init__(self, author_id: int, guild_id: int, guild=None):
        super().__init__(timeout=120)
        self.author_id = author_id
        self.guild_ref = guild
        for item in self.children:
            if isinstance(item, discord.ui.Button):
                if item.emoji and str(item.emoji) == "🟢":
                    item.label = t(guild, "ANTI_INVITE_BTN_ON")
                elif item.emoji and str(item.emoji) == "🔴":
                    item.label = t(guild, "ANTI_INVITE_BTN_OFF")

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id != self.author_id:
            await interaction.response.send_message(t(interaction.guild, "ANTI_INVITE_NOT_YOURS"), ephemeral=True)
            return False
        return True

    @discord.ui.button(label="Bật", style=discord.ButtonStyle.success, emoji="🟢")
    async def toggle_on(self, interaction: discord.Interaction, button: discord.ui.Button):
        guild_id_str = str(interaction.guild.id)
        if guild_id_str not in link_settings:
            link_settings[guild_id_str] = {}
        link_settings[guild_id_str]["invite_enabled_guild"] = True
        save_settings()
        await interaction.response.send_message(t(interaction.guild, "ANTI_INVITE_TOGGLE_ON_SUCCESS"), ephemeral=True)

    @discord.ui.button(label="Tắt", style=discord.ButtonStyle.danger, emoji="🔴")
    async def toggle_off(self, interaction: discord.Interaction, button: discord.ui.Button):
        guild_id_str = str(interaction.guild.id)
        if guild_id_str not in link_settings:
            link_settings[guild_id_str] = {}
        link_settings[guild_id_str]["invite_enabled_guild"] = False
        save_settings()
        await interaction.response.send_message(t(interaction.guild, "ANTI_INVITE_TOGGLE_OFF_SUCCESS"), ephemeral=True)

class InviteFilterCog(commands.Cog, name="Invite Filter"):
    """Cog để kiểm duyệt và lọc các link mời server Discord khác."""

    def __init__(self, bot: commands.Bot):
        self.bot = bot
        load_invite_data()

    async def handle_violation(self, message: discord.Message, reason: str):
        """Hàm chung để xử lý khi phát hiện vi phạm."""
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
                mute_embed = discord.Embed(title=t(message.guild, "ANTI_INVITE_AUTOMUTE_TITLE"), description=t(message.guild, "ANTI_INVITE_AUTOMUTE_DESC", mention=message.author.mention, limit=warning_limit), color=discord.Color.dark_red())
                await message.channel.send(embed=mute_embed)
                link_warnings[guild_id_str][user_id_str] = 0
            except discord.Forbidden:
                await message.channel.send(t(message.guild, "ANTI_INVITE_MUTE_FORBIDDEN", mention=message.author.mention), delete_after=10)
        else:
            warning_desc = t(message.guild, "ANTI_INVITE_WARN_DESC", mention=message.author.mention, reason=reason)
            if warning_limit > 0:
                warning_desc += t(message.guild, "ANTI_INVITE_WARN_COUNT", cur=user_warnings, limit=warning_limit)
            
            warning_embed = discord.Embed(title=t(message.guild, "ANTI_INVITE_WARN_TITLE"), description=warning_desc, color=discord.Color.orange())
            await message.channel.send(embed=warning_embed, delete_after=15)
            link_warnings[guild_id_str][user_id_str] = user_warnings
        
        save_link_warnings()

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if not message.guild or message.author.bot or not message.content:
            return

        if not global_invite_filter_enabled:
            return
        guild_setting = link_settings.get(str(message.guild.id), {}).get("invite_enabled_guild", False)
        if not guild_setting:
            return

        if message.author.id == OWNER_ID:
            return
        
        guild_admin_roles = admin_roles.get(str(message.guild.id), [])
        user_role_ids = {role.id for role in message.author.roles}
        if any(admin_role_id in user_role_ids for admin_role_id in guild_admin_roles):
            return

        invite_pattern = re.compile(r"(?:discord(?:app)?\.com/invite/|discord\.gg/)([a-zA-Z0-9-]+)")
        invites_found = invite_pattern.findall(message.content)

        if invites_found:
            is_foreign_invite = False
            for code in invites_found:
                try:
                    invite = await self.bot.fetch_invite(code)
                    if invite.guild and invite.guild.id != message.guild.id:
                        is_foreign_invite = True
                        break
                except discord.NotFound:
                    is_foreign_invite = True
                    break
                except Exception as e:
                    print(f"[Invite Filter] Lỗi khi fetch invite '{code}': {e}")
                    continue
            
            if is_foreign_invite:
                await self.handle_violation(message, t(message.guild, "ANTI_INVITE_REASON"))
                return

    @commands.group(name="antiinvite", description="Quản lý hệ thống chống link mời server khác.")
    @has_admin_role()
    async def antiinvite(self, ctx: commands.Context):
        """Lệnh gốc cho nhóm quản lý chống link mời."""
        if ctx.invoked_subcommand is None:
            global_status_text = t(ctx.guild, "ANTI_LINK_STATUS_ON") if global_invite_filter_enabled else t(ctx.guild, "ANTI_LINK_STATUS_OFF")
            guild_setting = link_settings.get(str(ctx.guild.id), {}).get("invite_enabled_guild", False)
            guild_status_text = t(ctx.guild, "ANTI_LINK_STATUS_ON") if guild_setting else t(ctx.guild, "ANTI_LINK_STATUS_OFF")
            
            color = discord.Color.green() if global_invite_filter_enabled and guild_setting else discord.Color.red()
            prefix = ctx.prefix

            embed = discord.Embed(
                title=t(ctx.guild, "ANTI_INVITE_DASHBOARD_TITLE"),
                description=t(ctx.guild, "ANTI_INVITE_DASHBOARD_DESC", global_status=global_status_text, guild_status=guild_status_text),
                color=color
            )
            embed.add_field(
                name=t(ctx.guild, "ANTI_INVITE_FIELD_CMDS"),
                value=t(ctx.guild, "ANTI_INVITE_FIELD_CMDS_VALUE", prefix=prefix),
                inline=False
            )
            view = AntiInviteControlView(ctx.author.id, ctx.guild.id, guild=ctx.guild)
            await ctx.send(embed=embed, view=view, ephemeral=True)

    @antiinvite.command(name="global", description="[Owner] Bật hoặc tắt chống link mời trên toàn bộ bot.")
    @is_owner()
    async def toggle_global(self, ctx: commands.Context, status: Literal["on", "off"]):
        """Bật hoặc tắt hệ thống lọc link mời trên toàn cục."""
        global global_invite_filter_enabled
        if status.lower() == "on":
            global_invite_filter_enabled = True
            msg = t(ctx.guild, "ANTI_INVITE_GLOBAL_ON")
        else:
            global_invite_filter_enabled = False
            msg = t(ctx.guild, "ANTI_INVITE_GLOBAL_OFF")
        save_settings()
        await ctx.send(msg, ephemeral=True)

async def setup(bot: commands.Bot):
    await bot.add_cog(InviteFilterCog(bot))
