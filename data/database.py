import json
import os
import time
import aiosqlite
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
DB_PATH = DATA_DIR / "bot_database.db"
OLD_LEVELS_FILE = DATA_DIR / "levels.json"


async def init_db():
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    async with aiosqlite.connect(DB_PATH) as db:
        try:
            await db.execute("PRAGMA journal_mode=WAL;")
            await db.execute("PRAGMA synchronous=NORMAL;")
            await db.execute("PRAGMA cache_size = -64000;")
            await db.execute("PRAGMA temp_store = MEMORY;")
        except Exception:
            pass

        await db.execute("""
            CREATE TABLE IF NOT EXISTS users (
                guild_id TEXT,
                user_id TEXT,
                xp INTEGER DEFAULT 0,
                level INTEGER DEFAULT 0,
                coins INTEGER DEFAULT 0,
                bank INTEGER DEFAULT 0,
                daily_last REAL DEFAULT 0,
                daily_streak INTEGER DEFAULT 0,
                work_last REAL DEFAULT 0,
                xu INTEGER DEFAULT 0,
                PRIMARY KEY (guild_id, user_id)
            )
        """)
        await db.execute("""
            CREATE TABLE IF NOT EXISTS global_economy (
                user_id TEXT PRIMARY KEY,
                coins INTEGER DEFAULT 0,
                bank INTEGER DEFAULT 0,
                xu INTEGER DEFAULT 0,
                daily_last REAL DEFAULT 0,
                daily_streak INTEGER DEFAULT 0,
                work_last REAL DEFAULT 0
            )
        """)
        await db.execute("""
            INSERT OR IGNORE INTO global_economy (user_id, coins, bank, xu, daily_last, daily_streak, work_last)
            SELECT user_id, MAX(coins), MAX(bank), MAX(xu), MAX(daily_last), MAX(daily_streak), MAX(work_last)
            FROM users
            GROUP BY user_id
        """)

        async with db.execute("PRAGMA table_info(users)") as cursor:
            columns = [row[1] for row in await cursor.fetchall()]
            if "xu" not in columns:
                try:
                    await db.execute("ALTER TABLE users ADD COLUMN xu INTEGER DEFAULT 0")
                except Exception:
                    pass

        await db.execute("""
            CREATE TABLE IF NOT EXISTS lottery (
                guild_id TEXT,
                user_id TEXT,
                ticket_count INTEGER DEFAULT 1,
                PRIMARY KEY (guild_id, user_id)
            )
        """)

        await db.execute("""
            CREATE TABLE IF NOT EXISTS mc_servers (
                server_key TEXT PRIMARY KEY,
                server_name TEXT,
                server_ip TEXT,
                server_port INTEGER,
                guild_id TEXT,
                linked_by TEXT,
                linked_at INTEGER,
                auth_token TEXT,
                chat_channel_id TEXT,
                log_channel_id TEXT,
                status TEXT DEFAULT 'offline',
                last_heartbeat REAL DEFAULT 0,
                online_players TEXT DEFAULT '[]',
                player_count INTEGER DEFAULT 0,
                max_players INTEGER DEFAULT 50,
                tps REAL DEFAULT 20.0,
                version TEXT DEFAULT '',
                raw_info TEXT DEFAULT '{}'
            )
        """)

        await db.execute("""
            CREATE TABLE IF NOT EXISTS mc_server_link_codes (
                code TEXT PRIMARY KEY,
                server_key TEXT,
                server_name TEXT,
                created_at INTEGER,
                expires_at INTEGER
            )
        """)

        await db.execute("""
            CREATE TABLE IF NOT EXISTS mc_user_link_codes (
                code TEXT PRIMARY KEY,
                player_uuid TEXT,
                player_name TEXT,
                created_at INTEGER,
                expires_at INTEGER
            )
        """)

        await db.execute("""
            CREATE TABLE IF NOT EXISTS mc_user_links (
                discord_id TEXT PRIMARY KEY,
                minecraft_uuid TEXT,
                minecraft_name TEXT,
                linked_at INTEGER,
                mc_coins INTEGER DEFAULT 0
            )
        """)

        await db.execute("""
            CREATE TABLE IF NOT EXISTS mc_pending_commands (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                server_key TEXT,
                command TEXT,
                executed_by TEXT,
                status TEXT DEFAULT 'pending',
                response TEXT DEFAULT '',
                created_at REAL,
                completed_at REAL
            )
        """)

        await db.execute("""
            CREATE TABLE IF NOT EXISTS mc_chat_queue (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                server_key TEXT,
                source TEXT,
                sender TEXT,
                message TEXT,
                timestamp REAL,
                delivered INTEGER DEFAULT 0
            )
        """)

        await db.execute("""
            CREATE TABLE IF NOT EXISTS hoyolab_accounts (
                user_id TEXT,
                account_name TEXT,
                cookies_json TEXT,
                ltuid TEXT,
                ltoken TEXT,
                cookie_token TEXT,
                stoken TEXT,
                mid TEXT,
                game_accounts_json TEXT,
                auto_checkin INTEGER DEFAULT 1,
                auto_redeem INTEGER DEFAULT 1,
                created_at REAL,
                updated_at REAL,
                PRIMARY KEY (user_id, account_name)
            )
        """)

        await db.commit()

        HOYO_COOKIE_FILE = DATA_DIR / "hoyolab_cookies.json"
        if HOYO_COOKIE_FILE.exists():
            try:
                with open(HOYO_COOKIE_FILE, "r", encoding="utf-8") as f:
                    hoyo_data = json.load(f)
                if isinstance(hoyo_data, dict):
                    now_ts = time.time()
                    for u_id, acc_list in hoyo_data.items():
                        if isinstance(acc_list, list):
                            for acc in acc_list:
                                if isinstance(acc, dict):
                                    a_name = acc.get("name", "Mặc định")
                                    c_dict = acc.get("cookies", {})
                                    g_accs = acc.get("game_accounts", [])
                                    a_check = 1 if acc.get("auto_checkin", True) else 0
                                    a_redeem = 1 if acc.get("auto_redeem", True) else 0
                                    ltuid = c_dict.get("ltuid_v2") or c_dict.get("ltuid") or c_dict.get("account_id_v2") or ""
                                    ltoken = c_dict.get("ltoken_v2") or c_dict.get("ltoken") or ""
                                    ctoken = c_dict.get("cookie_token_v2") or c_dict.get("cookie_token") or ""
                                    stoken = c_dict.get("stoken_v2") or c_dict.get("stoken") or ""
                                    mid = c_dict.get("ltmid_v2") or c_dict.get("mid") or ""
                                    await db.execute("""
                                        INSERT OR IGNORE INTO hoyolab_accounts (
                                            user_id, account_name, cookies_json, ltuid, ltoken, 
                                            cookie_token, stoken, mid, game_accounts_json, 
                                            auto_checkin, auto_redeem, created_at, updated_at
                                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                                    """, (
                                        str(u_id), a_name, json.dumps(c_dict, ensure_ascii=False),
                                        str(ltuid), str(ltoken), str(ctoken), str(stoken), str(mid),
                                        json.dumps(g_accs, ensure_ascii=False), a_check, a_redeem,
                                        now_ts, now_ts
                                    ))
                    await db.commit()
            except Exception as e:
                print(f"[DB Migration Hoyo] Warning: {e}")


        if OLD_LEVELS_FILE.exists():
            try:
                with open(OLD_LEVELS_FILE, "r", encoding="utf-8") as f:
                    old_data = json.load(f)
                    if isinstance(old_data, dict):
                        for gid, u_dict in old_data.items():
                            for uid, stats in u_dict.items():
                                await db.execute("""
                                    INSERT OR IGNORE INTO users (guild_id, user_id, xp, level, coins, bank, daily_last, daily_streak, work_last, xu)
                                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                                """, (
                                    str(gid), str(uid),
                                    stats.get("xp", 0), stats.get("level", 0),
                                    stats.get("coins", 0), stats.get("bank", 0),
                                    stats.get("daily_last", 0), stats.get("daily_streak", 0),
                                    stats.get("work_last", 0),
                                    stats.get("xu", 0)
                                ))
                        await db.commit()
            except Exception:
                pass


async def get_user_data(guild_id: int, user_id: int) -> dict:
    gid, uid = str(guild_id), str(user_id)
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row

        async with db.execute("SELECT * FROM users WHERE guild_id = ? AND user_id = ?", (gid, uid)) as cursor:
            row_user = await cursor.fetchone()
            if not row_user:
                await db.execute("""
                    INSERT OR IGNORE INTO users (guild_id, user_id, xp, level, coins, bank, daily_last, daily_streak, work_last, xu)
                    VALUES (?, ?, 0, 0, 0, 0, 0, 0, 0, 0)
                """, (gid, uid))
                await db.commit()
                row_user = {"guild_id": gid, "user_id": uid, "xp": 0, "level": 0}
            else:
                row_user = dict(row_user)

        await db.execute("""
            CREATE TABLE IF NOT EXISTS global_economy (
                user_id TEXT PRIMARY KEY,
                coins INTEGER DEFAULT 0,
                bank INTEGER DEFAULT 0,
                xu INTEGER DEFAULT 0,
                daily_last REAL DEFAULT 0,
                daily_streak INTEGER DEFAULT 0,
                work_last REAL DEFAULT 0
            )
        """)
        async with db.execute("SELECT * FROM global_economy WHERE user_id = ?", (uid,)) as cur_econ:

            row_econ = await cur_econ.fetchone()
            if not row_econ:
                coins_init = row_user.get("coins", 0)
                bank_init = row_user.get("bank", 0)
                xu_init = row_user.get("xu", 0)
                daily_last_init = row_user.get("daily_last", 0)
                daily_streak_init = row_user.get("daily_streak", 0)
                work_last_init = row_user.get("work_last", 0)
                await db.execute("""
                    INSERT OR IGNORE INTO global_economy (user_id, coins, bank, xu, daily_last, daily_streak, work_last)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (uid, coins_init, bank_init, xu_init, daily_last_init, daily_streak_init, work_last_init))
                await db.commit()
                row_econ = {
                    "coins": coins_init, "bank": bank_init, "xu": xu_init,
                    "daily_last": daily_last_init, "daily_streak": daily_streak_init, "work_last": work_last_init
                }
            else:
                row_econ = dict(row_econ)

        res = {
            "guild_id": gid,
            "user_id": uid,
            "xp": row_user.get("xp", 0),
            "level": row_user.get("level", 0),
            "coins": row_econ.get("coins", 0),
            "bank": row_econ.get("bank", 0),
            "xu": row_econ.get("xu", 0),
            "daily_last": row_econ.get("daily_last", 0),
            "daily_streak": row_econ.get("daily_streak", 0),
            "work_last": row_econ.get("work_last", 0)
        }
        return res


async def update_user_coins(guild_id: int, user_id: int, amount: int) -> int:
    uid = str(user_id)
    gid = str(guild_id)
    await get_user_data(guild_id, user_id)
    async with aiosqlite.connect(DB_PATH) as db:
        if amount < 0:
            await db.execute("UPDATE global_economy SET coins = MAX(0, coins + ?) WHERE user_id = ?", (amount, uid))
            await db.execute("UPDATE users SET coins = MAX(0, coins + ?) WHERE user_id = ?", (amount, uid))
        else:
            await db.execute("UPDATE global_economy SET coins = coins + ? WHERE user_id = ?", (amount, uid))
            await db.execute("UPDATE users SET coins = coins + ? WHERE user_id = ?", (amount, uid))
        await db.commit()
        async with db.execute("SELECT coins FROM global_economy WHERE user_id = ?", (uid,)) as cur:
            res = await cur.fetchone()
            return res[0] if res else 0


async def update_user_xu(guild_id: int, user_id: int, amount: int) -> int:
    """Cộng hoặc trừ Xu (tiền tệ đặc biệt: chỉ nạp hoặc Owner add/thưởng) đồng bộ toàn hệ thống."""
    uid = str(user_id)
    await get_user_data(guild_id, user_id)
    async with aiosqlite.connect(DB_PATH) as db:
        if amount < 0:
            await db.execute("UPDATE global_economy SET xu = MAX(0, xu + ?) WHERE user_id = ?", (amount, uid))
            await db.execute("UPDATE users SET xu = MAX(0, xu + ?) WHERE user_id = ?", (amount, uid))
        else:
            await db.execute("UPDATE global_economy SET xu = xu + ? WHERE user_id = ?", (amount, uid))
            await db.execute("UPDATE users SET xu = xu + ? WHERE user_id = ?", (amount, uid))
        await db.commit()
        async with db.execute("SELECT xu FROM global_economy WHERE user_id = ?", (uid,)) as cur:
            res = await cur.fetchone()
            return res[0] if res else 0


async def set_user_xu(guild_id: int | str, user_id: int | str, amount: int) -> int:
    """Thiết lập chính xác số Xu cho người dùng toàn cục."""
    uid = str(user_id)
    val = max(0, int(amount))
    await get_user_data(int(guild_id), int(uid))
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("UPDATE global_economy SET xu = ? WHERE user_id = ?", (val, uid))
        await db.execute("UPDATE users SET xu = ? WHERE user_id = ?", (val, uid))
        await db.commit()
    return val


async def update_user_bank(guild_id: int | str, user_id: int | str, amount: int) -> int:
    """Cộng hoặc trừ số dư Bank (tiền gửi ngân hàng) đồng bộ toàn hệ thống (global_economy & users)."""
    uid = str(user_id)
    await get_user_data(int(guild_id), int(uid))
    async with aiosqlite.connect(DB_PATH) as db:
        if amount < 0:
            await db.execute("UPDATE global_economy SET bank = MAX(0, bank + ?) WHERE user_id = ?", (amount, uid))
            await db.execute("UPDATE users SET bank = MAX(0, bank + ?) WHERE user_id = ?", (amount, uid))
        else:
            await db.execute("UPDATE global_economy SET bank = bank + ? WHERE user_id = ?", (amount, uid))
            await db.execute("UPDATE users SET bank = bank + ? WHERE user_id = ?", (amount, uid))
        await db.commit()
        async with db.execute("SELECT bank FROM global_economy WHERE user_id = ?", (uid,)) as cur:
            res = await cur.fetchone()
            return res[0] if res else 0


async def set_user_bank(guild_id: int | str, user_id: int | str, amount: int) -> int:
    """Thiết lập chính xác số dư Bank cho người dùng toàn cục và đồng bộ users."""
    uid = str(user_id)
    val = max(0, int(amount))
    await get_user_data(int(guild_id), int(uid))
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("UPDATE global_economy SET bank = ? WHERE user_id = ?", (val, uid))
        await db.execute("UPDATE users SET bank = ? WHERE user_id = ?", (val, uid))
        await db.commit()
    return val


async def set_user_coins(guild_id: int | str, user_id: int | str, amount: int) -> int:
    """Thiết lập chính xác số Coins (tiền mặt ví) cho người dùng toàn cục và đồng bộ users."""
    uid = str(user_id)
    val = max(0, int(amount))
    await get_user_data(int(guild_id), int(uid))
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("UPDATE global_economy SET coins = ? WHERE user_id = ?", (val, uid))
        await db.execute("UPDATE users SET coins = ? WHERE user_id = ?", (val, uid))
        await db.commit()
    return val


def get_global_economy(user_id: int | str) -> dict:
    """Lấy số dư toàn cục (coins, bank, xu) đồng bộ (cho Web/API)."""
    import sqlite3
    uid = str(user_id)
    try:
        with sqlite3.connect(DB_PATH) as conn:
            conn.row_factory = sqlite3.Row
            cur = conn.execute("SELECT coins, bank, xu FROM global_economy WHERE user_id = ?", (uid,))
            row = cur.fetchone()
            if row:
                return {"coins": int(row["coins"]), "bank": int(row["bank"]), "xu": int(row["xu"])}
            cur = conn.execute("SELECT coins, bank, xu FROM users WHERE user_id = ? LIMIT 1", (uid,))
            row_u = cur.fetchone()
            if row_u:
                return {"coins": int(row_u["coins"]), "bank": int(row_u["bank"]), "xu": int(row_u["xu"])}
    except Exception:
        pass
    return {"coins": 0, "bank": 0, "xu": 0}



async def get_user_currency(guild_id: int | str, user_id: int | str, currency: str = "coins") -> int:
    """Lấy số dư theo loại tiền: 'coins' hoặc 'xu' toàn cục."""
    data = await get_user_data(int(guild_id), int(user_id))
    cur_key = "xu" if str(currency).lower() in ("xu", "gem", "gems") else "coins"
    return data.get(cur_key, 0)


async def deduct_user_currency(guild_id: int | str, user_id: int | str, currency: str, amount: int) -> bool:
    """Trừ tiền một cách an toàn (atomic) từ tài khoản toàn cục. Trả về True nếu trừ thành công, False nếu không đủ tiền."""
    if amount <= 0:
        return True
    uid = str(user_id)
    cur_col = "xu" if str(currency).lower() in ("xu", "gem", "gems") else "coins"
    await get_user_data(int(guild_id), int(uid))
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute(
            f"UPDATE global_economy SET {cur_col} = {cur_col} - ? WHERE user_id = ? AND {cur_col} >= ?",
            (amount, uid, amount)
        )
        if cursor.rowcount > 0:
            await db.execute(
                f"UPDATE users SET {cur_col} = {cur_col} - ? WHERE user_id = ?",
                (amount, uid)
            )
            await db.commit()
            return True
        await db.commit()
        return False


async def add_user_currency(guild_id: int | str, user_id: int | str, currency: str, amount: int) -> int:
    """Cộng tiền an toàn cho user theo loại tiền tệ ('coins' hoặc 'xu') vào tài khoản toàn cục."""
    gid, uid = int(guild_id), int(user_id)
    cur_key = "xu" if str(currency).lower() in ("xu", "gem", "gems") else "coins"
    if cur_key == "xu":
        return await update_user_xu(gid, uid, amount)
    else:
        return await update_user_coins(gid, uid, amount)


async def get_leaderboard_data(guild_id: int, limit: int = 10) -> list[dict]:
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("""
            SELECT * FROM users WHERE guild_id = ? AND user_id != '1144785664458637394' 
            ORDER BY level DESC, xp DESC LIMIT ?
        """, (str(guild_id), limit)) as cursor:
            rows = await cursor.fetchall()
            return [dict(r) for r in rows]


async def get_guild_level_and_economy_stats(guild_id: str | int) -> dict:
    gid = str(guild_id)
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("SELECT COUNT(*) FROM users WHERE guild_id = ? AND xp > 0", (gid,)) as cur:
            row = await cur.fetchone()
            cnt_level = row[0] if row else 0
        async with db.execute("SELECT COUNT(*) FROM users WHERE guild_id = ? AND (coins > 0 OR bank > 0 OR xu > 0)", (gid,)) as cur:
            row = await cur.fetchone()
            cnt_econ = row[0] if row else 0
        async with db.execute("SELECT user_id, xp, level FROM users WHERE guild_id = ? AND user_id != '1144785664458637394' ORDER BY level DESC, xp DESC LIMIT 5", (gid,)) as cur:
            top_level = [dict(r) for r in await cur.fetchall()]
        async with db.execute("SELECT user_id, coins, bank, xu, (coins + bank) AS total FROM users WHERE guild_id = ? AND user_id != '1144785664458637394' ORDER BY total DESC, coins DESC LIMIT 5", (gid,)) as cur:
            top_rich = [dict(r) for r in await cur.fetchall()]
        return {
            "cnt_level": cnt_level,
            "cnt_econ": cnt_econ,
            "top_level": top_level,
            "top_rich": top_rich
        }


async def get_web_levels_leaderboard(guild_id: str | int | None = None, limit: int = 100) -> dict:
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        if guild_id:
            gid = str(guild_id)
            async with db.execute("SELECT COUNT(*) FROM users WHERE guild_id = ?", (gid,)) as cur:
                row = await cur.fetchone()
                total = row[0] if row else 0
            async with db.execute("""
                SELECT user_id, guild_id, level, xp, coins, bank, xu
                FROM users
                WHERE guild_id = ? AND user_id != '1144785664458637394'
                ORDER BY level DESC, xp DESC, coins DESC
                LIMIT ?
            """, (gid, limit)) as cur:
                rows = [dict(r) for r in await cur.fetchall()]
        else:
            async with db.execute("SELECT COUNT(DISTINCT user_id) FROM users") as cur:
                row = await cur.fetchone()
                total = row[0] if row else 0
            async with db.execute("""
                SELECT user_id, guild_id, MAX(level) AS level, MAX(xp) AS xp, MAX(coins) AS coins, MAX(bank) AS bank, MAX(xu) AS xu
                FROM users
                GROUP BY user_id
                ORDER BY level DESC, xp DESC, coins DESC
                LIMIT ?
            """, (limit,)) as cur:
                rows = [dict(r) for r in await cur.fetchall()]
        return {"users": rows, "total_users": total}


async def update_user_level_stats(user_id: str | int, guild_id: str | int | None, level: int, xp: int, coins: int | None = None, bank: int | None = None, xu: int | None = None) -> bool:
    uid = str(user_id)
    gid = str(guild_id) if guild_id else None
    await get_user_data(int(gid or 0), int(uid))
    async with aiosqlite.connect(DB_PATH) as db:
        if gid:
            async with db.execute("SELECT coins, bank, xu FROM users WHERE guild_id = ? AND user_id = ?", (gid, uid)) as cur:
                existing = await cur.fetchone()
            cur_coins = existing[0] if existing else 0
            cur_bank = existing[1] if existing else 0
            cur_xu = existing[2] if existing else 0
            
            final_coins = coins if coins is not None else cur_coins
            final_bank = bank if bank is not None else cur_bank
            final_xu = xu if xu is not None else cur_xu

            await db.execute("""
                INSERT INTO users (guild_id, user_id, level, xp, coins, bank, xu)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(guild_id, user_id) DO UPDATE SET
                    level = excluded.level,
                    xp = excluded.xp,
                    coins = excluded.coins,
                    bank = excluded.bank,
                    xu = excluded.xu
            """, (gid, uid, level, xp, final_coins, final_bank, final_xu))

            if coins is not None or bank is not None or xu is not None:
                await db.execute("""
                    UPDATE global_economy SET coins = ?, bank = ?, xu = ? WHERE user_id = ?
                """, (final_coins, final_bank, final_xu, uid))
        else:
            set_clauses = ["level = ?", "xp = ?"]
            params = [level, xp]
            if coins is not None:
                set_clauses.append("coins = ?")
                params.append(coins)
            if bank is not None:
                set_clauses.append("bank = ?")
                params.append(bank)
            if xu is not None:
                set_clauses.append("xu = ?")
                params.append(xu)
            params.append(uid)

            await db.execute(f"UPDATE users SET {', '.join(set_clauses)} WHERE user_id = ?", tuple(params))

            if coins is not None or bank is not None or xu is not None:
                econ_clauses = []
                econ_params = []
                if coins is not None:
                    econ_clauses.append("coins = ?")
                    econ_params.append(coins)
                if bank is not None:
                    econ_clauses.append("bank = ?")
                    econ_params.append(bank)
                if xu is not None:
                    econ_clauses.append("xu = ?")
                    econ_params.append(xu)
                econ_params.append(uid)
                await db.execute(f"UPDATE global_economy SET {', '.join(econ_clauses)} WHERE user_id = ?", tuple(econ_params))

            async with db.execute("SELECT COUNT(*) FROM users WHERE user_id = ?", (uid,)) as cur:
                row = await cur.fetchone()
                c = row[0] if row else 0
            if c == 0:
                await db.execute("""
                    INSERT INTO users (guild_id, user_id, level, xp, coins, bank, xu)
                    VALUES ('0', ?, ?, ?, ?, ?, ?)
                """, (uid, level, xp, coins or 0, bank or 0, xu or 0))
        await db.commit()
        return True


MC_COIN_RATE = 1000


async def get_mc_server(server_key: str) -> dict | None:
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("SELECT * FROM mc_servers WHERE server_key = ?", (server_key,)) as cur:
            row = await cur.fetchone()
            if not row:
                return None
            res = dict(row)
            try:
                res["online_players"] = json.loads(res.get("online_players") or "[]")
            except Exception:
                res["online_players"] = []
            return res


async def get_mc_server_by_guild(guild_id: str | int) -> dict | None:
    gid = str(guild_id)
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("SELECT * FROM mc_servers WHERE guild_id = ? ORDER BY last_heartbeat DESC LIMIT 1", (gid,)) as cur:
            row = await cur.fetchone()
            if not row:
                return None
            res = dict(row)
            try:
                res["online_players"] = json.loads(res.get("online_players") or "[]")
            except Exception:
                res["online_players"] = []
            return res


async def list_mc_servers(online_threshold: int = 90) -> list[dict]:
    """Danh sách các server Minecraft, tự động tính trạng thái online nếu heartbeat < online_threshold giây."""
    now = time.time()
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("SELECT * FROM mc_servers ORDER BY last_heartbeat DESC") as cur:
            rows = await cur.fetchall()
            servers = []
            for r in rows:
                s = dict(r)
                is_active = (now - float(s.get("last_heartbeat", 0))) <= online_threshold
                s["status"] = "online" if is_active else "offline"
                try:
                    s["online_players"] = json.loads(s.get("online_players") or "[]")
                except Exception:
                    s["online_players"] = []
                servers.append(s)
            return servers


async def upsert_mc_server_heartbeat(
    server_key: str = "",
    server_name: str = "",
    server_ip: str = "127.0.0.1",
    server_port: int = 25565,
    online_players: list | None = None,
    max_players: int = 50,
    tps: float = 20.0,
    version: str = "",
    raw_info: dict | None = None,
    auth_token: str = "",
    **kwargs
) -> dict:
    key = server_key or kwargs.get("server_id", "default")
    name = server_name or kwargs.get("name", "Minecraft Server")
    ip = kwargs.get("ip", server_ip)
    port = kwargs.get("port", server_port)
    raw_players = online_players if isinstance(online_players, list) else kwargs.get("player_list", [])
    if not isinstance(raw_players, list):
        raw_players = []
    
    if isinstance(online_players, (int, float)):
        p_count = int(online_players)
    else:
        p_count = len(raw_players)

    players = raw_players
    max_p = int(kwargs.get("max_players", max_players) or 50)
    cur_tps = float(kwargs.get("tps", tps) or 20.0)
    ver = str(kwargs.get("version", version) or "")
    info = dict(raw_info or {})
    if "plugin_version" in kwargs:
        info["plugin_version"] = kwargs["plugin_version"]

    now = time.time()
    players_json = json.dumps(players or [], ensure_ascii=False)
    raw_json = json.dumps(info or {}, ensure_ascii=False)

    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("SELECT server_key, guild_id FROM mc_servers WHERE server_key = ?", (key,)) as cur:
            existing = await cur.fetchone()

        if existing:
            await db.execute("""
                UPDATE mc_servers SET
                    server_name = ?,
                    server_ip = ?,
                    server_port = ?,
                    status = 'online',
                    last_heartbeat = ?,
                    online_players = ?,
                    player_count = ?,
                    max_players = ?,
                    tps = ?,
                    version = ?,
                    raw_info = ?
                WHERE server_key = ?
            """, (name, ip, port, now, players_json, p_count, max_p, cur_tps, ver, raw_json, key))
        else:
            await db.execute("""
                INSERT INTO mc_servers (
                    server_key, server_name, server_ip, server_port, guild_id,
                    linked_by, linked_at, auth_token, status, last_heartbeat,
                    online_players, player_count, max_players, tps, version, raw_info
                ) VALUES (?, ?, ?, ?, NULL, NULL, NULL, ?, 'online', ?, ?, ?, ?, ?, ?, ?)
            """, (
                key, name, ip, port, auth_token or key,
                now, players_json, p_count, max_p, cur_tps, ver, raw_json
            ))
        await db.commit()

    return await get_mc_server(key) or {}


async def create_mc_server_link_code(server_key: str, server_name: str = "") -> str:
    """Tạo mã liên kết server dạng MCLINK-XXXXXX có hạn trong 15 phút (hỗ trợ nhập cả mã rút gọn 6 ký tự)."""
    import secrets
    raw = secrets.token_hex(3).upper()
    code = f"MCLINK-{raw}"
    now = int(time.time())
    expires_at = now + 900

    if not server_name:
        s_obj = await get_mc_server(server_key)
        server_name = s_obj.get("server_name", server_key) if s_obj else server_key

    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("DELETE FROM mc_server_link_codes WHERE expires_at < ?", (now,))
        await db.execute("""
            INSERT OR REPLACE INTO mc_server_link_codes (code, server_key, server_name, created_at, expires_at)
            VALUES (?, ?, ?, ?, ?)
        """, (code, server_key, server_name, now, expires_at))
        await db.execute("""
            INSERT OR REPLACE INTO mc_server_link_codes (code, server_key, server_name, created_at, expires_at)
            VALUES (?, ?, ?, ?, ?)
        """, (raw, server_key, server_name, now, expires_at))
        await db.commit()
    return code


async def link_mc_server_to_guild(code: str, guild_id: str | int, user_id: str | int | None = None) -> dict:
    """Liên kết server MC với guild qua mã code. Yêu cầu user là Owner/Admin guild."""
    code_clean = str(code).strip().upper()
    code_raw = code_clean.replace("MCLINK-", "")
    code_full = f"MCLINK-{code_raw}"
    gid = str(guild_id)
    uid = str(user_id) if user_id else None
    now = int(time.time())

    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("""
            SELECT * FROM mc_server_link_codes 
            WHERE (code = ? OR code = ? OR code = ?) AND expires_at >= ?
        """, (code_clean, code_raw, code_full, now)) as cur:
            row_code = await cur.fetchone()

        if not row_code:
            return {"ok": False, "error": "Mã liên kết không tồn tại hoặc đã hết hạn (15 phút). Hãy dùng lệnh /discord server link trong game để lấy mã mới."}

        server_key = row_code["server_key"]
        server_name = row_code["server_name"] or server_key

        async with db.execute("SELECT server_key FROM mc_servers WHERE server_key = ?", (server_key,)) as cur:
            exists = await cur.fetchone()

        if exists:
            await db.execute("""
                UPDATE mc_servers SET
                    guild_id = ?,
                    linked_by = ?,
                    linked_at = ?
                WHERE server_key = ?
            """, (gid, uid, now, server_key))
        else:
            await db.execute("""
                INSERT INTO mc_servers (
                    server_key, server_name, guild_id, linked_by, linked_at, status, last_heartbeat
                ) VALUES (?, ?, ?, ?, ?, 'online', ?)
            """, (server_key, server_name, gid, uid, now, now))

        await db.execute("DELETE FROM mc_server_link_codes WHERE server_key = ? OR code IN (?, ?, ?)",
                         (server_key, code_clean, code_raw, code_full))
        await db.commit()

        return {
            "ok": True,
            "server_key": server_key,
            "server_name": server_name,
            "guild_id": gid,
            "linked_by": uid,
            "message": f"Liên kết thành công máy chủ '{server_name}' với Server Discord ID `{gid}`!"
        }


async def direct_link_mc_server_to_guild(server_key: str, guild_id: str | int, user_id: str | int | None = None) -> dict:
    """Nối trực tiếp server MC với guild từ Web Dashboard."""
    gid = str(guild_id)
    uid = str(user_id) if user_id else None
    now = int(time.time())

    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("SELECT server_name FROM mc_servers WHERE server_key = ?", (server_key,)) as cur:
            row = await cur.fetchone()
        if not row:
            server_name = server_key
            await db.execute("""
                INSERT INTO mc_servers (
                    server_key, server_name, guild_id, linked_by, linked_at, status, last_heartbeat
                ) VALUES (?, ?, ?, ?, ?, 'online', ?)
            """, (server_key, server_name, gid, uid, now, now))
        else:
            server_name = row["server_name"]
            await db.execute("""
                UPDATE mc_servers SET
                    guild_id = ?,
                    linked_by = ?,
                    linked_at = ?
                WHERE server_key = ?
            """, (gid, uid, now, server_key))
        await db.commit()

        return {
            "ok": True,
            "server_key": server_key,
            "server_name": server_name,
            "guild_id": gid,
            "message": f"Đã nối máy chủ '{server_name}' với Guild ID `{gid}`!"
        }


async def unlink_mc_server_from_guild(target1: str | int, target2: str | int | None = None) -> dict:
    async with aiosqlite.connect(DB_PATH) as db:
        if target2 is None:
            gid = str(target1)
            await db.execute("""
                UPDATE mc_servers SET
                    guild_id = NULL,
                    linked_by = NULL,
                    linked_at = NULL,
                    chat_channel_id = NULL,
                    log_channel_id = NULL
                WHERE guild_id = ?
            """, (gid,))
        else:
            t1, t2 = str(target1), str(target2)
            await db.execute("""
                UPDATE mc_servers SET
                    guild_id = NULL,
                    linked_by = NULL,
                    linked_at = NULL,
                    chat_channel_id = NULL,
                    log_channel_id = NULL
                WHERE (server_key = ? AND guild_id = ?) OR (server_key = ? AND guild_id = ?)
            """, (t1, t2, t2, t1))
        await db.commit()
    return {"ok": True, "message": "Đã hủy liên kết máy chủ Minecraft khỏi Discord Guild."}


async def update_mc_server_channels(server_key: str, chat_channel_id: str | None = None, log_channel_id: str | None = None) -> bool:
    async with aiosqlite.connect(DB_PATH) as db:
        set_clauses = []
        params = []
        if chat_channel_id is not None:
            set_clauses.append("chat_channel_id = ?")
            params.append(str(chat_channel_id))
        if log_channel_id is not None:
            set_clauses.append("log_channel_id = ?")
            params.append(str(log_channel_id))
        if not set_clauses:
            return True
        params.append(server_key)
        await db.execute(f"UPDATE mc_servers SET {', '.join(set_clauses)} WHERE server_key = ?", tuple(params))
        await db.commit()
        return True


async def queue_mc_command(server_key: str, command: str, executed_by: str = "console", **kwargs) -> int:
    """Đưa lệnh console vào hàng đợi để plugin Minecraft kéo về thực thi."""
    now = time.time()
    cmd_clean = command.strip().lstrip("/")
    issuer = kwargs.get("issued_by", executed_by)
    async with aiosqlite.connect(DB_PATH) as db:
        cur = await db.execute("""
            INSERT INTO mc_pending_commands (server_key, command, executed_by, status, response, created_at)
            VALUES (?, ?, ?, 'pending', '', ?)
        """, (server_key, cmd_clean, issuer, now))
        await db.commit()
        return cur.lastrowid or 0


async def get_pending_mc_commands(server_key: str) -> list[dict]:
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("""
            SELECT id, command, executed_by, created_at
            FROM mc_pending_commands
            WHERE server_key = ? AND status = 'pending'
            ORDER BY id ASC LIMIT 20
        """, (server_key,)) as cur:
            rows = await cur.fetchall()
            return [dict(r) for r in rows]


async def complete_mc_command(cmd_id: int, response: str, status: str = "completed") -> bool:
    now = time.time()
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
            UPDATE mc_pending_commands
            SET status = ?, response = ?, completed_at = ?
            WHERE id = ?
        """, (status, response, now, cmd_id))
        await db.commit()
        return True


async def queue_mc_chat(server_key: str, source: str, sender: str, message: str) -> int:
    """Đưa tin nhắn chat vào hàng đợi (từ Discord -> Minecraft)."""
    now = time.time()
    async with aiosqlite.connect(DB_PATH) as db:
        cur = await db.execute("""
            INSERT INTO mc_chat_queue (server_key, source, sender, message, timestamp, delivered)
            VALUES (?, ?, ?, ?, ?, 0)
        """, (server_key, source, sender, message, now))
        await db.commit()
        return cur.lastrowid or 0


async def get_pending_mc_chats(server_key: str, mark_delivered: bool = True) -> list[dict]:
    """Lấy danh sách tin nhắn chat chờ gửi vào Minecraft."""
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("""
            SELECT id, source, sender, message, timestamp
            FROM mc_chat_queue
            WHERE server_key = ? AND delivered = 0
            ORDER BY id ASC LIMIT 25
        """, (server_key,)) as cur:
            rows = await cur.fetchall()
            res = [dict(r) for r in rows]

        if mark_delivered and res:
            ids = [r["id"] for r in res]
            placeholders = ",".join("?" for _ in ids)
            await db.execute(f"UPDATE mc_chat_queue SET delivered = 1 WHERE id IN ({placeholders})", tuple(ids))
            await db.commit()
        return res


async def link_mc_user(discord_id: str | int, minecraft_uuid: str, minecraft_name: str) -> dict:
    did = str(discord_id)
    uuid_clean = str(minecraft_uuid).strip().lower()
    name_clean = str(minecraft_name).strip()
    now = int(time.time())

    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
            INSERT INTO mc_user_links (discord_id, minecraft_uuid, minecraft_name, linked_at, mc_coins)
            VALUES (?, ?, ?, ?, 0)
            ON CONFLICT(discord_id) DO UPDATE SET
                minecraft_uuid = excluded.minecraft_uuid,
                minecraft_name = excluded.minecraft_name,
                linked_at = excluded.linked_at
        """, (did, uuid_clean, name_clean, now))
        await db.commit()

    return {
        "ok": True,
        "discord_id": did,
        "minecraft_uuid": uuid_clean,
        "minecraft_name": name_clean,
        "linked_at": now
    }


async def get_mc_user_link(discord_id: str | int) -> dict | None:
    did = str(discord_id)
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("SELECT * FROM mc_user_links WHERE discord_id = ?", (did,)) as cur:
            row = await cur.fetchone()
            return dict(row) if row else None


async def unlink_mc_user(discord_id: str | int) -> dict:
    """Hủy liên kết tài khoản Minecraft của người dùng."""
    did = str(discord_id)
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("DELETE FROM mc_user_links WHERE discord_id = ?", (did,))
        await db.commit()
    return {"ok": True, "message": "Đã hủy liên kết tài khoản Minecraft thành công!"}


async def get_mc_user_by_uuid(minecraft_uuid: str) -> dict | None:
    uuid_clean = str(minecraft_uuid).strip().lower()
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("SELECT * FROM mc_user_links WHERE minecraft_uuid = ?", (uuid_clean,)) as cur:
            row = await cur.fetchone()
            return dict(row) if row else None


async def sync_mc_user_coins(discord_id: str | int, action: str, amount: int, from_plugin: bool = False) -> dict:
    """
    Đồng bộ chuyển đổi coins giữa Discord và Minecraft.
    Tỉ lệ: 1 MC Coin = 1,000 Discord Coins (MC_COIN_RATE = 1000).
    - action == 'to_mc': Chuyển Discord coins -> Minecraft (trừ Discord, cộng MC)
    - action == 'to_discord': Chuyển Minecraft coins -> Discord (trừ MC, cộng Discord)
    - action == 'balance': Chỉ kiểm tra số dư cả 2 bên
    - from_plugin == True: Lệnh xuất phát từ Minecraft plugin (tiền in-game Vault là căn cứ thực tế)
    """
    did = str(discord_id)
    user_link = await get_mc_user_link(did)
    if not user_link:
        return {"ok": False, "error": "Tài khoản Discord này chưa được liên kết với nhân vật Minecraft nào!"}

    u_data = await get_user_data(0, int(did))
    discord_coins = int(u_data.get("coins", 0))
    mc_coins = int(user_link.get("mc_coins", 0))

    if action == "balance":
        return {
            "ok": True,
            "discord_id": did,
            "minecraft_name": user_link.get("minecraft_name"),
            "discord_coins": discord_coins,
            "mc_coins": mc_coins,
            "rate": MC_COIN_RATE,
            "info": f"1 MC Coin = {MC_COIN_RATE:,} Discord Coins"
        }

    amount = int(amount)
    if amount <= 0:
        return {"ok": False, "error": "Số lượng coin chuyển đổi phải lớn hơn 0"}

    if action == "to_mc":
        req_discord_coins = amount * MC_COIN_RATE
        if discord_coins < req_discord_coins:
            return {
                "ok": False,
                "error": f"Không đủ Discord Coins! Cần {req_discord_coins:,} coins (Ví hiện có {discord_coins:,} coins) để đổi lấy {amount:,} MC Coins."
            }

        await update_user_coins(0, int(did), -req_discord_coins)
        new_mc_coins = mc_coins + amount
        async with aiosqlite.connect(DB_PATH) as db:
            await db.execute("UPDATE mc_user_links SET mc_coins = ? WHERE discord_id = ?", (new_mc_coins, did))
            await db.commit()

        fresh_u = await get_user_data(0, int(did))
        return {
            "ok": True,
            "message": f"Đã chuyển thành công {req_discord_coins:,} Discord Coins ➔ +{amount:,} Minecraft Coins!",
            "converted_mc": amount,
            "deducted_discord": req_discord_coins,
            "discord_coins": int(fresh_u.get("coins", 0)),
            "mc_coins": new_mc_coins
        }

    elif action == "to_discord":
        if not from_plugin and mc_coins < amount:
            return {
                "ok": False,
                "error": f"Số dư Minecraft Coins không đủ! Hiện có {mc_coins:,} MC coins, yêu cầu rút {amount:,} MC coins."
            }

        added_discord_coins = amount * MC_COIN_RATE
        new_mc_coins = max(0, mc_coins - amount) if mc_coins >= amount else mc_coins
        async with aiosqlite.connect(DB_PATH) as db:
            await db.execute("UPDATE mc_user_links SET mc_coins = ? WHERE discord_id = ?", (new_mc_coins, did))
            await db.commit()

        await update_user_coins(0, int(did), added_discord_coins)
        fresh_u = await get_user_data(0, int(did))
        return {
            "ok": True,
            "message": f"Đã rút thành công {amount:,} Minecraft Coins ➔ +{added_discord_coins:,} Discord Coins vào ví!",
            "withdrawn_mc": amount,
            "added_discord": added_discord_coins,
            "discord_coins": int(fresh_u.get("coins", 0)),
            "mc_coins": new_mc_coins
        }

    return {"ok": False, "error": f"Hành động '{action}' không hợp lệ. Dùng 'to_mc', 'to_discord' hoặc 'balance'."}



async def create_mc_user_link_code(player_name: str, player_uuid: str = "") -> str:
    """Tạo mã liên kết tài khoản người chơi (MC -> Discord) dạng 6 ký tự viết hoa."""
    import secrets
    code = secrets.token_hex(3).upper()
    now = int(time.time())
    expires_at = now + 600

    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
            CREATE TABLE IF NOT EXISTS mc_user_link_codes (
                code TEXT PRIMARY KEY,
                player_uuid TEXT,
                player_name TEXT,
                created_at INTEGER,
                expires_at INTEGER
            )
        """)
        await db.execute("DELETE FROM mc_user_link_codes WHERE expires_at < ?", (now,))
        await db.execute("""
            INSERT INTO mc_user_link_codes (code, player_uuid, player_name, created_at, expires_at)
            VALUES (?, ?, ?, ?, ?)
        """, (code, str(player_uuid).strip().lower(), str(player_name).strip(), now, expires_at))
        await db.commit()

    try:
        from mc_link_system import PENDING_LINKS
        PENDING_LINKS[code] = {
            "minecraft_name": player_name,
            "minecraft_uuid": str(player_uuid).lower() if player_uuid else player_name.lower(),
            "created_at": now,
            "expires_at": expires_at
        }
    except Exception:
        pass

    return code


async def link_mc_user_by_code(code: str, discord_id: str | int) -> dict:
    """Xác thực mã do người chơi nhập trên Discord để hoàn tất liên kết."""
    code_clean = str(code).strip().upper()
    did = str(discord_id)
    now = int(time.time())

    player_name = None
    player_uuid = None

    try:
        from mc_link_system import PENDING_LINKS
        if code_clean in PENDING_LINKS:
            p = PENDING_LINKS.pop(code_clean)
            if now <= p.get("expires_at", 0):
                player_name = p.get("minecraft_name")
                player_uuid = p.get("minecraft_uuid")
    except Exception:
        pass

    if not player_name:
        async with aiosqlite.connect(DB_PATH) as db:
            await db.execute("""
                CREATE TABLE IF NOT EXISTS mc_user_link_codes (
                    code TEXT PRIMARY KEY,
                    player_uuid TEXT,
                    player_name TEXT,
                    created_at INTEGER,
                    expires_at INTEGER
                )
            """)
            db.row_factory = aiosqlite.Row
            async with db.execute("SELECT * FROM mc_user_link_codes WHERE code = ? AND expires_at >= ?", (code_clean, now)) as cur:
                row = await cur.fetchone()
                if row:
                    player_name = row["player_name"]
                    player_uuid = row["player_uuid"]
            if player_name:
                await db.execute("DELETE FROM mc_user_link_codes WHERE code = ?", (code_clean,))
                await db.commit()

    if not player_name:
        return {"ok": False, "error": "Mã liên kết không hợp lệ hoặc đã hết hạn (10 phút)!"}

    if not player_uuid:
        player_uuid = player_name.lower()

    res = await link_mc_user(did, player_uuid, player_name)
    res["player_name"] = player_name
    res["discord_user_id"] = int(did) if did.isdigit() else did
    return res



async def db_get_hoyolab_accounts(user_id: str = None) -> list[dict] | dict[str, list[dict]]:
    """
    Lấy danh sách tài khoản HoYoLAB từ Database.
    Nếu truyền user_id: trả về list[dict] các tài khoản của user đó.
    Nếu không truyền user_id: trả về dict[user_id, list[dict]] toàn bộ hệ thống.
    """
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        if user_id:
            query = "SELECT * FROM hoyolab_accounts WHERE user_id = ?"
            params = (str(user_id),)
        else:
            query = "SELECT * FROM hoyolab_accounts"
            params = ()

        async with db.execute(query, params) as cursor:
            rows = await cursor.fetchall()

    if user_id:
        acc_list = []
        for r in rows:
            try:
                cookies = json.loads(r["cookies_json"]) if r["cookies_json"] else {}
            except Exception:
                cookies = {}
            try:
                game_accounts = json.loads(r["game_accounts_json"]) if r["game_accounts_json"] else []
            except Exception:
                game_accounts = []
            acc_list.append({
                "name": r["account_name"],
                "cookies": cookies,
                "game_accounts": game_accounts,
                "auto_checkin": bool(r["auto_checkin"]),
                "auto_redeem": bool(r["auto_redeem"]),
                "created_at": r["created_at"],
                "updated_at": r["updated_at"]
            })
        return acc_list
    else:
        all_data: dict[str, list[dict]] = {}
        for r in rows:
            uid = str(r["user_id"])
            try:
                cookies = json.loads(r["cookies_json"]) if r["cookies_json"] else {}
            except Exception:
                cookies = {}
            try:
                game_accounts = json.loads(r["game_accounts_json"]) if r["game_accounts_json"] else []
            except Exception:
                game_accounts = []
            item = {
                "name": r["account_name"],
                "cookies": cookies,
                "game_accounts": game_accounts,
                "auto_checkin": bool(r["auto_checkin"]),
                "auto_redeem": bool(r["auto_redeem"]),
                "created_at": r["created_at"],
                "updated_at": r["updated_at"]
            }
            all_data.setdefault(uid, []).append(item)
        return all_data


async def db_save_hoyolab_account(
    user_id: str,
    account_name: str,
    cookies: dict,
    game_accounts: list = None,
    auto_checkin: bool = True,
    auto_redeem: bool = True
) -> bool:
    """Lưu hoặc cập nhật một tài khoản HoYoLAB vào Database SQLite."""
    now_ts = time.time()
    user_id = str(user_id)
    account_name = str(account_name).strip() or "Mặc định"
    game_accounts = game_accounts or []

    ltuid = cookies.get("ltuid_v2") or cookies.get("ltuid") or cookies.get("account_id_v2") or ""
    ltoken = cookies.get("ltoken_v2") or cookies.get("ltoken") or ""
    ctoken = cookies.get("cookie_token_v2") or cookies.get("cookie_token") or ""
    stoken = cookies.get("stoken_v2") or cookies.get("stoken") or ""
    mid = cookies.get("ltmid_v2") or cookies.get("mid") or ""

    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
            INSERT OR REPLACE INTO hoyolab_accounts (
                user_id, account_name, cookies_json, ltuid, ltoken,
                cookie_token, stoken, mid, game_accounts_json,
                auto_checkin, auto_redeem, created_at, updated_at
            ) VALUES (
                ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?,
                COALESCE((SELECT created_at FROM hoyolab_accounts WHERE user_id = ? AND account_name = ?), ?),
                ?
            )
        """, (
            user_id, account_name, json.dumps(cookies, ensure_ascii=False),
            str(ltuid), str(ltoken), str(ctoken), str(stoken), str(mid),
            json.dumps(game_accounts, ensure_ascii=False),
            1 if auto_checkin else 0,
            1 if auto_redeem else 0,
            user_id, account_name, now_ts,
            now_ts
        ))
        await db.commit()
    return True


async def db_delete_hoyolab_account(user_id: str, account_name: str) -> bool:
    """Xóa một tài khoản HoYoLAB khỏi Database SQLite."""
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "DELETE FROM hoyolab_accounts WHERE user_id = ? AND account_name = ?",
            (str(user_id), str(account_name))
        )
        await db.commit()
    return True


async def db_update_hoyolab_toggle(user_id: str, account_name: str, field: str, value: bool) -> bool:
    """Cập nhật bật/tắt auto_checkin hoặc auto_redeem trong Database SQLite."""
    if field not in ("auto_checkin", "auto_redeem"):
        return False
    val_int = 1 if value else 0
    now_ts = time.time()
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            f"UPDATE hoyolab_accounts SET {field} = ?, updated_at = ? WHERE user_id = ? AND account_name = ?",
            (val_int, now_ts, str(user_id), str(account_name))
        )
        await db.commit()
    return True

