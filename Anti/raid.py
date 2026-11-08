import discord
from discord.ext import commands, tasks
from discord import app_commands
import json
import os
import time
from collections import deque
from typing import Literal, Optional
from Checks_vi.i18n import t

# --- Quản lý dữ liệu ---
RAID_SETTINGS_FILE = "data/raid_settings.json"
global_raid_enabled = False

def load_raid_settings():
    """Tải cài đặt anti-raid từ file JSON."""
    global global_raid_enabled
    if os.path.exists(RAID_SETTINGS_FILE):
        with open(RAID_SETTINGS_FILE, 'r', encoding='utf-8') as f:
            try:
                settings = json.load(f)
                global_raid_enabled = settings.get("__global__", {}).get("enabled", False)
                return settings
            except json.JSONDecodeError:
                return {}
    return {}

def save_raid_settings(settings):
    """Lưu cài đặt anti-raid vào file JSON."""
    global global_raid_enabled
    os.makedirs(os.path.dirname(RAID_SETTINGS_FILE), exist_ok=True)
    settings.setdefault("__global__", {})["enabled"] = global_raid_enabled
    with open(RAID_SETTINGS_FILE, 'w', encoding='utf-8') as f:
        json.dump(settings, f, indent=4)

class AntiRaidControlView(discord.ui.View):
    def __init__(self, author_id: int, cog_instance, guild=None):
        super().__init__(timeout=180)
        self.author_id = author_id
        self.cog = cog_instance
        for item in self.children:
            if isinstance(item, discord.ui.Button):
                if item.emoji and str(item.emoji) == "🟢":
                    item.label = t(guild, "ANTI_RAID_BTN_ON")
                elif item.emoji and str(item.emoji) == "🔴":
                    item.label = t(guild, "ANTI_RAID_BTN_OFF")

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id != self.author_id:
            await interaction.response.send_message(t(interaction.guild, "ANTI_RAID_NOT_YOURS"), ephemeral=True)
            return False
        return True

    async def _update_view(self, interaction: discord.Interaction):
        """Hàm helper để cập nhật lại embed và view sau khi có thay đổi."""
        prefix = "/" # Mặc định cho slash command
        new_embed = self.cog._create_status_embed(interaction.guild, prefix)
        config = self.cog.get_guild_settings(interaction.guild.id)
        self.toggle_on.disabled = config.get("enabled", False)
        self.toggle_off.disabled = not config.get("enabled", False)
        await interaction.response.edit_message(embed=new_embed, view=self)

    @discord.ui.button(label="Bật cho Server", style=discord.ButtonStyle.success, emoji="🟢")
    async def toggle_on(self, interaction: discord.Interaction, button: discord.ui.Button):
        config = self.cog.get_guild_settings(interaction.guild_id)
        config["enabled"] = True
        save_raid_settings(self.cog.settings)
        await self._update_view(interaction)

    @discord.ui.button(label="Tắt cho Server", style=discord.ButtonStyle.danger, emoji="🔴")
    async def toggle_off(self, interaction: discord.Interaction, button: discord.ui.Button):
        config = self.cog.get_guild_settings(interaction.guild_id)
        config["enabled"] = False
        save_raid_settings(self.cog.settings)
        await self._update_view(interaction)

class AntiRaidActionView(discord.ui.View):
    """View chứa nút khôi phục lại hình phạt."""
    def __init__(self, punished_user_id: int, guild=None):
        super().__init__(timeout=None)
        self.punished_user_id = punished_user_id
        for item in self.children:
            if isinstance(item, discord.ui.Button):
                item.label = t(guild, "ANTI_RAID_BTN_UNBAN")

    @discord.ui.button(label="Khôi phục (Unban)", style=discord.ButtonStyle.success, emoji="♻️", custom_id="antiraid_unban_button")
    async def unban_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not interaction.user.guild_permissions.ban_members:
            return await interaction.response.send_message(t(interaction.guild, "ANTI_RAID_NO_BAN_PERM"), ephemeral=True)

        await interaction.response.defer(ephemeral=True)

        try:
            user_to_unban = await interaction.client.fetch_user(self.punished_user_id)
            await interaction.guild.unban(user_to_unban, reason=f"Hành động Anti-Raid được khôi phục bởi {interaction.user.name}")
            
            original_embed = interaction.message.embeds[0]
            original_embed.title = t(interaction.guild, "ANTI_RAID_RESTORED_TITLE")
            original_embed.color = discord.Color.green()
            original_embed.add_field(name=t(interaction.guild, "ANTI_RAID_RESTORED_FIELD"), value=interaction.user.mention, inline=False)
            
            button.disabled = True
            button.label = t(interaction.guild, "ANTI_RAID_BTN_RESTORED")
            await interaction.message.edit(embed=original_embed, view=self)
            
            await interaction.followup.send(t(interaction.guild, "ANTI_RAID_UNBANNED_SUCCESS", mention=user_to_unban.mention), ephemeral=True)

        except discord.NotFound:
            await interaction.followup.send(t(interaction.guild, "ANTI_RAID_UNBAN_NOT_FOUND"), ephemeral=True)
        except Exception as e:
            await interaction.followup.send(t(interaction.guild, "ANTI_RAID_UNBAN_ERROR", error=e), ephemeral=True)

class AntiRaidCog(commands.Cog, name="Anti-Raid"):
    """Hệ thống chống tấn công (raid) bằng cách tham gia hàng loạt."""

    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.settings = load_raid_settings() # type: ignore
        # Cấu trúc: {guild_id: deque([timestamp])}
        self.join_tracker = {}

    def get_guild_settings(self, guild_id: int) -> dict:
        """Lấy cài đặt cho một server, nếu không có thì dùng mặc định."""
        guild_id_str = str(guild_id)
        defaults = {
            "enabled": False,
            "log_channel": None,
            "punishment": "kick",
            "join_limit": 10,
            "timeframe": 15  # 10 người trong 15 giây
        }
        if guild_id_str not in self.settings:
            self.settings[guild_id_str] = defaults
        for key, value in defaults.items():
            self.settings[guild_id_str].setdefault(key, value)
        return self.settings[guild_id_str]

    def _create_status_embed(self, guild: discord.Guild, prefix: str) -> discord.Embed:
        """Hàm tạo embed trạng thái, tách ra để dễ tái sử dụng."""
        config = self.get_guild_settings(guild.id)
        global_status = t(guild, "ANTI_LINK_STATUS_ON") if global_raid_enabled else t(guild, "ANTI_LINK_STATUS_OFF")
        guild_status = t(guild, "ANTI_LINK_STATUS_ON") if config.get("enabled") else t(guild, "ANTI_LINK_STATUS_OFF")
        log_channel = f"<#{config.get('log_channel')}>" if config.get('log_channel') else t(guild, "ANTI_RAID_NOT_SET")
        punishment = config.get('punishment', 'kick').title()
        threshold = f"{config.get('join_limit')} người / {config.get('timeframe')} giây"

        embed = discord.Embed(title=t(guild, "ANTI_RAID_DASHBOARD_TITLE"), color=discord.Color.blue())
        embed.description = t(guild, "ANTI_RAID_DASHBOARD_DESC", global_status=global_status, guild_status=guild_status)
        embed.add_field(name=t(guild, "ANTI_RAID_FIELD_LOG"), value=log_channel, inline=False)
        embed.add_field(name=t(guild, "ANTI_RAID_FIELD_PUNISH"), value=f"`{punishment}`", inline=True)
        embed.add_field(name=t(guild, "ANTI_RAID_FIELD_THRESHOLD"), value=f"`{threshold}`", inline=True)
        embed.add_field(name=t(guild, "ANTI_RAID_FIELD_CMDS"), value=t(guild, "ANTI_RAID_FIELD_CMDS_VALUE", prefix=prefix), inline=False)
        return embed

    @commands.Cog.listener()
    async def on_member_join(self, member: discord.Member):
        """Sự kiện khi có thành viên mới tham gia server."""
        guild = member.guild
        config = self.get_guild_settings(guild.id)

        if not config.get("enabled"):
            return

        current_time = time.time()
        timeframe = config.get("timeframe", 15) # type: ignore

        if guild.id not in self.join_tracker:
            self.join_tracker[guild.id] = deque()

        # Dọn dẹp các lượt tham gia cũ
        join_queue = self.join_tracker[guild.id] # type: ignore
        while join_queue and join_queue[0] < current_time - timeframe:
            join_queue.popleft()

        # Ghi nhận lượt tham gia mới
        join_queue.append(current_time)

        # Kiểm tra nếu vượt ngưỡng
        join_limit = config.get("join_limit", 10) # type: ignore
        if len(join_queue) >= join_limit:
            # Kích hoạt chế độ raid
            await self._handle_raid(guild, member)
            # Xóa tracker để tránh phạt liên tục
            self.join_tracker[guild.id].clear()

    async def _handle_raid(self, guild: discord.Guild, member: discord.Member):
        """Xử lý khi phát hiện raid."""
        config = self.get_guild_settings(guild.id)
        punishment = config.get("punishment", "kick") # type: ignore
        reason = "Anti-Raid: Phát hiện tham gia hàng loạt."

        try:
            if punishment == "kick":
                await member.kick(reason=reason)
            elif punishment == "ban":
                await member.ban(reason=reason)
        except discord.Forbidden:
            print(f"[Anti-Raid] Không thể phạt {member} trong server {guild.name} do thiếu quyền.")
        except Exception as e:
            print(f"[Anti-Raid] Lỗi khi phạt {member}: {e}")

        # Gửi log
        log_channel_id = config.get("log_channel") # type: ignore
        if log_channel_id:
            log_channel = guild.get_channel(log_channel_id)
            if log_channel:
                embed = discord.Embed(
                    title=t(guild, "ANTI_RAID_ALERT_TITLE"),
                    description=t(guild, "ANTI_RAID_ALERT_DESC"),
                    color=discord.Color.dark_red()
                )
                embed.add_field(name=t(guild, "ANTI_RAID_FIELD_MEMBER"), value=f"{member.mention} (`{member.id}`)", inline=False) # type: ignore
                embed.add_field(name=t(guild, "ANTI_RAID_FIELD_COUNT"), value=f"`{len(self.join_tracker.get(guild.id, []))} người / {config.get('timeframe')} giây`", inline=True) # type: ignore
                embed.add_field(name=t(guild, "ANTI_RAID_FIELD_PUNISHMENT"), value=f"`{punishment.title()}`", inline=True) # type: ignore
                embed.set_footer(text=t(guild, "ANTI_RAID_FOOTER"))
                embed.timestamp = discord.utils.utcnow()
                view_to_send = AntiRaidActionView(member.id, guild=guild) if punishment == "ban" else None
                
                await log_channel.send(embed=embed, view=view_to_send)

    # --- Lệnh quản lý (Prefix) ---
    @commands.group(name="antiraid", description="Quản lý hệ thống chống tấn công (raid).")
    @commands.has_permissions(administrator=True)
    async def antiraid(self, ctx: commands.Context):
        """Lệnh gốc cho nhóm anti-raid."""
        if ctx.invoked_subcommand is None:
            prefix = ctx.prefix if ctx.prefix else "/"
            embed = self._create_status_embed(ctx.guild, prefix)
            view = AntiRaidControlView(ctx.author.id, self, guild=ctx.guild)
            config = self.get_guild_settings(ctx.guild.id)
            view.toggle_on.disabled = config.get("enabled", False)
            view.toggle_off.disabled = not config.get("enabled", False)
            await ctx.send(embed=embed, view=view, ephemeral=True)

    @antiraid.command(name="global", description="[Owner] Bật hoặc tắt hệ thống Anti-Raid trên toàn bộ bot.")
    @commands.is_owner()
    async def antiraid_global(self, ctx: commands.Context, status: Literal["on", "off"]):
        """Bật/tắt hệ thống Anti-Raid toàn cục."""
        global global_raid_enabled
        global_raid_enabled = (status.lower() == "on")
        save_raid_settings(self.settings)
        await ctx.send(t(ctx.guild, "ANTI_RAID_GLOBAL_ON", status=status.upper()), ephemeral=True)

    @antiraid.command(name="toggle", description="Bật hoặc tắt hệ thống Anti-Raid.")
    @app_commands.describe(status="Chọn 'on' để bật hoặc 'off' để tắt.")
    async def toggle(self, ctx: commands.Context, status: Literal["on", "off"]):
        """Bật/tắt hệ thống Anti-Raid."""
        config = self.get_guild_settings(ctx.guild.id)
        config["enabled"] = (status.lower() == "on")
        save_raid_settings(self.settings)
        await ctx.send(t(ctx.guild, "ANTI_RAID_TOGGLE_SUCCESS", status=status.upper()), ephemeral=True)

    @antiraid.command(name="logchannel", description="Thiết lập kênh để gửi cảnh báo Anti-Raid.")
    @app_commands.describe(channel="Kênh bạn muốn dùng để log.")
    async def logchannel(self, ctx: commands.Context, channel: discord.TextChannel):
        """Thiết lập kênh log."""
        config = self.get_guild_settings(ctx.guild.id)
        config["log_channel"] = channel.id
        save_raid_settings(self.settings)
        await ctx.send(t(ctx.guild, "ANTI_RAID_LOG_SET", channel=channel.mention), ephemeral=True)

    @antiraid.command(name="punishment", description="Chọn hình phạt khi phát hiện raid.")
    @app_commands.describe(action="Chọn hình phạt: kick hoặc ban.")
    async def punishment(self, ctx: commands.Context, action: Literal["kick", "ban"]):
        """Thiết lập hình phạt."""
        config = self.get_guild_settings(ctx.guild.id)
        config["punishment"] = action.lower()
        save_raid_settings(self.settings)
        await ctx.send(t(ctx.guild, "ANTI_RAID_PUNISH_SET", punishment=action.title()), ephemeral=True)

    @antiraid.command(name="threshold", description="Đặt ngưỡng phát hiện raid.")
    @app_commands.describe(
        limit="Số lượng người tham gia tối đa.",
        timeframe="Khung thời gian (giây) để theo dõi."
    )
    async def threshold(self, ctx: commands.Context, limit: int, timeframe: int):
        """Thiết lập ngưỡng phát hiện raid."""
        if limit < 3 or timeframe < 5:
            return await ctx.send(t(ctx.guild, "ANTI_RAID_THRESHOLD_INVALID"), ephemeral=True)
        
        config = self.get_guild_settings(ctx.guild.id)
        config["join_limit"] = limit
        config["timeframe"] = timeframe
        save_raid_settings(self.settings)
        await ctx.send(t(ctx.guild, "ANTI_RAID_THRESHOLD_SUCCESS", limit=limit, timeframe=timeframe), ephemeral=True)

async def setup(bot: commands.Bot):
    await bot.add_cog(AntiRaidCog(bot))
