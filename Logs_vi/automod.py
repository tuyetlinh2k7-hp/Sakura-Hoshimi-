import discord
from discord.ext import commands
from Checks_vi.data import automod_log_channels
from Checks_vi.i18n import t


class AutoModLog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    async def _get_log_channel(self, guild: discord.Guild) -> discord.abc.Messageable | None:
        guild_id = str(guild.id)
        if guild_id not in automod_log_channels:
            return None

        channel_id = int(automod_log_channels[guild_id])
        channel = guild.get_channel(channel_id)
        if channel is None:
            try:
                channel = await self.bot.fetch_channel(channel_id)
            except (discord.NotFound, discord.Forbidden, discord.HTTPException):
                return None

        return channel if isinstance(channel, discord.abc.Messageable) else None

    def _format_actions(self, actions: list[discord.AutoModRuleAction]) -> str:
        if not actions:
            return "*None*"
        lines = []
        for a in actions:
            action_name = a.type.name.replace("_", " ").title()
            details = []
            if a.channel_id:
                details.append(f"<#{a.channel_id}>")
            if a.duration:
                details.append(f"{int(a.duration.total_seconds())}s")
            if a.custom_message:
                details.append(f"\"{a.custom_message[:50]}\"")

            detail_str = f" ({', '.join(details)})" if details else ""
            lines.append(f"• `{action_name}`{detail_str}")
        return "\n".join(lines)[:1024]

    @commands.Cog.listener()
    async def on_automod_action(self, execution: discord.AutoModAction):
        guild = execution.guild
        channel = await self._get_log_channel(guild)
        if channel is None:
            return

        embed = discord.Embed(
            title=t(guild, "LOG_AUTOMOD_TRIGGERED_TITLE"),
            color=discord.Color.red(),
            timestamp=discord.utils.utcnow()
        )

        if execution.member:
            embed.set_thumbnail(url=execution.member.display_avatar.url)
            member_val = f"{execution.member.mention}\n`{execution.member.id}`"
        else:
            member_val = f"<@{execution.user_id}>\n`{execution.user_id}`"

        embed.add_field(
            name=t(guild, "LOG_AUTOMOD_FIELD_MEMBER"),
            value=member_val,
            inline=True
        )

        if execution.channel:
            channel_val = execution.channel.mention
        elif execution.channel_id:
            channel_val = f"<#{execution.channel_id}>"
        else:
            channel_val = "*None*"

        embed.add_field(
            name=t(guild, "LOG_AUTOMOD_FIELD_CHANNEL"),
            value=channel_val,
            inline=True
        )

        trigger_name = execution.rule_trigger_type.name.replace("_", " ").title()
        embed.add_field(
            name=t(guild, "LOG_AUTOMOD_FIELD_RULE"),
            value=f"ID: `{execution.rule_id}`\nTrigger: `{trigger_name}`",
            inline=True
        )

        action_type_name = execution.action.type.name.replace("_", " ").title()
        action_detail = f"`{action_type_name}`"
        if execution.action.duration:
            action_detail += f" (`{int(execution.action.duration.total_seconds())}s`)"

        embed.add_field(
            name=t(guild, "LOG_AUTOMOD_FIELD_ACTION"),
            value=action_detail,
            inline=False
        )

        if execution.content:
            embed.add_field(
                name=t(guild, "LOG_AUTOMOD_FIELD_CONTENT"),
                value=execution.content[:1024],
                inline=False
            )

        if execution.matched_content:
            embed.add_field(
                name=t(guild, "LOG_AUTOMOD_FIELD_MATCHED_CONTENT"),
                value=execution.matched_content[:1024],
                inline=True
            )

        if execution.matched_keyword:
            embed.add_field(
                name=t(guild, "LOG_AUTOMOD_FIELD_MATCHED_KEYWORD"),
                value=f"`{execution.matched_keyword[:1000]}`",
                inline=True
            )

        try:
            await channel.send(embed=embed)
        except (discord.Forbidden, discord.HTTPException) as e:
            print(t(guild, "LOG_AUTOMOD_ERROR_SEND", error=e))

    @commands.Cog.listener()
    async def on_automod_rule_create(self, rule: discord.AutoModRule):
        guild = rule.guild
        channel = await self._get_log_channel(guild)
        if channel is None:
            return

        embed = discord.Embed(
            title=t(guild, "LOG_AUTOMOD_RULE_CREATED_TITLE"),
            color=discord.Color.green(),
            timestamp=discord.utils.utcnow()
        )

        embed.add_field(
            name=t(guild, "LOG_AUTOMOD_FIELD_RULE_NAME"),
            value=f"**{rule.name}**",
            inline=True
        )
        embed.add_field(
            name=t(guild, "LOG_AUTOMOD_FIELD_RULE_ID"),
            value=f"`{rule.id}`",
            inline=True
        )
        embed.add_field(
            name=t(guild, "LOG_AUTOMOD_FIELD_ENABLED"),
            value=f"`{rule.enabled}`",
            inline=True
        )
        embed.add_field(
            name=t(guild, "LOG_AUTOMOD_FIELD_TRIGGER_TYPE"),
            value=f"`{rule.trigger.type.name.replace('_', ' ').title()}`",
            inline=True
        )
        embed.add_field(
            name=t(guild, "LOG_AUTOMOD_FIELD_EVENT_TYPE"),
            value=f"`{rule.event_type.name.replace('_', ' ').title()}`",
            inline=True
        )

        creator_val = (
            f"<@{rule.creator_id}> (`{rule.creator_id}`)"
            if rule.creator_id
            else t(guild, "LOG_EMOJI_UNKNOWN")
        )
        embed.add_field(
            name=t(guild, "LOG_AUTOMOD_FIELD_CREATOR_ID"),
            value=creator_val,
            inline=False
        )
        embed.add_field(
            name=t(guild, "LOG_AUTOMOD_FIELD_ACTIONS"),
            value=self._format_actions(rule.actions),
            inline=False
        )

        try:
            await channel.send(embed=embed)
        except (discord.Forbidden, discord.HTTPException):
            pass

    @commands.Cog.listener()
    async def on_automod_rule_update(self, rule: discord.AutoModRule):
        guild = rule.guild
        channel = await self._get_log_channel(guild)
        if channel is None:
            return

        embed = discord.Embed(
            title=t(guild, "LOG_AUTOMOD_RULE_UPDATED_TITLE"),
            color=discord.Color.orange(),
            timestamp=discord.utils.utcnow()
        )

        embed.add_field(
            name=t(guild, "LOG_AUTOMOD_FIELD_RULE2"),
            value=f"**{rule.name}** (`{rule.id}`)",
            inline=False
        )
        embed.add_field(
            name=t(guild, "LOG_AUTOMOD_FIELD_STATUS"),
            value=f"Enabled: `{rule.enabled}`",
            inline=True
        )
        embed.add_field(
            name=t(guild, "LOG_AUTOMOD_FIELD_TRIGGER"),
            value=f"`{rule.trigger.type.name.replace('_', ' ').title()}`",
            inline=True
        )
        embed.add_field(
            name=t(guild, "LOG_AUTOMOD_FIELD_ACTIONS2"),
            value=self._format_actions(rule.actions),
            inline=False
        )

        embed.set_footer(text=t(guild, "LOG_AUTOMOD_FOOTER_GUILD", id=rule.guild.id))

        try:
            await channel.send(embed=embed)
        except (discord.Forbidden, discord.HTTPException):
            pass

    @commands.Cog.listener()
    async def on_automod_rule_delete(self, rule: discord.AutoModRule):
        guild = rule.guild
        channel = await self._get_log_channel(guild)
        if channel is None:
            return

        embed = discord.Embed(
            title=t(guild, "LOG_AUTOMOD_RULE_DELETED_TITLE"),
            color=discord.Color.dark_red(),
            timestamp=discord.utils.utcnow()
        )

        embed.add_field(
            name=t(guild, "LOG_AUTOMOD_FIELD_RULE2"),
            value=f"**{rule.name}** (`{rule.id}`)",
            inline=False
        )
        embed.add_field(
            name=t(guild, "LOG_AUTOMOD_FIELD_TRIGGER"),
            value=f"`{rule.trigger.type.name.replace('_', ' ').title()}`",
            inline=True
        )

        embed.set_footer(text=t(guild, "LOG_AUTOMOD_FOOTER_GUILD", id=rule.guild.id))

        try:
            await channel.send(embed=embed)
        except (discord.Forbidden, discord.HTTPException):
            pass


async def setup(bot: commands.Bot):
    await bot.add_cog(AutoModLog(bot))
