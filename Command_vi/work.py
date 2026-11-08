import asyncio
import json
import math
import random
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Optional, Literal

import discord
from discord import app_commands
from discord.ext import commands
from discord.ui import Button, Select, View

from Checks_vi.level_handler import add_xp
from Checks_vi.mod import OWNER_ID
from Checks_vi.i18n import t, is_vietnamese

from data.database import DB_PATH, get_user_data, update_user_coins

BASE_DIR = Path(__file__).resolve().parent.parent
CAREER_DATA_FILE = BASE_DIR / "data" / "career_system.json"
VN_TZ = timezone(timedelta(hours=7))

WORK_COOLDOWN_SECONDS = 1800  # 30 phút một ca làm việc

# ==============================================================================
# HỆ THỐNG DANH MỤC NGHỀ NGHIỆP & CÁC BẬC THĂNG TIẾN
# ==============================================================================
CAREER_CATALOG = {
    "tech": {
        "name_vi": "💻 Ngành Công Nghệ Thông Tin",
        "name_en": "💻 Information Technology",
        "desc_vi": "Lập trình, quản trị hệ thống và phát triển phần mềm.",
        "desc_en": "Coding, cloud engineering and software development.",
        "tiers": [
            {
                "tier": 1,
                "title_vi": "Thực tập sinh IT (Intern)",
                "title_en": "IT Intern",
                "req_level": 1,
                "req_shifts": 0,
                "min_salary": 25000,
                "max_salary": 45000,
                "xp_reward": 40,
                "fail_rate": 0.22,
                "success_events_vi": [
                    "Sửa thành công lỗi hiển thị giao diện và được mentor khen ngợi.",
                    "Hỗ trợ cấu hình máy tính văn phòng xong sớm trước thời hạn."
                ],
                "success_events_en": [
                    "Fixed a UI rendering bug successfully and received mentor praise.",
                    "Configured office workstations ahead of schedule."
                ],
                "fail_events_vi": [
                    ("Cài nhầm phiên bản làm xung đột thư viện của team, bị trừ phụ cấp.", 20000),
                    ("Lỡ tay làm đổ cà phê làm chập bàn phím công ty, phải đền bù.", 15000)
                ],
                "fail_events_en": [
                    ("Installed conflicting library version causing team build failure, allowance cut.", 20000),
                    ("Accidentally spilled coffee on company equipment, had to pay damages.", 15000)
                ]
            },
            {
                "tier": 2,
                "title_vi": "Lập trình viên (Junior Dev)",
                "title_en": "Junior Software Developer",
                "req_level": 5,
                "req_shifts": 10,
                "min_salary": 80000,
                "max_salary": 140000,
                "xp_reward": 80,
                "fail_rate": 0.18,
                "success_events_vi": [
                    "Viết xong tính năng thanh toán tự động, chạy mượt mà không lỗi.",
                    "Tối ưu câu truy vấn cơ sở dữ liệu giúp hệ thống tải nhanh gấp 3 lần."
                ],
                "success_events_en": [
                    "Implemented payment integration seamlessly without errors.",
                    "Optimized database queries making the application load 3x faster."
                ],
                "fail_events_vi": [
                    ("Đẩy code lỗi thẳng lên máy chủ Production làm sập hệ thống 15 phút, bị phạt KPI.", 90000),
                    ("Quên mã hóa thông tin người dùng bị trưởng bộ phận lập biên bản phạt.", 60000)
                ],
                "fail_events_en": [
                    ("Pushed broken code directly to Production causing 15m outage, KPI fined.", 90000),
                    ("Forgot to encrypt sensitive user data and received a compliance warning.", 60000)
                ]
            },
            {
                "tier": 3,
                "title_vi": "Kỹ sư phần mềm cao cấp (Senior Dev)",
                "title_en": "Senior Software Engineer",
                "req_level": 15,
                "req_shifts": 30,
                "min_salary": 250000,
                "max_salary": 450000,
                "xp_reward": 180,
                "fail_rate": 0.14,
                "success_events_vi": [
                    "Thiết kế kiến trúc chịu tải cho sự kiện Black Friday đón hàng triệu lượt truy cập.",
                    "Vá kịp thời lỗ hổng bảo mật zero-day trước khi bị hacker tấn công."
                ],
                "success_events_en": [
                    "Designed scalable microservice architecture handling millions of requests on Black Friday.",
                    "Patched a critical zero-day vulnerability before malicious intrusion."
                ],
                "fail_events_vi": [
                    ("Cấu hình sai phân quyền Cloud làm lộ dữ liệu nội bộ, bị hội đồng kỷ luật phạt nặng.", 250000),
                    ("Ước lượng sai tiến độ dự án quốc tế khiến công ty bị phạt vi phạm tiến độ hợp đồng.", 300000)
                ],
                "fail_events_en": [
                    ("Misconfigured IAM cloud roles causing internal data exposure, disciplinary fine.", 250000),
                    ("Severely miscalculated sprint milestones leading to client SLA breach fine.", 300000)
                ]
            },
            {
                "tier": 4,
                "title_vi": "Giám đốc công nghệ (CTO)",
                "title_en": "Chief Technology Officer (CTO)",
                "req_level": 30,
                "req_shifts": 70,
                "min_salary": 800000,
                "max_salary": 1500000,
                "xp_reward": 400,
                "fail_rate": 0.10,
                "success_events_vi": [
                    "Ký kết thành công hợp đồng chuyển đổi số trị giá hàng triệu USD.",
                    "Tái cấu trúc toàn bộ hạ tầng kỹ thuật, tiết kiệm 40% chi phí vận hành cho tập đoàn."
                ],
                "success_events_en": [
                    "Signed multi-million dollar digital transformation enterprise contract.",
                    "Refactored infrastructure architecture saving 40% in annual cloud costs."
                ],
                "fail_events_vi": [
                    ("Dự án AI mới đầu tư hàng tỷ đồng thất bại do sai định hướng chiến lược, bồi thường uy tín.", 800000),
                    ("Hệ thống cốt lõi bị gián đoạn diện rộng trong phiên giao dịch, chịu trách nhiệm pháp lý.", 1000000)
                ],
                "fail_events_en": [
                    ("New enterprise AI initiative failed due to architectural misalignment.", 800000),
                    ("Core exchange system suffered outage during high-volume trading hours.", 1000000)
                ]
            }
        ]
    },
    "business": {
        "name_vi": "📈 Ngành Kinh Doanh & Tài Chính",
        "name_en": "📈 Business & Finance",
        "desc_vi": "Bán hàng, phân tích thị trường, quản trị nguồn vốn và đầu tư.",
        "desc_en": "Sales, market analytics, capital management and investments.",
        "tiers": [
            {
                "tier": 1,
                "title_vi": "Cộng tác viên bán hàng (Sales Rep)",
                "title_en": "Sales Representative",
                "req_level": 1,
                "req_shifts": 0,
                "min_salary": 20000,
                "max_salary": 40000,
                "xp_reward": 35,
                "fail_rate": 0.25,
                "success_events_vi": [
                    "Chốt thành công 5 đơn hàng bán lẻ trong buổi chiều.",
                    "Tư vấn nhiệt tình khiến khách hàng quay lại mua thêm gói dịch vụ."
                ],
                "success_events_en": [
                    "Closed 5 retail product orders in an afternoon.",
                    "Helpful consultation persuaded customer to purchase premium service."
                ],
                "fail_events_vi": [
                    ("Gửi nhầm báo giá thấp hơn giá vốn cho khách, phải tự bù tiền túi.", 25000),
                    ("Bị khách bùng đơn giao hàng tận nơi, chịu phí ship hai chiều.", 15000)
                ],
                "fail_events_en": [
                    ("Sent quote below cost price to customer and had to cover difference.", 25000),
                    ("Customer cancelled delivery order on arrival, paid return logistics.", 15000)
                ]
            },
            {
                "tier": 2,
                "title_vi": "Chuyên viên tư vấn tài chính (Broker)",
                "title_en": "Financial Broker",
                "req_level": 5,
                "req_shifts": 10,
                "min_salary": 75000,
                "max_salary": 135000,
                "xp_reward": 75,
                "fail_rate": 0.20,
                "success_events_vi": [
                    "Hỗ trợ khách hàng tái cơ cấu danh mục cổ phiếu chốt lời ấn tượng.",
                    "Đạt chỉ tiêu doanh số môi giới cao nhất chi nhánh trong tuần."
                ],
                "success_events_en": [
                    "Guided high net worth client through profitable portfolio restructuring.",
                    "Achieved highest brokerage volume across the entire regional branch."
                ],
                "fail_events_vi": [
                    ("Phân tích sai xu hướng khiến lệnh giao dịch của khách bị cắt lỗ, bị phạt hoa hồng.", 80000),
                    ("Nhập sai lệnh mua bán chứng khoán trên sàn, bị sàn giao dịch phạt lỗi thao tác.", 100000)
                ],
                "fail_events_en": [
                    ("Inaccurate trend forecast triggered client stop-loss, commission revoked.", 80000),
                    ("Fat-finger order error on trading desk incurred exchange penalty fee.", 100000)
                ]
            },
            {
                "tier": 3,
                "title_vi": "Trưởng phòng kinh doanh (Sales Manager)",
                "title_en": "Sales Department Manager",
                "req_level": 15,
                "req_shifts": 30,
                "min_salary": 240000,
                "max_salary": 420000,
                "xp_reward": 170,
                "fail_rate": 0.15,
                "success_events_vi": [
                    "Đàm phán thành công hợp đồng bao tiêu sản phẩm với chuỗi siêu thị lớn.",
                    "Dẫn dắt đội ngũ kinh doanh vượt 150% chỉ tiêu quý."
                ],
                "success_events_en": [
                    "Secured exclusive distribution agreement with nationwide hypermarket chain.",
                    "Led regional business sales team to surpass quarterly targets by 150%."
                ],
                "fail_events_vi": [
                    ("Đội ngũ không đạt chỉ tiêu doanh số tối thiểu của công ty, bị cắt toàn bộ thưởng tháng.", 220000),
                    ("Bị đối thủ cạnh tranh khiếu nại bản quyền tiếp thị, chịu phí dàn xếp tranh chấp.", 260000)
                ],
                "fail_events_en": [
                    ("Branch missed minimum quota threshold, forfeiture of quarterly management bonus.", 220000),
                    ("Competitor filed marketing infringement dispute, settlement fees deducted.", 260000)
                ]
            },
            {
                "tier": 4,
                "title_vi": "Giám đốc quản lý quỹ đầu tư (Fund Director)",
                "title_en": "Investment Fund Director",
                "req_level": 30,
                "req_shifts": 70,
                "min_salary": 750000,
                "max_salary": 1450000,
                "xp_reward": 380,
                "fail_rate": 0.12,
                "success_events_vi": [
                    "Thực hiện thương vụ sáp nhập doanh nghiệp thành công rực rỡ, chia cổ tức khủng.",
                    "Quản lý danh mục đầu tư đem lại lợi nhuận ròng vượt trội cho các cổ đông."
                ],
                "success_events_en": [
                    "Executed high-profile merger & acquisition yielding massive dividend payouts.",
                    "Delivered market-beating net alpha across shareholder equity portfolios."
                ],
                "fail_events_vi": [
                    ("Đầu tư sai lầm vào một dự án khởi nghiệp kém minh bạch, bị cổ đông truy cứu trách nhiệm.", 750000),
                    ("Thị trường tài chính biến động bất ngờ gây thua lỗ nặng nề cho quỹ.", 950000)
                ],
                "fail_events_en": [
                    ("Misallocated seed investment into fraudulent startup entity.", 750000),
                    ("Severe macroeconomic volatility caused drawdown on treasury fund.", 950000)
                ]
            }
        ]
    },
    "service": {
        "name_vi": "🛵 Dịch Vụ & Hậu Cần Xã Hội",
        "name_en": "🛵 Services & Social Logistics",
        "desc_vi": "Vận tải, giao nhận hàng, ẩm thực nhà hàng và kỹ thuật dân dụng.",
        "desc_en": "Transport, deliveries, gastronomy and operational logistics.",
        "tiers": [
            {
                "tier": 1,
                "title_vi": "Tài xế công nghệ (Shipper)",
                "title_en": "Delivery Courier / Shipper",
                "req_level": 1,
                "req_shifts": 0,
                "min_salary": 18000,
                "max_salary": 38000,
                "xp_reward": 30,
                "fail_rate": 0.20,
                "success_events_vi": [
                    "Giao 10 cuốc hàng giờ cao điểm an toàn, nhận thêm tiền tip từ khách.",
                    "Tìm đường tắt thông minh, giao đồ ăn nóng hổi đúng hẹn."
                ],
                "success_events_en": [
                    "Delivered 10 rush hour packages safely and earned generous tips.",
                    "Took efficient shortcuts delivering hot meals ahead of ETA."
                ],
                "fail_events_vi": [
                    ("Làm rơi vỡ kiện hàng gốm sứ đắt tiền của khách, phải bồi thường 100%.", 30000),
                    ("Bị cảnh sát giao thông phạt vì đi nhầm vào đường một chiều trong lúc vội.", 25000)
                ],
                "fail_events_en": [
                    ("Accidentally dropped fragile ceramic parcel, had to compensate full value.", 30000),
                    ("Traffic citation fine for wrong-way street entry during rush order.", 25000)
                ]
            },
            {
                "tier": 2,
                "title_vi": "Bếp phó nhà hàng (Sous Chef)",
                "title_en": "Restaurant Sous Chef",
                "req_level": 5,
                "req_shifts": 10,
                "min_salary": 70000,
                "max_salary": 125000,
                "xp_reward": 70,
                "fail_rate": 0.16,
                "success_events_vi": [
                    "Nấu tiệc phục vụ đoàn khách VIP 50 người nhận được cơn mưa lời khen.",
                    "Sáng tạo món khai vị mới được thực khách hưởng ứng nồng nhiệt."
                ],
                "success_events_en": [
                    "Served 50-guest VIP banquet receiving unanimous culinary praise.",
                    "Created innovative appetizer recipe acclaimed by visiting food critics."
                ],
                "fail_events_vi": [
                    ("Sơ suất bảo quản nguyên liệu hải sản đắt tiền bị hỏng, bị bếp trưởng trừ lương.", 70000),
                    ("Làm cháy món nướng chính của bàn đại tiệc, phải đích thân đền món cho khách.", 85000)
                ],
                "fail_events_en": [
                    ("Failed temperature control spoiled expensive seafood ingredients, salary docked.", 70000),
                    ("Overcooked prime roast for banquet table, personally replaced entree.", 85000)
                ]
            },
            {
                "tier": 3,
                "title_vi": "Quản lý chuỗi kho vận (Logistics Head)",
                "title_en": "Supply Chain & Logistics Head",
                "req_level": 15,
                "req_shifts": 30,
                "min_salary": 220000,
                "max_salary": 380000,
                "xp_reward": 160,
                "fail_rate": 0.12,
                "success_events_vi": [
                    "Điều phối trơn tru hàng chục nghìn kiện hàng trong ngày đại hội mua sắm.",
                    "Ứng dụng hệ thống mã vạch mới giúp giảm thời gian phân loại kho xuống một nửa."
                ],
                "success_events_en": [
                    "Flawlessly dispatched tens of thousands of parcels during mega sales event.",
                    "Introduced automated barcode sorting cutting processing time in half."
                ],
                "fail_events_vi": [
                    ("Xe tải trung chuyển gặp sự cố chậm hàng loạt đơn giao dịch, công ty chịu phạt hợp đồng.", 200000),
                    ("Kiểm kê cuối tháng phát hiện thất thoát hàng hóa nghiêm trọng trong kho phụ trách.", 240000)
                ],
                "fail_events_en": [
                    ("Freight truck breakdown stalled regional dispatches, freight penalty fee.", 200000),
                    ("End-of-month stock count revealed inventory discrepancy under your division.", 240000)
                ]
            },
            {
                "tier": 4,
                "title_vi": "Chủ chuỗi nhượng quyền ẩm thực (Franchise Owner)",
                "title_en": "Franchise Brand Owner",
                "req_level": 30,
                "req_shifts": 70,
                "min_salary": 700000,
                "max_salary": 1300000,
                "xp_reward": 350,
                "fail_rate": 0.08,
                "success_events_vi": [
                    "Khai trương thêm 3 chi nhánh mới tại các trung tâm thương mại lớn.",
                    "Ký kết hợp tác nhượng quyền độc quyền với đối tác nước ngoài."
                ],
                "success_events_en": [
                    "Opened 3 new successful outlets in premier metropolitan malls.",
                    "Secured exclusive master franchise agreement with overseas partners."
                ],
                "fail_events_vi": [
                    ("Một chi nhánh bị kiểm tra vệ sinh an toàn thực phẩm phạt vi phạm quy định cơ sở.", 600000),
                    ("Khủng hoảng truyền thông vì sự cố nhân viên phục vụ, doanh thu toàn chuỗi sụt giảm.", 750000)
                ],
                "fail_events_en": [
                    ("Outlet failed random hygiene inspection incurring heavy compliance fine.", 600000),
                    ("Public relations incident over staff conduct caused momentary revenue drop.", 750000)
                ]
            }
        ]
    }
}

career_storage = {}


def load_career_data():
    global career_storage
    if CAREER_DATA_FILE.exists():
        try:
            with open(CAREER_DATA_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                if isinstance(data, dict):
                    career_storage.update(data)
        except Exception:
            pass


def save_career_data():
    CAREER_DATA_FILE.parent.mkdir(parents=True, exist_ok=True)
    try:
        with open(CAREER_DATA_FILE, "w", encoding="utf-8") as f:
            json.dump(career_storage, f, indent=4, ensure_ascii=False)
    except Exception:
        pass


load_career_data()


def get_user_career(guild_id: int, user_id: int) -> dict:
    key = f"{guild_id}_{user_id}"
    record = career_storage.setdefault(key, {})
    record.setdefault("career_id", "service")
    record.setdefault("tier", 1)
    record.setdefault("career_exp", 0)
    record.setdefault("total_shifts", 0)
    record.setdefault("success_shifts", 0)
    record.setdefault("failed_shifts", 0)
    record.setdefault("last_work_time", 0)
    record.setdefault("reputation", 100)
    record.setdefault("total_earned", 0)
    record.setdefault("total_fined", 0)
    return record


def get_tier_config(career_id: str, tier: int) -> Optional[dict]:
    career = CAREER_CATALOG.get(career_id)
    if not career:
        return None
    for t in career["tiers"]:
        if t["tier"] == tier:
            return t
    return None


# ==============================================================================
# VIEW NỘP ĐƠN ỨNG TUYỂN / CHUYỂN ĐỔI NGÀNH NGHỀ
# ==============================================================================
class JobMarketView(View):
    def __init__(self, author: discord.Member, parent_view: "WorkMainView"):
        super().__init__(timeout=90)
        self.author = author
        self.parent_view = parent_view
        vi = is_vietnamese(parent_view.guild_id)
        self.back_btn.label = "Quay Lại" if vi else "Back"

        options = []
        for cid, cdata in CAREER_CATALOG.items():
            first_tier = cdata["tiers"][0]
            c_name = cdata["name_vi"] if vi else cdata["name_en"]
            t_title = first_tier["title_vi"] if vi else first_tier["title_en"]
            desc_str = f"Khởi điểm: {t_title} (Lv.1)" if vi else f"Starts: {t_title} (Lv.1)"
            options.append(
                discord.SelectOption(
                    label=c_name[:100],
                    value=cid,
                    description=desc_str[:100],
                    emoji="👔"
                )
            )

        ph = "Chọn ngành nghề bạn muốn theo đuổi..." if vi else "Choose career path..."
        self.select_menu = Select(placeholder=ph, options=options, row=0)
        self.select_menu.callback = self._on_select_career
        self.add_item(self.select_menu)

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id != self.author.id:
            vi = is_vietnamese(interaction.guild_id)
            msg = "❌ Đây không phải phiên làm việc của bạn!" if vi else "❌ This session does not belong to you!"
            await interaction.response.send_message(msg, ephemeral=True)
            return False
        return True

    async def _on_select_career(self, interaction: discord.Interaction):
        vi = is_vietnamese(interaction.guild_id)
        chosen_career_id = self.select_menu.values[0]
        rec = get_user_career(interaction.guild_id, self.author.id)

        if rec.get("career_id") == chosen_career_id:
            msg = "⚠️ Bạn hiện đã đang làm việc trong lĩnh vực này!" if vi else "⚠️ You are already employed in this career path!"
            return await interaction.response.send_message(msg, ephemeral=True)

        rec["career_id"] = chosen_career_id
        rec["tier"] = 1
        rec["career_exp"] = 0
        rec["reputation"] = 100
        save_career_data()

        c_info = CAREER_CATALOG[chosen_career_id]
        t_info = c_info["tiers"][0]
        c_name = c_info["name_vi"] if vi else c_info["name_en"]
        t_title = t_info["title_vi"] if vi else t_info["title_en"]

        embed = await self.parent_view.build_main_embed()
        await interaction.response.edit_message(embed=embed, view=self.parent_view)

        if vi:
            succ = (
                f"🎉 **CHUYỂN NGÀNH THÀNH CÔNG!**\n"
                f"Chào mừng bạn gia nhập **{c_name}** với chức danh: **{t_title}**!"
            )
        else:
            succ = (
                f"🎉 **CAREER CHANGE SUCCESSFUL!**\n"
                f"Welcome to **{c_name}** with the starting position: **{t_title}**!"
            )
        await interaction.followup.send(succ, ephemeral=True)

    @discord.ui.button(label="Quay Lại", style=discord.ButtonStyle.secondary, emoji="🔙", row=1)
    async def back_btn(self, interaction: discord.Interaction, button: Button):
        embed = await self.parent_view.build_main_embed()
        await interaction.response.edit_message(embed=embed, view=self.parent_view)


# ==============================================================================
# GIAO DIỆN CHÍNH CỦA HỆ THỐNG WORK & SỰ NGHIỆP
# ==============================================================================
class WorkMainView(View):
    def __init__(self, author: discord.Member, guild_id: int):
        super().__init__(timeout=180)
        self.author = author
        self.guild_id = guild_id
        vi = is_vietnamese(guild_id)

        self.work_btn.label = "Vào Ca Làm Việc" if vi else "Start Work Shift"
        self.promote_btn.label = "Xin Thăng Chức" if vi else "Apply Promotion"
        self.switch_career_btn.label = "Ứng Tuyển / Đổi Ngành" if vi else "Switch Career"
        self.refresh_btn.label = "Làm Mới" if vi else "Refresh"

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id != self.author.id:
            vi = is_vietnamese(interaction.guild_id)
            msg = "❌ Giao diện này thuộc về người khác!" if vi else "❌ This interface belongs to another user!"
            await interaction.response.send_message(msg, ephemeral=True)
            return False
        return True

    async def build_main_embed(self) -> discord.Embed:
        user_id = self.author.id
        guild_id = self.guild_id
        vi = is_vietnamese(guild_id)

        u_data = await get_user_data(guild_id, user_id)
        user_level = int(u_data.get("level", 0))

        rec = get_user_career(guild_id, user_id)
        c_id = rec.get("career_id", "service")
        tier_num = rec.get("tier", 1)
        t_info = get_tier_config(c_id, tier_num)
        c_info = CAREER_CATALOG.get(c_id, CAREER_CATALOG["service"])

        c_name = c_info["name_vi"] if vi else c_info["name_en"]
        t_title = t_info["title_vi"] if vi else t_info["title_en"]

        now = int(time.time())
        cooldown_left = max(0, (rec.get("last_work_time", 0) + WORK_COOLDOWN_SECONDS) - now)
        if cooldown_left > 0:
            status_shift = f"⏳ Đang nghỉ giữa ca (Sẵn sàng <t:{now + cooldown_left}:R>)" if vi else f"⏳ Resting between shifts (Ready <t:{now + cooldown_left}:R>)"
        else:
            status_shift = "🟢 **ĐÃ SẴN SÀNG VÀO CA LÀM VIỆC**" if vi else "🟢 **READY FOR NEXT SHIFT**"

        rep = rec.get("reputation", 100)
        if vi:
            rep_status = "⭐ Xuất sắc" if rep >= 90 else ("🟢 Tốt" if rep >= 70 else ("⚠️ Cảnh cáo kỷ luật" if rep >= 40 else "🔴 Nguy cơ sa thải"))
            title = "🏢 TRUNG TÂM PHÁT TRIỂN SỰ NGHIỆP & VIỆC LÀM"
            desc = f"Hồ sơ nghề nghiệp của nhân sự: **{self.author.display_name}**"
        else:
            rep_status = "⭐ Excellent" if rep >= 90 else ("🟢 Good" if rep >= 70 else ("⚠️ Warning" if rep >= 40 else "🔴 At Risk"))
            title = "🏢 CAREER & EMPLOYMENT CENTER"
            desc = f"Personnel career portfolio: **{self.author.display_name}**"

        embed = discord.Embed(
            title=title,
            description=desc,
            color=discord.Color.from_rgb(16, 185, 129),
            timestamp=discord.utils.utcnow()
        )
        if self.author.display_avatar:
            embed.set_thumbnail(url=self.author.display_avatar.url)

        if vi:
            f1_title = "👔 Vị Trí Công Tác Hiện Tại"
            f1_val = (
                f"• Lĩnh vực: **{c_name}**\n"
                f"• Chức danh: **{t_title}** (Bậc {tier_num}/4)\n"
                f"• Khung lương: `{t_info['min_salary']:,}` - `{t_info['max_salary']:,}` coin/ca\n"
                f"• Tỷ lệ rủi ro: `{int(t_info['fail_rate']*100)}%` khả năng mắc lỗi"
            )
        else:
            f1_title = "👔 Current Employment Position"
            f1_val = (
                f"• Industry: **{c_name}**\n"
                f"• Position: **{t_title}** (Tier {tier_num}/4)\n"
                f"• Salary range: `{t_info['min_salary']:,}` - `{t_info['max_salary']:,}` coins/shift\n"
                f"• Error risk: `{int(t_info['fail_rate']*100)}%` failure chance"
            )
        embed.add_field(name=f1_title, value=f1_val, inline=False)

        next_tier = get_tier_config(c_id, tier_num + 1)
        if next_tier:
            next_title = next_tier["title_vi"] if vi else next_tier["title_en"]
            if vi:
                promo_reqs = (
                    f"• Vị trí kế tiếp: **{next_title}**\n"
                    f"• Cấp nhân vật yêu cầu: `Lv.{next_tier['req_level']}` (Hiện tại: `Lv.{user_level}`)\n"
                    f"• Ca làm việc tích lũy: `{rec.get('total_shifts', 0)}/{next_tier['req_shifts']}` ca\n"
                    f"• Điểm chuyên môn: `{rec.get('career_exp', 0)}/100` điểm"
                )
            else:
                promo_reqs = (
                    f"• Next Rank: **{next_title}**\n"
                    f"• Required Character Level: `Lv.{next_tier['req_level']}` (Current: `Lv.{user_level}`)\n"
                    f"• Accumulated Shifts: `{rec.get('total_shifts', 0)}/{next_tier['req_shifts']}` shifts\n"
                    f"• Expertise Points: `{rec.get('career_exp', 0)}/100` pts"
                )
        else:
            promo_reqs = "👑 **Bạn đã đạt chức danh cao nhất trong ngành nghề này!**" if vi else "👑 **You have reached the pinnacle position in this industry!**"

        f2_title = "🎯 Điều Kiện Thăng Chức Kế Tiếp" if vi else "🎯 Next Promotion Requirements"
        embed.add_field(name=f2_title, value=promo_reqs, inline=False)

        total_shifts = rec.get("total_shifts", 0)
        rate = round((rec.get("success_shifts", 0) / total_shifts * 100), 1) if total_shifts > 0 else 100.0

        if vi:
            f3_title = "📊 Hiệu Suất & Uy Tín"
            f3_val = (
                f"• Tổng ca hoàn thành: `{total_shifts}` ca\n"
                f"• Tỷ lệ thành công: `{rate}%`\n"
                f"• Điểm uy tín nghề nghiệp: `{rep}/100` ({rep_status})\n"
                f"• Trạng thái ca: {status_shift}"
            )
            f4_title = "💰 Tài Chính Sự Nghiệp"
            f4_val = (
                f"• Tổng thu nhập: `+{rec.get('total_earned', 0):,}` c\n"
                f"• Tổng tiền bị phạt: `-{rec.get('total_fined', 0):,}` c"
            )
            footer_text = "Làm việc chăm chỉ, cẩn trọng tránh sai sót và tích lũy thâm niên để thăng tiến."
        else:
            f3_title = "📊 Performance & Reputation"
            f3_val = (
                f"• Total completed shifts: `{total_shifts}` shifts\n"
                f"• Success rate: `{rate}%`\n"
                f"• Career reputation: `{rep}/100` ({rep_status})\n"
                f"• Shift status: {status_shift}"
            )
            f4_title = "💰 Career Financials"
            f4_val = (
                f"• Total earnings: `+{rec.get('total_earned', 0):,}` c\n"
                f"• Total penalties: `-{rec.get('total_fined', 0):,}` c"
            )
            footer_text = "Work diligently, minimize operational errors and accrue seniority to earn promotions."

        embed.add_field(name=f3_title, value=f3_val, inline=True)
        embed.add_field(name=f4_title, value=f4_val, inline=True)
        embed.set_footer(text=footer_text)
        return embed

    @discord.ui.button(label="Vào Ca Làm Việc", style=discord.ButtonStyle.success, emoji="💼", row=0)
    async def work_btn(self, interaction: discord.Interaction, button: Button):
        guild_id = self.guild_id
        user_id = self.author.id
        vi = is_vietnamese(guild_id)
        now = int(time.time())
        rec = get_user_career(guild_id, user_id)

        cooldown_left = (rec.get("last_work_time", 0) + WORK_COOLDOWN_SECONDS) - now
        if cooldown_left > 0:
            mins = cooldown_left // 60
            secs = cooldown_left % 60
            msg = f"⏳ Bạn vừa hoàn thành một ca làm việc và đang nghỉ ngơi! Vui lòng quay lại sau **{mins} phút {secs} giây**." if vi else f"⏳ You are resting between work shifts! Please return in **{mins} min {secs} sec**."
            return await interaction.response.send_message(msg, ephemeral=True)

        c_id = rec.get("career_id", "service")
        tier_num = rec.get("tier", 1)
        t_info = get_tier_config(c_id, tier_num)

        rec["last_work_time"] = now
        rec["total_shifts"] = rec.get("total_shifts", 0) + 1

        is_failed = random.random() < t_info["fail_rate"]

        if is_failed:
            rec["failed_shifts"] = rec.get("failed_shifts", 0) + 1
            rec["reputation"] = max(0, rec.get("reputation", 100) - 8)

            events_pool = t_info["fail_events_vi"] if vi else t_info["fail_events_en"]
            event_text, penalty_cost = random.choice(events_pool)
            rec["total_fined"] = rec.get("total_fined", 0) + penalty_cost

            u_data = await get_user_data(guild_id, user_id)
            current_wallet = u_data.get("coins", 0)
            actual_penalty = min(current_wallet, penalty_cost)
            await update_user_coins(guild_id, user_id, -actual_penalty)

            demoted_msg = ""
            if rec["reputation"] < 30 and tier_num > 1:
                rec["tier"] -= 1
                rec["reputation"] = 60
                rec["career_exp"] = 0
                lower_tier = get_tier_config(c_id, rec["tier"])
                lower_title = lower_tier["title_vi"] if vi else lower_tier["title_en"]
                demoted_msg = f"\n⚠️ **BỊ GIÁNG CHỨC:** Do liên tục mắc sai lầm nghiêm trọng, bạn đã bị chuyển xuống vị trí **{lower_title}**!" if vi else f"\n⚠️ **DEMOTED:** Due to critical infractions, you were demoted to **{lower_title}**!"

            save_career_data()

            embed = await self.build_main_embed()
            await interaction.response.edit_message(embed=embed, view=self)

            if vi:
                res = (
                    f"💥 **SỰ CỐ TRONG CA LÀM VIỆC!**\n"
                    f"*{event_text}*\n"
                    f"• Thiệt hại bị trừ vào ví: **`-{actual_penalty:,}` coin**\n"
                    f"• Điểm uy tín giảm: **`-8 điểm`** (Hiện còn {rec['reputation']}/100){demoted_msg}"
                )
            else:
                res = (
                    f"💥 **INCIDENT DURING WORK SHIFT!**\n"
                    f"*{event_text}*\n"
                    f"• Damages deducted from wallet: **`-{actual_penalty:,}` coins**\n"
                    f"• Reputation decreased: **`-8 points`** (Current: {rec['reputation']}/100){demoted_msg}"
                )
            return await interaction.followup.send(res, ephemeral=False)

        # Xử lý khi làm việc thành công
        rec["success_shifts"] = rec.get("success_shifts", 0) + 1
        rec["reputation"] = min(100, rec.get("reputation", 100) + 2)
        rec["career_exp"] = min(100, rec.get("career_exp", 0) + random.randint(8, 15))

        earned_salary = random.randint(t_info["min_salary"], t_info["max_salary"])
        rec["total_earned"] = rec.get("total_earned", 0) + earned_salary

        await update_user_coins(guild_id, user_id, earned_salary)
        await add_xp(user_id, guild_id, interaction.channel)

        success_pool = t_info["success_events_vi"] if vi else t_info["success_events_en"]
        success_story = random.choice(success_pool)
        save_career_data()

        embed = await self.build_main_embed()
        await interaction.response.edit_message(embed=embed, view=self)

        if vi:
            res = (
                f"✅ **HOÀN THÀNH CA LÀM VIỆC XUẤT SẮC!**\n"
                f"*{success_story}*\n"
                f"• Tiền lương thực nhận: **`+{earned_salary:,}` coin**\n"
                f"• Kinh nghiệm thăng tiến: **`+{t_info['xp_reward']}` XP** & **Chuyên môn +{rec['career_exp']}%**\n"
                f"• Điểm uy tín: **`+2 điểm`** (Hiện có {rec['reputation']}/100)"
            )
        else:
            res = (
                f"✅ **WORK SHIFT COMPLETED SUCCESSFULLY!**\n"
                f"*{success_story}*\n"
                f"• Earned Salary: **`+{earned_salary:,}` coins**\n"
                f"• Experience: **`+{t_info['xp_reward']}` XP** & **Expertise +{rec['career_exp']}%**\n"
                f"• Reputation: **`+2 points`** (Current: {rec['reputation']}/100)"
            )
        await interaction.followup.send(res, ephemeral=False)

    @discord.ui.button(label="Xin Thăng Chức", style=discord.ButtonStyle.primary, emoji="⭐", row=0)
    async def promote_btn(self, interaction: discord.Interaction, button: Button):
        guild_id = self.guild_id
        user_id = self.author.id
        vi = is_vietnamese(guild_id)
        rec = get_user_career(guild_id, user_id)
        c_id = rec.get("career_id", "service")
        tier_num = rec.get("tier", 1)

        next_tier = get_tier_config(c_id, tier_num + 1)
        if not next_tier:
            msg = "👑 Bạn đã đạt đến bậc danh vọng cao nhất trong lĩnh vực hiện tại!" if vi else "👑 You have already reached the highest rank in this industry!"
            return await interaction.response.send_message(msg, ephemeral=True)

        u_data = await get_user_data(guild_id, user_id)
        user_level = int(u_data.get("level", 0))
        next_title = next_tier["title_vi"] if vi else next_tier["title_en"]

        if user_level < next_tier["req_level"]:
            msg = f"❌ Cấp độ nhân vật chưa đủ! Vị trí **{next_title}** yêu cầu đạt tối thiểu **Level {next_tier['req_level']}** (Bạn đang ở Level {user_level})." if vi else f"❌ Character level too low! Position **{next_title}** requires at least **Level {next_tier['req_level']}** (You are Level {user_level})."
            return await interaction.response.send_message(msg, ephemeral=True)

        if rec.get("total_shifts", 0) < next_tier["req_shifts"]:
            msg = f"❌ Thiếu số ca làm việc tích lũy! Bạn cần hoàn thành tối thiểu **{next_tier['req_shifts']} ca** (Hiện có: {rec.get('total_shifts', 0)} ca)." if vi else f"❌ Insufficient work shifts! You need at least **{next_tier['req_shifts']} shifts** (Current: {rec.get('total_shifts', 0)})."
            return await interaction.response.send_message(msg, ephemeral=True)

        if rec.get("career_exp", 0) < 100:
            msg = f"❌ Điểm chuyên môn chưa đạt yêu cầu! Bạn cần đạt **100 điểm chuyên môn** từ các ca làm việc thành công (Hiện có: {rec.get('career_exp', 0)}/100)." if vi else f"❌ Expertise requirements not met! You need **100 expertise points** (Current: {rec.get('career_exp', 0)}/100)."
            return await interaction.response.send_message(msg, ephemeral=True)

        if rec.get("reputation", 100) < 70:
            msg = f"❌ Điểm uy tín quá thấp ({rec.get('reputation')}/100)! Ban giám đốc yêu cầu uy tín tối thiểu từ 70 điểm trở lên để xét duyệt bổ nhiệm." if vi else f"❌ Reputation score too low ({rec.get('reputation')}/100)! Minimum 70 reputation required for promotion approval."
            return await interaction.response.send_message(msg, ephemeral=True)

        rec["tier"] += 1
        rec["career_exp"] = 0
        save_career_data()

        embed = await self.build_main_embed()
        await interaction.response.edit_message(embed=embed, view=self)

        if vi:
            succ = (
                f"🎉🎉 **CHÚC MỪNG BỔ NHIỆM CHỨC VỤ MỚI!**\n"
                f"Hội đồng quản trị đã phê duyệt hồ sơ thăng chức của bạn lên vị trí: **{next_title}**!\n"
                f"Mức lương khởi điểm mỗi ca làm việc đã được nâng lên **`{next_tier['min_salary']:,}` - `{next_tier['max_salary']:,}` coin**!"
            )
        else:
            succ = (
                f"🎉🎉 **CONGRATULATIONS ON YOUR PROMOTION!**\n"
                f"The executive board has approved your promotion to: **{next_title}**!\n"
                f"Your shift salary scale has been upgraded to **`{next_tier['min_salary']:,}` - `{next_tier['max_salary']:,}` coins**!"
            )
        await interaction.followup.send(succ, ephemeral=False)

    @discord.ui.button(label="Ứng Tuyển / Đổi Ngành", style=discord.ButtonStyle.secondary, emoji="👔", row=0)
    async def switch_career_btn(self, interaction: discord.Interaction, button: Button):
        vi = is_vietnamese(interaction.guild_id)
        market_view = JobMarketView(self.author, self)
        if vi:
            title = "🏢 SÀN GIAO DỊCH VIỆC LÀM & TUYỂN DỤNG"
            desc = (
                "Hãy chọn một ngành nghề mới từ menu bên dưới để bắt đầu lộ trình sự nghiệp mới:\n\n"
                "• ⚠️ *Lưu ý: Khi chuyển sang một ngành nghề mới, bạn sẽ bắt đầu lại từ **Bậc 1 (Tập sự/Thực tập)** của ngành đó.*"
            )
        else:
            title = "🏢 JOB MARKET & CAREER RECRUITMENT"
            desc = (
                "Choose a new career path from the menu below:\n\n"
                "• ⚠️ *Note: When switching to a new career, you start at **Tier 1 (Intern/Apprentice)** of that industry.*"
            )
        embed = discord.Embed(title=title, description=desc, color=discord.Color.blue())
        await interaction.response.edit_message(embed=embed, view=market_view)

    @discord.ui.button(label="Làm Mới", style=discord.ButtonStyle.secondary, emoji="🔄", row=0)
    async def refresh_btn(self, interaction: discord.Interaction, button: Button):
        embed = await self.build_main_embed()
        await interaction.response.edit_message(embed=embed, view=self)


# ==============================================================================
# LỚP COG CHÍNH TÍCH HỢP
# ==============================================================================
class CareerCog(commands.Cog, name="Sự Nghiệp & Việc Làm"):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.hybrid_command(
        name="work",
        aliases=["career", "lamviec", "cv"],
        description="💼 Hệ thống Sự Nghiệp & Việc Làm: Lương thưởng, Thăng chức, Rủi ro đền bù / Career & Work system."
    )
    @commands.guild_only()
    async def work_command(self, ctx: commands.Context):
        view = WorkMainView(ctx.author, ctx.guild.id)
        embed = await view.build_main_embed()
        await ctx.send(embed=embed, view=view)


async def setup(bot: commands.Bot):
    await bot.add_cog(CareerCog(bot))
