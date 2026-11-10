import discord
from Check.voice import check_owner, temp_channels, banned_members


def apply_owner_permissions(overwrite: discord.PermissionOverwrite) -> discord.PermissionOverwrite:
    """Thiết lập bộ quyền tiêu chuẩn cho chủ phòng Temp Voice."""
    overwrite.view_channel = True
    overwrite.connect = True
    overwrite.manage_channels = True
    overwrite.manage_permissions = True
    overwrite.move_members = True
    overwrite.mute_members = True
    overwrite.deafen_members = True
    overwrite.priority_speaker = True
    return overwrite


class RenameModal(discord.ui.Modal, title="Đổi tên Voice"):
    name = discord.ui.TextInput(
        label="Tên phòng mới",
        placeholder="Nhập tên phòng...",
        min_length=1,
        max_length=50
    )

    async def on_submit(self, interaction: discord.Interaction):
        channel = await check_owner(interaction)
        if channel is None:
            return

        new_name = self.name.value.strip()
        try:
            await channel.edit(name=new_name)
            await interaction.response.send_message(
                f"✅ Đã đổi tên phòng thành **{new_name}**.",
                ephemeral=True
            )
        except discord.HTTPException:
            await interaction.response.send_message(
                "❌ Không thể đổi tên phòng lúc này (Discord giới hạn đổi tên 2 lần / 10 phút).",
                ephemeral=True
            )


class StatusModal(discord.ui.Modal, title="Đặt trạng thái Voice"):
    status_text = discord.ui.TextInput(
        label="Trạng thái kênh (Để trống để xóa)",
        placeholder="Nhập nội dung trạng thái...",
        required=False,
        max_length=100
    )

    async def on_submit(self, interaction: discord.Interaction):
        channel = await check_owner(interaction)
        if channel is None:
            return

        new_status = self.status_text.value.strip() or None
        try:
            await channel.edit(status=new_status)
            if new_status:
                await interaction.response.send_message(
                    f"✅ Đã cập nhật trạng thái phòng: **{new_status}**",
                    ephemeral=True
                )
            else:
                await interaction.response.send_message(
                    "✅ Đã xóa trạng thái của phòng thoại.",
                    ephemeral=True
                )
        except discord.HTTPException:
            await interaction.response.send_message(
                "❌ Không thể cập nhật trạng thái lúc này.",
                ephemeral=True
            )


class LimitModal(discord.ui.Modal, title="Giới hạn người"):
    limit = discord.ui.TextInput(
        label="Nhập số lượng (0 - 99, 0 là không giới hạn)",
        placeholder="10",
        min_length=1,
        max_length=2
    )

    async def on_submit(self, interaction: discord.Interaction):
        channel = await check_owner(interaction)
        if channel is None:
            return

        try:
            number = int(self.limit.value.strip())
            if not (0 <= number <= 99):
                raise ValueError
        except ValueError:
            return await interaction.response.send_message(
                "❌ Vui lòng nhập một số nguyên hợp lệ từ **0** đến **99**.",
                ephemeral=True
            )

        try:
            await channel.edit(user_limit=number)
            limit_text = f"**{number}** người" if number > 0 else "**Không giới hạn**"
            await interaction.response.send_message(
                f"✅ Đã đặt giới hạn phòng: {limit_text}.",
                ephemeral=True
            )
        except discord.HTTPException:
            await interaction.response.send_message(
                "❌ Có lỗi xảy ra khi cập nhật giới hạn phòng.",
                ephemeral=True
            )


class TransferOwnerView(discord.ui.View):
    def __init__(self, channel: discord.VoiceChannel):
        super().__init__(timeout=60)
        self.channel = channel

    @discord.ui.select(
        cls=discord.ui.UserSelect,
        placeholder="Chọn chủ phòng mới...",
        min_values=1,
        max_values=1
    )
    async def select_owner(
        self,
        interaction: discord.Interaction,
        select: discord.ui.UserSelect
    ):
        new_owner = select.values[0]

        if new_owner.bot:
            return await interaction.response.send_message(
                "❌ Không thể chuyển quyền chủ phòng cho Bot.",
                ephemeral=True
            )

        if new_owner.id == interaction.user.id:
            return await interaction.response.send_message(
                "❌ Bạn đã là chủ phòng hiện tại rồi.",
                ephemeral=True
            )

        if new_owner not in self.channel.members:
            return await interaction.response.send_message(
                "❌ Người này hiện không có mặt trong phòng Voice.",
                ephemeral=True
            )

        temp_channels[self.channel.id] = new_owner.id

        try:
            await self.channel.set_permissions(interaction.user, overwrite=None)
            new_overwrite = apply_owner_permissions(self.channel.overwrites_for(new_owner))
            await self.channel.set_permissions(new_owner, overwrite=new_overwrite)
        except discord.HTTPException:
            pass

        await interaction.response.edit_message(
            content=f"👑 Đã chuyển quyền chủ phòng cho {new_owner.mention}.",
            view=None
        )


class KickMemberView(discord.ui.View):
    def __init__(self, channel: discord.VoiceChannel):
        super().__init__(timeout=60)
        self.channel = channel

    @discord.ui.select(
        cls=discord.ui.UserSelect,
        placeholder="Chọn người cần kick...",
        min_values=1,
        max_values=1
    )
    async def kick_member(
        self,
        interaction: discord.Interaction,
        select: discord.ui.UserSelect
    ):
        member = select.values[0]

        if member.id == interaction.user.id:
            return await interaction.response.send_message(
                "❌ Bạn không thể tự kick chính mình.",
                ephemeral=True
            )

        if not isinstance(member, discord.Member) or member not in self.channel.members:
            return await interaction.response.send_message(
                "❌ Người này hiện không ở trong phòng Voice.",
                ephemeral=True
            )

        try:
            await member.move_to(None, reason=f"Kicked by room owner {interaction.user}")
            await interaction.response.edit_message(
                content=f"🦶 Đã đá {member.mention} khỏi phòng.",
                view=None
            )
        except discord.HTTPException:
            await interaction.response.send_message(
                "❌ Không thể kick thành viên này.",
                ephemeral=True
            )


class BanMemberView(discord.ui.View):
    def __init__(self, channel: discord.VoiceChannel):
        super().__init__(timeout=60)
        self.channel = channel

    @discord.ui.select(
        cls=discord.ui.UserSelect,
        placeholder="Chọn người cần cấm...",
        min_values=1,
        max_values=1
    )
    async def ban_member(
        self,
        interaction: discord.Interaction,
        select: discord.ui.UserSelect
    ):
        member = select.values[0]

        if member.id == interaction.user.id:
            return await interaction.response.send_message(
                "❌ Bạn không thể tự cấm chính mình.",
                ephemeral=True
            )

        if not isinstance(member, discord.Member):
            return await interaction.response.send_message(
                "❌ Không tìm thấy thông tin thành viên trong máy chủ.",
                ephemeral=True
            )

        banned_members.setdefault(self.channel.id, set()).add(member.id)

        try:
            overwrite = self.channel.overwrites_for(member)
            overwrite.connect = False
            await self.channel.set_permissions(member, overwrite=overwrite)

            if member in self.channel.members:
                await member.move_to(None, reason=f"Banned by room owner {interaction.user}")
        except discord.HTTPException:
            pass

        await interaction.response.edit_message(
            content=f"🚫 Đã cấm {member.mention} tham gia phòng.",
            view=None
        )


class UnbanSelect(discord.ui.Select):
    def __init__(self, options: list[discord.SelectOption], channel: discord.VoiceChannel):
        super().__init__(
            placeholder="Chọn người cần bỏ cấm...",
            options=options[:25],
            min_values=1,
            max_values=1
        )
        self.channel = channel

    async def callback(self, interaction: discord.Interaction):
        user_id = int(self.values[0])
        banned_members.get(self.channel.id, set()).discard(user_id)

        member = self.channel.guild.get_member(user_id)
        if member:
            try:
                await self.channel.set_permissions(member, overwrite=None)
            except discord.HTTPException:
                pass
            target_text = member.mention
        else:
            target_text = f"ID `{user_id}`"

        await interaction.response.edit_message(
            content=f"✅ Đã gỡ lệnh cấm cho {target_text}.",
            view=None
        )


class UnbanMemberView(discord.ui.View):
    def __init__(self, channel: discord.VoiceChannel):
        super().__init__(timeout=60)
        self.channel = channel

        banned = banned_members.get(channel.id, set())
        options = []
        for uid in list(banned)[:25]:
            member = channel.guild.get_member(uid)
            label = member.display_name if member else f"User ID: {uid}"
            options.append(discord.SelectOption(label=label[:100], value=str(uid)))

        if options:
            self.add_item(UnbanSelect(options, channel))


class VoiceStateSelect(discord.ui.Select):
    def __init__(
        self,
        channel: discord.VoiceChannel,
        options: list[discord.SelectOption],
        action: str,
        placeholder: str
    ):
        super().__init__(
            placeholder=placeholder,
            min_values=1,
            max_values=len(options),
            options=options
        )
        self.channel = channel
        self.action = action

    async def callback(self, interaction: discord.Interaction):
        if not self.values:
            return

        await interaction.response.defer(ephemeral=True)
        count = 0

        for user_id in self.values:
            member = self.channel.guild.get_member(int(user_id))
            if not member or member not in self.channel.members:
                continue
            try:
                if self.action == "mute":
                    await member.edit(mute=True)
                elif self.action == "unmute":
                    await member.edit(mute=False)
                elif self.action == "deafen":
                    await member.edit(deafen=True)
                elif self.action == "undeafen":
                    await member.edit(deafen=False)
                count += 1
            except discord.HTTPException:
                continue

        messages = {
            "mute": f"🔇 Đã khóa mic **{count}** thành viên.",
            "unmute": f"🔊 Đã mở mic **{count}** thành viên.",
            "deafen": f"🔈 Đã tắt âm **{count}** thành viên.",
            "undeafen": f"🔊 Đã bật âm **{count}** thành viên.",
        }
        await interaction.followup.send(messages[self.action], ephemeral=True)


class VoiceStateActionView(discord.ui.View):
    def __init__(self, channel: discord.VoiceChannel, action: str, placeholder: str):
        super().__init__(timeout=60)
        options = [
            discord.SelectOption(label=m.display_name[:100], value=str(m.id))
            for m in channel.members
            if not m.bot
        ][:25]

        if options:
            self.add_item(VoiceStateSelect(channel, options, action, placeholder))


class VoicePanel(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    def _has_human_targets(self, channel: discord.VoiceChannel) -> bool:
        return any(not m.bot for m in channel.members)


    @discord.ui.button(label="🔒 Khóa", style=discord.ButtonStyle.red, row=0, custom_id="vc_panel:lock")
    async def lock(self, interaction: discord.Interaction, button: discord.ui.Button):
        channel = await check_owner(interaction)
        if channel is None:
            return

        overwrite = channel.overwrites_for(interaction.guild.default_role)
        overwrite.connect = False
        await channel.set_permissions(interaction.guild.default_role, overwrite=overwrite)

        owner_overwrite = apply_owner_permissions(channel.overwrites_for(interaction.user))
        await channel.set_permissions(interaction.user, overwrite=owner_overwrite)

        await interaction.response.send_message("🔒 Đã khóa phòng.", ephemeral=True)

    @discord.ui.button(label="🔓 Mở", style=discord.ButtonStyle.green, row=0, custom_id="vc_panel:unlock")
    async def unlock(self, interaction: discord.Interaction, button: discord.ui.Button):
        channel = await check_owner(interaction)
        if channel is None:
            return

        overwrite = channel.overwrites_for(interaction.guild.default_role)
        overwrite.connect = True
        await channel.set_permissions(interaction.guild.default_role, overwrite=overwrite)

        await interaction.response.send_message("🔓 Đã mở phòng.", ephemeral=True)

    @discord.ui.button(label="👁️ Ẩn", style=discord.ButtonStyle.secondary, row=0, custom_id="vc_panel:hide")
    async def hide(self, interaction: discord.Interaction, button: discord.ui.Button):
        channel = await check_owner(interaction)
        if channel is None:
            return

        overwrite = channel.overwrites_for(interaction.guild.default_role)
        overwrite.view_channel = False
        await channel.set_permissions(interaction.guild.default_role, overwrite=overwrite)

        owner_overwrite = apply_owner_permissions(channel.overwrites_for(interaction.user))
        await channel.set_permissions(interaction.user, overwrite=owner_overwrite)

        await interaction.response.send_message("👁️ Đã ẩn phòng.", ephemeral=True)

    @discord.ui.button(label="👀 Hiện", style=discord.ButtonStyle.secondary, row=0, custom_id="vc_panel:show")
    async def show(self, interaction: discord.Interaction, button: discord.ui.Button):
        channel = await check_owner(interaction)
        if channel is None:
            return

        overwrite = channel.overwrites_for(interaction.guild.default_role)
        overwrite.view_channel = True
        await channel.set_permissions(interaction.guild.default_role, overwrite=overwrite)

        await interaction.response.send_message("👀 Đã hiện phòng.", ephemeral=True)


    @discord.ui.button(label="✏️ Đổi tên", style=discord.ButtonStyle.primary, row=1, custom_id="vc_panel:rename")
    async def rename(self, interaction: discord.Interaction, button: discord.ui.Button):
        channel = await check_owner(interaction)
        if channel is None:
            return
        await interaction.response.send_modal(RenameModal())

    @discord.ui.button(label="📝 Trạng thái", style=discord.ButtonStyle.secondary, row=1, custom_id="vc_panel:status")
    async def set_status(self, interaction: discord.Interaction, button: discord.ui.Button):
        channel = await check_owner(interaction)
        if channel is None:
            return
        await interaction.response.send_modal(StatusModal())

    @discord.ui.button(label="👥 Giới hạn", style=discord.ButtonStyle.secondary, row=1, custom_id="vc_panel:limit")
    async def limit(self, interaction: discord.Interaction, button: discord.ui.Button):
        channel = await check_owner(interaction)
        if channel is None:
            return
        await interaction.response.send_modal(LimitModal())

    @discord.ui.button(label="👑 Owner", style=discord.ButtonStyle.primary, row=1, custom_id="vc_panel:transfer")
    async def transfer(self, interaction: discord.Interaction, button: discord.ui.Button):
        channel = await check_owner(interaction)
        if channel is None:
            return

        await interaction.response.send_message(
            "Chọn chủ phòng mới:",
            view=TransferOwnerView(channel),
            ephemeral=True
        )

    @discord.ui.button(label="🦶 Kick", style=discord.ButtonStyle.secondary, row=1, custom_id="vc_panel:kick")
    async def kick(self, interaction: discord.Interaction, button: discord.ui.Button):
        channel = await check_owner(interaction)
        if channel is None:
            return

        await interaction.response.send_message(
            "Chọn thành viên cần kick:",
            view=KickMemberView(channel),
            ephemeral=True
        )


    @discord.ui.button(label="🔇 Mute", style=discord.ButtonStyle.secondary, row=2, custom_id="vc_panel:mute")
    async def mute_all(self, interaction: discord.Interaction, button: discord.ui.Button):
        channel = await check_owner(interaction)
        if channel is None:
            return
        if not self._has_human_targets(channel):
            return await interaction.response.send_message("❌ Không có thành viên nào trong phòng.", ephemeral=True)

        await interaction.response.send_message(
            "Chọn người cần khóa mic:",
            view=VoiceStateActionView(channel, "mute", "Chọn thành viên để mute..."),
            ephemeral=True
        )

    @discord.ui.button(label="🔊 Unmute", style=discord.ButtonStyle.success, row=2, custom_id="vc_panel:unmute")
    async def unmute_all(self, interaction: discord.Interaction, button: discord.ui.Button):
        channel = await check_owner(interaction)
        if channel is None:
            return
        if not self._has_human_targets(channel):
            return await interaction.response.send_message("❌ Không có thành viên nào trong phòng.", ephemeral=True)

        await interaction.response.send_message(
            "Chọn người cần mở khóa mic:",
            view=VoiceStateActionView(channel, "unmute", "Chọn thành viên để unmute..."),
            ephemeral=True
        )

    @discord.ui.button(label="🚫 Ban", style=discord.ButtonStyle.danger, row=2, custom_id="vc_panel:ban")
    async def ban(self, interaction: discord.Interaction, button: discord.ui.Button):
        channel = await check_owner(interaction)
        if channel is None:
            return

        await interaction.response.send_message(
            "Chọn thành viên cần cấm:",
            view=BanMemberView(channel),
            ephemeral=True
        )

    @discord.ui.button(label="✅ Unban", style=discord.ButtonStyle.success, row=2, custom_id="vc_panel:unban")
    async def unban(self, interaction: discord.Interaction, button: discord.ui.Button):
        channel = await check_owner(interaction)
        if channel is None:
            return

        if not banned_members.get(channel.id):
            return await interaction.response.send_message(
                "❌ Hiện không có ai nằm trong danh sách bị cấm.",
                ephemeral=True
            )

        await interaction.response.send_message(
            "Chọn người cần bỏ cấm:",
            view=UnbanMemberView(channel),
            ephemeral=True
        )


    @discord.ui.button(label="🔈 Tắt âm", style=discord.ButtonStyle.secondary, row=3, custom_id="vc_panel:deafen")
    async def deafen(self, interaction: discord.Interaction, button: discord.ui.Button):
        channel = await check_owner(interaction)
        if channel is None:
            return
        if not self._has_human_targets(channel):
            return await interaction.response.send_message("❌ Không có thành viên nào trong phòng.", ephemeral=True)

        await interaction.response.send_message(
            "Chọn thành viên cần tắt âm:",
            view=VoiceStateActionView(channel, "deafen", "Chọn thành viên để tắt âm..."),
            ephemeral=True
        )

    @discord.ui.button(label="🔊 Bật âm", style=discord.ButtonStyle.success, row=3, custom_id="vc_panel:undeafen")
    async def undeafen(self, interaction: discord.Interaction, button: discord.ui.Button):
        channel = await check_owner(interaction)
        if channel is None:
            return
        if not self._has_human_targets(channel):
            return await interaction.response.send_message("❌ Không có thành viên nào trong phòng.", ephemeral=True)

        await interaction.response.send_message(
            "Chọn thành viên cần bật âm:",
            view=VoiceStateActionView(channel, "undeafen", "Chọn thành viên để bật âm..."),
            ephemeral=True
        )


    @discord.ui.button(label="🙋 Nhận phòng", style=discord.ButtonStyle.secondary, row=4, custom_id="vc_panel:claim")
    async def claim(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not interaction.user.voice or not interaction.user.voice.channel:
            return await interaction.response.send_message(
                "❌ Bạn phải đang ở trong phòng Voice này mới có thể nhận phòng.",
                ephemeral=True
            )

        channel = interaction.user.voice.channel
        if channel.id not in temp_channels or channel.id != interaction.channel_id:
            return await interaction.response.send_message(
                "❌ Đây không phải là phòng Voice tạm thời hợp lệ.",
                ephemeral=True
            )

        current_owner_id = temp_channels.get(channel.id)
        if current_owner_id == interaction.user.id:
            return await interaction.response.send_message(
                "❌ Bạn đã là chủ phòng rồi!",
                ephemeral=True
            )

        if any(m.id == current_owner_id for m in channel.members):
            return await interaction.response.send_message(
                "❌ Chủ phòng hiện tại vẫn đang ở trong kênh Voice.",
                ephemeral=True
            )

        temp_channels[channel.id] = interaction.user.id
        owner_overwrite = apply_owner_permissions(channel.overwrites_for(interaction.user))
        await channel.set_permissions(interaction.user, overwrite=owner_overwrite)

        await interaction.response.send_message(
            f"👑 {interaction.user.mention} đã nhận quyền chủ phòng!",
            ephemeral=False
        )

    @discord.ui.button(label="♻️ Reset", style=discord.ButtonStyle.primary, row=4, custom_id="vc_panel:reset")
    async def reset(self, interaction: discord.Interaction, button: discord.ui.Button):
        channel = await check_owner(interaction)
        if channel is None:
            return

        banned_members.pop(channel.id, None)

        overwrites = {
            interaction.guild.default_role: discord.PermissionOverwrite(
                connect=True,
                view_channel=True
            ),
            interaction.guild.me: discord.PermissionOverwrite(
                view_channel=True,
                connect=True,
                manage_channels=True,
                manage_permissions=True,
                move_members=True
            ),
            interaction.user: apply_owner_permissions(discord.PermissionOverwrite())
        }

        await channel.edit(overwrites=overwrites, user_limit=0, status=None)
        await interaction.response.send_message(
            "✅ Đã đặt lại toàn bộ quyền, trạng thái, danh sách cấm và giới hạn phòng về mặc định.",
            ephemeral=True
        )

    @discord.ui.button(label="🗑️ Xóa", style=discord.ButtonStyle.danger, row=4, custom_id="vc_panel:delete")
    async def delete(self, interaction: discord.Interaction, button: discord.ui.Button):
        channel = await check_owner(interaction)
        if channel is None:
            return

        temp_channels.pop(channel.id, None)
        banned_members.pop(channel.id, None)

        await interaction.response.send_message(
            "🗑️ Đang xóa phòng...",
            ephemeral=True
        )

        try:
            await channel.delete(reason=f"Được xóa bởi chủ phòng {interaction.user}")
        except (discord.NotFound, discord.Forbidden, discord.HTTPException):
            pass
