import discord
import random
import json
import os
import asyncio

from openai import AsyncOpenAI
from data.data import TAROT_DECK
from Checks_vi.tarot import save_history, get_history, draw_cards, can_draw_today
from Checks_vi.i18n import t

# --- CẤU HÌNH XKIRO API ---
API_KEY = None
try:
    from config import XKIRO_API_KEY as API_KEY
except ImportError:
    try:
        from config import GEMINI_API_KEY as API_KEY
    except ImportError:
        API_KEY = os.getenv("XKIRO_API_KEY") or os.getenv("GEMINI_API_KEY")

xkiro_client = AsyncOpenAI(
    api_key=API_KEY or "missing-api-key",
    base_url="https://api.xkiro.com/v1",
)

try:
    from config import AI_MODEL
except ImportError:
    AI_MODEL = "sensenova/sensenova-6.8-flash-lite"

class GiaiDapButtonView(discord.ui.View):
    def __init__(self, la_bai_info: dict, giong_doc: str):
        super().__init__(timeout=600) # Nút bấm có hiệu lực trong 10 phút
        self.la_bai_info = la_bai_info
        self.giong_doc = giong_doc

    @discord.ui.button(label="Xem giải đáp chi tiết", style=discord.ButtonStyle.success, emoji="💡")
    async def xem_giai_dap(self, interaction: discord.Interaction, button: discord.ui.Button):
        # Defer response ngay lập tức để tránh timeout
        await interaction.response.defer(ephemeral=True, thinking=True)

        # Vô hiệu hóa nút và hiển thị trạng thái đang tải
        button.disabled = True
        button.label = "AI đang luận giải..."
        button.style = discord.ButtonStyle.secondary

        name = self.la_bai_info['name']
        orientation = self.la_bai_info['orientation']
        meaning = self.la_bai_info['meaning']
        
        # Tạo Embed giải đáp chuyên sâu
        embed = discord.Embed(
            title=f"📖 Luận Giải Chi Tiết: {name}",
            color=0x2ECC71
        )
        embed.add_field(name="☯️ Hướng bài:", value=orientation, inline=True)
        embed.add_field(name="🌸 Giọng đọc:", value=self.giong_doc, inline=True)
        
        # Tạo prompt và gọi AI qua xKiro để có lời giải đáp chi tiết
        try:
            prompt = (
                f"Bạn là một reader Tarot chuyên nghiệp, có khả năng luận giải ý nghĩa lá bài một cách sâu sắc và tinh tế. "
                f"Hãy giải thích chi tiết ý nghĩa của lá bài sau đây theo giọng văn '{self.giong_doc}'. "
                f"Lá bài: {name} ({orientation}). Ý nghĩa gốc: {meaning}. "
                "Luôn trả lời bằng tiếng Việt, trình bày rõ ràng, không cần lặp lại tên lá bài ở đầu câu."
            )
            chat_completion = await xkiro_client.chat.completions.create(
                model=AI_MODEL,
                messages=[
                    {"role": "system", "content": "Bạn là một chuyên gia Tarot, hãy đưa ra lời luận giải sâu sắc."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.8,
                max_tokens=400
            )
            ai_reply = (
                chat_completion.choices[0].message.content.strip()
                if (chat_completion.choices and chat_completion.choices[0].message.content)
                else "..."
            )
            # Cắt ngắn ai_reply nếu nó quá dài để tránh lỗi Discord Embed Field Limit (1024 ký tự)
            if len(ai_reply) > 1024:
                ai_reply = ai_reply[:1021] + "..." # Cắt và thêm dấu "..."

        except Exception as e:
            ai_reply = f"Xin lỗi, quả cầu tiên tri của tôi đang bị nhiễu sóng (Lỗi: {e}). Vui lòng thử lại sau."

        embed.add_field(name="💡 Lời khuyên từ AI dành cho bạn:", value=ai_reply, inline=False)
        embed.set_footer(text=f"Nội dung giải đáp mang tính chất định hướng năng lượng • Model: {AI_MODEL}")

        # Gửi lời giải đáp dưới dạng ẩn danh (chỉ người bấm nhìn thấy)
        await interaction.followup.send(embed=embed, ephemeral=True)

class BoiNhanhModal(discord.ui.Modal, title="🔮 Bói Nhanh 1 Lá"):
    # Định nghĩa các ô nhập liệu (TextInput)
    cau_hoi = discord.ui.TextInput(
        label="Câu hỏi / điều bạn muốn xem",
        style=discord.TextStyle.paragraph, # Ô nhập dài (Paragraph)
        placeholder="Có thể để trống để xem tổng quát...",
        required=False, # Không bắt buộc nhập
        max_length=500
    )
    
    boi_canh = discord.ui.TextInput(
        label="Bối cảnh của bạn (giúp luận đúng hơn)",
        style=discord.TextStyle.paragraph,
        placeholder="VD: NV văn phòng đang muốn nhảy việc / tự kinh doanh quán cà phê / SV năm cuối...",
        required=False,
        max_length=1000
    )
    
    lien_quan = discord.ui.TextInput(
        label="Liên quan tới ai / điều gì? (tùy chọn)",
        style=discord.TextStyle.short, # Ô nhập ngắn (Short)
        placeholder="VD: sếp, người yêu cũ, một dự án sắp tới...",
        required=False
    )
    
    xung_ho = discord.ui.TextInput(
        label="Xưng hô + giới tính (tùy chọn)",
        style=discord.TextStyle.short,
        placeholder="VD: Linh, nữ / anh Minh / chị Hai",
        required=False
    )
    
    ngay_sinh = discord.ui.TextInput(
        label="Ngày sinh DD/MM/YYYY (tùy chọn)",
        style=discord.TextStyle.short,
        placeholder="VD: 11/06/1999 — để tính lá bài chủ đạo",
        required=False
    )

    # Xử lý sau khi người dùng nhấn nút "Gửi" trên biểu mẫu
    async def on_submit(self, interaction: discord.Interaction):
        # Lấy dữ liệu người dùng đã nhập vào các ô
        user_cau_hoi = self.cau_hoi.value or "Xem tổng quát"
        user_boi_canh = self.boi_canh.value or "Không cung cấp"
        
        # Gọi hàm rút bài (giả định hàm draw_cards đã viết ở câu trước)
        card = draw_cards(1)[0]

        save_history(
            user_id=interaction.user.id,
            user_name=interaction.user.name,
            kieu_trai="Bói Nhanh 1 Lá 🔮",
            danh_sach_la=[f"{card['name']} ({card['orientation']})"] 
        )
        
        # Tạo Embed hiển thị kết quả kèm thông tin họ đã nhập
        embed = discord.Embed(title="🔮 Kết Quả Bói Nhanh 1 Lá", color=0x9B59B6)
        embed.add_field(name="❓ Câu hỏi của bạn:", value=user_cau_hoi, inline=False)
        embed.add_field(name=f"🃏 Lá bài nhận được: {card['name']}", value=f"Trạng thái:", inline=False)
        embed.add_field(name="📝 Luận giải diễn biến:", value=card['meaning'], inline=False)
        
        await interaction.response.send_message(f"🔮 Kết quả trải bài của {interaction.user.mention}:", embed=embed)

class CoKhongModal(discord.ui.Modal, title="⚖️ Trải Bài Có / Không"):
    # Ô nhập câu hỏi dạng Có / Không
    cau_hoi = discord.ui.TextInput(
        label="Câu hỏi Có / Không của bạn",
        style=discord.TextStyle.paragraph,
        placeholder="VD: Mình và người cũ có quay lại với nhau trong tháng này không?...",
        required=True, # Bắt buộc phải nhập câu hỏi
        max_length=500
    )
    
    boi_canh = discord.ui.TextInput(
        label="Bối cảnh của bạn (giúp luận đúng hơn)",
        style=discord.TextStyle.paragraph,
        placeholder="VD: Hai đứa đã chia tay được 2 tháng và hiện đang im lặng...",
        required=False,
        max_length=1000
    )
    
    xung_ho = discord.ui.TextInput(
        label="Xưng hô + giới tính (tùy chọn)",
        style=discord.TextStyle.short,
        placeholder="VD: Nam, nữ / mình là nữ, họ là nam...",
        required=False
    )

    # Xử lý khi nhấn nút Gửi
    async def on_submit(self, interaction: discord.Interaction):
        user_cau_hoi = self.cau_hoi.value
        
        # Rút 1 lá bài ngẫu nhiên (sử dụng hàm draw_cards đã viết ở các câu trước)
        card = draw_cards(1)[0]

        save_history(
            user_id=interaction.user.id,
            user_name=interaction.user.name,
            kieu_trai="Bói Có / Không ⚖️",
            danh_sach_la=[f"{card['name']} ({card['orientation']})"]
        )
        
        # Logic quyết định Có hay Không dựa trên hướng lá bài
        # Nếu trạng thái chứa chữ "Xuôi" -> CÓ, ngược lại -> KHÔNG
        if "Xuôi" in card['orientation']:
            ket_qua = "🟢 CÓ (Chắc chắn hoặc có xu hướng tích cực)"
            mau_sac = 0x2ECC71 # Màu xanh lá
        else:
            ket_qua = "🔴 KHÔNG (Trở ngại hoặc có xu hướng tiêu cực)"
            mau_sac = 0xE74C3C # Màu đỏ

        # Tạo Embed hiển thị kết quả cho người dùng
        embed = discord.Embed(title="⚖️ Kết Quả Trải Bài Có / Không", color=mau_sac)
        embed.add_field(name="❓ Câu hỏi:", value=user_cau_hoi, inline=False)
        embed.add_field(name="✨ Câu trả lời của thông điệp:", value=f"**{ket_qua}**", inline=False)
        embed.add_field(name=f"🃏 Lá bài định hướng: {card['name']}", value=f"Trạng thái:\nÝ nghĩa:", inline=False)
        
        await interaction.response.send_message(f"⚖️ Quẻ bài Có/Không của {interaction.user.mention}:", embed=embed)

class QkHtTlModal(discord.ui.Modal, title="⏳ Trải Bài Quá Khứ - Hiện Tại - Tương Lai"):
    # Ô nhập vấn đề cần xem
    cau_hoi = discord.ui.TextInput(
        label="Vấn đề / Sự việc bạn muốn bốc bài",
        style=discord.TextStyle.paragraph,
        placeholder="VD: Diễn biến công việc sắp tới của mình / Chuyện tình cảm dạo này đang bế tắc...",
        required=True, # Bắt buộc nhập để có chủ đề luận giải
        max_length=500
    )
    
    boi_canh = discord.ui.TextInput(
        label="Bối cảnh chi tiết (giúp luận đúng hơn)",
        style=discord.TextStyle.paragraph,
        placeholder="VD: Mình mới phỏng vấn một công ty tuần trước và đang đợi kết quả...",
        required=False,
        max_length=1000
    )
    
    xung_ho = discord.ui.TextInput(
        label="Xưng hô + giới tính (tùy chọn)",
        style=discord.TextStyle.short,
        placeholder="VD: Nữ, sinh năm 2001 / Mình là nam...",
        required=False
    )

    # Xử lý khi nhấn nút Gửi
    async def on_submit(self, interaction: discord.Interaction):
        user_cau_hoi = self.cau_hoi.value
        
        # Rút 3 lá bài ngẫu nhiên không trùng nhau cho 3 mốc thời gian
        cards = draw_cards(3)

        save_history(
            user_id=interaction.user.id,
            user_name=interaction.user.name,
            kieu_trai="Quá Khứ - Hiện Tại - Tương Lai ⏳",
            danh_sach_la=[f"{c['name']} ({c['orientation']})" for c in cards]
        )
        
        # Tạo Embed hiển thị dòng chảy thời gian của vấn đề
        embed = discord.Embed(
            title="⏳ Kết Quả Trải Bài Quá Khứ - Hiện Tại - Tương Lai", 
            description=f"🔮 **Vấn đề xem:** {user_cau_hoi}",
            color=0xE67E22 # Màu cam ấm áp hợp tone thời gian
        )
        
        # Thêm 3 lá bài tương ứng vào Embed
        embed.add_field(
            name="1. Quá Khứ (Gốc rễ vấn đề)", 
            value=f"🃏 **Lá bài:** {cards[0]['name']} ({cards[0]['orientation']})\n📝 **Ý nghĩa:** {cards[0]['meaning']}", 
            inline=False
        )
        embed.add_field(
            name="2. Hiện Tại (Trạng thái cốt lõi lúc này)", 
            value=f"🃏 **Lá bài:** {cards[1]['name']} ({cards[1]['orientation']})\n📝 **Ý nghĩa:** {cards[1]['meaning']}", 
            inline=False
        )
        embed.add_field(
            name="3. Tương Lai (Xu hướng / Kết quả sắp tới)", 
            value=f"🃏 **Lá bài:** {cards[2]['name']} ({cards[2]['orientation']})\n📝 **Ý nghĩa:** {cards[2]['meaning']}", 
            inline=False
        )
        
        await interaction.response.send_message(f"⏳ Trải bài 3 lá của {interaction.user.mention}:", embed=embed)

class TinhYeuModal(discord.ui.Modal, title="💕 Trải Bài Tình Yêu"):
    # Ô nhập mối quan hệ hiện tại
    moi_quan_he = discord.ui.TextInput(
        label="Mối quan hệ hiện tại / Điều bạn muốn biết",
        style=discord.TextStyle.paragraph,
        placeholder="VD: Tìm hiểu người mới / Mối quan hệ dạo này hay cãi vã mập mờ...",
        required=True, # Bắt buộc nhập để biết trạng thái tình cảm
        max_length=500
    )
    
    boi_canh = discord.ui.TextInput(
        label="Bối cảnh chi tiết của hai bạn",
        style=discord.TextStyle.paragraph,
        placeholder="VD: Đang trong giai đoạn tìm hiểu được 3 tháng nhưng bỗng dưng đối phương lạnh nhạt...",
        required=False,
        max_length=1000
    )
    
    xung_ho_ban = discord.ui.TextInput(
        label="Xưng hô + giới tính của BẠN (tùy chọn)",
        style=discord.TextStyle.short,
        placeholder="VD: Linh, nữ, 2002",
        required=False
    )

    xung_ho_ho = discord.ui.TextInput(
        label="Xưng hô + giới tính của ĐỐI PHƯƠNG (tùy chọn)",
        style=discord.TextStyle.short,
        placeholder="VD: Hoàng, nam, 1999",
        required=False
    )

    # Xử lý khi nhấn nút Gửi
    async def on_submit(self, interaction: discord.Interaction):
        user_relationship = self.moi_quan_he.value
        
        # Rút 2 lá bài không trùng nhau cho góc nhìn 2 phía
        cards = draw_cards(2)

        save_history(
            user_id=interaction.user.id,
            user_name=interaction.user.name,
            kieu_trai="Trải Bài Tình Yêu 💕",
            danh_sach_la=[f"{card['name']} ({card['orientation']})" for card in cards]
        )
        
        # Tạo Embed hiển thị kết quả tình duyên
        embed = discord.Embed(
            title="💕 Kết Quả Trải Bài Tình Yêu (Góc Nhìn 2 Phía)", 
            description=f"🔮 **Câu chuyện của hai bạn:** {user_relationship}",
            color=0xE91E63 # Màu hồng tình yêu ngọt ngào
        )
        
        # Thêm thông tin 2 lá bài vào Embed
        embed.add_field(
            name="👩‍❤️‍👨 1. Góc nhìn / Năng lượng từ phía BẠN", 
            value=f"🃏 **Lá bài:** {cards[0]['name']} ({cards[0]['orientation']})\n📝 **Ý nghĩa:** {cards[0]['meaning']}", 
            inline=False
        )
        embed.add_field(
            name="👨‍❤️‍👩 2. Góc nhìn / Năng lượng từ phía ĐỐI PHƯƠNG", 
            value=f"🃏 **Lá bài:** {cards[1]['name']} ({cards[1]['orientation']})\n📝 **Ý nghĩa:** {cards[1]['meaning']}", 
            inline=False
        )
        
        await interaction.response.send_message(f"💕 Trải bài tình yêu của {interaction.user.mention}:", embed=embed)

class GiaiQyetModal(discord.ui.Modal, title="🧭 Hướng Giải Quyết"):
    # Ô nhập khó khăn / vấn đề lớn cần tìm lối thoát
    van_de = discord.ui.TextInput(
        label="Nêu vấn đề / bế tắc bạn đang gặp phải",
        style=discord.TextStyle.paragraph,
        placeholder="VD: Dự án đang bị đình trệ, bất đồng ý kiến với cộng sự không biết giải quyết ra sao...",
        required=True, # Bắt buộc nhập
        max_length=600
    )
    
    nguyen_nhan = discord.ui.TextInput(
        label="Bạn nghĩ nguyên nhân cốt lõi do đâu? (tùy chọn)",
        style=discord.TextStyle.paragraph,
        placeholder="VD: Do giao tiếp kém và áp lực doanh số quá lớn từ cấp trên...",
        required=False,
        max_length=600
    )
    
    xung_ho = discord.ui.TextInput(
        label="Xưng hô + giới tính (tùy chọn)",
        style=discord.TextStyle.short,
        placeholder="VD: Nam, 25 tuổi / Mình là nữ...",
        required=False
    )

    # Xử lý khi nhấn nút Gửi
    async def on_submit(self, interaction: discord.Interaction):
        user_van_de = self.van_de.value
        
        # Rút đúng 5 lá bài ngẫu nhiên không trùng nhau cho sơ đồ 5 góc độ giải quyết
        cards = draw_cards(5)

        save_history(
            user_id=interaction.user.id,
            user_name=interaction.user.name,
            kieu_trai="Sơ Đồ 5 Lá Phân Tích & Hướng Giải Quyết 🧭",
            danh_sach_la=[f"{card['name']} ({card['orientation']})" for card in cards]
        )

        # Tạo Embed hiển thị phân tích 5 bước giải quyết vấn đề
        embed = discord.Embed(
            title="🧭 Sơ Đồ 5 Lá Phân Tích & Hướng Giải Quyết", 
            description=f"📌 **Vấn đề cốt lõi:** {user_van_de}",
            color=0x3498DB # Màu xanh dương sáng suốt, định hướng
        )
        
        # Sắp xếp 5 lá tương ứng với các vị trí phân tích
        embed.add_field(
            name="📍 Lá 1: Thực trạng hiện tại", 
            value=f"🃏 **{cards[0]['name']}** ({cards[0]['orientation']})\n📝 {cards[0]['meaning']}", 
            inline=False
        )
        embed.add_field(
            name="⚠️ Lá 2: Trở ngại / Thách thức chính", 
            value=f"🃏 **{cards[1]['name']}** ({cards[1]['orientation']})\n📝 {cards[1]['meaning']}", 
            inline=False
        )
        embed.add_field(
            name="💡 Lá 3: Yếu tố tiềm ẩn / Lời khuyên", 
            value=f"🃏 **{cards[2]['name']}** ({cards[2]['orientation']})\n📝 {cards[2]['meaning']}", 
            inline=False
        )
        embed.add_field(
            name="🏃‍♂️ Lá 4: Hành động cần làm ngay", 
            value=f"🃏 **{cards[3]['name']}** ({cards[3]['orientation']})\n📝 {cards[3]['meaning']}", 
            inline=False
        )
        embed.add_field(
            name="🔮 Lá 5: Kết quả tiềm năng sau giải quyết", 
            value=f"🃏 **{cards[4]['name']}** ({cards[4]['orientation']})\n📝 {cards[4]['meaning']}", 
            inline=False
        )
        
        await interaction.response.send_message(f"🧭 Trải bài định hướng của {interaction.user.mention}:", embed=embed)

class CelticModal(discord.ui.Modal, title="✨ Thập Tự Celtic (10 lá)"):
    # Ô nhập đại sự / vấn đề lớn cần mổ xẻ toàn diện
    van_de = discord.ui.TextInput(
        label="Vấn đề lớn cần mổ xẻ toàn diện",
        style=discord.TextStyle.paragraph,
        placeholder="VD: Toàn cảnh sự nghiệp và tài chính của mình trong 6 tháng tới...",
        required=True, # Bắt buộc nhập
        max_length=600
    )
    
    boi_canh = discord.ui.TextInput(
        label="Bối cảnh chi tiết và mong muốn của bạn",
        style=discord.TextStyle.paragraph,
        placeholder="VD: Mình đang làm quản lý nhưng cảm thấy áp lực và có ý định ra khởi nghiệp riêng...",
        required=False,
        max_length=1000
    )
    
    xung_ho = discord.ui.TextInput(
        label="Xưng hô + giới tính + ngày sinh (tùy chọn)",
        style=discord.TextStyle.short,
        placeholder="VD: Nam, 15/08/1995",
        required=False
    )

    # Xử lý khi nhấn nút Gửi
    async def on_submit(self, interaction: discord.Interaction):
        user_van_de = self.van_de.value
        
        # Rút đúng 10 lá bài ngẫu nhiên không trùng nhau cho sơ đồ Celtic Cross
        cards = draw_cards(10)

        save_history(
            user_id=interaction.user.id,
            user_name=interaction.user.name,
            kieu_trai="Thập Tự Celtic (10 lá)",
            danh_sach_la=[f"{card['name']} ({card['orientation']})" for card in cards]
        )

        # Do 10 lá bài quá dài, nếu nhét chung vào 1 Embed sẽ rất rối hoặc vượt quá giới hạn ký tự.
        # Giải pháp tối ưu là chia thành 2 Embed gửi cùng lúc:
        
        # EMBED 1: Khung cốt lõi (Vấn đề và Tác động nội tại)
        embed1 = discord.Embed(
            title="✨ Kết Quả Thập Tự Celtic - Phần 1: Tâm Điểm",
            description=f"📌 **Đại sự cần mổ xẻ:** {user_van_de}\n\n"
                        f"🔹 **Lá 1: Bản chất hiện tại:** **{cards[0]['name']}** ({cards[0]['orientation']})\n↳ *{cards[0]['meaning']}*\n\n"
                        f"🔹 **Lá 2: Trở ngại trực tiếp:** **{cards[1]['name']}** ({cards[1]['orientation']})\n↳ *{cards[1]['meaning']}*\n\n"
                        f"🔹 **Lá 3: Gốc rễ/Quá khứ xa:** **{cards[2]['name']}** ({cards[2]['orientation']})\n↳ *{cards[2]['meaning']}*\n\n"
                        f"🔹 **Lá 4: Quá khứ gần/Điều vừa qua:** **{cards[3]['name']}** ({cards[3]['orientation']})\n↳ *{cards[3]['meaning']}*\n\n"
                        f"🔹 **Lá 5: Mục tiêu/Mặt ý thức:** **{cards[4]['name']}** ({cards[4]['orientation']})\n↳ *{cards[4]['meaning']}*",
            color=0x9B59B6 # Màu tím huyền bí
        )
        
        # EMBED 2: Khung mở rộng (Yếu tố ngoại cảnh và Kết quả)
        embed2 = discord.Embed(
            title="✨ Kết Quả Thập Tự Celtic - Phần 2: Xu Hướng",
            description=f"🔹 **Lá 6: Tương lai gần:** **{cards[5]['name']}** ({cards[5]['orientation']})\n↳ *{cards[5]['meaning']}*\n\n"
                        f"🔹 **Lá 7: Vị thế/Thái độ của bạn:** **{cards[6]['name']}** ({cards[6]['orientation']})\n↳ *{cards[6]['meaning']}*\n\n"
                        f"🔹 **Lá 8: Yếu tố môi trường/Ngoại cảnh:** **{cards[7]['name']}** ({cards[7]['orientation']})\n↳ *{cards[7]['meaning']}*\n\n"
                        f"🔹 **Lá 9: Hy vọng hoặc Nỗi sợ thầm kín:** **{cards[8]['name']}** ({cards[8]['orientation']})\n↳ *{cards[8]['meaning']}*\n\n"
                        f"🔹 **Lá 10: Kết quả chung cuộc:** **{cards[9]['name']}** ({cards[9]['orientation']})\n↳ *{cards[9]['meaning']}*",
            color=0x8E44AD
        )
        
        # Gửi đồng thời cả 2 Embed trong một tin nhắn để hiển thị liền mạch
        await interaction.response.send_message(
            content=f"✨ Trải bài Thập Tự Celtic 10 lá chuyên sâu của {interaction.user.mention}:", 
            embeds=[embed1, embed2]
        )
    
class TarotMenuView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None) # Không hết hạn tương tác

        self.voice = "Dịu dàng"  # Giọng đọc mặc định
        self.destination = "public"  # Nơi nhận kết quả mặc định

    # ---- HÀNG BUTTON 1 ----
    @discord.ui.button(label="Lá hôm nay", style=discord.ButtonStyle.primary, emoji="🌅", row=0)
    async def la_hom_nay(self, interaction: discord.Interaction, button: discord.ui.Button):
        # 1. KIỂM TRA COOLDOWN TRƯỚC
        can_draw, error_message = can_draw_today(interaction.user.id)
        
        if not can_draw:
            # Nếu đã rút rồi, gửi thông báo ẩn chỉ mình họ thấy và dừng hàm
            await interaction.response.send_message(error_message, ephemeral=True)
            return

        # 2. NẾU CHƯA RÚT -> TIẾN HÀNH RÚT BÀI BÌNH THƯỜNG
        card = draw_cards(1)[0]
        
        # Lưu lịch sử (hàm mới sẽ tự động đính kèm timestamp)
        save_history(
            user_id=interaction.user.id,
            user_name=interaction.user.name,
            kieu_trai="Lá Bài Hôm Nay 🌅",
            danh_sach_la=[f"{card['name']} ({card['orientation']})"]
        )
        
        # Tạo và gửi Embed kết quả
        embed = discord.Embed(title="🌅 Lá Bài Ngày Hôm Nay Của Bạn", color=0xFFD700)
        embed.add_field(name=f"Lá bài: {card['name']}", value=f"Trạng thái:", inline=False)
        embed.add_field(name="Thông điệp:", value=card['meaning'], inline=False)
        embed.set_footer(text=f"Giọng đọc: {self.voice}")

        giai_dap_view = GiaiDapButtonView(la_bai_info=card, giong_doc=self.voice)

        if self.destination == "dm":
            await interaction.user.send(embed=embed, view=giai_dap_view)
            await interaction.response.send_message("🔮 Mình đã gửi kết quả vào DM của bạn rồi nhé!", ephemeral=True)
        else:
            await interaction.response.send_message(f"🔮 Kết quả ngày mới của {interaction.user.mention}:", embed=embed, view=giai_dap_view)

    @discord.ui.button(label="Bói nhanh", style=discord.ButtonStyle.secondary, emoji="🔮", row=0)
    async def boi_nhanh(self, interaction: discord.Interaction, button: discord.ui.Button):
        # Mở modal để người dùng nhập câu hỏi
        modal = BoiNhanhModal()
        await interaction.response.send_modal(modal)

    @discord.ui.button(label="Có/Không", style=discord.ButtonStyle.secondary, emoji="⚖️", row=0)
    async def co_khong(self, interaction: discord.Interaction, button: discord.ui.Button):
        modal = CoKhongModal()
        await interaction.response.send_modal(modal)

    @discord.ui.button(label="QK·HT·TL", style=discord.ButtonStyle.secondary, emoji="⏳", row=0)
    async def qk_ht_tl(self, interaction: discord.Interaction, button: discord.ui.Button):
        modal = QkHtTlModal()
        await interaction.response.send_modal(modal)


    # ---- HÀNG BUTTON 2 ----
    @discord.ui.button(label="Tình yêu", style=discord.ButtonStyle.secondary, emoji="💕", row=1)
    async def tinh_yeu(self, interaction: discord.Interaction, button: discord.ui.Button):
        modal = TinhYeuModal()
        await interaction.response.send_modal(modal)

    @discord.ui.button(label="Giải quyết", style=discord.ButtonStyle.secondary, emoji="🧭", row=1)
    async def giai_quyet(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(GiaiQyetModal())

    @discord.ui.button(label="Celtic 10 lá", style=discord.ButtonStyle.secondary, emoji="✨", row=1)
    async def celtic(self, interaction: discord.Interaction, button: discord.ui.Button):
        modal = CelticModal()
        await interaction.response.send_modal(modal)

    @discord.ui.button(label="Lịch sử", style=discord.ButtonStyle.secondary, emoji="📜", row=1)
    async def lich_su(self, interaction: discord.Interaction, button: discord.ui.Button):
        user_history = get_history(interaction.user.id)
        
        embed = discord.Embed(
            title=f"📜 Lịch Sử Xem Bài Của {interaction.user.display_name}", 
            color=0x71717A
        )
        
        if not user_history:
            embed.description = "❌ Bạn chưa có lượt trải bài nào gần đây cùng Sakura. Hãy chọn một kiểu bói ở trên nhé!"
        else:
            description_text = "Dưới đây là tối đa 5 lượt trải bài gần nhất của bạn:\n\n"
            for i, record in enumerate(user_history, 1):
                description_text += f"**{i}. Khung trải:** {record['kieu_trai']}\n"
                description_text += f"🃏 **Lá bài bốc được:** {record['danh_sach_la']}\n"
                description_text += f"⏱️ *Trạng thái:* {record['thoi_gian']}\n"
                description_text += "───────────────────\n"
            embed.description = description_text
            
        # Gửi lịch sử ở chế độ ẩn danh (Chỉ người bấm nút nhìn thấy) để đảm bảo riêng tư
        await interaction.response.send_message(embed=embed, ephemeral=True)


    # ---- HÀNG DROPDOWN SELECTION ----
    # Menu chọn giọng đọc (Dịu dàng, Mạnh mẽ,...)
    @discord.ui.select(
        placeholder="🌸 Dịu dàng",
        options=[
            discord.SelectOption(label="Dịu dàng", value="diu_dang", emoji="🌸", default=True),
            discord.SelectOption(label="Huyền bí", value="huyen_bi", emoji="🔮"),
            discord.SelectOption(label="Thẳng thắn", value="thang_than", emoji="⚔️")
        ],
        row=2
    )
    async def select_voice(self, interaction: discord.Interaction, select: discord.ui.Select):
        self.voice = select.values[0]  # Cập nhật giọng đọc người dùng chọn
        await interaction.response.send_message(f"⚙️ Đã chuyển giọng đọc Tarot sang: **{self.voice}**", ephemeral=True)

    # Menu chọn nơi nhận kết quả (Công khai, DM,...)
    @discord.ui.select(
        placeholder="🌐 Công khai tại kênh",
        options=[
            discord.SelectOption(label="Công khai tại kênh", value="public", emoji="🌐", default=True),
            discord.SelectOption(label="Nhắn tin riêng (DM)", value="dm", emoji="📥")
        ],
        row=3
    )
    async def select_destination(self, interaction: discord.Interaction, select: discord.ui.Select):
        self.destination = select.values[0]  # Cập nhật nơi nhận kết quả
        text = "Công khai tại kênh" if self.destination == "public" else "Nhắn tin riêng (DM)"
        await interaction.response.send_message(f"⚙️ Nơi nhận kết quả đã đổi thành: **{text}**", ephemeral=True)
