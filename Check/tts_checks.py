import discord
import Check.dave_patch  # Kích hoạt bản vá DAVE E2EE 0.2.0 cho discord.py 2.7.1
import asyncio
import os
import re
import shutil
from gtts import gTTS
import time
from collections import deque

import emoji
import json

from Command.checks import save_json, load_json # Đảm bảo import này tồn tại
from deep_translator import GoogleTranslator

# --- BIẾN TRẠNG THÁI TOÀN CỤC CHO TTS ---

# Hàng đợi tin nhắn cho mỗi server: {guild_id: deque}
tts_queue = {}
# Trạng thái đang phát cho mỗi server: {guild_id: bool}
tts_playing = {}
# Người dùng cuối cùng nói và thời gian: {guild_id: {"id": user_id, "time": timestamp}}
last_tts_user = {}
# Kênh chat được phép dùng TTS khi bot trong voice: {guild_id: channel_id}
voice_text_channels = {}
# Tên tùy chỉnh của người dùng: {user_id: custom_name}
tts_names = load_json("tts_names.json", {})
# Ngôn ngữ TTS cho mỗi server: {guild_id: lang_code} # Sửa đổi: Cấu trúc mới cho tts_names
tts_language = load_json("tts_language.json", {}) # Ngôn ngữ của server
# Âm lượng TTS cho mỗi server: {guild_id: float}
tts_volume = load_json("tts_volume.json", {})
# Cách đọc emoji tùy chỉnh cho mỗi server: {guild_id: {emoji_id: reading}}
tts_emoji_readings = load_json("tts_emoji_readings.json", {}) # Ngôn ngữ của người dùng
tts_user_language = load_json("tts_user_language.json", {})
# Giới hạn ký tự cho mỗi server: {guild_id: int}
tts_char_limit = load_json("tts_char_limit.json", {})
# Giới hạn số lượng emoji trong một tin nhắn: {guild_id: int}
tts_emoji_count_limit = load_json("tts_emoji_count_limit.json", {})

_FFMPEG_EXECUTABLE = None

def get_ffmpeg_executable() -> str:
    """Tìm đường dẫn thực thi của FFmpeg trên mọi hệ thống (Windows, Linux, Docker, v.v.)."""
    global _FFMPEG_EXECUTABLE
    if _FFMPEG_EXECUTABLE and (os.path.exists(_FFMPEG_EXECUTABLE) or shutil.which(_FFMPEG_EXECUTABLE)):
        return _FFMPEG_EXECUTABLE

    # 1. Thử lệnh ffmpeg trong PATH
    path_exe = shutil.which("ffmpeg") or shutil.which("ffmpeg.exe")
    if path_exe:
        _FFMPEG_EXECUTABLE = path_exe
        return _FFMPEG_EXECUTABLE

    # 2. Thử imageio_ffmpeg (tự động có binary tĩnh đi kèm trên cả Windows/Linux)
    try:
        import imageio_ffmpeg
        img_exe = imageio_ffmpeg.get_ffmpeg_exe()
        if img_exe and os.path.exists(img_exe):
            _FFMPEG_EXECUTABLE = img_exe
            return _FFMPEG_EXECUTABLE
    except Exception:
        pass

    # 3. Thử các đường dẫn phổ biến
    candidate_paths = [
        os.path.join(os.getcwd(), "ffmpeg.exe"),
        os.path.join(os.getcwd(), "bin", "ffmpeg.exe"),
        os.path.join(os.getcwd(), "ffmpeg"),
        "C:\\ffmpeg\\bin\\ffmpeg.exe",
        "/usr/bin/ffmpeg",
        "/usr/local/bin/ffmpeg",
    ]
    for cp in candidate_paths:
        if os.path.exists(cp):
            _FFMPEG_EXECUTABLE = cp
            return _FFMPEG_EXECUTABLE

    _FFMPEG_EXECUTABLE = "ffmpeg"
    return _FFMPEG_EXECUTABLE

# --- HỆ THỐNG NGÔN NGỮ (i18n) - Đã chuyển sang Check.i18n ---
# Giữ compat layer để không break các import cũ
from Check.i18n import server_language, language_cache, get_guild_language, t, get_lang_string as _new_get_lang_string  # noqa: F401

# --- CÁC HÀM TIỆN ÍCH CHO TTS ---

def save_tts_names():
    """Lưu danh sách tên tùy chỉnh vào file."""
    save_json("tts_names.json", tts_names)

def save_tts_language():
    """Lưu danh sách ngôn ngữ TTS vào file."""
    save_json("tts_language.json", tts_language)

def save_tts_volume():
    """Lưu danh sách âm lượng TTS vào file."""
    save_json("tts_volume.json", tts_volume)

def save_tts_emoji_readings():
    """Lưu danh sách cách đọc emoji tùy chỉnh vào file."""
    save_json("tts_emoji_readings.json", tts_emoji_readings)

def save_tts_user_language():
    """Lưu danh sách ngôn ngữ tùy chỉnh của người dùng vào file."""
    save_json("tts_user_language.json", tts_user_language)

def save_tts_emoji_count_limit():
    """Lưu giới hạn số lượng emoji vào file."""
    save_json("tts_emoji_count_limit.json", tts_emoji_count_limit)

def save_tts_char_limit():
    """Lưu giới hạn ký tự TTS vào file."""
    save_json("tts_char_limit.json", tts_char_limit)

def save_server_language():
    """Lưu cài đặt ngôn ngữ chung của server. (compat wrapper)"""
    from Check.i18n import _save_server_language
    _save_server_language()

def get_lang_string(guild_id: int, key: str, **kwargs) -> str:
    """Compat: delegate sang Check.i18n.t() để tự động theo locale."""
    from Check.i18n import t as _t
    return _t(guild_id, key, **kwargs)

async def get_gtts_object(text: str, guild_id: int, user_id: int):
    """Tạo đối tượng gTTS với ngôn ngữ phù hợp."""
    guild_id_str = str(guild_id)
    user_id_str = str(user_id)

    # Ưu tiên ngôn ngữ của người dùng
    lang = tts_user_language.get(guild_id_str, {}).get(user_id_str)
    # Nếu không có, dùng ngôn ngữ của server, mặc định là 'vi'
    if not lang:
        lang = tts_language.get(guild_id_str, 'vi')

    # Chuẩn hóa mã ngôn ngữ
    if lang.lower() == "zh-cn":
        lang = "zh-CN"

    try:
        loop = asyncio.get_running_loop()
        tts_object = await loop.run_in_executor(None, lambda: gTTS(text=text, lang=lang, slow=False))
        return tts_object
    except Exception as e:
        print(f"Lỗi khi tạo đối tượng gTTS ({lang}): {e}")
        try:
            # Fallback về tiếng Việt nếu mã ngôn ngữ tùy chỉnh gặp lỗi
            loop = asyncio.get_running_loop()
            return await loop.run_in_executor(None, lambda: gTTS(text=text, lang='vi', slow=False))
        except Exception as e2:
            print(f"Lỗi fallback gTTS vi: {e2}")
            return None

async def play_next_tts(guild_id: int, voice_client: discord.VoiceClient, bot):
    """
    Hàm phát tin nhắn tiếp theo trong hàng đợi TTS của một server.
    """
    guild = bot.get_guild(guild_id) if bot else None
    if guild and guild.voice_client:
        voice_client = guild.voice_client

    if not voice_client or not getattr(voice_client, "is_connected", lambda: False)():
        tts_playing[guild_id] = False
        return

    # Nếu voice client đang thực sự phát âm thanh, đợi sau khi phát xong
    if hasattr(voice_client, "is_playing") and voice_client.is_playing():
        return

    # Lấy file hợp lệ tiếp theo trong hàng đợi
    file_path = None
    while tts_queue.get(guild_id):
        data = tts_queue[guild_id].popleft()
        candidate = data.get("file")
        if candidate and os.path.exists(candidate) and os.path.getsize(candidate) > 100:
            file_path = candidate
            break
        # Xóa file rỗng hoặc hỏng nếu có
        try:
            if candidate and os.path.exists(candidate):
                os.remove(candidate)
        except Exception:
            pass

    if not file_path:
        tts_playing[guild_id] = False
        return

    tts_playing[guild_id] = True
    playback_loop = asyncio.get_running_loop()

    # Hàm callback sẽ được gọi sau khi phát xong
    def after_playing(error):
        if error:
            print(f"Lỗi khi phát TTS: {error}")
        tts_playing[guild_id] = False
        playback_loop.call_soon_threadsafe(
            playback_loop.create_task,
            after_tts_playback(guild_id, voice_client, file_path, bot),
        )

    try:
        # Lấy âm lượng cho server, mặc định là 1.0 (100%)
        try:
            volume_level = float(tts_volume.get(str(guild_id), 1.0))
            if volume_level <= 0:
                volume_level = 1.0
        except Exception:
            volume_level = 1.0

        ffmpeg_exe = get_ffmpeg_executable()
        raw_source = discord.FFmpegPCMAudio(
            file_path,
            executable=ffmpeg_exe,
            options="-vn -loglevel error"
        )
        if volume_level != 1.0:
            source = discord.PCMVolumeTransformer(raw_source, volume=volume_level)
        else:
            source = raw_source

        # Kiểm tra trạng thái DAVE E2EE (nếu kênh đang đàm phán mã hóa)
        conn_state = getattr(voice_client, "_connection", None)
        if conn_state and getattr(conn_state, "dave_protocol_version", 0) > 0 and not getattr(conn_state, "can_encrypt", False):
            for _ in range(25):
                if getattr(conn_state, "can_encrypt", False):
                    break
                await asyncio.sleep(0.1)

        print(f"[TTS Audio] 🎵 Phát: {file_path} (size={os.path.getsize(file_path)}B, vol={volume_level}, dave_ver={getattr(conn_state, 'dave_protocol_version', 0)}, can_encrypt={getattr(conn_state, 'can_encrypt', None)})")
        voice_client.play(source, after=after_playing)
    except Exception as e:
        print(f"Lỗi khi gọi voice_client.play TTS: {e}")
        tts_playing[guild_id] = False
        try:
            if os.path.exists(file_path):
                os.remove(file_path)
        except Exception:
            pass

        text_ch_id = voice_text_channels.get(guild_id)
        if text_ch_id and bot:
            ch = bot.get_channel(text_ch_id)
            if ch:
                asyncio.create_task(ch.send(f"⚠️ **Lỗi phát âm thanh TTS**: `{e}`. Kiểm tra xem bot có bị Mute hoặc thiếu quyền không.", delete_after=15))

        await play_next_tts(guild_id, voice_client, bot)

async def after_tts_playback(guild_id: int, voice_client: discord.VoiceClient, file_path: str, bot):
    """
    Dọn dẹp file mp3 và gọi hàm phát bài tiếp theo.
    """
    await asyncio.sleep(0.3)
    try:
        if os.path.exists(file_path):
            os.remove(file_path)
    except Exception as e:
        print(f"Lỗi khi xóa file TTS {file_path}: {e}")

    await play_next_tts(guild_id, voice_client, bot)

async def play_announcement(guild: discord.Guild, text: str, bot):
    """
    Tạo và phát một thông báo TTS ngay lập tức.
    Hàm này sẽ ưu tiên phát nó trước hàng đợi.
    """
    voice_client = guild.voice_client
    if not voice_client:
        return

    try:
        tts_object = await get_gtts_object(text, guild.id, bot.user.id)
        if not tts_object:
            return

        if not os.path.exists("tts_audio"):
            os.makedirs("tts_audio", exist_ok=True)
        file_path = f"tts_audio/announcement_{guild.id}_{int(time.time())}.mp3"

        loop = asyncio.get_running_loop()
        await loop.run_in_executor(None, tts_object.save, file_path)

        if not os.path.exists(file_path) or os.path.getsize(file_path) < 100:
            return

        if guild.id not in tts_queue:
            tts_queue[guild.id] = deque()
        tts_queue[guild.id].appendleft({"file": file_path})

        if hasattr(voice_client, "is_playing") and not voice_client.is_playing():
            tts_playing[guild.id] = False

        if not tts_playing.get(guild.id, False):
            await play_next_tts(guild.id, voice_client, bot)
    except Exception as e:
        print(f"[TTS Announcement Error]: {e}")


def process_tts_text(message: discord.Message) -> str:
    """
    Xử lý và làm sạch văn bản từ tin nhắn để chuẩn bị cho TTS.
    """
    text = message.content

    # 0. Xử lý link TRƯỚC TIÊN (để tránh emoticon như :/ làm hỏng cấu trúc https://)
    # Markdown link: [Tiêu đề](https://...) -> Tiêu đề link
    text = re.sub(r'\[([^\]]+)\]\((?:https?://|www\.)\S+\)', r' \1 link ', text)
    # Link bọc < > trong Discord: <https://...> -> link
    text = re.sub(r'<(?:https?://|www\.)\S+>', ' link ', text)
    # Link chuẩn: https://, http://, www. -> link
    text = re.sub(r'(?:https?://|www\.)\S+', ' link ', text)

    # Bản đồ emoticon sang cách đọc
    emoticon_map = {
        ":)": " mặt cười ",
        ":(": " mặt buồn ",
        ":D": " cười lớn ",
        ":v": " mặt pacman ",
        ":p": " lêu lêu ",
        ":3": " mặt mèo ",
        "<3": " trái tim ",
        ":o": " ngạc nhiên ",
        ":'(": " khóc ",
        ":/": " phân vân ",
        ">.<": " ngại ngùng ",
        "T_T": " khóc ròng ",
        "-_-": " bất lực ",
        "O_O": " ngơ ngác ",
        ":))": " cười nghiêng ngả ",
        ":)))": " rất buồn cười ",
        ":((( ": " rất buồn ",
        ":<": " mặt xịu ",
        ":>": " mặt cười đểu ",
        "=))": " cười lăn lộn ",
        ":-(": " mặt buồn ",
        ":-)": " mặt cười ",
        ":-D": " cười lớn ",
        ":-P": " lêu lêu ",
        ":-O": " ngạc nhiên ",
        ":'‑(": " khóc ",
        ":'‑)": " cười ra nước mắt ",
        ":|": " mặt đơ ",
        ":-|": " mặt đơ ",
        ":$": " ngại ngùng ",
        ":-$": " ngại ngùng ",
        ":*": " thơm một cái ",
        ":-*": " thơm một cái ",
        ":@": " tức giận ",
        ":-@": " tức giận ",
        "B-)": " ngầu lòi ",
        "8-)": " ngầu lòi ",
        ":>": " mặt cười nham hiểm ",
        ":<": " mặt phụng phịu ",
        ":((": " mặt mếu ",
        ";))": " mặt nháy mắt ",
        ";)": " mặt nháy mắt ",
        "^^": " tôi cảm thấy rất vui ",
        ":3": " meow meow ",
        "uwu": " mặt cute ",
        "owo": " mặt cute ",
        "t-t": " hu hu hu ",
    }
    for emoticon, reading in emoticon_map.items():
        text = text.replace(emoticon, reading)

    # 7. Xử lý emoji tùy chỉnh
    def format_custom_emoji(match: re.Match) -> str:
        emoji_id = match.group(2)
        emoji_name = match.group(1)
        guild_id_str = str(message.guild.id)

        # Ưu tiên đọc theo cài đặt của server
        server_readings = tts_emoji_readings.get(guild_id_str, {})
        if emoji_id in server_readings:
            return f" {server_readings[emoji_id]} "
        
        # Nếu không có, đọc theo tên mặc định
        return f" emoji {emoji_name.replace('_', ' ')} "
    text = re.sub(r"<a?:([a-zA-Z0-9_]+):(\d+)>", format_custom_emoji, text)

    # 1.5. Xử lý emoji Unicode (emoji mặc định của Discord) - SAU KHI XỬ LÝ CUSTOM EMOJI
    text = emoji.demojize(text, language='alias') # Chuyển 😊 thành :smiling_face:
    text = re.sub(r':([a-zA-Z0-9_]+):', r' \1 ', text) # Chuyển :smiling_face: thành smiling_face

    # 2. Xử lý mention người dùng
    for member in message.mentions:
        text = text.replace(f"<@{member.id}>", f"tag {member.display_name}")
        text = text.replace(f"<@!{member.id}>", f"tag {member.display_name}")

    # 2.1. Xử lý mention Role (Vai trò: <@&role_id>)
    if hasattr(message, "role_mentions"):
        for role in message.role_mentions:
            text = text.replace(f"<@&{role.id}>", f"tag role {role.name}")

    # Dự phòng cho Role nếu không nằm trong cache/message.role_mentions
    def format_role_fallback(match: re.Match) -> str:
        role_id = int(match.group(1))
        if message.guild:
            role = message.guild.get_role(role_id)
            if role:
                return f"tag role {role.name}"
        return "tag role"
    text = re.sub(r"<@&(\d+)>", format_role_fallback, text)

    # 2.2. Xử lý tag Game mới của Discord (<@game Tên Game>)
    text = re.sub(r"<@game:?\s*([^>]+)>", r" tag game \1 ", text, flags=re.IGNORECASE)

    # 2.3. Xử lý mention chung (@everyone / @here)
    text = text.replace("@everyone", "tag mọi người").replace("@here", "tag ở đây")
    # 3. Xử lý kênh
    for channel in message.channel_mentions:
        text = text.replace(f"<#{channel.id}>", f"kênh {channel.name}")

    # 5. Xử lý sticker
    if message.stickers:
        for sticker in message.stickers:
            sticker_name = sticker.name.replace("_", " ").replace("-", " ")
            text += f" sticker {sticker_name}"

    # 6. Xử lý file đính kèm
    if message.attachments:
        img_count = sum(1 for f in message.attachments if f.content_type and f.content_type.startswith('image/'))
        vid_count = sum(1 for f in message.attachments if f.content_type and f.content_type.startswith('video/'))
        if img_count > 0: text += f" đã gửi {img_count} hình ảnh "
        if vid_count > 0: text += f" đã gửi {vid_count} video "

    # 8. Xử lý code block (thay thế nội dung trong `...` và ```...```)
    text = re.sub(r"`{1,3}.*?`{1,3}", " code text ", text, flags=re.DOTALL)

    # 9. Xử lý các ký tự markdown còn lại
    text = re.sub(r"[*_~>#|]", " ", text)

    # 10. Xử lý từ lóng và viết tắt
    slang_map = {
        "ko": "không", "k": "không", "kh": "không", "hok": "không",
        "dc": "được", "đc": "được", "vs": "với", "cx": "cũng",
        "mik": "mình", "mk": "mình", "ny": "người yêu", "nyc": "người yêu cũ",
        "ck": "chồng", "vk": "vợ", "bt": "biết", "r": "rồi",
        "j": "gì", "z": "vậy", "zay": "vậy", "lun": "luôn", "iu": "yêu",
        "vl": "vãi", "vcl": "vi ci eo", "wtf": "oát dơ heo",
        "lol": "cười lớn", "lmao": "cười lớn", "ib": "nhắn tin", "rep": "trả lời",
        "t": "tao", "m": "mày", "dm": "đờ mờ", "dcm": "đờ cờ mờ",
        "kkk": "cười", "haha": "ha ha", "huhu": "hu hu",
        "cặk": " ", "lồn": " ", "buồi": " ", "cặc": " ",
    }
    words = [slang_map.get(word.lower(), word) for word in text.split()]
    text = " ".join(words)

    return text.strip()


async def add_to_tts_queue(message: discord.Message, bot):
    """
    Hàm chính để xử lý một tin nhắn, chuyển nó thành giọng nói và thêm vào hàng đợi.
    """
    guild = message.guild
    author = message.author
    voice_client = guild.voice_client

    # --- CÁC ĐIỀU KIỆN CẦN THIẾT ---
    # Chỉ cần bot đang ở trong voice là được, không cần kiểm tra người dùng
    if not voice_client or not getattr(voice_client, "is_connected", lambda: False)():
        return

    # Lấy kênh chat được phép (nếu chưa set thì tự động gán kênh hiện tại hoặc cho phép text chat của voice channel)
    allowed_channel_id = voice_text_channels.get(guild.id)
    is_voice_text_chat = (hasattr(voice_client, "channel") and voice_client.channel and message.channel.id == voice_client.channel.id)
    if not allowed_channel_id and not is_voice_text_chat:
        voice_text_channels[guild.id] = message.channel.id
        allowed_channel_id = message.channel.id

    if allowed_channel_id and message.channel.id != allowed_channel_id and not is_voice_text_chat:
        return

    # --- KIỂM TRA GIỚI HẠN SỐ LƯỢNG EMOJI ---
    guild_id_str = str(guild.id)
    emoji_count_limit = tts_emoji_count_limit.get(guild_id_str, 10) # Mặc định 10 emoji
    if emoji_count_limit > 0:
        custom_emojis_found = re.findall(r"<a?:\w+:\d+>", message.content)
        if len(custom_emojis_found) > emoji_count_limit:
            await message.channel.send(
                f"⚠️ {message.author.mention}, tin nhắn của bạn chứa quá nhiều emoji (vượt quá **{emoji_count_limit}** emoji) và đã bị bỏ qua.", delete_after=10
            )
            return
    # --- XỬ LÝ NỘI DUNG ---
    # Thêm tên người nói nếu là người mới hoặc đã im lặng một lúc
    prefix_text = ""
    say_name = True
    last_user_info = last_tts_user.get(guild.id)
    current_time = time.time()

    if last_user_info:
        # Nếu là cùng một người và chưa quá 30 giây thì không cần đọc lại tên
        if last_user_info.get("id") == author.id and (current_time - last_user_info.get("time", 0)) < 30:
            say_name = False

    if say_name:
        # Lấy tên đọc tùy chỉnh theo server
        user_display_name = tts_names.get(str(guild.id), {}).get(str(author.id), author.display_name)
        prefix_text = f"{user_display_name} nói, "
    last_tts_user[guild.id] = {"id": author.id, "time": current_time}

    # Làm sạch nội dung tin nhắn
    processed_content = process_tts_text(message)

    # Áp dụng giới hạn ký tự
    char_limit = tts_char_limit.get(str(guild.id), 300) # Mặc định 300
    if char_limit > 0 and len(message.content) > char_limit:
        # Gửi một tin nhắn cảnh báo nhẹ nhàng
        await message.channel.send(f"⚠️ {message.author.mention}, tin nhắn của bạn quá dài (vượt quá **{char_limit}** ký tự) và đã bị bỏ qua.", delete_after=10)
        # Bỏ qua hoàn toàn, không đọc tin nhắn này
        return

    # Kết hợp tiền tố và nội dung
    final_text = prefix_text + processed_content

    # Bỏ qua nếu không có nội dung để nói
    if not final_text.strip():
        return

    # --- TẠO FILE ÂM THANH VÀ THÊM VÀO HÀNG ĐỢI ---
    try:
        if not os.path.exists("tts_audio"):
            os.makedirs("tts_audio", exist_ok=True)

        tts_object = await get_gtts_object(final_text, guild.id, author.id)
        if not tts_object:
            return

        file_path = f"tts_audio/tts_{message.id}.mp3"
        loop = asyncio.get_running_loop()
        await loop.run_in_executor(None, tts_object.save, file_path)

        if not os.path.exists(file_path) or os.path.getsize(file_path) < 100:
            return

        # Thêm vào hàng đợi của server
        if guild.id not in tts_queue:
            tts_queue[guild.id] = deque()
        tts_queue[guild.id].append({"file": file_path})

        # Đồng bộ trạng thái: nếu voice_client không thực sự phát, giải phóng cờ tts_playing
        if hasattr(voice_client, "is_playing") and not voice_client.is_playing():
            tts_playing[guild.id] = False

        # Nếu bot không đang phát, bắt đầu phát
        if not tts_playing.get(guild.id, False):
            await play_next_tts(guild.id, voice_client, bot)

    except Exception as e:
        print(f"[TTS Generation Error]: {e}")

