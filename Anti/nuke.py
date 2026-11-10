import discord
from discord.ext import commands, tasks
from discord import app_commands
import json
import os
import time
from collections import defaultdict, deque
from typing import Literal, Optional
from Check.i18n import t

# --- Quản lý dữ liệu ---
NUKE_SETTINGS_FILE = "data/nuke_settings.json"
global_nuke_enabled = False

def load_nuke_settings():
    """Tải cài đặt anti-nuke từ file JSON."""
    global global_nuke_enabled
    if os.path.exists(NUKE_SETTINGS_FILE):
        with open(NUKE_SETTINGS_FILE, 'r', encoding='utf-8') as f:
            try:
                settings = json.load(f)
                global_nuke_enabled = settings.get("__global__", {}).get("enabled", False)
                return settings
            except json.JSONDecodeError:
                return {}
    return {}

def save_nuke_settings(settings):
    """Lưu cài đặt anti-nuke vào file JSON."""
    global global_nuke_enabled
    os.makedirs(os.path.dirname(NUKE_SETTINGS_FILE), exist_ok=True)
    settings.setdefault("__global__", {})["enabled"] = global_nuke_enabled
    with open(NUKE_SETTINGS_FILE, 'w', encoding='utf-8') as f:
        json.dump(settings, f, indent=4)

# --- Views & Modals ---
class ThresholdModal(discord.ui.Modal):
    def __init__(self, cog_instance, guild=None):
        super().__init__(title=t(guild, "ANTI_NUKE_MODAL_THRESHOLD_TITLE"))
        self.cog = cog_instance
        self.guild_ref = guild
        self.action_input = discord.ui.TextInput(
            label=t(guild, "ANTI_NUKE_MODAL_ACTION_LABEL"),
            placeholder=t(guild, "ANTI_NUKE_MODAL_ACTION_PLACEHOLDER"),
            required=True
        )
        self.limit_input = discord.ui.TextInput(label=t(guild, "ANTI_NUKE_MODAL_LIMIT_LABEL"), placeholder=t(guild, "ANTI_NUKE_MODAL_LIMIT_PLACEHOLDER"), required=True)
        self.timeframe_input = discord.ui.TextInput(label=t(guild, "ANTI_NUKE_MODAL_TIMEFRAME_LABEL"), placeholder=t(guild, "ANTI_NUKE_MODAL_TIMEFRAME_PLACEHOLDER"), required=True)
        self.add_item(self.action_input)
        self.add_item(self.limit_input)
        self.add_item(self.timeframe_input)

    async def on_submit(self, interaction: discord.Interaction):
        try:
            action = self.action_input.value.lower().strip()
            valid_actions = ["channel_create", "channel_delete", "role_create", "role_delete", "kick", "ban"]
            if action not in valid_actions:
                return await interaction.response.send_message(
                    t(interaction.guild, "ANTI_NUKE_INVALID_ACTION", actions=', '.join(valid_actions)),
                    ephemeral=True
                )

            limit = int(self.limit_input.value)
            timeframe = int(self.timeframe_input.value)

            if limit < 2 or timeframe < 10:
                return await interaction.response.send_message(t(interaction.guild, "ANTI_NUKE_LIMIT_TIME_INVALID"), ephemeral=True)

            config = self.cog.get_guild_settings(interaction.guild_id)
            config["thresholds"][action] = limit
            config["timeframe"] = timeframe
            save_nuke_settings(self.cog.settings)
            await interaction.response.send_message(t(interaction.guild, "ANTI_NUKE_THRESHOLD_SET", action=action, limit=limit, timeframe=timeframe), ephemeral=True)
        except ValueError:
            await interaction.response.send_message(t(interaction.guild, "ANTI_NUKE_VALUE_NOT_INT"), ephemeral=True)

class WhitelistModal(discord.ui.Modal):
    def __init__(self, cog_instance, guild=None):
        super().__init__(title=t(guild, "ANTI_NUKE_WHITELIST_TITLE"))
        self.cog = cog_instance
        self.guild_ref = guild
        self.action_input = discord.ui.TextInput(
            label=t(guild, "ANTI_NUKE_WHITELIST_ACTION_LABEL"),
            placeholder=t(guild, "ANTI_NUKE_WHITELIST_ACTION_PLACEHOLDER"),
            required=True
        )
        self.member_id_input = discord.ui.TextInput(
            label=t(guild, "ANTI_NUKE_WHITELIST_ID_LABEL"),
            placeholder=t(guild, "ANTI_NUKE_WHITELIST_ID_PLACEHOLDER"),
            required=True
        )
        self.add_item(self.action_input)
        self.add_item(self.member_id_input)

    async def on_submit(self, interaction: discord.Interaction):
        action = self.action_input.value.lower().strip()
        if action not in ["add", "remove"]:
            return await interaction.response.send_message(t(interaction.guild, "ANTI_NUKE_WHITELIST_INVALID_ACTION"), ephemeral=True)

        try:
            member_id = int(self.member_id_input.value)
            member = await interaction.guild.fetch_member(member_id)
        except (ValueError, discord.NotFound):
            return await interaction.response.send_message(t(interaction.guild, "ANTI_NUKE_MEMBER_NOT_FOUND"), ephemeral=True)

        config = self.cog.get_guild_settings(interaction.guild_id)
        if action == "add":
            if member.id in config["whitelist"]:
                return await interaction.response.send_message(t(interaction.guild, "ANTI_NUKE_WHITELIST_ALREADY", mention=member.mention), ephemeral=True)
            config["whitelist"].append(member.id)
            await interaction.response.send_message(t(interaction.guild, "ANTI_NUKE_WHITELIST_ADDED", mention=member.mention), ephemeral=True)
        elif action == "remove":
            if member.id not in config["whitelist"]:
                return await interaction.response.send_message(t(interaction.guild, "ANTI_NUKE_WHITELIST_NOT_IN", mention=member.mention), ephemeral=True)
            config["whitelist"].remove(member.id)
            await interaction.response.send_message(t(interaction.guild, "ANTI_NUKE_WHITELIST_REMOVED", mention=member.mention), ephemeral=True)
        
        save_nuke_settings(self.cog.settings)

class AntiNukeControlView(discord.ui.View):
    def __init__(self, author_id: int, cog_instance, guild=None):
        super().__init__(timeout=180)
        self.author_id = author_id
        self.cog = cog_instance
        self.guild_ref = guild
        for item in self.children:
            if isinstance(item, discord.ui.Button):
                if item.emoji and str(item.emoji) == "🟢":
                    item.label = t(guild, "ANTI_NUKE_BTN_ON")
                elif item.emoji and str(item.emoji) == "🔴":
                    item.label = t(guild, "ANTI_NUKE_BTN_OFF")
                elif str(item.emoji) == "📊":
                    item.label = t(guild, "ANTI_NUKE_BTN_THRESHOLD")
                elif str(item.emoji) == "🛡️":
                    item.label = t(guild, "ANTI_NUKE_BTN_WHITELIST")

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id != self.author_id:
            await interaction.response.send_message(t(interaction.guild, "ANTI_NUKE_NOT_YOURS"), ephemeral=True)
            return False
        return True

    async def _update_view(self, interaction: discord.Interaction):
        """Hàm helper để cập nhật lại embed và view sau khi có thay đổi."""
        prefix = "/" # Mặc định cho slash command
        # Tạo lại embed với thông tin mới nhất
        new_embed = self.cog._create_status_embed(interaction.guild, prefix)
        # Cập nhật trạng thái của các nút
        config = self.cog.get_guild_settings(interaction.guild.id)
        self.toggle_on.disabled = config.get("enabled", False)
        self.toggle_off.disabled = not config.get("enabled", False)
        await interaction.response.edit_message(embed=new_embed, view=self)

    @discord.ui.button(label="Bật cho Server", style=discord.ButtonStyle.success, emoji="🟢")
    async def toggle_on(self, interaction: discord.Interaction, button: discord.ui.Button):
        config = self.cog.get_guild_settings(interaction.guild_id)
        config["enabled"] = True
        save_nuke_settings(self.cog.settings)
        await self._update_view(interaction)

    @discord.ui.button(label="Tắt cho Server", style=discord.ButtonStyle.danger, emoji="🔴")
    async def toggle_off(self, interaction: discord.Interaction, button: discord.ui.Button):
        config = self.cog.get_guild_settings(interaction.guild_id)
        config["enabled"] = False
        save_nuke_settings(self.cog.settings)
        await self._update_view(interaction)

    @discord.ui.button(label="Đặt Ngưỡng", style=discord.ButtonStyle.primary, emoji="📊", row=1)
    async def set_threshold(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(ThresholdModal(self.cog, guild=interaction.guild))

    @discord.ui.button(label="Whitelist", style=discord.ButtonStyle.secondary, emoji="🛡️", row=1)
    async def manage_whitelist(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(WhitelistModal(self.cog, guild=interaction.guild))

class AntiNukeActionView(discord.ui.View):
    """View chứa nút khôi phục lại hình phạt."""
    def __init__(self, punished_user_id: int, guild=None):
        super().__init__(timeout=None)
        self.punished_user_id = punished_user_id
        self.guild_ref = guild

    @discord.ui.button(label="Khôi phục (Unban)", style=discord.ButtonStyle.success, emoji="♻️", custom_id="antinuke_unban_button")
    async def unban_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not interaction.user.guild_permissions.ban_members:
            return await interaction.response.send_message(t(interaction.guild, "ANTI_NUKE_NO_BAN_PERM"), ephemeral=True)

        await interaction.response.defer(ephemeral=True)

        try:
            user_to_unban = await interaction.client.fetch_user(self.punished_user_id)
            await interaction.guild.unban(user_to_unban, reason=f"Hành động Anti-Nuke được khôi phục bởi {interaction.user.name}")
            
            original_embed = interaction.message.embeds[0]
            original_embed.title = t(interaction.guild, "ANTI_NUKE_RESTORED_TITLE")
            original_embed.color = discord.Color.green()
            original_embed.add_field(name=t(interaction.guild, "ANTI_NUKE_RESTORED_FIELD"), value=interaction.user.mention, inline=False)
            
            button.disabled = True
            button.label = t(interaction.guild, "ANTI_NUKE_BTN_RESTORED")
            await interaction.message.edit(embed=original_embed, view=self)
            
            await interaction.followup.send(t(interaction.guild, "ANTI_NUKE_UNBANNED_SUCCESS", mention=user_to_unban.mention), ephemeral=True)

        except discord.NotFound:
            await interaction.followup.send(t(interaction.guild, "ANTI_NUKE_UNBAN_NOT_FOUND"), ephemeral=True)
        except Exception as e:
            await interaction.followup.send(t(interaction.guild, "ANTI_NUKE_UNBAN_ERROR", error=e), ephemeral=True)

class AntiNukeCog(commands.Cog, name="Anti-Nuke"):
    """Hệ thống chống phá hoại (nuke) server."""

    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.settings = load_nuke_settings()
        # Cấu trúc: {guild_id: {user_id: {action: deque([timestamps])}}}
        self.action_tracker = defaultdict(lambda: defaultdict(lambda: defaultdict(deque)))

    async def cog_load(self):
        """Đăng ký View persistent khi cog được nạp."""
        self.bot.add_view(AntiNukeActionView(punished_user_id=0)) # Khởi tạo với ID giả

    def _create_status_embed(self, guild: discord.Guild, prefix: str) -> discord.Embed:
        """Hàm tạo embed trạng thái, tách ra để dễ tái sử dụng."""
        config = self.get_guild_settings(guild.id)
        global_status = t(guild, "ANTI_LINK_STATUS_ON") if global_nuke_enabled else t(guild, "ANTI_LINK_STATUS_OFF")
        guild_status = t(guild, "ANTI_LINK_STATUS_ON") if config.get("enabled") else t(guild, "ANTI_LINK_STATUS_OFF")
        log_channel = f"<#{config.get('log_channel')}>" if config.get('log_channel') else t(guild, "ANTI_NUKE_NOT_SET")
        punishment = config.get('punishment', 'ban').title()

        embed = discord.Embed(title=t(guild, "ANTI_NUKE_DASHBOARD_TITLE"), color=discord.Color.blue())
        embed.description = t(guild, "ANTI_NUKE_DASHBOARD_DESC", global_status=global_status, guild_status=guild_status)
        embed.add_field(name=t(guild, "ANTI_NUKE_FIELD_LOG"), value=log_channel, inline=True)
        embed.add_field(name=t(guild, "ANTI_NUKE_FIELD_PUNISH"), value=f"`{punishment}`", inline=True)
        embed.add_field(
            name=t(guild, "ANTI_NUKE_FIELD_GUIDE"),
            value=t(guild, "ANTI_NUKE_FIELD_GUIDE_VALUE", prefix=prefix),
            inline=False
        )
        return embed

    def get_guild_settings(self, guild_id: int) -> dict:
        """Lấy cài đặt cho một server, nếu không có thì dùng mặc định."""
        guild_id_str = str(guild_id)
        defaults = {
            "enabled": False,
            "log_channel": None,
            "punishment": "ban",
            "whitelist": [],
            "thresholds": {
                "channel_create": 5,
                "channel_delete": 5,
                "role_create": 5,
                "role_delete": 5,
                "kick": 5,
                "ban": 5
            },
            "timeframe": 60  # 60 giây
        }
        if guild_id_str not in self.settings:
            self.settings[guild_id_str] = defaults
        # Đảm bảo các key mặc định tồn tại nếu file config cũ
        for key, value in defaults.items():
            self.settings[guild_id_str].setdefault(key, value)
        return self.settings[guild_id_str]

    async def _check_actions(self, guild: discord.Guild, member: discord.Member, action: str):
        """Kiểm tra và xử lý nếu một hành động vượt ngưỡng cho phép."""
        if not guild or not member or not getattr(guild, "id", None):
            return

        # Kiểm tra công tắc toàn cục trước
        if not global_nuke_enabled:
            return

        config = self.get_guild_settings(guild.id)
        perms = getattr(member, "guild_permissions", None)
        is_admin = perms.administrator if perms else False
        if not config.get("enabled") or member.id == self.bot.user.id or member.id == guild.owner_id or is_admin:
            return

        # Kiểm tra whitelist
        if member.id in config.get("whitelist", []):
            return

        current_time = time.time()
        timeframe = config.get("timeframe", 60)
        
        # Dọn dẹp các hành động cũ
        user_actions = self.action_tracker[guild.id][member.id][action]
        while user_actions and user_actions[0] < current_time - timeframe:
            user_actions.popleft()

        # Ghi nhận hành động mới và kiểm tra
        user_actions.append(current_time)
        threshold = config.get("thresholds", {}).get(action, 5)

        if len(user_actions) >= threshold:
            # Vượt ngưỡng, thực hiện hình phạt
            await self._punish(guild, member, action, len(user_actions), timeframe)
            # Xóa tracker của user này để tránh phạt liên tục
            self.action_tracker[guild.id][member.id][action].clear()

    async def _punish(self, guild: discord.Guild, member: discord.Member, action: str, count: int, timeframe: int):
        """Thực thi hình phạt và gửi log."""
        if not guild or not member:
            return
        config = self.get_guild_settings(guild.id)
        punishment = config.get("punishment", "ban")
        reason = f"Anti-Nuke: Vượt ngưỡng cho phép ({count} lần {action.replace('_', ' ')} trong {timeframe}s)."

        try:
            if punishment == "ban":
                if hasattr(member, "ban"):
                    await member.ban(reason=reason)
                else:
                    await guild.ban(member, reason=reason)
            elif punishment == "kick":
                if hasattr(member, "kick"):
                    await member.kick(reason=reason)
                else:
                    await guild.kick(member, reason=reason)
        except (discord.Forbidden, discord.NotFound, discord.HTTPException) as e:
            gname = getattr(guild, "name", str(guild.id))
            print(f"[Anti-Nuke] Không thể phạt {member} trong server {gname}: {e}")
        except Exception as e:
            print(f"[Anti-Nuke] Lỗi khi phạt {member}: {e}")

        # Gửi log
        log_channel_id = config.get("log_channel")
        if log_channel_id:
            log_channel = guild.get_channel(log_channel_id)
            if log_channel:
                try:
                    embed = discord.Embed(
                        title=t(guild, "ANTI_NUKE_ALERT_TITLE"),
                        description=t(guild, "ANTI_NUKE_ALERT_DESC"),
                        color=discord.Color.dark_red()
                    )
                    embed.add_field(name=t(guild, "ANTI_NUKE_FIELD_SUSPECT"), value=f"{member.mention} (`{member.id}`)", inline=False)
                    embed.add_field(name=t(guild, "ANTI_NUKE_FIELD_ACTION"), value=f"`{action.replace('_', ' ').title()}`", inline=True)
                    embed.add_field(name=t(guild, "ANTI_NUKE_FIELD_COUNT"), value=f"`{count} lần / {timeframe} giây`", inline=True)
                    embed.add_field(name=t(guild, "ANTI_NUKE_FIELD_PUNISHMENT"), value=f"`{punishment.title()}`", inline=True)
                    embed.set_footer(text=t(guild, "ANTI_NUKE_FOOTER"))
                    embed.timestamp = discord.utils.utcnow()
                    
                    view_to_send = AntiNukeActionView(member.id, guild=guild) if punishment == "ban" else None
                    if view_to_send:
                        for item in view_to_send.children:
                            if isinstance(item, discord.ui.Button):
                                item.label = t(guild, "ANTI_NUKE_BTN_UNBAN")
                    
                    await log_channel.send(embed=embed, view=view_to_send)
                except Exception:
                    pass

    async def _get_latest_audit_entry(self, guild, action):
        """Lấy bản ghi audit log gần nhất một cách an toàn."""
        if not guild:
            return None
        me = getattr(guild, "me", None)
        if not me or not getattr(me, "guild_permissions", None) or not me.guild_permissions.view_audit_log:
            return None
        try:
            async for entry in guild.audit_logs(limit=1, action=action):
                return entry
        except (discord.NotFound, discord.Forbidden, discord.HTTPException):
            return None
        except Exception:
            return None
        return None

    # --- Listeners cho các sự kiện ---
    @commands.Cog.listener()
    async def on_guild_channel_create(self, channel):
        guild = getattr(channel, "guild", None)
        entry = await self._get_latest_audit_entry(guild, discord.AuditLogAction.channel_create)
        if entry and getattr(entry, "user", None):
            await self._check_actions(guild, entry.user, "channel_create")

    @commands.Cog.listener()
    async def on_guild_channel_delete(self, channel):
        guild = getattr(channel, "guild", None)
        entry = await self._get_latest_audit_entry(guild, discord.AuditLogAction.channel_delete)
        if entry and getattr(entry, "user", None):
            await self._check_actions(guild, entry.user, "channel_delete")

    @commands.Cog.listener()
    async def on_member_ban(self, guild, user):
        entry = await self._get_latest_audit_entry(guild, discord.AuditLogAction.ban)
        if entry and getattr(entry, "user", None):
            await self._check_actions(guild, entry.user, "ban")

    @commands.Cog.listener()
    async def on_member_remove(self, member):
        guild = getattr(member, "guild", None)
        entry = await self._get_latest_audit_entry(guild, discord.AuditLogAction.kick)
        if entry and getattr(entry, "target", None) and entry.target.id == member.id and getattr(entry, "user", None):
            await self._check_actions(guild, entry.user, "kick")

    @commands.Cog.listener()
    async def on_guild_role_create(self, role):
        guild = getattr(role, "guild", None)
        entry = await self._get_latest_audit_entry(guild, discord.AuditLogAction.role_create)
        if entry and getattr(entry, "user", None):
            await self._check_actions(guild, entry.user, "role_create")

    @commands.Cog.listener()
    async def on_guild_role_delete(self, role):
        guild = getattr(role, "guild", None)
        entry = await self._get_latest_audit_entry(guild, discord.AuditLogAction.role_delete)
        if entry and getattr(entry, "user", None):
            await self._check_actions(guild, entry.user, "role_delete")

    # --- Lệnh quản lý (Prefix) ---
    @commands.group(name="antinuke", description="Quản lý hệ thống chống phá hoại server.")
    @commands.has_permissions(administrator=True)
    async def antinuke(self, ctx: commands.Context):
        """Lệnh gốc cho nhóm anti-nuke."""
        if ctx.invoked_subcommand is None:
            prefix = ctx.prefix if ctx.prefix else "/"
            embed = self._create_status_embed(ctx.guild, prefix)
            view = AntiNukeControlView(ctx.author.id, self, guild=ctx.guild)
            config = self.get_guild_settings(ctx.guild.id)
            view.toggle_on.disabled = config.get("enabled", False)
            view.toggle_off.disabled = not config.get("enabled", False)
            await ctx.send(embed=embed, view=view, ephemeral=True)

    @antinuke.command(name="global", description="[Owner] Bật hoặc tắt hệ thống Anti-Nuke trên toàn bộ bot.")
    @commands.is_owner()
    async def antinuke_global(self, ctx: commands.Context, status: Literal["on", "off"]):
        """Bật/tắt hệ thống Anti-Nuke toàn cục."""
        global global_nuke_enabled
        global_nuke_enabled = (status.lower() == "on")
        save_nuke_settings(self.settings)
        await ctx.send(t(ctx.guild, "ANTI_NUKE_GLOBAL_ON", status=status.upper()), ephemeral=True)

    @antinuke.command(name="toggle", description="Bật hoặc tắt hệ thống Anti-Nuke.")
    @app_commands.describe(status="Chọn 'on' để bật hoặc 'off' để tắt.")
    @commands.has_permissions(administrator=True)
    async def toggle(self, ctx: commands.Context, status: Literal["on", "off"]):
        """Bật/tắt hệ thống Anti-Nuke."""
        config = self.get_guild_settings(ctx.guild.id)
        config["enabled"] = (status.lower() == "on")
        save_nuke_settings(self.settings)
        msg = t(ctx.guild, "ANTI_NUKE_TOGGLE_SUCCESS", status=status.upper())
        await ctx.send(msg, ephemeral=True)

    @antinuke.command(name="logchannel", description="Thiết lập kênh để gửi cảnh báo Anti-Nuke.")
    @app_commands.describe(channel="Kênh bạn muốn dùng để log.")
    @commands.has_permissions(administrator=True)
    async def logchannel(self, ctx: commands.Context, channel: discord.TextChannel):
        """Thiết lập kênh log."""
        config = self.get_guild_settings(ctx.guild.id)
        config["log_channel"] = channel.id
        save_nuke_settings(self.settings)
        await ctx.send(t(ctx.guild, "ANTI_NUKE_LOG_SET", channel=channel.mention), ephemeral=True)

    @antinuke.command(name="punishment", description="Chọn hình phạt khi phát hiện vi phạm.")
    @app_commands.describe(action="Chọn hình phạt: ban hoặc kick.")
    @commands.has_permissions(administrator=True)
    async def punishment(self, ctx: commands.Context, action: Literal["ban", "kick"]):
        """Thiết lập hình phạt."""
        config = self.get_guild_settings(ctx.guild.id)
        config["punishment"] = action.lower()
        save_nuke_settings(self.settings)
        await ctx.send(t(ctx.guild, "ANTI_NUKE_PUNISH_SET", punishment=action.title()), ephemeral=True)

    @antinuke.command(name="threshold", description="Đặt ngưỡng cho một hành động cụ thể.")
    @app_commands.describe(
        action="Hành động bạn muốn đặt ngưỡng.",
        limit="Số lần thực hiện tối đa trong khung thời gian.",
        timeframe="Khung thời gian (giây) để theo dõi (mặc định 60s)."
    )
    @app_commands.choices(action=[
        app_commands.Choice(name="Tạo Kênh", value="channel_create"),
        app_commands.Choice(name="Xóa Kênh", value="channel_delete"),
        app_commands.Choice(name="Tạo Role", value="role_create"),
        app_commands.Choice(name="Xóa Role", value="role_delete"),
        app_commands.Choice(name="Kick Thành Viên", value="kick"),
        app_commands.Choice(name="Ban Thành Viên", value="ban"),
    ])
    @commands.has_permissions(administrator=True)
    async def threshold(self, ctx: commands.Context, action: app_commands.Choice[str], limit: int, timeframe: Optional[int] = 60):
        """Thiết lập ngưỡng cho các hành động."""
        if limit < 2 or timeframe < 10:
            return await ctx.send(t(ctx.guild, "ANTI_NUKE_THRESHOLD_INVALID"), ephemeral=True)
        
        config = self.get_guild_settings(ctx.guild.id)
        config["thresholds"][action.value] = limit
        config["timeframe"] = timeframe
        save_nuke_settings(self.settings)
        await ctx.send(t(ctx.guild, "ANTI_NUKE_THRESHOLD_SUCCESS", name=action.name, limit=limit, timeframe=timeframe), ephemeral=True)

    @antinuke.command(name="whitelist", description="Thêm hoặc xóa người dùng khỏi danh sách trắng (miễn nhiễm).")
    @app_commands.describe(
        action="Chọn 'add' để thêm hoặc 'remove' để xóa.",
        member="Thành viên bạn muốn thêm/xóa."
    )
    @commands.has_permissions(administrator=True)
    async def whitelist(self, ctx: commands.Context, action: Literal["add", "remove"], member: discord.Member):
        """Quản lý danh sách trắng."""
        config = self.get_guild_settings(ctx.guild.id)
        
        if action == "add":
            if member.id in config["whitelist"]:
                return await ctx.send(t(ctx.guild, "ANTI_NUKE_WHITELIST_ALREADY", mention=member.mention), ephemeral=True)
            config["whitelist"].append(member.id)
            await ctx.send(t(ctx.guild, "ANTI_NUKE_WHITELIST_ADD_SUCCESS", mention=member.mention), ephemeral=True)
        else: # remove
            if member.id not in config["whitelist"]:
                return await ctx.send(t(ctx.guild, "ANTI_NUKE_WHITELIST_NOT_IN", mention=member.mention), ephemeral=True)
            config["whitelist"].remove(member.id)
            await ctx.send(t(ctx.guild, "ANTI_NUKE_WHITELIST_REMOVE_SUCCESS", mention=member.mention), ephemeral=True)
            
        save_nuke_settings(self.settings)

async def setup(bot: commands.Bot):
    await bot.add_cog(AntiNukeCog(bot))
