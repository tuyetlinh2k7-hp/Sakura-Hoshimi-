import discord

# =============================================================================
# CẦN CÂU & MỒI CÂU CƠ BẢN
# =============================================================================
fishing_rods = {
    "🎣 Cần Câu Gỗ": {
        "level": 1,
        "luck": 1,
        "durability": 50,
        "description": "Cần câu cơ bản cho người mới.\nTỉ lệ cá hiếm thấp."
    },
    "🎣 Cần Câu Sắt": {
        "level": 5,
        "luck": 20,
        "durability": 1200,
        "description": "Cần câu chắc chắn hơn.\nTăng tỉ lệ cá hiếm."
    },
    "🎣 Cần Câu Vàng": {
        "level": 10,
        "luck": 30,
        "durability": 2500,
        "description": "Cần câu cao cấp.\nDễ câu được cá giá trị."
    },
    "🎣 Cần Câu Kim Cương": {
        "level": 20,
        "luck": 50,
        "durability": 5000,
        "description": "Cần câu huyền thoại.\nTỉ lệ cá cực hiếm rất cao."
    }
}

fish_baits = {
    "🪱 Mồi Thường": {
        "price": 100,
        "luck": 1,
        "description": "Mồi cơ bản.\nDễ mua nhưng hiệu quả thấp."
    },
    "🪱 Mồi Hiếm": {
        "price": 5000,
        "luck": 4,
        "description": "Mồi chất lượng cao.\nTăng cơ hội cá hiếm."
    },
    "🪱 Mồi Sử Thi": {
        "price": 15000,
        "luck": 8,
        "description": "Mồi quý hiếm.\nCá lớn rất thích."
    },
    "🪱 Mồi Huyền Thoại": {
        "price": 50000,
        "luck": 15,
        "description": "Mồi cực hiếm.\nCó thể dụ cá huyền thoại."
    }
}

RARITY_ICONS = {
    "common": "⚪",
    "rare": "🔵",
    "epic": "🟣",
    "legendary": "🟡",
    "admin": "🔴"
}

RARITY_COLORS = {
    "common": discord.Color.light_grey(),
    "rare": discord.Color.blue(),
    "epic": discord.Color.purple(),
    "legendary": discord.Color.gold(),
    "admin": discord.Color.red()
}

# =============================================================================
# CÁ SỰ KIỆN THEO MÙA MỞ RỘNG (EVENT FISH - ĐÃ TĂNG GIÁ GẤP 9 - 11 LẦN)
# =============================================================================
event_fish = [
    {"name": "🎄 Cá Noel Băng Giá", "price": 500000, "chance": 0.5, "rarity": "legendary", "description": "Cá chỉ xuất hiện mùa Giáng Sinh tuyết trắng phủ ngọn sóng."},
    {"name": "🎃 Cá Bí Ngô Ám Ảnh", "price": 420000, "chance": 0.7, "rarity": "epic", "description": "Cá Halloween ma mị với nụ cười bí ngô phát sáng bí ẩn."},
    {"name": "❤️ Cá Valentine Chung Thủy", "price": 600000, "chance": 0.3, "rarity": "legendary", "description": "Mang theo tình yêu nồng cháy của biển cả lứa đôi."},
    {"name": "🐰 Cá Phục Sinh Đa Sắc", "price": 380000, "chance": 1.0, "rarity": "epic", "description": "Cá sự kiện Easter mang theo những quả trứng may mắn diệu kỳ."},
    {"name": "🧧 Cá Thần Tài Kim Bửu", "price": 950000, "chance": 0.2, "rarity": "legendary", "description": "Cá xuất hiện dịp Tết Nguyên Đán, mang lại vạn sự hanh thông phú quý."},
    {"name": "🥮 Cá Trăng Rằm Thu Nguyệt", "price": 450000, "chance": 0.6, "rarity": "epic", "description": "Cá Trung Thu tỏa sáng lung linh như vầng trăng rằm tháng Tám."},
    {"name": "🏖️ Cá Nhiệt Đới Mùa Hè", "price": 300000, "chance": 1.2, "rarity": "rare", "description": "Sắc màu rực rỡ mang hơi thở của những bãi san hô đầy nắng."},
    {"name": "👻 Cá U Hồn Hallow", "price": 550000, "chance": 0.4, "rarity": "epic", "description": "Bơi lượn trong làn sương đêm lạnh buốt của lễ hội hóa trang."},
    {"name": "🎆 Cá Pháo Hoa Giao Thừa", "price": 750000, "chance": 0.25, "rarity": "legendary", "description": "Thân mình bắn ra những tia sáng rực rỡ chào đón năm mới."},
    {"name": "🏮 Cá Lồng Đèn Nguyên Tiêu", "price": 440000, "chance": 0.65, "rarity": "epic", "description": "Tỏa sáng ấm áp giữa đêm trăng đầu tiên của năm mới."},
    {"name": "🎋 Cá Ngưu Lang Chức Nữ (Thất Tịch)", "price": 680000, "chance": 0.28, "rarity": "legendary", "description": "Xuất hiện bên cầu Ô Thước vào ngày 7 tháng 7 âm lịch hằng năm."},
    {"name": "🍁 Cá Lá Phong Mùa Thu", "price": 350000, "chance": 0.8, "rarity": "rare", "description": "Mang sắc đỏ cam rực rỡ báo hiệu mùa thu lãng mạn trôi về bờ."},
    {"name": "🌸 Cá Hoa Anh Đào (Sakura Hanami)", "price": 580000, "chance": 0.35, "rarity": "epic", "description": "Loài cá linh vật của mùa hoa nở, thân mang hoa văn cánh đào thanh khiết."},
    {"name": "🐲 Cá Đua Thuyền Rồng (Đoan Ngọ)", "price": 820000, "chance": 0.22, "rarity": "legendary", "description": "Cá thần bảo hộ các tay đua thuyền rồng giữa dòng nước xoáy cuồn cuộn."},
    {"name": "🧟 Cá Xác Sống Zombie Fish", "price": 460000, "chance": 0.55, "rarity": "epic", "description": "Thực thể cá hồi sinh từ vùng nước ngập bùn độc hại đêm Halloween."},
    {"name": "💐 Cá Tri Ân Tình Mẹ", "price": 520000, "chance": 0.45, "rarity": "epic", "description": "Xuất hiện trong Ngày Của Mẹ mang theo lời chúc bình an và ấm áp."},
    {"name": "🍺 Cá Lễ Hội Bia Biển Sâu", "price": 330000, "chance": 0.9, "rarity": "rare", "description": "Cá chỉ xuất hiện trong mùa lễ hội Oktoberfest tưng bừng sóng vỗ."},
    {"name": "🃏 Cá Trêu Đùa (Cá Tháng Tư)", "price": 404404, "chance": 0.6, "rarity": "epic", "description": "Bơi giật lùi và đánh lừa thị giác của mọi cần thủ bất cẩn."}
]

# =============================================================================
# HỆ THỐNG ĐỘT BIẾN GEN (MUTATIONS)
# =============================================================================
mutations = [
    {"name": "🔥 Lửa Rực Cháy", "price_multi": 2.0},
    {"name": "❄️ Băng Giá Vĩnh Cửu", "price_multi": 2.0},
    {"name": "☢️ Đột Biến Phóng Xạ", "price_multi": 3.0},
    {"name": "⚡ Lôi Điện Sấm Sét", "price_multi": 3.5},
    {"name": "✨ Huỳnh Quang Phát Sáng", "price_multi": 4.0},
    {"name": "🌪️ Phong Ba Bão Táp", "price_multi": 2.6},
    {"name": "🌿 Rêu Phong Thảo Mộc", "price_multi": 2.2},
    {"name": "☣️ Axit Ăn Mòn", "price_multi": 3.2},
    {"name": "🌈 Cầu Vồng Lục Sắc", "price_multi": 4.5},
    {"name": "💎 Kim Cương Tinh Thể", "price_multi": 5.0},
    {"name": "⚙️ Cơ Khí Cyberpunk", "price_multi": 5.5},
    {"name": "🌑 Hắc Ám Vực Sâu", "price_multi": 6.0},
    {"name": "👻 Linh Hồn U Minh", "price_multi": 6.8},
    {"name": "🧬 Biến Dị Hỗn Loạn", "price_multi": 7.2},
    {"name": "🩸 Huyết Nguyệt Ma Đỏ", "price_multi": 7.8},
    {"name": "🪙 Hoàng Kim Midas", "price_multi": 8.5},
    {"name": "✨ Thánh Quang Thiên Giới", "price_multi": 9.0},
    {"name": "🔮 Huyết Mạch Thần Thú", "price_multi": 9.5},
    {"name": "🌌 Hư Không Void-Touched", "price_multi": 10.0},
    {"name": "☄️ Plasma Tinh Vân", "price_multi": 11.5},
    {"name": "⚡ Siêu Lôi Thần Tích", "price_multi": 12.5},
    {"name": "⏳ Nghịch Đảo Thời Gian", "price_multi": 13.0},
    {"name": "☣️ Bụi Phấn Độc Ma Quái", "price_multi": 13.5},
    {"name": "☄️ Tinh Thể Thiên Thạch", "price_multi": 14.0},
    {"name": "🪐 Vũ Trụ Đa Chiều", "price_multi": 15.0},
    {"name": "✨ Cực Quang Huyền Ảo", "price_multi": 15.5},
    {"name": "🌸 Hoa Anh Đào Sakura Dạ Quang", "price_multi": 16.0},
    {"name": "💎 Thạch Anh Tím Huyền Bí", "price_multi": 17.5},
    {"name": "🖤 Hắc Động Singularity", "price_multi": 18.0},
    {"name": "🩸 Ma Cà Rồng Biển Đỏ", "price_multi": 19.0},
    {"name": "🐉 Long Hồn Thượng Cổ", "price_multi": 20.0},
    {"name": "👾 Lỗi Thực Tại (Glitch)", "price_multi": 22.0},
    {"name": "🧿 Mắt Quỷ Vực Thẳm", "price_multi": 25.0},
    {"name": "🌠 Bụi Sao Băng Cổ Đại", "price_multi": 26.5},
    {"name": "💠 Lõi Lượng Tử Hỗn Loạn", "price_multi": 28.0},
    {"name": "👑 Thần Cách Nguyên Thủy", "price_multi": 30.0},
    {"name": "☀️ Nhật Hoa Vĩnh Cửu", "price_multi": 32.0},
    {"name": "🌌 Khởi Nguyên Sáng Thế", "price_multi": 40.0},
    {"name": "🪐 Ma Trận Thực Tại", "price_multi": 45.0},
    {"name": "👑 Thần Vương Tối Thượng", "price_multi": 50.0}
]

# =============================================================================
# BÁCH KHOA TOÀN THƯ SINH VẬT BIỂN (ĐÃ TĂNG GIÁ GẤP 9 - 11 LẦN)
# =============================================================================
fish_list = [
    # -------------------------------------------------------------------------
    # ⚪ COMMON (THƯỜNG - GIÁ GỐC 8-30 COIN ➜ NÂNG LÊN 90 - 320 COIN)
    # -------------------------------------------------------------------------
    {"name": "🐟 Cá Chép", "price": 100, "chance": 100, "rarity": "common", "description": "Loài cá nước ngọt phổ biến quen thuộc."},
    {"name": "🐠 Cá Hề", "price": 160, "chance": 95, "rarity": "common", "description": "Cá nhỏ thích ẩn náu trong các bụi hải quỳ rạn san hô."},
    {"name": "🐟 Cá Rô Đồng", "price": 120, "chance": 95, "rarity": "common", "description": "Cá đồng khỏe khoắn, thích nghi tốt."},
    {"name": "🦐 Tôm Sú", "price": 140, "chance": 90, "rarity": "common", "description": "Một chú tôm sú tươi ngon búng tanh tách."},
    {"name": "🦀 Cua Biển", "price": 200, "chance": 85, "rarity": "common", "description": "Cua biển đôi càng chắc khỏe đầy gạch."},
    {"name": "🐟 Cá Bống Cát", "price": 120, "chance": 105, "rarity": "common", "description": "Loài cá nhỏ vùi mình dưới cát phù sa ven sông."},
    {"name": "🐟 Cá Lóc Non", "price": 150, "chance": 90, "rarity": "common", "description": "Một chú cá lóc háu ăn còn nhỏ."},
    {"name": "🐟 Cá Trích Biển", "price": 100, "chance": 100, "rarity": "common", "description": "Cá biển nhỏ bơi lội theo từng đàn lớn bạc óng."},
    {"name": "🐟 Cá Mòi", "price": 95, "chance": 105, "rarity": "common", "description": "Cá mòi phổ biến thường dùng làm món cá hộp."},
    {"name": "🐟 Cá Kèo", "price": 140, "chance": 85, "rarity": "common", "description": "Đặc sản vùng đất ngập mặn phù sa bùn lầy."},
    {"name": "🐠 Cá Bảy Màu", "price": 85, "chance": 110, "rarity": "common", "description": "Loài cá cảnh nhỏ với đuôi xòe rực rỡ."},
    {"name": "🐠 Cá Neon Huỳnh Quang", "price": 95, "chance": 105, "rarity": "common", "description": "Cá cảnh mini phát sáng dải xanh đỏ dọc thân."},
    {"name": "🐟 Cá Hồng Két", "price": 180, "chance": 75, "rarity": "common", "description": "Loài cá cảnh tròn trịa nổi bật với sắc đỏ cam."},
    {"name": "🐟 Cá Tai Tượng", "price": 220, "chance": 65, "rarity": "common", "description": "Loài cá nước ngọt bản thịt to dày dặn."},
    {"name": "🐟 Cá Đuối Mini", "price": 250, "chance": 50, "rarity": "common", "description": "Cá đuối non bơi lượn như cánh diều dưới đáy cát."},
    {"name": "🐟 Cá Ngừ Nhỏ", "price": 240, "chance": 45, "rarity": "common", "description": "Cá ngừ đại dương đang ở giai đoạn phát triển."},
    {"name": "🐟 Cá Chai", "price": 110, "chance": 85, "rarity": "common", "description": "Loài cá đáy biển có phần đầu dẹt như chai thủy tinh."},
    {"name": "🐟 Cá Đối", "price": 130, "chance": 82, "rarity": "common", "description": "Cá nhảy rất cao ven các cửa sông đầm lầy."},
    {"name": "🐟 Cá Chuồn Lướt Gió", "price": 200, "chance": 60, "rarity": "common", "description": "Đôi vây ngực xòe rộng bay lướt trên mặt nước biển."},
    {"name": "🦈 Cá Mập Tre", "price": 300, "chance": 35, "rarity": "common", "description": "Cá mập đáy nhỏ bé, hiền lành dưới rạn san hô."},
    {"name": "🐟 Cá Tra Sông", "price": 150, "chance": 80, "rarity": "common", "description": "Cá nước ngọt thân tròn béo mẫm."},
    {"name": "🐟 Cá Basa", "price": 160, "chance": 78, "rarity": "common", "description": "Cá da trơn với thớ thịt mềm béo ngậy."},
    {"name": "🐟 Cá Trắm Cỏ", "price": 180, "chance": 70, "rarity": "common", "description": "Loài cá nước ngọt ăn cỏ, thân thon dài vảy bạc."},
    {"name": "🐟 Cá Nục Gai", "price": 110, "chance": 95, "rarity": "common", "description": "Cá nục tươi ngon đánh bắt từng mẻ lớn ngoài khơi."},
    {"name": "🐟 Cá Chỉ Vàng", "price": 100, "chance": 100, "rarity": "common", "description": "Vệt sọc vàng óng ánh chạy dọc từ mang tới đuôi."},
    {"name": "🦪 Sò Điệp Quạt", "price": 170, "chance": 80, "rarity": "common", "description": "Vỏ hình quạt xòe, cồi sò trắng giòn ngọt."},
    {"name": "🦪 Hàu Sữa Biển", "price": 220, "chance": 70, "rarity": "common", "description": "Hàu bám trên vách đá ngầm giàu dưỡng chất."},
    {"name": "🐚 Ốc Hương Vàng", "price": 190, "chance": 75, "rarity": "common", "description": "Ốc biển đốm rằn khi chế biến tỏa hương thơm ngát."},
    {"name": "🦑 Mực Ống Tươi", "price": 230, "chance": 65, "rarity": "common", "description": "Thân mực trong suốt lấp lánh chấm mi sắc tố."},
    {"name": "🐟 Cá Diếc Bạc", "price": 110, "chance": 90, "rarity": "common", "description": "Cá sông nhỏ vảy trắng bóng thích rỉa mồi nhẹ."},
    {"name": "🐟 Cá Cơm Than", "price": 85, "chance": 115, "rarity": "common", "description": "Cá cơm nhỏ xíu nguyên liệu làm nước mắm hảo hạng."},
    {"name": "🐟 Cá Chim Trắng", "price": 220, "chance": 60, "rarity": "common", "description": "Thân dẹt hình thoi vảy trắng óng ánh như gương."},
    {"name": "🐟 Cá Phèn Hồng", "price": 160, "chance": 80, "rarity": "common", "description": "Sắc hồng phớt với đôi râu cằm dò mồi đáy biển."},
    {"name": "🐟 Cá Bạc Má", "price": 130, "chance": 85, "rarity": "common", "description": "Bơi theo đàn lớn với tốc độ lướt sóng cực nhanh."},
    {"name": "🐟 Cá Đục Cát", "price": 150, "chance": 78, "rarity": "common", "description": "Cá thân thon dài ẩn mình dưới cát ven bãi tắm."},
    {"name": "🐟 Cá Khoai Biển", "price": 140, "chance": 82, "rarity": "common", "description": "Thân mềm như thạch không vảy ngọt mát."},
    {"name": "🐟 Cá Chạch Đồng", "price": 160, "chance": 75, "rarity": "common", "description": "Luồn lách siêu nhanh dưới bùn lầy đồng ruộng."},
    {"name": "🐟 Cá Ngát Gai", "price": 190, "chance": 65, "rarity": "common", "description": "Cá da trơn có gai ngạnh nhọn ở vây ngực."},
    {"name": "🐟 Cá Bớp Non", "price": 280, "chance": 50, "rarity": "common", "description": "Cá săn mồi biển đang ở độ tuổi lớn nhanh."},
    {"name": "🐠 Cá Mó Cầu Vồng", "price": 200, "chance": 70, "rarity": "common", "description": "Mỏ vẹt cứng dùng để gặm san hô và tảo biển."},
    {"name": "🐠 Cá Thia San Hô", "price": 120, "chance": 90, "rarity": "common", "description": "Bơi lượn thành bầy điểm xuyết cho các rạn đá ngầm."},
    {"name": "🦪 Nghêu Bến Tre", "price": 140, "chance": 88, "rarity": "common", "description": "Hai mảnh vỏ bóng loáng vùi mình bãi cát triều."},
    {"name": "🦪 Sò Huyết Đầm Ô Loan", "price": 210, "chance": 68, "rarity": "common", "description": "Ruột đỏ như son bổ dưỡng thơm ngọt lừng danh."},
    {"name": "🦀 Cua Đồng Lột", "price": 150, "chance": 85, "rarity": "common", "description": "Cua đồng giòn béo đào hang dọc bờ kênh ruộng."},
    {"name": "🦐 Tép Bạc Sông", "price": 95, "chance": 105, "rarity": "common", "description": "Những con tép nhỏ vỏ trong veo nhảy tanh tách."},
    {"name": "🐟 Cá Đù Một Nắng", "price": 170, "chance": 76, "rarity": "common", "description": "Loài cá biển quen thuộc của ngư dân duyên hải."},
    {"name": "🐟 Cá Trích Lầm", "price": 130, "chance": 86, "rarity": "common", "description": "Cá biển nhỏ giàu Omega-3 bơi dọc dòng hải lưu ấm."},
    {"name": "🐟 Cá Bác Sĩ (Cleaner Wrasse)", "price": 180, "chance": 72, "rarity": "common", "description": "Chuyên dọn dẹp ký sinh trùng cho các loài cá lớn."},
    {"name": "🐟 Cá Bống Mú Non", "price": 260, "chance": 52, "rarity": "common", "description": "Cá mú con ẩn nấp trong các hang đá rạn cạn."},
    {"name": "🦀 Cáy Biển Đào Hang", "price": 110, "chance": 95, "rarity": "common", "description": "Chạy rất nhanh trên bãi bùn rừng ngập mặn."},
    {"name": "🐟 Cá Lìm Kìm Nước Lợ", "price": 130, "chance": 84, "rarity": "common", "description": "Mõm dài như cây kìm nhỏ nổi trên mặt nước."},
    {"name": "🐟 Cá Sặc Rằn Đồng", "price": 150, "chance": 79, "rarity": "common", "description": "Sọc rằn ri đặc trưng thịt thơm dùng làm khô."},
    {"name": "🐟 Cá Trôi Đen", "price": 170, "chance": 73, "rarity": "common", "description": "Cá nước ngọt khỏe ăn bùn và mùn bã hữu cơ."},
    {"name": "🐟 Cá Thiều Ven Biển", "price": 200, "chance": 67, "rarity": "common", "description": "Cá da trơn thịt ngọt thơm bơi ven các vũng vịnh."},
    {"name": "🐟 Cá Hố Trắng Nhỏ", "price": 210, "chance": 64, "rarity": "common", "description": "Thân mỏng dẹt như dải ruy băng bạc óng ánh."},
    {"name": "🐟 Cá Nâu Hoa San Hô", "price": 220, "chance": 62, "rarity": "common", "description": "Đốm hoa tròn trên thân da nâu thích rỉa rong biển."},
    {"name": "🐟 Cá Sơn Thóc", "price": 120, "chance": 89, "rarity": "common", "description": "Vảy dày như hạt thóc bơi quanh chân cầu cảng."},
    {"name": "🐟 Cá Mắt Tre Biển", "price": 140, "chance": 83, "rarity": "common", "description": "Đôi mắt lồi to tinh tường săn mồi trong rạn đá."},
    {"name": "🦐 Tôm Tít Cỡ Vừa", "price": 250, "chance": 55, "rarity": "common", "description": "Càng búa gõ vỏ ốc lách cách dưới đáy biển."},
    {"name": "🦀 Ghẹ Xanh Cửa Biển", "price": 270, "chance": 51, "rarity": "common", "description": "Ghẹ xanh tươi rói hai mái chèo bơi thoăn thoắt."},

    # -------------------------------------------------------------------------
    # 🔵 RARE (HIẾM - GIÁ GỐC 150-950 COIN ➜ NÂNG LÊN 1,500 - 10,000 COIN)
    # -------------------------------------------------------------------------
    {"name": "🐡 Cá Nóc Gai Độc", "price": 1500, "chance": 25, "rarity": "rare", "description": "Phồng tròn gai góc chứa chất độc nhưng thịt siêu đắt."},
    {"name": "🦑 Mực Khổng Lồ", "price": 2200, "chance": 20, "rarity": "rare", "description": "Thân mềm với những giác bám và xúc tu khỏe khoắn."},
    {"name": "🐙 Bạch Tuộc Đốm Xanh", "price": 2800, "chance": 18, "rarity": "rare", "description": "Bạch tuộc độc có vòng đốm xanh cảnh báo nguy hiểm."},
    {"name": "🐢 Rùa Biển Đồi Mồi", "price": 3200, "chance": 15, "rarity": "rare", "description": "Sinh vật sống thọ với hoa văn mai rùa tinh xảo tuyệt mỹ."},
    {"name": "🪼 Sứa Phát Sáng Biển Sâu", "price": 3800, "chance": 12, "rarity": "rare", "description": "Tỏa ánh huỳnh quang rực rỡ giữa làn nước đêm đen."},
    {"name": "🦈 Cá Mập Rạn San Hô", "price": 4200, "chance": 14, "rarity": "rare", "description": "Kẻ săn mồi nhanh nhẹn tuần tra rạn đá ngầm."},
    {"name": "🐬 Cá Heo Mũi Chai", "price": 4800, "chance": 12, "rarity": "rare", "description": "Người bạn thông minh thân thiện luôn cứu hộ ngư dân."},
    {"name": "🦄 Cá Ngựa Biển Vàng", "price": 3500, "chance": 16, "rarity": "rare", "description": "Dáng đứng kỳ lạ bám đuôi vào rong rêu rực rỡ sắc vàng."},
    {"name": "🐟 Cá Hổ Goliath Nước Ngọt", "price": 5500, "chance": 10, "rarity": "rare", "description": "Quái ngư nước ngọt với hàm răng sắc như dao cạo."},
    {"name": "🐊 Cá Sấu Hỏa Tiễn", "price": 5800, "chance": 9, "rarity": "rare", "description": "Cá cổ đại có mõm dài và vảy cứng như giáp sắt."},
    {"name": "🐉 Cá Rồng Đỏ Huyết Long", "price": 8500, "chance": 6, "rarity": "rare", "description": "Cá cảnh phong thủy vương giả tượng trưng quyền lực."},
    {"name": "🏮 Cá Đèn Lồng Anglerfish", "price": 4500, "chance": 14, "rarity": "rare", "description": "Chiếc cần câu sinh học phát sáng dụ con mồi sập bẫy."},
    {"name": "🪚 Cá Cưa Mõm Dài", "price": 6200, "chance": 8, "rarity": "rare", "description": "Mõm dài gắn răng cưa dùng để chém xẻ bầy cá mồi."},
    {"name": "⚔️ Cá Kiếm Hoàng Gia", "price": 7500, "chance": 7, "rarity": "rare", "description": "Đấu sĩ đại dương tốc độ cao với thanh kiếm nhọn hoắt."},
    {"name": "🔨 Cá Mập Búa Đầu Dẹt", "price": 8800, "chance": 5, "rarity": "rare", "description": "Chiếc đầu búa độc đáo cảm nhận điện trường con mồi."},
    {"name": "🐟 Cá Ngừ Vây Vàng", "price": 6000, "chance": 9, "rarity": "rare", "description": "Cá ngừ đại dương cao cấp cho các nhà hàng 5 sao."},
    {"name": "⛵ Cá Buồm Cực Tốc", "price": 7200, "chance": 8, "rarity": "rare", "description": "Loài cá bơi nhanh nhất hành tinh xé toạc ngọn sóng."},
    {"name": "🌕 Cá Mặt Trăng Mola Mola", "price": 8200, "chance": 6, "rarity": "rare", "description": "Thân hình tròn khổng lồ thích nổi lên sưởi nắng."},
    {"name": "⚡ Cá Chình Điện Amazon", "price": 5000, "chance": 11, "rarity": "rare", "description": "Phóng luồng điện 600V hạ gục con mồi trong chớp mắt."},
    {"name": "🐟 Cá Hồi Vân Bắc Cực", "price": 4800, "chance": 12, "rarity": "rare", "description": "Vượt thác ghềnh ngược dòng để duy trì nòi giống."},
    {"name": "🐟 Cá Tầm Trắng Beluga", "price": 9500, "chance": 5, "rarity": "rare", "description": "Nguồn gốc của món trứng cá muối Caviar hoàng gia."},
    {"name": "🦞 Tôm Hùm Alaska", "price": 7800, "chance": 7, "rarity": "rare", "description": "Đôi càng vĩ đại của vùng biển băng lạnh giá phương Bắc."},
    {"name": "🦀 Cua Tuyết Đại Tây Dương", "price": 6900, "chance": 8, "rarity": "rare", "description": "Chân dài miên man đầy ắp thịt thơm ngọt hảo hạng."},
    {"name": "🐟 Cá Chép Koi Ngũ Sắc", "price": 6500, "chance": 9, "rarity": "rare", "description": "Tác phẩm nghệ thuật sống bơi lội trong hồ thanh tịnh."},
    {"name": "🐟 Cá Hô Sông Mê Kông", "price": 9000, "chance": 5, "rarity": "rare", "description": "Vua cá nước ngọt nặng hàng trăm ký của dòng Mê Kông."},
    {"name": "🐟 Cá Chẽm Đại Dương (Barramundi)", "price": 5200, "chance": 11, "rarity": "rare", "description": "Cá săn mồi dũng mãnh giữa vùng nước lợ và biển."},
    {"name": "🐟 Cá Mú Đỏ San Hô", "price": 7600, "chance": 7, "rarity": "rare", "description": "Sắc đỏ rực rỡ với thịt trắng phau đắt giá hàng đầu."},
    {"name": "🐟 Cá Bơn Lưỡi Trâu", "price": 4900, "chance": 12, "rarity": "rare", "description": "Hai mắt nằm cùng một bên ngụy trang tài tình dưới đáy."},
    {"name": "🐟 Cá Chó Bắc Mỹ (Northern Pike)", "price": 5800, "chance": 10, "rarity": "rare", "description": "Hàm răng sắc lẹm phục kích con mồi từ đám lau sậy."},
    {"name": "🐟 Cá Chép Giòn Hoàng Gia", "price": 6200, "chance": 9, "rarity": "rare", "description": "Thịt dai giòn sần sật được nuôi dưỡng bằng đậu tằm."},
    {"name": "🐟 Cá Chình Bông Biển Sâu", "price": 7100, "chance": 8, "rarity": "rare", "description": "Thân hình uốn lượn hoa văn da báo săn mồi trong hốc đá."},
    {"name": "🦑 Mực Nang Khổng Lồ", "price": 6800, "chance": 8, "rarity": "rare", "description": "Chiếc mai vôi lớn có khả năng đổi màu trong tíc tắc."},
    {"name": "🐙 Bạch Tuộc Thái Bình Dương", "price": 8200, "chance": 6, "rarity": "rare", "description": "Sải tay dài hàng mét có thể mở được nắp lọ thủy tinh."},
    {"name": "🐡 Cá Nóc Nhím Biển", "price": 4600, "chance": 13, "rarity": "rare", "description": "Gai nhọn tua tủa như nhím khi gặp nguy hiểm."},
    {"name": "🐟 Cá Bò Da Giáp", "price": 4300, "chance": 14, "rarity": "rare", "description": "Lớp da nhám dày như áo giáp bảo vệ trước kẻ thù."},
    {"name": "🐟 Cá Nhồng Săn Mồi (Barracuda)", "price": 7900, "chance": 7, "rarity": "rare", "description": "Tên lửa sống của biển cả lao tới xé toạc mục tiêu."},
    {"name": "🐟 Cá Báo Hoa Mai San Hô", "price": 8400, "chance": 6, "rarity": "rare", "description": "Đốm hoa mai phủ kín mình ẩn hiện quanh rạn đá."},
    {"name": "🐟 Cá Bướm Nữ Hoàng", "price": 5600, "chance": 10, "rarity": "rare", "description": "Màu vàng hoàng yến cùng vương miện xanh lam quyền quý."},
    {"name": "🐟 Cá Thiên Thần Xanh (Blue Angelfish)", "price": 5900, "chance": 9, "rarity": "rare", "description": "Vẻ đẹp kiêu sa lộng lẫy nhất trong các rạn san hô."},
    {"name": "🦀 Cua Huỳnh Đế Đại Lãnh", "price": 8700, "chance": 5, "rarity": "rare", "description": "Hình dáng như loài bọ khổng lồ màu đỏ gạch thơm nức."},
    {"name": "🐟 Cá Mú Cọp Đại Dương", "price": 8100, "chance": 6, "rarity": "rare", "description": "Vằn hổ dữ tợn ẩn mình dưới đáy sâu chờ đớp mồi."},
    {"name": "🐟 Cá Chim Đen Biển Sâu", "price": 6300, "chance": 9, "rarity": "rare", "description": "Thân dẹt đen mun bơi lượn vùng nước tối mịt."},
    {"name": "🐟 Cá Mai Biển Vàng", "price": 4700, "chance": 12, "rarity": "rare", "description": "Vảy mạ vàng óng ả phát sáng lấp lánh khi cắn câu."},
    {"name": "🐟 Cá Chẽm Hoa Nước Ngọt", "price": 5300, "chance": 11, "rarity": "rare", "description": "Hoa văn đốm hoa văn kỳ ảo trên vây và đuôi."},
    {"name": "🐟 Cá Hồng Vĩ Mỏ Két", "price": 6700, "chance": 8, "rarity": "rare", "description": "Đuôi đỏ rực rỡ như ngọn lửa bơi lội thanh thoát."},
    {"name": "🐟 Cá Đầu Bò Biển (Cowfish)", "price": 5400, "chance": 10, "rarity": "rare", "description": "Hai chiếc sừng nhô ra trên trán trông như chú bò con."},
    {"name": "🐟 Cá Sư Tử Độc (Lionfish)", "price": 7300, "chance": 7, "rarity": "rare", "description": "Vây xòe lộng lẫy nhưng mang gai độc gây buốt nhức."},
    {"name": "🐟 Cá Chuột Biển Dò Đáy", "price": 4100, "chance": 14, "rarity": "rare", "description": "Bộ râu cằm đánh hơi mồi giấu kín dưới cát biển."},
    {"name": "🐟 Cá Cương Thi Biển Sâu", "price": 8900, "chance": 5, "rarity": "rare", "description": "Làn da nhợt nhạt và hàm răng chìa ra rùng rợn."},
    {"name": "🦀 Cua Lông Thượng Hải", "price": 7700, "chance": 7, "rarity": "rare", "description": "Lớp lông nâu mịn ở càng, gạch béo ngậy nức tiếng."},

    # -------------------------------------------------------------------------
    # 🟣 EPIC (SỬ THI - GIÁ GỐC 4,500-21,000 COIN ➜ NÂNG LÊN 45,000 - 210,000 COIN)
    # -------------------------------------------------------------------------
    {"name": "🦈 Cá Mập Trắng Khổng Lồ", "price": 45000, "chance": 4.0, "rarity": "epic", "description": "Cỗ máy săn mồi hoàn hảo đứng đầu chuỗi thức ăn đại dương."},
    {"name": "🐬 Cá Heo Lưng Xám Thần Tốc", "price": 52000, "chance": 3.2, "rarity": "epic", "description": "Bơi lượn xé toạc ngọn sóng với trí tuệ vượt bậc."},
    {"name": "🐋 Cá Voi Xanh Đại Dương", "price": 80000, "chance": 2.0, "rarity": "epic", "description": "Sinh vật có kích thước vĩ đại nhất từng tồn tại trên Trái Đất."},
    {"name": "🦭 Hải Cẩu Băng Giá", "price": 48000, "chance": 3.5, "rarity": "epic", "description": "Sinh vật đáng yêu bơi lặn thiện nghệ giữa những tảng băng trôi."},
    {"name": "🦞 Tôm Hùm Hoàng Kim", "price": 95000, "chance": 1.5, "rarity": "epic", "description": "Đột biến sắc tố vàng kim triệu con mới có một."},
    {"name": "🦈 Megalodon Hóa Thạch", "price": 120000, "chance": 1.2, "rarity": "epic", "description": "Bạo chúa biển sâu thời tiền sử với hàm răng nuốt trọn thuyền."},
    {"name": "🐉 Rồng Biển Xanh Thẳm", "price": 110000, "chance": 1.3, "rarity": "epic", "description": "Sinh vật huyền bí uốn lượn như dải lụa phát sáng dưới đáy vực."},
    {"name": "🌌 Cá Thiên Hà Tinh Vân", "price": 140000, "chance": 0.9, "rarity": "epic", "description": "Làn da phát ra tinh tú lấp lánh như chứa cả dải ngân hà."},
    {"name": "🌑 Cá Hắc Ám Vực Sâu", "price": 135000, "chance": 1.0, "rarity": "epic", "description": "Hấp thụ mọi ánh sáng xung quanh, chỉ để lại đôi mắt đỏ rực."},
    {"name": "🔥 Cá Phượng Hoàng Lửa Biển", "price": 150000, "chance": 0.8, "rarity": "epic", "description": "Ngọn lửa bất tử bốc cháy rực rỡ ngay dưới làn nước lạnh giá."},
    {"name": "🐙 Ấu Thể Kraken (Baby Kraken)", "price": 160000, "chance": 0.7, "rarity": "epic", "description": "Dù còn nhỏ nhưng đã đủ sức quấn chìm tàu đánh cá nhỏ."},
    {"name": "💀 Cá Hố Tử Thần Mariana", "price": 130000, "chance": 1.0, "rarity": "epic", "description": "Thích nghi hoàn hảo với áp suất hàng nghìn atmosphere dưới rãnh Mariana."},
    {"name": "🌀 Cá Hư Không Void-Touched", "price": 180000, "chance": 0.5, "rarity": "epic", "description": "Bị nuốt chửng bởi vết rách không gian, nửa thực nửa ảo."},
    {"name": "⚡ Cá Sấm Sét Plasma", "price": 165000, "chance": 0.6, "rarity": "epic", "description": "Tích tụ bão điện xung quanh vây, phóng sét làm sôi cả nước."},
    {"name": "🔱 Sứ Giả Thần Biển", "price": 200000, "chance": 0.4, "rarity": "epic", "description": "Mang theo lời thì thầm và uy quyền của các vị thần đại dương."},
    {"name": "🌊 Cá Mái Chèo Oarfish Khổng Lồ", "price": 115000, "chance": 1.4, "rarity": "epic", "description": "Loài rồng biển dài hàng chục mét báo hiệu những chấn động địa chấn."},
    {"name": "🐋 Cá Voi Sát Thủ Orca", "price": 125000, "chance": 1.1, "rarity": "epic", "description": "Bầy thợ săn sát thủ thông minh phối hợp tác chiến điêu luyện."},
    {"name": "🦑 Mực Vực Thẳm Colossal Squid", "price": 145000, "chance": 0.8, "rarity": "epic", "description": "Sở hữu những chiếc móc vuốt xoay tròn trên xúc tu khổng lồ."},
    {"name": "🦴 Cá Vây Tay Hóa Thạch Sống (Coelacanth)", "price": 138000, "chance": 0.9, "rarity": "epic", "description": "Hóa thạch sống ngỡ đã tuyệt chủng cùng thời kỳ khủng long."},
    {"name": "🦈 Cá Mập Yêu Tinh (Goblin Shark)", "price": 105000, "chance": 1.5, "rarity": "epic", "description": "Bộ hàm có thể phóng ngược ra phía trước đớp trọn con mồi."},
    {"name": "🦀 Cua Hoàng Đế Đỏ Kamchatka", "price": 110000, "chance": 1.3, "rarity": "epic", "description": "Vua loài cua xứ băng tuyết với bộ giáp gai nhọn uy dũng."},
    {"name": "🌋 Cá Dung Nham Núi Lửa Biển", "price": 155000, "chance": 0.7, "rarity": "epic", "description": "Bơi lội tung tăng trong dòng thủy nhiệt núi lửa sôi sùng sục."},
    {"name": "🦈 Cá Mập Hổ (Tiger Shark)", "price": 118000, "chance": 1.2, "rarity": "epic", "description": "Sọc vằn như chúa sơn lâm sẵn sàng xơi tái mọi thứ trên đường bơi."},
    {"name": "🦈 Cá Mập Mako Cực Tốc", "price": 132000, "chance": 1.0, "rarity": "epic", "description": "Cá mập nhanh nhất thế giới lao vút như một quả ngư lôi."},
    {"name": "🦈 Cá Mập Thần Mù Greenland", "price": 142000, "chance": 0.9, "rarity": "epic", "description": "Sinh vật sống thọ hơn 400 năm dưới đáy biển băng Bắc Cực."},
    {"name": "🐋 Cá Voi Lưng Gù (Humpback Whale)", "price": 150000, "chance": 0.8, "rarity": "epic", "description": "Khúc tráng ca đại dương vang vọng hàng ngàn hải lý."},
    {"name": "🐋 Cá Voi Đầu Cong Vùng Cực", "price": 165000, "chance": 0.6, "rarity": "epic", "description": "Bộ hàm khổng lồ lọc hàng tấn sinh vật phù du mỗi ngày."},
    {"name": "🌿 Rồng Biển Lá (Leafy Seadragon)", "price": 175000, "chance": 0.5, "rarity": "epic", "description": "Ngụy trang hoàn hảo thành những nhánh rong biển đung đưa."},
    {"name": "🐉 Cá Rồng Kim Long Quá Bối", "price": 190000, "chance": 0.4, "rarity": "epic", "description": "Bộ vảy vàng rực xếp tầng như giáp trụ của bậc đế vương."},
    {"name": "🐢 Thần Quy Mai Vàng Nghìn Năm", "price": 185000, "chance": 0.5, "rarity": "epic", "description": "Mang theo linh khí đất trời ngự trị tại các giếng đáy đại dương."},
    {"name": "🧛 Mực Ma Ma Cà Rồng (Vampire Squid)", "price": 160000, "chance": 0.7, "rarity": "epic", "description": "Tấm màng đen như áo choàng quỷ lộn ngược phát sáng kỳ dị."},
    {"name": "🦁 Sứa Bờm Sư Tử Khổng Lồ", "price": 170000, "chance": 0.6, "rarity": "epic", "description": "Chiếc dù rộng 2m cùng hàng ngàn xúc tu dài hơn 30 mét."},
    {"name": "🦷 Cá Răng Nanh (Fangtooth)", "price": 140000, "chance": 0.9, "rarity": "epic", "description": "Tỉ lệ răng so với cơ thể lớn nhất thế giới sinh vật biển."},
    {"name": "🦀 Cua Nhện Nhật Bản Khổng Lồ", "price": 155000, "chance": 0.7, "rarity": "epic", "description": "Sải chân dài tới 4 mét lang thang dưới đáy vực tối."},
    {"name": "🦇 Cá Nạng Hải Manta Ray Khổng Lồ", "price": 180000, "chance": 0.5, "rarity": "epic", "description": "Sải cánh khổng lồ bay lượn nhẹ nhàng trong làn nước xanh biếc."},
    {"name": "🐟 Cá Mập Miệng Lớn (Megamouth Shark)", "price": 168000, "chance": 0.6, "rarity": "epic", "description": "Chiếc mồm phát sáng khổng lồ chỉ mở ra khi đêm xuống."},
    {"name": "🐉 Ngư Thần Răng Rồng (Dragonfish)", "price": 172000, "chance": 0.55, "rarity": "epic", "description": "Cơ thể đen nhánh với bộ răng trong suốt xuyên thấu con mồi."},
    {"name": "🐋 Cá Nhà Táng Săn Mực Khổng Lồ", "price": 195000, "chance": 0.45, "rarity": "epic", "description": "Chuyên lặn sâu hàng ngàn mét để tử chiến cùng mực khổng lồ."},
    {"name": "🐟 Cá Mú Nghệ Khổng Lồ (Goliath Grouper)", "price": 158000, "chance": 0.75, "rarity": "epic", "description": "Nặng nửa tấn nuốt chửng cả thợ lặn bất cẩn."},
    {"name": "🐊 Thằn Lằn Biển Mosasaurus Cổ Đại", "price": 210000, "chance": 0.35, "rarity": "epic", "description": "Quái thú bò sát biển thời Phấn Trắng tái sinh từ hóa thạch."},
    {"name": "🦈 Cá Mập Vây Đen Biển Đỏ", "price": 148000, "chance": 0.85, "rarity": "epic", "description": "Tốc độ bứt phá kinh hoàng ở những eo biển hẹp hiểm trở."},
    {"name": "🪼 Sứa Hộp Chết Chóc Chironex", "price": 162000, "chance": 0.65, "rarity": "epic", "description": "Nọc độc làm tê liệt tim trong vài giây trôi dạt trong suốt."},

    # -------------------------------------------------------------------------
    # 🟡 LEGENDARY (HUYỀN THOẠI - GIÁ GỐC 60,000-2,600,000 COIN ➜ NÂNG LÊN 600,000 - 26,000,000 COIN)
    # -------------------------------------------------------------------------
    {"name": "🐉 Hắc Long Hải Thần", "price": 600000, "chance": 0.8, "rarity": "legendary", "description": "Rồng đen trấn giữ long mạch biển sâu ngàn năm."},
    {"name": "🐙 Thủy Quái Kraken Bắc Hải", "price": 850000, "chance": 0.5, "rarity": "legendary", "description": "Cơn ác mộng kinh hoàng nhất của mọi thuyền trưởng từng ra khơi."},
    {"name": "🐋 Thủy Thần Leviathan", "price": 1200000, "chance": 0.3, "rarity": "legendary", "description": "Cự thú đại dương có thân hình to lớn như cả một hòn đảo di động."},
    {"name": "🧜 Nàng Tiên Cá Thần Thoại", "price": 1500000, "chance": 0.2, "rarity": "legendary", "description": "Giọng hát mê đắm lòng người mang theo phép thuật đại dương."},
    {"name": "🐋 Leviathan Prime Tối Thượng", "price": 1800000, "chance": 0.15, "rarity": "legendary", "description": "Nguyên bản đầu tiên của giống loài Leviathan thống trị kỷ Cambri."},
    {"name": "🐙 Kraken Alpha Chúa Tể", "price": 2200000, "chance": 0.10, "rarity": "legendary", "description": "Thủ lĩnh đàn Kraken với hàng trăm xúc tu che lấp cả mặt trời."},
    {"name": "🌌 Cá Voi Thiên Cầu Vũ Trụ", "price": 2800000, "chance": 0.08, "rarity": "legendary", "description": "Bơi lội giữa ranh giới đại dương và vũ trụ vô tận."},
    {"name": "🐉 Thần Long Đại Dương Ryujin", "price": 3500000, "chance": 0.06, "rarity": "legendary", "description": "Long vương nắm giữ thủy triều và ngọc ước nguyện của biển cả."},
    {"name": "🔱 Cá Hải Thần Poseidon", "price": 4500000, "chance": 0.04, "rarity": "legendary", "description": "Mang theo cây đinh ba quyền năng điều khiển cuồng phong biển dữ."},
    {"name": "☠️ Cá Hủy Diệt Abaddon", "price": 6000000, "chance": 0.03, "rarity": "legendary", "description": "Hơi thở của nó làm nước biển sôi trào và ăn mòn mọi kim loại."},
    {"name": "☄️ Cá Thiên Thạch Sao Băng", "price": 7500000, "chance": 0.02, "rarity": "legendary", "description": "Rơi xuống từ không gian sâu thẳm, vây cá rực cháy ánh plasma."},
    {"name": "✨ Cá Tinh Linh Ánh Sáng Seraph", "price": 9000000, "chance": 0.015, "rarity": "legendary", "description": "Tỏa ra vầng hào quang thần thánh xua tan bóng tối muôn trượng."},
    {"name": "🌑 Cá Vực Thẳm Tartarus", "price": 12000000, "chance": 0.01, "rarity": "legendary", "description": "Sinh vật trồi lên từ tầng sâu tăm tối nhất của đáy địa ngục."},
    {"name": "🪐 Cá Tận Thế Ragnarok", "price": 20000000, "chance": 0.005, "rarity": "legendary", "description": "Sự xuất hiện của nó báo hiệu ngày suy tàn của mọi nền văn minh."},
    {"name": "🦀 Cự Thần Cua Karkinos", "price": 8500000, "chance": 0.02, "rarity": "legendary", "description": "Con cua thần trong thần thoại Hy Lạp với lớp vỏ bất hoại."},
    {"name": "🦴 Bạo Ngư Thiết Giáp Dunkleosteus", "price": 9500000, "chance": 0.018, "rarity": "legendary", "description": "Chiếc hàm bọc giáp thép có lực cắn nghiền nát cả vỏ tàu ngầm."},
    {"name": "❄️ Cự Xà Băng Giá Jormungandr", "price": 14000000, "chance": 0.008, "rarity": "legendary", "description": "Mãng xà quấn quanh thế giới, đóng băng mọi dòng hải lưu."},
    {"name": "🩸 Thần Mập Huyết Hải Bloodmoon", "price": 11000000, "chance": 0.012, "rarity": "legendary", "description": "Chỉ trồi lên dưới ánh trăng máu, nhuộm đỏ cả một vùng biển."},
    {"name": "🌙 Cự Ngư Bakunawa Nuốt Trăng", "price": 16000000, "chance": 0.007, "rarity": "legendary", "description": "Quái rồng biển trong truyền thuyết chuyên nuốt chửng các mặt trăng."},
    {"name": "🐘 Thần Thú Biển Makara Ấn Độ", "price": 13000000, "chance": 0.010, "rarity": "legendary", "description": "Sinh vật mình thú đuôi cá vật cưỡi của thần mưa Varuna."},
    {"name": "🐋 Bạch Kình Moby Dick Vĩ Đại", "price": 17500000, "chance": 0.006, "rarity": "legendary", "description": "Con cá voi trắng bất tử cắm đầy những ngọn giáo săn cá voi xưa."},
    {"name": "🌊 Mẫu Thần Tiamat Thủy Tổ", "price": 22000000, "chance": 0.004, "rarity": "legendary", "description": "Nữ thần rồng biển nguyên thủy hiện thân của biển nước mặn hỗn mang."},
    {"name": "🐉 Hắc Long Nidhogg Biển Sâu", "price": 19000000, "chance": 0.005, "rarity": "legendary", "description": "Rồng đen gặm nhấm rễ cây thế giới nằm ẩn dưới đáy vực thẳm."},
    {"name": "🪶 Vũ Xà Quetzalcoatl Biển Nam", "price": 21000000, "chance": 0.004, "rarity": "legendary", "description": "Rắn có lông vũ khổng lồ uốn lượn mang lại những cơn mưa đại ngàn."},
    {"name": "🦕 Quái Vật Hồ Loch Ness (Nessie)", "price": 15000000, "chance": 0.008, "rarity": "legendary", "description": "Chiếc cổ dài vươn lên giữa làn sương mù huyền bí của xứ Scotland."},
    {"name": "⚡ Lôi Long Hải Vương Thunder Drake", "price": 18500000, "chance": 0.006, "rarity": "legendary", "description": "Tiếng gầm thét tạo thành những cơn lốc xoáy sấm sét ngoài khơi."},
    {"name": "🔥 Hỏa Long Thủy Triều Magma Drake", "price": 19500000, "chance": 0.005, "rarity": "legendary", "description": "Nung chảy cả đáy biển tạo thành những mạch đá quý đỏ rực."},
    {"name": "💎 Cá Pha Lê Bất Diệt Crystalline", "price": 25000000, "chance": 0.003, "rarity": "legendary", "description": "Cơ thể hoàn toàn bằng kim cương tinh khiết phản chiếu ánh mặt trời."},
    {"name": "🗿 Cự Thạch Ngư Biển Cổ", "price": 16500000, "chance": 0.007, "rarity": "legendary", "description": "Thân thể kết tinh từ đá tảng đáy biển phong ấn linh hồn chiến binh cổ."},
    {"name": "🌪️ Phong Thần Cá Chình Cực Bắc", "price": 17800000, "chance": 0.006, "rarity": "legendary", "description": "Kéo theo những trận bão tuyết xé tan băng đảo Bắc Băng Dương."},
    {"name": "🦚 Cá Khổng Tước Thần Hải", "price": 23000000, "chance": 0.0035, "rarity": "legendary", "description": "Đuôi xòe như chim khổng tước phát ra âm thanh du dương ru ngủ đại dương."},
    {"name": "⚔️ Kiếm Thần Ngư Excalibur", "price": 26000000, "chance": 0.0028, "rarity": "legendary", "description": "Mũi kiếm đúc từ thiên thạch rèn bởi các pháp sư hoàng gia cổ đại."},

    # -------------------------------------------------------------------------
    # 🔴 ADMIN (THẦN THOẠI TỐI CAO - GIÁ GỐC 5M-999M ➜ NÂNG LÊN 50M - 9.9 TỶ COIN)
    # -------------------------------------------------------------------------
    {"name": "👑 Cá Thần Tối Thượng", "price": 50000000, "chance": 0.003, "rarity": "admin", "description": "Sinh vật tôn quý tối thượng cai quản toàn bộ sinh linh biển cả."},
    {"name": "🌌 Cá Hư Không Vĩnh Cửu", "price": 100000000, "chance": 0.0015, "rarity": "admin", "description": "Sinh vật vượt ra ngoài ranh giới không gian và thời gian 3 chiều."},
    {"name": "👾 Discord Leviathan Nguyên Bản", "price": 250000000, "chance": 0.0008, "rarity": "admin", "description": "Được tạo nên từ hàng tỷ dòng code và năng lượng máy chủ Discord."},
    {"name": "🌌 Void Kraken Vô Tận", "price": 400000000, "chance": 0.0005, "rarity": "admin", "description": "Thủy quái nuốt trọn cả các lỗ đen vũ trụ vào chiếc xúc tu khổng lồ."},
    {"name": "🌸 Nanally Whale Thần Thánh", "price": 600000000, "chance": 0.0003, "rarity": "admin", "description": "Linh thú hộ mệnh tối thượng của chủ nhân Sakura Bot."},
    {"name": "🪐 Cá Vũ Trụ Ngân Hà Thần Tộc", "price": 850000000, "chance": 0.0002, "rarity": "admin", "description": "Cơ thể nó chứa đựng các hành tinh và hàng triệu ngôi sao đang xoay."},
    {"name": "🔱 Abyss God Fish - Thần Vực Sâu", "price": 1200000000, "chance": 0.0001, "rarity": "admin", "description": "Vị thần tối cao của bóng tối vĩnh hằng dưới tâm Trái Đất."},
    {"name": "⚠️ Cá ERROR [404 Not Found]", "price": 1800000000, "chance": 0.00008, "rarity": "admin", "description": "Một lỗi glitch thực tại biến thành thực thể sinh vật sống động."},
    {"name": "💥 Reality Breaker Kẻ Phá Vỡ", "price": 2500000000, "chance": 0.00005, "rarity": "admin", "description": "Mỗi cái vẫy đuôi làm rạn nứt không thời gian thực tại."},
    {"name": "👑 Cá Thần Tối Cao Chí Tôn", "price": 4000000000, "chance": 0.00003, "rarity": "admin", "description": "Đấng sáng thế cai trị mọi biển khơi trong vũ trụ."},
    {"name": "🌱 The First Fish (Cá Khởi Nguyên)", "price": 6500000000, "chance": 0.00001, "rarity": "admin", "description": "Sinh vật sống đầu tiên xuất hiện khi đại dương khai sinh."},
    {"name": "♾️ Null Fish - Vô Cực", "price": 9999999999, "chance": 0.000005, "rarity": "admin", "description": "Tồn tại ngoài mọi định nghĩa ngôn từ, giá trị vô lượng."},
    {"name": "⏳ Chronos Fish (Cá Thời Gian)", "price": 3200000000, "chance": 0.00004, "rarity": "admin", "description": "Bơi ngược dòng thời gian, mang ký ức của quá khứ và tương lai."},
    {"name": "🧬 Genesis Fish (Cá Khởi Sinh)", "price": 5000000000, "chance": 0.00002, "rarity": "admin", "description": "Mang mã gen gốc có thể tái tạo lại toàn bộ hệ sinh thái đã diệt vong."},
    {"name": "🕳️ Hố Đen Đại Dương Singularity", "price": 8000000000, "chance": 0.000008, "rarity": "admin", "description": "Hút cạn mọi vật chất và ánh sáng vào một điểm kỳ dị vô cực."},
    {"name": "☀️ Siêu Tân Tinh Supernova Koi", "price": 4500000000, "chance": 0.000025, "rarity": "admin", "description": "Bùng nổ với năng lượng ánh sáng của một ngôi sao khổng lồ phát nổ."},
    {"name": "🌌 Đa Vũ Trụ Thôn Phệ Giả (Multiverse Devourer)", "price": 9000000000, "chance": 0.000006, "rarity": "admin", "description": "Sinh vật khổng lồ bơi qua các vũ trụ song song nuốt chửng các thiên hà."},
    {"name": "💻 Matrix Cyber Whale", "price": 2800000000, "chance": 0.000045, "rarity": "admin", "description": "Cá voi cơ khí cấu thành từ mã nhị phân màu xanh lá chạy dọc thân."},
    {"name": "⚛️ Cá Hạt Lượng Tử Quantum Fish", "price": 3600000000, "chance": 0.000035, "rarity": "admin", "description": "Đồng thời tồn tại ở cả trong giỏ và ngoài biển cho đến khi được quan sát."},
    {"name": "🐍 Ouroboros Vô Tận Thần Ngư", "price": 7500000000, "chance": 0.000009, "rarity": "admin", "description": "Cắn đuôi tạo thành vòng tròn hoàn mỹ biểu trưng cho sự tái sinh bất diệt."},
    {"name": "👁️ Con Mắt Hải Thần The All-Seeing", "price": 8888888888, "chance": 0.000007, "rarity": "admin", "description": "Thấu suốt tất cả sự việc diễn ra ở mọi độ sâu của các đại dương."},
    {"name": "📜 Cá Định Mệnh Khắc Tên (Fated Fish)", "price": 6000000000, "chance": 0.000015, "rarity": "admin", "description": "Chỉ cắn câu đúng một người duy nhất được số phận lựa chọn."},
    {"name": "🌌 Cthulhu Thần Thoại Thức Giấc", "price": 9500000000, "chance": 0.000004, "rarity": "admin", "description": "Cổ thần ngủ say dưới thành phố chìm R'lyeh nay đã thức tỉnh."},
    {"name": "💠 Tinh Thể Khởi Thủy Primordial Shard", "price": 7000000000, "chance": 0.000010, "rarity": "admin", "description": "Khối tinh thể ngưng tụ trước cả khi vũ trụ giãn nở."},
    {"name": "🪞 Gương Thực Tại Kính Ngư", "price": 8200000000, "chance": 0.000008, "rarity": "admin", "description": "Phản chiếu hình ảnh phản nghịch của bất kỳ sinh vật nào nhìn vào mắt nó."},
    {"name": "🔥 Phượng Hoàng Lửa Bất Diệt Solaris", "price": 6800000000, "chance": 0.000012, "rarity": "admin", "description": "Hóa tro tàn sau mỗi 1000 năm rồi hồi sinh từ ngọn lửa đáy biển."}
]

# Tải thêm cá tùy chỉnh tạo từ Admin Web nếu có
try:
    import json
    from pathlib import Path
    _cf_path = Path(__file__).resolve().parent / "custom_fish.json"
    if _cf_path.exists():
        with open(_cf_path, "r", encoding="utf-8") as _f:
            _custom = json.load(_f)
            if isinstance(_custom, list):
                fish_list.extend(_custom)
except Exception:
    pass

# =============================================================================
# CỬA HÀNG VẬT PHẨM & NÂNG CẤP
# =============================================================================
shop_items = {
    "rename_card": {
        "name": "📝 Thẻ Đổi Tên",
        "price": 2200000,
        "description": "Đổi nickname người khác trong server",
        "type": "rename",
        "rarity": "admin",
        "limited": False
    },
    "voice_kick": {
        "name": "🔊 Voice Kick",
        "price": 1800000,
        "description": "Kick người khác khỏi phòng thoại",
        "type": "voicekick",
        "rarity": "admin",
        "limited": False
    },
    "mute_card": {
        "name": "🔇 Thẻ Mute",
        "price": 2000000,
        "description": "Timeout người khác trong 30 giây",
        "type": "mute",
        "rarity": "admin",
        "limited": False
    },
    "bomb_card": {
        "name": "💣 Thẻ Bom Hẹn Giờ",
        "price": 450000,
        "description": "Gài bom hẹn giờ và tag mục tiêu sau 5 giây.",
        "type": "bomb",
        "rarity": "epic",
        "limited": False
    },
    "love_confession": {
        "name": "💌 Thư Tỏ Tình",
        "price": 150000,
        "description": "Gửi một lời tỏ tình bất ngờ đến ai đó.",
        "type": "confess",
        "rarity": "rare",
        "limited": False
    },
    "ghost_ping": {
        "name": "👻 Thẻ Ghost Ping",
        "price": 800000,
        "description": "Ping một người rồi xóa tin nhắn ngay lập tức.",
        "type": "ghostping",
        "rarity": "epic",
        "limited": False
    },
    "shield": {
        "name": "🛡️ Khiên Bảo Vệ",
        "price": 1500000,
        "description": "Chặn hoàn toàn 1 đòn troll độc hại",
        "type": "shield",
        "rarity": "admin",
        "limited": False
    },
    "dragon_pet": {
        "name": "🐉 Rồng Pet",
        "price": 6500000,
        "description": "Pet siêu hiếm tăng mạnh may mắn và giá bán",
        "type": "pet",
        "rarity": "legendary",
        "limited": True
    },
    "cat_pet": {
        "name": "🐱 Mèo Pet",
        "price": 60000,
        "description": "Pet dễ thương nhặt thêm mồi câu",
        "type": "pet",
        "rarity": "common",
        "limited": False
    },
    "vip_role": {
        "name": "👑 VIP Role",
        "price": 5000000,
        "description": "Nhận role VIP danh giá",
        "type": "role",
        "rarity": "legendary",
        "role_id": 1506108953795493909,
        "limited": True
    },
    "ve_so": {
        "name": "🎟️ Vé Số",
        "price": 30000,
        "description": "Thử vận may có cơ hội trúng 2,000,000 coin",
        "type": "lottory",
        "rarity": "common",
        "limited": False
    },
    "inventory_bag_small": {
        "name": "🎒 Túi Đồ Nhỏ",
        "price": 20000,
        "type": "inventory_limit",
        "rarity": "rare",
        "inventory_slots": 10,
        "description": "Tăng giới hạn item thêm 10."
    },
    "inventory_bag_medium": {
        "name": "👜 Túi Đồ Vừa",
        "price": 95000,
        "type": "inventory_limit",
        "rarity": "epic",
        "inventory_slots": 25,
        "description": "Tăng giới hạn item thêm 25."
    },
    "inventory_bag_large": {
        "name": "📦 Kho Đồ Lớn",
        "price": 300000,
        "type": "inventory_limit",
        "rarity": "legendary",
        "inventory_slots": 50,
        "description": "Tăng giới hạn item thêm 50."
    },
    "fish_bag_small": {
        "name": "🎒 Túi Cá Nhỏ",
        "price": 20000,
        "type": "fish_limit",
        "rarity": "rare",
        "fish_slots": 10,
        "description": "Tăng giới hạn giỏ cá thêm 10."
    },
    "fish_bag_medium": {
        "name": "👜 Túi Cá Vừa",
        "price": 95000,
        "type": "fish_limit",
        "rarity": "epic",
        "fish_slots": 25,
        "description": "Tăng giới hạn giỏ cá thêm 25."
    },
    "fish_bag_large": {
        "name": "📦 Thùng Cá Lớn",
        "price": 300000,
        "type": "fish_limit",
        "rarity": "legendary",
        "fish_slots": 50,
        "description": "Tăng giới hạn giỏ cá thêm 50."
    },
    "fish_bag_admin": {
        "name": "👑 Kho Cá Admin",
        "price": 9999999,
        "type": "fish_limit",
        "rarity": "admin",
        "fish_slots": 999,
        "description": "Kho chứa cá vô hạn."
    },
    # Cần câu
    "rod_wood": {
        "name": "🎣 Cần Câu Gỗ",
        "price": 2500,
        "level": 1,
        "luck": 2,
        "description": "Cần câu cơ bản cho người mới bắt đầu.",
        "type": "rod",
        "durability": 50,
        "rarity": "common"
    },
    "rod_bamboo": {
        "name": "🎋 Cần Câu Tre Dẻo",
        "price": 12000,
        "level": 3,
        "luck": 8,
        "description": "Cần tre có độ đàn hồi tốt, dễ vớt cá nhanh.",
        "type": "rod",
        "durability": 90,
        "rarity": "common"
    },
    "rod_iron": {
        "name": "🎣 Cần Câu Sắt",
        "price": 45000,
        "level": 5,
        "luck": 16,
        "description": "Cần câu chắc chắn hơn, bắt được cá hiếm.",
        "type": "rod",
        "durability": 160,
        "rarity": "rare"
    },
    "rod_coral": {
        "name": "🪸 Cần San Hô Cổ",
        "price": 95000,
        "level": 8,
        "luck": 26,
        "description": "Được đẽo gọt từ rạn san hô ngàn năm.",
        "type": "rod",
        "durability": 250,
        "rarity": "rare"
    },
    "rod_gold": {
        "name": "🎣 Cần Câu Vàng",
        "price": 190000,
        "level": 12,
        "luck": 38,
        "description": "Cần câu cao cấp mạ vàng óng ánh.",
        "type": "rod",
        "durability": 400,
        "rarity": "epic"
    },
    "rod_obsidian": {
        "name": "🖤 Cần Hắc Diện Thạch",
        "price": 380000,
        "level": 16,
        "luck": 55,
        "description": "Độ bền cực cao rèn từ đá núi lửa biển sâu.",
        "type": "rod",
        "durability": 700,
        "rarity": "epic"
    },
    "rod_diamond": {
        "name": "💎 Cần Câu Kim Cương",
        "price": 750000,
        "level": 20,
        "luck": 75,
        "description": "Cần câu huyền thoại tỉ lệ cá khủng rất cao.",
        "type": "rod",
        "durability": 1100,
        "rarity": "legendary"
    },
    "rod_mecha": {
        "name": "🤖 Cần Cơ Khí Thủy Triều",
        "price": 1800000,
        "level": 25,
        "luck": 105,
        "description": "Công nghệ trợ lực điện từ kéo quái thú dễ dàng.",
        "type": "rod",
        "durability": 1800,
        "rarity": "legendary"
    },
    "rod_owner": {
        "name": "👑 Cần Câu Tối Thượng",
        "price": 99999999,
        "description": "Cần câu quyền năng bất tử của Chủ Bot.",
        "level": 99,
        "luck": 9999,
        "type": "rod",
        "durability": 99999,
        "rarity": "admin"
    },
    # Mồi câu
    "bait_normal": {
        "name": "🪱 Mồi Thường",
        "price": 300,
        "luck": 3,
        "description": "Mồi cơ bản dễ mua.",
        "type": "bait",
        "rarity": "common"
    },
    "bait_rare": {
        "name": "🪱 Mồi Hiếm",
        "price": 2500,
        "luck": 10,
        "description": "Mồi chất lượng cao thu hút cá hiếm.",
        "type": "bait",
        "rarity": "rare"
    },
    "bait_epic": {
        "name": "🪱 Mồi Sử Thi",
        "price": 9500,
        "luck": 22,
        "description": "Mồi thơm ngon cá lớn rất thích.",
        "type": "bait",
        "rarity": "epic"
    },
    "bait_glow": {
        "name": "✨ Mồi Dạ Quang",
        "price": 28000,
        "luck": 35,
        "description": "Phát sáng dưới đáy biển sâu.",
        "type": "bait",
        "rarity": "epic"
    },
    "bait_legend": {
        "name": "🪱 Mồi Huyền Thoại",
        "price": 65000,
        "luck": 55,
        "description": "Có thể dụ các loài thủy quái huyền thoại.",
        "type": "bait",
        "rarity": "legendary"
    },
    "bait_dragon": {
        "name": "🩸 Mồi Máu Rồng",
        "price": 150000,
        "luck": 80,
        "description": "Tẩm huyết long có sức hút cực kỳ khủng khiếp.",
        "type": "bait",
        "rarity": "legendary"
    }
}

market = {}

# =============================================================================
# DỮ LIỆU CUNG HOÀNG ĐẠO (ZODIAC)
# =============================================================================
ZODIAC_DATA = [
    {
        "name": "Bảo Bình (Aquarius)", "emoji": "♒", "dates": "20/01 - 18/02", "start_code": 120, "end_code": 218, "color": 0x2980b9,
        "personality": "Sáng tạo, độc lập, có tư duy lập dị/độc đáo và yêu chủ nghĩa nhân đạo. Thích đi ngược lại số đông.",
        "love": "Coi trọng sự tự do cá nhân và không gian riêng. Thường bắt đầu từ tình bạn rồi mới tiến đến tình yêu.",
        "work": "Xuất sắc trong nghiên cứu công nghệ, lập trình viên, nhà khoa học hoặc hoạt động xã hội."
    },
    {
        "name": "Song Ngư (Pisces)", "emoji": "♓", "dates": "19/02 - 20/03", "start_code": 219, "end_code": 320, "color": 0x16a085,
        "personality": "Mơ mộng, giàu lòng trắc ẩn, nghệ sĩ và dễ thấu cảm với người khác. Tuy nhiên dễ bị ảnh hưởng tâm lý tiêu cực.",
        "love": "Lãng mạn, hy sinh hết mình vì người yêu. Thích những câu chuyện tình mang màu sắc cổ tích.",
        "work": "Phù hợp tuyệt đối với nghệ thuật (âm nhạc, hội họa), viết lách, công tác từ thiện hoặc điều dưỡng."
    },
    {
        "name": "Bạch Dương (Aries)", "emoji": "♈", "dates": "21/03 - 19/04", "start_code": 321, "end_code": 419, "color": 0xe74c3c,
        "personality": "Mạnh mẽ, tiên phong, đầy nhiệt huyết và có tính cạnh tranh cao. Đôi khi hơi nóng nảy và thiếu kiên nhẫn.",
        "love": "Chủ động, mãnh liệt và chân thành. Thích sự rõ ràng và luôn muốn bảo vệ nửa kia của mình.",
        "work": "Phù hợp với vai trò lãnh đạo, nhà khởi nghiệp hoặc các công việc đòi hỏi sự đổi mới và năng động."
    },
    {
        "name": "Kim Ngưu (Taurus)", "emoji": "♉", "dates": "20/04 - 20/05", "start_code": 420, "end_code": 520, "color": 0x2ecc71,
        "personality": "Kiên nhẫn, đáng tin cậy, thực tế và yêu chuộng sự ổn định. Có thiên hướng yêu nghệ thuật và ẩm thực.",
        "love": "Chung thủy, thực tế và có xu hướng chiếm hữu cao. Cần thời gian dài để tìm hiểu nhưng một khi đã yêu sẽ rất bền vững.",
        "work": "Xuất sắc trong các lĩnh vực quản lý tài chính, ngân hàng, bất động sản hoặc nghệ thuật nhờ sự cẩn trọng."
    },
    {
        "name": "Song Tử (Gemini)", "emoji": "♊", "dates": "21/05 - 21/06", "start_code": 521, "end_code": 621, "color": 0xf1c40f,
        "personality": "Thông minh, thích giao tiếp, thích nghi nhanh và tò mò về thế giới. Có tính cách đa dạng.",
        "love": "Thích sự mới mẻ, thú vị và cần sự hòa hợp về mặt trí tuệ. Ghét sự ràng buộc hoặc nhàm chán.",
        "work": "Rất hợp với ngành truyền thông, marketing, báo chí, hướng dẫn viên hoặc bất kỳ công việc nào cần đàm phán."
    },
    {
        "name": "Cự Giải (Cancer)", "emoji": "♋", "dates": "22/06 - 22/07", "start_code": 622, "end_code": 722, "color": 0x3498db,
        "personality": "Giàu tình cảm, tinh tế, có trực giác nhạy bén và luôn hướng về gia đình. Tuy nhiên, tâm trạng khá thất thường.",
        "love": "Ấm áp, chu đáo và thích chăm sóc người yêu. Dễ bị tổn thương nên thường tự tạo lớp vỏ bọc bảo vệ.",
        "work": "Thích hợp làm giáo viên, bác sĩ, tâm lý học, quản lý nhân sự hoặc các công việc liên quan đến chăm sóc khách hàng."
    },
    {
        "name": "Sư Tử (Leo)", "emoji": "♌", "dates": "23/07 - 22/08", "start_code": 723, "end_code": 822, "color": 0xe67e22,
        "personality": "Tự tin, hào phóng, có tố chất lãnh đạo và thích trở thành tâm điểm của sự chú ý. Có cái tôi khá cao.",
        "love": "Say đắm, kiêu hãnh và rất chiều chuộng người yêu. Thích được đối phương khen ngợi và tôn trọng.",
        "work": "Thích hợp làm quản lý, diễn viên, nghệ sĩ biểu diễn hoặc các công việc có sức ảnh hưởng lớn trước công chúng."
    },
    {
        "name": "Xử Nữ (Virgo)", "emoji": "♍", "dates": "23/08 - 22/09", "start_code": 823, "end_code": 922, "color": 0x95a5a6,
        "personality": "Cầu toàn, phân tích logic tốt, sạch sẽ và rất thực tế. Đôi khi hay soi xét chi tiết quá mức.",
        "love": "Thận trọng và thực tế. Biểu hiện tình yêu bằng hành động chăm sóc cụ thể chứ không thích những lời sáo rỗng.",
        "work": "Làm tốt các công việc phân tích dữ liệu, kế toán, biên tập viên, kiểm toán hoặc nghiên cứu khoa học."
    },
    {
        "name": "Thiên Bình (Libra)", "emoji": "♎", "dates": "23/09 - 23/10", "start_code": 923, "end_code": 1023, "color": 0x1abc9c,
        "personality": "Duyên dáng, yêu hòa bình, công bằng và có gu thẩm mỹ cao. Điểm yếu là thường hay do dự khi quyết định.",
        "love": "Lãng mạn, tinh tế và luôn tìm kiếm sự cân bằng, hòa hợp. Thích một mối quan hệ nhẹ nhàng, không cãi vã.",
        "work": "Thích hợp làm luật sư, nhà ngoại giao, nhà thiết kế thời trang hoặc quan hệ công chúng (PR)."
    },
    {
        "name": "Thiên Yết (Scorpio)", "emoji": "♏", "dates": "24/10 - 22/11", "start_code": 1024, "end_code": 1122, "color": 0x34495e,
        "personality": "Bí ẩn, có ý chí mạnh mẽ, sâu sắc và có trực giác cực kỳ nhạy bén. Đã ghét ai thì ghét rất lâu.",
        "love": "Yêu cuồng nhiệt, chung thủy tuyệt đối nhưng đi kèm với lòng ghen tuông và tính kiểm soát cực kỳ cao.",
        "work": "Phù hợp làm thám tử, nhà nghiên cứu, bác sĩ phẫu thuật, tâm lý học tội phạm hoặc đầu tư tài chính."
    },
    {
        "name": "Nhân Mã (Sagittarius)", "emoji": "♐", "dates": "23/11 - 21/12", "start_code": 1123, "end_code": 1221, "color": 0x9b59b6,
        "personality": "Lạc quan, yêu tự do, thích khám phá và thẳng thắn. Ghét sự gò bó nhưng đôi khi vô tâm.",
        "love": "Thích trải nghiệm, không thích bị kiểm soát. Khi yêu cần một người bạn đồng hành có cùng lý tưởng sống.",
        "work": "Phù hợp làm hướng dẫn viên du lịch, xuất nhập khẩu, giáo sư, nhiếp ảnh gia tự do hoặc dịch thuật."
    },
    {
        "name": "Ma Kết (Capricorn)", "emoji": "♑", "dates": "22/12 - 19/01", "start_code": 1222, "end_code": 1019, "color": 0x7f8c8d,
        "personality": "Trách nhiệm, kỷ luật, kiên trì và tham vọng lớn. Sống thực tế, trưởng thành sớm nhưng hơi khô khan.",
        "love": "Nghiêm túc, hướng đến tương lai lâu dài và sự ổn định. Thể hiện tình cảm bằng sự che chở và vững chãi kinh tế.",
        "work": "Sinh ra để làm nhà quản lý, chính trị gia, giám đốc tài chính hoặc các công việc hành chính cấp cao."
    }
]

# =============================================================================
# DỮ LIỆU BÀI TAROT (78 LÁ)
# =============================================================================
TAROT_DECK = {
    # 22 Lá Ẩn Chính (Major Arcana)
    "0. The Fool (Chàng Khờ)": {"upright": "Khởi đầu mới, tự do, ngây thơ, phiêu lưu, tự phát.", "reversed": "Liều lĩnh, bất cẩn, trì hoãn, sợ rủi ro, ngây ngô."},
    "I. The Magician (Nhà Ảo Thuật)": {"upright": "Sức mạnh ý chí, khéo léo, tài năng, chủ động, hiện thực hóa ước mơ.", "reversed": "Thao túng, lừa dối, lãng phí tiềm năng, ảo tưởng sức mạnh."},
    "II. The High Priestess (Nữ Tư Tế)": {"upright": "Trực giác, bí ẩn, tiềm thức, sự thông thái, tĩnh lặng.", "reversed": "Bí mật bị lộ, lờ đi tiếng nói bên trong, hời hợt, bồn chồn."},
    "III. The Empress (Nữ Hoàng)": {"upright": "Nuôi dưỡng, phong phú, thiên nhiên, sáng tạo, sung túc.", "reversed": "Sự phụ thuộc, ngột ngạt, thiếu sáng tạo, hoang phí."},
    "IV. The Emperor (Hoàng Đế)": {"upright": "Quyền lực, cấu trúc, vững chãi, bảo vệ, tính kỷ luật.", "reversed": "Bảo thủ, độc đoán, kiểm soát quá mức, bất lực."},
    "V. The Hierophant (Thầy Tư Tế)": {"upright": "Truyền thống, giáo dục, niềm tin, tổ chức, sự phù hợp.", "reversed": "Nổi loạn, phá vỡ quy chuẩn, giáo điều, tư duy mới."},
    "VI. The Lovers (Tình Nhân)": {"upright": "Tình yêu, hòa hợp, mối quan hệ, lựa chọn, đồng điệu.", "reversed": "Mất cân bằng, bất hòa, lựa chọn sai lầm, rạn nứt."},
    "VII. The Chariot (Cỗ Xe Chiến Thắng)": {"upright": "Ý chí, chiến thắng, kiểm soát, quyết tâm, tiến về phía trước.", "reversed": "Mất phương hướng, thiếu kiểm soát, hung hăng, bế tắc."},
    "VIII. Strength (Sức Mạnh)": {"upright": "Dũng cảm, kiên nhẫn, sức mạnh nội tâm, bao dung.", "reversed": "Yếu đuối, tự ti, mất bình tĩnh, thô bạo."},
    "IX. The Hermit (Ẩn Sĩ)": {"upright": "Sự chiêm nghiệm, cô độc, tìm kiếm nội tâm, dẫn đường.", "reversed": "Cô lập, cô đơn, từ chối lời khuyên, lập dị."},
    "X. Wheel of Fortune (Vòng Quay Số Phận)": {"upright": "May mắn, định mệnh, thay đổi lớn, bước ngoặt, chu kỳ mới.", "reversed": "Xui xẻo, kháng cự thay đổi, xáo trộn ngoài ý muốn."},
    "XI. Justice (Công Lý)": {"upright": "Công bằng, sự thật, luật pháp, nhân quả, trách nhiệm.", "reversed": "Bất công, dối trá, không nhận lỗi, thiên vị."},
    "XII. The Hanged Man (Kẻ Treo Ngược)": {"upright": "Buông bỏ, góc nhìn mới, trì hoãn có mục đích, hy sinh.", "reversed": "Trì trệ, hy sinh vô ích, chống đối, không chịu thay đổi."},
    "XIII. Death (Cái Chết)": {"upright": "Kết thúc, chuyển giao, thay đổi lớn, tái sinh, buông bỏ cái cũ.", "reversed": "Kháng cự thay đổi, trì trệ, lặp lại lối mòn, sợ hãi."},
    "XIV. Temperance (Sự Chừng Mực)": {"upright": "Cân bằng, kiên nhẫn, hòa hợp, điều độ, chữa lành.", "reversed": "Mất cân bằng, thừa thãi, xung đột, thiếu nhất quán."},
    "XV. The Devil (Ác Quỷ)": {"upright": "Sự ràng buộc, cám dỗ, vật chất, nghiện ngập, ảo tưởng.", "reversed": "Sự giải thoát, nhận ra sai lầm, buông bỏ thói quen xấu."},
    "XVI. The Tower (Tòa Tháp)": {"upright": "Sụp đổ bất ngờ, biến động mạnh, sự thật phơi bày, thức tỉnh.", "reversed": "Tránh được tai họa, trì hoãn điều không thể tránh, sợ khủng hoảng."},
    "XVII. The Star (Ngôi Sao)": {"upright": "Hy vọng, niềm tin, tái tạo năng lượng, thanh thản, tương lai tươi sáng.", "reversed": "Mất niềm tin, thất vọng, bi quan, thiếu cảm hứng."},
    "XVIII. The Moon (Mặt Trăng)": {"upright": "Ảo ảnh, sợ hãi, lo âu, trực giác, sự bất an, nhầm lẫn.", "reversed": "Sự thật sáng tỏ, vượt qua nỗi sợ, giải tỏa lo âu."},
    "XIX. The Sun (Mặt Trời)": {"upright": "Thành công, hạnh phúc, rực rỡ, sức sống, rõ ràng.", "reversed": "Thành công bị trì hoãn, thiếu nhiệt huyết, tự mãn quá mức."},
    "XX. Judgement (Phán Xét)": {"upright": "Thức tỉnh, tiếng gọi lương tri, tha thứ, quyết định quan trọng.", "reversed": "Nghi ngờ bản thân, đổ lỗi, trốn tránh quyết định."},
    "XXI. The World (Thế Giới)": {"upright": "Hoàn thành, trọn vẹn, thành tựu, tự do, kết thúc mỹ mãn.", "reversed": "Chưa hoàn tất, thiếu kiên nhẫn, mục tiêu dang dở."},

    # Bộ Gậy (Wands)
    "Ace of Wands": {"upright": "Cơ hội mới, cảm hứng dồi dào, đam mê bùng cháy.", "reversed": "Trì hoãn khởi đầu, thiếu động lực, lãng phí ý tưởng."},
    "Two of Wands": {"upright": "Lên kế hoạch, định hướng tương lai, đưa ra lựa chọn.", "reversed": "Thiếu chuẩn bị, sợ hãi bước ra vùng an toàn."},
    "Three of Wands": {"upright": "Mở rộng tầm nhìn, chờ đợi thành quả, thám hiểm.", "reversed": "Thất vọng, dự án bị đình trệ, tầm nhìn ngắn hạn."},
    "Four of Wands": {"upright": "Chúc mừng, gia đình hòa thuận, sự ổn định, tiệc tùng.", "reversed": "Bất ổn trong nhà, rạn nứt nhỏ, niềm vui chưa trọn vẹn."},
    "Five of Wands": {"upright": "Cạnh tranh, xung đột, bất đồng ý kiến, tranh đấu.", "reversed": "Hòa giải, né tránh xung đột, kết thúc tranh chấp."},
    "Six of Wands": {"upright": "Chiến thắng, được công nhận, vinh quang, tự tin.", "reversed": "Thiếu tự tin, thất bại tạm thời, bị ngó lơ."},
    "Seven of Wands": {"upright": "Phòng thủ, kiên định bảo vệ lập trường, đối đầu thử thách.", "reversed": "Kiệt sức, bỏ cuộc, bị áp đảo bởi áp lực."},
    "Eight of Wands": {"upright": "Tốc độ nhanh, tin tức tới tấp, chuyển động, tiến triển.", "reversed": "Trì trệ, hấp tấp dẫn đến sai lầm, giao tiếp tắc nghẽn."},
    "Nine of Wands": {"upright": "Kiên trì, kiên cường phòng thủ, mệt mỏi nhưng không bỏ cuộc.", "reversed": "Kiệt sức hoàn toàn, hoang tưởng, buông xuôi vũ khí."},
    "Ten of Wands": {"upright": "Gánh nặng, áp lực quá tải, trách nhiệm đè nặng.", "reversed": "Buông bớt gánh nặng, chia sẻ công việc, sụp đổ vì kiệt sức."},
    "Page of Wands": {"upright": "Tin tức tích cực, sự khám phá, nhiệt huyết tuổi trẻ.", "reversed": "Thiếu kiên nhẫn, tin đồn thất thiệt, lười biếng."},
    "Knight of Wands": {"upright": "Hành động mãnh liệt, phiêu lưu, dũng cảm, bốc đồng.", "reversed": "Nóng nảy, hung hăng, cả thèm chóng chán, gây rắc rối."},
    "Queen of Wands": {"upright": "Tự tin, quyến rũ, quảng giao, độc lập, ấm áp.", "reversed": "Ghen tị, thao túng, nóng nảy, tự ti thầm kín."},
    "King of Wands": {"upright": "Nhà lãnh đạo, tầm nhìn lớn, bản lĩnh, kinh doanh giỏi.", "reversed": "Độc tài, bốc đồng, kỳ vọng quá cao, ích kỷ."},

    # Bộ Cốc (Cups)
    "Ace of Cups": {"upright": "Tình yêu mới, cảm xúc dâng trào, trực giác nhạy bén.", "reversed": "Cảm xúc dồn nén, thất tình, trống rỗng."},
    "Two of Cups": {"upright": "Kết nối, tình cảm đôi lứa, đối tác ăn ý, hòa hợp.", "reversed": "Bất hòa, rạn nứt tình cảm, mất cân bằng quan hệ."},
    "Three of Cups": {"upright": "Tình bạn, tụ tập, ăn mừng, chia sẻ niềm vui.", "reversed": "Người thứ ba, tiệc tùng quá đà, cô lập khỏi nhóm."},
    "Four of Cups": {"upright": "Chán nản, thờ ơ, bỏ lỡ cơ hội, trầm ngâm.", "reversed": "Thức tỉnh, mở lòng đón nhận cơ hội mới, năng động lại."},
    "Five of Cups": {"upright": "Nuối tiếc, đau khổ vì mất mát, tập trung vào điều tiêu cực.", "reversed": "Vượt qua nỗi đau, chấp nhận thực tại, mở ra trang mới."},
    "Six of Cups": {"upright": "Hoài niệm, ký ức tuổi thơ, sự ngây thơ, gặp lại người cũ.", "reversed": "Mắc kẹt trong quá khứ, không chịu trưởng thành."},
    "Seven of Cups": {"upright": "Nhiều lựa chọn, mơ mộng, ảo tưởng, thiếu thực tế.", "reversed": "Nhìn rõ sự thật, đưa ra quyết định thực tế, dứt khoát."},
    "Eight of Cups": {"upright": "Buông bỏ, quay lưng ra đi, tìm kiếm giá trị cao hơn.", "reversed": "Do dự không dám từ bỏ, níu kéo mù quáng."},
    "Nine of Cups": {"upright": "Ước nguyện thành sự thật, mãn nguyện, tự hào, sung sướng.", "reversed": "Tham lam, sự thỏa mãn hời hợt, thất vọng về vật chất."},
    "Ten of Cups": {"upright": "Hạnh phúc viên mãn, gia đình ấm êm, tình yêu trọn vẹn.", "reversed": "Gia đình lục đục, giá trị đảo lộn, xa cách người thân."},
    "Page of Cups": {"upright": "Tin nhắn tình cảm, sáng tạo, thông điệp trực giác.", "reversed": "Cảm xúc thất thường, trẻ con, tin buồn, block nhau."},
    "Knight of Cups": {"upright": "Lãng mạn, lời mời gọi tình cảm, theo đuổi đam mê.", "reversed": "Thất hứa, giả tạo, ảo tưởng tình yêu, lăng nhăng."},
    "Queen of Cups": {"upright": "Giàu tình cảm, thấu cảm, người mẹ hiền, trực giác tốt.", "reversed": "Thao túng cảm xúc, quá nhạy cảm, ghen tuông vô cớ."},
    "King of Cups": {"upright": "Kiểm soát cảm xúc giỏi, thông thái, điềm tĩnh, bao dung.", "reversed": "Lạnh lùng, bạo lực lạnh, giả tạo cảm xúc."},

    # Bộ Kiếm (Swords)
    "Ace of Swords": {"upright": "Ý tưởng đột phá, sự thật, tư duy sắc bén, chiến thắng.", "reversed": "Nhầm lẫn, phán đoán sai, giao tiếp thất bại."},
    "Two of Swords": {"upright": "Tiến thoái lưỡng nan, bế tắc, né tránh quyết định.", "reversed": "Mông lung, buộc phải chọn, sự thật đau lòng phơi bày."},
    "Three of Swords": {"upright": "Tổn thương, đau lòng, chia tay, thất vọng tràn trề.", "reversed": "Chữa lành tổn thương, tha thứ, giải phóng u uất."},
    "Four of Swords": {"upright": "Nghỉ ngơi, hồi phục, thiền định, rút lui tạm thời.", "reversed": "Kiệt sức vì cố quá, trở lại hành động sau dưỡng thương."},
    "Five of Swords": {"upright": "Chiến thắng bằng mọi giá, xung đột, ích kỷ, tư thù.", "reversed": "Buông bỏ tranh cãi, muốn hòa giải, hối hận."},
    "Six of Swords": {"upright": "Vượt qua giai đoạn khó khăn, chuyển chỗ, tìm sự bình yên.", "reversed": "Mắc kẹt trong rắc rối, kháng cự thay đổi."},
    "Seven of Swords": {"upright": "Lén lút, dối trá, chiến thuật ngầm, trốn tránh trách nhiệm.", "reversed": "Lời nói dối bị bóc trần, tự kiểm điểm, thú nhận."},
    "Eight of Swords": {"upright": "Bị trói buộc, bất lực tự ti, suy nghĩ tiêu cực tự huyễn.", "reversed": "Tự cởi trói, tìm thấy lối thoát, tư duy thoáng hơn."},
    "Nine of Swords": {"upright": "Lo âu quá độ, mất ngủ, trầm cảm, ác mộng, stress.", "reversed": "Vượt qua khủng hoảng, giải tỏa áp lực tâm lý."},
    "Ten of Swords": {"upright": "Chạm đáy nỗi đau, thất bại hoàn toàn, sự kết thúc đau đớn.", "reversed": "Hồi sinh từ đống đổ nát, bắt đầu lại từ số 0."},
    "Page of Swords": {"upright": "Tò mò, dò xét, học hỏi nhanh, nhiều năng lượng trí tuệ.", "reversed": "Nói suông, thọc mạch, phao tin đồn, trẻ con."},
    "Knight of Swords": {"upright": "Lao về phía trước, thẳng thắn, sắc bén, hành động nhanh.", "reversed": "Hấp tấp, hung hăng, thiếu suy nghĩ gây họa."},
    "Queen of Swords": {"upright": "Sắc sảo, độc lập, lý trí, thẳng thắn, rạch ròi.", "reversed": "Lạnh lùng, độc miệng, định kiến, thù dai."},
    "King of Swords": {"upright": "Thẩm phán, tư duy logic cao, chân lý, kỷ luật, uy quyền.", "reversed": "Tàn nhẫn, thao túng luật lệ, ích kỷ, độc đoán."},

    # Bộ Tiền (Pentacles)
    "Ace of Pentacles": {"upright": "Cơ hội tài chính, tài lộc, khởi đầu thực tế, may mắn tiền bạc.", "reversed": "Bỏ lỡ cơ hội đầu tư, hao tài tốn của, tính toán sai."},
    "Two of Pentacles": {"upright": "Cân bằng tài chính, xoay xở nhiều việc, linh hoạt.", "reversed": "Mất cân bằng, ôm đồm quá nhiều việc dẫn đến đổ bể."},
    "Three of Pentacles": {"upright": "Hợp tác đội nhóm, kỹ năng tốt, xây dựng nền tảng.", "reversed": "Làm việc nhóm kém, thiếu liên kết, chuyên môn yếu."},
    "Four of Pentacles": {"upright": "Giữ của, tiết kiệm, an toàn tài chính, bảo thủ.", "reversed": "Hoang phí tiền bạc hoặc quá keo kiệt gây mất lòng."},
    "Five of Pentacles": {"upright": "Nghèo khó, cô độc, khủng hoảng tài chính, thiếu thốn.", "reversed": "Vượt qua khó khăn tiền bạc, tìm thấy sự giúp đỡ."},
    "Six of Pentacles": {"upright": "Hào phóng, từ thiện, chia sẻ lợi ích, cho và nhận.", "reversed": "Lợi dụng lòng tốt, bất công tài chính, mắc nợ."},
    "Seven of Pentacles": {"upright": "Kiên nhẫn chờ đợi kết quả, đánh giá lại thành quả lao động.", "reversed": "Thiếu kiên nhẫn, đầu tư sai chỗ, nỗ lực đổ sông đổ biển."},
    "Eight of Pentacles": {"upright": "Chăm chỉ, rèn luyện kỹ năng, tập trung cao độ vào chuyên môn.", "reversed": "Thiếu định hướng công việc, lười biếng, làm ẩu."},
    "Nine of Pentacles": {"upright": "Độc lập tài chính, tự do, hưởng thụ thành quả, sang chảnh.", "reversed": "Lệ thuộc tài chính, vẻ ngoài hào nhoáng nhưng rỗng tuếch."},
    "Ten of Pentacles": {"upright": "Giàu có, gia tộc, thừa kế vinh hoa, sự nghiệp vững chắc.", "reversed": "Tranh chấp tài sản, rạn nứt gia đình, thất bại tài chính."},
    "Page of Pentacles": {"upright": "Tin tức công việc mới, học tập, kế hoạch kiếm tiền thực tế.", "reversed": "Trì trệ, thiếu thực tế, lười học, tầm nhìn hạn hẹp."},
    "Knight of Pentacles": {"upright": "Cần mẫn, đáng tin cậy, tiến chậm nhưng chắc, thực tế.", "reversed": "Chây ì, cứng nhắc, nhàm chán, sợ thay đổi."},
    "Queen of Pentacles": {"upright": "Thực tế, quản lý tài chính tốt, chăm sóc nhà cửa, sung túc.", "reversed": "Mất cân bằng cuộc sống, quá thực dụng, bỏ bê bản thân."},
    "King of Pentacles": {"upright": "Doanh nhân thành đạt, vương quốc tài chính, bảo chứng an toàn.", "reversed": "Tham nhũng, thực dụng mù quáng, đầu cơ thất bại."}
}
