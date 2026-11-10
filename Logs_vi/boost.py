import discord
from discord.ext import commands
from Check.data import get_guild_settings
from Check.i18n import t

class BoostLog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_member_update(self, before: discord.Member, after: discord.Member):
        settings = get_guild_settings(after.guild.id)

        if not settings.get("boost_message", True):
            return

        if before.premium_since is None and after.premium_since is not None:
            channel_id = settings.get("boost_channel")
            channel = after.guild.get_channel(channel_id) if channel_id else after.guild.system_channel

            if not channel:
                for ch in after.guild.text_channels:
                    if ch.permissions_for(after.guild.me).send_messages:
                        channel = ch
                        break

            if not channel:
                return

            custom_msg = settings.get("boost_message_text") or ""
            if custom_msg:
                description = custom_msg.replace("{user}", after.mention).replace("{mention}", after.mention).replace("{user_name}", after.display_name).replace("{server}", after.guild.name).replace("{guild_name}", after.guild.name)
                content = None
            else:
                description = t(after.guild, "LOG_BOOST_DESC", mention=after.mention, guild_name=after.guild.name)
                content = t(after.guild, "LOG_BOOST_CONTENT", mention=after.mention)

            embed = discord.Embed(
                title=t(after.guild, "LOG_BOOST_TITLE"),
                description=description,
                color=discord.Color.nitro_pink()
            )
            embed.set_thumbnail(url=after.display_avatar.url)
            if custom_msg:
                embed.set_footer(text=t(after.guild, "LOG_BOOST_FOOTER"))
            else:
                embed.set_image(url="https://i.pinimg.com/originals/41/d2/a8/41d2a863f7199b73b533723c343a4b93.gif")
                embed.set_footer(text=t(after.guild, "LOG_BOOST_FOOTER"))
            embed.timestamp = discord.utils.utcnow()

            # Kiểm tra quyền hạn bot
            bot_member = after.guild.me
            if bot_member:
                perms = channel.permissions_for(bot_member)
                if not perms.view_channel or not perms.send_messages:
                    return

            try:
                await channel.send(content=content, embed=embed)
            except (discord.Forbidden, discord.HTTPException) as e:
                print(f"[BoostLog] Không thể gửi log boost tại #{channel.name}: {e}")

async def setup(bot: commands.Bot):
    await bot.add_cog(BoostLog(bot))
