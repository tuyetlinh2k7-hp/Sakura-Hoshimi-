import discord

temp_channels = {}
banned_members = {}

async def check_owner(interaction: discord.Interaction):

    if interaction.user.voice is None:
        await interaction.response.send_message(
            "❌ Bạn chưa ở voice.",
            ephemeral=True
        )
        return None

    channel = interaction.user.voice.channel

    if temp_channels.get(channel.id) != interaction.user.id:
        await interaction.response.send_message(
            "❌ Bạn không phải chủ phòng.",
            ephemeral=True
        )
        return None

    return channel