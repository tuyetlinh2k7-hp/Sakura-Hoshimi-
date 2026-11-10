import discord
from discord.ext import commands
from discord import app_commands
import json
import os
from datetime import timedelta, datetime
from collections import deque
from typing import Literal
import re
from Check.i18n import t

# Import các hàm kiểm tra và biến cấu hình cần thiết
from config import OWNER_ID
from Check.mod import has_admin_role, is_owner, admin_roles
# Import các biến và hàm từ link_filter để dùng chung hệ thống cảnh cáo
from Anti.link_filter import link_warnings, link_settings, save_link_warnings, load_link_data


# --- Quản lý dữ liệu ---
SPAM_SETTINGS_FILE = "data/spam_settings.json"

# Cấu trúc: {guild_id: {user_id: deque([(timestamp, message_id, content), ...])}}
user_message_history = {}
spam_settings = {}
global_spam_filter_enabled = False

def load_spam_data():
    """Tải cài đặt chống spam từ file."""
    global spam_settings, global_spam_filter_enabled
    if os.path.exists(SPAM_SETTINGS_FILE):
        with open(SPAM_SETTINGS_FILE, 'r') as f:
            try:
                spam_settings = json.load(f)
            except json.JSONDecodeError:
                spam_settings = {}
    global_spam_filter_enabled = spam_settings.get("__global__", {}).get("enabled", False) # Đọc đúng key 'enabled'

    load_link_data() # Tải cả dữ liệu cảnh cáo và cài đặt link để dùng chung

def save_spam_settings():
    """Lưu cài đặt chống spam vào file."""
    os.makedirs(os.path.dirname(SPAM_SETTINGS_FILE), exist_ok=True)
    if "__global__" not in spam_settings:
        spam_settings["__global__"] = {}
    spam_settings["__global__"]["enabled"] = global_spam_filter_enabled
    with open(SPAM_SETTINGS_FILE, 'w') as f:
        json.dump(spam_settings, f, indent=4)

class AntiSpamControlView(discord.ui.View):
    """View chứa các nút bật/tắt cho bộ lọc spam."""
    def __init__(self, author_id: int, cog_instance, guild=None):
        super().__init__(timeout=120)
        self.author_id = author_id
        self.cog = cog_instance
        for item in self.children:
            if isinstance(item, discord.ui.Button):
                if item.emoji and str(item.emoji) == "🟢":
                    item.label = t(guild, "ANTI_SPAM_BTN_ON")
                elif item.emoji and str(item.emoji) == "🔴":
                    item.label = t(guild, "ANTI_SPAM_BTN_OFF")

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id != self.author_id:
            await interaction.response.send_message(t(interaction.guild, "ANTI_SPAM_NOT_YOURS"), ephemeral=True)
            return False
        return True

    @discord.ui.button(label="Bật cho Server", style=discord.ButtonStyle.success, emoji="🟢")
    async def toggle_on(self, interaction: discord.Interaction, button: discord.ui.Button):
        guild_id_str = str(interaction.guild.id)
        if guild_id_str not in spam_settings:
            spam_settings[guild_id_str] = {}
        spam_settings[guild_id_str]["enabled_guild"] = True
        save_spam_settings()
        # Cập nhật lại embed
        prefix = (await self.cog.bot.get_prefix(interaction.message))[0] if interaction.message and interaction.guild else "!"
        new_embed = self.cog._create_status_embed(interaction.guild, prefix)
        await interaction.response.edit_message(embed=new_embed, view=self)

    @discord.ui.button(label="Tắt cho Server", style=discord.ButtonStyle.danger, emoji="🔴")
    async def toggle_off(self, interaction: discord.Interaction, button: discord.ui.Button):
        guild_id_str = str(interaction.guild.id)
        if guild_id_str not in spam_settings:
            spam_settings[guild_id_str] = {}
        spam_settings[guild_id_str]["enabled_guild"] = False
        save_spam_settings()
        # Cập nhật lại embed
        prefix = (await self.cog.bot.get_prefix(interaction.message))[0] if interaction.message and interaction.guild else "!"
        new_embed = self.cog._create_status_embed(interaction.guild, prefix)
        await interaction.response.edit_message(embed=new_embed, view=self)

class SpamFilterCog(commands.Cog, name="Anti-Spam"):
    """Cog để phát hiện và xử lý hành vi spam tin nhắn."""

    def __init__(self, bot: commands.Bot):
        self.bot = bot
        load_spam_data()

    def _create_status_embed(self, guild: discord.Guild, prefix: str) -> discord.Embed:
        """Hàm trợ giúp để tạo embed trạng thái."""
        guild_id_str = str(guild.id)
        settings = spam_settings.get(guild_id_str, {})
        
        global_status = t(guild, "ANTI_LINK_STATUS_ON") if global_spam_filter_enabled else t(guild, "ANTI_LINK_STATUS_OFF")
        guild_status = t(guild, "ANTI_LINK_STATUS_ON") if settings.get("enabled_guild", False) else t(guild, "ANTI_LINK_STATUS_OFF")
        
        message_limit = settings.get("message_limit", 5)
        time_period = settings.get("time_period", 3)
        mute_duration = settings.get("mute_duration", 5)
        duplicate_limit = settings.get("duplicate_limit", 3)
        emoji_limit = settings.get("emoji_limit", 10)
        mention_limit = settings.get("mention_limit", 5)

        embed = discord.Embed(
            title=t(guild, "ANTI_SPAM_DASHBOARD_TITLE"),
            description=t(guild, "ANTI_SPAM_DASHBOARD_DESC", global_status=global_status, guild_status=guild_status, message_limit=message_limit, time_period=time_period, duplicate_limit=duplicate_limit, emoji_limit=emoji_limit, mention_limit=mention_limit, mute_duration=mute_duration),
            color=discord.Color.blue()
        )
        embed.add_field(
            name=t(guild, "ANTI_SPAM_FIELD_MANAGE"),
            value=t(guild, "ANTI_SPAM_FIELD_MANAGE_VALUE", prefix=prefix),
            inline=False
        )
        return embed

    async def handle_spam_violation(self, message: discord.Message, reason: str):
        """Hàm xử lý khi phát hiện spam, tích hợp hệ thống cảnh cáo."""
        guild_id_str = str(message.guild.id)
        user_id_str = str(message.author.id)

        # Xóa tin nhắn vi phạm
        try:
            # Tối ưu hóa: Dùng purge để xóa tin nhắn của người dùng vi phạm
            # Lấy thời gian bắt đầu của chuỗi spam để xóa chính xác hơn
            history = user_message_history.get(guild_id_str, {}).get(user_id_str, deque())
            start_time = history[0][0] if history else datetime.now().timestamp() - 5 # Mặc định 5 giây trước
            await message.channel.purge(
                limit=len(history) + 10, # Xóa nhiều hơn một chút để đảm bảo
                check=lambda m: m.author.id == message.author.id,
                after=datetime.fromtimestamp(start_time - 1) # Xóa các tin nhắn sau thời điểm bắt đầu spam
            )
        except (discord.NotFound, discord.Forbidden) as e:
            print(f"[Anti-Spam] Không thể xóa tin nhắn spam: {e}")
            await message.delete() # Nếu lỗi, chỉ xóa tin nhắn hiện tại

        # Xử lý hệ thống cảnh cáo và mute (dùng chung với anti-link)
        warning_limit = link_settings.get(guild_id_str, {}).get("warning_limit", 5)
        if guild_id_str not in link_warnings: link_warnings[guild_id_str] = {}
        user_warnings = link_warnings[guild_id_str].get(user_id_str, 0) + 1

        if warning_limit > 0 and user_warnings >= warning_limit:
            try:
                duration = timedelta(minutes=5)
                await message.author.timeout(duration, reason=f"Vi phạm quy định chống spam quá nhiều lần.")
                mute_embed = discord.Embed(title=t(message.guild, "ANTI_SPAM_AUTOMUTE_TITLE"), description=t(message.guild, "ANTI_SPAM_AUTOMUTE_DESC", mention=message.author.mention, limit=warning_limit), color=discord.Color.dark_red())
                await message.channel.send(embed=mute_embed)
                link_warnings[guild_id_str][user_id_str] = 0 # Reset cảnh cáo
            except discord.Forbidden:
                await message.channel.send(t(message.guild, "ANTI_SPAM_MUTE_FORBIDDEN", mention=message.author.mention), delete_after=10)
        else:
            warning_desc = t(message.guild, "ANTI_SPAM_WARN_DESC", mention=message.author.mention, reason=reason)
            if warning_limit > 0:
                warning_desc += t(message.guild, "ANTI_SPAM_WARN_COUNT", cur=user_warnings, limit=warning_limit)
            warning_embed = discord.Embed(title=t(message.guild, "ANTI_SPAM_WARN_TITLE"), description=warning_desc, color=discord.Color.orange())
            await message.channel.send(embed=warning_embed, delete_after=15)
            link_warnings[guild_id_str][user_id_str] = user_warnings
        
        save_link_warnings()

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if not message.guild or message.author.bot:
            return

        # 1. Kiểm tra Global Toggle (Owner)
        if not global_spam_filter_enabled:
            return
        
        guild_id_str = str(message.guild.id)
        # 2. Kiểm tra Server Toggle (Admin), mặc định là Tắt
        guild_setting = spam_settings.get(guild_id_str, {}).get("enabled_guild", False)
        if not guild_setting:
            return

        # 3. Bỏ qua Owner và Admin
        if message.author.id == OWNER_ID:
            return
        guild_admin_roles = admin_roles.get(guild_id_str, [])
        user_role_ids = {role.id for role in message.author.roles}
        if any(admin_role_id in user_role_ids for admin_role_id in guild_admin_roles):
            return

        # --- Logic phát hiện Spam ---
        now = datetime.now().timestamp()
        user_id_str = str(message.author.id)

        # Lấy cài đặt của server, nếu không có thì dùng mặc định
        settings = spam_settings.get(guild_id_str, {})
        message_limit = settings.get("message_limit", 5)
        time_period = settings.get("time_period", 3) # giây
        mute_duration = settings.get("mute_duration", 5) # phút

        # Sử dụng .get() để tránh KeyError và khởi tạo nếu cần
        guild_history = user_message_history.setdefault(guild_id_str, {})
        history = guild_history.setdefault(user_id_str, deque())

        # Thêm tin nhắn hiện tại vào lịch sử
        history.append((now, message.id, message.content))

        # Loại bỏ các tin nhắn cũ hơn time_period
        while history and now - history[0][0] > time_period:
            history.popleft()

        # --- Kiểm tra các loại vi phạm ---
        violation_reason = None
        settings = spam_settings.get(guild_id_str, {})
        message_limit = settings.get("message_limit", 5)
        duplicate_limit = settings.get("duplicate_limit", 3)
        emoji_limit = settings.get("emoji_limit", 10)
        mention_limit = settings.get("mention_limit", 5)

        # 1. Kiểm tra spam nhanh (nhiều tin nhắn trong thời gian ngắn)
        if len(history) > message_limit:
            violation_reason = t(message.guild, "ANTI_SPAM_REASON_FAST", count=len(history), seconds=time_period)
        
        # 2. Kiểm tra spam emoji
        elif emoji_limit > 0:
            # Regex để tìm cả emoji unicode và emoji tùy chỉnh của Discord
            emoji_pattern = re.compile(r'<a?:\w+:\d+>|[\U0001F600-\U0001F64F\U0001F300-\U0001F5FF\U0001F680-\U0001F6FF\U0001F1E0-\U0001F1FF\U00002702-\U000027B0\U000024C2-\U0001F251]+')
            emojis_found = emoji_pattern.findall(message.content)
            if len(emojis_found) > emoji_limit:
                violation_reason = t(message.guild, "ANTI_SPAM_REASON_EMOJI", count=len(emojis_found), limit=emoji_limit)

        # 3. Kiểm tra spam tag
        elif mention_limit > 0:
            total_mentions = len(message.mentions) + len(message.role_mentions)
            if message.mention_everyone:
                total_mentions += 1 # @everyone và @here được tính là 1
            
            if total_mentions > mention_limit:
                violation_reason = t(message.guild, "ANTI_SPAM_REASON_MENTION", count=total_mentions, limit=mention_limit)

        # 4. Kiểm tra spam lặp lại (nhiều tin nhắn giống hệt nhau)
        elif duplicate_limit > 0:
            # Đếm số tin nhắn có nội dung giống hệt tin nhắn hiện tại (và không rỗng)
            duplicate_count = sum(1 for _, _, content in history if content and content == message.content)
            if duplicate_count > duplicate_limit:
                violation_reason = t(message.guild, "ANTI_SPAM_REASON_DUPLICATE", count=duplicate_count)

        if violation_reason:
            await self.handle_spam_violation(message, violation_reason)
            # Xóa lịch sử của người dùng sau khi xử lý
            history.clear()

    @commands.group(name="antispam", description="Quản lý hệ thống chống spam tin nhắn.")
    @has_admin_role()
    async def antispam(self, ctx: commands.Context):
        """Lệnh gốc cho nhóm quản lý chống spam."""
        if ctx.invoked_subcommand is None:
            embed = self._create_status_embed(ctx.guild, ctx.prefix)
            view = AntiSpamControlView(ctx.author.id, self, guild=ctx.guild)
            await ctx.send(embed=embed, view=view, ephemeral=True)

    @antispam.command(name="global", description="[Owner] Bật hoặc tắt chống spam trên toàn bộ bot.")
    @is_owner()
    async def toggle_global(self, ctx: commands.Context, status: Literal["on", "off"]):
        global global_spam_filter_enabled
        global_spam_filter_enabled = (status.lower() == "on")
        save_spam_settings()
        status_text = t(ctx.guild, "ANTI_SPAM_GLOBAL_ON") if global_spam_filter_enabled else t(ctx.guild, "ANTI_SPAM_GLOBAL_OFF")
        await ctx.send(status_text, ephemeral=True)

    @antispam.command(name="set", description="Đặt ngưỡng phát hiện spam (ví dụ: 5 tin nhắn trong 3 giây).")
    @has_admin_role()
    @app_commands.describe(messages="Số lượng tin nhắn tối đa.", seconds="Khoảng thời gian (giây).")
    async def set_threshold(self, ctx: commands.Context, messages: int, seconds: int):
        if messages < 2 or seconds < 1:
            return await ctx.send(t(ctx.guild, "ANTI_SPAM_THRESHOLD_INVALID"), ephemeral=True)
        
        guild_id_str = str(ctx.guild.id)
        if guild_id_str not in spam_settings:
            spam_settings[guild_id_str] = {}
        
        spam_settings[guild_id_str]["message_limit"] = messages
        spam_settings[guild_id_str]["time_period"] = seconds
        save_spam_settings()
        await ctx.send(t(ctx.guild, "ANTI_SPAM_THRESHOLD_SUCCESS", messages=messages, seconds=seconds), ephemeral=True)

    @antispam.command(name="setduplicate", description="Đặt ngưỡng tin nhắn giống hệt nhau bị coi là spam.")
    @has_admin_role()
    @app_commands.describe(limit="Số lượng tin nhắn giống nhau tối đa. Nhập 0 để tắt.")
    async def set_duplicate_threshold(self, ctx: commands.Context, limit: int):
        if limit < 0:
            return await ctx.send(t(ctx.guild, "ANTI_SPAM_DUP_INVALID"), ephemeral=True)

        guild_id_str = str(ctx.guild.id)
        if guild_id_str not in spam_settings:
            spam_settings[guild_id_str] = {}

        spam_settings[guild_id_str]["duplicate_limit"] = limit
        save_spam_settings()
        if limit > 0:
            await ctx.send(t(ctx.guild, "ANTI_SPAM_DUP_SET", limit=limit), ephemeral=True)
        else:
            await ctx.send(t(ctx.guild, "ANTI_SPAM_DUP_OFF"), ephemeral=True)

    @antispam.command(name="setemoji", description="Đặt giới hạn số lượng emoji trong một tin nhắn.")
    @has_admin_role()
    @app_commands.describe(limit="Số lượng emoji tối đa. Nhập 0 để tắt.")
    async def set_emoji_limit(self, ctx: commands.Context, limit: int):
        if limit < 0:
            return await ctx.send(t(ctx.guild, "ANTI_SPAM_EMOJI_INVALID"), ephemeral=True)

        guild_id_str = str(ctx.guild.id)
        if guild_id_str not in spam_settings:
            spam_settings[guild_id_str] = {}

        spam_settings[guild_id_str]["emoji_limit"] = limit
        save_spam_settings()
        if limit > 0:
            await ctx.send(t(ctx.guild, "ANTI_SPAM_EMOJI_SET", limit=limit), ephemeral=True)
        else:
            await ctx.send(t(ctx.guild, "ANTI_SPAM_EMOJI_OFF"), ephemeral=True)

    @antispam.command(name="setmention", description="Đặt giới hạn số lượt tag (người dùng, vai trò) trong một tin nhắn.")
    @has_admin_role()
    @app_commands.describe(limit="Số lượt tag tối đa. Nhập 0 để tắt.")
    async def set_mention_limit(self, ctx: commands.Context, limit: int):
        if limit < 0:
            return await ctx.send(t(ctx.guild, "ANTI_SPAM_MENTION_INVALID"), ephemeral=True)

        guild_id_str = str(ctx.guild.id)
        if guild_id_str not in spam_settings:
            spam_settings[guild_id_str] = {}

        spam_settings[guild_id_str]["mention_limit"] = limit
        save_spam_settings()
        if limit > 0:
            await ctx.send(t(ctx.guild, "ANTI_SPAM_MENTION_SET", limit=limit), ephemeral=True)
        else:
            await ctx.send(t(ctx.guild, "ANTI_SPAM_MENTION_OFF"), ephemeral=True)

    @antispam.command(name="setmute", description="Đặt thời gian mute khi phát hiện spam (phút).")
    @has_admin_role()
    @app_commands.describe(minutes="Thời gian mute (phút). Nhập 0 để chỉ xóa tin nhắn.")
    async def set_mute_duration(self, ctx: commands.Context, minutes: int):
        if minutes < 0:
            return await ctx.send(t(ctx.guild, "ANTI_SPAM_MUTE_INVALID"), ephemeral=True)
        
        guild_id_str = str(ctx.guild.id)
        if guild_id_str not in spam_settings:
            spam_settings[guild_id_str] = {}
            
        spam_settings[guild_id_str]["mute_duration"] = minutes
        save_spam_settings()
        if minutes > 0:
            await ctx.send(t(ctx.guild, "ANTI_SPAM_MUTE_SET", minutes=minutes), ephemeral=True)
        else:
            await ctx.send(t(ctx.guild, "ANTI_SPAM_MUTE_OFF"), ephemeral=True)

async def setup(bot: commands.Bot):
    await bot.add_cog(SpamFilterCog(bot))
