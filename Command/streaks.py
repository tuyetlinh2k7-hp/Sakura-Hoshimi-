import datetime
import json
import os
from pathlib import Path
from typing import Optional

import discord
from discord.ext import commands, tasks
from discord import app_commands

from Check.i18n import t, is_vietnamese

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
DATA_FILE = DATA_DIR / "streks.json" if (DATA_DIR / "streks.json").exists() else DATA_DIR / "streaks.json"

_streak_cache: dict = {}


def load_data() -> dict:
    global _streak_cache
    if _streak_cache:
        return _streak_cache

    if not DATA_FILE.exists():
        _streak_cache = {}
        return _streak_cache

    try:
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            _streak_cache = json.load(f)
    except (json.JSONDecodeError, OSError):
        _streak_cache = {}
    return _streak_cache


def save_data(data: Optional[dict] = None):
    global _streak_cache
    if data is not None:
        _streak_cache = data

    DATA_DIR.mkdir(parents=True, exist_ok=True)
    try:
        with open(DATA_FILE, "w", encoding="utf-8") as f:
            json.dump(_streak_cache, f, ensure_ascii=False, indent=4)
    except Exception:
        pass


def get_streak_channel_id(guild_id: int) -> Optional[int]:
    data = load_data()
    guild_key = f"guild_{guild_id}"
    return data.get(guild_key, {}).get("channel_id")


def get_streak_emoji(streak: int) -> str:
    if streak >= 5000: return "🌌"
    elif streak >= 1000: return "⚡"
    elif streak >= 500: return "🏆"
    elif streak >= 200: return "👑"
    elif streak >= 100: return "💎"
    elif streak >= 50: return "🔮"
    elif streak >= 30: return "⭐"
    elif streak >= 7: return "🔥"
    elif streak >= 3: return "✨"
    else: return "🌱"


def get_current_vn_date() -> datetime.date:
    return (datetime.datetime.utcnow() + datetime.timedelta(hours=7)).date()


class RestoreStreakView(discord.ui.View):
    def __init__(self, user_id: str, guild_id: int, is_vi: bool = True):
        super().__init__(timeout=None)
        self.user_id = user_id
        self.guild_id = guild_id
        self.is_vi = is_vi
        self.restore_btn.label = "❄️ Hồi chuỗi ngay" if is_vi else "❄️ Restore Streak Now"

    @discord.ui.button(label="❄️ Hồi chuỗi ngay", style=discord.ButtonStyle.primary, custom_id="persistent_restore_streak_btn")
    async def restore_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        vi = is_vietnamese(interaction.guild or self.guild_id)
        if str(interaction.user.id) != self.user_id:
            msg = "⚠️ Đây không phải thông báo chuỗi của bạn!" if vi else "⚠️ This is not your streak notification!"
            return await interaction.response.send_message(msg, ephemeral=True)

        data = load_data()
        guild_key = f"guild_{self.guild_id}"

        if guild_key not in data or "users" not in data[guild_key] or self.user_id not in data[guild_key]["users"]:
            msg = "❌ Không tìm thấy dữ liệu chuỗi của bạn." if vi else "❌ No streak record found for your account."
            return await interaction.response.send_message(msg, ephemeral=True)

        user_data = data[guild_key]["users"][self.user_id]
        old_streak = user_data.get("previous_streak", 0)

        if old_streak <= 1:
            msg = "⚠️ Chuỗi của bạn không đủ điều kiện để hồi phục!" if vi else "⚠️ Your streak is not eligible for recovery!"
            return await interaction.response.send_message(msg, ephemeral=True)

        now = datetime.datetime.utcnow()
        if "restore_history" not in user_data:
            user_data["restore_history"] = []

        thirty_days_ago = now - datetime.timedelta(days=30)
        valid_history = [ts for ts in user_data["restore_history"] if datetime.datetime.fromisoformat(ts) > thirty_days_ago]
        user_data["restore_history"] = valid_history

        if len(valid_history) >= 3:
            msg = "❌ Bạn đã dùng hết hạn mức hồi chuỗi (**3 lần/30 ngày**)." if vi else "❌ You have used up your streak recovery quota (**3 times / 30 days**)."
            return await interaction.response.send_message(msg, ephemeral=True)

        user_data["streak"] = old_streak
        user_data["last_date"] = get_current_vn_date().isoformat()
        user_data.pop("previous_streak", None)
        user_data["restore_history"].append(now.isoformat())
        save_data(data)

        for child in self.children:
            child.disabled = True
        try:
            await interaction.message.edit(view=self)
        except Exception:
            pass

        emoji = get_streak_emoji(old_streak)
        rem = 3 - len(user_data['restore_history'])
        if vi:
            resp = f"🎉 **Khôi phục thành công!** Chuỗi của bạn đã được đưa về mức **{old_streak} ngày** {emoji}. (Còn `{rem}` lượt trong tháng)."
        else:
            resp = f"🎉 **Restore successful!** Your streak is back to **{old_streak} days** {emoji}. (`{rem}` restore(s) left this month)."
        await interaction.response.send_message(resp, ephemeral=True)


class StreakCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.check_streaks_reset.start()

    def cog_unload(self):
        self.check_streaks_reset.cancel()

    @commands.hybrid_group(name="streak", description="Hệ thống quản lý chuỗi điểm danh (Streak) / Daily streak system")
    @commands.guild_only()
    async def streak_group(self, ctx: commands.Context):
        vi = is_vietnamese(ctx.guild)
        if ctx.invoked_subcommand is None:
            msg = "ℹ️ Sử dụng `/streak view` để xem chuỗi hoặc `/streak setup` để cài đặt kênh điểm danh." if vi else "ℹ️ Use `/streak view` to check your streak or `/streak setup` to configure the streak channel."
            await ctx.send(msg, ephemeral=True)

    @streak_group.command(name="setup", description="[Admin] Cài đặt kênh điểm danh giữ chuỗi tự động / Setup streak channel.")
    @app_commands.describe(channel="Chọn kênh văn bản làm kênh điểm danh / Select text channel for streak")
    @commands.has_permissions(administrator=True)
    async def streak_setup(self, ctx: commands.Context, channel: Optional[discord.TextChannel] = None):
        vi = is_vietnamese(ctx.guild)
        data = load_data()
        guild_key = f"guild_{ctx.guild.id}"

        if guild_key not in data:
            data[guild_key] = {"users": {}, "channel_id": None}

        target_channel = channel or ctx.channel
        data[guild_key]["channel_id"] = target_channel.id
        save_data(data)

        confirm_msg = f"✅ Đã thiết lập thành công {target_channel.mention} làm kênh giữ chuỗi!" if vi else f"✅ Successfully set {target_channel.mention} as the daily streak channel!"
        await ctx.send(confirm_msg, ephemeral=True)

        embed = discord.Embed(
            title="🔥 HỆ THỐNG GIỮ CHUỖI (STREAK) HOẠT ĐỘNG" if vi else "🔥 DAILY STREAK SYSTEM ACTIVE",
            description="Chào mừng mọi người đến với kênh điểm danh giữ chuỗi tự động!\nNhắn bất kỳ tin nhắn nào mỗi ngày để duy trì chuỗi." if vi else "Welcome to the automatic daily streak channel!\nSend any message here every day to maintain your streak.",
            color=discord.Color.from_rgb(255, 100, 0)
        )
        embed.add_field(
            name="📌 Quy tắc & Hồi chuỗi" if vi else "📌 Rules & Recovery",
            value=("• **Duy trì**: Chat 1 tin/ngày để cộng chuỗi.\n• **Quên chat**: Chuỗi reset về 1, bot hiển thị nút **❄️ Hồi chuỗi**.\n• **Giới hạn**: Tối đa **3 lần / 30 ngày**."
                   if vi else
                   "• **Maintain**: Chat 1 message/day to extend streak.\n• **Missed day**: Streak resets to 1, bot provides a **❄️ Restore** button.\n• **Limit**: Up to **3 times / 30 days**."),
            inline=False
        )
        try:
            await target_channel.send(embed=embed)
        except Exception:
            pass

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if message.author.bot or not message.guild:
            return

        guild_id = message.guild.id
        streak_channel_id = get_streak_channel_id(guild_id)
        if not streak_channel_id or message.channel.id != streak_channel_id:
            return

        vi = is_vietnamese(message.guild)
        user_id = str(message.author.id)
        data = load_data()
        guild_key = f"guild_{guild_id}"

        if guild_key not in data:
            data[guild_key] = {"users": {}, "channel_id": streak_channel_id}

        users_data = data[guild_key]["users"]
        today = get_current_vn_date()
        today_str = today.isoformat()

        status_text = ""
        current_streak = 1
        is_reset = False
        old_streak = 0

        if user_id not in users_data:
            users_data[user_id] = {"streak": 1, "last_date": today_str, "restore_history": []}
            status_text = "🎉 Chúc mừng bạn đã bắt đầu chuỗi hoạt động mới!" if vi else "🎉 Congratulations on starting a new daily streak!"
        else:
            user_data = users_data[user_id]
            last_date = datetime.date.fromisoformat(user_data["last_date"])

            if last_date == today:
                return
            else:
                yesterday = today - datetime.timedelta(days=1)
                if last_date == yesterday:
                    user_data["streak"] += 1
                    user_data["last_date"] = today_str
                    current_streak = user_data["streak"]
                    status_text = "✅ Duy trì chuỗi thành công!" if vi else "✅ Successfully maintained your streak!"
                else:
                    old_streak = user_data["streak"]
                    if old_streak > 1:
                        is_reset = True
                        user_data["previous_streak"] = old_streak

                    user_data["streak"] = 1
                    user_data["last_date"] = today_str
                    current_streak = 1
                    status_text = "💔 Bạn đã bỏ lỡ ngày hôm qua nên chuỗi đã bị reset về 1!" if vi else "💔 You missed yesterday, so your streak has reset to 1!"

        save_data(data)

        emoji = get_streak_emoji(current_streak)
        try:
            await message.add_reaction(emoji)
        except Exception:
            pass

        day_unit = "ngày" if vi else "days"
        member_lbl = "Thành viên" if vi else "Member"

        if is_reset and old_streak > 1:
            embed = discord.Embed(
                title="🔥 Cập Nhật Chuỗi Điểm Danh" if vi else "🔥 Daily Streak Update",
                description=f"{status_text}\n\n👤 {member_lbl}: {message.author.mention}",
                color=discord.Color.red()
            )
            embed.set_thumbnail(url=message.author.display_avatar.url)
            embed.add_field(name="Chuỗi hiện tại" if vi else "Current Streak", value=f"**{current_streak} {day_unit}** {emoji}", inline=True)
            embed.add_field(
                name="❄️ Hồi chuỗi" if vi else "❄️ Restore Streak",
                value=(f"Chuỗi trước đó của bạn là **{old_streak} ngày**. Bấm nút dưới để khôi phục (Tối đa 3 lần/30 ngày)."
                       if vi else
                       f"Your previous streak was **{old_streak} days**. Click the button below to restore (Max 3 times / 30 days)."),
                inline=False
            )
            view = RestoreStreakView(user_id, guild_id, is_vi=vi)
            await message.channel.send(embed=embed, view=view)
        else:
            embed = discord.Embed(
                title="🔥 Cập Nhật Chuỗi Điểm Danh" if vi else "🔥 Daily Streak Update",
                description=f"{status_text}\n\n👤 {member_lbl}: {message.author.mention}",
                color=discord.Color.orange()
            )
            embed.set_thumbnail(url=message.author.display_avatar.url)
            embed.add_field(name="Chuỗi hiện tại" if vi else "Current Streak", value=f"**{current_streak} {day_unit}** {emoji}", inline=True)
            embed.set_footer(text="Hãy tiếp tục giữ phong độ vào ngày mai nhé!" if vi else "Keep up the momentum tomorrow!")
            await message.channel.send(embed=embed)

    @streak_group.command(name="view", description="Xem chuỗi điểm danh hiện tại của bạn hoặc thành viên khác.")
    @app_commands.describe(thanh_vien="Thành viên muốn xem (để trống nếu là chính bạn)")
    async def streak_view(self, ctx: commands.Context, thanh_vien: Optional[discord.Member] = None):
        vi = is_vietnamese(ctx.guild)
        target = thanh_vien or ctx.author
        guild_key = f"guild_{ctx.guild.id}"
        user_id = str(target.id)
        data = load_data()

        if guild_key not in data or "users" not in data[guild_key] or user_id not in data[guild_key]["users"]:
            msg = f"👤 {target.mention} chưa có chuỗi hoạt động nào trong server này." if vi else f"👤 {target.mention} has no active streak record in this server."
            return await ctx.send(msg, ephemeral=True)

        user_data = data[guild_key]["users"][user_id]
        current_streak = user_data["streak"]
        emoji = get_streak_emoji(current_streak)

        now = datetime.datetime.utcnow()
        thirty_days_ago = now - datetime.timedelta(days=30)
        valid_restores = [ts for ts in user_data.get("restore_history", []) if datetime.datetime.fromisoformat(ts) > thirty_days_ago]
        remaining_restores = max(0, 3 - len(valid_restores))

        day_unit = "ngày" if vi else "days"
        restores_unit = "lượt" if vi else "left"

        embed = discord.Embed(
            title="📊 Thống Kê Chuỗi Hoạt Động" if vi else "📊 Streak Statistics",
            description=f"{('Thành viên' if vi else 'Member')}: {target.mention}",
            color=discord.Color.blue()
        )
        embed.set_thumbnail(url=target.display_avatar.url)
        embed.add_field(name="Chuỗi hiện tại" if vi else "Current Streak", value=f"**{current_streak} {day_unit}** {emoji}", inline=True)
        embed.add_field(name="❄️ Lượt hồi chuỗi còn lại" if vi else "❄️ Restores Remaining", value=f"**{remaining_restores}/3** {restores_unit}", inline=True)
        await ctx.send(embed=embed)

    @tasks.loop(hours=24)
    async def check_streaks_reset(self):
        data = load_data()
        today = get_current_vn_date()
        yesterday = today - datetime.timedelta(days=1)
        updated = False

        for guild_key, guild_info in data.items():
            if "users" not in guild_info:
                continue
            for user_id, user_data in guild_info["users"].items():
                if "last_date" not in user_data:
                    continue
                last_date = datetime.date.fromisoformat(user_data["last_date"])
                if last_date < yesterday and user_data["streak"] > 0:
                    if user_data["streak"] > 1:
                        user_data["previous_streak"] = user_data["streak"]
                    user_data["streak"] = 0
                    updated = True

        if updated:
            save_data(data)

    @check_streaks_reset.before_loop
    async def before_check_streaks_reset(self):
        await self.bot.wait_until_ready()


async def setup(bot):
    await bot.add_cog(StreakCog(bot))
