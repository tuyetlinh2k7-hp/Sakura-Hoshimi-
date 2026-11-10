import asyncio
import json
import math
import re
from pathlib import Path
from typing import Literal, Optional

import discord
import Check.dave_patch  # Kích hoạt bản vá DAVE E2EE 0.2.0 cho discord.py 2.7.1
from discord import app_commands
from discord.ext import commands

from config import OWNER_ID
from Check.tts_checks import (
    tts_queue, tts_playing, last_tts_user, voice_text_channels,
    tts_names, tts_language, tts_volume, tts_emoji_readings,
    tts_char_limit, tts_emoji_count_limit, tts_user_language,
    play_announcement, add_to_tts_queue,
    save_tts_names, save_tts_language, save_tts_volume,
    save_tts_emoji_readings, save_tts_user_language,
    save_tts_char_limit, save_tts_emoji_count_limit
)
from Check.mod import admin_roles
from Check.i18n import t

BASE_DIR = Path(__file__).resolve().parent.parent
VOICE_ONLY_FILE = BASE_DIR / "data" / "tts_voice_only.json"

SUPPORTED_LANGS = {
    "vi": "Tiếng Việt 🇻🇳",
    "en": "Tiếng Anh 🇬🇧",
    "ja": "Tiếng Nhật 🇯🇵",
    "ko": "Tiếng Hàn 🇰🇷",
    "zh-cn": "Tiếng Trung (Giản thể) 🇨🇳",
    "fr": "Tiếng Pháp 🇫🇷",
    "de": "Tiếng Đức 🇩🇪",
    "ru": "Tiếng Nga 🇷🇺",
    "es": "Tiếng Tây Ban Nha 🇪🇸",
    "th": "Tiếng Thái 🇹🇭",
    "id": "Tiếng Indonesia 🇮🇩"
}

tts_voice_only: dict[str, bool] = {}


def load_voice_only():
    if VOICE_ONLY_FILE.exists():
        try:
            with open(VOICE_ONLY_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                if isinstance(data, dict):
                    tts_voice_only.update(data)
        except Exception:
            pass


def save_voice_only():
    VOICE_ONLY_FILE.parent.mkdir(parents=True, exist_ok=True)
    try:
        with open(VOICE_ONLY_FILE, "w", encoding="utf-8") as f:
            json.dump(tts_voice_only, f, indent=4, ensure_ascii=False)
    except Exception:
        pass


load_voice_only()


def is_tts_admin(member: discord.Member) -> bool:
    if member.id in (OWNER_ID, member.guild.owner_id):
        return True
    if member.guild_permissions.administrator:
        return True
    guild_admins = admin_roles.get(str(member.guild.id), [])
    return any(role.id in guild_admins for role in member.roles)


def cleanup_guild_tts(guild_id: int):
    if guild_id in tts_queue:
        tts_queue[guild_id].clear()
    if guild_id in tts_playing:
        tts_playing[guild_id] = False
    last_tts_user.pop(guild_id, None)
    voice_text_channels.pop(guild_id, None)


def is_connected(vc) -> bool:
    if not vc:
        return False
    if hasattr(vc, "is_connected"):
        return vc.is_connected()
    return getattr(vc, "connected", False)


def is_wavelink_player(vc) -> bool:
    """Kiểm tra xem voice_client hiện tại có phải là CustomPlayer (Wavelink) của Music hay không."""
    return vc is not None and (hasattr(vc, "queue") or not isinstance(vc, discord.VoiceClient))


class SetNameModal(discord.ui.Modal, title="✏️ Đặt Tên Đọc TTS"):
    name_input = discord.ui.TextInput(
        label="Tên bạn muốn Bot gọi khi đọc tin nhắn",
        placeholder="Để trống nếu muốn xóa tên tùy chỉnh...",
        required=False,
        max_length=50
    )

    async def on_submit(self, interaction: discord.Interaction):
        gid_str = str(interaction.guild.id)
        uid_str = str(interaction.user.id)
        tts_names.setdefault(gid_str, {})

        val = self.name_input.value.strip() if self.name_input.value else ""
        if val:
            tts_names[gid_str][uid_str] = val
            desc = f"Tên đọc của bạn đã được đặt thành: **{val}**"
            title = "✨ Đặt Tên Thành Công"
        else:
            tts_names[gid_str].pop(uid_str, None)
            desc = "Đã xóa tên đọc tùy chỉnh, bot sẽ dùng tên hiển thị của bạn."
            title = "✨ Xóa Tên Thành Công"

        save_tts_names()
        embed = discord.Embed(title=title, description=desc, color=0xffb6c1)
        await interaction.response.send_message(embed=embed, ephemeral=True)


class TTSControlView(discord.ui.View):
    def __init__(self, cog: "TextToSpeechCog", guild: discord.Guild):
        super().__init__(timeout=180)
        self.cog = cog
        self.guild = guild
        self.message: Optional[discord.Message] = None
        self._sync_voice_only_btn()
        self._build_lang_select()

    def _sync_voice_only_btn(self):
        enabled = tts_voice_only.get(str(self.guild.id), False)
        self.voice_only_btn.label = f"Chỉ đọc trong Voice: {'BẬT' if enabled else 'TẮT'}"
        self.voice_only_btn.style = discord.ButtonStyle.success if enabled else discord.ButtonStyle.secondary

    def _build_lang_select(self):
        options = [
            discord.SelectOption(label="Mặc định theo Server (Reset)", value="reset", emoji="🔄")
        ]
        for code, label in SUPPORTED_LANGS.items():
            options.append(discord.SelectOption(label=f"{label} ({code})", value=code, emoji="🌐"))

        select = discord.ui.Select(
            placeholder="🌐 Chọn giọng đọc TTS cá nhân của bạn (ulang)...",
            options=options,
            row=2
        )
        select.callback = self.lang_select_callback
        self.add_item(select)

    async def on_timeout(self):
        if self.message:
            for item in self.children:
                item.disabled = True
            try:
                await self.message.edit(view=self)
            except discord.HTTPException:
                pass

    @discord.ui.button(label="Bật TTS", style=discord.ButtonStyle.success, emoji="▶️", row=0)
    async def on_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.cog._handle_on(interaction)

    @discord.ui.button(label="Tắt TTS", style=discord.ButtonStyle.danger, emoji="⏹️", row=0)
    async def off_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.cog._handle_off(interaction)

    @discord.ui.button(label="Bỏ qua", style=discord.ButtonStyle.primary, emoji="⏭️", row=0)
    async def skip_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not is_tts_admin(interaction.user):
            return await interaction.response.send_message("⛔ Bạn cần quyền Admin của Bot để bỏ qua tin nhắn!", ephemeral=True)
        vc = interaction.guild.voice_client
        if not vc or is_wavelink_player(vc) or not vc.is_playing():
            return await interaction.response.send_message("❌ Hiện không có tin nhắn TTS nào đang được đọc.", ephemeral=True)
        tts_playing[interaction.guild.id] = False
        vc.stop()
        await interaction.response.send_message("⏭️ Đã bỏ qua tin nhắn đang đọc.", ephemeral=True)

    @discord.ui.button(label="Xóa hàng đợi", style=discord.ButtonStyle.secondary, emoji="🗑️", row=0)
    async def clear_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not is_tts_admin(interaction.user):
            return await interaction.response.send_message("⛔ Bạn cần quyền Admin của Bot để xóa hàng đợi!", ephemeral=True)
        gid = interaction.guild.id
        if gid in tts_queue:
            tts_queue[gid].clear()
        tts_playing[gid] = False
        vc = interaction.guild.voice_client
        if vc and not is_wavelink_player(vc) and vc.is_playing():
            vc.stop()
        await interaction.response.send_message("🗑️ Đã xóa toàn bộ hàng đợi TTS.", ephemeral=True)

    @discord.ui.button(label="Trạng thái", style=discord.ButtonStyle.secondary, emoji="📊", row=1)
    async def status_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        embed = self.cog._build_status_embed(interaction.guild, interaction.user)
        await interaction.response.send_message(embed=embed, ephemeral=True)

    @discord.ui.button(label="Đặt tên đọc", style=discord.ButtonStyle.primary, emoji="✏️", row=1)
    async def setname_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(SetNameModal())

    @discord.ui.button(label="Chỉ đọc trong Voice: TẮT", style=discord.ButtonStyle.secondary, emoji="🎙️", row=1)
    async def voice_only_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not is_tts_admin(interaction.user):
            return await interaction.response.send_message("⛔ Chỉ Admin mới có thể bật/tắt chế độ này!", ephemeral=True)
        gid_str = str(interaction.guild.id)
        new_state = not tts_voice_only.get(gid_str, False)
        tts_voice_only[gid_str] = new_state
        save_voice_only()
        self._sync_voice_only_btn()
        await interaction.response.edit_message(view=self)
        status_txt = "🟢 **BẬT** (Chỉ đọc tin nhắn của người đang ở trong phòng thoại)" if new_state else "🔴 **TẮT** (Đọc tin nhắn của mọi người trong kênh chat)"
        await interaction.followup.send(f"🎙️ Chế độ Chỉ đọc người trong Voice: {status_txt}", ephemeral=True)

    async def lang_select_callback(self, interaction: discord.Interaction):
        choice = interaction.data["values"][0]
        gid_str = str(interaction.guild.id)
        uid_str = str(interaction.user.id)
        tts_user_language.setdefault(gid_str, {})

        if choice == "reset":
            tts_user_language[gid_str].pop(uid_str, None)
            save_tts_user_language()
            return await interaction.response.send_message("🔄 Đã đặt lại giọng đọc của bạn theo ngôn ngữ mặc định của Server.", ephemeral=True)

        tts_user_language[gid_str][uid_str] = choice
        save_tts_user_language()
        await interaction.response.send_message(
            f"🌐 Đã đổi giọng đọc cá nhân của bạn thành: **{SUPPORTED_LANGS[choice]}**",
            ephemeral=True
        )


class TextToSpeechCog(commands.Cog, name="Text-to-Speech"):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if message.author.bot or not message.guild:
            return

        vc = message.guild.voice_client
        # Không chạy TTS nếu bot chưa vào voice hoặc đang là trình phát nhạc Wavelink
        if not vc or is_wavelink_player(vc):
            return

        prefix = await self.bot.get_prefix(message)
        if isinstance(prefix, (list, tuple)):
            if any(message.content.startswith(p) for p in prefix):
                return
        elif isinstance(prefix, str) and message.content.startswith(prefix):
            return

        if tts_voice_only.get(str(message.guild.id), False):
            if not vc.channel:
                return
            if not message.author.voice or message.author.voice.channel != vc.channel:
                return

        await add_to_tts_queue(message, self.bot)

    @commands.Cog.listener()
    async def on_voice_state_update(self, member: discord.Member, before: discord.VoiceState, after: discord.VoiceState):
        guild = member.guild
        vc = guild.voice_client

        if self.bot.user and member.id == self.bot.user.id:
            if before.channel and not after.channel:
                cleanup_guild_tts(guild.id)
            return

        if is_wavelink_player(vc):
            return

        if vc and is_connected(vc) and before.channel == vc.channel:
            humans = [m for m in vc.channel.members if not m.bot]
            if not humans:
                await asyncio.sleep(30)
                vc_now = guild.voice_client
                if vc_now and not is_wavelink_player(vc_now) and is_connected(vc_now):
                    still_humans = [m for m in vc_now.channel.members if not m.bot]
                    if not still_humans:
                        cleanup_guild_tts(guild.id)
                        await vc_now.disconnect()

    def _build_status_embed(self, guild: discord.Guild, author: discord.abc.User) -> discord.Embed:
        gid = guild.id
        gid_str = str(gid)
        vc = guild.voice_client
        embed = discord.Embed(title="🌸 Trạng Thái Hệ Thống TTS 🌸", color=0xffb6c1)

        if not vc or not is_connected(vc):
            embed.description = "🔴 Bot hiện không hoạt động trong kênh thoại nào."
            return embed

        if is_wavelink_player(vc):
            embed.description = f"🎵 Bot hiện đang phát nhạc tại {vc.channel.mention} (TTS đang tắt). Dùng `/tts on` để ưu tiên chuyển sang TTS."
            return embed

        embed.description = f"🟢 Bot đang hoạt động TTS trong phòng thoại {vc.channel.mention}."

        text_ch_id = voice_text_channels.get(gid)
        text_ch = guild.get_channel(text_ch_id) if text_ch_id else None
        embed.add_field(
            name="🎧 Kênh Lắng Nghe",
            value=text_ch.mention if isinstance(text_ch, (discord.TextChannel, discord.VoiceChannel, discord.Thread)) else "`Chưa thiết lập`",
            inline=True
        )

        is_playing = tts_playing.get(gid, False)
        embed.add_field(name="🎤 Trạng Thái Phát", value="Đang nói..." if is_playing else "Đang chờ", inline=True)
        embed.add_field(name="📬 Hàng Đợi", value=f"`{len(tts_queue.get(gid, []))}` tin nhắn", inline=True)

        lang_code = tts_language.get(gid_str, "vi")
        embed.add_field(name="🌐 Ngôn Ngữ Server", value=f"`{lang_code}` ({SUPPORTED_LANGS.get(lang_code, lang_code)})", inline=True)

        vol = int(tts_volume.get(gid_str, 1.0) * 100)
        embed.add_field(name="🔉 Âm Lượng", value=f"`{vol}%`", inline=True)

        v_only = tts_voice_only.get(gid_str, False)
        embed.add_field(name="🎙️ Chỉ đọc người trong Voice", value="🟢 `Bật`" if v_only else "🔴 `Tắt`", inline=True)

        char_lim = tts_char_limit.get(gid_str, 300)
        embed.add_field(name="📝 Giới hạn Ký tự", value=f"`{char_lim}`" if char_lim > 0 else "`Không giới hạn`", inline=True)

        emoji_lim = tts_emoji_count_limit.get(gid_str, 10)
        embed.add_field(name="🔢 Giới hạn Emoji", value=f"`{emoji_lim}`" if emoji_lim > 0 else "`Không giới hạn`", inline=True)

        embed.set_footer(text=f"Yêu cầu bởi {author.display_name}", icon_url=author.display_avatar.url)
        return embed

    async def _handle_on(self, target: commands.Context | discord.Interaction):
        is_inter = isinstance(target, discord.Interaction)
        guild = target.guild
        author = target.user if is_inter else target.author
        channel = target.channel

        async def reply(embed: discord.Embed = None, content: str = None, ephemeral: bool = False):
            if is_inter:
                if target.response.is_done():
                    await target.followup.send(content=content, embed=embed, ephemeral=ephemeral)
                else:
                    await target.response.send_message(content=content, embed=embed, ephemeral=ephemeral)
            else:
                await target.send(content=content, embed=embed, ephemeral=ephemeral if target.interaction else False)

        if not isinstance(author, discord.Member) or not author.voice or not author.voice.channel:
            embed = discord.Embed(
                title="⚠️ Yêu Cầu Thất Bại",
                description="Bạn phải tham gia vào một kênh thoại trước khi gọi tôi!",
                color=discord.Color.orange()
            )
            return await reply(embed=embed, ephemeral=True)

        if is_inter and not target.response.is_done():
            await target.response.defer()

        voice_channel = author.voice.channel
        vc = guild.voice_client

        # ƯU TIÊN TTS: Nếu bot đang phát nhạc bằng Wavelink CustomPlayer, tự động dừng nhạc và ngắt Wavelink
        if vc and is_wavelink_player(vc):
            try:
                if hasattr(vc, "queue"):
                    vc.queue.clear()
                if hasattr(vc, "auto_tracks_pool"):
                    vc.auto_tracks_pool.clear()
                if hasattr(vc, "cleanup_panel"):
                    await vc.cleanup_panel()
                await vc.disconnect(force=True)
                await asyncio.sleep(0.6)
            except Exception:
                pass
            vc = guild.voice_client

        if vc and is_connected(vc) and not is_wavelink_player(vc):
            if vc.channel != voice_channel:
                humans_in_old = [m for m in vc.channel.members if not m.bot]
                if humans_in_old:
                    embed = discord.Embed(
                        title="⚠️ Yêu Cầu Bị Từ Chối",
                        description=f"Tôi đang phục vụ **{len(humans_in_old)}** thành viên ở {vc.channel.mention} mất rồi! 🥺",
                        color=discord.Color.red()
                    )
                    embed.set_footer(text="Vui lòng thử lại sau hoặc dùng lệnh /tts off ở kênh đó.")
                    return await reply(embed=embed, ephemeral=True)

                try:
                    await vc.move_to(voice_channel)
                except (asyncio.TimeoutError, TimeoutError):
                    await vc.disconnect(force=True)
                    return await reply(content="⚠️ Discord không phản hồi khi chuyển kênh thoại. Vui lòng thử lại.", ephemeral=True)
        else:
            try:
                await voice_channel.connect(timeout=30, reconnect=True, self_deaf=False, self_mute=False)
            except (asyncio.TimeoutError, TimeoutError):
                if guild.voice_client:
                    await guild.voice_client.disconnect(force=True)
                return await reply(content="⚠️ Không thể kết nối kênh thoại trong thời gian chờ. Hãy kiểm tra quyền Connect/Speak.", ephemeral=True)
            except discord.ClientException:
                try:
                    if guild.voice_client:
                        await guild.voice_client.disconnect(force=True)
                        await asyncio.sleep(0.5)
                    await voice_channel.connect(timeout=30, reconnect=True, self_deaf=False, self_mute=False)
                except Exception:
                    return await reply(content="⚠️ Bot đang có một phiên kết nối thoại khác. Vui lòng thử lại.", ephemeral=True)

        voice_text_channels[guild.id] = channel.id
        tts_playing[guild.id] = False
        embed = discord.Embed(
            title="🌸 TTS Đã Bật 🌸",
            description=f"✅ Đã tham gia phòng thoại {voice_channel.mention} và sẽ đọc tin nhắn tại kênh {channel.mention}.",
            color=0xffb6c1
        )
        embed.set_footer(text=f"Yêu cầu bởi {author.display_name}", icon_url=author.display_avatar.url)
        await reply(embed=embed)

        # Cảnh báo nếu bot bị Server Mute trong phòng thoại
        if guild.me.voice and guild.me.voice.mute:
            await channel.send("⚠️ **Cảnh báo**: Sakura đang bị **Tắt tiếng (Server Mute)** trong kênh thoại. Vui lòng Bỏ Tắt Tiếng (Unmute) cho bot để nghe được âm thanh!", delete_after=15)

        # Cảnh báo nếu bot thiếu quyền Nói (Speak)
        perms = voice_channel.permissions_for(guild.me)
        if not perms.speak:
            await channel.send("⚠️ **Cảnh báo**: Sakura không có quyền **Nói (Speak)** trong kênh thoại này. Vui lòng cấp quyền để bot phát âm thanh!", delete_after=15)

        # Chờ 0.8s để kết nối voice và mã hóa DAVE (E2EE) của Discord hoàn tất bắt tay (handshake)
        await asyncio.sleep(0.8)
        await play_announcement(guild, "Sakura đã tìm thấy kênh thoại, Sakura sẽ đọc chat của các bạn", self.bot)

    async def _handle_off(self, target: commands.Context | discord.Interaction):
        is_inter = isinstance(target, discord.Interaction)
        guild = target.guild
        vc = guild.voice_client

        if not vc or is_wavelink_player(vc):
            cleanup_guild_tts(guild.id)
            msg = "❌ Hệ thống TTS hiện không hoạt động."
            if is_inter:
                return await target.response.send_message(msg, ephemeral=True)
            return await target.send(msg, ephemeral=True)

        cleanup_guild_tts(guild.id)
        await vc.disconnect()

        embed = discord.Embed(
            title="🌸 TTS Đã Tắt 🌸",
            description="Hẹn gặp lại chủ nhân lần sau nhé! 💮",
            color=0xffb6c1
        )
        if is_inter:
            await target.response.send_message(embed=embed)
        else:
            await target.send(embed=embed)

    async def tts_value_autocomplete(self, interaction: discord.Interaction, current: str):
        action = getattr(interaction.namespace, "action", None)
        cur = current.lower()

        if action in ("lang", "ulang"):
            choices = [app_commands.Choice(name="📋 Xem danh sách ngôn ngữ (list)", value="list")]
            if action == "ulang":
                choices.append(app_commands.Choice(name="🔄 Mặc định theo Server (reset)", value="reset"))
            for code, name in SUPPORTED_LANGS.items():
                if cur in code.lower() or cur in name.lower():
                    choices.append(app_commands.Choice(name=f"{name} ({code})", value=code))
            return choices[:25]

        if action == "volume":
            vols = ["50", "80", "100", "120", "150", "200"]
            return [app_commands.Choice(name=f"Âm lượng {v}%", value=v) for v in vols if cur in v]

        if action == "voiceonly":
            return [
                app_commands.Choice(name="🟢 Bật (Chỉ đọc người trong phòng Voice)", value="on"),
                app_commands.Choice(name="🔴 Tắt (Đọc tất cả mọi người)", value="off")
            ]

        if action == "limit":
            limits = ["0", "100", "200", "300", "500"]
            return [app_commands.Choice(name="Không giới hạn (0)" if l == "0" else f"Tối đa {l} ký tự", value=l) for l in limits if cur in l]

        if action == "emojilimit":
            elimits = ["0", "3", "5", "10", "15"]
            return [app_commands.Choice(name="Không giới hạn (0)" if l == "0" else f"Tối đa {l} emoji", value=l) for l in elimits if cur in l]

        return []

    @commands.hybrid_command(
        name="tts",
        description="🌸 Bảng điều khiển và quản lý toàn bộ hệ thống đọc tin nhắn (Text-to-Speech)."
    )
    @commands.guild_only()
    @app_commands.describe(
        action="Chọn chức năng TTS cần dùng (Bỏ trống hoặc chọn 'panel' để mở Bảng điều khiển nút bấm)",
        value="Giá trị đi kèm: Tên đọc, mã ngôn ngữ (vi/en/ja...), mức âm lượng (0-200), on/off, hoặc emoji + cách đọc"
    )
    @app_commands.autocomplete(value=tts_value_autocomplete)
    async def tts(
        self,
        ctx: commands.Context,
        action: Optional[Literal[
            "panel", "on", "off", "skip", "clear", "status",
            "setname", "ulang", "lang", "volume", "setemoji",
            "limit", "emojilimit", "voiceonly", "listnames"
        ]] = "panel",
        *,
        value: Optional[str] = None
    ):
        act = (action or "panel").lower().strip()
        prefix = ctx.prefix
        is_slash = ctx.interaction is not None
        gid_str = str(ctx.guild.id)
        uid_str = str(ctx.author.id)

        if act in ("panel", "help"):
            embed = discord.Embed(
                title=t(ctx.guild, "TTS_CONTROL_PANEL_TITLE"),
                description=t(ctx.guild, "TTS_CONTROL_PANEL_DESC"),
                color=0xffb6c1
            )
            if self.bot.user and self.bot.user.avatar:
                embed.set_thumbnail(url=self.bot.user.avatar.url)

            embed.add_field(
                name="▶️ Điều Khiển Cơ Bản",
                value=(
                    f"{t(ctx.guild, 'TTS_CMD_ON', prefix=prefix)}\n"
                    f"{t(ctx.guild, 'TTS_CMD_OFF', prefix=prefix)}\n"
                    f"{t(ctx.guild, 'TTS_CMD_SKIP', prefix=prefix)}\n"
                    f"{t(ctx.guild, 'TTS_CMD_CLEAR', prefix=prefix)}"
                ),
                inline=False
            )
            embed.add_field(
                name="⚙️ Tùy Chỉnh & Cấu Hình",
                value=(
                    f"{t(ctx.guild, 'TTS_CMD_SETNAME', prefix=prefix)}\n"
                    f"{t(ctx.guild, 'TTS_CMD_VOLUME', prefix=prefix)}\n"
                    f"`{prefix}tts lang <mã>` — Đổi ngôn ngữ đọc của Server\n"
                    f"`{prefix}tts ulang <mã>` — Đổi ngôn ngữ đọc cho riêng bạn\n"
                    f"`{prefix}tts voiceonly <on/off>` — Chỉ đọc người đang ở trong Voice\n"
                    f"`{prefix}tts setemoji <emoji> <cách_đọc>` — Cài cách đọc Emoji\n"
                    f"`{prefix}tts limit <số>` | `{prefix}tts emojilimit <số>`"
                ),
                inline=False
            )
            embed.add_field(
                name="📊 Thông Tin & Quản Lý",
                value=(
                    f"{t(ctx.guild, 'TTS_CMD_STATUS', prefix=prefix)}\n"
                    f"`{prefix}tts listnames` — Xem danh sách tên đọc đã lưu"
                ),
                inline=False
            )

            view = TTSControlView(self, ctx.guild)
            msg = await ctx.send(embed=embed, view=view)
            view.message = msg
            return

        if act == "on":
            return await self._handle_on(ctx)

        if act == "off":
            return await self._handle_off(ctx)

        if act == "status":
            return await ctx.send(embed=self._build_status_embed(ctx.guild, ctx.author))

        if act == "setname":
            tts_names.setdefault(gid_str, {})
            if value and value.strip():
                clean_name = value.strip()
                tts_names[gid_str][uid_str] = clean_name
                embed = discord.Embed(
                    title="✨ Đặt Tên Thành Công",
                    description=f"Tên đọc của bạn đã được đặt thành: **{clean_name}**",
                    color=0xffb6c1
                )
            else:
                tts_names[gid_str].pop(uid_str, None)
                embed = discord.Embed(
                    title="✨ Xóa Tên Thành Công",
                    description="Đã xóa tên đọc tùy chỉnh, bot sẽ dùng tên Discord của bạn.",
                    color=0xffb6c1
                )
            save_tts_names()
            return await ctx.send(embed=embed, ephemeral=is_slash)

        if act == "ulang":
            tts_user_language.setdefault(gid_str, {})
            val = value.lower().strip() if value else ""

            if val == "list":
                desc = "\n".join(f"🌸 `{c}` — {n}" for c, n in SUPPORTED_LANGS.items())
                embed = discord.Embed(
                    title="🌐 Danh sách ngôn ngữ được hỗ trợ",
                    description=f"Sử dụng `{prefix}tts ulang <mã>` để thay đổi.\n\n{desc}",
                    color=0xffb6c1
                )
                return await ctx.send(embed=embed, ephemeral=is_slash)

            if not val or val == "reset":
                tts_user_language[gid_str].pop(uid_str, None)
                save_tts_user_language()
                embed = discord.Embed(
                    title="✨ Reset Ngôn Ngữ Thành Công",
                    description="Đã xóa ngôn ngữ tùy chỉnh, bot sẽ đọc theo ngôn ngữ của Server.",
                    color=0xffb6c1
                )
                return await ctx.send(embed=embed, ephemeral=is_slash)

            if val not in SUPPORTED_LANGS:
                return await ctx.send(f"❌ Mã ngôn ngữ `{val}` không hợp lệ. Gõ `{prefix}tts ulang list` để xem danh sách.", ephemeral=True)

            tts_user_language[gid_str][uid_str] = val
            save_tts_user_language()
            embed = discord.Embed(
                title="✨ Đặt Ngôn Ngữ Thành Công",
                description=f"Ngôn ngữ đọc của bạn đã được đặt thành: **{SUPPORTED_LANGS[val]}**",
                color=0xffb6c1
            )
            return await ctx.send(embed=embed, ephemeral=is_slash)

        if not is_tts_admin(ctx.author):
            return await ctx.send("⛔ Bạn cần có quyền **Admin của Bot** để sử dụng chức năng này!", ephemeral=True)

        if act == "skip":
            vc = ctx.guild.voice_client
            if not vc or is_wavelink_player(vc) or not vc.is_playing():
                return await ctx.send("❌ Không có tin nhắn TTS nào đang được đọc.", ephemeral=True)
            tts_playing[ctx.guild.id] = False
            vc.stop()
            await ctx.send("⏭️ Đã bỏ qua tin nhắn hiện tại.", ephemeral=is_slash)
            if not is_slash:
                await ctx.message.add_reaction("⏭️")
            return

        if act == "clear":
            if ctx.guild.id in tts_queue:
                tts_queue[ctx.guild.id].clear()
            tts_playing[ctx.guild.id] = False
            vc = ctx.guild.voice_client
            if vc and not is_wavelink_player(vc) and vc.is_playing():
                vc.stop()
            await ctx.send("🗑️ Đã xóa toàn bộ hàng đợi TTS.", ephemeral=is_slash)
            if not is_slash:
                await ctx.message.add_reaction("🗑️")
            return

        if act == "lang":
            val = value.lower().strip() if value else "list"
            if val == "list":
                desc = "\n".join(f"🌸 `{c}` — {n}" for c, n in SUPPORTED_LANGS.items())
                embed = discord.Embed(
                    title="🌐 Danh sách ngôn ngữ được hỗ trợ",
                    description=f"Sử dụng `{prefix}tts lang <mã>` để thay đổi.\n\n{desc}",
                    color=0xffb6c1
                )
                return await ctx.send(embed=embed, ephemeral=is_slash)

            if val not in SUPPORTED_LANGS:
                return await ctx.send(f"❌ Mã ngôn ngữ `{val}` không được hỗ trợ. Gõ `{prefix}tts lang list` để xem danh sách.", ephemeral=True)

            tts_language[gid_str] = val
            save_tts_language()
            embed = discord.Embed(
                title="🌸 Thay Đổi Ngôn Ngữ Thành Công",
                description=f"Giọng đọc TTS của Server đã được đổi thành **{SUPPORTED_LANGS[val]}**.",
                color=0xffb6c1
            )
            return await ctx.send(embed=embed)

        if act == "volume":
            try:
                level = int(value.strip().replace("%", "")) if value else -1
                if not (0 <= level <= 200):
                    raise ValueError
            except ValueError:
                return await ctx.send("❌ Vui lòng nhập mức âm lượng từ `0` đến `200`.", ephemeral=True)

            tts_volume[gid_str] = level / 100.0
            save_tts_volume()
            embed = discord.Embed(
                title="🌸 Điều Chỉnh Âm Lượng Thành Công",
                description=f"Âm lượng giọng nói TTS đã được đặt thành **{level}%**.",
                color=0xffb6c1
            )
            return await ctx.send(embed=embed)

        if act == "voiceonly":
            current_state = tts_voice_only.get(gid_str, False)
            if not value:
                new_state = not current_state
            elif value.lower().strip() in ("on", "true", "bat", "1"):
                new_state = True
            elif value.lower().strip() in ("off", "false", "tat", "0"):
                new_state = False
            else:
                return await ctx.send("⚠️ Vui lòng nhập `on` (Bật) hoặc `off` (Tắt)!", ephemeral=True)

            tts_voice_only[gid_str] = new_state
            save_voice_only()
            state_txt = "🟢 **BẬT** (Chỉ đọc tin nhắn của người đang ở trong phòng Voice)" if new_state else "🔴 **TẮT** (Đọc tin nhắn của mọi người)"
            return await ctx.send(f"🎙️ Chế độ Chỉ đọc người trong Voice đã chuyển sang: {state_txt}")

        if act == "setemoji":
            if not value:
                return await ctx.send(f"⚠️ Cú pháp: `{prefix}tts setemoji <emoji_server> [cách_đọc]`", ephemeral=True)

            parts = value.strip().split(maxsplit=1)
            emoji_str = parts[0]
            cach_doc = parts[1].strip() if len(parts) > 1 else None

            match = re.match(r"<a?:[a-zA-Z0-9_]+:(\d+)>", emoji_str)
            if not match:
                return await ctx.send("❌ Emoji không hợp lệ. Vui lòng chỉ sử dụng emoji tùy chỉnh của Server.", ephemeral=True)

            emoji_id = match.group(1)
            tts_emoji_readings.setdefault(gid_str, {})

            if cach_doc:
                tts_emoji_readings[gid_str][emoji_id] = cach_doc
                await ctx.send(f"✅ Đã cài đặt: Khi gặp {emoji_str}, bot sẽ đọc là **'{cach_doc}'**.")
            else:
                tts_emoji_readings[gid_str].pop(emoji_id, None)
                await ctx.send(f"🗑️ Đã xóa cài đặt đọc riêng cho {emoji_str}. Bot sẽ đọc theo tên mặc định.")

            save_tts_emoji_readings()
            return

        if act in ("limit", "emojilimit"):
            try:
                limit_val = int(value.strip()) if value else -1
                if limit_val < 0:
                    raise ValueError
            except ValueError:
                return await ctx.send("❌ Vui lòng nhập một số nguyên không âm (`0` để tắt giới hạn).", ephemeral=True)

            if act == "limit":
                tts_char_limit[gid_str] = limit_val
                save_tts_char_limit()
                msg = f"✅ Đã đặt giới hạn ký tự TTS là **{limit_val}**." if limit_val > 0 else "✅ Đã **tắt** giới hạn ký tự TTS."
            else:
                tts_emoji_count_limit[gid_str] = limit_val
                save_tts_emoji_count_limit()
                msg = f"✅ Đã đặt giới hạn số lượng Emoji mỗi tin nhắn là **{limit_val}**." if limit_val > 0 else "✅ Đã **tắt** giới hạn số lượng Emoji."

            return await ctx.send(msg, ephemeral=is_slash)

        if act == "listnames":
            server_names = tts_names.get(gid_str, {})
            if not server_names:
                embed = discord.Embed(
                    title="🌸 Danh Sách Tên Đọc Tùy Chỉnh",
                    description="Hiện chưa có ai trong Server này cài đặt tên đọc tùy chỉnh.",
                    color=0xffb6c1
                )
                return await ctx.send(embed=embed, ephemeral=True)

            if is_slash:
                await ctx.defer(ephemeral=True)

            lines = []
            for uid, custom_name in server_names.items():
                member = ctx.guild.get_member(int(uid)) or self.bot.get_user(int(uid))
                if member:
                    lines.append(f"• {member.mention} (`{uid}`): **{custom_name}**")
                else:
                    lines.append(f"• `<@{uid}>` (`{uid}`): **{custom_name}**")

            items_per_page = 15
            pages = math.ceil(len(lines) / items_per_page)
            first_page = "\n".join(lines[:items_per_page])

            embed = discord.Embed(
                title="🌸 Danh Sách Tên Đọc Tùy Chỉnh",
                description=first_page,
                color=0xffb6c1
            )
            embed.set_footer(text=f"Trang 1/{pages} | Tổng cộng: {len(lines)} tên")
            return await ctx.send(embed=embed, ephemeral=True)


async def setup(bot: commands.Bot):
    await bot.add_cog(TextToSpeechCog(bot))
