from Checks_vi.i18n import t, is_vietnamese
import discord
from discord.ext import commands
from discord import app_commands
import os
import json
import time
import aiohttp
import asyncio
from typing import Optional, Union

VOTE_FILE = "data/votes.json"
BOT_ID = "1504825128499019807"
TOPGG_VOTE_URL = f"https://top.gg/bot/{BOT_ID}/vote"
VOTE_DURATION = 43200  # 12 giờ (43,200 giây) theo chu kỳ Top.gg

# Danh sách các lệnh cao cấp yêu cầu Vote Top.gg để mở khóa
VOTE_LOCKED_COMMANDS = [
    {"name": "/music volume (hoặc nút Vol - / Vol +)", "desc": "Tăng / giảm âm lượng phát nhạc bot trong Voice", "icon": "🔊"},
    {"name": "/math (hoặc s!math, s!calc)", "desc": "Máy tính thông minh giải biểu thức, hàm toán học & phần trăm", "icon": "🧮"},
    {"name": "/translate (hoặc s!translate, s!t)", "desc": "Dịch thuật đa ngôn ngữ thông minh sang tiếng Việt bằng AI", "icon": "🌐"},
    {"name": "/xemboi", "desc": "Xin quẻ & nhờ AI giải mã tương lai", "icon": "🔮"},
]

os.makedirs(os.path.dirname(VOTE_FILE), exist_ok=True)

def load_vote_data() -> dict:
    if os.path.exists(VOTE_FILE):
        try:
            with open(VOTE_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {}
    return {}

def save_vote_data(data: dict):
    try:
        with open(VOTE_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4, ensure_ascii=False)
    except Exception:
        pass

def is_bot_owner(user_id: Union[int, str]) -> bool:
    try:
        from config import OWNER_ID
        return str(user_id) == str(OWNER_ID)
    except Exception:
        return False

def is_vote_required_enabled() -> bool:
    votes = load_vote_data()
    return votes.get("_config", {}).get("vote_required_enabled", True)

def set_vote_required_enabled(enabled: bool):
    votes = load_vote_data()
    votes.setdefault("_config", {})["vote_required_enabled"] = bool(enabled)
    save_vote_data(votes)

def has_voted(user_id: Union[int, str]) -> bool:
    """Kiểm tra xem người dùng đã bình chọn trên Top.gg trong 12 giờ qua chưa."""
    if not is_vote_required_enabled():
        return True  # Hệ thống vote đang tắt

    uid = str(user_id)
    if is_bot_owner(uid):
        return True  # Owner luôn mở khóa toàn bộ

    votes = load_vote_data()
    if uid in votes:
        last_vote = votes[uid].get("last_vote", 0)
        now = time.time()
        if (now - last_vote) < VOTE_DURATION:
            return True
    return False

def get_vote_status(user_id: Union[int, str]) -> dict:
    """Lấy chi tiết trạng thái vote của người dùng."""
    uid = str(user_id)
    is_owner = is_bot_owner(uid)
    votes = load_vote_data()
    user_info = votes.get(uid, {})
    last_vote = user_info.get("last_vote", 0)
    total_votes = user_info.get("total_votes", 0)
    now = time.time()
    diff = now - last_vote
    system_enabled = is_vote_required_enabled()

    if not system_enabled:
        return {
            "voted": True,
            "system_enabled": False,
            "is_owner": is_owner,
            "remaining_seconds": VOTE_DURATION,
            "remaining_text": "Mở khóa tự do (Hệ thống vote đang TẮT)",
            "total_votes": total_votes,
            "last_vote": last_vote
        }

    if is_owner:
        return {
            "voted": True,
            "system_enabled": True,
            "is_owner": True,
            "remaining_seconds": VOTE_DURATION,
            "remaining_text": "Vĩnh viễn (Chủ sở hữu Bot)",
            "total_votes": total_votes,
            "last_vote": last_vote
        }

    if diff < VOTE_DURATION:
        rem = int(VOTE_DURATION - diff)
        hours = rem // 3600
        mins = (rem % 3600) // 60
        return {
            "voted": True,
            "system_enabled": True,
            "is_owner": False,
            "remaining_seconds": rem,
            "remaining_text": f"{hours} giờ {mins} phút",
            "total_votes": total_votes,
            "last_vote": last_vote
        }
    else:
        return {
            "voted": False,
            "system_enabled": True,
            "is_owner": False,
            "remaining_seconds": 0,
            "remaining_text": "Chưa vote hoặc đã hết hạn 12h",
            "total_votes": total_votes,
            "last_vote": last_vote
        }

def record_vote(user_id: Union[int, str]) -> dict:
    """Ghi nhận lượt vote mới cho user."""
    uid = str(user_id)
    votes = load_vote_data()
    cur = votes.get(uid, {"total_votes": 0, "last_vote": 0})
    cur["total_votes"] = cur.get("total_votes", 0) + 1
    cur["last_vote"] = time.time()
    votes[uid] = cur
    save_vote_data(votes)
    return cur

async def send_vote_success_dm(bot: Optional[commands.Bot] = None, user_id: Union[int, str] = 0) -> bool:
    """Gửi tin nhắn riêng (DM) chúc mừng và thông báo quyền lợi khi người dùng Vote Top.gg thành công.
    Hỗ trợ 2 tầng: Dùng Bot client nếu online; nếu offline/chạy riêng thì gửi bằng Discord REST API qua BOT_TOKEN.
    """
    uid_str = str(user_id).strip()
    if not uid_str:
        return False

    desc_lines = [
        "Xin chào! Sakura Bot vừa nhận được lượt bình chọn của bạn trên **Top.gg**!",
        "Sự ủng hộ quý giá này giúp Sakura Bot ngày càng phát triển và lan tỏa đến nhiều cộng đồng hơn 💖",
        "",
        "🎁 **Phần Thưởng Đã Được Kích Hoạt Tự Động:**",
        "• 🔓 **Mở khóa 12h VIP:** Toàn quyền sử dụng các lệnh (`/music volume`, `/math`, `/translate`, `/xemboi`...)",
        "• 🪙 **+5,000 Coins** đã được cộng vào tài khoản ví",
        "• ⭐ **+500 XP** kinh nghiệm thăng cấp",
        "",
        "⏰ **Lưu ý:** Bạn có thể tiếp tục bình chọn sau mỗi **12 giờ** để tích lũy thêm thật nhiều Coins & XP!",
        "Chúc bạn luôn có những phút giây trải nghiệm tuyệt vời cùng Sakura Bot nhé! ✨"
    ]
    desc_text = "\n".join(desc_lines)

    # 1. Thử gửi qua Bot Client (nếu bot có sẵn)
    if bot:
        try:
            uid = int(uid_str)
            user = bot.get_user(uid)
            if not user:
                try:
                    user = await bot.fetch_user(uid)
                except Exception:
                    user = None
            if user:
                user_lines = [
                    f"Xin chào **{user.name}**! Sakura Bot vừa nhận được lượt bình chọn của bạn trên **Top.gg**!",
                    "Sự ủng hộ quý giá này giúp Sakura Bot ngày càng phát triển và lan tỏa đến nhiều cộng đồng hơn 💖",
                    "",
                    "🎁 **Phần Thưởng Đã Được Kích Hoạt Tự Động:**",
                    "• 🔓 **Mở khóa 12h VIP:** Toàn quyền sử dụng các lệnh (`/music volume`, `/math`, `/translate`, `/xemboi`...)",
                    "• 🪙 **+5,000 Coins** đã được cộng vào tài khoản ví",
                    "• ⭐ **+500 XP** kinh nghiệm thăng cấp",
                    "",
                    "⏰ **Lưu ý:** Bạn có thể tiếp tục bình chọn sau mỗi **12 giờ** để tích lũy thêm thật nhiều Coins & XP!",
                    "Chúc bạn luôn có những phút giây trải nghiệm tuyệt vời cùng Sakura Bot nhé! ✨"
                ]
                embed = discord.Embed(
                    title="🌸 CẢM ƠN BẠN ĐÃ BÌNH CHỌN CHO SAKURA BOT! 🌸",
                    description="\n".join(user_lines),
                    color=discord.Color.from_rgb(255, 121, 198)
                )
                bot_user = getattr(bot, "user", None)
                bot_avatar = bot_user.display_avatar.url if bot_user and bot_user.display_avatar else "https://cdn.discordapp.com/avatars/1504825128499019807/dea9d2725b620317b25b9da8f36d129a?size=256"
                embed.set_thumbnail(url=bot_avatar)
                embed.set_footer(text="Sakura Bot • Top.gg Vote System", icon_url=bot_avatar)

                view = discord.ui.View()
                view.add_item(discord.ui.Button(
                    label="🌐 Web Dashboard",
                    url="https://sakurabot.wispbyte.org",
                    style=discord.ButtonStyle.link,
                    emoji="🌸"
                ))
                view.add_item(discord.ui.Button(
                    label="🗳️ Trang Vote Top.gg",
                    url=TOPGG_VOTE_URL,
                    style=discord.ButtonStyle.link,
                    emoji="✨"
                ))

                await user.send(embed=embed, view=view)
                return True
        except (discord.Forbidden, discord.HTTPException):
            pass
        except Exception as e:
            print(f"Lỗi gửi DM qua Bot client: {e}")

    # 2. Fallback sang Discord REST API trực tiếp bằng Bot Token
    try:
        from config import TOKEN
        token = TOKEN or os.getenv("DISCORD_TOKEN", "")
        if not token:
            return False

        def _send_rest_dm():
            import urllib.request
            import json
            headers = {
                "Authorization": f"Bot {token}",
                "Content-Type": "application/json",
                "User-Agent": "DiscordBot (https://sakurabot.top, 1.0)"
            }
            # Mở DM channel
            ch_req = urllib.request.Request(
                "https://discord.com/api/v10/users/@me/channels",
                data=json.dumps({"recipient_id": uid_str}).encode("utf-8"),
                headers=headers
            )
            with urllib.request.urlopen(ch_req, timeout=10) as resp:
                ch_data = json.loads(resp.read().decode())
                channel_id = ch_data.get("id")

            if not channel_id:
                return False

            payload = {
                "embeds": [{
                    "title": "🌸 CẢM ƠN BẠN ĐÃ BÌNH CHỌN CHO SAKURA BOT! 🌸",
                    "description": desc_text,
                    "color": 0xff79c6,
                    "thumbnail": {"url": "https://cdn.discordapp.com/avatars/1504825128499019807/dea9d2725b620317b25b9da8f36d129a?size=256"},
                    "footer": {
                        "text": "Sakura Bot • Top.gg Vote System",
                        "icon_url": "https://cdn.discordapp.com/avatars/1504825128499019807/dea9d2725b620317b25b9da8f36d129a?size=256"
                    }
                }],
                "components": [{
                    "type": 1,
                    "components": [
                        {"type": 2, "style": 5, "label": "🌐 Web Dashboard", "url": "https://sakurabot.wispbyte.org"},
                        {"type": 2, "style": 5, "label": "🗳️ Trang Vote Top.gg", "url": TOPGG_VOTE_URL}
                    ]
                }]
            }
            msg_req = urllib.request.Request(
                f"https://discord.com/api/v10/channels/{channel_id}/messages",
                data=json.dumps(payload).encode("utf-8"),
                headers=headers
            )
            with urllib.request.urlopen(msg_req, timeout=10) as resp:
                return resp.status in (200, 201)

        return await asyncio.to_thread(_send_rest_dm)
    except Exception as e:
        print(f"Lỗi gửi DM qua REST API cho {uid_str}: {e}")
        return False

async def check_topgg_api(user_id: Union[int, str], bot: Optional[commands.Bot] = None) -> dict:
    """Truy vấn trực tiếp REST API của Top.gg để kiểm tra xem user_id đã vote bot chưa.
    Endpoint: GET https://top.gg/api/bots/{BOT_ID}/check?userId={user_id}
    Headers: Authorization: {TOPGG_TOKEN}
    """
    token = ""
    try:
        from config import TOPGG_TOKEN
        token = TOPGG_TOKEN or os.getenv("TOPGG_TOKEN", "")
    except Exception:
        token = os.getenv("TOPGG_TOKEN", "")

    if not token:
        return {"ok": False, "reason": "Chưa cấu hình TOPGG_TOKEN trong file config.py"}

    uid = str(user_id)
    url = f"https://top.gg/api/bots/{BOT_ID}/check?userId={uid}"
    headers = {"Authorization": token}

    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=headers, timeout=10) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    has_voted_api = data.get("voted") == 1
                    if has_voted_api:
                        votes = load_vote_data()
                        cur_vote = votes.get(uid, {})
                        last_vote_time = cur_vote.get("last_vote", 0) if isinstance(cur_vote, dict) else 0
                        now = time.time()

                        if (now - last_vote_time) >= VOTE_DURATION:
                            record_vote(uid)
                            try:
                                from data.database import update_user_level_stats, get_user_data
                                user_data = await get_user_data(0, int(uid))
                                cur_coins = user_data.get("coins", 0) if isinstance(user_data, dict) else 0
                                cur_xp = user_data.get("xp", 0) if isinstance(user_data, dict) else 0
                                cur_level = user_data.get("level", 1) if isinstance(user_data, dict) else 1
                                await update_user_level_stats(uid, None, cur_level, cur_xp + 500, cur_coins + 5000)
                            except Exception:
                                pass

                            await send_vote_success_dm(bot, uid)
                            return {"ok": True, "voted": True, "newly_rewarded": True}
                        return {"ok": True, "voted": True, "newly_rewarded": False}
                    else:
                        return {"ok": True, "voted": False}
                elif resp.status == 401:
                    return {"ok": False, "reason": "TOPGG_TOKEN không hợp lệ hoặc đã hết hạn (401 Unauthorized)"}
                elif resp.status == 404:
                    return {"ok": False, "reason": f"Không tìm thấy bot {BOT_ID} trên Top.gg"}
                else:
                    return {"ok": False, "reason": f"Top.gg API trả về HTTP {resp.status}"}
    except Exception as e:
        return {"ok": False, "reason": f"Không thể kết nối API Top.gg: {str(e)}"}


class VoteRequiredView(discord.ui.View):
    """View hiển thị nút Vote Top.gg và Nút kiểm tra lại vote."""
    def __init__(self, user_id: int, guild: Optional[discord.Guild] = None):
        super().__init__(timeout=180)
        self.user_id = user_id
        self.guild = guild
        vi = is_vietnamese(guild) if guild else True
        vote_label = "🗳️ Bình Chọn Trên Top.gg" if vi else "🗳️ Vote on Top.gg"
        self.add_item(discord.ui.Button(
            label=vote_label,
            url=TOPGG_VOTE_URL,
            style=discord.ButtonStyle.link
        ))

    @discord.ui.button(label="🔄 Kiểm Tra Lại Vote", style=discord.ButtonStyle.primary, emoji="✨")
    async def btn_check_vote(self, interaction: discord.Interaction, button: discord.ui.Button):
        guild = interaction.guild
        if interaction.user.id != self.user_id:
            return await interaction.response.send_message("⚠️ Nút này chỉ dành cho người thực hiện lệnh!", ephemeral=True)

        await interaction.response.defer(ephemeral=True)
        client_bot = getattr(interaction, "client", None)
        api_res = await check_topgg_api(self.user_id, bot=client_bot)
        status = get_vote_status(self.user_id)

        if api_res.get("newly_rewarded"):
            embed = discord.Embed(
                title="🎉 XÁC NHẬN BÌNH CHỌN THÀNH CÔNG!",
                description=(
                    f"Cảm ơn bạn {interaction.user.mention} đã bình chọn cho Sakura Bot trên **Top.gg**! 💖\n\n"
                    f"🎁 **Phần thưởng đã kích hoạt:**\n"
                    f"• 🔓 **Mở khóa 12h:** VIP & toàn bộ lệnh yêu cầu vote\n"
                    f"• 🪙 **+5,000 Coins** vào tài khoản ví\n"
                    f"• ⭐ **+500 XP** kinh nghiệm thăng cấp\n"
                    f"• 📬 Đã gửi thư cảm ơn chi tiết qua tin nhắn riêng (DM)!"
                ),
                color=discord.Color.green()
            )
            return await interaction.followup.send(embed=embed, ephemeral=True)

        if status["voted"]:
            embed = discord.Embed(
                title="🎉 Bạn Đã Mở Khóa Tính Năng!",
                description=(
                    f"✅ Hệ thống ghi nhận bạn đã mở khóa quyền lợi bình chọn!\n\n"
                    f"⏱️ **Thời gian còn lại:** `{status['remaining_text']}`\n"
                    f"🎁 **Đặc quyền:** Tất cả lệnh VIP và giới hạn đã được mở khóa toàn bộ.\n"
                    f"👉 *Bây giờ bạn có thể gõ lại lệnh để sử dụng bình thường!*"
                ),
                color=discord.Color.green()
            )
            return await interaction.followup.send(embed=embed, ephemeral=True)

        reason = api_res.get("reason", "")
        embed = discord.Embed(
            title="⏳ Chưa Ghi Nhận Lượt Vote Mới",
            description=(
                f"Hệ thống Top.gg chưa tìm thấy lượt vote hợp lệ của bạn trong 12 giờ qua.\n\n"
                f"1. Nhấn nút **[🗳️ Bình Chọn Trên Top.gg]({TOPGG_VOTE_URL})** bên trên.\n"
                f"2. Bấm nút **Vote** trên trang Top.gg và chờ 5-10 giây để Top.gg cập nhật.\n"
                f"3. Quay lại đây và nhấn **[🔄 Kiểm Tra Lại Vote]** một lần nữa!\n\n"
                + (f"*(Chi tiết API: {reason})*\n\n" if reason else "")
                + f"*(Mỗi lượt vote mở khóa 12h sử dụng toàn bộ tính năng và tặng ngay 5,000 Coin!)*"
            ),
            color=discord.Color.orange()
        )
        await interaction.followup.send(embed=embed, ephemeral=True)


async def require_vote_or_notify(interaction_or_ctx, command_name: Optional[str] = None) -> bool:
    """Hàm kiểm tra quyền Vote trước khi thực thi lệnh.
    Nếu chưa vote: thử truy vấn Top.gg API trước để auto-unlock nếu user vừa vote xong.
    Nếu vẫn chưa vote: gửi Embed thông báo bắt mắt + nút vote và trả về False.
    """
    is_interaction = isinstance(interaction_or_ctx, discord.Interaction)
    user = interaction_or_ctx.user if is_interaction else interaction_or_ctx.author
    bot = getattr(interaction_or_ctx, "client", None) if is_interaction else getattr(interaction_or_ctx, "bot", None)

    if has_voted(user.id):
        return True

    # Thử check nhanh Top.gg API phòng trường hợp webhook chưa tới
    try:
        api_res = await check_topgg_api(user.id, bot=bot)
        if api_res.get("voted") or api_res.get("newly_rewarded"):
            return True
    except Exception:
        pass

    cmd_label = command_name or "Lệnh này"
    guild = interaction_or_ctx.guild
    embed = discord.Embed(
        title="🔒 TÍNH NĂNG NÀY YÊU CẦU MỞ KHÓA BẰNG VOTE TRÊN TOP.GG",
        description=(
            f"Chào {user.mention}! Tính năng **{cmd_label}** là một trong các tính năng đặc quyền cao cấp (VIP) của **Sakura Bot**.\n\n"
            f"Để mở khóa tính năng này hoàn toàn **MIỄN PHÍ** trong vòng **12 Giờ**, bạn chỉ cần bình chọn (Vote) cho bot trên Top.gg!\n\n"
            f"🎁 **Phần Thưởng Kèm Theo Khi Vote:**\n"
            f"• 🔓 Mở khóa toàn bộ các lệnh giới hạn trong **12 Giờ**\n"
            f"• 🪙 **+5,000 Coins** vào tài khoản ví\n"
            f"• ⭐ **+500 XP** kinh nghiệm thăng cấp\n\n"
            f"👉 Nhấn vào nút **[Bình Chọn Trên Top.gg]({TOPGG_VOTE_URL})** bên dưới để mở khóa ngay!"
        ),
        color=discord.Color.from_rgb(255, 121, 198)
    )
    embed.add_field(
        name="📜 Danh Sách Tính Năng Yêu Cầu Vote",
        value="\n".join([f"• **{c['icon']} `{c['name']}`**: {c['desc']}" for c in VOTE_LOCKED_COMMANDS]),
        inline=False
    )
    embed.set_footer(text="Cảm ơn bạn đã luôn ủng hộ và đồng hành cùng Sakura Bot 💖")
    embed.set_thumbnail(url="https://cdn.discordapp.com/avatars/1504825128499019807/dea9d2725b620317b25b9da8f36d129a?size=256")

    view = VoteRequiredView(user.id, guild=guild)

    if is_interaction:
        if interaction_or_ctx.response.is_done():
            await interaction_or_ctx.followup.send(embed=embed, view=view, ephemeral=True)
        else:
            await interaction_or_ctx.response.send_message(embed=embed, view=view, ephemeral=True)
    else:
        await interaction_or_ctx.send(embed=embed, view=view)

    return False


class VoteCog(commands.Cog, name="Vote"):
    """Cog quản lý hệ thống bình chọn Top.gg và mở khóa tính năng VIP."""

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.hybrid_group(
        name="vote",
        description="🗳️ Hệ thống bình chọn Top.gg để nhận quà và mở khóa các tính năng VIP của Bot."
    )
    async def vote_group(self, ctx: commands.Context):
        if ctx.invoked_subcommand is None:
            await self._show_vote_menu(ctx)

    async def _show_vote_menu(self, ctx: commands.Context):
        user_id = ctx.author.id

        # Tự động đồng bộ và kiểm tra từ Top.gg REST API
        newly_rewarded = False
        try:
            api_res = await check_topgg_api(user_id, bot=self.bot)
            if api_res.get("newly_rewarded"):
                newly_rewarded = True
        except Exception:
            pass

        status = get_vote_status(user_id)

        if status.get("is_owner"):
            status_text = "👑 **QUYỀN CHỦ BOT:** `ĐƯỢC BYPASS` (Luôn mở khóa vĩnh viễn)"
            color = discord.Color.gold()
        elif status["voted"]:
            status_text = f"🟢 **ĐÃ MỞ KHÓA** (Còn `{status['remaining_text']}`)"
            color = discord.Color.green()
        else:
            status_text = "🔴 **CHƯA MỞ KHÓA** (Cần vote để kích hoạt 12h)"
            color = discord.Color.from_rgb(255, 121, 198)

        extra_notice = ""
        if newly_rewarded:
            extra_notice = "🎉 **Chúc mừng!** Sakura Bot đã xác nhận lượt vote mới của bạn trên Top.gg! (+5,000 Coins, +500 XP, mở khóa 12h VIP, đã gửi DM thư cảm ơn)!\n\n"

        embed = discord.Embed(
            title="🗳️ BÌNH CHỌN CHO SAKURA BOT TRÊN TOP.GG",
            description=(
                extra_notice +
                f"Bình chọn cho Sakura Bot trên danh sách danh tiếng **Top.gg** giúp bot phát triển và lan tỏa đến nhiều cộng đồng hơn!\n\n"
                f"👤 **Trạng thái của bạn:** {status_text}\n"
                f"🏆 **Tổng số lượt đã vote:** `{status['total_votes']} lần`\n\n"
                f"🎁 **Phần Thưởng Mỗi Lượt Vote:**\n"
                f"• 🔓 **Mở khóa 12h** tất cả tính năng VIP và giới hạn lệnh\n"
                f"• 🪙 **+5,000 Coins** vào tài khoản ví\n"
                f"• ⭐ **+500 XP** kinh nghiệm thăng cấp"
            ),
            color=color
        )

        embed.add_field(
            name="🔒 Các Lệnh Cần Vote Để Mở Khóa",
            value="\n".join([f"• **{c['icon']} `{c['name']}`**: {c['desc']}" for c in VOTE_LOCKED_COMMANDS]),
            inline=False
        )

        embed.set_thumbnail(url="https://cdn.discordapp.com/avatars/1504825128499019807/dea9d2725b620317b25b9da8f36d129a?size=256")
        embed.set_footer(text=f"Yêu cầu bởi {ctx.author.display_name} • Mỗi 12 giờ vote được 1 lần", icon_url=ctx.author.display_avatar.url)

        view = VoteRequiredView(ctx.author.id, guild=ctx.guild)
        if ctx.interaction:
            await ctx.send(embed=embed, view=view, ephemeral=True)
        else:
            await ctx.send(embed=embed, view=view)

    @vote_group.command(name="check", description="🔄 Kiểm tra lại trạng thái bình chọn từ Top.gg và nhận thưởng ngay.")
    async def vote_check(self, ctx: commands.Context):
        user_id = ctx.author.id
        guild = ctx.guild
        api_res = await check_topgg_api(user_id, bot=self.bot)
        status = get_vote_status(user_id)

        if api_res.get("newly_rewarded"):
            embed = discord.Embed(
                title="🎉 XÁC NHẬN BÌNH CHỌN THÀNH CÔNG!",
                description=(
                    f"Cảm ơn bạn {ctx.author.mention} đã bình chọn cho Sakura Bot trên **Top.gg**! 💖\n\n"
                    f"🎁 **Phần thưởng đã kích hoạt:**\n"
                    f"• 🔓 **Mở khóa 12h:** VIP & toàn bộ lệnh yêu cầu vote\n"
                    f"• 🪙 **+5,000 Coins** vào tài khoản ví\n"
                    f"• ⭐ **+500 XP** kinh nghiệm thăng cấp\n"
                    f"• 📬 Đã gửi thư cảm ơn chi tiết qua tin nhắn riêng (DM)!"
                ),
                color=discord.Color.green()
            )
            embed.set_footer(text="Mỗi 12 giờ bạn có thể vote lại 1 lần để nhận thưởng tiếp!")
            return await ctx.send(embed=embed)

        if status["voted"]:
            embed = discord.Embed(
                title="✅ Trạng Thái Vote Đang Hoạt Động",
                description=(
                    f"Xin chào {ctx.author.mention}!\n\n"
                    f"⏱️ **Thời gian còn lại:** `{status['remaining_text']}`\n"
                    f"🏆 **Tổng lượt vote của bạn:** `{status['total_votes']} lần`\n\n"
                    f"Bạn đang có toàn quyền sử dụng tất cả tính năng của Sakura Bot!"
                ),
                color=discord.Color.green()
            )
            view = VoteRequiredView(user_id, guild=guild)
            return await ctx.send(embed=embed, view=view)

        reason = api_res.get("reason", "")
        embed = discord.Embed(
            title="⏳ Chưa Ghi Nhận Lượt Vote Mới",
            description=(
                f"Hệ thống Top.gg chưa tìm thấy lượt vote mới của {ctx.author.mention} trong 12 giờ qua.\n\n"
                f"👉 Hãy bấm vào nút **[Bình Chọn Trên Top.gg]({TOPGG_VOTE_URL})** bên dưới để vote, sau đó bấm **Kiểm Tra Lại Vote** nhé!\n"
                + (f"*(Chi tiết API: {reason})*\n" if reason else "")
            ),
            color=discord.Color.orange()
        )
        view = VoteRequiredView(user_id, guild=guild)
        await ctx.send(embed=embed, view=view)

    @vote_group.command(name="test_dm", description="🧪 Thử nghiệm gửi DM thông báo vote thành công (Chỉ Owner).")
    async def vote_test_dm(self, ctx: commands.Context, user: Optional[discord.User] = None):
        if not is_bot_owner(ctx.author.id):
            return await ctx.send("❌ Chỉ **Chủ Bot** mới có quyền chạy lệnh kiểm tra này!", ephemeral=True)

        target = user or ctx.author
        ok = await send_vote_success_dm(self.bot, target.id)
        if ok:
            await ctx.send(f"✅ Đã gửi thành công tin nhắn DM thông báo Vote cho **{target.mention}**!", ephemeral=True)
        else:
            await ctx.send(f"⚠️ Không thể gửi DM cho **{target.mention}**. Người dùng có thể đã tắt tin nhắn trực tiếp từ thành viên máy chủ hoặc đã chặn bot.", ephemeral=True)

    @vote_group.command(name="rewards", description="🎁 Xem danh sách các lệnh và phần thưởng khi bình chọn.")
    async def vote_rewards(self, ctx: commands.Context):
        embed = discord.Embed(
            title="🎁 ĐẶC QUYỀN & LỆNH MỞ KHÓA KHI VOTE TOP.GG",
            description=(
                "Mỗi lượt bình chọn trên Top.gg (12 giờ một lần) sẽ mở khóa toàn bộ quyền lợi sau:\n\n"
                "**1. Kinh Tế & Cấp Độ:**\n"
                "• 🪙 **+5,000 Coins** ví tiền tệ\n"
                "• ⭐ **+500 XP** cấp độ tài khoản\n\n"
                "**2. Mở Khóa Các Lệnh Cao Cấp:**\n" +
                "\n".join([f"• `{c['name']}`: {c['desc']}" for c in VOTE_LOCKED_COMMANDS])
            ),
            color=discord.Color.from_rgb(255, 121, 198)
        )
        view = VoteRequiredView(ctx.author.id, guild=ctx.guild)
        await ctx.send(embed=embed, view=view, ephemeral=True)


async def setup(bot: commands.Bot):
    await bot.add_cog(VoteCog(bot))
