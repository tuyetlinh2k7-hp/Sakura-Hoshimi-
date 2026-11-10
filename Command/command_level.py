from datetime import datetime, timedelta, timezone
from typing import Literal, Optional
import aiosqlite
import discord
from discord import app_commands
from discord.ext import commands, tasks
from discord.ui import Button, ChannelSelect, View, UserSelect, Modal, TextInput, Select

from Check.i18n import t, is_vietnamese
from Check.level_handler import (
    add_xp,
    award_daily,
    get_xp_for_level,
    leveling_settings,
    load_leveling_data,
    save_leveling_settings,
    user_levels,
    save_leveling_data,
    is_user_ignored, set_ignored_user,
    get_period_leaderboard, get_voice_leaderboard, get_global_voice_leaderboard,
    start_voice_session, end_voice_session, format_duration,
)
from Check.mod import OWNER_ID, admin_roles
from Command.checks import blacklist_users

from data.database import DB_PATH, get_leaderboard_data, get_user_data, update_user_coins
from data.card_generator import create_rank_card

VN_TZ = timezone(timedelta(hours=7))


def is_admin_or_owner(member: discord.Member, guild: discord.Guild) -> bool:
    if member.id == OWNER_ID or member.guild_permissions.administrator or member.guild_permissions.manage_guild:
        return True
    guild_id_str = str(guild.id)
    if guild_id_str in admin_roles:
        user_role_ids = {r.id for r in member.roles}
        if any(rid in user_role_ids for rid in admin_roles[guild_id_str]):
            return True
    return False


class IgnoreChannelView(View):
    def __init__(self, author_id: int, cog_instance, panel_view: "LevelingPanelView"):
        super().__init__(timeout=120)
        self.author_id = author_id
        self.cog = cog_instance
        self.panel_view = panel_view

        self.channel_select = ChannelSelect(
            placeholder="Chọn một hoặc nhiều kênh văn bản...",
            min_values=1,
            max_values=25,
            channel_types=[discord.ChannelType.text],
            row=0,
        )
        self.channel_select.callback = self.on_select_channels
        self.add_item(self.channel_select)

    async def on_select_channels(self, interaction: discord.Interaction):
        await interaction.response.defer()

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id != self.author_id:
            await interaction.response.send_message(t(interaction.guild, "LEVEL_NOT_YOURS"), ephemeral=True)
            return False
        return True

    async def handle_action(self, interaction: discord.Interaction, action: str):
        selected_channels = self.channel_select.values
        if not selected_channels:
            return await interaction.response.send_message(
                "⚠️ Vui lòng chọn ít nhất một kênh ở menu phía trên trước khi bấm nút!",
                ephemeral=True,
            )

        await interaction.response.defer(ephemeral=True)
        guild_id_str = str(interaction.guild_id)
        ignored_list = leveling_settings.setdefault(guild_id_str, {}).setdefault("ignored_channels", [])

        added, removed, already, not_found = [], [], [], []

        if action == "add":
            for channel in selected_channels:
                if channel.id not in ignored_list:
                    ignored_list.append(channel.id)
                    added.append(channel.mention)
                else:
                    already.append(channel.mention)
        elif action == "remove":
            for channel in selected_channels:
                if channel.id in ignored_list:
                    ignored_list.remove(channel.id)
                    removed.append(channel.mention)
                else:
                    not_found.append(channel.mention)

        save_leveling_settings()

        response_lines = []
        if added:
            response_lines.append(f"✅ Đã thêm: {', '.join(added)}")
        if removed:
            response_lines.append(f"🗑️ Đã xóa: {', '.join(removed)}")
        if already:
            response_lines.append(f"ℹ️ Đã tồn tại: {', '.join(already)}")
        if not_found:
            response_lines.append(f"❓ Không có trong danh sách: {', '.join(not_found)}")

        await interaction.followup.send("\n".join(response_lines) or "Không có thay đổi nào.", ephemeral=True)
        await self.panel_view.refresh_panel(interaction.guild)

    @discord.ui.button(label="Thêm vào danh sách bỏ qua", style=discord.ButtonStyle.success, emoji="➕", row=1)
    async def add_button(self, interaction: discord.Interaction, button: Button):
        await self.handle_action(interaction, "add")

    @discord.ui.button(label="Xóa khỏi danh sách bỏ qua", style=discord.ButtonStyle.danger, emoji="➖", row=1)
    async def remove_button(self, interaction: discord.Interaction, button: Button):
        await self.handle_action(interaction, "remove")



class IgnoreUserView(View):
    """Chọn thành viên rồi bật/tắt bỏ qua XP ngay trên panel."""
    def __init__(self, author_id: int, cog_instance):
        super().__init__(timeout=120)
        self.author_id = author_id
        self.cog = cog_instance
        self.user_select = UserSelect(placeholder="Chọn thành viên cần bật/tắt bỏ qua level", min_values=1, max_values=1, row=0)
        self.user_select.callback = self.selected_user
        self.add_item(self.user_select)

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id != self.author_id:
            await interaction.response.send_message("⛔ Bảng điều khiển này không thuộc về bạn.", ephemeral=True)
            return False
        if not interaction.guild or not is_admin_or_owner(interaction.user, interaction.guild):
            await interaction.response.send_message("⛔ Cần quyền Admin/Owner server.", ephemeral=True)
            return False
        return True

    async def selected_user(self, interaction: discord.Interaction):
        member = self.user_select.values[0]
        ignored = is_user_ignored(interaction.guild.id, member.id)
        set_ignored_user(interaction.guild.id, member.id, not ignored)
        state = "đã bị bỏ qua XP" if not ignored else "đã được bật lại XP"
        await interaction.response.send_message(f"✅ {member.mention} {state} trong server này.", ephemeral=True)


class OwnerStatModal(Modal):
    def __init__(self, cog_instance, operation: str):
        super().__init__(title="Cộng chỉ số" if operation == "add" else "Trừ chỉ số")
        self.cog = cog_instance
        self.operation = operation
        self.user_id = TextInput(label="ID thành viên", placeholder="Nhập Discord User ID", max_length=25)
        self.stat = TextInput(label="Chỉ số: xp hoặc level", placeholder="xp", default="xp", max_length=5)
        self.amount = TextInput(label="Số lượng", placeholder="Ví dụ: 500", max_length=12)
        self.add_item(self.user_id); self.add_item(self.stat); self.add_item(self.amount)

    async def on_submit(self, interaction: discord.Interaction):
        if interaction.user.id != OWNER_ID:
            return await interaction.response.send_message("⛔ Chỉ Owner bot được dùng chức năng này.", ephemeral=True)
        try:
            uid = int(str(self.user_id.value).strip())
            stat = str(self.stat.value).strip().lower()
            amount = int(str(self.amount.value).strip())
            if stat not in ("xp", "level") or amount <= 0:
                raise ValueError
        except ValueError:
            return await interaction.response.send_message("❌ ID, chỉ số hoặc số lượng không hợp lệ. Chỉ số là `xp`/`level`, số lượng phải > 0.", ephemeral=True)
        if not interaction.guild:
            return await interaction.response.send_message("Chỉ dùng trong server.", ephemeral=True)
        data = await get_user_data(interaction.guild.id, uid)
        current = int(data.get(stat, 0))
        value = current + amount if self.operation == "add" else max(0, current - amount)
        async with aiosqlite.connect(DB_PATH) as db:
            await db.execute(f"UPDATE users SET {stat}=? WHERE guild_id=? AND user_id=?", (value, str(interaction.guild.id), str(uid)))
            await db.commit()
        verb = "Cộng" if self.operation == "add" else "Trừ"
        await interaction.response.send_message(f"✅ {verb} **{amount:,} {stat.upper()}** cho <@{uid}>. Giá trị mới: **{value:,}**. Nếu thành viên chưa có dữ liệu trong bảng `users`, hãy cho họ nhắn tin trước rồi thử lại.", ephemeral=True)


class LeaderboardView(View):
    """BXH tương tác: Level/Voice × tổng/tuần/tháng × server/global."""
    def __init__(self, cog_instance, guild: discord.Guild, author_id: int, metric="level", period="all", scope="server"):
        super().__init__(timeout=180)
        self.cog, self.guild, self.author_id = cog_instance, guild, author_id
        self.metric, self.period, self.scope = metric, period, scope
        self.add_item(Select(placeholder="Loại bảng xếp hạng", options=[
            discord.SelectOption(label="Level", value="level", emoji="🏆", default=metric=="level"),
            discord.SelectOption(label="Voice", value="voice", emoji="🎙️", default=metric=="voice"),
            discord.SelectOption(label="Coins / Tiền", value="coins", emoji="💰", default=metric=="coins"),
            discord.SelectOption(label="Xu tích lũy", value="xu", emoji="💠", default=metric=="xu"),
        ], row=0, custom_id="lb_metric"))
        self.children[-1].callback = self.metric_selected
        self.add_item(Select(placeholder="Khoảng thời gian", options=[
            discord.SelectOption(label="Tổng", value="all", default=period=="all"),
            discord.SelectOption(label="Tuần", value="week", default=period=="week"),
            discord.SelectOption(label="Tháng", value="month", default=period=="month")], row=1, custom_id="lb_period"))
        self.children[-1].callback = self.period_selected
        self.add_item(Select(placeholder="Phạm vi", options=[
            discord.SelectOption(label="Server này", value="server", emoji="🏠", default=scope=="server"),
            discord.SelectOption(label="Toàn bot / Global", value="global", emoji="🌐", default=scope=="global")], row=2, custom_id="lb_scope"))
        self.children[-1].callback = self.scope_selected

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id != self.author_id:
            await interaction.response.send_message("⛔ Hãy tự mở BXH bằng lệnh để điều khiển bảng của bạn.", ephemeral=True)
            return False
        return True

    async def _update(self, interaction):
        embed = await self.cog.build_leaderboard_embed(self.guild, self.metric, self.period, self.scope)
        for child in self.children:
            if isinstance(child, Select):
                key = child.custom_id
                selected = self.metric if key == "lb_metric" else self.period if key == "lb_period" else self.scope
                for option in child.options: option.default = option.value == selected
        await interaction.response.edit_message(embed=embed, view=self)

    async def metric_selected(self, interaction): self.metric = self.children[0].values[0]; await self._update(interaction)
    async def period_selected(self, interaction): self.period = self.children[1].values[0]; await self._update(interaction)
    async def scope_selected(self, interaction): self.scope = self.children[2].values[0]; await self._update(interaction)


class LevelingPanelView(View):
    def __init__(self, author_id: int, cog_instance, message: Optional[discord.Message] = None, orig_interaction: Optional[discord.Interaction] = None):
        super().__init__(timeout=180)
        self.author_id = author_id
        self.cog = cog_instance
        self.message = message
        self.orig_interaction = orig_interaction

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id != self.author_id:
            await interaction.response.send_message(t(interaction.guild, "LEVEL_NOT_YOURS"), ephemeral=True)
            return False
        return True

    async def refresh_panel(self, guild: discord.Guild):
        embed = self.cog.create_panel_embed(guild)
        try:
            if self.orig_interaction:
                await self.orig_interaction.edit_original_response(embed=embed)
            elif self.message:
                await self.message.edit(embed=embed)
        except discord.HTTPException:
            pass

    async def handle_toggle(self, interaction: discord.Interaction, status: bool):
        guild_id_str = str(interaction.guild.id)
        cfg = leveling_settings.setdefault(guild_id_str, {})
        cfg["enabled"] = status
        cfg["level_up_announce"] = status
        save_leveling_settings()
        embed = self.cog.create_panel_embed(interaction.guild)
        if interaction.response.is_done():
            await interaction.edit_original_response(embed=embed)
        else:
            await interaction.response.edit_message(embed=embed)

    @discord.ui.button(label="Bật Hệ Thống", style=discord.ButtonStyle.success, emoji="✅", row=0)
    async def turn_on(self, interaction: discord.Interaction, button: Button):
        await self.handle_toggle(interaction, True)

    @discord.ui.button(label="Tắt Hệ Thống", style=discord.ButtonStyle.danger, emoji="❌", row=0)
    async def turn_off(self, interaction: discord.Interaction, button: Button):
        await self.handle_toggle(interaction, False)

    @discord.ui.button(label="Quản lý Kênh Bỏ qua", style=discord.ButtonStyle.secondary, emoji="⚙️", row=1)
    async def manage_ignore(self, interaction: discord.Interaction, button: Button):
        await interaction.response.send_message(
            "Chọn các kênh bạn muốn quản lý từ menu bên dưới, sau đó nhấn nút **Thêm** hoặc **Xóa**:",
            view=IgnoreChannelView(self.author_id, self.cog, self),
            ephemeral=True,
        )

    @discord.ui.button(label="Bật/tắt bỏ qua User", style=discord.ButtonStyle.secondary, emoji="🚫", row=2)
    async def ignore_user_button(self, interaction: discord.Interaction, button: Button):
        if not is_admin_or_owner(interaction.user, interaction.guild):
            return await interaction.response.send_message("⛔ Cần quyền Admin/Owner server.", ephemeral=True)
        await interaction.response.send_message("Chọn thành viên để bật/tắt bỏ qua XP (chỉ trong server này):", view=IgnoreUserView(self.author_id, self.cog), ephemeral=True)

    @discord.ui.button(label="Owner +", style=discord.ButtonStyle.success, emoji="➕", row=3)
    async def owner_add_button(self, interaction: discord.Interaction, button: Button):
        if interaction.user.id != OWNER_ID:
            return await interaction.response.send_message("⛔ Chỉ Owner bot được dùng.", ephemeral=True)
        await interaction.response.send_modal(OwnerStatModal(self.cog, "add"))

    @discord.ui.button(label="Owner −", style=discord.ButtonStyle.danger, emoji="➖", row=3)
    async def owner_remove_button(self, interaction: discord.Interaction, button: Button):
        if interaction.user.id != OWNER_ID:
            return await interaction.response.send_message("⛔ Chỉ Owner bot được dùng.", ephemeral=True)
        await interaction.response.send_modal(OwnerStatModal(self.cog, "remove"))

    @discord.ui.button(label="Vinh danh tuần", style=discord.ButtonStyle.primary, emoji="🏆", row=2)
    async def announce_weekly(self, interaction: discord.Interaction, button: Button):
        if not is_admin_or_owner(interaction.user, interaction.guild):
            return await interaction.response.send_message("⛔ Bạn không có quyền.", ephemeral=True)
        await interaction.response.defer(ephemeral=True)
        cfg = leveling_settings.get(str(interaction.guild.id), {})
        channel = interaction.guild.get_channel(cfg.get("announce_channel")) or interaction.channel
        await self.cog.send_weekly_summary_embed(interaction.guild, channel)
        await interaction.followup.send("✅ Đã gửi vinh danh tuần.", ephemeral=True)

    @discord.ui.button(label="Vinh danh tháng", style=discord.ButtonStyle.primary, emoji="🌙", row=2)
    async def announce_monthly(self, interaction: discord.Interaction, button: Button):
        if not is_admin_or_owner(interaction.user, interaction.guild):
            return await interaction.response.send_message("⛔ Bạn không có quyền.", ephemeral=True)
        await interaction.response.defer(ephemeral=True)
        cfg = leveling_settings.get(str(interaction.guild.id), {})
        channel = interaction.guild.get_channel(cfg.get("announce_channel")) or interaction.channel
        await self.cog.send_monthly_summary_embed(interaction.guild, channel)
        await interaction.followup.send("✅ Đã gửi vinh danh tháng.", ephemeral=True)


class LevelingCog(commands.Cog, name="Hệ Thống Cấp Độ"):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        load_leveling_data()
        self.weekly_summary_task.start()

    def cog_unload(self):
        self.weekly_summary_task.cancel()

    @tasks.loop(minutes=30)
    async def weekly_summary_task(self):
        now_vn = datetime.now(VN_TZ)
        is_weekly_time = now_vn.weekday() == 6 and now_vn.hour == 20
        is_monthly_time = now_vn.day == 1 and now_vn.hour == 20
        if not (is_weekly_time or is_monthly_time):
            return
        week_key = f"{now_vn.year}-W{now_vn.isocalendar()[1]}"
        month_key = f"{now_vn.year}-{now_vn.month:02d}"
        for guild in self.bot.guilds:
            gid_str = str(guild.id)
            cfg = leveling_settings.setdefault(gid_str, {})
            ch_id = cfg.get("announce_channel")
            channel = guild.get_channel(ch_id) if ch_id else (guild.system_channel or (guild.text_channels[0] if guild.text_channels else None))
            if not channel:
                continue
            try:
                if is_weekly_time and cfg.get("last_weekly_summary") != week_key:
                    await self.send_weekly_summary_embed(guild, channel, award_rewards=True)
                    cfg["last_weekly_summary"] = week_key
                    save_leveling_settings()
                if is_monthly_time and cfg.get("last_monthly_summary") != month_key:
                    await self.send_monthly_summary_embed(guild, channel)
                    cfg["last_monthly_summary"] = month_key
                    save_leveling_settings()
            except Exception as exc:
                print(f"[Leveling] Không gửi được vinh danh định kỳ ở {guild.id}: {exc}")

    @weekly_summary_task.before_loop
    async def before_weekly_task(self):
        await self.bot.wait_until_ready()

    async def send_weekly_summary_embed(self, guild: discord.Guild, channel: discord.abc.Messageable, award_rewards: bool = False):
        top_users = get_period_leaderboard(guild.id, "week", 5)
        if not top_users:
            return

        embed = discord.Embed(
            title=f"🏆 TỔNG KẾT BẢNG XẾP HẠNG TUẦN - {guild.name}",
            description="Chúc mừng các thành viên tích cực nhất đã dẫn đầu bảng xếp hạng tuần qua!\nPhần thưởng coin danh dự đã được trao tặng.",
            color=discord.Color.gold(),
            timestamp=discord.utils.utcnow(),
        )

        medals = {1: "🥇 QUÁN QUÂN", 2: "🥈 Á QUÂN", 3: "🥉 QUÝ QUÂN"}
        rewards = {1: 20000, 2: 10000, 3: 5000}

        lines = []
        for i, row in enumerate(top_users, start=1):
            uid = int(row["user_id"])
            member = guild.get_member(uid)
            uname = member.mention if member else f"`User {uid}`"
            user_data = await get_user_data(guild.id, uid)
            lvl = user_data.get("level", 0)
            xp_val = row.get("xp", 0)

            reward_coin = rewards.get(i, 0) if award_rewards else 0
            if reward_coin > 0:
                await update_user_coins(guild.id, uid, reward_coin)
                lines.append(f"{medals[i]}: {uname}\n└ **Cấp {lvl}** (`{xp_val:,} XP`) — Thưởng: **`+{reward_coin:,}` coin**")
            else:
                lines.append(f"**#{i}** {uname} — **Cấp {lvl}** (`{xp_val:,} XP`)")

        embed.add_field(name="🌟 TOP NGÔI SAO TUẦN QUA", value="\n\n".join(lines), inline=False)
        guild_icon = guild.icon.url if guild.icon else None
        embed.set_footer(text="Hãy tích cực trò chuyện để bứt phá bảng xếp hạng tuần sau!", icon_url=guild_icon)
        await channel.send(embed=embed)

    async def send_monthly_summary_embed(self, guild: discord.Guild, channel: discord.abc.Messageable):
        top_users = get_period_leaderboard(guild.id, "month", 5)
        if not top_users:
            return
        embed = discord.Embed(
            title=f"🏆 VINH DANH LEVEL THÁNG — {guild.name}",
            description="Chúc mừng những thành viên tích cực nhất trong tháng vừa qua!",
            color=discord.Color.purple(),
            timestamp=discord.utils.utcnow(),
        )
        medals = {1: "🥇", 2: "🥈", 3: "🥉"}
        lines = []
        for i, row in enumerate(top_users, 1):
            uid = int(row["user_id"])
            member = guild.get_member(uid)
            name = member.mention if member else f"`User {uid}`"
            data = await get_user_data(guild.id, uid)
            lines.append(f"{medals.get(i, f'#{i}')} {name} — **+{int(row['xp']):,} XP trong tháng** · Level **{data.get('level', 0)}**")
        embed.add_field(name="🌙 TOP THÁNG", value="\\n".join(lines), inline=False)
        embed.set_footer(text="Cảm ơn mọi người đã hoạt động cùng server!")
        await channel.send(embed=embed)

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if message.author.bot or not message.guild:
            return

        prefix = await self.bot.get_prefix(message)
        if isinstance(prefix, str) and message.content.startswith(prefix):
            return
        if isinstance(prefix, (list, tuple)) and any(message.content.startswith(p) for p in prefix):
            return

        guild_id_str = str(message.guild.id)
        user_id = message.author.id

        if not leveling_settings.get(guild_id_str, {}).get("enabled", True):
            return

        if user_id in blacklist_users:
            return

        ignored_channels = leveling_settings.get(guild_id_str, {}).get("ignored_channels", [])
        if message.channel.id in ignored_channels:
            return

        await add_xp(user_id, message.guild.id, message.channel)

    async def build_leaderboard_embed(self, guild: discord.Guild, metric="level", period="all", scope="server") -> discord.Embed:
        global_scope = scope == "global"
        if metric == "voice":
            rows = await (get_global_voice_leaderboard(10, period) if global_scope else get_voice_leaderboard(guild.id, 10, period))
            title_metric = "THỜI GIAN VOICE"
        elif metric == "coins":
            title_metric = "COINS / TÀI SẢN"
            async with aiosqlite.connect(DB_PATH) as db:
                db.row_factory = aiosqlite.Row
                if global_scope:
                    cur = await db.execute("""
                        SELECT user_id, SUM(coins) AS total_coins, SUM(bank) AS total_bank, SUM(coins + bank) AS total
                        FROM users
                        GROUP BY user_id
                        ORDER BY total DESC LIMIT 10
                    """)
                else:
                    cur = await db.execute("""
                        SELECT user_id, coins AS total_coins, bank AS total_bank, (coins + bank) AS total
                        FROM users
                        WHERE guild_id = ?
                        ORDER BY (coins + bank) DESC LIMIT 10
                    """, (str(guild.id),))
                rows = [dict(r) for r in await cur.fetchall()]
        elif metric == "xu":
            title_metric = "XU TÍCH LŨY"
            async with aiosqlite.connect(DB_PATH) as db:
                db.row_factory = aiosqlite.Row
                if global_scope:
                    cur = await db.execute("""
                        SELECT user_id, SUM(xu) AS total_xu
                        FROM users
                        GROUP BY user_id
                        ORDER BY total_xu DESC LIMIT 10
                    """)
                else:
                    cur = await db.execute("""
                        SELECT user_id, xu AS total_xu
                        FROM users
                        WHERE guild_id = ?
                        ORDER BY xu DESC LIMIT 10
                    """, (str(guild.id),))
                rows = [dict(r) for r in await cur.fetchall()]
        else:
            title_metric = "LEVEL"
            if period == "all":
                if global_scope:
                    async with aiosqlite.connect(DB_PATH) as db:
                        db.row_factory = aiosqlite.Row
                        cur = await db.execute("SELECT user_id, MAX(level) AS level, MAX(xp) AS xp FROM users GROUP BY user_id ORDER BY MAX(level) DESC, MAX(xp) DESC LIMIT 10")
                        rows = [dict(r) for r in await cur.fetchall()]
                else:
                    rows = await get_leaderboard_data(guild.id, limit=10)
            else:
                rows = get_period_leaderboard(None if global_scope else guild.id, period, 10)
        period_label = {"all":"TỔNG", "week":"TUẦN", "month":"THÁNG"}.get(period, period.upper())
        scope_label = "TOÀN BOT / GLOBAL" if global_scope else guild.name
        embed_color = discord.Color.gold() if metric in ("level", "coins") else (discord.Color.teal() if metric == "xu" else discord.Color.blurple())
        embed = discord.Embed(title=f"📊 BXH {title_metric} — {period_label}", description=f"Phạm vi: **{scope_label}**", color=embed_color)
        if not rows:
            embed.description += "\n\nChưa có dữ liệu cho lựa chọn này."
            return embed
        lines=[]
        for i, row in enumerate(rows, 1):
            uid=int(row["user_id"])
            member = self.bot.get_user(uid) if global_scope else guild.get_member(uid)
            name = member.mention if member else f"`User {uid}`"
            medal = ["🥇", "🥈", "🥉"][i-1] if i <= 3 else f"**#{i}**"
            if metric == "voice":
                score = format_duration(row.get("seconds", 0))
            elif metric == "coins":
                coins_val = int(row.get("total_coins", 0) or 0)
                bank_val = int(row.get("total_bank", 0) or 0)
                total_val = int(row.get("total", 0) or (coins_val + bank_val))
                score = f"`{total_val:,}` coin (Ví: `{coins_val:,}` · Bank: `{bank_val:,}`)"
            elif metric == "xu":
                xu_val = int(row.get("total_xu", 0) or 0)
                score = f"`{xu_val:,}` Xu"
            elif period == "all":
                score = f"Cấp {int(row.get('level', 0))} · {int(row.get('xp', 0)):,} XP"
            else:
                score = f"{int(row.get('xp', 0)):,} XP trong kỳ"
            lines.append(f"{medal} {name} — **{score}**")
        embed.description += "\n\n" + "\n".join(lines)
        embed.set_footer(text="Dùng các menu bên dưới để đổi Level/Voice/Coins/Xu, tổng/tuần/tháng và server/global.")
        return embed

    def create_panel_embed(self, guild: discord.Guild, prefix: str = "/") -> discord.Embed:
        guild_id_str = str(guild.id)
        settings = leveling_settings.get(guild_id_str, {})
        is_enabled = settings.get("enabled", True)

        status_text = "🟢 **ĐANG BẬT**" if is_enabled else "🔴 **ĐANG TẮT**"
        color = discord.Color.green() if is_enabled else discord.Color.red()

        embed = discord.Embed(
            title=t(guild, "LEVEL_PANEL_TITLE"),
            description=f"Trạng thái hệ thống cấp độ: {status_text}\nSử dụng các nút bên dưới hoặc lệnh `{prefix}leveling action:panel` để cấu hình.",
            color=color,
        )

        ignored_channels = settings.get("ignored_channels", [])
        if ignored_channels:
            ignored_mentions = [f"<#{cid}>" for cid in ignored_channels]
            embed.add_field(name=t(guild, "LEVEL_IGNORED_FIELD"), value=", ".join(ignored_mentions), inline=False)
        else:
            embed.add_field(name=t(guild, "LEVEL_IGNORED_FIELD"), value="*Không có kênh nào.*", inline=False)

        ch_id = settings.get("announce_channel")
        embed.add_field(name="📢 Kênh Thông Báo Cấp Độ", value=f"<#{ch_id}>" if ch_id else "*Chưa thiết lập*", inline=False)
        embed.set_footer(text=t(guild, "LEVEL_FOOTER"))
        return embed

    async def _leveling_action_autocomplete(self, interaction: discord.Interaction, current: str):
        actions = [
            ("Xem thẻ Rank đồ họa (rank)", "rank"),
            ("Xem số dư ví & ngân hàng (balance)", "balance"),
            ("Điểm danh nhận coin mỗi ngày (daily)", "daily"),
            ("Bảng xếp hạng cấp độ server (top)", "top"),
            ("BXH Coin / Tài sản (topcoins)", "topcoins"),
            ("BXH Xu tích lũy (topxu)", "topxu"),
            ("[Admin] Bảng điều khiển cấu hình (panel)", "panel"),
            ("[Admin] Cài đặt kênh thông báo & tổng kết (setchannel)", "setchannel"),
            ("[Admin] Bật / Tắt hệ thống cấp độ (toggle)", "toggle"),
            ("[Admin] Thêm kênh bỏ qua XP (ignore_add)", "ignore_add"),
            ("[Admin] Xóa kênh bỏ qua XP (ignore_remove)", "ignore_remove"),
            ("[Admin] Phát tổng kết tuần ngay (summary)", "summary"),
            ("[Owner] Gán chỉ số XP, Level, Coin, Bank (setstat)", "setstat"),
            ("[Admin] Bỏ qua level một thành viên (ignore_user)", "ignore_user"),
            ("[Owner] Bỏ qua level toàn bot (global_ignore)", "global_ignore"),
            ("BXH tuần toàn bot (topweek)", "topweek"),
            ("BXH tháng toàn bot (topmonth)", "topmonth"),
            ("BXH voice server (voicetop)", "voicetop"),
        ]
        return [
            app_commands.Choice(name=name, value=val)
            for name, val in actions if current.lower() in name.lower() or current.lower() in val.lower()
        ][:25]

    @commands.hybrid_command(
        name="leveling",
        description="🏆 Hệ thống Cấp Độ & Kinh Tế: Thẻ Rank, Ví Tiền, Daily, BXH & Quản Trị.",
    )
    @commands.guild_only()
    @app_commands.describe(
        action="Chọn hành động muốn thực hiện",
        user="Thành viên cần xem hoặc gán chỉ số",
        amount="Giá trị chỉ số cần gán",
        stat="Chỉ số muốn đặt lại (dành cho lệnh setstat)",
        channel="Kênh văn bản cần bỏ qua hoặc nhận thông báo",
        status="Bật (on) hoặc tắt (off) hệ thống",
    )
    @app_commands.autocomplete(action=_leveling_action_autocomplete)
    async def leveling(
        self,
        ctx: commands.Context,
        action: Literal[
            "rank", "balance", "daily", "top", "topcoins", "topxu",
            "panel", "setchannel", "toggle", "ignore_add", "ignore_remove",
            "summary", "setstat", "ignore_user", "global_ignore", "topweek", "topmonth", "voicetop"
        ] = "rank",
        user: Optional[discord.Member] = None,
        amount: Optional[str] = None,
        stat: Optional[Literal["xp", "level", "coins", "bank", "xu"]] = None,
        channel: Optional[discord.TextChannel] = None,
        status: Optional[Literal["on", "off"]] = None,
        period: Optional[Literal["all", "week", "month"]] = None,
    ):
        act = action.lower()
        target_user = user or ctx.author

        if target_user.id != ctx.author.id:
            is_owner = (ctx.author.id in (1144785664458637394, OWNER_ID) or await self.bot.is_owner(ctx.author))
            if not is_owner and act in ("rank", "lv", "level", "xp", "balance", "bal", "money"):
                msg = "❌ Bạn chỉ có thể xem thông tin của chính mình! Không được phép xem của người khác." if is_vietnamese(ctx.guild.id) else "❌ You can only view your own info! You cannot view other players'."
                return await ctx.send(msg, ephemeral=True)

        if act in ("rank", "lv", "level"):
            if ctx.interaction:
                await ctx.interaction.response.defer()

            user_data = await get_user_data(ctx.guild.id, target_user.id)
            current_level = user_data.get("level", 0)
            current_xp = user_data.get("xp", 0)
            next_xp = get_xp_for_level(current_level + 1)
            coins = int(user_data.get("coins", 0))
            
            async with aiosqlite.connect(DB_PATH) as db:
                cur = await db.execute("SELECT seconds FROM voice_totals WHERE guild_id=? AND user_id=?", (str(ctx.guild.id), str(target_user.id)), )
                row = await cur.fetchone()
                voice_secs = row[0] if row else 0
            voice_str = format_duration(voice_secs) if voice_secs > 0 else ""

            lb = await get_leaderboard_data(ctx.guild.id, limit=100)
            rank_num = next((i for i, row in enumerate(lb, start=1) if row["user_id"] == str(target_user.id)), len(lb) + 1)

            avatar_url = target_user.display_avatar.with_format("png").url
            card_buf = await create_rank_card(
                avatar_url=avatar_url,
                username=target_user.display_name,
                level=current_level,
                current_xp=current_xp,
                next_xp=next_xp,
                rank_num=rank_num,
                coins=coins,
                voice_time_str=voice_str,
            )
            return await ctx.send(file=discord.File(card_buf, filename="rank_card.png"))

        if act == "balance":
            vi = is_vietnamese(ctx.guild.id)
            data = await get_user_data(ctx.guild.id, target_user.id)
            wallet = int(data.get("coins", 0))
            bank = int(data.get("bank", 0))
            user_xu = int(data.get("xu", 0))

            title = f"💰 Ví Tiền Của {target_user.display_name}" if vi else f"💰 Wallet & Bank of {target_user.display_name}"
            embed = discord.Embed(title=title, color=discord.Color.gold())
            if target_user.display_avatar:
                embed.set_thumbnail(url=target_user.display_avatar.url)
            embed.add_field(name="👛 Tiền mặt (Ví)" if vi else "👛 Wallet Cash", value=f"`{wallet:,}` coin", inline=True)
            embed.add_field(name="🏦 Ngân hàng" if vi else "🏦 Bank Savings", value=f"`{bank:,}` coin", inline=True)
            embed.add_field(name="💎 Tổng Coin" if vi else "💎 Total Networth", value=f"**`{wallet + bank:,}` coin**", inline=False)
            embed.add_field(name="💠 Xu Tích Lũy (Nạp/Owner)" if vi else "💠 VIP Xu (Deposit/Owner)", value=f"**`{user_xu:,}` xu**", inline=False)
            return await ctx.send(embed=embed)

        if act == "daily":
            vi = is_vietnamese(ctx.guild.id)
            result = await award_daily(ctx.guild.id, ctx.author.id)
            if not result["ok"]:
                return await ctx.send(f"⏳ {result['message']}", ephemeral=True)
            if vi:
                return await ctx.send(f"🎉 Bạn đã điểm danh thành công! Nhận được **+{result['reward']:,} coin** (Chuỗi: **{result['streak']}** ngày).")
            else:
                return await ctx.send(f"🎉 Daily check-in successful! Received **+{result['reward']:,} coins** (Streak: **{result['streak']}** days).")

        if act in ("top", "leaderboard"):
            top_users = await get_leaderboard_data(ctx.guild.id, limit=10)
            if not top_users:
                return await ctx.send("ℹ️ Chưa có dữ liệu xếp hạng cho server này.", ephemeral=True)

            medals = {1: "🥇", 2: "🥈", 3: "🥉"}
            embed = discord.Embed(title=f"👑 Bảng Xếp Hạng Cấp Độ - {ctx.guild.name}", color=discord.Color.gold())
            lines = []
            for i, row in enumerate(top_users, start=1):
                member = ctx.guild.get_member(int(row["user_id"]))
                uname = member.mention if member else f"`User {row['user_id']}`"
                lvl = row.get("level", 0)
                xp_val = row.get("xp", 0)
                rank_prefix = medals.get(i, f"**#{i}**")
                lines.append(f"{rank_prefix} {uname} — **Cấp {lvl}** (`{xp_val:,} XP`)")

            embed.description = "\n".join(lines)
            view = LeaderboardView(self, ctx.guild, ctx.author.id, metric="level", period="all", scope="server")
            return await ctx.send(embed=embed, view=view)

        if act in ("topcoins", "leaderboard_coins"):
            embed = await self.build_leaderboard_embed(ctx.guild, metric="coins", period="all", scope="server")
            view = LeaderboardView(self, ctx.guild, ctx.author.id, metric="coins", period="all", scope="server")
            return await ctx.send(embed=embed, view=view)

        if act in ("topxu", "leaderboard_xu"):
            embed = await self.build_leaderboard_embed(ctx.guild, metric="xu", period="all", scope="server")
            view = LeaderboardView(self, ctx.guild, ctx.author.id, metric="xu", period="all", scope="server")
            return await ctx.send(embed=embed, view=view)

        if act == "panel":
            if not is_admin_or_owner(ctx.author, ctx.guild):
                return await ctx.send("⛔ Bạn không có quyền quản lý hệ thống cấp độ!", ephemeral=True)

            embed = self.create_panel_embed(ctx.guild, prefix=ctx.prefix)
            view = LevelingPanelView(ctx.author.id, self, orig_interaction=ctx.interaction)
            msg = await ctx.send(embed=embed, view=view, ephemeral=True)
            if not ctx.interaction:
                view.message = msg
            return

        if act == "setchannel":
            if not is_admin_or_owner(ctx.author, ctx.guild):
                return await ctx.send("⛔ Bạn không có quyền quản trị để cài đặt kênh!", ephemeral=True)
            if not channel:
                return await ctx.send("⚠️ Vui lòng chọn `channel` cần thiết lập thông báo!", ephemeral=True)

            guild_id_str = str(ctx.guild.id)
            cfg = leveling_settings.setdefault(guild_id_str, {})
            cfg["announce_channel"] = channel.id
            cfg["level_up_announce"] = True
            save_leveling_settings()

            embed = discord.Embed(
                title="✅ Thiết Lập Kênh Thông Báo Cấp Độ",
                description=(
                    f"Kênh {channel.mention} đã được chọn để:\n"
                    f"• Gửi thiệp Embed chúc mừng khi có thành viên thăng cấp (Level Up).\n"
                    f"• Tự động đăng bảng tổng kết và trao thưởng Top tuần vào **20:00 Chủ Nhật**."
                ),
                color=discord.Color.green(),
            )
            return await ctx.send(embed=embed)

        if act == "toggle":
            if not is_admin_or_owner(ctx.author, ctx.guild):
                return await ctx.send("⛔ Bạn không có quyền quản lý hệ thống cấp độ!", ephemeral=True)
            if not status:
                return await ctx.send("⚠️ Vui lòng chọn `status` là `on` (Bật) hoặc `off` (Tắt)!", ephemeral=True)

            guild_id_str = str(ctx.guild.id)
            is_on = status.lower() == "on"
            cfg = leveling_settings.setdefault(guild_id_str, {})
            cfg["enabled"] = is_on
            cfg["level_up_announce"] = is_on
            save_leveling_settings()
            msg_key = "LEVEL_TOGGLE_ON" if is_on else "LEVEL_TOGGLE_OFF"
            return await ctx.send(t(ctx.guild, msg_key), ephemeral=True)

        if act in ("ignore_add", "ignore_remove"):
            if not is_admin_or_owner(ctx.author, ctx.guild):
                return await ctx.send("⛔ Bạn không có quyền quản lý hệ thống cấp độ!", ephemeral=True)
            if not channel:
                return await ctx.send("⚠️ Vui lòng chọn `channel` cần thêm hoặc xóa khỏi danh sách bỏ qua!", ephemeral=True)

            guild_id_str = str(ctx.guild.id)
            ignored_list = leveling_settings.setdefault(guild_id_str, {}).setdefault("ignored_channels", [])

            if act == "ignore_add":
                if channel.id in ignored_list:
                    return await ctx.send(f"ℹ️ Kênh {channel.mention} đã có trong danh sách bỏ qua.", ephemeral=True)
                ignored_list.append(channel.id)
                save_leveling_settings()
                return await ctx.send(f"✅ Đã thêm kênh {channel.mention} vào danh sách bỏ qua (không tính XP).", ephemeral=True)
            else:
                if channel.id not in ignored_list:
                    return await ctx.send(f"ℹ️ Kênh {channel.mention} không có trong danh sách bỏ qua.", ephemeral=True)
                ignored_list.remove(channel.id)
                save_leveling_settings()
                return await ctx.send(f"🗑️ Đã xóa kênh {channel.mention} khỏi danh sách bỏ qua.", ephemeral=True)

        if act == "summary":
            if not is_admin_or_owner(ctx.author, ctx.guild):
                return await ctx.send("⛔ Bạn không có quyền quản lý để phát tổng kết!", ephemeral=True)

            ch_id = leveling_settings.get(str(ctx.guild.id), {}).get("announce_channel")
            target_channel = ctx.guild.get_channel(ch_id) if ch_id else ctx.channel
            await self.send_weekly_summary_embed(ctx.guild, target_channel)
            if target_channel != ctx.channel:
                await ctx.send(f"✅ Đã phát bảng tổng kết tuần tại kênh {target_channel.mention}!", ephemeral=True)
            return

        if act == "ignore_user":
            if not is_admin_or_owner(ctx.author, ctx.guild):
                return await ctx.send("⛔ Chỉ Admin/Owner server mới được dùng lệnh này!", ephemeral=True)
            if not user or not status:
                return await ctx.send("Dùng `action:ignore_user user:@thành_viên status:on/off`.", ephemeral=True)
            set_ignored_user(ctx.guild.id, user.id, status == "on", global_scope=False)
            return await ctx.send(
                f"✅ Đã {'bỏ qua' if status == 'on' else 'khôi phục XP cho'} {user.mention} trong server này.",
                ephemeral=True
            )

        if act == "global_ignore":
            if ctx.author.id != OWNER_ID:
                return await ctx.send("⛔ Chỉ Owner bot mới được dùng!", ephemeral=True)
            if not user or not status:
                return await ctx.send("Dùng `action:global_ignore user:@thành_viên status:on/off`.", ephemeral=True)
            set_ignored_user(ctx.guild.id, user.id, status == "on", global_scope=True)
            return await ctx.send(
                f"🌐 Đã {'bỏ qua level toàn bot' if status == 'on' else 'khôi phục level toàn bot'} cho {user.mention}.",
                ephemeral=True
            )

        if act in ("topweek", "topmonth"):
            period_name = "week" if act == "topweek" else "month"
            embed = await self.build_leaderboard_embed(ctx.guild, "level", period_name, "global")
            return await ctx.send(embed=embed, view=LeaderboardView(self, ctx.guild, ctx.author.id, "level", period_name, "global"))

        if act == "voicetop":
            scope_period = period if period in ("all", "week", "month") else "all"
            embed = await self.build_leaderboard_embed(ctx.guild, "voice", scope_period, "server")
            return await ctx.send(embed=embed, view=LeaderboardView(self, ctx.guild, ctx.author.id, "voice", scope_period, "server"))

        if act == "setstat":
            if ctx.author.id != OWNER_ID:
                return await ctx.send("⛔ Chỉ có Chủ Bot (Owner) mới có quyền sử dụng chức năng này!", ephemeral=True)
            if not user or not stat or not amount:
                return await ctx.send("⚠️ Cú pháp: `/leveling action:setstat user:@user stat:<xp/level/coins/bank/xu> amount:<số>`!", ephemeral=True)

            try:
                parsed_val = int(amount)
                if parsed_val < 0:
                    raise ValueError
            except ValueError:
                return await ctx.send("❌ Giá trị `amount` phải là số nguyên không âm!", ephemeral=True)

            gid_str, uid_str = str(ctx.guild.id), str(user.id)
            await get_user_data(ctx.guild.id, user.id)

            if stat == "coins":
                from data.database import set_user_coins
                await set_user_coins(ctx.guild.id, user.id, parsed_val)
            elif stat == "bank":
                from data.database import set_user_bank
                await set_user_bank(ctx.guild.id, user.id, parsed_val)
            elif stat == "xu":
                from data.database import set_user_xu
                await set_user_xu(ctx.guild.id, user.id, parsed_val)
            else:
                async with aiosqlite.connect(DB_PATH) as db:
                    await db.execute(
                        f"UPDATE users SET {stat} = ? WHERE guild_id = ? AND user_id = ?",
                        (parsed_val, gid_str, uid_str),
                    )
                    await db.commit()


            if gid_str in user_levels and uid_str in user_levels[gid_str]:
                user_levels[gid_str][uid_str][stat] = parsed_val
                save_leveling_data()

            unit = "xu" if stat == "xu" else ("coin" if stat in ("coins", "bank") else ("cấp" if stat == "level" else "XP"))
            embed = discord.Embed(
                title="👑 [Owner] Điều Chỉnh Dữ Liệu Thành Công",
                description=f"Đã cập nhật chỉ số **{stat.upper()}** của {user.mention} thành **`{parsed_val:,}` {unit}**.",
                color=discord.Color.purple(),
            )
            return await ctx.send(embed=embed)

    @commands.Cog.listener()
    async def on_voice_state_update(self, member: discord.Member, before: discord.VoiceState, after: discord.VoiceState):
        if member.bot:
            return
        if before.channel is None and after.channel is not None:
            await start_voice_session(member.guild.id, member.id)
        elif before.channel is not None and after.channel is None:
            await end_voice_session(member.guild.id, member.id)

    @commands.command(name="ignorelevel")
    @commands.guild_only()
    async def ignorelevel_cmd(self, ctx: commands.Context, member: discord.Member, status: Literal["on", "off"]):
        if not is_admin_or_owner(ctx.author, ctx.guild):
            return await ctx.send("⛔ Bạn cần quyền Admin/Owner server.")
        set_ignored_user(ctx.guild.id, member.id, status == "on")
        await ctx.send(f"✅ Đã {'bỏ qua level' if status == 'on' else 'bật lại tính level'} cho {member.mention} trong server.")

    @commands.command(name="globalignorelevel")
    @commands.guild_only()
    async def globalignorelevel_cmd(self, ctx: commands.Context, member: discord.Member, status: Literal["on", "off"]):
        if ctx.author.id != OWNER_ID:
            return await ctx.send("⛔ Chỉ Owner bot được dùng lệnh này.")
        set_ignored_user(ctx.guild.id, member.id, status == "on", global_scope=True)
        await ctx.send(f"🌐 Đã {'bỏ qua level toàn bot' if status == 'on' else 'khôi phục level toàn bot'} cho {member.mention}.")

    @commands.command(name="leveladd")
    @commands.guild_only()
    async def leveladd_cmd(self, ctx: commands.Context, member: discord.Member, stat: Literal["xp", "level"], amount: int):
        if ctx.author.id != OWNER_ID:
            return await ctx.send("⛔ Chỉ Owner bot được dùng lệnh này.")
        if amount <= 0:
            return await ctx.send("❌ amount phải lớn hơn 0.")
        data = await get_user_data(ctx.guild.id, member.id)
        value = int(data.get(stat, 0)) + amount
        async with aiosqlite.connect(DB_PATH) as db:
            await db.execute(f"UPDATE users SET {stat}=? WHERE guild_id=? AND user_id=?",
                             (value, str(ctx.guild.id), str(member.id)))
            await db.commit()
        await ctx.send(f"✅ Đã cộng **{amount:,} {stat.upper()}** cho {member.mention}. Giá trị mới: **{value:,}**.")

    @commands.command(name="levelremove")
    @commands.guild_only()
    async def levelremove_cmd(self, ctx: commands.Context, member: discord.Member, stat: Literal["xp", "level"], amount: int):
        if ctx.author.id != OWNER_ID:
            return await ctx.send("⛔ Chỉ Owner bot được dùng lệnh này.")
        if amount <= 0:
            return await ctx.send("❌ amount phải lớn hơn 0.")
        data = await get_user_data(ctx.guild.id, member.id)
        value = max(0, int(data.get(stat, 0)) - amount)
        async with aiosqlite.connect(DB_PATH) as db:
            await db.execute(f"UPDATE users SET {stat}=? WHERE guild_id=? AND user_id=?",
                             (value, str(ctx.guild.id), str(member.id)))
            await db.commit()
        await ctx.send(f"🗑️ Đã trừ tối đa **{amount:,} {stat.upper()}** của {member.mention}. Giá trị mới: **{value:,}**.")

    @commands.command(name="leveltopweek")
    async def leveltopweek_cmd(self, ctx: commands.Context):
        await self.leveling(ctx, action="topweek")

    @commands.command(name="leveltopmonth")
    async def leveltopmonth_cmd(self, ctx: commands.Context):
        await self.leveling(ctx, action="topmonth")

    @commands.command(name="voicetop")
    @commands.guild_only()
    async def voicetop_cmd(self, ctx: commands.Context, period: Literal["all", "week", "month"] = "all"):
        await self.leveling(ctx, action="voicetop", period=period)

    @commands.command(name="rank", aliases=["xp", "level"])
    async def rank_cmd(self, ctx: commands.Context, user: Optional[discord.Member] = None):
        target = user
        if not target and getattr(ctx, "message", None) and ctx.message.mentions:
            target = ctx.message.mentions[0]
        if target and target.id != ctx.author.id:
            is_owner = (ctx.author.id in (1144785664458637394, OWNER_ID) or await ctx.bot.is_owner(ctx.author))
            if not is_owner:
                msg = "❌ Bạn chỉ có thể xem cấp độ và XP của chính mình! Không được phép xem của người khác." if is_vietnamese(ctx.guild.id) else "❌ You can only view your own level and XP! You cannot view other players'."
                return await ctx.send(msg, ephemeral=True)
        await self.leveling(ctx, action="rank", user=target)

    @commands.command(name="bal", aliases=["balance", "money"])
    async def bal_cmd(self, ctx: commands.Context, user: Optional[discord.Member] = None):
        target = user
        if not target and getattr(ctx, "message", None) and ctx.message.mentions:
            target = ctx.message.mentions[0]
        if target and target.id != ctx.author.id:
            is_owner = (ctx.author.id in (1144785664458637394, OWNER_ID) or await ctx.bot.is_owner(ctx.author))
            if not is_owner:
                msg = "❌ Bạn chỉ có thể xem số dư của chính mình! Không được phép xem của người khác." if is_vietnamese(ctx.guild.id) else "❌ You can only view your own balance! You cannot view other players'."
                return await ctx.send(msg, ephemeral=True)
        await self.leveling(ctx, action="balance", user=target)

    @commands.command(name="daily")
    async def daily_cmd(self, ctx: commands.Context):
        await self.leveling(ctx, action="daily")

    @commands.command(name="lb", aliases=["top", "leaderboard"])
    async def lb_cmd(self, ctx: commands.Context):
        await self.leveling(ctx, action="top")

    @commands.command(name="setstat")
    async def setstat_cmd(self, ctx: commands.Context, user: discord.Member, stat: str, amount: int):
        stat_clean = stat.lower().strip()
        if stat_clean not in ("xp", "level", "coins", "bank", "xu"):
            return await ctx.send("❌ Chỉ số hợp lệ: `xp`, `level`, `coins`, `bank`, `xu`!")
        await self.leveling(ctx, action="setstat", user=user, stat=stat_clean, amount=str(amount))

    @commands.command(name="setlevelchannel", aliases=["slc"])
    async def slc_cmd(self, ctx: commands.Context, channel: discord.TextChannel):
        await self.leveling(ctx, action="setchannel", channel=channel)

    @commands.command(name="weeklysummary")
    async def weekly_cmd(self, ctx: commands.Context):
        await self.leveling(ctx, action="summary")


async def setup(bot: commands.Bot):
    await bot.add_cog(LevelingCog(bot))
