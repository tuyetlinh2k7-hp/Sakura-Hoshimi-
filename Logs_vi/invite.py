import discord
from discord.ext import commands

from Check.data import invite_log_channels
from Check.i18n import t


class InviteLog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_invite_create(self, invite: discord.Invite):
        guild = invite.guild
        guild_id = str(guild.id)

        if guild_id not in invite_log_channels:
            return

        channel = self.bot.get_channel(invite_log_channels[guild_id])
        
        if channel is None:
            return

        embed = discord.Embed(
            title=t(guild, "LOG_INVITE_CREATED_TITLE"),
            color=discord.Color.green(),
            timestamp=discord.utils.utcnow()
        )

        embed.add_field(
            name=t(guild, "LOG_INVITE_FIELD_CODE"),
            value=f"`{invite.code}`",
            inline=True
        )

        embed.add_field(
            name=t(guild, "LOG_INVITE_FIELD_CHANNEL"),
            value=invite.channel.mention,
            inline=True
        )

        embed.add_field(
            name=t(guild, "LOG_INVITE_FIELD_INVITER"),
            value=invite.inviter.mention if invite.inviter else t(guild, "LOG_INVITE_UNKNOWN"),
            inline=False
        )

        embed.add_field(
            name=t(guild, "LOG_INVITE_FIELD_MAX_AGE"),
            value=f"{invite.max_age} seconds" if invite.max_age else t(guild, "LOG_INVITE_MAX_AGE_UNLIMITED"),
            inline=True
        )

        embed.add_field(
            name=t(guild, "LOG_INVITE_FIELD_MAX_USES"),
            value=invite.max_uses if invite.max_uses else t(guild, "LOG_INVITE_MAX_USES_UNLIMITED"),
            inline=True
        )

        embed.add_field(
            name=t(guild, "LOG_INVITE_FIELD_TEMPORARY"),
            value=str(invite.temporary),
            inline=True
        )

        try:
            await channel.send(embed=embed)
        except (discord.Forbidden, discord.HTTPException) as e:
            print(f"[InviteLog] Không thể gửi log invite tại #{channel.name}: {e}")

    @commands.Cog.listener()
    async def on_invite_delete(self, invite: discord.Invite):
        guild = invite.guild
        guild_id = str(guild.id)

        if guild_id not in invite_log_channels:
            return

        channel = self.bot.get_channel(invite_log_channels[guild_id])
        
        if channel is None:
            return
        
        embed = discord.Embed(
            title=t(guild, "LOG_INVITE_DELETED_TITLE"),
            color=discord.Color.red(),
            timestamp=discord.utils.utcnow()
        )

        embed.add_field(
            name=t(guild, "LOG_INVITE_FIELD_CODE"),
            value=f"`{invite.code}`",
            inline=True
        )

        embed.add_field(
            name=t(guild, "LOG_INVITE_FIELD_CHANNEL"),
            value=invite.channel.mention if invite.channel else t(guild, "LOG_INVITE_UNKNOWN"),
            inline=True
        )

        embed.add_field(
            name=t(guild, "LOG_INVITE_FIELD_INVITER"),
            value=invite.inviter.mention if invite.inviter else t(guild, "LOG_INVITE_UNKNOWN"),
            inline=False
        )

        try:
            await channel.send(embed=embed)
        except (discord.Forbidden, discord.HTTPException) as e:
            print(f"[InviteLog] Không thể gửi log invite tại #{channel.name}: {e}")

async def setup(bot: commands.Bot):
    await bot.add_cog(InviteLog(bot))
