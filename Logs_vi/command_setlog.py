import discord
from discord.ext import commands
from discord import app_commands

from Checks_vi.i18n import t
from Checks_vi.data import (
    chat_log_channels, edit_log_channels, delete_log_channels, voice_log_channels,
    server_log_channels, user_log_channels, member_log_channels,
    automod_log_channels, invite_log_channels, command_log_channels,
    LOG_CHANNEL_ID, CREATE_CHANNEL_ID, save_data
)


class ChannelSetup(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.hybrid_command(
        name="set",
        description="Cài đặt kênh log, tự động tạo hệ thống log hoặc quản lý phòng voice."
    )
    @app_commands.choices(mode=[
        app_commands.Choice(name="✨ Tự động tạo tất cả (Auto Setup)", value="autosetup"),
        app_commands.Choice(name="⚡ Gom tất cả Log vào 1 kênh (All)", value="all"),
        app_commands.Choice(name="🌸 Chat Log", value="chatlog"),
        app_commands.Choice(name="🌸 Edit Log", value="editlog"),
        app_commands.Choice(name="🌸 Delete Log", value="deletelog"),
        app_commands.Choice(name="🌸 Voice Log", value="voicelog"),
        app_commands.Choice(name="🌸 Server Log", value="serverlog"),
        app_commands.Choice(name="🌸 Audit Log", value="auditlog"),
        app_commands.Choice(name="🌸 Member Log", value="memberlog"),
        app_commands.Choice(name="🌸 AutoMod Log", value="automodlog"),
        app_commands.Choice(name="🌸 Invite Log", value="invitelog"),
        app_commands.Choice(name="🌸 Command Log", value="commandlog"),
        app_commands.Choice(name="🌸 Log Cảnh Cáo", value="set_log"),
        app_commands.Choice(name="🎙️ Tạo Phòng Voice", value="createvoice"),
    ])
    @app_commands.describe(
        mode="Chọn loại log, tính năng tự động thiết lập hoặc tạo phòng voice",
        channel="Tag hoặc chọn kênh cần áp dụng (bỏ trống để xem trạng thái hoặc xóa cài đặt)"
    )
    @commands.guild_only()
    @commands.has_permissions(administrator=True)
    async def set_channel(
        self,
        ctx: commands.Context,
        mode: str = None,
        channel: discord.abc.GuildChannel = None
    ):
        guild = ctx.guild
        guild_id = str(guild.id)

        # Danh sách 11 loại Log văn bản chuẩn (Đã xóa Reaction, Thread, Emoji, Sticker)
        log_mapping = {
            ("chatlog", "chat"): (chat_log_channels, "Chat Log", "💬・chat-log"),
            ("editlog", "edit"): (edit_log_channels, "Edit Log", "✏️・edit-log"),
            ("deletelog", "delete"): (delete_log_channels, "Delete Log", "🗑️・delete-log"),
            ("voicelog", "voice"): (voice_log_channels, "Voice Log", "🔊・voice-log"),
            ("serverlog", "server", "logserver"): (server_log_channels, "Server Log", "🏠・server-log"),
            ("auditlog", "audit", "userlog"): (user_log_channels, "Audit Log", "🛡️・audit-log"),
            ("memberlog", "member"): (member_log_channels, "Member Log", "👥・member-log"),
            ("automodlog", "automod"): (automod_log_channels, "AutoMod Log", "🤖・automod-log"),
            ("invitelog", "invite"): (invite_log_channels, "Invite Log", "📨・invite-log"),
            ("commandlog", "command"): (command_log_channels, "Command Log", "⌨️・command-log"),
            ("set_log", "warnlog"): (LOG_CHANNEL_ID, "Log Cảnh Cáo", "⚠️・log-cảnh-cáo"),
        }

        # =====================================================================
        # 1. XEM BẢNG TRẠNG THÁI (KHI BỎ TRỐNG MODE)
        # =====================================================================
        if mode is None:
            embed = discord.Embed(
                title=t(guild, "LOG_SETLOG_MENU_TITLE"),
                description=t(guild, "LOG_SETLOG_MENU_DESC"),
                color=discord.Color.pink(),
                timestamp=discord.utils.utcnow()
            )

            status_lines = []
            for _, (target_dict, display_name, _) in log_mapping.items():
                ch_id = target_dict.get(guild_id)
                ch_obj = guild.get_channel(ch_id) if ch_id else None
                val = ch_obj.mention if ch_obj else "`Chưa cài đặt`"
                status_lines.append(f"• **{display_name}:** {val}")

            voice_id = CREATE_CHANNEL_ID.get(guild_id)
            voice_obj = guild.get_channel(voice_id) if voice_id else None
            status_lines.append(f"• **🎙️ Tạo Phòng Voice:** {voice_obj.mention if voice_obj else '`Chưa cài đặt`'}")

            embed.add_field(
                name="📋 Trạng thái cấu hình hiện tại",
                value="\n".join(status_lines),
                inline=False
            )

            if self.bot.user:
                embed.set_thumbnail(url=self.bot.user.display_avatar.url)
            embed.set_footer(
                text=t(guild, "LOG_SETLOG_MENU_FOOTER", name=ctx.author.display_name),
                icon_url=ctx.author.display_avatar.url
            )
            return await ctx.send(embed=embed)

        mode_lower = mode.lower()

        # =====================================================================
        # 2. TỰ ĐỘNG TẠO DANH MỤC & CÁC KÊNH LOG (AUTO-SETUP)
        # =====================================================================
        if mode_lower == "autosetup":
            if not guild.me.guild_permissions.manage_channels:
                return await ctx.send(
                    "❌ Bot cần quyền **Quản lý Kênh (`Manage Channels`)** để tự động tạo danh mục và kênh!",
                    ephemeral=True
                )

            await ctx.defer()

            try:
                # 2.1. Tạo hoặc tìm lại Danh mục Hệ thống Log (Ẩn với @everyone)
                overwrites_log = {
                    guild.default_role: discord.PermissionOverwrite(view_channel=False),
                    guild.me: discord.PermissionOverwrite(
                        view_channel=True,
                        send_messages=True,
                        embed_links=True,
                        attach_files=True,
                        manage_channels=True
                    )
                }

                log_category = discord.utils.get(guild.categories, name="📊 ┃ HỆ THỐNG LOG")
                if not log_category:
                    log_category = await guild.create_category(
                        name="📊 ┃ HỆ THỐNG LOG",
                        overwrites=overwrites_log,
                        reason=f"Auto-Setup Log bởi {ctx.author}"
                    )

                created_logs = []
                reused_logs = []

                for _, (target_dict, display_name, ch_name) in log_mapping.items():
                    existing_id = target_dict.get(guild_id)
                    existing_ch = guild.get_channel(existing_id) if existing_id else None

                    # Smart Reuse: Nếu kênh đã cài trước đó vẫn còn tồn tại thì giữ nguyên, không tạo trùng
                    if existing_ch and isinstance(existing_ch, discord.TextChannel):
                        reused_logs.append(f"{display_name} ({existing_ch.mention})")
                    else:
                        new_ch = await guild.create_text_channel(
                            name=ch_name,
                            category=log_category,
                            reason=f"Auto-Setup Log bởi {ctx.author}"
                        )
                        target_dict[guild_id] = new_ch.id
                        created_logs.append(f"{display_name} ({new_ch.mention})")

                # 2.2. Tạo Danh mục & Kênh Tạo Phòng Voice riêng biệt (Công khai cho @everyone)
                existing_voice_id = CREATE_CHANNEL_ID.get(guild_id)
                existing_voice_ch = guild.get_channel(existing_voice_id) if existing_voice_id else None

                if existing_voice_ch and isinstance(existing_voice_ch, (discord.VoiceChannel, discord.StageChannel)):
                    voice_status = f"Giữ nguyên kênh cũ: {existing_voice_ch.mention}"
                else:
                    overwrites_voice = {
                        guild.default_role: discord.PermissionOverwrite(view_channel=True, connect=True),
                        guild.me: discord.PermissionOverwrite(
                            view_channel=True,
                            connect=True,
                            manage_channels=True,
                            move_members=True
                        )
                    }
                    voice_category = discord.utils.get(guild.categories, name="🎙️ ┃ KHU VỰC VOICE")
                    if not voice_category:
                        voice_category = await guild.create_category(
                            name="🎙️ ┃ KHU VỰC VOICE",
                            overwrites=overwrites_voice,
                            reason=f"Auto-Setup Voice bởi {ctx.author}"
                        )

                    new_voice_ch = await guild.create_voice_channel(
                        name="➕ Tạo Phòng Voice",
                        category=voice_category,
                        reason=f"Auto-Setup Voice bởi {ctx.author}"
                    )
                    CREATE_CHANNEL_ID[guild_id] = new_voice_ch.id
                    voice_status = f"Đã tạo mới: {new_voice_ch.mention} (Danh mục: **{voice_category.name}**)"

                save_data()

                embed = discord.Embed(
                    title=t(guild, "SETLOG_AUTO_COMPLETE_TITLE"),
                    color=discord.Color.green(),
                    timestamp=discord.utils.utcnow()
                )
                if created_logs:
                    embed.add_field(
                        name=t(guild, "SETLOG_FIELD_CREATED_LOGS", count=len(created_logs)),
                        value="\n".join(f"• {item}" for item in created_logs),
                        inline=False
                    )
                if reused_logs:
                    embed.add_field(
                        name=t(guild, "SETLOG_FIELD_REUSED_LOGS", count=len(reused_logs)),
                        value="\n".join(f"• {item}" for item in reused_logs),
                        inline=False
                    )
                embed.add_field(
                    name=t(guild, "SETLOG_FIELD_VOICE_AREA"),
                    value=voice_status,
                    inline=False
                )
                embed.set_footer(
                    text=f"Thiết lập bởi {ctx.author.display_name}",
                    icon_url=ctx.author.display_avatar.url
                )
                return await ctx.send(embed=embed)

            except discord.Forbidden:
                return await ctx.send("❌ Bot bị thiếu quyền hạn trong quá trình tạo danh mục/kênh!", ephemeral=True)
            except discord.HTTPException as e:
                return await ctx.send(f"❌ Lỗi kết nối Discord khi tạo kênh: `{e}`", ephemeral=True)

        # =====================================================================
        # 3. CHẾ ĐỘ GOM TẤT CẢ LOG VÀO 1 KÊNH DUY NHẤT (ALL)
        # =====================================================================
        if mode_lower == "all":
            if channel is None:
                # Nếu bỏ trống kênh -> Xóa toàn bộ cấu hình của cả 11 loại log
                for _, (target_dict, _, _) in log_mapping.items():
                    target_dict.pop(guild_id, None)
                save_data()
                return await ctx.send(t(guild, "SETLOG_ALL_DISABLED"), ephemeral=True)

            if not isinstance(channel, discord.TextChannel):
                return await ctx.send(t(guild, "LOG_SETLOG_ERROR_NOT_TEXT"), ephemeral=True)

            perms = channel.permissions_for(guild.me)
            if not (perms.view_channel and perms.send_messages and perms.embed_links):
                return await ctx.send(
                    t(guild, "SETLOG_ERR_PERMS", channel=channel.mention),
                    ephemeral=True
                )

            for _, (target_dict, _, _) in log_mapping.items():
                target_dict[guild_id] = channel.id
            save_data()

            embed = discord.Embed(
                title=t(guild, "LOG_SETLOG_SUCCESS_TITLE"),
                description=t(guild, "SETLOG_ALL_ASSIGNED", channel=channel.mention),
                color=discord.Color.green()
            )
            return await ctx.send(embed=embed)

        # =====================================================================
        # 4. CÀI ĐẶT HOẶC HỦY TỪNG LOẠI LOG ĐƠN LẺ
        # =====================================================================
        for keys, (target_dict, display_name, _) in log_mapping.items():
            if mode_lower in keys:
                # Nếu bỏ trống channel -> Gỡ cài đặt (Unset) loại log đó
                if channel is None:
                    if guild_id in target_dict:
                        del target_dict[guild_id]
                        save_data()
                        return await ctx.send(t(guild, "SETLOG_SINGLE_DISABLED", name=display_name), ephemeral=True)
                    return await ctx.send(
                        t(guild, "SETLOG_SINGLE_NOT_SET", name=display_name),
                        ephemeral=True
                    )

                if not isinstance(channel, discord.TextChannel):
                    return await ctx.send(t(guild, "LOG_SETLOG_ERROR_NOT_TEXT"), ephemeral=True)

                # Kiểm tra quyền của Bot trong kênh được chọn
                perms = channel.permissions_for(guild.me)
                if not (perms.view_channel and perms.send_messages and perms.embed_links):
                    return await ctx.send(
                        t(guild, "SETLOG_ERR_PERMS", channel=channel.mention),
                        ephemeral=True
                    )

                target_dict[guild_id] = channel.id
                save_data()

                embed = discord.Embed(
                    title=t(guild, "LOG_SETLOG_SUCCESS_TITLE"),
                    description=t(guild, "LOG_SETLOG_SUCCESS_DESC", channel=channel.mention),
                    color=discord.Color.random()
                )
                embed.add_field(name=t(guild, "LOG_SETLOG_FIELD_TYPE"), value=display_name)
                return await ctx.send(embed=embed)

        # =====================================================================
        # 5. CÀI ĐẶT HOẶC HỦY KÊNH TẠO PHÒNG VOICE (CREATEVOICE / JOINVOICE)
        # =====================================================================
        if mode_lower in ["createvoice", "joinvoice"]:
            if channel is None:
                if guild_id in CREATE_CHANNEL_ID:
                    del CREATE_CHANNEL_ID[guild_id]
                    save_data()
                    return await ctx.send(t(guild, "SETLOG_VOICE_DISABLED"), ephemeral=True)
                return await ctx.send(
                    t(guild, "SETLOG_VOICE_NOT_SET"),
                    ephemeral=True
                )

            if not isinstance(channel, (discord.VoiceChannel, discord.StageChannel)):
                return await ctx.send(t(guild, "LOG_SETLOG_ERROR_NOT_VOICE"), ephemeral=True)

            CREATE_CHANNEL_ID[guild_id] = channel.id
            save_data()

            embed = discord.Embed(
                title=t(guild, "LOG_SETLOG_CREATEVOICE_TITLE"),
                description=t(guild, "LOG_SETLOG_CREATEVOICE_DESC"),
                color=discord.Color.random()
            )
            embed.add_field(name=t(guild, "LOG_SETLOG_CREATEVOICE_FIELD"), value=channel.mention, inline=False)
            embed.set_footer(
                text=t(guild, "LOG_SETLOG_FOOTER_SERVER", name=ctx.guild.name),
                icon_url=ctx.guild.icon.url if ctx.guild.icon else None
            )
            return await ctx.send(embed=embed)

        await ctx.send(t(guild, "LOG_SETLOG_ERROR_INVALID_MODE"), ephemeral=True)


async def setup(bot: commands.Bot):
    await bot.add_cog(ChannelSetup(bot))
