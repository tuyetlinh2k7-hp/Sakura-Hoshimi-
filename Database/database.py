import aiosqlite
import os

DB_DIR = "data"
DB_PATH = os.path.join(DB_DIR, "bot.db")

class Database:
    def __init__(self, db_path: str = DB_PATH):
        self.db_path = db_path
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)

    async def init_db(self):
        """Khởi tạo bảng cấu hình autorole"""
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("""
                CREATE TABLE IF NOT EXISTS autorole_config (
                    guild_id INTEGER PRIMARY KEY,
                    user_role_id INTEGER,
                    bot_role_id INTEGER
                )
            """)
            await db.commit()

    async def set_role(self, guild_id: int, target: str, role_id: int | None):
        """Cập nhật role cho User hoặc Bot (dùng UPSERT)"""
        column = "user_role_id" if target == "user" else "bot_role_id"
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(f"""
                INSERT INTO autorole_config (guild_id, {column})
                VALUES (?, ?)
                ON CONFLICT(guild_id) DO UPDATE SET {column} = excluded.{column}
            """, (guild_id, role_id))
            await db.commit()

    async def get_config(self, guild_id: int) -> dict:
        """Lấy cấu hình autorole của một guild"""
        async with aiosqlite.connect(self.db_path) as db:
            async with db.execute(
                "SELECT user_role_id, bot_role_id FROM autorole_config WHERE guild_id = ?",
                (guild_id,)
            ) as cursor:
                row = await cursor.fetchone()
                if row:
                    return {"user": row[0], "bot": row[1]}
        return {"user": None, "bot": None}
