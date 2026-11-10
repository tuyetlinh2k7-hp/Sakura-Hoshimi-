import asyncio
import json
import random
import time
import unicodedata
from typing import Dict, List, Optional, Any
from aiohttp import web, WSMsgType

def remove_accents(input_str: str) -> str:
    if not input_str:
        return ""
    s1 = unicodedata.normalize('NFD', input_str.lower())
    s2 = "".join(c for c in s1 if unicodedata.category(c) != 'Mn')
    return s2.replace('đ', 'd').strip()

def levenshtein_dist(s1: str, s2: str) -> int:
    if len(s1) < len(s2):
        return levenshtein_dist(s2, s1)
    if len(s2) == 0:
        return len(s1)
    previous_row = range(len(s2) + 1)
    for i, c1 in enumerate(s1):
        current_row = [i + 1]
        for j, c2 in enumerate(s2):
            insertions = previous_row[j + 1] + 1
            deletions = current_row[j] + 1
            substitutions = previous_row[j] + (c1 != c2)
            current_row.append(min(insertions, deletions, substitutions))
        previous_row = current_row
    return previous_row[-1]

WORD_CATEGORIES_VI = {
    "Động vật": [
        "Con mèo", "Con chó", "Con cá", "Con chim", "Con voi", "Con hổ", "Con rắn",
        "Con rùa", "Con gấu", "Con khỉ", "Sư tử", "Cá mập", "Con thỏ", "Con vịt",
        "Con bướm", "Con ếch", "Con bò", "Con cừu", "Con ngựa", "Cá heo", "Chim cánh cụt",
        "Con gà", "Con lợn", "Hươu cao cổ", "Con chuột", "Con cua", "Con tôm", "Con ong",
        "Đại bàng", "Con trâu", "Con sóc", "Bạch tuộc", "Con lạc đà", "Con nhện", "Con cáo"
    ],
    "Đồ ăn & Thức uống": [
        "Bánh mì", "Phở", "Trà sữa", "Cà phê", "Cây kem", "Quả táo", "Quả chuối",
        "Dưa hấu", "Trứng rán", "Xúc xích", "Kẹo mút", "Hamburger", "Pizza", "Bánh kem",
        "Bún chả", "Bánh quy", "Cơm cuộn", "Quả xoài", "Quả cam", "Quả dâu", "Nước dừa",
        "Mì tôm", "Bánh bao", "Bánh donut", "Bắp rang bơ", "Quả dứa", "Quả bơ", "Socola"
    ],
    "Đồ vật & Gia dụng": [
        "Cái bàn", "Cái ghế", "Đồng hồ", "Điện thoại", "Máy tính", "Bút chì", "Quyển sách",
        "Cái giường", "Cái kéo", "Cái thìa", "Cái bát", "Đèn pin", "Cái ô", "Cái quạt",
        "Tủ lạnh", "Ti vi", "Kính râm", "Cái mũ", "Chiếc nhẫn", "Cây đàn", "Cái chổi",
        "Cái gương", "Cái gối", "Cái vali", "Cái cốc", "Bình hoa", "Tai nghe", "Bong bóng"
    ],
    "Tự nhiên & Vũ trụ": [
        "Mặt trời", "Mặt trăng", "Ngôi sao", "Cầu vồng", "Đám mây", "Bông hoa", "Cây cối",
        "Ngọn núi", "Cơn mưa", "Tuyết rơi", "Sấm sét", "Núi lửa", "Hòn đảo", "Bãi biển",
        "Ngọn lửa", "Giọt nước", "Lá cây", "Cây nấm", "Củ cà rốt", "Bụi cỏ", "Cây xương rồng"
    ],
    "Xe cộ & Địa điểm": [
        "Xe đạp", "Xe máy", "Ô tô", "Máy bay", "Tàu hỏa", "Thuyền buồm", "Khinh khí cầu",
        "Tàu ngầm", "Ngôi nhà", "Lâu đài", "Cây cầu", "Bệnh viện", "Trường học", "Cối xay gió",
        "Kim tự tháp", "Đèn giao thông", "Trạm xăng", "Tên lửa"
    ],
    "Hành động & Khác": [
        "Trái tim", "Vương miện", "Cây kiếm", "Cái khiên", "Kim cương", "Hộp quà",
        "Đôi giày", "Cái áo", "Quần jean", "Bàn tay", "Con mắt", "Nụ cười", "Mặt cười",
        "Ma cà rồng", "Người tuyết", "Bộ xương", "Nốt nhạc", "Lá cờ", "Quả bóng"
    ]
}

ALL_WORDS_VI = []
for words in WORD_CATEGORIES_VI.values():
    ALL_WORDS_VI.extend(words)

ENGLISH_WORDS = [
    "Cat", "Dog", "Fish", "Bird", "Elephant", "Tiger", "Snake", "Turtle", "Bear", "Monkey",
    "Lion", "Shark", "Rabbit", "Duck", "Butterfly", "Frog", "Cow", "Sheep", "Horse", "Dolphin",
    "Penguin", "Chicken", "Pig", "Giraffe", "Mouse", "Crab", "Shrimp", "Bee", "Eagle", "Fox",
    "Bread", "Pizza", "Hamburger", "Coffee", "Ice cream", "Apple", "Banana", "Watermelon",
    "Egg", "Sausage", "Candy", "Cake", "Cookie", "Sushi", "Mango", "Orange", "Strawberry",
    "Coconut", "Noodles", "Donut", "Popcorn", "Pineapple", "Avocado", "Chocolate", "Cheese",
    "Table", "Chair", "Clock", "Phone", "Computer", "Pencil", "Book", "Bed", "Scissors",
    "Spoon", "Bowl", "Flashlight", "Umbrella", "Fan", "Fridge", "Television", "Sunglasses",
    "Hat", "Ring", "Guitar", "Broom", "Mirror", "Pillow", "Suitcase", "Cup", "Vase", "Headphones",
    "Sun", "Moon", "Star", "Rainbow", "Cloud", "Flower", "Tree", "Mountain", "Rain", "Snow",
    "Lightning", "Volcano", "Island", "Beach", "Fire", "Water drop", "Leaf", "Mushroom", "Carrot",
    "Bicycle", "Motorcycle", "Car", "Airplane", "Train", "Boat", "Hot air balloon",
    "Submarine", "House", "Castle", "Bridge", "Hospital", "School", "Windmill", "Pyramid",
    "Heart", "Crown", "Sword", "Shield", "Diamond", "Gift box", "Shoes", "Shirt", "Jeans",
    "Hand", "Eye", "Smile", "Vampire", "Snowman", "Skeleton", "Music note", "Flag", "Ball",
    "Rocket", "Ghost", "Robot", "Anchor", "Camera", "Key", "Lock"
]

ALL_WORDS = ALL_WORDS_VI

BOT_SKETCHES: Dict[str, List[Dict[str, Any]]] = {
    "mặt trời": [
        {"tool": "pen", "color": "#ffe400", "size": 6, "points": [[0.5,0.3],[0.55,0.32],[0.6,0.38],[0.62,0.45],[0.6,0.52],[0.55,0.58],[0.5,0.6],[0.45,0.58],[0.4,0.52],[0.38,0.45],[0.4,0.38],[0.45,0.32],[0.5,0.3]]},
        {"tool": "pen", "color": "#ff7100", "size": 5, "points": [[0.5,0.25],[0.5,0.15]]},
        {"tool": "pen", "color": "#ff7100", "size": 5, "points": [[0.5,0.65],[0.5,0.75]]},
        {"tool": "pen", "color": "#ff7100", "size": 5, "points": [[0.33,0.45],[0.23,0.45]]},
        {"tool": "pen", "color": "#ff7100", "size": 5, "points": [[0.67,0.45],[0.77,0.45]]},
    ],
    "sun": [
        {"tool": "pen", "color": "#ffe400", "size": 6, "points": [[0.5,0.3],[0.55,0.32],[0.6,0.38],[0.62,0.45],[0.6,0.52],[0.55,0.58],[0.5,0.6],[0.45,0.58],[0.4,0.52],[0.38,0.45],[0.4,0.38],[0.45,0.32],[0.5,0.3]]},
        {"tool": "pen", "color": "#ff7100", "size": 5, "points": [[0.5,0.25],[0.5,0.15]]},
        {"tool": "pen", "color": "#ff7100", "size": 5, "points": [[0.5,0.65],[0.5,0.75]]},
    ],
    "ngôi nhà": [
        {"tool": "pen", "color": "#231fd3", "size": 5, "points": [[0.3,0.45],[0.7,0.45],[0.7,0.8],[0.3,0.8],[0.3,0.45]]},
        {"tool": "pen", "color": "#ef130b", "size": 6, "points": [[0.25,0.46],[0.5,0.2],[0.75,0.46]]},
        {"tool": "pen", "color": "#00b2ff", "size": 4, "points": [[0.44,0.8],[0.44,0.6],[0.56,0.6],[0.56,0.8]]},
    ],
    "house": [
        {"tool": "pen", "color": "#231fd3", "size": 5, "points": [[0.3,0.45],[0.7,0.45],[0.7,0.8],[0.3,0.8],[0.3,0.45]]},
        {"tool": "pen", "color": "#ef130b", "size": 6, "points": [[0.25,0.46],[0.5,0.2],[0.75,0.46]]},
        {"tool": "pen", "color": "#00b2ff", "size": 4, "points": [[0.44,0.8],[0.44,0.6],[0.56,0.6],[0.56,0.8]]},
    ],
    "con cá": [
        {"tool": "pen", "color": "#00b2ff", "size": 6, "points": [[0.2,0.5],[0.35,0.32],[0.6,0.35],[0.75,0.5],[0.6,0.65],[0.35,0.68],[0.2,0.5]]},
        {"tool": "pen", "color": "#00cc00", "size": 5, "points": [[0.75,0.5],[0.88,0.36],[0.85,0.5],[0.88,0.64],[0.75,0.5]]},
    ],
    "fish": [
        {"tool": "pen", "color": "#00b2ff", "size": 6, "points": [[0.2,0.5],[0.35,0.32],[0.6,0.35],[0.75,0.5],[0.6,0.65],[0.35,0.68],[0.2,0.5]]},
        {"tool": "pen", "color": "#00cc00", "size": 5, "points": [[0.75,0.5],[0.88,0.36],[0.85,0.5],[0.88,0.64],[0.75,0.5]]},
    ],
    "trái tim": [
        {"tool": "pen", "color": "#ef130b", "size": 7, "points": [[0.5,0.35],[0.42,0.22],[0.28,0.24],[0.22,0.38],[0.26,0.52],[0.5,0.8],[0.74,0.52],[0.78,0.38],[0.72,0.24],[0.58,0.22],[0.5,0.35]]},
    ],
    "heart": [
        {"tool": "pen", "color": "#ef130b", "size": 7, "points": [[0.5,0.35],[0.42,0.22],[0.28,0.24],[0.22,0.38],[0.26,0.52],[0.5,0.8],[0.74,0.52],[0.78,0.38],[0.72,0.24],[0.58,0.22],[0.5,0.35]]},
    ],
    "bông hoa": [
        {"tool": "pen", "color": "#00cc00", "size": 6, "points": [[0.5,0.5],[0.5,0.85]]},
        {"tool": "pen", "color": "#ffe400", "size": 14, "points": [[0.5,0.38],[0.5,0.38]]},
        {"tool": "pen", "color": "#df69a7", "size": 7, "points": [[0.5,0.25],[0.54,0.3],[0.5,0.35]]},
        {"tool": "pen", "color": "#df69a7", "size": 7, "points": [[0.5,0.45],[0.54,0.5],[0.5,0.53]]},
    ],
    "flower": [
        {"tool": "pen", "color": "#00cc00", "size": 6, "points": [[0.5,0.5],[0.5,0.85]]},
        {"tool": "pen", "color": "#ffe400", "size": 14, "points": [[0.5,0.38],[0.5,0.38]]},
        {"tool": "pen", "color": "#df69a7", "size": 7, "points": [[0.5,0.25],[0.54,0.3],[0.5,0.35]]},
    ]
}

def make_word_hint(word: str, revealed_indices: set, game_mode: str = "classic") -> Dict[str, Any]:
    words = word.split()
    lengths = [len(w) for w in words]

    if game_mode == "mystery":
        hint_parts = ["? " * l for l in lengths]
        return {
            "text": "   ".join([p.strip() for p in hint_parts]),
            "lengths": lengths,
            "lengths_str": "Ẩn danh"
        }

    hint_parts = []
    idx = 0
    for w in words:
        chars = []
        for ch in w:
            if idx in revealed_indices:
                chars.append(ch)
            else:
                chars.append("_")
            idx += 1
        hint_parts.append(" ".join(chars))
        idx += 1

    return {
        "text": "   ".join(hint_parts),
        "lengths": lengths,
        "lengths_str": ", ".join(str(l) for l in lengths)
    }

class Player:
    def __init__(self, pid: str, name: str, avatar: str, avatar_data: Optional[Dict[str, int]], ws: Optional[web.WebSocketResponse], is_bot: bool = False):
        self.pid = pid
        self.name = name
        self.avatar = avatar or ""
        self.avatar_data = avatar_data or {"color": random.randint(0, 17), "eyes": random.randint(0, 7), "mouth": random.randint(0, 7)}
        self.ws = ws
        self.is_bot = is_bot
        self.score = 0
        self.round_score = 0
        self.has_guessed = False

    def to_dict(self):
        return {
            "id": self.pid,
            "name": self.name,
            "avatar": self.avatar,
            "avatar_data": self.avatar_data,
            "score": self.score,
            "is_bot": self.is_bot,
            "has_guessed": self.has_guessed,
        }

class ScribbleRoom:
    def __init__(self, room_id: str):
        self.room_id = room_id
        self.players: Dict[str, Player] = {}
        self.host_id: Optional[str] = None
        self.state = "waiting"
        self.drawer_id: Optional[str] = None
        self.drawer_order: List[str] = []
        self.drawer_index = -1
        self.word = ""
        self.word_choices: List[str] = []
        self.revealed_indices = set()
        self.hint_data: Dict[str, Any] = {"text": "_ _ _ _", "lengths": [4], "lengths_str": "4"}
        self.timer = 0

        self.max_players = 8
        self.language = "vi"
        self.draw_time = 80
        self.max_rounds = 3
        self.game_mode = "classic"
        self.word_choices_count = 3
        self.hint_count = -1
        self.custom_words: List[str] = []
        self.game_word_pool: List[str] = []

        self.strokes: List[Dict[str, Any]] = []
        self.bot_enabled = False
        self.loop_task: Optional[asyncio.Task] = None
        self.bot_drawing_task: Optional[asyncio.Task] = None
        self.thumbs_up = 0
        self.thumbs_down = 0

    def _add_bot(self):
        bot_player = Player(
            "sakura_bot", "🌸 Sakura Bot",
            "https://raw.githubusercontent.com/twitter/twemoji/master/assets/72x72/1f338.png",
            {"color": 4, "eyes": 2, "mouth": 1},
            None, is_bot=True
        )
        self.players["sakura_bot"] = bot_player

    def ensure_loop(self):
        if self.loop_task is None or self.loop_task.done():
            self.loop_task = asyncio.create_task(self._room_lifecycle_loop())

    async def broadcast(self, msg: dict, exclude_pid: Optional[str] = None):
        data = json.dumps(msg, ensure_ascii=False)
        dead = []
        for pid, p in self.players.items():
            if exclude_pid and pid == exclude_pid:
                continue
            if p.ws and not p.ws.closed:
                try:
                    await p.ws.send_str(data)
                except Exception:
                    dead.append(pid)
        for pid in dead:
            self.remove_player(pid)

    async def send_to(self, pid: str, msg: dict):
        p = self.players.get(pid)
        if p and p.ws and not p.ws.closed:
            try:
                await p.ws.send_str(json.dumps(msg, ensure_ascii=False))
            except Exception:
                pass

    def add_player(self, pid: str, name: str, avatar: str, avatar_data: Optional[dict], ws: web.WebSocketResponse):
        if pid in self.players:
            p = self.players[pid]
            p.ws = ws
            p.name = name
            if avatar:
                p.avatar = avatar
            if avatar_data:
                p.avatar_data = avatar_data
        else:
            p = Player(pid, name, avatar, avatar_data, ws, is_bot=False)
            self.players[pid] = p

        if not self.host_id or self.host_id not in self.players or self.players[self.host_id].is_bot:
            humans = [pl.pid for pl in self.players.values() if not pl.is_bot]
            if humans:
                self.host_id = humans[0]

        self.ensure_loop()
        return p

    def remove_player(self, pid: str):
        if pid in self.players and not self.players[pid].is_bot:
            del self.players[pid]
            if pid in self.drawer_order:
                self.drawer_order.remove(pid)
            if self.host_id == pid:
                remaining_humans = [pl.pid for pl in self.players.values() if not pl.is_bot]
                self.host_id = remaining_humans[0] if remaining_humans else None
            if self.drawer_id == pid:
                asyncio.create_task(self.end_turn("Người vẽ đã rời phòng!"))

    def toggle_bot(self):
        self.bot_enabled = not self.bot_enabled
        if not self.bot_enabled:
            if "sakura_bot" in self.players:
                del self.players["sakura_bot"]
            if "sakura_bot" in self.drawer_order:
                self.drawer_order.remove("sakura_bot")
        else:
            if "sakura_bot" not in self.players:
                self._add_bot()
        return self.bot_enabled

    def update_settings(self, max_players: int = 8, language: str = "vi", draw_time: int = 80,
                        max_rounds: int = 3, game_mode: str = "classic", word_choices_count: int = 3,
                        hint_count: int = -1, custom_words_str: str = ""):
        if 2 <= max_players <= 16:
            self.max_players = max_players
        if language in ("vi", "en", "bilingual"):
            self.language = language
        if draw_time in (30, 45, 60, 80, 100, 120, 150, 180):
            self.draw_time = draw_time
        if 1 <= max_rounds <= 10:
            self.max_rounds = max_rounds
        if game_mode in ("classic", "mystery", "speed", "practice"):
            self.game_mode = game_mode
        if 2 <= word_choices_count <= 5:
            self.word_choices_count = word_choices_count
        if -1 <= hint_count <= 3:
            self.hint_count = hint_count

        if custom_words_str is not None:
            raw_list = [w.strip() for w in custom_words_str.replace("\n", ",").split(",") if w.strip()]
            self.custom_words = raw_list

    def prepare_game_word_pool(self):
        participants = [p for p in self.players.values() if not p.is_bot or self.bot_enabled]
        num_players = max(1, len(participants))
        total_words_needed = self.word_choices_count * num_players * self.max_rounds

        base_pool = []
        if self.language == "en":
            base_pool = list(ENGLISH_WORDS)
        elif self.language == "bilingual":
            base_pool = list(ALL_WORDS_VI) + list(ENGLISH_WORDS)
        else:
            base_pool = list(ALL_WORDS_VI)
        random.shuffle(base_pool)

        clean_custom = [w.strip() for w in self.custom_words if w.strip()]

        if len(clean_custom) >= total_words_needed:
            shuffled_custom = list(clean_custom)
            random.shuffle(shuffled_custom)
            self.game_word_pool = shuffled_custom[:total_words_needed]
        else:
            needed_more = total_words_needed - len(clean_custom)
            custom_lower = {remove_accents(w).lower() for w in clean_custom}
            fillers = [w for w in base_pool if remove_accents(w).lower() not in custom_lower]
            if len(fillers) < needed_more:
                fillers = fillers * (needed_more // max(1, len(fillers)) + 1)
            added = fillers[:needed_more]
            combined = clean_custom + added
            random.shuffle(combined)
            self.game_word_pool = combined

    def get_room_state_dict(self):
        drawer_name = ""
        if self.drawer_id and self.drawer_id in self.players:
            drawer_name = self.players[self.drawer_id].name

        sorted_players = sorted(self.players.values(), key=lambda p: p.score, reverse=True)
        participants_cnt = max(1, len([p for p in self.players.values() if not p.is_bot or self.bot_enabled]))
        total_needed = self.word_choices_count * participants_cnt * self.max_rounds

        return {
            "type": "room_state",
            "room_id": self.room_id,
            "host_id": self.host_id,
            "state": self.state,
            "round": self.round,
            "max_rounds": self.max_rounds,
            "draw_time": self.draw_time,
            "timer": self.timer,
            "drawer_id": self.drawer_id,
            "drawer_name": drawer_name,
            "hint": self.hint_data.get("text", ""),
            "lengths_str": self.hint_data.get("lengths_str", ""),
            "bot_enabled": self.bot_enabled,
            "thumbs_up": self.thumbs_up,
            "thumbs_down": self.thumbs_down,
            "settings": {
                "max_players": self.max_players,
                "language": self.language,
                "draw_time": self.draw_time,
                "max_rounds": self.max_rounds,
                "game_mode": self.game_mode,
                "word_choices_count": self.word_choices_count,
                "hint_count": self.hint_count,
                "custom_words": ", ".join(self.custom_words),
                "custom_words_count": len(self.custom_words),
                "total_words_needed": total_needed
            },
            "players": [p.to_dict() for p in sorted_players],
        }

    async def start_game(self):
        human_count = sum(1 for p in self.players.values() if not p.is_bot)
        if human_count < 1:
            return

        self.prepare_game_word_pool()
        self.round = 1
        for p in self.players.values():
            p.score = 0
        humans = [pid for pid, p in self.players.items() if not p.is_bot]
        random.shuffle(humans)
        self.drawer_order = humans
        self.drawer_index = -1
        self.strokes = []
        await self.broadcast({"type": "clear"})
        await self.next_turn()

    async def next_turn(self):
        self.drawer_index += 1
        if self.drawer_index >= len(self.drawer_order):
            self.round += 1
            if self.round > self.max_rounds:
                await self.game_over()
                return
            self.drawer_index = 0
            humans = [pid for pid, p in self.players.items() if not p.is_bot]
            random.shuffle(humans)
            self.drawer_order = humans

        self.drawer_id = self.drawer_order[self.drawer_index]
        drawer = self.players.get(self.drawer_id)
        if not drawer:
            await self.next_turn()
            return

        self.strokes = []
        await self.broadcast({"type": "clear"})
        self.thumbs_up = 0
        self.thumbs_down = 0
        for p in self.players.values():
            p.has_guessed = False
            p.round_score = 0

        self.state = "selecting"
        self.timer = 15
        self.word = ""
        self.revealed_indices = set()
        self.hint_data = {"text": "", "lengths": [], "lengths_str": ""}

        choices = []
        while len(choices) < self.word_choices_count and self.game_word_pool:
            choices.append(self.game_word_pool.pop(0))
        if len(choices) < self.word_choices_count:
            fallback = ALL_WORDS_VI if self.language == "vi" else ENGLISH_WORDS
            choices.extend(random.sample(fallback, min(self.word_choices_count - len(choices), len(fallback))))

        self.word_choices = choices

        await self.broadcast(self.get_room_state_dict())
        await self.broadcast({
            "type": "chat",
            "sender": "Hệ thống",
            "text": f"🎨 {drawer.name} đang chọn từ khóa...",
            "system": True
        })

        if drawer.is_bot:
            chosen = random.choice(self.word_choices)
            asyncio.create_task(self.start_drawing_phase(chosen))
        else:
            await self.send_to(drawer.pid, {
                "type": "word_choices",
                "words": self.word_choices
            })

    async def start_drawing_phase(self, word: str):
        if self.state != "selecting":
            return
        self.word = word
        self.state = "drawing"
        if self.game_mode == "speed":
            self.timer = 35
        else:
            self.timer = self.draw_time

        self.revealed_indices = set()
        self.hint_data = make_word_hint(self.word, self.revealed_indices, self.game_mode)

        if self.drawer_id:
            await self.send_to(self.drawer_id, {
                "type": "your_word",
                "word": self.word
            })

        await self.broadcast(self.get_room_state_dict())
        await self.broadcast({
            "type": "chat",
            "sender": "Hệ thống",
            "text": f"🚀 {self.players[self.drawer_id].name if self.drawer_id in self.players else 'Người vẽ'} đang vẽ!",
            "system": True
        })

        if self.drawer_id == "sakura_bot":
            if self.bot_drawing_task and not self.bot_drawing_task.done():
                self.bot_drawing_task.cancel()
            self.bot_drawing_task = asyncio.create_task(self._bot_draw_routine(word))

    async def _bot_draw_routine(self, word: str):
        try:
            w_norm = remove_accents(word).strip().lower()
            sketch = None
            for key, strokes in BOT_SKETCHES.items():
                if key in w_norm or w_norm in key:
                    sketch = strokes
                    break

            if not sketch:
                sketch = [
                    {"tool": "pen", "color": "#df69a7", "size": 6, "points": [[0.3,0.3],[0.7,0.3],[0.7,0.7],[0.3,0.7],[0.3,0.3]]},
                    {"tool": "pen", "color": "#00b2ff", "size": 5, "points": [[0.3,0.3],[0.7,0.7]]},
                    {"tool": "pen", "color": "#ffe400", "size": 5, "points": [[0.7,0.3],[0.3,0.7]]},
                ]

            await asyncio.sleep(1.0)
            for item in sketch:
                if self.state != "drawing" or self.drawer_id != "sakura_bot":
                    break
                pts = item.get("points", [])
                tool = item.get("tool", "pen")
                color = item.get("color", "#000000")
                size = item.get("size", 6)

                for i in range(len(pts) - 1):
                    if self.state != "drawing":
                        break
                    p0 = pts[i]
                    p1 = pts[i+1]
                    stroke = {
                        "tool": tool, "color": color, "size": size,
                        "x0": p0[0], "y0": p0[1], "x1": p1[0], "y1": p1[1]
                    }
                    self.strokes.append(stroke)
                    await self.broadcast({"type": "draw", "stroke": stroke})
                    await asyncio.sleep(random.uniform(0.12, 0.28))

                await asyncio.sleep(random.uniform(0.3, 0.7))
        except asyncio.CancelledError:
            pass
        except Exception:
            pass

    async def end_turn(self, reason: str = ""):
        if self.state not in ("selecting", "drawing"):
            return
        self.state = "round_end"
        self.timer = 5
        self.strokes = []
        await self.broadcast({"type": "clear"})

        drawer = self.players.get(self.drawer_id)
        if drawer:
            guesser_count = sum(1 for pid, p in self.players.items() if pid != self.drawer_id and p.has_guessed)
            if guesser_count > 0:
                drawer_bonus = guesser_count * 80
                drawer.score += drawer_bonus
                drawer.round_score += drawer_bonus

        word_text = self.word or "(Chưa chọn)"
        sorted_players = sorted(self.players.values(), key=lambda p: p.score, reverse=True)

        await self.broadcast({
            "type": "turn_summary",
            "word": word_text,
            "reason": reason or f"Hết giờ! Từ khóa là: {word_text}",
            "scores": {pid: p.score for pid, p in self.players.items()},
            "players": [p.to_dict() for p in sorted_players]
        })

        await asyncio.sleep(5)
        await self.next_turn()

    async def game_over(self):
        self.state = "game_over"
        ranked = sorted(self.players.values(), key=lambda p: p.score, reverse=True)
        await self.broadcast({
            "type": "game_over",
            "leaderboard": [p.to_dict() for p in ranked]
        })

    async def handle_guess(self, pid: str, text: str):
        p = self.players.get(pid)
        if not p or not text.strip():
            return

        text = text.strip()

        if self.drawer_id == pid:
            await self.send_to(pid, {
                "type": "chat",
                "sender": "Hệ thống",
                "text": "✏️ Bạn đang là người vẽ nên bị cấm chat trong lượt này!",
                "system": True
            })
            return

        if p.has_guessed:
            msg = {
                "type": "chat",
                "sender": p.name,
                "text": text,
                "system": False,
                "sender_id": pid,
                "green_chat": True
            }
            for pl_id, pl in self.players.items():
                if pl.has_guessed or pl_id == self.drawer_id:
                    await self.send_to(pl_id, msg)
            return

        if self.state != "drawing":
            await self.broadcast({
                "type": "chat",
                "sender": p.name,
                "text": text,
                "system": False,
                "sender_id": pid
            })
            return

        clean_guess = remove_accents(text).replace(" ", "").lower()
        clean_word = remove_accents(self.word).replace(" ", "").lower()

        if clean_guess == clean_word:
            p.has_guessed = True
            base_draw_time = 35 if self.game_mode == "speed" else self.draw_time
            ratio = max(0.1, min(1.0, self.timer / float(base_draw_time or 60)))
            earned = 100 + int(ratio * 400)
            if self.game_mode == "speed":
                earned *= 2

            p.score += earned
            p.round_score = earned

            await self.broadcast({
                "type": "chat",
                "sender": "Hệ thống",
                "text": f"🎉 {p.name} đã đoán đúng từ khóa!",
                "system": True,
                "correct": True
            })
            await self.send_to(pid, {
                "type": "chat",
                "sender": "Hệ thống",
                "text": f"✅ Bạn đã đoán đúng từ khóa! (+{earned} điểm)",
                "system": True,
                "correct": True
            })

            await self.broadcast(self.get_room_state_dict())

            guessers = [pl for pl_id, pl in self.players.items() if pl_id != self.drawer_id]
            if all(pl.has_guessed for pl in guessers):
                await self.end_turn("Tất cả người chơi đều đã đoán đúng!")
            return

        dist = levenshtein_dist(clean_guess, clean_word)
        if dist <= 1 and len(clean_word) >= 3 and self.game_mode != "mystery":
            await self.send_to(pid, {
                "type": "chat",
                "sender": "Gợi ý",
                "text": f"🔥 '{text}' rất gần với từ khóa rồi!",
                "system": True,
                "close": True
            })

        await self.broadcast({
            "type": "chat",
            "sender": p.name,
            "text": text,
            "system": False,
            "sender_id": pid
        })

    async def handle_reaction(self, pid: str, reaction: str):
        if self.state != "drawing" or not self.drawer_id or pid == self.drawer_id:
            return
        if reaction == "like":
            self.thumbs_up += 1
        elif reaction == "dislike":
            self.thumbs_down += 1
        p = self.players.get(pid)
        pname = p.name if p else "Ai đó"
        await self.broadcast({
            "type": "reaction_fly",
            "reaction": reaction,
            "player_name": pname,
            "thumbs_up": self.thumbs_up,
            "thumbs_down": self.thumbs_down
        })

    async def _room_lifecycle_loop(self):
        try:
            while True:
                await asyncio.sleep(1.0)
                humans = [p for p in self.players.values() if not p.is_bot and p.ws and not p.ws.closed]
                if not humans and self.state != "waiting":
                    self.state = "waiting"
                    self.timer = 0
                    continue

                if self.state == "waiting":
                    continue

                if self.state in ("selecting", "drawing"):
                    self.timer -= 1
                    await self.broadcast({"type": "timer_tick", "timer": self.timer})

                    if self.state == "drawing" and self.game_mode != "mystery":
                        curr_draw_time = 35 if self.game_mode == "speed" else self.draw_time
                        target_hints = self.hint_count
                        if target_hints == -1:
                            w_len = len(self.word.replace(" ", ""))
                            target_hints = 0 if w_len <= 3 else (1 if w_len <= 6 else (2 if w_len <= 9 else 3))

                        if target_hints > 0:
                            t_milestones = [int(curr_draw_time * (1.0 - (k + 1) / (target_hints + 1))) for k in range(target_hints)]
                            if self.timer in t_milestones:
                                non_revealed = [i for i, c in enumerate(self.word) if c != ' ' and i not in self.revealed_indices]
                                if non_revealed:
                                    pick = random.choice(non_revealed)
                                    self.revealed_indices.add(pick)
                                    self.hint_data = make_word_hint(self.word, self.revealed_indices, self.game_mode)
                                    await self.broadcast({
                                        "type": "hint_update",
                                        "hint": self.hint_data.get("text", "")
                                    })

                    if self.state == "drawing" and self.drawer_id != "sakura_bot" and self.bot_enabled:
                        bot = self.players.get("sakura_bot")
                        curr_draw_time = 35 if self.game_mode == "speed" else self.draw_time
                        if bot and not bot.has_guessed:
                            if self.timer < int(curr_draw_time * 0.5) and random.random() < 0.22:
                                await self.handle_guess("sakura_bot", self.word)
                            elif self.timer < int(curr_draw_time * 0.75) and random.random() < 0.12:
                                sample_words = [w for w in (ALL_WORDS_VI if self.language == "vi" else ENGLISH_WORDS) if w != self.word]
                                if sample_words:
                                    await self.handle_guess("sakura_bot", random.choice(sample_words))

                    if self.timer <= 0:
                        if self.state == "selecting":
                            chosen = self.word_choices[0] if self.word_choices else "Mặt trời"
                            await self.start_drawing_phase(chosen)
                        elif self.state == "drawing":
                            await self.end_turn("Hết thời gian!")

        except asyncio.CancelledError:
            pass
        except Exception:
            pass

SCRIBBLE_ROOMS: Dict[str, ScribbleRoom] = {}

def get_or_create_room(room_id: str) -> ScribbleRoom:
    clean_id = (room_id or "lobby").strip().lower()
    if clean_id not in SCRIBBLE_ROOMS:
        SCRIBBLE_ROOMS[clean_id] = ScribbleRoom(clean_id)
    return SCRIBBLE_ROOMS[clean_id]
