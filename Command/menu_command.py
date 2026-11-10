import discord
from discord.ext import commands
from discord import app_commands
from typing import Optional
from config import OWNER_ID
from Check.i18n import t

def is_guild_admin(member: discord.abc.User, guild: Optional[discord.Guild]) -> bool:
    if not guild or not isinstance(member, discord.Member):
        return False
    if member.id == OWNER_ID:
        return True
    if member.guild_permissions.administrator or member.guild_permissions.manage_guild:
        return True
    from Check.mod import has_admin_role
    return has_admin_role(member)


class MenuSelect(discord.ui.Select):
    def __init__(self, bot: commands.Bot, author: discord.abc.User, guild: Optional[discord.Guild], prefix: str):
        self.bot = bot
        self.author = author
        self.guild = guild
        self.prefix = prefix

        options = [
            discord.SelectOption(
                label=t(guild, "MENU_SELECT_BASIC_LABEL"),
                description=t(guild, "MENU_SELECT_BASIC_DESC"),
                value="basic",
                emoji="✨"
            ),
            discord.SelectOption(
                label=t(guild, "MENU_SELECT_FUN_LABEL"),
                description=t(guild, "MENU_SELECT_FUN_DESC"),
                value="fun",
                emoji="🎮"
            ),
            discord.SelectOption(
                label=t(guild, "MENU_SELECT_UTILITY_LABEL"),
                description=t(guild, "MENU_SELECT_UTILITY_DESC"),
                value="utility",
                emoji="🛠️"
            ),
            discord.SelectOption(
                label=t(guild, "MENU_SELECT_GAME_LABEL"),
                description=t(guild, "MENU_SELECT_GAME_DESC"),
                value="game",
                emoji="🎲"
            ),
            discord.SelectOption(
                label=t(guild, "MENU_SELECT_FISHING_LABEL"),
                description=t(guild, "MENU_SELECT_FISHING_DESC"),
                value="fishing",
                emoji="🎣"
            ),
            discord.SelectOption(
                label=t(guild, "MENU_SELECT_MINING_LABEL"),
                description=t(guild, "MENU_SELECT_MINING_DESC"),
                value="mining",
                emoji="⛏️"
            ),
            discord.SelectOption(
                label=t(guild, "MENU_SELECT_FARM_LABEL"),
                description=t(guild, "MENU_SELECT_FARM_DESC"),
                value="farm",
                emoji="🌾"
            ),
            discord.SelectOption(
                label=t(guild, "MENU_SELECT_MARRIAGE_LABEL"),
                description=t(guild, "MENU_SELECT_MARRIAGE_DESC"),
                value="marriage",
                emoji="💍"
            ),
            discord.SelectOption(
                label=t(guild, "MENU_SELECT_ACHIEVEMENTS_LABEL"),
                description=t(guild, "MENU_SELECT_ACHIEVEMENTS_DESC"),
                value="achievements",
                emoji="🏆"
            ),
            discord.SelectOption(
                label=t(guild, "MENU_SELECT_CASINO_LABEL"),
                description=t(guild, "MENU_SELECT_CASINO_DESC"),
                value="casino",
                emoji="🎰"
            ),
            discord.SelectOption(
                label=t(guild, "MENU_SELECT_TTS_LABEL"),
                description=t(guild, "MENU_SELECT_TTS_DESC"),
                value="tts",
                emoji="🔊"
            ),
            discord.SelectOption(
                label=t(guild, "MENU_SELECT_MUSIC_LABEL"),
                description=t(guild, "MENU_SELECT_MUSIC_DESC"),
                value="music",
                emoji="🎵"
            ),
        ]

        if is_guild_admin(author, guild):
            options.extend([
                discord.SelectOption(
                    label=t(guild, "MENU_SELECT_MOD_LABEL"),
                    description=t(guild, "MENU_SELECT_MOD_DESC"),
                    value="mod",
                    emoji="🛡️"
                ),
                discord.SelectOption(
                    label=t(guild, "MENU_SELECT_ANTI_LABEL"),
                    description=t(guild, "MENU_SELECT_ANTI_DESC"),
                    value="anti",
                    emoji="⚔️"
                ),
                discord.SelectOption(
                    label=t(guild, "MENU_SELECT_LOGS_LABEL"),
                    description=t(guild, "MENU_SELECT_LOGS_DESC"),
                    value="logs",
                    emoji="📜"
                ),
            ])

        if author.id == OWNER_ID:
            options.append(
                discord.SelectOption(
                    label=t(guild, "MENU_SELECT_OWNER_LABEL"),
                    description=t(guild, "MENU_SELECT_OWNER_DESC"),
                    value="owner",
                    emoji="👑"
                )
            )

        super().__init__(
            placeholder=t(guild, "MENU_PLACEHOLDER"),
            min_values=1,
            max_values=1,
            options=options,
            row=0
        )

    async def callback(self, interaction: discord.Interaction):
        category = self.values[0]
        guild = interaction.guild
        p = self.prefix

        for opt in self.options:
            opt.default = (opt.value == category)

        embed = discord.Embed(color=discord.Color.from_rgb(255, 182, 193))
        if self.bot.user and self.bot.user.display_avatar:
            embed.set_thumbnail(url=self.bot.user.display_avatar.url)

        # 1. BASIC
        if category == "basic":
            embed.title = t(guild, "MENU_BASIC_TITLE")
            commands_list = [
                f"**{t(guild, 'MENU_SEC_CORE')}:**",
                f"• `{p}ping` — {t(guild, 'MENU_CMD_PING')}",
                f"• `{p}hello` / `{p}bye` — {t(guild, 'MENU_CMD_HELLO')}",
                f"• `{p}help` / `{p}menu` — {t(guild, 'MENU_CMD_HELP')}",
                f"• `/setlanguage <vi|en>` (`{p}setlanguage`, `{p}ngonngu`) — {t(guild, 'MENU_CMD_SETLANG')}",
                f"• `{p}mylang` — {t(guild, 'MENU_CMD_MYLANG')}",
                f"• `{p}botinfo` / `{p}uptime` — {t(guild, 'MENU_CMD_BOTINFO')}",
                "",
                f"**{t(guild, 'MENU_SEC_ECONOMY')}:**",
                f"• `/leveling rank [@user]` (`{p}rank`, `{p}xp`, `{p}level`) — {t(guild, 'MENU_CMD_RANK')}",
                f"• `/leveling balance [@user]` (`{p}bal`, `{p}balance`, `{p}money`) — {t(guild, 'MENU_CMD_BALANCE')}",
                f"• `/leveling daily` (`{p}daily`) — {t(guild, 'MENU_CMD_DAILY')}",
                f"• `/leveling top` (`{p}lb`, `{p}top`, `{p}leaderboard`) — {t(guild, 'MENU_CMD_TOP')}",
                f"• `{p}streak` — {t(guild, 'MENU_CMD_STREAK')}",
                f"• `{p}bank` / `{p}deposit` / `{p}withdraw` — {t(guild, 'MENU_CMD_BANK')}",
                f"• `{p}work` / `{p}crime` / `{p}rob` — {t(guild, 'MENU_CMD_WORK')}",
            ]
            embed.description = "\n".join(commands_list)

        # 2. FUN
        elif category == "fun":
            embed.title = t(guild, "MENU_FUN_TITLE")
            commands_list = [
                f"**{t(guild, 'MENU_SEC_ANIME')}:**",
                f"• `/anime action:anime query:<tên>` (`{p}anime <tên>`) — {t(guild, 'MENU_CMD_ANIME')}",
                f"• `/anime action:manga query:<tên>` (`{p}manga <tên>`) — {t(guild, 'MENU_CMD_MANGA')}",
                f"• `/anime action:random` (`{p}randomanime`) — {t(guild, 'MENU_CMD_RANDOMANIME')}",
                f"• `/anime action:waifu` / `action:neko` (`{p}waifu`, `{p}neko`) — {t(guild, 'MENU_CMD_WAIFU')}",
                f"• `/anime action:image query:<từ_khóa>` (`{p}image`) — {t(guild, 'MENU_CMD_IMAGE')}",
                "",
                f"**{t(guild, 'MENU_SEC_FORTUNE')}:**",
                f"• `{p}action <hành_động> [@user]` — {t(guild, 'MENU_CMD_ACTION')}",
                f"• `{p}tarot` — {t(guild, 'MENU_CMD_TAROT')}",
                f"• `{p}xemboi <câu_hỏi>` — {t(guild, 'MENU_CMD_XEMBOI')}",
                f"• `{p}quest <câu_hỏi>` — {t(guild, 'MENU_CMD_QUEST')}",
                f"• `{p}zodiac <ngày> <tháng>` — {t(guild, 'MENU_CMD_ZODIAC')}",
                f"• `{p}rate <chỉ_số>` — {t(guild, 'MENU_CMD_RATE')}",
                "",
                f"**{t(guild, 'MENU_SEC_MINIGAMES')}:**",
                f"• `{p}meme` — {t(guild, 'MENU_CMD_MEME')}",
                f"• `{p}wordchain` — {t(guild, 'MENU_CMD_WORDCHAIN')}",
                f"• `{p}altp` — {t(guild, 'MENU_CMD_ALTP')}",
            ]
            embed.description = "\n".join(commands_list)

        # 3. UTILITY
        elif category == "utility":
            embed.title = t(guild, "MENU_UTILITY_TITLE")
            commands_list = [
                f"• `{p}userinfo [@user]` — {t(guild, 'MENU_CMD_USERINFO')}",
                f"• `{p}serverinfo` — {t(guild, 'MENU_CMD_SERVERINFO')}",
                f"• `{p}avatar [@user]` — {t(guild, 'MENU_CMD_AVATAR')}",
                f"• `{p}afk [lý_do]` — {t(guild, 'MENU_CMD_AFK')}",
                f"• `{p}qr <nội_dung/link>` — {t(guild, 'MENU_CMD_QR')}",
                f"• `/translate` (`{p}translate`) — {t(guild, 'MENU_CMD_TRANSLATE')}",
                f"• `{p}ids` — {t(guild, 'MENU_CMD_IDS')}",
                f"• `{p}vote` — {t(guild, 'MENU_CMD_VOTE')}",
                f"• `{p}support <nội_dung>` — {t(guild, 'MENU_CMD_SUPPORT')}",
                f"• `{p}invite` — {t(guild, 'MENU_CMD_INVITE')}",
            ]
            embed.description = "\n".join(commands_list)

        # 4. GAME LOOKUP
        elif category == "game":
            embed.title = t(guild, "MENU_GAME_TITLE")
            commands_list = [
                f"**{t(guild, 'MENU_SEC_HOYO')}:**",
                f"• `{p}enka gi <UID/tên>` / `build <UID> <nhân_vật>` — {t(guild, 'MENU_CMD_ENKA_GI')}",
                f"• `{p}enka hsr <UID/tên>` / `build <UID> <nhân_vật>` — {t(guild, 'MENU_CMD_ENKA_HSR')}",
                f"• `{p}enka zzz <UID/tên>` / `build <UID> <agent>` — {t(guild, 'MENU_CMD_ENKA_ZZZ')}",
                f"• `{p}enka save <gi|hsr|zzz> <tên> <UID>` — {t(guild, 'MENU_CMD_ENKA_SAVE')}",
                f"• `{p}akasha <UID>` — {t(guild, 'MENU_CMD_AKASHA')}",
                f"• `{p}gi abyss` — {t(guild, 'MENU_CMD_GI_ABYSS')}",
                f"• `/hoyolab manage` — {t(guild, 'MENU_CMD_HOYOLAB')}",
                "",
                f"**{t(guild, 'MENU_SEC_MC')}:**",
                f"• `{p}mc status` / `{p}mc list` — {t(guild, 'MENU_CMD_MC_STATUS')}",
                f"• `{p}link` — {t(guild, 'MENU_CMD_MC_LINK')}",
            ]
            embed.description = "\n".join(commands_list)

        # 5. OCEAN FISHING (Names of fish stay in Vietnamese)
        elif category == "fishing":
            embed.title = t(guild, "MENU_FISHING_TITLE")
            commands_list = [
                f"**{t(guild, 'MENU_SEC_FISHING_CATCH')}:**",
                f"• `/fishing cast` (`{p}f`, `{p}fish`, `{p}fcast`) — {t(guild, 'MENU_CMD_FISHING_CAST')}",
                f"• `/fishing inv` (`{p}inv`, `{p}tuido`, `{p}gio`) — {t(guild, 'MENU_CMD_FISHING_INV')}",
                f"• `/fishing shop` (`{p}fshop`, `{p}shop`) — {t(guild, 'MENU_CMD_FISHING_SHOP')}",
                f"• `/fishing sell [loại]` (`{p}sell`) — {t(guild, 'MENU_CMD_FISHING_SELL')}",
                f"• `/fishing upgrade` (`{p}rodup`, `{p}cuonghoa`) — {t(guild, 'MENU_CMD_FISHING_UPGRADE')}",
                f"• `/fishing repair` — {t(guild, 'MENU_CMD_FISHING_REPAIR')}",
                f"• `/fishing license` (`{p}fcard`, `{p}license`) — {t(guild, 'MENU_CMD_FISHING_CARD')}",
                "",
                f"**{t(guild, 'MENU_SEC_FISHING_MUSEUM')}:**",
                f"• `/fishing aquarium` (`{p}faqua`, `{p}thuycung`, `{p}baotang`) — {t(guild, 'MENU_CMD_FISHING_AQUA')}",
                f"• `/fishing cook` (`{p}fcook`, `{p}bep`, `{p}nauan`) — {t(guild, 'MENU_CMD_FISHING_COOK')}",
                f"• `/fishing fishdex` (`{p}fdex`, `{p}fishdex`, `{p}sotay`) — {t(guild, 'MENU_CMD_FISHING_DEX')}",
                f"• `/fishing chest [id]` (`{p}ruong`, `{p}fchest`) — {t(guild, 'MENU_CMD_FISHING_CHEST')}",
                "",
                f"**{t(guild, 'MENU_SEC_FISHING_MARKET')}:**",
                f"• `/fishing market` (`{p}fchungkhoan`, `{p}ck`) — {t(guild, 'MENU_CMD_FISHING_MARKET')}",
                f"• `/fishing weather` — {t(guild, 'MENU_CMD_FISHING_WEATHER')}",
                f"• `/fishing tournament` (`{p}ftour`, `{p}giaidau`) — {t(guild, 'MENU_CMD_FISHING_TOUR')}",
                f"• `/fishing top` — {t(guild, 'MENU_CMD_FISHING_TOP')}",
            ]
            embed.description = "\n".join(commands_list)

        # 6. MINING (Names of minerals stay in Vietnamese)
        elif category == "mining":
            embed.title = t(guild, "MENU_MINING_TITLE")
            commands_list = [
                f"**{t(guild, 'MENU_SEC_MINING')}:**",
                f"• `{p}mine` (`{p}daokhoang`) — {t(guild, 'MENU_CMD_MINING_MINE')}",
                f"• `{p}minv` (`{p}khoangsan`) — {t(guild, 'MENU_CMD_MINING_INV')}",
                f"• `{p}mshop` (`{p}cuahangcuoc`) — {t(guild, 'MENU_CMD_MINING_SHOP')}",
                f"• `{p}msell [loại/all]` — {t(guild, 'MENU_CMD_MINING_SELL')}",
                f"• `{p}mup` (`{p}cuonghoacuoc`) — {t(guild, 'MENU_CMD_MINING_UPGRADE')}",
            ]
            embed.description = "\n".join(commands_list)

        # 7. FARM
        elif category == "farm":
            embed.title = t(guild, "MENU_FARM_TITLE")
            commands_list = [
                f"**{t(guild, 'MENU_SEC_FARM')}:**",
                f"• `{p}farm` (`{p}nongtrai`) — {t(guild, 'MENU_CMD_FARM_MAIN')}",
                f"• `{p}plant <hạt_giống>` — {t(guild, 'MENU_CMD_FARM_PLANT')}",
                f"• `{p}water` (`{p}tuoinuoc`) — {t(guild, 'MENU_CMD_FARM_WATER')}",
                f"• `{p}harvest` (`{p}thuhoach`) — {t(guild, 'MENU_CMD_FARM_HARVEST')}",
                f"• `{p}fshop` (`{p}cuahangnongsan`) — {t(guild, 'MENU_CMD_FARM_SHOP')}",
            ]
            embed.description = "\n".join(commands_list)

        # 8. MARRIAGE
        elif category == "marriage":
            embed.title = t(guild, "MENU_MARRIAGE_TITLE")
            commands_list = [
                f"**{t(guild, 'MENU_SEC_MARRIAGE')}:**",
                f"• `{p}marry <@user>` — {t(guild, 'MENU_CMD_MARRY_PROPOSE')}",
                f"• `{p}couple [@user]` — {t(guild, 'MENU_CMD_MARRY_COUPLE')}",
                f"• `{p}divorce` — {t(guild, 'MENU_CMD_MARRY_DIVORCE')}",
                f"• `{p}gift <@user> <vật_phẩm>` — {t(guild, 'MENU_CMD_MARRY_GIFT')}",
                f"• `{p}topcouple` — {t(guild, 'MENU_CMD_MARRY_TOP')}",
            ]
            embed.description = "\n".join(commands_list)

        # 9. ACHIEVEMENTS
        elif category == "achievements":
            embed.title = t(guild, "MENU_ACHIEVEMENTS_TITLE")
            commands_list = [
                f"**{t(guild, 'MENU_SEC_ACHIEVEMENTS')}:**",
                f"• `{p}achievements` (`{p}ach`, `{p}thanhtuu`) — {t(guild, 'MENU_CMD_ACHIEVEMENTS_LIST')}",
                f"• `{p}achievements top` (`{p}achtop`, `{p}bxhthanhtuu`) — {t(guild, 'MENU_CMD_ACHIEVEMENTS_LB')}",
            ]
            embed.description = "\n".join(commands_list)

        # 10. CASINO
        elif category == "casino":
            embed.title = t(guild, "MENU_CASINO_TITLE")
            commands_list = [
                f"**{t(guild, 'MENU_SEC_CASINO')}:**",
                f"• `{p}coinflip <head|tail> <tiền>` (`{p}cf`) — {t(guild, 'MENU_CMD_CASINO_COINFLIP')}",
                f"• `{p}slots <tiền>` — {t(guild, 'MENU_CMD_CASINO_SLOTS')}",
                f"• `{p}baucua <cửa> <tiền>` — {t(guild, 'MENU_CMD_CASINO_BAUCUA')}",
                f"• `{p}blackjack <tiền>` (`{p}bj`) — {t(guild, 'MENU_CMD_CASINO_BJ')}",
                f"• `{p}roulette <cửa> <tiền>` — {t(guild, 'MENU_CMD_CASINO_ROULETTE')}",
            ]
            embed.description = "\n".join(commands_list)

        # 11. TTS
        elif category == "tts":
            embed.title = t(guild, "MENU_TTS_TITLE")
            commands_list = [
                f"• `{p}tts on` — {t(guild, 'MENU_CMD_TTS_ON')}",
                f"• `{p}tts off` — {t(guild, 'MENU_CMD_TTS_OFF')}",
                f"• `{p}tts skip` — {t(guild, 'MENU_CMD_TTS_SKIP')}",
                f"• `{p}tts clear` — {t(guild, 'MENU_CMD_TTS_CLEAR')}",
                f"• `{p}tts status` — {t(guild, 'MENU_CMD_TTS_STATUS')}",
                f"• `{p}tts vol <0-100>` — {t(guild, 'MENU_CMD_TTS_VOL')}",
                f"• `{p}tts lang <mã>` — {t(guild, 'MENU_CMD_TTS_LANG')}",
            ]
            embed.description = "\n".join(commands_list)

        # 12. MUSIC
        elif category == "music":
            embed.title = t(guild, "MENU_MUSIC_TITLE")
            commands_list = [
                f"**{t(guild, 'MENU_SEC_MUSIC')}:**",
                f"• `/music panel` (`{p}m`) — {t(guild, 'MENU_CMD_MUSIC_PANEL')}",
                f"• `/music play <tên/url>` (`{p}play`, `{p}p`) — {t(guild, 'MENU_CMD_MUSIC_PLAY')}",
                f"• `/music skip [số_lượng]` (`{p}skip`, `{p}s`) — {t(guild, 'MENU_CMD_MUSIC_SKIP')}",
                f"• `/music stop` (`{p}stop`, `{p}leave`) — {t(guild, 'MENU_CMD_MUSIC_STOP')}",
                f"• `/music queue` (`{p}queue`, `{p}q`) — {t(guild, 'MENU_CMD_MUSIC_QUEUE')}",
                f"• `/music nowplaying` (`{p}np`) — {t(guild, 'MENU_CMD_MUSIC_NP')}",
                f"• `/music pause` / `/music resume` — {t(guild, 'MENU_CMD_MUSIC_PAUSE')}",
                f"• `/music loop <off|song|queue>` — {t(guild, 'MENU_CMD_MUSIC_LOOP')}",
                f"• `/music volume <0-200>` (`{p}volume`, `{p}vol`) — {t(guild, 'MENU_CMD_MUSIC_VOL')}",
                f"• `/music filter <bassboost|nightcore|vaporwave|8d|off>` — {t(guild, 'MENU_CMD_MUSIC_FILTER')}",
                f"• `/music fav <add|play|list|remove>` (`{p}fav`) — {t(guild, 'MENU_CMD_MUSIC_FAV')}",
                f"• `/music shuffle` | `/music seek <giây>` | `/music previous` (`{p}prev`) — {t(guild, 'MENU_CMD_MUSIC_EXTRA')}",
            ]
            embed.description = "\n".join(commands_list)

        # 13. MODERATION
        elif category == "mod":
            embed.title = t(guild, "MENU_MOD_TITLE")
            commands_list = [
                f"**{t(guild, 'MENU_SEC_MOD_PUNISH')}:**",
                f"• `/mod panel` (`{p}mod panel`) — {t(guild, 'MENU_CMD_MOD_PANEL')}",
                f"• `/mod clear <số_lượng/all> [member]` — {t(guild, 'MENU_CMD_MOD_CLEAR')}",
                f"• `/mod warn <member> [lý_do]` — {t(guild, 'MENU_CMD_MOD_WARN')}",
                f"• `/mod warnings` / `unwarn` — {t(guild, 'MENU_CMD_MOD_WARNS')}",
                f"• `/mod mute <member> <phút>` / `unmute` — {t(guild, 'MENU_CMD_MOD_MUTE')}",
                f"• `/mod kick <member>` / `/mod ban <member>` / `unban` — {t(guild, 'MENU_CMD_MOD_KICK')}",
                f"• `/mod channel <lock|unlock|hide|unhide|slowmode|nsfw|rename|reset>` — {t(guild, 'MENU_CMD_MOD_CHANNEL')}",
                f"• `/mod server <status|name|description|icon|banner|lockdown>` — {t(guild, 'MENU_CMD_MOD_SERVER')}",
                f"• `/mod members` — {t(guild, 'MENU_CMD_MOD_MEMBERS')}",
                f"• `/mod setlang <vi|en>` — {t(guild, 'MENU_CMD_MOD_SETLANG')}",
                "",
                f"**{t(guild, 'MENU_SEC_MOD_CONFIG')}:**",
                f"• `/fishing setup` (`{p}fsetup`) — {t(guild, 'MENU_CMD_MOD_FSETUP')}",
                f"• `/leveling panel` (`{p}leveling`, `{p}lv`) — {t(guild, 'MENU_CMD_MOD_LV_PANEL')}",
                f"• `/leveling toggle <on|off>` — {t(guild, 'MENU_CMD_MOD_LV_TOGGLE')}",
                f"• `{p}setprefix <prefix>` — {t(guild, 'MENU_CMD_MOD_SETPREFIX')}",
                f"• `{p}globalchat set/unset` — {t(guild, 'MENU_CMD_MOD_GLOBALCHAT')}",
                f"• `/ticket setup` | `/confession setup` | `/requestrole setup` — {t(guild, 'MENU_CMD_MOD_SYSTEMS')}",
                f"• `{p}embed` — {t(guild, 'MENU_CMD_MOD_EMBED')}",
            ]
            embed.description = "\n".join(commands_list)

        # 14. LOGS
        elif category == "logs":
            embed.title = t(guild, "MENU_LOGS_TITLE")
            commands_list = [
                f"• `/setup config` — {t(guild, 'MENU_CMD_LOGS_SETUP')}",
                f"• `/setup view` / `/setup test` — {t(guild, 'MENU_CMD_LOGS_TEST')}",
                f"• `/setlog <chế_độ> <#kênh>` — {t(guild, 'MENU_CMD_LOGS_SETLOG')}",
                f"• `{p}roleadmin add/remove/list` — {t(guild, 'MENU_CMD_LOGS_ROLEADMIN')}",
            ]
            embed.description = "\n".join(commands_list)

        # 15. ANTI-RAID
        elif category == "anti":
            embed.title = t(guild, "MENU_ANTI_TITLE")
            commands_list = [
                f"• `{p}antinuke` — {t(guild, 'MENU_CMD_ANTI_NUKE')}",
                f"• `{p}antiraid` — {t(guild, 'MENU_CMD_ANTI_RAID')}",
                f"• `{p}antispam` — {t(guild, 'MENU_CMD_ANTI_SPAM')}",
                f"• `{p}antilink` — {t(guild, 'MENU_CMD_ANTI_LINK')}",
                f"• `{p}antiinvite` — {t(guild, 'MENU_CMD_ANTI_INVITE')}",
                f"• `{p}antiword` — {t(guild, 'MENU_CMD_ANTI_WORD')}",
                f"• `/antiinsult` — {t(guild, 'MENU_CMD_ANTI_INSULT')}",
                f"• `{p}backup` — {t(guild, 'MENU_CMD_ANTI_BACKUP')}",
            ]
            embed.description = "\n".join(commands_list)

        # 16. OWNER ONLY (Giữ nguyên tiếng Việt theo yêu cầu)
        elif category == "owner":
            embed.title = "👑 LỆNH DÀNH CHO CHỦ SỞ HỮU (OWNER ONLY)"
            commands_list = [
                "**👑 Quản trị Tối cao (/owner):**",
                f"• `/owner panel` (`{p}owner`) — Bảng điều khiển quản trị Chủ Bot",
                f"• `/fishing owner` (`{p}fowner`) — Bảng điều khiển Đại Dương (Tạo Giftcode, Tra cứu Catalog, Cấp phát đồ/cá, Thao túng thời tiết & chứng khoán)",
                f"• `/leveling setstat <@user> <xp|level|coins|bank> <số>` — Gán chỉ số kinh tế & cấp độ",
                f"• `/owner botinfo` (`{p}botinfo`) — Xem thông số phần cứng, RAM, CPU, Uptime",
                f"• `/owner reload/load/unload <cog>` — Tải lại module nóng không cần tắt Bot",
                f"• `/owner sync` — Đồng bộ toàn bộ Slash Command lên Discord",
                f"• `/owner servers` (`{p}servers`) — Danh sách các Server Bot tham gia",
                f"• `/owner addadmin/rmadmin/listadmin` — Quản lý Role Admin Bot từ xa",
                f"• `/owner say <channel_id> <nội_dung>` (`{p}sayto`) — Gửi tin nhắn mượn danh Bot",
                f"• `/owner findrole <server_id> <role_name>` — Tra cứu ID Role từ xa",
                f"• `/owner restart` (`{p}restart`) | `/owner shutdown` (`{p}shutdown`)",
                "",
                "**🎛️ Quản lý Đa tiến trình (/menubot):**",
                f"• `/menubot panel` (`{p}menubot`) — Bảng điều khiển tiến trình file .py",
                f"• `/menubot check` — Kiểm tra trạng thái hoạt động của tất cả file .py",
                f"• `/menubot start/stop/restart <file.py>` — Khởi chạy, dừng, khởi động lại file",
                f"• `/menubot info <file.py>` | `/menubot net <file.py>` — Giám sát tài nguyên & mạng",
                f"• `{p}botping <file.py>` — Đo độ trễ phản hồi của tiến trình",
                "",
                "**🔒 Hệ thống Toàn cục:**",
                f"• `{p}blacklist <add/remove/list>` — Quản lý danh sách đen toàn hệ thống",
                f"• `{p}proxy` — Bảng điều khiển Proxy Command",
                f"• `{p}download_toggle <on/off>` — Bật/tắt tự động tải video MXH",
            ]
            embed.description = "\n".join(commands_list)

        embed.set_footer(
            text=t(guild, "MENU_FOOTER", prefix=p, user=interaction.user.display_name),
            icon_url=interaction.user.display_avatar.url
        )
        await interaction.response.edit_message(embed=embed, view=self.view)


class MenuView(discord.ui.View):
    def __init__(self, bot: commands.Bot, author: discord.abc.User, guild: Optional[discord.Guild], prefix: str):
        super().__init__(timeout=180)
        self.bot = bot
        self.author = author
        self.guild = guild
        self.prefix = prefix
        self.message: Optional[discord.Message] = None

        self.select_menu = MenuSelect(bot, author, guild, prefix)
        self.add_item(self.select_menu)

        # Dynamic bilingual button labels
        self.home_button.label = t(guild, "MENU_BTN_HOME")
        self.close_button.label = t(guild, "MENU_BTN_CLOSE")

    def build_home_embed(self) -> discord.Embed:
        embed = discord.Embed(
            title=t(self.guild, "MENU_MAIN_TITLE"),
            description=t(self.guild, "MENU_MAIN_DESC"),
            color=discord.Color.from_rgb(255, 182, 193)
        )
        if self.bot.user and self.bot.user.display_avatar:
            embed.set_thumbnail(url=self.bot.user.display_avatar.url)
        embed.set_footer(
            text=t(self.guild, "MENU_FOOTER", prefix=self.prefix, user=self.author.display_name),
            icon_url=self.author.display_avatar.url
        )
        return embed

    @discord.ui.button(label="Trang chủ", emoji="🏠", style=discord.ButtonStyle.secondary, row=1)
    async def home_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        for opt in self.select_menu.options:
            opt.default = False
        await interaction.response.edit_message(embed=self.build_home_embed(), view=self)

    @discord.ui.button(label="Đóng Menu", emoji="🗑️", style=discord.ButtonStyle.danger, row=1)
    async def close_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer()
        await interaction.delete_original_response()
        self.stop()

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id != self.author.id:
            await interaction.response.send_message(
                t(interaction.guild, "MENU_NOT_YOURS", prefix=self.prefix),
                ephemeral=True
            )
            return False
        return True

    async def on_timeout(self):
        for item in self.children:
            item.disabled = True
        try:
            if self.message:
                await self.message.edit(view=self)
        except Exception:
            pass


class MenuCog(commands.Cog, name="Menu"):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    async def _send_menu(self, ctx_or_interaction, prefix: str):
        is_slash = isinstance(ctx_or_interaction, discord.Interaction)
        author = ctx_or_interaction.user if is_slash else ctx_or_interaction.author
        guild = ctx_or_interaction.guild

        view = MenuView(self.bot, author, guild, prefix)
        embed = view.build_home_embed()

        if is_slash:
            await ctx_or_interaction.response.send_message(embed=embed, view=view)
            view.message = await ctx_or_interaction.original_response()
        else:
            view.message = await ctx_or_interaction.send(embed=embed, view=view)

    @commands.command(name="menu", aliases=["danhmuc"], description="Show interactive command menu / Xem menu lệnh tương tác")
    async def menu_prefix(self, ctx: commands.Context):
        prefix = ctx.prefix if hasattr(ctx, "prefix") and ctx.prefix else "s!"
        await self._send_menu(ctx, prefix)

    @app_commands.command(name="menu", description="Show interactive command menu / Xem menu lệnh tương tác")
    async def menu_slash(self, interaction: discord.Interaction):
        prefix = "/"
        await self._send_menu(interaction, prefix)


async def setup(bot: commands.Bot):
    await bot.add_cog(MenuCog(bot))
