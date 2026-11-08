import io
import aiohttp
import asyncio
from PIL import Image, ImageDraw, ImageFont, ImageFilter

def create_gradient_mask(size: tuple[int, int], color1: tuple, color2: tuple) -> Image.Image:
    """Tạo gradient ngang rực rỡ và hiện đại"""
    width, height = size
    base = Image.new("RGBA", (width, height), color1)
    top = Image.new("RGBA", (width, height), color2)
    mask = Image.new("L", (width, height))
    mask_data = []
    for y in range(height):
        for x in range(width):
            mask_data.append(int(255 * (x / max(1, width - 1))))
    mask.putdata(mask_data)
    base.paste(top, (0, 0), mask)
    return base

def draw_circle_avatar(avatar_img: Image.Image, size: int) -> Image.Image:
    avatar_img = avatar_img.resize((size, size), Image.Resampling.LANCZOS).convert("RGBA")
    mask = Image.new("L", (size, size), 0)
    draw = ImageDraw.Draw(mask)
    draw.ellipse((0, 0, size, size), fill=255)
    output = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    output.paste(avatar_img, (0, 0), mask=mask)
    return output

def _generate_rank_card_sync(
    avatar_bytes: bytes,
    username: str,
    level: int,
    current_xp: int,
    next_xp: int,
    rank_num: int,
    coins: int = 0,
    voice_time_str: str = ""
) -> io.BytesIO:
    width, height = 960, 310

    # 1. Background hiện đại dạng Cyberpunk/Modern Dark (nền tối mượt, bo góc)
    card = Image.new("RGBA", (width, height), (15, 17, 24, 255))
    draw = ImageDraw.Draw(card)

    # Thẻ chính có viền neon nhẹ
    draw.rounded_rectangle([(0, 0), (width, height)], radius=28, fill=(16, 18, 27, 255), outline=(55, 62, 85, 255), width=2)

    # 2. Hiệu ứng hình ảnh nền sống động (Ambient glow)
    glow_layer = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    glow_draw = ImageDraw.Draw(glow_layer)
    glow_draw.ellipse((20, 20, 320, 280), fill=(138, 43, 226, 75))
    glow_draw.ellipse((width - 320, -40, width + 50, 220), fill=(0, 210, 255, 50))
    glow_layer = glow_layer.filter(ImageFilter.GaussianBlur(55))
    card.alpha_composite(glow_layer)

    # Khung nền nội dung Glassmorphism
    inner_card = Image.new("RGBA", (width - 32, height - 32), (25, 28, 40, 195))
    inner_mask = Image.new("L", (width - 32, height - 32), 0)
    inner_draw = ImageDraw.Draw(inner_mask)
    inner_draw.rounded_rectangle([(0, 0), (width - 32, height - 32)], radius=22, fill=255)
    card.paste(inner_card, (16, 16), mask=inner_mask)

    draw = ImageDraw.Draw(card)
    draw.rounded_rectangle([(16, 16), (width - 16, height - 16)], radius=22, outline=(60, 68, 95, 130), width=1)

    # 3. Avatar với viền sáng kép rực rỡ
    avatar_size = 175
    avatar_x, avatar_y = 48, 65

    outer_ring_box = (avatar_x - 6, avatar_y - 6, avatar_x + avatar_size + 6, avatar_y + avatar_size + 6)
    draw.ellipse(outer_ring_box, outline=(168, 85, 247, 240), width=4)

    try:
        avatar_raw = Image.open(io.BytesIO(avatar_bytes))
        avatar = draw_circle_avatar(avatar_raw, avatar_size)
        card.paste(avatar, (avatar_x, avatar_y), mask=avatar.getchannel("A"))
    except Exception:
        draw.ellipse((avatar_x, avatar_y, avatar_x + avatar_size, avatar_y + avatar_size), fill=(45, 52, 70, 255))
        draw.ellipse((avatar_x + 50, avatar_y + 40, avatar_x + 120, avatar_y + 110), fill=(140, 150, 175, 255))

    # Huy hiệu chấm trạng thái online
    draw.ellipse(
        (avatar_x + avatar_size - 32, avatar_y + avatar_size - 32, avatar_x + avatar_size - 4, avatar_y + avatar_size - 4),
        fill=(34, 197, 94, 255),
        outline=(16, 18, 27, 255),
        width=3
    )

    # 4. Phông chữ
    font_names = ["arialbd.ttf", "arial.ttf", "seguiui.ttf", "DejaVuSans-Bold.ttf", "DejaVuSans.ttf"]
    font_name = None
    for name in font_names:
        try:
            ImageFont.truetype(name, 10)
            font_name = name
            break
        except Exception:
            continue

    if font_name:
        font_name_user = ImageFont.truetype(font_name, 42)
        font_rank_num = ImageFont.truetype(font_name, 44)
        font_sub = ImageFont.truetype(font_name, 24)
        font_badge = ImageFont.truetype(font_name, 20)
        font_bar = ImageFont.truetype(font_name, 20)
        font_meta = ImageFont.truetype(font_name, 20)
    else:
        font_name_user = font_rank_num = font_sub = font_badge = font_bar = font_meta = ImageFont.load_default()

    content_x = 252
    right_edge = width - 48

    # 5. Thông tin Tên & Rank
    display_name = username if len(username) <= 15 else username[:13] + "..."
    draw.text((content_x, 48), display_name, fill=(255, 255, 255), font=font_name_user)

    # Tag Rank góc trên bên phải
    rank_val = f"#{rank_num}"
    rank_label = "RANK "
    try:
        rank_val_w = draw.textlength(rank_val, font=font_rank_num)
        rank_lbl_w = draw.textlength(rank_label, font=font_badge)
    except Exception:
        rank_val_w = len(rank_val) * 26
        rank_lbl_w = len(rank_label) * 14

    draw.text((right_edge - rank_val_w, 46), rank_val, fill=(250, 204, 21), font=font_rank_num)
    draw.text((right_edge - rank_val_w - rank_lbl_w - 4, 66), rank_label, fill=(156, 163, 175), font=font_badge)

    # 6. Thông tin Level (Badged Pill), XP & Extra Info (Coins, Voice)
    # Badge Level
    lvl_tag = f"LVL {level}"
    badge_w = 100
    badge_h = 32
    draw.rounded_rectangle([(content_x, 108), (content_x + badge_w, 108 + badge_h)], radius=10, fill=(126, 34, 206, 220), outline=(168, 85, 247, 255), width=1)
    draw.text((content_x + 14, 112), lvl_tag, fill=(255, 255, 255), font=font_badge)

    # Thông tin bổ sung: Coins & Voice Time (gắn bên cạnh badge level)
    extra_x = content_x + badge_w + 16
    extra_items = []
    if coins is not None:
        extra_items.append(f"💰 {coins:,} Coins")
    if voice_time_str:
        extra_items.append(f"🎙️ {voice_time_str}")
    
    if extra_items:
        extra_text = "  •  ".join(extra_items)
        draw.text((extra_x, 113), extra_text, fill=(209, 213, 225), font=font_meta)

    # XP chi tiết của cấp hiện tại
    xp_text = f"{current_xp:,} / {next_xp:,} XP"
    try:
        xp_w = draw.textlength(xp_text, font=font_sub)
    except Exception:
        xp_w = len(xp_text) * 13
    draw.text((right_edge - xp_w, 112), xp_text, fill=(209, 213, 219), font=font_sub)

    # 7. Thanh tiến trình XP (Progress Bar) Gradient
    bar_x = content_x
    bar_y = 165
    bar_w = width - content_x - 48
    bar_h = 36

    # Nền thanh progress
    draw.rounded_rectangle([(bar_x, bar_y), (bar_x + bar_w, bar_y + bar_h)], radius=18, fill=(30, 35, 48, 255), outline=(50, 58, 80, 255), width=1)

    # Tính tỷ lệ % (dựa trên XP tích lũy trong cấp hiện tại / mốc cần đạt của cấp đó)
    percent = min(1.0, max(0.0, current_xp / max(1, next_xp)))
    fill_w = max(36, int(bar_w * percent)) if percent > 0 else 0

    if fill_w > 0:
        grad_bar = create_gradient_mask((fill_w, bar_h), (147, 51, 234, 255), (6, 182, 212, 255))
        mask_bar = Image.new("L", (fill_w, bar_h), 0)
        mask_draw = ImageDraw.Draw(mask_bar)
        mask_draw.rounded_rectangle([(0, 0), (fill_w, bar_h)], radius=18, fill=255)
        card.paste(grad_bar, (bar_x, bar_y), mask=mask_bar)

    # Chữ % XP ở chính giữa thanh tiến trình
    pct_str = f"{int(percent * 100)}%"
    try:
        pct_w = draw.textlength(pct_str, font=font_bar)
    except Exception:
        pct_w = len(pct_str) * 11
    draw.text((bar_x + (bar_w - pct_w) // 2, bar_y + 7), pct_str, fill=(255, 255, 255), font=font_bar)

    buf = io.BytesIO()
    card.save(buf, format="PNG")
    buf.seek(0)
    return buf

async def create_rank_card(
    avatar_url: str,
    username: str,
    level: int,
    current_xp: int,
    next_xp: int,
    rank_num: int,
    coins: int = 0,
    voice_time_str: str = ""
) -> io.BytesIO:
    avatar_bytes = b""
    timeout = aiohttp.ClientTimeout(total=10)
    try:
        async with aiohttp.ClientSession(timeout=timeout) as session:
            async with session.get(avatar_url) as resp:
                if resp.status == 200:
                    avatar_bytes = await resp.read()
    except (aiohttp.ClientError, TimeoutError, Exception):
        avatar_bytes = b""

    return await asyncio.to_thread(
        _generate_rank_card_sync,
        avatar_bytes,
        username,
        level,
        current_xp,
        next_xp,
        rank_num,
        coins,
        voice_time_str
    )