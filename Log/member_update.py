import discord
from discord.ext import commands
from Check.data import member_log_channels
from Check.i18n import t


class MemberLog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    async def _get_log_channel(self, guild: discord.Guild) -> discord.abc.Messageable | None:
        guild_id = str(guild.id)
        if guild_id not in member_log_channels:
            return None

        channel_id = int(member_log_channels[guild_id])
        channel = guild.get_channel(channel_id)
        if channel is None:
            try:
                channel = await self.bot.fetch_channel(channel_id)
            except (discord.NotFound, discord.Forbidden, discord.HTTPException):
                return None

        return channel if isinstance(channel, discord.abc.Messageable) else None

    def _create_base_embed(
        self, user: discord.Member | discord.User, guild: discord.Guild, title: str, color: discord.Color
    ) -> discord.Embed:
        embed = discord.Embed(
            title=title,
            color=color,
            timestamp=discord.utils.utcnow()
        )
        embed.set_thumbnail(url=user.display_avatar.url)
        embed.add_field(
            name=t(guild, "LOG_MEMBER_FIELD_MEMBER"),
            value=f"{user.mention} (`{user.id}`)",
            inline=False
        )
        embed.set_footer(text=t(guild, "LOG_MEMBER_FOOTER", id=user.id))
        return embed

    @commands.Cog.listener()
    async def on_member_update(self, before: discord.Member, after: discord.Member):
        guild = after.guild
        log_channel = await self._get_log_channel(guild)
        if log_channel is None:
            return

        embeds_to_send: list[discord.Embed] = []

        if before.nick != after.nick:
            embed = self._create_base_embed(
                after, guild, t(guild, "LOG_MEMBER_NICK_TITLE"), discord.Color.orange()
            )
            embed.add_field(
                name=t(guild, "LOG_MEMBER_FIELD_BEFORE"),
                value=f"`{before.nick}`" if before.nick else t(guild, "LOG_MEMBER_NONE"),
                inline=True
            )
            embed.add_field(
                name=t(guild, "LOG_MEMBER_FIELD_AFTER"),
                value=f"`{after.nick}`" if after.nick else t(guild, "LOG_MEMBER_NONE"),
                inline=True
            )
            embeds_to_send.append(embed)

        if before.roles != after.roles:
            before_set = set(before.roles)
            after_set = set(after.roles)
            added_roles = list(after_set - before_set)
            removed_roles = list(before_set - after_set)

            if added_roles or removed_roles:
                embed = self._create_base_embed(
                    after, guild, t(guild, "LOG_MEMBER_ROLES_TITLE"), discord.Color.blue()
                )
                if added_roles:
                    added_str = ", ".join(r.mention for r in added_roles)
                    embed.add_field(
                        name=t(guild, "LOG_MEMBER_FIELD_ADDED_ROLES"),
                        value=added_str[:1024],
                        inline=False
                    )
                if removed_roles:
                    removed_str = ", ".join(r.mention for r in removed_roles)
                    embed.add_field(
                        name=t(guild, "LOG_MEMBER_FIELD_REMOVED_ROLES"),
                        value=removed_str[:1024],
                        inline=False
                    )
                embeds_to_send.append(embed)

        if before.timed_out_until != after.timed_out_until:
            embed = self._create_base_embed(
                after, guild, t(guild, "LOG_MEMBER_TIMEOUT_TITLE"), discord.Color.red()
            )
            if after.is_timed_out() and after.timed_out_until:
                embed.description = t(
                    guild,
                    "LOG_MEMBER_TIMEOUT_DESC_MUTED",
                    time=discord.utils.format_dt(after.timed_out_until, style="F")
                )
            else:
                embed.description = t(guild, "LOG_MEMBER_TIMEOUT_DESC_REMOVED")
            embeds_to_send.append(embed)

        if before.guild_avatar != after.guild_avatar:
            embed = self._create_base_embed(
                after, guild, t(guild, "LOG_MEMBER_AVATAR_TITLE"), discord.Color.blurple()
            )
            if after.guild_avatar:
                embed.set_image(url=after.guild_avatar.url)
            else:
                embed.description = t(guild, "LOG_MEMBER_AVATAR_DESC_REMOVED")
            embeds_to_send.append(embed)

        if before.pending != after.pending:
            embed = self._create_base_embed(
                after, guild, t(guild, "LOG_MEMBER_SCREENING_TITLE"), discord.Color.green()
            )
            verified_status = (
                t(guild, "LOG_MEMBER_VERIFIED_YES")
                if not after.pending
                else t(guild, "LOG_MEMBER_VERIFIED_NO")
            )
            embed.add_field(
                name=t(guild, "LOG_MEMBER_FIELD_VERIFIED"),
                value=verified_status,
                inline=False
            )
            embeds_to_send.append(embed)

        if before.premium_since != after.premium_since:
            if after.premium_since and not before.premium_since:
                embed = self._create_base_embed(
                    after, guild, t(guild, "LOG_MEMBER_BOOST_NEW_TITLE"), discord.Color.nitro_pink()
                )
                embed.description = t(guild, "LOG_MEMBER_BOOST_NEW_DESC", mention=after.mention)
                embeds_to_send.append(embed)
            elif before.premium_since and not after.premium_since:
                embed = self._create_base_embed(
                    after, guild, t(guild, "LOG_MEMBER_BOOST_REMOVED_TITLE"), discord.Color.light_grey()
                )
                embed.description = t(guild, "LOG_MEMBER_BOOST_REMOVED_DESC", mention=after.mention)
                embeds_to_send.append(embed)

        if before.public_flags != after.public_flags:
            embed = self._create_base_embed(
                after, guild, t(guild, "LOG_MEMBER_BADGES_TITLE"), discord.Color.teal()
            )
            flags_before = [f.name.replace("_", " ").title() for f in before.public_flags.all()]
            flags_after = [f.name.replace("_", " ").title() for f in after.public_flags.all()]

            embed.add_field(
                name=t(guild, "LOG_MEMBER_FIELD_BEFORE"),
                value=", ".join(flags_before) if flags_before else t(guild, "LOG_MEMBER_NONE"),
                inline=True
            )
            embed.add_field(
                name=t(guild, "LOG_MEMBER_FIELD_AFTER"),
                value=", ".join(flags_after) if flags_after else t(guild, "LOG_MEMBER_NONE"),
                inline=True
            )
            embeds_to_send.append(embed)

        if embeds_to_send:
            try:
                await log_channel.send(embeds=embeds_to_send[:10])
            except (discord.Forbidden, discord.HTTPException):
                pass

    @commands.Cog.listener()
    async def on_user_update(self, before: discord.User, after: discord.User):
        """Bắt sự kiện thay đổi hồ sơ gốc (Username, Global Name, Avatar gốc)."""
        if (
            before.name == after.name
            and before.global_name == after.global_name
            and before.avatar == after.avatar
        ):
            return

        for guild in after.mutual_guilds:
            log_channel = await self._get_log_channel(guild)
            if log_channel is None:
                continue

            embeds_to_send: list[discord.Embed] = []

            if before.name != after.name or before.global_name != after.global_name:
                embed = self._create_base_embed(
                    after, guild, t(guild, "LOG_USER_NAME_TITLE"), discord.Color.gold()
                )
                before_display = f"{before.global_name or before.name} (`@{before.name}`)"
                after_display = f"{after.global_name or after.name} (`@{after.name}`)"

                embed.add_field(
                    name=t(guild, "LOG_MEMBER_FIELD_BEFORE"),
                    value=before_display,
                    inline=True
                )
                embed.add_field(
                    name=t(guild, "LOG_MEMBER_FIELD_AFTER"),
                    value=after_display,
                    inline=True
                )
                embeds_to_send.append(embed)

            if before.avatar != after.avatar:
                embed = self._create_base_embed(
                    after, guild, t(guild, "LOG_USER_AVATAR_TITLE"), discord.Color.purple()
                )
                if after.avatar:
                    embed.set_image(url=after.avatar.url)
                else:
                    embed.description = t(guild, "LOG_MEMBER_AVATAR_DESC_REMOVED")
                embeds_to_send.append(embed)

            if embeds_to_send:
                try:
                    await log_channel.send(embeds=embeds_to_send[:10])
                except (discord.Forbidden, discord.HTTPException):
                    pass


async def setup(bot: commands.Bot):
    await bot.add_cog(MemberLog(bot))
