from Check.i18n import t, is_vietnamese
import asyncio
import datetime
import json
import random
import re
import sqlite3
import discord
from discord.ext import commands, tasks

DB_PATH = "data/giveaways.db"
GACHA_KEYWORDS = ["thẻ tháng", "the thang", "genshin", "honkai", "gacha", "star rail", "zenless"]


def parse_duration(time_str: str) -> int | None:
    if not time_str:
        return None
    match = re.match(r"^(\d+)([smhd])$", time_str.strip().lower())
    if not match:
        return None
    val, unit = match.groups()
    multipliers = {"s": 1, "m": 60, "h": 3600, "d": 86400}
    return int(val) * multipliers[unit]


# ==========================================
# 1. QUẢN LÝ CƠ SỞ DỮ LIỆU SQLITE
# ==========================================
class Database:
    @staticmethod
    def init():
        with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS giveaways (
                    message_id INTEGER PRIMARY KEY,
                    channel_id INTEGER,
                    guild_id INTEGER,
                    host_id INTEGER,
                    prize TEXT,
                    winners_count INTEGER,
                    end_time REAL,
                    claim_timeout INTEGER,
                    required_role_ids TEXT,
                    reason TEXT,
                    on_failure TEXT,
                    hide_host INTEGER,
                    status TEXT DEFAULT 'running'
                )
            """)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS participants (
                    message_id INTEGER,
                    user_id INTEGER,
                    PRIMARY KEY (message_id, user_id)
                )
            """)
            conn.commit()

    @staticmethod
    def add_giveaway(msg_id, ch_id, guild_id, host_id, prize, winners, end_time, claim_to, roles, reason, on_fail, hide_host):
        with sqlite3.connect(DB_PATH) as conn:
            conn.execute("""
                INSERT INTO giveaways VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'running')
            """, (msg_id, ch_id, guild_id, host_id, prize, winners, end_time, claim_to, json.dumps(roles), reason, on_fail, int(hide_host)))
            conn.commit()

    @staticmethod
    def get_giveaway(msg_id):
        with sqlite3.connect(DB_PATH) as conn:
            conn.row_factory = sqlite3.Row
            return conn.execute("SELECT * FROM giveaways WHERE message_id = ?", (msg_id,)).fetchone()

    @staticmethod
    def get_expired_giveaways():
        now = datetime.datetime.now(datetime.timezone.utc).timestamp()
        with sqlite3.connect(DB_PATH) as conn:
            conn.row_factory = sqlite3.Row
            return conn.execute("SELECT * FROM giveaways WHERE status = 'running' AND end_time <= ?", (now,)).fetchall()

    @staticmethod
    def set_status(msg_id, status):
        with sqlite3.connect(DB_PATH) as conn:
            conn.execute("UPDATE giveaways SET status = ? WHERE message_id = ?", (status, msg_id))
            conn.commit()

    @staticmethod
    def toggle_participant(msg_id, user_id) -> bool:
        """Thêm hoặc xóa người tham gia. Trả về True nếu tham gia, False nếu hủy."""
        with sqlite3.connect(DB_PATH) as conn:
            exists = conn.execute("SELECT 1 FROM participants WHERE message_id = ? AND user_id = ?", (msg_id, user_id)).fetchone()
            if exists:
                conn.execute("DELETE FROM participants WHERE message_id = ? AND user_id = ?", (msg_id, user_id))
                conn.commit()
                return False
            else:
                conn.execute("INSERT INTO participants VALUES (?, ?)", (msg_id, user_id))
                conn.commit()
                return True

    @staticmethod
    def get_participants(msg_id) -> list[int]:
        with sqlite3.connect(DB_PATH) as conn:
            rows = conn.execute("SELECT user_id FROM participants WHERE message_id = ?", (msg_id,)).fetchall()
            return [r[0] for r in rows]

    @staticmethod
    def get_participant_count(msg_id) -> int:
        with sqlite3.connect(DB_PATH) as conn:
            return conn.execute("SELECT COUNT(*) FROM participants WHERE message_id = ?", (msg_id,)).fetchone()[0]


# ==========================================
# 2. VIEW THAM GIA VĨNH VIỄN (PERSISTENT VIEW)
# ==========================================
class PersistentGiveawayView(discord.ui.View):
    def __init__(self, guild=None):
        super().__init__(timeout=None)
        self.guild = guild
        if guild:
            vi = is_vietnamese(guild)
            self.join_button.label = "Tham gia 🎉" if vi else "Join 🎉"

    @discord.ui.button(label="Tham gia 🎉", style=discord.ButtonStyle.primary, custom_id="persistent_gw_join_btn")
    async def join_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        vi = is_vietnamese(interaction.guild)
        msg_id = interaction.message.id
        gw = Database.get_giveaway(msg_id)

        if not gw or gw["status"] != "running":
            await interaction.response.send_message("❌ Giveaway này đã kết thúc hoặc không còn hiệu lực!", ephemeral=True)
            return

        # Kiểm tra Role yêu cầu từ DB
        req_roles = json.loads(gw["required_role_ids"])
        if req_roles:
            user_roles = {r.id for r in interaction.user.roles}
            if not any(rid in user_roles for rid in req_roles):
                role_mentions = ", ".join(f"<@&{rid}>" for rid in req_roles)
                await interaction.response.send_message(f"❌ Bạn không đủ điều kiện! Cần có một trong các role: {role_mentions}", ephemeral=True)
                return

        joined = Database.toggle_participant(msg_id, interaction.user.id)
        count = Database.get_participant_count(msg_id)

        button.label = f"{'Tham gia' if vi else 'Join'} 🎉 ({count})"
        try:
            await interaction.response.edit_message(view=self)
            if joined:
                await interaction.followup.send(t(interaction.guild, "GW_JOIN_SUCCESS"), ephemeral=True)
            else:
                await interaction.followup.send(t(interaction.guild, "GW_LEAVE_SUCCESS"), ephemeral=True)
        except discord.HTTPException:
            pass


# Alias for backward compatibility / web imports
GiveawayView = PersistentGiveawayView


# ==========================================
# 3. MODAL & VIEWS XÁC NHẬN NHẬN QUÀ
# ==========================================
class GameClaimModal(discord.ui.Modal, title="Thông Tin Nhận Quà Game"):
    uid_input = discord.ui.TextInput(label="UID Game & Server", placeholder="VD: 812345678 - Server Asia (Bắt buộc)", required=True, max_length=100)
    acc_input = discord.ui.TextInput(label="Tài khoản (Không bắt buộc)", placeholder="Để trống nếu nạp trực tiếp qua UID", required=False, max_length=100)
    pwd_input = discord.ui.TextInput(label="Mật khẩu (Không bắt buộc)", placeholder="Để trống nếu không cần thiết", required=False, max_length=100)
    note_input = discord.ui.TextInput(label="Ghi chú thêm", placeholder="VD: Có mã xác thực qua email...", required=False, style=discord.TextStyle.paragraph)

    def __init__(self, future: asyncio.Future, host: discord.User | discord.Member, prize: str, channel: discord.TextChannel):
        super().__init__()
        self.future = future
        self.host = host
        self.prize = prize
        self.channel = channel

    async def on_submit(self, interaction: discord.Interaction):
        if not self.future.done():
            self.future.set_result("claimed")

        dm_embed = discord.Embed(
            title="🎁 THÔNG TIN NHẬN QUÀ GAME TỪ NGƯỜI TRÚNG",
            description=(
                f"👤 **Người trúng:** {interaction.user.mention} (`{interaction.user.name}` | ID: `{interaction.user.id}`)\n"
                f"🎁 **Phần thưởng:** **{self.prize}**\n"
                f"📢 **Kênh:** {self.channel.mention}\n"
                f"───────────────\n"
                f"🆔 **UID & Server:** `{self.uid_input.value.strip()}`\n"
                f"👤 **Tài khoản:** `{self.acc_input.value.strip() or 'Không cung cấp'}`\n"
                f"🔑 **Mật khẩu:** `{self.pwd_input.value.strip() or 'Không cung cấp'}`\n"
                f"📝 **Ghi chú:** {self.note_input.value.strip() or 'Không có'}\n"
                f"───────────────"
            ),
            color=discord.Color.green(),
            timestamp=datetime.datetime.now(datetime.timezone.utc)
        )
        try:
            await self.host.send(embed=dm_embed)
            await interaction.response.send_message("🎉 **Xác nhận thành công!** Đã gửi kín thông tin UID/Tài khoản đến người tổ chức.", ephemeral=True)
        except (discord.Forbidden, discord.HTTPException):
            await interaction.response.send_message("⚠️ Đã lưu thông tin, nhưng Host đang chặn DM người lạ!", ephemeral=True)


class ClaimView(discord.ui.View):
    def __init__(self, winner_id: int, future: asyncio.Future, timeout: float, is_gacha: bool, host: discord.User | discord.Member, prize: str, channel: discord.TextChannel):
        super().__init__(timeout=timeout)
        self.winner_id = winner_id
        self.future = future
        self.is_gacha = is_gacha
        self.host = host
        self.prize = prize
        self.channel = channel
        vi = is_vietnamese(channel.guild)
        self.claim_btn.label = "Nhận quà 🎁" if vi else "Claim Prize 🎁"
        self.decline_btn.label = "Từ chối ❌" if vi else "Decline ❌" 

    @discord.ui.button(label="Nhận quà 🎁", style=discord.ButtonStyle.success)
    async def claim_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.winner_id:
            await interaction.response.send_message("❌ Nút này chỉ dành cho người trúng giải!", ephemeral=True)
            return

        if self.is_gacha:
            await interaction.response.send_modal(GameClaimModal(self.future, self.host, self.prize, self.channel))
        else:
            if not self.future.done():
                self.future.set_result("claimed")
            await interaction.response.send_message("🎉 Bạn đã xác nhận **Nhận quà** thành công!", ephemeral=True)

    @discord.ui.button(label="Từ chối ❌", style=discord.ButtonStyle.danger)
    async def decline_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.winner_id:
            await interaction.response.send_message("❌ Nút này chỉ dành cho người trúng giải!", ephemeral=True)
            return
        if not self.future.done():
            self.future.set_result("declined")
        await interaction.response.send_message("❌ Bạn đã chọn **Từ chối nhận quà**.", ephemeral=True)


async def handle_winner_claim_slot(channel: discord.TextChannel, winner: discord.Member, prize: str, claim_seconds: int, host_text: str, host: discord.User | discord.Member, is_gacha: bool) -> str:
    deadline_unix = int((datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(seconds=claim_seconds)).timestamp())
    loop = asyncio.get_running_loop()
    future = loop.create_future()

    desc = (
        f"Chúc mừng {winner.mention} đã trúng phần thưởng: **{prize}**!\n\n"
        f"👑 **Người tổ chức:** {host_text}\n"
        f"⏳ **Hạn chót xác nhận:** <t:{deadline_unix}:R> (<t:{deadline_unix}:F>)\n\n"
    )
    if is_gacha:
        desc += "🎮 *Đây là quà game/thẻ tháng. Bấm **Nhận quà 🎁** để điền UID (TK/MK là tùy chọn, không bắt buộc).* \n\n"
    desc += "👉 Bấm **Nhận quà 🎁** hoặc **Từ chối ❌** bên dưới."

    embed = discord.Embed(title="🎁 XÁC NHẬN NHẬN THƯỞNG!", description=desc, color=discord.Color.gold())

    ch_view = ClaimView(winner.id, future, float(claim_seconds), is_gacha, host, prize, channel)
    dm_view = ClaimView(winner.id, future, float(claim_seconds), is_gacha, host, prize, channel)

    ch_msg = await channel.send(content=f"🎉 Chúc mừng {winner.mention}!", embed=embed, view=ch_view)
    dm_msg = None
    try:
        dm_msg = await winner.send(content=f"🎉 Bạn vừa trúng giveaway **{prize}** tại **{channel.guild.name}**!", embed=embed, view=dm_view)
    except (discord.Forbidden, discord.HTTPException):
        await channel.send(f"⚠️ *{winner.mention} đang chặn DM. Vui lòng thao tác tại kênh chat!*", delete_after=10)

    try:
        result = await asyncio.wait_for(future, timeout=float(claim_seconds))
    except asyncio.TimeoutError:
        result = "timeout"

    for b in ch_view.children:
        b.disabled = True
    for b in dm_view.children:
        b.disabled = True

    status_text = {
        "claimed": f"✅ {winner.mention} đã **XÁC NHẬN NHẬN QUÀ**!",
        "declined": f"❌ {winner.mention} đã **TỪ CHỐI** nhận giải.",
        "timeout": f"⏰ {winner.mention} đã **QUÁ HẠN** nhận thưởng."
    }[result]

    end_claim_embed = discord.Embed(title="📋 Trạng Thái Nhận Giải", description=f"🎁 **Quà:** {prize}\n👤 **Người trúng:** {winner.mention}\n📌 **Kết quả:** {status_text}", color=discord.Color.blue())
    try:
        await ch_msg.edit(embed=end_claim_embed, view=ch_view)
    except discord.HTTPException:
        pass
    if dm_msg:
        try:
            await dm_msg.edit(embed=end_claim_embed, view=dm_view)
        except discord.HTTPException:
            pass

    return result


# ==========================================
# 4. GIAO DIỆN SETUP VÀ MODAL TẠO GIVEAWAY
# ==========================================
class GiveawayInfoModal(discord.ui.Modal, title="Thông Tin Giveaway"):
    prize_input = discord.ui.TextInput(label="Phần thưởng", placeholder="VD: Thẻ tháng Genshin, Nitro...", required=True)
    duration_input = discord.ui.TextInput(label="Thời gian diễn ra", placeholder="VD: 30s, 10m, 2h, 1d", required=True)
    winners_input = discord.ui.TextInput(label="Số lượng người trúng", placeholder="Mặc định: 1", default="1", required=True)
    claim_timeout_input = discord.ui.TextInput(label="Hạn nhận giải (Claim Timeout)", placeholder="VD: 60s, 5m (Mặc định: 60s)", default="60s", required=True)
    reason_input = discord.ui.TextInput(label="Lý do / Sự kiện (Tùy chọn)", placeholder="VD: Mừng sinh nhật server...", required=False, style=discord.TextStyle.paragraph)

    def __init__(self, target_channel: discord.TextChannel, roles: list[discord.Role], on_failure: str, hide_host: bool, setup_msg: discord.Message):
        super().__init__()
        self.target_channel = target_channel
        self.roles = roles
        self.on_failure = on_failure
        self.hide_host = hide_host
        self.setup_msg = setup_msg

    async def on_submit(self, interaction: discord.Interaction):
        seconds = parse_duration(self.duration_input.value)
        if not seconds:
            await interaction.response.send_message("❌ Thời gian không hợp lệ!", ephemeral=True)
            return

        claim_seconds = parse_duration(self.claim_timeout_input.value) or 60

        try:
            winners = int(self.winners_input.value.strip())
            if winners <= 0:
                raise ValueError
        except ValueError:
            await interaction.response.send_message("❌ Số người trúng phải là số nguyên > 0!", ephemeral=True)
            return

        reason = self.reason_input.value.strip() or None
        end_time = datetime.datetime.now(datetime.timezone.utc).timestamp() + seconds
        end_unix = int(end_time)

        is_gacha = any(kw in self.prize_input.value.lower() for kw in GACHA_KEYWORDS)
        host_text = "Ẩn danh 🎭" if self.hide_host else interaction.user.mention
        roles_text = ", ".join(r.mention for r in self.roles) if self.roles else "Tất cả mọi người (`All`)"
        failure_text = "Quay người khác (Reroll)" if self.on_failure == "reroll" else "Hủy giải"

        embed = discord.Embed(title=f"🎁 GIVEAWAY: {self.prize_input.value}", color=discord.Color.gold())
        desc = f"📝 **Lý do / Sự kiện:** {reason}\n\n" if reason else ""
        desc += (
            f"Bấm nút bên dưới để tham gia!\n\n"
            f"🏆 **Số giải:** `{winners}`\n"
            f"👑 **Người tổ chức:** {host_text}\n"
            f"🛡️ **Yêu cầu Role:** {roles_text}\n"
            f"⏱️ **Hạn nhận quà:** `{claim_seconds}s` ({failure_text})\n"
        )
        if is_gacha:
            desc += "🎮 **Loại quà:** Game Gacha / Thẻ tháng (Điền UID khi trúng)\n"
        desc += f"⏳ **Kết thúc lúc:** <t:{end_unix}:R> (<t:{end_unix}:F>)"
        embed.description = desc
        embed.set_footer(text="Chúc các bạn may mắn!")

        # Gửi tin nhắn chứa Persistent View
        view = PersistentGiveawayView()
        gw_msg = await self.target_channel.send(embed=embed, view=view)

        # Lưu ngay vào SQLite
        Database.add_giveaway(
            msg_id=gw_msg.id,
            ch_id=self.target_channel.id,
            guild_id=self.target_channel.guild.id,
            host_id=interaction.user.id,
            prize=self.prize_input.value.strip(),
            winners=winners,
            end_time=end_time,
            claim_to=claim_seconds,
            roles=[r.id for r in self.roles],
            reason=reason,
            on_fail=self.on_failure,
            hide_host=self.hide_host
        )

        try:
            await self.setup_msg.delete()
        except discord.DiscordException:
            pass

        await interaction.response.send_message(f"✅ Đã tạo Giveaway thành công tại {self.target_channel.mention}!", ephemeral=True)


class GiveawaySetupView(discord.ui.View):
    def __init__(self, author: discord.Member, default_channel: discord.TextChannel):
        super().__init__(timeout=300)
        self.author = author
        self.selected_channel = default_channel
        self.selected_roles = []
        self.on_failure = "reroll"
        self.hide_host = False
        vi = is_vietnamese(default_channel.guild)
        self.channel_select.placeholder = "📢 Chọn kênh đăng giveaway" if vi else "📢 Select giveaway channel"
        self.role_select.placeholder = "🛡️ Role tham gia (Để trống nếu cho All)" if vi else "🛡️ Required role (Leave empty for All)"
        self.toggle_host_btn.label = "Ẩn người tạo: ❌ TẮT" if vi else "Hide Host: ❌ OFF"
        self.open_modal_btn.label = "Tiếp tục: Điền thông tin 📝" if vi else "Continue: Fill Details 📝" 

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id != self.author.id:
            await interaction.response.send_message("❌ Bạn không có quyền thao tác trên bảng này!", ephemeral=True)
            return False
        return True

    @discord.ui.select(cls=discord.ui.ChannelSelect, channel_types=[discord.ChannelType.text], placeholder="📢 Chọn kênh đăng giveaway", row=0)
    async def channel_select(self, interaction: discord.Interaction, select: discord.ui.ChannelSelect):
        self.selected_channel = interaction.guild.get_channel(select.values[0].id)
        await interaction.response.send_message(f"📌 Kênh đăng: {self.selected_channel.mention}", ephemeral=True)

    @discord.ui.select(cls=discord.ui.RoleSelect, placeholder="🛡️ Role tham gia (Để trống nếu cho All)", min_values=0, max_values=10, row=1)
    async def role_select(self, interaction: discord.Interaction, select: discord.ui.RoleSelect):
        self.selected_roles = list(select.values)
        txt = ", ".join(r.mention for r in self.selected_roles) if self.selected_roles else "Tất cả (All)"
        await interaction.response.send_message(f"🛡️ Role yêu cầu: {txt}", ephemeral=True)

    @discord.ui.select(
        placeholder="⚙️ Khi từ chối hoặc hết giờ nhận quà:",
        options=[
            discord.SelectOption(label="Tự quay người khác (Reroll)", value="reroll", default=True),
            discord.SelectOption(label="Kết thúc / Hủy giải (End)", value="end"),
        ],
        row=2
    )
    async def failure_select(self, interaction: discord.Interaction, select: discord.ui.Select):
        self.on_failure = select.values[0]
        txt = "Quay người khác (Reroll)" if self.on_failure == "reroll" else "Kết thúc (End)"
        await interaction.response.send_message(f"⚙️ Chế độ xử lý: **{txt}**", ephemeral=True)

    @discord.ui.button(label="Ẩn người tạo: ❌ TẮT", style=discord.ButtonStyle.secondary, row=3)
    async def toggle_host_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.hide_host = not self.hide_host
        button.label = "Ẩn người tạo: ✅ BẬT" if self.hide_host else "Ẩn người tạo: ❌ TẮT"
        button.style = discord.ButtonStyle.primary if self.hide_host else discord.ButtonStyle.secondary
        await interaction.response.edit_message(view=self)

    @discord.ui.button(label="Tiếp tục: Điền thông tin 📝", style=discord.ButtonStyle.success, row=3)
    async def open_modal_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(
            GiveawayInfoModal(self.selected_channel, self.selected_roles, self.on_failure, self.hide_host, interaction.message)
        )


# ==========================================
# 5. COG ĐIỀU HÀNH CHÍNH & VÒNG LẶP NỀN
# ==========================================
class GiveawayCog(commands.Cog, name="Giveaway"):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        Database.init()
        # Đăng ký View vĩnh viễn vào hệ thống bot khi khởi động
        self.bot.add_view(PersistentGiveawayView())
        self.check_giveaways.start()

    def cog_unload(self):
        self.check_giveaways.cancel()

    # Vòng lặp kiểm tra CSDL mỗi 5 giây
    @tasks.loop(seconds=5)
    async def check_giveaways(self):
        expired_list = Database.get_expired_giveaways()
        for gw in expired_list:
            # Đổi trạng thái sang processing để không bị quét lặp lại
            Database.set_status(gw["message_id"], "processing")
            asyncio.create_task(self.finalize_giveaway(gw))

    @check_giveaways.before_loop
    async def before_check(self):
        await self.bot.wait_until_ready()

    async def finalize_giveaway(self, gw: sqlite3.Row):
        channel = self.bot.get_channel(gw["channel_id"])
        if not channel:
            Database.set_status(gw["message_id"], "ended")
            return

        try:
            msg = await channel.fetch_message(gw["message_id"])
        except (discord.NotFound, discord.Forbidden):
            Database.set_status(gw["message_id"], "ended")
            return

        # Khóa nút tham gia
        view = PersistentGiveawayView()
        for child in view.children:
            child.disabled = True
        try:
            await msg.edit(view=view)
        except discord.HTTPException:
            pass

        participant_ids = Database.get_participants(gw["message_id"])
        guild = channel.guild
        pool = [guild.get_member(uid) for uid in participant_ids if guild.get_member(uid)]

        host_member = guild.get_member(gw["host_id"]) or await self.bot.fetch_user(gw["host_id"])
        host_text = "Ẩn danh 🎭" if gw["hide_host"] else f"<@{gw['host_id']}>"
        prize = gw["prize"]
        is_gacha = any(kw in prize.lower() for kw in GACHA_KEYWORDS)

        if not pool:
            Database.set_status(gw["message_id"], "ended")
            ended_embed = discord.Embed(
                title=f"🎉 GIVEAWAY KẾT THÚC: {prize}",
                description=f"Không có ai tham gia giveaway này.\n👑 **Người tổ chức:** {host_text}",
                color=discord.Color.red()
            )
            await msg.edit(embed=ended_embed, view=view)
            await channel.send(f"⚠️ Giveaway **{prize}** kết thúc mà không có ai tham gia.")
            return

        ended_embed = discord.Embed(
            title=f"🎉 GIVEAWAY KẾT THÚC: {prize}",
            description=f"Đang tiến hành gửi yêu cầu xác nhận cho người trúng giải!\n👑 **Người tổ chức:** {host_text}",
            color=discord.Color.blue()
        )
        await msg.edit(embed=ended_embed, view=view)

        confirmed_winners = []
        available_pool = pool.copy()

        for _ in range(1, gw["winners_count"] + 1):
            slot_awarded = False
            while available_pool and not slot_awarded:
                candidate = random.choice(available_pool)
                available_pool.remove(candidate)

                res = await handle_winner_claim_slot(
                    channel=channel,
                    winner=candidate,
                    prize=prize,
                    claim_seconds=gw["claim_timeout"],
                    host_text=host_text,
                    host=host_member,
                    is_gacha=is_gacha
                )

                if res == "claimed":
                    confirmed_winners.append(candidate)
                    slot_awarded = True
                else:
                    if gw["on_failure"] == "reroll":
                        await channel.send(f"🔄 Đang tự động quay người khác thay thế cho {candidate.mention}...")
                        await asyncio.sleep(2)
                    else:
                        await channel.send(f"🚫 Giải thưởng này đã bị hủy bỏ theo cài đặt của người tổ chức.")
                        break

        Database.set_status(gw["message_id"], "ended")

        if confirmed_winners:
            win_str = ", ".join(m.mention for m in confirmed_winners)
            final_embed = discord.Embed(
                title=f"🏆 TỔNG KẾT GIVEAWAY: {prize}",
                description=(
                    f"🎉 **Người trúng giải chính thức:** {win_str}\n"
                    f"👑 **Người tổ chức:** {host_text}\n"
                    f"👥 **Tổng người tham gia:** `{len(pool)}`"
                ),
                color=discord.Color.green()
            )
            await channel.send(embed=final_embed)
        else:
            await channel.send(f"⚠️ Giveaway **{prize}** đã kết thúc nhưng không có ai nhận thưởng.")

    @commands.command(name="giveaway", aliases=["gstart"])
    @commands.has_permissions(manage_messages=True)
    async def giveaway_command(self, ctx: commands.Context):
        embed = discord.Embed(
            title="⚙️ Bảng Thiết Lập Giveaway",
            description="Tùy chỉnh thông số kênh, role, ẩn danh bên dưới rồi bấm **Tiếp tục** để mở bảng nhập quà.",
            color=discord.Color.blurple()
        )
        view = GiveawaySetupView(author=ctx.author, default_channel=ctx.channel)
        await ctx.send(embed=embed, view=view)


async def setup(bot: commands.Bot):
    await bot.add_cog(GiveawayCog(bot))
