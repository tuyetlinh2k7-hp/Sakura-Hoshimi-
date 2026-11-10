import discord
from discord.ext import commands
import os

from datetime import datetime
from Check.data import get_guild_settings
from Check.server_member import update_stats
from Check.i18n import t


class LeaveLog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_member_remove(self, member: discord.Member):
        await self.handle_goodbye(member)

    async def handle_goodbye(self, member: discord.Member):
        settings = get_guild_settings(member.guild.id)

        # nếu chưa đặt kênh tạm biệt thì tắt (Reine chọn Không đặt)
        if not settings or not settings.get("leave_channel"):
            return
        channel_id = settings.get("leave_channel")
        channel = member.guild.get_channel(channel_id) if channel_id else member.guild.system_channel
        if not channel:
            return

        join_duration = discord.utils.utcnow() - member.joined_at
        if join_duration.days > 0:
            duration_str = t(member.guild, "LOG_LEAVE_DURATION_DAYS", days=join_duration.days)
        else:
            hours, remainder = divmod(join_duration.seconds, 3600)
            duration_str = t(member.guild, "LOG_LEAVE_DURATION_HOURS", hours=hours) if hours > 0 else t(member.guild, "LOG_LEAVE_DURATION_SHORT")

        roles = [role.mention for role in member.roles if role.name != "@everyone"]
        roles_str = ", ".join(roles) if roles else t(member.guild, "LOG_LEAVE_NO_ROLES")

        custom_msg = settings.get("goodbye") or ""
        custom_img = settings.get("goodbye_image") or ""
        if custom_msg:
            desc = custom_msg.replace("{user}", member.mention).replace("{server}", member.guild.name).replace("{user_name}", member.display_name)
        else:
            desc = t(member.guild, "LOG_LEAVE_DESC", name=member.display_name)
        embed = discord.Embed(
            title=t(member.guild, "LOG_LEAVE_TITLE"),
            description=desc,
            color=discord.Color.dark_grey(),
            timestamp=discord.utils.utcnow()
        )

        embed.set_thumbnail(url=member.display_avatar.url)
        img_url = custom_img if custom_img.startswith("http") else "https://media.tenor.com/DLbH0i7N7yIAAAAd/bay-anime-bye-anime.gif"
        embed.set_image(url=img_url)
        embed.add_field(name=t(member.guild, "LOG_LEAVE_FIELD_MEMBER_COUNT"), value=f"`{member.guild.member_count}`", inline=True)
        embed.add_field(name=t(member.guild, "LOG_LEAVE_FIELD_DURATION"), value=f"`{duration_str}`", inline=True)
        embed.add_field(name=t(member.guild, "LOG_LEAVE_FIELD_ROLES"), value=roles_str, inline=False)
        embed.set_footer(text=t(member.guild, "LOG_LEAVE_FOOTER", id=member.id))

        try:
            await channel.send(embed=embed)
        except discord.Forbidden:
            print(t(member.guild, "LOG_LEAVE_ERROR_FORBIDDEN", channel=channel.name, guild=member.guild.name))
        await update_stats(member.guild)
       

async def setup(bot: commands.Bot):
    await bot.add_cog(LeaveLog(bot))
