import discord
from discord.ext import commands
from discord import app_commands
from typing import Union

# Import check quyền admin từ file khác
from Check.mod import has_admin_role
from Check.i18n import t

class SayCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.hybrid_command(name="say", description="Gửi tin nhắn thay mặt bot đến một kênh chỉ định.") # en: Send a message as the bot to a specified channel.
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
        # Kiểm tra xem bot có quyền gửi tin nhắn trong kênh đó không
        if not kenh.permissions_for(ctx.guild.me).send_messages:
            return await ctx.send(t(ctx.guild, "SAY_NO_PERM", channel=kenh.mention), ephemeral=True)

        try:
            # Gửi tin nhắn
            await kenh.send(noi_dung)

            # Gửi phản hồi xác nhận cho người dùng
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
        # Bắt lỗi khi người dùng nhập kênh không hợp lệ
        if isinstance(error, commands.BadUnionArgument):
            await ctx.send(
                t(ctx.guild, "SAY_BAD_CHANNEL"),
                ephemeral=True
            )
        # Đối với các lỗi khác, có thể in ra để debug
        else:
            print(f"Lỗi không xác định trong lệnh 'say': {error}")

async def setup(bot: commands.Bot):
    await bot.add_cog(SayCog(bot))
