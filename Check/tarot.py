import discord
import random
import json
import os

from data.data import TAROT_DECK
from datetime import datetime, timedelta, timezone

VN_TZ = timezone(timedelta(hours=7))
HISTORY_FILE = "data/tarot_history.json"

def save_history(user_id: int, user_name: str, kieu_trai: str, danh_sach_la: list):
    """
    Hàm lưu lịch sử bói bài (Hỗ trợ trải bài nhiều lá)
    :param danh_sach_la: Truyền vào một list dạng ["Lá 1 (Xuôi)", "Lá 2 (Ngược)",...]
    """
    if os.path.exists(HISTORY_FILE):
        with open(HISTORY_FILE, "r", encoding="utf-8") as f:
            try:
                data = json.load(f)
            except json.JSONDecodeError:
                data = {}
    else:
        data = {}

    str_user_id = str(user_id)
    if str_user_id not in data:
        data[str_user_id] = []

    new_record = {
        "user_name": user_name,
        "kieu_trai": kieu_trai,
        "danh_sach_la": danh_sach_la,
        "thoi_gian": datetime.now(VN_TZ).strftime("%Y-%m-%d %H:%M:%S"),
        "timestamp": datetime.now(VN_TZ).isoformat()
    }
    
    data[str_user_id].insert(0, new_record)
    data[str_user_id] = data[str_user_id][:5]

    with open(HISTORY_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

def get_history(user_id: int):
    """Hàm lấy lịch sử bói bài của người dùng"""
    if os.path.exists(HISTORY_FILE):
        with open(HISTORY_FILE, "r", encoding="utf-8") as f:
            try:
                data = json.load(f)
                return data.get(str(user_id), [])
            except json.JSONDecodeError:
                return []
    return []

def draw_cards(num_cards=1):
    card_names = list(TAROT_DECK.keys())
    selected_names = random.sample(card_names, min(num_cards, len(card_names)))
    
    results = []
    for name in selected_names:
        orientation = random.choice(["upright", "reversed"])
        meaning = TAROT_DECK[name][orientation]
        orientation_vn = "Xuôi" if orientation == "upright" else "Ngược (Reversed)"
        results.append({
            "name": name,
            "orientation": orientation_vn,
            "meaning": meaning
        })
    return results

def can_draw_today(user_id: int) -> tuple[bool, str]:
    """
    Kiểm tra xem hôm nay người dùng đã rút bài chưa.
    Trả về: (True/False, Tin nhắn thông báo)
    """
    if not os.path.exists(HISTORY_FILE):
        return True, ""
        
    with open(HISTORY_FILE, "r", encoding="utf-8") as f:
        try:
            data = json.load(f)
        except json.JSONDecodeError:
            return True, ""
            
    str_user_id = str(user_id)
    if str_user_id not in data:
        return True, ""
        
    for record in data[str_user_id]:
        if record["kieu_trai"] == "Lá Bài Hôm Nay 🌅":
            last_draw_str = record.get("timestamp")
            if not last_draw_str:
                continue
                
            last_draw = datetime.fromisoformat(last_draw_str).astimezone(VN_TZ)
            now = datetime.now(VN_TZ)
            
            if last_draw.date() == now.date():
                tomorrow = datetime.combine(now.date() + timedelta(days=1), datetime.min.time(), tzinfo=VN_TZ)
                time_remaining = tomorrow - now
                hours, remainder = divmod(time_remaining.seconds, 3600)
                minutes, _ = divmod(remainder, 60)
                
                return False, f"⏰ Bạn đã rút lá bài hôm nay rồi! Vui lòng quay lại sau **{hours} giờ {minutes} phút** (khi sang ngày mới) nhé."
                
    return True, ""