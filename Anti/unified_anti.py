import asyncio
import datetime
import difflib
import json
import os
import re
import time
from collections import defaultdict, deque
from typing import Literal, Optional

import discord
from discord import app_commands
from discord.ext import commands
from Check.i18n import t, is_vietnamese

CONFIG_PATH = "data/anti_system_config.json"
STRIKES_PATH = "data/anti_strikes.json"

# Phishing / Scam keywords & known scam domains
SCAM_DOMAINS = [
    "dlscord.gg", "dlscord.com", "discrod-app.com", "discorcl.com", "discorcl-app.com",
    "discord-nitro", "free-nitro", "steamcommuniity.com", "steamcommunlty.com",
    "steam-wallet", "grabify.link", "iplogger.org", "2no.co", "yip.su",
    "airdrop-crypto", "gift-nitro", "nitro-free", "claim-nitro", "discordgift"
]

DANGEROUS_EXTS = (
    ".exe", ".scr", ".bat", ".cmd", ".vbs", ".ps1", ".apk", ".jar", ".msi", ".pif"
)

DEFAULT_WHITELIST_DOMAINS = [
    "youtube.com", "youtu.be", "tenor.com", "giphy.com", "google.com",
    "github.com", "facebook.com", "twitter.com", "x.com", "reddit.com",
    "wikipedia.org", "spotify.com", "imgur.com", "discord.com"
]

DEFAULT_GUILD_CONFIG = {
    "enabled": True,
    "log_channel_id": None,
    "whitelist_roles": [],
    "whitelist_users": [],
    "exempt_channels": [],
    "anti_raid": {
        "enabled": True,
        "join_threshold": 4,      # 4 joins within 10 seconds
        "timeframe": 10,
        "min_account_age_days": 3, # flag accounts < 3 days old during burst
        "block_default_avatar": True,
        "action": "kick",         # kick / ban / timeout
        "auto_lockdown": False
    },
    "anti_nuke": {
        "enabled": True,
        "timeframe": 60,
        "channel_delete_limit": 3,
        "channel_create_limit": 4,
        "role_delete_limit": 3,
        "role_create_limit": 4,
        "ban_limit": 3,
        "kick_limit": 3,
        "action": "strip_and_ban"  # strip_and_ban / strip_and_kick / strip_only
    },
    "anti_spam": {
        "enabled": True,
        "max_messages": 5,        # 5 messages in 4s
        "timeframe": 4,
        "fuzzy_check": True,      # detect slight changes in repeated messages
        "max_mentions": 5,
        "max_emojis": 8,
        "max_caps_percent": 75,
        "anti_zalgo": True
    },
    "anti_link": {
        "enabled": True,
        "block_all_links": False,
        "block_scam_phishing": True,
        "block_discord_invites": True,
        "block_executables": True,
        "whitelist_domains": DEFAULT_WHITELIST_DOMAINS
    },
    "anti_words": {
        "enabled": True,
        "words": ["đụ", "lồn", "buồi", "cặc", "chó chết", "súc sinh", "dcm", "vcl"]
    },
    "adaptive_punishment": {
        "enabled": True,
        "strike_decay_hours": 24, # strikes reset after 24h
        "strike_actions": {
            "1": "warn",
            "2": "timeout_5m",
            "3": "timeout_1h",
            "4": "kick"
        }
    }
}


def load_config() -> dict:
    if os.path.exists(CONFIG_PATH):
        try:
            with open(CONFIG_PATH, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {}
    return {}


def save_config(data: dict):
    os.makedirs(os.path.dirname(CONFIG_PATH), exist_ok=True)
    with open(CONFIG_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def load_strikes() -> dict:
    if os.path.exists(STRIKES_PATH):
        try:
            with open(STRIKES_PATH, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {}
    return {}


def save_strikes(data: dict):
    os.makedirs(os.path.dirname(STRIKES_PATH), exist_ok=True)
    with open(STRIKES_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


class UnifiedAntiCog(commands.Cog, name="UnifiedAnti"):
    """Hệ thống Bảo Mật & Anti All-In-One Thông Minh duy nhất của SakuraBot."""

    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.config = load_config()
        self.strikes = load_strikes()

        # In-memory tracking
        self.join_history = defaultdict(deque)  # guild_id: deque[timestamp]
        self.msg_history = defaultdict(lambda: defaultdict(deque))  # guild_id: {user_id: deque[(timestamp, content)]}
        self.nuke_history = defaultdict(lambda: defaultdict(lambda: defaultdict(deque))) # guild_id: {user_id: {action: deque[ts]}}
        self.lockdown_cache = {}  # guild_id: {channel_id: overwrites}

    def get_guild_cfg(self, guild_id: int) -> dict:
        gid = str(guild_id)
        if gid not in self.config:
            # Deep copy default
            self.config[gid] = json.loads(json.dumps(DEFAULT_GUILD_CONFIG))
            save_config(self.config)
        return self.config[gid]

    def is_exempt(self, member: discord.Member, channel: Optional[discord.abc.GuildChannel] = None) -> bool:
        """Kiểm tra thành viên hoặc kênh có được miễn trừ không."""
        if not member or not member.guild:
            return True
        if member.id == self.bot.user.id:
            return True
        if member.id == member.guild.owner_id:
            return True
        if member.guild_permissions.administrator:
            return True

        cfg = self.get_guild_cfg(member.guild.id)
        if member.id in cfg.get("whitelist_users", []):
            return True

        for role in getattr(member, "roles", []):
            if role.id in cfg.get("whitelist_roles", []):
                return True

        if channel and channel.id in cfg.get("exempt_channels", []):
            return True

        return False

    async def log_security_event(self, guild: discord.Guild, title: str, description: str, color: discord.Color = discord.Color.red()):
        """Gửi cảnh báo an ninh vào kênh log đã chỉ định."""
        cfg = self.get_guild_cfg(guild.id)
        channel_id = cfg.get("log_channel_id")
        if not channel_id:
            return

        channel = guild.get_channel(channel_id)
        if not channel:
            return

        embed = discord.Embed(
            title=f"🚨 [SAKURA SHIELD] {title}",
            description=description,
            color=color,
            timestamp=datetime.datetime.now(datetime.timezone.utc)
        )
        embed.set_footer(text=f"Guild ID: {guild.id} • Sakura AI Protection", icon_url=guild.icon.url if guild.icon else None)
        try:
            await channel.send(embed=embed)
        except Exception:
            pass

    async def apply_strike(self, member: discord.Member, reason: str, channel: Optional[discord.TextChannel] = None):
        """Hệ thống phạt lũy tiến (Adaptive Strike Escalation)."""
        guild = member.guild
        gid, uid = str(guild.id), str(member.id)
        cfg = self.get_guild_cfg(guild.id)

        now = time.time()
        user_strikes = self.strikes.setdefault(gid, {}).setdefault(uid, {"count": 0, "last_strike": 0})
        
        # Reset if decay time passed (24h)
        decay_sec = cfg.get("adaptive_punishment", {}).get("strike_decay_hours", 24) * 3600
        if now - user_strikes["last_strike"] > decay_sec:
            user_strikes["count"] = 0

        user_strikes["count"] += 1
        user_strikes["last_strike"] = now
        count = user_strikes["count"]
        save_strikes(self.strikes)

        actions = cfg.get("adaptive_punishment", {}).get("strike_actions", {})
        action_key = str(min(count, 4))
        action = actions.get(action_key, "warn")

        action_msg = t(guild, "ANTI_UNIFIED_ACT_WARN")
        try:
            if action == "warn":
                action_msg = t(guild, "ANTI_UNIFIED_ACT_WARN_MSG", count=count)
                if channel:
                    await channel.send(t(guild, "ANTI_UNIFIED_WARN_CHANNEL", mention=member.mention, reason=reason, count=count), delete_after=8)
            elif action == "timeout_5m":
                action_msg = t(guild, "ANTI_UNIFIED_ACT_TO5")
                await member.timeout(datetime.timedelta(minutes=5), reason=f"[Sakura Anti] {reason} (Vi phạm lần 2)")
                if channel:
                    await channel.send(t(guild, "ANTI_UNIFIED_TO5_CHANNEL", mention=member.mention, reason=reason), delete_after=10)
            elif action == "timeout_1h":
                action_msg = t(guild, "ANTI_UNIFIED_ACT_TO1H")
                await member.timeout(datetime.timedelta(hours=1), reason=f"[Sakura Anti] {reason} (Vi phạm lần 3)")
                if channel:
                    await channel.send(t(guild, "ANTI_UNIFIED_TO1H_CHANNEL", mention=member.mention, reason=reason), delete_after=10)
            elif action in ("kick", "ban"):
                if action == "ban":
                    action_msg = t(guild, "ANTI_UNIFIED_ACT_BAN")
                    await member.ban(reason=f"[Sakura Anti] Vi phạm quá nhiều lần: {reason}")
                else:
                    action_msg = t(guild, "ANTI_UNIFIED_ACT_KICK")
                    await member.kick(reason=f"[Sakura Anti] Vi phạm quá nhiều lần: {reason}")
                if channel:
                    await channel.send(t(guild, "ANTI_UNIFIED_EVICT_CHANNEL", mention=member.mention), delete_after=10)
        except Exception as e:
            action_msg += f" ({t(guild, 'ANTI_UNIFIED_ERR_PERM')}: {e})"

        await self.log_security_event(
            guild,
            t(guild, "ANTI_UNIFIED_LOG_PUNISH_TITLE", name=member.display_name),
            f"**{t(guild, 'ANTI_UNIFIED_LOG_MEMBER')}:** {member.mention} (`{member.id}`)\n"
            f"**{t(guild, 'ANTI_UNIFIED_LOG_REASON')}:** {reason}\n"
            f"**{t(guild, 'ANTI_UNIFIED_LOG_PENALTY', count=count)}:** {action_msg}",
            discord.Color.orange()
        )

    # ================= LISTENER: MESSAGE SHIELD =================
    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if not message.guild or message.author.bot:
            return

        cfg = self.get_guild_cfg(message.guild.id)
        if not cfg.get("enabled", True):
            return

        if self.is_exempt(message.author, message.channel):
            return

        content = message.content or ""
        author = message.author
        now = time.time()

        # 1. Quét File Đính Kèm Độc Hại (.exe, .scr, .bat...)
        if cfg.get("anti_link", {}).get("block_executables", True):
            for att in message.attachments:
                fn = att.filename.lower()
                if fn.endswith(DANGEROUS_EXTS):
                    try:
                        await message.delete()
                    except Exception:
                        pass
                    await self.apply_strike(author, t(message.guild, "ANTI_UNIFIED_REASON_EXE", filename=att.filename), message.channel)
                    return

        # 2. Quét Link Lừa Đảo / Phishing / IP Grabber
        if cfg.get("anti_link", {}).get("block_scam_phishing", True):
            content_lower = content.lower()
            for scam_kw in SCAM_DOMAINS:
                if scam_kw in content_lower:
                    try:
                        await message.delete()
                    except Exception:
                        pass
                    await self.apply_strike(author, t(message.guild, "ANTI_UNIFIED_REASON_PHISHING", domain=scam_kw), message.channel)
                    return

        # 3. Quét Discord Invite (Trừ invite chính server)
        if cfg.get("anti_link", {}).get("block_discord_invites", True):
            invite_pattern = r"(discord\.gg/|discord\.com/invite/|discordapp\.com/invite/)([a-zA-Z0-9\-]+)"
            match = re.search(invite_pattern, content)
            if match:
                code = match.group(2)
                # Kiểm tra xem có phải invite của chính server này không
                is_own_invite = False
                try:
                    if message.guild.me.guild_permissions.manage_guild:
                        invites = await message.guild.invites()
                        if any(inv.code.lower() == code.lower() for inv in invites):
                            is_own_invite = True
                except Exception:
                    pass

                if not is_own_invite:
                    try:
                        await message.delete()
                    except Exception:
                        pass
                    await self.apply_strike(author, t(message.guild, "ANTI_UNIFIED_REASON_INVITE", code=code), message.channel)
                    return

        # 4. Quét Toàn Bộ Link (Nếu block_all_links bật)
        if cfg.get("anti_link", {}).get("block_all_links", False):
            if re.search(r"https?://\S+", content):
                # Bỏ qua whitelist domains
                whitelisted = False
                for wd in cfg.get("anti_link", {}).get("whitelist_domains", DEFAULT_WHITELIST_DOMAINS):
                    if wd.lower() in content.lower():
                        whitelisted = True
                        break
                if not whitelisted:
                    try:
                        await message.delete()
                    except Exception:
                        pass
                    await self.apply_strike(author, t(message.guild, "ANTI_UNIFIED_REASON_UNAPPROVED_LINK", domain="link"), message.channel)
                    return

        # 5. Quét Từ Cấm (Anti-Words)
        if cfg.get("anti_words", {}).get("enabled", True):
            words = cfg.get("anti_words", {}).get("words", [])
            content_clean = re.sub(r"[^\w\s]", "", content.lower())
            for w in words:
                if w.lower() in content_clean:
                    try:
                        await message.delete()
                    except Exception:
                        pass
                    await self.apply_strike(author, t(message.guild, "ANTI_UNIFIED_REASON_BAD_WORD", word=w), message.channel)
                    return

        # 6. Quét Spam Thông Minh (Burst Rate & Fuzzy Duplicate)
        spam_cfg = cfg.get("anti_spam", {})
        if spam_cfg.get("enabled", True):
            # 6.1 Mass Mentions
            max_mentions = spam_cfg.get("max_mentions", 5)
            if len(message.mentions) + len(message.role_mentions) > max_mentions:
                try:
                    await message.delete()
                except Exception:
                    pass
                await self.apply_strike(author, t(message.guild, "ANTI_UNIFIED_REASON_MASS_MENTION"), message.channel)
                return

            # 6.2 Zalgo Text
            if spam_cfg.get("anti_zalgo", True):
                zalgo_matches = re.findall(r"[\u0300-\u036f\u0483-\u0489\u1dc0-\u1dff\u20d0-\u20ff\ufe20-\ufe2f]", content)
                if len(zalgo_matches) > 6:
                    try:
                        await message.delete()
                    except Exception:
                        pass
                    await self.apply_strike(author, t(message.guild, "ANTI_UNIFIED_REASON_ZALGO"), message.channel)
                    return

            # 6.3 Burst Speed Tracker
            user_history = self.msg_history[message.guild.id][author.id]
            timeframe = spam_cfg.get("timeframe", 4)
            while user_history and now - user_history[0][0] > timeframe:
                user_history.popleft()

            user_history.append((now, content))

            if len(user_history) >= spam_cfg.get("max_messages", 5):
                user_history.clear()
                try:
                    await message.delete()
                except Exception:
                    pass
                await self.apply_strike(author, t(message.guild, "ANTI_UNIFIED_REASON_FAST_SPAM", rate=">5"), message.channel)
                return

            # 6.4 Fuzzy Duplicate Spam (Detect slight modifications: "free nitro 1", "free nitro 2")
            if spam_cfg.get("fuzzy_check", True) and len(content) > 6:
                recent_msgs = [c for ts, c in user_history if now - ts < 12 and c != content]
                for old_msg in recent_msgs:
                    sim = difflib.SequenceMatcher(None, content.lower(), old_msg.lower()).ratio()
                    if sim >= 0.82:
                        try:
                            await message.delete()
                        except Exception:
                            pass
                        await self.apply_strike(author, t(message.guild, "ANTI_UNIFIED_REASON_DUPLICATE"), message.channel)
                        return

    # ================= LISTENER: SMART RAID SHIELD =================
    @commands.Cog.listener()
    async def on_member_join(self, member: discord.Member):
        guild = member.guild
        cfg = self.get_guild_cfg(guild.id)
        if not cfg.get("enabled", True):
            return

        raid_cfg = cfg.get("anti_raid", {})
        if not raid_cfg.get("enabled", True):
            return

        now = time.time()
        history = self.join_history[guild.id]
        timeframe = raid_cfg.get("timeframe", 10)

        while history and now - history[0] > timeframe:
            history.popleft()

        history.append(now)

        # Tính tuổi tài khoản
        account_age_days = (datetime.datetime.now(datetime.timezone.utc) - member.created_at).total_seconds() / 86400.0
        min_age = raid_cfg.get("min_account_age_days", 3)
        has_default_avatar = member.avatar is None

        # Kiểm tra ngưỡng tràn vào
        threshold = raid_cfg.get("join_threshold", 4)
        is_raid_detected = len(history) >= threshold
        is_suspicious_account = (account_age_days < min_age) or (has_default_avatar and account_age_days < 7)

        if is_raid_detected or (len(history) >= 2 and is_suspicious_account):
            action = raid_cfg.get("action", "kick")
            punish_str = "Trục xuất"
            try:
                if action == "ban":
                    await member.ban(reason=f"[Sakura Anti-Raid] Tấn công tràn vào / Clone account ({account_age_days:.1f} ngày tuổi)")
                    punish_str = "Ban vĩnh viễn"
                elif action == "timeout":
                    await member.timeout(datetime.timedelta(hours=2), reason="[Sakura Anti-Raid] Nghi vấn tài khoản tấn công")
                    punish_str = "Timeout 2 giờ"
                else:
                    await member.kick(reason=f"[Sakura Anti-Raid] Tấn công tràn vào / Clone account ({account_age_days:.1f} ngày tuổi)")
                    punish_str = "Kick ra khỏi server"
            except Exception as e:
                punish_str += f" (Thất bại: {e})"

            await self.log_security_event(
                guild,
                "🛡️ PHÁT HIỆN TẤN CÔNG TRÀN VÀO (RAID DETECTED)!",
                f"**Thành viên kích hoạt:** {member.mention} (`{member.id}`)\n"
                f"**Tuổi tài khoản:** `{account_age_days:.1f}` ngày\n"
                f"**Avatar mặc định:** {'Có' if has_default_avatar else 'Không'}\n"
                f"**Lưu lượng gia nhập:** `{len(history)}` lượt / `{timeframe}` giây\n"
                f"**Hành động đã xử lý:** **{punish_str}**",
                discord.Color.red()
            )

            # Auto-Lockdown nếu được cấu hình
            if raid_cfg.get("auto_lockdown", False) and is_raid_detected:
                await self.trigger_lockdown(guild, True, reason="Tự động khóa khẩn cấp do phát hiện Raid tràn vào ồ ạt!")

    # ================= LISTENER: SMART ANTI-NUKE SHIELD =================
    async def _handle_nuke_action(self, guild: discord.Guild, action_type: str, limit_key: str):
        cfg = self.get_guild_cfg(guild.id)
        if not cfg.get("enabled", True):
            return

        nuke_cfg = cfg.get("anti_nuke", {})
        if not nuke_cfg.get("enabled", True):
            return

        limit = nuke_cfg.get(limit_key, 3)
        timeframe = nuke_cfg.get("timeframe", 60)
        now = time.time()

        try:
            # Tra cứu Audit Log để tìm thủ phạm
            action_map = {
                "channel_delete": discord.AuditLogAction.channel_delete,
                "channel_create": discord.AuditLogAction.channel_create,
                "role_delete": discord.AuditLogAction.role_delete,
                "role_create": discord.AuditLogAction.role_create,
                "ban": discord.AuditLogAction.ban,
                "kick": discord.AuditLogAction.kick,
            }
            audit_action = action_map.get(action_type)
            if not audit_action:
                return

            async for entry in guild.audit_logs(limit=1, action=audit_action):
                user = entry.user
                if not user or user.id == self.bot.user.id or user.id == guild.owner_id:
                    return

                member = guild.get_member(user.id)
                if member and self.is_exempt(member):
                    return

                # Đếm số hành vi trong timeframe
                user_acts = self.nuke_history[guild.id][user.id][action_type]
                while user_acts and now - user_acts[0] > timeframe:
                    user_acts.popleft()

                user_acts.append(now)

                if len(user_acts) >= limit:
                    user_acts.clear()
                    action = nuke_cfg.get("action", "strip_and_ban")
                    status_log = ""

                    # 1. Tước mọi quyền quản trị ngay lập tức
                    if member:
                        try:
                            dangerous_roles = [r for r in member.roles if r.permissions.administrator or r.permissions.manage_guild or r.permissions.manage_channels or r.permissions.manage_roles or r.permissions.ban_members]
                            if dangerous_roles:
                                await member.remove_roles(*dangerous_roles, reason="[Sakura Anti-Nuke] Tước vai trò nguy hiểm do có hành vi phá hoại!")
                                status_log += f"{t(guild, 'ANTI_UNIFIED_NUKE_ROLES_STRIPPED', count=len(dangerous_roles))}\n"
                        except Exception as e:
                            status_log += f"{t(guild, 'ANTI_UNIFIED_NUKE_STRIP_ERR', err=str(e))}\n"

                    # 2. Xử phạt (Ban hoặc Kick)
                    try:
                        if "ban" in action:
                            await guild.ban(user, reason=f"[Sakura Anti-Nuke] Phá hoại server ({action_type} vượt quá ngưỡng {limit}/{timeframe}s)")
                            status_log += t(guild, "ANTI_UNIFIED_NUKE_BANNED")
                        elif "kick" in action and member:
                            await member.kick(reason=f"[Sakura Anti-Nuke] Phá hoại server ({action_type})")
                            status_log += t(guild, "ANTI_UNIFIED_NUKE_KICKED")
                    except Exception as e:
                        status_log += t(guild, "ANTI_UNIFIED_NUKE_PUNISH_ERR", err=str(e))

                    await self.log_security_event(
                        guild,
                        t(guild, "ANTI_UNIFIED_NUKE_ALERT_TITLE"),
                        f"**{t(guild, 'ANTI_UNIFIED_NUKE_PERPETRATOR')}:** {user.mention} (`{user.id}`)\n"
                        f"**{t(guild, 'ANTI_UNIFIED_NUKE_BEHAVIOR')}:** `{action_type}` `{limit}` / `{timeframe}`s\n"
                        f"**{t(guild, 'ANTI_UNIFIED_NUKE_RESPONSE')}:**\n{status_log}",
                        discord.Color.dark_red()
                    )
        except Exception:
            pass

    @commands.Cog.listener()
    async def on_guild_channel_delete(self, channel: discord.abc.GuildChannel):
        await self._handle_nuke_action(channel.guild, "channel_delete", "channel_delete_limit")

    @commands.Cog.listener()
    async def on_guild_channel_create(self, channel: discord.abc.GuildChannel):
        await self._handle_nuke_action(channel.guild, "channel_create", "channel_create_limit")

    @commands.Cog.listener()
    async def on_guild_role_delete(self, role: discord.Role):
        await self._handle_nuke_action(role.guild, "role_delete", "role_delete_limit")

    @commands.Cog.listener()
    async def on_guild_role_create(self, role: discord.Role):
        await self._handle_nuke_action(role.guild, "role_create", "role_create_limit")

    @commands.Cog.listener()
    async def on_member_ban(self, guild: discord.Guild, user: discord.User | discord.Member):
        await self._handle_nuke_action(guild, "ban", "ban_limit")

    @commands.Cog.listener()
    async def on_member_remove(self, member: discord.Member):
        # Có thể là kick
        await self._handle_nuke_action(member.guild, "kick", "kick_limit")

    # ================= LOCKDOWN / PANIC MODE =================
    async def trigger_lockdown(self, guild: discord.Guild, lock: bool = True, reason: str = "") -> int:
        """Khóa hoặc mở khóa tạm thời các kênh chat khi có báo động khẩn cấp."""
        affected = 0
        default_role = guild.default_role

        if lock:
            saved_perms = {}
            for channel in guild.text_channels:
                if channel.permissions_for(default_role).send_messages is not False:
                    try:
                        ow = channel.overwrites_for(default_role)
                        saved_perms[channel.id] = ow.send_messages
                        ow.send_messages = False
                        await channel.set_permissions(default_role, overwrite=ow, reason=f"[Sakura Lockdown] {reason}")
                        affected += 1
                    except Exception:
                        pass
            self.lockdown_cache[guild.id] = saved_perms
        else:
            saved_perms = self.lockdown_cache.get(guild.id, {})
            for channel in guild.text_channels:
                if channel.id in saved_perms:
                    try:
                        ow = channel.overwrites_for(default_role)
                        ow.send_messages = saved_perms[channel.id]
                        await channel.set_permissions(default_role, overwrite=ow, reason="[Sakura Lockdown] Mở khóa an ninh server")
                        affected += 1
                    except Exception:
                        pass
            self.lockdown_cache.pop(guild.id, None)

        return affected

    # ================= EMBED FACTORY =================
    def build_dashboard_embed(self, guild: discord.Guild) -> discord.Embed:
        cfg = self.get_guild_cfg(guild.id)
        is_on = cfg.get("enabled", True)

        embed = discord.Embed(
            title=f"🛡️ TRUNG TÂM BẢO MẬT & ANTI SAKURA — {guild.name.upper()}",
            description=(
                f"Hệ thống an ninh thế hệ mới tích hợp AI của SakuraBot bảo vệ máy chủ toàn diện.\n"
                f"**Trạng thái máy chủ:** {'🟢 **ĐANG BẢO VỆ CHỦ ĐỘNG**' if is_on else '🔴 **ĐANG TẮT**'}\n"
                f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
            ),
            color=discord.Color.from_rgb(255, 105, 180) if is_on else discord.Color.greyple()
        )

        def badge(b: bool) -> str:
            return "🟢 `BẬT`" if b else "🔴 `TẮT`"

        r = cfg.get("anti_raid", {})
        n = cfg.get("anti_nuke", {})
        s = cfg.get("anti_spam", {})
        l = cfg.get("anti_link", {})
        w = cfg.get("anti_words", {})
        p = cfg.get("adaptive_punishment", {})

        embed.add_field(
            name="🛡️ Chống Tràn Vào (Anti-Raid)",
            value=f"• Trạng thái: {badge(r.get('enabled', True))}\n• Ngưỡng: `{r.get('join_threshold', 4)}` vào / `{r.get('timeframe', 10)}s`\n• Lọc Clone: `{r.get('min_account_age_days', 3)}` ngày",
            inline=True
        )

        embed.add_field(
            name="💣 Chống Phá Server (Anti-Nuke)",
            value=f"• Trạng thái: {badge(n.get('enabled', True))}\n• Giới hạn kênh/role: `{n.get('channel_delete_limit', 3)}`/60s\n• Tước quyền & Xử phạt tức thì",
            inline=True
        )

        embed.add_field(
            name="⚡ Chống Spam & Lặp Tin",
            value=f"• Trạng thái: {badge(s.get('enabled', True))}\n• Tần suất: `{s.get('max_messages', 5)}` tin / `{s.get('timeframe', 4)}s`\n• Quét lặp mờ (Fuzzy AI): {badge(s.get('fuzzy_check', True))}",
            inline=True
        )

        embed.add_field(
            name="🔗 Chống Link & Phishing",
            value=f"• Trạng thái: {badge(l.get('enabled', True))}\n• Chặn Phishing/Scam: {badge(l.get('block_scam_phishing', True))}\n• Chặn Invite lạ: {badge(l.get('block_discord_invites', True))}",
            inline=True
        )

        embed.add_field(
            name="🤬 Lọc Từ Cấm & Xúc Phạm",
            value=f"• Trạng thái: {badge(w.get('enabled', True))}\n• Danh sách từ cấm: `{len(w.get('words', []))}` từ",
            inline=True
        )

        embed.add_field(
            name="⚖️ Xử Phạt Lũy Tiến (Strikes)",
            value=f"• Trạng thái: {badge(p.get('enabled', True))}\n• Nâng cấp phạt: `Warn` ➔ `5m` ➔ `1h` ➔ `Kick`",
            inline=True
        )

        log_ch = guild.get_channel(cfg.get("log_channel_id", 0))
        log_str = log_ch.mention if log_ch else "*Chưa thiết lập*"
        wl_roles = len(cfg.get("whitelist_roles", []))
        wl_users = len(cfg.get("whitelist_users", []))

        embed.add_field(
            name="⚙️ Kênh Log & Danh Sách Trắng",
            value=f"• Kênh cảnh báo: {log_str}\n• Role miễn trừ: `{wl_roles}` | Thành viên miễn trừ: `{wl_users}`",
            inline=False
        )

        embed.set_footer(text="Chọn module bên dưới hoặc dùng nút bấm thao tác nhanh 1 chạm.")
        return embed

    # ================= THE MASTER SLASH COMMAND =================
    @commands.hybrid_group(name="anti", description="Quản lý toàn bộ hệ sinh thái bảo mật & anti của SakuraBot.")
    @commands.has_permissions(administrator=True)
    async def anti_cmd(self, ctx: commands.Context):
        if ctx.invoked_subcommand is None:
            view = AntiMasterDashboardView(self, ctx.guild, ctx.author.id)
            embed = self.build_dashboard_embed(ctx.guild)
            await ctx.send(embed=embed, view=view, ephemeral=True)

    @anti_cmd.command(name="setup", description="Bảng điều khiển thiết lập hệ thống Anti duy nhất với giao diện trực quan.")
    @commands.has_permissions(administrator=True)
    async def anti_setup(self, ctx: commands.Context):
        """Lệnh setup duy nhất theo yêu cầu người dùng!"""
        view = AntiMasterDashboardView(self, ctx.guild, ctx.author.id)
        embed = self.build_dashboard_embed(ctx.guild)
        await ctx.send(embed=embed, view=view, ephemeral=True)

    @anti_cmd.command(name="quicksetup", description="1-Chạm kích hoạt toàn bộ tính năng bảo vệ thông minh tối ưu.")
    @commands.has_permissions(administrator=True)
    async def anti_quicksetup(self, ctx: commands.Context):
        cfg = self.get_guild_cfg(ctx.guild.id)
        cfg["enabled"] = True
        cfg["anti_raid"]["enabled"] = True
        cfg["anti_nuke"]["enabled"] = True
        cfg["anti_spam"]["enabled"] = True
        cfg["anti_link"]["enabled"] = True
        cfg["anti_words"]["enabled"] = True
        cfg["adaptive_punishment"]["enabled"] = True
        save_config(self.config)

        embed = discord.Embed(
            title=t(ctx.guild, "ANTI_UNIFIED_QUICKSETUP_TITLE"),
            description=t(ctx.guild, "ANTI_UNIFIED_QUICKSETUP_DESC"),
            color=discord.Color.green()
        )
        await ctx.send(embed=embed, ephemeral=True)

    @anti_cmd.command(name="panic", description="Bật/Tắt chế độ khóa khẩn cấp toàn máy chủ khi đang bị phá hoại.")
    @app_commands.describe(action="Chọn khóa (lock) hoặc mở khóa (unlock)")
    @commands.has_permissions(administrator=True)
    async def anti_panic(self, ctx: commands.Context, action: Literal["lock", "unlock"]):
        is_lock = (action == "lock")
        count = await self.trigger_lockdown(ctx.guild, is_lock, reason=f"Kích hoạt thủ công bởi {ctx.author.name}")
        if is_lock:
            await ctx.send(t(ctx.guild, "ANTI_UNIFIED_PANIC_MANUAL_LOCK", count=count), ephemeral=True)
        else:
            await ctx.send(t(ctx.guild, "ANTI_UNIFIED_PANIC_MANUAL_UNLOCK", count=count), ephemeral=True)

    @anti_cmd.command(name="whitelist", description="Thêm hoặc xóa Role/User khỏi danh sách trắng miễn nhiễm.")
    @app_commands.describe(
        action="Thêm (add) hoặc Xóa (remove)",
        target="Role hoặc Thành viên cần cấu hình"
    )
    @commands.has_permissions(administrator=True)
    async def anti_whitelist(self, ctx: commands.Context, action: Literal["add", "remove"], target: discord.Role | discord.Member):
        cfg = self.get_guild_cfg(ctx.guild.id)
        is_role = isinstance(target, discord.Role)
        list_key = "whitelist_roles" if is_role else "whitelist_users"
        target_list = cfg.setdefault(list_key, [])

        if action == "add":
            if target.id not in target_list:
                target_list.append(target.id)
                save_config(self.config)
                await ctx.send(t(ctx.guild, "ANTI_UNIFIED_WL_ADDED", target=target.mention), ephemeral=True)
            else:
                await ctx.send(t(ctx.guild, "ANTI_UNIFIED_WL_EXISTS", target=target.mention), ephemeral=True)
        else:
            if target.id in target_list:
                target_list.remove(target.id)
                save_config(self.config)
                await ctx.send(t(ctx.guild, "ANTI_UNIFIED_WL_REMOVED", target=target.mention), ephemeral=True)
            else:
                await ctx.send(t(ctx.guild, "ANTI_UNIFIED_WL_NOT_FOUND", target=target.mention), ephemeral=True)


# ================= DASHBOARD UI VIEWS =================
class AntiMasterDashboardView(discord.ui.View):
    def __init__(self, cog: UnifiedAntiCog, guild: discord.Guild, author_id: int):
        super().__init__(timeout=300)
        self.cog = cog
        self.guild = guild
        self.author_id = author_id

        vi = is_vietnamese(guild)
        self.btn_optimal.label = t(guild, "ANTI_UNIFIED_BTN_OPTIMAL")
        self.btn_toggle_all.label = t(guild, "ANTI_UNIFIED_BTN_TOGGLE_ALL")
        self.btn_panic.label = t(guild, "ANTI_UNIFIED_BTN_PANIC")
        self.btn_unlock.label = t(guild, "ANTI_UNIFIED_BTN_UNLOCK")

        self.select_module.placeholder = t(guild, "ANTI_UNIFIED_SELECT_PLACEHOLDER")
        self.select_module.options = [
            discord.SelectOption(
                label="Chống Raid (Anti-Raid)" if vi else "Anti-Raid Shield",
                value="raid",
                description="Cài đặt ngưỡng tràn vào, tuổi acc, auto-lockdown" if vi else "Join threshold, account age, auto-lockdown",
                emoji="🛡️"
            ),
            discord.SelectOption(
                label="Chống Nuke (Anti-Nuke)" if vi else "Anti-Nuke Shield",
                value="nuke",
                description="Cài đặt hạn mức xóa kênh/role, tước quyền" if vi else "Channel/role delete limits, instant strip",
                emoji="💣"
            ),
            discord.SelectOption(
                label="Chống Spam & AI Lặp Tin" if vi else "Anti-Spam & AI Duplicate",
                value="spam",
                description="Tốc độ gửi tin, AI fuzzy check, mentions" if vi else "Message rate, AI fuzzy check, mentions",
                emoji="⚡"
            ),
            discord.SelectOption(
                label="Chống Link & Phishing" if vi else "Anti-Link & Phishing",
                value="link",
                description="Chặn Nitro scam, web lừa đảo, invite lạ" if vi else "Block Nitro scams, phishing links, invites",
                emoji="🔗"
            ),
            discord.SelectOption(
                label="Lọc Từ Cấm & Ngôn Từ" if vi else "Bad Words & Insult Filter",
                value="words",
                description="Quản lý danh sách từ khóa bị chặn" if vi else "Manage blocked keywords and patterns",
                emoji="🤬"
            ),
            discord.SelectOption(
                label="Kênh Log & Cảnh Báo" if vi else "Log Channel & Alerts",
                value="logs",
                description="Thiết lập kênh gửi báo cáo an ninh" if vi else "Set security alert log channel",
                emoji="📢"
            ),
        ]

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id != self.author_id:
            await interaction.response.send_message(t(self.guild, "VIEW_OTHER_USER_DENIED"), ephemeral=True)
            return False
        return True

    @discord.ui.select(
        placeholder="🛠️ Chọn module bạn muốn tinh chỉnh chi tiết...",
        options=[discord.SelectOption(label="...", value="temp")]
    )
    async def select_module(self, interaction: discord.Interaction, select: discord.ui.Select):
        val = select.values[0]
        cfg = self.cog.get_guild_cfg(self.guild.id)
        g = self.guild

        if val == "raid":
            cur = cfg.get("anti_raid", {}).get("enabled", True)
            cfg["anti_raid"]["enabled"] = not cur
            save_config(self.cog.config)
            mod_title = "Anti-Raid"
            st = "ON" if not cur else "OFF"
            await interaction.response.send_message(t(g, "ANTI_UNIFIED_MODULE_TOGGLED", module=mod_title, state=st), ephemeral=True)
        elif val == "nuke":
            cur = cfg.get("anti_nuke", {}).get("enabled", True)
            cfg["anti_nuke"]["enabled"] = not cur
            save_config(self.cog.config)
            mod_title = "Anti-Nuke"
            st = "ON" if not cur else "OFF"
            await interaction.response.send_message(t(g, "ANTI_UNIFIED_MODULE_TOGGLED", module=mod_title, state=st), ephemeral=True)
        elif val == "spam":
            cur = cfg.get("anti_spam", {}).get("enabled", True)
            cfg["anti_spam"]["enabled"] = not cur
            save_config(self.cog.config)
            mod_title = "Anti-Spam"
            st = "ON" if not cur else "OFF"
            await interaction.response.send_message(t(g, "ANTI_UNIFIED_MODULE_TOGGLED", module=mod_title, state=st), ephemeral=True)
        elif val == "link":
            cur = cfg.get("anti_link", {}).get("enabled", True)
            cfg["anti_link"]["enabled"] = not cur
            save_config(self.cog.config)
            mod_title = "Anti-Link"
            st = "ON" if not cur else "OFF"
            await interaction.response.send_message(t(g, "ANTI_UNIFIED_MODULE_TOGGLED", module=mod_title, state=st), ephemeral=True)
        elif val == "words":
            cur = cfg.get("anti_words", {}).get("enabled", True)
            cfg["anti_words"]["enabled"] = not cur
            save_config(self.cog.config)
            mod_title = "Bad Words"
            st = "ON" if not cur else "OFF"
            await interaction.response.send_message(t(g, "ANTI_UNIFIED_MODULE_TOGGLED", module=mod_title, state=st), ephemeral=True)
        elif val == "logs":
            cfg["log_channel_id"] = interaction.channel.id
            save_config(self.cog.config)
            await interaction.response.send_message(t(g, "ANTI_UNIFIED_LOG_SET", channel=interaction.channel.mention), ephemeral=True)

        embed = self.cog.build_dashboard_embed(self.guild)
        await interaction.message.edit(embed=embed, view=self)

    @discord.ui.button(label="Bảo Vệ Tối Ưu (1-Chạm)", style=discord.ButtonStyle.success, emoji="⚡", row=1)
    async def btn_optimal(self, interaction: discord.Interaction, button: discord.ui.Button):
        cfg = self.cog.get_guild_cfg(self.guild.id)
        cfg["enabled"] = True
        cfg["anti_raid"]["enabled"] = True
        cfg["anti_nuke"]["enabled"] = True
        cfg["anti_spam"]["enabled"] = True
        cfg["anti_link"]["enabled"] = True
        cfg["anti_words"]["enabled"] = True
        cfg["adaptive_punishment"]["enabled"] = True
        save_config(self.cog.config)
        embed = self.cog.build_dashboard_embed(self.guild)
        await interaction.response.edit_message(embed=embed, view=self)

    @discord.ui.button(label="Bật/Tắt Toàn Bộ", style=discord.ButtonStyle.primary, emoji="🔄", row=1)
    async def btn_toggle_all(self, interaction: discord.Interaction, button: discord.ui.Button):
        cfg = self.cog.get_guild_cfg(self.guild.id)
        cfg["enabled"] = not cfg.get("enabled", True)
        save_config(self.cog.config)
        embed = self.cog.build_dashboard_embed(self.guild)
        await interaction.response.edit_message(embed=embed, view=self)

    @discord.ui.button(label="Khóa Khẩn Cấp (Lockdown)", style=discord.ButtonStyle.danger, emoji="🚨", row=1)
    async def btn_panic(self, interaction: discord.Interaction, button: discord.ui.Button):
        count = await self.cog.trigger_lockdown(self.guild, True, reason="Lockdown via Dashboard")
        await interaction.response.send_message(t(self.guild, "ANTI_UNIFIED_PANIC_LOCKED", count=count), ephemeral=True)

    @discord.ui.button(label="Mở Khóa Server", style=discord.ButtonStyle.secondary, emoji="🔓", row=1)
    async def btn_unlock(self, interaction: discord.Interaction, button: discord.ui.Button):
        count = await self.cog.trigger_lockdown(self.guild, False, reason="Unlock via Dashboard")
        await interaction.response.send_message(t(self.guild, "ANTI_UNIFIED_PANIC_UNLOCKED", count=count), ephemeral=True)


async def setup(bot: commands.Bot):
    await bot.add_cog(UnifiedAntiCog(bot))
