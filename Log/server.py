import io
import asyncio
from collections import defaultdict
import discord
from discord.ext import commands

from Check.data import server_log_channels
from Check.i18n import t


class ServerLog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        # Hàng đợi chống spam khi chỉnh sửa kênh liên tiếp: {channel_id: dict_info}
        self.channel_update_queues: dict[int, dict] = {}
        self.channel_update_tasks: dict[int, asyncio.Task] = {}
        self.UPDATE_DELAY = 3.5

        # Theo dõi xóa kênh hàng loạt (Anti-Nuke): {guild_id: list[timestamp]}
        self.delete_tracker: dict[int, list[float]] = defaultdict(list)

        # Danh sách ID danh mục muốn bỏ qua log tạo/xóa kênh tự động (Ticket / Temp Voice)
        # Bạn có thể thêm ID category vào tập hợp này nếu cần
        self.ignored_category_ids: set[int] = set()

    def cog_unload(self):
        for task in self.channel_update_tasks.values():
            task.cancel()

    # =========================================================================
    # CÁC HÀM PHỤ TRỢ (HELPER FUNCTIONS)
    # =========================================================================

    @staticmethod
    def _format_duration(seconds: int) -> str:
        """Chuyển đổi số giây sang định dạng dễ đọc (phút/giờ)."""
        if seconds == 0:
            return "Tắt (0s)"
        hours, remainder = divmod(seconds, 3600)
        minutes, secs = divmod(remainder, 60)
        parts = []
        if hours:
            parts.append(f"{hours} giờ")
        if minutes:
            parts.append(f"{minutes} phút")
        if secs:
            parts.append(f"{secs} giây")
        return f"{' '.join(parts)} (`{seconds}s`)"

    @staticmethod
    def _truncate(text: str | None, max_len: int = 450) -> str:
        if not text:
            return ""
        return text[: max_len - 3] + "..." if len(text) > max_len else text

    async def _get_audit_executor(
        self,
        guild: discord.Guild,
        actions: list[discord.AuditLogAction] | discord.AuditLogAction,
        target_id: int | None = None,
        delay: float = 1.0
    ) -> discord.abc.User | None:
        """
        Truy vấn Audit Log an toàn, kiểm tra quyền hạn và độ trễ thời gian (< 25s).
        Hỗ trợ kiểm tra 1 hoặc nhiều AuditLogAction.
        """
        if not guild.me or not guild.me.guild_permissions.view_audit_log:
            return None

        if delay > 0:
            await asyncio.sleep(delay)

        if isinstance(actions, discord.AuditLogAction):
            actions = [actions]

        now = discord.utils.utcnow()
        try:
            async for entry in guild.audit_logs(limit=8):
                if entry.action in actions:
                    if target_id is None or (entry.target and entry.target.id == target_id):
                        if (now - entry.created_at).total_seconds() <= 25:
                            return entry.user
        except (discord.Forbidden, discord.HTTPException, discord.errors.DiscordServerError):
            pass
        except Exception:
            pass

        return None

    def _format_overwrites_diff(
        self,
        before_ow: dict[discord.Role | discord.Member | discord.Object, discord.PermissionOverwrite],
        after_ow: dict[discord.Role | discord.Member | discord.Object, discord.PermissionOverwrite]
    ) -> str:
        """Phân tích chi tiết sự thay đổi quyền hạn (Overwrites) của Role/Member trong kênh."""
        lines = []
        all_targets = set(before_ow.keys()) | set(after_ow.keys())

        for target in all_targets:
            target_name = target.mention if hasattr(target, "mention") else f"ID: `{target.id}`"
            b_perm = before_ow.get(target)
            a_perm = after_ow.get(target)

            if b_perm is None and a_perm is not None:
                lines.append(f"➕ **Thêm phân quyền cho {target_name}**")
                b_perm = discord.PermissionOverwrite()
            elif a_perm is None and b_perm is not None:
                lines.append(f"➖ **Xóa phân quyền của {target_name}**")
                continue

            if b_perm and a_perm:
                b_dict = dict(iter(b_perm))
                a_dict = dict(iter(a_perm))
                perm_changes = []

                for perm_name, a_val in a_dict.items():
                    b_val = b_dict.get(perm_name)
                    if b_val != a_val:
                        fmt = {True: "✅", False: "❌", None: "➖"}
                        perm_changes.append(f"  • `{perm_name}`: {fmt[b_val]} ➜ {fmt[a_val]}")

                if perm_changes:
                    lines.append(f"⚙️ **{target_name}:**\n" + "\n".join(perm_changes[:8]))
                    if len(perm_changes) > 8:
                        lines.append(f"  *(...và {len(perm_changes) - 8} quyền khác)*")

        result = "\n".join(lines)
        return self._truncate(result, 1000) if result else ""

    def _generate_channel_blueprint(self, channel: discord.abc.GuildChannel) -> discord.File:
        """Xuất file .txt chứa toàn bộ cấu hình và phân quyền của kênh trước khi bị xóa."""
        lines = [
            f"=== BẢN THIẾT KẾ KÊNH ĐÃ XÓA (CHANNEL BLUEPRINT) ===",
            f"Tên kênh: {channel.name} (ID: {channel.id})",
            f"Loại kênh: {channel.type}",
            f"Danh mục: {channel.category.name if channel.category else 'Không có'}",
            f"Vị trí (Position): {channel.position}",
            f"Ngày tạo: {channel.created_at.strftime('%Y-%m-%d %H:%M:%S UTC')}",
        ]

        if hasattr(channel, "topic") and channel.topic:
            lines.append(f"\n[Chủ đề kênh (Topic)]:\n{channel.topic}")
        if hasattr(channel, "slowmode_delay"):
            lines.append(f"Chế độ chậm (Slowmode): {channel.slowmode_delay}s")
        if hasattr(channel, "nsfw"):
            lines.append(f"NSFW: {channel.nsfw}")
        if hasattr(channel, "bitrate"):
            lines.append(f"Bitrate: {channel.bitrate // 1000} kbps")
        if hasattr(channel, "user_limit"):
            lines.append(f"Giới hạn người: {channel.user_limit}")

        lines.append("\n=== BẢNG PHÂN QUYỀN (PERMISSION OVERWRITES) ===")
        if not channel.overwrites:
            lines.append("Không có phân quyền riêng.")
        else:
            for target, ow in channel.overwrites.items():
                t_type = "Role" if isinstance(target, discord.Role) else "Member"
                t_name = getattr(target, "name", str(target.id))
                allow, deny = ow.pair()
                allowed_list = [perm for perm, val in allow if val]
                denied_list = [perm for perm, val in deny if val]
                lines.append(f"\n• [{t_type}] {t_name} (ID: {target.id}):")
                if allowed_list:
                    lines.append(f"  ✅ Cho phép: {', '.join(allowed_list)}")
                if denied_list:
                    lines.append(f"  ❌ Cấm: {', '.join(denied_list)}")

        return discord.File(
            fp=io.BytesIO("\n".join(lines).encode("utf-8")),
            filename=f"channel_blueprint_{channel.id}.txt"
        )

    # =========================================================================
    # 1. SỰ KIỆN THÊM / GỠ BOT KHỎI SERVER
    # =========================================================================

    async def _send_owner_guild_join_dm(self, guild: discord.Guild):
        """Gửi thông báo DM cho Bot Owner khi tham gia server (có fallback tự thân)."""
        try:
            from Check.owner_notifier import notify_owner_guild_join
            await notify_owner_guild_join(self.bot, guild)
            return
        except (ImportError, AttributeError):
            pass
        except Exception as e:
            print(f"[ServerLog] ⚠️ Lỗi gọi notify_owner_guild_join: {e}")

        # Fallback trực tiếp nếu file Check/owner_notifier.py chưa đồng bộ trên host
        try:
            from config import OWNER_ID
        except Exception:
            OWNER_ID = 1144785664458637394

        if not OWNER_ID:
            return

        try:
            owner = self.bot.get_user(OWNER_ID) or await self.bot.fetch_user(OWNER_ID)
            if not owner:
                return

            embed = discord.Embed(
                title="📥 SAKURABOT: THAM GIA MÁY CHỦ MỚI!",
                description=f"Bot vừa được thêm vào một máy chủ mới: **{guild.name}**",
                color=0x2ECC71,
                timestamp=discord.utils.utcnow()
            )
            if guild.icon:
                embed.set_thumbnail(url=guild.icon.url)
            elif self.bot.user and self.bot.user.display_avatar:
                embed.set_thumbnail(url=self.bot.user.display_avatar.url)

            server_owner_str = f"<@{guild.owner_id}> (`{guild.owner_id}`)" if guild.owner_id else "Không rõ"
            embed.add_field(name="🏠 Thông Tin Máy Chủ", value=f"• Tên: **{guild.name}**\n• ID: `{guild.id}`", inline=False)
            embed.add_field(name="👑 Chủ Sở Hữu (Server Owner)", value=server_owner_str, inline=True)
            embed.add_field(name="👥 Thành Viên", value=f"**{guild.member_count or len(guild.members):,}**", inline=True)
            embed.add_field(name="📊 Tổng Số Server", value=f"Đang phục vụ: **{len(self.bot.guilds):,}** máy chủ", inline=False)
            embed.set_footer(text="SakuraBot Guild Sentinel")
            await owner.send(embed=embed)
            print(f"[ServerLog] 📨 [Fallback] Đã gửi DM thông báo Bot tham gia server '{guild.name}' tới Owner.")
        except Exception as err:
            print(f"[ServerLog] ⚠️ Fallback gửi DM Guild Join thất bại: {err}")

    async def _send_owner_guild_remove_dm(self, guild: discord.Guild):
        """Gửi thông báo DM cho Bot Owner khi rời server (có fallback tự thân)."""
        try:
            from Check.owner_notifier import notify_owner_guild_remove
            await notify_owner_guild_remove(self.bot, guild)
            return
        except (ImportError, AttributeError):
            pass
        except Exception as e:
            print(f"[ServerLog] ⚠️ Lỗi gọi notify_owner_guild_remove: {e}")

        # Fallback trực tiếp
        try:
            from config import OWNER_ID
        except Exception:
            OWNER_ID = 1144785664458637394

        if not OWNER_ID:
            return

        try:
            owner = self.bot.get_user(OWNER_ID) or await self.bot.fetch_user(OWNER_ID)
            if not owner:
                return

            embed = discord.Embed(
                title="📤 SAKURABOT: RỜI KHỎI MÁY CHỦ",
                description=f"Bot vừa rời khỏi hoặc bị xóa khỏi máy chủ: **{guild.name}**",
                color=0xED4245,
                timestamp=discord.utils.utcnow()
            )
            if guild.icon:
                embed.set_thumbnail(url=guild.icon.url)
            embed.add_field(name="🏠 Máy Chủ", value=f"• Tên: **{guild.name}**\n• ID: `{guild.id}`", inline=False)
            embed.add_field(name="📊 Máy Chủ Còn Lại", value=f"Hiện còn: **{len(self.bot.guilds):,}** máy chủ", inline=False)
            embed.set_footer(text="SakuraBot Guild Sentinel")
            await owner.send(embed=embed)
            print(f"[ServerLog] 📨 [Fallback] Đã gửi DM thông báo Bot rời server '{guild.name}' tới Owner.")
        except Exception as err:
            print(f"[ServerLog] ⚠️ Fallback gửi DM Guild Remove thất bại: {err}")

    @commands.Cog.listener()
    async def on_guild_join(self, guild: discord.Guild):
        # Gửi thông báo DM chi tiết tới Bot Owner
        await self._send_owner_guild_join_dm(guild)
        print(
            f"[+] Bot đã được thêm vào server mới: {guild.name} (ID: {guild.id}) "
            f"- Chủ sở hữu: {guild.owner} (ID: {guild.owner_id})"
        )

        target_channel = guild.system_channel

        def _can_send_embed(ch: discord.TextChannel) -> bool:
            if not ch or not guild.me:
                return False
            perms = ch.permissions_for(guild.me)
            return perms.view_channel and perms.send_messages and perms.embed_links

        if target_channel is None or not _can_send_embed(target_channel):
            target_channel = None
            for ch in guild.text_channels:
                if _can_send_embed(ch):
                    target_channel = ch
                    break

        if target_channel:
            embed_guild = discord.Embed(
                title=t(guild, "LOG_SERVER_WELCOME_TITLE"),
                description=t(guild, "LOG_SERVER_WELCOME_DESC"),
                color=discord.Color.from_rgb(255, 121, 198),
                timestamp=discord.utils.utcnow()
            )
            embed_guild.add_field(
                name=t(guild, "LOG_SERVER_WELCOME_FIELD_MOD"),
                value=t(guild, "LOG_SERVER_WELCOME_FIELD_MOD_VAL"),
                inline=False
            )
            embed_guild.add_field(
                name=t(guild, "LOG_SERVER_WELCOME_FIELD_ECO"),
                value=t(guild, "LOG_SERVER_WELCOME_FIELD_ECO_VAL"),
                inline=False
            )
            embed_guild.add_field(
                name=t(guild, "LOG_SERVER_WELCOME_FIELD_GUIDE"),
                value=t(guild, "LOG_SERVER_WELCOME_FIELD_GUIDE_VAL"),
                inline=False
            )
            if self.bot.user and self.bot.user.display_avatar:
                embed_guild.set_thumbnail(url=self.bot.user.display_avatar.url)
            embed_guild.set_footer(text=t(guild, "LOG_SERVER_WELCOME_FOOTER"))

            # View nút liên kết hữu ích (Link buttons)
            class ServerWelcomeView(discord.ui.View):
                def __init__(self):
                    super().__init__(timeout=None)
                    self.add_item(discord.ui.Button(label="🌐 Web Dashboard", url="https://sakurabot.wispbyte.org/dashboard", style=discord.ButtonStyle.link))
                    self.add_item(discord.ui.Button(label="📖 Hỗ Trợ & Mời Bot", url="https://sakurabot.wispbyte.org/support", style=discord.ButtonStyle.link))

            try:
                await target_channel.send(embed=embed_guild, view=ServerWelcomeView())
            except (discord.Forbidden, discord.HTTPException):
                try:
                    fallback_text = (
                        f"🌸 **Xin chào {guild.name}!** Cảm ơn bạn đã mời **Sakura Bot**!\n"
                        f"• Dùng `/menu` hoặc `s!menu` để xem toàn bộ danh sách lệnh.\n"
                        f"• Quản lý trực quan trên Web: https://sakurabot.wispbyte.org"
                    )
                    await target_channel.send(fallback_text)
                except Exception:
                    pass

    @commands.Cog.listener()
    async def on_guild_remove(self, guild: discord.Guild):
        # Gửi thông báo DM chi tiết tới Bot Owner
        await self._send_owner_guild_remove_dm(guild)
        print(f"[-] Bot đã rời khỏi hoặc bị xóa khỏi server: {guild.name} (ID: {guild.id})")

    # =========================================================================
    # 2. SỰ KIỆN CẬP NHẬT CÀI ĐẶT SERVER (ON_GUILD_UPDATE)
    # =========================================================================

    @commands.Cog.listener()
    async def on_guild_update(self, before: discord.Guild, after: discord.Guild):
        guild = after
        guild_id = str(guild.id)

        if guild_id not in server_log_channels:
            return

        channel = after.get_channel(server_log_channels[guild_id])
        if channel is None:
            return

        embed = discord.Embed(
            title=t(guild, "LOG_SERVER_UPDATED_TITLE"),
            color=discord.Color.gold(),
            timestamp=discord.utils.utcnow()
        )

        changed = False
        saved_files: list[discord.File] = []

        if before.name != after.name:
            embed.add_field(
                name=t(guild, "LOG_SERVER_FIELD_NAME"),
                value=f"`{before.name}` ➜ `{after.name}`",
                inline=False
            )
            changed = True

        if before.description != after.description:
            b_desc = self._truncate(before.description, 400) or t(guild, "LOG_SERVER_NONE")
            a_desc = self._truncate(after.description, 400) or t(guild, "LOG_SERVER_NONE")
            embed.add_field(
                name=t(guild, "LOG_SERVER_FIELD_DESC"),
                value=t(guild, "LOG_SERVER_FIELD_DESC_VALUE", before=b_desc, after=a_desc),
                inline=False
            )
            changed = True

        if before.icon != after.icon:
            embed.add_field(
                name=t(guild, "LOG_SERVER_FIELD_ICON"),
                value=t(guild, "LOG_SERVER_FIELD_ICON_VALUE"),
                inline=False
            )
            if after.icon:
                embed.set_thumbnail(url=after.icon.url)
            # Cứu lại file Icon cũ trước khi bị CDN xóa
            if before.icon:
                try:
                    old_icon_file = await before.icon.to_file(filename="old_server_icon.png")
                    saved_files.append(old_icon_file)
                except (discord.HTTPException, discord.NotFound):
                    pass
            changed = True

        if before.banner != after.banner:
            embed.add_field(
                name=t(guild, "LOG_SERVER_FIELD_BANNER"),
                value=t(guild, "LOG_SERVER_FIELD_BANNER_VALUE"),
                inline=False
            )
            if after.banner:
                embed.set_image(url=after.banner.url)
            if before.banner:
                try:
                    old_banner_file = await before.banner.to_file(filename="old_server_banner.png")
                    saved_files.append(old_banner_file)
                except (discord.HTTPException, discord.NotFound):
                    pass
            changed = True

        if before.splash != after.splash:
            embed.add_field(
                name=t(guild, "LOG_SERVER_FIELD_SPLASH"),
                value=t(guild, "LOG_SERVER_FIELD_SPLASH_VALUE"),
                inline=False
            )
            changed = True

        if before.afk_channel != after.afk_channel:
            embed.add_field(
                name=t(guild, "LOG_SERVER_FIELD_AFK_CHANNEL"),
                value=f"{before.afk_channel.mention if before.afk_channel else t(guild, 'LOG_SERVER_NONE')} ➜ "
                      f"{after.afk_channel.mention if after.afk_channel else t(guild, 'LOG_SERVER_NONE')}",
                inline=True
            )
            changed = True

        if before.afk_timeout != after.afk_timeout:
            embed.add_field(
                name=t(guild, "LOG_SERVER_FIELD_AFK_TIMEOUT"),
                value=f"{self._format_duration(before.afk_timeout)} ➜ {self._format_duration(after.afk_timeout)}",
                inline=True
            )
            changed = True

        if before.system_channel != after.system_channel:
            embed.add_field(
                name=t(guild, "LOG_SERVER_FIELD_SYSTEM_CHANNEL"),
                value=f"{before.system_channel.mention if before.system_channel else t(guild, 'LOG_SERVER_NONE')} ➜ "
                      f"{after.system_channel.mention if after.system_channel else t(guild, 'LOG_SERVER_NONE')}",
                inline=False
            )
            changed = True

        if before.rules_channel != after.rules_channel:
            embed.add_field(
                name=t(guild, "LOG_SERVER_FIELD_RULES_CHANNEL"),
                value=f"{before.rules_channel.mention if before.rules_channel else t(guild, 'LOG_SERVER_NONE')} ➜ "
                      f"{after.rules_channel.mention if after.rules_channel else t(guild, 'LOG_SERVER_NONE')}",
                inline=False
            )
            changed = True

        if before.public_updates_channel != after.public_updates_channel:
            embed.add_field(
                name=t(guild, "LOG_SERVER_FIELD_COMMUNITY"),
                value=f"{before.public_updates_channel.mention if before.public_updates_channel else t(guild, 'LOG_SERVER_NONE')} ➜ "
                      f"{after.public_updates_channel.mention if after.public_updates_channel else t(guild, 'LOG_SERVER_NONE')}",
                inline=False
            )
            changed = True

        if before.verification_level != after.verification_level:
            embed.add_field(
                name=t(guild, "LOG_SERVER_FIELD_VERIFICATION"),
                value=f"`{before.verification_level}` ➜ `{after.verification_level}`",
                inline=True
            )
            changed = True

        if before.explicit_content_filter != after.explicit_content_filter:
            embed.add_field(
                name=t(guild, "LOG_SERVER_FIELD_EXPLICIT"),
                value=f"`{before.explicit_content_filter}` ➜ `{after.explicit_content_filter}`",
                inline=True
            )
            changed = True

        if before.default_notifications != after.default_notifications:
            embed.add_field(
                name=t(guild, "LOG_SERVER_FIELD_NOTIFICATIONS"),
                value=f"`{before.default_notifications}` ➜ `{after.default_notifications}`",
                inline=True
            )
            changed = True

        if before.preferred_locale != after.preferred_locale:
            embed.add_field(
                name=t(guild, "LOG_SERVER_FIELD_LOCALE"),
                value=f"`{before.preferred_locale}` ➜ `{after.preferred_locale}`",
                inline=True
            )
            changed = True

        if before.premium_tier != after.premium_tier:
            embed.add_field(
                name="💎 Cấp độ Boost (Premium Tier)",
                value=f"`Level {before.premium_tier}` ➜ `Level {after.premium_tier}`",
                inline=True
            )
            changed = True

        if before.vanity_url_code != after.vanity_url_code:
            embed.add_field(
                name="🔗 Đường dẫn tùy chỉnh (Vanity URL)",
                value=f"`{before.vanity_url_code or 'Không có'}` ➜ `{after.vanity_url_code or 'Không có'}`",
                inline=True
            )
            changed = True

        if before.owner_id != after.owner_id:
            embed.add_field(
                name=t(guild, "LOG_SERVER_FIELD_OWNER"),
                value=f"<@{before.owner_id}> ➜ <@{after.owner_id}>",
                inline=False
            )
            changed = True

        # Chỉ gọi API Audit Log khi thực sự có thuộc tính thay đổi
        if not changed:
            return

        executor = await self._get_audit_executor(
            after, discord.AuditLogAction.guild_update, target_id=after.id
        )

        if executor:
            embed.set_footer(
                text=t(guild, "LOG_SERVER_FOOTER_EXECUTOR", user=executor),
                icon_url=executor.display_avatar.url
            )
        else:
            embed.set_footer(text=t(guild, "LOG_SERVER_FOOTER_UNKNOWN"))

        try:
            await channel.send(embed=embed, files=saved_files if saved_files else None)
        except (discord.Forbidden, discord.HTTPException):
            pass

    # =========================================================================
    # 3. SỰ KIỆN TẠO / XÓA KÊNH (CREATE & DELETE CHANNEL)
    # =========================================================================

    @commands.Cog.listener()
    async def on_guild_channel_create(self, channel: discord.abc.GuildChannel):
        if channel.category_id and channel.category_id in self.ignored_category_ids:
            return

        guild = channel.guild
        guild_id = str(guild.id)

        if guild_id not in server_log_channels:
            return

        log_channel = guild.get_channel(server_log_channels[guild_id])
        if log_channel is None:
            return

        executor = await self._get_audit_executor(
            guild, discord.AuditLogAction.channel_create, target_id=channel.id
        )

        embed = discord.Embed(
            title=t(guild, "LOG_SERVER_CHANNEL_CREATED_TITLE"),
            color=discord.Color.green(),
            timestamp=discord.utils.utcnow()
        )

        embed.add_field(name=t(guild, "LOG_SERVER_FIELD_NAME2"), value=f"{channel.mention} (`{channel.name}`)", inline=False)
        embed.add_field(name=t(guild, "LOG_SERVER_FIELD_ID"), value=f"`{channel.id}`", inline=True)
        embed.add_field(name=t(guild, "LOG_SERVER_FIELD_TYPE"), value=f"`{channel.type}`", inline=True)
        embed.add_field(
            name=t(guild, "LOG_SERVER_FIELD_CATEGORY"),
            value=channel.category.mention if channel.category else t(guild, "LOG_SERVER_NONE"),
            inline=True
        )

        # Kiểm tra xem kênh mới tạo có phải là Kênh Riêng Tư (Private Channel) không
        everyone_ow = channel.overwrites_for(guild.default_role)
        if everyone_ow.view_channel is False:
            allowed_targets = [
                target.mention for target, ow in channel.overwrites.items()
                if ow.view_channel is True and target != guild.default_role
            ]
            priv_text = "🔒 **Kênh riêng tư**"
            if allowed_targets:
                priv_text += f"\nCho phép xem: {', '.join(allowed_targets[:10])}"
            embed.add_field(name="🔐 Quyền truy cập", value=priv_text, inline=False)

        if executor:
            embed.add_field(
                name=t(guild, "LOG_SERVER_FIELD_CREATED_BY"),
                value=f"{executor.mention} (`{executor.id}`)",
                inline=False
            )
            embed.set_footer(
                text=t(guild, "LOG_SERVER_FOOTER_EXECUTOR", user=executor),
                icon_url=executor.display_avatar.url
            )
        else:
            embed.set_footer(text=t(guild, "LOG_SERVER_FOOTER_UNKNOWN"))

        try:
            await log_channel.send(embed=embed)
        except (discord.Forbidden, discord.HTTPException):
            pass

    @commands.Cog.listener()
    async def on_guild_channel_delete(self, channel: discord.abc.GuildChannel):
        if channel.category_id and channel.category_id in self.ignored_category_ids:
            return

        guild = channel.guild
        guild_id = str(guild.id)

        if guild_id not in server_log_channels:
            return

        # Nếu chính kênh Log bị xóa thì không gửi vào chính nó được nữa
        if channel.id == server_log_channels[guild_id]:
            return

        log_channel = guild.get_channel(server_log_channels[guild_id])
        if log_channel is None:
            return

        # Đã sửa lỗi: Dùng đúng AuditLogAction.channel_delete thay vì channel_create
        executor = await self._get_audit_executor(
            guild, discord.AuditLogAction.channel_delete, target_id=channel.id
        )

        # Kiểm tra Anti-Nuke: Đếm số kênh bị xóa trong vòng 10 giây
        now_ts = discord.utils.utcnow().timestamp()
        self.delete_tracker[guild.id] = [ts for ts in self.delete_tracker[guild.id] if now_ts - ts <= 10.0]
        self.delete_tracker[guild.id].append(now_ts)
        is_mass_delete = len(self.delete_tracker[guild.id]) >= 3

        embed = discord.Embed(
            title="🚨 CẢNH BÁO XÓA KÊNH HÀNG LOẠT!" if is_mass_delete else t(guild, "LOG_SERVER_CHANNEL_DELETED_TITLE"),
            color=discord.Color.dark_red() if is_mass_delete else discord.Color.red(),
            timestamp=discord.utils.utcnow()
        )

        embed.add_field(name=t(guild, "LOG_SERVER_FIELD_NAME2"), value=f"**#{channel.name}**", inline=False)
        embed.add_field(name=t(guild, "LOG_SERVER_FIELD_ID"), value=f"`{channel.id}`", inline=True)
        embed.add_field(name=t(guild, "LOG_SERVER_FIELD_TYPE"), value=f"`{channel.type}`", inline=True)
        embed.add_field(
            name=t(guild, "LOG_SERVER_FIELD_CATEGORY"),
            value=channel.category.name if channel.category else t(guild, "LOG_SERVER_NONE"),
            inline=True
        )

        if executor:
            embed.add_field(
                name="🛠️ Người xóa (Deleted By)",
                value=f"{executor.mention} (`{executor.id}`)",
                inline=False
            )
            embed.set_footer(
                text=t(guild, "LOG_SERVER_FOOTER_EXECUTOR", user=executor),
                icon_url=executor.display_avatar.url
            )
        else:
            embed.set_footer(text=t(guild, "LOG_SERVER_FOOTER_UNKNOWN"))

        # Tạo bản thiết kế kênh (Blueprint) đính kèm để Admin dễ khôi phục
        blueprint_file = self._generate_channel_blueprint(channel)
        alert_content = f"⚠️ <@{guild.owner_id}> Phát hiện xóa nhiều kênh liên tiếp trong thời gian ngắn!" if is_mass_delete else None

        try:
            await log_channel.send(content=alert_content, embed=embed, file=blueprint_file)
        except (discord.Forbidden, discord.HTTPException):
            pass

    # =========================================================================
    # 4. SỰ KIỆN CẬP NHẬT KÊNH (CÓ DEBOUNCE & CHI TIẾT OVERWRITES)
    # =========================================================================

    @commands.Cog.listener()
    async def on_guild_channel_update(
        self,
        before: discord.abc.GuildChannel,
        after: discord.abc.GuildChannel
    ):
        guild = after.guild
        guild_id = str(guild.id)

        if guild_id not in server_log_channels:
            return

        log_channel = guild.get_channel(server_log_channels[guild_id])
        if log_channel is None:
            return

        # KIỂM TRA SỰ THAY ĐỔI TRƯỚC KHI GỌI API AUDIT LOG
        # Bỏ qua việc gọi API nếu chỉ là thay đổi vị trí (position) do kéo thả kênh
        has_meaningful_change = (
            before.name != after.name
            or before.category != after.category
            or getattr(before, "topic", None) != getattr(after, "topic", None)
            or getattr(before, "slowmode_delay", None) != getattr(after, "slowmode_delay", None)
            or getattr(before, "nsfw", None) != getattr(after, "nsfw", None)
            or getattr(before, "bitrate", None) != getattr(after, "bitrate", None)
            or getattr(before, "user_limit", None) != getattr(after, "user_limit", None)
            or getattr(before, "rtc_region", None) != getattr(after, "rtc_region", None)
            or getattr(before, "video_quality_mode", None) != getattr(after, "video_quality_mode", None)
            or getattr(before, "default_reaction_emoji", None) != getattr(after, "default_reaction_emoji", None)
            or before.overwrites != after.overwrites
        )

        if not has_meaningful_change:
            return

        ch_id = after.id
        if ch_id not in self.channel_update_queues:
            self.channel_update_queues[ch_id] = {
                "before": before,
                "after": after,
                "guild": guild,
                "log_channel": log_channel
            }
        else:
            # Giữ nguyên bản gốc `before` đầu tiên, chỉ cập nhật `after` mới nhất
            self.channel_update_queues[ch_id]["after"] = after

        if ch_id in self.channel_update_tasks and not self.channel_update_tasks[ch_id].done():
            self.channel_update_tasks[ch_id].cancel()

        self.channel_update_tasks[ch_id] = asyncio.create_task(
            self._process_channel_update_queue(ch_id)
        )

    async def _process_channel_update_queue(self, ch_id: int):
        try:
            await asyncio.sleep(self.UPDATE_DELAY)
        except asyncio.CancelledError:
            return

        item = self.channel_update_queues.pop(ch_id, None)
        self.channel_update_tasks.pop(ch_id, None)

        if not item:
            return

        before: discord.abc.GuildChannel = item["before"]
        after: discord.abc.GuildChannel = item["after"]
        guild: discord.Guild = item["guild"]
        log_channel: discord.TextChannel = item["log_channel"]

        embed = discord.Embed(
            title=t(guild, "LOG_SERVER_CHANNEL_UPDATED_TITLE"),
            color=discord.Color.orange(),
            timestamp=discord.utils.utcnow()
        )

        changed = False
        audit_actions = [discord.AuditLogAction.channel_update]

        if before.name != after.name:
            embed.add_field(
                name=t(guild, "LOG_SERVER_FIELD_NAME3"),
                value=f"`{before.name}` ➜ `{after.name}`",
                inline=False
            )
            changed = True

        if before.category != after.category:
            embed.add_field(
                name=t(guild, "LOG_SERVER_FIELD_CATEGORY2"),
                value=f"{before.category or t(guild, 'LOG_SERVER_NONE')} ➜ {after.category or t(guild, 'LOG_SERVER_NONE')}",
                inline=False
            )
            changed = True

        if hasattr(before, "topic") and before.topic != after.topic:
            # Cắt ngắn mỗi bên tối đa 450 ký tự để không bao giờ vượt giới hạn 1024 của Embed Field
            b_topic = self._truncate(before.topic, 450) or t(guild, "LOG_SERVER_NONE")
            a_topic = self._truncate(after.topic, 450) or t(guild, "LOG_SERVER_NONE")
            embed.add_field(
                name=t(guild, "LOG_SERVER_FIELD_TOPIC"),
                value=t(guild, "LOG_SERVER_FIELD_DESC_VALUE", before=b_topic, after=a_topic),
                inline=False
            )
            changed = True

        if hasattr(before, "slowmode_delay") and before.slowmode_delay != after.slowmode_delay:
            embed.add_field(
                name=t(guild, "LOG_SERVER_FIELD_SLOWMODE"),
                value=f"{self._format_duration(before.slowmode_delay)} ➜ {self._format_duration(after.slowmode_delay)}",
                inline=True
            )
            changed = True

        if hasattr(before, "nsfw") and before.nsfw != after.nsfw:
            embed.add_field(
                name=t(guild, "LOG_SERVER_FIELD_NSFW"),
                value=f"`{before.nsfw}` ➜ `{after.nsfw}`",
                inline=True
            )
            changed = True

        if hasattr(before, "bitrate") and before.bitrate != after.bitrate:
            embed.add_field(
                name=t(guild, "LOG_SERVER_FIELD_BITRATE"),
                value=f"`{before.bitrate // 1000} kbps` ➜ `{after.bitrate // 1000} kbps`",
                inline=True
            )
            changed = True

        if hasattr(before, "user_limit") and before.user_limit != after.user_limit:
            embed.add_field(
                name=t(guild, "LOG_SERVER_FIELD_USER_LIMIT"),
                value=f"`{before.user_limit or 'Không giới hạn'}` ➜ `{after.user_limit or 'Không giới hạn'}`",
                inline=True
            )
            changed = True

        if hasattr(before, "rtc_region") and before.rtc_region != after.rtc_region:
            embed.add_field(
                name=t(guild, "LOG_SERVER_FIELD_RTC"),
                value=f"`{before.rtc_region or 'Auto'}` ➜ `{after.rtc_region or 'Auto'}`",
                inline=True
            )
            changed = True

        if hasattr(before, "video_quality_mode") and before.video_quality_mode != after.video_quality_mode:
            embed.add_field(
                name="📹 Chất lượng Video",
                value=f"`{before.video_quality_mode.name}` ➜ `{after.video_quality_mode.name}`",
                inline=True
            )
            changed = True

        if before.overwrites != after.overwrites:
            audit_actions.extend([
                discord.AuditLogAction.overwrite_create,
                discord.AuditLogAction.overwrite_update,
                discord.AuditLogAction.overwrite_delete,
            ])
            ow_diff = self._format_overwrites_diff(before.overwrites, after.overwrites)
            embed.add_field(
                name=t(guild, "LOG_SERVER_FIELD_PERMS"),
                value=ow_diff or t(guild, "LOG_SERVER_FIELD_PERMS_VALUE"),
                inline=False
            )
            changed = True

        if not changed:
            return

        # Tìm người thực hiện trong cả channel_update lẫn overwrite_*
        executor = await self._get_audit_executor(
            guild, audit_actions, target_id=after.id, delay=0.0
        )

        embed.add_field(
            name=t(guild, "LOG_SERVER_FIELD_CHANNEL2"),
            value=f"{after.mention} (`{after.id}`)",
            inline=True
        )

        if executor:
            embed.add_field(
                name=t(guild, "LOG_SERVER_FIELD_UPDATED_BY"),
                value=f"{executor.mention} (`{executor.id}`)",
                inline=True
            )
            embed.set_footer(
                text=t(guild, "LOG_SERVER_FOOTER_EXECUTOR", user=executor),
                icon_url=executor.display_avatar.url
            )
        else:
            embed.set_footer(text=t(guild, "LOG_SERVER_FOOTER_UNKNOWN"))

        try:
            await log_channel.send(embed=embed)
        except (discord.Forbidden, discord.HTTPException):
            pass

    # =========================================================================
    # 5. GIÁM SÁT CHỦ ĐỀ (THREADS) & EMOJI / STICKER SERVER
    # =========================================================================

    @commands.Cog.listener()
    async def on_thread_create(self, thread: discord.Thread):
        guild = thread.guild
        guild_id = str(guild.id)
        if guild_id not in server_log_channels:
            return

        log_channel = guild.get_channel(server_log_channels[guild_id])
        if not log_channel:
            return

        embed = discord.Embed(
            title=t(guild, "LOG_SERVER_THREAD_CREATED_TITLE"),
            color=discord.Color.green(),
            timestamp=discord.utils.utcnow()
        )
        embed.add_field(name=t(guild, "LOG_SERVER_THREAD_FIELD_NAME"), value=f"{thread.mention} (`{thread.name}`)", inline=True)
        embed.add_field(name=t(guild, "LOG_SERVER_THREAD_FIELD_PARENT"), value=thread.parent.mention if thread.parent else "Không rõ", inline=True)
        if thread.owner:
            embed.add_field(name=t(guild, "LOG_SERVER_THREAD_FIELD_CREATOR"), value=f"{thread.owner.mention} (`{thread.owner.id}`)", inline=False)

        try:
            await log_channel.send(embed=embed)
        except (discord.Forbidden, discord.HTTPException):
            pass

    @commands.Cog.listener()
    async def on_thread_delete(self, thread: discord.Thread):
        guild = thread.guild
        guild_id = str(guild.id)
        if guild_id not in server_log_channels:
            return

        log_channel = guild.get_channel(server_log_channels[guild_id])
        if not log_channel:
            return

        executor = await self._get_audit_executor(
            guild, discord.AuditLogAction.thread_delete, target_id=thread.id
        )

        embed = discord.Embed(
            title=t(guild, "LOG_SERVER_THREAD_DELETED_TITLE"),
            color=discord.Color.red(),
            timestamp=discord.utils.utcnow()
        )
        embed.add_field(name=t(guild, "LOG_SERVER_THREAD_FIELD_NAME"), value=f"**{thread.name}** (`{thread.id}`)", inline=True)
        embed.add_field(name=t(guild, "LOG_SERVER_THREAD_FIELD_PARENT"), value=thread.parent.mention if thread.parent else "Không rõ", inline=True)
        if executor:
            embed.add_field(name=t(guild, "LOG_SERVER_THREAD_FIELD_DELETER"), value=f"{executor.mention} (`{executor.id}`)", inline=False)

        try:
            await log_channel.send(embed=embed)
        except (discord.Forbidden, discord.HTTPException):
            pass

    @commands.Cog.listener()
    async def on_guild_emojis_update(
        self,
        guild: discord.Guild,
        before: tuple[discord.Emoji, ...],
        after: tuple[discord.Emoji, ...]
    ):
        guild_id = str(guild.id)
        if guild_id not in server_log_channels:
            return

        log_channel = guild.get_channel(server_log_channels[guild_id])
        if not log_channel:
            return

        before_set = set(before)
        after_set = set(after)

        added = after_set - before_set
        removed = before_set - after_set

        if not added and not removed:
            return

        embed = discord.Embed(
            title=t(guild, "LOG_SERVER_EMOJI_UPDATE_TITLE"),
            color=discord.Color.blurple(),
            timestamp=discord.utils.utcnow()
        )

        if added:
            embed.add_field(
                name=t(guild, "LOG_SERVER_FIELD_EMOJI_ADDED", count=len(added)),
                value="\n".join([f"{e} `:{e.name}:` (`{e.id}`)" for e in list(added)[:10]]),
                inline=False
            )

        if removed:
            embed.add_field(
                name=t(guild, "LOG_SERVER_FIELD_EMOJI_REMOVED", count=len(removed)),
                value="\n".join([f"`:{e.name}:` (`{e.id}`) - [Link ảnh]({e.url})" for e in list(removed)[:10]]),
                inline=False
            )
            first_removed = list(removed)[0]
            embed.set_thumbnail(url=first_removed.url)

        try:
            await log_channel.send(embed=embed)
        except (discord.Forbidden, discord.HTTPException):
            pass


async def setup(bot: commands.Bot):
    await bot.add_cog(ServerLog(bot))
