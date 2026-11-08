import os
import sys
import time
import random
from datetime import datetime, timezone, timedelta
from typing import Optional, Tuple, List, Dict, Any

import discord
from discord.ext import commands
from discord import app_commands

from config import OWNER_ID
from Checks_vi.i18n import t, get_guild_language
from data.database import get_user_data, update_user_coins, get_user_currency
VN_TZ = timezone(timedelta(hours=7))

# =============================================================================
# HỆ THỐNG DANH MỤC VẬT PHẨM HÔN NHÂN & BẤT ĐỘNG SẢN
# =============================================================================

RING_IDS = ["ring_bronze", "ring_silver", "ring_gold", "ring_diamond"]

RING_INFO = {
    "ring_bronze": {
        "id": "ring_bronze",
        "name": "💍 Nhẫn Đồng Đôi",
        "price": 2500670,
        "buff_affection": 0,
        "emoji": "💍",
        "color": 0xcd7f32,
        "desc": "Nhẫn khởi đầu kết đôi hạnh phúc trong hệ thống hôn nhân."
    },
    "ring_silver": {
        "id": "ring_silver",
        "name": "💍 Nhẫn Bạc Tình Yêu",
        "price": 15000870,
        "buff_affection": 10,  # +10% điểm tình cảm
        "emoji": "💍",
        "color": 0xc0c0c0,
        "desc": "Nhẫn bạc tinh tế, tăng +10% điểm tình cảm khi tương tác."
    },
    "ring_gold": {
        "id": "ring_gold",
        "name": "💍 Nhẫn Vàng Vĩnh Cửu",
        "price": 75009800,
        "buff_affection": 25,  # +25% điểm tình cảm
        "emoji": "💍",
        "color": 0xffd700,
        "desc": "Nhẫn vàng sang trọng, tăng +25% điểm tình cảm khi tương tác."
    },
    "ring_diamond": {
        "id": "ring_diamond",
        "name": "💎 Nhẫn Kim Cương",
        "price": 500000000,
        "buff_affection": 50,  # +50% điểm tình cảm
        "emoji": "💎",
        "color": 0x00ffff,
        "desc": "Nhẫn kim cương huyền thoại, tăng +50% điểm tình cảm & mở khóa thiệp cưới VIP."
    }
}

PROPERTY_INFO = {
    "house_small": {
        "id": "house_small",
        "name": "🏡 Nhà Nhỏ Tổ Ấm",
        "tax": 1000000,
        "value": 500000000,
        "bonus_cap": 0,
        "bonus_buff": 10,
        "desc": "Tổ ấm bình yên, tăng +10% điểm tình cảm khi tương tác."
    },
    "house_villa": {
        "id": "house_villa",
        "name": "🏘️ Biệt Thự Hạnh Phúc",
        "tax": 10000000,
        "value": 5000000000,
        "bonus_cap": 2,
        "bonus_buff": 25,
        "desc": "Không gian đẳng cấp, tăng +25% điểm tình cảm & thêm +2 lượt tương tác/ngày."
    },
    "house_island": {
        "id": "house_island",
        "name": "🏝️ Đảo Riêng Tư",
        "tax": 50000000,
        "value": 250000000000,
        "bonus_cap": 4,
        "bonus_buff": 50,
        "desc": "Thiên đường tình yêu riêng tư, tăng +50% tình cảm, +4 lượt tương tác/ngày."
    }
}

LOVE_ITEMS = {
    "love_chocolate": {"name": "🍫 Socola Tình Yêu", "pts": 2, "cost": 5000},
    "love_flower": {"name": "💐 Bó Hoa Lãng Mạn", "pts": 5, "cost": 12000},
    "love_teddy": {"name": "🧸 Gấu Bông Ôm Ấp", "pts": 10, "cost": 30000},
    "love_date": {"name": "🕯️ Vé Hẹn Hò Lãng Mạn", "pts": 20, "cost": 80000}
}

# =============================================================================
# HELPER FUNCTIONS (TRUY VẤN VÀ ĐỒNG BỘ DỮ LIỆU)
# =============================================================================

def _pair_key(guild_id: int, a: int, b: int) -> str:
    """Tạo key duy nhất cho cặp đôi trong cùng máy chủ theo thứ tự ID."""
    x, y = sorted((int(a), int(b)))
    return f"{guild_id}:{x}:{y}"


def _get_couple(guild_id: int, a: int, b: int) -> Optional[dict]:
    """Lấy dữ liệu cặp đôi theo Guild ID và ID 2 người."""
    import Command_vi.command_fishing as cf
    return cf.fishing_state.setdefault("couples", {}).get(_pair_key(guild_id, a, b))


def _get_user_couple(guild_id: int, uid: int) -> Tuple[Optional[str], Optional[dict]]:
    """Tìm cặp đôi của một người trong máy chủ cụ thể."""
    import Command_vi.command_fishing as cf
    for key, data in cf.fishing_state.setdefault("couples", {}).items():
        if not key.startswith(f"{guild_id}:"):
            continue
        if int(uid) in (int(data.get("a", 0)), int(data.get("b", 0))):
            return key, data
    return None, None


def get_user_fishing(user_id: int) -> dict:
    """Truy xuất túi đồ/thông tin câu cá của user từ command_fishing."""
    import Command_vi.command_fishing as cf
    return cf.get_user_fishing(user_id)


def save_fishing_data():
    """Lưu dữ liệu câu cá và hôn nhân vào file."""
    import Command_vi.command_fishing as cf
    return cf.save_fishing_data()


class _FishingStateProxy(dict):
    """Proxy truy xuất động dict fishing_state từ command_fishing để đồng bộ và tránh circular import."""
    @property
    def _target(self) -> dict:
        import Command_vi.command_fishing as cf
        return cf.fishing_state

    def __getitem__(self, key):
        return self._target[key]

    def __setitem__(self, key, value):
        self._target[key] = value

    def __delitem__(self, key):
        del self._target[key]

    def __contains__(self, key):
        return key in self._target

    def __len__(self):
        return len(self._target)

    def __iter__(self):
        return iter(self._target)

    def get(self, key, default=None):
        return self._target.get(key, default)

    def setdefault(self, key, default=None):
        return self._target.setdefault(key, default)

    def pop(self, key, default=None):
        return self._target.pop(key, default)

    def items(self):
        return self._target.items()

    def keys(self):
        return self._target.keys()

    def values(self):
        return self._target.values()

    def update(self, *args, **kwargs):
        return self._target.update(*args, **kwargs)

    def clear(self):
        return self._target.clear()


fishing_state = _FishingStateProxy()


def __getattr__(name: str):
    """Truy xuất động các thành phần dùng chung từ command_fishing để tránh circular import."""
    if name in ("fishing_state", "save_fishing_data", "get_user_fishing", "UTILITY_ITEMS"):
        import Command_vi.command_fishing as cf
        return getattr(cf, name)
    raise AttributeError(f"module '{__name__}' has no attribute '{name}'")


def _get_user_ring_count(user_id: int, ring_id: str) -> int:
    """Kiểm tra số lượng nhẫn trong túi đồ câu cá/kho của user."""
    inv = get_user_fishing(user_id)
    items = inv.setdefault("items", {})
    return int(items.get(ring_id, 0))


def _deduct_ring(user_id: int, ring_id: str) -> bool:
    """Trừ 1 chiếc nhẫn khi gửi lời cầu hôn."""
    inv = get_user_fishing(user_id)
    items = inv.setdefault("items", {})
    if int(items.get(ring_id, 0)) >= 1:
        items[ring_id] -= 1
        save_fishing_data()
        return True
    return False


def _refund_ring(user_id: int, ring_id: str):
    """Hoàn trả lại nhẫn cho người cầu hôn nếu bị từ chối hoặc hết hạn."""
    inv = get_user_fishing(user_id)
    items = inv.setdefault("items", {})
    items[ring_id] = int(items.get(ring_id, 0)) + 1
    save_fishing_data()


def _get_daily_love_cap(couple: dict) -> int:
    """Lấy số lượt tương tác tình cảm tối đa mỗi ngày (cơ bản 6 + bonus từ nhà)."""
    base_cap = 6
    props = couple.get("properties", [])
    for p in props:
        bonus = PROPERTY_INFO.get(p, {}).get("bonus_cap", 0)
        base_cap += bonus
    return base_cap


async def _trigger_marriage_achievements(guild_id: int, proposer_id: int, target_id: int, channel: Optional[discord.abc.Messageable] = None):
    """Kích hoạt thành tựu đám cưới cho cặp đôi mới cưới."""
    try:
        from Command_vi.achievement_system import unlock_achievement
        await unlock_achievement(guild_id, proposer_id, "marry_propose", channel)
        await unlock_achievement(guild_id, proposer_id, "marry_wedding", channel)
        await unlock_achievement(guild_id, target_id, "marry_wedding", channel)
    except Exception as e:
        print(f"[Marriage] ⚠️ Lỗi trao thành tựu đám cưới: {e}")


async def _check_duration_achievements(guild_id: int, couple: dict, channel: Optional[discord.abc.Messageable] = None):
    """Kiểm tra và trao thưởng các mốc kỷ niệm ngày cưới (7 ngày, 30 ngày, 100 ngày)."""
    try:
        from Command_vi.achievement_system import unlock_achievement
        now = time.time()
        married_at = float(couple.get("married_at", now))
        days = int((now - married_at) // 86400)
        a, b = int(couple.get("a", 0)), int(couple.get("b", 0))

        if days >= 7:
            await unlock_achievement(guild_id, a, "marry_days_7", channel)
            await unlock_achievement(guild_id, b, "marry_days_7", channel)
        if days >= 30:
            await unlock_achievement(guild_id, a, "marry_days_30", channel)
            await unlock_achievement(guild_id, b, "marry_days_30", channel)
        if days >= 100:
            await unlock_achievement(guild_id, a, "marry_days_100", channel)
            await unlock_achievement(guild_id, b, "marry_days_100", channel)
    except Exception as e:
        print(f"[Marriage] ⚠️ Lỗi trao mốc thành tựu kỷ niệm: {e}")


# =============================================================================
# GIAO DIỆN CHUẨN BỊ & CẦU HÔN (VIEWS)
# =============================================================================

class WeddingSetupView(discord.ui.View):
    """
    Giao diện chuẩn bị đám cưới hiện đại:
    - Hỗ trợ UserSelect chọn bất kỳ ai trong server (không bị giới hạn 25 thành viên cache)
    - Chọn nhẫn cưới trực quan
    - Chọn công khai hoặc cầu hôn ẩn qua DM
    """
    def __init__(self, cog, author: discord.Member, preselected_target: Optional[discord.Member] = None):
        super().__init__(timeout=180)
        self.cog = cog
        self.author = author
        self.target: Optional[discord.Member] = preselected_target
        self.ring_id: str = "ring_bronze"
        self.public: bool = True
        self.blesser_id: Optional[int] = None

        # 1. Nếu chưa có người được chọn, thêm UserSelect
        if not self.target:
            self.user_select = discord.ui.UserSelect(
                placeholder="💞 Chọn người thương trong server để cầu hôn...",
                min_values=1,
                max_values=1,
                row=0
            )
            self.user_select.callback = self._on_user_select
            self.add_item(self.user_select)

        # 2. Chọn nhẫn cưới
        ring_options = []
        for r_id in RING_IDS:
            info = RING_INFO[r_id]
            owned_cnt = _get_user_ring_count(author.id, r_id)
            status_txt = f"(Có x{owned_cnt})" if owned_cnt > 0 else f"(Chưa có - {info['price']:,}🪙)"
            ring_options.append(discord.SelectOption(
                label=f"{info['name']} {status_txt}"[:100],
                value=r_id,
                description=info["desc"][:100],
                emoji=info["emoji"],
                default=(r_id == self.ring_id)
            ))

        self.ring_select = discord.ui.Select(
            placeholder="💍 Chọn nhẫn cưới...",
            options=ring_options,
            row=1
        )
        self.ring_select.callback = self._on_ring_select
        self.add_item(self.ring_select)

        # 3. Nút bật tắt công khai
        self.visibility_btn = discord.ui.Button(
            label="Chế độ: Công khai",
            emoji="📣",
            style=discord.ButtonStyle.secondary,
            row=2
        )
        self.visibility_btn.callback = self._toggle_visibility
        self.add_item(self.visibility_btn)

        # 4. Nút gửi lời cầu hôn
        self.submit_btn = discord.ui.Button(
            label="Gửi Lời Cầu Hôn",
            emoji="💌",
            style=discord.ButtonStyle.success,
            row=2,
            disabled=(self.target is None)
        )
        self.submit_btn.callback = self._on_submit
        self.add_item(self.submit_btn)

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id != self.author.id:
            await interaction.response.send_message("❌ Chỉ người tạo bảng chuẩn bị lễ cưới mới được thao tác!", ephemeral=True)
            return False
        return True

    def build_embed(self) -> discord.Embed:
        ring = RING_INFO[self.ring_id]
        owned = _get_user_ring_count(self.author.id, self.ring_id)
        ring_status = f"✅ Đang có **x{owned}** trong túi" if owned > 0 else f"⚠️ Chưa có! Mua tại shop với giá **{ring['price']:,}🪙**"

        embed = discord.Embed(
            title="💒 CHUẨN BỊ LỄ CƯỚI & CẦU HÔN",
            description=f"Hãy chuẩn bị những điều ngọt ngào nhất để gửi đến người bạn yêu thương.",
            color=ring["color"]
        )
        embed.add_field(name="🤵 Người Cầu Hôn", value=self.author.mention, inline=True)
        embed.add_field(name="👰 Đối Phương", value=self.target.mention if self.target else "*Chưa chọn (Dùng menu bên dưới)*", inline=True)
        embed.add_field(name="💍 Nhẫn Đã Chọn", value=f"**{ring['name']}**\n{ring_status}", inline=False)
        embed.add_field(name="📣 Hình Thức Công Bố", value="📢 **Công khai trên kênh**" if self.public else "🔒 **Gửi riêng qua DM**", inline=True)
        embed.add_field(name="✨ Đặc Quyền Nhẫn", value=f"• Buff tình cảm: **+{ring['buff_affection']}%**", inline=True)
        embed.set_footer(text="SakuraBot Marriage System • Nhẫn sẽ chỉ được trừ khi gửi lời cầu hôn và được hoàn lại nếu từ chối.")
        if self.target and self.target.display_avatar:
            embed.set_thumbnail(url=self.target.display_avatar.url)
        return embed

    async def _on_user_select(self, interaction: discord.Interaction):
        selected_user = self.user_select.values[0]
        # Lấy member trong guild
        member = interaction.guild.get_member(selected_user.id) or selected_user
        if member.id == self.author.id:
            return await interaction.response.send_message("❌ Bạn không thể tự cầu hôn chính mình!", ephemeral=True)
        if getattr(member, "bot", False):
            return await interaction.response.send_message("❌ Bạn không thể kết hôn với Bot!", ephemeral=True)

        self.target = member
        self.submit_btn.disabled = False
        await interaction.response.edit_message(embed=self.build_embed(), view=self)

    async def _on_ring_select(self, interaction: discord.Interaction):
        self.ring_id = self.ring_select.values[0]
        await interaction.response.edit_message(embed=self.build_embed(), view=self)

    async def _toggle_visibility(self, interaction: discord.Interaction):
        self.public = not self.public
        self.visibility_btn.label = "Chế độ: Công khai" if self.public else "Chế độ: Ẩn (DM)"
        await interaction.response.edit_message(embed=self.build_embed(), view=self)

    async def _on_submit(self, interaction: discord.Interaction):
        if not self.target:
            return await interaction.response.send_message("❌ Vui lòng chọn đối tượng cầu hôn trước!", ephemeral=True)

        gid = interaction.guild_id
        # Kiểm tra trạng thái hôn nhân hiện tại
        if _get_user_couple(gid, self.author.id)[1]:
            return await interaction.response.send_message("❌ Bạn đang trong một cuộc hôn nhân! Cần ly hôn trước nếu muốn kết hôn với người khác.", ephemeral=True)
        if _get_user_couple(gid, self.target.id)[1]:
            return await interaction.response.send_message(f"❌ {self.target.display_name} hiện đã kết hôn với người khác!", ephemeral=True)

        # Kiểm tra và trừ nhẫn cưới
        ring = RING_INFO[self.ring_id]
        if not _deduct_ring(self.author.id, self.ring_id):
            return await interaction.response.send_message(
                f"❌ Bạn không có **{ring['name']}** trong túi đồ! Vui lòng ghé shop mua với giá `{ring['price']:,}` coin.",
                ephemeral=True
            )

        # Tạo Proposal View gửi tới đối phương
        prop_view = WeddingProposalView(self.cog, self.author, self.target, self.ring_id, self.blesser_id, self.public, gid)
        proposal_embed = prop_view.build_proposal_embed()

        if self.public:
            sent_msg = await interaction.channel.send(
                content=f"💌 {self.target.mention}, bạn vừa nhận được lời cầu hôn từ {self.author.mention}!",
                embed=proposal_embed,
                view=prop_view,
                allowed_mentions=discord.AllowedMentions(users=True)
            )
            prop_view.message = sent_msg
            await interaction.response.send_message("💌 Đã gửi lời cầu hôn công khai! Đang chờ đối phương mở lời đồng ý...", ephemeral=True)
        else:
            try:
                sent_msg = await self.target.send(
                    content=f"💌 **Lời Cầu Hôn Bí Mật:** {self.author.display_name} vừa gửi lời cầu hôn riêng tư tới bạn!",
                    embed=proposal_embed,
                    view=prop_view
                )
                prop_view.message = sent_msg
                await interaction.response.send_message(f"💌 Đã gửi lời cầu hôn kín đáo tới DM của **{self.target.display_name}**!", ephemeral=True)
            except discord.Forbidden:
                # Hoàn trả lại nhẫn nếu không gửi được DM
                _refund_ring(self.author.id, self.ring_id)
                return await interaction.response.send_message(
                    "❌ Không thể gửi tin nhắn DM cho đối phương (Chặn tin nhắn người lạ). **Chiếc nhẫn cưới đã được hoàn trả lại vào túi đồ của bạn!**",
                    ephemeral=True
                )


class WeddingProposalView(discord.ui.View):
    """
    Giao diện nhận lời cầu hôn:
    - [Đồng ý] -> Xác nhận kết hôn, lưu database, mở khóa thành tựu.
    - [Từ chối] -> Hoàn trả lại nhẫn cưới 100% cho người cầu hôn.
    - [Timeout] -> Hoàn trả lại nhẫn cưới nếu hết hạn mà không phản hồi.
    """
    def __init__(self, cog, proposer: discord.Member, target: discord.Member, ring_id: str, blesser_id: Optional[int], public: bool, guild_id: int):
        super().__init__(timeout=86400) # Cho phép phản hồi trong 24 giờ
        self.cog = cog
        self.proposer = proposer
        self.target = target
        self.ring_id = ring_id
        self.blesser_id = blesser_id
        self.public = public
        self.guild_id = guild_id
        self.message: Optional[discord.Message] = None
        self.resolved: bool = False

    def build_proposal_embed(self) -> discord.Embed:
        ring = RING_INFO.get(self.ring_id, RING_INFO["ring_bronze"])
        embed = discord.Embed(
            title="💍 THIỆP CẦU HÔN TRỌNG ĐẠI 💍",
            description=(
                f"{self.proposer.mention} đã trao gửi chiếc **{ring['name']}** lấp lánh và muốn cùng {self.target.mention} "
                f"viết nên câu chuyện tình yêu vĩnh hằng trên SakuraBot!\n\n"
                f"💖 **Bạn có đồng ý nhận lời và trở thành một nửa của nhau?**\n"
                f"• Chế độ: {'📢 Công khai' if self.public else '🔒 Riêng tư (DM)'}\n"
                f"• Hiệu ứng nhẫn: `+{ring['buff_affection']}%` điểm tình cảm"
            ),
            color=ring["color"]
        )
        if self.proposer.display_avatar:
            embed.set_author(name=f"Lời cầu hôn từ {self.proposer.display_name}", icon_url=self.proposer.display_avatar.url)
        if self.target.display_avatar:
            embed.set_thumbnail(url=self.target.display_avatar.url)
        embed.set_footer(text="Lời cầu hôn có hiệu lực trong 24 giờ • Hãy nhấn nút bên dưới để phản hồi.")
        return embed

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id != self.target.id:
            await interaction.response.send_message("❌ Chỉ người nhận được lời cầu hôn mới có quyền phản hồi!", ephemeral=True)
            return False
        return True

    @discord.ui.button(label="Đồng Ý Kết Hôn", emoji="💍", style=discord.ButtonStyle.success)
    async def accept(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.resolved = True
        gid = self.guild_id

        # Kiểm tra lại xem trong lúc chờ có ai kết hôn với người khác không
        if _get_user_couple(gid, self.proposer.id)[1] or _get_user_couple(gid, self.target.id)[1]:
            _refund_ring(self.proposer.id, self.ring_id)
            for child in self.children:
                child.disabled = True
            await interaction.response.edit_message(content="💔 Hôn lễ bị hủy do một trong hai người đã có hôn nhân khác trong thời gian chờ.", embed=None, view=self)
            return

        guild = self.cog.bot.get_guild(self.guild_id)
        blesser = guild.get_member(self.blesser_id) if (self.blesser_id and guild) else None
        if blesser is None and guild:
            candidates = [m for m in guild.members if not m.bot and m.id not in (self.proposer.id, self.target.id)]
            blesser = random.choice(candidates) if candidates else None

        key = _pair_key(gid, self.proposer.id, self.target.id)
        now = time.time()
        couple_data = {
            "guild_id": gid,
            "a": self.proposer.id,
            "b": self.target.id,
            "ring": self.ring_id,
            "married_at": now,
            "public": self.public,
            "affection": 10,  # Điểm tình cảm khởi đầu
            "weekly": {},
            "monthly": {},
            "daily": {},
            "common_coins": 0,
            "properties": [],
            "blesser": blesser.id if blesser else None,
            "tax_paid_at": now
        }

        # Lưu dữ liệu đồng bộ
        fishing_state.setdefault("couples", {})[key] = couple_data
        fishing_state.setdefault("marriages", {})[str(self.proposer.id)] = self.target.id
        fishing_state["marriages"][str(self.target.id)] = self.proposer.id
        save_fishing_data()

        ring = RING_INFO.get(self.ring_id, RING_INFO["ring_bronze"])
        for child in self.children:
            child.disabled = True

        # Embed chứng nhận kết hôn đẹp mắt
        cert_embed = discord.Embed(
            title="💒 HÔN LỄ THÀNH CÔNG · GIẤY CHỨNG NHẬN KẾT HÔN 💒",
            description=(
                f"🎉 **Chúc mừng đôi uyên ương mới của máy chủ!**\n\n"
                f"🤵 **Tân lang / Chồng:** {self.proposer.mention}\n"
                f"👰 **Tân nương / Vợ:** {self.target.mention}\n"
                f"💍 **Tín vật định tình:** **{ring['name']}**\n"
                f"🎉 **Người chứng hôn & chúc phúc:** {blesser.mention if blesser else 'Toàn thể cư dân server'}\n"
                f"🕒 **Ngày nên duyên:** <t:{int(now)}:F>\n\n"
                f"💌 *Hãy cùng nhau bồi đắp tình cảm mỗi ngày qua các lệnh `/cplove`, `/giftlove`, tạo quỹ chung `/couplecoin` và sắm tổ ấm `/couplehouse`!*"
            ),
            color=discord.Color.from_rgb(255, 105, 180),
            timestamp=datetime.now(timezone.utc)
        )
        if self.target.display_avatar:
            cert_embed.set_thumbnail(url=self.target.display_avatar.url)
        cert_embed.set_footer(text="🌸 SakuraBot Marriage • Chúc hai bạn trăm năm hạnh phúc!")

        await interaction.response.edit_message(content=None, embed=cert_embed, view=self)

        # Mở khóa thành tựu
        await _trigger_marriage_achievements(gid, self.proposer.id, self.target.id, interaction.channel)

        if self.public:
            try:
                await interaction.channel.send(
                    f"🎊 **TIN VUI:** {self.proposer.mention} và {self.target.mention} đã chính thức về chung một nhà! Hãy gửi lời chúc mừng tới cặp đôi mới nào! 💖🥂"
                )
            except Exception:
                pass

    @discord.ui.button(label="Từ Chối", emoji="💔", style=discord.ButtonStyle.danger)
    async def reject(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.resolved = True
        # HOÀN TRẢ NHẪN CƯỚI CHO PROPOSER
        _refund_ring(self.proposer.id, self.ring_id)
        for child in self.children:
            child.disabled = True

        ring = RING_INFO.get(self.ring_id, RING_INFO["ring_bronze"])
        await interaction.response.edit_message(
            content=f"💔 **Lời cầu hôn đã bị từ chối.** Chiếc **{ring['name']}** đã được hoàn trả lại cho {self.proposer.mention}.",
            embed=None,
            view=self
        )

    async def on_timeout(self):
        if not self.resolved:
            self.resolved = True
            # HOÀN TRẢ NHẪN KHI HẾT THỜI GIAN CHỜ
            _refund_ring(self.proposer.id, self.ring_id)
            for child in self.children:
                child.disabled = True
            if self.message:
                try:
                    ring = RING_INFO.get(self.ring_id, RING_INFO["ring_bronze"])
                    await self.message.edit(
                        content=f"⌛ Lời cầu hôn đã hết thời hạn 24 giờ mà chưa nhận được phản hồi. **Chiếc {ring['name']} đã được hoàn trả về túi đồ.**",
                        view=self
                    )
                except Exception:
                    pass


# =============================================================================
# GIAO DIỆN HỒ SƠ CẶP ĐÔI & TƯƠNG TÁC (VIEWS)
# =============================================================================

class CoupleActionsView(discord.ui.View):
    """Bảng điều khiển tương tác nhanh của cặp đôi."""
    def __init__(self, cog, guild_id: int, key: str, couple: dict):
        super().__init__(timeout=600)
        self.cog = cog
        self.guild_id = guild_id
        self.key = key

    @discord.ui.button(label="Làm Mới", emoji="🔄", style=discord.ButtonStyle.primary, row=0)
    async def refresh_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        couple = fishing_state.setdefault("couples", {}).get(self.key)
        if not couple:
            return await interaction.response.send_message("❌ Hôn nhân không còn tồn tại.", ephemeral=True)
        embed = self.cog.build_couple_embed(interaction.guild, self.key, couple)
        await interaction.response.edit_message(embed=embed, view=self)

    @discord.ui.button(label="Yêu Thương", emoji="💗", style=discord.ButtonStyle.success, row=0)
    async def love_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        couple = fishing_state.setdefault("couples", {}).get(self.key)
        if not couple:
            return await interaction.response.send_message("❌ Hôn nhân không còn tồn tại.", ephemeral=True)
        a, b = int(couple["a"]), int(couple["b"])
        if interaction.user.id not in (a, b):
            return await interaction.response.send_message("❌ Chỉ vợ hoặc chồng mới có thể bồi dưỡng tình cảm!", ephemeral=True)

        today = datetime.now(VN_TZ).date().isoformat()
        daily = couple.setdefault("daily", {})
        used = int(daily.get(today, 0))
        max_cap = _get_daily_love_cap(couple)

        if used >= max_cap:
            return await interaction.response.send_message(f"🌙 Hai bạn đã dùng hết `{max_cap}/{max_cap}` lượt tình cảm hôm nay. Hãy quay lại ngày mai!", ephemeral=True)

        ring = RING_INFO.get(couple.get("ring"), RING_INFO["ring_bronze"])
        buff_pct = ring.get("buff_affection", 0)
        base_gain = 2
        bonus_pts = round(base_gain * (1 + buff_pct / 100))

        couple["affection"] = int(couple.get("affection", 0)) + bonus_pts
        daily[today] = used + 1

        wk = datetime.now(VN_TZ).strftime("%G-W%V")
        mo = datetime.now(VN_TZ).strftime("%Y-%m")
        couple.setdefault("weekly", {})[wk] = int(couple.setdefault("weekly", {}).get(wk, 0)) + bonus_pts
        couple.setdefault("monthly", {})[mo] = int(couple.setdefault("monthly", {}).get(mo, 0)) + bonus_pts
        save_fishing_data()

        await interaction.response.send_message(
            f"💗 **Tình yêu đơm hoa kết trái!** Điểm tình cảm +{bonus_pts} (Buff nhẫn: +{buff_pct}%). Lượt hôm nay: `{used + 1}/{max_cap}`.",
            ephemeral=True
        )

    @discord.ui.button(label="Chứng Nhận", emoji="📜", style=discord.ButtonStyle.secondary, row=0)
    async def certificate_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        couple = fishing_state.setdefault("couples", {}).get(self.key)
        if not couple:
            return await interaction.response.send_message("❌ Hôn nhân không còn tồn tại.", ephemeral=True)
        now = time.time()
        m_at = float(couple.get("married_at", now))
        days = int((now - m_at) // 86400)
        a, b = int(couple["a"]), int(couple["b"])
        ring = RING_INFO.get(couple.get("ring"), RING_INFO["ring_bronze"])

        embed = discord.Embed(
            title="📜 GIẤY CHỨNG NHẬN KẾT HÔN ĐIỆN TỬ",
            description=(
                f"Đã được SakuraBot ghi nhận vào sổ bộ máy chủ **{interaction.guild.name}**.\n\n"
                f"💑 **Cặp Đôi:** <@{a}> ❤️ <@{b}>\n"
                f"💍 **Tín Vật:** {ring['name']}\n"
                f"📅 **Ngày Kết Hôn:** <t:{int(m_at)}:F>\n"
                f"⏳ **Thời Gian Bên Nhau:** **{days} ngày**\n"
                f"💖 **Điểm Tình Cảm:** **{int(couple.get('affection', 0)):,}** điểm"
            ),
            color=ring["color"]
        )
        embed.set_footer(text="SakuraBot Official Registry Certificate")
        await interaction.response.send_message(embed=embed, ephemeral=True)


class DivorceConsentView(discord.ui.View):
    """
    Giao diện xử lý ly hôn:
    - [Đồng ý] -> Giải trừ quan hệ, chia đều hoặc chuyển giao tài sản.
    - [Không đồng ý] -> Giữ nguyên cuộc hôn nhân.
    """
    def __init__(self, requester_id: int, partner_id: int, key: str, mode: str, guild_id: int):
        super().__init__(timeout=86400)
        self.requester_id = requester_id
        self.partner_id = partner_id
        self.key = key
        self.mode = mode
        self.guild_id = guild_id

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id != self.partner_id:
            await interaction.response.send_message("❌ Chỉ người còn lại trong cuộc hôn nhân mới có quyền đồng ý ly hôn!", ephemeral=True)
            return False
        return True

    @discord.ui.button(label="Đồng Ý Ly Hôn", emoji="💔", style=discord.ButtonStyle.danger)
    async def consent(self, interaction: discord.Interaction, button: discord.ui.Button):
        couple = fishing_state.setdefault("couples", {}).get(self.key)
        if not couple:
            return await interaction.response.send_message("❌ Hôn nhân không còn tồn tại.", ephemeral=True)

        properties = list(couple.get("properties", []))
        coins = int(couple.get("common_coins", 0))

        # Phân chia tài sản
        if self.mode in ("divide", "court"):
            share_req = coins // 2
            share_part = coins - share_req
            if share_req > 0:
                await update_user_coins(self.guild_id, self.requester_id, share_req)
            if share_part > 0:
                await update_user_coins(self.guild_id, self.partner_id, share_part)
        elif self.mode == "leave_empty":
            # Ra đi tay trắng: toàn bộ quỹ chung chuyển cho đối phương
            if coins > 0:
                await update_user_coins(self.guild_id, self.partner_id, coins)

        a, b = int(couple["a"]), int(couple["b"])
        fishing_state["couples"].pop(self.key, None)
        fishing_state.setdefault("marriages", {}).pop(str(a), None)
        fishing_state["marriages"].pop(str(b), None)
        save_fishing_data()

        for child in self.children:
            child.disabled = True

        mode_name = "Chia đôi tài sản chung" if self.mode in ("divide", "court") else "Ra đi tay trắng"
        await interaction.response.edit_message(
            content=f"💔 **Cả hai bên đã chính thức ly hôn.** Thủ tục giải trừ hoàn tất (Phương án: **{mode_name}**).",
            embed=None,
            view=self
        )

    @discord.ui.button(label="Không Đồng Ý", emoji="🛑", style=discord.ButtonStyle.secondary)
    async def decline(self, interaction: discord.Interaction, button: discord.ui.Button):
        for child in self.children:
            child.disabled = True
        await interaction.response.edit_message(
            content="🛡️ **Đối phương không đồng ý ly hôn.** Hôn nhân vẫn được giữ nguyên. Nếu có tranh chấp, bạn có thể khởi kiện ra `/court`.",
            embed=None,
            view=self
        )


class CourtCaseView(discord.ui.View):
    """Giao diện tòa án hôn nhân do Chủ Server chủ tọa."""
    def __init__(self, case_id: str):
        super().__init__(timeout=604800)
        self.case_id = case_id

    @discord.ui.button(label="Chấp Thuận Phán Quyết", emoji="⚖️", style=discord.ButtonStyle.success)
    async def decide(self, interaction: discord.Interaction, button: discord.ui.Button):
        case = fishing_state.setdefault("court_cases", {}).get(self.case_id)
        if not case or not interaction.guild or interaction.user.id != interaction.guild.owner_id:
            return await interaction.response.send_message("❌ Chỉ Chủ sở hữu Server mới có quyền chủ tọa và ra phán quyết!", ephemeral=True)

        couple = fishing_state.setdefault("couples", {}).get(case["couple_key"])
        if not couple:
            return await interaction.response.send_message("❌ Hôn nhân không còn tồn tại.", ephemeral=True)

        if case.get("type") == "divorce":
            case["status"] = "approved_by_court"
            case["judged_by"] = interaction.user.id
            save_fishing_data()
            view = DivorceConsentView(case["plaintiff"], case["defendant"], case["couple_key"], "court", interaction.guild_id)
            await interaction.response.send_message(
                f"⚖️ **Tòa đã phê chuẩn đơn ly hôn.** Gửi xác nhận phân chia tài sản cho <@{case['defendant']}>.",
                view=view,
                ephemeral=False
            )
        else:
            case["status"] = "resolved"
            case["judged_by"] = interaction.user.id
            save_fishing_data()
            for child in self.children:
                child.disabled = True
            await interaction.response.edit_message(content=f"⚖️ Vụ việc `{self.case_id}` đã được Chủ tọa xử lý xong.", embed=None, view=self)

    @discord.ui.button(label="Bác Đơn / Đóng Vụ", emoji="🛑", style=discord.ButtonStyle.danger)
    async def reject(self, interaction: discord.Interaction, button: discord.ui.Button):
        case = fishing_state.setdefault("court_cases", {}).get(self.case_id)
        if not case or not interaction.guild or interaction.user.id != interaction.guild.owner_id:
            return await interaction.response.send_message("❌ Chỉ Chủ sở hữu Server mới có quyền phán quyết!", ephemeral=True)

        case["status"] = "rejected"
        save_fishing_data()
        for child in self.children:
            child.disabled = True
        await interaction.response.edit_message(content=f"⚖️ Chủ tọa đã bác bỏ đơn vụ kiện `{self.case_id}`.", embed=None, view=self)


class PairingView(discord.ui.View):
    """Giao diện ghép đôi ngẫu nhiên đường phố."""
    def __init__(self, first_id: int, second_id: int, guild_id: int):
        super().__init__(timeout=86400)
        self.first_id = first_id
        self.second_id = second_id
        self.guild_id = guild_id

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id not in (self.first_id, self.second_id):
            await interaction.response.send_message("❌ Chỉ hai người được ghép đôi mới có thể tương tác!", ephemeral=True)
            return False
        return True

    @discord.ui.button(label="Đồng Ý Tìm Hiểu", emoji="💞", style=discord.ButtonStyle.success)
    async def accept(self, interaction: discord.Interaction, button: discord.ui.Button):
        recs = fishing_state.setdefault("pairings", {})
        a = recs.get(str(self.first_id), {})
        b = recs.get(str(self.second_id), {})
        if not a or not b:
            return await interaction.response.send_message("❌ Lượt ghép đôi này đã hết hạn.", ephemeral=True)

        a["status"] = "matched"
        b["status"] = "matched"
        save_fishing_data()

        for child in self.children:
            child.disabled = True

        m1 = interaction.guild.get_member(self.first_id)
        m2 = interaction.guild.get_member(self.second_id)
        name1 = m1.mention if m1 else f"<@{self.first_id}>"
        name2 = m2.mention if m2 else f"<@{self.second_id}>"
        await interaction.response.edit_message(
            content=f"💞 **Duyên phận đã mở lối!** {name1} và {name2} đã đồng ý tìm hiểu nhau. Hãy cùng trò chuyện và tiến tới đám cưới bằng `/wedding`!",
            view=self
        )

    @discord.ui.button(label="Bỏ Qua", emoji="🙈", style=discord.ButtonStyle.secondary)
    async def decline(self, interaction: discord.Interaction, button: discord.ui.Button):
        fishing_state.setdefault("pairings", {}).pop(str(self.first_id), None)
        fishing_state.setdefault("pairings", {}).pop(str(self.second_id), None)
        save_fishing_data()

        for child in self.children:
            child.disabled = True
        await interaction.response.edit_message(content="💔 Lượt ghép đôi đã được hủy bỏ. Bạn có thể thử lại vào ngày mai.", view=self)


# =============================================================================
# COG CHÍNH: HỆ THỐNG HÔN NHÂN & GIA ĐÌNH (MARRIAGE COG)
# =============================================================================

class MarriageCog(commands.Cog, name="Marriage"):
    """
    🌸 Hệ thống Hôn Nhân, Tình Yêu & Gia Đình SakuraBot:
    - Cầu hôn với 4 cấp độ nhẫn cưới, bảo toàn 100% tài sản nhẫn nếu bị từ chối
    - Bồi đắp tình cảm cặp đôi, quỹ chung, mua sắm bất động sản
    - Tự động tích hợp thành tựu cưới & kỷ niệm 7, 30, 100 ngày
    - Hệ thống ghép đôi đường phố & Tòa án ly hôn văn minh
    """

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    def build_couple_embed(self, guild: discord.Guild, key: str, couple: dict) -> discord.Embed:
        """Tạo giao diện Embed hồ sơ hôn nhân chi tiết."""
        now = time.time()
        a, b = int(couple["a"]), int(couple["b"])
        ring = RING_INFO.get(couple.get("ring"), RING_INFO["ring_bronze"])
        m_at = float(couple.get("married_at", now))
        days = max(0, int((now - m_at) // 86400))
        affection = int(couple.get("affection", 0))
        coins = int(couple.get("common_coins", 0))
        props = couple.get("properties", [])
        props_str = ", ".join(PROPERTY_INFO.get(p, {}).get("name", p) for p in props) if props else "Chưa có bất động sản"

        tax_total = sum(PROPERTY_INFO.get(p, {}).get("tax", 0) for p in props)

        # Tính toán thanh đo độ thân mật (Progress bar)
        level = min(10, affection // 100 + 1)
        progress_in_lvl = affection % 100
        filled = min(10, progress_in_lvl // 10)
        bar = "💖" * filled + "🤍" * (10 - filled)

        embed = discord.Embed(
            title="💞 HỒ SƠ HÔN NHÂN & GIA ĐÌNH",
            description=f"Không gian ấm áp gắn kết của đôi lứa trên máy chủ **{guild.name}**.",
            color=ring["color"]
        )

        embed.add_field(
            name="💑 Đôi Uyên Ương",
            value=f"• <@{a}> 💗 <@{b}>\n• Ngày cưới: <t:{int(m_at)}:D> (**{days} ngày** bên nhau)",
            inline=False
        )

        embed.add_field(
            name="💍 Tín Vật Hôn Nhân",
            value=f"**{ring['name']}**\n• Buff tình cảm: `+{ring['buff_affection']}%`",
            inline=True
        )

        embed.add_field(
            name="🏦 Quỹ Tài Chính Chung",
            value=f"**{coins:,}** 🪙 Coins\n*(Dùng `/couplecoin` để nạp/rút)*",
            inline=True
        )

        embed.add_field(
            name=f"💖 Tình Cảm (Cấp {level})",
            value=f"**{affection:,}** điểm\n{bar} `{progress_in_lvl}/100`",
            inline=False
        )

        embed.add_field(
            name="🏡 Bất Động Sản & Gia Viên",
            value=f"• {props_str}\n• Chi phí bảo trì/thuế: `{tax_total:,}🪙/ngày`",
            inline=False
        )

        embed.set_footer(text="🌸 Dùng /cplove, /giftlove mỗi ngày để nâng cao chỉ số tình cảm!")
        return embed

    # --------------------------------------------------------------------------
    # NHÓM LỆNH HYBRID /marry (Tối ưu hóa Slash Commands)
    # --------------------------------------------------------------------------

    @commands.hybrid_group(name="marry", aliases=["honnhan"], description="Hệ thống hôn nhân & cặp đôi / Marriage & Couple system")
    @commands.guild_only()
    async def marry_group(self, ctx: commands.Context):
        """Hệ thống hôn nhân & cặp đôi."""
        if ctx.invoked_subcommand is None:
            await self.couple_cmd(ctx)

    @marry_group.command(name="wedding", description="Propose or prepare wedding / Cầu hôn hoặc chuẩn bị đám cưới")
    @app_commands.describe(member="Member you want to propose to / Người bạn muốn cầu hôn")
    async def marry_wedding(self, ctx: commands.Context, member: Optional[discord.Member] = None):
        await self.wedding_cmd(ctx, member)

    @marry_group.command(name="profile", aliases=["couple"], description="View couple profile / Xem hồ sơ hôn nhân")
    @app_commands.describe(member="Member whose marriage profile you want to view / Người cần xem hồ sơ")
    async def marry_profile(self, ctx: commands.Context, member: Optional[discord.Member] = None):
        await self.couple_cmd(ctx, member)

    # --------------------------------------------------------------------------
    # 1. LỆNH CẦU HÔN & ĐÁM CƯỚI (WEDDING / MARRY) - PREFIX
    # --------------------------------------------------------------------------

    @commands.command(name="wedding", aliases=["damcuoi", "cauhon"], description="Propose to someone or prepare a wedding / Cầu hôn hoặc chuẩn bị đám cưới")
    @commands.guild_only()
    async def wedding_cmd(self, ctx: commands.Context, member: Optional[discord.Member] = None):
        """Mở bảng chuẩn bị hôn lễ hoặc gửi lời cầu hôn trực tiếp tới một thành viên."""
        if member:
            if member.id == ctx.author.id:
                return await ctx.send("❌ Bạn không thể tự cầu hôn chính mình!", ephemeral=True)
            if member.bot:
                return await ctx.send("❌ Bạn không thể kết hôn với Bot!", ephemeral=True)
            if _get_user_couple(ctx.guild.id, ctx.author.id)[1]:
                return await ctx.send("❌ Bạn đang trong một cuộc hôn nhân! Hãy dùng `/divorce` nếu muốn giải trừ.", ephemeral=True)
            if _get_user_couple(ctx.guild.id, member.id)[1]:
                return await ctx.send(f"❌ **{member.display_name}** hiện đã kết hôn với người khác!", ephemeral=True)

        view = WeddingSetupView(self, ctx.author, preselected_target=member)
        embed = view.build_embed()
        await ctx.send(embed=embed, view=view)

    # --------------------------------------------------------------------------
    # 2. XEM HỒ SƠ HÔN NHÂN (COUPLE) - PREFIX
    # --------------------------------------------------------------------------

    @commands.command(name="couple", aliases=["capdoi"], description="View couple marriage profile & shared assets / Xem hồ sơ hôn nhân & tài sản chung")
    @commands.guild_only()
    async def couple_cmd(self, ctx: commands.Context, member: Optional[discord.Member] = None):
        """Xem thông tin chi tiết về hôn nhân, tình cảm, quỹ chung và bất động sản."""
        target_user = member or ctx.author
        key, couple = _get_user_couple(ctx.guild.id, target_user.id)

        if not couple:
            if target_user.id == ctx.author.id:
                return await ctx.send("💔 Bạn chưa kết hôn! Hãy dùng `/wedding` để cầu hôn người thương hoặc `/pairup` để tìm kiếm nửa kia ngẫu nhiên.", ephemeral=True)
            else:
                return await ctx.send(f"💔 **{target_user.display_name}** hiện vẫn đang độc thân!", ephemeral=True)

        a, b = int(couple["a"]), int(couple["b"])
        if not couple.get("public", True) and ctx.author.id not in (a, b) and ctx.author.id != OWNER_ID:
            return await ctx.send("🔒 Hồ sơ hôn nhân này đang được đặt ở chế độ riêng tư.", ephemeral=True)

        # Kiểm tra và trừ thuế bất động sản tự động từ quỹ chung
        now = time.time()
        last = float(couple.get("tax_paid_at", now))
        days_unpaid = int((now - last) // 86400)
        tax_daily = sum(PROPERTY_INFO.get(x, {}).get("tax", 0) for x in couple.get("properties", []))

        if days_unpaid > 0 and tax_daily > 0:
            due = days_unpaid * tax_daily
            current_funds = int(couple.get("common_coins", 0))
            paid = min(current_funds, due)
            couple["common_coins"] = current_funds - paid
            couple["tax_paid_at"] = last + days_unpaid * 86400
            save_fishing_data()

        # Kiểm tra và trao mốc thành tựu kỷ niệm 7, 30, 100 ngày
        await _check_duration_achievements(ctx.guild.id, couple, ctx.channel)

        embed = self.build_couple_embed(ctx.guild, key, couple)
        view = CoupleActionsView(self, ctx.guild.id, key, couple)
        await ctx.send(embed=embed, view=view)

    # --------------------------------------------------------------------------
    # 3. BỒI DƯỠNG TÌNH CẢM (CPLOVE / YEUTHUONG / CP_LOVE)
    # --------------------------------------------------------------------------

    @commands.command(name="cplove", aliases=["yeuthuong", "cp_love", "marrylove", "cpdate"], description="Express affection to your spouse / Thể hiện tình cảm với vợ/chồng")
    @commands.guild_only()
    async def love_cmd(self, ctx: commands.Context, member: Optional[discord.Member] = None, action: str = "love"):
        """Thể hiện tình cảm yêu thương với vợ hoặc chồng để tăng điểm tình cảm."""
        key, couple = _get_user_couple(ctx.guild.id, ctx.author.id)
        if not couple:
            return await ctx.send("💌 Bạn chưa kết hôn! Hãy kết đôi bằng lệnh `/wedding` trước.", ephemeral=True)

        a, b = int(couple["a"]), int(couple["b"])
        partner_id = b if ctx.author.id == a else a

        if member and member.id != partner_id:
            # Tán tỉnh người khác khi đang có gia đình bị trừ điểm
            couple["affection"] = max(0, int(couple.get("affection", 0)) - 2)
            save_fishing_data()
            return await ctx.send(f"💔 **Ghen tuông!** Bạn thể hiện tình cảm với người khác khiến điểm tình cảm gia đình bị trừ **2** điểm! Hiện còn `{couple['affection']}` điểm.")

        today = datetime.now(VN_TZ).date().isoformat()
        daily = couple.setdefault("daily", {})
        used = int(daily.get(today, 0))
        max_cap = _get_daily_love_cap(couple)

        if used >= max_cap:
            return await ctx.send(f"🌙 Hai bạn đã đạt giới hạn `{max_cap}/{max_cap}` lượt bồi đắp tình cảm hôm nay! Hãy quay lại vào ngày mai nhé.", ephemeral=True)

        act = action.lower().strip()
        bonus_base = {"kiss": 3, "love": 2, "hug": 2, "date": 5}.get(act, 2)

        # Tính buff từ nhẫn cưới và nhà
        ring = RING_INFO.get(couple.get("ring"), RING_INFO["ring_bronze"])
        buff_pct = ring.get("buff_affection", 0)
        for p in couple.get("properties", []):
            buff_pct += PROPERTY_INFO.get(p, {}).get("bonus_buff", 0)

        total_gain = round(bonus_base * (1 + buff_pct / 100))
        couple["affection"] = int(couple.get("affection", 0)) + total_gain
        daily[today] = used + 1

        wk = datetime.now(VN_TZ).strftime("%G-W%V")
        mo = datetime.now(VN_TZ).strftime("%Y-%m")
        couple.setdefault("weekly", {})[wk] = int(couple.setdefault("weekly", {}).get(wk, 0)) + total_gain
        couple.setdefault("monthly", {})[mo] = int(couple.setdefault("monthly", {}).get(mo, 0)) + total_gain
        save_fishing_data()

        act_labels = {
            "kiss": "trao một nụ hôn nồng cháy 💋",
            "hug": "ôm thật chặt vào lòng 🫂",
            "date": "cùng hẹn hò lãng mạn dưới ánh nến 🕯️",
            "love": "bày tỏ tình yêu chân thành 💖"
        }
        lbl = act_labels.get(act, "trao lời yêu thương 💗")

        partner_mention = f"<@{partner_id}>"
        await ctx.send(
            f"🌸 {ctx.author.mention} đã {lbl} tới {partner_mention}!\n"
            f"✨ Điểm tình cảm: **+{total_gain}** (Buff tổng: `+{buff_pct}%`) • Lượt hôm nay: `{used + 1}/{max_cap}`."
        )

    # --------------------------------------------------------------------------
    # 4. TẶNG QUÀ TÌNH YÊU (GIFTLOVE / TANGHOA / TANGQUA / LOVEGIFT)
    # --------------------------------------------------------------------------

    @commands.command(name="giftlove", aliases=["tanghoa", "lovegift", "cpgift", "tangqua"], description="Gift a romantic item to your spouse / Tặng quà tình cảm cho bạn đời")
    @commands.guild_only()
    async def giftlove_cmd(self, ctx: commands.Context, item: str = "love_flower", member: Optional[discord.Member] = None):
        """Tặng các vật phẩm tình yêu ngọt ngào để bồi dưỡng tình cảm vợ chồng."""
        item_id = item.lower().strip()
        if item_id not in LOVE_ITEMS:
            return await ctx.send(
                "❌ Vật phẩm không hợp lệ! Danh sách quà tặng: `love_chocolate` (🍫 Socola), `love_flower` (💐 Hoa hồng), `love_teddy` (🧸 Gấu bông), `love_date` (🕯️ Vé hẹn hò).",
                ephemeral=True
            )

        key, couple = _get_user_couple(ctx.guild.id, ctx.author.id)
        if not couple:
            return await ctx.send("💌 Bạn chưa kết hôn! Hãy kết hôn để cùng bồi đắp tổ ấm.", ephemeral=True)

        a, b = int(couple["a"]), int(couple["b"])
        partner_id = b if ctx.author.id == a else a
        if member and member.id != partner_id:
            return await ctx.send("❌ Bạn chỉ có thể tặng quà tình cảm cho vợ/chồng của mình!", ephemeral=True)

        today = datetime.now(VN_TZ).date().isoformat()
        daily = couple.setdefault("daily", {})
        used = int(daily.get(today, 0))
        max_cap = _get_daily_love_cap(couple)

        if used >= max_cap:
            return await ctx.send(f"🌙 Hai bạn đã dùng hết `{max_cap}/{max_cap}` lượt tình cảm hôm nay. Hãy để dành quà cho ngày mai nhé!", ephemeral=True)

        # Kiểm tra kho đồ cá nhân
        inv = get_user_fishing(ctx.author.id)
        items = inv.setdefault("items", {})
        q_info = LOVE_ITEMS[item_id]

        if int(items.get(item_id, 0)) < 1:
            return await ctx.send(
                f"❌ Bạn không có **{q_info['name']}** trong túi đồ! Có thể mua tại shop bằng lệnh `s!shop`.",
                ephemeral=True
            )

        items[item_id] -= 1
        gain = q_info["pts"]

        couple["affection"] = int(couple.get("affection", 0)) + gain
        daily[today] = used + 1

        wk = datetime.now(VN_TZ).strftime("%G-W%V")
        mo = datetime.now(VN_TZ).strftime("%Y-%m")
        couple.setdefault("weekly", {})[wk] = int(couple.setdefault("weekly", {}).get(wk, 0)) + gain
        couple.setdefault("monthly", {})[mo] = int(couple.setdefault("monthly", {}).get(mo, 0)) + gain
        save_fishing_data()

        await ctx.send(
            f"🎁 {ctx.author.mention} đã tặng **{q_info['name']}** cho <@{partner_id}>!\n"
            f"💖 Điểm tình cảm tăng thêm **+{gain}** điểm! (Lượt hôm nay: `{used + 1}/{max_cap}`)."
        )

    # --------------------------------------------------------------------------
    # 5. QUẢN LÝ QUỸ CHUNG (COUPLECOIN)
    # --------------------------------------------------------------------------

    @commands.command(name="couplecoin", aliases=["quychung", "cplcoin"], description="Deposit or withdraw coins from shared couple fund / Nạp hoặc rút tiền quỹ chung")
    @commands.guild_only()
    async def couplecoin_cmd(self, ctx: commands.Context, action: str, amount: int):
        """Quản lý tài chính quỹ chung gia đình (Nạp hoặc Rút coins)."""
        key, couple = _get_user_couple(ctx.guild.id, ctx.author.id)
        if not couple:
            return await ctx.send("❌ Bạn chưa kết hôn để sử dụng quỹ chung!", ephemeral=True)

        if amount <= 0:
            return await ctx.send("❌ Số lượng Coin phải lớn hơn 0!", ephemeral=True)

        act = action.lower().strip()
        if act not in ("nap", "rut", "deposit", "withdraw"):
            return await ctx.send("❌ Thao tác không hợp lệ! Dùng: `/couplecoin nap <số_tiền>` hoặc `/couplecoin rut <số_tiền>`.", ephemeral=True)

        current_common = int(couple.get("common_coins", 0))

        if act in ("nap", "deposit"):
            user_coins = await get_user_currency(ctx.guild.id, ctx.author.id, "coins")
            if user_coins < amount:
                return await ctx.send(f"❌ Bạn không đủ Coin cá nhân! Hiện có: `{user_coins:,}` 🪙.", ephemeral=True)

            await update_user_coins(ctx.guild.id, ctx.author.id, -amount)
            couple["common_coins"] = current_common + amount
            save_fishing_data()
            await ctx.send(f"🏦 {ctx.author.mention} đã nạp thành công **{amount:,}** 🪙 vào Quỹ chung!\n💰 Số dư hiện tại của quỹ: **{couple['common_coins']:,}** coin.")

        else:
            if current_common < amount:
                return await ctx.send(f"❌ Quỹ chung không đủ Coin! Số dư hiện tại chỉ còn `{current_common:,}` 🪙.", ephemeral=True)

            couple["common_coins"] = current_common - amount
            await update_user_coins(ctx.guild.id, ctx.author.id, amount)
            save_fishing_data()
            await ctx.send(f"🏦 {ctx.author.mention} đã rút **{amount:,}** 🪙 từ Quỹ chung về ví cá nhân!\n💰 Số dư còn lại trong quỹ: **{couple['common_coins']:,}** coin.")

    # --------------------------------------------------------------------------
    # 6. BẤT ĐỘNG SẢN GIA VIÊN (COUPLEHOUSE)
    # --------------------------------------------------------------------------

    @commands.command(name="couplehouse", aliases=["nhachung", "cplhouse"], description="Add a purchased property into couple estate / Đưa nhà vào tài sản chung của cặp đôi")
    @commands.guild_only()
    async def couplehouse_cmd(self, ctx: commands.Context, item_id: str):
        """Đưa nhà đã mua tại shop vào danh sách tài sản chung để hưởng buff tình cảm."""
        prop_id = item_id.lower().strip()
        if prop_id not in PROPERTY_INFO:
            return await ctx.send(
                "❌ Loại bất động sản không hợp lệ! Danh sách: `house_small` (🏡 Nhà Nhỏ), `house_villa` (🏘️ Biệt Thự), `house_island` (🏝️ Đảo Riêng).",
                ephemeral=True
            )

        key, couple = _get_user_couple(ctx.guild.id, ctx.author.id)
        if not couple:
            return await ctx.send("❌ Bạn chưa kết hôn để thiết lập gia viên!", ephemeral=True)

        inv = get_user_fishing(ctx.author.id)
        items = inv.setdefault("items", {})

        if int(items.get(prop_id, 0)) < 1:
            p_info = PROPERTY_INFO[prop_id]
            return await ctx.send(
                f"❌ Bạn chưa sở hữu **{p_info['name']}** trong túi đồ! Hãy mua tại shop với giá `{p_info['value']:,}` coin trước.",
                ephemeral=True
            )

        props = couple.setdefault("properties", [])
        if prop_id in props:
            return await ctx.send("❌ Hai bạn đã sở hữu bất động sản loại này rồi!", ephemeral=True)

        items[prop_id] -= 1
        props.append(prop_id)
        save_fishing_data()

        p_info = PROPERTY_INFO[prop_id]
        await ctx.send(
            f"🏡 **CHÚC MỪNG TÂN GIA!**\n"
            f"{ctx.author.mention} đã đưa **{p_info['name']}** vào tài sản chung của cặp đôi!\n"
            f"✨ Đặc quyền kích hoạt: **{p_info['desc']}**\n"
            f"⚖️ Thuế duy trì: `{p_info['tax']:,}` coin/ngày tự động trích từ Quỹ chung."
        )

    # --------------------------------------------------------------------------
    # 7. LY HÔN (DIVORCE)
    # --------------------------------------------------------------------------

    @commands.command(name="divorce", aliases=["lyhon", "ly_hon"], description="Initiate divorce or legal separation / Bắt đầu thủ tục ly hôn")
    @commands.guild_only()
    async def divorce_cmd(self, ctx: commands.Context, option: str = "divide"):
        """Khởi xướng thủ tục ly hôn (chia đều, ra đi tay trắng hoặc kiện ra tòa)."""
        key, couple = _get_user_couple(ctx.guild.id, ctx.author.id)
        if not couple:
            return await ctx.send("❌ Bạn hiện đang độc thân, không có cuộc hôn nhân nào để ly hôn!", ephemeral=True)

        opt = option.lower().strip()
        if opt not in ("empty", "divide", "court"):
            return await ctx.send(
                "❌ Tùy chọn không hợp lệ! Vui lòng chọn:\n"
                "• `/divorce divide`: Chia đều số coin trong quỹ chung (Cần đối phương bấm đồng ý).\n"
                "• `/divorce empty`: Tự nguyện ra đi tay trắng, nhường lại toàn bộ quỹ chung cho đối phương.\n"
                "• `/divorce court`: Đưa đơn ra Tòa án máy chủ để Chủ Server phân xử giải quyết.",
                ephemeral=True
            )

        a, b = int(couple["a"]), int(couple["b"])
        partner_id = b if ctx.author.id == a else a
        partner_member = ctx.guild.get_member(partner_id)

        if opt == "court":
            return await ctx.invoke(self.court_cmd, defendant=partner_member or ctx.author, reason="Yêu cầu giải quyết đơn phương ly hôn qua tòa án")

        mode = "leave_empty" if opt == "empty" else "divide"
        view = DivorceConsentView(ctx.author.id, partner_id, key, mode, ctx.guild.id)
        mode_desc = "ra đi tay trắng (nhường toàn bộ quỹ chung)" if opt == "empty" else "chia đôi số coin trong quỹ chung"

        partner_name = partner_member.mention if partner_member else f"<@{partner_id}>"
        await ctx.send(
            f"💔 {ctx.author.mention} đã gửi yêu cầu ly hôn tới {partner_name}!\n"
            f"📋 Phương án giải quyết: **{mode_desc}**.\n"
            f"⚠️ Thủ tục yêu cầu đối phương bấm xác nhận vào nút bên dưới.",
            view=view
        )

    # --------------------------------------------------------------------------
    # 8. BẢNG XẾP HẠNG CẶP ĐÔI (COUPLETOP / TOPCOUPLE)
    # --------------------------------------------------------------------------

    @commands.command(name="coupletop", aliases=["topcouple", "bxhcapdoi", "loveleaderboard"], description="Top couples leaderboard by affection points / Bảng xếp hạng cặp đôi hạnh phúc")
    @commands.guild_only()
    async def coupletop_cmd(self, ctx: commands.Context, scope: str = "server", period: str = "total"):
        """Xem bảng xếp hạng các cặp đôi có điểm tình cảm cao nhất server hoặc toàn cầu."""
        sc = scope.lower().strip()
        pr = period.lower().strip()

        if sc not in ("server", "global"):
            sc = "server"
        if pr not in ("total", "week", "month"):
            pr = "total"

        wk = datetime.now(VN_TZ).strftime("%G-W%V")
        mo = datetime.now(VN_TZ).strftime("%Y-%m")

        rows = []
        couples = fishing_state.setdefault("couples", {})

        for key, data in couples.items():
            # Loại trừ tài khoản test của Owner
            if str(data.get("a", "")) == str(OWNER_ID) or str(data.get("b", "")) == str(OWNER_ID):
                continue
            if sc == "server" and int(data.get("guild_id", 0)) != ctx.guild.id:
                continue
            if not data.get("public", True) and ctx.author.id not in (int(data.get("a", 0)), int(data.get("b", 0))):
                continue

            if pr == "week":
                score = int(data.get("weekly", {}).get(wk, 0))
            elif pr == "month":
                score = int(data.get("monthly", {}).get(mo, 0))
            else:
                score = int(data.get("affection", 0))

            rows.append((score, data))

        rows.sort(key=lambda x: x[0], reverse=True)

        lines = []
        medals = ["🥇", "🥈", "🥉", "4️⃣", "5️⃣", "6️⃣", "7️⃣", "8️⃣", "9️⃣", "🔟"]
        for i, (score, d) in enumerate(rows[:10]):
            medal = medals[i] if i < len(medals) else f"#{i+1}"
            ring = RING_INFO.get(d.get("ring"), RING_INFO["ring_bronze"])
            lines.append(f"{medal} <@{d['a']}> 💗 <@{d['b']}> • **{score:,}** 💖 {ring['emoji']}")

        title_scope = "Toàn Cầu (Global)" if sc == "global" else ctx.guild.name
        period_name = "Tuần Này" if pr == "week" else ("Tháng Này" if pr == "month" else "Mọi Thời Đại")

        embed = discord.Embed(
            title=f"🏆 BXH CẶP ĐÔI HẠNH PHÚC · {title_scope}",
            description=f"Thống kê điểm tình cảm theo mốc: **{period_name}**\n\n" + ("\n".join(lines) if lines else "*Chưa có dữ liệu cặp đôi nào trong mốc này.*"),
            color=discord.Color.from_rgb(255, 105, 180)
        )
        embed.set_footer(text="SakuraBot Couple Rankings • Cùng bồi đắp tình cảm mỗi ngày!")
        await ctx.send(embed=embed)

    # --------------------------------------------------------------------------
    # 9. GHÉP ĐÔI ĐƯỜNG PHỐ (PAIRUP / BLINDDATE)
    # --------------------------------------------------------------------------

    @commands.command(name="pairup", aliases=["ghepdoi", "blinddate"], description="Find a random dating match in the server / Ghép đôi tìm hiểu ngẫu nhiên trong server")
    @commands.guild_only()
    async def pairup_cmd(self, ctx: commands.Context):
        """Hệ thống mai mối đường phố: Ghép đôi ngẫu nhiên 2 thành viên độc thân để tìm hiểu nhau."""
        if _get_user_couple(ctx.guild.id, ctx.author.id)[1]:
            return await ctx.send("💍 Bạn đã kết hôn rồi! Hãy chung thủy với bạn đời nhé.", ephemeral=True)

        pairings = fishing_state.setdefault("pairings", {})
        today = datetime.now(VN_TZ).date().isoformat()
        prev = pairings.get(str(ctx.author.id), {})

        if prev.get("date") == today and prev.get("guild_id") == ctx.guild.id:
            partner = ctx.guild.get_member(int(prev.get("partner", 0)))
            p_name = partner.mention if partner else "người ấy đã rời server"
            return await ctx.send(f"💞 Bạn đã được ghép đôi hôm nay với {p_name}! Hãy trò chuyện hoặc dùng `/wedding` nếu muốn tiến xa hơn.", ephemeral=True)

        candidates = [
            m for m in ctx.guild.members
            if not m.bot and m.id != ctx.author.id
            and not _get_user_couple(ctx.guild.id, m.id)[1]
            and pairings.get(str(m.id), {}).get("date") != today
        ]

        if not candidates:
            return await ctx.send("🥺 Hiện chưa có thành viên độc thân phù hợp nào đang sẵn sàng ghép đôi. Hãy thử lại sau nhé!", ephemeral=True)

        target = random.choice(candidates)
        pairings[str(ctx.author.id)] = {"guild_id": ctx.guild.id, "partner": target.id, "date": today, "status": "pending"}
        pairings[str(target.id)] = {"guild_id": ctx.guild.id, "partner": ctx.author.id, "date": today, "status": "pending"}
        save_fishing_data()

        view = PairingView(ctx.author.id, target.id, ctx.guild.id)
        await ctx.send(
            f"🎲 **TƠ DUYÊN ĐÃ ĐỊNH!**\n"
            f"Nguyệt lão đã se duyên cho: {ctx.author.mention} 💞 {target.mention}!\n"
            f"Hai bạn có muốn đồng ý mở lòng tìm hiểu nhau không?",
            view=view
        )

    # --------------------------------------------------------------------------
    # 10. TÒA ÁN HÔN NHÂN (COURT)
    # --------------------------------------------------------------------------

    @commands.command(name="court", aliases=["toaan", "kien"], description="Open a family court petition for disputes / Mở hồ sơ tòa án hôn nhân")
    @commands.guild_only()
    async def court_cmd(self, ctx: commands.Context, defendant: discord.Member, *, reason: str = "Yêu cầu giải quyết mâu thuẫn hôn nhân"):
        """Mở hồ sơ kiện tụng hôn nhân để Chủ Server chủ tọa phân xử."""
        if defendant.bot or defendant.id == ctx.author.id:
            return await ctx.send("❌ Bị đơn không hợp lệ!", ephemeral=True)

        key, couple = _get_user_couple(ctx.guild.id, ctx.author.id)
        if not couple or defendant.id not in (int(couple["a"]), int(couple["b"])):
            return await ctx.send("❌ Tòa án hôn nhân chỉ tiếp nhận vụ kiện giữa hai người trong cùng một cuộc hôn nhân!", ephemeral=True)

        case_id = f"{ctx.guild.id}-{int(time.time())}-{random.randint(100, 999)}"
        case = {
            "id": case_id,
            "guild_id": ctx.guild.id,
            "plaintiff": ctx.author.id,
            "defendant": defendant.id,
            "reason": reason[:1000],
            "type": "divorce",
            "couple_key": key,
            "status": "pending",
            "created_at": time.time()
        }
        fishing_state.setdefault("court_cases", {})[case_id] = case
        save_fishing_data()

        owner_mention = ctx.guild.owner.mention if ctx.guild.owner else "Chủ Server"
        embed = discord.Embed(
            title=f"⚖️ TÒA ÁN HÔN NHÂN & GIA ĐÌNH · HỒ SƠ #{case_id}",
            description=(
                f"**Nguyên đơn:** {ctx.author.mention}\n"
                f"**Bị đơn:** {defendant.mention}\n"
                f"**Chủ tọa phiên tòa:** {owner_mention}\n"
                f"**Nội dung khởi kiện:** ```{reason[:800]}```\n"
                f"**Trạng thái:** ⏳ Đang chờ Chủ tọa xem xét ra phán quyết."
            ),
            color=discord.Color.dark_red()
        )
        await ctx.send(embed=embed, view=CourtCaseView(case_id))

    # --------------------------------------------------------------------------
    # 11. HƯỚNG DẪN TOÀN TẬP (MARRIAGEHELP)
    # --------------------------------------------------------------------------

    @commands.command(name="marriagehelp", aliases=["mhelp", "huongdancuoi"], description="Comprehensive guide to marriage and family features / Hướng dẫn hệ thống hôn nhân")
    async def marriage_help_cmd(self, ctx: commands.Context):
        """Xem hướng dẫn chi tiết về tính năng kết hôn, bồi dưỡng tình cảm và tài sản gia đình."""
        p = ctx.prefix if hasattr(ctx, "prefix") and ctx.prefix else "s!"
        embed = discord.Embed(
            title="📖 CẨM NANG HÔN NHÂN & TÌNH YÊU SAKURABOT",
            description="Chào mừng bạn đến với hệ thống kết duyên hạnh phúc của SakuraBot!",
            color=discord.Color.from_rgb(255, 105, 180)
        )

        embed.add_field(
            name="💍 1. Cầu Hôn & Kết Đôi",
            value=(
                f"• `{p}wedding [@user]`: Mở bảng chọn nhẫn cưới và gửi lời cầu hôn.\n"
                f"• `{p}pairup`: Tìm kiếm nửa kia ngẫu nhiên giữa những người độc thân.\n"
                f"• *Lưu ý: Nếu đối phương từ chối, nhẫn cưới sẽ được hoàn trả 100% vào túi đồ!*"
            ),
            inline=False
        )

        embed.add_field(
            name="💖 2. Bồi Đắp Tình Cảm",
            value=(
                f"• `{p}cplove [love|kiss|hug|date]`: Bày tỏ tình cảm mỗi ngày (Tối đa 6+ lượt/ngày).\n"
                f"• `{p}giftlove <loại_quà>`: Tặng socola, hoa tươi, gấu bông hoặc vé hẹn hò.\n"
                f"• Trò chuyện gắn thẻ bạn đời trong server cũng giúp tăng nhẹ tình cảm!"
            ),
            inline=False
        )

        embed.add_field(
            name="🏡 3. Tài Chính & Gia Viên",
            value=(
                f"• `{p}couple`: Xem hồ sơ chi tiết, giấy chứng nhận và ngày kỷ niệm.\n"
                f"• `{p}couplecoin nap/rut <tiền>`: Quản lý quỹ tài chính chung gia đình.\n"
                f"• `{p}couplehouse <loại_nhà>`: Mua nhà tổ ấm, biệt thự hoặc đảo riêng để nhận buff!"
            ),
            inline=False
        )

        embed.add_field(
            name="⚖️ 4. Xếp Hạng & Giải Quyết Tranh Chấp",
            value=(
                f"• `{p}coupletop [server/global]`: Bảng xếp hạng các cặp đôi hạnh phúc nhất.\n"
                f"• `{p}divorce [divide/empty/court]`: Thủ tục ly hôn chia tài sản hoặc ra đi tay trắng.\n"
                f"• `{p}court @user <lý_do>`: Nhờ Chủ Server chủ tọa phiên tòa phân xử."
            ),
            inline=False
        )

        embed.set_footer(text="SakuraBot Marriage System • Gắn kết yêu thương")
        await ctx.send(embed=embed)

    # --------------------------------------------------------------------------
    # 12. SỰ KIỆN TIN NHẮN TƯƠNG TÁC (LISTENER)
    # --------------------------------------------------------------------------

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        """Tăng nhẹ điểm tình cảm khi hai vợ chồng trò chuyện và nhắc đến nhau trong server."""
        if not message.guild or message.author.bot or not message.mentions:
            return

        key, couple = _get_user_couple(message.guild.id, message.author.id)
        if not couple:
            return

        a, b = int(couple["a"]), int(couple["b"])
        partner_id = b if int(couple["a"]) == message.author.id else a

        # Chỉ tính khi người gửi tag chính xác người bạn đời của mình
        if any(m.id == partner_id for m in message.mentions):
            today = datetime.now(VN_TZ).date().isoformat()
            daily = couple.setdefault("daily", {})
            used = int(daily.get(today, 0))
            max_cap = _get_daily_love_cap(couple)

            if used < max_cap:
                couple["affection"] = int(couple.get("affection", 0)) + 1
                daily[today] = used + 1

                wk = datetime.now(VN_TZ).strftime("%G-W%V")
                mo = datetime.now(VN_TZ).strftime("%Y-%m")
                couple.setdefault("weekly", {})[wk] = int(couple.setdefault("weekly", {}).get(wk, 0)) + 1
                couple.setdefault("monthly", {})[mo] = int(couple.setdefault("monthly", {}).get(mo, 0)) + 1
                save_fishing_data()


async def setup(bot: commands.Bot):
    await bot.add_cog(MarriageCog(bot))
