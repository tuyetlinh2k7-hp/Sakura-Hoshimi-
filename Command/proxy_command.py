import os
import re
import json
import copy
import asyncio
from pathlib import Path
from typing import Literal

import discord
from discord.ext import commands
from discord import app_commands
from openai import AsyncOpenAI

from Check.mod import has_admin_role, is_owner
from Check.i18n import t

# --- CẤU HÌNH XKIRO API ---
API_KEY = None
try:
    from config import XKIRO_API_KEY as API_KEY
except ImportError:
    try:
        from config import GEMINI_API_KEY as API_KEY
    except ImportError:
        API_KEY = os.getenv("XKIRO_API_KEY") or os.getenv("GEMINI_API_KEY")

xkiro_client = AsyncOpenAI(
    api_key=API_KEY or "missing-api-key",
    base_url="https://api.xkiro.com/v1",
)

try:
    from config import AI_MODEL as MODEL_NAME
except ImportError:
    MODEL_NAME = "sensenova/sensenova-6.8-flash-lite"

BASE_DIR = Path(__file__).resolve().parent.parent
PROXY_SETTINGS_FILE = BASE_DIR / "data" / "proxy_settings.json"

proxy_settings: dict = {}
global_proxy_enabled: bool = True

# Danh sách đen: Các lệnh quản trị/nhạy cảm cấm tuyệt đối không cho phép kích hoạt qua Proxy
BLACKLIST_COMMANDS = {
    "proxy", "eval", "reload", "load", "unload", "shutdown", "restart",
    "owner", "menubot", "botping", "sayto", "mod", "moderator", "admin",
    "roleadmin", "set", "ban", "kick", "purge", "clear", "mute", "unmute",
    "timeout", "warn", "unwarn"
}

# Các từ đệm tùy chọn ở đầu câu (nếu người dùng có thói quen gõ "@Bot dùng/lệnh ...", bot sẽ tự cắt bỏ)
OPTIONAL_TRIGGER_PREFIXES = ("lệnh ", "lenh ", "cmd ", "run ", "dùng ", "dung ", "hãy ", "hay ")


def load_proxy_settings():
    """Tải cài đặt proxy từ file JSON."""
    global proxy_settings, global_proxy_enabled
    if PROXY_SETTINGS_FILE.exists():
        try:
            with open(PROXY_SETTINGS_FILE, "r", encoding="utf-8") as f:
                proxy_settings = json.load(f)
        except (json.JSONDecodeError, OSError):
            proxy_settings = {}
    else:
        proxy_settings = {}

    global_proxy_enabled = proxy_settings.get("__global__", {}).get("enabled", True)


def save_proxy_settings():
    """Lưu cài đặt proxy vào file JSON."""
    PROXY_SETTINGS_FILE.parent.mkdir(parents=True, exist_ok=True)
    if "__global__" not in proxy_settings:
        proxy_settings["__global__"] = {}
    proxy_settings["__global__"]["enabled"] = global_proxy_enabled
    with open(PROXY_SETTINGS_FILE, "w", encoding="utf-8") as f:
        json.dump(proxy_settings, f, indent=4, ensure_ascii=False)


class ProxyCommandCog(commands.Cog, name="Proxy Command"):
    """Cog cho phép người dùng tag trực tiếp bot để thực thi lệnh bằng ngôn ngữ tự nhiên."""

    def __init__(self, bot: commands.Bot):
        self.bot = bot
        load_proxy_settings()
        # Cooldown chống spam API: Mỗi người dùng cách nhau tối thiểu 4 giây
        self._cd = commands.CooldownMapping.from_cooldown(1, 4.0, commands.BucketType.user)

    def get_guild_settings(self, guild_id: int) -> dict:
        guild_id_str = str(guild_id)
        if guild_id_str not in proxy_settings:
            proxy_settings[guild_id_str] = {"enabled": True}
        return proxy_settings[guild_id_str]

    def _get_dynamic_command_schema(self) -> str:
        """Tự động tạo danh mục lệnh hợp lệ từ bot (bao gồm cả lệnh con của Group), loại trừ lệnh cấm."""
        available_cmds = []
        for cmd in self.bot.commands:
            if cmd.hidden or cmd.name in BLACKLIST_COMMANDS:
                continue

            desc = cmd.short_doc or (cmd.help.split("\n")[0] if cmd.help else "Thực hiện lệnh này")
            available_cmds.append(f"- `{cmd.name}`: {desc}")

            # Nếu là nhóm lệnh (Group), liệt kê thêm các lệnh con an toàn
            if isinstance(cmd, commands.Group):
                for sub in cmd.commands:
                    if not sub.hidden and sub.name not in BLACKLIST_COMMANDS:
                        sub_desc = sub.short_doc or (sub.help.split("\n")[0] if sub.help else "Lệnh con")
                        available_cmds.append(f"  + `{cmd.name} {sub.name}`: {sub_desc}")

        return "\n".join(available_cmds) if available_cmds else "- Không có lệnh khả dụng"

    async def _call_llm(self, prompt: str, max_retries: int = 3) -> str:
        """Gọi mistralai/mistral-large-4-0 qua xKiro API với cơ chế tự động thử lại khi gặp lỗi 503/429."""
        messages = [
            {
                "role": "system",
                "content": (
                    "Bạn là API trích xuất lệnh Discord, chỉ trả lời bằng cú pháp lệnh duy nhất "
                    "(không có dấu prefix ở đầu, không giải thích) hoặc trả lời UNKNOWN."
                ),
            },
            {"role": "user", "content": prompt},
        ]

        last_error = None
        for attempt in range(max_retries):
            try:
                response = await xkiro_client.chat.completions.create(
                    model=MODEL_NAME,
                    messages=messages,
                    temperature=0.1,
                    max_tokens=60,
                )
                text = (
                    response.choices[0].message.content.strip()
                    if (response.choices and response.choices[0].message.content)
                    else "UNKNOWN"
                )
                return text.replace("`", "").strip()
            except Exception as e:
                last_error = e
                error_str = str(e).lower()
                status_code = getattr(e, "status_code", None)

                is_transient = (
                    status_code in (429, 500, 502, 503, 504)
                    or any(k in error_str for k in ("503", "429", "overloaded", "unavailable", "rate limit"))
                )

                if is_transient and attempt < max_retries - 1:
                    await asyncio.sleep(1.5 * (attempt + 1))
                    continue
                raise e

        if last_error is not None:
            raise last_error
        raise RuntimeError("Không thể gọi LLM sau các lượt thử lại.")

    async def _execute_resolved_command(self, message: discord.Message, command_to_run: str):
        """Kiểm tra an toàn, phân quyền và thực thi lệnh đã được phân giải."""
        if not command_to_run or command_to_run.upper() == "UNKNOWN":
            return

        # 1. Lấy prefix hiện tại của server
        prefix = await self.bot.get_prefix(message)
        if isinstance(prefix, (list, tuple)):
            prefix = prefix[0]

        # Loại bỏ prefix ở đầu nếu AI vô tình thêm vào
        if command_to_run.startswith(prefix):
            command_to_run = command_to_run[len(prefix):].strip()

        if not command_to_run:
            return

        # 2. Chặn tuyệt đối các lệnh nằm trong BLACKLIST_COMMANDS
        parts = command_to_run.split()
        cmd_root_name = parts[0].lower()
        cmd_sub_name = parts[1].lower() if len(parts) > 1 else ""

        if cmd_root_name in BLACKLIST_COMMANDS or cmd_sub_name in BLACKLIST_COMMANDS:
            await message.reply(
                "⚠️ Lệnh quản trị/nhạy cảm này không được phép thực hiện thông qua trợ lý Proxy.",
                mention_author=False,
                delete_after=5
            )
            return

        # 3. Tạo ngữ cảnh (Context) và kiểm tra quyền hạn của người dùng trước khi chạy
        new_message = copy.copy(message)
        new_message.content = f"{prefix}{command_to_run}"

        ctx = await self.bot.get_context(new_message)
        if not ctx.valid or ctx.command is None:
            return

        if ctx.command.name in BLACKLIST_COMMANDS or (ctx.command.root_parent and ctx.command.root_parent.name in BLACKLIST_COMMANDS):
            await message.reply(
                "⚠️ Lệnh này không được phép thực hiện thông qua trợ lý Proxy.",
                mention_author=False,
                delete_after=5
            )
            return

        try:
            # Đảm bảo người dùng có đủ quyền chạy lệnh đó (không cho phép mượn tay AI vượt quyền)
            if await ctx.command.can_run(ctx):
                await self.bot.invoke(ctx)
            else:
                await message.reply(
                    "⛔ Bạn không có đủ quyền hạn để sử dụng lệnh này!",
                    mention_author=False,
                    delete_after=5
                )
        except commands.CheckFailure:
            await message.reply(
                "⛔ Bạn không có đủ quyền hạn để sử dụng lệnh này!",
                mention_author=False,
                delete_after=5
            )
        except Exception as e:
            print(f"[ProxyCommand] Lỗi khi thực thi lệnh '{command_to_run}': {e}")

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if message.author.bot or not message.guild or not self.bot.user:
            return

        # Kiểm tra tag bot ở đầu tin nhắn
        mention_pattern = rf"^<@!?{self.bot.user.id}>\s*"
        match = re.match(mention_pattern, message.content)
        if not match:
            return

        if not global_proxy_enabled:
            return

        guild_config = self.get_guild_settings(message.guild.id)
        if not guild_config.get("enabled", True):
            return

        raw_prompt = message.content[match.end():].strip()
        if not raw_prompt:
            return

        # Cắt bỏ các từ khóa mở đầu tùy chọn ("lệnh ", "cmd ", "dùng "...) nếu người dùng có gõ kèm
        lower_prompt = raw_prompt.lower()
        for kw in OPTIONAL_TRIGGER_PREFIXES:
            if lower_prompt.startswith(kw):
                raw_prompt = raw_prompt[len(kw):].strip()
                lower_prompt = raw_prompt.lower()
                break

        if not raw_prompt:
            return

        # =====================================================================
        # BƯỚC 1: FAST-PATH (NẾU NGƯỜI DÙNG GÕ TRỰC TIẾP TÊN LỆNH HỢP LỆ)
        # Chạy thẳng ngay lập tức mà không cần tốn thời gian gọi AI API
        # =====================================================================
        first_word = lower_prompt.split()[0]
        direct_cmd = self.bot.get_command(first_word)
        if direct_cmd and not direct_cmd.hidden and direct_cmd.name not in BLACKLIST_COMMANDS:
            await self._execute_resolved_command(message, raw_prompt)
            return

        # =====================================================================
        # BƯỚC 2: DÙNG AI ĐỂ DỊCH NGÔN NGỮ TỰ NHIÊN THÀNH LỆNH BOT
        # =====================================================================
        bucket = self._cd.get_bucket(message)
        retry_after = bucket.update_rate_limit()
        if retry_after:
            await message.reply(
                f"⏳ Vui lòng đợi `{retry_after:.1f}s` trước khi yêu cầu lệnh tiếp.",
                mention_author=False,
                delete_after=4
            )
            return

        async with message.channel.typing():
            text_channels = [f"'{ch.name}': <#{ch.id}>" for ch in message.guild.text_channels[:15]]
            channels_info = ", ".join(text_channels)

            # Lọc danh sách người dùng được tag (bỏ qua chính con bot ở đầu câu)
            mentioned_users = [
                f"'{u.display_name}': <@{u.id}>"
                for u in message.mentions
                if not u.bot and u.id != self.bot.user.id
            ]
            users_info = ", ".join(mentioned_users) if mentioned_users else "Không có"

            commands_schema = self._get_dynamic_command_schema()

            prompt_for_ai = (
                "Bạn là bộ thông dịch lệnh cho Discord bot. Chuyển yêu cầu bằng ngôn ngữ tự nhiên của người dùng thành 1 lệnh hợp lệ.\n"
                "Quy tắc tuyệt đối:\n"
                "1. Chỉ trả lời bằng đúng cú pháp lệnh cần chạy (KHÔNG có dấu prefix như ! hay /, không kèm giải thích, không bọc markdown).\n"
                "2. Nếu yêu cầu không khớp với lệnh nào trong danh sách hoặc chỉ là câu trò chuyện thông thường, chỉ trả lời đúng 1 từ: UNKNOWN\n\n"
                "Danh sách các lệnh được phép:\n"
                f"{commands_schema}\n\n"
                f"Kênh tham chiếu: {channels_info}\n"
                f"Người dùng được tag trong câu: {users_info}\n\n"
                f"Yêu cầu của người dùng: '{raw_prompt}'\nLệnh:"
            )

            try:
                command_to_run = await self._call_llm(prompt_for_ai)
            except Exception as e:
                print(f"[ProxyCommand] Lỗi khi gọi model {MODEL_NAME}: {e}")
                command_to_run = "UNKNOWN"

        await self._execute_resolved_command(message, command_to_run)

    # =====================================================================
    # NHÓM LỆNH CẤU HÌNH (/proxy)
    # =====================================================================

    @commands.hybrid_group(name="proxy", fallback="status", description="🤖 Thiết lập tính năng tag bot để ra lệnh bằng ngôn ngữ tự nhiên.")
    @commands.guild_only()
    @has_admin_role()
    async def proxy(self, ctx: commands.Context):
        guild_config = self.get_guild_settings(ctx.guild.id)
        global_status = "🟢 Đang Bật" if global_proxy_enabled else "🔴 Đang Tắt"
        guild_status = "🟢 Đang Bật" if guild_config.get("enabled", True) else "🔴 Đang Tắt"
        bot_name = self.bot.user.display_name if self.bot.user else "Bot"

        embed = discord.Embed(
            title=t(ctx.guild, "PROXY_PANEL_TITLE"),
            description=t(ctx.guild, "PROXY_PANEL_DESC"),
            color=discord.Color.blue(),
            timestamp=discord.utils.utcnow()
        )
        embed.add_field(name="🌐 Trạng thái Toàn cục", value=global_status, inline=True)
        embed.add_field(name="🏠 Trạng thái Server này", value=guild_status, inline=True)
        embed.add_field(
            name="💡 Cách sử dụng",
            value=(
                f"Chỉ cần tag trực tiếp Bot kèm yêu cầu của bạn:\n"
                f"• `@{bot_name} kiểm tra ping`\n"
                f"• `@{bot_name} xem ảnh đại diện của @user`\n"
                f"• `@{bot_name} tạo mã qr xin chào`"
            ),
            inline=False
        )
        embed.set_footer(text=f"Model: {MODEL_NAME} • Dùng {ctx.prefix}proxy <toggle/global> để cấu hình.")
        await ctx.send(embed=embed, ephemeral=True)

    @proxy.command(name="global", description="🌐 [Owner] Bật/tắt tính năng Proxy trên toàn bộ hệ thống Bot.")
    @app_commands.describe(status="Chọn 'on' để bật hoặc 'off' để tắt toàn cục")
    @is_owner()
    async def proxy_global(self, ctx: commands.Context, status: Literal["on", "off"]):
        global global_proxy_enabled
        global_proxy_enabled = (status.lower() == "on")
        save_proxy_settings()
        state_str = "🟢 **BẬT**" if global_proxy_enabled else "🔴 **TẮT**"
        await ctx.send(f"✅ [Toàn Cục] Tính năng Proxy Command đã được chuyển sang: {state_str}.", ephemeral=True)

    @proxy.command(name="toggle", description="⚙️ Bật/tắt tính năng Proxy cho máy chủ hiện tại.")
    @app_commands.describe(status="Chọn 'on' để bật hoặc 'off' để tắt")
    @has_admin_role()
    async def proxy_toggle(self, ctx: commands.Context, status: Literal["on", "off"]):
        guild_config = self.get_guild_settings(ctx.guild.id)
        is_on = (status.lower() == "on")
        guild_config["enabled"] = is_on
        save_proxy_settings()
        state_str = "🟢 **BẬT**" if is_on else "🔴 **TẮT**"
        await ctx.send(f"✅ Tính năng Proxy Command cho máy chủ này đã được chuyển sang: {state_str}.", ephemeral=True)


async def setup(bot: commands.Bot):
    await bot.add_cog(ProxyCommandCog(bot))
