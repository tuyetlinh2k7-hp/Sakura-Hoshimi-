import discord
import genshin
from datetime import datetime


def _format_remaining(end_time: datetime | None) -> str:
    """Định dạng thời gian còn lại sang tiếng Việt dễ đọc, tránh hiển thị số âm."""
    if not end_time:
        return "Không xác định"

    now = datetime.now(end_time.tzinfo)
    delta = end_time - now
    total_seconds = int(delta.total_seconds())

    if total_seconds <= 0:
        return "Đã kết thúc"

    days, remainder = divmod(total_seconds, 86400)
    hours, remainder = divmod(remainder, 3600)
    minutes, _ = divmod(remainder, 60)

    parts = []
    if days > 0:
        parts.append(f"{days} ngày")
    if hours > 0:
        parts.append(f"{hours} giờ")
    if minutes > 0 or not parts:
        parts.append(f"{minutes} phút")

    return " ".join(parts)


async def get_gi_abyss_embed(client: genshin.Client, uid: int) -> discord.Embed:
    """Lấy và tạo Embed cho La Hoàn Uyên Cảnh (Genshin Impact)."""
    abyss = await client.get_spiral_abyss(uid, previous=False)

    embed = discord.Embed(
        title=f"🌀 La Hoàn Uyên Cảnh - Kỳ {abyss.season}",
        description=f"⏳ Kết thúc trong: `{_format_remaining(abyss.end_time)}`",
        color=discord.Color.dark_blue()
    )
    embed.add_field(name="⭐ Tổng sao", value=f"**{abyss.total_stars}** / 36", inline=True)
    embed.add_field(name="⚔️ Số trận", value=f"`{abyss.total_battles}`", inline=True)
    embed.add_field(name="🏔️ Tầng cao nhất", value=f"`{abyss.max_floor}`", inline=True)

    if abyss.strongest_team:
        strongest_team = " | ".join([f"**{c.name}** (Lv.{c.level})" for c in abyss.strongest_team])
        embed.add_field(name="💪 Đội hình mạnh nhất", value=strongest_team, inline=False)

    rank_lines = []
    if abyss.ranks:
        if abyss.ranks.most_played:
            most_played = " | ".join([f"**{c.name}** ({c.value} lần)" for c in abyss.ranks.most_played[:4]])
            rank_lines.append(f"**Dùng nhiều nhất:** {most_played}")
        if abyss.ranks.most_kills:
            mk = abyss.ranks.most_kills[0]
            rank_lines.append(f"**Hạ gục nhiều nhất:** **{mk.name}** ({mk.value} mạng)")
        if abyss.ranks.strongest_strike:
            ss = abyss.ranks.strongest_strike[0]
            rank_lines.append(f"**Đòn đánh mạnh nhất:** **{ss.name}** ({ss.value:,} sát thương)")

    if rank_lines:
        embed.add_field(
            name="🏆 Nhân vật nổi bật",
            value="\n".join(rank_lines),
            inline=False
        )
    return embed


async def get_gi_banners_embed(client: genshin.Client) -> discord.Embed:
    """Lấy và tạo Embed cho các banner Genshin Impact."""
    banners = await client.get_genshin_banners()
    embed = discord.Embed(title="✨ Banner Cầu Nguyện Hiện Tại (Genshin Impact)", color=discord.Color.purple())

    for banner in banners:
        rateup_chars = ", ".join(f"**{char.name}**" for char in banner.rateup_characters)
        rateup_weapons = ", ".join(f"**{weapon.name}**" for weapon in banner.rateup_weapons)

        value = ""
        if rateup_chars:
            value += f"**Nhân vật:** {rateup_chars}\n"
        if rateup_weapons:
            value += f"**Vũ khí:** {rateup_weapons}\n"
        value += f"*⏳ Kết thúc sau: `{_format_remaining(banner.end_time)}`*"

        name = f"**{banner.banner_type_name}**"
        if banner.rateup_characters:
            name += f" - {banner.rateup_characters[0].name}"
        elif banner.rateup_weapons:
            name += f" - {banner.rateup_weapons[0].name}"

        embed.add_field(name=name, value=value, inline=False)
    return embed


async def get_gi_events_embed(client: genshin.Client) -> discord.Embed:
    """Lấy và tạo Embed cho các sự kiện Genshin Impact."""
    events = await client.get_genshin_events()
    embed = discord.Embed(
        title="🎉 Sự Kiện In-game Hiện Tại (Genshin Impact)",
        color=discord.Color.from_rgb(255, 215, 0)
    )
    lines = [
        f"### {event.title}\n*Thời gian: `{event.start_time.strftime('%d/%m')} - {event.end_time.strftime('%d/%m')}`*"
        for event in events[:15]
    ]
    embed.description = "\n\n".join(lines)[:4000] if lines else "Hiện không có sự kiện nào đang diễn ra."
    return embed


async def get_hsr_moc_embed(client: genshin.Client, uid: int) -> discord.Embed:
    """Lấy và tạo Embed cho Hư Ảnh Ký Ức (Honkai: Star Rail)."""
    moc = await client.get_memory_of_chaos(uid)
    embed = discord.Embed(
        title=f"🌌 Hư Ảnh Ký Ức - Mùa {moc.season}",
        description=f"⏳ Kết thúc trong: `{_format_remaining(moc.end_time)}`",
        color=discord.Color.from_rgb(138, 43, 226)
    )
    embed.add_field(name="⭐ Tổng sao", value=f"**{moc.total_stars}** / 36", inline=True)
    embed.add_field(name="⚔️ Số trận", value=f"`{moc.total_battles}`", inline=True)
    embed.add_field(name="🏔️ Tầng cao nhất", value=f"`{moc.max_floor}`", inline=True)

    rank_lines = []
    if moc.ranks:
        if moc.ranks.most_used:
            most_used = " | ".join([f"**{c.name}** ({c.value} lần)" for c in moc.ranks.most_used[:4]])
            rank_lines.append(f"**Dùng nhiều nhất:** {most_used}")
        if moc.ranks.most_cycles:
            mc = moc.ranks.most_cycles[0]
            rank_lines.append(f"**Ít chu kỳ nhất:** **{mc.name}** ({mc.value} chu kỳ)")

    if rank_lines:
        embed.add_field(
            name="🏆 Nhân vật nổi bật",
            value="\n".join(rank_lines),
            inline=False
        )
    return embed


async def get_hsr_pf_embed(client: genshin.Client, uid: int) -> discord.Embed:
    """Lấy và tạo Embed cho Hư Cấu Thuần Túy (Honkai: Star Rail)."""
    pf = await client.get_pure_fiction(uid)
    embed = discord.Embed(
        title=f"🎭 Hư Cấu Thuần Túy - Kỳ {pf.season}",
        description=f"⏳ Kết thúc trong: `{_format_remaining(pf.end_time)}`",
        color=discord.Color.from_rgb(220, 20, 60)
    )
    embed.add_field(name="⭐ Tổng sao", value=f"**{pf.total_stars}** / 12", inline=True)
    embed.add_field(name="⚔️ Số trận", value=f"`{pf.total_battles}`", inline=True)
    embed.add_field(name="🏔️ Tầng cao nhất", value=f"`{pf.max_floor}`", inline=True)

    if pf.ranks and pf.ranks.most_used:
        most_used = " | ".join([f"**{c.name}** ({c.value} lần)" for c in pf.ranks.most_used[:4]])
        embed.add_field(name="🏆 Nhân vật dùng nhiều nhất", value=most_used, inline=False)
    return embed


async def get_hsr_banners_embed(client: genshin.Client) -> discord.Embed:
    """Lấy và tạo Embed cho các banner Honkai: Star Rail."""
    banners = await client.get_starrail_banners()
    embed = discord.Embed(
        title="🚀 Banner Bước Nhảy Hiện Tại (Honkai: Star Rail)",
        color=discord.Color.from_rgb(255, 165, 0)
    )

    for banner in banners:
        rateup_chars = ", ".join(f"**{char.name}**" for char in banner.rateup_characters)
        rateup_cones = ", ".join(f"**{cone.name}**" for cone in banner.rateup_light_cones)

        value = ""
        if rateup_chars:
            value += f"**Nhân vật:** {rateup_chars}\n"
        if rateup_cones:
            value += f"**Nón Ánh Sáng:** {rateup_cones}\n"
        value += f"*⏳ Kết thúc sau: `{_format_remaining(banner.end_time)}`*"

        name = f"**{banner.banner_type_name}**"
        if banner.rateup_characters:
            name += f" - {banner.rateup_characters[0].name}"
        elif banner.rateup_light_cones:
            name += f" - {banner.rateup_light_cones[0].name}"

        embed.add_field(name=name, value=value, inline=False)
    return embed


async def get_hsr_events_embed(client: genshin.Client) -> discord.Embed:
    """Lấy và tạo Embed cho các sự kiện Honkai: Star Rail."""
    events = await client.get_starrail_events()
    embed = discord.Embed(
        title="🎉 Sự Kiện In-game Hiện Tại (Honkai: Star Rail)",
        color=discord.Color.from_rgb(100, 149, 237)
    )
    lines = [
        f"### {event.title}\n*Thời gian: `{event.start_time.strftime('%d/%m')} - {event.end_time.strftime('%d/%m')}`*"
        for event in events[:15]
    ]
    embed.description = "\n\n".join(lines)[:4000] if lines else "Hiện không có sự kiện nào đang diễn ra."
    return embed
