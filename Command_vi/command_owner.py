import os

import sys

import time

import psutil

import asyncio

import subprocess

from pathlib import Path

from datetime import datetime

from typing import Optional, Literal



import discord

from discord.ext import commands

from discord import app_commands



from config import OWNER_ID

from Checks_vi.mod import is_owner, admin_roles, save_admin_roles

from Checks_vi.data import save_data

from Checks_vi.i18n import t



BASE_DIR = Path(__file__).resolve().parent.parent





class PowerConfirmView(discord.ui.View):

    def __init__(self, author: discord.abc.User, bot: commands.Bot, action: Literal["shutdown", "restart"]):

        super().__init__(timeout=30)

        self.author = author

        self.bot = bot

        self.action = action



    async def interaction_check(self, interaction: discord.Interaction) -> bool:

        if interaction.user.id != self.author.id and interaction.user.id != OWNER_ID:

            await interaction.response.send_message("⛔ Chỉ Chủ sở hữu Bot mới có quyền thực hiện thao tác này!", ephemeral=True)

            return False

        return True



    @discord.ui.button(label="Xác nhận thực hiện", style=discord.ButtonStyle.danger, emoji="✅")

    async def confirm_btn(self, interaction: discord.Interaction, button: discord.ui.Button):

        try:

            save_data()

            save_admin_roles()

        except Exception:

            pass



        if self.action == "shutdown":

            embed = discord.Embed(

                title="🔴 Đang tắt Bot (Shutdown)...",

                description=t(interaction.guild, "OWNER_SHUTDOWN_DONE"),

                color=discord.Color.red()

            )

            await interaction.response.edit_message(content=None, embed=embed, view=None)

            try:

                from Checks_vi.owner_notifier import notify_owner_bot_lifecycle

                await notify_owner_bot_lifecycle(self.bot, action="shutdown", source=f"Lệnh: {interaction.user}")

            except Exception:

                pass

            await self.bot.close()

        else:

            embed = discord.Embed(

                title=t(interaction.guild, "OWNER_RESTART_TITLE"),

                description=t(interaction.guild, "OWNER_RESTART_DESC"),

                color=discord.Color.orange()

            )

            await interaction.response.edit_message(content=None, embed=embed, view=None)

            try:

                from Checks_vi.owner_notifier import notify_owner_bot_lifecycle

                await notify_owner_bot_lifecycle(self.bot, action="restart", source=f"Lệnh: {interaction.user}")

            except Exception:

                pass

            os.execv(sys.executable, [sys.executable] + sys.argv)



    @discord.ui.button(label="Hủy thao tác", style=discord.ButtonStyle.secondary, emoji="✖️")

    async def cancel_btn(self, interaction: discord.Interaction, button: discord.ui.Button):

        await interaction.response.edit_message(

            content=t(interaction.guild, "OWNER_SHUTDOWN_CANCEL"),

            embed=None,

            view=None

        )





class GuildsPaginatorView(discord.ui.View):

    def __init__(self, author: discord.abc.User, guilds: list[discord.Guild], per_page: int = 10):

        super().__init__(timeout=120)

        self.author = author

        self.guilds = sorted(guilds, key=lambda g: g.member_count or 0, reverse=True)

        self.per_page = per_page

        self.current_page = 0

        self.total_pages = max(1, (len(self.guilds) - 1) // self.per_page + 1)

        self.update_buttons()



    def build_embed(self, ctx_guild: Optional[discord.Guild]) -> discord.Embed:

        embed = discord.Embed(

            title=t(ctx_guild, "OWNER_GUILDS_TITLE", count=len(self.guilds)),

            color=discord.Color.blue(),

            timestamp=discord.utils.utcnow()

        )

        start = self.current_page * self.per_page

        page_items = self.guilds[start : start + self.per_page]



        lines = []

        for idx, g in enumerate(page_items, start=start + 1):

            owner_str = f"<@{g.owner_id}>" if g.owner_id else "Không rõ"

            lines.append(

                f"**{idx}. {g.name}**\n"

                f"└ 🆔 ID: `{g.id}` • 👥 Thành viên: `{g.member_count}` • 👑 Owner: {owner_str}"

            )



        embed.description = "\n\n".join(lines) if lines else t(ctx_guild, "OWNER_SERVERS_EMPTY")

        embed.set_footer(text=f"Trang {self.current_page + 1}/{self.total_pages} • Tổng cộng {len(self.guilds)} máy chủ")

        return embed



    def update_buttons(self):

        self.prev_btn.disabled = self.current_page <= 0

        self.next_btn.disabled = self.current_page >= self.total_pages - 1



    async def interaction_check(self, interaction: discord.Interaction) -> bool:

        if interaction.user.id != self.author.id and interaction.user.id != OWNER_ID:

            await interaction.response.send_message("⛔ Bạn không thể điều khiển bảng này!", ephemeral=True)

            return False

        return True



    @discord.ui.button(label="◀ Trang trước", style=discord.ButtonStyle.secondary)

    async def prev_btn(self, interaction: discord.Interaction, button: discord.ui.Button):

        self.current_page -= 1

        self.update_buttons()

        await interaction.response.edit_message(embed=self.build_embed(interaction.guild), view=self)



    @discord.ui.button(label="Trang sau ▶", style=discord.ButtonStyle.primary)

    async def next_btn(self, interaction: discord.Interaction, button: discord.ui.Button):

        self.current_page += 1

        self.update_buttons()

        await interaction.response.edit_message(embed=self.build_embed(interaction.guild), view=self)





class OwnerManager(commands.Cog):

    def __init__(self, bot: commands.Bot):

        self.bot = bot

        self.start_time = time.time()



    def _sanitize_bot_file(self, bot_file: str) -> str:

        clean_name = os.path.basename(bot_file.strip())

        if not clean_name.endswith(".py"):

            clean_name += ".py"

        return clean_name



    def _find_process(self, bot_file: str) -> Optional[psutil.Process]:

        clean_name = self._sanitize_bot_file(bot_file)

        for proc in psutil.process_iter(["pid", "cmdline"]):

            try:

                cmdline = proc.info.get("cmdline")

                if cmdline and clean_name in " ".join(cmdline):

                    return proc

            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):

                pass

        return None



    async def _owner_action_autocomplete(self, interaction: discord.Interaction, current: str):

        actions = [

            ("Xem hướng dẫn và menu (panel)", "panel"),

            ("Thông số bot và tài nguyên (botinfo)", "botinfo"),

            ("Tải lại module không tắt bot (reload)", "reload"),

            ("Nạp module mới (load)", "load"),

            ("Gỡ module đang chạy (unload)", "unload"),

            ("Đồng bộ lệnh Slash (sync)", "sync"),

            ("Danh sách server tham gia (servers)", "servers"),

            ("Gửi tin nhắn qua bot (say)", "say"),

            ("Thêm role admin bot server (addadmin)", "addadmin"),

            ("Xóa role admin bot server (rmadmin)", "rmadmin"),

            ("Xem danh sách role admin (listadmin)", "listadmin"),

            ("Tra cứu ID role (findrole)", "findrole"),

            ("Khởi động lại bot (restart)", "restart"),

            ("Tắt bot an toàn (shutdown)", "shutdown"),

        ]

        return [

            app_commands.Choice(name=name, value=val)

            for name, val in actions if current.lower() in name.lower() or current.lower() in val.lower()

        ][:25]



    async def _owner_target_autocomplete(self, interaction: discord.Interaction, current: str):

        action = getattr(interaction.namespace, "action", "")

        if action in ("reload", "load", "unload"):

            exts = list(self.bot.extensions.keys())

            return [

                app_commands.Choice(name=ext, value=ext)

                for ext in exts if current.lower() in ext.lower()

            ][:25]

        if action in ("addadmin", "rmadmin", "findrole"):

            guilds = [f"{g.name} ({g.id})" for g in self.bot.guilds]

            return [

                app_commands.Choice(name=g, value=g.split("(")[-1].replace(")", "").strip())

                for g in guilds if current.lower() in g.lower()

            ][:25]

        return []



    async def _menubot_action_autocomplete(self, interaction: discord.Interaction, current: str):

        actions = [

            ("Bảng điều khiển (panel)", "panel"),

            ("Kiểm tra tất cả file bot (check)", "check"),

            ("Xem thông tin tiến trình (info)", "info"),

            ("Xem kết nối mạng (net)", "net"),

            ("Khởi chạy file bot (start)", "start"),

            ("Dừng tiến trình file (stop)", "stop"),

            ("Khởi động lại file bot (restart)", "restart"),

        ]

        return [

            app_commands.Choice(name=name, value=val)

            for name, val in actions if current.lower() in name.lower() or current.lower() in val.lower()

        ][:25]



    async def _menubot_file_autocomplete(self, interaction: discord.Interaction, current: str):

        py_files = [f for f in os.listdir(BASE_DIR) if f.endswith(".py")]

        return [

            app_commands.Choice(name=f, value=f)

            for f in py_files if current.lower() in f.lower()

        ][:25]



    async def _execute_botinfo(self, ctx: commands.Context):

        guilds_count = len(self.bot.guilds)

        users_count = sum(g.member_count or 0 for g in self.bot.guilds)

        latency = round(self.bot.latency * 1000)



        cpu = await asyncio.to_thread(psutil.cpu_percent, 0.3)

        ram = psutil.virtual_memory()

        ram_used = round(ram.used / (1024 ** 3), 2)

        ram_total = round(ram.total / (1024 ** 3), 2)



        proc = psutil.Process(os.getpid())

        bot_ram_mb = round(proc.memory_info().rss / (1024 ** 2), 2)

        uptime_sec = int(time.time() - proc.create_time())

        hours, rem = divmod(uptime_sec, 3600)

        minutes, seconds = divmod(rem, 60)



        embed = discord.Embed(

            title=t(ctx.guild, "OWNER_BOTINFO_TITLE"),

            color=discord.Color.from_rgb(255, 182, 193),

            timestamp=discord.utils.utcnow()

        )

        if self.bot.user:

            embed.set_thumbnail(url=self.bot.user.display_avatar.url)



        embed.add_field(name=t(ctx.guild, "OWNER_BOTINFO_FIELD_SERVERS"), value=f"`{guilds_count}`", inline=True)

        embed.add_field(name=t(ctx.guild, "OWNER_BOTINFO_FIELD_USERS"), value=f"`{users_count:,}`", inline=True)

        embed.add_field(name=t(ctx.guild, "OWNER_BOTINFO_FIELD_LATENCY"), value=f"`{latency} ms`", inline=True)

        embed.add_field(name=t(ctx.guild, "OWNER_BOTINFO_FIELD_CPU"), value=f"`{cpu}%`", inline=True)

        embed.add_field(name=t(ctx.guild, "OWNER_BOTINFO_FIELD_RAM"), value=f"`{ram_used} / {ram_total} GB` (Bot: `{bot_ram_mb} MB`)", inline=True)

        embed.add_field(name="🕒 Uptime", value=f"`{hours}h {minutes}m {seconds}s`", inline=True)

        embed.set_footer(

            text=t(ctx.guild, "OWNER_BOTINFO_FOOTER", name=ctx.author.display_name),

            icon_url=ctx.author.display_avatar.url

        )

        await ctx.send(embed=embed)



    async def _execute_sayto(self, ctx: commands.Context, channel_id: str, text: str):

        try:

            cid = int(channel_id.strip().replace("<#", "").replace(">", ""))

            channel = self.bot.get_channel(cid) or await self.bot.fetch_channel(cid)

            if not channel or not isinstance(channel, (discord.TextChannel, discord.VoiceChannel, discord.Thread)):

                return await ctx.send("❌ Không tìm thấy kênh văn bản hợp lệ với ID này!", ephemeral=True)



            await channel.send(text)



            embed = discord.Embed(

                title="✅ Đã gửi tin nhắn thành công",

                description=(

                    f"📁 **Máy chủ:** `{channel.guild.name}`\n"

                    f"📢 **Kênh nhận:** {channel.mention}\n\n"

                    f"💬 **Nội dung:**\n{text}"

                ),

                color=discord.Color.green()

            )

            embed.set_footer(text=f"Thực hiện bởi: {ctx.author}")

            await ctx.send(embed=embed, ephemeral=True)

        except discord.Forbidden:

            await ctx.send(t(ctx.guild, "OWNER_SAY_FORBIDDEN", channel=f"`{channel_id}`"), ephemeral=True)

        except Exception as e:

            await ctx.send(t(ctx.guild, "OWNER_SAY_ERROR", error=e), ephemeral=True)



    @commands.hybrid_command(

        name="owner",

        description="👑 Bảng điều khiển quản trị hệ thống dành riêng cho Chủ sở hữu Bot."

    )

    @app_commands.describe(

        action="Chọn hành động cần thực hiện",

        target="Tên Cog, ID Server, ID Kênh hoặc tham số chính",

        extra="Tham số phụ (ID Role, nội dung tin nhắn, hoặc tên Role)"

    )

    @app_commands.autocomplete(action=_owner_action_autocomplete, target=_owner_target_autocomplete)

    @is_owner()

    async def owner(

        self,

        ctx: commands.Context,

        action: Literal[

            "panel", "reload", "load", "unload", "sync",

            "servers", "addadmin", "rmadmin", "listadmin",

            "say", "botinfo", "restart", "shutdown", "findrole"

        ] = "panel",

        target: Optional[str] = None,

        *,

        extra: Optional[str] = None

    ):

        act = action.lower()



        if act == "panel":

            prefix = ctx.prefix

            embed = discord.Embed(

                title=t(ctx.guild, "OWNER_PANEL_TITLE"),

                description=t(ctx.guild, "OWNER_PANEL_DESC"),

                color=discord.Color.gold(),

                timestamp=discord.utils.utcnow()

            )

            embed.add_field(

                name="🔄 Quản lý Module / Cog",

                value=(

                    f"• `{prefix}owner reload <tên_extension>`\n"

                    f"• `{prefix}owner load <tên_extension>`\n"

                    f"• `{prefix}owner unload <tên_extension>`\n"

                    f"• `{prefix}owner sync`"

                ),

                inline=False

            )

            embed.add_field(

                name=t(ctx.guild, "OWNER_PANEL_FIELD_ADMIN"),

                value=(

                    f"• `{prefix}owner addadmin <server_id> <role_id>`\n"

                    f"• `{prefix}owner rmadmin <server_id> <role_id>`\n"

                    f"• `{prefix}owner listadmin`"

                ),

                inline=False

            )

            embed.add_field(

                name="🌐 Hệ thống & Máy chủ",

                value=(

                    f"• `{prefix}owner botinfo`\n"

                    f"• `{prefix}owner servers`\n"

                    f"• `{prefix}owner say <channel_id> <text>`\n"

                    f"• `{prefix}owner restart` | `{prefix}owner shutdown`"

                ),

                inline=False

            )

            return await ctx.send(embed=embed, ephemeral=True)



        if act == "botinfo":

            if ctx.interaction:

                await ctx.defer()

            return await self._execute_botinfo(ctx)



        if act == "reload":

            if not target:

                return await ctx.send("⚠️ Vui lòng nhập tên extension cần tải lại!", ephemeral=True)

            try:

                await self.bot.reload_extension(target)

                await ctx.send(f"✅ Đã tải lại thành công module `{target}`!", ephemeral=True)

            except Exception as e:

                await ctx.send(f"❌ Lỗi khi reload `{target}`:\n```py\n{e}\n```", ephemeral=True)

            return



        if act == "load":

            if not target:

                return await ctx.send("⚠️ Vui lòng nhập tên extension cần nạp!", ephemeral=True)

            try:

                await self.bot.load_extension(target)

                await ctx.send(f"✅ Đã nạp thành công module `{target}`!", ephemeral=True)

            except Exception as e:

                await ctx.send(f"❌ Lỗi khi load `{target}`:\n```py\n{e}\n```", ephemeral=True)

            return



        if act == "unload":

            if not target:

                return await ctx.send("⚠️ Vui lòng nhập tên extension cần gỡ!", ephemeral=True)

            try:

                await self.bot.unload_extension(target)

                await ctx.send(f"✅ Đã gỡ thành công module `{target}`!", ephemeral=True)

            except Exception as e:

                await ctx.send(f"❌ Lỗi khi unload `{target}`:\n```py\n{e}\n```", ephemeral=True)

            return



        if act == "sync":

            if ctx.interaction:

                await ctx.defer(ephemeral=True)

            try:

                synced = await self.bot.tree.sync()

                await ctx.send(f"⚡ Đã đồng bộ thành công **{len(synced)}** lệnh Slash Command!", ephemeral=True)

            except Exception as e:

                await ctx.send(f"❌ Lỗi khi đồng bộ Slash Command: `{e}`", ephemeral=True)

            return



        if act == "servers":

            if not self.bot.guilds:

                return await ctx.send(t(ctx.guild, "OWNER_SERVERS_EMPTY"), ephemeral=True)

            view = GuildsPaginatorView(ctx.author, list(self.bot.guilds))

            return await ctx.send(embed=view.build_embed(ctx.guild), view=view, ephemeral=True)



        if act == "addadmin":

            if not target or not extra:

                return await ctx.send("⚠️ Cú pháp: `/owner addadmin <server_id> <role_id>`", ephemeral=True)

            try:

                gid = int(target.strip())

                rid = int(extra.strip())

            except ValueError:

                return await ctx.send("⚠️ ID máy chủ hoặc ID Role phải là số nguyên hợp lệ!", ephemeral=True)



            guild = self.bot.get_guild(gid)

            if not guild:

                return await ctx.send(t(ctx.guild, "OWNER_ROLE_NOT_FOUND_SERVER"), ephemeral=True)



            role = guild.get_role(rid)

            if not role:

                return await ctx.send(t(ctx.guild, "OWNER_ROLE_NOT_FOUND"), ephemeral=True)



            gid_str = str(guild.id)

            if gid_str not in admin_roles:

                admin_roles[gid_str] = []



            if role.id in admin_roles[gid_str]:

                return await ctx.send(t(ctx.guild, "OWNER_ADDADMIN_EXISTS", role=role.name, guild=guild.name), ephemeral=True)



            admin_roles[gid_str].append(role.id)

            save_admin_roles()

            return await ctx.send(t(ctx.guild, "OWNER_ADDADMIN_SUCCESS", role=role.name, guild=guild.name))



        if act == "rmadmin":

            if not target or not extra:

                return await ctx.send("⚠️ Cú pháp: `/owner rmadmin <server_id> <role_id>`", ephemeral=True)

            try:

                gid = int(target.strip())

                rid = int(extra.strip())

            except ValueError:

                return await ctx.send("⚠️ ID máy chủ hoặc ID Role phải là số nguyên hợp lệ!", ephemeral=True)



            guild = self.bot.get_guild(gid)

            g_name = guild.name if guild else str(gid)

            r_name = guild.get_role(rid).name if (guild and guild.get_role(rid)) else str(rid)



            gid_str = str(gid)

            if gid_str not in admin_roles or rid not in admin_roles[gid_str]:

                return await ctx.send(t(ctx.guild, "OWNER_RMADMIN_NOT_FOUND", role=r_name, guild=g_name), ephemeral=True)



            admin_roles[gid_str].remove(rid)

            save_admin_roles()

            return await ctx.send(t(ctx.guild, "OWNER_RMADMIN_SUCCESS", role=r_name, guild=g_name))



        if act == "listadmin":

            if not admin_roles:

                return await ctx.send(t(ctx.guild, "OWNER_LISTADMIN_EMPTY"), ephemeral=True)



            embed = discord.Embed(title=t(ctx.guild, "OWNER_LISTADMIN_TITLE"), color=discord.Color.gold())

            has_any = False



            for gid_str, r_ids in admin_roles.items():

                guild = self.bot.get_guild(int(gid_str))

                if not guild or not r_ids:

                    continue

                mentions = [guild.get_role(int(rid)).mention for rid in r_ids if guild.get_role(int(rid))]

                if mentions:

                    has_any = True

                    embed.add_field(

                        name=t(ctx.guild, "OWNER_LISTADMIN_FIELD", guild=guild.name),

                        value="\n".join(mentions),

                        inline=False

                    )



            if not has_any:

                return await ctx.send(t(ctx.guild, "OWNER_LISTADMIN_EMPTY"), ephemeral=True)

            return await ctx.send(embed=embed, ephemeral=True)



        if act == "say":

            if not target or not extra:

                return await ctx.send("⚠️ Cú pháp: `/owner say <channel_id> <text>`", ephemeral=True)

            return await self._execute_sayto(ctx, target, extra)



        if act == "restart":

            view = PowerConfirmView(ctx.author, self.bot, action="restart")

            return await ctx.send("⚠️ Bạn có chắc chắn muốn **Khởi động lại (Restart)** toàn bộ Bot không?", view=view, ephemeral=True)



        if act == "shutdown":

            view = PowerConfirmView(ctx.author, self.bot, action="shutdown")

            return await ctx.send(t(ctx.guild, "OWNER_SHUTDOWN_PROMPT"), view=view, ephemeral=True)



        if act == "findrole":

            if not target or not extra:

                return await ctx.send("⚠️ Cú pháp: `/owner findrole <server_id> <role_name>`", ephemeral=True)

            try:

                gid = int(target.strip())

            except ValueError:

                return await ctx.send("⚠️ ID máy chủ phải là số nguyên!", ephemeral=True)



            guild = self.bot.get_guild(gid)

            if not guild:

                return await ctx.send(t(ctx.guild, "OWNER_ROLE_NOT_FOUND_SERVER"), ephemeral=True)



            role = discord.utils.get(guild.roles, name=extra.strip())

            if not role:

                return await ctx.send(t(ctx.guild, "OWNER_ROLE_NOT_FOUND"), ephemeral=True)



            embed = discord.Embed(title=t(ctx.guild, "OWNER_ROLE_INFO_TITLE"), color=discord.Color.gold())

            embed.add_field(name=t(ctx.guild, "OWNER_ROLE_FIELD_SERVER"), value=guild.name, inline=False)

            embed.add_field(name=t(ctx.guild, "OWNER_ROLE_FIELD_NAME"), value=role.name, inline=True)

            embed.add_field(name=t(ctx.guild, "OWNER_ROLE_FIELD_ID"), value=f"`{role.id}`", inline=True)

            embed.add_field(name=t(ctx.guild, "OWNER_ROLE_FIELD_MEMBERS"), value=str(len(role.members)), inline=True)

            return await ctx.send(embed=embed)



    @commands.command(
        name="menubot",
        aliases=["mbot"],
        description="🎛️ Bảng điều khiển và giám sát các tiến trình file Bot (.py)."
    )
    @is_owner()
    async def menubot(

        self,

        ctx: commands.Context,

        action: Literal["panel", "check", "start", "stop", "restart", "info", "net"] = "panel",

        bot_file: Optional[str] = None

    ):

        act = action.lower()



        if act == "panel":

            prefix = ctx.prefix

            embed = discord.Embed(

                title=t(ctx.guild, "OWNER_MENUBOT_CHECK_TITLE2"),

                description=t(ctx.guild, "OWNER_MENUBOT_PANEL_DESC"),

                color=discord.Color.blue()

            )

            embed.add_field(

                name="⏯️ Điều khiển tiến trình",

                value=(

                    f"• `{prefix}menubot start <tên_file>`\n"

                    f"• `{prefix}menubot stop <tên_file>`\n"

                    f"• `{prefix}menubot restart <tên_file>`"

                ),

                inline=False

            )

            embed.add_field(

                name="📊 Giám sát tài nguyên & Mạng",

                value=(

                    f"• `{prefix}menubot info <tên_file>`\n"

                    f"• `{prefix}menubot net <tên_file>`\n"

                    f"• `{prefix}menubot check`"

                ),

                inline=False

            )

            return await ctx.send(embed=embed, ephemeral=True)



        if act == "check":

            if ctx.interaction:

                await ctx.defer()



            bot_files = sorted([f for f in os.listdir(BASE_DIR) if f.endswith(".py")])

            embed = discord.Embed(title=t(ctx.guild, "OWNER_MENUBOT_CHECK_TITLE2"), color=discord.Color.dark_purple())

            running_bots = 0



            for bf in bot_files[:25]:

                proc = self._find_process(bf)

                if proc:

                    running_bots += 1

                    try:

                        with proc.oneshot():

                            ram = round(proc.memory_info().rss / (1024 ** 2), 2)

                            cpu = proc.cpu_percent(interval=None)

                            uptime_seconds = int(time.time() - proc.create_time())

                            hours, remainder = divmod(uptime_seconds, 3600)

                            minutes, _ = divmod(remainder, 60)

                            embed.add_field(

                                name=f"🟢 {bf}",

                                value=f"**PID:** `{proc.pid}` | **RAM:** `{ram} MB` | **CPU:** `{cpu}%` | **Uptime:** `{hours}h {minutes}m`",

                                inline=False

                            )

                    except (psutil.NoSuchProcess, psutil.AccessDenied):

                        embed.add_field(name=f"🔴 {bf}", value="Không hoạt động", inline=False)

                else:

                    embed.add_field(name=f"🔴 {bf}", value="Không hoạt động", inline=False)



            if running_bots == 0:

                embed.description = t(ctx.guild, "OWNER_MENUBOT_CHECK_DESC_EMPTY")



            embed.set_footer(text=f"Kiểm tra lúc {datetime.now().strftime('%H:%M:%S')}")

            return await ctx.send(embed=embed)



        if not bot_file:

            return await ctx.send("⚠️ Vui lòng chỉ định tên file bot `.py` cần thực hiện thao tác!", ephemeral=True)



        clean_file = self._sanitize_bot_file(bot_file)



        if act == "start":

            if not (BASE_DIR / clean_file).exists():

                return await ctx.send(t(ctx.guild, "OWNER_BOT_NOT_FOUND_FILE", file=clean_file), ephemeral=True)



            if self._find_process(clean_file):

                return await ctx.send(t(ctx.guild, "OWNER_BOT_RUNNING_SIMPLE", file=clean_file), ephemeral=True)



            try:

                subprocess.Popen([sys.executable, str(BASE_DIR / clean_file)], cwd=str(BASE_DIR))

                embed = discord.Embed(

                    title=t(ctx.guild, "OWNER_MENUBOT_STARTED"),

                    description=t(ctx.guild, "OWNER_MENUBOT_STARTED_DESC", file=clean_file),

                    color=discord.Color.green()

                )

                await ctx.send(embed=embed)

            except Exception as e:

                await ctx.send(f"❌ Lỗi khi khởi chạy `{clean_file}`: `{e}`", ephemeral=True)

            return



        if act == "stop":

            proc = self._find_process(clean_file)

            if not proc:

                return await ctx.send(t(ctx.guild, "OWNER_BOT_NOT_RUNNING_SIMPLE", file=clean_file), ephemeral=True)



            pid = proc.pid

            proc.kill()

            embed = discord.Embed(title="🔴 Bot Stopped", color=discord.Color.red())

            embed.add_field(name=t(ctx.guild, "OWNER_BOTPING_FIELD_BOT"), value=f"`{clean_file}`", inline=True)

            embed.add_field(name=t(ctx.guild, "OWNER_BOTPING_FIELD_PID"), value=f"`{pid}`", inline=True)

            return await ctx.send(embed=embed)



        if act == "restart":

            if not (BASE_DIR / clean_file).exists():

                return await ctx.send(t(ctx.guild, "OWNER_BOT_NOT_FOUND_FILE2", file=clean_file), ephemeral=True)



            proc = self._find_process(clean_file)

            old_pid = None

            if proc:

                old_pid = proc.pid

                proc.kill()

                await asyncio.sleep(1)



            try:

                subprocess.Popen([sys.executable, str(BASE_DIR / clean_file)], cwd=str(BASE_DIR))

                if old_pid:

                    embed = discord.Embed(title="🔄 Bot Restarted", color=discord.Color.green())

                    embed.add_field(name=t(ctx.guild, "OWNER_BOTPING_FIELD_BOT"), value=f"`{clean_file}`", inline=True)

                    embed.add_field(name="🆔 Old PID", value=f"`{old_pid}`", inline=True)

                else:

                    embed = discord.Embed(

                        title="🟢 Bot Started",

                        description=f"Tiến trình `{clean_file}` chưa chạy trước đó. Đã khởi động mới thành công!",

                        color=discord.Color.blue()

                    )

                await ctx.send(embed=embed)

            except Exception as e:

                await ctx.send(f"❌ Lỗi khi khởi động lại `{clean_file}`: `{e}`", ephemeral=True)

            return



        if act == "info":

            proc = self._find_process(clean_file)

            if not proc:

                return await ctx.send(t(ctx.guild, "OWNER_MENUBOT_INFO_NOT_RUNNING", file=clean_file), ephemeral=True)



            cpu = await asyncio.to_thread(proc.cpu_percent, 0.1)

            with proc.oneshot():

                pid = proc.pid

                ram = round(proc.memory_info().rss / (1024 ** 2), 2)

                uptime_seconds = int(time.time() - proc.create_time())

                hours, remainder = divmod(uptime_seconds, 3600)

                minutes, seconds = divmod(remainder, 60)

                status = proc.status()

                threads = proc.num_threads()

                start_time = datetime.fromtimestamp(proc.create_time()).strftime("%d/%m/%Y %H:%M:%S")

                cmd_text = " ".join(proc.cmdline())



            embed = discord.Embed(title=t(ctx.guild, "OWNER_MENUBOT_INFO_TITLE2", file=clean_file), color=discord.Color.blue())

            embed.add_field(name=t(ctx.guild, "OWNER_BOTPING_FIELD_PID"), value=f"`{pid}`", inline=True)

            embed.add_field(name="📌 Status", value=f"`{status}`", inline=True)

            embed.add_field(name="⚡ CPU", value=f"`{cpu}%`", inline=True)

            embed.add_field(name=t(ctx.guild, "OWNER_BOTPING_FIELD_RAM"), value=f"`{ram} MB`", inline=True)

            embed.add_field(name="🧵 Threads", value=f"`{threads}`", inline=True)

            embed.add_field(name="🕒 Uptime", value=f"`{hours}h {minutes}m {seconds}s`", inline=True)

            embed.add_field(name="🚀 Started At", value=f"`{start_time}`", inline=False)

            embed.add_field(name="💻 Command", value=f"```{cmd_text[:500]}```", inline=False)

            return await ctx.send(embed=embed)



        if act == "net":

            proc = self._find_process(clean_file)

            if not proc:

                return await ctx.send(f"❌ Tiến trình `{clean_file}` hiện không hoạt động.", ephemeral=True)



            try:

                connections = proc.net_connections()

            except AttributeError:

                connections = proc.connections()



            embed = discord.Embed(title=t(ctx.guild, "OWNER_MENUBOT_NET_TITLE2", file=clean_file), color=discord.Color.blue())

            embed.add_field(name=t(ctx.guild, "OWNER_BOTPING_FIELD_PID"), value=f"`{proc.pid}`", inline=False)



            if not connections:

                embed.description = t(ctx.guild, "OWNER_MENUBOT_NET_NONE")

            else:

                lines = []

                for conn in connections[:8]:

                    local = f"{conn.laddr.ip}:{conn.laddr.port}" if conn.laddr else "N/A"

                    remote = f"{conn.raddr.ip}:{conn.raddr.port}" if conn.raddr else "N/A"

                    lines.append(f"📡 **Status:** `{conn.status}` | 🏠 `{local}` ➜ 🌍 `{remote}`")

                embed.description = "\n".join(lines)

            return await ctx.send(embed=embed)



    @commands.command(name="botinfo")

    @is_owner()

    async def botinfo_shortcut(self, ctx: commands.Context):

        await self._execute_botinfo(ctx)



    @commands.command(name="botping", aliases=["bping"])

    @is_owner()

    async def botping_shortcut(self, ctx: commands.Context, bot_file: str):

        clean_file = self._sanitize_bot_file(bot_file)

        proc = self._find_process(clean_file)



        if not proc:

            return await ctx.send(t(ctx.guild, "OWNER_BOTPING_NOT_FOUND", file=clean_file))



        try:

            start = time.time()

            cpu = await asyncio.to_thread(proc.cpu_percent, 0.1)

            response_ms = round((time.time() - start) * 1000)



            if response_ms < 150:

                status = t(ctx.guild, "OWNER_BOTPING_STATUS_GOOD")

                color = discord.Color.green()

            elif response_ms < 300:

                status = t(ctx.guild, "OWNER_BOTPING_STATUS_MEDIUM")

                color = discord.Color.orange()

            else:

                status = t(ctx.guild, "OWNER_BOTPING_STATUS_SLOW")

                color = discord.Color.red()



            ram = round(proc.memory_info().rss / (1024 ** 2), 2)



            embed = discord.Embed(title=t(ctx.guild, "OWNER_BOTPING_TITLE"), color=color)

            embed.add_field(name=t(ctx.guild, "OWNER_BOTPING_FIELD_BOT"), value=f"`{clean_file}`", inline=False)

            embed.add_field(name=t(ctx.guild, "OWNER_BOTPING_FIELD_PID"), value=f"`{proc.pid}`", inline=True)

            embed.add_field(name=t(ctx.guild, "OWNER_BOTPING_FIELD_RESPONSE"), value=f"`{response_ms}ms`", inline=True)

            embed.add_field(name=t(ctx.guild, "OWNER_BOTPING_FIELD_STATUS"), value=status, inline=True)

            embed.add_field(name=t(ctx.guild, "OWNER_BOTPING_FIELD_RAM"), value=f"`{ram} MB`", inline=True)

            embed.add_field(name=t(ctx.guild, "OWNER_BOTPING_FIELD_CPU"), value=f"`{cpu}%`", inline=True)

            embed.set_footer(text=f"Checked by {ctx.author}")

            await ctx.send(embed=embed)

        except Exception as e:

            await ctx.send(f"❌ Lỗi khi kiểm tra tiến trình: `{e}`")



    @commands.command(name="sayto")

    @is_owner()

    async def sayto_shortcut(self, ctx: commands.Context, channel_id: str, *, text: str):

        await self._execute_sayto(ctx, channel_id, text)



    @commands.command(name="restart", aliases=["r", "rebot"])

    @is_owner()

    async def restart_shortcut(self, ctx: commands.Context):

        view = PowerConfirmView(ctx.author, self.bot, action="restart")

        await ctx.send("⚠️ Bạn có chắc chắn muốn **Khởi động lại (Restart)** toàn bộ Bot không?", view=view)



    @commands.command(name="shutdown")

    @is_owner()

    async def shutdown_shortcut(self, ctx: commands.Context):

        view = PowerConfirmView(ctx.author, self.bot, action="shutdown")

        await ctx.send(t(ctx.guild, "OWNER_SHUTDOWN_PROMPT"), view=view)



    @commands.command(name="servers")

    @is_owner()

    async def servers_shortcut(self, ctx: commands.Context):

        if not self.bot.guilds:

            return await ctx.send(t(ctx.guild, "OWNER_SERVERS_EMPTY"))

        view = GuildsPaginatorView(ctx.author, list(self.bot.guilds))

        await ctx.send(embed=view.build_embed(ctx.guild), view=view)



    @commands.command(name="ownerroleids")

    @is_owner()

    async def ownerroleids_shortcut(self, ctx: commands.Context, role: discord.Role):

        await ctx.send(t(ctx.guild, "OWNER_ROLE_ID_MSG", role=role.name, id=role.id))



    @commands.command(name="ownerroleid")

    @is_owner()

    async def ownerroleid_shortcut(self, ctx: commands.Context, guild_id: int, *, role_name: str):

        guild = self.bot.get_guild(guild_id)

        if not guild:

            return await ctx.send(t(ctx.guild, "OWNER_ROLE_NOT_FOUND_SERVER"))



        role = discord.utils.get(guild.roles, name=role_name)

        if not role:

            return await ctx.send(t(ctx.guild, "OWNER_ROLE_NOT_FOUND"))



        embed = discord.Embed(title=t(ctx.guild, "OWNER_ROLE_INFO_TITLE"), color=discord.Color.gold())

        embed.add_field(name=t(ctx.guild, "OWNER_ROLE_FIELD_SERVER"), value=guild.name, inline=False)

        embed.add_field(name=t(ctx.guild, "OWNER_ROLE_FIELD_NAME"), value=role.name, inline=True)

        embed.add_field(name=t(ctx.guild, "OWNER_ROLE_FIELD_ID"), value=f"`{role.id}`", inline=True)

        embed.add_field(name=t(ctx.guild, "OWNER_ROLE_FIELD_MEMBERS"), value=str(len(role.members)), inline=True)

        await ctx.send(embed=embed)





async def setup(bot: commands.Bot):

    await bot.add_cog(OwnerManager(bot))

