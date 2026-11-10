import discord
from discord.ext import commands
from discord import app_commands
import math
from Check.i18n import t

class VoiceStatusPaginator(discord.ui.View):
    def __init__(self, embeds: list, author_id: int, guild=None):
        super().__init__(timeout=120)
        self.embeds = embeds
        self.author_id = author_id
        self.guild = guild
        self.current_page = 0
        self.update_buttons()

    def update_buttons(self):
        self.children[0].disabled = self.current_page == 0
        self.children[1].disabled = self.current_page >= len(self.embeds) - 1

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id != self.author_id:
            await interaction.response.send_message(t(interaction.guild, "VOICESTATUS_NOT_YOURS"), ephemeral=True)
            return False
        return True

    @discord.ui.button(label="◀ Trước", style=discord.ButtonStyle.secondary)
    async def previous_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.current_page -= 1
        self.update_buttons()
        await interaction.response.edit_message(embed=self.embeds[self.current_page], view=self)

    @discord.ui.button(label="Sau ▶", style=discord.ButtonStyle.primary)
    async def next_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.current_page += 1
        self.update_buttons()
        await interaction.response.edit_message(embed=self.embeds[self.current_page], view=self)

class VoiceStatusCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.command(name="voicestatus", aliases=["vcstatus"], hidden=True)
    @commands.is_owner()
    async def voice_status(self, ctx: commands.Context):
        """[Owner] Kiểm tra trạng thái các kênh thoại trên tất cả các server."""
        await ctx.defer(ephemeral=True)

        guilds_with_vc = []
        for guild in self.bot.guilds:
            active_channels_text = ""
            for channel in guild.voice_channels:
                if channel.members:
                    members_list = ", ".join([member.display_name for member in channel.members])
                    active_channels_text += t(ctx.guild, "VOICESTATUS_FIELD_CHANNEL", channel=channel.name, count=len(channel.members), members=members_list) + "\n"
            
            if active_channels_text:
                guilds_with_vc.append({"name": guild.name, "value": active_channels_text})

        if not guilds_with_vc:
            embed = discord.Embed(
                title=t(ctx.guild, "VOICESTATUS_TITLE"),
                description=t(ctx.guild, "VOICESTATUS_EMPTY"),
                color=discord.Color.blue()
            )
            return await ctx.send(embed=embed, ephemeral=True)

        embeds = []
        items_per_page = 5
        total_pages = math.ceil(len(guilds_with_vc) / items_per_page)

        for i in range(total_pages):
            embed = discord.Embed(title=t(ctx.guild, "VOICESTATUS_TITLE"), color=discord.Color.blue())
            start_index = i * items_per_page
            end_index = start_index + items_per_page
            for guild_data in guilds_with_vc[start_index:end_index]:
                embed.add_field(name=t(ctx.guild, "VOICESTATUS_FIELD_SERVER", name=guild_data['name']), value=guild_data['value'], inline=False)
            embed.set_footer(text=t(ctx.guild, "VOICESTATUS_FOOTER", cur=i + 1, total=total_pages))
            embeds.append(embed)

        view = VoiceStatusPaginator(embeds, ctx.author.id, ctx.guild)
        await ctx.send(embed=embeds[0], view=view, ephemeral=True)

async def setup(bot: commands.Bot):
    await bot.add_cog(VoiceStatusCog(bot))
