import discord
from discord.ext import commands
from discord import app_commands
from typing import Union

from Check.mod import has_admin_role
from Check.i18n import t

class SayCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.hybrid_command(name="say", description="Gửi tin nhắn thay mặt bot đến một kênh chỉ định.")
    @app_commands.describe(
        kenh="Kênh bạn muốn gửi tin nhắn đến.",
        noi_dung="Nội dung tin nhắn bạn muốn gửi."
    )
    @has_admin_role()
    async def say(self, ctx: commands.Context, kenh: Union[discord.TextChannel, discord.VoiceChannel], *, noi_dung: str):
        """
        Gửi một tin nhắn đến một kênh cụ thể với tư cách là bot.
        Yêu cầu quyền admin của bot.
        """
        if not kenh.permissions_for(ctx.guild.me).send_messages:
            return await ctx.send(t(ctx.guild, "SAY_NO_PERM", channel=kenh.mention), ephemeral=True)

        try:
            await kenh.send(noi_dung)

            embed = discord.Embed(
                title=t(ctx.guild, "SAY_SUCCESS_TITLE"),
                description=t(ctx.guild, "SAY_SUCCESS_DESC", channel=kenh.mention),
                color=discord.Color.green()
            )
            embed.add_field(name=t(ctx.guild, "SAY_FIELD_CONTENT"), value=f"```{noi_dung}```", inline=False)
            embed.set_footer(text=t(ctx.guild, "SAY_FOOTER", name=ctx.author.display_name), icon_url=ctx.author.display_avatar.url)
            
            await ctx.send(embed=embed, ephemeral=True)
        except Exception as e:
            await ctx.send(t(ctx.guild, "SAY_ERROR", error=e), ephemeral=True)

    @say.error
    async def say_error(self, ctx: commands.Context, error: commands.CommandError):
        """Xử lý lỗi riêng cho lệnh say."""
        if isinstance(error, commands.BadUnionArgument):
            await ctx.send(
                t(ctx.guild, "SAY_BAD_CHANNEL"),
                ephemeral=True
            )
        else:
            print(f"Lỗi không xác định trong lệnh 'say': {error}")

async def setup(bot: commands.Bot):
    await bot.add_cog(SayCog(bot))
