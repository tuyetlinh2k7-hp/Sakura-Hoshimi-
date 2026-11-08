import discord
from discord.ext import commands
from discord import app_commands

from Checks_vi.mod import has_admin_role
from Checks_vi.prefix_handler import prefixes, save_prefixes, DEFAULT_PREFIX
from Checks_vi.i18n import t

class PrefixCog(commands.Cog):
    """Cog để quản lý prefix của bot cho từng server - bilingual"""

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.hybrid_command(name="setprefix", description="Change bot prefix for this server / Đổi tiền tố lệnh")
    @app_commands.describe(new_prefix="New prefix (e.g. '.', 's!', '?') or 'reset' / Tiền tố mới hoặc 'reset'")
    @has_admin_role()
    async def setprefix(self, ctx: commands.Context, *, new_prefix: str):
        if not new_prefix:
            return await ctx.send(t(ctx.guild, "PREFIX_NEED_NEW"), ephemeral=True)
        if len(new_prefix) > 5:
            return await ctx.send(t(ctx.guild, "PREFIX_TOO_LONG"), ephemeral=True)
        guild_id = str(ctx.guild.id)
        if new_prefix.lower() == 'reset':
            if guild_id in prefixes:
                del prefixes[guild_id]
            save_prefixes()
            await ctx.send(t(ctx.guild, "PREFIX_RESET", prefix=DEFAULT_PREFIX))
            return
        prefixes[guild_id] = new_prefix
        save_prefixes()
        embed = discord.Embed(
            title=t(ctx.guild, "PREFIX_SUCCESS_TITLE"),
            description=t(ctx.guild, "PREFIX_SUCCESS_DESC", prefix=new_prefix),
            color=discord.Color.green()
        )
        await ctx.send(embed=embed)

async def setup(bot: commands.Bot):
    await bot.add_cog(PrefixCog(bot))
