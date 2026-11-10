import discord
from discord.ext import commands
from Check.mod import has_admin_role, log_if_admin_or_owner
from Check.i18n import t

class EmbedBuilderModal(discord.ui.Modal, title="🎨 Thiết Kế Discord Embed"):
    embed_title = discord.ui.TextInput(
        label="Tiêu đề (Title)", 
        placeholder="Nhập tiêu đề cho Embed...", 
        required=False, max_length=256
    )
    embed_description = discord.ui.TextInput(
        label="Nội dung (Description)", 
        style=discord.TextStyle.paragraph,
        placeholder="Nhập nội dung hiển thị chính ở đây...", 
        required=True, max_length=4000
    )
    embed_color = discord.ui.TextInput(
        label="Mã màu Hex (Ví dụ: #ffb6c1 hoặc lướt qua)", 
        placeholder="Mặc định sẽ là màu ngẫu nhiên...", 
        required=False, max_length=7
    )
    embed_thumbnail = discord.ui.TextInput(
        label="Link ảnh nhỏ (Thumbnail URL)", 
        placeholder="https://example.com/image.png", 
        required=False
    )
    embed_image = discord.ui.TextInput(
        label="Link ảnh lớn (Image URL)", 
        placeholder="https://example.com/banner.png", 
        required=False
    )

    def __init__(self, guild=None):
        super().__init__(title=t(guild, "EMBED_MODAL_TITLE"))
        try:
            self.embed_title.label = t(guild, "EMBED_LABEL_TITLE")
            self.embed_title.placeholder = t(guild, "EMBED_PLACEHOLDER_TITLE")
            self.embed_description.label = t(guild, "EMBED_LABEL_DESC")
            self.embed_description.placeholder = t(guild, "EMBED_PLACEHOLDER_DESC")
            self.embed_color.label = t(guild, "EMBED_LABEL_COLOR")
            self.embed_color.placeholder = t(guild, "EMBED_PLACEHOLDER_COLOR")
            self.embed_thumbnail.label = t(guild, "EMBED_LABEL_THUMB")
            self.embed_image.label = t(guild, "EMBED_LABEL_IMAGE")
        except:
            pass

    async def on_submit(self, interaction: discord.Interaction):
        color = discord.Color.random()
        if self.embed_color.value:
            try:
                hex_color = self.embed_color.value.lstrip('#')
                color = discord.Color(int(hex_color, 16))
            except ValueError:
                pass

        embed = discord.Embed(
            title=self.embed_title.value if self.embed_title.value else None,
            description=self.embed_description.value,
            color=color
        )

        if self.embed_thumbnail.value and self.embed_thumbnail.value.startswith(("http://", "https://")):
            embed.set_thumbnail(url=self.embed_thumbnail.value)
            
        if self.embed_image.value and self.embed_image.value.startswith(("http://", "https://")):
            embed.set_image(url=self.embed_image.value)

        embed.set_footer(text=t(interaction.guild, "EMBED_FOOTER", name=interaction.user.display_name), icon_url=interaction.user.display_avatar.url)

        await interaction.response.send_message(embed=embed)
        try:
            await interaction.message.delete()
        except:
            pass


class EmbedBuilderView(discord.ui.View):
    def __init__(self, author: discord.Member):
        super().__init__(timeout=60)
        self.author = author

    @discord.ui.button(label="Bắt đầu tạo Embed 🌸", style=discord.ButtonStyle.success, emoji="🛠️")
    async def start_builder(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user != self.author:
            return await interaction.response.send_message(t(interaction.guild, "EMBED_NO_PERM_BTN"), ephemeral=True)
        
        await interaction.response.send_modal(EmbedBuilderModal(guild=interaction.guild))

    async def on_timeout(self):
        for item in self.children:
            item.disabled = True


class EmbedBuilder(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(aliases=["cembed", "makeembed"])
    @has_admin_role()
    @log_if_admin_or_owner("ADMIN_CMD")
    async def buildembed(self, ctx):
        """Lệnh mở bảng điều khiển tạo Embed thủ công"""
        embed = discord.Embed(
            title=t(ctx.guild, "EMBED_PANEL_TITLE"),
            description=t(ctx.guild, "EMBED_PANEL_DESC"),
            color=0xffb6c1
        )
        view = EmbedBuilderView(ctx.author)
        for child in view.children:
            if hasattr(child, 'label'):
                try:
                    child.label = t(ctx.guild, "EMBED_BTN_START")
                except:
                    pass
        msg = await ctx.send(embed=embed, view=view)
        view.message = msg

async def setup(bot):
    await bot.add_cog(EmbedBuilder(bot))
