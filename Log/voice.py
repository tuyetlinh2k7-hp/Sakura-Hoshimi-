import asyncio
import time
import discord
from discord.ext import commands
from Check.data import voice_log_channels, voice_stats, CREATE_CHANNEL_ID
from view.voice import VoicePanel
from Check.voice import temp_channels
from Check.i18n import t


class VoiceLog(commands.Cog):
    CREATE_COOLDOWN = 10.0

    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self._join_times: dict[tuple[int, int], float] = {}
        self._create_cooldowns: dict[tuple[int, int], float] = {}

    async def _get_log_channel(self, guild: discord.Guild) -> discord.abc.Messageable | None:
        guild_id = str(guild.id)
        if guild_id not in voice_log_channels:
            return None

        channel_id = int(voice_log_channels[guild_id])
        channel = guild.get_channel(channel_id)
        if channel is None:
            try:
                channel = await self.bot.fetch_channel(channel_id)
            except (discord.NotFound, discord.Forbidden, discord.HTTPException):
                return None

        return channel if isinstance(channel, discord.abc.Messageable) else None

    def _create_log_embed(
        self, member: discord.Member, title: str, color: discord.Color
    ) -> discord.Embed:
        guild = member.guild
        embed = discord.Embed(
            title=title,
            color=color,
            timestamp=discord.utils.utcnow()
        )
        embed.set_thumbnail(url=member.display_avatar.url)
        embed.add_field(
            name=t(guild, "LOG_VOICE_FIELD_MEMBER"),
            value=f"{member.mention} (`{member.id}`)",
            inline=False
        )
        embed.set_footer(text=t(guild, "LOG_VOICE_FOOTER", id=member.id))
        return embed

    def _format_duration(self, seconds: int) -> str:
        hours, remainder = divmod(seconds, 3600)
        minutes, secs = divmod(remainder, 60)
        parts = []
        if hours > 0:
            parts.append(f"{hours}h")
        if minutes > 0:
            parts.append(f"{minutes}m")
        parts.append(f"{secs}s")
        return " ".join(parts)

    def _record_voice_time(self, guild_id: str, member_id: int) -> int:
        key = (int(guild_id), member_id)
        start_time = self._join_times.pop(key, None)
        if start_time is None:
            return 0

        duration = max(0, int(time.time() - start_time))
        if duration > 0 and isinstance(voice_stats, dict):
            guild_stats = voice_stats.setdefault(guild_id, {})
            user_key = str(member_id)
            guild_stats[user_key] = guild_stats.get(user_key, 0) + duration

        return duration

    def _get_human_members(self, channel: discord.VoiceChannel | discord.StageChannel) -> list[discord.Member]:
        """Trả về danh sách thành viên là người thật trong kênh (loại trừ tất cả Bot)."""
        return [m for m in channel.members if not m.bot]

    @commands.Cog.listener()
    async def on_ready(self):
        """Khôi phục mốc tính giờ và tự động dọn kênh Temp Voice chỉ còn Bot hoặc trống khi khởi động."""
        now = time.time()
        for guild in self.bot.guilds:
            for vc in guild.voice_channels:
                for member in vc.members:
                    if not member.bot:
                        self._join_times.setdefault((guild.id, member.id), now)

            for chan_id in list(temp_channels.keys()):
                channel = guild.get_channel(chan_id)
                if channel and len(self._get_human_members(channel)) == 0:
                    temp_channels.pop(chan_id, None)
                    try:
                        await channel.delete(reason="Temp voice cleanup on startup (no human members)")
                    except (discord.NotFound, discord.Forbidden, discord.HTTPException):
                        pass

    @commands.Cog.listener()
    async def on_voice_state_update(
        self, member: discord.Member, before: discord.VoiceState, after: discord.VoiceState
    ):
        if before.channel == after.channel:
            return

        guild = member.guild
        guild_id = str(guild.id)
        raw_create_id = CREATE_CHANNEL_ID.get(guild_id)
        create_voice_id = int(raw_create_id) if raw_create_id else None

        session_duration = 0
        if not member.bot:
            if before.channel is None and after.channel is not None:
                self._join_times[(guild.id, member.id)] = time.time()
            elif before.channel is not None and after.channel is None:
                session_duration = self._record_voice_time(guild_id, member.id)

        log_channel = await self._get_log_channel(guild)
        if log_channel:
            embed = None
            is_entering_lobby = create_voice_id and after.channel and after.channel.id == create_voice_id
            is_leaving_lobby = create_voice_id and before.channel and before.channel.id == create_voice_id

            if not is_entering_lobby:
                if (before.channel is None or is_leaving_lobby) and after.channel is not None:
                    embed = self._create_log_embed(
                        member, t(guild, "LOG_VOICE_JOIN_TITLE"), discord.Color.green()
                    )
                    embed.add_field(
                        name=t(guild, "LOG_VOICE_FIELD_CHANNEL"),
                        value=after.channel.mention,
                        inline=False
                    )

                elif before.channel is not None and after.channel is None:
                    embed = self._create_log_embed(
                        member, t(guild, "LOG_VOICE_LEAVE_TITLE"), discord.Color.red()
                    )
                    embed.add_field(
                        name=t(guild, "LOG_VOICE_FIELD_CHANNEL"),
                        value=before.channel.mention,
                        inline=True
                    )
                    if session_duration > 0:
                        embed.add_field(
                            name="⏱️ Duration",
                            value=f"`{self._format_duration(session_duration)}`",
                            inline=True
                        )

                elif before.channel is not None and after.channel is not None:
                    embed = self._create_log_embed(
                        member, t(guild, "LOG_VOICE_SWITCH_TITLE"), discord.Color.orange()
                    )
                    embed.add_field(
                        name=t(guild, "LOG_VOICE_FIELD_BEFORE"),
                        value=before.channel.mention,
                        inline=True
                    )
                    embed.add_field(
                        name=t(guild, "LOG_VOICE_FIELD_AFTER"),
                        value=after.channel.mention,
                        inline=True
                    )

            if embed:
                try:
                    await log_channel.send(embed=embed)
                except (discord.Forbidden, discord.HTTPException):
                    pass

        if before.channel and before.channel.id in temp_channels:
            old_channel_id = before.channel.id
            await asyncio.sleep(1)
            channel = guild.get_channel(old_channel_id)

            if channel:
                human_members = self._get_human_members(channel)
                if len(human_members) == 0:
                    temp_channels.pop(channel.id, None)
                    try:
                        await channel.delete(reason="Temp voice empty (only bots or no members left)")
                    except (discord.NotFound, discord.Forbidden, discord.HTTPException):
                        pass

                elif temp_channels.get(channel.id) == member.id:
                    new_owner = human_members[0]
                    temp_channels[channel.id] = new_owner.id
                    try:
                        await channel.set_permissions(member, overwrite=None)
                        await channel.set_permissions(
                            new_owner,
                            manage_channels=True,
                            manage_permissions=True,
                            move_members=True,
                            mute_members=True,
                            deafen_members=True,
                            priority_speaker=True
                        )
                    except (discord.Forbidden, discord.HTTPException):
                        pass

        if not create_voice_id or after.channel is None or after.channel.id != create_voice_id:
            return

        if member.bot:
            return

        now = time.time()
        cooldown_key = (guild.id, member.id)
        last_created = self._create_cooldowns.get(cooldown_key, 0.0)

        if now - last_created < self.CREATE_COOLDOWN:
            try:
                await member.move_to(None, reason="Temp voice creation cooldown active")
            except (discord.Forbidden, discord.HTTPException):
                pass
            return

        self._create_cooldowns[cooldown_key] = now

        overwrites = {
            guild.default_role: discord.PermissionOverwrite(
                connect=True,
                view_channel=True
            ),
            guild.me: discord.PermissionOverwrite(
                view_channel=True,
                connect=True,
                manage_channels=True,
                manage_permissions=True,
                move_members=True
            ),
            member: discord.PermissionOverwrite(
                manage_channels=True,
                manage_permissions=True,
                move_members=True,
                mute_members=True,
                deafen_members=True,
                priority_speaker=True
            )
        }

        try:
            new_channel = await guild.create_voice_channel(
                name=t(guild, "LOG_VOICE_TEMP_NAME", name=member.display_name)[:100],
                category=after.channel.category,
                overwrites=overwrites,
                reason=f"Temp voice created by {member}"
            )
        except (discord.Forbidden, discord.HTTPException):
            return

        temp_channels[new_channel.id] = member.id

        try:
            await member.move_to(new_channel)
        except (discord.Forbidden, discord.HTTPException):
            temp_channels.pop(new_channel.id, None)
            try:
                await new_channel.delete(reason="Creator left before move completed")
            except (discord.NotFound, discord.Forbidden, discord.HTTPException):
                pass
            return

        embed = discord.Embed(
            title=t(guild, "LOG_VOICE_PANEL_TITLE"),
            description=t(guild, "LOG_VOICE_PANEL_DESC"),
            color=discord.Color.blurple(),
            timestamp=discord.utils.utcnow()
        )
        embed.add_field(
            name=t(guild, "LOG_VOICE_PANEL_FIELD_OWNER"),
            value=t(guild, "LOG_VOICE_PANEL_FIELD_OWNER_VALUE"),
            inline=True
        )
        embed.add_field(
            name=t(guild, "LOG_VOICE_PANEL_FIELD_ACCESS"),
            value=t(guild, "LOG_VOICE_PANEL_FIELD_ACCESS_VALUE"),
            inline=True
        )
        embed.add_field(
            name=t(guild, "LOG_VOICE_PANEL_FIELD_MEMBER"),
            value=t(guild, "LOG_VOICE_PANEL_FIELD_MEMBER_VALUE"),
            inline=False
        )
        embed.add_field(
            name=t(guild, "LOG_VOICE_PANEL_FIELD_NOTE"),
            value=t(guild, "LOG_VOICE_PANEL_FIELD_NOTE_VALUE"),
            inline=False
        )
        embed.set_image(
            url="https://cdn.discordapp.com/attachments/1518122337981960234/1518122676269481994/68747470733a2f2f73332e616d617a6f6e6177732e636f6d2f776174747061642d6d656469612d736572766963652f53746f7279496d6167652f6a6e6149584c465352715f3248673d3d2d36322e313464653439323232386239346631663935343835343431363632312e.gif?ex=6a38c56b&is=6a3773eb&hm=711a3455afd6f91afd1f07eec1d105ab0c8b03bf873880ce7b5e96cfe3d79a2a&"
        )
        embed.set_thumbnail(
            url="https://genk.mediacdn.vn/2018/12/12/photo-1-1544593039044211895467.gif"
        )

        if self.bot.user:
            embed.set_footer(
                text=t(guild, "LOG_VOICE_PANEL_FOOTER"),
                icon_url=self.bot.user.display_avatar.url
            )

        try:
            await new_channel.send(embed=embed, view=VoicePanel())
        except (discord.Forbidden, discord.HTTPException):
            pass


async def setup(bot: commands.Bot):
    await bot.add_cog(VoiceLog(bot))
