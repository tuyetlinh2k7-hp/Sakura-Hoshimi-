import io
import re
import random
import asyncio
import discord
from discord.ext import commands
from discord import app_commands
from typing import Optional, Literal

from config import OWNER_ID
from Check.mod import admin_roles, save_admin_roles, has_admin_role
from Check.i18n import t

# Danh sách 28 quyền quan trọng dùng cho quản lý và autocomplete
PERMS_LIST = [
    "administrator", "manage_guild", "manage_channels", "manage_roles",
    "manage_messages", "kick_members", "ban_members", "mention_everyone",
    "manage_nicknames", "mute_members", "deafen_members", "move_members",
    "manage_webhooks", "manage_emojis", "view_audit_log", "manage_threads",
    "create_public_threads", "create_private_threads", "moderate_members",
    "send_messages", "embed_links", "attach_files", "read_message_history",
    "use_external_emojis", "add_reactions", "connect", "speak", "stream"
]

# Các quyền nhạy cảm cần đánh dấu cảnh báo bảo mật
DANGEROUS_PERMS = {
    "administrator", "manage_guild", "manage_roles", "manage_channels",
    "ban_members", "kick_members", "manage_webhooks", "mention_everyone",
    "manage_messages", "moderate_members"
}

# Bảng màu gợi ý (Color Presets) cho Autocomplete
COLOR_PRESETS = {
    "🌸 Hồng Sakura (#FFB7C5)": "#FFB7C5",
    "💎 Xanh Ngọc Bích (#00FFCC)": "#00FFCC",
    "🔥 Đỏ Rực Lửa (#FF4500)": "#FF4500",
    "👑 Vàng Hoàng Gia (#FFD700)": "#FFD700",
    "💜 Tím Ngân Hà (#9B59B6)": "#9B59B6",
    "💙 Xanh Dương Sáng (#3498DB)": "#3498DB",
    "🍀 Xanh Lá Ngọc (#2ECC71)": "#2ECC71",
    "🌙 Đen Tuyền (#010101)": "#010101",
    "☁️ Trắng Tinh Khôi (#FFFFFF)": "#FFFFFF",
    "🎲 Ngẫu nhiên (Random)": "random",
    "🔄 Mặc định / Xóa màu (Reset)": "reset"
}


# =========================================================================
# CÁC HÀM PHỤ TRỢ (HELPER FUNCTIONS)
# =========================================================================

def parse_Color(color_str: Optional[str]) -> Optional[discord.Color]:
    """Chuyển đổi chuỗi mã HEX, tên màu, hoặc preset thành discord.Color."""
    if not color_str:
        return discord.Color.default()

    val = color_str.strip().lower()
    if val in ("reset", "default", "none", "clear"):
        return discord.Color.default()
    if val == "random":
        return discord.Color(random.randint(0, 0xFFFFFF))

    clean_hex = val.replace("#", "")
    try:
        return discord.Color(int(clean_hex, 16))
    except ValueError:
        try:
            return discord.Color.from_str(color_str.strip())
        except ValueError:
            return None


def parse_duration(duration_str: str) -> Optional[int]:
    """Chuyển đổi chuỗi thời gian (vd: 30s, 15m, 2h, 7d) sang tổng số giây."""
    pattern = re.compile(r"(\d+)\s*([smhd])", re.IGNORECASE)
    matches = pattern.findall(duration_str)
    if not matches:
        return None

    unit_map = {"s": 1, "m": 60, "h": 3600, "d": 86400}
    total_seconds = sum(int(amount) * unit_map[unit.lower()] for amount, unit in matches)
    return total_seconds if total_seconds > 0 else None


def format_duration_vi(seconds: int) -> str:
    days, rem = divmod(seconds, 86400)
    hours, rem = divmod(rem, 3600)
    minutes, secs = divmod(rem, 60)
    parts = []
    if days:
        parts.append(f"{days} ngày")
    if hours:
        parts.append(f"{hours} giờ")
    if minutes:
        parts.append(f"{minutes} phút")
    if secs:
        parts.append(f"{secs} giây")
    return " ".join(parts)


def check_role_hierarchy(
    guild: discord.Guild,
    author: discord.Member | discord.User,
    role: discord.Role,
    check_managed: bool = True
) -> Optional[str]:
    """
    Kiểm tra an toàn phân cấp Role trước khi chỉnh sửa / cấp / xóa.
    Trả về chuỗi báo lỗi nếu không hợp lệ, hoặc None nếu an toàn.
    """
    if role.is_default():
        return "⚠️ Không thể thực hiện thao tác này lên Role mặc định `@everyone`!"

    if check_managed and role.managed:
        return f"⚠️ {role.mention} là **Role hệ thống** (Bot/Booster/Tích hợp), không thể cấp hoặc xóa thủ công!"

    if role >= guild.me.top_role:
        return t(guild, "ROLE_HIGHER_THAN_BOT")

    if isinstance(author, discord.Member):
        if author.id != guild.owner_id and author.id != OWNER_ID:
            if role >= author.top_role:
                return "⛔ Bạn không thể tác động lên một Role **cao hơn hoặc ngang bằng** với Role cao nhất của chính bạn!"

    return None


def build_permissions_embed(role: discord.Role, author: discord.abc.User) -> discord.Embed:
    """Tạo Embed hiển thị danh sách quyền (có đánh dấu ⚠️ cho các quyền nhạy cảm)."""
    guild = role.guild
    embed = discord.Embed(
        title=t(guild, "ROLEINFO_PERMS_TITLE", name=role.name),
        color=role.color if role.color != discord.Color.default() else discord.Color.gold(),
        timestamp=discord.utils.utcnow()
    )

    enabled_perms = []
    disabled_perms = []

    for perm_name, is_enabled in iter(role.permissions):
        label = perm_name.replace("_", " ").title()
        if perm_name in DANGEROUS_PERMS:
            label = f"⚠️ **{label}** (`{perm_name}`)"
        else:
            label = f"• {label} (`{perm_name}`)"

        if is_enabled:
            enabled_perms.append(label)
        elif perm_name in PERMS_LIST:
            disabled_perms.append(f"• {perm_name.replace('_', ' ').title()}")

    if enabled_perms:
        embed.add_field(
            name=f"✅ {t(guild, 'ROLEINFO_PERMS_ENABLED')} ({len(enabled_perms)})",
            value="\n".join(enabled_perms)[:1024],
            inline=False
        )
    else:
        embed.add_field(
            name=f"✅ {t(guild, 'ROLEINFO_PERMS_ENABLED')}",
            value="*(Không có quyền nào được bật)*",
            inline=False
        )

    if disabled_perms:
        embed.add_field(
            name=f"❌ {t(guild, 'ROLEINFO_PERMS_DISABLED')} ({len(disabled_perms)})",
            value=", ".join(disabled_perms)[:1024],
            inline=False
        )

    embed.set_footer(
        text=f"{t(guild, 'ROLEINFO_FOOTER_REQUESTED', name=author.display_name)} | ⚠️ = Quyền quản trị nhạy cảm",
        icon_url=author.display_avatar.url
    )
    return embed


# =========================================================================
# CÁC GIAO DIỆN TƯƠNG TÁC (DISCORD UI VIEWS)
# =========================================================================

class ConfirmDeleteRoleView(discord.ui.View):
    """Hộp thoại xác nhận trước khi xóa vĩnh viễn 1 Role."""
    def __init__(self, author: discord.Member, role: discord.Role):
        super().__init__(timeout=60)
        self.author = author
        self.role = role

    @discord.ui.button(label="Xác nhận xóa", style=discord.ButtonStyle.danger, emoji="🗑️")
    async def confirm_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.author.id:
            return await interaction.response.send_message(t(interaction.guild, "ROLEINFO_VIEW_NOT_YOURS"), ephemeral=True)

        err = check_role_hierarchy(interaction.guild, interaction.user, self.role)
        if err:
            return await interaction.response.edit_message(content=err, embed=None, view=None)

        role_name = self.role.name
        role_id = self.role.id
        try:
            await self.role.delete(reason=f"Deleted by {interaction.user}")
            embed = discord.Embed(
                title=t(interaction.guild, "ROLE_DELETE_SUCCESS_TITLE"),
                color=discord.Color.red(),
                timestamp=discord.utils.utcnow()
            )
            embed.add_field(name=t(interaction.guild, "ROLE_DELETE_FIELD_OLD"), value=f"`{role_name}`", inline=True)
            embed.add_field(name=t(interaction.guild, "ROLE_FIELD_ID"), value=f"`{role_id}`", inline=True)
            embed.set_footer(text=t(interaction.guild, "ROLE_FOOTER_BY", name=interaction.user))
            await interaction.response.edit_message(content=None, embed=embed, view=None)
        except discord.Forbidden:
            await interaction.response.edit_message(content=t(interaction.guild, "ROLE_DELETE_BOT_NO_PERM"), embed=None, view=None)
        except Exception as e:
            await interaction.response.edit_message(content=t(interaction.guild, "ROLE_ERROR_GENERIC2", error=e), embed=None, view=None)

    @discord.ui.button(label="Hủy bỏ", style=discord.ButtonStyle.secondary, emoji="✖️")
    async def cancel_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.author.id:
            return await interaction.response.send_message(t(interaction.guild, "ROLEINFO_VIEW_NOT_YOURS"), ephemeral=True)
        await interaction.response.edit_message(content="✅ Đã hủy thao tác xóa Role.", embed=None, view=None)


class PermissionEditView(discord.ui.View):
    """Giao diện bật/tắt nhiều quyền cùng lúc + Cấp/Xóa toàn bộ quyền."""
    def __init__(self, author: discord.Member, role: discord.Role):
        super().__init__(timeout=180)
        self.author = author
        self.role = role
        self.update_components()

    def update_components(self):
        self.clear_items()
        guild = self.role.guild

        current_perms = dict(iter(self.role.permissions))
        enabled_perms = sorted([p for p, v in current_perms.items() if v and p in PERMS_LIST])
        disabled_perms = sorted([p for p in PERMS_LIST if not current_perms.get(p, False)])

        # Menu chọn bật nhiều quyền cùng lúc
        if disabled_perms:
            enable_opts = [
                discord.SelectOption(
                    label=p.replace("_", " ").title(),
                    value=p,
                    emoji="⚠️" if p in DANGEROUS_PERMS else "➕"
                )
                for p in disabled_perms[:25]
            ]
            enable_sel = discord.ui.Select(
                placeholder=t(guild, "ROLEINFO_PERM_ENABLE_PLACEHOLDER"),
                options=enable_opts,
                min_values=1,
                max_values=len(enable_opts),
                custom_id="perm_enable_select",
                row=0
            )
            enable_sel.callback = self.handle_selection
            self.add_item(enable_sel)

        # Menu chọn tắt nhiều quyền cùng lúc
        if enabled_perms:
            disable_opts = [
                discord.SelectOption(
                    label=p.replace("_", " ").title(),
                    value=p,
                    emoji="➖"
                )
                for p in enabled_perms[:25]
            ]
            disable_sel = discord.ui.Select(
                placeholder=t(guild, "ROLEINFO_PERM_DISABLE_PLACEHOLDER"),
                options=disable_opts,
                min_values=1,
                max_values=len(disable_opts),
                custom_id="perm_disable_select",
                row=1
            )
            disable_sel.callback = self.handle_selection
            self.add_item(disable_sel)

        # Nút Cấp tất cả & Xóa tất cả
        btn_all = discord.ui.Button(label="⚡ Cấp toàn bộ (All)", style=discord.ButtonStyle.success, row=2)
        btn_all.callback = self.grant_all_perms
        self.add_item(btn_all)

        btn_none = discord.ui.Button(label="🚫 Xóa toàn bộ (None)", style=discord.ButtonStyle.danger, row=2)
        btn_none.callback = self.clear_all_perms
        self.add_item(btn_none)

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id != self.author.id:
            await interaction.response.send_message(t(interaction.guild, "ROLEINFO_VIEW_NOT_YOURS"), ephemeral=True)
            return False
        if not interaction.user.guild_permissions.manage_roles and interaction.user.id != OWNER_ID:
            await interaction.response.send_message(t(interaction.guild, "ROLEINFO_VIEW_NEED_MANAGE"), ephemeral=True)
            return False
        err = check_role_hierarchy(interaction.guild, interaction.user, self.role, check_managed=False)
        if err:
            await interaction.response.send_message(err, ephemeral=True)
            return False
        return True

    async def handle_selection(self, interaction: discord.Interaction):
        await interaction.response.defer()
        selected_perms: list[str] = interaction.data["values"]
        is_enabling = interaction.data["custom_id"] == "perm_enable_select"

        try:
            current_perms = dict(iter(self.role.permissions))
            for p in selected_perms:
                # Chỉ người có quyền Administrator mới được bật quyền administrator cho Role
                if p == "administrator" and is_enabling and not interaction.user.guild_permissions.administrator:
                    continue
                current_perms[p] = is_enabling

            await self.role.edit(
                permissions=discord.Permissions(**current_perms),
                reason=f"Updated permissions by {interaction.user}"
            )

            action_text = t(interaction.guild, "ROLEINFO_PERM_ACTION_ON") if is_enabling else t(interaction.guild, "ROLEINFO_PERM_ACTION_OFF")
            perms_formatted = ", ".join(f"`{p}`" for p in selected_perms)
            msg = t(interaction.guild, "ROLEINFO_PERM_TOGGLE_DONE", action=action_text, perm=perms_formatted)

            self.update_components()
            new_embed = build_permissions_embed(self.role, self.author)
            await interaction.edit_original_response(content=msg, embed=new_embed, view=self)
        except discord.Forbidden:
            await interaction.followup.send(t(interaction.guild, "ROLEINFO_BOT_NO_PERM"), ephemeral=True)
        except Exception as e:
            await interaction.followup.send(t(interaction.guild, "ROLEINFO_ADD_ERROR", error=e), ephemeral=True)

    async def grant_all_perms(self, interaction: discord.Interaction):
        if not interaction.user.guild_permissions.administrator and interaction.user.id != OWNER_ID:
            return await interaction.response.send_message("⛔ Chỉ **Administrator** mới có thể cấp toàn bộ quyền!", ephemeral=True)

        await interaction.response.defer()
        try:
            await self.role.edit(permissions=discord.Permissions.all(), reason=f"Bulk ALL by {interaction.user}")
            self.update_components()
            new_embed = build_permissions_embed(self.role, self.author)
            await interaction.edit_original_response(
                content=t(interaction.guild, "ROLE_BULK_ALL", mention=self.role.mention),
                embed=new_embed,
                view=self
            )
        except Exception as e:
            await interaction.followup.send(t(interaction.guild, "ROLEINFO_ADD_ERROR", error=e), ephemeral=True)

    async def clear_all_perms(self, interaction: discord.Interaction):
        await interaction.response.defer()
        try:
            await self.role.edit(permissions=discord.Permissions.none(), reason=f"Bulk NONE by {interaction.user}")
            self.update_components()
            new_embed = build_permissions_embed(self.role, self.author)
            await interaction.edit_original_response(
                content=t(interaction.guild, "ROLE_BULK_NONE", mention=self.role.mention),
                embed=new_embed,
                view=self
            )
        except Exception as e:
            await interaction.followup.send(t(interaction.guild, "ROLEINFO_ADD_ERROR", error=e), ephemeral=True)


class MemberPaginatorView(discord.ui.View):
    """Phân trang danh sách thành viên trong Role (10 người/trang + Đầu/Cuối + Xuất file .txt)."""
    def __init__(self, author: discord.Member, role: discord.Role, members: list[discord.Member], items_per_page: int = 10):
        super().__init__(timeout=180)
        self.author = author
        self.role = role
        self.members = members
        self.items_per_page = items_per_page
        self.current_page = 0
        self.total_pages = max(1, (len(self.members) - 1) // self.items_per_page + 1)
        self.update_buttons()

    def create_page_embed(self) -> discord.Embed:
        guild = self.role.guild
        embed = discord.Embed(
            title=t(guild, "ROLEINFO_MEMBERS_TITLE", name=self.role.name),
            color=self.role.color if self.role.color != discord.Color.default() else discord.Color.green(),
            timestamp=discord.utils.utcnow()
        )

        start_idx = self.current_page * self.items_per_page
        page_members = self.members[start_idx : start_idx + self.items_per_page]

        lines = []
        for i, m in enumerate(page_members, start=start_idx + 1):
            joined_ts = f"<t:{int(m.joined_at.timestamp())}:R>" if m.joined_at else "Không rõ"
            bot_tag = " 🤖" if m.bot else ""
            lines.append(
                f"**{i}.** {m.mention}{bot_tag} (`{m.id}`)\n"
                f"   └ Tên: **{m.display_name}** • Tham gia: {joined_ts}"
            )

        embed.description = "\n".join(lines)
        if page_members:
            embed.set_thumbnail(url=page_members[0].display_avatar.url)

        embed.set_footer(
            text=t(guild, "ROLEINFO_MEMBERS_FOOTER", cur=self.current_page + 1, total=self.total_pages, count=len(self.members))
        )
        return embed

    def update_buttons(self):
        is_first = self.current_page <= 0
        is_last = self.current_page >= self.total_pages - 1
        self.first_btn.disabled = is_first
        self.prev_btn.disabled = is_first
        self.next_btn.disabled = is_last
        self.last_btn.disabled = is_last

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id != self.author.id:
            await interaction.response.send_message(t(interaction.guild, "ROLEINFO_VIEW_NOT_YOURS"), ephemeral=True)
            return False
        return True

    @discord.ui.button(label="⏮", style=discord.ButtonStyle.secondary)
    async def first_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.current_page = 0
        self.update_buttons()
        await interaction.response.edit_message(embed=self.create_page_embed(), view=self)

    @discord.ui.button(label="◀ Trước", style=discord.ButtonStyle.secondary)
    async def prev_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.current_page -= 1
        self.update_buttons()
        await interaction.response.edit_message(embed=self.create_page_embed(), view=self)

    @discord.ui.button(label="Sau ▶", style=discord.ButtonStyle.primary)
    async def next_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.current_page += 1
        self.update_buttons()
        await interaction.response.edit_message(embed=self.create_page_embed(), view=self)

    @discord.ui.button(label="⏭", style=discord.ButtonStyle.secondary)
    async def last_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.current_page = self.total_pages - 1
        self.update_buttons()
        await interaction.response.edit_message(embed=self.create_page_embed(), view=self)

    @discord.ui.button(label="Xuất file (.txt)", style=discord.ButtonStyle.success, emoji="📥", row=1)
    async def export_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        lines = [
            f"=== DANH SÁCH THÀNH VIÊN ROLE: {self.role.name} (ID: {self.role.id}) ===",
            f"Tổng số lượng: {len(self.members)} thành viên\n",
        ]
        for idx, m in enumerate(self.members, start=1):
            lines.append(f"{idx}. {m} | Display: {m.display_name} | ID: {m.id} | Bot: {m.bot}")

        file_obj = discord.File(
            fp=io.BytesIO("\n".join(lines).encode("utf-8")),
            filename=f"role_members_{self.role.id}.txt"
        )
        await interaction.response.send_message("📥 Danh sách thành viên chi tiết:", file=file_obj, ephemeral=True)


class RoleInfoActionView(discord.ui.View):
    """3 nút bấm tiện ích gắn trực tiếp dưới bảng /role info."""
    def __init__(self, author: discord.Member, role: discord.Role):
        super().__init__(timeout=180)
        self.author = author
        self.role = role

    @discord.ui.button(label="Xem thành viên", style=discord.ButtonStyle.primary, emoji="👥")
    async def view_members_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        members = self.role.members
        if not members:
            return await interaction.response.send_message(
                t(interaction.guild, "ROLEINFO_MEMBERS_EMPTY", mention=self.role.mention),
                ephemeral=True
            )
        view = MemberPaginatorView(interaction.user, self.role, members)
        await interaction.response.send_message(embed=view.create_page_embed(), view=view, ephemeral=True)

    @discord.ui.button(label="Chỉnh quyền", style=discord.ButtonStyle.secondary, emoji="🔧")
    async def edit_perms_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not interaction.user.guild_permissions.manage_roles and interaction.user.id != OWNER_ID:
            return await interaction.response.send_message(t(interaction.guild, "ROLEINFO_VIEW_NEED_MANAGE"), ephemeral=True)
        embed = build_permissions_embed(self.role, interaction.user)
        view = PermissionEditView(interaction.user, self.role)
        await interaction.response.send_message(embed=embed, view=view, ephemeral=True)

    @discord.ui.button(label="Xóa Role", style=discord.ButtonStyle.danger, emoji="🗑️")
    async def delete_role_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not interaction.user.guild_permissions.manage_roles and interaction.user.id != OWNER_ID:
            return await interaction.response.send_message(t(interaction.guild, "ROLEINFO_VIEW_NEED_MANAGE"), ephemeral=True)
        err = check_role_hierarchy(interaction.guild, interaction.user, self.role)
        if err:
            return await interaction.response.send_message(err, ephemeral=True)

        confirm_view = ConfirmDeleteRoleView(interaction.user, self.role)
        await interaction.response.send_message(
            f"⚠️ Bạn có chắc chắn muốn xóa vĩnh viễn Role {self.role.mention} (`{self.role.name}`) không?",
            view=confirm_view,
            ephemeral=True
        )


class EmptyRolesCleanupView(discord.ui.View):
    """Nút dọn dẹp nhanh các Role trống (0 thành viên)."""
    def __init__(self, author: discord.Member, empty_roles: list[discord.Role]):
        super().__init__(timeout=120)
        self.author = author
        self.empty_roles = empty_roles

    @discord.ui.button(label="Xóa tất cả Role trống ở trên", style=discord.ButtonStyle.danger, emoji="🧹")
    async def clean_all_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.author.id:
            return await interaction.response.send_message(t(interaction.guild, "ROLEINFO_VIEW_NOT_YOURS"), ephemeral=True)

        await interaction.response.defer()
        deleted_names = []
        for r in self.empty_roles:
            if len(r.members) == 0 and not check_role_hierarchy(interaction.guild, interaction.user, r):
                try:
                    await r.delete(reason=f"Empty role cleanup by {interaction.user}")
                    deleted_names.append(r.name)
                except (discord.Forbidden, discord.HTTPException):
                    pass

        self.clear_items()
        await interaction.edit_original_response(
            content=f"✅ Đã dọn dẹp thành công **{len(deleted_names)}** Role trống: `{', '.join(deleted_names) or 'Không có'}`",
            embed=None,
            view=None
        )


# =========================================================================
# COG CHÍNH: QUẢN LÝ TOÀN DIỆN ROLE (GỘP 4 FILE)
# =========================================================================

class RoleManager(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        # Quản lý các task thu hồi Temp Role: {(guild_id, user_id, role_id): asyncio.Task}
        self.temp_role_tasks: dict[tuple[int, int, int], asyncio.Task] = {}

    def cog_unload(self):
        for task in self.temp_role_tasks.values():
            task.cancel()

    # --- AUTOCOMPLETE ---
    async def perm_autocomplete(self, interaction: discord.Interaction, current: str):
        return [
            app_commands.Choice(name=f"{'⚠️ ' if p in DANGEROUS_PERMS else ''}{p}", value=p)
            for p in PERMS_LIST if current.lower() in p.lower()
        ][:25]

    async def color_autocomplete(self, interaction: discord.Interaction, current: str):
        return [
            app_commands.Choice(name=label, value=hex_val)
            for label, hex_val in COLOR_PRESETS.items()
            if current.lower() in label.lower() or current.lower() in hex_val.lower()
        ][:25]

    # =====================================================================
    # NHÓM LỆNH CHÍNH: /role (Và !role)
    # =====================================================================

    @commands.hybrid_group(name="role", description="🎭 Hệ thống quản lý và tra cứu Vai trò (Role) toàn diện.")
    @commands.guild_only()
    async def role_group(self, ctx: commands.Context):
        if ctx.invoked_subcommand is None:
            prefix = ctx.prefix
            embed = discord.Embed(
                title=t(ctx.guild, "ROLEINFO_PANEL_TITLE"),
                description=t(ctx.guild, "ROLEINFO_PANEL_DESC"),
                color=discord.Color.from_rgb(255, 183, 197),
                timestamp=discord.utils.utcnow()
            )
            if self.bot.user:
                embed.set_thumbnail(url=self.bot.user.display_avatar.url)

            embed.add_field(
                name="🔍 Tra cứu & Kiểm tra",
                value=(
                    f"• `{prefix}role info <@Role>`: Thông tin chi tiết & nút thao tác nhanh\n"
                    f"• `{prefix}role members <@Role>`: Danh sách thành viên & xuất file\n"
                    f"• `{prefix}role perms <@Role>`: Xem & bật/tắt nhiều quyền trực quan\n"
                    f"• `{prefix}role compare <@Role1> <@Role2>`: So sánh sự khác biệt giữa 2 Role\n"
                    f"• `{prefix}role empty`: Tìm và dọn dẹp các Role trống (0 thành viên)"
                ),
                inline=False
            )
            embed.add_field(
                name="⚙️ Cấp phát & Chỉnh sửa",
                value=(
                    f"• `{prefix}role add <@Member> <@Role> [thời_hạn]`: Cấp Role (hỗ trợ tạm thời: `1h`, `7d`)\n"
                    f"• `{prefix}role remove <@Member> <@Role>`: Gỡ Role khỏi thành viên\n"
                    f"• `{prefix}role toggle <@Member> <@Role>`: Đảo trạng thái Role nhanh\n"
                    f"• `{prefix}role mass <add/remove> <humans/bots> <@Role>`: Cấp/Gỡ hàng loạt\n"
                    f"• `{prefix}role create <tên> [màu] [hoist] [mentionable]`: Tạo Role mới\n"
                    f"• `{prefix}role clone <@RoleGốc> [tên_mới]`: Nhân bản toàn bộ cấu hình Role\n"
                    f"• `{prefix}role edit / color / position / set / bulk / delete`: Tinh chỉnh Role\n"
                    f"• `{prefix}role admin <add/remove/list/clear>`: Quản lý Role Admin của Bot"
                ),
                inline=False
            )
            embed.set_footer(
                text=t(ctx.guild, "ROLEINFO_FOOTER_REQUESTED", name=ctx.author.display_name),
                icon_url=ctx.author.display_avatar.url
            )
            await ctx.send(embed=embed, ephemeral=True)

    # ---------------------------------------------------------------------
    # 1. NHÓM TRA CỨU: INFO, MEMBERS, PERMS, LIST, COMPARE, EMPTY
    # ---------------------------------------------------------------------

    @role_group.command(name="info", description="🔍 Xem thông tin chi tiết của một Role kèm nút thao tác nhanh.")
    @app_commands.describe(role="Chọn Role bạn muốn xem thông tin")
    async def role_info(self, ctx: commands.Context, role: discord.Role):
        await ctx.defer(ephemeral=True)

        embed = discord.Embed(
            title=t(ctx.guild, "ROLEINFO_TITLE", name=role.name),
            color=role.color if role.color != discord.Color.default() else discord.Color.blue(),
            timestamp=discord.utils.utcnow()
        )
        if role.display_icon:
            embed.set_thumbnail(url=role.display_icon.url if hasattr(role.display_icon, "url") else None)

        embed.add_field(name=t(ctx.guild, "ROLEINFO_FIELD_NAME2"), value=f"{role.mention} (`{role.name}`)", inline=True)
        embed.add_field(name=t(ctx.guild, "ROLEINFO_FIELD_ID2"), value=f"`{role.id}`", inline=True)
        embed.add_field(name=t(ctx.guild, "ROLEINFO_FIELD_COLOR2"), value=f"`{str(role.color).upper()}`", inline=True)
        embed.add_field(name=t(ctx.guild, "ROLEINFO_FIELD_POS"), value=f"`{role.position}` / `{len(ctx.guild.roles) - 1}`", inline=True)
        embed.add_field(name="👥 Thành viên", value=f"**{len(role.members)}** người", inline=True)
        embed.add_field(
            name="🤖 Loại Role",
            value="Hệ thống (Bot/Boost)" if role.managed else "Role thông thường",
            inline=True
        )
        embed.add_field(
            name=t(ctx.guild, "ROLEINFO_FIELD_HOIST"),
            value=t(ctx.guild, "ROLEINFO_VALUE_YES") if role.hoist else t(ctx.guild, "ROLEINFO_VALUE_NO"),
            inline=True
        )
        embed.add_field(
            name=t(ctx.guild, "ROLEINFO_FIELD_MENTIONABLE"),
            value=t(ctx.guild, "ROLEINFO_VALUE_YES") if role.mentionable else t(ctx.guild, "ROLEINFO_VALUE_NO"),
            inline=True
        )
        embed.add_field(
            name=t(ctx.guild, "ROLEINFO_FIELD_CREATED"),
            value=f"<t:{int(role.created_at.timestamp())}:F> (<t:{int(role.created_at.timestamp())}:R>)",
            inline=False
        )

        # Cảnh báo nếu Role có quyền nhạy cảm
        danger_active = [p for p, v in iter(role.permissions) if v and p in DANGEROUS_PERMS]
        if danger_active:
            embed.add_field(
                name="⚠️ Quyền nhạy cảm đang bật",
                value=", ".join(f"`{p}`" for p in danger_active),
                inline=False
            )

        if role >= ctx.guild.me.top_role:
            embed.set_footer(text=t(ctx.guild, "ROLEINFO_FOOTER_HIGHER"))
        else:
            embed.set_footer(
                text=t(ctx.guild, "ROLEINFO_FOOTER_REQUESTED", name=ctx.author.display_name),
                icon_url=ctx.author.display_avatar.url
            )

        view = RoleInfoActionView(ctx.author, role)
        await ctx.send(embed=embed, view=view, ephemeral=True)

    @role_group.command(name="permissions", aliases=["perms"], description="🔧 Xem và bật/tắt nhiều quyền hạn của Role trực tiếp trên Menu.")
    @app_commands.describe(role="Chọn Role bạn muốn xem và chỉnh sửa quyền")
    async def role_permissions(self, ctx: commands.Context, role: discord.Role):
        await ctx.defer(ephemeral=True)
        embed = build_permissions_embed(role, ctx.author)
        view = PermissionEditView(ctx.author, role)
        await ctx.send(embed=embed, view=view, ephemeral=True)

    @role_group.command(name="members", aliases=["mem", "inrole"], description="👥 Liệt kê danh sách thành viên sở hữu Role này.")
    @app_commands.describe(role="Chọn Role bạn muốn xem danh sách thành viên")
    async def role_members(self, ctx: commands.Context, role: discord.Role):
        await ctx.defer(ephemeral=True)
        members = role.members
        if not members:
            return await ctx.send(t(ctx.guild, "ROLEINFO_MEMBERS_EMPTY", mention=role.mention), ephemeral=True)

        view = MemberPaginatorView(ctx.author, role, members)
        await ctx.send(embed=view.create_page_embed(), view=view, ephemeral=True)

    @role_group.command(name="list", description="📖 Xem danh sách các mã quyền hạn có thể chỉnh sửa.")
    async def role_list_perms(self, ctx: commands.Context):
        lines = [
            f"• `{p}` {'⚠️ *(Quyền nhạy cảm)*' if p in DANGEROUS_PERMS else ''}"
            for p in PERMS_LIST
        ]
        embed = discord.Embed(
            title=t(ctx.guild, "ROLE_LIST_TITLE"),
            description="\n".join(lines),
            color=discord.Color.green()
        )
        await ctx.send(embed=embed, ephemeral=True)

    @role_group.command(name="compare", description="⚖️ So sánh sự khác biệt về quyền hạn giữa 2 Role.")
    @app_commands.describe(role1="Role thứ nhất", role2="Role thứ hai")
    async def role_compare(self, ctx: commands.Context, role1: discord.Role, role2: discord.Role):
        perms1 = {p for p, v in iter(role1.permissions) if v}
        perms2 = {p for p, v in iter(role2.permissions) if v}

        only_1 = sorted(perms1 - perms2)
        only_2 = sorted(perms2 - perms1)
        both = sorted(perms1 & perms2)

        embed = discord.Embed(
            title=f"⚖️ So sánh Role: {role1.name} vs {role2.name}",
            color=discord.Color.blurple(),
            timestamp=discord.utils.utcnow()
        )
        embed.add_field(
            name="📊 Thông số cơ bản",
            value=(
                f"• **Vị trí:** {role1.mention} (`#{role1.position}`) vs {role2.mention} (`#{role2.position}`)\n"
                f"• **Thành viên:** `{len(role1.members)}` người vs `{len(role2.members)}` người\n"
                f"• **Quyền giống nhau:** `{len(both)}` quyền"
            ),
            inline=False
        )
        embed.add_field(
            name=f"➕ Chỉ {role1.name} có ({len(only_1)})",
            value=", ".join(f"`{p}`" for p in only_1)[:1024] if only_1 else "*(Không có)*",
            inline=False
        )
        embed.add_field(
            name=f"➕ Chỉ {role2.name} có ({len(only_2)})",
            value=", ".join(f"`{p}`" for p in only_2)[:1024] if only_2 else "*(Không có)*",
            inline=False
        )
        await ctx.send(embed=embed, ephemeral=True)

    @role_group.command(name="empty", description="🧹 Tìm và dọn dẹp các Role đang trống (0 thành viên).")
    @has_admin_role()
    async def role_empty(self, ctx: commands.Context):
        empty_roles = [
            r for r in ctx.guild.roles
            if not r.is_default() and not r.managed and len(r.members) == 0
        ]
        if not empty_roles:
            return await ctx.send("✨ Máy chủ hiện không có Role thông thường nào bị trống (0 thành viên)!", ephemeral=True)

        embed = discord.Embed(
            title=f"🧹 Phát hiện {len(empty_roles)} Role trống (0 thành viên)",
            description="\n".join(f"• {r.mention} (`{r.id}`)" for r in empty_roles[:30]),
            color=discord.Color.orange()
        )
        if len(empty_roles) > 30:
            embed.set_footer(text=f"...và {len(empty_roles) - 30} Role trống khác.")

        view = EmptyRolesCleanupView(ctx.author, empty_roles)
        await ctx.send(embed=embed, view=view, ephemeral=True)

    # ---------------------------------------------------------------------
    # 2. NHÓM CẤP / GỠ ROLE CHO THÀNH VIÊN: ADD (TEMP ROLE), REMOVE, TOGGLE, MASS
    # ---------------------------------------------------------------------

    @role_group.command(name="add", description="➕ Cấp một Role cho thành viên (Hỗ trợ cấp có thời hạn: 30m, 2h, 7d).")
    @app_commands.describe(
        member="Thành viên cần cấp Role",
        role="Role muốn cấp",
        duration="Thời hạn tự động thu hồi (Ví dụ: 30m, 2h, 7d). Bỏ trống nếu cấp vĩnh viễn."
    )
    @has_admin_role()
    async def role_add(
        self,
        ctx: commands.Context,
        member: discord.Member,
        role: discord.Role,
        duration: Optional[str] = None
    ):
        err = check_role_hierarchy(ctx.guild, ctx.author, role)
        if err:
            return await ctx.send(err, ephemeral=True)

        if role in member.roles:
            return await ctx.send(t(ctx.guild, "ROLE_ALREADY_HAS", mention=member.mention), ephemeral=True)

        seconds = None
        if duration:
            seconds = parse_duration(duration)
            if not seconds:
                return await ctx.send("⚠️ Định dạng thời gian không hợp lệ! Ví dụ hợp lệ: `30m`, `12h`, `7d`.", ephemeral=True)

        try:
            await member.add_roles(role, reason=f"Added by {ctx.author}" + (f" for {duration}" if duration else ""))

            embed = discord.Embed(
                title=t(ctx.guild, "ROLE_ADD_SUCCESS_TITLE"),
                color=discord.Color.green(),
                timestamp=discord.utils.utcnow()
            )
            embed.add_field(name=t(ctx.guild, "ROLE_FIELD_MEMBER"), value=member.mention, inline=True)
            embed.add_field(name=t(ctx.guild, "ROLE_FIELD_ROLE"), value=role.mention, inline=True)

            if seconds:
                expire_ts = int(discord.utils.utcnow().timestamp()) + seconds
                embed.add_field(
                    name="⏳ Thời hạn (Temp Role)",
                    value=f"{format_duration_vi(seconds)} (Thu hồi <t:{expire_ts}:R>)",
                    inline=False
                )
                self._schedule_temp_role_removal(ctx.guild, member.id, role.id, seconds)

            embed.set_footer(text=t(ctx.guild, "ROLE_FOOTER_BY", name=ctx.author))
            await ctx.send(embed=embed)
        except discord.Forbidden:
            await ctx.send(t(ctx.guild, "ROLE_BOT_NO_PERM_ADD"), ephemeral=True)
        except Exception as e:
            await ctx.send(t(ctx.guild, "ROLE_ERROR_GENERIC", error=e), ephemeral=True)

    def _schedule_temp_role_removal(self, guild: discord.Guild, user_id: int, role_id: int, seconds: int):
        key = (guild.id, user_id, role_id)
        if key in self.temp_role_tasks and not self.temp_role_tasks[key].done():
            self.temp_role_tasks[key].cancel()

        async def _remove_later():
            try:
                await asyncio.sleep(seconds)
                member = guild.get_member(user_id)
                role = guild.get_role(role_id)
                if member and role and role in member.roles:
                    await member.remove_roles(role, reason="Hết thời hạn Temp Role")
            except (asyncio.CancelledError, discord.Forbidden, discord.HTTPException):
                pass
            finally:
                self.temp_role_tasks.pop(key, None)

        self.temp_role_tasks[key] = asyncio.create_task(_remove_later())

    @role_group.command(name="remove", aliases=["take", "rm"], description="➖ Gỡ một Role khỏi thành viên cụ thể.")
    @app_commands.describe(member="Thành viên cần gỡ Role", role="Role muốn gỡ")
    @has_admin_role()
    async def role_remove(self, ctx: commands.Context, member: discord.Member, role: discord.Role):
        err = check_role_hierarchy(ctx.guild, ctx.author, role)
        if err:
            return await ctx.send(err, ephemeral=True)

        if role not in member.roles:
            return await ctx.send(f"⚠️ {member.mention} hiện không sở hữu Role {role.mention}!", ephemeral=True)

        try:
            await member.remove_roles(role, reason=f"Removed by {ctx.author}")
            embed = discord.Embed(
                title="➖ Đã gỡ Role thành công",
                color=discord.Color.orange(),
                timestamp=discord.utils.utcnow()
            )
            embed.add_field(name=t(ctx.guild, "ROLE_FIELD_MEMBER"), value=member.mention, inline=True)
            embed.add_field(name=t(ctx.guild, "ROLE_FIELD_ROLE"), value=role.mention, inline=True)
            embed.set_footer(text=t(ctx.guild, "ROLE_FOOTER_BY", name=ctx.author))
            await ctx.send(embed=embed)
        except discord.Forbidden:
            await ctx.send(t(ctx.guild, "ROLE_BOT_NO_PERM_ADD"), ephemeral=True)
        except Exception as e:
            await ctx.send(t(ctx.guild, "ROLE_ERROR_GENERIC", error=e), ephemeral=True)

    @role_group.command(name="toggle", description="🔄 Đảo trạng thái Role (Chưa có thì cấp, có rồi thì gỡ).")
    @app_commands.describe(member="Thành viên", role="Role cần đảo trạng thái")
    @has_admin_role()
    async def role_toggle(self, ctx: commands.Context, member: discord.Member, role: discord.Role):
        if role in member.roles:
            await self.role_remove(ctx, member, role)
        else:
            await self.role_add(ctx, member, role, duration=None)

    @role_group.command(name="mass", description="⚡ Cấp hoặc gỡ Role hàng loạt cho toàn bộ Người dùng hoặc Bot.")
    @app_commands.describe(
        action="Chọn cấp (add) hoặc gỡ (remove)",
        target="Đối tượng áp dụng: Toàn bộ thành viên (all), chỉ Người (humans), hoặc chỉ Bot (bots)",
        role="Role cần cấp hoặc gỡ"
    )
    @commands.has_permissions(administrator=True)
    async def role_mass(
        self,
        ctx: commands.Context,
        action: Literal["add", "remove"],
        target: Literal["humans", "bots", "all"],
        role: discord.Role
    ):
        err = check_role_hierarchy(ctx.guild, ctx.author, role)
        if err:
            return await ctx.send(err, ephemeral=True)

        await ctx.defer()

        if target == "humans":
            candidates = [m for m in ctx.guild.members if not m.bot]
        elif target == "bots":
            candidates = [m for m in ctx.guild.members if m.bot]
        else:
            candidates = list(ctx.guild.members)

        if action == "add":
            targets = [m for m in candidates if role not in m.roles]
        else:
            targets = [m for m in candidates if role in m.roles]

        if not targets:
            return await ctx.send(f"ℹ️ Không có thành viên nào thuộc nhóm `{target}` cần `{action}` Role {role.mention}.")

        success_count = 0
        for m in targets:
            try:
                if action == "add":
                    await m.add_roles(role, reason=f"Mass {action} by {ctx.author}")
                else:
                    await m.remove_roles(role, reason=f"Mass {action} by {ctx.author}")
                success_count += 1
                await asyncio.sleep(0.3)  # Tránh dính Rate Limit của Discord
            except (discord.Forbidden, discord.HTTPException):
                pass

        act_vi = "cấp" if action == "add" else "gỡ"
        await ctx.send(f"✅ Đã {act_vi} Role {role.mention} thành công cho **{success_count}/{len(targets)}** thành viên (`{target}`)!")

    # ---------------------------------------------------------------------
    # 3. NHÓM TẠO / SỬA / XÓA / NHÂN BẢN ROLE: CREATE, CLONE, EDIT, COLOR, POS, DEL, SET, BULK
    # ---------------------------------------------------------------------

    @role_group.command(name="create", description="🆕 Tạo một Role mới cho Server (Có gợi ý màu sắc đẹp).")
    @app_commands.describe(
        name="Tên của Role mới",
        color="Chọn màu gợi ý hoặc nhập mã HEX (Ví dụ: #ff0000)",
        hoist="Hiển thị tách biệt Role này trên danh sách thành viên?",
        mentionable="Cho phép mọi người @tag Role này?"
    )
    @app_commands.autocomplete(color=color_autocomplete)
    @has_admin_role()
    async def role_create(
        self,
        ctx: commands.Context,
        name: str,
        color: Optional[str] = None,
        hoist: bool = False,
        mentionable: bool = False
    ):
        if not ctx.guild.me.guild_permissions.manage_roles:
            return await ctx.send(t(ctx.guild, "ROLE_BOT_NO_PERM_MANAGE"), ephemeral=True)

        role_color = parse_Color(color)
        if role_color is None:
            return await ctx.send(t(ctx.guild, "ROLE_COLOR_INVALID"), ephemeral=True)

        try:
            new_role = await ctx.guild.create_role(
                name=name,
                color=role_color,
                hoist=hoist,
                mentionable=mentionable,
                reason=f"Created by {ctx.author}"
            )

            embed = discord.Embed(
                title=t(ctx.guild, "ROLE_CREATE_SUCCESS_TITLE"),
                color=new_role.color if new_role.color != discord.Color.default() else discord.Color.blue(),
                timestamp=discord.utils.utcnow()
            )
            embed.add_field(name=t(ctx.guild, "ROLE_FIELD_NAME"), value=new_role.mention, inline=True)
            embed.add_field(name=t(ctx.guild, "ROLE_FIELD_COLOR"), value=f"`{str(new_role.color).upper()}`", inline=True)
            embed.add_field(name=t(ctx.guild, "ROLE_FIELD_ID"), value=f"`{new_role.id}`", inline=True)
            embed.set_footer(text=t(ctx.guild, "ROLE_FOOTER_BY", name=ctx.author))
            await ctx.send(embed=embed)
        except discord.Forbidden:
            await ctx.send(t(ctx.guild, "ROLE_BOT_NO_PERM_MANAGE2"), ephemeral=True)
        except Exception as e:
            await ctx.send(t(ctx.guild, "ROLE_ERROR_GENERIC2", error=e), ephemeral=True)

    @role_group.command(name="clone", description="📑 Nhân bản một Role (Sao chép toàn bộ quyền hạn, màu sắc, cài đặt).")
    @app_commands.describe(role="Chọn Role gốc muốn nhân bản", new_name="Tên cho Role mới (bỏ trống sẽ lấy tên cũ + Bản sao)")
    @has_admin_role()
    async def role_clone(self, ctx: commands.Context, role: discord.Role, new_name: Optional[str] = None):
        err = check_role_hierarchy(ctx.guild, ctx.author, role, check_managed=False)
        if err:
            return await ctx.send(err, ephemeral=True)

        await ctx.defer()
        target_name = new_name or f"{role.name} (Copy)"
        try:
            cloned = await ctx.guild.create_role(
                name=target_name,
                permissions=role.permissions,
                color=role.color,
                hoist=role.hoist,
                mentionable=role.mentionable,
                reason=f"Cloned from {role.name} by {ctx.author}"
            )
            embed = discord.Embed(
                title="📑 Đã nhân bản Role thành công!",
                description=f"Đã sao chép cấu hình từ {role.mention} sang {cloned.mention}.",
                color=cloned.color if cloned.color != discord.Color.default() else discord.Color.green()
            )
            embed.add_field(name="🆔 ID Mới", value=f"`{cloned.id}`", inline=True)
            embed.add_field(name="🎨 Màu sắc", value=f"`{str(cloned.color).upper()}`", inline=True)
            await ctx.send(embed=embed)
        except Exception as e:
            await ctx.send(t(ctx.guild, "ROLE_ERROR_GENERIC2", error=e), ephemeral=True)

    @role_group.command(name="edit", description="✏️ Chỉnh sửa tổng hợp một Role (Tên, Màu sắc, Hoist, Mentionable).")
    @app_commands.describe(
        role="Role cần chỉnh sửa",
        name="Tên mới cho Role",
        color="Màu mới (mã HEX hoặc chọn từ gợi ý)",
        hoist="Hiển thị tách biệt trên danh sách?",
        mentionable="Cho phép @tag Role này?"
    )
    @app_commands.autocomplete(color=color_autocomplete)
    @has_admin_role()
    async def role_edit(
        self,
        ctx: commands.Context,
        role: discord.Role,
        name: Optional[str] = None,
        color: Optional[str] = None,
        hoist: Optional[bool] = None,
        mentionable: Optional[bool] = None
    ):
        err = check_role_hierarchy(ctx.guild, ctx.author, role, check_managed=False)
        if err:
            return await ctx.send(err, ephemeral=True)

        kwargs = {}
        changes = []

        if name is not None and name != role.name:
            kwargs["name"] = name
            changes.append(f"• **Tên:** `{role.name}` ➜ `{name}`")

        if color is not None:
            c_obj = parse_Color(color)
            if c_obj is None:
                return await ctx.send(t(ctx.guild, "ROLE_COLOR_INVALID"), ephemeral=True)
            kwargs["color"] = c_obj
            changes.append(f"• **Màu:** `{role.color}` ➜ `{c_obj}`")

        if hoist is not None and hoist != role.hoist:
            kwargs["hoist"] = hoist
            changes.append(f"• **Hiển thị riêng (Hoist):** `{role.hoist}` ➜ `{hoist}`")

        if mentionable is not None and mentionable != role.mentionable:
            kwargs["mentionable"] = mentionable
            changes.append(f"• **Cho phép @tag:** `{role.mentionable}` ➜ `{mentionable}`")

        if not kwargs:
            return await ctx.send("⚠️ Bạn chưa nhập thuộc tính nào mới để thay đổi!", ephemeral=True)

        try:
            await role.edit(**kwargs, reason=f"Edited by {ctx.author}")
            embed = discord.Embed(
                title="✏️ Đã cập nhật Role thành công",
                description=f"**Role:** {role.mention}\n\n" + "\n".join(changes),
                color=role.color if role.color != discord.Color.default() else discord.Color.green()
            )
            await ctx.send(embed=embed)
        except Exception as e:
            await ctx.send(t(ctx.guild, "ROLE_ERROR_GENERIC2", error=e), ephemeral=True)

    @role_group.command(name="color", description="🎨 Thay đổi hoặc reset màu sắc của một Role.")
    @app_commands.describe(role="Role bạn muốn đổi màu", color="Chọn màu gợi ý, nhập mã HEX (#ff0000) hoặc 'reset'")
    @app_commands.autocomplete(color=color_autocomplete)
    @has_admin_role()
    async def role_color(self, ctx: commands.Context, role: discord.Role, color: str):
        err = check_role_hierarchy(ctx.guild, ctx.author, role, check_managed=False)
        if err:
            return await ctx.send(err, ephemeral=True)

        color_obj = parse_Color(color)
        if color_obj is None:
            return await ctx.send(t(ctx.guild, "ROLE_COLOR_INVALID"), ephemeral=True)

        try:
            await role.edit(color=color_obj, reason=f"Color changed by {ctx.author}")
            if color.lower() in ("reset", "default", "none", "clear"):
                return await ctx.send(t(ctx.guild, "ROLE_COLOR_RESET", mention=role.mention))

            embed = discord.Embed(title=t(ctx.guild, "ROLE_COLOR_CHANGED_TITLE"), color=color_obj)
            embed.add_field(name=t(ctx.guild, "ROLE_FIELD_ROLE"), value=role.mention, inline=True)
            embed.add_field(name=t(ctx.guild, "ROLE_COLOR_NEW"), value=f"`{str(color_obj).upper()}`", inline=True)
            await ctx.send(embed=embed)
        except discord.Forbidden:
            await ctx.send(t(ctx.guild, "ROLE_BOT_NO_PERM_COLOR"), ephemeral=True)
        except Exception as e:
            await ctx.send(t(ctx.guild, "ROLE_ERROR_GENERIC2", error=e), ephemeral=True)

    @role_group.command(name="position", aliases=["pos"], description="📏 Thay đổi vị trí phân cấp của một Role trong danh sách.")
    @app_commands.describe(role="Role bạn muốn di chuyển", position="Vị trí mới (số càng cao càng nằm ở trên)")
    @has_admin_role()
    async def role_position(self, ctx: commands.Context, role: discord.Role, position: int):
        err = check_role_hierarchy(ctx.guild, ctx.author, role, check_managed=False)
        if err:
            return await ctx.send(err, ephemeral=True)

        max_pos = ctx.guild.me.top_role.position - 1
        if isinstance(ctx.author, discord.Member) and ctx.author.id not in (ctx.guild.owner_id, OWNER_ID):
            max_pos = min(max_pos, ctx.author.top_role.position - 1)

        if position <= 0 or position > max_pos:
            return await ctx.send(t(ctx.guild, "ROLEINFO_POS_INVALID", max=max_pos), ephemeral=True)

        old_pos = role.position
        try:
            await role.edit(position=position, reason=f"Moved by {ctx.author}")
            embed = discord.Embed(
                title=t(ctx.guild, "ROLEINFO_POS_SUCCESS_TITLE"),
                color=role.color if role.color != discord.Color.default() else discord.Color.blue()
            )
            embed.add_field(name=t(ctx.guild, "ROLEINFO_POS_FIELD_ROLE"), value=role.mention, inline=False)
            embed.add_field(name=t(ctx.guild, "ROLEINFO_POS_FIELD_OLD"), value=f"`{old_pos}`", inline=True)
            embed.add_field(name=t(ctx.guild, "ROLEINFO_POS_FIELD_NEW"), value=f"`{position}`", inline=True)
            await ctx.send(embed=embed)
        except Exception as e:
            await ctx.send(t(ctx.guild, "ROLEINFO_POS_ERROR", error=e), ephemeral=True)

    @role_group.command(name="set", description="🔧 Bật hoặc Tắt nhanh một quyền cụ thể cho Role.")
    @app_commands.describe(role="Role cần chỉnh quyền", permission="Tên quyền", value="True = Bật, False = Tắt")
    @app_commands.autocomplete(permission=perm_autocomplete)
    @commands.has_permissions(administrator=True)
    async def role_set_perm(self, ctx: commands.Context, role: discord.Role, permission: str, value: bool):
        err = check_role_hierarchy(ctx.guild, ctx.author, role, check_managed=False)
        if err:
            return await ctx.send(err, ephemeral=True)

        perms = dict(role.permissions)
        if permission not in perms:
            return await ctx.send(t(ctx.guild, "ROLE_NOT_EXIST"), ephemeral=True)

        perms[permission] = value
        await role.edit(permissions=discord.Permissions(**perms), reason=f"Set perm {permission}={value} by {ctx.author}")
        status = t(ctx.guild, "ROLE_STATUS_ON") if value else t(ctx.guild, "ROLE_STATUS_OFF")
        await ctx.send(t(ctx.guild, "ROLE_SET_DONE", status=status, permission=permission, mention=role.mention))

    @role_group.command(name="bulk", description="⚡ Cấp toàn bộ quyền (all) hoặc Xóa toàn bộ quyền (none) của Role.")
    @app_commands.describe(role="Role cần áp dụng", action="all = Cấp hết, none = Xóa hết")
    @commands.has_permissions(administrator=True)
    async def role_bulk_perms(self, ctx: commands.Context, role: discord.Role, action: Literal["all", "none"]):
        err = check_role_hierarchy(ctx.guild, ctx.author, role, check_managed=False)
        if err:
            return await ctx.send(err, ephemeral=True)

        if action == "all":
            await role.edit(permissions=discord.Permissions.all(), reason=f"Bulk ALL by {ctx.author}")
            await ctx.send(t(ctx.guild, "ROLE_BULK_ALL", mention=role.mention))
        else:
            await role.edit(permissions=discord.Permissions.none(), reason=f"Bulk NONE by {ctx.author}")
            await ctx.send(t(ctx.guild, "ROLE_BULK_NONE", mention=role.mention))

    @role_group.command(name="delete", aliases=["del", "delrole"], description="🗑️ Xóa một Role ra khỏi Server (Có xác nhận an toàn).")
    @app_commands.describe(role="Chọn Role bạn muốn xóa bỏ")
    @has_admin_role()
    async def role_delete(self, ctx: commands.Context, role: discord.Role):
        err = check_role_hierarchy(ctx.guild, ctx.author, role)
        if err:
            return await ctx.send(err, ephemeral=True)

        view = ConfirmDeleteRoleView(ctx.author, role)
        await ctx.send(
            f"⚠️ Bạn có chắc chắn muốn xóa vĩnh viễn Role {role.mention} (`{role.name}` - đang có **{len(role.members)}** thành viên) không?",
            view=view,
            ephemeral=True
        )

    # ---------------------------------------------------------------------
    # 4. QUẢN LÝ ROLE ADMIN CỦA BOT (GỘP TỪ ROLEADMIN.PY)
    # ---------------------------------------------------------------------

    @role_group.command(name="admin", description="👑 Quản lý danh sách các Role có quyền Admin của Bot.")
    @app_commands.describe(
        action="Chọn hành động: add (Thêm), remove (Gỡ), list (Xem danh sách), clear (Xóa hết)",
        role="Chọn Role cần thêm hoặc gỡ"
    )
    @commands.has_permissions(administrator=True)
    async def role_admin_sub(
        self,
        ctx: commands.Context,
        action: Optional[Literal["add", "remove", "list", "clear"]] = None,
        role: Optional[discord.Role] = None
    ):
        await self._handle_role_admin(ctx, action, role)

    @commands.command(name="roleadmin", description="👑 Quản lý danh sách các Role có quyền Admin của Bot.")
    @commands.guild_only()
    @commands.has_permissions(administrator=True)
    async def roleadmin_standalone(
        self,
        ctx: commands.Context,
        action: Optional[Literal["add", "remove", "list", "clear"]] = None,
        role: Optional[discord.Role] = None
    ):
        """Giữ lại lệnh /roleadmin độc lập để tương thích với thói quen cũ của Admin."""
        await self._handle_role_admin(ctx, action, role)

    async def _handle_role_admin(
        self,
        ctx: commands.Context,
        action: Optional[str],
        role: Optional[discord.Role]
    ):
        guild_id = str(ctx.guild.id)
        if guild_id not in admin_roles or not isinstance(admin_roles[guild_id], list):
            admin_roles[guild_id] = []

        if action is None:
            embed = discord.Embed(
                title="👑 QUẢN LÝ ROLE ADMIN CỦA BOT",
                description=(
                    "`/role admin add @Role` — Thêm Role vào danh sách Admin Bot\n"
                    "`/role admin remove @Role` — Gỡ Role khỏi danh sách Admin Bot\n"
                    "`/role admin list` — Xem các Role Admin hiện tại\n"
                    "`/role admin clear` — Xóa toàn bộ danh sách Role Admin"
                ),
                color=discord.Color.gold()
            )
            return await ctx.send(embed=embed)

        act = action.lower()

        if act == "add":
            if role is None:
                return await ctx.send(t(ctx.guild, "ROLEADMIN_NEED_ROLE"), ephemeral=True)
            if role.id in admin_roles[guild_id]:
                return await ctx.send(t(ctx.guild, "ROLEADMIN_ALREADY"), ephemeral=True)

            admin_roles[guild_id].append(role.id)
            save_admin_roles()
            return await ctx.send(t(ctx.guild, "ROLEADMIN_ADD_DONE", role=role.mention))

        if act == "remove":
            if role is None:
                return await ctx.send(t(ctx.guild, "ROLEADMIN_NEED_ROLE"), ephemeral=True)
            if role.id not in admin_roles[guild_id]:
                return await ctx.send(t(ctx.guild, "ROLEADMIN_NOT_IN_LIST"), ephemeral=True)

            admin_roles[guild_id].remove(role.id)
            save_admin_roles()
            return await ctx.send(t(ctx.guild, "ROLEADMIN_REMOVE_DONE", role=role.mention))

        if act == "list":
            valid_roles = []
            cleaned_ids = []
            for r_id in admin_roles[guild_id]:
                r_obj = ctx.guild.get_role(int(r_id))
                if r_obj:
                    valid_roles.append(f"• {r_obj.mention} (`{r_obj.id}`)")
                    cleaned_ids.append(r_obj.id)

            # Tự động dọn các ID Role đã bị xóa khỏi server
            if len(cleaned_ids) != len(admin_roles[guild_id]):
                admin_roles[guild_id] = cleaned_ids
                save_admin_roles()

            roles_text = "\n".join(valid_roles) if valid_roles else t(ctx.guild, "ROLEADMIN_LIST_EMPTY")
            embed = discord.Embed(
                title=t(ctx.guild, "ROLEADMIN_LIST_TITLE"),
                description=roles_text,
                color=discord.Color.gold()
            )
            return await ctx.send(embed=embed)

        if act == "clear":
            admin_roles[guild_id] = []
            save_admin_roles()
            return await ctx.send(t(ctx.guild, "ROLEADMIN_CLEAR_DONE"))


async def setup(bot: commands.Bot):
    await bot.add_cog(RoleManager(bot))
