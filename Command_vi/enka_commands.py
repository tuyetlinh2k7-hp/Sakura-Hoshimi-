import discord
from discord.ext import commands
from discord import app_commands
import json
import os
import io
import time
import asyncio
import aiohttp
import aiosqlite
from openai import AsyncOpenAI
from Checks_vi.i18n import t

# --- CẤU HÌNH XKIRO API ---
API_KEY = None
try:
    from config import XKIRO_API_KEY as API_KEY
except ImportError:
    try:
        from config import GEMINI_API_KEY as API_KEY
    except ImportError:
        API_KEY = os.getenv("XKIRO_API_KEY") or os.getenv("GEMINI_API_KEY")

xkiro_client = AsyncOpenAI(
    api_key=API_KEY or "missing-api-key",
    base_url="https://api.xkiro.com/v1",
)

try:
    from config import AI_MODEL
except ImportError:
    AI_MODEL = "sensenova/sensenova-6.8-flash-lite"

try:
    from PIL import Image, ImageDraw, ImageFont
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False

ELEMENT_COLORS = {
    "Anemo": discord.Color.from_rgb(113, 222, 199), "Cryo": discord.Color.from_rgb(153, 221, 255),
    "Dendro": discord.Color.from_rgb(165, 208, 99), "Electro": discord.Color.from_rgb(179, 136, 255),
    "Geo": discord.Color.from_rgb(248, 199, 99), "Hydro": discord.Color.from_rgb(77, 169, 255),
    "Pyro": discord.Color.from_rgb(255, 121, 99), "Default": discord.Color.light_grey()
}
ELEMENT_RGB = {
    "Anemo": (113, 222, 199), "Cryo": (153, 221, 255), "Dendro": (165, 208, 99),
    "Electro": (179, 136, 255), "Geo": (248, 199, 99), "Hydro": (77, 169, 255),
    "Pyro": (255, 121, 99), "Default": (180, 180, 195)
}
ELEMENT_ICONS = {
    "Anemo": "https://enka.network/ui/UI_Icon_Element_Anemo.png", "Cryo": "https://enka.network/ui/UI_Icon_Element_Cryo.png",
    "Dendro": "https://enka.network/ui/UI_Icon_Element_Dendro.png", "Electro": "https://enka.network/ui/UI_Icon_Element_Electro.png",
    "Geo": "https://enka.network/ui/UI_Icon_Element_Geo.png", "Hydro": "https://enka.network/ui/UI_Icon_Element_Hydro.png",
    "Pyro": "https://enka.network/ui/UI_Icon_Element_Pyro.png"
}


# ==========================================
# 1. VIEW CHỌN UID ĐÃ LƯU
# ==========================================
class UIDSelect(discord.ui.Select):
    def __init__(self, cog_instance, command_name: str, original_ctx, saved_uids: dict, extra_arg: str = None):
        self.cog_instance = cog_instance
        self.command_name = command_name
        self.original_ctx = original_ctx
        self.extra_arg = extra_arg

        uid_to_aliases = {}
        for alias, uid in saved_uids.items():
            uid_to_aliases.setdefault(uid, []).append(alias.title())

        guild = original_ctx.guild
        options = [
            discord.SelectOption(
                label=f"{', '.join(aliases)}: {uid}"[:100],
                value=uid,
                description=t(guild, "ENKA_SELECT_UID_DESC", uid=uid)
            )
            for uid, aliases in list(uid_to_aliases.items())[:25]
        ]

        super().__init__(placeholder=t(guild, "ENKA_SELECT_UID_PLACEHOLDER"), options=options)

    async def callback(self, interaction: discord.Interaction):
        if interaction.user.id != self.original_ctx.author.id:
            return await interaction.response.send_message("❌ Đây không phải menu của bạn!", ephemeral=True)

        await interaction.response.defer()
        selected_uid = self.values[0]
        try:
            await interaction.message.delete()
        except discord.HTTPException:
            pass

        if self.command_name == "gi":
            await self.original_ctx.invoke(self.cog_instance.enka_gi, uid_or_alias=selected_uid)
        elif self.command_name == "gi_build":
            args = f"{selected_uid} {self.extra_arg}" if self.extra_arg else selected_uid
            await self.original_ctx.invoke(self.cog_instance.enka_gi_build, full_args=args)
        elif self.command_name == "gi_team":
            await self.original_ctx.invoke(self.cog_instance.enka_gi_team, uid_or_alias=selected_uid)
        elif self.command_name == "hsr":
            await self.original_ctx.invoke(self.cog_instance.enka_hsr, uid_or_alias=selected_uid)
        elif self.command_name == "hsr_build":
            await self.original_ctx.invoke(self.cog_instance.enka_hsr_build, uid_or_alias=selected_uid, character_name=self.extra_arg)
        elif self.command_name == "hsr_team":
            await self.original_ctx.invoke(self.cog_instance.enka_hsr_team, uid_or_alias=selected_uid)
        elif self.command_name == "zzz":
            await self.original_ctx.invoke(self.cog_instance.enka_zzz, uid_or_alias=selected_uid)
        elif self.command_name == "zzz_build":
            await self.original_ctx.invoke(self.cog_instance.enka_zzz_build, uid_or_alias=selected_uid, character_name=self.extra_arg)


# ==========================================
# 2. VIEW ĐIỀU KHIỂN BUILD, SNAPSHOT, AI & ẢNH
# ==========================================
class CharacterSelect(discord.ui.Select):
    def __init__(self, parent_view: "CharacterBuildView"):
        self.parent_view = parent_view
        options = []

        if parent_view.game == "gi":
            char_list = parent_view.api_data.get("avatarInfoList", [])
            for idx, char in enumerate(char_list[:25]):
                char_id = str(char.get("avatarId"))
                c_name = parent_view.cog.char_data.get(char_id, f"Nhân vật {char_id}")
                c_lvl = char.get("propMap", {}).get("4001", {}).get("val", "1")
                cons = len(char.get("talentIdList", []))
                options.append(discord.SelectOption(
                    label=f"{c_name} (Cấp {c_lvl})",
                    description=f"Cung mệnh C{cons}",
                    value=str(idx)
                ))
        else:
            char_list = parent_view.api_data.get("detailInfo", {}).get("avatarDetailList", [])
            for idx, char in enumerate(char_list[:25]):
                c_name = char.get("name", f"Nhân vật #{idx+1}")
                c_lvl = char.get("level", 1)
                rank = char.get("rank", 0)
                options.append(discord.SelectOption(
                    label=f"{c_name} (Cấp {c_lvl})",
                    description=f"Tinh hồn / Rank: {rank}",
                    value=str(idx)
                ))

        super().__init__(
            placeholder="🎭 Chọn nhân vật trong Showcase để xem Build...",
            options=options,
            row=0
        )

    async def callback(self, interaction: discord.Interaction):
        if interaction.user.id != self.parent_view.author_id:
            return await interaction.response.send_message("❌ Chỉ người gọi lệnh mới có thể điều khiển menu này!", ephemeral=True)

        await interaction.response.defer()
        idx = int(self.values[0])
        self.parent_view.current_char_idx = idx
        embed = await self.parent_view.get_current_build_embed()

        self.parent_view.update_buttons_state(is_char_selected=True)
        await interaction.edit_original_response(embed=embed, attachments=[], view=self.parent_view)


class CharacterBuildView(discord.ui.View):
    def __init__(self, cog, author_id: int, uid: str, game: str, api_data: dict, initial_char_idx: int = None, profile_embed: discord.Embed = None):
        super().__init__(timeout=240)
        self.cog = cog
        self.author_id = author_id
        self.uid = uid
        self.game = game
        self.api_data = api_data
        self.current_char_idx = initial_char_idx
        self.profile_embed = profile_embed

        self.ai_button = None
        self.snapshot_button = None
        self.card_button = None
        self.team_button = None

        has_chars = (
            bool(api_data.get("avatarInfoList")) if game == "gi"
            else bool(api_data.get("detailInfo", {}).get("avatarDetailList"))
        )

        if has_chars:
            self.add_item(CharacterSelect(self))
            is_selected = initial_char_idx is not None

            if profile_embed is not None:
                profile_btn = discord.ui.Button(label="📋 Hồ Sơ", style=discord.ButtonStyle.secondary, row=1)
                profile_btn.callback = self.show_profile_callback
                self.add_item(profile_btn)

            self.card_button = discord.ui.Button(
                label="🖼️ Xuất Ảnh Card",
                style=discord.ButtonStyle.success,
                disabled=not is_selected,
                row=1
            )
            self.card_button.callback = self.export_card_callback
            self.add_item(self.card_button)

            if game in ["gi", "hsr"]:
                self.team_button = discord.ui.Button(
                    label="👥 Đội hình AI",
                    style=discord.ButtonStyle.secondary,
                    row=1
                )
                self.team_button.callback = self.ai_team_callback
                self.add_item(self.team_button)

            if game == "gi":
                self.snapshot_button = discord.ui.Button(
                    label="💾 Lưu mốc Build",
                    style=discord.ButtonStyle.secondary,
                    disabled=not is_selected,
                    row=2
                )
                self.snapshot_button.callback = self.save_snapshot_callback
                self.add_item(self.snapshot_button)

                self.ai_button = discord.ui.Button(
                    label="🤖 AI Đánh giá",
                    style=discord.ButtonStyle.primary,
                    disabled=not is_selected,
                    row=2
                )
                self.ai_button.callback = self.ai_review_callback
                self.add_item(self.ai_button)

    def update_buttons_state(self, is_char_selected: bool):
        for btn in [self.ai_button, self.snapshot_button, self.card_button]:
            if btn is not None:
                btn.disabled = not is_char_selected

    async def get_current_build_embed(self) -> discord.Embed:
        if self.game == "gi":
            char_list = self.api_data.get("avatarInfoList", [])
            nickname = self.api_data.get("playerInfo", {}).get("nickname", "Không tên")
            akasha_data = await self.cog._fetch_akasha_ranking(self.uid)
            return await self.cog._create_build_embed(self.uid, nickname, char_list[self.current_char_idx], akasha_data)
        elif self.game == "hsr":
            detail = self.api_data.get("detailInfo", {})
            char_list = detail.get("avatarDetailList", [])
            return self.cog._create_hsr_build_embed(self.uid, detail.get("nickname", "Không tên"), char_list[self.current_char_idx])
        else:
            detail = self.api_data.get("detailInfo", {})
            char_list = detail.get("avatarDetailList", [])
            return self.cog._create_zzz_build_embed(self.uid, detail.get("nickname", "Không tên"), char_list[self.current_char_idx])

    async def show_profile_callback(self, interaction: discord.Interaction):
        if interaction.user.id != self.author_id:
            return await interaction.response.send_message("❌ Đây không phải menu của bạn!", ephemeral=True)
        self.current_char_idx = None
        self.update_buttons_state(is_char_selected=False)
        await interaction.response.edit_message(embed=self.profile_embed, attachments=[], view=self)

    async def save_snapshot_callback(self, interaction: discord.Interaction):
        if interaction.user.id != self.author_id:
            return await interaction.response.send_message("❌ Đây không phải menu của bạn!", ephemeral=True)
        if self.current_char_idx is None:
            return await interaction.response.send_message("⚠️ Vui lòng chọn một nhân vật trước!", ephemeral=True)

        char_data = self.api_data.get("avatarInfoList", [])[self.current_char_idx]
        char_id = str(char_data.get("avatarId"))
        char_name = self.cog.char_data.get(char_id, f"Nhân vật {char_id}")
        await self.cog.save_character_snapshot(self.uid, char_data)

        await interaction.response.send_message(
            f"✅ Đã lưu chỉ số hiện tại của **{char_name}** (UID: `{self.uid}`) vào SQLite để so sánh tăng tiến sức mạnh!",
            ephemeral=True
        )

    async def export_card_callback(self, interaction: discord.Interaction):
        if interaction.user.id != self.author_id:
            return await interaction.response.send_message("❌ Đây không phải menu của bạn!", ephemeral=True)
        if not PIL_AVAILABLE:
            return await interaction.response.send_message("❌ Server chưa cài đặt thư viện `Pillow` (`pip install Pillow`).", ephemeral=True)

        await interaction.response.defer()
        if self.game == "gi":
            char_data = self.api_data.get("avatarInfoList", [])[self.current_char_idx]
            nickname = self.api_data.get("playerInfo", {}).get("nickname", "Không tên")
            akasha_data = await self.cog._fetch_akasha_ranking(self.uid)
            img_buffer = await self.cog.render_gi_build_card(self.uid, nickname, char_data, akasha_data)
        else:
            detail = self.api_data.get("detailInfo", {})
            char_data = detail.get("avatarDetailList", [])[self.current_char_idx]
            nickname = detail.get("nickname", "Không tên")
            img_buffer = await self.cog.render_hsr_zzz_build_card(self.uid, nickname, char_data, self.game)

        if not img_buffer:
            return await interaction.followup.send("❌ Không thể tạo ảnh thẻ nhân vật lúc này.", ephemeral=True)

        file = discord.File(fp=img_buffer, filename=f"build_{self.uid}.png")
        embed = await self.get_current_build_embed()
        embed.set_image(url=f"attachment://build_{self.uid}.png")
        await interaction.edit_original_response(embed=embed, attachments=[file], view=self)

    async def ai_review_callback(self, interaction: discord.Interaction):
        if interaction.user.id != self.author_id:
            return await interaction.response.send_message("❌ Đây không phải menu của bạn!", ephemeral=True)
        if self.current_char_idx is None:
            return await interaction.response.send_message("⚠️ Vui lòng chọn một nhân vật trước!", ephemeral=True)

        await interaction.response.defer()
        char_data = self.api_data.get("avatarInfoList", [])[self.current_char_idx]
        review_embed = await self.cog._generate_ai_review_embed(interaction.guild, self.uid, char_data)
        await interaction.followup.send(embed=review_embed)

    async def ai_team_callback(self, interaction: discord.Interaction):
        if interaction.user.id != self.author_id:
            return await interaction.response.send_message("❌ Đây không phải menu của bạn!", ephemeral=True)

        await interaction.response.defer()
        team_embed = await self.cog._generate_ai_team_embed(interaction.guild, self.uid, self.game, self.api_data)
        await interaction.followup.send(embed=team_embed)


# ==========================================
# 3. COG CHÍNH: ENKA NETWORK (SQLite & AI Team)
# ==========================================
class EnkaCog(commands.Cog, name="Enka Network"):
    def __init__(self, bot):
        self.bot = bot
        self.db_path = "data/enka_data.db"
        self.avatar_file_path = "data/gi_AvatarExcelConfigData.json"
        self.textmap_vi_path = "data/gi_TextMapVI.json"
        self.textmap_en_path = "data/gi_TextMapEN.json"
        self.enka_store_cache_path = "data/enka_loc_vi.json"

        self.asset_data = {}
        self.char_data = {}
        self.session: aiohttp.ClientSession = None

        self.api_cache = {}
        self.akasha_cache = {}
        self.cache_ttl = 300

    async def cog_load(self):
        self.session = aiohttp.ClientSession(headers={"User-Agent": "SakuraBot-EnkaViewer/4.0"})
        await self._init_database()
        await self._migrate_from_json_if_needed()
        await self.load_genshin_char_names()

    async def cog_unload(self):
        if self.session and not self.session.closed:
            await self.session.close()

    # ==========================================
    # CƠ SỞ DỮ LIỆU SQLITE (ASYNC ENGINE)
    # ==========================================
    async def _init_database(self):
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("""
                CREATE TABLE IF NOT EXISTS user_uids (
                    user_id TEXT,
                    game TEXT,
                    alias TEXT,
                    uid TEXT,
                    PRIMARY KEY (user_id, game, alias)
                )
            """)
            await db.execute("""
                CREATE TABLE IF NOT EXISTS build_history (
                    uid TEXT,
                    char_id TEXT,
                    hp INTEGER,
                    atk INTEGER,
                    def INTEGER,
                    em INTEGER,
                    cr REAL,
                    cd REAL,
                    er REAL,
                    cv REAL,
                    timestamp INTEGER,
                    PRIMARY KEY (uid, char_id)
                )
            """)
            await db.commit()

    async def _migrate_from_json_if_needed(self):
        """Tự động chuyển đổi dữ liệu từ các file JSON cũ sang SQLite nếu có."""
        old_uids_path = "data/user_uids.json"
        old_history_path = "data/build_history.json"

        async with aiosqlite.connect(self.db_path) as db:
            # 1. Chuyển UID
            if os.path.exists(old_uids_path):
                try:
                    with open(old_uids_path, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                    for u_id, games in data.items():
                        if isinstance(games, dict):
                            for g, aliases in games.items():
                                if isinstance(aliases, str):
                                    await db.execute(
                                        "INSERT OR REPLACE INTO user_uids VALUES (?, ?, ?, ?)",
                                        (str(u_id), g.lower(), "default", aliases)
                                    )
                                elif isinstance(aliases, dict):
                                    for al, uid_val in aliases.items():
                                        await db.execute(
                                            "INSERT OR REPLACE INTO user_uids VALUES (?, ?, ?, ?)",
                                            (str(u_id), g.lower(), al.lower(), str(uid_val))
                                        )
                    await db.commit()
                    os.rename(old_uids_path, f"{old_uids_path}.migrated")
                    print("✅ Đã chuyển đổi dữ liệu user_uids.json sang SQLite thành công!")
                except Exception as e:
                    print(f"⚠️ Lỗi chuyển đổi user_uids.json: {e}")

            # 2. Chuyển Lịch sử build
            if os.path.exists(old_history_path):
                try:
                    with open(old_history_path, 'r', encoding='utf-8') as f:
                        hist = json.load(f)
                    for uid, chars in hist.items():
                        if isinstance(chars, dict):
                            for char_id, stats in chars.items():
                                await db.execute("""
                                    INSERT OR REPLACE INTO build_history 
                                    (uid, char_id, hp, atk, def, em, cr, cd, er, cv, timestamp)
                                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                                """, (
                                    str(uid), str(char_id),
                                    stats.get('hp', 0), stats.get('atk', 0), stats.get('def', 0),
                                    stats.get('em', 0), stats.get('cr', 0.0), stats.get('cd', 0.0),
                                    stats.get('er', 0.0), stats.get('cv', 0.0),
                                    stats.get('timestamp', int(time.time()))
                                ))
                    await db.commit()
                    os.rename(old_history_path, f"{old_history_path}.migrated")
                    print("✅ Đã chuyển đổi dữ liệu build_history.json sang SQLite thành công!")
                except Exception as e:
                    print(f"⚠️ Lỗi chuyển đổi build_history.json: {e}")

    async def get_user_uids_dict(self, user_id: int, game: str = None) -> dict:
        """Lấy danh sách UID đã lưu của người dùng từ SQLite."""
        async with aiosqlite.connect(self.db_path) as db:
            if game:
                cursor = await db.execute(
                    "SELECT alias, uid FROM user_uids WHERE user_id = ? AND game = ?",
                    (str(user_id), game.lower())
                )
                rows = await cursor.fetchall()
                return {row[0]: row[1] for row in rows}
            else:
                cursor = await db.execute(
                    "SELECT game, alias, uid FROM user_uids WHERE user_id = ?",
                    (str(user_id),)
                )
                rows = await cursor.fetchall()
                result = {}
                for g, al, u in rows:
                    result.setdefault(g, {})[al] = u
                return result

    async def resolve_user_uid(self, user_id: int, game: str, uid_or_alias: str = None) -> str:
        saved = await self.get_user_uids_dict(user_id, game)
        if uid_or_alias:
            if uid_or_alias.isdigit():
                return uid_or_alias
            return saved.get(uid_or_alias.lower())
        if not saved:
            return None
        return saved.get("default") or next(iter(saved.values()), None)

    async def save_user_uid_to_db(self, user_id: int, game: str, alias: str, uid: str):
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(
                "INSERT OR REPLACE INTO user_uids VALUES (?, ?, ?, ?)",
                (str(user_id), game.lower(), alias.lower(), uid)
            )
            await db.commit()

    async def delete_user_uid_from_db(self, user_id: int, game: str, alias: str) -> str:
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute(
                "SELECT uid FROM user_uids WHERE user_id = ? AND game = ? AND alias = ?",
                (str(user_id), game.lower(), alias.lower())
            )
            row = await cursor.fetchone()
            if not row:
                return None
            uid = row[0]
            await db.execute(
                "DELETE FROM user_uids WHERE user_id = ? AND game = ? AND alias = ?",
                (str(user_id), game.lower(), alias.lower())
            )
            await db.commit()
            return uid

    async def get_character_snapshot(self, uid: str, char_id: str) -> dict:
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute(
                "SELECT hp, atk, def, em, cr, cd, er, cv, timestamp FROM build_history WHERE uid = ? AND char_id = ?",
                (str(uid), str(char_id))
            )
            row = await cursor.fetchone()
            if not row:
                return {}
            return {
                "hp": row[0], "atk": row[1], "def": row[2], "em": row[3],
                "cr": row[4], "cd": row[5], "er": row[6], "cv": row[7],
                "timestamp": row[8]
            }

    async def save_character_snapshot(self, uid: str, char_data: dict):
        char_id = str(char_data.get("avatarId"))
        curr = self.extract_current_stats(char_data)
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("""
                INSERT OR REPLACE INTO build_history 
                (uid, char_id, hp, atk, def, em, cr, cd, er, cv, timestamp)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                str(uid), char_id, curr['hp'], curr['atk'], curr['def'], curr['em'],
                curr['cr'], curr['cd'], curr['er'], curr['cv'], curr['timestamp']
            ))
            await db.commit()

    def extract_current_stats(self, char_data: dict) -> dict:
        stats = char_data.get("fightPropMap", {})
        total_cv = 0.0
        for item in char_data.get("equipList", []):
            if "reliquary" in item:
                for sub in item.get("flat", {}).get("reliquarySubstats", []):
                    if sub.get("appendPropId") == "FIGHT_PROP_CRITICAL":
                        total_cv += sub.get("statValue", 0) * 2
                    elif sub.get("appendPropId") == "FIGHT_PROP_CRITICAL_HURT":
                        total_cv += sub.get("statValue", 0)

        return {
            "hp": int(stats.get('2000', 0)),
            "atk": int(stats.get('2001', 0)),
            "def": int(stats.get('2002', 0)),
            "em": int(stats.get('28', 0)),
            "cr": round(stats.get('20', 0) * 100, 1),
            "cd": round(stats.get('22', 0) * 100, 1),
            "er": round(stats.get('23', 0) * 100, 1),
            "cv": round(total_cv, 1),
            "timestamp": int(time.time())
        }

    def _purge_expired_cache(self):
        now = time.time()
        self.api_cache = {k: v for k, v in self.api_cache.items() if now - v[0] < self.cache_ttl}
        self.akasha_cache = {k: v for k, v in self.akasha_cache.items() if now - v[0] < self.cache_ttl}

    async def sync_enka_vietnamese_store(self) -> bool:
        loc_url = "https://raw.githubusercontent.com/EnkaNetwork/API-docs/master/store/loc.json"
        chars_url = "https://raw.githubusercontent.com/EnkaNetwork/API-docs/master/store/characters.json"
        try:
            async with self.session.get(loc_url, timeout=30) as r1, self.session.get(chars_url, timeout=30) as r2:
                if r1.status == 200 and r2.status == 200:
                    loc_all = await r1.json(content_type=None)
                    chars_all = await r2.json(content_type=None)

                    vi_map = loc_all.get("vi") or loc_all.get("en") or {}
                    os.makedirs("data", exist_ok=True)
                    with open(self.enka_store_cache_path, 'w', encoding='utf-8') as f:
                        json.dump({"textmap": vi_map, "characters": chars_all}, f, ensure_ascii=False)

                    self.asset_data.update(vi_map)
                    for c_id, c_info in chars_all.items():
                        name_hash = str(c_info.get("NameTextMapHash", ""))
                        if name_hash in vi_map:
                            self.char_data[str(c_id)] = vi_map[name_hash]
                    return True
        except Exception as e:
            print(f"⚠️ Không thể đồng bộ dữ liệu Enka VI: {e}")
        return False

    async def load_genshin_char_names(self):
        try:
            if os.path.exists(self.enka_store_cache_path):
                with open(self.enka_store_cache_path, 'r', encoding='utf-8') as f:
                    store = json.load(f)
                self.asset_data.update(store.get("textmap", {}))
                for c_id, c_info in store.get("characters", {}).items():
                    h_id = str(c_info.get("NameTextMapHash", ""))
                    if h_id in self.asset_data:
                        self.char_data[str(c_id)] = self.asset_data[h_id]

            active_textmap_path = (
                self.textmap_vi_path if os.path.exists(self.textmap_vi_path)
                else (self.textmap_en_path if os.path.exists(self.textmap_en_path) else None)
            )

            if active_textmap_path and os.path.exists(self.avatar_file_path):
                with open(self.avatar_file_path, 'r', encoding='utf-8') as f:
                    avatar_data = json.load(f)
                with open(active_textmap_path, 'r', encoding='utf-8') as f:
                    text_map = json.load(f)

                items = avatar_data if isinstance(avatar_data, list) else avatar_data.values()
                for item in items:
                    if 'id' in item and 'NameTextMapHash' in item:
                        char_id = str(item['id'])
                        hash_id = str(item['NameTextMapHash'])
                        if char_id not in self.char_data:
                            self.char_data[char_id] = text_map.get(hash_id, f"Nhân vật {char_id}")

                for k, v in text_map.items():
                    self.asset_data.setdefault(k, v)

            if not os.path.exists(self.enka_store_cache_path) and not os.path.exists(self.textmap_vi_path):
                await self.sync_enka_vietnamese_store()

            print(f"✅ Sẵn sàng {len(self.char_data)} nhân vật Genshin Impact!")
        except Exception as e:
            print(f"❌ Lỗi nạp từ điển Genshin: {e}")

    # ==========================================
    # TRUY VẤN API ENKA & AKASHA.CV
    # ==========================================
    async def _fetch_enka_data(self, uid: str, game: str = 'gi', use_cache: bool = True) -> dict:
        self._purge_expired_cache()
        cache_key = (game, uid)
        now = time.time()

        if use_cache and cache_key in self.api_cache:
            ts, cached_data = self.api_cache[cache_key]
            if now - ts < self.cache_ttl:
                return {"data": cached_data, "status": 200, "cached": True}

        if game == 'gi':
            url = f"https://enka.network/api/uid/{uid}"
        elif game == 'hsr':
            url = f"https://enka.network/api/hsr/uid/{uid}"
        elif game == 'zzz':
            url = f"https://enka.network/api/zzz/uid/{uid}"
        else:
            url = f"https://enka.network/api/uid/{uid}"

        try:
            if not self.session or self.session.closed:
                self.session = aiohttp.ClientSession(headers={"User-Agent": "SakuraBot-EnkaViewer/4.0"})
            async with self.session.get(url, timeout=20) as resp:
                data = await resp.json() if resp.status == 200 else None
                if resp.status == 200 and data:
                    self.api_cache[cache_key] = (now, data)
                return {"data": data, "status": resp.status}
        except Exception as e:
            return {"error": str(e), "status": 500}

    async def _fetch_akasha_ranking(self, uid: str) -> dict:
        now = time.time()
        if uid in self.akasha_cache:
            ts, cached_rank = self.akasha_cache[uid]
            if now - ts < self.cache_ttl:
                return cached_rank

        url = f"https://akasha.cv/api/getCalculationsForUser/{uid}"
        rankings = {}
        try:
            async with self.session.get(url, timeout=8) as resp:
                if resp.status == 200:
                    json_data = await resp.json()
                    for item in json_data.get("data", []):
                        char_id = str(item.get("characterId", ""))
                        calcs = item.get("calculations", {})
                        best_pct = 101.0
                        best_info = None
                        for calc_key, calc_val in calcs.items():
                            r = calc_val.get("ranking")
                            out_of = calc_val.get("outOf")
                            if isinstance(r, int) and isinstance(out_of, int) and out_of > 0:
                                pct = (r / out_of) * 100
                                if pct < best_pct:
                                    best_pct = pct
                                    best_info = {
                                        "pct": pct,
                                        "ranking": r,
                                        "outOf": out_of,
                                        "name": calc_val.get("short", calc_val.get("name", "Standard"))
                                    }
                        if best_info:
                            rankings[char_id] = best_info
                    self.akasha_cache[uid] = (now, rankings)
        except Exception:
            pass
        return rankings

    def get_asset_name(self, hash_id: str) -> str:
        return self.asset_data.get(str(hash_id), "Không rõ")

    def get_stat_name(self, stat_key: str) -> str:
        mapping = {
            "FIGHT_PROP_HP": "HP", "FIGHT_PROP_ATTACK": "Tấn công", "FIGHT_PROP_DEFENSE": "Phòng ngự",
            "FIGHT_PROP_HP_PERCENT": "HP%", "FIGHT_PROP_ATTACK_PERCENT": "Tấn công%", "FIGHT_PROP_DEFENSE_PERCENT": "Phòng ngự%",
            "FIGHT_PROP_CRITICAL": "Tỷ lệ BK", "FIGHT_PROP_CRITICAL_HURT": "ST Bạo kích",
            "FIGHT_PROP_CHARGE_EFFICIENCY": "Hiệu quả Nạp", "FIGHT_PROP_HEAL_ADD": "Tăng Trị liệu",
            "FIGHT_PROP_ELEMENT_MASTERY": "Tinh thông NT",
            "FIGHT_PROP_PHYSICAL_ADD_HURT": "ST Vật lý", "FIGHT_PROP_PYRO_ADD_HURT": "ST Hỏa",
            "FIGHT_PROP_HYDRO_ADD_HURT": "ST Thủy", "FIGHT_PROP_ELECTRO_ADD_HURT": "ST Lôi",
            "FIGHT_PROP_ANEMO_ADD_HURT": "ST Phong", "FIGHT_PROP_CRYO_ADD_HURT": "ST Băng",
            "FIGHT_PROP_GEO_ADD_HURT": "ST Nham", "FIGHT_PROP_DENDRO_ADD_HURT": "ST Thảo"
        }
        return mapping.get(stat_key, stat_key)

    @staticmethod
    def _format_diff(curr_val: float, old_val: float, is_percent: bool = False) -> str:
        if old_val is None:
            return ""
        diff = curr_val - old_val
        if abs(diff) < 0.05:
            return ""
        sign = "+" if diff > 0 else ""
        arrow = "⬆️" if diff > 0 else "⬇️"
        if is_percent:
            return f" *({sign}{diff:.1f}% {arrow})*"
        return f" *({sign}{int(diff):,} {arrow})*"

    async def _create_build_embed(self, uid: str, player_nickname: str, char_data: dict, akasha_rankings: dict = None) -> discord.Embed:
        char_id = str(char_data.get("avatarId"))
        char_name = self.char_data.get(char_id, f"Nhân vật {char_id}")
        char_level = char_data.get("propMap", {}).get("4001", {}).get("val", "1")
        constellation = len(char_data.get("talentIdList", []))

        stats = char_data.get("fightPropMap", {})
        element_bonus = {
            "Pyro": stats.get('40', 0), "Electro": stats.get('41', 0), "Hydro": stats.get('42', 0),
            "Dendro": stats.get('43', 0), "Anemo": stats.get('44', 0), "Geo": stats.get('45', 0),
            "Cryo": stats.get('46', 0)
        }
        best_elem = max(element_bonus, key=element_bonus.get)
        element = best_elem if element_bonus[best_elem] > 0 else "Default"

        akasha_line = ""
        if akasha_rankings and char_id in akasha_rankings:
            ak = akasha_rankings[char_id]
            akasha_line = f"\n🏆 **Akasha.cv:** Top **{ak['pct']:.1f}%** (`#{ak['ranking']:,}/{ak['outOf']:,}` • *{ak['name']}*)"

        embed = discord.Embed(
            title=f"BUILD {char_name.upper()}",
            description=f"**Cấp {char_level}/90 | Cung Mệnh C{constellation}**{akasha_line}",
            color=ELEMENT_COLORS.get(element, ELEMENT_COLORS["Default"])
        )
        embed.set_thumbnail(url=f"https://enka.network/ui/UI_AvatarIcon_{char_id}.png")
        embed.set_author(name=f"{player_nickname} (UID: {uid})", icon_url=ELEMENT_ICONS.get(element))

        curr = self.extract_current_stats(char_data)
        old = await self.get_character_snapshot(uid, char_id)

        if not old:
            await self.save_character_snapshot(uid, char_data)

        stats_str = (
            f"❤️ **HP:** `{curr['hp']:,}`{self._format_diff(curr['hp'], old.get('hp'))}\n"
            f"⚔️ **Tấn công:** `{curr['atk']:,}`{self._format_diff(curr['atk'], old.get('atk'))}\n"
            f"🛡️ **Phòng ngự:** `{curr['def']:,}`{self._format_diff(curr['def'], old.get('def'))}\n"
            f"🌿 **Tinh thông:** `{curr['em']}`{self._format_diff(curr['em'], old.get('em'))}\n"
            f"💥 **Tỷ lệ BK:** `{curr['cr']:.1f}%`{self._format_diff(curr['cr'], old.get('cr'), True)}\n"
            f"☠️ **ST Bạo kích:** `{curr['cd']:.1f}%`{self._format_diff(curr['cd'], old.get('cd'), True)}\n"
            f"⚡ **Hiệu quả Nạp:** `{curr['er']:.1f}%`{self._format_diff(curr['er'], old.get('er'), True)}"
        )
        embed.add_field(name="📊 Chỉ số tổng quan", value=stats_str, inline=True)

        weapon = next((item for item in char_data.get("equipList", []) if "weapon" in item), None)
        if weapon:
            weapon_data = weapon.get("flat", {})
            weapon_name = self.get_asset_name(weapon_data.get("nameTextMapHash"))
            weapon_level = weapon.get("weapon", {}).get("level", 1)
            refinement = list(weapon.get("weapon", {}).get("affixMap", {}).values())[0] + 1 if weapon.get("weapon", {}).get("affixMap") else 1
            weapon_str = f"**{weapon_name}**\nTinh luyện `R{refinement}` • Cấp `{weapon_level}`"
            embed.add_field(name="⚔️ Vũ khí", value=weapon_str, inline=True)

        artifacts = [item for item in char_data.get("equipList", []) if "reliquary" in item]
        artifacts_lines = []
        set_counts = {}

        for art in artifacts:
            art_data = art.get("flat", {})
            art_name = self.get_asset_name(art_data.get("nameTextMapHash"))
            set_name = self.get_asset_name(art_data.get("setNameTextMapHash"))
            if set_name != "Không rõ":
                set_counts[set_name] = set_counts.get(set_name, 0) + 1

            main_stat_key = art_data.get("reliquaryMainstat", {}).get("mainPropId", "")
            main_stat_name = self.get_stat_name(main_stat_key)

            sub_cv = 0.0
            for sub in art_data.get("reliquarySubstats", []):
                if sub.get("appendPropId") == "FIGHT_PROP_CRITICAL":
                    sub_cv += sub.get("statValue", 0) * 2
                elif sub.get("appendPropId") == "FIGHT_PROP_CRITICAL_HURT":
                    sub_cv += sub.get("statValue", 0)
            cv_tag = f" `(CV: {sub_cv:.1f})`" if sub_cv > 0 else ""
            artifacts_lines.append(f"• **{art_name}**: {main_stat_name}{cv_tag}")

        cv_diff = self._format_diff(curr['cv'], old.get('cv'), True)
        art_field_title = f"💎 Thánh Di Vật (Tổng CV: {curr['cv']:.1f}{cv_diff})" if curr['cv'] > 0 else "💎 Thánh Di Vật"
        embed.add_field(
            name=art_field_title,
            value="\n".join(artifacts_lines) if artifacts_lines else "Chưa trang bị.",
            inline=False
        )

        active_sets = [f"• **Bộ {count >= 4 and 4 or 2} món:** {s_name}" for s_name, count in set_counts.items() if count >= 2]
        if active_sets:
            embed.add_field(name="✨ Kích hoạt Bộ", value="\n".join(active_sets), inline=False)

        embed.set_footer(text="Dữ liệu Enka & Akasha • Lưu SQLite • Bấm [🖼️ Xuất Ảnh Card] để lưu", icon_url="https://enka.network/favicon.ico")
        return embed

    def _create_hsr_build_embed(self, uid: str, player_nickname: str, char_data: dict) -> discord.Embed:
        char_name = char_data.get("name", "Không rõ")
        char_level = char_data.get("level", 1)
        char_promotion = char_data.get("promotion", 0)
        char_rank = char_data.get("rank", 0)
        element = char_data.get("element", {}).get("name", "Default")

        embed = discord.Embed(
            title=f"BUILD {char_name.upper()}",
            description=f"**Cấp {char_level}/{20 + char_promotion*10} | Tinh hồn E{char_rank}**",
            color=ELEMENT_COLORS.get(element, ELEMENT_COLORS["Default"])
        )
        if "icon" in char_data:
            embed.set_thumbnail(url=f"https://enka.network/{char_data['icon']}")
        elem_icon = char_data.get('element', {}).get('icon', '')
        embed.set_author(
            name=f"{player_nickname} (UID: {uid})",
            icon_url=f"https://enka.network/{elem_icon}" if elem_icon else None
        )

        stats_str = ""
        for stat in char_data.get("attributes", []):
            name = stat.get("name", "")
            value = stat.get("value", 0)
            display = stat.get("display", f"{value:.1f}")
            if stat.get("percent", False) and not str(display).endswith("%"):
                display = f"{display}%"
            stats_str += f"• **{name}:** `{display}`\n"
        embed.add_field(name="📊 Chỉ số", value=stats_str or "Không có dữ liệu.", inline=True)

        light_cone = char_data.get("lightCone")
        if light_cone:
            lc_name = light_cone.get("name", "Không rõ")
            lc_level = light_cone.get("level", 1)
            lc_promotion = light_cone.get("promotion", 0)
            lc_rank = light_cone.get("rank", 1)
            lc_str = f"**{lc_name}**\nTích tầng `S{lc_rank}` • Cấp `{lc_level}/{20 + lc_promotion*10}`"
            embed.add_field(name="💡 Nón Ánh Sáng", value=lc_str, inline=True)

        relics_str = ""
        relic_sets = {}
        for relic in char_data.get("relics", []):
            relic_name = relic.get("name", "Không rõ")
            main_stat = relic.get("mainStat", {}).get("name", "")
            relics_str += f"• **{relic_name}**: {main_stat}\n"
            set_name = relic.get("relicSet", {}).get("name", "Không rõ")
            relic_sets[set_name] = relic_sets.get(set_name, 0) + 1

        embed.add_field(name="💎 Di Vật", value=relics_str or "Chưa trang bị.", inline=False)

        set_str = "\n".join([f"• **{count} món:** {s_name}" for s_name, count in relic_sets.items() if count >= 2])
        if set_str:
            embed.add_field(name="⚙️ Kích hoạt Bộ", value=set_str, inline=False)

        embed.set_footer(text="Dữ liệu cung cấp bởi Enka.Network", icon_url="https://enka.network/favicon.ico")
        return embed

    def _create_zzz_build_embed(self, uid: str, player_nickname: str, char_data: dict) -> discord.Embed:
        char_name = char_data.get("name", "Không rõ")
        char_level = char_data.get("level", 1)
        char_promotion = char_data.get("promotion", 0)
        char_rank = char_data.get("rank", 0)
        element = char_data.get("element", {}).get("name", "Default")

        embed = discord.Embed(
            title=f"BUILD {char_name.upper()}",
            description=f"**Cấp {char_level}/{20 + char_promotion*10} | Mindscape M{char_rank}**",
            color=ELEMENT_COLORS.get(element, ELEMENT_COLORS["Default"])
        )
        if "icon" in char_data:
            embed.set_thumbnail(url=f"https://enka.network/{char_data['icon']}")
        elem_icon = char_data.get('element', {}).get('icon', '')
        embed.set_author(
            name=f"{player_nickname} (UID: {uid})",
            icon_url=f"https://enka.network/{elem_icon}" if elem_icon else None
        )

        stats_str = ""
        for stat in char_data.get("attributes", []):
            name = stat.get("name", "")
            display = stat.get("display", "0")
            if stat.get("percent", False) and not str(display).endswith("%"):
                display = f"{display}%"
            stats_str += f"• **{name}:** `{display}`\n"
        embed.add_field(name="📊 Chỉ số", value=stats_str or "Không có dữ liệu.", inline=True)

        w_engine = char_data.get("lightCone")
        if w_engine:
            engine_name = w_engine.get("name", "Không rõ")
            engine_level = w_engine.get("level", 1)
            engine_promotion = w_engine.get("promotion", 0)
            engine_rank = w_engine.get("rank", 1)
            engine_str = f"**{engine_name}**\nRank `W{engine_rank}` • Cấp `{engine_level}/{20 + engine_promotion*10}`"
            embed.add_field(name="⚙️ W-Engine", value=engine_str, inline=True)

        disks_str = ""
        disk_sets = {}
        for disk in char_data.get("relics", []):
            disk_name = disk.get("name", "Không rõ")
            main_stat = disk.get("mainStat", {}).get("name", "")
            disks_str += f"• **{disk_name}**: {main_stat}\n"
            set_name = disk.get("relicSet", {}).get("name", "Không rõ")
            disk_sets[set_name] = disk_sets.get(set_name, 0) + 1

        embed.add_field(name="💿 Disk Drives", value=disks_str or "Chưa trang bị.", inline=False)

        set_str = "\n".join([f"• **{count}-Set:** {s_name}" for s_name, count in disk_sets.items() if count >= 2])
        if set_str:
            embed.add_field(name="💾 Kích hoạt Bộ", value=set_str, inline=False)

        embed.set_footer(text="Dữ liệu cung cấp bởi Enka.Network", icon_url="https://enka.network/favicon.ico")
        return embed

    # ==========================================
    # 4. HỆ THỐNG RENDER ẢNH BUILD CARD (PILLOW)
    # ==========================================
    async def _download_image_bytes(self, url: str) -> bytes:
        try:
            async with self.session.get(url, timeout=10) as resp:
                if resp.status == 200:
                    return await resp.read()
        except Exception:
            pass
        return None

    def _get_font(self, size: int):
        font_candidates = [
            "arial.ttf", "segoeui.ttf", "tahoma.ttf",
            "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
            "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf"
        ]
        for path in font_candidates:
            try:
                return ImageFont.truetype(path, size)
            except Exception:
                continue
        return ImageFont.load_default()

    async def render_gi_build_card(self, uid: str, nickname: str, char_data: dict, akasha_rankings: dict = None) -> io.BytesIO:
        char_id = str(char_data.get("avatarId"))
        char_name = self.char_data.get(char_id, f"Nhân vật {char_id}")
        char_level = char_data.get("propMap", {}).get("4001", {}).get("val", "1")
        cons = len(char_data.get("talentIdList", []))
        curr = self.extract_current_stats(char_data)

        stats = char_data.get("fightPropMap", {})
        element_bonus = {
            "Pyro": stats.get('40', 0), "Electro": stats.get('41', 0), "Hydro": stats.get('42', 0),
            "Dendro": stats.get('43', 0), "Anemo": stats.get('44', 0), "Geo": stats.get('45', 0),
            "Cryo": stats.get('46', 0)
        }
        best_elem = max(element_bonus, key=element_bonus.get)
        accent_rgb = ELEMENT_RGB.get(best_elem if element_bonus[best_elem] > 0 else "Default")

        avatar_bytes = await self._download_image_bytes(f"https://enka.network/ui/UI_AvatarIcon_{char_id}.png")

        weapon = next((item for item in char_data.get("equipList", []) if "weapon" in item), None)
        w_name = self.get_asset_name(weapon.get("flat", {}).get("nameTextMapHash")) if weapon else "Chưa trang bị"
        w_lvl = weapon.get("weapon", {}).get("level", 1) if weapon else 1
        w_ref = (list(weapon.get("weapon", {}).get("affixMap", {}).values())[0] + 1) if (weapon and weapon.get("weapon", {}).get("affixMap")) else 1

        ak_text = "Chưa có xếp hạng Akasha"
        if akasha_rankings and char_id in akasha_rankings:
            ak = akasha_rankings[char_id]
            ak_text = f"Akasha Top {ak['pct']:.1f}% (#{ak['ranking']:,}/{ak['outOf']:,})"

        def _draw():
            img = Image.new("RGBA", (900, 480), (22, 24, 34, 255))
            draw = ImageDraw.Draw(img)

            draw.rectangle([0, 0, 900, 8], fill=accent_rgb)
            draw.rounded_rectangle([20, 25, 290, 455], radius=16, fill=(32, 35, 48, 255), outline=accent_rgb, width=2)
            draw.rounded_rectangle([310, 25, 880, 235], radius=16, fill=(32, 35, 48, 255))
            draw.rounded_rectangle([310, 255, 880, 455], radius=16, fill=(32, 35, 48, 255))

            f_title = self._get_font(26)
            f_sub = self._get_font(18)
            f_stat = self._get_font(20)

            if avatar_bytes:
                try:
                    av_img = Image.open(io.BytesIO(avatar_bytes)).convert("RGBA").resize((180, 180))
                    img.paste(av_img, (65, 45), av_img)
                except Exception:
                    pass

            draw.text((40, 240), char_name[:18], fill=accent_rgb, font=f_title)
            draw.text((40, 280), f"Cấp {char_level}/90  •  Cung mệnh C{cons}", fill=(230, 230, 240), font=f_sub)
            draw.text((40, 315), f"Người chơi: {nickname}", fill=(180, 185, 200), font=f_sub)
            draw.text((40, 345), f"UID: {uid}", fill=(150, 155, 175), font=f_sub)
            draw.text((40, 395), ak_text, fill=(255, 215, 100), font=f_sub)

            draw.text((335, 40), "CHỈ SỐ NHÂN VẬT", fill=accent_rgb, font=f_sub)
            left_stats = [
                f"HP: {curr['hp']:,}",
                f"Tấn công: {curr['atk']:,}",
                f"Phòng ngự: {curr['def']:,}",
                f"Tinh thông NT: {curr['em']}"
            ]
            right_stats = [
                f"Tỷ lệ Bạo kích: {curr['cr']:.1f}%",
                f"ST Bạo kích: {curr['cd']:.1f}%",
                f"Hiệu quả Nạp: {curr['er']:.1f}%",
                f"Tổng điểm CV: {curr['cv']:.1f}"
            ]
            for i, s_line in enumerate(left_stats):
                draw.text((335, 75 + i * 36), s_line, fill=(240, 240, 245), font=f_stat)
            for i, s_line in enumerate(right_stats):
                draw.text((600, 75 + i * 36), s_line, fill=(240, 240, 245), font=f_stat)

            draw.text((335, 270), f"VŨ KHÍ: {w_name} (R{w_ref} • Cấp {w_lvl})", fill=accent_rgb, font=f_sub)
            artifacts = [item for item in char_data.get("equipList", []) if "reliquary" in item]
            for idx, art in enumerate(artifacts[:5]):
                a_data = art.get("flat", {})
                a_name = self.get_asset_name(a_data.get("nameTextMapHash"))[:22]
                m_name = self.get_stat_name(a_data.get("reliquaryMainstat", {}).get("mainPropId", ""))
                sub_cv = sum(
                    (s.get("statValue", 0) * 2 if s.get("appendPropId") == "FIGHT_PROP_CRITICAL" else s.get("statValue", 0))
                    for s in a_data.get("reliquarySubstats", [])
                    if s.get("appendPropId") in ("FIGHT_PROP_CRITICAL", "FIGHT_PROP_CRITICAL_HURT")
                )
                y_pos = 310 + (idx % 3) * 40
                x_pos = 335 if idx < 3 else 610
                draw.text((x_pos, y_pos), f"• {a_name}: {m_name} ({sub_cv:.1f} CV)", fill=(215, 220, 230), font=self._get_font(16))

            buf = io.BytesIO()
            img.save(buf, format="PNG")
            buf.seek(0)
            return buf

        return await asyncio.to_thread(_draw)

    async def render_hsr_zzz_build_card(self, uid: str, nickname: str, char_data: dict, game: str) -> io.BytesIO:
        char_name = char_data.get("name", "Không rõ")
        char_level = char_data.get("level", 1)
        char_rank = char_data.get("rank", 0)
        element = char_data.get("element", {}).get("name", "Default")
        accent_rgb = ELEMENT_RGB.get(element, ELEMENT_RGB["Default"])

        icon_path = char_data.get("icon", "")
        avatar_bytes = await self._download_image_bytes(f"https://enka.network/{icon_path}") if icon_path else None

        def _draw():
            img = Image.new("RGBA", (900, 460), (22, 24, 34, 255))
            draw = ImageDraw.Draw(img)

            draw.rectangle([0, 0, 900, 8], fill=accent_rgb)
            draw.rounded_rectangle([20, 25, 290, 435], radius=16, fill=(32, 35, 48, 255), outline=accent_rgb, width=2)
            draw.rounded_rectangle([310, 25, 880, 435], radius=16, fill=(32, 35, 48, 255))

            f_title = self._get_font(26)
            f_sub = self._get_font(18)
            f_stat = self._get_font(19)

            if avatar_bytes:
                try:
                    av_img = Image.open(io.BytesIO(avatar_bytes)).convert("RGBA").resize((180, 180))
                    img.paste(av_img, (65, 45), av_img)
                except Exception:
                    pass

            rank_label = f"Tinh hồn E{char_rank}" if game == "hsr" else f"Mindscape M{char_rank}"
            draw.text((40, 245), char_name[:18], fill=accent_rgb, font=f_title)
            draw.text((40, 285), f"Cấp {char_level}  •  {rank_label}", fill=(230, 230, 240), font=f_sub)
            draw.text((40, 325), f"Người chơi: {nickname}", fill=(180, 185, 200), font=f_sub)
            draw.text((40, 360), f"UID: {uid} ({game.upper()})", fill=(150, 155, 175), font=f_sub)

            draw.text((335, 45), "CHỈ SỐ & TRANG BỊ", fill=accent_rgb, font=f_sub)
            attrs = char_data.get("attributes", [])[:8]
            for i, stat in enumerate(attrs):
                s_name = stat.get("name", "")
                disp = str(stat.get("display", "0"))
                if stat.get("percent", False) and not disp.endswith("%"):
                    disp += "%"
                col_x = 335 if i < 4 else 610
                row_y = 85 + (i % 4) * 42
                draw.text((col_x, row_y), f"• {s_name}: {disp}", fill=(240, 240, 245), font=f_stat)

            lc = char_data.get("lightCone")
            if lc:
                lc_title = "NÓN ÁNH SÁNG" if game == "hsr" else "W-ENGINE"
                draw.text((335, 280), f"{lc_title}: {lc.get('name', 'Không rõ')} (Rank {lc.get('rank', 1)} • Cấp {lc.get('level', 1)})", fill=accent_rgb, font=f_sub)

            buf = io.BytesIO()
            img.save(buf, format="PNG")
            buf.seek(0)
            return buf

        return await asyncio.to_thread(_draw)

    # ==========================================
    # 5. AI ĐÁNH GIÁ BUILD & ĐỘI HÌNH (XKIRO - MISTRAL LARGE 4.0)
    # ==========================================
    def _detect_guild_language(self, guild: discord.Guild) -> str:
        if guild:
            loc = str(guild.preferred_locale).lower()
            if "vi" in loc:
                return "vi"
            elif "ja" in loc:
                return "ja"
            elif "ko" in loc:
                return "ko"
            elif "zh" in loc:
                return "zh"
            elif "en" in loc:
                return "en"
        return "vi"

    async def _execute_ai_call(self, system_instruction: str, user_content: str, max_tokens: int = 800) -> str:
        """Thực thi gọi model mistralai/mistral-large-4-0 qua xKiro API kèm cơ chế retry."""
        last_error = None
        for attempt in range(3):
            try:
                resp = await xkiro_client.chat.completions.create(
                    model=AI_MODEL,
                    messages=[
                        {"role": "system", "content": system_instruction},
                        {"role": "user", "content": user_content}
                    ],
                    max_tokens=max_tokens,
                    temperature=0.6
                )
                if resp.choices and resp.choices[0].message.content:
                    return resp.choices[0].message.content.strip()
                return "..."
            except Exception as e:
                last_error = e
                error_str = str(e).lower()
                status_code = getattr(e, "status_code", None)
                if status_code in (429, 500, 502, 503, 504) or "429" in error_str or "503" in error_str:
                    if attempt < 2:
                        await asyncio.sleep(1.5 * (attempt + 1))
                        continue
                raise e
        if last_error is not None:
            raise last_error
        raise RuntimeError("Không thể nhận phản hồi từ AI sau nhiều lần thử.")

    async def _generate_ai_review_embed(self, guild, uid: str, target_char_data: dict) -> discord.Embed:
        char_id = str(target_char_data.get("avatarId"))
        char_name = self.char_data.get(char_id, "Không rõ")
        curr = self.extract_current_stats(target_char_data)
        constellation = len(target_char_data.get("talentIdList", []))

        weapon = next((item for item in target_char_data.get("equipList", []) if "weapon" in item), None)
        weapon_name = self.get_asset_name(weapon.get("flat", {}).get("nameTextMapHash")) if weapon else "Không rõ"

        lang_code = self._detect_guild_language(guild)
        lang_prompt_guide = {
            "vi": "Hãy phân tích bằng Tiếng Việt thân thiện, súc tích và sử dụng các thuật ngữ Genshin quen thuộc.",
            "en": "Please analyze and review in English with a friendly, concise tone and standard Genshin Impact terminology.",
            "ja": "日本語で親しみやすく簡潔に分析し、原神の標準的な用語を使用してください。",
            "zh": "请用中文以亲切、简练的语气进行分析，并使用标准原神游戏术语。",
            "ko": "친근하고 간결한 어조로 표준 원신 용어를 사용하여 한국어로 분석해 주세요."
        }.get(lang_code, "Hãy phân tích bằng ngôn ngữ phù hợp với máy chủ.")

        system_instruction = f"You are a Genshin Impact character theorycrafter and build expert. {lang_prompt_guide}"
        user_content = (
            f"Analyze and review the following Genshin Impact build:\n"
            f"- Character: {char_name} (Constellation C{constellation})\n"
            f"- Weapon: {weapon_name}\n"
            f"- Stats: HP {curr['hp']:,} | ATK {curr['atk']:,} | DEF {curr['def']:,}\n"
            f"- Crit: CR {curr['cr']:.1f}% | CD {curr['cd']:.1f}% (Artifacts Total CV: {curr['cv']:.1f})\n"
            f"- ER: {curr['er']:.1f}% | EM: {curr['em']}\n\n"
            f"Provide an overall tier rank (S, A, B, C), key strengths, weaknesses, and concise recommendations."
        )

        try:
            ai_comment = await self._execute_ai_call(system_instruction, user_content, max_tokens=700)
        except Exception as e:
            ai_comment = t(guild, "ENKA_AI_ERROR", error=e)

        embed = discord.Embed(
            title=t(guild, "ENKA_AI_TITLE", name=char_name, uid=uid),
            description=ai_comment,
            color=discord.Color.purple()
        )
        embed.set_footer(text=f"AI Build Reviewer • xKiro ({AI_MODEL})")
        return embed

    async def _generate_ai_team_embed(self, guild, uid: str, game: str, api_data: dict) -> discord.Embed:
        """AI Phân tích toàn bộ Showcase và đề xuất đội hình La Hoàn/MoC tối ưu."""
        lang_code = self._detect_guild_language(guild)
        lang_prompt_guide = {
            "vi": "Hãy đề xuất và phân tích bằng Tiếng Việt súc tích, chuyên nghiệp, nêu rõ combo rotation và phản ứng nguyên tố.",
            "en": "Please recommend and analyze in English with a concise, professional tone, explaining combos, rotations, and synergies.",
            "ja": "日本語で簡潔かつプロフェッショナルに推奨編成とローテーションを解説してください。",
            "zh": "请用中文简明专业地推荐队伍配置，并说明输出手法与元素反应协同。",
            "ko": "한국어로 간결하고 전문적으로 추천 파티 구성과 로테이션을 분석해 주세요."
        }.get(lang_code, "Phân tích bằng ngôn ngữ thích hợp.")

        if game == "gi":
            characters = []
            for c in api_data.get("avatarInfoList", []):
                cid = str(c.get("avatarId"))
                c_name = self.char_data.get(cid, f"ID_{cid}")
                c_lvl = c.get("propMap", {}).get("4001", {}).get("val", "1")
                cons = len(c.get("talentIdList", []))
                wp = next((item for item in c.get("equipList", []) if "weapon" in item), None)
                w_name = self.get_asset_name(wp.get("flat", {}).get("nameTextMapHash")) if wp else "Không rõ"
                characters.append(f"• {c_name} (Lv.{c_lvl}, C{cons}, VK: {w_name})")

            chars_text = "\n".join(characters)
            game_title = "Genshin Impact (La Hoàn Thâm Cảnh)"
            system_instruction = f"You are an elite theorycrafter for Genshin Impact endgame content. {lang_prompt_guide}"
            user_content = (
                f"Dưới đây là danh sách toàn bộ các nhân vật đang có trong Showcase (UID: {uid}):\n{chars_text}\n\n"
                f"Yêu cầu:\n"
                f"1. Ghép 1 đến 2 đội hình tối ưu nhất để vượt La Hoàn Thâm Cảnh (Spiral Abyss).\n"
                f"2. Nêu rõ vai trò của từng nhân vật (Main DPS, Sub-DPS, Support, Healer/Shielder).\n"
                f"3. Phân tích synergy nổi bật (Phản ứng nguyên tố, buff tương tác) và tóm tắt vòng quay kỹ năng (Rotation).\n"
                f"4. Gợi ý 1 nhân vật nên ưu tiên cải thiện trang bị trước."
            )
        else:
            characters = []
            detail = api_data.get("detailInfo", {})
            for c in detail.get("avatarDetailList", []):
                c_name = c.get("name", "Không rõ")
                c_lvl = c.get("level", 1)
                rank = c.get("rank", 0)
                lc = c.get("lightCone", {}).get("name", "Không rõ")
                characters.append(f"• {c_name} (Lv.{c_lvl}, E{rank}, Nón: {lc})")

            chars_text = "\n".join(characters)
            game_title = "Honkai: Star Rail (Sảnh Đường Hỗn Độn & Kể Chuyện)"
            system_instruction = f"You are an elite theorycrafter for Honkai: Star Rail endgame content. {lang_prompt_guide}"
            user_content = (
                f"Dưới đây là danh sách toàn bộ nhân vật trong Showcase HSR (UID: {uid}):\n{chars_text}\n\n"
                f"Yêu cầu:\n"
                f"1. Ghép đội hình vượt MoC / Kể chuyện hư cấu mạnh nhất từ dàn nhân vật trên.\n"
                f"2. Phân tích điểm chiến kỹ (SP economy), thứ tự hành động (Speed tuning).\n"
                f"3. Lời khuyên tối ưu hóa ngắn gọn."
            )

        try:
            ai_comment = await self._execute_ai_call(system_instruction, user_content, max_tokens=1000)
        except Exception as e:
            ai_comment = f"❌ Không thể phân tích đội hình lúc này: {e}"

        embed = discord.Embed(
            title=f"👥 CHIẾN THUẬT ĐỘI HÌNH AI — {game_title}",
            description=ai_comment[:4000],
            color=discord.Color.gold()
        )
        embed.set_author(name=f"UID: {uid}")
        embed.set_footer(text=f"AI Team Synergy Engine • xKiro ({AI_MODEL})")
        return embed

    # ==========================================
    # CÁC HÀM LẤY PROFILE (TRẢ VỀ EMBED + DATA)
    # ==========================================
    async def get_gi_profile_with_data(self, uid: str):
        response = await self._fetch_enka_data(uid, 'gi')
        data = response.get("data")
        status = response.get("status")

        if status != 200 or not data:
            return f"❌ Lỗi API Enka (Mã: {status}). Có thể UID không tồn tại hoặc đang bảo trì.", None

        player_info = data.get("playerInfo", {})
        if not player_info:
            return "❌ UID này đang ẩn thông tin hoặc không có dữ liệu hiển thị.", None

        nickname = player_info.get("nickname", "Không tên")
        level = player_info.get("level", 0)
        world_level = player_info.get("worldLevel", 0)
        signature = player_info.get("signature", "*Không có chữ ký*")
        achievements = player_info.get("finishAchievementNum", 0)
        abyss_floor = player_info.get("towerFloorIndex", 0)
        abyss_level = player_info.get("towerLevelIndex", 0)
        total_characters = len(player_info.get("avatarIdList", [])) or "Ẩn"

        showcase_characters = player_info.get("showAvatarInfoList", [])
        if showcase_characters:
            lines = []
            for c in showcase_characters:
                c_id = str(c.get("avatarId", ""))
                c_name = self.char_data.get(c_id, f"Nhân vật {c_id}")
                c_level = c.get("level", 1)
                lines.append(f"• **{c_name}** (Cấp {c_level})")
            showcase_str = "\n".join(lines)
        else:
            showcase_str = "*Không có nhân vật nào được trưng bày.*"

        embed = discord.Embed(
            title=f"🌟 HỒ SƠ GENSHIN IMPACT — {nickname}",
            description=f"**UID:** `{uid}` | **Số nhân vật sở hữu:** `{total_characters}`",
            color=discord.Color.from_rgb(255, 182, 193)
        )
        profile_picture = player_info.get("profilePicture", {})
        if "avatarId" in profile_picture:
            embed.set_thumbnail(url=f"https://enka.network/ui/UI_AvatarIcon_{profile_picture['avatarId']}.png")

        embed.add_field(name="📊 Hạng mạo hiểm", value=f"Cấp `{level}` (TG {world_level})", inline=True)
        embed.add_field(name="🏆 Thành tựu đạt được", value=f"`{achievements}`", inline=True)
        embed.add_field(name="⚔️ La Hoàn Thâm Cảnh", value=f"Tầng {abyss_floor} - Phòng {abyss_level}", inline=True)
        embed.add_field(name="✍️ Chữ ký", value=f"*{signature}*", inline=False)
        embed.add_field(name="🎭 Nhân vật trưng bày", value=showcase_str, inline=False)
        embed.set_footer(text="Enka & Akasha • SQLite Database Engine", icon_url="https://enka.network/favicon.ico")
        return embed, data

    async def get_hsr_profile_with_data(self, uid: str):
        response = await self._fetch_enka_data(uid, 'hsr')
        data = response.get("data")
        status = response.get("status")

        if status != 200 or not data:
            return f"❌ Lỗi API Enka (Mã: {status}). Có thể UID không tồn tại hoặc đang bảo trì.", None

        player_info = data.get("detailInfo", {})
        if not player_info:
            return "❌ UID này đang ẩn thông tin hoặc không có dữ liệu hiển thị.", None

        nickname = player_info.get("nickname", "Không tên")
        level = player_info.get("level", 0)
        equilibrium_level = player_info.get("worldLevel", 0)
        signature = player_info.get("signature", "*Không có chữ ký*")
        achievements = player_info.get("recordInfo", {}).get("achievementCount", 0)
        avatar_count = player_info.get("recordInfo", {}).get("avatarCount", 0)

        embed = discord.Embed(
            title=f"🚂 HỒ SƠ STAR RAIL — {nickname}",
            description=f"**UID:** `{uid}`",
            color=discord.Color.from_rgb(200, 150, 255)
        )
        embed.add_field(name="🚀 Cấp Khai Phá", value=f"`{level}` (Cân bằng {equilibrium_level})", inline=True)
        embed.add_field(name="🏆 Thành tựu", value=f"`{achievements}`", inline=True)
        embed.add_field(name="👥 Số nhân vật", value=f"`{avatar_count}`", inline=True)
        embed.add_field(name="✍️ Chữ ký", value=f"*{signature}*", inline=False)

        showcase_characters = player_info.get("avatarDetailList", [])
        if showcase_characters:
            showcase_str = "\n".join([f"• **{c.get('name', 'Không rõ')}** (Cấp {c.get('level', 1)})" for c in showcase_characters[:8]])
        else:
            showcase_str = "*Không có nhân vật nào được trưng bày.*"

        embed.add_field(name="🎭 Nhân vật trưng bày", value=showcase_str, inline=False)
        embed.set_footer(text="Dữ liệu cung cấp bởi Enka.Network", icon_url="https://enka.network/favicon.ico")
        return embed, data

    async def get_zzz_profile_with_data(self, uid: str):
        response = await self._fetch_enka_data(uid, 'zzz')
        data = response.get("data")
        status = response.get("status")

        if status != 200 or not data:
            return f"❌ Lỗi API Enka (Mã: {status}). Có thể UID không tồn tại hoặc đang bảo trì.", None

        player_info = data.get("detailInfo", {})
        if not player_info:
            return "❌ UID này đang ẩn thông tin hoặc không có dữ liệu hiển thị.", None

        nickname = player_info.get("nickname", "Không tên")
        level = player_info.get("level", 0)
        signature = player_info.get("signature", "*Không có chữ ký*")
        avatar_count = player_info.get("recordInfo", {}).get("avatarCount", 0)

        embed = discord.Embed(
            title=f"📼 HỒ SƠ PROXY — {nickname}",
            description=f"**UID:** `{uid}`",
            color=discord.Color.from_rgb(255, 225, 50)
        )
        embed.add_field(name="⚡ Cấp Inter-Knot", value=f"`{level}`", inline=True)
        embed.add_field(name="👥 Số Agent", value=f"`{avatar_count}`", inline=True)
        embed.add_field(name="✍️ Chữ ký", value=f"*{signature}*", inline=False)
        embed.set_footer(text="Dữ liệu cung cấp bởi Enka.Network", icon_url="https://enka.network/favicon.ico")
        return embed, data

    # ==========================================
    # ⌨️ HỆ THỐNG LỆNH PREFIX (.enka ...)
    # ==========================================
    @commands.group(name="enka", invoke_without_command=True)
    async def enka_group(self, ctx, *, args: str = None):
        prefix = ctx.prefix
        if args:
            parts = args.split()
            first_arg = parts[0]
            sub_commands = [cmd.name for cmd in self.enka_group.commands]
            if first_arg.isdigit() or first_arg.lower() not in sub_commands:
                return await ctx.invoke(self.enka_gi, uid_or_alias=first_arg)

        embed = discord.Embed(
            title="📖 Menu Lệnh Enka (v4.0 SQLite Edition)",
            description=(
                f"🌸 Tra cứu Hồ sơ, Build Card, Xếp hạng **Akasha.cv** & Đội hình **AI ({AI_MODEL})**\n\n"
                f"🌟 **Genshin Impact (gi)**\n"
                f"`{prefix}enka gi [UID/tên]` — Xem hồ sơ & chọn nhân vật\n"
                f"`{prefix}enka gi build [UID/tên] <nhân vật>` — Chi tiết build & thẻ ảnh\n"
                f"`{prefix}enka gi review [UID/tên] <nhân vật>` — AI phân tích build lẻ\n"
                f"`{prefix}enka gi team [UID/tên]` — AI lập đội hình La Hoàn tối ưu\n\n"
                f"🚂 **Honkai: Star Rail (hsr)**\n"
                f"`{prefix}enka hsr [UID/tên]` — Xem tổng quan hồ sơ\n"
                f"`{prefix}enka hsr build [UID/tên] <nhân vật>` — Chi tiết build & thẻ ảnh\n"
                f"`{prefix}enka hsr team [UID/tên]` — AI lập đội hình MoC tối ưu\n\n"
                f"📼 **Zenless Zone Zero (zzz)**\n"
                f"`{prefix}enka zzz [UID/tên]` — Xem tổng quan hồ sơ\n"
                f"`{prefix}enka zzz build [UID/tên] <agent>` — Xem chi tiết Agent & thẻ ảnh\n\n"
                f"💾 **Cơ sở dữ liệu (SQLite)**\n"
                f"`{prefix}enka save <gi|hsr|zzz> <tên> <UID>` — Lưu UID\n"
                f"`{prefix}enka delete <gi|hsr|zzz> <tên>` — Xóa UID\n"
                f"`{prefix}enka list` — Danh sách UID đã lưu"
            ),
            color=discord.Color.pink()
        )
        if self.bot.user.avatar:
            embed.set_footer(text=f"Enka SQLite & xKiro ({AI_MODEL})", icon_url=self.bot.user.avatar.url)
        await ctx.send(embed=embed)

    @enka_group.command(name="sync")
    async def enka_sync(self, ctx):
        msg = await ctx.send("🔄 Đang đồng bộ từ điển Tiếng Việt mới nhất từ Enka.Network...")
        ok = await self.sync_enka_vietnamese_store()
        if ok:
            await msg.edit(content=f"✅ Đã cập nhật thành công **{len(self.char_data)}** nhân vật từ điển Tiếng Việt!")
        else:
            await msg.edit(content="❌ Không thể đồng bộ dữ liệu lúc này. Vui lòng thử lại sau.")

    @enka_group.group(name="gi", invoke_without_command=True)
    async def enka_gi(self, ctx, uid_or_alias: str = None):
        saved_uids = await self.get_user_uids_dict(ctx.author.id, "gi")
        if not uid_or_alias:
            if not saved_uids:
                return await ctx.send(t(ctx.guild, "ENKA_NEED_UID_GI", prefix=ctx.prefix))
            view = discord.ui.View(timeout=60)
            view.add_item(UIDSelect(self, "gi", ctx, saved_uids))
            return await ctx.send(t(ctx.guild, "ENKA_SELECT_PROFILE"), view=view)

        target_uid = await self.resolve_user_uid(ctx.author.id, "gi", uid_or_alias)
        if not target_uid or not target_uid.isdigit() or len(target_uid) < 9:
            return await ctx.send(t(ctx.guild, "ENKA_INVALID_UID"))

        loading_msg = await ctx.send(t(ctx.guild, "ENKA_LOADING_GI", uid=target_uid))
        result, data = await self.get_gi_profile_with_data(target_uid)
        await loading_msg.delete()

        if isinstance(result, str):
            await ctx.send(result)
        else:
            view = CharacterBuildView(self, ctx.author.id, target_uid, "gi", data, profile_embed=result)
            await ctx.send(embed=result, view=view)

    @enka_gi.command(name="build")
    async def enka_gi_build(self, ctx, *, full_args: str = None):
        if not full_args:
            return await ctx.send(t(ctx.guild, "ENKA_BUILD_SYNTAX", prefix=ctx.prefix))

        parts = full_args.split()
        saved_uids = await self.get_user_uids_dict(ctx.author.id, "gi")
        uid_or_alias = None

        if (parts[0].isdigit() and len(parts[0]) >= 9) or (parts[0].lower() in saved_uids and len(parts) > 1):
            uid_or_alias = parts[0]
            character_name = " ".join(parts[1:])
        else:
            character_name = full_args

        if not uid_or_alias:
            if not saved_uids:
                return await ctx.send(t(ctx.guild, "ENKA_NO_SAVED_GI", prefix=ctx.prefix))
            if len(saved_uids) == 1:
                uid = next(iter(saved_uids.values()))
            else:
                view = discord.ui.View(timeout=60)
                view.add_item(UIDSelect(self, "gi_build", ctx, saved_uids, extra_arg=character_name))
                return await ctx.send(t(ctx.guild, "ENKA_SELECT_BUILD", name=character_name), view=view)
        else:
            uid = await self.resolve_user_uid(ctx.author.id, "gi", uid_or_alias)

        if not uid or not uid.isdigit():
            return await ctx.send(t(ctx.guild, "ENKA_INVALID_UID"))

        loading_msg = await ctx.send(t(ctx.guild, "ENKA_LOADING_BUILD", name=character_name, uid=uid))
        response, akasha_data = await asyncio.gather(
            self._fetch_enka_data(uid, 'gi'),
            self._fetch_akasha_ranking(uid)
        )
        data = response.get("data")
        status = response.get("status")
        await loading_msg.delete()

        if status != 200 or not data:
            return await ctx.send(t(ctx.guild, "ENKA_API_ERROR_SIMPLE", status=status))

        target_idx = None
        char_list = data.get("avatarInfoList", [])
        for idx, char_info in enumerate(char_list):
            char_id = str(char_info.get("avatarId"))
            char_name = self.char_data.get(char_id, f"Nhân vật {char_id}")
            if character_name.lower() in char_name.lower():
                target_idx = idx
                break

        if target_idx is None:
            return await ctx.send(t(ctx.guild, "ENKA_NOT_FOUND_CHAR", name=character_name, uid=uid))

        player_nickname = data.get("playerInfo", {}).get("nickname", "Không tên")
        embed = await self._create_build_embed(uid, player_nickname, char_list[target_idx], akasha_data)
        view = CharacterBuildView(self, ctx.author.id, uid, "gi", data, initial_char_idx=target_idx)
        await ctx.send(embed=embed, view=view)

    @enka_gi.command(name="team")
    async def enka_gi_team(self, ctx, uid_or_alias: str = None):
        """AI phân tích toàn bộ Showcase Genshin và gợi ý đội hình La Hoàn."""
        target_uid = await self.resolve_user_uid(ctx.author.id, "gi", uid_or_alias)
        if not target_uid:
            saved = await self.get_user_uids_dict(ctx.author.id, "gi")
            if saved:
                view = discord.ui.View(timeout=60)
                view.add_item(UIDSelect(self, "gi_team", ctx, saved))
                return await ctx.send("📋 Chọn tài khoản Genshin để phân tích đội hình:", view=view)
            return await ctx.send("❌ Vui lòng nhập UID hoặc dùng `.enka save gi <tên> <UID>` trước.")

        msg = await ctx.send(f"🧠 AI (`{AI_MODEL}`) đang phân tích đội hình La Hoàn cho UID `{target_uid}`...")
        res = await self._fetch_enka_data(target_uid, 'gi')
        data = res.get("data")
        if not data or not data.get("avatarInfoList"):
            await msg.delete()
            return await ctx.send("❌ Không tìm thấy nhân vật nào được hiển thị chi tiết trong Showcase.")

        embed = await self._generate_ai_team_embed(ctx.guild, target_uid, "gi", data)
        await msg.delete()
        await ctx.send(embed=embed)

    @enka_gi.command(name="review")
    async def enka_gi_review(self, ctx, uid: str = None, *, nhan_vat: str = None):
        if not uid:
            return await ctx.send(t(ctx.guild, "ENKA_REVIEW_NEED_NAME", prefix=ctx.prefix, uid="UID"))

        if not nhan_vat:
            nhan_vat = uid
            target_uid = await self.resolve_user_uid(ctx.author.id, "gi")
            if not target_uid:
                return await ctx.send(t(ctx.guild, "ENKA_NO_SAVED_UID", prefix=ctx.prefix))
        else:
            target_uid = await self.resolve_user_uid(ctx.author.id, "gi", uid)
            if not target_uid:
                nhan_vat = f"{uid} {nhan_vat}".strip()
                target_uid = await self.resolve_user_uid(ctx.author.id, "gi")

        if not target_uid or not target_uid.isdigit() or len(target_uid) < 9:
            return await ctx.send(t(ctx.guild, "ENKA_INVALID_UID2"))

        loading_msg = await ctx.send(t(ctx.guild, "ENKA_AI_ANALYZING", name=nhan_vat, uid=target_uid))
        response = await self._fetch_enka_data(target_uid, 'gi')
        data = response.get("data")
        status = response.get("status")

        if status != 200 or not data:
            await loading_msg.delete()
            return await ctx.send(f"❌ Lỗi API Enka (Mã: {status}). Không thể lấy dữ liệu để phân tích.")

        target_char_data = None
        for char_info in data.get("avatarInfoList", []):
            char_id = str(char_info.get("avatarId"))
            char_name_from_data = self.char_data.get(char_id, f"Nhân vật {char_id}")
            if nhan_vat.lower() in char_name_from_data.lower():
                target_char_data = char_info
                break

        if not target_char_data:
            await loading_msg.delete()
            return await ctx.send(f"❌ Không tìm thấy nhân vật **{nhan_vat}** trong showcase của UID `{target_uid}`.")

        embed = await self._generate_ai_review_embed(ctx.guild, target_uid, target_char_data)
        await loading_msg.delete()
        await ctx.send(embed=embed)

    # --- PREFIX HONKAI: STAR RAIL ---
    @enka_group.group(name="hsr", invoke_without_command=True)
    async def enka_hsr(self, ctx, uid_or_alias: str = None):
        saved_uids = await self.get_user_uids_dict(ctx.author.id, "hsr")
        if not uid_or_alias:
            if not saved_uids:
                return await ctx.send(t(ctx.guild, "ENKA_NEED_UID_HSR", prefix=ctx.prefix))
            view = discord.ui.View(timeout=60)
            view.add_item(UIDSelect(self, "hsr", ctx, saved_uids))
            return await ctx.send(t(ctx.guild, "ENKA_SELECT_PROFILE"), view=view)

        target_uid = await self.resolve_user_uid(ctx.author.id, "hsr", uid_or_alias)
        if not target_uid or not target_uid.isdigit() or len(target_uid) != 9:
            return await ctx.send(t(ctx.guild, "ENKA_INVALID_HSR_UID"))

        loading_msg = await ctx.send(t(ctx.guild, "ENKA_LOADING_HSR", uid=target_uid))
        result, data = await self.get_hsr_profile_with_data(target_uid)
        await loading_msg.delete()

        if isinstance(result, str):
            await ctx.send(result)
        else:
            view = CharacterBuildView(self, ctx.author.id, target_uid, "hsr", data, profile_embed=result)
            await ctx.send(embed=result, view=view)

    @enka_hsr.command(name="build")
    async def enka_hsr_build(self, ctx, uid_or_alias: str = None, *, character_name: str = None):
        if not uid_or_alias:
            return await ctx.send(t(ctx.guild, "ENKA_HSR_BUILD_SYNTAX", prefix=ctx.prefix))

        saved_uids = await self.get_user_uids_dict(ctx.author.id, "hsr")
        if not character_name:
            character_name = uid_or_alias
            if not saved_uids:
                return await ctx.send(t(ctx.guild, "ENKA_NO_SAVED_HSR", prefix=ctx.prefix))
            if len(saved_uids) == 1:
                uid = next(iter(saved_uids.values()))
            else:
                view = discord.ui.View(timeout=60)
                view.add_item(UIDSelect(self, "hsr_build", ctx, saved_uids, extra_arg=character_name))
                return await ctx.send(t(ctx.guild, "ENKA_SELECT_BUILD", name=character_name), view=view)
        else:
            uid = await self.resolve_user_uid(ctx.author.id, "hsr", uid_or_alias)
            if not uid:
                return await ctx.send(f"❌ Không tìm thấy tài khoản HSR nào có tên `{uid_or_alias}`.")

        loading_msg = await ctx.send(f"🛠️ Đang lấy dữ liệu build HSR của **{character_name}** (UID: `{uid}`)...")
        response = await self._fetch_enka_data(uid, 'hsr')
        raw_data = response.get("data", {})
        data = raw_data.get("detailInfo", {}) if raw_data else {}
        status = response.get("status")
        await loading_msg.delete()

        if status != 200 or not data:
            return await ctx.send(f"❌ Lỗi API Enka (Mã: {status}). Không thể lấy dữ liệu HSR.")

        char_list = data.get("avatarDetailList", [])
        target_idx = next((i for i, c in enumerate(char_list) if character_name.lower() in c.get("name", "").lower()), None)

        if target_idx is None:
            return await ctx.send(f"❌ Không tìm thấy nhân vật **{character_name}** trong showcase HSR của UID `{uid}`.")

        player_nickname = data.get("nickname", "Không tên")
        embed = self._create_hsr_build_embed(uid, player_nickname, char_list[target_idx])
        view = CharacterBuildView(self, ctx.author.id, uid, "hsr", raw_data, initial_char_idx=target_idx)
        await ctx.send(embed=embed, view=view)

    @enka_hsr.command(name="team")
    async def enka_hsr_team(self, ctx, uid_or_alias: str = None):
        """AI phân tích Showcase HSR và gợi ý đội hình Sảnh Đường Hỗn Độn."""
        target_uid = await self.resolve_user_uid(ctx.author.id, "hsr", uid_or_alias)
        if not target_uid:
            saved = await self.get_user_uids_dict(ctx.author.id, "hsr")
            if saved:
                view = discord.ui.View(timeout=60)
                view.add_item(UIDSelect(self, "hsr_team", ctx, saved))
                return await ctx.send("📋 Chọn tài khoản HSR để phân tích đội hình:", view=view)
            return await ctx.send("❌ Vui lòng nhập UID hoặc dùng `.enka save hsr <tên> <UID>` trước.")

        msg = await ctx.send(f"🧠 AI (`{AI_MODEL}`) đang phân tích đội hình HSR cho UID `{target_uid}`...")
        res = await self._fetch_enka_data(target_uid, 'hsr')
        raw_data = res.get("data", {})
        if not raw_data or not raw_data.get("detailInfo", {}).get("avatarDetailList"):
            await msg.delete()
            return await ctx.send("❌ Không tìm thấy nhân vật nào được hiển thị trong Showcase HSR.")

        embed = await self._generate_ai_team_embed(ctx.guild, target_uid, "hsr", raw_data)
        await msg.delete()
        await ctx.send(embed=embed)

    # --- PREFIX ZENLESS ZONE ZERO ---
    @enka_group.group(name="zzz", invoke_without_command=True)
    async def enka_zzz(self, ctx, uid_or_alias: str = None):
        saved_uids = await self.get_user_uids_dict(ctx.author.id, "zzz")
        if not uid_or_alias:
            if not saved_uids:
                return await ctx.send(t(ctx.guild, "ENKA_NEED_UID_ZZZ", prefix=ctx.prefix))
            view = discord.ui.View(timeout=60)
            view.add_item(UIDSelect(self, "zzz", ctx, saved_uids))
            return await ctx.send(t(ctx.guild, "ENKA_SELECT_PROFILE"), view=view)

        target_uid = await self.resolve_user_uid(ctx.author.id, "zzz", uid_or_alias)
        if not target_uid or not target_uid.isdigit() or len(target_uid) != 10:
            return await ctx.send(t(ctx.guild, "ENKA_INVALID_ZZZ_UID"))

        loading_msg = await ctx.send(t(ctx.guild, "ENKA_LOADING_ZZZ", uid=target_uid))
        result, data = await self.get_zzz_profile_with_data(target_uid)
        await loading_msg.delete()

        if isinstance(result, str):
            await ctx.send(result)
        else:
            view = CharacterBuildView(self, ctx.author.id, target_uid, "zzz", data, profile_embed=result)
            await ctx.send(embed=result, view=view)

    @enka_zzz.command(name="build")
    async def enka_zzz_build(self, ctx, uid_or_alias: str = None, *, character_name: str = None):
        if not uid_or_alias:
            return await ctx.send(t(ctx.guild, "ENKA_ZZZ_BUILD_SYNTAX", prefix=ctx.prefix))

        saved_uids = await self.get_user_uids_dict(ctx.author.id, "zzz")
        if not character_name:
            character_name = uid_or_alias
            if not saved_uids:
                return await ctx.send(t(ctx.guild, "ENKA_NO_SAVED_ZZZ", prefix=ctx.prefix))
            if len(saved_uids) == 1:
                uid = next(iter(saved_uids.values()))
            else:
                view = discord.ui.View(timeout=60)
                view.add_item(UIDSelect(self, "zzz_build", ctx, saved_uids, extra_arg=character_name))
                return await ctx.send(t(ctx.guild, "ENKA_SELECT_BUILD", name=character_name), view=view)
        else:
            uid = await self.resolve_user_uid(ctx.author.id, "zzz", uid_or_alias)
            if not uid:
                return await ctx.send(f"❌ Không tìm thấy tài khoản ZZZ nào có tên `{uid_or_alias}`.")

        loading_msg = await ctx.send(f"🛠️ Đang lấy dữ liệu build ZZZ của **{character_name}** (UID: `{uid}`)...")
        response = await self._fetch_enka_data(uid, 'zzz')
        raw_data = response.get("data", {})
        data = raw_data.get("detailInfo", {}) if raw_data else {}
        status = response.get("status")
        await loading_msg.delete()

        if status != 200 or not data:
            return await ctx.send(f"❌ Lỗi API Enka (Mã: {status}). Không thể lấy dữ liệu ZZZ.")

        char_list = data.get("avatarDetailList", [])
        target_idx = next((i for i, c in enumerate(char_list) if character_name.lower() in c.get("name", "").lower()), None)

        if target_idx is None:
            return await ctx.send(f"❌ Không tìm thấy Agent **{character_name}** trong showcase ZZZ của UID `{uid}`.")

        player_nickname = data.get("nickname", "Không tên")
        embed = self._create_zzz_build_embed(uid, player_nickname, char_list[target_idx])
        view = CharacterBuildView(self, ctx.author.id, uid, "zzz", raw_data, initial_char_idx=target_idx)
        await ctx.send(embed=embed, view=view)

    # --- LƯU, XÓA & XEM DANH SÁCH UID (SQLITE) ---
    @enka_group.command(name="save", aliases=["add", "link"])
    async def enka_save(self, ctx, game: str, alias: str, uid: str = None):
        if uid is None:
            uid = alias
            alias = "default"

        game_lower = game.lower()
        alias_lower = alias.lower()

        if game_lower not in ["gi", "hsr", "zzz"]:
            return await ctx.send(t(ctx.guild, "ENKA_INVALID_GAME"))
        if not uid.isdigit() or len(uid) not in [9, 10]:
            return await ctx.send(t(ctx.guild, "ENKA_INVALID_UID_LEN"))
        if not alias_lower.isalnum() or len(alias_lower) > 20:
            return await ctx.send(t(ctx.guild, "ENKA_INVALID_ALIAS"))

        await self.save_user_uid_to_db(ctx.author.id, game_lower, alias_lower, uid)
        await ctx.send(t(ctx.guild, "ENKA_SAVED", uid=uid, game=game.upper(), alias=alias_lower))

    @enka_group.command(name="delete", aliases=["del", "remove"])
    async def enka_delete(self, ctx, game: str, alias: str = "default"):
        removed_uid = await self.delete_user_uid_from_db(ctx.author.id, game.lower(), alias.lower())
        if not removed_uid:
            return await ctx.send(f"❌ Không tìm thấy tên lưu `{alias}` trong game **{game.upper()}**.")
        await ctx.send(f"🗑️ Đã xóa UID `{removed_uid}` (`{alias}`) khỏi danh sách **{game.upper()}**.")

    @enka_group.command(name="list", aliases=["show", "uids"])
    async def enka_list(self, ctx):
        user_data = await self.get_user_uids_dict(ctx.author.id)
        if not user_data:
            return await ctx.send(t(ctx.guild, "ENKA_NO_SAVED_ANY"))

        embed = discord.Embed(title=f"✨ Danh sách UID SQLite của {ctx.author.display_name}", color=discord.Color.blue())
        for game, uids in user_data.items():
            if isinstance(uids, dict) and uids:
                value = "\n".join([f"• **{alias}**: `{uid}`" for alias, uid in uids.items()])
                embed.add_field(name=f"🎮 {game.upper()}", value=value, inline=False)

        await ctx.send(embed=embed)

    # ==========================================
    # ⌨️ HỆ THỐNG LỆNH SLASH (/enka ...)
    # ==========================================
    enka_slash = app_commands.Group(name="enka", description="Tra cứu Enka.Network cho Genshin, HSR, ZZZ")

    gi_slash = app_commands.Group(name="gi", description="Các lệnh cho Genshin Impact", parent=enka_slash)

    @gi_slash.command(name="profile", description="Xem tổng quan hồ sơ người chơi Genshin Impact")
    @app_commands.describe(uid="UID hoặc tên đã lưu (Bỏ trống để dùng UID mặc định)")
    async def slash_gi_profile(self, interaction: discord.Interaction, uid: str = None):
        await interaction.response.defer()
        target_uid = await self.resolve_user_uid(interaction.user.id, "gi", uid)
        if not target_uid:
            return await interaction.followup.send(t(interaction.guild, "ENKA_SLASH_NO_UID"))

        result, data = await self.get_gi_profile_with_data(target_uid)
        if isinstance(result, str):
            await interaction.followup.send(result)
        else:
            view = CharacterBuildView(self, interaction.user.id, target_uid, "gi", data, profile_embed=result)
            await interaction.followup.send(embed=result, view=view)

    async def character_autocomplete(self, interaction: discord.Interaction, current: str) -> list[app_commands.Choice[str]]:
        return [
            app_commands.Choice(name=name, value=name)
            for char_id, name in self.char_data.items()
            if current.lower() in name.lower()
        ][:25]

    @gi_slash.command(name="build", description="Xem chi tiết build của một nhân vật Genshin Impact")
    @app_commands.describe(nhan_vat="Tên nhân vật bạn muốn xem", uid="UID hoặc tên đã lưu (Bỏ trống nếu đã lưu)")
    @app_commands.autocomplete(nhan_vat=character_autocomplete)
    async def slash_gi_build(self, interaction: discord.Interaction, nhan_vat: str, uid: str = None):
        await interaction.response.defer()
        target_uid = await self.resolve_user_uid(interaction.user.id, "gi", uid)
        if not target_uid:
            return await interaction.followup.send(t(interaction.guild, "ENKA_SLASH_NO_UID"))

        response, akasha_data = await asyncio.gather(
            self._fetch_enka_data(target_uid, 'gi'),
            self._fetch_akasha_ranking(target_uid)
        )
        data = response.get("data")
        status = response.get("status")

        if status != 200 or not data:
            return await interaction.followup.send(f"❌ Lỗi API Enka (Mã: {status}). Không thể lấy dữ liệu.")

        char_list = data.get("avatarInfoList", [])
        target_idx = None
        for idx, char_info in enumerate(char_list):
            char_id = str(char_info.get("avatarId"))
            char_name_from_data = self.char_data.get(char_id, f"Nhân vật {char_id}")
            if nhan_vat.lower() in char_name_from_data.lower():
                target_idx = idx
                break

        if target_idx is None:
            return await interaction.followup.send(f"❌ Không tìm thấy nhân vật **{nhan_vat}** trong showcase của UID `{target_uid}`.")

        player_nickname = data.get("playerInfo", {}).get("nickname", "Không tên")
        embed = await self._create_build_embed(target_uid, player_nickname, char_list[target_idx], akasha_data)
        view = CharacterBuildView(self, interaction.user.id, target_uid, "gi", data, initial_char_idx=target_idx)
        await interaction.followup.send(embed=embed, view=view)

    @gi_slash.command(name="team", description="AI phân tích và đề xuất đội hình La Hoàn tối ưu")
    @app_commands.describe(uid="UID hoặc tên đã lưu (Bỏ trống để dùng UID mặc định)")
    async def slash_gi_team(self, interaction: discord.Interaction, uid: str = None):
        await interaction.response.defer()
        target_uid = await self.resolve_user_uid(interaction.user.id, "gi", uid)
        if not target_uid:
            return await interaction.followup.send(t(interaction.guild, "ENKA_SLASH_NO_UID"))

        res = await self._fetch_enka_data(target_uid, 'gi')
        data = res.get("data")
        if not data or not data.get("avatarInfoList"):
            return await interaction.followup.send("❌ Không tìm thấy danh sách nhân vật trưng bày của UID này.")

        embed = await self._generate_ai_team_embed(interaction.guild, target_uid, "gi", data)
        await interaction.followup.send(embed=embed)

    # --- Slash Honkai: Star Rail ---
    hsr_slash = app_commands.Group(name="hsr", description="Các lệnh cho Honkai: Star Rail", parent=enka_slash)

    @hsr_slash.command(name="profile", description="Xem tổng quan hồ sơ người chơi Honkai: Star Rail")
    @app_commands.describe(uid="UID hoặc tên đã lưu (Bỏ trống nếu đã lưu UID)")
    async def slash_hsr_profile(self, interaction: discord.Interaction, uid: str = None):
        await interaction.response.defer()
        target_uid = await self.resolve_user_uid(interaction.user.id, "hsr", uid)
        if not target_uid:
            return await interaction.followup.send(t(interaction.guild, "ENKA_SLASH_NO_UID_HSR"))

        result, data = await self.get_hsr_profile_with_data(target_uid)
        if isinstance(result, str):
            await interaction.followup.send(result)
        else:
            view = CharacterBuildView(self, interaction.user.id, target_uid, "hsr", data, profile_embed=result)
            await interaction.followup.send(embed=result, view=view)

    @hsr_slash.command(name="build", description="Xem chi tiết build nhân vật Honkai: Star Rail")
    @app_commands.describe(nhan_vat="Tên nhân vật HSR muốn xem", uid="UID hoặc tên đã lưu")
    async def slash_hsr_build(self, interaction: discord.Interaction, nhan_vat: str, uid: str = None):
        await interaction.response.defer()
        target_uid = await self.resolve_user_uid(interaction.user.id, "hsr", uid)
        if not target_uid:
            return await interaction.followup.send("❌ Vui lòng nhập UID hoặc lưu UID bằng `/enka save` trước.")

        response = await self._fetch_enka_data(target_uid, 'hsr')
        raw_data = response.get("data", {})
        data = raw_data.get("detailInfo", {}) if raw_data else {}
        status = response.get("status")

        if status != 200 or not data:
            return await interaction.followup.send(f"❌ Lỗi API Enka (Mã: {status}).")

        char_list = data.get("avatarDetailList", [])
        target_idx = next((i for i, c in enumerate(char_list) if nhan_vat.lower() in c.get("name", "").lower()), None)
        if target_idx is None:
            return await interaction.followup.send(f"❌ Không tìm thấy **{nhan_vat}** trong showcase HSR của UID `{target_uid}`.")

        embed = self._create_hsr_build_embed(target_uid, data.get("nickname", "Không tên"), char_list[target_idx])
        view = CharacterBuildView(self, interaction.user.id, target_uid, "hsr", raw_data, initial_char_idx=target_idx)
        await interaction.followup.send(embed=embed, view=view)

    @hsr_slash.command(name="team", description="AI phân tích và đề xuất đội hình MoC HSR tối ưu")
    @app_commands.describe(uid="UID hoặc tên đã lưu (Bỏ trống để dùng UID mặc định)")
    async def slash_hsr_team(self, interaction: discord.Interaction, uid: str = None):
        await interaction.response.defer()
        target_uid = await self.resolve_user_uid(interaction.user.id, "hsr", uid)
        if not target_uid:
            return await interaction.followup.send(t(interaction.guild, "ENKA_SLASH_NO_UID_HSR"))

        res = await self._fetch_enka_data(target_uid, 'hsr')
        raw_data = res.get("data", {})
        if not raw_data or not raw_data.get("detailInfo", {}).get("avatarDetailList"):
            return await interaction.followup.send("❌ Không tìm thấy danh sách nhân vật trưng bày HSR.")

        embed = await self._generate_ai_team_embed(interaction.guild, target_uid, "hsr", raw_data)
        await interaction.followup.send(embed=embed)

    # --- Slash Zenless Zone Zero ---
    zzz_slash = app_commands.Group(name="zzz", description="Các lệnh cho Zenless Zone Zero", parent=enka_slash)

    @zzz_slash.command(name="profile", description="Xem tổng quan hồ sơ Zenless Zone Zero")
    @app_commands.describe(uid="UID hoặc tên đã lưu (Bỏ trống nếu đã lưu UID)")
    async def slash_zzz_profile(self, interaction: discord.Interaction, uid: str = None):
        await interaction.response.defer()
        target_uid = await self.resolve_user_uid(interaction.user.id, "zzz", uid)
        if not target_uid:
            return await interaction.followup.send("❌ Bạn chưa lưu UID Zenless Zone Zero! Hãy dùng `/enka save`.")

        result, data = await self.get_zzz_profile_with_data(target_uid)
        if isinstance(result, str):
            await interaction.followup.send(result)
        else:
            view = CharacterBuildView(self, interaction.user.id, target_uid, "zzz", data, profile_embed=result)
            await interaction.followup.send(embed=result, view=view)

    @zzz_slash.command(name="build", description="Xem chi tiết build Agent Zenless Zone Zero")
    @app_commands.describe(agent="Tên Agent muốn xem", uid="UID hoặc tên đã lưu")
    async def slash_zzz_build(self, interaction: discord.Interaction, agent: str, uid: str = None):
        await interaction.response.defer()
        target_uid = await self.resolve_user_uid(interaction.user.id, "zzz", uid)
        if not target_uid:
            return await interaction.followup.send("❌ Bạn chưa lưu UID Zenless Zone Zero! Hãy dùng `/enka save`.")

        response = await self._fetch_enka_data(target_uid, 'zzz')
        raw_data = response.get("data", {})
        data = raw_data.get("detailInfo", {}) if raw_data else {}
        status = response.get("status")

        if status != 200 or not data:
            return await interaction.followup.send(f"❌ Lỗi API Enka (Mã: {status}).")

        char_list = data.get("avatarDetailList", [])
        target_idx = next((i for i, c in enumerate(char_list) if agent.lower() in c.get("name", "").lower()), None)
        if target_idx is None:
            return await interaction.followup.send(f"❌ Không tìm thấy **{agent}** trong showcase ZZZ của UID `{target_uid}`.")

        embed = self._create_zzz_build_embed(target_uid, data.get("nickname", "Không tên"), char_list[target_idx])
        view = CharacterBuildView(self, interaction.user.id, target_uid, "zzz", raw_data, initial_char_idx=target_idx)
        await interaction.followup.send(embed=embed, view=view)

    @enka_slash.command(name="save", description="Lưu UID của bạn vào SQLite database")
    @app_commands.describe(game="Chọn game bạn muốn lưu UID", uid="Nhập UID (9 hoặc 10 chữ số)", alias="Tên gợi nhớ (mặc định: default)")
    @app_commands.choices(game=[
        app_commands.Choice(name="Genshin Impact", value="gi"),
        app_commands.Choice(name="Honkai: Star Rail", value="hsr"),
        app_commands.Choice(name="Zenless Zone Zero", value="zzz"),
    ])
    async def slash_save_uid(self, interaction: discord.Interaction, game: app_commands.Choice[str], uid: str, alias: str = "default"):
        if not uid.isdigit() or len(uid) not in [9, 10]:
            return await interaction.response.send_message(t(interaction.guild, "ENKA_INVALID_UID_LEN"), ephemeral=True)

        alias_clean = alias.lower().strip()
        await self.save_user_uid_to_db(interaction.user.id, game.value, alias_clean, uid)
        await interaction.response.send_message(t(interaction.guild, "ENKA_SAVED", uid=uid, game=game.name, alias=alias_clean), ephemeral=True)


async def setup(bot):
    await bot.add_cog(EnkaCog(bot))
