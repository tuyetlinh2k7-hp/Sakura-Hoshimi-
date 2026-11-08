import asyncio
from datetime import datetime, timedelta, timezone
import os
import time
import aiohttp
import aiosqlite
import discord
from discord import app_commands
from discord.ext import commands, tasks

# ==============================================================================
# CẤU HÌNH & DỮ LIỆU
# ==============================================================================
DATA_DIR = "gacha_data"
os.makedirs(DATA_DIR, exist_ok=True)
DB_PATH = os.path.join(DATA_DIR, "database.sqlite")

REPORT_THRESHOLD = 3
CHECK_INTERVAL_SECONDS = 300  # 5 phút/lần
REMIND_BEFORE_SECONDS = 7200  # Nhắc nhở khi code còn dưới 2 tiếng (7200 giây)
VN_TZ = timezone(timedelta(hours=7))  # Múi giờ Việt Nam (UTC+7)

# Bạn có thể tạo 1 file JSON trên GitHub Gist chứa code của NTE và Endfield rồi dán link Raw vào đây
CUSTOM_CODES_GIST_URL = None 

GAMES = {
    "genshin": {
        "name": "Genshin Impact",
        "publisher": "hoyoverse",
        "api_param": "genshin",
        "color": 0x4B69FF,
        "redeem_method": "web",
        "redeem_url": "https://genshin.hoyoverse.com/en/gift?code=",
        "youtube_url": "https://www.youtube.com/@GenshinImpact",
        "twitch_url": "https://www.twitch.tv/genshinimpactofficial"
    },
    "hsr": {
        "name": "Honkai: Star Rail",
        "publisher": "hoyoverse",
        "api_param": "hkrpg",
        "color": 0xDE86FF,
        "redeem_method": "web",
        "redeem_url": "https://hsr.hoyoverse.com/gift?code=",
        "youtube_url": "https://www.youtube.com/@HonkaiStarRail",
        "twitch_url": "https://www.twitch.tv/honkaistarrail"
    },
    "zzz": {
        "name": "Zenless Zone Zero",
        "publisher": "hoyoverse",
        "api_param": "nap",
        "color": 0xFFDF00,
        "redeem_method": "web",
        "redeem_url": "https://zenless.hoyoverse.com/redemption?code=",
        "youtube_url": "https://www.youtube.com/@ZZZ_Official",
        "twitch_url": "https://www.twitch.tv/zenlesszonezero"
    },
    "nte": {
        "name": "Neverness to Everness",
        "publisher": "hotta",
        "color": 0x00F0FF,
        "redeem_method": "in_game",
        "guide": "Vào game ➔ Menu (...) ➔ Cài đặt ➔ Đổi mã (Redeem Code)"
    },
    "endfield": {
        "name": "Arknights: Endfield",
        "publisher": "hypergryph",
        "color": 0xFF5722,
        "redeem_method": "in_game",
        "guide": "Vào game ➔ Cài đặt ➔ Tài khoản & Nền tảng ➔ Đổi mã (Exchange Code)"
    }
}

# ==============================================================================
# HÀM BỔ TRỢ (DATABASE & API)
# ==============================================================================
async def init_db():
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
            CREATE TABLE IF NOT EXISTS guild_config (
                guild_id TEXT, game_key TEXT, channel_id INTEGER, 
                role_id INTEGER, webhook_url TEXT,
                PRIMARY KEY (guild_id, game_key)
            )
        """)
        await db.execute("""
            CREATE TABLE IF NOT EXISTS sent_codes (
                game_key TEXT, code TEXT, 
                PRIMARY KEY (game_key, code)
            )
        """)
        await db.execute("""
            CREATE TABLE IF NOT EXISTS tracked_messages (
                message_id TEXT PRIMARY KEY, channel_id INTEGER, guild_id TEXT, 
                game_key TEXT, code TEXT, rewards TEXT, expires_at REAL, 
                is_manual INTEGER, is_test INTEGER, reminded INTEGER
            )
        """)
        await db.execute("""
            CREATE TABLE IF NOT EXISTS reports (
                message_id TEXT, user_id TEXT, 
                PRIMARY KEY (message_id, user_id)
            )
        """)
        await db.commit()

async def fetch_game_codes(session: aiohttp.ClientSession, game_key: str) -> list:
    game_info = GAMES.get(game_key)
    if not game_info:
        return []

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36",
        "Accept": "application/json, text/plain, */*",
    }

    if game_info.get("publisher") == "hoyoverse":
        url = f"https://hoyo-codes.seria.moe/codes?game={game_info['api_param']}"
        try:
            async with session.get(url, headers=headers, timeout=aiohttp.ClientTimeout(total=12)) as resp:
                if resp.status == 200:
                    try:
                        data = await resp.json(content_type=None)
                    except Exception:
                        text = await resp.text()
                        data = json.loads(text) if text and text.strip() else None

                    if isinstance(data, list):
                        return [c for c in data if isinstance(c, dict)]
                    elif isinstance(data, dict):
                        codes = data.get("codes", [])
                        if isinstance(codes, list):
                            return [c for c in codes if isinstance(c, dict)]
                        return []
                    return []
                else:
                    print(f"[GachaCog API Warning] Không thể tải code {game_key}: HTTP {resp.status}")
        except Exception as e:
            print(f"[GachaCog API Error] Không thể tải code {game_key}: {e}")
        return []

    if CUSTOM_CODES_GIST_URL:
        try:
            async with session.get(CUSTOM_CODES_GIST_URL, headers=headers, timeout=aiohttp.ClientTimeout(total=10)) as resp:
                if resp.status == 200:
                    custom_data = await resp.json(content_type=None)
                    if isinstance(custom_data, dict):
                        res = custom_data.get(game_key, [])
                        return [c for c in res if isinstance(c, dict)] if isinstance(res, list) else []
                    elif isinstance(custom_data, list):
                        return [c for c in custom_data if isinstance(c, dict)]
        except Exception as e:
            print(f"[GachaCog Custom API Error] {game_key}: {e}")

    mock_codes = {
        "nte": [{"code": "NTEGIFT", "rewards": "50 Annulith", "expires_at": None}],
        "endfield": [{"code": "ENDFIELDGIFT", "rewards": "150 Oroberyl", "expires_at": None}]
    }
    return mock_codes.get(game_key, [])

# ==============================================================================
# TẠO EMBED GIAO DIỆN
# ==============================================================================
def create_code_embed(game_key: str, code_data: dict, is_expired: bool = False, expired_reason: str = None, is_test: bool = False) -> discord.Embed:
    game_info = GAMES[game_key]
    code = code_data.get("code", "UNKNOWN")
    rewards = code_data.get("rewards") or code_data.get("description") or "Phần thưởng trong game"
    if isinstance(rewards, list):
        rewards = ", ".join(rewards)

    expires_at = code_data.get("expires_at")

    if is_expired:
        reason_text = f" ({expired_reason})" if expired_reason else ""
        embed = discord.Embed(title=f"❌ [HẾT HẠN] {game_info['name']}", color=0x7F8C8D)
        embed.add_field(name="Mã Quà Tặng", value=f"~~`{code}`~~", inline=False)
        embed.add_field(name="Phần Thưởng", value=rewards, inline=False)
        embed.add_field(name="Trạng Thái", value=f"🔴 **ĐÃ HẾT HẠN{reason_text}**", inline=False)
    else:
        title_prefix = "🧪 [TEST] " if is_test else "🎁 "
        embed = discord.Embed(title=f"{title_prefix}Mã Code Mới: {game_info['name']}", color=game_info["color"])
        embed.add_field(name="Mã Quà Tặng", value=f"```{code}```", inline=False)
        embed.add_field(name="Phần Thưởng", value=rewards, inline=False)

        if expires_at:
            expiry_text = f"🟢 **Còn hiệu lực** (Hết hạn: <t:{int(expires_at)}:R> • <t:{int(expires_at)}:f>)"
        else:
            expiry_text = "🟢 **Còn hiệu lực** (Nên nhập sớm)"
        embed.add_field(name="Trạng Thái", value=expiry_text, inline=False)

        if game_info["redeem_method"] == "web":
            embed.add_field(name="Cách Nhận", value=f"👉 **[Bấm vào đây để đổi quà tự động]({game_info['redeem_url']}{code})**", inline=False)
        else:
            embed.add_field(name="Cách Nhập Trong Game", value=f"🎮 {game_info['guide']}", inline=False)

    embed.set_footer(text=f"{game_info['name']} • Giftcode Notification")
    return embed

def create_livestream_embed(game_key: str, version_title: str, timestamp_unix: int, notes: str = None, image_url: str = None) -> discord.Embed:
    game_info = GAMES[game_key]
    embed = discord.Embed(
        title=f"🎬 [LIVESTREAM] CHƯƠNG TRÌNH ĐẶC BIỆT: {game_info['name'].upper()}",
        description=f"### 📢 Phát sóng trực tiếp: {version_title}\nBuổi phát sóng giới thiệu nội dung phiên bản mới sắp diễn ra!",
        color=0xE74C3C
    )
    embed.add_field(
        name="⏰ Thời Gian Phát Sóng (Giờ Việt Nam)",
        value=f"• Thời gian: <t:{timestamp_unix}:F>\n• Đếm ngược: **<t:{timestamp_unix}:R>**",
        inline=False
    )
    embed.add_field(
        name="📺 Link Xem Trực Tiếp",
        value=f"🔴 **[Xem trên YouTube]({game_info.get('youtube_url', '')})**\n🟣 **[Xem trên Twitch]({game_info.get('twitch_url', '')})**",
        inline=False
    )
    reward_note = "300 Nguyên Thạch" if game_key == "genshin" else ("300 Ngọc Ánh Sao" if game_key == "hsr" else "300 Film Màu")
    embed.add_field(
        name="🎁 Phần Thưởng Livestream",
        value=f"Trong buổi phát sóng sẽ phát **3 mã Giftcode** trị giá **{reward_note}**!\n*(Bot sẽ tự động bắt mã và gửi vào kênh ngay khi có)*",
        inline=False
    )
    if notes:
        embed.add_field(name="📝 Ghi Chú Thêm", value=notes, inline=False)
        
    if image_url:
        embed.set_image(url=image_url)

    embed.set_footer(text=f"{game_info['name']} • Special Program Stream")
    return embed

def build_game_summary_embed(game_key: str, codes_list: list) -> discord.Embed:
    game_info = GAMES[game_key]
    embed = discord.Embed(title=f"🎮 {game_info['name']}", color=game_info["color"])

    if not codes_list:
        embed.description = "*Hiện không có mã code nào còn hiệu lực.*"
        return embed

    lines = []
    for item in codes_list[:10]:
        code = item.get("code")
        rewards = item.get("rewards") or item.get("description") or "Phần thưởng"
        if isinstance(rewards, list):
            rewards = ", ".join(rewards)

        if game_info["redeem_method"] == "web":
            lines.append(f"• `{code}` — {rewards} ➔ **[Nhận nhanh]({game_info['redeem_url']}{code})**")
        else:
            lines.append(f"• `{code}` — {rewards}")

    if game_info["redeem_method"] == "in_game":
        lines.append(f"\n💡 *Cách nhập:* {game_info['guide']}")

    embed.description = "\n".join(lines)
    return embed

# ==============================================================================
# UI COMPONENTS (BUTTON & DROPDOWN)
# ==============================================================================
class CodeActionView(discord.ui.View):
    def __init__(self, cog: "GachaCodesCog"):
        super().__init__(timeout=None)
        self.cog = cog

    @discord.ui.button(label="Copy Mã 📋", style=discord.ButtonStyle.primary, custom_id="persistent_btn_copy_gacha_code")
    async def copy_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        message_id = str(interaction.message.id)
        
        async with aiosqlite.connect(DB_PATH) as db:
            async with db.execute("SELECT code FROM tracked_messages WHERE message_id = ?", (message_id,)) as cursor:
                row = await cursor.fetchone()

        if row:
            await interaction.response.send_message(f"{row[0]}", ephemeral=True)
        else:
            await interaction.response.send_message("⚠️ Không tìm thấy mã, hoặc mã đã cũ.", ephemeral=True)

    @discord.ui.button(label="Nhập Vào Game 🎁", style=discord.ButtonStyle.success, custom_id="persistent_btn_redeem_gacha_code")
    async def redeem_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer(ephemeral=True, thinking=True)
        message_id = str(interaction.message.id)

        async with aiosqlite.connect(DB_PATH) as db:
            async with db.execute("SELECT game_key, code FROM tracked_messages WHERE message_id = ?", (message_id,)) as cursor:
                track = await cursor.fetchone()

        if not track:
            return await interaction.followup.send("⚠️ Không tìm thấy thông tin của mã này hoặc mã đã quá cũ.", ephemeral=True)

        game_key, code_str = track

        if game_key not in ["genshin", "hsr", "zzz"]:
            return await interaction.followup.send(
                f"ℹ️ Nhà phát hành **{GAMES.get(game_key, {}).get('name', game_key)}** chỉ cho phép nhập mã trực tiếp trong game (không có web API).\n"
                f"👉 Mã của bạn: `{code_str}` (Hãy copy và vào game nhập theo hướng dẫn nhé!)",
                ephemeral=True
            )

        hoyolab_cog = interaction.client.get_cog("HoyolabCheckin")
        if not hoyolab_cog:
            return await interaction.followup.send("⚠️ Hệ thống HoYoLAB hiện đang không khả dụng.", ephemeral=True)

        await hoyolab_cog.handle_quick_redeem_interaction(interaction, game_key=game_key, code=code_str)

    @discord.ui.button(label="Báo hết hạn ⚠️", style=discord.ButtonStyle.secondary, custom_id="persistent_btn_report_gacha_code")
    async def report_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        message_id = str(interaction.message.id)
        user_id = str(interaction.user.id)
        is_admin = interaction.user.guild_permissions.administrator

        async with aiosqlite.connect(DB_PATH) as db:
            async with db.execute("SELECT game_key, code FROM tracked_messages WHERE message_id = ?", (message_id,)) as cursor:
                track = await cursor.fetchone()
            
            if not track:
                return await interaction.response.send_message("⚠️ Tin nhắn này không còn được theo dõi hoặc đã hết hạn.", ephemeral=True)
            
            game_key, code_str = track

            if is_admin:
                await self.cog.expire_code_globally(game_key, code_str, "Xác nhận bởi Admin")
                return await interaction.response.send_message(f"✅ [Admin] Đã chuyển mã `{code_str}` sang trạng thái hết hạn!", ephemeral=True)

            async with db.execute("SELECT 1 FROM reports WHERE message_id = ? AND user_id = ?", (message_id, user_id)) as cursor:
                if await cursor.fetchone():
                    return await interaction.response.send_message("⚠️ Bạn đã gửi báo cáo cho mã này rồi.", ephemeral=True)

            await db.execute("INSERT INTO reports (message_id, user_id) VALUES (?, ?)", (message_id, user_id))
            async with db.execute("SELECT COUNT(*) FROM reports WHERE message_id = ?", (message_id,)) as cursor:
                count = (await cursor.fetchone())[0]
            await db.commit()

        if count >= REPORT_THRESHOLD:
            await self.cog.expire_code_globally(game_key, code_str, f"Cộng đồng báo cáo ({count}/{REPORT_THRESHOLD})")
            await interaction.response.send_message(f"🚨 Mã `{code_str}` đã nhận đủ lượt báo cáo và bị xóa.", ephemeral=True)
        else:
            await interaction.response.send_message(f"📥 Đã ghi nhận báo cáo ({count}/{REPORT_THRESHOLD} lượt).", ephemeral=True)

class AllCodesSelect(discord.ui.Select):
    def __init__(self, all_data: dict):
        self.all_data = all_data
        options = [discord.SelectOption(label="Tất cả game", value="all", emoji="🌐")]
        for gk, ginfo in GAMES.items():
            options.append(discord.SelectOption(label=ginfo["name"], value=gk))
        super().__init__(placeholder="🔍 Chọn game để lọc mã...", min_values=1, max_values=1, options=options)

    async def callback(self, interaction: discord.Interaction):
        selected = self.values[0]
        if selected == "all":
            embeds = [build_game_summary_embed(gk, self.all_data.get(gk, [])) for gk in GAMES.keys()]
            await interaction.response.edit_message(content="📋 **Danh sách mã code còn hạn (Tất cả game):**", embeds=embeds)
        else:
            embed = build_game_summary_embed(selected, self.all_data.get(selected, []))
            await interaction.response.edit_message(content="📋 **Danh sách mã code còn hạn:**", embeds=[embed])

class AllCodesView(discord.ui.View):
    def __init__(self, all_data: dict):
        super().__init__(timeout=180)
        self.add_item(AllCodesSelect(all_data))

# ==============================================================================
# COG CHÍNH (LỆNH SLASH & VÒNG LẶP NỀN)
# ==============================================================================
GAME_CHOICES = [
    app_commands.Choice(name="Genshin Impact", value="genshin"),
    app_commands.Choice(name="Honkai: Star Rail", value="hsr"),
    app_commands.Choice(name="Zenless Zone Zero", value="zzz"),
    app_commands.Choice(name="Neverness to Everness (NTE)", value="nte"),
    app_commands.Choice(name="Arknights: Endfield", value="endfield")
]

HOYO_CHOICES = [app_commands.Choice(name="Genshin Impact", value="genshin"), app_commands.Choice(name="Honkai: Star Rail", value="hsr"), app_commands.Choice(name="Zenless Zone Zero", value="zzz")]

class GachaCodesCog(commands.GroupCog, group_name="gachacode"):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.session = getattr(bot, "session", None)
        self._owns_session = False
        self.action_view = CodeActionView(self)
        self.check_codes_loop.start()

    async def cog_load(self):
        await init_db()
        if self.session is None:
            self.session = aiohttp.ClientSession()
            self._owns_session = True
        self.bot.add_view(self.action_view)

    async def cog_unload(self):
        self.check_codes_loop.cancel()
        if self._owns_session and self.session and not self.session.closed:
            await self.session.close()

    # --- CORE GIAO TIẾP GỬI/SỬA TIN NHẮN (WEBHOOK + SEMAPHORE) ---
    async def broadcast_code_to_channels(self, game_key: str, code_data: dict, embed: discord.Embed, target_guilds: list = None, is_test: int = 0, is_manual: int = 0):
        game_info = GAMES[game_key]
        
        async with aiosqlite.connect(DB_PATH) as db:
            query = "SELECT guild_id, channel_id, role_id, webhook_url FROM guild_config WHERE game_key = ?"
            params = [game_key]
            if target_guilds:
                query += f" AND guild_id IN ({','.join('?' for _ in target_guilds)})"
                params.extend(target_guilds)
                
            async with db.execute(query, params) as cursor:
                configs = await cursor.fetchall()

        if not configs:
            return 0

        sem = asyncio.Semaphore(15) # Giới hạn 15 request gửi đi cùng lúc
        sent_count = 0

        async def send_task(config):
            nonlocal sent_count
            guild_id, channel_id, role_id, webhook_url = config
            if not webhook_url: return

            async with sem:
                try:
                    # ✅ Sửa lỗi "view parameter requires the webhook to be created with a bot or client"
                    webhook = discord.Webhook.from_url(webhook_url, session=self.session, client=self.bot)
                    mention_text = f"<@&{role_id}> " if role_id else ""
                    
                    msg = await webhook.send(
                        content=f"{mention_text}🔔 Code mới cho **{game_info['name']}**!",
                        embed=embed,
                        view=self.action_view,
                        username=f"{game_info['name']} Notification",
                        wait=True
                    )
                    
                    async with aiosqlite.connect(DB_PATH) as db:
                        await db.execute("""
                            INSERT INTO tracked_messages (message_id, channel_id, guild_id, game_key, code, rewards, expires_at, is_manual, is_test, reminded)
                            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 0)
                        """, (str(msg.id), channel_id, guild_id, game_key, code_data["code"], str(code_data.get("rewards", "")), code_data.get("expires_at"), is_manual, is_test))
                        await db.commit()
                    sent_count += 1
                except Exception as e:
                    print(f"[Webhook Send Error Server {guild_id}] {e}")

        await asyncio.gather(*(send_task(cfg) for cfg in configs))
        return sent_count

    async def _edit_message_expired(self, track: dict, reason: str):
        try:
            async with aiosqlite.connect(DB_PATH) as db:
                async with db.execute("SELECT webhook_url FROM guild_config WHERE guild_id = ? AND game_key = ?", (track['guild_id'], track['game_key'])) as cursor:
                    row = await cursor.fetchone()
            
            webhook_url = row[0] if row else None
            dummy_code_data = {"code": track['code'], "rewards": track['rewards']}
            exp_embed = create_code_embed(track['game_key'], dummy_code_data, is_expired=True, expired_reason=reason)

            if webhook_url:
                # ✅ Sửa lỗi thêm client=self.bot cho chức năng xóa View khi sửa tin nhắn
                webhook = discord.Webhook.from_url(webhook_url, session=self.session, client=self.bot)
                await webhook.edit_message(int(track['message_id']), content="⚠️ **[MÃ NÀY ĐÃ HẾT HẠN]**", embed=exp_embed, view=None)
            else:
                ch = self.bot.get_channel(track['channel_id'])
                if ch:
                    msg = await ch.fetch_message(int(track['message_id']))
                    await msg.edit(content="⚠️ **[MÃ NÀY ĐÃ HẾT HẠN]**", embed=exp_embed, view=None)
        except discord.NotFound:
            pass
        except Exception as e:
            print(f"[GachaCog Expire Edit Error] {e}")

    async def expire_code_globally(self, game_key: str, code_str: str, reason: str):
        async with aiosqlite.connect(DB_PATH) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute("SELECT * FROM tracked_messages WHERE game_key = ? AND code = ?", (game_key, code_str)) as cursor:
                targets = await cursor.fetchall()

        for t in targets:
            await self._edit_message_expired(t, reason)
            await asyncio.sleep(0.5)

        async with aiosqlite.connect(DB_PATH) as db:
            await db.execute("DELETE FROM tracked_messages WHERE game_key = ? AND code = ?", (game_key, code_str))
            for t in targets:
                await db.execute("DELETE FROM reports WHERE message_id = ?", (t['message_id'],))
            await db.commit()

    # --- TÁC VỤ VÒNG LẶP CHẠY NGẦM ---
    @tasks.loop(seconds=CHECK_INTERVAL_SECONDS)
    async def check_codes_loop(self):
        current_time = time.time()
        active_codes_by_game = {}

        for game_key in GAMES.keys():
            codes_data = await fetch_game_codes(self.session, game_key)
            valid_codes = [c for c in codes_data if isinstance(c, dict) and c.get("code")]
            if valid_codes:
                active_codes_by_game[game_key] = [c.get("code") for c in valid_codes]

            async with aiosqlite.connect(DB_PATH) as db:
                async with db.execute("SELECT code FROM sent_codes WHERE game_key = ?", (game_key,)) as cursor:
                    sent_codes = [row[0] for row in await cursor.fetchall()]

                new_items = [c for c in valid_codes if c.get("code") not in sent_codes]
                
                for item in new_items:
                    rewards_str = item.get("rewards") or item.get("description") or "Phần thưởng trong game"
                    if isinstance(rewards_str, list): rewards_str = ", ".join(rewards_str)
                    item["rewards"] = rewards_str

                    embed = create_code_embed(game_key, item, is_expired=False)
                    await self.broadcast_code_to_channels(game_key, item, embed)
                    await db.execute("INSERT OR IGNORE INTO sent_codes (game_key, code) VALUES (?, ?)", (game_key, item["code"]))

                    # Tự động nhập code cho các tài khoản HoYoverse đã liên kết và bật auto_redeem
                    if game_key in ["genshin", "hsr", "zzz"]:
                        hoyolab_cog = self.bot.get_cog("HoyolabCheckin")
                        if hoyolab_cog and hasattr(hoyolab_cog, "auto_redeem_new_code"):
                            asyncio.create_task(hoyolab_cog.auto_redeem_new_code(game_key, item["code"]))
                
                if new_items:
                    await db.commit()

        # 2. Xử lý mã hết hạn & Nhắc nhở
        async with aiosqlite.connect(DB_PATH) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute("SELECT * FROM tracked_messages") as cursor:
                tracked_msgs = await cursor.fetchall()

        for track in tracked_msgs:
            game_key, code, expires_at = track["game_key"], track["code"], track["expires_at"]
            is_manual, reminded = track["is_manual"], track["reminded"]

            is_expired = False
            reason = "Hết hạn sử dụng"

            if expires_at and current_time >= expires_at:
                is_expired = True
                reason = "Quá hạn thời gian"
            elif not is_manual and game_key in active_codes_by_game and code not in active_codes_by_game[game_key]:
                is_expired = True
                reason = "Nhà phát hành đã gỡ mã"

            if is_expired:
                await self._edit_message_expired(track, reason)
                async with aiosqlite.connect(DB_PATH) as db:
                    await db.execute("DELETE FROM tracked_messages WHERE message_id = ?", (track["message_id"],))
                    await db.execute("DELETE FROM reports WHERE message_id = ?", (track["message_id"],))
                    await db.commit()
                await asyncio.sleep(0.5)
            else:
                if expires_at and not reminded and 0 < (expires_at - current_time) <= REMIND_BEFORE_SECONDS:
                    try:
                        ch = self.bot.get_channel(track["channel_id"])
                        if ch:
                            await ch.send(
                                content=f"⏳ **Nhắc nhở:** Mã `{code}` của **{GAMES[game_key]['name']}** sẽ hết hạn <t:{int(expires_at)}:R>! Hãy nhập ngay nhé.",
                                reference=discord.MessageReference(message_id=int(track["message_id"]), channel_id=track["channel_id"])
                            )
                            async with aiosqlite.connect(DB_PATH) as db:
                                await db.execute("UPDATE tracked_messages SET reminded = 1 WHERE message_id = ?", (track["message_id"],))
                                await db.commit()
                    except (discord.NotFound, discord.HTTPException):
                        pass

    @check_codes_loop.before_loop
    async def before_loop(self):
        await self.bot.wait_until_ready()

    # --- SLASH COMMANDS ---
    @app_commands.command(name="setup", description="Cài đặt kênh nhận mã (Có thể bật/tắt nhiều game cùng lúc)")
    @app_commands.default_permissions(administrator=True)
    async def setup_code(
        self, interaction: discord.Interaction, channel: discord.TextChannel, role: discord.Role = None,
        genshin: bool = False, hsr: bool = False, zzz: bool = False, nte: bool = False, endfield: bool = False
    ):
        await interaction.response.defer(ephemeral=True)
        selected_games = []
        if genshin: selected_games.append("genshin")
        if hsr: selected_games.append("hsr")
        if zzz: selected_games.append("zzz")
        if nte: selected_games.append("nte")
        if endfield: selected_games.append("endfield")

        if not selected_games:
            return await interaction.followup.send("⚠️ Bạn phải chọn `True` cho ít nhất 1 tựa game!", ephemeral=True)

        webhook_url = None
        try:
            webhooks = await channel.webhooks()
            bot_webhook = next((w for w in webhooks if w.user == self.bot.user), None)
            if not bot_webhook:
                bot_webhook = await channel.create_webhook(name="Gacha Auto Code")
            webhook_url = bot_webhook.url
        except Exception:
            return await interaction.followup.send(f"❌ Không thể tạo Webhook ở kênh {channel.mention} (Thiếu quyền `Manage Webhooks`).", ephemeral=True)

        guild_id = str(interaction.guild_id)
        role_id = role.id if role else None

        async with aiosqlite.connect(DB_PATH) as db:
            for game_key in selected_games:
                await db.execute("""
                    INSERT OR REPLACE INTO guild_config (guild_id, game_key, channel_id, role_id, webhook_url)
                    VALUES (?, ?, ?, ?, ?)
                """, (guild_id, game_key, channel.id, role_id, webhook_url))
            await db.commit()

        games_str = ", ".join([GAMES[gk]["name"] for gk in selected_games])
        await interaction.followup.send(f"✅ **Đã thiết lập thành công qua Webhook!**\n🎮 **Game:** {games_str}\n📢 **Kênh:** {channel.mention}", ephemeral=True)

    @app_commands.command(name="remove", description="Hủy nhận mã code cho một game hoặc toàn bộ")
    @app_commands.choices(game=[*GAME_CHOICES, app_commands.Choice(name="Tất cả các game (Xóa toàn bộ)", value="all")])
    @app_commands.default_permissions(administrator=True)
    async def remove_setup(self, interaction: discord.Interaction, game: app_commands.Choice[str]):
        guild_id = str(interaction.guild_id)
        async with aiosqlite.connect(DB_PATH) as db:
            if game.value == "all":
                await db.execute("DELETE FROM guild_config WHERE guild_id = ?", (guild_id,))
                msg = "🗑️ Đã xóa toàn bộ cấu hình trên server."
            else:
                await db.execute("DELETE FROM guild_config WHERE guild_id = ? AND game_key = ?", (guild_id, game.value))
                msg = f"🗑️ Đã xóa cấu hình nhận mã của **{game.name}**."
            await db.commit()
        await interaction.response.send_message(msg, ephemeral=True)

    @app_commands.command(name="live", description="Phát thông báo lịch Livestream (Có hỗ trợ gắn Banner)")
    @app_commands.describe(
        game="Chọn game", version="Tên phiên bản (VD: Phiên Bản 5.2)",
        time_str="Giờ VN: DD/MM/YYYY HH:MM", notes="Ghi chú thêm",
        image_url="Link hình ảnh Banner (URL)", create_event="Tự động tạo Sự kiện?"
    )
    @app_commands.choices(game=HOYO_CHOICES)
    @app_commands.default_permissions(administrator=True)
    async def announce_live(self, interaction: discord.Interaction, game: app_commands.Choice[str], version: str, time_str: str, notes: str = None, image_url: str = None, create_event: bool = True):
        await interaction.response.defer(ephemeral=True)
        guild_id = str(interaction.guild_id)
        
        async with aiosqlite.connect(DB_PATH) as db:
            async with db.execute("SELECT channel_id, role_id FROM guild_config WHERE guild_id = ? AND game_key = ?", (guild_id, game.value)) as cursor:
                cfg = await cursor.fetchone()
        
        if not cfg:
            return await interaction.followup.send(f"❌ Bạn chưa setup kênh cho **{game.name}**.", ephemeral=True)

        channel = self.bot.get_channel(cfg[0])
        role_id = cfg[1]
        
        try:
            dt_vn = datetime.strptime(time_str.strip(), "%d/%m/%Y %H:%M").replace(tzinfo=VN_TZ)
            timestamp_unix = int(dt_vn.timestamp())
        except ValueError:
            return await interaction.followup.send("❌ Sai định dạng! Nhập dạng `DD/MM/YYYY HH:MM`.", ephemeral=True)

        embed = create_livestream_embed(game.value, version, timestamp_unix, notes, image_url)
        mention_text = f"<@&{role_id}> " if role_id else ""
        await channel.send(content=f"{mention_text}🎬 **THÔNG BÁO LIVESTREAM CHƯƠNG TRÌNH ĐẶC BIỆT!**", embed=embed)

        event_msg = ""
        if create_event and dt_vn > datetime.now(VN_TZ):
            try:
                game_info = GAMES[game.value]
                cover_image_bytes = None
                if image_url:
                    try:
                        async with self.session.get(image_url) as resp:
                            if resp.status == 200: cover_image_bytes = await resp.read()
                    except Exception:
                        pass

                await interaction.guild.create_scheduled_event(
                    name=f"🎬 Livestream {game.name}: {version}",
                    description=f"Chương trình đặc biệt giới thiệu {version} của {game.name}.\n🎁 Đừng quên theo dõi để nhận 3 mã Giftcode giá trị!",
                    start_time=dt_vn,
                    end_time=dt_vn + timedelta(hours=1, minutes=30),
                    entity_type=discord.EntityType.external,
                    location=game_info.get("youtube_url", "YouTube / Twitch"),
                    privacy_level=discord.PrivacyLevel.guild_only,
                    image=cover_image_bytes
                )
                event_msg = "\n🗓️ **Đã tạo Sự kiện (Scheduled Event) trên Server (Có kèm Banner)!**"
            except Exception as e:
                event_msg = f"\n⚠️ *Không thể tạo Sự kiện tự động: {e}*"

        await interaction.followup.send(f"✅ Đã gửi thông báo Live cho **{game.name}** vào {channel.mention}!{event_msg}", ephemeral=True)

    @app_commands.command(name="all", description="Xem toàn bộ mã code đang còn hạn của TẤT CẢ các tựa game")
    @app_commands.describe(cong_khai="Gửi công khai vào kênh? (Mặc định: Chỉ mình bạn thấy)")
    async def all_codes(self, interaction: discord.Interaction, cong_khai: bool = False):
        await interaction.response.defer(ephemeral=not cong_khai)
        game_keys = list(GAMES.keys())
        results = await asyncio.gather(*(fetch_game_codes(self.session, gk) for gk in game_keys))
        all_data = dict(zip(game_keys, results))

        embed_list = [build_game_summary_embed(gk, all_data[gk]) for gk in game_keys]
        view = AllCodesView(all_data)
        await interaction.followup.send(content="📋 **Danh sách mã code còn hạn (Tất cả game):**", embeds=embed_list, view=view, ephemeral=not cong_khai)

    @app_commands.command(name="test", description="Gửi thử một mã mẫu vào kênh đã cài đặt")
    @app_commands.choices(game=GAME_CHOICES)
    @app_commands.default_permissions(administrator=True)
    async def test_code(self, interaction: discord.Interaction, game: app_commands.Choice[str]):
        await interaction.response.defer(ephemeral=True)
        sample = {"code": "TESTCODE2026", "rewards": "100 Kim Cương/Vé Quay", "expires_at": None}
        embed = create_code_embed(game.value, sample, is_test=True)
        
        sent = await self.broadcast_code_to_channels(game.value, sample, embed, target_guilds=[str(interaction.guild_id)], is_test=1, is_manual=1)
        if sent > 0:
            await interaction.followup.send(f"✅ Đã gửi mã thử nghiệm cho **{game.name}**!", ephemeral=True)
        else:
            await interaction.followup.send(f"❌ Kênh cho **{game.name}** chưa được setup (Hoặc hãy setup lại nếu bạn vừa cập nhật Bot).", ephemeral=True)

    @app_commands.command(name="broadcast", description="Phát mã nóng (Livestream/Event) kèm thời gian đếm ngược")
    @app_commands.describe(game="Chọn game", code="Mã giftcode", rewards="Phần thưởng", hours_valid="Hết hạn sau bao nhiêu giờ?", all_servers="Phát cho TẤT CẢ Server?")
    @app_commands.choices(game=GAME_CHOICES)
    @app_commands.default_permissions(administrator=True)
    async def broadcast_code(self, interaction: discord.Interaction, game: app_commands.Choice[str], code: str, rewards: str, hours_valid: float = None, all_servers: bool = False):
        await interaction.response.defer(ephemeral=True)
        clean_code = code.strip().upper()
        expires_at = (time.time() + (hours_valid * 3600)) if hours_valid else None
        payload = {"code": clean_code, "rewards": rewards, "expires_at": expires_at}
        embed = create_code_embed(game.value, payload, is_expired=False)

        async with aiosqlite.connect(DB_PATH) as db:
            await db.execute("INSERT OR IGNORE INTO sent_codes (game_key, code) VALUES (?, ?)", (game.value, clean_code))
            await db.commit()

        target_guilds = None if all_servers else [str(interaction.guild_id)]
        sent_count = await self.broadcast_code_to_channels(game.value, payload, embed, target_guilds=target_guilds, is_manual=1)

        if sent_count == 0:
            await interaction.followup.send(f"❌ Kênh cho **{game.name}** chưa được setup.", ephemeral=True)
        else:
            scope_text = f"trên **{sent_count} server**" if all_servers else "vào kênh cài đặt"
            await interaction.followup.send(f"✅ Đã phát code `{clean_code}` {scope_text}!", ephemeral=True)

# ==============================================================================
# HÀM NẠP COG CHO BOT LỚN
# ==============================================================================
async def setup(bot: commands.Bot):
    await bot.add_cog(GachaCodesCog(bot))
