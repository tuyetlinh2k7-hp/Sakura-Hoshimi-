import re
import json
import os
import logging
import discord
from discord import app_commands
from discord.ext import commands
from typing import Literal
from Checks_vi.i18n import t

logger = logging.getLogger(__name__)
CONFIG_FILE = "data/autoreact_config.json"

class AutoReactCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        
        # Biên dịch sẵn Regex bắt từ khóa
        self.keyword_pattern = re.compile(r'(@everyone|@here|@{2,})', re.IGNORECASE)
        
        # Cooldown chống spam: Tối đa 1 lần kích hoạt mỗi 10 giây cho mỗi thành viên (BucketType.user)
        self.cooldown = commands.CooldownMapping.from_cooldown(1, 10.0, commands.BucketType.user)
        
        # Tải cấu hình từ file JSON
        self.config = self._load_config()

    # ==========================================
    # QUẢN LÝ DỮ LIỆU CẤU HÌNH (JSON)
    # ==========================================
    def _load_config(self) -> dict:
        default_config = {
            "global": {
                "enabled": True,
                "mention_emojis": ["👀", "🔥"],
                "forum_emojis": ["👍", "❤️"]
            },
            "guilds": {}
        }
        if os.path.exists(CONFIG_FILE):
            try:
                with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    # Đảm bảo đủ key mặc định
                    default_config.update(data)
                    return default_config
            except Exception as e:
                logger.error(f"Lỗi đọc file cấu hình {CONFIG_FILE}: {e}")
        return default_config

    def _save_config(self):
        try:
            with open(CONFIG_FILE, "w", encoding="utf-8") as f:
                json.dump(self.config, f, ensure_ascii=False, indent=4)
        except Exception as e:
            logger.error(f"Lỗi lưu file cấu hình {CONFIG_FILE}: {e}")

    def _get_guild_settings(self, guild_id: int) -> tuple[bool, list[str], list[str]]:
        """Lấy cấu hình hiệu lực của Server (Ưu tiên cài đặt riêng của Server, nếu không có sẽ lấy Global)."""
        g_id = str(guild_id)
        guild_cfg = self.config["guilds"].get(g_id, {})
        global_cfg = self.config["global"]

        # Nếu Global tắt thì tắt toàn bộ. Nếu Global bật thì xét xem Server có tắt riêng không.
        is_enabled = global_cfg.get("enabled", True) and guild_cfg.get("enabled", True)
        
        mention_emojis = guild_cfg.get("mention_emojis") or global_cfg.get("mention_emojis", ["👀", "🔥"])
        forum_emojis = guild_cfg.get("forum_emojis") or global_cfg.get("forum_emojis", ["👍", "❤️"])
        
        return is_enabled, mention_emojis, forum_emojis

    # ==========================================
    # HÀM XỬ LÝ SỰ KIỆN (LISTENERS)
    # ==========================================
    async def _safe_add_reactions(self, message: discord.Message | discord.PartialMessage, emojis: list[str]):
        for emoji in emojis:
            try:
                await message.add_reaction(emoji.strip())
            except discord.Forbidden:
                logger.warning(f"Thiếu quyền thả reaction tại kênh {message.channel.id}")
                break
            except discord.NotFound:
                break
            except discord.HTTPException as e:
                logger.error(f"Emoji không hợp lệ hoặc lỗi mạng ({emoji}): {e}")

    @commands.Cog.listener()
    async def on_thread_create(self, thread: discord.Thread):
        if not thread.guild or not isinstance(thread.parent, discord.ForumChannel):
            return

        enabled, _, forum_emojis = self._get_guild_settings(thread.guild.id)
        if not enabled:
            return

        try:
            await thread.join()
            starter_msg = thread.get_partial_message(thread.id)
            await self._safe_add_reactions(starter_msg, forum_emojis)
        except discord.HTTPException as e:
            logger.error(f"Lỗi xử lý bài viết Forum {thread.id}: {e}")

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if message.author.bot or not message.guild:
            return

        # Tránh thả emoji trùng lặp cho tin nhắn mở đầu của bài viết Forum (vì on_thread_create đã xử lý)
        if isinstance(message.channel, discord.Thread) and message.id == message.channel.id:
            return

        enabled, mention_emojis, _ = self._get_guild_settings(message.guild.id)
        if not enabled:
            return

        if message.mention_everyone or self.keyword_pattern.search(message.content):
            # Kiểm tra Cooldown chống spam
            bucket = self.cooldown.get_bucket(message)
            retry_after = bucket.update_rate_limit()
            if retry_after:
                # Đang trong thời gian hồi (cooldown), bỏ qua không thả emoji
                return

            await self._safe_add_reactions(message, mention_emojis)

    # ==========================================
    # HỆ THỐNG LỆNH SLASH COMMAND (/autoreact)
    # ==========================================
    autoreact_group = app_commands.Group(
        name="autoreact", 
        description="Quản lý tính năng tự động thả emoji",
        default_permissions=discord.Permissions(manage_guild=True) # Mặc định chỉ người có quyền Quản lý Server mới thấy lệnh
    )

    @autoreact_group.command(name="toggle", description="Bật hoặc tắt tự động thả emoji")
    @app_commands.describe(
        scope="Phạm vi áp dụng: Server hiện tại hoặc Toàn cục (Chỉ Owner Bot)",
        state="Trạng thái Bật (True) hoặc Tắt (False)"
    )
    async def toggle_cmd(self, interaction: discord.Interaction, scope: Literal["server", "global"], state: bool):
        status_text = "🟢 ĐÃ BẬT" if state else "🔴 ĐÃ TẮT"

        if scope == "global":
            if not await self.bot.is_owner(interaction.user):
                return await interaction.response.send_message(t(interaction.guild, "AUTOREACT_OWNER_ONLY"), ephemeral=True)
            
            self.config["global"]["enabled"] = state
            self._save_config()
            await interaction.response.send_message(f"**[Global]** {status_text} tính năng tự động thả emoji trên toàn bộ hệ thống.", ephemeral=True)
        
        else:
            g_id = str(interaction.guild_id)
            if g_id not in self.config["guilds"]:
                self.config["guilds"][g_id] = {}
            
            self.config["guilds"][g_id]["enabled"] = state
            self._save_config()
            await interaction.response.send_message(t(interaction.guild, "AUTOREACT_TOGGLED_SERVER", state=status_text), ephemeral=True)

    @autoreact_group.command(name="set_emojis", description="Thiết lập danh sách emoji tự động thả")
    @app_commands.describe(
        scope="Phạm vi: Server hiện tại hoặc Global (Chỉ Owner Bot)",
        target="Loại sự kiện: Khi nhắc từ khóa (mention) hoặc Bài đăng Forum mới (forum)",
        emojis="Nhập các emoji cách nhau bằng khoảng trắng (VD: 👀 🔥 <:pepe:123456>). Gõ 'reset' để về mặc định."
    )
    async def set_emojis_cmd(
        self, 
        interaction: discord.Interaction, 
        scope: Literal["server", "global"], 
        target: Literal["mention", "forum"], 
        emojis: str
    ):
        key_name = "mention_emojis" if target == "mention" else "forum_emojis"
        target_label = t(interaction.guild, "AUTOREACT_LABEL_MENTION") if target == "mention" else t(interaction.guild, "AUTOREACT_LABEL_FORUM")

        # Tách chuỗi emoji người dùng nhập vào thành danh sách
        emoji_list = [e.strip() for e in emojis.split() if e.strip()]

        if scope == "global":
            if not await self.bot.is_owner(interaction.user):
                return await interaction.response.send_message(t(interaction.guild, "AUTOREACT_OWNER_ONLY"), ephemeral=True)
            
            if emojis.lower().strip() == "reset":
                emoji_list = ["👀", "🔥"] if target == "mention" else ["👍", "❤️"]
                
            self.config["global"][key_name] = emoji_list
            self._save_config()
            await interaction.response.send_message(
                f"✅ **[Global]** Đã cập nhật emoji cho **{target_label}**: {' '.join(emoji_list)}", 
                ephemeral=True
            )

        else:
            g_id = str(interaction.guild_id)
            if g_id not in self.config["guilds"]:
                self.config["guilds"][g_id] = {}

            # Nếu gõ 'reset', xóa cấu hình riêng của server để tự động dùng lại cấu hình Global
            if emojis.lower().strip() == "reset":
                self.config["guilds"][g_id].pop(key_name, None)
                self._save_config()
                return await interaction.response.send_message(
                    t(interaction.guild, "AUTOREACT_RESET_SERVER", label=target_label), 
                    ephemeral=True
                )

            self.config["guilds"][g_id][key_name] = emoji_list
            self._save_config()
            await interaction.response.send_message(
                t(interaction.guild, "AUTOREACT_UPDATED_SERVER", label=target_label, emojis=' '.join(emoji_list)), 
                ephemeral=True
            )

    @autoreact_group.command(name="status", description="Xem cấu hình thả emoji hiện tại của Server và Global")
    async def status_cmd(self, interaction: discord.Interaction):
        g_id = str(interaction.guild_id)
        guild_cfg = self.config["guilds"].get(g_id, {})
        global_cfg = self.config["global"]
        
        eff_enabled, eff_mention, eff_forum = self._get_guild_settings(interaction.guild_id)

        embed = discord.Embed(title=t(interaction.guild, "AUTOREACT_STATUS_TITLE"), color=discord.Color.blurple())
        
        # Thông tin Global
        g_state = "🟢 Bật" if global_cfg.get("enabled", True) else "🔴 Tắt"
        embed.add_field(
            name="🌐 Cấu hình Mặc định (Global)",
            value=(
                f"**Trạng thái:** {g_state}\n"
                f"**Mention Emojis:** {' '.join(global_cfg.get('mention_emojis', []))}\n"
                f"**Forum Emojis:** {' '.join(global_cfg.get('forum_emojis', []))}"
            ),
            inline=False
        )

        # Thông tin Server hiện tại
        s_state = "🟢 Đang hoạt động" if eff_enabled else "🔴 Đang tắt"
        is_custom_mention = "(Tùy chỉnh riêng)" if "mention_emojis" in guild_cfg else "(Theo Global)"
        is_custom_forum = "(Tùy chỉnh riêng)" if "forum_emojis" in guild_cfg else "(Theo Global)"
        
        embed.add_field(
            name=f"🏠 Đang áp dụng tại: {interaction.guild.name}",
            value=(
                f"**Trạng thái hiệu lực:** {s_state}\n"
                f"**Mention Emojis:** {' '.join(eff_mention)} `{is_custom_mention}`\n"
                f"**Forum Emojis:** {' '.join(eff_forum)} `{is_custom_forum}`"
            ),
            inline=False
        )
        
        await interaction.response.send_message(embed=embed, ephemeral=True)

async def setup(bot: commands.Bot):
    await bot.add_cog(AutoReactCog(bot))
