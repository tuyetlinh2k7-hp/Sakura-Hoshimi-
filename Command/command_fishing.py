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
from PIL import Image, ImageDraw, ImageFont

from Check.i18n import t, is_vietnamese
from Check.mod import is_owner, OWNER_ID
from data.database import get_user_data, update_user_coins, update_user_xu, set_user_xu
from Command.farm_system import (
    SEEDS_CATALOG,
    CROPS_CATALOG,
    get_crop_info,
    PESTS_CATALOG,
    FARM_TOOLS_CATALOG,
    SEASONS_INFO,
    FARM_WEATHER_CYCLE,
    FARM_COOK_RECIPES,
    get_user_farm,
    update_farm_state,
    get_current_season_and_weather,
    FarmView,
    safe_field_text,
    safe_add_field
)

ENCHANT_AFFIXES = [
    {"id": "luck_boost", "name": "Vận Khí Trời Ban", "icon": "🍀", "desc": "Tăng May Mắn khi thả câu", "stat": "luck", "min_val": 15, "max_val": 60, "val_range": (15, 60), "format": "+{val} May Mắn"},
    {"id": "speed_pull", "name": "Thần Tốc Kéo Cần", "icon": "⚡", "desc": "Giảm thời gian cá cắn câu", "stat": "pull_speed", "min_val": 10, "max_val": 35, "val_range": (10, 35), "format": "-{val}% Thời gian cắn"},
    {"id": "wealth_coin", "name": "Khai Tài Phú Quý", "icon": "💰", "desc": "Tăng Coins nhận được khi bán cá", "stat": "sell_bonus", "min_val": 15, "max_val": 50, "val_range": (15, 50), "format": "+{val}% Coins bán cá"},
    {"id": "unbreakable", "name": "Bất Hoại Chi Thân", "icon": "🛡️", "desc": "Tỉ lệ câu cá không tiêu hao độ bền", "stat": "durability_save", "min_val": 20, "max_val": 55, "val_range": (20, 55), "format": "{val}% Không hao bền"},
    {"id": "farmer_boost", "name": "Thần Nông Trợ Lực", "icon": "🌾", "desc": "Rút ngắn thời gian lớn của cây trồng", "stat": "farm_speed", "min_val": 15, "max_val": 40, "val_range": (15, 40), "format": "-{val}% Thời gian cây lớn"},
    {"id": "forge_master", "name": "Thần Chúc Búa Vàng", "icon": "🔨", "desc": "Tăng tỉ lệ thành công đập đồ & tiến sao", "stat": "refine_rate", "min_val": 5, "max_val": 15, "val_range": (5, 15), "format": "+{val}% Tỉ lệ đập đồ"},
    {"id": "mutant_attract", "name": "Thiên Duyên Kỳ Ngộ", "icon": "🌈", "desc": "Tăng tỉ lệ câu được cá mang gen đột biến", "stat": "mutant_rate", "min_val": 25, "max_val": 65, "val_range": (25, 65), "format": "+{val}% Gặp cá đột biến"}
]

def get_max_enchant_slots(rod_data: Dict[str, Any]) -> int:
    rarity = rod_data.get("rarity", "common")
    rarity_slots = {
        "common": 1,
        "uncommon": 2,
        "rare": 2,
        "epic": 3,
        "legendary": 4,
        "mythic": 5,
        "ancient": 6,
        "exotic": 6,
        "admin": 6
    }
    base = rarity_slots.get(rarity, 1)
    extra = rod_data.get("extra_enchant_slots", 0)
    return min(7, base + extra)

def get_rod_enchant_stats(rod_data: Dict[str, Any] | None) -> Dict[str, int]:
    """Tổng hợp chỉ số các dòng enchant trên cần câu."""
    stats = {
        "luck": 0,
        "pull_speed": 0,
        "sell_bonus": 0,
        "durability_save": 0,
        "farm_speed": 0,
        "refine_rate": 0,
        "mutant_rate": 0
    }
    if not isinstance(rod_data, dict):
        return stats
    for aff in rod_data.get("enchant_affixes", []):
        if not isinstance(aff, dict):
            continue
        st = aff.get("stat")
        val = aff.get("val", 0)
        try:
            val_int = int(val)
        except (ValueError, TypeError):
            val_int = 0
        if st in stats:
            stats[st] += val_int
    return stats

try:
    from data.data import (
        fish_list,
        event_fish,
        mutations,
        RARITY_ICONS,
        RARITY_COLORS,
    )
except ImportError:
    fish_list = [{"name": "🐟 Cá Chép", "price": 100, "chance": 100, "rarity": "common", "description": "Cá phổ biến"}]
    event_fish = []
    mutations = [
        {"name": "🔥 Lửa Rực Cháy", "price_multi": 2.0},
        {"name": "❄️ Băng Giá Vĩnh Cửu", "price_multi": 2.0},
        {"name": "☢️ Đột Biến Phóng Xạ", "price_multi": 3.0},
        {"name": "⚡ Lôi Điện Sấm Sét", "price_multi": 3.5},
        {"name": "✨ Huỳnh Quang Phát Sáng", "price_multi": 4.0},
        {"name": "🌪️ Phong Ba Bão Táp", "price_multi": 2.6},
        {"name": "🌿 Rêu Phong Thảo Mộc", "price_multi": 2.2},
        {"name": "☣️ Axit Ăn Mòn", "price_multi": 3.2},
        {"name": "🌈 Cầu Vồng Lục Sắc", "price_multi": 4.5},
        {"name": "💎 Kim Cương Tinh Thể", "price_multi": 5.0},
        {"name": "⚙️ Cơ Khí Cyberpunk", "price_multi": 5.5},
        {"name": "🌑 Hắc Ám Vực Sâu", "price_multi": 6.0},
        {"name": "👻 Linh Hồn U Minh", "price_multi": 6.8},
        {"name": "🧬 Biến Dị Hỗn Loạn", "price_multi": 7.2},
        {"name": "🩸 Huyết Nguyệt Ma Đỏ", "price_multi": 7.8},
        {"name": "🪙 Hoàng Kim Midas", "price_multi": 8.5},
        {"name": "✨ Thánh Quang Thiên Giới", "price_multi": 9.0},
        {"name": "🔮 Huyết Mạch Thần Thú", "price_multi": 9.5},
        {"name": "🌌 Hư Không Void-Touched", "price_multi": 10.0},
        {"name": "☄️ Plasma Tinh Vân", "price_multi": 11.5},
        {"name": "⚡ Siêu Lôi Thần Tích", "price_multi": 12.5},
        {"name": "⏳ Nghịch Đảo Thời Gian", "price_multi": 13.0},
        {"name": "☣️ Bụi Phấn Độc Ma Quái", "price_multi": 13.5},
        {"name": "☄️ Tinh Thể Thiên Thạch", "price_multi": 14.0},
        {"name": "🪐 Vũ Trụ Đa Chiều", "price_multi": 15.0},
        {"name": "✨ Cực Quang Huyền Ảo", "price_multi": 15.5},
        {"name": "🌸 Hoa Anh Đào Sakura Dạ Quang", "price_multi": 16.0},
        {"name": "💎 Thạch Anh Tím Huyền Bí", "price_multi": 17.5},
        {"name": "🖤 Hắc Động Singularity", "price_multi": 18.0},
        {"name": "🩸 Ma Cà Rồng Biển Đỏ", "price_multi": 19.0},
        {"name": "🐉 Long Hồn Thượng Cổ", "price_multi": 20.0},
        {"name": "👾 Lỗi Thực Tại (Glitch)", "price_multi": 22.0},
        {"name": "🧿 Mắt Quỷ Vực Thẳm", "price_multi": 25.0},
        {"name": "🌠 Bụi Sao Băng Cổ Đại", "price_multi": 26.5},
        {"name": "💠 Lõi Lượng Tử Hỗn Loạn", "price_multi": 28.0},
        {"name": "👑 Thần Cách Nguyên Thủy", "price_multi": 30.0},
        {"name": "☀️ Nhật Hoa Vĩnh Cửu", "price_multi": 32.0},
        {"name": "🌌 Khởi Nguyên Sáng Thế", "price_multi": 40.0},
        {"name": "🪐 Ma Trận Thực Tại", "price_multi": 45.0},
        {"name": "👑 Thần Vương Tối Thượng", "price_multi": 50.0}
    ]
    RARITY_ICONS = {"common": "⚪", "rare": "🔵", "epic": "🟣", "legendary": "🟡", "admin": "🔴"}
    RARITY_COLORS = {"common": discord.Color.light_grey(), "rare": discord.Color.blue(), "epic": discord.Color.purple(), "legendary": discord.Color.gold(), "admin": discord.Color.red()}

BASE_DIR = Path(__file__).resolve().parent.parent
FISHING_DATA_FILE = BASE_DIR / "data" / "fishing_inventory.json"
VN_TZ = timezone(timedelta(hours=7))

RODS_CATALOG = {
    "rod_wood": {"name": "🎣 Cần Câu Gỗ", "price": 5000, "level": 1, "luck": 2, "durability": 50, "rarity": "common", "chest_only": False},
    "rod_bamboo": {"name": "🎋 Cần Câu Tre Dẻo", "price": 25000, "level": 3, "luck": 8, "durability": 90, "rarity": "common", "chest_only": False},
    "rod_iron": {"name": "🎣 Cần Câu Sắt", "price": 90000, "level": 5, "luck": 16, "durability": 160, "rarity": "rare", "chest_only": False},
    "rod_coral": {"name": "🪸 Cần San Hô Cổ", "price": 220000, "level": 8, "luck": 26, "durability": 250, "rarity": "rare", "chest_only": False},
    "rod_gold": {"name": "🎣 Cần Câu Vàng", "price": 450000, "level": 12, "luck": 38, "durability": 400, "rarity": "epic", "chest_only": False},
    "rod_obsidian": {"name": "🖤 Cần Hắc Diện Thạch", "price": 950000, "level": 16, "luck": 55, "durability": 700, "rarity": "epic", "chest_only": False},
    "rod_diamond": {"name": "💎 Cần Câu Kim Cương", "price": 2200000, "level": 20, "luck": 75, "durability": 1100, "rarity": "legendary", "chest_only": False},
    "rod_mecha": {"name": "🤖 Cần Cơ Khí Thủy Triều", "price": 5500000, "level": 25, "luck": 105, "durability": 1800, "rarity": "legendary", "chest_only": False},
    "rod_poseidon": {"name": "🔱 Cần Hải Thần Poseidon", "price": 0, "level": 30, "luck": 160, "durability": 3000, "rarity": "legendary", "chest_only": True},
    "rod_abyssal_reaper": {"name": "💀 Cần Tử Thần Vực Thẳm", "price": 0, "level": 35, "luck": 210, "durability": 4500, "rarity": "legendary", "chest_only": True},
    "rod_starlight": {"name": "✨ Cần Tinh Tú Thần Thoại", "price": 0, "level": 40, "luck": 280, "durability": 6000, "rarity": "legendary", "chest_only": True},
    "rod_owner": {"name": "👑 Cần Câu Tối Thượng", "price": 999999999, "level": 150, "luck": 400, "durability": 9999, "rarity": "admin", "chest_only": False},
    "rod_owner2": {"name": "👑 Cần Câu Tối Thượng II", "price": 9999999999, "level": 150, "luck": 600, "durability": 19999, "rarity": "admin", "chest_only": False},
    "rod_owner3": {"name": "👑 Cần Câu Tối Thượng III", "price": 99999999999, "level": 150, "luck": 800, "durability": 29999, "rarity": "admin", "chest_only": False},
    "rod_owner4": {"name": "👑 Cần Câu Tối Thượng VI", "price": 99999999999, "level": 150, "luck": 1000, "durability": 29999, "rarity": "admin", "chest_only": False},
    "rod_owner5": {"name": "👑 Cần Câu Tối Thượng V", "price": 9999999999999, "level": 150, "luck": 1200, "durability": 39999, "rarity": "admin", "chest_only": False},
    "rod_owner6": {"name": "👑 Cần Câu Tối Thượng II", "price": 99999999999999, "level": 150, "luck": 2000, "durability": 49999, "rarity": "admin", "chest_only": False},
    "rod_astral_god": {"name": "🌌 Cần Thần Tinh Tú Astral", "price": 500, "currency": "xu", "level": 1, "luck": 350, "durability": 8000, "rarity": "legendary", "chest_only": False},
    "rod_dragon_emperor": {"name": "🐉 Cần Long Vương Tối Cao", "price": 1500, "currency": "xu", "level": 1, "luck": 600, "durability": 15000, "rarity": "legendary", "chest_only": False},
    "rod_infinity_void": {"name": "🔮 Cần Vô Cực Hư Không", "price": 5000, "currency": "xu", "level": 1, "luck": 1200, "durability": 30000, "rarity": "admin", "chest_only": False},
}

BAITS_CATALOG = {
    "bait_normal": {"name": "🪱 Mồi Thường", "price": 500, "luck": 3, "buyable": True},
    "bait_rare": {"name": "🪱 Mồi Hiếm", "price": 4500, "luck": 10, "buyable": True},
    "bait_epic": {"name": "🪱 Mồi Sử Thi", "price": 18000, "luck": 22, "buyable": True},
    "bait_glow": {"name": "✨ Mồi Dạ Quang", "price": 505000, "luck": 35, "buyable": True},
    "bait_legend": {"name": "🪱 Mồi Huyền Thoại", "price": 1040000, "luck": 55, "buyable": True},
    "bait_dragon": {"name": "🩸 Mồi Máu Rồng", "price": 3020000, "luck": 80, "buyable": True},
    "bait_mermaid_tear": {"name": "💧 Nước Mắt Tiên Cá", "price": 0, "luck": 105, "buyable": False},
    "bait_abyss": {"name": "🌀 Mồi Vực Thẳm", "price": 0, "luck": 130, "buyable": False},
    "bait_kraken_tentacle": {"name": "🦑 Xúc Tu Kraken", "price": 0, "luck": 160, "buyable": False},
    "bait_golden": {"name": "🪙 Mồi Hoàng Kim", "price": 0, "luck": 200, "buyable": False},
    "bait_godly_essence": {"name": "🌟 Tinh Hoa Thần Biển", "price": 0, "luck": 260, "buyable": False},
    "bait_cosmic": {"name": "🪐 Mồi Vũ Trụ", "price": 0, "luck": 350, "buyable": False},
    "bait_phoenix_blood": {"name": "🩸 Mồi Huyết Phượng Hoàng", "price": 10, "currency": "xu", "luck": 150, "buyable": True},
    "bait_cosmic_core": {"name": "🪐 Mồi Lõi Vũ Trụ", "price": 25, "currency": "xu", "luck": 300, "buyable": True},
    "bait_celestial_ambrosia": {"name": "🌟 Mồi Tiên Dược Thiên Giới", "price": 60, "currency": "xu", "luck": 500, "buyable": True},
}

BAGS_UPGRADES = {
    "fish_bag_small": {"name": "🎒 Túi Cá Nhỏ (+10 ô)", "price": 35000, "extra_slots": 10},
    "fish_bag_medium": {"name": "👜 Túi Cá Vừa (+25 ô)", "price": 180000, "extra_slots": 25},
    "fish_bag_large": {"name": "📦 Thùng Cá Lớn (+50 ô)", "price": 650000, "extra_slots": 50},
    "fish_bag_larges": {"name": "Thùng Cá Lớn I", "price": 890000, "extra_slots": 75 },
    "fish_bag_largess": {"name": "Thùng Cá Lớn II", "price": 1690000, "extra_slots": 100 },
    "fish_bag_largesss": {"name": "Thùng Cá Lớn III", "price": 3590000, "extra_slots": 200 },
    "fish_bag_largessss": {"name": "Thùng Cá Lớn IV", "price": 9720000, "extra_slots": 500 },
    "fish_bag_largesssss": {"name": "Thùng Cá Lớn V", "price": 28780000, "extra_slots": 1000 },
    "fish_bag_large6s": {"name": "Thùng Cá Lớn VI", "price": 57890000, "extra_slots": 2000 },
    "fish_bag_large7s": {"name": "Thùng Cá Lớn VII", "price": 88890000, "extra_slots":  4000 },
    "fish_bag_large8s": {"name": "Thùng Cá Lớn VIII", "price": 256890000, "extra_slots": 9036 },
    "fish_bag_large9s": {"name": "Thùng Cá Lớn XI", "price": 3667890000, "extra_slots": 13667 },
    "fish_bag_large10s": {"name": "Thùng Cá Lớn X", "price": 36363890000, "extra_slots": 363636 },
    "fish_bag_admin": {"name": "👑 Kho Cá Admin (+999 ô)", "price": 999999999999999, "extra_slots": 9999999},
    "fish_bag_infinity_1": {"name": "🎒 Túi Không Gian Vô Tận I (+5,000 ô)", "price": 50, "currency": "xu", "extra_slots": 5000},
    "fish_bag_infinity_2": {"name": "👜 Túi Không Gian Vô Tận II (+20,000 ô)", "price": 150, "currency": "xu", "extra_slots": 20000},
    "fish_bag_infinity_max": {"name": "👑 Kho Vũ Trụ Vô Cực (+100,000 ô)", "price": 500, "currency": "xu", "extra_slots": 100000},
}

PETS_CATALOG = {
    "cat_pet": {"name": "🐱 Mèo Biển", "price": 1200900, "luck_bonus": 8, "bait_drop_bonus": 0.10, "price_multi": 1.05},
    "otter_pet": {"name": "🦦 Rái Cá Lặn", "price": 4500000, "luck_bonus": 15, "bait_drop_bonus": 0.15, "price_multi": 1.10},
    "penguin_pet": {"name": "🐧 Cánh Cụt Băng", "price": 11000000, "luck_bonus": 22, "bait_drop_bonus": 0.20, "price_multi": 1.15},
    "turtle_pet": {"name": "🐢 Rùa Cổ Đại", "price": 25000000, "luck_bonus": 30, "bait_drop_bonus": 0.25, "price_multi": 1.20},
    "dolphin_pet": {"name": "🐬 Cá Heo Thần Sóng", "price": 60000000, "luck_bonus": 40, "bait_drop_bonus": 0.30, "price_multi": 1.28},
    "dragon_pet": {"name": "🐉 Rồng Đại Dương", "price": 150000000, "luck_bonus": 55, "bait_drop_bonus": 0.35, "price_multi": 1.38},
    "kraken_pet": {"name": "🐙 Tiểu Kraken Vực Sâu", "price": 350000000, "luck_bonus": 80, "bait_drop_bonus": 0.45, "price_multi": 1.50},
    "pet_phoenix": {"name": "🔥 Phượng Hoàng Lửa Đại Dương", "price": 300, "currency": "xu", "luck_bonus": 80, "bait_drop_bonus": 0.35, "price_multi": 1.50},
    "pet_celestial_fox": {"name": "🦊 Hồ Ly Cửu Vĩ Tinh Tú", "price": 800, "currency": "xu", "luck_bonus": 150, "bait_drop_bonus": 0.50, "price_multi": 2.00},
}

UTILITY_ITEMS = {
    "ve_so": {"name": "🎟️ Vé Số Đại Dương", "price": 50000, "desc": "Cào vé thử may mắn trúng tới 2,000,000 coin!"},
    "bomb_card": {"name": "💣 Thẻ Bom Hẹn Giờ", "price": 8500900, "desc": "Gài bom nổ chậm 5s tag trúng mục tiêu."},
    "shield": {"name": "🛡️ Khiên Bảo Vệ", "price": 25000000, "desc": "Miễn nhiễm hoàn toàn 1 đòn troll xấu tính."},
    "rename_card": {"name": "📝 Thẻ Đổi Tên", "price": 38000000, "desc": "Đổi biệt danh (nickname) thành viên trong server."},
    "voice_kick": {"name": "🔊 Voice Kick", "price": 30000000, "desc": "Trục xuất đối phương khỏi phòng thoại Discord."},
    "mute_card": {"name": "🔇 Thẻ Mute", "price": 32000000, "desc": "Khóa mõm (Timeout) đối phương trong 30 giây."},
    "ghost_ping": {"name": "👻 Thẻ Ghost Ping", "price": 12000000, "desc": "Ping ma bí ẩn rồi lập tức xóa dấu vết."},
    "banana_peel": {"name": "🍌 Vỏ Chuối Trơn Trượt", "price": 6500000, "desc": "Đặt bẫy khiến người khác trượt chân rơi mất 10,000 - 50,000 coin!", "action_key": "STEAL_COIN"},
    "magic_mirror": {"name": "🪞 Gương Phản Chiếu", "price": 28000000, "desc": "Bật ngược lại 1 đòn troll của kẻ khác sang chính họ."},
    "mystery_box": {"name": "🎁 Hộp Quà Bí Ẩn", "price": 9000000, "desc": "Tặng quà troll: Người mở nhận hù dọa hoặc trúng 500,000 coin ngẫu nhiên."},
    "reverse_card": {"name": "🔀 Thẻ Đảo Ngược Ngôn Từ", "price": 15000000, "desc": "Nguyền rủa đối phương nói năng lộn xộn ngược chiều trong 3 phút!", "action_key": "REVERSE_TEXT"},
    "freeze_card": {"name": "🧊 Bom Băng Giá", "price": 22000000, "desc": "Đóng băng cần câu đối phương, cấm câu cá trong 2 phút!", "action_key": "FREEZE_FISHING"},
    "steal_fish_card": {"name": "🦹 Bàn Tay Đạo Tặc", "price": 35000000, "desc": "Thò tay móc trộm 1 con cá ngẫu nhiên trong giỏ của đối thủ!", "action_key": "STEAL_FISH"},
    "fake_nitro": {"name": "💎 Thẻ Fake Nitro", "price": 5000000, "desc": "Tặng hộp quà Nitro giả Rickroll siêu cay cú!", "action_key": "FAKE_NITRO"},
    "frog_potion": {"name": "🐸 Thuốc Biến Ếch", "price": 18000000, "desc": "Hóa phép đổi tên nạn nhân thành Ếch Ộp trong 5 phút!", "action_key": "FROG"},
    "slap_fish": {"name": "🐟 Cá Hồi Tát Mặt", "price": 7500000, "desc": "Cầm cá hồi quất bôm bốp vào mặt đối thủ kèm tiếng vang!", "action_key": "SLAP"},
    "cursed_bait": {"name": "🪱 Mồi Câu Nguyền Rủa", "price": 16000000, "desc": "Bỏ lén vào giỏ, khiến lần câu tiếp theo của mục tiêu 100% vớt rác!", "action_key": "CURSED_BAIT"},
    "troll_box": {"name": "📦 Hộp Quà Lừa Tình", "price": 10000000, "desc": "Hộp quà nhìn như rương thần nhưng mở ra thì bị hù dọa té khói!", "action_key": "JUMPSCARE"},
    "key_silver": {"name": "🔑 Chìa Khóa Bạc", "price": 800900, "desc": "Mở Rương Bạc Chìm dưới đáy biển."},
    "key_shipwreck": {"name": "🗝️ Chìa Khóa Tàu Cổ", "price": 2200000, "desc": "Mở Rương Tàu Đắm Cổ xưa."},
    "key_gold": {"name": "👑 Chìa Khóa Hoàng Gia", "price": 6009000, "desc": "Mở Rương Hoàng Gia lộng lẫy."},
    "key_abyss": {"name": "🐙 Chìa Khóa Vực Thẳm", "price": 18000900, "desc": "Mở Rương Thủy Quái Vực Sâu."},
    "key_void": {"name": "🌌 Chìa Khóa Hư Không", "price": 50000000, "desc": "Mở Rương Hư Không Vĩnh Hằng."},
    "pearl_ancient": {"name": "🔮 Ngọc Trai Cổ Đại", "price": 0, "desc": "Bán cho thương gia thu về 500,000 - 1,500,000 coin!"},
    "treasure_map": {"name": "🗺️ Bản Đồ Kho Báu", "price": 0, "desc": "Buff nhân đôi (+100%) May Mắn trong 60 phút."},
    "relic_sea_stone": {"name": "🗿 Đá Trấn Hải", "price": 0, "desc": "Cần câu không mất độ bền trong 30 lần thả câu."},
    "relic_golden_scale": {"name": "🪙 Vảy Rồng Vàng", "price": 0, "desc": "Tăng +50% giá bán toàn bộ cá trong 60 phút."},
    "ring_bronze": {"name": "💍 Nhẫn Đồng Đôi", "price": 2500670, "desc": "Nhẫn khởi đầu cho lễ cưới trong hệ thống hôn nhân."},
    "ring_silver": {"name": "💍 Nhẫn Bạc Tình Yêu", "price": 15000870, "desc": "Nhẫn bạc dành cho cặp đôi."},
    "ring_gold": {"name": "💍 Nhẫn Vàng Vĩnh Cửu", "price": 75009800, "desc": "Nhẫn vàng cao cấp dành cho lễ cưới."},
    "ring_diamond": {"name": "💎 Nhẫn Kim Cương", "price": 500000000, "desc": "Nhẫn cưới quý hiếm."},
    "house_small": {"name": "🏡 Nhà Nhỏ Tổ Ấm", "price": 500000000, "desc": "Bất động sản cấp cơ bản cho cặp đôi."},
    "house_villa": {"name": "🏘️ Biệt Thự Hạnh Phúc", "price": 5000000000, "desc": "Bất động sản cao cấp cho cặp đôi."},
    "house_island": {"name": "🏝️ Đảo Riêng Tư", "price": 250000000000, "desc": "Bất động sản hiếm dành cho hôn nhân."},
    "love_chocolate": {"name": "🍫 Socola Tình Yêu", "price": 5000, "desc": "Quà tặng tương tác để bồi dưỡng tình cảm."},
    "love_flower": {"name": "💐 Bó Hoa Lãng Mạn", "price": 12000, "desc": "Tặng người thương để tăng điểm tình cảm."},
    "love_teddy": {"name": "🧸 Gấu Bông Ôm Ấp", "price": 30000, "desc": "Quà tặng tình cảm đáng yêu."},
    "love_date": {"name": "🕯️ Vé Hẹn Hò", "price": 80000, "desc": "Vật phẩm cho hoạt động hẹn hò của cặp đôi."},
    "buff_luck_potion_x3": {"name": "🧪 Thuốc Thần May Mắn x3 (1h)", "price": 20, "currency": "xu", "desc": "Tăng gấp 3 lần may mắn khi câu trong 60 phút."},
    "unbreakable_anvil": {"name": "🔨 Đe Cường Hóa Hoàng Kim (100% tỉ lệ)", "price": 100, "currency": "xu", "desc": "Đảm bảo 100% đập cần thành công lên cấp tiếp theo."},
    "potion_x2_coins_2h": {"name": "🧪 Thuốc Nhân Đôi Coins (2h)", "price": 0, "desc": "Nhân đôi (x2) toàn bộ lượng Coins nhận được từ bán cá trong 2 giờ.", "action_key": "BUFF_X2_COINS_2H"},
    "stardust_dust": {"name": "✨ Bụi Sao Lấp Lánh", "price": 1000000, "desc": "Bụi sao huyền ảo, nguyên liệu cần thiết để Tiến Cấp Sao cho trang bị đạt +150."},
    "black_pearl": {"name": "🦪 Ngọc Trai Đen", "price": 5000000, "desc": "Ngọc trai đen quý hiếm mở từ Rương Báu hoặc mò dưới đáy đại dương, dùng để Tiến Cấp Sao."},
    "end_crystal": {"name": "💎 Đá Pha Lê End", "price": 8000000, "desc": "Đá pha lê chứa năng lượng thần bí, dùng cùng 10M coins để Enchant gán dòng thuộc tính ngẫu nhiên."},
    "special_enchant_stone": {"name": "🔮 Đá Enchant Đặc Biệt", "price": 40000000, "desc": "Đá cổ xưa quý giá, dùng cùng 100M coins để mở thêm ô dòng Enchant vượt giới hạn trang bị."},
    "fertilizer_organic": {"name": "🌿 Phân Hữu Cơ Vi Sinh", "price": 3000, "desc": "Tăng 30% tốc độ lớn của cây trồng trong ô đất."},
    "fertilizer_speed": {"name": "⚡ Phân Bón Siêu Tốc", "price": 12000, "desc": "Rút ngắn 50% thời gian chín của cây trồng."},
    "fertilizer_yield": {"name": "🌾 Phân Bón Bội Thu", "price": 25000, "desc": "Nhân đôi (x2) sản lượng nông sản khi thu hoạch."},
    "fertilizer_revive": {"name": "💖 Phân Kích Rễ Hồi Sinh", "price": 15000, "desc": "Cứu sống cây trồng bị héo úa do thiếu nước hoặc bão giông."},
    "watering_can_copper": {"name": "🪣 Bình Tưới Đồng", "price": 50000, "desc": "Giữ ẩm đất liên tục suốt 4 giờ."},
    "watering_can_silver": {"name": "🥈 Bình Tưới Bạc", "price": 250000, "desc": "Giữ ẩm đất liên tục suốt 8 giờ."},
    "watering_can_mythic": {"name": "🌟 Bình Tưới Thần Thoại", "price": 1500000, "desc": "Giữ ẩm đất liên tục suốt 24 giờ."},
    "farmer_gloves": {"name": "🧤 Bao Tay Nhà Nông", "price": 100000, "desc": "Bắt sâu an toàn, tăng 50% tỉ lệ bắt được sâu bọ quý hiếm."},
    "greenhouse_cover": {"name": "🏛️ Lồng Kính Bảo Vệ", "price": 800000, "desc": "Lồng kính bảo vệ ô đất khỏi bão giông và sương giá."},
    "rain_talisman": {"name": "🌧️ Bùa Gọi Mưa", "price": 50000, "desc": "Triệu hồi cơn mưa rào, tự động tưới nước cho toàn bộ ô đất."},
    "sun_talisman": {"name": "☀️ Bùa Thái Dương", "price": 80000, "desc": "Xua tan bão giông và thời tiết xấu trong trang trại."}
}


TRASH_ITEMS = {
    "trash_can": {"name": "🥫 Vỏ Lon Rỉ Sét", "recycle_price": 1200, "desc": "Phế liệu kim loại tái chế."},
    "trash_boot": {"name": "👢 Chiếc Ủng Rách", "recycle_price": 1800, "desc": "Chiếc ủng da ngâm nước biển lâu ngày."},
    "trash_seaweed": {"name": "🪸 Rong Biển Mục", "recycle_price": 2500, "desc": "Dùng nấu canh hoặc tái chế."},
    "trash_tire": {"name": "🛞 Lốp Xe Cũ", "recycle_price": 5000, "desc": "Cao su nặng chìm đáy biển."},
    "trash_bottle": {"name": "🍾 Chai Thủy Tinh Kèm Thư", "recycle_price": 9000, "desc": "Chứa coin hoặc lời nhắn bí mật."},
    "trash_anchor": {"name": "⚓ Mỏ Neo Gãy", "recycle_price": 35000, "desc": "Khối sắt lớn giá trị tái chế cao."},
    "trash_plastic_bag": {"name": "🛍️ Túi Nilon Đại Dương", "recycle_price": 800, "desc": "Rác thải nhựa cần thu gom."},
    "trash_sunken_skull": {"name": "💀 Đầu Lâu Hải Tặc", "recycle_price": 60000, "desc": "Cổ vật ma mị thời đại cướp biển."},
}

CHESTS_DATA = {
    "chest_wood": {"name": "📦 Rương Gỗ Trôi Dạt", "req_key": None, "min_coin": 15000, "max_coin": 50000, "bait_pool": ["bait_normal", "bait_rare"], "rod_pool": [], "item_pool": ["stardust_dust"], "chance": 0.09},
    "chest_coral": {"name": "🪸 Rương San Hô", "req_key": None, "min_coin": 60000, "max_coin": 180000, "bait_pool": ["bait_rare", "bait_epic", "bait_mermaid_tear"], "rod_pool": [], "item_pool": ["pearl_ancient", "black_pearl", "stardust_dust"], "chance": 0.055},
    "chest_silver": {"name": "🪙 Rương Bạc Chìm", "req_key": "key_silver", "min_coin": 200000, "max_coin": 500000, "bait_pool": ["bait_epic", "bait_glow", "bait_mermaid_tear"], "rod_pool": [], "item_pool": ["pearl_ancient", "treasure_map", "black_pearl", "stardust_dust"], "chance": 0.035},
    "chest_shipwreck": {"name": "⚓ Rương Tàu Đắm Cổ", "req_key": "key_shipwreck", "min_coin": 600000, "max_coin": 1500000, "bait_pool": ["bait_glow", "bait_legend", "bait_abyss"], "rod_pool": ["rod_abyssal_reaper"], "item_pool": ["treasure_map", "relic_sea_stone", "black_pearl", "stardust_dust", "end_crystal"], "chance": 0.02},
    "chest_gold": {"name": "👑 Rương Hoàng Gia", "req_key": "key_gold", "min_coin": 1800000, "max_coin": 4500000, "bait_pool": ["bait_legend", "bait_dragon", "bait_abyss", "bait_golden"], "rod_pool": ["rod_poseidon"], "item_pool": ["relic_sea_stone", "relic_golden_scale", "black_pearl", "stardust_dust", "end_crystal"], "chance": 0.012},
    "chest_abyss": {"name": "🐙 Rương Thủy Quái Vực Sâu", "req_key": "key_abyss", "min_coin": 5000000, "max_coin": 12000000, "bait_pool": ["bait_dragon", "bait_abyss", "bait_kraken_tentacle", "bait_golden"], "rod_pool": ["rod_poseidon", "rod_abyssal_reaper"], "item_pool": ["relic_golden_scale", "treasure_map", "black_pearl", "stardust_dust", "end_crystal", "special_enchant_stone"], "chance": 0.006},
    "chest_void": {"name": "🌌 Rương Hư Không Vĩnh Hằng", "req_key": "key_void", "min_coin": 15000000, "max_coin": 45000000, "bait_pool": ["bait_abyss", "bait_golden", "bait_godly_essence", "bait_cosmic"], "rod_pool": ["rod_poseidon", "rod_abyssal_reaper", "rod_starlight"], "item_pool": ["relic_golden_scale", "relic_sea_stone", "treasure_map", "black_pearl", "stardust_dust", "end_crystal", "special_enchant_stone"], "chance": 0.0025},
}

WEATHER_CYCLE = [
    {"id": "sunny", "name": "☀️ Nắng Đẹp Rực Rỡ", "bonus_luck": 6, "mutation_rate": 0.05, "desc": "Mặt biển êm đềm, thuận lợi thả câu."},
    {"id": "rainy", "name": "🌧️ Mưa Giông Biển Sâu", "bonus_luck": 20, "mutation_rate": 0.09, "desc": "Sóng lớn kích thích cá tầng mặt."},
    {"id": "misty", "name": "🌫️ Sương Mù Ma Quái", "bonus_luck": 16, "mutation_rate": 0.16, "desc": "Tầm nhìn hạn chế, sinh vật cổ đại nổi lên."},
    {"id": "full_moon", "name": "🌕 Đêm Trăng Tròn Huyền Bí", "bonus_luck": 38, "mutation_rate": 0.24, "desc": "Ánh trăng huyền ảo thu hút cá thần kỳ bí."},
    {"id": "red_tide", "name": "🌊 Thủy Triều Đỏ Đột Biến", "bonus_luck": 32, "mutation_rate": 0.48, "desc": "Tỷ lệ cá đột biến gen tăng vọt."},
    {"id": "magnetic_storm", "name": "⚡ Bão Từ Trường Vực Thẳm", "bonus_luck": 50, "mutation_rate": 0.28, "desc": "Sóng điện từ kích động các loài thủy quái."},
    {"id": "eclipse", "name": "🌑 Nhật Thực Toàn Phần", "bonus_luck": 70, "mutation_rate": 0.55, "desc": "Bóng tối bao trùm, sinh vật tối thượng thức giấc."},
    {"id": "meteor_shower", "name": "🌠 Mưa Sao Băng Đại Dương", "bonus_luck": 95, "mutation_rate": 0.35, "desc": "Bụi sao băng kích thích cá cắn câu dồn dập."},
    {"id": "blizzard", "name": "❄️ Băng Giá Bắc Cực", "bonus_luck": 30, "mutation_rate": 0.40, "desc": "Cá đột biến Băng xuất hiện liên tục."},
    {"id": "cosmic_radiation", "name": "🪐 Bão Bức Xạ Vũ Trụ", "bonus_luck": 130, "mutation_rate": 0.65, "desc": "Năng lượng vũ trụ tràn xuống, cá hiếm xuất hiện dày đặc!"},
]

FISHING_ZONES = {
    "ven_bo": {
        "id": "ven_bo",
        "name": "🏖️ Bờ Biển Nắng Ấm",
        "icon": "🏖️",
        "min_level": 1,
        "luck_bonus": 0,
        "mutation_rate_bonus": 0.0,
        "desc": "Khu vực ven bờ biển dịu êm, sóng lặng, thuận lợi cho tân thủ mới vào nghề."
    },
    "ran_san_ho": {
        "id": "ran_san_ho",
        "name": "🪸 Rạn San Hô Rực Rỡ",
        "icon": "🪸",
        "min_level": 3,
        "luck_bonus": 15,
        "mutation_rate_bonus": 0.06,
        "desc": "Hệ sinh thái san hô trù phú, tăng khả năng cắn câu của các loài cá hiếm sắc màu."
    },
    "bien_sau": {
        "id": "bien_sau",
        "name": "🌊 Biển Khơi Thái Bình Dương",
        "icon": "🌊",
        "min_level": 5,
        "luck_bonus": 30,
        "mutation_rate_bonus": 0.12,
        "desc": "Vùng biển khơi dậy sóng lớn, tụ hội cá ngừ đại dương và các loài cá săn mồi cỡ lớn."
    },
    "vuc_mariana": {
        "id": "vuc_mariana",
        "name": "🕳️ Rãnh Vực Mariana Sâu Thẳm",
        "icon": "🕳️",
        "min_level": 8,
        "luck_bonus": 50,
        "mutation_rate_bonus": 0.20,
        "desc": "Bóng tối tuyệt đối và áp suất nghìn mét kích thích sinh vật cổ đại phát quang dị thường."
    },
    "nui_lua_ngam": {
        "id": "nui_lua_ngam",
        "name": "🌋 Vực Núi Lửa Dung Nham Biển",
        "icon": "🌋",
        "min_level": 12,
        "luck_bonus": 75,
        "mutation_rate_bonus": 0.30,
        "desc": "Nước biển sôi sục hòa trộn macma nóng bỏng, nơi sinh ra các đột biến Lửa và Nham Thạch cực hiếm."
    },
    "bac_cuc_bang": {
        "id": "bac_cuc_bang",
        "name": "❄️ Biển Băng Bắc Cực Vĩnh Hằng",
        "icon": "❄️",
        "min_level": 16,
        "luck_bonus": 110,
        "mutation_rate_bonus": 0.40,
        "desc": "Băng giá vĩnh cửu bao bọc các loài thủy quái tiền sử và đột biến Băng Tinh Thể huyền thoại."
    },
    "vuc_hu_khong": {
        "id": "vuc_hu_khong",
        "name": "🌌 Vực Hư Không Tinh Vân",
        "icon": "🌌",
        "min_level": 20,
        "luck_bonus": 160,
        "mutation_rate_bonus": 0.55,
        "desc": "Vết rách không thời gian nối liền đại dương với vũ trụ vô tận, mở ra cơ hội bắt đột biến Thần Vương tối thượng!"
    }
}

SIZES_CONFIG = [
    {"name": "Bé Tí", "multi": 0.75, "weight_range": (0.2, 1.5), "length_range": (5, 20)},
    {"name": "Tiêu Chuẩn", "multi": 1.0, "weight_range": (1.5, 6.0), "length_range": (20, 50)},
    {"name": "To Lớn", "multi": 1.5, "weight_range": (6.0, 25.0), "length_range": (50, 110)},
    {"name": "Khổng Lồ", "multi": 2.3, "weight_range": (25.0, 150.0), "length_range": (110, 300)},
    {"name": "Thần Thoại", "multi": 4.0, "weight_range": (150.0, 800.0), "length_range": (300, 750)},
]

DEX_MILESTONES = [
    {"count": 5, "reward_coin": 50000, "reward_bait": "bait_rare", "bait_amount": 3},
    {"count": 10, "reward_coin": 180000, "reward_bait": "bait_epic", "bait_amount": 3},
    {"count": 20, "reward_coin": 500000, "reward_bait": "bait_glow", "bait_amount": 4},
    {"count": 35, "reward_coin": 1500000, "reward_bait": "bait_legend", "bait_amount": 3},
    {"count": 50, "reward_coin": 4500000, "reward_bait": "bait_dragon", "bait_amount": 3},
    {"count": 70, "reward_coin": 10000000, "reward_bait": "bait_abyss", "bait_amount": 4},
    {"count": 100, "reward_coin": 25000000, "reward_bait": "bait_godly_essence", "bait_amount": 4},
]

CUSTOM_FISHING_ITEMS_FILE = BASE_DIR / "data" / "custom_fishing_items.json"
MASTER_SHOP_ITEMS = []


def rebuild_master_shop_items():
    global MASTER_SHOP_ITEMS
    MASTER_SHOP_ITEMS.clear()
    for k, v in RODS_CATALOG.items():
        if not v.get("chest_only") and k != "rod_owner":
            MASTER_SHOP_ITEMS.append({"id": k, "category": "rod", **v})
    for k, v in BAGS_UPGRADES.items():
        if k != "fish_bag_admin":
            MASTER_SHOP_ITEMS.append({"id": k, "category": "bag", **v})
    for k, v in PETS_CATALOG.items():
        MASTER_SHOP_ITEMS.append({"id": k, "category": "pet", **v})
    for k, v in BAITS_CATALOG.items():
        if v.get("buyable"):
            MASTER_SHOP_ITEMS.append({"id": k, "category": "bait", **v})
    for k, v in UTILITY_ITEMS.items():
        if v.get("price", 0) > 0:
            MASTER_SHOP_ITEMS.append({"id": k, "category": "item", **v})
    for k, v in SEEDS_CATALOG.items():
        y_range = v.get("harvest_yield", (v.get("yield_min", 2), v.get("yield_max", 5)))
        sell_val = v.get("crop_sell_price", v.get("sell_price", 500))
        grow_sec = v.get("growth_time", v.get("grow_seconds", 300))
        seasons = v.get("preferred_seasons", ["Bốn mùa"])
        c_name = v.get("crop_name", v.get("name", "Nông sản"))
        MASTER_SHOP_ITEMS.append({
            "id": k,
            "category": "seed",
            "name": f"Hạt Giống {v.get('name', k)}",
            "price": v.get("price", v.get("seed_price", 1000)),
            "currency": "coins",
            "desc": f"Thu hoạch: {y_range[0]}-{y_range[1]} {c_name} | Bán: {sell_val:,}c | Lớn: {grow_sec//60}p | Mùa: {', '.join(seasons)}"
        })
    for k, v in FARM_TOOLS_CATALOG.items():
        MASTER_SHOP_ITEMS.append({
            "id": k,
            "category": "farm_tool",
            "name": v["name"],
            "price": v.get("price", 5000),
            "currency": "coins",
            "desc": v.get("desc", "Dụng cụ nông nghiệp")
        })
    try:
        from Command.command_mining import PICKS_CATALOG, MINING_SUPPLIES
        for k, v in PICKS_CATALOG.items():
            if k != "pick_owner":
                MASTER_SHOP_ITEMS.append({"id": k, "category": "pick", **v})
        for k, v in MINING_SUPPLIES.items():
            MASTER_SHOP_ITEMS.append({"id": k, "category": "mine_supply", **v})
    except Exception:
        pass

    shop_overrides_file = BASE_DIR / "data" / "shop_overrides.json"
    if shop_overrides_file.exists():
        try:
            with open(shop_overrides_file, "r", encoding="utf-8") as f:
                overrides = json.load(f)
                if isinstance(overrides, dict):
                    for item in MASTER_SHOP_ITEMS:
                        iid = item.get("id")
                        if iid in overrides:
                            ov = overrides[iid]
                            item.update(ov)
                            cat = item.get("category")
                            if cat == "rod" and iid in RODS_CATALOG:
                                RODS_CATALOG[iid].update(ov)
                            elif cat == "bait" and iid in BAITS_CATALOG:
                                BAITS_CATALOG[iid].update(ov)
                            elif cat == "pet" and iid in PETS_CATALOG:
                                PETS_CATALOG[iid].update(ov)
                            elif cat == "item" and iid in UTILITY_ITEMS:
                                UTILITY_ITEMS[iid].update(ov)
                            elif cat == "bag" and iid in BAGS_UPGRADES:
                                BAGS_UPGRADES[iid].update(ov)
        except Exception:
            pass


def load_custom_fishing_items():
    if CUSTOM_FISHING_ITEMS_FILE.exists():
        try:
            with open(CUSTOM_FISHING_ITEMS_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                if isinstance(data, dict):
                    for k, v in data.get("rods", {}).items():
                        RODS_CATALOG[k] = v
                    for k, v in data.get("baits", {}).items():
                        BAITS_CATALOG[k] = v
                    for k, v in data.get("bags", {}).items():
                        BAGS_UPGRADES[k] = v
                    for k, v in data.get("pets", {}).items():
                        PETS_CATALOG[k] = v
                    for k, v in data.get("items", {}).items():
                        UTILITY_ITEMS[k] = v
                    for k, v in data.get("chests", {}).items():
                        CHESTS_DATA[k] = v
        except Exception:
            pass
    rebuild_master_shop_items()


def add_custom_item(item_type: str, item_id: str, item_data: dict):
    CUSTOM_FISHING_ITEMS_FILE.parent.mkdir(parents=True, exist_ok=True)
    all_custom = {"rods": {}, "baits": {}, "bags": {}, "pets": {}, "items": {}, "chests": {}}
    if CUSTOM_FISHING_ITEMS_FILE.exists():
        try:
            with open(CUSTOM_FISHING_ITEMS_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                if isinstance(data, dict):
                    all_custom.update(data)
        except Exception:
            pass

    if item_type in ("rod", "rods"):
        all_custom.setdefault("rods", {})[item_id] = item_data
        RODS_CATALOG[item_id] = item_data
    elif item_type in ("bait", "baits"):
        all_custom.setdefault("baits", {})[item_id] = item_data
        BAITS_CATALOG[item_id] = item_data
    elif item_type in ("bag", "bags"):
        all_custom.setdefault("bags", {})[item_id] = item_data
        BAGS_UPGRADES[item_id] = item_data
    elif item_type in ("pet", "pets"):
        all_custom.setdefault("pets", {})[item_id] = item_data
        PETS_CATALOG[item_id] = item_data
    elif item_type in ("item", "items", "troll"):
        all_custom.setdefault("items", {})[item_id] = item_data
        UTILITY_ITEMS[item_id] = item_data
    elif item_type in ("chest", "chests"):
        all_custom.setdefault("chests", {})[item_id] = item_data
        CHESTS_DATA[item_id] = item_data

    with open(CUSTOM_FISHING_ITEMS_FILE, "w", encoding="utf-8") as f:
        json.dump(all_custom, f, indent=4, ensure_ascii=False)

    rebuild_master_shop_items()


def check_user_item_expiration(user_id: int) -> list:
    """
    Kiểm tra hạn sử dụng (HSD) các vật phẩm, cần câu, pet của người chơi.
    - Nếu hết hạn: tự động tháo trang bị nếu đang equip.
    - Nếu không thể gia hạn (renewable=False): xóa vật phẩm khỏi túi.
    - Nếu có thể gia hạn (renewable=True): đánh dấu hết hạn để người dùng gia hạn tiếp tục sử dụng.
    Trả về danh sách thông báo nhắc nhở.
    """
    u_fish = get_user_fishing(user_id)
    now = time.time()
    expired_notifs = []
    item_exp = u_fish.setdefault("item_expiry", {})

    user_rods = u_fish.setdefault("rods", {})
    for rid in list(user_rods.keys()):
        r_entry = user_rods[rid]
        exp_time = None
        renewable = False
        duration_days = 7
        if isinstance(r_entry, dict) and r_entry.get("expires_at"):
            exp_time = r_entry["expires_at"]
            renewable = r_entry.get("renewable", False)
            duration_days = r_entry.get("duration_days", 7)
        elif rid in item_exp:
            exp_time = item_exp[rid].get("expires_at")
            renewable = item_exp[rid].get("renewable", False)
            duration_days = item_exp[rid].get("duration_days", 7)
        elif rid in RODS_CATALOG and RODS_CATALOG[rid].get("has_expiry"):
            exp_info = RODS_CATALOG[rid]
            renewable = exp_info.get("renewable", False)
            duration_days = exp_info.get("duration_days", 7)

        if exp_time and now > exp_time:
            r_name = RODS_CATALOG.get(rid, {}).get("name", rid)
            if u_fish.get("equipped_rod") == rid:
                u_fish["equipped_rod"] = None
                expired_notifs.append(f"🎣 Cần câu **{r_name}** đã hết hạn và tự động tháo rời!")
            if not renewable:
                user_rods.pop(rid, None)
                item_exp.pop(rid, None)
                expired_notifs.append(f"⚠️ Cần câu **{r_name}** (vật phẩm không thể gia hạn) đã hết hạn và biến mất!")
            else:
                if isinstance(r_entry, dict):
                    r_entry["expired"] = True
                expired_notifs.append(f"⏳ Cần câu **{r_name}** đã hết hạn sử dụng. Hãy gia hạn để tiếp tục sử dụng!")

    user_pets = u_fish.setdefault("pets", [])
    for pid in list(user_pets):
        exp_time = None
        renewable = False
        if pid in item_exp:
            exp_time = item_exp[pid].get("expires_at")
            renewable = item_exp[pid].get("renewable", False)
        elif pid in PETS_CATALOG and PETS_CATALOG[pid].get("has_expiry"):
            exp_info = PETS_CATALOG[pid]
            renewable = exp_info.get("renewable", False)

        if exp_time and now > exp_time:
            p_name = PETS_CATALOG.get(pid, {}).get("name", pid)
            if u_fish.get("equipped_pet") == pid:
                u_fish["equipped_pet"] = None
                expired_notifs.append(f"🐾 Thú cưng **{p_name}** đã hết hạn đồng hành và tự động tháo rời!")
            if not renewable:
                if pid in user_pets:
                    user_pets.remove(pid)
                item_exp.pop(pid, None)
                expired_notifs.append(f"⚠️ Thú cưng **{p_name}** (không thể gia hạn) đã hết hạn hợp đồng!")
            else:
                item_exp.setdefault(pid, {})["expired"] = True
                expired_notifs.append(f"⏳ Thú cưng **{p_name}** đã hết hạn. Hãy gia hạn để pet tiếp tục buff chỉ số!")

    user_items = u_fish.setdefault("items", {})
    for iid in list(user_items.keys()):
        if iid in item_exp:
            exp_time = item_exp[iid].get("expires_at")
            renewable = item_exp[iid].get("renewable", False)
            if exp_time and now > exp_time:
                it_name = UTILITY_ITEMS.get(iid, {}).get("name", iid)
                if not renewable:
                    user_items.pop(iid, None)
                    item_exp.pop(iid, None)
                    expired_notifs.append(f"⚠️ Vật phẩm **{it_name}** (không thể gia hạn) đã hết hạn sử dụng và biến mất!")
                else:
                    item_exp[iid]["expired"] = True
                    expired_notifs.append(f"⏳ Vật phẩm **{it_name}** đã hết hạn. Cần gia hạn để dùng tiếp!")

    if expired_notifs:
        save_fishing_data()
    return expired_notifs


async def renew_user_item(user_id: int, item_id: str, guild_id: int) -> tuple:
    """
    Gia hạn thêm thời gian sử dụng cho vật phẩm có HSD.
    Trả về (thành_công: bool, thông_báo: str).
    """
    u_fish = get_user_fishing(user_id)
    item_exp = u_fish.setdefault("item_expiry", {})

    catalog_info = (
        RODS_CATALOG.get(item_id)
        or PETS_CATALOG.get(item_id)
        or UTILITY_ITEMS.get(item_id)
        or CHESTS_DATA.get(item_id)
        or {}
    )
    exp_info = item_exp.get(item_id, {})

    has_item = (
        item_id in u_fish.get("rods", {})
        or item_id in u_fish.get("pets", [])
        or u_fish.get("items", {}).get(item_id, 0) > 0
        or item_id in item_exp
    )
    if not has_item:
        return False, f"Bạn không sở hữu vật phẩm `{item_id}` để gia hạn!"

    renewable = exp_info.get("renewable", catalog_info.get("renewable", True))
    if not renewable:
        return False, f"Vật phẩm **{catalog_info.get('name', item_id)}** là loại **KHÔNG THỂ GIA HẠN**!"

    duration_days = exp_info.get("duration_days", catalog_info.get("duration_days", 7))
    price = exp_info.get("renew_price", catalog_info.get("renew_price", catalog_info.get("price", 10000)))
    currency = exp_info.get("renew_currency", catalog_info.get("renew_currency", catalog_info.get("currency", "coins")))

    u_data = await get_user_data(guild_id, user_id)
    if currency == "xu":
        if u_data.get("xu", 0) < price:
            return False, f"Bạn không đủ `{price:,}` Xu để gia hạn (Hiện có: `{u_data.get('xu', 0):,}` Xu)!"
        await update_user_xu(guild_id, user_id, -price)
    else:
        if u_data.get("coins", 0) < price:
            return False, f"Bạn không đủ `{price:,}` Coin để gia hạn (Hiện có: `{u_data.get('coins', 0):,}` Coin)!"
        await update_user_coins(guild_id, user_id, -price)

    now = time.time()
    cur_exp = exp_info.get("expires_at", now)
    base_time = max(now, cur_exp)
    new_exp = base_time + (duration_days * 86400)

    item_exp[item_id] = {
        "expires_at": new_exp,
        "renewable": renewable,
        "duration_days": duration_days,
        "renew_price": price,
        "renew_currency": currency,
        "name": catalog_info.get("name", item_id)
    }

    if item_id in u_fish.get("rods", {}):
        if isinstance(u_fish["rods"][item_id], dict):
            u_fish["rods"][item_id]["expires_at"] = new_exp
            u_fish["rods"][item_id].pop("expired", None)

    save_fishing_data()
    item_name = catalog_info.get("name", item_id)
    return True, f"🎉 Gia hạn thành công **{item_name}** thêm **{duration_days} ngày**! (Hạn mới: <t:{int(new_exp)}:R> - Chi phí: `{price:,}` {currency})"


load_custom_fishing_items()

fishing_state = {
    "users": {},
    "event": {"active": False, "name": "Đại Dương Bình Yên", "bonus_luck": 0, "price_multi": 1.0, "end_time": 0},
    "tournament": {"active": False, "name": "", "end_time": 0, "participants": {}},
    "fishing_channels": {},
    "code_channels": {},
    "giftcodes": {},
    "forced_weather": None,
    "marriages": {},
    "couples": {},
    "pairings": {},
    "court_cases": {},
}


def load_fishing_data():
    global fishing_state
    if FISHING_DATA_FILE.exists():
        try:
            with open(FISHING_DATA_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                if isinstance(data, dict):
                    fishing_state.update(data)
        except Exception:
            pass


def save_fishing_data():
    FISHING_DATA_FILE.parent.mkdir(parents=True, exist_ok=True)
    try:
        with open(FISHING_DATA_FILE, "w", encoding="utf-8") as f:
            json.dump(fishing_state, f, indent=4, ensure_ascii=False)
    except Exception:
        pass


load_fishing_data()


def get_user_fishing(user_id: int) -> dict:
    uid = str(user_id)
    users = fishing_state.setdefault("users", {})
    if uid not in users:
        users[uid] = {
            "equipped_rod": None,
            "equipped_bait": None,
            "equipped_pet": None,
            "rods": {},
            "baits": {},
            "chests": {k: 0 for k in CHESTS_DATA},
            "items": {},
            "trash_bag": {},
            "pets": [],
            "purchased_bags": [],
            "fish_bag": [],
            "aquarium": [],
            "aquarium_slots": 6,
            "aquarium_favorite": None,
            "aquarium_likes": [],
            "aquarium_last_claim": time.time(),
            "buffs": {},
            "fishdex": {},
            "dex_claimed_milestones": [],
            "biggest_catch": {"name": "Chưa có", "weight": 0.0, "length": 0.0},
            "max_bag": 30,
            "last_cast": 0,
            "stats": {"total_caught": 0, "broken_rods": 0, "total_earned": 0, "total_trash": 0},
        }
    else:
        for k in CHESTS_DATA:
            users[uid].setdefault("chests", {}).setdefault(k, 0)
        users[uid].setdefault("items", {})
        users[uid].setdefault("trash_bag", {})
        users[uid].setdefault("aquarium", [])
        users[uid].setdefault("aquarium_slots", 6)
        users[uid].setdefault("aquarium_favorite", None)
        users[uid].setdefault("aquarium_likes", [])
        users[uid].setdefault("aquarium_last_claim", time.time())
        users[uid].setdefault("buffs", {})
        users[uid].setdefault("biggest_catch", {"name": "Chưa có", "weight": 0.0, "length": 0.0})
        users[uid].setdefault("fishdex", {})
        users[uid].setdefault("dex_claimed_milestones", [])
        users[uid].setdefault("pets", [])
        users[uid].setdefault("purchased_bags", [])
        users[uid].setdefault("max_bag", 30)
        users[uid].setdefault("fish_bag", [])
        users[uid].setdefault("rods", {})
        users[uid].setdefault("baits", {})
        users[uid].setdefault("last_cast", 0)
        st = users[uid].setdefault("stats", {})
        for sk in ("total_caught", "broken_rods", "total_earned", "total_trash"):
            st.setdefault(sk, 0)
    return users[uid]


class ShopQuantityModal(discord.ui.Modal):
    quantity_input = discord.ui.TextInput(
        label="Số lượng muốn mua",
        placeholder="Nhập số lượng (Ví dụ: 1, 5, 10, 50...)",
        default="1",
        required=True,
        max_length=5
    )

    def __init__(self, item: dict, shop_view: "FishingShopView"):
        super().__init__(title=f"🛒 Mua: {item['name'][:35]}")
        self.item = item
        self.shop_view = shop_view

    async def on_submit(self, interaction: discord.Interaction):
        raw_val = self.quantity_input.value.strip().replace(",", "")
        if not raw_val.isdigit() or int(raw_val) <= 0:
            return await interaction.response.send_message("❌ Số lượng mua phải là một số nguyên dương hợp lệ!", ephemeral=True)

        quantity = int(raw_val)
        cat = self.item["category"]
        item_id = self.item["id"]

        if cat in ("rod", "pet", "pick") and quantity > 1:
            return await interaction.response.send_message("⚠️ Cần câu, Thú cưng và Cuốc đào chỉ có thể mua tối đa 1 cái mỗi lần!", ephemeral=True)

        user_id = self.shop_view.author.id
        u_data = await get_user_data(self.shop_view.guild_id, user_id)
        is_xu = (self.item.get("currency") == "xu")
        wallet = int(u_data.get("xu", 0)) if is_xu else u_data.get("coins", 0)
        curr_label = "xu" if is_xu else "coin"
        curr_icon = "💎" if is_xu else "🪙"
        total_cost = self.item["price"] * quantity

        if self.item["id"] == "rod_owner" and user_id != OWNER_ID:
            return await interaction.response.send_message("👑 Vật phẩm này chỉ dành riêng cho Chủ Bot!", ephemeral=True)

        if wallet < total_cost:
            return await interaction.response.send_message(f"❌ Bạn không đủ tiền! Cần **`{total_cost:,}` {curr_label}** cho **{quantity}x** món này (Số dư: `{wallet:,}` {curr_label}).", ephemeral=True)

        u_fish = get_user_fishing(user_id)

        if cat == "rod":
            if item_id in u_fish.setdefault("rods", {}):
                return await interaction.response.send_message("⚠️ Bạn đã sở hữu cần câu này rồi!", ephemeral=True)
            u_fish.setdefault("rods", {})[item_id] = {
                "name": self.item["name"],
                "durability": self.item.get("durability", 100),
                "max_durability": self.item.get("durability", 100),
                "luck": self.item.get("luck", 1),
                "price": self.item["price"],
                "currency": self.item.get("currency", "coins"),
                "refine": 0
            }
            if not u_fish.get("equipped_rod"):
                u_fish["equipped_rod"] = item_id

        elif cat == "bait":
            u_fish.setdefault("baits", {})[item_id] = u_fish.setdefault("baits", {}).get(item_id, 0) + quantity
            if not u_fish.get("equipped_bait"):
                u_fish["equipped_bait"] = item_id

        elif cat == "bag":
            purchased = u_fish.setdefault("purchased_bags", [])
            if item_id in purchased:
                return await interaction.response.send_message("⚠️ Bạn đã mua gói nâng cấp túi cá này rồi!", ephemeral=True)
            purchased.append(item_id)
            u_fish["max_bag"] = u_fish.get("max_bag", 30) + self.item.get("extra_slots", 10)

        elif cat == "pet":
            pets = u_fish.setdefault("pets", [])
            if item_id in pets:
                return await interaction.response.send_message("⚠️ Bạn đã sở hữu thú cưng này rồi!", ephemeral=True)
            pets.append(item_id)
            if not u_fish.get("equipped_pet"):
                u_fish["equipped_pet"] = item_id

        elif cat == "item":
            u_fish.setdefault("items", {})[item_id] = u_fish.setdefault("items", {}).get(item_id, 0) + quantity

        elif cat == "seed":
            farm = u_fish.setdefault("farm", {})
            seeds = farm.setdefault("seeds", {})
            seeds[item_id] = seeds.get(item_id, 0) + quantity

        elif cat == "farm_tool":
            farm = u_fish.setdefault("farm", {})
            tools = farm.setdefault("tools", {})
            tools[item_id] = tools.get(item_id, 0) + quantity
            u_fish.setdefault("items", {})[item_id] = u_fish.setdefault("items", {}).get(item_id, 0) + quantity

        elif cat == "pick":
            from Command.command_mining import get_user_mining, save_mining_data
            u_mine = get_user_mining(user_id)
            if item_id in u_mine.setdefault("picks", {}):
                return await interaction.response.send_message("⚠️ Bạn đã sở hữu cuốc đào này rồi!", ephemeral=True)
            u_mine.setdefault("picks", {})[item_id] = {
                "name": self.item["name"],
                "durability": self.item.get("durability", 100),
                "max_durability": self.item.get("durability", 100),
                "luck": self.item.get("luck", 1),
                "refine": 0,
                "stars": 0,
                "enchants": []
            }
            if not u_mine.get("equipped_pick"):
                u_mine["equipped_pick"] = item_id
            save_mining_data()

        elif cat == "mine_supply":
            from Command.command_mining import get_user_mining, save_mining_data
            u_mine = get_user_mining(user_id)
            if "tnt" in item_id or "fuel" in item_id or "lantern" in item_id:
                u_mine.setdefault("supplies", {})[item_id] = u_mine.setdefault("supplies", {}).get(item_id, 0) + quantity
            elif "bag" in item_id:
                u_mine["max_bag"] = u_mine.get("max_bag", 50) + self.item.get("extra_slots", 30)
            save_mining_data()

        if is_xu:
            await update_user_xu(self.shop_view.guild_id, user_id, -total_cost)
        else:
            await update_user_coins(self.shop_view.guild_id, user_id, -total_cost)
        save_fishing_data()

        new_data = await get_user_data(self.shop_view.guild_id, user_id)
        self.shop_view._refresh_components()
        new_embed = self.shop_view.build_embed(new_data.get("coins", 0), int(new_data.get("xu", 0)))
        await interaction.response.edit_message(embed=new_embed, view=self.shop_view)
        await interaction.followup.send(f"🎉 Mua thành công **{quantity}x {self.item['name']}** với tổng giá **{curr_icon} `{total_cost:,}` {curr_label}**!", ephemeral=True)


class RedeemCodeModal(discord.ui.Modal, title="🎁 Nhập Mã Giftcode"):
    code_input = discord.ui.TextInput(
        label="Nhập mã Giftcode",
        placeholder="Ví dụ: SAKURA2026, TANTHU...",
        required=True,
        max_length=40
    )

    def __init__(self, author: discord.Member, guild_id: int):
        super().__init__()
        self.author = author
        self.guild_id = guild_id

    async def on_submit(self, interaction: discord.Interaction):
        code_str = self.code_input.value.strip().upper()
        codes = fishing_state.setdefault("giftcodes", {})

        if code_str not in codes:
            return await interaction.response.send_message("❌ Mã Giftcode không tồn tại hoặc đã hết hạn!", ephemeral=True)

        c_data = codes[code_str]
        now = time.time()

        if c_data.get("expires_at", 0) > 0 and now > c_data["expires_at"]:
            return await interaction.response.send_message("⌛ Mã Giftcode này đã hết hạn sử dụng!", ephemeral=True)

        used_by = c_data.setdefault("used_by", [])
        if self.author.id in used_by:
            return await interaction.response.send_message("⚠️ Bạn đã sử dụng mã Giftcode này rồi!", ephemeral=True)

        max_uses = c_data.get("max_uses", 0)
        if max_uses > 0 and len(used_by) >= max_uses:
            return await interaction.response.send_message("❌ Mã Giftcode này đã hết lượt nhập!", ephemeral=True)

        rewards = c_data.get("rewards", {})
        u_fish = get_user_fishing(self.author.id)
        reward_lines = []

        coin_amt = rewards.get("coins", 0)
        if coin_amt > 0:
            await update_user_coins(self.guild_id, self.author.id, coin_amt)
            reward_lines.append(f"• 💰 **`+{coin_amt:,}` coin**")

        xu_amt = rewards.get("xu", 0)
        if xu_amt > 0:
            try:
                from data.database import update_user_xu
                await update_user_xu(self.guild_id, self.author.id, xu_amt)
                reward_lines.append(f"• 🪙 **`+{xu_amt:,}` xu**")
            except Exception:
                pass

        for r_data in rewards.get("rods", []):
            rid = r_data.get("id") if isinstance(r_data, dict) else r_data
            refine = int(r_data.get("refine", 0)) if isinstance(r_data, dict) else 0
            stars = int(r_data.get("stars", 0)) if isinstance(r_data, dict) else 0
            if rid in RODS_CATALOG:
                r_item = RODS_CATALOG[rid]
                base_dur = r_item.get("durability", 100)
                max_dur = base_dur + (refine * 50) + (stars * 500)
                luck = r_item.get("luck", 5) + (refine * 15) + (stars * 100)
                u_fish.setdefault("rods", {})[rid] = {
                    "name": r_item["name"],
                    "durability": max_dur,
                    "max_durability": max_dur,
                    "luck": luck,
                    "price": r_item.get("price", 0),
                    "refine": refine,
                    "stars": stars
                }
                if not u_fish.get("equipped_rod"):
                    u_fish["equipped_rod"] = rid
                stat_str = f" (+{refine} | {stars}⭐)" if (refine > 0 or stars > 0) else ""
                reward_lines.append(f"• 🎣 **1x {r_item['name']}{stat_str}**")

        for p_data in rewards.get("picks", []):
            try:
                from Command.command_mining import get_user_mining, save_mining_data as save_mining, PICKS_CATALOG
                pkid = p_data.get("id") if isinstance(p_data, dict) else p_data
                refine = int(p_data.get("refine", 0)) if isinstance(p_data, dict) else 0
                stars = int(p_data.get("stars", 0)) if isinstance(p_data, dict) else 0
                if pkid in PICKS_CATALOG:
                    u_mine = get_user_mining(self.author.id)
                    p_item = PICKS_CATALOG[pkid]
                    base_dur = p_item.get("durability") or p_item.get("max_durability", 60)
                    max_dur = base_dur + (refine * 30) + (stars * 300)
                    luck = p_item.get("luck", 5) + (refine * 10) + (stars * 50)
                    u_mine.setdefault("picks", {})[pkid] = {
                        "id": pkid,
                        "name": p_item["name"],
                        "durability": max_dur,
                        "max_durability": max_dur,
                        "luck": luck,
                        "refine": refine,
                        "stars": stars
                    }
                    if not u_mine.get("equipped_pick"):
                        u_mine["equipped_pick"] = pkid
                    save_mining()
                    stat_str = f" (+{refine} | {stars}⭐)" if (refine > 0 or stars > 0) else ""
                    reward_lines.append(f"• ⛏️ **1x {p_item['name']}{stat_str}**")
            except Exception:
                pass

        for bid, amt in rewards.get("baits", {}).items():
            if bid in BAITS_CATALOG and amt > 0:
                u_fish.setdefault("baits", {})[bid] = u_fish.setdefault("baits", {}).get(bid, 0) + amt
                reward_lines.append(f"• 🪱 **{amt}x {BAITS_CATALOG[bid]['name']}**")

        for cid, amt in rewards.get("chests", {}).items():
            if cid in CHESTS_DATA and amt > 0:
                u_fish.setdefault("chests", {})[cid] = u_fish.setdefault("chests", {}).get(cid, 0) + amt
                reward_lines.append(f"• 📦 **{amt}x {CHESTS_DATA[cid]['name']}**")

        for pet_entry in rewards.get("pets", []):
            pid = pet_entry.get("id") if isinstance(pet_entry, dict) else pet_entry
            stars = int(pet_entry.get("stars", 0)) if isinstance(pet_entry, dict) else 0
            refine = int(pet_entry.get("refine", 0)) if isinstance(pet_entry, dict) else 0
            if pid in PETS_CATALOG:
                if pid not in u_fish.setdefault("pets", []):
                    u_fish["pets"].append(pid)
                u_fish.setdefault("pets_detail", {})[pid] = {
                    "stars": stars,
                    "refine": refine
                }
                stat_str = f" ({stars}⭐ | Đột phá +{refine})" if (stars > 0 or refine > 0) else ""
                reward_lines.append(f"• 🐾 **Pet: {PETS_CATALOG[pid]['name']}{stat_str}**")

        for iid, amt in rewards.get("items", {}).items():
            if iid in UTILITY_ITEMS and amt > 0:
                u_fish.setdefault("items", {})[iid] = u_fish.setdefault("items", {}).get(iid, 0) + amt
                reward_lines.append(f"• ✨ **{amt}x {UTILITY_ITEMS[iid]['name']}**")

        try:
            from Command.farm_system import get_user_farm, SEEDS_CATALOG, CROPS_CATALOG, FARM_TOOLS_CATALOG
            user_farm = get_user_farm(u_fish)
            for sid, amt in rewards.get("farm_seeds", {}).items():
                if amt > 0:
                    user_farm.setdefault("seeds", {})[sid] = user_farm.setdefault("seeds", {}).get(sid, 0) + int(amt)
                    sname = SEEDS_CATALOG.get(sid, {}).get("name", sid)
                    reward_lines.append(f"• 🌱 **{amt}x Hạt Giống: {sname}**")

            for cid, amt in rewards.get("farm_crops", {}).items():
                if amt > 0:
                    user_farm.setdefault("crops", {})[cid] = user_farm.setdefault("crops", {}).get(cid, 0) + int(amt)
                    cname = CROPS_CATALOG.get(cid, {}).get("name", cid)
                    reward_lines.append(f"• 🌾 **{amt}x Nông Sản: {cname}**")

            for tid, amt in rewards.get("farm_tools", {}).items():
                if amt > 0:
                    user_farm.setdefault("tools", {})[tid] = user_farm.setdefault("tools", {}).get(tid, 0) + int(amt)
                    tname = FARM_TOOLS_CATALOG.get(tid, {}).get("name", tid)
                    reward_lines.append(f"• 🚜 **{amt}x Dụng Cụ: {tname}**")

            for fid, amt in rewards.get("fertilizers", {}).items():
                if amt > 0:
                    user_farm.setdefault("fertilizers", {})[fid] = user_farm.setdefault("fertilizers", {}).get(fid, 0) + int(amt)
                    fname = FARM_TOOLS_CATALOG.get(fid, {}).get("name", fid)
                    reward_lines.append(f"• 🧪 **{amt}x Phân Bón: {fname}**")
        except Exception:
            pass

        for c_item in rewards.get("custom_items", []):
            try:
                c_id = str(c_item.get("id", "")).strip()
                if not c_id:
                    continue
                c_cat = str(c_item.get("category", "items")).strip()
                c_amt = max(1, int(c_item.get("amount", 1)))
                c_name = str(c_item.get("name", c_id)).strip()
                c_refine = int(c_item.get("refine", 0))
                c_stars = int(c_item.get("stars", 0))

                if c_cat == "rods":
                    u_fish.setdefault("rods", {})[c_id] = {
                        "name": c_name, "durability": 200, "max_durability": 200, "luck": 50,
                        "refine": c_refine, "stars": c_stars
                    }
                    stat_str = f" (+{c_refine} | {c_stars}⭐)" if (c_refine > 0 or c_stars > 0) else ""
                    reward_lines.append(f"• 🎣 **1x {c_name}{stat_str}**")
                elif c_cat == "picks":
                    from Command.command_mining import get_user_mining, save_mining_data as save_mining
                    u_mine = get_user_mining(self.author.id)
                    u_mine.setdefault("picks", {})[c_id] = {
                        "id": c_id, "name": c_name, "durability": 250, "max_durability": 250,
                        "luck": 15, "refine": c_refine, "stars": c_stars
                    }
                    save_mining()
                    stat_str = f" (+{c_refine} | {c_stars}⭐)" if (c_refine > 0 or c_stars > 0) else ""
                    reward_lines.append(f"• ⛏️ **1x {c_name}{stat_str}**")
                elif c_cat in ("pets", "pet"):
                    if c_id not in u_fish.setdefault("pets", []):
                        u_fish["pets"].append(c_id)
                    u_fish.setdefault("pets_detail", {})[c_id] = {"stars": c_stars, "refine": c_refine}
                    stat_str = f" ({c_stars}⭐ | Đột phá +{c_refine})" if (c_stars > 0 or c_refine > 0) else ""
                    reward_lines.append(f"• 🐾 **Thú Cưng: {c_name}{stat_str}**")
                elif c_cat in ("farm_seeds", "seeds"):
                    from Command.farm_system import get_user_farm
                    get_user_farm(u_fish).setdefault("seeds", {})[c_id] = get_user_farm(u_fish).setdefault("seeds", {}).get(c_id, 0) + c_amt
                    reward_lines.append(f"• 🌱 **{c_amt}x Hạt Giống: {c_name}**")
                elif c_cat in ("farm_crops", "crops"):
                    from Command.farm_system import get_user_farm
                    get_user_farm(u_fish).setdefault("crops", {})[c_id] = get_user_farm(u_fish).setdefault("crops", {}).get(c_id, 0) + c_amt
                    reward_lines.append(f"• 🌾 **{c_amt}x Nông Sản: {c_name}**")
                else:
                    u_fish.setdefault("items", {})[c_id] = u_fish.setdefault("items", {}).get(c_id, 0) + c_amt
                    reward_lines.append(f"• 🎁 **{c_amt}x {c_name}**")
            except Exception:
                pass

        ores_dict = rewards.get("ores", {})
        if ores_dict and isinstance(ores_dict, dict):
            try:
                from Command.command_mining import get_user_mining, save_mining_data as save_mining, ORES_CATALOG
                u_mine = get_user_mining(self.author.id)
                ore_bag = u_mine.setdefault("ore_bag", [])
                for oid, count in ores_dict.items():
                    if count > 0:
                        oinfo = ORES_CATALOG.get(oid, {"name": oid, "rarity": "rare", "price": 1000})
                        for _ in range(int(count)):
                            ore_bag.append({
                                "id": oid,
                                "name": oinfo.get("name", oid),
                                "rarity": oinfo.get("rarity", "rare"),
                                "price": oinfo.get("price", 1000),
                                "weight": 2.5,
                                "depth": 50,
                                "mutation": None,
                                "time": int(time.time())
                            })
                        reward_lines.append(f"• 💎 **{count}x {oinfo.get('name', oid)}**")
                save_mining()
            except Exception:
                pass

        supplies_dict = rewards.get("supplies", {})
        if supplies_dict and isinstance(supplies_dict, dict):
            try:
                from Command.command_mining import get_user_mining, save_mining_data as save_mining, MINING_SUPPLIES
                u_mine = get_user_mining(self.author.id)
                user_supplies = u_mine.setdefault("supplies", {})
                for sid, count in supplies_dict.items():
                    if count > 0:
                        sinfo = MINING_SUPPLIES.get(sid, {"name": sid})
                        user_supplies[sid] = user_supplies.get(sid, 0) + int(count)
                        reward_lines.append(f"• 🧨 **{count}x {sinfo.get('name', sid)}**")
                save_mining()
            except Exception:
                pass

        used_by.append(self.author.id)
        save_fishing_data()

        embed = discord.Embed(
            title="🎉 NHẬP MÃ GIFTCODE THÀNH CÔNG!",
            description="Chúc mừng bạn đã nhận được các phần thưởng sau:\n" + "\n".join(reward_lines),
            color=discord.Color.green()
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)


class ItemTargetModal(discord.ui.Modal):
    def __init__(self, item_id: str, author: discord.Member):
        titles = {
            "rename_card": "📝 Đổi Biệt Danh Người Khác",
            "mute_card": "🔇 Khóa Mõm (Mute 30s)",
            "voice_kick": "🔊 Trục Xuất Khỏi Phòng Thoại",
            "bomb_card": "💣 Đặt Bom Hẹn Giờ Troll",
            "ghost_ping": "👻 Thẻ Ghost Ping Bí Ẩn",
            "banana_peel": "🍌 Đặt Bẫy Vỏ Chuối",
            "mystery_box": "🎁 Tặng Hộp Quà Bí Ẩn",
            "reverse_card": "🔀 Đảo Ngược Ngôn Từ",
            "freeze_card": "🧊 Đóng Băng Cần Câu",
            "steal_fish_card": "🦹 Móc Trộm Cá Trong Giỏ",
            "fake_nitro": "💎 Tặng Fake Nitro Rickroll",
            "frog_potion": "🐸 Biến Nạn Nhân Thành Ếch",
            "slap_fish": "🐟 Tát Bằng Cá Hồi",
            "cursed_bait": "🪱 Nguyền Rủa Mồi Câu",
            "troll_box": "📦 Hộp Quà Lừa Tình",
        }
        item_data = UTILITY_ITEMS.get(item_id, {})
        def_title = item_data.get("name", "Sử Dụng Vật Phẩm Troll")
        super().__init__(title=titles.get(item_id, def_title[:45]))
        self.item_id = item_id
        self.author = author

        self.target_input = discord.ui.TextInput(
            label="ID hoặc @Mention thành viên mục tiêu",
            placeholder="Nhập ID (Ví dụ: 123456789012345678)",
            required=True,
            max_length=30
        )
        self.add_item(self.target_input)

        if item_id == "rename_card":
            self.extra_input = discord.ui.TextInput(
                label="Biệt danh mới muốn đổi thành",
                placeholder="Nhập tên mới (tối đa 32 ký tự)",
                required=True,
                max_length=32
            )
            self.add_item(self.extra_input)
        elif item_id == "bomb_card":
            self.extra_input = discord.ui.TextInput(
                label="Lời nhắn gài bom",
                placeholder="Ví dụ: Vĩnh biệt người anh em!",
                default="💣 BÙÙÙM! Bạn đã dính phải bom nổ chậm!",
                required=False,
                max_length=80
            )
            self.add_item(self.extra_input)

    async def on_submit(self, interaction: discord.Interaction):
        guild = interaction.guild
        author_id = self.author.id
        u_fish = get_user_fishing(author_id)
        items = u_fish.setdefault("items", {})

        if items.get(self.item_id, 0) <= 0:
            return await interaction.response.send_message("❌ Bạn không còn vật phẩm này trong kho!", ephemeral=True)

        raw_id = self.target_input.value.strip().replace("<@", "").replace(">", "").replace("!", "")
        if not raw_id.isdigit():
            return await interaction.response.send_message("❌ ID người nhận không hợp lệ!", ephemeral=True)

        target_member = guild.get_member(int(raw_id))
        if not target_member:
            return await interaction.response.send_message("❌ Không tìm thấy thành viên này trong server!", ephemeral=True)

        if target_member.id == author_id:
            return await interaction.response.send_message("❌ Bạn không thể tự dùng vật phẩm này lên chính mình!", ephemeral=True)

        target_fish = get_user_fishing(target_member.id)
        target_buffs = target_fish.setdefault("buffs", {})

        if target_buffs.get("magic_mirror", False):
            target_buffs["magic_mirror"] = False
            items[self.item_id] -= 1
            save_fishing_data()
            return await interaction.response.send_message(
                f"🪞 **GƯƠNG PHẢN CHIẾU KÍCH HOẠT!** {target_member.mention} đã bật ngược hiệu ứng của **{UTILITY_ITEMS[self.item_id]['name']}** lại bạn!",
                ephemeral=False
            )

        if target_buffs.get("shield", False):
            target_buffs["shield"] = False
            items[self.item_id] -= 1
            save_fishing_data()
            return await interaction.response.send_message(
                f"🛡️ **KHIÊN BẢO VỆ KÍCH HOẠT!** {target_member.mention} đã chặn đứng tác động từ **{UTILITY_ITEMS[self.item_id]['name']}** của bạn!",
                ephemeral=False
            )

        items[self.item_id] -= 1
        save_fishing_data()

        if self.item_id == "rename_card":
            new_nick = self.extra_input.value.strip()
            try:
                await target_member.edit(nick=new_nick)
                await interaction.response.send_message(f"📝 Đã đổi biệt danh của {target_member.mention} thành: **{new_nick}**!", ephemeral=False)
            except discord.Forbidden:
                await interaction.response.send_message(f"⚠️ Bot không đủ quyền hạn để đổi biệt danh cho {target_member.mention}. Đã tiêu hao thẻ!", ephemeral=True)

        elif self.item_id == "mute_card":
            try:
                await target_member.timeout(timedelta(seconds=30), reason=f"Bị {self.author.display_name} dùng Thẻ Mute")
                await interaction.response.send_message(f"🔇 {target_member.mention} đã bị khóa mõm trong **30 giây**!", ephemeral=False)
            except discord.Forbidden:
                await interaction.response.send_message(f"⚠️ Bot không có quyền Timeout {target_member.mention}!", ephemeral=True)

        elif self.item_id == "voice_kick":
            if not target_member.voice or not target_member.voice.channel:
                items[self.item_id] += 1
                save_fishing_data()
                return await interaction.response.send_message(f"⚠️ {target_member.mention} hiện không ở trong phòng thoại nào cả!", ephemeral=True)
            try:
                await target_member.move_to(None, reason=f"Voice Kick bởi {self.author.display_name}")
                await interaction.response.send_message(f"🔊 Đã trục xuất {target_member.mention} khỏi phòng thoại!", ephemeral=False)
            except discord.Forbidden:
                await interaction.response.send_message("⚠️ Bot không có quyền kick thành viên khỏi voice!", ephemeral=True)

        elif self.item_id == "banana_peel":
            t_data = await get_user_data(guild.id, target_member.id)
            lost_coin = min(t_data.get("coins", 0), random.randint(10000, 50000))
            if lost_coin > 0:
                await update_user_coins(guild.id, target_member.id, -lost_coin)
                await update_user_coins(guild.id, author_id, lost_coin)
            await interaction.response.send_message(
                f"🍌 Oái! {target_member.mention} đã dẫm phải vỏ chuối của {self.author.mention}, trượt ngã lăn quay và đánh rơi **`{lost_coin:,}` coin** vào túi người đặt!",
                ephemeral=False
            )

        elif self.item_id == "mystery_box":
            roll = random.random()
            if roll < 0.4:
                bonus = 500000
                await update_user_coins(guild.id, target_member.id, bonus)
                await interaction.response.send_message(f"🎁 {target_member.mention} mở Hộp Quà Bí Ẩn của {self.author.mention} và bất ngờ trúng **`+{bonus:,}` coin**!", ephemeral=False)
            else:
                await interaction.response.send_message(f"🎁 {target_member.mention} hí hửng mở Hộp Quà Bí Ẩn và bị một con quỷ lò xo nhảy xổ ra dọa giật bắn mình! 👻", ephemeral=False)

        elif self.item_id == "bomb_card":
            msg_text = self.extra_input.value
            await interaction.response.send_message(f"💣 **BOM ĐÃ GÀI!** Đang đếm ngược nhắm vào {target_member.mention}...")
            await asyncio.sleep(5)
            await interaction.channel.send(f"💥💥💥 **BÙÙÙÙÙM!** {target_member.mention} ơi:\n> *\"{msg_text}\"* — Từ {self.author.mention}")

        elif self.item_id == "ghost_ping":
            await interaction.response.send_message("👻 Đã bắn Ghost Ping thành công!", ephemeral=True)
            ghost_msg = await interaction.channel.send(f"👻 {target_member.mention}")
            await asyncio.sleep(0.4)
            try:
                await ghost_msg.delete()
            except Exception:
                pass

        elif self.item_id == "reverse_card":
            target_buffs["reverse_text"] = time.time() + 180
            await interaction.response.send_message(f"🔀 **ĐẢO NGƯỢC THỜI KHÔNG!** {self.author.mention} đã niệm chú đảo ngược lên {target_member.mention}! Bây giờ hãy nói năng cẩn thận kẻo đảo chiều!", ephemeral=False)

        elif self.item_id == "freeze_card":
            target_buffs["freeze_fishing"] = time.time() + 120
            await interaction.response.send_message(f"🧊 **BĂNG GIÁ VĨNH CỬU!** {self.author.mention} ném Bom Băng Giá vào {target_member.mention}, đóng băng cần câu khiến đối phương không thể câu cá trong **2 phút**!", ephemeral=False)

        elif self.item_id == "steal_fish_card":
            t_bag = target_fish.setdefault("fish_bag", [])
            if not t_bag:
                await interaction.response.send_message(f"🦹 {self.author.mention} thò tay vào giỏ của {target_member.mention} nhưng giỏ trống trơn không có con cá nào!", ephemeral=False)
            else:
                stolen_idx = random.randrange(len(t_bag))
                stolen_fish = t_bag.pop(stolen_idx)
                u_fish.setdefault("fish_bag", []).append(stolen_fish)
                save_fishing_data()
                await interaction.response.send_message(f"🦹 **ĐẠO TẶC THÀNH CÔNG!** {self.author.mention} đã nhanh tay móc trộm được con **{stolen_fish.get('name', 'Cá')}** ({stolen_fish.get('weight', 1)}kg) từ giỏ của {target_member.mention}!", ephemeral=False)

        elif self.item_id == "fake_nitro":
            embed = discord.Embed(
                title="🎁 BẠN ĐÃ NHẬN ĐƯỢC 1 THÁNG DISCORD NITRO!",
                description=f"Từ: {self.author.mention}\n\n[**👉 NHẤP VÀO ĐÂY ĐỂ NHẬN NITRO MIỄN PHÍ NGAY 👈**](https://www.youtube.com/watch?v=dQw4w9WgXcQ)\n\n*(Quà tặng sẽ hết hạn sau 24 giờ)*",
                color=discord.Color.from_rgb(88, 101, 242)
            )
            embed.set_thumbnail(url="https://assets-global.website-files.com/6257adef93867e50d84d30e2/636e0a6a49cf127bf92de1e2_icon_clyde_blurple_RGB.png")
            embed.set_footer(text="Discord Nitro Gift • Sakura Bot System")
            await interaction.response.send_message(content=f"🎁 {target_member.mention}, bạn có một món quà bí mật từ {self.author.mention}!", embed=embed, ephemeral=False)

        elif self.item_id == "frog_potion":
            old_nick = target_member.display_name
            frog_nick = f"🐸 {old_nick[:20]} Ộp Ộp"
            try:
                await target_member.edit(nick=frog_nick)
                await interaction.response.send_message(f"🐸 **PHÙ PHÉP THÀNH CÔNG!** {self.author.mention} ném Thuốc Biến Ếch vào {target_member.mention}, biến đối phương thành chú ếch xanh mang tên: **{frog_nick}**!", ephemeral=False)
            except Exception:
                await interaction.response.send_message(f"🐸 {target_member.mention} bị trúng Thuốc Biến Ếch của {self.author.mention} và phát ra tiếng kêu *'Ộp ộp ộp...'* khắp kênh!", ephemeral=False)

        elif self.item_id == "slap_fish":
            slap_sounds = ["BÔM BỐP", "CHÁT CHÚA", "BẸP BẸP", "BỐP CHÁT"]
            chosen_sound = random.choice(slap_sounds)
            await interaction.response.send_message(f"🐟 **{chosen_sound}!!** {self.author.mention} cầm con cá hồi 15kg quất túi bụi vào mặt {target_member.mention}! Nạn nhân choáng váng hoa mắt chóng mặt!", ephemeral=False)

        elif self.item_id == "cursed_bait":
            target_buffs["cursed_bait"] = True
            await interaction.response.send_message(f"🪱 **LỜI NGUYỀN GIĂNG RA!** {self.author.mention} đã bỏ lén Mồi Nguyền Rủa vào giỏ {target_member.mention}. Lần câu kế tiếp chắc chắn sẽ vớt phải rác rưởi!", ephemeral=False)

        elif self.item_id == "troll_box":
            await interaction.response.send_message(f"📦 {target_member.mention} ơi! {self.author.mention} gửi tặng bạn một kiện hàng báu vật đại dương đặc biệt...", ephemeral=False)
            await asyncio.sleep(2)
            await interaction.channel.send(f"👻 **OÁCH XÀ LÁCH!** Rương phát nổ ra một đầu lâu quỷ ma lè lưỡi hù {target_member.mention} giật bắn mình té ghế!")

        else:
            it_info = UTILITY_ITEMS.get(self.item_id, {})
            act_k = it_info.get("action_key", "").upper()
            act_val = it_info.get("action_value", "")
            it_n = it_info.get("name", self.item_id)

            if act_k == "MUTE":
                dur_sec = int(act_val) if str(act_val).isdigit() else 30
                try:
                    await target_member.timeout(timedelta(seconds=dur_sec), reason=f"Bị dùng vật phẩm troll {it_n}")
                    await interaction.response.send_message(f"🔇 {target_member.mention} đã bị khóa mõm trong **{dur_sec} giây** bởi **{it_n}**!", ephemeral=False)
                except Exception:
                    await interaction.response.send_message(f"⚠️ Bot không đủ quyền Timeout {target_member.mention}!", ephemeral=True)
            elif act_k == "STEAL_COIN":
                t_data = await get_user_data(guild.id, target_member.id)
                lost_coin = min(t_data.get("coins", 0), int(act_val) if str(act_val).isdigit() else random.randint(10000, 50000))
                if lost_coin > 0:
                    await update_user_coins(guild.id, target_member.id, -lost_coin)
                    await update_user_coins(guild.id, author_id, lost_coin)
                await interaction.response.send_message(f"💸 {self.author.mention} đã dùng **{it_n}** móc trộm được **`{lost_coin:,}` coin** từ túi của {target_member.mention}!", ephemeral=False)
            elif act_k == "FREEZE_FISHING":
                dur_sec = int(act_val) if str(act_val).isdigit() else 120
                target_buffs["freeze_fishing"] = time.time() + dur_sec
                await interaction.response.send_message(f"🧊 {self.author.mention} đã dùng **{it_n}** đóng băng cần câu {target_member.mention} trong **{dur_sec}s**!", ephemeral=False)
            elif act_k == "SLAP":
                await interaction.response.send_message(f"👋 **CHÁT!** {self.author.mention} dùng **{it_n}** tấn công {target_member.mention} một cú trời giáng!", ephemeral=False)
            elif act_k == "JUMPSCARE":
                await interaction.response.send_message(f"👻 **HÙÙÙÙ!** {self.author.mention} kích hoạt **{it_n}** làm {target_member.mention} giật mình hốt hoảng!", ephemeral=False)
            else:
                await interaction.response.send_message(f"✨ {self.author.mention} đã sử dụng thành công **{it_n}** lên {target_member.mention}!", ephemeral=False)


class AquariumView(discord.ui.View):
    def __init__(self, owner: discord.Member, viewer: discord.Member, guild_id: int):
        super().__init__(timeout=240)
        self.owner = owner
        self.viewer = viewer
        self.guild_id = guild_id
        
        u_fish = get_user_fishing(self.owner.id)
        if "aquarium_last_claim" not in u_fish or not isinstance(u_fish.get("aquarium_last_claim"), (int, float)):
            u_fish["aquarium_last_claim"] = time.time()
            save_fishing_data()

        self._refresh_components()

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id != self.viewer.id:
            await interaction.response.send_message("❌ Đây không phải giao diện của bạn! Hãy tự mở lệnh riêng.", ephemeral=True)
            return False
        return True

    def _refresh_components(self):
        self.clear_items()
        is_self = (self.owner.id == self.viewer.id)
        u_fish = get_user_fishing(self.owner.id)
        tank = u_fish.setdefault("aquarium", [])
        bag = u_fish.get("fish_bag", [])
        max_slots = u_fish.get("aquarium_slots", 6)
        cur_row = 0

        if is_self:
            if bag and len(tank) < max_slots:
                options = []
                for idx, f in enumerate(bag[:25]):
                    mut_str = f" [{f['mutation']}]" if f.get("mutation") else ""
                    label_str = f"{idx + 1}. {f.get('name', 'Cá')}{mut_str}"[:100]
                    pr = int(f.get("price") or 100)
                    options.append(
                        discord.SelectOption(
                            label=label_str,
                            value=str(idx),
                            description=f"Giá: {pr:,}c | Nặng: {f.get('weight', 0)}kg"[:100],
                            emoji="🐠"
                        )
                    )
                deposit_select = discord.ui.Select(placeholder="🐠 Chọn cá từ giỏ để thả vào Thủy Cung...", options=options, row=cur_row, custom_id="aqua_deposit")
                deposit_select.callback = self._deposit_fish_callback
                self.add_item(deposit_select)
                cur_row += 1

            if tank:
                fav_options = []
                fav_raw = u_fish.get("aquarium_favorite")
                fav_idx_safe = int(fav_raw) if (fav_raw is not None and str(fav_raw).isdigit()) else None
                for idx, f in enumerate(tank[:25]):
                    is_fav = (fav_idx_safe is not None and idx == fav_idx_safe)
                    fav_options.append(
                        discord.SelectOption(
                            label=f"Bể #{idx + 1}: {f.get('name', 'Cá')}"[:100],
                            value=str(idx),
                            description="Đặt làm Ngôi Sao Thủy Cung (+25% vé thu)",
                            emoji="⭐" if is_fav else "🐟",
                            default=is_fav
                        )
                    )
                fav_select = discord.ui.Select(placeholder="⭐ Đặt cá tiêu biểu (Linh vật Thủy Cung)...", options=fav_options, row=cur_row, custom_id="aqua_fav")
                fav_select.callback = self._set_favorite_callback
                self.add_item(fav_select)
                cur_row += 1

            vi = is_vietnamese(self.guild_id)
            claim_lbl = "Thu Tiền Vé" if vi else "Collect Fees"
            withdraw_lbl = "Rút Cá Về Giỏ" if vi else "Withdraw Fish"
            upgrade_lbl = f"Mua Ô ({max_slots}➜{max_slots + 2})" if vi else f"Upgrade Slots ({max_slots}➜{max_slots + 2})"

            claim_btn = discord.ui.Button(label=claim_lbl, style=discord.ButtonStyle.success, emoji="🪙", row=cur_row)
            claim_btn.callback = self._claim_income
            self.add_item(claim_btn)

            if tank:
                withdraw_btn = discord.ui.Button(label=withdraw_lbl, style=discord.ButtonStyle.secondary, emoji="🎣", row=cur_row)
                withdraw_btn.callback = self._withdraw_fish
                self.add_item(withdraw_btn)

            upgrade_tank_btn = discord.ui.Button(label=upgrade_lbl, style=discord.ButtonStyle.primary, emoji="🏗️", row=cur_row)
            upgrade_tank_btn.callback = self._upgrade_slots
            self.add_item(upgrade_tank_btn)
            cur_row += 1

            if cur_row <= 4:
                cook_nav_lbl = "Menu Nấu Nướng" if vi else "Kitchen Menu"
                inv_nav_lbl = "Về Túi Đồ" if vi else "Back to Bag"
                cook_nav_btn = discord.ui.Button(label=cook_nav_lbl, style=discord.ButtonStyle.primary, emoji="🍳", row=cur_row)
                cook_nav_btn.callback = self._goto_cook
                self.add_item(cook_nav_btn)

                inv_nav_btn = discord.ui.Button(label=inv_nav_lbl, style=discord.ButtonStyle.secondary, emoji="🎒", row=cur_row)
                inv_nav_btn.callback = self._goto_inv
                self.add_item(inv_nav_btn)

        else:
            vi = is_vietnamese(self.guild_id)
            has_liked = self.viewer.id in u_fish.setdefault("aquarium_likes", [])
            like_text = ('Đã Thả Tim' if has_liked else 'Thả Tim Thủy Cung') if vi else ('Liked' if has_liked else 'Like Aquarium')
            like_btn = discord.ui.Button(
                label=f"{like_text} ({len(u_fish['aquarium_likes'])})",
                style=discord.ButtonStyle.danger if has_liked else discord.ButtonStyle.secondary,
                emoji="❤️",
                row=0,
                disabled=has_liked
            )
            like_btn.callback = self._like_aquarium
            self.add_item(like_btn)

            is_admin = (self.viewer.id == OWNER_ID or (getattr(self.viewer, 'guild_permissions', None) and self.viewer.guild_permissions.administrator))
            if is_admin:
                admin_btn = discord.ui.Button(
                    label="Quản Trị Bể",
                    style=discord.ButtonStyle.danger,
                    emoji="⚙️",
                    row=0
                )
                admin_btn.callback = self._admin_manage_aquarium
                self.add_item(admin_btn)

    async def _admin_manage_aquarium(self, interaction: discord.Interaction):
        await interaction.response.send_modal(OwnerAquariumModal(interaction.client, interaction.guild, target_uid=self.owner.id))

    def build_embed(self) -> discord.Embed:
        u_fish = get_user_fishing(self.owner.id)
        tank = u_fish.setdefault("aquarium", [])
        slots = u_fish.get("aquarium_slots", 6)
        fav_raw = u_fish.get("aquarium_favorite")
        fav_idx = int(fav_raw) if (fav_raw is not None and str(fav_raw).isdigit()) else None
        likes = len(u_fish.setdefault("aquarium_likes", []))

        base_rate = sum(max(25, int(int(f.get("price") or 100) * 0.012)) for f in tank if isinstance(f, dict))
        fav_bonus = int(base_rate * 0.25) if (fav_idx is not None and 0 <= fav_idx < len(tank)) else 0
        like_bonus = int(base_rate * (min(0.50, likes * 0.02)))
        hourly_rate = base_rate + fav_bonus + like_bonus

        last_claim = float(u_fish.get("aquarium_last_claim") or time.time())
        hours_passed = max(0.0, min(24.0, (time.time() - last_claim) / 3600.0))
        pending_coins = int(hourly_rate * hours_passed)

        fav_name = tank[fav_idx]["name"] if (fav_idx is not None and 0 <= fav_idx < len(tank)) else "Chưa thiết lập"

        filled_blocks = min(10, max(0, int((len(tank) / max(1, slots)) * 10)))
        cap_bar = "█" * filled_blocks + "░" * (10 - filled_blocks)

        embed = discord.Embed(
            title=f"🏛️ BẢO TÀNG THỦY CUNG: {self.owner.display_name.upper()}",
            description=(
                f"• Sức chứa: `[{cap_bar}]` **`{len(tank)}/{slots}`** ô | ❤️ Thả tim: **`{likes}`**\n"
                f"• Doanh thu vé: **`+{hourly_rate:,}` coin/giờ** (+25% Linh vật, +{int(min(50, likes * 2))}% Lượt thích)\n"
                f"• Vé đang tích lũy: **`+{pending_coins:,}` coin** (`{hours_passed:.2f}` giờ qua)\n"
                f"• ⭐ **Linh vật đại diện**: **{fav_name}**"
            ),
            color=discord.Color.teal()
        )

        if tank:
            max_show = min(len(tank), 24)
            for idx in range(max_show):
                f = tank[idx]
                star = "⭐ " if idx == fav_idx else ""
                mut_str = f" [{f['mutation']}]" if f.get("mutation") else ""
                icon = RARITY_ICONS.get(f.get("rarity", "common"), "🐟")
                pr = int(f.get("price") or 100)
                rate_this = max(25, int(pr * 0.012))
                safe_add_field(
                    embed,
                    name=f"{star}Bể #{idx + 1}: {icon} {f.get('name', 'Cá')}{mut_str}",
                    value=f"• Kích cỡ: `{f.get('weight', 0)}kg` (`{f.get('size_name','TB')}`)\n• Giá trị: `{pr:,}`c ➜ `+{rate_this:,}c/h`",
                    inline=True
                )
            if len(tank) > max_show:
                safe_add_field(
                    embed,
                    name="🌊 Sinh Vật Khác Trong Bể",
                    value=f"*...và còn {len(tank) - max_show} sinh vật khác đang bơi lội trong thủy cung!*",
                    inline=False
                )
        else:
            safe_add_field(embed, name="🌊 Bể Đang Trống", value="*Chưa có sinh vật nào được thả vào bể. Hãy chọn cá từ menu bên dưới để bắt đầu sinh lời!*", inline=False)

        embed.set_footer(text="Bảo tàng mở cửa 24/7 • Người xem có thể bấm [❤️ Thả Tim] để ủng hộ!")
        return embed

    async def _like_aquarium(self, interaction: discord.Interaction):
        u_fish = get_user_fishing(self.owner.id)
        likes = u_fish.setdefault("aquarium_likes", [])
        if self.viewer.id in likes:
            return await interaction.response.send_message("❤️ Bạn đã thả tim cho Thủy Cung này rồi!", ephemeral=True)

        likes.append(self.viewer.id)
        await update_user_coins(self.guild_id, self.viewer.id, 5000)
        save_fishing_data()

        self._refresh_components()
        await interaction.response.edit_message(embed=self.build_embed(), view=self)
        await interaction.followup.send(f"❤️ Cảm ơn bạn đã thả tim cho Thủy Cung của {self.owner.mention}! Bạn được thưởng **+5,000 coin**!", ephemeral=True)

    async def _deposit_fish_callback(self, interaction: discord.Interaction):
        idx = int(interaction.data["values"][0])
        u_fish = get_user_fishing(self.owner.id)
        bag = u_fish.get("fish_bag", [])
        tank = u_fish.setdefault("aquarium", [])
        max_slots = u_fish.get("aquarium_slots", 6)

        if len(tank) >= max_slots:
            return await interaction.response.send_message("⚠️ Thủy cung đã hết ô trống!", ephemeral=True)
        if idx >= len(bag):
            return await interaction.response.send_message("❌ Con cá này không còn trong giỏ!", ephemeral=True)

        chosen = bag.pop(idx)
        tank.append(chosen)
        
        if len(tank) == 1:
            u_fish["aquarium_last_claim"] = time.time()
            if u_fish.get("aquarium_favorite") is None:
                u_fish["aquarium_favorite"] = 0

        save_fishing_data()

        self._refresh_components()
        await interaction.response.edit_message(embed=self.build_embed(), view=self)
        await interaction.followup.send(f"🐠 Đã thả thành công **{chosen.get('name', 'Cá')}** vào bể trưng bày!", ephemeral=True)

    async def _set_favorite_callback(self, interaction: discord.Interaction):
        idx = int(interaction.data["values"][0])
        u_fish = get_user_fishing(self.owner.id)
        u_fish["aquarium_favorite"] = idx
        save_fishing_data()

        self._refresh_components()
        await interaction.response.edit_message(embed=self.build_embed(), view=self)
        fav_fish = u_fish["aquarium"][idx] if (0 <= idx < len(u_fish.get("aquarium", []))) else {"name": "Linh vật"}
        await interaction.followup.send(f"⭐ Đã đặt **{fav_fish.get('name', 'Cá')}** làm Linh Vật Tiêu Biểu (+25% tiền vé)!", ephemeral=True)

    async def _claim_income(self, interaction: discord.Interaction):
        u_fish = get_user_fishing(self.owner.id)
        tank = u_fish.setdefault("aquarium", [])
        if not tank:
            return await interaction.response.send_message("❌ Thủy cung chưa có cá để tạo doanh thu!", ephemeral=True)

        last_claim = float(u_fish.get("aquarium_last_claim") or time.time())
        hours_passed = max(0.0, min(24.0, (time.time() - last_claim) / 3600.0))

        fav_raw = u_fish.get("aquarium_favorite")
        fav_idx = int(fav_raw) if (fav_raw is not None and str(fav_raw).isdigit()) else None
        likes = len(u_fish.setdefault("aquarium_likes", []))
        base_rate = sum(max(25, int(int(f.get("price") or 100) * 0.012)) for f in tank if isinstance(f, dict))
        fav_bonus = int(base_rate * 0.25) if (fav_idx is not None and 0 <= fav_idx < len(tank)) else 0
        like_bonus = int(base_rate * (min(0.50, likes * 0.02)))
        total_income = int((base_rate + fav_bonus + like_bonus) * hours_passed)

        if total_income < 10:
            return await interaction.response.send_message(f"⏳ Lượng coin tích lũy hiện tại (`+{total_income:,}` coin) còn quá nhỏ, hãy chờ thêm một lát!", ephemeral=True)

        u_fish["aquarium_last_claim"] = time.time()
        await update_user_coins(self.guild_id, self.owner.id, total_income)
        save_fishing_data()

        self._refresh_components()
        await interaction.response.edit_message(embed=self.build_embed(), view=self)
        await interaction.followup.send(f"🪙 **THU TIỀN VÉ THÀNH CÔNG!** Bạn đã nhận được **`+{total_income:,}` coin**!", ephemeral=True)

    async def _withdraw_fish(self, interaction: discord.Interaction):
        u_fish = get_user_fishing(self.owner.id)
        tank = u_fish.setdefault("aquarium", [])
        bag = u_fish.setdefault("fish_bag", [])
        max_bag = u_fish.get("max_bag", 30)

        if not tank:
            return await interaction.response.send_message("❌ Thủy cung không có cá!", ephemeral=True)
        if len(bag) >= max_bag:
            return await interaction.response.send_message("🎒 Giỏ cá đầy, không thể thu hồi cá về giỏ!", ephemeral=True)

        fish_ret = tank.pop(-1)
        bag.append(fish_ret)
        fav_raw = u_fish.get("aquarium_favorite")
        if fav_raw is not None and str(fav_raw).isdigit():
            fav_idx = int(fav_raw)
            if fav_idx >= len(tank):
                u_fish["aquarium_favorite"] = (len(tank) - 1) if len(tank) > 0 else None
        if not tank:
            u_fish["aquarium_favorite"] = None
        save_fishing_data()

        self._refresh_components()
        await interaction.response.edit_message(embed=self.build_embed(), view=self)
        await interaction.followup.send(f"🎣 Đã rút **{fish_ret.get('name', 'Cá')}** từ bể về lại giỏ đồ!", ephemeral=True)

    async def _upgrade_slots(self, interaction: discord.Interaction):
        u_fish = get_user_fishing(self.owner.id)
        curr_slots = u_fish.get("aquarium_slots", 6)
        if curr_slots >= 24:
            return await interaction.response.send_message("👑 Bảo tàng của bạn đã đạt số ô tối đa (**24 ô**)!", ephemeral=True)

        cost = (curr_slots // 2) * 85000
        u_data = await get_user_data(self.guild_id, self.owner.id)
        if u_data.get("coins", 0) < cost:
            return await interaction.response.send_message(f"❌ Không đủ coin! Cần **`{cost:,}` coin**.", ephemeral=True)

        await update_user_coins(self.guild_id, self.owner.id, -cost)
        u_fish["aquarium_slots"] = curr_slots + 2
        save_fishing_data()

        self._refresh_components()
        await interaction.response.edit_message(embed=self.build_embed(), view=self)
        await interaction.followup.send(f"🎉 Đã mở rộng sức chứa Thủy Cung lên **{u_fish['aquarium_slots']} ô**!", ephemeral=True)

    async def _goto_cook(self, interaction: discord.Interaction):
        cook_view = CookingView(self.owner, self.guild_id)
        await interaction.response.edit_message(embed=cook_view.build_embed(), view=cook_view)

    async def _goto_inv(self, interaction: discord.Interaction):
        inv_view = FishingInventoryView(self.owner, self.guild_id)
        u_data = await get_user_data(self.guild_id, self.owner.id)
        await interaction.response.edit_message(embed=inv_view.build_embed(u_data.get("coins", 0)), view=inv_view)


class FishingInventoryView(discord.ui.View):
    def __init__(self, author: discord.Member, guild_id: int, inv_page: int = 0, enhance_target: str = "rod"):
        super().__init__(timeout=240)
        self.author = author
        self.guild_id = guild_id
        self.inv_page = inv_page
        self.enhance_target = enhance_target
        self._build_components()

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id != self.author.id:
            await interaction.response.send_message("❌ Đây không phải túi đồ của bạn!", ephemeral=True)
            return False
        return True

    def _add_tab_selector(self):
        vi = is_vietnamese(self.guild_id)
        if vi:
            tab_options = [
                discord.SelectOption(label="Trang 1: Đồ Câu & Giỏ Cá", value="0", emoji="🎣", description="Cần câu, mồi, giỏ cá, đổi vùng", default=(self.inv_page == 0)),
                discord.SelectOption(label="Trang 2: Pet, Rương & Đồ Chơi", value="1", emoji="🐾", description="Thú cưng, mở rương, dùng đồ troll", default=(self.inv_page == 1)),
                discord.SelectOption(label="Trang 3: Kho Farmer & Nông Trại", value="2", emoji="🌾", description="Hạt giống, hoa màu, sâu bọ, ăn đồ", default=(self.inv_page == 2)),
                discord.SelectOption(label="Trang 4: Lò Rèn (+150) & Thăng Sao ⭐", value="3", emoji="🔨", description="Cường hóa đến +150, thăng cấp sao 1-20 (Cần & Cuốc)", default=(self.inv_page == 3)),
                discord.SelectOption(label="Trang 5: Bàn Phép Enchant Dòng", value="4", emoji="✨", description="Gán dòng bằng Đá End & 10M, mở ô", default=(self.inv_page == 4)),
                discord.SelectOption(label="Trang 6: Kho Quặng & Cuốc Đào", value="5", emoji="⛏️", description="Cuốc đào mỏ, quặng quý, bán quặng, bảo tàng", default=(self.inv_page == 5)),
            ]
            ph = "📑 Chuyển phân trang túi đồ (Trang 1 ➜ 6)..."
        else:
            tab_options = [
                discord.SelectOption(label="Page 1: Tackle & Fish Bag", value="0", emoji="🎣", description="Rods, baits, fish bag, change zone", default=(self.inv_page == 0)),
                discord.SelectOption(label="Page 2: Pets, Chests & Props", value="1", emoji="🐾", description="Pets, open chests, use items", default=(self.inv_page == 1)),
                discord.SelectOption(label="Page 3: Farm & Produce Bag", value="2", emoji="🌾", description="Seeds, crops, pests, eat produce", default=(self.inv_page == 2)),
                discord.SelectOption(label="Page 4: Forge (+150) & Stars ⭐", value="3", emoji="🔨", description="Refine to +150, ascend 1-20 stars", default=(self.inv_page == 3)),
                discord.SelectOption(label="Page 5: Enchanting Altar", value="4", emoji="✨", description="Affixes with End Stones, slot unlock", default=(self.inv_page == 4)),
                discord.SelectOption(label="Page 6: Ores & Pickaxes", value="5", emoji="⛏️", description="Pickaxes, ores, sell ore, museum", default=(self.inv_page == 5)),
            ]
            ph = "📑 Switch inventory tab (Page 1 ➜ 6)..."
        sel = discord.ui.Select(placeholder=ph, options=tab_options, row=4, custom_id="inv_tab_switch")
        sel.callback = self._on_switch_tab
        self.add_item(sel)

    def _build_components(self):
        self.clear_items()
        u_fish = get_user_fishing(self.author.id)

        if self.inv_page == 0:
            user_rods = u_fish.get("rods", {})
            if user_rods:
                rod_options = []
                for rid, rdata in list(user_rods.items())[:25]:
                    refine_str = f" (+{rdata.get('refine', 0)})" if rdata.get("refine", 0) > 0 else ""
                    star_str = f" [⭐x{rdata.get('stars', 0)}]" if rdata.get("stars", 0) > 0 else ""
                    is_cur = (rid == u_fish.get("equipped_rod"))
                    rod_options.append(
                        discord.SelectOption(
                            label=f"{rdata['name']}{refine_str}{star_str}"[:100],
                            value=rid,
                            description=f"Bền: {rdata.get('durability', 0)}/{rdata.get('max_durability', 50)} | May mắn: +{rdata.get('luck', 1)}",
                            emoji="🎣",
                            default=is_cur
                        )
                    )
                rod_select = discord.ui.Select(placeholder="🎣 Chọn cần câu đang cầm...", options=rod_options, row=0, custom_id="inv_select_rod")
                rod_select.callback = self._select_rod_callback
                self.add_item(rod_select)

            user_baits = u_fish.get("baits", {})
            bait_options = [
                discord.SelectOption(label="Không dùng mồi", value="none", emoji="❌", default=(u_fish.get("equipped_bait") is None))
            ]
            for bid, count in user_baits.items():
                if count > 0 and bid in BAITS_CATALOG:
                    b_info = BAITS_CATALOG[bid]
                    bait_options.append(
                        discord.SelectOption(
                            label=f"{b_info['name']} (x{count})"[:100],
                            value=bid,
                            description=f"Tăng +{b_info['luck']} May Mắn",
                            emoji="🪱",
                            default=(bid == u_fish.get("equipped_bait"))
                        )
                    )
            if len(bait_options) > 1:
                bait_select = discord.ui.Select(placeholder="🪱 Chọn mồi câu trang bị...", options=bait_options[:25], row=1, custom_id="inv_select_bait")
                bait_select.callback = self._select_bait_callback
                self.add_item(bait_select)

            bag_detail_btn = discord.ui.Button(label="Chi Tiết Giỏ Cá", style=discord.ButtonStyle.primary, emoji="🐟", row=2)
            bag_detail_btn.callback = self._goto_bag_detail
            self.add_item(bag_detail_btn)

            recycle_btn = discord.ui.Button(label="Tái Chế Rác", style=discord.ButtonStyle.success, emoji="♻️", row=2)
            recycle_btn.callback = self._recycle_trash
            self.add_item(recycle_btn)

            expand_bag_btn = discord.ui.Button(label="Mở Rộng Túi", style=discord.ButtonStyle.secondary, emoji="🎒", row=2)
            expand_bag_btn.callback = self._expand_bag
            self.add_item(expand_bag_btn)

            cook_btn = discord.ui.Button(label="Bếp Nấu Ăn", style=discord.ButtonStyle.primary, emoji="🍳", row=3)
            cook_btn.callback = self._goto_cook
            self.add_item(cook_btn)

            aqua_btn = discord.ui.Button(label="Thủy Cung", style=discord.ButtonStyle.secondary, emoji="🏛️", row=3)
            aqua_btn.callback = self._goto_aqua
            self.add_item(aqua_btn)

            dex_btn = discord.ui.Button(label="Sổ Sưu Tầm", style=discord.ButtonStyle.secondary, emoji="📖", row=3)
            dex_btn.callback = self._goto_dex
            self.add_item(dex_btn)

            zone_btn = discord.ui.Button(label="Đổi Vùng", style=discord.ButtonStyle.secondary, emoji="📍", row=3)
            zone_btn.callback = self._open_zone_view
            self.add_item(zone_btn)

            self._add_tab_selector()

        elif self.inv_page == 1:
            user_pets = u_fish.get("pets", [])
            pet_options = [
                discord.SelectOption(label="Không dùng Pet", value="none", emoji="❌", default=(u_fish.get("equipped_pet") is None))
            ]
            for pid in user_pets:
                if pid in PETS_CATALOG:
                    p_info = PETS_CATALOG[pid]
                    pet_options.append(
                        discord.SelectOption(
                            label=f"{p_info['name']}"[:100],
                            value=pid,
                            description=f"Luck: +{p_info['luck_bonus']} | Giá bán: x{p_info['price_multi']}",
                            emoji="🐾",
                            default=(pid == u_fish.get("equipped_pet"))
                        )
                    )
            if len(pet_options) > 1:
                pet_select = discord.ui.Select(placeholder="🐾 Chọn Thú Cưng đồng hành...", options=pet_options[:25], row=0, custom_id="inv_select_pet")
                pet_select.callback = self._select_pet_callback
                self.add_item(pet_select)

            chests = u_fish.get("chests", {})
            chest_options = []
            for cid, cnt in chests.items():
                if cnt > 0 and cid in CHESTS_DATA:
                    c_info = CHESTS_DATA[cid]
                    key_tag = f" [Cần {UTILITY_ITEMS[c_info['req_key']]['name']}]" if c_info.get("req_key") else ""
                    chest_options.append(
                        discord.SelectOption(
                            label=f"{c_info['name']} (x{cnt}){key_tag}"[:100],
                            value=cid,
                            description=f"Mở rương nhận coin, mồi, báu vật hiếm",
                            emoji="📦"
                        )
                    )
            if chest_options:
                chest_select = discord.ui.Select(placeholder="📦 Chọn Rương Báu để mở...", options=chest_options[:25], row=1, custom_id="inv_select_chest")
                chest_select.callback = self._select_chest_callback
                self.add_item(chest_select)

            user_items = u_fish.get("items", {})
            usable_items = [iid for iid, count in user_items.items() if count > 0 and iid in UTILITY_ITEMS]
            if usable_items:
                item_options = []
                for iid in usable_items[:25]:
                    it = UTILITY_ITEMS[iid]
                    item_options.append(
                        discord.SelectOption(
                            label=f"{it['name']} (x{user_items[iid]})"[:100],
                            value=iid,
                            description=it.get("desc", "Sử dụng vật phẩm")[:100],
                            emoji="✨"
                        )
                    )
                item_select = discord.ui.Select(placeholder="🛠️ Dùng vật phẩm chức năng / troll...", options=item_options, row=2, custom_id="inv_select_item")
                item_select.callback = self._select_item_callback
                self.add_item(item_select)

            sell_tiered_btn = discord.ui.Button(label="Bán Cá Theo Cấp", style=discord.ButtonStyle.secondary, emoji="💰", row=3)
            sell_tiered_btn.callback = self._open_sell_tiered_modal
            self.add_item(sell_tiered_btn)

            code_btn = discord.ui.Button(label="Nhập Code", style=discord.ButtonStyle.success, emoji="🎁", row=3)
            code_btn.callback = self._open_redeem_code
            self.add_item(code_btn)

            transfer_btn = discord.ui.Button(label="Chuyển Coin", style=discord.ButtonStyle.secondary, emoji="💸", row=3)
            transfer_btn.callback = self._open_transfer_modal
            self.add_item(transfer_btn)

            self._add_tab_selector()

        elif self.inv_page == 2:
            farm_data = u_fish.setdefault("farm", {})
            crops = farm_data.setdefault("crops", {})

            go_farm_btn = discord.ui.Button(label="Mở Nông Trại Trồng Cây", style=discord.ButtonStyle.success, emoji="🌾", row=0)
            go_farm_btn.callback = self._goto_farm_view
            self.add_item(go_farm_btn)

            cook_farm_btn = discord.ui.Button(label="Bếp Nấu Ăn (Cá + Rau)", style=discord.ButtonStyle.primary, emoji="🍳", row=0)
            cook_farm_btn.callback = self._goto_cook
            self.add_item(cook_farm_btn)

            shop_farm_btn = discord.ui.Button(label="Mua Hạt Giống", style=discord.ButtonStyle.secondary, emoji="🌱", row=0)
            shop_farm_btn.callback = self._goto_farm_shop
            self.add_item(shop_farm_btn)

            sell_crops_btn = discord.ui.Button(label="Bán Toàn Bộ Hoa Màu", style=discord.ButtonStyle.success, emoji="💰", row=1)
            sell_crops_btn.callback = self._sell_all_crops
            self.add_item(sell_crops_btn)

            sell_pests_btn = discord.ui.Button(label="Bán Toàn Bộ Sâu Bọ", style=discord.ButtonStyle.secondary, emoji="🐛", row=1)
            sell_pests_btn.callback = self._sell_all_pests
            self.add_item(sell_pests_btn)

            available_crops = [cid for cid, cnt in crops.items() if cnt > 0]
            if available_crops:
                eat_options = []
                for cid in available_crops[:25]:
                    c_info = get_crop_info(cid)
                    c_name = c_info.get("name", cid)
                    eat_options.append(
                        discord.SelectOption(
                            label=f"Ăn {c_name} (x{crops[cid]})"[:100],
                            value=cid,
                            description=f"Hồi độ bền cần & buff may mắn nông sản"[:100],
                            emoji="🍎"
                        )
                    )
                eat_select = discord.ui.Select(placeholder="🍎 Chọn hoa màu để ăn (Hồi độ bền cần & Buff)...", options=eat_options, row=2, custom_id="inv_eat_crop")
                eat_select.callback = self._eat_crop_callback
                self.add_item(eat_select)

            self._add_tab_selector()

        elif self.inv_page == 3:
            is_pick = (self.enhance_target == "pick")
            if is_pick:
                from Command.command_mining import get_user_mining
                u_mine = get_user_mining(self.author.id)
                pick_id = u_mine.get("equipped_pick")
                cur_item = u_mine.get("picks", {}).get(pick_id) if pick_id else None
                item_title = "Cuốc Đào"
                switch_label = "Đổi Mục Tiêu: 🎣 Cần Câu"
            else:
                rod_id = u_fish.get("equipped_rod")
                cur_item = u_fish.get("rods", {}).get(rod_id) if rod_id else None
                item_title = "Cần Câu"
                switch_label = "Đổi Mục Tiêu: ⛏️ Cuốc Đào"

            ref = cur_item.get("refine", 0) if cur_item else 0
            stars = cur_item.get("stars", 0) if cur_item else 0

            upgrade_label = f"Cường Hóa {item_title} (+{ref} ➜ +{ref + 1})" if ref < 150 else f"{item_title} Đã Max (+150)!"
            upgrade_btn = discord.ui.Button(label=upgrade_label, style=discord.ButtonStyle.primary, emoji="🔨", row=0, disabled=(ref >= 150 or cur_item is None))
            upgrade_btn.callback = self._upgrade_rod
            self.add_item(upgrade_btn)

            star_label = f"Tiến Cấp Sao {item_title} (⭐ {stars} ➜ ⭐ {stars + 1})" if stars < 20 else f"{item_title} Đã Max 20 Sao ⭐!"
            star_btn = discord.ui.Button(
                label=star_label,
                style=discord.ButtonStyle.success if (ref >= 150 and stars < 20) else discord.ButtonStyle.secondary,
                emoji="⭐",
                row=1,
                disabled=(ref < 150 or stars >= 20 or cur_item is None)
            )
            star_btn.callback = self._ascend_star
            self.add_item(star_btn)

            repair_btn = discord.ui.Button(label=f"Sửa Độ Bền {item_title}", style=discord.ButtonStyle.secondary, emoji="🔧", row=2, disabled=(cur_item is None))
            repair_btn.callback = self._repair_rod
            self.add_item(repair_btn)

            shop_mat_btn = discord.ui.Button(label="Mua Bụi Sao & Nguyên Liệu", style=discord.ButtonStyle.secondary, emoji="💎", row=2)
            shop_mat_btn.callback = self._goto_material_shop
            self.add_item(shop_mat_btn)

            switch_btn = discord.ui.Button(label=switch_label, style=discord.ButtonStyle.primary, emoji="🔄", row=3)
            switch_btn.callback = self._switch_enhance_target
            self.add_item(switch_btn)

            self._add_tab_selector()

        elif self.inv_page == 4:
            is_pick = (self.enhance_target == "pick")
            if is_pick:
                from Command.command_mining import get_user_mining
                u_mine = get_user_mining(self.author.id)
                pick_id = u_mine.get("equipped_pick")
                cur_item = u_mine.get("picks", {}).get(pick_id) if pick_id else None
                item_title = "Cuốc Đào"
                switch_label = "Đổi Mục Tiêu: 🎣 Cần Câu"
            else:
                rod_id = u_fish.get("equipped_rod")
                cur_item = u_fish.get("rods", {}).get(rod_id) if rod_id else None
                item_title = "Cần Câu"
                switch_label = "Đổi Mục Tiêu: ⛏️ Cuốc Đào"

            enchant_btn = discord.ui.Button(label=f"Gán Dòng {item_title} (1 Đá End + 10M)", style=discord.ButtonStyle.primary, emoji="✨", row=0, disabled=(cur_item is None))
            enchant_btn.callback = self._enchant_rod
            self.add_item(enchant_btn)

            extra_btn = discord.ui.Button(label=f"Mở Ô Dòng {item_title} (1 Đá ĐB + 100M)", style=discord.ButtonStyle.success, emoji="🔓", row=1, disabled=(cur_item is None))
            extra_btn.callback = self._unlock_extra_enchant_slot
            self.add_item(extra_btn)

            clear_btn = discord.ui.Button(label=f"Tẩy Dòng {item_title}", style=discord.ButtonStyle.danger, emoji="♻️", row=2, disabled=(cur_item is None))
            clear_btn.callback = self._clear_enchant_affixes
            self.add_item(clear_btn)

            switch_btn = discord.ui.Button(label=switch_label, style=discord.ButtonStyle.primary, emoji="🔄", row=3)
            switch_btn.callback = self._switch_enhance_target
            self.add_item(switch_btn)

            self._add_tab_selector()

        else:
            from Command.command_mining import get_user_mining
            u_mine = get_user_mining(self.author.id)
            user_picks = u_mine.get("picks", {})

            if user_picks:
                pick_options = []
                for pid, pdata in list(user_picks.items())[:25]:
                    refine_str = f" (+{pdata.get('refine', 0)})" if pdata.get("refine", 0) > 0 else ""
                    star_str = f" [⭐x{pdata.get('stars', 0)}]" if pdata.get("stars", 0) > 0 else ""
                    is_cur = (pid == u_mine.get("equipped_pick"))
                    pick_options.append(
                        discord.SelectOption(
                            label=f"{pdata.get('name', pid)}{refine_str}{star_str}"[:100],
                            value=pid,
                            description=f"Bền: {pdata.get('durability', 0)}/{pdata.get('max_durability', 60)} | May mắn: +{pdata.get('luck', 5)}",
                            emoji="⛏️",
                            default=is_cur
                        )
                    )
                pick_select = discord.ui.Select(placeholder="⛏️ Chọn cuốc đào đang cầm...", options=pick_options, row=0, custom_id="inv_select_pick")
                pick_select.callback = self._select_pick_callback
                self.add_item(pick_select)

            sell_ores_btn = discord.ui.Button(label="Bán Toàn Bộ Quặng", style=discord.ButtonStyle.success, emoji="💰", row=1)
            sell_ores_btn.callback = self._sell_all_ores
            self.add_item(sell_ores_btn)

            museum_btn = discord.ui.Button(label="Bảo Tàng Địa Chất", style=discord.ButtonStyle.secondary, emoji="🏛️", row=1)
            museum_btn.callback = self._goto_mining_museum
            self.add_item(museum_btn)

            zone_mine_btn = discord.ui.Button(label="Đổi Mỏ Khoáng", style=discord.ButtonStyle.secondary, emoji="📍", row=2)
            zone_mine_btn.callback = self._open_mining_zone_view
            self.add_item(zone_mine_btn)

            shop_mine_btn = discord.ui.Button(label="Cửa Hàng Cuốc & Mỏ", style=discord.ButtonStyle.secondary, emoji="🛒", row=2)
            shop_mine_btn.callback = self._goto_mining_shop
            self.add_item(shop_mine_btn)

            forge_pick_btn = discord.ui.Button(label="Vào Lò Rèn Cuốc (+150 & ⭐)", style=discord.ButtonStyle.primary, emoji="🔨", row=3)
            forge_pick_btn.callback = self._goto_pick_forge
            self.add_item(forge_pick_btn)

            self._add_tab_selector()

    def build_embed(self, user_coins: int = 0, user_xu: int = 0) -> discord.Embed:
        u_fish = get_user_fishing(self.author.id)
        cur_zone = FISHING_ZONES.get(u_fish.get("zone", "ven_bo"), FISHING_ZONES["ven_bo"])
        equipped_rod_id = u_fish.get("equipped_rod")
        user_rods = u_fish.get("rods", {})
        cur_rod = user_rods.get(equipped_rod_id) if equipped_rod_id else None

        embed = discord.Embed(
            title=f"🎒 TÚI ĐỒ & KHO DỰ TRỮ: {self.author.display_name.upper()} [Trang {self.inv_page + 1}/6]",
            color=discord.Color.teal()
        )

        if self.inv_page == 0:
            if cur_rod:
                ref_str = f" (+{cur_rod.get('refine', 0)})" if cur_rod.get("refine", 0) > 0 else ""
                star_str = f" [⭐x{cur_rod.get('stars', 0)}]" if cur_rod.get("stars", 0) > 0 else ""
                dur = cur_rod.get("durability", 0)
                max_dur = cur_rod.get("max_durability", 50)
                dur_pct = max(0, min(100, int((dur / max_dur) * 100))) if max_dur > 0 else 0
                bar_len = 8
                filled = int(bar_len * (dur_pct / 100))
                dur_bar = "█" * filled + "░" * (bar_len - filled)
                rod_desc = f"**{cur_rod['name']}{ref_str}{star_str}**\n• Độ bền: `[{dur_bar}] {dur}/{max_dur}` ({dur_pct}%)\n• May mắn: `+{cur_rod.get('luck', 1)}`"
            else:
                rod_desc = "*(Chưa trang bị cần câu nào)*"

            safe_add_field(embed, name="🎣 Cần Câu Đang Cầm", value=rod_desc, inline=True)

            max_bag = u_fish.get("max_bag", 30)
            bag = u_fish.get("fish_bag", [])
            trash = u_fish.get("trash_bag", {})
            safe_add_field(
                embed,
                name="👛 Tài Chính & Giỏ",
                value=f"• Tiền tệ: **`{user_coins:,}` coin** | **`{user_xu:,}` xu** 💠\n• Vùng câu: **{cur_zone['name']}**\n• Sức chứa: **`{len(bag)}/{max_bag}`** cá\n• Rác biển: **`{sum(trash.values())}`** món",
                inline=True
            )

            user_baits = u_fish.get("baits", {})
            eq_bait = u_fish.get("equipped_bait")
            baits_list = [f"• {BAITS_CATALOG[bid]['name']}: `x{cnt}`{' *(Đang dùng)*' if bid == eq_bait else ''}" for bid, cnt in user_baits.items() if cnt > 0 and bid in BAITS_CATALOG]
            if len(baits_list) > 8:
                baits_text = "\n".join(baits_list[:8]) + f"\n*...và còn {len(baits_list) - 8} loại mồi khác*"
            else:
                baits_text = "\n".join(baits_list) if baits_list else "*Hết mồi câu*"
            safe_add_field(embed, name="🪱 Hộp Mồi Câu", value=baits_text, inline=True)

            if bag:
                recent_fish = []
                for f in reversed(bag[-5:]):
                    mut = f" [{f['mutation']}]" if f.get("mutation") else ""
                    icon = RARITY_ICONS.get(f.get("rarity", "common"), "🐟")
                    recent_fish.append(f"{icon} **{f['name']}**{mut} (`{f.get('weight', 0)}kg` - `{f.get('price', 0):,}`c)")
                safe_add_field(embed, name=f"🐟 Cá Trong Giỏ ({len(bag)} con - mới nhất)", value="\n".join(recent_fish), inline=False)
            else:
                safe_add_field(embed, name="🐟 Cá Trong Giỏ", value="*Giỏ trống. Dùng `/fishing cast` để câu cá!*", inline=False)

            embed.set_footer(text="Dùng Menu chọn ở phía dưới để chuyển sang Trang 2, 3, 4, 5, 6!")

        elif self.inv_page == 1:
            eq_pet = u_fish.get("equipped_pet")
            p_name = PETS_CATALOG[eq_pet]['name'] if eq_pet in PETS_CATALOG else "*Chưa trang bị*"
            safe_add_field(embed, name="🐾 Thú Cưng Đang Dùng", value=p_name, inline=True)

            chests = u_fish.get("chests", {})
            chest_lines = [f"• {CHESTS_DATA[cid]['name']}: `x{cnt}`" for cid, cnt in chests.items() if cnt > 0 and cid in CHESTS_DATA]
            if len(chest_lines) > 8:
                chest_text = "\n".join(chest_lines[:8]) + f"\n*...và {len(chest_lines) - 8} loại rương khác*"
            else:
                chest_text = "\n".join(chest_lines) if chest_lines else "*Không có rương*"
            safe_add_field(embed, name="📦 Rương Báu Đang Có", value=chest_text, inline=True)

            items = u_fish.get("items", {})
            item_lines = [f"• {UTILITY_ITEMS[iid]['name']}: `x{cnt}`" for iid, cnt in items.items() if cnt > 0 and iid in UTILITY_ITEMS]
            if len(item_lines) > 10:
                item_text = "\n".join(item_lines[:10]) + f"\n*...và {len(item_lines) - 10} vật phẩm khác*"
            else:
                item_text = "\n".join(item_lines) if item_lines else "*Không có*"
            safe_add_field(embed, name="✨ Vật Phẩm Chức Năng", value=item_text, inline=True)
            embed.set_footer(text="Trang 2: Quản lý Pet, Mở Rương Báu và Vật phẩm Troll")

        elif self.inv_page == 2:
            farm_data = u_fish.setdefault("farm", {})
            seeds = farm_data.get("seeds", {})
            crops = farm_data.get("crops", {})
            pests = farm_data.get("pests", {})
            tools = farm_data.get("tools", {})

            seed_lines = [f"• {SEEDS_CATALOG[sid]['name']}: `x{cnt}`" for sid, cnt in seeds.items() if cnt > 0 and sid in SEEDS_CATALOG]
            if len(seed_lines) > 6:
                seed_text = "\n".join(seed_lines[:6]) + f"\n*...và {len(seed_lines)-6} loại hạt khác*"
            else:
                seed_text = "\n".join(seed_lines) if seed_lines else "*Hết hạt giống*"
            
            crop_lines = []
            total_crop_val = 0
            for cid, cnt in crops.items():
                if cnt > 0:
                    c_info = get_crop_info(cid)
                    val = c_info.get("sell_price", 500) * cnt
                    total_crop_val += val
                    crop_lines.append(f"• {c_info.get('name', cid)}: `x{cnt}` (`+{val:,}`c)")
            if len(crop_lines) > 6:
                crop_text = "\n".join(crop_lines[:6]) + f"\n*...và {len(crop_lines)-6} nông sản khác*"
            else:
                crop_text = "\n".join(crop_lines) if crop_lines else "*Chưa có nông sản*"

            pest_lines = [f"• {PESTS_CATALOG[pid]['name']}: `x{cnt}` (`+{PESTS_CATALOG[pid]['sell_price']*cnt:,}`c)" for pid, cnt in pests.items() if cnt > 0 and pid in PESTS_CATALOG]
            total_pest_val = sum(PESTS_CATALOG[pid]['sell_price'] * cnt for pid, cnt in pests.items() if cnt > 0 and pid in PESTS_CATALOG)
            if len(pest_lines) > 6:
                pest_text = "\n".join(pest_lines[:6]) + f"\n*...và {len(pest_lines)-6} loại sâu khác*"
            else:
                pest_text = "\n".join(pest_lines) if pest_lines else "*Không có sâu bọ*"

            tool_lines = [f"• {FARM_TOOLS_CATALOG[tid]['name']}: `x{cnt}`" for tid, cnt in tools.items() if cnt > 0 and tid in FARM_TOOLS_CATALOG]
            if len(tool_lines) > 6:
                tool_text = "\n".join(tool_lines[:6]) + f"\n*...và {len(tool_lines)-6} dụng cụ khác*"
            else:
                tool_text = "\n".join(tool_lines) if tool_lines else "*Chưa có dụng cụ*"

            mutated = farm_data.get("mutated_crops", [])
            mut_val = sum(m.get("sell_price", 1000) for m in mutated)
            mut_lines = [f"• {m.get('prefix', '🧬')} {m.get('crop_name')}: `+{m.get('sell_price', 1000):,}`c" for m in mutated[:5]]
            if len(mutated) > 5:
                mut_lines.append(f"*... và {len(mutated)-5} nông sản đột biến khác*")

            safe_add_field(embed, name=f"🥬 Hoa Màu Thu Hoạch (Trị giá: `{total_crop_val:,}`c)", value=crop_text, inline=True)
            safe_add_field(embed, name=f"🐛 Sâu Bọ Bắt Được (Trị giá: `{total_pest_val:,}`c)", value=pest_text, inline=True)
            if mutated:
                safe_add_field(embed, name=f"🧬 Nông Sản Đột Biến (x{len(mutated)} • `{mut_val:,}`c)", value="\n".join(mut_lines), inline=False)
            safe_add_field(embed, name="🌱 Túi Hạt Giống", value=seed_text, inline=True)
            safe_add_field(embed, name="🌾 Phân Bón & Dụng Cụ", value=tool_text, inline=False)
            embed.set_footer(text="Trang 3: Kho Nông Dân • Bấm [Mở Nông Trại Trồng Cây] để vào vườn!")

        elif self.inv_page == 3:
            is_pick = (self.enhance_target == "pick")
            if is_pick:
                from Command.command_mining import get_user_mining
                u_mine = get_user_mining(self.author.id)
                pick_id = u_mine.get("equipped_pick")
                cur_target = u_mine.get("picks", {}).get(pick_id) if pick_id else None
                item_header = "⛏️ Cuốc Đào Khoáng"
            else:
                cur_target = cur_rod
                item_header = "🎣 Cần Câu Cá"

            if cur_target:
                ref = cur_target.get("refine", 0)
                stars = cur_target.get("stars", 0)
                base_cost = cur_target.get("price", 5000)
                cost = int(base_cost * 0.20 * ((ref + 1) ** 1.28))
                star_icon = "⭐" * min(stars, 10) + (f" (+{stars - 10})" if stars > 10 else "")
                if not star_icon:
                    star_icon = "*(Chưa có Sao nào)*"

                safe_add_field(
                    embed,
                    name=f"{item_header} Đang Cường Hóa",
                    value=f"• Tên: **{cur_target['name']}**\n• Cấp Cường Hóa: **`+{ref}/150`**\n• Cấp Sao: **{star_icon}** (`{stars}/20` ⭐)\n• May mắn hiện tại: `+{cur_target.get('luck', 1)}`\n• Độ bền: `{cur_target.get('durability', 0)}/{cur_target.get('max_durability', 100)}`",
                    inline=False
                )

                items = u_fish.setdefault("items", {})
                dust_cnt = items.get("stardust_dust", 0)
                pearl_cnt = items.get("black_pearl", 0)
                fish_cnt = len(u_fish.get("fish_bag", []))

                star_req = (
                    f"• ✨ **Bụi sao lấp lánh**: `{dust_cnt}/10`\n"
                    f"• 🐟 **Cá phẩm chất bất kỳ**: `{fish_cnt}/2` con\n"
                    f"• 🦪 **Ngọc trai đen**: `{pearl_cnt}/1`\n"
                    f"*(Thất bại thăng sao sẽ HOÀN LẠI 50% ngẫu nhiên số nguyên liệu!)*"
                )
                safe_add_field(
                    embed,
                    name="⭐ Điều Kiện Tiến Cấp Sao (Cần đạt +150)",
                    value=star_req,
                    inline=False
                )

                if ref < 150:
                    safe_add_field(
                        embed,
                        name="🔨 Chi Phí Đập Lên Cấp Kế",
                        value=f"• Cần lên: **`+{ref + 1}`**\n• Chi phí: **`{cost:,}` coin**\n• Thành công: Hồi 100% độ bền & tăng may mắn!",
                        inline=True
                    )
                else:
                    safe_add_field(
                        embed,
                        name="👑 Cảnh Giới Tối Cao",
                        value=f"• {item_header} đã đạt **+150 TỐI ĐA**! Hãy bấm **Tiến Cấp Sao** để thăng hoa sức mạnh!",
                        inline=True
                    )
            else:
                safe_add_field(embed, name=f"⚠️ Chưa Trang Bị {item_header}", value=f"Hãy trang bị {item_header} trước khi cường hóa!", inline=False)

            embed.set_footer(text=f"Trang 4: Lò Rèn Cường Hóa (+150) & Tiến Cấp Sao ⭐ 1-20 • Mục tiêu: {item_header}")

        elif self.inv_page == 4:
            is_pick = (self.enhance_target == "pick")
            if is_pick:
                from Command.command_mining import get_user_mining
                u_mine = get_user_mining(self.author.id)
                pick_id = u_mine.get("equipped_pick")
                cur_target = u_mine.get("picks", {}).get(pick_id) if pick_id else None
                item_header = "⛏️ Cuốc Đào Khoáng"
            else:
                cur_target = cur_rod
                item_header = "🎣 Cần Câu Cá"

            if cur_target:
                max_slots = get_max_enchant_slots(cur_target)
                affixes = cur_target.get("enchant_affixes") if not is_pick else (cur_target.get("affixes") or cur_target.get("enchant_affixes", []))
                if affixes is None:
                    affixes = []
                extra_unlocked = cur_target.get("extra_enchant_slots", 0) > 0

                affix_lines = []
                for i, aff in enumerate(affixes, 1):
                    fmt = aff.get("format") or aff.get("fmt") or f"+{aff.get('val', 0)} {aff.get('stat', '')}"
                    affix_lines.append(f"`[Ô {i}]` {aff.get('icon', '✨')} **{aff.get('name', 'Thuộc tính')}**: `{fmt}`")

                while len(affix_lines) < max_slots:
                    affix_lines.append(f"`[Ô {len(affix_lines) + 1}]` *(Trống - Có thể gán dòng mới)*")

                safe_add_field(
                    embed,
                    name=f"✨ Dòng Enchant Trên {item_header} ({len(affixes)}/{max_slots} Ô)",
                    value="\n".join(affix_lines),
                    inline=False
                )

                items = u_fish.setdefault("items", {})
                end_stone_cnt = items.get("end_crystal", 0)
                special_stone_cnt = items.get("special_enchant_stone", 0)

                safe_add_field(
                    embed,
                    name="💎 Chi Phí & Nguyên Liệu Enchant",
                    value=(
                        f"• 💎 **Đá Pha Lê End**: `{end_stone_cnt}` viên (Bán ở Shop)\n"
                        f"• 🔮 **Đá Enchant Đặc Biệt**: `{special_stone_cnt}` viên\n"
                        f"• Gán dòng mới: **1 Đá End + 10,000,000 Coins**\n"
                        f"• Mở thêm ô dòng: **1 Đá Đặc Biệt + 100,000,000 Coins** {'*(Đã mở)*' if extra_unlocked else ''}"
                    ),
                    inline=False
                )
            else:
                safe_add_field(embed, name=f"⚠️ Chưa Trang Bị {item_header}", value=f"Hãy trang bị {item_header} trước khi enchant!", inline=False)

            embed.set_footer(text=f"Trang 5: Bàn Phép Gán Dòng Enchant Thuộc Tính Cao Cấp • Mục tiêu: {item_header}")

        else:
            from Command.command_mining import get_user_mining, MINING_ZONES, RARITY_ICONS as M_ICONS
            u_mine = get_user_mining(self.author.id)
            eq_pick_id = u_mine.get("equipped_pick")
            cur_pick = u_mine.get("picks", {}).get(eq_pick_id) if eq_pick_id else None
            m_zone = MINING_ZONES.get(u_mine.get("zone", "hang_dat"), MINING_ZONES["hang_dat"])

            if cur_pick:
                ref_str = f" (+{cur_pick.get('refine', 0)})" if cur_pick.get("refine", 0) > 0 else ""
                star_str = f" [⭐x{cur_pick.get('stars', 0)}]" if cur_pick.get("stars", 0) > 0 else ""
                dur = cur_pick.get("durability", 0)
                max_dur = cur_pick.get("max_durability", 60)
                dur_pct = max(0, min(100, int((dur / max_dur) * 100))) if max_dur > 0 else 0
                bar_len = 8
                filled = int(bar_len * (dur_pct / 100))
                dur_bar = "█" * filled + "░" * (bar_len - filled)
                pick_desc = f"**{cur_pick['name']}{ref_str}{star_str}**\n• Độ bền: `[{dur_bar}] {dur}/{max_dur}` ({dur_pct}%)\n• May mắn: `+{cur_pick.get('luck', 5)}`"
            else:
                pick_desc = "*(Chưa trang bị cuốc đào nào)*"

            safe_add_field(embed, name="⛏️ Cuốc Đào Đang Cầm", value=pick_desc, inline=True)

            ore_bag = u_mine.get("ore_bag", [])
            max_mbag = u_mine.get("max_bag", 30)
            total_ore_val = sum(o.get("price", 0) for o in ore_bag)
            safe_add_field(
                embed,
                name="🎒 Giỏ Quặng & Hầm Mỏ",
                value=f"• Sức chứa: **`{len(ore_bag)}/{max_mbag}`** khối\n• Tổng trị giá: **`{total_ore_val:,}` coin**\n• Mỏ hiện tại: **{m_zone['name']}**\n• May mắn mỏ: `+{m_zone['luck_bonus']}`",
                inline=True
            )

            supplies = u_mine.get("supplies", {})
            sup_lines = [f"• {sid}: `x{cnt}`" for sid, cnt in supplies.items() if cnt > 0]
            sup_text = "\n".join(sup_lines[:6]) if sup_lines else "*Chưa có vật tư hầm mỏ*"
            safe_add_field(embed, name="🧨 Vật Tư Hầm Mỏ", value=sup_text, inline=True)

            if ore_bag:
                recent_ores = []
                for o in reversed(ore_bag[-6:]):
                    o_mut = f" [{o['mutation']}]" if o.get("mutation") else ""
                    o_icon = M_ICONS.get(o.get("rarity", "common"), "💎")
                    recent_ores.append(f"{o_icon} **{o['name']}**{o_mut} (`{o.get('weight', 0)}kg` - `{o.get('price', 0):,}`c)")
                safe_add_field(embed, name=f"💎 Khoáng Sản Trong Túi ({len(ore_bag)} khối - mới nhất)", value="\n".join(recent_ores), inline=False)
            else:
                safe_add_field(embed, name="💎 Khoáng Sản Trong Túi", value="*Túi quặng trống. Dùng `s!mine` để vung cuốc đào khoáng!*", inline=False)

            embed.set_footer(text="Trang 6: Kho Quặng & Cuốc Đào • Dùng [Bán Toàn Bộ Quặng] hoặc gửi vào Bảo Tàng!")

        return embed

    async def _on_switch_tab(self, interaction: discord.Interaction):
        self.inv_page = int(interaction.data["values"][0])
        self._build_components()
        u_data = await get_user_data(self.guild_id, self.author.id)
        await interaction.response.edit_message(embed=self.build_embed(u_data.get("coins", 0), int(u_data.get("xu", 0))), view=self)

    async def _select_pet_callback(self, interaction: discord.Interaction):
        selected_pet = interaction.data["values"][0]
        u_fish = get_user_fishing(self.author.id)
        if selected_pet == "none":
            u_fish["equipped_pet"] = None
            msg = "❌ Đã tháo thú cưng."
        else:
            u_fish["equipped_pet"] = selected_pet
            msg = f"🐾 Đã dẫn theo: **{PETS_CATALOG[selected_pet]['name']}**!"
        save_fishing_data()

        self._build_components()
        u_data = await get_user_data(self.guild_id, self.author.id)
        await interaction.response.edit_message(embed=self.build_embed(u_data.get("coins", 0), int(u_data.get("xu", 0))), view=self)
        await interaction.followup.send(msg, ephemeral=True)

    async def _select_chest_callback(self, interaction: discord.Interaction):
        c_id = interaction.data["values"][0]
        u_fish = get_user_fishing(self.author.id)
        chests = u_fish.setdefault("chests", {})

        if chests.get(c_id, 0) <= 0:
            return await interaction.response.send_message("❌ Bạn không có rương loại này để mở!", ephemeral=True)

        c_info = CHESTS_DATA[c_id]
        req_k = c_info.get("req_key")
        if req_k:
            items = u_fish.setdefault("items", {})
            if items.get(req_k, 0) <= 0:
                k_name = UTILITY_ITEMS[req_k]["name"]
                return await interaction.response.send_message(f"🔒 Rương này bị khóa kín! Bạn cần sở hữu **{k_name}** trong túi để mở khóa rương.", ephemeral=True)
            items[req_k] -= 1

        chests[c_id] -= 1
        reward_coins = random.randint(c_info["min_coin"], c_info["max_coin"])
        reward_bait = random.choice(c_info["bait_pool"])
        b_name = BAITS_CATALOG.get(reward_bait, {}).get("name", "Mồi")

        reward_lines = [f"• 💰 **`+{reward_coins:,}` coin**", f"• 🪱 **1x {b_name}**"]
        u_fish.setdefault("baits", {})[reward_bait] = u_fish.setdefault("baits", {}).get(reward_bait, 0) + 1

        if c_info.get("rod_pool") and random.random() < 0.08:
            won_rod_id = random.choice(c_info["rod_pool"])
            r_item = RODS_CATALOG[won_rod_id]
            u_fish.setdefault("rods", {})[won_rod_id] = {
                "name": r_item["name"], "durability": r_item["durability"],
                "max_durability": r_item["durability"], "luck": r_item["luck"],
                "price": r_item["price"], "refine": 0, "stars": 0
            }
            reward_lines.append(f"• 🎣 **CẦN ĐỘC QUYỀN: {r_item['name']}**!")

        if c_info.get("item_pool") and random.random() < 0.15:
            won_item_id = random.choice(c_info["item_pool"])
            it_info = UTILITY_ITEMS[won_item_id]
            u_fish.setdefault("items", {})[won_item_id] = u_fish.setdefault("items", {}).get(won_item_id, 0) + 1
            reward_lines.append(f"• 🔮 **BÁU VẬT HIẾM: {it_info['name']}**!")

        await update_user_coins(self.guild_id, self.author.id, reward_coins)
        save_fishing_data()

        self._build_components()
        u_data = await get_user_data(self.guild_id, self.author.id)
        await interaction.response.edit_message(embed=self.build_embed(u_data.get("coins", 0), int(u_data.get("xu", 0))), view=self)
        await interaction.followup.send(f"🗝️ **MỞ {c_info['name'].upper()} THÀNH CÔNG!**\n" + "\n".join(reward_lines), ephemeral=False)

    async def _open_redeem_code(self, interaction: discord.Interaction):
        await interaction.response.send_modal(RedeemCodeModal(self.author, self.guild_id))

    async def _select_rod_callback(self, interaction: discord.Interaction):
        selected_rod = interaction.data["values"][0]
        u_fish = get_user_fishing(self.author.id)
        u_fish["equipped_rod"] = selected_rod
        save_fishing_data()

        self._build_components()
        u_data = await get_user_data(self.guild_id, self.author.id)
        await interaction.response.edit_message(embed=self.build_embed(u_data.get("coins", 0), int(u_data.get("xu", 0))), view=self)
        await interaction.followup.send(f"🎣 Đã trang bị: **{u_fish['rods'][selected_rod]['name']}**!", ephemeral=True)

    async def _select_bait_callback(self, interaction: discord.Interaction):
        selected_bait = interaction.data["values"][0]
        u_fish = get_user_fishing(self.author.id)
        if selected_bait == "none":
            u_fish["equipped_bait"] = None
            msg = "❌ Đã tháo mồi câu."
        else:
            u_fish["equipped_bait"] = selected_bait
            msg = f"🪱 Đã trang bị: **{BAITS_CATALOG[selected_bait]['name']}**!"
        save_fishing_data()

        self._build_components()
        u_data = await get_user_data(self.guild_id, self.author.id)
        await interaction.response.edit_message(embed=self.build_embed(u_data.get("coins", 0), int(u_data.get("xu", 0))), view=self)
        await interaction.followup.send(msg, ephemeral=True)

    async def _select_item_callback(self, interaction: discord.Interaction):
        item_id = interaction.data["values"][0]
        u_fish = get_user_fishing(self.author.id)
        items = u_fish.setdefault("items", {})
        now = time.time()

        if items.get(item_id, 0) <= 0:
            return await interaction.response.send_message("❌ Bạn không còn vật phẩm này trong kho!", ephemeral=True)

        if item_id == "shield":
            items["shield"] -= 1
            u_fish.setdefault("buffs", {})["shield"] = True
            save_fishing_data()
            self._build_components()
            u_data = await get_user_data(self.guild_id, self.author.id)
            await interaction.response.edit_message(embed=self.build_embed(u_data.get("coins", 0)), view=self)
            return await interaction.followup.send("🛡️ **KHIÊN BẢO VỆ KÍCH HOẠT!** Bạn được bảo vệ khỏi 1 đòn troll tiếp theo!", ephemeral=True)

        if item_id == "magic_mirror":
            items["magic_mirror"] -= 1
            u_fish.setdefault("buffs", {})["magic_mirror"] = True
            save_fishing_data()
            self._build_components()
            u_data = await get_user_data(self.guild_id, self.author.id)
            await interaction.response.edit_message(embed=self.build_embed(u_data.get("coins", 0)), view=self)
            return await interaction.followup.send("🪞 **GƯƠNG PHẢN CHIẾU KÍCH HOẠT!** Sẵn sàng phản lại đòn troll của người khác!", ephemeral=True)

        if item_id == "treasure_map":
            items["treasure_map"] -= 1
            u_fish.setdefault("buffs", {})["treasure_map_luck"] = now + 3600
            save_fishing_data()
            self._build_components()
            u_data = await get_user_data(self.guild_id, self.author.id)
            await interaction.response.edit_message(embed=self.build_embed(u_data.get("coins", 0)), view=self)
            return await interaction.followup.send("🗺️ **BẢN ĐỒ KHO BÁU!** Tăng gấp đôi May Mắn trong 60 phút!", ephemeral=True)

        if item_id == "relic_sea_stone":
            items["relic_sea_stone"] -= 1
            u_fish.setdefault("buffs", {})["relic_sea_stone_charges"] = 30
            save_fishing_data()
            self._build_components()
            u_data = await get_user_data(self.guild_id, self.author.id)
            await interaction.response.edit_message(embed=self.build_embed(u_data.get("coins", 0)), view=self)
            return await interaction.followup.send("🗿 **ĐÁ TRẤN HẢI KÍCH HOẠT!** Cần câu không bị trừ độ bền trong 30 lần thả câu tiếp theo!", ephemeral=True)

        if item_id == "relic_golden_scale":
            items["relic_golden_scale"] -= 1
            u_fish.setdefault("buffs", {})["golden_scale_price"] = now + 3600
            save_fishing_data()
            self._build_components()
            u_data = await get_user_data(self.guild_id, self.author.id)
            await interaction.response.edit_message(embed=self.build_embed(u_data.get("coins", 0)), view=self)
            return await interaction.followup.send("🪙 **VẢY RỒNG VÀNG!** Toàn bộ cá bán được cộng thêm **+50% Coin** trong 60 phút!", ephemeral=True)

        if item_id == "potion_x2_coins_2h":
            items["potion_x2_coins_2h"] -= 1
            u_fish.setdefault("buffs", {})["double_coins_buff"] = now + 7200
            save_fishing_data()
            self._build_components()
            u_data = await get_user_data(self.guild_id, self.author.id)
            await interaction.response.edit_message(embed=self.build_embed(u_data.get("coins", 0)), view=self)
            return await interaction.followup.send("🧪 **THUỐC NHÂN ĐÔI COINS (2H) ĐÃ KÍCH HOẠT!** Toàn bộ cá bán thu về gấp đôi (**x2 Coins**) trong 2 giờ tới!", ephemeral=True)

        if item_id == "pearl_ancient":
            items["pearl_ancient"] -= 1
            coin_earned = random.randint(500000, 1500000)
            await update_user_coins(self.guild_id, self.author.id, coin_earned)
            save_fishing_data()
            self._build_components()
            u_data = await get_user_data(self.guild_id, self.author.id)
            await interaction.response.edit_message(embed=self.build_embed(u_data.get("coins", 0)), view=self)
            return await interaction.followup.send(f"🔮 **NGỌC TRAI CỔ ĐẠI!** Bạn đã bán cho thương gia thu về **`+{coin_earned:,}` coin**!", ephemeral=True)

        if item_id == "ve_so":
            items["ve_so"] -= 1
            roll = random.random()
            if roll < 0.005:
                prize = 2000000
                txt = "🎉🎉 **TRÚNG ĐẶC BIỆT!** Bạn nhận được **2,000,000 coin**!"
            elif roll < 0.05:
                prize = 300000
                txt = "🎊 **TRÚNG GIẢI NHẤT!** Bạn nhận được **300,000 coin**!"
            elif roll < 0.25:
                prize = 75000
                txt = "✨ **TRÚNG GIẢI NHÌ!** Bạn nhận được **75,000 coin**!"
            elif roll < 0.55:
                prize = 30000
                txt = "🍀 **HOÀN VỐN!** Bạn nhận lại **30,000 coin**!"
            else:
                prize = 0
                txt = "😢 **CHÚC BẠN MAY MẮN LẦN SAU!** Vé số không trúng giải nào."

            if prize > 0:
                await update_user_coins(self.guild_id, self.author.id, prize)
            save_fishing_data()

            self._build_components()
            u_data = await get_user_data(self.guild_id, self.author.id)
            await interaction.response.edit_message(embed=self.build_embed(u_data.get("coins", 0)), view=self)
            return await interaction.followup.send(txt, ephemeral=True)

        modal = ItemTargetModal(item_id, self.author)
        await interaction.response.send_modal(modal)

    async def _recycle_trash(self, interaction: discord.Interaction):
        u_fish = get_user_fishing(self.author.id)
        trash = u_fish.setdefault("trash_bag", {})
        total_items = sum(trash.values())
        if total_items <= 0:
            return await interaction.response.send_message("♻️ Túi của bạn không có rác để tái chế!", ephemeral=True)

        earned = 0
        bottle_bonus = 0
        for tid, cnt in list(trash.items()):
            if cnt > 0 and tid in TRASH_ITEMS:
                earned += TRASH_ITEMS[tid]["recycle_price"] * cnt
                if tid == "trash_bottle":
                    for _ in range(cnt):
                        bottle_bonus += random.randint(10000, 80000)

        total_reward = earned + bottle_bonus
        u_fish["trash_bag"] = {}
        await update_user_coins(self.guild_id, self.author.id, total_reward)
        save_fishing_data()

        self._build_components()
        u_data = await get_user_data(self.guild_id, self.author.id)
        await interaction.response.edit_message(embed=self.build_embed(u_data.get("coins", 0)), view=self)
        bonus_txt = f" (Kèm `{bottle_bonus:,}`c nhặt trong thư chai)" if bottle_bonus > 0 else ""
        await interaction.followup.send(f"♻️ **TÁI CHẾ THÀNH CÔNG!** Đã tái chế **{total_items}** món rác nhận **`+{total_reward:,}` coin**!{bonus_txt}", ephemeral=True)

    async def _open_sell_tiered_modal(self, interaction: discord.Interaction):
        class SellTierSelectView(discord.ui.View):
            def __init__(self, inv_parent: "FishingInventoryView"):
                super().__init__(timeout=60)
                self.inv_parent = inv_parent

            @discord.ui.select(
                placeholder="🐟 Chọn phân cấp cá bạn muốn bán...",
                options=[
                    discord.SelectOption(label="Bán Cá Đột Biến (Mutated)", value="mutation", emoji="🧬", description="Bán toàn bộ cá mang gen đột biến quý giá"),
                    discord.SelectOption(label="Bán Cá Thường (Common)", value="common", emoji="⚪"),
                    discord.SelectOption(label="Bán Cá Hiếm (Rare)", value="rare", emoji="🔵"),
                    discord.SelectOption(label="Bán Cá Sử Thi (Epic)", value="epic", emoji="🟣"),
                    discord.SelectOption(label="Bán Cá Huyền Thoại (Legendary)", value="legendary", emoji="🟡"),
                    discord.SelectOption(label="Bán Toàn Bộ (lọc Admin/Event/đột biến)", value="all", emoji="💰"),
                    discord.SelectOption(label="Bán cá sự kiện (Event)", value="event", emoji="🎉"),
                    discord.SelectOption(label="Bán cá Admin (cẩn thận)", value="admin", emoji="🔴"),
                ]
            )
            async def select_tier(self, select_inter: discord.Interaction, select: discord.ui.Select):
                tier = select.values[0]
                u_fish = get_user_fishing(self.inv_parent.author.id)
                bag = u_fish.get("fish_bag", [])
                def is_event_fish(f):
                    return bool(f.get("event") or f.get("is_event") or f.get("event_fish") or f.get("source") == "event" or any(isinstance(ef, dict) and str(f.get("name", "")).strip() == str(ef.get("name", "")).strip() for ef in event_fish))
                def eligible(f):
                    rarity = str(f.get("rarity", "common")).lower()
                    if tier == "mutation":
                        return bool(f.get("mutation")) and rarity != "admin"
                    if tier == "event":
                        return is_event_fish(f) and rarity != "admin"
                    if tier == "admin":
                        return rarity == "admin"
                    if tier == "all":
                        return rarity != "admin" and not is_event_fish(f) and not f.get("mutation")
                    return rarity == tier and rarity != "admin" and not is_event_fish(f) and not f.get("mutation")
                to_sell = [f for f in bag if eligible(f)]

                if not to_sell:
                    return await select_inter.response.send_message(f"⚠️ Không có cá phù hợp bộ lọc `{tier.upper()}` để bán!", ephemeral=True)

                earned = sum(f.get("price", 0) for f in to_sell)
                sell_ids = {id(f) for f in to_sell}
                u_fish["fish_bag"] = [f for f in bag if id(f) not in sell_ids]
                u_fish["stats"]["total_earned"] = u_fish["stats"].get("total_earned", 0) + earned
                await update_user_coins(self.inv_parent.guild_id, self.inv_parent.author.id, earned)
                save_fishing_data()

                self.inv_parent._build_components()
                u_data = await get_user_data(self.inv_parent.guild_id, self.inv_parent.author.id)
                await select_inter.response.send_message(f"💰 Đã bán thành công **{len(to_sell)}** con cá theo bộ lọc **{tier.upper()}** thu về **`+{earned:,}` coin**!", ephemeral=True)

        await interaction.response.send_message("Chọn phân cấp cá muốn thanh lý:", view=SellTierSelectView(self), ephemeral=True)

    async def _goto_farm_view(self, interaction: discord.Interaction):
        from Command.farm_system import FarmView
        fv = FarmView(self.author, self.guild_id)
        await interaction.response.edit_message(embed=fv.build_embed(), view=fv)

    async def _goto_farm_shop(self, interaction: discord.Interaction):
        shop_view = FishingShopView(self.author, self.guild_id)
        shop_view.selected_category = "seed"
        shop_view.current_page = 0
        shop_view._refresh_components()
        u_data = await get_user_data(self.guild_id, self.author.id)
        await interaction.response.edit_message(embed=shop_view.build_embed(u_data.get("coins", 0), int(u_data.get("xu", 0))), view=shop_view)

    async def _goto_material_shop(self, interaction: discord.Interaction):
        shop_view = FishingShopView(self.author, self.guild_id)
        shop_view.selected_category = "item"
        shop_view.current_page = 0
        shop_view._refresh_components()
        u_data = await get_user_data(self.guild_id, self.author.id)
        await interaction.response.edit_message(embed=shop_view.build_embed(u_data.get("coins", 0), int(u_data.get("xu", 0))), view=shop_view)

    async def _sell_all_crops(self, interaction: discord.Interaction):
        u_fish = get_user_fishing(self.author.id)
        farm_data = u_fish.setdefault("farm", {})
        crops = farm_data.setdefault("crops", {})

        total_earned = 0
        total_count = 0
        for cid, cnt in list(crops.items()):
            if cnt > 0:
                c_info = get_crop_info(cid)
                total_earned += c_info.get("sell_price", 500) * cnt
                total_count += cnt

        mutated = farm_data.get("mutated_crops", [])
        mut_count = len(mutated)
        mut_earned = sum(m.get("sell_price", 1000) for m in mutated)
        total_earned += mut_earned
        total_count += mut_count

        if total_count <= 0:
            return await interaction.response.send_message("⚠️ Kho nông sản của bạn đang trống, không có hoa màu để bán!", ephemeral=True)

        farm_data["crops"] = {}
        farm_data["mutated_crops"] = []
        await update_user_coins(self.guild_id, self.author.id, total_earned)
        save_fishing_data()

        self._build_components()
        u_data = await get_user_data(self.guild_id, self.author.id)
        await interaction.response.edit_message(embed=self.build_embed(u_data.get("coins", 0)), view=self)
        detail_mut = f" (bao gồm **{mut_count}** nông sản đột biến `+{mut_earned:,}`c)" if mut_count > 0 else ""
        await interaction.followup.send(f"💰 **BÁN NÔNG SẢN THÀNH CÔNG!** Đã xuất bán **{total_count}** nông sản các loại{detail_mut}, thu về **`+{total_earned:,}` coin**!", ephemeral=True)

    async def _sell_all_pests(self, interaction: discord.Interaction):
        u_fish = get_user_fishing(self.author.id)
        farm_data = u_fish.setdefault("farm", {})
        pests = farm_data.setdefault("pests", {})

        total_earned = 0
        total_count = 0
        for pid, cnt in list(pests.items()):
            if cnt > 0 and pid in PESTS_CATALOG:
                total_earned += PESTS_CATALOG[pid]["sell_price"] * cnt
                total_count += cnt

        if total_count <= 0:
            return await interaction.response.send_message("⚠️ Bạn không có sâu bọ nào trong kho để bán!", ephemeral=True)

        farm_data["pests"] = {}
        await update_user_coins(self.guild_id, self.author.id, total_earned)
        save_fishing_data()

        self._build_components()
        u_data = await get_user_data(self.guild_id, self.author.id)
        await interaction.response.edit_message(embed=self.build_embed(u_data.get("coins", 0)), view=self)
        await interaction.followup.send(f"🐛 **BÁN SÂU BỌ THÀNH CÔNG!** Đã bán **{total_count}** con sâu bọ cho thương gia làm mồi câu, thu về **`+{total_earned:,}` coin**!", ephemeral=True)

    async def _eat_crop_callback(self, interaction: discord.Interaction):
        crop_id = interaction.data["values"][0]
        u_fish = get_user_fishing(self.author.id)
        farm_data = u_fish.setdefault("farm", {})
        crops = farm_data.setdefault("crops", {})

        if crops.get(crop_id, 0) <= 0:
            return await interaction.response.send_message("❌ Bạn không còn nông sản loại này trong kho!", ephemeral=True)

        c_info = get_crop_info(crop_id)
        if not c_info:
            return await interaction.response.send_message("❌ Vật phẩm không hợp lệ!", ephemeral=True)

        crops[crop_id] -= 1
        rod_id = u_fish.get("equipped_rod")
        cur_rod = u_fish.get("rods", {}).get(rod_id) if rod_id else None

        dur_restored = 20
        buff_msg = ""
        now = time.time()

        if any(k in crop_id for k in ("golden_apple", "peach", "snow_lotus")):
            if cur_rod:
                cur_rod["durability"] = cur_rod.get("max_durability", 100)
            u_fish.setdefault("buffs", {})["divine_fruit_buff"] = now + 3600
            buff_msg = "🌟 Hồi phục **100% Độ Bền Cần** và kích hoạt Hào Quang Thần Quả (+60 May Mắn trong 60 phút)!"
        elif any(k in crop_id for k in ("watermelon", "strawberry", "grape")):
            dur_restored = 40
            if cur_rod:
                cur_rod["durability"] = min(cur_rod.get("max_durability", 100), cur_rod.get("durability", 0) + dur_restored)
            buff_msg = f"🍎 Thơm ngon mát lành! Hồi phục **+{dur_restored} Độ Bền Cần Câu**!"
        else:
            dur_restored = 15
            if cur_rod:
                cur_rod["durability"] = min(cur_rod.get("max_durability", 100), cur_rod.get("durability", 0) + dur_restored)
            buff_msg = f"🥗 Bổ sung dinh dưỡng! Hồi phục **+{dur_restored} Độ Bền Cần Câu**!"

        save_fishing_data()
        self._build_components()
        u_data = await get_user_data(self.guild_id, self.author.id)
        await interaction.response.edit_message(embed=self.build_embed(u_data.get("coins", 0)), view=self)
        await interaction.followup.send(f"😋 **ĂN {c_info['name'].upper()} THÀNH CÔNG!** {buff_msg}", ephemeral=True)

    async def _switch_enhance_target(self, interaction: discord.Interaction):
        self.enhance_target = "rod" if self.enhance_target == "pick" else "pick"
        self._build_components()
        u_data = await get_user_data(self.guild_id, self.author.id)
        target_name = "⛏️ Cuốc Đào Khoáng" if self.enhance_target == "pick" else "🎣 Cần Câu Cá"
        await interaction.response.edit_message(embed=self.build_embed(u_data.get("coins", 0), int(u_data.get("xu", 0))), view=self)
        await interaction.followup.send(f"🔄 Đã chuyển mục tiêu sang: **{target_name}**!", ephemeral=True)

    async def _upgrade_rod(self, interaction: discord.Interaction):
        u_fish = get_user_fishing(self.author.id)
        is_pick = (self.enhance_target == "pick")
        if is_pick:
            from Command.command_mining import get_user_mining, save_mining_data as save_mine_fn, get_pick_enchant_stats
            u_mine = get_user_mining(self.author.id)
            target_id = u_mine.get("equipped_pick")
            if not target_id or target_id not in u_mine.get("picks", {}):
                return await interaction.response.send_message("❌ Bạn cần trang bị cuốc đào trước khi đập đồ!", ephemeral=True)
            target_item = u_mine["picks"][target_id]
            item_type_label = "Cuốc"
            ench_stats = get_pick_enchant_stats(target_item)
            save_fn = save_mine_fn
        else:
            target_id = u_fish.get("equipped_rod")
            if not target_id or target_id not in u_fish.get("rods", {}):
                return await interaction.response.send_message("❌ Bạn cần trang bị một cần câu trước khi đập đồ!", ephemeral=True)
            target_item = u_fish["rods"][target_id]
            item_type_label = "Cần câu"
            ench_stats = get_rod_enchant_stats(target_item)
            save_fn = save_fishing_data

        curr_refine = target_item.setdefault("refine", 0)

        if curr_refine >= 300:
            return await interaction.response.send_message(f"⭐ {item_type_label} này đã đạt cấp tối đa (**+300 TỐI THƯỢNG**)! Hãy sử dụng tính năng **Tiến Cấp Sao** để thăng cấp sức mạnh!", ephemeral=True)

        base_cost = max(target_item.get("price", 5000), 10000)
        cost = max(3000, int(base_cost * 0.18 * ((curr_refine + 1) ** 1.25)))
        u_data = await get_user_data(self.guild_id, self.author.id)
        if u_data.get("coins", 0) < cost:
            return await interaction.response.send_message(f"❌ Không đủ coin! Cần **`{cost:,}` coin** để cường hóa lên +{curr_refine + 1}.", ephemeral=True)

        await update_user_coins(self.guild_id, self.author.id, -cost)

        if curr_refine < 10:
            success_rate = 1.0 - (curr_refine * 0.03)
        elif curr_refine < 30:
            success_rate = max(0.25, 0.65 - ((curr_refine - 10) * 0.012))
        elif curr_refine < 70:
            success_rate = max(0.12, 0.35 - ((curr_refine - 30) * 0.004))
        elif curr_refine < 120:
            success_rate = max(0.06, 0.15 - ((curr_refine - 70) * 0.0015))
        elif curr_refine < 200:
            success_rate = max(0.03, 0.06 - ((curr_refine - 120) * 0.0004))
        else:
            success_rate = max(0.015, 0.03 - ((curr_refine - 200) * 0.00015))

        if ench_stats.get("refine_rate", 0) > 0:
            success_rate = min(0.95, success_rate + (ench_stats["refine_rate"] / 100.0))

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
            success_rate = 1.0
        else:
            try:
                from data.game_rates import calculate_refine_rate
                success_rate = calculate_refine_rate(success_rate)
            except Exception:
                pass

        if random.random() <= success_rate:
            target_item["refine"] += 1
            target_item["max_durability"] = int(target_item.get("max_durability", 100) * 1.10)
            target_item["durability"] = target_item["max_durability"]
            bonus_luck_add = 3 if target_item["refine"] <= 15 else (5 if target_item["refine"] <= 50 else (8 if target_item["refine"] <= 150 else 15))
            target_item["luck"] = target_item.get("luck", 1) + bonus_luck_add
            save_fn()
            try:
                from Command.achievement_system import unlock_achievement
                rf = target_item.get("refine", 0)
                if rf >= 10: await unlock_achievement(self.guild_id, self.author.id, "rod_refine_10", getattr(interaction, "channel", None))
                if rf >= 30: await unlock_achievement(self.guild_id, self.author.id, "rod_refine_30", getattr(interaction, "channel", None))
                if rf >= 50: await unlock_achievement(self.guild_id, self.author.id, "rod_refine_50", getattr(interaction, "channel", None))
                if rf >= 100: await unlock_achievement(self.guild_id, self.author.id, "rod_refine_100", getattr(interaction, "channel", None))
                if rf >= 150: await unlock_achievement(self.guild_id, self.author.id, "rod_refine_150", getattr(interaction, "channel", None))
            except Exception:
                pass
            refine_note = f" (✨ +{ench_stats['refine_rate']}% Bậc Thầy Rèn)" if ench_stats.get("refine_rate", 0) > 0 else ""
            admin_note = " *(👑 Đặc quyền Admin/Owner Auto Lên)*" if is_admin_or_owner else ""
            msg = f"✨ **THÀNH CÔNG RỰC RỠ!** {item_type_label} **{target_item['name']}** đã thăng hoa lên **+{target_item['refine']}/300**{refine_note}{admin_note} (Hồi phục 100% độ bền & tăng +{bonus_luck_add} may mắn)!"
        else:
            save_fn()
            refine_note = f" (Đã +{ench_stats['refine_rate']}% từ Bậc Thầy Rèn)" if ench_stats.get("refine_rate", 0) > 0 else ""
            msg = f"💥 **THẤT BẠI!** Bạn mất `{cost:,}` coin phí đập đồ (Tỉ lệ thành công: `{success_rate*100:.1f}%`{refine_note}). Cố gắng thêm nhé!"

        self._build_components()
        new_data = await get_user_data(self.guild_id, self.author.id)
        await interaction.response.edit_message(embed=self.build_embed(new_data.get("coins", 0)), view=self)
        await interaction.followup.send(msg, ephemeral=True)

    async def _ascend_star(self, interaction: discord.Interaction):
        """Tiến cấp Sao (1-20 sao) cho cần câu hoặc cuốc đào đạt +150."""
        u_fish = get_user_fishing(self.author.id)
        is_pick = (self.enhance_target == "pick")
        if is_pick:
            from Command.command_mining import get_user_mining, save_mining_data as save_mine_fn, get_pick_enchant_stats
            u_mine = get_user_mining(self.author.id)
            target_id = u_mine.get("equipped_pick")
            if not target_id or target_id not in u_mine.get("picks", {}):
                return await interaction.response.send_message("❌ Bạn cần trang bị cuốc đào!", ephemeral=True)
            target_item = u_mine["picks"][target_id]
            item_type_label = "Cuốc đào"
            ench_stats = get_pick_enchant_stats(target_item)
            save_fn = save_mine_fn
        else:
            target_id = u_fish.get("equipped_rod")
            if not target_id or target_id not in u_fish.get("rods", {}):
                return await interaction.response.send_message("❌ Bạn cần trang bị một cần câu!", ephemeral=True)
            target_item = u_fish["rods"][target_id]
            item_type_label = "Cần câu"
            ench_stats = get_rod_enchant_stats(target_item)
            save_fn = save_fishing_data

        if target_item.get("refine", 0) < 150:
            return await interaction.response.send_message(f"❌ {item_type_label} cần đạt cấp cường hóa **+150** trước khi tiến cấp sao! (Hiện tại: `+{target_item.get('refine', 0)}`)", ephemeral=True)

        curr_stars = target_item.setdefault("stars", 0)
        if curr_stars >= 20:
            return await interaction.response.send_message(f"🌟 {item_type_label} đã đạt cấp độ tối đa tuyệt đối: **20 SAO THẦN THÁNH**!", ephemeral=True)

        items = u_fish.setdefault("items", {})
        fish_bag = u_fish.setdefault("fish_bag", [])
        dust = items.get("stardust_dust", 0)
        pearl = items.get("black_pearl", 0)

        missing = []
        if dust < 10:
            missing.append(f"• Bụi sao lấp lánh: thiếu `{10 - dust}` (Hiện có: `{dust}/10`)")
        if len(fish_bag) < 2:
            missing.append(f"• Cá trong giỏ: thiếu `{2 - len(fish_bag)}` con (Hiện có: `{len(fish_bag)}/2`)")
        if pearl < 1:
            missing.append(f"• Ngọc trai đen: thiếu `1` (Hiện có: `0/1` - mở từ Rương Báu)")

        if missing:
            return await interaction.response.send_message("❌ **CHƯA ĐỦ NGUYÊN LIỆU TIẾN CẤP SAO!**\n" + "\n".join(missing), ephemeral=True)

        items["stardust_dust"] -= 10
        items["black_pearl"] -= 1
        sacrificed_fish = [fish_bag.pop(0), fish_bag.pop(0)]

        if curr_stars < 2:
            star_rate = 0.50
        elif curr_stars < 6:
            star_rate = 0.40
        elif curr_stars < 11:
            star_rate = 0.30
        elif curr_stars < 16:
            star_rate = 0.20
        else:
            star_rate = 0.12

        if ench_stats.get("refine_rate", 0) > 0:
            star_rate = min(0.90, star_rate + (ench_stats["refine_rate"] / 100.0))

        try:
            from data.game_rates import calculate_star_rate
            star_rate = calculate_star_rate(star_rate)
        except Exception:
            pass

        is_success = (random.random() <= star_rate)

        if is_success:
            target_item["stars"] += 1
            target_item["refine"] = 0
            bonus_luck = 60
            target_item["luck"] = target_item.get("luck", 1) + bonus_luck
            save_fn()
            save_fishing_data()
            try:
                from Command.achievement_system import unlock_achievement
                st = target_item.get("stars", 0)
                if st >= 1: await unlock_achievement(self.guild_id, self.author.id, "rod_star_1", getattr(interaction, "channel", None))
                if st >= 5: await unlock_achievement(self.guild_id, self.author.id, "rod_star_5", getattr(interaction, "channel", None))
                if st >= 10: await unlock_achievement(self.guild_id, self.author.id, "rod_star_10", getattr(interaction, "channel", None))
                if st >= 20: await unlock_achievement(self.guild_id, self.author.id, "rod_star_20", getattr(interaction, "channel", None))
            except Exception:
                pass
            star_disp = "⭐" * target_item["stars"]
            msg = (
                f"🎉🌟 **TIẾN CẤP SAO THÀNH CÔNG RỰC RỠ!**\n"
                f"{item_type_label} **{target_item['name']}** đã thăng hoa lên **⭐ {target_item['stars']} SAO** ({star_disp})!\n"
                f"• Cấp cường hóa đã được đặt lại về **+0** để bạn tiếp tục đập lên các cấp sao tiếp theo!\n"
                f"• Nhận vĩnh viễn: **+{bonus_luck} May Mắn**\n"
                f"• Tăng thêm: **+15% Giá Bán Thu Hoạch**\n"
                f"• Hiển thị huy hiệu sao rực rỡ trên Web Dashboard!"
            )
        else:
            items["stardust_dust"] = items.get("stardust_dust", 0) + 5
            fish_bag.append(sacrificed_fish[0])
            refund_pearl = (random.random() < 0.50)
            if refund_pearl:
                items["black_pearl"] = items.get("black_pearl", 0) + 1

            pearl_text = "• 🦪 Hoàn trả: **1x Ngọc Trai Đen**\n" if refund_pearl else "• 🦪 Ngọc trai đen đã bị vỡ vụn.\n"
            save_fn()
            save_fishing_data()
            msg = (
                f"💥 **TIẾN CẤP SAO THẤT BẠI!**\n"
                f"Năng lượng sao tinh tú quá lớn khiến nghi thức thăng cấp thất bại (Tỉ lệ: `{star_rate*100:.0f}%`).\n\n"
                f"🛡️ **CƠ CHẾ BẢO HIỂM HOÀN TRẢ 50% NGUYÊN LIỆU NGẪU NHIÊN:**\n"
                f"• ✨ Hoàn trả: **5x Bụi Sao Lấp Lánh**\n"
                f"• 🐟 Hoàn trả: **1x {sacrificed_fish[0]['name']}**\n"
                f"{pearl_text}"
                f"*{item_type_label} không bị rớt cấp! Hãy thử lại khi gom đủ nguyên liệu.*"
            )

        self._build_components()
        u_data = await get_user_data(self.guild_id, self.author.id)
        await interaction.response.edit_message(embed=self.build_embed(u_data.get("coins", 0)), view=self)
        await interaction.followup.send(msg, ephemeral=False)

    async def _repair_rod(self, interaction: discord.Interaction):
        u_fish = get_user_fishing(self.author.id)
        is_pick = (self.enhance_target == "pick")
        if is_pick:
            from Command.command_mining import get_user_mining, save_mining_data as save_mine_fn
            u_mine = get_user_mining(self.author.id)
            target_id = u_mine.get("equipped_pick")
            if not target_id or target_id not in u_mine.get("picks", {}):
                return await interaction.response.send_message("❌ Bạn cần trang bị cuốc đào!", ephemeral=True)
            target_item = u_mine["picks"][target_id]
            item_type_label = "Cuốc đào"
            save_fn = save_mine_fn
        else:
            target_id = u_fish.get("equipped_rod")
            if not target_id or target_id not in u_fish.get("rods", {}):
                return await interaction.response.send_message("❌ Bạn cần trang bị một cần câu!", ephemeral=True)
            target_item = u_fish["rods"][target_id]
            item_type_label = "Cần câu"
            save_fn = save_fishing_data

        cur_dur = target_item.get("durability", 0)
        max_dur = target_item.get("max_durability", 100)

        if cur_dur >= max_dur:
            return await interaction.response.send_message(f"✨ {item_type_label} của bạn đang ở độ bền tối đa 100%, không cần sửa chữa!", ephemeral=True)

        cost = int(max(5000, (max_dur - cur_dur) * 350))
        u_data = await get_user_data(self.guild_id, self.author.id)
        if u_data.get("coins", 0) < cost:
            return await interaction.response.send_message(f"❌ Bạn không đủ coin để sửa! Cần **`{cost:,}` coin**.", ephemeral=True)

        await update_user_coins(self.guild_id, self.author.id, -cost)
        target_item["durability"] = max_dur
        save_fn()

        self._build_components()
        u_data = await get_user_data(self.guild_id, self.author.id)
        await interaction.response.edit_message(embed=self.build_embed(u_data.get("coins", 0)), view=self)
        await interaction.followup.send(f"🔧 Đã sửa chữa hoàn toàn {item_type_label} **{target_item['name']}** về độ bền **{max_dur}/{max_dur}** với chi phí **`{cost:,}` coin**!", ephemeral=True)

    async def _enchant_rod(self, interaction: discord.Interaction):
        """Gán dòng thuộc tính cho cần câu hoặc cuốc đào: Tốn 1 Đá End + 10,000,000 Coins."""
        u_fish = get_user_fishing(self.author.id)
        is_pick = (self.enhance_target == "pick")
        if is_pick:
            from Command.command_mining import get_user_mining, save_mining_data as save_mine_fn, MINING_ENCHANTS
            u_mine = get_user_mining(self.author.id)
            target_id = u_mine.get("equipped_pick")
            if not target_id or target_id not in u_mine.get("picks", {}):
                return await interaction.response.send_message("❌ Bạn cần trang bị cuốc đào trước khi Enchant!", ephemeral=True)
            target_item = u_mine["picks"][target_id]
            affixes = target_item.setdefault("affixes", [])
            max_slots = get_max_enchant_slots(target_item)
            affix_pool = MINING_ENCHANTS
            item_type_label = "Cuốc"
            save_fn = save_mine_fn
        else:
            target_id = u_fish.get("equipped_rod")
            if not target_id or target_id not in u_fish.get("rods", {}):
                return await interaction.response.send_message("❌ Bạn cần trang bị cần câu trước khi Enchant!", ephemeral=True)
            target_item = u_fish["rods"][target_id]
            affixes = target_item.setdefault("enchant_affixes", [])
            max_slots = get_max_enchant_slots(target_item)
            affix_pool = ENCHANT_AFFIXES
            item_type_label = "Cần câu"
            save_fn = save_fishing_data

        if len(affixes) >= max_slots:
            return await interaction.response.send_message(
                f"❌ {item_type_label} đã đạt giới hạn dòng tối đa (`{len(affixes)}/{max_slots}` ô)!\n"
                f"• Bấm **Mở Ô Dòng** để mở thêm ô đặc biệt (1 Đá Đặc Biệt + 100M)\n"
                f"• Hoặc bấm **Tẩy Dòng** để roll lại từ đầu.",
                ephemeral=True
            )

        items = u_fish.setdefault("items", {})
        end_stone = items.get("end_crystal", 0)
        u_data = await get_user_data(self.guild_id, self.author.id)
        user_coins = u_data.get("coins", 0)
        enchant_cost = 10000000

        if end_stone < 1:
            return await interaction.response.send_message("❌ Bạn cần sở hữu ít nhất **1 Đá Pha Lê End** (Mua trong Shop hoặc câu được dưới biển)!", ephemeral=True)
        if user_coins < enchant_cost:
            return await interaction.response.send_message(f"❌ Bạn không đủ tiền! Cần **`{enchant_cost:,}` coin** cho mỗi lần gán dòng (Hiện có: `{user_coins:,}` coin).", ephemeral=True)

        items["end_crystal"] -= 1
        await update_user_coins(self.guild_id, self.author.id, -enchant_cost)

        chosen_meta = random.choice(affix_pool)
        min_v = chosen_meta.get("min_val", chosen_meta.get("val_range", (15, 50))[0])
        max_v = chosen_meta.get("max_val", chosen_meta.get("val_range", (15, 50))[1])
        val = random.randint(min_v, max_v)
        fmt_template = chosen_meta.get("format") or chosen_meta.get("fmt") or "+{val}"
        fmt = fmt_template.format(val=val)
        new_affix = {
            "id": chosen_meta["id"],
            "name": chosen_meta["name"],
            "stat": chosen_meta["stat"],
            "val": val,
            "icon": chosen_meta.get("icon", "✨"),
            "desc": chosen_meta.get("desc", ""),
            "format": fmt
        }
        affixes.append(new_affix)
        save_fn()
        save_fishing_data()

        self._build_components()
        u_data = await get_user_data(self.guild_id, self.author.id)
        await interaction.response.edit_message(embed=self.build_embed(u_data.get("coins", 0)), view=self)
        await interaction.followup.send(
            f"✨ **ENCHANT THÀNH CÔNG!**\n"
            f"{item_type_label} **{target_item['name']}** vừa được ban phước dòng thuộc tính mới:\n"
            f"└ {new_affix['icon']} **{new_affix['name']}**: `{fmt}` ({new_affix['desc']})!\n"
            f"*(Số ô hiện tại: `{len(affixes)}/{max_slots}` ô)*",
            ephemeral=False
        )

    async def _unlock_extra_enchant_slot(self, interaction: discord.Interaction):
        """Mở thêm 1 ô dòng enchant đặc biệt: Tốn 1 Đá Enchant Đặc Biệt + 100,000,000 Coins."""
        u_fish = get_user_fishing(self.author.id)
        is_pick = (self.enhance_target == "pick")
        if is_pick:
            from Command.command_mining import get_user_mining, save_mining_data as save_mine_fn
            u_mine = get_user_mining(self.author.id)
            target_id = u_mine.get("equipped_pick")
            if not target_id or target_id not in u_mine.get("picks", {}):
                return await interaction.response.send_message("❌ Bạn cần trang bị cuốc đào trước!", ephemeral=True)
            target_item = u_mine["picks"][target_id]
            item_type_label = "Cuốc"
            save_fn = save_mine_fn
        else:
            target_id = u_fish.get("equipped_rod")
            if not target_id or target_id not in u_fish.get("rods", {}):
                return await interaction.response.send_message("❌ Bạn cần trang bị cần câu trước!", ephemeral=True)
            target_item = u_fish["rods"][target_id]
            item_type_label = "Cần câu"
            save_fn = save_fishing_data

        if target_item.get("extra_enchant_slots", 0) >= 1:
            return await interaction.response.send_message(f"⚠️ {item_type_label} này đã mở tối đa thêm 1 ô dòng đặc biệt vượt giới hạn!", ephemeral=True)

        items = u_fish.setdefault("items", {})
        spec_stone = items.get("special_enchant_stone", 0)
        u_data = await get_user_data(self.guild_id, self.author.id)
        coins = u_data.get("coins", 0)
        cost = 100000000

        if spec_stone < 1:
            return await interaction.response.send_message("❌ Bạn cần sở hữu ít nhất **1 Đá Enchant Đặc Biệt** (Mua trong Shop hoặc mở từ Rương Thần Thoại)!", ephemeral=True)
        if coins < cost:
            return await interaction.response.send_message(f"❌ Không đủ coin! Cần **`{cost:,}` coin** (100 triệu coin) để khai mở ô bí truyền.", ephemeral=True)

        items["special_enchant_stone"] -= 1
        await update_user_coins(self.guild_id, self.author.id, -cost)
        target_item["extra_enchant_slots"] = 1
        save_fn()
        save_fishing_data()

        self._build_components()
        u_data = await get_user_data(self.guild_id, self.author.id)
        await interaction.response.edit_message(embed=self.build_embed(u_data.get("coins", 0)), view=self)
        await interaction.followup.send(f"🔓 **KHAI MỞ Ô ENCHANT THÀNH CÔNG!** {item_type_label} **{target_item['name']}** đã được mở rộng thêm **+1 Ô Dòng Đặc Biệt**! (Giới hạn mới: `{get_max_enchant_slots(target_item)}` ô)", ephemeral=False)

    async def _clear_enchant_affixes(self, interaction: discord.Interaction):
        """Xóa sạch các dòng enchant để roll lại."""
        u_fish = get_user_fishing(self.author.id)
        is_pick = (self.enhance_target == "pick")
        if is_pick:
            from Command.command_mining import get_user_mining, save_mining_data as save_mine_fn
            u_mine = get_user_mining(self.author.id)
            target_id = u_mine.get("equipped_pick")
            if not target_id or target_id not in u_mine.get("picks", {}):
                return await interaction.response.send_message("❌ Bạn cần trang bị cuốc đào!", ephemeral=True)
            target_item = u_mine["picks"][target_id]
            aff_key = "affixes"
            item_type_label = "Cuốc"
            save_fn = save_mine_fn
        else:
            target_id = u_fish.get("equipped_rod")
            if not target_id or target_id not in u_fish.get("rods", {}):
                return await interaction.response.send_message("❌ Bạn cần trang bị cần câu!", ephemeral=True)
            target_item = u_fish["rods"][target_id]
            aff_key = "enchant_affixes"
            item_type_label = "Cần câu"
            save_fn = save_fishing_data

        if not target_item.get(aff_key):
            return await interaction.response.send_message(f"⚠️ {item_type_label} hiện tại chưa có dòng enchant nào để tẩy!", ephemeral=True)

        target_item[aff_key] = []
        save_fn()

        self._build_components()
        u_data = await get_user_data(self.guild_id, self.author.id)
        await interaction.response.edit_message(embed=self.build_embed(u_data.get("coins", 0)), view=self)
        await interaction.followup.send(f"♻️ **ĐÃ TẨY TOÀN BỘ DÒNG ENCHANT!** {item_type_label} **{target_item['name']}** đã được thanh tẩy sạch sẽ, sẵn sàng gán dòng mới!", ephemeral=True)

    async def _select_pick_callback(self, interaction: discord.Interaction):
        from Command.command_mining import get_user_mining, save_mining_data as save_mine_fn
        selected_pick = interaction.data["values"][0]
        u_mine = get_user_mining(self.author.id)
        u_mine["equipped_pick"] = selected_pick
        save_mine_fn()

        self._build_components()
        u_data = await get_user_data(self.guild_id, self.author.id)
        await interaction.response.edit_message(embed=self.build_embed(u_data.get("coins", 0), int(u_data.get("xu", 0))), view=self)
        p_name = u_mine.get("picks", {}).get(selected_pick, {}).get("name", selected_pick)
        await interaction.followup.send(f"⛏️ Đã trang bị: **{p_name}**!", ephemeral=True)

    async def _sell_all_ores(self, interaction: discord.Interaction):
        from Command.command_mining import get_user_mining, save_mining_data as save_mine_fn, get_pick_enchant_stats
        u_mine = get_user_mining(self.author.id)
        bag = u_mine.setdefault("ore_bag", [])
        if not bag:
            return await interaction.response.send_message("🎒 Giỏ quặng của bạn đang trống!", ephemeral=True)

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
        save_mine_fn()

        self._build_components()
        u_data = await get_user_data(self.guild_id, self.author.id)
        await interaction.response.edit_message(embed=self.build_embed(u_data.get("coins", 0)), view=self)
        bonus_msg = f" (✨ +{bonus_pct}% từ Cuốc & Hỏa Lò)" if bonus_pct > 0 else ""
        await interaction.followup.send(f"💰 Đã bán **{count}** khối quặng thu về **`+{earned:,}` coin**!{bonus_msg}", ephemeral=True)

    async def _goto_mining_museum(self, interaction: discord.Interaction):
        from Command.command_mining import MiningMuseumView
        v = MiningMuseumView(owner=self.author, viewer=self.author, guild_id=self.guild_id)
        await interaction.response.edit_message(embed=v.build_embed(), view=v)

    async def _open_mining_zone_view(self, interaction: discord.Interaction):
        from Command.command_mining import get_user_mining, MiningZoneSelectView
        u_mine = get_user_mining(self.author.id)
        u_data = await get_user_data(self.guild_id, self.author.id)
        v = MiningZoneSelectView(self.author, u_mine.get("zone", "hang_dat"), int(u_data.get("level", 0)))
        await interaction.response.send_message("📍 **BẢNG CHỌN MỎ KHOÁNG SẢN:**", view=v, ephemeral=True)

    async def _goto_mining_shop(self, interaction: discord.Interaction):
        shop_view = FishingShopView(self.author, self.guild_id)
        shop_view.selected_category = "pick"
        shop_view.current_page = 0
        shop_view._refresh_components()
        u_data = await get_user_data(self.guild_id, self.author.id)
        await interaction.response.edit_message(embed=shop_view.build_embed(u_data.get("coins", 0), int(u_data.get("xu", 0))), view=shop_view)

    async def _goto_pick_forge(self, interaction: discord.Interaction):
        self.inv_page = 3
        self.enhance_target = "pick"
        self._build_components()
        u_data = await get_user_data(self.guild_id, self.author.id)
        await interaction.response.edit_message(embed=self.build_embed(u_data.get("coins", 0), int(u_data.get("xu", 0))), view=self)

    async def _expand_bag(self, interaction: discord.Interaction):
        u_fish = get_user_fishing(self.author.id)
        purchased = u_fish.setdefault("purchased_bags", [])

        next_bag = None
        for b_id, b_info in BAGS_UPGRADES.items():
            if b_id not in purchased:
                next_bag = (b_id, b_info)
                break

        if not next_bag:
            return await interaction.response.send_message("👑 Bạn đã mở rộng toàn bộ các cấp túi cá tối đa!", ephemeral=True)

        b_id, b_info = next_bag
        cost = b_info["price"]
        is_xu = (b_info.get("currency") == "xu")
        curr_label = "xu" if is_xu else "coin"
        curr_icon = "💎" if is_xu else "🪙"
        u_data = await get_user_data(self.guild_id, self.author.id)
        wallet = int(u_data.get("xu", 0)) if is_xu else u_data.get("coins", 0)

        if wallet < cost:
            return await interaction.response.send_message(f"❌ Bạn không đủ tiền nâng cấp! Cần **{curr_icon} `{cost:,}` {curr_label}**.", ephemeral=True)

        if is_xu:
            await update_user_xu(self.guild_id, self.author.id, -cost)
        else:
            await update_user_coins(self.guild_id, self.author.id, -cost)
        purchased.append(b_id)
        u_fish["max_bag"] = u_fish.get("max_bag", 30) + b_info["extra_slots"]
        save_fishing_data()

        self._build_components()
        new_data = await get_user_data(self.guild_id, self.author.id)
        await interaction.response.edit_message(embed=self.build_embed(new_data.get("coins", 0)), view=self)
        await interaction.followup.send(f"🎉 Mua thành công **{b_info['name']}**! Sức chứa tăng lên **{u_fish['max_bag']:,} ô**.", ephemeral=True)

    async def _open_transfer_modal(self, interaction: discord.Interaction):
        modal = TransferCoinModal(self.author)
        await interaction.response.send_modal(modal)

    async def _goto_bag_detail(self, interaction: discord.Interaction):
        bag_view = FishBagDetailView(self.author, self.guild_id)
        await interaction.response.edit_message(embed=bag_view.build_embed(), view=bag_view)

    async def _goto_cook(self, interaction: discord.Interaction):
        cook_view = CookingView(self.author, self.guild_id)
        await interaction.response.edit_message(embed=cook_view.build_embed(), view=cook_view)

    async def _goto_dex(self, interaction: discord.Interaction):
        dex_view = FishdexView(self.author, self.guild_id)
        await interaction.response.edit_message(embed=dex_view.build_embed(), view=dex_view)

    async def _goto_aqua(self, interaction: discord.Interaction):
        aqua_view = AquariumView(self.author, self.author, self.guild_id)
        await interaction.response.edit_message(embed=aqua_view.build_embed(), view=aqua_view)

    async def _open_zone_view(self, interaction: discord.Interaction):
        u_fish = get_user_fishing(self.author.id)
        u_data = await get_user_data(self.guild_id, self.author.id)
        cur_z = u_fish.get("zone", "ven_bo")
        v = FishingZoneSelectView(self.author, cur_z, int(u_data.get("level", 0)), inv_parent=self)
        await interaction.response.send_message(embed=v.build_embed(), view=v, ephemeral=True)




class FishingZoneSelectView(discord.ui.View):
    def __init__(self, author: discord.Member, current_zone_id: str, user_level: int, inv_parent: Optional["FishingInventoryView"] = None):
        super().__init__(timeout=120)
        self.author = author
        self.current_zone_id = current_zone_id
        self.user_level = user_level
        self.inv_parent = inv_parent
        self._build_components()

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id != self.author.id:
            await interaction.response.send_message("❌ Đây không phải giao diện của bạn!", ephemeral=True)
            return False
        return True

    def _build_components(self):
        self.clear_items()
        options = []
        for zid, zdata in FISHING_ZONES.items():
            is_current = (zid == self.current_zone_id)
            is_locked = (self.user_level < zdata["min_level"])
            lock_str = f" [🔒 Lv.{zdata['min_level']}]" if is_locked else ""
            options.append(
                discord.SelectOption(
                    label=f"{zdata['name']}{lock_str}"[:100],
                    value=zid,
                    description=f"+{zdata['luck_bonus']} Luck | +{int(zdata['mutation_rate_bonus']*100)}% Đột biến"[:100],
                    emoji=zdata.get("icon", "📍"),
                    default=is_current
                )
            )
        sel = discord.ui.Select(placeholder="📍 Chọn vùng câu cá muốn di chuyển tới...", options=options, row=0)
        sel.callback = self._select_zone_cb
        self.add_item(sel)

    def build_embed(self) -> discord.Embed:
        cur_z = FISHING_ZONES.get(self.current_zone_id, FISHING_ZONES["ven_bo"])
        embed = discord.Embed(
            title="🗺️ BẢN ĐỒ KHU VỰC CÂU CÁ ĐẠI DƯƠNG",
            description=f"Cần thủ: **{self.author.display_name}** • Cấp độ: **Level {self.user_level}**\n📍 Đang thả neo tại: **{cur_z['name']}**\n\n*Hãy chọn vùng câu từ Menu bên dưới để di chuyển thuyền:*",
            color=discord.Color.teal()
        )
        for zid, z in FISHING_ZONES.items():
            is_cur = " 📍 *(Hiện tại)*" if zid == self.current_zone_id else ""
            status = "🟢 Đã mở khóa" if self.user_level >= z["min_level"] else f"🔒 Yêu cầu Level {z['min_level']}"
            safe_add_field(
                embed,
                name=f"{z['name']}{is_cur}",
                value=f"{z['desc']}\n• 🍀 May mắn: `+{z['luck_bonus']}` • 🧬 Tỷ lệ đột biến: `+{int(z['mutation_rate_bonus']*100)}%`\n• Trạng thái: **{status}**",
                inline=False
            )
        return embed

    async def _select_zone_cb(self, interaction: discord.Interaction):
        zid = interaction.data["values"][0]
        zdata = FISHING_ZONES.get(zid)
        if not zdata:
            return await interaction.response.send_message("❌ Vùng câu không hợp lệ!", ephemeral=True)
        if self.user_level < zdata["min_level"]:
            return await interaction.response.send_message(f"🔒 Bạn chưa đủ cấp độ! Vùng **{zdata['name']}** yêu cầu **Level {zdata['min_level']}** trở lên.", ephemeral=True)

        u_fish = get_user_fishing(self.author.id)
        u_fish["zone"] = zid
        save_fishing_data()
        self.current_zone_id = zid
        self._build_components()

        if self.inv_parent:
            self.inv_parent._build_components()

        await interaction.response.edit_message(embed=self.build_embed(), view=self)
        await interaction.followup.send(f"⛵ Thuyền câu đã cập bến **{zdata['name']}** thành công!", ephemeral=True)


class FishingShopView(discord.ui.View):
    def __init__(self, author: discord.Member, guild_id: int):
        super().__init__(timeout=180)
        self.author = author
        self.guild_id = guild_id
        self.selected_category = "all"
        self.current_page = 0
        self.items_per_page = 5
        self._refresh_components()

    def _get_filtered_items(self):
        items = [it for it in MASTER_SHOP_ITEMS if not it.get("is_hidden", False)]
        if self.selected_category != "all":
            items = [it for it in items if it.get("category") == self.selected_category]
        return items

    @property
    def total_pages(self):
        items = self._get_filtered_items()
        return max(1, math.ceil(len(items) / self.items_per_page))

    def _get_page_items(self):
        items = self._get_filtered_items()
        start = self.current_page * self.items_per_page
        return items[start:start + self.items_per_page]

    def _refresh_components(self):
        self.clear_items()

        vi = is_vietnamese(self.guild_id)
        if vi:
            cat_options = [
                discord.SelectOption(label="🌟 Tất Cả Vật Phẩm", value="all", description="Xem toàn bộ đồ trong cửa hàng", default=(self.selected_category == "all")),
                discord.SelectOption(label="🎣 Cần Câu Cá", value="rod", description="Cần câu các cấp độ và độ bền", emoji="🎣", default=(self.selected_category == "rod")),
                discord.SelectOption(label="🪱 Mồi Câu", value="bait", description="Mồi câu tăng may mắn", emoji="🪱", default=(self.selected_category == "bait")),
                discord.SelectOption(label="⛏️ Cuốc Đào Khoáng", value="pick", description="Cuốc đào các cấp độ từ Gỗ đến Vũ Trụ", emoji="⛏️", default=(self.selected_category == "pick")),
                discord.SelectOption(label="🧨 Vật Tư Hầm Mỏ", value="mine_supply", description="Thuốc nổ TNT, lồng đèn may mắn, nhiên liệu", emoji="🧨", default=(self.selected_category == "mine_supply")),
                discord.SelectOption(label="🌱 Hạt Giống Hoa Màu", value="seed", description="16 loại hạt giống hoa, rau củ, quả ngọt", emoji="🌱", default=(self.selected_category == "seed")),
                discord.SelectOption(label="🌾 Nông Trại & Phân Bón", value="farm_tool", description="Phân bón, bình tưới, lồng kính, bùa thời tiết", emoji="🌾", default=(self.selected_category == "farm_tool")),
                discord.SelectOption(label="🎒 Túi Chứa Cá", value="bag", description="Nâng cấp sức chứa giỏ cá", emoji="🎒", default=(self.selected_category == "bag")),
                discord.SelectOption(label="🐾 Thú Cưng Pet", value="pet", description="Pet đồng hành buff may mắn & giá", emoji="🐾", default=(self.selected_category == "pet")),
                discord.SelectOption(label="🃏 Đồ Chơi, Đá Đập & Troll", value="item", description="Đá End, Đá Enchant, Bụi sao, Ngọc trai, Bùa", emoji="🃏", default=(self.selected_category == "item")),
            ]
            ph = "📂 Phân loại danh mục cửa hàng..."
            prev_lbl = "◀ Trước"
            next_lbl = "Sau ▶"
            page_lbl = f"Trang {self.current_page + 1}/{self.total_pages}"
            close_lbl = "Đóng"
        else:
            cat_options = [
                discord.SelectOption(label="🌟 All Items", value="all", description="View all items in the store", default=(self.selected_category == "all")),
                discord.SelectOption(label="🎣 Fishing Rods", value="rod", description="Fishing rods of various tiers & durability", emoji="🎣", default=(self.selected_category == "rod")),
                discord.SelectOption(label="🪱 Baits", value="bait", description="Baits granting extra luck", emoji="🪱", default=(self.selected_category == "bait")),
                discord.SelectOption(label="⛏️ Mining Pickaxes", value="pick", description="Pickaxes ranging from Wood to Cosmic", emoji="⛏️", default=(self.selected_category == "pick")),
                discord.SelectOption(label="🧨 Mine Supplies", value="mine_supply", description="TNT explosives, miner lanterns, fuels", emoji="🧨", default=(self.selected_category == "mine_supply")),
                discord.SelectOption(label="🌱 Crop Seeds", value="seed", description="16 varieties of flower, crop & vegetable seeds", emoji="🌱", default=(self.selected_category == "seed")),
                discord.SelectOption(label="🌾 Farm Tools & Fertilizers", value="farm_tool", description="Fertilizers, watering cans, greenhouse glass", emoji="🌾", default=(self.selected_category == "farm_tool")),
                discord.SelectOption(label="🎒 Fish Bag", value="bag", description="Expand fish bag capacity", emoji="🎒", default=(self.selected_category == "bag")),
                discord.SelectOption(label="🐾 Companion Pets", value="pet", description="Pets boosting luck and sale prices", emoji="🐾", default=(self.selected_category == "pet")),
                discord.SelectOption(label="🃏 Upgrades & Enhancements", value="item", description="End Stones, Enchant Stones, Stardust, Talismans", emoji="🃏", default=(self.selected_category == "item")),
            ]
            ph = "📂 Filter shop category..."
            prev_lbl = "◀ Prev"
            next_lbl = "Next ▶"
            page_lbl = f"Page {self.current_page + 1}/{self.total_pages}"
            close_lbl = "Close"

        cat_select = discord.ui.Select(
            placeholder=ph,
            options=cat_options,
            row=0,
            custom_id="shop_cat_select"
        )
        cat_select.callback = self._on_select_category
        self.add_item(cat_select)

        page_items = self._get_page_items()
        for idx, item in enumerate(page_items):
            btn = discord.ui.Button(
                label=f"[{idx + 1}]",
                style=discord.ButtonStyle.primary,
                custom_id=f"shop_buy_{item['id']}",
                row=1
            )
            btn.callback = self._create_buy_callback(item)
            self.add_item(btn)

        prev_btn = discord.ui.Button(label=prev_lbl, style=discord.ButtonStyle.secondary, disabled=(self.current_page == 0), row=2)
        prev_btn.callback = self._prev_page
        self.add_item(prev_btn)

        page_ind = discord.ui.Button(label=page_lbl, style=discord.ButtonStyle.secondary, disabled=True, row=2)
        self.add_item(page_ind)

        next_btn = discord.ui.Button(label=next_lbl, style=discord.ButtonStyle.secondary, disabled=(self.current_page >= self.total_pages - 1), row=2)
        next_btn.callback = self._next_page
        self.add_item(next_btn)

        close_btn = discord.ui.Button(label=close_lbl, style=discord.ButtonStyle.danger, emoji="✖️", row=2)
        close_btn.callback = self._close_shop
        self.add_item(close_btn)

    async def _on_select_category(self, interaction: discord.Interaction):
        self.selected_category = interaction.data["values"][0]
        self.current_page = 0
        self._refresh_components()
        u_data = await get_user_data(self.guild_id, self.author.id)
        await interaction.response.edit_message(embed=self.build_embed(u_data.get("coins", 0), int(u_data.get("xu", 0))), view=self)

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id != self.author.id:
            await interaction.response.send_message("❌ Bạn không thể thao tác trên cửa hàng của người khác!", ephemeral=True)
            return False
        return True

    def build_embed(self, user_coins: int, user_xu: int = 0) -> discord.Embed:
        page_items = self._get_page_items()
        cat_titles = {
            "all": "TẤT CẢ VẬT PHẨM",
            "rod": "🎣 KHU CẦN CÂU CÁ",
            "bait": "🪱 KHU MỒI CÂU CHUYÊN DỤNG",
            "pick": "⛏️ KHU CUỐC ĐÀO KHOÁNG SẢN",
            "mine_supply": "🧨 KHU VẬT TƯ & THUỐC NỔ HẦM MỎ",
            "seed": "🌱 KHU HẠT GIỐNG HOA MÀU & NÔNG SẢN",
            "farm_tool": "🌾 KHU PHÂN BÓN & DỤNG CỤ NÔNG TRẠI",
            "bag": "🎒 KHU NÂNG CẤP TÚI CHỨA",
            "pet": "🐾 KHU THÚ CƯNG ĐỒNG HÀNH",
            "item": "🃏 KHU VẬT PHẨM, ĐÁ ENCHANT & ĐỒ CHƠI"
        }
        title_str = f"🏪 CỬA HÀNG ĐẠI DƯƠNG & HẦM MỎ: {cat_titles.get(self.selected_category, 'VẬT PHẨM')}"
        
        embed = discord.Embed(
            title=title_str,
            description=f"💰 Số dư ví: **`{user_coins:,}` coin** | 💎 **`{user_xu:,}` xu**\n*Dùng Menu phía trên để lọc phân loại, bấm `[1]` đến `[5]` để mua!*",
            color=discord.Color.gold()
        )

        if not page_items:
            embed.description += "\n\n*(Danh mục này hiện chưa có vật phẩm nào được bày bán)*"
        else:
            for idx, it in enumerate(page_items, start=1):
                cat = it["category"]
                curr_str = "xu" if it.get("currency") == "xu" else "coin"
                curr_icon = "💎" if it.get("currency") == "xu" else "🪙"
                price_str = f"**{curr_icon} `{it['price']:,}` {curr_str}**"
                details = ""
                if cat == "rod":
                    details = f"Cấp: `Lv.{it.get('level', 1)}` | May mắn: `+{it.get('luck', 0)}` | Độ bền: `{it.get('durability', 100)}`"
                elif cat == "pick":
                    details = f"Cấp: `Lv.{it.get('level', 1)}` | May mắn: `+{it.get('luck', 0)}` | Độ bền: `{it.get('durability', 100)}`"
                elif cat == "mine_supply":
                    details = it.get("desc", "Vật tư phụ trợ khai thác mỏ")
                elif cat == "bait":
                    details = f"May mắn: `+{it.get('luck', 0)}` khi câu"
                elif cat == "bag":
                    details = f"Mở rộng thêm: `+{it.get('extra_slots', 0):,} ô` chứa cá"
                elif cat == "pet":
                    details = f"Buff may mắn: `+{it.get('luck_bonus', 0)}%` | Buff mồi: `+{it.get('bait_bonus', 0)}%` | Giá bán: `x{it.get('price_multi', 1.0)}`"
                elif cat in ("seed", "farm_tool", "fertilizer"):
                    details = it.get("desc", "Vật phẩm nông nghiệp")
                elif cat == "item":
                    details = it.get("desc", "Vật phẩm chức năng")

                hsd_text = f" | ⏳ HSD: {it['duration_days']} ngày" if it.get("has_expiry") else ""
                safe_add_field(
                    embed,
                    name=f"**[{idx}] {it['name']}** — {price_str}",
                    value=f"└ {details}{hsd_text}",
                    inline=False
                )

        embed.set_footer(text=f"Trang {self.current_page + 1}/{self.total_pages} • Danh mục: {self.selected_category.upper()} • Sakura Fishing")
        return embed

    def _create_buy_callback(self, item: dict):
        async def callback(interaction: discord.Interaction):
            modal = ShopQuantityModal(item, self)
            await interaction.response.send_modal(modal)

        return callback

    async def _prev_page(self, interaction: discord.Interaction):
        if self.current_page > 0:
            self.current_page -= 1
            self._refresh_components()
            u_data = await get_user_data(self.guild_id, self.author.id)
            await interaction.response.edit_message(embed=self.build_embed(u_data.get("coins", 0), int(u_data.get("xu", 0))), view=self)

    async def _next_page(self, interaction: discord.Interaction):
        if self.current_page < self.total_pages - 1:
            self.current_page += 1
            self._refresh_components()
            u_data = await get_user_data(self.guild_id, self.author.id)
            await interaction.response.edit_message(embed=self.build_embed(u_data.get("coins", 0), int(u_data.get("xu", 0))), view=self)

    async def _close_shop(self, interaction: discord.Interaction):
        for child in self.children:
            child.disabled = True
        await interaction.response.edit_message(content="🚪 Đã đóng cửa hàng.", view=self)
        self.stop()


class TransferCoinModal(discord.ui.Modal, title="💸 Chuyển Coin Cho Thành Viên"):
    target_input = discord.ui.TextInput(label="ID hoặc @Mention người nhận", placeholder="Ví dụ: 123456789012345678", required=True, max_length=30)
    amount_input = discord.ui.TextInput(label="Số coin muốn chuyển", placeholder="Ví dụ: 50000", required=True, max_length=15)

    def __init__(self, author: discord.Member):
        super().__init__()
        self.author = author

    async def on_submit(self, interaction: discord.Interaction):
        raw_id = self.target_input.value.strip().replace("<@", "").replace(">", "").replace("!", "")
        raw_amt = self.amount_input.value.strip().replace(",", "")
        if not raw_id.isdigit() or not raw_amt.isdigit() or int(raw_amt) <= 0:
            return await interaction.response.send_message("❌ ID hoặc số coin không hợp lệ!", ephemeral=True)

        amount = int(raw_amt)
        target = interaction.guild.get_member(int(raw_id))
        if not target or target.bot:
            return await interaction.response.send_message("❌ Không tìm thấy thành viên hợp lệ!", ephemeral=True)
        if target.id == self.author.id:
            return await interaction.response.send_message("❌ Không thể tự chuyển cho chính mình!", ephemeral=True)

        u_data = await get_user_data(interaction.guild.id, self.author.id)
        if u_data.get("coins", 0) < amount:
            return await interaction.response.send_message(f"❌ Không đủ coin! Số dư: `{u_data.get('coins', 0):,}`.", ephemeral=True)

        await update_user_coins(interaction.guild.id, self.author.id, -amount)
        await update_user_coins(interaction.guild.id, target.id, amount)
        await interaction.response.send_message(f"💸 {self.author.mention} đã chuyển **`{amount:,}` coin** cho {target.mention}!")


class QTEPullView(discord.ui.View):
    def __init__(self, author: discord.Member, target_dir: str, guild_id: Optional[int] = None):
        super().__init__(timeout=4.5)
        self.author = author
        self.target_dir = target_dir
        self.guild_id = guild_id or (author.guild.id if getattr(author, 'guild', None) else 0)
        self.vi = is_vietnamese(self.guild_id)
        self.success = False
        labels = (("Kéo Trái", "left", "⬅️"), ("Ghìm Cước", "up", "⬆️"), ("Kéo Phải", "right", "➡️")) if self.vi else (("Reel Left", "left", "⬅️"), ("Hold Steady", "up", "⬆️"), ("Reel Right", "right", "➡️"))
        for label, key, emoji in labels:
            btn = discord.ui.Button(label=label, emoji=emoji, style=discord.ButtonStyle.primary)
            btn.callback = self._make_callback(key)
            self.add_item(btn)

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id != self.author.id:
            msg = "❌ Đây không phải cần câu của bạn!" if self.vi else "❌ This is not your fishing rod!"
            await interaction.response.send_message(msg, ephemeral=True)
            return False
        return True

    def _make_callback(self, key: str):
        async def callback(interaction: discord.Interaction):
            self.success = (key == self.target_dir)
            for child in self.children:
                child.disabled = True
            if self.vi:
                res = "✅ **KÉO THÀNH CÔNG!** Đang thu cá..." if self.success else "💥 Sai hướng rồi!"
            else:
                res = "✅ **REEL IN SUCCESSFUL!** Pulling the catch..." if self.success else "💥 Wrong direction! The fish got away!"
            await interaction.response.edit_message(content=res, view=self)
            self.stop()
        return callback


def _load_font(size: int, bold: bool = False):
    names = (["DejaVuSans-Bold.ttf", "arialbd.ttf"] if bold else ["DejaVuSans.ttf", "arial.ttf"])
    for base in ("", "/usr/share/fonts/truetype/dejavu/", "C:/Windows/Fonts/"):
        for n in names:
            try:
                return ImageFont.truetype(base + n, size)
            except Exception:
                continue
    return ImageFont.load_default()


def _strip_emoji(text: str) -> str:
    return "".join(c for c in str(text) if ord(c) < 0x2000 or 0x1E00 <= ord(c) <= 0x1EFF).strip() or "—"


def _generate_license_card_sync(avatar_bytes: bytes, name: str, rod_name: str, pet_name: str,
                                total_caught: int, dex_count: int, biggest_str: str) -> io.BytesIO:
    W, H = 800, 450
    img = Image.new("RGB", (W, H), (12, 38, 66))
    d = ImageDraw.Draw(img)
    for y in range(H):
        k = y / H
        d.line([(0, y), (W, y)], fill=(int(12 + 20 * k), int(38 + 60 * k), int(66 + 70 * k)))
    d.rounded_rectangle((15, 15, W - 15, H - 15), radius=24, outline=(255, 215, 0), width=4)

    d.text((40, 32), "CĂN CƯỚC CẦN THỦ", font=_load_font(34, True), fill=(255, 215, 0))
    d.text((40, 78), "SAKURA FISHING ASSOCIATION", font=_load_font(16), fill=(170, 210, 240))

    try:
        av = Image.open(io.BytesIO(avatar_bytes)).convert("RGBA").resize((150, 150))
        mask = Image.new("L", (150, 150), 0)
        ImageDraw.Draw(mask).ellipse((0, 0, 150, 150), fill=255)
        img.paste(av, (45, 130), mask)
    except Exception:
        d.ellipse((45, 130, 195, 280), outline=(255, 255, 255), width=3)
    d.ellipse((43, 128, 197, 282), outline=(255, 215, 0), width=4)

    d.text((230, 125), _strip_emoji(name)[:22], font=_load_font(30, True), fill=(255, 255, 255))
    rows = [
        ("Cần câu", _strip_emoji(rod_name)[:30]),
        ("Thú cưng", _strip_emoji(pet_name)[:30]),
        ("Tổng cá câu được", f"{total_caught:,}"),
        ("Sổ sưu tầm", f"{dex_count} loài"),
        ("Kỷ lục", _strip_emoji(biggest_str)[:34]),
    ]
    y = 180
    for k, v in rows:
        d.text((230, y), f"{k}:", font=_load_font(20), fill=(150, 200, 235))
        d.text((430, y), v, font=_load_font(20, True), fill=(255, 255, 255))
        y += 42

    buf = io.BytesIO()
    img.save(buf, "PNG")
    buf.seek(0)
    return buf


class FishBagDetailView(discord.ui.View):
    PER_PAGE = 10

    def __init__(self, author: discord.Member, guild_id: int):
        super().__init__(timeout=240)
        self.author = author
        self.guild_id = guild_id
        self.page = 0
        self.selected: set = set()
        self._refresh_components()

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id != self.author.id:
            await interaction.response.send_message("❌ Đây không phải giỏ cá của bạn!", ephemeral=True)
            return False
        return True

    def _bag(self):
        return get_user_fishing(self.author.id).setdefault("fish_bag", [])

    def _total_pages(self) -> int:
        return max(1, math.ceil(len(self._bag()) / self.PER_PAGE))

    def _refresh_components(self):
        self.clear_items()
        bag = self._bag()
        self.page = max(0, min(self.page, self._total_pages() - 1))
        start = self.page * self.PER_PAGE
        chunk = bag[start:start + self.PER_PAGE]

        if chunk:
            options = []
            for i, f in enumerate(chunk):
                gi = start + i
                mut = f" [{f['mutation']}]" if f.get("mutation") else ""
                options.append(discord.SelectOption(
                    label=f"#{gi + 1} {f['name']}{mut}"[:100], value=str(gi),
                    description=f"{f.get('weight', 0)}kg • {f.get('price', 0):,}c"[:100],
                    default=(gi in self.selected),
                ))
            sel = discord.ui.Select(placeholder="Chọn cá muốn bán (có thể chọn nhiều)...", options=options,
                                    min_values=0, max_values=len(options), row=0)
            sel.callback = self._on_select
            self.add_item(sel)

        sell_btn = discord.ui.Button(label=f"Bán Đã Chọn ({len(self.selected)})", style=discord.ButtonStyle.success, emoji="💰", row=1, disabled=not self.selected)
        sell_btn.callback = self._sell_selected
        self.add_item(sell_btn)

        prev_btn = discord.ui.Button(label="◀", style=discord.ButtonStyle.secondary, row=1, disabled=(self.page == 0))
        prev_btn.callback = self._prev
        self.add_item(prev_btn)
        ind = discord.ui.Button(label=f"{self.page + 1}/{self._total_pages()}", style=discord.ButtonStyle.secondary, row=1, disabled=True)
        self.add_item(ind)
        next_btn = discord.ui.Button(label="▶", style=discord.ButtonStyle.secondary, row=1, disabled=(self.page >= self._total_pages() - 1))
        next_btn.callback = self._next
        self.add_item(next_btn)

        back_btn = discord.ui.Button(label="Về Túi Đồ", style=discord.ButtonStyle.primary, emoji="🎒", row=2)
        back_btn.callback = self._back
        self.add_item(back_btn)

    def build_embed(self) -> discord.Embed:
        u_fish = get_user_fishing(self.author.id)
        bag = self._bag()
        start = self.page * self.PER_PAGE
        embed = discord.Embed(
            title=f"🐟 GIỎ CÁ: {self.author.display_name.upper()}",
            description=f"Sức chứa: **`{len(bag)}/{u_fish.get('max_bag', 30)}`** • Tổng giá trị: **`{sum(f.get('price', 0) for f in bag):,}` coin**",
            color=discord.Color.teal(),
        )
        lines = []
        for i, f in enumerate(bag[start:start + self.PER_PAGE], start=start + 1):
            mut = f" [{f['mutation']}]" if f.get("mutation") else ""
            icon = RARITY_ICONS.get(f.get("rarity", "common"), "🐟")
            lines.append(f"`#{i}` {icon} **{f['name']}**{mut} — `{f.get('weight', 0)}kg` • `{f.get('price', 0):,}`c")
        safe_add_field(embed, name=f"Trang {self.page + 1}/{self._total_pages()}", value="\n".join(lines) if lines else "*Giỏ trống.*", inline=False)
        return embed

    async def _redraw(self, interaction: discord.Interaction):
        self._refresh_components()
        await interaction.response.edit_message(embed=self.build_embed(), view=self)

    async def _on_select(self, interaction: discord.Interaction):
        start = self.page * self.PER_PAGE
        page_idx = set(range(start, start + self.PER_PAGE))
        self.selected = (self.selected - page_idx) | {int(v) for v in interaction.data.get("values", [])}
        await self._redraw(interaction)

    async def _prev(self, interaction: discord.Interaction):
        self.page -= 1
        await self._redraw(interaction)

    async def _next(self, interaction: discord.Interaction):
        self.page += 1
        await self._redraw(interaction)

    async def _sell_selected(self, interaction: discord.Interaction):
        u_fish = get_user_fishing(self.author.id)
        bag = u_fish.setdefault("fish_bag", [])
        idxs = sorted((i for i in self.selected if i < len(bag)), reverse=True)
        if not idxs:
            self.selected.clear()
            return await self._redraw(interaction)
        earned = 0
        for i in idxs:
            earned += bag.pop(i).get("price", 0)
        count = len(idxs)
        self.selected.clear()

        equipped_rod_id = u_fish.get("equipped_rod")
        cur_rod = u_fish.get("rods", {}).get(equipped_rod_id, {}) if equipped_rod_id else {}
        ench_stats = get_rod_enchant_stats(cur_rod)
        bonus_pct = ench_stats.get("sell_bonus", 0)
        buffs = u_fish.get("buffs", {})
        now_ts = time.time()
        if buffs.get("golden_scale_price", 0) > now_ts:
            bonus_pct += 50
        if bonus_pct > 0:
            earned = int(earned * (1.0 + bonus_pct / 100.0))
        if buffs.get("double_coins_buff", 0) > now_ts:
            earned = int(earned * 2.0)

        u_fish["stats"]["total_earned"] = u_fish["stats"].get("total_earned", 0) + earned
        await update_user_coins(self.guild_id, self.author.id, earned)
        save_fishing_data()
        await self._redraw(interaction)
        await interaction.followup.send(f"💰 Đã bán **{count}** con cá, thu về **`+{earned:,}` coin**!", ephemeral=True)

    async def _back(self, interaction: discord.Interaction):
        inv = FishingInventoryView(self.author, self.guild_id)
        u_data = await get_user_data(self.guild_id, self.author.id)
        await interaction.response.edit_message(embed=inv.build_embed(u_data.get("coins", 0)), view=inv)


COOK_RECIPES = {
    "cook_soup_s": {"name": "🍲 Canh Cá May Mắn", "buff": "soup_luck", "dur": 1800, "need": ("common", 3), "desc": "+30 May Mắn / 30 phút"},
    "cook_soup_l": {"name": "🍜 Lẩu Hải Sản Thượng Hạng", "buff": "soup_luck", "dur": 3600, "need": ("rare", 2), "desc": "+30 May Mắn / 60 phút"},
    "cook_bento_s": {"name": "🍱 Cơm Hộp Cá Nướng", "buff": "bento_price", "dur": 1800, "need": ("common", 4), "desc": "+20% giá bán cá / 30 phút"},
    "cook_bento_l": {"name": "🍣 Sushi Hoàng Gia", "buff": "bento_price", "dur": 3600, "need": ("rare", 3), "desc": "+20% giá bán cá / 60 phút"},
    "cook_fast_s": {"name": "🍤 Tôm Chiên Giòn", "buff": "fast_cast", "dur": 1800, "need": ("common", 2), "desc": "Hồi chiêu thả câu 5s / 30 phút"},
    "cook_fast_l": {"name": "🦀 Cua Hấp Tốc Độ", "buff": "fast_cast", "dur": 3600, "need": ("epic", 1), "desc": "Hồi chiêu thả câu 5s / 60 phút"},
    "cook_qte_s": {"name": "🐙 Bạch Tuộc Nướng", "buff": "auto_qte", "dur": 1800, "need": ("rare", 2), "desc": "Tự động kéo cá boss / 30 phút"},
    "cook_qte_l": {"name": "🦞 Tôm Hùm Nướng Bơ", "buff": "auto_qte", "dur": 3600, "need": ("legendary", 1), "desc": "Tự động kéo cá boss / 60 phút"},
    "cook_chest": {"name": "🍤 Gỏi Cá Thần Tài", "buff": "chest_buff", "dur": 1800, "need": ("epic", 2), "desc": "+3% tỷ lệ vớt rương / 30 phút"},
}
BUFF_LABELS = {"soup_luck": "🍲 May mắn", "bento_price": "🍱 Giá bán", "fast_cast": "⚡ Thả nhanh", "auto_qte": "🤖 Auto QTE", "chest_buff": "📦 Vớt rương"}


BUFF_LABELS.update({
    "curry_luck_exp": "🍛 Cà ri cá (+80 Luck & x1.5 Exp)",
    "unbreakable_rod_buff": "🛡️ Súp cà chua cá (Bất hoại độ bền)",
    "refine_luck_buff": "🥧 Bánh dâu (+20% Tỉ lệ đập đồ/sao)",
    "royal_feast_buff": "👑 Yến tiệc (+120 Luck, x2 Coin, Auto)",
    "farm_speed_buff": "🍧 Đá bào dưa hấu (x2 Tốc độ lớn cây)",
})


class CookingView(discord.ui.View):
    def __init__(self, author: discord.Member, guild_id: int):
        super().__init__(timeout=240)
        self.author = author
        self.guild_id = guild_id
        self.menu_mode = "farm"
        self._refresh_components()

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id != self.author.id:
            await interaction.response.send_message("❌ Đây không phải bếp của bạn!", ephemeral=True)
            return False
        return True

    def _refresh_components(self):
        self.clear_items()

        if self.menu_mode == "farm":
            options = []
            for rid, r in FARM_COOK_RECIPES.items():
                req_parts = []
                if r.get("req_fish"):
                    req_parts.append(f"{r['req_fish'][1]}x cá {r['req_fish'][0]}")
                for cid, cnt in r.get("req_crops", {}).items():
                    c_name = SEEDS_CATALOG.get(cid, {}).get("name", cid)
                    req_parts.append(f"{cnt}x {c_name}")
                desc_str = f"Cần: {', '.join(req_parts)} ➜ {r['desc']}"
                options.append(
                    discord.SelectOption(
                        label=r["name"][:100],
                        value=rid,
                        emoji="🍲",
                        description=desc_str[:100]
                    )
                )
            sel = discord.ui.Select(placeholder="🍲 Chọn món Nông Trại & Cá kết hợp để nấu...", options=options, row=0)
            sel.callback = self._cook_farm_callback
            self.add_item(sel)
        else:
            options = [
                discord.SelectOption(
                    label=r["name"][:100], value=rid, emoji="🍳",
                    description=f"Cần {r['need'][1]} cá {r['need'][0]} • {r['desc']}"[:100],
                ) for rid, r in COOK_RECIPES.items()
            ]
            sel = discord.ui.Select(placeholder="🍳 Chọn món cá truyền thống để nấu...", options=options, row=0)
            sel.callback = self._cook_classic_callback
            self.add_item(sel)

        toggle_btn = discord.ui.Button(
            label="Chuyển sang: Món Cá Truyền Thống" if self.menu_mode == "farm" else "Chuyển sang: Món Nông Trại & Cá",
            style=discord.ButtonStyle.success if self.menu_mode == "classic" else discord.ButtonStyle.primary,
            emoji="🔄",
            row=1
        )
        toggle_btn.callback = self._toggle_menu_mode
        self.add_item(toggle_btn)

        aqua_btn = discord.ui.Button(label="Thủy Cung", style=discord.ButtonStyle.secondary, emoji="🏛️", row=1)
        aqua_btn.callback = self._goto_aqua
        self.add_item(aqua_btn)

        inv_btn = discord.ui.Button(label="Về Túi Đồ", style=discord.ButtonStyle.primary, emoji="🎒", row=1)
        inv_btn.callback = self._goto_inv
        self.add_item(inv_btn)

    def build_embed(self) -> discord.Embed:
        u_fish = get_user_fishing(self.author.id)
        buffs = u_fish.get("buffs", {})
        now = time.time()
        active = [f"• {BUFF_LABELS.get(k, k)}: còn `{int((buffs[k] - now) // 60)}` phút" for k in list(buffs.keys()) if isinstance(buffs.get(k), (int, float)) and buffs[k] > now and k in BUFF_LABELS]

        title = "🍳 BẾP NẤU ĂN: HOA MÀU & THỦY TRIỀU" if self.menu_mode == "farm" else "🍳 BẾP NẤU ĂN: HẢI SẢN TRUYỀN THỐNG"
        desc = (
            "Kết hợp **hoa màu nông sản** và **cá tươi trong giỏ** để nấu ra những món đại tiệc mang sức mạnh phi thường!"
            if self.menu_mode == "farm"
            else "Dùng các loài **cá trong giỏ** để nấu món ăn tăng may mắn và hỗ trợ kéo cá."
        )

        embed = discord.Embed(title=title, color=discord.Color.orange(), description=desc)
        safe_add_field(embed, name="🔥 Các Buff Đang Hoạt Động", value="\n".join(active) if active else "*Chưa có buff nào đang kích hoạt*", inline=False)

        if self.menu_mode == "farm":
            recipe_lines = []
            for r in FARM_COOK_RECIPES.values():
                reqs = []
                if r.get("need_fish"):
                    reqs.append(f"{r['need_fish'][1]}x cá `{r['need_fish'][0]}`")
                elif r.get("req_fish"):
                    reqs.append(f"{r['req_fish'][1]}x cá `{r['req_fish'][0]}`")
                for cid, cnt in (r.get("need_crops") or r.get("req_crops") or {}).items():
                    reqs.append(f"{cnt}x `{SEEDS_CATALOG.get(f'seed_{cid[5:]}', {}).get('name', cid)}`")
                recipe_lines.append(f"**{r['name']}**\n└ Yêu cầu: {', '.join(reqs)}\n└ Hiệu ứng: *{r['desc']}*")
            safe_add_field(embed, name="📜 Thực Đơn Nông Trại & Cá", value="\n".join(recipe_lines), inline=False)
        else:
            recipe_lines = [f"**{r['name']}** — {r['need'][1]}x cá `{r['need'][0]}` ➜ *{r['desc']}*" for r in COOK_RECIPES.values()]
            safe_add_field(embed, name="📜 Thực Đơn Hải Sản Cổ Điển", value="\n".join(recipe_lines), inline=False)

        return embed

    async def _toggle_menu_mode(self, interaction: discord.Interaction):
        self.menu_mode = "classic" if self.menu_mode == "farm" else "farm"
        self._refresh_components()
        await interaction.response.edit_message(embed=self.build_embed(), view=self)

    async def _cook_farm_callback(self, interaction: discord.Interaction):
        rid = interaction.data["values"][0]
        r = FARM_COOK_RECIPES.get(rid)
        if not r:
            return await interaction.response.send_message("❌ Món ăn không hợp lệ!", ephemeral=True)

        u_fish = get_user_fishing(self.author.id)
        bag = u_fish.setdefault("fish_bag", [])
        farm_data = u_fish.setdefault("farm", {})
        crops = farm_data.setdefault("crops", {})

        fish_to_use = []
        if r.get("req_fish"):
            rarity, f_qty = r["req_fish"]
            candidates = sorted((f for f in bag if f.get("rarity") == rarity and not f.get("mutation")), key=lambda f: f.get("price", 0))
            if len(candidates) < f_qty:
                return await interaction.response.send_message(f"❌ Bạn không đủ **{f_qty}x cá {rarity}** trong giỏ! (Hiện có: {len(candidates)})", ephemeral=True)
            fish_to_use = candidates[:f_qty]

        for cid, req_cnt in r.get("req_crops", {}).items():
            have_cnt = crops.get(cid, 0)
            c_name = SEEDS_CATALOG.get(cid, {}).get("name", cid)
            if have_cnt < req_cnt:
                return await interaction.response.send_message(f"❌ Bạn không đủ nông sản **{c_name}**! (Cần: `{req_cnt}`, hiện có: `{have_cnt}` trong kho)", ephemeral=True)

        for f in fish_to_use:
            bag.remove(f)
        for cid, req_cnt in r.get("req_crops", {}).items():
            crops[cid] -= req_cnt

        now = time.time()
        buffs = u_fish.setdefault("buffs", {})
        buffs[r["buff"]] = max(now, buffs.get(r["buff"], 0) if isinstance(buffs.get(r["buff"]), (int, float)) else 0) + r["dur"]

        extra_note = ""
        if rid == "farm_dish_tomato_soup":
            rod_id = u_fish.get("equipped_rod")
            if rod_id and rod_id in u_fish.get("rods", {}):
                cur_rod = u_fish["rods"][rod_id]
                cur_rod["durability"] = cur_rod.get("max_durability", 100)
                extra_note = " Đồng thời đã **hồi phục 100% Độ Bền Cần Câu**!"

        save_fishing_data()
        self._refresh_components()
        await interaction.response.edit_message(embed=self.build_embed(), view=self)
        await interaction.followup.send(f"🍳😋 **NẤU THÀNH CÔNG: {r['name'].upper()}!**\n└ {r['desc']}.{extra_note}", ephemeral=False)

    async def _cook_classic_callback(self, interaction: discord.Interaction):
        rid = interaction.data["values"][0]
        r = COOK_RECIPES[rid]
        rarity, qty = r["need"]
        u_fish = get_user_fishing(self.author.id)
        bag = u_fish.setdefault("fish_bag", [])
        candidates = sorted((f for f in bag if f.get("rarity") == rarity and not f.get("mutation")), key=lambda f: f.get("price", 0))
        if len(candidates) < qty:
            return await interaction.response.send_message(f"❌ Cần **{qty}** cá `{rarity}` (không đột biến), bạn chỉ có **{len(candidates)}**!", ephemeral=True)

        used = candidates[:qty]
        for f in used:
            bag.remove(f)
        buffs = u_fish.setdefault("buffs", {})
        now = time.time()
        buffs[r["buff"]] = max(now, buffs.get(r["buff"], 0) if isinstance(buffs.get(r["buff"]), (int, float)) else 0) + r["dur"]
        save_fishing_data()

        self._refresh_components()
        await interaction.response.edit_message(embed=self.build_embed(), view=self)
        await interaction.followup.send(f"🍳 Đã nấu **{r['name']}**! {r['desc']}.", ephemeral=True)

    async def _goto_aqua(self, interaction: discord.Interaction):
        v = AquariumView(self.author, self.author, self.guild_id)
        await interaction.response.edit_message(embed=v.build_embed(), view=v)

    async def _goto_inv(self, interaction: discord.Interaction):
        v = FishingInventoryView(self.author, self.guild_id)
        u_data = await get_user_data(self.guild_id, self.author.id)
        await interaction.response.edit_message(embed=v.build_embed(u_data.get("coins", 0)), view=v)


class FishdexView(discord.ui.View):
    PER_PAGE = 8

    def __init__(self, author: discord.Member, guild_id: int, category: str = "fish"):
        super().__init__(timeout=240)
        self.author = author
        self.guild_id = guild_id
        self.page = 0
        self.category = category
        self.all_fish = list(fish_list) + list(event_fish)
        self._refresh_components()

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id != self.author.id:
            await interaction.response.send_message("❌ Đây không phải sổ của bạn!", ephemeral=True)
            return False
        return True

    def _get_current_items(self) -> list:
        if self.category == "fish":
            return self.all_fish
        elif self.category == "rod":
            return [{"id": k, **v} for k, v in RODS_CATALOG.items()]
        elif self.category == "bait":
            return [{"id": k, **v} for k, v in BAITS_CATALOG.items()]
        elif self.category == "pet":
            return [{"id": k, **v} for k, v in PETS_CATALOG.items()]
        elif self.category == "chest":
            return [{"id": k, **v} for k, v in CHESTS_DATA.items()]
        elif self.category == "troll":
            return [{"id": k, **v} for k, v in UTILITY_ITEMS.items()]
        return self.all_fish

    def _total_pages(self) -> int:
        return max(1, math.ceil(len(self._get_current_items()) / self.PER_PAGE))

    def _next_milestone(self):
        u_fish = get_user_fishing(self.author.id)
        found = len(u_fish.get("fishdex", {}))
        claimed = u_fish.get("dex_claimed_milestones", [])
        for m in DEX_MILESTONES:
            if m["count"] not in claimed:
                return m, found >= m["count"]
        return None, False

    def _refresh_components(self):
        self.clear_items()

        cat_options = [
            discord.SelectOption(label="🐟 Sinh Vật Biển", value="fish", description="Các loài cá và cột mốc phần thưởng", default=(self.category == "fish")),
            discord.SelectOption(label="🎣 Cần Câu", value="rod", description="Bách khoa các loại cần câu", default=(self.category == "rod")),
            discord.SelectOption(label="🪱 Mồi Câu", value="bait", description="Bách khoa các loại mồi câu", default=(self.category == "bait")),
            discord.SelectOption(label="🐾 Thú Cưng", value="pet", description="Bách khoa thú cưng đồng hành", default=(self.category == "pet")),
            discord.SelectOption(label="📦 Rương Báu", value="chest", description="Bách khoa rương báu đại dương", default=(self.category == "chest")),
            discord.SelectOption(label="🃏 Vật Phẩm Troll", value="troll", description="Bách khoa vật phẩm troll & tiện ích", default=(self.category == "troll")),
        ]
        cat_select = discord.ui.Select(placeholder="📖 Chọn danh mục Bách Khoa...", options=cat_options, row=0)
        cat_select.callback = self._on_change_category
        self.add_item(cat_select)

        prev_btn = discord.ui.Button(label="◀", style=discord.ButtonStyle.secondary, row=1, disabled=(self.page == 0))
        prev_btn.callback = self._prev
        self.add_item(prev_btn)
        ind = discord.ui.Button(label=f"{self.page + 1}/{self._total_pages()}", style=discord.ButtonStyle.secondary, row=1, disabled=True)
        self.add_item(ind)
        next_btn = discord.ui.Button(label="▶", style=discord.ButtonStyle.secondary, row=1, disabled=(self.page >= self._total_pages() - 1))
        next_btn.callback = self._next
        self.add_item(next_btn)

        if self.category == "fish":
            m, ready = self._next_milestone()
            claim_btn = discord.ui.Button(
                label=f"Nhận Thưởng Mốc {m['count']}" if m else "Đã Nhận Hết",
                style=discord.ButtonStyle.success, emoji="🎁", row=2, disabled=not ready,
            )
            claim_btn.callback = self._claim
            self.add_item(claim_btn)

        back_btn = discord.ui.Button(label="Về Túi Đồ", style=discord.ButtonStyle.primary, emoji="🎒", row=2)
        back_btn.callback = self._back
        self.add_item(back_btn)

    async def _on_change_category(self, interaction: discord.Interaction):
        self.category = interaction.data.get("values", ["fish"])[0]
        self.page = 0
        await self._redraw(interaction)

    def build_embed(self) -> discord.Embed:
        u_fish = get_user_fishing(self.author.id)
        items = self._get_current_items()
        start = self.page * self.PER_PAGE
        page_items = items[start:start + self.PER_PAGE]

        if self.category == "fish":
            dex = u_fish.get("fishdex", {})
            m, _ = self._next_milestone()
            embed = discord.Embed(
                title=f"📖 BÁCH KHOA: SINH VẬT BIỂN — {self.author.display_name.upper()}",
                description=f"Đã phát hiện: **`{len(dex)}/{len(self.all_fish)}`** loài" + (f" • Mốc tiếp theo: **{m['count']}** loài (`+{m['reward_coin']:,}` coin + {m['bait_amount']}x {BAITS_CATALOG.get(m['reward_bait'], {}).get('name', 'Mồi')})" if m else " • 🏆 Đã nhận mọi mốc!"),
                color=discord.Color.dark_green(),
            )
            for f in page_items:
                icon = RARITY_ICONS.get(f.get("rarity", "common"), "🐟")
                d = dex.get(f.get("name"))
                hidden_tag = " • 🔮 **Ẩn**" if f.get("is_hidden") else ""
                source_tag = f" • *Nguồn: {f.get('obtain_source')}*" if f.get("obtain_source") else ""
                if d:
                    val = f"Đã câu: `{d.get('count', 0)}` • Kỷ lục: `{d.get('max_weight', 0)}kg` / `{d.get('max_length', 0)}cm`{hidden_tag}{source_tag}"
                    name = f"{icon} {f['name']}"
                else:
                    val = f"*Chưa phát hiện*{hidden_tag}{source_tag}"
                    name = f"{icon} ???"
                safe_add_field(embed, name=name, value=val, inline=False)
            return embed

        elif self.category == "rod":
            embed = discord.Embed(
                title=f"🎣 BÁCH KHOA: CẦN CÂU ĐẠI DƯƠNG ({len(items)} loại)",
                description="Danh sách toàn bộ các loại cần câu trong hệ thống đại dương.",
                color=discord.Color.blue()
            )
            for r in page_items:
                r_name = r.get("name", r.get("id"))
                rarity = str(r.get("rarity", "common")).upper()
                price = r.get("price", 0)
                curr = "Xu" if r.get("currency") == "xu" else "Coin"
                hsd = f"⏳ HSD {r.get('duration_days', 7)} ngày ({'Có thể gia hạn' if r.get('renewable') else 'Không thể gia hạn'})" if r.get("has_expiry") else "Vĩnh viễn"
                hidden = "🔮 **VẬT PHẨM ẨN**" if r.get("is_hidden") else "🛒 Bán trong Shop"
                source = f"\n*Nguồn kiếm:* {r.get('obtain_source')}" if r.get("obtain_source") else ""
                val = f"• Độ hiếm: `{rarity}` • Độ bền: `{r.get('durability', 100)}` • May mắn: `+{r.get('luck', 0)}`\n• Giá: `{price:,} {curr}` • Trạng thái: {hidden} • HSD: `{hsd}`{source}"
                safe_add_field(embed, name=r_name, value=val, inline=False)
            return embed

        elif self.category == "bait":
            embed = discord.Embed(
                title=f"🪱 BÁCH KHOA: MỒI CÂU ĐẠI DƯƠNG ({len(items)} loại)",
                description="Danh sách toàn bộ các loại mồi câu giúp thu hút cá hiếm.",
                color=discord.Color.gold()
            )
            for b in page_items:
                b_name = b.get("name", b.get("id"))
                price = b.get("price", 0)
                curr = "Xu" if b.get("currency") == "xu" else "Coin"
                hidden = "🔮 **Ẩn / Rơi từ Rương**" if b.get("is_hidden") or not b.get("buyable") else "🛒 Bán trong Shop"
                source = f"\n*Nguồn kiếm:* {b.get('obtain_source')}" if b.get("obtain_source") else ""
                val = f"• May mắn: `+{b.get('luck', 0)}` • Giá: `{price:,} {curr}` • Trạng thái: {hidden}{source}"
                safe_add_field(embed, name=b_name, value=val, inline=False)
            return embed

        elif self.category == "pet":
            embed = discord.Embed(
                title=f"🐾 BÁCH KHOA: THÚ CƯNG ĐỒNG HÀNH ({len(items)} loài)",
                description="Danh sách thú cưng đại dương buff chỉ số may mắn và giá bán cá.",
                color=discord.Color.purple()
            )
            for p in page_items:
                p_name = p.get("name", p.get("id"))
                price = p.get("price", 0)
                curr = "Xu" if p.get("currency") == "xu" else "Coin"
                hidden = "🔮 **VẬT PHẨM ẨN**" if p.get("is_hidden") else "🛒 Bán trong Shop"
                hsd = f"⏳ HSD {p.get('duration_days', 7)} ngày ({'Có thể gia hạn' if p.get('renewable') else 'Không thể gia hạn'})" if p.get("has_expiry") else "Vĩnh viễn"
                source = f"\n*Nguồn kiếm:* {p.get('obtain_source')}" if p.get("obtain_source") else ""
                val = f"• May mắn: `+{p.get('luck_bonus', 0)}` • Giá cá: `x{p.get('price_multi', 1.0)}` • Tỉ lệ rơi mồi: `+{int(p.get('bait_drop_bonus', 0)*100)}%`\n• Giá: `{price:,} {curr}` • Trạng thái: {hidden} • HSD: `{hsd}`{source}"
                safe_add_field(embed, name=p_name, value=val, inline=False)
            return embed

        elif self.category == "chest":
            embed = discord.Embed(
                title=f"📦 BÁCH KHOA: RƯƠNG BÁU ĐẠI DƯƠNG ({len(items)} loại)",
                description="Danh sách các loại rương báu chìm dưới đại dương sâu thẳm.",
                color=discord.Color.orange()
            )
            for c in page_items:
                c_name = c.get("name", c.get("id"))
                key = f"🔑 Cần chìa: `{UTILITY_ITEMS.get(c.get('req_key'), {}).get('name', c.get('req_key'))}`" if c.get("req_key") else "🔓 Mở tự do (không cần chìa)"
                chance = f"{c.get('chance', 0) * 100:.2f}%" if c.get("chance") else "Đặc biệt"
                hidden = "🔮 **Rương Ẩn**" if c.get("is_hidden") else "🌊 Xuất hiện khi câu"
                source = f"\n*Nơi tìm:* {c.get('obtain_source')}" if c.get("obtain_source") else ""
                val = f"• Tỉ lệ câu trúng: `{chance}` • {key}\n• Phần thưởng coin: `{c.get('min_coin', 0):,} - {c.get('max_coin', 0):,} coin`\n• Trạng thái: {hidden}{source}"
                safe_add_field(embed, name=c_name, value=val, inline=False)
            return embed

        elif self.category == "troll":
            embed = discord.Embed(
                title=f"🃏 BÁCH KHOA: VẬT PHẨM TROLL & TIỆN ÍCH ({len(items)} loại)",
                description="Danh sách các thẻ bài troll hài hước và công cụ đại dương.",
                color=discord.Color.red()
            )
            for t in page_items:
                t_name = t.get("name", t.get("id"))
                price = t.get("price", 0)
                curr = "Xu" if t.get("currency") == "xu" else "Coin"
                hidden = "🔮 **Vật Phẩm Ẩn**" if t.get("is_hidden") else ("🛒 Bán trong Shop" if price > 0 else "🎁 Báu vật rơi từ rương")
                act_k = f" • Key lệnh: `{t.get('action_key')}`" if t.get("action_key") else ""
                source = f"\n*Nguồn kiếm:* {t.get('obtain_source')}" if t.get("obtain_source") else ""
                val = f"• Mô tả: {t.get('desc', '—')}\n• Giá: `{price:,} {curr}` • Trạng thái: {hidden}{act_k}{source}"
                safe_add_field(embed, name=t_name, value=val, inline=False)
            return embed

        return embed

    async def _redraw(self, interaction: discord.Interaction):
        self._refresh_components()
        await interaction.response.edit_message(embed=self.build_embed(), view=self)

    async def _prev(self, interaction: discord.Interaction):
        self.page -= 1
        await self._redraw(interaction)

    async def _next(self, interaction: discord.Interaction):
        self.page += 1
        await self._redraw(interaction)

    async def _claim(self, interaction: discord.Interaction):
        m, ready = self._next_milestone()
        if not m or not ready:
            return await interaction.response.send_message("❌ Chưa đủ điều kiện nhận thưởng!", ephemeral=True)
        u_fish = get_user_fishing(self.author.id)
        u_fish.setdefault("dex_claimed_milestones", []).append(m["count"])
        b = m["reward_bait"]
        u_fish.setdefault("baits", {})[b] = u_fish["baits"].get(b, 0) + m["bait_amount"]
        await update_user_coins(self.guild_id, self.author.id, m["reward_coin"])
        save_fishing_data()
        await self._redraw(interaction)
        await interaction.followup.send(f"🎁 Mốc **{m['count']}** loài: **`+{m['reward_coin']:,}` coin** + **{m['bait_amount']}x {BAITS_CATALOG.get(b, {}).get('name', 'Mồi')}**!", ephemeral=True)

    async def _back(self, interaction: discord.Interaction):
        v = FishingInventoryView(self.author, self.guild_id)
        u_data = await get_user_data(self.guild_id, self.author.id)
        await interaction.response.edit_message(embed=v.build_embed(u_data.get("coins", 0)), view=v)


class OwnerEventModal(discord.ui.Modal, title="🎉 Mở Sự Kiện Đại Dương"):
    name_in = discord.ui.TextInput(label="Tên sự kiện", default="Lễ Hội Đại Dương", max_length=50)
    luck_in = discord.ui.TextInput(label="May mắn cộng thêm", default="50", max_length=4)
    multi_in = discord.ui.TextInput(label="Hệ số giá bán (vd 1.5)", default="1.5", max_length=5)
    min_in = discord.ui.TextInput(label="Thời lượng (phút)", default="60", max_length=5)

    async def on_submit(self, interaction: discord.Interaction):
        try:
            luck, multi, mins = int(self.luck_in.value), float(self.multi_in.value), int(self.min_in.value)
            assert mins > 0 and multi > 0
        except Exception:
            return await interaction.response.send_message("❌ Giá trị nhập không hợp lệ!", ephemeral=True)
        fishing_state["event"] = {"active": True, "name": self.name_in.value, "bonus_luck": luck, "price_multi": multi, "end_time": time.time() + mins * 60}
        save_fishing_data()
        await interaction.response.send_message(f"🎉 Đã mở sự kiện **{self.name_in.value}** (+{luck} may mắn, x{multi} giá) trong {mins} phút!")


class OwnerGiftcodeModal(discord.ui.Modal, title="🎁 Tạo Giftcode Mới"):
    code_in = discord.ui.TextInput(label="Mã code", placeholder="SAKURA2026", max_length=40)
    coin_in = discord.ui.TextInput(label="Coin thưởng", default="0", max_length=12)
    limit_in = discord.ui.TextInput(label="Số lượt dùng tối đa (0 = vô hạn)", default="0", max_length=6)
    hours_in = discord.ui.TextInput(label="Hết hạn sau (giờ, 0 = vĩnh viễn)", default="24", max_length=6)
    items_in = discord.ui.TextInput(
        label="Vật phẩm: loại:id=sl (cách nhau dấu phẩy)", required=False, style=discord.TextStyle.paragraph,
        placeholder="bait:bait_rare=5, chest:chest_gold=1, rod:rod_gold, pet:cat_pet, item:shield=2", max_length=400)

    def __init__(self, bot: commands.Bot, guild: discord.Guild):
        super().__init__()
        self.bot = bot
        self.guild = guild

    async def on_submit(self, interaction: discord.Interaction):
        code = self.code_in.value.strip().upper()
        try:
            coins, max_uses, hours = int(self.coin_in.value), int(self.limit_in.value), float(self.hours_in.value)
        except ValueError:
            return await interaction.response.send_message("❌ Coin / lượt dùng / giờ phải là số!", ephemeral=True)

        rewards = {"coins": max(0, coins), "rods": [], "baits": {}, "chests": {}, "pets": [], "items": {}}
        catalogs = {"rod": RODS_CATALOG, "bait": BAITS_CATALOG, "chest": CHESTS_DATA, "pet": PETS_CATALOG, "item": UTILITY_ITEMS}
        for part in filter(None, (p.strip() for p in (self.items_in.value or "").split(","))):
            try:
                kind, rest = part.split(":", 1)
                iid, _, amt = rest.partition("=")
                iid, amt = iid.strip(), int(amt) if amt else 1
                kind = kind.strip().lower()
                assert iid in catalogs[kind] and amt > 0
            except Exception:
                return await interaction.response.send_message(f"❌ Sai định dạng/ID vật phẩm: `{part}`", ephemeral=True)
            if kind in ("rod", "pet"):
                rewards[kind + "s"].append(iid)
            else:
                rewards[kind + "s"][iid] = amt

        fishing_state.setdefault("giftcodes", {})[code] = {
            "rewards": rewards, "max_uses": max(0, max_uses), "used_by": [],
            "expires_at": (time.time() + hours * 3600) if hours > 0 else 0,
        }
        save_fishing_data()

        announced = 0
        for gid, cfg in fishing_state.get("code_channels", {}).items():
            ch = self.bot.get_channel(cfg.get("channel_id", 0))
            if not ch:
                continue
            embed = discord.Embed(title="🎁 GIFTCODE MỚI!", description=f"Mã: **`{code}`**\nNhập tại `inv` ➜ Trang 2 ➜ **Nhập Code**.", color=discord.Color.gold())
            try:
                await ch.send(content=f"<@&{cfg['role_id']}>" if cfg.get("role_id") else None, embed=embed,
                              allowed_mentions=discord.AllowedMentions(roles=True))
                announced += 1
            except Exception:
                pass
        await interaction.response.send_message(f"✅ Đã tạo code **`{code}`** (đã thông báo {announced} kênh).", ephemeral=True)


class OwnerEconomyModal(discord.ui.Modal, title="👑 Owner: Coin / Xu / Hôn nhân"):
    action_in = discord.ui.TextInput(label="Hành động", placeholder="add / remove / set / addxu / removexu / setxu / divorce", default="add", max_length=15)
    user_in = discord.ui.TextInput(label="ID user hoặc @mention", placeholder="123456789012345678", max_length=30)
    amount_in = discord.ui.TextInput(label="Số Coin hoặc Xu (bỏ trống nếu divorce)", placeholder="10000", required=False, max_length=15)
    partner_in = discord.ui.TextInput(label="ID đối phương (chỉ dùng restore)", placeholder="ID partner", required=False, max_length=30)

    async def on_submit(self, interaction: discord.Interaction):
        if interaction.user.id != OWNER_ID:
            return await interaction.response.send_message("⛔ Chỉ Owner được sử dụng.", ephemeral=True)
        action = self.action_in.value.strip().lower()
        raw_id = self.user_in.value.strip().replace("<@", "").replace(">", "").replace("!", "")
        if not raw_id.isdigit():
            return await interaction.response.send_message("❌ ID user không hợp lệ.", ephemeral=True)
        uid = int(raw_id)
        if action in ("divorce", "restore"):
            marriages = fishing_state.setdefault("marriages", {})
            if action == "divorce":
                partner = marriages.pop(str(uid), None)
                if partner is not None:
                    marriages.pop(str(partner), None)
                    for k, c in list(fishing_state.setdefault("couples", {}).items()):
                        if {int(c.get("a", 0)), int(c.get("b", 0))} == {uid, int(partner)}: fishing_state["couples"].pop(k, None)
                    save_fishing_data()
                    return await interaction.response.send_message(f"💔 Đã gỡ trạng thái hôn nhân của <@{uid}> và <@{partner}>.", ephemeral=True)
                return await interaction.response.send_message("ℹ️ Không tìm thấy hôn nhân của user này.", ephemeral=True)
            raw_partner = self.partner_in.value.strip().replace("<@", "").replace(">", "").replace("!", "")
            if not raw_partner.isdigit() or int(raw_partner) == uid:
                return await interaction.response.send_message("Nhập ID đối phương hợp lệ ở ô thứ ba để khôi phục hôn nhân.", ephemeral=True)
            pid = int(raw_partner)
            if str(uid) in marriages or str(pid) in marriages:
                return await interaction.response.send_message("Một trong hai user đã có trạng thái hôn nhân.", ephemeral=True)
            marriages[str(uid)] = pid; marriages[str(pid)] = uid
            gid = interaction.guild_id
            if gid:
                key = _pair_key(gid, uid, pid)
                fishing_state.setdefault("couples", {})[key] = {"guild_id":gid,"a":uid,"b":pid,"ring":"ring_bronze","married_at":time.time(),"public":True,"affection":0,"weekly":{},"monthly":{},"daily":{},"common_coins":0,"properties":[],"tax_paid_at":time.time(),"restored_by_owner":True}
            save_fishing_data()
            return await interaction.response.send_message(f"💍 Đã khôi phục trạng thái hôn nhân của <@{uid}> và <@{pid}>.", ephemeral=True)
        try:
            amount = int(self.amount_in.value.strip().replace(",", ""))
            if amount < 0:
                raise ValueError
        except Exception:
            return await interaction.response.send_message("❌ Số lượng Coin / Xu phải là số nguyên không âm.", ephemeral=True)
        guild_id = interaction.guild_id
        if not guild_id:
            return await interaction.response.send_message("❌ Hành động này cần thực hiện trong server.", ephemeral=True)
        data = await get_user_data(guild_id, uid)
        balance = int(data.get("coins", 0))
        xu_balance = int(data.get("xu", 0))

        if action == "add":
            await update_user_coins(guild_id, uid, amount)
            msg = f"➕ Đã cộng **{amount:,} coin** cho <@{uid}>."
        elif action == "remove":
            actual = min(balance, amount)
            await update_user_coins(guild_id, uid, -actual)
            msg = f"➖ Đã trừ **{actual:,} coin** của <@{uid}>."
        elif action == "set":
            await update_user_coins(guild_id, uid, amount - balance)
            msg = f"🪙 Đã đặt số dư Coin <@{uid}> thành **{amount:,} coin**."
        elif action in ("addxu", "add_xu"):
            await update_user_xu(guild_id, uid, amount)
            msg = f"💎 Đã nạp thành công **{amount:,} xu** cho <@{uid}>."
        elif action in ("removexu", "remove_xu"):
            await update_user_xu(guild_id, uid, -amount)
            msg = f"➖ Đã khấu trừ **{amount:,} xu** của <@{uid}>."
        elif action in ("setxu", "set_xu"):
            await set_user_xu(guild_id, uid, amount)
            msg = f"💠 Đã đặt số dư Xu của <@{uid}> thành **{amount:,} xu**."
        else:
            return await interaction.response.send_message("❌ Hành động phải là add, remove, set, addxu, removexu, setxu, divorce hoặc restore.", ephemeral=True)
        await interaction.response.send_message(msg, ephemeral=True)


class OwnerAquariumModal(discord.ui.Modal, title="🐠 Quản Trị Thủy Cung - Owner"):
    user_in = discord.ui.TextInput(
        label="ID User hoặc @mention",
        placeholder="Nhập ID người chơi (hoặc để trống để xem BXH Top Thủy Cung)",
        required=False,
        max_length=32
    )
    action_in = discord.ui.TextInput(
        label="Hành động (xem / addslots / setlikes / clear / bxh)",
        placeholder="xem (mặc định) | addslots | setlikes | clear | bxh",
        default="xem",
        required=False,
        max_length=15
    )
    amount_in = discord.ui.TextInput(
        label="Số lượng (cho addslots / setlikes)",
        placeholder="Ví dụ: 10",
        required=False,
        max_length=10
    )

    def __init__(self, bot: commands.Bot, guild: discord.Guild, target_uid: Optional[int] = None):
        super().__init__()
        self.bot = bot
        self.guild = guild
        if target_uid:
            self.user_in.default = str(target_uid)

    async def on_submit(self, interaction: discord.Interaction):
        if interaction.user.id != OWNER_ID and not (getattr(interaction.user, 'guild_permissions', None) and interaction.user.guild_permissions.administrator):
            return await interaction.response.send_message("⛔ Chỉ Owner hoặc Admin mới được dùng chức năng này!", ephemeral=True)

        action = (self.action_in.value or "xem").strip().lower()
        raw_user = (self.user_in.value or "").strip().replace("<@", "").replace(">", "").replace("!", "")

        if action in ("bxh", "top", "leaderboard") or (not raw_user and action == "xem"):
            all_users = fishing_state.get("users", {})
            aquas = []
            for uid_s, udata in all_users.items():
                if str(uid_s) == "1144785664458637394": continue
                tank = udata.get("aquarium", [])
                if tank or udata.get("aquarium_likes"):
                    likes_cnt = len(udata.get("aquarium_likes", []))
                    slots = udata.get("aquarium_slots", 6)
                    aquas.append((uid_s, len(tank), slots, likes_cnt))
            aquas.sort(key=lambda x: (x[3], x[1]), reverse=True)
            if not aquas:
                return await interaction.response.send_message("ℹ️ Hiện chưa có người chơi nào nuôi cá trong Thủy Cung!", ephemeral=True)
            embed = discord.Embed(title="🐠 BẢNG XẾP HẠNG THỦY CUNG TOÀN SERVER (OWNER VIEW)", color=discord.Color.blue())
            desc_lines = []
            for rank, (uid_s, fish_cnt, slots, likes_cnt) in enumerate(aquas[:15], 1):
                desc_lines.append(f"**#{rank}** <@{uid_s}> (`{uid_s}`) — 🐟 `{fish_cnt}/{slots}` cá | ❤️ `{likes_cnt}` tim")
            embed.description = "\n".join(desc_lines)
            return await interaction.response.send_message(embed=embed, ephemeral=True)

        if not raw_user.isdigit():
            return await interaction.response.send_message("❌ ID người chơi không hợp lệ!", ephemeral=True)
        target_uid = int(raw_user)
        u_fish = get_user_fishing(target_uid)

        if action == "clear":
            old_count = len(u_fish.get("aquarium", []))
            u_fish["aquarium"] = []
            u_fish["aquarium_favorite"] = None
            save_fishing_data()
            return await interaction.response.send_message(f"✅ Đã dọn sạch `{old_count}` con cá trong Thủy Cung của <@{target_uid}>!", ephemeral=True)

        if action in ("addslots", "slots", "setslots"):
            val_s = (self.amount_in.value or "2").strip()
            if not val_s.lstrip("-").isdigit():
                return await interaction.response.send_message("❌ Số ô nhập vào phải là số nguyên!", ephemeral=True)
            val = int(val_s)
            if action in ("addslots", "slots"):
                u_fish["aquarium_slots"] = max(2, min(50, int(u_fish.get("aquarium_slots", 6)) + val))
            else:
                u_fish["aquarium_slots"] = max(2, min(50, val))
            save_fishing_data()
            return await interaction.response.send_message(f"✅ Sức chứa Thủy Cung của <@{target_uid}> hiện là: `{u_fish['aquarium_slots']}` ô!", ephemeral=True)

        if action in ("setlikes", "likes", "addlikes"):
            val_s = (self.amount_in.value or "1").strip()
            if not val_s.isdigit():
                return await interaction.response.send_message("❌ Số lượt thích phải là số nguyên dương!", ephemeral=True)
            likes_cnt = int(val_s)
            u_fish["aquarium_likes"] = [interaction.user.id] * likes_cnt
            save_fishing_data()
            return await interaction.response.send_message(f"✅ Đã cập nhật Thủy Cung của <@{target_uid}> có `{likes_cnt}` lượt thích!", ephemeral=True)

        target_member = self.guild.get_member(target_uid)
        if not target_member:
            try:
                target_member = await self.bot.fetch_user(target_uid)
            except Exception:
                target_member = None
        if not target_member:
            target_member = interaction.user

        view = AquariumView(owner=target_member, viewer=interaction.user, guild_id=interaction.guild.id)
        return await interaction.response.send_message(
            content=f"👑 **[Owner Quản Trị Thủy Cung]** Xem bảo tàng của <@{target_uid}>:",
            embed=view.build_embed(),
            view=view,
            ephemeral=True
        )


class OwnerFishingControlView(discord.ui.View):
    def __init__(self, author: discord.Member, bot: commands.Bot, guild: discord.Guild):
        super().__init__(timeout=300)
        self.author = author
        self.bot = bot
        self.guild = guild
        self._build_components()

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id != OWNER_ID:
            await interaction.response.send_message("⛔ Chỉ Chủ Bot mới dùng được!", ephemeral=True)
            return False
        return True

    def _build_components(self):
        self.clear_items()
        forced = fishing_state.get("forced_weather")
        options = [discord.SelectOption(label="🔄 Tự động theo chu kỳ", value="auto", default=(forced is None))]
        options += [discord.SelectOption(label=w["name"][:100], value=w["id"], default=(w["id"] == forced)) for w in WEATHER_CYCLE]
        sel = discord.ui.Select(placeholder="🌦️ Ép thời tiết...", options=options, row=0)
        sel.callback = self._weather_cb
        self.add_item(sel)

        for label, style, emoji, cb, row in (
            ("Mở Sự Kiện", discord.ButtonStyle.success, "🎉", self._event_on, 1),
            ("Tắt Sự Kiện", discord.ButtonStyle.danger, "🛑", self._event_off, 1),
            ("Tạo Giftcode", discord.ButtonStyle.primary, "🎁", self._gift, 1),
            ("Mở Giải Đấu", discord.ButtonStyle.success, "🏆", self._tour_on, 2),
            ("Kết Thúc Giải", discord.ButtonStyle.danger, "🏁", self._tour_off, 2),
            ("DS Giftcode", discord.ButtonStyle.secondary, "📋", self._list_codes, 2),
            ("Coin / Gỡ hôn nhân", discord.ButtonStyle.primary, "💍", self._economy, 3),
            ("Xem Thủy Cung", discord.ButtonStyle.secondary, "🐠", self._admin_aquarium, 3),
        ):
            b = discord.ui.Button(label=label, style=style, emoji=emoji, row=row)
            b.callback = cb
            self.add_item(b)

    def build_embed(self) -> discord.Embed:
        ev, tour = fishing_state.get("event", {}), fishing_state.get("tournament", {})
        forced = fishing_state.get("forced_weather")
        w = next((x for x in WEATHER_CYCLE if x["id"] == forced), None)
        embed = discord.Embed(title="👑 BẢNG ĐIỀU KHIỂN OWNER - FISHING", color=discord.Color.red())
        embed.add_field(name="🌦️ Thời tiết", value=(f"Ép: {w['name']}" if w else "Tự động"), inline=True)
        embed.add_field(name="🎉 Sự kiện", value=(f"**{ev.get('name')}** (hết <t:{int(ev.get('end_time', 0))}:R>)" if ev.get("active") and time.time() < ev.get("end_time", 0) else "Không có"), inline=True)
        embed.add_field(name="🏆 Giải đấu", value=(tour.get("name") or "Đang diễn ra") if tour.get("active") else "Không có", inline=True)
        embed.add_field(name="🎁 Giftcode", value=f"`{len(fishing_state.get('giftcodes', {}))}` mã", inline=True)
        embed.add_field(name="👥 Người chơi", value=f"`{len(fishing_state.get('users', {}))}`", inline=True)
        return embed

    async def _weather_cb(self, interaction: discord.Interaction):
        v = interaction.data["values"][0]
        fishing_state["forced_weather"] = None if v == "auto" else v
        save_fishing_data()
        self._build_components()
        await interaction.response.edit_message(embed=self.build_embed(), view=self)

    async def _event_on(self, interaction: discord.Interaction):
        await interaction.response.send_modal(OwnerEventModal())

    async def _event_off(self, interaction: discord.Interaction):
        fishing_state.setdefault("event", {})["active"] = False
        save_fishing_data()
        await interaction.response.edit_message(embed=self.build_embed(), view=self)

    async def _gift(self, interaction: discord.Interaction):
        await interaction.response.send_modal(OwnerGiftcodeModal(self.bot, self.guild))

    async def _tour_on(self, interaction: discord.Interaction):
        fishing_state["tournament"] = {"active": True, "name": "🏆 GIẢI ĐẤU DO OWNER MỞ", "end_time": time.time() + 45 * 60, "participants": {}}
        save_fishing_data()
        await interaction.response.edit_message(embed=self.build_embed(), view=self)

    async def _tour_off(self, interaction: discord.Interaction):
        tour = fishing_state.get("tournament", {})
        if tour.get("active"):
            tour["end_time"] = 0
        save_fishing_data()
        await interaction.response.edit_message(embed=self.build_embed(), view=self)

    async def _economy(self, interaction: discord.Interaction):
        await interaction.response.send_modal(OwnerEconomyModal())

    async def _list_codes(self, interaction: discord.Interaction):
        codes = fishing_state.get("giftcodes", {})
        lines = [f"`{c}` — {len(d.get('used_by', []))}/{d.get('max_uses') or '∞'} lượt" for c, d in list(codes.items())[:25]]
        await interaction.response.send_message("\n".join(lines) or "*Chưa có code nào.*", ephemeral=True)

    async def _admin_aquarium(self, interaction: discord.Interaction):
        await interaction.response.send_modal(OwnerAquariumModal(self.bot, self.guild))



from Command.command_marriage import (
    RING_IDS, RING_INFO, PROPERTY_INFO, LOVE_ITEMS,
    _pair_key, _get_couple, _get_user_couple
)


def _is_event_fish_global(f):
    return bool(f.get("event") or f.get("is_event") or f.get("event_fish") or f.get("source") == "event" or any(isinstance(ef, dict) and str(f.get("name", "")).strip() == str(ef.get("name", "")).strip() for ef in event_fish))


FISHING_ACTIONS = [
    "cast", "inv", "chest", "sell", "license", "aquarium", "upgrade", "cook", "top", "fishdex",
    "shop", "repair", "weather", "tournament", "owner", "setcodechannel", "setup", "zone", "zones",
    "farm", "nongtrai", "vuon", "farmer", "enchant", "gandong", "sao", "tiencap", "thangsao",
]


def generate_daily_giftcode(force: bool = False, custom_date: str = None) -> tuple[bool, str, dict]:
    """Tự động hoặc thủ công tạo giftcode theo ngày:
    - Code: DAILY_YYYYMMDD
    - Thưởng: 10,000 coins, 10 mồi thường, 1 thuốc x2 coins trong 2h
    - Giới hạn: 1000 lượt dùng
    - HSD: từ 7h00 AM đến 8h30 PM (20h30) cùng ngày (giờ VN)
    """
    now_vn = datetime.now(VN_TZ)
    date_str = custom_date or now_vn.strftime("%Y%m%d")
    code_name = f"DAILY_{date_str}"

    codes = fishing_state.setdefault("giftcodes", {})
    if code_name in codes and not force:
        return False, f"Mã {code_name} đã tồn tại trong ngày hôm nay!", codes[code_name]

    expire_dt = datetime(now_vn.year, now_vn.month, now_vn.day, 20, 30, 0, tzinfo=VN_TZ)
    expire_timestamp = expire_dt.timestamp()

    if time.time() >= expire_timestamp:
        expire_timestamp = time.time() + (3600 * 2)

    code_data = {
        "code": code_name,
        "is_daily": True,
        "date": date_str,
        "rewards": {
            "coins": 10000,
            "baits": {"bait_normal": 10},
            "items": {"potion_x2_coins_2h": 1},
            "rods": [],
            "chests": {},
            "pets": []
        },
        "max_uses": 1000,
        "used_by": [],
        "created_at": time.time(),
        "expires_at": expire_timestamp
    }
    codes[code_name] = code_data
    save_fishing_data()
    return True, f"Tạo thành công Giftcode hàng ngày {code_name}!", code_data


class FishingCog(commands.Cog, name="Fishing"):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.tournament_check_task.start()
        self.daily_giftcode_task.start()

    def cog_unload(self):
        self.tournament_check_task.cancel()
        self.daily_giftcode_task.cancel()

    def _get_current_weather(self) -> dict:
        forced = fishing_state.get("forced_weather")
        if forced:
            found = next((w for w in WEATHER_CYCLE if w["id"] == forced), None)
            if found:
                return found
        weather_index = int(time.time() // 7200) % len(WEATHER_CYCLE)
        return WEATHER_CYCLE[weather_index]

    def _is_event_active(self) -> bool:
        ev = fishing_state.get("event", {})
        if ev.get("active") and time.time() < ev.get("end_time", 0):
            return True
        if ev.get("active") and time.time() >= ev.get("end_time", 0):
            ev["active"] = False
            save_fishing_data()
        return False

    def _check_allowed_channel(self, ctx: commands.Context) -> bool:
        guild_id_str = str(ctx.guild.id)
        if fishing_state.get("allow_outside", {}).get(guild_id_str, False):
            return True
        allowed_channels = fishing_state.setdefault("fishing_channels", {}).get(guild_id_str, [])
        if not allowed_channels:
            return True
        return ctx.channel.id in allowed_channels

    def _calculate_catch(self, total_luck: int, mutation_rate: float, zone_mutation_bonus: float = 0.0):
        mut_mult = 1.0
        try:
            from data.game_rates import get_game_rates
            grates = get_game_rates()
            total_luck = int(total_luck * grates.get("fishing_luck_mult", 1.0))
            mut_mult = grates.get("fishing_mutation_mult", 1.0)
        except Exception:
            pass

        luck = max(0, total_luck)
        p_admin = min(0.035, 0.0001 + (luck * 0.00007))
        p_legendary = min(0.20, 0.01 + (luck * 0.0010))
        p_epic = min(0.38, 0.05 + (luck * 0.0025))
        p_rare = min(0.65, 0.20 + (luck * 0.0045))

        roll = random.random()
        if roll < p_admin:
            target_rarity = "admin"
        elif roll < (p_admin + p_legendary):
            target_rarity = "legendary"
        elif roll < (p_admin + p_legendary + p_epic):
            target_rarity = "epic"
        elif roll < (p_admin + p_legendary + p_epic + p_rare):
            target_rarity = "rare"
        else:
            target_rarity = "common"

        pool = [f for f in fish_list if f.get("rarity", "common") == target_rarity]
        if self._is_event_active():
            pool.extend([f for f in event_fish if f.get("rarity", "common") == target_rarity])

        if not pool:
            pool = [f for f in fish_list if f.get("rarity", "common") == "common"] or fish_list

        chosen_fish = random.choice(pool)

        size_weights = [35, 45, 15, 4, 1]
        if luck > 50:
            size_weights = [12, 28, 35, 18, 7]
        chosen_size = random.choices(SIZES_CONFIG, weights=size_weights, k=1)[0]

        effective_mut_rate = min(0.95, (mutation_rate + zone_mutation_bonus + (luck * 0.0012)) * mut_mult)
        chosen_mutation = None
        if random.random() < effective_mut_rate and mutations:
            chosen_mutation = random.choice(mutations)

        return chosen_fish, chosen_size, chosen_mutation

    @tasks.loop(minutes=1)
    async def tournament_check_task(self):
        now_vn = datetime.now(VN_TZ)
        hour, minute = now_vn.hour, now_vn.minute
        tour = fishing_state.setdefault("tournament", {"active": False, "name": "", "end_time": 0, "participants": {}})

        is_noon = (hour == 12 and minute == 0)
        is_night = (hour == 20 and minute == 0)

        if not tour.get("active") and (is_noon or is_night):
            tour_name = "🏆 ĐUA TOP CÂU CÁ TRƯA NẮNG" if is_noon else "🌙 ĐẠI CHIẾN NGƯ PHỦ ĐÊM TRĂNG"
            tour["active"] = True
            tour["name"] = tour_name
            tour["end_time"] = time.time() + (45 * 60)
            tour["participants"] = {}
            save_fishing_data()

            for gid_str, ch_list in fishing_state.get("fishing_channels", {}).items():
                if ch_list:
                    ch = self.bot.get_channel(ch_list[0])
                    if ch:
                        embed = discord.Embed(
                            title=f"📢 GIẢI ĐẤU BẮT ĐẦU: {tour_name}!",
                            description="Giải đấu diễn ra trong **45 phút**!\nNgười câu con cá **nặng nhất** sẽ nhận **3,000,000 Coin** và Mồi Hoàng Kim!",
                            color=discord.Color.gold()
                        )
                        try:
                            await ch.send(embed=embed)
                        except Exception:
                            pass

        if tour.get("active") and time.time() >= tour.get("end_time", 0):
            tour["active"] = False
            parts = tour.get("participants", {})
            save_fishing_data()

            if parts:
                sorted_rank = sorted(parts.items(), key=lambda x: x[1].get("weight", 0), reverse=True)[:3]
                prizes = [
                    (3000000, "bait_golden", "🥇 QUÁN QUÂN"),
                    (1500000, "bait_abyss", "🥈 Á QUÂN"),
                    (800000, "bait_legend", "🥉 QUÝ QUÂN"),
                ]

                lines = []
                for i, (uid_str, pdata) in enumerate(sorted_rank):
                    c_reward, b_reward, title_str = prizes[i]
                    await update_user_coins(int(pdata.get("guild_id", 0)), int(uid_str), c_reward)
                    u_target = get_user_fishing(int(uid_str))
                    u_target.setdefault("baits", {})[b_reward] = u_target.setdefault("baits", {}).get(b_reward, 0) + 2
                    b_name = BAITS_CATALOG.get(b_reward, {}).get("name", "Mồi")
                    lines.append(f"{title_str}: <@{uid_str}> — Bắt: **{pdata['fish_name']}** (`{pdata['weight']}kg`)\n└ Thưởng: **`+{c_reward:,}` coin** + 2x {b_name}")

                save_fishing_data()
                for gid_str, ch_list in fishing_state.get("fishing_channels", {}).items():
                    if ch_list:
                        ch = self.bot.get_channel(ch_list[0])
                        if ch:
                            embed = discord.Embed(
                                title="🏁 KẾT QUẢ GIẢI ĐẤU CÂU CÁ!",
                                description="\n\n".join(lines),
                                color=discord.Color.magenta()
                            )
                            try:
                                await ch.send(embed=embed)
                            except Exception:
                                pass

    @tournament_check_task.before_loop
    async def before_tournament(self):
        await self.bot.wait_until_ready()

    @tasks.loop(minutes=1)
    async def daily_giftcode_task(self):
        now_vn = datetime.now(VN_TZ)
        if now_vn.hour == 7 and now_vn.minute == 0:
            ok, msg, cdata = generate_daily_giftcode()
            if ok:
                code_str = cdata["code"]
                code_channels = fishing_state.get("code_channels", {})
                for gid, cfg in code_channels.items():
                    try:
                        ch_id = cfg.get("channel_id")
                        ch = self.bot.get_channel(int(ch_id)) if ch_id else None
                        if ch:
                            embed = discord.Embed(
                                title="🎁 SAKURA DAILY GIFTCODE — QUÀ TẶNG MỖI NGÀY!",
                                description=(
                                    f"Mã quà tặng ngày **{now_vn.strftime('%d/%m/%Y')}** đã xuất hiện!\n"
                                    f"👉 Mã code: **`{code_str}`**\n"
                                    f"⏰ Hạn dùng: **Đến 20h30 tối nay** (7:00 AM - 8:30 PM)\n"
                                    f"👥 Giới hạn: **1,000 lượt sử dụng**\n\n"
                                    f"Nhập mã tại: `s!inv` hoặc `/fishing inv` ➜ chọn **Nhập Code**."
                                ),
                                color=discord.Color.from_rgb(255, 121, 198)
                            )
                            embed.add_field(name="💰 Tiền thưởng", value="+10,000 Coins", inline=True)
                            embed.add_field(name="🪱 Mồi câu", value="+10 Mồi Thường", inline=True)
                            embed.add_field(name="🧪 Dược phẩm", value="+1 Thuốc x2 Coins (2h)", inline=True)
                            embed.set_footer(text="🌸 Chúc các ngư phủ một ngày mới may mắn và kéo được thật nhiều cá to!")
                            await ch.send(embed=embed)
                    except Exception:
                        pass

    @daily_giftcode_task.before_loop
    async def before_daily_giftcode(self):
        await self.bot.wait_until_ready()

    async def _action_autocomplete(self, interaction: discord.Interaction, current: str):
        actions = [
            ("Thả câu cá (cast)", "cast"),
            ("Túi đồ & Giỏ cá (inv)", "inv"),
            ("Vùng câu cá đại dương (zones)", "zones"),
            ("Cửa hàng Cần & Mồi (shop)", "shop"),
            ("Mở rương báu đáy biển (chest)", "chest"),
            ("Bán cá thông minh & đột biến (sell)", "sell"),
            ("Căn cước cần thủ đồ họa (license)", "license"),
            ("Thủy cung trưng bày sinh lời (aquarium)", "aquarium"),
            ("Cường hóa cần câu (upgrade)", "upgrade"),
            ("Bếp nấu nướng hải sản (cook)", "cook"),
            ("Bảng vinh danh cần thủ (top)", "top"),
            ("Sổ tay sinh vật biển (fishdex)", "fishdex"),
            ("Sửa chữa cần (repair)", "repair"),
            ("Thời tiết biển (weather)", "weather"),
            ("Sự kiện giải đấu (tournament)", "tournament"),
            ("Bảng điều khiển Owner (owner)", "owner"),
            ("Thiết lập kênh thông báo code (setcodechannel)", "setcodechannel"),
            ("Thiết lập kênh câu cá (setup)", "setup"),
            ("Nông trại trồng cây (farm)", "farm"),
            ("Bàn phép Enchant (enchant)", "enchant"),
        ]
        return [
            app_commands.Choice(name=name, value=val)
            for name, val in actions if current.lower() in name.lower() or current.lower() in val.lower()
        ]

    @commands.hybrid_command(
        name="fishing",
        aliases=["fish", "f"],
        description="🎣 Hệ thống câu cá: Shop, Giỏ đồ, Bảo tàng, Nấu ăn, Giftcode, Owner Control."
    )
    @commands.guild_only()
    @app_commands.describe(
        action="Chọn hành động muốn thực hiện",
        item="Vật phẩm mua / trang bị / bán / sửa / nấu / mở rương / code / vùng câu",
        amount="Số lượng hoặc lọc phân loại (all / mutation / common / rare / epic...)",
        channel="Kênh văn bản thiết lập thông báo",
        role="Role ping thông báo khi phát hành giftcode mới",
        user="Xem hồ sơ / thủy cung của thành viên khác"
    )
    @app_commands.autocomplete(action=_action_autocomplete)
    async def fishing(
        self,
        ctx: commands.Context,
        action: str = "cast",
        item: Optional[str] = None,
        amount: Optional[str] = None,
        channel: Optional[discord.TextChannel] = None,
        role: Optional[discord.Role] = None,
        user: Optional[discord.Member] = None
    ):
        act = action.lower().strip()
        user_id = ctx.author.id

        if act in FISHING_ZONES:
            item = act
            act = "cast"

        if act not in FISHING_ACTIONS:
            return await ctx.send("❌ Hành động không hợp lệ! Dùng: " + ", ".join(f"`{a}`" for a in FISHING_ACTIONS), ephemeral=True)

        if act == "cast" and not self._check_allowed_channel(ctx):
            allowed = fishing_state.get("fishing_channels", {}).get(str(ctx.guild.id), [])
            mentions = ", ".join(f"<#{cid}>" for cid in allowed)
            return await ctx.send(f"🚫 Bạn không thể câu cá tại kênh này! Hãy đến khu vực câu cá: {mentions}", ephemeral=True)

        u_fish = get_user_fishing(user_id)
        u_data = await get_user_data(ctx.guild.id, user_id)

        if act == "owner":
            if ctx.author.id != OWNER_ID:
                return await ctx.send("⛔ Bạn không phải là Chủ Bot (Owner)!", ephemeral=True)
            owner_view = OwnerFishingControlView(ctx.author, self.bot, ctx.guild)
            return await ctx.send(embed=owner_view.build_embed(), view=owner_view, ephemeral=True)

        if act == "setcodechannel":
            if not ctx.author.guild_permissions.administrator and ctx.author.id != OWNER_ID:
                return await ctx.send("⛔ Bạn cần quyền Administrator để thiết lập kênh thông báo code!", ephemeral=True)
            target_ch = channel or ctx.channel
            role_id = role.id if role else None

            fishing_state.setdefault("code_channels", {})[str(ctx.guild.id)] = {
                "channel_id": target_ch.id,
                "role_id": role_id
            }
            save_fishing_data()

            role_msg = f" (Role ping: {role.mention})" if role else ""
            embed = discord.Embed(
                title="✅ ĐÃ THIẾT LẬP KÊNH THÔNG BÁO GIFTCODE",
                description=f"Từ giờ, các mã Giftcode mới sẽ tự động gửi vào: {target_ch.mention}{role_msg}!",
                color=discord.Color.green()
            )
            return await ctx.send(embed=embed)

        if act == "shop":
            view = FishingShopView(ctx.author, ctx.guild.id)
            embed = view.build_embed(u_data.get("coins", 0), int(u_data.get("xu", 0)))
            return await ctx.send(embed=embed, view=view)

        if act == "inv":
            target_user = user or ctx.author
            if target_user.id != ctx.author.id:
                is_owner = (ctx.author.id in (1144785664458637394, OWNER_ID) or await self.bot.is_owner(ctx.author))
                if not is_owner:
                    msg = "❌ Bạn chỉ có thể xem túi đồ của chính mình! Không được phép xem của người khác." if is_vietnamese(ctx.guild.id) else "❌ You can only view your own inventory! You cannot view other players'."
                    return await ctx.send(msg, ephemeral=True)
            u_target_data = await get_user_data(ctx.guild.id, target_user.id)
            view = FishingInventoryView(target_user, ctx.guild.id)
            embed = view.build_embed(u_target_data.get("coins", 0), u_target_data.get("xu", 0))
            return await ctx.send(embed=embed, view=view)

        if act in ("zone", "zones"):
            target_zone_id = (item or "").lower().strip()
            user_level = int(u_data.get("level", 0))
            if target_zone_id and target_zone_id in FISHING_ZONES:
                zdata = FISHING_ZONES[target_zone_id]
                if user_level < zdata["min_level"]:
                    return await ctx.send(f"🔒 Bạn cần đạt **Level {zdata['min_level']}** để vào vùng **{zdata['name']}**! (Hiện tại: Lv.{user_level})", ephemeral=True)
                u_fish["zone"] = target_zone_id
                save_fishing_data()
                return await ctx.send(f"⛵ Thuyền câu đã cập bến **{zdata['name']}**! (+{zdata['luck_bonus']} May Mắn, +{int(zdata['mutation_rate_bonus']*100)}% Đột Biến)")

            cur_z_id = u_fish.get("zone", "ven_bo")
            view = FishingZoneSelectView(ctx.author, cur_z_id, user_level)
            return await ctx.send(embed=view.build_embed(), view=view)

        if act == "cast":
            now = time.time()
            buffs = u_fish.setdefault("buffs", {})

            if buffs.get("freeze_fishing", 0) > now:
                rem_f = int(buffs["freeze_fishing"] - now)
                return await ctx.send(f"🧊 Cần câu của bạn đang bị **đóng băng** bởi Bom Băng Giá! Hãy chờ **{rem_f} giây** để rã đông.", ephemeral=True)

            exp_notifs = check_user_item_expiration(user_id)
            if exp_notifs and not u_fish.get("equipped_rod"):
                return await ctx.send(f"⚠️ **Cần câu của bạn đã hết hạn sử dụng:**\n" + "\n".join(exp_notifs) + f"\n\n*Dùng `{ctx.prefix}f renew <id_cần>` để gia hạn hoặc vào `{ctx.prefix}inv` đổi cần khác!*", ephemeral=True)

            equipped_rod_id = u_fish.get("equipped_rod")
            if not equipped_rod_id or equipped_rod_id not in u_fish.get("rods", {}):
                return await ctx.send(f"⚠️ Bạn chưa trang bị cần câu! Dùng `{ctx.prefix}fshop` để mua và `{ctx.prefix}inv` để chọn cần.", ephemeral=True)

            current_rod = u_fish["rods"][equipped_rod_id]
            if current_rod.get("expired"):
                return await ctx.send(f"⏳ Cần câu **{current_rod.get('name', equipped_rod_id)}** đã hết hạn sử dụng! Dùng `{ctx.prefix}f renew {equipped_rod_id}` để gia hạn thêm.", ephemeral=True)

            if current_rod.get("durability", 0) <= 0:
                return await ctx.send(f"❌ Cần câu đã hỏng độ bền! Dùng `{ctx.prefix}fishing repair` để sửa chữa.", ephemeral=True)

            ench_stats = get_rod_enchant_stats(current_rod)
            base_cooldown = 10
            if buffs.get("fast_cast", 0) > now:
                base_cooldown = 5
            if ench_stats.get("pull_speed", 0) > 0:
                base_cooldown = max(3, int(base_cooldown * (1.0 - min(ench_stats["pull_speed"], 60) / 100.0)))

            if now - u_fish.get("last_cast", 0) < base_cooldown:
                remain = int(base_cooldown - (now - u_fish.get("last_cast", 0)))
                return await ctx.send(f"⏳ Biển đang động! Hãy chờ **{remain} giây** trước khi thả tiếp.", ephemeral=True)

            if buffs.get("cursed_bait"):
                buffs.pop("cursed_bait", None)
                trash_id = random.choice(list(TRASH_ITEMS.keys()))
                u_fish.setdefault("trash_bag", {})[trash_id] = u_fish.setdefault("trash_bag", {}).get(trash_id, 0) + 1
                u_fish["stats"]["total_trash"] = u_fish["stats"].get("total_trash", 0) + 1
                u_fish["last_cast"] = now
                save_fishing_data()
                return await ctx.send(f"🪱 **LỜI NGUYỀN GIĂNG LƯỚI!** Bạn bị trúng Mồi Nguyền Rủa nên giật cước chỉ vớt lên được **{TRASH_ITEMS[trash_id]['name']}**! Toàn bộ cá đã sợ hãi bơi đi mất!")

            max_bag = u_fish.get("max_bag", 30)
            if len(u_fish.get("fish_bag", [])) >= max_bag:
                return await ctx.send(f"🎒 Giỏ cá đầy (`{len(u_fish['fish_bag'])}/{max_bag}`)! Dùng `{ctx.prefix}inv` để bán hoặc nấu nướng.", ephemeral=True)

            target_zone_id = (item or amount or "").lower().strip()
            user_level = int(u_data.get("level", 0))
            if target_zone_id in FISHING_ZONES:
                zdata = FISHING_ZONES[target_zone_id]
                if user_level < zdata["min_level"]:
                    return await ctx.send(f"🔒 Bạn cần đạt **Level {zdata['min_level']}** để vào vùng **{zdata['name']}**! (Hiện tại: Lv.{user_level})", ephemeral=True)
                u_fish["zone"] = target_zone_id

            current_zone_id = u_fish.get("zone", "ven_bo")
            if current_zone_id not in FISHING_ZONES:
                current_zone_id = "ven_bo"
                u_fish["zone"] = "ven_bo"
            current_zone = FISHING_ZONES[current_zone_id]
            if user_level < current_zone["min_level"]:
                current_zone_id = "ven_bo"
                u_fish["zone"] = "ven_bo"
                current_zone = FISHING_ZONES["ven_bo"]

            u_fish["last_cast"] = now

            current_weather = self._get_current_weather()
            rod_luck = current_rod.get("luck", 1) + (current_rod.get("refine", 0) * 4) + ench_stats.get("luck", 0)

            bait_luck = 0
            equipped_bait_id = u_fish.get("equipped_bait")
            if equipped_bait_id:
                b_count = u_fish.get("baits", {}).get(equipped_bait_id, 0)
                if b_count > 0:
                    u_fish["baits"][equipped_bait_id] -= 1
                    bait_luck = BAITS_CATALOG.get(equipped_bait_id, {}).get("luck", 0)
                    if u_fish["baits"][equipped_bait_id] <= 0:
                        del u_fish["baits"][equipped_bait_id]
                        u_fish["equipped_bait"] = None
                else:
                    u_fish["equipped_bait"] = None

            pet_luck = 0
            pet_price_multi = 1.0
            equipped_pet_id = u_fish.get("equipped_pet")
            if equipped_pet_id and equipped_pet_id in PETS_CATALOG:
                p_info = PETS_CATALOG[equipped_pet_id]
                pet_luck = p_info["luck_bonus"]
                pet_price_multi = p_info["price_multi"]

            cook_luck = 30 if buffs.get("soup_luck", 0) > now else 0
            cook_price_multi = 1.20 if buffs.get("bento_price", 0) > now else 1.0
            event_luck = fishing_state.get("event", {}).get("bonus_luck", 0) if self._is_event_active() else 0
            treasure_map_luck = (rod_luck + bait_luck) if buffs.get("treasure_map_luck", 0) > now else 0
            golden_scale_multi = 1.50 if buffs.get("golden_scale_price", 0) > now else 1.0

            total_luck = rod_luck + bait_luck + current_weather["bonus_luck"] + current_zone["luck_bonus"] + pet_luck + cook_luck + event_luck + treasure_map_luck
            zone_mut_bonus = current_zone["mutation_rate_bonus"] + (ench_stats.get("mutant_rate", 0) / 100.0)
            chosen_fish, chosen_size, chosen_mutation = self._calculate_catch(total_luck, current_weather["mutation_rate"], zone_mutation_bonus=zone_mut_bonus)

            rarity = chosen_fish.get("rarity", "common")
            is_big_boss = rarity in ("epic", "legendary", "admin") or (chosen_mutation is not None)
            has_auto_qte = buffs.get("auto_qte", 0) > now

            sea_stone_charges = buffs.get("relic_sea_stone_charges", 0)
            if sea_stone_charges > 0:
                buffs["relic_sea_stone_charges"] -= 1
            elif ench_stats.get("durability_save", 0) > 0 and (random.random() * 100.0 < ench_stats["durability_save"]):
                pass
            else:
                current_rod["durability"] -= 1
                if current_rod["durability"] <= 0:
                    u_fish["stats"]["broken_rods"] = u_fish["stats"].get("broken_rods", 0) + 1
                    u_fish["equipped_rod"] = None

            if is_big_boss and not has_auto_qte:
                target_dir = random.choice(["left", "up", "right"])
                dir_vi = {"left": "KÉO TRÁI ⬅️", "up": "GHÌM CƯỚC ⬆️", "right": "KÉO PHẢI ➡️"}
                view = QTEPullView(ctx.author, target_dir)
                msg = await ctx.send(content=f"🚨 **QUÁI THÚ CẮN CÂU!** Nhấn **[{dir_vi[target_dir]}]** trong 4.5 giây!", view=view)
                await view.wait()

                if not view.success:
                    save_fishing_data()
                    return await msg.edit(content="💥 **ĐỨT CƯỚC!** Con quái thú đã giãy mạnh và trốn thoát...", view=None)

            base_price = int(chosen_fish.get("price", 100))
            mutation_multi = chosen_mutation.get("price_multi", 1.0) if chosen_mutation else 1.0
            event_multi = fishing_state.get("event", {}).get("price_multi", 1.0) if self._is_event_active() else 1.0
            final_price = max(20, int(base_price * chosen_size["multi"] * mutation_multi * event_multi * pet_price_multi * cook_price_multi * golden_scale_multi))

            weight = round(random.uniform(*chosen_size["weight_range"]), 2)
            length = round(random.uniform(*chosen_size["length_range"]), 1)
            fish_name = chosen_fish.get("name", "Cá")

            fish_entry = {
                "name": fish_name,
                "rarity": rarity,
                "size_name": chosen_size["name"],
                "weight": weight,
                "length": length,
                "mutation": chosen_mutation.get("name") if chosen_mutation else None,
                "price": final_price,
                "time": int(now),
            }
            u_fish.setdefault("fish_bag", []).append(fish_entry)
            u_fish["stats"]["total_caught"] = u_fish["stats"].get("total_caught", 0) + 1

            caught_trash_name = None
            if random.random() < 0.35:
                trash_id = random.choice(list(TRASH_ITEMS.keys()))
                u_fish.setdefault("trash_bag", {})[trash_id] = u_fish.setdefault("trash_bag", {}).get(trash_id, 0) + 1
                u_fish["stats"]["total_trash"] = u_fish["stats"].get("total_trash", 0) + 1
                caught_trash_name = TRASH_ITEMS[trash_id]["name"]

            tour = fishing_state.get("tournament", {})
            if tour.get("active"):
                parts = tour.setdefault("participants", {})
                if str(user_id) not in parts or weight > parts[str(user_id)].get("weight", 0):
                    parts[str(user_id)] = {"weight": weight, "fish_name": fish_name, "guild_id": ctx.guild.id}

            if weight > u_fish["biggest_catch"].get("weight", 0.0):
                u_fish["biggest_catch"] = {"name": fish_name, "weight": weight, "length": length}

            dex = u_fish.setdefault("fishdex", {})
            if fish_name not in dex:
                dex[fish_name] = {"count": 1, "max_weight": weight, "max_length": length, "rarity": rarity}
            else:
                dex[fish_name]["count"] = dex[fish_name].get("count", 0) + 1
                dex[fish_name]["max_weight"] = max(dex[fish_name].get("max_weight", 0.0), weight)
                dex[fish_name]["max_length"] = max(dex[fish_name].get("max_length", 0.0), length)

            chest_bonus = 0.03 if buffs.get("chest_buff", 0) > now else 0.0
            found_chest_name = None
            try:
                from data.game_rates import get_game_rates
                c_mult = get_game_rates().get("fishing_chest_mult", 1.0)
            except Exception:
                c_mult = 1.0

            for c_id, c_data in CHESTS_DATA.items():
                if random.random() < ((c_data["chance"] * c_mult) + (total_luck * 0.0003) + chest_bonus):
                    u_fish.setdefault("chests", {})[c_id] = u_fish.setdefault("chests", {}).get(c_id, 0) + 1
                    found_chest_name = c_data["name"]
                    break

            save_fishing_data()

            try:
                from Command.achievement_system import unlock_achievement
                gid = ctx.guild.id if ctx.guild else 0
                tc = u_fish["stats"].get("total_caught", 1)
                await unlock_achievement(gid, user_id, "fish_first", ctx.channel)
                if tc >= 10: await unlock_achievement(gid, user_id, "fish_10", ctx.channel)
                if tc >= 50: await unlock_achievement(gid, user_id, "fish_50", ctx.channel)
                if tc >= 100: await unlock_achievement(gid, user_id, "fish_100", ctx.channel)
                if tc >= 250: await unlock_achievement(gid, user_id, "fish_250", ctx.channel)
                if tc >= 500: await unlock_achievement(gid, user_id, "fish_500", ctx.channel)
                if tc >= 1000: await unlock_achievement(gid, user_id, "fish_1000", ctx.channel)

                if rarity in ("rare", "epic", "legendary", "mythic", "godly"):
                    await unlock_achievement(gid, user_id, "fish_rare_first", ctx.channel)
                if rarity == "epic":
                    await unlock_achievement(gid, user_id, "fish_epic_first", ctx.channel)
                elif rarity == "legendary":
                    await unlock_achievement(gid, user_id, "fish_legendary_first", ctx.channel)
                elif rarity == "mythic":
                    await unlock_achievement(gid, user_id, "fish_mythic_first", ctx.channel)
                elif rarity == "godly":
                    await unlock_achievement(gid, user_id, "fish_godly_first", ctx.channel)

                if chosen_mutation:
                    await unlock_achievement(gid, user_id, "fish_mutant_first", ctx.channel)
                    m_id = str(chosen_mutation.get("id") or chosen_mutation.get("name", "")).lower()
                    if "gold" in m_id or "hoàng kim" in m_id:
                        await unlock_achievement(gid, user_id, "fish_mutant_gold", ctx.channel)
                    if "void" in m_id or "hư không" in m_id:
                        await unlock_achievement(gid, user_id, "fish_mutant_void", ctx.channel)

                if found_chest_name:
                    await unlock_achievement(gid, user_id, "fish_chest_open", ctx.channel)
                if u_fish["stats"].get("total_trash", 0) >= 10:
                    await unlock_achievement(gid, user_id, "fish_trash_10", ctx.channel)
            except Exception:
                pass

            embed = discord.Embed(
                title=f"{RARITY_ICONS.get(rarity, '🐟')} Thu Hoạch: {fish_name}!",
                description=chosen_fish.get("description", "Sinh vật đại dương quý giá."),
                color=RARITY_COLORS.get(rarity, discord.Color.blue()),
            )
            safe_add_field(embed, name="🏷️ Phẩm chất", value=f"`{rarity.upper()}`", inline=True)
            safe_add_field(embed, name="📏 Kích thước", value=f"`{chosen_size['name']}` ({length}cm - {weight}kg)", inline=True)
            safe_add_field(embed, name="💰 Trị giá", value=f"**`{final_price:,}` coin**", inline=True)
            safe_add_field(embed, name="📍 Vùng câu", value=f"**{current_zone['name']}** (+{current_zone['luck_bonus']} Luck, +{int(current_zone['mutation_rate_bonus']*100)}% Đột biến)", inline=False)
            if chosen_mutation:
                safe_add_field(embed, name="🧬 Đột biến", value=f"**{chosen_mutation['name']}** (x{chosen_mutation['price_multi']} giá)", inline=False)
            if caught_trash_name:
                safe_add_field(embed, name="🗑️ Rác Mắc Vào Cước!", value=f"Lưỡi câu móc trúng **{caught_trash_name}**! Mở `{ctx.prefix}inv` để tái chế.", inline=False)
            if found_chest_name:
                safe_add_field(embed, name="🎁 Vớt Được Rương Báu!", value=f"Bạn vừa vớt được **{found_chest_name}**! Mở tại `{ctx.prefix}inv`.", inline=False)

            stone_info = f" • 🗿 Đá Trấn Hải: còn {buffs.get('relic_sea_stone_charges', 0)} lần" if buffs.get("relic_sea_stone_charges", 0) > 0 else ""
            embed.set_footer(text=f"Giỏ: {len(u_fish['fish_bag'])}/{max_bag} • Vùng: {current_zone['name']} • May mắn: +{total_luck} • {current_weather['name']}{stone_info}")
            return await ctx.send(embed=embed)

        if act in ("aquarium", "thuycung", "aqua", "baotang", "tc", "faqua"):
            target_user = user or ctx.author
            view = AquariumView(owner=target_user, viewer=ctx.author, guild_id=ctx.guild.id)
            return await ctx.send(embed=view.build_embed(), view=view)

        if act == "cook":
            view = CookingView(ctx.author, ctx.guild.id)
            return await ctx.send(embed=view.build_embed(), view=view)

        if act in ("fishdex", "dex", "bachkhoa", "bk"):
            cat = "fish"
            if item:
                im = item.lower().strip()
                if im in ("cá", "ca", "fish"): cat = "fish"
                elif im in ("cần", "can", "rod", "rods"): cat = "rod"
                elif im in ("mồi", "moi", "bait", "baits"): cat = "bait"
                elif im in ("pet", "pets", "thú", "thu"): cat = "pet"
                elif im in ("rương", "ruong", "chest", "chests"): cat = "chest"
                elif im in ("troll", "item", "items"): cat = "troll"
            view = FishdexView(ctx.author, ctx.guild.id, category=cat)
            return await ctx.send(embed=view.build_embed(), view=view)

        if act in ("renew", "giahan"):
            target_item = (item or "").strip()
            if not target_item:
                target_item = u_fish.get("equipped_rod") or u_fish.get("equipped_pet")
            if not target_item:
                return await ctx.send(f"⚠️ Vui lòng chỉ định ID vật phẩm muốn gia hạn: `{ctx.prefix}f renew <id_vật_phẩm>`\nVí dụ: `{ctx.prefix}f renew rod_thunder`", ephemeral=True)
            ok, msg = await renew_user_item(user_id, target_item, ctx.guild.id)
            return await ctx.send(msg)

        if act == "chest":
            chests = u_fish.setdefault("chests", {})
            sub = (item or "list").lower().strip()

            if sub in CHESTS_DATA:
                c_id = sub
                if chests.get(c_id, 0) <= 0:
                    return await ctx.send(f"❌ Bạn không có rương **{CHESTS_DATA[c_id]['name']}** nào để mở!", ephemeral=True)

                c_info = CHESTS_DATA[c_id]
                req_k = c_info.get("req_key")
                if req_k:
                    items = u_fish.setdefault("items", {})
                    if items.get(req_k, 0) <= 0:
                        k_name = UTILITY_ITEMS[req_k]["name"]
                        return await ctx.send(f"🔒 Rương này bị khóa kín! Bạn cần sở hữu **{k_name}** trong túi để mở khóa rương.", ephemeral=True)
                    items[req_k] -= 1

                chests[c_id] -= 1
                reward_coins = random.randint(c_info["min_coin"], c_info["max_coin"])
                reward_bait = random.choice(c_info["bait_pool"])
                b_name = BAITS_CATALOG.get(reward_bait, {}).get("name", "Mồi")

                reward_lines = [f"• 💰 **`+{reward_coins:,}` coin**", f"• 🪱 **1x {b_name}**"]
                u_fish.setdefault("baits", {})[reward_bait] = u_fish.setdefault("baits", {}).get(reward_bait, 0) + 1

                if c_info.get("rod_pool") and random.random() < 0.08:
                    won_rod_id = random.choice(c_info["rod_pool"])
                    r_item = RODS_CATALOG[won_rod_id]
                    u_fish.setdefault("rods", {})[won_rod_id] = {
                        "name": r_item["name"], "durability": r_item["durability"],
                        "max_durability": r_item["durability"], "luck": r_item["luck"],
                        "price": r_item["price"], "refine": 0
                    }
                    reward_lines.append(f"• 🎣 **CẦN ĐỘC QUYỀN: {r_item['name']}**!")

                if c_info.get("item_pool") and random.random() < 0.15:
                    won_item_id = random.choice(c_info["item_pool"])
                    it_info = UTILITY_ITEMS[won_item_id]
                    u_fish.setdefault("items", {})[won_item_id] = u_fish.setdefault("items", {}).get(won_item_id, 0) + 1
                    reward_lines.append(f"• 🔮 **BÁU VẬT HIẾM: {it_info['name']}**!")

                await update_user_coins(ctx.guild.id, user_id, reward_coins)
                save_fishing_data()

                embed = discord.Embed(
                    title=f"🗝️ MỞ {c_info['name'].upper()} THÀNH CÔNG!",
                    description="Bạn đã nhận được:\n" + "\n".join(reward_lines),
                    color=discord.Color.gold()
                )
                return await ctx.send(embed=embed)

            lines = [f"• **{cdata['name']}** (`{cid}`): `x{chests.get(cid, 0)}` chiếc" for cid, cdata in CHESTS_DATA.items()]
            embed = discord.Embed(
                title=f"📦 RƯƠNG BÁU CỦA {ctx.author.display_name}",
                description="\n".join(lines) + f"\n\nHoặc mở nhanh tại giao diện `{ctx.prefix}inv`!",
                color=discord.Color.dark_teal()
            )
            return await ctx.send(embed=embed)

        if act == "sell":
            bag = u_fish.get("fish_bag", [])
            if not bag:
                return await ctx.send("🐟 Giỏ cá của bạn đang trống!", ephemeral=True)

            filter_mode = (amount or item or "all").lower().strip()
            mode_map = {
                "all": "all",
                "common": "common",
                "rare": "rare",
                "epic": "epic",
                "legendary": "legendary",
                "event": "event",
                "admin": "admin",
                "mutation": "mutation",
                "dotbien": "mutation",
                "mutated": "mutation",
                "db": "mutation"
            }
            target_filter = mode_map.get(filter_mode, "all")
            def _is_event_fish(f):
                return bool(f.get("event") or f.get("is_event") or f.get("event_fish") or f.get("source") == "event" or any(str(f.get("name", "")).strip() == str(ef.get("name", "")).strip() for ef in event_fish if isinstance(ef, dict)))
            def _sell_eligible(f):
                rarity = str(f.get("rarity", "common")).lower()
                if target_filter == "mutation": return bool(f.get("mutation")) and rarity != "admin"
                if target_filter == "event": return _is_event_fish(f) and rarity != "admin"
                if target_filter == "admin": return rarity == "admin"
                if target_filter == "all": return rarity != "admin" and not _is_event_fish(f) and not f.get("mutation")
                return rarity == target_filter and rarity != "admin" and not _is_event_fish(f) and not f.get("mutation")
            to_sell = [f for f in bag if _sell_eligible(f)]
            sell_ids = {id(f) for f in to_sell}
            kept_bag = [f for f in bag if id(f) not in sell_ids]

            if not to_sell:
                return await ctx.send(f"⚠️ Không có con cá nào khớp với bộ lọc `{filter_mode}` để bán!", ephemeral=True)

            earned = sum(f.get("price", 0) for f in to_sell)
            buffs = u_fish.get("buffs", {})
            now_ts = time.time()
            buff_notes = []

            equipped_rod_id = u_fish.get("equipped_rod")
            cur_rod = u_fish.get("rods", {}).get(equipped_rod_id, {}) if equipped_rod_id else {}
            ench_stats = get_rod_enchant_stats(cur_rod)
            if ench_stats.get("sell_bonus", 0) > 0:
                bonus_pct = ench_stats["sell_bonus"]
                earned = int(earned * (1.0 + bonus_pct / 100.0))
                buff_notes.append(f"✨ +{bonus_pct}% Hoàng Kim Ngư")

            if buffs.get("golden_scale_price", 0) > now_ts:
                earned = int(earned * 1.5)
                buff_notes.append("🪙 +50% Vảy Rồng Vàng")
            if buffs.get("double_coins_buff", 0) > now_ts:
                earned = int(earned * 2.0)
                buff_notes.append("🧪 x2 Thuốc Nhân Đôi")

            u_fish["fish_bag"] = kept_bag
            u_fish["stats"]["total_earned"] = u_fish["stats"].get("total_earned", 0) + earned
            await update_user_coins(ctx.guild.id, user_id, earned)
            save_fishing_data()

            filter_display = "CÁ ĐỘT BIẾN (MUTATION) 🧬" if target_filter == "mutation" else target_filter.upper()
            note_buff = f" [{' | '.join(buff_notes)}]" if buff_notes else ""
            note = "(Lọc ALL mặc định bỏ qua Admin/Event/đột biến để bảo vệ cá quý)" if target_filter == "all" else ""
            return await ctx.send(f"💰 Đã bán **{len(to_sell)}** con cá theo bộ lọc `{filter_display}` thu về **`+{earned:,}` coin**!{note_buff} (Giữ lại {len(kept_bag)} con) {note}")

        if act == "repair":
            rod_id = u_fish.get("equipped_rod")
            if not rod_id or rod_id not in u_fish.get("rods", {}):
                return await ctx.send("❌ Cần câu chưa được trang bị!", ephemeral=True)
            r = u_fish["rods"][rod_id]
            max_d = r.get("max_durability", 100)
            cur_d = r.get("durability", 0)
            if cur_d >= max_d:
                return await ctx.send("✅ Cần câu còn nguyên 100% độ bền!", ephemeral=True)
            cost = max(500, int(((max_d - cur_d) / max_d) * r.get("price", 5000) * 0.45))
            wallet = u_data.get("coins", 0)
            if wallet < cost:
                return await ctx.send(f"❌ Cần `{cost:,}` coin để sửa độ bền!", ephemeral=True)
            await update_user_coins(ctx.guild.id, user_id, -cost)
            r["durability"] = max_d
            save_fishing_data()
            return await ctx.send(f"🛠️ Đã sửa chữa cần **{r['name']}** với `{cost:,}` coin!")

        if act in ("farm", "nongtrai", "vuon"):
            from Command.farm_system import FarmView
            fv = FarmView(ctx.author, ctx.guild.id)
            return await ctx.send(embed=fv.build_embed(), view=fv)

        if act in ("enchant", "gandong"):
            v = FishingInventoryView(ctx.author, ctx.guild.id)
            v.inv_page = 4
            v._build_components()
            u_data = await get_user_data(ctx.guild.id, ctx.author.id)
            return await ctx.send(embed=v.build_embed(u_data.get("coins", 0), int(u_data.get("xu", 0))), view=v)

        if act in ("sao", "tiencap", "stars"):
            v = FishingInventoryView(ctx.author, ctx.guild.id)
            v.inv_page = 3
            v._build_components()
            u_data = await get_user_data(ctx.guild.id, ctx.author.id)
            return await ctx.send(embed=v.build_embed(u_data.get("coins", 0), int(u_data.get("xu", 0))), view=v)

        if act == "upgrade":
            rod_id = u_fish.get("equipped_rod")
            if not rod_id or rod_id not in u_fish.get("rods", {}):
                return await ctx.send("❌ Hãy trang bị cần câu trước khi đập đồ!", ephemeral=True)
            r = u_fish["rods"][rod_id]
            curr_refine = r.setdefault("refine", 0)
            if curr_refine >= 300:
                return await ctx.send("⭐ Cần câu đã đạt cấp cường hóa tối đa (**+300 TỐI THƯỢNG**)! Hãy dùng lệnh `s!sao` để Tiến Cấp Sao ⭐!", ephemeral=True)

            base_cost = max(r.get("price", 5000), 10000)
            cost = max(3000, int(base_cost * 0.18 * ((curr_refine + 1) ** 1.25)))
            wallet = u_data.get("coins", 0)
            if wallet < cost:
                return await ctx.send(f"❌ Không đủ coin! Cần **`{cost:,}` coin**.", ephemeral=True)

            if curr_refine < 10:
                success_rate = 1.0 - (curr_refine * 0.03)
            elif curr_refine < 30:
                success_rate = max(0.25, 0.65 - ((curr_refine - 10) * 0.012))
            elif curr_refine < 70:
                success_rate = max(0.12, 0.35 - ((curr_refine - 30) * 0.004))
            elif curr_refine < 120:
                success_rate = max(0.06, 0.15 - ((curr_refine - 70) * 0.0015))
            elif curr_refine < 200:
                success_rate = max(0.03, 0.06 - ((curr_refine - 120) * 0.0004))
            else:
                success_rate = max(0.015, 0.03 - ((curr_refine - 200) * 0.00015))

            ench_stats = get_rod_enchant_stats(r)
            if ench_stats.get("refine_rate", 0) > 0:
                success_rate = min(0.95, success_rate + (ench_stats["refine_rate"] / 100.0))

            is_admin_or_owner = False
            try:
                from config import OWNER_ID
                if user_id == int(OWNER_ID):
                    is_admin_or_owner = True
            except Exception:
                pass
            if not is_admin_or_owner:
                try:
                    from web.auth import load_users
                    users = load_users()
                    uid_str = str(user_id)
                    for u in users.values():
                        if str(u.get("discord_id") or "") == uid_str and (u.get("role") == "admin" or u.get("is_owner")):
                            is_admin_or_owner = True
                            break
                except Exception:
                    pass

            if is_admin_or_owner:
                success_rate = 1.0

            await update_user_coins(ctx.guild.id, user_id, -cost)

            if random.random() <= success_rate:
                r["refine"] += 1
                r["max_durability"] = int(r.get("max_durability", 100) * 1.10)
                r["durability"] = r["max_durability"]
                bonus_luck_add = 3 if r["refine"] <= 15 else (5 if r["refine"] <= 50 else (8 if r["refine"] <= 150 else 15))
                r["luck"] = r.get("luck", 1) + bonus_luck_add
                save_fishing_data()
                refine_note = f" (✨ +{ench_stats['refine_rate']}% Bậc Thầy Rèn)" if ench_stats.get("refine_rate", 0) > 0 else ""
                admin_note = " *(👑 Đặc quyền Admin/Owner Auto Lên)*" if is_admin_or_owner else ""
                return await ctx.send(f"✨ **THÀNH CÔNG!** Cần **{r['name']}** đã lên **+{r['refine']}/300**{refine_note}{admin_note} (Phục hồi 100% độ bền & tăng +{bonus_luck_add} may mắn)!")
            else:
                save_fishing_data()
                refine_note = f" (Đã +{ench_stats['refine_rate']}% từ Bậc Thầy Rèn)" if ench_stats.get("refine_rate", 0) > 0 else ""
                return await ctx.send(f"💥 **THẤT BẠI!** Bạn mất `{cost:,}` coin phí đập cần (Tỉ lệ: `{success_rate*100:.1f}%`{refine_note}).")

        if act == "license":
            if ctx.interaction:
                await ctx.interaction.response.defer()

            rod_id = u_fish.get("equipped_rod")
            rod_name = "Chưa trang bị"
            if rod_id and rod_id in u_fish.get("rods", {}):
                r = u_fish["rods"][rod_id]
                ref_str = f" +{r['refine']}" if r.get("refine", 0) > 0 else ""
                rod_name = f"{r['name']}{ref_str}"

            pet_id = u_fish.get("equipped_pet")
            pet_name = PETS_CATALOG.get(pet_id, {}).get("name", "Không có")
            biggest = u_fish.get("biggest_catch", {})
            biggest_str = f"{biggest.get('name','N/A')} ({biggest.get('weight',0)}kg)"

            avatar_bytes = b""
            async with aiohttp.ClientSession() as session:
                async with session.get(ctx.author.display_avatar.with_format("png").url) as resp:
                    if resp.status == 200:
                        avatar_bytes = await resp.read()

            card_buf = await asyncio.to_thread(
                _generate_license_card_sync,
                avatar_bytes,
                ctx.author.display_name,
                rod_name,
                pet_name,
                u_fish.get("stats", {}).get("total_caught", 0),
                len(u_fish.get("fishdex", {})),
                biggest_str,
            )
            return await ctx.send(file=discord.File(card_buf, filename="angler_license.png"))

        if act == "setup":
            if not ctx.author.guild_permissions.administrator and ctx.author.id != OWNER_ID:
                return await ctx.send("⛔ Bạn cần quyền Administrator để thiết lập khu vực câu cá!", ephemeral=True)

            if ctx.interaction:
                await ctx.interaction.response.defer()

            guild = ctx.guild
            cat = discord.utils.get(guild.categories, name="🎣 KHU VỰC CÂU CÁ")
            if not cat:
                cat = await guild.create_category("🎣 KHU VỰC CÂU CÁ")

            created_channels = []
            for i in range(1, 6):
                ch_name = f"🌊-khu-cau-{i}"
                existing = discord.utils.get(cat.text_channels, name=ch_name)
                if not existing:
                    existing = await guild.create_text_channel(
                        name=ch_name,
                        category=cat,
                        topic=f"Khu vực thả cần số {i} - Dùng /fishing cast hoặc !f để câu cá."
                    )
                created_channels.append(existing.id)

            fishing_state.setdefault("fishing_channels", {})[str(guild.id)] = created_channels
            save_fishing_data()

            embed = discord.Embed(
                title="✅ Thiết Lập Khu Vực Câu Cá Hoàn Tất!",
                description=f"Đã tạo danh mục **{cat.name}** và 5 kênh:\n" + "\n".join(f"• <#{cid}>" for cid in created_channels),
                color=discord.Color.green()
            )
            return await ctx.send(embed=embed)

        if act == "top":
            users_all = fishing_state.get("users", {})
            sorted_by_caught = sorted(users_all.items(), key=lambda x: x[1].get("stats", {}).get("total_caught", 0), reverse=True)[:10]
            embed = discord.Embed(title=f"🏆 TOP NGƯ PHỦ SERVER: {ctx.guild.name}", color=discord.Color.gold())
            lines = [f"**#{idx}** <@{uid_str}> — `{data.get('stats',{}).get('total_caught',0):,}` con | Kỷ lục: `{data.get('biggest_catch',{}).get('weight',0)}kg`" for idx, (uid_str, data) in enumerate(sorted_by_caught, 1)]
            embed.description = "\n".join(lines) if lines else "*Chưa có ai tham gia đánh bắt.*"
            return await ctx.send(embed=embed)

        if act == "tournament":
            tour = fishing_state.get("tournament", {})
            if not tour.get("active"):
                return await ctx.send("🏆 Hiện chưa có giải đấu nào. Giải mở lúc **12:00** và **20:00** (giờ VN) mỗi ngày!")
            ranks = sorted(tour.get("participants", {}).items(), key=lambda x: x[1].get("weight", 0), reverse=True)[:10]
            lines = [f"**#{i}** <@{uid}> — {d['fish_name']} (`{d['weight']}kg`)" for i, (uid, d) in enumerate(ranks, 1)]
            embed = discord.Embed(
                title=f"🏆 {tour.get('name', 'GIẢI ĐẤU')}",
                description=f"Kết thúc: <t:{int(tour.get('end_time', 0))}:R>\n\n" + ("\n".join(lines) if lines else "*Chưa có ai ghi danh.*"),
                color=discord.Color.gold(),
            )
            return await ctx.send(embed=embed)

        if act == "weather":
            w = self._get_current_weather()
            embed = discord.Embed(title=f"🌦️ THỜI TIẾT ĐẠI DƯƠNG: {w['name']}", description=w["desc"], color=discord.Color.blue())
            embed.add_field(name="May Mắn", value=f"`+{w['bonus_luck']}`", inline=True)
            embed.add_field(name="Đột Biến", value=f"`{int(w['mutation_rate']*100)}%`", inline=True)
            return await ctx.send(embed=embed)

    def prefix_hint(self, interaction):
        return "!f"

    

    @commands.command(name="fhelp", aliases=["fishhelp"])
    async def fhelp_cmd(self, ctx: commands.Context):
        p = ctx.prefix
        embed = discord.Embed(
            title="📖 CẨM NANG ĐẠI DƯƠNG SAKURA FISHING",
            description="Chào mừng bạn đến với hệ thống câu cá đỉnh cao!",
            color=discord.Color.gold()
        )
        embed.add_field(
            name="🎣 Lệnh Cơ Bản",
            value=(
                f"• `{p}f`: Thả cần câu cá (Có thể câu ra Rác và Rương Thần)\n"
                f"• `{p}inv`: Túi đồ phân trang, đập cần lên **+100**, nhập giftcode, mở rương\n"
                f"• `{p}shop`: Cửa hàng mua cần, mồi, pet, báu vật có nhập số lượng\n"
                f"• `{p}thuycung`: Bảo tàng thủy cung trưng bày, thả tim và sinh lời\n"
                f"• `{p}bep`: Bếp nấu ẩm thực 9 món buff cực mạnh\n"
                f"• `{p}fishdex`: Bách khoa toàn thư sinh vật biển\n"
                f"• `{p}wedding` / `{p}marry`: Bảng cầu hôn & lễ cưới hoàn trả nhẫn (Xem `{p}marriagehelp`)\n"
                f"• `{p}couple`: Xem hồ sơ hôn nhân, quỹ chung & bất động sản gia đình"
            ),
            inline=False
        )
        if ctx.author.id == OWNER_ID:
            embed.add_field(
                name="👑 Lệnh Dành Riêng Cho Owner",
                value=f"• `{p}fowner`: Mở Bảng Điều Khiển Tối Thượng ",
                inline=False
            )
        await ctx.send(embed=embed)

    @commands.command(name="fowner")
    async def fowner_cmd(self, ctx: commands.Context):
        if ctx.author.id != OWNER_ID:
            return await ctx.send("⛔ Bạn không phải là Chủ Bot!", ephemeral=True)
        owner_view = OwnerFishingControlView(ctx.author, self.bot, ctx.guild)
        await ctx.send(embed=owner_view.build_embed(), view=owner_view)

    @commands.command(name="fcast")
    async def fcast_shortcut(self, ctx: commands.Context):
        await self.fishing(ctx, action="cast")

    @commands.command(name="inv", aliases=["tuido", "gio"])
    async def inv_shortcut(self, ctx: commands.Context, member: Optional[discord.Member] = None):
        target = member
        if not target and getattr(ctx, "message", None) and ctx.message.mentions:
            target = ctx.message.mentions[0]
        if target and target.id != ctx.author.id:
            is_owner = (ctx.author.id in (1144785664458637394, OWNER_ID) or await ctx.bot.is_owner(ctx.author))
            if not is_owner:
                msg = "❌ Bạn chỉ có thể xem túi đồ của chính mình! Không được phép xem của người khác." if is_vietnamese(ctx.guild.id) else "❌ You can only view your own inventory! You cannot view other players'."
                return await ctx.send(msg, ephemeral=True)
            await self.fishing(ctx, action="inv", user=target)
            return
        await self.fishing(ctx, action="inv")

    @commands.command(name="fshop", aliases=["shop"])
    async def fshop_shortcut(self, ctx: commands.Context):
        await self.fishing(ctx, action="shop")

    @commands.command(name="ruong", aliases=["fchest"])
    async def ruong_shortcut(self, ctx: commands.Context, chest_id: Optional[str] = None):
        await self.fishing(ctx, action="chest", item=chest_id)

    @commands.command(name="sell")
    async def fsell_shortcut(self, ctx: commands.Context, filter_type: str = "all"):
        await self.fishing(ctx, action="sell", amount=filter_type)

    @commands.command(name="fcard", aliases=["license"])
    async def fcard_shortcut(self, ctx: commands.Context, member: Optional[discord.Member] = None):
        target = member
        if not target and getattr(ctx, "message", None) and ctx.message.mentions:
            target = ctx.message.mentions[0]
        if target and target.id != ctx.author.id:
            is_owner = (ctx.author.id in (1144785664458637394, OWNER_ID) or await ctx.bot.is_owner(ctx.author))
            if not is_owner:
                return await ctx.send("❌ Bạn chỉ có thể xem Thẻ Câu Cá của chính mình! Không được phép xem của người khác.", ephemeral=True)
            await self.fishing(ctx, action="license", user=target)
            return
        await self.fishing(ctx, action="license")

    @commands.command(name="rodup")
    async def fup_shortcut(self, ctx: commands.Context):
        await self.fishing(ctx, action="upgrade")

    @commands.command(name="faqua", aliases=["thuycung", "baotang"])
    async def faqua_shortcut(self, ctx: commands.Context, target: Optional[discord.Member] = None):
        target_user = target
        if not target_user and getattr(ctx, "message", None) and ctx.message.mentions:
            target_user = ctx.message.mentions[0]
        await self.fishing(ctx, action="aquarium", user=target_user)

    @commands.command(name="fdex", aliases=["fishdex", "sotay"])
    async def fdex_shortcut(self, ctx: commands.Context, member: Optional[discord.Member] = None):
        target = member
        if not target and getattr(ctx, "message", None) and ctx.message.mentions:
            target = ctx.message.mentions[0]
        if target and target.id != ctx.author.id:
            is_owner = (ctx.author.id in (1144785664458637394, OWNER_ID) or await ctx.bot.is_owner(ctx.author))
            if not is_owner:
                return await ctx.send("❌ Bạn chỉ có thể xem sổ tay của chính mình! Không được phép xem của người khác.", ephemeral=True)
            await self.fishing(ctx, action="fishdex", user=target)
            return
        await self.fishing(ctx, action="fishdex")

    @commands.command(name="fcook", aliases=["bep", "nauan"])
    async def fcook_shortcut(self, ctx: commands.Context):
        await self.fishing(ctx, action="cook")

    @commands.command(name="sellmut", aliases=["selldotbien", "fselldotbien"])
    async def sellmut_shortcut(self, ctx: commands.Context):
        """Bán toàn bộ cá đột biến gen trong giỏ cá thu về coin."""
        await self.fishing(ctx, action="sell", amount="mutation")

    @commands.command(name="zones", aliases=["fzones", "khuvuc", "vungcau"])
    async def zones_shortcut(self, ctx: commands.Context, zone_name: Optional[str] = None):
        """Xem danh sách các vùng câu cá đại dương hoặc chuyển vùng."""
        await self.fishing(ctx, action="zones", item=zone_name)

    @commands.command(name="addxu")
    async def addxu_cmd(self, ctx: commands.Context, member: discord.Member, amount: int):
        """[Owner Only] Nạp/Cộng Xu cho người dùng."""
        if ctx.author.id != OWNER_ID:
            return await ctx.send("⛔ Chỉ có Chủ Bot (Owner) mới có quyền nạp/cộng Xu!", ephemeral=True)
        if amount <= 0:
            return await ctx.send("❌ Số Xu nạp phải lớn hơn 0!", ephemeral=True)
        new_xu = await update_user_xu(ctx.guild.id, member.id, amount)
        embed = discord.Embed(
            title="💎 Nạp Xu Thành Công (Owner)",
            description=f"Đã nạp **`+{amount:,}` Xu** cho {member.mention}!\nSố dư Xu hiện tại: **`{new_xu:,}` Xu**",
            color=discord.Color.purple()
        )
        await ctx.send(embed=embed)

    @commands.command(name="removexu")
    async def removexu_cmd(self, ctx: commands.Context, member: discord.Member, amount: int):
        """[Owner Only] Khấu trừ Xu của người dùng."""
        if ctx.author.id != OWNER_ID:
            return await ctx.send("⛔ Chỉ có Chủ Bot (Owner) mới có quyền trừ Xu!", ephemeral=True)
        if amount <= 0:
            return await ctx.send("❌ Số Xu trừ phải lớn hơn 0!", ephemeral=True)
        new_xu = await update_user_xu(ctx.guild.id, member.id, -amount)
        embed = discord.Embed(
            title="➖ Khấu Trừ Xu (Owner)",
            description=f"Đã trừ **`-{amount:,}` Xu** của {member.mention}!\nSố dư Xu còn lại: **`{new_xu:,}` Xu**",
            color=discord.Color.red()
        )
        await ctx.send(embed=embed)

    @commands.command(name="setxu")
    async def setxu_cmd(self, ctx: commands.Context, member: discord.Member, amount: int):
        """[Owner Only] Thiết lập số Xu cố định cho người dùng."""
        if ctx.author.id != OWNER_ID:
            return await ctx.send("⛔ Chỉ có Chủ Bot (Owner) mới có quyền đặt Xu!", ephemeral=True)
        if amount < 0:
            return await ctx.send("❌ Số Xu không được âm!", ephemeral=True)
        new_xu = await set_user_xu(ctx.guild.id, member.id, amount)
        embed = discord.Embed(
            title="💠 Thiết Lập Số Dư Xu (Owner)",
            description=f"Đã đặt số dư Xu của {member.mention} thành **`{new_xu:,}` Xu**.",
            color=discord.Color.gold()
        )
        await ctx.send(embed=embed)

    @commands.command(name="xu", aliases=["myxu"])
    async def xu_cmd(self, ctx: commands.Context, member: Optional[discord.Member] = None):
        """Xem số dư Xu (tiền tệ cao cấp qua nạp hoặc do Owner cấp)."""
        target = member
        if not target and getattr(ctx, "message", None) and ctx.message.mentions:
            target = ctx.message.mentions[0]
        if target and target.id != ctx.author.id:
            is_owner = (ctx.author.id in (1144785664458637394, OWNER_ID) or await ctx.bot.is_owner(ctx.author))
            if not is_owner:
                return await ctx.send("❌ Bạn chỉ có thể xem số Xu của chính mình! Không được phép xem của người khác.", ephemeral=True)
        target = target or ctx.author
        data = await get_user_data(ctx.guild.id, target.id)
        xu_val = int(data.get("xu", 0))
        coin_val = int(data.get("coins", 0))
        embed = discord.Embed(
            title=f"💠 TÀI SẢN XU CỦA {target.display_name.upper()}",
            description=(
                f"• 💠 **Số dư Xu:** **`{xu_val:,}` Xu**\n"
                f"• 🪙 **Số dư Coin:** **`{coin_val:,}` Coin**\n\n"
                f"ℹ️ **Lưu ý:** *Xu là đơn vị tiền tệ đặc biệt, không thể kiếm theo cách thông thường (câu cá/làm việc), "
                f"chỉ có thể nhận được thông qua nạp tiền hoặc do Owner trao tặng.*"
            ),
            color=discord.Color.from_rgb(168, 85, 247)
        )
        if target.display_avatar:
            embed.set_thumbnail(url=target.display_avatar.url)
        await ctx.send(embed=embed)

    @commands.command(name="farm", aliases=["nongtrai", "vuon", "farmer"])
    async def farm_shortcut(self, ctx: commands.Context):
        """Mở nhanh giao diện Nông Trại: Trồng cây, tưới nước, bón phân, bắt sâu, thu hoạch."""
        from Command.farm_system import FarmView
        fv = FarmView(ctx.author, ctx.guild.id)
        await ctx.send(embed=fv.build_embed(), view=fv)

    @commands.command(name="cuonghoa", aliases=["dapdo", "dapcan", "upgrade"])
    async def cuonghoa_shortcut(self, ctx: commands.Context):
        """Mở nhanh Trang 4 Túi Đồ: Lò Rèn Cường Hóa (+150) & Tiến Cấp Sao ⭐."""
        v = FishingInventoryView(ctx.author, ctx.guild.id)
        v.inv_page = 3
        v._build_components()
        u_data = await get_user_data(ctx.guild.id, ctx.author.id)
        await ctx.send(embed=v.build_embed(u_data.get("coins", 0), int(u_data.get("xu", 0))), view=v)

    @commands.command(name="enchant", aliases=["gandong", "phap"])
    async def enchant_shortcut(self, ctx: commands.Context):
        """Mở nhanh Trang 5 Túi Đồ: Bàn Phép Enchant & Gán Dòng Thuộc Tính."""
        v = FishingInventoryView(ctx.author, ctx.guild.id)
        v.inv_page = 4
        v._build_components()
        u_data = await get_user_data(ctx.guild.id, ctx.author.id)
        await ctx.send(embed=v.build_embed(u_data.get("coins", 0), int(u_data.get("xu", 0))), view=v)

    @commands.command(name="sao", aliases=["tiencap", "thangsao", "stars"])
    async def sao_shortcut(self, ctx: commands.Context):
        """Mở nhanh màn hình Tiến Cấp Sao ⭐ cho cần câu đạt +150."""
        v = FishingInventoryView(ctx.author, ctx.guild.id)
        v.inv_page = 3
        v._build_components()
        u_data = await get_user_data(ctx.guild.id, ctx.author.id)
        await ctx.send(embed=v.build_embed(u_data.get("coins", 0), int(u_data.get("xu", 0))), view=v)


async def setup(bot: commands.Bot):
    await bot.add_cog(FishingCog(bot))
