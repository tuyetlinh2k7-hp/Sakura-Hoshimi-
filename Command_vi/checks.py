from Checks_vi.i18n import t, is_vietnamese
import discord
import random
import asyncio
import json
import os
import re
import sys
import asyncio
import psutil
import yt_dlp
import time
import math
import subprocess
import threading
import aiohttp

from gtts import gTTS
from discord.ext import commands
from config import GROQ_API_KEY, OWNER_ID
from datetime import timedelta
from groq import Groq
from discord.errors import Forbidden
from datetime import datetime
from discord.ext import tasks
from discord.ui import View, Button
from collections import deque
from functools import wraps
from mctools import RCONClient
from deep_translator import GoogleTranslator
from collections import defaultdict, deque
from pathlib import Path

BASE_DIR = Path(__file__).parent.parent
DATA_FILE = BASE_DIR / "data" / "data.json"
BLACKLIST_FILE = BASE_DIR / "data" / "blacklist.json"
DATA_DIR = BASE_DIR / "data"
RANK_FILE = BASE_DIR / "data" / "trieuphu_rank.json"
TRIEUPHU_FILE = BASE_DIR / "data" / "trieuphu.json"

def load_json(filename, default=None):
    path = DATA_DIR / filename

    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except:
        return default if default is not None else {}

def save_json(filename, data):
    path = DATA_DIR / filename

    with open(path, "w", encoding="utf-8") as f:
        json.dump(
            data,
            f,
            ensure_ascii=False,
            indent=4
        )

groq_client = Groq(
    api_key=GROQ_API_KEY
)

YTDL_OPTIONS = {

    "format": "bestvideo+bestaudio/best",

    "quiet": True,

    "noplaylist": True,

    "extract_flat": False,

    "cookiefile": "cookies.txt",

    "nocheckcertificate": True,

    "ignoreerrors": True
}

ytdl = yt_dlp.YoutubeDL(
    YTDL_OPTIONS
)

# delay fish system
last_global_fish = {}

# tts system
tts_queue = {}
tts_playing = {}

last_tts_user = {}

# Voice text channels system
voice_text_channels = {}

# Chat log system
chat_log_channels = {}
edit_log_channels = {}
delete_log_channels = {}

# AFK system
afk_users = {}

# Cooldown system
download_cooldown = {}

#admin role system
admin_roles = {}

#blacklist system
blacklist_users = set()

#` Log system`
warnings = {}

guild_settings = {}


with open(DATA_FILE, "r", encoding="utf-8") as f:
    data = json.load(f)

admin_roles = data.get("admin_roles", {})

# Load data from file
if os.path.exists(DATA_FILE):

    with open(DATA_FILE, "r") as f:

        data = json.load(f)

        levels = data.get("level", {})
        gain = data.get("xp", {})
        user_coins = data.get("coins", {})
        user_inventory = data.get("inventory", {})

        admin_roles = data.get(
            "admin_roles",
            {}
        )

else:

    levels = {}
    gain = {}
    user_coins = {}
    user_inventory = {}

    admin_roles = {}

if os.path.exists(
    BLACKLIST_FILE
):

    with open(

        BLACKLIST_FILE,

        "r",

        encoding="utf-8"

    ) as f:

        blacklist_users = set(
            json.load(f)
        )

else:

    blacklist_users = set()

def is_bot_owner():

    async def predicate(ctx):

        # Nếu là chủ bot
        if ctx.author.id == OWNER_ID:

            return True

        # Không phải chủ bot
        embed = discord.Embed(
            title=t(ctx, "CHECK_NO_PERMISSION", default="❌ Không có quyền"),
            description=t(ctx, "CHECK_OWNER_ONLY", default="Chỉ chủ bot mới được dùng lệnh này"),
            color=discord.Color.red()
        )

        embed.set_footer(
            text=f"User ID: {ctx.author.id}"
        )

        await ctx.send(embed=embed)

        return False

    return commands.check(predicate)

def create_user(user_id):

    defaults = {

        "xp": 0,

        "level": 1,

        "coins": 0,

        "inventory": [],

        "fish": [],

        "rods": [],

        "pets": [],

        "shields": False,

        "fish_limit": 50,

        "inventory_limit": 50,

        "muted_until": 0
    }

    # chưa có user
    if user_id not in levels:

        levels[user_id] = defaults.copy()

    # thiếu key
    else:

        for k, v in defaults.items():

            if k not in levels[user_id]:

                levels[user_id][k] = v

def delete_file(file):

    if os.path.exists(file):

        os.remove(file)

async def play_next_tts(

    guild_id,

    voice,

    bot
):

    # queue rỗng
    if (

        guild_id not in tts_queue
        or
        not tts_queue[guild_id]
    ):

        tts_playing[guild_id] = False

        return

    tts_playing[guild_id] = True

    data = tts_queue[guild_id].popleft()

    file_name = data["file"]

    # play
    voice.play(

        discord.FFmpegPCMAudio(
            file_name
        ),

        after=lambda e:
        asyncio.run_coroutine_threadsafe(

            after_tts(

                guild_id,

                voice,

                file_name
            ),

            bot.loop
        )
    )

tts_names = load_json(
    "tts_names.json",
    {}
)

def is_valid_word(word):

    return word.lower() in VALID_WORDS # type: ignore

def save_tts_names():
    save_json(
        "tts_names.json",
        tts_names
    )

async def after_tts(

    guild_id,

    voice,

    filename
):

    # đợi ffmpeg release file
    await asyncio.sleep(2)

    try:

        if os.path.exists(filename):

            os.remove(filename)

    except:

        pass

    # play tiếp
    await play_next_tts(

        guild_id,

        voice
    )

def get_guild_settings(guild_id):

    guild_id = str(guild_id)

    if guild_id not in guild_settings:

        guild_settings[guild_id] = {

            "welcome": True,
            "goodbye": True
        }

    return guild_settings[guild_id]

def save_codes():

    with open(
        "data/giftcodes.json",
        "w",
        encoding="utf-8"
    ) as f:

        json.dump(
            gift_codes,
            f,
            ensure_ascii=False,
            indent=4
        )

def load_codes():

    global gift_codes

    try:

        with open(
            "data/giftcodes.json",
            "r",
            encoding="utf-8"
        ) as f:

            gift_codes = json.load(f)

    except:

        gift_codes = {}

def save_blacklist():

    with open(

        BLACKLIST_FILE,

        "w",

        encoding="utf-8"

    ) as f:

        json.dump(

            list(blacklist_users),

            f,

            indent=4
        )

ACTIONS = {
    "blush": "đỏ mặt",
    "cry": "khóc",
    "dance": "nhảy múa",
    "pout": "dỗi",
    "shrug": "nhún vai",
    "sleepy": "buồn ngủ",
    "smile": "mỉm cười",
    "smug": "đắc ý",
    "thinking": "suy nghĩ",
    "thonking": "suy nghĩ căng não",
    "triggered": "kích động",
    "teehee": "cười khúc khích",
    "deredere": "dễ thương",
    "happy": "vui vẻ",
    "grin": "cười toe toét",
    "scoff": "cười khẩy",
    "laugh": "cười lớn",
    "giggle": "cười khúc khích",
    "facepalm": "bó tay",
    "confused": "bối rối",
    "angry": "tức giận",
    "sad": "buồn bã",
    "bored": "chán nản",
    "scared": "sợ hãi",
    "surprised": "ngạc nhiên",
    "shocked": "sốc",
    "embarrassed": "xấu hổ",
    "nervous": "hồi hộp",
    "excited": "phấn khích",
    "relaxed": "thư giãn",
    "yawn": "ngáp",
    "run": "chạy",
    "jump": "nhảy",
    "wave": "vẫy tay",
    "wink": "nháy mắt",
    "thumbsup": "giơ ngón tay cái",
    "clap": "vỗ tay",
    "cheer": "cổ vũ",
    "celebrate": "ăn mừng",
    "read": "đọc sách",
    "study": "học bài",
    "work": "làm việc",
    "listen": "nghe nhạc",
    "sing": "ca hát",
    "sleep": "ngủ",
    "rest": "nghỉ ngơi",
    "drink": "uống nước",
    "eat": "ăn uống",
    "pray": "cầu nguyện",
    "meditate": "thiền định",
    "stargaze": "ngắm sao",
    "think": "suy tư"
}
async def get_action_gif(action):
    url = f"https://nekos.best/api/v2/{action}"

    async with aiohttp.ClientSession() as session:
        async with session.get(url) as resp:
            if resp.status == 200:
                data = await resp.json()
                return data["results"][0]["url"]

    return None

ACTION_MAP = {
    "hug": "ôm",
    "kiss": "hôn",
    "pat": "xoa đầu",
    "poke": "chọc",
    "slap": "tát",
    "cuddle": "âu yếm",
    "bite": "cắn",
    "nom": "gặm",
    "lick": "liếm",
    "tickle": "cù lét",
    "highfive": "đập tay",
    "handhold": "nắm tay",
    "hold": "ôm chặt",
    "greet": "chào hỏi",
    "waveat": "vẫy tay với",
    "stare": "nhìn chằm chằm vào",
    "boop": "chạm mũi",
    "bonk": "cốc đầu",
    "punch": "đấm",
    "kick": "đá",
    "throw": "ném",
    "shoot": "bắn",
    "yeet": "quăng",
    "feed": "đút ăn",
    "gift": "tặng quà cho",
    "love": "thể hiện tình cảm với",
    "protect": "bảo vệ",
    "comfort": "an ủi",
    "carry": "cõng",
    "escort": "hộ tống",
    "chase": "đuổi theo",
    "tap": "gõ nhẹ vào",
    "pet": "vuốt ve",
    "snuggle": "ôm ấp",
    "glomp": "lao vào ôm",
    "laughat": "cười vào mặt",
    "tease": "trêu chọc",
    "pokecheek": "chọc má",
    "pinch": "nhéo",
    "winkat": "nháy mắt với",
    "salute": "chào kiểu quân đội với",
    "respect": "thể hiện sự tôn trọng với",
}

async def get_action_gif(action):

    async with aiohttp.ClientSession() as session:

        async with session.get(
            f"https://nekos.best/api/v2/{action}"
        ) as resp:

            if resp.status == 200:

                data = await resp.json()

                return data["results"][0]["url"]

    return None

PREDICTIONS = [
    "🔮 Có vẻ rất khả quan!",
    "✨ Khả năng cao sẽ thành công.",
    "🍀 Hôm nay vận may đang mỉm cười với bạn.",
    "😎 Dấu hiệu cho thấy mọi chuyện sẽ ổn.",
    "🤔 Kết quả vẫn còn khó đoán.",
    "☁️ Có thể, nhưng cần thêm nỗ lực.",
    "⚠️ Cẩn thận, mọi thứ không như mong đợi.",
    "💀 Có lẽ không phải lúc này.",
    "🙈 Tương lai đang được che giấu.",
    "🌈 Một bất ngờ thú vị đang chờ phía trước.",
    "🔥 Đây là thời điểm thích hợp để thử.",
    "❌ Các vì sao nói rằng câu trả lời là không."
]

# Load blacklist from file
async def blacklist_check(ctx):

    # =========================
    # BYPASS COMMAND
    # =========================

    bypass_commands = [

        "appeal"
    ]

    # =========================
    # ALLOW BYPASS
    # =========================

    if (
        ctx.command
        and
        ctx.command.name
        in bypass_commands
    ):

        return True

    # =========================
    # CHECK BLACKLIST
    # =========================

    if ctx.author.id in blacklist_users:

        embed = discord.Embed(
            title=t(ctx, "CHECK_BLACKLISTED_TITLE", default="⛔ Bạn bị cấm dùng bot"),
            description=t(ctx, "CHECK_BLACKLISTED_DESC", default="Bạn không thể dùng lệnh của bot"),
            color=discord.Color.red()
        )

        await ctx.send(
            embed=embed
        )

        return False

    return True

PRIZES = [
    "200.000₫",
    "400.000₫",
    "600.000₫",
    "1.000.000₫",
    "2.000.000₫",
    "3.000.000₫",
    "6.000.000₫",
    "10.000.000₫",
    "22.000.000₫",
    "150.000.000₫"
]

def load_questions():
    with open(TRIEUPHU_FILE, "r", encoding="utf-8") as f:
        return json.load(f)
    
def load_rank():

    if not os.path.exists(RANK_FILE):
        return {}

    with open(RANK_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def save_rank(data):

    with open(RANK_FILE, "w", encoding="utf-8") as f:
        json.dump(
            data,
            f,
            ensure_ascii=False,
            indent=4
        )

def update_rank(user_id, money):

    data = load_rank()

    user_id = str(user_id)

    if user_id not in data:
        data[user_id] = money

    elif money > data[user_id]:
        data[user_id] = money

    save_rank(data)

# =========================
# ADD GLOBAL CHECK
# =========================

# Kiểm tra data
for user_id in user_inventory:

    if type(user_inventory[user_id]) != list:

        user_inventory[user_id] = []

# Save data to file
def save_data():

    data = {

        "xp": gain,
        "level": levels,
        "coins": user_coins,
        "inventory": user_inventory,

        "admin_roles": admin_roles,

        "chat_log_channels": chat_log_channels,

        "edit_log_channels": edit_log_channels,

        "delete_log_channels": delete_log_channels
    }

    with open(DATA_FILE, "w") as f:

        json.dump(data, f, indent=4)

# kênh gửi phản hồi từ user tới admin
APPEAL_CHANNEL_ID = 1505854802645487696

RARITY_COLORS = {

    "common": discord.Color.light_grey(),

    "rare": discord.Color.blue(),

    "epic": discord.Color.purple(),

    "legendary": discord.Color.gold(),

    "admin": discord.Color.red()
}

appeal_cooldown = {}

# LEVEL SYSTEM
user_xp = {}
user_level = {}

# COIN SYSTEM
user_coins = {}

# TTS CHANNELS SYSTEM
tts_channels = ()

muted_users = {}

# Inventory system
user_inventory = {}

# Cooldown system
daily_cooldown = {}

#market system
market_items = []

if os.path.exists(
    "data/market.json"
):

    with open(
        "data/market.json",
        "r",
        encoding="utf-8"
    ) as f:

        market_items = json.load(f)

else:

    market_items = []

def save_market():

    with open(
        "data/market.json",
        "w",
        encoding="utf-8"
    ) as f:

        json.dump(

            market_items,

            f,

            indent=4,

            ensure_ascii=False
        )

RATESS = {
        "thiệncảm": "💖 Độ Thiện Cảm",
        "maymắn": "🍀 Độ May Mắn",
        "chămhọc": "📚 Mức Độ Chăm Học",
        "ngầu": "😎 Độ Ngầu",
        "simp": "🌹 Chỉ Số Simp",
        "lười": "🛌 Độ Lười Biếng",
        "thânthiện": "🤝 Độ Thân Thiện",
        "hàihước": "😂 Độ Hài Hước",
        "đángtin": "⭐ Độ Đáng Tin Cậy",
        "pro": "🏆 Độ Pro",
        "giàu": "💰 Chỉ Số Giàu Có",
        "đẹptrai": "😏 Độ Đẹp Trai",
        "xinhgái": "😊 Độ Xinh Gái",
        "cute": "🥰 Độ Dễ Thương"
    }

class PhoneSelectView(discord.ui.View):

    def __init__(self, game_view):
        super().__init__(timeout=30)
        self.game_view = game_view

    @discord.ui.select(
        cls=discord.ui.UserSelect,
        placeholder="📞 Chọn người thân để gọi...",
        min_values=1,
        max_values=1
    )
    async def select_user(
        self,
        interaction: discord.Interaction,
        select: discord.ui.UserSelect
    ):

        target = select.values[0]

        if target.bot:
            return await interaction.response.send_message(
                "❌ Không thể gọi cho bot.",
                ephemeral=True
            )

        try:

            question = self.game_view.current_question
            answers = self.game_view.answers_text

            letters = ["A", "B", "C", "D"]

            answer_text = "\n".join(
                f"**{letters[i]}.** {answers[i]}"
                for i in range(len(answers))
            )

            embed = discord.Embed(
                title="📞 Ai Là Triệu Phú - Trợ Giúp",
                description=(
                    f"🎮 {interaction.user.display_name} đang cần trợ giúp.\n\n"
                    f"❓ **{question}**"
                ),
                color=discord.Color.blurple()
            )

            embed.add_field(
                name="Đáp án",
                value=answer_text,
                inline=False
            )

            embed.set_footer(
                text="Trả lời A, B, C hoặc D trong DM này."
            )

            await target.send(embed=embed)

        except:

            return await interaction.response.send_message(
                "❌ Người này đang tắt DM.",
                ephemeral=True
            )

        await interaction.response.send_message(
            f"📞 Đã gọi cho {target.mention}.",
            ephemeral=True
        )

        def check(msg):
            return (
                msg.author.id == target.id
                and isinstance(msg.channel, discord.DMChannel)
                and msg.content.upper() in ["A", "B", "C", "D"]
            )

        try:

            msg = await interaction.client.wait_for(
                "message",
                timeout=30,
                check=check
            )

            answer = msg.content.upper()

            result = discord.Embed(
                title="📞 Người thân trả lời",
                description=(
                    f"👤 {target.mention}\n"
                    f"💬 Chọn đáp án: **{answer}**"
                ),
                color=discord.Color.green()
            )

            await interaction.followup.send(
                embed=result,
                ephemeral=True
            )

        except asyncio.TimeoutError:

            await interaction.followup.send(
                "⏰ Người thân không trả lời.",
                ephemeral=True
            )

        self.stop()

class MillionaireView(discord.ui.View):

    def __init__(self, owner, guild=None):
        super().__init__(timeout=30)
        self.owner = owner
        self.guild = guild
        vi = is_vietnamese(guild) if guild else True
        self.stop_game.label = "Kết thúc" if vi else "End Game"
        self.fifty.label = "50:50"
        self.audience.label = "Khán giả" if vi else "Audience"
        self.phone.label = "Gọi điện" if vi else "Phone a Friend" 
        self.answer = None
        self.used_5050 = False
        self.used_audience = False
        self.used_phone = False
        self.ended = False

        self.current_question = None

        self.correct_index = None
        self.answers_text = None
        self.ctx = None

    async def interaction_check(self, interaction):

        if interaction.user.id != self.owner.id:
            await interaction.response.send_message(
                "❌ Đây không phải lượt chơi của bạn.",
                ephemeral=True
            )
            return False

        return True

    @discord.ui.button(label="A", style=discord.ButtonStyle.primary)
    async def button_a(self, interaction, button):
        if interaction.user.id != self.owner.id:
            return
    
        self.answer = 0
        await interaction.response.defer()
        self.stop()

    @discord.ui.button(label="B", style=discord.ButtonStyle.primary)
    async def button_b(self, interaction, button):
        if interaction.user.id != self.owner.id:
            return
        
        self.answer = 1
        await interaction.response.defer()
        self.stop()

    @discord.ui.button(label="C", style=discord.ButtonStyle.primary)
    async def button_c(self, interaction, button):
        if interaction.user.id != self.owner.id:
            return
        
        self.answer = 2
        await interaction.response.defer()
        self.stop()

    @discord.ui.button(label="D", style=discord.ButtonStyle.primary)
    async def button_d(self, interaction, button):
        if interaction.user.id != self.owner.id:
            return
        
        self.answer = 3
        await interaction.response.defer()
        self.stop()
    
    @discord.ui.button(
        label="Kết thúc",
        emoji="🛑",
        style=discord.ButtonStyle.danger,
        row=1
    )
    async def stop_game(self, interaction, button):
        if interaction.user.id != self.owner.id:
            await interaction.response.send_message(
                "❌ Đây không phải lượt chơi của bạn.",
                ephemeral=True
            )

        self.ended = True

        await interaction.response.send_message(
            "💰 Bạn đã dừng cuộc chơi.",
            ephemeral=True
        )

        self.stop()
    
    @discord.ui.button(
        label="50:50",
        emoji="5️⃣",
        style=discord.ButtonStyle.secondary,
        row=1
    )
    async def fifty(self, interaction, button):
        if interaction.user.id != self.owner.id:
            await interaction.response.send_message(
                "❌ Đây không phải lượt chơi của bạn.",
                ephemeral=True
            )

        if self.used_5050:
            return await interaction.response.send_message(
                "❌ Bạn đã dùng quyền trợ giúp này.",
                ephemeral=True
            )

        self.used_5050 = True

        wrong = [
            i for i in range(4)
            if i != self.correct_index
        ]

        remove = random.sample(wrong, 2)

        letters = ["A", "B", "C", "D"]

        text = ""

        for i, answer in enumerate(self.answers_text):

            if i in remove:
                text += f"**{letters[i]}.** ~~Đã loại~~\n"
            else:
                text += f"**{letters[i]}.** {answer}\n"

        embed = discord.Embed(
            title="5️⃣0️⃣:5️⃣0️⃣",
            description=text,
            color=discord.Color.orange()
        )

        await interaction.response.send_message(
            embed=embed,
            ephemeral=True
        )

        button.disabled = True
        await interaction.message.edit(view=self)

    @discord.ui.button(
        label="Khán giả",
        emoji="👥",
        style=discord.ButtonStyle.success,
        row=1
    )
    async def audience(self, interaction, button):
        if interaction.user.id != self.owner.id:
            await interaction.response.send_message(
                "❌ Đây không phải lượt chơi của bạn.",
                ephemeral=True
            )

        if self.used_audience:
            return await interaction.response.send_message(
                "❌ Đã sử dụng.",
                ephemeral=True
            )

        self.used_audience = True

        votes = [0, 0, 0, 0]

        votes[self.correct_index] = random.randint(
            45,
            80
        )

        remain = 100 - votes[self.correct_index]

        wrong = [
            i for i in range(4)
            if i != self.correct_index
        ]

        for i in wrong:
            votes[i] = remain // 3

        embed = discord.Embed(
            title="👥 Ý kiến khán giả",
            color=discord.Color.green()
        )

        letters = ["A", "B", "C", "D"]

        for i in range(4):

            embed.add_field(
                name=letters[i],
                value=f"{votes[i]}%",
                inline=True
            )   

        await interaction.response.send_message(
            embed=embed,
            ephemeral=True
        )

        button.disabled = True
        await interaction.message.edit(view=self)

    @discord.ui.button(
        label="Gọi điện",
        emoji="📞",
        style=discord.ButtonStyle.primary,
        row=1
    )
    async def phone(self, interaction, button):
        if interaction.user.id != self.owner.id:
            await interaction.response.send_message(
                "❌ Đây không phải lượt chơi của bạn.",
                ephemeral=True
            )

        if self.used_phone:
            return await interaction.response.send_message(
                "❌ Đã sử dụng.",
                ephemeral=True
            )

        self.used_phone = True

        phone_view = PhoneSelectView(self)

        await interaction.response.send_message(
            "📞 Chọn người thân để gọi:",
            view=phone_view,
            ephemeral=True
        )

        button.disabled = True
        await interaction.message.edit(view=self)

PRIZE_VALUES = [
    2000,
    4000,
    6000,
    10000,
    20000,
    30000,
    60000,
    100000,
    220000,
    1500000
]