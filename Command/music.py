from wavelink.node import logger
import discord
import wavelink
import re
import datetime
import asyncio
import json
import math
from pathlib import Path
from typing import Literal, Optional
from discord.ext import commands
from discord import app_commands

from config import LAVALINK_HOST, LAVALINK_PORT, LAVALINK_PASSWORD, OWNER_ID
from Check.mod import admin_roles
from Check.i18n import t

BASE_DIR = Path(__file__).resolve().parent.parent
FAV_FILE = BASE_DIR / "data" / "music_favorites.json"
user_favorites: dict[str, list[dict]] = {}

def load_favorites():
    global user_favorites
    if FAV_FILE.exists():
        try:
            with open(FAV_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                if isinstance(data, dict):
                    user_favorites.update(data)
        except Exception:
            pass

def save_favorites():
    FAV_FILE.parent.mkdir(parents=True, exist_ok=True)
    try:
        with open(FAV_FILE, "w", encoding="utf-8") as f:
            json.dump(user_favorites, f, indent=4, ensure_ascii=False)
    except Exception:
        pass

load_favorites()

def is_music_admin(member: discord.Member) -> bool:
    if member.id in (OWNER_ID, member.guild.owner_id):
        return True
    if member.guild_permissions.administrator:
        return True
    guild_admins = admin_roles.get(str(member.guild.id), [])
    return any(role.id in guild_admins for role in member.roles)


class MusicControlView(discord.ui.View):
    def __init__(self, player: "CustomPlayer"):
        super().__init__(timeout=None)
        self.player = player

    async def _update_message(self, interaction: discord.Interaction):
        if self.player.current and self.player.bound_channel:
            embed = self.player.build_now_playing_embed(self.player.current)
            await self.player.safe_edit_panel(embed, self)

    @discord.ui.button(label="Pause/Resume", style=discord.ButtonStyle.primary, emoji="⏯️", row=0)
    async def pause_resume_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not interaction.user.voice or interaction.user.voice.channel != self.player.channel:
            return await interaction.response.send_message("❌ Bạn cần ở trong cùng kênh thoại với bot!", ephemeral=True)
        if self.player.paused:
            await self.player.pause(False)
            await interaction.response.send_message("▶️ Đã tiếp tục phát nhạc.", ephemeral=True)
        else:
            await self.player.pause(True)
            await interaction.response.send_message("⏸️ Đã tạm dừng phát nhạc.", ephemeral=True)
        await self._update_message(interaction)

    @discord.ui.button(label="Skip", style=discord.ButtonStyle.secondary, emoji="⏭️", row=0)
    async def skip_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not interaction.user.voice or interaction.user.voice.channel != self.player.channel:
            return await interaction.response.send_message("❌ Bạn cần ở trong cùng kênh thoại với bot!", ephemeral=True)
        if not self.player.playing:
            return await interaction.response.send_message("❌ Không có bài hát nào đang phát.", ephemeral=True)
        
        member = interaction.user
        is_owner = self.player.current and getattr(self.player.current, "requester", None) == member
        if not is_owner and not is_music_admin(member):
            humans = [m for m in self.player.channel.members if not m.bot]
            if len(humans) >= 3:
                uid = member.id
                if uid not in self.player.skip_votes:
                    self.player.skip_votes.add(uid)
                needed = math.ceil(len(humans) / 2)
                if len(self.player.skip_votes) < needed:
                    return await interaction.response.send_message(f"🗳️ Đã ghi nhận phiếu bầu bỏ qua ({len(self.player.skip_votes)}/{needed}). Cần {needed} phiếu.", ephemeral=True)
        
        self.player.skip_votes.clear()
        await self.player.skip(force=True)
        cog = interaction.client.get_cog("Music")
        if cog and hasattr(cog, "play_next"):
            await cog.play_next(self.player)
        await interaction.response.send_message("⏭️ Đã bỏ qua bài hát hiện tại.", ephemeral=True)

    @discord.ui.button(label="Loop", style=discord.ButtonStyle.secondary, emoji="🔂", row=0)
    async def loop_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not interaction.user.voice or interaction.user.voice.channel != self.player.channel:
            return await interaction.response.send_message("❌ Bạn cần ở trong cùng kênh thoại với bot!", ephemeral=True)
        if self.player.queue.mode == wavelink.QueueMode.normal:
            self.player.queue.mode = wavelink.QueueMode.loop
            await interaction.response.send_message("🔂 Bật lặp bài hiện tại.", ephemeral=True)
        elif self.player.queue.mode == wavelink.QueueMode.loop:
            self.player.queue.mode = wavelink.QueueMode.loop_all
            await interaction.response.send_message("🔁 Bật lặp toàn bộ hàng đợi.", ephemeral=True)
        else:
            self.player.queue.mode = wavelink.QueueMode.normal
            await interaction.response.send_message("🔄 Đã tắt chế độ lặp.", ephemeral=True)
        await self._update_message(interaction)

    @discord.ui.button(label="Shuffle", style=discord.ButtonStyle.secondary, emoji="🔀", row=0)
    async def shuffle_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not interaction.user.voice or interaction.user.voice.channel != self.player.channel:
            return await interaction.response.send_message("❌ Bạn cần ở trong cùng kênh thoại với bot!", ephemeral=True)
        if self.player.queue.is_empty:
            return await interaction.response.send_message("❌ Hàng đợi đang trống.", ephemeral=True)
        self.player.queue.shuffle()
        await interaction.response.send_message("🔀 Đã xáo trộn hàng đợi!", ephemeral=True)
        await self._update_message(interaction)

    @discord.ui.button(label="Stop", style=discord.ButtonStyle.danger, emoji="⏹️", row=0)
    async def stop_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not interaction.user.voice or interaction.user.voice.channel != self.player.channel:
            return await interaction.response.send_message("❌ Bạn cần ở trong cùng kênh thoại với bot!", ephemeral=True)
        self.player.queue.clear()
        self.player.auto_tracks_pool.clear()
        await self.player.cleanup_panel()
        await self.player.disconnect()
        await interaction.response.send_message("⏹️ Đã dừng phát nhạc.", ephemeral=True)

    @discord.ui.button(label="Vol -", style=discord.ButtonStyle.secondary, emoji="🔉", row=1)
    async def vol_down_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        from Command.vote import require_vote_or_notify
        if not await require_vote_or_notify(interaction, "Giảm Âm Lượng Nhạc (Vol -)"):
            return
        if not interaction.user.voice or interaction.user.voice.channel != self.player.channel:
            return await interaction.response.send_message("❌ Bạn cần ở trong cùng kênh thoại với bot!", ephemeral=True)
        current_vol = self.player.volume
        new_vol = max(0, current_vol - 10)
        await self.player.set_volume(new_vol)
        await interaction.response.send_message(f"🔉 Đã giảm âm lượng xuống: **{new_vol}%**", ephemeral=True)
        await self._update_message(interaction)

    @discord.ui.button(label="Vol +", style=discord.ButtonStyle.secondary, emoji="🔊", row=1)
    async def vol_up_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        from Command.vote import require_vote_or_notify
        if not await require_vote_or_notify(interaction, "Tăng Âm Lượng Nhạc (Vol +)"):
            return
        if not interaction.user.voice or interaction.user.voice.channel != self.player.channel:
            return await interaction.response.send_message("❌ Bạn cần ở trong cùng kênh thoại với bot!", ephemeral=True)
        current_vol = self.player.volume
        new_vol = min(200, current_vol + 10)
        await self.player.set_volume(new_vol)
        await interaction.response.send_message(f"🔊 Đã tăng âm lượng lên: **{new_vol}%**", ephemeral=True)
        await self._update_message(interaction)

    @discord.ui.button(label="Fav", style=discord.ButtonStyle.secondary, emoji="❤️", row=1)
    async def fav_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not self.player.current:
            return await interaction.response.send_message("❌ Không có bài hát nào đang phát!", ephemeral=True)
        uid = str(interaction.user.id)
        user_favs = user_favorites.setdefault(uid, [])
        track = self.player.current
        if any(f["uri"] == track.uri for f in user_favs):
            return await interaction.response.send_message("⚠️ Bài hát này đã có trong danh sách yêu thích của bạn!", ephemeral=True)
        user_favs.append({"title": track.title, "uri": track.uri})
        save_favorites()
        await interaction.response.send_message(f"❤️ Đã thêm **{track.title}** vào danh sách yêu thích!", ephemeral=True)

    @discord.ui.button(label="Chuyển sang TTS", style=discord.ButtonStyle.secondary, emoji="🤖", row=1)
    async def tts_toggle_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not interaction.user.voice or not interaction.user.voice.channel:
            return await interaction.response.send_message("❌ Bạn cần ở trong kênh thoại để chuyển sang TTS!", ephemeral=True)

        await interaction.response.defer(ephemeral=True)
        guild = interaction.guild
        guild_id = interaction.guild_id
        target_voice = interaction.user.voice.channel

        try:
            from Check.tts_checks import voice_text_channels, tts_playing, play_announcement
            self.player.queue.clear()
            self.player.auto_tracks_pool.clear()
            await self.player.cleanup_panel()
            try:
                await self.player.disconnect()
            except Exception:
                pass
            try:
                self.player.cleanup()
            except Exception:
                pass
            try:
                guild._state._remove_voice_client(guild.id)
            except Exception:
                pass
            try:
                await guild.change_voice_state(channel=None)
            except Exception:
                pass
            await asyncio.sleep(0.4)

            try:
                await target_voice.connect(timeout=30, reconnect=True, self_deaf=True)
            except discord.ClientException:
                guild._state._remove_voice_client(guild.id)
                await asyncio.sleep(0.3)
                await target_voice.connect(timeout=30, reconnect=True, self_deaf=True)

            voice_text_channels[guild_id] = interaction.channel.id
            tts_playing[guild_id] = False

            await interaction.followup.send(
                f"🟢 Đã dừng nhạc và **bật ưu tiên TTS** tại kênh {interaction.channel.mention} (Phòng thoại: {target_voice.mention})!",
                ephemeral=True
            )
            await play_announcement(guild, "Sakura đã chuyển sang chế độ đọc tin nhắn", interaction.client)
        except Exception as e:
            await interaction.followup.send(f"⚠️ Không thể chuyển sang chế độ TTS: `{e}`", ephemeral=True)


class CustomPlayer(wavelink.Player):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.bound_channel: discord.TextChannel | None = None
        self.bound_guild = None
        self.current_panel_message: discord.Message | None = None
        self.history: list[wavelink.Playable] = []
        self.skip_votes: set[int] = set()
        self.autoplay_enabled: bool = True
        self.auto_tracks_pool: list[wavelink.Playable] = []
        self._edit_lock = asyncio.Lock()
        self._progress_task: Optional[asyncio.Task] = None

    async def cleanup_panel(self):
        if self._progress_task and not self._progress_task.done():
            self._progress_task.cancel()
            self._progress_task = None
        if self.current_panel_message:
            try:
                await self.current_panel_message.delete()
            except Exception:
                pass
            self.current_panel_message = None

    async def fetch_autoplay_pool(self, seed_title: str):
        try:
            clean_title = re.sub(r'\(.*?\)|\[.*?\]|ft\..*|feat\..*|official video|lyrics', '', seed_title, flags=re.IGNORECASE).strip()
            search_query = f"ytsearch:{clean_title} audio"
            tracks = await wavelink.Playable.search(search_query)
            if not tracks:
                tracks = await wavelink.Playable.search(f"ytsearch:{clean_title}")
            if tracks:
                self.auto_tracks_pool = [t for t in tracks if t.uri][:25]
        except Exception:
            self.auto_tracks_pool = []

    def build_now_playing_embed(self, track: wavelink.Playable) -> discord.Embed:
        guild = getattr(self.bound_channel, 'guild', self.bound_guild)
        
        node_status = "🟢 Connected"
        try:
            node = wavelink.Pool.get_node()
            node_status = f"🟢 Connected ({node.identifier})"
        except Exception:
            node_status = "🔴 Disconnected"

        state_str = "⏸️ Tạm dừng" if self.paused else "▶️ Đang phát"
        loop_mode_map = {
            wavelink.QueueMode.normal: "🔄 Tắt lặp",
            wavelink.QueueMode.loop: "🔂 Lặp bài hiện tại",
            wavelink.QueueMode.loop_all: "🔁 Lặp toàn bộ hàng đợi"
        }
        loop_str = loop_mode_map.get(self.queue.mode, "🔄 Tắt lặp")

        pos_ms = self.position
        len_ms = track.length
        pos_str = str(datetime.timedelta(milliseconds=pos_ms))[:7]
        dur_str = str(datetime.timedelta(milliseconds=len_ms))[:7]
        
        length = 12
        percent = max(0.0, min(1.0, pos_ms / len_ms)) if len_ms > 0 else 0
        filled = int(length * percent)
        bar = "▬" * length
        if filled > 0:
            bar = "🔘" + "▬" * (filled - 1) + bar[filled:]
        else:
            bar = "🔘" + bar[1:]
        progress_bar = f"[{bar}] `{pos_str} / {dur_str}`"

        requester = getattr(track, "requester", None)
        req_name = requester.mention if requester else "Tự động phát (Autoplay)"

        next_track_title = "Không có"
        if not self.queue.is_empty:
            next_track_title = self.queue[0].title
        elif self.autoplay_enabled and self.auto_tracks_pool:
            next_track_title = f"{self.auto_tracks_pool[0].title} (Tự động)"

        total_tracks_count = len(self.queue) + (len(self.auto_tracks_pool) if self.autoplay_enabled else 0)

        embed = discord.Embed(
            title=t(guild, "MUSIC_NOW_PLAYING_TITLE"),
            description=f"🎶 **[{track.title}]({track.uri})**",
            color=discord.Color.from_rgb(138, 43, 226),
            timestamp=discord.utils.utcnow()
        )

        me = guild.me if guild else None
        if me and me.display_avatar:
            embed.set_thumbnail(url=me.display_avatar.url)

        if track.artwork:
            embed.set_image(url=track.artwork)

        embed.add_field(name="⏳ Tiến trình", value=progress_bar, inline=False)
        embed.add_field(name="👤 Người yêu cầu", value=req_name, inline=True)
        embed.add_field(name="🔊 Âm lượng", value=f"`{self.volume}%`", inline=True)
        embed.add_field(name="🎛️ Trạng thái", value=f"{state_str} | {loop_str}", inline=False)
        embed.add_field(name="🌐 Lavalink Node", value=node_status, inline=True)
        embed.add_field(name="📊 Hàng đợi", value=f"`{len(self.queue)}` ưu tiên (`{total_tracks_count}` tổng)", inline=True)
        embed.add_field(name="⏭️ Bài tiếp theo", value=f"*{next_track_title}*", inline=False)
        embed.set_footer(text="✨ Sakura Music System • Trải nghiệm âm nhạc tuyệt vời cùng bạn!", icon_url=guild.icon.url if guild and guild.icon else None)
        return embed

    async def safe_edit_panel(self, embed: discord.Embed, view: Optional[discord.ui.View] = None):
        async with self._edit_lock:
            try:
                if self.current_panel_message:
                    if view is not None:
                        await self.current_panel_message.edit(embed=embed, view=view)
                    else:
                        await self.current_panel_message.edit(embed=embed)
            except discord.HTTPException:
                pass

    async def _progress_loop(self):
        try:
            while self.playing:
                await asyncio.sleep(15)
                if not self.playing:
                    break
                if self.paused:
                    continue
                if self.bound_channel and self.current:
                    embed = self.build_now_playing_embed(self.current)
                    await self.safe_edit_panel(embed)
        except asyncio.CancelledError:
            pass

    async def send_now_playing(self, track: wavelink.Playable):
        self.skip_votes.clear()
        await self.cleanup_panel()

        if self.bound_channel:
            embed = self.build_now_playing_embed(track)
            view = MusicControlView(self)
            self.current_panel_message = await self.bound_channel.send(embed=embed, view=view)
            self._progress_task = asyncio.create_task(self._progress_loop())


class MusicControllerCog(commands.Cog, name="Music"):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    async def cog_load(self) -> None:
        asyncio.create_task(self._connect_lavalink_with_retry())

    async def _connect_lavalink_with_retry(self):
        try:
            if wavelink.Pool.get_node():
                return
        except Exception:
            pass

        delay = 2
        while True:
            node = wavelink.Node(
                uri=f"http://{LAVALINK_HOST}:{LAVALINK_PORT}",
                password=LAVALINK_PASSWORD
            )
            try:
                await wavelink.Pool.connect(client=self.bot, nodes=[node])
                break
            except Exception:
                await asyncio.sleep(delay)
                delay = min(delay * 2, 60)

    @commands.Cog.listener()
    async def on_voice_state_update(self, member: discord.Member, before: discord.VoiceState, after: discord.VoiceState):
        if member.bot:
            return
        if before.channel and before.channel != after.channel:
            vc = before.channel.guild.voice_client
            if isinstance(vc, CustomPlayer) and vc.channel == before.channel:
                humans = [m for m in before.channel.members if not m.bot]
                if len(humans) == 0:
                    await asyncio.sleep(30)
                    if vc.connected and vc.channel:
                        remaining = [m for m in vc.channel.members if not m.bot]
                        if len(remaining) == 0:
                            vc.queue.clear()
                            vc.auto_tracks_pool.clear()
                            await vc.cleanup_panel()
                            await vc.disconnect()

    @commands.Cog.listener()
    async def on_wavelink_track_start(self, payload: wavelink.TrackStartEventPayload) -> None:
        player: CustomPlayer | None = payload.player
        if player and payload.track:
            if not player.history or player.history[-1] != payload.track:
                player.history.append(payload.track)
                if len(player.history) > 10:
                    player.history.pop(0)
            await player.send_now_playing(payload.track)

    async def play_next(self, player: CustomPlayer):
        if not player or not player.connected:
            return

        while not player.queue.is_empty:
            try:
                next_track = player.queue.get()
                await player.play(next_track)
                return
            except Exception as e:
                logger.warning(f"Không thể phát bài từ hàng đợi: {e}")
                continue

        if player.autoplay_enabled:
            if not player.auto_tracks_pool and player.history:
                last_track = player.history[-1]
                await player.fetch_autoplay_pool(last_track.title)

            while player.auto_tracks_pool:
                next_track = player.auto_tracks_pool.pop(0)
                try:
                    await player.play(next_track)
                    return
                except Exception as e:
                    logger.warning(f"Lỗi khi phát bài autoplay: {e}")
                    continue

        asyncio.create_task(self._auto_disconnect_empty(player))

    @commands.Cog.listener()
    async def on_wavelink_track_end(self, payload: wavelink.TrackEndEventPayload) -> None:
        player: CustomPlayer | None = payload.player
        if not player or not player.connected:
            return
        if payload.reason == "cleanup":
            return

        if player.queue.mode == wavelink.QueueMode.loop and payload.track and payload.reason != "replaced":
            try:
                return await player.play(payload.track)
            except Exception:
                pass

        if player.queue.mode == wavelink.QueueMode.loop_all and payload.track:
            if getattr(payload.track, "requester", None) is not None:
                await player.queue.put_wait(payload.track)

        await self.play_next(player)

    @commands.Cog.listener()
    async def on_wavelink_track_exception(self, payload: wavelink.TrackExceptionEventPayload) -> None:
        player: CustomPlayer | None = payload.player
        if player and player.connected:
            logger.warning(f"Lavalink Track Exception trên Guild {player.guild}: {payload.exception}")
            await self.play_next(player)

    @commands.Cog.listener()
    async def on_wavelink_track_stuck(self, payload: wavelink.TrackStuckEventPayload) -> None:
        player: CustomPlayer | None = payload.player
        if player and player.connected:
            logger.warning(f"Lavalink Track Stuck trên Guild {player.guild}")
            await self.play_next(player)

    async def _auto_disconnect_empty(self, player: CustomPlayer):
        await asyncio.sleep(60)
        if player and player.connected and not player.playing and player.queue.is_empty:
            try:
                player.auto_tracks_pool.clear()
                await player.cleanup_panel()
                await player.disconnect()
            except Exception:
                pass

    def _is_tts_active(self, guild: discord.Guild) -> bool:
        try:
            from Check.tts_checks import voice_text_channels, tts_playing
            vc = guild.voice_client
            if vc and isinstance(vc, discord.VoiceClient) and not isinstance(vc, CustomPlayer) and vc.is_connected():
                if guild.id in voice_text_channels or tts_playing.get(guild.id, False):
                    return True
            return False
        except Exception:
            return False

    async def get_player(self, ctx: commands.Context) -> CustomPlayer | None:
        if not ctx.author.voice:
            embed = discord.Embed(title="⚠️ Cảnh Báo", description=t(ctx.guild, "MUSIC_NEED_VOICE"), color=discord.Color.orange())
            await ctx.send(embed=embed, ephemeral=True)
            return None

        if self._is_tts_active(ctx.guild):
            embed = discord.Embed(
                title="🌸 Hệ Thống TTS Đang Được Ưu Tiên",
                description="Bot hiện đang đọc tin nhắn (TTS) trong kênh thoại.\nVui lòng tắt TTS trước bằng lệnh `/tts off` nếu bạn muốn chuyển sang phát nhạc!",
                color=0xffb6c1
            )
            await ctx.send(embed=embed, ephemeral=True)
            return None

        try:
            wavelink.Pool.get_node()
        except Exception:
            embed = discord.Embed(title="❌ Lỗi Kết Nối Lavalink", description="Hiện chưa có Node Lavalink nào kết nối thành công! Vui lòng kiểm tra lại dịch vụ Lavalink.", color=discord.Color.red())
            await ctx.send(embed=embed, ephemeral=True)
            return None

        voice_channel = ctx.author.voice.channel
        guild_me = ctx.guild.me if ctx.guild else None
        if guild_me:
            perms = voice_channel.permissions_for(guild_me)
            if not perms.connect:
                embed = discord.Embed(
                    title="🚫 Thiếu Quyền Tham Gia",
                    description=f"Bot không có quyền tham gia kênh thoại **{voice_channel.name}** (`Connect`)! Vui lòng cấp quyền cho bot.",
                    color=discord.Color.red()
                )
                await ctx.send(embed=embed, ephemeral=True)
                return None
            if not perms.speak:
                embed = discord.Embed(
                    title="🚫 Thiếu Quyền Phát Âm",
                    description=f"Bot không có quyền nói (`Speak`) trong kênh thoại **{voice_channel.name}**!",
                    color=discord.Color.red()
                )
                await ctx.send(embed=embed, ephemeral=True)
                return None
            if voice_channel.user_limit and len(voice_channel.members) >= voice_channel.user_limit and not perms.move_members:
                embed = discord.Embed(
                    title="⚠️ Kênh Thoại Đã Đầy",
                    description=f"Kênh thoại **{voice_channel.name}** đã đạt giới hạn tối đa ({voice_channel.user_limit} người)!",
                    color=discord.Color.orange()
                )
                await ctx.send(embed=embed, ephemeral=True)
                return None

        if ctx.voice_client and not isinstance(ctx.voice_client, CustomPlayer):
            try:
                await ctx.voice_client.disconnect(force=True)
                await asyncio.sleep(0.5)
            except Exception:
                pass

        if not ctx.voice_client or not isinstance(ctx.voice_client, CustomPlayer):
            try:
                player: CustomPlayer = await voice_channel.connect(cls=CustomPlayer, timeout=20.0)
            except Exception as e:
                err_type = type(e).__name__
                if err_type in ("ChannelTimeoutException", "TimeoutError") or isinstance(e, (asyncio.TimeoutError, TimeoutError)):
                    embed = discord.Embed(
                        title="⏱️ Quá Thời Gian Chờ Kết Nối (Voice Timeout)",
                        description=(
                            f"Không thể kết nối đến kênh thoại **{voice_channel.name}** do quá thời gian chờ (Timeout 20s).\n\n"
                            f"💡 **Cách khắc phục:**\n"
                            f"• Máy chủ Discord có thể đang gặp lag mạng hoặc lỗi RTC khu vực.\n"
                            f"• Hãy thử đổi khu vực thoại (**Voice Region**) trong Cài Đặt Kênh Thoại.\n"
                            f"• Thử lại sau vài giây hoặc ngắt kết nối bot nếu đang bị kẹt."
                        ),
                        color=discord.Color.red()
                    )
                    await ctx.send(embed=embed, ephemeral=True)
                    return None
                elif isinstance(e, discord.Forbidden):
                    embed = discord.Embed(
                        title="🚫 Không Có Quyền Truy Cập",
                        description=f"Bot bị từ chối kết nối vào kênh thoại **{voice_channel.name}** (403 Forbidden).",
                        color=discord.Color.red()
                    )
                    await ctx.send(embed=embed, ephemeral=True)
                    return None
                else:
                    embed = discord.Embed(
                        title="❌ Lỗi Kết Nối Kênh Thoại",
                        description=f"Không thể kết nối vào kênh thoại **{voice_channel.name}**: `{e}`",
                        color=discord.Color.red()
                    )
                    await ctx.send(embed=embed, ephemeral=True)
                    return None
        else:
            player: CustomPlayer = ctx.voice_client

        player.bound_channel = ctx.channel
        player.bound_guild = ctx.guild
        return player

    async def action_autocomplete(self, interaction: discord.Interaction, current: str) -> list[app_commands.Choice[str]]:
        cur = current.lower()
        actions = [
            ("Phát nhạc (play)", "play"), ("Bỏ qua (skip)", "skip"),
            ("Bài trước (previous)", "previous"), ("Tự động phát bài tiếp theo (autoplay)", "autoplay"),
            ("Dừng & rời phòng (stop)", "stop"), ("Xem hàng đợi (queue)", "queue"),
            ("Đang phát (nowplaying)", "nowplaying"), ("Tạm dừng (pause)", "pause"),
            ("Tiếp tục (resume)", "resume"), ("Chế độ lặp (loop)", "loop"),
            ("Trộn bài (shuffle)", "shuffle"), ("Tua nhạc (seek)", "seek"),
            ("Bộ lọc âm thanh (filter)", "filter"), ("Danh sách yêu thích (fav)", "fav"),
            ("Vào phòng (join)", "join"), ("Bảng hướng dẫn (panel)", "panel"), ("Âm lượng (volume)", "volume")
        ]
        return [
            app_commands.Choice(name=name, value=val)
            for name, val in actions if cur in name.lower()
        ][:25]

    async def music_autocomplete(self, interaction: discord.Interaction, current: str) -> list[app_commands.Choice[str]]:
        action = getattr(interaction.namespace, "action", None)
        cur = current.lower()

        if action == "loop":
            choices = [
                app_commands.Choice(name="Tắt lặp (Off)", value="off"),
                app_commands.Choice(name="Lặp bài hát (Song)", value="song"),
                app_commands.Choice(name="Lặp hàng đợi (Queue)", value="queue")
            ]
            return [c for c in choices if cur in c.name.lower()]

        if action == "filter":
            choices = [
                app_commands.Choice(name="Tăng âm trầm (Bassboost)", value="bassboost"),
                app_commands.Choice(name="Tăng tốc độ (Nightcore)", value="nightcore"),
                app_commands.Choice(name="Hiệu ứng hoài niệm (Vaporwave)", value="vaporwave"),
                app_commands.Choice(name="Âm thanh đảo quanh tai (8D)", value="8d"),
                app_commands.Choice(name="Tắt bộ lọc (Off)", value="off")
            ]
            return [c for c in choices if cur in c.name.lower()]

        if action == "autoplay":
            choices = [
                app_commands.Choice(name="Bật tự động chọn bài (On)", value="on"),
                app_commands.Choice(name="Tắt tự động chọn bài (Off)", value="off")
            ]
            return [c for c in choices if cur in c.name.lower()]

        if action == "fav":
            choices = [
                app_commands.Choice(name="Thêm bài hiện tại (add)", value="add"),
                app_commands.Choice(name="Phát danh sách (play)", value="play"),
                app_commands.Choice(name="Xem danh sách (list)", value="list"),
                app_commands.Choice(name="Xóa bài theo số thứ tự (remove)", value="remove")
            ]
            return [c for c in choices if cur in c.name.lower()]

        return []

    async def _send_panel(self, ctx: commands.Context):
        prefix = ctx.prefix
        embed = discord.Embed(
            title="🎵 HỆ THỐNG PHÁT NHẠC WAVELINK",
            description="Chào mừng bạn đến với hệ thống âm nhạc chất lượng cao của Bot!",
            color=discord.Color.blurple()
        )
        embed.add_field(
            name="🎶 Các lệnh tắt cơ bản",
            value=(
                f"• `{prefix}play <tên/url>` (hoặc `{prefix}p`)\n"
                f"• `{prefix}skip` (hoặc `{prefix}s`)\n"
                f"• `{prefix}stop` (hoặc `{prefix}leave`)\n"
                f"• `{prefix}queue` (hoặc `{prefix}q`)\n"
                f"• `{prefix}np` (hoặc `{prefix}nowplaying`)\n"
                f"• `{prefix}volume <0-200>` (hoặc `{prefix}vol`)"
            ),
            inline=False
        )
        embed.add_field(
            name="⚙️ Các lệnh quản lý khác",
            value=(
                f"• `{prefix}pause` / `{prefix}resume`\n"
                f"• `{prefix}loop <off/song/queue>`\n"
                f"• `{prefix}shuffle` | `{prefix}seek <giây>`\n"
                f"• `{prefix}filter <bassboost/nightcore/...>`\n"
                f"• `{prefix}fav add/play/list/remove <stt>`"
            ),
            inline=False
        )
        embed.set_footer(text="Hoặc sử dụng menu Slash /music để tương tác trực quan hơn.")
        await ctx.send(embed=embed)

    @commands.hybrid_command(
        name="music",
        aliases=["m"],
        description="🎵 Hệ thống phát nhạc Wavelink nâng cao toàn diện."
    )
    @commands.guild_only()
    @app_commands.describe(
        action="Chọn hành động nhạc cần thực hiện (hoặc chọn panel để xem hướng dẫn)",
        query="Tên bài hát, URL, cấu hình, hoặc số lượng tùy chỉnh"
    )
    @app_commands.autocomplete(action=action_autocomplete, query=music_autocomplete)
    async def music(
        self,
        ctx: commands.Context,
        action: Literal[
            "panel", "play", "skip", "previous", "autoplay", "stop", "queue", "nowplaying",
            "pause", "resume", "loop", "shuffle", "seek", "filter", "fav", "join", "volume"
        ] = "panel",
        *,
        query: Optional[str] = None
    ):
        act = action.lower()

        if act == "panel":
            return await self._send_panel(ctx)

        if act == "play":
            if not query:
                embed = discord.Embed(title="⚠️ Thiếu Thông Tin", description="Vui lòng nhập tên bài hát hoặc đường dẫn cần phát!", color=discord.Color.orange())
                return await ctx.send(embed=embed, ephemeral=True)

            player = await self.get_player(ctx)
            if not player:
                return
            if ctx.interaction:
                await ctx.defer()

            search_query = query
            if not re.match(r"https?://(?:www\.)?.+", query):
                search_query = f"ytsearch:{query}"

            try:
                tracks: wavelink.Search = await wavelink.Playable.search(search_query)
                if not tracks and "ytsearch:" in search_query:
                    tracks = await wavelink.Playable.search(f"scsearch:{query}")
                if not tracks:
                    embed = discord.Embed(title="❌ Không Tìm Thấy", description=t(ctx.guild, "MUSIC_NOT_FOUND", query=query), color=discord.Color.red())
                    return await ctx.send(embed=embed, ephemeral=True)
            except Exception as e:
                embed = discord.Embed(title="❌ Lỗi Tìm Kiếm", description=t(ctx.guild, "MUSIC_SEARCH_ERROR", error=e), color=discord.Color.red())
                return await ctx.send(embed=embed, ephemeral=True)

            if isinstance(tracks, wavelink.Playlist):
                added = 0
                for trk in tracks:
                    trk.requester = ctx.author
                    await player.queue.put_wait(trk)
                    added += 1
                embed = discord.Embed(title="📜 Đã Thêm Playlist", description=t(ctx.guild, "MUSIC_PLAYLIST_ADDED", name=tracks.name, count=added), color=discord.Color.blue())
                await ctx.send(embed=embed)
                
                if not player.auto_tracks_pool and player.autoplay_enabled and len(tracks) > 0:
                    await player.fetch_autoplay_pool(tracks[0].title)
            else:
                track = tracks[0]
                track.requester = ctx.author
                
                await player.queue.put_wait(track)
                pos = len(player.queue)
                
                if player.playing:
                    embed = discord.Embed(
                        title="🎵 Đã Thêm Vào Hàng Đợi",
                        description=f"Đã thêm **{track.title}** vào vị trí `#{pos}` trong hàng đợi ưu tiên!",
                        color=discord.Color.green()
                    )
                else:
                    embed = discord.Embed(
                        title="🎵 Đã Thêm Vào Hàng Đợi",
                        description=t(ctx.guild, "MUSIC_TRACK_ADDED", title=track.title),
                        color=discord.Color.green()
                    )

                if track.artwork:
                    embed.set_thumbnail(url=track.artwork)
                await ctx.send(embed=embed)
                
                if not player.auto_tracks_pool and player.autoplay_enabled:
                    await player.fetch_autoplay_pool(track.title)

            if not player.playing and not player.queue.is_empty:
                await player.play(player.queue.get())
            elif player.playing and player.current and player.bound_channel:
                embed_np = player.build_now_playing_embed(player.current)
                await player.safe_edit_panel(embed_np)
            return

        if act == "skip":
            count = int(query) if query and query.isdigit() else 1
            player = await self.get_player(ctx)
            if not player or not player.playing:
                embed = discord.Embed(title="❌ Lỗi", description=t(ctx.guild, "MUSIC_NOT_PLAYING"), color=discord.Color.red())
                return await ctx.send(embed=embed, ephemeral=True)
            
            member = ctx.author
            is_owner = player.current and getattr(player.current, "requester", None) == member
            if not is_owner and not is_music_admin(member):
                humans = [m for m in player.channel.members if not m.bot]
                if len(humans) >= 3:
                    uid = member.id
                    if uid not in player.skip_votes:
                        player.skip_votes.add(uid)
                    needed = math.ceil(len(humans) / 2)
                    if len(player.skip_votes) < needed:
                        embed = discord.Embed(title="🗳️ Bình Chọn Bỏ Qua", description=f"Đã ghi nhận phiếu bầu bỏ qua ({len(player.skip_votes)}/{needed}). Cần ít nhất {needed} phiếu.", color=discord.Color.orange())
                        return await ctx.send(embed=embed, ephemeral=True)

            player.skip_votes.clear()
            if count > 1:
                if len(player.queue) < count - 1:
                    embed = discord.Embed(title="❌ Lỗi", description=t(ctx.guild, "MUSIC_QUEUE_NOT_ENOUGH"), color=discord.Color.red())
                    return await ctx.send(embed=embed, ephemeral=True)
                for _ in range(count - 1):
                    del player.queue[0]
            await player.skip(force=True)
            await self.play_next(player)
            embed = discord.Embed(title="⏭️ Bỏ Qua Bài Hát", description="Đã chuyển sang bài hát tiếp theo.", color=discord.Color.blue())
            await ctx.send(embed=embed, ephemeral=True if ctx.interaction else False)
            return

        if act == "previous":
            player = await self.get_player(ctx)
            if not player:
                return
            if len(player.history) < 2:
                embed = discord.Embed(title="❌ Lỗi", description="Không có lịch sử bài hát trước đó.", color=discord.Color.red())
                return await ctx.send(embed=embed, ephemeral=True)
            
            current_track = player.history.pop()
            prev_track = player.history.pop()
            
            player.queue.put_at(0, current_track)
            player.queue.put_at(0, prev_track)
            
            await player.skip(force=True)
            embed = discord.Embed(title="⏮️ Phát Lại Bài Trước", description=f"Đang phát: **{prev_track.title}**", color=discord.Color.blue())
            await ctx.send(embed=embed)
            return

        if act == "volume":
            from Command.vote import require_vote_or_notify
            if not await require_vote_or_notify(ctx, "/music volume (Điều Chỉnh Âm Lượng Nhạc)"):
                return

            player = await self.get_player(ctx)
            if not player:
                return
            try:
                vol = int(query.strip().replace("%", "")) if query else -1
                if not (0 <= vol <= 200):
                    raise ValueError
            except ValueError:
                embed = discord.Embed(title="⚠️ Sai Định Dạng", description="Vui lòng nhập mức âm lượng từ `0` đến `200`!", color=discord.Color.orange())
                return await ctx.send(embed=embed, ephemeral=True)
            
            await player.set_volume(vol)
            embed = discord.Embed(title="🔊 Âm Lượng", description=f"Đã chỉnh âm lượng thành **{vol}%**", color=discord.Color.blue())
            await ctx.send(embed=embed)
            if player.current and player.bound_channel:
                await player.send_now_playing(player.current)
            return

        if act == "autoplay":
            player = await self.get_player(ctx)
            if not player:
                return
            mode = (query or "").lower()
            if mode == "on":
                player.autoplay_enabled = True
                embed = discord.Embed(title="🟢 Autoplay", description="Đã **bật** tính năng tự động chọn bài tiếp theo.", color=discord.Color.green())
                await ctx.send(embed=embed)
            elif mode == "off":
                player.autoplay_enabled = False
                embed = discord.Embed(title="🔴 Autoplay", description="Đã **tắt** tính năng tự động chọn bài tiếp theo.", color=discord.Color.red())
                await ctx.send(embed=embed)
            else:
                status = "đang bật" if player.autoplay_enabled else "đang tắt"
                embed = discord.Embed(title="ℹ️ Trạng Thái Autoplay", description=f"Tính năng hiện tại `{status}`. Dùng `/music autoplay on` hoặc `off` để thay đổi.", color=discord.Color.blue())
                await ctx.send(embed=embed)
            return

        if act == "stop":
            player = await self.get_player(ctx)
            if not player:
                return
            player.queue.clear()
            player.auto_tracks_pool.clear()
            await player.cleanup_panel()
            await player.disconnect()
            embed = discord.Embed(title="⏹️ Dừng Phát Nhạc", description=t(ctx.guild, "MUSIC_STOPPED"), color=discord.Color.dark_red())
            await ctx.send(embed=embed)
            return

        if act == "queue":
            player = await self.get_player(ctx)
            if not player or player.queue.is_empty:
                embed = discord.Embed(title="📂 Hàng Đợi", description=t(ctx.guild, "MUSIC_QUEUE_EMPTY"), color=discord.Color.orange())
                return await ctx.send(embed=embed, ephemeral=True)
            embed = discord.Embed(title=t(ctx.guild, "MUSIC_QUEUE_TITLE"), color=discord.Color.blue())
            queue_text = "\n".join(f"`{i}.` {track.title}" for i, track in enumerate(list(player.queue)[:10], start=1))
            embed.description = queue_text
            embed.set_footer(text=t(ctx.guild, "MUSIC_QUEUE_FOOTER", count=len(player.queue)))
            await ctx.send(embed=embed)
            return

        if act == "nowplaying":
            player = await self.get_player(ctx)
            if not player or not player.current:
                embed = discord.Embed(title="❌ Lỗi", description=t(ctx.guild, "MUSIC_NOT_PLAYING"), color=discord.Color.red())
                return await ctx.send(embed=embed, ephemeral=True)
            track = player.current
            await player.send_now_playing(track)
            return

        if act == "pause":
            player = await self.get_player(ctx)
            if player and player.playing:
                await player.pause(True)
                embed = discord.Embed(title="⏸️ Tạm Dừng", description="Đã tạm dừng phát nhạc.", color=discord.Color.orange())
                await ctx.send(embed=embed, ephemeral=True if ctx.interaction else False)
            return

        if act == "resume":
            player = await self.get_player(ctx)
            if player and player.paused:
                await player.pause(False)
                embed = discord.Embed(title="▶️ Tiếp Tục", description="Đã tiếp tục phát nhạc.", color=discord.Color.green())
                await ctx.send(embed=embed, ephemeral=True if ctx.interaction else False)
            return

        if act == "loop":
            player = await self.get_player(ctx)
            if not player:
                return
            mode = (query or "off").lower()
            if mode == "off":
                player.queue.mode = wavelink.QueueMode.normal
                embed = discord.Embed(title="🔄 Chế Độ Lặp", description=t(ctx.guild, "MUSIC_LOOP_OFF"), color=discord.Color.blue())
                await ctx.send(embed=embed)
            elif mode == "song":
                player.queue.mode = wavelink.QueueMode.loop
                embed = discord.Embed(title="🔂 Chế Độ Lặp", description=t(ctx.guild, "MUSIC_LOOP_SONG"), color=discord.Color.blue())
                await ctx.send(embed=embed)
            elif mode == "queue":
                player.queue.mode = wavelink.QueueMode.loop_all
                embed = discord.Embed(title="🔁 Chế Độ Lặp", description=t(ctx.guild, "MUSIC_LOOP_QUEUE"), color=discord.Color.blue())
                await ctx.send(embed=embed)
            return

        if act == "shuffle":
            player = await self.get_player(ctx)
            if not player or player.queue.is_empty:
                embed = discord.Embed(title="❌ Lỗi", description="Hàng đợi đang trống.", color=discord.Color.red())
                return await ctx.send(embed=embed, ephemeral=True)
            player.queue.shuffle()
            embed = discord.Embed(title="🔀 Xáo Trộn", description="Đã xáo trộn hàng đợi bài hát thành công!", color=discord.Color.purple())
            await ctx.send(embed=embed)
            return

        if act == "seek":
            player = await self.get_player(ctx)
            if not player or not player.playing:
                embed = discord.Embed(title="❌ Lỗi", description=t(ctx.guild, "MUSIC_NOT_PLAYING"), color=discord.Color.red())
                return await ctx.send(embed=embed, ephemeral=True)
            if not query or not query.isdigit():
                embed = discord.Embed(title="⚠️ Sai Định Dạng", description="Vui lòng nhập số giây cần tua (ví dụ: `45`).", color=discord.Color.orange())
                return await ctx.send(embed=embed, ephemeral=True)
            seconds = int(query)
            target_ms = seconds * 1000
            if target_ms > player.current.length:
                embed = discord.Embed(title="⚠️ Vượt Quá Giới Hạn", description="Thời gian tua vượt quá độ dài bài hát!", color=discord.Color.orange())
                return await ctx.send(embed=embed, ephemeral=True)
            await player.seek(target_ms)
            embed = discord.Embed(title="⏩ Tua Nhạc", description=f"Đã tua đến giây thứ **{seconds}** của bài hát.", color=discord.Color.blue())
            await ctx.send(embed=embed)
            return

        if act == "filter":
            player = await self.get_player(ctx)
            if not player:
                return
            mode = (query or "off").lower()
            filters: wavelink.Filters = player.filters
            
            if mode == "bassboost":
                filters.equalizer.set(bands=[(0, 0.3), (1, 0.3), (2, 0.2), (3, 0.1)])
                await player.set_filters(filters)
                embed = discord.Embed(title="🔊 Bộ Lọc Âm Thanh", description="Đã bật bộ lọc **Bassboost** tăng âm trầm.", color=discord.Color.purple())
                await ctx.send(embed=embed)
            elif mode == "nightcore":
                filters.timescale.set(speed=1.25, pitch=1.25)
                await player.set_filters(filters)
                embed = discord.Embed(title="✨ Bộ Lọc Âm Thanh", description="Đã bật bộ lọc **Nightcore**.", color=discord.Color.purple())
                await ctx.send(embed=embed)
            elif mode == "vaporwave":
                filters.timescale.set(speed=0.85, pitch=0.85)
                await player.set_filters(filters)
                embed = discord.Embed(title="📼 Bộ Lọc Âm Thanh", description="Đã bật bộ lọc **Vaporwave**.", color=discord.Color.purple())
                await ctx.send(embed=embed)
            elif mode == "8d":
                filters.rotation.set(rotation_hz=0.2)
                await player.set_filters(filters)
                embed = discord.Embed(title="🎧 Bộ Lọc Âm Thanh", description="Đã bật hiệu ứng âm thanh **8D**.", color=discord.Color.purple())
                await ctx.send(embed=embed)
            else:
                filters.reset()
                await player.set_filters(filters)
                embed = discord.Embed(title="🔄 Bộ Lọc Âm Thanh", description="Đã tắt toàn bộ bộ lọc âm thanh.", color=discord.Color.blue())
                await ctx.send(embed=embed)
            return

        if act == "fav":
            uid = str(ctx.author.id)
            user_favs = user_favorites.setdefault(uid, [])
            sub = (query or "list").strip().lower()

            if sub.startswith("remove"):
                parts = sub.split()
                if len(parts) < 2 or not parts[1].isdigit():
                    embed = discord.Embed(title="⚠️ Thiếu số thứ tự", description=f"Cú pháp: `{ctx.prefix}fav remove <số_thứ_tự>` (hoặc `/music fav remove <số_thứ_tự>`)", color=discord.Color.orange())
                    return await ctx.send(embed=embed, ephemeral=True)
                idx = int(parts[1]) - 1
                if 0 <= idx < len(user_favs):
                    removed = user_favs.pop(idx)
                    save_favorites()
                    embed = discord.Embed(title="🗑️ Xóa Thành Công", description=f"Đã xóa **{removed['title']}** khỏi danh sách yêu thích!", color=discord.Color.green())
                    return await ctx.send(embed=embed)
                else:
                    embed = discord.Embed(title="❌ Lỗi", description=f"Số thứ tự không hợp lệ! Bạn có từ 1 đến {len(user_favs)} bài.", color=discord.Color.red())
                    return await ctx.send(embed=embed, ephemeral=True)

            elif sub == "add":
                player = await self.get_player(ctx)
                if not player or not player.current:
                    embed = discord.Embed(title="❌ Lỗi", description="Không có bài hát nào đang phát để thêm vào yêu thích.", color=discord.Color.red())
                    return await ctx.send(embed=embed, ephemeral=True)
                track = player.current
                if any(f["uri"] == track.uri for f in user_favs):
                    embed = discord.Embed(title="⚠️ Đã Tồn Tại", description="Bài hát này đã có trong danh sách yêu thích của bạn rồi!", color=discord.Color.orange())
                    return await ctx.send(embed=embed, ephemeral=True)
                user_favs.append({"title": track.title, "uri": track.uri})
                save_favorites()
                embed = discord.Embed(title="⭐ Thêm Yêu Thích", description=f"Đã thêm **{track.title}** vào danh sách yêu thích cá nhân!", color=discord.Color.gold())
                return await ctx.send(embed=embed)
            
            elif sub == "play":
                if not user_favs:
                    embed = discord.Embed(title="📂 Danh Sách Trống", description="Danh sách yêu thích của bạn đang trống.", color=discord.Color.orange())
                    return await ctx.send(embed=embed, ephemeral=True)
                
                player = await self.get_player(ctx)
                if not player:
                    return
                if ctx.interaction:
                    await ctx.defer()
                
                added = 0
                for item in user_favs:
                    try:
                        tracks = await wavelink.Playable.search(item["uri"])
                        if tracks:
                            trk = tracks[0] if not isinstance(tracks, wavelink.Playlist) else tracks[0]
                            trk.requester = ctx.author
                            await player.queue.put_wait(trk)
                            added += 1
                    except Exception:
                        continue
                
                if added == 0:
                    embed = discord.Embed(title="❌ Lỗi", description="Không thể tải được bài hát nào từ danh sách yêu thích.", color=discord.Color.red())
                    return await ctx.send(embed=embed, ephemeral=True)

                if not player.playing and not player.queue.is_empty:
                    await player.play(player.queue.get())
                embed = discord.Embed(title="▶️ Phát Yêu Thích", description=f"Đã thêm **{added}** bài hát từ danh sách yêu thích vào hàng đợi ưu tiên!", color=discord.Color.green())
                return await ctx.send(embed=embed)
            
            else:
                if not user_favs:
                    embed = discord.Embed(title="📂 Danh Sách Trống", description="Danh sách yêu thích của bạn đang trống.", color=discord.Color.orange())
                    return await ctx.send(embed=embed, ephemeral=True)
                lines = [f"`{i}.` [{f['title']}]({f['uri']})" for i, f in enumerate(user_favs, 1)]
                embed = discord.Embed(title=f"⭐ Danh sách yêu thích của {ctx.author.display_name}", description="\n".join(lines[:15]), color=discord.Color.gold())
                embed.set_footer(text=f"Dùng {ctx.prefix}fav remove <stt> để xóa bài hát khỏi danh sách.")
                return await ctx.send(embed=embed, ephemeral=True)

        if act == "join":
            player = await self.get_player(ctx)
            if not player:
                return
            embed = discord.Embed(title="✅ Kết Nối", description="Đã tham gia kênh thoại thành công.", color=discord.Color.green())
            await ctx.send(embed=embed, ephemeral=True if ctx.interaction else False)
            return

    @commands.command(name="play", aliases=["p"])
    async def p_shortcut(self, ctx: commands.Context, *, query: str):
        await self.music(ctx, action="play", query=query)

    @commands.command(name="skip", aliases=["s"])
    async def s_shortcut(self, ctx: commands.Context, count: Optional[str] = None):
        await self.music(ctx, action="skip", query=count)

    @commands.command(name="stop", aliases=["leave", "disconnect"])
    async def stop_shortcut(self, ctx: commands.Context):
        await self.music(ctx, action="stop")

    @commands.command(name="queue", aliases=["q"])
    async def q_shortcut(self, ctx: commands.Context):
        await self.music(ctx, action="queue")

    @commands.command(name="nowplaying", aliases=["np"])
    async def np_shortcut(self, ctx: commands.Context):
        await self.music(ctx, action="nowplaying")

    @commands.command(name="pause")
    async def pause_shortcut(self, ctx: commands.Context):
        await self.music(ctx, action="pause")

    @commands.command(name="resume")
    async def resume_shortcut(self, ctx: commands.Context):
        await self.music(ctx, action="resume")

    @commands.command(name="loop")
    async def loop_shortcut(self, ctx: commands.Context, mode: str = "off"):
        await self.music(ctx, action="loop", query=mode)

    @commands.command(name="shuffle")
    async def shuffle_shortcut(self, ctx: commands.Context):
        await self.music(ctx, action="shuffle")

    @commands.command(name="seek")
    async def seek_shortcut(self, ctx: commands.Context, seconds: str):
        await self.music(ctx, action="seek", query=seconds)

    @commands.command(name="filter")
    async def filter_shortcut(self, ctx: commands.Context, mode: str = "off"):
        await self.music(ctx, action="filter", query=mode)

    @commands.command(name="fav")
    async def fav_shortcut(self, ctx: commands.Context, *, sub: str = "list"):
        await self.music(ctx, action="fav", query=sub)

    @commands.command(name="join")
    async def join_shortcut(self, ctx: commands.Context):
        await self.music(ctx, action="join")

    @commands.command(name="previous", aliases=["prev"])
    async def prev_shortcut(self, ctx: commands.Context):
        await self.music(ctx, action="previous")

    @commands.command(name="autoplay")
    async def autoplay_shortcut(self, ctx: commands.Context, mode: str = ""):
        await self.music(ctx, action="autoplay", query=mode)

    @commands.command(name="volume", aliases=["vol", "v"])
    async def volume_shortcut(self, ctx: commands.Context, level: str):
        await self.music(ctx, action="volume", query=level)


async def setup(bot: commands.Bot):
    await bot.add_cog(MusicControllerCog(bot))
