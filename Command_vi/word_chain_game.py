import discord
from discord.ext import commands, tasks
from discord import app_commands
import json
import os
import random
import asyncio
import aiohttp
from datetime import datetime, time, timezone, timedelta
from typing import Optional, Dict, Set, List
from Checks_vi.i18n import t, is_vietnamese

# --- CẤU HÌNH ĐƯỜNG DẪN ---
WORD_CHAIN_CONFIG_FILE = "data/word_chain_config.json"
WORD_CHAIN_ACTIVE_GAMES_FILE = "data/word_chain_active_games.json"
WORD_CHAIN_SCORES_FILE = "data/word_chain_scores.json"
WORD_CHAIN_WEEKLY_SCORES_FILE = "data/word_chain_weekly_scores.json"
WORD_CHAIN_STATS_FILE = "data/word_chain_stats.json"
WORD_LIST_FILE = "data/vietnamese-words.txt"

# --- CẤU HÌNH XKIRO API (OpenAI-compatible) ---
from config import XKIRO_API_KEY
try:
    from config import AI_MODEL as XKIRO_MODEL
except ImportError:
    XKIRO_MODEL = "sensenova/sensenova-6.8-flash-lite"
XKIRO_API_URL = "https://api.xkiro.com/v1/chat/completions"

# Múi giờ Việt Nam (UTC+7)
VN_TZ = timezone(timedelta(hours=7))

# --- DANH SÁCH DANH HIỆU & THÀNH TỰU ---
ACHIEVEMENTS = {
    "vua_khoa_mom": {
        "name": "👑 Vua Khóa Mõm",
        "desc": "Dồn đối phương vào thế bí từ 10 lần",
        "field": "wins",
        "target": 10
    },
    "nha_tu_dien": {
        "name": "📚 Nhà Từ Điển Học",
        "desc": "Đóng góp 5 từ vựng mới hợp lệ vào từ điển",
        "field": "contributed",
        "target": 5
    },
    "ke_huy_diet": {
        "name": "💥 Kẻ Hủy Diệt Chuỗi",
        "desc": "Làm đứt chuỗi từ đang có độ dài >= 25 từ (3 lần)",
        "field": "long_streaks_broken",
        "target": 3
    },
    "ngon_lua_bat_diet": {
        "name": "🔥 Ngọn Lửa Bất Diệt",
        "desc": "Tham gia nối đạt mốc chuỗi 50 từ trở lên",
        "field": "max_streak",
        "target": 50
    },
    "chien_than_sinh_ton": {
        "name": "⚔️ Chiến Thần Sinh Tồn",
        "desc": "Chiến thắng chế độ Đấu Trường Sinh Tử (Battle Royale) 3 lần",
        "field": "br_wins",
        "target": 3
    },
    "bach_phat_bach_trung": {
        "name": "🎯 Bách Phát Bách Trúng",
        "desc": "Nối đúng 100 từ với tỷ lệ chính xác từ 90% trở lên",
        "field": "correct_words",
        "target": 100
    }
}


def is_valid_chain(prev_phrase: str, new_phrase: str) -> bool:
    prev_words = prev_phrase.split()
    new_words = new_phrase.split()
    if not prev_words or not new_words or len(new_words) != 2:
        return False
    return prev_words[-1] == new_words[0]


# --- 1. GIAO DIỆN EMBED HƯỚNG DẪN TƯƠNG TÁC ---
class HelpSelect(discord.ui.Select):
    def __init__(self, prefix: str):
        self.prefix = prefix
        options = [
            discord.SelectOption(label="Luật chơi cơ bản", emoji="📖", value="basic", description="Cách chơi, mẹo chat và hệ thống tính điểm"),
            discord.SelectOption(label="Tính năng & Vật phẩm", emoji="🛡️", value="features", description="Khiên bảo vệ, Từ khóa vàng, Đấu với Bot"),
            discord.SelectOption(label="Đấu Trường Sinh Tử (BR)", emoji="⚔️", value="br", description="Chế độ loại trực tiếp ăn trọn quỹ thưởng"),
            discord.SelectOption(label="Hồ sơ & Thành tựu", emoji="🏆", value="profile", description="Danh hiệu đặc biệt và thống kê cá nhân"),
            discord.SelectOption(label="Danh sách Lệnh", emoji="⌨️", value="commands", description="Tất cả các lệnh của game nối từ")
        ]
        super().__init__(placeholder="📌 Chọn mục hướng dẫn bạn muốn xem...", min_values=1, max_values=1, options=options)

    async def callback(self, interaction: discord.Interaction):
        val = self.values[0]
        p = self.prefix
        embed = discord.Embed(color=discord.Color.blurple())

        if val == "basic":
            embed.title = "📖 LUẬT CHƠI NỐI TỪ CƠ BẢN"
            embed.description = (
                "• **Quy tắc:** Nối một cụm **2 âm tiết** có nghĩa trong tiếng Việt sao cho từ đầu tiên của bạn trùng với từ cuối cùng của người trước.\n"
                "  *(Ví dụ: `con mèo` ➔ `mèo mướp` ➔ `mướp đắng`)*\n"
                "• **Giới hạn lặp từ:** Mỗi cụm từ chỉ được phép sử dụng tối đa **3 lần** trong một ván đấu.\n"
                "• **Không tự nối:** Bạn không thể nối 2 lượt liên tiếp (trừ khi bật chế độ Đấu với Bot).\n"
                "• **Mẹo trò chuyện:** Thêm dấu `.`, `!`, `?` hoặc `/` ở đầu câu (VD: `.từ này khó thế`) để chat tự do trong kênh mà không bị Bot bắt lỗi!"
            )
        elif val == "features":
            embed.title = "🛡️ TÍNH NĂNG ĐẶC BIỆT & VẬT PHẨM"
            embed.description = (
                "• **🤖 Trí tuệ nhân tạo xKiro:** Từ chưa có trong file từ điển sẽ được model `mistralai/mistral-large-4-0` tự động thẩm định và bổ sung.\n"
                "• **🌟 Từ Khóa Vàng (x3 Điểm):** Mỗi 8 lượt, Bot đưa ra chữ cái thử thách cho âm tiết thứ 2. Ai giải được nhận ngay **3 điểm**.\n"
                "• **🛡️ Khiên Bảo Vệ:** Mua bằng lệnh `/wc shield` (5 điểm) hoặc nhận miễn phí mỗi chuỗi 30 từ. Khiên tự động đỡ 1 lần nối sai để cứu chuỗi của phòng (tối đa 3 Khiên).\n"
                "• **💡 Mua Gợi Ý:** Dùng `/wc hint` (tốn 2 điểm) khi cả phòng bị bí từ.\n"
                "• **🤖 Đấu với Bot (PvE):** Bật bằng `/wc botmode` khi kênh vắng người để luyện phản xạ cùng Bot."
            )
        elif val == "br":
            embed.title = "⚔️ ĐẤU TRƯỜNG SINH TỬ (BATTLE ROYALE)"
            embed.description = (
                "• **Cách mở phòng:** Gõ `/wc br` để mở sảnh chờ trong **45 giây** (cần tối thiểu 2 người bấm **Tham gia**).\n"
                "• **Thể thức:** Bot gọi tên từng người theo vòng tròn. Người được gọi có **15 giây** để nối từ.\n"
                "• **Loại trực tiếp:** Nếu hết 15 giây không trả lời hoặc trả lời sai (mọi từ chỉ được dùng **1 lần**), người chơi đó sẽ bị loại khỏi vòng đấu.\n"
                "• **Phần thưởng Jackpot:** Người sống sót cuối cùng sẽ ẵm trọn quỹ điểm thưởng (`Số người tham gia x 5 điểm`) và tích lũy chiến tích **Chiến Thần Sinh Tồn**!"
            )
        elif val == "profile":
            embed.title = "🏆 HỒ SƠ CÁ NHÂN & DANH HIỆU"
            embed.description = (
                "Gõ `/wc profile` để xem thẻ thống kê chi tiết và các danh hiệu bạn đã mở khóa:\n\n"
                + "\n".join([f"• **{v['name']}**: {v['desc']}" for v in ACHIEVEMENTS.values()])
            )
        elif val == "commands":
            embed.title = "⌨️ DANH SÁCH LỆNH GAME NỐI TỪ"
            embed.description = (
                f"• `{p}wc start [từ] [đấu_bot]` : Bắt đầu ván mới\n"
                f"• `{p}wc br` : Mở phòng Đấu Trường Sinh Tử\n"
                f"• `{p}wc profile [@user]` : Xem hồ sơ thống kê & danh hiệu\n"
                f"• `{p}wc rank [tuần/tổng]` : Xem bảng xếp hạng\n"
                f"• `{p}wc hint` : Mua gợi ý từ (-2 điểm)\n"
                f"• `{p}wc shield` : Mua Khiên bảo vệ chuỗi (-5 điểm)\n"
                f"• `{p}wc botmode` : Bật/tắt chế độ đấu với Bot\n"
                f"• `{p}wc contribute <từ>` : Đóng góp từ mới vào từ điển\n"
                f"• `{p}wc setup <#kênh>` : (Admin) Cài đặt kênh chơi\n"
                f"• `{p}wc stop` : (Admin) Dừng ván đấu hiện tại"
            )

        embed.set_footer(text="Chọn mục khác ở thanh menu bên dưới để xem thêm.")
        await interaction.response.edit_message(embed=embed, view=self.view)


class HelpView(discord.ui.View):
    def __init__(self, prefix: str):
        super().__init__(timeout=300)
        self.add_item(HelpSelect(prefix))


# --- 2. GIAO DIỆN ĐỀ XUẤT & DUYỆT TỪ MỚI ---
class WordContributeView(discord.ui.View):
    def __init__(self, cog: "WordChainGame", word: str, author_id: int, guild_id_str: str):
        super().__init__(timeout=600)
        self.cog = cog
        self.word = word
        self.author_id = author_id
        self.guild_id_str = guild_id_str
        self.proposed = False
        vi = is_vietnamese(int(guild_id_str)) if guild_id_str.isdigit() else True
        self.propose_btn.label = "📩 Đề xuất thêm từ này" if vi else "📩 Suggest adding this word"

    @discord.ui.button(label="📩 Đề xuất thêm từ này", style=discord.ButtonStyle.secondary)
    async def propose_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        vi = is_vietnamese(interaction.guild)
        if self.proposed:
            already_msg = "Từ này đã được gửi yêu cầu duyệt rồi!" if vi else "This word is already awaiting approval!"
            return await interaction.response.send_message(already_msg, ephemeral=True)

        self.proposed = True
        button.disabled = True
        button.label = "⏳ Đang chờ Admin duyệt..." if vi else "⏳ Awaiting Admin approval..."

        approve_btn = discord.ui.Button(label="✅ Duyệt từ" if vi else "✅ Approve", style=discord.ButtonStyle.success)
        reject_btn = discord.ui.Button(label="🗑️ Từ chối" if vi else "🗑️ Reject", style=discord.ButtonStyle.danger)

        async def approve_callback(inter: discord.Interaction):
            if not inter.user.guild_permissions.administrator:
                return await inter.response.send_message("❌ Chỉ Admin mới có quyền duyệt từ!", ephemeral=True)

            self.cog.add_new_word_to_dict(self.word)
            # Cộng chỉ số đóng góp từ cho người đề xuất
            p_stats = self.cog.get_player_stats(self.guild_id_str, str(self.author_id))
            p_stats["contributed"] += 1
            unlocked = self.cog.check_achievements(p_stats)
            self.cog.dirty_data = True

            self.clear_items()
            ach_msg = f"\n🎉 <@{self.author_id}> vừa mở khóa danh hiệu: **{', '.join(unlocked)}**!" if unlocked else ""
            await inter.response.edit_message(
                content=f"✅ Admin {inter.user.mention} đã phê duyệt từ **`{self.word}`** vào từ điển! (<@{self.author_id}> +1 đóng góp){ach_msg}",
                view=self
            )

        async def reject_callback(inter: discord.Interaction):
            if not inter.user.guild_permissions.administrator:
                return await inter.response.send_message("❌ Chỉ Admin mới có quyền từ chối!", ephemeral=True)

            self.clear_items()
            await inter.response.edit_message(
                content=f"❌ Admin {inter.user.mention} đã từ chối thêm từ **`{self.word}`**.",
                view=self
            )

        approve_btn.callback = approve_callback
        reject_btn.callback = reject_callback
        self.add_item(approve_btn)
        self.add_item(reject_btn)

        await interaction.response.edit_message(
            content=f"📢 {interaction.user.mention} đã đề xuất thêm từ **`{self.word}`** vào từ điển. Admin hãy kiểm tra nhé!",
            view=self
        )


# --- 3. GIAO DIỆN PHÒNG CHỜ BATTLE ROYALE ---
class BRLobbyView(discord.ui.View):
    def __init__(self, host: discord.Member):
        super().__init__(timeout=45)
        self.host = host
        self.players: List[int] = [host.id]
        vi = is_vietnamese(host.guild)
        self.join_btn.label = f"⚔️ {'Tham gia' if vi else 'Join'} (1)"
        self.leave_btn.label = "🏳️ Rời phòng" if vi else "🏳️ Leave"

    @discord.ui.button(label="⚔️ Tham gia (1)", style=discord.ButtonStyle.success)
    async def join_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        vi = is_vietnamese(interaction.guild)
        if interaction.user.id in self.players:
            warn_msg = "⚠️ Bạn đã có tên trong danh sách tham gia rồi!" if vi else "⚠️ You are already in the player list!"
            return await interaction.response.send_message(warn_msg, ephemeral=True)
        if len(self.players) >= 15:
            full_msg = "⚠️ Phòng đấu đã đạt tối đa 15 người!" if vi else "⚠️ Arena lobby is full (max 15 players)!"
            return await interaction.response.send_message(full_msg, ephemeral=True)

        self.players.append(interaction.user.id)
        button.label = f"⚔️ {'Tham gia' if vi else 'Join'} ({len(self.players)})"
        await interaction.response.edit_message(view=self)
        enter_msg = f"🔥 {interaction.user.mention} đã bước vào Đấu Trường Sinh Tử!" if vi else f"🔥 {interaction.user.mention} has entered the Battle Arena!"
        await interaction.followup.send(enter_msg, ephemeral=False)

    @discord.ui.button(label="🏳️ Rời phòng", style=discord.ButtonStyle.secondary)
    async def leave_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        vi = is_vietnamese(interaction.guild)
        if interaction.user.id not in self.players:
            not_in_msg = "Bạn chưa tham gia phòng này!" if vi else "You have not joined this lobby!"
            return await interaction.response.send_message(not_in_msg, ephemeral=True)
        self.players.remove(interaction.user.id)
        self.children[0].label = f"⚔️ {'Tham gia' if vi else 'Join'} ({len(self.players)})"
        await interaction.response.edit_message(view=self)
        leave_msg = "Bạn đã rời khỏi phòng chờ." if vi else "You left the lobby."
        await interaction.followup.send(leave_msg, ephemeral=True)


# --- COG CHÍNH ---
class WordChainGame(commands.Cog, name="Word Chain Game"):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.game_configs: Dict[str, int] = {}
        self.scores: Dict[str, Dict[str, int]] = {}
        self.weekly_scores: Dict[str, Dict[str, int]] = {}
        self.player_stats: Dict[str, Dict[str, dict]] = {}
        self.active_games: Dict[str, dict] = {}
        self.br_games: Dict[str, dict] = {}  # Lưu trạng thái Battle Royale theo guild_id

        self.word_set: Set[str] = set()
        self.word_index: Dict[str, List[str]] = {}
        self.dirty_data = False

        self.load_all_data()
        if not self.auto_save_task.is_running():
            self.auto_save_task.start()
        if not self.weekly_summary_task.is_running():
            self.weekly_summary_task.start()

    async def _safe_add_reaction(self, message: discord.Message, emoji: str):
        try:
            await message.add_reaction(emoji)
        except (discord.NotFound, discord.HTTPException, discord.Forbidden):
            pass

    def cog_unload(self):
        self.auto_save_task.cancel()
        self.weekly_summary_task.cancel()
        for br in self.br_games.values():
            if br.get("timer_task"):
                br["timer_task"].cancel()
        if self.dirty_data:
            self.save_all_state()

    # --- QUẢN LÝ DỮ LIỆU & THỐNG KÊ HỒ SƠ ---
    def _load_json(self, path: str) -> dict:
        if os.path.exists(path):
            with open(path, 'r', encoding='utf-8') as f:
                try:
                    return json.load(f)
                except json.JSONDecodeError:
                    return {}
        return {}

    def _save_json(self, path: str, data: dict):
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=4, ensure_ascii=False)

    def load_all_data(self):
        self.game_configs = self._load_json(WORD_CHAIN_CONFIG_FILE)
        self.active_games = self._load_json(WORD_CHAIN_ACTIVE_GAMES_FILE)
        self.scores = self._load_json(WORD_CHAIN_SCORES_FILE)
        self.weekly_scores = self._load_json(WORD_CHAIN_WEEKLY_SCORES_FILE)
        self.player_stats = self._load_json(WORD_CHAIN_STATS_FILE)
        self.load_word_list()

    def save_all_state(self):
        self._save_json(WORD_CHAIN_ACTIVE_GAMES_FILE, self.active_games)
        self._save_json(WORD_CHAIN_SCORES_FILE, self.scores)
        self._save_json(WORD_CHAIN_WEEKLY_SCORES_FILE, self.weekly_scores)
        self._save_json(WORD_CHAIN_STATS_FILE, self.player_stats)
        self.dirty_data = False

    def get_player_stats(self, guild_id_str: str, user_id_str: str) -> dict:
        guild_stats = self.player_stats.setdefault(guild_id_str, {})
        if user_id_str not in guild_stats:
            guild_stats[user_id_str] = {
                "correct_words": 0,
                "wrong_words": 0,
                "wins": 0,
                "br_wins": 0,
                "max_streak": 0,
                "long_streaks_broken": 0,
                "contributed": 0,
                "word_freq": {},
                "badges": []
            }
        return guild_stats[user_id_str]

    def check_achievements(self, p_stats: dict) -> List[str]:
        """Kiểm tra và mở khóa danh hiệu mới cho người chơi."""
        newly_unlocked = []
        current_badges = p_stats.setdefault("badges", [])

        for key, ach in ACHIEVEMENTS.items():
            if key in current_badges:
                continue
            if key == "bach_phat_bach_trung":
                total = p_stats["correct_words"] + p_stats["wrong_words"]
                acc = (p_stats["correct_words"] / total * 100) if total > 0 else 0
                if p_stats["correct_words"] >= ach["target"] and acc >= 90.0:
                    current_badges.append(key)
                    newly_unlocked.append(ach["name"])
            else:
                if p_stats.get(ach["field"], 0) >= ach["target"]:
                    current_badges.append(key)
                    newly_unlocked.append(ach["name"])

        return newly_unlocked

    def load_word_list(self):
        self.word_set.clear()
        self.word_index.clear()
        if os.path.exists(WORD_LIST_FILE):
            with open(WORD_LIST_FILE, 'r', encoding='utf-8') as f:
                for line in f:
                    phrase = line.strip().lower()
                    words = phrase.split()
                    if len(words) == 2 and phrase not in self.word_set:
                        self.word_set.add(phrase)
                        self.word_index.setdefault(words[0], []).append(phrase)
        else:
            print(f"❌ Lỗi: Không tìm thấy file từ điển '{WORD_LIST_FILE}'.")

    def add_new_word_to_dict(self, phrase: str):
        phrase = phrase.strip().lower()
        words = phrase.split()
        if len(words) == 2 and phrase not in self.word_set:
            self.word_set.add(phrase)
            self.word_index.setdefault(words[0], []).append(phrase)
            os.makedirs(os.path.dirname(WORD_LIST_FILE), exist_ok=True)
            with open(WORD_LIST_FILE, 'a', encoding='utf-8') as f:
                f.write(f"\n{phrase}")

    async def verify_word_via_xkiro(self, phrase: str) -> bool:
        """Xác minh cụm từ tiếng Việt bằng model Mistral qua xKiro."""
        if not XKIRO_API_KEY:
            print("⚠️ Chưa cấu hình XKIRO_API_KEY (hoặc XTROUTER_API_KEY).")
            return False

        prompt = (
            f"Bạn là chuyên gia ngôn ngữ và từ điển tiếng Việt. "
            f"Hãy kiểm tra cụm 2 âm tiết '{phrase}' có phải là từ ghép, từ láy, "
            f"hoặc cụm từ tiếng Việt có nghĩa, đúng chính tả và được sử dụng trong thực tế hay không. "
            f"Chỉ trả lời duy nhất YES nếu đúng hoặc NO nếu sai."
        )
        payload = {
            "model": XKIRO_MODEL,
            "messages": [
                {
                    "role": "system",
                    "content": "Bạn xác minh từ vựng tiếng Việt. Trả lời đúng một từ: YES hoặc NO."
                },
                {"role": "user", "content": prompt}
            ],
            "temperature": 0,
            "max_tokens": 5
        }
        headers = {
            "Authorization": f"Bearer {XKIRO_API_KEY}",
            "Content-Type": "application/json"
        }

        try:
            timeout = aiohttp.ClientTimeout(total=15)
            async with aiohttp.ClientSession(timeout=timeout) as session:
                async with session.post(
                    XKIRO_API_URL, headers=headers, json=payload
                ) as resp:
                    if resp.status != 200:
                        body = (await resp.text())[:500]
                        print(f"⚠️ xKiro API lỗi HTTP {resp.status}: {body}")
                        return False

                    data = await resp.json()
                    choices = data.get("choices", [])
                    if not choices:
                        print("⚠️ xKiro API không trả về choices.")
                        return False

                    content = choices[0].get("message", {}).get("content", "")
                    answer = str(content).strip().upper().strip(" .!`\n\r")
                    if answer == "YES":
                        self.add_new_word_to_dict(phrase)
                        return True
                    return False
        except asyncio.TimeoutError:
            print("⚠️ xKiro API hết thời gian chờ khi xác minh từ.")
        except aiohttp.ClientError as exc:
            print(f"⚠️ Không thể kết nối xKiro API: {exc}")
        except (ValueError, KeyError, TypeError) as exc:
            print(f"⚠️ Phản hồi xKiro API không hợp lệ: {exc}")
        return False

    def has_next_word(self, word_to_check: str, used_words: Optional[dict] = None, max_use: int = 3) -> bool:
        last_syllable = word_to_check.split()[-1]
        candidates = self.word_index.get(last_syllable, [])
        if not used_words:
            return len(candidates) > 0
        return any(used_words.get(w, 0) < max_use for w in candidates)

    def get_random_valid_start_word(self) -> str:
        valid_pool = [w for w in self.word_set if self.has_next_word(w)]
        if valid_pool:
            return random.choice(valid_pool)
        return random.choice(list(self.word_set)) if self.word_set else "bắt đầu"

    def _reset_new_round(self, guild_id_str: str, channel_id: int, pve_mode: bool = False) -> str:
        new_start_word = self.get_random_valid_start_word()
        self.active_games[guild_id_str] = {
            "current_word": new_start_word,
            "last_player_id": self.bot.user.id,
            "channel_id": channel_id,
            "used_words": {new_start_word: 1},
            "streak": 1,
            "shields": 0,
            "pve_mode": pve_mode,
            "golden_letter": None
        }
        self.dirty_data = True
        return new_start_word

    # --- LOGIC ĐẤU TRƯỜNG SINH TỬ (BATTLE ROYALE) ---
    async def _advance_br_turn(self, guild_id_str: str, channel: discord.TextChannel):
        br = self.br_games.get(guild_id_str)
        if not br or not br.get("active"):
            return

        if br.get("timer_task"):
            br["timer_task"].cancel()

        # Kiểm tra nếu chỉ còn 1 người sống sót -> Chiến thắng!
        if len(br["players"]) == 1:
            winner_id = br["players"][0]
            w_str = str(winner_id)
            pot = br["pot"]

            self.scores.setdefault(guild_id_str, {})[w_str] = self.scores.get(guild_id_str, {}).get(w_str, 0) + pot
            self.weekly_scores.setdefault(guild_id_str, {})[w_str] = self.weekly_scores.get(guild_id_str, {}).get(w_str, 0) + pot

            p_stats = self.get_player_stats(guild_id_str, w_str)
            p_stats["br_wins"] += 1
            unlocked = self.check_achievements(p_stats)
            self.dirty_data = True

            del self.br_games[guild_id_str]

            ach_text = f"\n🏅 Mở khóa danh hiệu: **{', '.join(unlocked)}**!" if unlocked else ""
            embed = discord.Embed(
                title="👑 NHÀ VÔ ĐỊCH ĐẤU TRƯỜNG SINH TỬ 👑",
                description=(
                    f"🎉 Chúc mừng <@{winner_id}> đã trở thành người sống sót cuối cùng!\n"
                    f"💰 Phần thưởng Jackpot: **`+{pot} điểm`**{ach_text}\n\n"
                    f"*(Chế độ nối từ thông thường của kênh đã được khôi phục)*"
                ),
                color=discord.Color.gold()
            )
            await channel.send(embed=embed)
            return

        if len(br["players"]) == 0:
            del self.br_games[guild_id_str]
            await channel.send("⚠️ Đấu trường kết thúc do không còn người chơi nào trụ lại!")
            return

        br["turn_idx"] = br["turn_idx"] % len(br["players"])
        current_player_id = br["players"][br["turn_idx"]]
        curr_word = br["current_word"]
        target_syl = curr_word.split()[-1].upper()

        await channel.send(
            f"⚔️ **Lượt của <@{current_player_id}>!** (⏳ `15 giây`)\n"
            f"👉 Từ hiện tại: **`{curr_word.upper()}`** — Hãy nối tiếp bằng chữ **`{target_syl}`**!"
        )
        br["timer_task"] = self.bot.loop.create_task(
            self._br_turn_timeout(guild_id_str, channel, current_player_id)
        )

    async def _br_turn_timeout(self, guild_id_str: str, channel: discord.TextChannel, expected_player_id: int):
        try:
            await asyncio.sleep(15)
            br = self.br_games.get(guild_id_str)
            if not br or not br.get("active"):
                return
            if br["players"][br["turn_idx"]] != expected_player_id:
                return

            br["players"].remove(expected_player_id)
            await channel.send(f"⏰ **HẾT GIỜ!** <@{expected_player_id}> đã quá 15 giây suy nghĩ và bị loại khỏi Đấu Trường! (Còn `{len(br['players'])}` người)")
            await self._advance_br_turn(guild_id_str, channel)
        except asyncio.CancelledError:
            pass

    async def _handle_br_message(self, message: discord.Message, guild_id_str: str, br: dict):
        if not br.get("active"):
            return

        raw_content = message.content.strip()
        if raw_content.startswith((".", "!", "?", "/")):
            return

        current_player_id = br["players"][br["turn_idx"]]
        # Chỉ xử lý tin nhắn của người đang đến lượt
        if message.author.id != current_player_id:
            return

        new_phrase = raw_content.lower()
        words = new_phrase.split()
        if len(words) != 2:
            return

        if br.get("timer_task"):
            br["timer_task"].cancel()

        used_words = br["used_words"]
        last_syllable = br["current_word"].split()[-1]
        elim_reason = None

        if not is_valid_chain(br["current_word"], new_phrase):
            elim_reason = f"Nối sai chữ đầu (phải bắt đầu bằng `{last_syllable.upper()}`)"
        elif new_phrase in used_words:
            elim_reason = f"Từ `{new_phrase}` đã được sử dụng trong trận Sinh Tử này"
        elif new_phrase not in self.word_set and not await self.verify_word_via_xkiro(new_phrase):
            elim_reason = f"Từ `{new_phrase}` không có trong từ điển tiếng Việt"

        if elim_reason:
            await self._safe_add_reaction(message, "💀")
            br["players"].remove(current_player_id)
            await message.channel.send(
                f"💀 **BỊ LOẠI!** {message.author.mention} đã trả lời sai ({elim_reason}) và rời khỏi cuộc chơi! (Còn `{len(br['players'])}` người)"
            )
            await self._advance_br_turn(guild_id_str, message.channel)
            return

        # Nối đúng trong chế độ Sinh Tử
        await self._safe_add_reaction(message, "⚔️")
        used_words.add(new_phrase)
        br["current_word"] = new_phrase

        # Nếu từ vừa nối làm bí từ hoàn toàn, đổi từ ngẫu nhiên mới cho người kế tiếp để vòng đấu không bị kẹt
        if not self.has_next_word(new_phrase, {w: 3 for w in used_words}):
            new_w = self.get_random_valid_start_word()
            br["current_word"] = new_w
            used_words.add(new_w)
            await message.channel.send(f"🔥 {message.author.mention} đã khóa chết từ `{new_phrase}`! Bot tự động đổi từ mới cho vòng đấu: **`{new_w.upper()}`**")

        br["turn_idx"] = (br["turn_idx"] + 1) % len(br["players"])
        await self._advance_br_turn(guild_id_str, message.channel)

    # --- CÁC TÁC VỤ CHẠY NGẦM ---
    @tasks.loop(minutes=2)
    async def auto_save_task(self):
        if self.dirty_data:
            self.save_all_state()

    @tasks.loop(time=time(hour=0, minute=0, tzinfo=VN_TZ))
    async def weekly_summary_task(self):
        if datetime.now(VN_TZ).weekday() != 0:
            return

        for guild_id_str, guild_weekly in list(self.weekly_scores.items()):
            if not guild_weekly:
                continue

            channel_id = self.game_configs.get(guild_id_str)
            channel = self.bot.get_channel(channel_id) if channel_id else None
            if not channel:
                continue

            sorted_players = sorted(guild_weekly.items(), key=lambda item: item[1], reverse=True)
            desc = "🎉 **Chúc mừng các cao thủ nối từ tuần qua!** 🎉\n\n"
            medals = ["🥇", "🥈", "🥉"]
            for i, (user_id, score) in enumerate(sorted_players[:10]):
                prefix_rank = medals[i] if i < 3 else f"**#{i+1}**"
                desc += f"{prefix_rank} <@{user_id}> — `{score}` điểm\n"

            current_game = self.active_games.get(guild_id_str)
            if current_game:
                curr_w = current_game["current_word"]
                desc += f"\n🔥 *Ván đấu hiện tại vẫn đang tiếp diễn! Từ hiện tại là: **`{curr_w.upper()}`** (nối tiếp bằng chữ **`{curr_w.split()[-1].upper()}`**)*"

            embed = discord.Embed(
                title="🏆 TỔNG KẾT BẢNG XẾP HẠNG TUẦN - NỐI TỪ 🏆",
                description=desc,
                color=discord.Color.gold()
            )
            try:
                await channel.send(embed=embed)
            except discord.Forbidden:
                pass

        self.weekly_scores.clear()
        self._save_json(WORD_CHAIN_WEEKLY_SCORES_FILE, self.weekly_scores)

    # --- CÁC LỆNH ĐIỀU KHIỂN ---
    @commands.hybrid_group(name="wordchain", aliases=["wc"], description="Game nối chữ 2 từ tiếng Việt.")
    async def wordchain(self, ctx: commands.Context):
        if ctx.invoked_subcommand is None:
            await self.help_command(ctx)

    @wordchain.command(name="help", description="Xem bảng hướng dẫn chi tiết, luật chơi và danh sách lệnh.")
    async def help_command(self, ctx: commands.Context):
        prefix = ctx.prefix or "/"
        embed = discord.Embed(
            title="🎮 CẨM NANG TRÒ CHƠI NỐI TỪ TIẾNG VIỆT 🎮",
            description=(
                "Chào mừng bạn đến với **Word Chain Game** tích hợp AI xKiro `mistralai/mistral-large-4-0`!\n\n"
                "🔹 **Chế độ Thường:** Nối từ tự do, săn **Từ Khóa Vàng (x3 điểm)**, tích lũy **Khiên Bảo Vệ** và đua Top Tuần.\n"
                "🔹 **Đấu Trường Sinh Tử (`/wc br`):** Vòng tròn sinh tồn 15 giây/lượt, người trụ lại cuối cùng ăn trọn quỹ thưởng Jackpot.\n"
                "🔹 **Hồ Sơ & Danh Hiệu (`/wc profile`):** Mở khóa 6 danh hiệu độc quyền và theo dõi tỷ lệ chính xác của bạn.\n\n"
                "👇 **Hãy chọn danh mục ở menu bên dưới để xem chi tiết:**"
            ),
            color=discord.Color.blurple()
        )
        embed.set_footer(text=f"Sử dụng lệnh {prefix}wc start để bắt đầu chơi ngay!")
        await ctx.send(embed=embed, view=HelpView(prefix))

    @wordchain.command(name="profile", description="Xem hồ sơ thống kê cá nhân và các danh hiệu đã đạt được.")
    @app_commands.describe(thanh_vien="[Tùy chọn] Xem hồ sơ của người chơi khác.")
    async def profile_command(self, ctx: commands.Context, thanh_vien: Optional[discord.Member] = None):
        target = thanh_vien
        if not target and getattr(ctx, "message", None) and ctx.message.mentions:
            target = ctx.message.mentions[0]
        if target and target.id != ctx.author.id:
            from Checks_vi.mod import OWNER_ID
            is_owner = (ctx.author.id in (1144785664458637394, OWNER_ID) or await ctx.bot.is_owner(ctx.author))
            if not is_owner:
                return await ctx.send("❌ Bạn chỉ có thể xem hồ sơ nối từ của chính mình! Không được phép xem của người khác.", ephemeral=True)
        target = target or ctx.author
        guild_id_str = str(ctx.guild.id)
        user_id_str = str(target.id)

        p_stats = self.get_player_stats(guild_id_str, user_id_str)
        self.check_achievements(p_stats)

        total_score = self.scores.get(guild_id_str, {}).get(user_id_str, 0)
        weekly_score = self.weekly_scores.get(guild_id_str, {}).get(user_id_str, 0)

        # Tính thứ hạng hiện tại trong server
        guild_scores = self.scores.get(guild_id_str, {})
        sorted_ids = [k for k, _ in sorted(guild_scores.items(), key=lambda item: item[1], reverse=True)]
        rank_str = f"#{sorted_ids.index(user_id_str) + 1}/{len(sorted_ids)}" if user_id_str in sorted_ids else "Chưa xếp hạng"

        # Tính tỷ lệ chính xác & thanh tiến trình
        correct = p_stats["correct_words"]
        wrong = p_stats["wrong_words"]
        total_attempts = correct + wrong
        acc = (correct / total_attempts * 100) if total_attempts > 0 else 0.0
        filled_bars = int(round(acc / 10))
        acc_bar = "🟩" * filled_bars + "⬛" * (10 - filled_bars)

        # Tìm từ yêu thích nhất
        word_freq = p_stats.get("word_freq", {})
        if word_freq:
            fav_word, fav_count = max(word_freq.items(), key=lambda x: x[1])
            fav_str = f"`{fav_word}` ({fav_count} lần)"
        else:
            fav_str = "Chưa có dữ liệu"

        # Hiển thị danh hiệu
        badges = p_stats.get("badges", [])
        if badges:
            badge_display = "\n".join([f"• **{ACHIEVEMENTS[b]['name']}** — *{ACHIEVEMENTS[b]['desc']}*" for b in badges if b in ACHIEVEMENTS])
        else:
            badge_display = "*(Chưa mở khóa danh hiệu nào — Hãy tiếp tục nối từ nhé!)*"

        embed = discord.Embed(
            title=f"🪪 HỒ SƠ NỐI TỪ: {target.display_name.upper()}",
            color=discord.Color.teal()
        )
        embed.set_thumbnail(url=target.display_avatar.url)
        embed.add_field(name="🏆 Thứ hạng & Điểm số", value=f"• Hạng: **`{rank_str}`**\n• Điểm Tổng: **`{total_score}`**\n• Điểm Tuần: **`{weekly_score}`**", inline=True)
        embed.add_field(name="📊 Chiến tích", value=f"• Khóa mõm (Bí từ): **`{p_stats['wins']}`** lần\n• Thắng Sinh Tử (BR): **`{p_stats['br_wins']}`** lần\n• Chuỗi cao nhất: **`{p_stats['max_streak']}`** từ", inline=True)
        embed.add_field(name="📚 Đóng góp & Phá chuỗi", value=f"• Đóng góp từ: **`{p_stats['contributed']}`** từ\n• Phá chuỗi >=25: **`{p_stats['long_streaks_broken']}`** lần\n• Từ tủ: {fav_str}", inline=False)
        embed.add_field(name=f"🎯 Độ chính xác: {acc:.1f}% ({correct} Đúng / {wrong} Sai)", value=f"{acc_bar}", inline=False)
        embed.add_field(name=f"🎖️ Danh hiệu đạt được ({len(badges)}/{len(ACHIEVEMENTS)})", value=badge_display, inline=False)

        await ctx.send(embed=embed)

    @wordchain.command(name="br", description="Mở phòng Đấu Trường Sinh Tử (Battle Royale - Loại trực tiếp 15s/lượt).")
    async def battle_royale_command(self, ctx: commands.Context):
        guild_id_str = str(ctx.guild.id)
        game_channel_id = self.game_configs.get(guild_id_str)
        if not game_channel_id:
            return await ctx.send(t(ctx.guild, "WC_SETUP_NOT_SET", prefix=ctx.prefix), ephemeral=True)

        if guild_id_str in self.br_games:
            return await ctx.send("⚔️ Một trận Đấu Trường Sinh Tử đang diễn ra hoặc đang mở phòng chờ rồi!", ephemeral=True)

        game_channel = self.bot.get_channel(game_channel_id)
        if not game_channel:
            return await ctx.send(t(ctx.guild, "WC_CHANNEL_NOT_EXIST"), ephemeral=True)

        self.br_games[guild_id_str] = {"active": False}
        view = BRLobbyView(ctx.author)

        embed = discord.Embed(
            title="⚔️ ĐẤU TRƯỜNG SINH TỬ (BATTLE ROYALE) - SẢNH CHỜ ⚔️",
            description=(
                f"🔥 {ctx.author.mention} vừa triệu hồi Đấu Trường Sinh Tử!\n\n"
                "• **Luật chơi:** Bot gọi tên từng người theo thứ tự vòng tròn. Bạn có **15 giây** để nối từ.\n"
                "• **Loại trực tiếp:** Quá 15 giây hoặc nối sai sẽ bị loại ngay lập tức!\n"
                "• **Giải thưởng Jackpot:** `Số người tham gia x 5 điểm` dành trọn cho người sống sót cuối cùng!\n\n"
                "⏳ **Trận đấu sẽ tự động bắt đầu sau `45 giây` nữa! Hãy bấm nút bên dưới để tham gia:**"
            ),
            color=discord.Color.orange()
        )
        lobby_msg = await game_channel.send(embed=embed, view=view)
        if ctx.channel.id != game_channel.id:
            await ctx.send(f"✅ Đã mở sảnh chờ Đấu Trường Sinh Tử tại {game_channel.mention}!", ephemeral=True)

        await asyncio.sleep(45)
        for item in view.children:
            item.disabled = True
        try:
            await lobby_msg.edit(view=view)
        except discord.NotFound:
            pass

        if len(view.players) < 2:
            del self.br_games[guild_id_str]
            return await game_channel.send("⚠️ Không đủ người chơi (tối thiểu 2 người). Đấu Trường Sinh Tử đã bị hủy!")

        random.shuffle(view.players)
        start_word = self.get_random_valid_start_word()
        pot = len(view.players) * 5

        self.br_games[guild_id_str] = {
            "active": True,
            "channel_id": game_channel.id,
            "players": view.players,
            "turn_idx": 0,
            "current_word": start_word,
            "used_words": {start_word},
            "pot": pot,
            "timer_task": None
        }

        order_mentions = " ➔ ".join([f"<@{uid}>" for uid in view.players])
        start_embed = discord.Embed(
            title="🔔 ĐẤU TRƯỜNG SINH TỬ CHÍNH THỨC BẮT ĐẦU! 🔔",
            description=(
                f"👥 **Số chiến binh:** `{len(view.players)} người` | 💰 **Quỹ thưởng Jackpot:** `{pot} điểm`\n"
                f"🔄 **Thứ tự vòng quay:** {order_mentions}\n\n"
                f"🎯 Từ khởi đầu là: **`{start_word.upper()}`**"
            ),
            color=discord.Color.red()
        )
        await game_channel.send(embed=start_embed)
        await self._advance_br_turn(guild_id_str, game_channel)

    @wordchain.command(name="setup", description="Cài đặt kênh chơi game nối chữ (Admin).")
    @commands.has_permissions(administrator=True)
    async def setup_channel(self, ctx: commands.Context, channel: discord.TextChannel):
        guild_id_str = str(ctx.guild.id)
        self.game_configs[guild_id_str] = channel.id
        self._save_json(WORD_CHAIN_CONFIG_FILE, self.game_configs)
        await ctx.send(t(ctx.guild, "WC_SETUP_DONE", mention=channel.mention), ephemeral=True)

    @wordchain.command(name="start", description="Bắt đầu một game nối chữ mới.")
    @app_commands.describe(
        tu_bat_dau="[Tùy chọn] Cụm từ 2 từ để bắt đầu game.",
        dau_voi_bot="Bật chế độ chơi cùng Bot (PvE) hay không."
    )
    async def start_game(self, ctx: commands.Context, tu_bat_dau: Optional[str] = None, dau_voi_bot: bool = False):
        guild_id_str = str(ctx.guild.id)
        game_channel_id = self.game_configs.get(guild_id_str)

        if not game_channel_id:
            return await ctx.send(t(ctx.guild, "WC_SETUP_NOT_SET", prefix=ctx.prefix), ephemeral=True)

        game_channel = self.bot.get_channel(game_channel_id)
        if not game_channel:
            return await ctx.send(t(ctx.guild, "WC_CHANNEL_NOT_EXIST"), ephemeral=True)

        if not self.word_set:
            return await ctx.send(t(ctx.guild, "WC_NO_WORDLIST"), ephemeral=True)

        last_player_id = self.bot.user.id

        if tu_bat_dau:
            start_word = tu_bat_dau.strip().lower()
            if len(start_word.split()) != 2:
                return await ctx.send(t(ctx.guild, "WC_NEED_TWO_WORDS"), ephemeral=True)
            if start_word not in self.word_set and not await self.verify_word_via_xkiro(start_word):
                return await ctx.send(t(ctx.guild, "WC_NOT_IN_DICT", word=start_word), ephemeral=True)
            if not self.has_next_word(start_word):
                return await ctx.send(t(ctx.guild, "WC_DEAD_END", word=start_word), ephemeral=True)
            last_player_id = ctx.author.id if not dau_voi_bot else self.bot.user.id
        else:
            start_word = self.get_random_valid_start_word()

        self.active_games[guild_id_str] = {
            "current_word": start_word,
            "last_player_id": last_player_id,
            "channel_id": game_channel.id,
            "used_words": {start_word: 1},
            "streak": 1,
            "shields": 0,
            "pve_mode": dau_voi_bot,
            "golden_letter": None
        }
        self.save_all_state()

        mode_str = "\n🤖 **Chế độ Đấu với Bot (PvE): Đang BẬT**" if dau_voi_bot else ""
        embed = discord.Embed(
            title=t(game_channel.guild, "WC_NEW_GAME_TITLE"),
            description=t(game_channel.guild, "WC_NEW_GAME_DESC", word=start_word, syllable=start_word.split()[-1].upper()) + mode_str,
            color=discord.Color.green()
        )
        await game_channel.send(embed=embed)
        await ctx.send(t(ctx.guild, "WC_STARTED", mention=game_channel.mention), ephemeral=True)

    @wordchain.command(name="botmode", description="Bật/Tắt chế độ Bot tự động nối từ cùng người chơi (PvE).")
    async def toggle_bot_mode(self, ctx: commands.Context):
        guild_id_str = str(ctx.guild.id)
        game_state = self.active_games.get(guild_id_str)
        if not game_state:
            return await ctx.send(t(ctx.guild, "WC_NO_GAME"), ephemeral=True)

        current_mode = game_state.get("pve_mode", False)
        game_state["pve_mode"] = not current_mode
        self.dirty_data = True

        status = "🟢 **BẬT**" if game_state["pve_mode"] else "🔴 **TẮT**"
        await ctx.send(f"🤖 Chế độ Đấu với Bot (PvE) đã được {status}!")

    @wordchain.command(name="shield", description="Mua Khiên Bảo Vệ chuỗi hiện tại (Giá: 5 điểm) để tránh đứt chuỗi khi có người nối sai.")
    async def buy_shield(self, ctx: commands.Context):
        guild_id_str = str(ctx.guild.id)
        user_id_str = str(ctx.author.id)
        game_state = self.active_games.get(guild_id_str)

        if not game_state:
            return await ctx.send(t(ctx.guild, "WC_NO_GAME"), ephemeral=True)

        if game_state.get("shields", 0) >= 3:
            return await ctx.send("🛡️ Phòng chơi đã đạt tối đa `3 Khiên Bảo Vệ`!", ephemeral=True)

        user_score = self.scores.get(guild_id_str, {}).get(user_id_str, 0)
        if user_score < 5:
            return await ctx.send("❌ Bạn cần ít nhất `5 điểm` tích lũy để mua Khiên Bảo Vệ!", ephemeral=True)

        self.scores[guild_id_str][user_id_str] -= 5
        game_state["shields"] = game_state.get("shields", 0) + 1
        self.dirty_data = True

        await ctx.send(
            f"🛡️ {ctx.author.mention} đã dùng 5 điểm mua **1 Khiên Bảo Vệ** cho phòng! "
            f"(Hiện có: `{game_state['shields']}/3` Khiên - Sẽ tự động chặn 1 lần nối sai để giữ chuỗi `{game_state.get('streak', 1)}` từ)."
        )

    @wordchain.command(name="contribute", description="Đóng góp từ vựng mới vào từ điển của game.")
    @app_commands.describe(tu_moi="Cụm từ 2 âm tiết bạn muốn đóng góp.")
    async def contribute_word(self, ctx: commands.Context, *, tu_moi: str):
        tu_moi = tu_moi.strip().lower()
        guild_id_str = str(ctx.guild.id)
        user_id_str = str(ctx.author.id)

        if len(tu_moi.split()) != 2:
            return await ctx.send(t(ctx.guild, "WC_NEED_TWO_WORDS"), ephemeral=True)
        if tu_moi in self.word_set:
            return await ctx.send(f"✅ Từ **`{tu_moi}`** đã có sẵn trong từ điển rồi!", ephemeral=True)

        await ctx.defer()
        if await self.verify_word_via_xkiro(tu_moi):
            p_stats = self.get_player_stats(guild_id_str, user_id_str)
            p_stats["contributed"] += 1
            unlocked = self.check_achievements(p_stats)
            self.dirty_data = True
            ach_msg = f"\n🏅 Bạn vừa mở khóa danh hiệu: **{', '.join(unlocked)}**!" if unlocked else ""
            return await ctx.send(f"✨ AI xKiro (Mistral Large 4) đã xác nhận **`{tu_moi}`** là từ hợp lệ và tự động thêm vào từ điển! (+1 đóng góp){ach_msg}")

        view = WordContributeView(self, tu_moi, ctx.author.id, guild_id_str)
        await ctx.send(
            f"🤔 Từ **`{tu_moi}`** chưa có trong từ điển tiêu chuẩn. Bạn có muốn gửi đề xuất để Admin server phê duyệt thủ công không?",
            view=view
        )

    @wordchain.command(name="stop", description="Dừng game nối chữ hoặc trận Sinh Tử hiện tại (Admin).")
    @commands.has_permissions(administrator=True)
    async def stop_game(self, ctx: commands.Context):
        guild_id_str = str(ctx.guild.id)
        stopped_any = False

        if guild_id_str in self.br_games:
            if self.br_games[guild_id_str].get("timer_task"):
                self.br_games[guild_id_str]["timer_task"].cancel()
            del self.br_games[guild_id_str]
            stopped_any = True

        if guild_id_str in self.active_games:
            del self.active_games[guild_id_str]
            self.save_all_state()
            stopped_any = True

        if not stopped_any:
            return await ctx.send(t(ctx.guild, "WC_NO_GAME"), ephemeral=True)

        await ctx.send(t(ctx.guild, "WC_STOPPED"))

    @wordchain.command(name="hint", description="Dùng 2 điểm để mua gợi ý cho từ hiện tại.")
    async def hint_word(self, ctx: commands.Context):
        guild_id_str = str(ctx.guild.id)
        user_id_str = str(ctx.author.id)
        game_state = self.active_games.get(guild_id_str)

        if not game_state:
            return await ctx.send(t(ctx.guild, "WC_NO_GAME"), ephemeral=True)

        user_score = self.scores.get(guild_id_str, {}).get(user_id_str, 0)
        if user_score < 2:
            return await ctx.send("❌ Bạn cần ít nhất `2 điểm` tích lũy để mua gợi ý!", ephemeral=True)

        last_syllable = game_state["current_word"].split()[-1]
        used_words = game_state.get("used_words", {})
        candidates = [w for w in self.word_index.get(last_syllable, []) if used_words.get(w, 0) < 3]

        if not candidates:
            return await ctx.send("⚠️ Hiện không tìm thấy từ gợi ý nào khả dụng trong từ điển!", ephemeral=True)

        self.scores[guild_id_str][user_id_str] -= 2
        self.dirty_data = True

        secret_word = random.choice(candidates)
        second_part = secret_word.split()[1]
        masked = second_part[0] + "•" * (len(second_part) - 1)

        await ctx.send(
            f"💡 **Gợi ý cho bạn** (-2 điểm): `{last_syllable} {masked}` *(hoặc thử: `{secret_word}`)*",
            ephemeral=True
        )

    @wordchain.command(name="timtu", description="[Owner] Tra cứu một từ trong từ điển của game.")
    @commands.is_owner()
    async def find_word(self, ctx: commands.Context, *, keyword: str):
        await ctx.defer(ephemeral=True)
        keyword = keyword.strip().lower()

        is_exact_match = keyword in self.word_set
        if not is_exact_match and len(keyword.split()) == 2:
            is_exact_match = await self.verify_word_via_xkiro(keyword)

        status_text = t(ctx.guild, "WC_FIND_HAS") if is_exact_match else t(ctx.guild, "WC_FIND_NOT_HAS")

        first_word = keyword.split()[0]
        candidates = self.word_index.get(first_word, [])
        suggestions = sorted([w for w in candidates if w.startswith(keyword)])
        total_found = len(suggestions)

        embed = discord.Embed(title=t(ctx.guild, "WC_FIND_TITLE", keyword=keyword), color=discord.Color.blue())
        embed.add_field(name=t(ctx.guild, "WC_FIND_STATUS"), value=status_text, inline=False)

        if total_found > 0:
            limited = suggestions[:20]
            suggest_format = ", ".join([f"`{w}`" for w in limited])
            note = f"\n*(Hiển thị {len(limited)}/{total_found} từ gợi ý)*" if total_found > 20 else ""
            embed.add_field(name=t(ctx.guild, "WC_FIND_SUGGEST"), value=f"{suggest_format}{note}", inline=False)
        else:
            embed.add_field(name=t(ctx.guild, "WC_FIND_LABEL_SUGGEST"), value=t(ctx.guild, "WC_FIND_NO_SUGGEST", keyword=keyword), inline=False)

        await ctx.send(embed=embed, ephemeral=True)

    @wordchain.command(name="rank", description="Xem bảng xếp hạng game nối chữ (Tuần & Tổng).")
    @app_commands.describe(loai="Chọn xem bảng xếp hạng Tuần hiện tại hoặc Tổng tất cả")
    @app_commands.choices(loai=[
        app_commands.Choice(name="Bảng xếp hạng Tuần", value="weekly"),
        app_commands.Choice(name="Bảng xếp hạng Tổng", value="all")
    ])
    async def rank(self, ctx: commands.Context, loai: str = "all"):
        guild_id_str = str(ctx.guild.id)
        target_scores = self.weekly_scores.get(guild_id_str, {}) if loai == "weekly" else self.scores.get(guild_id_str, {})

        if not target_scores:
            return await ctx.send(t(ctx.guild, "WC_RANK_EMPTY"), ephemeral=True)

        sorted_players = sorted(target_scores.items(), key=lambda item: item[1], reverse=True)
        description = ""
        for i, (user_id, score) in enumerate(sorted_players[:10]):
            p_stats = self.get_player_stats(guild_id_str, user_id)
            badges = p_stats.get("badges", [])
            # Hiển thị icon của danh hiệu nổi bật nhất bên cạnh tên
            badge_icons = "".join([ACHIEVEMENTS[b]["name"].split()[0] for b in badges if b in ACHIEVEMENTS])
            badge_str = f" {badge_icons}" if badge_icons else ""
            description += f"**#{i+1}**: <@{user_id}>{badge_str} — `{score}` điểm\n"

        title = f"📅 BXH Tuần - {ctx.guild.name}" if loai == "weekly" else t(ctx.guild, "WC_RANK_TITLE", name=ctx.guild.name)
        embed = discord.Embed(title=title, description=description, color=discord.Color.gold())
        await ctx.send(embed=embed)

    # --- XỬ LÝ LƯỢT CHƠI ---
    @commands.Cog.listener("on_message")
    async def on_message_game_turn(self, message: discord.Message):
        if message.author.bot or not message.guild:
            return

        guild_id_str = str(message.guild.id)

        # Ưu tiên kiểm tra nếu kênh đang diễn ra trận Đấu Trường Sinh Tử (Battle Royale)
        br = self.br_games.get(guild_id_str)
        if br and br.get("active") and message.channel.id == br.get("channel_id"):
            await self._handle_br_message(message, guild_id_str, br)
            return

        game_state = self.active_games.get(guild_id_str)
        if not game_state or message.channel.id != game_state["channel_id"]:
            return

        raw_content = message.content.strip()
        if raw_content.startswith((".", "!", "?", "/")):
            return

        new_phrase = raw_content.lower()
        prefix = await self.bot.get_prefix(message)
        if (isinstance(prefix, str) and new_phrase.startswith(prefix)) or \
           (isinstance(prefix, (list, tuple)) and any(new_phrase.startswith(p) for p in prefix)):
            return

        words = new_phrase.split()
        if len(words) != 2:
            return

        if message.author.id == game_state["last_player_id"]:
            try:
                await message.delete()
            except (discord.Forbidden, discord.NotFound):
                pass
            await message.channel.send(t(message.guild, "WC_SELF_SPAM", mention=message.author.mention), delete_after=4)
            return

        user_id_str = str(message.author.id)
        p_stats = self.get_player_stats(guild_id_str, user_id_str)

        error_reason = None
        is_not_in_dict = False
        word_counts = game_state.get("used_words", {})
        last_syllable = game_state["current_word"].split()[-1]

        if not is_valid_chain(game_state["current_word"], new_phrase):
            error_reason = t(message.guild, "WC_ERROR_WRONG_CHAIN", syllable=last_syllable.upper())
        elif word_counts.get(new_phrase, 0) >= 3:
            error_reason = t(message.guild, "WC_ERROR_USED_MAX", word=new_phrase)
        elif new_phrase not in self.word_set:
            is_valid_api = await self.verify_word_via_xkiro(new_phrase)
            if not is_valid_api:
                error_reason = t(message.guild, "WC_ERROR_NOT_IN_DICT", word=new_phrase)
                is_not_in_dict = True

        # --- XỬ LÝ KHI NỐI SAI ---
        if error_reason:
            p_stats["wrong_words"] += 1
            shields = game_state.get("shields", 0)
            view = WordContributeView(self, new_phrase, message.author.id, guild_id_str) if is_not_in_dict else None

            if shields > 0:
                game_state["shields"] -= 1
                self.dirty_data = True
                await self._safe_add_reaction(message, "🛡️")
                await message.channel.send(
                    f"🛡️ **KHIÊN BẢO VỆ ĐÃ KÍCH HOẠT!** {message.author.mention} vừa nối sai ({error_reason}), "
                    f"nhưng phòng đã dùng 1 Khiên để giữ chuỗi **{game_state.get('streak', 1)} từ**! (Còn `{game_state['shields']}` Khiên)\n"
                    f"👉 Từ hiện tại vẫn là: **`{game_state['current_word'].upper()}`** (nối tiếp bằng chữ **`{last_syllable.upper()}`**)",
                    view=view
                )
                return

            # Ghi nhận nếu làm đứt chuỗi >= 25 từ
            if game_state.get("streak", 1) >= 25:
                p_stats["long_streaks_broken"] += 1
            unlocked = self.check_achievements(p_stats)

            await self._safe_add_reaction(message, "❌")
            embed_error = discord.Embed(
                title=t(message.guild, "WC_BROKEN_TITLE"),
                description=t(message.guild, "WC_BROKEN_DESC", mention=message.author.mention, reason=error_reason),
                color=discord.Color.red()
            )
            await message.channel.send(embed=embed_error, view=view)
            if unlocked:
                await message.channel.send(f"🏅 {message.author.mention} vừa mở khóa danh hiệu: **{', '.join(unlocked)}**!")

            pve_mode = game_state.get("pve_mode", False)
            new_start_word = self._reset_new_round(guild_id_str, game_state["channel_id"], pve_mode=pve_mode)
            embed_new = discord.Embed(
                title=t(message.guild, "WC_AUTO_NEW_TITLE"),
                description=t(message.guild, "WC_AUTO_NEW_DESC", word=new_start_word.upper(), syllable=new_start_word.split()[-1].upper()),
                color=discord.Color.purple()
            )
            await message.channel.send(embed=embed_new)
            return

        # --- XỬ LÝ KHI NỐI ĐÚNG ---
        await self._safe_add_reaction(message, "<:Like:1519266417994764400>")

        streak = game_state.get("streak", 1) + 1
        game_state["streak"] = streak

        # Cập nhật thống kê cá nhân
        p_stats["correct_words"] += 1
        if streak > p_stats["max_streak"]:
            p_stats["max_streak"] = streak
        w_freq = p_stats.setdefault("word_freq", {})
        w_freq[new_phrase] = w_freq.get(new_phrase, 0) + 1

        golden_letter = game_state.get("golden_letter")
        golden_bonus = 0
        if golden_letter and words[1].startswith(golden_letter):
            golden_bonus = 2
            await self._safe_add_reaction(message, "🌟")
        game_state["golden_letter"] = None

        streak_bonus = 1 if streak % 15 == 0 else 0
        shield_reward_msg = ""
        if streak % 30 == 0 and game_state.get("shields", 0) < 3:
            game_state["shields"] = game_state.get("shields", 0) + 1
            shield_reward_msg = f" và **+1 Khiên Bảo Vệ 🛡️** (Tổng: `{game_state['shields']}/3`)"

        points_earned = 1 + golden_bonus + streak_bonus

        self.scores.setdefault(guild_id_str, {})[user_id_str] = self.scores.get(guild_id_str, {}).get(user_id_str, 0) + points_earned
        self.weekly_scores.setdefault(guild_id_str, {})[user_id_str] = self.weekly_scores.get(guild_id_str, {}).get(user_id_str, 0) + points_earned

        game_state["current_word"] = new_phrase
        game_state["last_player_id"] = message.author.id
        word_counts[new_phrase] = word_counts.get(new_phrase, 0) + 1
        game_state["used_words"] = word_counts
        self.dirty_data = True

        next_target_syllable = words[-1]

        # Kiểm tra chiến thắng (Khóa mõm / Bí từ)
        if not self.has_next_word(new_phrase, word_counts):
            await self._safe_add_reaction(message, "👑")
            self.scores[guild_id_str][user_id_str] += 3
            self.weekly_scores[guild_id_str][user_id_str] += 3
            p_stats["wins"] += 1
            unlocked = self.check_achievements(p_stats)

            embed_winner = discord.Embed(
                title=t(message.guild, "WC_WIN_TITLE"),
                description=t(message.guild, "WC_WIN_DESC", syllable=next_target_syllable.upper(), mention=message.author.mention),
                color=discord.Color.gold()
            )
            await message.channel.send(embed=embed_winner)
            if unlocked:
                await message.channel.send(f"🏅 Chúc mừng {message.author.mention} vừa mở khóa danh hiệu: **{', '.join(unlocked)}**!")

            pve_mode = game_state.get("pve_mode", False)
            new_start_word = self._reset_new_round(guild_id_str, game_state["channel_id"], pve_mode=pve_mode)
            embed_new = discord.Embed(
                title=t(message.guild, "WC_AUTO_NEW_TITLE"),
                description=t(message.guild, "WC_AUTO_NEW_DESC", word=new_start_word.upper(), syllable=new_start_word.split()[-1].upper()),
                color=discord.Color.purple()
            )
            await message.channel.send(embed=embed_new)
            return

        unlocked = self.check_achievements(p_stats)
        if unlocked:
            await message.channel.send(f"🏅 Chúc mừng {message.author.mention} vừa mở khóa danh hiệu: **{', '.join(unlocked)}**!")

        if golden_bonus > 0:
            await message.channel.send(f"🌟 **TỪ KHÓA VÀNG!** {message.author.mention} đã nối thành công từ có âm tiết thứ 2 bắt đầu bằng chữ **`{golden_letter.upper()}`** và nhận được **x3 điểm**!")
        if streak_bonus > 0:
            await message.channel.send(f"🔥 Chuỗi **{streak} từ** liên tiếp! {message.author.mention} nhận thêm `+{streak_bonus}` điểm thưởng{shield_reward_msg}!")

        # --- CHẾ ĐỘ ĐẤU VỚI BOT (PvE MODE) ---
        if game_state.get("pve_mode", False):
            await asyncio.sleep(1.2)
            if game_state.get("current_word") != new_phrase:
                return

            candidates = [
                w for w in self.word_index.get(next_target_syllable, [])
                if word_counts.get(w, 0) < 3 and self.has_next_word(w, word_counts)
            ]

            if not candidates or (streak > 12 and random.random() < 0.08):
                self.scores[guild_id_str][user_id_str] += 3
                self.weekly_scores[guild_id_str][user_id_str] += 3
                pve_mode = game_state.get("pve_mode", False)
                new_start_word = self._reset_new_round(guild_id_str, game_state["channel_id"], pve_mode=pve_mode)
                await message.channel.send(
                    f"🏳️ **Bot xin chào thua!** Bot không nghĩ ra từ nào bắt đầu bằng **`{next_target_syllable.upper()}`** nữa. "
                    f"{message.author.mention} được thưởng nóng `+3 điểm`!\n"
                    f"🔄 Ván mới bắt đầu với từ: **`{new_start_word.upper()}`** (nối tiếp bằng chữ **`{new_start_word.split()[-1].upper()}`**)"
                )
                return

            bot_word = random.choice(candidates)
            game_state["current_word"] = bot_word
            game_state["last_player_id"] = self.bot.user.id
            game_state["streak"] = streak + 1
            word_counts[bot_word] = word_counts.get(bot_word, 0) + 1
            self.dirty_data = True

            bot_next_syllable = bot_word.split()[-1]
            await message.channel.send(f"🤖 Bot nối: **`{bot_word}`** *(Tiếp theo: **`{bot_next_syllable.upper()}`**)*")
            next_target_syllable = bot_next_syllable

        # --- KÍCH HOẠT SỰ KIỆN "TỪ KHÓA VÀNG" ---
        if game_state["streak"] % 8 == 0:
            available_next = [w for w in self.word_index.get(next_target_syllable, []) if word_counts.get(w, 0) < 3]
            possible_letters = list({w.split()[1][0] for w in available_next if len(w.split()) == 2})
            if possible_letters:
                chosen_letter = random.choice(possible_letters)
                game_state["golden_letter"] = chosen_letter
                await message.channel.send(
                    f"✨ **THỬ THÁCH TỪ KHÓA VÀNG:** Người tiếp theo nối từ bắt đầu bằng **`{next_target_syllable.upper()}`** "
                    f"mà chữ thứ hai bắt đầu bằng chữ cái **`{chosen_letter.upper()}`** (VD: `{next_target_syllable} {chosen_letter}...`) sẽ nhận ngay **x3 ĐIỂM**!"
                )


async def setup(bot: commands.Bot):
    await bot.add_cog(WordChainGame(bot))
