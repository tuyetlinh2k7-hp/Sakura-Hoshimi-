from discord import app_commands
import discord
from discord import app_commands
import json
import time
import os
from discord.ext import commands
from config import OWNER_ID
from Checks_vi.i18n import t, is_vietnamese

blacklist_users = set()
# Per-guild blacklist: {guild_id_str: set(user_ids)}
guild_blacklist = {}
appeal_cooldown = {}
APPEAL_CHANNEL_ID = 1505854802645487696
BLACKLIST_FILE = "data/blacklist.json"

# Tự động tạo thư mục data nếu chưa tồn tại nhằm tránh lỗi FileNotFoundError
os.makedirs(os.path.dirname(BLACKLIST_FILE), exist_ok=True)

def save_blacklist():
    # Lưu dạng mới {global:[], guilds:{}} để hỗ trợ blacklist theo server, vẫn tương thích bản cũ (list flat)
    try:
        data = {"global": sorted(list(blacklist_users)), "guilds": {gid: sorted(list(s)) for gid, s in guild_blacklist.items() if s}}
        with open(BLACKLIST_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4, ensure_ascii=False)
    except Exception as e:
        print(f"[BLACKLIST] save lỗi: {e}")

def load_blacklist():
    global blacklist_users, guild_blacklist
    if os.path.exists(BLACKLIST_FILE):
        try:
            with open(BLACKLIST_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                if isinstance(data, list):
                    # file cũ dạng list phẳng -> coi như global
                    blacklist_users = set(int(x) for x in data if str(x).isdigit())
                    guild_blacklist = {}
                elif isinstance(data, dict):
                    g = data.get("global", [])
                    blacklist_users = set(int(x) for x in g if str(x).isdigit())
                    guild_blacklist = {}
                    for gid, lst in (data.get("guilds") or {}).items():
                        guild_blacklist[str(gid)] = set(int(x) for x in lst if str(x).isdigit())
                else:
                    blacklist_users = set()
                    guild_blacklist = {}
        except Exception as e:
            print(f"[❌ ERROR] Không thể load file blacklist: {e}")
            blacklist_users = set()
            guild_blacklist = {}

def is_blacklisted(user_id: int, guild_id=None) -> bool:
    uid=int(user_id)
    if uid in blacklist_users:
        return True
    if guild_id is not None:
        s=guild_blacklist.get(str(guild_id))
        if s and uid in s:
            return True
    return False

def add_guild_blacklist(guild_id, user_id):
    gid=str(guild_id); uid=int(user_id)
    guild_blacklist.setdefault(gid, set()).add(uid)
    save_blacklist()

def remove_guild_blacklist(guild_id, user_id):
    gid=str(guild_id); uid=int(user_id)
    s=guild_blacklist.get(gid)
    if s and uid in s:
        s.discard(uid)
        if not s:
            guild_blacklist.pop(gid, None)
        save_blacklist()
        return True
    return False

# Load danh sách cấm ngay khi khởi động file
load_blacklist()


# --- INTERACTIVE BUTTONS FOR APPEAL ---
class AppealView(discord.ui.View):
    def __init__(self, target_user: discord.User, is_blacklisted: bool, guild=None):
        super().__init__(timeout=None) # Giữ nút bấm hoạt động vĩnh viễn (Persistent View)
        self.target_user = target_user
        self.is_blacklisted = is_blacklisted
        vi = is_vietnamese(guild)
        self.unblacklist_btn.label = "✅ Gỡ Blacklist" if vi else "✅ Un-Blacklist"
        self.ban_btn.label = "🔨 Ban Khỏi Server" if vi else "🔨 Ban From Server"

    @discord.ui.button(label="✅ Gỡ Blacklist", style=discord.ButtonStyle.green)
    async def unblacklist_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != OWNER_ID:
            return await interaction.response.send_message(t(interaction.guild, "BLACKLIST_NO_PERM"), ephemeral=True)

        if self.target_user.id in blacklist_users:
            blacklist_users.remove(self.target_user.id)
            save_blacklist()

            await interaction.response.send_message(t(interaction.guild, "BLACKLIST_UNBLACKLIST_DONE", user=self.target_user))
            
            button.disabled = True
            await interaction.message.edit(view=self)

            try:
                await self.target_user.send(t(interaction.guild, "BLACKLIST_DM_UNBANNED_MSG"))
            except discord.Forbidden:
                pass
        else:
            await interaction.response.send_message(t(interaction.guild, "BLACKLIST_NOT_IN_LIST"), ephemeral=True)

    @discord.ui.button(label="🔨 Ban Khỏi Server", style=discord.ButtonStyle.danger)
    async def ban_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != OWNER_ID:
            return await interaction.response.send_message(t(interaction.guild, "BLACKLIST_NO_PERM"), ephemeral=True)

        if not interaction.guild:
            return await interaction.response.send_message(t(interaction.guild, "BLACKLIST_ONLY_GUILD"), ephemeral=True)

        try:
            await interaction.guild.ban(self.target_user, reason="Phản hồi khiếu nại (Appeal) bị từ chối bởi Owner.")
            await interaction.response.send_message(t(interaction.guild, "BLACKLIST_BAN_SUCCESS", user=self.target_user))
            
            button.disabled = True
            await interaction.message.edit(view=self)
        except discord.Forbidden:
            await interaction.response.send_message(t(interaction.guild, "BLACKLIST_BAN_NO_PERM"), ephemeral=True)
        except Exception as e:
            await interaction.response.send_message(t(interaction.guild, "BLACKLIST_ERROR", error=e), ephemeral=True)


# --- MAIN COG CLASS ---
class BlackList(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        # Đăng ký một Global Check cho bot ngay khi Cog được khởi tạo
        self.bot.add_check(self.blacklist_global_check)

    def cog_unload(self):
        # Hủy đăng ký check khi Cog bị reload/unload để tránh lỗi trùng lặp check
        self.bot.remove_check(self.blacklist_global_check)

    async def blacklist_global_check(self, ctx):
        """Hàm kiểm tra toàn cục: Chặn nếu User bị cấm global hoặc cấm theo server hiện tại"""
        if ctx.command and ctx.command.name == "appeal":
            return True
        guild_id = str(ctx.guild.id) if ctx.guild else None
        if is_blacklisted(ctx.author.id, guild_id):
            embed = discord.Embed(
                title=t(ctx.guild, "BLACKLIST_DENIED_TITLE"),
                description=t(ctx.guild, "BLACKLIST_DENIED_DESC", mention=ctx.author.mention, prefix=ctx.prefix),
                color=discord.Color.red()
            )
            scope = "toàn cục" if ctx.author.id in blacklist_users else "server này"
            embed.set_footer(text=f"Bị cấm phạm vi: {scope} • Liên hệ admin để gỡ")
            await ctx.send(embed=embed)
            return False
        return True

    @commands.command()
    async def appeal(self, ctx, *, message: str = None):
        if not message:
            return await ctx.send(t(ctx.guild, "BLACKLIST_APPEAL_NEED_CONTENT", prefix=ctx.prefix))

        is_blacklisted = ctx.author.id in blacklist_users
        now = time.time()

        if ctx.author.id in appeal_cooldown:
            last = appeal_cooldown[ctx.author.id]
            remain = int(60 - (now - last))
            if remain > 0:
                return await ctx.send(t(ctx.guild, "BLACKLIST_APPEAL_COOLDOWN", remain=remain))

        appeal_cooldown[ctx.author.id] = now

        channel = self.bot.get_channel(APPEAL_CHANNEL_ID)
        if not channel:
            return await ctx.send(t(ctx.guild, "BLACKLIST_APPEAL_NO_CHANNEL"))

        embed = discord.Embed(
            title="📩 Phản Hồi Từ Người Dùng",
            color=discord.Color.orange()
        )
        embed.set_thumbnail(url=ctx.author.display_avatar.url)
        embed.add_field(name="👤 Người gửi", value=f"{ctx.author}\n`{ctx.author.id}`", inline=False)
        embed.add_field(name="⛔ Trạng thái", value="`Blacklist`" if is_blacklisted else "`Normal / Unknown`", inline=True)
        embed.add_field(name="📝 Nội dung khiếu nại", value=f"```{message}```", inline=False)
        embed.timestamp = discord.utils.utcnow()

        view = AppealView(ctx.author, is_blacklisted)
        await channel.send(embed=embed, view=view)

        await ctx.send(t(ctx.guild, "BLACKLIST_APPEAL_SENT"))
    
    @commands.command()
    @commands.is_owner()
    async def blacklist(self, ctx, action: str = None, user: discord.User = None, *, reason: str = "Không có lý do cụ thể"):
        if action is None:
            embed = discord.Embed(
                title=t(ctx.guild, "BLACKLIST_HELP_TITLE"),
                description=t(ctx.guild, "BLACKLIST_HELP_DESC", prefix=ctx.prefix),
                color=discord.Color.red()
            )
            return await ctx.send(embed=embed)

        action_lower = action.lower()

        if action_lower == "add":
            if user is None:
                return await ctx.send(t(ctx.guild, "BLACKLIST_NEED_USER"))

            if user.id in blacklist_users:
                return await ctx.send(t(ctx.guild, "BLACKLIST_ALREADY"))

            blacklist_users.add(user.id)
            save_blacklist()

            embed = discord.Embed(
                title=t(ctx.guild, "BLACKLIST_EXEC_TITLE"),
                color=discord.Color.red()
            )
            embed.set_thumbnail(url=user.display_avatar.url)
            embed.add_field(name="👤 Đối tượng", value=f"{user}\n`{user.id}`", inline=False)
            embed.add_field(name="📝 Lý do cấm", value=reason, inline=False)
            embed.add_field(name="👮 Người thực thi", value=ctx.author.mention, inline=False)
            await ctx.send(embed=embed)

            try:
                dm = discord.Embed(
                    title=t(ctx.guild, "BLACKLIST_DM_TITLE"),
                    description=t(ctx.guild, "BLACKLIST_DM_DESC", prefix=ctx.prefix),
                    color=discord.Color.red()
                )
                dm.add_field(name=t(ctx.guild, "BLACKLIST_DM_REASON"), value=reason, inline=False)
                await user.send(embed=dm)
            except discord.Forbidden:
                pass

        elif action_lower in ["remove", "del", "delete"]:
            if user is None:
                return await ctx.send(t(ctx.guild, "BLACKLIST_NEED_USER_REMOVE"))

            if user.id not in blacklist_users:
                return await ctx.send(t(ctx.guild, "BLACKLIST_NOT_IN_LIST2"))

            blacklist_users.remove(user.id)
            save_blacklist()

            embed = discord.Embed(
                title=t(ctx.guild, "BLACKLIST_REMOVE_TITLE"),
                description=t(ctx.guild, "BLACKLIST_REMOVE_DESC", mention=user.mention, id=user.id),
                color=discord.Color.green()
            )
            await ctx.send(embed=embed)

            try:
                await user.send(t(ctx.guild, "BLACKLIST_DM_UNBAN"))
            except discord.Forbidden:
                pass

        elif action_lower == "list":
            if not blacklist_users:
                return await ctx.send(t(ctx.guild, "BLACKLIST_LIST_EMPTY"))

            text = "\n".join(f"• `{user_id}`" for user_id in blacklist_users)
            if len(text) > 4000:
                text = text[:3900] + "\n...và một số ID khác"

            embed = discord.Embed(
                title=t(ctx.guild, "BLACKLIST_LIST_TITLE"),
                description=text,
                color=discord.Color.red()
            )
            await ctx.send(embed=embed)
        else:
            await ctx.send(t(ctx.guild, "BLACKLIST_INVALID_ACTION"))

    @commands.hybrid_command(name="gblacklist", description="Cấm/mở cấm theo server (phạm vi máy chủ) - cần Manage Server")
    @app_commands.describe(action="add/remove/list", user="Người dùng cần cấm/mở", reason="Lý do")
    @commands.has_permissions(manage_guild=True)
    async def gblacklist(self, ctx, action: str = None, user: discord.User = None, *, reason: str = "Không có lý do cụ thể"):
        if not ctx.guild:
            return await ctx.send("❌ Chỉ dùng trong server.", ephemeral=True)
        if action is None:
            # help embed
            gid=str(ctx.guild.id)
            lst=guild_blacklist.get(gid, set())
            cnt=len(lst)
            embed=discord.Embed(title=f"🚫 Blacklist Server — {ctx.guild.name}", description=f"Phạm vi **máy chủ** này: `{cnt}` người bị cấm dùng bot.\n\n`{ctx.prefix}gblacklist add @user [lý do]`\n`{ctx.prefix}gblacklist remove @user`\n`{ctx.prefix}gblacklist list`", color=discord.Color.orange())
            if cnt:
                embed.add_field(name="Danh sách", value="\n".join(f"• `{uid}`" for uid in list(lst)[:30]), inline=False)
            return await ctx.send(embed=embed, ephemeral=True)
        act=action.lower()
        gid=str(ctx.guild.id)
        if act=="add":
            if user is None: return await ctx.send("❌ Cần @user.", ephemeral=True)
            if user.id==ctx.author.id: return await ctx.send("❌ Không tự cấm mình.", ephemeral=True)
            if is_blacklisted(user.id, gid):
                # kiểm tra đã trong guild chưa
                if user.id in guild_blacklist.get(gid, set()):
                    return await ctx.send(f"⚠️ {user.mention} đã bị cấm ở server này rồi.", ephemeral=True)
                # nếu đã global thì vẫn báo
                if user.id in blacklist_users:
                    return await ctx.send(f"⚠️ {user.mention} đã bị cấm toàn cục rồi.", ephemeral=True)
            add_guild_blacklist(gid, user.id)
            embed=discord.Embed(title="🚫 Đã cấm dùng bot (server)", color=discord.Color.red())
            embed.set_thumbnail(url=user.display_avatar.url)
            embed.add_field(name="👤 Đối tượng", value=f"{user} `{user.id}`", inline=False)
            embed.add_field(name="🏰 Server", value=ctx.guild.name, inline=True)
            embed.add_field(name="📝 Lý do", value=reason, inline=False)
            await ctx.send(embed=embed)
            try:
                await user.send(f"🚫 Bạn đã bị cấm dùng bot ở server **{ctx.guild.name}**.\nLý do: {reason}")
            except: pass
        elif act in ["remove","del","delete","mở"]:
            if user is None: return await ctx.send("❌ Cần @user.", ephemeral=True)
            if not remove_guild_blacklist(gid, user.id):
                return await ctx.send(f"❌ {user.mention} không có trong blacklist server.", ephemeral=True)
            await ctx.send(embed=discord.Embed(title="✅ Đã mở cấm (server)", description=f"{user.mention} (`{user.id}`) đã được mở dùng bot ở **{ctx.guild.name}**.", color=discord.Color.green()))
            try:
                await user.send(f"✅ Bạn đã được mở cấm dùng bot ở **{ctx.guild.name}**.")
            except: pass
        elif act=="list":
            lst=guild_blacklist.get(gid, set())
            if not lst: return await ctx.send("📋 Blacklist server trống.", ephemeral=True)
            txt="\n".join(f"• `{uid}`" for uid in lst)
            if len(txt)>3900: txt=txt[:3900]+"\n..."
            await ctx.send(embed=discord.Embed(title=f"📋 Blacklist — {ctx.guild.name}", description=txt, color=discord.Color.orange()), ephemeral=True)
        else:
            await ctx.send("❌ action phải là `add/remove/list`.", ephemeral=True)

async def setup(bot):
    await bot.add_cog(BlackList(bot))