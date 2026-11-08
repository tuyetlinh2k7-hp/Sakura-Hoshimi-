

import discord
from Checks_vi.i18n import t


class ConfirmModerationView(discord.ui.View):
    def __init__(self, author: discord.User):
        super().__init__(timeout=30) # Tự động hủy sau 30 giây nếu không ai bấm
        self.author = author
        self.value = None # Lưu kết quả lựa chọn (True = Xác nhận, False = Hủy)

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id != self.author.id:
            await interaction.response.send_message(t(interaction.guild, "MOD_NOT_YOURS"), ephemeral=True)
            return False
        return True
    @discord.ui.button(label="Xác nhận 🟥", style=discord.ButtonStyle.danger)
    async def confirm(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.value = True
        self.stop()
        await interaction.response.defer()

    @discord.ui.button(label="Hủy bỏ 🟩", style=discord.ButtonStyle.secondary)
    async def cancel(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.value = False
        self.stop()
        await interaction.response.defer()

    async def on_timeout(self):
        self.stop()