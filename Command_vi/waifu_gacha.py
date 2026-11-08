import discord
from discord.ext import commands
from discord import app_commands
import time
import math
import asyncio
from typing import Optional, List, Dict, Any

from Checks_vi.i18n import t, get_guild_language
from data.database import update_user_coins, get_user_currency, deduct_user_currency
from data.waifu_db import (
    init_waifu_db, get_or_create_profile, consume_roll, consume_claim,
    add_bonus_rolls, add_bonus_claims, get_random_character, get_character_by_id,
    search_characters, mint_card, get_user_cards, get_user_card, burn_card,
    get_mergeable_characters, merge_star, list_card_for_sale, cancel_market_listing,
    get_market_listings, buy_market_listing, add_wishlist, remove_wishlist,
    get_user_wishlist, get_wishlist_users, get_top_collectors,
    RARITY_CONFIG, ROLL_REGEN_SECONDS, CLAIM_REGEN_SECONDS
)

def make_fav_bar(favourites: int, rarity: str) -> str:
    """
    Renders 12-block progress bar matching Image 2:
    e.g. ■■■■■■■□□□□□
    """
    max_fav = RARITY_CONFIG.get(rarity, {}).get("max_favs", 2000)
    ratio = min(1.0, max(0.05, favourites / max(1, max_fav)))
    boosted_ratio = math.sqrt(ratio)
    filled = min(12, max(1, round(boosted_ratio * 12)))
    return "■" * filled + "□" * (12 - filled)


def get_rarity_display(rarity: str, lang: str = "vi") -> tuple[str, str, int]:
    cfg = RARITY_CONFIG.get(rarity, RARITY_CONFIG["common"])
    name_key = f"name_{lang}" if f"name_{lang}" in cfg else "name_vi"
    name = cfg.get(name_key, cfg["name_vi"])
    return name, cfg["indicator"], cfg["color"]


class RollClaimButton(discord.ui.Button):
    def __init__(self, cog, character: dict, roll_time: float, roller_id: int, lang: str):
        super().__init__(
            label=t(lang, "GACHA_BTN_CLAIM", default="Claim"),
            style=discord.ButtonStyle.success,
            emoji="💖"
        )
        self.cog = cog
        self.character = character
        self.roll_time = roll_time
        self.roller_id = roller_id
        self.lang = lang
        self.is_claimed = False
        self.claimed_by = None

    async def callback(self, interaction: discord.Interaction):
        user = interaction.user
        lang = get_guild_language(interaction.guild)

        if self.is_claimed:
            return await interaction.response.send_message(
                t(lang, "GACHA_CLAIM_ALREADY", default="❌ Thẻ này đã được ai đó claim rồi!"),
                ephemeral=True
            )

        # Check 60-second expiration
        if time.time() - self.roll_time > 60:
            return await interaction.response.send_message(
                t(lang, "GACHA_CLAIM_EXPIRED", default="⌛ Thẻ đã hết hạn 60 giây, không thể claim nữa!"),
                ephemeral=True
            )

        # Attempt to consume 1 claim token
        success, profile = await consume_claim(user.id)
        if not success:
            return await interaction.response.send_message(
                t(lang, "GACHA_CLAIM_NO_CLAIMS", default="❌ Bạn đã hết lượt claim! Lượt claim hồi 1 lượt mỗi 2 tiếng, hoặc bạn có thể mua thêm trong **Mua claim**."),
                ephemeral=True
            )

        # Mark as claimed
        self.is_claimed = True
        self.claimed_by = user.id
        self.disabled = True
        self.label = t(lang, "GACHA_BTN_CLAIMED", default="Đã claim")
        self.style = discord.ButtonStyle.secondary

        # Mint card to database
        card = await mint_card(user.id, self.character["id"])

        # Update button view on original message
        try:
            await interaction.message.edit(view=self.view)
        except Exception:
            pass

        # Send celebration message in channel
        claim_msg = t(
            lang,
            "GACHA_CLAIM_SUCCESS",
            default="💖 **{user}** đã claim thành công **{character}**! (Mã: `{code}` ┆ Print `#{print}`)",
            user=user.display_name,
            character=self.character["name"],
            code=card["code"],
            print=card["print_number"]
        )
        await interaction.response.send_message(claim_msg)


class RollCardView(discord.ui.View):
    def __init__(self, cog, character: dict, roll_time: float, roller_id: int, lang: str):
        super().__init__(timeout=65.0)
        self.lang = lang
        self.claim_btn = RollClaimButton(cog, character, roll_time, roller_id, lang)
        self.add_item(self.claim_btn)

    async def on_timeout(self):
        if not self.claim_btn.is_claimed:
            self.claim_btn.disabled = True
            self.claim_btn.label = t(self.lang, "GACHA_BTN_EXPIRED", default="Hết hạn")
            self.claim_btn.style = discord.ButtonStyle.secondary


class CollectionPaginationView(discord.ui.View):
    def __init__(self, user: discord.User | discord.Member, cards: List[dict], lang: str):
        super().__init__(timeout=180.0)
        self.user = user
        self.cards = cards
        self.lang = lang
        self.page = 1
        self.per_page = 10
        self.total_pages = max(1, math.ceil(len(cards) / self.per_page))

        self.prev_button = discord.ui.Button(
            label=t(lang, "GACHA_BTN_PREV", default="Trang trước"),
            style=discord.ButtonStyle.secondary,
            disabled=True
        )
        self.prev_button.callback = self.on_prev

        self.next_button = discord.ui.Button(
            label=t(lang, "GACHA_BTN_NEXT", default="Trang sau"),
            style=discord.ButtonStyle.secondary,
            disabled=(self.total_pages <= 1)
        )
        self.next_button.callback = self.on_next

        self.add_item(self.prev_button)
        self.add_item(self.next_button)

    def generate_embed(self) -> discord.Embed:
        start_idx = (self.page - 1) * self.per_page
        end_idx = start_idx + self.per_page
        page_cards = self.cards[start_idx:end_idx]

        # Calculate rarity stats
        rarity_counts = {"legendary": 0, "epic": 0, "rare": 0, "common": 0}
        total_points = sum(c["points"] for c in self.cards)
        for c in self.cards:
            r = c.get("rarity", "common")
            rarity_counts[r] = rarity_counts.get(r, 0) + 1

        embed = discord.Embed(
            title=t(self.lang, "GACHA_COLLECTION_TITLE", default=f"Bộ sưu tập của {self.user.display_name}", name=self.user.display_name),
            color=discord.Color.from_rgb(43, 45, 49)
        )

        # Set thumbnail to top waifu image
        if self.cards and self.cards[0].get("image_url"):
            embed.set_thumbnail(url=self.cards[0]["image_url"])

        # Summary line
        if rarity_counts["legendary"] > 0:
            summary = t(
                self.lang,
                "GACHA_COLLECTION_SUMMARY_LEG",
                default=f"Huyền thoại: {rarity_counts['legendary']} ┆ Sử thi: {rarity_counts['epic']} ┆ Hiếm: {rarity_counts['rare']} ┆ Thường: {rarity_counts['common']}",
                legendary=rarity_counts["legendary"],
                epic=rarity_counts["epic"],
                rare=rarity_counts["rare"],
                common=rarity_counts["common"]
            )
        else:
            summary = t(
                self.lang,
                "GACHA_COLLECTION_SUMMARY",
                default=f"Sử thi: {rarity_counts['epic']} ┆ Hiếm: {rarity_counts['rare']} ┆ Thường: {rarity_counts['common']}",
                epic=rarity_counts["epic"],
                rare=rarity_counts["rare"],
                common=rarity_counts["common"]
            )

        lines = [summary, ""]
        for c in page_cards:
            name = c.get("name", "Unknown")
            stars = c.get("stars", 1)
            points = c.get("points", 0)
            print_num = c.get("print_number", 1)
            code = c.get("code", "000000")
            lines.append(f"**{name}** {stars}⭐ ┆ {points:,} ┆ #{print_num} ┆ `{code}`")

        embed.description = "\n".join(lines)

        footer_text = t(
            self.lang,
            "GACHA_COLLECTION_FOOTER",
            default=f"Trang {self.page}/{self.total_pages} ┆ {len(self.cards)} nhân vật ┆ tổng giá trị 💖{total_points:,}",
            page=self.page,
            total_pages=self.total_pages,
            total_cards=len(self.cards),
            total_points=f"{total_points:,}"
        )
        embed.set_footer(text=footer_text)
        return embed

    async def on_prev(self, interaction: discord.Interaction):
        if interaction.user.id != self.user.id:
            return await interaction.response.send_message(t(self.lang, "COMMON_ERROR_NO_PERM", default="❌ Bạn không thể thao tác nút/menu này."), ephemeral=True)
        if self.page > 1:
            self.page -= 1
            self.prev_button.disabled = (self.page == 1)
            self.next_button.disabled = (self.page == self.total_pages)
            await interaction.response.edit_message(embed=self.generate_embed(), view=self)

    async def on_next(self, interaction: discord.Interaction):
        if interaction.user.id != self.user.id:
            return await interaction.response.send_message(t(self.lang, "COMMON_ERROR_NO_PERM", default="❌ Bạn không thể thao tác nút/menu này."), ephemeral=True)
        if self.page < self.total_pages:
            self.page += 1
            self.prev_button.disabled = (self.page == 1)
            self.next_button.disabled = (self.page == self.total_pages)
            await interaction.response.edit_message(embed=self.generate_embed(), view=self)


class MergeSelect(discord.ui.Select):
    def __init__(self, user: discord.User | discord.Member, eligible: List[dict], lang: str):
        self.user_obj = user
        self.eligible = eligible
        self.lang = lang

        options = []
        for item in eligible[:25]:
            cid = str(item["character_id"])
            cname = item["name"]
            count = item["card_count"]
            cur_star = item["max_stars"]
            label = t(lang, "GACHA_CARD_COUNT_LABEL", default=f"{cname} ({count} thẻ)", name=cname, count=count)
            desc = t(lang, "GACHA_MERGE_OPTION_DESC", default=f"Nâng lên {cur_star + 1}⭐ (x2 💖) | Tiêu thụ 2 thẻ", stars=cur_star + 1)
            options.append(discord.SelectOption(label=label[:100], value=cid, description=desc[:100], emoji="⭐"))

        super().__init__(
            placeholder=t(lang, "GACHA_MERGE_SELECT_PLACEHOLDER", default="Chọn nhân vật bạn muốn nâng sao..."),
            min_values=1,
            max_values=1,
            options=options
        )

    async def callback(self, interaction: discord.Interaction):
        if interaction.user.id != self.user_obj.id:
            return await interaction.response.send_message(t(self.lang, "COMMON_ERROR_NO_PERM", default="❌ Bạn không thể thao tác nút/menu này."), ephemeral=True)

        char_id = int(self.values[0])
        success, status, card = await merge_star(interaction.user.id, char_id)

        if not success:
            err = t(self.lang, "GACHA_MERGE_NOT_ENOUGH", default="❌ Không đủ 3 thẻ cùng loại hoặc thẻ đang treo trên chợ!")
            return await interaction.response.send_message(err, ephemeral=True)

        char_name = card.get("name", "Unknown")
        stars = card.get("stars", 1)
        base_favs = card.get("base_favourites", 0)
        old_points = base_favs * (2 ** max(0, stars - 2))
        new_points = card.get("points", 0)

        msg = t(
            self.lang,
            "GACHA_MERGE_SUCCESS",
            default=f"🌟 **Nâng Sao Thành Công!**\n**{char_name}** đã được nâng lên **{stars}⭐**!\n💖 Điểm yêu thích: **{old_points:,} ➔ {new_points:,}** (x2)\nĐã tiêu hao 2 thẻ trùng lặp.",
            character=char_name,
            stars=stars,
            old_points=old_points,
            new_points=new_points
        )

        embed = discord.Embed(
            title=t(self.lang, "GACHA_MERGE_TITLE", default="🌟 Gộp Sao Nhân Vật (Star Merge)"),
            description=msg,
            color=discord.Color.gold()
        )
        if card.get("image_url"):
            embed.set_thumbnail(url=card["image_url"])
        embed.set_footer(text=t(self.lang, "GACHA_MERGE_FOOTER", default=f"Mã thẻ giữ lại: {card['code']} ┆ Print #{card['print_number']}", code=card['code'], print=card['print_number']))

        await interaction.response.edit_message(embed=embed, view=None)


class MergeView(discord.ui.View):
    def __init__(self, user: discord.User | discord.Member, eligible: List[dict], lang: str):
        super().__init__(timeout=120.0)
        self.add_item(MergeSelect(user, eligible, lang))


class BuyRollsView(discord.ui.View):
    def __init__(self, user: discord.User | discord.Member, guild_id: int, lang: str):
        super().__init__(timeout=120.0)
        self.user_obj = user
        self.guild_id = guild_id
        self.lang = lang

        packs = [
            (5, 250, "5 Roll — 250🪙"),
            (15, 700, "15 Roll — 700🪙 (-50🪙)"),
            (50, 2000, "50 Roll — 2,000🪙 (-500🪙)")
        ]
        for amount, cost, label in packs:
            btn = discord.ui.Button(label=label, style=discord.ButtonStyle.success, emoji="🎲")
            btn.callback = self.make_callback(amount, cost)
            self.add_item(btn)

    def make_callback(self, amount: int, cost: int):
        async def callback(interaction: discord.Interaction):
            if interaction.user.id != self.user_obj.id:
                return await interaction.response.send_message(t(self.lang, "COMMON_ERROR_NO_PERM", default="❌ Bạn không thể thao tác nút này."), ephemeral=True)

            user_coins = await get_user_currency(self.guild_id, interaction.user.id, "coins")
            if user_coins < cost:
                err = t(
                    self.lang,
                    "GACHA_BUY_NOT_ENOUGH_COINS",
                    default=f"❌ Bạn không có đủ coin! Cần: **{cost}🪙**, hiện có: **{user_coins}🪙**.",
                    cost=cost,
                    current=user_coins
                )
                return await interaction.response.send_message(err, ephemeral=True)

            # Deduct coins
            await deduct_user_currency(self.guild_id, interaction.user.id, "coins", cost)
            # Add bonus rolls
            total = await add_bonus_rolls(interaction.user.id, amount)

            succ = t(
                self.lang,
                "GACHA_BUY_ROLL_SUCCESS",
                default=f"✅ Đã mua thành công **{amount} lượt roll** với giá **{cost}🪙**! Hiện có: **{total} lượt roll**.",
                amount=amount,
                cost=cost,
                total=total
            )
            await interaction.response.edit_message(content=succ, embed=None, view=None)

        return callback


class BuyClaimsView(discord.ui.View):
    def __init__(self, user: discord.User | discord.Member, guild_id: int, lang: str):
        super().__init__(timeout=120.0)
        self.user_obj = user
        self.guild_id = guild_id
        self.lang = lang

        packs = [
            (1, 1500, "1 Claim — 1,500🪙"),
            (3, 4000, "3 Claim — 4,000🪙 (-500🪙)")
        ]
        for amount, cost, label in packs:
            btn = discord.ui.Button(label=label, style=discord.ButtonStyle.primary, emoji="💖")
            btn.callback = self.make_callback(amount, cost)
            self.add_item(btn)

    def make_callback(self, amount: int, cost: int):
        async def callback(interaction: discord.Interaction):
            if interaction.user.id != self.user_obj.id:
                return await interaction.response.send_message(t(self.lang, "COMMON_ERROR_NO_PERM", default="❌ Bạn không thể thao tác nút này."), ephemeral=True)

            user_coins = await get_user_currency(self.guild_id, interaction.user.id, "coins")
            if user_coins < cost:
                err = t(
                    self.lang,
                    "GACHA_BUY_NOT_ENOUGH_COINS",
                    default=f"❌ Bạn không có đủ coin! Cần: **{cost}🪙**, hiện có: **{user_coins}🪙**.",
                    cost=cost,
                    current=user_coins
                )
                return await interaction.response.send_message(err, ephemeral=True)

            # Deduct coins
            await deduct_user_currency(self.guild_id, interaction.user.id, "coins", cost)
            # Add bonus claims
            total = await add_bonus_claims(interaction.user.id, amount)

            succ = t(
                self.lang,
                "GACHA_BUY_CLAIM_SUCCESS",
                default=f"✅ Đã mua thành công **{amount} lượt claim** với giá **{cost}🪙**! Hiện có: **{total} lượt claim**.",
                amount=amount,
                cost=cost,
                total=total
            )
            await interaction.response.edit_message(content=succ, embed=None, view=None)

        return callback


class MarketBuySelect(discord.ui.Select):
    def __init__(self, user: discord.User | discord.Member, listings: List[dict], guild_id: int, lang: str):
        self.user_obj = user
        self.guild_id = guild_id
        self.lang = lang

        options = []
        for l in listings[:25]:
            lid = str(l["listing_id"])
            cname = l["name"]
            price = l["price_coins"]
            stars = l["stars"]
            item_desc = t(lang, "GACHA_MARKET_ITEM_DESC", default=f"Print #{l['print_number']} | Mã: {l['card_code']}", print=l['print_number'], code=l['card_code'])
            options.append(discord.SelectOption(
                label=f"{cname} {stars}⭐ — {price:,}🪙"[:100],
                value=lid,
                description=item_desc[:100],
                emoji="🛒"
            ))

        super().__init__(
            placeholder=t(lang, "GACHA_MARKET_SELECT_PLACEHOLDER", default="Chọn thẻ bạn muốn mua từ chợ..."),
            min_values=1,
            max_values=1,
            options=options
        )

    async def callback(self, interaction: discord.Interaction):
        if interaction.user.id != self.user_obj.id:
            return await interaction.response.send_message(t(self.lang, "COMMON_ERROR_NO_PERM", default="❌ Bạn không thể thao tác thay người khác."), ephemeral=True)

        lid = int(self.values[0])
        # Use buy_market_listing
        success, status, result = await buy_market_listing(lid, interaction.user.id)
        if not success:
            if status == "NOT_FOUND":
                return await interaction.response.send_message(t(self.lang, "GACHA_MARKET_ERR_NOT_FOUND", default="❌ Thẻ này đã bị xóa hoặc người khác đã mua rồi!"), ephemeral=True)
            elif status == "CANNOT_BUY_OWN":
                return await interaction.response.send_message(t(self.lang, "GACHA_MARKET_ERR_OWN", default="❌ Bạn không thể tự mua thẻ của chính mình!"), ephemeral=True)
            return await interaction.response.send_message(t(self.lang, "GACHA_MARKET_ERR_FAIL", default="❌ Giao dịch thất bại."), ephemeral=True)

        price = result["price"]
        seller_id = result["seller_id"]
        card = result["card"]

        # Deduct coins from buyer
        user_coins = await get_user_currency(self.guild_id, interaction.user.id, "coins")
        if user_coins < price:
            # Revert listing
            await list_card_for_sale(card["code"], seller_id, price)
            return await interaction.response.send_message(t(self.lang, "GACHA_MARKET_ERR_NO_COINS", default=f"❌ Bạn không đủ coin! Cần **{price:,}🪙**.", price=f"{price:,}"), ephemeral=True)

        await deduct_user_currency(self.guild_id, interaction.user.id, "coins", price)
        # Give coins to seller
        await update_user_coins(self.guild_id, seller_id, price)

        succ = t(self.lang, "GACHA_MARKET_BUY_SUCCESS", default=f"🎉 Chúc mừng! Bạn đã mua thành công **{card['name']} {card['stars']}⭐** với giá **{price:,}🪙**!", character=card['name'], stars=card['stars'], price=f"{price:,}")
        await interaction.response.edit_message(content=succ, embed=None, view=None)


class MarketPaginationView(discord.ui.View):
    def __init__(self, user: discord.User | discord.Member, listings: List[dict], total: int, guild_id: int, lang: str):
        super().__init__(timeout=120.0)
        self.user = user
        self.listings = listings
        self.total = total
        self.guild_id = guild_id
        self.lang = lang

        if listings:
            self.add_item(MarketBuySelect(user, listings, guild_id, lang))


class GachaMenuView(discord.ui.View):
    """
    Main interactive view matching Image 1:
    Row 0: [Roll] (Green), [Bộ sưu tập] (Grey), [Chợ] (Grey)
    Row 1: [Gộp sao] (Blurple), [Wishlist] (Grey), [BXH] (Grey)
    Row 2: [Mua roll] (Grey), [Mua claim] (Grey), [Trợ giúp] (Grey)
    """
    def __init__(self, cog, lang: str):
        super().__init__(timeout=None)
        self.cog = cog
        self.lang = lang

        # Row 0
        btn_roll = discord.ui.Button(
            label=t(lang, "GACHA_BTN_ROLL", default="Roll"),
            style=discord.ButtonStyle.success,
            row=0
        )
        btn_roll.callback = self.on_roll

        btn_collection = discord.ui.Button(
            label=t(lang, "GACHA_BTN_COLLECTION", default="Bộ sưu tập"),
            style=discord.ButtonStyle.secondary,
            row=0
        )
        btn_collection.callback = self.on_collection

        btn_market = discord.ui.Button(
            label=t(lang, "GACHA_BTN_MARKET", default="Chợ"),
            style=discord.ButtonStyle.secondary,
            row=0
        )
        btn_market.callback = self.on_market

        # Row 1
        btn_merge = discord.ui.Button(
            label=t(lang, "GACHA_BTN_MERGE", default="Gộp sao"),
            style=discord.ButtonStyle.primary,
            row=1
        )
        btn_merge.callback = self.on_merge

        btn_wishlist = discord.ui.Button(
            label=t(lang, "GACHA_BTN_WISHLIST", default="Wishlist"),
            style=discord.ButtonStyle.secondary,
            row=1
        )
        btn_wishlist.callback = self.on_wishlist

        btn_leaderboard = discord.ui.Button(
            label=t(lang, "GACHA_BTN_LEADERBOARD", default="BXH"),
            style=discord.ButtonStyle.secondary,
            row=1
        )
        btn_leaderboard.callback = self.on_leaderboard

        # Row 2
        btn_buy_roll = discord.ui.Button(
            label=t(lang, "GACHA_BTN_BUY_ROLL", default="Mua roll"),
            style=discord.ButtonStyle.secondary,
            row=2
        )
        btn_buy_roll.callback = self.on_buy_roll

        btn_buy_claim = discord.ui.Button(
            label=t(lang, "GACHA_BTN_BUY_CLAIM", default="Mua claim"),
            style=discord.ButtonStyle.secondary,
            row=2
        )
        btn_buy_claim.callback = self.on_buy_claim

        btn_help = discord.ui.Button(
            label=t(lang, "GACHA_BTN_HELP", default="Trợ giúp"),
            style=discord.ButtonStyle.secondary,
            row=2
        )
        btn_help.callback = self.on_help

        self.add_item(btn_roll)
        self.add_item(btn_collection)
        self.add_item(btn_market)
        self.add_item(btn_merge)
        self.add_item(btn_wishlist)
        self.add_item(btn_leaderboard)
        self.add_item(btn_buy_roll)
        self.add_item(btn_buy_claim)
        self.add_item(btn_help)

    async def on_roll(self, interaction: discord.Interaction):
        await self.cog.handle_roll(interaction)

    async def on_collection(self, interaction: discord.Interaction):
        await self.cog.handle_collection(interaction)

    async def on_market(self, interaction: discord.Interaction):
        await self.cog.handle_market(interaction)

    async def on_merge(self, interaction: discord.Interaction):
        await self.cog.handle_merge(interaction)

    async def on_wishlist(self, interaction: discord.Interaction):
        await self.cog.handle_wishlist(interaction)

    async def on_leaderboard(self, interaction: discord.Interaction):
        await self.cog.handle_leaderboard(interaction)

    async def on_buy_roll(self, interaction: discord.Interaction):
        await self.cog.handle_buy_roll(interaction)

    async def on_buy_claim(self, interaction: discord.Interaction):
        await self.cog.handle_buy_claim(interaction)

    async def on_help(self, interaction: discord.Interaction):
        await self.cog.handle_help(interaction)


class WaifuGachaCog(commands.Cog, name="WaifuGacha"):
    """
    Hệ thống Gacha Waifu Anime:
    - Tính điểm theo số tim (favourites) trên AniList
    - Độ hiếm: Thường, Hiếm, Sử thi, Huyền thoại
    - Star Merge: 3 thẻ cùng loại nâng lên +1 sao & x2 điểm yêu thích
    - Giao diện nút và embed trực quan y hệt hình ảnh
    - Đa ngôn ngữ (vi, en, ja)
    """

    def __init__(self, bot):
        self.bot = bot
        self._db_initialized = False

    async def cog_load(self):
        await init_waifu_db()
        self._db_initialized = True

    # ------------------ CORE ROLL HANDLER ------------------

    async def handle_roll(self, interaction_or_ctx):
        is_inter = isinstance(interaction_or_ctx, discord.Interaction)
        inter = interaction_or_ctx if is_inter else getattr(interaction_or_ctx, "interaction", None)
        user = interaction_or_ctx.user if is_inter else interaction_or_ctx.author
        guild = interaction_or_ctx.guild
        channel = getattr(interaction_or_ctx, "channel", None)
        lang = get_guild_language(guild)

        # Kiểm tra trước quyền của bot trong kênh (tránh lỗi 403 Forbidden / Missing Access)
        if guild and channel and hasattr(channel, "permissions_for"):
            me = guild.me or (guild.get_member(self.bot.user.id) if self.bot.user else None)
            if me:
                perms = channel.permissions_for(me)
                if not (perms.view_channel and perms.send_messages and perms.embed_links):
                    perm_err = t(
                        lang,
                        "GACHA_ERR_PERMS",
                        default="❌ SakuraBot không đủ quyền trong kênh này! Yêu cầu: **Xem kênh (View Channel)**, **Gửi tin nhắn (Send Messages)** và **Chèn liên kết (Embed Links)**."
                    )
                    if inter:
                        if not inter.response.is_done():
                            return await inter.response.send_message(perm_err, ephemeral=True)
                        else:
                            return await inter.followup.send(perm_err, ephemeral=True)
                    else:
                        try:
                            return await interaction_or_ctx.send(perm_err)
                        except Exception:
                            return

        # Check and consume roll
        success, profile = await consume_roll(user.id)
        if not success:
            msg = t(lang, "GACHA_ROLL_OUT_OF_ROLLS", default="❌ Bạn đã hết lượt roll! Vui lòng chờ hồi lượt (1 lượt/5 phút) hoặc bấm **Mua roll** trong menu.")
            if inter:
                if not inter.response.is_done():
                    return await inter.response.send_message(msg, ephemeral=True)
                else:
                    return await inter.followup.send(msg, ephemeral=True)
            else:
                return await interaction_or_ctx.send(msg)

        # Pick random character
        char = await get_random_character()
        if not char:
            # Hoàn trả lượt roll nếu không tải được nhân vật
            await add_bonus_rolls(user.id, 1)
            err = t(lang, "GACHA_ERR_NO_CHAR", default="❌ Không tìm thấy dữ liệu nhân vật. Vui lòng thử lại sau ít phút!")
            if inter:
                if not inter.response.is_done():
                    return await inter.response.send_message(err, ephemeral=True)
                else:
                    return await inter.followup.send(err, ephemeral=True)
            else:
                return await interaction_or_ctx.send(err)

        # Send ephemeral notice to user (Image 2 top prompt)
        ephemeral_text = t(
            lang,
            "GACHA_ROLL_EPHEMERAL",
            default="Đã roll! Xem thẻ vừa hiện ở kênh và bấm 💖 để claim."
        )
        if inter and not inter.response.is_done():
            try:
                await inter.response.send_message(ephemeral_text, ephemeral=True)
            except Exception:
                pass

        # Build Card Embed matching Image 2
        r_name, r_indicator, r_color = get_rarity_display(char["rarity"], lang)
        favs = char["favourites"]
        bar = make_fav_bar(favs, char["rarity"])
        burn_coins = RARITY_CONFIG.get(char["rarity"], {}).get("burn_coins", 15)

        embed = discord.Embed(
            title=char["name"],
            url=char["site_url"],
            color=discord.Color.from_rgb(43, 45, 49)
        )
        author_text = t(
            lang,
            "GACHA_ROLL_ANNOUNCEMENT",
            default=f"{user.display_name} đã mở một thẻ mới!",
            name=user.display_name
        )
        embed.set_author(name=author_text, icon_url=user.display_avatar.url)

        # Format description matching Image 2
        claim_prompt = t(lang, "GACHA_ROLL_CLAIM_PROMPT", default="Bấm Claim trong 60 giây để sở hữu!")
        field_rarity = t(lang, "GACHA_FIELD_RARITY", default="Độ hiếm")
        field_fav = t(lang, "GACHA_FIELD_FAVOURITES", default="Yêu thích")
        field_burn = t(lang, "GACHA_FIELD_BURN", default=f"Giá burn: {burn_coins} 🪙", coins=burn_coins)
        field_media = t(lang, "GACHA_FIELD_APPEARS_IN", default="Xuất hiện trong")

        desc_parts = [
            f"**{char['native_name']}**",
            claim_prompt,
            "",
            f"**{field_rarity}**",
            r_name,
            r_indicator,
            "",
            f"**{field_fav}**",
            f"{favs:,}",
            bar,
            "",
            f"**{field_burn}**",
            "",
            f"**{field_media}**",
            f"{char['media_title']}"
        ]
        embed.description = "\n".join(desc_parts)

        if char.get("image_url"):
            embed.set_image(url=char["image_url"])

        # Footer matching Image 2
        remaining_rolls = profile["rolls"]
        max_rolls = profile["max_rolls"]
        footer_text = t(
            lang,
            "GACHA_ROLL_FOOTER",
            default=f"Còn {remaining_rolls}/{max_rolls} lượt roll ┆ Hồi 1 lượt/5 phút ┆ Bấm 💖 claim trong 60s",
            rolls=remaining_rolls,
            max_rolls=max_rolls
        )
        embed.set_footer(text=footer_text)

        # View with Claim Button
        view = RollCardView(self, char, time.time(), user.id, lang)
        try:
            sent_msg = await channel.send(embed=embed, view=view)
        except discord.Forbidden:
            # Hoàn trả lượt roll và thông báo lỗi quyền
            await add_bonus_rolls(user.id, 1)
            err_fb = "❌ Bot không có quyền gửi tin nhắn hoặc Embed thẻ trong kênh này (403 Forbidden / Missing Access). Lượt roll đã được hoàn trả lại cho bạn!"
            if inter:
                try:
                    if not inter.response.is_done():
                        return await inter.response.send_message(err_fb, ephemeral=True)
                    else:
                        return await inter.followup.send(err_fb, ephemeral=True)
                except Exception:
                    pass
            try:
                await user.send(err_fb)
            except Exception:
                pass
            return
        except Exception as e:
            await add_bonus_rolls(user.id, 1)
            raise e

        # Check wishlist notify
        try:
            wishlist_users = await get_wishlist_users(char["id"])
            if wishlist_users:
                mentions = []
                for uid in wishlist_users:
                    member = guild.get_member(uid)
                    if member:
                        mentions.append(member.mention)
                if mentions:
                    notify_txt = t(
                        lang,
                        "GACHA_WISHLIST_NOTIFY",
                        default=f"🔔 **{', '.join(mentions)} ơi!** Nhân vật trong Wishlist của bạn **{char['name']}** vừa xuất hiện!",
                        user=", ".join(mentions),
                        character=char["name"]
                    )
                    await channel.send(notify_txt)
        except Exception:
            pass

    # ------------------ COLLECTION HANDLER ------------------

    async def handle_collection(self, interaction_or_ctx, target_user: Optional[discord.User] = None):
        is_inter = isinstance(interaction_or_ctx, discord.Interaction)
        user = target_user or (interaction_or_ctx.user if is_inter else interaction_or_ctx.author)
        guild = interaction_or_ctx.guild
        lang = get_guild_language(guild)

        cards = await get_user_cards(user.id)
        if not cards:
            empty_msg = t(
                lang,
                "GACHA_COLLECTION_EMPTY",
                default="Bạn chưa có nhân vật nào trong bộ sưu tập. Hãy dùng nút **Roll** để bắt đầu sưu tầm!"
            )
            if is_inter:
                return await interaction_or_ctx.response.send_message(empty_msg, ephemeral=True)
            else:
                return await interaction_or_ctx.send(empty_msg)

        view = CollectionPaginationView(user, cards, lang)
        embed = view.generate_embed()

        if is_inter:
            await interaction_or_ctx.response.send_message(embed=embed, view=view, ephemeral=True)
        else:
            await interaction_or_ctx.send(embed=embed, view=view)

    # ------------------ MERGE (GỘP SAO) HANDLER ------------------

    async def handle_merge(self, interaction_or_ctx):
        is_inter = isinstance(interaction_or_ctx, discord.Interaction)
        user = interaction_or_ctx.user if is_inter else interaction_or_ctx.author
        guild = interaction_or_ctx.guild
        lang = get_guild_language(guild)

        eligible = await get_mergeable_characters(user.id)
        if not eligible:
            no_elig = t(
                lang,
                "GACHA_MERGE_NO_ELIGIBLE",
                default="❌ Bạn chưa có nhân vật nào đủ **3 thẻ cùng loại** để nâng sao!\n\n💡 **Quy tắc nâng sao:**\n• Cần **3 thẻ** cùng 1 nhân vật để nâng lên **+1 sao**.\n• Mỗi cấp sao sẽ **x2 điểm yêu thích (💖)**!\n  1⭐ ➔ 2⭐ (x2) ➔ 3⭐ (x4) ➔ 4⭐ (x8) ➔ 5⭐ (x16)."
            )
            if is_inter:
                return await interaction_or_ctx.response.send_message(no_elig, ephemeral=True)
            else:
                return await interaction_or_ctx.send(no_elig)

        view = MergeView(user, eligible, lang)
        embed = discord.Embed(
            title=t(lang, "GACHA_MERGE_TITLE", default="🌟 Gộp Sao Nhân Vật (Star Merge)"),
            description=t(lang, "GACHA_MERGE_INSTRUCT", default="Chọn nhân vật bên dưới để tiêu hao 2 thẻ trùng lặp và nâng thẻ còn lại lên **+1 sao** với điểm yêu thích **x2**!"),
            color=discord.Color.gold()
        )
        if is_inter:
            await interaction_or_ctx.response.send_message(embed=embed, view=view, ephemeral=True)
        else:
            await interaction_or_ctx.send(embed=embed, view=view)

    # ------------------ BUY ROLLS & CLAIMS HANDLERS ------------------

    async def handle_buy_roll(self, interaction_or_ctx):
        is_inter = isinstance(interaction_or_ctx, discord.Interaction)
        user = interaction_or_ctx.user if is_inter else interaction_or_ctx.author
        guild = interaction_or_ctx.guild
        lang = get_guild_language(guild)

        embed = discord.Embed(
            title=t(lang, "GACHA_BUY_ROLL_TITLE", default="🛒 Mua Thêm Lượt Roll"),
            description=t(
                lang,
                "GACHA_BUY_ROLL_DESC",
                default=(
                    "Chọn gói roll bạn muốn mua bằng coin:\n\n"
                    "• **5 Roll**: `250 🪙`\n"
                    "• **15 Roll**: `700 🪙` *(Tiết kiệm 50🪙)*\n"
                    "• **50 Roll**: `2,000 🪙` *(Tiết kiệm 500🪙)*\n\n"
                    "*(Lượt mua thêm sẽ cộng dồn và không bị giới hạn 15 lượt)*"
                )
            ),
            color=discord.Color.green()
        )
        view = BuyRollsView(user, guild.id if guild else 0, lang)
        if is_inter:
            await interaction_or_ctx.response.send_message(embed=embed, view=view, ephemeral=True)
        else:
            await interaction_or_ctx.send(embed=embed, view=view)

    async def handle_buy_claim(self, interaction_or_ctx):
        is_inter = isinstance(interaction_or_ctx, discord.Interaction)
        user = interaction_or_ctx.user if is_inter else interaction_or_ctx.author
        guild = interaction_or_ctx.guild
        lang = get_guild_language(guild)

        embed = discord.Embed(
            title=t(lang, "GACHA_BUY_CLAIM_TITLE", default="🛒 Mua Thêm Lượt Claim"),
            description=t(
                lang,
                "GACHA_BUY_CLAIM_DESC",
                default=(
                    "Chọn gói claim bạn muốn mua bằng coin:\n\n"
                    "• **1 Claim**: `1,500 🪙`\n"
                    "• **3 Claim**: `4,000 🪙` *(Tiết kiệm 500🪙)*\n\n"
                    "*(Lượt mua thêm sẽ cộng dồn ngay lập tức)*"
                )
            ),
            color=discord.Color.magenta()
        )
        view = BuyClaimsView(user, guild.id if guild else 0, lang)
        if is_inter:
            await interaction_or_ctx.response.send_message(embed=embed, view=view, ephemeral=True)
        else:
            await interaction_or_ctx.send(embed=embed, view=view)

    # ------------------ MARKETPLACE HANDLER ------------------

    async def handle_market(self, interaction_or_ctx):
        is_inter = isinstance(interaction_or_ctx, discord.Interaction)
        user = interaction_or_ctx.user if is_inter else interaction_or_ctx.author
        guild = interaction_or_ctx.guild
        lang = get_guild_language(guild)

        listings, total = await get_market_listings(limit=10, offset=0)
        embed = discord.Embed(
            title=t(lang, "GACHA_MARKET_TITLE", default="🏪 Chợ Thẻ Waifu (Waifu Marketplace)"),
            color=discord.Color.blue()
        )

        if not listings:
            embed.description = t(
                lang,
                "GACHA_MARKET_EMPTY",
                default="Hiện chưa có thẻ nào được rao bán trên chợ.\n\n💡 Để đăng bán thẻ của bạn, hãy dùng lệnh:\n`.gacha sell <mã_thẻ> <giá_coin>` (ví dụ: `.gacha sell e18a9f 500`)"
            )
            if is_inter:
                return await interaction_or_ctx.response.send_message(embed=embed, ephemeral=True)
            else:
                return await interaction_or_ctx.send(embed=embed)

        lines = [t(lang, "GACHA_MARKET_TOTAL", default=f"Tổng cộng có **{total}** thẻ đang được bày bán:\n", total=total)]
        for idx, l in enumerate(listings, start=1):
            lines.append(f"**{idx}. {l['name']}** {l['stars']}⭐ ┆ 💖{l['points']:,} ┆ #{l['print_number']} ┆ `{l['card_code']}` ➔ **{l['price_coins']:,}🪙**")

        lines.append(t(lang, "GACHA_MARKET_HINT", default="\n💡 Dùng menu bên dưới để chọn mua, hoặc lệnh `.gacha sell <mã> <giá>` để đăng bán!"))
        embed.description = "\n".join(lines)

        view = MarketPaginationView(user, listings, total, guild.id if guild else 0, lang)
        if is_inter:
            await interaction_or_ctx.response.send_message(embed=embed, view=view, ephemeral=True)
        else:
            await interaction_or_ctx.send(embed=embed, view=view)

    # ------------------ WISHLIST HANDLER ------------------

    async def handle_wishlist(self, interaction_or_ctx):
        is_inter = isinstance(interaction_or_ctx, discord.Interaction)
        user = interaction_or_ctx.user if is_inter else interaction_or_ctx.author
        guild = interaction_or_ctx.guild
        lang = get_guild_language(guild)

        wishlist = await get_user_wishlist(user.id)
        embed = discord.Embed(
            title=t(lang, "GACHA_WISHLIST_TITLE", default=f"💖 Wishlist Của {user.display_name}", name=user.display_name),
            color=discord.Color.purple()
        )

        if not wishlist:
            embed.description = t(
                lang,
                "GACHA_WISHLIST_EMPTY",
                default=(
                    "Wishlist của bạn đang trống!\n\n"
                    "💡 **Cách thêm vào Wishlist:**\n"
                    "• Gõ lệnh `.gacha wish <tên_nhân_vật>` (Ví dụ: `.gacha wish Frieren`)\n"
                    "• Khi có bất kỳ ai trong server roll trúng nhân vật này, Bot sẽ thông báo ngay cho bạn!"
                )
            )
        else:
            lines = [t(lang, "GACHA_WISHLIST_HEADER", default=f"Danh sách mong ước ({len(wishlist)}/10):\n", count=len(wishlist))]
            for idx, w in enumerate(wishlist, start=1):
                r_name, r_indicator, _ = get_rarity_display(w["rarity"], lang)
                lines.append(f"**{idx}. {w['name']}** ({w['native_name']}) ┆ {r_indicator} ┆ 💖{w['favourites']:,}")
            lines.append(t(lang, "GACHA_WISHLIST_FOOTER_HINT", default="\n💡 Dùng `.gacha wish remove <tên>` để xóa khỏi wishlist."))
            embed.description = "\n".join(lines)

        if is_inter:
            await interaction_or_ctx.response.send_message(embed=embed, ephemeral=True)
        else:
            await interaction_or_ctx.send(embed=embed)

    # ------------------ LEADERBOARD HANDLER ------------------

    async def handle_leaderboard(self, interaction_or_ctx):
        is_inter = isinstance(interaction_or_ctx, discord.Interaction)
        guild = interaction_or_ctx.guild
        lang = get_guild_language(guild)

        top_users = await get_top_collectors(limit=10)
        embed = discord.Embed(
            title=t(lang, "GACHA_LB_TITLE", default="🏆 Bảng Xếp Hạng Nhà Sưu Tầm Waifu (Top Collectors)"),
            color=discord.Color.gold()
        )

        if not top_users:
            embed.description = t(lang, "GACHA_LB_EMPTY", default="Chưa có dữ liệu sưu tập nào.")
        else:
            medals = ["🥇", "🥈", "🥉", "4️⃣", "5️⃣", "6️⃣", "7️⃣", "8️⃣", "9️⃣", "🔟"]
            unit_cards = t(lang, "GACHA_UNIT_CARDS", default="thẻ")
            unit_merges = t(lang, "GACHA_UNIT_MERGES", default="lần gộp")
            lines = []
            for idx, u in enumerate(top_users):
                uid = u["user_id"]
                member = guild.get_member(uid) if guild else None
                name = member.display_name if member else f"User {uid}"
                medal = medals[idx] if idx < len(medals) else f"#{idx+1}"
                tot_p = u["total_points"] or 0
                tot_c = u["total_cards"] or 0
                merges = u.get("total_merges", 0) or 0
                lines.append(f"{medal} **{name}** ┆ 💖 **{tot_p:,}** ┆ 🎴 **{tot_c}** {unit_cards} ┆ 🌟 **{merges}** {unit_merges}")

            embed.description = "\n".join(lines)

        if is_inter:
            await interaction_or_ctx.response.send_message(embed=embed, ephemeral=True)
        else:
            await interaction_or_ctx.send(embed=embed)

    # ------------------ HELP HANDLER ------------------

    async def handle_help(self, interaction_or_ctx):
        is_inter = isinstance(interaction_or_ctx, discord.Interaction)
        guild = interaction_or_ctx.guild
        lang = get_guild_language(guild)

        embed = discord.Embed(
            title=t(lang, "GACHA_HELP_TITLE", default="📖 Hướng Dẫn Trò Chơi Gacha Waifu"),
            color=discord.Color.from_rgb(255, 182, 193),
            description=t(
                lang,
                "GACHA_HELP_DESC",
                default=(
                    "**Hệ thống sưu tầm thẻ bài Waifu anime đỉnh cao:**\n\n"
                    "🌸 **Lượt Roll & Claim:**\n"
                    "• **Roll**: Hồi 1 lượt / 5 phút (tối đa 15 lượt tự nhiên).\n"
                    "• **Claim**: Hồi 1 lượt / 2 tiếng. Bấm **Claim** trong 60 giây khi thẻ xuất hiện để sở hữu.\n\n"
                    "💎 **Độ hiếm & Giá Burn Thẻ:**\n"
                    "• `Thường` (🔷 ◽ ◽ ◽): < 2,000 💖 ➔ Burn: **15 🪙**\n"
                    "• `Hiếm` (🔷 🔷 ◽ ◽): 2,000 - 8,000 💖 ➔ Burn: **50 🪙**\n"
                    "• `Sử thi` (🔷 🔷 🔷 ◽): 8,000 - 20,000 💖 ➔ Burn: **150 🪙**\n"
                    "• `Huyền thoại` (🔷 🔷 🔷 🔷): ≥ 20,000 💖 ➔ Burn: **500 🪙**\n\n"
                    "🌟 **Cơ chế Gộp Sao (Star Merge):**\n"
                    "• Cứ **3 thẻ cùng loại** sẽ gộp được lên **+1 sao**.\n"
                    "• Mỗi cấp sao sẽ **x2 điểm yêu thích (💖)**!\n"
                    "  1⭐ (x1) ➔ 2⭐ (x2) ➔ 3⭐ (x4) ➔ 4⭐ (x8) ➔ 5⭐ (x16)\n\n"
                    "⌨️ **Các lệnh gõ tắt:**\n"
                    "• `.gacha` hoặc `/gacha`: Mở menu chính\n"
                    "• `.roll` hoặc `/gacha roll`: Roll thẻ nhanh\n"
                    "• `.col` hoặc `/gacha collection`: Xem bộ sưu tập\n"
                    "• `.gacha burn <code>`: Bán thẻ lấy coin\n"
                    "• `.gacha sell <code> <giá>`: Đăng bán thẻ lên chợ\n"
                    "• `.gacha wish <tên>`: Thêm nhân vật vào Wishlist"
                )
            )
        )
        if is_inter:
            await interaction_or_ctx.response.send_message(embed=embed, ephemeral=True)
        else:
            await interaction_or_ctx.send(embed=embed)

    # ------------------ COMMAND REGISTRATION ------------------

    # pyrefly: ignore[unexpected-keyword]
    @commands.hybrid_group(name="gacha", aliases=["g"], fallback="menu", invoke_without_command=True, description="Open Waifu Gacha interactive menu / Mở menu Gacha Waifu")
    async def gacha(self, ctx: commands.Context):
        """Mở menu điều khiển chính của Gacha Waifu với đầy đủ các nút bấm y hệt hình ảnh."""
        lang = get_guild_language(ctx.guild)
        embed = discord.Embed(
            title=t(lang, "GACHA_MENU_TITLE", default="Gacha Waifu"),
            description=t(
                lang,
                "GACHA_MENU_DESC",
                default="Roll nhân vật anime ➔ bấm **Claim** để sở hữu ➔ sưu tầm, nâng sao, mua bán!\n*Mẹo: vẫn dùng được lệnh .gacha <hành động> nếu thích gõ tay*"
            ),
            color=discord.Color.from_rgb(43, 45, 49)
        )
        view = GachaMenuView(self, lang)
        await ctx.send(embed=embed, view=view)

    @gacha.command(name="roll",aliases=["r"], description="Roll a waifu card / Roll thẻ nhân vật mới")
    async def gacha_roll(self, ctx: commands.Context):
        """Roll một nhân vật mới."""
        await self.handle_roll(ctx)

    @gacha.command(name="collection", aliases=["col", "bst"], description="View your waifu collection / Xem bộ sưu tập")
    @app_commands.describe(user="User whose collection you want to view")
    async def gacha_col(self, ctx: commands.Context, user: Optional[discord.User] = None):
        """Xem bộ sưu tập thẻ waifu."""
        await self.handle_collection(ctx, user)

    @gacha.command(name="merge", aliases=["gopsao"], description="Merge 3 duplicate cards to upgrade +1 star / Gộp 3 thẻ cùng loại lên +1 sao")
    async def gacha_merge(self, ctx: commands.Context):
        """Gộp 3 thẻ trùng lặp để nâng sao."""
        await self.handle_merge(ctx)

    @gacha.command(name="burn", description="Burn a card for coins / Bán thẻ lấy coins")
    @app_commands.describe(code="The 6-character card code (e.g. e18a9f)")
    async def gacha_burn(self, ctx: commands.Context, code: str):
        """Bán (burn) thẻ không dùng để nhận coins."""
        lang = get_guild_language(ctx.guild)
        guild_id = ctx.guild.id if ctx.guild else 0
        success, coins, card = await burn_card(code.strip(), ctx.author.id)

        if not success:
            err = t(
                lang,
                "GACHA_BURN_NOT_FOUND",
                default=f"❌ Không tìm thấy thẻ có mã `{code}` hoặc thẻ đang treo trên chợ!",
                code=code
            )
            return await ctx.send(err)

        # Award coins to user
        await update_user_coins(guild_id, ctx.author.id, coins)

        msg = t(
            lang,
            "GACHA_BURN_SUCCESS",
            default=f"🔥 Đã burn thẻ **{card['name']}** (`{code}`) thành công! Bạn nhận được **+{coins}🪙**.",
            character=card["name"],
            code=code,
            coins=coins
        )
        await ctx.send(msg)

    @gacha.command(name="buyroll", description="Buy extra rolls with coins / Mua thêm lượt roll")
    async def gacha_buyroll(self, ctx: commands.Context):
        """Mua thêm lượt roll bằng coins."""
        await self.handle_buy_roll(ctx)

    @gacha.command(name="buyclaim", description="Buy extra claims with coins / Mua thêm lượt claim")
    async def gacha_buyclaim(self, ctx: commands.Context):
        """Mua thêm lượt claim bằng coins."""
        await self.handle_buy_claim(ctx)

    @gacha.command(name="market", aliases=["cho"], description="View Waifu Marketplace / Xem chợ thẻ waifu")
    async def gacha_market(self, ctx: commands.Context):
        """Mở chợ trao đổi buôn bán thẻ."""
        await self.handle_market(ctx)

    @gacha.command(name="sell", description="List a card for sale on marketplace / Đăng bán thẻ lên chợ")
    @app_commands.describe(code="Card code to sell", price="Price in coins")
    async def gacha_sell(self, ctx: commands.Context, code: str, price: int):
        """Đăng bán thẻ của bạn lên chợ."""
        lang = get_guild_language(ctx.guild)
        if price <= 0:
            return await ctx.send(t(lang, "GACHA_SELL_INVALID_PRICE", default="❌ Giá bán phải lớn hơn 0🪙!"))

        success, status = await list_card_for_sale(code.strip(), ctx.author.id, price)
        if not success:
            if status == "NOT_OWNER":
                return await ctx.send(t(lang, "GACHA_SELL_NOT_OWNER", default="❌ Bạn không sở hữu thẻ có mã này!"))
            elif status == "ALREADY_LISTED":
                return await ctx.send(t(lang, "GACHA_SELL_ALREADY", default="❌ Thẻ này đã được đăng bán trên chợ rồi!"))
            return await ctx.send(t(lang, "GACHA_SELL_FAIL", default="❌ Đăng bán thất bại."))

        await ctx.send(t(lang, "GACHA_SELL_SUCCESS", default=f"✅ Đã niêm yết thẻ `{code}` lên chợ với giá **{price:,}🪙** thành công!", code=code, price=f"{price:,}"))

    @gacha.command(name="wishlist", aliases=["wish"], description="Manage your character wishlist / Quản lý danh sách mong ước")
    @app_commands.describe(action="add / remove / view", character_name="Name of anime character")
    async def gacha_wish(self, ctx: commands.Context, action: Optional[str] = "view", *, character_name: Optional[str] = None):
        """Quản lý wishlist waifu."""
        lang = get_guild_language(ctx.guild)
        act = (action or "view").lower().strip()
        if act == "view" or (not character_name and act not in ["add", "them", "remove", "xoa", "del"]):
            return await self.handle_wishlist(ctx)

        if act in ["add", "them"] and character_name:
            chars = await search_characters(character_name, limit=1)
            if not chars:
                return await ctx.send(t(lang, "GACHA_WISH_NOT_FOUND", default=f"❌ Không tìm thấy nhân vật nào có tên `{character_name}` trong kho!", name=character_name))
            c = chars[0]
            succ, status = await add_wishlist(ctx.author.id, c["id"])
            if not succ:
                if status == "WISHLIST_MAX_REACHED":
                    return await ctx.send(t(lang, "GACHA_WISH_MAX", default="❌ Wishlist của bạn đã đạt giới hạn tối đa (10 nhân vật)!"))
                elif status == "ALREADY_WISHLISTED":
                    return await ctx.send(t(lang, "GACHA_WISH_EXISTS", default=f"❌ **{c['name']}** đã có trong wishlist của bạn rồi!", name=c['name']))
                return await ctx.send(t(lang, "GACHA_WISH_FAIL", default="❌ Thao tác thất bại."))
            return await ctx.send(t(lang, "GACHA_WISH_ADD_SUCCESS", default=f"💖 Đã thêm **{c['name']}** vào wishlist! Bot sẽ thông báo khi có ai roll trúng!", name=c['name']))

        elif act in ["remove", "xoa", "del"] and character_name:
            chars = await search_characters(character_name, limit=1)
            if not chars:
                return await ctx.send(t(lang, "GACHA_WISH_NOT_FOUND", default=f"❌ Không tìm thấy nhân vật `{character_name}`!", name=character_name))
            c = chars[0]
            succ, _ = await remove_wishlist(ctx.author.id, c["id"])
            if not succ:
                return await ctx.send(t(lang, "GACHA_WISH_NOT_IN_LIST", default=f"❌ **{c['name']}** không có trong wishlist của bạn!", name=c['name']))
            return await ctx.send(t(lang, "GACHA_WISH_REMOVE_SUCCESS", default=f"✅ Đã xóa **{c['name']}** khỏi wishlist.", name=c['name']))

        await self.handle_wishlist(ctx)

    @gacha.command(name="top", aliases=["bxh", "leaderboard"], description="Top waifu collectors / Bảng xếp hạng người chơi")
    async def gacha_top(self, ctx: commands.Context):
        """Bảng xếp hạng người sưu tầm."""
        await self.handle_leaderboard(ctx)

    @gacha.command(name="help", description="Waifu Gacha guide & help / Hướng dẫn Gacha Waifu")
    async def gacha_help(self, ctx: commands.Context):
        """Xem hướng dẫn luật chơi."""
        await self.handle_help(ctx)

    # ------------------ SHORTCUT PREFIX COMMANDS ------------------

    @commands.command(name="roll", description="Quick roll a waifu card / Roll thẻ waifu nhanh")
    async def quick_roll(self, ctx: commands.Context):
        """Lệnh tắt để roll waifu nhanh."""
        await self.handle_roll(ctx)

    @commands.command(name="collection", aliases=["col"], description="Quick view your waifu collection / Xem bộ sưu tập nhanh")
    async def quick_collection(self, ctx: commands.Context, user: Optional[discord.User] = None):
        """Lệnh tắt để xem bộ sưu tập."""
        await self.handle_collection(ctx, user)


async def setup(bot):
    await bot.add_cog(WaifuGachaCog(bot))
