import discord
import random
import time
from Checks.data import save_data
from Check.i18n import t

class LeaderboardView(discord.ui.View):
    def __init__(self, author: discord.Member, level_pages: list, coin_pages: list):
        super().__init__(timeout=120)  # Tự hủy sau 120 giây
        self.author = author
        self.level_pages = level_pages
        self.coin_pages = coin_pages
        self.current_page_index = 0
        self.current_leaderboard = "level"  # Bắt đầu với bảng xếp hạng level

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        # Chỉ cho phép người gọi lệnh tương tác
        if interaction.user.id != self.author.id:
            await interaction.response.send_message(t(interaction.guild, "ECONOMY_NOT_YOURS"), ephemeral=True)
            return False
        return True

    async def update_message(self, interaction: discord.Interaction):
        """Hàm chung để cập nhật tin nhắn với trang và các nút bấm hiện tại."""
        pages = self.level_pages if self.current_leaderboard == "level" else self.coin_pages
        
        # Cập nhật trạng thái các nút
        self.btn_prev.disabled = self.current_page_index == 0
        self.btn_next.disabled = self.current_page_index >= len(pages) - 1
        self.btn_level.disabled = self.current_leaderboard == "level"
        self.btn_coin.disabled = self.current_leaderboard == "coin"

        await interaction.response.edit_message(embed=pages[self.current_page_index], view=self)

    @discord.ui.button(label="⭐ Top Level", style=discord.ButtonStyle.primary, custom_id="lb_level", disabled=True)
    async def btn_level(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.current_leaderboard = "level"
        self.current_page_index = 0  # Reset về trang đầu tiên khi đổi bảng
        await self.update_message(interaction)

    @discord.ui.button(label="🪙 Top Coins", style=discord.ButtonStyle.primary, custom_id="lb_coin")
    async def btn_coin(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.current_leaderboard = "coin"
        self.current_page_index = 0
        await self.update_message(interaction)

    @discord.ui.button(label="◀ Trước", style=discord.ButtonStyle.secondary, custom_id="lb_prev")
    async def btn_prev(self, interaction: discord.Interaction, button: discord.ui.Button):
        if self.current_page_index > 0:
            self.current_page_index -= 1
            await self.update_message(interaction)

    @discord.ui.button(label="Sau ▶", style=discord.ButtonStyle.secondary, custom_id="lb_next")
    async def btn_next(self, interaction: discord.Interaction, button: discord.ui.Button):
        pages = self.level_pages if self.current_leaderboard == "level" else self.coin_pages
        if self.current_page_index < len(pages) - 1:
            self.current_page_index += 1
            await self.update_message(interaction)
            
    async def on_timeout(self):
        # Vô hiệu hóa tất cả các nút khi hết thời gian
        for item in self.children:
            item.disabled = True
        try:
            if self.message:
                await self.message.edit(content=t(message.guild, "ECONOMY_EXPIRED"), view=self)
        except discord.NotFound:
            pass


#==============================================================
# VIEW CỦA DAILY
#==============================================================
class ClaimView(discord.ui.View):
    def __init__(self, author: discord.Member, economy_cog):
        super().__init__(timeout=180) # Tự hủy sau 3 phút
        self.author = author
        self.economy_cog = economy_cog # Để truy cập các hàm của Economy Cog
        self.message = None

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        # Chỉ cho phép người gọi lệnh tương tác
        if interaction.user.id != self.author.id:
            await interaction.response.send_message(t(interaction.guild, "ECONOMY_CLAIM_NOT_YOURS"), ephemeral=True)
            return False
        return True

    async def update_view(self, interaction: discord.Interaction):
        """Cập nhật lại Embed và trạng thái các nút bấm."""
        user_data = self.economy_cog.get_user_data(str(self.author.id))
        embed = self.economy_cog.create_claim_embed(user_data)
        
        # Cập nhật trạng thái các nút
        now = time.time()
        self.daily_button.disabled = (now - user_data.get("daily_last", 0)) < 86400
        self.weekly_button.disabled = (now - user_data.get("weekly_last", 0)) < 604800
        self.monthly_button.disabled = (now - user_data.get("monthly_last", 0)) < 2592000

        await interaction.response.edit_message(embed=embed, view=self)

    @discord.ui.button(label="Nhận Daily", style=discord.ButtonStyle.success, emoji="🎁")
    async def daily_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        user = self.economy_cog.get_user_data(str(self.author.id))
        now = time.time()
        
        if now - user.get("daily_last", 0) < 86400:
            await interaction.response.send_message("Bạn đang trong thời gian chờ nhận Daily!", ephemeral=True)
            return

        # Logic tính streak
        if now - user.get("daily_last", 0) <= 172800: # trong vòng 48h
            user["daily_streak"] = user.get("daily_streak", 0) + 1
        else:
            user["daily_streak"] = 1

        base_reward = random.randint(500, 1000)
        streak_bonus = user["daily_streak"] * 100
        total = base_reward + streak_bonus

        user["coins"] += total
        user["daily_last"] = now
        save_data()

        await interaction.response.send_message(f"✅ Bạn đã nhận thành công `{total:,}` xu từ phần thưởng Daily! (Chuỗi: `{user['daily_streak']}` ngày)", ephemeral=True)
        await self.update_view(interaction) # Cập nhật lại giao diện chính

    @discord.ui.button(label="Nhận Weekly", style=discord.ButtonStyle.primary, emoji="📦")
    async def weekly_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        user = self.economy_cog.get_user_data(str(self.author.id))
        now = time.time()

        if now - user.get("weekly_last", 0) < 604800:
            await interaction.response.send_message("Bạn đang trong thời gian chờ nhận Weekly!", ephemeral=True)
            return

        reward = random.randint(5000, 20000)
        user["coins"] += reward
        user["weekly_last"] = now
        save_data()

        await interaction.response.send_message(f"✅ Bạn đã nhận thành công `{reward:,}` xu từ phần thưởng Weekly!", ephemeral=True)
        await self.update_view(interaction)

    @discord.ui.button(label="Nhận Monthly", style=discord.ButtonStyle.secondary, emoji="💎")
    async def monthly_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        user = self.economy_cog.get_user_data(str(self.author.id))
        now = time.time()

        if now - user.get("monthly_last", 0) < 2592000:
            await interaction.response.send_message("Bạn đang trong thời gian chờ nhận Monthly!", ephemeral=True)
            return

        reward = random.randint(20000, 100000)
        user["coins"] += reward
        user["monthly_last"] = now
        save_data()

        await interaction.response.send_message(f"✅ Bạn đã nhận thành công `{reward:,}` xu từ phần thưởng Monthly!", ephemeral=True)
        await self.update_view(interaction)
        
    async def on_timeout(self):
        for item in self.children:
            item.disabled = True
        try:
            if self.message:
                await self.message.edit(content=t(message.guild, "ECONOMY_CLAIM_EXPIRED"), view=self)
        except discord.NotFound:
            pass

# VIEW XÁC NHẬN CHUYỂN TIỀN
class TransferConfirmationView(discord.ui.View):
    def __init__(self, author: discord.Member):
        super().__init__(timeout=30) # Giao dịch tự hủy sau 30 giây
        self.author = author
        self.value = None # Lưu trữ kết quả (True: đồng ý, False: hủy)

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        # Chỉ cho phép người gọi lệnh tương tác
        if interaction.user.id != self.author.id:
            await interaction.response.send_message(t(interaction.guild, "ECONOMY_TRANSFER_NOT_YOURS"), ephemeral=True)
            return False
        return True

    @discord.ui.button(label="Xác nhận chuyển", style=discord.ButtonStyle.green, emoji="✅")
    async def confirm(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.value = True
        self.stop()

    @discord.ui.button(label="Hủy", style=discord.ButtonStyle.danger, emoji="❌")
    async def cancel(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.value = False
        self.stop()