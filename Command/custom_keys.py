import os
import json
import uuid
import time
from pathlib import Path
from typing import Optional, Literal
import discord
from discord import app_commands
from discord.ext import commands

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
CUSTOM_KEYS_FILE = DATA_DIR / "custom_keys.json"
CUSTOM_KEYS_FILES_DIR = DATA_DIR / "custom_keys_files"


def load_all_custom_keys() -> dict:
    if not CUSTOM_KEYS_FILE.exists():
        return {}
    try:
        with open(CUSTOM_KEYS_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
            return data if isinstance(data, dict) else {}
    except Exception:
        return {}


def save_all_custom_keys(data: dict):
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    try:
        with open(CUSTOM_KEYS_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"[CustomKeys] Lỗi lưu custom_keys.json: {e}")


def get_guild_custom_keys(guild_id: int | str) -> list:
    all_data = load_all_custom_keys()
    g_data = all_data.get(str(guild_id), {})
    keys_dict = g_data.get("keys", {})
    return list(keys_dict.values())


def add_or_update_custom_key(guild_id: int | str, key_item: dict) -> dict:
    all_data = load_all_custom_keys()
    gid = str(guild_id)
    if gid not in all_data:
        all_data[gid] = {"keys": {}}

    key_id = key_item.get("id") or f"key_{uuid.uuid4().hex[:8]}"
    key_item["id"] = key_id
    key_item.setdefault("created_at", time.time())
    all_data[gid]["keys"][key_id] = key_item
    save_all_custom_keys(all_data)
    return key_item


def delete_guild_custom_key(guild_id: int | str, key_id: str) -> bool:
    all_data = load_all_custom_keys()
    gid = str(guild_id)
    if gid not in all_data or "keys" not in all_data[gid]:
        return False

    keys = all_data[gid]["keys"]
    # Check by id or by keyword
    target_id = None
    if key_id in keys:
        target_id = key_id
    else:
        for kid, kdata in keys.items():
            if kdata.get("keyword", "").lower() == key_id.lower():
                target_id = kid
                break

    if target_id and target_id in keys:
        item = keys.pop(target_id)
        # Delete attachment file if exists
        file_path = item.get("file_path")
        if file_path:
            p = Path(file_path)
            if not p.is_absolute():
                p = BASE_DIR / p
            if p.exists():
                try:
                    p.unlink()
                except Exception:
                    pass
        save_all_custom_keys(all_data)
        return True
    return False


class CustomKeys(commands.GroupCog, group_name="customkey"):
    """Quản lý các từ khóa tùy chỉnh (Custom Keys) và phản hồi tự động."""

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(name="add", description="Thêm hoặc cập nhật từ khóa phản hồi tự động")
    @app_commands.describe(
        keyword="Từ khóa mà bot sẽ lắng nghe trong tin nhắn",
        response="Nội dung phản hồi của bot khi gặp từ khóa",
        match_type="Khớp chính xác (exact) hoặc Tin nhắn chứa từ khóa (contains)",
        attachment="Tệp đính kèm (ảnh, file, zip...) gửi kèm phản hồi"
    )
    @app_commands.choices(match_type=[
        app_commands.Choice(name="Chính xác cả câu (Exact)", value="exact"),
        app_commands.Choice(name="Chứa từ khóa (Contains)", value="contains")
    ])
    @commands.has_permissions(manage_guild=True)
    async def add_key(
        self,
        interaction: discord.Interaction,
        keyword: str,
        response: str,
        match_type: Optional[app_commands.Choice[str]] = None,
        attachment: Optional[discord.Attachment] = None
    ):
        if not interaction.guild:
            return await interaction.response.send_message("❌ Lệnh này chỉ dùng trong server.", ephemeral=True)

        m_type = match_type.value if match_type else "exact"
        file_info = None

        if attachment:
            # Check server max upload limit (default 10MB safe check)
            if attachment.size > 25 * 1024 * 1024:
                return await interaction.response.send_message("❌ Kích thước tệp vượt quá 25MB!", ephemeral=True)

            g_dir = CUSTOM_KEYS_FILES_DIR / str(interaction.guild_id)
            g_dir.mkdir(parents=True, exist_ok=True)
            saved_filename = f"{int(time.time())}_{attachment.filename}"
            save_path = g_dir / saved_filename
            await attachment.save(save_path)
            file_info = {
                "file_path": str(save_path.relative_to(BASE_DIR)),
                "file_name": attachment.filename,
                "file_size": attachment.size
            }

        key_item = {
            "keyword": keyword.strip(),
            "response": response.strip(),
            "match_type": m_type,
            "created_by": str(interaction.user.id),
            "created_at": time.time(),
            "enabled": True
        }
        if file_info:
            key_item.update(file_info)

        saved = add_or_update_custom_key(interaction.guild_id, key_item)
        embed = discord.Embed(
            title="✅ Đã Thêm Custom Key Thành Công!",
            color=discord.Color.green(),
            description=f"Bot sẽ tự động phản hồi khi gặp từ khóa: **`{saved['keyword']}`**"
        )
        embed.add_field(name="Kiểu khớp", value="Chính xác toàn bộ" if m_type == "exact" else "Chứa từ khóa", inline=True)
        embed.add_field(name="Phản hồi", value=response[:200] + ("..." if len(response) > 200 else ""), inline=False)
        if file_info:
            embed.add_field(name="Tệp đính kèm", value=f"📎 `{file_info['file_name']}` ({file_info['file_size'] // 1024} KB)", inline=False)
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="list", description="Xem danh sách các từ khóa phản hồi tự động")
    @commands.has_permissions(manage_guild=True)
    async def list_keys(self, interaction: discord.Interaction):
        if not interaction.guild:
            return await interaction.response.send_message("❌ Lệnh này chỉ dùng trong server.", ephemeral=True)

        keys = get_guild_custom_keys(interaction.guild_id)
        if not keys:
            return await interaction.response.send_message("ℹ️ Server này chưa cài đặt Custom Key nào. Dùng `/customkey add` hoặc cấu hình trên Web Dashboard!", ephemeral=True)

        embed = discord.Embed(
            title=f"🔑 Danh Sách Custom Keys — {interaction.guild.name}",
            color=discord.Color.blurple(),
            description=f"Tổng cộng: **{len(keys)}** từ khóa đã được cấu hình."
        )
        for i, k in enumerate(keys[:20], 1):
            file_note = f" 📎 `{k.get('file_name')}`" if k.get("file_name") else ""
            embed.add_field(
                name=f"{i}. `{k.get('keyword')}` ({k.get('match_type', 'exact')})",
                value=f"**Trả lời**: {k.get('response', '')[:80]}{file_note}",
                inline=False
            )
        if len(keys) > 20:
            embed.set_footer(text=f"Còn {len(keys) - 20} key khác. Xem đầy đủ trên Web Dashboard!")
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="delete", description="Xóa một từ khóa phản hồi tự động")
    @app_commands.describe(keyword="Từ khóa cần xóa")
    @commands.has_permissions(manage_guild=True)
    async def delete_key(self, interaction: discord.Interaction, keyword: str):
        if not interaction.guild:
            return await interaction.response.send_message("❌ Lệnh này chỉ dùng trong server.", ephemeral=True)

        ok = delete_guild_custom_key(interaction.guild_id, keyword.strip())
        if ok:
            await interaction.response.send_message(f"🗑️ Đã xóa thành công từ khóa **`{keyword}`**.")
        else:
            await interaction.response.send_message(f"❌ Không tìm thấy từ khóa **`{keyword}`** trong server này.", ephemeral=True)

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if message.author.bot or not message.guild:
            return

        # Bỏ qua nếu tin nhắn là lệnh bot prefix
        content = message.content.strip()
        if not content:
            return

        keys = get_guild_custom_keys(message.guild.id)
        if not keys:
            return

        content_lower = content.lower()
        for k in keys:
            if not k.get("enabled", True):
                continue
            kw = k.get("keyword", "").strip().lower()
            if not kw:
                continue

            match_type = k.get("match_type", "exact")
            matched = False
            if match_type == "exact":
                matched = (content_lower == kw)
            else:
                matched = (kw in content_lower)

            if matched:
                response_text = k.get("response", "")
                file_to_send = None
                file_rel = k.get("file_path")
                if file_rel:
                    p = Path(file_rel)
                    if not p.is_absolute():
                        p = BASE_DIR / p
                    if p.exists():
                        file_to_send = discord.File(str(p), filename=k.get("file_name", p.name))

                try:
                    if file_to_send:
                        await message.channel.send(content=response_text or None, file=file_to_send)
                    elif response_text:
                        await message.channel.send(content=response_text)
                except Exception as e:
                    print(f"[CustomKeys] Lỗi gửi phản hồi {kw}: {e}")
                break


async def setup(bot: commands.Bot):
    await bot.add_cog(CustomKeys(bot))
