import discord
from discord import app_commands
from discord.ext import commands

from Check.i18n import t
from view.zodiac import ZodiacView, get_zodiac

class ZodiacCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.hybrid_command(name="cunghoangdao", aliases=["chd", "zodiac"], description="Tra cứu cung hoàng đạo và tính cách qua ngày tháng sinh")
    @app_commands.describe(ngay="Nhập ngày sinh của bạn (Ví dụ: 15)", thang="Nhập tháng sinh của bạn (Ví dụ: 8)")
    async def zodiac_check(self, ctx: commands.Context, ngay: int, thang: int):
        # Kiểm tra tính hợp lệ sơ bộ của ngày tháng
        if thang < 1 or thang > 12:
            return await ctx.send(t(ctx.guild, "ZODIAC_INVALID_MONTH"))
        if ngay < 1 or ngay > 31:
            return await ctx.send(t(ctx.guild, "ZODIAC_INVALID_DAY"))
        
        # Tìm cung hoàng đạo tương ứng
        zodiac_info = get_zodiac(ngay, thang)
        
        embed = discord.Embed(
            title=t(ctx.guild, "ZODIAC_RESULT_TITLE"),
            description=t(ctx.guild, "ZODIAC_RESULT_DESC", mention=ctx.author.mention, day=ngay, month=thang, emoji=zodiac_info['emoji'], name=zodiac_info['name'], dates=zodiac_info['dates']),
            color=zodiac_info["color"]
        )
        embed.set_thumbnail(url="https://i.imgur.com/E8W8f8O.png")
        
        view = ZodiacView(ctx.author, zodiac_info)
        await ctx.send(embed=embed, view=view)

async def setup(bot):
    await bot.add_cog(ZodiacCog(bot))
