from Check.i18n import t, is_vietnamese
import json
import math
import os
import time
from pathlib import Path
from typing import Dict, List, Optional, Any

import discord
from discord import app_commands
from discord.ext import commands

from data.database import get_user_data, update_user_coins, update_user_xu

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
ACHIEVEMENTS_FILE = DATA_DIR / "user_achievements.json"

ACHIEVEMENTS_CATALOG: Dict[str, Dict[str, Any]] = {}

def _register(ach_id: str, name: str, category: str, desc: str, coins: int, xu: int = 0, title: str = "", icon: str = "🏆"):
    ACHIEVEMENTS_CATALOG[ach_id] = {
        "id": ach_id,
        "name": name,
        "category": category,
        "desc": desc,
        "reward_coins": coins,
        "reward_xu": xu,
        "reward_title": title,
        "icon": icon
    }

_register("fish_first", "Nhát Giật Đầu Đời", "fishing", "Câu thành công chú cá đầu tiên", 5000, 0, "Tập Sự Thả Câu", "🎣")
_register("fish_10", "Ngư Dân Mới Vào Nghề", "fishing", "Câu tích lũy được 10 con cá", 10000, 0, "", "🐟")
_register("fish_50", "Tay Lưới Điêu Luyện", "fishing", "Câu tích lũy được 50 con cá", 25000, 1, "Thợ Săn Ven Bờ", "🎣")
_register("fish_100", "Bậc Thầy Thả Neo", "fishing", "Câu tích lũy được 100 con cá", 50000, 2, "Ngư Phủ Lão Luyện", "🎏")
_register("fish_250", "Chuyên Gia Đánh Bắt", "fishing", "Câu tích lũy được 250 con cá", 100000, 5, "", "⛵")
_register("fish_500", "Chúa Tể Duyên Hải", "fishing", "Câu tích lũy được 500 con cá", 250000, 10, "Kình Ngư Đại Dương", "🌊")
_register("fish_1000", "Hải Vương Giáng Thế", "fishing", "Câu tích lũy được 1,000 con cá", 1000000, 50, "Đại Đương Chủ", "🔱")

_register("fish_rare_first", "Cá Hiếm Lên Bờ", "fishing", "Câu được 1 con cá bậc Rare trở lên", 15000, 1, "", "✨")
_register("fish_epic_first", "Huyền Thoại Trỗi Dậy", "fishing", "Câu được 1 con cá bậc Epic", 30000, 2, "", "💜")
_register("fish_legendary_first", "Bóng Ma Biển Sâu", "fishing", "Câu được 1 con cá bậc Legendary", 75000, 5, "Săn Huyền Thoại", "🌟")
_register("fish_mythic_first", "Thần Thoại Vực Thẳm", "fishing", "Câu được 1 con cá bậc Mythic", 200000, 10, "Thần Hải Kỵ Sĩ", "🔮")
_register("fish_godly_first", "Thiên Thần Biển Cả", "fishing", "Câu được 1 con cá bậc Godly", 500000, 30, "Chế Ngự Thần Tộc", "👑")

_register("fish_mutant_first", "Biến Dị Kỳ Dị", "fishing", "Câu được con cá đột biến đầu tiên", 20000, 1, "", "🧬")
_register("fish_mutant_10", "Phòng Thí Nghiệm Đáy Biển", "fishing", "Sở hữu 10 cá thể đột biến gen", 80000, 5, "Nhà Sinh Học Biển", "🌈")
_register("fish_mutant_gold", "Vảy Vàng Lấp Lánh", "fishing", "Câu trúng cá mang đột biến Hoàng Kim", 100000, 5, "Bàn Tay Vàng", "🪙")
_register("fish_mutant_void", "Hắc Ám Hư Không", "fishing", "Câu trúng cá đột biến Hư Không Hắc Ám", 250000, 15, "Kẻ Xuyên Không", "🌌")

_register("rod_refine_10", "Búa Rèn Bắt Đầu", "fishing", "Cường hóa cần câu lên cấp +10", 30000, 1, "", "🔨")
_register("rod_refine_30", "Thép Rèn Tinh Luyện", "fishing", "Cường hóa cần câu lên cấp +30", 75000, 3, "", "⚔️")
_register("rod_refine_50", "Hào Quang Lò Rèn", "fishing", "Cường hóa cần câu lên cấp +50", 150000, 5, "Thợ Rèn Bậc Thầy", "🔥")
_register("rod_refine_100", "Tuyệt Đỉnh Cương Nhu", "fishing", "Cường hóa cần câu lên cấp +100", 500000, 20, "Vạn Lôi Đúc Cần", "⚡")
_register("rod_refine_150", "Bất Diệt Cần Thần", "fishing", "Chạm mốc cường hóa tối đa +150", 2000000, 100, "Thần Binh Xuất Thế", "💎")

_register("rod_star_1", "Ánh Sao Đầu Tiên", "fishing", "Thăng cấp sao cần câu lên ⭐x1", 100000, 5, "", "⭐")
_register("rod_star_5", "Ngũ Tinh Liên Châu", "fishing", "Thăng cấp sao cần câu lên ⭐x5", 300000, 15, "Tinh Tú Cần Thủ", "🌟")
_register("rod_star_10", "Thập Tinh Hội Tụ", "fishing", "Thăng cấp sao cần câu lên ⭐x10", 750000, 30, "", "🌌")
_register("rod_star_20", "Vũ Trụ Thần Cần", "fishing", "Đạt đỉnh cao tinh tú 20 sao ⭐x20", 3000000, 150, "Tinh Thần Hải Chủ", "🌠")

_register("rod_enchant_first", "Khai Mở Phù Chú", "fishing", "Khảm thành công phù phép đầu tiên cho cần câu", 25000, 1, "", "📜")
_register("rod_enchant_max", "Ngũ Phép Hoàn Mỹ", "fishing", "Mở đủ 5 ô phù phép và khảm kín dòng", 300000, 10, "Phù Thủy Thả Câu", "✨")

_register("fish_qte_first", "Phản Xạ Thần Tốc", "fishing", "Hoàn thành mini-game kéo cá QTE thành công", 15000, 0, "", "🎯")
_register("fish_qte_10", "Tay Lái Siêu Hạng", "fishing", "Chiến thắng 10 lần chạm trán QTE", 60000, 3, "Thợ Kéo Cước", "🎣")

_register("aquarium_build", "Thế Giới Dưới Nước", "fishing", "Mở khóa Thủy Cung cá nhân", 20000, 1, "Chủ Thủy Cung", "🐠")
_register("aquarium_slots_12", "Thủy Cung Mở Rộng", "fishing", "Nâng cấp Thủy Cung lên 12 ô trưng bày", 60000, 3, "", "🏛️")
_register("aquarium_slots_24", "Đại Dương Thu Nhỏ", "fishing", "Nâng cấp Thủy Cung lên tối đa 24 ô", 200000, 10, "Viện Trưởng Thủy Tộc", "🏰")
_register("aquarium_likes_10", "Thủy Cung Được Yêu Thích", "fishing", "Thủy cung nhận được 10 lượt thích từ bạn bè", 50000, 2, "Ngôi Sao Đáy Biển", "💖")
_register("aquarium_revenue_100k", "Vé Tham Quan Đắt Khách", "fishing", "Thu được tổng cộng 100,000 coins tiền vé", 80000, 4, "", "🎟️")

_register("fish_chest_open", "Kho Báu Đáy Biển", "fishing", "Câu trúng và mở chiếc rương kho báu đầu tiên", 30000, 2, "Thám Hiểm Biển Sâu", "📦")
_register("fish_trash_10", "Người Dọn Rác Biển", "fishing", "Câu phải 10 món rác thải và tái chế chúng", 20000, 1, "Chiến Binh Môi Trường", "♻️")
_register("fish_cook_first", "Bếp Trưởng Hải Sản", "fishing", "Chế biến thành công món ăn đầu tiên từ cá", 20000, 1, "Đầu Bếp Ven Biển", "🍲")
_register("fish_cook_10", "Bữa Tiệc Thịnh Soạn", "fishing", "Nấu thành công 10 món ẩm thực ngư dân", 80000, 3, "Bếp Trưởng 5 Sao", "🍱")
_register("fish_all_zones", "Vượt Mọi Trùng Khơi", "fishing", "Khám phá và thả câu ở tất cả 6 vùng biển", 150000, 8, "Nhà Du Hành Biển Cả", "🧭")

_register("mine_first", "Nhát Cuốc Đầu Tiên", "mining", "Đào thành công quặng khoáng sản đầu tiên", 5000, 0, "Thợ Mỏ Tập Sự", "⛏️")
_register("mine_10", "Người Khai Mỏ", "mining", "Đào được 10 viên khoáng sản", 10000, 0, "", "🪨")
_register("mine_50", "Phu Mỏ Chăm Chỉ", "mining", "Đào được 50 viên khoáng sản", 25000, 1, "", "⛏️")
_register("mine_100", "Đào Sâu Lòng Đất", "mining", "Đào được 100 viên khoáng sản", 50000, 2, "Thợ Khoan Địa Chất", "🧗")
_register("mine_500", "Cỗ Máy Đào Quặng", "mining", "Đào được 500 viên khoáng sản", 200000, 8, "Bá Chủ Hầm Mỏ", "🌋")
_register("mine_1000", "Trái Tim Núi Đá", "mining", "Đào được 1,000 viên khoáng sản", 750000, 30, "Thần Mỏ Thái Cổ", "⛰️")

_register("ore_iron_first", "Kỷ Nguyên Sắt Thép", "mining", "Khai thác được Quặng Sắt đầu tiên", 10000, 0, "", "⛓️")
_register("ore_gold_first", "Cơn Sốt Vàng Ròng", "mining", "Khai thác được Quặng Vàng đầu tiên", 20000, 1, "", "🪙")
_register("gem_diamond_first", "Ánh Kim Cương", "mining", "Đào trúng Viên Kim Cương lấp lánh", 50000, 3, "Đào Kim Cương", "💎")
_register("gem_emerald_first", "Lục Bảo Xanh Ngát", "mining", "Đào trúng Ngọc Lục Bảo", 40000, 2, "", "💚")
_register("gem_ruby_first", "Hồng Ngọc Rực Lửa", "mining", "Đào trúng Hồng Ngọc Ruby quý giá", 60000, 3, "", "❤️")
_register("gem_sapphire_first", "Lam Ngọc Biển Cả", "mining", "Đào trúng Lam Ngọc Sapphire", 60000, 3, "", "💙")
_register("ore_obsidian_first", "Hắc Diệu Thạch Cứng Cáp", "mining", "Phá vỡ và thu thập Hắc Diệu Thạch", 40000, 2, "", "🖤")
_register("ore_ancient_debris", "Dấu Vết Cổ Đại", "mining", "Đào trúng Mảnh Vỡ Cổ Đại Netherite", 100000, 5, "Khai Quật Cổ Đại", "🔥")
_register("ore_heart_of_earth", "Trái Tim Của Đất", "mining", "Đào trúng khoáng vật Thần Thoại: Trái Tim Lòng Đất", 300000, 15, "Khai Sáng Địa Cầu", "💖")
_register("ore_void_singularity", "Hố Đen Vô Tận", "mining", "Đào trúng khoáng vật Godly: Điểm Dị Thường Hư Không", 1000000, 50, "Chinh Phục Vực Hư", "🌌")

_register("mine_mutant_first", "Quặng Đột Biến", "mining", "Đào trúng khoáng sản mang gen đột biến", 20000, 1, "", "🧬")
_register("mine_mutant_radioactive", "Nhiễm Phóng Xạ", "mining", "Đào trúng quặng đột biến Phóng Xạ Cực Độc", 75000, 4, "Chiến Binh Hạt Nhân", "☢️")
_register("mine_mutant_cosmic", "Bụi Sao Thiên Thể", "mining", "Đào trúng quặng đột biến Tinh Tú Thiên Thể", 250000, 12, "Nhà Thiên Văn Đào Mỏ", "🌠")

_register("pick_refine_10", "Mũi Cuốc Sắc Bén", "mining", "Cường hóa cuốc đào lên +10", 30000, 1, "", "🔨")
_register("pick_refine_50", "Cuốc Vàng Rực Lửa", "mining", "Cường hóa cuốc đào lên +50", 150000, 5, "Đại Phu Mỏ", "🔥")
_register("pick_refine_100", "Cuốc Thần Xuyên Phá", "mining", "Cường hóa cuốc đào lên +100", 500000, 20, "Phá Sơn Đoạt Thạch", "⚡")
_register("pick_refine_150", "Cuốc Thần Vũ Trụ", "mining", "Cường hóa cuốc đào đạt cực hạn +150", 2000000, 100, "Vạn Vật Băng Hoại", "🌌")

_register("pick_star_1", "Sao Mỏ Đầu Tiên", "mining", "Thăng cấp sao cuốc đào lên ⭐x1", 100000, 5, "", "⭐")
_register("pick_star_10", "Sao Sáng Đáy Hang", "mining", "Thăng cấp sao cuốc đào lên ⭐x10", 750000, 30, "", "🌟")
_register("pick_star_20", "Tinh Tú Địa Vương", "mining", "Đạt tối đa 20 sao cuốc đào ⭐x20", 3000000, 150, "Địa Vương Tinh Thần", "👑")

_register("mine_tnt_use", "Nổ Tung Đá Cứng", "mining", "Sử dụng Thuốc nổ TNT khai thác mỏ", 20000, 1, "Chuyên Gia Thuốc Nổ", "💣")
_register("mine_fuel_use", "Máy Khoan Thần Tốc", "mining", "Dùng Nhiên liệu máy khoan giảm thời gian hồi chiêu", 20000, 1, "", "⛽")
_register("mine_lantern_use", "Ánh Sáng Hầm Tối", "mining", "Thắp Đèn Lồng Thợ Mỏ tăng vận may khai khoáng", 25000, 1, "", "🏮")

_register("mine_qte_perfect", "Nhát Búa Chuẩn Xác", "mining", "Hoàn thành mini-game gõ điểm yếu đá QTE", 20000, 1, "Thợ Tách Đá Hoàn Mỹ", "🎯")
_register("museum_open", "Viện Trưng Bày Khoáng Sản", "mining", "Mở khóa Viện Bảo Tàng Địa Chất", 30000, 1, "Giám Đốc Bảo Tàng", "🏛️")
_register("museum_slots_18", "Khoáng Vật Đại Hội", "mining", "Mở khóa 18 ô trưng bày mẫu địa chất", 150000, 8, "", "💎")
_register("museum_revenue_50k", "Vé Xem Đá Quý", "mining", "Thu được 50,000 coins tiền vé tham quan bảo tàng", 60000, 3, "", "🎟️")
_register("mine_all_zones", "Hành Trình Lòng Đất", "mining", "Đặt chân và khai thác tại tất cả 6 tầng hầm mỏ", 150000, 8, "Kẻ Khai Mở Địa Giới", "🗺️")

_register("farm_plant_first", "Mầm Sống Đầu Tiên", "farming", "Gieo hạt giống đầu tiên xuống ô đất", 5000, 0, "Bác Nông Dân Trẻ", "🌱")
_register("farm_harvest_first", "Mùa Gặt Khởi Đầu", "farming", "Thu hoạch nông sản chín đầu tiên", 5000, 0, "", "🌾")
_register("farm_harvest_50", "Nông Trại Đầy Ắp", "farming", "Thu hoạch tích lũy 50 nông sản", 25000, 1, "Lão Nông Chăm Chỉ", "🥕")
_register("farm_harvest_200", "Vựa Lúa Vàng", "farming", "Thu hoạch tích lũy 200 nông sản", 100000, 5, "Trang Trại Phú Quý", "🌽")
_register("farm_harvest_1000", "Thần Nông Tái Sinh", "farming", "Thu hoạch tích lũy 1,000 nông sản", 500000, 25, "Đại Địa Thần Nông", "🚜")

_register("crop_wheat", "Bánh Mì Thơm Lừng", "farming", "Thu hoạch thành công Lúa Mì", 10000, 0, "", "🍞")
_register("crop_carrot", "Cà Rốt Ngọt Lịm", "farming", "Thu hoạch thành công Cà Rốt", 10000, 0, "", "🥕")
_register("crop_potato", "Khoai Tây Vàng Ươm", "farming", "Thu hoạch thành công Khoai Tây", 10000, 0, "", "🥔")
_register("crop_strawberry", "Dâu Tây Đỏ Mọng", "farming", "Thu hoạch quả Dâu Tây", 15000, 1, "", "🍓")
_register("crop_watermelon", "Dưa Hấu Giải Nhiệt", "farming", "Thu hoạch quả Dưa Hấu to tròn", 20000, 1, "", "🍉")
_register("crop_pumpkin", "Bí Ngô Khổng Lồ", "farming", "Thu hoạch Bí Ngô Mùa Thu", 20000, 1, "", "🎃")
_register("crop_rose", "Đóa Hồng Rực Rỡ", "farming", "Thu hoạch Bông Hoa Hồng Tình Yêu", 25000, 1, "Người Trồng Hoa", "🌹")
_register("crop_sunflower", "Hoa Hướng Dương", "farming", "Thu hoạch Hoa Hướng Dương đón nắng", 25000, 1, "", "🌻")

_register("farm_mutant_first", "Cây Trồng Biến Dị", "farming", "Thu hoạch được nông sản đột biến đầu tiên", 25000, 1, "Nhà Làm Vườn Tài Ba", "🧬")
_register("farm_mutant_golden", "Bông Lúa Hoàng Kim", "farming", "Thu hoạch nông sản đột biến Hoàng Kim", 80000, 4, "", "🪙")
_register("farm_mutant_diamond", "Quả Ngọt Kim Cương", "farming", "Thu hoạch nông sản đột biến Kim Cương", 150000, 8, "Nhà Vườn Thượng Lưu", "💎")
_register("farm_mutant_cosmic", "Nông Sản Tinh Vân", "farming", "Thu hoạch nông sản đột biến Tinh Vân Vũ Trụ", 350000, 20, "Trang Trại Vũ Trụ", "🌌")

_register("farm_water_10", "Dòng Nước Mát Lành", "farming", "Tưới nước cho cây trồng 10 lần", 15000, 0, "", "💧")
_register("farm_water_100", "Mưa Rào Quanh Năm", "farming", "Tưới nước cho các ô đất 100 lần", 80000, 3, "Thủy Tề Đồng Ruộng", "🌧️")
_register("farm_fertilize", "Đất Đai Màu Mỡ", "farming", "Sử dụng phân bón hóa học hoặc hữu cơ cho cây", 15000, 0, "", "🧪")
_register("farm_pest_catch_first", "Bắt Sâu Diệt Bọ", "farming", "Tiêu diệt sâu bọ hại cây đầu tiên", 10000, 0, "Bảo Vệ Mùa Màng", "🐛")
_register("farm_pest_catch_20", "Thợ Săn Sâu Bọ", "farming", "Tiêu diệt 20 con sâu bọ phá hoại", 50000, 2, "Khắc Tinh Sâu Hại", "🦗")

_register("farm_plots_8", "Mở Rộng Điền Trang", "farming", "Mở khóa trang trại lên 8 ô đất", 50000, 2, "", "🏡")
_register("farm_plots_16", "Đại Điền Chủ", "farming", "Mở khóa toàn bộ 16 ô đất tối đa", 200000, 10, "Đại Phú Nông", "🏰")
_register("farm_greenhouse", "Nhà Kính Chống Bão", "farming", "Lắp đặt thành công lồng kính bảo vệ cây trồng", 50000, 2, "Kỹ Sư Nông Nghiệp", "🏡")

_register("farm_eat_crop", "Thưởng Thức Nông Sản", "farming", "Ăn hoa màu thu hoạch được để hồi phục độ bền cần", 15000, 0, "", "🍎")
_register("farm_sell_all_100k", "Mùa Màng Bội Thu", "farming", "Bán nông sản 1 lần thu về hơn 100,000 coins", 80000, 4, "", "💰")
_register("farm_cook_master", "Đại Tiệc Nông Gia", "farming", "Nấu món ăn kết hợp cả nông sản và cá biển", 50000, 2, "Vua Đầu Bếp Gia Đình", "🍲")
_register("farm_season_spring", "Xuân Về Hoa Nở", "farming", "Thu hoạch cây trồng trong Mùa Xuân", 20000, 1, "", "🌸")
_register("farm_season_summer", "Hè Sang Trái Ngọt", "farming", "Thu hoạch cây trồng trong Mùa Hè", 20000, 1, "", "☀️")
_register("farm_season_autumn", "Thu Vàng Lúa Chín", "farming", "Thu hoạch cây trồng trong Mùa Thu", 20000, 1, "", "🍂")
_register("farm_season_winter", "Đông Về Tuyết Phủ", "farming", "Chăm sóc cây sống sót qua Mùa Đông giá rét", 30000, 2, "Bất Khuất Trước Giá Lạnh", "❄️")

_register("casino_first_play", "Tập Tành Đỏ Đen", "casino_gacha", "Chơi ván casino hoặc gacha đầu tiên", 5000, 0, "", "🎲")
_register("casino_win_first", "Thần May Mắn Mỉm Cười", "casino_gacha", "Thắng ván cược đầu tiên", 10000, 0, "", "🍀")
_register("casino_win_streak_3", "Chuỗi Thắng Tam Phát", "casino_gacha", "Thắng 3 ván cược liên tiếp", 30000, 1, "", "🔥")
_register("casino_win_streak_5", "Vận Đỏ Khôn Cùng", "casino_gacha", "Thắng 5 ván cược liên tiếp", 100000, 5, "Bàn Tay Ma Thuật", "⚡")
_register("casino_win_streak_10", "Thần Bài Tái Thế", "casino_gacha", "Thắng 10 ván cược liên tiếp", 500000, 25, "Thần Bài Las Vegas", "👑")

_register("taixiu_win_100k", "Ăn Lớn Tài Xỉu", "casino_gacha", "Thắng cược hơn 100,000 coin trong 1 ván Tài Xỉu", 50000, 2, "", "🎲")
_register("taixiu_win_1m", "Tài Xỉu Triệu Phú", "casino_gacha", "Thắng cược hơn 1,000,000 coin trong 1 ván Tài Xỉu", 250000, 10, "Bá Chủ Chiếu Xúc Xắc", "💎")
_register("taixiu_win_10m", "Cá Cược Cực Hạn", "casino_gacha", "Thắng cược hơn 10,000,000 coin trong 1 ván Tài Xỉu", 1000000, 50, "Cổ Đông Casino", "🏆")

_register("baucua_win_triple", "Tam Hoa Quy Tụ", "casino_gacha", "Bầu cua lắc ra 3 mặt giống nhau ăn x3 tiền", 80000, 3, "Thần Rùa Bầu Cua", "🦀")
_register("baucua_play_50", "Dân Chơi Bầu Cua", "casino_gacha", "Chơi tích lũy 50 ván Bầu Cua", 50000, 2, "", "🦐")

_register("tarot_draw_first", "Lắng Nghe Vận Mệnh", "casino_gacha", "Rút quẻ bói bài Tarot đầu tiên", 10000, 0, "", "🃏")
_register("tarot_draw_10", "Nhà Chiêm Tinh Học", "casino_gacha", "Xem bói bài Tarot 10 lần", 40000, 2, "Nhà Tiên Tri", "🔮")
_register("tarot_fool", "Lá Bài The Fool", "casino_gacha", "Rút trúng lá bài The Fool (Chàng Khờ)", 30000, 1, "Kẻ Phiêu Lưu Tự Do", "🃏")
_register("tarot_death", "Lá Bài Cái Chết", "casino_gacha", "Rút trúng lá bài Death (Hồi Sinh Mới)", 30000, 1, "Tái Sinh Từ Tro Tàn", "💀")
_register("tarot_wheel", "Vòng Quay Số Phận", "casino_gacha", "Rút trúng lá bài Wheel of Fortune", 50000, 2, "Con Cưng Của Số Phận", "☸️")

_register("lottery_buy_first", "Vé Số Đổi Đời", "casino_gacha", "Mua tấm vé số may mắn đầu tiên", 10000, 0, "", "🎟️")
_register("lottery_buy_10", "Khách Quen Đại Lý", "casino_gacha", "Mua tích lũy 10 tấm vé số", 40000, 1, "", "🎫")
_register("lottery_win_any", "Trúng Giải Độc Đắc", "casino_gacha", "Trúng bất kỳ giải thưởng vé số nào", 100000, 5, "Vận May Gõ Cửa", "🎉")

_register("gacha_roll_10", "Duyên Phận Rút Thẻ", "casino_gacha", "Thực hiện 10 lượt quay Gacha", 30000, 1, "", "🎰")
_register("gacha_roll_100", "Tín Đồ Gacha", "casino_gacha", "Thực hiện 100 lượt quay Gacha", 200000, 10, "Thánh Quay Tay", "💫")
_register("gacha_ssr_first", "Ánh Sáng Hoàng Kim SSR", "casino_gacha", "Quay trúng vật phẩm / thẻ bậc SSR đầu tiên", 150000, 8, "Bàn Tay Tinh Tú", "🌟")
_register("gacha_ur_first", "Hào Quang Tối Thượng UR", "casino_gacha", "Quay trúng vật phẩm / thẻ cấp độ tối cao UR", 500000, 25, "Vận May Vũ Trụ", "👑")

_register("coin_transfer_first", "Giao Dịch Hào Phóng", "casino_gacha", "Chuyển tiền coin thành công cho người khác", 15000, 0, "Mạnh Thường Quân", "💸")
_register("coin_transfer_1m", "Nhà Tài Trợ Bạc Triệu", "casino_gacha", "Chuyển tặng hơn 1,000,000 coin cho bạn bè", 100000, 5, "Nhà Từ Thiện", "🎁")
_register("coin_bank_deposit", "Gửi Tiết Kiệm An Toàn", "casino_gacha", "Gửi tiền vào Ngân Hàng Sakura", 15000, 0, "", "🏦")
_register("coin_bank_10m", "Tỷ Phú Ngân Hàng", "casino_gacha", "Số dư ngân hàng đạt trên 10,000,000 coins", 300000, 15, "Đại Gia Ngân Hàng", "💳")

_register("wc_first_word", "Chữ Đầu Khởi Sắc", "words_trivia", "Nối thành công từ ngữ đầu tiên trong trò nối chữ", 5000, 0, "", "🧵")
_register("wc_words_10", "Vốn Từ Phong Phú", "words_trivia", "Nối thành công 10 từ", 15000, 0, "", "📖")
_register("wc_words_50", "Nhà Ngôn Ngữ Học", "words_trivia", "Nối thành công 50 từ", 50000, 2, "Cây Bút Trẻ", "✍️")
_register("wc_words_100", "Bậc Thầy Tiếng Việt", "words_trivia", "Nối thành công 100 từ", 100000, 5, "Từ Điển Sống", "📚")
_register("wc_words_500", "Đại Thi Hào", "words_trivia", "Nối thành công 500 từ", 350000, 15, "Bậc Thầy Ngôn Ngữ", "🖋️")
_register("wc_words_1000", "Văn Thánh Giáng Trần", "words_trivia", "Nối thành công 1,000 từ vựng", 1000000, 50, "Bách Khoa Toàn Thư", "🏛️")

_register("wc_streak_5", "Chuỗi Nối Thần Tốc", "words_trivia", "Nối liên tục 5 từ không vấp", 25000, 1, "", "⚡")
_register("wc_streak_15", "Mạch Văn Bất Tận", "words_trivia", "Nối liên tục 15 từ", 75000, 3, "Bất Khả Chiến Bại", "🌪️")
_register("wc_streak_30", "Dòng Chảy Bất Tận", "words_trivia", "Nối liên tục 30 từ trong một phiên", 200000, 10, "Xuất Khẩu Thành Thơ", "🌊")

_register("wc_hard_word", "Từ Khó Hiểm Hóc", "words_trivia", "Nối thành công một từ hiếm gặp kết thúc bằng âm khó", 30000, 1, "Thánh Đố Chữ", "🧩")
_register("wc_bot_defeat", "Chiến Thắng Trí Tuệ Nhân Tạo", "words_trivia", "Đưa ra từ khiến Bot Sakura phải bó tay", 50000, 2, "Khắc Tinh AI", "🤖")

_register("trivia_correct_first", "Nhà Thông Thái Trẻ", "words_trivia", "Trả lời đúng câu hỏi đố vui đầu tiên", 5000, 0, "", "💡")
_register("trivia_correct_10", "Hiểu Rộng Biết Sâu", "words_trivia", "Trả lời đúng 10 câu hỏi đố vui trí tuệ", 30000, 1, "", "🧠")
_register("trivia_correct_50", "Bách Khoa Tri Thức", "words_trivia", "Trả lời đúng 50 câu hỏi đố vui", 150000, 5, "Tiến Sĩ Tri Thức", "🎓")
_register("trivia_speed_fast", "Trả Lời Thần Tốc", "words_trivia", "Trả lời đúng câu đố trong vòng dưới 3 giây", 40000, 2, "Não Nhảy Số Nhanh", "⚡")

_register("xo_win_first", "Bàn Cờ Caro 15x15", "words_trivia", "Chiến thắng ván cờ Caro đầu tiên", 15000, 1, "Kỳ Thủ Nhập Môn", "⭕")
_register("xo_win_5", "Kỳ Thủ Đẳng Cấp", "words_trivia", "Thắng 5 ván cờ Caro", 60000, 3, "Chiến Lược Gia Cờ", "❌")
_register("chess_play_first", "Kỳ Nghệ Tinh Hoa", "words_trivia", "Chơi ván Cờ Vua AI đầu tiên trên Web", 20000, 1, "", "♟️")
_register("chess_checkmate", "Chiếu Bí Đỉnh Cao", "words_trivia", "Chiếu bí đối thủ trong ván cờ vua", 50000, 2, "Đại Kiện Tướng Cờ Vua", "👑")

_register("streak_3", "Giữ Vững Phong Độ", "social_level", "Điểm danh liên tục 3 ngày", 10000, 0, "", "🔥")
_register("streak_7", "Tuần Lễ Hoàn Hảo", "social_level", "Điểm danh liên tục 7 ngày (1 tuần)", 30000, 1, "Người Kiên Trì", "🗓️")
_register("streak_30", "Một Tháng Đồng Hành", "social_level", "Điểm danh liên tục 30 ngày (1 tháng)", 150000, 5, "Thành Viên Trung Kiên", "🌙")
_register("streak_100", "Trăm Ngày Gắn Kết", "social_level", "Điểm danh liên tục 100 ngày không đứt chuỗi", 500000, 20, "Huyền Thoại Điểm Danh", "💯")
_register("streak_365", "Một Năm Bền Vững", "social_level", "Điểm danh liên tục trọn vẹn 365 ngày (1 năm)", 2500000, 100, "Cây Cao Bóng Cả", "👑")

_register("bot_level_5", "Tăng Trưởng Nhanh Chóng", "social_level", "Đạt cấp độ Bot Level 5", 15000, 0, "", "⭐")
_register("bot_level_10", "Dấu Mốc Trưởng Thành", "social_level", "Đạt cấp độ Bot Level 10", 35000, 1, "", "🌟")
_register("bot_level_25", "Thành Viên Tích Cực", "social_level", "Đạt cấp độ Bot Level 25", 100000, 5, "Cựu Binh Server", "🎖️")
_register("bot_level_50", "Đỉnh Cao Đàm Đạo", "social_level", "Đạt cấp độ Bot Level 50", 300000, 15, "Trụ Cột Máy Chủ", "🛡️")
_register("bot_level_100", "Cảnh Giới Bách Niên", "social_level", "Chinh phục cột mốc đỉnh cao Bot Level 100", 1500000, 80, "Thánh Thượng Tôn Quý", "👑")

_register("marry_propose", "Lời Cầu Hôn Ngọt Ngào", "social_level", "Cầu hôn thành công một người bạn trong server", 50000, 2, "Đã Đính Ước", "💍")
_register("marry_wedding", "Lễ Cưới Trong Mơ", "social_level", "Tổ chức hôn lễ thành công tại máy chủ", 100000, 5, "Tân Lang / Tân Nương", "💒")
_register("marry_days_7", "Tuần Trăng Mật Ngọt Ngào", "social_level", "Duy trì cuộc hôn nhân hạnh phúc được 7 ngày", 60000, 3, "", "🍯")
_register("marry_days_30", "Tình Yêu Sắt Son", "social_level", "Duy trì hôn nhân hạnh phúc được 30 ngày", 200000, 10, "Uyên Ương Bền Chặt", "❤️")
_register("marry_days_100", "Bách Niên Giai Lão", "social_level", "Gắn bó hôn nhân qua 100 ngày", 800000, 40, "Thiên Duyên Tiền Định", "💖")

_register("giveaway_join_first", "Tham Gia Quà Tặng", "social_level", "Tham gia vào 1 sự kiện Giveaway trên server", 10000, 0, "", "🎉")
_register("giveaway_win_first", "Trúng Thưởng May Mắn", "social_level", "Trúng giải thưởng từ một sự kiện Giveaway", 50000, 2, "Người Được Chọn", "🎁")

_register("confession_send", "Tâm Tình Giấu Kín", "social_level", "Gửi một tâm sự Confession ẩn danh lên server", 15000, 0, "Kẻ Giấu Mặt Đa Tình", "💌")
_register("voice_time_1h", "Giao Lưu Thoại", "social_level", "Tham gia trò chuyện kênh thoại Voice được 1 giờ", 25000, 1, "", "🎙️")
_register("voice_time_10h", "Tâm Sự Đêm Khuya", "social_level", "Tổng thời gian trò chuyện kênh thoại đạt 10 giờ", 100000, 5, "Giọng Oanh Vàng", "🎧")

_register("role_custom_create", "Role Danh Giá", "social_level", "Tạo thành công một Role màu tùy chỉnh cá nhân", 50000, 2, "Chủ Sở Hữu Role", "🎨")
_register("web_profile_update", "Hồ Sơ Cá Nhân", "social_level", "Cập nhật và cá nhân hóa trang Profile trên Web Dashboard", 30000, 1, "Cư Dân Số Sakura", "🌐")
_register("global_chat_send", "Kết Nối Xuyên Biên Giới", "social_level", "Gửi tin nhắn lên Kênh Global Chat toàn cầu", 20000, 1, "Công Dân Toàn Cầu", "🌍")
_register("help_view", "Khám Phá Tính Năng", "social_level", "Xem danh mục trợ giúp của bot qua lệnh s!help", 5000, 0, "", "📖")



CUSTOM_ACH_FILE = DATA_DIR / "custom_achievements.json"

def _load_custom_achievements():
    """Tải và hợp nhất các thành tựu tùy chỉnh tạo từ Web Admin."""
    if CUSTOM_ACH_FILE.exists():
        try:
            with open(CUSTOM_ACH_FILE, "r", encoding="utf-8") as f:
                cdata = json.load(f)
                for k, v in cdata.items():
                    ACHIEVEMENTS_CATALOG[k] = v
        except Exception:
            pass

_load_custom_achievements()

def load_user_achievements() -> Dict[str, Any]:
    if not ACHIEVEMENTS_FILE.exists():
        return {}
    try:
        with open(ACHIEVEMENTS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}

def save_user_achievements(data: Dict[str, Any]):
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    with open(ACHIEVEMENTS_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def get_user_ach_data(user_id: int | str) -> Dict[str, Any]:
    uid = str(user_id)
    all_data = load_user_achievements()
    if uid not in all_data:
        all_data[uid] = {
            "unlocked": {},
            "titles": [],
            "stats": {}
        }
    return all_data[uid]

async def unlock_achievement(guild_id: int, user_id: int, ach_id: str, channel: Optional[discord.TextChannel] = None) -> Optional[Dict[str, Any]]:
    """Kiểm tra và mở khóa thành tựu cho người chơi. Trả về thông tin thành tựu nếu vừa mở mới."""
    _load_custom_achievements()
    ach = ACHIEVEMENTS_CATALOG.get(ach_id)
    if not ach:
        return None

    uid = str(user_id)
    all_data = load_user_achievements()
    u_data = all_data.setdefault(uid, {"unlocked": {}, "titles": [], "stats": {}})
    unlocked = u_data.setdefault("unlocked", {})

    if ach_id in unlocked:
        return None

    unlocked[ach_id] = int(time.time())
    if ach.get("reward_title") and ach["reward_title"] not in u_data.setdefault("titles", []):
        u_data["titles"].append(ach["reward_title"])

    save_user_achievements(all_data)

    reward_coins = ach.get("reward_coins", 0)
    reward_xu = ach.get("reward_xu", 0)
    if reward_coins > 0:
        await update_user_coins(guild_id, user_id, reward_coins)
    if reward_xu > 0:
        await update_user_xu(guild_id, user_id, reward_xu)

    if channel:
        try:
            embed = discord.Embed(
                title=f"🏆 THÀNH TỰU MỚI MỞ KHÓA!",
                description=f"Chúc mừng <@{user_id}> vừa đạt thành tựu:\n**{ach['icon']} {ach['name']}**\n*{ach['desc']}*",
                color=discord.Color.gold()
            )
            reward_parts = []
            if reward_coins > 0:
                reward_parts.append(f"🪙 **`+{reward_coins:,}` Coin**")
            if reward_xu > 0:
                reward_parts.append(f"💎 **`+{reward_xu:,}` Xu**")
            if ach.get("reward_title"):
                reward_parts.append(f"🏷️ Danh hiệu: **[{ach['reward_title']}]**")
            embed.add_field(name="🎁 Phần Thưởng", value=" • ".join(reward_parts) if reward_parts else "Huy chương danh dự", inline=False)
            embed.set_footer(text=f"Mở khóa thành tựu • Sakura Bot MiniGame System")
            await channel.send(embed=embed)
        except Exception:
            pass

    return ach



CATEGORY_LABELS_VI = {
    "all": ("Tất Cả", "🌟"),
    "fishing": ("Câu Cá & Thủy Tộc", "🎣"),
    "mining": ("Đào Khoáng & Hầm Mỏ", "⛏️"),
    "farming": ("Nông Trại & Đồng Ruộng", "🌾"),
    "casino_gacha": ("Casino & Vận May", "🎲"),
    "words_trivia": ("Nối Từ & Đố Vui", "🧵"),
    "social_level": ("Cộng Đồng & Xã Hội", "💖"),
}

CATEGORY_LABELS_EN = {
    "all": ("All", "🌟"),
    "fishing": ("Fishing & Aquarium", "🎣"),
    "mining": ("Mining & Cave", "⛏️"),
    "farming": ("Farming & Fields", "🌾"),
    "casino_gacha": ("Casino & Luck", "🎲"),
    "words_trivia": ("Word Chain & Trivia", "🧵"),
    "social_level": ("Community & Level", "💖"),
}

CATEGORY_LABELS = CATEGORY_LABELS_VI

class AchievementView(discord.ui.View):
    def __init__(self, author: discord.Member, guild_id: int):
        super().__init__(timeout=180)
        self.author = author
        self.guild_id = guild_id
        self.category = "all"
        self.page = 0
        self.per_page = 6
        self._build_components()

    def _get_filtered(self) -> List[Dict[str, Any]]:
        if self.category == "all":
            return list(ACHIEVEMENTS_CATALOG.values())
        return [ach for ach in ACHIEVEMENTS_CATALOG.values() if ach["category"] == self.category]

    @property
    def total_pages(self) -> int:
        return max(1, math.ceil(len(self._get_filtered()) / self.per_page))

    def _build_components(self):
        self.clear_items()

        vi = is_vietnamese(self.guild_id)
        cat_dict = CATEGORY_LABELS_VI if vi else CATEGORY_LABELS_EN
        options = []
        for cat_k, (label, em) in cat_dict.items():
            options.append(discord.SelectOption(
                label=label,
                value=cat_k,
                emoji=em,
                default=(self.category == cat_k)
            ))
        ph_cat = "📂 Chọn danh mục thành tựu..." if vi else "📂 Select achievement category..."
        sel = discord.ui.Select(placeholder=ph_cat, options=options, row=0)
        sel.callback = self._on_select_cat
        self.add_item(sel)

        prev_lbl = "Trang Trước" if vi else "Previous"
        next_lbl = "Trang Sau" if vi else "Next"
        page_lbl = f"Trang {self.page + 1}/{self.total_pages}" if vi else f"Page {self.page + 1}/{self.total_pages}"

        prev_btn = discord.ui.Button(label=prev_lbl, style=discord.ButtonStyle.secondary, emoji="⬅️", row=1, disabled=(self.page <= 0))
        prev_btn.callback = self._prev_page
        self.add_item(prev_btn)

        page_btn = discord.ui.Button(label=page_lbl, style=discord.ButtonStyle.primary, row=1, disabled=True)
        self.add_item(page_btn)

        next_btn = discord.ui.Button(label=next_lbl, style=discord.ButtonStyle.secondary, emoji="➡️", row=1, disabled=(self.page >= self.total_pages - 1))
        next_btn.callback = self._next_page
        self.add_item(next_btn)

    def build_embed(self) -> discord.Embed:
        u_data = get_user_ach_data(self.author.id)
        unlocked = u_data.get("unlocked", {})
        total_all = len(ACHIEVEMENTS_CATALOG)
        total_user = len(unlocked)
        pct = (total_user / total_all) * 100 if total_all else 0

        filled = int(pct / 10)
        bar = "▰" * filled + "▱" * (10 - filled)

        vi = is_vietnamese(self.guild_id)
        cat_dict = CATEGORY_LABELS_VI if vi else CATEGORY_LABELS_EN
        cat_name, cat_emoji = cat_dict.get(self.category, ("Tất Cả" if vi else "All", "🌟"))
        if vi:
            title_str = f"🏆 BẢNG THÀNH TỰU MINIGAME: {self.author.display_name.upper()}"
            desc_str = f"Tiến độ tổng: **{total_user}/{total_all}** ({pct:.1f}%)\n`[{bar}]`\n\nDanh mục hiện tại: **{cat_emoji} {cat_name}**"
            footer_str = f"Trang {self.page + 1}/{self.total_pages} • Tổng hơn 200 thành tựu có thưởng • Sakura Bot"
        else:
            title_str = f"🏆 MINIGAME ACHIEVEMENTS: {self.author.display_name.upper()}"
            desc_str = f"Total Progress: **{total_user}/{total_all}** ({pct:.1f}%)\n`[{bar}]`\n\nCurrent Category: **{cat_emoji} {cat_name}**"
            footer_str = f"Page {self.page + 1}/{self.total_pages} • Over 200 rewarding achievements • Sakura Bot"

        embed = discord.Embed(
            title=title_str,
            description=desc_str,
            color=discord.Color.gold()
        )

        filtered = self._get_filtered()
        start = self.page * self.per_page
        page_items = filtered[start:start + self.per_page]

        for ach in page_items:
            is_unlocked = (ach["id"] in unlocked)
            status_icon = "✅" if is_unlocked else "🔒"
            if vi:
                status_text = "Đã mở khóa" if is_unlocked else "Chưa mở"
                hon_str = "Danh dự"
            else:
                status_text = "Unlocked" if is_unlocked else "Locked"
                hon_str = "Honorary"

            rewards = []
            if ach.get("reward_coins"):
                rewards.append(f"🪙 `{ach['reward_coins']:,}`c")
            if ach.get("reward_xu"):
                rewards.append(f"💎 `{ach['reward_xu']:,}`x")
            if ach.get("reward_title"):
                rewards.append(f"🏷️ [{ach['reward_title']}]")
            reward_str = " | ".join(rewards) if rewards else hon_str

            name_str = f"{status_icon} {ach['icon']} {ach['name']}"
            if vi:
                field_val = f"• *{ach['desc']}*\n• Phần thưởng: {reward_str} • Trạng thái: **{status_text}**"
            else:
                field_val = f"• *{ach['desc']}*\n• Reward: {reward_str} • Status: **{status_text}**"
            embed.add_field(
                name=name_str,
                value=field_val,
                inline=False
            )

        embed.set_footer(text=footer_str)
        return embed

    async def _on_select_cat(self, interaction: discord.Interaction):
        if interaction.user.id != self.author.id:
            vi = is_vietnamese(interaction.guild)
        msg = "❌ Đây không phải bảng thành tựu của bạn!" if vi else "❌ This achievement panel does not belong to you!"
        return await interaction.response.send_message(msg, ephemeral=True)
        self.category = interaction.data["values"][0]
        self.page = 0
        self._build_components()
        await interaction.response.edit_message(embed=self.build_embed(), view=self)

    async def _prev_page(self, interaction: discord.Interaction):
        if interaction.user.id != self.author.id:
            vi = is_vietnamese(interaction.guild)
        msg = "❌ Đây không phải bảng thành tựu của bạn!" if vi else "❌ This achievement panel does not belong to you!"
        return await interaction.response.send_message(msg, ephemeral=True)
        if self.page > 0:
            self.page -= 1
            self._build_components()
            await interaction.response.edit_message(embed=self.build_embed(), view=self)

    async def _next_page(self, interaction: discord.Interaction):
        if interaction.user.id != self.author.id:
            vi = is_vietnamese(interaction.guild)
        msg = "❌ Đây không phải bảng thành tựu của bạn!" if vi else "❌ This achievement panel does not belong to you!"
        return await interaction.response.send_message(msg, ephemeral=True)
        if self.page < self.total_pages - 1:
            self.page += 1
            self._build_components()
            await interaction.response.edit_message(embed=self.build_embed(), view=self)



class AchievementCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.hybrid_group(name="achievement", aliases=["thanhtuu", "achieve", "achievements"], description="Hệ thống thành tựu và danh hiệu / Achievements system")
    async def ach_group(self, ctx: commands.Context):
        """Xem danh sách thành tựu nếu không chọn lệnh con."""
        if ctx.invoked_subcommand is None:
            await self.achievements_cmd(ctx)

    @ach_group.command(name="list", aliases=["view"], description="Xem danh sách hơn 200 thành tựu minigame và nhận thưởng")
    async def ach_list(self, ctx: commands.Context):
        await self.achievements_cmd(ctx)

    @ach_group.command(name="top", aliases=["leaderboard", "bxh"], description="Xem Bảng Xếp Hạng người chơi mở khóa nhiều thành tựu nhất")
    async def ach_top(self, ctx: commands.Context):
        await self.ach_top_cmd(ctx)

    async def achievements_cmd(self, ctx: commands.Context):
        """Xem danh sách hơn 200 thành tựu minigame và nhận thưởng."""
        view = AchievementView(ctx.author, ctx.guild.id if ctx.guild else 0)
        await ctx.send(embed=view.build_embed(), view=view)

    @commands.command(name="bxh_thanhtuu", aliases=["achtop", "achievetop", "top_thanhtuu"])
    async def ach_top_cmd(self, ctx: commands.Context):
        """Xem Bảng Xếp Hạng người chơi mở khóa nhiều thành tựu nhất trên bot."""
        all_user_ach = load_user_achievements()
        _load_custom_achievements()
        total_catalog = len(ACHIEVEMENTS_CATALOG)

        ranking = []
        owner_ids = {"1144785664458637394"}
        try:
            from config import OWNER_ID
            owner_ids.add(str(OWNER_ID))
        except Exception:
            pass

        for uid_str, udata in all_user_ach.items():
            if uid_str in owner_ids:
                continue
            unlocked = udata.get("unlocked", {})
            if unlocked:
                ranking.append((uid_str, len(unlocked), max(unlocked.values()), udata.get("titles", [])))

        ranking.sort(key=lambda x: (x[1], x[2]), reverse=True)

        vi = is_vietnamese(ctx.guild)
        if vi:
            t_title = "🏆 BẢNG XẾP HẠNG THỢ SĂN THÀNH TỰU (TOP 10)"
            t_desc = f"Tổng số thành tựu trong hệ thống: **{total_catalog}**\nChinh phục thành tựu minigame qua các hoạt động câu cá, đào mỏ, nông trại, level!"
            t_hon = "Bảng Vinh Danh"
            t_foot = "Dùng lệnh /achievements để kiểm tra và nhận thưởng thành tựu cá nhân • Sakura Bot"
        else:
            t_title = "🏆 ACHIEVEMENT HUNTERS LEADERBOARD (TOP 10)"
            t_desc = f"Total achievements registered in system: **{total_catalog}**\nUnlock achievements across fishing, mining, farming, casino and leveling!"
            t_hon = "Hall of Fame"
            t_foot = "Use /achievements to inspect your progress and claim rewards • Sakura Bot"

        embed = discord.Embed(
            title=t_title,
            description=t_desc,
            color=discord.Color.gold()
        )

        if not ranking:
            embed.description += ("\n\n*Chưa có ai mở khóa thành tựu nào.*" if vi else "\n\n*No players have unlocked achievements yet.*")
            return await ctx.send(embed=embed)

        medals = {1: "🥇", 2: "🥈", 3: "🥉"}
        lines = []
        for rank, (uid_str, count, _, titles) in enumerate(ranking[:10], start=1):
            medal = medals.get(rank, f"`#{rank}`")
            user_mention = f"<@{uid_str}>"
            pct = (count / total_catalog * 100) if total_catalog else 0
            title_str = f" • [{titles[-1]}]" if titles else ""
            lines.append(f"{medal} {user_mention}: **{count}/{total_catalog}** ({pct:.1f}%){title_str}")

        embed.add_field(name=t_hon, value="\n".join(lines), inline=False)
        embed.set_footer(text=t_foot)
        await ctx.send(embed=embed)

async def setup(bot: commands.Bot):
    await bot.add_cog(AchievementCog(bot))
