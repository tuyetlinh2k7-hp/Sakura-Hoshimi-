import logging
import discord
from discord import app_commands
from discord.ext import commands

logger = logging.getLogger(__name__)

@app_commands.guild_only()
@app_commands.default_permissions(manage_roles=True)
class AutoRole(commands.GroupCog, group_name="autorole"):
    """Quản lý tính năng tự động gán vai trò khi thành viên mới vào server"""

    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.db = bot.db

    # --- HÀM HỖ TRỢ GÁN ROLE ---

    async def _assign_autorole(self, member: discord.Member):
        config = await self.db.get_config(member.guild.id)
        if not config:
            return

        target_role_id = config.get("bot") if member.bot else config.get("user")
        if not target_role_id:
            return

        role = member.guild.get_role(target_role_id)
        # is_assignable() kiểm tra tự động: không phải @everyone, không phải managed role, và thấp hơn top_role của Bot
        if not role or not role.is_assignable():
            return

        if role in member.roles:
            return

        try:
            await member.add_roles(role, reason="Auto-role: Thành viên mới tham gia")
        except (discord.Forbidden, discord.HTTPException) as e:
            logger.warning(f"Không thể gán auto-role tại guild {member.guild.id}: {e}")

    # --- LỆNH SLASH COMMANDS ---

    @app_commands.command(name="set", description="Cài đặt role tự động khi thành viên mới tham gia")
    @app_commands.describe(
        target="Đối tượng áp dụng (Người dùng hoặc Bot)",
        role="Role bạn muốn tự động gán"
    )
    @app_commands.choices(target=[
        app_commands.Choice(name="Người dùng (User)", value="user"),
        app_commands.Choice(name="Bot", value="bot")
    ])
    @app_commands.checks.has_permissions(manage_roles=True)
    async def set_role(self, interaction: discord.Interaction, target: app_commands.Choice[str], role: discord.Role):
        # 1. Kiểm tra role mặc định (@everyone) hoặc role tích hợp của hệ thống/bot
        if role.is_default() or role.managed:
            await interaction.response.send_message(
                f"❌ Không thể chọn role {role.mention} vì đây là role mặc định hoặc được quản lý bởi hệ thống/tích hợp.",
                ephemeral=True
            )
            return

        # 2. Kiểm tra thứ bậc role so với người dùng thực hiện lệnh (trừ chủ server)
        if interaction.user.id != interaction.guild.owner_id and role >= interaction.user.top_role:
            await interaction.response.send_message(
                f"❌ Lỗi thứ bậc: Bạn không thể thiết lập role {role.mention} cao hơn hoặc bằng role cao nhất của bạn.",
                ephemeral=True
            )
            return

        # 3. Kiểm tra thứ bậc role so với Bot
        if role >= interaction.guild.me.top_role:
            await interaction.response.send_message(
                f"❌ Lỗi thứ bậc: Role {role.mention} cao hơn hoặc bằng role cao nhất của Bot.",
                ephemeral=True
            )
            return

        await self.db.set_role(interaction.guild_id, target.value, role.id)
        await interaction.response.send_message(
            f"✅ Đã thiết lập tự động gán cho **{target.name}**: {role.mention}"
        )

    @app_commands.command(name="view", description="Xem cấu hình Auto-Role hiện tại của server")
    @app_commands.checks.has_permissions(manage_roles=True)
    async def view_config(self, interaction: discord.Interaction):
        config = await self.db.get_config(interaction.guild_id) or {}

        def format_role_status(role_id: int | None) -> str:
            if not role_id:
                return "*Chưa thiết lập*"
            role = interaction.guild.get_role(role_id)
            if not role:
                return f"⚠️ *Role đã bị xóa (ID: `{role_id}`)*"
            if not role.is_assignable():
                return f"⚠️ {role.mention} *(Bot không đủ quyền gán)*"
            return role.mention

        embed = discord.Embed(
            title=f"⚙️ Cấu hình Auto-Role: {interaction.guild.name}",
            color=discord.Color.blurple()
        )
        embed.add_field(name="👤 Người dùng", value=format_role_status(config.get("user")), inline=False)
        embed.add_field(name="🤖 Bot", value=format_role_status(config.get("bot")), inline=False)

        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="remove", description="Xóa cấu hình Auto-Role")
    @app_commands.describe(target="Đối tượng muốn gỡ bỏ thiết lập")
    @app_commands.choices(target=[
        app_commands.Choice(name="Người dùng (User)", value="user"),
        app_commands.Choice(name="Bot", value="bot")
    ])
    @app_commands.checks.has_permissions(manage_roles=True)
    async def remove_role(self, interaction: discord.Interaction, target: app_commands.Choice[str]):
        await self.db.set_role(interaction.guild_id, target.value, None)
        await interaction.response.send_message(f"🗑️ Đã hủy tự động gán role cho **{target.name}**.")

    # --- SỰ KIỆN THÀNH VIÊN THAM GIA & XÁC MINH ---

    @commands.Cog.listener()
    async def on_member_join(self, member: discord.Member):
        # Nếu thành viên đang chờ đồng ý quy tắc (Membership Screening), chưa gán role ngay
        if member.pending:
            return
        await self._assign_autorole(member)

    @commands.Cog.listener()
    async def on_member_update(self, before: discord.Member, after: discord.Member):
        # Gán role ngay khi thành viên vừa hoàn tất bước đồng ý quy tắc
        if before.pending and not after.pending:
            await self._assign_autorole(after)

    # --- XỬ LÝ LỖI PHÂN QUYỀN TRONG COG ---

    async def cog_app_command_error(self, interaction: discord.Interaction, error: app_commands.AppCommandError):
        if isinstance(error, app_commands.errors.MissingPermissions):
            msg = "❌ Bạn cần quyền **Quản lý vai trò (Manage Roles)** để thực hiện."
        else:
            logger.error(f"Lỗi trong AutoRole cog: {error}", exc_info=True)
            msg = "❌ Đã có lỗi xảy ra khi thực hiện lệnh."

        if interaction.response.is_done():
            await interaction.followup.send(msg, ephemeral=True)
        else:
            await interaction.response.send_message(msg, ephemeral=True)


async def setup(bot: commands.Bot):
    await bot.add_cog(AutoRole(bot))
