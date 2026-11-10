import discord
from discord import app_commands
from discord.ext import commands
from datetime import datetime, timedelta
from typing import Optional

from config import OWNER_ID
from Command.command_blacklist import blacklist_users, save_blacklist
from Check.i18n import t, is_vietnamese

# --- MODALS (CỬA SỔ POPUP) ---

class UserActionModal(discord.ui.Modal):
    """Modal chung cho các hành động cần nhập liệu như Mute, Rename."""
    def __init__(self, title: str, action: str, target_user: discord.Member):
        super().__init__(title=title)
        self.action = action
        self.target_user = target_user

        if self.action == "mute":
            self.duration = discord.ui.TextInput(
                label="Thời gian Mute (phút)",
                placeholder="Ví dụ: 10, 60, 1440...",
                required=True
            )
            self.add_item(self.duration)

        if self.action == "rename":
            self.new_name = discord.ui.TextInput(
                label="Tên mới (Nickname)",
                placeholder="Nhập tên bạn muốn đổi cho thành viên này...",
                required=True,
                max_length=32
            )
            self.add_item(self.new_name)

        self.reason = discord.ui.TextInput(
            label="Lý do (Tùy chọn)",
            style=discord.TextStyle.short,
            required=False
        )
        self.add_item(self.reason)

    async def on_submit(self, interaction: discord.Interaction):
        reason_str = self.reason.value or f"Thực hiện bởi {interaction.user.display_name}"
        
        if self.action == "mute":
            try:
                minutes = int(self.duration.value)
                await self.target_user.timeout(timedelta(minutes=minutes), reason=reason_str)
                await interaction.response.send_message(t(interaction.guild, "USERPANEL_MUTE_DONE", mention=self.target_user.mention, minutes=minutes), ephemeral=True)
            except (ValueError, discord.Forbidden) as e:
                await interaction.response.send_message(f"❌ Lỗi khi Mute: {e}", ephemeral=True)

        elif self.action == "rename":
            try:
                await self.target_user.edit(nick=self.new_name.value, reason=reason_str)
                await interaction.response.send_message(t(interaction.guild, "USERPANEL_RENAME_DONE", mention=self.target_user.mention, name=self.new_name.value), ephemeral=True)
            except discord.Forbidden as e:
                await interaction.response.send_message(f"❌ Lỗi khi đổi tên: {e}", ephemeral=True)


# --- VIEWS (BỘ NÚT BẤM) ---

class ConfirmView(discord.ui.View):
    """View xác nhận cho các hành động nguy hiểm như Ban, Kick."""
    def __init__(self, author_id: int):
        super().__init__(timeout=30)
        self.author_id = author_id
        self.value = None

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        return interaction.user.id == self.author_id

    @discord.ui.button(label="Xác nhận", style=discord.ButtonStyle.danger)
    async def confirm(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.value = True
        self.stop()
        await interaction.response.defer()

    @discord.ui.button(label="Hủy", style=discord.ButtonStyle.secondary)
    async def cancel(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.value = False
        self.stop()
        await interaction.response.defer()

class RoleManageView(discord.ui.View):
    """View chứa RoleSelect và nút Submit, thay thế cho Modal không hợp lệ."""
    def __init__(self, author_id: int, target_user: discord.Member, action: str):
        super().__init__(timeout=120)
        self.author_id = author_id
        self.target_user = target_user
        self.action = action
        self.action_text = "thêm" if action == "add" else "xóa"

        self.role_select = discord.ui.RoleSelect(
            placeholder=f"Chọn role để {self.action_text} cho {target_user.display_name}...",
            min_values=1,
            max_values=25
        )
        self.add_item(self.role_select)

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        return interaction.user.id == self.author_id

    @discord.ui.button(label="Lưu thay đổi", style=discord.ButtonStyle.success)
    async def submit_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        roles_to_modify = self.role_select.values
        success_roles, failed_roles = [], []

        for role in roles_to_modify:
            try:
                if self.action == "add":
                    await self.target_user.add_roles(role, reason=f"Thêm bởi {interaction.user}")
                else: # remove
                    await self.target_user.remove_roles(role, reason=f"Xóa bởi {interaction.user}")
                success_roles.append(role.mention)
            except discord.Forbidden:
                failed_roles.append(role.mention)

        response_msg = ""
        if success_roles:
            response_msg += f"✅ Đã {self.action_text} thành công các role: {', '.join(success_roles)} cho {self.target_user.mention}.\n"
        if failed_roles:
            response_msg += f"❌ Thất bại với các role (thiếu quyền hoặc role cao hơn bot): {', '.join(failed_roles)}."

        # Chỉnh sửa tin nhắn gốc để hiển thị kết quả và xóa các nút bấm
        # thay vì cố gắng xóa một tin nhắn ephemeral (gây lỗi 10008)
        # SỬA LỖI: Không thể edit tin nhắn ephemeral. Thay vào đó, gửi một tin nhắn followup mới.
        await interaction.response.defer() # Đánh dấu đã nhận tương tác
        await interaction.followup.send(response_msg or "Không có thay đổi nào được thực hiện.", ephemeral=True)
        await interaction.message.delete() # Xóa tin nhắn có nút chọn role đi
        self.stop()

class UserPanelView(discord.ui.View):
    def __init__(self, author: discord.Member, target: discord.Member):
        super().__init__(timeout=180)
        self.author = author
        self.target = target

        vi = is_vietnamese(getattr(author, "guild", None))
        # --- Logic thêm/bớt nút dựa trên quyền và trạng thái ---
        # Quyền cơ bản
        if author.guild_permissions.kick_members:
            self.add_item(self.create_button("Kick", self.kick_callback, style=discord.ButtonStyle.danger, emoji="👢", row=0))
        if author.guild_permissions.ban_members:
            self.add_item(self.create_button("Ban", self.ban_callback, style=discord.ButtonStyle.danger, emoji="🔨", row=0))
        if author.guild_permissions.moderate_members:
            mute_lbl = "Mute" if vi else "Timeout"
            unmute_lbl = "Unmute" if vi else "Remove Timeout"
            self.add_item(self.create_button(mute_lbl, self.mute_callback, style=discord.ButtonStyle.secondary, emoji="🔇", row=0))
            self.add_item(self.create_button(unmute_lbl, self.unmute_callback, style=discord.ButtonStyle.success, emoji="🔊", row=0))
        if author.guild_permissions.manage_nicknames:
            rename_lbl = "Đổi Tên" if vi else "Rename"
            self.add_item(self.create_button(rename_lbl, self.rename_callback, style=discord.ButtonStyle.secondary, emoji="📝", row=1))
        if author.guild_permissions.manage_roles:
            add_role_lbl = "Thêm Role" if vi else "Add Role"
            rem_role_lbl = "Xóa Role" if vi else "Remove Role"
            self.add_item(self.create_button(add_role_lbl, self.add_role_callback, style=discord.ButtonStyle.success, emoji="➕", row=1))
            self.add_item(self.create_button(rem_role_lbl, self.remove_role_callback, style=discord.ButtonStyle.danger, emoji="➖", row=1))

        # Quyền trong kênh thoại
        if target.voice:
            if author.guild_permissions.move_members:
                self.add_item(self.create_button("Move", self.move_callback, style=discord.ButtonStyle.primary, emoji="🚀", row=2))
            if author.guild_permissions.mute_members:
                mic_lbl = "Tắt Mic" if vi else "Mute Mic"
                self.add_item(self.create_button(mic_lbl, self.mute_voice_callback, style=discord.ButtonStyle.primary, emoji="🎤", row=2))
            if author.guild_permissions.deafen_members:
                deaf_lbl = "Tắt Âm" if vi else "Deafen"
                self.add_item(self.create_button(deaf_lbl, self.deafen_voice_callback, style=discord.ButtonStyle.primary, emoji="🎧", row=2))

        # Quyền Owner
        if author.id == OWNER_ID:
            self.add_item(self.create_button("Blacklist", self.blacklist_callback, style=discord.ButtonStyle.grey, emoji="⛔", row=3))
            self.add_item(self.create_button("Un-Blacklist", self.unblacklist_callback, style=discord.ButtonStyle.grey, emoji="✅", row=3))

    def create_button(self, label, callback, **kwargs):
        button = discord.ui.Button(label=label, **kwargs)
        button.callback = callback
        return button

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id != self.author.id:
            await interaction.response.send_message(t(interaction.guild, "LEVEL_NOT_YOURS"), ephemeral=True)
            return False
        # Kiểm tra lại quyền hạn của người dùng trước khi thực hiện hành động
        # (Phòng trường hợp quyền bị thay đổi sau khi lệnh được gọi)
        if not interaction.user.guild_permissions.administrator: # Một check đơn giản, có thể làm chi tiết hơn
             await interaction.response.send_message(t(interaction.guild, "USERPANEL_NO_PERM"), ephemeral=True)
             return False
        return True

    # --- Callbacks cho các nút ---
    async def kick_callback(self, interaction: discord.Interaction):
        await self.confirm_and_execute(interaction, "kick", f"Bạn có chắc muốn **Kick** {self.target.mention} không?")

    async def ban_callback(self, interaction: discord.Interaction):
        await self.confirm_and_execute(interaction, "ban", f"Bạn có chắc muốn **Ban** {self.target.mention} không?")

    async def mute_callback(self, interaction: discord.Interaction):
        await interaction.response.send_modal(UserActionModal("Mute Thành Viên", "mute", self.target))

    async def unmute_callback(self, interaction: discord.Interaction):
        try:
            await self.target.timeout(None, reason=f"Gỡ Mute bởi {interaction.user}")
            await interaction.response.send_message(t(interaction.guild, "USERPANEL_UNMUTE_DONE", mention=self.target.mention), ephemeral=True)
        except discord.Forbidden as e:
            await interaction.response.send_message(f"❌ Lỗi khi gỡ Mute: {e}", ephemeral=True)

    async def rename_callback(self, interaction: discord.Interaction):
        await interaction.response.send_modal(UserActionModal("Đổi Tên Thành Viên", "rename", self.target))

    async def add_role_callback(self, interaction: discord.Interaction):
        view = RoleManageView(interaction.user.id, self.target, "add")
        await interaction.response.send_message("Vui lòng chọn các vai trò bạn muốn thêm:", view=view, ephemeral=True)

    async def remove_role_callback(self, interaction: discord.Interaction):
        view = RoleManageView(interaction.user.id, self.target, "remove")
        await interaction.response.send_message("Vui lòng chọn các vai trò bạn muốn xóa:", view=view, ephemeral=True)

    async def move_callback(self, interaction: discord.Interaction):
        # Logic cho move: Cần một Select Menu để chọn kênh voice
        voice_channels = interaction.guild.voice_channels
        if not voice_channels:
            return await interaction.response.send_message("Server không có kênh thoại nào để chuyển.", ephemeral=True)

        options = [discord.SelectOption(label=vc.name, value=str(vc.id)) for vc in voice_channels[:25]]
        select = discord.ui.Select(placeholder="Chọn kênh thoại để chuyển đến...", options=options)

        async def select_callback(inter: discord.Interaction):
            channel_id = int(select.values[0])
            target_channel = inter.guild.get_channel(channel_id)
            try:
                await self.target.move_to(target_channel, reason=f"Di chuyển bởi {inter.user}")
                await inter.response.send_message(f"🚀 Đã chuyển {self.target.mention} đến {target_channel.mention}.", ephemeral=True)
            except Exception as e:
                await inter.response.send_message(f"❌ Lỗi khi di chuyển: {e}", ephemeral=True)

        select.callback = select_callback
        view = discord.ui.View(timeout=60).add_item(select)
        await interaction.response.send_message("Chọn kênh đích:", view=view, ephemeral=True)

    async def mute_voice_callback(self, interaction: discord.Interaction):
        action = not self.target.voice.mute
        await self.target.edit(mute=action, reason=f"Voice Mute bởi {interaction.user}")
        await interaction.response.send_message(f"🎤 Đã {'bật' if not action else 'tắt'} mic của {self.target.mention}.", ephemeral=True)

    async def deafen_voice_callback(self, interaction: discord.Interaction):
        action = not self.target.voice.deaf
        await self.target.edit(deafen=action, reason=f"Voice Deafen bởi {interaction.user}")
        await interaction.response.send_message(f"🎧 Đã {'bật' if not action else 'tắt'} âm thanh của {self.target.mention}.", ephemeral=True)

    async def blacklist_callback(self, interaction: discord.Interaction):
        if self.target.id in blacklist_users:
            return await interaction.response.send_message(t(interaction.guild, "USERPANEL_BLACKLIST_ALREADY"), ephemeral=True)
        blacklist_users.add(self.target.id)
        save_blacklist()
        await interaction.response.send_message(t(interaction.guild, "USERPANEL_BLACKLIST_ADD", mention=self.target.mention), ephemeral=True)

    async def unblacklist_callback(self, interaction: discord.Interaction):
        if self.target.id not in blacklist_users:
            return await interaction.response.send_message(t(interaction.guild, "USERPANEL_BLACKLIST_NOT_IN"), ephemeral=True)
        blacklist_users.remove(self.target.id)
        save_blacklist()
        await interaction.response.send_message(t(interaction.guild, "USERPANEL_BLACKLIST_REMOVE", mention=self.target.mention), ephemeral=True)

    async def confirm_and_execute(self, interaction: discord.Interaction, action: str, message: str):
        """Hàm chung cho các hành động cần xác nhận."""
        confirm_view = ConfirmView(interaction.user.id)
        await interaction.response.send_message(message, view=confirm_view, ephemeral=True)
        await confirm_view.wait()

        if confirm_view.value:
            try:
                if action == "kick":
                    await self.target.kick(reason=f"Kicked by {interaction.user}")
                    await interaction.followup.send(t(interaction.guild, "USERPANEL_KICK_DONE", mention=self.target.mention), ephemeral=True)
                elif action == "ban":
                    await self.target.ban(reason=f"Banned by {interaction.user}")
                    await interaction.followup.send(t(interaction.guild, "USERPANEL_BAN_DONE", mention=self.target.mention), ephemeral=True)
            except discord.Forbidden as e:
                await interaction.followup.send(f"❌ Lỗi: {e}", ephemeral=True)
        else:
            await interaction.followup.send(t(interaction.guild, "USERPANEL_CANCELLED"), ephemeral=True)


# --- COG CHÍNH ---

class UserPanelCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.hybrid_command(name="userpanel", aliases=["upanel"], description="Xem thông tin và quản lý thành viên.")
    @app_commands.describe(thanh_vien="Người bạn muốn xem.")
    @commands.has_permissions(kick_members=True) # Yêu cầu quyền tối thiểu để dùng lệnh
    async def user_panel(self, ctx: commands.Context, thanh_vien: discord.Member):
        """Hiển thị bảng điều khiển quản lý cho một thành viên."""
        
        # Tạo embed thông tin người dùng (tương tự lệnh userinfo)
        embed = discord.Embed(
            title=f"👤 Bảng điều khiển cho {thanh_vien.display_name}",
            color=thanh_vien.top_role.color if thanh_vien.top_role.color != discord.Color.default() else discord.Color.blue(),
            timestamp=datetime.utcnow()
        )
        embed.set_thumbnail(url=thanh_vien.display_avatar.url)
        embed.add_field(name="📝 Tên đầy đủ", value=f"`{thanh_vien}`", inline=True)
        embed.add_field(name="🆔 ID", value=f"`{thanh_vien.id}`", inline=True)
        embed.add_field(name="✨ Vai trò cao nhất", value=thanh_vien.top_role.mention, inline=False)
        embed.add_field(name="📅 Ngày tạo tài khoản", value=f"<t:{int(thanh_vien.created_at.timestamp())}:F>", inline=False)
        embed.add_field(name="🏠 Ngày tham gia server", value=f"<t:{int(thanh_vien.joined_at.timestamp())}:F>", inline=False)

        roles = [role.mention for role in reversed(thanh_vien.roles) if role.name != "@everyone"]
        role_list = ", ".join(roles[:10]) + ("..." if len(roles) > 10 else "")
        embed.add_field(name=f"🎭 Vai trò ({len(roles)})", value=role_list if roles else "Không có.", inline=False)

        try:
            from data.database import get_user_data
            udata = get_user_data(ctx.guild.id, thanh_vien.id)
            coins = udata.get("coins", 0)
            bank = udata.get("bank", 0)
            xu = udata.get("xu", 0)
            networth = coins + bank
            finance_str = f"🪙 **Ví:** `{coins:,}` coins | 🏦 **Ngân hàng:** `{bank:,}` coins\n✨ **Xu VIP:** `{xu:,}` xu | 💎 **Tổng tài sản:** `{networth:,}` coins"
            embed.add_field(name="💳 Thông Tin Tài Chính", value=finance_str, inline=False)
        except Exception:
            pass

        # Tạo và gửi view với các nút điều khiển
        view = UserPanelView(ctx.author, thanh_vien)
        await ctx.send(embed=embed, view=view, ephemeral=True)

    #@user_panel.error
    #async def user_panel_error(self, ctx: commands.Context, error):
        #if isinstance(error, commands.MissingPermissions):
            #await ctx.send("❌ Bạn không có quyền `Kick Members` để sử dụng lệnh này.", ephemeral=True)
        #else:
            #await ctx.send(f"Đã xảy ra lỗi: {error}", ephemeral=True)

async def setup(bot: commands.Bot):
    await bot.add_cog(UserPanelCog(bot))