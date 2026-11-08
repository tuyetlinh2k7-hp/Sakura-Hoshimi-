import aiosqlite
import json
import os
import random
import time
import uuid
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Optional, List, Dict, Tuple, Any

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
DB_PATH = DATA_DIR / "waifu_gacha.db"
CHARACTERS_JSON = DATA_DIR / "waifu_characters.json"

# Rarity configurations & burn values
RARITY_CONFIG = {
    "common": {
        "name_vi": "Thường",
        "name_en": "Common",
        "name_ja": "コモン",
        "name_cn": "普通",
        "burn_coins": 15,
        "indicator": "🔷 ◽ ◽ ◽",
        "color": 0x95a5a6,  # Slate Grey
        "max_favs": 2000,
        "drop_weight": 50,
    },
    "rare": {
        "name_vi": "Hiếm",
        "name_en": "Rare",
        "name_ja": "レア",
        "name_cn": "稀有",
        "burn_coins": 50,
        "indicator": "🔷 🔷 ◽ ◽",
        "color": 0x3498db,  # Blue
        "max_favs": 8000,
        "drop_weight": 30,
    },
    "epic": {
        "name_vi": "Sử thi",
        "name_en": "Epic",
        "name_ja": "エピック",
        "name_cn": "史诗",
        "burn_coins": 150,
        "indicator": "🔷 🔷 🔷 ◽",
        "color": 0x9b59b6,  # Purple
        "max_favs": 20000,
        "drop_weight": 15,
    },
    "legendary": {
        "name_vi": "Huyền thoại",
        "name_en": "Legendary",
        "name_ja": "レジェンド",
        "name_cn": "传说",
        "burn_coins": 500,
        "indicator": "🔷 🔷 🔷 🔷",
        "color": 0xf1c40f,  # Gold
        "max_favs": 50000,
        "drop_weight": 5,
    },
}

ROLL_REGEN_SECONDS = 300   # 1 roll per 5 minutes
DEFAULT_MAX_ROLLS = 15
CLAIM_REGEN_SECONDS = 7200 # 1 claim per 2 hours
DEFAULT_MAX_CLAIMS = 1


@asynccontextmanager
async def get_connection():
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    async with aiosqlite.connect(DB_PATH) as conn:
        conn.row_factory = aiosqlite.Row
        yield conn


async def init_waifu_db():
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    async with get_connection() as db:
        await db.execute("""
            CREATE TABLE IF NOT EXISTS characters (
                id INTEGER PRIMARY KEY,
                name TEXT NOT NULL,
                native_name TEXT,
                media_title TEXT,
                image_url TEXT,
                favourites INTEGER DEFAULT 0,
                rarity TEXT NOT NULL,
                site_url TEXT,
                rank INTEGER DEFAULT 0
            )
        """)

        await db.execute("""
            CREATE TABLE IF NOT EXISTS character_stats (
                character_id INTEGER PRIMARY KEY,
                total_claims INTEGER DEFAULT 0
            )
        """)

        await db.execute("""
            CREATE TABLE IF NOT EXISTS user_profiles (
                user_id INTEGER PRIMARY KEY,
                rolls INTEGER DEFAULT 15,
                max_rolls INTEGER DEFAULT 15,
                last_roll_regen REAL DEFAULT 0,
                claims INTEGER DEFAULT 1,
                max_claims INTEGER DEFAULT 1,
                last_claim_regen REAL DEFAULT 0,
                total_rolls INTEGER DEFAULT 0,
                total_claims INTEGER DEFAULT 0,
                total_merges INTEGER DEFAULT 0,
                favorite_card_code TEXT DEFAULT NULL
            )
        """)

        await db.execute("""
            CREATE TABLE IF NOT EXISTS user_cards (
                code TEXT PRIMARY KEY,
                user_id INTEGER NOT NULL,
                character_id INTEGER NOT NULL,
                stars INTEGER DEFAULT 1,
                base_favourites INTEGER NOT NULL,
                points INTEGER NOT NULL,
                print_number INTEGER DEFAULT 1,
                obtained_at REAL NOT NULL,
                is_favorite INTEGER DEFAULT 0,
                FOREIGN KEY (character_id) REFERENCES characters (id)
            )
        """)
        await db.execute("CREATE INDEX IF NOT EXISTS idx_user_cards_user ON user_cards (user_id)")
        await db.execute("CREATE INDEX IF NOT EXISTS idx_user_cards_char ON user_cards (character_id)")

        await db.execute("""
            CREATE TABLE IF NOT EXISTS market_listings (
                listing_id INTEGER PRIMARY KEY AUTOINCREMENT,
                card_code TEXT UNIQUE NOT NULL,
                seller_id INTEGER NOT NULL,
                price_coins INTEGER NOT NULL,
                created_at REAL NOT NULL,
                FOREIGN KEY (card_code) REFERENCES user_cards (code)
            )
        """)

        await db.execute("""
            CREATE TABLE IF NOT EXISTS wishlists (
                user_id INTEGER NOT NULL,
                character_id INTEGER NOT NULL,
                created_at REAL NOT NULL,
                PRIMARY KEY (user_id, character_id)
            )
        """)

        await db.commit()

    # Load characters if table is empty or update
    await sync_characters_from_json()


async def sync_characters_from_json():
    if not CHARACTERS_JSON.exists():
        return
    try:
        with open(CHARACTERS_JSON, "r", encoding="utf-8") as f:
            chars = json.load(f)
        if not chars:
            return

        async with get_connection() as db:
            for c in chars:
                cid = c.get("id")
                name = c.get("name", "Unknown")
                native_name = c.get("native_name", name)
                media_title = c.get("media_title", "Unknown")
                image_url = c.get("image_url", "")
                favourites = int(c.get("favourites", 0))
                rarity = c.get("rarity", "common")
                site_url = c.get("site_url", f"https://anilist.co/character/{cid}")
                rank = int(c.get("rank", 0))

                await db.execute("""
                    INSERT INTO characters (id, name, native_name, media_title, image_url, favourites, rarity, site_url, rank)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ON CONFLICT(id) DO UPDATE SET
                        name=excluded.name,
                        native_name=excluded.native_name,
                        media_title=excluded.media_title,
                        image_url=excluded.image_url,
                        favourites=excluded.favourites,
                        rarity=excluded.rarity,
                        site_url=excluded.site_url,
                        rank=excluded.rank
                """, (cid, name, native_name, media_title, image_url, favourites, rarity, site_url, rank))
            await db.commit()
    except Exception as e:
        print(f"Error syncing characters: {e}")


# ===================== USER PROFILE & TIMERS =====================

async def get_or_create_profile(user_id: int) -> dict:
    now = time.time()
    async with get_connection() as db:
        async with db.execute("SELECT * FROM user_profiles WHERE user_id = ?", (user_id,)) as cur:
            row = await cur.fetchone()

        if not row:
            # Create fresh profile
            await db.execute("""
                INSERT INTO user_profiles (user_id, rolls, max_rolls, last_roll_regen, claims, max_claims, last_claim_regen)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (user_id, DEFAULT_MAX_ROLLS, DEFAULT_MAX_ROLLS, now, DEFAULT_MAX_CLAIMS, DEFAULT_MAX_CLAIMS, now))
            await db.commit()
            return {
                "user_id": user_id,
                "rolls": DEFAULT_MAX_ROLLS,
                "max_rolls": DEFAULT_MAX_ROLLS,
                "last_roll_regen": now,
                "claims": DEFAULT_MAX_CLAIMS,
                "max_claims": DEFAULT_MAX_CLAIMS,
                "last_claim_regen": now,
                "total_rolls": 0,
                "total_claims": 0,
                "total_merges": 0,
                "favorite_card_code": None,
                "next_roll_in": 0,
                "next_claim_in": 0
            }

        profile = dict(row)
        rolls = profile["rolls"]
        max_rolls = profile["max_rolls"]
        last_roll_regen = profile["last_roll_regen"]

        claims = profile["claims"]
        max_claims = profile["max_claims"]
        last_claim_regen = profile["last_claim_regen"]

        updated = False

        # Regen rolls if below max_rolls
        if rolls < max_rolls:
            elapsed_roll = now - last_roll_regen
            added_rolls = int(elapsed_roll // ROLL_REGEN_SECONDS)
            if added_rolls > 0:
                rolls = min(max_rolls, rolls + added_rolls)
                last_roll_regen = last_roll_regen + (added_rolls * ROLL_REGEN_SECONDS)
                updated = True
        else:
            last_roll_regen = now

        # Regen claims if below max_claims
        if claims < max_claims:
            elapsed_claim = now - last_claim_regen
            added_claims = int(elapsed_claim // CLAIM_REGEN_SECONDS)
            if added_claims > 0:
                claims = min(max_claims, claims + added_claims)
                last_claim_regen = last_claim_regen + (added_claims * CLAIM_REGEN_SECONDS)
                updated = True
        else:
            last_claim_regen = now

        if updated:
            await db.execute("""
                UPDATE user_profiles
                SET rolls = ?, last_roll_regen = ?, claims = ?, last_claim_regen = ?
                WHERE user_id = ?
            """, (rolls, last_roll_regen, claims, last_claim_regen, user_id))
            await db.commit()

        profile["rolls"] = rolls
        profile["last_roll_regen"] = last_roll_regen
        profile["claims"] = claims
        profile["last_claim_regen"] = last_claim_regen

        # Compute remaining seconds until next regen
        if rolls < max_rolls:
            profile["next_roll_in"] = max(0, int(ROLL_REGEN_SECONDS - (now - last_roll_regen)))
        else:
            profile["next_roll_in"] = 0

        if claims < max_claims:
            profile["next_claim_in"] = max(0, int(CLAIM_REGEN_SECONDS - (now - last_claim_regen)))
        else:
            profile["next_claim_in"] = 0

        return profile


async def consume_roll(user_id: int) -> Tuple[bool, dict]:
    profile = await get_or_create_profile(user_id)
    if profile["rolls"] <= 0:
        return False, profile

    now = time.time()
    new_rolls = profile["rolls"] - 1
    total_rolls = profile["total_rolls"] + 1

    last_regen = profile["last_roll_regen"]
    if profile["rolls"] >= profile["max_rolls"]:
        last_regen = now

    async with get_connection() as db:
        await db.execute("""
            UPDATE user_profiles
            SET rolls = ?, total_rolls = ?, last_roll_regen = ?
            WHERE user_id = ?
        """, (new_rolls, total_rolls, last_regen, user_id))
        await db.commit()

    profile["rolls"] = new_rolls
    profile["total_rolls"] = total_rolls
    profile["last_roll_regen"] = last_regen
    return True, profile


async def consume_claim(user_id: int) -> Tuple[bool, dict]:
    profile = await get_or_create_profile(user_id)
    if profile["claims"] <= 0:
        return False, profile

    now = time.time()
    new_claims = profile["claims"] - 1
    total_claims = profile["total_claims"] + 1

    last_regen = profile["last_claim_regen"]
    if profile["claims"] >= profile["max_claims"]:
        last_regen = now

    async with get_connection() as db:
        await db.execute("""
            UPDATE user_profiles
            SET claims = ?, total_claims = ?, last_claim_regen = ?
            WHERE user_id = ?
        """, (new_claims, total_claims, last_regen, user_id))
        await db.commit()

    profile["claims"] = new_claims
    profile["total_claims"] = total_claims
    profile["last_claim_regen"] = last_regen
    return True, profile


async def add_bonus_rolls(user_id: int, count: int) -> int:
    profile = await get_or_create_profile(user_id)
    new_rolls = profile["rolls"] + count
    async with get_connection() as db:
        await db.execute("UPDATE user_profiles SET rolls = ? WHERE user_id = ?", (new_rolls, user_id))
        await db.commit()
    return new_rolls


async def add_bonus_claims(user_id: int, count: int) -> int:
    profile = await get_or_create_profile(user_id)
    new_claims = profile["claims"] + count
    async with get_connection() as db:
        await db.execute("UPDATE user_profiles SET claims = ? WHERE user_id = ?", (new_claims, user_id))
        await db.commit()
    return new_claims


# ===================== CHARACTER SELECTION =====================

async def get_random_character() -> Optional[dict]:
    # Weighted choice by rarity
    rarities = list(RARITY_CONFIG.keys())
    weights = [RARITY_CONFIG[r]["drop_weight"] for r in rarities]
    chosen_rarity = random.choices(rarities, weights=weights, k=1)[0]

    async with get_connection() as db:
        async with db.execute("""
            SELECT * FROM characters WHERE rarity = ? ORDER BY RANDOM() LIMIT 1
        """, (chosen_rarity,)) as cur:
            row = await cur.fetchone()

        if not row:
            # Fallback to any character if that rarity has no rows
            async with db.execute("SELECT * FROM characters ORDER BY RANDOM() LIMIT 1") as cur2:
                row = await cur2.fetchone()

        return dict(row) if row else None


async def get_character_by_id(character_id: int) -> Optional[dict]:
    async with get_connection() as db:
        async with db.execute("SELECT * FROM characters WHERE id = ?", (character_id,)) as cur:
            row = await cur.fetchone()
            return dict(row) if row else None


async def search_characters(query: str, limit: int = 15) -> List[dict]:
    async with get_connection() as db:
        q = f"%{query.strip()}%"
        async with db.execute("""
            SELECT * FROM characters
            WHERE name LIKE ? OR native_name LIKE ? OR media_title LIKE ?
            ORDER BY favourites DESC
            LIMIT ?
        """, (q, q, q, limit)) as cur:
            rows = await cur.fetchall()
            return [dict(r) for r in rows]


# ===================== CARD MANAGEMENT =====================

def calculate_card_points(base_favourites: int, stars: int) -> int:
    """
    Điểm yêu thích x2 theo số sao:
    1⭐: base * 1
    2⭐: base * 2
    3⭐: base * 4
    4⭐: base * 8
    5⭐: base * 16
    """
    multiplier = 2 ** max(0, stars - 1)
    return int(base_favourites * multiplier)


async def mint_card(user_id: int, character_id: int) -> dict:
    char = await get_character_by_id(character_id)
    if not char:
        raise ValueError(f"Character {character_id} not found!")

    now = time.time()
    code = uuid.uuid4().hex[:6].lower()

    async with get_connection() as db:
        # Check uniqueness of code
        while True:
            async with db.execute("SELECT 1 FROM user_cards WHERE code = ?", (code,)) as c:
                if not await c.fetchone():
                    break
            code = uuid.uuid4().hex[:6].lower()

        # Update character_stats total_claims to get print_number
        await db.execute("""
            INSERT INTO character_stats (character_id, total_claims)
            VALUES (?, 1)
            ON CONFLICT(character_id) DO UPDATE SET total_claims = total_claims + 1
        """, (character_id,))

        async with db.execute("SELECT total_claims FROM character_stats WHERE character_id = ?", (character_id,)) as c:
            row = await c.fetchone()
            print_number = row["total_claims"] if row else 1

        stars = 1
        base_favs = char["favourites"]
        points = calculate_card_points(base_favs, stars)

        await db.execute("""
            INSERT INTO user_cards (code, user_id, character_id, stars, base_favourites, points, print_number, obtained_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (code, user_id, character_id, stars, base_favs, points, print_number, now))
        await db.commit()

    card_info = {
        "code": code,
        "user_id": user_id,
        "character_id": character_id,
        "stars": stars,
        "base_favourites": base_favs,
        "points": points,
        "print_number": print_number,
        "obtained_at": now,
        "is_favorite": 0,
        "name": char["name"],
        "native_name": char["native_name"],
        "media_title": char["media_title"],
        "image_url": char["image_url"],
        "rarity": char["rarity"],
        "site_url": char["site_url"],
        "rank": char["rank"],
    }
    return card_info


async def get_user_cards(user_id: int) -> List[dict]:
    async with get_connection() as db:
        async with db.execute("""
            SELECT c.*, ch.name, ch.native_name, ch.media_title, ch.image_url, ch.rarity, ch.site_url, ch.rank
            FROM user_cards c
            JOIN characters ch ON c.character_id = ch.id
            WHERE c.user_id = ?
            ORDER BY c.points DESC, c.stars DESC, c.obtained_at ASC
        """, (user_id,)) as cur:
            rows = await cur.fetchall()
            return [dict(r) for r in rows]


async def get_user_card(code: str) -> Optional[dict]:
    async with get_connection() as db:
        async with db.execute("""
            SELECT c.*, ch.name, ch.native_name, ch.media_title, ch.image_url, ch.rarity, ch.site_url, ch.rank
            FROM user_cards c
            JOIN characters ch ON c.character_id = ch.id
            WHERE c.code = ?
        """, (code.lower(),)) as cur:
            row = await cur.fetchone()
            return dict(row) if row else None


async def burn_card(code: str, user_id: int) -> Tuple[bool, int, Optional[dict]]:
    card = await get_user_card(code)
    if not card or card["user_id"] != user_id:
        return False, 0, None

    # Check if card is currently listed on market
    async with get_connection() as db:
        async with db.execute("SELECT 1 FROM market_listings WHERE card_code = ?", (code,)) as cur:
            if await cur.fetchone():
                return False, 0, None

        rarity = card["rarity"]
        burn_coins = RARITY_CONFIG.get(rarity, {}).get("burn_coins", 15)

        # Delete card
        await db.execute("DELETE FROM user_cards WHERE code = ?", (code,))
        await db.commit()

    return True, burn_coins, card


async def get_mergeable_characters(user_id: int) -> List[dict]:
    """
    Returns characters where the user owns at least 3 cards and star < 5.
    """
    async with get_connection() as db:
        async with db.execute("""
            SELECT ch.id as character_id, ch.name, ch.native_name, ch.image_url, ch.rarity,
                   COUNT(c.code) as card_count,
                   MAX(c.stars) as max_stars
            FROM user_cards c
            JOIN characters ch ON c.character_id = ch.id
            WHERE c.user_id = ?
            GROUP BY ch.id
            HAVING COUNT(c.code) >= 3 AND MAX(c.stars) < 5
            ORDER BY card_count DESC, ch.favourites DESC
        """, (user_id,)) as cur:
            rows = await cur.fetchall()
            return [dict(r) for r in rows]


async def merge_star(user_id: int, character_id: int) -> Tuple[bool, str, Optional[dict]]:
    """
    Mục nâng sao: cứ 3 thẻ cùng loại thì lên 1 sao (+1) với điểm yêu thích x2.
    Upgrades 1 card by +1 star (max 5⭐), consumes (deletes) 2 other cards.
    """
    async with get_connection() as db:
        # Find eligible cards not on marketplace
        async with db.execute("""
            SELECT c.code, c.stars, c.base_favourites
            FROM user_cards c
            LEFT JOIN market_listings m ON c.code = m.card_code
            WHERE c.user_id = ? AND c.character_id = ? AND m.card_code IS NULL
            ORDER BY c.stars DESC, c.obtained_at ASC
        """, (user_id, character_id)) as cur:
            rows = await cur.fetchall()

        if len(rows) < 3:
            return False, "NEED_3_CARDS", None

        # Select target card (highest star one that is < 5)
        target = None
        others = []
        for r in rows:
            if target is None and r["stars"] < 5:
                target = r
            else:
                others.append(r)

        if not target or len(others) < 2:
            return False, "MAX_STARS_REACHED", None

        # Take 2 cards to consume
        consume_codes = [others[0]["code"], others[1]["code"]]
        new_stars = target["stars"] + 1
        new_points = calculate_card_points(target["base_favourites"], new_stars)
        target_code = target["code"]

        # Delete the 2 consumed cards
        await db.execute("DELETE FROM user_cards WHERE code IN (?, ?)", (consume_codes[0], consume_codes[1]))

        # Upgrade target card
        await db.execute("""
            UPDATE user_cards
            SET stars = ?, points = ?
            WHERE code = ?
        """, (new_stars, new_points, target_code))

        # Update profile merge counter
        await db.execute("UPDATE user_profiles SET total_merges = total_merges + 1 WHERE user_id = ?", (user_id,))
        await db.commit()

    upgraded_card = await get_user_card(target_code)
    return True, "SUCCESS", upgraded_card


# ===================== MARKETPLACE =====================

async def list_card_for_sale(card_code: str, seller_id: int, price_coins: int) -> Tuple[bool, str]:
    card = await get_user_card(card_code)
    if not card or card["user_id"] != seller_id:
        return False, "NOT_OWNER"
    if price_coins <= 0:
        return False, "INVALID_PRICE"

    now = time.time()
    async with get_connection() as db:
        # Check if already listed
        async with db.execute("SELECT 1 FROM market_listings WHERE card_code = ?", (card_code,)) as cur:
            if await cur.fetchone():
                return False, "ALREADY_LISTED"

        await db.execute("""
            INSERT INTO market_listings (card_code, seller_id, price_coins, created_at)
            VALUES (?, ?, ?, ?)
        """, (card_code, seller_id, price_coins, now))
        await db.commit()

    return True, "SUCCESS"


async def cancel_market_listing(listing_id: int, seller_id: int) -> Tuple[bool, str]:
    async with get_connection() as db:
        async with db.execute("SELECT * FROM market_listings WHERE listing_id = ?", (listing_id,)) as cur:
            listing = await cur.fetchone()

        if not listing:
            return False, "NOT_FOUND"
        if listing["seller_id"] != seller_id:
            return False, "NOT_OWNER"

        await db.execute("DELETE FROM market_listings WHERE listing_id = ?", (listing_id,))
        await db.commit()

    return True, "SUCCESS"


async def get_market_listings(limit: int = 10, offset: int = 0) -> Tuple[List[dict], int]:
    async with get_connection() as db:
        async with db.execute("SELECT COUNT(*) as total FROM market_listings") as cur:
            row = await cur.fetchone()
            total = row["total"] if row else 0

        async with db.execute("""
            SELECT m.listing_id, m.card_code, m.seller_id, m.price_coins, m.created_at,
                   c.stars, c.points, c.print_number,
                   ch.id as character_id, ch.name, ch.native_name, ch.rarity, ch.image_url
            FROM market_listings m
            JOIN user_cards c ON m.card_code = c.code
            JOIN characters ch ON c.character_id = ch.id
            ORDER BY m.created_at DESC
            LIMIT ? OFFSET ?
        """, (limit, offset)) as cur:
            rows = await cur.fetchall()
            return [dict(r) for r in rows], total


async def buy_market_listing(listing_id: int, buyer_id: int) -> Tuple[bool, str, Optional[dict]]:
    async with get_connection() as db:
        async with db.execute("SELECT * FROM market_listings WHERE listing_id = ?", (listing_id,)) as cur:
            listing = await cur.fetchone()

        if not listing:
            return False, "NOT_FOUND", None
        if listing["seller_id"] == buyer_id:
            return False, "CANNOT_BUY_OWN", None

        card_code = listing["card_code"]
        seller_id = listing["seller_id"]
        price = listing["price_coins"]

        # Transfer card ownership
        await db.execute("UPDATE user_cards SET user_id = ? WHERE code = ?", (buyer_id, card_code))
        # Remove listing
        await db.execute("DELETE FROM market_listings WHERE listing_id = ?", (listing_id,))
        await db.commit()

    card = await get_user_card(card_code)
    return True, "SUCCESS", {
        "seller_id": seller_id,
        "price": price,
        "card": card
    }


# ===================== WISHLIST =====================

async def add_wishlist(user_id: int, character_id: int) -> Tuple[bool, str]:
    now = time.time()
    async with get_connection() as db:
        async with db.execute("SELECT COUNT(*) as count FROM wishlists WHERE user_id = ?", (user_id,)) as cur:
            row = await cur.fetchone()
            if row and row["count"] >= 10:
                return False, "WISHLIST_MAX_REACHED"

        try:
            await db.execute("""
                INSERT INTO wishlists (user_id, character_id, created_at)
                VALUES (?, ?, ?)
            """, (user_id, character_id, now))
            await db.commit()
            return True, "SUCCESS"
        except aiosqlite.IntegrityError:
            return False, "ALREADY_WISHLISTED"


async def remove_wishlist(user_id: int, character_id: int) -> Tuple[bool, str]:
    async with get_connection() as db:
        async with db.execute("SELECT 1 FROM wishlists WHERE user_id = ? AND character_id = ?", (user_id, character_id)) as cur:
            if not await cur.fetchone():
                return False, "NOT_IN_WISHLIST"

        await db.execute("DELETE FROM wishlists WHERE user_id = ? AND character_id = ?", (user_id, character_id))
        await db.commit()
    return True, "SUCCESS"


async def get_user_wishlist(user_id: int) -> List[dict]:
    async with get_connection() as db:
        async with db.execute("""
            SELECT w.character_id, w.created_at, ch.name, ch.native_name, ch.media_title, ch.image_url, ch.rarity, ch.favourites
            FROM wishlists w
            JOIN characters ch ON w.character_id = ch.id
            WHERE w.user_id = ?
            ORDER BY ch.favourites DESC
        """, (user_id,)) as cur:
            rows = await cur.fetchall()
            return [dict(r) for r in rows]


async def get_wishlist_users(character_id: int) -> List[int]:
    async with get_connection() as db:
        async with db.execute("SELECT user_id FROM wishlists WHERE character_id = ?", (character_id,)) as cur:
            rows = await cur.fetchall()
            return [r["user_id"] for r in rows]


# ===================== LEADERBOARD =====================

async def get_top_collectors(limit: int = 10) -> List[dict]:
    async with get_connection() as db:
        async with db.execute("""
            SELECT c.user_id,
                   COUNT(c.code) as total_cards,
                   SUM(c.points) as total_points,
                   MAX(c.points) as highest_card_points,
                   p.total_merges
            FROM user_cards c
            LEFT JOIN user_profiles p ON c.user_id = p.user_id
            GROUP BY c.user_id
            ORDER BY total_points DESC
            LIMIT ?
        """, (limit,)) as cur:
            rows = await cur.fetchall()
            return [dict(r) for r in rows]


# ===================== ADMIN & EXTENDED STATS =====================

async def get_gacha_global_stats() -> dict:
    async with get_connection() as db:
        async with db.execute("SELECT COUNT(*) as c FROM characters") as cur:
            row = await cur.fetchone()
            total_characters = row["c"] if row else 0

        async with db.execute("SELECT COUNT(*) as c FROM user_cards") as cur:
            row = await cur.fetchone()
            total_cards = row["c"] if row else 0

        async with db.execute("SELECT COUNT(DISTINCT user_id) as c FROM user_profiles") as cur:
            row = await cur.fetchone()
            total_users = row["c"] if row else 0

        async with db.execute("""
            SELECT SUM(total_rolls) as r, SUM(total_claims) as c, SUM(total_merges) as m
            FROM user_profiles
        """) as cur:
            row = await cur.fetchone()
            total_rolls = (row["r"] or 0) if row else 0
            total_claims = (row["c"] or 0) if row else 0
            total_merges = (row["m"] or 0) if row else 0

        async with db.execute("SELECT COUNT(*) as c FROM market_listings") as cur:
            row = await cur.fetchone()
            market_listings = row["c"] if row else 0

    return {
        "total_characters": total_characters,
        "total_cards": total_cards,
        "total_users": total_users,
        "total_rolls": total_rolls,
        "total_claims": total_claims,
        "total_merges": total_merges,
        "market_listings": market_listings
    }


async def admin_set_user_rolls(user_id: int, rolls: int) -> int:
    profile = await get_or_create_profile(user_id)
    new_rolls = max(0, int(rolls))
    async with get_connection() as db:
        await db.execute("UPDATE user_profiles SET rolls = ? WHERE user_id = ?", (new_rolls, user_id))
        await db.commit()
    return new_rolls


async def admin_set_user_claims(user_id: int, claims: int) -> int:
    profile = await get_or_create_profile(user_id)
    new_claims = max(0, int(claims))
    async with get_connection() as db:
        await db.execute("UPDATE user_profiles SET claims = ? WHERE user_id = ?", (new_claims, user_id))
        await db.commit()
    return new_claims


async def admin_grant_card(user_id: int, character_id: int, stars: int = 1, print_number: Optional[int] = None) -> dict:
    char = await get_character_by_id(character_id)
    if not char:
        raise ValueError(f"Character {character_id} not found")

    await get_or_create_profile(user_id)
    stars = max(1, min(5, int(stars)))
    base_favs = char["favourites"]
    points = calculate_card_points(base_favs, stars)
    now = time.time()
    code = uuid.uuid4().hex[:6].lower()

    async with get_connection() as db:
        # Check uniqueness of code
        while True:
            async with db.execute("SELECT 1 FROM user_cards WHERE code = ?", (code,)) as c:
                if not await c.fetchone():
                    break
            code = uuid.uuid4().hex[:6].lower()

        if print_number is None or print_number <= 0:
            await db.execute("""
                INSERT INTO character_stats (character_id, total_claims)
                VALUES (?, 1)
                ON CONFLICT(character_id) DO UPDATE SET total_claims = total_claims + 1
            """, (character_id,))
            async with db.execute("SELECT total_claims FROM character_stats WHERE character_id = ?", (character_id,)) as c:
                row = await c.fetchone()
                print_number = row["total_claims"] if row else 1

        await db.execute("""
            INSERT INTO user_cards (code, user_id, character_id, stars, base_favourites, points, print_number, obtained_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (code, user_id, character_id, stars, base_favs, points, print_number, now))
        await db.commit()

    return await get_user_card(code)


async def admin_delete_card(code: str) -> bool:
    code = code.strip().lower()
    async with get_connection() as db:
        await db.execute("DELETE FROM market_listings WHERE card_code = ?", (code,))
        cur = await db.execute("DELETE FROM user_cards WHERE code = ?", (code,))
        await db.commit()
        return cur.rowcount > 0


async def admin_update_card_stars(code: str, stars: int) -> Optional[dict]:
    code = code.strip().lower()
    stars = max(1, min(5, int(stars)))
    card = await get_user_card(code)
    if not card:
        return None

    new_points = calculate_card_points(card["base_favourites"], stars)
    async with get_connection() as db:
        await db.execute("UPDATE user_cards SET stars = ?, points = ? WHERE code = ?", (stars, new_points, code))
        await db.commit()

    return await get_user_card(code)


async def get_waifu_leaderboard_extended(limit: int = 100) -> List[dict]:
    async with get_connection() as db:
        async with db.execute("""
            SELECT c.user_id,
                   COUNT(c.code) as total_cards,
                   SUM(c.points) as total_points,
                   MAX(c.points) as highest_points,
                   COALESCE(p.total_merges, 0) as total_merges,
                   COALESCE(p.total_rolls, 0) as total_rolls,
                   COALESCE(p.total_claims, 0) as total_claims
            FROM user_cards c
            LEFT JOIN user_profiles p ON c.user_id = p.user_id
            GROUP BY c.user_id
            ORDER BY total_points DESC
            LIMIT ?
        """, (limit,)) as cur:
            rows = await cur.fetchall()

        result = []
        for r in rows:
            entry = dict(r)
            # Find the user's top card
            async with db.execute("""
                SELECT c.code, c.stars, c.points, ch.name, ch.image_url, ch.rarity
                FROM user_cards c
                JOIN characters ch ON c.character_id = ch.id
                WHERE c.user_id = ?
                ORDER BY c.points DESC, c.stars DESC
                LIMIT 1
            """, (entry["user_id"],)) as cur_card:
                top_card = await cur_card.fetchone()
                if top_card:
                    entry["top_card"] = dict(top_card)
                else:
                    entry["top_card"] = None
            result.append(entry)

        return result
