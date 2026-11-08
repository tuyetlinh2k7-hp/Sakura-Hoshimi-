import traceback
from config import OWNER_ID
import discord
import Checks_vi.dave_patch  # Kích hoạt bản vá DAVE E2EE 0.2.0 cho discord.py 2.7.1
from discord.ext import commands
from Checks_vi.prefix_handler import get_prefix, load_prefixes
from Checks_vi.server_member import update_stats
from discord.ext import tasks
from config import TOKEN
from file1 import EXTENSIONS
from file2 import EXTENSION_LOGS
from file3 import EXTENSION_ANTIS
import asyncio, json, os, sys

from Database.database import Database
from data.database import init_db
from Checks_vi.owner_notifier import install_live_console_tee, notify_owner_bot_online, notify_owner_bot_error

# Kích hoạt Live Console Stream để chuyển tiếp toàn bộ terminal sang Web Dashboard
install_live_console_tee()

# --- Lớp màu cho Terminal ---
class Colors:
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

load_prefixes()

intents = discord.Intents.default()
intents.message_content = True
intents.members = True

bot = commands.Bot(
    command_prefix=get_prefix,
    intents=intents
)

bot.db = Database()

@bot.check
async def _server_config_check(ctx):
    # Admin-Only Mode per-guild (Cài đặt chung) — giữ tương thích, chỉ chặn khi bật
    try:
        if ctx.guild:
            from Checks_vi.server_config import is_admin_only
            if is_admin_only(ctx.guild.id):
                # chỉ cho Administrator
                if ctx.author.guild_permissions.administrator or ctx.author.id == OWNER_ID:
                    return True
                # lặng lẽ chặn, báo nhẹ nếu là prefix command
                if ctx.command and not ctx.interaction:
                    try: await ctx.send("🔒 Server đang ở Admin-Only Mode — chỉ Administrator được dùng lệnh.", ephemeral=True)
                    except: pass
                return False
    except Exception:
        pass
    return True

@bot.event
async def setup_hook():
    """Hàm này được gọi một lần khi bot khởi động để nạp các extension. 
    Hệ thống ngôn ngữ giờ là per-guild (vi/en) và tự động theo Discord locale nếu chưa set."""

    try:
        await bot.db.init_db()
        print(f"{Colors.GREEN}✅ Database Auto-Role đã sẵn sàng.{Colors.ENDC}")
    except Exception as e:
        print(f"{Colors.FAIL}❌ Lỗi khởi tạo Database: {e}{Colors.ENDC}")
        
    print(f"{Colors.CYAN}--- Đang nạp extensions (đa ngôn ngữ per-guild vi/en) ---{Colors.ENDC}")
    print(f"{Colors.CYAN}--- Loading extensions (per-guild i18n vi/en) ---{Colors.ENDC}")

    async def load_extensions(extensions, ext_type):
        """Hàm helper để nạp một danh sách các extension."""
        loaded = 0
        for ext in extensions:
            try:
                await bot.load_extension(f"{ext_type}.{ext}")
                loaded += 1
            except Exception as e:
                print(f"{Colors.FAIL}❌ Lỗi nạp {ext_type}.{ext}: {e}{Colors.ENDC}")
                import traceback; traceback.print_exc()
        print(f"{Colors.GREEN}✅ Đã nạp {loaded}/{len(extensions)} extensions loại '{ext_type}'.{Colors.ENDC}")

    # Khởi động Sakura Web Dashboard tích hợp với bot
    try:
        from web.server import start_web_dashboard
        import config
        web_port = getattr(config, "WEB_PORT",10272)
        bot.web_runner, bot.web_port = await start_web_dashboard(bot, host="0.0.0.0", port=web_port)
    except Exception as e:
        print(f"{Colors.WARNING}⚠️ Không thể khởi động Web Dashboard: {e}{Colors.ENDC}")

    # Khởi động API để plugin Minecraft gửi mã xác thực liên kết
    try:
        from mc_link_system import start_link_server
        bot.link_server_runner = await start_link_server("127.0.0.1", 5001)
        print(f"{Colors.GREEN}✅ API liên kết Minecraft đã sẵn sàng trên cổng 5001.{Colors.ENDC}")
    except Exception as e:
        print(f"{Colors.WARNING}⚠️ Không thể khởi động API liên kết Minecraft: {e}{Colors.ENDC}")

    await load_extensions(EXTENSIONS, "Command_vi")
    await load_extensions(EXTENSION_LOGS, "Logs_vi")
    await load_extensions(EXTENSION_ANTIS, "Anti")

    try:
        await init_db()
        print(f"{Colors.GREEN}✅ Database đã sẵn sàng.{Colors.ENDC}")
    except Exception as e:
        print(f"{Colors.FAIL}❌ Lỗi khởi tạo Database: {e}{Colors.ENDC}")
        import traceback; traceback.print_exc()

    # Bắt lỗi toàn cục cho Slash Commands và gửi DM cho Owner
    async def _global_app_command_error(interaction: discord.Interaction, error: discord.app_commands.AppCommandError):
        orig = getattr(error, 'original', error)
        if isinstance(orig, (discord.app_commands.CommandOnCooldown, discord.app_commands.CheckFailure)):
            return

        if isinstance(orig, discord.Forbidden):
            try:
                msg = "❌ Bot không có đủ quyền truy cập hoặc thực thi trong kênh này (403 Forbidden / Missing Access)."
                if not interaction.response.is_done():
                    await interaction.response.send_message(msg, ephemeral=True)
                else:
                    await interaction.followup.send(msg, ephemeral=True)
            except Exception:
                pass
            return

        if type(orig).__name__ in ("ChannelTimeoutException", "TimeoutError") or isinstance(orig, TimeoutError):
            try:
                msg = "⏱️ Quá thời gian kết nối tới kênh thoại (Voice Timeout). Vui lòng thử lại sau giây lát!"
                if not interaction.response.is_done():
                    await interaction.response.send_message(msg, ephemeral=True)
                else:
                    await interaction.followup.send(msg, ephemeral=True)
            except Exception:
                pass
            return

        print(f"❌ Lỗi Slash Command /{interaction.command.name if interaction.command else '?'}: {orig}", file=sys.stderr)
        try:
            await notify_owner_bot_error(bot, error=orig, source=f"Slash Command: /{interaction.command.name if interaction.command else 'unknown'}", interaction=interaction)
        except Exception:
            pass

    bot.tree.on_error = _global_app_command_error

# --- Lệnh setlang per-guild (đã sửa lại) ---
@bot.hybrid_command(name="setlang", description="Change bot language for this server (vi/en) / Đổi ngôn ngữ bot cho server này")
@discord.app_commands.describe(lang="Language / Ngôn ngữ: vi or en")
async def setlang(ctx: commands.Context, lang: str):
    """Đổi ngôn ngữ per-guild. Mặc định tự động theo Discord server language nếu chưa set."""
    from Checks_vi.i18n import set_guild_language, get_guild_language, t
    # Kiểm tra quyền: cần Manage Server hoặc là Owner bot
    from config import OWNER_ID
    is_owner = ctx.author.id == OWNER_ID
    has_perm = False
    if ctx.guild:
        has_perm = ctx.author.guild_permissions.manage_guild or is_owner
    else:
        has_perm = is_owner

    if not has_perm:
        # Dùng i18n để trả về đúng ngôn ngữ hiện tại
        msg = t(ctx, "LANG_NEED_ADMIN")
        return await ctx.send(msg, ephemeral=True)

    lang = lang.lower().strip()
    if lang not in ['vi', 'en']:
        msg = t(ctx, "LANG_SET_INVALID")
        # Gợi ý thêm
        help_msg = t(ctx, "LANG_HELP", prefix=ctx.prefix if hasattr(ctx, 'prefix') else 's!')
        return await ctx.send(f"{msg}\n{help_msg}", ephemeral=True)

    if ctx.guild is None:
        return await ctx.send("❌ Lệnh này chỉ dùng trong server.", ephemeral=True)

    set_guild_language(ctx.guild.id, lang)
    lang_name = "Tiếng Việt" if lang == "vi" else "English"
    # Lấy chuỗi đã dịch sau khi set
    title = t(ctx.guild, "LANG_SET_SUCCESS", lang=lang.upper())
    desc = t(ctx.guild, "LANG_SET_SUCCESS_DESC", lang_name=lang_name)
    embed = discord.Embed(title=title, description=desc, color=discord.Color.green())
    # Thêm hint autodetect
    embed.set_footer(text=t(ctx.guild, "SETLANG_AUTODETECT"))
    await ctx.send(embed=embed)

@bot.hybrid_command(name="lang", description="View current server language / Xem ngôn ngữ hiện tại")
async def lang_info(ctx: commands.Context):
    from Checks_vi.i18n import get_guild_language, t
    if ctx.guild is None:
        return await ctx.send("DM default: vi", ephemeral=True)
    cur = get_guild_language(ctx.guild)
    lang_name = "Tiếng Việt" if cur == "vi" else "English"
    msg = t(ctx.guild, "LANG_CURRENT", lang=cur.upper(), lang_name=lang_name)
    await ctx.send(msg, ephemeral=True)

@tasks.loop(seconds=300)
async def update_stats_loop():
    for guild in bot.guilds:
        await update_stats(guild)

# READY

@bot.event
async def on_ready():

    # --- Giao diện khởi động ASCII ART ---
    sakura_art = f"""
{Colors.HEADER}
    ███████╗ █████╗ ██╗  ██╗██╗   ██╗██████╗  █████╗ 
    ██╔════╝██╔══██╗██║ ██╔╝██║   ██║██╔══██╗██╔══██╗
    ███████╗███████║█████╔╝ ██║   ██║██████╔╝███████║
    ╚════██║██╔══██║██╔═██╗ ██║   ██║██╔══██╗██╔══██║
    ███████║██║  ██║██║  ██╗╚██████╔╝██║  ██║██║  ██║
    ╚══════╝╚═╝  ╚═╝╚═╝  ╚═╝ ╚═════╝ ╚═╝  ╚═╝╚═╝  ╚═╝
    {Colors.ENDC}
    """
    print(sakura_art)
    print(f"\n{Colors.CYAN}{'='*50}{Colors.ENDC}")
    print(f"{Colors.HEADER}{Colors.BOLD}🌸 SAKURA BOT ĐÃ SẴN SÀNG PHỤC VỤ! 🌸{Colors.ENDC}")
    print(f"{Colors.CYAN}{'-'*50}{Colors.ENDC}")
    print(f"{Colors.BLUE}   - Tên Bot:    {Colors.BOLD}{bot.user}{Colors.ENDC}")
    print(f"{Colors.BLUE}   - ID Bot:     {Colors.BOLD}{bot.user.id}{Colors.ENDC}")
    print(f"{Colors.BLUE}   - Prefix:     {Colors.BOLD}s!{Colors.ENDC}")
    print(f"{Colors.BLUE}   - Owner:      {Colors.BOLD}Đồng Linh{Colors.ENDC}")
    print(f"{Colors.BLUE}   - Phục vụ:    {Colors.BOLD}{len(bot.guilds)} máy chủ{Colors.ENDC}")
    print(f"{Colors.GREEN}   - Web Panel:  {Colors.BOLD}http://localhost:{getattr(bot, 'web_port', 8080)}{Colors.ENDC}")
    print(f"{Colors.CYAN}{'='*50}{Colors.ENDC}\n")

    await bot.tree.sync() # Đồng bộ lệnh slash command toàn cầu
    print(f"{Colors.GREEN}🚀 Lệnh Slash đã được đồng bộ hóa và sẵn sàng sử dụng!{Colors.ENDC}")

    update_stats_loop.start()

    stream = discord.Streaming(
        name="🌸 SakuraBot | s!menu 🌚",
        url="http://www.twitch.tv/truyetlinh2k7"
    )

    await bot.change_presence(
        status=discord.Status.dnd,
        activity=stream
    )

    # Gửi thông báo DM tới Owner khi Bot Online thành công
    try:
        await notify_owner_bot_online(bot)
    except Exception as e_on:
        print(f"⚠️ Lỗi gửi DM Bot Online tới Owner: {e_on}")

@bot.event
async def on_error(event_method, *args, **kwargs):
    """Bắt các lỗi sự kiện discord cấp thấp và gửi thông báo trực tiếp đến Owner."""
    err = sys.exc_info()[1]
    if err:
        print(f"❌ Ngoại lệ trong sự kiện {event_method}: {err}", file=sys.stderr)
        traceback.print_exc()
        try:
            await notify_owner_bot_error(bot, error=err, source=f"Sự Kiện: {event_method}")
        except Exception:
            pass

bot.run(TOKEN)