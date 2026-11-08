import discord

from data.data import ZODIAC_DATA
from Checks_vi.i18n import t

def get_zodiac(day: int, month: int):
    # Quy đổi ngày tháng nhập vào thành 1 mã số nguyên duy nhất để so sánh
    date_code = month * 100 + day
    
    # Duyệt qua các cung (trừ Ma Kết có chu kỳ vắt năm)
    for z in ZODIAC_DATA[:-1]:
        if z["start_code"] <= date_code <= z["end_code"]:
            return z
            
    # Nếu không thuộc các cung trên, mặc định rơi vào chu kỳ Ma Kết (22/12 - 19/01)
    return ZODIAC_DATA[-1]


class ZodiacDropdown(discord.ui.Select):
    def __init__(self, zodiac_info):
        self.zodiac_info = zodiac_info
        options = [
            discord.SelectOption(label="🎭 Xem Tính Cách", description="Bản chất, ưu và nhược điểm", value="personality"),
            discord.SelectOption(label="❤️ Xem Tình Duyên", description="Quan điểm yêu và cách chọn người yêu", value="love"),
            discord.SelectOption(label="💼 Xem Sự Nghiệp", description="Lĩnh vực phù hợp và lộ trình thăng tiến", value="work")
        ]
        super().__init__(placeholder="🌟 Chọn khía cạnh bạn muốn khám phá...", min_values=1, max_values=1, options=options)

    async def callback(self, interaction: discord.Interaction):
        aspect = self.values[0]
        titles = {"personality": "🎭 TÍNH CÁCH BẢN NĂNG", "love": "❤️ VẬN TRÌNH TÌNH DUYÊN", "work": "💼 LỘ TRÌNH SỰ NGHIỆP"}
        
        embed = discord.Embed(
            title=f"{self.zodiac_info['emoji']} {self.zodiac_info['name']} ({self.zodiac_info['dates']})",
            description=f"🔮 **Khía cạnh:** `{titles[aspect]}`\n\n{self.zodiac_info[aspect]}",
            color=self.zodiac_info["color"]
        )
        embed.set_footer(text=f"Khám phá bởi {interaction.user.name}", icon_url=interaction.user.display_avatar.url)
        
        # Giữ lại menu để người chơi có thể bấm xem khía cạnh khác nếu muốn
        await interaction.response.edit_message(embed=embed, view=self.view)

class ZodiacView(discord.ui.View):
    def __init__(self, author: discord.User, zodiac_info):
        super().__init__(timeout=90)
        self.author = author
        self.add_item(ZodiacDropdown(zodiac_info))

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user != self.author:
            await interaction.response.send_message(t(interaction.guild, "ZODIAC_NOT_YOURS"), ephemeral=True)
            return False
        return True