import discord
from discord.ext import commands
from discord import app_commands
import asyncio
from typing import Optional
import json
import aiohttp
import os

# Import các hàm và biến cần thiết từ các file khác
from Checks_vi.mod import has_admin_role, admin_roles
from Checks_vi.i18n import t

# --- QUẢN LÝ CẤU HÌNH ---
REQUEST_ROLE_CONFIG_FILE = "data/request_role_config.json"

def load_request_role_config():
    if os.path.exists(REQUEST_ROLE_CONFIG_FILE):
        with open(REQUEST_ROLE_CONFIG_FILE, 'r', encoding='utf-8') as f:
            try: return json.load(f)
            except json.JSONDecodeError: return {}
    return {}

def save_request_role_config(data):
    os.makedirs(os.path.dirname(REQUEST_ROLE_CONFIG_FILE), exist_ok=True)
    with open(REQUEST_ROLE_CONFIG_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=4)

async def get_color_name(hex_code: str) -> str:
    """Lấy tên màu từ mã HEX bằng API thecolorapi.com."""
    if not hex_code:
        return t(None, "REQROLE_COLOR_DEFAULT")
    clean_hex = hex_code.lstrip('#')
    url = f"https://www.thecolorapi.com/id?hex={clean_hex}"
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                if response.status == 200:
                    data = await response.json()
                    return data.get("name", {}).get("value", hex_code.upper())
    except Exception:
        pass # Nếu API lỗi, trả về mã hex gốc
    return hex_code.upper()

# --- TỪ ĐIỂN MÀU TIẾNG VIỆT ---
VIETNAMESE_COLORS = {
    "đỏ": "#ff0000", "đỏ tươi": "#ff0000", "đỏ đậm": "#8b0000",
    "xanh lá": "#00ff00", "xanh lá cây": "#008000", "xanh đậm": "#00008b",
    "xanh dương": "#0000ff", "xanh da trời": "#87ceeb", "xanh lơ": "#00ffff", "xanh ngọc": "#40e0d0",
    "vàng": "#ffff00", "vàng chanh": "#fffacd", "vàng gold": "#ffd700",
    "tím": "#800080", "tím than": "#483d8b", "tím violet": "#ee82ee",
    "hồng": "#ffc0cb", "hồng phấn": "#ffb6c1", "hồng đậm": "#ff1493",
    "cam": "#ffa500",
    "đen": "#000000",
    "trắng": "#ffffff",
    "xám": "#808080", "xám tro": "#808080",
    "nâu": "#a52a2a",
}

def parse_color_input(color_input: str) -> discord.Color | None:
    """Phân tích đầu vào màu sắc, hỗ trợ HEX, tên tiếng Anh và tiếng Việt."""
    try: return discord.Color(int(color_input.lstrip('#'), 16)) # Thử HEX
    except ValueError:
        try: return discord.Color.from_str(color_input) # Thử tên tiếng Anh
        except ValueError:
            hex_from_vietnamese = VIETNAMESE_COLORS.get(color_input.lower())
            if hex_from_vietnamese:
                try: return discord.Color(int(hex_from_vietnamese.lstrip('#'), 16))
                except ValueError: return None
    return None

# --- MODAL (CỬA SỔ POPUP) ---

class RoleRequestModal(discord.ui.Modal, title="📝 Yêu Cầu Tạo Role Mới"):
    """Modal để người dùng nhập thông tin role họ muốn tạo."""
    role_name = discord.ui.TextInput(
        label="Tên Role bạn muốn tạo",
        placeholder="Ví dụ: Team A, Editor, VIP...",
        required=True,
        max_length=100
    )
    role_color = discord.ui.TextInput(
        label="Mã màu HEX (Tùy chọn)",
        placeholder="Ví dụ: #ffb6c1 (Mặc định: không màu)",
        required=False,
        max_length=7
    )
    hoist = discord.ui.TextInput(
        label="Hiển thị riêng biệt? (Có/Không)",
        placeholder="Nhập 'Có' để role hiện riêng trong danh sách thành viên",
        required=False,
        max_length=3
    )
    position_above = discord.ui.TextInput(
        label="Đặt role trên role cao nhất của bạn?",
        placeholder="Nhập 'Có' để role mới có vị trí cao hơn",
        required=False,
        max_length=3
    )
    reason = discord.ui.TextInput(
        label="Lý do yêu cầu (Tùy chọn)",
        style=discord.TextStyle.paragraph,
        placeholder="Mô tả ngắn gọn mục đích của role này...",
        required=False,
        max_length=500
    )

    def __init__(self, bot: commands.Bot):
        super().__init__()
        self.bot = bot

    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)

        # Lấy kênh đã được cấu hình để nhận yêu cầu
        guild_id_str = str(interaction.guild_id)
        config = load_request_role_config()
        guild_cfg = config.get(guild_id_str, {})
        request_channel_id = guild_cfg.get("approval_channel_id")

        # --- CẢI TIẾN: Xử lý và kiểm tra mã màu (HEX, tiếng Anh, tiếng Việt) ---
        embed_color = discord.Color.orange() # Màu mặc định cho embed
        role_color_input = self.role_color.value.strip() if self.role_color.value else None
        final_role_color_str_for_data = None # Biến để lưu mã hex chuẩn cho persistent_data

        if role_color_input:
            parsed_color = parse_color_input(role_color_input)
            if parsed_color:
                embed_color = parsed_color
                final_role_color_str_for_data = f"#{embed_color.value:06x}"
            else:
                return await interaction.followup.send(
                    t(interaction.guild, "REQROLE_INVALID_COLOR"),
                    ephemeral=True
                )

        # Nếu không có kênh duyệt thì tạo role ngay, không cần duyệt.
        if not request_channel_id:
            try:
                role_name = self.role_name.value.strip()
                hoist = self.hoist.value.lower() in ['yes', 'có', 'true', '1'] if self.hoist.value else False
                position_above = self.position_above.value.lower() in ['yes', 'có', 'true', '1'] if self.position_above.value else False
                color = discord.Color(int(final_role_color_str_for_data.lstrip('#'), 16)) if final_role_color_str_for_data else embed_color
                new_role = await interaction.guild.create_role(name=role_name, color=color, hoist=hoist, reason=f"Yêu cầu tự động tạo role bởi {interaction.user.name}")
                if position_above:
                    try:
                        target_position = interaction.user.top_role.position + 1 if interaction.user.top_role else 1
                        if target_position < interaction.guild.me.top_role.position:
                            await new_role.edit(position=target_position)
                    except Exception:
                        pass
                await interaction.user.add_roles(new_role)
                await interaction.followup.send(f"✅ Role `{role_name}` đã được tạo thành công cho bạn. {new_role.mention}", ephemeral=True)
                try:
                    await interaction.user.send(f"✅ Role `{role_name}` đã được tạo thành công trên server **{interaction.guild.name}**. {new_role.mention}")
                except Exception:
                    pass
                return
            except Exception as e:
                return await interaction.followup.send(t(interaction.guild, "REQROLE_APPROVE_ERROR", error=e), ephemeral=True)

        # Lấy tên màu từ API (sử dụng mã hex đã chuẩn hóa nếu có, nếu không thì dùng input gốc)
        color_name_str = await get_color_name(final_role_color_str_for_data or role_color_input)

        # Tạo embed yêu cầu để gửi cho admin
        embed = discord.Embed(
            title=t(interaction.guild, "REQROLE_NEW_REQUEST_TITLE"),
            description=t(interaction.guild, "REQROLE_NEW_REQUEST_DESC", mention=interaction.user.mention),
            color=embed_color,
            timestamp=discord.utils.utcnow()
        )
        embed.set_author(name=interaction.user.display_name, icon_url=interaction.user.display_avatar.url)
        embed.add_field(name=t(interaction.guild, "REQROLE_FIELD_REQUESTER"), value=f"{interaction.user.mention} (`{interaction.user.id}`)", inline=True)
        embed.add_field(name=t(interaction.guild, "REQROLE_FIELD_ROLE_NAME"), value=f"`{self.role_name.value}`", inline=True)
        embed.add_field(name=t(interaction.guild, "REQROLE_FIELD_COLOR"), value=f"`{color_name_str}`", inline=False)
        embed.add_field(name=t(interaction.guild, "REQROLE_FIELD_HOIST"), value=f"`{self.hoist.value or t(interaction.guild, 'REQROLE_COLOR_DEFAULT')}`", inline=True)
        embed.add_field(name=t(interaction.guild, "REQROLE_FIELD_POSITION"), value=f"`{self.position_above.value or t(interaction.guild, 'REQROLE_COLOR_DEFAULT')}`", inline=True)
        if self.reason.value:
            embed.add_field(name=t(interaction.guild, "REQROLE_FIELD_REASON"), value=self.reason.value, inline=False)

        # Thêm một trường ẩn để lưu trữ tất cả dữ liệu cần thiết cho persistent view
        # Dữ liệu này sẽ được phân tích lại khi nút Duyệt/Từ chối được nhấn
        persistent_data = {
            "requester_id": interaction.user.id,
            "role_name": self.role_name.value.strip(),
            "role_color_str": final_role_color_str_for_data,
            "hoist_str": self.hoist.value,
            "position_above_str": self.position_above.value
        }
        embed.add_field(name="persistent_data", value=json.dumps(persistent_data), inline=False)

        # Chuẩn bị view với các nút duyệt/từ chối
        view = AdminApprovalView(bot=self.bot)

        # Gửi yêu cầu đến kênh đã cấu hình
        try:
            request_channel = self.bot.get_channel(request_channel_id) or await self.bot.fetch_channel(request_channel_id)
            if not request_channel.permissions_for(interaction.guild.me).send_messages:
                return await interaction.followup.send(t(interaction.guild, "REQROLE_NO_PERM_CHANNEL", mention=request_channel.mention), ephemeral=True)
            
            await request_channel.send(embed=embed, view=view)
            await interaction.followup.send(t(interaction.guild, "REQROLE_SENT"), ephemeral=True)
        except discord.NotFound:
            await interaction.followup.send(t(interaction.guild, "REQROLE_CHANNEL_NOT_FOUND"), ephemeral=True)
        except discord.Forbidden:
            await interaction.followup.send(t(interaction.guild, "REQROLE_NO_PERM_SEND"), ephemeral=True)
        except Exception as e:
            await interaction.followup.send(t(interaction.guild, "REQROLE_SEND_ERROR", error=e), ephemeral=True)


class DenyReasonModal(discord.ui.Modal, title="📝 Lý Do Từ Chối"):
    def __init__(self, bot: commands.Bot, requester: discord.Member, role_name: str, original_message: discord.Message):
        super().__init__()
        self.bot = bot
        self.requester = requester
        self.role_name = role_name
        self.original_message = original_message # Lưu tin nhắn gốc để cập nhật

    reason = discord.ui.TextInput(
        label="Nhập lý do từ chối yêu cầu",
        style=discord.TextStyle.paragraph,
        required=True,
        max_length=500
    )
    async def on_submit(self, interaction: discord.Interaction):
        # Phản hồi tương tác modal trước
        await interaction.response.defer()

        # Gửi thông báo từ chối cho người dùng gốc
        await self.requester.send(t(interaction.guild, "REQROLE_DENY_DM", name=self.role_name, reason=self.reason.value))
        
        # Lấy embed từ tin nhắn gốc và cập nhật nó
        embed = self.original_message.embeds[0]
        embed.title = t(interaction.guild, "REQROLE_DENIED_TITLE")
        embed.color = discord.Color.red()
        embed.remove_field(embed.fields.index(next(f for f in embed.fields if f.name == "persistent_data"))) # Xóa trường ẩn
        embed.clear_fields() # Xóa các field cũ
        embed.add_field(name=t(interaction.guild, "REQROLE_FIELD_APPROVER"), value=interaction.user.mention, inline=False)
        embed.add_field(name=t(interaction.guild, "REQROLE_FIELD_DENY_REASON"), value=self.reason.value, inline=False)
        
        # Vô hiệu hóa các nút trên tin nhắn gốc và cập nhật nó
        self.view.stop() # Dừng view cũ
        for item in self.view.children: item.disabled = True
        await self.original_message.edit(embed=embed, view=self.view)


# --- VIEW (BỘ NÚT BẤM) ---

class AdminApprovalView(discord.ui.View):
    """View chứa nút Duyệt/Từ chối cho admin."""
    def __init__(self, bot: commands.Bot):
        super().__init__(timeout=None) # Đặt timeout=None để view không hết hạn
        self.bot = bot
        # Các thuộc tính này sẽ được lấy từ embed khi nút được nhấn
        self.requester: Optional[discord.Member] = None
        self.role_name: Optional[str] = None
        self.role_color_str: Optional[str] = None
        self.hoist_str: Optional[str] = None
        self.position_above_str: Optional[str] = None

    async def _extract_data_from_embed(self, embed: discord.Embed, guild: discord.Guild):
        """Trích xuất dữ liệu cần thiết từ embed."""
        persistent_data_field = next((f for f in embed.fields if f.name == "persistent_data"), None)
        if not persistent_data_field:
            raise ValueError("Không tìm thấy dữ liệu yêu cầu trong embed.")
        
        data = json.loads(persistent_data_field.value)
        self.requester = guild.get_member(data.get("requester_id")) or await guild.fetch_member(data.get("requester_id"))
        
        self.role_name = data.get("role_name")
        self.role_color_str = data.get("role_color_str")
        self.hoist_str = data.get("hoist_str")
        self.position_above_str = data.get("position_above_str")
    
    @discord.ui.button(label="Duyệt", style=discord.ButtonStyle.success, emoji="✅", custom_id="request_role:approve")
    async def approve(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer() # Defer để có thời gian xử lý

        # Trích xuất dữ liệu từ embed
        try:
            await self._extract_data_from_embed(interaction.message.embeds[0], interaction.guild)
        except (ValueError, json.JSONDecodeError, KeyError) as e:
            return await interaction.followup.send(t(interaction.guild, "REQROLE_DATA_ERROR", error=e), ephemeral=True)
        
        if not self.requester:
            return await interaction.followup.send(t(interaction.guild, "REQROLE_NOT_FOUND"), ephemeral=True)


        # Xử lý màu
        role_color = discord.Color.default()
        if self.role_color_str:
            try:
                role_color = discord.Color(int(self.role_color_str.lstrip('#'), 16))
            except ValueError:
                await interaction.followup.send(t(interaction.guild, "REQROLE_COLOR_FALLBACK"), ephemeral=True)

        # Xử lý hoist
        hoist = self.hoist_str.lower() in ['yes', 'có', 'true', '1'] if self.hoist_str else False
        
        # Xử lý vị trí
        position_above = self.position_above_str.lower() in ['yes', 'có', 'true', '1'] if self.position_above_str else False

        try:
            # Tạo role
            new_role = await interaction.guild.create_role(
                name=self.role_name,
                color=role_color,
                hoist=hoist,
                reason=f"Yêu cầu bởi {self.requester.name}, duyệt bởi {interaction.user.name}"
            )

            # Xử lý vị trí của role nếu được yêu cầu
            position_message = ""
            if position_above:
                try:
                    # Vị trí mục tiêu là ngay trên role cao nhất của người yêu cầu
                    target_position = self.requester.top_role.position + 1
                    # Đảm bảo không đặt role cao hơn bot
                    if target_position < interaction.guild.me.top_role.position:
                        await new_role.edit(position=target_position)
                        position_message = t(interaction.guild, "REQROLE_POSITION_MOVED", mention=self.requester.top_role.mention)
                    else:
                        position_message = t(interaction.guild, "REQROLE_POSITION_BLOCKED")
                except Exception as pos_e:
                    position_message = t(interaction.guild, "REQROLE_POSITION_ERROR", error=pos_e)

            # Gán role cho người yêu cầu
            await self.requester.add_roles(new_role)

            # Cập nhật tin nhắn của admin
            embed = interaction.message.embeds[0]
            embed.title = t(interaction.guild, "REQROLE_APPROVED_TITLE")
            embed.remove_field(embed.fields.index(next(f for f in embed.fields if f.name == "persistent_data"))) # Xóa trường ẩn
            embed.color = discord.Color.green()
            embed.clear_fields() # Xóa các field cũ
            embed.add_field(name=t(interaction.guild, "REQROLE_FIELD_APPROVER"), value=interaction.user.mention, inline=False)
            embed.add_field(name=t(interaction.guild, "REQROLE_CREATED_ROLE"), value=new_role.mention, inline=False)
            
            # Vô hiệu hóa các nút và cập nhật tin nhắn
            for item in self.children:
                item.disabled = True
            await interaction.edit_original_response(embed=embed, view=self)

            # Gửi DM cho người yêu cầu
            await self.requester.send(t(interaction.guild, "REQROLE_ASSIGN_SUCCESS_DM", name=self.role_name, extra=position_message))

        except discord.Forbidden:
            await interaction.followup.send(t(interaction.guild, "REQROLE_MANAGE_NO_PERM"), ephemeral=True)
        except Exception as e:
            await interaction.followup.send(t(interaction.guild, "REQROLE_APPROVE_ERROR", error=e), ephemeral=True)

    @discord.ui.button(label="Từ chối", style=discord.ButtonStyle.danger, emoji="🚫", custom_id="request_role:deny")
    async def deny(self, interaction: discord.Interaction, button: discord.ui.Button):
        # Trích xuất dữ liệu từ embed
        try:
            await self._extract_data_from_embed(interaction.message.embeds[0], interaction.guild)
        except (ValueError, json.JSONDecodeError, KeyError) as e:
            return await interaction.followup.send(t(interaction.guild, "REQROLE_DATA_ERROR", error=e), ephemeral=True)
        
        if not self.requester:
            return await interaction.followup.send(t(interaction.guild, "REQROLE_NOT_FOUND"), ephemeral=True)

        # Mở modal để admin nhập lý do từ chối
        modal = DenyReasonModal(self.bot, self.requester, self.role_name, interaction.message)
        modal.view = self # Truyền view vào modal để nó có thể vô hiệu hóa nút
        await interaction.response.send_modal(modal)


class RequestRoleView(discord.ui.View):
    """View chứa nút bấm ban đầu để người dùng bắt đầu yêu cầu."""
    def __init__(self, bot: commands.Bot):
        super().__init__(timeout=None) # Nút không bao giờ hết hạn
        self.bot = bot

    @discord.ui.button(label="Tạo Yêu Cầu Role", style=discord.ButtonStyle.primary, emoji="✨", custom_id="request_role_button")
    async def request_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(RoleRequestModal(self.bot))


# --- COG CHÍNH ---

class RoleRequestCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    async def cog_load(self):
        """Đăng ký view persistent khi cog được nạp."""
        self.bot.add_view(RequestRoleView(self.bot))
        self.bot.add_view(AdminApprovalView(self.bot)) # Đăng ký AdminApprovalView
        # Thay vào đó, chúng ta sẽ xử lý nó thông qua custom_id.
        print("✅ Đã nạp View của hệ thống Request Role (Panel).")

    @commands.hybrid_group(name="requestrole", description="Hệ thống yêu cầu tạo role mới.")
    async def request_role_group(self, ctx: commands.Context):
        """Lệnh gốc cho nhóm requestrole."""
        if ctx.invoked_subcommand is None:
            await ctx.send_help(ctx.command)

    async def _send_panel_to_channel(self, channel: discord.TextChannel, author: discord.Member):
        """Hàm trợ giúp nội bộ để gửi bảng điều khiển yêu cầu role đến một kênh."""
        panel_embed = discord.Embed(
            title=t(channel.guild, "REQROLE_PANEL_TITLE"),
            description=t(channel.guild, "REQROLE_PANEL_DESC"),
            color=discord.Color.blurple()
        )
        panel_embed.set_footer(text=t(channel.guild, "REQROLE_PANEL_FOOTER"))
        
        try:
            await channel.send(embed=panel_embed, view=RequestRoleView(self.bot))
            return True, None # Trả về True và không có lỗi
        except Exception as e:
            return False, t(channel.guild, "REQROLE_PANEL_SEND_ERROR", error=e)

    @request_role_group.command(name="setup", description="[Admin] Cài đặt kênh đặt bảng điều khiển và kênh duyệt yêu cầu.")
    @app_commands.describe(
        panel_channel="Kênh để đặt bảng điều khiển (sẽ bị khóa chat).",
        approval_channel="Kênh để quản trị viên nhận và duyệt yêu cầu. Bỏ trống nếu không cần duyệt."
    )
    @has_admin_role()
    async def setup(self, ctx: commands.Context, panel_channel: discord.TextChannel, approval_channel: discord.TextChannel = None):
        """Cài đặt kênh panel và kênh duyệt cho hệ thống yêu cầu role. Nếu không có kênh duyệt thì không cần duyệt."""
        await ctx.defer(ephemeral=True)

        # Lưu cấu hình
        config = load_request_role_config()
        guild_cfg = {
            "panel_channel_id": panel_channel.id,
        }
        if approval_channel is not None:
            guild_cfg["approval_channel_id"] = approval_channel.id
        config[str(ctx.guild.id)] = guild_cfg
        save_request_role_config(config)

        # Tự động khóa chat trong kênh panel
        try:
            everyone_role = ctx.guild.default_role
            await panel_channel.set_permissions(everyone_role, send_messages=False, reason="Thiết lập kênh panel cho Request Role")
            permission_status = t(ctx.guild, "REQROLE_PERM_LOCKED", mention=panel_channel.mention)
        except discord.Forbidden:
            permission_status = t(ctx.guild, "REQROLE_PERM_NO_PERM", mention=panel_channel.mention)
        except Exception as e:
            permission_status = t(ctx.guild, "REQROLE_PERM_ERROR", mention=panel_channel.mention, error=e)

        panel_status = ""
        success, error_msg = await self._send_panel_to_channel(panel_channel, ctx.author)
        if success:
            panel_status = t(ctx.guild, "REQROLE_PANEL_SENT", mention=panel_channel.mention)
        else:
            panel_status = t(ctx.guild, "REQROLE_PANEL_SEND_ERROR", error=error_msg)

        approval_text = approval_channel.mention if approval_channel else "Không cần duyệt"
        await ctx.send(
            t(ctx.guild, "REQROLE_SETUP_SUCCESS", panel_mention=panel_channel.mention, approval_mention=approval_text, perm_status=permission_status, panel_status=panel_status),
            ephemeral=True
        )

    @request_role_group.command(name="panel", description="[Admin] Gửi lại bảng điều khiển yêu cầu role (nếu bị trôi).")
    @has_admin_role()
    async def panel(self, ctx: commands.Context):
        """Hiển thị một bảng điều khiển cho phép người dùng yêu cầu tạo role."""
        await ctx.defer(ephemeral=True)
        guild_id_str = str(ctx.guild.id)
        config = load_request_role_config()
        panel_channel_id = config.get(guild_id_str, {}).get("panel_channel_id")

        if not panel_channel_id:
            return await ctx.send(t(ctx.guild, "REQROLE_NEED_SETUP"), ephemeral=True)

        panel_channel = self.bot.get_channel(panel_channel_id)
        if not panel_channel:
            return await ctx.send(t(ctx.guild, "REQROLE_PANEL_CHANNEL_NOT_FOUND"), ephemeral=True)

        success, error_msg = await self._send_panel_to_channel(panel_channel, ctx.author)
        if success:
            await ctx.send(t(ctx.guild, "REQROLE_PANEL_RESENT", mention=panel_channel.mention), ephemeral=True)
        else:
            await ctx.send(t(ctx.guild, "REQROLE_PANEL_RESEND_ERROR", error=error_msg), ephemeral=True)

async def setup(bot: commands.Bot):
    await bot.add_cog(RoleRequestCog(bot))
