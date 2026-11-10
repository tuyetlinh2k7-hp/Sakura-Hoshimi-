import time
import asyncio
import discord
from Check.data import voice_stats, save_data

# Quản lý thời gian cập nhật gần nhất của từng server để tránh bị Discord Rate Limit (2 lần / 10 phút)
_last_update_time: dict[str, float] = {}
_pending_tasks: dict[str, asyncio.Task] = {}
VOICE_EDIT_COOLDOWN = 600.0  # 10 phút (600 giây)


def get_stats(guild: discord.Guild) -> tuple[int, int, int]:
    all_members = guild.member_count or len(guild.members)
    bots = sum(1 for m in guild.members if m.bot)
    humans = max(0, all_members - bots)
    return all_members, humans, bots


async def _do_update_channels(guild: discord.Guild):
    guild_id = str(guild.id)
    if guild_id not in voice_stats:
        return

    config = voice_stats[guild_id]
    all_m, humans, bots = get_stats(guild)

    targets = [
        (guild.get_channel(config.get("all")), f"👥 Tất cả: {all_m}"),
        (guild.get_channel(config.get("members")), f"✨ Người dùng: {humans}"),
        (guild.get_channel(config.get("bots")), f"🤖 Bot/App: {bots}"),
    ]

    for ch, new_name in targets:
        # Chỉ gọi API edit nếu kênh tồn tại và tên hiện tại khác với tên mới
        if ch and ch.name != new_name:
            try:
                await ch.edit(name=new_name)
            except (discord.Forbidden, discord.HTTPException):
                pass

    _last_update_time[guild_id] = time.time()


async def update_stats(guild: discord.Guild):
    """Cập nhật tên kênh thống kê với cơ chế chống Rate Limit tự động."""
    guild_id = str(guild.id)
    if guild_id not in voice_stats:
        return

    now = time.time()
    last_time = _last_update_time.get(guild_id, 0.0)
    elapsed = now - last_time

    # Nếu đã qua 10 phút kể từ lần đổi tên trước -> Cập nhật ngay lập tức
    if elapsed >= VOICE_EDIT_COOLDOWN:
        await _do_update_channels(guild)
        return

    # Nếu đang trong thời gian hồi (dưới 10 phút), đặt lịch chạy tự động khi hết hồi chiêu
    if guild_id in _pending_tasks and not _pending_tasks[guild_id].done():
        return

    async def _delayed_update(delay: float):
        try:
            await asyncio.sleep(delay)
            await _do_update_channels(guild)
        except asyncio.CancelledError:
            pass
        finally:
            _pending_tasks.pop(guild_id, None)

    remaining_delay = VOICE_EDIT_COOLDOWN - elapsed
    _pending_tasks[guild_id] = asyncio.create_task(_delayed_update(remaining_delay))


def set_voice_channel(guild_id: int, all_id: int, members_id: int, bots_id: int):
    guild_id_str = str(guild_id)
    voice_stats[guild_id_str] = {
        "all": all_id,
        "members": members_id,
        "bots": bots_id
    }
    # Đã sửa lỗi: save_data() không nhận tham số
    save_data()
