import discord
import re
from discord import app_commands
from discord.ext import commands, tasks
from mcstatus import JavaServer
import base64
import traceback
import asyncio
import json
import os
import websockets
import io
import aiohttp  # Dùng để gọi API đến Pika Hosting công khai
from PIL import Image # Thư viện xử lý ảnh
from config import PKMC_API_KEY, OWNER_ID
from Check.minecraft import is_mc_admin, mc_admin_ids, save_mc_admins, mc_whitelist, save_mc_whitelist
from Check.i18n import t
from data.database import (
    get_mc_server,
    get_mc_server_by_guild,
    list_mc_servers,
    link_mc_server_to_guild,
    unlink_mc_server_from_guild,
    update_mc_server_channels,
    queue_mc_command,
    queue_mc_chat,
    link_mc_user,
    get_mc_user_link,
    sync_mc_user_coins,
    MC_COIN_RATE
)

# --- CẤU HÌNH SERVER MINECRAFT TRÊN PIKA HOSTING ---
MINECRAFT_HOST = "snow.pikamc.vn"
MINECRAFT_PORT = 25365
QUERY_PORT = 25355 # Port này phải được mở trên Pika và cấu hình trong server.properties

# Cấu hình RCON mặc định
RCON_HOST = "snow.pikamc.vn"
RCON_PORT = 25025
RCON_PASSWORD = "testserver123"

def get_guild_rcon_config(guild_id=None):
    """Lấy cấu hình RCON theo thứ tự: Guild config -> server.properties local -> fallback mặc định."""
    cfg_file = "data/guild_mc_connections.json"
    if guild_id and os.path.exists(cfg_file):
        try:
            with open(cfg_file, "r", encoding="utf-8") as f:
                data = json.load(f)
                gcfg = data.get(str(guild_id), {})
                rcon_p = gcfg.get("rcon_password")
                if rcon_p:
                    return {
                        "host": gcfg.get("rcon_host") or gcfg.get("host") or RCON_HOST,
                        "port": int(gcfg.get("rcon_port") or RCON_PORT),
                        "password": rcon_p
                    }
        except Exception:
            pass

    # Kiểm tra cấu hình server.properties của Minecraft server cục bộ nếu có
    sp_file = "server/server.properties"
    if os.path.exists(sp_file):
        try:
            with open(sp_file, "r", encoding="utf-8") as f:
                lines = f.readlines()
            sp_pass = ""
            sp_port = 25575
            sp_enabled = False
            for line in lines:
                line = line.strip()
                if line.startswith("enable-rcon="):
                    sp_enabled = line.split("=", 1)[1].strip().lower() == "true"
                elif line.startswith("rcon.password="):
                    sp_pass = line.split("=", 1)[1].strip()
                elif line.startswith("rcon.port="):
                    try:
                        sp_port = int(line.split("=", 1)[1].strip())
                    except Exception:
                        pass
            if sp_enabled and sp_pass:
                return {"host": "127.0.0.1", "port": sp_port, "password": sp_pass}
        except Exception:
            pass

    return {"host": RCON_HOST, "port": RCON_PORT, "password": RCON_PASSWORD}

def clean_minecraft_text_static(text: str) -> str:
    """Xóa bỏ mã màu Minecraft (§) và mã ANSI console."""
    if not text:
        return ""
    text = re.sub(r'§[0-9a-fk-orx]', '', str(text), flags=re.IGNORECASE)
    text = re.sub(r'\[[0-9;]*m', '', text)
    return text.strip()

def send_rcon_command_sync(command: str, host: str = None, port: int = None, password: str = None, guild_id=None) -> tuple[bool, str]:
    """Thực thi lệnh RCON đồng bộ và trả về (thành_công, phản_hồi)."""
    from mctools import RCONClient
    cfg = get_guild_rcon_config(guild_id)
    target_host = str(host or cfg.get("host") or RCON_HOST).strip()
    target_port = int(port or cfg.get("port") or RCON_PORT)
    target_pass = str(password or cfg.get("password") or RCON_PASSWORD).strip()

    clean_cmd = str(command).strip().lstrip("/")
    if not clean_cmd:
        return False, "Lệnh trống"

    if not target_pass:
        return False, "Chưa cài đặt mật khẩu RCON (hãy điền trong web hoặc server.properties)"

    try:
        rcon = RCONClient(target_host, port=target_port)
        if rcon.login(target_pass):
            resp = rcon.command(clean_cmd)
            rcon.stop()
            return True, clean_minecraft_text_static(resp)
        else:
            return False, "Sai mật khẩu RCON"
    except Exception as e:
        return False, f"Lỗi kết nối RCON ({e})"

async def send_rcon_command(command: str, host: str = None, port: int = None, password: str = None, guild_id=None) -> str:
    """Hàm bất đồng bộ xuất khẩu để web/server.py và bot gọi trực tiếp."""
    loop = asyncio.get_running_loop()
    ok, res = await loop.run_in_executor(None, send_rcon_command_sync, command, host, port, password, guild_id)
    return res if ok else f"Lỗi: {res}"

# Cấu hình Pterodactyl API (Pika Hosting)
PANEL_URL = "https://cp.pikamc.vn/"  
SERVER_ID = "749c34cf"               
PANEL_API_KEY = PKMC_API_KEY         

# --- CẤU HÌNH LOG MINECRAFT ---
MC_LOG_CONFIG_FILE = "data/minecraft_log_config.json"

def load_mc_log_config():
    if os.path.exists(MC_LOG_CONFIG_FILE):
        with open(MC_LOG_CONFIG_FILE, "r") as f:
            try: return json.load(f)
            except json.JSONDecodeError: return {}
    return {}

def save_mc_log_config(data):
    os.makedirs(os.path.dirname(MC_LOG_CONFIG_FILE), exist_ok=True)
    with open(MC_LOG_CONFIG_FILE, "w") as f:
        json.dump(data, f, indent=4)

# --- MÀU SẮC & HELPER EMBED MINECRAFT ---
MC_GREEN = discord.Color.from_rgb(83, 166, 73)    # Xanh lá cỏ cây Minecraft
MC_GOLD = discord.Color.from_rgb(250, 204, 21)     # Vàng gold / thành tựu / tiền tệ
MC_RED = discord.Color.from_rgb(239, 68, 68)       # Đỏ lỗi / ban / stop
MC_ORANGE = discord.Color.from_rgb(249, 115, 22)   # Cam cảnh báo / kick
MC_BLUE = discord.Color.from_rgb(59, 130, 246)     # Xanh dương info / channel / list
MC_DARK = discord.Color.from_rgb(31, 41, 55)       # Đen xám console / rcon
MC_GRASS_ICON = "https://minotar.net/cube/grass/32.png"

def make_mc_embed(
    title: str,
    description: str = "",
    color: discord.Color | int = MC_GREEN,
    player_name: str | None = None,
    fields: list[tuple[str, str, bool]] | None = None,
    footer: str = "Sakura Minecraft Network",
    thumbnail_url: str | None = None
) -> discord.Embed:
    embed = discord.Embed(title=title, description=description, color=color)
    if player_name:
        avatar_url = f"https://mc-heads.net/avatar/{player_name}/64"
        embed.set_author(name=f"Minecraft: {player_name}", icon_url=avatar_url)
        if not thumbnail_url:
            thumbnail_url = f"https://mc-heads.net/head/{player_name}/64"
    if thumbnail_url:
        embed.set_thumbnail(url=thumbnail_url)
    if fields:
        for f_name, f_val, f_inline in fields:
            embed.add_field(name=f_name, value=str(f_val), inline=f_inline)
    embed.set_footer(text=footer, icon_url=MC_GRASS_ICON)
    embed.timestamp = discord.utils.utcnow()
    return embed

class StatusView(discord.ui.View):
    def __init__(self, cog_instance, timeout=180):
        super().__init__(timeout=timeout)
        self.cog = cog_instance

    @discord.ui.button(label="Làm mới", style=discord.ButtonStyle.primary, emoji="🔄")
    async def refresh_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Nút làm mới trạng thái server."""
        await interaction.response.defer()
        embed, file = await self.cog.get_server_status_data()
        
        # Sửa lỗi gửi kèm file khi làm mới trong Ephemeral Message
        if file:
            await interaction.edit_original_response(embed=embed, view=self, attachments=[file])
        else:
            await interaction.edit_original_response(embed=embed, view=self, attachments=[])

    @discord.ui.button(label="Danh sách người chơi", style=discord.ButtonStyle.secondary, emoji="👥")
    async def list_players_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Nút hiển thị danh sách người chơi (Sửa lỗi crash Ephemeral Context)."""
        await interaction.response.defer(ephemeral=True)
        
        # Gọi trực tiếp logic xử lý RCON thay vì tạo fake_ctx bị lỗi
        response = await self.cog.execute_rcon_command("list")
        if "Lỗi" in response:
            embed = make_mc_embed(
                title="🔴 Lỗi Kết Nối RCON",
                description="Không thể lấy danh sách người chơi qua giao thức RCON.",
                color=MC_RED,
                fields=[("Chi tiết lỗi", f"```{response}```", False)]
            )
        else:
            embed = make_mc_embed(
                title="👥 Danh Sách Người Chơi Online",
                description=f"```{response}```",
                color=MC_BLUE
            )
            
        await interaction.followup.send(embed=embed, ephemeral=True)

class WhitelistPlayerModal(discord.ui.Modal, title="Quản lý Whitelist"):
    def __init__(self, cog_instance, action_type: str):
        super().__init__()
        self.cog = cog_instance
        self.action_type = action_type # "add" or "remove"

        self.player_name = discord.ui.TextInput(
            label="Tên người chơi Minecraft",
            placeholder="Nhập tên người chơi...",
            required=True,
            max_length=16
        )
        self.add_item(self.player_name)

    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True, thinking=True)
        player = self.player_name.value
        
        if self.action_type == "add":
            response = await self.cog._execute_whitelist_command("add", player)
            if "Lỗi" not in response:
                mc_whitelist.add(player.lower())
                save_mc_whitelist()
                embed = make_mc_embed(
                    title="✅ Thêm Whitelist Thành Công",
                    description=f"Đã thêm người chơi **`{player}`** vào danh sách cho phép (Whitelist)!",
                    color=MC_GREEN,
                    player_name=player,
                    fields=[("Phản hồi Server", f"```{response}```", False)]
                )
                await interaction.followup.send(embed=embed, ephemeral=True)
            else:
                embed = make_mc_embed(
                    title="❌ Thất Bại Khi Thêm Whitelist",
                    description=f"Không thể thêm người chơi **`{player}`** vào danh sách whitelist.",
                    color=MC_RED,
                    player_name=player,
                    fields=[("Chi tiết lỗi", f"```{response}```", False)]
                )
                await interaction.followup.send(embed=embed, ephemeral=True)
        elif self.action_type == "remove":
            response = await self.cog._execute_whitelist_command("remove", player)
            if "Lỗi" not in response:
                mc_whitelist.discard(player.lower())
                save_mc_whitelist()
                embed = make_mc_embed(
                    title="🗑️ Đã Xóa Khỏi Whitelist",
                    description=f"Đã gỡ người chơi **`{player}`** khỏi danh sách cho phép (Whitelist)!",
                    color=MC_ORANGE,
                    player_name=player,
                    fields=[("Phản hồi Server", f"```{response}```", False)]
                )
                await interaction.followup.send(embed=embed, ephemeral=True)
            else:
                embed = make_mc_embed(
                    title="❌ Thất Bại Khi Xóa Whitelist",
                    description=f"Không thể xóa người chơi **`{player}`** khỏi danh sách whitelist.",
                    color=MC_RED,
                    player_name=player,
                    fields=[("Chi tiết lỗi", f"```{response}```", False)]
                )
                await interaction.followup.send(embed=embed, ephemeral=True)

class BanKickPlayerModal(discord.ui.Modal):
    def __init__(self, cog_instance, action_type: str):
        super().__init__(title=f"{action_type.title()} Người chơi")
        self.cog = cog_instance
        self.action_type = action_type # "ban" or "kick"

        self.player_name = discord.ui.TextInput(
            label="Tên người chơi Minecraft",
            placeholder="Nhập tên người chơi...",
            required=True,
            max_length=16
        )
        self.add_item(self.player_name)

        self.reason = discord.ui.TextInput(
            label="Lý do (Tùy chọn)",
            placeholder="Lý do ban/kick...",
            required=False,
            max_length=100
        )
        self.add_item(self.reason)

    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True, thinking=True)
        player = self.player_name.value
        reason = self.reason.value if self.reason.value else "Không có lý do."
        
        if self.action_type == "ban":
            response = await self.cog._execute_ban_command(player, reason)
            embed = make_mc_embed(
                title="🔨 Cấm Người Chơi (BAN)",
                description=f"Đã cấm người chơi **`{player}`** tham gia máy chủ!",
                color=MC_RED,
                player_name=player,
                fields=[
                    ("Lý do", f"```{reason}```", False),
                    ("Phản hồi Server", f"```{response}```", False)
                ]
            )
            await interaction.followup.send(embed=embed, ephemeral=True)
        elif self.action_type == "kick":
            response = await self.cog._execute_kick_command(player, reason)
            embed = make_mc_embed(
                title="👢 Trục Xuất Người Chơi (KICK)",
                description=f"Đã trục xuất người chơi **`{player}`** khỏi máy chủ!",
                color=MC_ORANGE,
                player_name=player,
                fields=[
                    ("Lý do", f"```{reason}```", False),
                    ("Phản hồi Server", f"```{response}```", False)
                ]
            )
            await interaction.followup.send(embed=embed, ephemeral=True)

class UnbanPlayerModal(discord.ui.Modal, title="Gỡ Ban Người chơi"):
    def __init__(self, cog_instance):
        super().__init__()
        self.cog = cog_instance

        self.player_name = discord.ui.TextInput(
            label="Tên người chơi Minecraft",
            placeholder="Nhập tên người chơi cần gỡ ban...",
            required=True,
            max_length=16
        )
        self.add_item(self.player_name)

    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True, thinking=True)
        player = self.player_name.value
        response = await self.cog._execute_pardon_command(player)
        embed = make_mc_embed(
            title="🔓 Gỡ Cấm Người Chơi (UNBAN)",
            description=f"Đã gỡ cấm cho người chơi **`{player}`** thành công!",
            color=MC_GREEN,
            player_name=player,
            fields=[("Phản hồi Server", f"```{response}```", False)]
        )
        await interaction.followup.send(embed=embed, ephemeral=True)

class OpPlayerModal(discord.ui.Modal, title="Cấp quyền Operator"):
    def __init__(self, cog_instance):
        super().__init__()
        self.cog = cog_instance

        self.player_name = discord.ui.TextInput(
            label="Tên người chơi cần cấp OP",
            placeholder="Nhập tên người chơi...",
            required=True,
            max_length=16
        )
        self.add_item(self.player_name)

    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True, thinking=True)
        player = self.player_name.value
        response = await self.cog._execute_op_command(player, "op")
        embed = make_mc_embed(
            title="👑 Cấp Quyền Operator (OP)",
            description=f"Đã cấp quyền Quản trị viên (OP) cho **`{player}`**!",
            color=MC_GOLD,
            player_name=player,
            fields=[("Phản hồi Server", f"```{response}```", False)]
        )
        await interaction.followup.send(embed=embed, ephemeral=True)

class DeopPlayerModal(discord.ui.Modal, title="Gỡ quyền Operator"):
    def __init__(self, cog_instance):
        super().__init__()
        self.cog = cog_instance

        self.player_name = discord.ui.TextInput(
            label="Tên người chơi cần gỡ OP",
            placeholder="Nhập tên người chơi...",
            required=True,
            max_length=16
        )
        self.add_item(self.player_name)

    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True, thinking=True)
        player = self.player_name.value
        response = await self.cog._execute_op_command(player, "deop")
        embed = make_mc_embed(
            title="🔻 Gỡ Quyền Operator (DEOP)",
            description=f"Đã gỡ quyền Quản trị viên (OP) của **`{player}`**!",
            color=MC_RED,
            player_name=player,
            fields=[("Phản hồi Server", f"```{response}```", False)]
        )
        await interaction.followup.send(embed=embed, ephemeral=True)

class MinecraftPanelView(discord.ui.View):
    """View chứa các nút điều khiển server Minecraft."""
    def __init__(self, cog_instance, author_id: int, timeout=300):
        super().__init__(timeout=timeout)
        self.cog = cog_instance
        self.author_id = author_id

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        """Kiểm tra xem người tương tác có phải là người gọi lệnh không."""
        if interaction.user.id != self.author_id:
            embed = make_mc_embed(
                title="⛔ Từ Chối Truy Cập",
                description="Bảng điều khiển này không thuộc về bạn. Hãy gõ `/mc` để mở bảng điều khiển của riêng bạn!",
                color=MC_RED
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return False
        return True

    async def perform_power_action(self, interaction: discord.Interaction, signal: str, action_name: str):
        """Hàm chung để xử lý các hành động về nguồn."""
        await interaction.response.defer(ephemeral=True, thinking=True)
        success = await self.cog.send_panel_power_signal(signal)
        if success:
            act_color = MC_GREEN if signal == "start" else (MC_ORANGE if signal == "restart" else MC_RED)
            embed = make_mc_embed(
                title=f"⚡ Tín Hiệu Nguồn: {action_name}",
                description=f"Đã gửi lệnh **{action_name}** đến máy chủ Minecraft thành công!",
                color=act_color,
                footer="Pika Hosting Pterodactyl API"
            )
            await interaction.followup.send(embed=embed, ephemeral=True)
        else:
            embed = make_mc_embed(
                title=f"❌ Thất Bại Tín Hiệu Nguồn: {action_name}",
                description=f"Không thể gửi lệnh **{action_name}** đến máy chủ. Vui lòng kiểm tra lại kết nối API Hosting.",
                color=MC_RED,
                footer="Pika Hosting Pterodactyl API"
            )
            await interaction.followup.send(embed=embed, ephemeral=True)
        # Tự động làm mới panel sau khi thực hiện
        await asyncio.sleep(5)
        embed, file = await self.cog.get_server_status_data()
        await interaction.edit_original_response(embed=embed, view=self, attachments=[file] if file else [])

    @discord.ui.button(label="Start", style=discord.ButtonStyle.green, emoji="▶️", row=0)
    async def start_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.perform_power_action(interaction, "start", "START")

    @discord.ui.button(label="Stop", style=discord.ButtonStyle.danger, emoji="⏹️", row=0)
    async def stop_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.perform_power_action(interaction, "stop", "STOP")

    @discord.ui.button(label="Restart", style=discord.ButtonStyle.danger, emoji="🔥", row=0)
    async def restart_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.perform_power_action(interaction, "restart", "RESTART")

    @discord.ui.button(label="Làm mới", style=discord.ButtonStyle.primary, emoji="🔄", row=1)
    async def refresh_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer()
        embed, file = await self.cog.get_server_status_data()
        await interaction.edit_original_response(embed=embed, view=self, attachments=[file] if file else [])

    @discord.ui.button(label="Whitelist", style=discord.ButtonStyle.secondary, emoji="📝", row=1)
    async def whitelist_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        embed = make_mc_embed(
            title="📝 Quản Lý Danh Sách Whitelist",
            description="Vui lòng bấm các nút bên dưới để Thêm, Xóa hoặc Xem danh sách người chơi trong Whitelist:",
            color=MC_BLUE
        )
        await interaction.response.send_message(embed=embed, ephemeral=True, view=WhitelistActionView(self.cog, interaction.user.id))

    @discord.ui.button(label="Ban", style=discord.ButtonStyle.danger, emoji="🔨", row=2)
    async def ban_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(BanKickPlayerModal(self.cog, "ban"))

    @discord.ui.button(label="Kick", style=discord.ButtonStyle.danger, emoji="👢", row=2)
    async def kick_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(BanKickPlayerModal(self.cog, "kick"))

    @discord.ui.button(label="Unban", style=discord.ButtonStyle.success, emoji="✅", row=2)
    async def unban_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(UnbanPlayerModal(self.cog))

    @discord.ui.button(label="Add OP", style=discord.ButtonStyle.success, emoji="👑", row=3)
    async def add_op_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(OpPlayerModal(self.cog))

    @discord.ui.button(label="Del OP", style=discord.ButtonStyle.danger, emoji="🗑️", row=3)
    async def del_op_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(DeopPlayerModal(self.cog))

    @discord.ui.button(label="List OPs", style=discord.ButtonStyle.secondary, emoji="📜", row=3)
    async def list_ops_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer(ephemeral=True, thinking=True)
        response = await self.cog._execute_op_command(None, "list")
        embed = make_mc_embed(
            title="👑 Danh Sách Operator (OP)",
            description=f"```{response if response else 'Không có phản hồi hoặc lệnh không được hỗ trợ.'}```",
            color=MC_GOLD
        )
        await interaction.followup.send(embed=embed, ephemeral=True)

    @discord.ui.button(label="Bật Whitelist", style=discord.ButtonStyle.success, emoji="✅", row=4)
    async def enable_whitelist_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Bật chế độ whitelist trên server."""
        await interaction.response.defer(ephemeral=True)
        response = await self.cog.execute_rcon_command("whitelist on")
        embed = make_mc_embed(
            title="🔒 Bật Chế Độ Whitelist",
            description="Đã gửi lệnh kích hoạt Whitelist tới server Minecraft.",
            color=MC_GREEN,
            fields=[("Phản hồi Server", f"```{response}```", False)]
        )
        await interaction.followup.send(embed=embed, ephemeral=True)

    @discord.ui.button(label="Tắt Whitelist", style=discord.ButtonStyle.danger, emoji="❌", row=4)
    async def disable_whitelist_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Tắt chế độ whitelist trên server."""
        await interaction.response.defer(ephemeral=True)
        response = await self.cog.execute_rcon_command("whitelist off")
        embed = make_mc_embed(
            title="🔓 Tắt Chế Độ Whitelist",
            description="Đã gửi lệnh tắt chế độ Whitelist (cho phép mọi người chơi tham gia).",
            color=MC_ORANGE,
            fields=[("Phản hồi Server", f"```{response}```", False)]
        )
        await interaction.followup.send(embed=embed, ephemeral=True)

class WhitelistActionView(discord.ui.View):
    def __init__(self, cog_instance, author_id: int, timeout=60):
        super().__init__(timeout=timeout)
        self.cog = cog_instance
        self.author_id = author_id

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        return interaction.user.id == self.author_id

    @discord.ui.button(label="Thêm vào Whitelist", style=discord.ButtonStyle.green, emoji="➕")
    async def add_to_whitelist_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(WhitelistPlayerModal(self.cog, "add"))

    @discord.ui.button(label="Xóa khỏi Whitelist", style=discord.ButtonStyle.red, emoji="➖")
    async def remove_from_whitelist_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(WhitelistPlayerModal(self.cog, "remove"))

    @discord.ui.button(label="Xem Whitelist", style=discord.ButtonStyle.secondary, emoji="📜")
    async def list_whitelist_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer(ephemeral=True, thinking=True)
        response = await self.cog._execute_whitelist_command("list", "")
        embed = make_mc_embed(
            title="📜 Danh Sách Whitelist",
            description=f"```{response}```",
            color=MC_BLUE
        )
        await interaction.followup.send(embed=embed, ephemeral=True)

class MinecraftCog(commands.Cog, name="Minecraft Manager"):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self._log_task = None
        self.log_configs = load_mc_log_config()
        self._log_task = self.bot.loop.create_task(self.log_listener_task())

    @commands.hybrid_group(name="minecraft", aliases=["mc"], description="Quản lý server Minecraft của bạn từ Discord.")
    async def mc(self, ctx: commands.Context):
        """Nhóm lệnh quản lý server Minecraft."""
        if ctx.invoked_subcommand is None:            
            prefix = ctx.prefix
            embed = discord.Embed(
                title=t(ctx.guild, "MC_PANEL_TITLE"),
                description=t(ctx.guild, "MC_PANEL_DESC"),
                color=discord.Color.from_rgb(83, 166, 73) # Màu xanh lá của Minecraft
            )
            if self.bot.user.avatar:
                embed.set_thumbnail(url=self.bot.user.avatar.url)

            embed.add_field(
                name=t(ctx.guild, "MC_PANEL_FIELD_STATUS"),
                value=t(ctx.guild, "MC_PANEL_FIELD_STATUS_VALUE", prefix=prefix),
                      #f"`{prefix}mc panel` - Mở bảng điều khiển server.",
                inline=False
            )
            embed.add_field(
                name=t(ctx.guild, "MC_PANEL_FIELD_MANAGE"),
                value=t(ctx.guild, "MC_PANEL_FIELD_MANAGE_VALUE", prefix=prefix),
                      #f"`{prefix}mc admin <add/remove/list>` - Quản lý người dùng có quyền MC Admin.\n"
                      #f"`{prefix}mc panel` - Mở bảng điều khiển quản lý server.",
                inline=False
            )
            embed.add_field(
                name="🔗 LIÊN KẾT TÀI KHOẢN",
                value=f"`{prefix}mc account` - Xem trạng thái đã liên kết tài khoản.\n"
                      f"`{prefix}mc link [mã/tên]` - Liên kết nhân vật Minecraft.\n"
                      f"`{prefix}mc unlink` - Hủy liên kết tài khoản.\n"
                      f"`{prefix}mc coins` - Xem ví và chuyển đổi tiền giữa Discord và Game.",
                inline=False
            )
            embed.set_footer(text=t(ctx.guild, "MC_PANEL_FOOTER"))
            await ctx.send(embed=embed)

    def clean_minecraft_text(self, text: str) -> str:
        """Hàm xóa bỏ các mã màu của Minecraft (§) và cả mã màu ANSI console."""
        if not text:
            return ""
        text = re.sub(r'§[0-9a-fk-orx]', '', text, flags=re.IGNORECASE)
        text = re.sub(r'\x1b\[[0-9;]*m', '', text)
        return text.strip()

    def _blocking_rcon_command(self, command: str, guild_id=None) -> str:
        """Hàm đồng bộ (blocking) để thực thi RCON, hỗ trợ đa server theo guild_id."""
        ok, res = send_rcon_command_sync(command, guild_id=guild_id)
        return res

    async def execute_rcon_command(self, command: str, guild_id=None) -> str:
        """Thực thi lệnh RCON tới server."""
        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(None, self._blocking_rcon_command, command, guild_id)

    async def _execute_whitelist_command(self, action: str, player_name: str) -> str:
        """Thực thi lệnh whitelist qua RCON."""
        if action == "list":
            return await self.execute_rcon_command("whitelist list")
        elif action == "add":
            return await self.execute_rcon_command(f"whitelist add {player_name}")
        elif action == "remove":
            return await self.execute_rcon_command(f"whitelist remove {player_name}")
        return "Lỗi: Hành động whitelist không hợp lệ."

    async def _execute_ban_command(self, player_name: str, reason: str) -> str:
        """Thực thi lệnh ban qua RCON."""
        return await self.execute_rcon_command(f"ban {player_name} {reason}")

    async def _execute_kick_command(self, player_name: str, reason: str) -> str:
        """Thực thi lệnh kick qua RCON."""
        # Minecraft kick command doesn't usually take a reason in the command itself,
        # but it's good practice to log it.
        return await self.execute_rcon_command(f"kick {player_name} {reason}")

    async def _execute_pardon_command(self, player_name: str) -> str:
        """Thực thi lệnh pardon (unban) qua RCON."""
        return await self.execute_rcon_command(f"pardon {player_name}")

    async def _execute_op_command(self, player_name: str | None, action: str) -> str:
        """Thực thi các lệnh liên quan đến OP."""
        if action == "op" and player_name:
            return await self.execute_rcon_command(f"op {player_name}")
        elif action == "deop" and player_name:
            return await self.execute_rcon_command(f"deop {player_name}")
        elif action == "list":
            return await self.execute_rcon_command("op list") # Thử lệnh phổ biến, có thể không hoạt động trên mọi server
        return "Lỗi: Hành động OP không hợp lệ."

    async def send_panel_power_signal(self, signal: str) -> bool:
        """Gửi lệnh nguồn (start/stop/restart) đến Pika Hosting qua API."""
        url = f"{PANEL_URL.rstrip('/')}/api/client/servers/{SERVER_ID}/power"
        headers = {
            "Authorization": f"Bearer {PANEL_API_KEY}",
            "Accept": "application/json",
            "Content-Type": "application/json"
        }
        payload = {"signal": signal}

        async with aiohttp.ClientSession() as session:
            try:
                async with session.post(url, json=payload, headers=headers) as response:
                    if response.status in [204, 200]:
                        return True
                    return False
            except Exception:
                return False
    
    # --- HỆ THỐNG LOG CONSOLE MINECRAFT ---
    def cog_unload(self):
        """Dừng task khi cog được gỡ."""
        if self._log_task:
            self._log_task.cancel()

    async def get_websocket_details(self):
        """Lấy thông tin websocket từ Pterodactyl API."""
        url = f"{PANEL_URL.rstrip('/')}/api/client/servers/{SERVER_ID}/websocket"
        headers = {"Authorization": f"Bearer {PANEL_API_KEY}", "Accept": "application/json"}
        async with aiohttp.ClientSession() as session:
            try:
                async with session.get(url, headers=headers) as response:
                    if response.status == 200:
                        return await response.json()
            except Exception as e:
                print(f"[MC Log] Lỗi khi lấy thông tin websocket: {e}")
        return None

    def format_mc_death_message(self, raw: str) -> str:
        """Chuyển đổi các thông báo chết tiếng Anh mặc định trong Minecraft sang tiếng Việt sinh động."""
        text = raw.lower().strip()
        if "was slain by" in text:
            killer = raw.split("was slain by", 1)[1].strip()
            return f"bị sát hại dưới tay **{killer}**"
        elif "was shot by" in text:
            killer = raw.split("was shot by", 1)[1].strip()
            return f"bị bắn hạ bởi xạ thủ **{killer}**"
        elif "tried to swim in lava" in text:
            return "thử nhảy vào hồ dung nham rực lửa và bốc cháy thành tro"
        elif "drowned" in text:
            return "chìm sâu dưới làn nước lạnh và chết đuối"
        elif "blew up" in text:
            return "bị phát nổ tung thành trăm mảnh tro bụi"
        elif "hit the ground too hard" in text or "fell from" in text:
            return "trượt chân ngã từ trên cao xuống đất tan xác"
        elif "froze to death" in text:
            return "chết cóng trong cái lạnh thấu xương của băng tuyết"
        elif "starved to death" in text:
            return "kiệt sức ngã gục vì quá đói lả"
        elif "suffocated in a wall" in text:
            return "nghẹt thở đau đớn kẹt trong kẽ đá"
        elif "went up in flames" in text or "burned to death" in text:
            return "bị thiêu rụi thành tro tàn trong ngọn lửa"
        return f"đã {raw.strip()}"

    async def parse_and_send_log(self, log_line: str):
        """Phân tích một dòng log và gửi đến kênh Discord nếu khớp."""
        # SỬA LỖI: Tìm kênh log dựa trên ID của server Discord, không phải ID server game
        guild_id_str = next((gid for gid, cid in self.log_configs.items()), None)
        if not guild_id_str: return

        log_channel_id = self.log_configs.get(guild_id_str)
        if not log_channel_id:
            return

        log_channel = self.bot.get_channel(int(log_channel_id))
        if not log_channel: return

        cleaned_line = self.clean_minecraft_text(log_line)
        if not cleaned_line:
            return

        embed = None

        # 1. Log Chat: Tìm đoạn "[TEAM] [RANK] <name_player> » <message>" (<MCPE.name_player> nếu là người chơi PE)
        chat_match = re.search(r"^(?:\[Not Secure\]\s*)?((?:\[.*?\]\s)+)?([a-zA-Z0-9_]{3,16})\s»\s(.*)", cleaned_line)
        
        # 2. Player Join: Tìm đoạn "name_player joined the game"
        join_match = re.search(r"([a-zA-Z0-9_\.\* ]{3,20}) joined the game", cleaned_line)
        
        # 3. Player Leave: Tìm đoạn "name_player left the game"
        leave_match = re.search(r"([a-zA-Z0-9_\.\* ]{3,20}) left the game", cleaned_line)
        
        # 4. Advancement: Tìm đoạn "name_player has made the advancement [Tên_Thành_Tựu]"
        adv_match = re.search(r"([a-zA-Z0-9_\.\* ]{3,20}) has made the advancement \[([^\]]+)\]", cleaned_line)

        # 5. Player Death: Tìm các thông báo chết
        death_match = re.search(r"([a-zA-Z0-9_]{3,16}) (was slain by .*|was shot by .*|drowned|fell .*|blew up|hit the ground too hard|froze to death|starved to death|suffocated in a wall|tried to swim in lava.*|went up in flames|burned to death)", cleaned_line)

        # Phân nhánh xử lý logic và thiết kế embed sinh động, chuyên nghiệp
        if chat_match:
            prefix_tags, player_name, message = chat_match.groups()
            prefix_str = f"[{prefix_tags.strip()}] " if prefix_tags else ""
            avatar_url = f"https://mc-heads.net/avatar/{player_name}/64"
            embed = discord.Embed(
                description=f"💬 **{message}**",
                color=MC_BLUE
            )
            embed.set_author(name=f"{prefix_str}{player_name}", icon_url=avatar_url)
            embed.set_footer(text=f"Sakura Minecraft Network • {MINECRAFT_HOST}", icon_url=MC_GRASS_ICON)
            embed.timestamp = discord.utils.utcnow()

        elif join_match:
            player_name = join_match.group(1).strip()
            avatar_url = f"https://mc-heads.net/avatar/{player_name}/64"
            head_url = f"https://mc-heads.net/head/{player_name}/128"
            embed = discord.Embed(
                title=f"📥 Chào mừng {player_name}!",
                description=(
                    f"🟢 Người chơi **{player_name}** vừa tham gia máy chủ!\n"
                    f"*Chúc bạn có những giờ phút sinh tồn và khám phá thế giới thật tuyệt vời!*"
                ),
                color=MC_GREEN
            )
            embed.set_author(name="Người chơi tham gia máy chủ", icon_url=avatar_url)
            embed.set_thumbnail(url=head_url)
            embed.set_footer(text=f"Sakura Minecraft Network • {MINECRAFT_HOST}", icon_url=MC_GRASS_ICON)
            embed.timestamp = discord.utils.utcnow()

        elif leave_match:
            player_name = leave_match.group(1).strip()
            avatar_url = f"https://mc-heads.net/avatar/{player_name}/64"
            head_url = f"https://mc-heads.net/head/{player_name}/128"
            embed = discord.Embed(
                title=f"📤 Tạm biệt {player_name}!",
                description=(
                    f"🔴 Người chơi **{player_name}** đã ngắt kết nối khỏi máy chủ.\n"
                    f"*Hẹn sớm gặp lại bạn trong chuyến hành trình tiếp theo!*"
                ),
                color=discord.Color.from_rgb(149, 165, 166)
            )
            embed.set_author(name="Người chơi rời máy chủ", icon_url=avatar_url)
            embed.set_thumbnail(url=head_url)
            embed.set_footer(text=f"Sakura Minecraft Network • {MINECRAFT_HOST}", icon_url=MC_GRASS_ICON)
            embed.timestamp = discord.utils.utcnow()

        elif adv_match:
            player_name, advancement = adv_match.groups()
            player_name = player_name.strip()
            avatar_url = f"https://mc-heads.net/avatar/{player_name}/64"
            head_url = f"https://mc-heads.net/head/{player_name}/128"
            embed = discord.Embed(
                title=f"🏆 TIẾN TRÌNH / THÀNH TỰU MỚI!",
                description=(
                    f"⭐ Chúc mừng **{player_name}** vừa chinh phục được thành tựu:\n\n"
                    f"### 🎖️ [ {advancement} ]\n\n"
                    f"*Một cột mốc đáng tự hào trên hành trình sinh tồn và khám phá!*"
                ),
                color=MC_GOLD
            )
            embed.set_author(name=f"Vinh danh: {player_name}", icon_url=avatar_url)
            embed.set_thumbnail(url=head_url)
            embed.set_footer(text=f"Sakura Minecraft Network • Mở khóa thành tựu", icon_url=MC_GRASS_ICON)
            embed.timestamp = discord.utils.utcnow()

        elif death_match:
            player_name, death_message = death_match.groups()
            player_name = player_name.strip()
            avatar_url = f"https://mc-heads.net/avatar/{player_name}/64"
            head_url = f"https://mc-heads.net/head/{player_name}/128"
            vi_desc = self.format_mc_death_message(death_message)
            embed = discord.Embed(
                title=f"☠️ {player_name} đã hy sinh!",
                description=(
                    f"💀 **Nguyên nhân:** {player_name} {vi_desc}.\n\n"
                    f"⚠️ *Đồ đạc có thể rơi tại hiện trường! Hãy nhanh chóng quay lại nhặt đồ trước khi biến mất!*"
                ),
                color=MC_RED
            )
            embed.set_author(name="Báo cáo tử vong Minecraft", icon_url=avatar_url)
            embed.set_thumbnail(url=head_url)
            embed.set_footer(text=f"Sakura Minecraft Network • Chia buồn sâu sắc", icon_url=MC_GRASS_ICON)
            embed.timestamp = discord.utils.utcnow()

        elif "Done" in cleaned_line and "For help, type \"help\"" in cleaned_line:
            embed = discord.Embed(
                title="🟢 MÁY CHỦ SẴN SÀNG HOẠT ĐỘNG!",
                description=(
                    f"🚀 **Máy chủ Sakura Minecraft đã khởi động thành công!**\n\n"
                    f"🌐 **IP Kết nối:** `{MINECRAFT_HOST}:{MINECRAFT_PORT}`\n"
                    f"👥 **Trạng thái:** Đang mở cửa đón các dũng sĩ gia nhập thế giới!\n"
                    f"Chúc toàn thể cư dân có những trải nghiệm thật vui vẻ."
                ),
                color=MC_GREEN
            )
            embed.set_thumbnail(url=MC_GRASS_ICON)
            embed.set_footer(text="Sakura Minecraft Network • Server Online", icon_url=MC_GRASS_ICON)
            embed.timestamp = discord.utils.utcnow()
            
        elif "Stopping server" in cleaned_line:
            embed = discord.Embed(
                title="🔴 MÁY CHỦ ĐANG ĐÓNG CỬA",
                description=(
                    "🛑 **Máy chủ Minecraft đang tiến hành lưu dữ liệu và tắt an toàn.**\n\n"
                    "🔒 Toàn bộ dữ liệu vị trí, rương đồ và kinh nghiệm đã được bảo toàn.\n"
                    "Thông báo sẽ được gửi lại khi máy chủ mở cửa trở lại!"
                ),
                color=MC_RED
            )
            embed.set_thumbnail(url=MC_GRASS_ICON)
            embed.set_footer(text="Sakura Minecraft Network • Server Offline", icon_url=MC_GRASS_ICON)
            embed.timestamp = discord.utils.utcnow()
        else:
            pass
        
        if embed:
            try:
                await log_channel.send(embed=embed)
            except discord.Forbidden:
                print(f"[MC Log] Thiếu quyền gửi tin nhắn vào kênh log {log_channel_id}")
            except Exception as e:
                print(f"[MC Log] Lỗi khi gửi log: {e}")

    # --- TÍNH NĂNG CHAT BRIDGE: DISCORD TO MINECRAFT ---
    @commands.Cog.listener("on_message")
    async def discord_to_minecraft_bridge(self, message: discord.Message):
        """Lắng nghe tin nhắn từ kênh Discord và đồng bộ vào game qua Plugin hoặc RCON."""
        # Bỏ qua tin nhắn từ bot, tin nhắn riêng tư, hoặc tin nhắn là lệnh
        if message.author.bot or not message.guild:
            return

        # Bỏ qua nếu tin nhắn là một lệnh
        prefix = await self.bot.get_prefix(message)
        if isinstance(prefix, str) and message.content.startswith(prefix):
            return
        if isinstance(prefix, (list, tuple)) and any(message.content.startswith(p) for p in prefix):
            return

        # 1. Hỗ trợ Server Minecraft kết nối qua Plugin của Guild này
        try:
            mc_serv = await get_mc_server_by_guild(message.guild.id)
            if mc_serv:
                chat_ch = str(mc_serv.get("chat_channel_id") or "")
                if str(message.channel.id) == chat_ch:
                    content = message.clean_content or ("[Tệp đính kèm]" if message.attachments else "")
                    if content:
                        await queue_mc_chat(mc_serv["server_key"], "discord", message.author.display_name, content)
        except Exception as e:
            print(f"[Plugin Chat Bridge Error]: {e}")

        # 2. Hỗ trợ kênh log cũ qua RCON nếu có
        log_channel_id = self.log_configs.get(str(message.guild.id))
        if log_channel_id and message.channel.id == log_channel_id:
            author_name = message.author.display_name
            content = message.clean_content or ("[Tệp đính kèm]" if message.attachments else "")
            author_escaped = author_name.replace('\\', '\\\\').replace('"', '\\"')
            content_escaped = content.replace('\\', '\\\\').replace('"', '\\"')
            rcon_cmd = (
                f'tellraw @a {{"text":"","extra":['
                f'{{"text":"[Discord] ","color":"#7289DA"}},'
                f'{{"text":"{author_escaped}: ","color":"#FFFFFF","bold":true}},'
                f'{{"text":"{content_escaped}","color":"white","bold":false}}'
                f']}}'
            )
            try:
                await self.execute_rcon_command(rcon_cmd)
            except Exception:
                pass



    async def log_listener_task(self):
        """Task chạy nền để kết nối và lắng nghe log từ server."""
        await self.bot.wait_until_ready()
        
        while not self.bot.is_closed():
            # SỬA LỖI: Chỉ cần có bất kỳ cấu hình nào là chạy, không cần check theo SERVER_ID
            if self.log_configs:
                
                # DI CHUYỂN VÀO TRONG VÒNG LẶP: Luôn lấy token mới trước mỗi lần connect
                ws_details = await self.get_websocket_details()
                if not ws_details:
                    print("[MC Log] Không thể lấy thông tin websocket, thử lại sau 30s.")
                    await asyncio.sleep(30)
                    continue

                socket_url = ws_details['data']['socket']
                auth_token = ws_details['data']['token']

                try:
                    # Kết nối tới websocket với các tham số giữ kết nối (ping/pong)
                    async with websockets.connect(
                        socket_url, 
                        origin="https://cp.pikamc.vn",
                        ping_interval=20,     
                        ping_timeout=20, 
                        open_timeout=20
                    ) as websocket:
                        
                        # Gửi auth token để xác thực
                        await websocket.send(json.dumps({"event": "auth", "args": [auth_token]}))
                        print(f"[MC Log] Đã kết nối tới websocket của server {SERVER_ID}.")

                        # Vòng lặp nhận tin nhắn từ websocket
                        async for message in websocket:
                            try:
                                data = json.loads(message)
                                if data.get("event") == "console output":
                                    await self.parse_and_send_log(data["args"][0])
                                    
                                # THÊM VÀO: Lắng nghe sự kiện token sắp hết hạn từ Pterodactyl (nếu có)
                                elif data.get("event") == "token expiring" or data.get("event") == "token expired":
                                    print("[MC Log] Token hết hạn, đang chủ động ngắt để lấy token mới...")
                                    break # Thoát vòng lặp nhận tin nhắn để chạy lại vòng lặp chính (lấy token mới)
                                    
                            except json.JSONDecodeError:
                                pass
                            except Exception as e:
                                print(f"[MC Log] Lỗi khi xử lý tin nhắn log: {e}")
                
                except (websockets.exceptions.ConnectionClosed, websockets.exceptions.ConnectionClosedError, websockets.exceptions.ConnectionClosedOK, ConnectionRefusedError) as e:
                    print(f"[MC Log] Kết nối websocket đã đóng: {type(e).__name__}. Đang kết nối lại sau 10 giây...")
                    await asyncio.sleep(10)
                except asyncio.TimeoutError:
                    print("[MC Log] Kết nối websocket bị timeout. Đang thử lại...")
                    await asyncio.sleep(5)
                except Exception as e:
                    print(f"[MC Log] Lỗi websocket không xác định: {e}. Thử lại sau 30 giây...")
                    await asyncio.sleep(30)
            else:
                # Nếu chưa cấu hình kênh log, ngủ 30s rồi kiểm tra lại
                await asyncio.sleep(30)

    async def get_server_resources(self) -> dict | None:
        """Lấy thông tin tài nguyên (CPU, RAM, Disk) từ Pterodactyl API."""
        url = f"{PANEL_URL.rstrip('/')}/api/client/servers/{SERVER_ID}/resources"
        headers = {
            "Authorization": f"Bearer {PANEL_API_KEY}",
            "Accept": "application/json",
        }
        async with aiohttp.ClientSession() as session:
            try:
                async with session.get(url, headers=headers, timeout=10) as response:
                    if response.status == 200:
                        return await response.json()
            except Exception as e:
                print(f"[MC Panel] Lỗi khi lấy tài nguyên server: {e}")
        return None

    async def get_server_status_data(self, guild: discord.Guild | None = None) -> tuple[discord.Embed, discord.File | None]:

        """Helper function to fetch server data and build the status embed."""

        server_icon_file = None
        try:
            server = await JavaServer.async_lookup(f"{MINECRAFT_HOST}:{MINECRAFT_PORT}")
            stats = await server.async_status() 

            embed = discord.Embed(title="🎮 Bảng Điều Khiển Server Minecraft", color=discord.Color.green())
            embed.add_field(name="IP Server", value=f"`{MINECRAFT_HOST}:{MINECRAFT_PORT}`", inline=False)

            cleaned_motd = self.clean_minecraft_text(stats.description)
            embed.description = f"```\n{cleaned_motd}```"

            embed.add_field(name="Phiên bản", value=f"`{stats.version.name}`", inline=True)
            embed.add_field(name="Ping", value=f"`{stats.latency:.2f} ms`", inline=True)
            embed.add_field(name="Người chơi", value=f"`{stats.players.online}/{stats.players.max}`", inline=True)

            # --- Lấy thông tin tài nguyên từ Pika API ---
            resources = await self.get_server_resources()
            if resources and 'attributes' in resources:
                res_attr = resources['attributes']
                state = res_attr.get('current_state', 'N/A').capitalize()
                cpu_usage = res_attr.get('resources', {}).get('cpu_absolute', 0)
                ram_bytes = res_attr.get('resources', {}).get('memory_bytes', 0)
                disk_bytes = res_attr.get('resources', {}).get('disk_bytes', 0)
                
                ram_mb = ram_bytes / (1024 * 1024)
                disk_mb = disk_bytes / (1024 * 1024)

                embed.add_field(name="Trạng thái Panel", value=f"`{state}`", inline=True)
                embed.add_field(name="CPU", value=f"`{cpu_usage:.2f}%`", inline=True)
                embed.add_field(name="RAM", value=f"`{ram_mb:.2f} MB`", inline=True)

            # --- Lấy danh sách người chơi và tạo ảnh skin đầu ---
            players_online = []
            world_name = "Không rõ"
            plugins_list = []
            try:
                query_server = await JavaServer.async_lookup(f"{MINECRAFT_HOST}:{QUERY_PORT}")
                query = await query_server.async_query()
                players_online = query.players.names
                world_name = query.map
                plugins_list = query.software.plugins
            except Exception:
                rcon_response = await self.execute_rcon_command("list")
                # Phân tích chuỗi từ RCON: "There are 2/20 players online: player1, player2"
                match = re.search(r'online: (.*)', rcon_response)
                if match:
                    players_online = [p.strip() for p in match.group(1).split(',')]

            if players_online:
                # Hiển thị tên người chơi dưới dạng text
                player_list_str = ", ".join(f"`{p}`" for p in players_online)
                embed.add_field(name=f"Danh sách online ({len(players_online)})", value=player_list_str, inline=False)
            else:
                embed.add_field(name="Danh sách online", value="`Không có ai.`", inline=False)

            # Thêm thông tin World và Plugins
            embed.add_field(name="🗺️ Thế giới (World)", value=f"`{world_name}`", inline=True)
            if plugins_list:
                plugins_str = ", ".join(f"`{p}`" for p in plugins_list[:5]) # Giới hạn 5 plugin
                if len(plugins_list) > 5:
                    plugins_str += f" và {len(plugins_list) - 5} cái khác..."
                embed.add_field(name=f"🔌 Plugins ({len(plugins_list)})", value=plugins_str, inline=False)

            if stats.icon:
                icon_data = base64.b64decode(stats.icon.split(',')[-1])
                server_icon_file = discord.File(io.BytesIO(icon_data), filename="server_icon.png")
                embed.set_thumbnail(url="attachment://server_icon.png")
            elif not embed.thumbnail.url:
                embed.set_thumbnail(url=MC_GRASS_ICON)

            embed.set_footer(text=f"Sakura Minecraft Network • Host: {MINECRAFT_HOST}", icon_url=MC_GRASS_ICON)
            embed.timestamp = discord.utils.utcnow()
            
            return embed, server_icon_file

        except Exception as e:
            err_desc = t(guild, "MC_STATUS_OFFLINE_DESC", error=e, host=MINECRAFT_HOST, port=MINECRAFT_PORT) if guild else f"Không thể kết nối đến máy chủ {MINECRAFT_HOST}:{MINECRAFT_PORT}.\nLỗi: {e}"
            embed = discord.Embed(
                title="🔴 Trạng Thái Server: Offline hoặc Lỗi", 
                description=err_desc, 
                color=discord.Color.red()
            )
            return embed, None


    @mc.command(name="status", description="Kiểm tra trạng thái của server Minecraft.")
    @commands.cooldown(1, 10, commands.BucketType.user)
    async def status(self, ctx: commands.Context):
        await ctx.defer(ephemeral=True)
        embed, file = await self.get_server_status_data()
        await ctx.send(embed=embed, file=file, view=StatusView(self), ephemeral=True)

    @mc.command(name="panel", description="Hiển thị bảng điều khiển quản lý server Minecraft.")
    @is_mc_admin()
    @commands.cooldown(1, 20, commands.BucketType.user)
    async def panel(self, ctx: commands.Context):
        await ctx.defer()
        embed, file = await self.get_server_status_data()
        await ctx.send(embed=embed, file=file, view=MinecraftPanelView(self, ctx.author.id))

    @mc.command(name="logchannel", description="Thiết lập kênh để ghi lại log từ server Minecraft.")
    @commands.has_permissions(administrator=True)
    async def set_log_channel(self, ctx: commands.Context, channel: discord.TextChannel):
        """Thiết lập kênh log cho server Minecraft."""
        # SỬA LỖI: Lưu cấu hình theo ID của server Discord hiện tại, không phải ID server game
        self.log_configs[str(ctx.guild.id)] = channel.id
        save_mc_log_config(self.log_configs)
        embed = make_mc_embed(
            title="📢 Cài Đặt Kênh Log Minecraft",
            description=f"Đã thiết lập kênh {channel.mention} để ghi lại log, chat và sự kiện của server Minecraft!",
            color=MC_GREEN,
            fields=[
                ("Server Discord", f"{ctx.guild.name} (`{ctx.guild.id}`)", True),
                ("Kênh Log", channel.mention, True)
            ]
        )
        await ctx.send(embed=embed, ephemeral=True)
        # Khởi động lại task nếu nó chưa chạy hoặc đã dừng
        if self._log_task and self._log_task.done():
            self._log_task = self.bot.loop.create_task(self.log_listener_task())

    @mc.command(name="list", description="Liệt kê danh sách người chơi đang online.")
    @commands.cooldown(1, 10, commands.BucketType.user)
    async def list_players(self, ctx: commands.Context):
        """Hiển thị danh sách người chơi online kèm skin đầu."""
        await ctx.defer(ephemeral=True)
        players_online = []
        player_heads_file = None
        
        try:
            # Ưu tiên dùng Query để lấy danh sách người chơi
            query_server = await JavaServer.async_lookup(f"{MINECRAFT_HOST}:{QUERY_PORT}")
            query = await query_server.async_query()
            players_online = query.players.names
        except Exception as e:
            # Nếu Query thất bại, dùng RCON
            rcon_response = await self.execute_rcon_command("list")
            if "Lỗi" not in rcon_response:
                match = re.search(r'online: (.*)', rcon_response)
                if match:
                    players_online = [p.strip() for p in match.group(1).split(',') if p.strip()]

        if not players_online:
            embed = make_mc_embed(
                title="👥 Danh Sách Người Chơi Online (0)",
                description="Hiện tại không có người chơi nào đang kết nối trong server Minecraft.",
                color=MC_DARK
            )
            return await ctx.send(embed=embed, ephemeral=True)

        player_list_str = ", ".join(f"`{p}`" for p in players_online)
        first_head = f"https://mc-heads.net/avatar/{players_online[0]}/64" if players_online else None
        embed = make_mc_embed(
            title=f"👥 Danh Sách Người Chơi Online ({len(players_online)})",
            description=player_list_str,
            color=MC_GREEN,
            thumbnail_url=first_head
        )

        await ctx.send(embed=embed, file=player_heads_file, ephemeral=True)

    @mc.command(name="command", aliases=["lenh"], description="Gửi một lệnh đến console của server (Chỉ Owner).")
    @app_commands.describe(lenh="Lệnh bạn muốn thực thi trên server Minecraft.")
    @is_mc_admin()
    async def rcon_command(self, ctx: commands.Context, *, lenh: str):
        await ctx.defer(ephemeral=True)
        response = await self.execute_rcon_command(lenh)
        embed = make_mc_embed(
            title="💻 Minecraft Console (RCON)",
            description=f"Lệnh thực thi bởi {ctx.author.mention}",
            color=MC_DARK,
            fields=[
                ("📥 Lệnh đã gửi", f"```yaml\n/{lenh.lstrip('/')}```", False),
                ("📤 Phản hồi từ Console", f"```fix\n{response if response else t(ctx.guild, 'MC_RCON_NO_RESPONSE')}```", False)
            ],
            footer="Sakura Minecraft RCON Terminal"
        )
        await ctx.send(embed=embed, ephemeral=True)

    # --- NHÓM LỆNH QUẢN LÝ MC ADMIN ---
    @mc.group(name="admin", description="Quản lý danh sách quản trị viên Minecraft.")
    async def mc_admin(self, ctx: commands.Context):
        if ctx.invoked_subcommand is None:
            await ctx.send_help(ctx.command)

    @mc_admin.command(name="add", description="Thêm một người vào danh sách MC Admin (Chỉ Owner).")
    @commands.is_owner()
    async def mc_admin_add(self, ctx: commands.Context, user: discord.User):
        if user.id in mc_admin_ids:
            embed = make_mc_embed(
                title="⚠️ Đã Là Quản Trị Viên",
                description=f"Thành viên {user.mention} (**{user.display_name}**) đã có trong danh sách MC Admin!",
                color=MC_ORANGE
            )
            return await ctx.send(embed=embed, ephemeral=True)
        
        mc_admin_ids.add(user.id)
        save_mc_admins()
        embed = make_mc_embed(
            title="👑 Thêm Quản Trị Viên Thành Công",
            description=f"Đã thêm {user.mention} (**{user.display_name}**) vào danh sách quản trị viên Minecraft!",
            color=MC_GREEN,
            fields=[("User ID", f"`{user.id}`", True), ("Người thêm", ctx.author.mention, True)]
        )
        await ctx.send(embed=embed, ephemeral=True)

    @mc_admin.command(name="remove", description="Xóa một người khỏi danh sách MC Admin (Chỉ Owner).")
    @commands.is_owner()
    async def mc_admin_remove(self, ctx: commands.Context, user: discord.User):
        if user.id not in mc_admin_ids:
            embed = make_mc_embed(
                title="⚠️ Không Tìm Thấy Quản Trị Viên",
                description=f"Thành viên {user.mention} (**{user.display_name}**) không có trong danh sách MC Admin.",
                color=MC_ORANGE
            )
            return await ctx.send(embed=embed, ephemeral=True)

        mc_admin_ids.remove(user.id)
        save_mc_admins()
        embed = make_mc_embed(
            title="🗑️ Đã Xóa Quản Trị Viên",
            description=f"Đã gỡ {user.mention} (**{user.display_name}**) khỏi danh sách quản trị viên Minecraft.",
            color=MC_RED,
            fields=[("User ID", f"`{user.id}`", True), ("Người thực hiện", ctx.author.mention, True)]
        )
        await ctx.send(embed=embed, ephemeral=True)

    @mc_admin.command(name="list", description="Xem danh sách các quản trị viên Minecraft hiện tại.")
    @is_mc_admin()
    async def mc_admin_list(self, ctx: commands.Context):
        if not mc_admin_ids:
            embed = make_mc_embed(
                title="👑 Danh Sách Quản Trị Viên Minecraft",
                description="Hiện chưa có quản trị viên Minecraft nào được thiết lập.",
                color=MC_DARK
            )
            return await ctx.send(embed=embed, ephemeral=True)
        
        description = ""
        for user_id in mc_admin_ids:
            user = self.bot.get_user(user_id) or await self.bot.fetch_user(user_id)
            description += f"• {user.mention} (`{user_id}`)\n"
        embed = make_mc_embed(
            title="👑 Danh Sách Quản Trị Viên Minecraft",
            description=description,
            color=MC_GOLD
        )
        await ctx.send(embed=embed, ephemeral=True)

    @mc.command(name="start", aliases=["on"], description="Khởi động server Minecraft trên Pika Hosting (Chỉ Owner).")
    @is_mc_admin()
    async def start_server(self, ctx: commands.Context):
        await ctx.defer(ephemeral=True)
        success = await self.send_panel_power_signal("start")
        if success:
            embed = make_mc_embed(
                title="🚀 Đang Khởi Động Máy Chủ...",
                description="Đã gửi lệnh `START` đến Pika Hosting thành công!",
                color=MC_GREEN,
                footer="Pika Hosting Pterodactyl API"
            )
            await ctx.send(embed=embed, ephemeral=True)
        else:
            embed = make_mc_embed(
                title="❌ Khởi Động Thất Bại",
                description="Không thể kết nối hoặc gửi lệnh START đến API của Pika Hosting.",
                color=MC_RED,
                footer="Pika Hosting Pterodactyl API"
            )
            await ctx.send(embed=embed, ephemeral=True)

    @mc.command(name="stop", aliases=["off"], description="Tắt server Minecraft một cách an toàn trên Pika Hosting (Chỉ Owner).")
    @is_mc_admin()
    async def stop_server(self, ctx: commands.Context):
        await ctx.defer(ephemeral=True)
        success = await self.send_panel_power_signal("stop")
        if success:
            embed = make_mc_embed(
                title="🛑 Đang Dừng Máy Chủ...",
                description="Đã gửi lệnh `STOP` đến Pika Hosting.",
                color=MC_RED,
                footer="Pika Hosting Pterodactyl API"
            )
            await ctx.send(embed=embed, ephemeral=True)
        else:
            embed = make_mc_embed(
                title="❌ Dừng Máy Chủ Thất Bại",
                description="Không thể kết nối hoặc gửi lệnh STOP đến API của Pika Hosting.",
                color=MC_RED,
                footer="Pika Hosting Pterodactyl API"
            )
            await ctx.send(embed=embed, ephemeral=True)

    # BỔ SUNG: Lệnh restart bằng text/slash command phòng trường hợp không bấm nút
    @mc.command(name="restart", description="Khởi động lại server Minecraft trên Pika Hosting (Chỉ Owner).")
    @is_mc_admin()
    async def restart_server(self, ctx: commands.Context):
        await ctx.defer(ephemeral=True)
        success = await self.send_panel_power_signal("restart")
        if success:
            embed = make_mc_embed(
                title="🔥 Đang Khởi Động Lại Máy Chủ...",
                description="Đã gửi lệnh `RESTART` đến Pika Hosting.",
                color=MC_ORANGE,
                footer="Pika Hosting Pterodactyl API"
            )
            await ctx.send(embed=embed, ephemeral=True)
        else:
            embed = make_mc_embed(
                title="❌ Khởi Động Lại Thất Bại",
                description="Không thể kết nối hoặc gửi lệnh RESTART đến API của Pika Hosting.",
                color=MC_RED,
                footer="Pika Hosting Pterodactyl API"
            )
            await ctx.send(embed=embed, ephemeral=True)

    # ==============================================================================
    # HỆ THỐNG MINECRAFT PLUGIN - LIÊN KẾT SERVER & ĐIỀU KHIỂN
    # ==============================================================================

    @mc.command(name="servers", description="Xem danh sách các máy chủ Minecraft đang kết nối với bot qua Plugin.")
    async def list_servers_cmd(self, ctx: commands.Context):
        servers = await list_mc_servers(online_threshold=90)
        if not servers:
            embed = make_mc_embed(
                title="🌐 Danh Sách Máy Chủ Minecraft (Plugin)",
                description=(
                    "Hiện chưa có máy chủ Minecraft nào kết nối với bot qua Plugin Sakura.\n\n"
                    "👉 **Hướng dẫn cài đặt:**\n"
                    "1. Cài đặt plugin Sakura Minecraft vào thư mục `plugins/`.\n"
                    "2. Khởi động server, gõ `/sakura link` trong console hoặc trong game để lấy mã.\n"
                    f"3. Dùng `{ctx.prefix}mc linkserver <code>` trên Discord để liên kết!"
                ),
                color=MC_BLUE
            )
            return await ctx.send(embed=embed, ephemeral=True)

        embed = discord.Embed(
            title="🌐 Danh Sách Máy Chủ Minecraft (Plugin)",
            description=f"Tìm thấy **{len(servers)}** máy chủ đang sử dụng Plugin Sakura:",
            color=discord.Color.green()
        )
        for s in servers:
            st_emoji = "🟢" if s.get("status") == "online" else "🔴"
            gid = s.get("guild_id")
            linked_txt = f"🔗 Đã nối với Guild: `{gid}`" if gid else "⚠️ Chưa nối với Server Discord nào"
            if gid and str(gid) == str(ctx.guild.id if ctx.guild else ""):
                linked_txt = "⭐ **Đang nối với Server Discord này**"

            embed.add_field(
                name=f"{st_emoji} {s.get('server_name')} (`{s.get('server_key')}`)",
                value=(
                    f"• Địa chỉ: `{s.get('server_ip')}:{s.get('server_port')}`\n"
                    f"• Người chơi: `{s.get('player_count', 0)}/{s.get('max_players', 50)}` | TPS: `{s.get('tps', 20.0)}`\n"
                    f"• Trạng thái: {linked_txt}"
                ),
                inline=False
            )
        await ctx.send(embed=embed)

    @mc.command(name="linkserver", description="Nối máy chủ Minecraft với Discord Server này bằng mã link (Chỉ Owner/Admin).")
    @commands.guild_only()
    async def link_server_cmd(self, ctx: commands.Context, code: str):
        # Yêu cầu có quyền owner để nối server với server mc
        if not (ctx.author.id == ctx.guild.owner_id or ctx.author.guild_permissions.administrator):
            embed = make_mc_embed(
                title="⛔ Quyền Hạn Bị Từ Chối",
                description="Bạn cần có quyền **Owner** hoặc **Administrator** của Server Discord này để thực hiện liên kết máy chủ Minecraft!",
                color=MC_RED
            )
            return await ctx.send(embed=embed, ephemeral=True)

        res = await link_mc_server_to_guild(code, ctx.guild.id, ctx.author.id)
        if not res.get("ok"):
            embed = make_mc_embed(
                title="❌ Liên Kết Thất Bại",
                description=f"Lỗi: **{res.get('error')}**\nVui lòng kiểm tra lại mã hoặc gõ `/sakura link` trong game để lấy mã mới.",
                color=MC_RED
            )
            return await ctx.send(embed=embed, ephemeral=True)

        embed = discord.Embed(
            title="🎉 LIÊN KẾT MÁY CHỦ MINECRAFT THÀNH CÔNG!",
            description=(
                f"Đã nối máy chủ **`{res.get('server_name')}`** với Server Discord **{ctx.guild.name}**!\n\n"
                f"• Server Key: `{res.get('server_key')}`\n"
                f"• Người kết nối: {ctx.author.mention}\n\n"
                f"👉 **Các thiết lập tiếp theo:**\n"
                f"1. Dùng `{ctx.prefix}mc setchat <#kênh>` để chọn kênh chat 2 chiều giữa Discord & Minecraft.\n"
                f"2. Dùng `{ctx.prefix}mc setlog <#kênh>` để nhận thông báo người chơi tham gia, rời đi, chết, thành tựu.\n"
                f"3. Dùng `{ctx.prefix}mc lenh <lệnh>` để gửi lệnh console trực tiếp vào game!"
            ),
            color=discord.Color.brand_green()
        )
        await ctx.send(embed=embed)

    @mc.command(name="unlinkserver", description="Hủy liên kết máy chủ Minecraft khỏi Discord Server này (Chỉ Owner/Admin).")
    @commands.guild_only()
    async def unlink_server_cmd(self, ctx: commands.Context):
        if not (ctx.author.id == ctx.guild.owner_id or ctx.author.guild_permissions.administrator):
            embed = make_mc_embed(
                title="⛔ Quyền Hạn Bị Từ Chối",
                description="Bạn cần quyền **Owner** hoặc **Administrator** để hủy liên kết máy chủ!",
                color=MC_RED
            )
            return await ctx.send(embed=embed, ephemeral=True)

        serv = await get_mc_server_by_guild(ctx.guild.id)
        if not serv:
            embed = make_mc_embed(
                title="ℹ️ Chưa Liên Kết",
                description="Server Discord này hiện chưa liên kết với máy chủ Minecraft nào.",
                color=MC_DARK
            )
            return await ctx.send(embed=embed, ephemeral=True)

        await unlink_mc_server_from_guild(serv["server_key"], ctx.guild.id)
        embed = make_mc_embed(
            title="✅ Hủy Liên Kết Thành Công",
            description=f"Đã hủy liên kết máy chủ Minecraft **`{serv.get('server_name')}`** khỏi Server Discord này.",
            color=MC_GREEN,
            fields=[
                ("Server Key", f"`{serv.get('server_key')}`", True),
                ("Người thực hiện", ctx.author.mention, True)
            ]
        )
        await ctx.send(embed=embed)

    @mc.command(name="setchat", description="Cài đặt kênh chat 2 chiều giữa Discord và Minecraft (Chỉ Admin).")
    @commands.guild_only()
    @commands.has_permissions(administrator=True)
    async def set_chat_cmd(self, ctx: commands.Context, channel: discord.TextChannel):
        serv = await get_mc_server_by_guild(ctx.guild.id)
        if not serv:
            embed = make_mc_embed(
                title="⚠️ Chưa Liên Kết Máy Chủ",
                description=f"Server Discord này chưa nối với máy chủ Minecraft nào!\nDùng `{ctx.prefix}mc linkserver <code>` trước.",
                color=MC_ORANGE
            )
            return await ctx.send(embed=embed, ephemeral=True)

        await update_mc_server_channels(serv["server_key"], chat_channel_id=str(channel.id))
        embed = make_mc_embed(
            title="💬 Cài Đặt Kênh Chat 2 Chiều",
            description=f"Đã đặt kênh {channel.mention} làm kênh đồng bộ tin nhắn 2 chiều giữa Discord và Minecraft!",
            color=MC_GREEN,
            fields=[
                ("Máy chủ Minecraft", f"**`{serv.get('server_name')}`**", True),
                ("Kênh Discord", channel.mention, True)
            ]
        )
        await ctx.send(embed=embed)

    @mc.command(name="setlog", description="Cài đặt kênh nhận thông báo sự kiện Minecraft (Join, Quit, Thành tựu, Death).")
    @commands.guild_only()
    @commands.has_permissions(administrator=True)
    async def set_log_cmd(self, ctx: commands.Context, channel: discord.TextChannel):
        serv = await get_mc_server_by_guild(ctx.guild.id)
        if not serv:
            embed = make_mc_embed(
                title="⚠️ Chưa Liên Kết Máy Chủ",
                description=f"Server Discord này chưa nối với máy chủ Minecraft nào!\nDùng `{ctx.prefix}mc linkserver <code>` trước.",
                color=MC_ORANGE
            )
            return await ctx.send(embed=embed, ephemeral=True)

        await update_mc_server_channels(serv["server_key"], log_channel_id=str(channel.id))
        embed = make_mc_embed(
            title="📢 Cài Đặt Kênh Sự Kiện (Log)",
            description=f"Đã đặt kênh {channel.mention} làm kênh nhận thông báo sự kiện (Join, Quit, Thành tựu, Death) từ Minecraft!",
            color=MC_GREEN,
            fields=[
                ("Máy chủ Minecraft", f"**`{serv.get('server_name')}`**", True),
                ("Kênh nhận thông báo", channel.mention, True)
            ]
        )
        await ctx.send(embed=embed)

    @mc.command(name="cmd", aliases=["console"], description="Gửi lệnh console tới server Minecraft đã liên kết (Chỉ Quản lý Guild).")
    @commands.guild_only()
    async def cmd_server_cmd(self, ctx: commands.Context, *, lenh: str):
        # Yêu cầu chỉ có người quản lý của guild đấy mới có quyền thao tác gửi lệnh
        if not (ctx.author.id == ctx.guild.owner_id or ctx.author.guild_permissions.administrator or ctx.author.guild_permissions.manage_guild):
            embed = make_mc_embed(
                title="⛔ Quyền Hạn Bị Từ Chối",
                description="Chỉ người quản lý hoặc Administrator của Server này mới có quyền thao tác gửi lệnh Minecraft!",
                color=MC_RED
            )
            return await ctx.send(embed=embed, ephemeral=True)

        serv = await get_mc_server_by_guild(ctx.guild.id)
        if not serv:
            embed = make_mc_embed(
                title="⚠️ Chưa Liên Kết Máy Chủ",
                description=f"Server Discord này chưa nối với máy chủ Minecraft nào.\nDùng `{ctx.prefix}mc linkserver <code>` để kết nối trước!",
                color=MC_ORANGE
            )
            return await ctx.send(embed=embed, ephemeral=True)

        clean_cmd = lenh.strip().lstrip("/")
        await queue_mc_command(serv["server_key"], clean_cmd, f"{ctx.author.name} (ID: {ctx.author.id})")

        # RCON fallback nếu có
        rcon_resp = ""
        try:
            rcon_resp = await self.execute_rcon_command(clean_cmd)
        except Exception:
            pass

        embed = make_mc_embed(
            title=f"🕹️ Console Lệnh: {serv.get('server_name')}",
            description=f"Thực thi bởi {ctx.author.mention}",
            color=MC_DARK,
            fields=[
                ("📥 Lệnh đã gửi", f"```yaml\n/{clean_cmd}```", False),
                ("📤 Phản hồi / Trạng thái", f"```fix\n{rcon_resp}```" if (rcon_resp and "Lỗi" not in rcon_resp) else "⏳ Lệnh đã được đưa vào hàng đợi console của Plugin Minecraft và sẽ thực thi ngay lập tức!", False)
            ],
            footer="Sakura Minecraft Server Console"
        )
        await ctx.send(embed=embed, ephemeral=True)

    @mc.command(name="account", aliases=["profile", "mylink", "statuslink", "me"], description="Xem trạng thái liên kết tài khoản Minecraft của bạn hoặc người khác.")
    async def account_status_cmd(self, ctx: commands.Context, member: discord.Member = None):
        target = member or ctx.author
        from data.database import get_mc_user_link, get_user_data
        link = await get_mc_user_link(target.id)

        u_data = await get_user_data(0, target.id)
        d_coins = int(u_data.get("coins", 0))

        if not link:
            embed = make_mc_embed(
                title="🎮 TRẠNG THÁI LIÊN KẾT MINECRAFT",
                description=f"Tài khoản {target.mention} **chưa liên kết** với nhân vật Minecraft nào!",
                color=MC_RED,
                fields=[
                    ("📌 Trạng Thái", "❌ **CHƯA LIÊN KẾT**", True),
                    ("🆔 Discord ID", f"`{target.id}`", True),
                    ("💰 Discord Coins", f"**`{d_coins:,}`** coins", True),
                    ("📖 Hướng Dẫn Liên Kết", 
                     f"**Bước 1:** Vào server Minecraft gõ lệnh `/discord link` để nhận mã 6 ký tự.\n"
                     f"**Bước 2:** Nhập mã tại Discord bằng lệnh: `{ctx.prefix}mc link <mã_code>`\n"
                     f"*(Hoặc liên kết trực tiếp bằng: `{ctx.prefix}mc link <tên_nhân_vật>`)*", False)
                ],
                footer=f"Yêu cầu bởi {ctx.author.name}"
            )
            return await ctx.send(embed=embed)

        mc_name = link.get("minecraft_name") or "Chưa rõ"
        mc_uuid = link.get("minecraft_uuid") or "—"
        mc_coins = int(link.get("mc_coins", 0))
        linked_at = link.get("linked_at")
        linked_time_str = f"<t:{int(linked_at)}:R>" if linked_at else "Đã liên kết"

        embed = make_mc_embed(
            title="🎮 THÔNG TIN LIÊN KẾT MINECRAFT",
            description=f"Hồ sơ liên kết tài khoản của {target.mention}:",
            color=MC_GREEN,
            player_name=mc_name,
            fields=[
                ("📌 Trạng Thái", "✅ **ĐÃ LIÊN KẾT**", True),
                ("👤 Nhân Vật In-game", f"**`{mc_name}`**", True),
                ("⏱️ Thời Gian Liên Kết", linked_time_str, True),
                ("🪙 Minecraft Coins", f"**`{mc_coins:,}`** MC Coins", True),
                ("💰 Discord Coins", f"**`{d_coins:,}`** coins", True),
                ("📊 Tỉ Giá Chuyển Đổi", f"**1 MC Coin = {MC_COIN_RATE:,} Discord Coins**", True),
                ("🛠️ Lệnh Tiện Ích", 
                 f"• Chuyển tiền vào game: `{ctx.prefix}mc coins to_mc <số>`\n"
                 f"• Rút tiền về Discord: `{ctx.prefix}mc coins to_discord <số>`\n"
                 f"• Hủy liên kết: `{ctx.prefix}mc unlink`", False)
            ],
            footer=f"Yêu cầu bởi {ctx.author.name}"
        )
        await ctx.send(embed=embed)

    @mc.command(name="unlink", description="Hủy liên kết tài khoản Minecraft của bạn.")
    async def unlink_player_cmd(self, ctx: commands.Context):
        from data.database import get_mc_user_link, unlink_mc_user
        link = await get_mc_user_link(ctx.author.id)
        if not link:
            embed = make_mc_embed(
                title="⚠️ Chưa Có Liên Kết",
                description="Bạn chưa liên kết tài khoản Discord này với bất kỳ nhân vật Minecraft nào!",
                color=MC_RED
            )
            return await ctx.send(embed=embed, ephemeral=True)

        mc_name = link.get("minecraft_name", "Minecraft")
        await unlink_mc_user(ctx.author.id)
        embed = make_mc_embed(
            title="🗑️ HỦY LIÊN KẾT THÀNH CÔNG",
            description=f"Đã hủy liên kết giữa tài khoản {ctx.author.mention} và nhân vật **`{mc_name}`**.\n"
                        f"Bạn có thể liên kết lại bất cứ lúc nào bằng lệnh `{ctx.prefix}mc link`!",
            color=MC_GOLD
        )
        await ctx.send(embed=embed)

    @mc.command(name="link", description="Liên kết tài khoản Discord của bạn với nhân vật Minecraft (để trống để xem trạng thái).")
    async def link_player_cmd(self, ctx: commands.Context, player_name_or_code: str = None):
        if not player_name_or_code:
            return await self.account_status_cmd(ctx)
        val = player_name_or_code.strip()
        # 1. Thử xác thực theo mã code liên kết (do /discord link in-game tạo)
        try:
            from data.database import link_mc_user_by_code
            db_res = await link_mc_user_by_code(val, ctx.author.id)
            if db_res.get("ok"):
                mc_name = db_res.get("player_name") or db_res.get("minecraft_name") or val
                embed = make_mc_embed(
                    title="🎉 LIÊN KẾT TÀI KHOẢN THÀNH CÔNG!",
                    description=f"Đã liên kết tài khoản Discord {ctx.author.mention} với nhân vật Minecraft **`{mc_name}`**!",
                    color=MC_GREEN,
                    player_name=mc_name,
                    fields=[
                        ("👤 Nhân vật Minecraft", f"**`{mc_name}`**", True),
                        ("🆔 Discord", ctx.author.mention, True),
                        ("🪙 Đồng bộ Coins", f"Dùng `{ctx.prefix}mc coins` để nạp/rút tiền giữa Discord và game!", False)
                    ]
                )
                return await ctx.send(embed=embed)
        except Exception:
            pass

        # Tra cứu mã liên kết PENDING_LINKS nếu có
        try:
            from mc_link_system import PENDING_LINKS
            pdata = PENDING_LINKS.get(val.upper())
            if pdata:
                PENDING_LINKS.pop(val.upper(), None)
                mc_name = pdata.get("minecraft_name", val)
                mc_uuid = pdata.get("minecraft_uuid", val.lower())
                await link_mc_user(ctx.author.id, mc_uuid, mc_name)
                embed = make_mc_embed(
                    title="🎉 LIÊN KẾT TÀI KHOẢN THÀNH CÔNG!",
                    description=f"Đã liên kết tài khoản Discord {ctx.author.mention} với nhân vật Minecraft **`{mc_name}`**!",
                    color=MC_GREEN,
                    player_name=mc_name,
                    fields=[
                        ("👤 Nhân vật Minecraft", f"**`{mc_name}`**", True),
                        ("🆔 Discord", ctx.author.mention, True),
                        ("🪙 Đồng bộ Coins", f"Dùng `{ctx.prefix}mc coins` để nạp/rút tiền giữa Discord và game!", False)
                    ]
                )
                return await ctx.send(embed=embed)
        except Exception:
            pass

        # Gán trực tiếp qua tên người chơi
        await link_mc_user(ctx.author.id, val.lower(), val)
        embed = make_mc_embed(
            title="✅ LIÊN KẾT TÀI KHOẢN THÀNH CÔNG!",
            description=f"Đã liên kết tài khoản Discord của bạn với nhân vật Minecraft **`{val}`**!",
            color=MC_GREEN,
            player_name=val,
            fields=[
                ("👤 Nhân vật Minecraft", f"**`{val}`**", True),
                ("🆔 Discord", ctx.author.mention, True),
                ("🪙 Đồng bộ Coins", f"Dùng `{ctx.prefix}mc coins` để kiểm tra ví và chuyển đổi tiền tệ!", False)
            ]
        )
        await ctx.send(embed=embed)

    @mc.command(name="coins", aliases=["sync"], description="Xem số dư và đồng bộ Coins giữa Discord và Minecraft (1 MC = 1,000 Discord Coins).")
    async def coins_sync_cmd(self, ctx: commands.Context, action: str = "balance", amount: int = 0):
        act = action.lower().strip()
        res = await sync_mc_user_coins(ctx.author.id, act, amount)
        if not res.get("ok"):
            embed = make_mc_embed(
                title="❌ Lỗi Đồng Bộ Coins",
                description=res.get("error", "Đã xảy ra lỗi không xác định."),
                color=MC_RED
            )
            return await ctx.send(embed=embed, ephemeral=True)

        mc_user = res.get("minecraft_name", "Chưa đặt")
        if act == "balance":
            embed = make_mc_embed(
                title="💎 Số Dư Coins Đồng Bộ Discord ⇋ Minecraft",
                description="Hệ thống ví tiền tệ liên kết giữa Discord Server và Server Minecraft:",
                color=MC_GOLD,
                player_name=mc_user if mc_user != "Chưa đặt" else None,
                fields=[
                    ("👤 Nhân vật Minecraft", f"`{mc_user}`", True),
                    ("🪙 Minecraft Coins", f"**`{res.get('mc_coins', 0):,}`** MC Coins", True),
                    ("💰 Discord Coins", f"**`{res.get('discord_coins', 0):,}`** coins", True),
                    ("📊 Tỉ giá quy đổi", f"**1 MC Coin = {MC_COIN_RATE:,} Discord Coins**", False)
                ],
                footer=f"Đổi sang game: '{ctx.prefix}mc coins to_mc <số>' | Rút về ví: '{ctx.prefix}mc coins to_discord <số>'"
            )
            return await ctx.send(embed=embed)

        embed = make_mc_embed(
            title="💎 Giao Dịch Coins Thành Công",
            description=f"🎉 **{res.get('message')}**",
            color=MC_GOLD,
            player_name=mc_user if mc_user != "Chưa đặt" else None,
            fields=[
                ("💰 Ví Discord", f"**`{res.get('discord_coins', 0):,}`** coin", True),
                ("🪙 Ví Minecraft", f"**`{res.get('mc_coins', 0):,}`** MC Coin", True),
                ("📊 Tỉ giá", f"1 MC Coin = {MC_COIN_RATE:,} Discord Coins", False)
            ]
        )
        await ctx.send(embed=embed)


async def setup(bot: commands.Bot):
    await bot.add_cog(MinecraftCog(bot))