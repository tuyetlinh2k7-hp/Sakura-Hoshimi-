import discord
from discord.ext import commands
from discord import app_commands
import math
from Check.i18n import t

class SearchCommandModal(discord.ui.Modal):
    def __init__(self, bot: commands.Bot, guild):
        super().__init__(title=t(guild, "HELP_SEARCH_TITLE"))
        self.bot = bot
        self.guild = guild

    command_name = discord.ui.TextInput(
        label="Command name",
        placeholder="Example: ping, ban, fish...",
        required=True,
        max_length=50
    )

    async def on_submit(self, interaction: discord.Interaction):
        # Determine guild language for response
        guild = interaction.guild
        query = self.command_name.value.lower().strip()
        found_command = None
        is_slash = False
        prefix = "/"

        found_command = self.bot.get_command(query)
        if not found_command:
            for cmd in self.bot.tree.get_commands():
                if cmd.name == query:
                    found_command = cmd
                    is_slash = True
                    break
        if not found_command:
            await interaction.response.send_message(t(guild, "HELP_SEARCH_NOT_FOUND", query=query), ephemeral=True)
            return
        if is_slash:
            embed = discord.Embed(title=t(guild, "HELP_SEARCH_SLASH_TITLE", name=found_command.name), description=found_command.description or t(guild, "HELP_SEARCH_NO_DESC"), color=discord.Color.green())
            params = " ".join(f"<{p.name}>" for p in found_command.parameters)
            embed.add_field(name=t(guild, "HELP_SEARCH_USAGE"), value=f"`/{found_command.name} {params}`".strip(), inline=False)
        else:
            embed = discord.Embed(title=t(guild, "HELP_SEARCH_PREFIX_TITLE", prefix=prefix, name=found_command.name), description=found_command.short_doc or t(guild, "HELP_SEARCH_NO_DESC"), color=discord.Color.blue())
            usage = f"{prefix}{found_command.name} {found_command.signature}"
            embed.add_field(name=t(guild, "HELP_SEARCH_USAGE"), value=f"`{usage.strip()}`", inline=False)
            if found_command.aliases:
                embed.add_field(name=t(guild, "HELP_SEARCH_ALIASES"), value=", ".join(f"`{prefix}{alias}`" for alias in found_command.aliases), inline=False)
        await interaction.response.send_message(embed=embed, ephemeral=True)


class HelpPaginationView(discord.ui.View):
    def __init__(self, pages: list, user_id: int, bot: commands.Bot, guild):
        super().__init__(timeout=60)
        self.pages = pages
        self.user_id = user_id
        self.current_page = 0
        self.bot = bot
        self.guild = guild
        # Update button labels per language
        for child in self.children:
            if child.custom_id == "help_prev":
                child.label = t(guild, "HELP_BTN_PREV")
            elif child.custom_id == "help_next":
                child.label = t(guild, "HELP_BTN_NEXT")
            elif child.custom_id == "help_search":
                child.label = t(guild, "HELP_BTN_SEARCH")

    async def update_message(self, interaction: discord.Interaction):
        self.btn_prev.disabled = self.current_page == 0
        self.btn_next.disabled = self.current_page == len(self.pages) - 1
        await interaction.response.edit_message(embed=self.pages[self.current_page], view=self)

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id != self.user_id:
            await interaction.response.send_message(t(interaction.guild, "HELP_INTERACTION_ONLY"), ephemeral=True)
            return False
        return True

    @discord.ui.button(label="◀ Prev", style=discord.ButtonStyle.secondary, custom_id="help_prev")
    async def btn_prev(self, interaction: discord.Interaction, button: discord.ui.Button):
        if self.current_page > 0:
            self.current_page -= 1
            await self.update_message(interaction)

    @discord.ui.button(label="Next ▶", style=discord.ButtonStyle.primary, custom_id="help_next")
    async def btn_next(self, interaction: discord.Interaction, button: discord.ui.Button):
        if self.current_page < len(self.pages) - 1:
            self.current_page += 1
            await self.update_message(interaction)

    @discord.ui.button(label="Search", style=discord.ButtonStyle.success, emoji="🔍", custom_id="help_search")
    async def btn_search(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(SearchCommandModal(self.bot, interaction.guild))

    async def on_timeout(self):
        for item in self.children:
            item.disabled = True
        try:
            if self.message:
                await self.message.edit(content=t(self.guild, "HELP_EXPIRED"), view=self)
        except discord.NotFound:
            pass


class HelpCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    def create_pages(self, prefix: str, guild) -> list:
        all_commands_pool = []
        for cmd in self.bot.commands:
            if cmd.hidden:
                continue
            desc = cmd.short_doc or t(guild, "HELP_SEARCH_NO_DESC")
            all_commands_pool.append(f"⌨️ `{prefix}{cmd.name}`\n└ *{desc}*")
        slash_commands = sorted(self.bot.tree.get_commands(), key=lambda c: c.name)
        for cmd in slash_commands:
            all_commands_pool.append(f"🚀 `/{cmd.name}`\n└ *{cmd.description or t(guild, 'HELP_SEARCH_NO_DESC')}*")
        items_per_page = 7
        total_pages = math.ceil(len(all_commands_pool) / items_per_page)
        if total_pages == 0:
            total_pages = 1
        pages = []
        for i in range(total_pages):
            start_idx = i * items_per_page
            end_idx = start_idx + items_per_page
            page_items = all_commands_pool[start_idx:end_idx]
            embed = discord.Embed(
                title=t(guild, "HELP_TITLE"),
                description="\n\n".join(page_items) if page_items else t(guild, "HELP_NO_COMMAND_PUBLIC"),
                color=discord.Color.blue()
            )
            if self.bot.user and self.bot.user.avatar:
                embed.set_thumbnail(url=self.bot.user.avatar.url)
            embed.set_footer(text=t(guild, "HELP_FOOTER", cur=i+1, total=total_pages, count=len(all_commands_pool)))
            pages.append(embed)
        return pages

    async def send_help_pages(self, ctx_or_interaction):
        is_slash = isinstance(ctx_or_interaction, discord.Interaction)
        author = ctx_or_interaction.user if is_slash else ctx_or_interaction.author
        guild = ctx_or_interaction.guild
        prefix = ctx_or_interaction.prefix if not is_slash else "/"
        pages = self.create_pages(prefix, guild)
        if not pages:
            if is_slash:
                await ctx_or_interaction.response.send_message(t(guild, "HELP_NO_COMMAND"), ephemeral=True)
            else:
                await ctx_or_interaction.send(t(guild, "HELP_NO_COMMAND"))
            return
        view = HelpPaginationView(pages, author.id, self.bot, guild)
        view.btn_prev.disabled = True
        if len(pages) <= 1:
            view.btn_next.disabled = True
        if is_slash:
            await ctx_or_interaction.response.send_message(embed=pages[0], view=view)
        else:
            message = await ctx_or_interaction.send(embed=pages[0], view=view)
            view.message = message

    @commands.command(name="help", aliases=["trogiup"], description="View all bot commands / Xem danh sách lệnh")
    async def prefix_help(self, ctx: commands.Context):
        await self.send_help_pages(ctx)

    @app_commands.command(name="help", description="View paginated command list / Xem danh sách lệnh phân trang")
    async def slash_help(self, interaction: discord.Interaction):
        await self.send_help_pages(interaction)


async def setup(bot: commands.Bot):
    bot.remove_command("help")
    await bot.add_cog(HelpCog(bot))
