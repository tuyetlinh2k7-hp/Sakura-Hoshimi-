import discord
from discord.ext import commands
import traceback
import sys
import difflib
from Check.i18n import t

class CommandError(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_command_error(self, ctx, error):
        if hasattr(ctx.command, 'on_error'):
            return

        error = getattr(error, 'original', error)

        if isinstance(error, commands.NotOwner):
            return

        guild = getattr(ctx, 'guild', None)

        if isinstance(error, commands.CommandNotFound):
            invoked_command = ctx.invoked_with
            all_command_names = [cmd.name for cmd in self.bot.commands if not cmd.hidden]
            for cmd in self.bot.commands:
                if not cmd.hidden:
                    all_command_names.extend(cmd.aliases)

            suggestions = difflib.get_close_matches(invoked_command, all_command_names, n=3, cutoff=0.6)
            
            description = t(guild, "LOG_CMDERROR_NOTFOUND_DESC", command=invoked_command)
            if suggestions:
                suggestions_text = "\n".join([f"• `{ctx.prefix}{s}`" for s in suggestions])
                description += t(guild, "LOG_CMDERROR_NOTFOUND_SUGGEST", suggestions=suggestions_text)
            
            embed = discord.Embed(
                title=t(guild, "LOG_CMDERROR_NOTFOUND_TITLE"),
                description=description,
                color=discord.Color.orange()
            )
            await ctx.send(embed=embed, delete_after=10)

        elif isinstance(error, commands.MissingPermissions):
            missing_perms = ', '.join(f"`{perm.replace('_', ' ').title()}`" for perm in error.missing_permissions)
            embed = discord.Embed(
                title=t(guild, "LOG_CMDERROR_MISSINGPERM_TITLE"),
                description=t(guild, "LOG_CMDERROR_MISSINGPERM_DESC", perms=missing_perms),
                color=discord.Color.red()
            )
            await ctx.send(embed=embed)

        elif isinstance(error, commands.BotMissingPermissions):
            missing_perms = ', '.join(f"`{perm.replace('_', ' ').title()}`" for perm in error.missing_permissions)
            embed = discord.Embed(
                title=t(guild, "LOG_CMDERROR_BOTMISSINGPERM_TITLE"),
                description=t(guild, "LOG_CMDERROR_BOTMISSINGPERM_DESC", perms=missing_perms),
                color=discord.Color.orange()
            )
            await ctx.send(embed=embed)

        elif isinstance(error, commands.MissingRequiredArgument):
            embed = discord.Embed(
                title=t(guild, "LOG_CMDERROR_MISSINGARG_TITLE"),
                description=t(guild, "LOG_CMDERROR_MISSINGARG_DESC", param=error.param.name, prefix=ctx.prefix, command=ctx.command.qualified_name, signature=ctx.command.signature),
                color=discord.Color.orange()
            )
            await ctx.send(embed=embed)

        elif isinstance(error, commands.CommandOnCooldown):
            embed = discord.Embed(
                title=t(guild, "LOG_CMDERROR_COOLDOWN_TITLE"),
                description=t(guild, "LOG_CMDERROR_COOLDOWN_DESC", seconds=f"{error.retry_after:.1f}"),
                color=discord.Color.blue()
            )
            await ctx.send(embed=embed, delete_after=5)

        elif isinstance(error, commands.BadArgument):
            embed = discord.Embed(
                title=t(guild, "LOG_CMDERROR_BADARG_TITLE"),
                description=t(guild, "LOG_CMDERROR_BADARG_DESC"),
                color=discord.Color.orange()
            )
            await ctx.send(embed=embed)

        elif isinstance(error, commands.CheckFailure):
            pass

        elif isinstance(error, discord.Forbidden):
            embed = discord.Embed(
                title="🚫 Lỗi Quyền Truy Cập (403 Forbidden)",
                description="Bot không có đủ quyền thực hiện thao tác này trong kênh hoặc server (Missing Access).",
                color=discord.Color.red()
            )
            try:
                await ctx.send(embed=embed, ephemeral=True)
            except Exception:
                pass
            return

        elif type(error).__name__ in ("ChannelTimeoutException", "TimeoutError") or isinstance(error, TimeoutError):
            embed = discord.Embed(
                title="⏱️ Quá Thời Gian Chờ (Timeout)",
                description="Thao tác kết nối kênh thoại đã bị quá thời gian chờ (Timeout). Vui lòng thử lại sau!",
                color=discord.Color.red()
            )
            try:
                await ctx.send(embed=embed, ephemeral=True)
            except Exception:
                pass
            return

        else:
            print(f'Bỏ qua lỗi trong lệnh {ctx.command}:', file=sys.stderr)
            traceback.print_exception(type(error), error, error.__traceback__, file=sys.stderr)

            try:
                from Check.owner_notifier import notify_owner_bot_error
                await notify_owner_bot_error(self.bot, error=error, source=f"Lệnh: {ctx.command}", ctx=ctx)
            except Exception as e_notify:
                print(f"[CommandError] Lỗi khi gửi DM cho Owner: {e_notify}", file=sys.stderr)

            embed = discord.Embed(
                title=t(guild, "LOG_CMDERROR_UNKNOWN_TITLE"),
                description=t(guild, "LOG_CMDERROR_UNKNOWN_DESC"),
                color=discord.Color.dark_red()
            )
            await ctx.send(embed=embed)

async def setup(bot: commands.Bot):
    await bot.add_cog(CommandError(bot))
