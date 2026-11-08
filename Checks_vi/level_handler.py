import json
import random
import sqlite3
import time
import aiosqlite
import discord
from data.database import DB_PATH, get_user_data, update_user_coins

XP_COOLDOWN = 60
leveling_settings = {}
user_levels = {}
last_message_time = {}


def _ensure_settings_table(conn: sqlite3.Connection):
    conn.execute("""
        CREATE TABLE IF NOT EXISTS level_settings (
            guild_id TEXT PRIMARY KEY,
            enabled INTEGER DEFAULT 1,
            level_up_announce INTEGER DEFAULT 1,
            announce_channel INTEGER DEFAULT NULL,
            ignored_channels TEXT DEFAULT '[]',
            last_weekly_summary TEXT DEFAULT NULL,
            last_monthly_summary TEXT DEFAULT NULL
        )
    """)
    columns = {row[1] for row in conn.execute("PRAGMA table_info(level_settings)").fetchall()}
    if "last_monthly_summary" not in columns:
        conn.execute("ALTER TABLE level_settings ADD COLUMN last_monthly_summary TEXT DEFAULT NULL")
    conn.commit()


def load_leveling_data():
    """Nạp cấu hình level từ SQLite vào bộ nhớ đệm (giữ nguyên vùng nhớ dict)."""
    try:
        with sqlite3.connect(DB_PATH) as conn:
            conn.row_factory = sqlite3.Row
            _ensure_settings_table(conn)
            cursor = conn.execute("SELECT * FROM level_settings")
            rows = cursor.fetchall()

            loaded = {}
            for row in rows:
                try:
                    ignored = json.loads(row["ignored_channels"] or "[]")
                except Exception:
                    ignored = []
                loaded[str(row["guild_id"])] = {
                    "enabled": bool(row["enabled"]),
                    "level_up_announce": bool(row["level_up_announce"]),
                    "announce_channel": int(row["announce_channel"]) if row["announce_channel"] else None,
                    "ignored_channels": ignored,
                    "last_weekly_summary": row["last_weekly_summary"],
                    "last_monthly_summary": row["last_monthly_summary"] if "last_monthly_summary" in row.keys() else None,
                }

            leveling_settings.clear()
            leveling_settings.update(loaded)
    except Exception as e:
        print(f"[Leveling] Lỗi khi tải cấu hình từ SQLite: {e}")


def save_leveling_settings():
    """Lưu cấu hình level từ bộ nhớ vào bảng SQLite."""
    try:
        with sqlite3.connect(DB_PATH) as conn:
            _ensure_settings_table(conn)
            for gid_str, cfg in leveling_settings.items():
                enabled = 1 if cfg.get("enabled", True) else 0
                announce = 1 if cfg.get("level_up_announce", True) else 0
                ch_id = cfg.get("announce_channel")
                ignored_json = json.dumps(cfg.get("ignored_channels", []))
                last_summary = cfg.get("last_weekly_summary")
                last_monthly = cfg.get("last_monthly_summary")

                conn.execute("""
                    INSERT INTO level_settings (
                        guild_id, enabled, level_up_announce, announce_channel, ignored_channels, last_weekly_summary, last_monthly_summary
                    ) VALUES (?, ?, ?, ?, ?, ?, ?)
                    ON CONFLICT(guild_id) DO UPDATE SET
                        enabled = excluded.enabled,
                        level_up_announce = excluded.level_up_announce,
                        announce_channel = excluded.announce_channel,
                        ignored_channels = excluded.ignored_channels,
                        last_weekly_summary = excluded.last_weekly_summary,
                        last_monthly_summary = excluded.last_monthly_summary
                """, (str(gid_str), enabled, announce, ch_id, ignored_json, last_summary, last_monthly))
            conn.commit()
    except Exception as e:
        print(f"[Leveling] Lỗi khi lưu cấu hình vào SQLite: {e}")


def save_leveling_data():
    """Hàm tương thích ngược."""
    save_leveling_settings()


async def get_guild_level_settings(guild_id: int) -> dict:
    """Lấy cấu hình level của server từ bộ nhớ đồng bộ SQLite."""
    gid_str = str(guild_id)
    if gid_str not in leveling_settings:
        load_leveling_data()
    return leveling_settings.get(gid_str, {
        "enabled": True,
        "level_up_announce": True,
        "announce_channel": None,
        "ignored_channels": [],
        "last_weekly_summary": None,
    })


async def get_user_state(guild_id: int, user_id: int) -> dict:
    """Lấy thông tin người dùng từ database."""
    return await get_user_data(guild_id, user_id)


def get_xp_for_level(level: int) -> int:
    return 5 * (level ** 2) + 50 * level + 100


async def award_daily(guild_id: int, user_id: int):
    user_data = await get_user_data(guild_id, user_id)
    now = time.time()
    last_daily = float(user_data.get("daily_last", 0) or 0)

    if now - last_daily < 86400:
        remaining = int(86400 - (now - last_daily))
        return {
            "ok": False,
            "message": f"Bạn cần chờ thêm {remaining // 3600}h {(remaining % 3600) // 60}m nữa.",
            "remaining": remaining
        }

    streak = int(user_data.get("daily_streak", 0) or 0)
    streak = streak + 1 if (last_daily and now - last_daily <= 172800) else 1
    reward = 500 + random.randint(250, 1200) + streak * 150

    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
            UPDATE global_economy SET coins = coins + ?, daily_last = ?, daily_streak = ?
            WHERE user_id = ?
        """, (reward, now, streak, str(user_id)))
        await db.execute("""
            UPDATE users SET coins = coins + ?, daily_last = ?, daily_streak = ?
            WHERE user_id = ?
        """, (reward, now, streak, str(user_id)))
        await db.commit()

    return {"ok": True, "reward": reward, "streak": streak}


async def work_now(guild_id: int, user_id: int):
    user_data = await get_user_data(guild_id, user_id)
    now = time.time()
    last_work = float(user_data.get("work_last", 0) or 0)

    if now - last_work < 1800:
        remaining = int(1800 - (now - last_work))
        return {
            "ok": False,
            "message": f"Bạn cần chờ thêm {remaining // 60}m {remaining % 60}s nữa để làm việc tiếp.",
            "remaining": remaining
        }

    reward = random.randint(120, 550) + int(user_data.get("level", 0)) * 30
    xp_reward = random.randint(25, 60)

    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
            UPDATE global_economy SET coins = coins + ?, work_last = ?
            WHERE user_id = ?
        """, (reward, now, str(user_id)))
        await db.execute("""
            UPDATE users SET coins = coins + ?, xp = xp + ?, work_last = ?
            WHERE guild_id = ? AND user_id = ?
        """, (reward, xp_reward, now, str(guild_id), str(user_id)))
        await db.commit()

    return {"ok": True, "reward": reward, "xp": user_data.get("xp", 0) + xp_reward}


async def bank_transaction(guild_id: int, user_id: int, action: str, amount: int):
    user_data = await get_user_data(guild_id, user_id)
    amount = int(amount)
    wallet = int(user_data.get("coins", 0))
    bank = int(user_data.get("bank", 0))

    if action == "deposit":
        if amount <= 0:
            return {"ok": False, "message": "Số tiền gửi phải lớn hơn 0."}
        if wallet < amount:
            return {"ok": False, "message": "Bạn không đủ tiền mặt trong ví để gửi."}
        async with aiosqlite.connect(DB_PATH) as db:
            await db.execute("""
                UPDATE global_economy SET coins = coins - ?, bank = bank + ?
                WHERE user_id = ?
            """, (amount, amount, str(user_id)))
            await db.execute("""
                UPDATE users SET coins = coins - ?, bank = bank + ?
                WHERE user_id = ?
            """, (amount, amount, str(user_id)))
            await db.commit()
        return {"ok": True, "message": f"Đã gửi {amount:,} coin vào ngân hàng.", "amount": amount}

    if action == "withdraw":
        if amount <= 0:
            return {"ok": False, "message": "Số tiền rút phải lớn hơn 0."}
        if bank < amount:
            return {"ok": False, "message": "Số dư ngân hàng không đủ để rút."}
        async with aiosqlite.connect(DB_PATH) as db:
            await db.execute("""
                UPDATE global_economy SET bank = bank - ?, coins = coins + ?
                WHERE user_id = ?
            """, (amount, amount, str(user_id)))
            await db.execute("""
                UPDATE users SET bank = bank - ?, coins = coins + ?
                WHERE user_id = ?
            """, (amount, amount, str(user_id)))
            await db.commit()
        return {"ok": True, "message": f"Đã rút {amount:,} coin từ ngân hàng.", "amount": amount}

    return {"ok": False, "message": "Hành động không hợp lệ."}


LEVEL_ROLES_FILE = "data/level_roles.json"


def get_guild_level_roles(guild_id: int | str) -> dict:
    """Lấy danh sách mốc level -> role_id của server. Ví dụ: {'5': 123456, '10': 789012}"""
    import os
    if not os.path.exists(LEVEL_ROLES_FILE):
        return {}
    try:
        with open(LEVEL_ROLES_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
            return data.get(str(guild_id), {})
    except Exception:
        return {}


def save_guild_level_roles(guild_id: int | str, roles: dict):
    """Lưu danh sách mốc level -> role_id của server."""
    import os
    os.makedirs(os.path.dirname(LEVEL_ROLES_FILE), exist_ok=True)
    all_data = {}
    if os.path.exists(LEVEL_ROLES_FILE):
        try:
            with open(LEVEL_ROLES_FILE, "r", encoding="utf-8") as f:
                all_data = json.load(f)
        except Exception:
            all_data = {}
    all_data[str(guild_id)] = roles
    try:
        with open(LEVEL_ROLES_FILE, "w", encoding="utf-8") as f:
            json.dump(all_data, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"[Leveling] Lỗi lưu level_roles: {e}")


async def add_xp(user_id: int, guild_id: int, channel):
    guild_id_str = str(guild_id)
    user_id_str = str(user_id)

    cfg = leveling_settings.get(guild_id_str, {})
    if not cfg.get("enabled", True):
        return False

    if channel and getattr(channel, "id", None) in cfg.get("ignored_channels", []):
        return False

    if is_user_ignored(guild_id, user_id):
        return False

    now = time.time()
    user_cooldown_key = f"{guild_id_str}-{user_id_str}"

    if user_cooldown_key in last_message_time and now - last_message_time[user_cooldown_key] < XP_COOLDOWN:
        return False
    last_message_time[user_cooldown_key] = now

    user_data = await get_user_data(guild_id, user_id)
    gained_xp = random.randint(15, 25)
    record_period_xp(guild_id, user_id, gained_xp)
    current_xp = int(user_data.get("xp", 0)) + gained_xp
    current_level = int(user_data.get("level", 0))
    leveled_up = False

    while True:
        needed_xp = get_xp_for_level(current_level + 1)
        if current_xp >= needed_xp:
            current_xp -= needed_xp
            current_level += 1
            leveled_up = True
        else :
            break

    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
            UPDATE users SET xp = ?, level = ? WHERE guild_id = ? AND user_id = ?
        """, (current_xp, current_level, guild_id_str, user_id_str))
        await db.commit()

    if leveled_up and channel and getattr(channel, "guild", None):
        guild = channel.guild
        member = guild.get_member(user_id)
        if not member:
            try:
                member = await guild.fetch_member(user_id)
            except Exception:
                member = None

        rewarded_roles = []
        if member:
            level_roles = get_guild_level_roles(guild.id)
            for lvl_key, role_id in level_roles.items():
                try:
                    lvl_req = int(lvl_key)
                    if current_level >= lvl_req:
                        r = guild.get_role(int(role_id))
                        if r and r not in member.roles:
                            try:
                                await member.add_roles(r, reason=f"Thưởng đạt mốc Level {lvl_req}")
                                rewarded_roles.append(r)
                            except Exception as re:
                                print(f"[Leveling] Không thể gán role {r.name} cho {member}: {re}")
                except Exception as e:
                    pass

        if not cfg.get("enabled", True) or not cfg.get("level_up_announce", True):
            return leveled_up

        target_channel = channel
        ch_id = cfg.get("announce_channel")
        if ch_id:
            found_ch = channel.guild.get_channel(int(ch_id))
            if found_ch:
                target_channel = found_ch

        if member:
            embed = discord.Embed(
                title="🎉 CHÚC MỪNG THĂNG CẤP! 🎉",
                description=f"Chúc mừng {member.mention} đã tích lũy đủ kinh nghiệm và đạt mốc cấp độ mới!",
                color=discord.Color.gold(),
                timestamp=discord.utils.utcnow()
            )
            embed.set_thumbnail(url=member.display_avatar.url)
            embed.add_field(name="🏅 Cấp Độ Mới", value=f"**Level {current_level}**", inline=True)
            embed.add_field(name="✨ Tổng XP", value=f"`{current_xp:,} XP`", inline=True)
            if rewarded_roles:
                embed.add_field(
                    name="🎁 Phần Thưởng Vai Trò Mới",
                    value=", ".join(r.mention for r in rewarded_roles),
                    inline=False
                )
            try:
                await target_channel.send(content=member.mention, embed=embed)
            except Exception:
                pass

    return leveled_up


load_leveling_data()


# --- Extended leveling: ignored users, period activity and voice time ---
_EXTENDED_TABLES_READY = False


def ensure_extended_tables():
    global _EXTENDED_TABLES_READY
    if _EXTENDED_TABLES_READY:
        return
    try:
        with sqlite3.connect(DB_PATH) as conn:
            conn.executescript("""
                CREATE TABLE IF NOT EXISTS level_ignored_users (
                    guild_id TEXT NOT NULL, user_id TEXT NOT NULL,
                    PRIMARY KEY (guild_id, user_id)
                );
                CREATE TABLE IF NOT EXISTS level_global_ignored_users (
                    user_id TEXT PRIMARY KEY
                );
                CREATE TABLE IF NOT EXISTS level_activity (
                    guild_id TEXT NOT NULL, user_id TEXT NOT NULL,
                    period_key TEXT NOT NULL, period_type TEXT NOT NULL,
                    xp INTEGER NOT NULL DEFAULT 0,
                    PRIMARY KEY (guild_id, user_id, period_key, period_type)
                );
                CREATE TABLE IF NOT EXISTS voice_totals (
                    guild_id TEXT NOT NULL, user_id TEXT NOT NULL,
                    seconds INTEGER NOT NULL DEFAULT 0,
                    PRIMARY KEY (guild_id, user_id)
                );
                CREATE TABLE IF NOT EXISTS voice_activity (
                    guild_id TEXT NOT NULL, user_id TEXT NOT NULL,
                    period_key TEXT NOT NULL, period_type TEXT NOT NULL,
                    seconds INTEGER NOT NULL DEFAULT 0,
                    PRIMARY KEY (guild_id, user_id, period_key, period_type)
                );
                CREATE TABLE IF NOT EXISTS voice_sessions (
                    guild_id TEXT NOT NULL, user_id TEXT NOT NULL,
                    started_at REAL NOT NULL,
                    PRIMARY KEY (guild_id, user_id)
                );
            """)
            conn.commit()
        _EXTENDED_TABLES_READY = True
    except Exception as e:
        print(f"[Leveling] Lỗi tạo bảng mở rộng: {e}")


def _period_keys(ts=None):
    from datetime import datetime, timezone
    from zoneinfo import ZoneInfo
    dt = datetime.fromtimestamp(ts or time.time(), ZoneInfo("Asia/Ho_Chi_Minh"))
    iso = dt.isocalendar()
    return f"{iso.year}-W{iso.week:02d}", f"{dt.year}-{dt.month:02d}"


def is_user_ignored(guild_id: int, user_id: int) -> bool:
    ensure_extended_tables()
    try:
        with sqlite3.connect(DB_PATH) as conn:
            global_row = conn.execute(
                "SELECT 1 FROM level_global_ignored_users WHERE user_id=?", (str(user_id),)
            ).fetchone()
            local_row = conn.execute(
                "SELECT 1 FROM level_ignored_users WHERE guild_id=? AND user_id=?",
                (str(guild_id), str(user_id))
            ).fetchone()
            return bool(global_row or local_row)
    except Exception:
        return False


def set_ignored_user(guild_id: int, user_id: int, ignored: bool, global_scope: bool = False):
    ensure_extended_tables()
    with sqlite3.connect(DB_PATH) as conn:
        if global_scope:
            if ignored:
                conn.execute("INSERT OR IGNORE INTO level_global_ignored_users(user_id) VALUES (?)", (str(user_id),))
            else:
                conn.execute("DELETE FROM level_global_ignored_users WHERE user_id=?", (str(user_id),))
        else:
            if ignored:
                conn.execute("INSERT OR IGNORE INTO level_ignored_users(guild_id,user_id) VALUES (?,?)",
                             (str(guild_id), str(user_id)))
            else:
                conn.execute("DELETE FROM level_ignored_users WHERE guild_id=? AND user_id=?",
                             (str(guild_id), str(user_id)))
        conn.commit()


def record_period_xp(guild_id: int, user_id: int, amount: int):
    ensure_extended_tables()
    week, month = _period_keys()
    with sqlite3.connect(DB_PATH) as conn:
        for kind, key in (("week", week), ("month", month)):
            conn.execute("""
                INSERT INTO level_activity(guild_id,user_id,period_key,period_type,xp)
                VALUES(?,?,?,?,?)
                ON CONFLICT(guild_id,user_id,period_key,period_type)
                DO UPDATE SET xp=xp+excluded.xp
            """, (str(guild_id), str(user_id), key, kind, int(amount)))
        conn.commit()


def get_period_leaderboard(guild_id=None, period_type="week", limit=10):
    ensure_extended_tables()
    week, month = _period_keys()
    key = week if period_type == "week" else month
    with sqlite3.connect(DB_PATH) as conn:
        conn.row_factory = sqlite3.Row
        if guild_id is None:
            rows = conn.execute("""
                SELECT user_id, SUM(xp) AS xp FROM level_activity
                WHERE period_key=? AND period_type=? GROUP BY user_id
                ORDER BY xp DESC LIMIT ?
            """, (key, period_type, limit)).fetchall()
        else:
            rows = conn.execute("""
                SELECT user_id, xp FROM level_activity
                WHERE guild_id=? AND period_key=? AND period_type=?
                ORDER BY xp DESC LIMIT ?
            """, (str(guild_id), key, period_type, limit)).fetchall()
        return [dict(r) for r in rows]


async def add_voice_time(guild_id: int, user_id: int, seconds: int):
    seconds = max(0, int(seconds))
    if not seconds:
        return
    ensure_extended_tables()
    week, month = _period_keys()
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
            INSERT INTO voice_totals(guild_id,user_id,seconds) VALUES(?,?,?)
            ON CONFLICT(guild_id,user_id) DO UPDATE SET seconds=seconds+excluded.seconds
        """, (str(guild_id), str(user_id), seconds))
        for kind, key in (("week", week), ("month", month)):
            await db.execute("""
                INSERT INTO voice_activity(guild_id,user_id,period_key,period_type,seconds)
                VALUES(?,?,?,?,?)
                ON CONFLICT(guild_id,user_id,period_key,period_type)
                DO UPDATE SET seconds=seconds+excluded.seconds
            """, (str(guild_id), str(user_id), key, kind, seconds))
        await db.commit()


async def start_voice_session(guild_id: int, user_id: int):
    ensure_extended_tables()
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
            INSERT INTO voice_sessions(guild_id,user_id,started_at) VALUES(?,?,?)
            ON CONFLICT(guild_id,user_id) DO UPDATE SET started_at=excluded.started_at
        """, (str(guild_id), str(user_id), time.time()))
        await db.commit()


async def end_voice_session(guild_id: int, user_id: int):
    ensure_extended_tables()
    async with aiosqlite.connect(DB_PATH) as db:
        cur = await db.execute(
            "SELECT started_at FROM voice_sessions WHERE guild_id=? AND user_id=?",
            (str(guild_id), str(user_id))
        )
        row = await cur.fetchone()
        await db.execute("DELETE FROM voice_sessions WHERE guild_id=? AND user_id=?",
                         (str(guild_id), str(user_id)))
        await db.commit()
    if row:
        await add_voice_time(guild_id, user_id, int(max(0, time.time() - float(row[0]))))


async def get_voice_leaderboard(guild_id: int, limit=10, period_type="all"):
    ensure_extended_tables()
    with sqlite3.connect(DB_PATH) as conn:
        conn.row_factory = sqlite3.Row
        if period_type == "all":
            rows = conn.execute("""
                SELECT user_id, seconds FROM voice_totals WHERE guild_id=?
                ORDER BY seconds DESC LIMIT ?
            """, (str(guild_id), limit)).fetchall()
        else:
            week, month = _period_keys()
            key = week if period_type == "week" else month
            rows = conn.execute("""
                SELECT user_id, seconds FROM voice_activity
                WHERE guild_id=? AND period_key=? AND period_type=?
                ORDER BY seconds DESC LIMIT ?
            """, (str(guild_id), key, period_type, limit)).fetchall()
        return [dict(r) for r in rows]


async def get_global_voice_leaderboard(limit=10, period_type="all"):
    ensure_extended_tables()
    with sqlite3.connect(DB_PATH) as conn:
        conn.row_factory = sqlite3.Row
        if period_type == "all":
            rows = conn.execute("""
                SELECT user_id, SUM(seconds) AS seconds FROM voice_totals
                GROUP BY user_id ORDER BY seconds DESC LIMIT ?
            """, (limit,)).fetchall()
        else:
            week, month = _period_keys()
            key = week if period_type == "week" else month
            rows = conn.execute("""
                SELECT user_id, SUM(seconds) AS seconds FROM voice_activity
                WHERE period_key=? AND period_type=? GROUP BY user_id
                ORDER BY seconds DESC LIMIT ?
            """, (key, period_type, limit)).fetchall()
        return [dict(r) for r in rows]


def format_duration(seconds: int) -> str:
    seconds = max(0, int(seconds))
    days, rem = divmod(seconds, 86400)
    hours, rem = divmod(rem, 3600)
    minutes = rem // 60
    if days:
        return f"{days} ngày {hours} giờ"
    if hours:
        return f"{hours} giờ {minutes} phút"
    return f"{minutes} phút"
