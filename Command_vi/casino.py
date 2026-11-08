from Checks_vi.i18n import t, is_vietnamese
import asyncio
import random
from typing import Literal, Optional

import aiosqlite
import discord
from discord import app_commands
from discord.ext import commands, tasks

from data.database import (
    DB_PATH,
    add_user_currency,
    deduct_user_currency,
    get_user_currency,
    get_user_data,
    init_db,
    update_user_coins,
    update_user_xu,
)

# --- LOCK CHỐNG SPAM CLICK TRÙNG VÁN ---
_active_game_users = set()

# --- CARDS & SUITS CHO BLACKJACK ---
CARD_VALUES = {"2": 2, "3": 3, "4": 4, "5": 5, "6": 6, "7": 7, "8": 8, "9": 9, "10": 10, "J": 10, "Q": 10, "K": 10, "A": 11}
SUITS = ["♠", "♥", "♦", "♣"]

DICE_EMOJIS = {1: "⚀", 2: "⚁", 3: "⚂", 4: "⚃", 5: "⚄", 6: "⚅"}

BAUCUA_ITEMS = {
    "nai": {"name": "Nai", "emoji": "🦌"},
    "bau": {"name": "Bầu", "emoji": "🎃"},
    "ga": {"name": "Gà", "emoji": "🐓"},
    "ca": {"name": "Cá", "emoji": "🐟"},
    "cua": {"name": "Cua", "emoji": "🦀"},
    "tom": {"name": "Tôm", "emoji": "🦐"},
}

SLOT_SYMBOLS = ["🍒", "🍋", "🍇", "🔔", "💎", "7️⃣"]


def draw_card():
    rank = random.choice(list(CARD_VALUES.keys()))
    suit = random.choice(SUITS)
    return f"{rank}{suit}", rank


def calculate_hand(ranks: list[str]) -> int:
    val = sum(CARD_VALUES[r] for r in ranks)
    aces = ranks.count("A")
    while val > 21 and aces > 0:
        val -= 10
        aces -= 1
    return val


def cur_badge(currency: str) -> str:
    return "🪙" if currency == "coins" else "💎"


# ================= VIEW: BLACKJACK =================
class BlackjackView(discord.ui.View):
    def __init__(self, author: discord.Member, bet: int, currency: str = "coins"):
        super().__init__(timeout=60)
        self.author = author
        self.bet = bet
        self.currency = currency
        self.player_cards = [draw_card(), draw_card()]
        self.dealer_cards = [draw_card(), draw_card()]
        self.ended = False

        vi = is_vietnamese(getattr(author, "guild", None))
        self.hit.label = "Rút Bài (Hit)" if vi else "Hit (Draw)"
        self.stand.label = "Dằn Bài (Stand)" if vi else "Stand"

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id != self.author.id:
            vi = is_vietnamese(interaction.guild)
            msg = "❌ Đây không phải ván bài của bạn!" if vi else "❌ This is not your blackjack table!"
            await interaction.response.send_message(msg, ephemeral=True)
            return False
        return True

    async def on_timeout(self):
        _active_game_users.discard(self.author.id)
        for child in self.children:
            child.disabled = True

    def build_embed(self, hide_dealer: bool = True, final_text: str = None) -> discord.Embed:
        p_ranks = [c[1] for c in self.player_cards]
        p_val = calculate_hand(p_ranks)
        p_str = " ".join(f"`{c[0]}`" for c in self.player_cards)

        vi = is_vietnamese(getattr(self.author, "guild", None))
        title_str = f"🃏 Bàn Xì Dách của {self.author.display_name}" if vi else f"🃏 {self.author.display_name}'s Blackjack Table"
        embed = discord.Embed(title=title_str, color=discord.Color.dark_blue())
        embed.add_field(name=f"👤 {('Bạn' if vi else 'You')} ({p_val} {('điểm' if vi else 'pts')})", value=p_str, inline=False)

        if hide_dealer:
            embed.add_field(name="🎰 " + ("Nhà Cái" if vi else "Dealer"), value=f"`{self.dealer_cards[0][0]}` `❓`", inline=False)
        else:
            d_ranks = [c[1] for c in self.dealer_cards]
            d_val = calculate_hand(d_ranks)
            d_str = " ".join(f"`{c[0]}`" for c in self.dealer_cards)
            embed.add_field(name=f"🎰 {('Nhà Cái' if vi else 'Dealer')} ({d_val} {('điểm' if vi else 'pts')})", value=d_str, inline=False)

        if final_text:
            embed.description = final_text
        embed.set_footer(text=f"{('Tiền cược' if vi else 'Bet')}: {self.bet:,} {cur_badge(self.currency)}")
        return embed

    @discord.ui.button(label="Rút Bài (Hit)", style=discord.ButtonStyle.primary, emoji="🃏")
    async def hit(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.player_cards.append(draw_card())
        p_val = calculate_hand([c[1] for c in self.player_cards])

        if p_val > 21:
            self.ended = True
            _active_game_users.discard(self.author.id)
            for child in self.children:
                child.disabled = True
            vi = is_vietnamese(interaction.guild)
            bust_msg = f"💥 **Quắc (Bust)! Bạn đã vượt quá 21 điểm và mất `{self.bet:,}` {cur_badge(self.currency)}!**" if vi else f"💥 **Bust! You exceeded 21 points and lost `{self.bet:,}` {cur_badge(self.currency)}!**"
            await interaction.response.edit_message(
                embed=self.build_embed(hide_dealer=False, final_text=bust_msg),
                view=self
            )
            self.stop()
        else:
            await interaction.response.edit_message(embed=self.build_embed(hide_dealer=True), view=self)

    @discord.ui.button(label="Dằn Bài (Stand)", style=discord.ButtonStyle.success, emoji="🛑")
    async def stand(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.ended = True
        _active_game_users.discard(self.author.id)
        for child in self.children:
            child.disabled = True

        p_val = calculate_hand([c[1] for c in self.player_cards])
        d_ranks = [c[1] for c in self.dealer_cards]
        while calculate_hand(d_ranks) < 17:
            self.dealer_cards.append(draw_card())
            d_ranks = [c[1] for c in self.dealer_cards]

        d_val = calculate_hand(d_ranks)
        gid, uid = interaction.guild_id, self.author.id

        vi = is_vietnamese(interaction.guild)
        if d_val > 21 or p_val > d_val:
            win_amount = self.bet * 2
            await add_user_currency(gid, uid, self.currency, win_amount)
            msg = f"🎉 **Chiến thắng! Nhà cái bị quắc hoặc điểm thấp hơn. Bạn nhận lại `{win_amount:,}` {cur_badge(self.currency)}!**" if vi else f"🎉 **Win! The Dealer busted or had a lower hand. You receive `{win_amount:,}` {cur_badge(self.currency)}!**"
        elif p_val == d_val:
            await add_user_currency(gid, uid, self.currency, self.bet)
            msg = f"🤝 **Hòa (Push)! Bạn được hoàn lại `{self.bet:,}` {cur_badge(self.currency)}.**" if vi else f"🤝 **Push (Tie)! Your bet of `{self.bet:,}` {cur_badge(self.currency)} was refunded.**"
        else:
            msg = f"💀 **Thua cuộc! Nhà cái có điểm cao hơn ({d_val} > {p_val}). Bạn mất `{self.bet:,}` {cur_badge(self.currency)}.**" if vi else f"💀 **Loss! Dealer had a higher hand ({d_val} > {p_val}). You lost `{self.bet:,}` {cur_badge(self.currency)}.**"

        await interaction.response.edit_message(embed=self.build_embed(hide_dealer=False, final_text=msg), view=self)
        self.stop()


# ================= METADATA CÁC TRÒ CHƠI CASINO =================
GAME_INFO = {
    "taixiu": {
        "name_vi": "Tài Xỉu",
        "name_en": "Sic Bo (Over/Under)",
        "icon": "⚖️",
        "desc_vi": "Dự đoán tổng điểm 3 viên xúc xắc: Xỉu (4-10) x2, Tài (11-17) x2, Bão x30.",
        "desc_en": "Predict sum of 3 dice: Under (4-10) x2, Over (11-17) x2, Triple (Bão) x30.",
        "choices_vi": [
            ("tai", "🔴 Tài (11-17)", discord.ButtonStyle.danger),
            ("xiu", "🔵 Xỉu (4-10)", discord.ButtonStyle.primary),
            ("bao", "👑 Bão (x30)", discord.ButtonStyle.success),
        ],
        "choices_en": [
            ("tai", "🔴 Over (11-17)", discord.ButtonStyle.danger),
            ("xiu", "🔵 Under (4-10)", discord.ButtonStyle.primary),
            ("bao", "👑 Triple (x30)", discord.ButtonStyle.success),
        ],
        "default_choice": "tai"
    },
    "chanle": {
        "name_vi": "Xóc Đĩa Chẵn Lẻ",
        "name_en": "Even / Odd Dice",
        "icon": "🎲",
        "desc_vi": "Dự đoán tổng nút là Chẵn hoặc Lẻ với tỷ lệ x1.95.",
        "desc_en": "Predict sum of dice as Even or Odd with x1.95 payout.",
        "choices_vi": [
            ("chan", "🔵 Chẵn (x1.95)", discord.ButtonStyle.primary),
            ("le", "🔴 Lẻ (x1.95)", discord.ButtonStyle.danger),
        ],
        "choices_en": [
            ("chan", "🔵 Even (x1.95)", discord.ButtonStyle.primary),
            ("le", "🔴 Odd (x1.95)", discord.ButtonStyle.danger),
        ],
        "default_choice": "chan"
    },
    "doden": {
        "name_vi": "Vòng Quay Đỏ Đen",
        "name_en": "Red / Black Roulette",
        "icon": "🎡",
        "desc_vi": "Roulette 37 số: Đỏ x2, Đen x2, Hoàng Kim Số 0 x14.",
        "desc_en": "37-number Roulette: Red x2, Black x2, Golden Zero x14.",
        "choices_vi": [
            ("red", "🔴 Đỏ (x2)", discord.ButtonStyle.danger),
            ("black", "⚫ Đen (x2)", discord.ButtonStyle.secondary),
            ("zero", "🟢 Số 0 (x14)", discord.ButtonStyle.success),
        ],
        "choices_en": [
            ("red", "🔴 Red (x2)", discord.ButtonStyle.danger),
            ("black", "⚫ Black (x2)", discord.ButtonStyle.secondary),
            ("zero", "🟢 Zero (x14)", discord.ButtonStyle.success),
        ],
        "default_choice": "red"
    },
    "coinflip": {
        "name_vi": "Tung Đồng Xu",
        "name_en": "Coinflip",
        "icon": "🪙",
        "desc_vi": "Tung đồng xu may mắn: Ngửa (Heads) x2 hoặc Sấp (Tails) x2.",
        "desc_en": "Flip coin 50/50: Heads x2 or Tails x2.",
        "choices_vi": [
            ("heads", "🪙 Ngửa (Heads)", discord.ButtonStyle.primary),
            ("tails", "🪙 Sấp (Tails)", discord.ButtonStyle.secondary),
        ],
        "choices_en": [
            ("heads", "🪙 Heads (x2)", discord.ButtonStyle.primary),
            ("tails", "🪙 Tails (x2)", discord.ButtonStyle.secondary),
        ],
        "default_choice": "heads"
    },
    "baucua": {
        "name_vi": "Bầu Cua Tôm Cá",
        "name_en": "Bau Cua (Vietnamese Mascot Dice)",
        "icon": "🦀",
        "desc_vi": "Lắc 3 xúc xắc linh vật: Trúng 1 con x2, 2 con x3, 3 con x4.",
        "desc_en": "Roll 3 mascot dice: Match 1 mascot x2, 2 mascots x3, 3 mascots x4.",
        "choices_vi": [
            ("nai", "🦌 Nai", discord.ButtonStyle.secondary),
            ("bau", "🎃 Bầu", discord.ButtonStyle.secondary),
            ("ga", "🐓 Gà", discord.ButtonStyle.secondary),
            ("ca", "🐟 Cá", discord.ButtonStyle.secondary),
            ("cua", "🦀 Cua", discord.ButtonStyle.secondary),
            ("tom", "🦐 Tôm", discord.ButtonStyle.secondary),
        ],
        "choices_en": [
            ("nai", "🦌 Nai", discord.ButtonStyle.secondary),
            ("bau", "🎃 Bầu", discord.ButtonStyle.secondary),
            ("ga", "🐓 Gà", discord.ButtonStyle.secondary),
            ("ca", "🐟 Cá", discord.ButtonStyle.secondary),
            ("cua", "🦀 Cua", discord.ButtonStyle.secondary),
            ("tom", "🦐 Tôm", discord.ButtonStyle.secondary),
        ],
        "default_choice": "bau"
    },
    "slots": {
        "name_vi": "Máy Xèng Slots 777",
        "name_en": "Slots 777 Jackpot",
        "icon": "🎰",
        "desc_vi": "Quay máy xèng 3 cuộn: x2, x5, x7, x10, x15, Jackpot x20.",
        "desc_en": "Spin 3-reel slot machine: x2, x5, x7, x10, x15, Jackpot x20.",
        "choices_vi": [],
        "choices_en": [],
        "default_choice": "spin"
    },
    "blackjack": {
        "name_vi": "Xì Dách Blackjack",
        "name_en": "Blackjack 21",
        "icon": "🃏",
        "desc_vi": "Đấu bài với Dealer rút bài đến 21 điểm, thắng ăn x2.",
        "desc_en": "Play against the Dealer drawing to 21, win pays 1:1 (x2).",
        "choices_vi": [],
        "choices_en": [],
        "default_choice": "play"
    }
}


# ================= MODAL NHẬP TIỀN CƯỢC TÙY CHỈNH =================
class CustomBetModal(discord.ui.Modal):
    def __init__(self, parent_view: "CasinoBetView"):
        vi = is_vietnamese(parent_view.guild_id)
        title_str = "✏️ Nhập Số Tiền Cược Tùy Chỉnh" if vi else "✏️ Enter Custom Bet Amount"
        super().__init__(title=title_str)
        self.parent_view = parent_view
        self.amount_input = discord.ui.TextInput(
            label="Số tiền muốn đặt cược" if vi else "Bet amount",
            placeholder="Ví dụ: 25000, 50k, 2.5m, 100000..." if vi else "Ex: 25000, 50k, 2.5m, 100000...",
            min_length=1,
            max_length=20,
            required=True
        )
        self.add_item(self.amount_input)

    def __init__(self, parent_view: "CasinoBetView"):
        super().__init__()
        self.parent_view = parent_view

    async def on_submit(self, interaction: discord.Interaction):
        raw = self.amount_input.value.strip().lower().replace(",", "").replace(".", "").replace(" ", "")
        mult = 1
        if raw.endswith("k"):
            mult = 1_000
            raw = raw[:-1]
        elif raw.endswith("m"):
            mult = 1_000_000
            raw = raw[:-1]
        elif raw.endswith("b"):
            mult = 1_000_000_000
            raw = raw[:-1]

        try:
            val = int(float(raw) * mult)
            if val <= 0:
                return await interaction.response.send_message("❌ Số tiền cược phải lớn hơn 0!", ephemeral=True)
            self.parent_view.amount = val
            await self.parent_view.refresh_view(interaction)
        except ValueError:
            await interaction.response.send_message("❌ Số tiền nhập không hợp lệ! Vui lòng nhập số hợp lệ.", ephemeral=True)


# ================= VIEW ĐẶT CƯỢC CASINO TOÀN DIỆN =================
class CasinoBetView(discord.ui.View):
    def __init__(
        self,
        cog: "CasinoCog",
        author: discord.Member,
        guild_id: int,
        game: str = "taixiu",
        amount: int = 1000,
        currency: str = "coins",
        choice: Optional[str] = None,
        timeout: float = 120.0
    ):
        super().__init__(timeout=timeout)
        self.cog = cog
        self.author = author
        self.guild_id = guild_id
        self.game = game if game in GAME_INFO else "taixiu"
        self.amount = max(1, amount)
        self.currency = currency if currency in ("coins", "xu") else "coins"
        self.choice = choice or GAME_INFO[self.game]["default_choice"]
        self.message: Optional[discord.Message] = None
        self.setup_items()

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id != self.author.id:
            await interaction.response.send_message(
                "❌ Bảng đặt cược này không phải của bạn! Hãy gõ `/casino` hoặc lệnh game để mở bảng cược riêng.",
                ephemeral=True
            )
            return False
        return True

    async def on_timeout(self):
        for item in self.children:
            item.disabled = True
        if self.message:
            try:
                await self.message.edit(view=self)
            except Exception:
                pass

    def setup_items(self):
        self.clear_items()
        vi = is_vietnamese(self.guild_id)

        # Row 0: Các mốc cược cố định & nút tùy chỉnh
        btn_1k = discord.ui.Button(label="+1k", style=discord.ButtonStyle.secondary, row=0)
        btn_1k.callback = self.make_add_callback(1_000)
        self.add_item(btn_1k)

        btn_10k = discord.ui.Button(label="+10k", style=discord.ButtonStyle.secondary, row=0)
        btn_10k.callback = self.make_add_callback(10_000)
        self.add_item(btn_10k)

        btn_50k = discord.ui.Button(label="+50k", style=discord.ButtonStyle.secondary, row=0)
        btn_50k.callback = self.make_add_callback(50_000)
        self.add_item(btn_50k)

        btn_100k = discord.ui.Button(label="+100k", style=discord.ButtonStyle.secondary, row=0)
        btn_100k.callback = self.make_add_callback(100_000)
        self.add_item(btn_100k)

        btn_custom = discord.ui.Button(label="✏️ Tùy Chỉnh" if vi else "✏️ Custom", style=discord.ButtonStyle.primary, row=0)
        btn_custom.callback = self.btn_custom_callback
        self.add_item(btn_custom)

        # Row 1: Thao tác cược nhanh & Chọn loại tiền
        btn_double = discord.ui.Button(label="✖️2 Gấp Đôi" if vi else "✖️2 Double", style=discord.ButtonStyle.secondary, row=1)
        btn_double.callback = self.btn_double_callback
        self.add_item(btn_double)

        btn_allin = discord.ui.Button(label="💥 All-in", style=discord.ButtonStyle.secondary, row=1)
        btn_allin.callback = self.btn_allin_callback
        self.add_item(btn_allin)

        btn_reset = discord.ui.Button(label="🔄 Reset", style=discord.ButtonStyle.secondary, row=1)
        btn_reset.callback = self.btn_reset_callback
        self.add_item(btn_reset)

        if vi:
            cur_lbl = "🪙 Tiền: Coins" if self.currency == "coins" else "💎 Tiền: Xu"
        else:
            cur_lbl = "🪙 Currency: Coins" if self.currency == "coins" else "💎 Currency: Xu"
        cur_style = discord.ButtonStyle.success if self.currency == "coins" else discord.ButtonStyle.primary
        btn_currency = discord.ui.Button(label=cur_lbl, style=cur_style, row=1)
        btn_currency.callback = self.btn_currency_callback
        self.add_item(btn_currency)

        # Row 2: Chọn cửa đặt cho game hiện tại
        g_info = GAME_INFO.get(self.game, GAME_INFO["taixiu"])
        if self.game == "baucua":
            options = [
                discord.SelectOption(label="🦌 Nai", value="nai", default=(self.choice == "nai")),
                discord.SelectOption(label="🎃 Bầu", value="bau", default=(self.choice == "bau")),
                discord.SelectOption(label="🐓 Gà", value="ga", default=(self.choice == "ga")),
                discord.SelectOption(label="🐟 Cá", value="ca", default=(self.choice == "ca")),
                discord.SelectOption(label="🦀 Cua", value="cua", default=(self.choice == "cua")),
                discord.SelectOption(label="🦐 Tôm", value="tom", default=(self.choice == "tom")),
            ]
            ph = "Chọn linh vật đặt cược..." if vi else "Choose mascot to bet on..."
            select_baucua = discord.ui.Select(placeholder=ph, options=options, row=2)
            select_baucua.callback = self.make_select_choice_callback()
            self.add_item(select_baucua)
        elif self.game in ("slots", "blackjack"):
            info_lbl = "🎰 Toàn bộ ván chơi (Không cần chọn cửa)" if vi else "🎰 Entire game session (No choice needed)"
            info_btn = discord.ui.Button(label=info_lbl, style=discord.ButtonStyle.secondary, disabled=True, row=2)
            self.add_item(info_btn)
        else:
            raw_choices = g_info.get("choices_vi" if vi else "choices_en", g_info.get("choices", []))
            for item in raw_choices:
                c_id = item[0]
                c_lbl = item[1]
                c_style = item[2] if len(item) > 2 else discord.ButtonStyle.secondary
                is_selected = (self.choice == c_id)
                btn_choice = discord.ui.Button(
                    label=f"{'👉 ' if is_selected else ''}{c_lbl}",
                    style=c_style if is_selected else discord.ButtonStyle.secondary,
                    row=2
                )
                btn_choice.callback = self.make_choice_btn_callback(c_id)
                self.add_item(btn_choice)

        # Row 3: Menu chọn trò chơi khác
        if vi:
            game_options = [
                discord.SelectOption(label="🎲 Tài Xỉu (3 Xúc Xắc)", value="taixiu", description="Xỉu (4-10), Tài (11-17), Bão", default=(self.game == "taixiu")),
                discord.SelectOption(label="🎲 Xóc Đĩa Chẵn Lẻ", value="chanle", description="Đoán tổng nút Chẵn hoặc Lẻ (x1.95)", default=(self.game == "chanle")),
                discord.SelectOption(label="🦀 Bầu Cua Tôm Cá", value="baucua", description="Nai, Bầu, Gà, Cá, Cua, Tôm (x2-x4)", default=(self.game == "baucua")),
                discord.SelectOption(label="🎡 Vòng Quay Đỏ Đen", value="doden", description="Roulette Đỏ, Đen, Số 0 Hoàng Kim", default=(self.game == "doden")),
                discord.SelectOption(label="🪙 Tung Đồng Xu", value="coinflip", description="Ngửa (Heads) hoặc Sấp (Tails) x2", default=(self.game == "coinflip")),
                discord.SelectOption(label="🎰 Máy Xèng Slots 777", value="slots", description="Nổ Hũ Jackpot x20 cực lớn", default=(self.game == "slots")),
                discord.SelectOption(label="🃏 Xì Dách Blackjack", value="blackjack", description="Đấu bài 21 điểm với nhà cái", default=(self.game == "blackjack")),
            ]
            ph_game = "🎮 Đổi Trò Chơi Casino Khác..."
        else:
            game_options = [
                discord.SelectOption(label="🎲 Sic Bo (3 Dice)", value="taixiu", description="Under (4-10), Over (11-17), Triple", default=(self.game == "taixiu")),
                discord.SelectOption(label="🎲 Even / Odd Dice", value="chanle", description="Predict Even or Odd (x1.95)", default=(self.game == "chanle")),
                discord.SelectOption(label="🦀 Bau Cua Mascots", value="baucua", description="Nai, Bầu, Gà, Cá, Cua, Tôm (x2-x4)", default=(self.game == "baucua")),
                discord.SelectOption(label="🎡 Red / Black Roulette", value="doden", description="Roulette Red, Black, Golden Zero", default=(self.game == "doden")),
                discord.SelectOption(label="🪙 Coinflip", value="coinflip", description="Heads or Tails (x2)", default=(self.game == "coinflip")),
                discord.SelectOption(label="🎰 Slots 777", value="slots", description="Mega Jackpot x20 payout", default=(self.game == "slots")),
                discord.SelectOption(label="🃏 Blackjack 21", value="blackjack", description="Blackjack duel against the dealer", default=(self.game == "blackjack")),
            ]
            ph_game = "🎮 Switch Casino Game..."
        select_game = discord.ui.Select(placeholder=ph_game, options=game_options, row=3)
        select_game.callback = self.select_game_callback
        self.add_item(select_game)

        # Row 4: Đặt cược & Hủy
        btn_submit = discord.ui.Button(label="✅ ĐẶT CƯỢC NGAY" if vi else "✅ BET NOW", style=discord.ButtonStyle.success, row=4)
        btn_submit.callback = self.btn_submit_callback
        self.add_item(btn_submit)

        btn_cancel = discord.ui.Button(label="❌ HỦY BỎ" if vi else "❌ CANCEL", style=discord.ButtonStyle.danger, row=4)
        btn_cancel.callback = self.btn_cancel_callback
        self.add_item(btn_cancel)

    def build_embed(self, user_coins: int, user_xu: int) -> discord.Embed:
        vi = is_vietnamese(self.guild_id)
        g_info = GAME_INFO.get(self.game, GAME_INFO["taixiu"])
        c_badge = cur_badge(self.currency)
        g_name = g_info["name_vi"] if vi else g_info["name_en"]
        g_desc = g_info["desc_vi"] if vi else g_info["desc_en"]

        if vi:
            curr_name = "🪙 Coins (Tiền Thường)" if self.currency == "coins" else "💎 Xu (Tiền Cao Cấp)"
        else:
            curr_name = "🪙 Coins (Standard)" if self.currency == "coins" else "💎 Xu (Premium)"

        choice_display = self.choice
        if self.game == "baucua":
            item = BAUCUA_ITEMS.get(self.choice, {})
            choice_display = f"{item.get('emoji', '🎲')} {item.get('name', self.choice)}"
        elif self.game in ("slots", "blackjack"):
            choice_display = "🎰 Cược cả ván" if vi else "🎰 Entire Game"
        else:
            raw_choices = g_info.get("choices_vi" if vi else "choices_en", g_info.get("choices", []))
            for item in raw_choices:
                if len(item) >= 2 and item[0] == self.choice:
                    choice_display = item[1]
                    break

        if vi:
            title_str = f"{g_info['icon']} BẢNG ĐẶT CƯỢC — {g_name.upper()}"
            desc_str = (
                f"Chào {self.author.mention}! Hãy chọn mức cược, loại tiền và cửa đặt bên dưới.\n"
                f"*{g_desc}*\n\n"
                f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
                f"💳 **SỐ DƯ HIỆN TẠI CỦA BẠN:**\n"
                f"• 🪙 **Coins:** `{user_coins:,}`\n"
                f"• 💎 **Xu:** `{user_xu:,}`\n\n"
                f"🎯 **THÔNG TIN PHIẾU CƯỢC:**\n"
                f"• 🎮 **Trò chơi:** **{g_name}**\n"
                f"• 💰 **Mức cược:** `{self.amount:,}` {c_badge}\n"
                f"• 🪙 **Loại tiền tệ:** **{curr_name}**\n"
                f"• 🎲 **Cửa đặt đã chọn:** **{choice_display}**\n"
                f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
                f"👉 *Bấm các nút bên dưới để tùy chỉnh, sau đó bấm **✅ ĐẶT CƯỢC NGAY**!*"
            )
            footer_str = "Sakura Casino • Bấm ✏️ Tùy Chỉnh để nhập số tiền bất kỳ."
        else:
            title_str = f"{g_info['icon']} BETTING TABLE — {g_name.upper()}"
            desc_str = (
                f"Hello {self.author.mention}! Select bet amount, currency and your choice below.\n"
                f"*{g_desc}*\n\n"
                f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
                f"💳 **YOUR CURRENT BALANCE:**\n"
                f"• 🪙 **Coins:** `{user_coins:,}`\n"
                f"• 💎 **Xu:** `{user_xu:,}`\n\n"
                f"🎯 **BET SLIP DETAILS:**\n"
                f"• 🎮 **Game:** **{g_name}**\n"
                f"• 💰 **Bet Amount:** `{self.amount:,}` {c_badge}\n"
                f"• 🪙 **Currency:** **{curr_name}**\n"
                f"• 🎲 **Selected Choice:** **{choice_display}**\n"
                f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
                f"👉 *Click the buttons below to customize, then click **✅ BET NOW**!*"
            )
            footer_str = "Sakura Casino • Click ✏️ Custom to enter any amount."

        embed = discord.Embed(title=title_str, description=desc_str, color=discord.Color.from_rgb(255, 182, 193))
        embed.set_thumbnail(url=self.author.display_avatar.url)
        embed.set_footer(text=footer_str)
        return embed

    async def refresh_view(self, interaction: discord.Interaction):
        coins = await get_user_currency(self.guild_id, self.author.id, "coins")
        xu = await get_user_currency(self.guild_id, self.author.id, "xu")
        self.setup_items()
        embed = self.build_embed(coins, xu)
        await interaction.response.edit_message(embed=embed, view=self)

    def make_add_callback(self, delta: int):
        async def cb(interaction: discord.Interaction):
            self.amount += delta
            await self.refresh_view(interaction)
        return cb

    async def btn_double_callback(self, interaction: discord.Interaction):
        self.amount = max(1000, self.amount * 2)
        await self.refresh_view(interaction)

    async def btn_allin_callback(self, interaction: discord.Interaction):
        bal = await get_user_currency(self.guild_id, self.author.id, self.currency)
        self.amount = max(1, bal)
        await self.refresh_view(interaction)

    async def btn_reset_callback(self, interaction: discord.Interaction):
        self.amount = 1000
        await self.refresh_view(interaction)

    async def btn_currency_callback(self, interaction: discord.Interaction):
        self.currency = "xu" if self.currency == "coins" else "coins"
        await self.refresh_view(interaction)

    def make_choice_btn_callback(self, choice_id: str):
        async def cb(interaction: discord.Interaction):
            self.choice = choice_id
            await self.refresh_view(interaction)
        return cb

    def make_select_choice_callback(self):
        async def cb(interaction: discord.Interaction):
            if interaction.data and "values" in interaction.data and interaction.data["values"]:
                self.choice = interaction.data["values"][0]
            await self.refresh_view(interaction)
        return cb

    async def select_game_callback(self, interaction: discord.Interaction):
        if interaction.data and "values" in interaction.data and interaction.data["values"]:
            new_game = interaction.data["values"][0]
            if new_game in GAME_INFO:
                self.game = new_game
                self.choice = GAME_INFO[new_game]["default_choice"]
        await self.refresh_view(interaction)

    async def btn_custom_callback(self, interaction: discord.Interaction):
        await interaction.response.send_modal(CustomBetModal(self))

    async def btn_cancel_callback(self, interaction: discord.Interaction):
        vi = is_vietnamese(interaction.guild_id)
        embed = discord.Embed(
            title="❌ ĐÃ HỦY ĐẶT CƯỢC" if vi else "❌ BET CANCELLED",
            description=f"{self.author.mention} đã hủy phiên đặt cược. Tiền trong ví của bạn được giữ nguyên an toàn." if vi else f"{self.author.mention} cancelled the bet slip. Your funds remain safe in your wallet.",
            color=discord.Color.dark_grey()
        )
        self.stop()
        await interaction.response.edit_message(embed=embed, view=None)

    async def btn_submit_callback(self, interaction: discord.Interaction):
        if self.author.id in _active_game_users:
            return await interaction.response.send_message("⏳ Bạn đang có 1 ván chơi chưa kết thúc! Hãy đợi một chút.", ephemeral=True)

        if self.amount <= 0:
            return await interaction.response.send_message("❌ Số tiền cược phải lớn hơn 0!", ephemeral=True)

        cur_bal = await get_user_currency(self.guild_id, self.author.id, self.currency)
        if cur_bal < self.amount:
            return await interaction.response.send_message(
                f"❌ Bạn không đủ tiền! Số dư {cur_badge(self.currency)} hiện tại: `{cur_bal:,}`. Vui lòng giảm cược hoặc đổi loại tiền.",
                ephemeral=True
            )

        self.stop()
        if self.game == "taixiu":
            await self.cog.run_taixiu(interaction, self.author, self.guild_id, self.amount, self.choice, self.currency, is_interaction=True)
        elif self.game == "chanle":
            await self.cog.run_chanle(interaction, self.author, self.guild_id, self.amount, self.choice, self.currency, is_interaction=True)
        elif self.game == "doden":
            await self.cog.run_doden(interaction, self.author, self.guild_id, self.amount, self.choice, self.currency, is_interaction=True)
        elif self.game == "coinflip":
            await self.cog.run_coinflip(interaction, self.author, self.guild_id, self.amount, self.choice, self.currency, is_interaction=True)
        elif self.game == "baucua":
            await self.cog.run_baucua(interaction, self.author, self.guild_id, self.amount, self.choice, self.currency, is_interaction=True)
        elif self.game == "slots":
            await self.cog.run_slots(interaction, self.author, self.guild_id, self.amount, self.currency, is_interaction=True)
        elif self.game == "blackjack":
            await self.cog.run_blackjack(interaction, self.author, self.guild_id, self.amount, self.currency, is_interaction=True)


# ================= CASINO COG =================
class CasinoCog(commands.Cog, name="Casino"):
    """Sòng Bạc Mini-Games Cao Cấp với Hoạt Ảnh Chuyển Động & Tiêu Coins/Xu."""

    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.lottery_draw_task.start()

    def cog_unload(self):
        self.lottery_draw_task.cancel()

    # ================= RUNNER METHODS DÙNG CHUNG =================
    async def run_doden(self, target, user, guild_id, amount, choice, currency, is_interaction=False):
        if amount <= 0:
            err = "❌ Số tiền cược phải lớn hơn 0!"
            return await (target.response.send_message(err, ephemeral=True) if is_interaction else target.send(err, ephemeral=True))

        if user.id in _active_game_users:
            err = "⏳ Bạn đang có 1 ván chơi chưa kết thúc! Hãy đợi một chút."
            return await (target.response.send_message(err, ephemeral=True) if is_interaction else target.send(err, ephemeral=True))

        deducted = await deduct_user_currency(guild_id, user.id, currency, amount)
        if not deducted:
            cur_bal = await get_user_currency(guild_id, user.id, currency)
            err = f"❌ Bạn không đủ tiền! Số dư {cur_badge(currency)} hiện tại: `{cur_bal:,}`."
            return await (target.response.send_message(err, ephemeral=True) if is_interaction else target.send(err, ephemeral=True))

        _active_game_users.add(user.id)
        c_badge = cur_badge(currency)
        choice_str = "🔴 ĐỎ" if choice == "red" else ("⚫ ĐEN" if choice == "black" else "🟢 HOÀNG KIM (Số 0)")

        # FRAME 1: Bắt đầu quay
        embed = discord.Embed(
            title="🎡 VÒNG QUAY ĐỎ ĐEN — ĐANG QUAY TỐC ĐỘ CAO...",
            description=(
                f"👤 **Người chơi:** {user.mention}\n"
                f"💰 **Cược:** `{amount:,}` {c_badge} vào **{choice_str}**\n\n"
                f"```css\n"
                f"[  🔴 1  |  ⚫ 4  |  🔴 7  |  🟢 0  |  ⚫ 8  ]\n"
                f"```\n"
                f"🌪️ *Bánh xe Roulette đang quay vèo vèo với tốc độ chóng mặt...*"
            ),
            color=discord.Color.gold()
        )
        if is_interaction:
            await target.response.edit_message(embed=embed, view=None)
            msg = await target.original_response()
        else:
            msg = await target.send(embed=embed)
        await asyncio.sleep(1.0)

        # FRAME 2: Bánh xe chậm dần
        embed.title = "🎡 VÒNG QUAY ĐỎ ĐEN — BÁNH XE ĐANG CHẬM LẠI..."
        embed.description = (
            f"👤 **Người chơi:** {user.mention}\n"
            f"💰 **Cược:** `{amount:,}` {c_badge} vào **{choice_str}**\n\n"
            f"```css\n"
            f"[  ⚫ 8  |  🔴 3  |  ⚫ 2  |  🟢 0  |  🔴 9  ]\n"
            f"```\n"
            f"💨 *Tiếng viên bi kim loại nảy lách cách trên các rãnh số...*"
        )
        embed.color = discord.Color.orange()
        await msg.edit(embed=embed)
        await asyncio.sleep(1.0)

        # FRAME 3: Viên bi chuẩn bị dừng
        embed.title = "🎡 VÒNG QUAY ĐỎ ĐEN — VIÊN BI ĐANG RƠI VÀO RÃNH..."
        embed.description = (
            f"👤 **Người chơi:** {user.mention}\n"
            f"💰 **Cược:** `{amount:,}` {c_badge} vào **{choice_str}**\n\n"
            f"```css\n"
            f"[  🔴 7  |  ⚫ 10  |  🔴 1  |  ⚫ 6  |  🔴 5  ]\n"
            f"```\n"
            f"⏳ *Viên bi chậm lại từng nhịp... Chuẩn bị dừng lại!*"
        )
        embed.color = discord.Color.blue()
        await msg.edit(embed=embed)
        await asyncio.sleep(1.0)

        # FRAME 4: KẾT QUẢ
        _active_game_users.discard(user.id)
        landed_number = random.randint(0, 36)
        if landed_number == 0:
            result_color = "zero"
            res_str = "🟢 SỐ 0 (HOÀNG KIM)"
        elif landed_number % 2 == 1:
            result_color = "red"
            res_str = f"🔴 ĐỎ (Số {landed_number})"
        else:
            result_color = "black"
            res_str = f"⚫ ĐEN (Số {landed_number})"

        is_win = (choice == result_color)
        if is_win:
            multiplier = 14 if choice == "zero" else 2
            win_amount = amount * multiplier
            new_bal = await add_user_currency(guild_id, user.id, currency, win_amount)
            embed.title = "🎉 THẮNG LỚN! VÒNG QUAY ĐỎ ĐEN"
            embed.description = (
                f"👤 **Người chơi:** {user.mention}\n\n"
                f"🎯 **Viên bi dừng lại ở:** **{res_str}**\n"
                f"✨ **Lựa chọn của bạn:** **{choice_str}**\n\n"
                f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
                f"🏆 **Chiến thắng vẻ vang!** Bạn nhận: **`+{win_amount:,}` {c_badge}** (x{multiplier})\n"
                f"💳 **Số dư mới:** `{new_bal:,}` {c_badge}"
            )
            embed.color = discord.Color.green()
        else:
            new_bal = await get_user_currency(guild_id, user.id, currency)
            embed.title = "💀 THẤT BẠI! VÒNG QUAY ĐỎ ĐEN"
            embed.description = (
                f"👤 **Người chơi:** {user.mention}\n\n"
                f"🎯 **Viên bi dừng lại ở:** **{res_str}**\n"
                f"✨ **Lựa chọn của bạn:** **{choice_str}**\n\n"
                f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
                f"😢 **Bạn đã thua:** `-`**`{amount:,}` {c_badge}**\n"
                f"💳 **Số dư còn lại:** `{new_bal:,}` {c_badge}\n"
                f"💪 *Chúc bạn may mắn hơn ở vòng quay kế tiếp!*"
            )
            embed.color = discord.Color.red()

        await msg.edit(embed=embed)

    async def run_chanle(self, target, user, guild_id, amount, choice, currency, is_interaction=False):
        if amount <= 0:
            err = "❌ Số tiền cược phải lớn hơn 0!"
            return await (target.response.send_message(err, ephemeral=True) if is_interaction else target.send(err, ephemeral=True))

        if user.id in _active_game_users:
            err = "⏳ Bạn đang có 1 ván chơi chưa kết thúc! Hãy đợi một chút."
            return await (target.response.send_message(err, ephemeral=True) if is_interaction else target.send(err, ephemeral=True))

        deducted = await deduct_user_currency(guild_id, user.id, currency, amount)
        if not deducted:
            cur_bal = await get_user_currency(guild_id, user.id, currency)
            err = f"❌ Bạn không đủ tiền! Số dư {cur_badge(currency)} hiện tại: `{cur_bal:,}`."
            return await (target.response.send_message(err, ephemeral=True) if is_interaction else target.send(err, ephemeral=True))

        _active_game_users.add(user.id)
        c_badge = cur_badge(currency)
        choice_str = "🔵 CHẴN" if choice == "chan" else "🔴 LẺ"

        # FRAME 1: Úp bát
        embed = discord.Embed(
            title="🥣 BÀN XÓC ĐĨA CHẴN LẺ — ĐANG ÚP BÁT LẮC...",
            description=(
                f"👤 **Người chơi:** {user.mention}\n"
                f"💰 **Cược:** `{amount:,}` {c_badge} vào **{choice_str}**\n\n"
                f"```css\n"
                f"[ 🌪️ ÚP BÁT... CẠCH! CẠCH! CẠCH! ]\n"
                f"```\n"
                f"🎲 *Bát đĩa đang được lắc thật đều tay...*"
            ),
            color=discord.Color.purple()
        )
        if is_interaction:
            await target.response.edit_message(embed=embed, view=None)
            msg = await target.original_response()
        else:
            msg = await target.send(embed=embed)
        await asyncio.sleep(0.9)

        # FRAME 2: Rung lắc mạnh
        embed.title = "🥣 BÀN XÓC ĐĨA CHẴN LẺ — BÁT ĐANG RUNG LÊN BẦN BẬT..."
        embed.description = (
            f"👤 **Người chơi:** {user.mention}\n"
            f"💰 **Cược:** `{amount:,}` {c_badge} vào **{choice_str}**\n\n"
            f"```css\n"
            f"[ 💨 LẮC MẠNH TAY... LÁCH CÁCH... XỐC XỐC! ]\n"
            f"```\n"
            f"🌪️ *Tiếng các hạt xí ngầu va đập chan chát vào lòng bát sứ!*"
        )
        await msg.edit(embed=embed)
        await asyncio.sleep(0.9)

        # FRAME 3: Đặt xuống chờ mở
        embed.title = "🥣 BÀN XÓC ĐĨA CHẴN LẺ — CHUẨN BỊ MỞ BÁT!"
        embed.description = (
            f"👤 **Người chơi:** {user.mention}\n"
            f"💰 **Cược:** `{amount:,}` {c_badge} vào **{choice_str}**\n\n"
            f"```css\n"
            f"[ ✨ ĐẶT BÁT XUỐNG BÀN... MỞ BÁT! ]\n"
            f"```\n"
            f"✋ *Nhà cái từ từ nhấc bát lên...*"
        )
        await msg.edit(embed=embed)
        await asyncio.sleep(0.9)

        # FRAME 4: KẾT QUẢ
        _active_game_users.discard(user.id)
        d1 = random.randint(1, 6)
        d2 = random.randint(1, 6)
        total = d1 + d2
        result_type = "chan" if (total % 2 == 0) else "le"
        res_str = f"🔵 CHẴN ({total} điểm)" if result_type == "chan" else f"🔴 LẺ ({total} điểm)"

        is_win = (choice == result_type)
        if is_win:
            win_amount = int(amount * 1.95)
            new_bal = await add_user_currency(guild_id, user.id, currency, win_amount)
            embed.title = "🎉 ĐOÁN ĐÚNG! BẠN ĐÃ THẮNG CHẴN LẺ"
            embed.description = (
                f"👤 **Người chơi:** {user.mention}\n\n"
                f"🎲 **Xúc xắc:** {DICE_EMOJIS[d1]} ({d1}) + {DICE_EMOJIS[d2]} ({d2}) = **{total}**\n"
                f"🎯 **Kết quả:** **{res_str}**\n"
                f"✨ **Bạn chọn:** **{choice_str}**\n\n"
                f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
                f"🏆 **Thưởng nóng:** **`+{win_amount:,}` {c_badge}**\n"
                f"💳 **Số dư mới:** `{new_bal:,}` {c_badge}"
            )
            embed.color = discord.Color.green()
        else:
            cur_bal = await get_user_currency(guild_id, user.id, currency)
            embed.title = "💀 ĐOÁN SAI! THUA CUỘC CHẴN LẺ"
            embed.description = (
                f"👤 **Người chơi:** {user.mention}\n\n"
                f"🎲 **Xúc xắc:** {DICE_EMOJIS[d1]} ({d1}) + {DICE_EMOJIS[d2]} ({d2}) = **{total}**\n"
                f"🎯 **Kết quả:** **{res_str}**\n"
                f"❌ **Bạn chọn:** **{choice_str}**\n\n"
                f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
                f"🥀 **Mất cược:** **`-{amount:,}` {c_badge}**\n"
                f"💳 **Số dư còn lại:** `{cur_bal:,}` {c_badge}"
            )
            embed.color = discord.Color.red()

        await msg.edit(embed=embed)

    async def run_taixiu(self, target, user, guild_id, amount, choice, currency, is_interaction=False):
        if amount <= 0:
            err = "❌ Số tiền cược phải lớn hơn 0!"
            return await (target.response.send_message(err, ephemeral=True) if is_interaction else target.send(err, ephemeral=True))

        if user.id in _active_game_users:
            err = "⏳ Bạn đang có 1 ván chơi chưa kết thúc! Hãy đợi một chút."
            return await (target.response.send_message(err, ephemeral=True) if is_interaction else target.send(err, ephemeral=True))

        deducted = await deduct_user_currency(guild_id, user.id, currency, amount)
        if not deducted:
            cur_bal = await get_user_currency(guild_id, user.id, currency)
            err = f"❌ Bạn không đủ tiền! Số dư {cur_badge(currency)} hiện tại: `{cur_bal:,}`."
            return await (target.response.send_message(err, ephemeral=True) if is_interaction else target.send(err, ephemeral=True))

        _active_game_users.add(user.id)
        c_badge = cur_badge(currency)
        choice_str = "🔴 TÀI (11 - 17)" if choice == "tai" else ("🔵 XỈU (4 - 10)" if choice == "xiu" else "👑 BÃO (3 MẶT GIỐNG NHAU x30)")

        # FRAME 1: Lắc hộp xúc xắc
        embed = discord.Embed(
            title="🎲 TÀI XỈU SIC BO — ĐANG LẮC HỘP XÍ NGẦU...",
            description=(
                f"👤 **Người chơi:** {user.mention}\n"
                f"💰 **Cược:** `{amount:,}` {c_badge} vào **{choice_str}**\n\n"
                f"```css\n"
                f"[ 🎲 🎲 🎲  ĐANG LẮC MẠNH TRONG HỘP THỦY TINH... ]\n"
                f"```\n"
                f"🌪️ *Ba viên xúc xắc đang xoay tít mù...*"
            ),
            color=discord.Color.dark_gold()
        )
        if is_interaction:
            await target.response.edit_message(embed=embed, view=None)
            msg = await target.original_response()
        else:
            msg = await target.send(embed=embed)
        await asyncio.sleep(1.0)

        # FRAME 2: Lăn trên bàn
        embed.title = "🎲 TÀI XỈU SIC BO — XÚC XẮC LĂN LÔNG LỐC TRÊN BÀN..."
        embed.description = (
            f"👤 **Người chơi:** {user.mention}\n"
            f"💰 **Cược:** `{amount:,}` {c_badge} vào **{choice_str}**\n\n"
            f"```css\n"
            f"[ 🔄 🔄 🔄  LĂN TRÊN ĐĨA... TIẾNG VA ĐẬP LÁCH CÁCH... ]\n"
            f"```\n"
            f"💨 *Hồi hộp nín thở theo từng vòng lăn của xí ngầu...*"
        )
        await msg.edit(embed=embed)
        await asyncio.sleep(1.0)

        # FRAME 3: Kết quả
        _active_game_users.discard(user.id)
        d1 = random.randint(1, 6)
        d2 = random.randint(1, 6)
        d3 = random.randint(1, 6)
        total = d1 + d2 + d3
        is_bao = (d1 == d2 == d3)

        if is_bao:
            res_type = "bao"
            res_str = f"👑 BÃO {d1}-{d2}-{d3} ({total} Điểm)"
        elif total >= 11:
            res_type = "tai"
            res_str = f"🔴 TÀI ({total} Điểm)"
        else:
            res_type = "xiu"
            res_str = f"🔵 XỈU ({total} Điểm)"

        is_win = (choice == res_type)
        if is_win:
            multiplier = 30 if choice == "bao" else 2
            win_amount = amount * multiplier
            new_bal = await add_user_currency(guild_id, user.id, currency, win_amount)
            embed.title = "🎉 CHIẾN THẮNG RỰC RỠ! TÀI XỈU SIC BO"
            embed.description = (
                f"👤 **Người chơi:** {user.mention}\n\n"
                f"🎲 **Xúc xắc:** {DICE_EMOJIS[d1]} ({d1}) + {DICE_EMOJIS[d2]} ({d2}) + {DICE_EMOJIS[d3]} ({d3}) = **{total}**\n"
                f"🎯 **Kết quả:** **{res_str}**\n"
                f"✨ **Bạn chọn:** **{choice_str}**\n\n"
                f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
                f"🏆 **Thưởng lớn:** **`+{win_amount:,}` {c_badge}** (x{multiplier})\n"
                f"💳 **Số dư mới:** `{new_bal:,}` {c_badge}"
            )
            embed.color = discord.Color.green()
        else:
            cur_bal = await get_user_currency(guild_id, user.id, currency)
            embed.title = "💀 THUA CUỘC! TÀI XỈU SIC BO"
            embed.description = (
                f"👤 **Người chơi:** {user.mention}\n\n"
                f"🎲 **Xúc xắc:** {DICE_EMOJIS[d1]} ({d1}) + {DICE_EMOJIS[d2]} ({d2}) + {DICE_EMOJIS[d3]} ({d3}) = **{total}**\n"
                f"🎯 **Kết quả:** **{res_str}**\n"
                f"❌ **Bạn chọn:** **{choice_str}**\n\n"
                f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
                f"🥀 **Mất cược:** **`-{amount:,}` {c_badge}**\n"
                f"💳 **Số dư còn lại:** `{cur_bal:,}` {c_badge}"
            )
            embed.color = discord.Color.red()

        await msg.edit(embed=embed)

    async def run_slots(self, target, user, guild_id, amount, currency, is_interaction=False):
        if amount <= 0:
            err = "❌ Số tiền cược phải lớn hơn 0!"
            return await (target.response.send_message(err, ephemeral=True) if is_interaction else target.send(err, ephemeral=True))

        if user.id in _active_game_users:
            err = "⏳ Bạn đang có 1 ván chơi chưa kết thúc! Hãy đợi một chút."
            return await (target.response.send_message(err, ephemeral=True) if is_interaction else target.send(err, ephemeral=True))

        deducted = await deduct_user_currency(guild_id, user.id, currency, amount)
        if not deducted:
            cur_bal = await get_user_currency(guild_id, user.id, currency)
            err = f"❌ Bạn không đủ tiền! Số dư {cur_badge(currency)} hiện tại: `{cur_bal:,}`."
            return await (target.response.send_message(err, ephemeral=True) if is_interaction else target.send(err, ephemeral=True))

        _active_game_users.add(user.id)
        c_badge = cur_badge(currency)

        # FRAME 1: Cần gạt kéo, 3 guồng quay
        embed = discord.Embed(
            title="🎰 MÁY XÈNG SAKURA SLOTS — CẦN GẠT ĐÃ KÉO!",
            description=(
                f"👤 **Người chơi:** {user.mention}\n"
                f"💰 **Cược:** `{amount:,}` {c_badge}\n\n"
                f"```\n"
                f"┏━━━━━━━━━━━┓\n"
                f"┃ 🌀 ┃ 🌀 ┃ 🌀 ┃\n"
                f"┗━━━━━━━━━━━┛\n"
                f"```\n"
                f"🕹️ *Cả 3 guồng quay đang xoay tít mù với tốc độ cực đại...*"
            ),
            color=discord.Color.blue()
        )
        if is_interaction:
            await target.response.edit_message(embed=embed, view=None)
            msg = await target.original_response()
        else:
            msg = await target.send(embed=embed)
        await asyncio.sleep(0.9)

        # FRAME 2: Guồng 1 dừng
        s1 = random.choice(SLOT_SYMBOLS)
        embed.title = "🎰 MÁY XÈNG SAKURA SLOTS — GUỒNG 1 ĐÃ DỪNG!"
        embed.description = (
            f"👤 **Người chơi:** {user.mention}\n"
            f"💰 **Cược:** `{amount:,}` {c_badge}\n\n"
            f"```\n"
            f"┏━━━━━━━━━━━┓\n"
            f"┃ {s1} ┃ 🌀 ┃ 🌀 ┃\n"
            f"┗━━━━━━━━━━━┛\n"
            f"```\n"
            f"✅ *Guồng 1 đã dừng! Guồng 2 và 3 đang xoay nhanh...*"
        )
        await msg.edit(embed=embed)
        await asyncio.sleep(0.9)

        # FRAME 3: Guồng 2 dừng
        s2 = random.choice(SLOT_SYMBOLS)
        embed.title = "🎰 MÁY XÈNG SAKURA SLOTS — GUỒNG 2 ĐÃ DỪNG!"
        embed.description = (
            f"👤 **Người chơi:** {user.mention}\n"
            f"💰 **Cược:** `{amount:,}` {c_badge}\n\n"
            f"```\n"
            f"┏━━━━━━━━━━━┓\n"
            f"┃ {s1} ┃ {s2} ┃ 🌀 ┃\n"
            f"┗━━━━━━━━━━━┛\n"
            f"```\n"
            f"🔥 *Guồng 2 đã khóa! Hồi hộp nín thở chờ kết quả guồng 3...*"
        )
        await msg.edit(embed=embed)
        await asyncio.sleep(0.9)

        # FRAME 4: Guồng 3 dừng & Kết quả
        _active_game_users.discard(user.id)
        s3 = random.choice(SLOT_SYMBOLS)

        # Multipliers
        multiplier = 0
        payout_name = ""
        if s1 == s2 == s3:
            if s1 == "7️⃣":
                multiplier = 20
                payout_name = "🔥 SIÊU NỔ HŨ JACKPOT 777! (x20)"
            elif s1 == "💎":
                multiplier = 15
                payout_name = "💎 ĐẠI PHÚ QUÝ KIM CƯƠNG! (x15)"
            elif s1 == "🔔":
                multiplier = 10
                payout_name = "🔔 CHUÔNG VÀNG TÀI LỘC! (x10)"
            elif s1 == "🍒":
                multiplier = 7
                payout_name = "🍒 BA QUẢ CHERRY MAY MẮN! (x7)"
            else:
                multiplier = 5
                payout_name = "🍇 TRÁI CÂY TRÚNG LỚN! (x5)"
        elif s1 == s2 or s2 == s3 or s1 == s3:
            multiplier = 2
            payout_name = "✨ HAI BIỂU TƯỢNG TRÙNG NHAU! (x2)"

        if multiplier > 0:
            win_amount = amount * multiplier
            new_bal = await add_user_currency(guild_id, user.id, currency, win_amount)
            embed.title = "🎉 THẮNG LỚN! MÁY XÈNG SAKURA SLOTS"
            embed.description = (
                f"👤 **Người chơi:** {user.mention}\n\n"
                f"```\n"
                f"┏━━━━━━━━━━━┓\n"
                f"┃ {s1} ┃ {s2} ┃ {s3} ┃\n"
                f"┗━━━━━━━━━━━┛\n"
                f"```\n"
                f"🎯 **Giải thưởng:** **{payout_name}**\n\n"
                f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
                f"🏆 **Nhận thưởng:** **`+{win_amount:,}` {c_badge}**\n"
                f"💳 **Số dư mới:** `{new_bal:,}` {c_badge}"
            )
            embed.color = discord.Color.green()
        else:
            cur_bal = await get_user_currency(guild_id, user.id, currency)
            embed.title = "💀 HỤT RỒI! MÁY XÈNG SAKURA SLOTS"
            embed.description = (
                f"👤 **Người chơi:** {user.mention}\n\n"
                f"```\n"
                f"┏━━━━━━━━━━━┓\n"
                f"┃ {s1} ┃ {s2} ┃ {s3} ┃\n"
                f"┗━━━━━━━━━━━┛\n"
                f"```\n"
                f"❌ **Không khớp biểu tượng nào.**\n\n"
                f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
                f"🥀 **Mất cược:** **`-{amount:,}` {c_badge}**\n"
                f"💳 **Số dư còn lại:** `{cur_bal:,}` {c_badge}"
            )
            embed.color = discord.Color.red()

        await msg.edit(embed=embed)

    async def run_baucua(self, target, user, guild_id, amount, choice, currency, is_interaction=False):
        if amount <= 0:
            err = "❌ Số tiền cược phải lớn hơn 0!"
            return await (target.response.send_message(err, ephemeral=True) if is_interaction else target.send(err, ephemeral=True))

        if user.id in _active_game_users:
            err = "⏳ Bạn đang có 1 ván chơi chưa kết thúc! Hãy đợi một chút."
            return await (target.response.send_message(err, ephemeral=True) if is_interaction else target.send(err, ephemeral=True))

        deducted = await deduct_user_currency(guild_id, user.id, currency, amount)
        if not deducted:
            cur_bal = await get_user_currency(guild_id, user.id, currency)
            err = f"❌ Bạn không đủ tiền! Số dư {cur_badge(currency)} hiện tại: `{cur_bal:,}`."
            return await (target.response.send_message(err, ephemeral=True) if is_interaction else target.send(err, ephemeral=True))

        _active_game_users.add(user.id)
        c_badge = cur_badge(currency)
        chosen_info = BAUCUA_ITEMS.get(choice, {"name": choice, "emoji": "🎲"})
        choice_str = f"{chosen_info['emoji']} {chosen_info['name']}"

        # FRAME 1: Úp đĩa lắc
        embed = discord.Embed(
            title="🎋 BẦU CUA TÔM CÁ — ĐANG ÚP ĐĨA LẮC HỘT...",
            description=(
                f"👤 **Người chơi:** {user.mention}\n"
                f"💰 **Cược:** `{amount:,}` {c_badge} vào **{choice_str}**\n\n"
                f"```css\n"
                f"[ 🌪️ ÚP ĐĨA... CẠCH CẠCH CẠCH... ]\n"
                f"```\n"
                f"🎋 *Tiếng 3 hột bầu cua chạm lách cách trong đĩa gỗ...*"
            ),
            color=discord.Color.teal()
        )
        if is_interaction:
            await target.response.edit_message(embed=embed, view=None)
            msg = await target.original_response()
        else:
            msg = await target.send(embed=embed)
        await asyncio.sleep(1.0)

        # FRAME 2: Rung lắc đĩa
        embed.title = "🎋 BẦU CUA TÔM CÁ — ĐANG RUNG LẮC MẠNH TAY..."
        embed.description = (
            f"👤 **Người chơi:** {user.mention}\n"
            f"💰 **Cược:** `{amount:,}` {c_badge} vào **{choice_str}**\n\n"
            f"```css\n"
            f"[ 💨 RUNG LẮC ĐỀU TAY... ĐẶT ĐĨA XUỐNG BÀN! ]\n"
            f"```\n"
            f"✨ *Chuẩn bị mở đĩa xem 3 linh vật may mắn!*"
        )
        await msg.edit(embed=embed)
        await asyncio.sleep(1.0)

        # FRAME 3: Mở đĩa & Kết quả
        _active_game_users.discard(user.id)
        keys = list(BAUCUA_ITEMS.keys())
        r1, r2, r3 = random.choice(keys), random.choice(keys), random.choice(keys)
        results = [r1, r2, r3]
        match_count = results.count(choice)

        res_emojis = f"{BAUCUA_ITEMS[r1]['emoji']} {BAUCUA_ITEMS[r1]['name']} • {BAUCUA_ITEMS[r2]['emoji']} {BAUCUA_ITEMS[r2]['name']} • {BAUCUA_ITEMS[r3]['emoji']} {BAUCUA_ITEMS[r3]['name']}"

        if match_count > 0:
            multiplier = match_count + 1
            win_amount = amount * multiplier
            new_bal = await add_user_currency(guild_id, user.id, currency, win_amount)
            embed.title = f"🎉 TRÚNG LỚN! BẦU CUA RA {match_count} MẶT"
            embed.description = (
                f"👤 **Người chơi:** {user.mention}\n\n"
                f"🎋 **Kết quả đĩa:**\n**{res_emojis}**\n\n"
                f"🎯 **Bạn cược:** **{choice_str}**\n"
                f"✨ **Xuất hiện:** `{match_count}` lần!\n\n"
                f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
                f"🏆 **Thắng lớn:** **`+{win_amount:,}` {c_badge}** (x{multiplier})\n"
                f"💳 **Số dư mới:** `{new_bal:,}` {c_badge}"
            )
            embed.color = discord.Color.green()
        else:
            cur_bal = await get_user_currency(guild_id, user.id, currency)
            embed.title = "💀 KHÔNG TRÚNG! BẦU CUA TÔM CÁ"
            embed.description = (
                f"👤 **Người chơi:** {user.mention}\n\n"
                f"🎋 **Kết quả đĩa:**\n**{res_emojis}**\n\n"
                f"❌ **Bạn cược:** **{choice_str}** (Không xuất hiện mặt nào)\n\n"
                f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
                f"🥀 **Mất cược:** **`-{amount:,}` {c_badge}**\n"
                f"💳 **Số dư còn lại:** `{cur_bal:,}` {c_badge}"
            )
            embed.color = discord.Color.red()

        await msg.edit(embed=embed)

    async def run_coinflip(self, target, user, guild_id, amount, choice, currency, is_interaction=False):
        if amount <= 0:
            err = "❌ Số tiền cược phải lớn hơn 0!"
            return await (target.response.send_message(err, ephemeral=True) if is_interaction else target.send(err, ephemeral=True))

        if user.id in _active_game_users:
            err = "⏳ Bạn đang có 1 ván chơi chưa kết thúc! Hãy đợi một chút."
            return await (target.response.send_message(err, ephemeral=True) if is_interaction else target.send(err, ephemeral=True))

        deducted = await deduct_user_currency(guild_id, user.id, currency, amount)
        if not deducted:
            cur_bal = await get_user_currency(guild_id, user.id, currency)
            err = f"❌ Bạn không đủ tiền! Số dư {cur_badge(currency)} hiện tại: `{cur_bal:,}`."
            return await (target.response.send_message(err, ephemeral=True) if is_interaction else target.send(err, ephemeral=True))

        _active_game_users.add(user.id)
        c_badge = cur_badge(currency)
        choice_str = "🪙 NGỬA (Heads)" if choice == "heads" else "🪙 SẤP (Tails)"

        # FRAME 1: Búng đồng xu
        embed = discord.Embed(
            title="🪙 TUNG ĐỒNG XU — ĐANG BÚNG LÊN KHÔNG TRUNG...",
            description=(
                f"👤 **Người chơi:** {user.mention}\n"
                f"💰 **Cược:** `{amount:,}` {c_badge} vào **{choice_str}**\n\n"
                f"```\n"
                f"   [ 🪙 BÚNG TÍT LÊN CAO... 🌪️ ]\n"
                f"```\n"
                f"🔄 *Đồng xu đang xoay tròn giữa không trung...*"
            ),
            color=discord.Color.gold()
        )
        if is_interaction:
            await target.response.edit_message(embed=embed, view=None)
            msg = await target.original_response()
        else:
            msg = await target.send(embed=embed)
        await asyncio.sleep(0.9)

        # FRAME 2: Rơi xuống tay
        embed.title = "🪙 TUNG ĐỒNG XU — ĐỒNG XU RƠI XUỐNG..."
        embed.description = (
            f"👤 **Người chơi:** {user.mention}\n"
            f"💰 **Cược:** `{amount:,}` {c_badge} vào **{choice_str}**\n\n"
            f"```\n"
            f"   [ 💨 RƠI XUỐNG LÒNG BÀN TAY... CHỤP! ]\n"
            f"```\n"
            f"✋ *Bàn tay từ từ hé mở...*"
        )
        await msg.edit(embed=embed)
        await asyncio.sleep(0.9)

        # FRAME 3: Kết quả
        _active_game_users.discard(user.id)
        result = random.choice(["heads", "tails"])
        res_str = "🪙 NGỬA (Heads)" if result == "heads" else "🪙 SẤP (Tails)"

        if choice == result:
            win_amt = amount * 2
            new_bal = await add_user_currency(guild_id, user.id, currency, win_amt)
            embed.title = "🎉 THẮNG LỚN! TUNG ĐỒNG XU"
            embed.description = (
                f"👤 **Người chơi:** {user.mention}\n\n"
                f"🎯 **Đồng xu rơi vào mặt:** **{res_str}**\n"
                f"✨ **Bạn chọn:** **{choice_str}**\n\n"
                f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
                f"🏆 **Chiến thắng:** **`+{win_amt:,}` {c_badge}**\n"
                f"💳 **Số dư mới:** `{new_bal:,}` {c_badge}"
            )
            embed.color = discord.Color.green()
        else:
            cur_bal = await get_user_currency(guild_id, user.id, currency)
            embed.title = "💀 THUA CUỘC! TUNG ĐỒNG XU"
            embed.description = (
                f"👤 **Người chơi:** {user.mention}\n\n"
                f"🎯 **Đồng xu rơi vào mặt:** **{res_str}**\n"
                f"❌ **Bạn chọn:** **{choice_str}**\n\n"
                f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
                f"🥀 **Mất cược:** **`-{amount:,}` {c_badge}**\n"
                f"💳 **Số dư còn lại:** `{cur_bal:,}` {c_badge}"
            )
            embed.color = discord.Color.red()

        await msg.edit(embed=embed)

    async def run_blackjack(self, target, user, guild_id, amount, currency, is_interaction=False):
        if amount <= 0:
            err = "❌ Tiền cược phải lớn hơn 0!"
            return await (target.response.send_message(err, ephemeral=True) if is_interaction else target.send(err, ephemeral=True))

        if user.id in _active_game_users:
            err = "⏳ Bạn đang có 1 ván chơi chưa kết thúc! Hãy đợi một chút."
            return await (target.response.send_message(err, ephemeral=True) if is_interaction else target.send(err, ephemeral=True))

        deducted = await deduct_user_currency(guild_id, user.id, currency, amount)
        if not deducted:
            cur_bal = await get_user_currency(guild_id, user.id, currency)
            err = f"❌ Bạn không đủ tiền! Số dư {cur_badge(currency)} hiện tại: `{cur_bal:,}`."
            return await (target.response.send_message(err, ephemeral=True) if is_interaction else target.send(err, ephemeral=True))

        _active_game_users.add(user.id)
        view = BlackjackView(user, amount, currency)
        embed = view.build_embed(hide_dealer=True)
        if is_interaction:
            await target.response.edit_message(embed=embed, view=view)
        else:
            await target.send(embed=embed, view=view)

    # ================= GAME 1: ĐỎ ĐEN (ROULETTE WHEEL) =================
    @commands.command(name="doden", aliases=["redblack", "roulette"], description="🎡 Đặt cược Đỏ Đen vòng quay Roulette hoạt ảnh sống động.")
    @commands.guild_only()
    async def doden(
        self,
        ctx: commands.Context,
        amount: Optional[int] = None,
        choice: Optional[str] = None,
        currency: str = "coins"
    ):
        if amount is None or choice is None:
            view = CasinoBetView(self, ctx.author, ctx.guild.id, game="doden", amount=1000, currency=currency, choice=choice or "red")
            coins = await get_user_currency(ctx.guild.id, ctx.author.id, "coins")
            xu = await get_user_currency(ctx.guild.id, ctx.author.id, "xu")
            msg = await ctx.send(embed=view.build_embed(coins, xu), view=view)
            view.message = msg
            return

        await self.run_doden(ctx, ctx.author, ctx.guild.id, amount, choice, currency, is_interaction=False)

    # ================= GAME 2: XÓC ĐĨA CHẴN LẺ =================
    @commands.command(name="chanle", aliases=["cl", "xocdia"], description="🥣 Lắc đĩa Chẵn Lẻ hoạt ảnh mở bát giật gân.")
    @commands.guild_only()
    async def chanle(
        self,
        ctx: commands.Context,
        amount: Optional[int] = None,
        choice: Optional[str] = None,
        currency: str = "coins"
    ):
        if amount is None or choice is None:
            view = CasinoBetView(self, ctx.author, ctx.guild.id, game="chanle", amount=1000, currency=currency, choice=choice or "chan")
            coins = await get_user_currency(ctx.guild.id, ctx.author.id, "coins")
            xu = await get_user_currency(ctx.guild.id, ctx.author.id, "xu")
            msg = await ctx.send(embed=view.build_embed(coins, xu), view=view)
            view.message = msg
            return

        await self.run_chanle(ctx, ctx.author, ctx.guild.id, amount, choice, currency, is_interaction=False)

    # ================= GAME 3: TÀI XỈU (SIC BO) =================
    @commands.command(name="taixiu", aliases=["tx", "sicbo"], description="⚖️ Chơi Tài Xỉu 3 viên xúc xắc chuyển động hồi hộp kịch tính.")
    @commands.guild_only()
    async def taixiu(
        self,
        ctx: commands.Context,
        amount: Optional[int] = None,
        choice: Optional[str] = None,
        currency: str = "coins"
    ):
        if amount is None or choice is None:
            view = CasinoBetView(self, ctx.author, ctx.guild.id, game="taixiu", amount=1000, currency=currency, choice=choice or "tai")
            coins = await get_user_currency(ctx.guild.id, ctx.author.id, "coins")
            xu = await get_user_currency(ctx.guild.id, ctx.author.id, "xu")
            msg = await ctx.send(embed=view.build_embed(coins, xu), view=view)
            view.message = msg
            return

        await self.run_taixiu(ctx, ctx.author, ctx.guild.id, amount, choice, currency, is_interaction=False)

    # ================= GAME 4: MÁY XÈNG SLOTS (777 / NỔ HŨ) =================
    @commands.command(name="slots", aliases=["slot", "jackpot"], description="🎰 Quay máy xèng Slots 777 với hoạt ảnh guồng quay nổ hũ sống động.")
    @commands.guild_only()
    async def slots(
        self,
        ctx: commands.Context,
        amount: Optional[int] = None,
        currency: str = "coins"
    ):
        if amount is None:
            view = CasinoBetView(self, ctx.author, ctx.guild.id, game="slots", amount=1000, currency=currency)
            coins = await get_user_currency(ctx.guild.id, ctx.author.id, "coins")
            xu = await get_user_currency(ctx.guild.id, ctx.author.id, "xu")
            msg = await ctx.send(embed=view.build_embed(coins, xu), view=view)
            view.message = msg
            return

        await self.run_slots(ctx, ctx.author, ctx.guild.id, amount, currency, is_interaction=False)

    # ================= GAME 5: BẦU CUA TÔM CÁ =================
    @commands.command(name="baucua", description="🦀 Lắc Bầu Cua Tôm Cá dân gian với hoạt ảnh mở đĩa hồi hộp.")
    @commands.guild_only()
    async def baucua(
        self,
        ctx: commands.Context,
        amount: Optional[int] = None,
        choice: Optional[str] = None,
        currency: str = "coins"
    ):
        if amount is None or choice is None:
            view = CasinoBetView(self, ctx.author, ctx.guild.id, game="baucua", amount=1000, currency=currency, choice=choice or "bau")
            coins = await get_user_currency(ctx.guild.id, ctx.author.id, "coins")
            xu = await get_user_currency(ctx.guild.id, ctx.author.id, "xu")
            msg = await ctx.send(embed=view.build_embed(coins, xu), view=view)
            view.message = msg
            return

        await self.run_baucua(ctx, ctx.author, ctx.guild.id, amount, choice, currency, is_interaction=False)

    # ================= GAME 6: TUNG ĐỒNG XU (COINFLIP) =================
    @commands.command(name="coinflip", aliases=["cf"], description="🎲 Thử vận may tung đồng xu 50/50 hoạt ảnh chuyển động.")
    @commands.guild_only()
    async def coinflip(
        self,
        ctx: commands.Context,
        amount: Optional[int] = None,
        choice: Optional[str] = None,
        currency: str = "coins"
    ):
        if amount is None or choice is None:
            view = CasinoBetView(self, ctx.author, ctx.guild.id, game="coinflip", amount=1000, currency=currency, choice=choice or "heads")
            coins = await get_user_currency(ctx.guild.id, ctx.author.id, "coins")
            xu = await get_user_currency(ctx.guild.id, ctx.author.id, "xu")
            msg = await ctx.send(embed=view.build_embed(coins, xu), view=view)
            view.message = msg
            return

        await self.run_coinflip(ctx, ctx.author, ctx.guild.id, amount, choice, currency, is_interaction=False)

    # ================= GAME 7: BLACKJACK (XÌ DÁCH) =================
    @commands.command(name="blackjack", aliases=["bj"], description="🃏 Chơi bài Xì Dách 21 điểm với Nhà Cái (hỗ trợ Coins hoặc Xu).")
    @commands.guild_only()
    async def blackjack(
        self,
        ctx: commands.Context,
        amount: Optional[int] = None,
        currency: str = "coins"
    ):
        if amount is None:
            view = CasinoBetView(self, ctx.author, ctx.guild.id, game="blackjack", amount=1000, currency=currency)
            coins = await get_user_currency(ctx.guild.id, ctx.author.id, "coins")
            xu = await get_user_currency(ctx.guild.id, ctx.author.id, "xu")
            msg = await ctx.send(embed=view.build_embed(coins, xu), view=view)
            view.message = msg
            return

        await self.run_blackjack(ctx, ctx.author, ctx.guild.id, amount, currency, is_interaction=False)

    # ================= GAME 8: XỔ SỐ JACKPOT =================
    @commands.hybrid_group(name="lottery", fallback="view", description="🎟️ Mua vé số và tham gia giải Jackpot máy chủ.")
    @commands.guild_only()
    async def lottery(self, ctx: commands.Context):
        async with aiosqlite.connect(DB_PATH) as db:
            async with db.execute("SELECT SUM(ticket_count) FROM lottery WHERE guild_id = ?", (str(ctx.guild.id),)) as cur:
                res = await cur.fetchone()
                total_tickets = res[0] or 0

        jackpot = total_tickets * 10000
        embed = discord.Embed(title=f"🎟️ HŨ VÉ SỐ JACKPOT — {ctx.guild.name.upper()}", color=discord.Color.gold())
        embed.add_field(name="💰 Tổng Giá Trị Hũ Thưởng", value=f"**`{jackpot:,}` coin**", inline=False)
        embed.add_field(name="📊 Tổng Số Vé Đã Bán", value=f"`{total_tickets:,}` vé", inline=True)
        embed.set_footer(text=f"Dùng {ctx.prefix}lottery buy [số_lượng] để mua vé (10,000 coin/vé).")
        await ctx.send(embed=embed)

    @lottery.command(name="buy", description="Mua vé số tham gia mở thưởng Jackpot.")
    @app_commands.describe(count="Số lượng vé muốn mua")
    async def lottery_buy(self, ctx: commands.Context, count: int = 1):
        if count <= 0:
            return await ctx.send("❌ Số lượng vé phải từ 1 trở lên!", ephemeral=True)

        price = count * 10000
        deducted = await deduct_user_currency(ctx.guild.id, ctx.author.id, "coins", price)
        if not deducted:
            cur_bal = await get_user_currency(ctx.guild.id, ctx.author.id, "coins")
            return await ctx.send(f"❌ Bạn không đủ tiền mua {count} vé! Cần `{price:,}` coins. Số dư: `{cur_bal:,}`.", ephemeral=True)

        async with aiosqlite.connect(DB_PATH) as db:
            await db.execute("""
                INSERT INTO lottery (guild_id, user_id, ticket_count) VALUES (?, ?, ?)
                ON CONFLICT(guild_id, user_id) DO UPDATE SET ticket_count = ticket_count + ?
            """, (str(ctx.guild.id), str(ctx.author.id), count, count))
            await db.commit()

        await ctx.send(f"🎟️ Bạn đã mua thành công **{count} vé số** với giá **`{price:,}` coins**! Chúc bạn may mắn.")

    @tasks.loop(hours=24)
    async def lottery_draw_task(self):
        async with aiosqlite.connect(DB_PATH) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute("SELECT DISTINCT guild_id FROM lottery") as cur:
                guilds = await cur.fetchall()

            for g_row in guilds:
                gid = g_row["guild_id"]
                async with db.execute("SELECT user_id, ticket_count FROM lottery WHERE guild_id = ?", (gid,)) as c:
                    players = await c.fetchall()

                if not players:
                    continue

                pool = []
                for p in players:
                    pool.extend([p["user_id"]] * p["ticket_count"])

                winner_id = random.choice(pool)
                jackpot_coins = len(pool) * 10000

                await update_user_coins(int(gid), int(winner_id), jackpot_coins)
                await db.execute("DELETE FROM lottery WHERE guild_id = ?", (gid,))
                await db.commit()


                guild = self.bot.get_guild(int(gid))
                if guild and guild.system_channel:
                    try:
                        await guild.system_channel.send(
                            f"🎉 **KẾT QUẢ XỔ SỐ JACKPOT!**\nChúc mừng <@{winner_id}> đã may mắn trúng giải độc đắc với hũ thưởng **`{jackpot_coins:,}` coin**!"
                        )
                    except Exception:
                        pass

    # ================= GAME HUB: MENU TỔNG HỢP /MINIGAME =================
    @commands.hybrid_command(name="minigame", aliases=["game", "casino"], description="🎰 Mở Trung Tâm Mini-Games Sòng Bạc Sakura với đầy đủ game và hiệu ứng.")
    @commands.guild_only()
    async def minigame_hub(self, ctx: commands.Context):
        view = CasinoBetView(self, ctx.author, ctx.guild.id, game="taixiu", amount=1000, currency="coins", choice="tai")
        coins = await get_user_currency(ctx.guild.id, ctx.author.id, "coins")
        xu = await get_user_currency(ctx.guild.id, ctx.author.id, "xu")
        embed = view.build_embed(coins, xu)
        msg = await ctx.send(embed=embed, view=view)
        view.message = msg


async def setup(bot: commands.Bot):
    await bot.add_cog(CasinoCog(bot))
