import aiohttp
import discord
import random
import math
from discord.ext import commands
from discord import app_commands
from typing import Literal
from Checks_vi.i18n import t

ACTIONS = {
    "blush": "đỏ mặt", "cry": "khóc", "dance": "nhảy múa", "pout": "dỗi", "shrug": "nhún vai",
    "sleepy": "buồn ngủ", "smile": "mỉm cười", "smug": "đắc ý", "thinking": "suy nghĩ",
    "thonking": "suy nghĩ căng não", "triggered": "kích động", "teehee": "cười khúc khích", "working": "làm việc",
    "deredere": "dễ thương", "happy": "vui vẻ", "grin": "cười toe toét", "scoff": "cười khẩy",
    "laugh": "cười lớn", "giggle": "cười khúc khích", "facepalm": "bó tay", "confused": "bối rối",
    "angry": "tức giận", "sad": "buồn bã", "bored": "chán nản", "scared": "sợ hãi",
    "surprised": "ngạc nhiên", "shocked": "sốc", "embarrassed": "xấu hổ", "nervous": "hồi hộp",
    "excited": "phấn khích", "relaxed": "thư giãn", "yawn": "ngáp", "run": "chạy",
    "jump": "nhảy", "wave": "vẫy tay", "wink": "nháy mắt", "thumbsup": "giơ ngón tay cái",
    "clap": "vỗ tay", "cheer": "cổ vũ", "celebrate": "ăn mừng", "read": "đọc sách",
    "study": "học bài", "listen": "nghe nhạc", "sing": "ca hát",
    "sleep": "ngủ", "rest": "nghỉ ngơi", "drink": "uống nước", "eat": "ăn uống",
    "pray": "cầu nguyện", "meditate": "thiền định", "stargaze": "ngắm sao", "think": "suy tư"
}

ACTION_MAP = {
    "hug": "ôm", "kiss": "hôn", "pat": "xoa đầu", "poke": "chọc", "slap": "tát",
    "cuddle": "âu yếm", "bite": "cắn", "nom": "gặm", "lick": "liếm", "tickle": "cù lét",
    "highfive": "đập tay", "handhold": "nắm tay", "hold": "ôm chặt", "greet": "chào hỏi",
    "waveat": "vẫy tay với", "stare": "nhìn chằm chằm vào", "boop": "chạm mũi", "bonk": "cốc đầu",
    "punch": "đấm", "kick": "đá", "throw": "ném", "shoot": "bắn", "yeet": "quăng",
    "feed": "đút ăn", "gift": "tặng quà cho", "love": "thể hiện tình cảm với", "protect": "bảo vệ",
    "comfort": "an  ủi", "carry": "cõng", "escort": "hộ tống", "chase": "đuổi theo",
    "tap": "gõ nhẹ vào", "pet": "vuốt ve", "snuggle": "ôm ấp", "glomp": "lao vào ôm",
    "laughat": "cười vào mặt", "tease": "trêu chọc", "pokecheek": "chọc má", "pinch": "nhéo",
    "winkat": "nháy mắt với", "salute": "chào kiểu quân đội với", "respect": "thể hiện sự tôn trọng với",
}

ALL_ACTIONS = {**ACTION_MAP, **ACTIONS}

class ActionPaginationView(discord.ui.View):
    """View xử lý phân trang cho danh sách hành động"""
    def __init__(self, pages: list, user_id: int, guild=None):
        super().__init__(timeout=60)
        self.pages = pages
        self.user_id = user_id
        self.guild = guild
        self.current_page = 0
        # Update button labels with i18n if guild provided
        if guild is not None:
            try:
                self.btn_prev.label = t(guild, "ACTION_BTN_PREV")
                self.btn_next.label = t(guild, "ACTION_BTN_NEXT")
            except Exception:
                pass

    async def update_message(self, interaction: discord.Interaction):
        self.btn_prev.disabled = self.current_page == 0
        self.btn_next.disabled = self.current_page == len(self.pages) - 1
        await interaction.response.edit_message(embed=self.pages[self.current_page], view=self)

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id != self.user_id:
            await interaction.response.send_message(t(interaction.guild, "ACTION_INTERACTION_ONLY"), ephemeral=True)
            return False
        return True

    @discord.ui.button(label="◀ Trước", style=discord.ButtonStyle.secondary)
    async def btn_prev(self, interaction: discord.Interaction, button: discord.ui.Button):
        if self.current_page > 0:
            self.current_page -= 1
            await self.update_message(interaction)

    @discord.ui.button(label="Sau ▶", style=discord.ButtonStyle.primary)
    async def btn_next(self, interaction: discord.Interaction, button: discord.ui.Button):
        if self.current_page < len(self.pages) - 1:
            self.current_page += 1
            await self.update_message(interaction)


class Action(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.session = aiohttp.ClientSession()
        self.register_dynamic_prefix_commands()

    def cog_unload(self):
        self.bot.loop.create_task(self.session.close())

    def register_dynamic_prefix_commands(self):
        """Đăng ký động các lệnh dạng Prefix truyền thống"""
        for action in ALL_ACTIONS:
            if self.bot.get_command(action):
                continue

            def make_callback(action_name):
                async def callback(ctx, member: discord.Member = None):
                    await self.execute_action(ctx, action_name, member, is_slash=False)
                return callback

            self.bot.add_command(
                commands.Command(
                    make_callback(action),
                    name=action
                )
            )

    async def execute_action(self, ctx_or_interaction, action_name: str, member: discord.Member = None, is_slash: bool = False):
        """Hàm xử lý logic cốt lõi dùng chung cho cả Prefix và Slash Command"""
        # Xác định người gửi và guild tương ứng
        author = ctx_or_interaction.user if is_slash else ctx_or_interaction.author
        guild = ctx_or_interaction.guild

        # Defer trước vì gọi API lấy Gif có thể mất hơn 3 giây
        if is_slash:
            await ctx_or_interaction.response.defer()

        # Chuyển sang API purrbot.site
        gif = None
        try:
            async with self.session.get(f"https://purrbot.site/api/img/sfw/{action_name}/gif") as resp:
                if resp.status == 200:
                    data = await resp.json()
                    gif = data.get("link")
        except Exception as e:
            print(f"[❌ API ERROR] Lỗi khi lấy GIF cho {action_name} từ purrbot.site: {e}")

        if action_name in ACTION_MAP:
            if member is None:
                members = [m for m in guild.members if not m.bot and m != author]
                if not members:
                    embed = discord.Embed(
                        title=t(guild, "ACTION_NO_TARGET_TITLE"),
                        description=t(guild, "ACTION_NO_TARGET_DESC", author=author.display_name, action=ACTION_MAP[action_name]),
                        color=discord.Color.random()
                    )
                    if is_slash:
                        return await ctx_or_interaction.followup.send(embed=embed)
                    return await ctx_or_interaction.send(embed=embed)
                member = random.choice(members)

            embed = discord.Embed(
                description=t(guild, "ACTION_INTERACTIVE_DESC", author=author.display_name, action=ACTION_MAP[action_name], target=member.display_name),
                color=discord.Color.random()
            )
        else:
            embed = discord.Embed(
                description=t(guild, "ACTION_SOLO_DESC", author=author.display_name, action=ACTIONS[action_name]),
                color=discord.Color.random()
            )

        if gif:
            embed.set_image(url=gif)

        embed.set_footer(text=t(guild, "ACTION_FOOTER", action=action_name))
        
        if is_slash:
            await ctx_or_interaction.followup.send(embed=embed)
        else:
            await ctx_or_interaction.send(embed=embed)

    # --- 1. NHÓM LỆNH SLASH /action (Tối ưu hóa Slash Commands) ---
    action_group = app_commands.Group(name="action", description="Hệ thống tương tác hành động và cảm xúc")

    @action_group.command(name="do", description="Thực hiện một hành động tương tác hoặc trạng thái")
    @app_commands.describe(hành_động="Lựa chọn hành động mong muốn", thành_viên="Mục tiêu bạn muốn tương tác (nếu có)")
    async def slash_action_do(self, interaction: discord.Interaction, hành_động: str, thành_viên: discord.Member = None):
        if hành_động not in ALL_ACTIONS:
            await interaction.response.send_message(t(interaction.guild, "ACTION_INVALID"), ephemeral=True)
            return
        await self.execute_action(interaction, hành_động, thành_viên, is_slash=True)

    @slash_action_do.autocomplete("hành_động")
    async def action_autocomplete(self, interaction: discord.Interaction, current: str):
        """Hỗ trợ tự động hiển thị danh sách gợi ý (Autocomplete) khi gõ trên Discord"""
        return [
            app_commands.Choice(name=f"{k} ({v})", value=k)
            for k, v in ALL_ACTIONS.items() if current.lower() in k.lower() or current.lower() in v.lower()
        ][:25]

    @action_group.command(name="list", description="Xem toàn bộ danh sách hành động tích hợp sẵn")
    async def slash_action_list(self, interaction: discord.Interaction):
        pages = self.build_action_list_pages(interaction.guild)
        view = ActionPaginationView(pages, interaction.user.id, interaction.guild)
        view.btn_prev.disabled = True
        if len(pages) <= 1: view.btn_next.disabled = True
        await interaction.response.send_message(embed=pages[0], view=view)

    @action_group.command(name="wish", description="Bày tỏ mong muốn thực hiện hành động với ai đó")
    @app_commands.describe(action_name="Hành động mong muốn", member="Người bạn muốn tương tác")
    async def slash_action_wish(self, interaction: discord.Interaction, action_name: str, member: discord.Member):
        if action_name not in ACTION_MAP:
            await interaction.response.send_message(t(interaction.guild, "ACTION_MUON_NOT_INTERACTIVE"), ephemeral=True)
            return
        await self.execute_action(interaction, action_name, member, is_slash=True)

    @slash_action_wish.autocomplete("action_name")
    async def interaction_action_autocomplete(self, interaction: discord.Interaction, current: str):
        return [
            app_commands.Choice(name=f"{k} ({v})", value=k)
            for k, v in ACTION_MAP.items() if current.lower() in k.lower() or current.lower() in v.lower()
        ][:25]

    # --- 2. XEM DANH SÁCH HÀNH ĐỘNG (Có phân trang chống lỗi Embed 1024/6000 ký tự) ---
    def build_action_list_pages(self, guild=None) -> list:
        interaction_actions = sorted([f"`{k}` ({v})" for k, v in ACTION_MAP.items()])
        solo_actions = sorted([f"`{k}` ({v})" for k, v in ACTIONS.items()])

        # Chia nhỏ chuỗi lệnh để không bị tràn field của Embed
        def chunks(lst, n):
            for i in range(0, len(lst), n):
                yield lst[i:i + n]

        pages = []
        inter_chunks = list(chunks(interaction_actions, 15))
        solo_chunks = list(chunks(solo_actions, 15))
        
        max_pages = max(len(inter_chunks), len(solo_chunks))
        for i in range(max_pages):
            title = t(guild, "ACTION_LIST_TITLE") if guild else "📖 Danh sách Action công khai"
            embed = discord.Embed(title=title, color=discord.Color.purple())
            
            if i < len(inter_chunks):
                name1 = t(guild, "ACTION_LIST_NEED_USER") if guild else "👥 Cần @user (Tương tác)"
                embed.add_field(name=name1, value=", ".join(inter_chunks[i]), inline=False)
            if i < len(solo_chunks):
                name2 = t(guild, "ACTION_LIST_SOLO") if guild else "✨ Không cần @user (Đơn độc)"
                embed.add_field(name=name2, value=", ".join(solo_chunks[i]), inline=False)
                
            footer = t(guild, "ACTION_LIST_FOOTER", cur=i+1, total=max_pages, count=len(ALL_ACTIONS)) if guild else f"Trang {i+1}/{max_pages} | Tổng: {len(ALL_ACTIONS)} actions"
            embed.set_footer(text=footer)
            pages.append(embed)
        return pages

    @commands.command(name="actions_list")
    async def prefix_actions_list(self, ctx):
        pages = self.build_action_list_pages(ctx.guild)
        view = ActionPaginationView(pages, ctx.author.id, ctx.guild)
        view.btn_prev.disabled = True
        if len(pages) <= 1: view.btn_next.disabled = True
        await ctx.send(embed=pages[0], view=view)

    # --- 3. LỆNH MUỐN (!muon) ---
    @commands.command(aliases=["muốn"])
    async def muon(self, ctx, action_name=None, member: discord.Member = None):
        if not action_name or not member:
            return await ctx.send(t(ctx.guild, "ACTION_MUON_NEED_ARGS"))
        if action_name not in ACTION_MAP:
            return await ctx.send(t(ctx.guild, "ACTION_MUON_NOT_FOUND"))
        await self.execute_action(ctx, action_name, member, is_slash=False)

async def setup(bot):
    await bot.add_cog(Action(bot))
