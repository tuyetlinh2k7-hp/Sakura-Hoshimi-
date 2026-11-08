<div align="center">

# 🌸 SakuraBot - Discord Bot Đa Năng Tiếng Việt & Web Dashboard

[![Python](https://img.shields.io/badge/Python-3.10%2B-blue.svg?logo=python&logoColor=white)](https://www.python.org/)
[![discord.py](https://img.shields.io/badge/discord.py-2.7.1%2B-5865F2.svg?logo=discord&logoColor=white)](https://github.com/Rapptz/discord.py)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Lavalink](https://img.shields.io/badge/Audio-Lavalink%20v4-red.svg)](https://github.com/lavalink-devs/Lavalink)
[![AI Powered](https://img.shields.io/badge/AI-Gemini%20%7C%20OpenAI%20%7C%20Groq-orange.svg)](https://ai.google.dev/)

**SakuraBot** là bot Discord mã nguồn mở mạnh mẽ, giao diện tiếng Việt thân thiện, tích hợp **Web Dashboard** thời gian thực, hệ thống phát nhạc đa luồng bot phụ, minigame kinh tế/gacha hấp dẫn, trợ lý AI thông minh và bộ công cụ bảo mật máy chủ Discord chuyên nghiệp.

[✨ Tính năng](#-tính-năng-nổi-bật) • [🚀 Cài đặt nhanh](#-hướng-dẫn-cài-đặt) • [⚙️ Cấu hình .env](#️-cấu-hình-biến-môi-trường-env) • [📖 Danh sách lệnh](#-danh-sách-lệnh-tiêu-biểu) • [🤝 Đóng góp](#-đóng-góp--bản-quyền)

---

</div>

## ✨ Tính năng nổi bật

### 🛡️ 1. Bảo vệ & Quản trị Máy chủ Toàn diện
- **Unified Anti**: Hệ thống chống phá All-In-One (Anti-Raid, Anti-Nuke, Anti-Spam, Anti-Link, Anti-Invite).
- **AutoMod thông minh**: Tự động lọc từ ngữ khiếm nhã, ngăn chặn spam tin nhắn liên tục và xúc phạm bot.
- **Hệ thống Logs chuyên sâu**: Ghi lại lịch sử chỉnh sửa/xóa tin nhắn, hoạt động voice, thành viên ra/vào, audit log, boost server và tự động thả cảm xúc (Auto Reaction).

### 🎵 2. Phát nhạc Đa Luồng (Multi-Bot Wavelink / Lavalink)
- Tích hợp **Lavalink v4** và **Wavelink** với chất lượng âm thanh 24/7 ổn định cao.
- **Hỗ trợ Multi-Token**: Cho phép phân bổ danh sách bot phụ (Music Sub-Bots) để phát nhạc độc lập trên nhiều voice channel cùng một lúc mà không bị nghẽn luồng.

### 🤖 3. Trí tuệ Nhân tạo (Multi-LLM AI Assistant)
- Hỗ trợ đa mô hình AI: **Google Gemini**, **Groq LLaMA**, **OpenAI**.
- Kênh Chatbot AI thông minh trò chuyện tự nhiên bằng tiếng Việt.
- Bói bài **Tarot AI** và giải đoán cung hoàng đạo (**Zodiac**) chi tiết theo ngữ cảnh.

### 🎮 4. Minigames & Hệ thống Kinh tế Xã hội (Economy System)
- **Waifu Gacha System**: Thu thập hàng trăm nhân vật Anime/Game độc đáo với tỷ lệ gacha minh bạch, nâng cấp và sưu tầm thẻ bài.
- **Kinh tế chân thực**: Hệ thống Ngân hàng (gửi tiết kiệm có kỳ hạn, vay vốn), Chợ P2P, Việc làm (`work`), Đào khoáng (`mining`), Câu cá (`fishing`).
- **Tương tác xã hội**: Kết hôn (`marriage`), Hệ thống Tù tội (`jail`), Điểm danh chuỗi ngày (`streaks`), Thành tựu (`achievements`).
- **Trò chơi giải trí**: Game nối từ Tiếng Việt (từ điển 900.000+ từ), Cờ caro (XO), Ai là triệu phú, Casino xúc xắc/blackjack.

### 🌐 5. Web Dashboard Quản trị Hiện đại
- Đăng nhập bảo mật thông qua **Discord OAuth2**.
- Tự động lọc danh sách Server theo quyền Quản trị viên của người dùng.
- Theo dõi thông số tài nguyên máy chủ (CPU, RAM, Uptime), live console log terminal.
- Quản lý tập tin và cấu hình bot trực tiếp trên trình duyệt.

### ⛏️ 6. Tích hợp Máy chủ Minecraft & Dịch vụ Game
- Quản lý trạng thái và console server Minecraft từ xa (hỗ trợ tích hợp Falixnodes API).
- Hệ thống liên kết tài khoản Discord và tài khoản Minecraft.
- Tự động điểm danh HoYoLab hàng ngày cho Genshin Impact, Honkai: Star Rail.

---

## 📁 Cấu trúc Thư mục

```plaintext
SakuraBot/
├── Anti/                 # Module phòng thủ, chống raid, nuke, spam, lọc link
├── Checks_vi/             # Các bộ kiểm tra quyền hạn, prefix, tiện ích bổ trợ
├── Command_vi/            # Toàn bộ cogs lệnh tính năng (nhạc, game, kinh tế,...)
├── Database/              # Class kết nối và khởi tạo cơ sở dữ liệu SQLite
├── Logs_vi/               # Module ghi nhận log hệ thống và sự kiện server
├── data/                  # Dữ liệu tĩnh, từ điển, file mẫu cấu hình và logic DB
├── languages/             # Tập tin đa ngôn ngữ (Tiếng Việt, Tiếng Anh)
├── view/                  # Giao diện Discord UI (Buttons, Modals, Selects)
├── web/                   # Web Dashboard (Flask/aiohttp backend, HTML templates, CSS/JS)
├── scripts/               # Các công cụ và script hỗ trợ
├── config.py              # File nạp cấu hình tập trung từ biến môi trường
├── .env.example           # File mẫu biến môi trường cần thiết
├── .gitignore             # Danh sách loại trừ các file bí mật và dữ liệu nhạy cảm
├── requirements.txt       # Danh sách thư viện Python phụ thuộc
└── run.py                 # File khởi động chính của Bot
```

---

## 🚀 Hướng dẫn Cài đặt

### Yêu cầu Hệ thống
- **Python**: Phiên bản `3.10` trở lên (Khuyến nghị 3.11 hoặc 3.12).
- **Git**: Đã cài đặt trên máy.
- **Java**: Phiên bản `17` trở lên (nếu tự host server Lavalink phát nhạc).

### Bước 1: Tải mã nguồn về máy
```bash
git clone https://github.com/<tai-khoan-cua-ban>/SakuraBot.git
cd SakuraBot
```

### Bước 2: Tạo môi trường ảo và cài đặt thư viện
```bash
# Tạo môi trường ảo Python
python -m venv venv

# Kích hoạt môi trường ảo:
# Trên Windows:
venv\Scripts\activate
# Trên Linux/macOS:
source venv/bin/activate

# Cài đặt toàn bộ dependencies
pip install -r requirements.txt
```

### Bước 3: Cấu hình biến môi trường
Sao chép file `.env.example` thành file `.env`:
```bash
# Trên Windows CMD/PowerShell:
copy .env.example .env
# Trên Linux/macOS:
cp .env.example .env
```
Mở file `.env` bằng trình soạn thảo (VSCode, Notepad, Nano) và điền đầy đủ các thông tin:
- `DISCORD_TOKEN`: Token bot lấy từ [Discord Developer Portal](https://discord.com/developers/applications).
- `PREFIX`: Prefix lệnh mặc định (ví dụ: `s!`).
- `OWNER_ID`: Discord User ID của bạn.
- `GEMINI_API_KEY` / `OPENAI_API_KEY`: API Key để dùng các tính năng AI.
- `LAVALINK_HOST`, `LAVALINK_PASSWORD`: Thông tin kết nối máy chủ Lavalink.

### Bước 4: Khởi động Bot
```bash
python run.py
```
> [!TIP]
> Khi bot khởi động thành công, Web Dashboard sẽ tự động khả dụng tại địa chỉ `http://localhost:10272` (hoặc cổng được cấu hình trong `.env`).

---

## ⚙️ Cấu hình Biến môi trường (.env)

| Biến môi trường | Bắt buộc | Mô tả |
| :--- | :---: | :--- |
| `DISCORD_TOKEN` | **Có** | Token bot chính lấy từ Discord Developer Portal. |
| `PREFIX` | Không | Tiền tố lệnh bot (Mặc định: `s!`). |
| `OWNER_ID` | **Có** | Discord ID của người sở hữu bot (dùng cho lệnh độc quyền). |
| `GEMINI_API_KEY` | Không | API Key của Google Gemini (miễn phí tại Google AI Studio). |
| `GROQ_API_KEY` | Không | API Key từ Groq Cloud để tăng tốc suy luận AI. |
| `OPENAI_API_KEY` | Không | API Key từ OpenAI (nếu dùng GPT-4o / GPT-3.5). |
| `LAVALINK_HOST` | Không | Địa chỉ máy chủ Lavalink (Mặc định: `127.0.0.1`). |
| `LAVALINK_PORT` | Không | Cổng kết nối Lavalink (Mặc định: `2334`). |
| `LAVALINK_PASSWORD` | Không | Mật khẩu xác thực Lavalink. |
| `WEB_PORT` | Không | Cổng chạy Web Dashboard (Mặc định: `10272`). |
| `DISCORD_CLIENT_ID` | Không | Client ID ứng dụng Discord (dùng cho đăng nhập Web OAuth2). |
| `DISCORD_CLIENT_SECRET` | Không | Client Secret ứng dụng Discord. |

---

## 📖 Danh sách Lệnh tiêu biểu

Dưới đây là một số lệnh phổ biến (giả sử prefix mặc định là `s!`):

| Lệnh | Phân loại | Mô tả |
| :--- | :--- | :--- |
| `s!help` | Cơ bản | Hiển thị bảng hướng dẫn và danh sách tất cả các lệnh. |
| `s!ping` | Cơ bản | Kiểm tra độ trễ phản hồi của Bot và Discord API. |
| `s!play <tên bài hát / link>` | Âm nhạc | Phát nhạc từ YouTube, Spotify, SoundCloud qua Lavalink. |
| `s!stop` / `s!skip` / `s!queue` | Âm nhạc | Điều khiển bài hát, tạm dừng, bỏ qua hoặc xem hàng đợi. |
| `s!gacha` | Trò chơi | Mở menu quay thưởng Waifu Gacha anime đặc sắc. |
| `s!bank` | Kinh tế | Mở tài khoản ngân hàng, gửi tiết kiệm, quản lý số dư. |
| `s!work` | Kinh tế | Làm việc ngẫu nhiên nhận coins theo thời gian thực. |
| `s!fish` / `s!mine` | Kinh tế | Đi câu cá hoặc khai thác khoáng sản để bán lấy tiền. |
| `s!anti` | Bảo mật | Bảng thiết lập hệ thống bảo vệ máy chủ (Admin only). |
| `s!setlog` | Quản trị | Cấu hình kênh ghi log cho từng loại sự kiện máy chủ. |
| `s!ai <câu hỏi>` | AI | Trò chuyện trực tiếp cùng trợ lý AI tiếng Việt. |
| `s!tarot` | Tâm linh | Rút một lá bài Tarot và nhận luận giải chi tiết từ AI. |

---

## 🔒 Bảo mật & Lưu ý quan trọng

> [!WARNING]
> - **Tuyệt đối không đẩy file `.env` lên GitHub**: File này chứa các Token và API Key bí mật. File `.gitignore` đã được cấu hình sẵn để bỏ qua file này.
> - **Cơ sở dữ liệu cá nhân**: Các file SQLite (`*.db`) và dữ liệu người dùng thực tế sẽ không được đưa vào repository mã nguồn mở để bảo vệ quyền riêng tư người dùng. Khi bot khởi chạy lần đầu, cơ sở dữ liệu sẽ tự động được khởi tạo sạch sẽ.

---

## 🤝 Đóng góp & Bản quyền

- Xem chi tiết tại [CONTRIBUTING.md](CONTRIBUTING.md) nếu bạn muốn đóng góp tính năng hoặc sửa lỗi.
- Dự án được phân phối dưới giấy phép **MIT License**. Xem chi tiết tại [LICENSE](LICENSE).

---

<div align="center">
  <sub>Được phát triển với tất cả tình yêu thương dành cho cộng đồng Discord Việt Nam 🌸</sub>
</div>
