import discord
from discord import app_commands
from discord.ext import commands
import os
import copy
from datetime import datetime
from Check.i18n import t

# Import các hàm và biến quản lý dữ liệu tập trung
from Check.data import save_data, guild_settings, get_guild_settings

class SetupCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    setup = app_commands.Group(name="setup", description="Thiết lập các tính năng hệ thống cho Server")

    @setup.command(name="config", description="Cấu hình tin nhắn chào mừng/tạm biệt thành viên.")
    @app_commands.describe(
        tinh_nang="Chọn tính năng bạn muốn cấu hình",
        trang_thai="Bật hoặc Tắt tính năng đã chọn",
        kenh_gui="Kênh để gửi tin nhắn (Mặc định: Kênh hệ thống)"
    )
    @app_commands.choices(tinh_nang=[
        app_commands.Choice(name="Chào mừng (Welcome)", value="welcome"),
        app_commands.Choice(name="Tạm biệt (Leave)", value="leave"),
        app_commands.Choice(name="Cảm ơn Boost", value="boost"),
    ])
    @app_commands.checks.has_permissions(manage_guild=True)
    async def setup_config(
        self, 
        interaction: discord.Interaction, 
        tinh_nang: app_commands.Choice[str],
        trang_thai: bool, 
        kenh_gui: discord.TextChannel = None
    ):
        await interaction.response.defer(ephemeral=True)
        guild = interaction.guild
        guild_id = str(guild.id)
        
        settings = get_guild_settings(guild_id)
        
        if tinh_nang.value == "welcome":
            settings["welcome"] = trang_thai
            settings["welcome_channel"] = kenh_gui.id if kenh_gui else None
            title = t(guild, "LOG_SETUP_TITLE_WELCOME")
        elif tinh_nang.value == "leave":
            settings["goodbye"] = trang_thai
            settings["leave_channel"] = kenh_gui.id if kenh_gui else None
            title = t(guild, "LOG_SETUP_TITLE_LEAVE")
        elif tinh_nang.value == "boost":
            settings["boost_message"] = trang_thai
            settings["boost_channel"] = kenh_gui.id if kenh_gui else None
            title = t(guild, "LOG_SETUP_TITLE_BOOST")
            
        save_data()
        
        status_text = t(guild, "LOG_SETUP_STATUS_ON") if trang_thai else t(guild, "LOG_SETUP_STATUS_OFF")
        channel_text = kenh_gui.mention if kenh_gui else t(guild, "LOG_SETUP_CHANNEL_DEFAULT", channel=interaction.guild.system_channel)
        
        embed = discord.Embed(
            title=title,
            description=f"**{t(guild, 'LOG_SETUP_FIELD_FEATURE')}:** `{tinh_nang.name}`\n**{t(guild, 'LOG_SETUP_FIELD_STATUS')}:** {status_text}\n**{t(guild, 'LOG_SETUP_FIELD_CHANNEL')}:** {channel_text}",
            color=discord.Color.green() if trang_thai else discord.Color.red()
        )
        await interaction.followup.send(embed=embed)

    @setup.command(name="view", description="Kiểm tra các cài đặt hiện tại của hệ thống join/leave.")
    @app_commands.checks.has_permissions(manage_guild=True)
    async def view_settings(self, interaction: discord.Interaction):
        guild = interaction.guild
        settings = get_guild_settings(guild.id)

        welcome_status = t(guild, "LOG_SETUP_VIEW_STATUS_ON") if settings.get("welcome", True) else t(guild, "LOG_SETUP_VIEW_STATUS_OFF")
        welcome_channel_id = settings.get("welcome_channel")
        welcome_channel = guild.get_channel(welcome_channel_id) if welcome_channel_id else guild.system_channel
        welcome_channel_text = welcome_channel.mention if welcome_channel else t(guild, "LOG_SETUP_VIEW_NO_CHANNEL")

        leave_status = t(guild, "LOG_SETUP_VIEW_STATUS_ON") if settings.get("goodbye", True) else t(guild, "LOG_SETUP_VIEW_STATUS_OFF")
        leave_channel_id = settings.get("leave_channel")
        leave_channel = guild.get_channel(leave_channel_id) if leave_channel_id else guild.system_channel
        leave_channel_text = leave_channel.mention if leave_channel else t(guild, "LOG_SETUP_VIEW_NO_CHANNEL")

        boost_status = t(guild, "LOG_SETUP_VIEW_STATUS_ON") if settings.get("boost_message", True) else t(guild, "LOG_SETUP_VIEW_STATUS_OFF")
        boost_channel_id = settings.get("boost_channel")
        boost_channel = guild.get_channel(boost_channel_id) if boost_channel_id else guild.system_channel
        boost_channel_text = boost_channel.mention if boost_channel else t(guild, "LOG_SETUP_VIEW_NO_CHANNEL")

        embed = discord.Embed(title=t(guild, "LOG_SETUP_VIEW_TITLE", guild=guild.name), color=discord.Color.blue())
        embed.add_field(name=t(guild, "LOG_SETUP_VIEW_FIELD_WELCOME"), value=t(guild, "LOG_SETUP_VIEW_VALUE", status=welcome_status, channel=welcome_channel_text), inline=False)
        embed.add_field(name=t(guild, "LOG_SETUP_VIEW_FIELD_LEAVE"), value=t(guild, "LOG_SETUP_VIEW_VALUE", status=leave_status, channel=leave_channel_text), inline=False)
        embed.add_field(name=t(guild, "LOG_SETUP_VIEW_FIELD_BOOST"), value=t(guild, "LOG_SETUP_VIEW_VALUE", status=boost_status, channel=boost_channel_text), inline=False)
        await interaction.response.send_message(embed=embed, ephemeral=True)

    @setup.command(name="test", description="Kiểm tra tin nhắn chào mừng/tạm biệt (giả lập).")
    @app_commands.describe(hanh_dong="Chọn hành động để kiểm tra")
    @app_commands.choices(hanh_dong=[
        app_commands.Choice(name="👋 Giả lập thành viên tham gia (Join)", value="join"),
        app_commands.Choice(name="🚪 Giả lập thành viên rời đi (Leave)", value="leave"),
        app_commands.Choice(name="💖 Giả lập có người boost (Boost)", value="boost"),
    ])
    @app_commands.checks.has_permissions(manage_guild=True)
    async def test_joinleave(self, interaction: discord.Interaction, hanh_dong: app_commands.Choice[str]):
        await interaction.response.send_message(t(interaction.guild, "LOG_SETUP_TEST_SENDING", action=hanh_dong.name), ephemeral=True)
        
        if hanh_dong.value == "join":
            self.bot.dispatch("member_join", interaction.user)
        elif hanh_dong.value == "leave":
            self.bot.dispatch("member_leave", interaction.user)
        elif hanh_dong.value == "boost":
            before_member = copy.copy(interaction.user)
            before_member.premium_since = None
            self.bot.dispatch("member_update", before_member, interaction.user)


async def setup(bot: commands.Bot):
    await bot.add_cog(SetupCog(bot))
