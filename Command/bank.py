import json
import time
from datetime import timedelta, timezone
from pathlib import Path
from typing import Optional
import aiosqlite
import discord
from discord.ext import commands
from discord.ui import Button, Modal, Select, TextInput, View
from data.database import DB_PATH, get_user_data, update_user_coins, update_user_bank
from Check.i18n import t, is_vietnamese


BASE_DIR = Path(__file__).resolve().parent.parent
BANK_DATA_FILE = BASE_DIR / "data" / "bank_system.json"
VN_TZ = timezone(timedelta(hours=7))

BANK_BANNER_URL = "https://images.unsplash.com/photo-1501167786227-4cba60f6d58f?q=80&w=1200&auto=format&fit=crop"
BANK_THUMB_URL = "https://cdn-icons-png.flaticon.com/512/2830/2830284.png"

SAVINGS_TERMS = {
    "flexible": {
        "name_vi": "Không kỳ hạn (Ví thanh toán)",
        "name_en": "On-Demand (Checking)",
        "days": 0,
        "rate": 0.001,
        "label_vi": "Lãi 0.1%/ngày (Rút nạp linh hoạt bất kỳ lúc nào)",
        "label_en": "0.1%/day interest (Flexible deposit & withdraw anytime)"
    },
    "7d": {
        "name_vi": "Kỳ hạn 7 Ngày",
        "name_en": "7-Day Term",
        "days": 7,
        "rate": 0.05,
        "label_vi": "Lãi 5.0%/kỳ (Rút trước hạn: mất lãi + phạt 5% gốc)",
        "label_en": "5.0%/term interest (Early withdraw: forfeit interest + 5% penalty)"
    },
    "14d": {
        "name_vi": "Kỳ hạn 14 Ngày",
        "name_en": "14-Day Term",
        "days": 14,
        "rate": 0.12,
        "label_vi": "Lãi 12.0%/kỳ (Rút trước hạn: mất lãi + phạt 5% gốc)",
        "label_en": "12.0%/term interest (Early withdraw: forfeit interest + 5% penalty)"
    },
    "30d": {
        "name_vi": "Kỳ hạn 30 Ngày",
        "name_en": "30-Day Term",
        "days": 30,
        "rate": 0.30,
        "label_vi": "Lãi 30.0%/kỳ (Rút trước hạn: mất lãi + phạt 5% gốc)",
        "label_en": "30.0%/term interest (Early withdraw: forfeit interest + 5% penalty)"
    },
}

LOAN_TERMS = {
    "7d": {
        "name_vi": "Vay tiêu dùng 7 Ngày",
        "name_en": "7-Day Consumer Loan",
        "days": 7,
        "rate": 0.06,
        "label_vi": "Lãi suất 6.0% (Thời hạn 7 ngày)",
        "label_en": "6.0% interest rate (7 days duration)"
    },
    "14d": {
        "name_vi": "Vay kinh doanh 14 Ngày",
        "name_en": "14-Day Business Loan",
        "days": 14,
        "rate": 0.14,
        "label_vi": "Lãi suất 14.0% (Thời hạn 14 ngày)",
        "label_en": "14.0% interest rate (14 days duration)"
    },
    "30d": {
        "name_vi": "Vay đầu tư 30 Ngày",
        "name_en": "30-Day Investment Loan",
        "days": 30,
        "rate": 0.32,
        "label_vi": "Lãi suất 32.0% (Thời hạn 30 ngày)",
        "label_en": "32.0% interest rate (30 days duration)"
    },
}

EARLY_WITHDRAW_PENALTY_RATE = 0.05

bank_storage = {}


def load_bank_storage():
    global bank_storage
    if BANK_DATA_FILE.exists():
        try:
            with open(BANK_DATA_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                if isinstance(data, dict):
                    bank_storage.update(data)
        except Exception:
            pass


def save_bank_storage():
    BANK_DATA_FILE.parent.mkdir(parents=True, exist_ok=True)
    try:
        with open(BANK_DATA_FILE, "w", encoding="utf-8") as f:
            json.dump(bank_storage, f, indent=4, ensure_ascii=False)
    except Exception:
        pass


load_bank_storage()


def get_user_bank_record(guild_id: int, user_id: int) -> dict:
    key = f"{guild_id}_{user_id}"
    record = bank_storage.setdefault(key, {})
    record.setdefault("term_deposits", [])
    record.setdefault("loan", None)
    record.setdefault("credit_score", 700)
    record.setdefault("history", [])
    record.setdefault("last_penalty_check", int(time.time()))
    return record


async def update_user_bank_balance(guild_id: int, user_id: int, amount: int):
    return await update_user_bank(guild_id, user_id, amount)


def add_transaction_history(guild_id: int, user_id: int, tx_type: str, amount: int, note: str):
    rec = get_user_bank_record(guild_id, user_id)
    history = rec.setdefault("history", [])
    entry = {
        "time": int(time.time()),
        "type": tx_type,
        "amount": amount,
        "note": note
    }
    history.insert(0, entry)
    if len(history) > 25:
        rec["history"] = history[:25]
    save_bank_storage()


def check_and_apply_loan_penalties(guild_id: int, user_id: int):
    rec = get_user_bank_record(guild_id, user_id)
    loan = rec.get("loan")
    if not loan:
        return

    now = int(time.time())
    due_time = loan.get("due_time", 0)
    if now > due_time:
        loan["is_overdue"] = True
        last_check = rec.get("last_penalty_check", due_time)
        days_late = (now - last_check) // 86400
        if days_late >= 1:
            penalty = int(loan["remaining_debt"] * 0.05 * days_late)
            if penalty > 0:
                loan["remaining_debt"] += penalty
                rec["credit_score"] = max(300, rec.get("credit_score", 700) - (20 * days_late))
                add_transaction_history(guild_id, user_id, "PENALTY", penalty, f"Phạt trễ hạn khoản vay ({days_late} ngày)")
            rec["last_penalty_check"] = now
            save_bank_storage()


def calculate_max_loan(level: int, credit_score: int) -> int:
    base = max(100000, level * 150000)
    multiplier = credit_score / 700.0
    return int(min(50000000, base * multiplier))


class SimpleAmountModal(Modal):
    def __init__(self, title: str, label: str, placeholder: str, callback_action, is_vi: bool = True):
        super().__init__(title=title)
        self.callback_action = callback_action
        self.is_vi = is_vi
        self.amount_input = TextInput(
            label=label,
            placeholder=placeholder,
            required=True,
            min_length=1,
            max_length=15
        )
        self.add_item(self.amount_input)

    async def on_submit(self, interaction: discord.Interaction):
        val = self.amount_input.value.strip().replace(",", "").replace(".", "")
        if not val.isdigit() or int(val) <= 0:
            err = "❌ Số tiền nhập vào phải là số nguyên dương hợp lệ!" if self.is_vi else "❌ The amount must be a valid positive integer!"
            return await interaction.response.send_message(err, ephemeral=True)
        await self.callback_action(interaction, int(val))


class BankHistoryView(View):
    def __init__(self, author: discord.Member, parent_view: "BankMainView"):
        super().__init__(timeout=90)
        self.author = author
        self.parent_view = parent_view
        vi = is_vietnamese(parent_view.guild_id)
        self.back_btn.label = "Quay Lại Trang Chính" if vi else "Back to Main Page"

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id != self.author.id:
            vi = is_vietnamese(interaction.guild_id)
            msg = "❌ Đây không phải phiên làm việc của bạn!" if vi else "❌ This session does not belong to you!"
            await interaction.response.send_message(msg, ephemeral=True)
            return False
        return True

    @discord.ui.button(label="Quay Lại Trang Chính", style=discord.ButtonStyle.primary, emoji="🔙", row=0)
    async def back_btn(self, interaction: discord.Interaction, button: Button):
        embed = await self.parent_view.build_main_embed()
        await interaction.response.edit_message(embed=embed, view=self.parent_view)


class DepositFlowView(View):
    def __init__(self, author: discord.Member, parent_view: "BankMainView"):
        super().__init__(timeout=120)
        self.author = author
        self.parent_view = parent_view
        self.selected_amount: Optional[int] = None
        self.selected_term: str = "flexible"

        vi = is_vietnamese(parent_view.guild_id)

        self.amt_2m.label = "2 Triệu" if vi else "2 Million"
        self.amt_all.label = "Tất Cả Ví" if vi else "All Wallet"
        self.amt_custom.label = "Nhập Tùy Ý" if vi else "Custom Amount"
        self.confirm_deposit.label = "Xác Nhận Gửi" if vi else "Confirm Deposit"
        self.cancel_btn.label = "Hủy Bỏ" if vi else "Cancel"

        term_options = [
            discord.SelectOption(
                label=data["name_vi"] if vi else data["name_en"],
                value=key,
                description=data["label_vi"] if vi else data["label_en"],
                emoji="📈" if key != "flexible" else "🏦",
                default=(key == "flexible")
            )
            for key, data in SAVINGS_TERMS.items()
        ]
        ph = "Chọn kỳ hạn gửi tiết kiệm (7, 14, 30 ngày)..." if vi else "Select savings term (7, 14, 30 days)..."
        self.term_select = Select(placeholder=ph, options=term_options, row=1)
        self.term_select.callback = self._on_term_select
        self.add_item(self.term_select)

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id != self.author.id:
            vi = is_vietnamese(interaction.guild_id)
            msg = "❌ Đây không phải phiên làm việc của bạn!" if vi else "❌ This session does not belong to you!"
            await interaction.response.send_message(msg, ephemeral=True)
            return False
        return True

    def build_embed(self, wallet_coins: int) -> discord.Embed:
        vi = is_vietnamese(self.parent_view.guild_id)
        chosen_term = SAVINGS_TERMS[self.selected_term]
        t_name = chosen_term["name_vi"] if vi else chosen_term["name_en"]
        t_label = chosen_term["label_vi"] if vi else chosen_term["label_en"]
        term_desc = f"**{t_name}**\n└ *{t_label}*"

        amt_str = f"**`{self.selected_amount:,}` coin**" if self.selected_amount else ("*Chưa chọn số tiền*" if vi else "*No amount selected*")
        exp_interest_str = ""
        if self.selected_amount and self.selected_term != "flexible":
            exp_profit = int(self.selected_amount * chosen_term["rate"])
            if vi:
                exp_interest_str = f"\n• Tiền lãi khi đáo hạn: **`+{exp_profit:,}` coin**\n• Cảnh báo rút non: **Mất toàn bộ lãi + trừ 5% tiền gốc**"
            else:
                exp_interest_str = f"\n• Maturity Interest: **`+{exp_profit:,}` coins**\n• Early withdrawal warning: **Forfeit all interest + 5% principal penalty**"

        if vi:
            title = "📥 GỬI TIỀN & MỞ SỔ TIẾT KIỆM KỲ HẠN"
            desc = (
                f"👛 Tiền mặt trong ví: **`{wallet_coins:,}` coin**\n\n"
                f"• Số tiền chọn gửi: {amt_str}\n"
                f"• Gói kỳ hạn: {term_desc}{exp_interest_str}\n\n"
                "👉 *Chọn mốc tiền ở Hàng 1, chọn kỳ hạn ở Hàng 2 rồi bấm **Xác Nhận Gửi**.*"
            )
        else:
            title = "📥 DEPOSIT & TERM SAVINGS"
            desc = (
                f"👛 Cash in wallet: **`{wallet_coins:,}` coins**\n\n"
                f"• Selected Amount: {amt_str}\n"
                f"• Savings Plan: {term_desc}{exp_interest_str}\n\n"
                "👉 *Select amount in Row 1, choose term in Row 2, then click **Confirm Deposit**.*"
            )

        embed = discord.Embed(title=title, description=desc, color=discord.Color.green())
        embed.set_thumbnail(url=BANK_THUMB_URL)
        embed.set_image(url=BANK_BANNER_URL)
        return embed

    async def _on_term_select(self, interaction: discord.Interaction):
        self.selected_term = self.term_select.values[0]
        for opt in self.term_select.options:
            opt.default = (opt.value == self.selected_term)
        u_data = await get_user_data(interaction.guild_id, self.author.id)
        await interaction.response.edit_message(embed=self.build_embed(u_data.get("coins", 0)), view=self)

    async def _set_amount_and_update(self, interaction: discord.Interaction, amt: int):
        self.selected_amount = amt
        u_data = await get_user_data(interaction.guild_id, self.author.id)
        await interaction.response.edit_message(embed=self.build_embed(u_data.get("coins", 0)), view=self)

    @discord.ui.button(label="100K", style=discord.ButtonStyle.secondary, row=0)
    async def amt_100k(self, interaction: discord.Interaction, button: Button):
        await self._set_amount_and_update(interaction, 100000)

    @discord.ui.button(label="500K", style=discord.ButtonStyle.secondary, row=0)
    async def amt_500k(self, interaction: discord.Interaction, button: Button):
        await self._set_amount_and_update(interaction, 500000)

    @discord.ui.button(label="2 Triệu", style=discord.ButtonStyle.secondary, row=0)
    async def amt_2m(self, interaction: discord.Interaction, button: Button):
        await self._set_amount_and_update(interaction, 2000000)

    @discord.ui.button(label="Tất Cả Ví", style=discord.ButtonStyle.secondary, emoji="💰", row=0)
    async def amt_all(self, interaction: discord.Interaction, button: Button):
        vi = is_vietnamese(interaction.guild_id)
        u_data = await get_user_data(interaction.guild_id, self.author.id)
        wallet = u_data.get("coins", 0)
        if wallet <= 0:
            err = "❌ Ví của bạn không còn đồng nào để gửi!" if vi else "❌ You don't have any coins left in your wallet!"
            return await interaction.response.send_message(err, ephemeral=True)
        await self._set_amount_and_update(interaction, wallet)

    @discord.ui.button(label="Nhập Tùy Ý", style=discord.ButtonStyle.secondary, emoji="✏️", row=0)
    async def amt_custom(self, interaction: discord.Interaction, button: Button):
        vi = is_vietnamese(interaction.guild_id)
        async def on_submit_custom(modal_interaction: discord.Interaction, custom_val: int):
            self.selected_amount = custom_val
            u_data = await get_user_data(modal_interaction.guild_id, self.author.id)
            await modal_interaction.response.edit_message(embed=self.build_embed(u_data.get("coins", 0)), view=self)

        modal = SimpleAmountModal(
            title="Nhập Số Tiền Muốn Gửi" if vi else "Enter Deposit Amount",
            label="Số coin gửi vào ngân hàng" if vi else "Amount of coins to deposit",
            placeholder="250000",
            callback_action=on_submit_custom,
            is_vi=vi
        )
        await interaction.response.send_modal(modal)

    @discord.ui.button(label="Xác Nhận Gửi", style=discord.ButtonStyle.success, emoji="✅", row=2)
    async def confirm_deposit(self, interaction: discord.Interaction, button: Button):
        vi = is_vietnamese(interaction.guild_id)
        if not self.selected_amount or self.selected_amount <= 0:
            err = "⚠️ Vui lòng chọn hoặc nhập số tiền muốn gửi trước!" if vi else "⚠️ Please select or enter an amount to deposit first!"
            return await interaction.response.send_message(err, ephemeral=True)

        user_id = self.author.id
        guild_id = interaction.guild_id
        u_data = await get_user_data(guild_id, user_id)
        wallet = u_data.get("coins", 0)

        if wallet < self.selected_amount:
            err = f"❌ Bạn không đủ tiền mặt! Ví hiện có: `{wallet:,}` coin." if vi else f"❌ Insufficient wallet balance! You only have: `{wallet:,}` coins."
            return await interaction.response.send_message(err, ephemeral=True)

        amt = self.selected_amount
        term_cfg = SAVINGS_TERMS[self.selected_term]
        t_name = term_cfg["name_vi"] if vi else term_cfg["name_en"]

        await update_user_coins(guild_id, user_id, -amt)

        if self.selected_term == "flexible":
            await update_user_bank_balance(guild_id, user_id, amt)
            add_transaction_history(guild_id, user_id, "DEPOSIT", amt, "Gửi tiền vào tài khoản thanh toán" if vi else "Deposit into checking account")
            msg = f"✅ Đã nạp thành công **`{amt:,}` coin** vào tài khoản ngân hàng không kỳ hạn!" if vi else f"✅ Successfully deposited **`{amt:,}` coins** into your checking account!"
        else:
            now = int(time.time())
            dur_seconds = term_cfg["days"] * 86400
            exp_interest = int(amt * term_cfg["rate"])
            rec = get_user_bank_record(guild_id, user_id)
            dep_obj = {
                "id": f"SO-{int(now % 100000):05d}",
                "principal": amt,
                "term_key": self.selected_term,
                "term_name": t_name,
                "rate": term_cfg["rate"],
                "start_time": now,
                "end_time": now + dur_seconds,
                "expected_interest": exp_interest,
            }
            rec.setdefault("term_deposits", []).append(dep_obj)
            save_bank_storage()
            add_transaction_history(guild_id, user_id, "TERM_DEPOSIT", amt, f"Mở {t_name}" if vi else f"Opened {t_name}")
            if vi:
                msg = (
                    f"📈 Mở thành công sổ tiết kiệm **{dep_obj['id']}** ({t_name})!\n"
                    f"• Gốc: **`{amt:,}` coin** | Lãi: **`+{exp_interest:,}` coin**\n"
                    f"• Đáo hạn lúc: <t:{now + dur_seconds}:F>\n"
                    f"⚠️ *Lưu ý: Rút trước hạn sẽ bị hủy toàn bộ tiền lãi và trừ 5% phí phạt trên tiền gốc.*"
                )
            else:
                msg = (
                    f"📈 Successfully opened term savings passbook **{dep_obj['id']}** ({t_name})!\n"
                    f"• Principal: **`{amt:,}` coins** | Interest: **`+{exp_interest:,}` coins**\n"
                    f"• Matures at: <t:{now + dur_seconds}:F>\n"
                    f"⚠️ *Note: Early withdrawal will forfeit all interest and apply a 5% principal penalty.*"
                )

        embed = await self.parent_view.build_main_embed()
        await interaction.response.edit_message(embed=embed, view=self.parent_view)
        await interaction.followup.send(msg, ephemeral=True)

    @discord.ui.button(label="Hủy Bỏ", style=discord.ButtonStyle.danger, emoji="✖️", row=2)
    async def cancel_btn(self, interaction: discord.Interaction, button: Button):
        embed = await self.parent_view.build_main_embed()
        await interaction.response.edit_message(embed=embed, view=self.parent_view)


class SettleDepositSelectView(View):
    def __init__(self, author: discord.Member, parent_view: "BankMainView"):
        super().__init__(timeout=90)
        self.author = author
        self.parent_view = parent_view
        vi = is_vietnamese(parent_view.guild_id)
        self.back_btn.label = "Quay Lại" if vi else "Back"

        rec = get_user_bank_record(parent_view.guild_id, author.id)
        deposits = rec.get("term_deposits", [])
        now = int(time.time())

        options = []
        for d in deposits[:25]:
            is_matured = (d["end_time"] <= now)
            if is_matured:
                desc = f"🟢 Đã đáo hạn | Nhận: {d['principal'] + d['expected_interest']:,}c (Đủ gốc + lãi)" if vi else f"🟢 Matured | Payout: {d['principal'] + d['expected_interest']:,}c (Full)"
            else:
                pen = int(d["principal"] * EARLY_WITHDRAW_PENALTY_RATE)
                desc = f"🔴 Chưa đáo hạn | Phạt: -{pen:,}c (Chỉ nhận {d['principal'] - pen:,}c)" if vi else f"🔴 Active | Penalty: -{pen:,}c (Receive: {d['principal'] - pen:,}c)"

            options.append(
                discord.SelectOption(
                    label=f"{d['id']} - {d['term_name']}"[:100],
                    value=d["id"],
                    description=desc[:100],
                    emoji="✅" if is_matured else "⚠️"
                )
            )

        ph = "Chọn sổ tiết kiệm bạn muốn tất toán..." if vi else "Select the passbook you want to settle..."
        self.select_menu = Select(placeholder=ph, options=options, row=0)
        self.select_menu.callback = self._on_select_settle
        self.add_item(self.select_menu)

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id != self.author.id:
            vi = is_vietnamese(interaction.guild_id)
            msg = "❌ Đây không phải phiên làm việc của bạn!" if vi else "❌ This session does not belong to you!"
            await interaction.response.send_message(msg, ephemeral=True)
            return False
        return True

    async def _on_select_settle(self, interaction: discord.Interaction):
        vi = is_vietnamese(interaction.guild_id)
        so_id = self.select_menu.values[0]
        rec = get_user_bank_record(self.parent_view.guild_id, self.author.id)
        deposits = rec.get("term_deposits", [])

        target_dep = next((d for d in deposits if d["id"] == so_id), None)
        if not target_dep:
            err = "❌ Không tìm thấy thông tin sổ này!" if vi else "❌ Could not find information for this passbook!"
            return await interaction.response.send_message(err, ephemeral=True)

        now = int(time.time())
        is_matured = (target_dep["end_time"] <= now)

        if is_matured:
            total_receive = target_dep["principal"] + target_dep["expected_interest"]
            rec["term_deposits"] = [d for d in deposits if d["id"] != so_id]
            save_bank_storage()
            await update_user_coins(self.parent_view.guild_id, self.author.id, total_receive)
            add_transaction_history(self.parent_view.guild_id, self.author.id, "SETTLEMENT", total_receive, f"Tất toán đúng hạn sổ {so_id}" if vi else f"Matured settlement {so_id}")

            if vi:
                msg = (
                    f"🎉 **TẤT TOÁN ĐÚNG HẠN THÀNH CÔNG!**\n"
                    f"Sổ **{so_id}** đã được thanh toán toàn bộ:\n"
                    f"• Gốc: `{target_dep['principal']:,}` coin\n"
                    f"• Lãi: `+{target_dep['expected_interest']:,}` coin\n"
                    f"➜ Đã chuyển **`+{total_receive:,}` coin** vào ví tiền mặt!"
                )
            else:
                msg = (
                    f"🎉 **SUCCESSFUL MATURITY SETTLEMENT!**\n"
                    f"Passbook **{so_id}** has been settled in full:\n"
                    f"• Principal: `{target_dep['principal']:,}` coins\n"
                    f"• Interest: `+{target_dep['expected_interest']:,}` coins\n"
                    f"➜ Transferred **`+{total_receive:,}` coins** to your wallet!"
                )
        else:
            penalty = int(target_dep["principal"] * EARLY_WITHDRAW_PENALTY_RATE)
            actual_refund = max(0, target_dep["principal"] - penalty)
            rec["term_deposits"] = [d for d in deposits if d["id"] != so_id]
            save_bank_storage()
            await update_user_coins(self.parent_view.guild_id, self.author.id, actual_refund)
            add_transaction_history(self.parent_view.guild_id, self.author.id, "EARLY_WITHDRAW", actual_refund, f"Rút trước hạn sổ {so_id} (Phạt -{penalty:,}c)" if vi else f"Early settlement {so_id} (Penalty -{penalty:,}c)")

            if vi:
                msg = (
                    f"⚠️ **RÚT TIẾT KIỆM TRƯỚC HẠN!**\n"
                    f"Sổ **{so_id}** chưa tới ngày đáo hạn nên bị áp dụng chế tài:\n"
                    f"• Tiền lãi dự kiến: **`0 coin`** (Mất toàn bộ quyền nhận lãi)\n"
                    f"• Phí phạt vi phạm hợp đồng (5% gốc): **`-{penalty:,}` coin**\n"
                    f"• Tiền gốc hoàn trả thực tế: **`+{actual_refund:,}` coin** (Đã chuyển về ví tiền mặt)."
                )
            else:
                msg = (
                    f"⚠️ **EARLY WITHDRAWAL APPLIED!**\n"
                    f"Passbook **{so_id}** has not matured yet and terms apply:\n"
                    f"• Earned Interest: **`0 coins`** (All interest forfeited)\n"
                    f"• Contract Penalty (5% of principal): **`-{penalty:,}` coins**\n"
                    f"• Net Refund: **`+{actual_refund:,}` coins** (Transferred to wallet)."
                )

        embed = await self.parent_view.build_main_embed()
        await interaction.response.edit_message(embed=embed, view=self.parent_view)
        await interaction.followup.send(msg, ephemeral=True)

    @discord.ui.button(label="Quay Lại", style=discord.ButtonStyle.secondary, emoji="🔙", row=1)
    async def back_btn(self, interaction: discord.Interaction, button: Button):
        embed = await self.parent_view.build_main_embed()
        await interaction.response.edit_message(embed=embed, view=self.parent_view)


class LoanFlowView(View):
    def __init__(self, author: discord.Member, parent_view: "BankMainView", max_limit: int):
        super().__init__(timeout=120)
        self.author = author
        self.parent_view = parent_view
        self.max_limit = max_limit
        self.selected_amount: Optional[int] = None
        self.selected_term: str = "7d"

        vi = is_vietnamese(parent_view.guild_id)
        self.loan_1m.label = "1 Triệu" if vi else "1 Million"
        self.loan_max.label = "Tối Đa" if vi else "Maximum"
        self.loan_custom.label = "Nhập Tùy Chọn" if vi else "Custom Loan"
        self.confirm_loan.label = "Giải Ngân Ngay" if vi else "Disburse Now"
        self.cancel_loan_btn.label = "Quay Lại" if vi else "Back"

        loan_options = [
            discord.SelectOption(
                label=data["name_vi"] if vi else data["name_en"],
                value=key,
                description=data["label_vi"] if vi else data["label_en"],
                emoji="💳",
                default=(key == "7d")
            )
            for key, data in LOAN_TERMS.items()
        ]
        ph = "Chọn kỳ hạn vay vốn..." if vi else "Select loan term..."
        self.loan_select = Select(placeholder=ph, options=loan_options, row=1)
        self.loan_select.callback = self._on_term_select
        self.add_item(self.loan_select)

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id != self.author.id:
            vi = is_vietnamese(interaction.guild_id)
            msg = "❌ Đây không phải phiên làm việc của bạn!" if vi else "❌ This session does not belong to you!"
            await interaction.response.send_message(msg, ephemeral=True)
            return False
        return True

    def build_embed(self) -> discord.Embed:
        vi = is_vietnamese(self.parent_view.guild_id)
        term_cfg = LOAN_TERMS[self.selected_term]
        t_name = term_cfg["name_vi"] if vi else term_cfg["name_en"]
        interest = int(self.selected_amount * term_cfg["rate"]) if self.selected_amount else 0
        total_pay = (self.selected_amount + interest) if self.selected_amount else 0

        if vi:
            title = "💳 HỒ SƠ ĐĂNG KÝ VAY VỐN TÍN DỤNG"
            if self.selected_amount:
                desc = (
                    f"Hạn mức tín dụng tối đa: **`{self.max_limit:,}` coin**\n\n"
                    f"• Khoản vay đăng ký: **`{self.selected_amount:,}` coin**\n"
                    f"• Gói thời hạn: **{t_name}** (Lãi suất: `{int(term_cfg['rate']*100)}%`)\n"
                    f"• Tiền lãi vay: **`{interest:,}` coin**\n"
                    f"• Tổng hoàn trả khi đáo hạn: **`{total_pay:,}` coin**\n\n"
                    "👉 *Chọn mốc vay ở Hàng 1, gói kỳ hạn ở Hàng 2 rồi bấm **Giải Ngân Ngay**.*"
                )
            else:
                desc = (
                    f"Hạn mức tín dụng tối đa của bạn: **`{self.max_limit:,}` coin**\n"
                    "Hãy chọn số tiền muốn giải ngân và gói kỳ hạn tương ứng:"
                )
        else:
            title = "💳 CREDIT LOAN APPLICATION"
            if self.selected_amount:
                desc = (
                    f"Max approved loan limit: **`{self.max_limit:,}` coins**\n\n"
                    f"• Requested Loan: **`{self.selected_amount:,}` coins**\n"
                    f"• Loan Package: **{t_name}** (Interest: `{int(term_cfg['rate']*100)}%`)\n"
                    f"• Loan Interest: **`{interest:,}` coins**\n"
                    f"• Total Repayment: **`{total_pay:,}` coins**\n\n"
                    "👉 *Select amount in Row 1, term package in Row 2, then click **Disburse Now**.*"
                )
            else:
                desc = (
                    f"Your approved credit limit: **`{self.max_limit:,}` coins**\n"
                    "Select loan amount and desired term duration:"
                )

        embed = discord.Embed(title=title, description=desc, color=discord.Color.red())
        embed.set_thumbnail(url=BANK_THUMB_URL)
        embed.set_image(url=BANK_BANNER_URL)
        return embed

    async def _on_term_select(self, interaction: discord.Interaction):
        self.selected_term = self.loan_select.values[0]
        for opt in self.loan_select.options:
            opt.default = (opt.value == self.selected_term)
        await interaction.response.edit_message(embed=self.build_embed(), view=self)

    async def _set_loan_amount(self, interaction: discord.Interaction, amt: int):
        vi = is_vietnamese(interaction.guild_id)
        if amt > self.max_limit:
            err = f"❌ Số tiền vượt quá hạn mức tín dụng ({self.max_limit:,} coin)!" if vi else f"❌ Amount exceeds your credit limit ({self.max_limit:,} coins)!"
            return await interaction.response.send_message(err, ephemeral=True)
        self.selected_amount = amt
        await interaction.response.edit_message(embed=self.build_embed(), view=self)

    @discord.ui.button(label="100K", style=discord.ButtonStyle.secondary, row=0)
    async def loan_100k(self, interaction: discord.Interaction, button: Button):
        await self._set_loan_amount(interaction, 100000)

    @discord.ui.button(label="500K", style=discord.ButtonStyle.secondary, row=0)
    async def loan_500k(self, interaction: discord.Interaction, button: Button):
        await self._set_loan_amount(interaction, 500000)

    @discord.ui.button(label="1 Triệu", style=discord.ButtonStyle.secondary, row=0)
    async def loan_1m(self, interaction: discord.Interaction, button: Button):
        await self._set_loan_amount(interaction, 1000000)

    @discord.ui.button(label="Tối Đa", style=discord.ButtonStyle.secondary, emoji="⚡", row=0)
    async def loan_max(self, interaction: discord.Interaction, button: Button):
        await self._set_loan_amount(interaction, self.max_limit)

    @discord.ui.button(label="Nhập Tùy Chọn", style=discord.ButtonStyle.secondary, emoji="✏️", row=0)
    async def loan_custom(self, interaction: discord.Interaction, button: Button):
        vi = is_vietnamese(interaction.guild_id)
        async def on_submit_loan(modal_interaction: discord.Interaction, custom_val: int):
            if custom_val > self.max_limit:
                err = f"❌ Số tiền vượt hạn mức ({self.max_limit:,} coin)!" if vi else f"❌ Amount exceeds credit limit ({self.max_limit:,} coins)!"
                return await modal_interaction.response.send_message(err, ephemeral=True)
            self.selected_amount = custom_val
            await modal_interaction.response.edit_message(embed=self.build_embed(), view=self)

        modal = SimpleAmountModal(
            title="Đăng Ký Số Tiền Vay" if vi else "Apply For Loan Amount",
            label="Số coin muốn giải ngân" if vi else "Coins to disburse",
            placeholder=f"Max {self.max_limit:,}",
            callback_action=on_submit_loan,
            is_vi=vi
        )
        await interaction.response.send_modal(modal)

    @discord.ui.button(label="Giải Ngân Ngay", style=discord.ButtonStyle.danger, emoji="💸", row=2)
    async def confirm_loan(self, interaction: discord.Interaction, button: Button):
        vi = is_vietnamese(interaction.guild_id)
        if not self.selected_amount or self.selected_amount <= 0:
            err = "⚠️ Vui lòng chọn số tiền vay hợp lệ!" if vi else "⚠️ Please select a valid loan amount!"
            return await interaction.response.send_message(err, ephemeral=True)

        user_id = self.author.id
        guild_id = interaction.guild_id
        rec = get_user_bank_record(guild_id, user_id)

        if rec.get("loan") is not None:
            err = "❌ Bạn đang có một khoản vay chưa tất toán!" if vi else "❌ You currently have an active unsettled loan!"
            return await interaction.response.send_message(err, ephemeral=True)

        amt = self.selected_amount
        term_cfg = LOAN_TERMS[self.selected_term]
        t_name = term_cfg["name_vi"] if vi else term_cfg["name_en"]
        interest = int(amt * term_cfg["rate"])
        total_due = amt + interest
        now = int(time.time())
        due_time = now + (term_cfg["days"] * 86400)

        rec["loan"] = {
            "principal": amt,
            "interest": interest,
            "total_due": total_due,
            "remaining_debt": total_due,
            "term_name": t_name,
            "start_time": now,
            "due_time": due_time,
            "is_overdue": False,
        }
        rec["last_penalty_check"] = now
        save_bank_storage()

        await update_user_coins(guild_id, user_id, amt)
        add_transaction_history(guild_id, user_id, "LOAN_DISBURSED", amt, f"Giải ngân vay vốn {t_name}" if vi else f"Loan disburse {t_name}")

        embed = await self.parent_view.build_main_embed()
        await interaction.response.edit_message(embed=embed, view=self.parent_view)
        if vi:
            msg = (
                f"🎉 **GIẢI NGÂN THÀNH CÔNG!**\n"
                f"Số tiền **`+{amt:,}` coin** đã được cộng vào ví của bạn.\n"
                f"Hạn thanh toán: <t:{due_time}:F> (Tổng hoàn trả: **`{total_due:,}` coin**)."
            )
        else:
            msg = (
                f"🎉 **DISBURSEMENT SUCCESSFUL!**\n"
                f"An amount of **`+{amt:,}` coins** was credited to your wallet.\n"
                f"Due date: <t:{due_time}:F> (Total repayment: **`{total_due:,}` coins**)."
            )
        await interaction.followup.send(msg, ephemeral=True)

    @discord.ui.button(label="Quay Lại", style=discord.ButtonStyle.secondary, emoji="🔙", row=2)
    async def cancel_loan_btn(self, interaction: discord.Interaction, button: Button):
        embed = await self.parent_view.build_main_embed()
        await interaction.response.edit_message(embed=embed, view=self.parent_view)


class BankMainView(View):
    def __init__(self, author: discord.Member, guild_id: int):
        super().__init__(timeout=180)
        self.author = author
        self.guild_id = guild_id
        vi = is_vietnamese(guild_id)

        self.deposit_btn.label = "Gửi Tiền" if vi else "Deposit"
        self.withdraw_cash_btn.label = "Rút Tiền Ví" if vi else "Withdraw"
        self.settle_deposit_btn.label = "Tất Toán Sổ Tiết Kiệm" if vi else "Settle Savings"
        self.loan_btn.label = "Vay Vốn" if vi else "Get Loan"
        self.repay_btn.label = "Trả Nợ Khoản Vay" if vi else "Repay Loan"
        self.history_btn.label = "Lịch Sử Giao Dịch" if vi else "History"

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id != self.author.id:
            vi = is_vietnamese(interaction.guild_id)
            msg = "❌ Bảng giao dịch này thuộc về người khác!" if vi else "❌ This bank session belongs to another user!"
            await interaction.response.send_message(msg, ephemeral=True)
            return False
        return True

    async def build_main_embed(self) -> discord.Embed:
        user_id = self.author.id
        guild_id = self.guild_id
        vi = is_vietnamese(guild_id)
        check_and_apply_loan_penalties(guild_id, user_id)

        u_data = await get_user_data(guild_id, user_id)
        wallet_coins = int(u_data.get("coins", 0))
        bank_coins = int(u_data.get("bank", 0))
        level = int(u_data.get("level", 0))

        rec = get_user_bank_record(guild_id, user_id)
        credit_score = rec.get("credit_score", 700)
        max_loan_limit = calculate_max_loan(level, credit_score)

        title = "🏛️ NGÂN HÀNG TRUNG ƯƠNG DISCORD" if vi else "🏛️ DISCORD CENTRAL BANK"
        desc = (
            f"Kính chào quý khách **{self.author.display_name}**, thông tin tài chính hiện tại của bạn:"
            if vi else
            f"Welcome customer **{self.author.display_name}**, here is your financial overview:"
        )

        embed = discord.Embed(
            title=title,
            description=desc,
            color=discord.Color.from_rgb(30, 58, 138),
            timestamp=discord.utils.utcnow()
        )
        embed.set_thumbnail(url=BANK_THUMB_URL)
        embed.set_image(url=BANK_BANNER_URL)

        user_xu = int(u_data.get("xu", 0))

        if vi:
            acct_val = (
                f"• 👛 **Tiền mặt (Ví):** ` {wallet_coins:,} ` coin\n"
                f"• 🏦 **Tài khoản thanh toán:** ` {bank_coins:,} ` coin\n"
                f"• 💎 **Tổng Coin khả dụng:** **` {wallet_coins + bank_coins:,} ` coin**\n"
                f"• 💠 **Tài khoản Xu (Nạp/Owner):** **` {user_xu:,} ` xu**"
            )
            embed.add_field(name="💼 Tài Khoản & Số Dư Khả Dụng", value=acct_val, inline=False)
        else:
            acct_val = (
                f"• 👛 **Wallet Cash:** ` {wallet_coins:,} ` coins\n"
                f"• 🏦 **Checking Account:** ` {bank_coins:,} ` coins\n"
                f"• 💎 **Total Available Coins:** **` {wallet_coins + bank_coins:,} ` coins**\n"
                f"• 💠 **Xu Points (Topup/Owner):** **` {user_xu:,} ` xu**"
            )
            embed.add_field(name="💼 Accounts & Available Balance", value=acct_val, inline=False)

        deposits = rec.get("term_deposits", [])
        now = int(time.time())
        if deposits:
            dep_lines = []
            for dep in deposits[:4]:
                if dep["end_time"] <= now:
                    status_str = "🟢 **ĐÃ ĐÁO HẠN** (Bấm Rút Sổ để nhận)" if vi else "🟢 **MATURED** (Click Settle to claim)"
                else:
                    status_str = f"⏳ Đáo hạn <t:{dep['end_time']}:R> (Rút non: trừ 5% gốc)" if vi else f"⏳ Matures <t:{dep['end_time']}:R> (Early fee: 5% principal)"
                goc_lbl = "Gốc" if vi else "Principal"
                lai_lbl = "Lãi" if vi else "Interest"
                dep_lines.append(f"• **{dep['id']}** ({dep['term_name']}) | {goc_lbl}: `{dep['principal']:,}`c | {lai_lbl}: `+{dep['expected_interest']:,}`c\n  └ {status_str}")
            total_savings_principal = sum(d["principal"] for d in deposits)
            total_savings_expected = sum(d["expected_interest"] for d in deposits)
            if vi:
                field_title = f"📈 Sổ Tiết Kiệm Định Kỳ ({len(deposits)} sổ)"
                field_val = f"Tổng gốc gửi: **`{total_savings_principal:,}` c** | Lãi dự kiến: **`+{total_savings_expected:,}` c**\n" + "\n".join(dep_lines)
            else:
                field_title = f"📈 Term Savings ({len(deposits)} passbooks)"
                field_val = f"Total Principal: **`{total_savings_principal:,}` c** | Exp. Interest: **`+{total_savings_expected:,}` c**\n" + "\n".join(dep_lines)
            embed.add_field(name=field_title, value=field_val, inline=False)
        else:
            if vi:
                embed.add_field(name="📈 Sổ Tiết Kiệm Định Kỳ", value="*Chưa có sổ tiết kiệm nào (Kỳ hạn 7, 14, 30 ngày).* ", inline=False)
            else:
                embed.add_field(name="📈 Term Savings", value="*No active term savings passbooks (7, 14, 30 days).* ", inline=False)

        loan = rec.get("loan")
        if loan:
            if vi:
                overdue_tag = "🔴 **ĐÃ QUÁ HẠN (Phạt 5%/ngày)**" if loan.get("is_overdue") else f"🟢 Đến hạn: <t:{loan['due_time']}:R>"
                loan_desc = (
                    f"• Gói: **{loan.get('term_name', 'Vay tín dụng')}**\n"
                    f"• Dư nợ: **`{loan['remaining_debt']:,}` coin** (Gốc: `{loan['principal']:,}`c)\n"
                    f"• Trạng thái: {overdue_tag}"
                )
            else:
                overdue_tag = "🔴 **OVERDUE (Penalty 5%/day)**" if loan.get("is_overdue") else f"🟢 Due: <t:{loan['due_time']}:R>"
                loan_desc = (
                    f"• Package: **{loan.get('term_name', 'Credit Loan')}**\n"
                    f"• Remaining Debt: **`{loan['remaining_debt']:,}` coins** (Principal: `{loan['principal']:,}`c)\n"
                    f"• Status: {overdue_tag}"
                )
        else:
            loan_desc = f"• Không có nợ xấu | Hạn mức được duyệt: **`{max_loan_limit:,}` coin**" if vi else f"• No bad debt | Approved Limit: **`{max_loan_limit:,}` coins**"

        if vi:
            score_rating = "⭐ Hạng Vàng" if credit_score >= 750 else ("🟢 Hạng Chuẩn" if credit_score >= 600 else "⚠️ Tín Dụng Xấu")
            embed.add_field(name="📑 Tình Trạng Khoản Vay", value=loan_desc, inline=True)
            embed.add_field(name="📊 Điểm Tín Dụng", value=f"`{credit_score}/850` ({score_rating})", inline=True)
            embed.set_footer(text="Hệ thống ngân hàng chuẩn thời gian thực • Giao dịch tự động & Bảo mật")
        else:
            score_rating = "⭐ Gold Rating" if credit_score >= 750 else ("🟢 Standard Rating" if credit_score >= 600 else "⚠️ Poor Credit")
            embed.add_field(name="📑 Loan Status", value=loan_desc, inline=True)
            embed.add_field(name="📊 Credit Score", value=f"`{credit_score}/850` ({score_rating})", inline=True)
            embed.set_footer(text="Real-time Banking System • Automated & Secure")

        return embed

    @discord.ui.button(label="Gửi Tiền", style=discord.ButtonStyle.success, emoji="📥", row=0)
    async def deposit_btn(self, interaction: discord.Interaction, button: Button):
        flow = DepositFlowView(self.author, self)
        u_data = await get_user_data(self.guild_id, self.author.id)
        embed = flow.build_embed(u_data.get("coins", 0))
        await interaction.response.edit_message(embed=embed, view=flow)

    @discord.ui.button(label="Rút Tiền Ví", style=discord.ButtonStyle.primary, emoji="📤", row=0)
    async def withdraw_cash_btn(self, interaction: discord.Interaction, button: Button):
        vi = is_vietnamese(interaction.guild_id)
        async def on_submit_withdraw(modal_interaction: discord.Interaction, amt: int):
            u_data = await get_user_data(self.guild_id, self.author.id)
            current_bank = u_data.get("bank", 0)
            if current_bank < amt:
                err = f"❌ Số dư ngân hàng không đủ! Hiện có: `{current_bank:,}` coin." if vi else f"❌ Insufficient checking balance! You have: `{current_bank:,}` coins."
                return await modal_interaction.response.send_message(err, ephemeral=True)

            await update_user_bank_balance(self.guild_id, self.author.id, -amt)
            await update_user_coins(self.guild_id, self.author.id, amt)
            add_transaction_history(self.guild_id, self.author.id, "WITHDRAW", amt, "Rút tiền từ tài khoản thanh toán" if vi else "Withdraw from checking account")

            new_embed = await self.build_main_embed()
            await modal_interaction.response.edit_message(embed=new_embed, view=self)
            succ = f"✅ Đã rút thành công **`{amt:,}` coin** về ví tiền mặt!" if vi else f"✅ Successfully withdrew **`{amt:,}` coins** to your wallet!"
            await modal_interaction.followup.send(succ, ephemeral=True)

        modal = SimpleAmountModal(
            title="Rút Tiền Tài Khoản Thanh Toán" if vi else "Withdraw From Checking",
            label="Số coin cần rút về ví tiền mặt" if vi else "Amount to withdraw to wallet",
            placeholder="100000",
            callback_action=on_submit_withdraw,
            is_vi=vi
        )
        await interaction.response.send_modal(modal)

    @discord.ui.button(label="Tất Toán Sổ Tiết Kiệm", style=discord.ButtonStyle.secondary, emoji="📑", row=0)
    async def settle_deposit_btn(self, interaction: discord.Interaction, button: Button):
        vi = is_vietnamese(interaction.guild_id)
        rec = get_user_bank_record(self.guild_id, self.author.id)
        deposits = rec.get("term_deposits", [])
        if not deposits:
            msg = "ℹ️ Quý khách hiện không có sổ tiết kiệm nào!" if vi else "ℹ️ You currently do not have any active term savings passbooks!"
            return await interaction.response.send_message(msg, ephemeral=True)

        view = SettleDepositSelectView(self.author, self)
        if vi:
            title = "📑 TẤT TOÁN SỔ TIẾT KIỆM (7, 14, 30 NGÀY)"
            desc = (
                "Hãy chọn sổ tiết kiệm bạn muốn tất toán từ menu bên dưới:\n\n"
                "• 🟢 **Sổ đã đáo hạn:** Nhận 100% gốc + 100% lãi tích lũy.\n"
                "• ⚠️ **Sổ chưa đáo hạn (Rút non):** Mất toàn bộ tiền lãi và **bị phạt 5% tiền gốc** vi phạm hợp đồng."
            )
        else:
            title = "📑 SETTLE TERM SAVINGS (7, 14, 30 DAYS)"
            desc = (
                "Select the savings passbook you want to settle below:\n\n"
                "• 🟢 **Matured:** Receive 100% principal + 100% earned interest.\n"
                "• ⚠️ **Active (Early withdrawal):** Forfeit all interest and **pay 5% penalty** on principal."
            )

        embed = discord.Embed(title=title, description=desc, color=discord.Color.orange())
        embed.set_thumbnail(url=BANK_THUMB_URL)
        embed.set_image(url=BANK_BANNER_URL)
        await interaction.response.edit_message(embed=embed, view=view)

    @discord.ui.button(label="Vay Vốn", style=discord.ButtonStyle.danger, emoji="💳", row=1)
    async def loan_btn(self, interaction: discord.Interaction, button: Button):
        vi = is_vietnamese(interaction.guild_id)
        rec = get_user_bank_record(self.guild_id, self.author.id)
        if rec.get("loan") is not None:
            err = "❌ Quý khách hiện đang có một khoản vay chưa thanh toán xong!" if vi else "❌ You currently have an outstanding active loan!"
            return await interaction.response.send_message(err, ephemeral=True)

        u_data = await get_user_data(self.guild_id, self.author.id)
        level = int(u_data.get("level", 0))
        credit_score = rec.get("credit_score", 700)
        max_limit = calculate_max_loan(level, credit_score)

        flow = LoanFlowView(self.author, self, max_limit)
        await interaction.response.edit_message(embed=flow.build_embed(), view=flow)

    @discord.ui.button(label="Trả Nợ Khoản Vay", style=discord.ButtonStyle.secondary, emoji="🧾", row=1)
    async def repay_btn(self, interaction: discord.Interaction, button: Button):
        vi = is_vietnamese(interaction.guild_id)
        rec = get_user_bank_record(self.guild_id, self.author.id)
        loan = rec.get("loan")
        if not loan:
            msg = "ℹ️ Quý khách hiện không có khoản nợ nào cần thanh toán." if vi else "ℹ️ You do not currently have any debt to repay."
            return await interaction.response.send_message(msg, ephemeral=True)

        async def on_submit_repay(modal_interaction: discord.Interaction, amt: int):
            u_data = await get_user_data(self.guild_id, self.author.id)
            wallet = u_data.get("coins", 0)
            if wallet < amt:
                err = f"❌ Ví của bạn không đủ coin! (Hiện có: `{wallet:,}` c)" if vi else f"❌ Insufficient wallet balance! (You have: `{wallet:,}` c)"
                return await modal_interaction.response.send_message(err, ephemeral=True)

            debt = loan["remaining_debt"]
            actual_pay = min(amt, debt)
            await update_user_coins(self.guild_id, self.author.id, -actual_pay)
            loan["remaining_debt"] -= actual_pay

            if loan["remaining_debt"] <= 0:
                rec["loan"] = None
                rec["credit_score"] = min(850, rec.get("credit_score", 700) + 30)
                save_bank_storage()
                add_transaction_history(self.guild_id, self.author.id, "REPAY_FULL", actual_pay, "Tất toán toàn bộ khoản vay" if vi else "Full loan repayment")
                res_msg = "🎉 Quý khách đã **tất toán thành công 100% khoản vay**! Điểm tín dụng tăng `+30` điểm." if vi else "🎉 You have **fully repaid 100% of your loan**! Credit score increased by `+30` points."
            else:
                save_bank_storage()
                add_transaction_history(self.guild_id, self.author.id, "REPAY_PART", actual_pay, "Thanh toán một phần nợ" if vi else "Partial loan repayment")
                res_msg = f"✅ Đã thanh toán **`{actual_pay:,}` coin**! Dư nợ còn lại: **`{loan['remaining_debt']:,}` coin**." if vi else f"✅ Repaid **`{actual_pay:,}` coins**! Remaining debt: **`{loan['remaining_debt']:,}` coins**."

            new_embed = await self.build_main_embed()
            await modal_interaction.response.edit_message(embed=new_embed, view=self)
            await modal_interaction.followup.send(res_msg, ephemeral=True)

        modal = SimpleAmountModal(
            title="Thanh Toán Khoản Vay" if vi else "Repay Loan Debt",
            label=f"Nhập số coin (Nợ hiện tại: {loan['remaining_debt']:,})" if vi else f"Coins to repay (Debt: {loan['remaining_debt']:,})",
            placeholder=str(loan["remaining_debt"]),
            callback_action=on_submit_repay,
            is_vi=vi
        )
        await interaction.response.send_modal(modal)

    @discord.ui.button(label="Lịch Sử Giao Dịch", style=discord.ButtonStyle.secondary, emoji="📜", row=1)
    async def history_btn(self, interaction: discord.Interaction, button: Button):
        vi = is_vietnamese(interaction.guild_id)
        rec = get_user_bank_record(self.guild_id, self.author.id)
        history = rec.get("history", [])

        title = f"📜 LỊCH SỬ GIAO DỊCH: {self.author.display_name.upper()}" if vi else f"📜 TRANSACTION HISTORY: {self.author.display_name.upper()}"
        embed = discord.Embed(title=title, color=discord.Color.teal())
        embed.set_thumbnail(url=BANK_THUMB_URL)
        embed.set_image(url=BANK_BANNER_URL)

        if not history:
            embed.description = "*Chưa ghi nhận giao dịch nào phát sinh trong tài khoản.*" if vi else "*No transactions recorded in this account yet.*"
        else:
            lines = []
            for tx in history[:10]:
                tx_type = tx["type"]
                amt = tx["amount"]
                time_str = f"<t:{tx['time']}:f>"
                if tx_type in ("DEPOSIT", "TERM_DEPOSIT", "REPAY_FULL", "REPAY_PART"):
                    tag = "🔻"
                    sign = "-"
                elif tx_type in ("WITHDRAW", "LOAN_DISBURSED", "SETTLEMENT", "EARLY_WITHDRAW"):
                    tag = "🟢"
                    sign = "+"
                else:
                    tag = "⚠️"
                    sign = "+"
                note_str = tx['note']
                time_lbl = "Thời gian" if vi else "Time"
                lines.append(f"{tag} **{sign}{amt:,} c** — *{note_str}*\n  └ {time_lbl}: {time_str}")
            embed.description = "\n".join(lines)

        view = BankHistoryView(self.author, self)
        await interaction.response.edit_message(embed=embed, view=view)


class BankCog(commands.Cog, name="Ngân Hàng"):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.hybrid_command(
        name="bank",
        aliases=["atm", "nganhang"],
        description="🏛️ Ngân Hàng: Tiết kiệm kỳ hạn, Vay vốn, Trả nợ & Lịch sử / Term savings & loans."
    )
    @commands.guild_only()
    async def bank_cmd(self, ctx: commands.Context):
        view = BankMainView(ctx.author, ctx.guild.id)
        embed = await view.build_main_embed()
        await ctx.send(embed=embed, view=view)


async def setup(bot: commands.Bot):
    await bot.add_cog(BankCog(bot))
