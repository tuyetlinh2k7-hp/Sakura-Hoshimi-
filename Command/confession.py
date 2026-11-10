import discord
from discord import app_commands
from discord.ext import commands
import json
import os
import traceback
from Check.i18n import t

CONFIG_FILE = "data/cfs_config.json"
DATA_FILE = "data/cfs_data.json"

def load_config():
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, "r", encoding="utf-8") as f:
            try: return json.load(f)
            except: return {}
    return {}

def save_config(config):
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump(config, f, indent=4, ensure_ascii=False)

def get_guild_confession(guild_id):
    cfg=load_config().get(str(guild_id), {})
    # defaults như hình web (tất cả bật)
    return {
        "enabled": cfg.get("enabled", True) if "enabled" in cfg else True,
        "confession_channel_id": cfg.get("confession_channel_id"),
        "log_channel_id": cfg.get("log_channel_id"),
        "allow_public": cfg.get("allow_public", True) if "allow_public" in cfg else True,
        "allow_anonymous": cfg.get("allow_anonymous", True) if "allow_anonymous" in cfg else True,
        "create_thread": cfg.get("create_thread", True) if "create_thread" in cfg else True,
        "anon_reply": cfg.get("anon_reply", True) if "anon_reply" in cfg else True,
    }

def get_and_increment_cfs_number():
    if not os.path.exists(DATA_FILE):
        count = 1
    else:
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            try:
                data = json.load(f)
                count = data.get("cfs_count", 1)
            except:
                count = 1
    
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump({"cfs_count": count + 1}, f)
        return count

def create_panel_embed(guild=None):
    embed = discord.Embed(
        title=t(guild, "CFS_PANEL_TITLE"),
        description=t(guild, "CFS_PANEL_DESC"),
        color=0x2F3136
    )
    embed.set_footer(text=t(guild, "CFS_PANEL_FOOTER"))
    return embed

class ConfessionCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    async def cog_load(self):
        self.bot.add_view(CreateConfessionView(self.bot))
        self.bot.add_view(ReplyView(self.bot))

    async def send_log(self, guild_id, title, description, color=discord.Color.red()):
        config = load_config()
        guild_id_str = str(guild_id)
        
        if guild_id_str not in config or "log_channel_id" not in config[guild_id_str]:
            return

        try:
            log_channel_id = config[guild_id_str]["log_channel_id"]
            channel = self.bot.get_channel(log_channel_id) or await self.bot.fetch_channel(log_channel_id)
            embed = discord.Embed(title=title, description=description, color=color, timestamp=discord.utils.utcnow())
            await channel.send(embed=embed)
        except Exception as e:
            print(f"[LOG ERROR] {e}")

    @app_commands.command(name="cfs_setup", description="Cấu hình kênh Confession và kênh Log hệ thống (Chỉ Admin)")
    @app_commands.describe(kenh_cfs="Kênh hiển thị Panel và đăng các bài Confession", kenh_log="Kênh riêng tư để Admin nhận Log")
    @app_commands.checks.has_permissions(administrator=True)
    async def cfs_setup(self, interaction: discord.Interaction, kenh_cfs: discord.TextChannel, kenh_log: discord.TextChannel):
        await interaction.response.defer(ephemeral=True)
        
        guild_id_str = str(interaction.guild_id)
        config = load_config()
        
        config[guild_id_str] = {
            "confession_channel_id": kenh_cfs.id,
            "log_channel_id": kenh_log.id
        }
        save_config(config)
        
        try:
            async for message in kenh_cfs.history(limit=20):
                if message.author.id == self.bot.user.id and message.embeds:
                    if message.embeds[0].title == t(interaction.guild, "CFS_PANEL_TITLE"):
                        await message.delete()

            embed = create_panel_embed(interaction.guild)
            await kenh_cfs.send(embed=embed, view=CreateConfessionView(self.bot))
            
            await interaction.followup.send(
                t(interaction.guild, "CFS_SETUP_SUCCESS", mention_cfs=kenh_cfs.mention, mention_log=kenh_log.mention), 
                ephemeral=True
            )
        except Exception as e:
            await interaction.followup.send(t(interaction.guild, "CFS_SETUP_ERROR", error=e), ephemeral=True)

    @cfs_setup.error
    async def cfs_setup_error(self, interaction: discord.Interaction, error: app_commands.AppCommandError):
        if isinstance(error, app_commands.errors.MissingPermissions):
            await interaction.response.send_message(t(interaction.guild, "CFS_NEED_ADMIN"), ephemeral=True)


class ConfessionModal(discord.ui.Modal):
    def __init__(self, bot: commands.Bot, anonymous: bool, guild=None):
        title = t(guild, "CFS_MODAL_TITLE_ANON") if anonymous else t(guild, "CFS_MODAL_TITLE_PUBLIC")
        super().__init__(title=title)
        self.bot = bot
        self.anonymous = anonymous
        self.guild_ref = guild

        self.content = discord.ui.TextInput(
            label=t(guild, "CFS_MODAL_LABEL"),
            style=discord.TextStyle.paragraph,
            placeholder=t(guild, "CFS_MODAL_PLACEHOLDER"),
            max_length=4000,
            required=True
        )
        self.add_item(self.content)

    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)

        guild_id_str = str(interaction.guild_id)
        gc=get_guild_confession(guild_id_str)
        if not gc.get("enabled", True):
            await interaction.followup.send("❌ Confession đang tắt trong cài đặt.", ephemeral=True)
            return
        # kiểm tra quyền theo loại
        if self.anonymous and not gc.get("allow_anonymous", True):
            await interaction.followup.send("❌ Gửi Ẩn danh đang bị tắt.", ephemeral=True)
            return
        if not self.anonymous and not gc.get("allow_public", True):
            await interaction.followup.send("❌ Gửi Công khai đang bị tắt.", ephemeral=True)
            return
        config = load_config()
        if guild_id_str not in config or not config[guild_id_str].get("confession_channel_id"):
            await interaction.followup.send(t(interaction.guild, "CFS_NOT_SETUP"), ephemeral=True)
            return

        cfs_number = get_and_increment_cfs_number()
        cfs_title = t(interaction.guild, "CFS_ROOM_TITLE", number=cfs_number)
        channel = interaction.channel

        try:
            if interaction.message:
                try: await interaction.message.delete()
                except discord.NotFound: pass

            embed_cfs = discord.Embed(
                title=f"💌 {cfs_title}",
                description=f"{self.content.value}",
                color=0x2F3136,
                timestamp=discord.utils.utcnow()
            )
            if self.anonymous:
                embed_cfs.set_footer(text=t(interaction.guild, "CFS_FOOTER_ANON"))
            else:
                embed_cfs.set_footer(text=t(interaction.guild, "CFS_FOOTER_PUBLIC", name=interaction.user.display_name))

            # quyết định view trả lời theo anon_reply
            reply_view = ReplyView(self.bot, guild=interaction.guild) if gc.get("anon_reply", True) else None
            cfs_message = await channel.send(embed=embed_cfs, view=reply_view)

            if gc.get("create_thread", True):
                try:
                    await cfs_message.create_thread(
                        name=t(interaction.guild, "CFS_THREAD_NAME", title=cfs_title),
                        auto_archive_duration=1440
                    )
                except Exception as e:
                    print(f"[CFS] create_thread fail: {e}")

            new_panel_embed = create_panel_embed(interaction.guild)
            # panel mới cũng tôn trọng allow flags
            panel_view = CreateConfessionView(self.bot, guild=interaction.guild)
            if not gc.get("allow_anonymous", True):
                for ch in list(panel_view.children):
                    if getattr(ch,'custom_id','')=='cfs_anonymous': panel_view.remove_item(ch)
            if not gc.get("allow_public", True):
                for ch in list(panel_view.children):
                    if getattr(ch,'custom_id','')=='cfs_public': panel_view.remove_item(ch)
            if len(panel_view.children)>0:
                await channel.send(embed=new_panel_embed, view=panel_view)

            await interaction.followup.send(t(interaction.guild, "CFS_POSTED"), ephemeral=True)
            
            cog = self.bot.get_cog("ConfessionCog")
            if cog:
                await cog.send_log(
                    guild_id=interaction.guild_id,
                    title=t(interaction.guild, "CFS_LOG_TITLE", title=cfs_title),
                    description=t(interaction.guild, "CFS_LOG_DESC", mention=interaction.user.mention, content=self.content.value),
                    color=discord.Color.green()
                )
        except Exception as e:
            await interaction.followup.send(t(interaction.guild, "CFS_POST_ERROR"), ephemeral=True)
            traceback.print_exc()


class CreateConfessionView(discord.ui.View):
    def __init__(self, bot: commands.Bot, guild=None):
        super().__init__(timeout=None)
        self.bot = bot
        self.guild = guild
        if guild:
            vi = is_vietnamese(guild)
            self.anonymous.label = "Gửi Ẩn Danh" if vi else "Send Anonymously"
            self.public.label = "Gửi Công Khai" if vi else "Send Publicly" 

    @discord.ui.button(label="Gửi Ẩn Danh", emoji="💌", style=discord.ButtonStyle.secondary, custom_id="cfs_anonymous")
    async def anonymous(self, interaction: discord.Interaction, button: discord.ui.Button):
        gc=get_guild_confession(interaction.guild_id)
        if not gc.get("enabled", True): return await interaction.response.send_message("❌ Confession đang tắt.", ephemeral=True)
        if not gc.get("allow_anonymous", True): return await interaction.response.send_message("❌ Ẩn danh đang tắt.", ephemeral=True)
        await interaction.response.send_modal(ConfessionModal(self.bot, anonymous=True, guild=interaction.guild))

    @discord.ui.button(label="Gửi Công Khai", emoji="📢", style=discord.ButtonStyle.primary, custom_id="cfs_public")
    async def public(self, interaction: discord.Interaction, button: discord.ui.Button):
        gc=get_guild_confession(interaction.guild_id)
        if not gc.get("enabled", True): return await interaction.response.send_message("❌ Confession đang tắt.", ephemeral=True)
        if not gc.get("allow_public", True): return await interaction.response.send_message("❌ Công khai đang tắt.", ephemeral=True)
        await interaction.response.send_modal(ConfessionModal(self.bot, anonymous=False, guild=interaction.guild))


class ReplyModal(discord.ui.Modal, title="Bình luận ẩn danh"):
    def __init__(self, bot: commands.Bot, guild=None):
        title = t(guild, "CFS_REPLY_MODAL_TITLE") if guild else "Bình luận ẩn danh"
        super().__init__(title=title)
        self.bot = bot
        self.guild_ref = guild
        try:
            self.content.label = t(guild, "CFS_REPLY_LABEL")
        except:
            pass

    content = discord.ui.TextInput(
        label="🌸 Nội dung bình luận", style=discord.TextStyle.paragraph, max_length=2000, required=True
    )

    async def on_submit(self, interaction: discord.Interaction):
        gc=get_guild_confession(interaction.guild_id)
        if not gc.get("anon_reply", True):
            return await interaction.response.send_message("❌ Trả lời ẩn danh đang tắt.", ephemeral=True)
        thread = interaction.message.thread
        if not thread:
            # nếu không tạo thread mà vẫn bấm reply (view cũ) -> gửi thẳng vào kênh
            thread = interaction.channel
            if gc.get("create_thread", True):
                return await interaction.response.send_message(t(interaction.guild, "CFS_REPLY_NO_THREAD"), ephemeral=True)

        embed = discord.Embed(description=self.content.value, color=0x2b2d31, timestamp=discord.utils.utcnow())
        embed.set_author(name=t(interaction.guild, "CFS_REPLY_AUTHOR"), icon_url="https://cdn.discordapp.com/embed/avatars/0.png")
        
        await thread.send(embed=embed)
        await interaction.response.send_message(t(interaction.guild, "CFS_REPLY_SENT"), ephemeral=True)

        cog = self.bot.get_cog("ConfessionCog")
        if cog:
            await cog.send_log(
                guild_id=interaction.guild_id,
                title=t(interaction.guild, "CFS_REPLY_LOG_TITLE"),
                description=t(interaction.guild, "CFS_REPLY_LOG_DESC", mention=interaction.user.mention, content=self.content.value),
                color=discord.Color.yellow()
            )

class ReplyView(discord.ui.View):
    def __init__(self, bot: commands.Bot, guild=None):
        super().__init__(timeout=None)
        self.bot = bot
        self.guild = guild
        if guild:
            vi = is_vietnamese(guild)
            self.reply.label = "Trả lời ẩn danh" if vi else "Reply Anonymously" 

    @discord.ui.button(label="Trả lời ẩn danh", emoji="💬", style=discord.ButtonStyle.secondary, custom_id="cfs_reply_in_thread")
    async def reply(self, interaction: discord.Interaction, button: discord.ui.Button):
        gc=get_guild_confession(interaction.guild_id)
        if not gc.get("anon_reply", True):
            return await interaction.response.send_message("❌ Trả lời ẩn danh đang tắt.", ephemeral=True)
        await interaction.response.send_modal(ReplyModal(self.bot, guild=interaction.guild))


async def setup(bot: commands.Bot):
    await bot.add_cog(ConfessionCog(bot))
