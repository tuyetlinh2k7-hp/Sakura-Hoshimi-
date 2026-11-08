import discord
import traceback
from discord import commands
from Command.confession import load_config, get_and_increment_cfs_number

def create_panel_embed():
    embed = discord.Embed(
        title="📮 **NƠI TÂM SỰ** (*CONFESSIONS*)",
        description=(
            "🌸 Nơi bạn có thể tự do chia sẻ tâm tư, tình cảm hay những câu chuyện thầm kín nhất.\n\n"
            "🌸 **HƯỚNG DẪN SỬ DỤNG:**\n"
            "* 🌸 Nhấn **Gửi Ẩn Danh**: Thông tin của bạn sẽ bị giấu.\n"
            "* 🌸 Nhấn **Gửi Công Khai**: Thông tin của bạn sẽ bị phơi bày lên bài đăng >~< ."
        ),
        color=0x2F3136
    )
    embed.set_footer(text="🌸 Hệ thống Tự Động • An toàn và Bảo mật 🌸")
    return embed

class ConfessionModal(discord.ui.Modal):
    def __init__(self, bot: commands.Bot, anonymous: bool):
        super().__init__(title="💌 Confession Ẩn Danh" if anonymous else "📢 Confession Công Khai")
        self.bot = bot
        self.anonymous = anonymous

        self.content = discord.ui.TextInput(
            label="🌸 Tâm sự của bạn",
            style=discord.TextStyle.paragraph,
            placeholder="Bạn có gì muốn tâm sự? Hãy viết ra đây nhé...",
            max_length=4000,
            required=True
        )
        self.add_item(self.content)

    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)

        guild_id_str = str(interaction.guild_id)
        config = load_config()
        
        if guild_id_str not in config:
            await interaction.followup.send("[🌸 SAKURA] Hệ thống Confession chưa được thiết lập.", ephemeral=True)
            return

        cfs_number = get_and_increment_cfs_number()
        cfs_title = f"🌸 Phòng Tâm Sự số {cfs_number}"
        channel = interaction.channel

        try:
            if interaction.message:
                try: await interaction.message.delete()
                except discord.NotFound: pass

            embed_cfs = discord.Embed(
                title=f"💌 {cfs_title}",
                description=f"{self.content.value}",
                color=0x2F3136,
                timestamp=discord.utils.utcnow()
            )
            if self.anonymous:
                embed_cfs.set_footer(text="🌸 Gửi ẩn danh")
            else:
                embed_cfs.set_footer(text=f"🌸 Gửi bởi {interaction.user.display_name}")

            cfs_message = await channel.send(embed=embed_cfs, view=ReplyView(self.bot))

            await cfs_message.create_thread(
                name=f"Trả lời {cfs_title}",
                auto_archive_duration=1440
            )

            new_panel_embed = create_panel_embed()
            await channel.send(embed=new_panel_embed, view=CreateConfessionView(self.bot))

            await interaction.followup.send(f"[🌸 SAKURA] Tâm sự đã được đăng!", ephemeral=True)
            
            cog = self.bot.get_cog("ConfessionCog")
            if cog:
                await cog.send_log(
                    guild_id=interaction.guild_id,
                    title=f"📝 Log: {cfs_title}",
                    description=f"**Người gửi:** {interaction.user.mention}\n**Nội dung:**\n```\n{self.content.value}\n```",
                    color=discord.Color.green()
                )
        except Exception as e:
            await interaction.followup.send("[🌸 SAKURA] Đã xảy ra lỗi khi đăng bài.", ephemeral=True)
            traceback.print_exc()


class CreateConfessionView(discord.ui.View):
    def __init__(self, bot: commands.Bot):
        super().__init__(timeout=None)
        self.bot = bot

    @discord.ui.button(label="Gửi Ẩn Danh", emoji="💌", style=discord.ButtonStyle.secondary, custom_id="cfs_anonymous")
    async def anonymous(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(ConfessionModal(self.bot, anonymous=True))

    @discord.ui.button(label="Gửi Công Khai", emoji="📢", style=discord.ButtonStyle.primary, custom_id="cfs_public")
    async def public(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(ConfessionModal(self.bot, anonymous=False))


class ReplyModal(discord.ui.Modal, title="Bình luận ẩn danh"):
    def __init__(self, bot: commands.Bot):
        super().__init__()
        self.bot = bot

    content = discord.ui.TextInput(
        label="🌸 Nội dung bình luận", style=discord.TextStyle.paragraph, max_length=2000, required=True
    )

    async def on_submit(self, interaction: discord.Interaction):
        thread = interaction.message.thread
        if not thread:
            return await interaction.response.send_message("❌ Không tìm thấy thread!", ephemeral=True)

        embed = discord.Embed(description=self.content.value, color=0x2b2d31, timestamp=discord.utils.utcnow())
        embed.set_author(name="Người dùng ẩn danh", icon_url="https://cdn.discordapp.com/embed/avatars/0.png")
        
        await thread.send(embed=embed)
        await interaction.response.send_message("[🌸 SAKURA] Đã gửi bình luận!", ephemeral=True)

        cog = self.bot.get_cog("ConfessionCog")
        if cog:
            await cog.send_log(
                guild_id=interaction.guild_id,
                title="💬 Log: Bình luận ẩn danh",
                description=f"**Người bình luận:** {interaction.user.mention}\n**Nội dung:**\n```\n{self.content.value}\n```",
                color=discord.Color.yellow()
            )

class ReplyView(discord.ui.View):
    def __init__(self, bot: commands.Bot):
        super().__init__(timeout=None)
        self.bot = bot

    @discord.ui.button(label="Trả lời ẩn danh", emoji="💬", style=discord.ButtonStyle.secondary, custom_id="cfs_reply_in_thread")
    async def reply(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(ReplyModal(self.bot))