import discord
from discord.ext import commands
from Check.i18n import t
import json, os, re, asyncio
from datetime import datetime, timedelta
from collections import deque, defaultdict
import time

AUTOMOD_FILE = "data/automod_detailed.json"
WARN_FILE = "data/automod_warns.json"
SERVER_CONFIG_FILE = "data/server_config.json"

# in-memory spam history {guild_id:{user_id:deque[(ts,content)]}}
spam_history = defaultdict(lambda: defaultdict(deque))
# warns {guild_id:{user_id:count}}
warns_data = {}

def load_automod():
    if not os.path.exists(AUTOMOD_FILE):
        return {}
    try:
        with open(AUTOMOD_FILE,"r",encoding="utf-8") as f:
            return json.load(f)
    except: return {}

def load_server_config():
    if not os.path.exists(SERVER_CONFIG_FILE):
        return {}
    try:
        with open(SERVER_CONFIG_FILE,"r",encoding="utf-8") as f:
            return json.load(f)
    except: return {}

def load_warns():
    global warns_data
    if os.path.exists(WARN_FILE):
        try:
            with open(WARN_FILE,"r",encoding="utf-8") as f:
                warns_data=json.load(f)
        except: warns_data={}
    else: warns_data={}

def save_warns():
    os.makedirs(os.path.dirname(WARN_FILE), exist_ok=True)
    with open(WARN_FILE,"w",encoding="utf-8") as f:
        json.dump(warns_data,f,ensure_ascii=False,indent=2)

def is_exempt_channel(cfg, channel_id):
    if not cfg.get("exempt_enabled"): return False
    return str(channel_id) in (cfg.get("exempt_channels") or [])

def is_bypass(cfg, channel_id, key):
    # words/spam bypass
    if key=="words":
        if not cfg.get("words_bypass_enabled"): return False
        return str(channel_id) in (cfg.get("words_bypass_channels") or [])
    if key=="spam":
        sp=cfg.get("spam") or {}
        if not sp.get("bypass_enabled"): return False
        return str(channel_id) in (sp.get("bypass_channels") or [])
    return False

def check_word(content, words):
    """words=[{word,type}] type contains|exact|regex ; return matched word or None"""
    cl=content.lower()
    for w in words:
        txt=w.get("word","") or w.get("text","")
        if not txt: continue
        t=w.get("type","contains")
        if t=="contains":
            if txt.lower().strip() and txt.lower().strip() in cl:
                return txt
        elif t=="exact":
            # chỉ chặn khi tin nhắn CHÍNH XÁC bằng cụm từ (trim, case-insensitive) -> như mô tả hình
            if cl.strip()==txt.lower().strip():
                return txt
        elif t=="regex":
            try:
                if re.search(txt, content, flags=re.IGNORECASE):
                    return txt
            except re.error:
                # fallback contains
                if txt.lower() in cl:
                    return txt
    return None

def _get_adv_settings(cfg):
    adv_set=cfg.get("advanced_settings") or {}
    return {
        "mention_limit": max(2, min(15, int(adv_set.get("mention_limit", 4) or 4))),
        "caps_min": max(4, min(30, int(adv_set.get("caps_min", 8) or 8))),
        "caps_percent": max(40, min(100, int(adv_set.get("caps_percent", 70) or 70))),
        "emoji_limit": max(3, min(30, int(adv_set.get("emoji_limit", 7) or 7))),
        "duplicate_limit": max(2, min(10, int(adv_set.get("duplicate_limit", 3) or 3))),
        "zalgo_limit": max(4, min(20, int(adv_set.get("zalgo_limit", 6) or 6))),
        "link_whitelist": [str(x).lower().strip().strip('.') for x in (adv_set.get("link_whitelist") or []) if str(x).strip()],
        "invite_allow_own": bool(adv_set.get("invite_allow_own", True)),
    }

async def check_advanced(content, message, cfg, bot=None):
    adv=cfg.get("advanced") or {}
    advs=_get_adv_settings(cfg)
    # anti_invite
    if adv.get("anti_invite"):
        m=re.search(r'discord\.gg/(?P<code>\S+)|discord\.com/invite/(?P<code2>\S+)|discordapp\.com/invite/(?P<code3>\S+)', content, re.I)
        if m:
            code=(m.group('code') or m.group('code2') or m.group('code3') or '').strip().split('/')[0].split('?')[0].split('#')[0]
            # nếu cho phép invite của server này thì thử kiểm tra
            if advs["invite_allow_own"] and bot and code:
                try:
                    # thử fetch invites của guild để so sánh
                    guild_invites=[]
                    try:
                        # cache guild invites nếu bot có quyền
                        if message.guild.me.guild_permissions.manage_guild:
                            guild_invites=await message.guild.invites()
                    except: pass
                    if any(inv.code==code for inv in guild_invites):
                        pass # là invite của server -> không chặn
                    else:
                        # thử fetch invite để xem guild id có trùng không (nếu fetch được)
                        try:
                            inv=await bot.fetch_invite(code)
                            if inv.guild and inv.guild.id==message.guild.id:
                                pass
                            else:
                                return "invite"
                        except:
                            return "invite"
                except:
                    return "invite"
            else:
                return "invite"
    if adv.get("anti_link"):
        urls=re.findall(r'https?://[^\s]+', content)
        if urls:
            wl=set(advs["link_whitelist"])
            # mặc định whitelist nếu rỗng thì chặn hết, nếu có thì chỉ chặn khi domain không nằm trong whitelist
            blocked=False
            for url in urls:
                try:
                    from urllib.parse import urlparse
                    domain=urlparse(url).netloc.lower().strip()
                    if domain.startswith('www.'): domain=domain[4:]
                    domain=domain.split(':')[0]
                    if not domain: continue
                    # kiểm tra whitelist: cho phép nếu domain == whitelist hoặc endswith .whitelist
                    allowed=False
                    for w in wl:
                        if domain==w or domain.endswith('.'+w):
                            allowed=True
                            break
                    if not allowed:
                        blocked=True
                        break
                except: 
                    blocked=True
                    break
            if blocked:
                return "link"
    if adv.get("anti_mention"):
        total=len(message.mentions)+len(message.role_mentions)
        if message.mention_everyone: total+=1
        if total>=advs["mention_limit"]:
            return "mention_spam"
    if adv.get("anti_caps"):
        letters=''.join(c for c in content if c.isalpha())
        if len(letters)>=advs["caps_min"]:
            up=sum(1 for c in letters if c.isupper())
            if up/len(letters)*100 >= advs["caps_percent"]:
                return "caps"
    if adv.get("anti_emoji"):
        emoji_pat=re.compile(r'<a?:\w+:\d+>|[\U0001F600-\U0001F64F\U0001F300-\U0001F5FF\U0001F680-\U0001F6FF\U0001F1E0-\U0001F1FF\U00002702-\U000027B0\U000024C2-\U0001F251]+')
        found=emoji_pat.findall(content)
        if len(found)>=advs["emoji_limit"]:
            return "emoji_spam"
    if adv.get("anti_duplicate"):
        gid=str(message.guild.id); uid=str(message.author.id)
        dq=spam_history[gid][uid]
        if len(dq)>=2:
            dup = sum(1 for _,c in list(dq)[-6:] if c==content)
            if dup >= advs["duplicate_limit"]:
                return "duplicate"
    if adv.get("anti_zalgo"):
        combining=sum(1 for ch in content if 0x0300 <= ord(ch) <= 0x036f)
        if combining>=advs["zalgo_limit"]:
            return "zalgo"
        # thêm check nặng
        zalgo_len=len(re.findall(r'[\u0300-\u036f]{3,}', content))
        if zalgo_len>=1 and combining>=advs["zalgo_limit"]:
            return "zalgo"
    return None

class AutoModCog(commands.Cog, name="Auto-Mod"):
    def __init__(self, bot: commands.Bot):
        self.bot=bot
        load_warns()
        print("[AutoMod] Cog loaded - unified automod engine")

    async def increment_warn(self, guild, member, reason, timeout_min, warn_cfg):
        gid=str(guild.id); uid=str(member.id)
        if gid not in warns_data: warns_data[gid]={}
        cur=warns_data[gid].get(uid,0)+1
        warns_data[gid][uid]=cur
        save_warns()
        warn_need=int(warn_cfg.get("warns",5)) if warn_cfg else 5
        timeout=int(warn_cfg.get("timeout",5)) if warn_cfg else 5
        if warn_cfg and not warn_cfg.get("warn_enabled", True):
            # only delete + warn message, no timeout unless explicitly
            try:
                await member.timeout(timedelta(minutes=0))
            except: pass
            # if we still want timeout when threshold reached? spec says "dù ngưỡng thì timeout" for advanced => but for words/spam if warn_enabled off, maybe still timeout? We'll still timeout when threshold reached if timeout_min>0
            pass
        # check threshold
        if cur >= warn_need:
            try:
                await member.timeout(timedelta(minutes=timeout), reason=f"AutoMod: {reason} - đủ {warn_need} warns")
                warns_data[gid][uid]=0
                save_warns()
                return True, cur
            except discord.Forbidden:
                return False, cur
            except Exception as e:
                print(f"[AutoMod] timeout fail {e}")
                return False, cur
        return False, cur

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if not message.guild or message.author.bot or not message.content:
            return
        # Kiểm tra bật/tắt toàn cục hệ thống Anti
        if os.path.exists("data/anti_global.json"):
            try:
                with open("data/anti_global.json", "r", encoding="utf-8") as f:
                    if not json.load(f).get("enabled", True):
                        return
            except Exception:
                pass
        # ignore owner/admin? we respect same as other anti: skip if has admin role
        try:
            from Check.mod import admin_roles
            from config import OWNER_ID
            if message.author.id==OWNER_ID: return
            gid=str(message.guild.id)
            admin_ids=admin_roles.get(gid,[])
            if admin_ids and any(r.id in admin_ids for r in message.author.roles):
                return
            # also ignore if user has manage_guild / administrator
            perms=message.author.guild_permissions
            if perms.administrator or perms.manage_guild:
                return
        except: pass

        cfg=load_automod().get(str(message.guild.id))
        if not cfg: return
        # check global toggle
        sc=load_server_config().get(str(message.guild.id),{})
        if sc and sc.get("automod_enabled") is False:
            return
        # exempt channel
        if is_exempt_channel(cfg, message.channel.id):
            return

        content=message.content
        reason=None
        warn_cfg=None
        # prepare spam history tracking
        gid=str(message.guild.id); uid=str(message.author.id)
        now=time.time()
        # ensure dq
        dq=spam_history[gid][uid]
        dq.append((now, content))
        # cleanup old by window max 120s
        while dq and now - dq[0][0] > 120:
            dq.popleft()

        # 1) words filter (bypass check)
        if not is_bypass(cfg, message.channel.id, "words"):
            words=cfg.get("words") or []
            matched=check_word(content, words)
            if matched:
                reason=f"từ cấm `{matched}`"
                warn_cfg=cfg.get("words_violation") or {"warn_enabled":True,"warns":5,"timeout":5}
                try: await message.delete()
                except: pass
                timed, cur = await self.increment_warn(message.guild, message.author, reason, warn_cfg.get("timeout",5), warn_cfg)
                embed=discord.Embed(
                    title=t(message.guild, "AUTOMOD_VIOLATION_WORDS_TITLE"),
                    description=t(message.guild, "AUTOMOD_VIOLATION_WORDS_DESC", mention=message.author.mention, word=matched),
                    color=0xff79c6
                )
                if warn_cfg.get("warn_enabled"):
                    embed.add_field(name=t(message.guild, "AUTOMOD_FIELD_WARN"), value=f"{cur}/{warn_cfg.get('warns',5)}")
                if timed:
                    embed.add_field(name="Timeout", value=t(message.guild, "AUTOMOD_FIELD_TIMEOUT", minutes=warn_cfg.get('timeout',5)), inline=True)
                embed.set_footer(text=f"Auto-Mod • {message.guild.name}")
                try: await message.channel.send(embed=embed, delete_after=12)
                except: pass
                return

        # 2) spam (threshold/window)
        if not is_bypass(cfg, message.channel.id, "spam"):
            sp=cfg.get("spam") or {}
            thresh=int(sp.get("threshold",5))
            window=int(sp.get("window",5))
            # count messages in window
            cnt=sum(1 for ts,_ in dq if now - ts <= window)
            if cnt >= thresh:
                reason=f"spam {cnt} tin trong {window}s"
                warn_cfg=sp.get("violation") or {"warn_enabled":True,"warns":5,"timeout":5}
                # purge recent spam
                try:
                    # delete last messages by same user in window
                    # use purge check
                    def check(m): return m.author.id==message.author.id
                    await message.channel.purge(limit=cnt+5, check=check)
                except:
                    try: await message.delete()
                    except: pass
                # clear history after handling
                dq.clear()
                timed, cur = await self.increment_warn(message.guild, message.author, reason, warn_cfg.get("timeout",5), warn_cfg)
                embed=discord.Embed(
                    title=t(message.guild, "AUTOMOD_VIOLATION_SPAM_TITLE"),
                    description=t(message.guild, "AUTOMOD_VIOLATION_SPAM_DESC", mention=message.author.mention, count=cnt, window=window),
                    color=0xff9f43
                )
                if warn_cfg.get("warn_enabled"):
                    embed.add_field(name=t(message.guild, "AUTOMOD_FIELD_WARN"), value=f"{cur}/{warn_cfg.get('warns',5)}")
                if timed:
                    embed.add_field(name="Timeout", value=t(message.guild, "AUTOMOD_FIELD_TIMEOUT", minutes=warn_cfg.get('timeout',5)), inline=True)
                try: await message.channel.send(embed=embed, delete_after=12)
                except: pass
                return

        # 3) advanced filters
        adv_reason=await check_advanced(content, message, cfg, bot=self.bot)
        if adv_reason:
            # advanced always uses same violation as words? spec says "vi phạm sẽ bị xóa + cảnh cáo (đủ ngưỡng thì timeout)" -> use words_violation or spam? We'll use words_violation as default for advanced
            # try to find advanced_warn config? reuse words_violation
            warn_cfg=cfg.get("words_violation") or {"warn_enabled":True,"warns":5,"timeout":5}
            reason_map={"invite":"link mời Discord","link":"link","mention_spam":"tag quá nhiều","caps":"Caps quá nhiều","emoji_spam":"emoji spam","duplicate":"trùng lặp","zalgo":"ký tự rối"}
            reason=reason_map.get(adv_reason, adv_reason)
            try: await message.delete()
            except: pass
            timed, cur = await self.increment_warn(message.guild, message.author, f"advanced:{reason}", warn_cfg.get("timeout",5), warn_cfg)
            embed=discord.Embed(
                title=t(message.guild, "AUTOMOD_VIOLATION_ADV_TITLE"),
                description=t(message.guild, "AUTOMOD_VIOLATION_ADV_DESC", mention=message.author.mention, reason=reason),
                color=0xbd93f9
            )
            if warn_cfg.get("warn_enabled"):
                embed.add_field(name=t(message.guild, "AUTOMOD_FIELD_WARN"), value=f"{cur}/{warn_cfg.get('warns',5)}")
            if timed:
                embed.add_field(name="Timeout", value=t(message.guild, "AUTOMOD_FIELD_TIMEOUT", minutes=warn_cfg.get('timeout',5)), inline=True)
            try: await message.channel.send(embed=embed, delete_after=12)
            except: pass
            return

    @commands.command(name="automod_test", description="Test 1 tin nhắn có bị AutoMod chặn không (admin)")
    @commands.has_permissions(manage_guild=True)
    async def automod_test(self, ctx: commands.Context, *, content: str):
        cfg=load_automod().get(str(ctx.guild.id))
        if not cfg: return await ctx.send(t(ctx.guild, "AUTOMOD_TEST_NO_CONFIG"), ephemeral=True)
        # check word
        matched=check_word(content, cfg.get("words") or [])
        if matched: return await ctx.send(t(ctx.guild, "AUTOMOD_TEST_BLOCKED_WORD", word=matched), ephemeral=True)
        # spam can't test single
        adv=await check_advanced(content, ctx.message, cfg, bot=self.bot)
        if adv: 
            advs=_get_adv_settings(cfg)
            # hiển thị chi tiết ngưỡng
            detail=""
            if adv=="mention_spam": detail=f" (≥{advs['mention_limit']} mentions)"
            elif adv=="caps": detail=f" (≥{advs['caps_min']} ký tự, {advs['caps_percent']}% caps)"
            elif adv=="emoji_spam": detail=f" (≥{advs['emoji_limit']} emoji)"
            elif adv=="duplicate": detail=f" (≥{advs['duplicate_limit']} lần)"
            elif adv=="zalgo": detail=f" (≥{advs['zalgo_limit']} dấu)"
            elif adv=="link": detail=" (không trong whitelist)" if advs['link_whitelist'] else ""
            elif adv=="invite": detail=" (invite_allow_own="+str(advs['invite_allow_own'])+")"
            return await ctx.send(t(ctx.guild, "AUTOMOD_TEST_BLOCKED_ADV", adv=adv, detail=detail), ephemeral=True)
        await ctx.send(t(ctx.guild, "AUTOMOD_TEST_CLEAN"), ephemeral=True)

async def setup(bot: commands.Bot):
    await bot.add_cog(AutoModCog(bot))
