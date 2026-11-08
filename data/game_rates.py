"""
🌸 SakuraBot - Game Rates & Probability Manipulation System
Cung cấp khả năng cấu hình và thao túng các tỉ lệ trong game (Cường hóa / Đập đồ, Thăng sao, May mắn câu cá, Đào khoáng...)
"""
import json
from pathlib import Path
from typing import Dict, Any

DATA_DIR = Path(__file__).resolve().parent
RATES_FILE = DATA_DIR / "game_rates.json"

DEFAULT_RATES: Dict[str, Any] = {
    # 🔨 Cường hóa / Đập đồ (+1..+150)
    "refine_multiplier": 1.0,           # Hệ số nhân tỉ lệ đập đồ (0.1 -> 10.0)
    "refine_always_success": False,      # 100% Đập đồ luôn thành công (God Mode)

    # ⭐ Tiến cấp sao (1..20 ⭐)
    "star_multiplier": 1.0,             # Hệ số nhân tỉ lệ lên sao (0.1 -> 10.0)
    "star_always_success": False,        # 100% Lên sao luôn thành công

    # 🎣 Câu cá đại dương
    "fishing_luck_mult": 1.0,           # May mắn câu cá (x1.0 -> x10.0)
    "fishing_mutation_mult": 1.0,       # Tỉ lệ cá đột biến / biến dị (x1.0 -> x10.0)
    "fishing_chest_mult": 1.0,          # Tỉ lệ câu dính rương báu (x1.0 -> x10.0)

    # ⛏️ Khai thác mỏ khoáng
    "mining_luck_mult": 1.0,            # May mắn đào khoáng (x1.0 -> x10.0)
    "mining_rare_mult": 1.0,            # Tỉ lệ rơi quặng quý / sử thi / huyền thoại (x1.0 -> x10.0)
    "mining_mutation_mult": 1.0         # Tỉ lệ quặng đột biến địa chất (x1.0 -> x10.0)
}

# Alias map để tương thích frontend & backend
ALIASES = {
    "god_mode_refine": "refine_always_success",
    "refine_mult": "refine_multiplier",
    "god_mode_star": "star_always_success",
    "star_mult": "star_multiplier"
}

_cached_rates: Dict[str, Any] = {}

def get_game_rates() -> Dict[str, Any]:
    """Lấy cấu hình tỉ lệ game hiện tại kèm aliases."""
    global _cached_rates
    if not RATES_FILE.exists():
        _cached_rates = dict(DEFAULT_RATES)
        save_game_rates(_cached_rates)

    if not _cached_rates:
        try:
            with open(RATES_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
            merged = dict(DEFAULT_RATES)
            merged.update(data)
            _cached_rates = merged
        except Exception:
            _cached_rates = dict(DEFAULT_RATES)

    res = dict(_cached_rates)
    # Thêm aliases tiện lợi cho UI
    res["god_mode_refine"] = res.get("refine_always_success", False)
    res["refine_mult"] = res.get("refine_multiplier", 1.0)
    res["god_mode_star"] = res.get("star_always_success", False)
    res["star_mult"] = res.get("star_multiplier", 1.0)
    return res

def save_game_rates(new_rates: Dict[str, Any]) -> Dict[str, Any]:
    """Lưu và cập nhật cấu hình tỉ lệ game."""
    global _cached_rates
    current = dict(DEFAULT_RATES)
    if _cached_rates:
        current.update({k: v for k, v in _cached_rates.items() if k in DEFAULT_RATES})

    normalized = dict(new_rates)
    for alias_k, canonical_k in ALIASES.items():
        if alias_k in normalized and canonical_k not in normalized:
            normalized[canonical_k] = normalized[alias_k]

    for k, v in normalized.items():
        if k in DEFAULT_RATES:
            if isinstance(DEFAULT_RATES[k], bool):
                current[k] = bool(v)
            elif isinstance(DEFAULT_RATES[k], (int, float)):
                current[k] = max(0.0, min(100.0, float(v)))

    _cached_rates = current
    try:
        with open(RATES_FILE, "w", encoding="utf-8") as f:
            json.dump(_cached_rates, f, indent=4, ensure_ascii=False)
    except Exception as e:
        print(f"[GameRates] Error saving rates: {e}")
    return get_game_rates()

def calculate_refine_rate(base_rate: float) -> float:
    """Tính toán tỉ lệ đập đồ sau khi áp dụng thao túng tỉ lệ (hỗ trợ cả thang 0..1 và 0..100)."""
    rates = get_game_rates()
    is_percentage = base_rate > 1.0
    if rates.get("refine_always_success", False):
        return 100.0 if is_percentage else 1.0
    mult = rates.get("refine_multiplier", 1.0)
    if is_percentage:
        return min(100.0, max(0.1, base_rate * mult))
    return min(1.0, max(0.001, base_rate * mult))

def calculate_star_rate(base_rate: float) -> float:
    """Tính toán tỉ lệ thăng cấp sao sau khi áp dụng thao túng tỉ lệ (hỗ trợ cả thang 0..1 và 0..100)."""
    rates = get_game_rates()
    is_percentage = base_rate > 1.0
    if rates.get("star_always_success", False):
        return 100.0 if is_percentage else 1.0
    mult = rates.get("star_multiplier", 1.0)
    if is_percentage:
        return min(100.0, max(0.1, base_rate * mult))
    return min(1.0, max(0.001, base_rate * mult))
