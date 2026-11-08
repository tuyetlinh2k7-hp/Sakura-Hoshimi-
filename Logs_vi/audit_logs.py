import discord
from discord.ext import commands
from Checks_vi.data import user_log_channels
from Checks_vi.i18n import t


class AuditLog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    async def _get_log_channel(self, guild: discord.Guild) -> discord.abc.Messageable | None:
        guild_id = str(guild.id)
        if guild_id not in user_log_channels:
            return None

        channel_id = int(user_log_channels[guild_id])
        channel = guild.get_channel(channel_id)
        if channel is None:
            try:
                channel = await self.bot.fetch_channel(channel_id)
            except (discord.NotFound, discord.Forbidden, discord.HTTPException):
                return None

        return channel if isinstance(channel, discord.abc.Messageable) else None

    def _get_action_color(self, action_name: str) -> discord.Color:
        if any(k in action_name for k in ("create", "add", "unban")):
            return discord.Color.green()
        if any(k in action_name for k in ("delete", "remove", "kick", "ban", "prune")):
            return discord.Color.red()
        return discord.Color.blurple()

    def _format_target(self, target) -> str:
        if target is None:
            return "*None*"
        if isinstance(target, discord.Object):
            return f"ID: `{target.id}`"

        mention = getattr(target, "mention", None)
        target_id = getattr(target, "id", None)
        name = getattr(target, "name", str(target))

        if mention and target_id:
            return f"{mention} (`{target_id}`)"
        if target_id:
            return f"`{name}` (`{target_id}`)"
        return str(target)

    @commands.Cog.listener()
    async def on_audit_log_entry_create(self, entry: discord.AuditLogEntry):
        guild = entry.guild
        log_channel = await self._get_log_channel(guild)
        if log_channel is None:
            return

        action_name = entry.action.name
        embed = discord.Embed(
            title=t(guild, "LOG_AUDIT_TITLE"),
            color=self._get_action_color(action_name),
            timestamp=entry.created_at or discord.utils.utcnow()
        )

        embed.add_field(
            name=t(guild, "LOG_AUDIT_FIELD_ACTION"),
            value=f"`{action_name.replace('_', ' ').title()}`",
            inline=True
        )

        if entry.user:
            user_val = f"{entry.user.mention} (`{entry.user.id}`)"
            embed.set_author(name=str(entry.user), icon_url=entry.user.display_avatar.url)
        elif entry.user_id:
            user_val = f"<@{entry.user_id}> (`{entry.user_id}`)"
        else:
            user_val = "*Unknown*"

        embed.add_field(
            name=t(guild, "LOG_AUDIT_FIELD_USER"),
            value=user_val,
            inline=True
        )

        if entry.target:
            embed.add_field(
                name=t(guild, "LOG_AUDIT_FIELD_TARGET"),
                value=self._format_target(entry.target),
                inline=False
            )

        if entry.reason:
            embed.add_field(
                name=t(guild, "LOG_AUDIT_FIELD_REASON"),
                value=entry.reason[:1024],
                inline=False
            )

        changes_list = []
        if entry.changes:
            for attr, before_val in entry.changes.before:
                if "permission" in attr or "flags" in attr:
                    continue

                after_val = getattr(entry.changes.after, attr, None)
                if before_val == after_val:
                    continue

                before_str = f"`{before_val}`" if before_val is not None else "*None*"
                after_str = f"`{after_val}`" if after_val is not None else "*None*"

                if len(before_str) > 200:
                    before_str = before_str[:196] + "...`"
                if len(after_str) > 200:
                    after_str = after_str[:196] + "...`"

                attr_title = attr.replace("_", " ").title()
                changes_list.append(f"**{attr_title}:** {before_str} → {after_str}")

        changes_text = "\n".join(changes_list)
        if len(changes_text) > 1024:
            changes_text = changes_text[:1021] + "..."

        embed.add_field(
            name=t(guild, "LOG_AUDIT_FIELD_CHANGES"),
            value=changes_text if changes_text else t(guild, "LOG_AUDIT_NO_CHANGES"),
            inline=False
        )

        embed.set_footer(text=t(guild, "LOG_AUDIT_FOOTER", id=entry.id))

        try:
            await log_channel.send(embed=embed)
        except (discord.Forbidden, discord.HTTPException):
            pass


async def setup(bot: commands.Bot):
    await bot.add_cog(AuditLog(bot))
