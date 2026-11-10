import asyncio
import json
import random
import time
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any

import discord
from data.database import get_user_data, update_user_coins
from Check.i18n import t, is_vietnamese

VN_TZ = timezone(timedelta(hours=7))


def safe_field_text(text: Any, max_len: int = 1000, fallback: str = "*Không có*") -> str:
    """Đảm bảo chuỗi hiển thị không rỗng và không vượt quá max_len ký tự."""
    if text is None:
        return fallback
    s = str(text).strip()
    if not s:
        return fallback
    if len(s) > max_len:
        return s[:max_len - 3] + "..."
    return s


def safe_add_field(
    embed: discord.Embed,
    name: str,
    value: Any,
    inline: bool = False,
    max_chunk_len: int = 1000
) -> None:
    """
    Thêm field vào discord.Embed an toàn tuyệt đối:
    - Cắt title/name <= 256 ký tự (chuẩn Discord).
    - Nếu value > 1024 ký tự (hoặc max_chunk_len), tự động tách thành nhiều field (chunk) theo dòng.
    - Đảm bảo không vượt quá 25 fields (giới hạn cứng của Discord API).
    - Ngăn chặn vượt giới hạn tổng dung lượng 6000 ký tự của Discord Embed.
    """
    if len(embed.fields) >= 25:
        return

    # Tính tổng ký tự hiện tại để tránh tràn 6000
    current_total = len(embed.title or "") + len(embed.description or "")
    if embed.footer and embed.footer.text:
        current_total += len(embed.footer.text)
    for f in embed.fields:
        current_total += len(f.name or "") + len(f.value or "")
    if current_total >= 5600:
        return

    name_str = str(name).strip() if name else "Thông tin"
    if len(name_str) > 250:
        name_str = name_str[:247] + "..."

    val_str = str(value).strip() if value is not None else "*Không có*"
    if not val_str:
        val_str = "*Không có*"

    if len(val_str) <= max_chunk_len:
        embed.add_field(name=name_str, value=val_str, inline=inline)
        return

    lines = val_str.split("\n")
    chunks = []
    curr_lines = []
    curr_len = 0

    for line in lines:
        if len(line) > max_chunk_len:
            line = line[:max_chunk_len - 3] + "..."
        line_len = len(line) + (1 if curr_lines else 0)

        if curr_len + line_len > max_chunk_len and curr_lines:
            chunks.append("\n".join(curr_lines))
            curr_lines = [line]
            curr_len = len(line)
        else:
            curr_lines.append(line)
            curr_len += line_len

    if curr_lines:
        chunks.append("\n".join(curr_lines))

    if not chunks:
        chunks = [val_str[:max_chunk_len]]

    for idx, chunk in enumerate(chunks):
        if len(embed.fields) >= 25:
            break
        chunk_name = f"{name_str} ({idx + 1}/{len(chunks)})" if len(chunks) > 1 else name_str
        if len(chunk_name) > 250:
            chunk_name = chunk_name[:247] + "..."
        embed.add_field(name=chunk_name, value=chunk or "*Không có*", inline=inline)


# ==============================================================================
# 1. CATALOG HẠT GIỐNG & NÔNG SẢN (SEEDS & CROPS)
# ==============================================================================
SEEDS_CATALOG = {
    # Hoa màu & Lương thực cơ bản
    "seed_wheat": {
        "id": "seed_wheat",
        "name": "🌾 Hạt Giống Lúa Mì",
        "crop_id": "crop_wheat",
        "crop_name": "🌾 Bó Lúa Mì Vàng",
        "price": 500,
        "grow_seconds": 180,  # 3 phút
        "yield_min": 2,
        "yield_max": 5,
        "sell_price": 450,
        "desc": "Lương thực cơ bản, sinh trưởng nhanh, nguyên liệu làm bánh và sushi."
    },
    "seed_carrot": {
        "id": "seed_carrot",
        "name": "🥕 Hạt Giống Cà Rốt",
        "crop_id": "crop_carrot",
        "crop_name": "🥕 Cà Rốt Giòn Ngọt",
        "price": 1000,
        "grow_seconds": 300,  # 5 phút
        "yield_min": 2,
        "yield_max": 5,
        "sell_price": 750,
        "desc": "Củ cà rốt cam mọng nước, nguyên liệu nấu món hầm và salad nông dân."
    },
    "seed_bokchoy": {
        "id": "seed_bokchoy",
        "name": "🥬 Hạt Giống Cải Thìa",
        "crop_id": "crop_bokchoy",
        "crop_name": "🥬 Cây Cải Thìa Xanh",
        "price": 1500,
        "grow_seconds": 420,  # 7 phút
        "yield_min": 2,
        "yield_max": 6,
        "sell_price": 950,
        "desc": "Rau cải xanh tươi mát, dùng nấu canh cá giải nhiệt ngày hè."
    },
    "seed_tomato": {
        "id": "seed_tomato",
        "name": "🍅 Hạt Giống Cà Chua",
        "crop_id": "crop_tomato",
        "crop_name": "🍅 Cà Chua Mọng Đỏ",
        "price": 2500,
        "grow_seconds": 600,  # 10 phút
        "yield_min": 3,
        "yield_max": 6,
        "sell_price": 1400,
        "desc": "Trái cà chua đỏ rực, kết hợp nấu Canh Cá Cà Chua danh tiếng."
    },
    "seed_onion": {
        "id": "seed_onion",
        "name": "🧅 Hạt Giống Hành Tây",
        "crop_id": "crop_onion",
        "crop_name": "🧅 Củ Hành Tây Ngọt",
        "price": 3200,
        "grow_seconds": 720,  # 12 phút
        "yield_min": 3,
        "yield_max": 6,
        "sell_price": 1700,
        "desc": "Gia vị khử tanh tuyệt vời cho các món cá cao cấp."
    },
    "seed_garlic": {
        "id": "seed_garlic",
        "name": "🧄 Hạt Giống Tỏi Thơm",
        "crop_id": "crop_garlic",
        "crop_name": "🧄 Củ Tỏi Tía Thơm",
        "price": 4000,
        "grow_seconds": 840,  # 14 phút
        "yield_min": 3,
        "yield_max": 7,
        "sell_price": 2000,
        "desc": "Tỏi thơm cay nồng, xua đuổi sâu bọ và kích thích vị giác."
    },
    "seed_corn": {
        "id": "seed_corn",
        "name": "🌽 Hạt Giống Bắp Ngô",
        "crop_id": "crop_corn",
        "crop_name": "🌽 Bắp Ngô Vàng Óng",
        "price": 5000,
        "grow_seconds": 960,  # 16 phút
        "yield_min": 3,
        "yield_max": 7,
        "sell_price": 2600,
        "desc": "Ngô hạt vàng mẩy béo ngậy, bồi dưỡng sức lực cho nông dân."
    },
    "seed_chili": {
        "id": "seed_chili",
        "name": "🌶️ Hạt Giống Ớt Cay",
        "crop_id": "crop_chili",
        "crop_name": "🌶️ Ớt Chỉ Thiên Đỏ",
        "price": 6500,
        "grow_seconds": 1100, # 18 phút
        "yield_min": 4,
        "yield_max": 8,
        "sell_price": 2800,
        "desc": "Ớt đỏ cay xé lưỡi, nấu món Cá Nướng Ớt kích hoạt tỉ lệ cá đột biến."
    },
    # Trái cây ngọt ngào
    "seed_strawberry": {
        "id": "seed_strawberry",
        "name": "🍓 Hạt Giống Dâu Tây",
        "crop_id": "crop_strawberry",
        "crop_name": "🍓 Dâu Tây Đà Lạt",
        "price": 8500,
        "grow_seconds": 1200, # 20 phút
        "yield_min": 3,
        "yield_max": 7,
        "sell_price": 4200,
        "desc": "Dâu tây thơm ngát, ăn trực tiếp hồi 15 độ bền cần câu đang cầm."
    },
    "seed_watermelon": {
        "id": "seed_watermelon",
        "name": "🍉 Hạt Giống Dưa Hấu",
        "crop_id": "crop_watermelon",
        "crop_name": "🍉 Quả Dưa Hấu Khổng Lồ",
        "price": 15000,
        "grow_seconds": 1800, # 30 phút
        "yield_min": 2,
        "yield_max": 4,
        "sell_price": 11000,
        "desc": "Dưa hấu mát rượi ngày hè, dùng làm Sushi Cá Hồi Dưa Hấu xịn sò."
    },
    "seed_mushroom": {
        "id": "seed_mushroom",
        "name": "🍄 Bào Tử Nấm Hương",
        "crop_id": "crop_mushroom",
        "crop_name": "🍄 Nấm Hương Rừng Sâu",
        "price": 22000,
        "grow_seconds": 1500, # 25 phút
        "yield_min": 2,
        "yield_max": 5,
        "sell_price": 14000,
        "desc": "Nấm hương mọc trong bóng râm, nguyên liệu nấu Cháo Nấm Bát Trân bất hoại."
    },
    "seed_grape": {
        "id": "seed_grape",
        "name": "🍇 Hạt Giống Nho Tím",
        "crop_id": "crop_grape",
        "crop_name": "🍇 Chùm Nho Tím Mộng",
        "price": 30000,
        "grow_seconds": 2400, # 40 phút
        "yield_min": 3,
        "yield_max": 6,
        "sell_price": 18000,
        "desc": "Nho tím ngọt thanh, nguyên liệu ủ rượu vang và nấu tiệc cung đình."
    },
    # Hoa cảnh & Thảo mộc quý
    "seed_sunflower": {
        "id": "seed_sunflower",
        "name": "🌻 Hạt Giống Hướng Dương",
        "crop_id": "crop_sunflower",
        "crop_name": "🌻 Hoa Hướng Dương Rạng Rỡ",
        "price": 25000,
        "grow_seconds": 1800, # 30 phút
        "yield_min": 2,
        "yield_max": 5,
        "sell_price": 16000,
        "desc": "Hoa mặt trời luôn hướng về ánh dương, xua tan u ám trong trang trại."
    },
    "seed_rose": {
        "id": "seed_rose",
        "name": "🌹 Hạt Giống Hoa Hồng",
        "crop_id": "crop_rose",
        "crop_name": "🌹 Hoa Hồng Tình Yêu",
        "price": 35000,
        "grow_seconds": 2100, # 35 phút
        "yield_min": 2,
        "yield_max": 5,
        "sell_price": 22000,
        "desc": "Hoa hồng rực rỡ tượng trưng tình yêu, có thể tặng người thương hoặc bán giá cao."
    },
    # Thần quả cao cấp
    "seed_golden_apple": {
        "id": "seed_golden_apple",
        "name": "🍏 Hạt Giống Táo Vàng",
        "crop_id": "crop_golden_apple",
        "crop_name": "🍏 Táo Vàng Hoàng Gia",
        "price": 120000,
        "grow_seconds": 3600, # 60 phút
        "yield_min": 2,
        "yield_max": 4,
        "sell_price": 85000,
        "desc": "Trái cây thần thánh của các vị thần, ăn trực tiếp buff +25 May Mắn trong 2h."
    },
    "seed_peach": {
        "id": "seed_peach",
        "name": "🍑 Hạt Giống Đào Tiên",
        "crop_id": "crop_peach",
        "crop_name": "🍑 Đào Tiên Bồng Lai",
        "price": 250000,
        "grow_seconds": 5400, # 90 phút
        "yield_min": 2,
        "yield_max": 4,
        "sell_price": 180000,
        "desc": "Ba ngàn năm nở hoa, ba ngàn năm kết trái, nguyên liệu Đại Tiệc Hoàng Gia."
    },
    "seed_snow_lotus": {
        "id": "seed_snow_lotus",
        "name": "🪷 Hạt Giống Sen Tuyết",
        "crop_id": "crop_snow_lotus",
        "crop_name": "🪷 Tuyết Liên Vạn Năm",
        "price": 500000,
        "grow_seconds": 7200, # 120 phút
        "yield_min": 1,
        "yield_max": 3,
        "sell_price": 420000,
        "desc": "Mọc trên đỉnh băng tuyết ngàn năm, thần dược chữa lành và tăng cường sức mạnh."
    }
}

# ==============================================================================
# 2. CATALOG SÂU BỌ (PESTS & INSECTS)
# ==============================================================================
PESTS_CATALOG = {
    "caterpillar": {
        "id": "caterpillar",
        "name": "🐛 Sâu Xanh Lá",
        "sell_price": 1500,
        "bait_luck": 15,
        "desc": "Sâu ăn lá thường, bắt được có thể đem bán hoặc làm mồi câu khá bén."
    },
    "ladybug": {
        "id": "ladybug",
        "name": "🐞 Bọ Rùa Chấm Đỏ",
        "sell_price": 3800,
        "bait_luck": 25,
        "desc": "Bọ rùa xinh đẹp, làm mồi câu rất thu hút các loài cá hiếm sắc màu."
    },
    "beetle": {
        "id": "beetle",
        "name": "🪲 Bọ Cánh Cứng Sừng",
        "sell_price": 9500,
        "bait_luck": 45,
        "desc": "Bọ cánh cứng to khỏe, làm mồi câu cá săn mồi cỡ lớn rất nhạy."
    },
    "golden_cicada": {
        "id": "golden_cicada",
        "name": "🪙 Ve Sầu Hoàng Kim",
        "sell_price": 30000,
        "bait_luck": 80,
        "desc": "Ve sầu vàng lột xác quý hiếm, thương gia thu mua giá cao ngất ngưởng."
    },
    "rainbow_butterfly": {
        "id": "rainbow_butterfly",
        "name": "🦋 Bướm Đêm Ngũ Sắc",
        "sell_price": 120000,
        "bait_luck": 180,
        "desc": "Sinh vật huyền ảo lấp lánh bụi phấn, mồi câu kích hoạt đột biến cực mạnh!"
    }
}

# ==============================================================================
# 2.1 CATALOG MẦM BỆNH NÔNG TRẠI (DISEASES & PATHOGENS)
# ==============================================================================
DISEASES_CATALOG = {
    "root_rot": {
        "id": "root_rot",
        "name": "🥀 Bệnh Thối Rễ Đen",
        "infection_rate": 0.15,
        "yield_loss": 0.40,
        "cure": "Phân Hữu Cơ Vi Sinh",
        "desc": "Làm rễ cây bị úa đen, giảm 40% sản lượng nếu không xử lý kịp thời."
    },
    "mildew": {
        "id": "mildew",
        "name": "⚪ Bệnh Sương Mai Phấn Trắng",
        "infection_rate": 0.20,
        "yield_loss": 0.35,
        "cure": "Phân Bón Siêu Tốc",
        "desc": "Lớp mốc trắng bao phủ mặt lá khiến quang hợp giảm sút."
    },
    "yellow_leaf": {
        "id": "yellow_leaf",
        "name": "🍂 Đốm Vàng Rỉ Sắt",
        "infection_rate": 0.10,
        "yield_loss": 0.50,
        "cure": "Phân Kích Rễ Hồi Sinh",
        "desc": "Bệnh dịch nguy hiểm khiến lá cây úa vàng và héo rũ hàng loạt."
    },
    "blight": {
        "id": "blight",
        "name": "🔥 Dịch Bệnh Héo Rũ Vi Khuẩn",
        "infection_rate": 0.08,
        "yield_loss": 0.60,
        "cure": "Lồng Kính Bảo Vệ",
        "desc": "Vi khuẩn xâm nhập mạch dẫn cây trồng, gây nguy cơ chết héo cao."
    }
}


# ==============================================================================
# CATALOG ĐỘT BIẾN HOA MÀU & NÔNG SẢN (CROP MUTATIONS)
# ==============================================================================
CROP_MUTATIONS = [
    {
        "id": "golden",
        "name": "🌟 Hoàng Kim Midas",
        "prefix": "🌟 [Hoàng Kim]",
        "price_multi": 3.0,
        "weight": 35,
        "color": 0xFFD700,
        "buff_durability": 50,
        "desc": "Nông sản dát vàng lấp lánh rực rỡ, bán gấp x3 giá và ăn vào hồi 50 độ bền cần câu!"
    },
    {
        "id": "rainbow",
        "name": "🌈 Cầu Vồng Lục Sắc",
        "prefix": "🌈 [Cầu Vồng]",
        "price_multi": 5.0,
        "weight": 20,
        "color": 0xFF69B4,
        "buff_durability": 100,
        "desc": "Phát ra 7 sắc cầu vồng huyền ảo, giá bán x5 và ăn vào hồi phục 100% độ bền cần câu!"
    },
    {
        "id": "frost",
        "name": "❄️ Băng Tinh Ngàn Năm",
        "prefix": "❄️ [Băng Tinh]",
        "price_multi": 2.5,
        "weight": 40,
        "color": 0x87CEEB,
        "buff_durability": 40,
        "desc": "Kết tinh trong băng lạnh vĩnh cửu, giá bán x2.5 lần!"
    },
    {
        "id": "giant",
        "name": "👾 Đột Biến Khổng Lồ",
        "prefix": "👾 [Khổng Lồ]",
        "price_multi": 4.0,
        "weight": 25,
        "color": 0x32CD32,
        "buff_durability": 60,
        "desc": "Củ quả khổng lồ to bằng người thật, bán gấp x4 lần!"
    },
    {
        "id": "void",
        "name": "🌌 Hư Không Void-Touched",
        "prefix": "🌌 [Hư Không]",
        "price_multi": 7.0,
        "weight": 10,
        "color": 0x9370DB,
        "buff_durability": 100,
        "desc": "Mang năng lượng siêu nhiên của vũ trụ, bán gấp x7 lần và tăng tỉ lệ cắn câu cá thần!"
    },
    {
        "id": "divine",
        "name": "👑 Thần Nông Thượng Cổ",
        "prefix": "👑 [Thần Nông]",
        "price_multi": 10.0,
        "weight": 5,
        "color": 0xFF4500,
        "buff_durability": 100,
        "desc": "Cực phẩm nông nghiệp đất trời ban tặng! Bán x10 giá và rớt ngay 1-2 Bụi Sao Lấp Lánh!"
    }
]

# ==============================================================================
# 3. CATALOG DỤNG CỤ & PHÂN BÓN NÔNG TRẠI
# ==============================================================================
FARM_TOOLS_CATALOG = {
    "fertilizer_organic": {
        "id": "fertilizer_organic",
        "name": "🌿 Phân Hữu Cơ Vi Sinh",
        "price": 3000,
        "type": "fertilizer",
        "speed_bonus": 0.30, # tăng 30% tốc độ lớn
        "yield_bonus": 0,
        "desc": "Tăng 30% tốc độ sinh trưởng của cây trồng trong ô đất."
    },
    "fertilizer_speed": {
        "id": "fertilizer_speed",
        "name": "⚡ Phân Bón Siêu Tốc",
        "price": 12000,
        "type": "fertilizer",
        "speed_bonus": 0.50, # giảm 50% thời gian chín
        "yield_bonus": 0,
        "desc": "Kích thích cây lớn siêu tốc, rút ngắn 50% thời gian thu hoạch."
    },
    "fertilizer_yield": {
        "id": "fertilizer_yield",
        "name": "🌾 Phân Bón Bội Thu",
        "price": 25000,
        "type": "fertilizer",
        "speed_bonus": 0,
        "yield_bonus": 1.0, # x2 sản lượng thu hoạch
        "desc": "Cung cấp dinh dưỡng dồi dào, nhân đôi (x2) sản lượng nông sản thu hoạch."
    },
    "fertilizer_revive": {
        "id": "fertilizer_revive",
        "name": "💖 Phân Kích Rễ Hồi Sinh",
        "price": 15000,
        "type": "fertilizer",
        "speed_bonus": 0.20,
        "yield_bonus": 0,
        "desc": "Cứu sống cây trồng bị héo úa ngay lập tức, phục hồi trạng thái xanh tươi."
    },
    "watering_can_copper": {
        "id": "watering_can_copper",
        "name": "🪣 Bình Tưới Đồng",
        "price": 50000,
        "type": "tool",
        "water_duration": 14400, # 4 giờ giữ ẩm
        "desc": "Bình tưới bền bỉ, 1 lần tưới giữ đất ẩm suốt 4 tiếng."
    },
    "watering_can_silver": {
        "id": "watering_can_silver",
        "name": "🥈 Bình Tưới Bạc",
        "price": 250000,
        "type": "tool",
        "water_duration": 28800, # 8 giờ giữ ẩm
        "desc": "Bình tưới bạc sang trọng, giữ ẩm cho đất suốt 8 tiếng."
    },
    "watering_can_mythic": {
        "id": "watering_can_mythic",
        "name": "🌟 Bình Tưới Thần Thoại",
        "price": 1500000,
        "type": "tool",
        "water_duration": 86400, # 24 giờ giữ ẩm
        "desc": "Bình tưới thần ban, tưới 1 lần đất giữ ẩm nguyên 1 ngày không sợ khô."
    },
    "farmer_gloves": {
        "id": "farmer_gloves",
        "name": "🧤 Bao Tay Nhà Nông",
        "price": 100000,
        "type": "tool",
        "pest_catch_bonus": 0.50, # +50% bắt sâu quý
        "desc": "Bảo vệ đôi bàn tay, tăng 50% tỉ lệ bắt được sâu bọ quý hiếm."
    },
    "greenhouse_cover": {
        "id": "greenhouse_cover",
        "name": "🏛️ Lồng Kính Bảo Vệ",
        "price": 800000,
        "type": "plot_upgrade",
        "desc": "Lồng kính lắp cho ô đất, miễn nhiễm 100% bão giông và sương giá mùa đông."
    },
    "rain_talisman": {
        "id": "rain_talisman",
        "name": "🌧️ Bùa Gọi Mưa",
        "price": 50000,
        "type": "consumable",
        "desc": "Triệu hồi cơn mưa mát lành, tự động tưới nước cho toàn bộ ô đất trong trang trại."
    },
    "sun_talisman": {
        "id": "sun_talisman",
        "name": "☀️ Bùa Thái Dương",
        "price": 80000,
        "type": "consumable",
        "desc": "Xua tan bão giông và thời tiết xấu, ban tặng ánh nắng ấm áp cho cây phát triển."
    }
}

# ==============================================================================
# 4. MÙA MÀNG & THỜI TIẾT (SEASONS & WEATHER)
# ==============================================================================
SEASONS_INFO = {
    "spring": {
        "id": "spring",
        "name": "🌸 Mùa Xuân",
        "desc": "Vạn vật sinh sôi nảy nở, dâu tây và các loài hoa tăng 25% tốc độ phát triển.",
        "favored_crops": ["crop_strawberry", "crop_rose", "crop_sunflower"],
        "color": 0xFFB7C5
    },
    "summer": {
        "id": "summer",
        "name": "☀️ Mùa Hạ",
        "desc": "Nắng vàng chói chang, dưa hấu, bắp ngô và ớt cay tăng 30% sản lượng thu hoạch.",
        "favored_crops": ["crop_watermelon", "crop_corn", "crop_chili"],
        "color": 0xFFD700
    },
    "autumn": {
        "id": "autumn",
        "name": "🍁 Mùa Thu",
        "desc": "Mùa gặt trù phú, lúa mì, cà rốt và táo vàng bội thu tăng 30% sản lượng.",
        "favored_crops": ["crop_wheat", "crop_carrot", "crop_golden_apple"],
        "color": 0xFF8C00
    },
    "winter": {
        "id": "winter",
        "name": "❄️ Mùa Đông",
        "desc": "Giá lạnh tuyết phủ, cần lồng kính để tránh sương giá. Sen Tuyết và Nấm tăng x2 giá bán!",
        "favored_crops": ["crop_snow_lotus", "crop_mushroom"],
        "color": 0x87CEEB
    }
}

# Enrich SEEDS_CATALOG with backwards-compatible aliases (harvest_yield, crop_sell_price, etc.)
for sk, sv in SEEDS_CATALOG.items():
    sv.setdefault("seed_price", sv.get("price", 1000))
    sv.setdefault("crop_sell_price", sv.get("sell_price", 500))
    sv.setdefault("growth_time", sv.get("grow_seconds", 300))
    sv.setdefault("harvest_yield", (sv.get("yield_min", 2), sv.get("yield_max", 5)))
    preferred = []
    for s_id, s_data in SEASONS_INFO.items():
        if sv.get("crop_id") in s_data.get("favored_crops", []):
            preferred.append(s_data.get("name", s_id))
    sv.setdefault("preferred_seasons", preferred if preferred else ["Bốn mùa"])

# ==============================================================================
# CATALOG NÔNG SẢN THU HOẠCH (CROPS CATALOG)
# ==============================================================================
CROPS_CATALOG = {}
for sk, sv in SEEDS_CATALOG.items():
    c_id = sv["crop_id"]
    CROPS_CATALOG[c_id] = {
        "id": c_id,
        "seed_id": sk,
        "name": sv["crop_name"],
        "price": sv.get("sell_price", 500),
        "sell_price": sv.get("sell_price", 500),
        "crop_sell_price": sv.get("sell_price", 500),
        "preferred_seasons": sv.get("preferred_seasons", ["Bốn mùa"])
    }


# ==============================================================================
# HỆ THỐNG VẬT PHẨM TÙY CHỈNH ADMIN (CUSTOM FARM ITEMS)
# ==============================================================================
CUSTOM_FARM_FILE = Path(__file__).resolve().parent.parent / "data" / "custom_farm_items.json"

def load_custom_farm_items() -> dict:
    """Tải và cập nhật các vật phẩm nông trại tùy chỉnh (cây, phân bón, dụng cụ, sâu bọ, mầm bệnh)."""
    if not CUSTOM_FARM_FILE.exists():
        return {"seeds": {}, "crops": {}, "fertilizers": {}, "tools": {}, "pests": {}, "diseases": {}}
    try:
        with open(CUSTOM_FARM_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
    except Exception:
        return {"seeds": {}, "crops": {}, "fertilizers": {}, "tools": {}, "pests": {}, "diseases": {}}

    # Gộp seeds & crops
    for sid, sdata in data.get("seeds", {}).items():
        sdata.setdefault("seed_price", sdata.get("price", 1000))
        sdata.setdefault("crop_sell_price", sdata.get("sell_price", 500))
        sdata.setdefault("growth_time", sdata.get("grow_seconds", 300))
        sdata.setdefault("harvest_yield", (sdata.get("yield_min", 2), sdata.get("yield_max", 5)))
        sdata.setdefault("preferred_seasons", ["Bốn mùa"])
        SEEDS_CATALOG[sid] = sdata
        cid = sdata.get("crop_id", f"crop_{sid}")
        CROPS_CATALOG[cid] = {
            "id": cid,
            "seed_id": sid,
            "name": sdata.get("crop_name", sdata.get("name")),
            "price": sdata.get("sell_price", 500),
            "sell_price": sdata.get("sell_price", 500),
            "crop_sell_price": sdata.get("sell_price", 500),
            "desc": sdata.get("desc", ""),
            "preferred_seasons": sdata.get("preferred_seasons", ["Bốn mùa"])
        }

    # Gộp fertilizers & tools
    for tid, tdata in data.get("fertilizers", {}).items():
        tdata.setdefault("type", "fertilizer")
        FARM_TOOLS_CATALOG[tid] = tdata

    for tid, tdata in data.get("tools", {}).items():
        tdata.setdefault("type", tdata.get("type", "tool"))
        FARM_TOOLS_CATALOG[tid] = tdata

    # Gộp pests & diseases
    for pid, pdata in data.get("pests", {}).items():
        PESTS_CATALOG[pid] = pdata

    for did, ddata in data.get("diseases", {}).items():
        DISEASES_CATALOG[did] = ddata

    return data

def save_custom_farm_items(data: dict):
    """Lưu danh mục tùy chỉnh vào file JSON và nạp lại."""
    CUSTOM_FARM_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(CUSTOM_FARM_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    load_custom_farm_items()

load_custom_farm_items()



def get_crop_info(cid: str) -> Dict[str, Any]:
    """Lấy thông tin nông sản an toàn từ crop_id hoặc seed_id."""
    if cid in CROPS_CATALOG:
        return CROPS_CATALOG[cid]
    if cid in SEEDS_CATALOG:
        v = SEEDS_CATALOG[cid]
        return {
            "id": v.get("crop_id", cid),
            "seed_id": cid,
            "name": v.get("crop_name", v.get("name", cid)),
            "price": v.get("sell_price", v.get("crop_sell_price", 500)),
            "sell_price": v.get("sell_price", v.get("crop_sell_price", 500)),
            "crop_sell_price": v.get("sell_price", v.get("crop_sell_price", 500)),
            "desc": v.get("desc", ""),
            "preferred_seasons": v.get("preferred_seasons", ["Bốn mùa"])
        }
    return {
        "id": cid,
        "seed_id": cid,
        "name": cid,
        "price": 500,
        "sell_price": 500,
        "crop_sell_price": 500,
        "desc": "Nông sản",
        "preferred_seasons": ["Bốn mùa"]
    }

FARM_WEATHER_CYCLE = [
    {
        "id": "sunny",
        "name": "☀️ Nắng Ấm Dịu Êm",
        "desc": "Thời tiết ôn hòa lý tưởng, cây trồng phát triển bình thường và ổn định.",
        "effect": "normal",
        "speed_multi": 1.0
    },
    {
        "id": "rainy",
        "name": "🌧️ Mưa Rào Mát Lành",
        "desc": "Mưa rào xối xả, TỰ ĐỘNG TƯỚI NƯỚC cho toàn bộ ô đất đang trồng cây!",
        "effect": "auto_water",
        "speed_multi": 1.15
    },
    {
        "id": "storm",
        "name": "⛈️ Giông Bão Sấm Sét",
        "desc": "Gió bão dữ dội! Cây không có Lồng Kính có 25% nguy cơ bị héo úa do gió quật.",
        "effect": "storm_damage",
        "speed_multi": 0.8
    },
    {
        "id": "drought",
        "name": "🔥 Nắng Gắt Hạn Hán",
        "desc": "Nắng cháy da thịt, đất khô cằn nhanh gấp đôi, cây thiếu nước sẽ bị héo ngay!",
        "effect": "fast_dry",
        "speed_multi": 0.9
    },
    {
        "id": "frost",
        "name": "🌫️ Sương Giá Băng Phủ",
        "desc": "Sương muối lạnh thấu xương, cây không có Lồng Kính bị chậm lớn 40%.",
        "effect": "frost_slow",
        "speed_multi": 0.6
    },
    {
        "id": "rainbow",
        "name": "🌈 Cầu Vồng Thần Nông",
        "desc": "Hiện tượng kỳ diệu hiếm có! Cây lớn nhanh x1.5 lần và tăng 50% sản lượng!",
        "effect": "super_grow",
        "speed_multi": 1.5
    }
]

_FARM_OVERRIDE = {
    "season": None,
    "weather": None,
    "until": 0
}

def set_farm_environment_override(season_id: Optional[str] = None, weather_id: Optional[str] = None, duration_seconds: int = 7200):
    """Admin thiết lập mùa vụ hoặc thời tiết cưỡng chế trong khoảng thời gian."""
    now = time.time()
    _FARM_OVERRIDE["season"] = season_id
    _FARM_OVERRIDE["weather"] = weather_id
    _FARM_OVERRIDE["until"] = now + duration_seconds if (season_id or weather_id) else 0

def get_current_season_and_weather() -> Tuple[Dict[str, Any], Dict[str, Any]]:
    """Tính toán mùa vụ và thời tiết hiện tại dựa theo thời gian thực hoặc thiết lập admin."""
    now = time.time()
    override_season = None
    override_weather = None
    if _FARM_OVERRIDE["until"] > now:
        if _FARM_OVERRIDE["season"] and _FARM_OVERRIDE["season"] in SEASONS_INFO:
            override_season = SEASONS_INFO[_FARM_OVERRIDE["season"]]
        if _FARM_OVERRIDE["weather"]:
            override_weather = next((w for w in FARM_WEATHER_CYCLE if w["id"] == _FARM_OVERRIDE["weather"]), None)

    day_idx = int(now // (24 * 3600)) % 4
    season_keys = ["spring", "summer", "autumn", "winter"]
    season = override_season or SEASONS_INFO[season_keys[day_idx]]

    weather_idx = int(now // 7200) % len(FARM_WEATHER_CYCLE)
    weather = override_weather or FARM_WEATHER_CYCLE[weather_idx]
    return season, weather

# ==============================================================================
# 5. CÔNG THỨC NẤU ĂN HẢI SẢN & NÔNG SẢN (COOKING RECIPES)
# ==============================================================================
FARM_COOK_RECIPES = {
    "canh_ca_ca_chua": {
        "name": "🍲 Canh Cá Cà Chua Tươi",
        "need_fish": ("common", 1),
        "need_crops": {"crop_tomato": 2, "crop_onion": 1},
        "desc": "Tăng +20 May Mắn câu cá trong 60 phút.",
        "buff_key": "luck_bonus",
        "buff_val": 20,
        "buff_duration": 3600
    },
    "sushi_ca_hoi": {
        "name": "🍣 Sushi Cá Hồi Dưa Hấu",
        "need_fish": ("rare", 1),
        "need_crops": {"crop_wheat": 3, "crop_watermelon": 1},
        "desc": "Tăng +50% Exp câu cá và Nông trại trong 90 phút.",
        "buff_key": "exp_bonus",
        "buff_val": 1.5,
        "buff_duration": 5400
    },
    "ca_nuong_ot_toi": {
        "name": "🐟 Cá Nướng Ớt Tỏi Cay Nồng",
        "need_fish": ("rare", 1),
        "need_crops": {"crop_chili": 2, "crop_garlic": 2},
        "desc": "Tăng +100% (x2) tỉ lệ gặp Cá Đột Biến trong 60 phút.",
        "buff_key": "mutation_buff",
        "buff_val": 2.0,
        "buff_duration": 3600
    },
    "salad_nong_dan": {
        "name": "🥗 Salad Nông Dân Bổ Dưỡng",
        "need_fish": ("common", 1),
        "need_crops": {"crop_carrot": 2, "crop_bokchoy": 2, "crop_corn": 1, "crop_strawberry": 2},
        "desc": "Tăng +15% tỉ lệ thành công khi Đập Đồ & Tiến Cấp Sao trong 60 phút!",
        "buff_key": "refine_luck_buff",
        "buff_val": 0.15,
        "buff_duration": 3600
    },
    "chao_nam_bat_tran": {
        "name": "🥣 Cháo Nấm Bát Trân Thượng Hạng",
        "need_fish": ("epic", 1),
        "need_crops": {"crop_mushroom": 2, "crop_wheat": 3, "crop_garlic": 1},
        "desc": "Cần câu không mất độ bền khi câu cá trong 45 phút.",
        "buff_key": "unbreakable_durability",
        "buff_val": 1,
        "buff_duration": 2700
    },
    "dai_tiec_hoang_gia": {
        "name": "👑 Đại Tiệc Hoàng Gia Sakura",
        "need_fish": ("legendary", 1),
        "need_crops": {"crop_peach": 1, "crop_snow_lotus": 1, "crop_grape": 2, "crop_golden_apple": 1},
        "desc": "Nhân đôi (x2) toàn bộ tiền bán cá và nông sản trong 3 giờ!",
        "buff_key": "double_sell_buff",
        "buff_val": 2.0,
        "buff_duration": 10800
    }
}

# ==============================================================================
# 6. LOGIC XỬ LÝ NÔNG TRẠI (FARM LOGIC HELPERS)
# ==============================================================================
def get_user_farm(u_fish: Dict[str, Any]) -> Dict[str, Any]:
    """Khởi tạo và lấy dữ liệu trang trại của người dùng."""
    farm = u_fish.setdefault("farm", {})
    farm.setdefault("plots_count", 4)
    plots = farm.setdefault("plots", [])
    
    max_plots = farm.get("plots_count", 4)
    while len(plots) < max_plots:
        plot_idx = len(plots) + 1
        plots.append({
            "id": plot_idx,
            "seed": None,
            "planted_at": 0,
            "grow_seconds": 0,
            "watered": False,
            "watered_at": 0,
            "fertilizer": None,
            "pests": False,
            "pest_type": None,
            "wilted": False,
            "greenhouse": False
        })
    
    farm.setdefault("crops", {})
    farm.setdefault("seeds", {
        "seed_wheat": 3,
        "seed_carrot": 2
    })
    farm.setdefault("pests", {})
    farm.setdefault("tools", {})
    farm.setdefault("fertilizers", {
        "fertilizer_organic": 2
    })
    farm.setdefault("materials", {
        "stardust_dust": 0,
        "black_pearl": 0,
        "end_crystal": 0,
        "special_enchant_stone": 0
    })
    farm.setdefault("mutated_crops", [])
    return farm

def update_farm_state(farm: Dict[str, Any]) -> Tuple[List[str], bool]:
    """Cập nhật trạng thái lớn lên, thiếu nước, sâu bọ của cây trong các ô đất."""
    now = time.time()
    season, weather = get_current_season_and_weather()
    logs = []
    has_changes = False

    tools = farm.get("tools", {})
    water_dur = 7200 # 2 giờ
    if tools.get("watering_can_mythic", 0) > 0:
        water_dur = 86400
    elif tools.get("watering_can_silver", 0) > 0:
        water_dur = 28800
    elif tools.get("watering_can_copper", 0) > 0:
        water_dur = 14400

    is_rainy = (weather.get("effect") == "auto_water")

    for p in farm.get("plots", []):
        if not p.get("seed"):
            continue
        
        # Mưa rào tự động tưới nước
        if is_rainy and not p.get("watered"):
            p["watered"] = True
            p["watered_at"] = now
            has_changes = True

        # Độ ẩm đất
        if p.get("watered"):
            dry_rate = 2.0 if weather.get("effect") == "fast_dry" else 1.0
            actual_dur = water_dur / dry_rate
            if now - p.get("watered_at", 0) > actual_dur:
                p["watered"] = False
                has_changes = True

        # Héo úa do thiếu nước
        if not p.get("watered") and not p.get("wilted"):
            time_since_water = now - p.get("watered_at", 0)
            if time_since_water > (water_dur * 1.5):
                p["wilted"] = True
                has_changes = True
                logs.append(f"⚠️ Ô đất #{p['id']} cây bị héo do thiếu nước quá lâu!")

        # Bão giông quật cây nếu không có lồng kính
        if weather.get("effect") == "storm_damage" and not p.get("greenhouse") and not p.get("wilted"):
            if random.random() < 0.15:
                p["wilted"] = True
                has_changes = True
                logs.append(f"⛈️ Giông bão quật ngã cây ở ô đất #{p['id']}!")

        # Xuất hiện sâu bọ ngẫu nhiên
        if not p.get("wilted") and not p.get("pests") and p.get("watered"):
            if random.random() < 0.12:
                p["pests"] = True
                p["pest_type"] = random.choices(
                    ["caterpillar", "ladybug", "beetle", "golden_cicada", "rainbow_butterfly"],
                    weights=[50, 30, 14, 5, 1],
                    k=1
                )[0]
                has_changes = True
                pest_name = PESTS_CATALOG[p["pest_type"]]["name"]
                logs.append(f"🐛 Xuất hiện {pest_name} gặm lá ở ô đất #{p['id']}!")

    return logs, has_changes

def get_plot_growth_progress(plot: Dict[str, Any], season: Dict[str, Any], weather: Dict[str, Any]) -> Tuple[float, bool]:
    """Tính toán % trưởng thành của ô đất và xem đã sẵn sàng thu hoạch chưa."""
    if not plot.get("seed"):
        return 0.0, False
    if plot.get("wilted"):
        return 0.0, False # Cây bị héo úa ngừng lớn

    now = time.time()
    s_info = SEEDS_CATALOG.get(plot["seed"], {})
    base_sec = s_info.get("grow_seconds", 300)

    # Hiệu ứng phân bón
    speed_factor = 1.0
    fert_id = plot.get("fertilizer")
    if fert_id and fert_id in FARM_TOOLS_CATALOG:
        speed_factor += FARM_TOOLS_CATALOG[fert_id].get("speed_bonus", 0.0)

    # Hiệu ứng mùa màng
    crop_id = s_info.get("crop_id")
    if crop_id in season.get("favored_crops", []):
        speed_factor += 0.25

    # Hiệu ứng thời tiết
    speed_factor *= weather.get("speed_multi", 1.0)

    # Bị sâu bọ làm chậm 50%
    if plot.get("pests"):
        speed_factor *= 0.5

    # Thiếu nước làm chậm 50%
    if not plot.get("watered"):
        speed_factor *= 0.5

    effective_grow_time = max(30.0, base_sec / max(0.1, speed_factor))
    elapsed = now - plot.get("planted_at", now)
    pct = min(100.0, (elapsed / effective_grow_time) * 100.0)
    is_ready = (pct >= 100.0)
    return pct, is_ready

# ==============================================================================
# 7. GIAO DIỆN NÔNG TRẠI TƯƠNG TÁC (FARM VIEW)
# ==============================================================================
class FarmView(discord.ui.View):
    def __init__(self, author: discord.Member, guild_id: int):
        super().__init__(timeout=240)
        self.author = author
        self.guild_id = guild_id
        self.vi = is_vietnamese(guild_id)
        self.selected_plot_id = 1
        self._refresh_components()

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user != self.author:
            msg = "❌ Đây không phải trang trại của bạn!" if self.vi else "❌ This is not your farm!"
            await interaction.response.send_message(msg, ephemeral=True)
            return False
        return True

    def _refresh_components(self):
        from Command.command_fishing import get_user_fishing, save_fishing_data
        self.clear_items()
        u_fish = get_user_fishing(self.author.id)
        farm = get_user_farm(u_fish)
        update_farm_state(farm)
        save_fishing_data()

        plots = farm.get("plots", [])
        season, weather = get_current_season_and_weather()

        # Row 0: Chọn ô đất
        plot_options = []
        for p in plots:
            pct, ready = get_plot_growth_progress(p, season, weather)
            s_name = SEEDS_CATALOG[p["seed"]]["name"] if p.get("seed") else ("Đất trống" if self.vi else "Empty Plot")
            if self.vi:
                status_tag = "🌿 Sẵn sàng thu hoạch!" if ready else (f"🌱 Lớn {int(pct)}%" if p.get("seed") else "🟫 Đất trống")
                if p.get("wilted"):
                    status_tag = "🍂 Héo úa!"
                elif p.get("pests"):
                    status_tag += " • 🐛 Có sâu"
            else:
                status_tag = "🌿 Ready to harvest!" if ready else (f"🌱 Growing {int(pct)}%" if p.get("seed") else "🟫 Empty Plot")
                if p.get("wilted"):
                    status_tag = "🍂 Wilted!"
                elif p.get("pests"):
                    status_tag += " • 🐛 Has pests"

            plot_options.append(
                discord.SelectOption(
                    label=f"Ô #{p['id']}: {s_name}"[:100] if self.vi else f"Plot #{p['id']}: {s_name}"[:100],
                    value=str(p["id"]),
                    description=status_tag[:100],
                    default=(p["id"] == self.selected_plot_id),
                    emoji="🪴"
                )
            )

        if plot_options:
            sel_ph = "🪴 Chọn ô đất cần thao tác..." if self.vi else "🪴 Select plot to interact..."
            sel = discord.ui.Select(placeholder=sel_ph, options=plot_options, row=0)
            sel.callback = self._select_plot_callback
            self.add_item(sel)

        # Row 1: Gieo hạt (chọn hạt giống nếu ô trống)
        cur_plot = next((p for p in plots if p["id"] == self.selected_plot_id), None)
        seeds_inv = farm.get("seeds", {})

        if cur_plot and not cur_plot.get("seed"):
            seed_options = []
            for sid, count in seeds_inv.items():
                if count > 0 and sid in SEEDS_CATALOG:
                    s_info = SEEDS_CATALOG[sid]
                    mins = max(1, s_info["grow_seconds"] // 60)
                    desc_s = f"Thời gian: ~{mins}p | Thu: {s_info['crop_name']}" if self.vi else f"Growth: ~{mins}m | Yield: {s_info['crop_name']}"
                    seed_options.append(
                        discord.SelectOption(
                            label=f"{s_info['name']} (x{count})"[:100],
                            value=sid,
                            description=desc_s[:100],
                            emoji="🌱"
                        )
                    )
            if seed_options:
                seed_ph = f"🌱 Gieo hạt vào Ô #{self.selected_plot_id}..." if self.vi else f"🌱 Plant seed in Plot #{self.selected_plot_id}..."
                seed_select = discord.ui.Select(placeholder=seed_ph, options=seed_options[:25], row=1)
                seed_select.callback = self._plant_seed_callback
                self.add_item(seed_select)

        # Row 2: Các nút hành động chính
        water_btn = discord.ui.Button(label="Tưới Nước Toàn Bộ" if self.vi else "Water All", style=discord.ButtonStyle.primary, emoji="💧", row=2)
        water_btn.callback = self._water_all_callback
        self.add_item(water_btn)

        harvest_btn = discord.ui.Button(label="Thu Hoạch Hết" if self.vi else "Harvest All", style=discord.ButtonStyle.success, emoji="🌾", row=2)
        harvest_btn.callback = self._harvest_all_callback
        self.add_item(harvest_btn)

        pest_btn = discord.ui.Button(label="Bắt Sâu Bọ" if self.vi else "Catch Pests", style=discord.ButtonStyle.secondary, emoji="🐛", row=2)
        pest_btn.callback = self._catch_pest_callback
        self.add_item(pest_btn)

        revive_btn = discord.ui.Button(label="Cứu Cây Héo" if self.vi else "Revive Wilted", style=discord.ButtonStyle.secondary, emoji="💖", row=2)
        revive_btn.callback = self._revive_callback
        self.add_item(revive_btn)

        # Row 3: Bón phân, Shop Nông trại, Túi Farmer
        fert_btn = discord.ui.Button(label="Bón Phân" if self.vi else "Fertilize", style=discord.ButtonStyle.secondary, emoji="🧪", row=3)
        fert_btn.callback = self._open_fertilize_modal
        self.add_item(fert_btn)

        shop_btn = discord.ui.Button(label="Shop Hạt Giống" if self.vi else "Seed Shop", style=discord.ButtonStyle.secondary, emoji="🏪", row=3)
        shop_btn.callback = self._open_farm_shop
        self.add_item(shop_btn)

        bag_btn = discord.ui.Button(label="Kho Nông Dân" if self.vi else "Farmer Bag", style=discord.ButtonStyle.primary, emoji="🎒", row=3)
        bag_btn.callback = self._goto_farm_bag
        self.add_item(bag_btn)

        cook_btn = discord.ui.Button(label="Bếp Nấu Ăn" if self.vi else "Kitchen", style=discord.ButtonStyle.secondary, emoji="🍳", row=3)
        cook_btn.callback = self._goto_cooking
        self.add_item(cook_btn)

        expand_btn = discord.ui.Button(label="Mở Rộng Đất" if self.vi else "Expand Farm", style=discord.ButtonStyle.secondary, emoji="🚜", row=3)
        expand_btn.callback = self._expand_plots_callback
        self.add_item(expand_btn)

    def build_embed(self) -> discord.Embed:
        from Command.command_fishing import get_user_fishing
        u_fish = get_user_fishing(self.author.id)
        farm = get_user_farm(u_fish)
        season, weather = get_current_season_and_weather()

        if self.vi:
            title_txt = f"🌾 TRANG TRẠI NÔNG DÂN: {self.author.display_name.upper()}"
            desc_txt = f"**Mùa vụ:** {season['name']} • **Thời tiết:** {weather['name']}\n> *{weather['desc']}*"
        else:
            title_txt = f"🌾 FARMER'S FIELD: {self.author.display_name.upper()}"
            desc_txt = f"**Season:** {season['name']} • **Weather:** {weather['name']}\n> *{weather['desc']}*"

        embed = discord.Embed(
            title=title_txt,
            description=desc_txt,
            color=season.get("color", 0x76B852)
        )

        plots = farm.get("plots", [])
        plot_lines = []
        for p in plots:
            pct, ready = get_plot_growth_progress(p, season, weather)
            pid = p["id"]
            if not p.get("seed"):
                empty_lbl = f"**Ô #{pid}:** 🟫 *Đất trống sẵn sàng gieo hạt*" if self.vi else f"**Plot #{pid}:** 🟫 *Empty plot ready for planting*"
                plot_lines.append(empty_lbl)
            else:
                s_info = SEEDS_CATALOG.get(p["seed"], {})
                s_name = s_info.get("name", "Cây")
                c_name = s_info.get("crop_name", "Nông sản")

                if p.get("wilted"):
                    status = "🍂 **BỊ HÉO ÚA!** Cần cứu ngay!" if self.vi else "🍂 **WILTED!** Needs immediate revival!"
                elif ready:
                    status = f"✨ **ĐÃ CHÍN!** Thu hoạch được `{c_name}`" if self.vi else f"✨ **RIPE!** Ready to harvest `{c_name}`"
                else:
                    bar_len = 6
                    filled = int(bar_len * (pct / 100))
                    bar = "🌱" * filled + "░" * (bar_len - filled)
                    status = f"`[{bar}] {int(pct)}%`"

                extras = []
                if p.get("watered"):
                    extras.append("💧 Ẩm" if self.vi else "💧 Moist")
                else:
                    extras.append("⚠️ Khô" if self.vi else "⚠️ Dry")
                if p.get("pests"):
                    p_name = PESTS_CATALOG.get(p.get("pest_type"), {}).get("name", "Sâu")
                    extras.append(f"{p_name}")
                if p.get("fertilizer"):
                    extras.append("🧪 Có phân" if self.vi else "🧪 Fertilized")
                if p.get("greenhouse"):
                    extras.append("🏛️ Lồng kính" if self.vi else "🏛️ Greenhouse")

                extra_str = f" ({', '.join(extras)})" if extras else ""
                plot_prefix = f"**Ô #{pid}:**" if self.vi else f"**Plot #{pid}:**"
                plot_lines.append(f"{plot_prefix} {s_name} — {status}{extra_str}")

        # Chia các ô đất hợp lý để không vượt quá 1024 ký tự
        plots_field_name = f"🪴 Ô Đất Canh Tác ({len(plots)}/{farm.get('plots_count', 4)} ô)" if self.vi else f"🪴 Farming Plots ({len(plots)}/{farm.get('plots_count', 4)} plots)"
        if len(plot_lines) > 8:
            part1 = plot_lines[:8]
            part2 = plot_lines[8:]
            fn1 = f"🪴 Ô Đất Canh Tác (1-{len(part1)}/{len(plots)} ô)" if self.vi else f"🪴 Farming Plots (1-{len(part1)}/{len(plots)})"
            fn2 = f"🪴 Ô Đất Canh Tác ({len(part1)+1}-{len(plots)}/{len(plots)} ô)" if self.vi else f"🪴 Farming Plots ({len(part1)+1}-{len(plots)})"
            safe_add_field(embed, fn1, "\n".join(part1), inline=False)
            safe_add_field(embed, fn2, "\n".join(part2), inline=False)
        else:
            safe_add_field(embed, plots_field_name, "\n".join(plot_lines) if plot_lines else ("*Chưa có ô đất nào.*" if self.vi else "*No farming plots available.*"), inline=False)

        # Thông tin kho nhanh
        crops = farm.get("crops", {})
        crop_summary = [f"{SEEDS_CATALOG.get(f'seed_{k[5:]}', {}).get('crop_name', k)}: `x{cnt}`" for k, cnt in crops.items() if cnt > 0]
        seeds = farm.get("seeds", {})
        seed_summary = [f"{SEEDS_CATALOG.get(k, {}).get('name', k)}: `x{cnt}`" for k, cnt in seeds.items() if cnt > 0]
        pests = farm.get("pests", {})
        pest_summary = [f"{PESTS_CATALOG.get(k, {}).get('name', k)}: `x{cnt}`" for k, cnt in pests.items() if cnt > 0]

        empty_txt = "*Trống*" if self.vi else "*Empty*"
        no_seed_txt = "*Hết hạt*" if self.vi else "*No seeds*"
        no_pest_txt = "*Không có*" if self.vi else "*None*"

        crop_str = ", ".join(crop_summary[:4]) if crop_summary else empty_txt
        if len(crop_summary) > 4:
            crop_str += f" *(+{len(crop_summary)-4} {'loại khác' if self.vi else 'more'})*"

        seed_str = ", ".join(seed_summary[:4]) if seed_summary else no_seed_txt
        if len(seed_summary) > 4:
            seed_str += f" *(+{len(seed_summary)-4} {'loại khác' if self.vi else 'more'})*"

        pest_str = ", ".join(pest_summary[:3]) if pest_summary else no_pest_txt
        if len(pest_summary) > 3:
            pest_str += f" *(+{len(pest_summary)-3} {'con khác' if self.vi else 'more'})*"

        if self.vi:
            inv_text = (
                f"• **Nông sản:** {crop_str}\n"
                f"• **Hạt giống:** {seed_str}\n"
                f"• **Sâu bọ:** {pest_str}"
            )
            inv_hdr = "🎒 Nông Sản & Hạt Giống Đang Có"
            footer_txt = "Bấm [Tưới Nước] để giữ ẩm, [Bắt Sâu] để bảo vệ cây và thu mồi câu cá!"
        else:
            inv_text = (
                f"• **Crops:** {crop_str}\n"
                f"• **Seeds:** {seed_str}\n"
                f"• **Pests:** {pest_str}"
            )
            inv_hdr = "🎒 Farm Storage & Seeds"
            footer_txt = "Click [Water All] to hydrate, [Catch Pests] to protect crops & obtain fish bait!"

        safe_add_field(embed, name=inv_hdr, value=inv_text, inline=False)
        embed.set_footer(text=footer_txt)
        return embed

    async def _select_plot_callback(self, interaction: discord.Interaction):
        self.selected_plot_id = int(interaction.data["values"][0])
        self._refresh_components()
        await interaction.response.edit_message(embed=self.build_embed(), view=self)

    async def _plant_seed_callback(self, interaction: discord.Interaction):
        from Command.command_fishing import get_user_fishing, save_fishing_data
        seed_id = interaction.data["values"][0]
        u_fish = get_user_fishing(self.author.id)
        farm = get_user_farm(u_fish)
        seeds_inv = farm.setdefault("seeds", {})

        if seeds_inv.get(seed_id, 0) <= 0:
            return await interaction.response.send_message("❌ Bạn không có hạt giống này trong túi!" if self.vi else "❌ You do not have this seed in your bag!", ephemeral=True)

        plots = farm.get("plots", [])
        cur_plot = next((p for p in plots if p["id"] == self.selected_plot_id), None)
        if not cur_plot or cur_plot.get("seed"):
            return await interaction.response.send_message("❌ Ô đất này đã có cây trồng rồi!" if self.vi else "❌ This plot already has a crop growing!", ephemeral=True)

        seeds_inv[seed_id] -= 1
        s_info = SEEDS_CATALOG[seed_id]
        cur_plot["seed"] = seed_id
        cur_plot["planted_at"] = time.time()

        # Kiểm tra dòng Enchant Farmer Tinh Nhuệ (farm_speed) từ cần câu đang trang bị
        from Command.command_fishing import get_rod_enchant_stats
        equipped_rod_id = u_fish.get("equipped_rod")
        cur_rod = u_fish.get("rods", {}).get(equipped_rod_id, {}) if equipped_rod_id else {}
        ench_stats = get_rod_enchant_stats(cur_rod)
        farm_speed_bonus = ench_stats.get("farm_speed", 0)
        speed_factor = 1.0 - (min(farm_speed_bonus, 50) / 100.0)
        cur_plot["grow_seconds"] = max(30, int(s_info["grow_seconds"] * speed_factor))

        cur_plot["watered"] = True # Vừa gieo tự động có độ ẩm ban đầu
        cur_plot["watered_at"] = time.time()
        cur_plot["fertilizer"] = None
        cur_plot["pests"] = False
        cur_plot["pest_type"] = None
        cur_plot["wilted"] = False

        save_fishing_data()
        self._refresh_components()
        await interaction.response.edit_message(embed=self.build_embed(), view=self)
        plant_msg = f"🌱 Đã gieo thành công **{s_info['name']}** vào Ô đất #{self.selected_plot_id}!" if self.vi else f"🌱 Successfully planted **{s_info['name']}** into Plot #{self.selected_plot_id}!"
        await interaction.followup.send(plant_msg, ephemeral=True)

    async def _water_all_callback(self, interaction: discord.Interaction):
        from Command.command_fishing import get_user_fishing, save_fishing_data
        u_fish = get_user_fishing(self.author.id)
        farm = get_user_farm(u_fish)
        now = time.time()
        count = 0
        for p in farm.get("plots", []):
            if p.get("seed"):
                p["watered"] = True
                p["watered_at"] = now
                count += 1

        save_fishing_data()
        self._refresh_components()
        await interaction.response.edit_message(embed=self.build_embed(), view=self)
        water_msg = f"💧 Đã tưới nước mát lành cho toàn bộ **{count}** ô đất đang canh tác!" if self.vi else f"💧 Thoroughly watered all **{count}** active crop plots!"
        await interaction.followup.send(water_msg, ephemeral=True)

    async def _harvest_all_callback(self, interaction: discord.Interaction):
        from Command.command_fishing import get_user_fishing, save_fishing_data
        u_fish = get_user_fishing(self.author.id)
        farm = get_user_farm(u_fish)
        season, weather = get_current_season_and_weather()
        crops_inv = farm.setdefault("crops", {})
        mutated_crops = farm.setdefault("mutated_crops", [])

        tools = farm.get("tools", {})
        has_gloves = tools.get("farmer_gloves", 0) > 0
        weather_id = weather.get("id", "sunny")

        base_mutation_chance = 0.10
        if weather_id == "rainbow":
            base_mutation_chance += 0.30
        elif weather_id == "sunny":
            base_mutation_chance += 0.05
        if has_gloves:
            base_mutation_chance += 0.15

        harvested = {}
        mutation_events = []
        stardust_found = 0

        for p in farm.get("plots", []):
            pct, ready = get_plot_growth_progress(p, season, weather)
            if ready and p.get("seed"):
                s_info = SEEDS_CATALOG[p["seed"]]
                crop_id = s_info["crop_id"]
                yield_cnt = random.randint(s_info["yield_min"], s_info["yield_max"])

                plot_fert = p.get("fertilizer")
                # Phân bội thu
                if plot_fert == "fertilizer_yield":
                    yield_cnt = int(yield_cnt * 2)

                # Mùa màng ưu đãi
                if crop_id in season.get("favored_crops", []):
                    yield_cnt = int(yield_cnt * 1.3)

                # Kiểm tra ĐỘT BIẾN NÔNG SẢN
                mut_chance = base_mutation_chance
                if plot_fert == "fertilizer_mythic":
                    mut_chance += 0.25

                if random.random() < mut_chance:
                    weights = [m["weight"] for m in CROP_MUTATIONS]
                    mut_chosen = random.choices(CROP_MUTATIONS, weights=weights, k=1)[0]
                    base_price = s_info.get("sell_price", 500)
                    mut_price = int(base_price * mut_chosen["price_multi"])

                    mut_item = {
                        "crop_id": crop_id,
                        "crop_name": s_info["crop_name"],
                        "mutation_id": mut_chosen["id"],
                        "mutation_name": mut_chosen["name"],
                        "prefix": mut_chosen["prefix"],
                        "sell_price": mut_price,
                        "buff_durability": mut_chosen.get("buff_durability", 40),
                        "harvested_at": time.time()
                    }
                    mutated_crops.append(mut_item)
                    mutation_events.append(f"{mut_chosen['prefix']} **{s_info['crop_name']}** (Trị giá: `{mut_price:,}`c)")

                    if mut_chosen["id"] == "divine":
                        bonus_star = random.randint(1, 2)
                        stardust_found += bonus_star
                        materials = farm.setdefault("materials", {})
                        materials["stardust_dust"] = materials.get("stardust_dust", 0) + bonus_star

                crops_inv[crop_id] = crops_inv.get(crop_id, 0) + yield_cnt
                harvested[s_info["crop_name"]] = harvested.get(s_info["crop_name"], 0) + yield_cnt

                # Reset ô đất
                p["seed"] = None
                p["planted_at"] = 0
                p["watered"] = False
                p["fertilizer"] = None
                p["pests"] = False
                p["pest_type"] = None
                p["wilted"] = False

        if not harvested:
            return await interaction.response.send_message("❌ Chưa có cây nào chín để thu hoạch!" if self.vi else "❌ No crops are ripe for harvest yet!", ephemeral=True)

        save_fishing_data()
        self._refresh_components()
        await interaction.response.edit_message(embed=self.build_embed(), view=self)
        lines = [f"• {c_name}: **+{cnt}**" for c_name, cnt in harvested.items()]
        msg = "🌾 **VỤ MÙA BỘI THU!** Bạn đã thu hoạch được:\n" + "\n".join(lines)
        if mutation_events:
            msg += "\n\n🧬 **ĐỘT BIẾN NÔNG SẢN XUẤT HIỆN!**\n" + "\n".join(f"✨ {m}" for m in mutation_events)
        if stardust_found > 0:
            msg += f"\n\n🌟 *Linh khí Thần Nông: Nhận thêm **+{stardust_found} Bụi Sao Lấp Lánh** để tiến cấp sao cần câu!*"
        if len(msg) > 1900:
            msg = msg[:1890] + "\n*(...và còn nhiều nông sản khác)*"
        await interaction.followup.send(msg, ephemeral=False)

    async def _catch_pest_callback(self, interaction: discord.Interaction):
        from Command.command_fishing import get_user_fishing, save_fishing_data
        u_fish = get_user_fishing(self.author.id)
        farm = get_user_farm(u_fish)
        pests_inv = farm.setdefault("pests", {})

        caught = {}
        for p in farm.get("plots", []):
            if p.get("pests") and p.get("pest_type"):
                ptype = p["pest_type"]
                pests_inv[ptype] = pests_inv.get(ptype, 0) + 1
                p_name = PESTS_CATALOG.get(ptype, {}).get("name", "Sâu")
                caught[p_name] = caught.get(p_name, 0) + 1
                p["pests"] = False
                p["pest_type"] = None

        if not caught:
            return await interaction.response.send_message("🐞 Toàn bộ các ô đất đều sạch bóng sâu bọ!" if self.vi else "🐞 All farming plots are completely pest-free!", ephemeral=True)

        save_fishing_data()
        self._refresh_components()
        await interaction.response.edit_message(embed=self.build_embed(), view=self)
        lines = [f"• {p_name}: **+1 con**" for p_name in caught]
        await interaction.followup.send("🐛 **BẮT SÂU THÀNH CÔNG!** Đã bắt được:\n" + "\n".join(lines) + "\n*(Sâu bọ đã chuyển vào túi nông dân để bán hoặc làm mồi câu)*", ephemeral=True)

    async def _revive_callback(self, interaction: discord.Interaction):
        from Command.command_fishing import get_user_fishing, save_fishing_data
        u_fish = get_user_fishing(self.author.id)
        farm = get_user_farm(u_fish)
        ferts = farm.setdefault("fertilizers", {})

        cur_plot = next((p for p in farm.get("plots", []) if p["id"] == self.selected_plot_id), None)
        if not cur_plot or not cur_plot.get("wilted"):
            return await interaction.response.send_message("🌿 Cây ở ô đất này vẫn đang xanh tốt, không bị héo úa!" if self.vi else "🌿 Crops in this plot are healthy and thriving!", ephemeral=True)

        # Cần Phân Hồi Sinh hoặc Nước + Coins
        if ferts.get("fertilizer_revive", 0) > 0:
            ferts["fertilizer_revive"] -= 1
            cur_plot["wilted"] = False
            cur_plot["watered"] = True
            cur_plot["watered_at"] = time.time()
            msg = "💖 Bạn đã dùng **1x Phân Kích Rễ Hồi Sinh** để cứu sống cây trồng!" if self.vi else "💖 You used **1x Revive Root Fertilizer** to restore the wilted crop!"
        else:
            u_data = await get_user_data(self.guild_id, self.author.id)
            cost = 10000
            if u_data.get("coins", 0) < cost:
                return await interaction.response.send_message(f"❌ Không đủ coin hoặc Phân Hồi Sinh! Cần **`{cost:,}` coin** để hồi phục cây héo." if self.vi else f"❌ Not enough coins or Revive Fertilizer! Need **`{cost:,}` coins** to revive.", ephemeral=True)
            await update_user_coins(self.guild_id, self.author.id, -cost)
            cur_plot["wilted"] = False
            cur_plot["watered"] = True
            cur_plot["watered_at"] = time.time()
            msg = f"💖 Bạn đã chi **`{cost:,}` coin** chăm bón và hồi sinh cây trồng thành công!" if self.vi else f"💖 You spent **`{cost:,}` coins** to nurture and revive the crop!"

        save_fishing_data()
        self._refresh_components()
        await interaction.response.edit_message(embed=self.build_embed(), view=self)
        await interaction.followup.send(msg, ephemeral=True)

    async def _open_fertilize_modal(self, interaction: discord.Interaction):
        from Command.command_fishing import get_user_fishing, save_fishing_data
        u_fish = get_user_fishing(self.author.id)
        farm = get_user_farm(u_fish)
        ferts = farm.get("fertilizers", {})

        cur_plot = next((p for p in farm.get("plots", []) if p["id"] == self.selected_plot_id), None)
        if not cur_plot or not cur_plot.get("seed"):
            return await interaction.response.send_message("❌ Ô đất này chưa có cây trồng để bón phân!", ephemeral=True)

        class FertilizeSelectView(discord.ui.View):
            def __init__(self, parent_view: "FarmView"):
                super().__init__(timeout=60)
                self.parent_view = parent_view
                options = []
                for fid, cnt in ferts.items():
                    if cnt > 0 and fid in FARM_TOOLS_CATALOG:
                        f_info = FARM_TOOLS_CATALOG[fid]
                        options.append(discord.SelectOption(
                            label=f"{f_info['name']} (x{cnt})",
                            value=fid,
                            description=f_info["desc"][:100],
                            emoji="🧪"
                        ))
                if options:
                    sel = discord.ui.Select(placeholder="🧪 Chọn loại phân muốn bón...", options=options)
                    sel.callback = self._select_fert
                    self.add_item(sel)

            async def _select_fert(self, inter: discord.Interaction):
                fid = inter.data["values"][0]
                ferts[fid] -= 1
                cur_plot["fertilizer"] = fid
                save_fishing_data()
                self.parent_view._refresh_components()
                await inter.response.edit_message(content=f"✅ Đã bón **{FARM_TOOLS_CATALOG[fid]['name']}** cho Ô đất #{self.parent_view.selected_plot_id}!", view=None)

        view = FertilizeSelectView(self)
        if not view.children:
            return await interaction.response.send_message("❌ Bạn không có phân bón nào trong túi! Hãy mua tại Shop Nông Trại.", ephemeral=True)
        await interaction.response.send_message("🧪 **CHỌN PHÂN BÓN ĐỂ TĂNG TỐC VỤ MÙA:**", view=view, ephemeral=True)

    async def _open_farm_shop(self, interaction: discord.Interaction):
        from Command.command_fishing import FishingShopView
        shop_view = FishingShopView(self.author, self.guild_id)
        shop_view.category = "farm"
        shop_view._build_components()
        await interaction.response.send_message(embed=shop_view.build_embed(), view=shop_view, ephemeral=True)

    async def _goto_farm_bag(self, interaction: discord.Interaction):
        from Command.command_fishing import FishingInventoryView
        inv_view = FishingInventoryView(self.author, self.guild_id)
        inv_view.inv_page = 2 # Trang 3 (Farmer)
        inv_view._build_components()
        u_data = await get_user_data(self.guild_id, self.author.id)
        await interaction.response.edit_message(embed=inv_view.build_embed(u_data.get("coins", 0), u_data.get("xu", 0)), view=inv_view)

    async def _goto_cooking(self, interaction: discord.Interaction):
        from Command.command_fishing import CookingView
        cook_view = CookingView(self.author, self.guild_id)
        await interaction.response.edit_message(embed=cook_view.build_embed(), view=cook_view)

    async def _expand_plots_callback(self, interaction: discord.Interaction):
        from Command.command_fishing import get_user_fishing, save_fishing_data
        u_fish = get_user_fishing(self.author.id)
        farm = get_user_farm(u_fish)
        cur_plots = farm.get("plots_count", 4)

        if cur_plots >= 16:
            return await interaction.response.send_message("👑 Trang trại của bạn đã mở rộng tối đa (16 ô đất)!" if self.vi else "👑 Your farm is already at maximum capacity (16 plots)!", ephemeral=True)

        # Bảng giá mở rộng
        costs = {4: 100000, 6: 500000, 8: 2000000, 10: 5000000, 12: 12000000, 14: 25000000}
        cost = costs.get(cur_plots, 5000000)
        u_data = await get_user_data(self.guild_id, self.author.id)

        if u_data.get("coins", 0) < cost:
            return await interaction.response.send_message(f"❌ Không đủ coin! Cần **`{cost:,}` coin** để khai hoang thêm 2 ô đất mới (lên {cur_plots + 2} ô)." if self.vi else f"❌ Not enough coins! Need **`{cost:,}` coins** to clear 2 new plots (up to {cur_plots + 2} plots).", ephemeral=True)

        await update_user_coins(self.guild_id, self.author.id, -cost)
        farm["plots_count"] = cur_plots + 2
        # Cập nhật thêm các ô mới vào list
        plots = farm.setdefault("plots", [])
        while len(plots) < farm["plots_count"]:
            plots.append({
                "id": len(plots) + 1,
                "seed": None,
                "planted_at": 0,
                "grow_seconds": 0,
                "watered": False,
                "watered_at": 0,
                "fertilizer": None,
                "pests": False,
                "pest_type": None,
                "wilted": False,
                "greenhouse": False
            })

        save_fishing_data()
        self._refresh_components()
        await interaction.response.edit_message(embed=self.build_embed(), view=self)
        exp_msg = f"🚜 **KHAI HOANG THÀNH CÔNG!** Trang trại của bạn đã nâng lên **{farm['plots_count']} ô đất**!" if self.vi else f"🚜 **EXPANSION COMPLETE!** Your farm now has **{farm['plots_count']} plots**!"
        await interaction.followup.send(exp_msg, ephemeral=False)


async def setup(bot):
    """Extension setup handler for discord.py (supports bot.load_extension)."""
    pass


