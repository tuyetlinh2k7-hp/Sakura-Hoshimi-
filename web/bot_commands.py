from typing import List, Dict, Any, Optional

CATEGORIES = {
    "all": {"label": "Tất Cả", "icon": "🌸", "color": "#ff79c6"},
    "fishing": {"label": "Câu Cá", "icon": "🎣", "color": "#ff6b9d"},
    "core": {"label": "Cốt Lõi", "icon": "✨", "color": "#bd93f9"},
    "economy": {"label": "Kinh Tế & Level", "icon": "💰", "color": "#ffb86c"},
    "music": {"label": "Âm Nhạc", "icon": "🎵", "color": "#8be9fd"},
    "moderation": {"label": "Quản Trị", "icon": "🛡️", "color": "#ff5555"},
    "utility": {"label": "Tiện Ích", "icon": "⚙️", "color": "#50fa7b"},
    "games": {"label": "Trò Chơi & Anime", "icon": "🎮", "color": "#f1fa8c"},
    "anti": {"label": "Bảo Mật Anti", "icon": "⚔️", "color": "#ff79c6"},
    "owner": {"label": "Chủ Bot", "icon": "👑", "color": "#ffd700"}
}

BOT_COMMANDS_CATALOG: List[Dict[str, Any]] = [
    {
        "name": "fishing cast",
        "category": "fishing",
        "syntax": "/fishing cast hoặc s!f [khu_vực]",
        "description": "Thả cần câu cá đại dương (QTE săn boss biển, vớt rương báu & gom rác tái chế).",
        "aliases": ["s!f", "s!fish", "s!fcast"],
        "example": "/fishing cast | s!f bien_sau",
        "permissions": "Member"
    },
    {
        "name": "fishing inv",
        "category": "fishing",
        "syntax": "/fishing inv hoặc s!inv",
        "description": "Xem túi đồ câu, danh sách cá đã câu, cấp cường hóa cần câu và báu vật.",
        "aliases": ["s!inv", "s!tuido", "s!gio"],
        "example": "s!inv",
        "permissions": "Member"
    },
    {
        "name": "fishing shop",
        "category": "fishing",
        "syntax": "/fishing shop hoặc s!fshop",
        "description": "Cửa hàng mua bán cần câu cao cấp, mồi câu đặc biệt, pet trợ thủ và túi cá.",
        "aliases": ["s!fshop", "s!shop"],
        "example": "s!fshop",
        "permissions": "Member"
    },
    {
        "name": "fishing sell",
        "category": "fishing",
        "syntax": "/fishing sell [loại_cá / all] hoặc s!sell",
        "description": "Bán nhanh các loại cá trong túi theo phẩm chất hoặc bán toàn bộ để lấy Coins.",
        "aliases": ["s!sell"],
        "example": "s!sell all | s!sell huyen_thoai",
        "permissions": "Member"
    },
    {
        "name": "fishing sell mutation",
        "category": "fishing",
        "syntax": "s!sellmut hoặc s!f sell mutation",
        "description": "Bán toàn bộ cá đột biến gen quý hiếm trong túi đồ lấy số lượng Coins cực lớn.",
        "aliases": ["s!sellmut", "s!sellmutation"],
        "example": "s!sellmut",
        "permissions": "Member"
    },
    {
        "name": "fishing zones",
        "category": "fishing",
        "syntax": "s!zones hoặc /fishing zones",
        "description": "Xem bản đồ và chọn chuyển đổi 7 vùng biển thám hiểm với buff đột biến và sinh vật độc quyền.",
        "aliases": ["s!zones", "s!vung"],
        "example": "s!zones",
        "permissions": "Member"
    },
    {
        "name": "fishing upgrade",
        "category": "fishing",
        "syntax": "/fishing upgrade hoặc s!rodup",
        "description": "Cường hóa cần câu đang cầm (lên tới cấp độ +100) tăng tỷ lệ bắt cá quý hiếm.",
        "aliases": ["s!rodup", "s!cuonghoa"],
        "example": "s!cuonghoa",
        "permissions": "Member"
    },
    {
        "name": "fishing repair",
        "category": "fishing",
        "syntax": "/fishing repair",
        "description": "Phục hồi 100% độ bền cho cần câu bị hỏng hoặc hao mòn sau các mẻ câu.",
        "aliases": [],
        "example": "/fishing repair",
        "permissions": "Member"
    },
    {
        "name": "fishing license",
        "category": "fishing",
        "syntax": "/fishing license hoặc s!fcard",
        "description": "Xuất thẻ Căn cước Cần thủ đồ họa sang xịn kèm danh hiệu và cấp độ câu cá.",
        "aliases": ["s!fcard", "s!license"],
        "example": "s!fcard",
        "permissions": "Member"
    },
    {
        "name": "fishing aquarium",
        "category": "fishing",
        "syntax": "/fishing aquarium hoặc s!thuycung",
        "description": "Thủy cung trưng bày các loài cá quý hiếm và thu lợi nhuận tiền vé thụ động.",
        "aliases": ["s!faqua", "s!thuycung", "s!baotang"],
        "example": "s!thuycung",
        "permissions": "Member"
    },
    {
        "name": "fishing cook",
        "category": "fishing",
        "syntax": "/fishing cook hoặc s!bep",
        "description": "Bếp nấu ăn hải sản với 9 công thức nấu nướng buff cực mạnh cho cần thủ.",
        "aliases": ["s!fcook", "s!bep", "s!nauan"],
        "example": "s!bep",
        "permissions": "Member"
    },
    {
        "name": "fishing fishdex",
        "category": "fishing",
        "syntax": "/fishing fishdex hoặc s!fishdex",
        "description": "Sổ tay bách khoa toàn thư ghi chép các loài sinh vật biển & nhận quà theo mốc.",
        "aliases": ["s!fdex", "s!fishdex", "s!sotay"],
        "example": "s!fishdex",
        "permissions": "Member"
    },
    {
        "name": "fishing chest",
        "category": "fishing",
        "syntax": "/fishing chest [id] hoặc s!ruong",
        "description": "Mở các loại rương báu đại dương vớt được trong quá trình câu cá.",
        "aliases": ["s!ruong", "s!fchest"],
        "example": "s!ruong",
        "permissions": "Member"
    },
    {
        "name": "fishing market",
        "category": "fishing",
        "syntax": "/fishing market hoặc s!ck",
        "description": "Sàn chứng khoán cá VN-FISH Index với giá cả biến động theo từng khung giờ.",
        "aliases": ["s!fchungkhoan", "s!ck"],
        "example": "s!ck",
        "permissions": "Member"
    },
    {
        "name": "fishing weather",
        "category": "fishing",
        "syntax": "/fishing weather",
        "description": "Xem bản tin dự báo thời tiết đại dương và tỷ lệ đột biến cá hiếm.",
        "aliases": [],
        "example": "/fishing weather",
        "permissions": "Member"
    },
    {
        "name": "fishing tournament",
        "category": "fishing",
        "syntax": "/fishing tournament hoặc s!giaidau",
        "description": "Tham gia giải đấu câu cá đại dương đua top nhận phần thưởng lớn (12:00 & 20:00).",
        "aliases": ["s!ftour", "s!giaidau"],
        "example": "s!giaidau",
        "permissions": "Member"
    },
    {
        "name": "fishing top",
        "category": "fishing",
        "syntax": "/fishing top",
        "description": "Bảng vinh danh Top 10 cần thủ câu được nhiều cá và sở hữu cá to nhất.",
        "aliases": [],
        "example": "/fishing top",
        "permissions": "Member"
    },

    {
        "name": "ping",
        "category": "core",
        "syntax": "s!ping hoặc /ping",
        "description": "Kiểm tra độ trễ phản hồi của Bot và kết nối WebSocket Lavalink.",
        "aliases": ["/ping"],
        "example": "s!ping",
        "permissions": "Member"
    },
    {
        "name": "help",
        "category": "core",
        "syntax": "s!help [tên_lệnh] hoặc /help",
        "description": "Mở danh sách hướng dẫn sử dụng lệnh phân trang tương tác kèm tìm kiếm.",
        "aliases": ["s!trogiup", "/help"],
        "example": "s!help | s!help play",
        "permissions": "Member"
    },
    {
        "name": "menu",
        "category": "core",
        "syntax": "s!menu",
        "description": "Mở bảng danh mục tính năng dạng dropdown menu lựa chọn nhanh.",
        "aliases": [],
        "example": "s!menu",
        "permissions": "Member"
    },
    {
        "name": "botinfo",
        "category": "core",
        "syntax": "s!botinfo",
        "description": "Xem thông tin chi tiết về Sakura Bot: RAM, CPU, Uptime, số lượng server.",
        "aliases": [],
        "example": "s!botinfo",
        "permissions": "Member"
    },
    {
        "name": "invite",
        "category": "core",
        "syntax": "s!invite hoặc truy cập /bot trên web",
        "description": "Lấy liên kết mời Sakura Bot trực tiếp vào server (Guild Install truyền thống).",
        "aliases": ["/bot"],
        "example": "s!invite",
        "permissions": "Member"
    },

    {
        "name": "leveling rank",
        "category": "economy",
        "syntax": "/leveling rank [@user] hoặc s!rank",
        "description": "Xem thẻ Rank đồ họa hiển thị cấp độ Level, điểm kinh nghiệm EXP và thứ hạng.",
        "aliases": ["s!rank", "s!xp", "s!level"],
        "example": "s!rank | /leveling rank @member",
        "permissions": "Member"
    },
    {
        "name": "leveling balance",
        "category": "economy",
        "syntax": "/leveling balance [@user] hoặc s!bal",
        "description": "Xem số dư tiền mặt trong ví và số dư gửi trong ngân hàng.",
        "aliases": ["s!bal", "s!balance", "s!money"],
        "example": "s!bal",
        "permissions": "Member"
    },
    {
        "name": "leveling daily",
        "category": "economy",
        "syntax": "/leveling daily hoặc s!daily",
        "description": "Điểm danh hàng ngày nhận thưởng Coins ngẫu nhiên và tích lũy chuỗi ngày.",
        "aliases": ["s!daily"],
        "example": "s!daily",
        "permissions": "Member"
    },
    {
        "name": "leveling top",
        "category": "economy",
        "syntax": "/leveling top hoặc s!lb",
        "description": "Bảng xếp hạng Top Level và Top đại gia giàu có nhất trong máy chủ.",
        "aliases": ["s!lb", "s!top", "s!leaderboard"],
        "example": "s!top",
        "permissions": "Member"
    },
    {
        "name": "bank deposit",
        "category": "economy",
        "syntax": "s!dep <số_tiền/all>",
        "description": "Gửi tiền mặt vào tài khoản ngân hàng để bảo vệ tài sản an toàn.",
        "aliases": ["s!dep"],
        "example": "s!dep 10000 | s!dep all",
        "permissions": "Member"
    },
    {
        "name": "bank withdraw",
        "category": "economy",
        "syntax": "s!with <số_tiền/all>",
        "description": "Rút tiền từ tài khoản ngân hàng về ví tiền mặt để mua sắm.",
        "aliases": ["s!with"],
        "example": "s!with 5000",
        "permissions": "Member"
    },
    {
        "name": "bank transfer",
        "category": "economy",
        "syntax": "s!pay <@user> <số_tiền>",
        "description": "Chuyển tiền mặt nhanh chóng cho Member khác trong máy chủ.",
        "aliases": ["s!pay"],
        "example": "s!pay @member 20000",
        "permissions": "Member"
    },
    {
        "name": "xu balance",
        "category": "economy",
        "syntax": "s!xu [@user]",
        "description": "Xem số dư Xu tích lũy cao cấp (chỉ nhận được qua nạp tiền hoặc do Owner cấp).",
        "aliases": ["s!xu", "s!soduxu"],
        "example": "s!xu",
        "permissions": "Member"
    },
    {
        "name": "owner addxu",
        "category": "owner",
        "syntax": "s!addxu <@user> <số_xu>",
        "description": "[Owner] Cấp/nạp thêm Xu cao cấp cho người chơi trong máy chủ.",
        "aliases": ["s!addxu"],
        "example": "s!addxu @member 500",
        "permissions": "Chủ Bot"
    },
    {
        "name": "owner removexu",
        "category": "owner",
        "syntax": "s!removexu <@user> <số_xu>",
        "description": "[Owner] Trừ bớt Xu cao cấp của người chơi trong máy chủ.",
        "aliases": ["s!removexu"],
        "example": "s!removexu @member 100",
        "permissions": "Chủ Bot"
    },
    {
        "name": "owner setxu",
        "category": "owner",
        "syntax": "s!setxu <@user> <số_xu>",
        "description": "[Owner] Thiết lập trực tiếp số lượng Xu cao cấp cho người chơi.",
        "aliases": ["s!setxu"],
        "example": "s!setxu @member 1000",
        "permissions": "Chủ Bot"
    },

    {
        "name": "music play",
        "category": "music",
        "syntax": "/music play <tên/url> hoặc s!play <tên/url>",
        "description": "Tìm kiếm và phát nhạc chất lượng cao từ YouTube, Spotify, Soundcloud 24/7.",
        "aliases": ["s!play", "s!p"],
        "example": "s!play See Tinh | /music play url:...",
        "permissions": "Phòng Voice"
    },
    {
        "name": "music panel",
        "category": "music",
        "syntax": "/music panel hoặc s!m",
        "description": "Mở bảng điều khiển phát nhạc nhúng Embed thời gian thực với đầy đủ nút bấm tương tác.",
        "aliases": ["s!m"],
        "example": "/music panel",
        "permissions": "Phòng Voice"
    },
    {
        "name": "music skip",
        "category": "music",
        "syntax": "/music skip hoặc s!skip [số_lượng]",
        "description": "Bỏ qua bài hát đang phát sang bài kế tiếp (hỗ trợ vote skip 50%).",
        "aliases": ["s!skip", "s!s"],
        "example": "s!skip",
        "permissions": "Phòng Voice"
    },
    {
        "name": "music stop",
        "category": "music",
        "syntax": "/music stop hoặc s!stop",
        "description": "Dừng phát nhạc, xóa sạch hàng đợi bài hát và cho Bot rời khỏi kênh đàm thoại.",
        "aliases": ["s!stop", "s!leave"],
        "example": "s!stop",
        "permissions": "Phòng Voice"
    },
    {
        "name": "music queue",
        "category": "music",
        "syntax": "/music queue hoặc s!queue",
        "description": "Xem danh sách các bài hát đang xếp hàng chờ phát trong máy chủ.",
        "aliases": ["s!queue", "s!q"],
        "example": "s!queue",
        "permissions": "Phòng Voice"
    },
    {
        "name": "music nowplaying",
        "category": "music",
        "syntax": "/music nowplaying hoặc s!np",
        "description": "Hiển thị thanh tiến trình phát nhạc và thông tin bài hát đang phát.",
        "aliases": ["s!np"],
        "example": "s!np",
        "permissions": "Phòng Voice"
    },
    {
        "name": "music volume",
        "category": "music",
        "syntax": "/music volume <0-200> hoặc s!vol <0-200>",
        "description": "Điều chỉnh âm lượng bài hát phát ra mượt mà không bị vỡ tiếng.",
        "aliases": ["s!vol", "s!volume"],
        "example": "s!vol 80",
        "permissions": "Phòng Voice"
    },
    {
        "name": "music loop",
        "category": "music",
        "syntax": "/music loop <off|song|queue>",
        "description": "Cài đặt chế độ lặp: Tắt lặp, lặp lại duy nhất 1 bài, hoặc lặp lại cả danh sách.",
        "aliases": [],
        "example": "/music loop mode:song",
        "permissions": "Phòng Voice"
    },
    {
        "name": "music filter",
        "category": "music",
        "syntax": "/music filter <bassboost|nightcore|vaporwave|8d|off>",
        "description": "Kích hoạt các bộ lọc hiệu ứng âm thanh đặc biệt (Bassboost, Nightcore, 8D audio).",
        "aliases": [],
        "example": "/music filter type:bassboost",
        "permissions": "Phòng Voice"
    },
    {
        "name": "music shuffle",
        "category": "music",
        "syntax": "/music shuffle",
        "description": "Xáo trộn ngẫu nhiên thứ tự các bài hát trong hàng đợi chờ phát.",
        "aliases": [],
        "example": "/music shuffle",
        "permissions": "Phòng Voice"
    },

    {
        "name": "mod panel",
        "category": "moderation",
        "syntax": "/mod panel hoặc s!mod panel",
        "description": "Bảng điều khiển quản lý và xử phạt Member vi phạm bằng giao diện nút bấm.",
        "aliases": ["s!mod panel"],
        "example": "/mod panel",
        "permissions": "Quản lý Server"
    },
    {
        "name": "mod clear",
        "category": "moderation",
        "syntax": "/mod clear <số_lượng/all> [member]",
        "description": "Xóa nhanh tin nhắn trong kênh hàng loạt (tối đa 100 tin/lần hoặc lọc theo user).",
        "aliases": ["s!mod clear"],
        "example": "/mod clear amount:50",
        "permissions": "Quản lý Tin nhắn"
    },
    {
        "name": "mod warn",
        "category": "moderation",
        "syntax": "/mod warn <member> [lý_do]",
        "description": "Cảnh cáo chính thức Member vi phạm nội quy máy chủ và lưu vào nhật ký.",
        "aliases": ["s!mod warn"],
        "example": "/mod warn member:@user reason:Spam",
        "permissions": "Quản lý Member"
    },
    {
        "name": "mod mute",
        "category": "moderation",
        "syntax": "/mod mute <member> <phút> [lý_do]",
        "description": "Cấm chat (Timeout) Member vi phạm trong khoảng thời gian chỉ định.",
        "aliases": ["s!mod mute"],
        "example": "/mod mute member:@user minutes:60",
        "permissions": "Xử phạt Member"
    },
    {
        "name": "mod kick",
        "category": "moderation",
        "syntax": "/mod kick <member> [lý_do]",
        "description": "Trục xuất Member ra khỏi máy chủ (Member vẫn có thể vào lại).",
        "aliases": ["s!mod kick"],
        "example": "/mod kick member:@user",
        "permissions": "Đuổi Member"
    },
    {
        "name": "mod ban",
        "category": "moderation",
        "syntax": "/mod ban <member> [lý_do]",
        "description": "Cấm vĩnh viễn Member tham gia máy chủ (có bước xác nhận an toàn).",
        "aliases": ["s!mod ban"],
        "example": "/mod ban member:@user",
        "permissions": "Cấm Member"
    },
    {
        "name": "mod channel",
        "category": "moderation",
        "syntax": "/mod channel <lock|unlock|hide|unhide|slowmode|nsfw|rename|reset>",
        "description": "Khóa kênh, ẩn kênh, đặt chế độ gửi tin chậm (slowmode), gắn cờ NSFW, đổi tên hoặc làm mới kênh (reset).",
        "aliases": [],
        "example": "/mod channel action:lock",
        "permissions": "Quản lý Vai trò (lock/unlock/hide/unhide) | Quản lý Kênh (slowmode/nsfw/rename/reset)"
    },
    {
        "name": "setprefix",
        "category": "moderation",
        "syntax": "s!setprefix <prefix_mới>",
        "description": "Thay đổi tiền tố lệnh mặc định (s!) cho máy chủ.",
        "aliases": [],
        "example": "s!setprefix !",
        "permissions": "Quản trị viên"
    },
    {
        "name": "mod setlang",
        "category": "moderation",
        "syntax": "/mod setlang <vi|en>",
        "description": "Chuyển đổi ngôn ngữ hiển thị của Bot sang Tiếng Việt hoặc Tiếng Anh.",
        "aliases": ["s!setlang"],
        "example": "/mod setlang lang:vi",
        "permissions": "Quản trị viên"
    },

    {
        "name": "userinfo",
        "category": "utility",
        "syntax": "s!userinfo [@user]",
        "description": "Xem chi tiết hồ sơ tài khoản: Ngày tạo, ngày vào server, danh sách role, avatar.",
        "aliases": [],
        "example": "s!userinfo @member",
        "permissions": "Member"
    },
    {
        "name": "serverinfo",
        "category": "utility",
        "syntax": "s!serverinfo",
        "description": "Xem thông tin máy chủ: Chủ sở hữu, số lượng Member, boost, kênh và role.",
        "aliases": [],
        "example": "s!serverinfo",
        "permissions": "Member"
    },
    {
        "name": "avatar",
        "category": "utility",
        "syntax": "s!avatar [@user]",
        "description": "Xem và lấy link tải ảnh đại diện độ phân giải cao của Member.",
        "aliases": [],
        "example": "s!avatar @member",
        "permissions": "Member"
    },
    {
        "name": "afk",
        "category": "utility",
        "syntax": "s!afk [lý_do]",
        "description": "Bật trạng thái tạm vắng AFK; Bot sẽ tự động thông báo khi có người tag bạn.",
        "aliases": [],
        "example": "s!afk Đi ăn cơm",
        "permissions": "Member"
    },
    {
        "name": "qr",
        "category": "utility",
        "syntax": "s!qr <nội_dung_hoặc_link>",
        "description": "Tạo mã QR code quét nhanh từ đường link hoặc đoạn văn bản bất kỳ.",
        "aliases": [],
        "example": "s!qr https://discord.gg/...",
        "permissions": "Member"
    },
    {
        "name": "math",
        "category": "utility",
        "syntax": "/math <biểu_thức> hoặc s!math <biểu_thức>",
        "description": "Máy tính toán khoa học thông minh: giải biểu thức số học, căn bậc, lượng giác, lũy thừa, logarit và phần trăm.",
        "aliases": ["s!math", "s!calc", "s!tinh"],
        "example": "/math (150*12)/4 hoặc /math sqrt(144) + 15% of 200",
        "permissions": "Member (Vote Top.gg khi bật)"
    },
    {
        "name": "vote",
        "category": "utility",
        "syntax": "/vote [check|rewards|toggle]",
        "description": "Bình chọn cho Sakura Bot trên Top.gg để nhận +5,000 Coin, +500 XP và mở khóa 12h các lệnh VIP.",
        "aliases": ["s!vote"],
        "example": "/vote hoặc /vote toggle on",
        "permissions": "Member (Toggle: Owner & Admin Web)"
    },
    {
        "name": "translate",
        "category": "utility",
        "syntax": "/translate hoặc s!translate <ngôn_ngữ> <nội_dung>",
        "description": "Dịch thuật văn bản đa ngôn ngữ siêu tốc sang tiếng Việt hoặc ngôn ngữ khác.",
        "aliases": ["s!translate"],
        "example": "s!translate vi Hello world",
        "permissions": "Member"
    },
    {
        "name": "ticket setup",
        "category": "utility",
        "syntax": "/ticket setup",
        "description": "Cài đặt hệ thống Ticket tự động tạo phòng hỗ trợ riêng tư giữa Member và ban quản trị.",
        "aliases": [],
        "example": "/ticket setup",
        "permissions": "Quản trị viên"
    },
    {
        "name": "confession setup",
        "category": "utility",
        "syntax": "/confession setup",
        "description": "Cấu hình kênh Confession ẩn danh cho phép Member gửi tâm sự không lộ danh tính.",
        "aliases": [],
        "example": "/confession setup",
        "permissions": "Quản trị viên"
    },
    {
        "name": "embed",
        "category": "utility",
        "syntax": "s!embed",
        "description": "Trình thiết kế và gửi tin nhắn Embed thông báo tuyệt đẹp vào kênh chỉ định.",
        "aliases": [],
        "example": "s!embed",
        "permissions": "Quản trị viên"
    },
    {
        "name": "tts",
        "category": "utility",
        "syntax": "s!tts <on|off|skip|volume|lang>",
        "description": "Đọc tin nhắn chat bằng giọng nói tiếng Việt tự nhiên trong phòng voice.",
        "aliases": [],
        "example": "s!tts on | s!tts lang vi",
        "permissions": "Phòng Voice"
    },

    {
        "name": "anime",
        "category": "games",
        "syntax": "s!anime <tên> hoặc /anime action:anime",
        "description": "Tra cứu thông tin, điểm đánh giá, tóm tắt nội dung các bộ phim Anime.",
        "aliases": ["/anime"],
        "example": "s!anime Naruto",
        "permissions": "Member"
    },
    {
        "name": "manga",
        "category": "games",
        "syntax": "s!manga <tên> hoặc /anime action:manga",
        "description": "Tra cứu thông tin các bộ truyện tranh Manga, số chương và tác giả.",
        "aliases": [],
        "example": "s!manga One Piece",
        "permissions": "Member"
    },
    {
        "name": "waifu / neko",
        "category": "games",
        "syntax": "s!waifu hoặc s!neko",
        "description": "Gửi ngẫu nhiên các bức ảnh anime Waifu hoặc Neko dễ thương.",
        "aliases": ["s!waifu", "s!neko"],
        "example": "s!waifu",
        "permissions": "Member"
    },
    {
        "name": "tarot",
        "category": "games",
        "syntax": "s!tarot",
        "description": "Rút một lá bài Tarot giải mã vận mệnh và thông điệp vũ trụ gửi đến bạn.",
        "aliases": [],
        "example": "s!tarot",
        "permissions": "Member"
    },
    {
        "name": "xemboi",
        "category": "games",
        "syntax": "s!xemboi <câu_hỏi>",
        "description": "Xin quẻ quẻ bói vận mệnh cùng Thầy Bói Sakura AI.",
        "aliases": [],
        "example": "s!xemboi Hôm nay tình duyên thế nào?",
        "permissions": "Member"
    },
    {
        "name": "wordchain",
        "category": "games",
        "syntax": "s!wordchain hoặc /wordchain",
        "description": "Bắt đầu minigame nối từ tiếng Việt cực vui nhộn cùng các Member.",
        "aliases": ["/wordchain"],
        "example": "s!wordchain",
        "permissions": "Member"
    },
    {
        "name": "altp",
        "category": "games",
        "syntax": "s!altp",
        "description": "Minigame trí tuệ mô phỏng trò chơi truyền hình Ai Là Triệu Phú.",
        "aliases": [],
        "example": "s!altp",
        "permissions": "Member"
    },
    {
        "name": "enka hoyoverse",
        "category": "games",
        "syntax": "s!enka gi <UID> / s!enka hsr <UID> / s!enka zzz <UID>",
        "description": "Xuất thẻ bài đồ họa chỉ số nhân vật Genshin Impact, Honkai Star Rail, ZZZ.",
        "aliases": ["s!enka"],
        "example": "s!enka gi 812345678",
        "permissions": "Member"
    },
    {
        "name": "hoyolab checkin",
        "category": "games",
        "syntax": "/hoyolab manage",
        "description": "Tự động điểm danh nhận quà hàng ngày HoYoLAB (Genshin, Star Rail, Honkai 3rd, ZZZ).",
        "aliases": [],
        "example": "/hoyolab manage",
        "permissions": "Member"
    },

    {
        "name": "minigame hub",
        "category": "games",
        "syntax": "/minigame hoặc /casino",
        "description": "Trung tâm Mini-Games Sòng Bạc Sakura với đầy đủ trò chơi hoạt ảnh chuyển động (tiêu Coins hoặc Xu).",
        "aliases": ["/casino", "s!minigame"],
        "example": "/minigame",
        "permissions": "Member"
    },
    {
        "name": "doden",
        "category": "games",
        "syntax": "/doden [tiền] [red/black/zero] [coins/xu]",
        "description": "Vòng quay Roulette Đỏ Đen hoạt ảnh xoay bánh xe chân thực (x2 đến x14).",
        "aliases": ["/redblack", "s!doden"],
        "example": "/doden 50000 red coins",
        "permissions": "Member"
    },
    {
        "name": "chanle",
        "category": "games",
        "syntax": "/chanle [tiền] [chan/le] [coins/xu]",
        "description": "Xóc đĩa Chẵn Lẻ xúc xắc hoạt ảnh úp bát rung lắc dữ dội (x1.95).",
        "aliases": ["/xocdia", "s!chanle"],
        "example": "/chanle 20000 chan coins",
        "permissions": "Member"
    },
    {
        "name": "taixiu",
        "category": "games",
        "syntax": "/taixiu [tiền] [tai/xiu/bao] [coins/xu]",
        "description": "Tài Xỉu Sic Bo 3 viên xúc xắc lăn chuyển động (Tài/Xỉu x2, Bão x30).",
        "aliases": ["/tx", "s!taixiu"],
        "example": "/taixiu 10000 tai xu",
        "permissions": "Member"
    },
    {
        "name": "slots",
        "category": "games",
        "syntax": "/slots [tiền] [coins/xu]",
        "description": "Máy xèng Slots 777 nổ hũ siêu cấp với guồng quay chuyển động (x2 đến x20).",
        "aliases": ["/jackpot", "s!slots"],
        "example": "/slots 50000 coins",
        "permissions": "Member"
    },
    {
        "name": "baucua",
        "category": "games",
        "syntax": "/baucua [tiền] [nai/bau/ga/ca/cua/tom] [coins/xu]",
        "description": "Lắc Bầu Cua Tôm Cá dân gian hoạt ảnh mở đĩa lách cách (x2 đến x4).",
        "aliases": ["s!baucua"],
        "example": "/baucua 10000 cua coins",
        "permissions": "Member"
    },

    {
        "name": "anti setup",
        "category": "anti",
        "syntax": "/anti setup hoặc /anti",
        "description": "Lệnh Slash duy nhất thiết lập toàn diện hệ thống bảo mật & Anti Sakura với Dashboard trực quan.",
        "aliases": ["/anti_setup", "s!anti setup"],
        "example": "/anti setup",
        "permissions": "Quản trị viên"
    },
    {
        "name": "antinuke",
        "category": "anti",
        "syntax": "s!antinuke",
        "description": "Bảo vệ máy chủ chống phá hoại: Chặn xóa kênh, xóa role và kick Member hàng loạt.",
        "aliases": [],
        "example": "s!antinuke",
        "permissions": "Chủ Server"
    },
    {
        "name": "antiraid",
        "category": "anti",
        "syntax": "s!antiraid",
        "description": "Chế độ chống đột nhập tài khoản ảo và bot spam ồ ạt vào máy chủ.",
        "aliases": [],
        "example": "s!antiraid",
        "permissions": "Chủ Server"
    },
    {
        "name": "antispam",
        "category": "anti",
        "syntax": "s!antispam",
        "description": "Tự động phát hiện và chặn các hành vi gửi tin nhắn spam liên tục hoặc gửi ký tự lạ.",
        "aliases": [],
        "example": "s!antispam",
        "permissions": "Quản trị viên"
    },
    {
        "name": "antilink",
        "category": "anti",
        "syntax": "s!antilink",
        "description": "Tự động xóa các đường link trái phép hoặc link độc hại khi Member gửi vào kênh.",
        "aliases": [],
        "example": "s!antilink",
        "permissions": "Quản trị viên"
    },
    {
        "name": "antiinvite",
        "category": "anti",
        "syntax": "s!antiinvite",
        "description": "Ngăn chặn việc gửi link mời máy chủ Discord khác để quảng cáo trái phép.",
        "aliases": [],
        "example": "s!antiinvite",
        "permissions": "Quản trị viên"
    },
    {
        "name": "backup",
        "category": "anti",
        "syntax": "s!backup <create|load|list>",
        "description": "Sao lưu toàn bộ cấu hình, kênh, role của máy chủ và phục hồi nhanh khi cần.",
        "aliases": [],
        "example": "s!backup create",
        "permissions": "Chủ Server"
    },

    {
        "name": "owner panel",
        "category": "owner",
        "syntax": "/owner panel hoặc s!owner",
        "description": "Bảng điều khiển quản trị tối cao dành riêng cho Chủ Bot Sakura.",
        "aliases": ["s!owner"],
        "example": "/owner panel",
        "permissions": "👑 Owner (@linhxinh_dev)"
    },
    {
        "name": "owner sync",
        "category": "owner",
        "syntax": "/owner sync",
        "description": "Đồng bộ toàn bộ danh sách Slash Commands lên Discord Gateway ngay lập tức.",
        "aliases": [],
        "example": "/owner sync",
        "permissions": "👑 Owner (@linhxinh_dev)"
    },
    {
        "name": "owner reload",
        "category": "owner",
        "syntax": "/owner reload <tên_cog>",
        "description": "Nạp lại nóng module tính năng (Hot-reload) mà không làm gián đoạn bot.",
        "aliases": [],
        "example": "/owner reload cog:Command.music",
        "permissions": "👑 Owner (@linhxinh_dev)"
    },
    {
        "name": "owner servers",
        "category": "owner",
        "syntax": "/owner servers",
        "description": "Xem toàn bộ danh sách các server Discord mà Sakura Bot đang phục vụ.",
        "aliases": [],
        "example": "/owner servers",
        "permissions": "👑 Owner (@linhxinh_dev)"
    },
    {
        "name": "owner restart",
        "category": "owner",
        "syntax": "/owner restart",
        "description": "Khởi động lại toàn bộ tiến trình Sakura Bot từ xa một cách an toàn.",
        "aliases": ["s!restart"],
        "example": "/owner restart",
        "permissions": "👑 Owner (@linhxinh_dev)"
    },
    {
        "name": "menubot panel",
        "category": "owner",
        "syntax": "/menubot panel",
        "description": "Bảng điều khiển giám sát tài nguyên và điều khiển các tiến trình con .py.",
        "aliases": ["s!menubot"],
        "example": "/menubot panel",
        "permissions": "👑 Owner (@linhxinh_dev)"
    },
    {
        "name": "blacklist",
        "category": "owner",
        "syntax": "s!blacklist <add|remove|list> <user_id>",
        "description": "Quản lý danh sách cấm sử dụng Bot trên toàn cầu đối với người dùng phá hoại.",
        "aliases": [],
        "example": "s!blacklist add 123456789",
        "permissions": "👑 Owner (@linhxinh_dev)"
    }
]

def get_all_bot_commands(bot_instance=None) -> List[Dict[str, Any]]:
    """Lấy danh sách lệnh đầy đủ, đã lọc bỏ hoàn toàn các lệnh Minecraft"""
    commands_list = [dict(c) for c in BOT_COMMANDS_CATALOG]
    
    if bot_instance:
        existing_names = {c["name"].lower() for c in commands_list}
        try:
            for cmd in bot_instance.commands:
                if cmd.hidden:
                    continue
                cmd_name = cmd.name.lower()
                cog_name = (cmd.cog_name or "").lower()
                if "minecraft" in cog_name or cmd_name.startswith("mc") or cmd_name in ["link", "whitelist"]:
                    continue
                if cmd_name not in existing_names:
                    cat = "utility"
                    if "music" in cog_name: cat = "music"
                    elif "mod" in cog_name or "admin" in cog_name: cat = "moderation"
                    elif "fish" in cog_name: cat = "fishing"
                    elif "level" in cog_name or "bank" in cog_name: cat = "economy"
                    elif "fun" in cog_name or "anime" in cog_name: cat = "games"
                    elif "anti" in cog_name: cat = "anti"
                    elif "owner" in cog_name: cat = "owner"
                    
                    aliases_list = [f"s!{a}" for a in cmd.aliases] if cmd.aliases else []
                    commands_list.append({
                        "name": cmd.name,
                        "category": cat,
                        "syntax": f"s!{cmd.name} {cmd.signature}".strip(),
                        "description": cmd.short_doc or cmd.description or f"Lệnh s!{cmd.name}",
                        "aliases": aliases_list,
                        "example": f"s!{cmd.name}",
                        "permissions": "Member"
                    })
                    existing_names.add(cmd_name)
        except Exception:
            pass

    filtered = []
    for c in commands_list:
        n = c.get("name", "").lower()
        d = c.get("description", "").lower()
        s = c.get("syntax", "").lower()
        if "minecraft" in n or "minecraft" in d or "minecraft" in s or n.startswith("mc_") or n == "mc":
            continue
        filtered.append(c)
        
    return filtered
