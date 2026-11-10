from Check.i18n import t, is_vietnamese
import os
import json
import discord
from discord import app_commands
from discord.ext import commands

CONFIG_FILE = "data/rule.json"


def load_config() -> dict:
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except json.JSONDecodeError:
            return {}
    return {}


def save_config(data: dict):
    # Đảm bảo thư mục 'data' luôn tồn tại trước khi ghi file
    os.makedirs(os.path.dirname(CONFIG_FILE), exist_ok=True)
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)


class RuleVerificationView(discord.ui.View):
    def __init__(self, bot: commands.Bot, guild=None):
        super().__init__(timeout=None)
        self.bot = bot
        self.guild = guild
        if guild:
            vi = is_vietnamese(guild)
            self.verify_button.label = "Tôi đã đọc và đồng ý với nội quy" if vi else "I have read and agree to the rules" 

    @discord.ui.button(
        label="Tôi đã đọc và đồng ý với nội quy",
        style=discord.ButtonStyle.success,
        emoji="✅",
        custom_id="rules_verification_persistent_btn"
    )
    async def verify_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer(ephemeral=True)

        guild = interaction.guild
        member = interaction.user
        config = load_config()
        guild_id = str(guild.id)

        if guild_id not in config:
            await interaction.followup.send(
                "⚠️ Hệ thống nội quy trên server này chưa được cấu hình hoàn chỉnh.",
                ephemeral=True
            )
            return

        role_id = config[guild_id].get("role_id")
        role = guild.get_role(role_id) if role_id else None

        if not role:
            await interaction.followup.send(
                "❌ Không tìm thấy Role thành viên (có thể đã bị xóa). Vui lòng báo cho Admin!",
                ephemeral=True
            )
            return

        # Kiểm tra nếu thành viên đã có role từ trước
        if role in member.roles:
            await interaction.followup.send(
                "ℹ️ Bạn đã xác nhận nội quy và mở khóa server trước đó rồi!",
                ephemeral=True
            )
            return

        # Cấp role thành viên (chỉ tốn 1 API call duy nhất)
        try:
            await member.add_roles(role, reason="Đồng ý với nội quy server")
            await interaction.followup.send(
                f"🎉 **Xác nhận thành công!**\nBạn đã nhận được role {role.mention} và mở khóa toàn bộ các kênh trên server. Chúc bạn có trải nghiệm vui vẻ!",
                ephemeral=True
            )
        except discord.Forbidden:
            await interaction.followup.send(
                "❌ Bot không đủ quyền để cấp Role cho bạn (Role của Bot đang thấp hơn Role thành viên). Vui lòng báo Admin!",
                ephemeral=True
            )
        except discord.HTTPException:
            await interaction.followup.send(
                "❌ Đã xảy ra lỗi kết nối khi cấp quyền. Vui lòng thử lại sau giây lát!",
                ephemeral=True
            )


class RulesCog(commands.Cog, name="Rules"):
    """Hệ thống hiển thị nội quy, khóa/mở kênh và cấp quyền tự động chuẩn Role-based."""

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    async def cog_load(self):
        self.bot.add_view(RuleVerificationView(self.bot))

    def build_rules_embed(self, guild: discord.Guild) -> discord.Embed:
        icon_url = guild.icon.url if guild.icon else None

        embed = discord.Embed(
            title=f"——————❖ SERVER RULES: {guild.name.upper()} ❖——————",
            description=(
                "Chào mừng bạn đến với server! Bạn hiện chỉ thấy kênh nội quy này.\n"
                "Vui lòng đọc kỹ các quy định dưới đây và **nhấn nút xác nhận** để mở khóa toàn bộ server:\n"
            ),
            color=discord.Color.gold()
        )

        if icon_url:
            embed.set_thumbnail(url=icon_url)

        embed.add_field(
            name="👤 I. DANH TÍNH & TÀI KHOẢN",
            value=(
                "> **1.** Tên và ảnh đại diện của bạn phải phù hợp với **quy định chung của Discord**.\n"
                "> **2.** **Nghiêm cấm** sử dụng **acc clone** hoặc **giả danh** người khác trong server.\n"
                "> **3.** Không được đổi biệt danh bừa bãi không có lý do. Ai bị đổi biệt danh có thể liên hệ **ADMIN** để được đổi lại."
            ),
            inline=False
        )

        embed.add_field(
            name="💬 II. VĂN HÓA GIAO TIẾP & ỨNG XỬ",
            value=(
                "> **4.** **Không** công kích cá nhân, gây mâu thuẫn nội bộ hoặc cá nhân. Không gạ gẫm, quấy rối, xúc phạm những thành viên khác. Nói chung, đừng làm những gì khiến người khác khó chịu.\n"
                "> **5.** Khi chat, bạn **không** được chửi tục, sử dụng các từ ngữ tiêu cực.\n"
                "> **6.** Tôn trọng người lớn, hỗ trợ người nhỏ tuổi."
            ),
            inline=False
        )

        embed.add_field(
            name="🎮 III. KÊNH THẢO LUẬN & SỬ DỤNG BOT",
            value=(
                "> **7.** Yêu cầu các bạn thảo luận đúng chủ đề ở đúng kênh.\n"
                "> **8.** Hạn chế lạm dụng bot, việc này sẽ gây loãng server. Dùng bot đúng kênh dành cho bot.\n"
                "> **9.** Cần những sự giúp đỡ về game bạn đang chơi có thể ping **Support**.\n"
                "> **10.** Yêu cầu dùng bot đúng nơi, tránh tình trạng kênh này xọ kênh kia."
            ),
            inline=False
        )

        embed.add_field(
            name="🛡️ IV. AN TOÀN & THƯƠNG MẠI",
            value=(
                "> **11.** **Không** đăng những thứ liên quan đến NSFW, link virus rút gọn. **Nghiêm cấm** tất cả các hành động lừa đảo trong server.\n"
                "> **12.** Cấm mọi hình thức mua bán, trao đổi bằng tiền hay thứ gì đó có giá trị tương đương."
            ),
            inline=False
        )

        embed.add_field(
            name="⚖️ V. BAN QUẢN TRỊ & KHIẾU NẠI",
            value=(
                "> **13.** Không nên gây thù với nhóm role **ADMIN**.\n"
                "> **14.** Đừng ping **MOD, ADMIN** trừ khi có việc thật cần thiết.\n"
                "> **15.** Mọi quyết định của Mod, Admin là tuyệt đối. Việc lách luật không được khuyến khích.\n"
                "> **16.** Đừng ping `@everyone`, hay bất kỳ role nào khác. Trong trường hợp cần thiết, chỉ cần ping người cần đề cập.\n"
                "> **17.** Việc bạn bị xúc phạm, nhận thấy thành viên vi phạm luật lệ; hay bạn nhận các án phạt không thích đáng có thể khiếu nại cho **Admin, Mod**."
            ),
            inline=False
        )

        embed.set_footer(
            text="👉 Nhấn vào nút 'Tôi đã đọc và đồng ý với nội quy' bên dưới để mở khóa toàn bộ server!"
        )
        return embed

    @app_commands.command(
        name="setup_rules",
        description="Thiết lập bảng nội quy, tự động ẩn kênh với người mới và mở khóa qua Role"
    )
    @app_commands.describe(
        kenh="Kênh văn bản dùng để gửi bảng nội quy",
        role="Role cấp sau khi xác nhận (Bỏ trống nếu muốn bot tự tạo role mới)",
        dong_bo_kenh="Tự động ẩn tất cả các kênh hiện tại với @everyone và chỉ hiện cho Role này"
    )
    @app_commands.default_permissions(administrator=True)
    async def setup_rules(
        self,
        interaction: discord.Interaction,
        kenh: discord.TextChannel,
        role: discord.Role = None,
        dong_bo_kenh: bool = True
    ):
        await interaction.response.defer(ephemeral=True)
        guild = interaction.guild

        # 1. Kiểm tra quyền của Bot
        if not guild.me.guild_permissions.manage_channels or not guild.me.guild_permissions.manage_roles:
            await interaction.followup.send(
                "❌ Bot cần cả hai quyền **Quản lý kênh (Manage Channels)** và **Quản lý vai trò (Manage Roles)** để thiết lập!",
                ephemeral=True
            )
            return

        # 2. Xử lý Role xác nhận
        if role is None:
            try:
                role = await guild.create_role(
                    name="Thành Viên",
                    color=discord.Color.green(),
                    reason="Role tự động tạo bởi hệ thống nội quy"
                )
            except discord.HTTPException:
                await interaction.followup.send("❌ Không thể tự động tạo Role mới!", ephemeral=True)
                return
        else:
            if role >= guild.me.top_role:
                await interaction.followup.send(
                    f"❌ Role {role.mention} đang nằm cao hơn hoặc ngang bằng với Role của Bot! Vui lòng kéo Role của Bot lên cao hơn.",
                    ephemeral=True
                )
                return

        # 3. Cấu hình quyền cho kênh Rules (Ai cũng thấy, nhưng không được chat)
        try:
            await kenh.set_permissions(
                guild.default_role,
                view_channel=True,
                send_messages=False,
                send_messages_in_threads=False,
                create_public_threads=False,
                create_private_threads=False,
                add_reactions=False,
                read_message_history=True
            )
        except discord.Forbidden:
            await interaction.followup.send(
                f"❌ Bot không có đủ quyền để chỉnh sửa phân quyền tại kênh {kenh.mention}!",
                ephemeral=True
            )
            return

        # 4. Đồng bộ ẩn các kênh khác với @everyone và mở cho Role thành viên (Nếu bật)
        synced_count = 0
        if dong_bo_kenh:
            for channel in guild.channels:
                if channel.id == kenh.id:
                    continue
                
                # Bỏ qua các kênh hoặc danh mục vốn là kênh kín của Admin (đã ẩn với @everyone từ trước)
                default_ov = channel.overwrites_for(guild.default_role)
                if default_ov.view_channel is False:
                    continue

                try:
                    await channel.set_permissions(guild.default_role, view_channel=False)
                    await channel.set_permissions(role, view_channel=True)
                    synced_count += 1
                except (discord.Forbidden, discord.HTTPException):
                    continue

        # 5. Lưu cấu hình
        config = load_config()
        config[str(guild.id)] = {
            "channel_id": kenh.id,
            "role_id": role.id
        }
        save_config(config)

        # 6. Gửi bảng nội quy
        embed = self.build_rules_embed(guild)
        view = RuleVerificationView(self.bot, guild=guild)
        await kenh.send(embed=embed, view=view)

        sync_text = f"\n• **Kênh đã đồng bộ khóa `@everyone`:** {synced_count} kênh" if dong_bo_kenh else ""
        await interaction.followup.send(
            f"✅ **Đã thiết lập hệ thống nội quy thành công!**\n"
            f"• **Kênh nội quy:** {kenh.mention}\n"
            f"• **Role cấp sau xác nhận:** {role.mention}{sync_text}\n"
            f"• **Cơ chế:** Thành viên mới vào chỉ thấy kênh nội quy. Ngay khi bấm nút sẽ nhận được {role.mention} và mở khóa toàn bộ server tức thì!",
            ephemeral=True
        )


async def setup(bot: commands.Bot):
    await bot.add_cog(RulesCog(bot))
