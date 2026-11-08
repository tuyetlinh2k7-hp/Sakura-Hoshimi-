import discord
from discord.ext import commands

from Checks_vi.i18n import t
from view.tarot import TarotMenuView

class Tarot(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    # --- SỰ KIỆN LỆNH MỚI: BÓI BÀI TAROT TIÊN TRI ---
    @commands.command(aliases=["tarot", "boibai", "card"])
    async def tarot_draw(self, ctx):
        """Lệnh gọi Menu rút bài bói toán huyền bí"""
        embed = discord.Embed(
            title=t(ctx.guild, "TAROT_TITLE"),
            description=t(ctx.guild, "TAROT_DESC", mention=ctx.author.mention),
            color=0x6c5ce7
        )
        embed.set_footer(text=t(ctx.guild, "TAROT_FOOTER"))
        
        view = TarotMenuView()
        await ctx.send(embed=embed, view=view)

async def setup(bot: commands.Bot):
    await bot.add_cog(Tarot(bot))
