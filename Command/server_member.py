import discord
from discord.ext import commands
from Check.data import voice_stats, save_data
from Check.i18n import t

class ServerMemberChecks(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    # Chuyển đổi thành hybrid_command
    @commands.hybrid_command(
        name="setupstats",
        description="Cài đặt các kênh hiển thị thống kê số lượng thành viên (Voice Stats)."
    )
    # Thêm type hints đầy đủ để Discord Slash Command tự động nhận diện tham số là các Voice Channel
    async def setupstats(
        self, # Bắt buộc phải có 'self' trong Cog
        ctx: commands.Context, 
        all_channel: discord.VoiceChannel, 
        members_channel: discord.VoiceChannel, 
        bots_channel: discord.VoiceChannel
    ):
        # Kiểm tra nếu lệnh được dùng ngoài Server (trong DM)
        if not ctx.guild:
            return await ctx.send(t(ctx.guild, "SERVERMEMBER_ONLY_GUILD"))

        guild_id = str(ctx.guild.id)

        # Lưu dữ liệu cấu hình vào dict
        voice_stats[guild_id] = {
            "all": all_channel.id,
            "members": members_channel.id,
            "bots": bots_channel.id
        }

        # Lưu vào file cứng
        save_data()

        # Tạo giao diện Embed thông báo kết quả
        embed = discord.Embed(
            title=t(ctx.guild, "SERVERMEMBER_SETUP_TITLE"),
            description=t(ctx.guild, "SERVERMEMBER_SETUP_DESC"),
            color=discord.Color.green() # Đổi sang màu xanh lá cho đồng bộ thành công
        )

        embed.add_field(name="👥 All Members", value=all_channel.mention, inline=False)
        embed.add_field(name="✨ Members", value=members_channel.mention, inline=False)
        embed.add_field(name="🤖 Bots", value=bots_channel.mention, inline=False)

        embed.set_footer(text=f"Server: {ctx.guild.name}")
        embed.set_thumbnail(url=ctx.guild.icon.url if ctx.guild.icon else None)

        # Gửi phản hồi phù hợp với ngữ cảnh (Prefix / Slash)
        await ctx.send(embed=embed)

async def setup(bot: commands.Bot): # Đổi tên hàm setup này để tránh trùng tên với lệnh 'setup' bên trên
    await bot.add_cog(ServerMemberChecks(bot))