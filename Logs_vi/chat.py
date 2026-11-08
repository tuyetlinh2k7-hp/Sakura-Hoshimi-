import discord
from discord.ext import commands
from Checks_vi.data import chat_log_channels
from Checks_vi.i18n import t

class ChatLog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if message.author.bot:
            return
        if not message.guild:
            return
        
        guild_id = str(message.guild.id)

        if guild_id in chat_log_channels:

            log_channel = message.guild.get_channel(
                chat_log_channels[guild_id]
            )

            if log_channel:

                embed = discord.Embed(
                    title=t(message.guild, "LOG_CHAT_TITLE"),
                    color=discord.Color.blue(),
                    timestamp=discord.utils.utcnow()
                )

                embed.add_field(
                    name=t(message.guild, "LOG_CHAT_FIELD_USER"),
                    value=message.author.mention,
                    inline=False
                )

                embed.add_field(
                    name=t(message.guild, "LOG_CHAT_FIELD_CHANNEL"),
                    value=message.channel.mention,
                    inline=False
                )

                embed.add_field(
                    name=t(message.guild, "LOG_CHAT_FIELD_LINK"),
                    value=f"[Jump to Message]({message.jump_url})",
                    inline=False
                )

                content = (
                    message.content[:1000]
                    if message.content
                    else t(message.guild, "LOG_CHAT_NO_CONTENT")
                )

                embed.add_field(
                    name=t(message.guild, "LOG_CHAT_FIELD_CONTENT"),
                    value=content,
                    inline=False
                )

                if message.attachments:

                    files_text = ""
                    for attachment in message.attachments:
                        files_text += f"[{attachment.filename}]({attachment.url})\n"

                    embed.add_field(
                        name=t(message.guild, "LOG_CHAT_FIELD_ATTACHMENTS"),
                        value=files_text[:1000],
                        inline=False
                    )

                    first_attachment = message.attachments[0]
                    image_extensions = (".png", ".jpg", ".jpeg", ".gif", ".webp")
                    if first_attachment.filename.lower().endswith(image_extensions):
                        embed.set_image(
                            url=first_attachment.url
                        )

                embed.set_footer(
                    text=t(message.guild, "LOG_CHAT_FOOTER", id=message.author.id)
                )

                await log_channel.send(
                    embed=embed
                )

async def setup(bot: commands.Bot):
    await bot.add_cog(ChatLog(bot))
