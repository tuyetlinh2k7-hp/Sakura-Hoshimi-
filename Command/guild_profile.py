from typing import Optional
import discord
from discord import app_commands
from discord.ext import commands

# Giới hạn dung lượng ảnh (10 MB) và các định dạng cho phép
MAX_FILE_SIZE_BYTES = 10 * 1024 * 1024
ALLOWED_IMAGE_TYPES = {"image/png", "image/jpeg", "image/gif", "image/webp"}


class GuildProfile(commands.Cog):
    """Cog quản lý hồ sơ của bot (tên, avatar, banner, bio) theo từng máy chủ."""

    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    async def _validate_and_read_image(
        self, interaction: discord.Interaction, attachment: discord.Attachment, label: str
    ) -> Optional[bytes]:
        """Hàm phụ trợ kiểm tra định dạng, dung lượng và đọc bytes từ ảnh."""
        if not attachment.content_type or attachment.content_type.lower() not in ALLOWED_IMAGE_TYPES:
            await interaction.followup.send(
                f"❌ Định dạng **{label}** không hợp lệ! Vui lòng chọn ảnh PNG, JPG, GIF hoặc WebP.",
                ephemeral=True
            )
            return None

        if attachment.size > MAX_FILE_SIZE_BYTES:
            await interaction.followup.send(
                f"❌ Dung lượng **{label}** quá lớn! Vui lòng chọn ảnh dưới 10MB.",
                ephemeral=True
            )
            return None

        return await attachment.read()

    # --- NHÓM LỆNH SLASH /profile (Tối ưu hóa Slash Commands) ---
    profile_group = app_commands.Group(name="profile", description="Quản lý hồ sơ Bot và trang Bio Profile cá nhân")

    @profile_group.command(
        name="set",
        description="Tùy chỉnh hồ sơ của bot (tên, avatar, banner, bio) riêng cho máy chủ này"
    )
    @app_commands.guild_only()
    @app_commands.default_permissions(manage_guild=True)
    @app_commands.checks.has_permissions(manage_guild=True)
    @app_commands.checks.bot_has_permissions(change_nickname=True)
    @app_commands.checks.cooldown(2, 300.0, key=lambda i: i.guild_id)  # Tối đa 2 lần / 5 phút mỗi server
    @app_commands.describe(
        ten="Biệt danh mới của bot (1 - 32 ký tự)",
        avatar="Ảnh đại diện mới (PNG, JPG, GIF, WebP - tối đa 10MB)",
        banner="Ảnh bìa mới của bot (PNG, JPG, GIF, WebP - tối đa 10MB)",
        bio="Giới thiệu ngắn (Bio) của bot trong máy chủ (tối đa 190 ký tự)"
    )
    async def set_profile(
        self,
        interaction: discord.Interaction,
        ten: Optional[app_commands.Range[str, 1, 32]] = None,
        avatar: Optional[discord.Attachment] = None,
        banner: Optional[discord.Attachment] = None,
        bio: Optional[app_commands.Range[str, 1, 190]] = None
    ) -> None:
        if not interaction.guild or not interaction.guild.me:
            return

        # Kiểm tra nếu người dùng không truyền bất kỳ tham số nào
        if all(param is None for param in (ten, avatar, banner, bio)):
            await interaction.response.send_message(
                "⚠️ Bạn cần cung cấp ít nhất một thông tin (tên, avatar, banner hoặc bio) để cập nhật!",
                ephemeral=True
            )
            return

        await interaction.response.defer(ephemeral=True, thinking=True)

        edit_kwargs = {
            "reason": f"Cập nhật hồ sơ bởi {interaction.user} (ID: {interaction.user.id})"
        }
        updated_fields = []

        # 1. Xử lý Tên (Nickname)
        if ten is not None:
            edit_kwargs["nick"] = ten
            updated_fields.append(("🏷️ Tên mới", f"`{ten}`", True))

        # 2. Xử lý Bio
        if bio is not None:
            edit_kwargs["bio"] = bio
            updated_fields.append(("📝 Tiểu sử (Bio)", bio, False))

        # 3. Xử lý Avatar
        if avatar is not None:
            avatar_bytes = await self._validate_and_read_image(interaction, avatar, "Avatar")
            if avatar_bytes is None:
                return
            edit_kwargs["avatar"] = avatar_bytes
            updated_fields.append(("🖼️ Avatar", "Đã cập nhật", True))

        # 4. Xử lý Banner
        if banner is not None:
            banner_bytes = await self._validate_and_read_image(interaction, banner, "Banner")
            if banner_bytes is None:
                return
            edit_kwargs["banner"] = banner_bytes
            updated_fields.append(("🚩 Banner", "Đã cập nhật", True))

        try:
            # Gọi API cập nhật một lần duy nhất
            await interaction.guild.me.edit(**edit_kwargs)

            embed = discord.Embed(
                title="✅ Cập Nhật Hồ Sơ Thành Công",
                description=f"Hồ sơ của bot tại **{interaction.guild.name}** đã được làm mới.",
                color=discord.Color.green()
            )
            for name, value, inline in updated_fields:
                embed.add_field(name=name, value=value, inline=inline)

            if avatar:
                embed.set_thumbnail(url=avatar.url)
            if banner:
                embed.set_image(url=banner.url)

            embed.set_footer(text=f"Thực hiện bởi {interaction.user.display_name}")
            await interaction.followup.send(embed=embed, ephemeral=True)

        except discord.HTTPException as err:
            if err.status == 429:
                await interaction.followup.send(
                    "⏳ Bot đang bị Discord giới hạn tốc độ (Rate Limit) đổi hồ sơ. Vui lòng thử lại sau ít phút!",
                    ephemeral=True
                )
            else:
                await interaction.followup.send(
                    f"❌ Lỗi từ Discord API ({err.status}): {err.text}",
                    ephemeral=True
                )

    @profile_group.command(
        name="reset",
        description="Khôi phục hồ sơ của bot trong máy chủ này về mặc định ban đầu"
    )
    @app_commands.guild_only()
    @app_commands.default_permissions(manage_guild=True)
    @app_commands.checks.has_permissions(manage_guild=True)
    @app_commands.checks.bot_has_permissions(change_nickname=True)
    async def reset_profile(self, interaction: discord.Interaction) -> None:
        if not interaction.guild or not interaction.guild.me:
            return

        await interaction.response.defer(ephemeral=True, thinking=True)

        try:
            await interaction.guild.me.edit(
                nick=None,
                avatar=None,
                banner=None,
                bio=None,
                reason=f"Khôi phục mặc định bởi {interaction.user} (ID: {interaction.user.id})"
            )
            await interaction.followup.send(
                "✅ Đã khôi phục tên, avatar, banner và bio của bot về mặc định gốc!",
                ephemeral=True
            )
        except discord.HTTPException as err:
            await interaction.followup.send(
                f"❌ Không thể khôi phục hồ sơ ({err.status}): {err.text}",
                ephemeral=True
            )

    @profile_group.command(
        name="view",
        description="🌸 Xem danh sách Bio Profile cá nhân & liên kết mạng xã hội của Sakura"
    )
    @app_commands.describe(
        username="Tên người dùng (slug username) cần xem hồ sơ (để trống để mở danh sách hồ sơ)"
    )
    async def view_profile(
        self,
        interaction: discord.Interaction,
        username: Optional[str] = None
    ) -> None:
        web_base = "http://sakurabot.wispbyte.org:10272"
        from pathlib import Path
        import json
        profiles_file = Path("data/profiles.json")
        profiles = {}
        if profiles_file.exists():
            try:
                profiles = json.loads(profiles_file.read_text(encoding="utf-8"))
            except Exception:
                profiles = {}

        if username:
            slug = username.strip().lower()
            prof = profiles.get(slug)
            if not prof:
                return await interaction.response.send_message(
                    f"⚠️ Không tìm thấy hồ sơ với username `@{slug}`! Bạn có thể xem toàn bộ hồ sơ tại [Sakura Profiles]({web_base}/profile) hoặc tạo hồ sơ mới tại [Tạo Profile]({web_base}/add-profile).",
                    ephemeral=True
                )

            name = prof.get("name", slug)
            bio = prof.get("bio") or prof.get("tagline") or "Chưa có tiểu sử."
            avatar = prof.get("avatar") or (guild.me.display_avatar.url if guild and guild.me else "https://cdn.discordapp.com/avatars/1504825128499019807/dea9d2725b620317b25b9da8f36d129a?size=256")
            banner = prof.get("banner")
            verified_badge = " ✓ (Đã xác minh)" if prof.get("verified") else ""

            embed = discord.Embed(
                title=f"🌸 Hồ Sơ: {name}{verified_badge}",
                description=f"**@{slug}**\n\n{bio}",
                color=discord.Color.from_rgb(255, 121, 198),
                url=f"{web_base}/{slug}/profile"
            )
            embed.set_thumbnail(url=avatar)
            if banner:
                embed.set_image(url=banner)

            links_count = len(prof.get("links", []))
            socials_count = len([v for v in prof.get("socials", {}).values() if v])
            embed.add_field(name="🔗 Liên kết & Mạng xã hội", value=f"• **{links_count}** liên kết đính kèm\n• **{socials_count}** tài khoản mạng xã hội", inline=True)

            # Trạng thái Minecraft Plugin & Hôn nhân
            status_lines = []
            target_uid = prof.get("user_id") or prof.get("discord_id") or prof.get("owner_id")
            if not target_uid and slug.isdigit():
                target_uid = int(slug)

            if target_uid:
                try:
                    import mc_link_system
                    mc = mc_link_system.get_linked_account(int(target_uid))
                    if mc and mc.get("minecraft_name"):
                        status_lines.append(f"🎮 **Minecraft Plugin:** `{mc['minecraft_name']}` (Đã liên kết)")
                    else:
                        status_lines.append("🎮 **Minecraft Plugin:** *Chưa liên kết*")
                except Exception:
                    pass

                try:
                    import time
                    from Command.command_fishing import fishing_state, UTILITY_ITEMS
                    couples = fishing_state.get("couples", {}) if fishing_state else {}
                    t_int = int(target_uid)
                    found_marriage = False
                    for k, c in couples.items():
                        a, b = int(c.get("a", 0)), int(c.get("b", 0))
                        if t_int in (a, b):
                            partner_id = b if t_int == a else a
                            ring_name = UTILITY_ITEMS.get(c.get("ring", "ring_bronze"), {}).get("name", "💍 Nhẫn Cưới")
                            days = int((time.time() - c.get("married_at", 0)) // 86400) if c.get("married_at") else 0
                            status_lines.append(f"💍 **Hôn Nhân:** Đã kết hôn cùng <@{partner_id}> ({days} ngày) • {ring_name} • {c.get('affection', 0)} 💖")
                            found_marriage = True
                            break
                    if not found_marriage:
                        status_lines.append("💍 **Hôn Nhân:** *Đang độc thân*")
                except Exception:
                    pass

            if status_lines:
                embed.add_field(name="✨ Trạng Thái Thành Viên", value="\n".join(status_lines), inline=False)

            embed.set_footer(text="Sakura Bio Profiles • Nhấn nút bên dưới để mở trang hồ sơ đầy đủ")

            view = discord.ui.View()
            view.add_item(discord.ui.Button(label="👁️ Xem Trang Profile", url=f"{web_base}/{slug}/profile", style=discord.ButtonStyle.link))
            view.add_item(discord.ui.Button(label="🌐 Khám Phá Thêm Profiles", url=f"{web_base}/profile", style=discord.ButtonStyle.link))
            return await interaction.response.send_message(embed=embed, view=view)

        # Xem danh mục hồ sơ tổng hợp
        total_count = len(profiles)
        caller_status = []
        try:
            import mc_link_system
            mc = mc_link_system.get_linked_account(interaction.user.id)
            if mc and mc.get("minecraft_name"):
                caller_status.append(f"🎮 Minecraft: `{mc['minecraft_name']}` (Đã liên kết)")
            else:
                caller_status.append("🎮 Minecraft: *Chưa liên kết*")
        except Exception:
            pass

        try:
            import time
            from Command.command_fishing import fishing_state, UTILITY_ITEMS
            couples = fishing_state.get("couples", {}) if fishing_state else {}
            u_int = interaction.user.id
            m_found = False
            for k, c in couples.items():
                a, b = int(c.get("a", 0)), int(c.get("b", 0))
                if u_int in (a, b):
                    partner_id = b if u_int == a else a
                    ring_name = UTILITY_ITEMS.get(c.get("ring", "ring_bronze"), {}).get("name", "💍 Nhẫn Cưới")
                    days = int((time.time() - c.get("married_at", 0)) // 86400) if c.get("married_at") else 0
                    caller_status.append(f"💍 Hôn nhân: Đã kết hôn cùng <@{partner_id}> ({days} ngày) • {ring_name} • {c.get('affection', 0)} 💖")
                    m_found = True
                    break
            if not m_found:
                caller_status.append("💍 Hôn nhân: *Độc thân*")
        except Exception:
            pass
        embed = discord.Embed(
            title="🌸 SAKURA BIO PROFILES • DANH MỤC HỒ SƠ",
            description=(
                "Nền tảng hồ sơ liên kết cá nhân (Sakura Bio phong cách hiện đại)!\n\n"
                "Danh mục hồ sơ được phân chia rõ ràng thành 2 khu vực:\n"
                "• 👤 **Hồ sơ của bạn (Của mình):** Quản lý, chỉnh sửa và nhận liên kết chia sẻ của riêng bạn.\n"
                "• 🌐 **Hồ sơ cộng đồng (Của người khác):** Khám phá các hồ sơ thành viên, link mạng xã hội và donate.\n\n"
                f"📊 Hiện có **{total_count} hồ sơ** đang hoạt động trên hệ sinh thái Sakura."
            ),
            color=discord.Color.from_rgb(123, 223, 242)
        )
        if caller_status:
            embed.add_field(name="👤 Trạng Thái Của Bạn", value="\n".join(caller_status), inline=False)
        embed.set_thumbnail(url=guild.me.display_avatar.url if (guild and guild.me) else "https://cdn.discordapp.com/avatars/1504825128499019807/dea9d2725b620317b25b9da8f36d129a?size=256")
        embed.set_footer(text="Bấm các nút bên dưới để mở danh sách hồ sơ hoặc tạo hồ sơ của riêng bạn")

        view = discord.ui.View()
        view.add_item(discord.ui.Button(label="🌐 Danh Sách Hồ Sơ (/profile)", url=f"{web_base}/profile", style=discord.ButtonStyle.link))
        view.add_item(discord.ui.Button(label="➕ Tạo Hồ Sơ Của Bạn", url=f"{web_base}/add-profile", style=discord.ButtonStyle.link))
        await interaction.response.send_message(embed=embed, view=view)

    # Xử lý lỗi chung cho các lệnh trong Cog
    async def cog_app_command_error(
        self,
        interaction: discord.Interaction,
        error: app_commands.AppCommandError
    ) -> None:
        if isinstance(error, app_commands.MissingPermissions):
            msg = "🚫 Bạn cần có quyền **Quản lý máy chủ (Manage Server)** để dùng lệnh này."
        elif isinstance(error, app_commands.BotMissingPermissions):
            msg = "🚫 Bot đang thiếu quyền **Thay đổi biệt danh (Change Nickname)**."
        elif isinstance(error, app_commands.CommandOnCooldown):
            msg = f"⏳ Lệnh đang trong thời gian hồi. Vui lòng thử lại sau **{int(error.retry_after)} giây**."
        else:
            msg = f"❌ Lỗi thực thi lệnh: {error}"

        if interaction.response.is_done():
            await interaction.followup.send(msg, ephemeral=True)
        else:
            await interaction.response.send_message(msg, ephemeral=True)


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(GuildProfile(bot))
