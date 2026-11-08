import discord
from discord import app_commands
from discord.ext import commands
import os
import datetime
import yt_dlp
import aiohttp
import asyncio
import json
import io
import re
from urllib.parse import urljoin, urlparse
from bs4 import BeautifulSoup

from Command_vi.checks import time, download_cooldown, ytdl
from Checks_vi.mod import has_admin_role
from config import OWNER_ID
from Checks_vi.i18n import t, is_vietnamese

# Thư mục tạm để xử lý file (tự động xóa ngay sau khi gửi)
TEMP_DOWNLOADS_DIR = "downloads"
# File lưu trữ cấu hình Bật/Tắt và Chế độ của từng Server / Kênh
CONFIG_FILE = "data/download_config.json"

# Mở rộng Regex hỗ trợ:
# Video/Social: TikTok, Douyin, YouTube, Facebook, Instagram, X/Twitter, Reddit, Threads, Bilibili
# Ảnh/Art: Pinterest, Pixiv
# Audio/Music: SoundCloud, Spotify
ALLOWED_DOMAINS_REGEX = re.compile(
    r'https?://(?:www\.|m\.|vt\.|v\.|vm\.|on\.|open\.)?'
    r'(?:tiktok\.com|douyin\.com|youtube\.com|youtu\.be|facebook\.com|fb\.watch|'
    r'instagram\.com|twitter\.com|x\.com|reddit\.com|redd\.it|threads\.net|bilibili\.com|b23\.tv|'
    r'pinterest\.com|pin\.it|pixiv\.net|soundcloud\.com|spotify\.com)[^\s]+'
)

SHORT_DOMAINS = (
    "vt.tiktok.com", "vm.tiktok.com", "v.douyin.com", "youtu.be",
    "fb.watch", "redd.it", "b23.tv", "pin.it", "on.soundcloud.com"
)


class DownloadActionView(discord.ui.View):
    """Giao diện nút bấm Tải MP3, Tạo GIF, Xem Link Gốc và Xóa tin nhắn."""
    def __init__(
        self,
        cog,
        author_id: int,
        original_url: str,
        direct_audio_url: str = None,
        direct_video_url: str = None,
        show_mp3_btn: bool = True,
        show_gif_btn: bool = True,
        guild=None
    ):
        super().__init__(timeout=600)  # Nút có hiệu lực trong 10 phút
        self.cog = cog
        self.author_id = author_id
        self.original_url = original_url
        self.direct_audio_url = direct_audio_url
        self.direct_video_url = direct_video_url
        self.mp3_downloaded = False
        self.gif_created = False
        self.message: discord.Message | None = None
        self.guild = guild
        vi = is_vietnamese(guild)

        if not show_mp3_btn:
            self.remove_item(self.download_mp3)
        else:
            self.download_mp3.label = "🎵 Tải MP3" if vi else "🎵 Download MP3"

        if not show_gif_btn:
            self.remove_item(self.create_gif)
        else:
            self.create_gif.label = "🎞️ Tạo GIF" if vi else "🎞️ Create GIF"

        self.delete_msg.label = "🗑️ Xóa" if vi else "🗑️ Delete"

        # Thêm nút dẫn thẳng tới Link gốc
        link_lbl = "🔗 Link gốc" if vi else "🔗 Source Link"
        self.add_item(discord.ui.Button(label=link_lbl, url=original_url, style=discord.ButtonStyle.link))

    async def on_timeout(self):
        """Tự động vô hiệu hóa các nút bấm sau 10 phút."""
        for item in self.children:
            if isinstance(item, discord.ui.Button) and item.style != discord.ButtonStyle.link:
                item.disabled = True
        if self.message:
            try:
                await self.message.edit(view=self)
            except discord.HTTPException:
                pass

    @discord.ui.button(label="🎵 Tải MP3", style=discord.ButtonStyle.secondary)
    async def download_mp3(self, interaction: discord.Interaction, button: discord.ui.Button):
        if self.mp3_downloaded:
            return await interaction.response.send_message("⚠️ File MP3 của nội dung này đã được tải rồi!", ephemeral=True)

        await interaction.response.defer()
        button.disabled = True
        button.label = "⏳ Đang tách nhạc..."
        await interaction.message.edit(view=self)

        max_size = self.cog._get_max_filesize(interaction.guild)
        file_path = None

        try:
            # Ưu tiên 1: Nếu có sẵn link nhạc trực tiếp từ API
            if self.direct_audio_url:
                session = await self.cog.get_session()
                try:
                    audio_bytes = await self.cog._fetch_media_safe(session, self.direct_audio_url, max_size, timeout=30)
                    if audio_bytes:
                        audio_file = discord.File(io.BytesIO(audio_bytes), filename="audio.mp3")
                        await interaction.followup.send(f"🎶 Nhạc nền được yêu cầu bởi {interaction.user.mention}:", file=audio_file)
                        self.mp3_downloaded = True
                        button.label = "✅ Đã tải MP3"
                        return await interaction.message.edit(view=self)
                except ValueError as ve:
                    button.label = "❌ File quá lớn"
                    await interaction.message.edit(view=self)
                    return await interaction.followup.send(f"❌ {ve}", ephemeral=True)

            # Ưu tiên 2: Dùng yt-dlp để trích xuất âm thanh từ link gốc (hoặc Spotify search)
            target_url = await self.cog._resolve_spotify_to_ytsearch(self.original_url) or self.original_url
            os.makedirs(TEMP_DOWNLOADS_DIR, exist_ok=True)
            unique_prefix = f"mp3_{interaction.id}"
            ydl_opts = {
                'format': f'bestaudio[filesize<{max_size}]/best[filesize<{max_size}]/bestaudio/best',
                'outtmpl': f'{TEMP_DOWNLOADS_DIR}/{unique_prefix}_%(id)s.%(ext)s',
                'quiet': True,
                'noplaylist': True,
                'cookiefile': 'cookies.txt',
                'max_filesize': max_size,
            }

            async with self.cog.ytdl_semaphore:
                _, file_path = await asyncio.to_thread(self.cog._run_ytdl_sync, target_url, ydl_opts, True)

            if not file_path or not os.path.exists(file_path):
                button.disabled = False
                button.label = "🎵 Tải MP3"
                await interaction.message.edit(view=self)
                return await interaction.followup.send("❌ Không thể trích xuất âm thanh từ liên kết này.", ephemeral=True)

            actual_size = os.path.getsize(file_path)
            if actual_size > max_size:
                button.label = "❌ File quá lớn"
                await interaction.message.edit(view=self)
                return await interaction.followup.send(
                    f"❌ File âm thanh (`{actual_size / 1024 / 1024:.2f} MB`) vượt quá giới hạn của server (`{max_size / 1024 / 1024:.0f} MB`).",
                    ephemeral=True
                )

            await interaction.followup.send(
                f"🎶 Âm thanh được yêu cầu bởi {interaction.user.mention}:",
                file=discord.File(file_path, filename="audio.mp3")
            )
            self.mp3_downloaded = True
            button.label = "✅ Đã tải MP3"
            await interaction.message.edit(view=self)

        except Exception as e:
            button.disabled = False
            button.label = "🎵 Tải MP3"
            await interaction.message.edit(view=self)
            await interaction.followup.send(f"❌ Lỗi khi tải MP3: `{e}`", ephemeral=True)
        finally:
            if file_path and os.path.exists(file_path):
                try:
                    os.remove(file_path)
                except OSError:
                    pass

    @discord.ui.button(label="🎞️ Tạo GIF", style=discord.ButtonStyle.primary)
    async def create_gif(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Chuyển đổi tối đa 8 giây đầu của video thành ảnh động GIF sắc nét bằng FFmpeg."""
        if self.gif_created:
            return await interaction.response.send_message("⚠️ Ảnh GIF của video này đã được tạo rồi!", ephemeral=True)

        await interaction.response.defer()
        button.disabled = True
        button.label = "⏳ Đang tạo GIF..."
        await interaction.message.edit(view=self)

        max_size = self.cog._get_max_filesize(interaction.guild)
        os.makedirs(TEMP_DOWNLOADS_DIR, exist_ok=True)
        input_path = None
        gif_path = os.path.join(TEMP_DOWNLOADS_DIR, f"gif_{interaction.id}.gif")

        try:
            # Bước 1: Lấy nguồn video (ưu tiên link trực tiếp nếu có, nếu không thì tải qua yt-dlp)
            if self.direct_video_url:
                session = await self.cog.get_session()
                video_bytes = await self.cog._fetch_media_safe(session, self.direct_video_url, max_size, timeout=30)
                if video_bytes:
                    input_path = os.path.join(TEMP_DOWNLOADS_DIR, f"raw_{interaction.id}.mp4")
                    with open(input_path, "wb") as f:
                        f.write(video_bytes)

            if not input_path or not os.path.exists(input_path):
                ydl_opts = {
                    'format': f'best[filesize<{max_size}][ext=mp4]/best[filesize<{max_size}]/best',
                    'outtmpl': f'{TEMP_DOWNLOADS_DIR}/raw_{interaction.id}_%(id)s.%(ext)s',
                    'quiet': True,
                    'noplaylist': True,
                    'cookiefile': 'cookies.txt',
                    'max_filesize': max_size,
                }
                async with self.cog.ytdl_semaphore:
                    _, input_path = await asyncio.to_thread(self.cog._run_ytdl_sync, self.original_url, ydl_opts, True)

            if not input_path or not os.path.exists(input_path):
                button.disabled = False
                button.label = "🎞️ Tạo GIF"
                await interaction.message.edit(view=self)
                return await interaction.followup.send("❌ Không thể lấy dữ liệu video gốc để tạo GIF.", ephemeral=True)

            # Bước 2: Dùng FFmpeg cắt 8s đầu, scale 360p, 12fps và tối ưu bảng màu GIF
            ffmpeg_cmd = [
                "ffmpeg", "-y",
                "-t", "8",
                "-i", input_path,
                "-vf", "fps=12,scale=360:-1:flags=lanczos,split[s0][s1];[s0]palettegen=max_colors=128[p];[s1][p]paletteuse=dither=bayer",
                "-loop", "0",
                gif_path
            ]

            async with self.cog.ytdl_semaphore:
                proc = await asyncio.create_subprocess_exec(
                    *ffmpeg_cmd,
                    stdout=asyncio.subprocess.DEVNULL,
                    stderr=asyncio.subprocess.DEVNULL
                )
                await asyncio.wait_for(proc.wait(), timeout=45)

            if not os.path.exists(gif_path) or os.path.getsize(gif_path) == 0:
                button.disabled = False
                button.label = "🎞️ Tạo GIF"
                await interaction.message.edit(view=self)
                return await interaction.followup.send("❌ Máy chủ chưa cài đặt `ffmpeg` hoặc không thể chuyển đổi video này sang GIF.", ephemeral=True)

            gif_size = os.path.getsize(gif_path)
            if gif_size > max_size:
                button.label = "❌ GIF quá lớn"
                await interaction.message.edit(view=self)
                return await interaction.followup.send(
                    f"❌ Ảnh GIF tạo ra (`{gif_size / 1024 / 1024:.2f} MB`) vượt quá giới hạn của máy chủ.",
                    ephemeral=True
                )

            await interaction.followup.send(
                f"🎞️ Ảnh GIF (8s đầu) được tạo theo yêu cầu của {interaction.user.mention}:",
                file=discord.File(gif_path, filename="animated.gif")
            )
            self.gif_created = True
            button.label = "✅ Đã tạo GIF"
            await interaction.message.edit(view=self)

        except Exception as e:
            button.disabled = False
            button.label = "🎞️ Tạo GIF"
            await interaction.message.edit(view=self)
            await interaction.followup.send(f"❌ Lỗi khi tạo GIF: `{e}`", ephemeral=True)
        finally:
            for p in (input_path, gif_path):
                if p and os.path.exists(p):
                    try:
                        os.remove(p)
                    except OSError:
                        pass

    @discord.ui.button(label="🗑️ Xóa", style=discord.ButtonStyle.danger)
    async def delete_msg(self, interaction: discord.Interaction, button: discord.ui.Button):
        is_admin = interaction.guild and interaction.user.guild_permissions.manage_messages
        if interaction.user.id not in (self.author_id, OWNER_ID) and not is_admin:
            vi = is_vietnamese(interaction.guild)
            msg = "❌ Chỉ người gửi link hoặc Quản trị viên mới có quyền xóa tin nhắn này!" if vi else "❌ Only the link sender or Administrators can delete this message!"
            return await interaction.response.send_message(msg, ephemeral=True)
        await interaction.message.delete()


class TikTokVideoPreviewView(discord.ui.View):
    """View hiển thị các tùy chọn tải chất lượng Video TikTok: HD, SD, Có logo, MP3, GIF, Xóa."""
    def __init__(self, cog, author_id: int, original_url: str, data: dict, guild=None):
        super().__init__(timeout=300)
        self.cog = cog
        self.author_id = author_id
        self.original_url = original_url
        self.data = data
        self.guild = guild
        self.message: discord.Message | None = None

        hd_url = data.get("hdplay")
        play_url = data.get("play")
        wm_url = data.get("wmplay")
        music_url = data.get("music") or (data.get("music_info") or {}).get("play")

        # Nút Link gốc
        self.add_item(discord.ui.Button(label="🔗 Link Gốc", url=original_url, style=discord.ButtonStyle.link, row=1))

        # Nếu không có HD thì vô hiệu hóa nút HD
        if not hd_url:
            self.btn_hd.disabled = True
            self.btn_hd.label = "🎬 HD (Không khả dụng)"

        # Nếu không có Watermark thì vô hiệu hóa nút Watermark
        if not wm_url:
            self.btn_wm.disabled = True

        # Nếu không có audio
        if not music_url:
            self.btn_mp3.disabled = True

    async def on_timeout(self):
        for item in self.children:
            if isinstance(item, discord.ui.Button) and item.style != discord.ButtonStyle.link:
                item.disabled = True
        if self.message:
            try:
                await self.message.edit(view=self)
            except Exception:
                pass

    def get_embed(self) -> discord.Embed:
        title = (self.data.get("title") or "Video TikTok")[:250]
        author = self.data.get("author", {})
        nickname = author.get("nickname") or "Người dùng TikTok"
        unique_id = author.get("unique_id") or ""
        duration = self.data.get("duration", 0)
        digg = self.data.get("digg_count", 0)
        comment = self.data.get("comment_count", 0)
        share = self.data.get("share_count", 0)
        play_count = self.data.get("play_count", 0)
        music_info = self.data.get("music_info", {})
        music_title = music_info.get("title") or "Âm thanh gốc"
        cover = self.data.get("origin_cover") or self.data.get("cover")

        embed = discord.Embed(
            title=f"🎬 {title}",
            url=self.original_url,
            color=discord.Color.from_rgb(254, 44, 85)  # TikTok Red/Pink
        )
        author_display = f"**{nickname}**" + (f" (@{unique_id})" if unique_id else "")
        embed.description = (
            f"👤 **Kênh:** {author_display}\n"
            f"⏱️ **Thời lượng:** `{duration} giây`\n"
            f"📊 **Thống kê:** ❤️ `{digg:,}` • 💬 `{comment:,}` • 🔁 `{share:,}` • 👁️ `{play_count:,}`\n"
            f"🎶 **Nhạc nền:** {music_title}\n\n"
            f"👉 **Hãy chọn chất lượng hoặc định dạng bên dưới để bắt đầu tải xuống:**"
        )
        if cover:
            embed.set_image(url=cover)
        avatar = author.get("avatar")
        if avatar:
            embed.set_thumbnail(url=avatar)
        embed.set_footer(text="SakuraBot • Trình Tải TikTok Thông Minh")
        return embed

    async def _handle_video_dl(self, interaction: discord.Interaction, button: discord.ui.Button, url_key: str, filename: str, label_name: str):
        if interaction.user.id not in (self.author_id, OWNER_ID) and not (interaction.guild and interaction.user.guild_permissions.manage_messages):
            return await interaction.response.send_message("❌ Chỉ người dùng yêu cầu lệnh mới có quyền chọn tải!", ephemeral=True)

        target_url = self.data.get(url_key) or self.data.get("play")
        if not target_url:
            return await interaction.response.send_message("❌ Không tìm thấy đường dẫn video cho chất lượng này.", ephemeral=True)

        await interaction.response.defer()
        orig_label = button.label
        button.disabled = True
        button.label = "⏳ Đang tải..."
        await interaction.message.edit(view=self)

        session = await self.cog.get_session()
        max_size = self.cog._get_max_filesize(interaction.guild)

        try:
            video_bytes = await self.cog._fetch_media_safe(session, target_url, max_size, timeout=45)
            if not video_bytes:
                button.label = "❌ Lỗi tải"
                button.disabled = False
                await interaction.message.edit(view=self)
                return await interaction.followup.send("❌ Không thể tải được dữ liệu video từ máy chủ TikTok.", ephemeral=True)

            video_file = discord.File(io.BytesIO(video_bytes), filename=filename)
            await interaction.followup.send(
                content=f"✅ {label_name} được yêu cầu bởi {interaction.user.mention}:",
                file=video_file
            )
            button.label = f"✅ Đã tải ({label_name})"
            await interaction.message.edit(view=self)
        except ValueError as ve:
            button.label = "❌ Quá giới hạn"
            button.disabled = False
            await interaction.message.edit(view=self)
            view = discord.ui.View()
            view.add_item(discord.ui.Button(label="📥 Tải trực tiếp qua trình duyệt", url=target_url, style=discord.ButtonStyle.link))
            await interaction.followup.send(f"⚠️ {ve}\nBạn có thể bấm vào nút bên dưới để tải trực tiếp:", view=view, ephemeral=True)
        except Exception as e:
            button.label = orig_label
            button.disabled = False
            await interaction.message.edit(view=self)
            await interaction.followup.send(f"❌ Đã xảy ra lỗi: `{e}`", ephemeral=True)

    @discord.ui.button(label="🎬 Tải HD (Không Logo)", style=discord.ButtonStyle.success, row=0)
    async def btn_hd(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self._handle_video_dl(interaction, button, "hdplay", "tiktok_hd.mp4", "Video HD Không Logo")

    @discord.ui.button(label="📹 Tải SD (Không Logo)", style=discord.ButtonStyle.primary, row=0)
    async def btn_sd(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self._handle_video_dl(interaction, button, "play", "tiktok_sd.mp4", "Video SD")

    @discord.ui.button(label="🏷️ Tải Có Logo", style=discord.ButtonStyle.secondary, row=0)
    async def btn_wm(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self._handle_video_dl(interaction, button, "wmplay", "tiktok_watermark.mp4", "Video Có Logo")

    @discord.ui.button(label="🎵 Tải MP3", style=discord.ButtonStyle.secondary, row=1)
    async def btn_mp3(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id not in (self.author_id, OWNER_ID) and not (interaction.guild and interaction.user.guild_permissions.manage_messages):
            return await interaction.response.send_message("❌ Chỉ người dùng yêu cầu lệnh mới có quyền chọn tải!", ephemeral=True)

        music_url = self.data.get("music") or (self.data.get("music_info") or {}).get("play")
        if not music_url:
            return await interaction.response.send_message("❌ Không tìm thấy âm thanh của video này.", ephemeral=True)

        await interaction.response.defer()
        button.disabled = True
        button.label = "⏳ Đang tải MP3..."
        await interaction.message.edit(view=self)

        session = await self.cog.get_session()
        max_size = self.cog._get_max_filesize(interaction.guild)

        try:
            audio_bytes = await self.cog._fetch_media_safe(session, music_url, max_size, timeout=30)
            if audio_bytes:
                audio_file = discord.File(io.BytesIO(audio_bytes), filename="tiktok_audio.mp3")
                await interaction.followup.send(f"🎶 Âm thanh MP3 được yêu cầu bởi {interaction.user.mention}:", file=audio_file)
                button.label = "✅ Đã tải MP3"
                await interaction.message.edit(view=self)
            else:
                button.disabled = False
                button.label = "🎵 Tải MP3"
                await interaction.message.edit(view=self)
                await interaction.followup.send("❌ Không thể tải được file âm thanh.", ephemeral=True)
        except Exception as e:
            button.disabled = False
            button.label = "🎵 Tải MP3"
            await interaction.message.edit(view=self)
            await interaction.followup.send(f"❌ Lỗi tải MP3: `{e}`", ephemeral=True)

    @discord.ui.button(label="🎞️ Tạo GIF", style=discord.ButtonStyle.secondary, row=1)
    async def btn_gif(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id not in (self.author_id, OWNER_ID) and not (interaction.guild and interaction.user.guild_permissions.manage_messages):
            return await interaction.response.send_message("❌ Chỉ người dùng yêu cầu lệnh mới có quyền chọn tạo GIF!", ephemeral=True)

        await interaction.response.defer()
        button.disabled = True
        button.label = "⏳ Đang tạo GIF..."
        await interaction.message.edit(view=self)

        video_url = self.data.get("play") or self.data.get("hdplay")
        max_size = self.cog._get_max_filesize(interaction.guild)
        os.makedirs(TEMP_DOWNLOADS_DIR, exist_ok=True)
        input_path = os.path.join(TEMP_DOWNLOADS_DIR, f"raw_tk_{interaction.id}.mp4")
        gif_path = os.path.join(TEMP_DOWNLOADS_DIR, f"gif_tk_{interaction.id}.gif")

        try:
            session = await self.cog.get_session()
            video_bytes = await self.cog._fetch_media_safe(session, video_url, max_size, timeout=30)
            if not video_bytes:
                button.disabled = False
                button.label = "🎞️ Tạo GIF"
                await interaction.message.edit(view=self)
                return await interaction.followup.send("❌ Không thể tải dữ liệu video để tạo GIF.", ephemeral=True)

            with open(input_path, "wb") as f:
                f.write(video_bytes)

            ffmpeg_cmd = [
                "ffmpeg", "-y", "-t", "8", "-i", input_path,
                "-vf", "fps=12,scale=360:-1:flags=lanczos,split[s0][s1];[s0]palettegen[p];[s1][p]paletteuse",
                "-loop", "0", gif_path
            ]
            async with self.cog.ytdl_semaphore:
                proc = await asyncio.create_subprocess_exec(
                    *ffmpeg_cmd,
                    stdout=asyncio.subprocess.DEVNULL,
                    stderr=asyncio.subprocess.DEVNULL
                )
                await proc.wait()

            if not os.path.exists(gif_path):
                button.disabled = False
                button.label = "🎞️ Tạo GIF"
                await interaction.message.edit(view=self)
                return await interaction.followup.send("❌ Lỗi trong quá trình chuyển đổi GIF bằng FFmpeg.", ephemeral=True)

            gif_size = os.path.getsize(gif_path)
            if gif_size > max_size:
                button.label = "❌ GIF quá lớn"
                await interaction.message.edit(view=self)
                return await interaction.followup.send(f"❌ Dung lượng GIF ({gif_size / 1024 / 1024:.2f} MB) vượt quá giới hạn server.", ephemeral=True)

            await interaction.followup.send(
                f"🎞️ Ảnh động GIF được tạo bởi {interaction.user.mention}:",
                file=discord.File(gif_path, filename="tiktok.gif")
            )
            button.label = "✅ Đã tạo GIF"
            await interaction.message.edit(view=self)
        except Exception as e:
            button.disabled = False
            button.label = "🎞️ Tạo GIF"
            await interaction.message.edit(view=self)
            await interaction.followup.send(f"❌ Lỗi khi tạo GIF: `{e}`", ephemeral=True)
        finally:
            for p in (input_path, gif_path):
                if p and os.path.exists(p):
                    try:
                        os.remove(p)
                    except OSError:
                        pass

    @discord.ui.button(label="🗑️ Xóa", style=discord.ButtonStyle.danger, row=1)
    async def btn_delete(self, interaction: discord.Interaction, button: discord.ui.Button):
        is_admin = interaction.guild and interaction.user.guild_permissions.manage_messages
        if interaction.user.id not in (self.author_id, OWNER_ID) and not is_admin:
            return await interaction.response.send_message("❌ Bạn không có quyền xóa tin nhắn này!", ephemeral=True)
        await interaction.message.delete()


class TikTokPhotoPreviewView(discord.ui.View):
    """View hiển thị xem trước bộ ảnh TikTok (Photo Slideshow) với chức năng lật trang và tải ảnh."""
    def __init__(self, cog, author_id: int, original_url: str, data: dict, images: list, guild=None):
        super().__init__(timeout=300)
        self.cog = cog
        self.author_id = author_id
        self.original_url = original_url
        self.data = data
        self.images = images
        self.current_idx = 0
        self.total = len(images)
        self.guild = guild
        self.message: discord.Message | None = None

        # Nút Link gốc
        self.add_item(discord.ui.Button(label="🔗 Link Gốc", url=original_url, style=discord.ButtonStyle.link, row=1))

        # Cập nhật trạng thái nút điều hướng ban đầu
        self._update_nav_buttons()

        # Kiểm tra xem có nhạc nền không
        music_url = data.get("music") or (data.get("music_info") or {}).get("play")
        if not music_url:
            self.btn_dl_music.disabled = True

    def _update_nav_buttons(self):
        self.btn_prev.disabled = (self.current_idx <= 0)
        self.btn_next.disabled = (self.current_idx >= self.total - 1)
        self.btn_counter.label = f"{self.current_idx + 1} / {self.total}"

    async def on_timeout(self):
        for item in self.children:
            if isinstance(item, discord.ui.Button) and item.style != discord.ButtonStyle.link:
                item.disabled = True
        if self.message:
            try:
                await self.message.edit(view=self)
            except Exception:
                pass

    def get_embed(self) -> discord.Embed:
        title = (self.data.get("title") or "Bộ ảnh TikTok")[:250]
        author = self.data.get("author", {})
        nickname = author.get("nickname") or "Người dùng TikTok"
        unique_id = author.get("unique_id") or ""
        digg = self.data.get("digg_count", 0)
        comment = self.data.get("comment_count", 0)
        share = self.data.get("share_count", 0)
        music_info = self.data.get("music_info", {})
        music_title = music_info.get("title") or "Âm thanh nền"

        embed = discord.Embed(
            title=f"📸 {title}",
            url=self.original_url,
            color=discord.Color.from_rgb(37, 244, 238)  # TikTok Cyan
        )
        author_display = f"**{nickname}**" + (f" (@{unique_id})" if unique_id else "")
        embed.description = (
            f"👤 **Kênh:** {author_display}\n"
            f"📷 **Bộ ảnh gồm:** `{self.total}` ảnh • 📌 **Đang xem:** `Ảnh {self.current_idx + 1} / {self.total}`\n"
            f"📊 **Thống kê:** ❤️ `{digg:,}` • 💬 `{comment:,}` • 🔁 `{share:,}`\n"
            f"🎶 **Nhạc nền:** {music_title}\n\n"
            f"👉 *Sử dụng nút ◀️ và ▶️ để xem lướt qua các ảnh, hoặc bấm tải xuống bên dưới:*"
        )
        if self.images and self.current_idx < len(self.images):
            embed.set_image(url=self.images[self.current_idx])

        avatar = author.get("avatar")
        if avatar:
            embed.set_thumbnail(url=avatar)
        embed.set_footer(text=f"Ảnh {self.current_idx + 1}/{self.total} • SakuraBot TikTok Downloader")
        return embed

    @discord.ui.button(label="◀️ Trước", style=discord.ButtonStyle.primary, row=0)
    async def btn_prev(self, interaction: discord.Interaction, button: discord.ui.Button):
        if self.current_idx > 0:
            self.current_idx -= 1
            self._update_nav_buttons()
            embed = self.get_embed()
            await interaction.response.edit_message(embed=embed, view=self)
        else:
            await interaction.response.defer()

    @discord.ui.button(label="1 / 1", style=discord.ButtonStyle.secondary, disabled=True, row=0)
    async def btn_counter(self, interaction: discord.Interaction, button: discord.ui.Button):
        pass

    @discord.ui.button(label="Tiếp ▶️", style=discord.ButtonStyle.primary, row=0)
    async def btn_next(self, interaction: discord.Interaction, button: discord.ui.Button):
        if self.current_idx < self.total - 1:
            self.current_idx += 1
            self._update_nav_buttons()
            embed = self.get_embed()
            await interaction.response.edit_message(embed=embed, view=self)
        else:
            await interaction.response.defer()

    @discord.ui.button(label="📥 Tải Ảnh Đang Xem", style=discord.ButtonStyle.success, row=1)
    async def btn_dl_current(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id not in (self.author_id, OWNER_ID) and not (interaction.guild and interaction.user.guild_permissions.manage_messages):
            return await interaction.response.send_message("❌ Chỉ người dùng yêu cầu lệnh mới có quyền tải ảnh!", ephemeral=True)

        await interaction.response.defer()
        img_url = self.images[self.current_idx]
        session = await self.cog.get_session()
        max_size = self.cog._get_max_filesize(interaction.guild)

        try:
            img_bytes = await self.cog._fetch_media_safe(session, img_url, max_size, timeout=15)
            if img_bytes:
                file_obj = discord.File(io.BytesIO(img_bytes), filename=f"tiktok_photo_{self.current_idx + 1}.jpg")
                await interaction.followup.send(
                    f"🖼️ Ảnh số **{self.current_idx + 1} / {self.total}** được yêu cầu bởi {interaction.user.mention}:",
                    file=file_obj
                )
            else:
                await interaction.followup.send("❌ Không thể tải được file ảnh này.", ephemeral=True)
        except Exception as e:
            await interaction.followup.send(f"❌ Lỗi khi tải ảnh: `{e}`", ephemeral=True)

    @discord.ui.button(label="📦 Tải Toàn Bộ Ảnh", style=discord.ButtonStyle.primary, row=1)
    async def btn_dl_all(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id not in (self.author_id, OWNER_ID) and not (interaction.guild and interaction.user.guild_permissions.manage_messages):
            return await interaction.response.send_message("❌ Chỉ người dùng yêu cầu lệnh mới có quyền tải trọn bộ ảnh!", ephemeral=True)

        await interaction.response.defer()
        button.disabled = True
        button.label = "⏳ Đang tải toàn bộ..."
        await interaction.message.edit(view=self)

        session = await self.cog.get_session()
        max_size = self.cog._get_max_filesize(interaction.guild)

        try:
            tasks = [
                self.cog._download_single_image(session, img_url, i + 1, max_size)
                for i, img_url in enumerate(self.images)
            ]
            results = await asyncio.gather(*tasks)
            files = [f for f in results if f is not None]

            if not files:
                button.disabled = False
                button.label = "📦 Tải Toàn Bộ Ảnh"
                await interaction.message.edit(view=self)
                return await interaction.followup.send("❌ Không tải được ảnh nào trong bộ sưu tập.", ephemeral=True)

            await interaction.followup.send(
                f"📦 Toàn bộ **{len(files)}/{self.total}** ảnh trong bài đăng được yêu cầu bởi {interaction.user.mention}:",
                files=files[:10]
            )
            for i in range(10, len(files), 10):
                await interaction.channel.send(files=files[i:i+10])

            button.label = f"✅ Đã tải ({len(files)} ảnh)"
            await interaction.message.edit(view=self)
        except Exception as e:
            button.disabled = False
            button.label = "📦 Tải Toàn Bộ Ảnh"
            await interaction.message.edit(view=self)
            await interaction.followup.send(f"❌ Lỗi khi tải toàn bộ ảnh: `{e}`", ephemeral=True)

    @discord.ui.button(label="🎵 Nhạc Nền MP3", style=discord.ButtonStyle.secondary, row=1)
    async def btn_dl_music(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id not in (self.author_id, OWNER_ID) and not (interaction.guild and interaction.user.guild_permissions.manage_messages):
            return await interaction.response.send_message("❌ Chỉ người dùng yêu cầu lệnh mới có quyền tải nhạc!", ephemeral=True)

        music_url = self.data.get("music") or (self.data.get("music_info") or {}).get("play")
        if not music_url:
            return await interaction.response.send_message("❌ Bài đăng này không có file âm thanh nền.", ephemeral=True)

        await interaction.response.defer()
        button.disabled = True
        button.label = "⏳ Đang tải MP3..."
        await interaction.message.edit(view=self)

        session = await self.cog.get_session()
        max_size = self.cog._get_max_filesize(interaction.guild)

        try:
            audio_bytes = await self.cog._fetch_media_safe(session, music_url, max_size, timeout=30)
            if audio_bytes:
                audio_file = discord.File(io.BytesIO(audio_bytes), filename="tiktok_audio.mp3")
                await interaction.followup.send(f"🎶 Âm thanh nền bài đăng được yêu cầu bởi {interaction.user.mention}:", file=audio_file)
                button.label = "✅ Đã tải MP3"
                await interaction.message.edit(view=self)
            else:
                button.disabled = False
                button.label = "🎵 Nhạc Nền MP3"
                await interaction.message.edit(view=self)
                await interaction.followup.send("❌ Không thể tải được file âm thanh.", ephemeral=True)
        except Exception as e:
            button.disabled = False
            button.label = "🎵 Nhạc Nền MP3"
            await interaction.message.edit(view=self)
            await interaction.followup.send(f"❌ Lỗi tải MP3: `{e}`", ephemeral=True)

    @discord.ui.button(label="🗑️ Xóa", style=discord.ButtonStyle.danger, row=1)
    async def btn_delete(self, interaction: discord.Interaction, button: discord.ui.Button):
        is_admin = interaction.guild and interaction.user.guild_permissions.manage_messages
        if interaction.user.id not in (self.author_id, OWNER_ID) and not is_admin:
            return await interaction.response.send_message("❌ Bạn không có quyền xóa tin nhắn này!", ephemeral=True)
        await interaction.message.delete()


class Dowload(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.session: aiohttp.ClientSession | None = None
        self.config = self._load_config()
        # Giới hạn tối đa 3 luồng yt-dlp / ffmpeg chạy song song để bảo vệ CPU & RAM
        self.ytdl_semaphore = asyncio.Semaphore(3)

    # --- QUẢN LÝ CẤU HÌNH BẬT/TẮT & CHẾ ĐỘ KÊNH LƯU FILE JSON ---
    def _load_config(self) -> dict:
        default_cfg = {
            "global_enabled": True,
            "disabled_guilds": [],
            "disabled_channels": [],
            "channel_modes": {}  # Lưu dạng {"channel_id_str": "image" | "audio"}
        }
        if os.path.exists(CONFIG_FILE):
            try:
                with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    default_cfg.update(data)
                    return default_cfg
            except Exception:
                pass
        return default_cfg

    def _save_config(self):
        try:
            with open(CONFIG_FILE, "w", encoding="utf-8") as f:
                json.dump(self.config, f, indent=4, ensure_ascii=False)
        except Exception:
            pass

    def is_download_allowed(self, guild_id: int | None, channel_id: int) -> bool:
        if not self.config.get("global_enabled", True):
            return False
        if guild_id and guild_id in self.config.get("disabled_guilds", []):
            return False
        if channel_id in self.config.get("disabled_channels", []):
            return False
        return True

    def get_channel_mode(self, channel_id: int) -> str:
        """Lấy chế độ tải của kênh: 'all' (mặc định), 'image' (chỉ tải ảnh), hoặc 'audio' (chỉ tải MP3)."""
        return self.config.get("channel_modes", {}).get(str(channel_id), "all")

    def _get_max_filesize(self, guild: discord.Guild | None) -> int:
        limit = guild.filesize_limit if guild else (10 * 1024 * 1024)
        return max(limit - (500 * 1024), 8 * 1024 * 1024)

    async def get_session(self) -> aiohttp.ClientSession:
        if self.session is None or self.session.closed:
            self.session = aiohttp.ClientSession(
                headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"}
            )
        return self.session

    def cog_unload(self):
        if self.session and not self.session.closed:
            self.bot.loop.create_task(self.session.close())

    async def _fetch_media_safe(self, session: aiohttp.ClientSession, url: str, max_size: int, timeout: int = 30) -> bytes | None:
        """Tải dữ liệu từ URL theo từng chunk để chống tràn RAM nếu gặp file quá lớn."""
        async with session.get(url, timeout=timeout) as resp:
            if resp.status != 200:
                return None

            content_length = resp.headers.get("Content-Length")
            if content_length and int(content_length) > max_size:
                raise ValueError(f"Dung lượng file (`{int(content_length) / 1024 / 1024:.2f} MB`) vượt quá giới hạn của máy chủ (`{max_size / 1024 / 1024:.1f} MB`).")

            chunks = bytearray()
            async for chunk in resp.content.iter_chunked(64 * 1024):
                chunks.extend(chunk)
                if len(chunks) > max_size:
                    raise ValueError(f"Dung lượng file vượt quá giới hạn của máy chủ (`{max_size / 1024 / 1024:.1f} MB`).")
            return bytes(chunks)

    def _run_ytdl_sync(self, url: str, ydl_opts: dict = None, download: bool = True):
        if not download:
            with yt_dlp.YoutubeDL(ydl_opts or {'quiet': True, 'noplaylist': True, 'cookiefile': 'cookies.txt'}) as ydl:
                info = ydl.extract_info(url, download=False)
                if 'entries' in info and info['entries']:
                    info = info['entries'][0]
                return info, None
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            if 'entries' in info and info['entries']:
                info = info['entries'][0]
            file_path = ydl.prepare_filename(info)
            return info, file_path

    # --- HỖNG TRỢ CHUYỂN ĐỔI LINK SPOTIFY SANG TÌM KIẾM YOUTUBE ---
    async def _resolve_spotify_to_ytsearch(self, url: str) -> str | None:
        """Đọc tên bài hát + nghệ sĩ từ link Spotify và chuyển thành truy vấn ytsearch1: cho yt-dlp."""
        if "spotify.com" not in url.lower():
            return None
        session = await self.get_session()
        try:
            # Ưu tiên gọi oEmbed API chính thức của Spotify (nhanh và không bị chặn)
            oembed_url = f"https://open.spotify.com/oembed?url={url}"
            async with session.get(oembed_url, timeout=10) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    title = data.get("title")
                    if title:
                        return f"ytsearch1:{title} official audio"

            # Dự phòng quét thẻ OpenGraph trên trang web
            async with session.get(url, timeout=10) as resp:
                if resp.status == 200:
                    soup = BeautifulSoup(await resp.text(), "html.parser")
                    og_title = soup.find("meta", property="og:title")
                    og_desc = soup.find("meta", property="og:description")
                    title_text = og_title["content"] if og_title and og_title.get("content") else ""
                    desc_text = og_desc["content"].split("·")[0].strip() if og_desc and og_desc.get("content") else ""
                    if title_text:
                        return f"ytsearch1:{title_text} {desc_text} audio".strip()
        except Exception:
            pass
        return None

    # --- XỬ LÝ CHUYÊN BIỆT CHO PINTEREST & PIXIV (HẠNG MỤC 1) ---
    async def _handle_pinterest_pixiv(self, message: discord.Message, url: str, msg: discord.Message, mode: str, max_size: int) -> bool:
        """Trích xuất ảnh gốc / GIF / Video từ Pinterest và Pixiv."""
        if mode == "audio":
            await msg.edit(content="⚠️ Kênh này đang ở chế độ **Chỉ tải Âm thanh (MP3)**, không hỗ trợ link hình ảnh Pinterest/Pixiv.")
            return False

        session = await self.get_session()
        lower_url = url.lower()

        # 1. Xử lý Pixiv qua API JSON của Phixiv / Ajax Pixiv
        if "pixiv.net" in lower_url:
            await msg.edit(content="🎨 Đang trích xuất tác phẩm từ Pixiv...")
            artwork_match = re.search(r'artworks/(\d+)', url)
            if not artwork_match:
                await msg.edit(content="❌ Không tìm thấy ID tác phẩm Pixiv hợp lệ.")
                return False

            illust_id = artwork_match.group(1)
            try:
                api_url = f"https://www.phixiv.net/api/info?id={illust_id}"
                async with session.get(api_url, timeout=15) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        title = (data.get("title") or f"Pixiv #{illust_id}")[:250]
                        author_name = data.get("author_name") or "Artist"
                        image_urls = data.get("image_proxy_urls") or []

                        if image_urls:
                            embed = discord.Embed(
                                title=f"🎨 {title}",
                                url=url,
                                description=f"Minh họa bởi **{author_name}**",
                                color=discord.Color.blue()
                            )
                            embed.set_footer(text=f"Yêu cầu bởi {message.author.display_name}", icon_url=message.author.display_avatar.url)

                            tasks = [
                                self._download_single_image(session, img_url, i, max_size)
                                for i, img_url in enumerate(image_urls[:10])
                            ]
                            results = await asyncio.gather(*tasks)
                            files = [f for f in results if f is not None]

                            view = DownloadActionView(self, message.author.id, url, show_mp3_btn=False, show_gif_btn=False)
                            if files:
                                sent_msg = await self._reply_or_send(message, embed=embed, files=files, view=view)
                            else:
                                embed.set_image(url=image_urls[0])
                                sent_msg = await self._reply_or_send(message, embed=embed, view=view)

                            view.message = sent_msg
                            await msg.delete()
                            await self._suppress_source_embed(message)
                            return True
            except Exception:
                pass

        # 2. Xử lý Pinterest (Hỗ trợ cả Ảnh, GIF và Video Pin)
        if "pinterest.com" in lower_url or "pin.it" in lower_url:
            await msg.edit(content="📌 Đang trích xuất nội dung từ Pinterest...")
            try:
                async with session.get(url, timeout=15) as resp:
                    if resp.status == 200:
                        html = await resp.text()
                        soup = BeautifulSoup(html, "html.parser")

                        og_title = soup.find("meta", property="og:title")
                        og_image = soup.find("meta", property="og:image")
                        og_video = soup.find("meta", property="og:video") or soup.find("meta", property="og:video:secure_url")

                        title = (og_title["content"] if og_title and og_title.get("content") else "Pinterest Pin")[:250]
                        image_url = og_image["content"] if og_image and og_image.get("content") else None
                        video_url = og_video["content"] if og_video and og_video.get("content") else None

                        # Nâng cấp link ảnh Pinterest lên độ phân giải gốc (originals)
                        if image_url:
                            image_url = re.sub(r'/\d+x/', '/originals/', image_url)

                        embed = discord.Embed(title=f"📌 {title}", url=url, color=discord.Color.red())
                        embed.set_footer(text=f"Yêu cầu bởi {message.author.display_name}", icon_url=message.author.display_avatar.url)

                        # Nếu Pin là Video và kênh không bị khóa ở chế độ chỉ tải ảnh
                        if video_url and mode == "all":
                            video_bytes = await self._fetch_media_safe(session, video_url, max_size, timeout=30)
                            if video_bytes:
                                view = DownloadActionView(self, message.author.id, url, direct_video_url=video_url, show_mp3_btn=False, show_gif_btn=True)
                                sent_msg = await self._reply_or_send(
                                    message,
                                    embed=embed,
                                    file=discord.File(io.BytesIO(video_bytes), filename="pinterest.mp4"),
                                    view=view
                                )
                                view.message = sent_msg
                                await msg.delete()
                                await self._suppress_source_embed(message)
                                return True

                        # Nếu Pin là Ảnh hoặc GIF (hoặc kênh đang ở chế độ chỉ tải ảnh)
                        if image_url:
                            ext = "gif" if ".gif" in image_url.lower() else "jpg"
                            img_bytes = await self._fetch_media_safe(session, image_url, max_size, timeout=20)
                            view = DownloadActionView(self, message.author.id, url, show_mp3_btn=False, show_gif_btn=False)
                            if img_bytes:
                                sent_msg = await self._reply_or_send(
                                    message,
                                    embed=embed,
                                    file=discord.File(io.BytesIO(img_bytes), filename=f"pinterest.{ext}"),
                                    view=view
                                )
                            else:
                                embed.set_image(url=image_url)
                                sent_msg = await self._reply_or_send(message, embed=embed, view=view)

                            view.message = sent_msg
                            await msg.delete()
                            await self._suppress_source_embed(message)
                            return True
            except Exception:
                pass

        return False

    # --- XỬ LÝ ALBUM NHIỀU ẢNH / VIDEO CHO X (TWITTER) QUA VXTWITTER API (HẠNG MỤC 2) ---
    async def _handle_twitter_carousel(self, message: discord.Message, url: str, msg: discord.Message, mode: str, max_size: int) -> bool:
        """Hỗ trợ tải trọn bộ nhiều ảnh (Gallery) hoặc Video từ X/Twitter."""
        if mode == "audio":
            return False  # Để yt-dlp xử lý tách MP3

        tweet_match = re.search(r'(?:twitter\.com|x\.com)/([^/]+)/status/(\d+)', url)
        if not tweet_match:
            return False

        user_handle, status_id = tweet_match.groups()
        api_url = f"https://api.vxtwitter.com/{user_handle}/status/{status_id}"
        session = await self.get_session()

        try:
            async with session.get(api_url, timeout=15) as resp:
                if resp.status != 200:
                    return False
                data = await resp.json()

            media_list = data.get("media_extended") or []
            if not media_list:
                return False

            text = (data.get("text") or "Bài đăng trên X")[:250]
            author_name = f"{data.get('user_name', user_handle)} (@{data.get('user_screen_name', user_handle)})"
            likes = data.get("likes", 0)
            retweets = data.get("retweets", 0)
            replies = data.get("replies", 0)

            embed = discord.Embed(
                title=f"🐦 {text}",
                url=url,
                description=f"Đăng bởi **{author_name}**",
                color=discord.Color.dark_grey()
            )
            embed.add_field(name="❤️ Lượt thích", value=f"{likes:,}", inline=True)
            embed.add_field(name="🔁 Đăng lại", value=f"{retweets:,}", inline=True)
            embed.add_field(name="💬 Bình luận", value=f"{replies:,}", inline=True)
            embed.set_footer(text=f"Yêu cầu bởi {message.author.display_name}", icon_url=message.author.display_avatar.url)

            images = [m["url"] for m in media_list if m.get("type") == "image" and m.get("url")]
            videos = [m["url"] for m in media_list if m.get("type") in ("video", "gif") and m.get("url")]

            # Nếu kênh chuyên Ảnh hoặc bài đăng chứa bộ ảnh
            if images and (mode == "image" or not videos):
                await msg.edit(content=f"🖼️ Đang tải {len(images)} ảnh từ X/Twitter...")
                tasks = [
                    self._download_single_image(session, img_url, i, max_size)
                    for i, img_url in enumerate(images[:10])
                ]
                results = await asyncio.gather(*tasks)
                files = [f for f in results if f is not None]
                if files:
                    view = DownloadActionView(self, message.author.id, url, show_mp3_btn=False, show_gif_btn=False)
                    sent_msg = await self._reply_or_send(message, embed=embed, files=files, view=view)
                    view.message = sent_msg
                    await msg.delete()
                    await self._suppress_source_embed(message)
                    return True

            # Nếu bài đăng chứa Video và kênh ở chế độ 'all'
            if videos and mode == "all":
                await msg.edit(content="⏳ Đang tải video từ X/Twitter...")
                video_url = videos[0]
                video_bytes = await self._fetch_media_safe(session, video_url, max_size, timeout=30)
                if video_bytes:
                    view = DownloadActionView(
                        self,
                        message.author.id,
                        url,
                        direct_video_url=video_url,
                        show_mp3_btn=True,
                        show_gif_btn=True
                    )
                    sent_msg = await self._reply_or_send(
                        message,
                        embed=embed,
                        file=discord.File(io.BytesIO(video_bytes), filename="twitter_video.mp4"),
                        view=view
                    )
                    view.message = sent_msg
                    await msg.delete()
                    await self._suppress_source_embed(message)
                    return True
        except Exception:
            pass

        return False

    # --- NHÓM LỆNH HYBRID /dl (TỐI ƯU HÓA SLASH COMMANDS) ---
    @commands.hybrid_group(name="dl", aliases=["download", "download_toggle"], description="Quản lý Bật/Tắt và Tải phương tiện mạng xã hội")
    async def dl_group(self, ctx: commands.Context):
        """Xem bảng cấu hình tải phương tiện khi không truyền lệnh con."""
        if ctx.invoked_subcommand is None:
            await self.download_toggle(ctx)

    @dl_group.command(
        name="video",
        aliases=["media"],
        description="📥 Tải video, ảnh hoặc nhạc từ liên kết mạng xã hội bất kỳ"
    )
    @app_commands.describe(url="Đường dẫn (URL) TikTok, YouTube, FB, IG, X, Pinterest, SoundCloud, Spotify...")
    async def slash_dl_video(self, ctx: commands.Context, url: str):
        await self.dlvideo(ctx, url)

    @dl_group.command(
        name="tiktok",
        description="📱 Xem trước & chọn chất lượng tải Video, Album ảnh Slideshow hoặc MP3 từ TikTok & Douyin"
    )
    @app_commands.describe(url="Đường dẫn (URL) video hoặc bài đăng album ảnh TikTok / Douyin")
    async def slash_dl_tiktok(self, ctx: commands.Context, url: str):
        await self.tiktok(ctx, url)

    @dl_group.command(
        name="config",
        aliases=["toggle"],
        description="Quản lý Bật/Tắt và Chế độ tự động tải phương tiện"
    )
    @app_commands.describe(
        scope="Phạm vi hoặc tính năng muốn cài đặt (Server / Kênh / Chế độ kênh / Toàn cục)",
        mode="Trạng thái Bật/Tắt hoặc Chế độ tải (Tất cả / Chỉ Ảnh / Chỉ MP3)"
    )
    @app_commands.choices(
        scope=[
            app_commands.Choice(name="🏠 Máy chủ này (Server)", value="server"),
            app_commands.Choice(name="💬 Kênh hiện tại (Channel)", value="channel"),
            app_commands.Choice(name="🎛️ Chế độ Kênh (All / Ảnh / MP3)", value="mode"),
            app_commands.Choice(name="🌐 Toàn hệ thống (Chỉ Owner)", value="global"),
        ],
        mode=[
            app_commands.Choice(name="🟢 Bật (On)", value="on"),
            app_commands.Choice(name="🔴 Tắt (Off)", value="off"),
            app_commands.Choice(name="🎬 Chế độ: Tải Tất Cả (Video + Ảnh + MP3)", value="all"),
            app_commands.Choice(name="🖼️ Chế độ: Chỉ tải Ảnh (Slide / Art / Thumbnail)", value="image"),
            app_commands.Choice(name="🎵 Chế độ: Chỉ tải Âm thanh (MP3)", value="audio"),
        ]
    )
    @has_admin_role()
    async def slash_dl_config(self, ctx: commands.Context, scope: str = None, mode: str = None):
        await self.download_toggle(ctx, scope, mode)

    # --- HÀM XỬ LÝ CẤU HÌNH TẢI / PREFIX !dl ---
    @has_admin_role()
    async def download_toggle(self, ctx: commands.Context, scope: str = None, mode: str = None):
        """
        Quản lý Bật/Tắt và Chế độ tự động tải (Hỗ trợ cả Slash /dl và Prefix !dl):
        - /dl                        : Xem bảng cấu hình hiện tại
        - /dl server on/off          : Bật/Tắt cho toàn bộ Server hiện tại
        - /dl channel on/off         : Bật/Tắt riêng cho Kênh hiện tại
        - /dl mode <all|image|audio> : Đặt kênh hiện tại chỉ tải Ảnh, chỉ tải Audio hoặc Tất cả
        """
        guild_id = ctx.guild.id if ctx.guild else None
        channel_id = ctx.channel.id

        if scope and scope.lower() in ("on", "off") and mode is None:
            mode = scope.lower()
            scope = "server"
        elif scope:
            scope = scope.lower()
            mode = mode.lower() if mode else None

        # Tự động nhận diện nếu người dùng chọn trực tiếp mode image/audio/all trong Slash Command
        if mode in ("image", "audio", "all") and scope not in ("mode", "chedo", "type"):
            scope = "mode"

        mode_labels = {
            "all": "🎬 Tất cả (Video + Ảnh + MP3)",
            "image": "🖼️ Chỉ tải Ảnh (Slide / Art / Thumbnail)",
            "audio": "🎵 Chỉ tải Âm thanh (MP3)"
        }
        current_ch_mode = self.get_channel_mode(channel_id)

        # Hiển thị bảng trạng thái nếu không truyền đủ tham số
        if scope is None or mode is None:
            global_st = "🟢 Đang Bật" if self.config.get("global_enabled", True) else "🔴 Đang Tắt"
            server_st = "🔴 Đang Tắt" if (guild_id in self.config.get("disabled_guilds", [])) else "🟢 Đang Bật"
            channel_st = "🔴 Đang Tắt" if (channel_id in self.config.get("disabled_channels", [])) else "🟢 Đang Bật"
            max_mb = self._get_max_filesize(ctx.guild) / 1024 / 1024

            embed = discord.Embed(
                title="⚙️ CẤU HÌNH HỆ THỐNG TẢI ĐA NỀN TẢNG",
                description=(
                    f"🌐 **Toàn hệ thống (Global):** `{global_st}`\n"
                    f"🏠 **Máy chủ này (Server):** `{server_st}`\n"
                    f"💬 **Kênh hiện tại ({ctx.channel.mention}):** `{channel_st}`\n"
                    f"🎛️ **Chế độ kênh hiện tại:** `{mode_labels.get(current_ch_mode, mode_labels['all'])}`\n"
                    f"📦 **Giới hạn dung lượng Server:** `{max_mb:.1f} MB`\n\n"
                    f"**Hướng dẫn lệnh dành cho Admin (`/dl` hoặc `{ctx.prefix}dl`):**\n"
                    f"• `{ctx.prefix}dl on` / `off` : Bật/Tắt toàn Server\n"
                    f"• `{ctx.prefix}dl channel on` / `off` : Bật/Tắt riêng Kênh này\n"
                    f"• `{ctx.prefix}dl mode image` : Đặt kênh này **chỉ tải Ảnh**\n"
                    f"• `{ctx.prefix}dl mode audio` : Đặt kênh này **chỉ tải MP3**\n"
                    f"• `{ctx.prefix}dl mode all` : Đặt kênh về mặc định (tải mọi thứ)\n"
                    f"• `{ctx.prefix}dl global on` / `off` : Bật/Tắt toàn hệ thống (Owner)"
                ),
                color=discord.Color.orange()
            )
            embed.set_footer(text=f"Yêu cầu bởi {ctx.author.display_name}", icon_url=ctx.author.display_avatar.url)
            return await ctx.send(embed=embed)

        # Xử lý cài đặt Chế độ kênh (!dl mode <all|image|audio>)
        if scope in ("mode", "chedo", "type"):
            channel_modes = self.config.setdefault("channel_modes", {})
            if mode in ("image", "img", "photo", "anh", "pic"):
                channel_modes[str(channel_id)] = "image"
                self._save_config()
                return await ctx.send(f"🖼️ Đã đặt kênh {ctx.channel.mention} thành chế độ: **CHỈ TẢI ẢNH** (Hỗ trợ TikTok Slide, Pinterest, Pixiv, X Gallery & Thumbnail).")
            elif mode in ("audio", "mp3", "music", "nhac", "sound"):
                channel_modes[str(channel_id)] = "audio"
                self._save_config()
                return await ctx.send(f"🎵 Đã đặt kênh {ctx.channel.mention} thành chế độ: **CHỈ TẢI ÂM THANH (MP3)** (Tự động tách nhạc từ TikTok, YouTube, SoundCloud, Spotify...).")
            elif mode in ("all", "default", "reset", "video", "normal"):
                channel_modes.pop(str(channel_id), None)
                self._save_config()
                return await ctx.send(f"🎬 Đã đặt kênh {ctx.channel.mention} về chế độ mặc định: **TẢI TẤT CẢ (Video + Ảnh + MP3 + GIF)**.")
            else:
                return await ctx.send(f"⚠️ Chế độ không hợp lệ! Hãy chọn: `{ctx.prefix}dl mode image`, `{ctx.prefix}dl mode audio` hoặc `{ctx.prefix}dl mode all`.")

        if mode not in ("on", "off"):
            return await ctx.send(f"⚠️ Tham số không hợp lệ! Gõ `{ctx.prefix}dl` hoặc `/dl` để xem hướng dẫn chi tiết.")

        enable = (mode == "on")

        # 1. Phạm vi Toàn cục (Chỉ Owner)
        if scope == "global":
            if ctx.author.id != OWNER_ID:
                return await ctx.send("❌ Chỉ Chủ Bot mới có quyền bật/tắt trên toàn hệ thống!")
            self.config["global_enabled"] = enable
            self._save_config()
            status_text = "🟢 ĐÃ BẬT" if enable else "🔴 ĐÃ TẮT"
            return await ctx.send(f"🌐 Hệ thống tải tự động toàn cục: **{status_text}**.")

        # 2. Phạm vi Kênh hiện tại
        elif scope in ("channel", "chan", "kenh"):
            disabled_channels = self.config.setdefault("disabled_channels", [])
            if enable and channel_id in disabled_channels:
                disabled_channels.remove(channel_id)
            elif not enable and channel_id not in disabled_channels:
                disabled_channels.append(channel_id)
            self._save_config()
            status_text = "🟢 ĐÃ BẬT" if enable else "🔴 ĐÃ TẮT"
            return await ctx.send(f"💬 Tự động tải tại kênh {ctx.channel.mention}: **{status_text}**.")

        # 3. Phạm vi Server hiện tại
        elif scope in ("server", "guild", "sv"):
            if not guild_id:
                return await ctx.send("❌ Không thể dùng lệnh này trong tin nhắn riêng (DM).")
            disabled_guilds = self.config.setdefault("disabled_guilds", [])
            if enable and guild_id in disabled_guilds:
                disabled_guilds.remove(guild_id)
            elif not enable and guild_id not in disabled_guilds:
                disabled_guilds.append(guild_id)
            self._save_config()
            status_text = "🟢 ĐÃ BẬT" if enable else "🔴 ĐÃ TẮT"
            return await ctx.send(f"🏠 Tự động tải trên toàn máy chủ **{ctx.guild.name}**: **{status_text}**.")

    async def _extract_tiktok_metadata(self, url: str) -> tuple[dict | None, str]:
        """Trích xuất toàn bộ dữ liệu & tùy chọn chất lượng từ TikTok / Douyin (Video HD/SD, Có logo, MP3, Album ảnh)."""
        session = await self.get_session()
        canonical_url = url.strip()

        # 1. Giải phóng link rút gọn nếu là vt.tiktok.com, vm.tiktok.com, v.douyin.com...
        try:
            async with session.head(canonical_url, allow_redirects=True, timeout=10) as head_resp:
                canonical_url = str(head_resp.url)
        except Exception:
            pass

        # 2. Truy vấn API TikWM với tham số hd=1
        try:
            async with session.post("https://www.tikwm.com/api/", data={"url": canonical_url, "hd": 1}, timeout=20) as resp:
                if resp.status == 200:
                    api_data = await resp.json()
                    if api_data.get("code") == 0 and api_data.get("data"):
                        return api_data["data"], canonical_url
        except Exception:
            pass

        # 3. Dự phòng: Thử lại không kèm tham số hd
        try:
            async with session.post("https://www.tikwm.com/api/", data={"url": canonical_url}, timeout=20) as resp:
                if resp.status == 200:
                    api_data = await resp.json()
                    if api_data.get("code") == 0 and api_data.get("data"):
                        return api_data["data"], canonical_url
        except Exception:
            pass

        # 4. Dự phòng 2: Trích xuất thông tin qua yt-dlp
        try:
            ydl_opts = {'quiet': True, 'noplaylist': True, 'cookiefile': 'cookies.txt'}
            info, _ = await asyncio.to_thread(self._run_ytdl_sync, canonical_url, ydl_opts, False)
            if info:
                simulated_data = {
                    "title": info.get("title") or "Video TikTok",
                    "play": info.get("url"),
                    "cover": info.get("thumbnail"),
                    "duration": info.get("duration", 0),
                    "author": {
                        "nickname": info.get("uploader") or info.get("channel") or "TikTok User",
                        "unique_id": info.get("uploader_id") or ""
                    },
                    "digg_count": info.get("like_count") or 0,
                    "comment_count": info.get("comment_count") or 0,
                    "play_count": info.get("view_count") or 0,
                    "music_info": {
                        "title": info.get("track") or "Âm thanh gốc"
                    }
                }
                return simulated_data, canonical_url
        except Exception:
            pass

        return None, canonical_url

    @commands.command(
        name="tiktok",
        description="📱 Xem trước & chọn chất lượng tải Video, Album ảnh Slideshow hoặc MP3 từ TikTok & Douyin"
    )
    async def tiktok(self, ctx: commands.Context, url: str):
        if not self.is_download_allowed(ctx.guild.id if ctx.guild else None, ctx.channel.id):
            embed = discord.Embed(
                title=t(ctx.guild, "DOWNLOAD_MAINTENANCE_TITLE"),
                description=t(ctx.guild, "DOWNLOAD_MAINTENANCE_DESC"),
                color=discord.Color.red()
            )
            return await ctx.send(embed=embed)

        lower_url = url.lower().strip()
        if not any(d in lower_url for d in ("tiktok.com", "douyin.com")):
            return await ctx.send(
                "⚠️ Lệnh `/tiktok` chuyên biệt dành cho **TikTok** và **Douyin**.\n"
                "👉 Nếu bạn muốn tải từ các nền tảng khác (YouTube, Facebook, Instagram, Twitter...), vui lòng dùng lệnh `/dlvideo`!",
                ephemeral=True
            )

        msg = await ctx.send("🔍 Đang kết nối TikTok, trích xuất dữ liệu & tạo bản xem trước...")

        data, canonical_url = await self._extract_tiktok_metadata(url)
        if not data:
            return await msg.edit(
                content="❌ Không thể lấy dữ liệu từ liên kết TikTok này. Vui lòng kiểm tra lại đường dẫn hoặc trạng thái bài viết (có thể ở chế độ riêng tư hoặc đã bị xóa)."
            )

        # 1. Trường hợp bài đăng là Bộ ảnh trình chiếu (Photo Slideshow)
        images = data.get("images") or []
        if images and isinstance(images, list):
            view = TikTokPhotoPreviewView(self, ctx.author.id, canonical_url, data, images, guild=ctx.guild)
            embed = view.get_embed()
            view.message = await msg.edit(content=None, embed=embed, view=view)
            return

        # 2. Trường hợp bài đăng là Video (Cho phép xem trước, chọn chất lượng HD / SD / Có logo / MP3 / GIF)
        view = TikTokVideoPreviewView(self, ctx.author.id, canonical_url, data, guild=ctx.guild)
        embed = view.get_embed()
        view.message = await msg.edit(content=None, embed=embed, view=view)

    @commands.command(
        name="dlvideo",
        description="📥 Tải video, ảnh hoặc nhạc từ liên kết mạng xã hội bất kỳ"
    )
    async def dlvideo(self, ctx: commands.Context, url: str):
        if not self.is_download_allowed(ctx.guild.id if ctx.guild else None, ctx.channel.id):
            embed = discord.Embed(
                title=t(ctx.guild, "DOWNLOAD_MAINTENANCE_TITLE"),
                description=t(ctx.guild, "DOWNLOAD_MAINTENANCE_DESC"),
                color=discord.Color.red()
            )
            return await ctx.send(embed=embed)

        channel_mode = self.get_channel_mode(ctx.channel.id)
        msg = await ctx.send(t(ctx.guild, "DOWNLOAD_LOADING"))
        await self._handle_video_download(ctx.message, url, msg=msg, mode=channel_mode)

    async def _create_platform_embed(self, data: dict, author: discord.User, original_url: str, mode: str = "all") -> discord.Embed:
        """Tạo Embed thông tin chi tiết tùy chỉnh theo từng nền tảng và chế độ kênh."""
        extractor = data.get('extractor_key', '').lower()

        title = (data.get("title") or "Nội dung chia sẻ")[:250]
        uploader = data.get("uploader") or data.get("channel") or "Không rõ"
        duration = data.get("duration") or 0
        webpage_url = data.get("webpage_url") or original_url
        thumbnail = data.get("thumbnail")
        duration_text = str(datetime.timedelta(seconds=int(duration))) if duration > 0 else "N/A"

        views = data.get("view_count") or 0
        likes = data.get("like_count") or 0
        comments = data.get("comment_count") or 0
        reposts = data.get("repost_count") or 0

        prefix_icon = "🎶" if mode == "audio" else ("🖼️" if mode == "image" else "🎬")

        if "spotify.com" in original_url.lower():
            embed = discord.Embed(title=f"🟢 {title}", url=original_url, description=f"Nghệ sĩ / Kênh: **{uploader}**", color=discord.Color.green())
            embed.add_field(name="⏱️ Thời lượng", value=duration_text, inline=True)
            embed.add_field(name="🎧 Nguồn phát", value="Spotify ➔ YouTube Audio", inline=True)

        elif 'soundcloud' in extractor:
            embed = discord.Embed(title=f"☁️ {title}", url=webpage_url, description=f"Nghệ sĩ: **{uploader}**", color=discord.Color.orange())
            embed.add_field(name="👂 Lượt nghe", value=f"{views:,}", inline=True)
            embed.add_field(name="❤️ Yêu thích", value=f"{likes:,}", inline=True)
            embed.add_field(name="⏱️ Thời lượng", value=duration_text, inline=True)

        elif 'youtube' in extractor:
            embed = discord.Embed(title=f"{prefix_icon} {title}", url=webpage_url, description=f"Đăng bởi **{uploader}**", color=discord.Color.red())
            upload_date = data.get("upload_date")
            embed.add_field(name="👀 Lượt xem", value=f"{views:,}", inline=True)
            embed.add_field(name="👍 Lượt thích", value=f"{likes:,}", inline=True)
            embed.add_field(name="⏱️ Thời lượng", value=duration_text, inline=True)
            if upload_date and len(upload_date) == 8:
                embed.add_field(name="📅 Ngày đăng", value=f"{upload_date[6:8]}/{upload_date[4:6]}/{upload_date[0:4]}", inline=True)

        elif 'facebook' in extractor:
            embed = discord.Embed(title=f"{prefix_icon} {title}", url=webpage_url, description=f"Đăng bởi **{uploader}**", color=discord.Color.blue())
            embed.add_field(name="👍 Lượt thích", value=f"{likes:,}", inline=True)
            embed.add_field(name="💬 Bình luận", value=f"{comments:,}", inline=True)
            embed.add_field(name="⏱️ Thời lượng", value=duration_text, inline=True)

        elif 'instagram' in extractor:
            embed = discord.Embed(title=f"{prefix_icon} {title}", url=webpage_url, description=f"Đăng bởi **{uploader}**", color=discord.Color.purple())
            embed.add_field(name="❤️ Lượt thích", value=f"{likes:,}", inline=True)
            embed.add_field(name="💬 Bình luận", value=f"{comments:,}", inline=True)
            embed.add_field(name="⏱️ Thời lượng", value=duration_text, inline=True)

        elif 'twitter' in extractor or 'x' in extractor:
            embed = discord.Embed(title=f"{prefix_icon} {title}", url=webpage_url, description=f"Đăng bởi **{uploader}**", color=discord.Color.dark_grey())
            embed.add_field(name="❤️ Lượt thích", value=f"{likes:,}", inline=True)
            embed.add_field(name="🔁 Đăng lại", value=f"{reposts:,}", inline=True)
            embed.add_field(name="👀 Lượt xem", value=f"{views:,}", inline=True)

        elif 'reddit' in extractor:
            embed = discord.Embed(title=f"{prefix_icon} {title}", url=webpage_url, description=f"Đăng bởi **u/{uploader}**", color=discord.Color.orange())
            embed.add_field(name="⬆️ Upvotes", value=f"{likes:,}", inline=True)
            embed.add_field(name="💬 Bình luận", value=f"{comments:,}", inline=True)
            embed.add_field(name="⏱️ Thời lượng", value=duration_text, inline=True)

        else:
            embed = discord.Embed(title=f"{prefix_icon} {title}", url=webpage_url, description=f"Đăng bởi **{uploader}**", color=discord.Color.random())
            embed.add_field(name="👀 Lượt xem", value=f"{views:,}", inline=True)
            embed.add_field(name="❤️ Lượt thích", value=f"{likes:,}", inline=True)
            embed.add_field(name="⏱️ Thời lượng", value=duration_text, inline=True)
            if comments:
                embed.add_field(name="💬 Bình luận", value=f"{comments:,}", inline=True)
            if reposts:
                embed.add_field(name="🔁 Chia sẻ", value=f"{reposts:,}", inline=True)

        if thumbnail:
            embed.set_thumbnail(url=thumbnail)
        embed.set_footer(text=f"Yêu cầu bởi {author.display_name}", icon_url=author.display_avatar.url)
        return embed

    async def _handle_video_download(self, message: discord.Message, url: str, msg: discord.Message = None, mode: str = "all") -> bool:
        """Hàm xử lý đa nền tảng hỗ trợ cả Video, Audio (SoundCloud/Spotify), và Image (Pinterest/Pixiv/X)."""
        is_owner = message.author.id == OWNER_ID
        max_size = self._get_max_filesize(message.guild)
        lower_url = url.lower()

        if msg is None:
            msg = await message.channel.send("⏳ Đang phân tích liên kết...")

        # 1. Nếu là link Pinterest hoặc Pixiv -> Chuyển qua bộ xử lý Ảnh/Art chuyên biệt
        if any(d in lower_url for d in ("pinterest.com", "pin.it", "pixiv.net")):
            handled = await self._handle_pinterest_pixiv(message, url, msg, mode, max_size)
            if handled:
                return True

        # 2. Nếu là link X / Twitter -> Ưu tiên thử vxtwitter API để bắt trọn bộ nhiều ảnh (Carousel) hoặc Video nhanh
        if any(d in lower_url for d in ("twitter.com", "x.com")) and mode != "audio":
            handled = await self._handle_twitter_carousel(message, url, msg, mode, max_size)
            if handled:
                return True

        # 3. Nếu là link nhạc (Spotify / SoundCloud) -> Tự động ép sang chế độ tải Audio (MP3)
        is_music_platform = any(d in lower_url for d in ("spotify.com", "soundcloud.com"))
        if is_music_platform:
            if mode == "image":
                await msg.edit(content="⚠️ Kênh này đang ở chế độ **Chỉ tải Hình ảnh**, không hỗ trợ tải nhạc từ Spotify/SoundCloud.")
                return False
            mode = "audio"

        target_url = url
        if "spotify.com" in lower_url:
            await msg.edit(content="🟢 Đang tìm kiếm bản âm thanh chất lượng cao cho bài hát Spotify...")
            resolved_query = await self._resolve_spotify_to_ytsearch(url)
            if not resolved_query:
                await msg.edit(content="❌ Không thể đọc thông tin bài hát từ liên kết Spotify này (Hãy đảm bảo đây là link Track/Bài hát).")
                return False
            target_url = resolved_query

        status_text = (
            "🎵 Đang trích xuất âm thanh (MP3)..." if mode == "audio"
            else ("🖼️ Đang trích xuất hình ảnh..." if mode == "image" else "⏳ Đang xử lý và tải video...")
        )
        await msg.edit(content=status_text)

        file_path = None
        try:
            # --- CHẾ ĐỘ 1: CHỈ TẢI ẢNH (Lấy Thumbnail/Ảnh gốc không cần tải video) ---
            if mode == "image":
                async with self.ytdl_semaphore:
                    data, _ = await asyncio.to_thread(self._run_ytdl_sync, target_url, None, False)
                if not data:
                    await msg.edit(content="❌ Không lấy được thông tin hình ảnh từ liên kết này.")
                    return False

                embed = await self._create_platform_embed(data, message.author, url, mode="image")
                thumb_url = data.get("thumbnail")
                if not thumb_url:
                    await msg.edit(content="❌ Liên kết này không có hình ảnh hoặc ảnh bìa để tải.")
                    return False

                session = await self.get_session()
                img_file = await self._download_single_image(session, thumb_url, 1, max_size)
                view = DownloadActionView(self, message.author.id, url, show_mp3_btn=True, show_gif_btn=False)

                if img_file:
                    sent_msg = await self._reply_or_send(message, embed=embed, file=img_file, view=view)
                else:
                    embed.set_image(url=thumb_url)
                    sent_msg = await self._reply_or_send(message, embed=embed, view=view)

                view.message = sent_msg
                await msg.delete()
                await self._suppress_source_embed(message)
                return True

            # --- CHẾ ĐỘ 2 & 3: CHỈ TẢI AUDIO HOẶC TẢI VIDEO ---
            os.makedirs(TEMP_DOWNLOADS_DIR, exist_ok=True)
            unique_prefix = f"{mode}_{message.id}"

            if mode == "audio":
                ydl_opts = {
                    'outtmpl': f'{TEMP_DOWNLOADS_DIR}/{unique_prefix}_%(id)s.%(ext)s',
                    'quiet': True,
                    'noplaylist': True,
                    'cookiefile': 'cookies.txt',
                    'max_filesize': max_size,
                    'format': f'bestaudio[filesize<{max_size}]/best[filesize<{max_size}]/bestaudio/best',
                }
            else:
                ydl_opts = {
                    'outtmpl': f'{TEMP_DOWNLOADS_DIR}/{unique_prefix}_%(id)s.%(ext)s',
                    'quiet': True,
                    'noplaylist': True,
                    'cookiefile': 'cookies.txt',
                    'max_filesize': max_size,
                    'format': (
                        f'best[filesize<{max_size}][ext=mp4]/'
                        f'best[filesize_approx<{max_size}][ext=mp4]/'
                        f'bestvideo[filesize<{max_size}][ext=mp4]+bestaudio[ext=m4a]/'
                        f'best[filesize<{max_size}]/best'
                    ),
                    'merge_output_format': 'mp4',
                }

            async with self.ytdl_semaphore:
                data, file_path = await asyncio.to_thread(self._run_ytdl_sync, target_url, ydl_opts, True)

            if not data or not file_path or not os.path.exists(file_path):
                await msg.edit(content="❌ Không tải được nội dung (có thể do vượt quá giới hạn dung lượng).")
                return False

            actual_size = os.path.getsize(file_path)
            if actual_size > max_size:
                await msg.edit(
                    content=f"❌ File tải về (`{actual_size / 1024 / 1024:.2f} MB`) vượt quá giới hạn của máy chủ (`{max_size / 1024 / 1024:.1f} MB`)."
                )
                return False

            embed = await self._create_platform_embed(data, message.author, url, mode=mode)
            view = DownloadActionView(
                self,
                message.author.id,
                url,
                show_mp3_btn=(mode != "audio"),
                show_gif_btn=(mode == "all")
            )
            send_filename = "audio.mp3" if mode == "audio" else os.path.basename(file_path)

            try:
                sent_msg = await self._reply_or_send(
                    message,
                    embed=embed,
                    file=discord.File(file_path, filename=send_filename),
                    view=view
                )
                view.message = sent_msg
            except discord.HTTPException as e:
                if e.code == 40005:
                    await msg.edit(content=f"❌ **Lỗi Discord:** File (`{actual_size / 1024 / 1024:.2f} MB`) vượt quá giới hạn tải lên của kênh này.")
                else:
                    await msg.edit(content=f"❌ **Lỗi Discord khi gửi file:** `{e}`")
                return False

            await msg.delete()
            await self._suppress_source_embed(message)
            return True

        except yt_dlp.utils.DownloadError as e:
            if "File is larger than max-filesize" in str(e):
                await msg.edit(content=f"❌ Nội dung vượt quá giới hạn dung lượng của máy chủ (`{max_size / 1024 / 1024:.1f} MB`).")
                return False

            # Dự phòng quét ảnh Instagram hoặc HTML Video cho Owner
            if "instagram.com" in lower_url:
                try:
                    session = await self.get_session()
                    async with session.get(url, timeout=15) as resp:
                        if resp.status == 200:
                            soup = BeautifulSoup(await resp.text(), "html.parser")
                            og_img = soup.find("meta", property="og:image")
                            if og_img and og_img.get("content"):
                                img_file = await self._download_single_image(session, og_img["content"], 1, max_size)
                                if img_file:
                                    view = DownloadActionView(self, message.author.id, url, show_mp3_btn=False, show_gif_btn=False)
                                    sent_msg = await self._reply_or_send(
                                        message,
                                        content="📸 Đã trích xuất ảnh từ bài đăng Instagram:",
                                        file=img_file,
                                        view=view
                                    )
                                    view.message = sent_msg
                                    await msg.delete()
                                    await self._suppress_source_embed(message)
                                    return True
                except Exception:
                    pass

            if "Unsupported URL" in str(e) and is_owner and mode == "all":
                await msg.edit(content="⚠️ Không phải link được hỗ trợ sẵn, đang thử quét thẻ video trực tiếp...")
                try:
                    session = await self.get_session()
                    async with session.get(url, timeout=15) as response:
                        if response.status == 200:
                            soup = BeautifulSoup(await response.text(), 'html.parser')
                            video_tag = soup.find("video", src=True)
                            if video_tag:
                                video_url = video_tag['src']
                                if not video_url.startswith(('http:', 'https:')):
                                    video_url = urljoin(url, video_url)

                                video_bytes = await self._fetch_media_safe(session, video_url, max_size, timeout=30)
                                if video_bytes:
                                    view = DownloadActionView(self, message.author.id, url, direct_video_url=video_url)
                                    sent_msg = await self._reply_or_send(
                                        message,
                                        content="✅ Tải thành công bằng phương pháp quét HTML!",
                                        file=discord.File(io.BytesIO(video_bytes), filename="video.mp4"),
                                        view=view
                                    )
                                    view.message = sent_msg
                                    await msg.delete()
                                    await self._suppress_source_embed(message)
                                    return True
                except Exception as fallback_e:
                    await msg.edit(content=f"❌ Phương pháp thay thế cũng thất bại: `{fallback_e}`")
                    return False

            await msg.edit(content="❌ Lỗi tải xuống: Nội dung có thể bị giới hạn độ tuổi, riêng tư, hoặc không được hỗ trợ.")
            return False

        except Exception as e:
            await msg.edit(content=f"❌ Lỗi không xác định khi xử lý: `{e}`")
            return False

        finally:
            if file_path and os.path.exists(file_path):
                try:
                    os.remove(file_path)
                except OSError:
                    pass

    async def _reply_or_send(self, message: discord.Message, **kwargs) -> discord.Message:
        try:
            return await message.reply(**kwargs, mention_author=False)
        except discord.HTTPException:
            return await message.channel.send(**kwargs)

    async def _suppress_source_embed(self, message: discord.Message):
        """Tự động ẩn khung preview mặc định của Discord trên tin nhắn của người gửi."""
        try:
            await message.edit(suppress=True)
        except (discord.Forbidden, discord.HTTPException):
            pass

    async def resolve_redirect(self, url: str) -> str:
        session = await self.get_session()
        try:
            async with session.head(url, allow_redirects=True, timeout=5) as response:
                return str(response.url)
        except Exception:
            try:
                async with session.get(url, allow_redirects=True, timeout=5) as response:
                    return str(response.url)
            except Exception:
                return url

    async def _download_single_image(self, session: aiohttp.ClientSession, url: str, index: int, max_size: int = 8 * 1024 * 1024) -> discord.File | None:
        try:
            data = await self._fetch_media_safe(session, url, max_size=max_size, timeout=15)
            if data:
                return discord.File(io.BytesIO(data), filename=f"image_{index}.jpg")
        except Exception:
            pass
        return None

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        is_owner = message.author.id == OWNER_ID

        if message.author.bot or (not message.guild and not is_owner):
            return

        # Kiểm tra chuẩn xác xem tin nhắn có phải là một lệnh hợp lệ của Bot hay không
        ctx = await self.bot.get_context(message)
        if ctx.valid:
            return

        guild_id = message.guild.id if message.guild else None
        if not self.is_download_allowed(guild_id, message.channel.id):
            return

        content = message.content.strip()
        url_match = ALLOWED_DOMAINS_REGEX.search(content)
        if not url_match:
            return

        detected_url = url_match.group(0)
        user_id = message.author.id
        channel_mode = self.get_channel_mode(message.channel.id)

        # Kiểm tra Cooldown
        if not is_owner:
            now = time.time()
            if user_id in download_cooldown:
                remaining = int(30 - (now - download_cooldown[user_id]))
                if remaining > 0:
                    return await message.channel.send(t(message.guild, "DOWNLOAD_COOLDOWN", remain=remaining))
            download_cooldown[user_id] = now

        msg = await message.channel.send(t(message.guild, "DOWNLOAD_ANALYZING"))
        max_size = self._get_max_filesize(message.guild)

        actual_url = detected_url
        if any(domain in detected_url.lower() for domain in SHORT_DOMAINS):
            actual_url = await self.resolve_redirect(detected_url)

        session = await self.get_session()

        # --- XỬ LÝ NHANH CHO TIKTOK / DOUYIN QUA API ---
        if "tiktok.com" in actual_url or "douyin.com" in actual_url:
            await msg.edit(content="🎵 Đang xử lý link TikTok/Douyin...")
            tikwm_failed = False

            try:
                async with session.post("https://www.tikwm.com/api/", data={"url": actual_url}, timeout=20) as response:
                    if response.status != 200:
                        tikwm_failed = True
                    else:
                        api_data = await response.json()
                        if api_data.get("code") != 0:
                            tikwm_failed = True
                        else:
                            post_data = api_data.get("data", {})
                            author_info = post_data.get("author", {})
                            music_info = post_data.get("music_info", {})
                            direct_audio_url = music_info.get("play") or post_data.get("music")
                            direct_video_url = post_data.get("play")

                            embed = discord.Embed(
                                title=f"🎵 {(post_data.get('title') or 'Nội dung TikTok')[:250]}",
                                url=actual_url,
                                description=f"Đăng bởi **{author_info.get('nickname', 'N/A')}**",
                                color=discord.Color.random()
                            )
                            embed.add_field(name="❤️ Thích", value=f"{post_data.get('digg_count', 0):,}", inline=True)
                            embed.add_field(name="💬 Bình luận", value=f"{post_data.get('comment_count', 0):,}", inline=True)
                            embed.add_field(name="🔁 Chia sẻ", value=f"{post_data.get('share_count', 0):,}", inline=True)
                            if music_info:
                                embed.add_field(name="🎶 Âm nhạc", value=music_info.get('title', 'N/A'), inline=False)
                            embed.set_footer(text=f"Yêu cầu bởi {message.author.display_name}", icon_url=message.author.display_avatar.url)

                            # 1. NẾU KÊNH Ở CHẾ ĐỘ CHỈ TẢI AUDIO (MP3)
                            if channel_mode == "audio":
                                if not direct_audio_url:
                                    tikwm_failed = True
                                else:
                                    await msg.edit(content="🎶 Đang tải âm thanh MP3...")
                                    audio_bytes = await self._fetch_media_safe(session, direct_audio_url, max_size, timeout=30)
                                    if audio_bytes:
                                        view = DownloadActionView(self, message.author.id, actual_url, show_mp3_btn=False, show_gif_btn=False)
                                        audio_file = discord.File(io.BytesIO(audio_bytes), filename="tiktok_audio.mp3")
                                        sent_msg = await self._reply_or_send(message, embed=embed, file=audio_file, view=view)
                                        view.message = sent_msg
                                        await msg.delete()
                                        await self._suppress_source_embed(message)
                                        return
                                    else:
                                        tikwm_failed = True

                            # 2. NẾU KÊNH Ở CHẾ ĐỘ CHỈ TẢI ẢNH (IMAGE)
                            elif channel_mode == "image":
                                view = DownloadActionView(self, message.author.id, actual_url, direct_audio_url=direct_audio_url, show_gif_btn=False)
                                if "images" in post_data and post_data["images"]:
                                    await msg.edit(content="🖼️ Đang tải bộ ảnh...")
                                    tasks = [
                                        self._download_single_image(session, img_url, i, max_size)
                                        for i, img_url in enumerate(post_data["images"])
                                    ]
                                    results = await asyncio.gather(*tasks)
                                    files_to_send = [f for f in results if f is not None]

                                    if files_to_send:
                                        sent_msg = await self._reply_or_send(message, embed=embed, files=files_to_send[:10], view=view)
                                        view.message = sent_msg
                                        for i in range(10, len(files_to_send), 10):
                                            await message.channel.send(files=files_to_send[i:i+10])
                                        await msg.delete()
                                        await self._suppress_source_embed(message)
                                        return
                                    else:
                                        return await msg.edit(content="❌ Không tải được ảnh nào.")
                                else:
                                    cover_url = post_data.get("origin_cover") or post_data.get("cover")
                                    if cover_url:
                                        await msg.edit(content="🖼️ Kênh chuyên tải ảnh: Đang trích xuất ảnh bìa chất lượng cao...")
                                        cover_file = await self._download_single_image(session, cover_url, 1, max_size)
                                        if cover_file:
                                            sent_msg = await self._reply_or_send(message, embed=embed, file=cover_file, view=view)
                                            view.message = sent_msg
                                            await msg.delete()
                                            await self._suppress_source_embed(message)
                                            return
                                    return await msg.edit(content="⚠️ Kênh này chỉ cho phép tải hình ảnh (Link bạn gửi là Video không có ảnh trượt).")

                            # 3. NẾU KÊNH Ở CHẾ ĐỘ MẶC ĐỊNH (ALL)
                            else:
                                # Bài đăng dạng Slide nhiều ảnh (Ẩn nút tạo GIF vì là ảnh tĩnh)
                                if "images" in post_data and post_data["images"]:
                                    view = DownloadActionView(
                                        self,
                                        message.author.id,
                                        actual_url,
                                        direct_audio_url=direct_audio_url,
                                        show_gif_btn=False
                                    )
                                    await msg.edit(content="🖼️ Đang tải bộ ảnh...")
                                    tasks = [
                                        self._download_single_image(session, img_url, i, max_size)
                                        for i, img_url in enumerate(post_data["images"])
                                    ]
                                    results = await asyncio.gather(*tasks)
                                    files_to_send = [f for f in results if f is not None]

                                    if files_to_send:
                                        sent_msg = await self._reply_or_send(message, embed=embed, files=files_to_send[:10], view=view)
                                        view.message = sent_msg
                                        for i in range(10, len(files_to_send), 10):
                                            await message.channel.send(files=files_to_send[i:i+10])
                                        await msg.delete()
                                        await self._suppress_source_embed(message)
                                    else:
                                        await msg.edit(content="❌ Không tải được ảnh nào.")

                                # Bài đăng dạng Video (Hiển thị đầy đủ cả nút Tải MP3 và Tạo GIF)
                                elif direct_video_url:
                                    view = DownloadActionView(
                                        self,
                                        message.author.id,
                                        actual_url,
                                        direct_audio_url=direct_audio_url,
                                        direct_video_url=direct_video_url,
                                        show_gif_btn=True
                                    )
                                    await msg.edit(content="⏳ Đang tải video...")
                                    video_bytes = await self._fetch_media_safe(session, direct_video_url, max_size, timeout=30)
                                    if video_bytes:
                                        video_file = discord.File(io.BytesIO(video_bytes), filename="tiktok_video.mp4")
                                        sent_msg = await self._reply_or_send(message, embed=embed, file=video_file, view=view)
                                        view.message = sent_msg
                                        await msg.delete()
                                        await self._suppress_source_embed(message)
                                    else:
                                        tikwm_failed = True
            except ValueError as ve:
                return await msg.edit(content=f"❌ {ve}")
            except Exception:
                tikwm_failed = True

            # Dự phòng 1: ssstik.io (Chỉ dùng khi chế độ kênh là 'all')
            if tikwm_failed:
                if channel_mode == "all":
                    await msg.edit(content="⏳ API chính bận, đang thử API dự phòng (ssstik.io)...")
                    ssstik_failed = False
                    try:
                        async with session.get("https://ssstik.io/en", timeout=10) as home_resp:
                            home_html = await home_resp.text()
                            form_token = re.search(r'name="tt"\s+value="([^"]+)"', home_html)
                            if not form_token:
                                raise ValueError("Không tìm thấy token.")

                        post_data = {"id": actual_url, "locale": "en", "tt": form_token.group(1)}
                        async with session.post("https://ssstik.io/abc?url=dl", data=post_data, timeout=15) as dl_resp:
                            dl_html = await dl_resp.text()
                            download_link = re.search(r'href="([^"]+)"\s+class="[^"]*download_link[^"]*"', dl_html)
                            if not download_link:
                                raise ValueError("Không tìm thấy link tải.")

                            dl_url = download_link.group(1)
                            video_bytes = await self._fetch_media_safe(session, dl_url, max_size, timeout=30)
                            if not video_bytes:
                                raise ValueError("Không đọc được luồng video.")

                            view = DownloadActionView(self, message.author.id, actual_url, direct_video_url=dl_url, show_gif_btn=True)
                            sent_msg = await self._reply_or_send(
                                message,
                                file=discord.File(io.BytesIO(video_bytes), filename="video.mp4"),
                                view=view
                            )
                            view.message = sent_msg
                            await msg.delete()
                            await self._suppress_source_embed(message)
                    except ValueError as ve:
                        if "vượt quá giới hạn" in str(ve):
                            return await msg.edit(content=f"❌ {ve}")
                        ssstik_failed = True
                    except Exception:
                        ssstik_failed = True

                    if ssstik_failed:
                        await self._handle_video_download(message, actual_url, msg=msg, mode=channel_mode)
                else:
                    await self._handle_video_download(message, actual_url, msg=msg, mode=channel_mode)

        # --- XỬ LÝ CÁC NỀN TẢNG KHÁC (YouTube, FB, IG, X/Twitter, Reddit, Threads, Bilibili, Pinterest, Pixiv, SoundCloud, Spotify) ---
        else:
            await self._handle_video_download(message, actual_url, msg=msg, mode=channel_mode)


async def setup(bot):
    await bot.add_cog(Dowload(bot))
