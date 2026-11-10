import discord
from discord.ext import commands
from discord import app_commands
import json
import os
import io
import asyncio
from datetime import datetime
from Check.i18n import t, is_vietnamese

TICKET_CONFIG_FILE = "data/ticket_config.json"
OPEN_TICKETS_FILE = "data/open_tickets.json"

def load_json_data(file_path):
    """Tải dữ liệu từ file JSON một cách an toàn."""
    if os.path.exists(file_path):
        with open(file_path, 'r', encoding='utf-8') as f:
            try:
                return json.load(f)
            except json.JSONDecodeError:
                return {}
    return {}

def save_json_data(data, file_path):
    """Lưu dữ liệu vào file JSON, tự động tạo thư mục nếu cần."""
    os.makedirs(os.path.dirname(file_path), exist_ok=True)
    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=4)

class CloseTicketView(discord.ui.View):
    def __init__(self, guild=None):
        super().__init__(timeout=None)
        if guild:
            self.close_ticket.label = t(guild, "TICKET_CLOSE_BTN")

    @discord.ui.button(label="Đóng Ticket", style=discord.ButtonStyle.danger, emoji="🔒", custom_id="close_ticket_button")
    async def close_ticket(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer()

        open_tickets = load_json_data(OPEN_TICKETS_FILE)
        ticket_creator_id = None
        for user_id, channel_id in open_tickets.items():
            if channel_id == interaction.channel.id:
                ticket_creator_id = user_id
                break

        if not ticket_creator_id:
            error_embed = discord.Embed(title=t(interaction.guild, "TICKET_ERROR_TITLE"), description=t(interaction.guild, "TICKET_ERROR_NOT_FOUND"), color=discord.Color.red())
            await interaction.followup.send(embed=error_embed, ephemeral=True)
            if interaction.channel.name.startswith("ticket-"):
                 warning_embed = discord.Embed(
                    description=t(interaction.guild, "TICKET_DELETE_WARNING"),
                    color=discord.Color.orange()
                 )
                 await asyncio.sleep(5)
                 await interaction.channel.delete(reason="Ticket không có trong dữ liệu.")
            return

        ticket_creator = interaction.guild.get_member(int(ticket_creator_id))

        ticket_config = load_json_data(TICKET_CONFIG_FILE)
        guild_config = ticket_config.get(str(interaction.guild_id))
        if guild_config and guild_config.get("log_channel_id"):
            log_channel = interaction.guild.get_channel(guild_config["log_channel_id"])
            if log_channel:
                transcript = f"Transcript cho ticket của {ticket_creator.name if ticket_creator else 'Không rõ'} (ID: {ticket_creator_id})\n"
                transcript += f"Kênh: #{interaction.channel.name} (ID: {interaction.channel.id})\n"
                transcript += f"Người đóng: {interaction.user.name} (ID: {interaction.user.id})\n"
                transcript += f"Thời gian đóng: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"

                messages = []
                async for msg in interaction.channel.history(limit=None, oldest_first=True):
                    messages.append(f"[{msg.created_at.strftime('%d/%m %H:%M')}] {msg.author.name}: {msg.content}")
                
                transcript += "\n".join(messages)

                transcript_file = discord.File(io.BytesIO(transcript.encode()), filename=f"ticket-{interaction.channel.name}.txt")
                await log_channel.send(t(interaction.guild, "TICKET_TRANSCRIPT_SENT", mention=ticket_creator.mention if ticket_creator else 'Người dùng đã rời đi'), file=transcript_file)

        del open_tickets[ticket_creator_id]
        save_json_data(open_tickets, OPEN_TICKETS_FILE)

        if ticket_creator:
            try:
                dm_embed = discord.Embed(
                    title=t(interaction.guild, "TICKET_DM_CLOSED_TITLE"),
                    description=t(interaction.guild, "TICKET_DM_CLOSED_DESC", guild_name=interaction.guild.name, mention=interaction.user.mention),
                    color=discord.Color.blue()
                )
                await ticket_creator.send(embed=dm_embed)
            except discord.Forbidden:
                pass

        closing_embed = discord.Embed(
            description=t(interaction.guild, "TICKET_CLOSING_DESC"),
            color=discord.Color.orange()
        )
        await interaction.channel.send(embed=closing_embed)
        await asyncio.sleep(5)
        await interaction.channel.delete(reason="Ticket đã được đóng.")

class SpeakAsModal(discord.ui.Modal, title="Gửi tin nhắn thay mặt"):
    def __init__(self):
        super().__init__(timeout=None)

    target_user = discord.ui.UserSelect(
        placeholder="Chọn người dùng bạn muốn gửi tin nhắn thay...",
        min_values=1,
        max_values=1,
        row=0
    )

    message_content = discord.ui.TextInput(
        label="Nội dung tin nhắn",
        style=discord.TextStyle.paragraph,
        placeholder="Nhập nội dung bạn muốn gửi thay cho người dùng...",
        required=True,
        row=1
    )

    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        member = self.target_user.values[0]
        content = self.message_content.value

        if not isinstance(member, discord.Member):
            member = await interaction.guild.fetch_member(member.id)

        webhook = None
        webhooks = await interaction.channel.webhooks()
        for wh in webhooks:
            if wh.name == "Ticket Webhook":
                webhook = wh
                break
        
        if not webhook:
            try:
                webhook = await interaction.channel.create_webhook(name="Ticket Webhook", reason="Để gửi tin nhắn thay mặt trong ticket")
            except discord.Forbidden:
                return await interaction.followup.send(t(interaction.guild, "TICKET_WEBHOOK_NO_PERM"), ephemeral=True)

        try:
            await webhook.send(
                content=content,
                username=member.display_name,
                avatar_url=member.display_avatar.url,
                thread=interaction.channel if isinstance(interaction.channel, discord.Thread) else None
            )
            await interaction.followup.send(t(interaction.guild, "TICKET_WEBHOOK_SENT"), ephemeral=True)
        except Exception as e:
            await interaction.followup.send(t(interaction.guild, "TICKET_WEBHOOK_ERROR", error=e), ephemeral=True)


class TicketActionView(CloseTicketView):
    def __init__(self, guild=None):
        super().__init__(guild=guild)
        if guild:
            self.speak_as.label = t(guild, "TICKET_BTN_SPEAK_AS")

    @discord.ui.button(label="Gửi tin thay mặt", style=discord.ButtonStyle.secondary, emoji="🗣️", custom_id="speak_as_button")
    async def speak_as(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not interaction.user.guild_permissions.manage_messages:
            return await interaction.response.send_message(t(interaction.guild, "TICKET_NO_PERM_SPEAK"), ephemeral=True)
        await interaction.response.send_modal(SpeakAsModal())

class TicketCreationModal(discord.ui.Modal, title="Tạo Ticket Hỗ Trợ Mới"):
    def __init__(self, topic_value: str, topic_label: str):
        super().__init__()
        self.topic_value = topic_value
        self.topic_label = topic_label

    title_input = discord.ui.TextInput(
        label="Tiêu đề",
        placeholder="Tóm tắt ngắn gọn vấn đề của bạn...",
        required=True,
        max_length=100,
        custom_id="ticket_title_input"
    )

    description_input = discord.ui.TextInput(
        label="Mô tả chi tiết",
        style=discord.TextStyle.paragraph,
        placeholder="Vui lòng mô tả chi-tiết vấn đề bạn đang gặp phải.",
        required=True,
        max_length=1000,
        custom_id="ticket_desc_input"
    )

    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)

        topic_value = self.topic_value
        topic_label = self.topic_label
        ticket_title = self.title_input.value
        ticket_description = self.description_input.value

        ticket_config = load_json_data(TICKET_CONFIG_FILE)
        guild_config = ticket_config.get(str(interaction.guild_id))
        ticket_channel_parent = interaction.guild.get_channel(guild_config["ticket_channel_id"])
        support_role = interaction.guild.get_role(guild_config["support_role_id"])

        if not ticket_channel_parent or not support_role:
            error_embed = discord.Embed(title=t(interaction.guild, "TICKET_ERROR_CONFIG_TITLE"), description=t(interaction.guild, "TICKET_ERROR_CONFIG"), color=discord.Color.red())
            return await interaction.followup.send(embed=error_embed, ephemeral=True)

        channel_name = f"{topic_value}-{interaction.user.name}"
        ticket_thread = await ticket_channel_parent.create_thread(
            name=channel_name,
            type=discord.ChannelType.private_thread,
            reason=f"Ticket được tạo bởi {interaction.user.name}"
        )

        open_tickets = load_json_data(OPEN_TICKETS_FILE)
        open_tickets[str(interaction.user.id)] = ticket_thread.id
        save_json_data(open_tickets, OPEN_TICKETS_FILE)

        ticket_embed = discord.Embed(
            title=f"📝 {ticket_title}",
            description=ticket_description,
            color=discord.Color.green(),
            timestamp=datetime.now()
        )
        ticket_embed.set_author(name=f"Ticket từ {interaction.user.display_name}", icon_url=interaction.user.display_avatar.url)
        ticket_embed.add_field(name=t(interaction.guild, "TICKET_FIELD_TOPIC"), value=topic_label, inline=True)
        
        await ticket_thread.add_user(interaction.user)
        await ticket_thread.send(content=t(interaction.guild, "TICKET_GREETING", mention=interaction.user.mention, role_mention=support_role.mention), embed=ticket_embed, view=TicketActionView(interaction.guild))

        success_embed = discord.Embed(
            title=t(interaction.guild, "TICKET_CREATED_TITLE"),
            description=t(interaction.guild, "TICKET_CREATED_DESC", mention=ticket_thread.mention),
            color=discord.Color.green()
        )
        await interaction.followup.send(embed=success_embed, ephemeral=True)

class TopicSelectView(discord.ui.View):
    def __init__(self, author_id: int):
        super().__init__(timeout=60)
        self.author_id = author_id

    @discord.ui.select(
        placeholder="Chọn chủ đề cho ticket của bạn...",
        options=[
            discord.SelectOption(label="Báo lỗi", description="Báo cáo lỗi kỹ thuật của bot hoặc server.", emoji="🐛", value="lỗi"),
            discord.SelectOption(label="Khiếu nại", description="Khiếu nại về một thành viên hoặc một quyết định.", emoji="⚖️", value="khiếu-nại"),
            discord.SelectOption(label="Hỏi đáp", description="Đặt câu hỏi chung cho đội ngũ quản trị.", emoji="❓", value="hỏi-đáp"),
            discord.SelectOption(label="Khác", description="Các vấn đề khác không thuộc các loại trên.", emoji="📁", value="khác"),
        ]
    )
    async def select_callback(self, interaction: discord.Interaction, select: discord.ui.Select):
        if interaction.user.id != self.author_id:
            error_embed = discord.Embed(description=t(interaction.guild, "TICKET_NOT_YOURS"), color=discord.Color.red())
            return await interaction.response.send_message(embed=error_embed, ephemeral=True)

        topic_value = select.values[0]
        topic_label = next((opt.label for opt in select.options if opt.value == topic_value), "Không rõ")
        
        await interaction.response.send_modal(TicketCreationModal(topic_value, topic_label))

class TicketPanelView(discord.ui.View):
    def __init__(self, guild=None):
        super().__init__(timeout=None)
        if guild:
            self.create_ticket.label = t(guild, "TICKET_BTN_CREATE")

    @discord.ui.button(label="Tạo Ticket Hỗ Trợ", style=discord.ButtonStyle.success, emoji="📩", custom_id="create_ticket_button")
    async def create_ticket(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer(ephemeral=True, thinking=True)

        ticket_config = load_json_data(TICKET_CONFIG_FILE)
        open_tickets = load_json_data(OPEN_TICKETS_FILE)
        guild_id_str = str(interaction.guild_id)
        user_id_str = str(interaction.user.id)
        
        if guild_id_str not in ticket_config:
            error_embed = discord.Embed(title=t(interaction.guild, "TICKET_NOT_SETUP_TITLE"), description=t(interaction.guild, "TICKET_NOT_SETUP"), color=discord.Color.red())
            return await interaction.followup.send(embed=error_embed, ephemeral=True)

        if user_id_str in open_tickets:
            existing_channel_id = open_tickets[user_id_str]
            existing_channel = interaction.guild.get_channel(existing_channel_id)
            if existing_channel:
                error_embed = discord.Embed(title=t(interaction.guild, "TICKET_ALREADY_OPEN_TITLE"), description=t(interaction.guild, "TICKET_ALREADY_OPEN", mention=existing_channel.mention), color=discord.Color.orange())
                return await interaction.followup.send(embed=error_embed, ephemeral=True)
            else:
                del open_tickets[user_id_str]
                save_json_data(open_tickets, OPEN_TICKETS_FILE)

        guild_config = ticket_config[guild_id_str]
        if not guild_config.get("support_role_id") or not guild_config.get("ticket_channel_id"):
            error_embed = discord.Embed(title=t(interaction.guild, "TICKET_ERROR_CONFIG_TITLE"), description=t(interaction.guild, "TICKET_ERROR_CONFIG"), color=discord.Color.red())
            return await interaction.followup.send(embed=error_embed, ephemeral=True)

        view = TopicSelectView(interaction.user.id)
        await interaction.followup.send(t(interaction.guild, "TICKET_STEP1"), view=view, ephemeral=True)


class TicketCog(commands.Cog, name="Hệ Thống Ticket"):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_ready(self):
        """Đăng ký các view persistent khi bot khởi động."""
        self.bot.add_view(TicketPanelView())
        self.bot.add_view(CloseTicketView())
        self.bot.add_view(TicketActionView())
        print("✅ Đã nạp các View của hệ thống Ticket.")

    @commands.hybrid_group(name="ticket", description="Các lệnh quản lý hệ thống ticket hỗ trợ.")
    @commands.has_permissions(administrator=True)
    async def ticket(self, ctx: commands.Context):
        """Lệnh gốc cho nhóm ticket."""
        if ctx.invoked_subcommand is None:
            await ctx.send_help(ctx.command)

    @ticket.command(name="setup", description="Cài đặt hệ thống ticket cho server.")
    @app_commands.describe(
        panel_channel="Kênh để đặt bảng điều khiển tạo ticket.",
        support_role="Vai trò (role) của đội ngũ hỗ trợ (mod, admin).",
        log_channel="[TÙY CHỌN] Kênh để lưu lại nội dung các ticket đã đóng."
    )
    @commands.has_permissions(administrator=True)
    async def setup_ticket(
        self,
        ctx: commands.Context,
        panel_channel: discord.TextChannel,
        support_role: discord.Role,
        log_channel: discord.TextChannel = None
    ):
        """Cài đặt và tạo bảng điều khiển ticket."""
        await ctx.defer(ephemeral=True)

        ticket_config = load_json_data(TICKET_CONFIG_FILE)
        guild_id_str = str(ctx.guild.id)
        ticket_config[guild_id_str] = {
            "panel_channel_id": panel_channel.id,
            "ticket_channel_id": panel_channel.id,
            "log_channel_id": log_channel.id if log_channel else None,
            "support_role_id": support_role.id
        }
        save_json_data(ticket_config, TICKET_CONFIG_FILE)

        panel_embed = discord.Embed(
            title=t(ctx.guild, "TICKET_PANEL_TITLE"),
            description=t(ctx.guild, "TICKET_PANEL_DESC"),
            color=discord.Color.blue()
        )
        panel_embed.set_footer(text=t(ctx.guild, "TICKET_PANEL_FOOTER"))

        try:
            await panel_channel.send(embed=panel_embed, view=TicketPanelView(interaction.guild if 'interaction' in locals() else getattr(ctx, 'guild', None)))
        except discord.Forbidden:
            error_embed = discord.Embed(title=t(ctx.guild, "TICKET_NO_PERM_TITLE"), description=t(ctx.guild, "TICKET_NO_PERM_PANEL"), color=discord.Color.red())
            return await ctx.send(embed=error_embed, ephemeral=True)

        success_embed = discord.Embed(
            title=t(ctx.guild, "TICKET_SETUP_SUCCESS_TITLE"),
            description=t(ctx.guild, "TICKET_SETUP_SUCCESS_DESC"),
            color=discord.Color.green()
        )
        success_embed.add_field(name=t(ctx.guild, "TICKET_FIELD_PANEL_CHANNEL"), value=panel_channel.mention, inline=False)
        success_embed.add_field(name=t(ctx.guild, "TICKET_FIELD_LOG_CHANNEL"), value=log_channel.mention if log_channel else t(ctx.guild, "TICKET_FIELD_NO_LOG"), inline=False)
        success_embed.add_field(name=t(ctx.guild, "TICKET_FIELD_SUPPORT_ROLE"), value=support_role.mention, inline=False)

        await ctx.send(embed=success_embed, ephemeral=True)

    @ticket.command(name="panel", description="Gửi lại bảng điều khiển tạo ticket đến một kênh.")
    @app_commands.describe(channel="Kênh để gửi bảng điều khiển. Mặc định là kênh hiện tại.")
    @commands.has_permissions(administrator=True)
    async def send_panel(self, ctx: commands.Context, channel: discord.TextChannel = None):
        """Gửi lại bảng điều khiển tạo ticket mà không cần setup lại."""
        await ctx.defer(ephemeral=True)

        target_channel = channel or ctx.channel

        ticket_config = load_json_data(TICKET_CONFIG_FILE)
        guild_id_str = str(ctx.guild.id)

        if guild_id_str not in ticket_config:
            error_embed = discord.Embed(
                title=t(ctx.guild, "TICKET_NOT_SETUP_TITLE"),
                description=t(ctx.guild, "TICKET_NOT_SETUP"),
                color=discord.Color.red()
            )
            return await ctx.send(embed=error_embed, ephemeral=True)

        panel_embed = discord.Embed(
            title=t(ctx.guild, "TICKET_PANEL_TITLE"),
            description=t(ctx.guild, "TICKET_PANEL_DESC"),
            color=discord.Color.blue()
        )
        panel_embed.set_footer(text=t(ctx.guild, "TICKET_PANEL_FOOTER"))

        await target_channel.send(embed=panel_embed, view=TicketPanelView(interaction.guild if 'interaction' in locals() else getattr(ctx, 'guild', None)))
        success_embed = discord.Embed(
            title=t(ctx.guild, "TICKET_PANEL_SENT_TITLE"),
            description=t(ctx.guild, "TICKET_PANEL_SENT_SUCCESS", mention=target_channel.mention),
            color=discord.Color.green()
        )
        await ctx.send(embed=success_embed, ephemeral=True)

    @ticket.command(name="close", description="Đóng ticket hiện tại (chỉ dùng trong kênh ticket).")
    @commands.has_permissions(manage_channels=True)
    async def close_ticket_command(self, ctx: commands.Context):
        """Lệnh đóng ticket thủ công."""
        open_tickets = load_json_data(OPEN_TICKETS_FILE)
        if not isinstance(ctx.channel, discord.Thread) or ctx.channel.id not in open_tickets.values():
            error_embed = discord.Embed(title=t(ctx.guild, "TICKET_WRONG_CHANNEL_TITLE"), description=t(ctx.guild, "TICKET_WRONG_CHANNEL_DESC"), color=discord.Color.orange())
            return await ctx.send(embed=error_embed, ephemeral=True)

        class FakeInteraction:
            class _FakeResponse:
                async def defer(self, ephemeral: bool = False, thinking: bool = False) -> None:
                    pass
            class _FakeFollowup:
                def __init__(self, channel):
                    self._channel = channel
                async def send(self, *args, **kwargs):
                    kwargs.pop('ephemeral', None)
                    return await self._channel.send(*args, **kwargs)

            def __init__(self, ctx: commands.Context):
                self.guild = ctx.guild
                self.channel = ctx.channel
                self.user = ctx.author
                self.guild_id = ctx.guild.id
                self.response = self._FakeResponse()
                self.followup = self._FakeFollowup(ctx.channel)

        fake_interaction = FakeInteraction(ctx)
        view = CloseTicketView()
        await view.close_ticket(fake_interaction, None)

    @ticket.command(name="adduser", description="Thêm một thành viên vào ticket hiện tại.")
    @app_commands.describe(member="Thành viên cần thêm vào ticket.")
    @commands.has_permissions(manage_threads=True)
    async def add_user_to_ticket(self, ctx: commands.Context, member: discord.Member):
        """Thêm một người dùng vào luồng ticket."""
        open_tickets = load_json_data(OPEN_TICKETS_FILE)
        if not isinstance(ctx.channel, discord.Thread) or ctx.channel.id not in open_tickets.values():
            error_embed = discord.Embed(title=t(ctx.guild, "TICKET_WRONG_CHANNEL_TITLE"), description=t(ctx.guild, "TICKET_WRONG_CHANNEL_DESC"), color=discord.Color.orange())
            return await ctx.send(embed=error_embed, ephemeral=True)

        try:
            await ctx.channel.add_user(member)
            
            success_embed = discord.Embed(description=t(ctx.guild, "TICKET_ADD_SUCCESS", mention=member.mention), color=discord.Color.green())
            await ctx.send(embed=success_embed, ephemeral=True)
            
            notification_embed = discord.Embed(description=t(ctx.guild, "TICKET_ADD_NOTIFY", mention=member.mention, author_mention=ctx.author.mention), color=discord.Color.blue())
            await ctx.channel.send(embed=notification_embed)

        except Exception as e:
            error_embed = discord.Embed(title=t(ctx.guild, "TICKET_ERROR_GENERIC"), description=t(ctx.guild, "TICKET_ADD_ERROR", error=e), color=discord.Color.red())
            await ctx.send(embed=error_embed, ephemeral=True)

    @ticket.command(name="removeuser", description="Xóa một thành viên khỏi ticket hiện tại.")
    @app_commands.describe(member="Thành viên cần xóa khỏi ticket.")
    @commands.has_permissions(manage_threads=True)
    async def remove_user_from_ticket(self, ctx: commands.Context, member: discord.Member):
        """Xóa một người dùng khỏi luồng ticket."""
        open_tickets = load_json_data(OPEN_TICKETS_FILE)
        if not isinstance(ctx.channel, discord.Thread) or ctx.channel.id not in open_tickets.values():
            error_embed = discord.Embed(title=t(ctx.guild, "TICKET_WRONG_CHANNEL_TITLE"), description=t(ctx.guild, "TICKET_WRONG_CHANNEL_DESC"), color=discord.Color.orange())
            return await ctx.send(embed=error_embed, ephemeral=True)

        ticket_creator_id = None
        for user_id, channel_id in open_tickets.items():
            if channel_id == ctx.channel.id:
                ticket_creator_id = user_id
                break
        
        if str(member.id) == ticket_creator_id:
            error_embed = discord.Embed(title=t(ctx.guild, "TICKET_CANNOT_REMOVE_TITLE"), description=t(ctx.guild, "TICKET_CANNOT_REMOVE_CREATOR"), color=discord.Color.red())
            return await ctx.send(embed=error_embed, ephemeral=True)

        try:
            await ctx.channel.remove_user(member)

            success_embed = discord.Embed(description=t(ctx.guild, "TICKET_REMOVE_SUCCESS", mention=member.mention), color=discord.Color.green())
            await ctx.send(embed=success_embed, ephemeral=True)

            notification_embed = discord.Embed(description=t(ctx.guild, "TICKET_REMOVE_NOTIFY", mention=member.mention, author_mention=ctx.author.mention), color=discord.Color.orange())
            await ctx.channel.send(embed=notification_embed)

        except Exception as e:
            error_embed = discord.Embed(title=t(ctx.guild, "TICKET_ERROR_GENERIC"), description=t(ctx.guild, "TICKET_REMOVE_ERROR", error=e), color=discord.Color.red())
            await ctx.send(embed=error_embed, ephemeral=True)


async def setup(bot: commands.Bot):
    await bot.add_cog(TicketCog(bot))
