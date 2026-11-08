import time
import random
import asyncio
import urllib.parse
from datetime import datetime
import aiohttp
import discord
from discord.ext import commands
from discord import app_commands

from config import OWNER_ID, ZALO_PHONE, OWNER_DISCORD_TAG
from Command_vi.checks import RATESS, afk_users
from mc_link_system import create_link_code, get_linked_account
from Checks_vi.i18n import t, is_vietnamese


class SupportView(discord.ui.View):
    def __init__(self, guild=None):
        super().__init__()
        vi = is_vietnamese(guild)
        lbl = "🆘 Tham Gia Máy Chủ Hỗ Trợ" if vi else "🆘 Join Support Server"
        self.add_item(
            discord.ui.Button(
                label=lbl,
                url="https://discord.gg/jXvKRJkJgh"
            )
        )


class Basic(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.session = None

    async def cog_load(self):
        self.session = aiohttp.ClientSession()

    async def cog_unload(self):
        if self.session and not self.session.closed:
            await self.session.close()

    @commands.hybrid_command(name="ping", aliases=["latency", "pong"], description="Kiểm tra độ trễ của bot")
    async def ping(self, ctx: commands.Context):
        ping_ms = round(self.bot.latency * 1000)
        if ping_ms < 100:
            color = discord.Color.green()
            status = t(ctx.guild, "PING_STATUS_GOOD")
        elif ping_ms < 200:
            color = discord.Color.orange()
            status = t(ctx.guild, "PING_STATUS_MEDIUM")
        else:
            color = discord.Color.red()
            status = t(ctx.guild, "PING_STATUS_SLOW")

        embed = discord.Embed(
            title=t(ctx.guild, "PING_TITLE"),
            description=t(ctx.guild, "PING_DESC"),
            color=color,
            timestamp=datetime.utcnow()
        )
        embed.add_field(name=t(ctx.guild, "PING_FIELD_PING"), value=f"`{ping_ms}ms`", inline=True)
        embed.add_field(name=t(ctx.guild, "PING_FIELD_STATUS"), value=status, inline=True)
        embed.add_field(name=t(ctx.guild, "PING_FIELD_BOT"), value=self.bot.user.name, inline=True)
        if self.bot.user.avatar:
            embed.set_thumbnail(url=self.bot.user.avatar.url)
        embed.set_footer(text=f"Requested by {ctx.author.display_name}")
        await ctx.send(embed=embed)

    @commands.command(name="hello")
    async def hello(self, ctx: commands.Context):
        embed = discord.Embed(
            title=t(ctx.guild, "HELLO_TITLE"),
            description=t(ctx.guild, "HELLO_DESC", mention=ctx.author.mention),
            color=0xffb6c1
        )
        embed.set_thumbnail(url=ctx.author.display_avatar.url)
        await ctx.send(embed=embed)

    @commands.command(name="bye")
    async def bye(self, ctx: commands.Context):
        embed = discord.Embed(
            title=t(ctx.guild, "BYE_TITLE"),
            description=t(ctx.guild, "BYE_DESC", mention=ctx.author.mention),
            color=0xffb6c1
        )
        embed.set_thumbnail(url=ctx.author.display_avatar.url)
        await ctx.send(embed=embed)

    @commands.hybrid_command(name="qr", description="Tạo mã QR code từ nội dung bất kỳ")
    @app_commands.describe(content="Nội dung hoặc đường dẫn cần tạo mã QR")
    async def qr(self, ctx: commands.Context, *, content: str = None):
        if not content:
            return await ctx.send(t(ctx.guild, "QR_NEED_CONTENT"), ephemeral=True)
        encoded_content = urllib.parse.quote(content)
        qr_url = f"https://api.qrserver.com/v1/create-qr-code/?size=300x300&data={encoded_content}"
        embed = discord.Embed(
            title=t(ctx.guild, "QR_TITLE"),
            description=t(ctx.guild, "QR_CONTENT_LABEL", content=content),
            color=discord.Color.green()
        )
        embed.set_image(url=qr_url)
        embed.set_footer(text=t(ctx.guild, "QR_FOOTER", name=ctx.author.name), icon_url=ctx.author.display_avatar.url)
        await ctx.send(embed=embed)

    @commands.hybrid_command(name="meme", description="Xem ảnh meme ngẫu nhiên")
    async def meme(self, ctx: commands.Context):
        if ctx.interaction:
            await ctx.defer()
        loading_msg = await ctx.send(t(ctx.guild, "MEME_LOADING"))

        meme_api_url = "https://meme-api.com/gimme"
        try:
            if not self.session or self.session.closed:
                self.session = aiohttp.ClientSession()

            data = None
            for _ in range(3):
                async with self.session.get(meme_api_url) as response:
                    if response.status == 200:
                        temp_data = await response.json()
                        if not temp_data.get("nsfw", False):
                            data = temp_data
                            break

            if data:
                embed = discord.Embed(
                    title=data["title"],
                    url=data["postLink"],
                    color=discord.Color.random()
                )
                embed.set_image(url=data["url"])
                embed.set_footer(text=f"Nguồn: r/{data['subreddit']} | 👍 {data['ups']} upvotes")
                await loading_msg.edit(content=None, embed=embed)
            else:
                await loading_msg.edit(content=t(ctx.guild, "MEME_ERROR"))
        except Exception as e:
            await loading_msg.edit(content=t(ctx.guild, "MEME_ERROR_GENERIC", error=e))

    @commands.command(name="zalo")
    async def zalo(self, ctx: commands.Context):
        embed = discord.Embed(
            description=t(ctx.guild, "ZALO_DESC", phone=ZALO_PHONE),
            color=0x0068ff
        )
        await ctx.send(embed=embed)

    @commands.command(name="dis", aliases=["discord"])
    async def dis(self, ctx: commands.Context):
        embed = discord.Embed(
            description=t(ctx.guild, "DIS_DESC", tag=OWNER_DISCORD_TAG),
            color=0x5865f2
        )
        await ctx.send(embed=embed)

    @commands.hybrid_command(name="link", description="Tạo mã liên kết tài khoản Discord với Minecraft")
    async def link(self, ctx: commands.Context):
        existing = get_linked_account(ctx.author.id)
        if existing:
            return await ctx.send(
                t(ctx.guild, "LINK_ALREADY", name=existing.get("minecraft_name"), uuid=existing.get("minecraft_uuid")),
                ephemeral=True
            )
        code = create_link_code(ctx.author.id)
        embed = discord.Embed(
            title=t(ctx.guild, "LINK_TITLE"),
            description=t(ctx.guild, "LINK_DESC", code=code),
            color=discord.Color.green()
        )
        await ctx.send(embed=embed, ephemeral=True)

    # --- NHÓM LỆNH HYBRID /user (Tối ưu hóa Slash Commands) ---
    @commands.hybrid_group(name="user", aliases=["nguoidung"], description="Tra cứu thông tin người dùng: Avatar, Banner, Hồ sơ")
    async def user_group(self, ctx: commands.Context):
        """Xem thông tin người dùng nếu không chọn lệnh con."""
        if ctx.invoked_subcommand is None:
            await self._handle_userinfo(ctx, None)

    @user_group.command(name="info", description="Xem thông tin chi tiết tài khoản")
    @app_commands.describe(thanh_vien="Thành viên bạn muốn xem thông tin")
    async def user_info_cmd(self, ctx: commands.Context, thanh_vien: discord.Member = None):
        await self._handle_userinfo(ctx, thanh_vien)

    @user_group.command(name="avatar", aliases=["av"], description="Xem ảnh đại diện của thành viên")
    @app_commands.describe(thanh_vien="Thành viên bạn muốn xem (để trống nếu là chính bạn)")
    async def user_avatar_cmd(self, ctx: commands.Context, thanh_vien: discord.Member = None):
        await self._handle_avatar(ctx, thanh_vien)

    @user_group.command(name="banner", description="Xem ảnh bìa hồ sơ của thành viên")
    @app_commands.describe(thanh_vien="Thành viên bạn muốn xem banner")
    async def user_banner_cmd(self, ctx: commands.Context, thanh_vien: discord.Member = None):
        await self._handle_banner(ctx, thanh_vien)

    # Prefix shortcuts: !avatar, !av, !banner, !userinfo
    @commands.command(name="avatar", aliases=["av"])
    async def avatar(self, ctx: commands.Context, thanh_vien: discord.Member = None):
        await self._handle_avatar(ctx, thanh_vien)

    @commands.command(name="banner")
    async def banner(self, ctx: commands.Context, thanh_vien: discord.Member = None):
        await self._handle_banner(ctx, thanh_vien)

    @commands.command(name="userinfo", aliases=["profile", "info"])
    async def userinfo(self, ctx: commands.Context, thanh_vien: discord.Member = None):
        await self._handle_userinfo(ctx, thanh_vien)

    async def _handle_avatar(self, ctx: commands.Context, thanh_vien: discord.Member = None):
        target = thanh_vien or ctx.author
        embed = discord.Embed(
            title=t(ctx.guild, "AVATAR_TITLE", name=target.display_name),
            color=target.color if target.color != discord.Color.default() else discord.Color.blue()
        )
        embed.set_image(url=target.display_avatar.url)
        av_url = target.display_avatar
        embed.description = f"[PNG]({av_url.with_format('png')}) | [JPG]({av_url.with_format('jpg')}) | [WEBP]({av_url.with_format('webp')})"
        await ctx.send(embed=embed)

    async def _handle_banner(self, ctx: commands.Context, thanh_vien: discord.Member = None):
        target = thanh_vien or ctx.author
        user_obj = await self.bot.fetch_user(target.id)
        if not user_obj.banner:
            return await ctx.send(f"ℹ️ Thành viên **{target.display_name}** không có ảnh bìa hồ sơ.", ephemeral=True)

        embed = discord.Embed(
            title=f"🖼️ Ảnh bìa của {target.display_name}",
            color=user_obj.accent_color or discord.Color.blue()
        )
        embed.set_image(url=user_obj.banner.url)
        embed.description = f"[Tải xuống gốc]({user_obj.banner.url})"
        await ctx.send(embed=embed)

    async def _handle_userinfo(self, ctx: commands.Context, thanh_vien: discord.Member = None):
        target = thanh_vien
        if not target and getattr(ctx, "message", None) and ctx.message.mentions:
            target = ctx.message.mentions[0]
        if target and target.id != ctx.author.id:
            from Checks_vi.mod import OWNER_ID
            is_owner = (ctx.author.id in (1144785664458637394, OWNER_ID) or await ctx.bot.is_owner(ctx.author))
            if not is_owner:
                return await ctx.send("❌ Bạn chỉ có thể xem thông tin tài khoản của chính mình! Không được phép xem của người khác.", ephemeral=True)
        target = target or ctx.author
        embed = discord.Embed(
            title=t(ctx.guild, "USERINFO_TITLE", name=target.display_name),
            color=target.top_role.color if target.top_role.color != discord.Color.default() else discord.Color.blue(),
            timestamp=datetime.utcnow()
        )
        embed.set_thumbnail(url=target.display_avatar.url)
        embed.add_field(name=t(ctx.guild, "USERINFO_FULLNAME"), value=f"`{target}`", inline=True)
        embed.add_field(name=t(ctx.guild, "USERINFO_ID"), value=f"`{target.id}`", inline=True)
        embed.add_field(name=t(ctx.guild, "USERINFO_TOPROLE"), value=target.top_role.mention, inline=False)
        embed.add_field(name=t(ctx.guild, "USERINFO_CREATED"), value=f"<t:{int(target.created_at.timestamp())}:F>", inline=False)
        if target.joined_at:
            embed.add_field(name=t(ctx.guild, "USERINFO_JOINED"), value=f"<t:{int(target.joined_at.timestamp())}:F>", inline=False)

        roles = [role.mention for role in reversed(target.roles) if role.name != "@everyone"]
        role_list = ", ".join(roles[:10]) + ("..." if len(roles) > 10 else "")
        embed.add_field(name=t(ctx.guild, "USERINFO_ROLES", count=len(roles)), value=role_list if roles else t(ctx.guild, "USERINFO_ROLES_NONE"), inline=False)

        try:
            from data.database import get_user_data
            udata = get_user_data(ctx.guild.id, target.id)
            coins = udata.get("coins", 0)
            bank = udata.get("bank", 0)
            xu = udata.get("xu", 0)
            networth = coins + bank
            finance_str = f"🪙 **Ví:** `{coins:,}` coins | 🏦 **Ngân hàng:** `{bank:,}` coins\n✨ **Xu VIP:** `{xu:,}` xu | 💎 **Tổng tài sản:** `{networth:,}` coins"
            embed.add_field(name="💳 Thông Tin Tài Chính", value=finance_str, inline=False)
        except Exception:
            pass

        await ctx.send(embed=embed)

    @commands.hybrid_command(name="support", aliases=["report", "feedback", "sup"], description="Gửi báo cáo hoặc phản hồi đến chủ bot")
    @app_commands.describe(message="Nội dung cần báo cáo hoặc phản hồi")
    async def support(self, ctx: commands.Context, *, message: str = None):
        if message is None:
            embed = discord.Embed(
                title=t(ctx.guild, "SUPPORT_HELP_TITLE"),
                description=t(ctx.guild, "SUPPORT_HELP_DESC", prefix=ctx.prefix),
                color=discord.Color.orange()
            )
            return await ctx.send(embed=embed, view=SupportView(ctx.guild), ephemeral=True)

        owner = self.bot.get_user(OWNER_ID)
        if owner is None:
            try:
                owner = await self.bot.fetch_user(OWNER_ID)
            except discord.NotFound:
                return await ctx.send(t(ctx.guild, "SUPPORT_OWNER_NOT_FOUND"), ephemeral=True)

        embed_report = discord.Embed(
            title=t(ctx.guild, "SUPPORT_REPORT_TITLE"),
            color=discord.Color.red(),
            timestamp=datetime.utcnow()
        )
        embed_report.add_field(name=t(ctx.guild, "SUPPORT_REPORT_SENDER"), value=f"{ctx.author}\n`{ctx.author.id}`", inline=False)
        embed_report.add_field(name=t(ctx.guild, "SUPPORT_REPORT_SERVER"), value=f"{ctx.guild.name}\n`{ctx.guild.id}`", inline=False)
        embed_report.add_field(name=t(ctx.guild, "SUPPORT_REPORT_CONTENT"), value=message, inline=False)

        try:
            await owner.send(embed=embed_report)
            embed_success = discord.Embed(
                title=t(ctx.guild, "SUPPORT_SENT"),
                description=t(ctx.guild, "SUPPORT_SENT_DESC"),
                color=discord.Color.green()
            )
            await ctx.send(embed=embed_success, ephemeral=True)
        except discord.Forbidden:
            await ctx.send(t(ctx.guild, "SUPPORT_OWNER_DM_FORBIDDEN"), ephemeral=True)

    @commands.hybrid_command(name="afk", description="Bật chế độ vắng mặt")
    @app_commands.describe(reason="Lý do vắng mặt")
    async def afk(self, ctx: commands.Context, *, reason: str = "AFK"):
        user_id = str(ctx.author.id)
        afk_users[user_id] = {"reason": reason, "time": time.time()}
        embed = discord.Embed(
            title=t(ctx.guild, "AFK_ENABLED_TITLE"),
            description=t(ctx.guild, "AFK_ENABLED_DESC", mention=ctx.author.mention, reason=reason),
            color=discord.Color.orange()
        )
        await ctx.send(embed=embed)

    @commands.command(name="ids")
    @commands.guild_only()
    async def ids(self, ctx: commands.Context):
        embed = discord.Embed(
            title=t(ctx.guild, "IDS_TITLE"),
            color=discord.Color.dark_grey()
        )
        embed.add_field(name=t(ctx.guild, "IDS_SERVER"), value=f"`{ctx.guild.id}`", inline=False)
        embed.add_field(name=t(ctx.guild, "IDS_USER"), value=f"`{ctx.author.id}`", inline=False)
        await ctx.send(embed=embed)

    async def rate_autocomplete(self, interaction: discord.Interaction, current: str):
        return [
            app_commands.Choice(name=k, value=k)
            for k in RATESS.keys() if current.lower() in k.lower()
        ][:25]

    @commands.hybrid_command(name="rate", description="Đo chỉ số vui nhộn của thành viên")
    @app_commands.describe(chi_so="Chỉ số cần đo", thanh_vien="Thành viên được chọn")
    @app_commands.autocomplete(chi_so=rate_autocomplete)
    async def rate(self, ctx: commands.Context, chi_so: str = None, thanh_vien: discord.Member = None):
        if chi_so is None:
            available_rates = ", ".join([f"`{key}`" for key in RATESS.keys()])
            embed = discord.Embed(
                title=t(ctx.guild, "RATE_NEED_CHOICE"),
                description=t(ctx.guild, "RATE_NEED_CHOICE_DESC", rates=available_rates),
                color=discord.Color.blue()
            )
            return await ctx.send(embed=embed, ephemeral=True)

        chi_so_lower = chi_so.lower()
        if chi_so_lower not in RATESS:
            return await ctx.send(t(ctx.guild, "RATE_INVALID"), ephemeral=True)

        target = thanh_vien or ctx.author
        rate_percent = random.randint(0, 100)
        filled = "█" * (rate_percent // 10)
        empty = "░" * (10 - (rate_percent // 10))

        embed = discord.Embed(
            title=f"{RATESS[chi_so_lower]} của {target.display_name}",
            description=f"**{rate_percent}%**\n`[{filled}{empty}]`",
            color=discord.Color.random()
        )
        await ctx.send(embed=embed)

    @commands.hybrid_command(name="serverinfo", aliases=["svinfo"], description="Xem thông tin chi tiết về máy chủ")
    @commands.guild_only()
    async def serverinfo(self, ctx: commands.Context):
        guild = ctx.guild
        embed = discord.Embed(
            title=t(guild, "SERVERINFO_TITLE", name=guild.name),
            color=discord.Color.blurple(),
            timestamp=datetime.utcnow()
        )
        if guild.icon:
            embed.set_thumbnail(url=guild.icon.url)

        owner_mention = f"<@{guild.owner_id}>" if guild.owner_id else "Không rõ"
        embed.add_field(name=t(guild, "SERVERINFO_OWNER"), value=owner_mention, inline=True)
        embed.add_field(name=t(guild, "SERVERINFO_ID"), value=f"`{guild.id}`", inline=True)
        embed.add_field(name=t(guild, "SERVERINFO_CREATED"), value=f"<t:{int(guild.created_at.timestamp())}:F>", inline=False)

        total_members = guild.member_count or len(guild.members)
        bots = sum(1 for member in guild.members if member.bot)
        humans = total_members - bots
        embed.add_field(name=t(guild, "SERVERINFO_MEMBERS"), value=t(guild, "SERVERINFO_MEMBERS_VALUE", total=total_members, humans=humans, bots=bots), inline=True)

        text_channels = len(guild.text_channels)
        voice_channels = len(guild.voice_channels)
        embed.add_field(name=t(guild, "SERVERINFO_CHANNELS"), value=t(guild, "SERVERINFO_CHANNELS_VALUE", total=text_channels + voice_channels, text=text_channels, voice=voice_channels), inline=True)

        role_count = len(guild.roles)
        embed.add_field(name=t(guild, "SERVERINFO_OTHER"), value=t(guild, "SERVERINFO_ROLES", count=role_count), inline=True)
        embed.set_footer(text=t(guild, "SERVERINFO_FOOTER", name=ctx.author.display_name), icon_url=ctx.author.display_avatar.url)
        await ctx.send(embed=embed)

    @commands.hybrid_command(name="poll", description="Tạo bảng khảo sát bình chọn nhanh")
    @app_commands.describe(cau_hoi="Câu hỏi khảo sát", lua_chon_1="Lựa chọn 1", lua_chon_2="Lựa chọn 2")
    async def poll(self, ctx: commands.Context, cau_hoi: str, lua_chon_1: str = "👍 Đồng ý", lua_chon_2: str = "👎 Từ chối"):
        embed = discord.Embed(
            title=f"📊 Khảo sát ý kiến: {cau_hoi}",
            description=f"1️⃣ {lua_chon_1}\n\n2️⃣ {lua_chon_2}",
            color=discord.Color.gold(),
            timestamp=datetime.utcnow()
        )
        embed.set_footer(text=f"Khởi tạo bởi {ctx.author.display_name}", icon_url=ctx.author.display_avatar.url)
        msg = await ctx.send(embed=embed)
        await msg.add_reaction("1️⃣")
        await msg.add_reaction("2️⃣")

    @commands.command(name="choose")
    async def choose(self, ctx: commands.Context, *, options: str):
        choices = [c.strip() for c in options.split(",") if c.strip()]
        if len(choices) < 2:
            return await ctx.send("⚠️ Vui lòng nhập ít nhất 2 lựa chọn cách nhau bằng dấu phẩy (`,`)!")
        chosen = random.choice(choices)
        await ctx.send(f"🤔 Lựa chọn ngẫu nhiên: **{chosen}** 🎉")

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if message.author.bot or not message.guild:
            return

        user_id = str(message.author.id)
        if user_id in afk_users:
            afk_data = afk_users[user_id]
            if time.time() - afk_data.get("time", 0) > 3.0:
                del afk_users[user_id]
                duration_sec = int(time.time() - afk_data.get("time", time.time()))
                time_str = f" ({duration_sec // 60} phút trước)" if duration_sec > 60 else ""

                embed = discord.Embed(
                    description=t(message.guild, "AFK_WELCOME_BACK", mention=message.author.mention) + time_str,
                    color=discord.Color.green()
                )
                await message.channel.send(embed=embed, delete_after=10)

        for mentioned in message.mentions:
            mid = str(mentioned.id)
            if mid in afk_users:
                reason = afk_users[mid].get("reason", "AFK")
                await message.channel.send(
                    t(message.guild, "AFK_NOTIFY", mention=mentioned.mention, reason=reason),
                    delete_after=10
                )
                break


async def setup(bot):
    await bot.add_cog(Basic(bot))
