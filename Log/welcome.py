import discord
from discord.ext import commands
import os
from Check.server_member import update_stats
from Check.data import get_guild_settings
from Check.i18n import t


class WelcomeLog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_member_join(self, member: discord.Member):
        settings = get_guild_settings(member.guild.id)

        if not settings or not settings.get("welcome", True):
            return

        channel_id = settings.get("welcome_channel")
        channel = member.guild.get_channel(channel_id) if channel_id else member.guild.system_channel

        if not channel:
            return

        bot_member = member.guild.me
        if not bot_member:
            return

        perms = channel.permissions_for(bot_member)
        if not perms.view_channel or not perms.send_messages:
            print(f"[WelcomeLog] 403 Forbidden: Bot thiếu quyền xem hoặc gửi tin nhắn vào #{channel.name} ({channel.id}) tại {member.guild.name}")
            try:
                await update_stats(member.guild)
            except Exception:
                pass
            return

        account_age = discord.utils.utcnow() - member.created_at
        if account_age.days > 0:
            age_str = t(member.guild, "LOG_WELCOME_AGE_DAYS", days=account_age.days)
        else:
            hours, remainder = divmod(account_age.seconds, 3600)
            minutes, _ = divmod(remainder, 60)
            age_str = t(member.guild, "LOG_WELCOME_AGE_HOURS", hours=hours, minutes=minutes)

        custom_msg = settings.get("welcome")
        if not isinstance(custom_msg, str):
            custom_msg = ""
        custom_img = settings.get("welcome_image")
        if not isinstance(custom_img, str):
            custom_img = ""

        if custom_msg:
            desc = custom_msg.replace("{user}", str(member.mention)).replace("{server}", member.guild.name).replace("{user_name}", member.display_name)
        else:
            desc = t(member.guild, "LOG_WELCOME_DESC", mention=member.mention, guild=member.guild.name)
        embed = discord.Embed(
            title=t(member.guild, "LOG_WELCOME_TITLE"),
            description=desc,
            color=discord.Color.random(),
            timestamp=member.joined_at
        )
        embed.set_thumbnail(url=member.display_avatar.url)
        img_url = custom_img if custom_img.startswith("http") else "https://giffiles.alphacoders.com/484/48409.gif"
        embed.set_image(url=img_url)
        embed.add_field(name=t(member.guild, "LOG_WELCOME_FIELD_TOTAL"), value=f"`{member.guild.member_count}`", inline=True)
        embed.add_field(name=t(member.guild, "LOG_WELCOME_FIELD_AGE"), value=f"`{age_str}`", inline=True)
        embed.set_footer(text=t(member.guild, "LOG_WELCOME_FOOTER", id=member.id))

        content = t(member.guild, "LOG_WELCOME_CONTENT", mention=member.mention)
        if custom_msg and "{user}" in custom_msg:
            content = None

        try:
            if perms.embed_links:
                await channel.send(content=content, embed=embed)
            else:
                plain_text = f"{content or ''}\n\n🎉 **{member.display_name}** vừa tham gia {member.guild.name}!\nThành viên thứ: `{member.guild.member_count}`\nTuổi tài khoản: `{age_str}`".strip()
                await channel.send(content=plain_text)
        except (discord.Forbidden, discord.HTTPException) as e:
            print(f"[WelcomeLog] Không thể gửi tin nhắn chào mừng tại #{channel.name} ({channel.id}): {e}")
        finally:
            try:
                await update_stats(member.guild)
            except Exception as e:
                print(f"[WelcomeLog] Lỗi cập nhật stats server: {e}")

async def setup(bot: commands.Bot):
    await bot.add_cog(WelcomeLog(bot))
