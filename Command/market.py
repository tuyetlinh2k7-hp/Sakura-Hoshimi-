from Check.i18n import t, is_vietnamese
import asyncio
import json
import math
import random
import time
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Literal, Optional

import discord
from discord import app_commands
from discord.ext import commands, tasks

from Check.mod import is_owner, OWNER_ID
from data.database import get_user_data, update_user_coins
try:
    from data.data import RARITY_ICONS, RARITY_COLORS
except ImportError:
    RARITY_ICONS = {"common": "⚪", "rare": "🔵", "epic": "🟣", "legendary": "🟡", "admin": "🔴"}
    RARITY_COLORS = {"common": discord.Color.light_grey(), "rare": discord.Color.blue(), "epic": discord.Color.purple(), "legendary": discord.Color.gold(), "admin": discord.Color.red()}

BASE_DIR = Path(__file__).resolve().parent.parent
FISHING_DATA_FILE = BASE_DIR / "data" / "fishing_inventory.json"
MARKET_DATA_FILE = BASE_DIR / "data" / "p2p_market.json"

# ==============================================================================
# QUẢN LÝ DỮ LIỆU CHỢ & PHÍ SÀN
# ==============================================================================
market_state = {
    "listings": [],  # Danh sách đơn hàng
    "merchant_rates": {},
    "hourly_sold_volume": {},
    "last_rate_update": 0,
}


def load_all_data():
    global market_state
    if MARKET_DATA_FILE.exists():
        try:
            with open(MARKET_DATA_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                if isinstance(data, dict):
                    market_state.update(data)
        except Exception:
            pass


def save_market_data():
    MARKET_DATA_FILE.parent.mkdir(parents=True, exist_ok=True)
    try:
        with open(MARKET_DATA_FILE, "w", encoding="utf-8") as f:
            json.dump(market_state, f, indent=4, ensure_ascii=False)
    except Exception:
        pass


def load_fishing_users() -> dict:
    try:
        from Command.command_fishing import fishing_state
        if "users" in fishing_state:
            return fishing_state["users"]
    except Exception:
        pass
    if FISHING_DATA_FILE.exists():
        try:
            with open(FISHING_DATA_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                return data.get("users", {})
        except Exception:
            return {}
    return {}


def save_fishing_users(users: dict):
    try:
        from Command.command_fishing import fishing_state, save_fishing_data
        fishing_state["users"] = users
        save_fishing_data()
        return
    except Exception:
        pass
    FISHING_DATA_FILE.parent.mkdir(parents=True, exist_ok=True)
    try:
        existing = {}
        if FISHING_DATA_FILE.exists():
            with open(FISHING_DATA_FILE, "r", encoding="utf-8") as f:
                existing = json.load(f)
        existing["users"] = users
        with open(FISHING_DATA_FILE, "w", encoding="utf-8") as f:
            json.dump(existing, f, indent=4, ensure_ascii=False)
    except Exception:
        pass


def get_user_fishing_data(user_id: int) -> dict:
    try:
        from Command.command_fishing import get_user_fishing
        return get_user_fishing(user_id)
    except Exception:
        users = load_fishing_users()
        return users.setdefault(str(user_id), {})


load_all_data()


def update_merchant_rates(force: bool = False):
    now = time.time()
    if not force and (now - market_state.get("last_rate_update", 0) < 3600):
        return

    market_state["merchant_rates"] = {
        "fish_common": round(random.uniform(0.70, 1.30), 2),
        "fish_rare": round(random.uniform(0.80, 1.40), 2),
        "fish_epic": round(random.uniform(0.85, 1.50), 2),
        "fish_legendary": round(random.uniform(0.90, 1.65), 2),
        "rod": round(random.uniform(0.60, 1.10), 2),
        "bait": round(random.uniform(0.70, 1.20), 2),
        "trash": round(random.uniform(0.80, 1.50), 2),
    }
    market_state["hourly_sold_volume"].clear()
    market_state["last_rate_update"] = now
    save_market_data()


def refund_listing_item(u_fish: dict, listing: dict):
    """Hoàn trả vật phẩm về túi khi hết hạn hoặc người bán tự hủy."""
    itype = listing["item_type"]
    payload = listing["payload"]
    if itype in ("fish", "cá"):
        u_fish.setdefault("fish_bag", []).append(payload)
    elif itype in ("rod", "cần"):
        rid = payload.get("id", f"rod_custom_{int(time.time())}")
        u_fish.setdefault("rods", {})[rid] = payload
    elif itype in ("bait", "mồi"):
        bid = payload["id"]
        u_fish.setdefault("baits", {})[bid] = u_fish.setdefault("baits", {}).get(bid, 0) + payload["count"]
    elif itype in ("chest", "rương"):
        cid = payload["id"]
        u_fish.setdefault("chests", {})[cid] = u_fish.setdefault("chests", {}).get(cid, 0) + payload["count"]
    elif itype in ("item", "vật phẩm", "key"):
        iid = payload["id"]
        u_fish.setdefault("items", {})[iid] = u_fish.setdefault("items", {}).get(iid, 0) + payload["count"]
    elif itype in ("trash", "rác"):
        tid = payload["id"]
        u_fish.setdefault("trash_bag", {})[tid] = u_fish.setdefault("trash_bag", {}).get(tid, 0) + payload["count"]


# ==============================================================================
# MODAL ĐĂNG BÁN ĐẦY ĐỦ THỜI GIAN TREO & PHÍ ƯU TIÊN
# ==============================================================================
class PostListingModal(discord.ui.Modal, title="📦 Đăng Bán Lên Chợ Người Chơi"):
    item_type = discord.ui.TextInput(
        label="Loại (fish/rod/bait/chest/item/trash)",
        placeholder="Ví dụ: fish hoặc bait hoặc rod...",
        required=True,
        max_length=15
    )
    item_id_or_index = discord.ui.TextInput(
        label="STT trong giỏ (nếu cá) / ID vật phẩm",
        placeholder="Cá: nhập số thứ tự (ví dụ: 1). Khác: ID vật phẩm (ví dụ: bait_golden)",
        required=True,
        max_length=40
    )
    quantity_input = discord.ui.TextInput(
        label="Số lượng đăng bán (Cá luôn là 1)",
        placeholder="Ví dụ: 1, 5, 10...",
        default="1",
        required=True,
        max_length=6
    )
    price_input = discord.ui.TextInput(
        label="Giá bán (Coin) [Phí sàn: 5% - 20%]",
        placeholder="Nhập giá bạn muốn bán (tối thiểu 100 coin)",
        required=True,
        max_length=15
    )
    listing_options = discord.ui.TextInput(
        label="Thời gian treo (12/24/48)h | Đẩy VIP (yes/no)",
        placeholder="Cú pháp: <giờ>|<vip> (Ví dụ: 24|yes hoặc 12|no). VIP phí 10,000c",
        default="24|no",
        required=True,
        max_length=20
    )

    def __init__(self, author: discord.Member, guild_id: int):
        super().__init__()
        self.author = author
        self.guild_id = guild_id

    async def on_submit(self, interaction: discord.Interaction):
        itype = self.item_type.value.strip().lower()
        ident = self.item_id_or_index.value.strip()

        try:
            qty = max(1, int(self.quantity_input.value.strip().replace(",", "")))
            price = int(self.price_input.value.strip().replace(",", ""))
            if price < 100:
                raise ValueError
        except ValueError:
            return await interaction.response.send_message("❌ Số lượng và giá bán phải là số nguyên dương hợp lệ (giá tối thiểu 100c)!", ephemeral=True)

        # Phân tích tùy chọn Thời gian treo và Phí ưu tiên VIP
        opt_parts = self.listing_options.value.strip().split("|")
        raw_hours = opt_parts[0].strip() if len(opt_parts) > 0 else "24"
        raw_vip = opt_parts[1].strip().lower() if len(opt_parts) > 1 else "no"

        hours = 24
        if raw_hours in ("12", "24", "48"):
            hours = int(raw_hours)

        is_priority = raw_vip in ("yes", "y", "true", "1")
        priority_fee = 10000 if is_priority else 0

        # Kiểm tra tiền để trả phí ưu tiên nếu bật VIP
        u_data = await get_user_data(self.guild_id, self.author.id)
        if is_priority and u_data.get("coins", 0) < priority_fee:
            return await interaction.response.send_message(f"❌ Bạn không đủ tiền trả phí đẩy VIP ưu tiên! Cần **`{priority_fee:,}` coin**.", ephemeral=True)

        # Tính toán tỷ lệ phí sàn (Fee: 5% - 20% tùy theo thời gian treo)
        # Treo 12h: phí sàn 5%
        # Treo 24h: phí sàn 10%
        # Treo 48h: phí sàn 15% (nếu giá trị siêu khủng > 1M coin: 20%)
        if hours == 12:
            fee_pct = 5
        elif hours == 24:
            fee_pct = 10
        else:
            fee_pct = 20 if price >= 1000000 else 15

        users = load_fishing_users()
        uid = str(self.author.id)
        u_fish = get_user_fishing_data(self.author.id)

        listed_item_payload = None
        item_display_name = ""

        # 1. Bán Cá
        if itype in ("fish", "cá"):
            bag = u_fish.get("fish_bag", [])
            if not ident.isdigit() or int(ident) < 1 or int(ident) > len(bag):
                return await interaction.response.send_message(f"❌ Số thứ tự cá không hợp lệ! Bạn có từ 1 đến {len(bag)} con cá trong giỏ.", ephemeral=True)
            fish_obj = bag.pop(int(ident) - 1)
            listed_item_payload = fish_obj
            mut_str = f" [{fish_obj['mutation']}]" if fish_obj.get("mutation") else ""
            item_display_name = f"{fish_obj['name']}{mut_str} ({fish_obj.get('weight', 0)}kg)"

        # 2. Bán Cần Câu
        elif itype in ("rod", "cần"):
            rods = u_fish.get("rods", {})
            if ident not in rods:
                return await interaction.response.send_message("❌ Bạn không sở hữu cần câu này trong kho!", ephemeral=True)
            if u_fish.get("equipped_rod") == ident:
                u_fish["equipped_rod"] = None
            rod_obj = rods.pop(ident)
            listed_item_payload = rod_obj
            ref_str = f" (+{rod_obj.get('refine', 0)})" if rod_obj.get("refine", 0) > 0 else ""
            item_display_name = f"{rod_obj['name']}{ref_str} (Bền: {rod_obj.get('durability', 0)})"

        # 3. Bán Mồi Câu
        elif itype in ("bait", "mồi"):
            baits = u_fish.get("baits", {})
            if baits.get(ident, 0) < qty:
                return await interaction.response.send_message(f"❌ Bạn không đủ mồi `{ident}` để bán (Hiện có: {baits.get(ident, 0)})!", ephemeral=True)
            baits[ident] -= qty
            if baits[ident] <= 0:
                del baits[ident]
                if u_fish.get("equipped_bait") == ident:
                    u_fish["equipped_bait"] = None
            listed_item_payload = {"id": ident, "count": qty}
            item_display_name = f"{qty}x {ident}"

        # 4. Bán Rương
        elif itype in ("chest", "rương"):
            chests = u_fish.get("chests", {})
            if chests.get(ident, 0) < qty:
                return await interaction.response.send_message("❌ Bạn không đủ số lượng rương này để bán!", ephemeral=True)
            chests[ident] -= qty
            listed_item_payload = {"id": ident, "count": qty}
            item_display_name = f"{qty}x {ident}"

        # 5. Bán Vật phẩm / Chìa khóa
        elif itype in ("item", "vật phẩm", "key"):
            items = u_fish.get("items", {})
            if items.get(ident, 0) < qty:
                return await interaction.response.send_message("❌ Bạn không đủ vật phẩm này để bán!", ephemeral=True)
            items[ident] -= qty
            listed_item_payload = {"id": ident, "count": qty}
            item_display_name = f"{qty}x {ident}"

        # 6. Bán Rác Biển
        elif itype in ("trash", "rác"):
            trash = u_fish.get("trash_bag", {})
            if trash.get(ident, 0) < qty:
                return await interaction.response.send_message("❌ Bạn không đủ rác loại này để bán!", ephemeral=True)
            trash[ident] -= qty
            listed_item_payload = {"id": ident, "count": qty}
            item_display_name = f"{qty}x {ident}"
        else:
            return await interaction.response.send_message("❌ Loại vật phẩm không hợp lệ! Hãy chọn: `fish`, `rod`, `bait`, `chest`, `item`, `trash`.", ephemeral=True)

        if is_priority:
            await update_user_coins(self.guild_id, self.author.id, -priority_fee)

        save_fishing_users(users)

        # Lưu thông tin bài đăng
        listing_id = int(time.time() * 1000)
        now = time.time()
        market_state.setdefault("listings", []).append({
            "id": listing_id,
            "seller_id": self.author.id,
            "seller_name": self.author.display_name,
            "item_type": itype,
            "item_name": item_display_name,
            "payload": listed_item_payload,
            "price": price,
            "fee_pct": fee_pct,
            "is_priority": is_priority,
            "created_at": now,
            "expires_at": now + (hours * 3600),
        })
        save_market_data()

        actual_receive = int(price * (1 - (fee_pct / 100)))
        vip_tag = "⭐ **[ƯU TIÊN VIP LÊN ĐẦU]** " if is_priority else ""

        await interaction.response.send_message(
            f"✅ **ĐÃ ĐĂNG BÁN THÀNH CÔNG!**\n"
            f"• Vật phẩm: {vip_tag}**{item_display_name}**\n"
            f"• Giá niêm yết: **`{price:,}` coin**\n"
            f"• Phí sàn khi bán: **{fee_pct}%** (Thực nhận: **`{actual_receive:,}` coin**)\n"
            f"• Thời hạn treo: **{hours} giờ** (Hết hạn tự động hoàn về giỏ đồ)!",
            ephemeral=False
        )


# ==============================================================================
# VIEW CHỢ NGƯỜI CHƠI (TỰ ĐỘNG ƯU TIÊN HÀNG VIP ĐẦU DANH SÁCH)
# ==============================================================================
class P2PMarketView(discord.ui.View):
    def __init__(self, author: discord.Member, guild_id: int):
        super().__init__(timeout=240)
        self.author = author
        self.guild_id = guild_id
        self.page = 0
        self.per_page = 5
        self.filter_type = "all"
        self._refresh_components()

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user != self.author:
            await interaction.response.send_message("❌ Đây không phải phiên xem chợ của bạn!", ephemeral=True)
            return False
        return True

    def _get_filtered_listings(self):
        listings = market_state.get("listings", [])
        filtered = []
        if self.filter_type == "my":
            filtered = [it for it in listings if it["seller_id"] == self.author.id]
        elif self.filter_type != "all":
            filtered = [it for it in listings if it["item_type"] == self.filter_type]
        else:
            filtered = list(listings)

        # SẮP XẾP: Hàng VIP có phí ưu tiên (is_priority=True) LUÔN ĐƯỢC XẾP ĐẦU DANH SÁCH
        filtered.sort(key=lambda x: (not x.get("is_priority", False), -x.get("created_at", 0)))
        return filtered

    def _refresh_components(self):
        self.clear_items()
        filtered = self._get_filtered_listings()
        total_pages = max(1, math.ceil(len(filtered) / self.per_page))

        start = self.page * self.per_page
        current_items = filtered[start:start + self.per_page]

        vi = is_vietnamese(self.guild_id)
        # Row 0: Nút mua các món từ [1] đến [5]
        for idx, it in enumerate(current_items):
            is_seller = (it["seller_id"] == self.author.id)
            if is_seller:
                lbl = f"Hủy [{idx + 1}]" if vi else f"Cancel [{idx + 1}]"
            else:
                lbl = f"Mua [{idx + 1}]" if vi else f"Buy [{idx + 1}]"
            btn = discord.ui.Button(
                label=lbl,
                style=discord.ButtonStyle.danger if is_seller else discord.ButtonStyle.success,
                row=0
            )
            btn.callback = self._create_buy_callback(it)
            self.add_item(btn)

        # Row 1: Menu lọc danh mục
        filter_options = [
            discord.SelectOption(label="Tất cả hàng hóa" if vi else "All Items", value="all", default=(self.filter_type == "all"), emoji="🌐"),
            discord.SelectOption(label="Cá đại dương" if vi else "Ocean Fish", value="fish", default=(self.filter_type == "fish"), emoji="🐟"),
            discord.SelectOption(label="Cần câu cá" if vi else "Fishing Rods", value="rod", default=(self.filter_type == "rod"), emoji="🎣"),
            discord.SelectOption(label="Mồi câu & Rương" if vi else "Bait & Chests", value="bait", default=(self.filter_type == "bait"), emoji="🪱"),
            discord.SelectOption(label="Vật phẩm & Chìa khóa" if vi else "Items & Keys", value="item", default=(self.filter_type == "item"), emoji="✨"),
            discord.SelectOption(label="Gian hàng của tôi" if vi else "My Shop", value="my", default=(self.filter_type == "my"), emoji="🏪"),
        ]
        cat_select = discord.ui.Select(placeholder="🔍 Lọc sản phẩm trên chợ..." if vi else "🔍 Filter market items...", options=filter_options, row=1)
        cat_select.callback = self._filter_callback
        self.add_item(cat_select)

        # Row 2: Điều hướng trang & Đăng bán
        prev_btn = discord.ui.Button(label="◀ Trước" if vi else "◀ Prev", style=discord.ButtonStyle.secondary, disabled=(self.page == 0), row=2)
        prev_btn.callback = self._prev
        self.add_item(prev_btn)

        page_ind = discord.ui.Button(label=f"{'Trang' if vi else 'Page'} {self.page + 1}/{total_pages}", style=discord.ButtonStyle.secondary, disabled=True, row=2)
        self.add_item(page_ind)

        next_btn = discord.ui.Button(label="Sau ▶" if vi else "Next ▶", style=discord.ButtonStyle.secondary, disabled=(self.page >= total_pages - 1), row=2)
        next_btn.callback = self._next
        self.add_item(next_btn)

        post_btn = discord.ui.Button(label="Đăng Bán Đồ" if vi else "List Item", style=discord.ButtonStyle.primary, emoji="📦", row=2)
        post_btn.callback = self._open_post_modal
        self.add_item(post_btn)

        # Row 3: Chuyển sang Lái Buôn Biển Sâu
        merchant_btn = discord.ui.Button(label="Ghé Tiệm Lái Buôn Biển Sâu (Bán Nhanh)", style=discord.ButtonStyle.secondary, emoji="🚢", row=3)
        merchant_btn.callback = self._goto_merchant
        self.add_item(merchant_btn)

    def build_embed(self, user_coins: int) -> discord.Embed:
        filtered = self._get_filtered_listings()
        total_pages = max(1, math.ceil(len(filtered) / self.per_page))
        start = self.page * self.per_page
        current_items = filtered[start:start + self.per_page]

        embed = discord.Embed(
            title="🏪 SÀN GIAO THƯƠNG ĐẠI DƯƠNG (P2P MARKETPLACE)",
            description=(
                f"💰 Số dư: **`{user_coins:,}` coin** | Mặt hàng đang bán: **`{len(filtered)}` món**\n"
                f"• Phí sàn: **5% - 20%** | Hạn treo: **12h / 24h / 48h** (Hết hạn hoàn về giỏ)\n"
                f"• Bấm nút số `[1]` đến `[5]` để mua hàng. Nếu là hàng của bạn, nút tự chuyển thành Hủy!"
            ),
            color=discord.Color.gold()
        )

        if current_items:
            for idx, it in enumerate(current_items, start=1):
                vip_badge = "⭐ **[VIP]** " if it.get("is_priority") else ""
                is_mine = " `(CỦA BẠN)`" if it["seller_id"] == self.author.id else ""
                rem_time = max(0, int(it.get("expires_at", 0) - time.time()))
                hours_rem = rem_time // 3600
                mins_rem = (rem_time % 3600) // 60

                embed.add_field(
                    name=f"**[{idx}] {vip_badge}{it['item_name']}** — `{it['price']:,}` coin",
                    value=(
                        f"• Người bán: **{it['seller_name']}**{is_mine}\n"
                        f"• Phí sàn: `{it.get('fee_pct', 10)}%` | Còn hạn: `{hours_rem}h {mins_rem}m`"
                    ),
                    inline=False
                )
        else:
            embed.add_field(name="📭 Chợ Đang Trống", value="*Chưa có ai đăng bán vật phẩm thuộc danh mục này.*", inline=False)

        embed.set_footer(text=f"Trang {self.page + 1}/{total_pages} • Các món hàng VIP luôn được đẩy lên đầu danh sách!")
        return embed

    def _create_buy_callback(self, listing: dict):
        async def callback(interaction: discord.Interaction):
            listings = market_state.setdefault("listings", [])
            if listing not in listings:
                return await interaction.response.send_message("❌ Vật phẩm này đã được người khác mua hoặc người bán đã gỡ bỏ!", ephemeral=True)

            users = load_fishing_users()
            buyer_id = str(self.author.id)
            price = listing["price"]

            # Người bán tự hủy đơn hàng
            if listing["seller_id"] == self.author.id:
                listings.remove(listing)
                save_market_data()

                u_fish = get_user_fishing_data(self.author.id)
                refund_listing_item(u_fish, listing)
                save_fishing_users(users)

                self._refresh_components()
                u_data = await get_user_data(self.guild_id, self.author.id)
                await interaction.response.edit_message(embed=self.build_embed(u_data.get("coins", 0)), view=self)
                return await interaction.followup.send(f"🗑️ Đã hủy bán và hoàn trả **{listing['item_name']}** vào túi đồ!", ephemeral=True)

            # Người mua mua hàng
            buyer_data = await get_user_data(self.guild_id, self.author.id)
            if buyer_data.get("coins", 0) < price:
                return await interaction.response.send_message(f"❌ Bạn không đủ tiền! Cần **`{price:,}` coin**.", ephemeral=True)

            # Trừ phí sàn (5% - 20%) và chuyển tiền cho người bán
            fee_pct = listing.get("fee_pct", 10)
            seller_receive = int(price * (1 - (fee_pct / 100)))

            await update_user_coins(self.guild_id, self.author.id, -price)
            await update_user_coins(self.guild_id, listing["seller_id"], seller_receive)

            listings.remove(listing)
            save_market_data()

            # Chuyển đồ sang người mua
            buyer_fish = get_user_fishing_data(self.author.id)
            refund_listing_item(buyer_fish, listing)
            save_fishing_users(users)

            self._refresh_components()
            new_data = await get_user_data(self.guild_id, self.author.id)
            await interaction.response.edit_message(embed=self.build_embed(new_data.get("coins", 0)), view=self)
            await interaction.followup.send(
                f"🎉 **GIAO DỊCH THÀNH CÔNG!**\n"
                f"Bạn đã mua **{listing['item_name']}** với giá **`{price:,}` coin**!\n"
                f"(Người bán nhận được: **`{seller_receive:,}` coin** sau khi trừ {fee_pct}% phí sàn).",
                ephemeral=False
            )

        return callback

    async def _filter_callback(self, interaction: discord.Interaction):
        self.filter_type = interaction.data["values"][0]
        self.page = 0
        self._refresh_components()
        u_data = await get_user_data(self.guild_id, self.author.id)
        await interaction.response.edit_message(embed=self.build_embed(u_data.get("coins", 0)), view=self)

    async def _prev(self, interaction: discord.Interaction):
        if self.page > 0:
            self.page -= 1
            self._refresh_components()
            u_data = await get_user_data(self.guild_id, self.author.id)
            await interaction.response.edit_message(embed=self.build_embed(u_data.get("coins", 0)), view=self)

    async def _next(self, interaction: discord.Interaction):
        filtered = self._get_filtered_listings()
        total_pages = max(1, math.ceil(len(filtered) / self.per_page))
        if self.page < total_pages - 1:
            self.page += 1
            self._refresh_components()
            u_data = await get_user_data(self.guild_id, self.author.id)
            await interaction.response.edit_message(embed=self.build_embed(u_data.get("coins", 0)), view=self)

    async def _open_post_modal(self, interaction: discord.Interaction):
        await interaction.response.send_modal(PostListingModal(self.author, self.guild_id))

    async def _goto_merchant(self, interaction: discord.Interaction):
        merchant_view = DeepSeaMerchantView(self.author, self.guild_id)
        u_data = await get_user_data(self.guild_id, self.author.id)
        await interaction.response.edit_message(embed=merchant_view.build_embed(u_data.get("coins", 0)), view=merchant_view)


# ==============================================================================
# VIEW LÁI BUÔN BIỂN SÂU
# ==============================================================================
class DeepSeaMerchantView(discord.ui.View):
    def __init__(self, author: discord.Member, guild_id: int):
        super().__init__(timeout=180)
        self.author = author
        self.guild_id = guild_id
        vi = is_vietnamese(guild_id)
        self.sell_common.label = "Bán Cá Thường" if vi else "Sell Common Fish"
        self.sell_rare.label = "Bán Cá Hiếm" if vi else "Sell Rare Fish"
        self.sell_all.label = "Bán Toàn Bộ Cá" if vi else "Sell All Fish"
        self.back_to_market.label = "Quay Lại Chợ P2P" if vi else "Back to P2P Market" 
        update_merchant_rates(force=False)

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user != self.author:
            await interaction.response.send_message("❌ Đây không phải phiên giao dịch của bạn!", ephemeral=True)
            return False
        return True

    def build_embed(self, user_coins: int) -> discord.Embed:
        rates = market_state.get("merchant_rates", {})
        rem_mins = 60 - int((time.time() - market_state.get("last_rate_update", 0)) // 60)

        users = load_fishing_users()
        u_fish = users.get(str(self.author.id), {})
        bag = u_fish.get("fish_bag", [])

        embed = discord.Embed(
            title="🚢 TIỆM THU MUA LÁI BUÔN BIỂN SÂU",
            description=(
                f"💰 Số dư của bạn: **`{user_coins:,}` coin**\n"
                f"Lái buôn chấp nhận mua đứt cá ngay lập tức với **giá biến động theo phiên**.\n"
                f"⚠️ *Lưu ý: Bán ồ ạt một lượng cá quá lớn trong 1 giờ sẽ làm bão hòa thị trường và bị trừ 10% - 25% giá!*"
            ),
            color=discord.Color.dark_teal()
        )
        embed.add_field(
            name="📊 Tỉ Giá Thu Mua Hiện Tại (Đổi sau {} phút)".format(max(1, rem_mins)),
            value=(
                f"• Cá Thường (Common): `x{rates.get('fish_common', 1.0)}`\n"
                f"• Cá Hiếm (Rare): `x{rates.get('fish_rare', 1.0)}`\n"
                f"• Cá Sử Thi (Epic): `x{rates.get('fish_epic', 1.0)}`\n"
                f"• Cá Huyền Thoại (Legendary): `x{rates.get('fish_legendary', 1.0)}`"
            ),
            inline=False
        )
        embed.add_field(
            name="🐟 Giỏ Cá Của Bạn",
            value=f"Hiện có **{len(bag)} con cá** trong giỏ.",
            inline=False
        )
        embed.set_footer(text="Lái buôn biển sâu • Dòng tiền mặt tức thì")
        return embed

    def _calculate_payout(self, fish_list_to_sell: list) -> int:
        rates = market_state.get("merchant_rates", {})
        vols = market_state.setdefault("hourly_sold_volume", {})
        total = 0

        for f in fish_list_to_sell:
            r_key = f"fish_{f.get('rarity', 'common')}"
            rate = rates.get(r_key, 1.0)
            fname = f["name"]

            past_vol = vols.get(fname, 0)
            saturation_penalty = max(0.75, 1.0 - (past_vol * 0.015))

            item_price = int(f.get("price", 100) * rate * saturation_penalty)
            total += max(10, item_price)
            vols[fname] = past_vol + 1

        return total

    @discord.ui.button(label="Bán Cá Thường", style=discord.ButtonStyle.secondary, emoji="⚪", row=0)
    async def sell_common(self, interaction: discord.Interaction, button: discord.ui.Button):
        users = load_fishing_users()
        u_fish = users.setdefault(str(self.author.id), {})
        bag = u_fish.get("fish_bag", [])
        to_sell = [f for f in bag if f.get("rarity") == "common" and not f.get("mutation")]

        if not to_sell:
            return await interaction.response.send_message("⚠️ Bạn không có cá Common không đột biến để bán!", ephemeral=True)

        payout = self._calculate_payout(to_sell)
        u_fish["fish_bag"] = [f for f in bag if f not in to_sell]
        save_fishing_users(users)
        save_market_data()

        await update_user_coins(self.guild_id, self.author.id, payout)
        u_data = await get_user_data(self.guild_id, self.author.id)
        await interaction.response.edit_message(embed=self.build_embed(u_data.get("coins", 0)), view=self)
        await interaction.followup.send(f"🚢 Lái buôn đã thu mua **{len(to_sell)}** con cá Common và thanh toán **`+{payout:,}` coin**!", ephemeral=True)

    @discord.ui.button(label="Bán Cá Hiếm", style=discord.ButtonStyle.primary, emoji="🔵", row=0)
    async def sell_rare(self, interaction: discord.Interaction, button: discord.ui.Button):
        users = load_fishing_users()
        u_fish = get_user_fishing_data(self.author.id)
        bag = u_fish.get("fish_bag", [])
        to_sell = [f for f in bag if f.get("rarity") == "rare" and not f.get("mutation")]

        if not to_sell:
            return await interaction.response.send_message("⚠️ Bạn không có cá Rare để bán!", ephemeral=True)

        payout = self._calculate_payout(to_sell)
        u_fish["fish_bag"] = [f for f in bag if f not in to_sell]
        save_fishing_users(users)
        save_market_data()

        await update_user_coins(self.guild_id, self.author.id, payout)
        u_data = await get_user_data(self.guild_id, self.author.id)
        await interaction.response.edit_message(embed=self.build_embed(u_data.get("coins", 0)), view=self)
        await interaction.followup.send(f"🚢 Lái buôn đã thu mua **{len(to_sell)}** con cá Rare và thanh toán **`+{payout:,}` coin**!", ephemeral=True)

    @discord.ui.button(label="Bán Toàn Bộ Cá", style=discord.ButtonStyle.danger, emoji="💰", row=0)
    async def sell_all_fish(self, interaction: discord.Interaction, button: discord.ui.Button):
        users = load_fishing_users()
        u_fish = get_user_fishing_data(self.author.id)
        bag = u_fish.get("fish_bag", [])
        to_sell = [f for f in bag if not f.get("mutation")]
        kept = [f for f in bag if f.get("mutation")]

        if not to_sell:
            return await interaction.response.send_message("⚠️ Không có cá thường nào trong giỏ để bán!", ephemeral=True)

        payout = self._calculate_payout(to_sell)
        u_fish["fish_bag"] = kept
        save_fishing_users(users)
        save_market_data()

        await update_user_coins(self.guild_id, self.author.id, payout)
        u_data = await get_user_data(self.guild_id, self.author.id)
        await interaction.response.edit_message(embed=self.build_embed(u_data.get("coins", 0)), view=self)
        await interaction.followup.send(f"🚢 Lái buôn đã vét sạch **{len(to_sell)}** con cá và trả ngay **`+{payout:,}` coin**! (Giữ lại cá đột biến)", ephemeral=True)

    @discord.ui.button(label="Quay Lại Chợ P2P", style=discord.ButtonStyle.secondary, emoji="🏪", row=1)
    async def back_to_p2p(self, interaction: discord.Interaction, button: discord.ui.Button):
        p2p_view = P2PMarketView(self.author, self.guild_id)
        u_data = await get_user_data(self.guild_id, self.author.id)
        await interaction.response.edit_message(embed=p2p_view.build_embed(u_data.get("coins", 0)), view=p2p_view)


# ==============================================================================
# LỚP COG CHÍNH (MARKET COG)
# ==============================================================================
class MarketCog(commands.Cog, name="Market"):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.market_cleanup_task.start()

    def cog_unload(self):
        self.market_cleanup_task.cancel()

    # TASK TỰ ĐỘNG QUÉT HOÀN TRẢ ĐƠN HÀNG HẾT HẠN (MỖI 5 PHÚT)
    @tasks.loop(minutes=5)
    async def market_cleanup_task(self):
        now = time.time()
        listings = market_state.get("listings", [])
        expired_items = [it for it in listings if it.get("expires_at", 0) > 0 and now >= it["expires_at"]]

        if expired_items:
            users = load_fishing_users()
            for it in expired_items:
                listings.remove(it)
                seller_id = int(it["seller_id"])
                u_fish = get_user_fishing_data(seller_id)
                refund_listing_item(u_fish, it)

            save_market_data()
            save_fishing_users(users)

    @market_cleanup_task.before_loop
    async def before_cleanup(self):
        await self.bot.wait_until_ready()

    @commands.hybrid_command(
        name="market",
        aliases=["cho", "p2p", "chodaiduong"],
        description="🏪 Sàn giao dịch chợ người chơi (P2P), phí sàn 5-20%, đẩy bài VIP & tiệm Lái Buôn."
    )
    @commands.guild_only()
    async def market_cmd(self, ctx: commands.Context):
        view = P2PMarketView(ctx.author, ctx.guild.id)
        u_data = await get_user_data(ctx.guild.id, ctx.author.id)
        await ctx.send(embed=view.build_embed(u_data.get("coins", 0)), view=view)

    @commands.command(name="bancho")
    async def bancho_shortcut(self, ctx: commands.Context):
        modal = PostListingModal(ctx.author, ctx.guild.id)
        if ctx.interaction:
            await ctx.interaction.response.send_modal(modal)
        else:
            await ctx.send("👉 Hãy dùng lệnh Slash `/market` và bấm nút **[📦 Đăng Bán Đồ]** để mở form đăng bán tiện lợi nhất!")


async def setup(bot: commands.Bot):
    await bot.add_cog(MarketCog(bot))
