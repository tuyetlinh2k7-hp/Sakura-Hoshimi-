import asyncio
import io
import json
import math
import random
import time
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Literal, Optional, Dict, Any, List, Tuple

import aiohttp
import discord
from discord import app_commands
from discord.ext import commands, tasks

from data.database import get_user_data, update_user_coins, update_user_xu
from Check.i18n import t, is_vietnamese, get_guild_language
try:
    from Command.command_fishing import ENCHANT_AFFIXES
except Exception:
    ENCHANT_AFFIXES = []

# ==============================================================================
# HỆ THỐNG ĐÀO KHOÁNG SẢN (MINING SYSTEM - SAKURA BOT)
# ==============================================================================

MINING_DATA_FILE = Path("data/mining_data.json")
mining_state: Dict[str, Any] = {"users": {}}

# --- 1. DANH MỤC CUỐC ĐÀO (PICKS CATALOG) ---
PICKS_CATALOG: Dict[str, Dict[str, Any]] = {
    "pick_wooden": {
        "id": "pick_wooden", "name": "Cuốc Gỗ Sơ Cấp", "icon": "🪵", "rarity": "common",
        "price": 500, "luck": 5, "max_durability": 60, "min_level": 0, "speed_bonus": 0,
        "desc": "Chiếc cuốc gỗ mộc mạc cho tân thủ bắt đầu khám phá lòng đất."
    },
    "pick_stone": {
        "id": "pick_stone", "name": "Cuốc Đá Trầm Tích", "icon": "🪨", "rarity": "uncommon",
        "price": 4500, "luck": 20, "max_durability": 120, "min_level": 2, "speed_bonus": 5,
        "desc": "Được ghè từ đá hoa cương cứng cáp, bền bỉ hơn cuốc gỗ."
    },
    "pick_iron": {
        "id": "pick_iron", "name": "Cuốc Sắt Tôi Luyện", "icon": "⛏️", "rarity": "rare",
        "price": 18000, "luck": 50, "max_durability": 250, "min_level": 6, "speed_bonus": 10,
        "desc": "Lưỡi sắt rèn kỹ lưỡng, đập vỡ đá tảng một cách dễ dàng."
    },
    "pick_gold": {
        "id": "pick_gold", "name": "Cuốc Vàng Hoàng Kim", "icon": "🪙", "rarity": "rare",
        "price": 60000, "luck": 110, "max_durability": 180, "min_level": 12, "speed_bonus": 15, "sell_bonus": 25,
        "desc": "Tỏa ánh sáng kim tiền rực rỡ, tăng +25% giá bán quặng nhưng dễ mòn."
    },
    "pick_diamond": {
        "id": "pick_diamond", "name": "Cuốc Kim Cương Sắc Lẹm", "icon": "💎", "rarity": "epic",
        "price": 180000, "luck": 220, "max_durability": 600, "min_level": 20, "speed_bonus": 20, "mutant_bonus": 15,
        "desc": "Lưỡi kim cương siêu cứng, khai thác nhanh và dễ gặp mạch quặng đột biến."
    },
    "pick_netherite": {
        "id": "pick_netherite", "name": "Cuốc Netherite Dung Nham", "icon": "🖤", "rarity": "legendary",
        "price": 550000, "luck": 400, "max_durability": 1200, "min_level": 32, "speed_bonus": 25, "save_durability": 20,
        "desc": "Hợp kim địa ngục chịu nhiệt cao, 20% tỉ lệ không tiêu hao độ bền."
    },
    "pick_crystal": {
        "id": "pick_crystal", "name": "Cuốc Tinh Thể Vô Cực", "icon": "🔮", "rarity": "mythic",
        "price": 1600000, "luck": 700, "max_durability": 2500, "min_level": 45, "speed_bonus": 35,
        "desc": "Được đúc từ pha lê năng lượng vũ trụ, tăng vọt may mắn và tốc độ đào."
    },
    "pick_cosmic": {
        "id": "pick_cosmic", "name": "Cuốc Thần Thoại Khởi Nguyên", "icon": "🌌", "rarity": "godly",
        "price": 4500000, "luck": 1200, "max_durability": 5000, "min_level": 60, "speed_bonus": 45, "sell_bonus": 50, "auto_qte": True,
        "desc": "Bảo vật tối thượng chứa đựng sức mạnh vũ trụ: Tự động kéo khoáng boss & +50% giá trị quặng."
    }
}

# --- 2. DANH MỤC KHOÁNG SẢN & ĐÁ QUÝ (ORES CATALOG) ---
ORES_CATALOG: Dict[str, Dict[str, Any]] = {
    # COMMON
    "ore_stone": {"id": "ore_stone", "name": "Đá Hoa Cương", "icon": "🪨", "rarity": "common", "price": 50, "weight_range": (1.0, 4.0), "desc": "Đá thô thông thường dưới lòng đất."},
    "ore_coal": {"id": "ore_coal", "name": "Than Đá Hắc Thạch", "icon": "⬛", "rarity": "common", "price": 140, "weight_range": (1.2, 5.0), "desc": "Nhiên liệu đốt quan trọng."},
    "ore_copper": {"id": "ore_copper", "name": "Đồng Thô Cổ Điển", "icon": "🟫", "rarity": "common", "price": 320, "weight_range": (2.0, 7.5), "desc": "Quặng đồng mang ánh đỏ ánh vàng."},
    
    # UNCOMMON
    "ore_iron": {"id": "ore_iron", "name": "Quặng Sắt Tôi Rèn", "icon": "⚙️", "rarity": "uncommon", "price": 680, "weight_range": (3.0, 10.0), "desc": "Kim loại kiên cố phục vụ chế tác."},
    "ore_silver": {"id": "ore_silver", "name": "Bạc Ánh Trăng", "icon": "🥈", "rarity": "uncommon", "price": 1450, "weight_range": (2.5, 9.0), "desc": "Quặng bạc lấp lánh như trăng rằm."},
    "ore_lapis": {"id": "ore_lapis", "name": "Lapis Thần Bí", "icon": "🧿", "rarity": "uncommon", "price": 2200, "weight_range": (1.5, 6.0), "desc": "Khoáng thạch xanh thẳm tích tụ ma lực lòng đất."},

    # RARE
    "ore_gold": {"id": "ore_gold", "name": "Vàng Khối Tinh Khiết", "icon": "🪙", "rarity": "rare", "price": 3800, "weight_range": (4.0, 14.0), "desc": "Khối vàng tự nhiên lấp lánh ánh kim."},
    "gem_amethyst": {"id": "gem_amethyst", "name": "Thạch Anh Tím Hoàng Triều", "icon": "🟣", "rarity": "rare", "price": 5600, "weight_range": (1.0, 5.0), "desc": "Pha lê tím huyền bí tỏa sáng trong bóng tối."},
    "gem_topaz": {"id": "gem_topaz", "name": "Hoàng Ngọc Topaz", "icon": "🔶", "rarity": "rare", "price": 7500, "weight_range": (1.2, 6.0), "desc": "Viên đá quý màu hổ phách ấm áp."},

    # EPIC
    "gem_emerald": {"id": "gem_emerald", "name": "Ngọc Lục Bảo Đế Vương", "icon": "🟢", "rarity": "epic", "price": 13500, "weight_range": (1.0, 4.5), "desc": "Viên ngọc màu xanh lục bảo tượng trưng cho sự thịnh vượng."},
    "gem_ruby": {"id": "gem_ruby", "name": "Hồng Ngọc Huyết Long", "icon": "🔴", "rarity": "epic", "price": 19000, "weight_range": (1.2, 5.5), "desc": "Viên đá đỏ rực như máu rồng thức tỉnh."},
    "gem_sapphire": {"id": "gem_sapphire", "name": "Lam Ngọc Biển Cả", "icon": "🔷", "rarity": "epic", "price": 26000, "weight_range": (1.5, 6.0), "desc": "Viên ngọc xanh biếc mang linh hồn đại dương."},
    "gem_diamond": {"id": "gem_diamond", "name": "Kim Cương Tinh Khiết", "icon": "💎", "rarity": "epic", "price": 38000, "weight_range": (1.0, 7.0), "desc": "Khoáng vật cứng nhất tự nhiên, khúc xạ ánh sáng đa sắc."},

    # LEGENDARY
    "ore_obsidian": {"id": "ore_obsidian", "name": "Hắc Diện Thạch Hắc Ám", "icon": "🔲", "rarity": "legendary", "price": 65000, "weight_range": (8.0, 30.0), "desc": "Dung nham đông cứng tạo thành khối đá đen tuyền bất hoại."},
    "fossil_ancient": {"id": "fossil_ancient", "name": "Hóa Thạch Rồng Tiền Sử", "icon": "🦖", "rarity": "legendary", "price": 110000, "weight_range": (15.0, 45.0), "desc": "Dấu tích hóa thạch cổ xưa của loài rồng ngàn năm tuổi."},
    "ore_meteorite": {"id": "ore_meteorite", "name": "Mảnh Thiên Thạch Vũ Trụ", "icon": "☄️", "rarity": "legendary", "price": 185000, "weight_range": (6.0, 25.0), "desc": "Vụn vẫn thạch rơi từ khoảng không vũ trụ hàng triệu năm trước."},
    "ore_netherite": {"id": "ore_netherite", "name": "Kim Loại Netherite Địa Ngục", "icon": "🧱", "rarity": "legendary", "price": 320000, "weight_range": (10.0, 35.0), "desc": "Mảnh phế tích cổ đại được nén chặt dưới tầng dung nham sâu."},

    # MYTHIC & GODLY
    "heart_of_earth": {"id": "heart_of_earth", "name": "Trái Tim Địa Mẫu Gaia", "icon": "❤️‍🔥", "rarity": "mythic", "price": 750000, "weight_range": (20.0, 60.0), "desc": "Khối tinh hoa magma ấm nóng nuôi dưỡng linh khí cả hành tinh."},
    "void_singularity": {"id": "void_singularity", "name": "Hạt Nhân Hư Không The End", "icon": "🌌", "rarity": "godly", "price": 2000000, "weight_range": (35.0, 100.0), "desc": "Vật thể kỳ dị bẻ cong không thời gian, báu vật tối thượng của người khai mỏ."}
}

# --- 3. VÙNG KHAI THÁC MỎ (MINING ZONES) ---
MINING_ZONES: Dict[str, Dict[str, Any]] = {
    "hang_dat": {
        "id": "hang_dat", "name": "Hang Đất Đồi Cỏ", "icon": "🌿", "min_level": 0,
        "luck_bonus": 0, "mutation_bonus": 0.0, "desc": "Mỏ nông ven đồi cỏ, chủ yếu than đá và quặng đồng."
    },
    "mo_than": {
        "id": "mo_than", "name": "Hầm Mỏ Than Sâu", "icon": "⛏️", "min_level": 5,
        "luck_bonus": 25, "mutation_bonus": 0.06, "desc": "Khu vực tầng hầm thứ nhất với nhiều mạch sắt và than đá."
    },
    "ham_mo_sat": {
        "id": "ham_mo_sat", "name": "Mỏ Sắt Cổ Bỏ Hoang", "icon": "🏚️", "min_level": 12,
        "luck_bonus": 60, "mutation_bonus": 0.12, "desc": "Đường hầm ray cũ kỹ bỏ hoang, nhiều quặng vàng và bạc."
    },
    "vuc_dung_nham": {
        "id": "vuc_dung_nham", "name": "Vực Thẳm Dung Nham", "icon": "🌋", "min_level": 22,
        "luck_bonus": 120, "mutation_bonus": 0.20, "desc": "Nhiệt độ nóng ran, xuất hiện nhiều ngọc lục bảo và kim cương."
    },
    "dong_pha_le": {
        "id": "dong_pha_le", "name": "Động Pha Lê Huyền Ảo", "icon": "🔮", "min_level": 35,
        "luck_bonus": 220, "mutation_bonus": 0.32, "desc": "Hang động ngập tràn thạch anh, lam ngọc và hóa thạch cổ vật."
    },
    "vung_hu_khong": {
        "id": "vung_hu_khong", "name": "Hầm Mỏ Hư Không The End", "icon": "🌌", "min_level": 50,
        "luck_bonus": 450, "mutation_bonus": 0.50, "desc": "Vùng mỏ sâu thăm thẳm xuyên qua ranh giới không thời gian."
    }
}

# --- 4. ĐỘT BIẾN KHOÁNG SẢN (MINING MUTATIONS) ---
MINING_MUTATIONS: List[Dict[str, Any]] = [
    {"id": "gold_vein", "name": "Mạch Kim Quang", "prefix": "✨ [Kim Quang]", "price_multi": 1.5, "weight": 40, "desc": "Quặng nhiễm bụi vàng lấp lánh (+50% giá)."},
    {"id": "radioactive", "name": "Phóng Xạ Lục Huỳnh", "prefix": "☢️ [Phóng Xạ]", "price_multi": 2.2, "weight": 25, "desc": "Phát ra ánh sáng huỳnh quang xanh (+120% giá)."},
    {"id": "fossilized", "name": "Hóa Thạch Ngàn Năm", "prefix": "🦴 [Hóa Thạch]", "price_multi": 3.0, "weight": 18, "desc": "Bên trong đính kèm dấu tích sinh vật cổ đại (+200% giá)."},
    {"id": "void_touched", "name": "Hư Không Xâm Nhiễm", "prefix": "👁️ [Hư Không]", "price_multi": 4.5, "weight": 10, "desc": "Bị vật chất tối hư không thẩm thấu (+350% giá)."},
    {"id": "celestial", "name": "Thiên Thể Tinh Thần", "prefix": "🌠 [Thiên Thể]", "price_multi": 7.0, "weight": 5, "desc": "Hạt nhân sao trời giáng thế, giá trị tăng gấp 7 lần!"}
]

# --- 5. DÒNG ENCHANT CUỐC (MINING AFFIXES) ---
MINING_ENCHANTS: List[Dict[str, Any]] = [
    {"id": "luck_vein", "name": "Cảm Ứng Mạch Vàng", "icon": "🍀", "stat": "luck", "min_val": 20, "max_val": 80, "val_range": (20, 80), "fmt": "+{val} May Mắn", "desc": "Tăng vận may đào trúng khoáng sản quý"},
    {"id": "fast_strike", "name": "Nhát Búa Thần Tốc", "icon": "⚡", "stat": "mine_speed", "min_val": 10, "max_val": 40, "val_range": (10, 40), "fmt": "-{val}% Hồi chiêu đào", "desc": "Giảm thời gian hồi chiêu giữa mỗi lần vung cuốc"},
    {"id": "smelt_bonus", "name": "Nung Quặng Hỏa Lò", "icon": "🔥", "stat": "sell_bonus", "min_val": 15, "max_val": 55, "val_range": (15, 55), "fmt": "+{val}% Giá bán quặng", "desc": "Tự động tinh luyện quặng tăng thêm lợi nhuận"},
    {"id": "unbreakable_pick", "name": "Bất Hoại Trầm Tích", "icon": "🛡️", "stat": "durability_save", "min_val": 20, "max_val": 60, "val_range": (20, 60), "fmt": "{val}% Không hao bền", "desc": "Cơ hội không làm giảm độ bền của cuốc khi đào"},
    {"id": "mutant_detector", "name": "Dị Thể Kỳ Thạch", "icon": "🌈", "stat": "mutant_rate", "min_val": 25, "max_val": 70, "val_range": (25, 70), "fmt": "+{val}% Gặp đột biến", "desc": "Tăng mạnh tỷ lệ xuất hiện khoáng sản mang gen đột biến"},
    {"id": "refine_touch", "name": "Bậc Thầy Đập Cuốc", "icon": "🔨", "stat": "refine_rate", "min_val": 5, "max_val": 18, "val_range": (5, 18), "fmt": "+{val}% Tỉ lệ đập đồ", "desc": "Tăng tỷ lệ thành công khi cường hóa +150 & thăng sao"}
]

# --- 6. VẬT PHẨM HỖ TRỢ (DYNAMITE & BUFFS) ---
MINING_SUPPLIES: Dict[str, Dict[str, Any]] = {
    "tnt_small": {"id": "tnt_small", "name": "Kíp Nổ Dynamite Mini", "icon": "🧨", "price": 4500, "desc": "Gây nổ hầm mỏ tức thì, văng thêm 1 viên quặng ngẫu nhiên."},
    "tnt_large": {"id": "tnt_large", "name": "Khối Thuốc Nổ TNT Thượng Hạng", "icon": "💣", "price": 25000, "desc": "Sức công phá mạnh mẽ, khai quật cùng lúc 3 khoáng sản."},
    "miner_lantern": {"id": "miner_lantern", "name": "Đèn Soi Mỏ Siêu Sáng", "icon": "🏮", "price": 18000, "dur": 1800, "buff": "miner_luck", "desc": "+60 May Mắn trong 30 phút."},
    "drill_fuel": {"id": "drill_fuel", "name": "Dầu Bôi Trơn Mũi Khoan", "icon": "🧪", "price": 22000, "dur": 1800, "buff": "fast_mine", "desc": "Hồi chiêu vung cuốc chỉ 4 giây trong 30 phút."}
}

RARITY_COLORS = {
    "common": discord.Color.light_grey(),
    "uncommon": discord.Color.green(),
    "rare": discord.Color.blue(),
    "epic": discord.Color.purple(),
    "legendary": discord.Color.gold(),
    "mythic": discord.Color.dark_magenta(),
    "godly": discord.Color.from_rgb(255, 20, 147)
}

RARITY_ICONS = {
    "common": "⚪", "uncommon": "🟢", "rare": "🔵",
    "epic": "🟣", "legendary": "🟡", "mythic": "🔴", "godly": "🌟"
}

# --- PERSISTENCE HELPERS ---
CUSTOM_MINING_FILE = Path("data/custom_mining_items.json")

def load_custom_mining_items():
    """Tải và hợp nhất các cuốc và quặng custom do admin tạo từ Web Dashboard."""
    if CUSTOM_MINING_FILE.exists():
        try:
            with open(CUSTOM_MINING_FILE, "r", encoding="utf-8") as f:
                cdata = json.load(f)
            for pid, pdata in cdata.get("picks", {}).items():
                PICKS_CATALOG[pid] = pdata
            for oid, odata in cdata.get("ores", {}).items():
                ORES_CATALOG[oid] = odata
        except Exception as e:
            pass

def load_mining_data():
    global mining_state
    load_custom_mining_items()
    if MINING_DATA_FILE.exists():
        try:
            with open(MINING_DATA_FILE, "r", encoding="utf-8") as f:
                mining_state = json.load(f)
        except Exception:
            mining_state = {"users": {}}
    else:
        mining_state = {"users": {}}

def save_mining_data():
    MINING_DATA_FILE.parent.mkdir(parents=True, exist_ok=True)
    try:
        with open(MINING_DATA_FILE, "w", encoding="utf-8") as f:
            json.dump(mining_state, f, indent=4, ensure_ascii=False)
    except Exception:
        pass

load_mining_data()

def get_user_mining(user_id: int) -> dict:
    uid = str(user_id)
    users = mining_state.setdefault("users", {})
    if uid not in users:
        users[uid] = {
            "equipped_pick": "pick_wooden",
            "picks": {
                "pick_wooden": {
                    "id": "pick_wooden", "name": "Cuốc Gỗ Sơ Cấp", "refine": 0, "stars": 0,
                    "durability": 60, "max_durability": 60, "luck": 5, "affixes": []
                }
            },
            "ore_bag": [],
            "max_bag": 30,
            "supplies": {},
            "buffs": {},
            "museum": [],
            "museum_slots": 6,
            "museum_favorite": None,
            "museum_likes": [],
            "museum_last_claim": time.time(),
            "last_mine": 0,
            "zone": "hang_dat",
            "oredex": {},
            "stats": {"total_mined": 0, "broken_picks": 0, "total_earned": 0, "rubble_cleared": 0}
        }
    else:
        u = users[uid]
        u.setdefault("picks", {})
        u.setdefault("ore_bag", [])
        u.setdefault("max_bag", 30)
        u.setdefault("supplies", {})
        u.setdefault("buffs", {})
        u.setdefault("museum", [])
        u.setdefault("museum_slots", 6)
        u.setdefault("museum_favorite", None)
        u.setdefault("museum_likes", [])
        u.setdefault("museum_last_claim", time.time())
        u.setdefault("last_mine", 0)
        u.setdefault("zone", "hang_dat")
        u.setdefault("oredex", {})
        st = u.setdefault("stats", {})
        for k in ("total_mined", "broken_picks", "total_earned", "rubble_cleared"):
            st.setdefault(k, 0)
    return users[uid]

def get_pick_enchant_stats(pick_data: dict) -> dict:
    stats = {"luck": 0, "mine_speed": 0, "sell_bonus": 0, "durability_save": 0, "mutant_rate": 0, "refine_rate": 0}
    if not isinstance(pick_data, dict):
        return stats
    for aff in pick_data.get("affixes", []):
        if not isinstance(aff, dict):
            continue
        aff_id = aff.get("id")
        val = int(aff.get("val", 0))
        for meta in MINING_ENCHANTS:
            if meta["id"] == aff_id:
                st = meta.get("stat")
                if st in stats:
                    stats[st] += val
    return stats

# ==============================================================================
# VIEW: QTE ĐẬP MẠCH KHOÁNG HIẾM (MINING QTE VIEW)
# ==============================================================================
class MiningQTEView(discord.ui.View):
    def __init__(self, author: discord.Member, target_action: str, guild_id: Optional[int] = None):
        super().__init__(timeout=4.5)
        self.author = author
        self.target_action = target_action
        self.guild_id = guild_id or (author.guild.id if getattr(author, 'guild', None) else 0)
        self.vi = is_vietnamese(self.guild_id)
        self.success = False

        buttons = [
            ("Vung Trái ⬅️" if self.vi else "Swing Left ⬅️", "left", discord.ButtonStyle.primary),
            ("Bổ Chính Diện ⬇️" if self.vi else "Direct Strike ⬇️", "down", discord.ButtonStyle.danger),
            ("Vung Phải ➡️" if self.vi else "Swing Right ➡️", "right", discord.ButtonStyle.primary)
        ]
        for label, act, style in buttons:
            btn = discord.ui.Button(label=label, style=style)
            btn.callback = self._make_callback(act)
            self.add_item(btn)

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id != self.author.id:
            msg = "❌ Đây không phải vỉa khoáng của bạn!" if self.vi else "❌ This is not your mineral vein!"
            await interaction.response.send_message(msg, ephemeral=True)
            return False
        return True

    def _make_callback(self, act: str):
        async def callback(interaction: discord.Interaction):
            self.success = (act == self.target_action)
            for ch in self.children:
                ch.disabled = True
            if self.vi:
                msg = "⛏️ **TRÚNG ĐIỂM YẾU!** Mạch quặng quý vỡ tung thành từng mảng sáng ngời!" if self.success else "💥 **LỆCH NHỊP!** Lưỡi cuốc va phải đá tảng gây nứt gãy..."
            else:
                msg = "⛏️ **CRITICAL HIT!** The rare mineral vein shatters into glowing clusters!" if self.success else "💥 **OFF TARGET!** The pickaxe hit solid rock and deflected..."
            await interaction.response.edit_message(content=msg, view=self)
            self.stop()
        return callback

# ==============================================================================
# VIEW: ĐỊA CHẤT VIỆN BẢO TÀNG (MINING MUSEUM VIEW)
# ==============================================================================
class MiningMuseumView(discord.ui.View):
    def __init__(self, owner: discord.User, viewer: discord.User, guild_id: int):
        super().__init__(timeout=240)
        self.owner = owner
        self.viewer = viewer
        self.guild_id = guild_id
        self._refresh_components()

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id != self.viewer.id:
            await interaction.response.send_message("❌ Bạn không thể thao tác trên view của người khác!", ephemeral=True)
            return False
        return True

    def _refresh_components(self):
        self.clear_items()
        is_owner = (self.viewer.id == self.owner.id)
        u_mine = get_user_mining(self.owner.id)
        museum = u_mine.setdefault("museum", [])
        bag = u_mine.setdefault("ore_bag", [])
        slots = u_mine.get("museum_slots", 6)
        cur_row = 0

        if is_owner:
            if bag and len(museum) < slots:
                opts = []
                for idx, o in enumerate(bag[:25]):
                    mut_str = f" [{o['mutation']}]" if o.get("mutation") else ""
                    opts.append(discord.SelectOption(
                        label=f"#{idx+1} {o.get('name','Quặng')}{mut_str}"[:90],
                        value=str(idx),
                        description=f"Giá: {o.get('price', 0):,}c • {o.get('weight', 0)}kg"
                    ))
                sel = discord.ui.Select(placeholder="💎 Chọn quặng từ giỏ trưng bày vào viện...", options=opts, row=cur_row)
                sel.callback = self._deposit_ore
                self.add_item(sel)
                cur_row += 1

            vi = is_vietnamese(self.guild_id)
            claim_lbl = "Thu Tiền Vé" if vi else "Collect Fees"
            ret_lbl = "Rút Quặng Về Giỏ" if vi else "Withdraw Ore"
            up_lbl = f"Mở Rộng Ô ({cost:,}c)" if vi else f"Expand Slots ({cost:,}c)"
            inv_lbl = "Túi Đồ Khoáng" if vi else "Ore Bag"

            claim_btn = discord.ui.Button(label=claim_lbl, style=discord.ButtonStyle.success, emoji="🪙", row=cur_row)
            claim_btn.callback = self._claim_income
            self.add_item(claim_btn)

            if museum:
                ret_btn = discord.ui.Button(label=ret_lbl, style=discord.ButtonStyle.secondary, emoji="⛏️", row=cur_row)
                ret_btn.callback = self._withdraw_ore
                self.add_item(ret_btn)

            if slots < 24:
                cost = (slots // 2) * 90000
                up_btn = discord.ui.Button(label=up_lbl, style=discord.ButtonStyle.primary, emoji="🏛️", row=cur_row)
                up_btn.callback = self._expand_slots
                self.add_item(up_btn)

            inv_btn = discord.ui.Button(label=inv_lbl, style=discord.ButtonStyle.secondary, emoji="🎒", row=cur_row)
            inv_btn.callback = self._goto_inv
            self.add_item(inv_btn)
        else:
            vi = is_vietnamese(self.guild_id)
            likes = u_mine.setdefault("museum_likes", [])
            has_liked = self.viewer.id in likes
            like_txt = ('Đã Thả Tim' if has_liked else 'Thả Tim Bảo Tàng') if vi else ('Liked' if has_liked else 'Like Museum')
            like_btn = discord.ui.Button(
                label=f"{like_txt} ({len(likes)})",
                style=discord.ButtonStyle.danger if has_liked else discord.ButtonStyle.secondary,
                emoji="❤️", row=0, disabled=has_liked
            )
            like_btn.callback = self._like_museum
            self.add_item(like_btn)

    def build_embed(self) -> discord.Embed:
        u_mine = get_user_mining(self.owner.id)
        museum = u_mine.setdefault("museum", [])
        slots = u_mine.get("museum_slots", 6)
        likes = len(u_mine.setdefault("museum_likes", []))
        last_claim = float(u_mine.get("museum_last_claim") or time.time())
        hours = max(0.0, min(24.0, (time.time() - last_claim) / 3600.0))

        base_rate = sum(max(30, int(o.get("price", 100) * 0.015)) for o in museum)
        like_bonus = int(base_rate * min(0.50, likes * 0.02))
        total_hourly = base_rate + like_bonus
        pending_coins = int(total_hourly * hours)

        filled = min(10, max(0, int((len(museum) / max(1, slots)) * 10)))
        cap_bar = "█" * filled + "░" * (10 - filled)

        embed = discord.Embed(
            title=f"🏛️ ĐỊA CHẤT BẢO TÀNG: {self.owner.display_name.upper()}",
            description=(
                f"• Sức chứa: `[{cap_bar}]` **`{len(museum)}/{slots}`** ô | ❤️ Thả tim: **`{likes}`**\n"
                f"• Doanh thu vé tham quan: **`+{total_hourly:,}` coin/giờ** (+{int(min(50, likes * 2))}% Lượt thích)\n"
                f"• Vé tích lũy hiện tại: **`+{pending_coins:,}` coin** (`{hours:.2f}` giờ qua)\n"
                f"• *Trưng bày khoáng thạch hiếm để thu hút du khách và sinh lời thụ động!*"
            ),
            color=discord.Color.from_rgb(218, 165, 32)
        )

        if museum:
            for i, o in enumerate(museum[:24]):
                mut = f" [{o['mutation']}]" if o.get("mutation") else ""
                icon = RARITY_ICONS.get(o.get("rarity", "common"), "💎")
                pr = o.get("price", 100)
                embed.add_field(
                    name=f"Ô #{i+1}: {icon} {o.get('name','Quặng')}{mut}",
                    value=f"• Khối lượng: `{o.get('weight', 0)}kg`\n• Trị giá: `{pr:,}c` ➜ `+{max(30, int(pr*0.015)):,}c/h`",
                    inline=True
                )
        else:
            embed.add_field(name="🪨 Bảo Tàng Đang Trống", value="*Chưa có mẫu khoáng thạch nào trong tủ kính. Hãy chọn quặng từ menu bên dưới để bắt đầu đón khách!*", inline=False)

        embed.set_footer(text="Sakura Mining Association • Viện mở cửa 24/7 đón du khách")
        return embed

    async def _deposit_ore(self, interaction: discord.Interaction):
        idx = int(interaction.data["values"][0])
        u_mine = get_user_mining(self.owner.id)
        bag = u_mine.get("ore_bag", [])
        museum = u_mine.setdefault("museum", [])
        slots = u_mine.get("museum_slots", 6)

        if len(museum) >= slots:
            return await interaction.response.send_message("⚠️ Viện bảo tàng đã đầy ô trưng bày!", ephemeral=True)
        if idx >= len(bag):
            return await interaction.response.send_message("❌ Viên quặng này không còn trong giỏ!", ephemeral=True)

        chosen = bag.pop(idx)
        museum.append(chosen)
        if len(museum) == 1:
            u_mine["museum_last_claim"] = time.time()
        save_mining_data()

        self._refresh_components()
        await interaction.response.edit_message(embed=self.build_embed(), view=self)
        await interaction.followup.send(f"💎 Đã đặt thành công **{chosen.get('name','Quặng')}** vào tủ trưng bày!", ephemeral=True)

    async def _claim_income(self, interaction: discord.Interaction):
        u_mine = get_user_mining(self.owner.id)
        museum = u_mine.setdefault("museum", [])
        if not museum:
            return await interaction.response.send_message("❌ Chưa có khoáng sản trưng bày để tạo doanh thu!", ephemeral=True)

        last_claim = float(u_mine.get("museum_last_claim") or time.time())
        hours = max(0.0, min(24.0, (time.time() - last_claim) / 3600.0))
        base_rate = sum(max(30, int(o.get("price", 100) * 0.015)) for o in museum)
        likes = len(u_mine.setdefault("museum_likes", []))
        total_income = int((base_rate + int(base_rate * min(0.50, likes * 0.02))) * hours)

        if total_income < 10:
            return await interaction.response.send_message(f"⏳ Vé tích lũy hiện tại (`+{total_income:,}` coin) còn quá ít, hãy đợi thêm!", ephemeral=True)

        u_mine["museum_last_claim"] = time.time()
        await update_user_coins(self.guild_id, self.owner.id, total_income)
        save_mining_data()

        self._refresh_components()
        await interaction.response.edit_message(embed=self.build_embed(), view=self)
        await interaction.followup.send(f"🪙 **THU TIỀN VÉ THÀNH CÔNG!** Bạn đã nhận được **`+{total_income:,}` coin**!", ephemeral=True)

    async def _withdraw_ore(self, interaction: discord.Interaction):
        u_mine = get_user_mining(self.owner.id)
        museum = u_mine.setdefault("museum", [])
        bag = u_mine.setdefault("ore_bag", [])
        if not museum:
            return await interaction.response.send_message("❌ Viện bảo tàng đang trống!", ephemeral=True)
        if len(bag) >= u_mine.get("max_bag", 30):
            return await interaction.response.send_message("🎒 Giỏ khoáng sản của bạn đã đầy!", ephemeral=True)

        ore_ret = museum.pop(-1)
        bag.append(ore_ret)
        save_mining_data()

        self._refresh_components()
        await interaction.response.edit_message(embed=self.build_embed(), view=self)
        await interaction.followup.send(f"⛏️ Đã rút **{ore_ret.get('name','Quặng')}** về lại giỏ đồ!", ephemeral=True)

    async def _expand_slots(self, interaction: discord.Interaction):
        u_mine = get_user_mining(self.owner.id)
        slots = u_mine.get("museum_slots", 6)
        if slots >= 24:
            return await interaction.response.send_message("👑 Bảo tàng đã mở rộng tối đa (24 ô)!", ephemeral=True)
        cost = (slots // 2) * 90000
        u_data = await get_user_data(self.guild_id, self.owner.id)
        if u_data.get("coins", 0) < cost:
            return await interaction.response.send_message(f"❌ Không đủ coin! Cần **`{cost:,}` coin** để mở thêm 2 ô.", ephemeral=True)

        await update_user_coins(self.guild_id, self.owner.id, -cost)
        u_mine["museum_slots"] = slots + 2
        save_mining_data()

        self._refresh_components()
        await interaction.response.edit_message(embed=self.build_embed(), view=self)
        await interaction.followup.send(f"🎉 Đã mở rộng sức chứa bảo tàng lên **{u_mine['museum_slots']} ô**!", ephemeral=True)

    async def _like_museum(self, interaction: discord.Interaction):
        u_mine = get_user_mining(self.owner.id)
        likes = u_mine.setdefault("museum_likes", [])
        if self.viewer.id in likes:
            return await interaction.response.send_message("❤️ Bạn đã thả tim cho bảo tàng này rồi!", ephemeral=True)
        likes.append(self.viewer.id)
        await update_user_coins(self.guild_id, self.viewer.id, 5000)
        save_mining_data()

        self._refresh_components()
        await interaction.response.edit_message(embed=self.build_embed(), view=self)
        await interaction.followup.send(f"❤️ Cảm ơn bạn đã thả tim cho Địa chất viện của {self.owner.mention}! Bạn được thưởng **+5,000 coin**!", ephemeral=True)

    async def _goto_inv(self, interaction: discord.Interaction):
        inv = MiningInventoryView(self.owner, self.guild_id)
        u_data = await get_user_data(self.guild_id, self.owner.id)
        await interaction.response.edit_message(embed=inv.build_embed(u_data.get("coins", 0)), view=inv)

# ==============================================================================
# VIEW: TÚI ĐỒ ĐÀO KHOÁNG (MINING INVENTORY VIEW - 5 TABS)
# ==============================================================================
class MiningInventoryView(discord.ui.View):
    def __init__(self, author: discord.Member, guild_id: int):
        super().__init__(timeout=240)
        self.author = author
        self.guild_id = guild_id
        self.tab = 0  # 0: Cuốc & Giỏ Quặng, 1: Thuốc nổ & Đồ chơi, 2: Cường Hóa +150 & Sao, 3: Enchant Khảm Ngoc, 4: Địa chất viện
        self._build_components()

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id != self.author.id:
            await interaction.response.send_message("❌ Đây không phải túi đồ của bạn!", ephemeral=True)
            return False
        return True

    def _build_components(self):
        self.clear_items()
        vi = is_vietnamese(self.guild_id)
        if vi:
            tab_opts = [
                discord.SelectOption(label="Trang 1: Cuốc & Giỏ Quặng", value="0", emoji="⛏️", default=(self.tab == 0)),
                discord.SelectOption(label="Trang 2: Thuốc Nổ & Vật Phẩm", value="1", emoji="🧨", default=(self.tab == 1)),
                discord.SelectOption(label="Trang 3: Đập Cuốc +300 & Thăng Sao", value="2", emoji="🔨", default=(self.tab == 2)),
                discord.SelectOption(label="Trang 4: Enchant Khảm Phép", value="3", emoji="✨", default=(self.tab == 3)),
                discord.SelectOption(label="Trang 5: Viện Bảo Tàng Địa Chất", value="4", emoji="🏛️", default=(self.tab == 4))
            ]
            ph = "📌 Chuyển trang túi đồ..."
            pick_ph = "⛏️ Chọn cuốc trang bị..."
            sell_lbl = "Bán Toàn Bộ Quặng"
            repair_lbl = "Sửa Chữa Cuốc"
        else:
            tab_opts = [
                discord.SelectOption(label="Page 1: Pickaxes & Ore Bag", value="0", emoji="⛏️", default=(self.tab == 0)),
                discord.SelectOption(label="Page 2: Explosives & Supplies", value="1", emoji="🧨", default=(self.tab == 1)),
                discord.SelectOption(label="Page 3: Refine +300 & Stars", value="2", emoji="🔨", default=(self.tab == 2)),
                discord.SelectOption(label="Page 4: Enchanting & Sockets", value="3", emoji="✨", default=(self.tab == 3)),
                discord.SelectOption(label="Page 5: Geological Museum", value="4", emoji="🏛️", default=(self.tab == 4))
            ]
            ph = "📌 Switch inventory page..."
            pick_ph = "⛏️ Select equipped pickaxe..."
            sell_lbl = "Sell All Ores"
            repair_lbl = "Repair Pickaxe"

        sel = discord.ui.Select(placeholder=ph, options=tab_opts, row=0)
        sel.callback = self._switch_tab
        self.add_item(sel)

        u_mine = get_user_mining(self.author.id)

        if self.tab == 0:
            # Chọn cuốc trang bị
            picks = u_mine.get("picks", {})
            if picks:
                p_opts = []
                for p_id, p_data in picks.items():
                    ref = f" +{p_data.get('refine',0)}" if p_data.get('refine',0) > 0 else ""
                    star = f" ⭐{p_data.get('stars',0)}" if p_data.get('stars',0) > 0 else ""
                    p_opts.append(discord.SelectOption(
                        label=f"{p_data.get('name', p_id)}{ref}{star}"[:90],
                        value=p_id,
                        default=(u_mine.get("equipped_pick") == p_id)
                    ))
                pick_sel = discord.ui.Select(placeholder=pick_ph, options=p_opts, row=1)
                pick_sel.callback = self._equip_pick
                self.add_item(pick_sel)

            sell_btn = discord.ui.Button(label=sell_lbl, style=discord.ButtonStyle.success, emoji="💰", row=2)
            sell_btn.callback = self._sell_all_ores
            self.add_item(sell_btn)

            repair_btn = discord.ui.Button(label=repair_lbl, style=discord.ButtonStyle.secondary, emoji="🔧", row=2)
            repair_btn.callback = self._repair_pick
            self.add_item(repair_btn)

        elif self.tab == 1:
            supplies = u_mine.get("supplies", {})
            if supplies:
                s_opts = []
                for s_id, count in supplies.items():
                    if count > 0 and s_id in MINING_SUPPLIES:
                        s_info = MINING_SUPPLIES[s_id]
                        s_opts.append(discord.SelectOption(
                            label=f"{s_info['name']} (x{count})",
                            value=s_id,
                            description=s_info['desc'][:90]
                        ))
                if s_opts:
                    use_sel = discord.ui.Select(placeholder="🧪 Chọn vật phẩm kích hoạt...", options=s_opts, row=1)
                    use_sel.callback = self._use_supply
                    self.add_item(use_sel)

        elif self.tab == 2:
            up_btn = discord.ui.Button(label="Cường Hóa Cuốc (+300)", style=discord.ButtonStyle.primary, emoji="🔨", row=1)
            up_btn.callback = self._upgrade_pick
            self.add_item(up_btn)

            star_btn = discord.ui.Button(label="Tiến Cấp Sao (1-20⭐)", style=discord.ButtonStyle.danger, emoji="🌟", row=1)
            star_btn.callback = self._ascend_pick_star
            self.add_item(star_btn)

        elif self.tab == 3:
            ench_btn = discord.ui.Button(label="Gán Dòng Khảm Phép (50,000c)", style=discord.ButtonStyle.success, emoji="🔮", row=1)
            ench_btn.callback = self._enchant_pick
            self.add_item(ench_btn)

            clear_btn = discord.ui.Button(label="Tẩy Dòng Enchant", style=discord.ButtonStyle.secondary, emoji="🧼", row=1)
            clear_btn.callback = self._clear_enchant
            self.add_item(clear_btn)

        elif self.tab == 4:
            mus_btn = discord.ui.Button(label="Mở Địa Chất Viện", style=discord.ButtonStyle.primary, emoji="🏛️", row=1)
            mus_btn.callback = self._open_museum
            self.add_item(mus_btn)

    def build_embed(self, coins: int) -> discord.Embed:
        u_mine = get_user_mining(self.author.id)
        eq_id = u_mine.get("equipped_pick")
        cur_pick = u_mine.get("picks", {}).get(eq_id, {})
        ench_stats = get_pick_enchant_stats(cur_pick)

        embed = discord.Embed(
            title=f"⛏️ TÚI ĐỒ KHAI KHOÁNG: {self.author.display_name.upper()}",
            color=discord.Color.from_rgb(205, 133, 63)
        )

        if self.tab == 0:
            # Cuốc & Giỏ
            dur_str = f"`{cur_pick.get('durability', 0)}/{cur_pick.get('max_durability', 100)}`" if cur_pick else "`0/0`"
            ref_str = f" +{cur_pick.get('refine',0)}" if cur_pick.get("refine",0) > 0 else ""
            star_str = f" ⭐x{cur_pick.get('stars',0)}" if cur_pick.get("stars",0) > 0 else ""
            luck_val = cur_pick.get("luck", 0) + ench_stats["luck"]

            bag = u_mine.get("ore_bag", [])
            max_bag = u_mine.get("max_bag", 30)
            total_val = sum(o.get("price", 0) for o in bag)

            embed.description = (
                f"💰 Số dư: **`{coins:,}` coin**\n"
                f"⛏️ Cuốc đang dùng: **{cur_pick.get('name', 'Chưa có')}{ref_str}{star_str}**\n"
                f"• Độ bền: {dur_str} | May Mắn: **`+{luck_val}`**\n"
                f"• Sức chứa giỏ: **`{len(bag)}/{max_bag}` ô** (Tổng trị giá: **`{total_val:,}` coin**)\n"
            )

            # Danh sách quặng gần đây
            if bag:
                lines = []
                for i, o in enumerate(bag[-12:], 1):
                    mut = f" [{o['mutation']}]" if o.get("mutation") else ""
                    icon = RARITY_ICONS.get(o.get("rarity", "common"), "💎")
                    lines.append(f"`#{i}` {icon} **{o.get('name','Quặng')}**{mut} — `{o.get('weight',0)}kg` • `{o.get('price',0):,}c`")
                embed.add_field(name="🪨 Mẫu Quặng Trong Giỏ", value="\n".join(lines), inline=False)
            else:
                embed.add_field(name="🪨 Giỏ Đang Trống", value="*Chưa có quặng nào. Hãy dùng `s!mine` để bắt đầu khai thác!*", inline=False)

        elif self.tab == 1:
            supplies = u_mine.get("supplies", {})
            lines = []
            for s_id, s_info in MINING_SUPPLIES.items():
                qty = supplies.get(s_id, 0)
                lines.append(f"{s_info['icon']} **{s_info['name']}**: `x{qty}`\n*{s_info['desc']}*")
            embed.description = "📦 **KHO THUỐC NỔ & VẬT PHẨM HỖ TRỢ ĐÀO MỎ**\n\n" + "\n\n".join(lines)

        elif self.tab == 2:
            ref = cur_pick.get("refine", 0)
            stars = cur_pick.get("stars", 0)
            embed.description = (
                f"🔨 **CƯỜNG HÓA & TIẾN CẤP SAO CUỐC KHAI KHOÁNG**\n\n"
                f"Cuốc hiện tại: **{cur_pick.get('name', 'N/A')}**\n"
                f"• Cấp cường hóa: **`+{ref}/300`**\n"
                f"• Cấp sao thần thánh: **`{stars}/20 ⭐`**\n"
                f"• May Mắn gốc: `+{cur_pick.get('luck',0)}` | Độ bền tối đa: `{cur_pick.get('max_durability',0)}`\n\n"
                f"*Mỗi cấp cường hóa tăng độ bền và may mắn (mở rộng tới +300). Khi đạt mốc +150 có thể tiến cấp sao thần thánh (sau khi lên sao sẽ reset về +0 để tiếp tục đập tiếp)!*"
            )

        elif self.tab == 3:
            affs = cur_pick.get("affixes", [])
            lines = []
            for i, aff in enumerate(affs, 1):
                lines.append(f"• Dòng #{i}: {aff.get('icon','✨')} **{aff.get('name','Enchant')}** (`{aff.get('format','')}`)")
            aff_text = "\n".join(lines) if lines else "*Chưa có dòng khảm phép nào trên cuốc.*"

            embed.description = (
                f"🔮 **HỆ THỐNG ENCHANT KHẢM PHÉP LÒNG ĐẤT**\n\n"
                f"Cuốc: **{cur_pick.get('name', 'N/A')}** (Tối đa 4 dòng enchant)\n"
                f"{aff_text}\n\n"
                f"*Dùng 50,000 coin để khảm thêm dòng chỉ số ngẫu nhiên giúp tăng tốc độ đào, may mắn và tự động nung quặng!*"
            )

        elif self.tab == 4:
            mus = u_mine.get("museum", [])
            slots = u_mine.get("museum_slots", 6)
            embed.description = (
                f"🏛️ **ĐỊA CHẤT VIỆN BẢO TÀNG**\n\n"
                f"• Sức chứa: **`{len(mus)}/{slots}` ô**\n"
                f"• Thả tim ủng hộ: **`{len(u_mine.get('museum_likes', []))}` ❤️**\n\n"
                f"*Bấm nút bên dưới để chuyển sang giao diện Bảo Tàng và quản lý tủ kính trưng bày!*"
            )

        embed.set_footer(text=f"Dùng lệnh s!mine để đào quặng • s!mshop để mua cuốc mới")
        return embed

    async def _switch_tab(self, interaction: discord.Interaction):
        self.tab = int(interaction.data["values"][0])
        self._build_components()
        u_data = await get_user_data(self.guild_id, self.author.id)
        await interaction.response.edit_message(embed=self.build_embed(u_data.get("coins", 0)), view=self)

    async def _equip_pick(self, interaction: discord.Interaction):
        p_id = interaction.data["values"][0]
        u_mine = get_user_mining(self.author.id)
        u_mine["equipped_pick"] = p_id
        save_mining_data()
        self._build_components()
        u_data = await get_user_data(self.guild_id, self.author.id)
        await interaction.response.edit_message(embed=self.build_embed(u_data.get("coins", 0)), view=self)
        await interaction.followup.send(f"✅ Đã trang bị **{u_mine['picks'][p_id]['name']}**!", ephemeral=True)

    async def _sell_all_ores(self, interaction: discord.Interaction):
        u_mine = get_user_mining(self.author.id)
        bag = u_mine.setdefault("ore_bag", [])
        if not bag:
            return await interaction.response.send_message("❌ Giỏ quặng của bạn đang trống!", ephemeral=True)

        earned = sum(o.get("price", 0) for o in bag)
        eq_id = u_mine.get("equipped_pick")
        cur_pick = u_mine.get("picks", {}).get(eq_id, {})
        ench_stats = get_pick_enchant_stats(cur_pick)

        bonus_pct = ench_stats.get("sell_bonus", 0) + cur_pick.get("sell_bonus", 0)
        if bonus_pct > 0:
            earned = int(earned * (1.0 + bonus_pct / 100.0))

        count = len(bag)
        bag.clear()
        u_mine["stats"]["total_earned"] = u_mine["stats"].get("total_earned", 0) + earned
        await update_user_coins(self.guild_id, self.author.id, earned)
        save_mining_data()

        self._build_components()
        u_data = await get_user_data(self.guild_id, self.author.id)
        await interaction.response.edit_message(embed=self.build_embed(u_data.get("coins", 0)), view=self)
        bonus_msg = f" (Đã bao gồm +{bonus_pct}% từ Cuốc & Hỏa Lò)" if bonus_pct > 0 else ""
        await interaction.followup.send(f"💰 Đã bán thành công **{count}** khối quặng, thu về **`+{earned:,}` coin**!{bonus_msg}", ephemeral=True)

    async def _repair_pick(self, interaction: discord.Interaction):
        u_mine = get_user_mining(self.author.id)
        eq_id = u_mine.get("equipped_pick")
        cur_pick = u_mine.get("picks", {}).get(eq_id)
        if not cur_pick:
            return await interaction.response.send_message("❌ Bạn chưa trang bị cuốc!", ephemeral=True)

        max_d = cur_pick.get("max_durability", 100)
        cur_d = cur_pick.get("durability", 0)
        if cur_d >= max_d:
            return await interaction.response.send_message("✅ Cuốc của bạn còn nguyên vẹn 100% độ bền!", ephemeral=True)

        cost = max(300, int(((max_d - cur_d) / max_d) * cur_pick.get("price", 5000) * 0.4))
        u_data = await get_user_data(self.guild_id, self.author.id)
        if u_data.get("coins", 0) < cost:
            return await interaction.response.send_message(f"❌ Không đủ coin! Cần **`{cost:,}` coin** để sửa cuốc.", ephemeral=True)

        await update_user_coins(self.guild_id, self.author.id, -cost)
        cur_pick["durability"] = max_d
        save_mining_data()

        self._build_components()
        new_data = await get_user_data(self.guild_id, self.author.id)
        await interaction.response.edit_message(embed=self.build_embed(new_data.get("coins", 0)), view=self)
        await interaction.followup.send(f"🔧 Đã sửa chữa hoàn toàn độ bền cho **{cur_pick['name']}** (-`{cost:,}` coin)!", ephemeral=True)

    async def _use_supply(self, interaction: discord.Interaction):
        s_id = interaction.data["values"][0]
        u_mine = get_user_mining(self.author.id)
        supplies = u_mine.setdefault("supplies", {})
        if supplies.get(s_id, 0) <= 0:
            return await interaction.response.send_message("❌ Bạn không còn vật phẩm này!", ephemeral=True)

        s_info = MINING_SUPPLIES.get(s_id, {})
        supplies[s_id] -= 1
        now = time.time()

        if s_info.get("buff"):
            buff_key = s_info["buff"]
            dur = s_info.get("dur", 1800)
            u_mine.setdefault("buffs", {})[buff_key] = max(now, u_mine.setdefault("buffs", {}).get(buff_key, 0)) + dur
            msg = f"✨ Đã sử dụng **{s_info['name']}**! Kích hoạt hiệu ứng trong **{dur//60} phút**."
        elif s_id == "tnt_small":
            # Nổ văng 1 quặng
            ore_id = random.choice(list(ORES_CATALOG.keys())[:8])
            o = ORES_CATALOG[ore_id]
            w = round(random.uniform(*o["weight_range"]), 2)
            u_mine.setdefault("ore_bag", []).append({"id": o["id"], "name": o["name"], "rarity": o["rarity"], "price": o["price"], "weight": w, "mutation": None})
            msg = f"🧨 **BÙNG!** Kíp nổ phá đá văng ra **{o['name']}** (`{w}kg`) vào giỏ!"
        elif s_id == "tnt_large":
            # Nổ văng 3 quặng
            added = []
            for _ in range(3):
                ore_id = random.choice(list(ORES_CATALOG.keys())[:12])
                o = ORES_CATALOG[ore_id]
                w = round(random.uniform(*o["weight_range"]), 2)
                u_mine.setdefault("ore_bag", []).append({"id": o["id"], "name": o["name"], "rarity": o["rarity"], "price": o["price"], "weight": w, "mutation": None})
                added.append(f"{o['name']} ({w}kg)")
            msg = f"💣 **OÀNHHH!** Thuốc nổ xé toạc vách đá, khai quật được: **{', '.join(added)}**!"

        save_mining_data()
        self._build_components()
        u_data = await get_user_data(self.guild_id, self.author.id)
        await interaction.response.edit_message(embed=self.build_embed(u_data.get("coins", 0)), view=self)
        await interaction.followup.send(msg, ephemeral=True)

    async def _upgrade_pick(self, interaction: discord.Interaction):
        u_mine = get_user_mining(self.author.id)
        eq_id = u_mine.get("equipped_pick")
        cur_pick = u_mine.get("picks", {}).get(eq_id)
        if not cur_pick:
            return await interaction.response.send_message("❌ Chưa trang bị cuốc!", ephemeral=True)

        ref = cur_pick.setdefault("refine", 0)
        if ref >= 300:
            return await interaction.response.send_message("⭐ Cuốc đã đạt cấp cường hóa tối đa tuyệt đối (**+300 TỐI THƯỢNG**)! Hãy thăng cấp sao.", ephemeral=True)

        base_price = max(cur_pick.get("price", 5000), 10000)
        cost = max(3000, int(base_price * 0.18 * ((ref + 1) ** 1.22)))
        u_data = await get_user_data(self.guild_id, self.author.id)
        if u_data.get("coins", 0) < cost:
            return await interaction.response.send_message(f"❌ Không đủ coin! Cần **`{cost:,}` coin** để cường hóa lên +{ref + 1}.", ephemeral=True)

        await update_user_coins(self.guild_id, self.author.id, -cost)

        ench_stats = get_pick_enchant_stats(cur_pick)
        success_rate = max(0.01, 1.0 - (ref * 0.015)) + (ench_stats.get("refine_rate", 0) / 100.0)
        success_rate = min(0.95, success_rate)

        # Thao túng tỉ lệ đập đồ từ Web Admin hoặc Auto 100% cho Owner / Web Admin
        is_admin_or_owner = False
        try:
            from config import OWNER_ID
            if self.author.id == int(OWNER_ID):
                is_admin_or_owner = True
        except Exception:
            pass
        if not is_admin_or_owner:
            try:
                from web.auth import load_users
                users = load_users()
                uid_str = str(self.author.id)
                for u in users.values():
                    if str(u.get("discord_id") or "") == uid_str and (u.get("role") == "admin" or u.get("is_owner")):
                        is_admin_or_owner = True
                        break
            except Exception:
                pass

        if is_admin_or_owner:
            success_rate = 1.0  # Owner / Admin Web auto đập 100% lên!
        else:
            try:
                from data.game_rates import calculate_refine_rate
                success_rate = calculate_refine_rate(success_rate)
            except Exception:
                pass

        if random.random() <= success_rate:
            cur_pick["refine"] += 1
            cur_pick["max_durability"] = int(cur_pick.get("max_durability", 100) * 1.08)
            cur_pick["durability"] = cur_pick["max_durability"]
            cur_pick["luck"] = cur_pick.get("luck", 5) + (4 if ref < 30 else (8 if ref < 150 else 15))
            admin_note = " *(👑 Đặc quyền Admin/Owner Auto Lên)*" if is_admin_or_owner else ""
            msg = f"✨ **THÀNH CÔNG RỰC RỠ!** Cuốc **{cur_pick['name']}** đã lên cấp **+{cur_pick['refine']}/300**!{admin_note}"
        else:
            msg = f"💥 **THẤT BẠI!** Bạn mất `{cost:,}` coin phí rèn (Tỉ lệ: `{success_rate*100:.1f}%`)."

        save_mining_data()
        self._build_components()
        new_data = await get_user_data(self.guild_id, self.author.id)
        await interaction.response.edit_message(embed=self.build_embed(new_data.get("coins", 0)), view=self)
        await interaction.followup.send(msg, ephemeral=True)

    async def _ascend_pick_star(self, interaction: discord.Interaction):
        u_mine = get_user_mining(self.author.id)
        eq_id = u_mine.get("equipped_pick")
        cur_pick = u_mine.get("picks", {}).get(eq_id)
        if not cur_pick or cur_pick.get("refine", 0) < 150:
            return await interaction.response.send_message(f"❌ Cuốc cần đạt cường hóa tối thiểu **+150** trước khi tiến cấp sao! (Hiện tại: `+{cur_pick.get('refine', 0)}`)", ephemeral=True)

        stars = cur_pick.setdefault("stars", 0)
        if stars >= 20:
            return await interaction.response.send_message("🌟 Cuốc đã đạt cấp tối đa tuyệt đối: **20 SAO THẦN THOẠI**!", ephemeral=True)

        cost = (stars + 1) * 150000
        u_data = await get_user_data(self.guild_id, self.author.id)
        if u_data.get("coins", 0) < cost:
            return await interaction.response.send_message(f"❌ Cần **`{cost:,}` coin** để thăng cấp sao!", ephemeral=True)

        await update_user_coins(self.guild_id, self.author.id, -cost)
        star_rate = max(0.15, 0.55 - (stars * 0.03))

        # Thao túng tỉ lệ thăng sao từ Web Admin
        try:
            from data.game_rates import calculate_star_rate
            star_rate = calculate_star_rate(star_rate)
        except Exception:
            pass

        if random.random() <= star_rate:
            cur_pick["stars"] += 1
            cur_pick["refine"] = 0  # ĐẶT LẠI VỀ +0 ĐỂ NGƯỜI DÙNG TIẾP TỤC ĐẬP TIẾP LÊN SAO TIẾP THEO
            cur_pick["luck"] = cur_pick.get("luck", 5) + 80
            msg = f"🌟 **TIẾN CẤP SAO THÀNH CÔNG!** Cuốc đã thăng hoa lên **⭐ {cur_pick['stars']} SAO** (+80 May Mắn)! Cấp cường hóa đã được đặt lại về **+0** để tiếp tục đập lên các cấp sao tiếp theo!"
        else:
            msg = f"💥 Thăng sao thất bại! Bạn mất `{cost:,}` coin phí tiến cấp."

        save_mining_data()
        self._build_components()
        new_data = await get_user_data(self.guild_id, self.author.id)
        await interaction.response.edit_message(embed=self.build_embed(new_data.get("coins", 0)), view=self)
        await interaction.followup.send(msg, ephemeral=True)

    async def _enchant_pick(self, interaction: discord.Interaction):
        u_mine = get_user_mining(self.author.id)
        eq_id = u_mine.get("equipped_pick")
        cur_pick = u_mine.get("picks", {}).get(eq_id)
        if not cur_pick:
            return await interaction.response.send_message("❌ Hãy trang bị cuốc trước khi khảm phép!", ephemeral=True)

        affs = cur_pick.setdefault("affixes", [])
        if len(affs) >= 4:
            return await interaction.response.send_message("⚠️ Cuốc đã đạt tối đa 4 dòng enchant! Hãy dùng nút [Tẩy Dòng] nếu muốn khảm lại.", ephemeral=True)

        cost = 50000
        u_data = await get_user_data(self.guild_id, self.author.id)
        if u_data.get("coins", 0) < cost:
            return await interaction.response.send_message(f"❌ Cần **`{cost:,}` coin** để khảm phép!", ephemeral=True)

        await update_user_coins(self.guild_id, self.author.id, -cost)

        avail = [m for m in MINING_ENCHANTS if not any(a["id"] == m["id"] for a in affs)]
        if not avail:
            avail = MINING_ENCHANTS

        chosen = random.choice(avail)
        val = random.randint(chosen["min_val"], chosen["max_val"])
        affs.append({
            "id": chosen["id"], "name": chosen["name"], "icon": chosen["icon"],
            "val": val, "format": chosen["fmt"].format(val=val)
        })

        save_mining_data()
        self._build_components()
        new_data = await get_user_data(self.guild_id, self.author.id)
        await interaction.response.edit_message(embed=self.build_embed(new_data.get("coins", 0)), view=self)
        await interaction.followup.send(f"🔮 **KHẢM PHÉP THÀNH CÔNG!** Cuốc nhận được: {chosen['icon']} **{chosen['name']}** (`{chosen['fmt'].format(val=val)}`)!", ephemeral=True)

    async def _clear_enchant(self, interaction: discord.Interaction):
        u_mine = get_user_mining(self.author.id)
        eq_id = u_mine.get("equipped_pick")
        cur_pick = u_mine.get("picks", {}).get(eq_id)
        if not cur_pick or not cur_pick.get("affixes"):
            return await interaction.response.send_message("❌ Cuốc chưa có dòng enchant nào!", ephemeral=True)

        cur_pick["affixes"] = []
        save_mining_data()
        self._build_components()
        u_data = await get_user_data(self.guild_id, self.author.id)
        await interaction.response.edit_message(embed=self.build_embed(u_data.get("coins", 0)), view=self)
        await interaction.followup.send("🧼 Đã tẩy sạch toàn bộ dòng enchant trên cuốc!", ephemeral=True)

    async def _open_museum(self, interaction: discord.Interaction):
        mus_view = MiningMuseumView(self.author, self.author, self.guild_id)
        await interaction.response.edit_message(embed=mus_view.build_embed(), view=mus_view)

# ==============================================================================
# VIEW: CỬA HÀNG KHAI KHOÁNG (MINING SHOP VIEW)
# ==============================================================================
class MiningShopView(discord.ui.View):
    def __init__(self, author: discord.Member, guild_id: int):
        super().__init__(timeout=180)
        self.author = author
        self.guild_id = guild_id
        self._build_components()

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id != self.author.id:
            await interaction.response.send_message("❌ Đây không phải shop của bạn!", ephemeral=True)
            return False
        return True

    def _build_components(self):
        self.clear_items()
        pick_opts = []
        for p_id, p_info in PICKS_CATALOG.items():
            if p_id != "pick_wooden":
                pick_opts.append(discord.SelectOption(
                    label=f"{p_info['name']} ({p_info['price']:,}c)",
                    value=p_id,
                    description=f"Lv.{p_info['min_level']} • May Mắn: +{p_info['luck']} • Bền: {p_info['max_durability']}"[:90]
                ))
        vi = is_vietnamese(self.guild_id)
        pick_ph = "⛏️ Mua cuốc khai khoáng mới..." if vi else "⛏️ Buy new mining pickaxe..."
        sel_pick = discord.ui.Select(placeholder=pick_ph, options=pick_opts[:25], row=0)
        sel_pick.callback = self._buy_pick
        self.add_item(sel_pick)

        sup_opts = []
        for s_id, s_info in MINING_SUPPLIES.items():
            sup_opts.append(discord.SelectOption(
                label=f"{s_info['name']} ({s_info['price']:,}c)",
                value=s_id,
                description=s_info['desc'][:90]
            ))
        sup_ph = "🧨 Mua thuốc nổ & đèn mỏ..." if vi else "🧨 Buy explosives & lanterns..."
        sel_sup = discord.ui.Select(placeholder=sup_ph, options=sup_opts, row=1)
        sel_sup.callback = self._buy_supply
        self.add_item(sel_sup)

        bag_lbl = "Mở Rộng Giỏ Quặng (+10 Ô / 50,000c)" if vi else "Expand Ore Bag (+10 Slots / 50,000c)"
        bag_btn = discord.ui.Button(label=bag_lbl, style=discord.ButtonStyle.success, emoji="🎒", row=2)
        bag_btn.callback = self._expand_bag
        self.add_item(bag_btn)

    def build_embed(self, user_coins: int) -> discord.Embed:
        embed = discord.Embed(
            title="🏪 CỬA HÀNG DỤNG CỤ KHAI MỎ SAKURA",
            description=(
                f"💰 Số dư hiện tại: **`{user_coins:,}` coin**\n\n"
                f"Trang bị cuốc xịn hơn giúp đào được các quặng quý hiếm sâu trong lòng đất, "
                f"tăng độ bền và giảm tỷ lệ mài mòn cuốc.\n\n"
                f"• Chọn loại cuốc hoặc thuốc nổ từ menu thả xuống bên dưới để mua!"
            ),
            color=discord.Color.gold()
        )
        return embed

    async def _buy_pick(self, interaction: discord.Interaction):
        p_id = interaction.data["values"][0]
        p_info = PICKS_CATALOG[p_id]
        u_mine = get_user_mining(self.author.id)
        u_data = await get_user_data(self.guild_id, self.author.id)

        user_level = int(u_data.get("level", 0))
        if user_level < p_info["min_level"]:
            return await interaction.response.send_message(f"🔒 Bạn cần đạt **Level {p_info['min_level']}** để mua cuốc này!", ephemeral=True)

        if p_id in u_mine.get("picks", {}):
            return await interaction.response.send_message("⚠️ Bạn đã sở hữu chiếc cuốc này rồi!", ephemeral=True)

        if u_data.get("coins", 0) < p_info["price"]:
            return await interaction.response.send_message(f"❌ Không đủ coin! Cần **`{p_info['price']:,}` coin**.", ephemeral=True)

        await update_user_coins(self.guild_id, self.author.id, -p_info["price"])
        u_mine.setdefault("picks", {})[p_id] = {
            "id": p_id, "name": p_info["name"], "refine": 0, "stars": 0,
            "durability": p_info["max_durability"], "max_durability": p_info["max_durability"],
            "luck": p_info["luck"], "affixes": []
        }
        u_mine["equipped_pick"] = p_id
        save_mining_data()

        new_data = await get_user_data(self.guild_id, self.author.id)
        await interaction.response.edit_message(embed=self.build_embed(new_data.get("coins", 0)), view=self)
        await interaction.followup.send(f"🎉 Chúc mừng! Bạn đã mua thành công **{p_info['name']}** và tự động trang bị!", ephemeral=True)

    async def _buy_supply(self, interaction: discord.Interaction):
        s_id = interaction.data["values"][0]
        s_info = MINING_SUPPLIES[s_id]
        u_data = await get_user_data(self.guild_id, self.author.id)
        if u_data.get("coins", 0) < s_info["price"]:
            return await interaction.response.send_message(f"❌ Không đủ coin! Cần **`{s_info['price']:,}` coin**.", ephemeral=True)

        await update_user_coins(self.guild_id, self.author.id, -s_info["price"])
        u_mine = get_user_mining(self.author.id)
        u_mine.setdefault("supplies", {})[s_id] = u_mine.setdefault("supplies", {}).get(s_id, 0) + 1
        save_mining_data()

        new_data = await get_user_data(self.guild_id, self.author.id)
        await interaction.response.edit_message(embed=self.build_embed(new_data.get("coins", 0)), view=self)
        await interaction.followup.send(f"✅ Đã mua thành công 1x **{s_info['name']}**!", ephemeral=True)

    async def _expand_bag(self, interaction: discord.Interaction):
        u_mine = get_user_mining(self.author.id)
        cur_max = u_mine.get("max_bag", 30)
        if cur_max >= 150:
            return await interaction.response.send_message("👑 Giỏ quặng của bạn đã đạt giới hạn tối đa (150 ô)!", ephemeral=True)

        cost = 50000
        u_data = await get_user_data(self.guild_id, self.author.id)
        if u_data.get("coins", 0) < cost:
            return await interaction.response.send_message(f"❌ Cần **`{cost:,}` coin** để nâng cấp giỏ!", ephemeral=True)

        await update_user_coins(self.guild_id, self.author.id, -cost)
        u_mine["max_bag"] = cur_max + 10
        save_mining_data()

        new_data = await get_user_data(self.guild_id, self.author.id)
        await interaction.response.edit_message(embed=self.build_embed(new_data.get("coins", 0)), view=self)
        await interaction.followup.send(f"🎒 Đã mở rộng sức chứa giỏ khoáng sản lên **{u_mine['max_bag']} ô**!", ephemeral=True)

# ==============================================================================
# VIEW: CHỌN MỎ KHOÁNG (MINING ZONE VIEW)
# ==============================================================================
class MiningZoneSelectView(discord.ui.View):
    def __init__(self, author: discord.Member, current_zone: str, user_level: int, guild_id: Optional[int] = None):
        super().__init__(timeout=120)
        self.author = author
        self.current_zone = current_zone
        self.user_level = user_level
        self.guild_id = guild_id or (author.guild.id if getattr(author, 'guild', None) else 0)
        self.vi = is_vietnamese(self.guild_id)

        opts = []
        for z_id, z_info in MINING_ZONES.items():
            locked = "🔒 " if self.user_level < z_info["min_level"] else ""
            opts.append(discord.SelectOption(
                label=f"{locked}{z_info['name']} (Lv.{z_info['min_level']})",
                value=z_id,
                description=z_info["desc"][:90],
                default=(z_id == current_zone)
            ))
        ph = "📍 Chọn mỏ khai thác..." if self.vi else "📍 Select mining zone..."
        sel = discord.ui.Select(placeholder=ph, options=opts)
        sel.callback = self._on_select_zone
        self.add_item(sel)

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id != self.author.id:
            msg = "❌ Đây không phải menu chọn mỏ của bạn!" if self.vi else "❌ This is not your zone selection menu!"
            await interaction.response.send_message(msg, ephemeral=True)
            return False
        return True

    async def _on_select_zone(self, interaction: discord.Interaction):
        z_id = interaction.data["values"][0]
        z_info = MINING_ZONES[z_id]
        if self.user_level < z_info["min_level"]:
            msg = f"🔒 Bạn cần đạt **Level {z_info['min_level']}** để vào **{z_info['name']}**!" if self.vi else f"🔒 You need **Level {z_info['min_level']}** to enter **{z_info['name']}**!"
            return await interaction.response.send_message(msg, ephemeral=True)

        u_mine = get_user_mining(self.author.id)
        u_mine["zone"] = z_id
        save_mining_data()
        if self.vi:
            res = f"⛏️ Đã di chuyển đến mỏ **{z_info['name']}** (+{z_info['luck_bonus']} Luck, +{int(z_info['mutation_bonus']*100)}% Đột biến)!"
        else:
            res = f"⛏️ Relocated to **{z_info['name']}** (+{z_info['luck_bonus']} Luck, +{int(z_info['mutation_bonus']*100)}% Mutation)!"
        await interaction.response.edit_message(content=res, embed=None, view=None)

# ==============================================================================
# COG: COMMAND MINING (HỆ THỐNG ĐÀO KHOÁNG ĐẦY ĐỦ)
# ==============================================================================
class MiningCog(commands.Cog, name="Mining"):
    """Hệ thống khai thác mỏ & khoáng sản quy mô lớn, song hành cùng câu cá."""

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    def _calculate_mine_catch(self, total_luck: int, zone_mut_bonus: float) -> Tuple[Dict[str, Any], Optional[Dict[str, Any]]]:
        """Tính toán quặng đào trúng dựa theo tổng may mắn và tỉ lệ đột biến."""
        # Thao túng tỉ lệ đào khoáng & quặng quý từ Web Admin
        rare_mult = 1.0
        mut_mult = 1.0
        try:
            from data.game_rates import get_game_rates
            grates = get_game_rates()
            total_luck = int(total_luck * grates.get("mining_luck_mult", 1.0))
            rare_mult = grates.get("mining_rare_mult", 1.0)
            mut_mult = grates.get("mining_mutation_mult", 1.0)
        except Exception:
            pass

        ore_pool = list(ORES_CATALOG.values())
        weights = []
        for o in ore_pool:
            r = o.get("rarity", "common")
            if r == "common": base_w = 100.0
            elif r == "uncommon": base_w = 40.0 + (total_luck * 0.05)
            elif r == "rare": base_w = max(5.0, (15.0 + (total_luck * 0.08)) * rare_mult)
            elif r == "epic": base_w = max(1.0, (4.0 + (total_luck * 0.04)) * rare_mult)
            elif r == "legendary": base_w = max(0.2, (0.8 + (total_luck * 0.015)) * rare_mult)
            elif r == "mythic": base_w = max(0.04, (0.15 + (total_luck * 0.005)) * rare_mult)
            else: base_w = max(0.01, (0.03 + (total_luck * 0.002)) * rare_mult)
            weights.append(base_w)

        chosen_ore = random.choices(ore_pool, weights=weights, k=1)[0]

        # Kiểm tra đột biến
        mut_chance = min(1.0, (0.08 + zone_mut_bonus + (total_luck * 0.0002)) * mut_mult)
        chosen_mut = None
        if random.random() < mut_chance:
            m_pool = MINING_MUTATIONS
            m_weights = [m["weight"] for m in m_pool]
            chosen_mut = random.choices(m_pool, weights=m_weights, k=1)[0]

        return chosen_ore, chosen_mut

    @commands.command(name="mine", aliases=["dao", "daokhoang"])
    async def mining_cmd(self, ctx: commands.Context, action: Optional[str] = "mine", *, extra: Optional[str] = None):
        """Lệnh khai mỏ: s!mine [mine/shop/inv/sell/zone/museum/upgrade/repair]"""
        act = (action or "mine").lower().strip()
        user_id = ctx.author.id
        u_mine = get_user_mining(user_id)
        u_data = await get_user_data(ctx.guild.id, user_id)

        # 1. CỬA HÀNG (SHOP)
        if act in ("shop", "cuahang", "mshop"):
            from Command.command_fishing import FishingShopView
            v = FishingShopView(ctx.author, ctx.guild.id)
            v.selected_category = "pick"
            v.current_page = 0
            v._refresh_components()
            return await ctx.send(embed=v.build_embed(u_data.get("coins", 0), int(u_data.get("xu", 0))), view=v)

        # 2. TÚI ĐỒ (INV)
        if act in ("inv", "bag", "tuido", "minv"):
            target_user = ctx.author
            if getattr(ctx, "message", None) and ctx.message.mentions:
                tagged = ctx.message.mentions[0]
                if tagged.id != ctx.author.id:
                    from Check.mod import OWNER_ID
                    is_owner = (ctx.author.id in (1144785664458637394, OWNER_ID) or await self.bot.is_owner(ctx.author))
                    if not is_owner:
                        msg = "❌ Bạn chỉ có thể xem túi đồ của chính mình! Không được phép xem của người khác." if is_vietnamese(ctx.guild.id) else "❌ You can only view your own inventory! You cannot view other players'."
                        return await ctx.send(msg, ephemeral=True)
                    target_user = tagged
            from Command.command_fishing import FishingInventoryView
            u_target_data = await get_user_data(ctx.guild.id, target_user.id)
            v = FishingInventoryView(target_user, ctx.guild.id, inv_page=5, enhance_target="pick")
            return await ctx.send(embed=v.build_embed(u_target_data.get("coins", 0), int(u_target_data.get("xu", 0))), view=v)

        # 3. CHỌN MỎ KHOÁNG (ZONE)
        if act in ("zone", "mo", "mzone"):
            v = MiningZoneSelectView(ctx.author, u_mine.get("zone", "hang_dat"), int(u_data.get("level", 0)), guild_id=ctx.guild.id)
            header = "📍 **BẢNG CHỌN MỎ KHOÁNG SẢN:**" if is_vietnamese(ctx.guild.id) else "📍 **MINING ZONE SELECTION:**"
            return await ctx.send(header, view=v)

        # 4. ĐỊA CHẤT VIỆN BẢO TÀNG (MUSEUM)
        if act in ("museum", "baotang", "khoangvien"):
            v = MiningMuseumView(owner=ctx.author, viewer=ctx.author, guild_id=ctx.guild.id)
            return await ctx.send(embed=v.build_embed(), view=v)

        # 5. BÁN KHOÁNG SẢN (SELL)
        if act in ("sell", "ban", "msell"):
            bag = u_mine.setdefault("ore_bag", [])
            vi = is_vietnamese(ctx.guild.id)
            if not bag:
                return await ctx.send("🎒 Giỏ quặng của bạn đang trống!" if vi else "🎒 Your ore bag is empty!", ephemeral=True)

            earned = sum(o.get("price", 0) for o in bag)
            eq_id = u_mine.get("equipped_pick")
            cur_pick = u_mine.get("picks", {}).get(eq_id, {})
            ench_stats = get_pick_enchant_stats(cur_pick)

            bonus_pct = ench_stats.get("sell_bonus", 0) + cur_pick.get("sell_bonus", 0)
            if bonus_pct > 0:
                earned = int(earned * (1.0 + bonus_pct / 100.0))

            count = len(bag)
            bag.clear()
            u_mine["stats"]["total_earned"] = u_mine["stats"].get("total_earned", 0) + earned
            await update_user_coins(ctx.guild.id, user_id, earned)
            save_mining_data()

            if vi:
                bonus_msg = f" (✨ +{bonus_pct}% từ Cuốc & Hỏa Lò)" if bonus_pct > 0 else ""
                return await ctx.send(f"💰 Đã bán **{count}** khối quặng thu về **`+{earned:,}` coin**!{bonus_msg}")
            else:
                bonus_msg = f" (✨ +{bonus_pct}% from Pickaxe & Furnace)" if bonus_pct > 0 else ""
                return await ctx.send(f"💰 Sold **{count}** ores for **`+{earned:,}` coins**!{bonus_msg}")

        # 6. SỬA CUỐC (REPAIR)
        if act in ("repair", "sua"):
            eq_id = u_mine.get("equipped_pick")
            cur_pick = u_mine.get("picks", {}).get(eq_id)
            vi = is_vietnamese(ctx.guild.id)
            if not cur_pick:
                return await ctx.send("❌ Bạn chưa trang bị cuốc!" if vi else "❌ You don't have a pickaxe equipped!", ephemeral=True)
            max_d = cur_pick.get("max_durability", 100)
            cur_d = cur_pick.get("durability", 0)
            if cur_d >= max_d:
                return await ctx.send("✅ Cuốc của bạn còn nguyên vẹn 100% độ bền!" if vi else "✅ Your pickaxe is at 100% durability!", ephemeral=True)
            cost = max(300, int(((max_d - cur_d) / max_d) * cur_pick.get("price", 5000) * 0.4))
            if u_data.get("coins", 0) < cost:
                return await ctx.send(f"❌ Cần **`{cost:,}` coin** để sửa cuốc!" if vi else f"❌ You need **`{cost:,}` coins** to repair your pickaxe!", ephemeral=True)
            await update_user_coins(ctx.guild.id, user_id, -cost)
            cur_pick["durability"] = max_d
            save_mining_data()
            return await ctx.send(f"🔧 Đã sửa chữa hoàn toàn độ bền cho **{cur_pick['name']}** (-`{cost:,}` coin)!" if vi else f"🔧 Fully repaired durability for **{cur_pick['name']}** (-`{cost:,}` coins)!")

        # 7. CƯỜNG HÓA CUỐC (UPGRADE) & ENCHANT
        if act in ("upgrade", "dap", "cuonghoa", "enchant", "gandong"):
            from Command.command_fishing import FishingInventoryView
            tab = 4 if act in ("enchant", "gandong") else 3
            v = FishingInventoryView(ctx.author, ctx.guild.id, inv_page=tab, enhance_target="pick")
            return await ctx.send(embed=v.build_embed(u_data.get("coins", 0), int(u_data.get("xu", 0))), view=v)

        # 8. MẶC ĐỊNH: VUNG CUỐC ĐÀO KHOÁNG (MINE)
        vi = is_vietnamese(ctx.guild.id)
        now = time.time()
        eq_id = u_mine.get("equipped_pick")
        if not eq_id or eq_id not in u_mine.get("picks", {}):
            msg = f"⚠️ Bạn chưa trang bị cuốc! Dùng `{ctx.prefix}mshop` để mua và `{ctx.prefix}minv` để chọn cuốc." if vi else f"⚠️ You don't have a pickaxe equipped! Use `{ctx.prefix}mshop` to buy and `{ctx.prefix}minv` to equip one."
            return await ctx.send(msg, ephemeral=True)

        current_pick = u_mine["picks"][eq_id]
        if current_pick.get("durability", 0) <= 0:
            msg = f"❌ Cuốc đã hỏng độ bền! Dùng `{ctx.prefix}mine repair` để sửa chữa." if vi else f"❌ Your pickaxe is broken! Use `{ctx.prefix}mine repair` to repair it."
            return await ctx.send(msg, ephemeral=True)

        buffs = u_mine.setdefault("buffs", {})
        ench_stats = get_pick_enchant_stats(current_pick)

        # Tính hồi chiêu đào
        base_cooldown = 10
        if buffs.get("fast_mine", 0) > now:
            base_cooldown = 4
        if ench_stats.get("mine_speed", 0) > 0:
            base_cooldown = max(3, int(base_cooldown * (1.0 - min(ench_stats["mine_speed"], 50) / 100.0)))

        last_mine = u_mine.get("last_mine", 0)
        if now - last_mine < base_cooldown:
            rem = int(base_cooldown - (now - last_mine))
            msg = f"⏳ Cánh tay còn mỏi! Hãy nghỉ ngơi **{rem} giây** trước khi vung nhát tiếp theo." if vi else f"⏳ Your arms are tired! Rest for **{rem} seconds** before swinging again."
            return await ctx.send(msg, ephemeral=True)

        max_bag = u_mine.get("max_bag", 30)
        if len(u_mine.get("ore_bag", [])) >= max_bag:
            msg = f"🎒 Giỏ quặng đầy (`{len(u_mine['ore_bag'])}/{max_bag}`)! Dùng `{ctx.prefix}mine sell` để bán hoặc cất vào bảo tàng." if vi else f"🎒 Ore bag is full (`{len(u_mine['ore_bag'])}/{max_bag}`)! Use `{ctx.prefix}mine sell` to sell or store in museum."
            return await ctx.send(msg, ephemeral=True)

        # Khu vực đào
        z_id = u_mine.get("zone", "hang_dat")
        if z_id not in MINING_ZONES:
            z_id = "hang_dat"
            u_mine["zone"] = "hang_dat"
        zone = MINING_ZONES[z_id]

        u_mine["last_mine"] = now

        # Tính toán May Mắn
        pick_luck = current_pick.get("luck", 5) + (current_pick.get("refine", 0) * 4) + ench_stats["luck"]
        lamp_luck = 60 if buffs.get("miner_luck", 0) > now else 0
        total_luck = pick_luck + zone["luck_bonus"] + lamp_luck
        mut_bonus = zone["mutation_bonus"] + (ench_stats.get("mutant_rate", 0) / 100.0)

        chosen_ore, chosen_mut = self._calculate_mine_catch(total_luck, mut_bonus)

        rarity = chosen_ore.get("rarity", "common")
        is_rare_boss = rarity in ("epic", "legendary", "mythic", "godly") or (chosen_mut is not None)
        has_auto_qte = current_pick.get("auto_qte") or (buffs.get("auto_mine_qte", 0) > now)

        # Tiêu hao độ bền
        if ench_stats.get("durability_save", 0) > 0 and (random.random() * 100.0 < ench_stats["durability_save"]):
            pass # Dòng enchant bảo toàn độ bền
        elif current_pick.get("save_durability", 0) > 0 and (random.random() * 100.0 < current_pick["save_durability"]):
            pass
        else:
            current_pick["durability"] -= 1
            if current_pick["durability"] <= 0:
                u_mine["stats"]["broken_picks"] = u_mine["stats"].get("broken_picks", 0) + 1
                u_mine["equipped_pick"] = None

        # Mini-game QTE nếu gặp mạch quý
        if is_rare_boss and not has_auto_qte:
            acts = ["left", "down", "right"]
            target_act = random.choice(acts)
            act_names = {"left": "VUNG TRÁI ⬅️", "down": "BỔ CHÍNH DIỆN ⬇️", "right": "VUNG PHẢI ➡️"} if vi else {"left": "SWING LEFT ⬅️", "down": "DIRECT STRIKE ⬇️", "right": "SWING RIGHT ➡️"}
            qte = MiningQTEView(ctx.author, target_act, guild_id=ctx.guild.id)
            prompt = f"🚨 **PHÁT HIỆN MẠCH KHOÁNG HIẾM!** Hãy nhấn **[{act_names[target_act]}]** trong 4.5 giây để khai quật!" if vi else f"🚨 **RARE MINERAL VEIN FOUND!** Press **[{act_names[target_act]}]** within 4.5s to excavate!"
            qmsg = await ctx.send(prompt, view=qte)
            await qte.wait()
            if not qte.success:
                save_mining_data()
                fail_msg = "💥 **GÃY LƯỠI CUỐC!** Bạn vung sai hướng, mạch đá sụp đổ làm vỡ vụn khối quặng quý..." if vi else "💥 **PICKAXE SNAPPED!** You swung the wrong way, the rock collapsed crushing the precious ore..."
                return await qmsg.edit(content=fail_msg, view=None)

        # Khối lượng và giá bán
        weight = round(random.uniform(*chosen_ore["weight_range"]), 2)
        price_multi = chosen_mut.get("price_multi", 1.0) if chosen_mut else 1.0
        pick_sell_bonus = current_pick.get("sell_bonus", 0) / 100.0
        final_price = max(20, int(chosen_ore["price"] * price_multi * (1.0 + pick_sell_bonus)))

        ore_item = {
            "id": chosen_ore["id"],
            "name": chosen_ore["name"],
            "rarity": rarity,
            "weight": weight,
            "price": final_price,
            "mutation": chosen_mut.get("name") if chosen_mut else None,
            "time": int(now)
        }
        u_mine.setdefault("ore_bag", []).append(ore_item)
        u_mine["stats"]["total_mined"] = u_mine["stats"].get("total_mined", 0) + 1

        # Cập nhật oredex
        dex = u_mine.setdefault("oredex", {})
        if chosen_ore["name"] not in dex:
            dex[chosen_ore["name"]] = {"count": 1, "max_weight": weight, "rarity": rarity}
        else:
            dex[chosen_ore["name"]]["count"] = dex[chosen_ore["name"]].get("count", 0) + 1
            dex[chosen_ore["name"]]["max_weight"] = max(dex[chosen_ore["name"]].get("max_weight", 0.0), weight)

        save_mining_data()

        # Kích hoạt thành tựu Đào Khoáng
        try:
            from Command.achievement_system import unlock_achievement
            gid = ctx.guild.id if ctx.guild else 0
            tm = u_mine["stats"].get("total_mined", 1)
            await unlock_achievement(gid, user_id, "mine_first", ctx.channel)
            if tm >= 10: await unlock_achievement(gid, user_id, "mine_10", ctx.channel)
            if tm >= 50: await unlock_achievement(gid, user_id, "mine_50", ctx.channel)
            if tm >= 100: await unlock_achievement(gid, user_id, "mine_100", ctx.channel)
            if tm >= 500: await unlock_achievement(gid, user_id, "mine_500", ctx.channel)
            if tm >= 1000: await unlock_achievement(gid, user_id, "mine_1000", ctx.channel)

            ore_id = str(chosen_ore.get("id") or chosen_ore.get("name", "")).lower()
            if "iron" in ore_id or "sắt" in ore_id:
                await unlock_achievement(gid, user_id, "ore_iron_first", ctx.channel)
            if "gold" in ore_id or "vàng" in ore_id:
                await unlock_achievement(gid, user_id, "ore_gold_first", ctx.channel)
            if "diamond" in ore_id or "kim cương" in ore_id:
                await unlock_achievement(gid, user_id, "gem_diamond_first", ctx.channel)
            if "emerald" in ore_id or "lục bảo" in ore_id:
                await unlock_achievement(gid, user_id, "gem_emerald_first", ctx.channel)
            if "ruby" in ore_id or "hồng ngọc" in ore_id:
                await unlock_achievement(gid, user_id, "gem_ruby_first", ctx.channel)
        except Exception:
            pass

        # Tạo embed thông báo khai thác
        icon = RARITY_ICONS.get(rarity, "💎")
        if vi:
            title = f"{icon} Khai Quật Thành Công: {chosen_ore['name']}!"
            desc = chosen_ore.get("desc", "Khoáng vật quý giá trong lòng đất.")
        else:
            title = f"{icon} Excavation Successful: {chosen_ore['name']}!"
            desc = chosen_ore.get("desc_en", chosen_ore.get("desc", "Precious mineral from deep underground."))

        embed = discord.Embed(
            title=title,
            description=desc,
            color=RARITY_COLORS.get(rarity, discord.Color.blue())
        )
        embed.add_field(name="🏷️ Phẩm chất" if vi else "🏷️ Rarity", value=f"`{rarity.upper()}`", inline=True)
        embed.add_field(name="⚖️ Khối lượng" if vi else "⚖️ Weight", value=f"**`{weight} kg`**", inline=True)
        embed.add_field(name="💰 Trị giá" if vi else "💰 Value", value=f"**`{final_price:,}` coin**", inline=True)
        embed.add_field(name="📍 Vị trí mỏ" if vi else "📍 Mine Zone", value=f"**{zone['name']}** (+{zone['luck_bonus']} Luck)", inline=False)
        if chosen_mut:
            mut_suffix = "giá" if vi else "price"
            embed.add_field(name="🧬 Đột biến" if vi else "🧬 Mutation", value=f"**{chosen_mut['name']}** (x{chosen_mut['price_multi']} {mut_suffix})", inline=False)

        if vi:
            embed.set_footer(text=f"Giỏ: {len(u_mine['ore_bag'])}/{max_bag} • Cuốc: {current_pick['name']} • May mắn: +{total_luck}")
        else:
            embed.set_footer(text=f"Bag: {len(u_mine['ore_bag'])}/{max_bag} • Pick: {current_pick['name']} • Luck: +{total_luck}")
        return await ctx.send(embed=embed)

async def setup(bot: commands.Bot):
    await bot.add_cog(MiningCog(bot))
