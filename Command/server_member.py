import discord
from discord.ext import commands
from Check.data import voice_stats, save_data
from Check.i18n import t

class ServerMemberChecks(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.hybrid_command(
        name="setupstats",
        description="Cài đặt các kênh hiển thị thống kê số lượng thành viên (Voice Stats)."
    )
    async def setupstats(
        self,
        ctx: commands.Context, 
        all_channel: discord.VoiceChannel, 
        members_channel: discord.VoiceChannel, 
        bots_channel: discord.VoiceChannel
    ):
        if not ctx.guild:
            return await ctx.send(t(ctx.guild, "SERVERMEMBER_ONLY_GUILD"))

        guild_id = str(ctx.guild.id)

        voice_stats[guild_id] = {
            "all": all_channel.id,
            "members": members_channel.id,
            "bots": bots_channel.id
        }

        save_data()

        embed = discord.Embed(
            title=t(ctx.guild, "SERVERMEMBER_SETUP_TITLE"),
            description=t(ctx.guild, "SERVERMEMBER_SETUP_DESC"),
            color=discord.Color.green()
        )

        embed.add_field(name="👥 All Members", value=all_channel.mention, inline=False)
        embed.add_field(name="✨ Members", value=members_channel.mention, inline=False)
        embed.add_field(name="🤖 Bots", value=bots_channel.mention, inline=False)

        embed.set_footer(text=f"Server: {ctx.guild.name}")
        embed.set_thumbnail(url=ctx.guild.icon.url if ctx.guild.icon else None)

        await ctx.send(embed=embed)

async def setup(bot: commands.Bot):
    await bot.add_cog(ServerMemberChecks(bot))