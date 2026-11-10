"""
Language Cog — per-guild dynamic multi-language system (vi/en/...)
Cung cấp lệnh setlanguage / language / mylang cho từng server
"""
import discord
from discord.ext import commands
from discord import app_commands
from Check.i18n import get_guild_language, set_guild_language, get_supported_languages, get_languages_metadata, t
from Check.mod import has_admin_role
from config import OWNER_ID

class LanguageCog(commands.Cog, name="Language"):
    def __init__(self, bot):
        self.bot = bot

    def _is_admin(self, ctx_or_inter):
        user = ctx_or_inter.author if hasattr(ctx_or_inter, "author") else ctx_or_inter.user
        guild = ctx_or_inter.guild
        if user.id == OWNER_ID:
            return True
        if guild and user.guild_permissions.manage_guild:
            return True
        return False

    @commands.hybrid_group(name="language", aliases=["lang", "ngonngu", "setlanguage"], description="Cài đặt và xem ngôn ngữ máy chủ / Server language settings")
    async def lang_group(self, ctx: commands.Context):
        """Hiển thị danh sách ngôn ngữ khi không chọn lệnh con."""
        if ctx.invoked_subcommand is None:
            await self._handle_set_language(ctx, None)

    @lang_group.command(name="set", description="Change bot language for this server / Đổi ngôn ngữ Bot")
    @app_commands.describe(lang="Mã ngôn ngữ (ví dụ: vi, en, ja, cn...)")
    async def lang_set(self, ctx: commands.Context, lang: str):
        await self._handle_set_language(ctx, lang)

    @lang_group.command(name="current", aliases=["view", "my"], description="Show current server language / Xem ngôn ngữ hiện tại")
    async def lang_current(self, ctx: commands.Context):
        await self._handle_mylang(ctx)

    @commands.command(name="mylang", aliases=["curlang"])
    async def prefix_mylang(self, ctx: commands.Context):
        await self._handle_mylang(ctx)

    async def _handle_set_language(self, ctx: commands.Context, lang: str = None):
        """Đổi ngôn ngữ per-guild. Hỗ trợ vi, en và mở rộng bất kỳ ngôn ngữ nào trong thư mục languages."""
        is_slash = ctx.interaction is not None
        guild = ctx.guild
        if guild is None:
            return await ctx.send(t(guild, "COMMON_ERROR_NO_PERM") + " (DM not supported)", ephemeral=True)

        supported = get_supported_languages()
        meta = get_languages_metadata()

        if not lang:
            current = get_guild_language(guild)
            lines = []
            for code in sorted(supported):
                m = meta.get(code, {})
                flag = m.get("flag", "🌐")
                native = m.get("native", code)
                is_curr = " 👈 *(Hiện tại / Current)*" if code == current else ""
                lines.append(f"• `{code}` — {flag} **{native}**{is_curr}")

            list_str = "\n".join(lines)
            embed = discord.Embed(
                title=t(guild, "LANG_LIST_TITLE", default="🌐 Danh Sách Ngôn Ngữ / Available Languages"),
                description=t(guild, "LANG_LIST_DESC", default=f"Sử dụng `/language set <mã>` để đổi ngôn ngữ:\n\n{list_str}", prefix=ctx.prefix, list=list_str),
                color=discord.Color.from_rgb(255, 182, 193)
            )
            embed.set_footer(text=t(guild, "SETLANG_AUTODETECT", default="Tự động nhận diện theo ngôn ngữ máy chủ Discord nếu chưa cài đặt"))
            return await ctx.send(embed=embed, ephemeral=is_slash)

        if not self._is_admin(ctx):
            return await ctx.send(t(guild, "LANG_NEED_ADMIN", default="❌ Bạn cần quyền **Quản Lý Server (Manage Server)** hoặc là Owner để đổi ngôn ngữ!"), ephemeral=is_slash)

        lang = lang.lower().strip()
        if lang not in supported:
            avail = ", ".join(f"`{c}`" for c in sorted(supported))
            help_msg = t(guild, "LANG_HELP", default="Cú pháp: `/language set <mã>` (Ví dụ: `/language set en`)", prefix=ctx.prefix)
            err_text = f"❌ Ngôn ngữ `{lang}` chưa được hỗ trợ. Các ngôn ngữ khả dụng: {avail}\n{help_msg}"
            return await ctx.send(err_text, ephemeral=is_slash)

        set_guild_language(guild.id, lang)
        m = meta.get(lang, {})
        lang_name = f"{m.get('native', lang.upper())} {m.get('flag', '')}".strip()

        embed = discord.Embed(
            title=t(guild, "LANG_SET_SUCCESS", default="✅ Cài Đặt Ngôn Ngữ Thành Công ({lang})", lang=lang.upper()),
            description=t(guild, "LANG_SET_SUCCESS_DESC", default="Ngôn ngữ của Bot trên máy chủ này đã được chuyển sang: **{lang_name}**.", lang_name=lang_name),
            color=discord.Color.green()
        )
        embed.set_footer(text=t(guild, "SETLANG_AUTODETECT", default="Tự động áp dụng cho các lệnh và thông báo trong server"))
        await ctx.send(embed=embed, ephemeral=is_slash)

    async def _handle_mylang(self, ctx: commands.Context):
        guild = ctx.guild
        is_slash = ctx.interaction is not None
        if guild is None:
            return await ctx.send("DM: vi (default)", ephemeral=is_slash)

        cur = get_guild_language(guild)
        meta = get_languages_metadata().get(cur, {})
        lang_name = f"{meta.get('native', cur.upper())} {meta.get('flag', '')}".strip()

        from Check.i18n import server_language
        is_manual = str(guild.id) in server_language
        extra = ""
        if not is_manual:
            extra = f"\n*({t(guild, 'SETLANG_AUTODETECT', default='Tự động theo ngôn ngữ máy chủ Discord')})*"

        msg = t(guild, "LANG_CURRENT", default="Ngôn ngữ hiện tại của server: **{lang_name}** (`{lang}`)", lang=cur.upper(), lang_name=lang_name) + extra
        await ctx.send(msg, ephemeral=is_slash)

async def setup(bot):
    await bot.add_cog(LanguageCog(bot))
