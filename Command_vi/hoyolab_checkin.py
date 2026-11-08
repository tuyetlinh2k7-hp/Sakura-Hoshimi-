import discord
from discord import app_commands
from discord.ext import commands, tasks
import genshin
import asyncio
import re
import json
import os
from datetime import datetime, time, timezone, timedelta
from typing import Optional, List, Dict, Any, Union
import hashlib
import secrets
from Checks_vi.i18n import t
from Checks_vi.hoyo_captcha_session import (
    create_captcha_session, update_captcha_session, get_captcha_session, resolve_captcha_session,
    create_otp_session, get_otp_session, resolve_otp_session
)
from genshin.client.manager.cookie import fetch_cookie_with_stoken_v2

try:
    from config import WEB_BASE_URL
except Exception:
    WEB_BASE_URL = "https://sakurabot.wispbyte.org"

COOKIE_FILE = "data/hoyolab_cookies.json"

# Danh sách các game được hỗ trợ điểm danh
GAMES = {
    "genshin": {
        "name": "Genshin Impact",
        "game": genshin.Game.GENSHIN,
        "emoji": "🌸"
    },
    "hsr": {
        "name": "Honkai: Star Rail",
        "game": genshin.Game.STARRAIL,
        "emoji": "🚂"
    },
    "zzz": {
        "name": "Zenless Zone Zero",
        "game": genshin.Game.ZZZ,
        "emoji": "⚡"
    },
    "bh3": {
        "name": "Honkai Impact 3rd",
        "game": genshin.Game.HONKAI,
        "emoji": "⚔️"
    }
}

# Đoạn mã JavaScript Bookmarklet chuẩn 1 chạm trích xuất cookie tự động
BOOKMARKLET_JS = (
    "javascript:(function(){try{"
    "var c=document.cookie;"
    "var u=(c.match(/(?:ltuid_v2|ltuid|account_id_v2|account_id)\\s*=\\s*([^;]+)/)||[])[1];"
    "var t=(c.match(/(?:ltoken_v2|ltoken)\\s*=\\s*([^;]+)/)||[])[1];"
    "var ct=(c.match(/(?:cookie_token_v2|cookie_token)\\s*=\\s*([^;]+)/)||[])[1];"
    "if(u&&t){"
    "var res='ltuid_v2='+u+'; ltoken_v2='+t+';';"
    "if(ct){res+=' cookie_token_v2='+ct+';';}"
    "if(navigator.clipboard&&navigator.clipboard.writeText){"
    "navigator.clipboard.writeText(res).then(function(){"
    "alert('✅ ĐÃ SAO CHÉP COOKIE HOYOLAB THÀNH CÔNG!\\n\\n'+res+'\\n\\n👉 Hãy quay lại Discord dán vào SakuraBot nhé!');"
    "}).catch(function(){prompt('Vui lòng copy đoạn mã sau:',res);});"
    "}else{prompt('Vui lòng copy đoạn mã sau:',res);}"
    "}else{"
    "alert('❌ Không tìm thấy Cookie hợp lệ!\\n\\nHãy đăng nhập tại https://www.hoyolab.com rồi bấm lại bookmarklet.');"
    "}"
    "}catch(e){alert('Lỗi: '+e);}})();"
)

def load_cookies() -> Dict[str, Any]:
    """Tải dữ liệu cookie từ file JSON (kèm đồng bộ hai chiều từ Database)."""
    if os.path.exists(COOKIE_FILE):
        try:
            with open(COOKIE_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except (json.JSONDecodeError, OSError):
            return {}
    return {}

def save_cookies(data: Dict[str, Any]) -> None:
    """Lưu dữ liệu cookie vào file JSON an toàn và tự động đồng bộ vào SQLite Database."""
    os.makedirs(os.path.dirname(COOKIE_FILE), exist_ok=True)
    with open(COOKIE_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)

    try:
        from data.database import db_save_hoyolab_account
        async def _sync_to_sqlite():
            for uid, accounts in data.items():
                if isinstance(accounts, list):
                    for acc in accounts:
                        if isinstance(acc, dict):
                            await db_save_hoyolab_account(
                                user_id=uid,
                                account_name=acc.get("name", "Mặc định"),
                                cookies=acc.get("cookies", {}),
                                game_accounts=acc.get("game_accounts", []),
                                auto_checkin=acc.get("auto_checkin", True),
                                auto_redeem=acc.get("auto_redeem", True)
                            )
        loop = asyncio.get_event_loop()
        if loop.is_running():
            asyncio.create_task(_sync_to_sqlite())
    except Exception:
        pass

def extract_hoyolab_cookies(text: str) -> Dict[str, str]:
    """
    Trích xuất thông minh các token HoYoLAB từ bất kỳ định dạng nào:
    - Chuỗi Request Header Cookie đầy đủ (F12 Network)
    - Tab Application / Storage (Cookies)
    - Đầu ra từ Bookmarklet (ltuid_v2=...; ltoken_v2=...)
    - Các giá trị dán rời rạc hoặc nhiều dòng
    """
    if not text:
        return {}
    text = text.strip()
    result: Dict[str, str] = {}

    # Tìm ltuid / account_id
    uid_match = re.search(r'(?:ltuid_v2|ltuid|account_id_v2|account_id)\s*[:=]\s*["\']?(\d+)', text, re.IGNORECASE)
    if uid_match:
        result['ltuid_v2'] = uid_match.group(1).strip()
        result['ltuid'] = result['ltuid_v2']

    # Tìm ltoken
    token_match = re.search(r'(?:ltoken_v2|ltoken)\s*[:=]\s*["\']?([a-zA-Z0-9_\-\.]+)', text, re.IGNORECASE)
    if token_match:
        result['ltoken_v2'] = token_match.group(1).strip()
        result['ltoken'] = result['ltoken_v2']

    # Tìm cookie_token (nếu có)
    ctoken_match = re.search(r'(?:cookie_token_v2|cookie_token)\s*[:=]\s*["\']?([a-zA-Z0-9_\-\.]+)', text, re.IGNORECASE)
    if ctoken_match:
        result['cookie_token_v2'] = ctoken_match.group(1).strip()
        result['cookie_token'] = result['cookie_token_v2']

    # Tìm ltmid (nếu có)
    mid_match = re.search(r'(?:ltmid_v2|account_mid_v2)\s*[:=]\s*["\']?([a-zA-Z0-9_\-\.]+)', text, re.IGNORECASE)
    if mid_match:
        result['ltmid_v2'] = mid_match.group(1).strip()

    # Nếu người dùng chỉ dán giá trị thô theo từng dòng
    if 'ltuid_v2' not in result or 'ltoken_v2' not in result:
        lines = [line.strip() for line in text.splitlines() if line.strip()]
        for line in lines:
            if line.isdigit() and 'ltuid_v2' not in result:
                result['ltuid_v2'] = line
                result['ltuid'] = line
            elif (line.startswith('v2_') or len(line) >= 20) and 'ltoken_v2' not in result and not line.isdigit():
                result['ltoken_v2'] = line
                result['ltoken'] = line

    return result

# Danh mục game hỗ trợ đổi Giftcode trực tiếp qua API HoYoverse
REDEEM_SUPPORTED_GAMES = {
    "genshin": {
        "game": genshin.Game.GENSHIN,
        "name": "Genshin Impact",
        "biz_prefix": "hk4e"
    },
    "hsr": {
        "game": genshin.Game.STARRAIL,
        "name": "Honkai: Star Rail",
        "biz_prefix": "hkrpg"
    },
    "zzz": {
        "game": genshin.Game.ZZZ,
        "name": "Zenless Zone Zero",
        "biz_prefix": "nap"
    }
}

# Link bù điểm danh chính thức từ HoYoLAB (Hoyo Buddy style)
CHECK_IN_URLS = {
    "genshin": "https://act.hoyolab.com/ys/event/signin-sea-v3/index.html?act_id=e202102251931481",
    "hsr": "https://act.hoyolab.com/bbs/event/signin/hkrpg/index.html?act_id=e202303301540311",
    "zzz": "https://act.hoyolab.com/bbs/event/signin/zzz/e202406031448091.html?act_id=e202406031448091",
    "bh3": "https://act.hoyolab.com/bbs/event/signin-bh3/index.html?act_id=e202110291205111",
}

def build_genshin_client(account: dict) -> genshin.Client:
    """Khởi tạo genshin.Client đầy đủ token và alias dự phòng."""
    ltoken = account.get("ltoken_v2") or account.get("ltoken", "")
    ltuid = account.get("ltuid_v2") or account.get("ltuid", "")
    auth_cookies = {
        "ltoken_v2": ltoken,
        "ltuid_v2": ltuid,
        "ltoken": ltoken,
        "ltuid": ltuid,
        "account_id": ltuid,
        "account_id_v2": ltuid,
    }
    if account.get("cookie_token_v2"):
        auth_cookies["cookie_token_v2"] = account["cookie_token_v2"]
        auth_cookies["cookie_token"] = account["cookie_token_v2"]
    if account.get("ltmid_v2"):
        auth_cookies["ltmid_v2"] = account["ltmid_v2"]
        auth_cookies["account_mid_v2"] = account["ltmid_v2"]
    return genshin.Client(auth_cookies, lang="vi-vn")

def make_progress_bar(current: int, total: int, length: int = 8) -> str:
    """Tạo thanh tiến độ trực quan dạng emoji."""
    if total <= 0:
        return "⬜" * length
    ratio = min(max(current / total, 0.0), 1.0)
    filled = int(round(ratio * length))
    empty = length - filled
    percent = int(ratio * 100)
    return f"{'🟩' * filled}{'⬜' * empty} `{percent}%`"

def format_timedelta_future(td: Optional[timedelta]) -> str:
    """Định dạng thời gian hồi phục thể lực / nhựa thành dạng dễ đọc."""
    if not td or td.total_seconds() <= 0:
        return "✅ Đã hồi phục đầy đủ!"
    secs = int(td.total_seconds())
    hours, remainder = divmod(secs, 3600)
    minutes, _ = divmod(remainder, 60)
    target_time = datetime.now() + td
    return f"Đầy sau `{hours}h {minutes}m` (Lúc **{target_time.strftime('%H:%M')}**)"

async def redeem_code_for_single_account(
    acc: Dict[str, Any],
    code: str,
    target_game: Optional[str] = None
) -> List[str]:
    """
    Thực hiện đổi mã giftcode cho 1 tài khoản HoYoverse đã lưu.
    Tự động xác định nhân vật (UID), làm mới cookie_token nếu cần, và gọi API HoYoverse.
    """
    results: List[str] = []
    code = code.strip().upper()
    acc_name = acc.get("name", "Tài khoản")

    # Kiểm tra cookie_token_v2, nếu thiếu mà có stoken_v2 thì tự động làm mới
    if not acc.get("cookie_token_v2") and acc.get("stoken_v2"):
        try:
            cookies_to_exchange = {
                "stoken": acc["stoken_v2"],
                "ltuid_v2": acc.get("ltuid_v2"),
                "ltmid_v2": acc.get("ltmid_v2"),
                "account_id_v2": acc.get("ltuid_v2"),
            }
            fetched = await fetch_cookie_with_stoken_v2(cookies_to_exchange, token_types=[4])
            if fetched.get("cookie_token_v2"):
                acc["cookie_token_v2"] = fetched["cookie_token_v2"]
        except Exception:
            pass

    cookies = {}
    for k in ["cookie_token_v2", "cookie_token", "ltuid_v2", "account_id_v2", "ltoken_v2", "stoken_v2"]:
        if acc.get(k):
            cookies[k] = acc[k]

    if not cookies.get("cookie_token_v2") and not cookies.get("cookie_token"):
        return [f"⚠️ **{acc_name}**: Tài khoản thiếu `cookie_token_v2` (yêu cầu để nhập giftcode). Vui lòng đăng nhập lại qua bot để nhận token đầy đủ!"]

    client = genshin.Client(cookies, lang="vi-vn")

    # Xác định danh sách nhân vật cần đổi code
    targets_to_redeem = []

    tg = target_game.lower().strip() if target_game else None
    if tg == "gi": tg = "genshin"
    elif tg in ("starrail", "honkai_star_rail"): tg = "hsr"

    # 1. Thử lấy danh sách nhân vật từ API getUserGameRolesByCookie
    try:
        roles = await client.get_game_accounts()
    except Exception:
        roles = []

    if roles:
        for r in roles:
            biz = r.game_biz.lower()
            matched_key = None
            matched_cfg = None
            for gk, gcfg in REDEEM_SUPPORTED_GAMES.items():
                if biz.startswith(gcfg["biz_prefix"]):
                    matched_key = gk
                    matched_cfg = gcfg
                    break

            if not matched_key or not matched_cfg:
                continue

            if tg and tg != matched_key:
                continue

            targets_to_redeem.append((
                matched_cfg["game"],
                int(r.uid),
                r.nickname or acc_name,
                matched_cfg["name"]
            ))

    # 2. Nếu không gọi được API get_game_accounts nhưng trong acc đã lưu game_uid
    if not targets_to_redeem and acc.get("game_uid"):
        saved_uid = int(acc["game_uid"])
        saved_biz = (acc.get("game_biz") or "").lower()
        matched_cfg = None
        for gk, gcfg in REDEEM_SUPPORTED_GAMES.items():
            if tg == gk or saved_biz.startswith(gcfg["biz_prefix"]):
                matched_cfg = gcfg
                break
        if not matched_cfg and tg in REDEEM_SUPPORTED_GAMES:
            matched_cfg = REDEEM_SUPPORTED_GAMES[tg]

        if matched_cfg:
            targets_to_redeem.append((
                matched_cfg["game"],
                saved_uid,
                acc.get("nickname") or acc_name,
                matched_cfg["name"]
            ))

    if not targets_to_redeem:
        game_desc = f" ({REDEEM_SUPPORTED_GAMES[tg]['name']})" if tg in REDEEM_SUPPORTED_GAMES else ""
        return [f"⚠️ **{acc_name}**: Không tìm thấy nhân vật nào phù hợp{game_desc} trên tài khoản này để nhập mã."]

    # 3. Tiến hành đổi code cho từng nhân vật
    for game_enum, uid, nick, gname in targets_to_redeem:
        try:
            await client.redeem_code(code, uid=uid, game=game_enum)
            results.append(f"✅ **{gname}** (`{nick}` - UID: `{uid}`): Đổi mã `{code}` thành công! Quà đã được gửi vào hòm thư ingame.")
        except genshin.errors.AlreadyRedeemed:
            results.append(f"ℹ️ **{gname}** (`{nick}` - UID: `{uid}`): Mã `{code}` đã được nhập trước đó trên nhân vật này.")
        except genshin.errors.RedemptionClaimed:
            results.append(f"ℹ️ **{gname}** (`{nick}` - UID: `{uid}`): Mã đã đạt giới hạn số lần nhận tối đa.")
        except genshin.errors.RedemptionInvalid:
            results.append(f"❌ **{gname}**: Mã `{code}` không hợp lệ hoặc đã hết hạn sử dụng.")
        except genshin.errors.RedeemGameLevelTooLow:
            results.append(f"⚠️ **{gname}** (`{nick}`): Cấp độ nhân vật chưa đủ điều kiện để đổi mã này.")
        except genshin.errors.RedemptionCooldown:
            results.append(f"⏳ **{gname}** (`{nick}`): Thao tác quá nhanh, hệ thống đang cooldown. Vui lòng thử lại sau.")
        except genshin.errors.InvalidCookies:
            results.append(f"⚠️ **{acc_name}**: Phiên đăng nhập cookie đã hết hạn. Vui lòng cập nhật lại cookie hoặc đăng nhập lại.")
        except genshin.errors.GenshinException as ge:
            results.append(f"⚠️ **{gname}** (`{nick}`): {ge.msg or str(ge)}")
        except Exception as ex:
            results.append(f"❌ **{gname}** (`{nick}`): Lỗi kết nối `{ex}`")

        await asyncio.sleep(1.2)

    return results

class SmartCookieModal(discord.ui.Modal, title="🌸 Thiết Lập Cookie HoYoLAB"):
    """Modal nhập cookie thông minh - Hỗ trợ dán bất kỳ định dạng nào."""
    def __init__(self, management_view: Optional[Any] = None, cog_instance: Optional[Any] = None):
        super().__init__(title="🌸 Thiết Lập Cookie HoYoLAB")
        self.management_view = management_view
        self.cog_instance = cog_instance

    account_name = discord.ui.TextInput(
        label="Tên tài khoản gợi nhớ",
        placeholder="Ví dụ: Acc chính, Acc clone, Acc Genshin...",
        required=True,
        max_length=50
    )
    cookie_input = discord.ui.TextInput(
        label="Mã Cookie (Dán toàn bộ cookie / bookmarklet)",
        placeholder="Dán toàn bộ document.cookie, mã từ Bookmarklet hoặc ltoken_v2 / ltuid_v2 vào đây...",
        style=discord.TextStyle.paragraph,
        required=True,
        max_length=4000
    )

    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True, thinking=True)
        user_id = str(interaction.user.id)
        raw_cookie = self.cookie_input.value
        parsed = extract_hoyolab_cookies(raw_cookie)

        if not parsed.get("ltuid_v2") or not parsed.get("ltoken_v2"):
            missing = []
            if not parsed.get("ltuid_v2"):
                missing.append("`ltuid_v2` (ID tài khoản số)")
            if not parsed.get("ltoken_v2"):
                missing.append("`ltoken_v2` (Token đăng nhập)")

            embed = discord.Embed(
                title="❌ Thiếu Thông Tin Cookie",
                description=(
                    f"Bot không thể tìm thấy: {', '.join(missing)} trong nội dung bạn dán.\n\n"
                    "💡 **Lý do & Cách khắc phục:**\n"
                    "• Do `ltoken_v2` được HoYoverse đặt bảo mật **`HttpOnly`**, các công cụ Bookmarklet hoặc `document.cookie` cũ sẽ bị trình duyệt chặn không lấy được.\n"
                    "• **Cách 1 (Khuyên dùng):** Bấm nút **`🔐 Đăng Nhập Tự Động (Hoyo Buddy)`** ngay trên bot để đăng nhập trực tiếp mà không cần lấy cookie!\n"
                    "• **Cách 2 (F12 PC):** Mở [hoyolab.com](https://www.hoyolab.com) -> Nhấn `F12` -> tab **Network** -> `F5` -> bấm 1 request bất kỳ -> copy toàn bộ dòng **`Cookie:`** trong **Request Headers** rồi dán vào đây!"
                ),
                color=discord.Color.red()
            )
            return await interaction.followup.send(embed=embed, ephemeral=True)

        # Chuẩn bị auth dictionary đầy đủ cả v1 và v2
        auth_payload = {
            "ltoken_v2": parsed["ltoken_v2"],
            "ltuid_v2": parsed["ltuid_v2"],
            "ltoken": parsed["ltoken_v2"],
            "ltuid": parsed["ltuid_v2"],
            "account_id": parsed["ltuid_v2"],
            "account_id_v2": parsed["ltuid_v2"],
        }
        if "cookie_token_v2" in parsed:
            auth_payload["cookie_token_v2"] = parsed["cookie_token_v2"]
            auth_payload["cookie_token"] = parsed["cookie_token_v2"]
        if "ltmid_v2" in parsed:
            auth_payload["ltmid_v2"] = parsed["ltmid_v2"]
            auth_payload["account_mid_v2"] = parsed["ltmid_v2"]

        # Kiểm tra tính hợp lệ của cookie với HoYoLAB trước khi lưu
        test_client = genshin.Client(auth_payload, lang="vi-vn")
        try:
            await test_client.get_reward_info(game=genshin.Game.GENSHIN)
        except genshin.InvalidCookies:
            embed_err = discord.Embed(
                title="❌ Cookie Hết Hạn Hoặc Không Hợp Lệ (Lỗi [-100])",
                description=(
                    f"HoYoverse đã từ chối cookie vừa nhập cho **{self.account_name.value}** với thông báo:\n"
                    "`[-100] Phiên đăng nhập hết hiệu lực, vui lòng đăng nhập lại`.\n\n"
                    "🔍 **Nguyên nhân tại sao vừa nhập xong lại báo hết hạn?**\n"
                    "1️⃣ **Bạn vừa bấm \"Đăng xuất\" trên HoYoLAB:** Nếu bạn bấm nút Đăng xuất trên trang web HoYoLAB sau khi copy, hệ thống HoYoverse sẽ **lập tức vô hiệu hóa phiên** của cookie đó!\n"
                    "2️⃣ **Cookie lấy từ Bookmarklet / document.cookie cũ:** Do `ltoken_v2` là `HttpOnly`, copy bằng JavaScript chỉ lấy được token cũ đã hết hạn từ lâu.\n\n"
                    "👉 **Cách khắc phục triệt để:**\n"
                    "• **Cách tốt nhất:** Bấm nút **`🔐 Đăng Nhập Tự Động (Hoyo Buddy)`** ngay trên SakuraBot để bot tự đăng nhập & lấy token mới nhất, không cần đụng F12!\n"
                    "• **Thủ công:** Vào **[hoyolab.com](https://www.hoyolab.com)** (đã đăng nhập) -> Nhấn `F12` -> tab **Network** -> nhấn `F5` -> chọn 1 request bất kỳ -> tìm mục **Request Headers** -> chuột phải dòng **`Cookie:`** -> chọn **Copy value** rồi dán lại vào bot.\n"
                    "*(⚠️ Lưu ý: Sau khi copy, chỉ cần tắt tab trình duyệt, TUYỆT ĐỐI KHÔNG BẤM ĐĂNG XUẤT!)*"
                ),
                color=discord.Color.red()
            )
            return await interaction.followup.send(embed=embed_err, ephemeral=True)
        except Exception:
            pass  # Nếu lỗi mạng tạm thời hoặc server HoYoverse bận, vẫn lưu tài khoản

        cookies = load_cookies()
        if user_id not in cookies:
            cookies[user_id] = []
        elif isinstance(cookies[user_id], dict):
            cookies[user_id] = [cookies[user_id]]

        new_account = {
            "name": self.account_name.value.strip(),
            "ltoken_v2": parsed["ltoken_v2"],
            "ltuid_v2": parsed["ltuid_v2"],
            "auto_checkin": True,  # Mặc định bật auto checkin khi thiết lập thành công
            "auto_redeem": True   # Mặc định bật tự động nhận giftcode mới
        }
        if "cookie_token_v2" in parsed:
            new_account["cookie_token_v2"] = parsed["cookie_token_v2"]
        if "ltmid_v2" in parsed:
            new_account["ltmid_v2"] = parsed["ltmid_v2"]

        # Cập nhật nếu tên tài khoản đã tồn tại
        account_found = False
        for i, acc in enumerate(cookies[user_id]):
            if acc.get("name") == new_account["name"]:
                new_account["auto_checkin"] = acc.get("auto_checkin", True)
                new_account["auto_redeem"] = acc.get("auto_redeem", True)
                cookies[user_id][i] = new_account
                account_found = True
                break
        if not account_found:
            cookies[user_id].append(new_account)

        save_cookies(cookies)

        # Cập nhật cache của Cog
        if self.cog_instance:
            self.cog_instance.cookies_data = cookies
        elif self.management_view and hasattr(self.management_view, "cog_instance"):
            self.management_view.cog_instance.cookies_data = cookies

        # Cập nhật embed quản lý nếu view còn mở
        if self.management_view and hasattr(self.management_view, "update_embed_from_interaction"):
            try:
                await self.management_view.update_embed_from_interaction(interaction)
            except Exception:
                pass

        # Truy vấn các nhân vật UID liên kết
        game_roles = []
        try:
            game_roles = await test_client.get_game_accounts()
        except Exception:
            pass

        if len(game_roles) > 1 and self.cog_instance:
            return await self.cog_instance.show_uid_choice_menu(interaction, new_account, cookies[user_id], management_view=self.management_view)
        elif len(game_roles) == 1:
            r = game_roles[0]
            new_account["game_uid"] = str(r.uid)
            new_account["game_biz"] = r.game_biz
            new_account["nickname"] = r.nickname
            new_account["server_name"] = r.server_name
            new_account["level"] = r.level
            save_cookies(cookies)

        embed = discord.Embed(
            title="🌸 Lưu Cookie HoYoLAB Thành Công!",
            description=(
                f"Đã lưu thông tin cho tài khoản **{self.account_name.value}**.\n\n"
                f"• **HoYoLAB UID:** `{parsed['ltuid_v2']}`\n"
                f"• **Tự động điểm danh:** 🟢 Đang BẬT (01:00 AM mỗi ngày)\n"
                f"• **Trạng thái:** ✅ **Đã kết nối HoYoLAB thành công!** Cookie hoàn toàn hợp lệ.\n\n"
                "Bạn có thể dùng nút `✨ Điểm danh ngay` hoặc gõ `/hoyolab daily checkin` để nhận quà hôm nay!"
            ),
            color=discord.Color.green()
        )
        await interaction.followup.send(embed=embed, ephemeral=True)

class HoyoEmailOtpModal(discord.ui.Modal, title="📩 Nhập Mã Xác Nhận Email HoYoverse"):
    """
    Modal tiếp nhận mã xác nhận OTP 6 số do HoYoverse gửi về Email.
    """
    def __init__(self, session_id: str, user_id: str):
        super().__init__(title="📩 Nhập Mã Xác Nhận HoYoverse")
        self.session_id = session_id
        self.user_id = user_id

    otp_code = discord.ui.TextInput(
        label="Mã xác thực HoYoverse (6 chữ số)",
        placeholder="Nhập mã 6 chữ số gửi về email của bạn (VD: 123456)...",
        min_length=4,
        max_length=10,
        required=True
    )

    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True, thinking=True)
        code = self.otp_code.value.strip()
        resolved = resolve_otp_session(self.session_id, code) or resolve_otp_session(str(self.user_id), code)
        if resolved:
            await interaction.followup.send(
                "✅ **Đã tiếp nhận mã OTP!** SakuraBot đang gửi xác thực tới máy chủ HoYoverse, vui lòng chờ trong giây lát...",
                ephemeral=True
            )
        else:
            await interaction.followup.send(
                "⚠️ **Phiên xác thực Email đã hết hạn hoặc không tồn tại.** Vui lòng thử đăng nhập lại từ đầu!",
                ephemeral=True
            )

class HoyoEmailOtpView(discord.ui.View):
    """
    View chứa nút bấm mở Modal nhập mã OTP xác thực Email HoYoverse và link mở web nếu muốn.
    """
    def __init__(self, session_id: str, author_id: int, captcha_url: Optional[str] = None):
        super().__init__(timeout=300)
        self.session_id = session_id
        self.author_id = author_id

        if captcha_url:
            self.add_item(discord.ui.Button(
                label="🌐 Trang Xác Minh Web",
                style=discord.ButtonStyle.link,
                emoji="🧩",
                url=captcha_url
            ))

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id != self.author_id:
            await interaction.response.send_message("❌ Bạn không phải người khởi tạo phiên đăng nhập này!", ephemeral=True)
            return False
        return True

    @discord.ui.button(label="📩 Nhập Mã Xác Nhận Email (OTP)", style=discord.ButtonStyle.primary, emoji="📩", row=0)
    async def open_otp_modal(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(HoyoEmailOtpModal(session_id=self.session_id, user_id=str(self.author_id)))

class HoyoBuddyLoginModal(discord.ui.Modal, title="🔐 Đăng Nhập HoYoverse Tự Động"):
    """
    Modal đăng nhập bằng tài khoản HoYoverse (phong cách Hoyo Buddy).
    Thực hiện xác thực trực tiếp qua API HoYoverse với hỗ trợ giải Geetest Captcha qua Web
    và xác thực 2 bước (Email OTP) tự động.
    """
    def __init__(self, management_view: Optional[Any] = None, cog_instance: Optional[Any] = None):
        super().__init__(title="🔐 Đăng Nhập HoYoverse Tự Động")
        self.management_view = management_view
        self.cog_instance = cog_instance

    account_name = discord.ui.TextInput(
        label="Tên tài khoản gợi nhớ",
        placeholder="Ví dụ: Acc chính, Acc phụ...",
        required=True,
        max_length=50
    )
    credentials = discord.ui.TextInput(
        label="Email hoặc Tên người dùng HoYoverse",
        placeholder="Nhập email hoặc username tài khoản HoYoverse của bạn...",
        required=True,
        max_length=100
    )
    password = discord.ui.TextInput(
        label="Mật khẩu tài khoản HoYoverse",
        placeholder="Mật khẩu của bạn (được mã hóa RSA khi gửi)...",
        style=discord.TextStyle.short,
        required=True,
        max_length=100
    )

    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True, thinking=True)
        user_id = str(interaction.user.id)
        account_str = self.credentials.value.strip()
        pwd_str = self.password.value.strip()
        acc_name = self.account_name.value.strip()

        # Tạo device_id đồng nhất theo user_id để tránh HoYoverse bắt xác thực lại liên tục (chuẩn 16 ký tự)
        device_id = hashlib.md5(f"sakura_hoyo_{user_id}".encode()).hexdigest()[:16]
        client = genshin.Client(lang="vi-vn")

        try:
            # 1. Thử đăng nhập bằng endpoint chính thức của app HoYoverse (hỗ trợ RSA và DS)
            res = await client._app_login(
                account_str,
                pwd_str,
                device_id=device_id
            )

            session_id = secrets.token_urlsafe(16)
            captcha_url = f"{WEB_BASE_URL.rstrip('/')}/hoyo/captcha?session={session_id}"

            # 2. Xử lý trường hợp HoYoverse yêu cầu giải Geetest Captcha
            if isinstance(res, (genshin.models.SessionMMT, genshin.models.SessionMMTv4)):
                loop = asyncio.get_running_loop()
                captcha_future = loop.create_future()
                create_captcha_session(session_id, {
                    "user_id": user_id,
                    "mmt": res,
                    "is_v4": isinstance(res, genshin.models.SessionMMTv4),
                    "future": captcha_future,
                    "account_str": account_str,
                    "pwd_str": pwd_str,
                    "device_id": device_id
                })

                captcha_view = discord.ui.View(timeout=300)
                captcha_view.add_item(discord.ui.Button(
                    label="🧩 Mở Trang Giải Captcha",
                    style=discord.ButtonStyle.link,
                    emoji="🧩",
                    url=captcha_url
                ))

                embed_captcha = discord.Embed(
                    title="🧩 HoYoverse Yêu Cầu Xác Minh Captcha",
                    description=(
                        "HoYoverse đã kích hoạt cơ chế bảo vệ tài khoản và yêu cầu **kéo khớp mảnh ghép Captcha**.\n\n"
                        "👉 **Các bước thực hiện:**\n"
                        f"1️⃣ Nhấp vào nút **[🧩 Mở Trang Giải Captcha]** bên dưới để mở giao diện web SakuraBot.\n"
                        "2️⃣ Kéo trượt mảnh ghép khớp vào ô trống trên hình ảnh.\n"
                        "3️⃣ Sau khi kéo thành công trên web, SakuraBot sẽ tự động tiếp tục quá trình đăng nhập!\n\n"
                        "⏱️ *Phiên giải Captcha có hiệu lực trong **5 phút**.*"
                    ),
                    color=discord.Color.gold()
                )
                await interaction.followup.send(embed=embed_captcha, view=captcha_view, ephemeral=True)

                try:
                    captcha_data = await asyncio.wait_for(captcha_future, timeout=300.0)
                except asyncio.TimeoutError:
                    return await interaction.followup.send("⏰ **Đã hết thời gian chờ giải Captcha (5 phút).** Vui lòng thử lại!", ephemeral=True)

                # Chuyển đổi dữ liệu xác thực Captcha từ web về MMTResult
                if isinstance(res, genshin.models.SessionMMTv4):
                    mmt_result = genshin.models.SessionMMTv4Result(
                        session_id=res.session_id,
                        captcha_id=captcha_data.get("captcha_id") or getattr(res, "captcha_id", ""),
                        lot_number=captcha_data.get("lot_number", ""),
                        pass_token=captcha_data.get("pass_token", ""),
                        gen_time=captcha_data.get("gen_time", ""),
                        captcha_output=captcha_data.get("captcha_output", "")
                    )
                else:
                    mmt_result = genshin.models.SessionMMTResult(
                        session_id=res.session_id,
                        geetest_challenge=captcha_data.get("geetest_challenge", ""),
                        geetest_validate=captcha_data.get("geetest_validate", ""),
                        geetest_seccode=captcha_data.get("geetest_seccode", "")
                    )

                # Đăng nhập lại kèm kết quả giải Captcha
                try:
                    res = await client._app_login(
                        account_str,
                        pwd_str,
                        device_id=device_id,
                        mmt_result=mmt_result
                    )
                except (genshin.errors.GeetestFailed, genshin.errors.GenshinException) as ge_err:
                    err_txt = str(ge_err)
                    if isinstance(ge_err, genshin.errors.GeetestFailed) or "verification code" in err_txt.lower():
                        msg = (
                            "⚠️ **Mảnh ghép Captcha không khớp hoặc đã hết hạn (Verification code failed)!**\n\n"
                            "💡 **Nguyên nhân:**\n"
                            "• Mảnh ghép bị kéo lệch hoặc kéo quá thời gian chờ (hết hạn sau 60 giây).\n"
                            "• HoYoverse từ chối kết quả kéo và yêu cầu giải lại.\n\n"
                            "👉 **Giải pháp tốt nhất:** Bạn nên dùng lệnh **`/hoyolab quickcode` (Bookmarklet 1 chạm)** — copy cookie trực tiếp từ trình duyệt trong 1 giây mà KHÔNG cần giải Captcha hay nhập mật khẩu!"
                        )
                    else:
                        msg = f"❌ **Lỗi đăng nhập sau khi giải Captcha:** {ge_err}"
                    update_captcha_session(session_id, {"stage": "error", "error": msg})
                    return await interaction.followup.send(msg, ephemeral=True)

            # 3. Xử lý trường hợp HoYoverse yêu cầu xác thực 2 bước qua Email (ActionTicket)
            if isinstance(res, genshin.models.ActionTicket):
                try:
                    email_res = await client._send_verification_email(res)
                except Exception as mail_err:
                    update_captcha_session(session_id, {"stage": "error", "error": str(mail_err)})
                    return await interaction.followup.send(f"❌ **Không thể yêu cầu HoYoverse gửi mã Email:** {mail_err}", ephemeral=True)

                # HoYoverse có thể yêu cầu giải tiếp Geetest Captcha để gửi mã xác nhận Email (anti-spam retcode -3101)
                if isinstance(email_res, (genshin.models.SessionMMT, genshin.models.SessionMMTv4)):
                    loop = asyncio.get_running_loop()
                    email_captcha_future = loop.create_future()
                    if not get_captcha_session(session_id):
                        create_captcha_session(session_id, {
                            "user_id": user_id,
                            "stage": "email_captcha",
                            "mmt": email_res,
                            "is_v4": isinstance(email_res, genshin.models.SessionMMTv4),
                            "future": email_captcha_future,
                            "account_str": account_str,
                            "pwd_str": pwd_str,
                            "device_id": device_id
                        })
                    else:
                        update_captcha_session(session_id, {
                            "stage": "email_captcha",
                            "mmt": email_res,
                            "is_v4": isinstance(email_res, genshin.models.SessionMMTv4),
                            "future": email_captcha_future
                        })

                    embed_email_captcha = discord.Embed(
                        title="🧩 HoYoverse Yêu Cầu Xác Minh Gửi Mã Email (Bước 2/2)",
                        description=(
                            "HoYoverse yêu cầu **kéo thêm 1 mảnh ghép Captcha** để bảo vệ và gửi mã OTP về Email của bạn.\n\n"
                            "👉 **Nếu bạn đang mở trang Web**, trang web sẽ tự động chuyển sang mảnh ghép này!\n"
                            f"👉 Hoặc bấm nút **[🧩 Mở Trang Giải Captcha]** bên dưới.\n\n"
                            "⏱️ *Phiên giải Captcha có hiệu lực trong **5 phút**.*"
                        ),
                        color=discord.Color.gold()
                    )
                    captcha_view = discord.ui.View(timeout=300)
                    captcha_view.add_item(discord.ui.Button(
                        label="🧩 Mở Trang Giải Captcha",
                        style=discord.ButtonStyle.link,
                        emoji="🧩",
                        url=captcha_url
                    ))
                    await interaction.followup.send(embed=embed_email_captcha, view=captcha_view, ephemeral=True)

                    try:
                        email_captcha_data = await asyncio.wait_for(email_captcha_future, timeout=300.0)
                    except asyncio.TimeoutError:
                        return await interaction.followup.send("⏰ **Đã hết thời gian chờ giải Captcha gửi Email (5 phút).** Vui lòng thử lại!", ephemeral=True)

                    if isinstance(email_res, genshin.models.SessionMMTv4):
                        email_mmt_result = genshin.models.SessionMMTv4Result(
                            session_id=email_res.session_id,
                            captcha_id=email_captcha_data.get("captcha_id") or getattr(email_res, "captcha_id", ""),
                            lot_number=email_captcha_data.get("lot_number", ""),
                            pass_token=email_captcha_data.get("pass_token", ""),
                            gen_time=email_captcha_data.get("gen_time", ""),
                            captcha_output=email_captcha_data.get("captcha_output", "")
                        )
                    else:
                        email_mmt_result = genshin.models.SessionMMTResult(
                            session_id=email_res.session_id,
                            geetest_challenge=email_captcha_data.get("geetest_challenge", ""),
                            geetest_validate=email_captcha_data.get("geetest_validate", ""),
                            geetest_seccode=email_captcha_data.get("geetest_seccode", "")
                        )

                    try:
                        email_res2 = await client._send_verification_email(res, mmt_result=email_mmt_result)
                        if isinstance(email_res2, (genshin.models.SessionMMT, genshin.models.SessionMMTv4)):
                            update_captcha_session(session_id, {"stage": "error", "error": "Mảnh ghép Captcha không khớp"})
                            return await interaction.followup.send("❌ **Mảnh ghép Captcha không khớp.** Vui lòng thử lại!", ephemeral=True)
                    except Exception as mail_err2:
                        update_captcha_session(session_id, {"stage": "error", "error": str(mail_err2)})
                        return await interaction.followup.send(f"❌ **Lỗi khi gửi email sau khi giải Captcha:** {mail_err2}", ephemeral=True)

                # Khi đã gửi email thành công -> Cập nhật session sang stage "otp_pending"
                if not get_captcha_session(session_id):
                    create_captcha_session(session_id, {
                        "user_id": user_id,
                        "stage": "otp_pending",
                        "account_str": account_str,
                        "pwd_str": pwd_str,
                        "device_id": device_id
                    })
                else:
                    update_captcha_session(session_id, {"stage": "otp_pending"})

                loop = asyncio.get_running_loop()
                otp_future = loop.create_future()
                create_otp_session(session_id, {
                    "user_id": user_id,
                    "future": otp_future,
                    "ticket": res
                })

                otp_view = HoyoEmailOtpView(session_id=session_id, author_id=interaction.user.id, captcha_url=captcha_url)
                embed_otp = discord.Embed(
                    title="📩 Xác Minh Email Bảo Mật HoYoverse",
                    description=(
                        "HoYoverse đã gửi một mã xác nhận gồm **6 chữ số** đến địa chỉ Email liên kết của tài khoản này.\n\n"
                        "📧 **Vui lòng kiểm tra Hộp thư đến (hoặc thư mục Quảng cáo / Spam / Thư rác).**\n"
                        "👉 Bấm nút **[📩 Nhập Mã Xác Nhận Email (OTP)]** bên dưới (hoặc nhập trực tiếp trên web nếu đang mở) để hoàn tất đăng nhập!\n\n"
                        "⏱️ *Mã OTP có hiệu lực trong vòng **5 phút**.*"
                    ),
                    color=discord.Color.blue()
                )
                await interaction.followup.send(embed=embed_otp, view=otp_view, ephemeral=True)

                try:
                    otp_code = await asyncio.wait_for(otp_future, timeout=300.0)
                except asyncio.TimeoutError:
                    return await interaction.followup.send("⏰ **Đã hết thời gian chờ mã OTP Email (5 phút).** Vui lòng thử lại!", ephemeral=True)

                # Xác thực mã OTP và chốt phiên đăng nhập
                try:
                    await client._verify_email(otp_code, res)
                    res = await client._app_login(
                        account_str,
                        pwd_str,
                        device_id=device_id,
                        ticket=res
                    )
                    update_captcha_session(session_id, {"stage": "success"})
                except (genshin.errors.WrongOTP, genshin.errors.GenshinException) as otp_err:
                    err_txt = str(otp_err)
                    if isinstance(otp_err, genshin.errors.WrongOTP) or "verification code" in err_txt.lower():
                        msg = (
                            "❌ **Mã xác nhận Email (OTP) không chính xác hoặc đã hết hạn!**\n\n"
                            "💡 **Lưu ý:**\n"
                            "• HoYoverse chỉ chấp nhận mã trong email mới nhất (các mã cũ trước đó sẽ bị vô hiệu hóa).\n"
                            "• Mã OTP chỉ có hiệu lực trong vòng 5 phút."
                        )
                    else:
                        msg = f"❌ **Lỗi xác thực Email:** {otp_err}"
                    update_captcha_session(session_id, {"stage": "error", "error": msg})
                    return await interaction.followup.send(msg, ephemeral=True)

            # 4. Khi đăng nhập thành công (nhận được AppLoginResult chứa stoken & ltuid)
            if isinstance(res, genshin.models.AppLoginResult):
                cookies_to_exchange = {
                    "stoken": res.stoken,
                    "ltuid_v2": res.ltuid_v2,
                    "ltmid_v2": res.ltmid_v2,
                    "account_id_v2": res.account_id_v2,
                }
                try:
                    fetched = await fetch_cookie_with_stoken_v2(cookies_to_exchange, token_types=[2, 4])
                except Exception:
                    fetched = {}

                ltoken = fetched.get("ltoken_v2") or res.stoken
                cookie_token = fetched.get("cookie_token_v2", "")
                uid_val = str(res.ltuid_v2 or res.account_id_v2 or "")

                cookies = load_cookies()
                if user_id not in cookies:
                    cookies[user_id] = []
                elif isinstance(cookies[user_id], dict):
                    cookies[user_id] = [cookies[user_id]]

                new_account = {
                    "name": acc_name,
                    "ltoken_v2": ltoken,
                    "ltuid_v2": uid_val,
                    "cookie_token_v2": cookie_token,
                    "stoken_v2": res.stoken,
                    "ltmid_v2": res.ltmid_v2,
                    "auto_checkin": True,
                    "auto_redeem": True
                }

                account_found = False
                for i, acc in enumerate(cookies[user_id]):
                    if acc.get("name") == new_account["name"]:
                        cookies[user_id][i] = new_account
                        account_found = True
                        break
                if not account_found:
                    cookies[user_id].append(new_account)

                save_cookies(cookies)
                if self.cog_instance:
                    self.cog_instance.cookies_data = cookies
                elif self.management_view and hasattr(self.management_view, "cog_instance"):
                    self.management_view.cog_instance.cookies_data = cookies

                if self.management_view and hasattr(self.management_view, "update_embed_from_interaction"):
                    try:
                        await self.management_view.update_embed_from_interaction(interaction)
                    except Exception:
                        pass

                # Truy vấn danh sách UID game liên kết
                game_roles = []
                try:
                    query_client = genshin.Client({"ltoken_v2": ltoken, "ltuid_v2": uid_val}, lang="vi-vn")
                    game_roles = await query_client.get_game_accounts()
                except Exception:
                    pass

                if len(game_roles) > 1 and self.cog_instance:
                    return await self.cog_instance.show_uid_choice_menu(interaction, new_account, cookies[user_id], management_view=self.management_view)
                elif len(game_roles) == 1:
                    r = game_roles[0]
                    new_account["game_uid"] = str(r.uid)
                    new_account["game_biz"] = r.game_biz
                    new_account["nickname"] = r.nickname
                    new_account["server_name"] = r.server_name
                    new_account["level"] = r.level
                    save_cookies(cookies)

                embed_success = discord.Embed(
                    title="🎉 Đăng Nhập HoYoverse Thành Công!",
                    description=(
                        f"Đã tự động xác thực và liên kết tài khoản **{acc_name}** thành công!\n\n"
                        f"• **HoYoLAB UID:** `{uid_val}`\n"
                        f"• **Tự động điểm danh:** 🟢 Đang BẬT (01:00 AM mỗi ngày)\n"
                        f"• **Bảo mật:** Đã vượt qua Captcha & Email OTP thành công!\n\n"
                        "Bạn có thể dùng nút `✨ Điểm danh ngay` hoặc gõ `/hoyolab daily checkin` để nhận quà hôm nay!"
                    ),
                    color=discord.Color.green()
                )
                return await interaction.followup.send(embed=embed_success, ephemeral=True)
            else:
                return await interaction.followup.send("⚠️ **Không thể hoàn tất đăng nhập.** Vui lòng thử lại hoặc sử dụng tính năng **Lấy Mã Nhanh (Bookmarklet)**!", ephemeral=True)

        except genshin.errors.AccountLoginFail:
            await interaction.followup.send("❌ **Sai tài khoản hoặc mật khẩu HoYoverse.** Vui lòng kiểm tra lại thông tin đăng nhập!", ephemeral=True)
        except genshin.errors.AccountDoesNotExist:
            await interaction.followup.send("❌ **Tài khoản HoYoverse này không tồn tại.** Vui lòng kiểm tra lại email/username!", ephemeral=True)
        except genshin.errors.AccountHasLocked:
            await interaction.followup.send("⚠️ **Tài khoản của bạn đang bị khóa bảo vệ tạm thời.** Vui lòng đăng nhập trên website HoYoverse để mở khóa!", ephemeral=True)
        except (genshin.errors.GeetestFailed, genshin.errors.WrongOTP) as g_err:
            await interaction.followup.send(
                "⚠️ **Mảnh ghép Captcha hoặc mã xác thực không hợp lệ (Verification code failed)!**\n"
                "👉 Vui lòng kéo lại chính xác hoặc dùng lệnh `/hoyolab quickcode` (Bookmarklet 1 chạm) để liên kết nhanh.",
                ephemeral=True
            )
        except genshin.errors.GenshinException as ge:
            err_msg = ge.msg if hasattr(ge, 'msg') else str(ge)
            if "verification code" in err_msg.lower():
                await interaction.followup.send(
                    "⚠️ **Mảnh ghép Captcha hoặc mã xác thực không hợp lệ (Verification code failed)!**\n\n"
                    "💡 **Nguyên nhân phổ biến:**\n"
                    "1. Kéo mảnh ghép bị lệch hoặc quá thời gian chờ (hết hạn sau 60 giây).\n"
                    "2. Hoặc mã OTP Email nhập vào là mã cũ của lần gửi trước.\n\n"
                    "👉 **Giải pháp tốt nhất:** Sử dụng tính năng **`/hoyolab quickcode` (Bookmarklet 1 chạm)** — không cần mật khẩu và không cần giải Captcha!",
                    ephemeral=True
                )
            else:
                await interaction.followup.send(f"❌ **Lỗi xác thực HoYoverse:** {err_msg}", ephemeral=True)
        except ModuleNotFoundError as e:
            if "rsa" in str(e).lower():
                embed = discord.Embed(
                    title="📦 Máy Chủ Thiếu Thư Viện 'rsa'",
                    description=(
                        "Để mã hóa mật khẩu gửi tới HoYoverse, môi trường Python trên máy chủ cần cài đặt thư viện `rsa`.\n\n"
                        "🔧 **Cách khắc phục trên máy chủ (Terminal / Console Hosting):**\n"
                        "```bash\npip install rsa\n```\n"
                        "*(Hoặc thêm dòng `rsa` vào file `requirements.txt` rồi khởi động lại bot)*\n\n"
                        "⚡ **Giải pháp thay thế tức thì (Không cần cài thư viện & Không cần mật khẩu):**\n"
                        "Gõ lệnh `/hoyolab quickcode` hoặc dùng **Bookmarklet 1 chạm** để sao chép cookie HoYoLAB trực tiếp trên trình duyệt của bạn!"
                    ),
                    color=discord.Color.orange()
                )
                await interaction.followup.send(embed=embed, ephemeral=True)
            else:
                await interaction.followup.send(f"❌ **Lỗi thiếu thư viện Python:** `{e}`", ephemeral=True)
        except Exception as e:
            await interaction.followup.send(f"❌ **Lỗi khi kết nối HoYoverse:** `{e}`", ephemeral=True)

# Thông tin hiển thị cho các dòng game của HoYoverse
GAME_BIZ_INFO = {
    "hk4e_global": ("Genshin Impact", "🌸", "genshin"),
    "hk4e_cn": ("Genshin Impact (CN)", "🌸", "genshin"),
    "hkrpg_global": ("Honkai: Star Rail", "🚂", "hsr"),
    "hkrpg_cn": ("Honkai: Star Rail (CN)", "🚂", "hsr"),
    "nap_global": ("Zenless Zone Zero", "⚡", "zzz"),
    "nap_cn": ("Zenless Zone Zero (CN)", "⚡", "zzz"),
    "bh3_global": ("Honkai Impact 3rd", "⚔️", "bh3"),
    "bh3_cn": ("Honkai Impact 3rd (CN)", "⚔️", "bh3"),
}

class UIDChoiceSelect(discord.ui.Select):
    """Menu chọn UID cụ thể hoặc lưu tất cả UID khi tài khoản có nhiều nhân vật."""
    def __init__(self, user_id: str, base_account: dict, game_accounts: list, management_view: Optional[Any] = None, cog_instance: Optional[Any] = None):
        self.user_id = user_id
        self.base_account = base_account
        self.game_accounts = game_accounts
        self.management_view = management_view
        self.cog_instance = cog_instance

        options = [
            discord.SelectOption(
                label=f"✨ Lưu & Điểm danh TẤT CẢ ({len(game_accounts)} UID)",
                value="all_uids",
                emoji="✨",
                description="Tự động điểm danh cho mọi nhân vật"
            )
        ]
        for a in game_accounts[:24]:
            biz_name, biz_emoji, _ = GAME_BIZ_INFO.get(a.game_biz, (a.game_biz, "🎮", "unknown"))
            options.append(
                discord.SelectOption(
                    label=f"{biz_name}: {a.nickname}"[:100],
                    value=f"{a.uid}_{a.game_biz}",
                    emoji=biz_emoji,
                    description=f"UID: {a.uid} | {a.server_name} (Lv.{a.level})"[:100]
                )
            )

        super().__init__(placeholder="Chọn UID muốn sử dụng hoặc Lưu tất cả...", options=options, row=0)

    async def callback(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True, thinking=True)
        selected_val = self.values[0]
        cookies = load_cookies()
        user_list = cookies.get(self.user_id, [])

        if selected_val == "all_uids":
            added_names = []
            user_list = [acc for acc in user_list if acc.get("name") != self.base_account.get("name")]

            for a in self.game_accounts:
                biz_name, biz_emoji, game_key = GAME_BIZ_INFO.get(a.game_biz, (a.game_biz, "🎮", "genshin"))
                sub_name = f"{self.base_account.get('name')} - {biz_name} ({a.nickname})"
                sub_acc = dict(self.base_account)
                sub_acc["name"] = sub_name
                sub_acc["game_uid"] = str(a.uid)
                sub_acc["game_biz"] = a.game_biz
                sub_acc["game_key"] = game_key
                sub_acc["nickname"] = a.nickname
                sub_acc["server_name"] = a.server_name
                sub_acc["level"] = a.level
                sub_acc["auto_checkin"] = True

                found = False
                for i, existing in enumerate(user_list):
                    if existing.get("name") == sub_name or (existing.get("ltuid_v2") == sub_acc["ltuid_v2"] and existing.get("game_uid") == str(a.uid)):
                        user_list[i] = sub_acc
                        found = True
                        break
                if not found:
                    user_list.append(sub_acc)
                added_names.append(f"{biz_emoji} `{a.nickname}` (UID: `{a.uid}` - {a.server_name})")

            cookies[self.user_id] = user_list
            save_cookies(cookies)

            if self.cog_instance:
                self.cog_instance.cookies_data = cookies
            if self.management_view and hasattr(self.management_view, "update_embed_from_interaction"):
                try:
                    await self.management_view.update_embed_from_interaction(interaction)
                except Exception:
                    pass

            embed = discord.Embed(
                title="🎉 Đã Lưu Tất Cả UID Thành Công!",
                description=(
                    f"Đã lưu thành công **{len(self.game_accounts)} UID nhân vật** vào hệ thống SakuraBot:\n\n"
                    + "\n".join(added_names)
                    + "\n\n🟢 **Tất cả UID đều đã được bật tự động điểm danh hàng ngày!**"
                ),
                color=discord.Color.green()
            )
            await interaction.followup.send(embed=embed, ephemeral=True)

        else:
            parts = selected_val.split("_", 1)
            target_uid = parts[0]
            target_biz = parts[1] if len(parts) > 1 else ""
            chosen_role = next((a for a in self.game_accounts if str(a.uid) == target_uid and (not target_biz or a.game_biz == target_biz)), None)
            if not chosen_role:
                return await interaction.followup.send("❌ Không tìm thấy thông tin UID đã chọn.", ephemeral=True)

            biz_name, biz_emoji, game_key = GAME_BIZ_INFO.get(chosen_role.game_biz, (chosen_role.game_biz, "🎮", "genshin"))
            acc_name = self.base_account.get("name")

            for acc in user_list:
                if acc.get("name") == acc_name or acc.get("ltuid_v2") == self.base_account.get("ltuid_v2"):
                    acc["game_uid"] = str(chosen_role.uid)
                    acc["game_biz"] = chosen_role.game_biz
                    acc["game_key"] = game_key
                    acc["nickname"] = chosen_role.nickname
                    acc["server_name"] = chosen_role.server_name
                    acc["level"] = chosen_role.level
                    break

            cookies[self.user_id] = user_list
            save_cookies(cookies)

            if self.cog_instance:
                self.cog_instance.cookies_data = cookies
            if self.management_view and hasattr(self.management_view, "update_embed_from_interaction"):
                try:
                    await self.management_view.update_embed_from_interaction(interaction)
                except Exception:
                    pass

            embed = discord.Embed(
                title="✅ Đã Chọn UID Game Thành Công!",
                description=(
                    f"Đã gán nhân vật hoạt động cho tài khoản **{acc_name}**:\n\n"
                    f"• **Game:** {biz_emoji} **{biz_name}**\n"
                    f"• **Tên nhân vật:** `{chosen_role.nickname}`\n"
                    f"• **UID:** `{chosen_role.uid}`\n"
                    f"• **Cấp độ:** `Lv.{chosen_role.level}`\n"
                    f"• **Máy chủ:** `{chosen_role.server_name}`\n\n"
                    "🟢 Hệ thống sẽ ưu tiên sử dụng UID này khi kiểm tra và điểm danh!"
                ),
                color=discord.Color.green()
            )
            await interaction.followup.send(embed=embed, ephemeral=True)

class UIDChoiceView(discord.ui.View):
    """View hiển thị danh sách UID để người dùng lựa chọn."""
    def __init__(self, user_id: str, base_account: dict, game_accounts: list, management_view: Optional[Any] = None, cog_instance: Optional[Any] = None):
        super().__init__(timeout=180)
        self.user_id = user_id
        self.add_item(UIDChoiceSelect(user_id, base_account, game_accounts, management_view, cog_instance))

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if str(interaction.user.id) != str(self.user_id):
            await interaction.response.send_message("❌ Bạn không phải chủ sở hữu tài khoản này!", ephemeral=True)
            return False
        return True

class AccountSelectForUIDView(discord.ui.View):
    """View cho phép chọn tài khoản HoYoLAB để quản lý / chọn UID game."""
    def __init__(self, accounts: list, author_id: int, management_view: Optional[Any] = None, cog_instance: Optional[Any] = None):
        super().__init__(timeout=60)
        self.accounts = accounts
        self.author_id = author_id
        self.management_view = management_view
        self.cog_instance = cog_instance

        options = [
            discord.SelectOption(
                label=acc.get("name", f"Tài khoản #{i+1}")[:100],
                value=acc.get("name"),
                description=f"UID HoYoLAB: {acc.get('ltuid_v2')}"[:100]
            )
            for i, acc in enumerate(accounts[:25])
        ]
        self.select_menu = discord.ui.Select(placeholder="Chọn tài khoản muốn xem / chọn UID game...", options=options, row=0)
        self.select_menu.callback = self.on_select
        self.add_item(self.select_menu)

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        return interaction.user.id == self.author_id

    async def on_select(self, interaction: discord.Interaction):
        selected_name = self.select_menu.values[0]
        acc = next((a for a in self.accounts if a.get("name") == selected_name), None)
        if not acc:
            return await interaction.response.send_message("❌ Không tìm thấy tài khoản.", ephemeral=True)
        await interaction.response.defer(ephemeral=True, thinking=True)
        await self.cog_instance.show_uid_choice_menu(interaction, acc, self.accounts, management_view=self.management_view)

class AccountSelect(discord.ui.Select):
    """Menu chọn tài khoản để thực hiện hành động."""
    def __init__(self, accounts: list, placeholder: str):
        options = [
            discord.SelectOption(
                label=acc.get("name", f"Tài khoản #{i+1}")[:100],
                value=acc.get("name"),
                description=f"UID: {acc.get('ltuid_v2')}"[:100]
            ) for i, acc in enumerate(accounts)
        ]
        super().__init__(placeholder=placeholder, options=options)

class ToggleView(discord.ui.View):
    """View bật/tắt tính năng auto checkin cho từng tài khoản."""
    def __init__(self, accounts: list, author_id: int, management_view: Optional[Any] = None, cog_instance: Optional[Any] = None):
        super().__init__(timeout=60)
        self.author_id = author_id
        self.management_view = management_view
        self.cog_instance = cog_instance

        options = [
            discord.SelectOption(
                label=acc.get("name", f"Tài khoản #{i+1}")[:100],
                value=acc.get("name"),
                description=f"Hiện tại: {'BẬT' if acc.get('auto_checkin') else 'TẮT'} | UID: {acc.get('ltuid_v2')}"[:100],
                default=bool(acc.get("auto_checkin", False))
            ) for i, acc in enumerate(accounts)
        ]
        self.select_menu = discord.ui.Select(
            placeholder="Chọn các tài khoản muốn BẬT tự động điểm danh...",
            options=options,
            min_values=0,
            max_values=len(options)
        )
        self.add_item(self.select_menu)

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        return interaction.user.id == self.author_id

    @discord.ui.button(label="Lưu Cài Đặt", style=discord.ButtonStyle.green, emoji="💾", row=1)
    async def save_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        selected_accounts = self.select_menu.values
        cookies = load_cookies()
        user_accounts = cookies.get(str(self.author_id), [])

        for acc in user_accounts:
            acc["auto_checkin"] = (acc.get("name") in selected_accounts)

        save_cookies(cookies)
        if self.cog_instance:
            self.cog_instance.cookies_data = cookies
        elif self.management_view and hasattr(self.management_view, "cog_instance"):
            self.management_view.cog_instance.cookies_data = cookies

        if self.management_view and hasattr(self.management_view, "update_embed_from_interaction"):
            try:
                await self.management_view.update_embed_from_interaction(interaction)
            except Exception:
                pass

        enabled_names = ", ".join([f"`{n}`" for n in selected_accounts]) if selected_accounts else "Không có (Đã tắt tất cả)"
        embed = discord.Embed(
            title="✅ Cập Nhật Tự Động Điểm Danh",
            description=f"Đã lưu cài đặt tự động điểm danh hàng ngày.\n\n• **Tài khoản đang bật:** {enabled_names}\n• **Giờ chạy:** 01:00 AM (giờ Việt Nam) mỗi ngày.",
            color=discord.Color.green()
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)
        self.stop()

class DeleteAccountView(discord.ui.View):
    """View chọn tài khoản cần xóa."""
    def __init__(self, accounts: list, author_id: int, management_view: Optional[Any] = None, cog_instance: Optional[Any] = None):
        super().__init__(timeout=60)
        self.author_id = author_id
        self.management_view = management_view
        self.cog_instance = cog_instance

        self.select_menu = AccountSelect(accounts, "Chọn tài khoản bạn muốn xóa...")
        self.select_menu.callback = self.select_callback
        self.add_item(self.select_menu)

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        return interaction.user.id == self.author_id

    async def select_callback(self, interaction: discord.Interaction):
        account_name_to_delete = self.select_menu.values[0]
        cookies = load_cookies()
        user_accounts = cookies.get(str(self.author_id), [])

        account_found = False
        for acc in list(user_accounts):
            if acc.get("name") == account_name_to_delete:
                user_accounts.remove(acc)
                account_found = True
                break

        if account_found:
            save_cookies(cookies)
            if self.cog_instance:
                self.cog_instance.cookies_data = cookies
            elif self.management_view and hasattr(self.management_view, "cog_instance"):
                self.management_view.cog_instance.cookies_data = cookies

            if self.management_view and hasattr(self.management_view, "update_embed_from_interaction"):
                try:
                    await self.management_view.update_embed_from_interaction(interaction)
                except Exception:
                    pass

            await interaction.response.send_message(f"✅ Đã xóa thành công tài khoản **{account_name_to_delete}**.", ephemeral=True)
        else:
            await interaction.response.send_message("❌ Không tìm thấy tài khoản để xóa.", ephemeral=True)
        self.stop()

class QuickCodeView(discord.ui.View):
    """View cung cấp công cụ lấy mã cookie nhanh."""
    def __init__(self, author_id: int, cog_instance: Optional[Any] = None, management_view: Optional[Any] = None):
        super().__init__(timeout=180)
        self.author_id = author_id
        self.cog_instance = cog_instance
        self.management_view = management_view

        self.add_item(discord.ui.Button(
            label="Mở HoYoLAB Web",
            style=discord.ButtonStyle.link,
            emoji="🌐",
            url="https://www.hoyolab.com/home"
        ))

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        return interaction.user.id == self.author_id

    @discord.ui.button(label="📋 Copy Mã Bookmarklet", style=discord.ButtonStyle.primary, emoji="🔖", row=0)
    async def copy_bookmarklet(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message(
            "📋 **Mã Bookmarklet 1 Chạm:**\n"
            "Sao chép toàn bộ dòng mã bên dưới và tạo dấu trang trên trình duyệt:\n"
            f"```javascript\n{BOOKMARKLET_JS}\n```\n"
            "💡 **Cách dùng:** Khi đang ở trang https://www.hoyolab.com, chỉ cần nhấp vào Bookmark vừa lưu -> Cookie sẽ tự động được copy!",
            ephemeral=True
        )

    @discord.ui.button(label="📝 Dán Cookie Vào Bot", style=discord.ButtonStyle.success, emoji="📝", row=0)
    async def open_modal(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(SmartCookieModal(management_view=self.management_view, cog_instance=self.cog_instance))

    @discord.ui.button(label="🔐 Đăng Nhập Tự Động", style=discord.ButtonStyle.secondary, emoji="🔐", row=0)
    async def open_login(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(HoyoBuddyLoginModal(management_view=self.management_view, cog_instance=self.cog_instance))

class CheckinSelect(discord.ui.Select):
    """Menu chọn game cụ thể để điểm danh thủ công."""
    def __init__(self, cog_instance: Any, user_accounts: list):
        self.cog_instance = cog_instance

        options = [
            discord.SelectOption(label="Tất cả tài khoản & tất cả game", value="all_all", emoji="✨"),
        ]
        for acc in user_accounts:
            acc_name = acc.get("name", "N/A")
            for g_key, g_info in GAMES.items():
                options.append(
                    discord.SelectOption(
                        label=f"{g_info['name']} ({acc_name})"[:100],
                        value=f"{acc_name}_{g_key}",
                        emoji=g_info["emoji"]
                    )
                )

        super().__init__(placeholder="Chọn game hoặc tài khoản để điểm danh ngay...", options=options[:25], row=2)

    async def callback(self, interaction: discord.Interaction):
        selected = self.values[0]
        if selected == "all_all":
            await self.cog_instance.checkin_now_logic(interaction, account_name=None, game=None)
        else:
            parts = selected.rsplit('_', 1)
            if len(parts) == 2:
                acc_name, game_key = parts[0], parts[1]
                await self.cog_instance.checkin_now_logic(interaction, account_name=acc_name, game=game_key)
            else:
                await self.cog_instance.checkin_now_logic(interaction, account_name=None, game=None)

# ==============================================================================
# HỆ THỐNG GIAO DIỆN & TÍNH NĂNG THEO PHONG CÁCH HOYO BUDDY
# ==============================================================================

class HoyoCheckinGameSelect(discord.ui.Select):
    def __init__(self, parent_view: 'HoyoCheckinOverviewView', options: list[discord.SelectOption]):
        super().__init__(placeholder="Chọn game muốn xem tiến độ điểm danh...", options=options, row=0)
        self.parent_view = parent_view

    async def callback(self, interaction: discord.Interaction):
        await interaction.response.defer()
        self.parent_view.current_game = self.values[0]
        self.parent_view.render_controls()
        embed = await self.parent_view.get_checkin_embed()
        await interaction.edit_original_response(embed=embed, view=self.parent_view)

class HoyoCheckinAccountSelect(discord.ui.Select):
    def __init__(self, parent_view: 'HoyoCheckinOverviewView', options: list[discord.SelectOption]):
        super().__init__(placeholder="Chọn tài khoản...", options=options, row=1)
        self.parent_view = parent_view

    async def callback(self, interaction: discord.Interaction):
        await interaction.response.defer()
        self.parent_view.acc_idx = int(self.values[0])
        self.parent_view.render_controls()
        embed = await self.parent_view.get_checkin_embed()
        await interaction.edit_original_response(embed=embed, view=self.parent_view)

class HoyoDoCheckinButton(discord.ui.Button):
    def __init__(self, parent_view: 'HoyoCheckinOverviewView'):
        super().__init__(label="Điểm Danh Ngay", style=discord.ButtonStyle.success, emoji="✨", row=2)
        self.parent_view = parent_view

    async def callback(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True, thinking=True)
        account = self.parent_view.accounts[self.parent_view.acc_idx]
        g_info = GAMES.get(self.parent_view.current_game, GAMES["genshin"])
        game_enum = g_info["game"]
        game_name = g_info["name"]
        emoji = g_info["emoji"]
        user_id = str(interaction.user.id)

        client = build_genshin_client(account)
        try:
            reward = await client.claim_daily_reward(game=game_enum)
            msg = f"🎉 {emoji} **{game_name}:** Đã điểm danh thành công! Nhận `{reward.name}` (x{reward.amount})."
            new_embed = await self.parent_view.get_checkin_embed()
            await interaction.message.edit(embed=new_embed, view=self.parent_view)
            return await interaction.followup.send(msg, ephemeral=True)
        except genshin.AlreadyClaimed:
            new_embed = await self.parent_view.get_checkin_embed()
            await interaction.message.edit(embed=new_embed, view=self.parent_view)
            return await interaction.followup.send(f"☑️ {emoji} **{game_name}:** Bạn đã điểm danh hôm nay rồi!", ephemeral=True)
        except genshin.errors.DailyGeetestTriggered as ge:
            session_id = secrets.token_hex(8)
            loop = asyncio.get_running_loop()
            captcha_future = loop.create_future()
            create_captcha_session(session_id, {
                "user_id": user_id,
                "stage": "puzzle",
                "gt": ge.gt,
                "challenge": ge.challenge,
                "is_v4": False,
                "future": captcha_future,
            })
            captcha_url = f"{WEB_BASE_URL}/hoyo/captcha?session={session_id}"

            embed_c = discord.Embed(
                title=f"🧩 {emoji} HoYoLAB Yêu Cầu Kéo Mảnh Ghép Captcha",
                description=(
                    f"HoYoLAB yêu cầu giải Captcha Geetest để điểm danh **{game_name}** hôm nay.\n\n"
                    "👉 Bấm nút **[🧩 Mở Trang Giải Captcha]** bên dưới để kéo mảnh ghép trên trình duyệt.\n"
                    "Bot sẽ tự động nhận diện và hoàn tất điểm danh nhận quà ngay lập tức!\n\n"
                    "⏱️ *Thời gian chờ giải: **5 phút**.*"
                ),
                color=discord.Color.gold()
            )
            v_c = discord.ui.View(timeout=300)
            v_c.add_item(discord.ui.Button(label="🧩 Mở Trang Giải Captcha", style=discord.ButtonStyle.link, url=captcha_url))
            await interaction.followup.send(embed=embed_c, view=v_c, ephemeral=True)

            try:
                c_data = await asyncio.wait_for(captcha_future, timeout=300.0)
                challenge_dict = {
                    "geetest_challenge": c_data.get("geetest_challenge") or ge.challenge,
                    "geetest_validate": c_data.get("geetest_validate", ""),
                    "geetest_seccode": c_data.get("geetest_seccode") or (c_data.get("geetest_validate", "") + "|jordan")
                }
                reward2 = await client.claim_daily_reward(game=game_enum, challenge=challenge_dict)
                new_embed = await self.parent_view.get_checkin_embed()
                await interaction.message.edit(embed=new_embed, view=self.parent_view)
                await interaction.followup.send(f"🎉 {emoji} **{game_name}:** Vượt Captcha thành công! Đã nhận `{reward2.name}` (x{reward2.amount}).", ephemeral=True)
            except asyncio.TimeoutError:
                await interaction.followup.send("⏰ Đã hết thời gian chờ giải Captcha (5 phút). Vui lòng thử lại!", ephemeral=True)
            except Exception as cap_err:
                await interaction.followup.send(f"❌ Lỗi hoàn tất sau Captcha: {cap_err}", ephemeral=True)
        except genshin.InvalidCookies:
            return await interaction.followup.send("❌ Cookie hết hạn hoặc không hợp lệ. Vui lòng cập nhật lại!", ephemeral=True)
        except Exception as e:
            return await interaction.followup.send(f"⚠️ Không thể điểm danh: {e}", ephemeral=True)

class HoyoViewCalendarButton(discord.ui.Button):
    def __init__(self, parent_view: 'HoyoCheckinOverviewView'):
        super().__init__(label="Lịch Quà Tháng", style=discord.ButtonStyle.primary, emoji="📅", row=2)
        self.parent_view = parent_view

    async def callback(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True, thinking=True)
        account = self.parent_view.accounts[self.parent_view.acc_idx]
        g_info = GAMES.get(self.parent_view.current_game, GAMES["genshin"])
        game_enum = g_info["game"]
        game_name = g_info["name"]
        emoji = g_info["emoji"]

        client = build_genshin_client(account)
        try:
            rewards = await client.get_monthly_rewards(game=game_enum)
            info = await client.get_reward_info(game=game_enum)
        except Exception as e:
            return await interaction.followup.send(f"❌ Không thể tải lịch phần thưởng: {e}", ephemeral=True)

        claimed = info.claimed_rewards
        lines = []
        for i, r in enumerate(rewards, start=1):
            status_icon = "✅" if i <= claimed else ("📍" if i == claimed + 1 else "⬜")
            is_gem = any(k in r.name.lower() for k in ["nguyên thạch", "primogem", "ánh sao", "stellar jade", "polychrome", "phim màu"])
            gem_star = " 💎" if is_gem else ""
            lines.append(f"`{i:02d}` {status_icon} **{r.name}** x{r.amount}{gem_star}")

        embed = discord.Embed(
            title=f"📅 Lịch Quà Tháng {datetime.now().month}/{datetime.now().year} • {emoji} {game_name}",
            description="\n".join(lines[:16]),
            color=discord.Color.purple()
        )
        if len(lines) > 16:
            embed.add_field(name="Phần Còn Lại Trong Tháng", value="\n".join(lines[16:]), inline=False)
        embed.set_footer(text="Ký hiệu: ✅ Đã nhận | 📍 Ngày tiếp theo | 💎 Quà Nguyên Thạch / Ngọc Ánh Sao")
        await interaction.followup.send(embed=embed, ephemeral=True)

class HoyoRefreshCheckinButton(discord.ui.Button):
    def __init__(self, parent_view: 'HoyoCheckinOverviewView'):
        super().__init__(label="Làm Mới", style=discord.ButtonStyle.secondary, emoji="🔄", row=2)
        self.parent_view = parent_view

    async def callback(self, interaction: discord.Interaction):
        await interaction.response.defer()
        embed = await self.parent_view.get_checkin_embed()
        await interaction.edit_original_response(embed=embed, view=self.parent_view)

class HoyoOpenNotesFromCheckinButton(discord.ui.Button):
    def __init__(self, parent_view: 'HoyoCheckinOverviewView'):
        super().__init__(label="Realtime Notes", style=discord.ButtonStyle.secondary, emoji="📊", row=2)
        self.parent_view = parent_view

    async def callback(self, interaction: discord.Interaction):
        await interaction.response.defer()
        # Chuyển sang NotesView
        target_game = self.parent_view.current_game if self.parent_view.current_game in ["genshin", "hsr", "zzz"] else "genshin"
        notes_view = HoyoNotesView(
            self.parent_view.author,
            self.parent_view.accounts,
            initial_acc_idx=self.parent_view.acc_idx,
            initial_game=target_game,
            cog_instance=self.parent_view.cog_instance
        )
        embed = await notes_view.get_notes_embed()
        await interaction.edit_original_response(embed=embed, view=notes_view)

class HoyoCheckinOverviewView(discord.ui.View):
    """
    Giao diện theo phong cách Hoyo Buddy:
    Xem tiến độ điểm danh tháng, số ngày đã điểm danh, quà hôm nay/ngày mai,
    lịch nhận Nguyên Thạch/Ngọc Ánh Sao, bù điểm danh, và điểm danh trực tiếp kèm Captcha Solver!
    """
    def __init__(self, author: discord.Member, accounts: list, initial_acc_idx: int = 0, initial_game: str = "genshin", cog_instance: Any = None):
        super().__init__(timeout=180)
        self.author = author
        self.accounts = accounts
        self.acc_idx = min(initial_acc_idx, max(0, len(accounts) - 1)) if accounts else 0
        self.current_game = initial_game
        self.cog_instance = cog_instance
        self.render_controls()

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id != self.author.id:
            await interaction.response.send_message("❌ Bạn không phải chủ nhân của giao diện này.", ephemeral=True)
            return False
        return True

    def render_controls(self):
        self.clear_items()

        # Dropdown Game (Row 0)
        game_options = [
            discord.SelectOption(label="Genshin Impact", value="genshin", emoji="🌸", default=(self.current_game == "genshin")),
            discord.SelectOption(label="Honkai: Star Rail", value="hsr", emoji="🚂", default=(self.current_game == "hsr")),
            discord.SelectOption(label="Zenless Zone Zero", value="zzz", emoji="⚡", default=(self.current_game == "zzz")),
            discord.SelectOption(label="Honkai Impact 3rd", value="bh3", emoji="⚔️", default=(self.current_game == "bh3")),
        ]
        self.add_item(HoyoCheckinGameSelect(self, game_options))

        # Dropdown Account (Row 1) nếu có nhiều acc
        if len(self.accounts) > 1:
            acc_options = []
            for i, acc in enumerate(self.accounts):
                name = acc.get("name", f"Acc {i+1}")
                acc_options.append(
                    discord.SelectOption(label=name[:100], value=str(i), default=(i == self.acc_idx), emoji="👤")
                )
            self.add_item(HoyoCheckinAccountSelect(self, acc_options))

        # Row 2: Buttons
        self.add_item(HoyoDoCheckinButton(self))
        self.add_item(HoyoViewCalendarButton(self))
        url = CHECK_IN_URLS.get(self.current_game, "https://act.hoyolab.com/")
        self.add_item(discord.ui.Button(label="Bù Điểm Danh", style=discord.ButtonStyle.link, url=url, emoji="🎫", row=2))
        self.add_item(HoyoOpenNotesFromCheckinButton(self))
        self.add_item(HoyoRefreshCheckinButton(self))

    async def get_checkin_embed(self) -> discord.Embed:
        if not self.accounts:
            return discord.Embed(
                title="⚠️ Chưa Có Tài Khoản HoYoLAB",
                description="Bạn chưa lưu tài khoản nào. Hãy dùng `/hoyolab setcookie` hoặc nút `Đăng Nhập HoYoverse`!",
                color=discord.Color.red()
            )

        account = self.accounts[self.acc_idx]
        acc_name = account.get("name", "Tài khoản")
        g_info = GAMES.get(self.current_game, GAMES["genshin"])
        game_enum = g_info["game"]
        game_name = g_info["name"]
        emoji = g_info["emoji"]

        client = build_genshin_client(account)
        try:
            info = await client.get_reward_info(game=game_enum)
            rewards = await client.get_monthly_rewards(game=game_enum)
        except genshin.InvalidCookies:
            return discord.Embed(
                title=f"❌ {emoji} {game_name} - Cookie Hết Hạn",
                description=f"Cookie của tài khoản **{acc_name}** không hợp lệ hoặc đã hết hạn (Lỗi -100). Vui lòng cập nhật lại cookie hoặc dùng nút `Đăng Nhập Tự Động`!",
                color=discord.Color.red()
            )
        except Exception as e:
            return discord.Embed(
                title=f"⚠️ {emoji} {game_name} - Không Thể Tải Dữ Liệu",
                description=f"Lỗi kết nối HoYoLAB: `{e}`",
                color=discord.Color.orange()
            )

        total_days = len(rewards)
        claimed_num = info.claimed_rewards
        is_signed = info.signed_in
        missed = info.missed_rewards

        # Xác định phần thưởng hôm nay
        today_reward = None
        if is_signed and claimed_num > 0 and claimed_num <= total_days:
            today_reward = rewards[claimed_num - 1]
        elif not is_signed and claimed_num < total_days:
            today_reward = rewards[claimed_num]

        # Xác định phần thưởng tiếp theo
        next_reward = None
        if is_signed and claimed_num < total_days:
            next_reward = rewards[claimed_num]
        elif not is_signed and (claimed_num + 1) < total_days:
            next_reward = rewards[claimed_num + 1]

        # Tìm các mốc Nguyên Thạch / Ngọc Ánh Sao / Phim Màu kế tiếp
        major_milestones = []
        for idx in range(claimed_num, total_days):
            r = rewards[idx]
            rn = r.name.lower()
            if any(k in rn for k in ["nguyên thạch", "primogem", "ánh sao", "stellar jade", "polychrome", "phim màu"]):
                major_milestones.append((idx + 1, r.name, r.amount, idx + 1 - claimed_num))
                if len(major_milestones) >= 2:
                    break

        embed = discord.Embed(
            title=f"{emoji} Trung Tâm Điểm Danh • {game_name}",
            description=f"👤 Tài khoản: **{acc_name}** (HoYoLAB ID: `{account.get('ltuid_v2', 'N/A')}`)",
            color=discord.Color.brand_green() if is_signed else discord.Color.gold(),
            timestamp=datetime.now(timezone.utc)
        )

        progress_str = make_progress_bar(claimed_num, total_days, length=10)
        embed.add_field(
            name=f"📅 Tiến Độ Tháng {datetime.now().month}/{datetime.now().year}",
            value=(
                f"{progress_str}\n"
                f"• Đã nhận: **{claimed_num}/{total_days} ngày**\n"
                f"• Bị bỏ lỡ: **{missed} ngày**"
            ),
            inline=False
        )

        status_text = "✅ **Đã hoàn thành điểm danh hôm nay!**" if is_signed else "⏳ **Chưa điểm danh hôm nay!** (Bấm nút bên dưới để nhận)"
        embed.add_field(name="🌟 Trạng Thái Hôm Nay", value=status_text, inline=False)

        if today_reward:
            embed.add_field(
                name="🎁 Quà " + ("Đã Nhận Hôm Nay" if is_signed else "Hôm Nay Sắp Nhận"),
                value=f"• **{today_reward.name}** (x{today_reward.amount})\n*(Mốc ngày thứ {claimed_num if is_signed else claimed_num + 1})*",
                inline=True
            )
            embed.set_thumbnail(url=today_reward.icon)

        if next_reward:
            embed.add_field(
                name="🔮 Quà Ngày Kế Tiếp",
                value=f"• **{next_reward.name}** (x{next_reward.amount})",
                inline=True
            )

        if major_milestones:
            m_lines = [f"• **Ngày {day}**: {name} (x{amt}) — *còn {rem} ngày nữa*" for day, name, amt, rem in major_milestones]
            embed.add_field(name="💎 Mốc Quà Nguyên Thạch / Ngọc Ánh Sao Sắp Tới", value="\n".join(m_lines), inline=False)

        embed.set_footer(text="Phong cách Hoyo Buddy • SakuraBot")
        return embed

# ==============================================================================
# HỆ THỐNG REAL-TIME NOTES (THEO DÕI THỜI GIAN THỰC INGAME - HOYO BUDDY STYLE)
# ==============================================================================

class HoyoNotesGameSelect(discord.ui.Select):
    def __init__(self, parent_view: 'HoyoNotesView', options: list[discord.SelectOption]):
        super().__init__(placeholder="Chọn game muốn xem thời gian thực...", options=options, row=0)
        self.parent_view = parent_view

    async def callback(self, interaction: discord.Interaction):
        await interaction.response.defer()
        self.parent_view.current_game = self.values[0]
        self.parent_view.render_controls()
        embed = await self.parent_view.get_notes_embed()
        await interaction.edit_original_response(embed=embed, view=self.parent_view)

class HoyoNotesAccountSelect(discord.ui.Select):
    def __init__(self, parent_view: 'HoyoNotesView', options: list[discord.SelectOption]):
        super().__init__(placeholder="Chọn tài khoản...", options=options, row=1)
        self.parent_view = parent_view

    async def callback(self, interaction: discord.Interaction):
        await interaction.response.defer()
        self.parent_view.acc_idx = int(self.values[0])
        self.parent_view.render_controls()
        embed = await self.parent_view.get_notes_embed()
        await interaction.edit_original_response(embed=embed, view=self.parent_view)

class HoyoRefreshNotesButton(discord.ui.Button):
    def __init__(self, parent_view: 'HoyoNotesView'):
        super().__init__(label="Cập Nhật Trực Tiếp", style=discord.ButtonStyle.primary, emoji="🔄", row=2)
        self.parent_view = parent_view

    async def callback(self, interaction: discord.Interaction):
        await interaction.response.defer()
        embed = await self.parent_view.get_notes_embed()
        await interaction.edit_original_response(embed=embed, view=self.parent_view)

class HoyoOpenCheckinFromNotesButton(discord.ui.Button):
    def __init__(self, parent_view: 'HoyoNotesView'):
        super().__init__(label="Mở Điểm Danh", style=discord.ButtonStyle.success, emoji="✨", row=2)
        self.parent_view = parent_view

    async def callback(self, interaction: discord.Interaction):
        await interaction.response.defer()
        view = HoyoCheckinOverviewView(
            self.parent_view.author,
            self.parent_view.accounts,
            initial_acc_idx=self.parent_view.acc_idx,
            initial_game=self.parent_view.current_game,
            cog_instance=self.parent_view.cog_instance
        )
        embed = await view.get_checkin_embed()
        await interaction.edit_original_response(embed=embed, view=view)

class HoyoNotesView(discord.ui.View):
    """
    Giao diện theo phong cách Hoyo Buddy:
    Theo dõi Nhựa, Sức mạnh khai phá, Điện năng, Ủy thác, Động tiên, Boss tuần ingame theo thời gian thực!
    """
    def __init__(self, author: discord.Member, accounts: list, initial_acc_idx: int = 0, initial_game: str = "genshin", cog_instance: Any = None):
        super().__init__(timeout=180)
        self.author = author
        self.accounts = accounts
        self.acc_idx = min(initial_acc_idx, max(0, len(accounts) - 1)) if accounts else 0
        self.current_game = initial_game
        self.cog_instance = cog_instance
        self.render_controls()

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id != self.author.id:
            await interaction.response.send_message("❌ Bạn không phải chủ nhân của giao diện này.", ephemeral=True)
            return False
        return True

    def render_controls(self):
        self.clear_items()
        options = [
            discord.SelectOption(label="Genshin Impact", value="genshin", emoji="🌸", default=(self.current_game == "genshin")),
            discord.SelectOption(label="Honkai: Star Rail", value="hsr", emoji="🚂", default=(self.current_game == "hsr")),
            discord.SelectOption(label="Zenless Zone Zero", value="zzz", emoji="⚡", default=(self.current_game == "zzz")),
        ]
        self.add_item(HoyoNotesGameSelect(self, options))

        if len(self.accounts) > 1:
            acc_options = []
            for i, acc in enumerate(self.accounts):
                name = acc.get("name", f"Acc {i+1}")
                acc_options.append(discord.SelectOption(label=name[:100], value=str(i), default=(i == self.acc_idx), emoji="👤"))
            self.add_item(HoyoNotesAccountSelect(self, acc_options))

        self.add_item(HoyoRefreshNotesButton(self))
        self.add_item(HoyoOpenCheckinFromNotesButton(self))

    async def get_notes_embed(self) -> discord.Embed:
        if not self.accounts:
            return discord.Embed(
                title="⚠️ Chưa Có Tài Khoản HoYoLAB",
                description="Bạn chưa lưu tài khoản nào. Hãy dùng `/hoyolab setcookie` hoặc nút `Đăng Nhập HoYoverse`!",
                color=discord.Color.red()
            )

        account = self.accounts[self.acc_idx]
        acc_name = account.get("name", "Tài khoản")
        client = build_genshin_client(account)

        try:
            if self.current_game == "genshin":
                notes = await client.get_genshin_notes()
                embed = discord.Embed(
                    title="🌸 Thời Gian Thực (Real-time Notes) • Genshin Impact",
                    description=f"👤 Tài khoản: **{acc_name}**",
                    color=discord.Color.from_rgb(86, 172, 237),
                    timestamp=datetime.now(timezone.utc)
                )
                resin_prog = make_progress_bar(notes.current_resin, notes.max_resin)
                resin_time = format_timedelta_future(notes.remaining_resin_recovery_time)
                embed.add_field(
                    name="🧪 Nhựa Nguyên Bản (Resin)",
                    value=f"**{notes.current_resin} / {notes.max_resin}**\n{resin_prog}\n⏱️ {resin_time}",
                    inline=False
                )

                com_icon = "✅" if notes.completed_commissions >= notes.max_commissions else "⏳"
                reward_icon = "✅ Đã nhận" if notes.claimed_commission_reward else "⏳ Chưa nhận"
                embed.add_field(
                    name="📜 Nhiệm Vụ Ủy Thác Hàng Ngày",
                    value=f"{com_icon} Hoàn thành: **{notes.completed_commissions} / {notes.max_commissions}**\n🎁 Thưởng Katheryne: **{reward_icon}**",
                    inline=True
                )

                realm_prog = make_progress_bar(notes.current_realm_currency, notes.max_realm_currency)
                realm_time = format_timedelta_future(notes.remaining_realm_currency_recovery_time)
                embed.add_field(
                    name="🏡 Tiền Động Tiên (Ấm Trần Ca)",
                    value=f"**{notes.current_realm_currency} / {notes.max_realm_currency}**\n{realm_prog}\n⏱️ {realm_time}",
                    inline=True
                )

                boss_left = notes.remaining_resin_discounts
                boss_text = f"**{boss_left} / {notes.max_resin_discounts}** lần giảm nhựa (-50%)"
                if not notes.remaining_transformer_recovery_time or notes.remaining_transformer_recovery_time.total_seconds() <= 0:
                    tf_text = "✅ Sẵn sàng sử dụng!"
                else:
                    tf_days = notes.remaining_transformer_recovery_time.days
                    tf_hours = int(notes.remaining_transformer_recovery_time.total_seconds() % 86400 // 3600)
                    tf_text = f"⏳ Hồi sau {tf_days}d {tf_hours}h"

                embed.add_field(
                    name="⚔️ Boss Tuần & Đĩa Biến Đổi",
                    value=f"• Giảm giá Boss: {boss_text}\n• Đĩa biến đổi: {tf_text}",
                    inline=False
                )

                exp_finished = len([e for e in notes.expeditions if e.status == 'Finished'])
                exp_text = f"**{exp_finished} / {len(notes.expeditions)}** đã hoàn thành (Tối đa: {notes.max_expeditions})"
                embed.add_field(name="🧭 Phái Đi Thám Hiểm", value=exp_text, inline=True)

                embed.set_footer(text="Dữ liệu đồng bộ trực tiếp từ HoYoLAB • SakuraBot")
                return embed

            elif self.current_game == "hsr":
                notes = await client.get_starrail_notes()
                embed = discord.Embed(
                    title="🚂 Thời Gian Thực (Real-time Notes) • Honkai: Star Rail",
                    description=f"👤 Tài khoản: **{acc_name}**",
                    color=discord.Color.from_rgb(186, 126, 255),
                    timestamp=datetime.now(timezone.utc)
                )

                sta_prog = make_progress_bar(notes.current_stamina, notes.max_stamina)
                sta_time = format_timedelta_future(notes.stamina_recover_time)
                embed.add_field(
                    name="⚡ Sức Mạnh Khai Phá (Stamina)",
                    value=f"**{notes.current_stamina} / {notes.max_stamina}** *(Dự phòng: {notes.current_reserve_stamina}/2400)*\n{sta_prog}\n⏱️ {sta_time}",
                    inline=False
                )

                train_prog = make_progress_bar(notes.current_train_score, notes.max_train_score)
                embed.add_field(
                    name="🎯 Rèn Luyện Hàng Ngày",
                    value=f"**{notes.current_train_score} / {notes.max_train_score}** điểm\n{train_prog}",
                    inline=True
                )

                rogue_prog = make_progress_bar(notes.current_rogue_score, notes.max_rogue_score)
                embed.add_field(
                    name="🌌 Vũ Trụ Mô Phỏng",
                    value=f"**{notes.current_rogue_score} / {notes.max_rogue_score}** điểm\n{rogue_prog}",
                    inline=True
                )

                echo_left = notes.remaining_weekly_discounts
                embed.add_field(
                    name="⚔️ Dư Âm Chiến Đấu & Thám Hiểm",
                    value=f"• Nhận thưởng Boss tuần: **{echo_left} / {notes.max_weekly_discounts}** lần còn lại\n• Thám hiểm ủy thác: **{notes.accepted_expedition_num} / {notes.total_expedition_num}** đang chạy",
                    inline=False
                )

                embed.set_footer(text="Dữ liệu đồng bộ trực tiếp từ HoYoLAB • SakuraBot")
                return embed

            elif self.current_game == "zzz":
                notes = await client.get_zzz_notes()
                embed = discord.Embed(
                    title="⚡ Thời Gian Thực (Real-time Notes) • Zenless Zone Zero",
                    description=f"👤 Tài khoản: **{acc_name}**",
                    color=discord.Color.from_rgb(255, 115, 0),
                    timestamp=datetime.now(timezone.utc)
                )

                bat = notes.battery_charge
                bat_prog = make_progress_bar(bat.current, bat.max)
                bat_time = format_timedelta_future(timedelta(seconds=bat.seconds_till_full))
                embed.add_field(
                    name="🔋 Điện Năng Tích Trữ (Battery)",
                    value=f"**{bat.current} / {bat.max}**\n{bat_prog}\n⏱️ {bat_time}",
                    inline=False
                )

                eng = notes.engagement
                eng_prog = make_progress_bar(eng.current, eng.max)
                embed.add_field(
                    name="📋 Điểm Năng Nổ Hàng Ngày",
                    value=f"**{eng.current} / {eng.max}** điểm\n{eng_prog}",
                    inline=True
                )

                video_st = "✅ Đang kinh doanh" if getattr(notes.video_store_state, 'state', None) else "⏳ Chưa mở tiệm"
                scratch_st = "✅ Đã cào thẻ hôm nay" if notes.scratch_card_completed else "⏳ Chưa cào thẻ hôm nay"
                embed.add_field(
                    name="📼 Hoạt Động Thành Phố New Eridu",
                    value=f"• Tiệm băng đĩa Random Play: **{video_st}**\n• Cào thẻ sạp báo: **{scratch_st}**",
                    inline=True
                )

                embed.set_footer(text="Dữ liệu đồng bộ trực tiếp từ HoYoLAB • SakuraBot")
                return embed

        except genshin.DataNotPublic:
            embed_err = discord.Embed(
                title="🔒 Dữ Liệu Chiến Tích Chưa Được Mở Công Khai",
                description=(
                    "HoYoLAB báo rằng **Chiến Tích Thời Gian Thực (Real-time Notes)** của bạn đang bị ẩn.\n\n"
                    "👉 **Cách bật chỉ trong 10 giây:**\n"
                    "1. Mở ứng dụng **HoYoLAB** trên điện thoại (hoặc trang web [hoyolab.com](https://www.hoyolab.com)).\n"
                    "2. Vào mục **Cá Nhân (Profile)** -> chọn biểu tượng Cài đặt ⚙️ (hoặc Quyền riêng tư).\n"
                    "3. Chọn **Cài đặt quyền riêng tư (Privacy Settings)**.\n"
                    "4. Bật công tắc **\"Công khai Chiến Tích (Battle Chronicle)\"** và **\"Hiển thị thông tin thời gian thực (Real-time Notes)\"**.\n"
                    "5. Quay lại đây và nhấn nút **`🔄 Cập Nhật Trực Tiếp`** bên dưới!"
                ),
                color=discord.Color.gold()
            )
            return embed_err
        except genshin.InvalidCookies:
            return discord.Embed(
                title="❌ Cookie Hết Hạn Hoặc Không Hợp Lệ",
                description=f"Cookie của tài khoản **{acc_name}** đã hết hạn (Lỗi -100). Vui lòng cập nhật lại cookie hoặc dùng nút `Đăng Nhập Tự Động`!",
                color=discord.Color.red()
            )
        except Exception as e:
            return discord.Embed(
                title="⚠️ Lỗi Truy Vấn Dữ Liệu",
                description=f"Không thể tải thông tin từ máy chủ HoYoLAB: `{e}`",
                color=discord.Color.orange()
            )

class ManagementView(discord.ui.View):
    """Bảng điều khiển quản lý tài khoản Hoyolab."""
    def __init__(self, author: discord.Member, cog_instance: Any):
        super().__init__(timeout=180)
        self.author = author
        self.cog_instance = cog_instance
        self.message = None

        # Nút liên kết hướng dẫn bên ngoài
        self.add_item(discord.ui.Button(
            label="HoYoLAB Website",
            style=discord.ButtonStyle.link,
            emoji="🌐",
            url="https://www.hoyolab.com/home",
            row=3
        ))

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id != self.author.id:
            await interaction.response.send_message(t(interaction.guild, "LEVEL_NOT_YOURS"), ephemeral=True)
            return False
        return True

    async def update_embed_from_interaction(self, interaction: discord.Interaction):
        """Hàm làm mới Embed khi có thay đổi."""
        embed = self.cog_instance.create_management_embed(self.author)
        # Tái tạo CheckinSelect với dữ liệu mới
        user_accounts = self.cog_instance.cookies_data.get(str(self.author.id), [])
        for item in list(self.children):
            if isinstance(item, CheckinSelect):
                self.remove_item(item)
        if user_accounts:
            self.add_item(CheckinSelect(self.cog_instance, user_accounts))

        if not interaction.response.is_done():
            await interaction.response.edit_message(embed=embed, view=self)
        else:
            await interaction.edit_original_response(embed=embed, view=self)

    @discord.ui.button(label="Thêm Cookie", style=discord.ButtonStyle.success, emoji="📝", row=0)
    async def set_cookie(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(SmartCookieModal(management_view=self, cog_instance=self.cog_instance))

    @discord.ui.button(label="Đăng Nhập HoYoverse", style=discord.ButtonStyle.primary, emoji="🔐", row=0)
    async def login_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(HoyoBuddyLoginModal(management_view=self, cog_instance=self.cog_instance))

    @discord.ui.button(label="Lấy Mã Nhanh", style=discord.ButtonStyle.secondary, emoji="⚡", row=0)
    async def quick_code(self, interaction: discord.Interaction, button: discord.ui.Button):
        embed = self.cog_instance.create_quick_code_embed()
        view = QuickCodeView(self.author.id, cog_instance=self.cog_instance, management_view=self)
        await interaction.response.send_message(embed=embed, view=view, ephemeral=True)

    @discord.ui.button(label="Bật/Tắt Tự Động", style=discord.ButtonStyle.primary, emoji="🔄", row=1)
    async def toggle_auto(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.cog_instance.toggle_auto_logic(interaction, management_view=self)

    @discord.ui.button(label="Điểm Danh Ngay", style=discord.ButtonStyle.success, emoji="✨", row=1)
    async def checkin_all_now(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.cog_instance.checkin_now_logic(interaction, account_name=None, game=None)

    @discord.ui.button(label="Chọn UID Game", style=discord.ButtonStyle.secondary, emoji="🎮", row=1)
    async def select_uid_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        user_accounts = self.cog_instance.cookies_data.get(str(self.author.id), [])
        if not user_accounts:
            return await interaction.response.send_message("❌ Bạn chưa có tài khoản nào được lưu.", ephemeral=True)
        await interaction.response.defer(ephemeral=True, thinking=True)
        if len(user_accounts) == 1:
            await self.cog_instance.show_uid_choice_menu(interaction, user_accounts[0], user_accounts, management_view=self)
        else:
            view = AccountSelectForUIDView(user_accounts, self.author.id, management_view=self, cog_instance=self.cog_instance)
            await interaction.followup.send("🎮 Vui lòng chọn tài khoản muốn xem / chọn UID game:", view=view, ephemeral=True)

    @discord.ui.button(label="Xóa Tài Khoản", style=discord.ButtonStyle.danger, emoji="🗑️", row=1)
    async def delete_cookie(self, interaction: discord.Interaction, button: discord.ui.Button):
        user_accounts = self.cog_instance.cookies_data.get(str(self.author.id), [])
        if not user_accounts:
            return await interaction.response.send_message("❌ Bạn chưa có tài khoản nào để xóa.", ephemeral=True)
        view = DeleteAccountView(user_accounts, self.author.id, management_view=self, cog_instance=self.cog_instance)
        await interaction.response.send_message("Vui lòng chọn tài khoản cần xóa:", view=view, ephemeral=True)

    @discord.ui.button(label="Tự Động Code", style=discord.ButtonStyle.secondary, emoji="🎁", row=3)
    async def toggle_auto_redeem(self, interaction: discord.Interaction, button: discord.ui.Button):
        user_accounts = self.cog_instance.cookies_data.get(str(self.author.id), [])
        if not user_accounts:
            return await interaction.response.send_message("❌ Bạn chưa có tài khoản nào được lưu.", ephemeral=True)

        curr_state = any(acc.get("auto_redeem", True) for acc in user_accounts)
        new_state = not curr_state
        for acc in user_accounts:
            acc["auto_redeem"] = new_state

        save_cookies(self.cog_instance.cookies_data)
        status_text = "🟢 ĐÃ BẬT" if new_state else "🔴 ĐÃ TẮT"
        await interaction.response.send_message(
            f"🎁 **{status_text}** tính năng tự động nhập giftcode mới cho các tài khoản của bạn!",
            ephemeral=True
        )
        try:
            await self.update_embed_from_interaction(interaction)
        except Exception:
            pass

    @discord.ui.button(label="Realtime Notes", style=discord.ButtonStyle.secondary, emoji="📊", row=3)
    async def view_notes_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        user_accounts = self.cog_instance.cookies_data.get(str(self.author.id), [])
        if not user_accounts:
            return await interaction.response.send_message("❌ Bạn chưa có tài khoản nào được lưu.", ephemeral=True)
        await interaction.response.defer(ephemeral=True, thinking=True)
        view = HoyoNotesView(self.author, user_accounts, initial_acc_idx=0, initial_game="genshin", cog_instance=self.cog_instance)
        embed = await view.get_notes_embed()
        await interaction.followup.send(embed=embed, view=view, ephemeral=True)

    @discord.ui.button(label="Lịch & Quà Tháng", style=discord.ButtonStyle.secondary, emoji="📅", row=3)
    async def view_overview_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        user_accounts = self.cog_instance.cookies_data.get(str(self.author.id), [])
        if not user_accounts:
            return await interaction.response.send_message("❌ Bạn chưa có tài khoản nào được lưu.", ephemeral=True)
        await interaction.response.defer(ephemeral=True, thinking=True)
        view = HoyoCheckinOverviewView(self.author, user_accounts, initial_acc_idx=0, initial_game="genshin", cog_instance=self.cog_instance)
        embed = await view.get_checkin_embed()
        await interaction.followup.send(embed=embed, view=view, ephemeral=True)

    @discord.ui.button(label="Đồng Hành Mimo", style=discord.ButtonStyle.secondary, emoji="🕊️", row=3)
    async def view_accompany_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        user_accounts = self.cog_instance.cookies_data.get(str(self.author.id), [])
        if not user_accounts:
            return await interaction.response.send_message("❌ Bạn chưa có tài khoản nào được lưu.", ephemeral=True)
        await interaction.response.defer(ephemeral=True, thinking=True)
        await self.cog_instance.accompany_logic(interaction)

class HoyolabCheckinCog(commands.Cog, name="Trung Tâm Tài Khoản Hoyolab"):
    """Cog quản lý điểm danh tự động cho tất cả các game HoYoverse."""
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.cookies_data = load_cookies()
        self.auto_checkin_task.start()

    def cog_unload(self):
        self.auto_checkin_task.cancel()

    async def show_uid_choice_menu(self, interaction: discord.Interaction, account: dict, all_accounts: list, management_view: Optional[Any] = None):
        """Hiển thị menu chọn UID cho một tài khoản HoYoverse."""
        ltoken = account.get("ltoken_v2", "")
        ltuid = account.get("ltuid_v2", "")
        if not ltoken or not ltuid:
            msg = "❌ Tài khoản này không có đủ token để truy vấn UID game."
            if interaction.response.is_done():
                return await interaction.followup.send(msg, ephemeral=True)
            return await interaction.response.send_message(msg, ephemeral=True)

        auth_cookies = {
            "ltoken_v2": ltoken,
            "ltuid_v2": ltuid,
            "ltoken": ltoken,
            "ltuid": ltuid,
            "account_id": ltuid,
            "account_id_v2": ltuid,
        }
        if account.get("cookie_token_v2"):
            auth_cookies["cookie_token_v2"] = account["cookie_token_v2"]
            auth_cookies["cookie_token"] = account["cookie_token_v2"]
        if account.get("ltmid_v2"):
            auth_cookies["ltmid_v2"] = account["ltmid_v2"]
            auth_cookies["account_mid_v2"] = account["ltmid_v2"]

        client = genshin.Client(auth_cookies, lang="vi-vn")
        try:
            game_roles = await client.get_game_accounts()
        except genshin.InvalidCookies:
            msg = (
                "⚠️ **Không thể tải danh sách UID từ HoYoLAB:** `[-100] Phiên đăng nhập hết hiệu lực, vui lòng đăng nhập lại`\n\n"
                "💡 **Lý do xảy ra lỗi này:**\n"
                "1️⃣ Bạn đã bấm **\"Đăng xuất\"** trên website HoYoLAB (hành động này làm hủy phiên cookie ngay lập tức).\n"
                "2️⃣ Cookie được sao chép bằng Bookmarklet hoặc `copy(document.cookie)` cũ (do `ltoken_v2` là `HttpOnly` nên bị trình duyệt chặn, dẫn đến lấy phải token cũ/hết hạn).\n\n"
                "👉 **Cách khắc phục:**\n"
                "• Sử dụng nút **`🔐 Đăng Nhập Tự Động (Hoyo Buddy)`** ngay trên bảng quản lý để bot tự đăng nhập & nhận token đầy đủ!\n"
                "• Hoặc mở `F12` trên web HoYoLAB -> tab **Network** -> `F5` -> copy dòng **`Cookie:`** trong Request Headers rồi cập nhật lại cookie.\n"
                "*(⚠️ Nhớ: Sau khi copy, chỉ cần tắt tab, TUYỆT ĐỐI KHÔNG BẤM ĐĂNG XUẤT!)*"
            )
            if interaction.response.is_done():
                return await interaction.followup.send(msg, ephemeral=True)
            return await interaction.response.send_message(msg, ephemeral=True)
        except Exception as e:
            msg = f"⚠️ Không thể tải danh sách UID từ HoYoLAB: `{e}`"
            if interaction.response.is_done():
                return await interaction.followup.send(msg, ephemeral=True)
            return await interaction.response.send_message(msg, ephemeral=True)

        if not game_roles:
            msg = "ℹ️ Không tìm thấy nhân vật/UID game nào liên kết với tài khoản HoYoverse này."
            if interaction.response.is_done():
                return await interaction.followup.send(msg, ephemeral=True)
            return await interaction.response.send_message(msg, ephemeral=True)

        embed = discord.Embed(
            title="🎮 Chọn UID Game Cho Tài Khoản",
            description=(
                f"Tài khoản **{account.get('name')}** (HoYoLAB ID: `{ltuid}`) có **{len(game_roles)} nhân vật game**.\n\n"
                "👉 Bạn có thể chọn:\n"
                f"• **`✨ Lưu & Điểm danh TẤT CẢ ({len(game_roles)} UID)`**: Tự động tạo mục riêng cho từng nhân vật để điểm danh tất cả.\n"
                "• **Hoặc chọn 1 UID cụ thể** bên dưới để gán làm UID hoạt động chính."
            ),
            color=discord.Color.blurple()
        )
        for r in game_roles[:10]:
            biz_name, biz_emoji, _ = GAME_BIZ_INFO.get(r.game_biz, (r.game_biz, "🎮", "unknown"))
            embed.add_field(
                name=f"{biz_emoji} {biz_name}",
                value=f"• Tên: **{r.nickname}**\n• UID: `{r.uid}`\n• Cấp: **Lv.{r.level}**\n• Server: `{r.server_name}`",
                inline=True
            )

        view = UIDChoiceView(
            user_id=str(interaction.user.id),
            base_account=account,
            game_accounts=game_roles,
            management_view=management_view,
            cog_instance=self
        )
        if interaction.response.is_done():
            await interaction.followup.send(embed=embed, view=view, ephemeral=True)
        else:
            await interaction.response.send_message(embed=embed, view=view, ephemeral=True)

    def create_management_embed(self, user: discord.User) -> discord.Embed:
        """Tạo Embed quản lý tài khoản với giao diện trực quan."""
        user_id = str(user.id)
        user_accounts = self.cookies_data.get(user_id, [])

        embed = discord.Embed(
            title="🌸 Trung Tâm Điểm Danh Tự Động HoYoLAB",
            description=(
                f"Chào mừng {user.mention} đến với bảng điều khiển HoYoLAB Daily Check-in!\n"
                "Hệ thống tự động điểm danh hàng ngày lúc **01:00 AM** (giờ Việt Nam)."
            ),
            color=discord.Color.from_rgb(108, 92, 231)
        )
        if self.bot.user.avatar:
            embed.set_thumbnail(url=self.bot.user.avatar.url)

        if not user_accounts:
            embed.add_field(
                name="📊 Danh Sách Tài Khoản (0)",
                value="*Bạn chưa lưu tài khoản nào.*\n👉 Nhấn **`📝 Thêm Cookie`** hoặc **`⚡ Lấy Mã Nhanh`** để thêm ngay!",
                inline=False
            )
        else:
            acc_texts = []
            for i, acc in enumerate(user_accounts, start=1):
                name = acc.get("name", f"Acc #{i}")
                uid = acc.get("ltuid_v2", "N/A")
                game_uid = acc.get("game_uid")
                nickname = acc.get("nickname")
                server_name = acc.get("server_name")
                extra = ""
                if game_uid:
                    extra = f" | UID Game: `{game_uid}`"
                    if nickname:
                        extra += f" ({nickname})"
                    if server_name:
                        extra += f" [{server_name}]"
                auto_st = "🟢" if acc.get("auto_checkin", False) else "🔴"
                auto_code = "🟢" if acc.get("auto_redeem", True) else "🔴"
                acc_texts.append(f"**{i}. `{name}`** (HoYoLAB: `{uid}`{extra}) — Daily: {auto_st} | Code: {auto_code}")

            embed.add_field(
                name=f"📊 Tài Khoản Đã Lưu ({len(user_accounts)})",
                value="\n".join(acc_texts),
                inline=False
            )

        embed.add_field(
            name="🎮 Các Game Hỗ Trợ",
            value="• 🌸 **Genshin Impact**\n• 🚂 **Honkai: Star Rail**\n• ⚡ **Zenless Zone Zero**\n• ⚔️ **Honkai Impact 3rd**",
            inline=True
        )
        embed.add_field(
            name="⏰ Lịch Chạy Tự Động",
            value="• **01:00 AM** mỗi ngày\n• Tự động gửi kết quả điểm danh qua DM cho bạn!",
            inline=True
        )

        embed.set_footer(text="SakuraBot • Điểm danh an toàn & nhanh chóng với chuẩn HoYoLAB v2")
        embed.timestamp = datetime.now(timezone.utc)
        return embed

    def create_quick_code_embed(self) -> discord.Embed:
        """Tạo embed hướng dẫn lấy cookie nhanh và an toàn."""
        embed = discord.Embed(
            title="⚡ Hướng Dẫn Liên Kết Tài Khoản HoYoLAB Chuẩn Xác",
            description=(
                "Để SakuraBot tự động điểm danh hàng ngày và nhận Giftcode cho tài khoản game của bạn, "
                "bạn có thể lựa chọn 1 trong các cách sau:\n"
            ),
            color=discord.Color.purple()
        )
        embed.add_field(
            name="🌟 Cách 1: Đăng Nhập Tự Động (Khuyên Dùng - Nhanh & Không Sợ Hết Hạn)",
            value=(
                "• Bấm nút **`🔐 Đăng Nhập Tự Động`** bên dưới (hoặc gõ `/hoyolab login`).\n"
                "• Nhập email/username & mật khẩu HoYoverse.\n"
                "• Kéo mảnh ghép Captcha trên web xác minh và nhập mã OTP gửi về Email.\n"
                "👉 **Bot sẽ tự động nhận đủ mọi token cần thiết (`stoken`, `ltoken`, `cookie_token`), không cần đụng đến F12!**"
            ),
            inline=False
        )
        embed.add_field(
            name="💻 Cách 2: Copy Request Header F12 (Chuẩn 100% Cho PC / Laptop)",
            value=(
                "1. Đăng nhập vào tài khoản trên **[hoyolab.com](https://www.hoyolab.com/home)**.\n"
                "2. Nhấn `F12` (hoặc chuột phải -> *Kiểm tra / Inspect*).\n"
                "3. Chuyển sang thẻ **Network** (Mạng) và nhấn `F5` tải lại trang.\n"
                "4. Nhấp vào bất kỳ request nào (ví dụ: `getGameRecordCard` hoặc `home`).\n"
                "5. Tại khung bên phải, kéo xuống mục **Request Headers** -> tìm dòng **`Cookie:`**.\n"
                "6. Chuột phải dòng `Cookie:` -> chọn **Copy value** (Sao chép giá trị).\n"
                "7. Bấm nút **`📝 Dán Cookie Vào Bot`** bên dưới rồi dán toàn bộ vào!"
            ),
            inline=False
        )
        embed.add_field(
            name="📱 Cách 3: Lấy từ Tab Application / Storage",
            value=(
                "1. Nhấn `F12` trên trang HoYoLAB -> chọn thẻ **Application** (hoặc **Storage** trên Firefox).\n"
                "2. Ở menu trái, mở **Cookies** -> chọn `https://www.hoyolab.com`.\n"
                "3. Copy giá trị của **`ltuid_v2`** và **`ltoken_v2`**.\n"
                "4. Bấm **`📝 Dán Cookie Vào Bot`** và dán theo dạng: `ltuid_v2=...; ltoken_v2=...;`"
            ),
            inline=False
        )
        embed.add_field(
            name="⚠️ LƯU Ý CỰC KỲ QUAN TRỌNG",
            value=(
                "🚫 **TUYỆT ĐỐI KHÔNG BẤM \"ĐĂNG XUẤT\" TRÊN HOYOLAB!**\n"
                "Nếu bạn bấm Đăng xuất, HoYoverse sẽ lập tức hủy hiệu lực cookie đó trên máy chủ, dẫn đến lỗi `[-100] Phiên đăng nhập hết hiệu lực`. Sau khi copy cookie, chỉ cần **tắt tab trình duyệt** là xong.\n\n"
                "ℹ️ **Tại sao lệnh Console cũ `copy(document.cookie)` không hoạt động?**\n"
                "HoYoverse đã kích hoạt cờ bảo mật **`HttpOnly`** cho cookie `ltoken_v2`, nên trình duyệt chặn JavaScript truy cập. Vì vậy hãy copy qua thẻ **Network** F12 hoặc dùng **Đăng Nhập Tự Động**!"
            ),
            inline=False
        )
        embed.set_footer(text="Mã cookie ltoken chỉ dùng để điểm danh và an toàn tuyệt đối, không thể đổi mật khẩu.")
        return embed

    async def perform_checkin_for_account(self, account_cookies: dict, game_to_checkin: Optional[str] = None) -> str:
        """
        Thực hiện điểm danh tất cả các game của HoYoverse cho một tài khoản.
        Bắt toàn bộ các lỗi riêng lẻ của từng game để không ảnh hưởng đến các game khác.
        """
        if not account_cookies:
            return "Lỗi: Dữ liệu cookie trống."

        auth_cookies = {
            "ltoken_v2": account_cookies.get("ltoken_v2"),
            "ltuid_v2": account_cookies.get("ltuid_v2"),
            "ltoken": account_cookies.get("ltoken_v2"),
            "ltuid": account_cookies.get("ltuid_v2"),
            "account_id": account_cookies.get("ltuid_v2"),
            "account_id_v2": account_cookies.get("ltuid_v2"),
        }
        if account_cookies.get("cookie_token_v2"):
            auth_cookies["cookie_token_v2"] = account_cookies["cookie_token_v2"]
            auth_cookies["cookie_token"] = account_cookies["cookie_token_v2"]
        if account_cookies.get("ltmid_v2"):
            auth_cookies["ltmid_v2"] = account_cookies["ltmid_v2"]
            auth_cookies["account_mid_v2"] = account_cookies["ltmid_v2"]

        client = genshin.Client(auth_cookies, lang="vi-vn")
        results = []

        games_to_process = {}
        if game_to_checkin and game_to_checkin.lower() in GAMES:
            g_key = game_to_checkin.lower()
            games_to_process[g_key] = GAMES[g_key]
        else:
            games_to_process = GAMES

        for _, g_info in games_to_process.items():
            game_name = g_info["name"]
            game_enum = g_info["game"]
            emoji = g_info["emoji"]

            try:
                reward = await client.claim_daily_reward(game=game_enum)
                if reward:
                    results.append(f"✅ {emoji} **{game_name}:** Đã nhận `{reward.name}` (x{reward.amount})")
                else:
                    results.append(f"✅ {emoji} **{game_name}:** Điểm danh thành công!")
            except genshin.AlreadyClaimed:
                results.append(f"☑️ {emoji} **{game_name}:** Đã điểm danh hôm nay.")
            except genshin.InvalidCookies:
                results.append(
                    f"❌ {emoji} **{game_name}:** Cookie hết hạn hoặc không hợp lệ (Lỗi [-100]).\n"
                    "   *(Hãy dùng nút `🔐 Đăng Nhập Tự Động` hoặc copy header F12 Network; Tuyệt đối không bấm Đăng xuất trên web)*"
                )
                break  # Cookie sai hoàn toàn thì dừng các game tiếp theo
            except genshin.errors.DailyGeetestTriggered:
                results.append(f"⚠️ {emoji} **{game_name}:** HoYoLAB yêu cầu giải Captcha điểm danh hôm nay.")
            except genshin.errors.AccountNotFound:
                results.append(f"ℹ️ {emoji} **{game_name}:** Chưa tạo nhân vật hoặc không chơi game này.")
            except genshin.GenshinException as e:
                retcode = getattr(e, "retcode", None)
                msg_str = str(e).lower()
                if retcode in (-1004, -10002) or "character" in msg_str or "haven't created" in msg_str:
                    results.append(f"ℹ️ {emoji} **{game_name}:** Chưa tạo nhân vật trong game này.")
                else:
                    error_msg = getattr(e, "msg", str(e))
                    results.append(f"⚠️ {emoji} **{game_name}:** {error_msg}")
            except Exception as e:
                results.append(f"❌ {emoji} **{game_name}:** Lỗi - `{str(e)[:100]}`")

        return "\n".join(results)

    async def checkin_now_logic(self, interaction: discord.Interaction, account_name: Optional[str] = None, game: Optional[str] = None):
        """Logic điểm danh thủ công xử lý đa luồng."""
        if not interaction.response.is_done():
            await interaction.response.defer(ephemeral=True, thinking=True)

        user_id = str(interaction.user.id)
        user_accounts = self.cookies_data.get(user_id, [])

        if not user_accounts:
            return await interaction.followup.send("❌ Bạn chưa lưu tài khoản nào. Vui lòng thêm cookie trước!", ephemeral=True)

        accounts_to_check = []
        if account_name and account_name != "all":
            acc = next((a for a in user_accounts if a.get("name", "").lower() == account_name.lower()), None)
            if acc:
                accounts_to_check.append(acc)
            else:
                return await interaction.followup.send(f"❌ Không tìm thấy tài khoản có tên `{account_name}`.", ephemeral=True)
        else:
            accounts_to_check = user_accounts

        full_results = []
        for account in accounts_to_check:
            acc_name = account.get("name", "Tài khoản không tên")
            res_msg = await self.perform_checkin_for_account(account, game_to_checkin=game)
            full_results.append(f"### 👤 Tài khoản: `{acc_name}`\n{res_msg}")

        game_title = GAMES[game]["name"] if (game and game in GAMES) else "Tất cả các Game"
        embed = discord.Embed(
            title="📝 Kết Quả Điểm Danh Thủ Công",
            description=f"**Mục tiêu:** {game_title}\n\n" + "\n\n".join(full_results),
            color=discord.Color.blue()
        )
        embed.timestamp = datetime.now(timezone.utc)
        await interaction.followup.send(embed=embed, ephemeral=True)

    async def toggle_auto_logic(self, interaction: discord.Interaction, management_view: Optional[Any] = None):
        """Mở giao diện bật/tắt tự động điểm danh."""
        user_id = str(interaction.user.id)
        user_accounts = self.cookies_data.get(user_id, [])

        if not user_accounts:
            return await interaction.response.send_message("❌ Bạn chưa có tài khoản nào để cấu hình.", ephemeral=True)

        view = ToggleView(user_accounts, interaction.user.id, management_view=management_view, cog_instance=self)
        await interaction.response.send_message("Chọn các tài khoản bạn muốn **BẬT** tự động điểm danh hàng ngày:", view=view, ephemeral=True)

    # ==========================
    # HYBRID COMMANDS
    # ==========================
    @commands.hybrid_group(name="hoyolab", aliases=["hoyo"], description="Quản lý điểm danh tự động cho các game HoYoverse.")
    async def hoyocheckin(self, ctx: commands.Context):
        """Bảng điều khiển chung cho hệ thống HoYoLAB."""
        if ctx.invoked_subcommand is None:
            prefix = ctx.prefix
            embed = discord.Embed(
                title="⚙️ Bảng Điều Khiển HoYoLAB Check-in",
                description="Hệ thống tự động điểm danh nhận quà hàng ngày cho Genshin, Star Rail, ZZZ và Honkai 3rd.",
                color=discord.Color.from_rgb(108, 92, 231)
            )
            if self.bot.user.avatar:
                embed.set_thumbnail(url=self.bot.user.avatar.url)

            embed.add_field(
                name="✨ Lệnh Thường Dùng (Phong cách Hoyo Buddy)",
                value=(
                    f"• `{prefix}hoyolab manage` - Mở bảng điều khiển tương tác (đầy đủ nút bấm).\n"
                    f"• `{prefix}hoyolab notes` - Xem Nhựa, Sức mạnh khai phá, Điện năng & Ủy thác thời gian thực.\n"
                    f"• `{prefix}hoyolab overview` - Xem chi tiết điểm danh, lịch nhận Nguyên Thạch & bù điểm danh.\n"
                    f"• `{prefix}hoyolab accompany` - Tương tác đồng hành nhân vật Mimo nhận điểm đổi quà.\n"
                    f"• `{prefix}hoyolab login` - Tự động đăng nhập tài khoản HoYoverse (vượt Captcha & OTP).\n"
                    f"• `{prefix}hoyolab redeem <code>` - Tự động nhập Giftcode vào game.\n"
                    f"• `{prefix}hoyolab daily checkin` - Điểm danh ngay lập tức."
                ),
                inline=False
            )
            embed.add_field(
                name="🔧 Cấu Hình & Quản Lý",
                value=(
                    f"• `{prefix}hoyolab setcookie` - Thêm/Cập nhật cookie thông minh.\n"
                    f"• `{prefix}hoyolab toggle` - Bật/tắt tự động điểm danh.\n"
                    f"• `{prefix}hoyolab delcookie <tên>` - Xóa tài khoản đã lưu.\n"
                    f"• `{prefix}hoyolab guide` - Xem hướng dẫn chi tiết."
                ),
                inline=False
            )
            embed.set_footer(text="Gõ /hoyolab manage để mở bảng tương tác đầy đủ với các nút bấm.")
            await ctx.send(embed=embed)

    @hoyocheckin.command(name="manage", description="Mở bảng điều khiển tương tác quản lý tài khoản HoYoLAB.")
    async def manage(self, ctx: commands.Context):
        """Mở bảng điều khiển quản lý tài khoản."""
        embed = self.create_management_embed(ctx.author)
        view = ManagementView(ctx.author, self)
        user_accounts = self.cookies_data.get(str(ctx.author.id), [])
        if user_accounts:
            view.add_item(CheckinSelect(self, user_accounts))

        msg = await ctx.send(embed=embed, view=view, ephemeral=True)
        view.message = msg

    @hoyocheckin.command(name="quickcode", aliases=["getcookie", "bookmarklet"], description="Công cụ lấy mã Cookie HoYoLAB siêu nhanh trong 5 giây.")
    async def quickcode(self, ctx: commands.Context):
        """Hiển thị công cụ lấy mã nhanh bằng Bookmarklet hoặc Console."""
        embed = self.create_quick_code_embed()
        view = QuickCodeView(ctx.author.id, cog_instance=self)
        await ctx.send(embed=embed, view=view, ephemeral=True)

    @hoyocheckin.command(name="login", description="Tự động đăng nhập tài khoản HoYoverse để lấy mã (phong cách Hoyo Buddy).")
    async def login_cmd(self, ctx: commands.Context):
        """Mở form đăng nhập bằng tài khoản HoYoverse."""
        if ctx.interaction:
            await ctx.interaction.response.send_modal(HoyoBuddyLoginModal(cog_instance=self))
        else:
            await ctx.send("❌ Vui lòng sử dụng Slash Command `/hoyolab login` để mở form nhập mật khẩu an toàn.", ephemeral=True)

    @hoyocheckin.command(name="setcookie", description="Thiết lập hoặc cập nhật cookie HoYoLAB của bạn.")
    async def setcookie(self, ctx: commands.Context):
        """Thêm hoặc sửa cookie HoYoLAB."""
        if ctx.interaction:
            return await ctx.interaction.response.send_modal(SmartCookieModal(cog_instance=self))

        # Nếu là Prefix command, gửi hướng dẫn qua DM
        try:
            embed = discord.Embed(
                title="🌸 Thiết Lập Cookie HoYoLAB (Prefix)",
                description=(
                    "Vui lòng trả lời tin nhắn này với thông tin cookie của bạn theo cú pháp:\n\n"
                    "```\n"
                    "Tên: Acc chính\n"
                    "ltuid_v2=12345678; ltoken_v2=v2_xxxxx\n"
                    "```\n"
                    "*(Bạn có thể dán toàn bộ mã từ Bookmarklet hoặc document.cookie, bot sẽ tự nhận diện)*"
                ),
                color=discord.Color.purple()
            )
            await ctx.author.send(embed=embed)
            await ctx.send("✅ Đã gửi hướng dẫn thiết lập cookie vào tin nhắn riêng (DM) của bạn!", ephemeral=True)
        except discord.Forbidden:
            return await ctx.send("❌ Không thể gửi tin nhắn DM cho bạn. Vui lòng mở DM hoặc dùng Slash Command `/hoyolab setcookie`.", ephemeral=True)

        def check(m):
            return m.author.id == ctx.author.id and isinstance(m.channel, discord.DMChannel)

        try:
            msg = await self.bot.wait_for("message", timeout=300.0, check=check)
            content = msg.content

            name_match = re.search(r"Tên:\s*([^\n\r]+)", content, re.IGNORECASE)
            account_name = name_match.group(1).strip() if name_match else "Acc HoYoLAB"

            parsed = extract_hoyolab_cookies(content)
            if not parsed.get("ltuid_v2") or not parsed.get("ltoken_v2"):
                return await ctx.author.send("❌ Không tìm thấy đủ `ltuid_v2` và `ltoken_v2`. Vui lòng dùng lệnh `/hoyolab quickcode` để lấy mã chuẩn!")

            user_id = str(ctx.author.id)
            cookies = load_cookies()
            if user_id not in cookies:
                cookies[user_id] = []
            elif isinstance(cookies[user_id], dict):
                cookies[user_id] = [cookies[user_id]]

            new_account = {
                "name": account_name,
                "ltoken_v2": parsed["ltoken_v2"],
                "ltuid_v2": parsed["ltuid_v2"],
                "auto_checkin": True
            }
            if "cookie_token_v2" in parsed:
                new_account["cookie_token_v2"] = parsed["cookie_token_v2"]
            if "ltmid_v2" in parsed:
                new_account["ltmid_v2"] = parsed["ltmid_v2"]

            account_found = False
            for i, acc in enumerate(cookies[user_id]):
                if acc.get("name") == account_name:
                    cookies[user_id][i] = new_account
                    account_found = True
                    break
            if not account_found:
                cookies[user_id].append(new_account)

            save_cookies(cookies)
            self.cookies_data = cookies
            await ctx.author.send(f"✅ Đã lưu thành công cookie cho tài khoản **{account_name}**!")

        except asyncio.TimeoutError:
            await ctx.author.send("⏰ Đã hết thời gian nhập cookie. Vui lòng thử lại bằng lệnh `/hoyolab setcookie` trên server.")

    @hoyocheckin.command(name="guide", description="Hướng dẫn chi tiết cách lấy cookie HoYoLAB an toàn.")
    async def guide(self, ctx: commands.Context):
        """Hiển thị hướng dẫn lấy cookie chi tiết."""
        embed = discord.Embed(
            title="❓ Hướng Dẫn Lấy Cookie HoYoLAB An Toàn & Chi Tiết",
            description="Làm theo các bước sau để lấy cookie cần thiết cho việc điểm danh tự động.",
            color=discord.Color.blue()
        )
        embed.add_field(
            name="Cách 1: Lấy Mã Nhanh 1 Chạm (Khuyên Dùng)",
            value="Gõ lệnh `/hoyolab quickcode` để sử dụng Bookmarklet 1 chạm hoặc lệnh Console F12 tự động.",
            inline=False
        )
        embed.add_field(
            name="Cách 2: Lấy Thủ Công Từ DevTools",
            value=(
                "1. Truy cập **[hoyolab.com](https://www.hoyolab.com/home)** và đăng nhập.\n"
                "2. Nhấn `F12` (hoặc `Ctrl+Shift+I`) để mở DevTools.\n"
                "3. Chuyển sang thẻ **Application** (Ứng dụng) -> chọn **Cookies** -> `https://www.hoyolab.com`.\n"
                "4. Tìm và sao chép 2 giá trị: `ltuid_v2` và `ltoken_v2`.\n"
                "5. Dán vào SakuraBot bằng lệnh `/hoyolab setcookie`."
            ),
            inline=False
        )
        embed.add_field(
            name="🔒 Vấn Đề Bảo Mật",
            value=(
                "• Cookie `ltoken_v2` chỉ có quyền đọc thông tin sự kiện và nhận quà hàng ngày.\n"
                "• **TUYỆT ĐỐI KHÔNG** thể đổi mật khẩu, không thể liên kết email mới hay chiếm đoạt tài khoản game của bạn.\n"
                "• An toàn hơn nhiều so với việc nhập mật khẩu tài khoản game!"
            ),
            inline=False
        )
        embed.set_footer(text="Lưu ý: Không chia sẻ cookie của bạn cho bất kỳ ai ngoài bot đáng tin cậy.")
        await ctx.send(embed=embed, ephemeral=True)

    @hoyocheckin.group(name="daily", description="Các lệnh liên quan đến điểm danh hàng ngày.")
    async def daily(self, ctx: commands.Context):
        """Nhóm lệnh con cho hoạt động điểm danh."""
        if ctx.invoked_subcommand is None:
            await ctx.invoke(self.checkin_now)

    @daily.command(name="checkin", description="Điểm danh ngay lập tức cho các game HoYoverse.")
    @commands.cooldown(1, 30, commands.BucketType.user)
    @app_commands.describe(
        account_name="Tên tài khoản (để trống hoặc chọn 'all' để điểm danh tất cả acc)",
        game="Tên game (để trống để điểm danh tất cả game)"
    )
    @app_commands.choices(game=[
        app_commands.Choice(name="🌸 Tất cả game", value="all"),
        app_commands.Choice(name="🌸 Genshin Impact", value="genshin"),
        app_commands.Choice(name="🚂 Honkai: Star Rail", value="hsr"),
        app_commands.Choice(name="⚡ Zenless Zone Zero", value="zzz"),
        app_commands.Choice(name="⚔️ Honkai Impact 3rd", value="bh3"),
    ])
    async def checkin_now(self, ctx: commands.Context, account_name: Optional[str] = None, game: Optional[str] = None):
        """Thực hiện điểm danh thủ công."""
        actual_game = None if (not game or game == "all") else game
        actual_acc = None if (not account_name or account_name == "all") else account_name

        if ctx.interaction:
            await self.checkin_now_logic(ctx.interaction, account_name=actual_acc, game=actual_game)
        else:
            # Fallback cho prefix command
            msg = await ctx.send("⏳ Đang tiến hành điểm danh...")
            user_id = str(ctx.author.id)
            user_accounts = self.cookies_data.get(user_id, [])
            if not user_accounts:
                return await msg.edit(content="❌ Bạn chưa lưu tài khoản nào. Dùng `/hoyolab setcookie` để thêm nhé!")

            accounts_to_check = []
            if actual_acc:
                acc = next((a for a in user_accounts if a.get("name", "").lower() == actual_acc.lower()), None)
                if acc:
                    accounts_to_check.append(acc)
                else:
                    return await msg.edit(content=f"❌ Không tìm thấy tài khoản `{actual_acc}`.")
            else:
                accounts_to_check = user_accounts

            full_results = []
            for a in accounts_to_check:
                r_msg = await self.perform_checkin_for_account(a, game_to_checkin=actual_game)
                full_results.append(f"### 👤 Tài khoản: `{a.get('name', 'N/A')}`\n{r_msg}")

            game_title = GAMES[actual_game]["name"] if actual_game else "Tất cả các Game"
            embed = discord.Embed(
                title="📝 Kết Quả Điểm Danh Thủ Công",
                description=f"**Mục tiêu:** {game_title}\n\n" + "\n\n".join(full_results),
                color=discord.Color.blue()
            )
            embed.timestamp = datetime.now(timezone.utc)
            await msg.edit(content=None, embed=embed)

    @checkin_now.autocomplete("account_name")
    async def checkin_account_autocomplete(self, interaction: discord.Interaction, current: str) -> list[app_commands.Choice[str]]:
        """Autocomplete danh sách tài khoản cho lệnh điểm danh."""
        user_id = str(interaction.user.id)
        accounts = self.cookies_data.get(user_id, [])
        choices = [app_commands.Choice(name="🌟 Tất cả tài khoản", value="all")]
        for acc in accounts:
            name = acc.get("name", "N/A")
            if current.lower() in name.lower():
                choices.append(app_commands.Choice(name=name, value=name))
        return choices[:25]

    @hoyocheckin.command(name="toggle", description="Bật/Tắt chế độ tự động điểm danh hàng ngày.")
    async def toggle_auto(self, ctx: commands.Context):
        """Bật hoặc tắt tự động điểm danh."""
        if ctx.interaction:
            await self.toggle_auto_logic(ctx.interaction)
        else:
            await ctx.send("❌ Vui lòng dùng Slash Command `/hoyolab toggle` để sử dụng menu chọn trực quan.", ephemeral=True)

    @hoyocheckin.command(name="status", description="Xem trạng thái các tài khoản HoYoLAB đã lưu.")
    async def check_status(self, ctx: commands.Context):
        """Kiểm tra trạng thái cài đặt."""
        user_id = str(ctx.author.id)
        user_accounts = self.cookies_data.get(user_id, [])

        if not user_accounts:
            return await ctx.send("❌ Bạn chưa cài đặt tài khoản nào. Dùng lệnh `/hoyolab setcookie` hoặc `/hoyolab manage`.", ephemeral=True)

        embed = discord.Embed(
            title=f"📊 Trạng Thái Tài Khoản của {ctx.author.display_name}",
            description="Danh sách các tài khoản HoYoLAB và trạng thái điểm danh tự động:",
            color=discord.Color.purple()
        )
        for acc in user_accounts:
            name = acc.get("name", "Tài khoản không tên")
            uid = acc.get("ltuid_v2", "N/A")
            auto_status = "🟢 Đang BẬT" if acc.get("auto_checkin", False) else "🔴 Đang TẮT"
            embed.add_field(
                name=f"👤 `{name}`",
                value=f"• UID: `{uid}`\n• Tự động: {auto_status}",
                inline=True
            )

        embed.set_footer(text="Lịch tự động điểm danh: 01:00 AM mỗi ngày.")
        embed.timestamp = datetime.now(timezone.utc)
        await ctx.send(embed=embed, ephemeral=True)

    @hoyocheckin.command(name="delcookie", description="Xóa một tài khoản HoYoLAB đã lưu.")
    @app_commands.describe(ten_tai_khoan="Tên tài khoản bạn muốn xóa")
    async def delcookie(self, ctx: commands.Context, *, ten_tai_khoan: str):
        """Xóa một cookie đã lưu theo tên."""
        user_id = str(ctx.author.id)
        cookies = load_cookies()
        user_accounts = cookies.get(user_id, [])

        account_to_delete = None
        for acc in user_accounts:
            if acc.get("name", "").lower() == ten_tai_khoan.lower():
                account_to_delete = acc
                break

        if not account_to_delete:
            return await ctx.send(f"❌ Không tìm thấy tài khoản nào có tên `{ten_tai_khoan}`.", ephemeral=True)

        user_accounts.remove(account_to_delete)
        save_cookies(cookies)
        self.cookies_data = cookies

        await ctx.send(f"✅ Đã xóa thành công tài khoản **{ten_tai_khoan}**.", ephemeral=True)

    @delcookie.autocomplete("ten_tai_khoan")
    async def delcookie_autocomplete(self, interaction: discord.Interaction, current: str) -> list[app_commands.Choice[str]]:
        """Autocomplete danh sách tài khoản cần xóa."""
        user_id = str(interaction.user.id)
        accounts = self.cookies_data.get(user_id, [])
        choices = []
        for acc in accounts:
            name = acc.get("name", "N/A")
            if current.lower() in name.lower():
                choices.append(app_commands.Choice(name=name, value=name))
        return choices[:25]

    @hoyocheckin.command(name="redeem", description="🎁 Nhập giftcode tự động cho tài khoản HoYoverse đã liên kết.")
    @app_commands.describe(
        code="Mã giftcode cần nhập (ví dụ: GENSHINGIFT, STARRAILGIFT...)",
        game="Chọn game cần nhập mã (hoặc để trống để tự động nhận diện)",
        account_name="Tên tài khoản (để trống để nhập cho tất cả tài khoản)"
    )
    @app_commands.choices(game=[
        app_commands.Choice(name="🌸 Tất cả game", value="all"),
        app_commands.Choice(name="🌸 Genshin Impact", value="genshin"),
        app_commands.Choice(name="🚂 Honkai: Star Rail", value="hsr"),
        app_commands.Choice(name="⚡ Zenless Zone Zero", value="zzz"),
    ])
    async def redeem_code_cmd(self, ctx: commands.Context, code: str, game: Optional[str] = None, account_name: Optional[str] = None):
        """Đổi mã giftcode vào tài khoản game HoYoverse."""
        if ctx.interaction:
            await ctx.interaction.response.defer(ephemeral=True, thinking=True)
            send_fn = ctx.interaction.followup.send
        else:
            msg = await ctx.send("⏳ Đang tiến hành đổi mã giftcode...")
            send_fn = msg.edit

        user_id = str(ctx.author.id)
        user_accounts = self.cookies_data.get(user_id, [])
        if not user_accounts:
            err_msg = "❌ **Bạn chưa liên kết tài khoản HoYoverse nào!**\n👉 Dùng lệnh `/hoyolab login` hoặc `/hoyolab setcookie` để liên kết nhé."
            if ctx.interaction:
                return await send_fn(err_msg, ephemeral=True)
            return await send_fn(content=err_msg)

        actual_game = None if (not game or game == "all") else game
        actual_acc = None if (not account_name or account_name == "all") else account_name

        targets = []
        if actual_acc:
            acc = next((a for a in user_accounts if a.get("name", "").lower() == actual_acc.lower()), None)
            if not acc:
                err_msg = f"❌ Không tìm thấy tài khoản mang tên `{actual_acc}`."
                if ctx.interaction: return await send_fn(err_msg, ephemeral=True)
                return await send_fn(content=err_msg)
            targets.append(acc)
        else:
            targets = user_accounts

        all_results = []
        clean_code = code.strip().upper()
        for acc in targets:
            res_lines = await redeem_code_for_single_account(acc, clean_code, target_game=actual_game)
            all_results.append(f"### 👤 Tài khoản: `{acc.get('name', 'N/A')}`\n" + "\n".join(res_lines))

        embed = discord.Embed(
            title=f"🎁 Kết Quả Đổi Giftcode: `{clean_code}`",
            description="\n\n".join(all_results),
            color=discord.Color.brand_green()
        )
        embed.timestamp = datetime.now(timezone.utc)
        embed.set_footer(text="SakuraBot | HoYoLAB Auto Code")

        if ctx.interaction:
            await send_fn(embed=embed, ephemeral=True)
        else:
            await send_fn(content=None, embed=embed)

    async def handle_quick_redeem_interaction(self, interaction: discord.Interaction, game_key: str, code: str):
        """Xử lý khi người dùng bấm nút [Nhập Vào Game 🎁] trên tin nhắn thông báo code."""
        user_id = str(interaction.user.id)
        user_accounts = self.cookies_data.get(user_id, [])
        if not user_accounts:
            return await interaction.followup.send(
                "⚠️ **Bạn chưa liên kết tài khoản HoYoverse với SakuraBot!**\n"
                "👉 Dùng `/hoyolab login` để đăng nhập nhanh hoặc `/hoyolab setcookie` để thêm tài khoản và nhập code 1 chạm.",
                ephemeral=True
            )

        clean_code = code.strip().upper()
        all_results = []
        for acc in user_accounts:
            res_lines = await redeem_code_for_single_account(acc, clean_code, target_game=game_key)
            all_results.append(f"### 👤 Tài khoản: `{acc.get('name', 'N/A')}`\n" + "\n".join(res_lines))

        embed = discord.Embed(
            title=f"🎁 Kết Quả Nhập Mã: `{clean_code}` ({GAMES.get(game_key, {}).get('name', game_key)})",
            description="\n\n".join(all_results),
            color=discord.Color.green()
        )
        embed.timestamp = datetime.now(timezone.utc)
        embed.set_footer(text="SakuraBot | Auto Code 1-Click")
        await interaction.followup.send(embed=embed, ephemeral=True)

    async def auto_redeem_new_code(self, game_key: str, code: str):
        """Tự động đổi giftcode mới tìm thấy cho tất cả tài khoản đã bật auto_redeem."""
        if game_key not in REDEEM_SUPPORTED_GAMES:
            return

        clean_code = code.strip().upper()
        print(f"[AutoRedeem] Bắt đầu tự động nhập giftcode mới: {clean_code} ({game_key})...")
        
        self.cookies_data = load_cookies()
        for user_id, acc_list in list(self.cookies_data.items()):
            if isinstance(acc_list, dict):
                acc_list = [acc_list]
            for acc in acc_list:
                # Mặc định auto_redeem là True nếu chưa cài đặt
                if not acc.get("auto_redeem", True):
                    continue

                try:
                    res_lines = await redeem_code_for_single_account(acc, clean_code, target_game=game_key)
                    print(f"[AutoRedeem] User {user_id} - Acc {acc.get('name')}: {res_lines}")
                except Exception as e:
                    print(f"[AutoRedeem Error] User {user_id} - Acc {acc.get('name')}: {e}")
                await asyncio.sleep(2.0)

    async def accompany_logic(self, interaction: discord.Interaction, account_name: Optional[str] = None):
        """Logic tương tác đồng hành nhân vật Mimo trên HoYoLAB (Hoyo Buddy style)."""
        user_id = str(interaction.user.id)
        user_accounts = self.cookies_data.get(user_id, [])
        if not user_accounts:
            return await interaction.followup.send("❌ Bạn chưa có tài khoản nào được lưu.", ephemeral=True)

        accounts_to_run = user_accounts
        if account_name:
            acc = next((a for a in user_accounts if a.get("name", "").lower() == account_name.lower()), None)
            if acc:
                accounts_to_run = [acc]
            else:
                return await interaction.followup.send(f"❌ Không tìm thấy tài khoản `{account_name}`.", ephemeral=True)

        full_results = []
        for a in accounts_to_run:
            a_name = a.get("name", "Tài khoản")
            client = build_genshin_client(a)
            try:
                char_games = await client.get_accompany_characters()
                total_pts = 0
                acc_chars_info = []

                chars_to_accompany = []
                for cg in char_games:
                    for ch in cg.characters:
                        chars_to_accompany.append(ch)
                        if len(chars_to_accompany) >= 3:
                            break
                    if len(chars_to_accompany) >= 3:
                        break

                for ch in chars_to_accompany:
                    try:
                        res = await client.accompany_character(role_id=ch.role_id, topic_id=ch.topic_id)
                        total_pts += res.points_increased
                        acc_chars_info.append(f"• **{ch.name}**: +{res.points_increased} điểm (đã đồng hành {res.accompany_days} ngày)")
                        await asyncio.sleep(1.0)
                    except Exception:
                        pass

                if acc_chars_info:
                    full_results.append(f"**👤 Tài khoản `{a_name}`:**\n" + "\n".join(acc_chars_info) + f"\n👉 *Tổng nhận: +{total_pts} điểm Mimo!*")
                else:
                    full_results.append(f"**👤 Tài khoản `{a_name}`:** Hôm nay bạn đã đồng hành với các nhân vật này rồi.")
            except genshin.InvalidCookies:
                full_results.append(f"**👤 Tài khoản `{a_name}`:** ❌ Cookie hết hạn hoặc không hợp lệ (Lỗi -100).")
            except Exception as e:
                full_results.append(f"**👤 Tài khoản `{a_name}`:** ⚠️ Lỗi: `{e}`")

        embed = discord.Embed(
            title="🕊️ Kết Quả Đồng Hành Nhân Vật HoYoLAB (Mimo Task)",
            description="\n\n".join(full_results),
            color=discord.Color.green(),
            timestamp=datetime.now(timezone.utc)
        )
        embed.set_footer(text="Hoyo Buddy Accompany • Tích điểm Mimo đổi quà trên HoYoLAB")
        await interaction.followup.send(embed=embed, ephemeral=True)

    @hoyocheckin.command(name="notes", description="📊 Xem Nhựa, Sức mạnh khai phá, Ủy thác, Điện năng ingame thời gian thực (Hoyo Buddy).")
    @app_commands.describe(
        game="Chọn game để xem (mặc định là Genshin)",
        account_name="Tên tài khoản muốn xem (để trống nếu dùng tài khoản đầu tiên)"
    )
    @app_commands.choices(game=[
        app_commands.Choice(name="🌸 Genshin Impact", value="genshin"),
        app_commands.Choice(name="🚂 Honkai: Star Rail", value="hsr"),
        app_commands.Choice(name="⚡ Zenless Zone Zero", value="zzz"),
    ])
    async def notes_command(self, ctx: commands.Context, game: Optional[str] = "genshin", account_name: Optional[str] = None):
        """Xem tài nguyên ingame thời gian thực (Hoyo Buddy Notes)."""
        if ctx.interaction:
            await ctx.interaction.response.defer(ephemeral=True, thinking=True)
        user_id = str(ctx.author.id)
        user_accounts = self.cookies_data.get(user_id, [])
        if not user_accounts:
            msg = "❌ Bạn chưa có tài khoản nào được lưu. Dùng `/hoyolab setcookie` hoặc nút `Đăng Nhập HoYoverse` nhé!"
            if ctx.interaction:
                return await ctx.interaction.followup.send(msg, ephemeral=True)
            return await ctx.send(msg)

        init_idx = 0
        if account_name:
            for idx, a in enumerate(user_accounts):
                if a.get("name", "").lower() == account_name.lower():
                    init_idx = idx
                    break

        view = HoyoNotesView(ctx.author, user_accounts, initial_acc_idx=init_idx, initial_game=game or "genshin", cog_instance=self)
        embed = await view.get_notes_embed()
        if ctx.interaction:
            await ctx.interaction.followup.send(embed=embed, view=view, ephemeral=True)
        else:
            await ctx.send(embed=embed, view=view)

    @hoyocheckin.command(name="overview", aliases=["info", "calendar"], description="🎁 Xem chi tiết điểm danh, lịch nhận Nguyên Thạch và quà tháng HoYoLAB.")
    @app_commands.describe(
        game="Chọn game để xem (mặc định là Genshin)",
        account_name="Tên tài khoản muốn xem"
    )
    @app_commands.choices(game=[
        app_commands.Choice(name="🌸 Genshin Impact", value="genshin"),
        app_commands.Choice(name="🚂 Honkai: Star Rail", value="hsr"),
        app_commands.Choice(name="⚡ Zenless Zone Zero", value="zzz"),
        app_commands.Choice(name="⚔️ Honkai Impact 3rd", value="bh3"),
    ])
    async def overview_command(self, ctx: commands.Context, game: Optional[str] = "genshin", account_name: Optional[str] = None):
        """Xem tổng quan điểm danh tháng và lịch nhận quà (Hoyo Buddy style)."""
        if ctx.interaction:
            await ctx.interaction.response.defer(ephemeral=True, thinking=True)
        user_id = str(ctx.author.id)
        user_accounts = self.cookies_data.get(user_id, [])
        if not user_accounts:
            msg = "❌ Bạn chưa có tài khoản nào được lưu. Dùng `/hoyolab setcookie` hoặc nút `Đăng Nhập HoYoverse` nhé!"
            if ctx.interaction:
                return await ctx.interaction.followup.send(msg, ephemeral=True)
            return await ctx.send(msg)

        init_idx = 0
        if account_name:
            for idx, a in enumerate(user_accounts):
                if a.get("name", "").lower() == account_name.lower():
                    init_idx = idx
                    break

        view = HoyoCheckinOverviewView(ctx.author, user_accounts, initial_acc_idx=init_idx, initial_game=game or "genshin", cog_instance=self)
        embed = await view.get_checkin_embed()
        if ctx.interaction:
            await ctx.interaction.followup.send(embed=embed, view=view, ephemeral=True)
        else:
            await ctx.send(embed=embed, view=view)

    @hoyocheckin.command(name="accompany", description="🕊️ Tương tác đồng hành nhân vật Mimo trên HoYoLAB để nhận điểm thưởng.")
    @app_commands.describe(account_name="Tên tài khoản (để trống để chạy cho tài khoản chính)")
    async def accompany_command(self, ctx: commands.Context, account_name: Optional[str] = None):
        """Thực hiện tương tác đồng hành nhân vật Mimo trên HoYoLAB."""
        if ctx.interaction:
            await ctx.interaction.response.defer(ephemeral=True, thinking=True)
            await self.accompany_logic(ctx.interaction, account_name=account_name)
        else:
            msg = await ctx.send("⏳ Đang tương tác đồng hành nhân vật HoYoLAB...")
            user_id = str(ctx.author.id)
            user_accounts = self.cookies_data.get(user_id, [])
            if not user_accounts:
                return await msg.edit(content="❌ Bạn chưa có tài khoản nào được lưu.")
            class MockInteraction:
                def __init__(self, message, author):
                    self.message = message
                    self.user = author
                    self.followup = self
                async def send(self, *args, **kwargs):
                    return await self.message.edit(content=kwargs.get("content"), embed=kwargs.get("embed"))
            mock_i = MockInteraction(msg, ctx.author)
            await self.accompany_logic(mock_i, account_name=account_name)

    # ==========================
    # BACKGROUND TASK
    # ==========================
    @tasks.loop(time=time(hour=1, minute=0, tzinfo=timezone(timedelta(hours=7))))
    async def auto_checkin_task(self):
        """Tác vụ chạy nền lúc 01:00 AM VN mỗi ngày để tự động điểm danh cho mọi user."""
        print(f"[{datetime.now():%Y-%m-%d %H:%M:%S}] 🚀 Bắt đầu tác vụ tự động điểm danh HoYoLAB...")
        self.cookies_data = load_cookies()

        total_users = 0
        total_accounts = 0

        for user_id, accounts in self.cookies_data.items():
            if not isinstance(accounts, list):
                continue

            accounts_to_checkin = [acc for acc in accounts if acc.get("auto_checkin", False)]
            if not accounts_to_checkin:
                continue

            total_users += 1
            full_results = []
            has_error = False
            has_success = False

            for account in accounts_to_checkin:
                total_accounts += 1
                acc_name = account.get("name", "Tài khoản không tên")
                try:
                    print(f"  -> Đang điểm danh cho '{acc_name}' (User: {user_id})")
                    result_msg = await self.perform_checkin_for_account(account)

                    if "❌" in result_msg:
                        has_error = True
                    if "✅" in result_msg or "☑️" in result_msg:
                        has_success = True

                    full_results.append(f"### 👤 Tài khoản: `{acc_name}`\n{result_msg}")
                except Exception as e:
                    print(f"  -> ❌ Lỗi ngoại lệ tài khoản '{acc_name}': {e}")
                    full_results.append(f"### 👤 Tài khoản: `{acc_name}`\n❌ Lỗi hệ thống: `{e}`")
                    has_error = True

            if full_results:
                try:
                    user = await self.bot.fetch_user(int(user_id))
                    color = discord.Color.green()
                    if has_error and not has_success:
                        color = discord.Color.red()
                    elif has_error and has_success:
                        color = discord.Color.orange()

                    embed = discord.Embed(
                        title="🌸 Kết Quả Tự Động Điểm Danh HoYoLAB Hàng Ngày",
                        description="\n\n".join(full_results),
                        color=color,
                        timestamp=datetime.now(timezone.utc)
                    )
                    embed.set_footer(text="SakuraBot Auto Check-in • Đã hoàn thành điểm danh lúc 01:00 AM")
                    await user.send(embed=embed)
                except discord.Forbidden:
                    print(f"  -> ⚠️ Không thể gửi DM cho User {user_id} (bị chặn DM hoặc tắt DM).")
                except Exception as e:
                    print(f"  -> ❌ Lỗi khi gửi DM cho User {user_id}: {e}")

        print(f"[{datetime.now():%Y-%m-%d %H:%M:%S}] ✅ Hoàn tất điểm danh: {total_accounts} tài khoản của {total_users} người dùng.")

    @auto_checkin_task.before_loop
    async def before_auto_checkin_task(self):
        await self.bot.wait_until_ready()

async def setup(bot: commands.Bot):
    await bot.add_cog(HoyolabCheckinCog(bot))
