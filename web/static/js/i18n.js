

(function () {
  'use strict';

  const LANG_STORAGE_KEY = 'sakura_web_lang';

  const LANGUAGES = {
    vi: { name: 'Tiếng Việt', native: 'Tiếng Việt', flag: '🇻🇳', code: 'VI' },
    en: { name: 'English', native: 'English', flag: '🇬🇧', code: 'EN' },
    ja: { name: '日本語', native: '日本語', flag: '🇯🇵', code: 'JA' },
    cn: { name: 'Chinese', native: '中文', flag: '🇨🇳', code: 'CN' }
  };

  
  const PHRASES = {
  "Sakura Bot": {
    "en": "Sakura Bot",
    "ja": "Sakura Bot",
    "cn": "樱花机器人"
  },
  "Bản Chính Thức": {
    "en": "Official Version",
    "ja": "正式版",
    "cn": "正式版"
  },
  "Tính năng": {
    "en": "Features",
    "ja": "特長",
    "cn": "特点"
  },
  "Mời Bot": {
    "en": "Invite Bots",
    "ja": "ボットを招待する",
    "cn": "邀请机器人"
  },
  "Minecraft": {
    "en": "Minecraft",
    "ja": "マインクラフト",
    "cn": "我的世界"
  },
  "Tất Cả Máy Chủ": {
    "en": "All Servers",
    "ja": "すべてのサーバー",
    "cn": "所有服务器"
  },
  "Bảng Console": {
    "en": "Console panel",
    "ja": "コンソールパネル",
    "cn": "控制台面板"
  },
  "Quản Lý Tệp": {
    "en": "File Management",
    "ja": "ファイル管理",
    "cn": "文件管理"
  },
  "Cấu Hình Server": {
    "en": "Server Configuration",
    "ja": "サーバー構成",
    "cn": "服务器配置"
  },
  "Soi Kho Đồ Player": {
    "en": "Check Player Inventory",
    "ja": "プレーヤーのインベントリを確認する",
    "cn": "检查玩家库存"
  },
  "Phân Quyền Hosting": {
    "en": "Decentralized Hosting",
    "ja": "分散型ホスティング",
    "cn": "去中心化托管"
  },
  "Kho Plugin Server": {
    "en": "Server Plugins",
    "ja": "プラグイン一覧",
    "cn": "插件服务器存储库"
  },
  "Tiện Ích": {
    "en": "Utilities",
    "ja": "ユーティリティ",
    "cn": "公用事业"
  },
  "Tải Video TikTok": {
    "en": "Download TikTok Videos",
    "ja": "TikTok動画をダウンロードする",
    "cn": "下载 TikTok 视频"
  },
  "Tải TikTok": {
    "en": "Download TikTok",
    "ja": "TikTokをダウンロード",
    "cn": "下载抖音"
  },
  "Thư Viện Ảnh": {
    "en": "Photo Library",
    "ja": "フォトライブラリー",
    "cn": "照片库"
  },
  "Minigames & Giải Trí": {
    "en": "Minigames & Entertainment",
    "ja": "ミニゲームとエンターテイメント",
    "cn": "迷你游戏和娱乐"
  },
  "Minigames": {
    "en": "Minigames",
    "ja": "ミニゲーム",
    "cn": "小游戏"
  },
  "Hồ Sơ Sakura Bio": {
    "en": "Sakura Bio Profile",
    "ja": "さくらプロフィール",
    "cn": "樱花生物简介"
  },
  "Hướng dẫn": {
    "en": "Instructions",
    "ja": "指示",
    "cn": "使用说明"
  },
  "Hỗ trợ": {
    "en": "Support",
    "ja": "サポート",
    "cn": "支持"
  },
  "Đăng nhập": {
    "en": "Sign in",
    "ja": "サインイン",
    "cn": "登录"
  },
  "Đăng xuất": {
    "en": "Sign out",
    "ja": "サインアウト",
    "cn": "退出"
  },
  "Dashboard": {
    "en": "Dashboard",
    "ja": "ダッシュボード",
    "cn": "仪表板"
  },
  "Trang chủ": {
    "en": "Home page",
    "ja": "ホームページ",
    "cn": "主页"
  },
  "Trang Chủ": {
    "en": "Home page",
    "ja": "ホームページ",
    "cn": "主页"
  },
  "Xem Video": {
    "en": "Watch Video",
    "ja": "動画を見る",
    "cn": "观看视频"
  },
  "Chế độ rạp": {
    "en": "Theater Mode",
    "ja": "シアターモード",
    "cn": "剧场模式"
  },
  "Rạp chiếu": {
    "en": "Theater",
    "ja": "シアター",
    "cn": "电影院"
  },
  "Lưu": {
    "en": "Save",
    "ja": "保存",
    "cn": "保存"
  },
  "Đổi giao diện": {
    "en": "Toggle theme",
    "ja": "テーマ切替",
    "cn": "更改界面"
  },
  "Đổi ngôn ngữ": {
    "en": "Change language",
    "ja": "言語切替",
    "cn": "更改语言"
  },
  "Tổng Quan": {
    "en": "Overview",
    "ja": "概要",
    "cn": "概述"
  },
  "Lệnh Bot": {
    "en": "Bot Commands",
    "ja": "ボットコマンド",
    "cn": "机器人命令"
  },
  "Quản Lý Server": {
    "en": "Server Manager",
    "ja": "サーバー管理",
    "cn": "服务器管理"
  },
  "Cài Đặt": {
    "en": "Settings",
    "ja": "設定",
    "cn": "设置"
  },
  "Tài Khoản": {
    "en": "Account",
    "ja": "アカウント",
    "cn": "账户"
  },
  "Nhật Ký": {
    "en": "Logs",
    "ja": "ログ",
    "cn": "日记"
  },
  "Cấu Hình Bot": {
    "en": "Bot Configuration",
    "ja": "ボット構成",
    "cn": "机器人配置"
  },
  "Thống Kê Hệ Thống": {
    "en": "System Statistics",
    "ja": "システム統計",
    "cn": "系统统计"
  },
  "Kinh Tế & RPG": {
    "en": "Economy & RPG",
    "ja": "経済・RPG",
    "cn": "经济与角色扮演"
  },
  "Thủy Cung & Câu Cá": {
    "en": "Aquarium & Fishing",
    "ja": "水族館・釣り",
    "cn": "水族馆和钓鱼"
  },
  "Thủy Cung": {
    "en": "Aquarium",
    "ja": "水族館",
    "cn": "水族馆"
  },
  "Đào Khoáng & Hầm Mỏ": {
    "en": "Mining & Caves",
    "ja": "採掘・鉱山",
    "cn": "采矿业"
  },
  "Hầm Mỏ": {
    "en": "Mining",
    "ja": "採掘",
    "cn": "我的"
  },
  "Nông Trại & Thú Cưng": {
    "en": "Farming & Pets",
    "ja": "農場・ペット",
    "cn": "农场与宠物"
  },
  "Nông Trại": {
    "en": "Farming",
    "ja": "農業",
    "cn": "农场"
  },
  "Casino & Game": {
    "en": "Casino & Games",
    "ja": "カジノ・ゲーム",
    "cn": "赌场与游戏"
  },
  "Sòng Bạc": {
    "en": "Casino",
    "ja": "カジノ",
    "cn": "赌场"
  },
  "Âm Nhạc Lavalink": {
    "en": "Lavalink Music",
    "ja": "音楽ストリーミング",
    "cn": "拉瓦林克音乐"
  },
  "Âm Nhạc": {
    "en": "Music",
    "ja": "音楽",
    "cn": "音乐"
  },
  "Global Chat": {
    "en": "Global Chat",
    "ja": "グローバルチャット",
    "cn": "全球聊天"
  },
  "Games": {
    "en": "Games",
    "ja": "ゲーム",
    "cn": "游戏"
  },
  "Quản Trị Tệp Tin": {
    "en": "Bot File Manager",
    "ja": "ファイル管理",
    "cn": "文件管理"
  },
  "Quản Trị Tệp": {
    "en": "Bot Files",
    "ja": "ボットファイル",
    "cn": "文件管理"
  },
  "Góc Nhìn User": {
    "en": "User View",
    "ja": "ユーザー視点",
    "cn": "用户视角"
  },
  "Quay Lại Góc Nhìn Admin": {
    "en": "Return to Admin View",
    "ja": "管理者視点に戻る",
    "cn": "返回管理员视角"
  },
  "Nạp Lại Cogs": {
    "en": "Reload Cogs",
    "ja": "Cogs再読込",
    "cn": "重新加载齿轮"
  },
  "Đồng Bộ Slash": {
    "en": "Sync Slash",
    "ja": "スラッシュ同期",
    "cn": "斜线同步"
  },
  "Gateway Ping:": {
    "en": "Gateway Ping:",
    "ja": "応答速度:",
    "cn": "网关 Ping："
  },
  "Uptime:": {
    "en": "Uptime:",
    "ja": "稼働時間:",
    "cn": "正常运行时间："
  },
  "Trạng Thái Bot": {
    "en": "Bot Status",
    "ja": "ボット状態",
    "cn": "机器人状态"
  },
  "Đang Hoạt Động": {
    "en": "Active",
    "ja": "アクティブ",
    "cn": "活跃"
  },
  "Ngoại Tuyến": {
    "en": "Offline",
    "ja": "オフライン",
    "cn": "离线"
  },
  "Thời Gian Hoạt Động": {
    "en": "Active Uptime",
    "ja": "連続稼働時間",
    "cn": "工作时间"
  },
  "Độ Trễ": {
    "en": "Latency",
    "ja": "レイテンシ",
    "cn": "延迟"
  },
  "Độ Trễ WebSocket": {
    "en": "WebSocket Latency",
    "ja": "WebSocket遅延",
    "cn": "WebSocket 延迟"
  },
  "Tổng Số Máy Chủ": {
    "en": "Total Number of Servers",
    "ja": "サーバーの総数",
    "cn": "服务器总数"
  },
  "Máy chủ tin dùng": {
    "en": "Trusted Servers",
    "ja": "参加サーバー数",
    "cn": "可信服务器"
  },
  "Tổng Người Dùng": {
    "en": "Total Users",
    "ja": "ユーザー総数",
    "cn": "用户总数"
  },
  "Người dùng phục vụ": {
    "en": "Users Served",
    "ja": "利用ユーザー数",
    "cn": "服务用户"
  },
  "Số Kênh": {
    "en": "Channels",
    "ja": "チャンネル数",
    "cn": "通道数"
  },
  "Số Lệnh Đã Xử Lý": {
    "en": "Commands Processed",
    "ja": "処理コマンド数",
    "cn": "处理的订单数量"
  },
  "Lệnh đã xử lý": {
    "en": "Commands Processed",
    "ja": "処理コマンド数",
    "cn": "订单已处理"
  },
  "Bộ Nhớ RAM": {
    "en": "RAM Usage",
    "ja": "メモリ使用量",
    "cn": "内存"
  },
  "Sử Dụng RAM": {
    "en": "RAM Usage",
    "ja": "メモリ使用量",
    "cn": "内存使用情况"
  },
  "Tải CPU": {
    "en": "CPU Usage",
    "ja": "CPU使用率",
    "cn": "CPU负载"
  },
  "Tải CPU:": {
    "en": "CPU Usage:",
    "ja": "CPU使用率:",
    "cn": "CPU负载："
  },
  "Thư Viện Cogs": {
    "en": "Loaded Cogs",
    "ja": "読み込み済みCogs",
    "cn": "齿轮库"
  },
  "Tự Động Làm Mới": {
    "en": "Auto Refresh",
    "ja": "自動更新",
    "cn": "自动刷新"
  },
  "Làm Mới": {
    "en": "Refresh",
    "ja": "リフレッシュ",
    "cn": "刷新"
  },
  "Làm Mới Dữ Liệu": {
    "en": "Refresh Data",
    "ja": "データを更新する",
    "cn": "刷新数据"
  },
  "Lưu Thay Đổi": {
    "en": "Save Changes",
    "ja": "変更を保存",
    "cn": "保存更改"
  },
  "Lưu Cài Đặt": {
    "en": "Save Settings",
    "ja": "設定の保存",
    "cn": "保存设置"
  },
  "Hủy Bỏ": {
    "en": "Cancel Cancel",
    "ja": "キャンセル キャンセル",
    "cn": "取消 取消"
  },
  "Hủy": {
    "en": "Cancel",
    "ja": "キャンセル",
    "cn": "取消"
  },
  "Xác Nhận": {
    "en": "Confirm",
    "ja": "確認",
    "cn": "确认"
  },
  "Đóng": {
    "en": "Close",
    "ja": "閉じる",
    "cn": "关闭"
  },
  "Bật": {
    "en": "Turn on",
    "ja": "オンにする",
    "cn": "打开"
  },
  "Tắt": {
    "en": "Turn off",
    "ja": "オフにする",
    "cn": "关闭"
  },
  "ĐÃ BẬT": {
    "en": "ENABLED",
    "ja": "有効",
    "cn": "启用"
  },
  "ĐÃ TẮT": {
    "en": "DISABLED",
    "ja": "無効",
    "cn": "禁用"
  },
  "Tìm kiếm...": {
    "en": "Search...",
    "ja": "検索...",
    "cn": "搜索..."
  },
  "Tìm kiếm": {
    "en": "Search",
    "ja": "検索",
    "cn": "搜索"
  },
  "Tìm kiếm lệnh bot...": {
    "en": "Search bot commands...",
    "ja": "コマンドを検索...",
    "cn": "搜索机器人命令..."
  },
  "Tất cả danh mục": {
    "en": "All Categories",
    "ja": "全カテゴリ",
    "cn": "所有类别"
  },
  "Hành động": {
    "en": "Action",
    "ja": "アクション",
    "cn": "行动"
  },
  "Chỉnh sửa": {
    "en": "Edit",
    "ja": "編集",
    "cn": "编辑"
  },
  "Xóa": {
    "en": "Delete",
    "ja": "削除",
    "cn": "删除"
  },
  "Tải lên": {
    "en": "Upload",
    "ja": "アップロード",
    "cn": "上传"
  },
  "Tải xuống": {
    "en": "Download",
    "ja": "ダウンロード",
    "cn": "下载"
  },
  "Tải Về": {
    "en": "Download",
    "ja": "ダウンロード",
    "cn": "下载"
  },
  "Sao chép": {
    "en": "Copy",
    "ja": "コピー",
    "cn": "复制"
  },
  "Đã sao chép!": {
    "en": "Copied!",
    "ja": "コピー完了！",
    "cn": "复制了！"
  },
  "Quay lại": {
    "en": "Back",
    "ja": "戻る",
    "cn": "回来吧"
  },
  "Tiếp theo": {
    "en": "Next",
    "ja": "次へ",
    "cn": "下一步"
  },
  "Trước": {
    "en": "Previous",
    "ja": "前へ",
    "cn": "之前"
  },
  "Áp dụng": {
    "en": "Apply",
    "ja": "適用",
    "cn": "申请"
  },
  "Khởi động lại": {
    "en": "Restart",
    "ja": "再起動",
    "cn": "重新启动"
  },
  "Sakura TikTok": {
    "en": "Sakura TikTok",
    "ja": "Sakura TikTok",
    "cn": "樱花TikTok"
  },
  "Trình Tải Video & Album Ảnh Không Logo": {
    "en": "No-Watermark Video & Photo Album Downloader",
    "ja": "透かしなし動画・アルバムダウンローダー",
    "cn": "无徽标视频和相册下载器"
  },
  "Trình Tải TikTok & Douyin Đa Năng": {
    "en": "Universal TikTok & Douyin Downloader",
    "ja": "万能TikTok・Douyinダウンローダー",
    "cn": "多功能 TikTok 和抖音下载器"
  },
  "Xem Trước & Tải Video TikTok Không Logo": {
    "en": "Preview & Download TikTok Videos (No Watermark)",
    "ja": "透かしなしTikTok動画プレビュー＆保存",
    "cn": "预览和下载没有徽标的 TikTok 视频"
  },
  "Dán link TikTok (vd: https://vt.tiktok.com/... hoặc https://www.tiktok.com/@.../video/...)": {
    "en": "Paste TikTok link (e.g. https://vt.tiktok.com/... or https://www.tiktok.com/@.../video/...)",
    "ja": "TikTokリンクを貼り付け (例: https://vt.tiktok.com/...)",
    "cn": "粘贴 TikTok 链接（例如：https://vt.tiktok.com/... 或 https://www.tiktok.com/@.../video/...）"
  },
  "Dán": {
    "en": "Paste",
    "ja": "貼り付け",
    "cn": "粘贴"
  },
  "Xem Trước & Tải": {
    "en": "Preview & Download",
    "ja": "プレビュー＆保存",
    "cn": "预览及下载"
  },
  "Đang Xử Lý...": {
    "en": "Processing...",
    "ja": "処理中...",
    "cn": "处理中..."
  },
  "Đang phân tích bài viết TikTok...": {
    "en": "Analyzing TikTok post...",
    "ja": "TikTok投稿を解析中...",
    "cn": "正在分析 TikTok 帖子..."
  },
  "Đang trích xuất luồng video chất lượng cao & dữ liệu album...": {
    "en": "Extracting high quality video stream and album data...",
    "ja": "高画質動画ストリームとアルバムデータを抽出中...",
    "cn": "提取高质量视频流和专辑数据..."
  },
  "TÙY CHỌN CHẤT LƯỢNG & TẢI XUỐNG": {
    "en": "QUALITY & DOWNLOAD OPTIONS",
    "ja": "画質選択・ダウンロード",
    "cn": "质量和下载选项"
  },
  "Tải Video HD (Không Logo)": {
    "en": "Download HD Video (No Watermark)",
    "ja": "HD動画ダウンロード (ロゴなし)",
    "cn": "下载高清视频（无徽标）"
  },
  "Tải Thường SD (Không Logo)": {
    "en": "Download SD Video (No Watermark)",
    "ja": "通常SD動画 (ロゴなし)",
    "cn": "下载普通 SD（无徽标）"
  },
  "Tải Có Logo (Watermark)": {
    "en": "Download With Watermark",
    "ja": "ウォーターマーク付き保存",
    "cn": "下载带有徽标（水印）"
  },
  "Tải Âm Thanh MP3": {
    "en": "Download MP3 Audio",
    "ja": "MP3音声をダウンロード",
    "cn": "下载音频 MP3"
  },
  "TÙY CHỌN TẢI ALBUM ẢNH": {
    "en": "PHOTO ALBUM DOWNLOAD OPTIONS",
    "ja": "アルバム写真ダウンロード",
    "cn": "可选下载相册"
  },
  "Tải Ảnh Đang Xem": {
    "en": "Download Current Photo",
    "ja": "表示中の写真を保存",
    "cn": "下载当前正在查看的图像"
  },
  "Tải Toàn Bộ Ảnh (.ZIP)": {
    "en": "Download All Photos (.ZIP)",
    "ja": "全写真の一括保存 (.ZIP)",
    "cn": "下载所有图像 (.ZIP)"
  },
  "Tải Nhạc Nền MP3": {
    "en": "Download Background MP3",
    "ja": "BGM音声をダウンロード",
    "cn": "下载 MP3 背景音乐"
  },
  "Dùng phím ← và → để đổi ảnh": {
    "en": "Use ← and → arrow keys to switch photos",
    "ja": "矢印キー ← → で写真を切り替え",
    "cn": "使用 ← 和 → 键更改图像"
  },
  "Video HD Không Logo": {
    "en": "HD Video Without Logo",
    "ja": "ロゴなしの HD ビデオ",
    "cn": "高清视频无标志"
  },
  "Hỗ Trợ Album Slideshow": {
    "en": "Photo Slideshow Support",
    "ja": "スライドショー対応",
    "cn": "专辑幻灯片支持"
  },
  "Tách Nhạc Nền MP3": {
    "en": "Split MP3 Background Music",
    "ja": "MP3 BGM を分割",
    "cn": "分割 MP3 背景音乐"
  },
  "Bảng Điều Khiển Máy Chủ Minecraft": {
    "en": "Minecraft Server Control Panel",
    "ja": "Minecraftサーバー管理パネル",
    "cn": "我的世界服务器仪表板"
  },
  "Quản Lý Máy Chủ": {
    "en": "Server Manager",
    "ja": "サーバー管理",
    "cn": "服务器管理"
  },
  "Máy Chủ Minecraft": {
    "en": "Minecraft Servers",
    "ja": "Minecraftサーバー",
    "cn": "我的世界服务器"
  },
  "Khởi Động Server": {
    "en": "Start Server",
    "ja": "サーバー起動",
    "cn": "启动服务器"
  },
  "Khởi Động": {
    "en": "Start",
    "ja": "起動",
    "cn": "启动"
  },
  "Dừng Server": {
    "en": "Stop Server",
    "ja": "サーバー停止",
    "cn": "停止服务器"
  },
  "Dừng": {
    "en": "Stop",
    "ja": "停止",
    "cn": "停止"
  },
  "Khởi Động Lại Server": {
    "en": "Restart Server",
    "ja": "サーバー再起動",
    "cn": "重新启动服务器"
  },
  "Gửi Lệnh Console": {
    "en": "Send Console Command",
    "ja": "コンソールコマンド送信",
    "cn": "发送控制台命令"
  },
  "Gửi Lệnh": {
    "en": "Send Order",
    "ja": "注文の送信",
    "cn": "发送订单"
  },
  "Gửi": {
    "en": "Send",
    "ja": "送信",
    "cn": "发送"
  },
  "Nhập lệnh console...": {
    "en": "Enter console command...",
    "ja": "コマンドを入力...",
    "cn": "输入控制台命令..."
  },
  "Người Chơi Online": {
    "en": "Online Players",
    "ja": "オンラインプレイヤー",
    "cn": "在线玩家"
  },
  "Người Chơi Trực Tuyến": {
    "en": "Online Players",
    "ja": "オンラインプレイヤー",
    "cn": "在线玩家"
  },
  "Không có người chơi online": {
    "en": "No players online",
    "ja": "オンラインプレイヤーはいません",
    "cn": "没有在线玩家"
  },
  "Tạo Thư Mục": {
    "en": "New Folder",
    "ja": "新規フォルダ",
    "cn": "创建文件夹"
  },
  "Tạo Tệp": {
    "en": "New File",
    "ja": "新規ファイル",
    "cn": "创建文件"
  },
  "Tải Lên Tệp": {
    "en": "Upload File",
    "ja": "ファイルアップロード",
    "cn": "上传文件"
  },
  "Đổi Tên": {
    "en": "Rename",
    "ja": "名前変更",
    "cn": "更改姓名"
  },
  "Tên Tệp": {
    "en": "File Name",
    "ja": "ファイル名",
    "cn": "文件名"
  },
  "Kích Thước": {
    "en": "Size",
    "ja": "サイズ",
    "cn": "尺寸"
  },
  "Ngày Sửa Đổi": {
    "en": "Date Modified",
    "ja": "変更日",
    "cn": "修改日期"
  },
  "Đăng Nhập": {
    "en": "Login",
    "ja": "ログイン",
    "cn": "登录"
  },
  "Đăng Ký": {
    "en": "Register",
    "ja": "アカウント登録",
    "cn": "注册"
  },
  "Đăng nhập tài khoản": {
    "en": "Account Login",
    "ja": "アカウントログイン",
    "cn": "登录您的帐户"
  },
  "Đăng ký tài khoản": {
    "en": "Create an Account",
    "ja": "新規アカウント登録",
    "cn": "注册账户"
  },
  "Chào mừng bạn trở lại!": {
    "en": "Welcome back!",
    "ja": "おかえりなさい！",
    "cn": "欢迎回来！"
  },
  "Tên đăng nhập": {
    "en": "Username",
    "ja": "ユーザー名",
    "cn": "登录名"
  },
  "Tên đăng nhập...": {
    "en": "Enter username...",
    "ja": "ユーザー名を入力...",
    "cn": "用户名..."
  },
  "Mật khẩu": {
    "en": "Password",
    "ja": "パスワード",
    "cn": "密码"
  },
  "Mật khẩu...": {
    "en": "Enter password...",
    "ja": "パスワードを入力...",
    "cn": "密码..."
  },
  "Nhập lại mật khẩu": {
    "en": "Confirm Password",
    "ja": "パスワード再入力",
    "cn": "重新输入密码"
  },
  "Xác nhận mật khẩu": {
    "en": "Confirm Password",
    "ja": "パスワード確認",
    "cn": "确认密码"
  },
  "Quên mật khẩu?": {
    "en": "Forgot password?",
    "ja": "パスワードをお忘れですか？",
    "cn": "忘记密码？"
  },
  "Đăng nhập bằng Discord": {
    "en": "Login with Discord",
    "ja": "Discordでログイン",
    "cn": "使用 Discord 登录"
  },
  "Chưa có tài khoản?": {
    "en": "Don't have an account?",
    "ja": "アカウントをお持ちでないですか？",
    "cn": "还没有帐户？"
  },
  "Đã có tài khoản?": {
    "en": "Already have an account?",
    "ja": "すでにアカウントをお持ちですか？",
    "cn": "已经有帐户？"
  },
  "Thông Tin Tài Khoản": {
    "en": "Account Information",
    "ja": "アカウント情報",
    "cn": "账户信息"
  },
  "Đổi Mật Khẩu": {
    "en": "Change Password",
    "ja": "パスワード変更",
    "cn": "更改密码"
  },
  "Mật khẩu hiện tại": {
    "en": "Current Password",
    "ja": "現在のパスワード",
    "cn": "当前密码"
  },
  "Mật khẩu mới": {
    "en": "New Password",
    "ja": "新しいパスワード",
    "cn": "新密码"
  },
  "Xác nhận mật khẩu mới": {
    "en": "Confirm New Password",
    "ja": "新しいパスワードの確認",
    "cn": "确认新密码"
  },
  "Cập nhật mật khẩu": {
    "en": "Update Password",
    "ja": "パスワード更新",
    "cn": "更新密码"
  },
  "Liên Kết Discord": {
    "en": "Discord Integration",
    "ja": "Discord連携",
    "cn": "不和谐链接"
  },
  "Đã liên kết": {
    "en": "Linked",
    "ja": "連携済み",
    "cn": "链接"
  },
  "Chưa liên kết": {
    "en": "Not linked yet",
    "ja": "まだリンクされていません",
    "cn": "尚未链接"
  },
  "Trung Tâm Giải Trí & Minigames": {
    "en": "Minigames & Entertainment Hub",
    "ja": "ミニゲーム・娯楽ハブ",
    "cn": "娱乐中心和小游戏"
  },
  "Bảng Xếp Hạng": {
    "en": "Leaderboard",
    "ja": "ランキング",
    "cn": "排行榜"
  },
  "Chơi Ngay": {
    "en": "Play Now",
    "ja": "今すぐプレイ",
    "cn": "立即播放"
  },
  "Tạo Phòng": {
    "en": "Create Room",
    "ja": "ルーム作成",
    "cn": "创建房间"
  },
  "Tham Gia": {
    "en": "Join",
    "ja": "参加",
    "cn": "加入"
  },
  "Cờ Caro": {
    "en": "Gomoku (Tic-Tac-Toe)",
    "ja": "五目並べ",
    "cn": "方格旗"
  },
  "Cờ Vua": {
    "en": "Chess",
    "ja": "チェス",
    "cn": "国际象棋"
  },
  "Nối Chữ": {
    "en": "Word Chain",
    "ja": "しりとり",
    "cn": "连接字母"
  },
  "Vẽ Hình Đoán Chữ": {
    "en": "Draw Pictures and Guess the Words",
    "ja": "絵を描いて言葉を推測する",
    "cn": "画图猜单词"
  },
  "Bói Bài Tarot": {
    "en": "Tarot Card Fortune Telling",
    "ja": "タロットカード占い",
    "cn": "塔罗牌算命"
  },
  "Số trận thắng:": {
    "en": "Wins:",
    "ja": "勝利数:",
    "cn": "获胜次数："
  },
  "Điểm số:": {
    "en": "Score:",
    "ja": "スコア:",
    "cn": "分数："
  },
  "Chưa có dữ liệu": {
    "en": "No data available",
    "ja": "データなし",
    "cn": "还没有数据"
  },
  "Đang chờ đối thủ...": {
    "en": "Waiting for opponent...",
    "ja": "対戦相手を待っています...",
    "cn": "等待对手..."
  },
  "Quản Lý Tệp Tin Bot": {
    "en": "Bot File Manager",
    "ja": "ボットファイル管理",
    "cn": "机器人文件管理"
  },
  "Quản lý mã nguồn, cấu hình và cơ sở dữ liệu của Sakura Bot.": {
    "en": "Manage source code, configurations, and databases of Sakura Bot.",
    "ja": "Sakura Botのソースコード、設定、データベースを管理します。",
    "cn": "管理 Sakura Bot 的源代码、配置和数据库。"
  },
  "Tạo Tệp Mới": {
    "en": "New File",
    "ja": "新規ファイル",
    "cn": "创建新文件"
  },
  "Tạo Thư Mục Mới": {
    "en": "New Folder",
    "ja": "新規フォルダ",
    "cn": "创建新文件夹"
  },
  "Đồng Bộ Lệnh": {
    "en": "Command Synchronization",
    "ja": "コマンドの同期",
    "cn": "命令同步"
  },
  "Cơ Sở Dữ Liệu": {
    "en": "Database Viewer",
    "ja": "データベース閲覧",
    "cn": "数据库"
  },
  "Danh Bạ Hồ Sơ": {
    "en": "Profile Directory",
    "ja": "プロフィール名鑑",
    "cn": "简介目录"
  },
  "Danh Bạ Hồ Sơ Sakura Bio": {
    "en": "Sakura Bio Directory",
    "ja": "Sakura Bio プロフィール名鑑",
    "cn": "樱花简介目录"
  },
  "Tạo Hồ Sơ": {
    "en": "Create Profile",
    "ja": "プロフィール作成",
    "cn": "创建个人资料"
  },
  "Chỉnh Sửa Hồ Sơ": {
    "en": "Edit Profile",
    "ja": "プロフィール編集",
    "cn": "编辑个人资料"
  },
  "Giới thiệu bản thân": {
    "en": "About Me",
    "ja": "自己紹介",
    "cn": "自我介绍一下"
  },
  "Liên kết mạng xã hội": {
    "en": "Social Links",
    "ja": "ソーシャルリンク",
    "cn": "社交网络链接"
  },
  "Nâng Tầm Máy Chủ Với": {
    "en": "Supercharge Your Community With",
    "ja": "最高のコミュニティ体験を",
    "cn": "升级您的服务器"
  },
  "Hệ Thống Tính Năng Vượt Trội": {
    "en": "Outstanding Feature Suite",
    "ja": "圧倒的な機能一覧",
    "cn": "突出的功能系统"
  },
  "Thủy Cung & Câu Cá RPG": {
    "en": "Aquarium & Fishing RPG",
    "ja": "水族館＆釣りRPG",
    "cn": "水族馆和钓鱼角色扮演游戏"
  },
  "Nông Trại & Thú Nuôi": {
    "en": "Farming & Companion Pets",
    "ja": "農業＆ペット飼育",
    "cn": "农场与宠物"
  },
  "Âm Nhạc Cao Cấp": {
    "en": "Premium Music Engine",
    "ja": "プレミアム音楽再生",
    "cn": "优质音乐"
  },
  "Sòng Bạc & Mini-Games": {
    "en": "Casino & Mini-Games",
    "ja": "カジノ＆ミニゲーム",
    "cn": "赌场和迷你游戏"
  },
  "Hosting Minecraft Tự Động": {
    "en": "Automated Minecraft Hosting",
    "ja": "自動マイクラホスティング",
    "cn": "自动 Minecraft 托管"
  },
  "Bắt Đầu Thật Dễ Dàng": {
    "en": "Get Started Easily",
    "ja": "簡単3ステップ導入",
    "cn": "入门很简单"
  },
  "1. Mời Bot Vào Server": {
    "en": "1. Invite Bot to Server",
    "ja": "1. ボットをサーバーに招待",
    "cn": "1. 邀请机器人加入服务器"
  },
  "2. Khởi Tạo Cài Đặt": {
    "en": "2. Configure Settings",
    "ja": "2. 初期設定を行う",
    "cn": "2. 初始化设置"
  },
  "3. Thưởng Thức Trọn Vẹn": {
    "en": "3. Enjoy Community Fun",
    "ja": "3. コミュニティを楽しむ",
    "cn": "3. 尽情享受"
  },
  "Điều khoản dịch vụ": {
    "en": "Terms of Service",
    "ja": "利用規約",
    "cn": "服务条款"
  },
  "Chính sách bảo mật": {
    "en": "Privacy Policy",
    "ja": "プライバシーポリシー",
    "cn": "隐私政策"
  },
  "Máy chủ hỗ trợ": {
    "en": "Support Server",
    "ja": "サポートサーバー",
    "cn": "服务器支持"
  },
  "Tài liệu hướng dẫn": {
    "en": "Documentation",
    "ja": "ドキュメント",
    "cn": "说明书文件"
  },
  "Bản quyền © 2026 Sakura Bot. Bảo lưu mọi quyền.": {
    "en": "Copyright © 2026 Sakura Bot. All rights reserved.",
    "ja": "Copyright © 2026 Sakura Bot. All rights reserved.",
    "cn": "版权所有 © 2026 樱花机器人。版权所有。"
  },
  "Đang tải...": {
    "en": "Loading...",
    "ja": "読み込み中...",
    "cn": "正在加载..."
  },
  "Vui lòng chờ...": {
    "en": "Please wait...",
    "ja": "少々お待ちください...",
    "cn": "请稍等..."
  },
  "Thành công": {
    "en": "Success",
    "ja": "成功",
    "cn": "成功"
  },
  "Thất bại": {
    "en": "Failed",
    "ja": "失敗",
    "cn": "失败"
  },
  "Lỗi": {
    "en": "Error",
    "ja": "エラー",
    "cn": "错误"
  },
  "Cảnh báo": {
    "en": "Warning",
    "ja": "警告",
    "cn": "警告"
  },
  "Thông báo": {
    "en": "Notice",
    "ja": "お知らせ",
    "cn": "通知"
  },
  "Có": {
    "en": "Yes",
    "ja": "はい",
    "cn": "是的"
  },
  "Không": {
    "en": "No",
    "ja": "いいえ",
    "cn": "否"
  },
  "Tất cả": {
    "en": "All",
    "ja": "すべて",
    "cn": "全部"
  },
  "Sakura Bot được cung cấp trên nguyên tắc \"nguyên trạng\" (As-Is). Chúng tôi nỗ lực duy trì bot hoạt động ổn định 24/7 nhưng không chịu trách nhiệm cho bất kỳ tổn thất dữ liệu, thiệt hại máy chủ do người dùng tự cấu hình sai quyền hạn hoặc sự cố từ phía Discord.": {
    "en": "Sakura Bot is provided on an \"as-is\" basis. We strive to keep the bot running stably 24/7 but are not liable for any data loss or server damage caused by user misconfiguration of permissions or issues on Discord's side.",
    "ja": "Sakura Bot は「現状のまま」で提供されます。私たちはボットを24時間365日安定して動作させるよう努めていますが、ユーザーによる権限設定の誤りやDiscord側の問題によるデータ損失やサーバーへの損害については責任を負いません。",
    "cn": "Sakura Bot 按“原样”提供。我们努力保持机器人 24/7 平稳运行，但对任何数据丢失、由于用户权限配置错误而导致的服务器损坏或 Discord 方面的问题不承担任何责任。"
  },
  "Chủ sở hữu Bot (Owner) và Quản trị viên Web luôn có toàn quyền tự động. Tại đây bạn có thể cấp quyền cho các thành viên Discord khác vào xem Console, gửi lệnh RCON, điều khiển nguồn máy chủ, quản lý tệp tin hoặc soi túi đồ người chơi.": {
    "en": "The Bot Owner and Web Administrators always have full automatic permissions. Here, you can grant other Discord members permissions to view the Console, send RCON commands, control server power, manage files, or inspect player inventories.",
    "ja": "ボットオーナーとWeb管理者には常に完全な権限が自動的に付与されます。ここでは、他のDiscordメンバーにコンソールの表示、RCONコマンドの送信、サーバー電源の制御、ファイルの管理、またはプレイヤーのインベントリ確認を許可できます。",
    "cn": "机器人所有者（Owner）和 Web 管理员始终自动拥有完全权限。在这里，您可以授予其他 Discord 成员查看控制台、发送 RCON 命令、控制服务器电源、管理文件或查看玩家库存的权限。"
  },
  "vào máy chủ Discord của bạn, truy cập bảng điều khiển Web Dashboard hoặc sử dụng bất kỳ dịch vụ, tính năng nào do Sakura Bot cung cấp, bạn đồng ý tuân thủ và chịu sự ràng buộc bởi các Điều khoản Dịch vụ này cũng như": {
    "en": "by joining your Discord server, accessing the Web Dashboard, or using any service or feature provided by Sakura Bot, you agree to comply with and be bound by these Terms of Service as well as",
    "ja": "Discordサーバーに参加し、Webダッシュボードにアクセスし、またはSakura Botが提供するサービスや機能を使用することで、これらの利用規約および",
    "cn": "访问您的 Discord 服务器、访问网络仪表板或使用 Sakura Bot 提供的任何服务或功能，即表示您同意遵守这些服务条款并受其约束"
  },
  "Nếu từ custom đủ nhiều (≥ số từ cần: số từ mỗi lượt × số người chơi × số vòng), hệ thống sẽ dùng 100% từ custom. Nếu thiếu, hệ thống tự động bù thêm từ từ điển chuẩn để đảm bảo trận đấu trọn vẹn không lặp lại!": {
    "en": "If there are enough custom words (≥ required words: words per turn × number of players × number of rounds), the system will use 100% custom words. If insufficient, the system automatically supplements with standard dictionary words to ensure a complete, non-repeating game!",
    "ja": "カスタム単語が十分にある場合（必要単語数以上：1ターンあたりの単語数 × プレイヤー数 × ラウンド数）、システムは100%カスタム単語を使用します。不足している場合は、標準辞書から自動的に単語を補完し、重複のない完全なゲームを保証します！",
    "cn": "如果自定义单词足够多（≥需要单词数：每回合单词数×玩家数量×回合数），系统将使用100%自定义单词。如果缺失，系统会自动从标准词典中进行补偿，确保完整匹配不重复！"
  },
  "Hệ thống hỗ trợ kết nối máy chủ Minecraft SMP và các dịch vụ thứ ba (YouTube, Spotify, Lavalink, Groq/Gemini AI). Việc sử dụng các dịch vụ liên kết phải tuân thủ quy định riêng của từng nền tảng tương ứng.": {
    "en": "The system supports connecting to Minecraft SMP servers and third-party services (YouTube, Spotify, Lavalink, Groq/Gemini AI). The use of linked services must comply with the specific regulations of each respective platform.",
    "ja": "システムはMinecraft SMPサーバーおよびサードパーティサービス（YouTube、Spotify、Lavalink、Groq/Gemini AI）への接続をサポートしています。リンクされたサービスの使用は、各プラットフォームの個別の規定に従う必要があります。",
    "cn": "该系统支持连接到 Minecraft SMP 服务器和第三方服务（YouTube、Spotify、Lavalink、Groq/Gemini AI）。使用链接服务必须遵守各个平台的个别规定。"
  },
  "Tự động phát hiện các server Minecraft có cài đặt SakuraBot Plugin. Nối server với Discord Guild (yêu cầu quyền Server Owner hoặc Administrator). Chat 2 chiều, điều khiển Console và đồng bộ Coins.": {
    "en": "Automatically detect Minecraft servers with the SakuraBot Plugin installed. Connect the server to a Discord Guild (requires Server Owner or Administrator permissions). Two-way chat, Console control, and Coin synchronization.",
    "ja": "SakuraBot Plugin がインストールされた Minecraft サーバーを自動的に検出します。サーバーを Discord ギルドに接続します（Server Owner または Administrator の権限が必要です）。双方向チャット、コンソール操作、Coins の同期。",
    "cn": "自动检测安装了 SakuraBot 插件的 Minecraft 服务器。将服务器连接到 Discord Guild（需要服务器所有者或管理员权限）。 2 方聊天、控制台控制和硬币同步。"
  },
  "Tính năng cho phép bạn cài đặt các từ khóa tùy chỉnh. Khi thành viên nhắn tin chứa từ khóa đó trong server, bot sẽ tự động phản hồi lại bằng văn bản hoặc gửi file đính kèm đã tải lên!": {
    "en": "This feature allows you to set custom keywords. When a member sends a message containing that keyword in the server, the bot will automatically respond with text or send an uploaded attachment!",
    "ja": "この機能はカスタムキーワードを設定できるようにします。メンバーがサーバー内でそのキーワードを含むメッセージを送信すると、ボットは自動的にテキストで返信するか、アップロードされた添付ファイルを送信します！",
    "cn": "该功能允许您安装自定义关键字。当会员在服务器中发送包含该关键字的消息时，机器人将自动回复文本或发送上传的附件！"
  },
  "Sakura Plugin là giải pháp mở rộng cho máy chủ Minecraft, hỗ trợ các tính năng quản lý, kiếm tiền, nhiệm vụ, bảo vệ và trải nghiệm chơi game tốt hơn cho cộng đồng của bạn.": {
    "en": "Sakura Plugin is an expansion solution for Minecraft servers, supporting management features, monetization, quests, protection, and a better gaming experience for your community.",
    "ja": "Sakura PluginはMinecraftサーバー向けの拡張ソリューションで、管理機能、収益化、クエスト、保護、そしてコミュニティにより良いゲーム体験を提供します。",
    "cn": "Sakura Plugin 是 Minecraft 服务器的扩展解决方案，支持管理功能、货币化、任务、保护，并为您的社区提供更好的游戏体验。"
  },
  "Cho thành viên gửi Confession (công khai hoặc ẩn danh). Bot đăng panel với 2 nút, tự tạo thread thảo luận cho mỗi confession. Có nhật ký kiểm duyệt để chống lạm dụng.": {
    "en": "Allow members to submit Confessions (public or anonymous). The bot posts a panel with 2 buttons, automatically creating a discussion thread for each confession. There is an audit log to prevent abuse.",
    "ja": "メンバーが告白（公開または匿名）を送信できるようにします。ボットは2つのボタン付きのパネルを投稿し、各告白ごとにディスカッションスレッドを自動生成します。乱用防止のために監査ログがあります。",
    "cn": "允许成员提交供词（公开或匿名）。该机器人发布一个带有 2 个按钮的面板，为每个忏悔创建一个讨论线程。有一个审核日志可以防止滥用。"
  },
  "nằm dưới mục Level. Tại đây bạn có thể chọn kênh chỉ định để câu cá, kênh nhận thông báo mã quà tặng (Giftcode), và bật/tắt cho phép câu cá ngoài kênh quy định.": {
    "en": "Located under the Level section. Here you can select a specific channel for fishing, a channel to receive gift code notifications, and toggle allowing fishing outside the designated channel.",
    "ja": "レベルセクションの下にあります。ここでは、釣り用に指定されたチャンネル、ギフトコード通知を受け取るチャンネルを選択し、指定されたチャンネル以外での釣りを許可するかどうかを切り替えることができます。",
    "cn": "位于级别部分下。在这里您可以选择指定的钓鱼渠道、接收礼品码通知（Giftcode）的渠道以及启用/禁用指定渠道之外的钓鱼。"
  },
  "Dán liên kết TikTok hoặc Douyin bất kỳ để xem trước video, chọn độ phân giải Full HD / SD, tải âm thanh MP3 hoặc trọn bộ album ảnh Slideshow chất lượng gốc.": {
    "en": "Paste any TikTok or Douyin link to preview the video, choose Full HD / SD resolution, download MP3 audio or the full original-quality photo album slideshow.",
    "ja": "任意のTikTokまたはDouyinリンクを貼り付けて動画をプレビューし、Full HD / SD解像度を選択し、MP3オーディオまたはオリジナル品質のフルフォトアルバムスライドショーをダウンロードします。",
    "cn": "粘贴任何 TikTok 或抖音链接以预览视频，选择全高清/标清分辨率，下载 MP3 音频或完整原始质量幻灯片相册。"
  },
  "Sakura Bot cung cấp các công cụ hỗ trợ quản lý máy chủ, bảo mật AutoMod, cấp độ tương tác (Level), hệ thống Ticket và kết nối Minecraft SMP. Bạn cam kết:": {
    "en": "Sakura Bot provides tools to support server management, AutoMod security, interaction levels (Level), Ticket system, and Minecraft SMP connection. You commit:",
    "ja": "Sakura Botは、サーバー管理、AutoModセキュリティ、インタラクションレベル（Level）、チケットシステム、Minecraft SMP接続をサポートするツールを提供します。あなたは以下に同意します：",
    "cn": "Sakura Bot 提供的工具支持服务器管理、AutoMod 安全性、关卡交互（Level）、Ticket 系统和 Minecraft SMP 连接。您承诺："
  },
  "Khi Cấp Thành Tựu, người chơi sẽ tự động nhận toàn bộ phần thưởng Coins, Xu và Danh hiệu được cấu hình. Thu hồi sẽ xóa khỏi hồ sơ và danh hiệu của user.": {
    "en": "When granting an Achievement, the player will automatically receive all configured rewards: Coins, Xu, and Titles. Revocation will remove them from the user's profile and titles.",
    "ja": "実績が付与されると、プレイヤーは設定されたすべての報酬（Coins、Xu、称号）を自動的に受け取ります。取り消しは、ユーザーのプロフィールと称号からそれらを削除します。",
    "cn": "升级成就时，玩家将自动获得所有配置的金币、金币和头衔奖励。撤销将从用户的个人资料和头衔中删除。"
  },
  "Bạn cần hỗ trợ cấu hình bot, báo cáo lỗi phát sinh hoặc đóng góp ý tưởng phát triển? Chúng tôi luôn lắng nghe và sẵn sàng đồng hành cùng bạn 24/7!": {
    "en": "Do you need help configuring the bot, reporting any bugs, or contributing development ideas? We are always listening and ready to accompany you 24/7!",
    "ja": "ボットの設定サポートや発生したバグの報告、開発アイデアの提供が必要ですか？私たちは常に耳を傾け、24時間365日あなたと共にサポートします！",
    "cn": "您是否需要帮助配置机器人、报告错误或贡献开发想法？我们始终倾听并准备好 24/7 陪伴您！"
  },
  "Không sử dụng các tính năng của Bot (như AutoMod, Mod Commands) để gây tổn hại bất hợp pháp đến người dùng khác mà không có lý do chính đáng.": {
    "en": "Do not use the Bot's features (such as AutoMod, Mod Commands) to cause illegal harm to other users without a legitimate reason.",
    "ja": "Bot の機能（AutoMod、Mod Commands など）を正当な理由なく他のユーザーに違法な害を与えるために使用しないでください。",
    "cn": "无正当理由不得利用Bot功能（如AutoMod、Mod Commands）非法伤害其他用户。"
  },
  ": Đồng bộ cấu trúc mà không xóa kênh cũ (giữ nguyên tin nhắn). Nếu tắt Sync: bot sẽ dọn dẹp cấu trúc cũ để tạo mới hoàn toàn như lúc backup.": {
    "en": "Synchronize the structure without deleting old channels (preserve messages). If Sync is turned off: the bot will clean up the old structure to create a completely new one as during backup.",
    "ja": "古いチャンネルを削除せずに構造を同期します（メッセージを保持）。Sync をオフにすると、バックアップ時と同様に古い構造をクリーンアップして完全に新しいものを作成します。",
    "cn": "：同步结构而不删除旧通道（保持消息完整）。如果关闭同步：机器人将清理旧结构以创建一个全新的结构，就像备份时一样。"
  },
  "Dưới đây là quy trình rõ ràng để bạn tải plugin, thêm vào server, kiểm tra cài đặt, và sử dụng các lệnh tiện ích ngay khi vào server.": {
    "en": "Below is a clear process for you to download the plugin, add it to the server, check the installation, and use utility commands as soon as you join the server.",
    "ja": "以下は、プラグインをダウンロードし、サーバーに追加し、インストールを確認し、サーバーに参加したらすぐにユーティリティコマンドを使用するための明確な手順です。",
    "cn": "下面是一个清晰的过程，供您下载插件，将其添加到服务器，检查设置，并在进入服务器时立即使用实用程序命令。"
  },
  "Khởi động lại server hoặc vào console rồi kiểm tra xem plugin đã load thành công chưa. Đảm bảo Java và Vault đang hoạt động đúng.": {
    "en": "Restart the server or go to the console and check whether the plugin has loaded successfully. Ensure that Java and Vault are running correctly.",
    "ja": "サーバーを再起動するかコンソールに入り、プラグインが正常にロードされたか確認してください。Java と Vault が正しく動作していることを確認してください。",
    "cn": "重启服务器或者到控制台查看插件是否加载成功。确保 Java 和 Vault 正常工作。"
  },
  "Bot Discord đa năng với phong cách hoa anh đào anime. Tích hợp bảo mật AutoMod toàn diện, hệ thống âm nhạc chất lượng cao, cấp độ tương tác và tính năng câu cá RPG sống động.": {
    "en": "Multipurpose Discord bot with anime cherry blossom style. Integrating comprehensive AutoMod security, high-quality music system, interactive levels and immersive RPG fishing features.",
    "ja": "アニメ桜風の多目的Discordボット。包括的な AutoMod セキュリティ、高品質の音楽システム、インタラクティブなレベル、没入型 RPG フィッシング機能を統合します。",
    "cn": "具有动漫樱花风格的多用途 Discord 机器人。集成全面的 AutoMod 安全性、高品质音乐系统、互动关卡和身临其境的 RPG 钓鱼功能。"
  },
  "Sakura Bot giúp bạn quản lý server trong 30 giây: AutoMod chống raid/nuke/spam, Welcome, Level & Kinh tế, Ticket, Music 24/7. Tùy chỉnh trực quan qua web dashboard hiện đại.": {
    "en": "Sakura Bot helps you manage the server in 30 seconds: AutoMod anti-raid/nuke/spam, Welcome, Level & Economy, Ticket, Music 24/7. Intuitive customization via modern web dashboard.",
    "ja": "サクラボットは、AutoMod アンチレイド/ニューク/スパム、ウェルカム、レベルとエコノミー、チケット、音楽を 24 時間年中無休で 30 秒でサーバー管理するのに役立ちます。最新の Web ダッシュボードによる直感的なカスタマイズ。",
    "cn": "Sakura Bot 可帮助您在 30 秒内管理服务器：AutoMod 反袭击/核武器/垃圾邮件、欢迎、等级和经济、票务、音乐 24/7。通过现代网络仪表板进行直观定制。"
  },
  "Khi đăng nhập qua Discord, tài khoản Owner (@linhxinh_dev) sẽ tự động nhận toàn quyền quản trị cao nhất và quản lý mọi server mà bot tham gia.": {
    "en": "When logging in via Discord, the Owner account (@linhxinh_dev) will automatically receive full administrative rights and manage all servers that the bot participates in.",
    "ja": "Discord 経由でログインすると、オーナー アカウント (@linhxinh_dev) は自動的に完全な管理権限を受け取り、ボットが参加するすべてのサーバーを管理します。",
    "cn": "通过 Discord 登录时，所有者帐户 (@linhxinh_dev) 将自动获得完整的管理权限并管理机器人参与的所有服务器。"
  },
  "📜 Bảng nhiệm vụ ủy thác thương hội: Nhận và hoàn thành các đơn hàng thu mua nông sản, khoáng sản để nhận thưởng coin & danh vọng.": {
    "en": "📜 Guild entrusted tasks table: Receive and complete orders to purchase agricultural products and minerals to receive coin rewards & fame.",
    "ja": "📜 ギルド委託タスクテーブル: 農産物や鉱物を購入する注文を受け取り、完了して、コイン報酬と名声を受け取ります。",
    "cn": "📜 公会委托任务表：接收并完成购买农产品、矿产的订单即可获得金币奖励和声望。"
  },
  "Nhập các từ tùy chọn, cách nhau bằng dấu phẩy hoặc xuống dòng (Ví dụ: Naruto, Kimetsu no Yaiba, Doraemon, Sakura, Minecraft...)": {
    "en": "Enter optional words, separated by commas or line breaks (For example: Naruto, Kimetsu no Yaiba, Doraemon, Sakura, Minecraft...)",
    "ja": "オプションの単語をカンマまたは改行で区切って入力します (例: NARUTO、鬼滅の刃、ドラえもん、さくら、Minecraft...)",
    "cn": "输入可选单词，以逗号或换行符分隔（例如：Naruto、Kimetsu no Yaiba、Doraemon、Sakura、Minecraft...）"
  },
  "Trước khi người chơi bắt đầu dùng, nên xác nhận server có đủ chuẩn bị như Vault, Permission và cấu hình cơ bản khớp với plugin.": {
    "en": "Before players start using it, they should confirm that the server has enough preparations such as Vault, Permission, and basic configuration that matches the plugin.",
    "ja": "プレイヤーは使用を開始する前に、サーバーに Vault、権限、プラグインに一致する基本構成などの十分な準備が整っていることを確認する必要があります。",
    "cn": "玩家在开始使用之前，应确认服务器有足够的准备工作，如Vault、权限以及与插件匹配的基本配置。"
  },
  "Số dư Coins và Xu của người dùng được quản lý an toàn và đồng bộ độc lập, không cho phép chỉnh sửa trực tiếp từ Bảng Xếp Hạng.": {
    "en": "User balances of Coins and Coins are managed securely and synchronized independently, with no direct editing allowed from the Leaderboard.",
    "ja": "コインとコインのユーザー残高は安全に管理され、個別に同期され、リーダーボードから直接編集することはできません。",
    "cn": "用户的金币和金币余额得到安全管理并独立同步，不允许从排行榜直接编辑。"
  },
  "Nhập Discord User ID phía trên hoặc chọn một cần thủ từ danh sách bảng xếp hạng bên dưới để ngắm bể cá và thao tác quản trị.": {
    "en": "Enter the Discord User ID above or select an angler from the leaderboard list below to view the fish tank and operate the admin.",
    "ja": "上に Discord ユーザー ID を入力するか、下のリーダーボード リストから釣り人を選択して水槽を表示し、管理者を操作します。",
    "cn": "输入上方的 Discord 用户 ID 或从下方的排行榜列表中选择钓鱼者即可查看鱼缸并进行管理。"
  },
  "Nếu bạn không đồng ý với bất kỳ phần nào của các điều khoản này, vui lòng ngừng sử dụng Bot và xóa Bot khỏi máy chủ của bạn.": {
    "en": "If you do not agree with any part of these terms, please stop using the Bot and remove the Bot from your server.",
    "ja": "これらの規約の一部でも同意できない場合は、ボットの使用を中止し、サーバーからボットを削除してください。",
    "cn": "如果您不同意这些条款的任何部分，请停止使用机器人并从您的服务器中删除机器人。"
  },
  "để đồng bộ tiến độ và tự động nhận thưởng Coins / Xu khi chơi minigame! Dưới đây là danh mục toàn bộ thành tựu của bot:": {
    "en": "to synchronize progress and automatically receive Coins / Coins rewards when playing minigames! Below is the complete catalog of the bot's achievements:",
    "ja": "ミニゲームをプレイするときに進行状況を同期し、コイン/コイン報酬を自動的に受け取ります!以下はボットの成果の完全なカタログです。",
    "cn": "玩小游戏时同步进度并自动获得金币/金币奖励！以下是机器人成就的完整目录："
  },
  "Thiết kế trang bio cá nhân hiện đại với giao diện tùy biến, hình nền, màu sắc tương tác và sắp xếp các khối theo ý bạn.": {
    "en": "Design a modern personal bio page with customizable interface, backgrounds, interactive colors and block arrangements as you like.",
    "ja": "カスタマイズ可能なインターフェイス、背景、インタラクティブな色、ブロックの配置を自由に使用して、モダンな個人の自己紹介ページをデザインします。",
    "cn": "根据您的喜好设计具有可定制界面、背景、交互式颜色和块排列的现代个人简介页面。"
  },
  "Sakura TikTok Downloader • Phát triển bởi SakuraBot Team 🌸 • Không lưu trữ bất kỳ video nào trên máy chủ của chúng tôi.": {
    "en": "Sakura TikTok Downloader • Developed by SakuraBot Team 🌸 • Does not host any videos on our server.",
    "ja": "さくら TikTok ダウンローダー • さくらボット チームによって開発されました 🌸 • 当社のサーバー上でビデオをホストしません。",
    "cn": "Sakura TikTok Downloader • 由 SakuraBot 团队开发 ♡ • 不在我们的服务器上托管任何视频。"
  },
  "Trang tổng hợp hồ sơ liên kết cá nhân của cộng đồng Sakura Bot. Tạo trang bio đẹp mắt của riêng bạn chỉ trong 30 giây!": {
    "en": "Page summarizing the personal link profiles of the Sakura Bot community. Create your own beautiful bio page in just 30 seconds!",
    "ja": "さくらボットコミュニティの個人リンクプロフィールをまとめたページ。たった 30 秒で自分だけの美しい自己紹介ページを作成できます。",
    "cn": "总结 Sakura Bot 社区个人链接配置文件的页面。只需 30 秒即可创建您自己的精美个人简介页面！"
  },
  "Quản lý danh mục vật phẩm trong shop bot, cập nhật giá Coins/Xu, chỉnh sửa thuộc tính, ẩn/hiện hoặc tạo trang bị mới.": {
    "en": "Manage the item list in the bot shop, update Coins/Coins prices, edit attributes, hide/show or create new equipment.",
    "ja": "ボットショップのアイテムリストの管理、コイン/コインの価格の更新、属性の編集、非表示/表示、または新しい装備の作成を行います。",
    "cn": "管理机器人商店中的物品列表，更新金币/金币价格，编辑属性，隐藏/显示或创建新装备。"
  },
  "Xem toàn bộ vật phẩm trong cửa hàng bot, điều chỉnh giá Coins/Xu, chỉnh sửa thuộc tính và bật/tắt hiển thị (ẩn/hiện).": {
    "en": "View all items in the bot shop, adjust Coins/Coins prices, edit properties and enable/disable display (hide/show).",
    "ja": "ボットショップのすべてのアイテムを表示し、コイン/コインの価格を調整し、プロパティを編集し、表示を有効/無効にします (非表示/表示)。",
    "cn": "查看机器人商店中的所有物品，调整金币/金币价格，编辑属性以及启用/禁用显示（隐藏/显示）。"
  },
  "Theo dõi danh sách các cuộc hôn nhân, nhẫn cưới, điểm tình cảm, quỹ chung và can thiệp giải trừ ly hôn khi cần thiết.": {
    "en": "Monitor the list of marriages, wedding rings, affection points, joint funds and intervene in divorce dissolution when necessary.",
    "ja": "結婚、結婚指輪、愛情ポイント、共同資金のリストを監視し、必要に応じて離婚の解消に介入します。",
    "cn": "监控婚姻清单、婚戒、感情点、共同资金，必要时介入离婚解除。"
  },
  "Xem các cuộc hôn nhân đang có trên Discord, tiến độ tình cảm, quỹ chung, chỉnh sửa thông tin hoặc giải trừ (ly hôn).": {
    "en": "View existing marriages on Discord, love progress, joint funds, edit information or dissolve (divorce).",
    "ja": "Discord で既存の結婚生活、恋愛の進行状況、共同資金を表示し、情報を編集したり、解消 (離婚) したりできます。",
    "cn": "在 Discord 上查看现有婚姻、爱情进展、共同资金、编辑信息或解散（离婚）。"
  },
  "🛡️ Quản trị hệ thống Anti-XRay ẩn quặng và bảo vệ rương khỏi gian lận (Hỗ trợ 3 cấp độ bảo vệ chống X-Ray mod/pack).": {
    "en": "🛡️ Anti-XRay system admin hides ores and protects chests from cheats (Supports 3 levels of anti-X-Ray protection mod/pack).",
    "ja": "🛡️ 対 X 線システム管理者は鉱石を隠し、チェストをチートから保護します (3 レベルの対 X 線保護 MOD/パックをサポート)。",
    "cn": "🛡️ 抗 X 射线系统管理员隐藏矿石并保护箱子免受作弊（支持 3 级抗 X 射线保护模块/包）。"
  },
  "Xem lướt qua từng bức ảnh với giao diện mượt mà và tải toàn bộ bộ sưu tập ảnh dưới dạng file ZIP chỉ với 1 cú click.": {
    "en": "Glance through each photo with a smooth interface and download the entire photo collection as a ZIP file with just 1 click.",
    "ja": "スムーズなインターフェイスで各写真を確認し、1 回クリックするだけで写真コレクション全体を ZIP ファイルとしてダウンロードできます。",
    "cn": "通过流畅的界面浏览每张照片，只需单击一下即可将整个照片集下载为 ZIP 文件。"
  },
  "Chọn tài khoản User và Server đích để cộng thêm, trừ bớt hoặc gán chính xác số dư Coin, Xu hoặc Tiền gửi Ngân Hàng.": {
    "en": "Select the target User and Server account to add, subtract or assign the exact Coin, Coin or Bank Deposit balance.",
    "ja": "ターゲットのユーザーとサーバーのアカウントを選択して、正確なコイン、コイン、または銀行預金残高を追加、減算、または割り当てます。",
    "cn": "选择目标用户和服务器帐户以添加、减去或分配确切的硬币、硬币或银行存款余额。"
  },
  "Quản lý đất canh tác, hạt giống, hoa màu, sâu bọ, nông sản đột biến và điều khiển Mùa màng & Thời tiết nông nghiệp.": {
    "en": "Manage arable land, seeds, crops, insects, mutant agricultural products and control Agricultural Crops & Weather.",
    "ja": "耕地、種子、作物、昆虫、突然変異農産物を管理し、農作物と天候を制御します。",
    "cn": "管理耕地、种子、农作物、昆虫、突变农产品并控制农作物和天气。"
  },
  "Tích hợp trí tuệ nhân tạo Minimax & Alpha-Beta Pruning 4 cấp độ. Chạm vào quân để chọn, chạm ô đích để di chuyển.": {
    "en": "Integrated artificial intelligence Minimax & Alpha-Beta Pruning 4 levels. Touch the piece to select, touch the target square to move.",
    "ja": "統合された人工知能 Minimax & Alpha-Beta Pruning 4 レベル。ピースをタッチして選択し、ターゲットのマスをタッチして移動します。",
    "cn": "集成人工智能 Minimax 和 Alpha-Beta 修剪 4 个级别。触摸棋子进行选择，触摸目标方块进行移动。"
  },
  "Gửi một hộp quà Discord Nitro miễn phí giả mạo. Nạn nhân bấm vào sẽ bị troll phát âm thanh hoặc thông báo quê xệ!": {
    "en": "Send a fake free Discord Nitro gift box. If the victim clicks on it, the troll will play a sound or a saggy message!",
    "ja": "偽の無料 Discord Nitro ギフト ボックスを送信します。被害者がそれをクリックすると、トロールは音または垂れ下がったメッセージを再生します。",
    "cn": "发送一个假的免费 Discord Nitro 礼品盒。如果受害者点击它，巨魔就会播放声音或下垂的消息！"
  },
  "👑 Quyền Admin: Tạo, cấp phát và quản lý các trang bị tùy chỉnh, vũ khí đặc biệt có gắn hiệu ứng thuộc tính riêng.": {
    "en": "👑 Admin rights: Create, allocate and manage custom equipment and special weapons with unique attribute effects.",
    "ja": "👑 管理者権限: 独自の属性効果を持つカスタム装備や特別な武器を作成、割り当て、管理します。",
    "cn": "👑 管理员权限：创建、分配和管理具有独特属性效果的自定义装备和特殊武器。"
  },
  "Yêu cầu xóa thông tin liên kết Minecraft hoặc đặt lại Level/Coins bằng cách liên hệ với Ban quản trị qua Discord.": {
    "en": "Request removal of Minecraft link information or reset of Levels/Coins by contacting Admin via Discord.",
    "ja": "Minecraft リンク情報の削除またはレベル/コインのリセットをリクエストするには、Discord 経由で管理者に連絡してください。",
    "cn": "通过 Discord 联系管理员，请求删除 Minecraft 链接信息或重置关卡/金币。"
  },
  "Nếu bạn có bất kỳ câu hỏi hoặc thắc mắc nào liên quan đến Điều khoản Dịch vụ, vui lòng liên hệ với chúng tôi qua:": {
    "en": "If you have any questions or concerns regarding the Terms of Service, please contact us via:",
    "ja": "利用規約に関してご質問やご不明な点がございましたら、次の方法でお問い合わせください。",
    "cn": "如果您对服务条款有任何疑问或疑虑，请通过以下方式联系我们："
  },
  "Quản lý cuốc đào, cấp cường hóa (+150 & 20⭐), túi quặng người chơi, bách khoa khoáng sản và tạo trang bị custom.": {
    "en": "Manage digging hoe, enhancement level (+150 & 20⭐), player ore bag, mineral encyclopedia and create custom equipment.",
    "ja": "掘鍬、強化レベル (+150 & 20⭐)、プレイヤーの鉱石バッグ、鉱物図鑑を管理し、カスタム装備を作成します。",
    "cn": "管理挖掘锄头、增强等级（+150 & 20⭐）、玩家矿袋、矿物百科全书并创建自定义设备。"
  },
  "Điều chỉnh tỉ lệ đập cuốc (+150 & 20⭐), sản lượng khoáng sản và tỉ lệ đột biến mỏ đá quý. Đồng bộ toàn hệ thống.": {
    "en": "Adjusted pickaxe strike rate (+150 & 20⭐), mineral output and gem mine mutation rate. Synchronize the entire system.",
    "ja": "つるはしの攻撃率 (+150 & 20⭐)、鉱物生産量、宝石鉱山の突然変異率を調整しました。システム全体を同期します。",
    "cn": "调整了镐命中率（+150 & 20⭐）、矿物产量和宝石矿变异率。同步整个系统。"
  },
  "📦 Mở hòm bán đồ nhanh tự động: Thả vật phẩm vào rương, hệ thống tự đối chiếu bảng giá Shop và cộng coin tức thì.": {
    "en": "📦 Open the box to sell items automatically: Drop items into the chest, the system automatically compares the Shop price list and adds coins immediately.",
    "ja": "📦 ボックスを開けてアイテムを自動的に販売します: アイテムをチェストにドロップすると、システムがショップの価格リストを自動的に比較し、すぐにコインを追加します。",
    "cn": "📦开箱自动出售物品：将物品放入宝箱，系统自动比对商店价目表并立即添加金币。"
  },
  "✨ Mở cây kỹ năng & chỉ số nội tại RPG: Nâng cấp sức mạnh khai khoáng, chặt cây, chiến đấu, phòng thủ và hồi máu.": {
    "en": "✨ Open RPG skill tree & internal stats: Upgrade mining power, tree cutting, combat, defense and healing.",
    "ja": "✨ オープン RPG スキル ツリーと内部統計: 採掘力、木の伐採、戦闘、防御、治癒をアップグレードします。",
    "cn": "✨ 开放RPG技能树和内部统计数据：升级采矿能力、砍树、战斗、防御和治疗。"
  },
  "🌸 Liên kết tài khoản Minecraft với Discord SakuraBot, kiểm tra trạng thái và chuyển đổi coins an toàn hai chiều.": {
    "en": "🌸 Link your Minecraft account with Discord SakuraBot, check status and securely convert coins two-way.",
    "ja": "🌸 Minecraft アカウントを Discord のサクラボットにリンクし、ステータスを確認し、コインを双方向で安全に変換します。",
    "cn": "⭐ 将您的 Minecraft 帐户与 Discord SakuraBot 关联，检查状态并安全地双向兑换硬币。"
  },
  "Đình chỉ hoặc chặn vĩnh viễn (Blacklist) bất kỳ người dùng hoặc máy chủ nào cố tình lạm dụng, phá hoại hệ thống.": {
    "en": "Suspend or permanently block (Blacklist) any user or server who intentionally abuses or sabotages the system.",
    "ja": "システムを意図的に悪用または妨害するユーザーまたはサーバーを停止または永久にブロック (ブラックリスト) します。",
    "cn": "暂停或永久阻止（列入黑名单）任何故意滥用或破坏系统的用户或服务器。"
  },
  "🪑 Ngồi xuống mọi bề mặt block, bậc thang, ghế sofa hoặc chuyển đổi cho phép người chơi khác cõng/ngồi lên mình.": {
    "en": "🪑 Sit down on any block surface, step, sofa or switch allowing another player to carry/sit on you.",
    "ja": "🪑 ブロックの表面、ステップ、ソファ、またはスイッチに座り、他のプレイヤーが自分の上に乗ったり座ったりできるようにします。",
    "cn": "🪑 坐在任何方块表面、台阶、沙发或开关上，让其他玩家可以抱着/坐在你身上。"
  },
  "và hệ thống Web Dashboard thu thập, sử dụng và bảo vệ thông tin của bạn khi bạn sử dụng dịch vụ của chúng tôi.": {
    "en": "and the Web Dashboard system collects, uses and protects your information when you use our services.",
    "ja": "また、Web ダッシュボード システムは、お客様が当社のサービスを使用する際にお客様の情報を収集、使用、保護します。",
    "cn": "Web Dashboard 系统在您使用我们的服务时收集、使用和保护您的信息。"
  },
  "🏴‍☠️ Mở Chợ Đen bí mật bán các nguyên liệu thần thoại và trang bị quý hiếm với số lượng giới hạn theo chu kỳ.": {
    "en": "🏴‍☠️ Open a secret Black Market selling mythical ingredients and rare equipment in limited quantities periodically.",
    "ja": "🏴‍☠️ 秘密のブラックマーケットをオープンし、数量限定で神話の食材や珍しい装備を販売します。",
    "cn": "🏴‍☠️ 开设秘密黑市，定期限量出售神话原料和稀有装备。"
  },
  "Để vận hành các tính năng bot một cách trơn tru, Sakura Bot chỉ thu thập những thông tin cần thiết tối thiểu:": {
    "en": "To operate bot features smoothly, Sakura Bot only collects the minimum necessary information:",
    "ja": "さくらボットはボット機能をスムーズに動作させるために、必要最小限の情報のみを収集します。",
    "cn": "为了顺利操作机器人功能，Sakura Bot 仅收集最少的必要信息："
  },
  "Dùng để lưu trữ điểm kinh nghiệm (EXP), số dư Coins, Level cá nhân và danh sách liên kết tài khoản Minecraft.": {
    "en": "Used to store experience points (EXP), Coins balance, personal Level and Minecraft account link list.",
    "ja": "経験値 (EXP)、コイン残高、個人レベル、Minecraft アカウントのリンク リストを保存するために使用されます。",
    "cn": "用于存储经验值（EXP）、金币余额、个人等级和Minecraft帐户链接列表。"
  },
  "Tùy biến tỉ lệ đập đồ (+1..+150), tiến sao (1..20 ⭐), may mắn câu cá & đào mỏ trực tiếp theo thời gian thực.": {
    "en": "Customize loot rate (+1..+150), earn stars (1..20 ⭐), fishing & mining luck directly in real time.",
    "ja": "略奪率 (+1..+150) をカスタマイズし、スター (1..20 ⭐) を獲得し、釣りと採掘の運をリアルタイムで直接カスタマイズします。",
    "cn": "自定义战利品率（+1..+150），赚取星星（1..20⭐），直接实时钓鱼和采矿运气。"
  },
  "Không cố ý khai thác lỗi (bug/exploit), tấn công DoS/DDoS hoặc can thiệp vào máy chủ hạ tầng của Sakura Bot.": {
    "en": "Do not intentionally exploit bugs/exploits, attack DoS/DDoS or interfere with Sakura Bot's infrastructure server.",
    "ja": "意図的にバグやエクスプロイトを悪用したり、DoS/DDoS攻撃をしたり、さくらボットのインフラサーバーに干渉したりしないでください。",
    "cn": "请勿故意利用错误/漏洞、攻击 DoS/DDoS 或干扰 Sakura Bot 的基础设施服务器。"
  },
  "Sakura Bot sử dụng xác thực bảo mật trực tiếp qua Discord để tự động đồng bộ máy chủ bạn có quyền Quản lý.": {
    "en": "Sakura Bot uses direct security authentication via Discord to automatically sync servers you have Admin rights to.",
    "ja": "さくらボットは、Discord 経由の直接セキュリティ認証を使用して、管理者権限を持つサーバーを自動的に同期します。",
    "cn": "Sakura Bot 通过 Discord 使用直接安全身份验证来自动同步您拥有管理员权限的服务器。"
  },
  "Bật cái nào cần — vi phạm sẽ bị xóa + cảnh cáo (đủ ngưỡng thì timeout). Mỗi mục có cài đặt riêng khi bật.": {
    "en": "Turn on whichever you need — violations will be deleted + warning (timeout is enough). Each item has its own settings when enabled.",
    "ja": "必要なものをオンにします。違反は削除され、警告が表示されます (タイムアウトで十分です)。有効にした場合、各項目には独自の設定があります。",
    "cn": "打开您需要的任何一个 - 违规行为将被删除+警告（超时就足够了）。每个项目在启用时都有其自己的设置。"
  },
  "Hỗ trợ 2 dòng và toàn bộ mã màu Minecraft (§0 - §f, §l, §o, v.v.). Nhấp vào ô màu bên dưới để chèn nhanh.": {
    "en": "Supports 2 lines and the entire Minecraft color code (§0 - §f, §l, §o, etc.). Click the colored box below for quick insertion.",
    "ja": "2 行と Minecraft カラー コード全体 (§0 - §f、§l、§o など) をサポートします。すぐに挿入するには、下の色付きのボックスをクリックします。",
    "cn": "支持 2 行和整个 Minecraft 颜色代码（§0 - §f、§l、§o 等）。单击下面的彩色框可快速插入。"
  },
  "Rút một lá bài để soi chiếu năng lượng hiện tại. AI Sakura sẽ giúp bạn đọc thông điệp theo câu hỏi riêng.": {
    "en": "Draw a card to reflect your current energy. AI Sakura will help you read messages according to specific questions.",
    "ja": "あなたの現在のエネルギーを反映するカードを引いてください。 AIさくらが、具体的な質問に応じてメッセージを読むお手伝いをします。",
    "cn": "抽一张牌来反映你当前的能量。 AI樱花会根据具体问题帮助您阅读消息。"
  },
  "Khám phá thế giới Sakura Bot, hoàn thành thử thách và nhận thưởng Coin, Xu VIP cùng Danh hiệu độc quyền.": {
    "en": "Explore the world of Sakura Bot, complete challenges and receive Coin rewards, VIP Coins and exclusive Titles.",
    "ja": "サクラボットの世界を探索し、チャレンジを完了して、コイン報酬、VIP コイン、限定称号を受け取りましょう。",
    "cn": "探索 Sakura Bot 的世界，完成挑战并获得金币奖励、VIP 金币和专属头衔。"
  },
  "Khi TẮT, bot tạm ngưng toàn bộ module Anti-Raid, Anti-Nuke, Anti-Spam và lọc từ trên toàn bộ các server.": {
    "en": "When turned OFF, the bot suspends all Anti-Raid, Anti-Nuke, Anti-Spam and word filtering modules on all servers.",
    "ja": "OFF にすると、ボットはすべてのサーバー上のすべての Anti-Raid、Anti-Nuke、Anti-Spam、およびワード フィルタリング モジュールを一時停止します。",
    "cn": "关闭后，机器人会暂停所有服务器上的所有反袭击、反核武器、反垃圾邮件和文字过滤模块。"
  },
  "Chỉ được lưu lại khi người quản trị hoặc người dùng bấm đóng Ticket hỗ trợ nhằm mục đích tra cứu nội bộ.": {
    "en": "Only saved when the administrator or user clicks to close the support ticket for internal lookup purposes.",
    "ja": "管理者またはユーザーが内部検索の目的でサポート チケットをクリックして閉じた場合にのみ保存されます。",
    "cn": "仅当管理员或用户出于内部查找目的单击关闭支持票证时才保存。"
  },
  "Bạn có toàn quyền yêu cầu xóa toàn bộ dữ liệu của bạn hoặc máy chủ của bạn khỏi hệ thống của Sakura Bot:": {
    "en": "You have the full right to request deletion of all your data or your server from Sakura Bot's system:",
    "ja": "あなたには、Sakura Bot のシステムからすべてのデータまたはサーバーの削除を要求する完全な権利があります。",
    "cn": "您拥有完全权利要求从 Sakura Bot 系统中删除您的所有数据或服务器："
  },
  "Hệ thống TTS sử dụng Google TTS và AI Translator tự động vào Voice Channel phát âm theo thời gian thực.": {
    "en": "The TTS system uses Google TTS and AI Translator to automatically enter Voice Channel for real-time pronunciation.",
    "ja": "TTS システムは、Google TTS と AI Translator を使用して、音声チャンネルに自動的に入力し、リアルタイムの発音を実現します。",
    "cn": "TTS系统采用Google TTS和AI Translator自动进入Voice Channel进行实时发音。"
  },
  "Quản lý hơn 210 thành tựu minigame Sakura, cấp/thu hồi cho người chơi và thiết kế thành tựu tùy chỉnh.": {
    "en": "Manage over 210 Sakura minigame achievements, grant/revoke to players, and design custom achievements.",
    "ja": "210 を超えるさくらミニゲームの実績を管理し、プレイヤーに付与/取り消しし、カスタム実績をデザインします。",
    "cn": "管理超过 210 个樱花小游戏成就、向玩家授予/撤销以及设计自定义成就。"
  },
  "Mặc định: youtube.com, youtu.be, discord.com, tenor.com, giphy.com, imgur.com — để trống sẽ chặn hết.": {
    "en": "Default: youtube.com, youtu.be, discord.com, tenor.com, giphy.com, imgur.com — leaving blank will block them all.",
    "ja": "デフォルト: youtube.com、youtu.be、discord.com、tenor.com、giphy.com、imgur.com — 空白のままにすると、すべてブロックされます。",
    "cn": "默认值：youtube.com、youtu.be、discord.com、tenor.com、giphy.com、imgur.com — 留空将阻止所有这些内容。"
  },
  "Quản lý giỏ cá & vật phẩm người chơi, phát hành giftcode, tra cứu bách khoa và sáng tạo loài cá mới.": {
    "en": "Manage fish baskets & player items, issue gift codes, look up encyclopedias and create new fish species.",
    "ja": "魚かごやプレイヤーアイテムを管理し、ギフトコードを発行し、百科事典を調べ、新しい魚種を作成します。",
    "cn": "管理鱼篮和玩家物品、发放礼品代码、查找百科全书并创建新的鱼类品种。"
  },
  "Thêm các mốc sự kiện đặc biệt, nhiệm vụ máy chủ hoặc phần thưởng thành tựu độc quyền cho Sakura Bot.": {
    "en": "Add special event milestones, server quests, or exclusive achievement rewards for Sakura Bot.",
    "ja": "特別なイベントのマイルストーン、サーバークエスト、またはサクラボットの特別な実績報酬を追加します。",
    "cn": "为樱花机器人添加特殊事件里程碑、服务器任务或专属成就奖励。"
  },
  "Chỉ Chủ Sở Hữu Web (Owner) mới có quyền cấp hoặc thu hồi quyền Quản Trị Viên (Admin) cho người dùng.": {
    "en": "Only the Web Owner (Owner) has the right to grant or revoke Administrator rights to users.",
    "ja": "Web 所有者 (オーナー) のみが、ユーザーに管理者権限を付与または取り消す権利を持ちます。",
    "cn": "只有Web所有者（Owner）才有权授予或撤销用户的管理员权限。"
  },
  ": Vai trò được chọn phải có thứ bậc thấp hơn vai trò cao nhất của Sakura Bot để bot có thể gán được.": {
    "en": ": The selected role must be lower in hierarchy than Sakura Bot's highest role for the bot to assign.",
    "ja": ": 選択したロールは、ボットが割り当てるために、Sakura Bot の最上位のロールよりも階層が低い必要があります。",
    "cn": "：所选角色的层次结构必须低于 Sakura Bot 机器人要分配的最高角色。"
  },
  "Dùng để lưu trữ cài đặt riêng của server (Prefix, Kênh Welcome, Cấu hình AutoMod, Danh sách từ cấm).": {
    "en": "Used to store the server's own settings (Prefix, Welcome Channel, AutoMod Configuration, Prohibited Word List).",
    "ja": "サーバー独自の設定 (プレフィックス、ウェルカム チャネル、AutoMod 構成、禁止語リスト) を保存するために使用されます。",
    "cn": "用于存储服务器自己的设置（前缀、欢迎频道、AutoMod 配置、禁止单词列表）。"
  },
  "Kiểm soát bật/tắt yêu cầu Vote Top.gg cho các lệnh VIP (/math, /translate, /music volume, /xemboi).": {
    "en": "Controls enabling/disabling Vote Top.gg requests for VIP commands (/math, /translate, /music volume, /xemboi).",
    "ja": "VIP コマンド (/math、/translate、/music volume、/xemboi) に対する Vote Top.gg リクエストの有効化/無効化を制御します。",
    "cn": "控制启用/禁用 VIP 命令（/math、/translate、/musicvolume、/xemboi）的 Vote Top.gg 请求。"
  },
  "🎵 Phát nhạc trực tiếp qua Simple Voice Chat trong game cho toàn bộ người chơi xung quanh cùng nghe.": {
    "en": "🎵 Stream music directly via Simple Voice Chat in the game for all players around you to listen to.",
    "ja": "🎵 ゲーム内のシンプルボイスチャット経由で音楽を直接ストリーミングし、周囲のすべてのプレイヤーが聞くことができます。",
    "cn": "🎵 通过游戏中的简单语音聊天直接串流音乐，供您周围的所有玩家收听。"
  },
  "Bạn cần đăng nhập để lưu video cá nhân. Tuy nhiên danh sách gợi ý bên dưới vẫn có thể xem miễn phí.": {
    "en": "You need to log in to save personal videos. However, the list of suggestions below can still be viewed for free.",
    "ja": "個人的なビデオを保存するにはログインする必要があります。ただし、以下の提案リストは引き続き無料で閲覧できます。",
    "cn": "您需要登录才能保存个人视频。不过，仍然可以免费查看下面的建议列表。"
  },
  "Tạo bảng cho phép thành viên tự nhận role bằng cách bấm nút (Button) hoặc thả biểu cảm (Reaction)": {
    "en": "Create a board that allows members to claim their roles by pressing a button or releasing an expression (Reaction).",
    "ja": "メンバーがボタンを押すか表情 (リアクション) を放すことで自分の役割を主張できるボードを作成します。",
    "cn": "创建一个板，允许成员通过按下按钮或释放表情（反应）来声明自己的角色。"
  },
  "[System] Kênh trò chuyện 2 chiều đang hoạt động. Nhập nội dung bên dưới để gửi tin nhắn vào game.": {
    "en": "[System] 2-way chat channel is active. Enter the content below to send a message into the game.",
    "ja": "[システム] 双方向チャットチャンネルがアクティブです。以下の内容を入力してゲーム内にメッセージを送信してください。",
    "cn": "[系统] 2路聊天频道已激活。输入以下内容即可向游戏发送消息。"
  },
  "Bán đồ nhanh qua GUI, Chợ Đen buôn hàng quý hiếm, vé số may mắn và nhiệm vụ thương hội phong phú.": {
    "en": "Sell ​​items quickly via GUI, Black Market for rare goods, lucky lottery tickets and rich merchant guild missions.",
    "ja": "GUI、ブラックマーケットでレアな商品、幸運の宝くじ、そして裕福な商人のギルドミッションを介してアイテムを素早く販売します。",
    "cn": "通过 GUI 快速出售物品、稀有商品黑市、幸运彩票和丰富的商人公会任务。"
  },
  "Tải video TikTok với độ phân giải Full HD gốc, xóa sạch hoàn toàn watermark và logo mờ bản quyền.": {
    "en": "Download TikTok videos in original Full HD resolution, completely removing watermarks and blurred copyright logos.",
    "ja": "TikTokビデオをオリジナルのフルHD解像度でダウンロードし、透かしやぼやけた著作権ロゴを完全に削除します。",
    "cn": "以原始全高清分辨率下载 TikTok 视频，完全去除水印和模糊的版权标志。"
  },
  "Săn bắt cá đại dương, nâng cấp cần câu, buôn bán hải sản và cạnh tranh top cần thủ toàn máy chủ.": {
    "en": "Hunt for ocean fish, upgrade fishing rods, trade seafood and compete with the top anglers across the server.",
    "ja": "海の魚を狩り、釣り竿をアップグレードし、魚介類を取引し、サーバー全体でトップの釣り人たちと競争しましょう。",
    "cn": "寻找海鱼、升级鱼竿、交易海鲜并与全服务器的顶级钓鱼者竞争。"
  },
  "Bảo vệ quặng khỏi mod X-Ray với 3 cấp độ mã hóa khối, chống mở trộm rương và phá hoại đất claim.": {
    "en": "Protect ores from X-Ray mods with 3 levels of block encryption, prevent chest theft and claim land destruction.",
    "ja": "3 レベルのブロック暗号化で X 線改造から鉱石を保護し、チェストの盗難を防ぎ、土地の破壊を主張します。",
    "cn": "通过 3 级区块加密保护矿石免受 X 射线模组的侵害，防止宝箱被盗并声称土地被破坏。"
  },
  "🎯 Hệ thống treo thưởng truy nã người chơi hoặc truy vết vị trí kẻ bị truy nã để nhận thưởng lớn.": {
    "en": "🎯 The system places a bounty on players or tracks the location of a wanted person to receive a big reward.",
    "ja": "🎯 このシステムはプレイヤーに賞金をかけたり、指名手配者の位置を追跡したりして多額の報酬を受け取ります。",
    "cn": "🎯 系统对玩家悬赏或追踪通缉犯的位置以获得丰厚奖励。"
  },
  "🎟️ Mua vé số may mắn hàng ngày, tra cứu giải thưởng và thời gian quay thưởng jackpot trong game.": {
    "en": "🎟️ Buy lucky lottery tickets every day, look up prizes and jackpot drawing time in the game.",
    "ja": "🎟️ 毎日幸運の宝くじを購入し、ゲーム内で賞品とジャックポットの抽選時間を調べてください。",
    "cn": "🎟️每天购买幸运彩票，在游戏中查看奖品和大奖抽奖时间。"
  },
  "🎁 Quyền Admin: Cấp các trang bị thần thoại, vũ khí OP và các cuốn sách phù phép đặc biệt Sakura.": {
    "en": "🎁 Admin Rights: Grant mythical equipment, OP weapons and special Sakura spell books.",
    "ja": "🎁 管理者権限: 神話の装備、OP 武器、特別な桜の魔法の本を付与します。",
    "cn": "🎁 管理员权限：授予神话装备、OP武器和特殊的樱花咒语书。"
  },
  "Mọi đóng góp dù lớn hay nhỏ đều là nguồn động viên to lớn cho đội ngũ duy trì và phát triển bot.": {
    "en": "Every contribution, big or small, is a great source of encouragement for the bot maintenance and development team.",
    "ja": "大小を問わず、あらゆる貢献がボットのメンテナンスおよび開発チームにとって大きな励みになります。",
    "cn": "每一个贡献，无论大小，都是对机器人维护和开发团队的巨大鼓励。"
  },
  "Cập nhật, thay đổi, thêm hoặc bớt các tính năng của Bot và Web Dashboard mà không cần báo trước.": {
    "en": "Update, change, add or remove features of the Bot and Web Dashboard without prior notice.",
    "ja": "事前の通知なしに、ボットおよび Web ダッシュボードの機能を更新、変更、追加、または削除すること。",
    "cn": "更新、更改、添加或删除机器人和 Web 仪表板的功能，恕不另行通知。"
  },
  "Xem chi tiết túi đồ, trang bị giáp, rương Ender và các hộp Shulker bên trong máy chủ Minecraft.": {
    "en": "See details of inventory, armor, Ender chests and Shulker boxes inside the Minecraft server.",
    "ja": "Minecraft サーバー内のインベントリ、アーマー、エンダー チェスト、シュルカー ボックスの詳細を確認します。",
    "cn": "查看 Minecraft 服务器内的库存、盔甲、末影箱和潜影盒的详细信息。"
  },
  "Cung cấp tính năng AutoMod và phát hiện các hành vi phá hoại (Anti-Raid, Anti-Nuke, Anti-Spam).": {
    "en": "Provides AutoMod features and detects vandalism (Anti-Raid, Anti-Nuke, Anti-Spam).",
    "ja": "AutoMod 機能を提供し、破壊行為を検出します (Anti-Raid、Anti-Nuke、Anti-Spam)。",
    "cn": "提供 AutoMod 功能并检测破坏行为（反袭击、反核武器、反垃圾邮件）。"
  },
  "Bạn chưa có quyền quản lý server nào mà bot đang ở, hoặc bot chưa được mời vào server của bạn.": {
    "en": "You do not have permission to manage the server the bot is on, or the bot has not been invited to your server.",
    "ja": "ボットが存在するサーバーを管理する権限がないか、ボットがサーバーに招待されていません。",
    "cn": "您无权管理机器人所在的服务器，或者机器人尚未被邀请到您的服务器。"
  },
  "Đơn vị tiền tệ chính cho câu cá, làm việc, điểm danh daily, mua cần câu, mồi câu và giao dịch.": {
    "en": "Main currency for fishing, working, daily attendance, buying fishing rods, bait and trading.",
    "ja": "釣り、仕事、日々の出勤、釣り竿の購入、餌の購入、取引に使用される主要通貨。",
    "cn": "钓鱼、工作、日常出勤、购买鱼竿、鱼饵和交易的主要货币。"
  },
  "Khi thành viên gửi tin nhắn khớp với từ khóa, bot sẽ tự động gửi câu trả lời hoặc tệp đính kèm": {
    "en": "When a member sends a message that matches the keyword, the bot will automatically send a reply or attachment",
    "ja": "メンバーがキーワードに一致するメッセージを送信すると、ボットは自動的に返信または添付ファイルを送信します。",
    "cn": "当会员发送符合关键字的消息时，机器人会自动发送回复或附件"
  },
  "Mời Sakura Bot về máy chủ của bạn để trải nghiệm tính năng Quản trị, Level, Fishing, Casino...": {
    "en": "Invite Sakura Bot to your server to experience Administration, Level, Fishing, Casino...",
    "ja": "サーバーにさくらボットを招待して、管理、レベル、釣り、カジノなどを体験してください...",
    "cn": "邀请樱花机器人到您的服务器体验管理、关卡、钓鱼、赌场......"
  },
  "Yểm bùa biến nạn nhân thành Cóc/Ếch. Lần câu kế tiếp chắc chắn vớt lên Cóc Ghẻ hoặc Rác rưởi.": {
    "en": "Cast a spell that turns the victim into a Toad/Frog. The next time you fish, make sure to pick up Toadstools or Trash.",
    "ja": "犠牲者をヒキガエル/カエルに変える呪文を唱えます。次回釣りをするときは、キノコやゴミを必ず拾ってください。",
    "cn": "施放一个咒语，将受害者变成蟾蜍/青蛙。下次钓鱼时，请务必捡起伞菌或垃圾。"
  },
  "⚠️ Bạn phải là Chủ sở hữu (Owner) hoặc Administrator của Discord Server này để thực hiện nối!": {
    "en": "⚠️ You must be the Owner or Administrator of this Discord Server to make the connection!",
    "ja": "⚠️ 接続するには、この Discord サーバーの所有者または管理者である必要があります。",
    "cn": "⚠️ 您必须是此 Discord 服务器的所有者或管理员才能建立连接！"
  },
  "để thêm mốc cấp độ và vai trò tương ứng. Khi thành viên đạt đủ cấp, bot sẽ tự động trao role!": {
    "en": "to add corresponding level and role markers. When the member reaches enough level, the bot will automatically award the role!",
    "ja": "対応するレベルとロールのマーカーを追加します。メンバーが十分なレベルに達すると、ボットが自動的に役割を与えます。",
    "cn": "添加相应的级别和角色标记。当会员达到足够等级时，机器人将自动授予该角色！"
  },
  "Dùng các nút Lên / Xuống để điều chỉnh thứ tự xuất hiện của các khối trên trang bio của bạn:": {
    "en": "Use the Up / Down buttons to adjust the order in which blocks appear on your bio page:",
    "ja": "上/下ボタンを使用して、自己紹介ページに表示されるブロックの順序を調整します。",
    "cn": "使用向上/向下按钮调整块在您的个人简介页面上显示的顺序："
  },
  "trong Discord và bot đã được mời vào server đó. Thử đăng xuất và đăng nhập lại bằng Discord.": {
    "en": "in Discord and the bot has been invited to that server. Try logging out and back in using Discord.",
    "ja": "Discord 内にあり、ボットはそのサーバーに招待されています。 Discord を使用してログアウトしてから再度ログインしてみてください。",
    "cn": "在 Discord 中并且机器人已被邀请到该服务器。尝试使用 Discord 注销并重新登录。"
  },
  "Plugin Sakura được đóng gói dưới dạng file .jar sẵn sàng dùng cho máy chủ Minecraft của bạn.": {
    "en": "The Sakura plugin is packaged as a .jar file ready to be used on your Minecraft server.",
    "ja": "さくらプラグインは、Minecraft サーバーですぐに使用できる .jar ファイルとしてパッケージ化されています。",
    "cn": "Sakura 插件打包为 .jar 文件，可在您的 Minecraft 服务器上使用。"
  },
  "Không sử dụng Bot cho các hành vi quấy rối, phá hoại, spam hoặc vi phạm pháp luật hiện hành.": {
    "en": "Do not use the Bot for acts of harassment, vandalism, spam or other violations of applicable laws.",
    "ja": "ボットを嫌がらせ、破壊行為、スパム行為、またはその他の適用法違反に使用しないでください。",
    "cn": "请勿使用机器人进行骚扰、破坏、垃圾邮件或其他违反适用法律的行为。"
  },
  "Trích xuất âm thanh chất lượng cao 320kbps từ bất kỳ video hoặc bài đăng TikTok nào dễ dàng.": {
    "en": "Extract high quality 320kbps audio from any TikTok video or post with ease.",
    "ja": "TikTok ビデオや投稿から高品質の 320kbps オーディオを簡単に抽出します。",
    "cn": "轻松从任何 TikTok 视频或帖子中提取高质量 320kbps 音频。"
  },
  "Dùng một con cá biển trơn trượt tát bôm bốp vào mặt nạn nhân kèm ping công khai trong kênh.": {
    "en": "Use a slippery sea fish to slap the victim in the face with a public ping on the channel.",
    "ja": "滑りやすい海の魚を使って、チャンネル上で公開 ping を送り、被害者の顔を叩きます。",
    "cn": "使用滑溜溜的海鱼在频道上发出公共 ping 来打受害者的脸。"
  },
  "Khi Bot bị gỡ khỏi máy chủ, bạn có thể liên hệ để yêu cầu dọn dẹp toàn bộ cấu hình máy chủ.": {
    "en": "Once the Bot is removed from the server, you can contact to request a cleanup of the entire server configuration.",
    "ja": "ボットがサーバーから削除されたら、サーバー構成全体のクリーンアップをリクエストするために連絡できます。",
    "cn": "从服务器中删除机器人后，您可以联系请求清理整个服务器配置。"
  },
  "Bật (True) để chỉ cho tài khoản bản quyền; Tắt (False) để cho phép cả bản Crack / Offline.": {
    "en": "Turn on (True) to indicate the copyright account; Turn off (False) to allow both Crack / Offline versions.",
    "ja": "著作権アカウントを示すには (True) をオンにします。クラック バージョンとオフライン バージョンの両方を許可するには、オフ (False) にします。",
    "cn": "开启（True）表示版权账号；关闭（False）以允许破解/离线版本。"
  },
  "Tham gia cộng đồng chính thức để nhận hỗ trợ trực tiếp, nhận thông báo update và giao lưu.": {
    "en": "Join the official community to receive direct support, receive updates and socialize.",
    "ja": "公式コミュニティに参加すると、直接サポートを受けたり、最新情報を受け取ったり、交流したりできます。",
    "cn": "加入官方社区以获得直接支持、接收更新和社交。"
  },
  "Tra cứu danh sách hơn 100+ lệnh, cú pháp sử dụng và tài liệu hướng dẫn cấu hình toàn diện.": {
    "en": "Look up a list of over 100+ commands, usage syntax and comprehensive configuration documentation.",
    "ja": "100 を超えるコマンドのリスト、使用構文、および包括的な構成ドキュメントを検索します。",
    "cn": "查找包含 100 多个命令、使用语法和综合配置文档的列表。"
  },
  "Cấu hình kết nối Minecraft riêng cho Server này (hỗ trợ cả RCON / Query và Sakura Plugin)": {
    "en": "Configure a separate Minecraft connection for this Server (supports both RCON / Query and Sakura Plugin)",
    "ja": "このサーバー用に別の Minecraft 接続を設定します (RCON / Query とさくらプラグインの両方をサポート)",
    "cn": "为此服务器配置单独的 Minecraft 连接（支持 RCON / Query 和 Sakura 插件）"
  },
  "Gửi tin nhắn chào mừng kèm ảnh avatar xịn xò, tự động gán vai trò khi thành viên mới vào.": {
    "en": "Send a welcome message with a cool avatar photo, automatically assign roles when new members join.",
    "ja": "クールなアバター写真付きのウェルカム メッセージを送信し、新しいメンバーが参加すると自動的に役割を割り当てます。",
    "cn": "发送带有炫酷头像照片的欢迎信息，新成员加入时自动分配角色。"
  },
  "Giám sát trạng thái Lavalink, kết nối API tích hợp và thông số kỹ thuật chi tiết của Bot": {
    "en": "Monitor Lavalink status, integrated API connections, and detailed Bot specifications",
    "ja": "Lavalink ステータス、統合された API 接続、および詳細なボット仕様を監視します",
    "cn": "监控 Lavalink 状态、集成 API 连接和详细的 Bot 规格"
  },
  "Bỏ bùa nói ngược. Bot sẽ bắt chước các tin nhắn của nạn nhân và đảo ngược toàn bộ ký tự!": {
    "en": "Cast the reverse spell. The bot will imitate the victim's messages and reverse all the characters!",
    "ja": "逆の呪文を唱えます。ボットは被害者のメッセージを模倣し、すべての文字を反転します。",
    "cn": "施展反向咒语。机器人会模仿受害者的消息并反转所有字符！"
  },
  "Kho từ điển tiếng Việt 73,000+ từ, tra cứu, thêm/xóa từ vựng và bảng xếp hạng người chơi": {
    "en": "Vietnamese dictionary with 73,000+ words, lookup, add/delete vocabulary and player rankings",
    "ja": "73,000以上の単語を収録したベトナム語辞書、語彙の検索、追加/削除、プレイヤーランキング",
    "cn": "越南语词典，包含 73,000 多个单词，可查找、添加/删除词汇和玩家排名"
  },
  "Nếu bạn có thắc mắc hoặc yêu cầu về quyền riêng tư và dữ liệu cá nhân, vui lòng liên hệ:": {
    "en": "If you have questions or requests about privacy and personal data, please contact:",
    "ja": "プライバシーおよび個人データに関するご質問またはご要望がある場合は、以下までご連絡ください。",
    "cn": "如果您对隐私和个人数据有疑问或请求，请联系："
  },
  "Bảng vinh danh cao thủ minigame toàn bot và danh sách tra cứu hơn 210 thành tựu Sakura.": {
    "en": "Minigame honor board full of bots and lookup list of more than 210 Sakura achievements.",
    "ja": "ボットが満載のミニゲーム名誉ボードと 210 を超えるサクラ実績のルックアップ リスト。",
    "cn": "迷你游戏荣誉板充满了机器人和超过 210 个樱花成就的查找列表。"
  },
  "Thêm các mẫu cần câu, mồi câu, thú cưng hoặc vật phẩm troll hoàn toàn mới vào hệ thống.": {
    "en": "Add completely new fishing rod models, lures, pets or trolling items to the system.",
    "ja": "まったく新しい釣り竿モデル、ルアー、ペット、またはトローリング アイテムをシステムに追加します。",
    "cn": "将全新的钓鱼竿模型、鱼饵、宠物或拖钓物品添加到系统中。"
  },
  "Tự động bắt mã đổi thưởng mới cho Genshin, HSR, ZZZ, NTE, Endfield và gửi kèm role ping": {
    "en": "Automatically capture new redemption codes for Genshin, HSR, ZZZ, NTE, Endfield and send with role ping",
    "ja": "Genshin、HSR、ZZZ、NTE、Endfield の新しい引き換えコードを自動的に取得し、ロール ping で送信します",
    "cn": "自动捕获 Genshin、HSR、ZZZ、NTE、Endfield 的新兑换代码并通过角色 ping 发送"
  },
  "Tài khoản tiết kiệm tích lũy coin của người chơi trong hệ thống ngân hàng Sakura Bank.": {
    "en": "The player's savings account accumulates coins in the Sakura Bank banking system.",
    "ja": "プレイヤーの普通預金口座は、さくら銀行銀行システムにコインを蓄積します。",
    "cn": "玩家的储蓄账户在樱花银行的银行系统中积累硬币。"
  },
  "Tích lũy kinh nghiệm khi chat & voice, bảng xếp hạng Top server, shop vai trò và coin.": {
    "en": "Gain experience in chat & voice, Top server rankings, role shop and coins.",
    "ja": "チャットと音声、トップサーバーランキング、ロールショップ、コインの経験を積みましょう。",
    "cn": "获得聊天和语音、顶级服务器排名、角色商店和金币方面的经验。"
  },
  "Đóng góp kinh phí duy trì hạ tầng máy chủ và API cao cấp giúp Sakura Bot luôn mượt mà.": {
    "en": "Contribute funds to maintain server infrastructure and high-end APIs to help Sakura Bot always run smoothly.",
    "ja": "さくらボットが常にスムーズに動作するように、サーバー インフラストラクチャとハイエンド API を維持するために資金を寄付してください。",
    "cn": "贡献资金维护服务器基础设施和高端API，帮助Sakura Bot始终平稳运行。"
  },
  "Mồi câu bị nguyền rủa. Buộc người câu chỉ bắt được ủng rách, rác thải, tảo biển thối.": {
    "en": "The bait is cursed. Force fishermen to only catch torn boots, garbage, and rotten seaweed.",
    "ja": "餌は呪われています。漁師たちに、破れた長靴、ゴミ、腐った海藻だけを捕獲するよう強制する。",
    "cn": "诱饵被诅咒了。迫使渔民只捕捞破靴子、垃圾和腐烂的海藻。"
  },
  "Sao lưu toàn bộ danh mục, kênh, quyền hạn (permissions) và vai trò (roles) của server": {
    "en": "Back up all server categories, channels, permissions and roles",
    "ja": "すべてのサーバー カテゴリ、チャネル、権限、役割をバックアップします。",
    "cn": "备份所有服务器类别、频道、权限和角色"
  },
  "Thời gian ms tối đa cho 1 tick trước khi watchdog tự dừng server (-1 để vô hiệu hóa).": {
    "en": "Maximum ms time for 1 tick before watchdog automatically stops the server (-1 to disable).",
    "ja": "ウォッチドッグがサーバーを自動的に停止するまでの 1 ティックの最大ミリ秒時間 (無効にする場合は -1)。",
    "cn": "看门狗自动停止服务器之前 1 个周期的最大毫秒时间（-1 表示禁用）。"
  },
  "Gửi liên kết bên dưới cho bạn bè. Họ chỉ cần bấm vào là có thể tham gia ngay lập tức": {
    "en": "Send the link below to your friends. They just need to click to join immediately",
    "ja": "以下のリンクを友達に送信してください。クリックするだけですぐに参加できます",
    "cn": "将下面的链接发送给您的朋友。他们只需点击立即加入"
  },
  "Chia sẻ đường link bên dưới. Bạn bè của bạn bấm vào là có thể tham gia trận đấu ngay": {
    "en": "Share the link below. Your friends can click to join the match immediately",
    "ja": "以下のリンクを共有してください。友達はクリックしてすぐに試合に参加できます",
    "cn": "分享下面的链接。您的好友可以点击立即加入比赛"
  },
  "theo cách thông thường, chỉ nhận được khi nạp tiền hoặc do Owner cấp phát trực tiếp.": {
    "en": "Normally, you can only receive money when depositing money or directly from the Owner.",
    "ja": "通常、お金を受け取ることができるのは、お金を入金する場合、またはオーナーから直接受け取る場合のみです。",
    "cn": "通常，您只能在存款时或直接从店主处收到款项。"
  },
  "cho họ (cùng category) – họ tự đặt tên, giới hạn, khóa/ẩn. Rời kênh thì kênh tự xóa.": {
    "en": "for them (same category) – they name themselves, limit, lock/hide. If you leave the channel, the channel will automatically delete itself.",
    "ja": "彼らにとって (同じカテゴリ) – 彼らは自分自身に名前を付け、制限し、ロック/非表示にします。チャンネルを離れると、チャンネルは自動的に削除されます。",
    "cn": "对于他们（同一类别）——他们命名自己、限制、锁定/隐藏。如果您离开频道，该频道将自动删除。"
  },
  "Khởi động lại máy chủ và kiểm tra console xem plugin đã bắt đầu thành công hay chưa.": {
    "en": "Restart the server and check the console to see if the plugin started successfully or not.",
    "ja": "サーバーを再起動し、コンソールでプラグインが正常に開始したかどうかを確認します。",
    "cn": "重新启动服务器并检查控制台以查看插件是否启动成功。"
  },
  "Tạo phòng hỗ trợ riêng tư 1 chạm cho thành viên, lưu transcript và lịch sử tin cậy.": {
    "en": "Create a 1-touch private support room for members, save transcripts and trust history.",
    "ja": "ワンタッチでメンバー向けのプライベート サポート ルームを作成し、トランスクリプトと信頼履歴を保存します。",
    "cn": "为会员创建一键式私人支持室，保存记录和信任历史记录。"
  },
  "Phát nhạc chất lượng cao từ YouTube, SoundCloud, Spotify qua node Lavalink ổn định.": {
    "en": "Stream high quality music from YouTube, SoundCloud, Spotify via stable Lavalink node.",
    "ja": "安定した Lavalink ノードを介して YouTube、SoundCloud、Spotify から高品質の音楽をストリーミングします。",
    "cn": "通过稳定的 Lavalink 节点流式传输来自 YouTube、SoundCloud、Spotify 的高品质音乐。"
  },
  "Thông điệp hiển thị tại màn hình xác nhận tải resource pack khi người chơi kết nối.": {
    "en": "Message displayed on the resource pack download confirmation screen when the player connects.",
    "ja": "プレイヤー接続時のリソースパックダウンロード確認画面に表示されるメッセージ。",
    "cn": "播放器连接时，资源包下载确认屏幕上显示消息。"
  },
  "Dán link YouTube (youtube.com/watch?v=..., youtu.be/..., shorts) hoặc link file mp4": {
    "en": "Paste the YouTube link (youtube.com/watch?v=..., youtu.be/..., shorts) or mp4 file link",
    "ja": "YouTube リンク (youtube.com/watch?v=...、youtu.be/...、shorts) または mp4 ファイル リンクを貼り付けます。",
    "cn": "粘贴 YouTube 链接（youtube.com/watch?v=...、youtu.be/...、shorts）或 mp4 文件链接"
  },
  "* Cần câu mới sẽ tự động trang bị nếu user chưa có cần. Hỗ trợ tối đa +300 và 20⭐.": {
    "en": "* New fishing rods will automatically be equipped if the user does not have one yet. Maximum support +300 and 20⭐.",
    "ja": "※ユーザーがまだ釣り竿を持っていない場合は、新しい釣り竿が自動的に装備されます。最大サポート+300と20⭐。",
    "cn": "* 如果用户还没有钓鱼竿，将会自动装备新的钓鱼竿。最大支持+300和20⭐。"
  },
  "Vẽ hình theo từ khóa & thi tài đoán từ real-time, hỗ trợ Multiplayer & Bot Sakura": {
    "en": "Draw pictures according to keywords & compete in real-time word guessing, support Multiplayer & Sakura Bot",
    "ja": "キーワードに従って絵を描き、リアルタイムの単語推測で競い合い、マルチプレイヤーとさくらボットをサポート",
    "cn": "根据关键词画图并进行实时猜词比赛，支持多人游戏和樱花机器人"
  },
  "Hiển thị nội quy và nút bấm để thành viên đồng ý quy tắc trước khi mở khóa server": {
    "en": "Display rules and buttons for members to agree to the rules before unlocking the server",
    "ja": "サーバーのロックを解除する前に、メンバーがルールに同意するためのルールとボタンを表示します。",
    "cn": "显示规则和按钮，让成员在解锁服务器之前同意规则"
  },
  "Bấm vào từng tính năng để xem danh sách lệnh và hướng dẫn chi tiết từ Sakura Bot.": {
    "en": "Click on each feature to see a list of commands and detailed instructions from Sakura Bot.",
    "ja": "各機能をクリックすると、Sakura Bot のコマンド一覧と詳細な手順が表示されます。",
    "cn": "单击每个功能可查看 Sakura Bot 的命令列表和详细说明。"
  },
  "Tarot chỉ mang tính tham khảo và tự phản chiếu, không thay thế tư vấn chuyên môn.": {
    "en": "Tarot is for reference and self-reflection purposes only and is not a substitute for professional advice.",
    "ja": "タロットは参考と自省のみを目的としており、専門的なアドバイスの代わりとなるものではありません。",
    "cn": "塔罗牌仅供参考和自我反省之用，不能替代专业建议。"
  },
  "Gửi log chi tiết vào kênh riêng cho admin theo dõi. Chọn kênh cho từng nhóm — để": {
    "en": "Send detailed logs to a private channel for admin to monitor. Select channels for each group — to",
    "ja": "管理者が監視できるように、詳細なログをプライベート チャネルに送信します。各グループのチャンネルを選択する —",
    "cn": "将详细日志发送到专用通道供管理员监控。为每个组选择频道 — 以便"
  },
  "Đóng băng cần câu của nạn nhân. Trong thời gian này nạn nhân không thể thả cần.": {
    "en": "Freeze the victim's fishing rod. During this time the victim cannot release the lever.",
    "ja": "被害者の釣り竿を凍らせます。この間、被害者はレバーを放すことができません。",
    "cn": "冻结受害者的钓鱼竿。在此期间，受害者无法松开控制杆。"
  },
  "© 2026 Sakura Bot — Trợ lý Discord thông minh & đa năng cho cộng đồng Việt Nam.": {
    "en": "© 2026 Sakura Bot — Smart & versatile Discord assistant for the Vietnamese community.",
    "ja": "© 2026 Sakura Bot — ベトナム人コミュニティ向けのスマートで多用途な Discord アシスタント。",
    "cn": "© 2026 Sakura Bot — 越南社区的智能多功能 Discord 助手。"
  },
  "Cướp ngẫu nhiên 1 con cá có giá trị cao nhất trong kho đồ câu cá của nạn nhân.": {
    "en": "Randomly steal 1 fish with the highest value in the victim's fishing inventory.",
    "ja": "被害者の釣りインベントリの中で最も価値の高い魚をランダムに 1 匹盗みます。",
    "cn": "随机偷取受害者钓鱼库存中价值最高的 1 条鱼。"
  },
  "Tin nhắn gửi trên Discord sẽ tự động chuyển vào Minecraft chat, và ngược lại.": {
    "en": "Messages sent on Discord will automatically be transferred to Minecraft chat, and vice versa.",
    "ja": "Discord で送信されたメッセージは自動的に Minecraft チャットに転送され、その逆も同様です。",
    "cn": "在 Discord 上发送的消息将自动转移到 Minecraft 聊天，反之亦然。"
  },
  "Gửi thông báo nhúng (Embed) đẹp mắt kèm skin nhân vật khi có sự kiện in-game.": {
    "en": "Send beautiful Embed notifications with character skins when there are in-game events.",
    "ja": "ゲーム内イベントがあるときに、キャラクター スキンを使用して美しい埋め込み通知を送信します。",
    "cn": "当有游戏内事件时，发送带有角色皮肤的精美嵌入通知。"
  },
  "Tùy biến biệt danh, ảnh banner và tiểu sử (About Me) của bot theo từng server": {
    "en": "Customize the bot's nickname, banner image and biography (About Me) for each server",
    "ja": "サーバーごとにボットのニックネーム、バナー画像、プロフィール (About Me) をカスタマイズします",
    "cn": "为每个服务器自定义机器人的昵称、横幅图像和简介（关于我）"
  },
  "Chuyển cá vào kho của kẻ dùng. Nạn nhân có thể phản đòn bằng Gương ma thuật!": {
    "en": "Move the fish to the user's inventory. The victim can counterattack with the Magic Mirror!",
    "ja": "魚をユーザーの在庫に移動します。被害者はマジックミラー号で反撃できる！",
    "cn": "将鱼移至用户的库存中。受害者可以用魔镜进行反击！"
  },
  "Gửi ngay thông báo mã quà tặng kèm link đổi thưởng vào kênh game đã cấu hình": {
    "en": "Immediately send the gift code notification with the reward link to the configured game channel",
    "ja": "設定されたゲーム チャネルに特典リンクを含むギフト コード通知をすぐに送信します",
    "cn": "立即将带有奖励链接的礼品代码通知发送到配置的游戏频道"
  },
  "Khuyến khích thành viên tương tác hàng ngày để tích lũy ngày streak liên tục": {
    "en": "Encourage members to interact daily to accumulate continuous streak days",
    "ja": "継続的な連続日数を蓄積するために、メンバーに毎日交流するよう奨励します。",
    "cn": "鼓励会员每天互动，累积连续连胜天数"
  },
  "Thành viên chỉ cần gửi ít nhất 1 tin nhắn mỗi ngày tại kênh này để giữ chuỗi": {
    "en": "Members only need to send at least 1 message per day on this channel to keep the chain",
    "ja": "チェーンを維持するには、メンバーはこのチャネルで 1 日に少なくとも 1 つのメッセージを送信するだけで済みます。",
    "cn": "会员每天只需在此频道发送至少1条消息即可保链"
  },
  "Nhập lệnh console gửi đến Bot (status, testdm, say, eval, rates, help...)...": {
    "en": "Enter console commands sent to Bot (status, testdm, say, eval, rates, help...)...",
    "ja": "ボットに送信されるコンソール コマンド (ステータス、testdm、たとえば、eval、rate、help...) を入力します...",
    "cn": "输入发送到 Bot 的控制台命令（状态、testdm、例如、eval、费率、帮助...）..."
  },
  "Hỗ trợ gửi hình ảnh, video, âm thanh hoặc tài liệu đính kèm cùng thông báo.": {
    "en": "Supports sending images, videos, audio or documents attached with notifications.",
    "ja": "通知に添付された画像、ビデオ、オーディオ、またはドキュメントの送信をサポートします。",
    "cn": "支持发送带有通知的图像、视频、音频或文档。"
  },
  "Tài khoản hiện chưa liên kết Discord. Hãy liên kết tài khoản Discord ở tab": {
    "en": "The account is not currently linked to Discord. Please link your Discord account in the tab",
    "ja": "現在、アカウントは Discord にリンクされていません。タブで Discord アカウントをリンクしてください",
    "cn": "该帐户当前未链接到 Discord。请在选项卡中链接您的 Discord 帐户"
  },
  "Anti-raid, anti-nuke, chống spam tin nhắn, lọc link mời và từ cấm tự động.": {
    "en": "Anti-raid, anti-nuke, anti-message spam, filter invitation links and automatic banned words.",
    "ja": "アンチレイド、アンチニューク、アンチメッセージスパム、フィルター招待リンク、自動禁止ワード。",
    "cn": "防袭击、防核武器、防垃圾邮件、过滤邀请链接和自动禁言。"
  },
  "Mã kiểm tra tính toàn vẹn 40 ký tự hex để client không tải lại nếu đã có.": {
    "en": "40 hex character integrity check code so the client does not reload if it already exists.",
    "ja": "40 16 進数文字の整合性チェック コード。コードがすでに存在する場合、クライアントはリロードしません。",
    "cn": "40 十六进制字符完整性检查代码，因此如果该代码已存在，则客户端不会重新加载。"
  },
  "Nếu bật, người chơi từ chối tải sẽ tự động bị ngắt kết nối khỏi máy chủ.": {
    "en": "If enabled, players who refuse to load will automatically be disconnected from the server.",
    "ja": "有効にすると、ロードを拒否したプレーヤーは自動的にサーバーから切断されます。",
    "cn": "如果启用，拒绝加载的玩家将自动断开与服务器的连接。"
  },
  "⚠️ Bạn không phải chủ sở hữu của hồ sơ này và không có quyền chỉnh sửa.": {
    "en": "⚠️ You are not the owner of this profile and do not have editing rights.",
    "ja": "⚠️ あなたはこのプロフィールの所有者ではないため、編集権限がありません。",
    "cn": "⚠️ 您不是此个人资料的所有者，也没有编辑权限。"
  },
  "Cướp một khoản tiền trong ví người khác chuyển thẳng vào ví người dùng.": {
    "en": "Steal an amount of money from someone else's wallet and transfer it directly to the user's wallet.",
    "ja": "他人のウォレットからある金額を盗み、それをユーザーのウォレットに直接転送します。",
    "cn": "从别人的钱包中窃取一定数量的钱并将其直接转移到用户的钱包中。"
  },
  "tính năng này để mọi người dùng được dùng các lệnh tự do không bị chặn.": {
    "en": "This feature allows all users to use commands freely without being blocked.",
    "ja": "この機能により、すべてのユーザーがブロックされることなくコマンドを自由に使用できるようになります。",
    "cn": "此功能允许所有用户自由使用命令而不会被阻止。"
  },
  "Chọn 1 kênh thoại làm “Join to Create”. Khi thành viên vào kênh đó, bot": {
    "en": "Select a voice channel as “Join to Create”. When a member enters that channel, bot",
    "ja": "「参加して作成」として音声チャンネルを選択します。メンバーがそのチャンネルに入ると、ボットが",
    "cn": "选择一个语音通道“加入创建”。当成员进入该频道时，机器人"
  },
  "Tự động trao role khi thành viên trò chuyện đạt các mốc level nhất định": {
    "en": "Automatically award roles when chat members reach certain level milestones",
    "ja": "チャットメンバーが特定のレベルのマイルストーンに到達すると、自動的に役割を付与します",
    "cn": "当聊天成员达到一定级别里程碑时自动授予角色"
  },
  "Bot sẽ thông báo mã quà tặng (Giftcode) vào kênh này khi được phát hành": {
    "en": "The bot will notify the gift code (Giftcode) to this channel when released",
    "ja": "ボットはリリース時にギフトコード（ギフトコード）をこのチャンネルに通知します",
    "cn": "机器人发布时会通知该渠道礼品码（Giftcode）"
  },
  "Tự ý đổi biệt danh của nạn nhân trong server thành tên troll ngớ ngẩn.": {
    "en": "Arbitrarily changed the victim's nickname on the server to a silly troll.",
    "ja": "サーバー上で被害者のニックネームを恣意的に愚かな荒らしに変更しました。",
    "cn": "随意将受害者在服务器上的昵称更改为愚蠢的巨魔。"
  },
  "Rút Minecraft Coins về ví tiền Discord (+1,000 Discord Coins mỗi 1 MC)": {
    "en": "Withdraw Minecraft Coins to Discord wallet (+1,000 Discord Coins per MC)",
    "ja": "Minecraft コインを Discord ウォレットに引き出します (MC ごとに +1,000 Discord コイン)",
    "cn": "将 Minecraft 硬币提取到 Discord 钱包（每个 MC + 1,000 Discord 硬币）"
  },
  "Cho phép invite của server này (không chặn invite trỏ về chính server)": {
    "en": "Allow invites from this server (do not block invites pointing to the server itself)",
    "ja": "このサーバーからの招待を許可します (サーバー自体を指す招待はブロックしないでください)",
    "cn": "允许来自该服务器的邀请（不要阻止指向服务器本身的邀请）"
  },
  "Ví dụ: Rương cổ chìm dưới đáy đại dương chứa mồi quý và thú cưng hiếm!": {
    "en": "For example: Ancient chests sunk to the bottom of the ocean contain precious bait and rare pets!",
    "ja": "例: 海の底に沈んだ古代の宝箱には、貴重な餌や珍しいペットが含まれています。",
    "cn": "例如：沉入海底的古代宝箱里有珍贵的鱼饵和稀有的宠物！"
  },
  "Ví dụ: Khiến nạn nhân bị cóc hóa, lần câu tiếp theo chắc chắn vớt rác!": {
    "en": "For example: Cause the victim to become a frog, the next time you fish, make sure to pick up trash!",
    "ja": "例: 犠牲者をカエルにして、次回釣りをするときは必ずゴミを拾いましょう。",
    "cn": "例如：导致受害者变成青蛙，下次钓鱼时，一定要捡起垃圾！"
  },
  "Quét mã QR hoặc sao chép liên kết để chia sẻ hồ sơ của bạn với bạn bè:": {
    "en": "Scan the QR code or copy the link to share your profile with friends:",
    "ja": "QR コードをスキャンするかリンクをコピーして、プロフィールを友達と共有します。",
    "cn": "扫描二维码或复制链接与好友分享您的个人资料："
  },
  "Viết đôi dòng giới thiệu về bản thân, đam mê, dự án đang thực hiện...": {
    "en": "Write a few lines introducing yourself, passion, ongoing projects...",
    "ja": "自己紹介、情熱、進行中のプロジェクトなどを数行書きます。",
    "cn": "写几行介绍自己、热情、正在进行的项目......"
  },
  "(User View Preview). Các mục quản trị và dữ liệu nhạy cảm đã được ẩn.": {
    "en": "(User View Preview). Admin items and sensitive data have been hidden.",
    "ja": "(ユーザービュープレビュー)。管理項目と機密データは非表示になっています。",
    "cn": "（用户视图预览）。管理项目和敏感数据已被隐藏。"
  },
  "Chỉ những kênh có trong danh sách trên mới được phép dùng lệnh câu cá": {
    "en": "Only channels listed above are allowed to use fishing commands",
    "ja": "上記のチャンネルのみがフィッシング コマンドを使用できます。",
    "cn": "只有上面列出的通道才允许使用钓鱼命令"
  },
  "Tự động trao vai trò ngay khi thành viên hoặc bot mới tham gia server": {
    "en": "Automatically assign roles as soon as new members or bots join the server",
    "ja": "新しいメンバーまたはボットがサーバーに参加するとすぐに自動的に役割を割り当てます",
    "cn": "新成员或机器人加入服务器后自动分配角色"
  },
  "🌸 Sakura TikTok — Xem Trước & Tải Video / Album Ảnh TikTok Không Logo": {
    "en": "🌸 Sakura TikTok — Preview & Download TikTok Videos / Photo Albums Without Logo",
    "ja": "🌸 さくら TikTok — ロゴなしの TikTok ビデオ / フォト アルバムをプレビュー & ダウンロード",
    "cn": "⭐ Sakura TikTok — 预览和下载没有徽标的 TikTok 视频/相册"
  },
  "Xử lý trực tiếp trên trình duyệt, dữ liệu không được gửi lên server.": {
    "en": "Processed directly in the browser, data is not sent to the server.",
    "ja": "ブラウザ内で直接処理され、データはサーバーに送信されません。",
    "cn": "直接在浏览器中处理，数据不发送到服务器。"
  },
  "Môi trường thực thi, tiến trình PID, bộ nhớ RAM và kiến trúc runtime": {
    "en": "Execution environment, process PID, RAM memory and runtime architecture",
    "ja": "実行環境、プロセス PID、RAM メモリ、およびランタイム アーキテクチャ",
    "cn": "执行环境、进程PID、RAM内存和运行时架构"
  },
  "Tạo sự kiện quay thưởng quà tặng công bằng và tự động cho thành viên": {
    "en": "Create fair and automatic gift drawing events for members",
    "ja": "メンバー向けに公正かつ自動のプレゼント抽選イベントを作成する",
    "cn": "为会员打造公平、自动的抽奖活动"
  },
  "Đồng bộ trạng thái và danh sách Whitelist cho máy chủ Minecraft SMP.": {
    "en": "Synchronize status and whitelist for Minecraft SMP server.",
    "ja": "Minecraft SMP サーバーのステータスとホワイトリストを同期します。",
    "cn": "同步 Minecraft SMP 服务器的状态和白名单。"
  },
  "Đổi Discord Coins sang Minecraft Coins (1 MC = 1,000 Discord Coins)": {
    "en": "Convert Discord Coins to Minecraft Coins (1 MC = 1,000 Discord Coins)",
    "ja": "Discord コインを Minecraft コインに変換 (1 MC = 1,000 Discord コイン)",
    "cn": "将 Discord 硬币转换为 Minecraft 硬币（1 MC = 1,000 Discord 硬币）"
  },
  "trong game Minecraft hoặc chọn trực tiếp server phát hiện bên dưới.": {
    "en": "in Minecraft game or directly select the detection server below.",
    "ja": "Minecraft ゲーム内で、または以下の検出サーバーを直接選択します。",
    "cn": "在Minecraft游戏中或者直接选择下面的检测服务器。"
  },
  "Hỗ trợ dán link ảnh hoặc tải tệp từ máy tính (PNG, JPG, GIF, WebP).": {
    "en": "Supports pasting image links or downloading files from your computer (PNG, JPG, GIF, WebP).",
    "ja": "画像リンクの貼り付け、またはコンピューターからのファイルのダウンロード (PNG、JPG、GIF、WebP) をサポートします。",
    "cn": "支持粘贴图像链接或从计算机下载文件（PNG、JPG、GIF、WebP）。"
  },
  "vd: Tham gia sự kiện máy chủ và hoàn thành chuỗi 10 thử thách kỳ bí": {
    "en": "eg: Participate in server events and complete a series of 10 mysterious challenges",
    "ja": "例: サーバーイベントに参加し、一連の 10 個の謎のチャレンジを完了する",
    "cn": "例如：参加服务器活动并完成一系列10个神秘挑战"
  },
  "Nhấn vào từng mục bên dưới để xem mô tả và cú pháp cụ thể của lệnh.": {
    "en": "Click on each item below to see the command's description and specific syntax.",
    "ja": "以下の各項目をクリックすると、コマンドの説明と特定の構文が表示されます。",
    "cn": "单击下面的每一项可查看命令的说明和具体语法。"
  },
  "📢 Tự động gửi thông báo code mới đến kênh Giftcode của Discord Bot": {
    "en": "📢 Automatically send new code notifications to Discord Bot's Giftcode channel",
    "ja": "📢 新しいコード通知を Discord Bot の Giftcode チャンネルに自動的に送信します",
    "cn": "📢 自动向 Discord Bot 的 Giftcode 频道发送新代码通知"
  },
  "(mọi server — chỉ admin). Bị cấm sẽ không thực hiện được lệnh (trừ": {
    "en": "(all servers — admin only). Banned will not be able to execute orders (except",
    "ja": "(すべてのサーバー - 管理者のみ)。禁止された場合、注文を実行することはできません（ただし、",
    "cn": "（所有服务器 - 仅限管理员）。被禁止将无法执行订单（除非"
  },
  "Ví dụ: Tăng 35% may mắn, tiết kiệm 20% mồi và buff 25% giá bán cá!": {
    "en": "For example: Increase luck by 35%, save 20% on bait and buff 25% of fish selling price!",
    "ja": "例: 運を 35% 増加させ、餌を 20% 節約し、魚の販売価格を 25% 強化します。",
    "cn": "例如：运气增加35%，鱼饵节省20%，鱼售价提高25%！"
  },
  "Nhập lệnh console... (ví dụ: say Hello server, list, time set day)": {
    "en": "Enter console command... (e.g. say Hello server, list, time set day)",
    "ja": "コンソール コマンドを入力してください... (例: Hello サーバー、リスト、時刻設定日と言う)",
    "cn": "输入控制台命令...（例如，说你好服务器、列表、时间设置日期）"
  },
  "Danh sách được nhóm theo danh mục; 🔊 là phần chat của kênh voice.": {
    "en": "The list is grouped by category; 🔊 is the chat part of the voice channel.",
    "ja": "リストはカテゴリごとにグループ化されています。 🔊はボイスチャンネルのチャット部分です。",
    "cn": "该列表按类别分组； 🔊 是语音频道的聊天部分。"
  },
  "Nhập lệnh console (vd: list, help, say Xin chào, time set day)...": {
    "en": "Enter console commands (e.g. list, help, say Hello, time set day)...",
    "ja": "コンソール コマンドを入力します (例: list、help、Say Hello、time set day)...",
    "cn": "输入控制台命令（例如列表、帮助、说你好、时间设置日期）..."
  },
  "Vui lòng tải gói tài nguyên tùy chỉnh để có trải nghiệm tốt nhất!": {
    "en": "Please download custom resource packs for the best experience!",
    "ja": "最高のエクスペリエンスを得るには、カスタム リソース パックをダウンロードしてください。",
    "cn": "请下载自定义资源包以获得最佳体验！"
  },
  "Mở hệ thống cửa hàng và mua vật phẩm hoặc quyền lợi trong server.": {
    "en": "Open the store system and buy items or benefits in the server.",
    "ja": "ストア システムを開き、サーバー内のアイテムや特典を購入します。",
    "cn": "打开商店系统，购买服务器中的物品或福利。"
  },
  "Ping ma quái chọc ghẹo nạn nhân trong kênh chat rồi xóa tức thì.": {
    "en": "Ghostly ping teases the victim in the chat channel and then deletes it immediately.",
    "ja": "Ghostly ping はチャット チャネルで被害者をからかい、すぐに削除します。",
    "cn": "Ghostly ping 在聊天频道中戏弄受害者，然后立即将其删除。"
  },
  "Nếu bật: thành viên có thể câu cá ở bất kỳ kênh nào trong server": {
    "en": "If enabled: members can fish on any channel on the server",
    "ja": "有効な場合: メンバーはサーバー上の任意のチャネルで釣りをすることができます",
    "cn": "如果启用：成员可以在服务器上的任何频道上钓鱼"
  },
  "Tìm kiếm lệnh (ví dụ: fish, help, ban, play, daily, level...)...": {
    "en": "Search for commands (eg: fish, help, ban, play, daily, level...)...",
    "ja": "コマンドを検索します (例:fish、help、ban、play、daily、level...)...",
    "cn": "搜索命令（例如：钓鱼、帮助、禁止、播放、每日、关卡...）..."
  },
  "Nhập lệnh gửi đến server... (vd: say Hello, whitelist add Steve)": {
    "en": "Enter the command to send to the server... (eg: say Hello, whitelist add Steve)",
    "ja": "サーバーに送信するコマンドを入力してください... (例: Hello、ホワイトリストに Steve を追加)",
    "cn": "输入要发送到服务器的命令...（例如：say Hello，白名单添加 Steve）"
  },
  "thu thập bất kỳ thông tin thanh toán hay tài chính nhạy cảm nào.": {
    "en": "Collect any sensitive financial or payment information.",
    "ja": "機密の財務情報または支払い情報を収集します。",
    "cn": "收集任何敏感的财务或付款信息。"
  },
  "Hiển thị Bảng xếp hạng Level, EXP và quản lý số dư Sakura Coins.": {
    "en": "Display Level, EXP Rankings and manage Sakura Coins balance.",
    "ja": "レベルや経験値ランキングの表示、桜コインの残高管理ができます。",
    "cn": "显示等级、经验排名并管理樱花币余额。"
  },
  "Mô tả cụ thể sự cố bạn gặp phải hoặc ý tưởng bạn muốn chia sẻ...": {
    "en": "Describe specifically the problem you encountered or the idea you want to share...",
    "ja": "遭遇した問題や共有したいアイデアについて具体的に説明してください...",
    "cn": "具体描述您遇到的问题或您想分享的想法..."
  },
  "Rương cổ chìm dưới đáy đại dương chứa mồi quý và thú cưng hiếm!": {
    "en": "Ancient chests sunk to the bottom of the ocean contain precious bait and rare pets!",
    "ja": "海の底に沈んだ古代の宝箱には、貴重な餌や珍しいペットが入っています。",
    "cn": "沉入海底的远古宝箱里有珍贵的鱼饵和稀有的宠物！"
  },
  "Hiển thị thông điệp troll tùy ý kèm hiệu ứng embed hoa anh đào.": {
    "en": "Display arbitrary troll messages with cherry blossom embed effects.",
    "ja": "桜の埋め込みエフェクトを使用して任意の荒らしメッセージを表示します。",
    "cn": "使用樱花嵌入效果显示任意巨魔消息。"
  },
  "Tin nhắn giống hệt nhau quá ngưỡng trong lịch sử gần đây → xóa.": {
    "en": "Identical messages exceeding the threshold in recent history → delete.",
    "ja": "最近の履歴でしきい値を超えた同一メッセージ → 削除。",
    "cn": "最近历史记录中超过阈值的相同消息 → 删除。"
  },
  "Chọn hành động và thực thi ngay trên server này (cần quyền mod)": {
    "en": "Choose action and execute it right on this server (mod permission required)",
    "ja": "アクションを選択し、このサーバー上で直接実行します (MOD 権限が必要です)",
    "cn": "选择操作并在此服务器上执行（需要 mod 权限）"
  },
  "Ví dụ: sensenova/sensenova-6.8-flash-lite hoặc gemini-2.5-flash": {
    "en": "For example: sensenova/sensenova-6.8-flash-lite or gemini-2.5-flash",
    "ja": "例: sensenova/sensenova-6.8-flash-lite または gemini-2.5-flash",
    "cn": "例如：sensenova/sensenova-6.8-flash-lite 或 gemini-2.5-flash"
  },
  "Bấm nút hoặc thả reaction bên dưới để nhận vai trò tương ứng...": {
    "en": "Click the button or drop the reaction below to receive the corresponding role...",
    "ja": "ボタンをクリックするか、下にリアクションをドロップして、対応する役割を受け取ります...",
    "cn": "点击按钮或下拉下方反应即可领取对应角色..."
  },
  "Bạn chỉ thấy và điều khiển các máy chủ Discord mà bạn có quyền": {
    "en": "You only see and control Discord servers to which you have permission",
    "ja": "許可されている Discord サーバーのみを表示および制御できます",
    "cn": "您只能查看和控制您有权访问的 Discord 服务器"
  },
  "🎁 Bể Phần Thưởng Của Rương (Chọn các vật phẩm có thể mở trúng)": {
    "en": "🎁 Chest Rewards Pool (Select items that can be opened)",
    "ja": "🎁 チェスト報酬プール (開けられるアイテムを選択)",
    "cn": "🎁 宝箱奖励池（选择可开启的物品）"
  },
  "Rút trộm tiền. Nếu nạn nhân trang bị Khiên bảo vệ sẽ cướp hụt.": {
    "en": "Stealing money. If the victim is equipped with a Shield, the robbery will be missed.",
    "ja": "お金を盗む。被害者がシールドを装備していれば、強盗は見逃されます。",
    "cn": "偷钱。如果受害者装备了盾牌，抢劫就会错过。"
  },
  "Discord Timeout member. Yêu cầu SakuraBot có quyền Moderation.": {
    "en": "Discord Timeout member. Requires SakuraBot to have Moderation permission.",
    "ja": "Discordのタイムアウトメンバー。サクラボットにはモデレーション権限が必要です。",
    "cn": "Discord 超时成员。需要 SakuraBot 拥有审核权限。"
  },
  "Quản lý khu vực câu cá, kênh nhận giftcode và quy định thả cần": {
    "en": "Manage fishing areas, giftcode receiving channels and fishing regulations",
    "ja": "釣り場、ギフトコード受け取りチャネル、釣り規制を管理する",
    "cn": "管理钓鱼区域、礼品代码接收渠道和钓鱼法规"
  },
  "Tự động cắt và chuyển đổi thành chuẩn 64x64 PNG của Minecraft.": {
    "en": "Automatically crop and convert to Minecraft's 64x64 PNG standard.",
    "ja": "自動的に切り抜き、Minecraft の 64x64 PNG 標準に変換します。",
    "cn": "自动裁剪并转换为 Minecraft 的 64x64 PNG 标准。"
  },
  "không bao giờ bán, chia sẻ hoặc thương mại hóa dữ liệu cá nhân": {
    "en": "never sell, share or commercialize personal data",
    "ja": "個人データを決して販売、共有、商品化しないでください",
    "cn": "绝不出售、分享或商业化个人数据"
  },
  "Tôi có thể đổi biệt danh (nickname) cho bot trên server không?": {
    "en": "Can I change the nickname for a bot on the server?",
    "ja": "サーバー上のボットのニックネームを変更できますか?",
    "cn": "我可以更改服务器上机器人的昵称吗？"
  },
  "Chưa thêm vật phẩm đính kèm nào (mã chỉ tặng tiền/xu nếu có).": {
    "en": "No attached items have been added (code only gives money/coins if available).",
    "ja": "付属アイテムは追加されていません (コードは、利用可能な場合はお金/コインのみを提供します)。",
    "cn": "未添加任何附加物品（代码仅提供金钱/硬币（如果有）。"
  },
  "Troll câu cá khiến đối phương tụt may mắn về 0 trong 15 phút.": {
    "en": "Troll fishing causes the opponent's luck to drop to 0 for 15 minutes.",
    "ja": "トロールフィッシングを行うと、相手の幸運が 15 分間 0 になります。",
    "cn": "巨魔钓鱼会使对手的运气下降到0，持续15分钟。"
  },
  "Mật Khẩu / Mã PIN Bảo Vệ Dashboard (Để trống nếu không khóa):": {
    "en": "Password / PIN Protect Dashboard (Leave blank if not locked):",
    "ja": "パスワード / PIN 保護ダッシュボード (ロックされていない場合は空白のままにします):",
    "cn": "密码/PIN 码保护仪表板（如果未锁定，则留空）："
  },
  "https://www.youtube.com/watch?v=... hoặc https://youtu.be/...": {
    "en": "https://www.youtube.com/watch?v=... or https://youtu.be/...",
    "ja": "https://www.youtube.com/watch?v=... または https://youtu.be/...",
    "cn": "https://www.youtube.com/watch?v=... 或 https://youtu.be/..."
  },
  "Mô tả ngắn cho video này (ví dụ: Hài, nhạc, anime, tập 12...)": {
    "en": "Short description for this video (e.g. Comedy, music, anime, episode 12...)",
    "ja": "このビデオの短い説明 (例: コメディ、音楽、アニメ、エピソード 12...)",
    "cn": "该视频的简短描述（例如喜剧、音乐、动漫、第 12 集...）"
  },
  "Chưa giới hạn kênh câu cá (Thành viên có thể câu ở mọi kênh)": {
    "en": "Unlimited fishing channels (Members can fish in any channel)",
    "ja": "無制限の釣りチャンネル（メンバーはどのチャンネルでも釣りが可能）",
    "cn": "无限钓鱼频道（会员可以在任何频道钓鱼）"
  },
  "Gửi embed/thông báo đến kênh của server này như các bot lớn.": {
    "en": "Send embed/notification to this server's channel like big bots.",
    "ja": "大きなボットのように、このサーバーのチャネルに埋め込み/通知を送信します。",
    "cn": "像大机器人一样向该服务器的通道发送嵌入/通知。"
  },
  "Khi có người nhắn trong kênh Chat Sync, bot tự phát qua RCON": {
    "en": "When someone messages in the Chat Sync channel, the bot automatically broadcasts via RCON",
    "ja": "誰かが Chat Sync チャネルにメッセージを送信すると、ボットは RCON 経由で自動的にブロードキャストします。",
    "cn": "当有人在聊天同步频道中发送消息时，机器人会自动通过 RCON 进行广播"
  },
  "Nhập Discord User ID cần thủ (Ví dụ: 1144785664458637394)...": {
    "en": "Enter Discord User ID (Example: 1144785664458637394)...",
    "ja": "Discord ユーザー ID を入力してください (例: 1144785664458637394)...",
    "cn": "输入 Discord 用户 ID（示例：1144785664458637394）..."
  },
  "Mô tả tập tính, môi trường sống và vẻ đẹp của loài cá này...": {
    "en": "Describe the behavior, habitat and beauty of this fish...",
    "ja": "この魚の行動、生息地、美しさを説明してください...",
    "cn": "描述一下这种鱼的行为、栖息地和美丽......"
  },
  "Xem Trước Danh Sách Máy Chủ (Minecraft Server List Preview):": {
    "en": "Minecraft Server List Preview:",
    "ja": "Minecraft サーバー リスト プレビュー:",
    "cn": "Minecraft 服务器列表预览："
  },
  "Chỉ những người chơi trong danh sách whitelist mới được vào.": {
    "en": "Only players on the whitelist can enter.",
    "ja": "ホワイトリストに登録されているプレイヤーのみが参加できます。",
    "cn": "只有白名单上的玩家才能进入。"
  },
  "Chúng tôi tôn trọng quyền riêng tư của người dùng và cam kết": {
    "en": "We respect user privacy and are committed",
    "ja": "私たちはユーザーのプライバシーを尊重し、全力を尽くします",
    "cn": "我们尊重用户隐私并承诺"
  },
  "Xác thực quyền quản trị khi bạn đăng nhập vào Web Dashboard.": {
    "en": "Authenticate administrative rights when you log in to the Web Dashboard.",
    "ja": "Web ダッシュボードにログインするときに管理者権限を認証します。",
    "cn": "登录 Web 仪表板时验证管理权限。"
  },
  "Ví dụ: Mình nên tập trung điều gì trong công việc tháng này?": {
    "en": "For example: What should I focus on at work this month?",
    "ja": "例: 今月は仕事で何に重点を置くべきですか?",
    "cn": "例如：这个月工作中我应该关注什么？"
  },
  "Chọn ảnh GIF, PNG, JPG, WEBP (tối đa 5MB). Hỗ trợ GIF động.": {
    "en": "Choose GIF, PNG, JPG, WEBP images (maximum 5MB). Supports animated GIFs.",
    "ja": "GIF、PNG、JPG、WEBP 画像 (最大 5MB) を選択します。アニメーションGIFをサポートします。",
    "cn": "选择 GIF、PNG、JPG、WEBP 图像（最大 5MB）。支持动画 GIF。"
  },
  "https://images.unsplash.com/... (Để trống nếu dùng màu nền)": {
    "en": "https://images.unsplash.com/... (Leave blank if using background color)",
    "ja": "https://images.unsplash.com/... (背景色を使用する場合は空白のままにします)",
    "cn": "https://images.unsplash.com/...（如果使用背景颜色则留空）"
  },
  "Chọn game để chơi ngay trên trình duyệt — không cần Discord": {
    "en": "Choose a game to play right in your browser — no Discord required",
    "ja": "ブラウザで直接プレイするゲームを選択してください - Discord は必要ありません",
    "cn": "选择直接在浏览器中玩的游戏 - 无需 Discord"
  },
  "Cần cụm 2 từ, từ sau phải bắt đầu bằng từ cuối của từ trước": {
    "en": "Need a 2-word phrase, the next word must start with the last word of the previous word",
    "ja": "2 単語のフレーズが必要です。次の単語は前の単語の最後の単語から始まる必要があります",
    "cn": "需要 2 个单词的短语，下一个单词必须从上一个单词的最后一个单词开始"
  },
  ". User thường chỉ thấy server của mình, admin thấy toàn bộ.": {
    "en": ". Users usually only see their server, admins see everything.",
    "ja": "。通常、ユーザーには自分のサーバーのみが表示され、管理者にはすべてが表示されます。",
    "cn": "。用户通常只能看到他们的服务器，管理员可以看到一切。"
  },
  "[SakuraBot] Đang lắng nghe luồng log từ Minecraft server...": {
    "en": "[SakuraBot] Listening to the log stream from the Minecraft server...",
    "ja": "[SakuraBot] Minecraft サーバーからのログ ストリームを聞いています...",
    "cn": "[SakuraBot] 正在监听 Minecraft 服务器的日志流..."
  },
  "Bật/tắt tổng thể ở tab Cài đặt chung. Dưới đây là chi tiết.": {
    "en": "General toggle on/off in General Settings tab. Here are the details.",
    "ja": "一般設定タブで一般のオン/オフを切り替えます。詳細は次のとおりです。",
    "cn": "在常规设置选项卡中打开/关闭常规开关。以下是详细信息。"
  },
  "Chọn 1 thành viên bên trên — hoặc nhập ID thủ công bên dưới": {
    "en": "Select a member above — or enter the ID manually below",
    "ja": "上でメンバーを選択するか、下に ID を手動で入力します",
    "cn": "在上面选择一个成员 — 或在下面手动输入 ID"
  },
  "Hoặc nhập ID Discord thủ công (nhiều ID cách nhau dấu phẩy)": {
    "en": "Or enter Discord ID manually (multiple IDs separated by commas)",
    "ja": "または、Discord ID を手動で入力します (複数の ID をカンマで区切ります)",
    "cn": "或者手动输入Discord ID（多个ID用逗号分隔）"
  },
  "/discord [link <mã_liên_kết> | transfer <số_coin> | status]": {
    "en": "/discord [link <link_code> | transfer <number_coin> | status]",
    "ja": "/discord [リンク <リンクコード> | <数値_コイン> を転送 |ステータス】",
    "cn": "/discord [链接 <链接代码> |转账 <number_coin> |状态]"
  },
  "Bảo trì máy chủ định kỳ để tối ưu hóa hiệu suất và bảo mật.": {
    "en": "Regular server maintenance to optimize performance and security.",
    "ja": "パフォーマンスとセキュリティを最適化するための定期的なサーバー メンテナンス。",
    "cn": "定期维护服务器以优化性能和安全性。"
  },
  "Đổi nickname nạn nhân (cần bot có quyền Manage Nicknames).": {
    "en": "Change the victim's nickname (requires bot to have Manage Nicknames permission).",
    "ja": "被害者のニックネームを変更します (ボットにニックネームの管理権限が必要です)。",
    "cn": "更改受害者的昵称（需要机器人具有管理昵称权限）。"
  },
  "Chủ sở hữu Bot (Owner) và tất cả người dùng được cấp quyền": {
    "en": "Bot owner (Owner) and all authorized users",
    "ja": "ボット所有者 (Owner) とすべての許可されたユーザー",
    "cn": "机器人所有者（Owner）和所有授权用户"
  },
  "🌸 Sakura MC Console — Đang kết nối đến WebSocket server...": {
    "en": "🌸 Sakura MC Console — Connecting to WebSocket server...",
    "ja": "🌸 さくら MC コンソール — WebSocket サーバーに接続中...",
    "cn": "💕 Sakura MC 控制台 — 连接到 WebSocket 服务器..."
  },
  "Cổng mạng để người chơi kết nối vào game (mặc định 25565).": {
    "en": "Network port for players to connect to the game (default 25565).",
    "ja": "プレーヤーがゲームに接続するためのネットワーク ポート (デフォルトは 25565)。",
    "cn": "玩家连接游戏的网络端口（默认25565）。"
  },
  "Cổng kết nối dành riêng cho console RCON (mặc định 25575).": {
    "en": "Connection port reserved for RCON console (default 25575).",
    "ja": "RCON コンソール用に予約されている接続ポート (デフォルトは 25575)。",
    "cn": "为 RCON 控制台保留的连接端口（默认 25575）。"
  },
  "Dán link YouTube để xem mô tả chi tiết của video hiện tại.": {
    "en": "Paste the YouTube link to see a detailed description of the current video.",
    "ja": "YouTube リンクを貼り付けると、現在のビデオの詳細な説明が表示されます。",
    "cn": "粘贴 YouTube 链接可查看当前视频的详细说明。"
  },
  "Tránh kick người chơi nếu server nghi ngờ họ bay lơ lửng.": {
    "en": "Avoid kicking players if the server suspects they are floating.",
    "ja": "サーバーがプレイヤーがフローティングしていると疑う場合は、プレイヤーをキックしないでください。",
    "cn": "如果服务器怀疑玩家漂浮，请避免踢他们。"
  },
  "Liên kết tài khoản in-game với Discord SakuraBot qua lệnh": {
    "en": "Link in-game account to Discord SakuraBot via command",
    "ja": "コマンド経由でゲーム内アカウントを Discord のサクラボットにリンクする",
    "cn": "通过命令将游戏内帐户链接到 Discord SakuraBot"
  },
  "Sau khi rút bài, hãy bấm AI luận giải để nhận thông điệp.": {
    "en": "After drawing the cards, press AI interpretation to receive the message.",
    "ja": "カードを引いたらAI通訳を押すとメッセージが届きます。",
    "cn": "抽完牌后，按AI解读即可接收消息。"
  },
  "Từ mời bot đến cấu hình server — tất cả chỉ trong 3 bước": {
    "en": "From inviting bots to configuring the server — all in just 3 steps",
    "ja": "ボットの招待からサーバーの構成まで、すべてわずか 3 ステップで完了",
    "cn": "从邀请机器人到配置服务器 - 只需 3 个步骤"
  },
  "Vật phẩm troll dùng để tặng hoặc gắn vào cần người khác.": {
    "en": "Troll items are used to give or attach to other people's rods.",
    "ja": "トロール アイテムは、他の人にロッドを与えたり、ロッドに取り付けたりするために使用されます。",
    "cn": "巨魔物品用于赠送或附加到其他人的鱼竿上。"
  },
  "Kích nổ quả bom cảm tử trừ coin ngẫu nhiên của cả 2 bên.": {
    "en": "Detonate a suicide bomb that deducts random coins from both sides.",
    "ja": "自爆爆弾を爆発させると、両側からランダムなコインが減ります。",
    "cn": "引爆自杀式炸弹，双方随机扣除硬币。"
  },
  ": chỉ chặn đúng cụm → \"linh béo\" không chặn \"linh béo ú\"": {
    "en": ": only blocks the correct phrase → \"fat soul\" does not block \"fat soul\"",
    "ja": ": 正しいフレーズのみをブロックします → 「fat soul」は「fat soul」をブロックしません",
    "cn": "：只屏蔽正确的短语→“fat Soul”不屏蔽“fat Soul”"
  },
  "Whitelist domain (mỗi dòng 1 domain, cách nhau dấu phẩy)": {
    "en": "Whitelist domains (1 domain per line, separated by commas)",
    "ja": "ホワイトリスト ドメイン (1 行に 1 つのドメイン、カンマで区切る)",
    "cn": "白名单域（每行 1 个域，以逗号分隔）"
  },
  "📜 Kênh Nội Quy & Xác Minh Thành Viên (Rule Verification)": {
    "en": "📜 Rules & Member Verification Channel (Rule Verification)",
    "ja": "📜 ルールとメンバー検証チャンネル (ルール検証)",
    "cn": "📜 规则及会员验证通道（规则验证）"
  },
  "Ví dụ: linhxinh hoặc Discord ID (1144785664458637394)...": {
    "en": "For example: linhxinh or Discord ID (1144785664458637394)...",
    "ja": "例: linhxinh または Discord ID (1144785664458637394)...",
    "cn": "例如：linhxinh 或 Discord ID (1144785664458637394)..."
  },
  "⚙️ Lệnh Admin cấu hình và nạp lại hệ thống ngồi in-game.": {
    "en": "⚙️ Admin command to configure and reload the in-game system.",
    "ja": "⚙️ ゲーム内システムを設定およびリロードするための管理コマンド。",
    "cn": "⚙️ 用于配置和重新加载游戏内系统的管理命令。"
  },
  "Xem bảng xếp hạng và các chỉ số quan trọng trong server.": {
    "en": "View rankings and important indicators in the server.",
    "ja": "サーバー内のランキングと重要な指標を表示します。",
    "cn": "查看服务器内的排名及重要指标。"
  },
  "Banner & Avatar → Bio → Mạng Xã Hội → Liên Kết → Donate": {
    "en": "Banner & Avatar → Bio → Social Network → Link → Donate",
    "ja": "バナーとアバター → 自己紹介 → ソーシャルネットワーク → リンク → 寄付",
    "cn": "横幅和头像 → 个人简介 → 社交网络 → 链接 → 捐赠"
  },
  "Ví dụ: Chỉ câu được vào mùa bão, Hoặc mua từ Chợ Đen...": {
    "en": "For example: Can only fish during storm season, Or buy from the Black Market...",
    "ja": "例: 嵐の季節にしか釣りができない、またはブラック マーケットから購入できる...",
    "cn": "例如：只能在暴风雨季节钓鱼，或者从黑市购买......"
  },
  "🌸 Sakura Bot - Bảng Điều Khiển Quản Lý (Web Dashboard)": {
    "en": "🌸 Sakura Bot - Management Dashboard (Web Dashboard)",
    "ja": "🌸 さくらボット - 管理ダッシュボード（Webダッシュボード）",
    "cn": "😍 Sakura Bot - 管理仪表板（Web 仪表板）"
  },
  "Timeout / Mute tạm thời nạn nhân trong server Discord.": {
    "en": "Timeout / Temporarily Mute the victim in the Discord server.",
    "ja": "タイムアウト / Discord サーバーで被害者を一時的にミュートします。",
    "cn": "超时/暂时将 Discord 服务器中的受害者静音。"
  },
  "📜 Kênh Ghi Nhật Ký Game (Join, Quit, Chết, Thành tựu):": {
    "en": "📜 Game Log Channel (Join, Quit, Death, Achievement):",
    "ja": "📜 ゲームログチャンネル (参加、終了、死亡、達成):",
    "cn": "📜 游戏日志通道（加入、退出、死亡、成就）："
  },
  "Thiết lập kênh cho các mini game đã tích hợp trong bot": {
    "en": "Set up channels for mini games integrated into the bot",
    "ja": "ボットに統合されたミニゲーム用のチャンネルを設定する",
    "cn": "设置集成到机器人中的小游戏的频道"
  },
  "🔴 Ẩn vật phẩm khỏi Cửa Hàng (Người chơi không thể mua)": {
    "en": "🔴 Hide items from the Store (Players cannot buy)",
    "ja": "🔴 ストアからアイテムを非表示にする (プレイヤーは購入できません)",
    "cn": "🔴隐藏商店中的物品（玩家无法购买）"
  },
  "🔍 Tìm kiếm thành tựu theo tên, mô tả hoặc danh hiệu...": {
    "en": "🔍 Search achievements by name, description or title...",
    "ja": "🔍 名前、説明、タイトルで実績を検索...",
    "cn": "🔍 按名称、描述或标题搜索成就..."
  },
  "Chế độ chơi khởi đầu khi người chơi tham gia thế giới.": {
    "en": "The game mode begins when the player joins the world.",
    "ja": "ゲームモードは、プレイヤーがワールドに参加すると始まります。",
    "cn": "当玩家加入世界时，游戏模式就开始了。"
  },
  "Ảnh hưởng lượng sát thương và mức độ quái vật sinh ra.": {
    "en": "Affects the amount of damage and level of monsters spawned.",
    "ja": "ダメージ量と出現するモンスターのレベルに影響します。",
    "cn": "影响所产生的怪物的伤害量和等级。"
  },
  "Cần thiết để bot điều khiển server và chạy lệnh từ xa.": {
    "en": "Necessary for the bot to control the server and run commands remotely.",
    "ja": "ボットがサーバーを制御し、コマンドをリモートで実行するために必要です。",
    "cn": "机器人远程控制服务器和运行命令所必需的。"
  },
  "Đăng ký tài khoản để sử dụng các tính năng của server.": {
    "en": "Register an account to use the server's features.",
    "ja": "サーバーの機能を使用するにはアカウントを登録します。",
    "cn": "注册一个帐户以使用服务器的功能。"
  },
  "Cơ sở dữ liệu này hiện chưa có bảng hoặc dữ liệu nào.": {
    "en": "This database currently has no tables or data.",
    "ja": "現在、このデータベースにはテーブルやデータがありません。",
    "cn": "该数据库当前没有表或数据。"
  },
  "🎨 Scribble It! — Trò chơi Vẽ & Đoán từ như Skribbl.io": {
    "en": "🎨 Scribble It! — Drawing & Guessing Word Games like Skribbl.io",
    "ja": "🎨 落書きしてみよう！ — Skribbl.io のような描画と推測の単語ゲーム",
    "cn": "🎨 乱写乱画！ — 像 Skribbl.io 这样的绘画和猜测文字游戏"
  },
  "và Slash commands được đồng bộ trực tiếp từ hệ thống.": {
    "en": "and Slash commands are synchronized directly from the system.",
    "ja": "およびスラッシュ コマンドはシステムから直接同期されます。",
    "cn": "和 Slash 命令直接从系统同步。"
  },
  "Vui lòng nhập Discord User ID vào ô phía trên và nhấn": {
    "en": "Please enter Discord User ID in the box above and click",
    "ja": "上のボックスに Discord ユーザー ID を入力し、クリックしてください。",
    "cn": "请在上面的框中输入 Discord 用户 ID，然后单击"
  },
  "trong 10 phút. Bị chặn bởi Khiên hoặc Gương phản đòn!": {
    "en": "for 10 minutes. Blocked by Shield or Counterattack Mirror!",
    "ja": "10分間。シールドまたは反撃ミラーでブロックされる!",
    "cn": "10分钟。被盾牌或反击镜格挡！"
  },
  "Vai trò (Role) nhận khi thành viên bấm Đồng ý quy tắc": {
    "en": "Role is received when the member clicks Agree to the rules",
    "ja": "メンバーがルールに同意するをクリックすると、役割が付与されます",
    "cn": "当成员单击“同意规则”时，就会收到角色"
  },
  "[Sakura MC] Đang khởi tạo kết nối Terminal Console...": {
    "en": "[Sakura MC] Initializing Terminal Console connection...",
    "ja": "[さくらMC] ターミナルコンソール接続を初期化しています...",
    "cn": "[Sakura MC] 正在初始化终端控制台连接..."
  },
  "Cầu Nối Trò Chuyện Trực Tuyến (Discord <—> Minecraft)": {
    "en": "Online Chat Bridge (Discord <—> Minecraft)",
    "ja": "オンライン チャット ブリッジ (Discord <—> Minecraft)",
    "cn": "在线聊天桥（Discord <—> Minecraft）"
  },
  "Liên kết tải trực tiếp tệp .zip texture pack máy chủ.": {
    "en": "Direct download link for the server texture pack .zip file.",
    "ja": "サーバー テクスチャ パック .zip ファイルの直接ダウンロード リンク。",
    "cn": "服务器纹理包 .zip 文件的直接下载链接。"
  },
  "đọc hoặc lưu trữ tin nhắn riêng tư (Direct Messages),": {
    "en": "read or store private messages (Direct Messages),",
    "ja": "プライベート メッセージ (ダイレクト メッセージ) の読み取りまたは保存、",
    "cn": "读取或存储私人消息（私信），"
  },
  "Truy vấn hợp lệ nhưng không trả về dòng dữ liệu nào.": {
    "en": "The query is valid but returns no rows of data.",
    "ja": "クエリは有効ですが、データ行が返されません。",
    "cn": "查询有效，但未返回任何数据行。"
  },
  "Nạp lại toàn bộ Cogs trong Command, Anti, Log": {
    "en": "Reload all Cogs in Command, Anti, Log",
    "ja": "Command、Anti、Log のすべての Cog をリロードします",
    "cn": "重新加载 Command、Anti、Log 中的所有 Cogs"
  },
  "Phòng trò chuyện toàn cầu kết nối cộng đồng Sakura •": {
    "en": "Global chat room connecting the Sakura community •",
    "ja": "サクラコミュニティをつなぐグローバルチャットルーム •",
    "cn": "连接樱花社区的全球聊天室 •"
  },
  "Bảo vệ Server khỏi hành vi xóa kênh / role hàng loạt": {
    "en": "Protect Server from mass deletion of channels/roles",
    "ja": "チャネル/ロールの一括削除からサーバーを保護",
    "cn": "保护服务器免遭大规模删除频道/角色"
  },
  "Đá nạn nhân văng ra khỏi phòng Voice đang đàm thoại.": {
    "en": "Kick the victim out of the room where Voice is talking.",
    "ja": "ボイスが話している部屋から被害者を追い出します。",
    "cn": "将受害者踢出 Voice 正在说话的房间。"
  },
  "Mật khẩu xác thực cho kết nối điều khiển RCON từ xa.": {
    "en": "Authentication password for remote RCON control connection.",
    "ja": "リモート RCON 制御接続用の認証パスワード。",
    "cn": "远程RCON控制连接的验证密码。"
  },
  "Các máy chủ được tự động phát hiện trong thư mục bot": {
    "en": "The servers are automatically discovered in the bot directory",
    "ja": "サーバーはボット ディレクトリで自動的に検出されます",
    "cn": "服务器会在 bot 目录中自动发现"
  },
  "Xem danh sách các khu vực đã claim và quản lý chúng.": {
    "en": "View a list of claimed areas and manage them.",
    "ja": "権利主張のある地域のリストを表示し、管理します。",
    "cn": "查看已声明区域的列表并对其进行管理。"
  },
  "Làm sao để bot gán vai trò khi lên cấp (Level Role)?": {
    "en": "How can the bot assign roles when leveling up (Level Role)?",
    "ja": "レベルアップ時にボットはどのように役割を割り当てることができますか (レベル役割)?",
    "cn": "机器人升级时如何分配角色（Level Role）？"
  },
  "Đổi tên tài khoản. Không được trùng với người khác.": {
    "en": "Rename account. Do not overlap with others.",
    "ja": "アカウントの名前を変更します。他の人と重ならないようにしてください。",
    "cn": "重命名帐户。不要与其他人重叠。"
  },
  "Không tìm thấy dòng dữ liệu nào khớp với điều kiện.": {
    "en": "No data lines were found that matched the condition.",
    "ja": "条件に一致するデータ行は見つかりませんでした。",
    "cn": "未找到与条件匹配的数据线。"
  },
  ". Hệ thống tự động lọc chỉ hiện server bạn có quyền": {
    "en": ". The system automatically filters only the server you have permission to display",
    "ja": "。システムは、表示権限のあるサーバーのみを自動的にフィルタリングします。",
    "cn": "。系统自动过滤仅您有权限显示的服务器"
  },
  "🌈 Cầu Vồng Thần Nông (x1.5 tốc độ & Siêu Đột Biến!)": {
    "en": "🌈 Rainbow Scorpio (x1.5 speed & Super Mutation!)",
    "ja": "🌈 レインボースコーピオ (x1.5 スピード & スーパーミューテーション!)",
    "cn": "🌈 彩虹天蝎座（x1.5 速度和超级变异！）"
  },
  "Khi bot chưa được duyệt chính thức trên Top.gg, hãy": {
    "en": "When the bot has not been officially approved on Top.gg, please",
    "ja": "Top.ggでボットが正式に承認されていない場合は、",
    "cn": "当该机器人尚未在 Top.gg 上正式批准时，请"
  },
  "Nhập Tên Đăng Nhập (Username) hoặc Discord User ID:": {
    "en": "Enter Username or Discord User ID:",
    "ja": "ユーザー名または Discord ユーザー ID を入力してください:",
    "cn": "输入用户名或 Discord 用户 ID："
  },
  "🔥 Quản Lý Kênh Điểm Danh Giữ Chuỗi (Channel Streak)": {
    "en": "🔥 Channel Streak Management",
    "ja": "🔥 チャンネルストリーク管理",
    "cn": "🔥 频道连续管理"
  },
  "🔍 Tìm kiếm cao thủ theo Tên hoặc Discord User ID...": {
    "en": "🔍 Search for players by Name or Discord User ID...",
    "ja": "🔍 名前または Discord ユーザー ID でプレイヤーを検索...",
    "cn": "🔍 按姓名或 Discord 用户 ID 搜索玩家..."
  },
  "Nhập Discord User ID (ví dụ: 123456789012345678)...": {
    "en": "Enter Discord User ID (ex: 123456789012345678)...",
    "ja": "Discord ユーザー ID を入力してください (例: 123456789012345678)...",
    "cn": "输入 Discord 用户 ID（例如：123456789012345678）..."
  },
  "Nhập lời giới thiệu ngắn về bot trong server này...": {
    "en": "Enter a short introduction about the bot in this server...",
    "ja": "このサーバーのボットに関する簡単な紹介文を入力してください...",
    "cn": "输入有关此服务器中机器人的简短介绍..."
  },
  "Kiểm tra plugin đã bật mà không có lỗi nghiêm trọng": {
    "en": "Check the plugin is enabled without fatal errors",
    "ja": "致命的なエラーが発生せずにプラグインが有効になっていることを確認します",
    "cn": "检查插件是否启用，没有致命错误"
  },
  "Hỗ trợ GIF động (nếu file là GIF sẽ giữ animation)": {
    "en": "Animated GIF support (if the file is a GIF, it will keep the animation)",
    "ja": "アニメーション GIF のサポート (ファイルが GIF の場合、アニメーションは保持されます)",
    "cn": "动画GIF支持（如果文件是GIF，它将保留动画）"
  },
  "vd: Cảm ơn bạn đã luôn đồng hành và ủng hộ mình! 💖": {
    "en": "eg: Thank you for always accompanying and supporting me! 💖",
    "ja": "例：いつも付き添って応援してくれてありがとう！ 💖",
    "cn": "例如：感谢您一直以来的陪伴和支持！ 💖"
  },
  "Gửi ảnh hoặc âm thanh hù dọa bất ngờ tới nạn nhân.": {
    "en": "Sending suddenly threatening images or sounds to the victim.",
    "ja": "被害者に突然脅迫的な画像や音声を送信する。",
    "cn": "突然向受害者发送威胁性图像或声音。"
  },
  "Cụm 2 từ tiếng Việt (ví dụ: \"hoa hồng\", \"nhà cửa\")": {
    "en": "Phrase of 2 Vietnamese words (for example: \"rose\", \"house\")",
    "ja": "ベトナム語 2 単語のフレーズ (例: 「バラ」、「家」)",
    "cn": "2 个越南语单词组成的短语（例如：“rose”、“house”）"
  },
  "Chọn 1 thành viên bên trên — hoặc nhập ID thủ công": {
    "en": "Select a member above — or enter the ID manually",
    "ja": "上でメンバーを選択するか、ID を手動で入力します",
    "cn": "选择上方的成员 — 或手动输入 ID"
  },
  "📎 Tệp đính kèm (Ảnh, File tài liệu, Zip... < 25MB)": {
    "en": "📎 Attachments (Photos, Document Files, Zip... < 25MB)",
    "ja": "📎 添付ファイル (写真、ドキュメントファイル、Zip... < 25MB)",
    "cn": "📎 附件（照片、文档文件、Zip...< 25MB）"
  },
  "✨ Discord Bot Đa Năng • Online 24/7 • Tiếng Việt 🌸": {
    "en": "✨ Discord Bot Multipurpose • Online 24/7 • Vietnamese 🌸",
    "ja": "✨ Discord ボット多目的 • 24 時間 365 日オンライン • ベトナム語 🌸",
    "cn": "✨ Discord Bot 多用途 • 在线 24/7 • 越南语 💕"
  },
  "Tin nhắn được đồng bộ tức thì giữa game và Discord": {
    "en": "Messages are instantly synced between the game and Discord",
    "ja": "メッセージはゲームと Discord の間で即座に同期されます",
    "cn": "消息在游戏和 Discord 之间立即同步"
  },
  "Bấm vào nút tải xuống trên trang plugin, chọn file": {
    "en": "Click the download button on the plugin page, select the file",
    "ja": "プラグインページのダウンロードボタンをクリックし、ファイルを選択します",
    "cn": "点击插件页面的下载按钮，选择文件"
  },
  "Đặt vị trí nhà của bạn để có thể quay lại dễ dàng.": {
    "en": "Set your home location so you can get back easily.",
    "ja": "簡単に帰宅できるように自宅の場所を設定します。",
    "cn": "设置您的家庭位置，以便您可以轻松返回。"
  },
  "Chia đôi màn hình: Mã nguồn & Xem trước trực tiếp": {
    "en": "Split Screen: Source Code & Live Preview",
    "ja": "分割画面: ソースコードとライブプレビュー",
    "cn": "分屏：源代码和实时预览"
  },
  "Tic-Tac-Toe 2 người hoặc vs Bot Sakura, tính điểm": {
    "en": "Tic-Tac-Toe 2 people or vs Bot Sakura, score",
    "ja": "三目並べ 2人 or vs Botさくら、スコア",
    "cn": "井字棋 2 人或 Bot Sakura，得分"
  },
  "Word Chain Việt Nam — nối chữ như Discord, vs Bot": {
    "en": "Word Chain Vietnam — connect words like Discord, vs Bot",
    "ja": "Word Chain Vietnam — Discord、vs Bot などの単語を接続します",
    "cn": "Word Chain Vietnam — 连接诸如 Discord、vs Bot 之类的单词"
  },
  "trước. Mặc định đăng vào kênh Confession đã chọn.": {
    "en": "before. By default, posting to the selected Confession channel.",
    "ja": "前に。デフォルトでは、選択した告白チャンネルに投稿します。",
    "cn": "之前。默认情况下，发布到选定的忏悔频道。"
  },
  "Xem số dư tài sản của bạn trong hệ thống tiền tệ.": {
    "en": "View your asset balance in the currency system.",
    "ja": "通貨システムで資産残高を表示します。",
    "cn": "查看您在货币系统中的资产余额。"
  },
  "Trình duyệt của bạn không hỗ trợ thẻ video HTML5.": {
    "en": "Your browser does not support HTML5 video tags.",
    "ja": "お使いのブラウザは HTML5 ビデオ タグをサポートしていません。",
    "cn": "您的浏览器不支持 HTML5 视频标签。"
  },
  "Tự động chặn tin nhắn spam và link mời trái phép": {
    "en": "Automatically block spam messages and unauthorized invitation links",
    "ja": "スパムメッセージと不正な招待リンクを自動的にブロックします",
    "cn": "自动拦截垃圾邮件和未经授权的邀请链接"
  },
  "Nếu tắt, mọi invite đều bị xóa kể cả của server.": {
    "en": "If turned off, all invites will be deleted, including those from the server.",
    "ja": "オフにすると、サーバーからの招待も含め、すべての招待が削除されます。",
    "cn": "如果关闭，所有邀请都将被删除，包括来自服务器的邀请。"
  },
  "🏅 Phần Thưởng Role Theo Mốc Cấp Độ (Level Roles)": {
    "en": "🏅 Level Roles Rewards",
    "ja": "🏅 レベルの役割報酬",
    "cn": "🏅 等级角色奖励"
  },
  "🔑 Quản Lý Từ Khóa Phản Hồi Tự Động (Custom Keys)": {
    "en": "🔑 Automatic Response Keyword Management (Custom Keys)",
    "ja": "🔑 自動応答キーワード管理 (カスタムキー)",
    "cn": "🔑 自动响应关键字管理（自定义键）"
  },
  "Nhập Discord User ID cần thủ để xem Thủy Cung...": {
    "en": "Enter your Discord User ID to view the Aquarium...",
    "ja": "水族館を表示するには、Discord ユーザー ID を入力してください...",
    "cn": "输入您的 Discord 用户 ID 以查看水族馆..."
  },
  "Sakura Bot • Chúc bạn có những giây phút vui vẻ!": {
    "en": "Sakura Bot • Wish you have fun moments!",
    "ja": "さくらボット • 楽しいひとときをお過ごしください。",
    "cn": "Sakura Bot •祝您度过愉快的时光！"
  },
  "Tỉ lệ xuất hiện khi thành viên câu cá thành công": {
    "en": "Odds appear when the member fishes successfully",
    "ja": "メンバーが釣りに成功するとオッズが表示されます",
    "cn": "会员钓鱼成功后出现赔率"
  },
  "Hệ số nhân khi bán cá (ví dụ 1.2 = +20% giá bán)": {
    "en": "Multiplier when selling fish (eg 1.2 = +20% selling price)",
    "ja": "魚を販売する際の乗数 (例: 1.2 = +20% 販売価格)",
    "cn": "出售鱼时的乘数（例如 1.2 = +20% 售价）"
  },
  "⚙️ Sakura MC — Cấu Hình server.properties & MOTD": {
    "en": "⚙️ Sakura MC — Server.properties & MOTD Configuration",
    "ja": "⚙️ さくら MC — Server.properties と MOTD 構成",
    "cn": "⚙️ Sakura MC — Server.properties 和 MOTD 配置"
  },
  "Icon Máy Chủ & Lời Chào (MOTD Preview Trực Quan)": {
    "en": "Server Icon & Greeting (MOTD Visual Preview)",
    "ja": "サーバーアイコンと挨拶（MOTDビジュアルプレビュー）",
    "cn": "服务器图标和问候语（MOTD 视觉预览）"
  },
  "Plugin giúp server của bạn mạnh hơn cùng Sakura.": {
    "en": "Plugins help your server become more powerful with Sakura.",
    "ja": "プラグインは、Sakura を使用してサーバーをより強力にするのに役立ちます。",
    "cn": "插件可帮助您的服务器通过 Sakura 变得更加强大。"
  },
  "Thông tin thu thập chỉ phục vụ cho các mục đích:": {
    "en": "Information collected is only for the following purposes:",
    "ja": "収集される情報は、次の目的のみに使用されます。",
    "cn": "收集的信息仅用于以下目的："
  },
  "Hãy thử nhập từ khóa khác hoặc chuyển danh mục.": {
    "en": "Try entering a different keyword or switching categories.",
    "ja": "別のキーワードを入力するか、カテゴリを切り替えてみてください。",
    "cn": "尝试输入不同的关键字或切换类别。"
  },
  "Trung Tâm Quản Trị Cửa Hàng & Sáng Tạo Vật Phẩm": {
    "en": "Store Management & Item Creation Center",
    "ja": "店舗管理＆アイテム作成センター",
    "cn": "商店管理和物品创建中心"
  },
  "Bảng Tra Cứu Key Lệnh & Hiệu Ứng Vật Phẩm Troll": {
    "en": "Troll Item Command & Effect Key Lookup Table",
    "ja": "トロールアイテムのコマンドと効果キーの検索表",
    "cn": "巨魔物品命令和效果键查找表"
  },
  "⚙️ Thiết Lập Kênh Discord Kết Nối Với Minecraft": {
    "en": "⚙️ Set up a Discord Channel Connecting to Minecraft",
    "ja": "⚙️ Minecraft に接続する Discord チャンネルをセットアップする",
    "cn": "⚙️ 设置连接到 Minecraft 的 Discord 频道"
  },
  "🪙 Đồng Bộ & Quy Đổi Coins Discord <-> Minecraft": {
    "en": "🪙 Synchronize & Convert Coins Discord <-> Minecraft",
    "ja": "🪙 コインの同期と変換 Discord <-> Minecraft",
    "cn": "🪙 同步和转换硬币 Discord <-> Minecraft"
  },
  "• Dừng đọc và rời khỏi voice bất cứ lúc nào với": {
    "en": "• Stop reading and leave the voice at any time",
    "ja": "• いつでも読み上げをやめて音声を残すことができます",
    "cn": "• 随时停止阅读并留下声音"
  },
  "🎮 Cấu Hình Thông Báo Giftcode Hoyoverse & Gacha": {
    "en": "🎮 Hoyoverse & Gacha Giftcode Notification Configuration",
    "ja": "🎮 Hoyoverse & ガチャギフトコード通知設定",
    "cn": "🎮 Hoyoverse & Gacha Giftcode 通知配置"
  },
  "Ví dụ: Discord Nitro, Thẻ Cào, 100.000 Coins...": {
    "en": "For example: Discord Nitro, Scratch Card, 100,000 Coins...",
    "ja": "例: Discord Nitro、スクラッチ カード、100,000 コイン...",
    "cn": "例如：Discord Nitro、刮刮卡、100,000 个金币..."
  },
  "Để trống để lắng nghe trên tất cả địa chỉ mạng.": {
    "en": "Leave blank to listen on all network addresses.",
    "ja": "すべてのネットワーク アドレスをリッスンするには、空白のままにします。",
    "cn": "留空以侦听所有网络地址。"
  },
  "Giới hạn số lượng người chơi tham gia cùng lúc.": {
    "en": "Limit the number of players participating at the same time.",
    "ja": "同時に参加するプレイヤーの数を制限します。",
    "cn": "限制同时参与的玩家数量。"
  },
  "Cho phép hoặc cấm người chơi tấn công lẫn nhau.": {
    "en": "Allow or prohibit players from attacking each other.",
    "ja": "プレイヤー同士の攻撃を許可または禁止します。",
    "cn": "允许或禁止玩家互相攻击。"
  },
  "Tự động sinh ra Zombie, Skeleton, Creeper, v.v.": {
    "en": "Automatically spawn Zombies, Skeletons, Creepers, etc.",
    "ja": "ゾンビ、スケルトン、クリーパーなどを自動的にスポーンします。",
    "cn": "自动生成僵尸、骷髅、苦力怕等。"
  },
  "Ví dụ: 4e1243bd22c66e76c2ba9eddc1f91394e57f9f83": {
    "en": "For example: 4e1243bd22c66e76c2ba9eddc1f91394e57f9f83",
    "ja": "例: 4e1243bd22c66e76c2ba9eddc1f91394e57f9f83",
    "cn": "例如：4e1243bd22c66e76c2ba9eddc1f91394e57f9f83"
  },
  "Tạo điểm warp để người chơi khác có thể đi đến.": {
    "en": "Create warp points that other players can go to.",
    "ja": "他のプレイヤーが行けるワープポイントを作成します。",
    "cn": "创建其他玩家可以前往的扭曲点。"
  },
  "Chỉ gồm chữ cái, số, gạch dưới hoặc gạch ngang": {
    "en": "Contains only letters, numbers, underscores or dashes",
    "ja": "文字、数字、アンダースコア、またはダッシュのみが含まれます",
    "cn": "仅包含字母、数字、下划线或破折号"
  },
  "Nhập câu lệnh SQL chỉ đọc (SELECT / PRAGMA)...": {
    "en": "Enter a read-only SQL statement (SELECT / PRAGMA)...",
    "ja": "読み取り専用 SQL ステートメント (SELECT / PRAGMA) を入力してください...",
    "cn": "输入只读 SQL 语句 (SELECT / PRAGMA)..."
  },
  "⭕ Caro XO (3×3 & Siêu Lớn 15×15) — Sakura Game": {
    "en": "⭕ Caro XO (3×3 & Super Large 15×15) — Sakura Game",
    "ja": "⭕ カロ XO (3×3 & 超大型 15×15) — サクラゲーム",
    "cn": "⭕ 卡罗 XO (3×3 & 超大 15×15) — 樱花游戏"
  },
  "🌸 © 2026 Sakura Bot • Phát triển bởi Đồng Linh": {
    "en": "🌸 © 2026 Sakura Bot • Developed by Dong Linh",
    "ja": "🌸 © 2026 さくらボット • 開発者: Dong Linh",
    "cn": "💕 © 2026 Sakura Bot • 由 Dong Linh 开发"
  },
  "Gửi tin nhắn troll hài hước kèm hiệu ứng động.": {
    "en": "Send funny troll messages with animated effects.",
    "ja": "アニメーション効果を使って面白い荒らしメッセージを送信します。",
    "cn": "发送带有动画效果的有趣的巨魔消息。"
  },
  "Ví dụ: \"Xin chào Sakura\" -> \"arukaS oàhc niX\".": {
    "en": "For example: \"Hello Sakura\" -> \"arukaS oàhc niX\".",
    "ja": "例：「こんにちはさくら」→「arukaS oàhc niX」。",
    "cn": "例如：“Hello Sakura”->“arukaS oàhc niX”。"
  },
  "Troll thông báo đỏ mà vào không thấy tin nhắn.": {
    "en": "Troll notices red but doesn't see the message.",
    "ja": "トロルは赤いことに気づきましたが、メッセージは見えませんでした。",
    "cn": "巨魔注意到红色但没有看到消息。"
  },
  "Vinh danh những bậc thầy nối chữ xuất sắc nhất": {
    "en": "Honoring the best word joining masters",
    "ja": "マスターに参加する最高の言葉を称える",
    "cn": "表彰最佳单词连接大师"
  },
  "Gửi panel Confession (kèm 2 nút) vào kênh. Nhớ": {
    "en": "Send the Confession panel (with 2 buttons) to the channel. Remember",
    "ja": "告白パネル (2 つのボタン付き) をチャンネルに送信します。覚えておいてください",
    "cn": "将 Confession 面板（带有 2 个按钮）发送到频道。记住"
  },
  "Kênh Log Sự Kiện (Join/Quit/Death/Advancement)": {
    "en": "Event Log Channel (Join/Quit/Death/Advancement)",
    "ja": "イベントログチャンネル (参加/終了/死亡/進行)",
    "cn": "事件日志通道（加入/退出/死亡/晋级）"
  },
  "🔍 Tìm kiếm theo Discord ID hoặc tên bạn đời...": {
    "en": "🔍 Search by Discord ID or partner name...",
    "ja": "🔍 Discord IDまたはパートナー名で検索...",
    "cn": "🔍 按 Discord ID 或合作伙伴名称搜索..."
  },
  "của máy chủ Paper/Spigot/Bukkit bạn đang chạy.": {
    "en": "of the Paper/Spigot/Bukkit server you are running.",
    "ja": "実行している Paper/Spigot/Bukkit サーバーの。",
    "cn": "您正在运行的 Paper/Spigot/Bukkit 服务器的名称。"
  },
  "/shop [danh_mục] [danh_mục_con] | /shop reload": {
    "en": "/shop [category] [subcategory] | /shop reload",
    "ja": "/shop [カテゴリ] [サブカテゴリ] | /ショップリロード",
    "cn": "/shop [类别] [子类别] | /商店重新加载"
  },
  "Trao đổi vật phẩm an toàn với người chơi khác.": {
    "en": "Safely exchange items with other players.",
    "ja": "他のプレイヤーと安全にアイテムを交換できます。",
    "cn": "与其他玩家安全地交换物品。"
  },
  "Câu hỏi hoặc bối cảnh của bạn (không bắt buộc)": {
    "en": "Your question or context (optional)",
    "ja": "質問または背景 (オプション)",
    "cn": "您的问题或背景（可选）"
  },
  "⚡ Tệp này là một Extension Cog của SakuraBot:": {
    "en": "⚡ This file is an Extension Cog of SakuraBot:",
    "ja": "⚡ このファイルはSakuraBotの拡張Cogです:",
    "cn": "⚡ 这个文件是 SakuraBot 的扩展齿轮："
  },
  "Phân quyền Quản trị & Owner hoạt động ra sao?": {
    "en": "How does decentralization of Administration & Ownership work?",
    "ja": "管理と所有権の分散化はどのように機能しますか?",
    "cn": "管理和所有权的分散化如何运作？"
  },
  "🚀 Áp Dụng Môi Trường Nông Nghiệp Ngay Lập Tức": {
    "en": "🚀 Apply Agricultural Environment Immediately",
    "ja": "🚀 農業環境をすぐに適用する",
    "cn": "🚀立即应用农业环境"
  },
  "Thao Túng Tỉ Lệ Khai Thác Mỏ & Cường Hóa Cuốc": {
    "en": "Manipulate Mining Rate & Enhance Pickaxe",
    "ja": "採掘速度を操作し、つるはしを強化する",
    "cn": "操纵采矿率并增强镐"
  },
  "Lavalink Music, Falix & Điểm Danh (config.py)": {
    "en": "Lavalink Music, Falix & Attendance (config.py)",
    "ja": "Lavalink 音楽、Falix、出席 (config.py)",
    "cn": "Lavalink 音乐、Falix 和考勤 (config.py)"
  },
  "Quản Trị Danh Sách Admin Web (Phân Quyền Web)": {
    "en": "Managing the Web Admin List (Web Authorization)",
    "ja": "Web管理者リストの管理（Web認証）",
    "cn": "管理 Web 管理员列表（Web 授权）"
  },
  "Bật/tắt và cấu hình lệnh mod — đã loại trừ MC": {
    "en": "Enable/disable and configure mod commands — MC excluded",
    "ja": "mod コマンドの有効化/無効化と設定 - MC を除く",
    "cn": "启用/禁用和配置 mod 命令 — MC 除外"
  },
  "Quản lý và xóa các bảng Reaction Role đã đăng": {
    "en": "Manage and delete posted Reaction Role tables",
    "ja": "投稿されたリアクションロールテーブルの管理と削除",
    "cn": "管理和删除已发布的反应角色表"
  },
  "Nhập Discord ID (nhiều ID cách nhau dấu phẩy)": {
    "en": "Enter Discord ID (multiple IDs separated by commas)",
    "ja": "Discord ID を入力してください (複数の ID をカンマで区切ります)",
    "cn": "输入 Discord ID（多个 ID 以逗号分隔）"
  },
  "Nhập mã (ví dụ: ABC123 hoặc MCLINK-ABC123)...": {
    "en": "Enter the code (e.g. ABC123 or MCLINK-ABC123)...",
    "ja": "コードを入力してください (例: ABC123 または MCLINK-ABC123)...",
    "cn": "输入代码（例如 ABC123 或 MCLINK-ABC123）..."
  },
  "Buff cơ hội giữ lại mồi hoặc tăng lực hút mồi": {
    "en": "Buffs the chance to retain bait or increases bait attraction",
    "ja": "餌を保持する可能性を強化するか、餌の魅力を増加させます",
    "cn": "增加保留诱饵的机会或增加诱饵的吸引力"
  },
  "👤 Sakura MC — Quản Lý Người Chơi & Soi Túi Đồ": {
    "en": "👤 Sakura MC — Player Management & Inventory Check",
    "ja": "👤 さくら MC — 選手管理と在庫チェック",
    "cn": "👤 Sakura MC — 玩家管理和库存检查"
  },
  "Gói Tài Nguyên Máy Chủ (Server Resource Pack)": {
    "en": "Server Resource Pack",
    "ja": "サーバーリソースパック",
    "cn": "服务器资源包"
  },
  "⛏️ Sakura Hosting — Quản Lý Máy Chủ Minecraft": {
    "en": "⛏️ Sakura Hosting — Minecraft Server Management",
    "ja": "⛏️ さくらホスティング — Minecraft サーバー管理",
    "cn": "⛏️ Sakura Hosting — Minecraft 服务器管理"
  },
  "Mở trang xem trước trong tab trình duyệt mới": {
    "en": "Open the preview page in a new browser tab",
    "ja": "新しいブラウザタブでプレビューページを開きます",
    "cn": "在新的浏览器选项卡中打开预览页面"
  },
  "Cấp Phát / Điều Chỉnh Kinh Tế Cho Người Dùng": {
    "en": "Allocation / Economic Adjustment to Users",
    "ja": "ユーザーへの配分・経済的調整",
    "cn": "对用户的分配/经济调整"
  },
  "Bảng Xếp Hạng & Danh Sách Thành Tựu Minigame": {
    "en": "Minigame Leaderboard & Achievement List",
    "ja": "ミニゲームのリーダーボードと実績リスト",
    "cn": "小游戏排行榜和成就列表"
  },
  "⛏️ Cuốc Khai Khoáng (Hỗ trợ Cường Hóa & Sao)": {
    "en": "⛏️ Mining Pickaxe (Supports Enhancement & Stars)",
    "ja": "⛏️ 採掘ツルハシ (強化とスターをサポート)",
    "cn": "⛏️ 采矿镐（支持增强和星星）"
  },
  "Trung Tâm Quản Trị Hệ Thống Hôn Lễ & Cặp Đôi": {
    "en": "Wedding & Couple System Administration Center",
    "ja": "ウェディング＆カップルシステム管理センター",
    "cn": "婚礼情侣系统管理中心"
  },
  "Trung Tâm Quản Trị Hệ Thống Nông Trại Sakura": {
    "en": "Sakura Farm System Administration Center",
    "ja": "さくらファームシステム管理センター",
    "cn": "樱花农场系统管理中心"
  },
  "💬 Kênh Chat 2 Chiều (Discord <-> Minecraft):": {
    "en": "💬 2-Way Chat Channel (Discord <-> Minecraft):",
    "ja": "💬 双方向チャットチャンネル (Discord <-> Minecraft):",
    "cn": "💬 2 向聊天频道（Discord <-> Minecraft）："
  },
  "Mã Liên Kết (MCLINK-XXXXXX) hoặc Key Server:": {
    "en": "Link Code (MCLINK-XXXX) or Server Key:",
    "ja": "リンク コード (MCLINK-XXXX) またはサーバー キー:",
    "cn": "链接代码 (MCLINK-XXXX) 或服务器密钥："
  },
  "🌸 Trợ lý Discord đa năng cho server của bạn.": {
    "en": "🌸 Versatile Discord Assistant for your server.",
    "ja": "🌸 サーバー用の多機能な Discord アシスタント。",
    "cn": "为您的服务器提供多功能 Discord 助手。"
  },
  "Chưa có dữ liệu — bot sẽ ghi khi có vi phạm.": {
    "en": "No data yet — bot will record when there is a violation.",
    "ja": "データはまだありません。違反があった場合はボットが記録します。",
    "cn": "尚无数据 - 机器人会记录违规情况。"
  },
  "Vui lòng nhập mật khẩu quản trị để tiếp tục.": {
    "en": "Please enter your admin password to continue.",
    "ja": "続行するには管理者パスワードを入力してください。",
    "cn": "请输入您的管理员密码以继续。"
  },
  "Ví dụ: Nhẫn Cỏ, Nhẫn Vàng, Nhẫn Kim Cương...": {
    "en": "For example: Grass Ring, Gold Ring, Diamond Ring...",
    "ja": "例: グラスリング、ゴールドリング、ダイヤモンドリング...",
    "cn": "例如：草戒、金戒、钻戒……"
  },
  "🛡️ Sakura MC — Phân Quyền & Quản Lý Truy Cập": {
    "en": "🛡️ Sakura MC — Decentralization & Access Management",
    "ja": "🛡️ さくら MC — 分散化とアクセス管理",
    "cn": "🛡️ Sakura MC — 去中心化和访问管理"
  },
  "Quản lý, vật phẩm, nhiệm vụ, bảo vệ, kinh tế": {
    "en": "Management, items, quests, protection, economy",
    "ja": "管理、アイテム、クエスト、保護、経済",
    "cn": "管理、物品、任务、保护、经济"
  },
  "Chuyển tiền cho người chơi khác trên server.": {
    "en": "Transfer money to other players on the server.",
    "ja": "サーバー上の他のプレイヤーに送金します。",
    "cn": "向服务器上的其他玩家转账。"
  },
  "Gửi yêu cầu dịch chuyển đến người chơi khác.": {
    "en": "Send a teleport request to another player.",
    "ja": "別のプレイヤーにテレポート要求を送信します。",
    "cn": "向其他玩家发送传送请求。"
  },
  "Chấp nhận yêu cầu dịch chuyển từ người khác.": {
    "en": "Accept teleport requests from others.",
    "ja": "他の人からのテレポート要求を受け入れます。",
    "cn": "接受其他人的传送请求。"
  },
  "Đăng nhập vào tài khoản đã đăng ký trước đó.": {
    "en": "Log in to the previously registered account.",
    "ja": "先ほど登録したアカウントにログインします。",
    "cn": "登录之前注册的账号。"
  },
  "Đổi mật khẩu tài khoản riêng của người chơi.": {
    "en": "Change the player's own account password.",
    "ja": "プレイヤー自身のアカウントのパスワードを変更します。",
    "cn": "修改玩家自己的账号密码。"
  },
  "/changepassword <mật_khẩu_cũ> <mật_khẩu_mới>": {
    "en": "/changepassword <old_password> <new_password>",
    "ja": "/changepassword <古いパスワード> <新しいパスワード>",
    "cn": "/changepassword <旧密码> <新密码>"
  },
  "(không cần đăng nhập hoặc có thể đăng nhập)": {
    "en": "(no need to log in or can log in)",
    "ja": "(ログインする必要はありません、またはログインできます)",
    "cn": "（无需登录或可以登录）"
  },
  "Bảng Xếp Hạng & Danh Sách Thủy Cung Cần Thủ": {
    "en": "Rankings & List of Aquarium Anglers",
    "ja": "水族館釣り人のランキング＆リスト",
    "cn": "水族馆钓鱼者排名和列表"
  },
  "🔮 Vật phẩm troll ẩn (Chỉ rơi từ Rương/Drop)": {
    "en": "🔮 Hidden troll item (Only drops from Chest/Drop)",
    "ja": "🔮 隠しトロールアイテム (チェスト/ドロップからのみドロップ)",
    "cn": "🔮 隐藏的巨魔物品（仅从宝箱/掉落中掉落）"
  },
  "Prefix 1-5 ký tự và ngôn ngữ cho server này": {
    "en": "Prefix 1-5 characters and language for this server",
    "ja": "このサーバーのプレフィックス 1 ～ 5 文字と言語",
    "cn": "该服务器的前缀 1-5 个字符和语言"
  },
  "Phạm vi global — cấm mọi server (chỉ admin)": {
    "en": "Global scope — ban all servers (admin only)",
    "ja": "グローバル スコープ - すべてのサーバーを禁止します (管理者のみ)",
    "cn": "全局范围 - 禁止所有服务器（仅限管理员）"
  },
  "Công dụng, nguồn gốc hoặc lưu ý canh tác...": {
    "en": "Uses, origin or cultivation notes...",
    "ja": "用途、産地、栽培上の注意点...",
    "cn": "用途、产地或栽培说明..."
  },
  "Ví dụ: 1 Tháng Discord Nitro / 100,000 Coin": {
    "en": "For example: 1 Month of Discord Nitro / 100,000 Coins",
    "ja": "例: 1 か月の Discord Nitro / 100,000 コイン",
    "cn": "例如：1 个月的 Discord Nitro / 100,000 个硬币"
  },
  "Gửi tin nhắn từ Web vào server Minecraft...": {
    "en": "Sending messages from the Web to the Minecraft server...",
    "ja": "Web から Minecraft サーバーにメッセージを送信しています...",
    "cn": "正在从 Web 向 Minecraft 服务器发送消息..."
  },
  "Hệ Thống Phân Quyền Minecraft Cloud Hosting": {
    "en": "Minecraft Cloud Hosting Decentralized System",
    "ja": "Minecraft クラウド ホスティング分散システム",
    "cn": "Minecraft 云托管去中心化系统"
  },
  "Java 17+ hoặc phiên bản phù hợp với máy chủ": {
    "en": "Java 17+ or version appropriate for the server",
    "ja": "Java 17+ またはサーバーに適したバージョン",
    "cn": "Java 17+ 或适合服务器的版本"
  },
  "Tính năng Custom Key hoạt động như thế nào?": {
    "en": "How does the Custom Key feature work?",
    "ja": "カスタム キー機能はどのように機能しますか?",
    "cn": "自定义按键功能如何工作？"
  },
  "Chess vs bạn hoặc vs Bot, đầy đủ luật FIDE": {
    "en": "Chess vs friend or vs Bot, full FIDE rules",
    "ja": "チェス対友人または対ボット、完全な FIDE ルール",
    "cn": "国际象棋 vs 朋友或 vs 机器人，完整的国际棋联规则"
  },
  "Rút bài và nhận lời luận giải từ AI Sakura": {
    "en": "Draw cards and receive interpretation from AI Sakura",
    "ja": "カードを引いてAIさくらの通訳を受ける",
    "cn": "抽卡并接受 AI Sakura 的解读"
  },
  "Làm thế nào để xem toàn bộ danh sách lệnh?": {
    "en": "How to see the entire command list?",
    "ja": "コマンドリスト全体を確認するにはどうすればよいですか?",
    "cn": "如何查看整个命令列表？"
  },
  "Kết nối bình thường đến wavelink node pool": {
    "en": "Connect normally to the wavelink node pool",
    "ja": "通常通り Wavelink ノード プールに接続します",
    "cn": "正常连接到wavelink节点池"
  },
  "Phát hiện và ngăn chặn người dùng vào ồ ạt": {
    "en": "Detect and prevent users from entering massively",
    "ja": "ユーザーの大量侵入を検出して阻止する",
    "cn": "检测并阻止用户大量进入"
  },
  "Quà Tặng Mỗi Ngày (Daily Giftcode Tự Động)": {
    "en": "Daily Gift (Automatic Daily Giftcode)",
    "ja": "デイリーギフト（自動デイリーギフトコード）",
    "cn": "每日礼物（自动每日礼物代码）"
  },
  "Hệ thống tự động phát hành mã Giftcode lúc": {
    "en": "The system automatically issues the Giftcode at",
    "ja": "システムは自動的にギフトコードを発行します。",
    "cn": "系统自动发出礼品码"
  },
  "👑 GOD MODE 100% (Đập Đồ & Sao Không Trượt)": {
    "en": "👑 GOD MODE 100% (Smash Things & Stars Don't Slip)",
    "ja": "👑 GOD MODE 100% (スマッシュシングス&スターは滑らない)",
    "cn": "👑 上帝模式 100%（粉碎物体且星星不滑落）"
  },
  "🔮 Vật phẩm ẩn (Không bán ở shop công khai)": {
    "en": "🔮 Hidden items (Not sold in public shops)",
    "ja": "🔮 隠しアイテム（一般のショップでは販売されていません）",
    "cn": "🔮隐藏物品（不在公共商店出售）"
  },
  "Mã định danh ID (troll_... hoặc item_...):": {
    "en": "ID identifier (troll_... or item_...):",
    "ja": "ID 識別子 (troll_... または item_...):",
    "cn": "ID标识符（troll_...或item_...）："
  },
  "Danh Sách Máy Chủ Minecraft Được Phát Hiện": {
    "en": "List of Minecraft Servers Discovered",
    "ja": "発見された Minecraft サーバーのリスト",
    "cn": "已发现的 Minecraft 服务器列表"
  },
  "ID Kênh Lưu Log Toàn Cục (Log Channel ID):": {
    "en": "Global Log Channel ID (Log Channel ID):",
    "ja": "グローバル ログ チャネル ID (ログ チャネル ID):",
    "cn": "全局日志通道ID（Log Channel ID）："
  },
  "Trí Tuệ Nhân Tạo (AI) & Models (config.py)": {
    "en": "Artificial Intelligence (AI) & Models (config.py)",
    "ja": "人工知能 (AI) とモデル (config.py)",
    "cn": "人工智能 (AI) 和模型 (config.py)"
  },
  "Groq API Key (Dùng cho AI Chat & Xem bói):": {
    "en": "Groq API Key (Used for AI Chat & Fortune Telling):",
    "ja": "Groq API キー (AI チャットと占いに使用):",
    "cn": "Groq API 密钥（用于 AI 聊天和算命）："
  },
  "📋 Danh Sách Người Dùng & Quản Trị Viên Web": {
    "en": "📋 List of Users & Web Admins",
    "ja": "📋 ユーザーとウェブ管理者のリスト",
    "cn": "📋 用户和网络管理员列表"
  },
  "Số ký tự kết hợp (◌̃◌́) vượt ngưỡng → xóa.": {
    "en": "The number of combined characters (◌̃◌́) exceeds the threshold → delete.",
    "ja": "結合文字数(◌̃◌́)が閾値を超えている→削除。",
    "cn": "组合字符数（◌̃◌́）超过阈值→删除。"
  },
  "🎭 Cấu Hình Tự Động Gán Vai Trò (Auto Role)": {
    "en": "🎭 Automatic Role Assignment Configuration (Auto Role)",
    "ja": "🎭 自動役割割り当て構成 (自動役割)",
    "cn": "🎭 自动角色分配配置（Auto Role）"
  },
  "✨ Tạo Bảng Tự Chọn Vai Trò (Reaction Role)": {
    "en": "✨ Create a Reaction Role Table",
    "ja": "✨ リアクションロールテーブルを作成する",
    "cn": "✨ 创建反应角色表"
  },
  "Ví dụ: Rơi từ Rương Atlantis, Boss biển...": {
    "en": "For example: Dropped from Atlantis Chest, Sea Boss...",
    "ja": "例: アトランティスのチェスト、シーボスからドロップ...",
    "cn": "例如：从亚特兰蒂斯宝箱、海王中掉落..."
  },
  "Ví dụ: Rơi từ Rương Hỗn Loạn, Mini-game...": {
    "en": "For example: Drops from Chaos Chests, Mini-games...",
    "ja": "例: カオスチェストからのドロップ、ミニゲーム...",
    "cn": "例如：混沌宝箱掉落、迷你游戏……"
  },
  "Nội dung chi tiết bên trong khung Embed...": {
    "en": "Detailed content inside the Embed frame...",
    "ja": "埋め込みフレーム内の詳細なコンテンツ...",
    "cn": "嵌入框架内的详细内容..."
  },
  "Xác minh tài khoản bản quyền (Online Mode)": {
    "en": "Verify copyright account (Online Mode)",
    "ja": "著作権アカウントの確認 (オンライン モード)",
    "cn": "验证版权账号（在线模式）"
  },
  ", sách phù phép và custom items độc quyền.": {
    "en": ", spell books and exclusive custom items.",
    "ja": "、魔法の本、限定のカスタムアイテム。",
    "cn": "、咒语书籍和独家定制物品。"
  },
  "Hướng dẫn cài đặt và sử dụng Plugin Sakura": {
    "en": "Instructions for installing and using Sakura Plugin",
    "ja": "さくらプラグインのインストールと使用方法",
    "cn": "Sakura插件安装和使用说明"
  },
  "Cách cài đặt kênh câu cá và nhận Giftcode?": {
    "en": "How to install fishing channel and receive Giftcode?",
    "ja": "釣りチャンネルをインストールしてギフトコードを受け取るにはどうすればよいですか?",
    "cn": "如何安装钓鱼频道并接收Giftcode？"
  },
  "Truy cập Dashboard > chọn máy chủ > mở mục": {
    "en": "Go to Dashboard > select server > open item",
    "ja": "ダッシュボードに移動 > サーバーを選択 > 項目を開く",
    "cn": "转到仪表板 > 选择服务器 > 打开项目"
  },
  "📁 Sakura Bot — Quản Lý Tệp & Nạp Lại Cogs": {
    "en": "📁 Sakura Bot — File Management & Cogs Reload",
    "ja": "📁 さくらボット — ファイル管理と歯車のリロード",
    "cn": "📁 Sakura Bot — 文件管理和 Cogs 重新加载"
  },
  "Chỉ cho phép đọc: SELECT, PRAGMA, EXPLAIN": {
    "en": "Read only: SELECT, PRAGMA, EXPLAIN",
    "ja": "読み取り専用: SELECT、PRAGMA、EXPLAIN",
    "cn": "只读：SELECT、PRAGMA、EXPLAIN"
  },
  "trong kênh chat Discord hoặc truy cập mục": {
    "en": "in the Discord chat channel or visit the section",
    "ja": "Discord チャット チャネルまたはセクションにアクセスしてください",
    "cn": "在 Discord 聊天频道中或访问该部分"
  },
  "Công Tắc Bật / Tắt Toàn Cục Hệ Thống Anti": {
    "en": "Anti System Global On/Off Switch",
    "ja": "アンチシステムグローバルオン/オフスイッチ",
    "cn": "反系统全局开关"
  },
  "Bảng Xếp Hạng Level & Kinh Tế Toàn Server": {
    "en": "Server-wide Level & Economy Rankings",
    "ja": "サーバー全体のレベルと経済のランキング",
    "cn": "全服务器级别和经济排名"
  },
  "Mô tả sinh vật biển sẽ xuất hiện tại đây.": {
    "en": "Descriptions of marine life will appear here.",
    "ja": "海洋生物の説明がここに表示されます。",
    "cn": "海洋生物的描述将出现在这里。"
  },
  "Chọn chế độ thiết lập sẵn chỉ với 1 click": {
    "en": "Choose a preset mode with just 1 click",
    "ja": "1クリックでプリセットモードを選択",
    "cn": "只需单击 1 次即可选择预设模式"
  },
  "Quản Lý Danh Mục Vật Phẩm Cửa Hàng (Shop)": {
    "en": "Manage Store Item List (Shop)",
    "ja": "ストアアイテムリストの管理（ショップ）",
    "cn": "管理商店商品列表（商店）"
  },
  "Troll thành viên hám quà trong kênh chat.": {
    "en": "Troll members greedy for gifts in the chat channel.",
    "ja": "チャット チャンネルでギフトを貪欲に狙うトロール メンバー。",
    "cn": "巨魔成员在聊天频道中贪图礼物。"
  },
  "Tự động tải video/ảnh khi gửi link TikTok": {
    "en": "Automatically download videos/photos when sending TikTok links",
    "ja": "TikTokリンクを送信するときにビデオ/写真を自動的にダウンロードします",
    "cn": "发送 TikTok 链接时自动下载视频/照片"
  },
  "XEM TRƯỚC HỒ SƠ (DISCORD PROFILE PREVIEW)": {
    "en": "DISCORD PROFILE PREVIEW",
    "ja": "DISCORD プロフィールのプレビュー",
    "cn": "DISCORD 个人资料预览"
  },
  "🔤 Mở Bảng Quản Lý Từ Điển & BXH Nối Chữ ➔": {
    "en": "🔤 Open the Dictionary Management Board & Letter Connection Chart ➔",
    "ja": "🔤 辞書管理ボードと文字接続表を開く ➔",
    "cn": "🔤 打开词典管理板和字母连接图 ➔"
  },
  "VD: 8 ký tự trở lên và >70% là hoa → xóa.": {
    "en": "For example: 8 characters or more and >70% are capital letters → delete.",
    "ja": "例: 8 文字以上かつ 70% 以上が大文字 → 削除。",
    "cn": "例如：8个字符或更多且>70%为大写字母→删除。"
  },
  "💡 Bị cấm sẽ không dùng được lệnh bot (trừ": {
    "en": "💡 If you are banned, you will not be able to use bot commands (except",
    "ja": "💡 禁止された場合、ボットコマンドを使用できなくなります（例外を除きます）",
    "cn": "💡 如果您被禁止，您将无法使用机器人命令（除了"
  },
  "Nhập Discord ID (vd: 1144785664458637394)": {
    "en": "Enter Discord ID (eg: 1144785664458637394)",
    "ja": "Discord ID を入力してください (例: 1144785664458637394)",
    "cn": "输入 Discord ID（例如：1144785664458637394）"
  },
  "Quản Lý Phân Quyền Người Dùng Web Hosting": {
    "en": "Managing Web Hosting User Permissions",
    "ja": "Web ホスティング ユーザー権限の管理",
    "cn": "管理虚拟主机用户权限"
  },
  "Giới hạn thời gian 1 tick (Max Tick Time)": {
    "en": "1 tick time limit (Max Tick Time)",
    "ja": "1 ティック時間制限 (Max Tick Time)",
    "cn": "1 个刻度时间限制（最大刻度时间）"
  },
  "Đọc log nếu có lỗi permission hoặc config": {
    "en": "Read log if there are permission or config errors",
    "ja": "権限または構成エラーがある場合はログを読み取ります",
    "cn": "如果存在权限或配置错误，则读取日志"
  },
  "Mua hoặc bảo vệ khu đất hiện tại của bạn.": {
    "en": "Buy or secure your existing land.",
    "ja": "既存の土地を購入または確保します。",
    "cn": "购买或保护您现有的土地。"
  },
  "Mở menu cá nhân chứa các chức năng nhanh.": {
    "en": "Opens a personal menu containing quick functions.",
    "ja": "クイック機能を含む個人メニューを開きます。",
    "cn": "打开包含快速功能的个人菜单。"
  },
  "Sakura Profiles • Danh Sách Hồ Sơ Cá Nhân": {
    "en": "Sakura Profiles • List of Personal Profiles",
    "ja": "さくらプロフィール・個人プロフィール一覧",
    "cn": "Sakura 个人资料 • 个人资料列表"
  },
  "💡 Đề xuất tính năng mới (Feature Request)": {
    "en": "💡 New feature proposal (Feature Request)",
    "ja": "💡 新機能の提案 (機能リクエスト)",
    "cn": "💡 新功能提案（功能请求）"
  },
  "• Áp dụng cho Discord Bot & Web Dashboard": {
    "en": "• Applies to Discord Bot & Web Dashboard",
    "ja": "• Discord ボットと Web ダッシュボードに適用されます",
    "cn": "• 适用于 Discord 机器人和 Web 仪表板"
  },
  "URL Ảnh nền trang web (Background Image)": {
    "en": "Website Background Image URL (Background Image)",
    "ja": "Webサイト背景画像URL（背景画像）",
    "cn": "网站背景图片URL（背景图片）"
  },
  "Màu tương tác / Điểm nhấn (Accent Color)": {
    "en": "Accent Color",
    "ja": "アクセントカラー",
    "cn": "强调色"
  },
  ". Bot sẽ tự online và sẵn sàng nhận lệnh": {
    "en": ". The bot will automatically be online and ready to receive orders",
    "ja": "。ボットは自動的にオンラインになり、注文を受け付ける準備が整います",
    "cn": "。机器人将自动上线并准备接收订单"
  },
  "Prefix, Ngôn ngữ, Welcome, AutoMod, Logs": {
    "en": "Prefix, Language, Welcome, AutoMod, Logs",
    "ja": "プレフィックス、言語、ようこそ、AutoMod、ログ",
    "cn": "前缀、语言、欢迎、AutoMod、日志"
  },
  "Đang tải danh sách lệnh từ Sakura Bot...": {
    "en": "Loading command list from Sakura Bot...",
    "ja": "さくらボットからコマンドリストを読み込み中...",
    "cn": "正在从 Sakura Bot 加载命令列表..."
  },
  "Bảng Điều Khiển Thao Túng Tỉ Lệ Hệ Thống": {
    "en": "System Scale Manipulation Panel",
    "ja": "システムスケール操作パネル",
    "cn": "系统规模操作面板"
  },
  "Nạn nhân bị ngắt kết nối voice đột ngột.": {
    "en": "The victim's voice connection was suddenly disconnected.",
    "ja": "被害者の音声接続が突然切断されました。",
    "cn": "受害者的语音连接突然断开。"
  },
  "Cường hóa cuốc & cần câu 100% thành công": {
    "en": "Enhanced pickaxe & fishing rod 100% successful",
    "ja": "強化されたつるはしと釣り竿は100%成功しました",
    "cn": "增强型镐和钓鱼竿 100% 成功"
  },
  "Mã định danh (ID không dấu, viết thường)": {
    "en": "Identifier (unsigned ID, lower case)",
    "ja": "識別子 (署名なし ID、小文字)",
    "cn": "标识符（无符号ID，小写）"
  },
  "🔗 Nối Server Minecraft Với Discord Guild": {
    "en": "🔗 Connect Minecraft Server With Discord Guild",
    "ja": "🔗 Minecraft サーバーを Discord ギルドに接続する",
    "cn": "🔗 将 Minecraft 服务器与 Discord Guild 连接"
  },
  "• Dịch thuật đa ngôn ngữ nhanh bằng lệnh": {
    "en": "• Fast multilingual translation using commands",
    "ja": "• コマンドを使用した高速多言語翻訳",
    "cn": "• 使用命令进行快速多语言翻译"
  },
  "Bỏ qua TẤT CẢ kiểm duyệt ở các kênh chọn": {
    "en": "Bypass ALL censorship on select channels",
    "ja": "選択したチャンネルですべての検閲をバイパスします",
    "cn": "绕过选定频道的所有审查"
  },
  "Tự động tính theo trọng lượng & đột biến": {
    "en": "Automatically calculated by weight & mutation",
    "ja": "重みと突然変異によって自動的に計算されます",
    "cn": "根据权重和突变自动计算"
  },
  "🔍 Tìm kiếm tên, mô tả, nguồn rơi, key...": {
    "en": "🔍 Search for name, description, source, key...",
    "ja": "🔍 名前、説明、ソース、キーを検索...",
    "cn": "🔍 搜索名称、描述、来源、密钥..."
  },
  "pika_... hoặc để trống nếu chỉ dùng RCON": {
    "en": "pika_... or leave blank if only using RCON",
    "ja": "pika_... または RCON のみを使用する場合は空白のままにします",
    "cn": "pika_...或者如果只使用 RCON 则留空"
  },
  "ví dụ: list hoặc say Xin chào mọi người!": {
    "en": "for example: list or say Hello everyone!",
    "ja": "例: リストするか、「皆さん、こんにちは!」と言ってください。",
    "cn": "例如：列出或说大家好！"
  },
  "Nhấn để tải ảnh đại diện mới từ máy tính": {
    "en": "Click to download a new profile picture from your computer",
    "ja": "クリックして、コンピュータから新しいプロフィール写真をダウンロードします",
    "cn": "单击可从您的计算机下载新的个人资料图片"
  },
  "⛏️ Sakura MC — Console Điều Khiển Server": {
    "en": "⛏️ Sakura MC — Server Control Console",
    "ja": "⛏️さくらMC — サーバーコントロールコンソール",
    "cn": "⛏️ Sakura MC — 服务器控制台"
  },
  "3. Khi đã có plugin trên server, làm gì?": {
    "en": "3. Once you have the plugin on the server, what to do?",
    "ja": "3. プラグインをサーバー上に配置したら、何をすればよいでしょうか?",
    "cn": "3. 将插件安装到服务器后，该怎么办？"
  },
  "/register <mật_khẩu> <nhập_lại_mật_khẩu>": {
    "en": "/register <password> <re-enter_password>",
    "ja": "/register <パスワード> <パスワードの再入力>",
    "cn": "/register <密码> <重新输入密码>"
  },
  "Tìm theo tên, username (@slug), mô tả...": {
    "en": "Search by name, username (@slug), description...",
    "ja": "名前、ユーザー名 (@slug)、説明で検索...",
    "cn": "按名称、用户名 (@slug)、描述搜索..."
  },
  "Trung Tâm Hỗ Trợ & Phản Hồi — Sakura Bot": {
    "en": "Support & Feedback Center — Sakura Bot",
    "ja": "サポート&フィードバックセンター — さくらボット",
    "cn": "支持与反馈中心 — Sakura Bot"
  },
  "⚙️ Cần trợ giúp cấu hình bot cho máy chủ": {
    "en": "⚙️ Need help configuring bot for server",
    "ja": "⚙️ サーバー用にボットを構成するのにサポートが必要です",
    "cn": "⚙️ 需要帮助为服务器配置机器人"
  },
  "Màu nền các hộp & thẻ (Card Background)": {
    "en": "Background color of boxes & cards (Card Background)",
    "ja": "ボックス＆カードの背景色（カード背景）",
    "cn": "盒子和卡片的背景颜色（卡片背景）"
  },
  "Trình duyệt không hỗ trợ thẻ video này.": {
    "en": "The browser does not support this video tag.",
    "ja": "ブラウザはこのビデオタグをサポートしていません。",
    "cn": "浏览器不支持此视频标签。"
  },
  "(Không có bảng nào trong cơ sở dữ liệu)": {
    "en": "(There are no tables in the database)",
    "ja": "(データベースにテーブルがありません)",
    "cn": "（数据库中没有表）"
  },
  "Câu cá đại dương & buôn bán hải sản RPG": {
    "en": "Ocean fishing & seafood trading RPG",
    "ja": "海釣り＆海産物取引RPG",
    "cn": "远洋捕鱼和海鲜贸易角色扮演游戏"
  },
  "Trạng Thái Hiện Diện (Presence Status):": {
    "en": "Presence Status:",
    "ja": "プレゼンスステータス:",
    "cn": "存在状态："
  },
  "). Theo dõi trạng thái kết nối Discord.": {
    "en": "). Monitor Discord connection status.",
    "ja": "）。 Discordの接続ステータスを監視します。",
    "cn": "）。监控 Discord 连接状态。"
  },
  "Cổng kết nối AI, Dữ liệu game & Lưu trữ": {
    "en": "AI Connection Port, Game Data & Storage",
    "ja": "AI接続ポート、ゲームデータおよびストレージ",
    "cn": "AI连接端口、游戏数据及存储"
  },
  "🐾 Thú Cưng / Pet (Hỗ trợ Sao & Đột Phá)": {
    "en": "🐾 Pets (Support Stars & Breakthroughs)",
    "ja": "🐾 ペット (サポートスターとブレークスルー)",
    "cn": "🐾 宠物（支持明星和突破）"
  },
  "Bách Khoa Toàn Thư Đại Dương & Vật Phẩm": {
    "en": "Ocean & Item Encyclopedia",
    "ja": "海とアイテムの百科事典",
    "cn": "海洋与物品百科全书"
  },
  "Nơi có thể kiếm / Điều kiện nhận rương:": {
    "en": "Where to find / Conditions for receiving chests:",
    "ja": "宝箱の入手場所・入手条件：",
    "cn": "哪里可以找到/接收宝箱的条件："
  },
  "Xem Trước Thông Báo Chào Mừng (Welcome)": {
    "en": "Preview the Welcome Notice (Welcome)",
    "ja": "ウェルカム通知のプレビュー (ようこそ)",
    "cn": "预览欢迎通知（欢迎）"
  },
  "không kiểm tra loại này ở các kênh chọn": {
    "en": "Do not test this type on select channels",
    "ja": "選択したチャネルではこのタイプをテストしないでください",
    "cn": "不要在选定的通道上测试此类型"
  },
  "Thành viên quản lý kênh riêng bằng lệnh": {
    "en": "Members manage private channels with commands",
    "ja": "メンバーはコマンドを使用してプライベート チャネルを管理します",
    "cn": "会员通过命令管理私人频道"
  },
  "(ai xóa tin/đổi role/ban) bot cần quyền": {
    "en": "(who deletes message/changes role/ban) bot needs permission",
    "ja": "(メッセージを削除/ロールを変更/禁止する人) ボットには許可が必要です",
    "cn": "（谁删除消息/更改角色/禁止）机器人需要许可"
  },
  "💾 Sao Lưu & Khôi Phục Máy Chủ (Backups)": {
    "en": "💾 Server Backup & Restore (Backups)",
    "ja": "💾 サーバーのバックアップと復元 (バックアップ)",
    "cn": "💾 服务器备份和恢复（备份）"
  },
  "API Key Pterodactyl / Hosting (Nếu có):": {
    "en": "API Key Pterodactyl / Hosting (If available):",
    "ja": "API キー Pterodactyl / ホスティング (利用可能な場合):",
    "cn": "API 密钥 Pterodactyl / 托管（如果有）："
  },
  "Chọn Kênh Nhận Tin (Text + Chat Voice):": {
    "en": "Select Channel to Receive News (Text + Voice Chat):",
    "ja": "ニュースを受信するチャンネルを選択してください (テキスト + ボイスチャット):",
    "cn": "选择接收新闻的渠道（文字+语音聊天）："
  },
  "Nhập cụm 2 từ (vd: trà sữa, hoa sen)...": {
    "en": "Enter a 2-word phrase (eg: milk tea, lotus)...",
    "ja": "2 単語のフレーズを入力してください (例: ミルク ティー、ロータス)...",
    "cn": "输入两个词的短语（例如：奶茶、莲花）..."
  },
  "ví dụ: pick_titanium hoặc ore_vibranium": {
    "en": "e.g. pick_titanium or ore_vibranium",
    "ja": "例: pick_titanium または ore_vibranium",
    "cn": "例如pick_titanium 或 ore_vibranium"
  },
  "Nhập Token bot Discord nếu cần cập nhật": {
    "en": "Enter the Discord bot Token if an update is needed",
    "ja": "アップデートが必要な場合は、Discord ボットトークンを入力してください",
    "cn": "如果需要更新，请输入 Discord 机器人令牌"
  },
  "ví dụ: snow.pikamc.vn hoặc 123.45.67.89": {
    "en": "For example: snow.pikamc.vn or 123.45.67.89",
    "ja": "例:snow.pikamc.vn または 123.45.67.89",
    "cn": "例如：snow.pikamc.vn 或 123.45.67.89"
  },
  "Bảng Mã Màu Minecraft (Nhấp để chèn §):": {
    "en": "Minecraft Color Code Table (Click to insert §):",
    "ja": "Minecraft カラーコード表 (クリックして§を挿入):",
    "cn": "Minecraft 颜色代码表（点击插入§）："
  },
  "Bật (Chỉ tài khoản bản quyền Minecraft)": {
    "en": "Enable (Minecraft license accounts only)",
    "ja": "有効にする (Minecraft ライセンス アカウントのみ)",
    "cn": "启用（仅限 Minecraft 许可证帐户）"
  },
  "Đảm bảo plugin phụ thuộc đang hoạt động": {
    "en": "Make sure the dependent plugin is active",
    "ja": "依存するプラグインがアクティブであることを確認してください",
    "cn": "确保依赖插件处于活动状态"
  },
  "Xem nhiệm vụ và nộp nhiệm vụ hàng ngày.": {
    "en": "View tasks and submit daily tasks.",
    "ja": "タスクを表示し、毎日のタスクを送信します。",
    "cn": "查看任务并提交日常任务。"
  },
  "• Tuân thủ chính sách Discord Developer": {
    "en": "• Comply with Discord Developer policies",
    "ja": "• Discord 開発者ポリシーに準拠する",
    "cn": "• 遵守Discord 开发者政策"
  },
  "Vui lòng chọn một bảng để xem dữ liệu.": {
    "en": "Please select a table to view data.",
    "ja": "データを表示するにはテーブルを選択してください。",
    "cn": "请选择一个表来查看数据。"
  },
  "Quản Trị Hệ Thống & Chẩn Đoán Kỹ Thuật": {
    "en": "System Administration & Technical Diagnosis",
    "ja": "システム管理と技術診断",
    "cn": "系统管理与技术诊断"
  },
  "Tự động giám sát & làm mới theo chu kỳ": {
    "en": "Automatically monitor & refresh periodically",
    "ja": "自動的に監視し、定期的に更新します",
    "cn": "自动监控并定期刷新"
  },
  "💀 CURSED_BAIT (Mồi nguyền rủa vớt rác)": {
    "en": "💀 CURSED_BAIT (Cursed bait to pick up trash)",
    "ja": "💀 CURSED_BAIT (ゴミを拾うための呪われた餌)",
    "cn": "💀 CURSED_BAIT（被诅咒的诱饵来捡起垃圾）"
  },
  "Bảng Điều Khiển Môi Trường Nông Nghiệp": {
    "en": "Agricultural Environmental Dashboard",
    "ja": "農業環境ダッシュボード",
    "cn": "农业环境仪表板"
  },
  "Trung Tâm Quản Trị Hệ Thống Đào Khoáng": {
    "en": "Mining System Administration Center",
    "ja": "マイニング システム管理センター",
    "cn": "矿业系统管理中心"
  },
  "Đang tải danh sách server Minecraft...": {
    "en": "Loading Minecraft server list...",
    "ja": "Minecraft サーバー リストを読み込んでいます...",
    "cn": "正在加载 Minecraft 服务器列表..."
  },
  "👥 Danh Sách Người Chơi Đang Trực Tuyến": {
    "en": "👥 List of Online Players",
    "ja": "👥 オンラインプレイヤーのリスト",
    "cn": "👥 在线玩家列表"
  },
  "TỈ LỆ: 1 MC COIN = 1,000 DISCORD COINS": {
    "en": "RATE: 1 MC COIN = 1,000 DISCORD COINS",
    "ja": "レート: 1 MC コイン = 1,000 ディスコードコイン",
    "cn": "比率：1 MC 币 = 1,000 DISCORD 币"
  },
  "Mã ID Thành Tựu (duy nhất, không dấu):": {
    "en": "Achievement ID code (unique, unsigned):",
    "ja": "実績 ID コード (一意、署名なし):",
    "cn": "成就 ID 代码（唯一，未签名）："
  },
  "để bot tham gia voice và đọc tin nhắn.": {
    "en": "Let the bot join the voice and read the message.",
    "ja": "ボットに音声を加えてメッセージを読んでもらいましょう。",
    "cn": "让机器人加入语音并阅读消息。"
  },
  "Panel chọn role và kênh duyệt (nếu có)": {
    "en": "Panel selects role and approval channel (if any)",
    "ja": "パネルは役割と承認チャネル (存在する場合) を選択します",
    "cn": "面板选择角色和审批渠道（如果有）"
  },
  "Xem Trước Thông Báo Tạm Biệt (Goodbye)": {
    "en": "Preview Goodbye Notice (Goodbye)",
    "ja": "さよならのお知らせ（さようなら）のプレビュー",
    "cn": "预览告别通知（再见）"
  },
  "Chặn link mời Discord (discord.gg/...)": {
    "en": "Block Discord invite links (discord.gg/...)",
    "ja": "Discord の招待リンク (discord.gg/...) をブロックする",
    "cn": "阻止 Discord 邀请链接 (discord.gg/...)"
  },
  "Phạm vi máy chủ — chỉ cấm ở server này": {
    "en": "Server range — only banned on this server",
    "ja": "サーバー範囲 - このサーバーでのみ禁止されています",
    "cn": "服务器范围——仅在该服务器上被禁止"
  },
  "Chỉ được chọn 1 role duy nhất (Single)": {
    "en": "You can only choose one role (Single)",
    "ja": "ロールは 1 つだけ選択できます (シングル)",
    "cn": "您只能选择一个角色（单人）"
  },
  "Tự Động Chuyển Tin Nhắn Discord ➔ Game": {
    "en": "Automatically Transfer Discord Messages ➔ Game",
    "ja": "Discord メッセージを自動的に転送 ➔ ゲーム",
    "cn": "自动传输 Discord 消息 ➔ 游戏"
  },
  "Nhập mã 6 ký tự vào ô bên dưới rồi bấm": {
    "en": "Enter the 6-character code in the box below then click",
    "ja": "下のボックスに6文字のコードを入力し、クリックしてください。",
    "cn": "在下面的框中输入 6 个字符的代码，然后单击"
  },
  "Để trống nếu muốn dùng tên gốc của bot": {
    "en": "Leave blank if you want to use the bot's original name",
    "ja": "ボットの元の名前を使用する場合は空白のままにしてください",
    "cn": "如果您想使用机器人的原始名称，请留空"
  },
  "Ví dụ: 60 Nguyên Thạch, 5x Kinh Nghiệm": {
    "en": "For example: 60 Primogems, 5x Experience",
    "ja": "例: 60 プリモジェム、経験値 5 倍",
    "cn": "例如：60 个原始宝石，5x 经验"
  },
  "Tài Khoản Liên Kết Discord — Minecraft": {
    "en": "Discord Linked Account — Minecraft",
    "ja": "Discord にリンクされたアカウント — Minecraft",
    "cn": "Discord 关联帐户 — Minecraft"
  },
  "🖥️ Sakura MC — Bảng Điều Khiển Console": {
    "en": "🖥️ Sakura MC — Console Control Panel",
    "ja": "🖥️ さくら MC — コンソールコントロールパネル",
    "cn": "🖥️ Sakura MC — 控制台控制面板"
  },
  "Tắt (Cho phép cả Crack / Launcher lậu)": {
    "en": "Disable (Allow pirated Crack/Launcher too)",
    "ja": "無効にする (海賊版のクラック/ランチャーも許可します)",
    "cn": "禁用（也允许盗版 Crack/Launcher）"
  },
  "Tự động sinh ra Bò, Cừu, Lợn, Gà, v.v.": {
    "en": "Automatically spawn Cows, Sheep, Pigs, Chickens, etc.",
    "ja": "牛、羊、豚、鶏などを自動的にスポーンします。",
    "cn": "自动生成牛、羊、猪、鸡等。"
  },
  "Kích hoạt giao thức RCON (Enable RCON)": {
    "en": "Enable RCON protocol (Enable RCON)",
    "ja": "RCON プロトコルを有効にする (RCON を有効にする)",
    "cn": "启用RCON协议（启用RCON）"
  },
  "và lưu file .jar vào máy tính của bạn.": {
    "en": "and save the .jar file to your computer.",
    "ja": ".jar ファイルをコンピュータに保存します。",
    "cn": "并将 .jar 文件保存到您的计算机。"
  },
  "Không đổi tên file nếu không cần thiết": {
    "en": "Do not rename files if not necessary",
    "ja": "必要がない場合はファイル名を変更しないでください",
    "cn": "如果没有必要，不要重命名文件"
  },
  "Chính sách Bảo mật này giải thích cách": {
    "en": "This Privacy Policy explains how",
    "ja": "このプライバシー ポリシーでは、次の方法について説明します。",
    "cn": "本隐私政策解释了如何"
  },
  "ID Máy Chủ (Guild ID) & Cấu Hình Kênh:": {
    "en": "Server ID (Guild ID) & Channel Configuration:",
    "ja": "サーバーID (ギルドID) とチャンネル構成:",
    "cn": "服务器 ID（公会 ID）和频道配置："
  },
  "Lịch Sử Hội Thoại Ticket (Transcript):": {
    "en": "Ticket Conversation History (Transcript):",
    "ja": "チケットの会話履歴 (トランスクリプト):",
    "cn": "票证对话历史记录（文字记录）："
  },
  "Ban quản trị Sakura Bot có toàn quyền:": {
    "en": "Sakura Bot Administration Board has full authority:",
    "ja": "さくらボット管理委員会は以下の全権限を持っています。",
    "cn": "Sakura Bot 管理委员会拥有全权："
  },
  "Danh Sách Nút Liên Kết (Custom Links)": {
    "en": "Custom Links List",
    "ja": "カスタムリンクリスト",
    "cn": "自定义链接列表"
  },
  "🧩 Quản Lý & Nạp Lại Cogs / Extensions": {
    "en": "🧩 Manage & Reload Cogs / Extensions",
    "ja": "🧩 コグ/拡張機能の管理とリロード",
    "cn": "🧩 管理和重新加载齿轮/扩展"
  },
  "Cần đăng nhập để tham gia Global Chat": {
    "en": "You need to log in to join Global Chat",
    "ja": "グローバルチャットに参加するにはログインする必要があります",
    "cn": "您需要登录才能加入全球聊天"
  },
  "để thêm Sakura vào server và thử lại.": {
    "en": "to add Sakura to the server and try again.",
    "ja": "サーバーにさくらを追加して再試行してください。",
    "cn": "将 Sakura 添加到服务器并重试。"
  },
  "🎁 Phần Thưởng Cố Định Của Daily Code:": {
    "en": "🎁 Daily Code Fixed Rewards:",
    "ja": "🎁 毎日のコード固定報酬:",
    "cn": "🎁 每日代码固定奖励："
  },
  "Thuốc Nhân Đôi Coins 2 Giờ (x2 Coins)": {
    "en": "Potion Doubles Coins 2 Hours (x2 Coins)",
    "ja": "ポーション コイン 2 時間 2 時間 (x2 コイン)",
    "cn": "药水双倍金币 2 小时（x2 金币）"
  },
  "🎣 Cần Câu Cá (Hỗ trợ Cường Hóa & Sao)": {
    "en": "🎣 Fishing Rod (Support Enhancement & Stars)",
    "ja": "🎣 釣り竿（サポート強化＆スター）",
    "cn": "🎣 钓鱼竿（支持增强和星星）"
  },
  "🔮 Pet ẩn (Chỉ mở khóa từ Rương/Event)": {
    "en": "🔮 Hidden Pet (Only unlocked from Chests/Events)",
    "ja": "🔮 隠しペット (チェスト/イベントからのみロック解除)",
    "cn": "🔮隐藏宠物（仅从宝箱/活动中解锁）"
  },
  "Trạng Thái Cưỡng Chế (Admin Override)": {
    "en": "Admin Override",
    "ja": "管理者のオーバーライド",
    "cn": "管理员覆盖"
  },
  "⛈️ Giông Bão Dữ Dội (Có thể quật cây)": {
    "en": "⛈️ Severe Thunderstorms (Can knock down trees)",
    "ja": "⛈️激しい雷雨（木を倒す可能性があります）",
    "cn": "⛈️ 严重雷暴（可以击倒树木）"
  },
  "👑 GOD MODE 100% (Đập Cuốc & Sao 100%)": {
    "en": "👑 GOD MODE 100% (Smash Pickaxe & Stars 100%)",
    "ja": "👑 GOD MODE 100% (ツルハシとスターをスマッシュ 100%)",
    "cn": "👑 上帝模式 100%（粉碎镐和星星 100%）"
  },
  "Hỗ Trợ Giọng Đọc Text-To-Speech (TTS)": {
    "en": "Text-To-Speech (TTS) Voice Support",
    "ja": "Text-To-Speech (TTS) 音声サポート",
    "cn": "文本转语音 (TTS) 语音支持"
  },
  "📘 Hướng dẫn 3 kiểu khớp & ví dụ Regex": {
    "en": "📘 Tutorial on 3 match types & Regex examples",
    "ja": "📘 3 つの一致タイプと正規表現の例に関するチュートリアル",
    "cn": "📘 3 种匹配类型和正则表达式示例教程"
  },
  "cho phép trả lời ẩn danh trong thread": {
    "en": "Allow anonymous replies in threads",
    "ja": "スレッド内で匿名の返信を許可する",
    "cn": "允许在线程中匿名回复"
  },
  "🎣 Các khu vực / Kênh câu cá được phép": {
    "en": "🎣 Permitted Fishing Areas/Channels",
    "ja": "🎣 許可された釣り場/水路",
    "cn": "🎣 允许捕鱼的区域/渠道"
  },
  "Kênh Chat Đồng Bộ (Sync Chat 2 Chiều)": {
    "en": "Synchronized Chat Channel (2-Way Sync Chat)",
    "ja": "同期チャットチャンネル（双方向同期チャット）",
    "cn": "同步聊天通道（2路同步聊天）"
  },
  "🟢 Đã Liên Kết Qua Plugin MyVaultAddon": {
    "en": "🟢 Linked via MyVaultAddon Plugin",
    "ja": "🟢 MyVaultAddon プラグイン経由でリンクされています",
    "cn": "🟢 通过 MyVaultAddon 插件链接"
  },
  "Hướng dẫn kết nối máy chủ qua Plugin:": {
    "en": "Instructions for connecting to the server via Plugin:",
    "ja": "プラグイン経由でサーバーに接続する手順:",
    "cn": "通过插件连接服务器的说明："
  },
  "Nhập password trong server.properties": {
    "en": "Enter the password in server.properties",
    "ja": "「server.properties」にパスワードを入力します。",
    "cn": "在server.properties中输入密码"
  },
  "Tắt (Hòa bình / Không gây sát thương)": {
    "en": "Off (Peaceful / No Damage)",
    "ja": "オフ (平和/ダメージなし)",
    "cn": "关闭（和平/无伤害）"
  },
  ", chuyển đổi coins hai chiều tức thì.": {
    "en": ", instant two-way coin conversion.",
    "ja": "、即時の双方向コイン変換。",
    "cn": "，即时双向硬币兑换。"
  },
  "Nhận phần thưởng điểm danh hàng ngày.": {
    "en": "Receive daily attendance rewards.",
    "ja": "毎日の出席報酬を受け取ります。",
    "cn": "获得每日出席奖励。"
  },
  "ID Người Dùng & Tên Hiển Thị Discord:": {
    "en": "Discord User ID & Display Name:",
    "ja": "DiscordのユーザーIDと表示名:",
    "cn": "Discord 用户 ID 和显示名称："
  },
  "Màu nền trang web (Background Color)": {
    "en": "Website background color (Background Color)",
    "ja": "ウェブサイトの背景色 (Background Color)",
    "cn": "网站背景色（Background Color）"
  },
  "Mở tệp gốc trong tab trình duyệt mới": {
    "en": "Open the original file in a new browser tab",
    "ja": "新しいブラウザタブで元のファイルを開きます",
    "cn": "在新的浏览器选项卡中打开原始文件"
  },
  "♟️ Cờ Vua AI Đa Cấp Độ — Sakura Game": {
    "en": "♟️ Multi-Level AI Chess — Sakura Game",
    "ja": "♟️ マルチレベル AI チェス — サクラゲーム",
    "cn": "♟️多级AI象棋——樱花游戏"
  },
  "Danh sách từ tùy chọn (Custom Words)": {
    "en": "Custom Words List",
    "ja": "カスタム単語リスト",
    "cn": "自定义单词列表"
  },
  "Cờ Caro Siêu Lớn 15×15 (Nối 5 Thắng)": {
    "en": "Super Large Checkers 15×15 (Connect 5 Wins)",
    "ja": "超大型チェッカー 15×15 (5つの勝利を接続)",
    "cn": "超大跳棋 15×15（连棋 5 胜）"
  },
  "Phát nhạc YouTube/Spotify (Lavalink)": {
    "en": "Play music YouTube/Spotify (Lavalink)",
    "ja": "音楽の再生 YouTube/Spotify (Lavalink)",
    "cn": "播放音乐 YouTube/Spotify (Lavalink)"
  },
  "CÁC LOÀI THỦY SINH ĐANG BƠI TRONG BỂ": {
    "en": "AQUATIC SPECIES ARE SWIMMING IN THE TANK",
    "ja": "水生生物が水槽内を泳いでいる",
    "cn": "水生生物在水箱里游泳"
  },
  "🧊 FREEZE_FISHING (Đóng băng cần câu)": {
    "en": "🧊 FREEZE_FISHING (Freeze fishing rods)",
    "ja": "🧊 FREEZE_FISHING (釣り竿を凍結)",
    "cn": "🧊 FREEZE_FISHING（冷冻鱼竿）"
  },
  "Hiển thị ảnh quái vật troll bất ngờ.": {
    "en": "Shows a picture of a surprise troll monster.",
    "ja": "驚きのトロール モンスターの写真を表示します。",
    "cn": "显示一张令人惊讶的巨魔怪物的图片。"
  },
  "Quản Trị Hệ Thống Thành Tựu Minigame": {
    "en": "System Administration Minigame Achievements",
    "ja": "システム管理ミニゲームの実績",
    "cn": "系统管理小游戏成就"
  },
  "Mô Tả Chi Tiết / Điều Kiện Đạt Được:": {
    "en": "Detailed Description / Qualifications:",
    "ja": "詳しい説明/資格:",
    "cn": "详细描述/资格："
  },
  "Map ID Điểm Danh (MAP_DIEM_DANH_ID):": {
    "en": "Map Attendance ID (MAP_DIEM_DANH_ID):",
    "ja": "マップ出席 ID (MAP_DIEM_DANH_ID):",
    "cn": "地图出勤 ID (MAP_DIEM_DANH_ID)："
  },
  "Kênh chơi câu hỏi / trò chơi trí tuệ": {
    "en": "Channel for playing questions/intellectual games",
    "ja": "質問・知的ゲームをするチャンネル",
    "cn": "做题/智力游戏频道"
  },
  "Tag quá nhiều người/role trong 1 tin": {
    "en": "Tag too many people/roles in 1 post",
    "ja": "1 つの投稿にタグ付けする人や役割が多すぎます",
    "cn": "在 1 个帖子中标记太多人员/角色"
  },
  "nút “Công Khai” — hiện tên người gửi": {
    "en": "“Make Public” button — displays the sender's name",
    "ja": "「公開」ボタン — 送信者の名前が表示されます",
    "cn": "“公开”按钮 — 显示发件人姓名"
  },
  "🐟 Cấu hình Hệ thống Câu cá (Fishing)": {
    "en": "🐟 Fishing System Configuration (Fishing)",
    "ja": "🐟 釣りシステム構成（釣り）",
    "cn": "🐟 钓鱼系统配置（钓鱼）"
  },
  "📋 Danh Sách Custom Keys Đã Thiết Lập": {
    "en": "📋 List of Custom Keys Set Up",
    "ja": "📋 設定されたカスタムキーのリスト",
    "cn": "📋 自定义按键设置列表"
  },
  "🚀 Đăng Bảng Reaction Role Lên Server": {
    "en": "🚀 Post the Reaction Role Table to the Server",
    "ja": "🚀 リアクションロールテーブルをサーバーにポストする",
    "cn": "🚀 将反应角色表发布到服务器"
  },
  "Ví dụ: s!help | Playing with members": {
    "en": "For example: s!help | Playing with members",
    "ja": "例: s!help |メンバーと遊ぶ",
    "cn": "例如： s!help |和会员一起玩"
  },
  "Ví dụ: Mở Rương Hải Tặc, Boss rơi...": {
    "en": "For example: Open Pirate Chest, Boss falls...",
    "ja": "例: 海賊の宝箱を開けると、ボスが倒れます...",
    "cn": "例如：打开海盗宝箱，Boss掉落……"
  },
  "Ví dụ: Rơi hiếm từ Rương Atlantis...": {
    "en": "For example: Rare drop from Atlantis Chest...",
    "ja": "例: アトランティスチェストからのレアドロップ...",
    "cn": "例如：亚特兰蒂斯宝箱的稀有掉落物..."
  },
  "⚡ Xem menu lệnh quản trị & AutoMod →": {
    "en": "⚡ View admin command menu & AutoMod →",
    "ja": "⚡ 管理コマンドメニューと AutoMod を表示 →",
    "cn": "⚡ 查看管理命令菜单和 AutoMod →"
  },
  "Bắt Buộc Tải (Require Resource Pack)": {
    "en": "Required Resource Pack",
    "ja": "必要なリソース パック",
    "cn": "所需资源包"
  },
  "Lời Nhắc Tải Gói Tài Nguyên (Prompt)": {
    "en": "Resource Pack Download Prompt (Prompt)",
    "ja": "リソース パックのダウンロード プロンプト (プロンプト)",
    "cn": "资源包下载提示（提示）"
  },
  "Tên file: LinhDevPlugin-Test-1.0.jar": {
    "en": "File name: LinhDevPlugin-Test-1.0.jar",
    "ja": "ファイル名: LinhDevPlugin-Test-1.0.jar",
    "cn": "文件名：LinhDevPlugin-Test-1.0.jar"
  },
  "Chưa có video — dán link rồi bấm Xem": {
    "en": "No video yet — paste the link and click Watch",
    "ja": "まだビデオはありません — リンクを貼り付けて「見る」をクリックします",
    "cn": "还没有视频 — 粘贴链接并单击“观看”"
  },
  "🌸 Tạo & Tùy Biến Sakura Bio Profile": {
    "en": "🌸 Create & Customize Sakura Bio Profile",
    "ja": "🌸 さくらプロフィールの作成とカスタマイズ",
    "cn": "⭐ 创建和自定义樱花个人资料"
  },
  "Giao Diện, Màu Sắc & Thứ Tự Các Hộp": {
    "en": "Interface, Color & Order of Boxes",
    "ja": "インターフェース、色、ボックスの順序",
    "cn": "盒子的界面、颜色和顺序"
  },
  "Liên Kết Mạng Xã Hội (Social Icons)": {
    "en": "Social Network Links (Social Icons)",
    "ja": "ソーシャル ネットワーク リンク (ソーシャル アイコン)",
    "cn": "社交网络链接（社交图标）"
  },
  "Kết quả truy vấn sẽ hiển thị ở đây.": {
    "en": "Query results will be displayed here.",
    "ja": "クエリ結果がここに表示されます。",
    "cn": "查询结果将显示在这里。"
  },
  "Đồng bộ lại cây lệnh Slash Commands": {
    "en": "Resynchronize the Slash Commands command tree",
    "ja": "スラッシュ コマンド コマンド ツリーを再同期する",
    "cn": "重新同步 Slash Commands 命令树"
  },
  "⚡ Tốc Độ (35s vẽ, x2 điểm đoán sớm)": {
    "en": "⚡ Speed (35 seconds to draw, x2 early guess points)",
    "ja": "⚡ スピード (描画まで 35 秒、早期推測ポイント x2)",
    "cn": "⚡ 速度（35秒抽奖，x2早期猜测点）"
  },
  ". Nhấn Lưu là áp dụng ngay lập tức.": {
    "en": ". Click Save to apply immediately.",
    "ja": "。 「保存」をクリックしてすぐに適用します。",
    "cn": "。单击“保存”立即应用。"
  },
  "Tại sao không thấy server của mình?": {
    "en": "Why can't I see my server?",
    "ja": "自分のサーバーが表示されないのはなぜですか?",
    "cn": "为什么我看不到我的服务器？"
  },
  "Nội Dung Hoạt Động (Activity Text):": {
    "en": "Activity Text:",
    "ja": "アクティビティテキスト:",
    "cn": "活动正文："
  },
  "Mã Code (Tùy chọn hoặc ngẫu nhiên):": {
    "en": "Code (Optional or random):",
    "ja": "コード (オプションまたはランダム):",
    "cn": "代码（可选或随机）："
  },
  "💎 Chìa Khóa Kim Cương (key_diamond)": {
    "en": "💎 Diamond Key (key_diamond)",
    "ja": "💎 ダイヤモンドの鍵 (key_diamond)",
    "cn": "💎 钻石钥匙 (key_diamond)"
  },
  "🔮 Rương Ẩn / Rương Sự Kiện Đặc Biệt": {
    "en": "🔮 Hidden Chests / Special Event Chests",
    "ja": "🔮 隠しチェスト/特別イベントチェスト",
    "cn": "🔮 隐藏宝箱/特别活动宝箱"
  },
  "Bật/tắt lệnh tra cứu cung hoàng đạo": {
    "en": "Turn on/off the zodiac search command",
    "ja": "干支検索コマンドのオン/オフ",
    "cn": "打开/关闭生肖搜索命令"
  },
  "📊 Xem thống kê vi phạm spam gần đây": {
    "en": "📊 View recent spam violation statistics",
    "ja": "📊 最近のスパム違反統計を表示する",
    "cn": "📊 查看近期垃圾邮件违规统计数据"
  },
  "Chặn mọi URL trừ whitelist bên dưới": {
    "en": "Block all URLs except the whitelist below",
    "ja": "以下のホワイトリストを除くすべての URL をブロックします",
    "cn": "阻止除下面白名单之外的所有 URL"
  },
  "xem người gửi thật (chống lạm dụng)": {
    "en": "see real sender (anti-abuse)",
    "ja": "実際の送信者を確認する (不正行為防止)",
    "cn": "查看真实发件人（防滥用）"
  },
  "👤 Vai trò cho Người dùng mới (User)": {
    "en": "👤 Roles for New Users (User)",
    "ja": "👤 新規ユーザーの役割 (ユーザー)",
    "cn": "👤 新用户（用户）的角色"
  },
  "Thành viên đang giữ chuỗi hoạt động": {
    "en": "Member is keeping the thread active",
    "ja": "メンバーがスレッドをアクティブに維持しています",
    "cn": "会员保持线程活跃"
  },
  "📢 Gửi Tin Nhắn / Thông Báo Đến Kênh": {
    "en": "📢 Send Message / Notification To Channel",
    "ja": "📢 チャンネルにメッセージ/通知を送信",
    "cn": "📢 向频道发送消息/通知"
  },
  "Nội Dung Tin Nhắn (Văn bản thường):": {
    "en": "Message Content (Normal Text):",
    "ja": "メッセージの内容 (通常のテキスト):",
    "cn": "消息内容（普通文本）："
  },
  "🔍 Tìm kiếm từ vựng trong từ điển...": {
    "en": "🔍 Search vocabulary in the dictionary...",
    "ja": "🔍 辞書で語彙を検索...",
    "cn": "🔍 在字典中搜索词汇..."
  },
  "Nhập câu trả lời tự động của bot...": {
    "en": "Enter the bot's automatic response...",
    "ja": "ボットの自動応答を入力してください...",
    "cn": "输入机器人的自动回复..."
  },
  "Kênh Chat 2 Chiều (Discord <-> MC):": {
    "en": "2-Way Chat Channel (Discord <-> MC):",
    "ja": "双方向チャットチャンネル (Discord <-> MC):",
    "cn": "2 向聊天频道（Discord <-> MC）："
  },
  "Danh Sách Người Dùng Được Cấp Quyền": {
    "en": "List of Authorized Users",
    "ja": "許可されたユーザーのリスト",
    "cn": "授权用户名单"
  },
  "Bật (Bắt buộc phải tải để vào game)": {
    "en": "On (Required to download to enter the game)",
    "ja": "オン (ゲームに参加するにはダウンロードが必要です)",
    "cn": "开启（需要下载才能进入游戏）"
  },
  "Dịch chuyển về nhà đã đặt trước đó.": {
    "en": "Teleport to the previously booked home.",
    "ja": "以前に予約した家にテレポートします。",
    "cn": "传送到之前预定的家。"
  },
  "của máy chủ trên Dashboard, tại thẻ": {
    "en": "of the server on the Dashboard, at the tab",
    "ja": "ダッシュボードのタブでサーバーの",
    "cn": "服务器在仪表板上的选项卡上"
  },
  "✨ Trình Tải TikTok & Douyin Đa Năng": {
    "en": "✨ Versatile TikTok & Douyin Downloader",
    "ja": "✨ 多機能な TikTok & Douyin ダウンローダー",
    "cn": "✨ 多功能 TikTok 和抖音下载器"
  },
  "Nội dung tệp sẽ xuất hiện ở đây...": {
    "en": "File contents will appear here...",
    "ja": "ファイルの内容がここに表示されます...",
    "cn": "文件内容将出现在这里..."
  },
  "Trung Tâm Quản Trị Hệ Thống Câu Cá": {
    "en": "Fishing System Administration Center",
    "ja": "釣りシステム管理センター",
    "cn": "渔业系统管理中心"
  },
  "🧨 Vật Tư Khai Khoáng (TNT, Đèn...)": {
    "en": "🧨 Mining Supplies (TNT, Lamp...)",
    "ja": "🧨 鉱山用品 (TNT、ランプなど)",
    "cn": "🧨 采矿用品（TNT、灯...）"
  },
  "Tỉ Lệ Quặng Siêu Hiếm (Netherite):": {
    "en": "Super Rare Ore (Netherite) Ratio:",
    "ja": "スーパーレア鉱石（ネザライト）比率：",
    "cn": "超级稀有矿石（下界合金）比例："
  },
  "Quản Trị Hệ Thống Hôn Lễ & Cặp Đôi": {
    "en": "Wedding & Couple System Administration",
    "ja": "ウェディング＆カップルシステム運営管理",
    "cn": "婚礼及情侣系统管理"
  },
  "🌧️ Mưa Rào Mát Lành (Tự tưới nước)": {
    "en": "🌧️ Cool Showers (Self-watering)",
    "ja": "🌧️ クールシャワー (自動給水)",
    "cn": "🌧️ 凉水淋浴（自动浇水）"
  },
  "🔥 Nắng Gắt Hạn Hán (Đất khô nhanh)": {
    "en": "🔥 Severe Sun Drought (Soil dries quickly)",
    "ja": "🔥 ひどい日照り（土壌がすぐに乾く）",
    "cn": "🔥 严重日晒（土壤很快干燥）"
  },
  "Quản Trị Hệ Thống Minecraft Server": {
    "en": "Minecraft Server System Administration",
    "ja": "Minecraft サーバー システム管理",
    "cn": "Minecraft 服务器系统管理"
  },
  "Cài Đặt Hệ Thống & Web (config.py)": {
    "en": "System & Web Settings (config.py)",
    "ja": "システムと Web 設定 (config.py)",
    "cn": "系统和 Web 设置 (config.py)"
  },
  "Token Điểm Danh (TOKEN_DIEM_DANH):": {
    "en": "Attendance Token (TOKEN_DIEM_DAMN):",
    "ja": "出席トークン (TOKEN_DIEM_DAMN):",
    "cn": "出席令牌（TOKEN_DIEM_DAMN）："
  },
  "luôn được miễn phí Vote vĩnh viễn.": {
    "en": "Voting is always free forever.",
    "ja": "投票はいつでも永久に無料です。",
    "cn": "投票永远是免费的。"
  },
  "= tên server trong thông báo boost": {
    "en": "= server name in boost notification",
    "ja": "= ブースト通知のサーバー名",
    "cn": "= boost 通知中的服务器名称"
  },
  "nút “Ẩn danh” — giấu tên người gửi": {
    "en": "“Anonymous” button — hides the sender's name",
    "ja": "「匿名」ボタン - 送信者の名前を非表示にします",
    "cn": "“匿名”按钮 — 隐藏发件人的姓名"
  },
  "🚀 Phát Hành Mã Code Gacha Thủ Công": {
    "en": "🚀 Released Manual Gacha Codes",
    "ja": "🚀 手動ガチャコードを公開しました",
    "cn": "🚀 发布手动扭蛋代码"
  },
  "📎 Đính Kèm Tệp / Hình Ảnh / Video:": {
    "en": "📎 Attach Files / Images / Videos:",
    "ja": "📎 ファイル/画像/ビデオを添付:",
    "cn": "📎 附加文件/图像/视频："
  },
  "Loại Nhẫn Cưới (Tên hoặc Mã Nhẫn):": {
    "en": "Type of Wedding Ring (Name or Ring Code):",
    "ja": "結婚指輪の種類 (名前またはリングコード):",
    "cn": "结婚戒指类型（名称或戒指代码）："
  },
  "🌸 Sakura Bot — Discord Bot Đa Năng": {
    "en": "🌸 Sakura Bot — Multipurpose Discord Bot",
    "ja": "🌸 さくらボット — 多目的 Discord ボット",
    "cn": "😍 Sakura Bot — 多用途 Discord 机器人"
  },
  "Phân Tích Dung Lượng Ổ Đĩa Máy Chủ": {
    "en": "Analyze Server Drive Capacity",
    "ja": "サーバードライブ容量の分析",
    "cn": "分析服务器驱动器容量"
  },
  "Số người chơi tối đa (Max Players)": {
    "en": "Max Players",
    "ja": "最大プレイヤー数",
    "cn": "最大玩家数"
  },
  "🛡️ Chính sách Bảo mật — Sakura Bot": {
    "en": "🛡️ Privacy Policy — Sakura Bot",
    "ja": "🛡️プライバシーポリシー — さくらボット",
    "cn": "🛡️ 隐私政策 — Sakura Bot"
  },
  "của bạn cho bất kỳ bên thứ ba nào.": {
    "en": "yours to any third party.",
    "ja": "あなたの所有物を第三者に譲渡します。",
    "cn": "您的任何第三方。"
  },
  "🌐 Hồ Sơ Cộng Đồng (Của Người Khác)": {
    "en": "🌐 Community Profile (Other People's)",
    "ja": "🌐 コミュニティプロフィール (他の人の)",
    "cn": "🌐 社区简介（其他人的）"
  },
  "✨ Tạo & Thiết Kế Trang Sakura Bio": {
    "en": "✨ Create & Design Sakura Bio Page",
    "ja": "✨ サクラバイオページの作成とデザイン",
    "cn": "✨ 创建和设计 Sakura Bio 页面"
  },
  "Chế độ Điện thoại di động (390px)": {
    "en": "Mobile Mode (390px)",
    "ja": "モバイルモード (390px)",
    "cn": "移动模式（390 像素）"
  },
  "Tự Động (dựa theo độ dài từ khóa)": {
    "en": "Automatic (based on keyword length)",
    "ja": "自動 (キーワードの長さに基づいて)",
    "cn": "自动（基于关键字长度）"
  },
  "Bạn chỉ thấy server mình có quyền": {
    "en": "You only see the server you have permission to",
    "ja": "権限のあるサーバーのみが表示されます",
    "cn": "您只能看到您有权访问的服务器"
  },
  "💾 Thực Hiện Cấp Phát / Điều Chỉnh": {
    "en": "💾 Perform Allocation / Adjustment",
    "ja": "💾 割り当て/調整を実行する",
    "cn": "💾 进行分配/调整"
  },
  "Hết hạn sau (giờ, 0 = vĩnh viễn):": {
    "en": "Expires in (hours, 0 = forever):",
    "ja": "有効期限が切れます (時間、0 = 永久):",
    "cn": "过期时间（小时，0 = 永远）："
  },
  "Tên loài cá (Kèm emoji đại diện):": {
    "en": "Fish species name (with representative emoji):",
    "ja": "魚種名（代表的な絵文字付き）：",
    "cn": "鱼种名称（带代表性表情符号）："
  },
  "🗝️ Chìa Khóa Cổ Đại (key_ancient)": {
    "en": "🗝️ Ancient Key (key_ancient)",
    "ja": "🗝️ 古代の鍵 (key_ancient)",
    "cn": "🗝️ 古代钥匙 (key_ancient)"
  },
  "Hệ Số Đập Đồ (Refine Multiplier):": {
    "en": "Refine Multiplier:",
    "ja": "乗数を調整:",
    "cn": "精炼乘数："
  },
  "Hệ Số Tiến Sao (Star Multiplier):": {
    "en": "Star Multiplier:",
    "ja": "スターマルチプライヤー:",
    "cn": "星级倍增器："
  },
  "Vận May Đào Mỏ (Sản lượng quặng):": {
    "en": "Mining Luck (Ore output):",
    "ja": "採掘運（鉱石産出量）：",
    "cn": "采矿运气（矿石产量）："
  },
  "Số ô chứa mở rộng (+extra slots):": {
    "en": "Number of expansion slots (+extra slots):",
    "ja": "拡張スロットの数 (+ 追加スロット):",
    "cn": "扩展插槽数量（+额外插槽）："
  },
  "Cả 2 người bị nổ trừ 50,000 coin!": {
    "en": "Both people exploded minus 50,000 coins!",
    "ja": "二人ともマイナス5万コイン爆発しました！",
    "cn": "两人都炸掉了负五万币！"
  },
  "Các Ô Đất Canh Tác Thời Gian Thực": {
    "en": "Real Time Farming Plots",
    "ja": "リアルタイム農業プロット",
    "cn": "实时农田"
  },
  "✨ Bụi Sao Lấp Lánh (Tiến Cấp Sao)": {
    "en": "✨ Sparkling Star Dust (Star Level Up)",
    "ja": "✨ スパークリングスターダスト (スターレベルアップ)",
    "cn": "✨ 闪闪发光的星尘（星级提升）"
  },
  "Danh Sách Thành Tựu Toàn Hệ Thống": {
    "en": "List of Systemwide Achievements",
    "ja": "システム全体の実績のリスト",
    "cn": "全系统成就清单"
  },
  ": tin nhắn chứa chuỗi → chặn. VD:": {
    "en": ": message contains string → block. For example:",
    "ja": ": メッセージには文字列→ブロックが含まれています。たとえば:",
    "cn": "：消息包含字符串→块。例如："
  },
  "🎉 Danh Sách Giveaway Đang Diễn Ra": {
    "en": "🎉 Ongoing Giveaway List",
    "ja": "🎉 進行中のプレゼントリスト",
    "cn": "🎉 持续赠品清单"
  },
  "🎨 Cấu Hình Khung Embed (Tùy Chọn)": {
    "en": "🎨 Embed Frame Configuration (Optional)",
    "ja": "🎨 埋め込みフレーム構成 (オプション)",
    "cn": "🎨 嵌入框架配置（可选）"
  },
  "Ví dụ: 🐧 Chim Cánh Cụt Băng Tuyết": {
    "en": "For example: 🐧 Snowy Penguin",
    "ja": "例: 🐧 雪に覆われたペンギン",
    "cn": "例如：🐧 雪企鹅"
  },
  "Ví dụ: 🐸 Thuốc Biến Hình Ếch Xanh": {
    "en": "For example: 🐸 Green Frog Transformation Potion",
    "ja": "例: 🐸 緑のカエルの変身ポーション",
    "cn": "例如：🐸绿蛙变身药水"
  },
  "⚡ Xem menu lệnh Level & Kinh tế →": {
    "en": "⚡ See Level & Economy command menu →",
    "ja": "⚡ レベルとエコノミーコマンドメニューを参照 →",
    "cn": "⚡ 查看等级和经济命令菜单 →"
  },
  "Đang chuẩn bị xác thực Discord...": {
    "en": "Preparing to authenticate Discord...",
    "ja": "Discord を認証する準備をしています...",
    "cn": "准备验证 Discord..."
  },
  "-- Chưa chọn kênh chat đồng bộ --": {
    "en": "-- No sync chat channel selected --",
    "ja": "-- 同期チャット チャネルが選択されていません --",
    "cn": "-- 未选择同步聊天频道 --"
  },
  "Chọn một người chơi để soi kho đồ": {
    "en": "Choose a player to check the inventory",
    "ja": "インベントリを確認するプレーヤーを選択してください",
    "cn": "选择一名玩家查看库存"
  },
  "Những Gì Chúng Tôi KHÔNG Thu Thập": {
    "en": "What We DO NOT Collect",
    "ja": "収集しないもの",
    "cn": "我们不收集什么"
  },
  "Phần thưởng vai trò (Level Roles)": {
    "en": "Level Roles",
    "ja": "レベルの役割",
    "cn": "级别角色"
  },
  "📜 Điều khoản Dịch vụ — Sakura Bot": {
    "en": "📜 Terms of Service — Sakura Bot",
    "ja": "📜利用規約 — さくらボット",
    "cn": "📜 服务条款 — Sakura Bot"
  },
  "Giới Hạn Trách Nhiệm (Disclaimer)": {
    "en": "Limitation of Liability (Disclaimer)",
    "ja": "責任の制限（免責事項）",
    "cn": "责任限制（免责声明）"
  },
  "📥 TÙY CHỌN CHẤT LƯỢNG & TẢI XUỐNG": {
    "en": "📥 QUALITY & DOWNLOAD OPTIONS",
    "ja": "📥 品質とダウンロードのオプション",
    "cn": "📥 质量和下载选项"
  },
  "Tip: Bạn cũng có thể mở trực tiếp": {
    "en": "Tip: You can also open it directly",
    "ja": "ヒント: 直接開くこともできます",
    "cn": "提示：也可以直接打开"
  },
  "🕵️ Ẩn Danh (Giấu ký tự & độ dài)": {
    "en": "🕵️ Anonymous (Hide characters & length)",
    "ja": "🕵️ 匿名 (文字と長さを非表示)",
    "cn": "🕵️匿名（隐藏字符和长度）"
  },
  "🌸 Chào mừng đến với Scribble It!": {
    "en": "🌸 Welcome to Scribble It!",
    "ja": "🌸 Scribble It へようこそ!",
    "cn": "🎈欢迎来到涂鸦它！"
  },
  "📖 Sakura Bot — Hướng dẫn sử dụng": {
    "en": "📖 Sakura Bot — Instructions for use",
    "ja": "📖 さくらボット — 使用説明書",
    "cn": "📖 Sakura Bot — 使用说明"
  },
  "Cường hóa / Đột phá (+0 - +300):": {
    "en": "Enhancement / Breakthrough (+0 - +300):",
    "ja": "強化/ブレークスルー (+0 - +300):",
    "cn": "增强/突破（+0 - +300）："
  },
  "🔓 Không cần chìa khóa (Mở tự do)": {
    "en": "🔓 No key needed (Open freely)",
    "ja": "🔓 鍵不要（自由に開けられます）",
    "cn": "🔓无需钥匙（自由开启）"
  },
  "Vận May Câu Cá (Bắt cá hiếm/to):": {
    "en": "Fishing Luck (Catch rare/big fish):",
    "ja": "釣り運（珍しい魚・大きな魚が釣れる）：",
    "cn": "钓鱼运气（捕获稀有/大鱼）："
  },
  "🔮 Mồi ẩn (Kiếm từ sự kiện/rương)": {
    "en": "🔮 Hidden Lure (Earn from events/chests)",
    "ja": "🔮 隠しルアー (イベント/宝箱から獲得)",
    "cn": "🔮 隐藏的诱惑（从活动/宝箱中赚取）"
  },
  "💣 BOMB (Bom nổ trừ tiền đôi bên)": {
    "en": "💣 BOMB (Bomb explodes to deduct money from both sides)",
    "ja": "💣 BOMB (爆弾が爆発して双方からお金を差し押さえます)",
    "cn": "💣 BOMB（炸弹爆炸双方扣钱）"
  },
  "để xem trang trại và điều chỉnh.": {
    "en": "to view the farm and make adjustments.",
    "ja": "農場を表示して調整します。",
    "cn": "查看农场并进行调整。"
  },
  "Nguyên Liệu Cường Hóa & Tiến Cấp": {
    "en": "Strengthening & Advanced Materials",
    "ja": "強化・先端材料",
    "cn": "强化及先进材料"
  },
  "🔮 Tinh Thể End Crystal (Enchant)": {
    "en": "🔮 End Crystal (Enchant)",
    "ja": "🔮 エンドクリスタル (エンチャント)",
    "cn": "🔮 末影水晶（附魔）"
  },
  "🌫️ Sương Giá Băng Phủ (Chậm lớn)": {
    "en": "🌫️ Frost Covered (Slow growth)",
    "ja": "🌫️ 霜に覆われている (成長が遅い)",
    "cn": "🌫️霜冻覆盖（生长缓慢）"
  },
  "🔨 Thần Rèn (x5 Đập Cuốc, x3 Sao)": {
    "en": "🔨 Forge God (x5 Pickaxes, x3 Stars)",
    "ja": "🔨 フォージゴッド (ツルハシx5、スターx3)",
    "cn": "🔨 锻造之神（x5 镐，x3 星星）"
  },
  "Nạp Vào Minecraft (Discord ➔ MC)": {
    "en": "Load into Minecraft (Discord ➔ MC)",
    "ja": "Minecraft にロードする (Discord ➔ MC)",
    "cn": "加载到 Minecraft（Discord ➔ MC）"
  },
  "Cấp / Thu Hồi Thành Tựu Cho User": {
    "en": "Grant / Revoke Achievements to Users",
    "ja": "ユーザーへの実績の付与/取り消し",
    "cn": "向用户授予/撤销成就"
  },
  "Thiết Kế Thành Tựu Tùy Chỉnh Mới": {
    "en": "New Custom Achievement Design",
    "ja": "新しいカスタム実績デザイン",
    "cn": "新的定制成就设计"
  },
  "Quản Lý Giveaway Cho Từng Server": {
    "en": "Manage Giveaway For Each Server",
    "ja": "各サーバーのプレゼントを管理する",
    "cn": "管理每台服务器的赠品"
  },
  "Số Điện Thoại Zalo (ZALO_PHONE):": {
    "en": "Zalo Phone Number (ZALO_PHONE):",
    "ja": "Zalo 電話番号 (ZALO_PHONE):",
    "cn": "扎洛电话号码 (ZALO_PHONE)："
  },
  "💾 Lưu Toàn Bộ Cấu Hình config.py": {
    "en": "💾 Save All Configuration config.py",
    "ja": "💾 すべての設定を保存 config.py",
    "cn": "💾 保存所有配置config.py"
  },
  "Chỉ Administrator được dùng lệnh": {
    "en": "Only Administrators can use commands",
    "ja": "管理者のみがコマンドを使用できます",
    "cn": "只有管理员可以使用命令"
  },
  "Xem Trước Thông Báo Server Boost": {
    "en": "Preview Server Boost Notification",
    "ja": "サーバーブースト通知のプレビュー",
    "cn": "预览服务器提升通知"
  },
  ".. hoặc panel nút. Bot cần quyền": {
    "en": ".. or button panel. Bots need permissions",
    "ja": ".. またはボタンパネル。ボットには権限が必要です",
    "cn": "..或按钮面板。机器人需要权限"
  },
  "mỗi confession có 1 thread riêng": {
    "en": "Each confession has its own thread",
    "ja": "それぞれの告白には独自のスレッドがある",
    "cn": "每个告白都有自己的线索"
  },
  "(trống = gửi ngay tại kênh chat)": {
    "en": "(empty = send immediately in chat channel)",
    "ja": "(空 = チャット チャネルですぐに送信)",
    "cn": "（空=立即在聊天频道中发送）"
  },
  "Cho phép câu ngoài kênh quy định": {
    "en": "Fishing outside the prescribed channel is allowed",
    "ja": "所定の水路以外での釣りは許可されています",
    "cn": "允许在规定航道外钓鱼"
  },
  "Tin nhắn chứa từ khóa (Contains)": {
    "en": "Messages containing keywords (Contains)",
    "ja": "キーワードを含むメッセージ (含む)",
    "cn": "包含关键字的消息（包含）"
  },
  "GỬI LỆNH CONSOLE (RCON TERMINAL)": {
    "en": "SEND CONSOLE COMMAND (RCON TERMINAL)",
    "ja": "コンソールコマンド送信（RCONターミナル）",
    "cn": "发送控制台命令（RCON 终端）"
  },
  "Nhập Discord User ID nông dân...": {
    "en": "Enter Discord User ID farmer...",
    "ja": "Discord ユーザー ID ファーマーを入力してください...",
    "cn": "输入 Discord 用户 ID 农民..."
  },
  "⚡ Xem menu lệnh Welcome & Role →": {
    "en": "⚡ See Welcome & Role command menu →",
    "ja": "⚡ 「ようこそと役割」コマンド メニューを参照 →",
    "cn": "⚡ 请参阅欢迎和角色命令菜单→"
  },
  "Xem toàn bộ mã nguồn trên GitHub": {
    "en": "See the full source code on GitHub",
    "ja": "GitHub で完全なソース コードを参照してください",
    "cn": "查看 GitHub 上的完整源代码"
  },
  "🔐 Đăng nhập Discord — Sakura Bot": {
    "en": "🔐 Login to Discord — Sakura Bot",
    "ja": "🔐 Discordにログイン — さくらボット",
    "cn": "🔐 登录 Discord — Sakura Bot"
  },
  "Nhập tên người chơi Minecraft...": {
    "en": "Enter Minecraft player name...",
    "ja": "Minecraft のプレイヤー名を入力してください...",
    "cn": "输入 Minecraft 玩家名称..."
  },
  "Đang tải danh sách phân quyền...": {
    "en": "Loading list of permissions...",
    "ja": "権限のリストを読み込んでいます...",
    "cn": "正在加载权限列表..."
  },
  "Đang tải danh sách người chơi...": {
    "en": "Loading player list...",
    "ja": "プレイヤーリストを読み込んでいます...",
    "cn": "正在加载玩家列表..."
  },
  "Backup dữ liệu trước khi cài đặt": {
    "en": "Backup data before installation",
    "ja": "インストール前にデータをバックアップする",
    "cn": "安装前备份数据"
  },
  "Quyền Xóa Dữ Liệu Của Người Dùng": {
    "en": "User's Right to Data Deletion",
    "ja": "データ削除に対するユーザーの権利",
    "cn": "用户删除数据的权利"
  },
  ", nhập biệt danh mới và bấm Lưu.": {
    "en": ", enter a new nickname, and click Save.",
    "ja": "をクリックし、新しいニックネームを入力し、「保存」をクリックします。",
    "cn": "，输入新的昵称，然后单击“保存”。"
  },
  "🤖 Luyện Tập (Vẽ tự do cùng Bot)": {
    "en": "🤖 Practice (Draw freely with Bot)",
    "ja": "🤖 練習（ボットで自由に描く）",
    "cn": "🤖 练习（用Bot自由绘画）"
  },
  "Nhập tin nhắn... (Enter để gửi)": {
    "en": "Enter message... (Enter to send)",
    "ja": "メッセージを入力してください... (送信するには入力してください)",
    "cn": "输入消息...（输入发送）"
  },
  "Thông Tin Kỹ Thuật Chi Tiết Bot": {
    "en": "Detailed Technical Information Bot",
    "ja": "詳細技術情報ボット",
    "cn": "详细技术信息机器人"
  },
  "hàng ngày và có hạn sử dụng đến": {
    "en": "daily and has an expiration date",
    "ja": "毎日、有効期限あり",
    "cn": "每日并有有效期"
  },
  "Danh Sách Mã Giftcode Hiện Có (": {
    "en": "List of Existing Giftcode Codes (",
    "ja": "既存のギフトコード コードのリスト (",
    "cn": "现有礼品代码列表（"
  },
  "🫧 Thủy cung tương tác sống động": {
    "en": "🫧 Lively interactive aquarium",
    "ja": "🫧 活気あふれるインタラクティブな水族館",
    "cn": "🫧 热闹的互动水族馆"
  },
  "Sáng Tạo Vật Phẩm Tùy Chỉnh Mới": {
    "en": "New Custom Item Creation",
    "ja": "新しいカスタムアイテムの作成",
    "cn": "新的自定义项目创建"
  },
  "Có thể kiếm từ đâu (Nguồn gốc):": {
    "en": "Where can you get it from (Origin):",
    "ja": "どこから入手できますか (起源):",
    "cn": "从哪里可以获得（来源）："
  },
  "Mã định danh ID (fish_bag_...):": {
    "en": "Identifier ID (fish_bag_...):",
    "ja": "識別子ID (fish_bag_...):",
    "cn": "标识符ID（fish_bag_...）："
  },
  "Mô tả hiệu ứng kỹ năng của Pet:": {
    "en": "Description of Pet's skill effects:",
    "ja": "ペットのスキル効果の説明:",
    "cn": "宠物技能效果说明："
  },
  "💬 CUSTOM_MSG (Thông điệp troll)": {
    "en": "💬 CUSTOM_MSG (Troll message)",
    "ja": "💬 CUSTOM_MSG (荒らしメッセージ)",
    "cn": "💬 CUSTOM_MSG（巨魔消息）"
  },
  "Nạn nhân bị đông cứng không thể": {
    "en": "The frozen victim cannot",
    "ja": "冷凍された被害者はできません",
    "cn": "被冰冻的受害者不能"
  },
  "🔄 Hủy Bỏ Cưỡng Chế (Về Tự Động)": {
    "en": "🔄 Forced Cancellation (Automatic Return)",
    "ja": "🔄強制キャンセル（自動復帰）",
    "cn": "🔄 强制取消（自动返回）"
  },
  "Discord User ID của Người Chơi:": {
    "en": "Discord User ID of the Player:",
    "ja": "プレイヤーの Discord ユーザー ID:",
    "cn": "玩家的 Discord 用户 ID："
  },
  "⛏️ Thêm Trang Bị Khoáng Sản Mới": {
    "en": "⛏️ Add New Mineral Equipment",
    "ja": "⛏️ 新しい鉱物装備を追加",
    "cn": "⛏️ 添加新的矿物设备"
  },
  "🌱 Thêm Vật Phẩm Nông Nghiệp Mới": {
    "en": "🌱 Add New Agricultural Items",
    "ja": "🌱 新しい農業アイテムを追加",
    "cn": "🌱 添加新的农业项目"
  },
  "Mô Hình AI Mặc Định (AI_MODEL):": {
    "en": "Default AI Model (AI_MODEL):",
    "ja": "デフォルトの AI モデル (AI_MODEL):",
    "cn": "默认AI模型（AI_MODEL）："
  },
  "Bật hệ thống kiểm duyệt tự động": {
    "en": "Turn on the automatic moderation system",
    "ja": "自動モデレーション システムをオンにする",
    "cn": "开启自动审核系统"
  },
  "BIỆT DANH BOT (SERVER NICKNAME)": {
    "en": "BOT NAME (SERVER NICKNAME)",
    "ja": "ボット名 (サーバーのニックネーム)",
    "cn": "机器人名称（服务器昵称）"
  },
  "Nội dung tin nhắn (Description)": {
    "en": "Message content (Description)",
    "ja": "メッセージ内容（説明）",
    "cn": "留言内容（说明）"
  },
  "ở tab Tổng quan để có hiệu lực.": {
    "en": "in the Overview tab to take effect.",
    "ja": "[概要] タブで有効にします。",
    "cn": "在概览选项卡中即可生效。"
  },
  "nơi đăng panel & các confession": {
    "en": "where to post panels & confessions",
    "ja": "パネルと告白を投稿する場所",
    "cn": "在哪里张贴面板和忏悔"
  },
  "📢 Phát Sóng Mã Code & Ping Role": {
    "en": "📢 Broadcast Code & Ping Role",
    "ja": "📢 ブロードキャスト コードと Ping の役割",
    "cn": "📢 广播代码和 Ping 角色"
  },
  "Ví dụ: 💎 Rương Hải Tặc Atlantis": {
    "en": "For example: 💎 Atlantis Pirate Chest",
    "ja": "例: 💎 アトランティス海賊チェスト",
    "cn": "例如：💎亚特兰蒂斯海盗宝箱"
  },
  "Ví dụ: Đạt mốc câu cá mùa hè...": {
    "en": "For example: Reaching summer fishing milestone...",
    "ja": "例: 夏釣りのマイルストーンに到達...",
    "cn": "例如：达到夏季钓鱼里程碑......"
  },
  "Ghi chú thêm về vật phẩm này...": {
    "en": "Additional notes about this item...",
    "ja": "この商品に関する追加の注意事項...",
    "cn": "关于此项目的附加说明..."
  },
  "Ví dụ: 📢 [THÔNG BÁO QUAN TRỌNG]": {
    "en": "For example: 📢 [IMPORTANT NOTICE]",
    "ja": "例: 📢 【重要なお知らせ】",
    "cn": "例如：📢【重要通知】"
  },
  "Bot Discord • Âm nhạc • Quản lý": {
    "en": "Discord Bot • Music • Management",
    "ja": "Discord ボット • 音楽 • 管理",
    "cn": "Discord 机器人 • 音乐 • 管理"
  },
  "⚡ Xem menu lệnh Ticket hỗ trợ →": {
    "en": "⚡ See the Support Ticket command menu →",
    "ja": "⚡ サポートチケットコマンドメニューを参照 →",
    "cn": "⚡ 查看支持票命令菜单 →"
  },
  "Xem hướng dẫn chi tiết 3 bước →": {
    "en": "See detailed 3-step instructions →",
    "ja": "詳細な 3 ステップの手順を参照→",
    "cn": "请参阅详细的 3 步说明 →"
  },
  "🔍 Tìm kiếm tệp trong thư mục...": {
    "en": "🔍 Search for files in folders...",
    "ja": "🔍 フォルダー内のファイルを検索...",
    "cn": "🔍 搜索文件夹中的文件..."
  },
  "🔍 Tìm kiếm người chơi / UUID...": {
    "en": "🔍 Search for players / UUID...",
    "ja": "🔍 プレーヤー/UUIDを検索...",
    "cn": "🔍 搜索玩家/UUID..."
  },
  "Bật (Chỉ người trong Whitelist)": {
    "en": "On (Only people in Whitelist)",
    "ja": "オン (ホワイトリストに登録されている人のみ)",
    "cn": "开启（仅限白名单中的人员）"
  },
  "Chế độ chơi mặc định (Gamemode)": {
    "en": "Default game mode (Gamemode)",
    "ja": "デフォルトのゲームモード (Gamemode)",
    "cn": "默认游戏模式（Gamemode）"
  },
  "Đánh nhau giữa người chơi (PVP)": {
    "en": "Player PvP (PVP)",
    "ja": "プレイヤー PvP (PVP)",
    "cn": "玩家对战 (PVP)"
  },
  "Hệ Thống Hosting Đang Hoạt Động": {
    "en": "Hosting System Is Active",
    "ja": "ホスティング システムはアクティブです",
    "cn": "托管系统处于活动状态"
  },
  "💬 Ý kiến đóng góp & trải nghiệm": {
    "en": "💬 Opinions & experiences",
    "ja": "💬 意見と経験",
    "cn": "💬意见和经验"
  },
  "Liên Kết Bên Thứ Ba & Minecraft": {
    "en": "Third Party Links & Minecraft",
    "ja": "サードパーティのリンクと Minecraft",
    "cn": "第三方链接和 Minecraft"
  },
  "Thành Tựu & Danh Hiệu Minigame": {
    "en": "Minigame Achievements & Trophies",
    "ja": "ミニゲームの実績とトロフィー",
    "cn": "迷你游戏成就和奖杯"
  },
  "https://discord.gg/... hoặc ID": {
    "en": "https://discord.gg/... or ID",
    "ja": "https://discord.gg/... または ID",
    "cn": "https://discord.gg/... 或 ID"
  },
  "Đang truy vấn cơ sở dữ liệu...": {
    "en": "Querying the database...",
    "ja": "データベースにクエリを実行しています...",
    "cn": "正在查询数据库..."
  },
  "👑 Siêu Lớn 15×15 (Nối 5 Thắng)": {
    "en": "👑 Super Large 15×15 (Connect 5 Wins)",
    "ja": "👑 スーパーラージ 15×15 (5 つの勝利を接続)",
    "cn": "👑 超大15×15（连线5胜）"
  },
  "📖 Hướng dẫn sử dụng Sakura Bot": {
    "en": "📖 Instructions for using Sakura Bot",
    "ja": "📖 さくらボットの使い方",
    "cn": "📖 Sakura Bot 使用说明"
  },
  "Web panel tích hợp trong bot (": {
    "en": "Web panel integrated in bot (",
    "ja": "ボットに統合された Web パネル (",
    "cn": "集成在机器人中的 Web 面板（"
  },
  "Đang tải trạng thái các API...": {
    "en": "Loading API status...",
    "ja": "API ステータスを読み込み中...",
    "cn": "正在加载 API 状态..."
  },
  "Lượt dùng tối đa (0 = vô hạn):": {
    "en": "Maximum usage (0 = infinite):",
    "ja": "最大使用量 (0 = 無限):",
    "cn": "最大使用量（0 = 无限）："
  },
  "Thêm Loài Cá Mới Vào Đại Dương": {
    "en": "Adding New Fish Species to the Ocean",
    "ja": "新しい魚種を海に加える",
    "cn": "向海洋添加新的鱼类"
  },
  "Chìa Khóa Yêu Cầu Để Mở Rương:": {
    "en": "Key Required to Open Chest:",
    "ja": "チェストを開けるには鍵が必要です:",
    "cn": "打开宝箱所需的钥匙："
  },
  "🔨 Thần Rèn (x5 Đập Đồ, x3 Sao)": {
    "en": "🔨 Forge God (x5 Smashing Items, x3 Stars)",
    "ja": "🔨 フォージゴッド (x5 スマッシングアイテム、x3 スター)",
    "cn": "🔨 锻造之神（x5 粉碎物品，x3 星星）"
  },
  "Cường hóa luôn 100% thành công": {
    "en": "Enhancement is always 100% successful",
    "ja": "強化は常に 100% 成功します",
    "cn": "增强总是 100% 成功"
  },
  "❌ Không thể gia hạn (Tiêu hao)": {
    "en": "❌ Cannot be renewed (Consumable)",
    "ja": "❌ 更新不可（消耗品）",
    "cn": "❌ 无法续订（消耗品）"
  },
  "🔄 REVERSE_TEXT (Nói ngược chữ)": {
    "en": "🔄 REVERSE_TEXT (Say words backwards)",
    "ja": "🔄 REVERSE_TEXT (単語を逆に言う)",
    "cn": "🔄 REVERSE_TEXT（倒着说单词）"
  },
  "➕ Thêm Vật Phẩm Troll Vào Game": {
    "en": "➕ Add Troll Items to the Game",
    "ja": "➕ トロールアイテムをゲームに追加",
    "cn": "➕ 将巨魔物品添加到游戏中"
  },
  "🛠️ Cập Nhật Dụng Cụ / Phân Bón": {
    "en": "🛠️ Update Tools / Fertilizers",
    "ja": "🛠️ ツール/肥料を更新",
    "cn": "🛠️更新工具/肥料"
  },
  "Đang chạy theo chu kỳ tự nhiên": {
    "en": "Running in natural cycles",
    "ja": "自然なサイクルで走る",
    "cn": "自然循环运行"
  },
  "Chọn Thời Tiết Muốn Thiết Lập:": {
    "en": "Select the Weather You Want to Set:",
    "ja": "設定したい天気を選択してください:",
    "cn": "选择您要设置的天气："
  },
  "➕ Khởi Tạo & Lưu Thành Tựu Mới": {
    "en": "➕ Create & Save New Achievements",
    "ja": "➕ 新しい実績を作成して保存",
    "cn": "➕ 创造并保存新成就"
  },
  "➕ Thêm Từ Vựng Mới Vào Từ Điển": {
    "en": "➕ Add New Vocabulary to Dictionary",
    "ja": "➕ 新しい語彙を辞書に追加",
    "cn": "➕ 将新词汇添加到词典中"
  },
  "Cổng Web Dashboard (WEB_PORT):": {
    "en": "Web Dashboard Port (WEB_PORT):",
    "ja": "Web ダッシュボード ポート (WEB_PORT):",
    "cn": "Web 仪表板端口 (WEB_PORT)："
  },
  "để khiếu nại). Gỡ cấm bằng nút": {
    "en": "to complain). Unblock with button",
    "ja": "文句を言う）。ボタンでブロックを解除",
    "cn": "来抱怨）。使用按钮解锁"
  },
  "🎁 Kênh nhận thông báo Giftcode": {
    "en": "🎁 Channel to receive Giftcode notifications",
    "ja": "🎁 ギフトコード通知を受け取るチャンネル",
    "cn": "🎁 接收礼品代码通知的渠道"
  },
  "Chính xác cả câu (Exact Match)": {
    "en": "Exact Match",
    "ja": "完全一致",
    "cn": "精确匹配"
  },
  "📋 Các Bảng Role Đang Hoạt Động": {
    "en": "📋 Active Role Tables",
    "ja": "📋 アクティブな役割テーブル",
    "cn": "📋 活跃角色表"
  },
  "💍 Chỉnh Sửa Thông Tin Hôn Nhân": {
    "en": "💍 Edit Marriage Information",
    "ja": "💍 結婚情報を編集する",
    "cn": "💍编辑婚姻信息"
  },
  "🎣 Chỉnh Sửa Thuộc Tính Cần Câu": {
    "en": "🎣 Edit Fishing Rod Attributes",
    "ja": "🎣 釣り竿の属性を編集する",
    "cn": "🎣 编辑钓鱼竿属性"
  },
  "Ví dụ: 🪐 Mồi Tinh Vân Tinh Thể": {
    "en": "For example: 🪐 Crystal Nebula Bait",
    "ja": "例: 🪐 クリスタルネビュラベイト",
    "cn": "例如：🪐水晶星云饵"
  },
  "Ví dụ: 📦 Thùng Siêu Không Gian": {
    "en": "For example: 📦 Hyper Space Bin",
    "ja": "例: 📦 ハイパースペースビン",
    "cn": "例如：📦 超空间箱"
  },
  "Kênh Ghi Log Server (Discord):": {
    "en": "Server Logging Channel (Discord):",
    "ja": "サーバーログチャンネル (Discord):",
    "cn": "服务器日志通道（Discord）："
  },
  "Buộc dừng process ngay lập tức": {
    "en": "Force stop the process immediately",
    "ja": "プロセスをただちに強制停止する",
    "cn": "立即强制停止进程"
  },
  "➕ Cấp Quyền Cho Người Dùng Mới": {
    "en": "➕ Grant Permissions to New Users",
    "ja": "➕ 新しいユーザーに権限を付与する",
    "cn": "➕ 向新用户授予权限"
  },
  "Icon Máy Chủ (server-icon.png)": {
    "en": "Server Icon (server-icon.png)",
    "ja": "サーバーアイコン (server-icon.png)",
    "cn": "服务器图标 (server-icon.png)"
  },
  "Đường Dẫn Gói Tài Nguyên (URL)": {
    "en": "Resource Package Link (URL)",
    "ja": "リソース パッケージ リンク (URL)",
    "cn": "资源包链接（URL）"
  },
  "Địa chỉ IP Máy Chủ (Server IP)": {
    "en": "Server IP Address (Server IP)",
    "ja": "サーバーIPアドレス (サーバーIP)",
    "cn": "服务器IP地址（服务器IP）"
  },
  "Danh sách cho phép (Whitelist)": {
    "en": "Whitelist",
    "ja": "ホワイトリスト",
    "cn": "白名单"
  },
  "Sinh quái vật (Spawn Monsters)": {
    "en": "Spawn Monsters",
    "ja": "モンスターをスポーンする",
    "cn": "生成怪物"
  },
  "Sakura Plugin Help | Hướng dẫn": {
    "en": "Sakura Plugin Help | Instructions",
    "ja": "さくらプラグインのヘルプ |指示",
    "cn": "樱花插件帮助 |使用说明"
  },
  "Luôn backup trước khi cập nhật": {
    "en": "Always backup before updating",
    "ja": "アップデートする前に必ずバックアップを行ってください",
    "cn": "更新前务必备份"
  },
  "Điều khoản Dịch vụ của Discord": {
    "en": "Discord Terms of Service",
    "ja": "Discord利用規約",
    "cn": "不和谐服务条款"
  },
  "✨ Trạng thái kết nối & Xã hội": {
    "en": "✨ Social & Connection Status",
    "ja": "✨ ソーシャル＆コネクションステータス",
    "cn": "✨ 社交和联系状态"
  },
  "Thông Tin Cá Nhân & Định Danh": {
    "en": "Personal Information & Identifiers",
    "ja": "個人情報と識別子",
    "cn": "个人信息和标识符"
  },
  "Tên đường dẫn (Username Slug)": {
    "en": "Username Slug",
    "ja": "ユーザー名スラッグ",
    "cn": "用户名 蛞蝓"
  },
  "📱 Zalo URL hoặc Số điện thoại": {
    "en": "📱 Zalo URL or Phone number",
    "ja": "📱 Zalo URLまたは電話番号",
    "cn": "📱 Zalo 网址或电话号码"
  },
  "🚀 Lưu & Mở Trang Profile Ngay": {
    "en": "🚀 Save & Open Profile Page Now",
    "ja": "🚀 今すぐ保存してプロフィールページを開く",
    "cn": "🚀 立即保存并打开个人资料页面"
  },
  "⚡ Bàn Điều Khiển Truy Vấn SQL": {
    "en": "⚡ SQL Query Console",
    "ja": "⚡ SQLクエリコンソール",
    "cn": "⚡ SQL 查询控制台"
  },
  "Không thể tải danh sách Cogs.": {
    "en": "Unable to load Cogs list.",
    "ja": "歯車リストをロードできません。",
    "cn": "无法加载 Cogs 列表。"
  },
  "Kết quả sẽ xuất hiện ở đây...": {
    "en": "The results will appear here...",
    "ja": "結果はここに表示されます...",
    "cn": "结果将出现在这里..."
  },
  "Thao Tác Nhanh Trạng Thái Bot": {
    "en": "Quick Operation of Bot Status",
    "ja": "ボットステータスのクイック操作",
    "cn": "Bot状态快速操作"
  },
  "Module Bảo Mật Đang Hoạt Động": {
    "en": "Security Module Active",
    "ja": "セキュリティモジュールがアクティブです",
    "cn": "安全模块激活"
  },
  "📢 Phát sóng kênh Giftcode bot": {
    "en": "📢 Broadcast the Giftcode bot channel",
    "ja": "📢 Giftcode ボットチャンネルをブロードキャストする",
    "cn": "📢 广播 Giftcode 机器人频道"
  },
  "⚠️ Buộc phát hành lại (Force)": {
    "en": "⚠️ Forced re-release (Force)",
    "ja": "⚠️強制再解放（強制）",
    "cn": "⚠️强制重新释放（Force）"
  },
  "✨ Thêm Vào Bách Khoa Toàn Thư": {
    "en": "✨ Added to Encyclopedia",
    "ja": "✨百科事典に追加されました",
    "cn": "✨ 已添加至百科全书"
  },
  "Xem Trước Hiển Thị Trong Game": {
    "en": "Preview Displayed In Game",
    "ja": "ゲーム内に表示されるプレビュー",
    "cn": "游戏中显示的预览"
  },
  "Tên Rương (kèm icon bắt mắt):": {
    "en": "Chest name (with eye-catching icon):",
    "ja": "チェスト名 (目を引くアイコン付き):",
    "cn": "宝箱名称（带有醒目的图标）："
  },
  "🥉 Chìa Khóa Đồng (key_bronze)": {
    "en": "🥉 Bronze Key (key_bronze)",
    "ja": "🥉 ブロンズキー (key_bronze)",
    "cn": "🥉 青铜钥匙 (key_bronze)"
  },
  "🥇 Chìa Khóa Vàng (key_golden)": {
    "en": "🥇 Golden Key (key_golden)",
    "ja": "🥇 ゴールデンキー (key_golden)",
    "cn": "🥇 金钥匙 (key_golden)"
  },
  "⭐ God Mode Tiến Sao (1..20 ⭐)": {
    "en": "⭐ God Mode Tien Sao (1..20 ⭐)",
    "ja": "⭐ ゴッドモード ティエンサオ (1..20 ⭐)",
    "cn": "⭐ 上帝模式天嫂 (1..20 ⭐)"
  },
  "Tiến sao luôn 100% thành công": {
    "en": "Progress is always 100% successful",
    "ja": "進歩は常に 100% 成功します",
    "cn": "进步总是100%成功"
  },
  "Tỉ Lệ Biến Dị Địa Tầng Quặng:": {
    "en": "Rate of Ore Stratigraphic Variation:",
    "ja": "鉱石の層序変動の割合:",
    "cn": "矿石地层变化率："
  },
  "Tạo Vật Phẩm Troll & Tiện Ích": {
    "en": "Create Troll Items & Gadgets",
    "ja": "トロールアイテムとガジェットを作成する",
    "cn": "创建巨魔物品和小工具"
  },
  "💠 Đá Phép Khảm Ngoc (Mở Dòng)": {
    "en": "💠 Mosaic Magic Stone (Open Line)",
    "ja": "💠モザイク魔石(オープンライン)",
    "cn": "💠 马赛克魔法石（开线）"
  },
  "Cường Hóa Cuốc & Tiến Cấp Sao": {
    "en": "Enhance Pickaxe & Level Up Stars",
    "ja": "つるはしを強化してスターをレベルアップ",
    "cn": "增强镐和升级星星"
  },
  "Tiến sao cuốc 100% thành công": {
    "en": "The hoe is 100% successful",
    "ja": "鍬は100%成功しました",
    "cn": "锄头100%成功"
  },
  "Rút Về Discord (MC ➔ Discord)": {
    "en": "Withdraw to Discord (MC ➔ Discord)",
    "ja": "Discordに退会（MC ➔ Discord）",
    "cn": "撤回 Discord（MC ➔ Discord）"
  },
  "Chọn Máy Chủ Discord Cần Nối:": {
    "en": "Choose the Discord Server to Connect:",
    "ja": "接続する Discord サーバーを選択してください:",
    "cn": "选择要连接的 Discord 服务器："
  },
  "= tên hiển thị của thành viên": {
    "en": "= member's display name",
    "ja": "= メンバーの表示名",
    "cn": "= member's display name"
  },
  "vào / rời / chuyển kênh thoại": {
    "en": "enter/leave/switch voice channels",
    "ja": "音声チャンネルに入る/出る/切り替える",
    "cn": "进入/离开/切换语音通道"
  },
  "channel, role, đổi tên server": {
    "en": "channel, role, rename server",
    "ja": "チャネル、ロール、サーバー名の変更",
    "cn": "channel, role, rename server"
  },
  "; để biết ai mời ai cần quyền": {
    "en": "; To know who invited who needs permission",
    "ja": ";誰が誰を招待したかを知るには許可が必要です",
    "cn": "; To know who invited who needs permission"
  },
  "Tự do nhận nhiều role (Multi)": {
    "en": "Freedom to accept many roles (Multi)",
    "ja": "多くの役割を受け入れる自由 (マルチ)",
    "cn": "Freedom to accept many roles (Multi)"
  },
  "🎁 Quản Lý Phát Quà & Giveaway": {
    "en": "🎁 Gift Distribution & Giveaway Management",
    "ja": "🎁 ギフト配布と景品管理",
    "cn": "🎁 礼品分发和赠品管理"
  },
  "✏️ Chỉnh Sửa Cấp Độ & XP User": {
    "en": "✏️ Edit User Level & XP",
    "ja": "✏️ ユーザーレベルと XP を編集",
    "cn": "✏️ 编辑用户级别和 XP"
  },
  "🛒 Chỉnh Sửa Vật Phẩm Cửa Hàng": {
    "en": "🛒 Edit Shop Items",
    "ja": "🛒 ショップアイテムを編集",
    "cn": "🛒 Edit Shop Items"
  },
  "Ví dụ: ⚡ Cần Lôi Thần Sấm Sét": {
    "en": "For example: ⚡ Can Thunder God",
    "ja": "例: ⚡ 雷神はできますか",
    "cn": "For example: ⚡ Can Thunder God"
  },
  "Sakura Bot • Hẹn gặp lại bạn!": {
    "en": "Sakura Bot • See you soon!",
    "ja": "さくらボット • また会いましょう！",
    "cn": "Sakura Bot • See you soon!"
  },
  "Khởi động lại server qua RCON": {
    "en": "Restart the server via RCON",
    "ja": "RCON経由でサーバーを再起動します",
    "cn": "Restart the server via RCON"
  },
  "📁 Sakura MC — Quản Lý Tệp Tin": {
    "en": "📁 Sakura MC — File Manager",
    "ja": "📁 さくら MC — ファイルマネージャー",
    "cn": "📁 Sakura MC — 文件管理器"
  },
  "Đang tải danh sách tệp tin...": {
    "en": "Loading file list...",
    "ja": "ファイルリストを読み込んでいます...",
    "cn": "Loading file list..."
  },
  "Ví dụ: Tuyết Linh (Moderator)": {
    "en": "Example: Tuyet Linh (Moderator)",
    "ja": "例: Tuyet Linh (モデレーター)",
    "cn": "Example: Tuyet Linh (Moderator)"
  },
  "Sinh động vật (Spawn Animals)": {
    "en": "Spawn Animals",
    "ja": "動物をスポーンする",
    "cn": "Spawn Animals"
  },
  "Cổng kết nối RCON (RCON Port)": {
    "en": "RCON connection port (RCON Port)",
    "ja": "RCON接続ポート（RCONポート）",
    "cn": "RCON connection port (RCON Port)"
  },
  "Mật khẩu RCON (RCON Password)": {
    "en": "RCON Password (RCON Password)",
    "ja": "RCONパスワード (RCONパスワード)",
    "cn": "RCON密码（RCON密码）"
  },
  "Đang tải danh sách máy chủ...": {
    "en": "Loading server list...",
    "ja": "サーバーリストを読み込んでいます...",
    "cn": "Loading server list..."
  },
  "4. Cài đặt trước khi vào game": {
    "en": "4. Install before entering the game",
    "ja": "4. ゲームを始める前にインストールしてください",
    "cn": "4. Install before entering the game"
  },
  "Chính Sách Bảo Mật Sakura Bot": {
    "en": "Privacy Policy Sakura Bot",
    "ja": "プライバシーポリシー さくらボット",
    "cn": "Privacy Policy Sakura Bot"
  },
  "Điều Khoản Dịch Vụ Sakura Bot": {
    "en": "Terms of Service Sakura Bot",
    "ja": "利用規約 さくらボット",
    "cn": "樱花机器人服务条款"
  },
  "Quyền Của Ban Quản Trị Sakura": {
    "en": "Rights of Sakura Board of Management",
    "ja": "さくら経営委員会の権利",
    "cn": "樱花经营委员会的权利"
  },
  "Đường dẫn bio của bạn sẽ là:": {
    "en": "Your bio link will be:",
    "ja": "あなたのバイオリンクは次のようになります:",
    "cn": "Your bio link will be:"
  },
  "📁 Quản Lý Tệp & Nạp Lại Cogs": {
    "en": "📁 File Management & Cogs Reload",
    "ja": "📁 ファイル管理と歯車のリロード",
    "cn": "📁 文件管理和齿轮重新加载"
  },
  "⚙️ TẠO PHÒNG RIÊNG & CÀI ĐẶT": {
    "en": "⚙️ CREATE YOUR PRIVATE ROOM & SETUP",
    "ja": "⚙️ プライベートルームを作成してセットアップ",
    "cn": "⚙️ CREATE YOUR PRIVATE ROOM & SETUP"
  },
  "Đang quét danh sách phòng...": {
    "en": "Scanning room list...",
    "ja": "スキャンルームリスト...",
    "cn": "正在扫描房间列表..."
  },
  "Giám Sát Tài Nguyên Hệ Thống": {
    "en": "System Resource Monitoring",
    "ja": "システムリソースの監視",
    "cn": "系统资源监控"
  },
  "Thời Gian Hoạt Động (Uptime)": {
    "en": "Uptime",
    "ja": "稼働時間",
    "cn": "正常运行时间"
  },
  "để mở bảng điều khiển riêng.": {
    "en": "to open a separate control panel.",
    "ja": "をクリックして、別のコントロール パネルを開きます。",
    "cn": "打开单独的控制面板。"
  },
  "🪙 Coins (Tiền mặt phổ thông)": {
    "en": "🪙 Coins (Common Cash)",
    "ja": "🪙 コイン (共通現金)",
    "cn": "🪙 Coins (Common Cash)"
  },
  "Bảng Xếp Hạng Cần Thủ Câu Cá": {
    "en": "Fishing Angler Rankings",
    "ja": "釣り人ランキング",
    "cn": "钓鱼者排名"
  },
  "để xem kho đồ và điều chỉnh.": {
    "en": "to view inventory and make adjustments.",
    "ja": "在庫を表示し、調整を行います。",
    "cn": "查看库存并进行调整。"
  },
  "🎟️ Vật Phẩm Tiện Ích (Items)": {
    "en": "🎟️ Utility Items (Items)",
    "ja": "🎟️ ユーティリティアイテム (アイテム)",
    "cn": "🎟️ 实用物品（物品）"
  },
  "Số lượng (0 = Xóa khỏi kho):": {
    "en": "Quantity (0 = Removed from inventory):",
    "ja": "数量 (0 = 在庫から削除):",
    "cn": "数量（0 = 从库存中移除）："
  },
  "⚡ Phát Mã Daily Code Hôm Nay": {
    "en": "⚡ Distribute Daily Code Today",
    "ja": "⚡ デイリーコードを今すぐ配布",
    "cn": "⚡ 今天分发每日代码"
  },
  "Mã định danh ID (chest_...):": {
    "en": "Identifier ID (chest_...):",
    "ja": "識別子ID (chest_...):",
    "cn": "标识符ID（chest_...）："
  },
  "🥈 Chìa Khóa Bạc (key_silver)": {
    "en": "🥈 Silver Key (key_silver)",
    "ja": "🥈 シルバーキー (key_silver)",
    "cn": "🥈 银钥匙 (key_silver)"
  },
  "🃏 Vật Phẩm Troll & Tiện Ích:": {
    "en": "🃏 Troll Items & Gadgets:",
    "ja": "🃏 トロールアイテムとガジェット:",
    "cn": "🃏 巨魔物品和小工具："
  },
  "Thiết Lập Nhanh (Preset Mẫu)": {
    "en": "Quick Setup (Preset Templates)",
    "ja": "クイックセットアップ（プリセットテンプレート）",
    "cn": "快速设置（预设模板）"
  },
  "👑 God Mode Đập Đồ (+1..+150)": {
    "en": "👑 God Mode Smash Items (+1..+150)",
    "ja": "👑 ゴッドモードスマッシュアイテム (+1..+150)",
    "cn": "👑 上帝模式粉碎物品（+1..+150）"
  },
  "➕ Thêm Thú Cưng Vào Hệ Thống": {
    "en": "➕ Add Pets to the System",
    "ja": "➕ ペットをシステムに追加",
    "cn": "➕ 将宠物添加到系统中"
  },
  "🚪 VOICE_KICK (Đá khỏi voice)": {
    "en": "🚪 VOICE_KICK (Kick off voice)",
    "ja": "🚪 VOICE_KICK (キックオフボイス)",
    "cn": "🚪 VOICE_KICK（启动声音）"
  },
  "🎒 Túi Quặng Trong Khoang Đào": {
    "en": "🎒 Ore Bag In Digging Chamber",
    "ja": "🎒 採掘室の鉱石バッグ",
    "cn": "🎒 挖掘室中的矿石袋"
  },
  "Chọn Thành Tựu Cần Thao Tác:": {
    "en": "Select the Achievement that needs to be worked on:",
    "ja": "取り組む必要がある実績を選択してください:",
    "cn": "选择需要努力的成就："
  },
  "Danh Hiệu Độc Quyền (Title):": {
    "en": "Exclusive Title (Title):",
    "ja": "独占タイトル (タイトル):",
    "cn": "Exclusive Title (Title):"
  },
  "Mã ID (viết liền không dấu):": {
    "en": "ID code (written immediately without accents):",
    "ja": "ID コード (アクセントなしで直接記述):",
    "cn": "ID 代码（立即书写，不带重音符号）："
  },
  "• 🤖 Có thể dùng lệnh Discord": {
    "en": "• 🤖 Can use Discord commands",
    "ja": "• 🤖 Discordコマンドを使用できます",
    "cn": "• 🤖 可以使用Discord 命令"
  },
  "Hệ thống tiền tệ / ngân hàng": {
    "en": "Currency/banking system",
    "ja": "通貨/銀行システム",
    "cn": "Currency/banking system"
  },
  "BANNER URL (ẢNH BÌA PROFILE)": {
    "en": "BANNER URL (PROFILE COVER PHOTO)",
    "ja": "バナーURL（プロフィールカバー写真）",
    "cn": "横幅 URL（个人资料封面照片）"
  },
  "Đầu Embed (Tiêu đề / Author)": {
    "en": "Head Embed (Title / Author)",
    "ja": "ヘッドエンベッド (タイトル/著者)",
    "cn": "头嵌入（标题/作者）"
  },
  "+ Thêm kênh bỏ qua từ cấm...": {
    "en": "+ Add channels that skip forbidden words...",
    "ja": "+ 禁止ワードをスキップするチャンネルを追加...",
    "cn": "+ 添加跳过禁用词的频道..."
  },
  "➕ Thêm / Cập nhật Custom Key": {
    "en": "➕ Add/Update Custom Key",
    "ja": "➕ カスタムキーの追加/更新",
    "cn": "➕ 添加/更新自定义密钥"
  },
  "📦 Các Bản Sao Lưu Đã Lưu Trữ": {
    "en": "📦 Archived Backups",
    "ja": "📦 アーカイブされたバックアップ",
    "cn": "📦 Archived Backups"
  },
  "Thời lượng (vd: 10m, 1h, 1d)": {
    "en": "Duration (eg: 10m, 1h, 1d)",
    "ja": "期間 (例: 10 分、1 時間、1 日)",
    "cn": "持续时间（例如：10m、1h、1d）"
  },
  "📢 Đăng Bảng Nội Quy Vào Kênh": {
    "en": "📢 Post the Rules to the Channel",
    "ja": "📢 ルールをチャンネルに投稿する",
    "cn": "📢 将规则发布到频道"
  },
  "URL Hình Ảnh Embed (Banner):": {
    "en": "Embed Image URL (Banner):",
    "ja": "埋め込み画像 URL (バナー):",
    "cn": "嵌入图片 URL（横幅）："
  },
  "ví dụ: ⚡ Cuốc Titan Siêu Cấp": {
    "en": "For example: ⚡ Super Titan Pickaxe",
    "ja": "例: ⚡ スーパータイタンのつるはし",
    "cn": "例如：⚡超级泰坦镐"
  },
  "Dán link ảnh hoặc tải tệp...": {
    "en": "Paste the image link or download the file...",
    "ja": "画像のリンクを貼り付けるか、ファイルをダウンロードしてください...",
    "cn": "粘贴图像链接或下载文件..."
  },
  "Ví dụ: luatchoi, ip, link...": {
    "en": "For example: luatchoi, ip, link...",
    "ja": "例: ルアチョイ、ip、リンク...",
    "cn": "例如：luatchoi、ip、链接..."
  },
  "Cộng thẳng % may mắn khi câu": {
    "en": "Add up the lucky percentage when fishing",
    "ja": "釣りをするときに幸運の割合を合計します",
    "cn": "钓鱼时累加幸运率"
  },
  "-- Chưa chọn kênh ghi log --": {
    "en": "-- Logging channel not selected --",
    "ja": "-- ロギングチャネルが選択されていません --",
    "cn": "-- 未选择记录通道 --"
  },
  "Lối Chơi & Thế Giới Gameplay": {
    "en": "Gameplay & Gameplay World",
    "ja": "ゲームプレイとゲームプレイの世界",
    "cn": "游戏玩法和游戏世界"
  },
  "và lưu vào máy tính của bạn.": {
    "en": "and save to your computer.",
    "ja": "そしてコンピュータに保存します。",
    "cn": "并保存到您的计算机。"
  },
  "2. Thêm vào server Minecraft": {
    "en": "2. Add to Minecraft server",
    "ja": "2. Minecraftサーバーに追加",
    "cn": "2. 添加到我的世界服务器"
  },
  "Đi đến một điểm warp đã tạo.": {
    "en": "Go to a created warp point.",
    "ja": "作成したワープポイントに移動します。",
    "cn": "转到创建的扭曲点。"
  },
  "Giới Thiệu & Cam Kết Bảo Mật": {
    "en": "Introduction & Privacy Commitment",
    "ja": "はじめにとプライバシーへの取り組み",
    "cn": "简介及隐私承诺"
  },
  "lưu trữ mật khẩu Discord, và": {
    "en": "Discord password storage, and",
    "ja": "Discordのパスワードストレージと",
    "cn": "不一致的密码存储，以及"
  },
  "Khám Phá Sakura Bio Profiles": {
    "en": "Explore Sakura Bio Profiles",
    "ja": "さくらのプロフィールを調べる",
    "cn": "探索樱花生物档案"
  },
  "📹 Tải Thường SD (Không Logo)": {
    "en": "📹 Normal SD Download (No Logo)",
    "ja": "📹 通常の SD ダウンロード (ロゴなし)",
    "cn": "📹 普通标清下载（无标志）"
  },
  "Tên hiển thị (Display Name)": {
    "en": "Display Name",
    "ja": "表示名",
    "cn": "显示名称"
  },
  "💡 Thứ tự hiển thị hiện tại:": {
    "en": "💡 Current display order:",
    "ja": "💡 現在の表示順序:",
    "cn": "💡 当前显示顺序："
  },
  "Đang tải dữ liệu tệp tin...": {
    "en": "Loading file data...",
    "ja": "ファイルデータをロード中...",
    "cn": "Loading file data..."
  },
  "🛡️ Chỉ đọc (Safe Read-Only)": {
    "en": "🛡️ Safe Read-Only",
    "ja": "🛡️ 安全な読み取り専用",
    "cn": "🛡️ Safe Read-Only"
  },
  "Chưa thực thi truy vấn nào.": {
    "en": "No queries have been executed yet.",
    "ja": "まだクエリは実行されていません。",
    "cn": "尚未执行任何查询。"
  },
  "🔍 Lọc từ khóa trong bảng...": {
    "en": "🔍 Filter keywords in the table...",
    "ja": "🔍 表内のキーワードをフィルターします...",
    "cn": "🔍 过滤表格中的关键字..."
  },
  "Nhập cụm 2 từ, vd: hoa hồng": {
    "en": "Enter a 2-word phrase, for example: rose",
    "ja": "2 単語のフレーズを入力します。例: ローズ",
    "cn": "输入 2 个词的短语，例如：rose"
  },
  "hoặc Discord Slash Commands": {
    "en": "or Discord Slash Commands",
    "ja": "またはDiscordのスラッシュコマンド",
    "cn": "或不和谐斜线命令"
  },
  "Trạng Thái Các API Tích Hợp": {
    "en": "Status of Integration APIs",
    "ja": "統合 API のステータス",
    "cn": "集成 API 的状态"
  },
  "Không tìm thấy lệnh phù hợp": {
    "en": "No matching command found",
    "ja": "一致するコマンドが見つかりません",
    "cn": "没有找到匹配的命令"
  },
  "Discord User ID (Bắt buộc):": {
    "en": "Discord User ID (Required):",
    "ja": "Discord ユーザー ID (必須):",
    "cn": "Discord 用户 ID（必填）："
  },
  "🏦 Bank (Tiền gửi Ngân hàng)": {
    "en": "🏦 Bank (Bank Deposit)",
    "ja": "🏦 銀行 (銀行預金)",
    "cn": "🏦 银行（银行存款）"
  },
  "🐾 Thú Cưng Đồng Hành (Pets)": {
    "en": "🐾 Companion Pets (Pets)",
    "ja": "🐾 コンパニオンペット (ペット)",
    "cn": "🐾 伴侣宠物（宠物）"
  },
  "Danh Sách Cá Trong Giỏ Đồ (": {
    "en": "List of Fish in the Shopping Cart (",
    "ja": "ショッピングカート内の魚のリスト (",
    "cn": "购物车中的鱼列表 ("
  },
  "🎁 Vật Phẩm Đặc Biệt & Troll": {
    "en": "🎁 Special Items & Trolls",
    "ja": "🎁 特別なアイテムとトロール",
    "cn": "🎁 特殊物品和巨魔"
  },
  "mục tra cứu trong hệ thống.": {
    "en": "lookup item in the system.",
    "ja": "システム内のルックアップ項目。",
    "cn": "系统中查找项目。"
  },
  "🎣 Cần Câu Hiếm Trong Rương:": {
    "en": "🎣 Rare Fishing Rod in Chest:",
    "ja": "🎣 チェスト内のレアな釣り竿:",
    "cn": "🎣 宝箱中的稀有鱼竿："
  },
  "Mã định danh ID (bait_...):": {
    "en": "Identifier ID (bait_...):",
    "ja": "識別子ID (bait_...):",
    "cn": "标识符ID（bait_...）："
  },
  "Tên túi / thùng (kèm icon):": {
    "en": "Name of bag / box (with icon):",
    "ja": "バッグ/ボックスの名前 (アイコン付き):",
    "cn": "袋子/盒子名称（带图标）："
  },
  "💰 STEAL_COIN (Trộm tiền ví)": {
    "en": "💰 STEAL_COIN (Wallet money theft)",
    "ja": "💰 STEAL_COIN (ウォレットマネーの盗難)",
    "cn": "💰 STEAL_COIN（钱包钱被盗）"
  },
  "😱 JUMPSCARE (Hù ma dọa tim)": {
    "en": "😱 JUMPSCARE (Heart-threatening scare)",
    "ja": "😱 JUMPSCARE (心臓を脅かす恐怖)",
    "cn": "😱 JUMPSCARE（威胁心脏的恐慌）"
  },
  "Thời gian hiệu lực còn lại:": {
    "en": "Remaining validity period:",
    "ja": "残りの有効期限:",
    "cn": "剩余有效期："
  },
  "Thời Gian Cưỡng Chế (Phút):": {
    "en": "Enforcement Time (Minutes):",
    "ja": "施行時間 (分):",
    "cn": "执行时间（分钟）："
  },
  "🏛️ Mở Khóa Toàn Bộ Bảo Tàng": {
    "en": "🏛️ Unlock All Museums",
    "ja": "🏛️ すべての博物館のロックを解除する",
    "cn": "🏛️解锁所有博物馆"
  },
  "🔗 Nối Server MC Với Discord": {
    "en": "🔗 Connect MC Server With Discord",
    "ja": "🔗 MCサーバーをDiscordに接続する",
    "cn": "🔗 使用 Discord 连接 MC 服务器"
  },
  "📖 Tra Cứu & Quản Lý Từ Điển": {
    "en": "📖 Look Up & Manage Dictionary",
    "ja": "📖 辞書の検索と管理",
    "cn": "📖 查找和管理词典"
  },
  "🟢 Không Phổ Biến (Uncommon)": {
    "en": "🟢 Uncommon",
    "ja": "🟢 珍しい",
    "cn": "🟢不常见"
  },
  "🟡 Truyền Thuyết (Legendary)": {
    "en": "🟡 Legend",
    "ja": "🟡 伝説",
    "cn": "🟡传奇"
  },
  "Nhập mã kết nối tạo từ lệnh": {
    "en": "Enter the connection code generated from the command",
    "ja": "コマンドから生成された接続コードを入力します。",
    "cn": "输入命令生成的连接代码"
  },
  "Quản Lý Yêu Cầu Vote Top.gg": {
    "en": "Manage Vote Requests Top.gg",
    "ja": "投票リクエストの管理 Top.gg",
    "cn": "管理投票请求 Top.gg"
  },
  "🤖 Hồ Sơ Bot Tại Máy Chủ Này": {
    "en": "🤖 Bot Profile On This Server",
    "ja": "🤖 このサーバー上のボットプロファイル",
    "cn": "🤖 此服务器上的机器人配置文件"
  },
  "Panel ticket và kênh hỗ trợ": {
    "en": "Panel tickets and support channels",
    "ja": "パネルチケットとサポートチャネル",
    "cn": "小组门票和支持渠道"
  },
  "mỗi từ chọn kiểu khớp riêng": {
    "en": "Each word chooses its own matching type",
    "ja": "各単語は独自の一致タイプを選択します",
    "cn": "每个单词选择自己的匹配类型"
  },
  "Quá nhiều emoji trong 1 tin": {
    "en": "Too many emojis in 1 message",
    "ja": "1 つのメッセージ内の絵文字が多すぎます",
    "cn": "1 条消息中的表情符号过多"
  },
  "Gửi lặp lại cùng 1 nội dung": {
    "en": "Repeat sending the same content",
    "ja": "同じ内容を繰り返し送信する",
    "cn": "重复发送相同内容"
  },
  "Chặn ký tự rối (H̶e̶l̶l̶o̶)": {
    "en": "Block tangled characters (H̶e̶l̶l̶o̶)",
    "ja": "絡まった文字をブロック (H̶e̶l̶l̶o̶)",
    "cn": "块纠缠字符 (H̶e̶l̶l̶o̶)"
  },
  "nếu không muốn log nhóm đó.": {
    "en": "If you don't want to log that group.",
    "ja": "そのグループをログに記録したくない場合。",
    "cn": "如果您不想记录该组。"
  },
  "DANH SÁCH MỐC ROLE HIỆN CÓ:": {
    "en": "LIST OF CURRENT ROLE MARKET:",
    "ja": "現在の役割市場のリスト:",
    "cn": "当前角色市场列表："
  },
  "🔔 Role ping khi có Code mới": {
    "en": "🔔 Role ping when there is a new Code",
    "ja": "🔔 新しいコードがあるときにロールを ping する",
    "cn": "🔔 有新代码时角色 ping"
  },
  "🤖 Vai trò cho Bot mới (Bot)": {
    "en": "🤖 Roles for New Bots (Bot)",
    "ja": "🤖 新しいボットの役割 (ボット)",
    "cn": "🤖 新机器人的角色 (Bot)"
  },
  "Chưa có role nào được thêm.": {
    "en": "No roles have been added yet.",
    "ja": "まだ役割が追加されていません。",
    "cn": "尚未添加任何角色。"
  },
  "để lấy mã liên kết 6 ký tự.": {
    "en": "to get the 6-character link code.",
    "ja": "6 文字のリンク コードを取得します。",
    "cn": "获取 6 个字符的链接代码。"
  },
  "Ví dụ: fish_bag_hyper_space": {
    "en": "For example: fish_bag_hyper_space",
    "ja": "例:fish_bag_hyper_space",
    "cn": "例如：fish_bag_hyper_space"
  },
  "ID Discord người sở hữu bot": {
    "en": "The Discord ID of the bot owner",
    "ja": "ボット所有者の Discord ID",
    "cn": "机器人所有者的 Discord ID"
  },
  "🌸 CHÀO MỪNG THÀNH VIÊN MỚI!": {
    "en": "🌸 WELCOME NEW MEMBER!",
    "ja": "🌸 新しいメンバーを歓迎します!",
    "cn": "❤ 欢迎新会员！"
  },
  "Cấu Hình Discord Log & Chat": {
    "en": "Configuring Discord Log & Chat",
    "ja": "Discordのログとチャットを設定する",
    "cn": "配置 Discord 日志和聊天"
  },
  "Độ khó máy chủ (Difficulty)": {
    "en": "Server difficulty (Difficulty)",
    "ja": "サーバーの難易度（難易度）",
    "cn": "服务器难度（难度）"
  },
  "Cho phép bay (Allow Flight)": {
    "en": "Allow Flight",
    "ja": "飛行を許可する",
    "cn": "允许飞行"
  },
  "Danh Sách Máy Chủ Minecraft": {
    "en": "Minecraft Server List",
    "ja": "Minecraftサーバーリスト",
    "cn": "我的世界服务器列表"
  },
  "Thư mục plugins đã sẵn sàng": {
    "en": "The plugins folder is ready",
    "ja": "プラグインフォルダーの準備ができました",
    "cn": "插件文件夹已准备就绪"
  },
  "/pay <người_nhận> <số_tiền>": {
    "en": "/pay <recipient> <amount>",
    "ja": "/pay <受取人> <金額>",
    "cn": "/pay <收款人> <金额>"
  },
  "Trung Tâm Hỗ Trợ & Phản Hồi": {
    "en": "Support & Feedback Center",
    "ja": "サポート&フィードバックセンター",
    "cn": "支持与反馈中心"
  },
  "Hoàn toàn được! Bạn vào mục": {
    "en": "Absolutely! You enter the section",
    "ja": "絶対に！セクションに入ります",
    "cn": "绝对！您进入该部分"
  },
  "Ví dụ: linh#1234 hoặc email": {
    "en": "For example: linh#1234 or email",
    "ja": "例: linh#1234 または電子メール",
    "cn": "例如：linh#1234 或电子邮件"
  },
  "🎬 Tải Video HD (Không Logo)": {
    "en": "🎬 Download HD Video (No Logo)",
    "ja": "🎬 Download HD Video (No Logo)",
    "cn": "🎬 下载高清视频（无徽标）"
  },
  "URL Ảnh bìa (Cover Banner)": {
    "en": "Cover Banner URL",
    "ja": "カバーバナーURL",
    "cn": "封面横幅 URL"
  },
  "Hỗ Trợ & Donate (Tùy chọn)": {
    "en": "Support & Donate (Optional)",
    "ja": "Support & Donate (Optional)",
    "cn": "支持和捐赠（可选）"
  },
  "👁️ Xem Trước Trực Quan Bio": {
    "en": "👁️ Visual Bio Preview",
    "ja": "👁️ Visual Bio Preview",
    "cn": "👁️ 视觉生物预览"
  },
  "Đang tải danh sách bảng...": {
    "en": "Loading table list...",
    "ja": "テーブルリストをロード中...",
    "cn": "正在加载表格列表..."
  },
  "Đang tải danh sách Cogs...": {
    "en": "Loading Cogs list...",
    "ja": "歯車リストを読み込み中...",
    "cn": "正在加载齿轮列表..."
  },
  "(không bắt buộc đăng nhập)": {
    "en": "(no login required)",
    "ja": "(ログインは必要ありません)",
    "cn": "（无需登录）"
  },
  "👥 Người chơi trong phòng (": {
    "en": "👥 Players in the room (",
    "ja": "👥 Players in the room (",
    "cn": "👥 房间里的玩家 ("
  },
  "🔤 Số từ được chọn mỗi lượt": {
    "en": "🔤 Number of words selected each turn",
    "ja": "🔤 Number of words selected each turn",
    "cn": "🔤 每轮选择的单词数量"
  },
  "❓ Câu hỏi thường gặp (FAQ)": {
    "en": "❓ Frequently Asked Questions (FAQ)",
    "ja": "❓ Frequently Asked Questions (FAQ)",
    "cn": "❓ 常见问题（FAQ）"
  },
  "Góc Nhìn Người Dùng Thường": {
    "en": "Normal User Perspective",
    "ja": "通常のユーザーの視点",
    "cn": "普通用户视角"
  },
  "Tài Nguyên Bot (RSS / CPU)": {
    "en": "Bot Resources (RSS / CPU)",
    "ja": "Bot Resources (RSS / CPU)",
    "cn": "机器人资源（RSS / CPU）"
  },
  "🏰 Chọn máy chủ để cấu hình": {
    "en": "🏰 Select server to configure",
    "ja": "🏰 Select server to configure",
    "cn": "🏰 选择要配置的服务器"
  },
  "🌍 Tất Cả Server / Toàn Cục": {
    "en": "🌍 All Servers / Whole Department",
    "ja": "🌍 All Servers / Whole Department",
    "cn": "🌍 所有服务器/整个部门"
  },
  "💠 Xu (Tiền tệ Nạp/Premium)": {
    "en": "💠 Coins (Deposit/Premium Currency)",
    "ja": "💠 Coins (Deposit/Premium Currency)",
    "cn": "💠 硬币（存款/高级货币）"
  },
  "⚙️ Thiết lập chính xác (=)": {
    "en": "⚙️ Correct setup (=)",
    "ja": "⚙️ 正しいセットアップ (=)",
    "cn": "⚙️正确设置(=)"
  },
  "Quy Định & Ghi Chú Kinh Tế": {
    "en": "Economic Regulations & Notes",
    "ja": "経済規制と注意事項",
    "cn": "经济法规及注意事项"
  },
  "Tiền tệ độc quyền cao cấp,": {
    "en": "Premium exclusive currency,",
    "ja": "プレミアム専用通貨、",
    "cn": "优质专属货币，"
  },
  "Tổng Số Thành Tựu Hệ Thống": {
    "en": "Total System Achievements",
    "ja": "システム全体の実績",
    "cn": "系统总体成就"
  },
  "Đang tải danh sách item...": {
    "en": "Loading item list...",
    "ja": "アイテムリストを読み込んでいます...",
    "cn": "正在加载项目列表..."
  },
  "⚖️ Mặc Định (Cân Bằng Gốc)": {
    "en": "⚖️ Default (Original Balanced)",
    "ja": "⚖️ デフォルト (オリジナルバランス)",
    "cn": "⚖️默认（原始平衡）"
  },
  "Tỉ Lệ Rớt Rương Đại Dương:": {
    "en": "Ocean Chest Drop Rate:",
    "ja": "オーシャンチェストのドロップ率:",
    "cn": "海洋宝箱掉落率："
  },
  "Mã định danh ID (rod_...):": {
    "en": "Identifier ID (rod_...):",
    "ja": "識別子ID (rod_...):",
    "cn": "标识符ID（rod_...）："
  },
  "May mắn cộng thêm khi câu:": {
    "en": "Bonus luck when fishing:",
    "ja": "釣り時のボーナス運:",
    "cn": "钓鱼时额外幸运："
  },
  "Mã định danh ID (pet_...):": {
    "en": "ID identifier (pet_...):",
    "ja": "ID識別子(pet_...):",
    "cn": "ID标识符（pet_...）："
  },
  "🐟 STEAL_FISH (Trộm cá quý)": {
    "en": "🐟 STEAL_FISH (Stealing precious fish)",
    "ja": "🐟 STEAL_FISH (貴重な魚を盗む)",
    "cn": "🐟 STEAL_FISH（偷珍贵的鱼）"
  },
  "🎁 FAKE_NITRO (Hộp quà bẫy)": {
    "en": "🎁 FAKE_NITRO (Trap gift box)",
    "ja": "🎁 FAKE_NITRO (トラップギフトボックス)",
    "cn": "🎁 FAKE_NITRO（陷阱礼盒）"
  },
  "👻 GHOST_PING (Tag ma quái)": {
    "en": "👻 GHOST_PING (Ghost Tag)",
    "ja": "👻 GHOST_PING (ゴーストタグ)",
    "cn": "👻 GHOST_PING（幽灵标签）"
  },
  "Sâu Bọ & Dụng Cụ, Phân Bón": {
    "en": "Pests & Tools, Fertilizers",
    "ja": "害虫と道具、肥料",
    "cn": "害虫和工具、肥料"
  },
  "⚡ Đặt Cấp Refine (+0..150)": {
    "en": "⚡ Set Refine Level (+0..150)",
    "ja": "⚡ リファインレベルの設定 (+0..150)",
    "cn": "⚡ 设置精炼级别（+0..150）"
  },
  "⚡ Thao Tác Quản Trị Thợ Mỏ": {
    "en": "⚡ Miner Administration Operations",
    "ja": "⚡ マイナー管理業務",
    "cn": "⚡ 矿工管理运营"
  },
  "Biểu Tượng (Icon / Emoji):": {
    "en": "Icon (Icon / Emoji):",
    "ja": "アイコン (アイコン/絵文字):",
    "cn": "图标（图标/表情符号）："
  },
  "🔤 Quản Lý Minigame Nối Chữ": {
    "en": "🔤 Manage Letter Matching Minigame",
    "ja": "🔤 文字マッチングミニゲームの管理",
    "cn": "🔤 管理字母匹配小游戏"
  },
  "Thêm Quản Trị Viên Web Mới": {
    "en": "Add New Web Admin",
    "ja": "新しい Web 管理者の追加",
    "cn": "添加新的网络管理员"
  },
  "Xem trước theo từng chế độ": {
    "en": "Preview by each mode",
    "ja": "各モードでプレビュー",
    "cn": "各模式预览"
  },
  "💰 Trivia / Ai Là Triệu Phú": {
    "en": "💰 Trivia / Who Wants to Be a Millionaire",
    "ja": "💰 トリビア / 大富豪になりたい人",
    "cn": "💰 琐事 / 谁想成为百万富翁"
  },
  "Bật/tắt lệnh bói bài tarot": {
    "en": "Enable/disable tarot card fortune telling commands",
    "ja": "タロットカード占いコマンドの有効化/無効化",
    "cn": "启用/禁用塔罗牌算命命令"
  },
  "+ Thêm kênh bỏ qua spam...": {
    "en": "+ Add channel to ignore spam...",
    "ja": "+ スパムを無視するチャンネルを追加...",
    "cn": "+ 添加忽略垃圾邮件的频道..."
  },
  "Ngưỡng dấu kết hợp (4-20):": {
    "en": "Combined mark threshold (4-20):",
    "ja": "結合マークしきい値 (4 ～ 20):",
    "cn": "组合分数阈值（4-20）："
  },
  "🚫 Blacklist — Cấm dùng bot": {
    "en": "🚫 Blacklist — Forbidden to use bots",
    "ja": "🚫 ブラックリスト — ボットの使用を禁止します",
    "cn": "🚫 黑名单 — 禁止使用机器人"
  },
  "TempVoice — Kênh thoại tạm": {
    "en": "TempVoice — Temporary voice channel",
    "ja": "TempVoice — 一時的な音声チャネル",
    "cn": "TempVoice — 临时语音通道"
  },
  "-- Theo kênh Confession --": {
    "en": "-- According to Confession channel --",
    "ja": "-- 告白チャンネルによると --",
    "cn": "——据Confession频道报道——"
  },
  "join (ai mời), leave, kick": {
    "en": "join (who invited), leave, kick",
    "ja": "参加する（誰が招待したか）、離れる、キックする",
    "cn": "加入（邀请者）、离开、踢出"
  },
  "gửi tin nhắn khi lên level": {
    "en": "Send messages when leveling up",
    "ja": "レベルアップ時にメッセージを送信する",
    "cn": "升级时发送消息"
  },
  "Màu viền Hex (vd: #5865F2)": {
    "en": "Hex border color (eg: #5865F2)",
    "ja": "16 進数の境界線の色 (例: #5865F2)",
    "cn": "十六进制边框颜色（例如：#5865F2）"
  },
  "Ảnh Banner (URL, tùy chọn)": {
    "en": "Banner image (URL, optional)",
    "ja": "バナー画像（URL、オプション）",
    "cn": "横幅图片（URL，可选）"
  },
  "Điểm Tình Cảm (Affection):": {
    "en": "Affection Score (Affection):",
    "ja": "愛情スコア（愛情）：",
    "cn": "好感度（好感度）："
  },
  "Ví dụ: 1144785664458637394": {
    "en": "For example: 1144785664458637394",
    "ja": "例: 1144785664458637394",
    "cn": "例如：1144785664458637394"
  },
  "Ví dụ: bait_nebula_crystal": {
    "en": "For example: bait_nebula_crystal",
    "ja": "例: Bait_nebula_crystal",
    "cn": "例如：bait_nebula_crystal"
  },
  "🔍 Tìm tên, username, ID...": {
    "en": "🔍 Find name, username, ID...",
    "ja": "🔍 名前、ユーザー名、ID を検索...",
    "cn": "🔍 查找姓名、用户名、ID..."
  },
  "Nhập nội dung thông báo...": {
    "en": "Enter notification content...",
    "ja": "通知内容を入力してください...",
    "cn": "输入通知内容..."
  },
  "Gửi lệnh /restart qua RCON": {
    "en": "Send /restart command via RCON",
    "ja": "RCON経由で/再起動コマンドを送信",
    "cn": "通过RCON发送/重启命令"
  },
  "Cổng Máy Chủ (Server Port)": {
    "en": "Server Port",
    "ja": "サーバーポート",
    "cn": "服务器端口"
  },
  "Kinh Tế, SellGUI & Chợ Đen": {
    "en": "Economics, SellGUI & Black Market",
    "ja": "経済学、SellGUI、ブラックマーケット",
    "cn": "经济学、SellGUI 和黑市"
  },
  "Dữ Liệu Chúng Tôi Thu Thập": {
    "en": "Data We Collect",
    "ja": "当社が収集するデータ",
    "cn": "我们收集的数据"
  },
  "👤 Hồ Sơ Của Bạn (Của Mình)": {
    "en": "👤 Your Profile (Mine)",
    "ja": "👤 あなたのプロフィール (私の)",
    "cn": "👤 你的个人资料（我的）"
  },
  "Quyền Hạn & Sử Dụng Hợp Lệ": {
    "en": "Permissions & Eligible Use",
    "ja": "許可と適格な使用",
    "cn": "权限和合法使用"
  },
  "Link rút gọn vt.tiktok.com": {
    "en": "Shortened link vt.tiktok.com",
    "ja": "短縮リンク vt.tiktok.com",
    "cn": "缩短的链接 vt.tiktok.com"
  },
  "🏷️ Tải Có Logo (Watermark)": {
    "en": "🏷️ Download with Logo (Watermark)",
    "ja": "🏷️ ロゴ（透かし）付きでダウンロード",
    "cn": "🏷️ 带徽标下载（水印）"
  },
  "trên Discord để kết duyên": {
    "en": "on Discord to make love",
    "ja": "Discord で愛を育む",
    "cn": "在 Discord 上做爱"
  },
  "URL Ảnh đại diện (Avatar)": {
    "en": "Avatar URL",
    "ja": "アバターURL",
    "cn": "头像网址"
  },
  "📐 Sắp Xếp Thứ Tự Khối Bio": {
    "en": "📐 Arrange Bio Block Order",
    "ja": "📐 バイオブロックの注文を手配する",
    "cn": "📐 安排生物区块顺序"
  },
  "Vừa màn hình (Fit Screen)": {
    "en": "Fit Screen",
    "ja": "画面に合わせる",
    "cn": "适合屏幕"
  },
  "Nhập văn bản cần xử lý...": {
    "en": "Enter the text to be processed...",
    "ja": "処理するテキストを入力してください...",
    "cn": "输入要处理的文字..."
  },
  "🎨 Cổ Điển (Chuẩn Skribbl)": {
    "en": "🎨 Classic (Skribbl Standard)",
    "ja": "🎨 クラシック (Skribbl スタンダード)",
    "cn": "🎨 经典（Skribbl 标准）"
  },
  "Tự động lưu khi đăng nhập": {
    "en": "Autosave when logged in",
    "ja": "ログイン時に自動保存",
    "cn": "登录时自动保存"
  },
  "Xem danh sách lệnh đầy đủ": {
    "en": "See full command list",
    "ja": "完全なコマンドリストを参照",
    "cn": "查看完整命令列表"
  },
  "👑 Quay Lại Góc Nhìn Admin": {
    "en": "👑 Back to Admin Perspective",
    "ja": "👑 管理者の視点に戻る",
    "cn": "👑 返回管理员视角"
  },
  "💾 Cập Nhật Trạng Thái Bot": {
    "en": "💾 Update Bot Status",
    "ja": "💾 ボットのステータスを更新する",
    "cn": "💾 更新机器人状态"
  },
  "Trạng thái Bot (tích hợp)": {
    "en": "Bot Status (integrated)",
    "ja": "ボットステータス (統合)",
    "cn": "机器人状态（集成）"
  },
  "Không tìm thấy server nào": {
    "en": "No servers found",
    "ja": "サーバーが見つかりませんでした",
    "cn": "未找到服务器"
  },
  "Danh Sách Lệnh Sakura Bot": {
    "en": "Sakura Bot Command List",
    "ja": "さくらボットコマンド一覧",
    "cn": "Sakura 机器人命令列表"
  },
  "Mã ID vật phẩm tùy chỉnh:": {
    "en": "Custom Item ID:",
    "ja": "カスタムアイテムID:",
    "cn": "自定义项目 ID："
  },
  "🟡 Huyền Thoại (Legendary)": {
    "en": "🟡 Legendary",
    "ja": "🟡 伝説の",
    "cn": "🟡传奇"
  },
  "Tỉ lệ xuất hiện (Chance):": {
    "en": "Chance:",
    "ja": "チャンス:",
    "cn": "机会："
  },
  "Đang tải danh sách mồi...": {
    "en": "Loading bait list...",
    "ja": "餌リストを読み込んでいます...",
    "cn": "正在加载诱饵列表..."
  },
  "Đang tải danh sách pet...": {
    "en": "Loading pet list...",
    "ja": "ペットリストを読み込み中...",
    "cn": "正在加载宠物列表..."
  },
  "Đang tải danh sách cần...": {
    "en": "Loading wish list...",
    "ja": "ウィッシュリストを読み込んでいます...",
    "cn": "正在加载愿望清单..."
  },
  "Loại hiệu ứng (Key Lệnh):": {
    "en": "Effect type (Command Key):",
    "ja": "エフェクトタイプ（コマンドキー）：",
    "cn": "效果类型（命令键）："
  },
  "🏷️ RENAME (Đổi biệt danh)": {
    "en": "🏷️ RENAME (Change nickname)",
    "ja": "🏷️ RENAME (ニックネームを変更)",
    "cn": "🏷️ RENAME（更改昵称）"
  },
  "Số lần câu bị nguyền (VD:": {
    "en": "Number of times the sentence is cursed (Example:",
    "ja": "文が呪われた回数（例：",
    "cn": "句子被咒骂的次数（例如："
  },
  "☀️ Nắng Ấm Dịu Êm (Chuẩn)": {
    "en": "☀️ Warm and Soft Sunshine (Standard)",
    "ja": "☀️ 暖かく柔らかな日差し（標準）",
    "cn": "☀️温暖柔和的阳光（标准）"
  },
  "Sản Lượng & Độ Hiếm Quặng": {
    "en": "Ore Production & Rarity",
    "ja": "鉱石の生産量と希少性",
    "cn": "矿石产量和稀有度"
  },
  "Tên Hiển Thị (kèm Emoji):": {
    "en": "Display Name (with Emoji):",
    "ja": "表示名 (絵文字付き):",
    "cn": "显示名称（带表情符号）："
  },
  "Prefix Mặc Định Toàn Cục:": {
    "en": "Global Default Prefix:",
    "ja": "グローバルデフォルトプレフィックス:",
    "cn": "全局默认前缀："
  },
  "AVATAR (ẢNH ĐẠI DIỆN BOT)": {
    "en": "AVATAR (BOT REPRESENTATIVE PHOTO)",
    "ja": "アバター（ボット代表写真）",
    "cn": "阿凡达（机器人代表照片）"
  },
  "📝 Bảng nội dung thông báo": {
    "en": "📝 Notice content table",
    "ja": "📝お知らせ内容表",
    "cn": "📝 通知内容表"
  },
  "Số mention tối đa (2-15):": {
    "en": "Maximum number of mentions (2-15):",
    "ja": "メンションの最大数 (2 ～ 15):",
    "cn": "最大提及次数（2-15）："
  },
  "Số lần lặp tối đa (2-10):": {
    "en": "Maximum number of repetitions (2-10):",
    "ja": "最大繰り返し回数 (2 ～ 10):",
    "cn": "最大重复次数（2-10）："
  },
  "xóa / sửa / xóa hàng loạt": {
    "en": "delete/edit/bulk delete",
    "ja": "削除/編集/一括削除",
    "cn": "删除/编辑/批量删除"
  },
  "Mở Leaderboard toàn cục →": {
    "en": "Open global Leaderboard →",
    "ja": "グローバルリーダーボードを開く →",
    "cn": "打开全球排行榜 →"
  },
  "Kết Nối Máy Chủ Minecraft": {
    "en": "Connect to Minecraft Server",
    "ja": "Minecraft サーバーに接続する",
    "cn": "连接到 Minecraft 服务器"
  },
  "Địa chỉ IP / Host máy chủ": {
    "en": "Server IP/Host address",
    "ja": "サーバーIP/ホストアドレス",
    "cn": "服务器IP/主机地址"
  },
  "URL Icon Góc (Thumbnail):": {
    "en": "Corner Icon URL (Thumbnail):",
    "ja": "コーナーアイコンURL（サムネイル）：",
    "cn": "角图标 URL（缩略图）："
  },
  "Ví dụ: 🦈 Cá Mập Búa Titan": {
    "en": "For example: 🦈 Titan Hammer Shark",
    "ja": "例: 🦈 タイタンハンマーシャーク",
    "cn": "例如：🦈泰坦锤鲨"
  },
  "Nhập mã PIN hoặc mật khẩu": {
    "en": "Enter your PIN or password",
    "ja": "PIN またはパスワードを入力してください",
    "cn": "输入您的 PIN 码或密码"
  },
  "⚡ Xem menu lệnh Âm nhạc →": {
    "en": "⚡ See Music command menu →",
    "ja": "⚡ 音楽コマンドメニューを参照→",
    "cn": "⚡ 参见音乐命令菜单→"
  },
  "🎣 Xem menu câu cá & chợ →": {
    "en": "🎣 See fishing & market menu →",
    "ja": "🎣 フィッシング＆マーケットメニューを見る →",
    "cn": "🎣 查看钓鱼和市场菜单 →"
  },
  "Điều Hành Viên (Operator)": {
    "en": "Operator",
    "ja": "オペレーター",
    "cn": "操作员"
  },
  "Mã Băm SHA-1 (SHA-1 Hash)": {
    "en": "SHA-1 Hash Code (SHA-1 Hash)",
    "ja": "SHA-1 ハッシュ コード (SHA-1 ハッシュ)",
    "cn": "SHA-1 哈希代码（SHA-1 哈希）"
  },
  "Tắt (Không sinh động vật)": {
    "en": "Off (No animals spawn)",
    "ja": "オフ (動物はスポーンしません)",
    "cn": "关闭（没有动物生成）"
  },
  "Tắt (Chặn bay ở Survival)": {
    "en": "Off (Block flying in Survival)",
    "ja": "オフ (サバイバルではブロック飛行)",
    "cn": "关闭（生存模式下阻止飞行）"
  },
  "Đưa file .jar vào thư mục": {
    "en": "Put the .jar file into the directory",
    "ja": ".jar ファイルをディレクトリに置きます",
    "cn": "将.jar文件放入目录中"
  },
  "Ngày 31 tháng 08 năm 2026": {
    "en": "August 31, 2026",
    "ja": "2026年8月31日",
    "cn": "2026 年 8 月 31 日"
  },
  "🚀 Tạo Trang Hồ Sơ Của Bạn": {
    "en": "🚀 Create Your Profile Page",
    "ja": "🚀 プロフィールページを作成する",
    "cn": "🚀 创建您的个人资料页面"
  },
  "🌸 Về Trang Chủ Sakura Bot": {
    "en": "🌸 Back to Sakura Bot Homepage",
    "ja": "🌸 さくらボットのホームページに戻る",
    "cn": "🌟返回樱花机器人主页"
  },
  "Liên hệ (Discord / Email)": {
    "en": "Contact (Discord / Email)",
    "ja": "連絡先（Discord / メール）",
    "cn": "联系方式（Discord/电子邮件）"
  },
  "Hồ Sơ Bot Trên Server Này": {
    "en": "Bot Profile On This Server",
    "ja": "このサーバー上のボット プロファイル",
    "cn": "此服务器上的机器人配置文件"
  },
  "Chấp Thuận Các Điều Khoản": {
    "en": "Acceptance of Terms",
    "ja": "規約への同意",
    "cn": "接受条款"
  },
  "👤 Tài khoản — Sakura Bot": {
    "en": "👤 Account — Sakura Bot",
    "ja": "👤 アカウント — さくらボット",
    "cn": "👤 账户 — Sakura 机器人"
  },
  "Chức danh / Tagline ngắn": {
    "en": "Short title / Tagline",
    "ja": "短いタイトル/キャッチフレーズ",
    "cn": "短标题/标语"
  },
  "Tiểu sử giới thiệu (Bio)": {
    "en": "Introductory biography (Bio)",
    "ja": "略歴 (略歴)",
    "cn": "简介传记（Bio）"
  },
  "📐 Sắp Xếp Vị Trí Các Hộp": {
    "en": "📐 Arrange the Location of Boxes",
    "ja": "📐 ボックスの位置を調整する",
    "cn": "📐 安排盒子的位置"
  },
  "Đang tải cấu trúc cột...": {
    "en": "Loading column structure...",
    "ja": "列構造を読み込んでいます...",
    "cn": "正在加载柱结构..."
  },
  "Chuyển chế độ Sáng / Tối": {
    "en": "Switch Light/Dark mode",
    "ja": "ライト/ダークモードの切り替え",
    "cn": "切换亮/暗模式"
  },
  "🎮 Game tích hợp trên web": {
    "en": "🎮 Game integrated on the web",
    "ja": "🎮 ウェブ上に統合されたゲーム",
    "cn": "🎮 集成在网络上的游戏"
  },
  "👑 Siêu Khó (Grandmaster)": {
    "en": "👑 Super Hard (Grandmaster)",
    "ja": "👑 スーパーハード (グランドマスター)",
    "cn": "👑 超难（宗师）"
  },
  "Các Phòng Hiện Đang Mở (": {
    "en": "Rooms Currently Open (",
    "ja": "現在オープンしている部屋 (",
    "cn": "目前开放的房间 ("
  },
  "⏱️ Thời gian vẽ mỗi lượt": {
    "en": "⏱️ Drawing time per turn",
    "ja": "⏱️ 1ターンあたりの描画時間",
    "cn": "⏱️ 每回合绘图时间"
  },
  "Chọn 1 từ khóa dưới đây:": {
    "en": "Choose 1 keyword below:",
    "ja": "以下からキーワードを 1 つ選択してください:",
    "cn": "选择以下 1 个关键字："
  },
  ", chọn server, cấp quyền": {
    "en": ", select server, grant permissions",
    "ja": "、サーバーを選択し、権限を付与します",
    "cn": "、选择服务器、授予权限"
  },
  "Bạn đang xem giao diện ở": {
    "en": "You are viewing the interface here",
    "ja": "ここでインターフェースを表示しています",
    "cn": "您正在此处查看界面"
  },
  "Máy Chủ Âm Nhạc Lavalink": {
    "en": "Lavalink Music Server",
    "ja": "Lavalink ミュージック サーバー",
    "cn": "Lavalink 音乐服务器"
  },
  "Kênh Thoại Voice Clients": {
    "en": "Voice Channel Voice Clients",
    "ja": "音声チャネル音声クライアント",
    "cn": "语音通道语音客户端"
  },
  "🐟 Tiêu Chuẩn (1.5 - 6kg)": {
    "en": "🐟 Standard (1.5 - 6kg)",
    "ja": "🐟 標準 (1.5 - 6kg)",
    "cn": "🐟 标准（1.5 - 6kg）"
  },
  "Bể Thủy Cung Trưng Bày (": {
    "en": "Display Aquarium (",
    "ja": "展示水族館（",
    "cn": "展示水族箱 ("
  },
  "Mồi Thường (bait_normal)": {
    "en": "Bait_normal (bait_normal)",
    "ja": "ベイト_ノーマル (ベイト_ノーマル)",
    "cn": "诱饵正常（诱饵正常）"
  },
  "🎉 Phát Hành Giftcode Mới": {
    "en": "🎉 New Giftcode Released",
    "ja": "🎉 新しいギフトコードがリリースされました",
    "cn": "🎉 新礼品码发布"
  },
  "🎁 Rơi từ Rương / Sự kiện": {
    "en": "🎁 Dropped from Chests / Events",
    "ja": "🎁 宝箱/イベントからドロップ",
    "cn": "🎁 从宝箱/活动中掉落"
  },
  "✨ Tạo Rương Mới Vào Game": {
    "en": "✨ Create a New Chest in the Game",
    "ja": "✨ ゲーム内に新しいチェストを作成します",
    "cn": "✨ 在游戏中创建新宝箱"
  },
  "💎 Rương Hải Tặc Atlantis": {
    "en": "💎 Atlantis Pirate Chest",
    "ja": "💎 アトランティス海賊チェスト",
    "cn": "💎 亚特兰蒂斯海盗宝箱"
  },
  "Hiển thị trong Bách Khoa": {
    "en": "Shown in Encyclopedia",
    "ja": "百科事典に掲載",
    "cn": "出现在百科全书中"
  },
  "💾 Lưu Tỉ Lệ Vào Hệ Thống": {
    "en": "💾 Save the Rate to the System",
    "ja": "💾 レートをシステムに保存",
    "cn": "💾 将费率保存到系统"
  },
  "🍀 May Mắn x2 (Tất Cả x2)": {
    "en": "🍀 Lucky x2 (All x2)",
    "ja": "🍀 ラッキー x2 (すべて x2)",
    "cn": "🍀 幸运x2（全部x2）"
  },
  "Tạo Túi / Thùng Chứa Mới": {
    "en": "Create New Bag/Container",
    "ja": "新しいバッグ/コンテナを作成する",
    "cn": "创建新袋子/容器"
  },
  "Tên Thú Cưng (kèm icon):": {
    "en": "Pet Name (with icon):",
    "ja": "ペットの名前 (アイコン付き):",
    "cn": "宠物名称（带图标）："
  },
  "Tên vật phẩm (kèm icon):": {
    "en": "Item name (with icon):",
    "ja": "項目名（アイコン付き）：",
    "cn": "项目名称（带图标）："
  },
  "🔇 MUTE (Cấm chat server)": {
    "en": "🔇 MUTE (Ban chat server)",
    "ja": "🔇 MUTE (チャットサーバーの禁止)",
    "cn": "🔇 静音（禁止聊天服务器）"
  },
  "Thông báo troll tự soạn.": {
    "en": "Self-composed troll notification.",
    "ja": "自作荒らし通知。",
    "cn": "自创的巨魔通知。"
  },
  "Tặng / Thu Hồi Hạt Giống": {
    "en": "Donate / Take Back Seeds",
    "ja": "種子の寄付・持ち帰り",
    "cn": "捐赠/收回种子"
  },
  "🦪 Ngọc Trai Đen Huyền Bí": {
    "en": "🦪 Mysterious Black Pearl",
    "ja": "🦪 ミステリアスブラックパール",
    "cn": "🦪神秘黑珍珠"
  },
  "Chọn Mùa Muốn Thiết Lập:": {
    "en": "Select the Season You Want to Set Up:",
    "ja": "設定したいシーズンを選択してください:",
    "cn": "选择您要设置的季节："
  },
  "— Không chọn kênh chat —": {
    "en": "— Do not select chat channel —",
    "ja": "— チャットチャンネルを選択しないでください —",
    "cn": "— 不选择聊天频道 —"
  },
  "🌾 Nông Trại & Đồng Ruộng": {
    "en": "🌾 Farms & Fields",
    "ja": "🌾 農場と畑",
    "cn": "🌾 农场和田野"
  },
  "⛏️ Cuốc Đào Mỏ (Pickaxe)": {
    "en": "⛏️ Pickaxe",
    "ja": "⛏️つるはし",
    "cn": "⛏️ 镐"
  },
  "Kênh chơi XO / TicTacToe": {
    "en": "XO / TicTacToe playing channel",
    "ja": "XO / TicTacToe プレイチャンネル",
    "cn": "XO / TicTacToe 游戏频道"
  },
  "Cửa sổ spam (giây) 1-120": {
    "en": "Spam window (seconds) 1-120",
    "ja": "スパムウィンドウ (秒) 1 ～ 120",
    "cn": "垃圾邮件窗口（秒）1-120"
  },
  "(Có thể chọn nhiều kênh)": {
    "en": "(Multiple channels can be selected)",
    "ja": "(複数チャンネル選択可能)",
    "cn": "（可以选择多个通道）"
  },
  "— Không đặt kênh riêng —": {
    "en": "— Do not set private channels —",
    "ja": "— プライベートチャンネルを設定しない —",
    "cn": "— 请勿设置私人频道 —"
  },
  "💾 Lưu Cài Đặt Hoyo Codes": {
    "en": "💾 Save Settings Hoyo Codes",
    "ja": "💾 設定を保存 Hoyo コード",
    "cn": "💾 保存设置 Hoyo 代码"
  },
  "Kênh giữ chuỗi điểm danh": {
    "en": "The channel keeps the attendance sequence",
    "ja": "チャンネルは出席順序を維持します",
    "cn": "通道保持考勤顺序"
  },
  "— Chọn Role thành viên —": {
    "en": "— Select Member Role —",
    "ja": "— メンバーの役割を選択 —",
    "cn": "— 选择会员角色 —"
  },
  "💾 Lưu Cấu Hình Minecraft": {
    "en": "💾 Save Minecraft Configuration",
    "ja": "💾 Minecraft の設定を保存する",
    "cn": "💾 保存 Minecraft 配置"
  },
  "🔍 Tìm server theo tên...": {
    "en": "🔍 Search server by name...",
    "ja": "🔍 サーバーを名前で検索...",
    "cn": "🔍 按名称搜索服务器..."
  },
  "Ví dụ: pet_frost_penguin": {
    "en": "For example: pet_frost_penguin",
    "ja": "例: pet_frost_penguin",
    "cn": "例如：pet_frost_penguin"
  },
  "vd: 🥭 Hạt Giống Xoài Cát": {
    "en": "eg: 🥭 Cat Mango Seeds",
    "ja": "例: 🥭 キャットマンゴーの種",
    "cn": "例如：🥭猫芒果种子"
  },
  "🚀 CẢM ƠN SERVER BOOSTER!": {
    "en": "🚀 THANK YOU SERVER BOOSTER!",
    "ja": "🚀 サーバーブースターに感謝します!",
    "cn": "🚀 谢谢服务器助推器！"
  },
  "Trang Facebook Cộng đồng": {
    "en": "Community Facebook page",
    "ja": "コミュニティ Facebook ページ",
    "cn": "社区脸书页面"
  },
  "Danh Sách Banned Players": {
    "en": "List of Banned Players",
    "ja": "禁止されたプレイヤーのリスト",
    "cn": "被封禁玩家名单"
  },
  "Thời gian chạy (Uptime):": {
    "en": "Uptime:",
    "ja": "稼働時間:",
    "cn": "正常运行时间："
  },
  "Cấp Quyền Người Dùng Mới": {
    "en": "New User Authorization",
    "ja": "新規ユーザーの認証",
    "cn": "新用户授权"
  },
  "Tắt (Ai cũng có thể vào)": {
    "en": "Off (Anyone can enter)",
    "ja": "オフ（誰でも入場可能）",
    "cn": "关闭（任何人都可以进入）"
  },
  "Bật (Cho phép đánh nhau)": {
    "en": "On (Allow fighting)",
    "ja": "オン（戦闘許可）",
    "cn": "开（允许战斗）"
  },
  "Hiệu Năng & Kết Nối RCON": {
    "en": "RCON Performance & Connectivity",
    "ja": "RCON のパフォーマンスと接続性",
    "cn": "RCON 性能和连接"
  },
  "Anti-XRay & Bảo Vệ Rương": {
    "en": "Anti-XRay & Chest Protection",
    "ja": "抗X線および胸部保護",
    "cn": "防X射线和胸部保护"
  },
  "Hệ thống kỹ năng nội tại": {
    "en": "Internal skill system",
    "ja": "社内スキル制度",
    "cn": "内部技能系统"
  },
  "Chép file plugin vào đây": {
    "en": "Copy the plugin file here",
    "ja": "ここにプラグインファイルをコピーします",
    "cn": "将插件文件复制到这里"
  },
  "Mục Đích Sử Dụng Dữ Liệu": {
    "en": "Purpose of Data Use",
    "ja": "データの利用目的",
    "cn": "数据使用目的"
  },
  "Xem Điều khoản Dịch vụ →": {
    "en": "See Terms of Service →",
    "ja": "利用規約を参照→",
    "cn": "请参阅服务条款 →"
  },
  "📝 Gửi Phản Hồi & Báo Lỗi": {
    "en": "📝 Send Feedback & Report Errors",
    "ja": "📝 フィードバックを送信してエラーを報告する",
    "cn": "📝 发送反馈并报告错误"
  },
  "Xem Chính sách Bảo mật →": {
    "en": "See Privacy Policy →",
    "ja": "プライバシーポリシーを参照→",
    "cn": "请参阅隐私政策 →"
  },
  "📥 TÙY CHỌN TẢI ALBUM ẢNH": {
    "en": "📥 OPTION TO DOWNLOAD PHOTO ALBUM",
    "ja": "📥 写真アルバムをダウンロードするオプション",
    "cn": "📥 下载相册的选项"
  },
  "📦 Tải Toàn Bộ Ảnh (.ZIP)": {
    "en": "📦 Download All Photos (.ZIP)",
    "ja": "📦 すべての写真をダウンロード (.ZIP)",
    "cn": "📦 下载所有照片 (.ZIP)"
  },
  "▶️ Gán link để xem video": {
    "en": "▶️ Assign link to watch video",
    "ja": "▶️ ビデオを視聴するためのリンクを割り当てます",
    "cn": "▶️分配观看视频的链接"
  },
  "🏆 Thành Tựu & Danh Hiệu": {
    "en": "🏆 Achievements & Titles",
    "ja": "🏆 実績と称号",
    "cn": "🏆 成就和头衔"
  },
  "🏷️ Danh Hiệu Đã Mở Khóa": {
    "en": "🏷️ Title Unlocked",
    "ja": "🏷️ タイトルのロックが解除されました",
    "cn": "🏷️ 标题已解锁"
  },
  "⚪ Chưa kiểm tra cú pháp": {
    "en": "⚪ Haven't checked the syntax",
    "ja": "⚪ 構文をチェックしていない",
    "cn": "⚪ 尚未检查语法"
  },
  "Xem trước toàn màn hình": {
    "en": "Full screen preview",
    "ja": "全画面プレビュー",
    "cn": "全屏预览"
  },
  "🌐 Mời Bạn (Online Room)": {
    "en": "🌐 Invite Friends (Online Room)",
    "ja": "🌐 友達を招待（オンラインルーム）",
    "cn": "🌐 邀请好友（在线房间）"
  },
  "🌐 Song ngữ (Việt - Anh)": {
    "en": "🌐 Bilingual (Vietnamese - English)",
    "ja": "🌐 バイリンガル (ベトナム語 - 英語)",
    "cn": "🌐 双语（越南语 - 英语）"
  },
  "80 Giây (Chuẩn Skribbl)": {
    "en": "80 Seconds (Skribbl Standard)",
    "ja": "80 秒 (Skribbl 標準)",
    "cn": "80 秒（Skribbl 标准）"
  },
  "🔄 Số vòng chơi (Rounds)": {
    "en": "🔄 Number of rounds (Rounds)",
    "ja": "🔄ラウンド数(Rounds)",
    "cn": "🔄 回合数（Rounds）"
  },
  "🎯 Bản 3×3 (Nối 3 Thắng)": {
    "en": "🎯 3×3 version (Connect 3 Wins)",
    "ja": "🎯 3×3 バージョン (3 つの勝利を接続)",
    "cn": "🎯 3×3 版本（连线 3 胜）"
  },
  "🏆 Bảng Xếp Hạng Caro XO": {
    "en": "🏆 Caro XO Rankings",
    "ja": "🏆カロ XO ランキング",
    "cn": "🏆 卡罗 XO 排名"
  },
  "Đổi ngôn ngữ per-server": {
    "en": "Change per-server language",
    "ja": "サーバーごとの言語を変更する",
    "cn": "更改每台服务器的语言"
  },
  "Tạo panel ticket hỗ trợ": {
    "en": "Create a support ticket panel",
    "ja": "サポートチケットパネルを作成する",
    "cn": "创建支持票面板"
  },
  "🔴 Không Làm Phiền (DND)": {
    "en": "🔴 Do Not Disturb (DND)",
    "ja": "🔴 邪魔しないでください (DND)",
    "cn": "🔴请勿打扰（DND）"
  },
  "⚪ Tàng Hình (Invisible)": {
    "en": "⚪ Invisible (Invisible)",
    "ja": "⚪ インビジブル（不可視）",
    "cn": "⚪ 隐形（隐形）"
  },
  "Cogs / Modules đang nạp": {
    "en": "Cogs / Modules are loading",
    "ja": "コグ/モジュールがロード中です",
    "cn": "齿轮/模块正在加载"
  },
  "Đầy đủ các lệnh tiền tố": {
    "en": "Full range of prefix commands",
    "ja": "あらゆる種類の接頭辞コマンド",
    "cn": "全系列前缀命令"
  },
  "Người Chơi Tham Gia Săn": {
    "en": "Players Participate in Hunting",
    "ja": "プレイヤーは狩猟に参加します",
    "cn": "玩家参与狩猎"
  },
  "🐋 Khổng Lồ (25 - 150kg)": {
    "en": "🐋 Giant (25 - 150kg)",
    "ja": "🐋 巨人 (25 - 150kg)",
    "cn": "🐋 巨型（25 - 150 公斤）"
  },
  "🐉 Thần Thoại (>= 150kg)": {
    "en": "🐉 Mythical (>= 150kg)",
    "ja": "🐉 神話級 (>= 150kg)",
    "cn": "🐉 神话（>= 150kg）"
  },
  "💾 Lưu Số Lượng Vật Phẩm": {
    "en": "💾 Save Item Quantity",
    "ja": "💾 アイテム数量を保存",
    "cn": "💾 保存商品数量"
  },
  "Trọng Lượng & Chiều Dài": {
    "en": "Weight & Length",
    "ja": "重量と長さ",
    "cn": "重量和长度"
  },
  "cho toàn bộ người chơi!": {
    "en": "for all players!",
    "ja": "すべてのプレイヤーのために！",
    "cn": "对于所有玩家！"
  },
  "Đính Kèm Nhiều Vật Phẩm": {
    "en": "Attach Multiple Items",
    "ja": "複数のアイテムを添付する",
    "cn": "附加多个项目"
  },
  "Danh mục vật phẩm tặng:": {
    "en": "List of gift items:",
    "ja": "ギフトアイテム一覧：",
    "cn": "礼品清单："
  },
  "🏷️ Nhập Mã ID Tùy Chỉnh": {
    "en": "🏷️ Enter Custom ID Code",
    "ja": "🏷️カスタムIDコードを入力してください",
    "cn": "🏷️ 输入自定义 ID 代码"
  },
  "Trạng Thái & Nguồn Kiếm": {
    "en": "Sword Status & Source",
    "ja": "剣のステータスとソース",
    "cn": "剑的地位与来源"
  },
  "Giá bán cơ bản (Coins):": {
    "en": "Basic selling price (Coins):",
    "ja": "基本販売価格（コイン）：",
    "cn": "基本售价（币）："
  },
  "🐾 Thú Cưng Trong Rương:": {
    "en": "🐾 Pets in the Chest:",
    "ja": "🐾 チェストの中のペット:",
    "cn": "🐾 箱子里的宠物："
  },
  "Tên cần câu (kèm icon):": {
    "en": "Fishing rod name (with icon):",
    "ja": "釣り竿名（アイコン付き）：",
    "cn": "鱼竿名称（带图标）："
  },
  "➕ Thêm Cần Vào Hệ Thống": {
    "en": "➕ Add Need to System",
    "ja": "➕ システムにニーズを追加",
    "cn": "➕ 向系统添加需求"
  },
  "Tên mồi câu (kèm icon):": {
    "en": "Bait name (with icon):",
    "ja": "餌名 (アイコン付き):",
    "cn": "诱饵名称（带图标）："
  },
  "➕ Thêm Mồi Vào Hệ Thống": {
    "en": "➕ Add Bait to the System",
    "ja": "➕ システムに餌を追加します",
    "cn": "➕ 将诱饵添加到系统中"
  },
  "➕ Thêm Túi Vào Hệ Thống": {
    "en": "➕ Add Bags to the System",
    "ja": "➕ システムにバッグを追加する",
    "cn": "➕ 将行李添加到系统中"
  },
  "🐸 FROG (Biến thành Ếch)": {
    "en": "🐸 FROG (Turn into a Frog)",
    "ja": "🐸 FROG (カエルに変身)",
    "cn": "🐸 青蛙（变成青蛙）"
  },
  "Nội dung tin nhắn tùy ý": {
    "en": "Message content is optional",
    "ja": "メッセージの内容は任意です",
    "cn": "留言内容可选"
  },
  "🌦️ Mùa Màng & Thời Tiết": {
    "en": "🌦️ Crops & Weather",
    "ja": "🌦️ 作物と天気",
    "cn": "🌦️ 农作物和天气"
  },
  "📖 Bách Khoa Nông Nghiệp": {
    "en": "📖 Agricultural Encyclopedia",
    "ja": "📖 農業百科事典",
    "cn": "📖农业百科全书"
  },
  "✨ Tạo Nông Sản Đột Biến": {
    "en": "✨ Create Mutant Agricultural Products",
    "ja": "✨ 突然変異した農産物を作成する",
    "cn": "✨ 创造突变农产品"
  },
  "✨ Dòng Enchant: Chưa có": {
    "en": "✨ Enchant line: Not yet available",
    "ja": "✨ エンチャントライン: まだ利用できません",
    "cn": "✨ 附魔线：尚未推出"
  },
  "⭐ Đặt Thăng Sao (0..20)": {
    "en": "⭐ Set Star Promotion (0..20)",
    "ja": "⭐ スタープロモーションを設定 (0..20)",
    "cn": "⭐ 设置星级促销 (0..20)"
  },
  "🧪 Hồi Phục 100% Thể Lực": {
    "en": "🧪 100% Physical Recovery",
    "ja": "🧪 100% 体力回復",
    "cn": "🧪体力恢复100%"
  },
  "— Không chọn kênh log —": {
    "en": "— Do not select log channel —",
    "ja": "— ログチャネルを選択しないでください —",
    "cn": "— 不选择日志通道 —"
  },
  "Tên Thành Tựu Hiển Thị:": {
    "en": "Achievement Name Displayed:",
    "ja": "表示される実績名:",
    "cn": "显示的成就名称："
  },
  "🏆 Bảng Xếp Hạng Nối Chữ": {
    "en": "🏆 Word Matching Chart",
    "ja": "🏆単語一致チャート",
    "cn": "🏆 单词匹配表"
  },
  "🌱 Hạt Giống & Cây Trồng": {
    "en": "🌱 Seeds & Plants",
    "ja": "🌱 種子と植物",
    "cn": "🌱 种子和植物"
  },
  "🎯 Cấu hình Role Request": {
    "en": "🎯 Configure Role Request",
    "ja": "🎯 ロールリクエストを構成する",
    "cn": "🎯 配置角色请求"
  },
  "Kênh duyệt yêu cầu role": {
    "en": "The channel approves the role request",
    "ja": "チャネルがロールリクエストを承認します",
    "cn": "频道批准角色请求"
  },
  "Ảnh góc Thumbnail (URL)": {
    "en": "Thumbnail corner photo (URL)",
    "ja": "サムネイルコーナー写真（URL）",
    "cn": "缩略图角落照片（URL）"
  },
  "💾 Lưu cấu hình MiniGame": {
    "en": "💾 Save MiniGame configuration",
    "ja": "💾 ミニゲーム設定を保存する",
    "cn": "💾 保存小游戏配置"
  },
  "+ Thêm kênh miễn trừ...": {
    "en": "+ Add exemption channel...",
    "ja": "+ 除外チャネルを追加...",
    "cn": "+ 添加豁免通道..."
  },
  ": biểu thức chính quy →": {
    "en": ":regular expression →",
    "ja": ":正規表現 →",
    "cn": ":正则表达式 →"
  },
  "Số emoji tối đa (3-30):": {
    "en": "Maximum number of emojis (3-30):",
    "ja": "絵文字の最大数 (3 ～ 30):",
    "cn": "表情符号最大数量（3-30）："
  },
  "tự tạo kênh thoại riêng": {
    "en": "Create your own voice channel",
    "ja": "独自の音声チャンネルを作成する",
    "cn": "创建您自己的语音频道"
  },
  "Cho phép gửi confession": {
    "en": "Allow sending confessions",
    "ja": "自白の送信を許可する",
    "cn": "允许发送供词"
  },
  "Kênh nhật ký kiểm duyệt": {
    "en": "Censorship log channel",
    "ja": "検閲ログチャンネル",
    "cn": "审查日志频道"
  },
  "— Chọn kênh muốn thêm —": {
    "en": "— Select the channel you want to add —",
    "ja": "— 追加したいチャンネルを選択します —",
    "cn": "— 选择您要添加的频道 —"
  },
  "🔘 Nút bấm (Button View)": {
    "en": "🔘 Button View",
    "ja": "🔘 ボタンビュー",
    "cn": "🔘 按钮视图"
  },
  "— Tắt hệ thống Streak —": {
    "en": "— Turn off the Streak system —",
    "ja": "— Streak システムをオフにする —",
    "cn": "— 关闭Streak系统—"
  },
  "⚡ Liên Kết RCON & Query": {
    "en": "⚡ RCON Link & Query",
    "ja": "⚡ RCON リンクとクエリ",
    "cn": "⚡ RCON 链接与查询"
  },
  "— Chưa chọn kênh chat —": {
    "en": "— Chat channel not selected —",
    "ja": "— チャットチャネルが選択されていません —",
    "cn": "— 未选择聊天频道 —"
  },
  "🧪 Kiểm Tra Kết Nối Live": {
    "en": "🧪 Check Live Connection",
    "ja": "🧪 ライブ接続を確認する",
    "cn": "🧪 检查实时连接"
  },
  "🎉 Khởi Tạo Giveaway Mới": {
    "en": "🎉 Start a New Giveaway",
    "ja": "🎉 新しいプレゼントを開始する",
    "cn": "🎉 开始新的赠品"
  },
  "Ngày Cưới (YYYY-MM-DD):": {
    "en": "Wedding Date (YYYY-MM-DD):",
    "ja": "結婚式の日付 (YYYY-MM-DD):",
    "cn": "结婚日期（年-月-日）："
  },
  "Tìm theo ID hoặc Tên...": {
    "en": "Search by ID or Name...",
    "ja": "IDまたは名前で検索...",
    "cn": "按 ID 或名称搜索..."
  },
  "Số MC Coin muốn nhận...": {
    "en": "Number of MC Coins you want to receive...",
    "ja": "受け取りたいMCコインの数...",
    "cn": "您想收到的MC币数量..."
  },
  "🔍 Tìm kiếm thành tựu...": {
    "en": "🔍 Looking for achievements...",
    "ja": "🔍 実績を求めて...",
    "cn": "🔍寻找成就..."
  },
  "https://... url ảnh lớn": {
    "en": "https://... large image url",
    "ja": "https://...大きな画像のURL",
    "cn": "https://...大图网址"
  },
  "🤖 Mời Sakura vào Server": {
    "en": "🤖 Invite Sakura to the Server",
    "ja": "🤖 さくらをサーバーに招待する",
    "cn": "🤖 邀请小樱加入服务器"
  },
  "Kênh YouTube Sakura Bot": {
    "en": "Sakura Bot YouTube channel",
    "ja": "さくらボットのYouTubeチャンネル",
    "cn": "Sakura Bot YouTube 频道"
  },
  "Gửi lệnh /stop qua RCON": {
    "en": "Send /stop command via RCON",
    "ja": "RCON経由で/停止コマンドを送信",
    "cn": "通过 RCON 发送/停止命令"
  },
  "Tên hiển thị / Ghi chú:": {
    "en": "Display Name / Notes:",
    "ja": "表示名/メモ:",
    "cn": "显示名称/注释："
  },
  "Đồng Bộ Coins & Discord": {
    "en": "Sync Coins & Discord",
    "ja": "コインとディスコードを同期する",
    "cn": "同步硬币和不和谐"
  },
  "Đặt vào thư mục plugins": {
    "en": "Place in plugins folder",
    "ja": "プラグインフォルダーに置きます",
    "cn": "放入插件文件夹"
  },
  "Máy chủ hỗ trợ Discord:": {
    "en": "Discord supported servers:",
    "ja": "Discord がサポートするサーバー:",
    "cn": "Discord 支持的服务器："
  },
  "Kênh GitHub chính thức:": {
    "en": "Official GitHub channel:",
    "ja": "公式 GitHub チャンネル:",
    "cn": "官方GitHub频道："
  },
  "Handle / Tag định danh": {
    "en": "Handle / Identification tag",
    "ja": "ハンドル/識別タグ",
    "cn": "手柄/识别标签"
  },
  "Chế độ Máy tính (100%)": {
    "en": "Computer Mode (100%)",
    "ja": "コンピュータモード (100%)",
    "cn": "电脑模式（100%）"
  },
  "Xuất dữ liệu dạng JSON": {
    "en": "Export data as JSON",
    "ja": "データをJSONとしてエクスポート",
    "cn": "将数据导出为 JSON"
  },
  "Cần đăng nhập để xem —": {
    "en": "Need to log in to view —",
    "ja": "閲覧するにはログインが必要です —",
    "cn": "需要登录才能查看——"
  },
  "Chuyển chế độ sáng/tối": {
    "en": "Switch light/dark mode",
    "ja": "ライト/ダークモードを切り替える",
    "cn": "切换亮/暗模式"
  },
  "⚔️ Trung Bình (Kỳ Thủ)": {
    "en": "⚔️ Average (Player)",
    "ja": "⚔️ 平均 (プレイヤー)",
    "cn": "⚔️ 平均（玩家）"
  },
  "⚡ AI đang tính toán...": {
    "en": "⚡ AI is calculating...",
    "ja": "⚡ AIが計算中です...",
    "cn": "⚡ AI正在计算..."
  },
  "🏆 Bảng Xếp Hạng Cờ Vua": {
    "en": "🏆 Chess Rankings",
    "ja": "🏆チェスランキング",
    "cn": "🏆 国际象棋排名"
  },
  "▶ VÀO PHÒNG CHƠI CHUNG": {
    "en": "▶ ENTER THE COMMON PLAYROOM",
    "ja": "▶ 共通プレイルームに入る",
    "cn": "▶ 进入公共游戏室"
  },
  "👥 Số người chơi tối đa": {
    "en": "👥 Maximum number of players",
    "ja": "👥 最大プレイヤー数",
    "cn": "👥 最大玩家数量"
  },
  "Không gợi ý (Hardcore)": {
    "en": "Not recommended (Hardcore)",
    "ja": "推奨しません（ハードコア）",
    "cn": "不推荐（硬核）"
  },
  "🖌️ Chuẩn bị bảng vẽ...": {
    "en": "🖌️ Prepare the drawing board...",
    "ja": "🖌️ 製図板を準備してください...",
    "cn": "🖌️准备画板..."
  },
  "🔗 Nối Từ — Sakura Game": {
    "en": "🔗 Word Matching — Sakura Game",
    "ja": "🔗 単語マッチング — さくらゲーム",
    "cn": "🔗 单词匹配 — 樱花游戏"
  },
  "Môi Trường Python & OS": {
    "en": "Python & OS Environment",
    "ja": "PythonとOS環境",
    "cn": "Python & 操作系统环境"
  },
  "⛏️ Đào Khoáng & Hầm Mỏ": {
    "en": "⛏️ Mining & Mining",
    "ja": "⛏️ 採掘と採掘",
    "cn": "⛏️ 采矿与采矿"
  },
  "Cường hóa (+0 - +300):": {
    "en": "Enhance (+0 - +300):",
    "ja": "エンハンス (+0 ～ +300):",
    "cn": "增强（+0 - +300）："
  },
  "🎣 Cấp Cần Câu Cho User": {
    "en": "🎣 Providing Fishing Rods to Users",
    "ja": "🎣 ユーザーへの釣り竿の提供",
    "cn": "🎣 为用户提供钓鱼竿"
  },
  "🔮 Vật phẩm ẩn (Secret)": {
    "en": "🔮 Hidden items (Secret)",
    "ja": "🔮 隠しアイテム（シークレット）",
    "cn": "🔮 隐藏物品（秘密）"
  },
  "Thiết Kế Rương Báu Mới": {
    "en": "New Treasure Chest Design",
    "ja": "新しい宝箱のデザイン",
    "cn": "新宝箱设计"
  },
  "Tỉ Lệ Rơi Khi Câu (%):": {
    "en": "Fishing Drop Rate (%):",
    "ja": "釣りドロップ率 (%):",
    "cn": "钓鱼掉落率（%）："
  },
  "🪱 Mồi Câu Trong Rương:": {
    "en": "🪱 Fishing Lures in the Chest:",
    "ja": "🪱 チェスト内の釣りルアー:",
    "cn": "🪱 箱子里的鱼饵："
  },
  "Live Preview Rương Báu": {
    "en": "Live Preview of Treasure Chests",
    "ja": "宝箱のライブプレビュー",
    "cn": "宝箱实时预览"
  },
  "Bể Thủy Cung Đại Dương": {
    "en": "Ocean Aquarium Tank",
    "ja": "海洋水族館の水槽",
    "cn": "海洋水族馆"
  },
  "Tỉ Lệ Cá Đột Biến Gen:": {
    "en": "Rate of Genetically Mutated Fish:",
    "ja": "遺伝子変異した魚の割合:",
    "cn": "鱼类基因突变率："
  },
  "🛠️ Nông Cụ & Lồng Kính": {
    "en": "🛠️ Farm Tools & Glass Cages",
    "ja": "🛠️ 農具とガラスケージ",
    "cn": "🛠️农具和玻璃笼"
  },
  "⏳ Có hạn sử dụng (HSD)": {
    "en": "⏳ Expiry date (HSD)",
    "ja": "⏳ 有効期限 (HSD)",
    "cn": "⏳ 有效期 (HSD)"
  },
  "Tạo Thú Cưng (Pet) Mới": {
    "en": "Create a New Pet",
    "ja": "新しいペットを作成する",
    "cn": "创建新宠物"
  },
  "Số phút đóng băng (VD:": {
    "en": "Number of freezing minutes (eg:",
    "ja": "フリーズする分数 (例:",
    "cn": "冻结分钟数（例如："
  },
  "Thời hạn hiệu lực (VD:": {
    "en": "Validity period (eg:",
    "ja": "有効期間 (例:",
    "cn": "有效期（例如："
  },
  "Tổng Quỹ Chung Cặp Đôi": {
    "en": "Joint Couple Fund",
    "ja": "夫婦共同基金",
    "cn": "夫妻联名基金"
  },
  "Tặng / Thu Hồi Hoa Màu": {
    "en": "Donate / Take Back Crops",
    "ja": "作物を寄付/引き取ります",
    "cn": "捐赠/收回农作物"
  },
  "Tặng Nông Sản Đột Biến": {
    "en": "Donate Mutant Agricultural Products",
    "ja": "変異農産物を寄付する",
    "cn": "捐赠突变农产品"
  },
  "(Giữ nguyên / Tự động)": {
    "en": "(Hold/Auto)",
    "ja": "(長押し/オート)",
    "cn": "（保持/自动）"
  },
  "➕ Tạo Cuốc / Quặng Mới": {
    "en": "➕ Create New Pickaxe/Ore",
    "ja": "➕ 新しいつるはし/鉱石を作成",
    "cn": "➕ 创建新的镐/矿石"
  },
  "Trận Đang Nối (Active)": {
    "en": "Active Battle",
    "ja": "アクティブなバトル",
    "cn": "主动战斗"
  },
  "Giá bán cơ bản (Coins)": {
    "en": "Base selling price (Coins)",
    "ja": "基本販売価格（コイン）",
    "cn": "基本售价（币）"
  },
  "🔗 Tiến Hành Nối Server": {
    "en": "🔗 Proceed to connect to the server",
    "ja": "🔗 サーバーへの接続に進みます",
    "cn": "🔗 继续连接服务器"
  },
  "💾 Lưu Hồ Sơ Bot Server": {
    "en": "💾 Save Bot Server Profile",
    "ja": "💾 ボットサーバープロファイルを保存",
    "cn": "💾 保存机器人服务器配置文件"
  },
  "Ngưỡng spam (tin) 2-50": {
    "en": "Spam threshold (news) 2-50",
    "ja": "スパムしきい値 (ニュース) 2 ～ 50",
    "cn": "垃圾邮件阈值（新闻）2-50"
  },
  "Mute - Cấm chat (phút)": {
    "en": "Mute - Ban chat (minutes)",
    "ja": "ミュート - チャットの禁止 (分)",
    "cn": "静音 - 禁止聊天（分钟）"
  },
  "📋 Danh sách cấm server": {
    "en": "📋 Server banned list",
    "ja": "📋 サーバー禁止リスト",
    "cn": "📋 服务器禁止列表"
  },
  "🔊 Trạng thái TempVoice": {
    "en": "🔊 TempVoice status",
    "ja": "🔊 TempVoice ステータス",
    "cn": "🔊 TempVoice 状态"
  },
  "Kênh thông báo lên cấp": {
    "en": "Notification channel level up",
    "ja": "通知チャンネルのレベルアップ",
    "cn": "通知通道级别提升"
  },
  "🗑️ Xóa tất cả kênh câu": {
    "en": "🗑️ Delete all fishing channels",
    "ja": "🗑️ すべての釣りチャンネルを削除します",
    "cn": "🗑️删除所有钓鱼频道"
  },
  "😀 Thả Reaction (Emoji)": {
    "en": "😀 Drop Reaction (Emoji)",
    "ja": "😀 ドロップリアクション (絵文字)",
    "cn": "😀 掉落反应（表情符号）"
  },
  "— Chưa chọn kênh log —": {
    "en": "— Log channel not selected —",
    "ja": "— ログチャネルが選択されていません —",
    "cn": "— 未选择日志通道 —"
  },
  "Chỉ số May mắn (Luck):": {
    "en": "Luck Index (Luck):",
    "ja": "運指数（運）：",
    "cn": "幸运指数（运气）："
  },
  "Cường Hóa (+0 - +300):": {
    "en": "Enhancement (+0 - +300):",
    "ja": "強化 (+0 ～ +300):",
    "cn": "增强（+0 - +300）："
  },
  "Chỉ Số May Mắn (Luck):": {
    "en": "Luck Index (Luck):",
    "ja": "運指数（運）：",
    "cn": "幸运指数（运气）："
  },
  "Ví dụ: SAKURA-VIP-2026": {
    "en": "For example: SAKURA-VIP-2026",
    "ja": "例: SAKURA-VIP-2026",
    "cn": "例如：SAKURA-VIP-2026"
  },
  "🔍 Tìm kiếm vật phẩm...": {
    "en": "🔍 Search for items...",
    "ja": "🔍 アイテムを検索...",
    "cn": "🔍 搜索项目..."
  },
  "Ví dụ: rod_thunder_god": {
    "en": "For example: rod_thunder_god",
    "ja": "例: ロッド_サンダー_ゴッド",
    "cn": "例如：rod_thunder_god"
  },
  "Số MC Coin muốn rút...": {
    "en": "Number of MC Coins you want to withdraw...",
    "ja": "出金したいMCコインの数...",
    "cn": "您想要提取的MC币数量..."
  },
  "vd: Thợ Săn Đêm Bí Ngô": {
    "en": "eg: Night Pumpkin Hunter",
    "ja": "例: ナイトパンプキンハンター",
    "cn": "例如：夜间南瓜猎人"
  },
  "👋 TẠM BIỆT THÀNH VIÊN!": {
    "en": "👋 GOODBYE MEMBERS!",
    "ja": "👋 メンバーの皆さん、さようなら！",
    "cn": "👋 再见会员！"
  },
  "● Hệ thống Online 24/7": {
    "en": "● Online system 24/7",
    "ja": "●24時間365日オンラインシステム",
    "cn": "● 在线系统24/7"
  },
  "🌸 Trang chủ giới thiệu": {
    "en": "🌸 Introduction home page",
    "ja": "🌸紹介ホームページ",
    "cn": "🌟介绍首页"
  },
  "🎣 Câu cá RPG Đại Dương": {
    "en": "🎣 Ocean RPG Fishing",
    "ja": "🎣 海洋 RPG 釣り",
    "cn": "🎣 海洋角色扮演钓鱼"
  },
  "Mạng Xã Hội & Liên Kết": {
    "en": "Social Networks & Links",
    "ja": "ソーシャルネットワークとリンク",
    "cn": "社交网络和链接"
  },
  "Xem hướng dẫn chi tiết": {
    "en": "See detailed instructions",
    "ja": "詳細な手順を参照してください",
    "cn": "查看详细说明"
  },
  "Người chơi trực tuyến:": {
    "en": "Online players:",
    "ja": "オンラインプレイヤー:",
    "cn": "在线玩家："
  },
  "Mạng & Kết Nối Máy Chủ": {
    "en": "Network & Server Connection",
    "ja": "ネットワークとサーバーの接続",
    "cn": "网络和服务器连接"
  },
  "Kỹ Năng RPG & Tùy Biến": {
    "en": "RPG Skills & Customization",
    "ja": "RPG スキルとカスタマイズ",
    "cn": "RPG 技能和定制"
  },
  "của máy chủ Minecraft.": {
    "en": "of the Minecraft server.",
    "ja": "Minecraftサーバーの。",
    "cn": "Minecraft 服务器的。"
  },
  "Xem thông tin Donate →": {
    "en": "View Donate information →",
    "ja": "寄付情報を見る →",
    "cn": "查看捐赠信息 →"
  },
  "🐛 Báo lỗi (Bug Report)": {
    "en": "🐛 Bug Report",
    "ja": "🐛 バグレポート",
    "cn": "🐛 错误报告"
  },
  "Bộ ảnh Photo Slideshow": {
    "en": "Photo Slideshow photo set",
    "ja": "写真スライドショー写真セット",
    "cn": "照片幻灯片照片集"
  },
  "💳 Thông tin tài chính": {
    "en": "💳 Financial information",
    "ja": "💳 財務情報",
    "cn": "💳 财务信息"
  },
  "trong game để kết nối": {
    "en": "in game to connect",
    "ja": "ゲーム内で接続する",
    "cn": "在游戏中连接"
  },
  "💬 Discord URL hoặc ID": {
    "en": "💬 Discord URL or ID",
    "ja": "💬 DiscordのURLまたはID",
    "cn": "💬 不和谐的 URL 或 ID"
  },
  "🔍 Tìm kiếm tệp tin...": {
    "en": "🔍 Search files...",
    "ja": "🔍 ファイルを検索...",
    "cn": "🔍 搜索文件..."
  },
  "Làm mới danh sách tệp": {
    "en": "Refresh file list",
    "ja": "ファイルリストを更新する",
    "cn": "刷新文件列表"
  },
  "Chỉ xem mã nguồn HTML": {
    "en": "View only HTML source code",
    "ja": "HTML ソース コードのみを表示する",
    "cn": "仅查看 HTML 源代码"
  },
  "Tải lại bản xem trước": {
    "en": "Reload the preview",
    "ja": "プレビューをリロードする",
    "cn": "重新加载预览"
  },
  "Tải lại cơ sở dữ liệu": {
    "en": "Reload the database",
    "ja": "データベースをリロードする",
    "cn": "重新加载数据库"
  },
  "Xuất dữ liệu dạng CSV": {
    "en": "Export data as CSV",
    "ja": "データをCSVとしてエクスポート",
    "cn": "将数据导出为 CSV"
  },
  "💌 Mời Bạn Chơi Cờ Vua": {
    "en": "💌 Invite You to Play Chess",
    "ja": "💌 チェスに招待します",
    "cn": "💌邀你下棋"
  },
  "Trở về danh sách Game": {
    "en": "Return to the Games list",
    "ja": "ゲームリストに戻る",
    "cn": "返回游戏列表"
  },
  "Lịch sử sẽ hiện ở đây": {
    "en": "History will appear here",
    "ja": "ここに履歴が表示されます",
    "cn": "历史将会出现在这里"
  },
  "🔐 Đăng nhập Dashboard": {
    "en": "🔐 Login to Dashboard",
    "ja": "🔐 ダッシュボードにログイン",
    "cn": "🔐登录仪表板"
  },
  "→ chọn server → chỉnh": {
    "en": "→ select server → edit",
    "ja": "→ サーバーを選択 → 編集",
    "cn": "→ 选择服务器 → 编辑"
  },
  "🟢 Trực Tuyến (Online)": {
    "en": "🟢 Online",
    "ja": "🟢 オンライン",
    "cn": "🟢 在线"
  },
  "Lọc Từ Cấm & Xúc Phạm": {
    "en": "Filter Forbidden & Offensive Words",
    "ja": "禁止されている言葉や攻撃的な言葉をフィルタリングする",
    "cn": "过滤禁止和攻击性词语"
  },
  "📜 Danh Sách Thành Tựu": {
    "en": "📜 List of Achievements",
    "ja": "📜 実績リスト",
    "cn": "📜 成就列表"
  },
  "Mô Tả & Điều Kiện Đạt": {
    "en": "Description & Qualifications",
    "ja": "説明と資格",
    "cn": "描述和资格"
  },
  "Cấp Mồi / Rương / Pet": {
    "en": "Provides Lure / Chest / Pet",
    "ja": "ルアー/チェスト/ペットを提供します",
    "cn": "提供诱饵/宝箱/宠物"
  },
  "📦 Rương Báu & Hòm Quà": {
    "en": "📦 Treasure Chest & Gift Box",
    "ja": "📦 宝箱とギフトボックス",
    "cn": "📦 宝箱和礼品盒"
  },
  "💎 Khoáng Sản & Đá Quý": {
    "en": "💎 Minerals & Gems",
    "ja": "💎 鉱物と宝石",
    "cn": "💎 矿物和宝石"
  },
  "🌱 Hạt Giống Nông Trại": {
    "en": "🌱 Farm Seeds",
    "ja": "🌱 農場の種子",
    "cn": "🌱 农场种子"
  },
  "Chọn vật phẩm cụ thể:": {
    "en": "Select specific items:",
    "ja": "特定の項目を選択します:",
    "cn": "选择具体项目："
  },
  "🔴 Đang ẩn (Không bán)": {
    "en": "🔴 Hidden (Not for sale)",
    "ja": "🔴 隠し（非売品）",
    "cn": "🔴隐藏（非卖品）"
  },
  "Mô tả vật phẩm troll:": {
    "en": "Troll item description:",
    "ja": "トロールアイテムの説明:",
    "cn": "巨魔物品描述："
  },
  "Key Lệnh (Action Key)": {
    "en": "Action Key",
    "ja": "アクションキー",
    "cn": "动作键"
  },
  "Tùy chọn độ mạnh (VD:": {
    "en": "Strength options (eg:",
    "ja": "強度のオプション (例:",
    "cn": "强度选项（例如："
  },
  "Số phút hiệu lực (VD:": {
    "en": "Number of minutes of validity (eg:",
    "ja": "有効期限の分数 (例:",
    "cn": "有效分钟数（例如："
  },
  "Cặp Đôi Bền Chặt Nhất": {
    "en": "The Strongest Couple",
    "ja": "最強のカップル",
    "cn": "最强情侣"
  },
  "Ngày Cưới & Thời Gian": {
    "en": "Wedding Date & Time",
    "ja": "結婚式の日付と時間",
    "cn": "婚礼日期和时间"
  },
  "🛠️ Dụng Cụ & Phân Bón": {
    "en": "🛠️ Tools & Fertilizers",
    "ja": "🛠️ 道具と肥料",
    "cn": "🛠️ 工具和肥料"
  },
  "📚 Bách Khoa Mỏ Khoáng": {
    "en": "📚 Mineral Mining Encyclopedia",
    "ja": "📚 鉱物採掘百科事典",
    "cn": "📚 矿产开采百科全书"
  },
  "📋 Danh Mục & Cấp Phát": {
    "en": "📋 Catalog & Allocation",
    "ja": "📋 カタログと割り当て",
    "cn": "📋 目录与分配"
  },
  "⏳ Đang tải từ điển...": {
    "en": "⏳ Loading dictionary...",
    "ja": "⏳ 辞書を読み込み中...",
    "cn": "⏳ 正在加载词典..."
  },
  "Hệ số Sức Đào (Power)": {
    "en": "Power Factor",
    "ja": "力率",
    "cn": "功率因数"
  },
  "🔴 Thần Thoại (Mythic)": {
    "en": "🔴 Mythic",
    "ja": "🔴ミシック",
    "cn": "🔴神话"
  },
  "🔄 Đổi Trạng Thái Vote": {
    "en": "🔄 Change Vote Status",
    "ja": "🔄 投票ステータスを変更する",
    "cn": "🔄 更改投票状态"
  },
  "ở Cài đặt chung → bật": {
    "en": "in General Settings → on",
    "ja": "一般設定→オン",
    "cn": "在常规设置→打开"
  },
  "chặn \"con linh béo ú\"": {
    "en": "block the \"fat spirit\"",
    "ja": "「太った魂」をブロックする",
    "cn": "挡住“胖灵”"
  },
  "Đang tải danh sách...": {
    "en": "Loading list...",
    "ja": "リストを読み込んでいます...",
    "cn": "正在加载列表..."
  },
  "(chỉ server này) hoặc": {
    "en": "(this server only) or",
    "ja": "(このサーバーのみ) または",
    "cn": "（仅限此服务器）或"
  },
  "Kênh “Join to Create”": {
    "en": "“Join to Create” channel",
    "ja": "「参加して作成」チャンネル",
    "cn": "“加入创造”频道"
  },
  "Thành viên có economy": {
    "en": "Members have economy",
    "ja": "会員には経済性がある",
    "cn": "会员有经济"
  },
  "Nội dung bot phản hồi": {
    "en": "Bot response content",
    "ja": "ボットの応答内容",
    "cn": "机器人响应内容"
  },
  "➕ Tạo Bản Sao Lưu Mới": {
    "en": "➕ Create New Backup",
    "ja": "➕ 新しいバックアップを作成する",
    "cn": "➕ 创建新备份"
  },
  "— Không tự động gán —": {
    "en": "— No automatic assignment —",
    "ja": "— 自動割り当てなし —",
    "cn": "— 无自动分配 —"
  },
  "-- Không ping role --": {
    "en": "-- No ping role --",
    "ja": "-- ping の役割がありません --",
    "cn": "-- 无 ping 作用 --"
  },
  "Kênh tổ chức Giveaway": {
    "en": "Giveaway organization channel",
    "ja": "プレゼント企画チャンネル",
    "cn": "赠品组织渠道"
  },
  "Kênh đặt bảng nội quy": {
    "en": "The channel sets the rules board",
    "ja": "チャンネルがルールボードを設定する",
    "cn": "频道设定规则板"
  },
  "— Chọn kênh nội quy —": {
    "en": "— Select channel rules —",
    "ja": "— チャネルルールの選択 —",
    "cn": "— 选择频道规则 —"
  },
  "vào server Minecraft.": {
    "en": "Go to the Minecraft server.",
    "ja": "Minecraft サーバーに移動します。",
    "cn": "前往《我的世界》服务器。"
  },
  "Trong game, dùng lệnh": {
    "en": "In the game, use commands",
    "ja": "ゲーム内でコマンドを使用する",
    "cn": "在游戏中使用命令"
  },
  "Đang trang bị cần này": {
    "en": "Equipping this rod",
    "ja": "このロッドを装備すると",
    "cn": "装备此杆"
  },
  "Ví dụ: chest_atlantis": {
    "en": "For example: chest_atlantis",
    "ja": "例: Chest_atlantis",
    "cn": "例如：胸部_亚特兰蒂斯"
  },
  "Âm nhạc Lavalink 24/7": {
    "en": "Lavalink music 24/7",
    "ja": "Lavalink 音楽を 24 時間年中無休で提供",
    "cn": "Lavalink 音乐 24/7"
  },
  "🔐 Đăng nhập tài khoản": {
    "en": "🔐 Log in to your account",
    "ja": "🔐 アカウントにログインします",
    "cn": "🔐登录您的帐户"
  },
  "🏆 Bảng xếp hạng Level": {
    "en": "🏆 Level rankings",
    "ja": "🏆レベルランキング",
    "cn": "🏆 等级排名"
  },
  "Lưu Thay Đổi (Ctrl+S)": {
    "en": "Save Changes (Ctrl+S)",
    "ja": "変更を保存 (Ctrl+S)",
    "cn": "保存更改 (Ctrl+S)"
  },
  "Quản Trị Viên (Admin)": {
    "en": "Administrator (Admin)",
    "ja": "管理者（管理者）",
    "cn": "管理员（管理员）"
  },
  "Tệp Thô (.properties)": {
    "en": "Raw Files (.properties)",
    "ja": "RAW ファイル (.properties)",
    "cn": "原始文件（.properties）"
  },
  "Phiêu Lưu (Adventure)": {
    "en": "Adventure",
    "ja": "冒険",
    "cn": "冒险"
  },
  "Tắt (Không sinh quái)": {
    "en": "Off (Does not spawn monsters)",
    "ja": "オフ (モンスターを出現させません)",
    "cn": "关闭（不生成怪物）"
  },
  "0.0.0.0 hoặc để trống": {
    "en": "0.0.0.0 or leave blank",
    "ja": "0.0.0.0 または空白のままにします",
    "cn": "0.0.0.0 或留空"
  },
  "Khởi động lại máy chủ": {
    "en": "Restart the server",
    "ja": "サーバーを再起動します",
    "cn": "重新启动服务器"
  },
  "Kiểm tra Vault đã cài": {
    "en": "Check installed Vault",
    "ja": "インストールされている Vault を確認する",
    "cn": "检查已安装的保管库"
  },
  "🌸 Tạo Profile Của Bạn": {
    "en": "🌸 Create Your Profile",
    "ja": "🌸 プロフィールを作成する",
    "cn": "创建您的个人资料"
  },
  "🌸 Chia Sẻ Bio Cá Nhân": {
    "en": "🌸 Share Personal Bio",
    "ja": "🌸 個人的な経歴を共有する",
    "cn": "💕 分享个人简介"
  },
  "Vào Discord Support →": {
    "en": "Go to Discord Support →",
    "ja": "Discordサポートに移動→",
    "cn": "前往 Discord 支持 →"
  },
  "Xử lý nhanh trong 24h": {
    "en": "Fast processing within 24 hours",
    "ja": "24時間以内の迅速な処理",
    "cn": "24小时内快速处理"
  },
  "Miễn trừ trách nhiệm:": {
    "en": "Disclaimer:",
    "ja": "免責事項:",
    "cn": "免责声明："
  },
  "💒 Hôn Nhân & Cặp Đôi": {
    "en": "💒 Marriage & Couples",
    "ja": "💒 結婚とカップル",
    "cn": "💒 婚姻与情侣"
  },
  "Nạp Lại Toàn Bộ Cogs": {
    "en": "Refill All Cogs",
    "ja": "すべてのコグを補充する",
    "cn": "重新填充所有齿轮"
  },
  "Nạp Lại Cog Này Ngay": {
    "en": "Refill This Cog Now",
    "ja": "今すぐこの歯車を補充してください",
    "cn": "立即重新填充此齿轮"
  },
  "Đóng database viewer": {
    "en": "Close the database viewer",
    "ja": "データベースビューアを閉じます",
    "cn": "关闭数据库查看器"
  },
  "Đóng trình xem media": {
    "en": "Close the media viewer",
    "ja": "メディアビューアを閉じます",
    "cn": "关闭媒体查看器"
  },
  "8 Người (Tiêu chuẩn)": {
    "en": "8 People (Standard)",
    "ja": "8人（標準）",
    "cn": "8人（标准）"
  },
  "180 Giây (Thoải mái)": {
    "en": "180 Seconds (Comfortable)",
    "ja": "180秒（快適）",
    "cn": "180秒（舒适）"
  },
  "🤖 Mời bot vào server": {
    "en": "🤖 Invite bots to the server",
    "ja": "🤖 ボットをサーバーに招待する",
    "cn": "🤖 邀请机器人加入服务器"
  },
  "📊 Tổng Quan Hệ Thống": {
    "en": "📊 System Overview",
    "ja": "📊 システム概要",
    "cn": "📊 系统概述"
  },
  "👤 Chế độ người dùng:": {
    "en": "👤 User Mode:",
    "ja": "👤 ユーザーモード:",
    "cn": "👤 用户模式："
  },
  "Cơ Sở Dữ Liệu SQLite": {
    "en": "SQLite Database",
    "ja": "SQLiteデータベース",
    "cn": "SQLite数据库"
  },
  "Chọn Server Áp Dụng:": {
    "en": "Select Applicable Server:",
    "ja": "該当するサーバーを選択してください:",
    "cn": "选择适用的服务器："
  },
  "🎣 Câu Cá & Thủy Cung": {
    "en": "🎣 Fishing & Aquarium",
    "ja": "🎣 釣りと水族館",
    "cn": "🎣 钓鱼和水族馆"
  },
  "🌾 Nông Trại & Mùa Vụ": {
    "en": "🌾 Farms & Crops",
    "ja": "🌾 農場と作物",
    "cn": "🌾 农场和农作物"
  },
  "Đột biến (Mutation):": {
    "en": "Mutation:",
    "ja": "突然変異:",
    "cn": "突变："
  },
  "📦 Rương Báu (Chests)": {
    "en": "📦 Chests",
    "ja": "📦 チェスト",
    "cn": "📦 宝箱"
  },
  "🧹 Dọn Sạch Thủy Cung": {
    "en": "🧹 Clean the Aquarium",
    "ja": "🧹 水族館を掃除する",
    "cn": "🧹 清洁水族箱"
  },
  "🛠️ Nông Cụ & Công Cụ": {
    "en": "🛠️ Farm Tools & Tools",
    "ja": "🛠️ 農具と工具",
    "cn": "🛠️农具和工具"
  },
  "🛒 Chỉ bán trong Shop": {
    "en": "🛒 Only sold in Shop",
    "ja": "🛒 ショップのみで販売",
    "cn": "🛒 只在商店出售"
  },
  "🔴 Thần Thoại / Admin": {
    "en": "🔴 Mythology / Admin",
    "ja": "🔴 神話 / 管理者",
    "cn": "🔴神话/管理员"
  },
  "⭐ Linh vật: Chưa đặt": {
    "en": "⭐ Mascot: Not set yet",
    "ja": "⭐ マスコット: まだ設定されていません",
    "cn": "⭐ 吉祥物：尚未确定"
  },
  "Cường Hóa & Tiến Sao": {
    "en": "Strengthening & Advancing Stars",
    "ja": "スターの強化と進化",
    "cn": "强化和提升明星"
  },
  "🟢 Đang bán công khai": {
    "en": "🟢 On public sale",
    "ja": "🟢 一般販売中",
    "cn": "🟢 公开发售"
  },
  "🔴 Thần Thánh (Admin)": {
    "en": "🔴 Divine (Admin)",
    "ja": "🔴ディバイン（管理者）",
    "cn": "🔴神圣（管理员）"
  },
  "🐟 SLAP (Tát bằng cá)": {
    "en": "🐟 SLAP (Slap with fish)",
    "ja": "🐟 SLAP (魚を叩く)",
    "cn": "🐟 SLAP（用鱼拍打）"
  },
  "Không cần (hoặc nhập": {
    "en": "No need (or import",
    "ja": "必要ありません（またはインポート）",
    "cn": "不需要（或导入"
  },
  "💖 Cứu Cây & Diệt Sâu": {
    "en": "💖 Save Trees & Kill Pests",
    "ja": "💖 木を守り、害虫を殺す",
    "cn": "💖 拯救树木并消灭害虫"
  },
  "➕ Cập Nhật Hạt Giống": {
    "en": "➕ Update Seeds",
    "ja": "➕ シードを更新する",
    "cn": "➕ 更新种子"
  },
  "❄️ Mùa Đông (Winter)": {
    "en": "❄️ Winter",
    "ja": "❄️冬",
    "cn": "❄️冬天"
  },
  "⛏️ Cuốc Đào Trang Bị": {
    "en": "⛏️ Equipped Digging Hoe",
    "ja": "⛏️装備された掘鍬",
    "cn": "⛏️ 配备挖掘锄头"
  },
  "💎 Tặng Quặng Vào Túi": {
    "en": "💎 Give Ore Into Bag",
    "ja": "💎 鉱石を袋に入れる",
    "cn": "💎 将矿石放入袋子中"
  },
  "🧨 Thêm Vật Tư Hầm Mỏ": {
    "en": "🧨 More Mining Supplies",
    "ja": "🧨 その他の採掘用品",
    "cn": "🧨 更多采矿用品"
  },
  "🔄 Làm mới người chơi": {
    "en": "🔄 Refresh players",
    "ja": "🔄 プレーヤーを更新する",
    "cn": "🔄 刷新玩家"
  },
  "💖 Cộng Đồng & Xã Hội": {
    "en": "💖 Community & Society",
    "ja": "💖 コミュニティと社会",
    "cn": "💖 社区与社会"
  },
  "Tổng Từ Điển Nối Chữ": {
    "en": "Total Word Connection Dictionary",
    "ja": "総単語接続辞書",
    "cn": "总词连接词典"
  },
  "🦠 Mầm Bệnh Cây Trồng": {
    "en": "🦠 Plant Pathogens",
    "ja": "🦠 植物病原体",
    "cn": "🦠植物病原体"
  },
  "Kênh panel chọn role": {
    "en": "Panel channel selects roles",
    "ja": "パネルチャンネルは役割を選択します",
    "cn": "面板通道选择角色"
  },
  "Ảnh lớn Banner (URL)": {
    "en": "Large image Banner (URL)",
    "ja": "大きな画像バナー（URL）",
    "cn": "大图像横幅 (URL)"
  },
  "= mention thành viên": {
    "en": "= mention member",
    "ja": "=メンバーに言及",
    "cn": "= 提及会员"
  },
  "Quá nhiều chữ IN HOA": {
    "en": "Too many CAPITAL letters",
    "ja": "大文字が多すぎます",
    "cn": "大写字母过多"
  },
  "Clear - Xóa tin nhắn": {
    "en": "Clear - Delete the message",
    "ja": "クリア - メッセージを削除します",
    "cn": "清除 - 删除消息"
  },
  "🌐 Blacklist toàn cục": {
    "en": "🌐 Global Blacklist",
    "ja": "🌐 グローバルブラックリスト",
    "cn": "🌐 全球黑名单"
  },
  "Tạo thread thảo luận": {
    "en": "Create a discussion thread",
    "ja": "ディスカッション スレッドを作成する",
    "cn": "创建讨论线程"
  },
  "Theo kênh Confession": {
    "en": "According to Confession channel",
    "ja": "告白チャンネルによると",
    "cn": "据Confession频道报道"
  },
  "💾 Lưu Cài Đặt Câu Cá": {
    "en": "💾 Save Fishing Settings",
    "ja": "💾 釣り設定を保存",
    "cn": "💾 保存钓鱼设置"
  },
  "➕ Thêm Role Vào Bảng": {
    "en": "➕ Add Roles to the Table",
    "ja": "➕ テーブルに役割を追加する",
    "cn": "➕ 将角色添加到表中"
  },
  "Chân Trang (Footer):": {
    "en": "Footer:",
    "ja": "フッター:",
    "cn": "页脚："
  },
  "Độ bền (Durability):": {
    "en": "Durability:",
    "ja": "耐久性:",
    "cn": "耐用性："
  },
  "🛡️ An toàn & Bảo mật": {
    "en": "🛡️ Safe & Secure",
    "ja": "🛡️ 安心安全",
    "cn": "🛡️ 安全可靠"
  },
  "🛡️ AutoMod & Bảo mật": {
    "en": "🛡️ AutoMod & Security",
    "ja": "🛡️ AutoMod とセキュリティ",
    "cn": "🛡️ AutoMod 和安全"
  },
  "🎫 Kênh hỗ trợ Ticket": {
    "en": "🎫 Ticket support channel",
    "ja": "🎫 チケットサポートチャンネル",
    "cn": "🎫 票务支持渠道"
  },
  "Xóa màn hình console": {
    "en": "Clear console screen",
    "ja": "コンソール画面をクリアする",
    "cn": "清晰的控制台屏幕"
  },
  "Tắt (Không bắt buộc)": {
    "en": "Off (Optional)",
    "ja": "オフ (オプション)",
    "cn": "关闭（可选）"
  },
  "Khán Giả (Spectator)": {
    "en": "Spectator",
    "ja": "観客",
    "cn": "旁观者"
  },
  "Bình Thường (Normal)": {
    "en": "Normal",
    "ja": "ノーマル",
    "cn": "正常"
  },
  "Mật khẩu RCON bí mật": {
    "en": "Secret RCON password",
    "ja": "秘密の RCON パスワード",
    "cn": "RCON 秘密密码"
  },
  "Khởi động lại server": {
    "en": "Restart the server",
    "ja": "サーバーを再起動します",
    "cn": "重新启动服务器"
  },
  "1. Tải plugin về máy": {
    "en": "1. Download the plugin to your device",
    "ja": "1. プラグインをデバイスにダウンロードします",
    "cn": "1. 将插件下载到您的设备"
  },
  "Giám sát log console": {
    "en": "Monitor console logs",
    "ja": "コンソールログを監視する",
    "cn": "监控控制台日志"
  },
  "Danh sách lệnh chính": {
    "en": "List of main commands",
    "ja": "主なコマンド一覧",
    "cn": "主要命令列表"
  },
  "Kênh hỗ trợ Discord:": {
    "en": "Discord support channel:",
    "ja": "Discord サポート チャネル:",
    "cn": "Discord 支持渠道："
  },
  "Tài Liệu & Hướng Dẫn": {
    "en": "Documents & Instructions",
    "ja": "書類と説明書",
    "cn": "文件和说明"
  },
  "Họ & Tên / Biệt danh": {
    "en": "Full Name / Nickname",
    "ja": "氏名 / ニックネーム",
    "cn": "全名/昵称"
  },
  "Đánh giá trải nghiệm": {
    "en": "Rate the experience",
    "ja": "体験を評価する",
    "cn": "评价体验"
  },
  "❓ Câu Hỏi Thường Gặp": {
    "en": "❓ Frequently Asked Questions",
    "ja": "❓ よくある質問",
    "cn": "❓ 常见问题"
  },
  "> chọn máy chủ > mục": {
    "en": "> select server > item",
    "ja": "> サーバーを選択 > アイテム",
    "cn": "> 选择服务器 > 项目"
  },
  "Mô tả bài đăng album": {
    "en": "Album post description",
    "ja": "アルバム投稿の説明",
    "cn": "专辑帖子描述"
  },
  "✏️ Đổi tên hiển thị": {
    "en": "✏️ Change display name",
    "ja": "✏️ 表示名を変更する",
    "cn": "✏️更改显示名称"
  },
  "Tiến độ hoàn thành:": {
    "en": "Completion progress:",
    "ja": "完了の進捗状況:",
    "cn": "完成进度："
  },
  "Ngôn ngữ / Language": {
    "en": "Language / Language",
    "ja": "言語 / 言語",
    "cn": "语言/语言"
  },
  "Mẫu: SELECT 20 dòng": {
    "en": "Sample: SELECT 20 lines",
    "ja": "サンプル：SELECT 20行",
    "cn": "示例：选择 20 行"
  },
  "Mẫu: Danh sách bảng": {
    "en": "Sample: List of tables",
    "ja": "サンプル: テーブルのリスト",
    "cn": "示例：表格列表"
  },
  "📥 Xuất Kết Quả JSON": {
    "en": "📥 Export JSON Result",
    "ja": "📥 JSON結果をエクスポート",
    "cn": "📥 导出 JSON 结果"
  },
  "Nạp Lại Tất Cả Cogs": {
    "en": "Reload All Cogs",
    "ja": "すべての歯車をリロードする",
    "cn": "重新加载所有齿轮"
  },
  "♟️ Cờ Vua Sakura AI": {
    "en": "♟️ Chess Sakura AI",
    "ja": "♟️チェスさくらAI",
    "cn": "♟️ 樱花棋AI"
  },
  "3 Vòng (Tiêu chuẩn)": {
    "en": "3 Rings (Standard)",
    "ja": "3リング（標準）",
    "cn": "3 环（标准）"
  },
  "Chưa nhập từ custom": {
    "en": "The word custom has not been imported",
    "ja": "カスタムという単語はインポートされていません",
    "cn": "尚未导入“custom”一词"
  },
  "Quy tắc thông minh:": {
    "en": "Smart rules:",
    "ja": "賢いルール:",
    "cn": "智能规则："
  },
  "Nhập tên của bạn...": {
    "en": "Enter your name...",
    "ja": "あなたの名前を入力してください...",
    "cn": "输入你的名字..."
  },
  "💌 Mời Bạn Chơi Caro": {
    "en": "💌 We invite you to play Caro",
    "ja": "💌 カロをプレイしてみませんか",
    "cn": "💌我们邀请你来玩卡罗"
  },
  "Quản Trị Khoáng Sản": {
    "en": "Mineral Management",
    "ja": "ミネラル管理",
    "cn": "矿产管理"
  },
  "Người dùng tiếp cận": {
    "en": "User approach",
    "ja": "ユーザーアプローチ",
    "cn": "用户方法"
  },
  "⚡ Chuyển Trạng Thái": {
    "en": "⚡ Change Status",
    "ja": "⚡ステータス変更",
    "cn": "⚡ 更改状态"
  },
  "Tổng Tiền Kiếm Được": {
    "en": "Total Money Earned",
    "ja": "獲得した合計金額",
    "cn": "赚到的钱总额"
  },
  "🦈 To Lớn (6 - 25kg)": {
    "en": "🦈 Large (6 - 25kg)",
    "ja": "🦈 ラージ（6～25kg）",
    "cn": "🦈 大号（6 - 25 公斤）"
  },
  "Kho Mồi & Rương Báu": {
    "en": "Lure Warehouse & Treasure Chest",
    "ja": "ルアー倉庫＆宝箱",
    "cn": "诱饵仓库和宝箱"
  },
  "8:30 PM (20h30) tối": {
    "en": "8:30 PM (8:30 p.m.) evening",
    "ja": "午後 8 時 30 分 (午後 8 時 30 分) 夕方",
    "cn": "晚上 8:30（晚上 8:30）"
  },
  "cùng ngày. Giới hạn": {
    "en": "same day. Limit",
    "ja": "同じ日。限界",
    "cn": "同一天。限制"
  },
  "Hạn Sử Dụng Hôm Nay": {
    "en": "Expiry Date Today",
    "ja": "有効期限は今日です",
    "cn": "今天到期日"
  },
  "Tạo Mã Giftcode Mới": {
    "en": "Create New Giftcode",
    "ja": "新しいギフトコードを作成する",
    "cn": "创建新的礼品代码"
  },
  "🌐 Tất cả trạng thái": {
    "en": "🌐 All statuses",
    "ja": "🌐 すべてのステータス",
    "cn": "🌐所有状态"
  },
  "Chỉ Số & Thuộc Tính": {
    "en": "Stats & Attributes",
    "ja": "統計と属性",
    "cn": "统计数据和属性"
  },
  "Khai Thác Mỏ Khoáng": {
    "en": "Mineral Mining",
    "ja": "鉱物採掘",
    "cn": "矿物开采"
  },
  "🛒 Danh Mục Cửa Hàng": {
    "en": "🛒 Store Directory",
    "ja": "🛒 ストアディレクトリ",
    "cn": "🛒 商店目录"
  },
  "❌ Không thể gia hạn": {
    "en": "❌ Cannot be extended",
    "ja": "❌延長不可",
    "cn": "❌ 不可延长"
  },
  "Số tiền hoặc % (VD:": {
    "en": "Amount or % (eg:",
    "ja": "量または% (例:",
    "cn": "金额或%（例如："
  },
  "Thiệt hại coin (VD:": {
    "en": "Coin damage (eg:",
    "ja": "コインのダメージ (例:",
    "cn": "硬币损坏（例如："
  },
  "URL ảnh/âm thanh hù": {
    "en": "Scare image/audio URL",
    "ja": "恐怖画像・音声URL",
    "cn": "吓人的图像/音频 URL"
  },
  "🌸 Mùa Xuân (Spring)": {
    "en": "🌸 Spring",
    "ja": "🌸春",
    "cn": "🌈春天"
  },
  "🧬 Các Loại Đột Biến": {
    "en": "🧬 Types of Mutations",
    "ja": "🧬 突然変異の種類",
    "cn": "🧬 突变类型"
  },
  "🔧 Sửa Tối Đa Độ Bền": {
    "en": "🔧 Maximum Repair Durability",
    "ja": "🔧 最大の修理耐久性",
    "cn": "🔧 最大修复耐久性"
  },
  "💾 Lưu Cấu Hình Kênh": {
    "en": "💾 Save Channel Configuration",
    "ja": "💾 チャンネル設定を保存",
    "cn": "💾 保存通道配置"
  },
  "✨ Tạo Thành Tựu Mới": {
    "en": "✨ Create New Achievements",
    "ja": "✨ 新しい実績を作成する",
    "cn": "✨ 创造新业绩"
  },
  "❌ Thu Hồi Thành Tựu": {
    "en": "❌ Withdraw Achievements",
    "ja": "❌ 実績を撤回する",
    "cn": "❌ 撤回成就"
  },
  "Danh Mục Phân Loại:": {
    "en": "Classification Category:",
    "ja": "分類カテゴリー:",
    "cn": "分类类别："
  },
  "Thành Viên Ghi Điểm": {
    "en": "Members Score Points",
    "ja": "メンバーのスコアポイント",
    "cn": "会员积分"
  },
  "🧪 Phân Bón Sinh Học": {
    "en": "🧪 Biological Fertilizer",
    "ja": "🧪生物肥料",
    "cn": "🧪生物肥料"
  },
  "🛠️ Dụng Cụ Canh Tác": {
    "en": "🛠️ Farming Tools",
    "ja": "🛠️ 農具",
    "cn": "🛠️农具"
  },
  "🔄 Làm Mới Danh Sách": {
    "en": "🔄 Refresh List",
    "ja": "🔄 リストを更新",
    "cn": "🔄 刷新列表"
  },
  "👤 Người Dùng Thường": {
    "en": "👤 Regular Users",
    "ja": "👤 通常のユーザー",
    "cn": "👤普通用户"
  },
  "— Không cần duyệt —": {
    "en": "— No approval needed —",
    "ja": "— 承認は必要ありません —",
    "cn": "— 无需批准 —"
  },
  "📢 Đăng panel Ticket": {
    "en": "📢 Post the Ticket panel",
    "ja": "📢 チケットパネルを投稿する",
    "cn": "📢 张贴票务面板"
  },
  "📍 Bảng cài đặt kênh": {
    "en": "📍 Channel settings panel",
    "ja": "📍 チャンネル設定パネル",
    "cn": "📍 频道设置面板"
  },
  "Chân Embed (Footer)": {
    "en": "Footer Embed",
    "ja": "フッターの埋め込み",
    "cn": "页脚嵌入"
  },
  "Cấm user dùng bot ở": {
    "en": "Ban users from using bots",
    "ja": "ユーザーによるボットの使用を禁止する",
    "cn": "禁止用户使用机器人"
  },
  "Nút trả lời ẩn danh": {
    "en": "Anonymous reply button",
    "ja": "匿名返信ボタン",
    "cn": "匿名回复按钮"
  },
  "Thành viên có level": {
    "en": "Members have levels",
    "ja": "メンバーにはレベルがあります",
    "cn": "会员有等级"
  },
  "Vai Trò (Role) Nhận": {
    "en": "Role Receive",
    "ja": "ロールレシーブ",
    "cn": "角色接收"
  },
  "— Không ping role —": {
    "en": "— Do not ping role —",
    "ja": "— 役割に ping を実行しない —",
    "cn": "— 不 ping 角色 —"
  },
  "-- Chọn kênh gửi --": {
    "en": "-- Select sending channel --",
    "ja": "-- 送信チャンネルを選択 --",
    "cn": "-- 选择发送通道 --"
  },
  "Kênh thông báo code": {
    "en": "Code notification channel",
    "ja": "コード通知チャネル",
    "cn": "代码通知通道"
  },
  "Role ping nhận code": {
    "en": "Role ping receives code",
    "ja": "ロール ping がコードを受信する",
    "cn": "角色 ping 接收代码"
  },
  "Phần thưởng (Prize)": {
    "en": "Prize",
    "ja": "賞品",
    "cn": "奖品"
  },
  "Xác Nhận Nối Server": {
    "en": "Confirm Server Connection",
    "ja": "サーバー接続の確認",
    "cn": "确认服务器连接"
  },
  "Kênh Đăng Giveaway:": {
    "en": "Giveaway Posting Channel:",
    "ja": "プレゼント投稿チャンネル:",
    "cn": "赠品发布渠道："
  },
  "Số phút, số tiền...": {
    "en": "Number of minutes, amount of money...",
    "ja": "時間や金額など…",
    "cn": "分钟数、金额……"
  },
  "Để trống = tên role": {
    "en": "Leave blank = role name",
    "ja": "空白のまま = ロール名",
    "cn": "留空=角色名称"
  },
  "Cấu Hình Properties": {
    "en": "Configuration Properties",
    "ja": "構成プロパティ",
    "cn": "配置属性"
  },
  "🔐 Đăng Nhập Discord": {
    "en": "🔐 Login to Discord",
    "ja": "🔐 Discordにログイン",
    "cn": "🔐 登录 Discord"
  },
  "✨ Tính năng nổi bật": {
    "en": "✨ Outstanding features",
    "ja": "✨優れた機能",
    "cn": "✨ 突出特点"
  },
  "Câu Cá & Chợ Cá RPG": {
    "en": "Fishing & Fish Market RPG",
    "ja": "釣り＆魚市場RPG",
    "cn": "钓鱼和鱼市角色扮演游戏"
  },
  "🖼️ Xem thư viện ảnh": {
    "en": "🖼️ View photo gallery",
    "ja": "🖼️ フォトギャラリーを見る",
    "cn": "🖼️ 查看照片库"
  },
  "📖 Hướng dẫn sử dụng": {
    "en": "📖 Instructions for use",
    "ja": "📖 使用説明書",
    "cn": "📖 使用说明"
  },
  "Đăng nhập Dashboard": {
    "en": "Log in to Dashboard",
    "ja": "ダッシュボードにログインする",
    "cn": "登录仪表板"
  },
  "Liên Kết Discord-MC": {
    "en": "Discord-MC Link",
    "ja": "Discord-MCリンク",
    "cn": "Discord-MC 链接"
  },
  "Dừng server an toàn": {
    "en": "Stop the server safely",
    "ja": "サーバーを安全に停止する",
    "cn": "安全地停止服务器"
  },
  "Chi Tiết Quyền Hạn:": {
    "en": "Power Details:",
    "ja": "電力の詳細:",
    "cn": "电源详情："
  },
  "🔌 Bật / Tắt Máy Chủ": {
    "en": "🔌 Enable/Disable Server",
    "ja": "🔌 サーバーを有効/無効にする",
    "cn": "🔌 启用/禁用服务器"
  },
  "Giao Diện Trực Quan": {
    "en": "Intuitive Interface",
    "ja": "直感的なインターフェース",
    "cn": "直观的界面"
  },
  "Sinh Tồn (Survival)": {
    "en": "Survival",
    "ja": "サバイバル",
    "cn": "生存"
  },
  "Sáng Tạo (Creative)": {
    "en": "Creative",
    "ja": "クリエイティブ",
    "cn": "创意"
  },
  "Bình Yên (Peaceful)": {
    "en": "Peaceful",
    "ja": "平和な",
    "cn": "和平"
  },
  "📘 Hướng dẫn cài đặt": {
    "en": "📘 Installation instructions",
    "ja": "📘 インストール手順",
    "cn": "📘 安装说明"
  },
  "Chọn đúng file .jar": {
    "en": "Choose the correct .jar file",
    "ja": "正しい .jar ファイルを選択してください",
    "cn": "选择正确的 .jar 文件"
  },
  "Vào thư mục plugins": {
    "en": "Go to the plugins folder",
    "ja": "プラグインフォルダーに移動します",
    "cn": "转到插件文件夹"
  },
  "/setwarp <tên_warp>": {
    "en": "/setwarp <warp_name>",
    "ja": "/setwarp <ワープ名>",
    "cn": "/setwarp <扭曲名称>"
  },
  "🌐 Xem Danh Sách Bio": {
    "en": "🌐 View Bio List",
    "ja": "🌐 略歴リストを見る",
    "cn": "🌐 查看简历列表"
  },
  "Thêm Bot Vào Server": {
    "en": "Add Bot To Server",
    "ja": "ボットをサーバーに追加",
    "cn": "将机器人添加到服务器"
  },
  "🚀 Gửi Phản Hồi Ngay": {
    "en": "🚀 Send Feedback Now",
    "ja": "🚀 今すぐフィードバックを送信",
    "cn": "🚀 立即发送反馈"
  },
  "Tổng quan (General)": {
    "en": "Overview (General)",
    "ja": "概要（全般）",
    "cn": "概述（一般）"
  },
  "💖 Ủng Hộ Sakura Bot": {
    "en": "💖 Support Sakura Bot",
    "ja": "💖 さくらボットをサポート",
    "cn": "💖 支持樱花机器人"
  },
  "tên mới (≥3 ký tự)": {
    "en": "new name (≥3 characters)",
    "ja": "新しい名前 (3 文字以上)",
    "cn": "新名称（≥3个字符）"
  },
  "Số Tài Khoản (STK)": {
    "en": "Account Number (STK)",
    "ja": "口座番号 (STK)",
    "cn": "帐号 (STK)"
  },
  "● Trực Tiếp (Live)": {
    "en": "● Live",
    "ja": "● ライブ",
    "cn": "● 直播"
  },
  "Chưa chọn database": {
    "en": "Database not selected",
    "ja": "データベースが選択されていません",
    "cn": "未选择数据库"
  },
  "Mẫu: Đếm tổng dòng": {
    "en": "Sample: Count total lines",
    "ja": "サンプル: 総行数をカウントする",
    "cn": "示例：计算总行数"
  },
  "Thu nhỏ (Zoom Out)": {
    "en": "Zoom Out",
    "ja": "ズームアウト",
    "cn": "缩小"
  },
  "Phóng to (Zoom In)": {
    "en": "Zoom In",
    "ja": "ズームイン",
    "cn": "放大"
  },
  "🔐 Mã hóa & Giải mã": {
    "en": "🔐 Encoding & Decoding",
    "ja": "🔐 エンコードとデコード",
    "cn": "🔐 编码与解码"
  },
  "🔥 Khó (Kiện Tướng)": {
    "en": "🔥 Difficult (Grandmaster)",
    "ja": "🔥 難しい (グランドマスター)",
    "cn": "🔥 困难（宗师）"
  },
  "Cấp độ: Trung bình": {
    "en": "Level: Medium",
    "ja": "レベル: 中",
    "cn": "级别：中"
  },
  "Cài Đặt Phòng Chơi": {
    "en": "Playroom Settings",
    "ja": "プレイルームの設定",
    "cn": "游戏室设置"
  },
  "🌐 Ngôn ngữ từ vựng": {
    "en": "🌐 Vocabulary language",
    "ja": "🌐 語彙言語",
    "cn": "🌐 词汇语言"
  },
  "30 Giây (Siêu tốc)": {
    "en": "30 Seconds (Super Speed)",
    "ja": "30秒（スーパースピード）",
    "cn": "30秒（超高速）"
  },
  "🎨 ĐẾN LƯỢT BẠN VẼ!": {
    "en": "🎨 IT'S YOUR TURN TO DRAW!",
    "ja": "🎨 あなたが絵を描く番です!",
    "cn": "🎨 轮到你画画了！"
  },
  "💌 Mời Bạn Tham Gia": {
    "en": "💌 We invite you to join",
    "ja": "💌 ぜひご参加ください",
    "cn": "💌诚邀您的加入"
  },
  "Đính kèm tệp / ảnh": {
    "en": "Attach files/photos",
    "ja": "ファイル/写真を添付する",
    "cn": "附加文件/照片"
  },
  "⚙️ Cấu hình server": {
    "en": "⚙️ Server configuration",
    "ja": "⚙️ サーバー構成",
    "cn": "⚙️服务器配置"
  },
  "Quản Trị Nông Trại": {
    "en": "Farm Management",
    "ja": "農場管理",
    "cn": "农场管理"
  },
  "Quản Trị Minecraft": {
    "en": "Minecraft Administration",
    "ja": "Minecraft 管理者",
    "cn": "我的世界管理"
  },
  "Quản Trị Thành Tựu": {
    "en": "Achievement Management",
    "ja": "実績管理",
    "cn": "成果管理"
  },
  "Quản Lý Tệp & Cogs": {
    "en": "File Management & Cogs",
    "ja": "ファイル管理と歯車",
    "cn": "文件管理和齿轮"
  },
  "Quản Trị Admin Web": {
    "en": "Web Admin Administration",
    "ja": "Web管理者管理",
    "cn": "网络管理员管理"
  },
  "Lệnh & Modules Nạp": {
    "en": "Commands & Modules Loaded",
    "ja": "ロードされたコマンドとモジュール",
    "cn": "加载的命令和模块"
  },
  "không thể cày cuốc": {
    "en": "cannot plow",
    "ja": "耕すことができない",
    "cn": "不能犁地"
  },
  "Số Dư (Coins & Xu)": {
    "en": "Balance (Coins & Coins)",
    "ja": "残高（コインとコイン）",
    "cn": "余额（硬币和硬币）"
  },
  "Thành Tựu Gần Nhất": {
    "en": "Latest Achievements",
    "ja": "最新の成果",
    "cn": "最新成果"
  },
  "🧵 Nối Từ & Trí Tuệ": {
    "en": "🧵 Word Connection & Wisdom",
    "ja": "🧵 言葉のつながりと知恵",
    "cn": "🧵 文字联系与智慧"
  },
  "🎁 Quản Lý Giftcode": {
    "en": "🎁 Giftcode Management",
    "ja": "🎁 ギフトコード管理",
    "cn": "🎁 礼品码管理"
  },
  "🐠 Xem Bể Thủy Cung": {
    "en": "🐠 See the Aquarium",
    "ja": "🐠 水族館を見る",
    "cn": "🐠 参观水族馆"
  },
  "🎛️ Thao Túng Tỉ Lệ": {
    "en": "🎛️ Scale Manipulation",
    "ja": "🎛️ スケールの操作",
    "cn": "🎛️ 尺度操纵"
  },
  "Phân hạng kích cỡ:": {
    "en": "Size classification:",
    "ja": "サイズ分類:",
    "cn": "尺寸分类："
  },
  "Số sao (0 - 20 ⭐):": {
    "en": "Number of stars (0 - 20 ⭐):",
    "ja": "星の数 (0 - 20 ⭐):",
    "cn": "星星数量（0 - 20 ⭐）："
  },
  "Danh mục vật phẩm:": {
    "en": "Item categories:",
    "ja": "アイテムカテゴリ:",
    "cn": "物品类别："
  },
  "Sinh Vật Thủy Cung": {
    "en": "Aquarium Creatures",
    "ja": "水族館の生き物",
    "cn": "水族馆生物"
  },
  "Hành Động Quản Trị": {
    "en": "Administrative Action",
    "ja": "行政措置",
    "cn": "行政行为"
  },
  "➕ Thêm Vào Gói Quà": {
    "en": "➕ Add to Gift Wrapping",
    "ja": "➕ ギフトラッピングに追加",
    "cn": "➕ 添加到礼品包装"
  },
  "✨ Tiện Ích & Troll": {
    "en": "✨ Gadgets & Trolls",
    "ja": "✨ ガジェットとトロール",
    "cn": "✨ 小工具和巨魔"
  },
  "Thuộc Tính / Mô Tả": {
    "en": "Attribute / Description",
    "ja": "属性/説明",
    "cn": "属性/描述"
  },
  "Loại tiền gia hạn:": {
    "en": "Renewal currency:",
    "ja": "更新通貨:",
    "cn": "续订币种："
  },
  "[Bấm để Đóng / Mở]": {
    "en": "[Click to Close / Open]",
    "ja": "[クリックして閉じる/開く]",
    "cn": "[点击关闭/打开]"
  },
  "Ý Nghĩa & Tác Dụng": {
    "en": "Meaning & Effects",
    "ja": "意味と効果",
    "cn": "意义及作用"
  },
  "Nội dung câu troll": {
    "en": "Content of troll sentence",
    "ja": "荒らし文の内容",
    "cn": "巨魔句子的内容"
  },
  "Biệt danh mới (VD:": {
    "en": "New nickname (eg:",
    "ja": "新しいニックネーム (例:",
    "cn": "新昵称（例如："
  },
  "👤 Quản Lý Nông Dân": {
    "en": "👤 Farmer Management",
    "ja": "👤 農家の管理",
    "cn": "👤 农民管理"
  },
  "Chưa chọn nông dân": {
    "en": "Haven't chosen a farmer yet",
    "ja": "まだ農家を選んでいない",
    "cn": "还没有选择农民"
  },
  "Nông Dân Triệu Phú": {
    "en": "Millionaire Farmer",
    "ja": "大富豪ファーマー",
    "cn": "百万富翁农民"
  },
  "➕ Cập Nhật Hoa Màu": {
    "en": "➕ Update Flower Colors",
    "ja": "➕ 花の色を更新",
    "cn": "➕ 更新花朵颜色"
  },
  "💎 Thêm Nguyên Liệu": {
    "en": "💎 Add Ingredients",
    "ja": "💎 材料を追加する",
    "cn": "💎添加配料"
  },
  "Thời Tiết Hiện Tại": {
    "en": "Current Weather",
    "ja": "現在の天気",
    "cn": "当前天气"
  },
  "☀️ Mùa Hạ (Summer)": {
    "en": "☀️ Summer",
    "ja": "☀️夏",
    "cn": "☀️夏天"
  },
  "🍁 Mùa Thu (Autumn)": {
    "en": "🍁 Autumn (Autumn)",
    "ja": "🍁秋(秋)",
    "cn": "🍁 秋天（秋天）"
  },
  "➕ Tạo Vật Phẩm Mới": {
    "en": "➕ Create New Items",
    "ja": "➕ 新しいアイテムを作成する",
    "cn": "➕ 创建新项目"
  },
  "💎 Khoáng Sản (Ore)": {
    "en": "💎 Minerals (Ore)",
    "ja": "💎 鉱物（鉱石）",
    "cn": "💎 矿物（矿石）"
  },
  "Giá mua trong Shop": {
    "en": "Purchase price in Shop",
    "ja": "ショップでの購入価格",
    "cn": "商店购买价格"
  },
  "➕ Tạo Giveaway Mới": {
    "en": "➕ Create New Giveaway",
    "ja": "➕ 新しい特典を作成する",
    "cn": "➕ 创建新赠品"
  },
  "Thời Gian Kết Thúc": {
    "en": "End Time",
    "ja": "終了時間",
    "cn": "结束时间"
  },
  "⚙️ Cài Đặt Máy Chủ": {
    "en": "⚙️ Server Settings",
    "ja": "⚙️ サーバー設定",
    "cn": "⚙️ 服务器设置"
  },
  "Prefix Của Server:": {
    "en": "Server Prefix:",
    "ja": "サーバープレフィックス:",
    "cn": "服务器前缀："
  },
  "TIỂU SỬ / ABOUT ME": {
    "en": "BIOGRAPHY / ABOUT ME",
    "ja": "略歴 / 私について",
    "cn": "传记/关于我"
  },
  "Role hỗ trợ ticket": {
    "en": "Ticket support role",
    "ja": "チケットサポートの役割",
    "cn": "票务支持角色"
  },
  "📋 Danh sách global": {
    "en": "📋 Global list",
    "ja": "📋 グローバルリスト",
    "cn": "📋 全球名单"
  },
  "Cho phép Công khai": {
    "en": "Allow Publicity",
    "ja": "宣伝を許可する",
    "cn": "允许公开"
  },
  "tính EXP khi voice": {
    "en": "Calculate EXP when voice",
    "ja": "ボイス時のEXP計算",
    "cn": "语音时计算EXP"
  },
  "Kênh gửi bảng Role": {
    "en": "Role table sending channel",
    "ja": "役割テーブル送信チャネル",
    "cn": "角色表发送通道"
  },
  "-- Chưa cài đặt --": {
    "en": "-- Not installed --",
    "ja": "-- インストールされていません --",
    "cn": "-- 未安装 --"
  },
  "🎉 Bắt Đầu Giveaway": {
    "en": "🎉 Start Giveaway",
    "ja": "🎉 プレゼントを開始",
    "cn": "🎉 开始赠品"
  },
  "Thời Lượng (Phút):": {
    "en": "Duration (Minutes):",
    "ja": "所要時間 (分):",
    "cn": "持续时间（分钟）："
  },
  "Quỹ Chung (Coins):": {
    "en": "General Fund (Coins):",
    "ja": "一般資金 (コイン):",
    "cn": "普通基金（硬币）："
  },
  "Số Sao (0 - 20 ⭐):": {
    "en": "Number of Stars (0 - 20 ⭐):",
    "ja": "星の数 (0 ～ 20 ⭐):",
    "cn": "星星数量（0 - 20 ⭐）："
  },
  "Mật Khẩu Quản Trị:": {
    "en": "Admin Password:",
    "ja": "管理者パスワード:",
    "cn": "管理员密码："
  },
  "Thêm từ cấm mới...": {
    "en": "Add new forbidden words...",
    "ja": "新しい禁止用語を追加...",
    "cn": "添加新的禁用词..."
  },
  "Ví dụ: frog_potion": {
    "en": "For example: frog_potion",
    "ja": "例: frog_potion",
    "cn": "例如：青蛙药水"
  },
  "Nhập Discord ID...": {
    "en": "Enter Discord ID...",
    "ja": "Discord IDを入力してください...",
    "cn": "输入不和谐 ID..."
  },
  "Ví dụ: GENSHINGIFT": {
    "en": "For example: GENSHINGIFT",
    "ja": "例: ゲンシンギフト",
    "cn": "例如：GENSHIFT"
  },
  "Mời Bot Vào Server": {
    "en": "Invite Bot to Server",
    "ja": "ボットをサーバーに招待する",
    "cn": "邀请机器人加入服务器"
  },
  "Thư Viện Ảnh Anime": {
    "en": "Anime Photo Gallery",
    "ja": "アニメエロ画像",
    "cn": "动漫照片库"
  },
  "Console Điều Khiển": {
    "en": "Console Control",
    "ja": "コンソールコントロール",
    "cn": "控制台控制"
  },
  "Thời gian liên kết": {
    "en": "Link time",
    "ja": "リンク時間",
    "cn": "链接时间"
  },
  "Địa chỉ IP & Cổng:": {
    "en": "IP Address & Port:",
    "ja": "IPアドレスとポート:",
    "cn": "IP 地址和端口："
  },
  "Quyền Hạn Được Cấp": {
    "en": "Powers Granted",
    "ja": "付与された権限",
    "cn": "授予的权力"
  },
  "Người Xem (Viewer)": {
    "en": "Viewer",
    "ja": "ビューア",
    "cn": "观众"
  },
  "⚡ Gửi Lệnh Console": {
    "en": "⚡ Send Console Commands",
    "ja": "⚡ コンソールコマンドを送信する",
    "cn": "⚡ 发送控制台命令"
  },
  "⚙️ Cấu Hình Server": {
    "en": "⚙️ Server Configuration",
    "ja": "⚙️ サーバー構成",
    "cn": "⚙️ 服务器配置"
  },
  "Bật (Cho phép bay)": {
    "en": "On (Allow flight)",
    "ja": "オン (飛行を許可)",
    "cn": "开启（允许飞行）"
  },
  "⬇️ Tải plugin ngay": {
    "en": "⬇️ Download the plugin now",
    "ja": "⬇️ 今すぐプラグインをダウンロードしてください",
    "cn": "⬇️ 立即下载插件"
  },
  "Mở thư mục máy chủ": {
    "en": "Open the server folder",
    "ja": "サーバーフォルダーを開きます",
    "cn": "打开服务器文件夹"
  },
  "/sethome [tên_nhà]": {
    "en": "/sethome [home_name]",
    "ja": "/sethome [ホーム名]",
    "cn": "/sethome [主页名称]"
  },
  "Điều khoản Dịch vụ": {
    "en": "Terms of Service",
    "ja": "利用規約",
    "cn": "服务条款"
  },
  "Cập nhật lần cuối:": {
    "en": "Last updated:",
    "ja": "最終更新日:",
    "cn": "最后更新："
  },
  "🌐 Của Người Khác (": {
    "en": "🌐 Other People's (",
    "ja": "🌐 他の人 (",
    "cn": "🌐其他人的（"
  },
  "Ủng Hộ & Quyên Góp": {
    "en": "Support & Donate",
    "ja": "サポートと寄付",
    "cn": "支持与捐赠"
  },
  "MB Bank (Quân Đội)": {
    "en": "MB Bank (Military)",
    "ja": "MB 銀行 (軍事)",
    "cn": "MB 银行（军事）"
  },
  "Hãy rút một lá bài": {
    "en": "Let's draw a card",
    "ja": "カードを引いてみましょう",
    "cn": "我们来画一张卡"
  },
  "Chính sách Bảo mật": {
    "en": "Privacy Policy",
    "ja": "プライバシーポリシー",
    "cn": "隐私政策"
  },
  "🎵 Tải Âm Thanh MP3": {
    "en": "🎵 Download MP3 Audio",
    "ja": "🎵 MP3 オーディオをダウンロード",
    "cn": "🎵 下载 MP3 音频"
  },
  "📥 Tải Ảnh Đang Xem": {
    "en": "📥 Download Image Currently Viewing",
    "ja": "📥 現在閲覧中の画像をダウンロード",
    "cn": "📥 下载当前正在查看的图像"
  },
  "🎵 Tải Nhạc Nền MP3": {
    "en": "🎵 Download MP3 Background Music",
    "ja": "🎵 MP3 BGM をダウンロード",
    "cn": "🎵 下载MP3背景音乐"
  },
  "▶️ Video tiếp theo": {
    "en": "▶️ Next video",
    "ja": "▶️次の動画",
    "cn": "▶️下一个视频"
  },
  "🪙 Coins tích lũy:": {
    "en": "🪙 Accumulated Coins:",
    "ja": "🪙 蓄積されたコイン:",
    "cn": "🪙累积金币："
  },
  "🧵 Nối Từ & Đố Vui": {
    "en": "🧵 Word Matching & Fun Quiz",
    "ja": "🧵 単語マッチングと楽しいクイズ",
    "cn": "🧵 单词匹配和趣味测验"
  },
  "💖 Xã Hội & Cấp Độ": {
    "en": "💖 Society & Level",
    "ja": "💖 社会とレベル",
    "cn": "💖 社会与等级"
  },
  "👁️ Xem Trước HTML": {
    "en": "👁️ HTML Preview",
    "ja": "👁️ HTML プレビュー",
    "cn": "👁️ HTML 预览"
  },
  "👥 2 Người (Local)": {
    "en": "👥 2 People (Local)",
    "ja": "👥 2名（現地）",
    "cn": "👥 2人（本地）"
  },
  "📋 Copy Link Phòng": {
    "en": "📋 Copy Room Link",
    "ja": "📋 ルームリンクをコピー",
    "cn": "📋复制房间链接"
  },
  "🤖 Bot Sakura: Tắt": {
    "en": "🤖 Bot Sakura: Off",
    "ja": "🤖 ボットさくら: オフ",
    "cn": "🤖 机器人樱花：关闭"
  },
  "KẾT THÚC VÁN ĐẤU!": {
    "en": "END OF THE GAME!",
    "ja": "ゲーム終了！",
    "cn": "游戏结束！"
  },
  "Gõ từ bạn đoán...": {
    "en": "Type the word you guess...",
    "ja": "推測した単語を入力してください...",
    "cn": "输入你猜的单词..."
  },
  "Xem cài đặt phòng": {
    "en": "View room settings",
    "ja": "部屋の設定を表示する",
    "cn": "查看房间设置"
  },
  "Thích nét vẽ này!": {
    "en": "Love this drawing!",
    "ja": "この絵が大好きです!",
    "cn": "喜欢这幅画！"
  },
  "Nét cực to (40px)": {
    "en": "Extremely large stroke (40px)",
    "ja": "非常に大きなストローク (40px)",
    "cn": "超大笔画（40px）"
  },
  "Quản Trị Cửa Hàng": {
    "en": "Store Management",
    "ja": "店舗管理",
    "cn": "店铺管理"
  },
  "🪙 Coins (Thường):": {
    "en": "🪙 Coins (Regular):",
    "ja": "🪙 コイン (通常):",
    "cn": "🪙硬币（普通）："
  },
  "Kỷ Lục Cá To Nhất": {
    "en": "Record for Largest Fish",
    "ja": "最大の魚の記録",
    "cn": "最大鱼类记录"
  },
  "Cần Câu Đang Dùng": {
    "en": "Fishing Rod In Use",
    "ja": "使用中の釣り竿",
    "cn": "使用中的钓鱼竿"
  },
  "🌟 Tất Cả Danh Mục": {
    "en": "🌟 All Categories",
    "ja": "🌟 すべてのカテゴリ",
    "cn": "🌟 所有类别"
  },
  "Danh Hiệu (Title)": {
    "en": "Title",
    "ja": "タイトル",
    "cn": "标题"
  },
  "👤 Quản Lý Cần Thủ": {
    "en": "👤 Fishing Manager",
    "ja": "👤 釣りマネージャー",
    "cn": "👤 钓鱼经理"
  },
  "Chưa chọn cần thủ": {
    "en": "Haven't chosen an angler yet",
    "ja": "まだ釣り人を選んでいない",
    "cn": "还没选好钓手"
  },
  "🔥 Xóa Sạch Giỏ Cá": {
    "en": "🔥 Clear Fish Basket",
    "ja": "🔥 クリアフィッシュバスケット",
    "cn": "🔥 透明鱼篮"
  },
  "Trọng lượng (kg):": {
    "en": "Weight (kg):",
    "ja": "重量 (kg):",
    "cn": "重量（公斤）："
  },
  "⚡ Tự động theo kg": {
    "en": "⚡ Automatically according to kg",
    "ja": "⚡ kgに応じて自動的に",
    "cn": "⚡ 自动按公斤"
  },
  "🐟 Bé Tí (< 1.5kg)": {
    "en": "🐟 Tiny Baby (< 1.5kg)",
    "ja": "🐟 小さな赤ちゃん (< 1.5kg)",
    "cn": "🐟 小宝宝（<1.5公斤）"
  },
  "🪱 Mồi Câu (Baits)": {
    "en": "🪱 Baits",
    "ja": "🪱餌",
    "cn": "🪱 诱饵"
  },
  "Trọng Lượng & Dài": {
    "en": "Weight & Length",
    "ja": "重量と長さ",
    "cn": "重量和长度"
  },
  "⚪ Thường (Common)": {
    "en": "⚪ Common",
    "ja": "⚪共通",
    "cn": "⚪ 常见"
  },
  "❤️ Đặt Lượt Thích": {
    "en": "❤️ Set Likes",
    "ja": "❤️ いいねを設定する",
    "cn": "❤️ 设置喜欢"
  },
  "🌟 Tất cả danh mục": {
    "en": "🌟 All categories",
    "ja": "🌟 すべてのカテゴリ",
    "cn": "🌟所有类别"
  },
  "Phân cấp độ hiếm:": {
    "en": "Rarity classification:",
    "ja": "レア度分類:",
    "cn": "稀有度分类："
  },
  "Cho phép gia hạn:": {
    "en": "Extension allowed:",
    "ja": "許可される拡張子:",
    "cn": "允许延期："
  },
  "Tham Số (Giá Trị)": {
    "en": "Parameter (Value)",
    "ja": "パラメータ（値）",
    "cn": "参数（值）"
  },
  "Ví Dụ & Tương Tác": {
    "en": "Examples & Interactions",
    "ja": "例と対話",
    "cn": "示例和交互"
  },
  "Số phút mute (VD:": {
    "en": "Number of mute minutes (eg:",
    "ja": "ミュートの分数 (例:",
    "cn": "静音分钟数（例如："
  },
  "Cặp Đôi (Bạn Đời)": {
    "en": "Couple (Partners)",
    "ja": "カップル（パートナー）",
    "cn": "情侣（伴侣）"
  },
  "🐛 Cập Nhật Sâu Bọ": {
    "en": "🐛 Pest Update",
    "ja": "🐛 害虫の最新情報",
    "cn": "🐛 害虫更新"
  },
  "✨ Vật Phẩm Custom": {
    "en": "✨ Custom Items",
    "ja": "✨カスタムアイテム",
    "cn": "✨ 定制物品"
  },
  "👤 Tài Khoản Admin": {
    "en": "👤 Admin Account",
    "ja": "👤 管理者アカウント",
    "cn": "👤 管理员帐户"
  },
  "Thể Lực (Stamina)": {
    "en": "Stamina",
    "ja": "スタミナ",
    "cn": "耐力"
  },
  "Tổng Quặng Đã Đào": {
    "en": "Total Ore Excavated",
    "ja": "総採掘鉱石数",
    "cn": "矿石总开采量"
  },
  "Bảo Tàng Địa Chất": {
    "en": "Geological Museum",
    "ja": "地質博物館",
    "cn": "地质博物馆"
  },
  "🔄 Quét Server Mới": {
    "en": "🔄 Scan New Server",
    "ja": "🔄 新しいサーバーをスキャン",
    "cn": "🔄 扫描新服务器"
  },
  "Mô Tả / Điều Kiện": {
    "en": "Description / Conditions",
    "ja": "説明/条件",
    "cn": "描述/条件"
  },
  "⏳ Đang nạp BXH...": {
    "en": "⏳ Loading rankings...",
    "ja": "⏳ ランキングを読み込み中...",
    "cn": "⏳ 正在加载排名..."
  },
  "Tỉ lệ May Mắn (%)": {
    "en": "Lucky Rate (%)",
    "ja": "幸運率 (%)",
    "cn": "幸运率(%)"
  },
  "Số Người Tham Gia": {
    "en": "Number of Participants",
    "ja": "参加者数",
    "cn": "参加人数"
  },
  "trực tiếp từ bot.": {
    "en": "directly from bots.",
    "ja": "ボットから直接。",
    "cn": "直接来自机器人。"
  },
  "⭐ Cấp Quyền Admin": {
    "en": "⭐ Grant Admin Rights",
    "ja": "⭐ 管理者権限を付与する",
    "cn": "⭐ 授予管理员权限"
  },
  "Tích EXP khi chat": {
    "en": "Earn EXP while chatting",
    "ja": "チャットしながらEXPを獲得",
    "cn": "聊天时赚取 EXP"
  },
  "📢 Đăng panel Role": {
    "en": "📢 Post the Role panel",
    "ja": "📢 役割パネルを投稿する",
    "cn": "📢 发布角色面板"
  },
  "🎫 Cấu hình Ticket": {
    "en": "🎫 Ticket configuration",
    "ja": "🎫 チケットの構成",
    "cn": "🎫 票证配置"
  },
  "Kênh panel ticket": {
    "en": "Ticket panel channel",
    "ja": "チケットパネルチャンネル",
    "cn": "票务面板通道"
  },
  "= tag người boost": {
    "en": "= tag the person who boosts",
    "ja": "= ブーストする人にタグを付ける",
    "cn": "= 标记提升的人"
  },
  "Kênh chơi nối chữ": {
    "en": "Word play channel",
    "ja": "言葉遊びチャンネル",
    "cn": "文字游戏频道"
  },
  "Trạng thái Zodiac": {
    "en": "Zodiac status",
    "ja": "黄道帯のステータス",
    "cn": "十二生肖状态"
  },
  "🧹 Bộ lọc nâng cao": {
    "en": "🧹 Advanced filters",
    "ja": "🧹 高度なフィルター",
    "cn": "🧹 高级过滤器"
  },
  "— Tắt TempVoice —": {
    "en": "— Turn off TempVoice —",
    "ja": "— TempVoice をオフにする —",
    "cn": "— 关闭 TempVoice —"
  },
  "⚙️ Cấu hình Level": {
    "en": "⚙️ Level configuration",
    "ja": "⚙️レベル構成",
    "cn": "⚙️ 等级配置"
  },
  "Thông báo lên cấp": {
    "en": "Level up notice",
    "ja": "レベルアップのお知らせ",
    "cn": "升级通知"
  },
  "Từ khóa (Keyword)": {
    "en": "Keyword",
    "ja": "キーワード",
    "cn": "关键词"
  },
  "Mô tả / Hướng dẫn": {
    "en": "Description/Instructions",
    "ja": "説明/説明",
    "cn": "描述/说明"
  },
  "💾 Lưu Kênh Streak": {
    "en": "💾 Save Streak Channel",
    "ja": "💾 ストリークチャンネルを保存",
    "cn": "💾 保存连胜频道"
  },
  "🔌 Liên Kết Plugin": {
    "en": "🔌 Plugin Link",
    "ja": "🔌 プラグインリンク",
    "cn": "🔌 插件链接"
  },
  "Kinh Nghiệm (XP):": {
    "en": "Experience (XP):",
    "ja": "経験値 (XP):",
    "cn": "经验（XP）："
  },
  "Ví dụ: 0987654321": {
    "en": "For example: 0987654321",
    "ja": "例: 0987654321",
    "cn": "例如：0987654321"
  },
  "Số lượng hoặc all": {
    "en": "Quantity or all",
    "ja": "数量またはすべて",
    "cn": "数量或全部"
  },
  "Tính Năng Nổi Bật": {
    "en": "Outstanding Features",
    "ja": "優れた機能",
    "cn": "突出特点"
  },
  "Danh Sách Máy Chủ": {
    "en": "Server List",
    "ja": "サーバーリスト",
    "cn": "服务器列表"
  },
  "Hướng Dẫn Sử Dụng": {
    "en": "Instructions for Use",
    "ja": "使用説明書",
    "cn": "使用说明"
  },
  "📊 Bảng Điều Khiển": {
    "en": "📊 Control Panel",
    "ja": "📊 コントロールパネル",
    "cn": "📊 控制面板"
  },
  "Bảo mật & AutoMod": {
    "en": "Security & AutoMod",
    "ja": "セキュリティとAutoMod",
    "cn": "安全与自动模组"
  },
  "📊 Bảng điều khiển": {
    "en": "📊 Control panel",
    "ja": "📊 コントロールパネル",
    "cn": "📊 控制面板"
  },
  "💻 Mã nguồn GitHub": {
    "en": "💻 GitHub source code",
    "ja": "💻 GitHub ソースコード",
    "cn": "💻 GitHub 源代码"
  },
  "Mã Nguồn (GitHub)": {
    "en": "Source Code (GitHub)",
    "ja": "ソースコード (GitHub)",
    "cn": "源代码 (GitHub)"
  },
  "Kênh TikTok Video": {
    "en": "TikTok Video Channel",
    "ja": "TikTokビデオチャンネル",
    "cn": "抖音视频频道"
  },
  "Trạng Thái Server": {
    "en": "Server Status",
    "ja": "サーバーステータス",
    "cn": "服务器状态"
  },
  "Quản Lý Whitelist": {
    "en": "Whitelist Management",
    "ja": "ホワイトリスト管理",
    "cn": "白名单管理"
  },
  "Buộc dừng process": {
    "en": "Force stop the process",
    "ja": "プロセスを強制停止する",
    "cn": "强制停止进程"
  },
  "Tốc Độ Mạng (I/O)": {
    "en": "Network Speed (I/O)",
    "ja": "ネットワーク速度 (I/O)",
    "cn": "网络速度（I/O）"
  },
  "Thông Tin Máy Chủ": {
    "en": "Server Information",
    "ja": "サーバー情報",
    "cn": "服务器信息"
  },
  "Phiên bản / Core:": {
    "en": "Version/Core:",
    "ja": "バージョン/コア:",
    "cn": "版本/核心："
  },
  "Tên Tệp / Thư Mục": {
    "en": "File / Folder Name",
    "ja": "ファイル/フォルダー名",
    "cn": "文件/文件夹名称"
  },
  "🛡️ Quản Lý Cơ Bản": {
    "en": "🛡️ Basic Management",
    "ja": "🛡️ 基本的な管理",
    "cn": "🛡️基础管理"
  },
  "📁 Quản Lý Tệp Tin": {
    "en": "📁 File Management",
    "ja": "📁 ファイル管理",
    "cn": "📁 文件管理"
  },
  "0 / 27 ô vật phẩm": {
    "en": "0 / 27 item slots",
    "ja": "0 / 27 アイテムスロット",
    "cn": "0 / 27 个物品槽"
  },
  "Chọn Ảnh Icon Mới": {
    "en": "Select New Icon Image",
    "ja": "新しいアイコン画像を選択",
    "cn": "选择新图标图像"
  },
  "Đã cập nhật icon!": {
    "en": "Updated icon!",
    "ja": "アイコンを更新しました！",
    "cn": "更新了图标！"
  },
  "Bật (Có quái vật)": {
    "en": "On (There are monsters)",
    "ja": "オン (モンスターがいます)",
    "cn": "开（有怪物）"
  },
  "Bật (Có động vật)": {
    "en": "On (With animals)",
    "ja": "オン（動物あり）",
    "cn": "开（与动物一起）"
  },
  "Bật (Khuyến nghị)": {
    "en": "Enable (Recommended)",
    "ja": "有効にする (推奨)",
    "cn": "启用（推荐）"
  },
  "Tính năng nổi bật": {
    "en": "Outstanding features",
    "ja": "優れた機能",
    "cn": "突出特点"
  },
  "/login <mật_khẩu>": {
    "en": "/login <password>",
    "ja": "/login <パスワード>",
    "cn": "/登录<密码>"
  },
  "Nội dung chi tiết": {
    "en": "Detailed content",
    "ja": "詳しい内容",
    "cn": "详细内容"
  },
  "> cuộn xuống phần": {
    "en": "> scroll down to section",
    "ja": "> セクションまで下にスクロールします",
    "cn": "> 向下滚动到部分"
  },
  "⚡ Xem Trước & Tải": {
    "en": "⚡ Preview & Download",
    "ja": "⚡ プレビューとダウンロード",
    "cn": "⚡ 预览和下载"
  },
  "Link video thường": {
    "en": "Regular video link",
    "ja": "通常のビデオリンク",
    "cn": "常规视频链接"
  },
  "Dán từ bộ nhớ tạm": {
    "en": "Paste from clipboard",
    "ja": "クリップボードから貼り付け",
    "cn": "从剪贴板粘贴"
  },
  "📤 Tải lên avatar": {
    "en": "📤 Upload avatar",
    "ja": "📤 アバターをアップロード",
    "cn": "📤上传头像"
  },
  "/ Tùy Biến Hồ Sơ": {
    "en": "/ Profile Customization",
    "ja": "/ プロファイルのカスタマイズ",
    "cn": "/ 个人资料定制"
  },
  "Danh Sách Cogs (": {
    "en": "Cogs List (",
    "ja": "歯車リスト (",
    "cn": "齿轮列表（"
  },
  "Lưu Tệp (Ctrl+S)": {
    "en": "Save File (Ctrl+S)",
    "ja": "ファイルを保存 (Ctrl+S)",
    "cn": "保存文件（Ctrl+S）"
  },
  "Mở trong tab mới": {
    "en": "Open in new tab",
    "ja": "新しいタブで開く",
    "cn": "在新选项卡中打开"
  },
  "Khóa dịch chuyển": {
    "en": "Teleport lock",
    "ja": "テレポートロック",
    "cn": "传送锁"
  },
  "Lịch sử nước đi:": {
    "en": "Move history:",
    "ja": "移動履歴:",
    "cn": "移动历史："
  },
  "💡 Số ký tự gợi ý": {
    "en": "💡 Suggested number of characters",
    "ja": "💡 推奨文字数",
    "cn": "💡 建议字符数"
  },
  "Vẽ khó hiểu quá!": {
    "en": "Drawing is so confusing!",
    "ja": "絵を描くのはとても混乱します！",
    "cn": "画图太混乱了！"
  },
  "Thùng sơn đổ màu": {
    "en": "Colored paint bucket",
    "ja": "カラーペイントバケツ",
    "cn": "彩色油漆桶"
  },
  "Bạn cần có quyền": {
    "en": "You need permission",
    "ja": "許可が必要です",
    "cn": "你需要许可"
  },
  "Cấp Phát Kinh Tế": {
    "en": "Economic Allocation",
    "ja": "経済的配分",
    "cn": "经济配置"
  },
  "Quản Lý Giveaway": {
    "en": "Giveaway Management",
    "ja": "プレゼント管理",
    "cn": "赠品管理"
  },
  "Cài Đặt Hệ Thống": {
    "en": "System Settings",
    "ja": "システム設定",
    "cn": "系统设置"
  },
  "👁️ Góc Nhìn User": {
    "en": "👁️ User Perspective",
    "ja": "👁️ ユーザーの視点",
    "cn": "👁️用户视角"
  },
  "Channels kết nối": {
    "en": "Connection channels",
    "ja": "接続チャネル",
    "cn": "连接通道"
  },
  "Module hoạt động": {
    "en": "Module active",
    "ja": "モジュールがアクティブです",
    "cn": "模块激活"
  },
  "Đang kiểm tra...": {
    "en": "Checking...",
    "ja": "確認中...",
    "cn": "正在检查..."
  },
  "Kinh Nghiệm (XP)": {
    "en": "Experience (XP)",
    "ja": "経験値（XP）",
    "cn": "经验（XP）"
  },
  "Danh Hiệu Đã Đạt": {
    "en": "Title Achieved",
    "ja": "タイトル達成",
    "cn": "获得头衔"
  },
  "(Không đột biến)": {
    "en": "(No mutation)",
    "ja": "(突然変異なし)",
    "cn": "（无突变）"
  },
  "➕ Cấp Cá Vào Giỏ": {
    "en": "➕ Add Fish to Basket",
    "ja": "➕ 魚をバスケットに追加",
    "cn": "➕ 将鱼添加到篮子中"
  },
  "Tên Cá & Độ Hiếm": {
    "en": "Fish Name & Rarity",
    "ja": "魚の名前と希少性",
    "cn": "鱼的名称和稀有度"
  },
  "Gói quà đã thêm:": {
    "en": "Gift wrapping added:",
    "ja": "ギフトラッピングを追加しました:",
    "cn": "礼品包装添加："
  },
  "🐾 Thú Cưng (Pet)": {
    "en": "🐾 Pets",
    "ja": "🐾 ペット",
    "cn": "🐾 宠物"
  },
  "🃏 Vật Phẩm Troll": {
    "en": "🃏 Troll Items",
    "ja": "🃏 トロールアイテム",
    "cn": "🃏 巨魔物品"
  },
  "🔮 Báu Vật & Khác": {
    "en": "🔮 Treasures & Other",
    "ja": "🔮 宝物とその他",
    "cn": "🔮 宝藏及其他"
  },
  "Mô tả rương báu:": {
    "en": "Treasure chest description:",
    "ja": "宝箱の説明:",
    "cn": "宝箱说明："
  },
  "🎯 Tỉ Lệ Khi Câu:": {
    "en": "🎯 Fishing Ratio:",
    "ja": "🎯 釣り比率:",
    "cn": "🎯 钓鱼比例："
  },
  "➕ Thêm Cá Vào Bể": {
    "en": "➕ Add Fish to the Tank",
    "ja": "➕ 水槽に魚を追加する",
    "cn": "➕ 将鱼添加到鱼缸中"
  },
  "Câu Cá Đại Dương": {
    "en": "Ocean Fishing",
    "ja": "オーシャンフィッシング",
    "cn": "远洋钓鱼"
  },
  "🎒 Túi Cá Mở Rộng": {
    "en": "🎒 Expandable Fish Bag",
    "ja": "🎒 拡張可能なフィッシュバッグ",
    "cn": "🎒 可扩展鱼袋"
  },
  "Thời hạn (Ngày):": {
    "en": "Term (Day):",
    "ja": "期間 (日):",
    "cn": "学期（日）："
  },
  "✅ Có thể gia hạn": {
    "en": "✅ Can be extended",
    "ja": "✅延長可能",
    "cn": "✅ 可延长"
  },
  "Tham số giá trị:": {
    "en": "Value parameter:",
    "ja": "値パラメータ:",
    "cn": "数值参数："
  },
  "Nội dung ma quái": {
    "en": "Spooky content",
    "ja": "不気味なコンテンツ",
    "cn": "恐怖内容"
  },
  "Tra Cứu Nông Dân": {
    "en": "Look Up Farmers",
    "ja": "農家を調べる",
    "cn": "查找农民"
  },
  "👤 Quản Lý Thợ Mỏ": {
    "en": "👤 Miner Management",
    "ja": "👤 マイナー管理",
    "cn": "👤 矿工管理"
  },
  "🔍 Tra Cứu Thợ Mỏ": {
    "en": "🔍 Miner Lookup",
    "ja": "🔍 マイナー検索",
    "cn": "🔍 矿工查找"
  },
  "🗑️ Dọn Túi Quặng": {
    "en": "🗑️ Clean Out the Ore Bag",
    "ja": "🗑️ 鉱石バッグを掃除する",
    "cn": "🗑️清理矿石袋"
  },
  "💎 Các Loại Quặng": {
    "en": "💎 Types of Ore",
    "ja": "💎 鉱石の種類",
    "cn": "💎 矿石类型"
  },
  "🧬 Đột Biến Quặng": {
    "en": "🧬 Ore Mutation",
    "ja": "🧬 鉱石の突然変異",
    "cn": "🧬 矿石突变"
  },
  "🏆 Toàn thời gian": {
    "en": "🏆 Full time",
    "ja": "🏆フルタイム",
    "cn": "🏆 全职"
  },
  "🐛 Sâu Bọ Gây Hại": {
    "en": "🐛 Harmful Pests",
    "ja": "🐛 有害な害虫",
    "cn": "🐛 有害害虫"
  },
  "Mã Tin Nhắn (ID)": {
    "en": "Message ID (ID)",
    "ja": "メッセージID(ID)",
    "cn": "消息ID（ID）"
  },
  "📊 Trạng Thái Bot": {
    "en": "📊 Bot Status",
    "ja": "📊 ボットのステータス",
    "cn": "📊 机器人状态"
  },
  "Vai Trò Hiện Tại": {
    "en": "Current Role",
    "ja": "現在の役割",
    "cn": "目前的角色"
  },
  "Ngôn Ngữ Server:": {
    "en": "Server Language:",
    "ja": "サーバー言語:",
    "cn": "服务器语言："
  },
  "⚙️ Cài đặt chung": {
    "en": "⚙️ General settings",
    "ja": "⚙️ 一般設定",
    "cn": "⚙️ 常规设置"
  },
  "📊 Thống kê nhanh": {
    "en": "📊 Quick statistics",
    "ja": "📊 簡単な統計",
    "cn": "📊 快速统计"
  },
  "⌨️ Key hướng dẫn": {
    "en": "⌨️ Key instructions",
    "ja": "⌨️ 重要な指示",
    "cn": "⌨️ 关键说明"
  },
  "Trạng thái Tarot": {
    "en": "Tarot status",
    "ja": "タロットのステータス",
    "cn": "塔罗牌状态"
  },
  "🔮 Cung hoàng đạo": {
    "en": "🔮 Zodiac",
    "ja": "🔮 黄道帯",
    "cn": "🔮 十二生肖"
  },
  "Kênh chơi cờ vua": {
    "en": "Chess channel",
    "ja": "チェスチャンネル",
    "cn": "象棋频道"
  },
  "⚠️ Auto-Mod đang": {
    "en": "⚠️ Auto-Mod is",
    "ja": "⚠️自動MODは",
    "cn": "⚠️ 自动模式是"
  },
  "🛡️ Kênh miễn trừ": {
    "en": "🛡️ Exempt channel",
    "ja": "🛡️免除チャンネル",
    "cn": "🛡️豁免通道"
  },
  "Quá ngưỡng → xóa": {
    "en": "Exceeds threshold → delete",
    "ja": "閾値を超える→削除",
    "cn": "超过阈值→删除"
  },
  "Tối thiểu ký tự:": {
    "en": "Minimum characters:",
    "ja": "最小文字数:",
    "cn": "最少字符数："
  },
  "⚡ Thực thi nhanh": {
    "en": "⚡ Fast execution",
    "ja": "⚡ 高速実行",
    "cn": "⚡ 快速执行"
  },
  "Cho phép Ẩn danh": {
    "en": "Allow Anonymous",
    "ja": "匿名を許可する",
    "cn": "允许匿名"
  },
  "Tính EXP & Level": {
    "en": "Calculate EXP & Level",
    "ja": "EXPとレベルの計算",
    "cn": "计算经验值和等级"
  },
  "Chế độ Sync Mode": {
    "en": "Sync Mode",
    "ja": "同期モード",
    "cn": "同步模式"
  },
  "Tên nút hiển thị": {
    "en": "Display button name",
    "ja": "表示ボタン名",
    "cn": "显示按钮名称"
  },
  "Cổng Game (Port)": {
    "en": "Game Port (Port)",
    "ja": "ゲームポート (ポート)",
    "cn": "游戏端口（Port）"
  },
  "Tên Phần Thưởng:": {
    "en": "Reward Name:",
    "ja": "報酬名:",
    "cn": "奖励名称："
  },
  "💾 Lưu Level & XP": {
    "en": "💾 Save Level & XP",
    "ja": "💾 レベルとXPを保存",
    "cn": "💾 保存等级和 XP"
  },
  "Độ Bền Hiện Tại:": {
    "en": "Current Durability:",
    "ja": "現在の耐久性:",
    "cn": "当前耐用性："
  },
  "vd: Kỵ Sĩ Bí Ngô": {
    "en": "eg: Pumpkin Rider",
    "ja": "例：パンプキンライダー",
    "cn": "例如：南瓜骑士"
  },
  "Lý do (tùy chọn)": {
    "en": "Reason (optional)",
    "ja": "理由（任意）",
    "cn": "原因（可选）"
  },
  "Nhập mật khẩu...": {
    "en": "Enter password...",
    "ja": "パスワードを入力してください...",
    "cn": "输入密码..."
  },
  "Bạn mới bắt đầu?": {
    "en": "Are you just starting out?",
    "ja": "始めたばかりですか？",
    "cn": "你刚刚开始吗？"
  },
  "• Phát triển bởi": {
    "en": "• Developed by",
    "ja": "• 開発者",
    "cn": "• 开发者"
  },
  "Tổng Quan Server": {
    "en": "Server Overview",
    "ja": "サーバーの概要",
    "cn": "服务器概览"
  },
  "Thông Tin Server": {
    "en": "Server Information",
    "ja": "サーバー情報",
    "cn": "服务器信息"
  },
  "Cấu Hình Kết Nối": {
    "en": "Connection Configuration",
    "ja": "接続構成",
    "cn": "连接配置"
  },
  "Lưu Kênh Discord": {
    "en": "Save Discord Channel",
    "ja": "Discordチャンネルを保存する",
    "cn": "保存不和谐频道"
  },
  "Khởi động server": {
    "en": "Start the server",
    "ja": "サーバーを起動します",
    "cn": "启动服务器"
  },
  "👤 Xem Người Chơi": {
    "en": "👤 View Players",
    "ja": "👤 プレーヤーを見る",
    "cn": "👤 查看玩家"
  },
  "💾 Lưu Phân Quyền": {
    "en": "💾 Save Decentralization",
    "ja": "💾 分散化を保存",
    "cn": "💾 拯救去中心化"
  },
  "tùy biến dễ dàng": {
    "en": "Easy customization",
    "ja": "簡単なカスタマイズ",
    "cn": "轻松定制"
  },
  "Phiên bản hỗ trợ": {
    "en": "Supported version",
    "ja": "サポートされているバージョン",
    "cn": "支持版本"
  },
  ", ngồi nghỉ ngơi": {
    "en": ", sit and rest",
    "ja": "、座って休む",
    "cn": "，坐下来休息"
  },
  "Yêu cầu hệ thống": {
    "en": "System requirements",
    "ja": "システム要件",
    "cn": "系统要求"
  },
  "/warp <tên_warp>": {
    "en": "/warp <warp_name>",
    "ja": "/warp <ワープ名>",
    "cn": "/经线 <经线名称>"
  },
  "Cam kết bảo mật:": {
    "en": "Privacy commitment:",
    "ja": "プライバシーへの取り組み:",
    "cn": "隐私承诺："
  },
  "CỘNG ĐỒNG SAKURA": {
    "en": "SAKURA COMMUNITY",
    "ja": "さくらコミュニティ",
    "cn": "樱花社区"
  },
  "Mời Sakura Bot →": {
    "en": "Invite Sakura Bot →",
    "ja": "さくらボットを招待 →",
    "cn": "邀请樱花机器人 →"
  },
  "🤝 Hợp tác & Khác": {
    "en": "🤝 Collaboration & Others",
    "ja": "🤝 コラボレーションとその他",
    "cn": "🤝 合作及其他"
  },
  "Fishing (Câu cá)": {
    "en": "Fishing",
    "ja": "釣り",
    "cn": "钓鱼"
  },
  "Liên Hệ & Hỗ Trợ": {
    "en": "Contact & Support",
    "ja": "お問い合わせとサポート",
    "cn": "联系与支持"
  },
  "Lời nhắn cảm ơn": {
    "en": "Thank you message",
    "ja": "ありがとうのメッセージ",
    "cn": "谢谢留言"
  },
  "Chưa mở tệp nào": {
    "en": "No files opened yet",
    "ja": "まだ開いているファイルはありません",
    "cn": "尚未打开任何文件"
  },
  "Tạo thư mục mới": {
    "en": "Create a new folder",
    "ja": "新しいフォルダーを作成する",
    "cn": "创建一个新文件夹"
  },
  "Văn bản đầu vào": {
    "en": "Input text",
    "ja": "テキストを入力する",
    "cn": "输入文字"
  },
  "Chưa có nước đi": {
    "en": "No moves yet",
    "ja": "まだ動きはありません",
    "cn": "还没有动作"
  },
  "⚙️ Về Phòng Chờ": {
    "en": "⚙️ Back to the Waiting Room",
    "ja": "⚙️待合室に戻ります",
    "cn": "⚙️回到候诊室"
  },
  "🚀 Chơi Lại Ngay": {
    "en": "🚀 Play Again Now",
    "ja": "🚀 今すぐもう一度プレイ",
    "cn": "🚀 现在再玩一次"
  },
  "Hoàn tác nét vẽ": {
    "en": "Undo strokes",
    "ja": "ストロークを元に戻す",
    "cn": "撤消笔画"
  },
  "Đang kết nối...": {
    "en": "Connecting...",
    "ja": "接続中...",
    "cn": "正在连接..."
  },
  "⌨️ Lệnh nổi bật": {
    "en": "⌨️ Outstanding command",
    "ja": "⌨️ 優れたコマンド",
    "cn": "⌨️出色的指挥"
  },
  "trực tiếp trong": {
    "en": "directly in",
    "ja": "直接",
    "cn": "直接在"
  },
  "Bảng Điều Khiển": {
    "en": "Control Panel",
    "ja": "コントロールパネル",
    "cn": "控制面板"
  },
  "Máy Chủ Discord": {
    "en": "Discord Server",
    "ja": "ディスコードサーバー",
    "cn": "不和谐服务器"
  },
  "Quản Trị Câu Cá": {
    "en": "Fishing Administration",
    "ja": "漁業管理局",
    "cn": "渔业管理局"
  },
  "Quản Trị Hôn Lễ": {
    "en": "Wedding Administration",
    "ja": "結婚式の管理",
    "cn": "婚礼管理"
  },
  "Quản Lý Nối Chữ": {
    "en": "Letter Connection Management",
    "ja": "レターコネクション管理",
    "cn": "信函连接管理"
  },
  "⚡ Đồng Bộ Slash": {
    "en": "⚡ Slash Sync",
    "ja": "⚡スラッシュシンクロ",
    "cn": "⚡ 斜线同步"
  },
  "Tổng Thành Viên": {
    "en": "General Membership",
    "ja": "一般会員",
    "cn": "普通会员"
  },
  "Kênh Text/Voice": {
    "en": "Text/Voice channel",
    "ja": "テキスト/音声チャンネル",
    "cn": "文字/语音通道"
  },
  "Trạng Thái Node": {
    "en": "Node Status",
    "ja": "ノードのステータス",
    "cn": "节点状态"
  },
  "Phòng Đang Phát": {
    "en": "Playing Room",
    "ja": "プレイルーム",
    "cn": "游戏室"
  },
  "📦 Xem danh sách": {
    "en": "📦 See list",
    "ja": "📦 リストを見る",
    "cn": "📦 查看列表"
  },
  "Đơn Vị Tiền Tệ:": {
    "en": "Currency:",
    "ja": "通貨:",
    "cn": "货币："
  },
  "➕ Cộng thêm (+)": {
    "en": "➕ Plus (+)",
    "ja": "➕ プラス (+)",
    "cn": "➕ 加号 (+)"
  },
  "Tiến Độ Mở Khóa": {
    "en": "Unlock Progress",
    "ja": "進行状況のロックを解除する",
    "cn": "解锁进度"
  },
  "Tra Cứu Cần Thủ": {
    "en": "Look Up Anglers",
    "ja": "釣り人を調べる",
    "cn": "查找钓鱼者"
  },
  "Tài Khoản Admin": {
    "en": "Admin Account",
    "ja": "管理者アカウント",
    "cn": "管理员帐户"
  },
  "Thêm Cá Vào Giỏ": {
    "en": "Add Fish To Cart",
    "ja": "魚をカートに追加",
    "cn": "将鱼添加到购物车"
  },
  "Chiều dài (cm):": {
    "en": "Length (cm):",
    "ja": "長さ (cm):",
    "cn": "长度（厘米）："
  },
  "Độ bền ban đầu:": {
    "en": "Initial durability:",
    "ja": "初期耐久性：",
    "cn": "初始耐久度："
  },
  "❤️ 0 Lượt Thích": {
    "en": "❤️ 0 Likes",
    "ja": "❤️ 0 いいね",
    "cn": "❤️ 0 赞"
  },
  "1,000 lượt dùng": {
    "en": "1,000 uses",
    "ja": "1,000回の使用",
    "cn": "1,000 次使用"
  },
  "🔄 Làm Mới Daily": {
    "en": "🔄 Refresh Daily",
    "ja": "🔄 毎日更新",
    "cn": "🔄 每日刷新"
  },
  "Mã Code Hôm Nay": {
    "en": "Code Code Today",
    "ja": "今日のコードコード",
    "cn": "今日代码"
  },
  "Lượt Đã Sử Dụng": {
    "en": "Counts Used",
    "ja": "使用回数",
    "cn": "使用次数"
  },
  "🪙 Coins thưởng:": {
    "en": "🪙 Bonus Coins:",
    "ja": "🪙 ボーナスコイン:",
    "cn": "🪙奖励金币："
  },
  "🌾 Nông Sản Chín": {
    "en": "🌾 Ripe Agricultural Products",
    "ja": "🌾 熟した農産物",
    "cn": "🌾 成熟的农产品"
  },
  "TẤT CẢ DANH MỤC": {
    "en": "ALL CATEGORIES",
    "ja": "ALL CATEGORIES",
    "cn": "所有类别"
  },
  "🟣 Sử Thi (Epic)": {
    "en": "🟣 Epic",
    "ja": "🟣 Epic",
    "cn": "🟣 史诗般的"
  },
  "🐟 Sinh Vật Biển": {
    "en": "🐟 Marine Creatures",
    "ja": "🐟 Marine Creatures",
    "cn": "🐟 海洋生物"
  },
  "Coin Tối Thiểu:": {
    "en": "Minimum Coins:",
    "ja": "最小コイン:",
    "cn": "最低金币："
  },
  "3.5% cơ hội vớt": {
    "en": "3.5% chance to catch",
    "ja": "3.5% chance to catch",
    "cn": "3.5% 的几率捕获"
  },
  "Thủy Cung Admin": {
    "en": "Aquarium Admin",
    "ja": "Aquarium Admin",
    "cn": "水族馆管理员"
  },
  "⚙️ Đổi Sức Chứa": {
    "en": "⚙️ Change Capacity",
    "ja": "⚙️ 容量の変更",
    "cn": "⚙️ 改变容量"
  },
  "🔄 Tải Lại Tỉ Lệ": {
    "en": "🔄 Reload Rate",
    "ja": "🔄 リロード速度",
    "cn": "🔄 重新加载率"
  },
  "🛠️ Tạo Vật Phẩm": {
    "en": "🛠️ Item Creation",
    "ja": "🛠️ Item Creation",
    "cn": "🛠️ 物品创建"
  },
  "⛏️ Cuốc Khai Mỏ": {
    "en": "⛏️ Mining Pickaxe",
    "ja": "⛏️ Mining Pickaxe",
    "cn": "⛏️ 采矿镐"
  },
  "🧨 Vật Tư Hầm Mỏ": {
    "en": "🧨 Mining Supplies",
    "ja": "🧨 Mining Supplies",
    "cn": "🧨 采矿用品"
  },
  "Tạo Cần Câu Mới": {
    "en": "Create a New Fishing Rod",
    "ja": "新しい釣り竿を作成する",
    "cn": "创建新的钓鱼竿"
  },
  "Tạo Mồi Câu Mới": {
    "en": "Create New Fishing Lures",
    "ja": "Create New Fishing Lures",
    "cn": "创建新的鱼饵"
  },
  "Tổng Số Cặp Đôi": {
    "en": "Total Couples",
    "ja": "Total Couples",
    "cn": "情侣总数"
  },
  "Mùa Vụ Hiện Tại": {
    "en": "Current Season",
    "ja": "Current Season",
    "cn": "当前季节"
  },
  "Hoa màu ưu đãi:": {
    "en": "Preferential flower colors:",
    "ja": "優先される花の色:",
    "cn": "优先花色："
  },
  "Độ Sâu Hiện Tại": {
    "en": "Current Depth",
    "ja": "現在の深さ",
    "cn": "当前深度"
  },
  "🎁 Tặng Cuốc Mới": {
    "en": "🎁 Free New Hoe",
    "ja": "🎁 新しいホーを無料で入手",
    "cn": "🎁 免费新锄头"
  },
  "Thiết Lập Nhanh": {
    "en": "Quick Setup",
    "ja": "クイックセットアップ",
    "cn": "快速设置"
  },
  "CUỐC +150 & 20⭐": {
    "en": "HOOK +150 & 20⭐",
    "ja": "フック+150&20⭐",
    "cn": "钩+150 & 20⭐"
  },
  "⚙️ Kênh Discord": {
    "en": "⚙️ Discord channel",
    "ja": "⚙️Discordチャンネル",
    "cn": "⚙️ 不和谐频道"
  },
  "🗑️ Xóa màn hình": {
    "en": "🗑️ Clear screen",
    "ja": "🗑️ 画面をクリア",
    "cn": "🗑️清晰屏幕"
  },
  "🎁 Cấp Thành Tựu": {
    "en": "🎁 Achievement Level",
    "ja": "🎁 達成レベル",
    "cn": "🎁 成就水平"
  },
  "Mô Tả Vật Phẩm:": {
    "en": "Item Description:",
    "ja": "商品説明:",
    "cn": "物品描述："
  },
  "🗑️ Xóa Màn Hình": {
    "en": "🗑️ Clear Screen",
    "ja": "🗑️ 画面をクリア",
    "cn": "🗑️ 清晰屏幕"
  },
  "⭐ Quản Trị Viên": {
    "en": "⭐ Administrator",
    "ja": "⭐ 管理者",
    "cn": "⭐ 管理员"
  },
  "Tiếng Việt (vi)": {
    "en": "Vietnamese (vi)",
    "ja": "ベトナム語 (vi)",
    "cn": "越南语（六）"
  },
  "🐟 Câu cá (Fish)": {
    "en": "🐟 Fishing (Fish)",
    "ja": "🐟 釣り（魚）",
    "cn": "🐟 钓鱼（鱼）"
  },
  "📢 Gửi thông báo": {
    "en": "📢 Send notification",
    "ja": "📢 通知を送信する",
    "cn": "📢 发送通知"
  },
  "Kênh log ticket": {
    "en": "Ticket log channel",
    "ja": "チケットログチャンネル",
    "cn": "工单日志通道"
  },
  "Thông báo boost": {
    "en": "Notification boost",
    "ja": "通知のブースト",
    "cn": "通知增强"
  },
  "Màu Embed (Hex)": {
    "en": "Embed Color (Hex)",
    "ja": "埋め込み色 (16 進数)",
    "cn": "嵌入颜色（十六进制）"
  },
  "Kênh Word Chain": {
    "en": "Word Chain channel",
    "ja": "ワードチェーンチャンネル",
    "cn": "字链频道"
  },
  "🔕 Bỏ qua ở kênh": {
    "en": "🔕 Skip to the channel",
    "ja": "🔕 チャンネルにスキップ",
    "cn": "🔕 跳至频道"
  },
  "Unmute - Gỡ cấm": {
    "en": "Unmute - Remove ban",
    "ja": "ミュートを解除 - 禁止を解除します",
    "cn": "取消静音 - 解除禁令"
  },
  "Warn - Cảnh cáo": {
    "en": "Warn - Warning",
    "ja": "警告 - 警告",
    "cn": "警告 - 警告"
  },
  "Kênh & Số lượng": {
    "en": "Channel & Quantity",
    "ja": "チャネルと数量",
    "cn": "渠道及数量"
  },
  "phạm vi máy chủ": {
    "en": "server range",
    "ja": "サーバー範囲",
    "cn": "服务器范围"
  },
  "Kênh Confession": {
    "en": "Confession Channel",
    "ja": "告白チャンネル",
    "cn": "告白频道"
  },
  "-- Chọn kênh --": {
    "en": "-- Select channel --",
    "ja": "-- チャンネルを選択 --",
    "cn": "-- 选择频道 --"
  },
  "Kênh đăng panel": {
    "en": "Panel posting channel",
    "ja": "パネル投稿チャンネル",
    "cn": "面板发布通道"
  },
  "-- Chọn role --": {
    "en": "-- Select role --",
    "ja": "-- 役割を選択 --",
    "cn": "-- 选择角色 --"
  },
  "💾 Lưu Auto Role": {
    "en": "💾 Save Auto Role",
    "ja": "💾 自動ロールを保存",
    "cn": "💾 保存自动角色"
  },
  "Trạng Thái RCON": {
    "en": "RCON Status",
    "ja": "RCONステータス",
    "cn": "RCON 状态"
  },
  "🚀 Gửi Thông Báo": {
    "en": "🚀 Send Notification",
    "ja": "🚀 通知を送信",
    "cn": "🚀 发送通知"
  },
  "Số Người Thắng:": {
    "en": "Number of Winners:",
    "ja": "受賞者数:",
    "cn": "获奖者人数："
  },
  "Cấp Độ (Level):": {
    "en": "Level:",
    "ja": "レベル:",
    "cn": "级别："
  },
  "Mô tả chi tiết:": {
    "en": "Detailed description:",
    "ja": "詳細な説明:",
    "cn": "详细说明："
  },
  "Nhập số tiền...": {
    "en": "Enter amount...",
    "ja": "金額を入力してください...",
    "cn": "输入金额..."
  },
  "vd: 30m hoặc 1h": {
    "en": "eg: 30m or 1h",
    "ja": "例: 30 分または 1 時間",
    "cn": "例如：30m或1h"
  },
  "✨ Tiện Ích Khác": {
    "en": "✨ Other Utilities",
    "ja": "✨ その他のユーティリティ",
    "cn": "✨ 其他实用程序"
  },
  "Quản lý Discord": {
    "en": "Manage Discord",
    "ja": "Discordを管理する",
    "cn": "管理不和谐"
  },
  "⚙️ Mở Dashboard": {
    "en": "⚙️ Open Dashboard",
    "ja": "⚙️ ダッシュボードを開く",
    "cn": "⚙️ 打开仪表板"
  },
  "🌸 Miễn phí 100%": {
    "en": "🌸 100% Free",
    "ja": "🌸 完全無料",
    "cn": "100%免费"
  },
  "Level & Kinh tế": {
    "en": "Level & Economy",
    "ja": "レベルと経済性",
    "cn": "水平与经济"
  },
  "👤 Quản lý hồ sơ": {
    "en": "👤 Profile management",
    "ja": "👤 プロフィール管理",
    "cn": "👤 档案管理"
  },
  "Cuộn xuống cuối": {
    "en": "Scroll to the bottom",
    "ja": "一番下までスクロールします",
    "cn": "滚动到底部"
  },
  "Hồ Sơ Cộng Đồng": {
    "en": "Community Profile",
    "ja": "コミュニティプロフィール",
    "cn": "社区简介"
  },
  "PID Tiến trình:": {
    "en": "Process PID:",
    "ja": "プロセス PID:",
    "cn": "进程PID："
  },
  "Vai Trò (Role):": {
    "en": "Role:",
    "ja": "役割:",
    "cn": "角色："
  },
  "🖥️ Bảng Console": {
    "en": "🖥️ Console panel",
    "ja": "🖥️ コンソールパネル",
    "cn": "🖥️ 控制台面板"
  },
  "Hộp Shulker Box": {
    "en": "Shulker Box",
    "ja": "シュルカーボックス",
    "cn": "潜影盒"
  },
  "hỗ trợ vận hành": {
    "en": "operational support",
    "ja": "運用サポート",
    "cn": "运营支持"
  },
  "Tính năng chính": {
    "en": "Main features",
    "ja": "主な特長",
    "cn": "主要特点"
  },
  "Hướng dẫn nhanh": {
    "en": "Quick guide",
    "ja": "クイックガイド",
    "cn": "快速指南"
  },
  "File chính thức": {
    "en": "Official files",
    "ja": "公式ファイル",
    "cn": "官方文件"
  },
  "Định dạng: .jar": {
    "en": "Format: .jar",
    "ja": "形式: .jar",
    "cn": "格式：.jar"
  },
  "📘 Xem hướng dẫn": {
    "en": "📘 See instructions",
    "ja": "📘 手順を参照",
    "cn": "📘 查看说明"
  },
  "/home [tên_nhà]": {
    "en": "/home [home_name]",
    "ja": "/home [ホーム名]",
    "cn": "/home [主页名称]"
  },
  "Hỗ Trợ & Donate": {
    "en": "Support & Donate",
    "ja": "サポートと寄付",
    "cn": "支持与捐赠"
  },
  "QUẢN LÝ CỦA TÔI": {
    "en": "MY MANAGER",
    "ja": "私のマネージャー",
    "cn": "我的经理"
  },
  "Chủ đề phản hồi": {
    "en": "Response topic",
    "ja": "応答トピック",
    "cn": "回应主题"
  },
  "Ví dụ: Linh Dev": {
    "en": "For example: Linh Dev",
    "ja": "例: リン・デヴ",
    "cn": "例如：林德夫"
  },
  "Server quản lý": {
    "en": "Management server",
    "ja": "管理サーバー",
    "cn": "管理服务器"
  },
  "Loại tài khoản": {
    "en": "Account type",
    "ja": "アカウントの種類",
    "cn": "账户类型"
  },
  "💎 Tổng tài sản": {
    "en": "💎 Total assets",
    "ja": "💎総資産",
    "cn": "💎 总资产"
  },
  "💾 Lưu thay đổi": {
    "en": "💾 Save changes",
    "ja": "💾 変更を保存",
    "cn": "💾 保存更改"
  },
  "📊 Bảng Dữ Liệu": {
    "en": "📊 Data Table",
    "ja": "📊 データテーブル",
    "cn": "📊 数据表"
  },
  "⚡ Truy Vấn SQL": {
    "en": "⚡ SQL Query",
    "ja": "⚡ SQLクエリ",
    "cn": "⚡ SQL 查询"
  },
  "Dòng 0 - 0 / 0": {
    "en": "Line 0 - 0 / 0",
    "ja": "行0 - 0 / 0",
    "cn": "线路 0 - 0 / 0"
  },
  "Đổi ngẫu nhiên": {
    "en": "Random change",
    "ja": "ランダムチェンジ",
    "cn": "随机变化"
  },
  "1 Vòng (Nhanh)": {
    "en": "1 Round (Fast)",
    "ja": "1ラウンド(高速)",
    "cn": "1 轮（快速）"
  },
  "Cần tối thiểu:": {
    "en": "Minimum required:",
    "ja": "最低限必要なもの:",
    "cn": "最低要求："
  },
  "🚀 BẮT ĐẦU CHƠI": {
    "en": "🚀 START PLAYING",
    "ja": "🚀 プレイを開始",
    "cn": "🚀 开始玩"
  },
  "Hết thời gian!": {
    "en": "Time's up!",
    "ja": "時間切れです！",
    "cn": "时间到了！"
  },
  "Nét vừa (10px)": {
    "en": "Medium stroke (10px)",
    "ja": "中ストローク (10px)",
    "cn": "中描边（10 像素）"
  },
  "Đăng nhập ngay": {
    "en": "Sign in now",
    "ja": "今すぐサインイン",
    "cn": "立即登录"
  },
  "Quản lý Server": {
    "en": "Server Management",
    "ja": "サーバー管理",
    "cn": "服务器管理"
  },
  "Bảo Mật & Anti": {
    "en": "Security & Anti",
    "ja": "セキュリティとアンチ",
    "cn": "安全防盗"
  },
  "🔄 Nạp Lại Cogs": {
    "en": "🔄 Reload Cogs",
    "ja": "🔄 歯車をリロードする",
    "cn": "🔄 重新加载齿轮"
  },
  "Tên Người Dùng": {
    "en": "User Name",
    "ja": "ユーザー名",
    "cn": "用户名"
  },
  "🥇 Thợ Săn Số 1": {
    "en": "🥇 Number 1 Hunter",
    "ja": "🥇ナンバー1ハンター",
    "cn": "🥇第一猎人"
  },
  "210+ thành tựu": {
    "en": "210+ achievements",
    "ja": "210以上の実績",
    "cn": "210 多项成就"
  },
  "Số lượng thêm:": {
    "en": "Extra Quantity:",
    "ja": "追加数量:",
    "cn": "额外数量："
  },
  "Chọn vật phẩm:": {
    "en": "Select item:",
    "ja": "項目を選択してください:",
    "cn": "选择项目："
  },
  "⚙️ Sức Chứa Bể": {
    "en": "⚙️ Tank Capacity",
    "ja": "⚙️タンク容量",
    "cn": "⚙️ 水箱容量"
  },
  "Cần Câu Sở Hữu": {
    "en": "Fishing Rod Owned",
    "ja": "釣竿所有",
    "cn": "拥有钓鱼竿"
  },
  "🧪 Phân Bón Đất": {
    "en": "🧪 Soil Fertilizer",
    "ja": "🧪土壌肥料",
    "cn": "🧪土壤肥料"
  },
  "Tất cả độ hiếm": {
    "en": "All rarities",
    "ja": "すべてのレアリティ",
    "cn": "所有稀有品"
  },
  "Mô Tả Chi Tiết": {
    "en": "Detailed Description",
    "ja": "詳細な説明",
    "cn": "详细说明"
  },
  "Mô tả loài cá:": {
    "en": "Fish description:",
    "ja": "魚の説明:",
    "cn": "鱼的描述："
  },
  "Coins • Tỉ lệ:": {
    "en": "Coins • Rate:",
    "ja": "コイン • レート:",
    "cn": "硬币• 率："
  },
  "🪙 Tiền Thưởng:": {
    "en": "🪙 Bonus:",
    "ja": "🪙 ボーナス:",
    "cn": "🪙奖金："
  },
  "🏷️ Trạng Thái:": {
    "en": "🏷️ Status:",
    "ja": "🏷️ステータス:",
    "cn": "🏷️状态："
  },
  "Chủ sở hữu ID:": {
    "en": "Owner ID:",
    "ja": "オーナーID:",
    "cn": "所有者 ID："
  },
  "Số Cá Trong Bể": {
    "en": "Number of Fish in the Tank",
    "ja": "水槽内の魚の数",
    "cn": "鱼缸里的鱼数量"
  },
  "Hệ số Bán (x):": {
    "en": "Sales Factor (x):",
    "ja": "売上係数 (x):",
    "cn": "销售系数 (x)："
  },
  "💧 Tưới Toàn Bộ": {
    "en": "💧 Complete Irrigation",
    "ja": "💧 完全な灌漑",
    "cn": "💧 彻底灌溉"
  },
  "👤 Hồ Sơ Thợ Mỏ": {
    "en": "👤 Miner Profile",
    "ja": "👤 マイナープロフィール",
    "cn": "👤 矿工简介"
  },
  "Cuốc Gỗ Sơ Cấp": {
    "en": "Beginner Wooden Hoe",
    "ja": "初心者用木鍬",
    "cn": "初级木锄头"
  },
  "💻 Console Lệnh": {
    "en": "💻 Console Command",
    "ja": "💻 コンソールコマンド",
    "cn": "💻 控制台命令"
  },
  "👥 Người Chơi (": {
    "en": "👥 Player (",
    "ja": "👥プレイヤー (",
    "cn": "👥 玩家 ("
  },
  "Rút Về Discord": {
    "en": "Withdraw to Discord",
    "ja": "Discordに退会する",
    "cn": "撤回不和谐"
  },
  "Thưởng Xu VIP:": {
    "en": "VIP Coin Reward:",
    "ja": "VIPコイン報酬：",
    "cn": "VIP金币奖励："
  },
  "Mô tả vật phẩm": {
    "en": "Item description",
    "ja": "商品説明",
    "cn": "物品描述"
  },
  "💾 Lưu Vật Phẩm": {
    "en": "💾 Save Items",
    "ja": "💾 アイテムを保存",
    "cn": "💾 保存项目"
  },
  "Loại Vật Phẩm:": {
    "en": "Item Type:",
    "ja": "アイテムの種類:",
    "cn": "物品类型："
  },
  "Số Người Thắng": {
    "en": "Number of Winners",
    "ja": "受賞者数",
    "cn": "获奖者人数"
  },
  "Thao tác nhanh": {
    "en": "Quick action",
    "ja": "クイックアクション",
    "cn": "快速行动"
  },
  "🌐 Ngôn ngữ bot": {
    "en": "🌐 Bot language",
    "ja": "🌐 ボット言語",
    "cn": "🌐 机器人语言"
  },
  "💾 Lưu cấu hình": {
    "en": "💾 Save configuration",
    "ja": "💾 設定を保存する",
    "cn": "💾 保存配置"
  },
  "Kênh chào mừng": {
    "en": "Welcome channel",
    "ja": "ウェルカムチャンネル",
    "cn": "欢迎频道"
  },
  "Unban - Gỡ cấm": {
    "en": "Unban - Unban",
    "ja": "禁止解除 - 禁止解除",
    "cn": "解禁 - 解禁"
  },
  "🚫 Cấm dùng bot": {
    "en": "🚫 It is forbidden to use bots",
    "ja": "🚫ボットの使用は禁止されています",
    "cn": "🚫 禁止使用机器人"
  },
  "Bật Confession": {
    "en": "Turn on Confession",
    "ja": "告白をオンにする",
    "cn": "开启忏悔"
  },
  "công tắc chính": {
    "en": "main switch",
    "ja": "メインスイッチ",
    "cn": "主开关"
  },
  "Hạn Dùng (giờ)": {
    "en": "Expiry date (hours)",
    "ja": "有効期限（時間）",
    "cn": "有效期（小时）"
  },
  "Số người thắng": {
    "en": "Number of winners",
    "ja": "当選者数",
    "cn": "获奖人数"
  },
  "Cài đặt plugin": {
    "en": "Install plugins",
    "ja": "プラグインのインストール",
    "cn": "安装插件"
  },
  "Tiêu Đề Embed:": {
    "en": "Embed Title:",
    "ja": "タイトルを埋め込む:",
    "cn": "嵌入标题："
  },
  "💾 Lưu Thay Đổi": {
    "en": "💾 Save Changes",
    "ja": "💾 変更を保存",
    "cn": "💾 保存更改"
  },
  "💾 Lưu Hôn Nhân": {
    "en": "💾 Save Marriage",
    "ja": "💾 結婚を救う",
    "cn": "💾 挽救婚姻"
  },
  "Độ Bền Tối Đa:": {
    "en": "Maximum Durability:",
    "ja": "最大の耐久性:",
    "cn": "最大耐用性："
  },
  "Ví dụ: linhdev": {
    "en": "For example: linhdev",
    "ja": "例: linhdev",
    "cn": "例如：linhdev"
  },
  "🗑 Xóa màn hình": {
    "en": "🗑 Clear screen",
    "ja": "🗑 画面をクリア",
    "cn": "🗑 清晰屏幕"
  },
  "Soạn Thảo MOTD": {
    "en": "Drafting MOTD",
    "ja": "製図MOTD",
    "cn": "起草 MOTD"
  },
  "Ổ Đĩa Khả Dụng": {
    "en": "Available Drives",
    "ja": "利用可能なドライブ",
    "cn": "可用驱动器"
  },
  "1.20.x trở lên": {
    "en": "1.20.x or later",
    "ja": "1.20.x以降",
    "cn": "1.20.x 或更高版本"
  },
  "Di chuyển file": {
    "en": "Move files",
    "ja": "ファイルの移動",
    "cn": "移动文件"
  },
  "Hỗ trợ & Góp ý": {
    "en": "Support & Suggestions",
    "ja": "サポートと提案",
    "cn": "支持与建议"
  },
  "Đọc tài liệu →": {
    "en": "Read documents →",
    "ja": "ドキュメントを読む→",
    "cn": "阅读文档 →"
  },
  "Trải bài Tarot": {
    "en": "Spread Tarot cards",
    "ja": "タロットカードを広げる",
    "cn": "展开塔罗牌"
  },
  "🤖 AI luận giải": {
    "en": "🤖 AI explains",
    "ja": "🤖 AIが説明します",
    "cn": "🤖 AI解释"
  },
  "🇻🇳 Tiếng Việt": {
    "en": "🇻🇳 Vietnamese",
    "ja": "🇻🇳ベトナム語",
    "cn": "🇻🇳 越南语"
  },
  "Đổi thông tin": {
    "en": "Change information",
    "ja": "変更情報",
    "cn": "更改信息"
  },
  "Đang độc thân": {
    "en": "Single",
    "ja": "シングル",
    "cn": "单人"
  },
  "🖼️ Đổi avatar": {
    "en": "🖼️ Change avatar",
    "ja": "🖼️ アバターを変更する",
    "cn": "🖼️更换头像"
  },
  "🏷️ Danh hiệu:": {
    "en": "🏷️ Title:",
    "ja": "🏷️ タイトル:",
    "cn": "🏷️标题："
  },
  "⛏️ Đào Khoáng": {
    "en": "⛏️ Mineral Peaches",
    "ja": "⛏️ミネラルピーチ",
    "cn": "⛏️ 矿物桃子"
  },
  "Tên Ngân Hàng": {
    "en": "Bank Name",
    "ja": "銀行名",
    "cn": "银行名称"
  },
  "Chủ Tài Khoản": {
    "en": "Account Owner",
    "ja": "アカウント所有者",
    "cn": "账户所有者"
  },
  "Dòng 1, Cột 1": {
    "en": "Row 1, Column 1",
    "ja": "行 1、列 1",
    "cn": "第 1 行、第 1 列"
  },
  "Chạy Truy Vấn": {
    "en": "Run Query",
    "ja": "クエリの実行",
    "cn": "运行查询"
  },
  "Chưa chọn tệp": {
    "en": "File not selected",
    "ja": "ファイルが選択されていません",
    "cn": "未选择文件"
  },
  "Tải xuống tệp": {
    "en": "Download files",
    "ja": "ファイルをダウンロードする",
    "cn": "下载文件"
  },
  "🌱 Dễ (Tập Sự)": {
    "en": "🌱 Easy (Novice)",
    "ja": "🌱 簡単 (初心者)",
    "cn": "🌱 简单（新手）"
  },
  "🎮 Chế độ chơi": {
    "en": "🎮 Game mode",
    "ja": "🎮 ゲームモード",
    "cn": "🎮 游戏模式"
  },
  "💾 Lưu Cài Đặt": {
    "en": "💾 Save Settings",
    "ja": "💾 設定を保存",
    "cn": "💾 保存设置"
  },
  "Copy Link Mời": {
    "en": "Copy Invite Link",
    "ja": "招待リンクをコピー",
    "cn": "复制邀请链接"
  },
  "Nét nhỏ (4px)": {
    "en": "Small stroke (4px)",
    "ja": "小さなストローク (4px)",
    "cn": "小笔划（4px）"
  },
  "Nét to (22px)": {
    "en": "Large stroke (22px)",
    "ja": "大きなストローク (22px)",
    "cn": "大笔划（22px）"
  },
  "• Trạng thái:": {
    "en": "• Status:",
    "ja": "• ステータス:",
    "cn": "• 状态："
  },
  "Quản trị viên": {
    "en": "Administrator",
    "ja": "管理者",
    "cn": "管理员"
  },
  "Bạn có thể gõ": {
    "en": "You can type",
    "ja": "入力できます",
    "cn": "您可以输入"
  },
  "__COUNT__ ảnh": {
    "en": "__COUNT__ photos",
    "ja": "__COUNT__ 枚の写真",
    "cn": "__COUNT__ 张照片"
  },
  "BXH Thành Tựu": {
    "en": "Achievement Ranking",
    "ja": "業績ランキング",
    "cn": "成就排名"
  },
  "Dung lượng: —": {
    "en": "Capacity: —",
    "ja": "容量: —",
    "cn": "容量：—"
  },
  "0 cogs đã nạp": {
    "en": "0 cogs loaded",
    "ja": "歯車が 0 個装填されています",
    "cn": "0 个齿轮已加载"
  },
  "➖ Trừ bớt (-)": {
    "en": "➖ Subtract (-)",
    "ja": "➖ 減算 (-)",
    "cn": "➖ 减(-)"
  },
  "🏆 BXH Cao Thủ": {
    "en": "🏆 Master Ranking",
    "ja": "🏆マスターランキング",
    "cn": "🏆 大师排名"
  },
  "Tên Thành Tựu": {
    "en": "Name Achievement",
    "ja": "名前 業績",
    "cn": "名称 成就"
  },
  "➕ Thêm Cá Mới": {
    "en": "➕ Add New Fish",
    "ja": "➕ 新しい魚を追加",
    "cn": "➕ 添加新鱼"
  },
  "🧹 Xóa Túi Rác": {
    "en": "🧹 Clear Trash Bag",
    "ja": "🧹 透明なゴミ袋",
    "cn": "🧹 透明垃圾袋"
  },
  "Loại cần câu:": {
    "en": "Fishing rod type:",
    "ja": "釣り竿の種類:",
    "cn": "鱼竿类型:"
  },
  "Thời Gian Bắt": {
    "en": "Catch Time",
    "ja": "キャッチタイム",
    "cn": "赶时间"
  },
  "0 phần thưởng": {
    "en": "0 rewards",
    "ja": "0 報酬",
    "cn": "0 奖励"
  },
  "🔵 Hiếm (Rare)": {
    "en": "🔵 Rare (Rare)",
    "ja": "🔵レア（レア）",
    "cn": "🔵 稀有（稀有）"
  },
  "HSD & Gia Hạn": {
    "en": "Expiration & Renewal",
    "ja": "有効期限と更新",
    "cn": "到期与续订"
  },
  "🔑 Yêu Cầu Mở:": {
    "en": "🔑 Open Request:",
    "ja": "🔑 オープンリクエスト:",
    "cn": "🔑 开放请求："
  },
  "Tải Danh Sách": {
    "en": "Download List",
    "ja": "ダウンロードリスト",
    "cn": "下载列表"
  },
  "🧹 Dọn Sạch Bể": {
    "en": "🧹 Clean the Tank",
    "ja": "🧹 タンクを掃除する",
    "cn": "🧹清洁水箱"
  },
  "❤️ Lượt Thích": {
    "en": "❤️ Likes",
    "ja": "❤️ いいね！",
    "cn": "❤️ 喜欢"
  },
  "+May mắn (%):": {
    "en": "+Luck (%):",
    "ja": "+運(%):",
    "cn": "+运气（%）："
  },
  "Buff Mồi (%):": {
    "en": "Bait Buff (%):",
    "ja": "餌バフ (%):",
    "cn": "诱饵增益 (%):"
  },
  "Điểm Tình Cảm": {
    "en": "Sentiment Score",
    "ja": "センチメントスコア",
    "cn": "情绪评分"
  },
  "⚠️ Reset Vườn": {
    "en": "⚠️ Reset the Garden",
    "ja": "⚠️ 庭をリセットする",
    "cn": "⚠️重置花园"
  },
  "🗺️ Khu Vực Mỏ": {
    "en": "🗺️ Mine Area",
    "ja": "🗺️鉱山エリア",
    "cn": "🗺️矿区"
  },
  "Thưởng Coins:": {
    "en": "Bonus Coins:",
    "ja": "ボーナスコイン:",
    "cn": "奖励金币："
  },
  "◀ Trang trước": {
    "en": "◀ Previous page",
    "ja": "◀ 前のページへ",
    "cn": "◀ 上一页"
  },
  "Loại vật phẩm": {
    "en": "Item type",
    "ja": "アイテムの種類",
    "cn": "物品类型"
  },
  "Độ bền tối đa": {
    "en": "Maximum durability",
    "ja": "最大の耐久性",
    "cn": "最大耐用性"
  },
  "📁 Tải Ảnh Lên": {
    "en": "📁 Upload Photos",
    "ja": "📁 写真をアップロードする",
    "cn": "📁 上传照片"
  },
  "— Không đặt —": {
    "en": "— Do not set —",
    "ja": "― 設定しないでください ―",
    "cn": "— 不设置 —"
  },
  "— Chưa chọn —": {
    "en": "— Not selected —",
    "ja": "— 未選択 —",
    "cn": "— 未选择 —"
  },
  "Chưa cấu hình": {
    "en": "Not configured yet",
    "ja": "まだ設定されていません",
    "cn": "尚未配置"
  },
  "Kênh tạm biệt": {
    "en": "Goodbye channel",
    "ja": "さようならチャンネル",
    "cn": "再见频道"
  },
  "✨ Khi vi phạm": {
    "en": "✨ When violating",
    "ja": "✨違反した場合",
    "cn": "✨ 违反时"
  },
  "Tỉ lệ caps %:": {
    "en": "Caps ratio %:",
    "ja": "キャップ率 %:",
    "cn": "上限比例%："
  },
  "bên cạnh tên.": {
    "en": "next to the name.",
    "ja": "名前の横にあります。",
    "cn": "名字旁边。"
  },
  "✈️ Đăng panel": {
    "en": "✈️ Post panels",
    "ja": "✈️ パネルを投稿する",
    "cn": "✈️ 帖子面板"
  },
  "Mật Khẩu RCON": {
    "en": "RCON Password",
    "ja": "RCONパスワード",
    "cn": "密码"
  },
  "Phiên bản: --": {
    "en": "Version: --",
    "ja": "バージョン: --",
    "cn": "版本：--"
  },
  "Chưa kiểm tra": {
    "en": "Not checked yet",
    "ja": "まだチェックされていません",
    "cn": "尚未检查"
  },
  "Kiểm tra file": {
    "en": "Check files",
    "ja": "ファイルをチェックする",
    "cn": "检查文件"
  },
  "Tên hiển thị:": {
    "en": "Display name:",
    "ja": "表示名:",
    "cn": "显示名称："
  },
  "Thành Tựu Của": {
    "en": "Achievements Of",
    "ja": "の業績",
    "cn": "的成就"
  },
  "⭐ hoặc :pepe:": {
    "en": "⭐ or :pepe:",
    "ja": "⭐ または :pepe:",
    "cn": "⭐ 或：佩佩："
  },
  "Ticket Hỗ trợ": {
    "en": "Support Tickets",
    "ja": "サポートチケット",
    "cn": "支持票"
  },
  "Máy Chủ & Bot": {
    "en": "Servers & Bots",
    "ja": "サーバーとボット",
    "cn": "服务器和机器人"
  },
  "💬 Hỗ trợ 24/7": {
    "en": "💬 24/7 support",
    "ja": "💬 年中無休のサポート",
    "cn": "💬 24/7 支持"
  },
  "Menu Lệnh Bot": {
    "en": "Bot Command Menu",
    "ja": "ボットコマンドメニュー",
    "cn": "机器人命令菜单"
  },
  "Tất Cả Server": {
    "en": "All Servers",
    "ja": "すべてのサーバー",
    "cn": "所有服务器"
  },
  "§m Gạch ngang": {
    "en": "§m Strikethrough",
    "ja": "§m 取り消し線",
    "cn": "§m 删除线"
  },
  "⬇️ Tải plugin": {
    "en": "⬇️ Download plugin",
    "ja": "⬇️ プラグインをダウンロード",
    "cn": "⬇️下载插件"
  },
  "cài đặt nhanh": {
    "en": "quick installation",
    "ja": "クイックインストール",
    "cn": "快速安装"
  },
  "Chủ tài khoản": {
    "en": "Account owner",
    "ja": "アカウント所有者",
    "cn": "账户所有者"
  },
  "Lời luận giải": {
    "en": "Commentary",
    "ja": "解説",
    "cn": "评论"
  },
  "Bằng việc mời": {
    "en": "By inviting",
    "ja": "招待することで",
    "cn": "通过邀请"
  },
  "Đã xảy ra lỗi": {
    "en": "An error has occurred",
    "ja": "エラーが発生しました",
    "cn": "发生错误"
  },
  "📝 Mô tả video": {
    "en": "📝 Video description",
    "ja": "📝 ビデオの説明",
    "cn": "📝 视频说明"
  },
  "👁️ Xem Trước": {
    "en": "👁️ Preview",
    "ja": "👁️ プレビュー",
    "cn": "👁️预览"
  },
  "Danh Mục Bio": {
    "en": "Bio Category",
    "ja": "バイオ部門",
    "cn": "生物类别"
  },
  "Cogs Đăng Ký": {
    "en": "Cogs Register",
    "ja": "コグレジスター",
    "cn": "齿轮寄存器"
  },
  "• Thời gian:": {
    "en": "• Time:",
    "ja": "• 時間:",
    "cn": "• 时间："
  },
  "Xóa tìm kiếm": {
    "en": "Clear search",
    "ja": "検索をクリア",
    "cn": "清除搜索"
  },
  "Nối Từ 2 chữ": {
    "en": "Connect 2 words",
    "ja": "2つの単語をつなげる",
    "cn": "连接2个字"
  },
  "🏆 BXH Cờ Vua": {
    "en": "🏆 Chess rankings",
    "ja": "🏆チェスランキング",
    "cn": "🏆 国际象棋排名"
  },
  "👑 Chủ phòng:": {
    "en": "👑 Room owner:",
    "ja": "👑 ルームオーナー:",
    "cn": "👑 房主："
  },
  "3 Từ (Chuẩn)": {
    "en": "3 Words (Standard)",
    "ja": "3ワード（標準）",
    "cn": "3 字（标准）"
  },
  "🏆 BXH Nối Từ": {
    "en": "🏆 Word Connection Chart",
    "ja": "🏆単語の接続表",
    "cn": "🏆 单词连接图"
  },
  "Hủy đính kèm": {
    "en": "Cancel attachment",
    "ja": "添付ファイルのキャンセル",
    "cn": "取消附件"
  },
  "Mở Dashboard": {
    "en": "Open Dashboard",
    "ja": "ダッシュボードを開く",
    "cn": "打开仪表板"
  },
  "s!play <bài>": {
    "en": "s!play <post>",
    "ja": "s!play <投稿>",
    "cn": "s!play <帖子>"
  },
  "Thư viện ảnh": {
    "en": "Photo gallery",
    "ja": "フォトギャラリー",
    "cn": "照片库"
  },
  "Tổng Máy Chủ": {
    "en": "Total Server",
    "ja": "トータルサーバー",
    "cn": "总服务器数"
  },
  "Đang phục vụ": {
    "en": "In service",
    "ja": "サービス中",
    "cn": "服役中"
  },
  "🟡 Chờ (Idle)": {
    "en": "🟡 Wait (Idle)",
    "ja": "🟡 待機 (アイドル)",
    "cn": "🟡 等待（空闲）"
  },
  "Vừa kiểm tra": {
    "en": "Just checked",
    "ja": "たった今確認しました",
    "cn": "刚刚检查过"
  },
  "Khởi động: —": {
    "en": "Startup: —",
    "ja": "起動時: —",
    "cn": "启动：—"
  },
  "0 kênh voice": {
    "en": "0 voice channels",
    "ja": "0 音声チャンネル",
    "cn": "0个语音通道"
  },
  "🏦 Ngân Hàng:": {
    "en": "🏦 Bank:",
    "ja": "🏦銀行:",
    "cn": "🏦 银行："
  },
  "7:00 AM sáng": {
    "en": "7:00 AM am",
    "ja": "午前7時",
    "cn": "上午 7:00"
  },
  "🎲 Ngẫu Nhiên": {
    "en": "🎲 Random",
    "ja": "🎲ランダム",
    "cn": "🎲 随机"
  },
  "💎 Xu thưởng:": {
    "en": "💎 Bonus Coins:",
    "ja": "💎 ボーナスコイン:",
    "cn": "💎 奖励金币："
  },
  "🪱 Mồi Câu Cá": {
    "en": "🪱 Fishing Lure",
    "ja": "🪱 釣りルアー",
    "cn": "🪱 鱼饵"
  },
  "🔄 Làm Mới DS": {
    "en": "🔄 Refresh DS",
    "ja": "🔄 DSをリフレッシュ",
    "cn": "🔄 刷新DS"
  },
  "Tên Vật Phẩm": {
    "en": "Item Name",
    "ja": "項目名",
    "cn": "商品名称"
  },
  "Coin Tối Đa:": {
    "en": "Maximum Coins:",
    "ja": "最大コイン数:",
    "cn": "最大金币数："
  },
  "Phí gia hạn:": {
    "en": "Renewal fee:",
    "ja": "更新料:",
    "cn": "续订费用："
  },
  "🌱 Hạt giống:": {
    "en": "🌱 Seeds:",
    "ja": "🌱 種子:",
    "cn": "🌱 种子："
  },
  "• Phiên bản:": {
    "en": "• Version:",
    "ja": "• バージョン:",
    "cn": "• 版本："
  },
  "Tên hiển thị": {
    "en": "Display name",
    "ja": "表示名",
    "cn": "显示名称"
  },
  "Chọn Server:": {
    "en": "Select Server:",
    "ja": "サーバーを選択します:",
    "cn": "选择服务器："
  },
  "🎛️ Xem Tỉ Lệ": {
    "en": "🎛️ See Rate",
    "ja": "🎛️ 料金を見る",
    "cn": "🎛️ 查看价格"
  },
  "0 Thành Viên": {
    "en": "0 Members",
    "ja": "0 メンバー",
    "cn": "0 会员"
  },
  "= tên server": {
    "en": "= server name",
    "ja": "= サーバー名",
    "cn": "= 服务器名称"
  },
  "Timeout phút": {
    "en": "Timeout minutes",
    "ja": "タイムアウト分",
    "cn": "超时分钟数"
  },
  "🚫 Cấm global": {
    "en": "🚫 Ban globally",
    "ja": "🚫 世界的に禁止する",
    "cn": "🚫 全球禁止"
  },
  "Lưu thay đổi": {
    "en": "Save changes",
    "ja": "変更を保存する",
    "cn": "保存更改"
  },
  "Tiêu đề bảng": {
    "en": "Table title",
    "ja": "表のタイトル",
    "cn": "表标题"
  },
  "🔵 Xanh dương": {
    "en": "🔵 Blue",
    "ja": "🔵 ブルー",
    "cn": "🔵蓝色"
  },
  "Hủy Liên Kết": {
    "en": "Cancel Link",
    "ja": "リンクをキャンセル",
    "cn": "取消链接"
  },
  "Mô Tả Embed:": {
    "en": "Embed Description:",
    "ja": "埋め込み説明:",
    "cn": "嵌入说明："
  },
  "Đơn vị tiền:": {
    "en": "Currency unit:",
    "ja": "通貨単位:",
    "cn": "货币单位："
  },
  "Tên Cần Câu:": {
    "en": "Fishing Rod Name:",
    "ja": "釣り竿名:",
    "cn": "鱼竿名称："
  },
  "Thông báo...": {
    "en": "Notice...",
    "ja": "お知らせ...",
    "cn": "注意..."
  },
  "🎣 Câu Cá RPG": {
    "en": "🎣 Fishing RPG",
    "ja": "🎣 釣りRPG",
    "cn": "🎣 钓鱼角色扮演游戏"
  },
  "📜 Điều khoản": {
    "en": "📜 Terms",
    "ja": "📜規約",
    "cn": "📜 条款"
  },
  "Cần giúp đỡ?": {
    "en": "Need help?",
    "ja": "助けが必要ですか?",
    "cn": "需要帮助吗？"
  },
  "Gửi Vào Game": {
    "en": "Send to Game",
    "ja": "ゲームに送信",
    "cn": "发送至游戏"
  },
  "⚡ Toàn Quyền": {
    "en": "⚡ Full Authority",
    "ja": "⚡ 全権限",
    "cn": "⚡ 全权"
  },
  "§n Gạch chân": {
    "en": "§n Underline",
    "ja": "§n 下線",
    "cn": "§n 下划线"
  },
  "§b Aqua nhạt": {
    "en": "§b Light Aqua",
    "ja": "§b ライトアクア",
    "cn": "§b 浅水色"
  },
  "RAM Hệ Thống": {
    "en": "System RAM",
    "ja": "システムRAM",
    "cn": "系统内存"
  },
  "👤 Của Mình (": {
    "en": "👤 Mine (",
    "ja": "👤 わたしの（",
    "cn": "👤 我的（"
  },
  "Số tài khoản": {
    "en": "Account number",
    "ja": "口座番号",
    "cn": "帐号"
  },
  "/ Điều khoản": {
    "en": "/ Terms",
    "ja": "/ 規約",
    "cn": "/ 条款"
  },
  "Âm thanh gốc": {
    "en": "Original audio",
    "ja": "オリジナルオーディオ",
    "cn": "原声"
  },
  "Âm thanh nền": {
    "en": "Background sound",
    "ja": "背景音",
    "cn": "背景音"
  },
  "🎬 Chế độ rạp": {
    "en": "🎬 Theater mode",
    "ja": "🎬 シアターモード",
    "cn": "🎬 剧院模式"
  },
  "/ Tài khoản": {
    "en": "/Account",
    "ja": "/アカウント",
    "cn": "/账户"
  },
  "🏦 Ngân hàng": {
    "en": "🏦 Bank",
    "ja": "🏦銀行",
    "cn": "🏦 银行"
  },
  "🌾 Nông Trại": {
    "en": "🌾 Farm",
    "ja": "🌾 農場",
    "cn": "🌾 农场"
  },
  "+ Thêm Link": {
    "en": "+ Add Link",
    "ja": "+ リンクを追加",
    "cn": "+ 添加链接"
  },
  "Dòng/trang:": {
    "en": "Line/page:",
    "ja": "行/ページ:",
    "cn": "行/页："
  },
  "🟢 Hoạt động": {
    "en": "🟢 Activities",
    "ja": "🟢 アクティビティ",
    "cn": "🟢活动"
  },
  "Tạo tệp mới": {
    "en": "Create new file",
    "ja": "新しいファイルを作成する",
    "cn": "创建新文件"
  },
  "Tải lên tệp": {
    "en": "Upload files",
    "ja": "ファイルをアップロードする",
    "cn": "上传文件"
  },
  "Lọc dữ liệu": {
    "en": "Filter data",
    "ja": "データをフィルタリングする",
    "cn": "过滤数据"
  },
  "Trang trước": {
    "en": "Previous page",
    "ja": "前のページへ",
    "cn": "上一页"
  },
  "Chơi ngay →": {
    "en": "Play now →",
    "ja": "今すぐプレイ →",
    "cn": "立即播放 →"
  },
  "🤖 Vs AI Máy": {
    "en": "🤖 Vs AI Machine",
    "ja": "🤖 vs AIマシン",
    "cn": "🤖 与人工智能机器"
  },
  "Lượt: Trắng": {
    "en": "Hit: White",
    "ja": "ヒット：ホワイト",
    "cn": "命中：白"
  },
  "Top cao thủ": {
    "en": "Top players",
    "ja": "トッププレイヤー",
    "cn": "顶级球员"
  },
  "Xóa toàn bộ": {
    "en": "Delete all",
    "ja": "すべて削除",
    "cn": "全部删除"
  },
  "Từ hiện tại": {
    "en": "From the present",
    "ja": "現在から",
    "cn": "从现在开始"
  },
  "🔐 Đăng nhập": {
    "en": "🔐 Log in",
    "ja": "🔐 ログイン",
    "cn": "🔐 登录"
  },
  "tên_tệp.png": {
    "en": "file_name.png",
    "ja": "ファイル名.png",
    "cn": "文件名.png"
  },
  "/ Hướng dẫn": {
    "en": "/ Instructions",
    "ja": "/ 説明書",
    "cn": "/ 使用说明"
  },
  "Dùng prefix": {
    "en": "Use prefixes",
    "ja": "プレフィックスを使用する",
    "cn": "使用前缀"
  },
  "Độ Trễ Ping": {
    "en": "Ping Latency",
    "ja": "Ping 遅延",
    "cn": "Ping 延迟"
  },
  "🛡️ Quản Trị": {
    "en": "🛡️ Administration",
    "ja": "🛡️管理",
    "cn": "🛡️ 行政管理"
  },
  "⚙️ Tiện Ích": {
    "en": "⚙️ Utilities",
    "ja": "⚙️ 公共事業",
    "cn": "⚙️ 实用工具"
  },
  "Tổng Cá Bắt": {
    "en": "Total Fish Catch",
    "ja": "総漁獲量",
    "cn": "总渔获量"
  },
  "Phần Thưởng": {
    "en": "Rewards",
    "ja": "報酬",
    "cn": "奖励"
  },
  "📖 Bách Khoa": {
    "en": "📖 Bach Khoa",
    "ja": "📖 バックコア",
    "cn": "📖 巴赫科阿"
  },
  "📦 Tạo Rương": {
    "en": "📦 Create a Chest",
    "ja": "📦 チェストを作成する",
    "cn": "📦 创建一个箱子"
  },
  "Cấp Cần Câu": {
    "en": "Fishing Rod Level",
    "ja": "釣り竿レベル",
    "cn": "钓鱼竿水平仪"
  },
  "⭐ Linh vật:": {
    "en": "⭐ Mascot:",
    "ja": "⭐マスコット:",
    "cn": "⭐ 吉祥物："
  },
  "Hạn Sử Dụng": {
    "en": "Expiry date",
    "ja": "有効期限",
    "cn": "有效期"
  },
  "📦 Rương Báu": {
    "en": "📦 Treasure Chest",
    "ja": "📦 宝箱",
    "cn": "📦 宝箱"
  },
  "• Sức chứa:": {
    "en": "• Capacity:",
    "ja": "• 容量:",
    "cn": "• 容量："
  },
  "🌱 Hạt Giống": {
    "en": "🌱 Seeds",
    "ja": "🌱 種子",
    "cn": "🌱 种子"
  },
  "🔮 Túi đồ ẩn": {
    "en": "🔮 Hidden storage pockets",
    "ja": "🔮隠し収納ポケット",
    "cn": "🔮 隐藏式储物袋"
  },
  "🧬 Đột biến:": {
    "en": "🧬 Mutation:",
    "ja": "🧬 突然変異:",
    "cn": "🧬 突变："
  },
  "🚜 Đổi Ô Đất": {
    "en": "🚜 Change Land Plot",
    "ja": "🚜 土地区画を変更する",
    "cn": "🚜 改变土地"
  },
  "LV.1 THỢ MỎ": {
    "en": "LV.1 MINER",
    "ja": "LV.1 マイナー",
    "cn": "LV.1 矿工"
  },
  "⛏️ Cuốc Đào": {
    "en": "⛏️ Cuoc Dao",
    "ja": "⛏️クオック・ダオ",
    "cn": "⛏️ 措克道"
  },
  "🪙 Đổi Coins": {
    "en": "🪙 Exchange Coins",
    "ja": "🪙 コインを交換する",
    "cn": "🪙 兑换硬币"
  },
  "Lệnh nhanh:": {
    "en": "Quick command:",
    "ja": "クイックコマンド:",
    "cn": "快速命令："
  },
  "Đổi Sang MC": {
    "en": "Change to MC",
    "ja": "MCにチェンジ",
    "cn": "更改为MC"
  },
  "📜 Kênh Rule": {
    "en": "📜 Rule Channel",
    "ja": "📜ルールチャンネル",
    "cn": "📜 规则频道"
  },
  "📢 Thông báo": {
    "en": "📢 Notice",
    "ja": "📢 お知らせ",
    "cn": "📢 通知"
  },
  "Prefix lệnh": {
    "en": "Prefix command",
    "ja": "プレフィックスコマンド",
    "cn": "前缀命令"
  },
  "📌 Đã setup:": {
    "en": "📌 Already set up:",
    "ja": "📌 すでにセットアップされています:",
    "cn": "📌 已设置："
  },
  "Key có sẵn:": {
    "en": "Available keys:",
    "ja": "利用可能なキー:",
    "cn": "可用键："
  },
  "Kênh Trivia": {
    "en": "Trivia channel",
    "ja": "トリビアチャンネル",
    "cn": "问答频道"
  },
  "Kick - Đuổi": {
    "en": "Kick - Chase",
    "ja": "キック - チェイス",
    "cn": "踢-追"
  },
  "Phút (mute)": {
    "en": "Minutes (mute)",
    "ja": "分（ミュート）",
    "cn": "分钟（静音）"
  },
  "💾 Lưu Level": {
    "en": "💾 Save Level",
    "ja": "💾 レベルを保存",
    "cn": "💾 保存等级"
  },
  "➕ Thêm kênh": {
    "en": "➕ Add channels",
    "ja": "➕ チャンネルを追加する",
    "cn": "➕ 添加频道"
  },
  "Chế độ nhận": {
    "en": "Receive mode",
    "ja": "受信モード",
    "cn": "接收方式"
  },
  "đã trỏ tới:": {
    "en": "pointed to:",
    "ja": "指摘したのは：",
    "cn": "指出："
  },
  "🔓 Đăng Nhập": {
    "en": "🔓 Login",
    "ja": "🔓ログイン",
    "cn": "🔓 登录"
  },
  "Liên Kết MC": {
    "en": "MC Link",
    "ja": "MCリンク",
    "cn": "MC链接"
  },
  "⬇ Cuộn cuối": {
    "en": "⬇ Final roll",
    "ja": "⬇ 最終ロール",
    "cn": "⬇ 最后一卷"
  },
  "Thư Mục Mới": {
    "en": "New Folder",
    "ja": "新しいフォルダー",
    "cn": "新建文件夹"
  },
  "§k Nhảy chữ": {
    "en": "§k Jump words",
    "ja": "§k ジャンプワード",
    "cn": "§k 跳转单词"
  },
  "§3 Aqua đậm": {
    "en": "§3 Dark Aqua",
    "ja": "§3 ダークアクア",
    "cn": "§3 暗水色"
  },
  "§6 Vàng cam": {
    "en": "§6 Orange yellow",
    "ja": "§6 オレンジイエロー",
    "cn": "§6 橙黄色"
  },
  "§9 Lam nhạt": {
    "en": "§9 Light blue",
    "ja": "§9 ライトブルー",
    "cn": "§9 浅蓝色"
  },
  "§a Lục nhạt": {
    "en": "§a Light green",
    "ja": "§a ライトグリーン",
    "cn": "§a 浅绿色"
  },
  "§d Hồng tím": {
    "en": "§d Purple pink",
    "ja": "§d パープルピンク",
    "cn": "§d 紫粉色"
  },
  "Loại plugin": {
    "en": "Plugin type",
    "ja": "プラグインの種類",
    "cn": "插件类型"
  },
  "File tải về": {
    "en": "Download file",
    "ja": "ファイルをダウンロードする",
    "cn": "下载文件"
  },
  "vào thư mục": {
    "en": "into the folder",
    "ja": "フォルダに",
    "cn": "进入文件夹"
  },
  "⬇️ Tải ngay": {
    "en": "⬇️ Download now",
    "ja": "⬇️ 今すぐダウンロード",
    "cn": "⬇️立即下载"
  },
  "Đã xác minh": {
    "en": "Verified",
    "ja": "確認済み",
    "cn": "已验证"
  },
  "🏠 Trang Chủ": {
    "en": "🏠 Home page",
    "ja": "🏠ホームページ",
    "cn": "🏠 主页"
  },
  "➕ Tạo Hồ Sơ": {
    "en": "➕ Create Profile",
    "ja": "➕ プロファイルの作成",
    "cn": "➕ 创建个人资料"
  },
  "Lệnh & Docs": {
    "en": "Commands & Docs",
    "ja": "コマンドとドキュメント",
    "cn": "命令和文档"
  },
  "Mô tả video": {
    "en": "Video description",
    "ja": "ビデオの説明",
    "cn": "视频说明"
  },
  "🎬 Rạp chiếu": {
    "en": "🎬 Theaters",
    "ja": "🎬 劇場",
    "cn": "🎬 剧院"
  },
  "để chia sẻ.": {
    "en": "to share.",
    "ja": "共有するために。",
    "cn": "分享。"
  },
  "🪙 Ví Coins": {
    "en": "🪙 Coins Wallet",
    "ja": "🪙 コインウォレット",
    "cn": "🪙 硬币钱包"
  },
  "Số Ví MoMo": {
    "en": "MoMo Wallet Number",
    "ja": "MoMoウォレット番号",
    "cn": "MoMo 钱包号码"
  },
  "Tổng cộng:": {
    "en": "Total:",
    "ja": "合計:",
    "cn": "总计："
  },
  "Trạng Thái": {
    "en": "Status",
    "ja": "ステータス",
    "cn": "状态"
  },
  "⚪ Chưa nạp": {
    "en": "⚪ Not loaded yet",
    "ja": "⚪ まだロードされていません",
    "cn": "⚪ 尚未加载"
  },
  "Trang cuối": {
    "en": "Last page",
    "ja": "最後のページ",
    "cn": "最后一页"
  },
  "Thuật toán": {
    "en": "Algorithm",
    "ja": "アルゴリズム",
    "cn": "算法"
  },
  "↩ Hoàn tác": {
    "en": "↩ Undo",
    "ja": "↩ 元に戻す",
    "cn": "↩ 撤消"
  },
  "↻ Chơi lại": {
    "en": "↻ Play again",
    "ja": "↻ もう一度プレイする",
    "cn": "↻ 再玩一次"
  },
  "Lượt đánh:": {
    "en": "Hits:",
    "ja": "ヒット数:",
    "cn": "点击次数："
  },
  "CHỌN EMOJI": {
    "en": "CHOOSE EMOJI",
    "ja": "絵文字を選択してください",
    "cn": "选择表情符号"
  },
  "Chèn Emoji": {
    "en": "Insert Emoji",
    "ja": "絵文字の挿入",
    "cn": "插入表情符号"
  },
  "Mời Sakura": {
    "en": "Invite Sakura",
    "ja": "さくらを招待する",
    "cn": "邀请小樱"
  },
  "Điều khoản": {
    "en": "Terms",
    "ja": "規約",
    "cn": "条款"
  },
  "🔄 Nạp Cogs": {
    "en": "🔄 Recharge Cogs",
    "ja": "🔄 リチャージコグ",
    "cn": "🔄 为齿轮充电"
  },
  "BXH Câu Cá": {
    "en": "Fishing rankings",
    "ja": "釣りランキング",
    "cn": "钓鱼排名"
  },
  "🔍 Kiểm tra": {
    "en": "🔍 Check",
    "ja": "🔍チェック",
    "cn": "🔍检查"
  },
  "🎮 Giải Trí": {
    "en": "🎮 Entertainment",
    "ja": "🎮 エンターテイメント",
    "cn": "🎮 娱乐"
  },
  "Hành Động:": {
    "en": "Action:",
    "ja": "アクション:",
    "cn": "行动："
  },
  "🌍 Toàn Cục": {
    "en": "🌍 Whole Department",
    "ja": "🌍 部門全体",
    "cn": "🌍整个部门"
  },
  "Người Chơi": {
    "en": "Player",
    "ja": "プレーヤー",
    "cn": "玩家"
  },
  "Giá Coins:": {
    "en": "Coins Price:",
    "ja": "コイン価格:",
    "cn": "硬币价格："
  },
  "🔓 Mở tự do": {
    "en": "🔓 Open freely",
    "ja": "🔓自由にオープン",
    "cn": "🔓 自由开放"
  },
  "⭐ Linh Vật": {
    "en": "⭐ Mascot",
    "ja": "⭐マスコット",
    "cn": "⭐ 吉祥物"
  },
  "Loại tiền:": {
    "en": "Currency:",
    "ja": "通貨:",
    "cn": "货币："
  },
  "🥬 Hoa màu:": {
    "en": "🥬 Flower color:",
    "ja": "🥬 花の色:",
    "cn": "🥬花色："
  },
  "⭐ Bụi sao:": {
    "en": "⭐ Stardust:",
    "ja": "⭐スターダスト:",
    "cn": "⭐ 星尘："
  },
  "🦠 Mầm Bệnh": {
    "en": "🦠 Pathogens",
    "ja": "🦠 病原体",
    "cn": "🦠病原体"
  },
  "📅 Tuần này": {
    "en": "📅 This week",
    "ja": "📅 今週",
    "cn": "📅本周"
  },
  "❓ Trợ Giúp": {
    "en": "❓ Help",
    "ja": "❓ ヘルプ",
    "cn": "❓ 帮助"
  },
  "Người Dùng": {
    "en": "User",
    "ja": "ユーザー",
    "cn": "用户"
  },
  "Tiếng Việt": {
    "en": "Vietnamese",
    "ja": "ベトナム語",
    "cn": "越南语"
  },
  "(tùy chọn)": {
    "en": "(optional)",
    "ja": "(オプション)",
    "cn": "（可选）"
  },
  "Kênh boost": {
    "en": "Boost channel",
    "ja": "ブーストチャンネル",
    "cn": "升压通道"
  },
  "Kênh Chess": {
    "en": "Chess Channel",
    "ja": "チェスチャンネル",
    "cn": "国际象棋频道"
  },
  "Chống spam": {
    "en": "Anti-spam",
    "ja": "スパム対策",
    "cn": "反垃圾邮件"
  },
  "🔨 Lệnh Mod": {
    "en": "🔨 Mod command",
    "ja": "🔨 Modコマンド",
    "cn": "🔨 模组命令"
  },
  "Thành viên": {
    "en": "Member",
    "ja": "メンバー",
    "cn": "会员"
  },
  "🚀 Thực thi": {
    "en": "🚀 Execution",
    "ja": "🚀 実行",
    "cn": "🚀 执行"
  },
  "Đăng panel": {
    "en": "Post panels",
    "ja": "ポストパネル",
    "cn": "柱板"
  },
  "⚠️ Để biết": {
    "en": "⚠️ To know",
    "ja": "⚠️知ること",
    "cn": "⚠️要知道"
  },
  "🪙 Top Giàu": {
    "en": "🪙 Top Rich",
    "ja": "🪙 トップリッチ",
    "cn": "🪙 顶级富豪"
  },
  "➕ Thêm mốc": {
    "en": "➕ Add landmarks",
    "ja": "➕ ランドマークを追加する",
    "cn": "➕ 添加地标"
  },
  "🚀 Gửi ngay": {
    "en": "🚀 Send now",
    "ja": "🚀 今すぐ送信",
    "cn": "🚀 立即发送"
  },
  "Nối Server": {
    "en": "Connect Server",
    "ja": "サーバーに接続する",
    "cn": "连接服务器"
  },
  "Màu Embed:": {
    "en": "Embed Color:",
    "ja": "埋め込み色:",
    "cn": "嵌入颜色："
  },
  "Tiêu đề...": {
    "en": "Title...",
    "ja": "タイトル...",
    "cn": "标题..."
  },
  "Xóa bộ lọc": {
    "en": "Clear filter",
    "ja": "クリアフィルター",
    "cn": "清除过滤器"
  },
  "✨ Tiện Ích": {
    "en": "✨ Utilities",
    "ja": "✨ ユーティリティ",
    "cn": "✨ 实用工具"
  },
  "với Sakura": {
    "en": "with Sakura",
    "ja": "さくらと",
    "cn": "与樱花"
  },
  "Chính Thức": {
    "en": "Official",
    "ja": "公式",
    "cn": "官方"
  },
  "Điều Hướng": {
    "en": "Navigation",
    "ja": "ナビゲーション",
    "cn": "导航"
  },
  "💻 Mã nguồn": {
    "en": "💻 Source code",
    "ja": "💻ソースコード",
    "cn": "💻源代码"
  },
  "🛡️ Bảo mật": {
    "en": "🛡️ Security",
    "ja": "🛡️ セキュリティ",
    "cn": "🛡️安全"
  },
  "Tên Server": {
    "en": "Server name",
    "ja": "サーバー名",
    "cn": "服务器名称"
  },
  "Bật Server": {
    "en": "Turn on Server",
    "ja": "サーバーをオンにする",
    "cn": "打开服务器"
  },
  "Tắt Server": {
    "en": "Turn off the Server",
    "ja": "サーバーの電源をオフにする",
    "cn": "关闭服务器"
  },
  "Phân Quyền": {
    "en": "Separation of Powers",
    "ja": "三権分立",
    "cn": "权力分立"
  },
  "Tổng: 0 MB": {
    "en": "Total: 0 MB",
    "ja": "合計: 0 MB",
    "cn": "总计：0 MB"
  },
  "👁️ Chỉ Xem": {
    "en": "👁️ Just Watch",
    "ja": "👁️ 見てください",
    "cn": "👁️只需观看"
  },
  "§o Nghiêng": {
    "en": "§o Tilt",
    "ja": "§o 傾斜",
    "cn": "§o 倾斜"
  },
  "Khó (Hard)": {
    "en": "Hard",
    "ja": "ハード",
    "cn": "硬"
  },
  "§1 Lam đậm": {
    "en": "§1 Dark blue",
    "ja": "§1 ダークブルー",
    "cn": "§1 深蓝色"
  },
  "§2 Lục đậm": {
    "en": "§2 Dark green",
    "ja": "§2 ダークグリーン",
    "cn": "§2 深绿色"
  },
  "§5 Tím đậm": {
    "en": "§5 Dark purple",
    "ja": "§5 ダークパープル",
    "cn": "§5 深紫色"
  },
  "§8 Xám đậm": {
    "en": "§8 Dark gray",
    "ja": "§8 ダークグレー",
    "cn": "§8 深灰色"
  },
  "§c Đỏ nhạt": {
    "en": "§c Light red",
    "ja": "§c ライトレッド",
    "cn": "§c 浅红色"
  },
  "Tải plugin": {
    "en": "Download plugins",
    "ja": "プラグインをダウンロードする",
    "cn": "下载插件"
  },
  "🌟 Tất Cả (": {
    "en": "🌟 All (",
    "ja": "🌟全員（",
    "cn": "🌟全部（"
  },
  "Thông tin": {
    "en": "Information",
    "ja": "情報",
    "cn": "信息"
  },
  "Dùng lệnh": {
    "en": "Use command",
    "ja": "コマンドを使用する",
    "cn": "使用命令"
  },
  "🔄 Làm mới": {
    "en": "🔄 Refresh",
    "ja": "🔄リフレッシュ",
    "cn": "🔄 刷新"
  },
  "Xem Trước": {
    "en": "See Before",
    "ja": "前に見る",
    "cn": "参见之前"
  },
  "Hành Động": {
    "en": "Action",
    "ja": "アクション",
    "cn": "行动"
  },
  "🔄 Nạp lại": {
    "en": "🔄 Recharge",
    "ja": "🔄 リチャージ",
    "cn": "🔄 充电"
  },
  "Trang đầu": {
    "en": "Home page",
    "ja": "ホームページ",
    "cn": "主页"
  },
  "Xem bài →": {
    "en": "View article →",
    "ja": "記事を見る→",
    "cn": "查看文章→"
  },
  "🔓 Giải mã": {
    "en": "🔓 Decoding",
    "ja": "🔓 デコード",
    "cn": "🔓 解码"
  },
  "💌 Mời Bạn": {
    "en": "💌 We invite you",
    "ja": "💌 あなたを招待します",
    "cn": "💌我们邀请你"
  },
  "↻ Ván mới": {
    "en": "↻ New board",
    "ja": "↻ 新しいボード",
    "cn": "↻ 新板"
  },
  "⇅ Lật bàn": {
    "en": "⇅ Flip the table",
    "ja": "⇅ テーブルをひっくり返す",
    "cn": "⇅ 翻转桌子"
  },
  "Tẩy trắng": {
    "en": "Bleaching",
    "ja": "漂白",
    "cn": "漂白"
  },
  "＋ Mời Bot": {
    "en": "＋ Invite Bots",
    "ja": "＋ ボットを招待する",
    "cn": "＋ 邀请机器人"
  },
  "Phiên Bản": {
    "en": "Version",
    "ja": "バージョン",
    "cn": "版本"
  },
  "+ Mời bot": {
    "en": "+ Invite bots",
    "ja": "+ ボットを招待する",
    "cn": "+ 邀请机器人"
  },
  "🌸 Cốt Lõi": {
    "en": "🌸 Core",
    "ja": "🌸コア",
    "cn": "❤ 核心"
  },
  "💰 Kinh Tế": {
    "en": "💰 Economy",
    "ja": "💰 経済",
    "cn": "💰经济"
  },
  "🎵 Âm Nhạc": {
    "en": "🎵 Music",
    "ja": "🎵 音楽",
    "cn": "🎵 音乐"
  },
  "🚨 Bảo Mật": {
    "en": "🚨 Security",
    "ja": "🚨セキュリティ",
    "cn": "🚨 安全"
  },
  "Hoạt động": {
    "en": "Activities",
    "ja": "活動内容",
    "cn": "活动"
  },
  "Số Lượng:": {
    "en": "Quantity:",
    "ja": "数量:",
    "cn": "数量："
  },
  "🔄 Làm Mới": {
    "en": "🔄 Refresh",
    "ja": "🔄リフレッシュ",
    "cn": "🔄 刷新"
  },
  "🎒 Giỏ cá:": {
    "en": "🎒 Fish basket:",
    "ja": "🎒 魚かご:",
    "cn": "🎒 鱼篮："
  },
  "Cường Hóa": {
    "en": "Enhancement",
    "ja": "強化",
    "cn": "强化"
  },
  "Số lượng:": {
    "en": "Quantity:",
    "ja": "数量:",
    "cn": "数量："
  },
  "Lượt Dùng": {
    "en": "Number of Uses",
    "ja": "使用回数",
    "cn": "使用次数"
  },
  "🎣 Cần Câu": {
    "en": "🎣 Fishing rod",
    "ja": "🎣 釣り竿",
    "cn": "🎣 钓鱼竿"
  },
  "🪱 Mồi Câu": {
    "en": "🪱 Fishing Bait",
    "ja": "🪱 釣り餌",
    "cn": "🪱 鱼饵"
  },
  "Phân Loại": {
    "en": "Classification",
    "ja": "分類",
    "cn": "分类"
  },
  "Xem Bể Cá": {
    "en": "See Fish Tank",
    "ja": "水槽を見る",
    "cn": "查看鱼缸"
  },
  "Level mở:": {
    "en": "Open Level:",
    "ja": "オープンレベル:",
    "cn": "开放级别："
  },
  "Không cần": {
    "en": "No need",
    "ja": "必要ありません",
    "cn": "不需要"
  },
  "0 cặp đôi": {
    "en": "0 couples",
    "ja": "0 カップル",
    "cn": "0 情侣"
  },
  "Nhẫn Cưới": {
    "en": "Wedding Rings",
    "ja": "結婚指輪",
    "cn": "结婚戒指"
  },
  "Quỹ Chung": {
    "en": "General Fund",
    "ja": "一般基金",
    "cn": "普通基金"
  },
  "🐛 Sâu bọ:": {
    "en": "🐛 Pests:",
    "ja": "🐛害虫:",
    "cn": "🐛 害虫："
  },
  "Hiệu ứng:": {
    "en": "Effects:",
    "ja": "効果:",
    "cn": "效果："
  },
  "🥬 Hoa Màu": {
    "en": "🥬 Colored Flowers",
    "ja": "🥬 色とりどりの花",
    "cn": "🥬 彩色花朵"
  },
  "🔍 Tra Cứu": {
    "en": "🔍 Look Up",
    "ja": "🔍ルックアップ",
    "cn": "🔍 向上看"
  },
  "Tổng quan": {
    "en": "Overview",
    "ja": "概要",
    "cn": "概述"
  },
  "Kênh Rule": {
    "en": "Rule Channel",
    "ja": "ルールチャンネル",
    "cn": "规则通道"
  },
  "1-5 ký tự": {
    "en": "1-5 characters",
    "ja": "1～5文字",
    "cn": "1-5 个字符"
  },
  "＋ Thêm từ": {
    "en": "＋ Add words",
    "ja": "＋ 言葉を追加する",
    "cn": "＋ 添加文字"
  },
  "Chính xác": {
    "en": "Exactly",
    "ja": "まさに",
    "cn": "正是如此"
  },
  "Ban - Cấm": {
    "en": "Ban - Ban",
    "ja": "禁止 - 禁止",
    "cn": "班-班"
  },
  "“— Tắt —”": {
    "en": "“— Off —”",
    "ja": "「――オフ――」",
    "cn": "“——关——”"
  },
  "Vào / Rời": {
    "en": "Enter/Leave",
    "ja": "入退室",
    "cn": "进入/离开"
  },
  "Mốc Level": {
    "en": "Level landmark",
    "ja": "レベルランドマーク",
    "cn": "水平地标"
  },
  "Kiểu khớp": {
    "en": "Match type",
    "ja": "マッチタイプ",
    "cn": "比赛类型"
  },
  "Loại bảng": {
    "en": "Table type",
    "ja": "テーブルタイプ",
    "cn": "桌子类型"
  },
  "🟢 Xanh lá": {
    "en": "🟢 Green",
    "ja": "🟢 緑",
    "cn": "🟢绿色"
  },
  "🔄 Nạp Lại": {
    "en": "🔄 Reload",
    "ja": "🔄 リロード",
    "cn": "🔄 重新加载"
  },
  "Chọn Game": {
    "en": "Select Game",
    "ja": "ゲームを選択",
    "cn": "选择游戏"
  },
  "Đồng Linh": {
    "en": "Dong Linh",
    "ja": "ドン・リン",
    "cn": "东林"
  },
  "🤖 Mời Bot": {
    "en": "🤖 Invite Bot",
    "ja": "🤖 ボットを招待",
    "cn": "🤖 邀请机器人"
  },
  "Phiên bản": {
    "en": "Version",
    "ja": "バージョン",
    "cn": "版本"
  },
  "Ổ Đĩa: 0%": {
    "en": "Drive: 0%",
    "ja": "ドライブ: 0%",
    "cn": "驱动力：0%"
  },
  "Kim Cương": {
    "en": "Diamond",
    "ja": "ダイヤモンド",
    "cn": "钻石"
  },
  "Dễ (Easy)": {
    "en": "Easy (Easy)",
    "ja": "簡単 (簡単)",
    "cn": "简单（简单）"
  },
  "§4 Đỏ đậm": {
    "en": "§4 Dark red",
    "ja": "§4 ダークレッド",
    "cn": "§4 深红色"
  },
  "/ Bảo mật": {
    "en": "/Security",
    "ja": "/セキュリティ",
    "cn": "/安全"
  },
  "Chỉnh Sửa": {
    "en": "Edit",
    "ja": "編集",
    "cn": "编辑"
  },
  "Ngân hàng": {
    "en": "Bank",
    "ja": "銀行",
    "cn": "银行"
  },
  "Liên kết:": {
    "en": "Link:",
    "ja": "リンク:",
    "cn": "链接："
  },
  "✨ Rút bài": {
    "en": "✨ Draw cards",
    "ja": "✨ カードを引く",
    "cn": "✨抽卡"
  },
  "💡 Hỗ trợ:": {
    "en": "💡 Support:",
    "ja": "💡サポート:",
    "cn": "💡支持："
  },
  "Ảnh 1 / 1": {
    "en": "Photo 1 / 1",
    "ja": "写真1/1",
    "cn": "照片 1 / 1"
  },
  "Ngày tạo": {
    "en": "Creation date",
    "ja": "作成日",
    "cn": "创建日期"
  },
  "Độc thân": {
    "en": "Single",
    "ja": "シングル",
    "cn": "单人"
  },
  "🌟 Tất Cả": {
    "en": "🌟 All",
    "ja": "🌟すべて",
    "cn": "🌟全部"
  },
  "🎣 Câu Cá": {
    "en": "🎣 Fishing",
    "ja": "🎣 釣り",
    "cn": "🎣 钓鱼"
  },
  "📁 Tất Cả": {
    "en": "📁 All",
    "ja": "📁すべて",
    "cn": "📁 全部"
  },
  "Chia Đôi": {
    "en": "Split in Half",
    "ja": "半分に分割",
    "cn": "分成两半"
  },
  "◀️ Trước": {
    "en": "◀️ Before",
    "ja": "◀️前",
    "cn": "◀️之前"
  },
  "🔒 Mã hóa": {
    "en": "🔒 Encryption",
    "ja": "🔒 暗号化",
    "cn": "🔒 加密"
  },
  "/ Cờ Vua": {
    "en": "/ Chess",
    "ja": "/ チェス",
    "cn": "/ 国际象棋"
  },
  "Trắng đi": {
    "en": "Go white",
    "ja": "真っ白になれ",
    "cn": "变白"
  },
  "🎮 Phòng:": {
    "en": "🎮 Room:",
    "ja": "🎮部屋:",
    "cn": "🎮 房间："
  },
  "10 Người": {
    "en": "10 People",
    "ja": "10名",
    "cn": "10人"
  },
  "12 Người": {
    "en": "12 People",
    "ja": "12名",
    "cn": "12人"
  },
  "16 Người": {
    "en": "16 People",
    "ja": "16名",
    "cn": "16人"
  },
  "100 Giây": {
    "en": "100 Seconds",
    "ja": "100秒",
    "cn": "100秒"
  },
  "120 Giây": {
    "en": "120 Seconds",
    "ja": "120秒",
    "cn": "120秒"
  },
  "150 Giây": {
    "en": "150 Seconds",
    "ja": "150秒",
    "cn": "150秒"
  },
  "⚙️ Phòng": {
    "en": "⚙️ Room",
    "ja": "⚙️部屋",
    "cn": "⚙️房间"
  },
  "🪣 Đổ màu": {
    "en": "🪣 Color filling",
    "ja": "🪣 色の塗りつぶし",
    "cn": "🪣 颜色填充"
  },
  "/ Nối Từ": {
    "en": "/ Connect Words",
    "ja": "/ 言葉をつなぐ",
    "cn": "/ 连接单词"
  },
  "Sẵn sàng": {
    "en": "Ready",
    "ja": "準備完了",
    "cn": "准备好"
  },
  "Nhấn nút": {
    "en": "Press the button",
    "ja": "ボタンを押してください",
    "cn": "按下按钮"
  },
  "Mời ngay": {
    "en": "Invite now",
    "ja": "今すぐ招待する",
    "cn": "立即邀请"
  },
  "Kết nối:": {
    "en": "Connection:",
    "ja": "接続:",
    "cn": "连接："
  },
  "Cấu hình": {
    "en": "Configuration",
    "ja": "構成",
    "cn": "配置"
  },
  "Đang Bật": {
    "en": "On",
    "ja": "オン",
    "cn": "开"
  },
  "Danh Mục": {
    "en": "Category",
    "ja": "カテゴリ",
    "cn": "类别"
  },
  "Loài cá:": {
    "en": "Fish species:",
    "ja": "魚種:",
    "cn": "鱼种："
  },
  "Đột Biến": {
    "en": "Mutation",
    "ja": "突然変異",
    "cn": "突变"
  },
  "🌐 Tất Cả": {
    "en": "🌐 All",
    "ja": "🌐 すべて",
    "cn": "🌐全部"
  },
  "Độ hiếm:": {
    "en": "Rarity:",
    "ja": "レアリティ:",
    "cn": "稀有度："
  },
  "⚪ THƯỜNG": {
    "en": "⚪ NORMAL",
    "ja": "⚪ ノーマル",
    "cn": "⚪ 正常"
  },
  "Giá bán:": {
    "en": "Price:",
    "ja": "価格:",
    "cn": "价格："
  },
  "Vật Phẩm": {
    "en": "Items",
    "ja": "アイテム",
    "cn": "项目"
  },
  "May mắn:": {
    "en": "Luck:",
    "ja": "運:",
    "cn": "运气："
  },
  "🚜 Ô đất:": {
    "en": "🚜 Land plot:",
    "ja": "🚜 土地区画:",
    "cn": "🚜 地块："
  },
  "🐛 Sâu Bọ": {
    "en": "🐛 Insects",
    "ja": "🐛 昆虫",
    "cn": "🐛 昆虫"
  },
  "Quản Trị": {
    "en": "Administration",
    "ja": "管理",
    "cn": "行政管理"
  },
  "🚫 Từ cấm": {
    "en": "🚫 Forbidden words",
    "ja": "🚫禁止用語",
    "cn": "🚫 禁忌词"
  },
  "Cảnh cáo": {
    "en": "Warning",
    "ja": "警告",
    "cn": "警告"
  },
  "toàn cục": {
    "en": "overall",
    "ja": "全体的に",
    "cn": "整体"
  },
  "Tin nhắn": {
    "en": "Messages",
    "ja": "メッセージ",
    "cn": "留言"
  },
  "“bởi ai”": {
    "en": "“by whom”",
    "ja": "「誰によって」",
    "cn": "“由谁”"
  },
  "Nội dung": {
    "en": "Content",
    "ja": "内容",
    "cn": "内容"
  },
  "Cặp Đôi:": {
    "en": "Couple:",
    "ja": "カップル:",
    "cn": "情侣："
  },
  "Máy chủ:": {
    "en": "Server:",
    "ja": "サーバー:",
    "cn": "服务器："
  },
  "Thao Tác": {
    "en": "Operation",
    "ja": "操作",
    "cn": "操作"
  },
  "§f Trắng": {
    "en": "§f White",
    "ja": "§f ホワイト",
    "cn": "§f 白色"
  },
  "Sao Chép": {
    "en": "Copy",
    "ja": "コピー",
    "cn": "复制"
  },
  "Tên mới": {
    "en": "New name",
    "ja": "新しい名前",
    "cn": "新名称"
  },
  "Làm mới": {
    "en": "Refresh",
    "ja": "リフレッシュ",
    "cn": "刷新"
  },
  "Tab Mới": {
    "en": "New Tab",
    "ja": "新しいタブ",
    "cn": "新标签"
  },
  "Tiếp ▶️": {
    "en": "Next ▶️",
    "ja": "次へ ▶️",
    "cn": "下一页▶️"
  },
  "Số Lệnh": {
    "en": "Order Number",
    "ja": "注文番号",
    "cn": "订单号"
  },
  "Kết quả": {
    "en": "Results",
    "ja": "結果",
    "cn": "结果"
  },
  "✕ Thoát": {
    "en": "✕ Exit",
    "ja": "✕ 終了",
    "cn": "✕ 退出"
  },
  "2 Người": {
    "en": "2 People",
    "ja": "2名",
    "cn": "2人"
  },
  "4 Người": {
    "en": "4 People",
    "ja": "4人",
    "cn": "4人"
  },
  "6 Người": {
    "en": "6 People",
    "ja": "6名",
    "cn": "6人"
  },
  "45 Giây": {
    "en": "45 Seconds",
    "ja": "45秒",
    "cn": "45秒"
  },
  "60 Giây": {
    "en": "60 Seconds",
    "ja": "60秒",
    "cn": "60秒"
  },
  "10 Vòng": {
    "en": "10 Rounds",
    "ja": "10ラウンド",
    "cn": "10轮"
  },
  "1 Ký tự": {
    "en": "1 Character",
    "ja": "1キャラクター",
    "cn": "1 个字符"
  },
  "2 Ký tự": {
    "en": "2 Characters",
    "ja": "2文字",
    "cn": "2 个角色"
  },
  "3 Ký tự": {
    "en": "3 Characters",
    "ja": "3 キャラクター",
    "cn": "3 个角色"
  },
  "CON MÈO": {
    "en": "CAT",
    "ja": "猫",
    "cn": "计算机辅助翻译"
  },
  "Tự chơi": {
    "en": "Play by yourself",
    "ja": "自分で遊ぶ",
    "cn": "自己玩"
  },
  "Điểm: 0": {
    "en": "Score: 0",
    "ja": "スコア: 0",
    "cn": "得分：0"
  },
  "Ván mới": {
    "en": "New board",
    "ja": "新しいボード",
    "cn": "新板"
  },
  "Bảo mật": {
    "en": "Security",
    "ja": "セキュリティ",
    "cn": "安全性"
  },
  "Mời bot": {
    "en": "Invite bots",
    "ja": "ボットを招待する",
    "cn": "邀请机器人"
  },
  "Cần Thủ": {
    "en": "Can Thu",
    "ja": "カン・トゥー",
    "cn": "芹周四"
  },
  "0 người": {
    "en": "0 people",
    "ja": "0人",
    "cn": "0 人"
  },
  "Tra Cứu": {
    "en": "Look Up",
    "ja": "ルックアップ",
    "cn": "查找"
  },
  "Giá Bán": {
    "en": "Selling Price",
    "ja": "販売価格",
    "cn": "售价"
  },
  "Giá Trị": {
    "en": "Value",
    "ja": "値",
    "cn": "价值"
  },
  "Tên Cần": {
    "en": "Name Can",
    "ja": "名前缶",
    "cn": "姓名 可以"
  },
  "May Mắn": {
    "en": "Lucky",
    "ja": "ラッキー",
    "cn": "幸运儿"
  },
  "Mã Code": {
    "en": "Code Code",
    "ja": "コード コード",
    "cn": "代码 代码"
  },
  "0 / 6 ô": {
    "en": "0 / 6 cells",
    "ja": "0 / 6 セル",
    "cn": "0 / 6 细胞"
  },
  "Độ bền:": {
    "en": "Durability:",
    "ja": "耐久性:",
    "cn": "耐用性："
  },
  "cặp đôi": {
    "en": "couple",
    "ja": "カップル",
    "cn": "情侣"
  },
  "Thêm Từ": {
    "en": "Add Words",
    "ja": "言葉を追加する",
    "cn": "添加单词"
  },
  "Điểm Số": {
    "en": "Score",
    "ja": "スコア",
    "cn": "分数"
  },
  "Độ hiếm": {
    "en": "Rarity",
    "ja": "レアリティ",
    "cn": "稀有度"
  },
  "Kênh XO": {
    "en": "XO Channel",
    "ja": "XOチャンネル",
    "cn": "XO频道"
  },
  "Chứa từ": {
    "en": "Contains words",
    "ja": "単語が含まれています",
    "cn": "包含单词"
  },
  "Số warn": {
    "en": "Number of warnings",
    "ja": "警告の数",
    "cn": "警告次数"
  },
  "— Tắt —": {
    "en": "— Off —",
    "ja": "— オフ —",
    "cn": "— 关闭 —"
  },
  "Vai trò": {
    "en": "Role",
    "ja": "役割",
    "cn": "角色"
  },
  "Màu nút": {
    "en": "Button color",
    "ja": "ボタンの色",
    "cn": "按钮颜色"
  },
  "Tự động": {
    "en": "Automatically",
    "ja": "自動的に",
    "cn": "自动"
  },
  "dễ dàng": {
    "en": "easy",
    "ja": "簡単な",
    "cn": "容易"
  },
  "Máy Chủ": {
    "en": "Server",
    "ja": "サーバー",
    "cn": "服务器"
  },
  "Quản Lý": {
    "en": "Management",
    "ja": "管理",
    "cn": "管理"
  },
  "Tệp Mới": {
    "en": "New File",
    "ja": "新しいファイル",
    "cn": "新文件"
  },
  "Tải Lên": {
    "en": "Upload",
    "ja": "アップロード",
    "cn": "上传"
  },
  "Tải Lại": {
    "en": "Reload",
    "ja": "リロード",
    "cn": "重新加载"
  },
  "Vai Trò": {
    "en": "Role",
    "ja": "役割",
    "cn": "角色"
  },
  "§e Vàng": {
    "en": "§e Gold",
    "ja": "§e ゴールド",
    "cn": "§e 黄金"
  },
  "Vào mục": {
    "en": "Go to section",
    "ja": "セクションに移動",
    "cn": "转到部分"
  },
  "Liên Hệ": {
    "en": "Contact",
    "ja": "お問い合わせ",
    "cn": "联系方式"
  },
  "Chia Sẻ": {
    "en": "Share",
    "ja": "シェアする",
    "cn": "分享"
  },
  "Bạn vào": {
    "en": "You enter",
    "ja": "あなたが入力します",
    "cn": "你输入"
  },
  "Bản gốc": {
    "en": "Original",
    "ja": "オリジナル",
    "cn": "原创"
  },
  "JPG Gốc": {
    "en": "Original JPG",
    "ja": "オリジナルJPG",
    "cn": "原始JPG"
  },
  "Trọn bộ": {
    "en": "Complete set",
    "ja": "コンプリートセット",
    "cn": "全套"
  },
  "Hủy bỏ": {
    "en": "Cancel",
    "ja": "キャンセル",
    "cn": "取消"
  },
  "0 dòng": {
    "en": "0 lines",
    "ja": "0行",
    "cn": "0 行"
  },
  "2 Vòng": {
    "en": "2 Rounds",
    "ja": "2ラウンド",
    "cn": "2 轮"
  },
  "4 Vòng": {
    "en": "4 Rounds",
    "ja": "4ラウンド",
    "cn": "4轮"
  },
  "5 Vòng": {
    "en": "5 Rounds",
    "ja": "5ラウンド",
    "cn": "5轮"
  },
  "6 Vòng": {
    "en": "6 Rounds",
    "ja": "6ラウンド",
    "cn": "6轮"
  },
  "8 Vòng": {
    "en": "8 Rounds",
    "ja": "8ラウンド",
    "cn": "8轮"
  },
  "✏️ Bút": {
    "en": "✏️ Pen",
    "ja": "✏️ペン",
    "cn": "✏️笔"
  },
  "Bút vẽ": {
    "en": "Drawing pen",
    "ja": "描画ペン",
    "cn": "绘图笔"
  },
  "0 phút": {
    "en": "0 minutes",
    "ja": "0分",
    "cn": "0分钟"
  },
  "0 lệnh": {
    "en": "0 orders",
    "ja": "注文数0件",
    "cn": "0 订单"
  },
  ". Nhấn": {
    "en": ". Press",
    "ja": "。プレス",
    "cn": "。新闻"
  },
  "Tất Cả": {
    "en": "All",
    "ja": "すべて",
    "cn": "全部"
  },
  "Độ Bền": {
    "en": "Durability",
    "ja": "耐久性",
    "cn": "耐用性"
  },
  "Cá Mẫu": {
    "en": "Model Fish",
    "ja": "モデルフィッシュ",
    "cn": "模型鱼"
  },
  "Độ bền": {
    "en": "Durability",
    "ja": "耐久性",
    "cn": "耐用性"
  },
  "0 viên": {
    "en": "0 pills",
    "ja": "0錠",
    "cn": "0 粒"
  },
  "Cụm Từ": {
    "en": "Phrases",
    "ja": "フレーズ",
    "cn": "短语"
  },
  "Gợi ý:": {
    "en": "Suggestion:",
    "ja": "提案:",
    "cn": "建议："
  },
  "✕ Đóng": {
    "en": "✕ Close",
    "ja": "✕ 閉じる",
    "cn": "✕ 关闭"
  },
  "🗑️ Xóa": {
    "en": "🗑️ Delete",
    "ja": "🗑️削除",
    "cn": "🗑️删除"
  },
  "➕ Thêm": {
    "en": "➕ Add",
    "ja": "➕ 追加",
    "cn": "➕ 添加"
  },
  "Hỗ Trợ": {
    "en": "Support",
    "ja": "サポート",
    "cn": "支持"
  },
  "+ Thêm": {
    "en": "+ Add",
    "ja": "+追加",
    "cn": "+ 添加"
  },
  "§l Đậm": {
    "en": "§l Bold",
    "ja": "§l 太字",
    "cn": "§l 粗体"
  },
  "§0 Đen": {
    "en": "§0 Black",
    "ja": "§0 ブラック",
    "cn": "§0 黑色"
  },
  "§7 Xám": {
    "en": "§7 Gray",
    "ja": "§7 グレー",
    "cn": "§7 灰色"
  },
  "Tải về": {
    "en": "Download",
    "ja": "ダウンロード",
    "cn": "下载"
  },
  "Ủng hộ": {
    "en": "Support",
    "ja": "サポート",
    "cn": "支持"
  },
  "Hồ Sơ": {
    "en": "Profile",
    "ja": "プロフィール",
    "cn": "公司简介"
  },
  "Bảng:": {
    "en": "Table:",
    "ja": "表:",
    "cn": "表："
  },
  "Miệng": {
    "en": "Mouth",
    "ja": "口",
    "cn": "嘴"
  },
  "📋 Mời": {
    "en": "📋 Please",
    "ja": "📋お願いします",
    "cn": "📋请"
  },
  "🧹 Tẩy": {
    "en": "🧹 Eraser",
    "ja": "🧹 消しゴム",
    "cn": "🧹 橡皮擦"
  },
  "↻ Mới": {
    "en": "↻ New",
    "ja": "↻新規",
    "cn": "↻ 新"
  },
  "Mã ID": {
    "en": "ID code",
    "ja": "IDコード",
    "cn": "身份证号码"
  },
  "Tổng:": {
    "en": "Total:",
    "ja": "合計:",
    "cn": "总计："
  },
  "phút)": {
    "en": "minutes)",
    "ja": "分）",
    "cn": "分钟）"
  },
  "Lý do": {
    "en": "Reason",
    "ja": "理由",
    "cn": "原因"
  },
  "Lưu ý": {
    "en": "Note",
    "ja": "注記",
    "cn": "注意事项"
  },
  "⚪ Xám": {
    "en": "⚪ Gray",
    "ja": "⚪ グレー",
    "cn": "⚪ 灰色"
  },
  "Gửi ⏎": {
    "en": "Send ⏎",
    "ja": "送信 ⏎",
    "cn": "发送 ⏎"
  },
  "KHÔNG": {
    "en": "NO",
    "ja": "いいえ",
    "cn": "否"
  },
  "📋 Dán": {
    "en": "📋 Stickers",
    "ja": "📋 ステッカー",
    "cn": "📋 贴纸"
  },
  "Chuẩn": {
    "en": "Correct",
    "ja": "正しい",
    "cn": "正确"
  },
  "💾 Lưu": {
    "en": "💾 Save",
    "ja": "💾保存",
    "cn": "💾 保存"
  },
  "2 Từ": {
    "en": "2 Words",
    "ja": "2 単語",
    "cn": "2 字"
  },
  "4 Từ": {
    "en": "4 Words",
    "ja": "4 つの言葉",
    "cn": "4 字"
  },
  "5 Từ": {
    "en": "5 Words",
    "ja": "5つの言葉",
    "cn": "5 字"
  },
  "Vòng": {
    "en": "Round",
    "ja": "ラウンド",
    "cn": "圆形"
  },
  "Hòa:": {
    "en": "Draw:",
    "ja": "描画:",
    "cn": "绘制："
  },
  "Nhấn": {
    "en": "Press",
    "ja": "プレス",
    "cn": "新闻"
  },
  "Thêm": {
    "en": "Add",
    "ja": "追加",
    "cn": "添加"
  },
  "Hạng": {
    "en": "Class",
    "ja": "クラス",
    "cn": "班级"
  },
  "0 Bể": {
    "en": "0 Tank",
    "ja": "0タンク",
    "cn": "0 坦克"
  },
  "hoặc": {
    "en": "or",
    "ja": "または",
    "cn": "或"
  },
  "• Gõ": {
    "en": "• Type",
    "ja": "• タイプ",
    "cn": "• 类型"
  },
  "🔴 Đỏ": {
    "en": "🔴 Red",
    "ja": "🔴レッド",
    "cn": "🔴红色"
  },
  "Kênh": {
    "en": "Channel",
    "ja": "チャンネル",
    "cn": "频道"
  },
  "Tệp": {
    "en": "File",
    "ja": "ファイル",
    "cn": "文件"
  },
  "Mục": {
    "en": "Section",
    "ja": "セクション",
    "cn": "部分"
  },
  "Lọc": {
    "en": "Filter",
    "ja": "フィルター",
    "cn": "过滤器"
  },
  "Màu": {
    "en": "Color",
    "ja": "色",
    "cn": "颜色"
  },
  "Mắt": {
    "en": "Eyes",
    "ja": "目",
    "cn": "眼睛"
  },
  "Vào": {
    "en": "Enter",
    "ja": "入力してください",
    "cn": "输入"
  },
  "Mới": {
    "en": "New",
    "ja": "新しい",
    "cn": "新"
  },
  "4 Ô": {
    "en": "4 Oh",
    "ja": "4 ああ",
    "cn": "4 哦"
  },
  "Tìm": {
    "en": "Find",
    "ja": "探す",
    "cn": "查找"
  },
  "TẮT": {
    "en": "OFF",
    "ja": "オフ",
    "cn": "关闭"
  },
  "ảnh": {
    "en": "photo",
    "ja": "写真",
    "cn": "照片"
  },
  "Mã": {
    "en": "Code",
    "ja": "コード",
    "cn": "代码"
  },
  "từ": {
    "en": "word",
    "ja": "言葉",
    "cn": "词"
  },
  "ô)": {
    "en": "oh)",
    "ja": "ああ）",
    "cn": "哦）"
  },
  "Mở": {
    "en": "Open",
    "ja": "開く",
    "cn": "打开"
  },
  "Gateway Ping": {
    "en": "Gateway Ping",
    "ja": "応答速度",
    "cn": "网关 Ping"
  },
  "Uptime": {
    "en": "Uptime",
    "ja": "稼働時間",
    "cn": "正常运行时间"
  },
  "Tìm kiếm lệnh bot": {
    "en": "Search bot commands",
    "ja": "コマンドを検索",
    "cn": "搜索机器人命令"
  },
  "Đã sao chép": {
    "en": "Copied",
    "ja": "コピーしました",
    "cn": "已复制"
  },
  "Đang Xử Lý": {
    "en": "Processing",
    "ja": "処理中",
    "cn": "加工"
  },
  "Đang phân tích bài viết TikTok": {
    "en": "Analyzing TikTok post",
    "ja": "TikTok投稿を解析中",
    "cn": "分析 TikTok 帖子"
  },
  "Đang trích xuất luồng video chất lượng cao & dữ liệu album": {
    "en": "Extracting high quality video stream and album data",
    "ja": "高画質動画ストリームとアルバムデータを抽出中",
    "cn": "提取高质量视频流和专辑数据"
  },
  "Nhập lệnh console": {
    "en": "Enter console command",
    "ja": "コマンドを入力",
    "cn": "输入控制台命令"
  },
  "Chào mừng bạn trở lại": {
    "en": "Welcome back",
    "ja": "おかえりなさい！",
    "cn": "欢迎回来"
  },
  "Quên mật khẩu": {
    "en": "Forgot password",
    "ja": "パスワードをお忘れですか？",
    "cn": "忘记密码"
  },
  "Chưa có tài khoản": {
    "en": "Don't have an account",
    "ja": "アカウントをお持ちでないですか？",
    "cn": "还没有帐户"
  },
  "Đã có tài khoản": {
    "en": "Already have an account",
    "ja": "すでにアカウントをお持ちですか？",
    "cn": "已有账户"
  },
  "Số trận thắng": {
    "en": "Wins",
    "ja": "勝利数",
    "cn": "获胜次数"
  },
  "Điểm số": {
    "en": "Score",
    "ja": "スコア",
    "cn": "分数"
  },
  "Đang chờ đối thủ": {
    "en": "Waiting for opponent",
    "ja": "対戦相手を待っています",
    "cn": "等待对手"
  },
  "Quản lý mã nguồn, cấu hình và cơ sở dữ liệu của Sakura Bot": {
    "en": "Manage source code, configurations, and databases of Sakura Bot",
    "ja": "Sakura Botのソースコード、設定、データベースを管理します。",
    "cn": "管理Sakura Bot的源代码、配置和数据库"
  },
  "Bản quyền © 2026 Sakura Bot. Bảo lưu mọi quyền": {
    "en": "Copyright © 2026 Sakura Bot. All rights reserved",
    "ja": "Copyright © 2026 Sakura Bot. All rights reserved",
    "cn": "版权所有 © 2026 樱花机器人。保留所有权利"
  },
  "Đang tải": {
    "en": "Loading",
    "ja": "読み込み中",
    "cn": "加载中"
  },
  "Vui lòng chờ": {
    "en": "Please wait",
    "ja": "少々お待ちください",
    "cn": "请稍候"
  },
  "Sakura Bot được cung cấp trên nguyên tắc \"nguyên trạng\" (As-Is). Chúng tôi nỗ lực duy trì bot hoạt động ổn định 24/7 nhưng không chịu trách nhiệm cho bất kỳ tổn thất dữ liệu, thiệt hại máy chủ do người dùng tự cấu hình sai quyền hạn hoặc sự cố từ phía Discord": {
    "en": "Sakura Bot is provided on an \"as-is\" basis. We strive to keep the bot running stably 24/7 but are not liable for any data loss or server damage caused by user misconfiguration of permissions or issues on Discord's side",
    "ja": "Sakura Bot は「現状のまま」で提供されます。私たちはボットを24時間365日安定して動作させるよう努めていますが、ユーザーによる権限設定の誤りやDiscord側の問題によるデータ損失やサーバーへの損害については責任を負いません。",
    "cn": "Sakura Bot 按“原样”提供。我们努力保持机器人 24/7 稳定运行，但对于由于用户错误配置权限或 Discord 方面的问题而导致的任何数据丢失、服务器损坏不承担任何责任。"
  },
  "Chủ sở hữu Bot (Owner) và Quản trị viên Web luôn có toàn quyền tự động. Tại đây bạn có thể cấp quyền cho các thành viên Discord khác vào xem Console, gửi lệnh RCON, điều khiển nguồn máy chủ, quản lý tệp tin hoặc soi túi đồ người chơi": {
    "en": "The Bot Owner and Web Administrators always have full automatic permissions. Here, you can grant other Discord members permissions to view the Console, send RCON commands, control server power, manage files, or inspect player inventories",
    "ja": "ボットオーナーとWeb管理者には常に完全な権限が自動的に付与されます。ここでは、他のDiscordメンバーにコンソールの表示、RCONコマンドの送信、サーバー電源の制御、ファイルの管理、またはプレイヤーのインベントリ確認を許可できます。",
    "cn": "机器人所有者（Owner）和 Web 管理员始终自动拥有完全权限。在这里，您可以授予其他 Discord 成员查看控制台、发送 RCON 命令、控制服务器电源、管理文件或查看玩家库存的权限。"
  },
  "Nếu từ custom đủ nhiều (≥ số từ cần: số từ mỗi lượt × số người chơi × số vòng), hệ thống sẽ dùng 100% từ custom. Nếu thiếu, hệ thống tự động bù thêm từ từ điển chuẩn để đảm bảo trận đấu trọn vẹn không lặp lại": {
    "en": "If there are enough custom words (≥ required words: words per turn × number of players × number of rounds), the system will use 100% custom words. If insufficient, the system automatically supplements with standard dictionary words to ensure a complete, non-repeating game",
    "ja": "カスタム単語が十分にある場合（必要単語数以上：1ターンあたりの単語数 × プレイヤー数 × ラウンド数）、システムは100%カスタム単語を使用します。不足している場合は、標準辞書から自動的に単語を補完し、重複のない完全なゲームを保証します！",
    "cn": "如果自定义单词足够多（≥需要单词数：每回合单词数×玩家数量×回合数），系统将使用100%自定义单词。如果缺失，系统自动从标准词典中进行补偿，确保完整匹配不重复"
  },
  "Hệ thống hỗ trợ kết nối máy chủ Minecraft SMP và các dịch vụ thứ ba (YouTube, Spotify, Lavalink, Groq/Gemini AI). Việc sử dụng các dịch vụ liên kết phải tuân thủ quy định riêng của từng nền tảng tương ứng": {
    "en": "The system supports connecting to Minecraft SMP servers and third-party services (YouTube, Spotify, Lavalink, Groq/Gemini AI). The use of linked services must comply with the specific regulations of each respective platform",
    "ja": "システムはMinecraft SMPサーバーおよびサードパーティサービス（YouTube、Spotify、Lavalink、Groq/Gemini AI）への接続をサポートしています。リンクされたサービスの使用は、各プラットフォームの個別の規定に従う必要があります。",
    "cn": "该系统支持连接到 Minecraft SMP 服务器和第三方服务（YouTube、Spotify、Lavalink、Groq/Gemini AI）。使用链接服务必须遵守各平台的个别规定"
  },
  "Tự động phát hiện các server Minecraft có cài đặt SakuraBot Plugin. Nối server với Discord Guild (yêu cầu quyền Server Owner hoặc Administrator). Chat 2 chiều, điều khiển Console và đồng bộ Coins": {
    "en": "Automatically detect Minecraft servers with the SakuraBot Plugin installed. Connect the server to a Discord Guild (requires Server Owner or Administrator permissions). Two-way chat, Console control, and Coin synchronization",
    "ja": "SakuraBot Plugin がインストールされた Minecraft サーバーを自動的に検出します。サーバーを Discord ギルドに接続します（Server Owner または Administrator の権限が必要です）。双方向チャット、コンソール操作、Coins の同期。",
    "cn": "自动检测安装了 SakuraBot 插件的 Minecraft 服务器。将服务器连接到 Discord Guild（需要服务器所有者或管理员权限）。 2 方聊天、控制台控制和硬币同步"
  },
  "Tính năng cho phép bạn cài đặt các từ khóa tùy chỉnh. Khi thành viên nhắn tin chứa từ khóa đó trong server, bot sẽ tự động phản hồi lại bằng văn bản hoặc gửi file đính kèm đã tải lên": {
    "en": "This feature allows you to set custom keywords. When a member sends a message containing that keyword in the server, the bot will automatically respond with text or send an uploaded attachment",
    "ja": "この機能はカスタムキーワードを設定できるようにします。メンバーがサーバー内でそのキーワードを含むメッセージを送信すると、ボットは自動的にテキストで返信するか、アップロードされた添付ファイルを送信します！",
    "cn": "该功能允许您安装自定义关键字。当会员在服务器中发送包含该关键字的消息时，机器人将自动回复文本或发送上传的附件。"
  },
  "Sakura Plugin là giải pháp mở rộng cho máy chủ Minecraft, hỗ trợ các tính năng quản lý, kiếm tiền, nhiệm vụ, bảo vệ và trải nghiệm chơi game tốt hơn cho cộng đồng của bạn": {
    "en": "Sakura Plugin is an expansion solution for Minecraft servers, supporting management features, monetization, quests, protection, and a better gaming experience for your community",
    "ja": "Sakura PluginはMinecraftサーバー向けの拡張ソリューションで、管理機能、収益化、クエスト、保護、そしてコミュニティにより良いゲーム体験を提供します。",
    "cn": "Sakura Plugin 是 Minecraft 服务器的扩展解决方案，支持管理功能、货币化、任务、保护，并为您的社区提供更好的游戏体验"
  },
  "Cho thành viên gửi Confession (công khai hoặc ẩn danh). Bot đăng panel với 2 nút, tự tạo thread thảo luận cho mỗi confession. Có nhật ký kiểm duyệt để chống lạm dụng": {
    "en": "Allow members to submit Confessions (public or anonymous). The bot posts a panel with 2 buttons, automatically creating a discussion thread for each confession. There is an audit log to prevent abuse",
    "ja": "メンバーが告白（公開または匿名）を送信できるようにします。ボットは2つのボタン付きのパネルを投稿し、各告白ごとにディスカッションスレッドを自動生成します。乱用防止のために監査ログがあります。",
    "cn": "允许成员提交供词（公开或匿名）。该机器人发布一个带有 2 个按钮的面板，为每个忏悔创建一个讨论线程。有一个审核日志以防止滥用"
  },
  "nằm dưới mục Level. Tại đây bạn có thể chọn kênh chỉ định để câu cá, kênh nhận thông báo mã quà tặng (Giftcode), và bật/tắt cho phép câu cá ngoài kênh quy định": {
    "en": "Located under the Level section. Here you can select a specific channel for fishing, a channel to receive gift code notifications, and toggle allowing fishing outside the designated channel",
    "ja": "レベルセクションの下にあります。ここでは、釣り用に指定されたチャンネル、ギフトコード通知を受け取るチャンネルを選択し、指定されたチャンネル以外での釣りを許可するかどうかを切り替えることができます。",
    "cn": "位于级别部分下。在这里您可以选择指定的钓鱼渠道、接收礼品码通知（Giftcode）的渠道以及启用/禁用指定渠道之外的钓鱼。"
  },
  "Dán liên kết TikTok hoặc Douyin bất kỳ để xem trước video, chọn độ phân giải Full HD / SD, tải âm thanh MP3 hoặc trọn bộ album ảnh Slideshow chất lượng gốc": {
    "en": "Paste any TikTok or Douyin link to preview the video, choose Full HD / SD resolution, download MP3 audio or the full original-quality photo album slideshow",
    "ja": "任意のTikTokまたはDouyinリンクを貼り付けて動画をプレビューし、Full HD / SD解像度を選択し、MP3オーディオまたはオリジナル品質のフルフォトアルバムスライドショーをダウンロードします。",
    "cn": "粘贴任何 TikTok 或抖音链接来预览视频，选择全高清/标清分辨率，下载 MP3 音频或完整原始质量幻灯片相册"
  },
  "Sakura Bot cung cấp các công cụ hỗ trợ quản lý máy chủ, bảo mật AutoMod, cấp độ tương tác (Level), hệ thống Ticket và kết nối Minecraft SMP. Bạn cam kết": {
    "en": "Sakura Bot provides tools to support server management, AutoMod security, interaction levels (Level), Ticket system, and Minecraft SMP connection. You commit",
    "ja": "Sakura Botは、サーバー管理、AutoModセキュリティ、インタラクションレベル（Level）、チケットシステム、Minecraft SMP接続をサポートするツールを提供します。あなたは以下に同意します：",
    "cn": "Sakura Bot 提供的工具支持服务器管理、AutoMod 安全性、关卡交互（Level）、Ticket 系统和 Minecraft SMP 连接。你承诺"
  },
  "Khi Cấp Thành Tựu, người chơi sẽ tự động nhận toàn bộ phần thưởng Coins, Xu và Danh hiệu được cấu hình. Thu hồi sẽ xóa khỏi hồ sơ và danh hiệu của user": {
    "en": "When granting an Achievement, the player will automatically receive all configured rewards: Coins, Xu, and Titles. Revocation will remove them from the user's profile and titles",
    "ja": "実績が付与されると、プレイヤーは設定されたすべての報酬（Coins、Xu、称号）を自動的に受け取ります。取り消しは、ユーザーのプロフィールと称号からそれらを削除します。",
    "cn": "升级成就时，玩家将自动获得所有配置的金币、金币和头衔奖励。撤销将从用户的个人资料和头衔中删除"
  },
  "Bạn cần hỗ trợ cấu hình bot, báo cáo lỗi phát sinh hoặc đóng góp ý tưởng phát triển? Chúng tôi luôn lắng nghe và sẵn sàng đồng hành cùng bạn 24/7": {
    "en": "Do you need help configuring the bot, reporting any bugs, or contributing development ideas? We are always listening and ready to accompany you 24/7",
    "ja": "ボットの設定サポートや発生したバグの報告、開発アイデアの提供が必要ですか？私たちは常に耳を傾け、24時間365日あなたと共にサポートします！",
    "cn": "您是否需要帮助配置机器人、报告错误或贡献开发想法？我们始终倾听并准备好 24/7 陪伴您"
  },
  "Không sử dụng các tính năng của Bot (như AutoMod, Mod Commands) để gây tổn hại bất hợp pháp đến người dùng khác mà không có lý do chính đáng": {
    "en": "Do not use the Bot's features (such as AutoMod, Mod Commands) to cause illegal harm to other users without a legitimate reason",
    "ja": "Bot の機能（AutoMod、Mod Commands など）を正当な理由なく他のユーザーに違法な害を与えるために使用しないでください。",
    "cn": "无正当理由不得利用Bot功能（如AutoMod、Mod Commands）非法伤害其他用户。"
  },
  ": Đồng bộ cấu trúc mà không xóa kênh cũ (giữ nguyên tin nhắn). Nếu tắt Sync: bot sẽ dọn dẹp cấu trúc cũ để tạo mới hoàn toàn như lúc backup": {
    "en": "Synchronize the structure without deleting old channels (preserve messages). If Sync is turned off: the bot will clean up the old structure to create a completely new one as during backup",
    "ja": "古いチャンネルを削除せずに構造を同期します（メッセージを保持）。Sync をオフにすると、バックアップ時と同様に古い構造をクリーンアップして完全に新しいものを作成します。",
    "cn": "：同步结构而不删除旧通道（保持消息完整）。如果同步关闭：机器人将清理旧结构以创建一个全新的结构，就像备份时一样"
  },
  "Dưới đây là quy trình rõ ràng để bạn tải plugin, thêm vào server, kiểm tra cài đặt, và sử dụng các lệnh tiện ích ngay khi vào server": {
    "en": "Below is a clear process for you to download the plugin, add it to the server, check the installation, and use utility commands as soon as you join the server",
    "ja": "以下は、プラグインをダウンロードし、サーバーに追加し、インストールを確認し、サーバーに参加したらすぐにユーティリティコマンドを使用するための明確な手順です。",
    "cn": "下面是一个清晰的过程，供您下载插件，将其添加到服务器，检查设置，并在进入服务器时立即使用实用程序命令。"
  },
  "Khởi động lại server hoặc vào console rồi kiểm tra xem plugin đã load thành công chưa. Đảm bảo Java và Vault đang hoạt động đúng": {
    "en": "Restart the server or go to the console and check whether the plugin has loaded successfully. Ensure that Java and Vault are running correctly",
    "ja": "サーバーを再起動するかコンソールに入り、プラグインが正常にロードされたか確認してください。Java と Vault が正しく動作していることを確認してください。",
    "cn": "重启服务器或者到控制台查看插件是否加载成功。确保 Java 和 Vault 正常工作"
  },
  "Bot Discord đa năng với phong cách hoa anh đào anime. Tích hợp bảo mật AutoMod toàn diện, hệ thống âm nhạc chất lượng cao, cấp độ tương tác và tính năng câu cá RPG sống động": {
    "en": "Multipurpose Discord bot with anime cherry blossom style. Integrating comprehensive AutoMod security, high-quality music system, interactive levels and immersive RPG fishing features",
    "ja": "アニメ桜風の多目的Discordボット。包括的な AutoMod セキュリティ、高品質の音楽システム、インタラクティブなレベル、没入型 RPG フィッシング機能を統合します。",
    "cn": "具有动漫樱花风格的多用途 Discord 机器人。全面的 AutoMod 安全集成、高品质音乐系统、互动关卡和身临其境的 RPG 钓鱼功能"
  },
  "Sakura Bot giúp bạn quản lý server trong 30 giây: AutoMod chống raid/nuke/spam, Welcome, Level & Kinh tế, Ticket, Music 24/7. Tùy chỉnh trực quan qua web dashboard hiện đại": {
    "en": "Sakura Bot helps you manage the server in 30 seconds: AutoMod anti-raid/nuke/spam, Welcome, Level & Economy, Ticket, Music 24/7. Intuitive customization via modern web dashboard",
    "ja": "サクラボットは、AutoMod アンチレイド/ニューク/スパム、ウェルカム、レベルとエコノミー、チケット、音楽を 24 時間年中無休で 30 秒でサーバー管理するのに役立ちます。最新の Web ダッシュボードによる直感的なカスタマイズ。",
    "cn": "Sakura Bot 可帮助您在 30 秒内管理服务器：AutoMod 反袭击/核武器/垃圾邮件、欢迎、等级和经济、票务、音乐 24/7。通过现代网络仪表板进行直观定制"
  },
  "Khi đăng nhập qua Discord, tài khoản Owner (@linhxinh_dev) sẽ tự động nhận toàn quyền quản trị cao nhất và quản lý mọi server mà bot tham gia": {
    "en": "When logging in via Discord, the Owner account (@linhxinh_dev) will automatically receive full administrative rights and manage all servers that the bot participates in",
    "ja": "Discord 経由でログインすると、オーナー アカウント (@linhxinh_dev) は自動的に完全な管理権限を受け取り、ボットが参加するすべてのサーバーを管理します。",
    "cn": "通过 Discord 登录时，所有者帐户 (@linhxinh_dev) 将自动获得完整的管理权限并管理机器人参与的所有服务器。"
  },
  "Bảng nhiệm vụ ủy thác thương hội: Nhận và hoàn thành các đơn hàng thu mua nông sản, khoáng sản để nhận thưởng coin & danh vọng.": {
    "en": "Guild entrusted tasks table: Receive and complete orders to purchase agricultural products and minerals to receive coin rewards & fame.",
    "ja": "ギルド委託タスクテーブル: 農産物や鉱物を購入する注文を受け取り、完了して、コイン報酬と名声を受け取ります。",
    "cn": "公会委托任务表：接收并完成购买农产品、矿产的订单即可获得金币和声望奖励。"
  },
  "Bảng nhiệm vụ ủy thác thương hội: Nhận và hoàn thành các đơn hàng thu mua nông sản, khoáng sản để nhận thưởng coin & danh vọng": {
    "en": "Guild entrusted tasks table: Receive and complete orders to purchase agricultural products and minerals to receive coin rewards & fame",
    "ja": "ギルド委託タスクテーブル: 農産物や鉱物を購入する注文を受け取り、完了して、コイン報酬と名声を受け取ります。",
    "cn": "公会信任任务表：接收并完成购买农产品、矿产的订单即可获得金币和名誉奖励"
  },
  "Trước khi người chơi bắt đầu dùng, nên xác nhận server có đủ chuẩn bị như Vault, Permission và cấu hình cơ bản khớp với plugin": {
    "en": "Before players start using it, they should confirm that the server has enough preparations such as Vault, Permission, and basic configuration that matches the plugin",
    "ja": "プレイヤーは使用を開始する前に、サーバーに Vault、権限、プラグインに一致する基本構成などの十分な準備が整っていることを確認する必要があります。",
    "cn": "玩家在开始使用之前，应确认服务器有足够的准备工作，如Vault、权限以及与插件匹配的基本配置。"
  },
  "Số dư Coins và Xu của người dùng được quản lý an toàn và đồng bộ độc lập, không cho phép chỉnh sửa trực tiếp từ Bảng Xếp Hạng": {
    "en": "User balances of Coins and Coins are managed securely and synchronized independently, with no direct editing allowed from the Leaderboard",
    "ja": "コインとコインのユーザー残高は安全に管理され、個別に同期され、リーダーボードから直接編集することはできません。",
    "cn": "用户的金币和金币余额安全管理并独立同步，不允许从排行榜直接编辑"
  },
  "Nhập Discord User ID phía trên hoặc chọn một cần thủ từ danh sách bảng xếp hạng bên dưới để ngắm bể cá và thao tác quản trị": {
    "en": "Enter the Discord User ID above or select an angler from the leaderboard list below to view the fish tank and operate the admin",
    "ja": "上に Discord ユーザー ID を入力するか、下のリーダーボード リストから釣り人を選択して水槽を表示し、管理者を操作します。",
    "cn": "输入上面的 Discord 用户 ID 或从下面的排行榜列表中选择钓鱼者来查看水族馆并管理管理操作。"
  },
  "Nếu bạn không đồng ý với bất kỳ phần nào của các điều khoản này, vui lòng ngừng sử dụng Bot và xóa Bot khỏi máy chủ của bạn": {
    "en": "If you do not agree with any part of these terms, please stop using the Bot and remove the Bot from your server",
    "ja": "これらの規約の一部でも同意できない場合は、ボットの使用を中止し、サーバーからボットを削除してください。",
    "cn": "如果您不同意这些条款的任何部分，请停止使用机器人并从您的服务器中删除机器人"
  },
  "để đồng bộ tiến độ và tự động nhận thưởng Coins / Xu khi chơi minigame! Dưới đây là danh mục toàn bộ thành tựu của bot": {
    "en": "to synchronize progress and automatically receive Coins / Coins rewards when playing minigames! Below is the complete catalog of the bot's achievements",
    "ja": "ミニゲームをプレイするときに進行状況を同期し、コイン/コイン報酬を自動的に受け取ります!以下はボットの成果の完全なカタログです。",
    "cn": "玩小游戏时同步进度并自动获得金币/金币奖励！以下是机器人成就的完整目录"
  },
  "Thiết kế trang bio cá nhân hiện đại với giao diện tùy biến, hình nền, màu sắc tương tác và sắp xếp các khối theo ý bạn": {
    "en": "Design a modern personal bio page with customizable interface, backgrounds, interactive colors and block arrangements as you like",
    "ja": "カスタマイズ可能なインターフェイス、背景、インタラクティブな色、ブロックの配置を自由に使用して、モダンな個人の自己紹介ページをデザインします。",
    "cn": "根据您的喜好设计具有可定制界面、背景、交互式颜色和块排列的现代个人简介页面"
  },
  "Sakura TikTok Downloader • Phát triển bởi SakuraBot Team 🌸 • Không lưu trữ bất kỳ video nào trên máy chủ của chúng tôi": {
    "en": "Sakura TikTok Downloader • Developed by SakuraBot Team 🌸 • Does not host any videos on our server",
    "ja": "さくら TikTok ダウンローダー • さくらボット チームによって開発されました 🌸 • 当社のサーバー上でビデオをホストしません。",
    "cn": "Sakura TikTok Downloader • 由 SakuraBot 团队开发 ♡ • 不在我们的服务器上托管任何视频"
  },
  "Trang tổng hợp hồ sơ liên kết cá nhân của cộng đồng Sakura Bot. Tạo trang bio đẹp mắt của riêng bạn chỉ trong 30 giây": {
    "en": "Page summarizing the personal link profiles of the Sakura Bot community. Create your own beautiful bio page in just 30 seconds",
    "ja": "さくらボットコミュニティの個人リンクプロフィールをまとめたページ。たった 30 秒で自分だけの美しい自己紹介ページを作成できます。",
    "cn": "总结 Sakura Bot 社区个人链接配置文件的页面。只需 30 秒即可创建您自己的精美个人简介页面"
  },
  "Quản lý danh mục vật phẩm trong shop bot, cập nhật giá Coins/Xu, chỉnh sửa thuộc tính, ẩn/hiện hoặc tạo trang bị mới": {
    "en": "Manage the item list in the bot shop, update Coins/Coins prices, edit attributes, hide/show or create new equipment",
    "ja": "ボットショップのアイテムリストの管理、コイン/コインの価格の更新、属性の編集、非表示/表示、または新しい装備の作成を行います。",
    "cn": "管理机器人商店中的物品列表，更新金币/金币价格，编辑属性，隐藏/显示或创建新装备"
  },
  "Xem toàn bộ vật phẩm trong cửa hàng bot, điều chỉnh giá Coins/Xu, chỉnh sửa thuộc tính và bật/tắt hiển thị (ẩn/hiện)": {
    "en": "View all items in the bot shop, adjust Coins/Coins prices, edit properties and enable/disable display (hide/show)",
    "ja": "ボットショップのすべてのアイテムを表示し、コイン/コインの価格を調整し、プロパティを編集し、表示を有効/無効にします (非表示/表示)。",
    "cn": "查看机器人商店中的所有物品，调整金币/金币价格，编辑属性以及启用/禁用显示（隐藏/显示）"
  },
  "Theo dõi danh sách các cuộc hôn nhân, nhẫn cưới, điểm tình cảm, quỹ chung và can thiệp giải trừ ly hôn khi cần thiết": {
    "en": "Monitor the list of marriages, wedding rings, affection points, joint funds and intervene in divorce dissolution when necessary",
    "ja": "結婚、結婚指輪、愛情ポイント、共同資金のリストを監視し、必要に応じて離婚の解消に介入します。",
    "cn": "监控婚姻清单、婚戒、感情点、共同资金，必要时介入离婚解除。"
  },
  "Xem các cuộc hôn nhân đang có trên Discord, tiến độ tình cảm, quỹ chung, chỉnh sửa thông tin hoặc giải trừ (ly hôn)": {
    "en": "View existing marriages on Discord, love progress, joint funds, edit information or dissolve (divorce)",
    "ja": "Discord で既存の結婚生活、恋愛の進行状況、共同資金を表示し、情報を編集したり、解消 (離婚) したりできます。",
    "cn": "查看 Discord 上的现有婚姻、关系进展、共同资金、编辑信息或解散（离婚）"
  },
  "Quản trị hệ thống Anti-XRay ẩn quặng và bảo vệ rương khỏi gian lận (Hỗ trợ 3 cấp độ bảo vệ chống X-Ray mod/pack).": {
    "en": "Anti-XRay system admin hides ores and protects chests from cheats (Supports 3 levels of anti-X-Ray protection mod/pack).",
    "ja": "対 X 線システム管理者は鉱石を隠し、チェストをチートから保護します (3 レベルの対 X 線保護 MOD/パックをサポート)。",
    "cn": "抗 X 射线系统管理员隐藏矿石并保护箱子免受作弊（支持 3 级抗 X 射线保护模块/包）。"
  },
  "Quản trị hệ thống Anti-XRay ẩn quặng và bảo vệ rương khỏi gian lận (Hỗ trợ 3 cấp độ bảo vệ chống X-Ray mod/pack)": {
    "en": "Anti-XRay system admin hides ores and protects chests from cheats (Supports 3 levels of anti-X-Ray protection mod/pack)",
    "ja": "対 X 線システム管理者は鉱石を隠し、チェストをチートから保護します (3 レベルの対 X 線保護 MOD/パックをサポート)。",
    "cn": "防X射线系统管理员隐藏矿石并保护箱子免受作弊（支持3级防X射线保护模块/包）"
  },
  "Xem lướt qua từng bức ảnh với giao diện mượt mà và tải toàn bộ bộ sưu tập ảnh dưới dạng file ZIP chỉ với 1 cú click": {
    "en": "Glance through each photo with a smooth interface and download the entire photo collection as a ZIP file with just 1 click",
    "ja": "スムーズなインターフェイスで各写真を確認し、1 回クリックするだけで写真コレクション全体を ZIP ファイルとしてダウンロードできます。",
    "cn": "通过流畅的界面浏览每张照片，只需单击一下即可将整个照片集下载为 ZIP 文件"
  },
  "Chọn tài khoản User và Server đích để cộng thêm, trừ bớt hoặc gán chính xác số dư Coin, Xu hoặc Tiền gửi Ngân Hàng": {
    "en": "Select the target User and Server account to add, subtract or assign the exact Coin, Coin or Bank Deposit balance",
    "ja": "ターゲットのユーザーとサーバーのアカウントを選択して、正確なコイン、コイン、または銀行預金残高を追加、減算、または割り当てます。",
    "cn": "选择目标用户和服务器帐户以添加、减去或分配确切的硬币、硬币或银行存款余额"
  },
  "Quản lý đất canh tác, hạt giống, hoa màu, sâu bọ, nông sản đột biến và điều khiển Mùa màng & Thời tiết nông nghiệp": {
    "en": "Manage arable land, seeds, crops, insects, mutant agricultural products and control Agricultural Crops & Weather",
    "ja": "耕地、種子、作物、昆虫、突然変異農産物を管理し、農作物と天候を制御します。",
    "cn": "管理耕地、种子、农作物、昆虫、突变农产品并控制农作物和天气"
  },
  "Tích hợp trí tuệ nhân tạo Minimax & Alpha-Beta Pruning 4 cấp độ. Chạm vào quân để chọn, chạm ô đích để di chuyển": {
    "en": "Integrated artificial intelligence Minimax & Alpha-Beta Pruning 4 levels. Touch the piece to select, touch the target square to move",
    "ja": "統合された人工知能 Minimax & Alpha-Beta Pruning 4 レベル。ピースをタッチして選択し、ターゲットのマスをタッチして移動します。",
    "cn": "集成人工智能 Minimax 和 Alpha-Beta 修剪 4 个级别。触摸棋子进行选择，触摸目标方格进行移动"
  },
  "Gửi một hộp quà Discord Nitro miễn phí giả mạo. Nạn nhân bấm vào sẽ bị troll phát âm thanh hoặc thông báo quê xệ": {
    "en": "Send a fake free Discord Nitro gift box. If the victim clicks on it, the troll will play a sound or a saggy message",
    "ja": "偽の無料 Discord Nitro ギフト ボックスを送信します。被害者がそれをクリックすると、トロールは音または垂れ下がったメッセージを再生します。",
    "cn": "发送一个假的免费 Discord Nitro 礼品盒。如果受害者点击它，巨魔会播放声音或下垂通知"
  },
  "Quyền Admin: Tạo, cấp phát và quản lý các trang bị tùy chỉnh, vũ khí đặc biệt có gắn hiệu ứng thuộc tính riêng.": {
    "en": "Admin rights: Create, allocate and manage custom equipment and special weapons with unique attribute effects.",
    "ja": "管理者権限: 独自の属性効果を持つカスタム装備や特別な武器を作成、割り当て、管理します。",
    "cn": "管理员权限：创建、分配和管理具有独特属性效果的自定义装备和特殊武器。"
  },
  "Quyền Admin: Tạo, cấp phát và quản lý các trang bị tùy chỉnh, vũ khí đặc biệt có gắn hiệu ứng thuộc tính riêng": {
    "en": "Admin rights: Create, allocate and manage custom equipment and special weapons with unique attribute effects",
    "ja": "管理者権限: 独自の属性効果を持つカスタム装備や特別な武器を作成、割り当て、管理します。",
    "cn": "管理员权限：创建、分配和管理具有独特属性效果的自定义装备和特殊武器"
  },
  "Yêu cầu xóa thông tin liên kết Minecraft hoặc đặt lại Level/Coins bằng cách liên hệ với Ban quản trị qua Discord": {
    "en": "Request removal of Minecraft link information or reset of Levels/Coins by contacting Admin via Discord",
    "ja": "Minecraft リンク情報の削除またはレベル/コインのリセットをリクエストするには、Discord 経由で管理者に連絡してください。",
    "cn": "通过 Discord 联系管理员，请求删除 Minecraft 链接信息或重置级别/硬币"
  },
  "Nếu bạn có bất kỳ câu hỏi hoặc thắc mắc nào liên quan đến Điều khoản Dịch vụ, vui lòng liên hệ với chúng tôi qua": {
    "en": "If you have any questions or concerns regarding the Terms of Service, please contact us via",
    "ja": "利用規約に関してご質問やご不明な点がございましたら、次の方法でお問い合わせください。",
    "cn": "如果您对服务条款有任何疑问或疑虑，请通过以下方式联系我们"
  },
  "Quản lý cuốc đào, cấp cường hóa (+150 & 20⭐), túi quặng người chơi, bách khoa khoáng sản và tạo trang bị custom": {
    "en": "Manage digging hoe, enhancement level (+150 & 20⭐), player ore bag, mineral encyclopedia and create custom equipment",
    "ja": "掘鍬、強化レベル (+150 & 20⭐)、プレイヤーの鉱石バッグ、鉱物図鑑を管理し、カスタム装備を作成します。",
    "cn": "管理挖掘机、等级增强（+150 和 20⭐）、玩家矿袋、矿物百科全书并创建自定义设备"
  },
  "Điều chỉnh tỉ lệ đập cuốc (+150 & 20⭐), sản lượng khoáng sản và tỉ lệ đột biến mỏ đá quý. Đồng bộ toàn hệ thống": {
    "en": "Adjusted pickaxe strike rate (+150 & 20⭐), mineral output and gem mine mutation rate. Synchronize the entire system",
    "ja": "つるはしの攻撃率 (+150 & 20⭐)、鉱物生産量、宝石鉱山の突然変異率を調整しました。システム全体を同期します。",
    "cn": "调整了镐命中率（+150 & 20⭐）、矿物产量和宝石矿变异率。同步整个系统"
  },
  "Mở hòm bán đồ nhanh tự động: Thả vật phẩm vào rương, hệ thống tự đối chiếu bảng giá Shop và cộng coin tức thì.": {
    "en": "Open the box to sell items automatically: Drop items into the chest, the system automatically compares the Shop price list and adds coins immediately.",
    "ja": "ボックスを開けてアイテムを自動的に販売します: アイテムをチェストにドロップすると、システムがショップの価格リストを自動的に比較し、すぐにコインを追加します。",
    "cn": "打开自动速卖箱：将物品放入宝箱，系统自动比对商店价目表并立即添加金币。"
  },
  "Mở hòm bán đồ nhanh tự động: Thả vật phẩm vào rương, hệ thống tự đối chiếu bảng giá Shop và cộng coin tức thì": {
    "en": "Open the box to sell items automatically: Drop items into the chest, the system automatically compares the Shop price list and adds coins immediately",
    "ja": "ボックスを開けてアイテムを自動的に販売します: アイテムをチェストにドロップすると、システムがショップの価格リストを自動的に比較し、すぐにコインを追加します。",
    "cn": "开箱自动售卖物品：将物品放入宝箱，系统自动比对商店价目表并立即添加金币"
  },
  "Mở cây kỹ năng & chỉ số nội tại RPG: Nâng cấp sức mạnh khai khoáng, chặt cây, chiến đấu, phòng thủ và hồi máu.": {
    "en": "Open RPG skill tree & internal stats: Upgrade mining power, tree cutting, combat, defense and healing.",
    "ja": "オープン RPG スキル ツリーと内部統計: 採掘力、木の伐採、戦闘、防御、治癒をアップグレードします。",
    "cn": "开放RPG技能树和内部统计数据：升级采矿能力、砍树、战斗、防御和治疗。"
  },
  "Mở cây kỹ năng & chỉ số nội tại RPG: Nâng cấp sức mạnh khai khoáng, chặt cây, chiến đấu, phòng thủ và hồi máu": {
    "en": "Open RPG skill tree & internal stats: Upgrade mining power, tree cutting, combat, defense and healing",
    "ja": "オープン RPG スキル ツリーと内部統計: 採掘力、木の伐採、戦闘、防御、治癒をアップグレードします。",
    "cn": "开放RPG技能树和内部统计数据：升级采矿能力、砍树、战斗、防御和治疗"
  },
  "Liên kết tài khoản Minecraft với Discord SakuraBot, kiểm tra trạng thái và chuyển đổi coins an toàn hai chiều.": {
    "en": "Link your Minecraft account with Discord SakuraBot, check status and securely convert coins two-way.",
    "ja": "Minecraft アカウントを Discord のサクラボットにリンクし、ステータスを確認し、コインを双方向で安全に変換します。",
    "cn": "将您的 Minecraft 帐户链接到 Discord SakuraBot，检查状态并安全地双向交换硬币。"
  },
  "Liên kết tài khoản Minecraft với Discord SakuraBot, kiểm tra trạng thái và chuyển đổi coins an toàn hai chiều": {
    "en": "Link your Minecraft account with Discord SakuraBot, check status and securely convert coins two-way",
    "ja": "Minecraft アカウントを Discord のサクラボットにリンクし、ステータスを確認し、コインを双方向で安全に変換します。",
    "cn": "将您的 Minecraft 帐户链接到 Discord SakuraBot，检查状态并安全地双向交换硬币"
  },
  "Đình chỉ hoặc chặn vĩnh viễn (Blacklist) bất kỳ người dùng hoặc máy chủ nào cố tình lạm dụng, phá hoại hệ thống": {
    "en": "Suspend or permanently block (Blacklist) any user or server who intentionally abuses or sabotages the system",
    "ja": "システムを意図的に悪用または妨害するユーザーまたはサーバーを停止または永久にブロック (ブラックリスト) します。",
    "cn": "暂停或永久阻止（列入黑名单）任何故意滥用或破坏系统的用户或服务器"
  },
  "Ngồi xuống mọi bề mặt block, bậc thang, ghế sofa hoặc chuyển đổi cho phép người chơi khác cõng/ngồi lên mình.": {
    "en": "Sit down on any block surface, step, sofa or switch allowing another player to carry/sit on you.",
    "ja": "ブロックの表面、ステップ、ソファ、またはスイッチに座り、他のプレイヤーが自分の上に乗ったり座ったりできるようにします。",
    "cn": "坐在任何可以让其他玩家背着/坐在你身上的方块表面、台阶、沙发或过渡处。"
  },
  "Ngồi xuống mọi bề mặt block, bậc thang, ghế sofa hoặc chuyển đổi cho phép người chơi khác cõng/ngồi lên mình": {
    "en": "Sit down on any block surface, step, sofa or switch allowing another player to carry/sit on you",
    "ja": "ブロックの表面、ステップ、ソファ、またはスイッチに座り、他のプレイヤーが自分の上に乗ったり座ったりできるようにします。",
    "cn": "坐在任何允许其他玩家背着/坐在你身上的方块表面、台阶、沙发或过渡处"
  },
  "và hệ thống Web Dashboard thu thập, sử dụng và bảo vệ thông tin của bạn khi bạn sử dụng dịch vụ của chúng tôi": {
    "en": "and the Web Dashboard system collects, uses and protects your information when you use our services",
    "ja": "また、Web ダッシュボード システムは、お客様が当社のサービスを使用する際にお客様の情報を収集、使用、保護します。",
    "cn": "当您使用我们的服务时，Web Dashboard 系统会收集、使用和保护您的信息"
  },
  "Mở Chợ Đen bí mật bán các nguyên liệu thần thoại và trang bị quý hiếm với số lượng giới hạn theo chu kỳ.": {
    "en": "Open a secret Black Market selling mythical ingredients and rare equipment in limited quantities periodically.",
    "ja": "秘密のブラックマーケットをオープンし、数量限定で神話の食材や珍しい装備を販売します。",
    "cn": "定期开设秘密黑市，出售限量的神秘原料和稀有装备。"
  },
  "Mở Chợ Đen bí mật bán các nguyên liệu thần thoại và trang bị quý hiếm với số lượng giới hạn theo chu kỳ": {
    "en": "Open a secret Black Market selling mythical ingredients and rare equipment in limited quantities periodically",
    "ja": "秘密のブラックマーケットをオープンし、数量限定で神話の食材や珍しい装備を販売します。",
    "cn": "开设秘密黑市，定期限量出售神话原料和稀有装备"
  },
  "Để vận hành các tính năng bot một cách trơn tru, Sakura Bot chỉ thu thập những thông tin cần thiết tối thiểu": {
    "en": "To operate bot features smoothly, Sakura Bot only collects the minimum necessary information",
    "ja": "さくらボットはボット機能をスムーズに動作させるために、必要最小限の情報のみを収集します。",
    "cn": "为了顺利操作机器人功能，Sakura Bot 仅收集最少的必要信息"
  },
  "Dùng để lưu trữ điểm kinh nghiệm (EXP), số dư Coins, Level cá nhân và danh sách liên kết tài khoản Minecraft": {
    "en": "Used to store experience points (EXP), Coins balance, personal Level and Minecraft account link list",
    "ja": "経験値 (EXP)、コイン残高、個人レベル、Minecraft アカウントのリンク リストを保存するために使用されます。",
    "cn": "用于存储经验值（EXP）、金币余额、个人等级和Minecraft帐户链接列表"
  },
  "Tùy biến tỉ lệ đập đồ (+1..+150), tiến sao (1..20 ⭐), may mắn câu cá & đào mỏ trực tiếp theo thời gian thực": {
    "en": "Customize loot rate (+1..+150), earn stars (1..20 ⭐), fishing & mining luck directly in real time",
    "ja": "略奪率 (+1..+150) をカスタマイズし、スター (1..20 ⭐) を獲得し、釣りと採掘の運をリアルタイムで直接カスタマイズします。",
    "cn": "自定义战利品率（+1..+150），赚取星星（1..20⭐），直接实时钓鱼和采矿运气"
  },
  "Không cố ý khai thác lỗi (bug/exploit), tấn công DoS/DDoS hoặc can thiệp vào máy chủ hạ tầng của Sakura Bot": {
    "en": "Do not intentionally exploit bugs/exploits, attack DoS/DDoS or interfere with Sakura Bot's infrastructure server",
    "ja": "意図的にバグやエクスプロイトを悪用したり、DoS/DDoS攻撃をしたり、さくらボットのインフラサーバーに干渉したりしないでください。",
    "cn": "不得故意利用错误/漏洞、攻击 DoS/DDoS 或干扰 Sakura Bot 的基础设施服务器"
  },
  "Sakura Bot sử dụng xác thực bảo mật trực tiếp qua Discord để tự động đồng bộ máy chủ bạn có quyền Quản lý": {
    "en": "Sakura Bot uses direct security authentication via Discord to automatically sync servers you have Admin rights to",
    "ja": "さくらボットは、Discord 経由の直接セキュリティ認証を使用して、管理者権限を持つサーバーを自動的に同期します。",
    "cn": "Sakura Bot 通过 Discord 使用直接安全身份验证来自动同步您拥有管理员权限的服务器"
  },
  "Bật cái nào cần — vi phạm sẽ bị xóa + cảnh cáo (đủ ngưỡng thì timeout). Mỗi mục có cài đặt riêng khi bật": {
    "en": "Turn on whichever you need — violations will be deleted + warning (timeout is enough). Each item has its own settings when enabled",
    "ja": "必要なものをオンにします。違反は削除され、警告が表示されます (タイムアウトで十分です)。有効にした場合、各項目には独自の設定があります。",
    "cn": "打开您需要的任何一个 - 违规行为将被删除+警告（超时就足够了）。每个项目在启用时都有自己的设置"
  },
  "Hỗ trợ 2 dòng và toàn bộ mã màu Minecraft (§0 - §f, §l, §o, v.v.). Nhấp vào ô màu bên dưới để chèn nhanh": {
    "en": "Supports 2 lines and the entire Minecraft color code (§0 - §f, §l, §o, etc.). Click the colored box below for quick insertion",
    "ja": "2 行と Minecraft カラー コード全体 (§0 - §f、§l、§o など) をサポートします。すぐに挿入するには、下の色付きのボックスをクリックします。",
    "cn": "支持 2 行和整个 Minecraft 颜色代码（§0 - §f、§l、§o 等）。点击下方彩色框即可快速插入"
  },
  "Rút một lá bài để soi chiếu năng lượng hiện tại. AI Sakura sẽ giúp bạn đọc thông điệp theo câu hỏi riêng": {
    "en": "Draw a card to reflect your current energy. AI Sakura will help you read messages according to specific questions",
    "ja": "あなたの現在のエネルギーを反映するカードを引いてください。 AIさくらが、具体的な質問に応じてメッセージを読むお手伝いをします。",
    "cn": "抽一张牌来反映你当前的能量。 AI小樱会根据具体问题帮助你阅读消息"
  },
  "Khám phá thế giới Sakura Bot, hoàn thành thử thách và nhận thưởng Coin, Xu VIP cùng Danh hiệu độc quyền": {
    "en": "Explore the world of Sakura Bot, complete challenges and receive Coin rewards, VIP Coins and exclusive Titles",
    "ja": "サクラボットの世界を探索し、チャレンジを完了して、コイン報酬、VIP コイン、限定称号を受け取りましょう。",
    "cn": "探索 Sakura Bot 的世界，完成挑战并获得金币奖励、VIP 金币和专属头衔"
  },
  "Khi TẮT, bot tạm ngưng toàn bộ module Anti-Raid, Anti-Nuke, Anti-Spam và lọc từ trên toàn bộ các server": {
    "en": "When turned OFF, the bot suspends all Anti-Raid, Anti-Nuke, Anti-Spam and word filtering modules on all servers",
    "ja": "OFF にすると、ボットはすべてのサーバー上のすべての Anti-Raid、Anti-Nuke、Anti-Spam、およびワード フィルタリング モジュールを一時停止します。",
    "cn": "关闭后，机器人会暂停所有服务器上的所有反袭击、反核武器、反垃圾邮件和文字过滤模块。"
  },
  "Chỉ được lưu lại khi người quản trị hoặc người dùng bấm đóng Ticket hỗ trợ nhằm mục đích tra cứu nội bộ": {
    "en": "Only saved when the administrator or user clicks to close the support ticket for internal lookup purposes",
    "ja": "管理者またはユーザーが内部検索の目的でサポート チケットをクリックして閉じた場合にのみ保存されます。",
    "cn": "仅当管理员或用户出于内部查找目的单击关闭支持票证时才保存"
  },
  "Bạn có toàn quyền yêu cầu xóa toàn bộ dữ liệu của bạn hoặc máy chủ của bạn khỏi hệ thống của Sakura Bot": {
    "en": "You have the full right to request deletion of all your data or your server from Sakura Bot's system",
    "ja": "あなたには、Sakura Bot のシステムからすべてのデータまたはサーバーの削除を要求する完全な権利があります。",
    "cn": "您拥有完全权利要求从 Sakura Bot 系统中删除您的所有数据或服务器"
  },
  "Hệ thống TTS sử dụng Google TTS và AI Translator tự động vào Voice Channel phát âm theo thời gian thực": {
    "en": "The TTS system uses Google TTS and AI Translator to automatically enter Voice Channel for real-time pronunciation",
    "ja": "TTS システムは、Google TTS と AI Translator を使用して、音声チャンネルに自動的に入力し、リアルタイムの発音を実現します。",
    "cn": "TTS系统采用Google TTS和AI Translator自动进入Voice Channel进行实时发音"
  },
  "Quản lý hơn 210 thành tựu minigame Sakura, cấp/thu hồi cho người chơi và thiết kế thành tựu tùy chỉnh": {
    "en": "Manage over 210 Sakura minigame achievements, grant/revoke to players, and design custom achievements",
    "ja": "210 を超えるさくらミニゲームの実績を管理し、プレイヤーに付与/取り消しし、カスタム実績をデザインします。",
    "cn": "管理超过 210 个樱花小游戏成就、向玩家授予/撤销以及设计自定义成就"
  },
  "Mặc định: youtube.com, youtu.be, discord.com, tenor.com, giphy.com, imgur.com — để trống sẽ chặn hết": {
    "en": "Default: youtube.com, youtu.be, discord.com, tenor.com, giphy.com, imgur.com — leaving blank will block them all",
    "ja": "デフォルト: youtube.com、youtu.be、discord.com、tenor.com、giphy.com、imgur.com — 空白のままにすると、すべてブロックされます。",
    "cn": "默认值：youtube.com、youtu.be、discord.com、tenor.com、giphy.com、imgur.com — 留空将阻止所有这些内容"
  },
  "Quản lý giỏ cá & vật phẩm người chơi, phát hành giftcode, tra cứu bách khoa và sáng tạo loài cá mới": {
    "en": "Manage fish baskets & player items, issue gift codes, look up encyclopedias and create new fish species",
    "ja": "魚かごやプレイヤーアイテムを管理し、ギフトコードを発行し、百科事典を調べ、新しい魚種を作成します。",
    "cn": "管理鱼篮和玩家物品、发放礼品代码、查找百科全书并创建新的鱼类品种"
  },
  "Thêm các mốc sự kiện đặc biệt, nhiệm vụ máy chủ hoặc phần thưởng thành tựu độc quyền cho Sakura Bot": {
    "en": "Add special event milestones, server quests, or exclusive achievement rewards for Sakura Bot",
    "ja": "特別なイベントのマイルストーン、サーバークエスト、またはサクラボットの特別な実績報酬を追加します。",
    "cn": "为樱花机器人添加特殊事件里程碑、服务器任务或专属成就奖励"
  },
  "Chỉ Chủ Sở Hữu Web (Owner) mới có quyền cấp hoặc thu hồi quyền Quản Trị Viên (Admin) cho người dùng": {
    "en": "Only the Web Owner (Owner) has the right to grant or revoke Administrator rights to users",
    "ja": "Web 所有者 (オーナー) のみが、ユーザーに管理者権限を付与または取り消す権利を持ちます。",
    "cn": "只有 Web 所有者有权授予或撤销用户的管理员权限。"
  },
  ": Vai trò được chọn phải có thứ bậc thấp hơn vai trò cao nhất của Sakura Bot để bot có thể gán được": {
    "en": ": The selected role must be lower in hierarchy than Sakura Bot's highest role for the bot to assign",
    "ja": ": 選択したロールは、ボットが割り当てるために、Sakura Bot の最上位のロールよりも階層が低い必要があります。",
    "cn": "：所选角色的层次结构必须低于 Sakura Bot 机器人分配的最高角色"
  },
  "Dùng để lưu trữ cài đặt riêng của server (Prefix, Kênh Welcome, Cấu hình AutoMod, Danh sách từ cấm)": {
    "en": "Used to store the server's own settings (Prefix, Welcome Channel, AutoMod Configuration, Prohibited Word List)",
    "ja": "サーバー独自の設定 (プレフィックス、ウェルカム チャネル、AutoMod 構成、禁止語リスト) を保存するために使用されます。",
    "cn": "用于存储服务器自己的设置（前缀、欢迎频道、AutoMod 配置、禁止单词列表）"
  },
  "Kiểm soát bật/tắt yêu cầu Vote Top.gg cho các lệnh VIP (/math, /translate, /music volume, /xemboi)": {
    "en": "Controls enabling/disabling Vote Top.gg requests for VIP commands (/math, /translate, /music volume, /xemboi)",
    "ja": "VIP コマンド (/math、/translate、/music volume、/xemboi) に対する Vote Top.gg リクエストの有効化/無効化を制御します。",
    "cn": "控制启用/禁用 VIP 命令的 Vote Top.gg 请求（/math、/translate、/musicvolume、/xemboi）"
  },
  "Phát nhạc trực tiếp qua Simple Voice Chat trong game cho toàn bộ người chơi xung quanh cùng nghe.": {
    "en": "Stream music directly via Simple Voice Chat in the game for all players around you to listen to.",
    "ja": "ゲーム内のシンプルボイスチャット経由で音楽を直接ストリーミングし、周囲のすべてのプレイヤーが聞くことができます。",
    "cn": "通过游戏中的简单语音聊天直接播放音乐，供您周围的所有玩家收听。"
  },
  "Phát nhạc trực tiếp qua Simple Voice Chat trong game cho toàn bộ người chơi xung quanh cùng nghe": {
    "en": "Stream music directly via Simple Voice Chat in the game for all players around you to listen to",
    "ja": "ゲーム内のシンプルボイスチャット経由で音楽を直接ストリーミングし、周囲のすべてのプレイヤーが聞くことができます。",
    "cn": "通过游戏中的简单语音聊天直接串流音乐，供您周围的所有玩家收听"
  },
  "Bạn cần đăng nhập để lưu video cá nhân. Tuy nhiên danh sách gợi ý bên dưới vẫn có thể xem miễn phí": {
    "en": "You need to log in to save personal videos. However, the list of suggestions below can still be viewed for free",
    "ja": "個人的なビデオを保存するにはログインする必要があります。ただし、以下の提案リストは引き続き無料で閲覧できます。",
    "cn": "您需要登录才能保存个人视频。不过，下面的建议列表仍然可以免费查看"
  },
  "[System] Kênh trò chuyện 2 chiều đang hoạt động. Nhập nội dung bên dưới để gửi tin nhắn vào game": {
    "en": "[System] 2-way chat channel is active. Enter the content below to send a message into the game",
    "ja": "[システム] 双方向チャットチャンネルがアクティブです。以下の内容を入力してゲーム内にメッセージを送信してください。",
    "cn": "[系统] 2路聊天频道已激活。输入以下内容即可向游戏发送消息"
  },
  "Bán đồ nhanh qua GUI, Chợ Đen buôn hàng quý hiếm, vé số may mắn và nhiệm vụ thương hội phong phú": {
    "en": "Sell ​​items quickly via GUI, Black Market for rare goods, lucky lottery tickets and rich merchant guild missions",
    "ja": "GUI、ブラックマーケットでレアな商品、幸運の宝くじ、そして裕福な商人のギルドミッションを介してアイテムを素早く販売します。",
    "cn": "通过 GUI 快速出售物品、稀有物品黑市、幸运彩票和丰富的商人公会任务"
  },
  "Tải video TikTok với độ phân giải Full HD gốc, xóa sạch hoàn toàn watermark và logo mờ bản quyền": {
    "en": "Download TikTok videos in original Full HD resolution, completely removing watermarks and blurred copyright logos",
    "ja": "TikTokビデオをオリジナルのフルHD解像度でダウンロードし、透かしやぼやけた著作権ロゴを完全に削除します。",
    "cn": "以原始全高清分辨率下载 TikTok 视频，完全去除水印和模糊的版权标志"
  },
  "Săn bắt cá đại dương, nâng cấp cần câu, buôn bán hải sản và cạnh tranh top cần thủ toàn máy chủ": {
    "en": "Hunt for ocean fish, upgrade fishing rods, trade seafood and compete with the top anglers across the server",
    "ja": "海の魚を狩り、釣り竿をアップグレードし、魚介類を取引し、サーバー全体でトップの釣り人たちと競争しましょう。",
    "cn": "寻找海鱼、升级鱼竿、交易海鲜并与全服务器的顶级钓鱼者竞争"
  },
  "Bảo vệ quặng khỏi mod X-Ray với 3 cấp độ mã hóa khối, chống mở trộm rương và phá hoại đất claim": {
    "en": "Protect ores from X-Ray mods with 3 levels of block encryption, prevent chest theft and claim land destruction",
    "ja": "3 レベルのブロック暗号化で X 線改造から鉱石を保護し、チェストの盗難を防ぎ、土地の破壊を主張します。",
    "cn": "通过 3 级区块加密保护矿石免受 X 射线模组的侵害，防止宝箱被盗并声称土地被破坏"
  },
  "Hệ thống treo thưởng truy nã người chơi hoặc truy vết vị trí kẻ bị truy nã để nhận thưởng lớn.": {
    "en": "The system places a bounty on players or tracks the location of a wanted person to receive a big reward.",
    "ja": "このシステムはプレイヤーに賞金をかけたり、指名手配者の位置を追跡したりして多額の報酬を受け取ります。",
    "cn": "系统向玩家悬赏或追踪通缉犯的位置以获得巨额奖励。"
  },
  "Hệ thống treo thưởng truy nã người chơi hoặc truy vết vị trí kẻ bị truy nã để nhận thưởng lớn": {
    "en": "The system places a bounty on players or tracks the location of a wanted person to receive a big reward",
    "ja": "このシステムはプレイヤーに賞金をかけたり、指名手配者の位置を追跡したりして多額の報酬を受け取ります。",
    "cn": "系统对玩家悬赏或追踪通缉犯的位置以获得巨额奖励"
  },
  "Mua vé số may mắn hàng ngày, tra cứu giải thưởng và thời gian quay thưởng jackpot trong game.": {
    "en": "Buy lucky lottery tickets every day, look up prizes and jackpot drawing time in the game.",
    "ja": "毎日幸運の宝くじを購入し、ゲーム内で賞品とジャックポットの抽選時間を調べてください。",
    "cn": "每天购买幸运彩票，在游戏中查看奖品和大奖抽奖时间。"
  },
  "Mua vé số may mắn hàng ngày, tra cứu giải thưởng và thời gian quay thưởng jackpot trong game": {
    "en": "Buy lucky lottery tickets every day, look up prizes and jackpot drawing time in the game",
    "ja": "毎日幸運の宝くじを購入し、ゲーム内で賞品とジャックポットの抽選時間を調べてください。",
    "cn": "每日购买幸运彩票，在游戏中查看奖品和大奖抽奖时间"
  },
  "Quyền Admin: Cấp các trang bị thần thoại, vũ khí OP và các cuốn sách phù phép đặc biệt Sakura.": {
    "en": "Admin Rights: Grant mythical equipment, OP weapons and special Sakura spell books.",
    "ja": "管理者権限: 神話の装備、OP 武器、特別な桜の魔法の本を付与します。",
    "cn": "管理员权限：授予神话装备、OP 武器和特殊的樱花咒语书。"
  },
  "Quyền Admin: Cấp các trang bị thần thoại, vũ khí OP và các cuốn sách phù phép đặc biệt Sakura": {
    "en": "Admin Rights: Grant mythical equipment, OP weapons and special Sakura spell books",
    "ja": "管理者権限: 神話の装備、OP 武器、特別な桜の魔法の本を付与します。",
    "cn": "管理员权限：授予神话装备、OP武器和特殊的樱花咒语书"
  },
  "Mọi đóng góp dù lớn hay nhỏ đều là nguồn động viên to lớn cho đội ngũ duy trì và phát triển bot": {
    "en": "Every contribution, big or small, is a great source of encouragement for the bot maintenance and development team",
    "ja": "大小を問わず、あらゆる貢献がボットのメンテナンスおよび開発チームにとって大きな励みになります。",
    "cn": "每一个贡献，无论大小，都是对机器人维护和开发团队的巨大鼓励"
  },
  "Cập nhật, thay đổi, thêm hoặc bớt các tính năng của Bot và Web Dashboard mà không cần báo trước": {
    "en": "Update, change, add or remove features of the Bot and Web Dashboard without prior notice",
    "ja": "事前の通知なしに、ボットおよび Web ダッシュボードの機能を更新、変更、追加、または削除すること。",
    "cn": "更新、更改、添加或删除机器人和 Web 仪表板的功能，恕不另行通知"
  },
  "Xem chi tiết túi đồ, trang bị giáp, rương Ender và các hộp Shulker bên trong máy chủ Minecraft": {
    "en": "See details of inventory, armor, Ender chests and Shulker boxes inside the Minecraft server",
    "ja": "Minecraft サーバー内のインベントリ、アーマー、エンダー チェスト、シュルカー ボックスの詳細を確認します。",
    "cn": "查看 Minecraft 服务器内的库存、盔甲、末影箱和潜影盒的详细信息"
  },
  "Cung cấp tính năng AutoMod và phát hiện các hành vi phá hoại (Anti-Raid, Anti-Nuke, Anti-Spam)": {
    "en": "Provides AutoMod features and detects vandalism (Anti-Raid, Anti-Nuke, Anti-Spam)",
    "ja": "AutoMod 機能を提供し、破壊行為を検出します (Anti-Raid、Anti-Nuke、Anti-Spam)。",
    "cn": "提供 AutoMod 功能并检测破坏行为（反袭击、反核武器、反垃圾邮件）"
  },
  "Bạn chưa có quyền quản lý server nào mà bot đang ở, hoặc bot chưa được mời vào server của bạn": {
    "en": "You do not have permission to manage the server the bot is on, or the bot has not been invited to your server",
    "ja": "ボットが存在するサーバーを管理する権限がないか、ボットがサーバーに招待されていません。",
    "cn": "您无权管理机器人所在的服务器，或者机器人尚未被邀请到您的服务器"
  },
  "Đơn vị tiền tệ chính cho câu cá, làm việc, điểm danh daily, mua cần câu, mồi câu và giao dịch": {
    "en": "Main currency for fishing, working, daily attendance, buying fishing rods, bait and trading",
    "ja": "釣り、仕事、日々の出勤、釣り竿の購入、餌の購入、取引に使用される主要通貨。",
    "cn": "钓鱼、工作、日常出勤、购买鱼竿、鱼饵和交易的主要货币"
  },
  "Mời Sakura Bot về máy chủ của bạn để trải nghiệm tính năng Quản trị, Level, Fishing, Casino": {
    "en": "Invite Sakura Bot to your server to experience Administration, Level, Fishing, Casino",
    "ja": "サーバーにさくらボットを招待して、管理、レベル、釣り、カジノなどを体験してください",
    "cn": "邀请樱花机器人到您的服务器体验管理、关卡、钓鱼、赌场功能"
  },
  "Yểm bùa biến nạn nhân thành Cóc/Ếch. Lần câu kế tiếp chắc chắn vớt lên Cóc Ghẻ hoặc Rác rưởi": {
    "en": "Cast a spell that turns the victim into a Toad/Frog. The next time you fish, make sure to pick up Toadstools or Trash",
    "ja": "犠牲者をヒキガエル/カエルに変える呪文を唱えます。次回釣りをするときは、キノコやゴミを必ず拾ってください。",
    "cn": "施放一个咒语，将受害者变成蟾蜍/青蛙。下次钓鱼时，请务必捡起伞菌或垃圾"
  },
  "Bạn phải là Chủ sở hữu (Owner) hoặc Administrator của Discord Server này để thực hiện nối!": {
    "en": "You must be the Owner or Administrator of this Discord Server to make the connection!",
    "ja": "接続するには、この Discord サーバーの所有者または管理者である必要があります。",
    "cn": "您必须是此 Discord 服务器的所有者或管理员才能建立连接！"
  },
  "Bạn phải là Chủ sở hữu (Owner) hoặc Administrator của Discord Server này để thực hiện nối": {
    "en": "You must be the Owner or Administrator of this Discord Server to make the connection",
    "ja": "接続するには、この Discord サーバーの所有者または管理者である必要があります。",
    "cn": "您必须是此 Discord 服务器的所有者或管理员才能建立连接"
  },
  "để thêm mốc cấp độ và vai trò tương ứng. Khi thành viên đạt đủ cấp, bot sẽ tự động trao role": {
    "en": "to add corresponding level and role markers. When the member reaches enough level, the bot will automatically award the role",
    "ja": "対応するレベルとロールのマーカーを追加します。メンバーが十分なレベルに達すると、ボットが自動的に役割を与えます。",
    "cn": "添加相应的级别和角色标记。当会员达到足够等级时，机器人会自动授予角色"
  },
  "Dùng các nút Lên / Xuống để điều chỉnh thứ tự xuất hiện của các khối trên trang bio của bạn": {
    "en": "Use the Up / Down buttons to adjust the order in which blocks appear on your bio page",
    "ja": "上/下ボタンを使用して、自己紹介ページに表示されるブロックの順序を調整します。",
    "cn": "使用向上/向下按钮调整块在您的个人简介页面上显示的顺序"
  },
  "trong Discord và bot đã được mời vào server đó. Thử đăng xuất và đăng nhập lại bằng Discord": {
    "en": "in Discord and the bot has been invited to that server. Try logging out and back in using Discord",
    "ja": "Discord 内にあり、ボットはそのサーバーに招待されています。 Discord を使用してログアウトしてから再度ログインしてみてください。",
    "cn": "在 Discord 中并且机器人已被邀请到该服务器。尝试使用 Discord 注销并重新登录"
  },
  "Plugin Sakura được đóng gói dưới dạng file .jar sẵn sàng dùng cho máy chủ Minecraft của bạn": {
    "en": "The Sakura plugin is packaged as a .jar file ready to be used on your Minecraft server",
    "ja": "さくらプラグインは、Minecraft サーバーですぐに使用できる .jar ファイルとしてパッケージ化されています。",
    "cn": "Sakura 插件打包为 .jar 文件，可在您的 Minecraft 服务器上使用"
  },
  "Không sử dụng Bot cho các hành vi quấy rối, phá hoại, spam hoặc vi phạm pháp luật hiện hành": {
    "en": "Do not use the Bot for acts of harassment, vandalism, spam or other violations of applicable laws",
    "ja": "ボットを嫌がらせ、破壊行為、スパム行為、またはその他の適用法違反に使用しないでください。",
    "cn": "请勿使用机器人进行骚扰、破坏、垃圾邮件或其他违反适用法律的行为"
  },
  "Trích xuất âm thanh chất lượng cao 320kbps từ bất kỳ video hoặc bài đăng TikTok nào dễ dàng": {
    "en": "Extract high quality 320kbps audio from any TikTok video or post with ease",
    "ja": "TikTok ビデオや投稿から高品質の 320kbps オーディオを簡単に抽出します。",
    "cn": "轻松从任何 TikTok 视频或帖子中提取高质量 320kbps 音频"
  },
  "Dùng một con cá biển trơn trượt tát bôm bốp vào mặt nạn nhân kèm ping công khai trong kênh": {
    "en": "Use a slippery sea fish to slap the victim in the face with a public ping on the channel",
    "ja": "滑りやすい海の魚を使って、チャンネル上で公開 ping を送り、被害者の顔を叩きます。",
    "cn": "使用滑溜的海鱼在频道上公开 ping 来打受害者的脸"
  },
  "Khi Bot bị gỡ khỏi máy chủ, bạn có thể liên hệ để yêu cầu dọn dẹp toàn bộ cấu hình máy chủ": {
    "en": "Once the Bot is removed from the server, you can contact to request a cleanup of the entire server configuration",
    "ja": "ボットがサーバーから削除されたら、サーバー構成全体のクリーンアップをリクエストするために連絡できます。",
    "cn": "从服务器中删除机器人后，您可以联系请求清理整个服务器配置"
  },
  "Bật (True) để chỉ cho tài khoản bản quyền; Tắt (False) để cho phép cả bản Crack / Offline": {
    "en": "Turn on (True) to indicate the copyright account; Turn off (False) to allow both Crack / Offline versions",
    "ja": "著作権アカウントを示すには (True) をオンにします。クラック バージョンとオフライン バージョンの両方を許可するには、オフ (False) にします。",
    "cn": "开启（True）表示版权账号；关闭（False）以允许破解/离线版本"
  },
  "Tham gia cộng đồng chính thức để nhận hỗ trợ trực tiếp, nhận thông báo update và giao lưu": {
    "en": "Join the official community to receive direct support, receive updates and socialize",
    "ja": "公式コミュニティに参加すると、直接サポートを受けたり、最新情報を受け取ったり、交流したりできます。",
    "cn": "加入官方社区以获得直接支持、接收更新和社交"
  },
  "Tra cứu danh sách hơn 100+ lệnh, cú pháp sử dụng và tài liệu hướng dẫn cấu hình toàn diện": {
    "en": "Look up a list of over 100+ commands, usage syntax and comprehensive configuration documentation",
    "ja": "100 を超えるコマンドのリスト、使用構文、および包括的な構成ドキュメントを検索します。",
    "cn": "查找超过 100 个命令、使用语法和全面的配置文档的列表"
  },
  "Gửi tin nhắn chào mừng kèm ảnh avatar xịn xò, tự động gán vai trò khi thành viên mới vào": {
    "en": "Send a welcome message with a cool avatar photo, automatically assign roles when new members join",
    "ja": "クールなアバター写真付きのウェルカム メッセージを送信し、新しいメンバーが参加すると自動的に役割を割り当てます。",
    "cn": "发送带有炫酷头像照片的欢迎信息，新成员加入时自动分配角色"
  },
  "Bỏ bùa nói ngược. Bot sẽ bắt chước các tin nhắn của nạn nhân và đảo ngược toàn bộ ký tự": {
    "en": "Cast the reverse spell. The bot will imitate the victim's messages and reverse all the characters",
    "ja": "逆の呪文を唱えます。ボットは被害者のメッセージを模倣し、すべての文字を反転します。",
    "cn": "施展反向咒语。机器人会模仿受害者的消息并反转所有字符"
  },
  "Nếu bạn có thắc mắc hoặc yêu cầu về quyền riêng tư và dữ liệu cá nhân, vui lòng liên hệ": {
    "en": "If you have questions or requests about privacy and personal data, please contact",
    "ja": "プライバシーおよび個人データに関するご質問またはご要望がある場合は、以下までご連絡ください。",
    "cn": "如果您对隐私和个人数据有疑问或要求，请联系我们"
  },
  "Bảng vinh danh cao thủ minigame toàn bot và danh sách tra cứu hơn 210 thành tựu Sakura": {
    "en": "Minigame honor board full of bots and lookup list of more than 210 Sakura achievements",
    "ja": "ボットが満載のミニゲーム名誉ボードと 210 を超えるサクラ実績のルックアップ リスト。",
    "cn": "充满机器人的迷你游戏荣誉板和超过 210 个樱花成就的查找列表"
  },
  "Thêm các mẫu cần câu, mồi câu, thú cưng hoặc vật phẩm troll hoàn toàn mới vào hệ thống": {
    "en": "Add completely new fishing rod models, lures, pets or trolling items to the system",
    "ja": "まったく新しい釣り竿モデル、ルアー、ペット、またはトローリング アイテムをシステムに追加します。",
    "cn": "将全新的钓鱼竿模型、鱼饵、宠物或拖钓物品添加到系统中"
  },
  "Tài khoản tiết kiệm tích lũy coin của người chơi trong hệ thống ngân hàng Sakura Bank": {
    "en": "The player's savings account accumulates coins in the Sakura Bank banking system",
    "ja": "プレイヤーの普通預金口座は、さくら銀行銀行システムにコインを蓄積します。",
    "cn": "玩家的储蓄账户在樱花银行银行系统中积累硬币"
  },
  "Tích lũy kinh nghiệm khi chat & voice, bảng xếp hạng Top server, shop vai trò và coin": {
    "en": "Gain experience in chat & voice, Top server rankings, role shop and coins",
    "ja": "チャットと音声、トップサーバーランキング、ロールショップ、コインの経験を積みましょう。",
    "cn": "获得聊天和语音、顶级服务器排名、角色商店和金币方面的经验"
  },
  "Đóng góp kinh phí duy trì hạ tầng máy chủ và API cao cấp giúp Sakura Bot luôn mượt mà": {
    "en": "Contribute funds to maintain server infrastructure and high-end APIs to help Sakura Bot always run smoothly",
    "ja": "さくらボットが常にスムーズに動作するように、サーバー インフラストラクチャとハイエンド API を維持するために資金を寄付してください。",
    "cn": "贡献资金维护服务器基础设施和高端API，帮助Sakura Bot始终平稳运行"
  },
  "Mồi câu bị nguyền rủa. Buộc người câu chỉ bắt được ủng rách, rác thải, tảo biển thối": {
    "en": "The bait is cursed. Force fishermen to only catch torn boots, garbage, and rotten seaweed",
    "ja": "餌は呪われています。漁師たちに、破れた長靴、ゴミ、腐った海藻だけを捕獲するよう強制する。",
    "cn": "诱饵被诅咒了。迫使渔民只捕捞破靴子、垃圾和腐烂的海藻"
  },
  "Thời gian ms tối đa cho 1 tick trước khi watchdog tự dừng server (-1 để vô hiệu hóa)": {
    "en": "Maximum ms time for 1 tick before watchdog automatically stops the server (-1 to disable)",
    "ja": "ウォッチドッグがサーバーを自動的に停止するまでの 1 ティックの最大ミリ秒時間 (無効にする場合は -1)。",
    "cn": "看门狗自动停止服务器之前 1 个周期的最大毫秒时间（-1 表示禁用）"
  },
  "theo cách thông thường, chỉ nhận được khi nạp tiền hoặc do Owner cấp phát trực tiếp": {
    "en": "Normally, you can only receive money when depositing money or directly from the Owner",
    "ja": "通常、お金を受け取ることができるのは、お金を入金する場合、またはオーナーから直接受け取る場合のみです。",
    "cn": "一般情况下，您只能在存款时或直接从店主处收到款项"
  },
  "cho họ (cùng category) – họ tự đặt tên, giới hạn, khóa/ẩn. Rời kênh thì kênh tự xóa": {
    "en": "for them (same category) – they name themselves, limit, lock/hide. If you leave the channel, the channel will automatically delete itself",
    "ja": "彼らにとって (同じカテゴリ) – 彼らは自分自身に名前を付け、制限し、ロック/非表示にします。チャンネルを離れると、チャンネルは自動的に削除されます。",
    "cn": "对于他们（同一类别）——他们命名自己、限制、锁定/隐藏。如果您离开频道，该频道将自动删除"
  },
  "Khởi động lại máy chủ và kiểm tra console xem plugin đã bắt đầu thành công hay chưa": {
    "en": "Restart the server and check the console to see if the plugin started successfully or not",
    "ja": "サーバーを再起動し、コンソールでプラグインが正常に開始したかどうかを確認します。",
    "cn": "重启服务器，查看控制台是否插件启动成功"
  },
  "Tạo phòng hỗ trợ riêng tư 1 chạm cho thành viên, lưu transcript và lịch sử tin cậy": {
    "en": "Create a 1-touch private support room for members, save transcripts and trust history",
    "ja": "ワンタッチでメンバー向けのプライベート サポート ルームを作成し、トランスクリプトと信頼履歴を保存します。",
    "cn": "为会员创建一键式私人支持室，保存记录和信任历史记录"
  },
  "Phát nhạc chất lượng cao từ YouTube, SoundCloud, Spotify qua node Lavalink ổn định": {
    "en": "Stream high quality music from YouTube, SoundCloud, Spotify via stable Lavalink node",
    "ja": "安定した Lavalink ノードを介して YouTube、SoundCloud、Spotify から高品質の音楽をストリーミングします。",
    "cn": "通过稳定的 Lavalink 节点从 YouTube、SoundCloud、Spotify 流式传输高品质音乐"
  },
  "Thông điệp hiển thị tại màn hình xác nhận tải resource pack khi người chơi kết nối": {
    "en": "Message displayed on the resource pack download confirmation screen when the player connects",
    "ja": "プレイヤー接続時のリソースパックダウンロード確認画面に表示されるメッセージ。",
    "cn": "播放器连接时资源包下载确认屏幕上显示的消息"
  },
  "* Cần câu mới sẽ tự động trang bị nếu user chưa có cần. Hỗ trợ tối đa +300 và 20⭐": {
    "en": "* New fishing rods will automatically be equipped if the user does not have one yet. Maximum support +300 and 20⭐",
    "ja": "※ユーザーがまだ釣り竿を持っていない場合は、新しい釣り竿が自動的に装備されます。最大サポート+300と20⭐。",
    "cn": "* 如果用户还没有钓鱼竿，将会自动装备新的钓鱼竿。最大支持+300和20⭐"
  },
  "Bấm vào từng tính năng để xem danh sách lệnh và hướng dẫn chi tiết từ Sakura Bot": {
    "en": "Click on each feature to see a list of commands and detailed instructions from Sakura Bot",
    "ja": "各機能をクリックすると、Sakura Bot のコマンド一覧と詳細な手順が表示されます。",
    "cn": "单击每个功能可查看 Sakura Bot 的命令列表和详细说明"
  },
  "Tarot chỉ mang tính tham khảo và tự phản chiếu, không thay thế tư vấn chuyên môn": {
    "en": "Tarot is for reference and self-reflection purposes only and is not a substitute for professional advice",
    "ja": "タロットは参考と自省のみを目的としており、専門的なアドバイスの代わりとなるものではありません。",
    "cn": "塔罗牌仅供参考和自我反省之用，不能替代专业建议"
  },
  "Đóng băng cần câu của nạn nhân. Trong thời gian này nạn nhân không thể thả cần": {
    "en": "Freeze the victim's fishing rod. During this time the victim cannot release the lever",
    "ja": "被害者の釣り竿を凍らせます。この間、被害者はレバーを放すことができません。",
    "cn": "冻结受害者的钓鱼竿。在此期间受害者无法松开控制杆"
  },
  "© 2026 Sakura Bot — Trợ lý Discord thông minh & đa năng cho cộng đồng Việt Nam": {
    "en": "© 2026 Sakura Bot — Smart & versatile Discord assistant for the Vietnamese community",
    "ja": "© 2026 Sakura Bot — ベトナム人コミュニティ向けのスマートで多用途な Discord アシスタント。",
    "cn": "© 2026 Sakura Bot — 越南社区的智能多功能 Discord 助手"
  },
  "Cướp ngẫu nhiên 1 con cá có giá trị cao nhất trong kho đồ câu cá của nạn nhân": {
    "en": "Randomly steal 1 fish with the highest value in the victim's fishing inventory",
    "ja": "被害者の釣りインベントリの中で最も価値の高い魚をランダムに 1 匹盗みます。",
    "cn": "随机偷取受害者钓鱼库存中价值最高的 1 条鱼"
  },
  "Tin nhắn gửi trên Discord sẽ tự động chuyển vào Minecraft chat, và ngược lại": {
    "en": "Messages sent on Discord will automatically be transferred to Minecraft chat, and vice versa",
    "ja": "Discord で送信されたメッセージは自動的に Minecraft チャットに転送され、その逆も同様です。",
    "cn": "在 Discord 上发送的消息将自动转移到 Minecraft 聊天，反之亦然"
  },
  "Gửi thông báo nhúng (Embed) đẹp mắt kèm skin nhân vật khi có sự kiện in-game": {
    "en": "Send beautiful Embed notifications with character skins when there are in-game events",
    "ja": "ゲーム内イベントがあるときに、キャラクター スキンを使用して美しい埋め込み通知を送信します。",
    "cn": "当有游戏内事件时，发送带有角色皮肤的精美嵌入通知"
  },
  "Chuyển cá vào kho của kẻ dùng. Nạn nhân có thể phản đòn bằng Gương ma thuật": {
    "en": "Move the fish to the user's inventory. The victim can counterattack with the Magic Mirror",
    "ja": "魚をユーザーの在庫に移動します。被害者はマジックミラー号で反撃できる！",
    "cn": "将鱼移至用户的库存中。受害者可以用魔镜进行反击"
  },
  "Nhập lệnh console gửi đến Bot (status, testdm, say, eval, rates, help...)": {
    "en": "Enter console commands sent to Bot (status, testdm, say, eval, rates, help...)",
    "ja": "ボットに送信されるコンソール コマンド (ステータス、testdm、たとえば、eval、rate、help...) を入力します",
    "cn": "输入发送到 Bot 的控制台命令（状态、testdm、例如、eval、费率、帮助...）"
  },
  "Hỗ trợ gửi hình ảnh, video, âm thanh hoặc tài liệu đính kèm cùng thông báo": {
    "en": "Supports sending images, videos, audio or documents attached with notifications",
    "ja": "通知に添付された画像、ビデオ、オーディオ、またはドキュメントの送信をサポートします。",
    "cn": "支持发送带有通知的图像、视频、音频或文档"
  },
  "Anti-raid, anti-nuke, chống spam tin nhắn, lọc link mời và từ cấm tự động": {
    "en": "Anti-raid, anti-nuke, anti-message spam, filter invitation links and automatic banned words",
    "ja": "アンチレイド、アンチニューク、アンチメッセージスパム、フィルター招待リンク、自動禁止ワード。",
    "cn": "防袭击、防核弹、防垃圾短信、过滤邀请链接和自动禁言"
  },
  "Mã kiểm tra tính toàn vẹn 40 ký tự hex để client không tải lại nếu đã có": {
    "en": "40 hex character integrity check code so the client does not reload if it already exists",
    "ja": "40 16 進数文字の整合性チェック コード。コードがすでに存在する場合、クライアントはリロードしません。",
    "cn": "40 个十六进制字符完整性检查代码，因此如果该代码已存在，客户端不会重新加载"
  },
  "Nếu bật, người chơi từ chối tải sẽ tự động bị ngắt kết nối khỏi máy chủ": {
    "en": "If enabled, players who refuse to load will automatically be disconnected from the server",
    "ja": "有効にすると、ロードを拒否したプレーヤーは自動的にサーバーから切断されます。",
    "cn": "如果启用，拒绝加载的玩家将自动断开与服务器的连接"
  },
  "Bạn không phải chủ sở hữu của hồ sơ này và không có quyền chỉnh sửa.": {
    "en": "You are not the owner of this profile and do not have editing rights.",
    "ja": "あなたはこのプロフィールの所有者ではないため、編集権限がありません。",
    "cn": "您不是此个人资料的所有者，也没有编辑权限。"
  },
  "Bạn không phải chủ sở hữu của hồ sơ này và không có quyền chỉnh sửa": {
    "en": "You are not the owner of this profile and do not have editing rights",
    "ja": "あなたはこのプロフィールの所有者ではないため、編集権限がありません。",
    "cn": "您不是此个人资料的所有者，并且没有编辑权限"
  },
  "Cướp một khoản tiền trong ví người khác chuyển thẳng vào ví người dùng": {
    "en": "Steal an amount of money from someone else's wallet and transfer it directly to the user's wallet",
    "ja": "他人のウォレットからある金額を盗み、それをユーザーのウォレットに直接転送します。",
    "cn": "从别人的钱包中窃取一定数量的钱并将其直接转移到用户的钱包中"
  },
  "tính năng này để mọi người dùng được dùng các lệnh tự do không bị chặn": {
    "en": "This feature allows all users to use commands freely without being blocked",
    "ja": "この機能により、すべてのユーザーがブロックされることなくコマンドを自由に使用できるようになります。",
    "cn": "该功能允许所有用户自由使用命令而不会被阻止"
  },
  "Tự ý đổi biệt danh của nạn nhân trong server thành tên troll ngớ ngẩn": {
    "en": "Arbitrarily changed the victim's nickname on the server to a silly troll",
    "ja": "サーバー上で被害者のニックネームを恣意的に愚かな荒らしに変更しました。",
    "cn": "随意将受害者在服务器上的昵称更改为愚蠢的巨魔"
  },
  "Ví dụ: Rương cổ chìm dưới đáy đại dương chứa mồi quý và thú cưng hiếm": {
    "en": "For example: Ancient chests sunk to the bottom of the ocean contain precious bait and rare pets",
    "ja": "例: 海の底に沈んだ古代の宝箱には、貴重な餌や珍しいペットが含まれています。",
    "cn": "例如：沉入海底的古代箱子里有珍贵的鱼饵和稀有的宠物"
  },
  "Ví dụ: Khiến nạn nhân bị cóc hóa, lần câu tiếp theo chắc chắn vớt rác": {
    "en": "For example: Cause the victim to become a frog, the next time you fish, make sure to pick up trash",
    "ja": "例: 犠牲者をカエルにして、次回釣りをするときは必ずゴミを拾いましょう。",
    "cn": "例如：导致受害者变成青蛙，下次钓鱼时，他一定会捡垃圾"
  },
  "Quét mã QR hoặc sao chép liên kết để chia sẻ hồ sơ của bạn với bạn bè": {
    "en": "Scan the QR code or copy the link to share your profile with friends",
    "ja": "QR コードをスキャンするかリンクをコピーして、プロフィールを友達と共有します。",
    "cn": "扫描二维码或复制链接与好友分享您的个人资料"
  },
  "Viết đôi dòng giới thiệu về bản thân, đam mê, dự án đang thực hiện": {
    "en": "Write a few lines introducing yourself, passion, ongoing projects",
    "ja": "自己紹介、情熱、進行中のプロジェクトなどを数行書きます。",
    "cn": "写几行介绍你自己、你的热情以及你正在从事的项目"
  },
  "(User View Preview). Các mục quản trị và dữ liệu nhạy cảm đã được ẩn": {
    "en": "(User View Preview). Admin items and sensitive data have been hidden",
    "ja": "(ユーザービュープレビュー)。管理項目と機密データは非表示になっています。",
    "cn": "（用户视图预览）。管理项目和敏感数据已被隐藏"
  },
  "Sakura TikTok — Xem Trước & Tải Video / Album Ảnh TikTok Không Logo": {
    "en": "Sakura TikTok — Preview & Download TikTok Videos / Photo Albums Without Logo",
    "ja": "さくら TikTok — ロゴなしの TikTok ビデオ / フォト アルバムをプレビュー & ダウンロード",
    "cn": "Sakura TikTok — 预览和下载没有徽标的 TikTok 视频/相册"
  },
  "Xử lý trực tiếp trên trình duyệt, dữ liệu không được gửi lên server": {
    "en": "Processed directly in the browser, data is not sent to the server",
    "ja": "ブラウザ内で直接処理され、データはサーバーに送信されません。",
    "cn": "直接在浏览器中处理，数据不发送到服务器"
  },
  "Đồng bộ trạng thái và danh sách Whitelist cho máy chủ Minecraft SMP": {
    "en": "Synchronize status and whitelist for Minecraft SMP server",
    "ja": "Minecraft SMP サーバーのステータスとホワイトリストを同期します。",
    "cn": "同步 Minecraft SMP 服务器的状态和白名单"
  },
  "trong game Minecraft hoặc chọn trực tiếp server phát hiện bên dưới": {
    "en": "in Minecraft game or directly select the detection server below",
    "ja": "Minecraft ゲーム内で、または以下の検出サーバーを直接選択します。",
    "cn": "在Minecraft游戏中或者直接选择下面的检测服务器"
  },
  "Hỗ trợ dán link ảnh hoặc tải tệp từ máy tính (PNG, JPG, GIF, WebP)": {
    "en": "Supports pasting image links or downloading files from your computer (PNG, JPG, GIF, WebP)",
    "ja": "画像リンクの貼り付け、またはコンピューターからのファイルのダウンロード (PNG、JPG、GIF、WebP) をサポートします。",
    "cn": "支持粘贴图像链接或从计算机下载文件（PNG、JPG、GIF、WebP）"
  },
  "Nhấn vào từng mục bên dưới để xem mô tả và cú pháp cụ thể của lệnh": {
    "en": "Click on each item below to see the command's description and specific syntax",
    "ja": "以下の各項目をクリックすると、コマンドの説明と特定の構文が表示されます。",
    "cn": "单击下面的每一项可以查看命令的描述和具体语法"
  },
  "Tự động gửi thông báo code mới đến kênh Giftcode của Discord Bot": {
    "en": "Automatically send new code notifications to Discord Bot's Giftcode channel",
    "ja": "新しいコード通知を Discord Bot の Giftcode チャンネルに自動的に送信します",
    "cn": "自动向 Discord Bot 的 Giftcode 频道发送新代码通知"
  },
  "Ví dụ: Tăng 35% may mắn, tiết kiệm 20% mồi và buff 25% giá bán cá": {
    "en": "For example: Increase luck by 35%, save 20% on bait and buff 25% of fish selling price",
    "ja": "例: 運を 35% 増加させ、餌を 20% 節約し、魚の販売価格を 25% 強化します。",
    "cn": "例如：运气增加35%，鱼饵节省20%，鱼售价提高25%"
  },
  "Danh sách được nhóm theo danh mục; 🔊 là phần chat của kênh voice": {
    "en": "The list is grouped by category; 🔊 is the chat part of the voice channel",
    "ja": "リストはカテゴリごとにグループ化されています。 🔊はボイスチャンネルのチャット部分です。",
    "cn": "该列表按类别分组； 🔊是语音频道的聊天部分"
  },
  "Nhập lệnh console (vd: list, help, say Xin chào, time set day)": {
    "en": "Enter console commands (e.g. list, help, say Hello, time set day)",
    "ja": "コンソール コマンドを入力します (例: list、help、Say Hello、time set day)",
    "cn": "输入控制台命令（例如列表、帮助、说你好、时间设置日期）"
  },
  "Vui lòng tải gói tài nguyên tùy chỉnh để có trải nghiệm tốt nhất": {
    "en": "Please download custom resource packs for the best experience",
    "ja": "最高のエクスペリエンスを得るには、カスタム リソース パックをダウンロードしてください。",
    "cn": "请下载自定义资源包以获得最佳体验"
  },
  "Mở hệ thống cửa hàng và mua vật phẩm hoặc quyền lợi trong server": {
    "en": "Open the store system and buy items or benefits in the server",
    "ja": "ストア システムを開き、サーバー内のアイテムや特典を購入します。",
    "cn": "打开商店系统，购买服务器内的物品或福利"
  },
  "Ping ma quái chọc ghẹo nạn nhân trong kênh chat rồi xóa tức thì": {
    "en": "Ghostly ping teases the victim in the chat channel and then deletes it immediately",
    "ja": "Ghostly ping はチャット チャネルで被害者をからかい、すぐに削除します。",
    "cn": "Ghostly ping 在聊天频道中戏弄受害者，然后立即删除"
  },
  "Tìm kiếm lệnh (ví dụ: fish, help, ban, play, daily, level...)": {
    "en": "Search for commands (eg: fish, help, ban, play, daily, level...)",
    "ja": "コマンドを検索します (例:fish、help、ban、play、daily、level...)",
    "cn": "搜索命令（例如钓鱼、帮助、禁止、播放、每日、关卡...）"
  },
  "thu thập bất kỳ thông tin thanh toán hay tài chính nhạy cảm nào": {
    "en": "Collect any sensitive financial or payment information",
    "ja": "機密の財務情報または支払い情報を収集します。",
    "cn": "收集任何敏感的财务或付款信息"
  },
  "Hiển thị Bảng xếp hạng Level, EXP và quản lý số dư Sakura Coins": {
    "en": "Display Level, EXP Rankings and manage Sakura Coins balance",
    "ja": "レベルや経験値ランキングの表示、桜コインの残高管理ができます。",
    "cn": "显示等级、经验排名并管理樱花币余额"
  },
  "Mô tả cụ thể sự cố bạn gặp phải hoặc ý tưởng bạn muốn chia sẻ": {
    "en": "Describe specifically the problem you encountered or the idea you want to share",
    "ja": "遭遇した問題や共有したいアイデアについて具体的に説明してください",
    "cn": "具体描述您遇到的问题或您想分享的想法"
  },
  "Rương cổ chìm dưới đáy đại dương chứa mồi quý và thú cưng hiếm": {
    "en": "Ancient chests sunk to the bottom of the ocean contain precious bait and rare pets",
    "ja": "海の底に沈んだ古代の宝箱には、貴重な餌や珍しいペットが入っています。",
    "cn": "沉入海底的古代箱子里装有珍贵的鱼饵和稀有的宠物"
  },
  "Hiển thị thông điệp troll tùy ý kèm hiệu ứng embed hoa anh đào": {
    "en": "Display arbitrary troll messages with cherry blossom embed effects",
    "ja": "桜の埋め込みエフェクトを使用して任意の荒らしメッセージを表示します。",
    "cn": "使用樱花嵌入效果显示任意巨魔消息"
  },
  "Tin nhắn giống hệt nhau quá ngưỡng trong lịch sử gần đây → xóa": {
    "en": "Identical messages exceeding the threshold in recent history → delete",
    "ja": "最近の履歴でしきい値を超えた同一メッセージ → 削除。",
    "cn": "最近历史记录中超过阈值的相同消息 → 删除"
  },
  "Bấm nút hoặc thả reaction bên dưới để nhận vai trò tương ứng": {
    "en": "Click the button or drop the reaction below to receive the corresponding role",
    "ja": "ボタンをクリックするか、下にリアクションをドロップして、対応する役割を受け取ります",
    "cn": "点击按钮或下拉下方反应即可领取对应角色"
  },
  "Bể Phần Thưởng Của Rương (Chọn các vật phẩm có thể mở trúng)": {
    "en": "Chest Rewards Pool (Select items that can be opened)",
    "ja": "チェスト報酬プール (開けられるアイテムを選択)",
    "cn": "宝箱奖励池（选择可开启的物品）"
  },
  "Rút trộm tiền. Nếu nạn nhân trang bị Khiên bảo vệ sẽ cướp hụt": {
    "en": "Stealing money. If the victim is equipped with a Shield, the robbery will be missed",
    "ja": "お金を盗む。被害者がシールドを装備していれば、強盗は見逃されます。",
    "cn": "偷钱。如果受害者装备了盾牌，抢劫就会错过"
  },
  "Discord Timeout member. Yêu cầu SakuraBot có quyền Moderation": {
    "en": "Discord Timeout member. Requires SakuraBot to have Moderation permission",
    "ja": "Discordのタイムアウトメンバー。サクラボットにはモデレーション権限が必要です。",
    "cn": "Discord 超时成员。需要 SakuraBot 拥有审核权限"
  },
  "Tự động cắt và chuyển đổi thành chuẩn 64x64 PNG của Minecraft": {
    "en": "Automatically crop and convert to Minecraft's 64x64 PNG standard",
    "ja": "自動的に切り抜き、Minecraft の 64x64 PNG 標準に変換します。",
    "cn": "自动裁剪并转换为 Minecraft 的 64x64 PNG 标准"
  },
  "Tôi có thể đổi biệt danh (nickname) cho bot trên server không": {
    "en": "Can I change the nickname for a bot on the server",
    "ja": "サーバー上のボットのニックネームを変更できますか",
    "cn": "我可以更改服务器上机器人的昵称吗？"
  },
  "Chưa thêm vật phẩm đính kèm nào (mã chỉ tặng tiền/xu nếu có)": {
    "en": "No attached items have been added (code only gives money/coins if available)",
    "ja": "付属アイテムは追加されていません (コードは、利用可能な場合はお金/コインのみを提供します)。",
    "cn": "尚未添加任何附件（代码仅提供金钱/硬币（如果有）"
  },
  "Troll câu cá khiến đối phương tụt may mắn về 0 trong 15 phút": {
    "en": "Troll fishing causes the opponent's luck to drop to 0 for 15 minutes",
    "ja": "トロールフィッシングを行うと、相手の幸運が 15 分間 0 になります。",
    "cn": "巨魔钓鱼导致对手运气降至0，持续15分钟"
  },
  "Mật Khẩu / Mã PIN Bảo Vệ Dashboard (Để trống nếu không khóa)": {
    "en": "Password / PIN Protect Dashboard (Leave blank if not locked)",
    "ja": "パスワード / PIN 保護ダッシュボード (ロックされていない場合は空白のままにします)",
    "cn": "密码/PIN 码保护仪表板（如果未锁定，则留空）"
  },
  "https://www.youtube.com/watch?v=... hoặc https://youtu.be/": {
    "en": "https://www.youtube.com/watch?v=... or https://youtu.be/",
    "ja": "https://www.youtube.com/watch?v=... または https://youtu.be/",
    "cn": "https://www.youtube.com/watch?v=... 或 https://youtu.be/"
  },
  "Gửi embed/thông báo đến kênh của server này như các bot lớn": {
    "en": "Send embed/notification to this server's channel like big bots",
    "ja": "大きなボットのように、このサーバーのチャネルに埋め込み/通知を送信します。",
    "cn": "像大机器人一样向该服务器的频道发送嵌入/通知"
  },
  "Nhập Discord User ID cần thủ (Ví dụ: 1144785664458637394)": {
    "en": "Enter Discord User ID (Example: 1144785664458637394)",
    "ja": "Discord ユーザー ID を入力してください (例: 1144785664458637394)",
    "cn": "输入 Discord 用户 ID（例如：1144785664458637394）"
  },
  "Mô tả tập tính, môi trường sống và vẻ đẹp của loài cá này": {
    "en": "Describe the behavior, habitat and beauty of this fish",
    "ja": "この魚の行動、生息地、美しさを説明してください",
    "cn": "描述这种鱼的行为、栖息地和美丽"
  },
  "Xem Trước Danh Sách Máy Chủ (Minecraft Server List Preview)": {
    "en": "Minecraft Server List Preview",
    "ja": "Minecraft サーバー リスト プレビュー",
    "cn": "Minecraft 服务器列表预览（Minecraft 服务器列表预览）"
  },
  "Chỉ những người chơi trong danh sách whitelist mới được vào": {
    "en": "Only players on the whitelist can enter",
    "ja": "ホワイトリストに登録されているプレイヤーのみが参加できます。",
    "cn": "只有白名单内的玩家才能进入"
  },
  "Xác thực quyền quản trị khi bạn đăng nhập vào Web Dashboard": {
    "en": "Authenticate administrative rights when you log in to the Web Dashboard",
    "ja": "Web ダッシュボードにログインするときに管理者権限を認証します。",
    "cn": "登录 Web Dashboard 时验证管理权限"
  },
  "Ví dụ: Mình nên tập trung điều gì trong công việc tháng này": {
    "en": "For example: What should I focus on at work this month",
    "ja": "例: 今月は仕事で何に重点を置くべきですか",
    "cn": "例如：这个月工作中我应该关注什么？"
  },
  "Chọn ảnh GIF, PNG, JPG, WEBP (tối đa 5MB). Hỗ trợ GIF động": {
    "en": "Choose GIF, PNG, JPG, WEBP images (maximum 5MB). Supports animated GIFs",
    "ja": "GIF、PNG、JPG、WEBP 画像 (最大 5MB) を選択します。アニメーションGIFをサポートします。",
    "cn": "选择 GIF、PNG、JPG、WEBP 图像（最大 5MB）。支持动画 GIF"
  },
  ". User thường chỉ thấy server của mình, admin thấy toàn bộ": {
    "en": ". Users usually only see their server, admins see everything",
    "ja": "。通常、ユーザーには自分のサーバーのみが表示され、管理者にはすべてが表示されます。",
    "cn": "。用户通常只能看到他们的服务器，管理员可以看到一切"
  },
  "[SakuraBot] Đang lắng nghe luồng log từ Minecraft server": {
    "en": "[SakuraBot] Listening to the log stream from the Minecraft server",
    "ja": "[SakuraBot] Minecraft サーバーからのログ ストリームを聞いています",
    "cn": "[SakuraBot] 监听 Minecraft 服务器的日志流"
  },
  "Bật/tắt tổng thể ở tab Cài đặt chung. Dưới đây là chi tiết": {
    "en": "General toggle on/off in General Settings tab. Here are the details",
    "ja": "一般設定タブで一般のオン/オフを切り替えます。詳細は次のとおりです。",
    "cn": "在常规设置选项卡中打开/关闭常规开关。这是详细信息"
  },
  "Bảo trì máy chủ định kỳ để tối ưu hóa hiệu suất và bảo mật": {
    "en": "Regular server maintenance to optimize performance and security",
    "ja": "パフォーマンスとセキュリティを最適化するための定期的なサーバー メンテナンス。",
    "cn": "定期服务器维护以优化性能和安全性"
  },
  "Đổi nickname nạn nhân (cần bot có quyền Manage Nicknames)": {
    "en": "Change the victim's nickname (requires bot to have Manage Nicknames permission)",
    "ja": "被害者のニックネームを変更します (ボットにニックネームの管理権限が必要です)。",
    "cn": "更改受害者的昵称（需要机器人具有管理昵称权限）"
  },
  "Sakura MC Console — Đang kết nối đến WebSocket server...": {
    "en": "Sakura MC Console — Connecting to WebSocket server...",
    "ja": "さくら MC コンソール — WebSocket サーバーに接続中...",
    "cn": "Sakura MC 控制台 — 正在连接到 WebSocket 服务器..."
  },
  "Sakura MC Console — Đang kết nối đến WebSocket server": {
    "en": "Sakura MC Console — Connecting to WebSocket server",
    "ja": "さくら MC コンソール — WebSocket サーバーに接続中",
    "cn": "Sakura MC Console — 连接到 WebSocket 服务器"
  },
  "Cổng mạng để người chơi kết nối vào game (mặc định 25565)": {
    "en": "Network port for players to connect to the game (default 25565)",
    "ja": "プレーヤーがゲームに接続するためのネットワーク ポート (デフォルトは 25565)。",
    "cn": "玩家连接游戏的网络端口（默认25565）"
  },
  "Cổng kết nối dành riêng cho console RCON (mặc định 25575)": {
    "en": "Connection port reserved for RCON console (default 25575)",
    "ja": "RCON コンソール用に予約されている接続ポート (デフォルトは 25575)。",
    "cn": "RCON控制台专用连接端口（默认25575）"
  },
  "Dán link YouTube để xem mô tả chi tiết của video hiện tại": {
    "en": "Paste the YouTube link to see a detailed description of the current video",
    "ja": "YouTube リンクを貼り付けると、現在のビデオの詳細な説明が表示されます。",
    "cn": "粘贴 YouTube 链接以查看当前视频的详细说明"
  },
  "Tránh kick người chơi nếu server nghi ngờ họ bay lơ lửng": {
    "en": "Avoid kicking players if the server suspects they are floating",
    "ja": "サーバーがプレイヤーがフローティングしていると疑う場合は、プレイヤーをキックしないでください。",
    "cn": "如果服务器怀疑玩家漂浮，请避免踢他们"
  },
  "Sau khi rút bài, hãy bấm AI luận giải để nhận thông điệp": {
    "en": "After drawing the cards, press AI interpretation to receive the message",
    "ja": "カードを引いたらAI通訳を押すとメッセージが届きます。",
    "cn": "抽牌后按AI解读即可接收消息"
  },
  "Vật phẩm troll dùng để tặng hoặc gắn vào cần người khác": {
    "en": "Troll items are used to give or attach to other people's rods",
    "ja": "トロール アイテムは、他の人にロッドを与えたり、ロッドに取り付けたりするために使用されます。",
    "cn": "巨魔物品用于赠送或附加到其他人的鱼竿上"
  },
  "Kích nổ quả bom cảm tử trừ coin ngẫu nhiên của cả 2 bên": {
    "en": "Detonate a suicide bomb that deducts random coins from both sides",
    "ja": "自爆爆弾を爆発させると、両側からランダムなコインが減ります。",
    "cn": "引爆自杀式炸弹，双方随机扣除硬币"
  },
  "Kênh Nội Quy & Xác Minh Thành Viên (Rule Verification)": {
    "en": "Rules & Member Verification Channel (Rule Verification)",
    "ja": "ルールとメンバー検証チャンネル (ルール検証)",
    "cn": "频道规则&会员验证（规则验证）"
  },
  "Ví dụ: linhxinh hoặc Discord ID (1144785664458637394)": {
    "en": "For example: linhxinh or Discord ID (1144785664458637394)",
    "ja": "例: linhxinh または Discord ID (1144785664458637394)",
    "cn": "例如：linhxinh 或 Discord ID (1144785664458637394)"
  },
  "Lệnh Admin cấu hình và nạp lại hệ thống ngồi in-game.": {
    "en": "Admin command to configure and reload the in-game system.",
    "ja": "ゲーム内システムを設定およびリロードするための管理コマンド。",
    "cn": "用于配置和重新加载游戏内系统的管理命令。"
  },
  "Lệnh Admin cấu hình và nạp lại hệ thống ngồi in-game": {
    "en": "Admin command to configure and reload the in-game system",
    "ja": "ゲーム内システムを設定およびリロードするための管理コマンド。",
    "cn": "用于配置和重新加载游戏内系统的管理命令"
  },
  "Xem bảng xếp hạng và các chỉ số quan trọng trong server": {
    "en": "View rankings and important indicators in the server",
    "ja": "サーバー内のランキングと重要な指標を表示します。",
    "cn": "查看服务器内的排名及重要指标"
  },
  "Ví dụ: Chỉ câu được vào mùa bão, Hoặc mua từ Chợ Đen": {
    "en": "For example: Can only fish during storm season, Or buy from the Black Market",
    "ja": "例: 嵐の季節にしか釣りができない、またはブラック マーケットから購入できる",
    "cn": "例如：只能在暴风雨季节钓鱼，或者从黑市购买"
  },
  "Sakura Bot - Bảng Điều Khiển Quản Lý (Web Dashboard)": {
    "en": "Sakura Bot - Management Dashboard (Web Dashboard)",
    "ja": "さくらボット - 管理ダッシュボード（Webダッシュボード）",
    "cn": "Sakura Bot - 管理仪表板（Web 仪表板）"
  },
  "Timeout / Mute tạm thời nạn nhân trong server Discord": {
    "en": "Timeout / Temporarily Mute the victim in the Discord server",
    "ja": "タイムアウト / Discord サーバーで被害者を一時的にミュートします。",
    "cn": "超时/暂时将 Discord 服务器中的受害者静音"
  },
  "Kênh Ghi Nhật Ký Game (Join, Quit, Chết, Thành tựu):": {
    "en": "Game Log Channel (Join, Quit, Death, Achievement):",
    "ja": "ゲームログチャンネル (参加、終了、死亡、達成):",
    "cn": "游戏日志通道（加入、退出、死亡、成就）："
  },
  "Kênh Ghi Nhật Ký Game (Join, Quit, Chết, Thành tựu)": {
    "en": "Game Log Channel (Join, Quit, Death, Achievement)",
    "ja": "ゲームログチャンネル (参加、終了、死亡、達成)",
    "cn": "游戏日志通道（加入、退出、死亡、成就）"
  },
  "Ẩn vật phẩm khỏi Cửa Hàng (Người chơi không thể mua)": {
    "en": "Hide items from the Store (Players cannot buy)",
    "ja": "ストアからアイテムを非表示にする (プレイヤーは購入できません)",
    "cn": "隐藏商店中的物品（玩家无法购买）"
  },
  "Tìm kiếm thành tựu theo tên, mô tả hoặc danh hiệu...": {
    "en": "Search achievements by name, description or title...",
    "ja": "名前、説明、タイトルで実績を検索...",
    "cn": "按名称、描述或标题搜索成就..."
  },
  "Tìm kiếm thành tựu theo tên, mô tả hoặc danh hiệu": {
    "en": "Search achievements by name, description or title",
    "ja": "名前、説明、タイトルで実績を検索",
    "cn": "按名称、描述或标题搜索成就"
  },
  "Chế độ chơi khởi đầu khi người chơi tham gia thế giới": {
    "en": "The game mode begins when the player joins the world",
    "ja": "ゲームモードは、プレイヤーがワールドに参加すると始まります。",
    "cn": "当玩家加入世界时游戏模式开始"
  },
  "Ảnh hưởng lượng sát thương và mức độ quái vật sinh ra": {
    "en": "Affects the amount of damage and level of monsters spawned",
    "ja": "ダメージ量と出現するモンスターのレベルに影響します。",
    "cn": "影响生成的怪物的伤害量和等级"
  },
  "Cần thiết để bot điều khiển server và chạy lệnh từ xa": {
    "en": "Necessary for the bot to control the server and run commands remotely",
    "ja": "ボットがサーバーを制御し、コマンドをリモートで実行するために必要です。",
    "cn": "机器人远程控制服务器和运行命令所必需的"
  },
  "Đăng ký tài khoản để sử dụng các tính năng của server": {
    "en": "Register an account to use the server's features",
    "ja": "サーバーの機能を使用するにはアカウントを登録します。",
    "cn": "注册帐户以使用服务器功能"
  },
  "Cơ sở dữ liệu này hiện chưa có bảng hoặc dữ liệu nào": {
    "en": "This database currently has no tables or data",
    "ja": "現在、このデータベースにはテーブルやデータがありません。",
    "cn": "该数据库当前没有表或数据"
  },
  "Scribble It! — Trò chơi Vẽ & Đoán từ như Skribbl.io": {
    "en": "Scribble It! — Drawing & Guessing Word Games like Skribbl.io",
    "ja": "落書きしてみよう！ — Skribbl.io のような描画と推測の単語ゲーム",
    "cn": "乱写它！ — 像 Skribbl.io 这样的绘画和猜测文字游戏"
  },
  "và Slash commands được đồng bộ trực tiếp từ hệ thống": {
    "en": "and Slash commands are synchronized directly from the system",
    "ja": "およびスラッシュ コマンドはシステムから直接同期されます。",
    "cn": "和 Slash 命令直接从系统同步"
  },
  "trong 10 phút. Bị chặn bởi Khiên hoặc Gương phản đòn": {
    "en": "for 10 minutes. Blocked by Shield or Counterattack Mirror",
    "ja": "10分間。シールドまたは反撃ミラーでブロックされる",
    "cn": "10分钟。被盾牌或反射镜阻挡"
  },
  "[Sakura MC] Đang khởi tạo kết nối Terminal Console": {
    "en": "[Sakura MC] Initializing Terminal Console connection",
    "ja": "[さくらMC] ターミナルコンソール接続を初期化しています",
    "cn": "[Sakura MC] 初始化终端控制台连接"
  },
  "Liên kết tải trực tiếp tệp .zip texture pack máy chủ": {
    "en": "Direct download link for the server texture pack .zip file",
    "ja": "サーバー テクスチャ パック .zip ファイルの直接ダウンロード リンク。",
    "cn": "服务器纹理包 .zip 文件的直接下载链接"
  },
  "Truy vấn hợp lệ nhưng không trả về dòng dữ liệu nào": {
    "en": "The query is valid but returns no rows of data",
    "ja": "クエリは有効ですが、データ行が返されません。",
    "cn": "查询有效，但没有返回任何数据行"
  },
  "Đá nạn nhân văng ra khỏi phòng Voice đang đàm thoại": {
    "en": "Kick the victim out of the room where Voice is talking",
    "ja": "ボイスが話している部屋から被害者を追い出します。",
    "cn": "将受害者踢出 Voice 正在说话的房间"
  },
  "Mật khẩu xác thực cho kết nối điều khiển RCON từ xa": {
    "en": "Authentication password for remote RCON control connection",
    "ja": "リモート RCON 制御接続用の認証パスワード。",
    "cn": "远程RCON控制连接的验证密码"
  },
  "Xem danh sách các khu vực đã claim và quản lý chúng": {
    "en": "View a list of claimed areas and manage them",
    "ja": "権利主張のある地域のリストを表示し、管理します。",
    "cn": "查看已声明区域的列表并对其进行管理"
  },
  "Làm sao để bot gán vai trò khi lên cấp (Level Role)": {
    "en": "How can the bot assign roles when leveling up (Level Role)",
    "ja": "レベルアップ時にボットはどのように役割を割り当てることができますか (レベル役割)",
    "cn": "如何让机器人在升级时分配角色（Level Role）"
  },
  "Đổi tên tài khoản. Không được trùng với người khác": {
    "en": "Rename account. Do not overlap with others",
    "ja": "アカウントの名前を変更します。他の人と重ならないようにしてください。",
    "cn": "重命名帐户。不要与其他人重叠"
  },
  "Không tìm thấy dòng dữ liệu nào khớp với điều kiện": {
    "en": "No data lines were found that matched the condition",
    "ja": "条件に一致するデータ行は見つかりませんでした。",
    "cn": "没有找到符合条件的数据线"
  },
  "Cầu Vồng Thần Nông (x1.5 tốc độ & Siêu Đột Biến!)": {
    "en": "Rainbow Scorpio (x1.5 speed & Super Mutation!)",
    "ja": "レインボースコーピオ (x1.5 スピード & スーパーミューテーション!)",
    "cn": "天蝎座的彩虹（x1.5速度和超级突变！）"
  },
  "Nhập Tên Đăng Nhập (Username) hoặc Discord User ID": {
    "en": "Enter Username or Discord User ID",
    "ja": "ユーザー名または Discord ユーザー ID を入力してください",
    "cn": "输入用户名或 Discord 用户 ID"
  },
  "Quản Lý Kênh Điểm Danh Giữ Chuỗi (Channel Streak)": {
    "en": "Channel Streak Management",
    "ja": "チャンネルストリーク管理",
    "cn": "管理出勤渠道连续记录（Channel Streak）"
  },
  "Tìm kiếm cao thủ theo Tên hoặc Discord User ID...": {
    "en": "Search for players by Name or Discord User ID...",
    "ja": "名前または Discord ユーザー ID でプレイヤーを検索...",
    "cn": "按名称或 Discord 用户 ID 搜索大师..."
  },
  "Tìm kiếm cao thủ theo Tên hoặc Discord User ID": {
    "en": "Search for players by Name or Discord User ID",
    "ja": "名前または Discord ユーザー ID でプレイヤーを検索",
    "cn": "按名称或 Discord 用户 ID 搜索大师"
  },
  "Nhập Discord User ID (ví dụ: 123456789012345678)": {
    "en": "Enter Discord User ID (ex: 123456789012345678)",
    "ja": "Discord ユーザー ID を入力してください (例: 123456789012345678)",
    "cn": "输入 Discord 用户 ID（例如：123456789012345678）"
  },
  "Nhập lời giới thiệu ngắn về bot trong server này": {
    "en": "Enter a short introduction about the bot in this server",
    "ja": "このサーバーのボットに関する簡単な紹介文を入力してください",
    "cn": "输入有关此服务器中机器人的简短介绍"
  },
  "Gửi ảnh hoặc âm thanh hù dọa bất ngờ tới nạn nhân": {
    "en": "Sending suddenly threatening images or sounds to the victim",
    "ja": "被害者に突然脅迫的な画像や音声を送信する。",
    "cn": "突然向受害者发送威胁性图像或声音"
  },
  "Tệp đính kèm (Ảnh, File tài liệu, Zip... < 25MB)": {
    "en": "Attachments (Photos, Document Files, Zip... < 25MB)",
    "ja": "添付ファイル (写真、ドキュメントファイル、Zip... < 25MB)",
    "cn": "附加文件（照片、文档文件、Zip...< 25MB）"
  },
  "Discord Bot Đa Năng • Online 24/7 • Tiếng Việt 🌸": {
    "en": "Discord Bot Multipurpose • Online 24/7 • Vietnamese 🌸",
    "ja": "Discord ボット多目的 • 24 時間 365 日オンライン • ベトナム語 🌸",
    "cn": "Discord Bot 多用途 • 在线 24/7 • 越南语 💕"
  },
  "Đặt vị trí nhà của bạn để có thể quay lại dễ dàng": {
    "en": "Set your home location so you can get back easily",
    "ja": "簡単に帰宅できるように自宅の場所を設定します。",
    "cn": "设置您的家庭位置，以便您可以轻松返回"
  },
  "trước. Mặc định đăng vào kênh Confession đã chọn": {
    "en": "before. By default, posting to the selected Confession channel",
    "ja": "前に。デフォルトでは、選択した告白チャンネルに投稿します。",
    "cn": "之前。默认情况下，发布到选定的告白频道"
  },
  "Xem số dư tài sản của bạn trong hệ thống tiền tệ": {
    "en": "View your asset balance in the currency system",
    "ja": "通貨システムで資産残高を表示します。",
    "cn": "查看您在货币系统中的资产余额"
  },
  "Trình duyệt của bạn không hỗ trợ thẻ video HTML5": {
    "en": "Your browser does not support HTML5 video tags",
    "ja": "お使いのブラウザは HTML5 ビデオ タグをサポートしていません。",
    "cn": "您的浏览器不支持 HTML5 视频标签"
  },
  "Nếu tắt, mọi invite đều bị xóa kể cả của server": {
    "en": "If turned off, all invites will be deleted, including those from the server",
    "ja": "オフにすると、サーバーからの招待も含め、すべての招待が削除されます。",
    "cn": "如果关闭，所有邀请都将被删除，包括来自服务器的邀请"
  },
  "Phần Thưởng Role Theo Mốc Cấp Độ (Level Roles)": {
    "en": "Level Roles Rewards",
    "ja": "レベルの役割報酬",
    "cn": "等级角色奖励"
  },
  "Quản Lý Từ Khóa Phản Hồi Tự Động (Custom Keys)": {
    "en": "Automatic Response Keyword Management (Custom Keys)",
    "ja": "自動応答キーワード管理 (カスタムキー)",
    "cn": "自定义按键"
  },
  "Nhập Discord User ID cần thủ để xem Thủy Cung": {
    "en": "Enter your Discord User ID to view the Aquarium",
    "ja": "水族館を表示するには、Discord ユーザー ID を入力してください",
    "cn": "输入钓鱼者的 Discord 用户 ID 以查看水族馆"
  },
  "Sakura Bot • Chúc bạn có những giây phút vui vẻ": {
    "en": "Sakura Bot • Wish you have fun moments",
    "ja": "さくらボット • 楽しいひとときをお過ごしください。",
    "cn": "Sakura Bot • Wish you have fun moments"
  },
  "Sakura MC — Cấu Hình server.properties & MOTD": {
    "en": "Sakura MC — Server.properties & MOTD Configuration",
    "ja": "さくら MC — Server.properties と MOTD 構成",
    "cn": "Sakura MC — Server.properties 和 MOTD 配置"
  },
  "Plugin giúp server của bạn mạnh hơn cùng Sakura": {
    "en": "Plugins help your server become more powerful with Sakura",
    "ja": "プラグインは、Sakura を使用してサーバーをより強力にするのに役立ちます。",
    "cn": "插件可帮助您的服务器通过 Sakura 变得更加强大"
  },
  "Thông tin thu thập chỉ phục vụ cho các mục đích": {
    "en": "Information collected is only for the following purposes",
    "ja": "収集される情報は、次の目的のみに使用されます。",
    "cn": "收集的信息仅用于一般目的"
  },
  "Hãy thử nhập từ khóa khác hoặc chuyển danh mục": {
    "en": "Try entering a different keyword or switching categories",
    "ja": "別のキーワードを入力するか、カテゴリを切り替えてみてください。",
    "cn": "尝试输入不同的关键字或切换类别"
  },
  "Thiết Lập Kênh Discord Kết Nối Với Minecraft": {
    "en": "Set up a Discord Channel Connecting to Minecraft",
    "ja": "Minecraft に接続する Discord チャンネルをセットアップする",
    "cn": "Set Up a Discord Channel Connecting to Minecraft"
  },
  "Đồng Bộ & Quy Đổi Coins Discord <-> Minecraft": {
    "en": "Synchronize & Convert Coins Discord <-> Minecraft",
    "ja": "コインの同期と変換 Discord <-> Minecraft",
    "cn": "Sync & Convert Coins Discord <-> Minecraft"
  },
  "Cấu Hình Thông Báo Giftcode Hoyoverse & Gacha": {
    "en": "Hoyoverse & Gacha Giftcode Notification Configuration",
    "ja": "Hoyoverse & ガチャギフトコード通知設定",
    "cn": "配置礼品代码通知 Hoyoverse 和 Gacha"
  },
  "Ví dụ: Discord Nitro, Thẻ Cào, 100.000 Coins": {
    "en": "For example: Discord Nitro, Scratch Card, 100,000 Coins",
    "ja": "例: Discord Nitro、スクラッチ カード、100,000 コイン",
    "cn": "例如：Discord Nitro、刮刮卡、100,000 个金币"
  },
  "Để trống để lắng nghe trên tất cả địa chỉ mạng": {
    "en": "Leave blank to listen on all network addresses",
    "ja": "すべてのネットワーク アドレスをリッスンするには、空白のままにします。",
    "cn": "Leave blank to listen on all network addresses"
  },
  "Giới hạn số lượng người chơi tham gia cùng lúc": {
    "en": "Limit the number of players participating at the same time",
    "ja": "同時に参加するプレイヤーの数を制限します。",
    "cn": "限制同时参与的玩家数量"
  },
  "Cho phép hoặc cấm người chơi tấn công lẫn nhau": {
    "en": "Allow or prohibit players from attacking each other",
    "ja": "プレイヤー同士の攻撃を許可または禁止します。",
    "cn": "允许或禁止玩家互相攻击"
  },
  "Tự động sinh ra Zombie, Skeleton, Creeper, v.v": {
    "en": "Automatically spawn Zombies, Skeletons, Creepers, etc",
    "ja": "ゾンビ、スケルトン、クリーパーなどを自動的にスポーンします。",
    "cn": "自动生成僵尸、骷髅、苦力怕等"
  },
  "Tạo điểm warp để người chơi khác có thể đi đến": {
    "en": "Create warp points that other players can go to",
    "ja": "他のプレイヤーが行けるワープポイントを作成します。",
    "cn": "Create warp points that other players can go to"
  },
  "Nhập câu lệnh SQL chỉ đọc (SELECT / PRAGMA)": {
    "en": "Enter a read-only SQL statement (SELECT / PRAGMA)",
    "ja": "読み取り専用 SQL ステートメント (SELECT / PRAGMA) を入力してください",
    "cn": "Enter read-only SQL statements (SELECT / PRAGMA)"
  },
  "Caro XO (3×3 & Siêu Lớn 15×15) — Sakura Game": {
    "en": "Caro XO (3×3 & Super Large 15×15) — Sakura Game",
    "ja": "カロ XO (3×3 & 超大型 15×15) — サクラゲーム",
    "cn": "Caro XO（3×3＆超大15×15）—樱花游戏"
  },
  "© 2026 Sakura Bot • Phát triển bởi Đồng Linh": {
    "en": "© 2026 Sakura Bot • Developed by Dong Linh",
    "ja": "© 2026 さくらボット • 開発者: Dong Linh",
    "cn": "© 2026 Sakura Bot • Developed by Dong Linh"
  },
  "Gửi tin nhắn troll hài hước kèm hiệu ứng động": {
    "en": "Send funny troll messages with animated effects",
    "ja": "アニメーション効果を使って面白い荒らしメッセージを送信します。",
    "cn": "Send funny troll messages with animated effects"
  },
  "Ví dụ: \"Xin chào Sakura\" -> \"arukaS oàhc niX\"": {
    "en": "For example: \"Hello Sakura\" -> \"arukaS oàhc niX\"",
    "ja": "例：「こんにちはさくら」→「arukaS oàhc niX」。",
    "cn": "For example: \"Hello Sakura\" -> \"arukaS oahc niX\""
  },
  "Troll thông báo đỏ mà vào không thấy tin nhắn": {
    "en": "Troll notices red but doesn't see the message",
    "ja": "トロルは赤いことに気づきましたが、メッセージは見えませんでした。",
    "cn": "Troll notices red but doesn't see the message"
  },
  "Tìm kiếm theo Discord ID hoặc tên bạn đời...": {
    "en": "Search by Discord ID or partner name...",
    "ja": "Discord IDまたはパートナー名で検索...",
    "cn": "按 Discord ID 或合作伙伴名称搜索..."
  },
  "Tìm kiếm theo Discord ID hoặc tên bạn đời": {
    "en": "Search by Discord ID or partner name",
    "ja": "Discord IDまたはパートナー名で検索",
    "cn": "按 Discord ID 或好友姓名搜索"
  },
  "của máy chủ Paper/Spigot/Bukkit bạn đang chạy": {
    "en": "of the Paper/Spigot/Bukkit server you are running",
    "ja": "実行している Paper/Spigot/Bukkit サーバーの。",
    "cn": "您正在运行的 Paper/Spigot/Bukkit 服务器的"
  },
  "Trao đổi vật phẩm an toàn với người chơi khác": {
    "en": "Safely exchange items with other players",
    "ja": "他のプレイヤーと安全にアイテムを交換できます。",
    "cn": "与其他玩家安全交换物品"
  },
  "Tệp này là một Extension Cog của SakuraBot:": {
    "en": "This file is an Extension Cog of SakuraBot:",
    "ja": "このファイルはSakuraBotの拡張Cogです:",
    "cn": "该文件是 SakuraBot 的扩展齿轮："
  },
  "Tệp này là một Extension Cog của SakuraBot": {
    "en": "This file is an Extension Cog of SakuraBot",
    "ja": "このファイルはSakuraBotの拡張Cogです",
    "cn": "该文件是 SakuraBot 的扩展齿轮"
  },
  "Phân quyền Quản trị & Owner hoạt động ra sao": {
    "en": "How does decentralization of Administration & Ownership work",
    "ja": "管理と所有権の分散化はどのように機能しますか",
    "cn": "管理和所有权的分散化如何运作？"
  },
  "Áp Dụng Môi Trường Nông Nghiệp Ngay Lập Tức": {
    "en": "Apply Agricultural Environment Immediately",
    "ja": "農業環境をすぐに適用する",
    "cn": "农业环境直接应用"
  },
  "Nhập mã (ví dụ: ABC123 hoặc MCLINK-ABC123)": {
    "en": "Enter the code (e.g. ABC123 or MCLINK-ABC123)",
    "ja": "コードを入力してください (例: ABC123 または MCLINK-ABC123)",
    "cn": "输入代码（例如 ABC123 或 MCLINK-ABC123）"
  },
  "Sakura MC — Quản Lý Người Chơi & Soi Túi Đồ": {
    "en": "Sakura MC — Player Management & Inventory Check",
    "ja": "さくら MC — 選手管理と在庫チェック",
    "cn": "Sakura MC — 玩家管理和库存检查"
  },
  "Sakura Hosting — Quản Lý Máy Chủ Minecraft": {
    "en": "Sakura Hosting — Minecraft Server Management",
    "ja": "さくらホスティング — Minecraft サーバー管理",
    "cn": "Sakura Hosting — Minecraft 服务器管理"
  },
  "Cuốc Khai Khoáng (Hỗ trợ Cường Hóa & Sao)": {
    "en": "Mining Pickaxe (Supports Enhancement & Stars)",
    "ja": "採掘ツルハシ (強化とスターをサポート)",
    "cn": "采矿镐（支持增强和星星）"
  },
  "Kênh Chat 2 Chiều (Discord <-> Minecraft):": {
    "en": "2-Way Chat Channel (Discord <-> Minecraft):",
    "ja": "双方向チャットチャンネル (Discord <-> Minecraft):",
    "cn": "2 向聊天频道（Discord <-> Minecraft）："
  },
  "Kênh Chat 2 Chiều (Discord <-> Minecraft)": {
    "en": "2-Way Chat Channel (Discord <-> Minecraft)",
    "ja": "双方向チャットチャンネル (Discord <-> Minecraft)",
    "cn": "2 向聊天频道（Discord <-> Minecraft）"
  },
  "Mã Liên Kết (MCLINK-XXXXXX) hoặc Key Server": {
    "en": "Link Code (MCLINK-XXXX) or Server Key",
    "ja": "リンク コード (MCLINK-XXXX) またはサーバー キー",
    "cn": "链接代码 (MCLINK-XXXX) 或服务器密钥"
  },
  "Trợ lý Discord đa năng cho server của bạn.": {
    "en": "Versatile Discord Assistant for your server.",
    "ja": "サーバー用の多機能な Discord アシスタント。",
    "cn": "适用于您的服务器的多功能 Discord 助手。"
  },
  "Trợ lý Discord đa năng cho server của bạn": {
    "en": "Versatile Discord Assistant for your server",
    "ja": "サーバー用の多機能な Discord アシスタント。",
    "cn": "适用于您服务器的多功能 Discord 助手"
  },
  "Chưa có dữ liệu — bot sẽ ghi khi có vi phạm": {
    "en": "No data yet — bot will record when there is a violation",
    "ja": "データはまだありません。違反があった場合はボットが記録します。",
    "cn": "尚无数据 - 机器人将记录违规情况"
  },
  "Vui lòng nhập mật khẩu quản trị để tiếp tục": {
    "en": "Please enter your admin password to continue",
    "ja": "続行するには管理者パスワードを入力してください。",
    "cn": "请输入您的管理员密码以继续"
  },
  "Ví dụ: Nhẫn Cỏ, Nhẫn Vàng, Nhẫn Kim Cương": {
    "en": "For example: Grass Ring, Gold Ring, Diamond Ring",
    "ja": "例: グラスリング、ゴールドリング、ダイヤモンドリング",
    "cn": "例如：草戒、金戒、钻戒"
  },
  "Sakura MC — Phân Quyền & Quản Lý Truy Cập": {
    "en": "Sakura MC — Decentralization & Access Management",
    "ja": "さくら MC — 分散化とアクセス管理",
    "cn": "Sakura MC — 去中心化和访问管理"
  },
  "Chuyển tiền cho người chơi khác trên server": {
    "en": "Transfer money to other players on the server",
    "ja": "サーバー上の他のプレイヤーに送金します。",
    "cn": "向服务器上的其他玩家转账"
  },
  "Gửi yêu cầu dịch chuyển đến người chơi khác": {
    "en": "Send a teleport request to another player",
    "ja": "別のプレイヤーにテレポート要求を送信します。",
    "cn": "向其他玩家发送传送请求"
  },
  "Chấp nhận yêu cầu dịch chuyển từ người khác": {
    "en": "Accept teleport requests from others",
    "ja": "他の人からのテレポート要求を受け入れます。",
    "cn": "接受他人的传送请求"
  },
  "Đăng nhập vào tài khoản đã đăng ký trước đó": {
    "en": "Log in to the previously registered account",
    "ja": "先ほど登録したアカウントにログインします。",
    "cn": "登录之前注册的账号"
  },
  "Đổi mật khẩu tài khoản riêng của người chơi": {
    "en": "Change the player's own account password",
    "ja": "プレイヤー自身のアカウントのパスワードを変更します。",
    "cn": "修改玩家自己的账号密码"
  },
  "Vật phẩm troll ẩn (Chỉ rơi từ Rương/Drop)": {
    "en": "Hidden troll item (Only drops from Chest/Drop)",
    "ja": "隠しトロールアイテム (チェスト/ドロップからのみドロップ)",
    "cn": "隐藏的巨魔物品（仅从宝箱/掉落物中掉落）"
  },
  "Công dụng, nguồn gốc hoặc lưu ý canh tác": {
    "en": "Uses, origin or cultivation notes",
    "ja": "用途、産地、栽培上の注意点",
    "cn": "用途、产地或栽培说明"
  },
  "Gửi tin nhắn từ Web vào server Minecraft": {
    "en": "Sending messages from the Web to the Minecraft server",
    "ja": "Web から Minecraft サーバーにメッセージを送信しています",
    "cn": "从 Web 向 Minecraft 服务器发送消息"
  },
  "Tính năng Custom Key hoạt động như thế nào": {
    "en": "How does the Custom Key feature work",
    "ja": "カスタム キー機能はどのように機能しますか",
    "cn": "自定义按键功能如何工作？"
  },
  "Làm thế nào để xem toàn bộ danh sách lệnh": {
    "en": "How to see the entire command list",
    "ja": "コマンドリスト全体を確認するにはどうすればよいですか",
    "cn": "如何查看整个命令列表"
  },
  "GOD MODE 100% (Đập Đồ & Sao Không Trượt)": {
    "en": "GOD MODE 100% (Smash Things & Stars Don't Slip)",
    "ja": "GOD MODE 100% (スマッシュシングス&スターは滑らない)",
    "cn": "上帝模式 100%（粉碎物品且星星不滑落）"
  },
  "Vật phẩm ẩn (Không bán ở shop công khai)": {
    "en": "Hidden items (Not sold in public shops)",
    "ja": "隠しアイテム（一般のショップでは販売されていません）",
    "cn": "隐藏物品（不在公共商店出售）"
  },
  "Mã định danh ID (troll_... hoặc item_...)": {
    "en": "ID identifier (troll_... or item_...)",
    "ja": "ID 識別子 (troll_... または item_...)",
    "cn": "ID 标识符（troll_... 或 item_...）"
  },
  "ID Kênh Lưu Log Toàn Cục (Log Channel ID)": {
    "en": "Global Log Channel ID (Log Channel ID)",
    "ja": "グローバル ログ チャネル ID (ログ チャネル ID)",
    "cn": "全局日志通道ID（Log Channel ID）"
  },
  "Groq API Key (Dùng cho AI Chat & Xem bói)": {
    "en": "Groq API Key (Used for AI Chat & Fortune Telling)",
    "ja": "Groq API キー (AI チャットと占いに使用)",
    "cn": "Groq API 密钥（用于 AI 聊天和算命）"
  },
  "Danh Sách Người Dùng & Quản Trị Viên Web": {
    "en": "List of Users & Web Admins",
    "ja": "ユーザーとウェブ管理者のリスト",
    "cn": "用户和网站管理员列表"
  },
  "Số ký tự kết hợp (◌̃◌́) vượt ngưỡng → xóa": {
    "en": "The number of combined characters (◌̃◌́) exceeds the threshold → delete",
    "ja": "結合文字数(◌̃◌́)が閾値を超えている→削除。",
    "cn": "组合字符数(◌̃◌́)超过阈值→删除"
  },
  "Cấu Hình Tự Động Gán Vai Trò (Auto Role)": {
    "en": "Automatic Role Assignment Configuration (Auto Role)",
    "ja": "自動役割割り当て構成 (自動役割)",
    "cn": "自动角色配置"
  },
  "Tạo Bảng Tự Chọn Vai Trò (Reaction Role)": {
    "en": "Create a Reaction Role Table",
    "ja": "リアクションロールテーブルを作成する",
    "cn": "创建反应角色表"
  },
  "Ví dụ: Rơi từ Rương Atlantis, Boss biển": {
    "en": "For example: Dropped from Atlantis Chest, Sea Boss",
    "ja": "例: アトランティスのチェスト、シーボスからドロップ",
    "cn": "示例：从亚特兰蒂斯宝箱掉落，海王"
  },
  "Ví dụ: Rơi từ Rương Hỗn Loạn, Mini-game": {
    "en": "For example: Drops from Chaos Chests, Mini-games",
    "ja": "例: カオスチェストからのドロップ、ミニゲーム",
    "cn": "示例：从迷你游戏的混沌宝箱中掉落"
  },
  "Nội dung chi tiết bên trong khung Embed": {
    "en": "Detailed content inside the Embed frame",
    "ja": "埋め込みフレーム内の詳細なコンテンツ",
    "cn": "嵌入框架内的详细内容"
  },
  ", sách phù phép và custom items độc quyền": {
    "en": ", spell books and exclusive custom items",
    "ja": "、魔法の本、限定のカスタムアイテム。",
    "cn": "、咒语书和独家定制物品"
  },
  "Cách cài đặt kênh câu cá và nhận Giftcode": {
    "en": "How to install fishing channel and receive Giftcode",
    "ja": "釣りチャンネルをインストールしてギフトコードを受け取るにはどうすればよいですか",
    "cn": "如何安装钓鱼频道并接收礼品码"
  },
  "Sakura Bot — Quản Lý Tệp & Nạp Lại Cogs": {
    "en": "Sakura Bot — File Management & Cogs Reload",
    "ja": "さくらボット — ファイル管理と歯車のリロード",
    "cn": "Sakura Bot — 文件管理和 Cogs 重新加载"
  },
  "Mô tả sinh vật biển sẽ xuất hiện tại đây": {
    "en": "Descriptions of marine life will appear here",
    "ja": "海洋生物の説明がここに表示されます。",
    "cn": "海洋生物的描述将出现在这里"
  },
  "Troll thành viên hám quà trong kênh chat": {
    "en": "Troll members greedy for gifts in the chat channel",
    "ja": "チャット チャンネルでギフトを貪欲に狙うトロール メンバー。",
    "cn": "巨魔成员在聊天频道中贪图礼物"
  },
  "Mở Bảng Quản Lý Từ Điển & BXH Nối Chữ ➔": {
    "en": "Open the Dictionary Management Board & Letter Connection Chart ➔",
    "ja": "辞書管理ボードと文字接続表を開く ➔",
    "cn": "打开词典管理板和字母匹配表 ➔"
  },
  "VD: 8 ký tự trở lên và >70% là hoa → xóa": {
    "en": "For example: 8 characters or more and >70% are capital letters → delete",
    "ja": "例: 8 文字以上かつ 70% 以上が大文字 → 削除。",
    "cn": "例如：8个字符或更多且>70%为大写字母→删除"
  },
  "Bị cấm sẽ không dùng được lệnh bot (trừ": {
    "en": "If you are banned, you will not be able to use bot commands (except",
    "ja": "禁止された場合、ボットコマンドを使用できなくなります（例外を除きます）",
    "cn": "如果您被禁止，您将无法使用机器人命令（除了"
  },
  "Mua hoặc bảo vệ khu đất hiện tại của bạn": {
    "en": "Buy or secure your existing land",
    "ja": "既存の土地を購入または確保します。",
    "cn": "购买或保护您现有的土地"
  },
  "Mở menu cá nhân chứa các chức năng nhanh": {
    "en": "Opens a personal menu containing quick functions",
    "ja": "クイック機能を含む個人メニューを開きます。",
    "cn": "打开包含快速功能的个人菜单"
  },
  "Đề xuất tính năng mới (Feature Request)": {
    "en": "New feature proposal (Feature Request)",
    "ja": "新機能の提案 (機能リクエスト)",
    "cn": "功能请求"
  },
  "Đang tải danh sách lệnh từ Sakura Bot": {
    "en": "Loading command list from Sakura Bot",
    "ja": "さくらボットからコマンドリストを読み込み中",
    "cn": "从 Sakura Bot 加载命令列表"
  },
  "Nạn nhân bị ngắt kết nối voice đột ngột": {
    "en": "The victim's voice connection was suddenly disconnected",
    "ja": "被害者の音声接続が突然切断されました。",
    "cn": "受害者的语音连接突然断开"
  },
  "Nối Server Minecraft Với Discord Guild": {
    "en": "Connect Minecraft Server With Discord Guild",
    "ja": "Minecraft サーバーを Discord ギルドに接続する",
    "cn": "将 Minecraft 服务器与 Discord Guild 连接"
  },
  "Tìm kiếm tên, mô tả, nguồn rơi, key...": {
    "en": "Search for name, description, source, key...",
    "ja": "名前、説明、ソース、キーを検索...",
    "cn": "搜索名称、描述、来源、密钥..."
  },
  "Tìm kiếm tên, mô tả, nguồn rơi, key": {
    "en": "Search for name, description, source, key",
    "ja": "名前、説明、ソース、キーを検索",
    "cn": "搜索名称、描述、放置源、密钥"
  },
  "ví dụ: list hoặc say Xin chào mọi người": {
    "en": "for example: list or say Hello everyone",
    "ja": "例: リストするか、「皆さん、こんにちは!」と言ってください。",
    "cn": "例如：列出或向大家打招呼"
  },
  "Sakura MC — Console Điều Khiển Server": {
    "en": "Sakura MC — Server Control Console",
    "ja": "さくらMC — サーバーコントロールコンソール",
    "cn": "Sakura MC — 服务器控制台"
  },
  "3. Khi đã có plugin trên server, làm gì": {
    "en": "3. Once you have the plugin on the server, what to do",
    "ja": "3. プラグインをサーバー上に配置したら、何をすればよいでしょうか",
    "cn": "3. 将插件安装到服务器后，该怎么办？"
  },
  "Tìm theo tên, username (@slug), mô tả": {
    "en": "Search by name, username (@slug), description",
    "ja": "名前、ユーザー名 (@slug)、説明で検索",
    "cn": "按名称、用户名 (@slug)、描述搜索"
  },
  "Cần trợ giúp cấu hình bot cho máy chủ": {
    "en": "Need help configuring bot for server",
    "ja": "サーバー用にボットを構成するのにサポートが必要です",
    "cn": "需要帮助为服务器配置机器人"
  },
  "Trình duyệt không hỗ trợ thẻ video này": {
    "en": "The browser does not support this video tag",
    "ja": "ブラウザはこのビデオタグをサポートしていません。",
    "cn": "浏览器不支持该视频标签"
  },
  "Trạng Thái Hiện Diện (Presence Status)": {
    "en": "Presence Status",
    "ja": "プレゼンスステータス",
    "cn": "状态"
  },
  "). Theo dõi trạng thái kết nối Discord": {
    "en": "). Monitor Discord connection status",
    "ja": "）。 Discordの接続ステータスを監視します。",
    "cn": "）。监控 Discord 连接状态"
  },
  "Thú Cưng / Pet (Hỗ trợ Sao & Đột Phá)": {
    "en": "Pets (Support Stars & Breakthroughs)",
    "ja": "ペット (サポートスターとブレークスルー)",
    "cn": "宠物/宠物（支持明星和突破）"
  },
  "Nơi có thể kiếm / Điều kiện nhận rương": {
    "en": "Where to find / Conditions for receiving chests",
    "ja": "宝箱の入手場所・入手条件：",
    "cn": "哪里可以找到/接收宝箱的条件"
  },
  "Sao Lưu & Khôi Phục Máy Chủ (Backups)": {
    "en": "Server Backup & Restore (Backups)",
    "ja": "サーバーのバックアップと復元 (バックアップ)",
    "cn": "服务器备份与恢复（备份）"
  },
  "API Key Pterodactyl / Hosting (Nếu có)": {
    "en": "API Key Pterodactyl / Hosting (If available)",
    "ja": "API キー Pterodactyl / ホスティング (利用可能な場合)",
    "cn": "API 密钥 Pterodactyl / 托管（如果有）"
  },
  "Chọn Kênh Nhận Tin (Text + Chat Voice)": {
    "en": "Select Channel to Receive News (Text + Voice Chat)",
    "ja": "ニュースを受信するチャンネルを選択してください (テキスト + ボイスチャット)",
    "cn": "选择接收渠道（文字+语音聊天）"
  },
  "Nhập cụm 2 từ (vd: trà sữa, hoa sen)": {
    "en": "Enter a 2-word phrase (eg: milk tea, lotus)",
    "ja": "2 単語のフレーズを入力してください (例: ミルク ティー、ロータス)",
    "cn": "输入 2 个词的短语（例如：奶茶、莲花）"
  },
  "Bảng Mã Màu Minecraft (Nhấp để chèn §)": {
    "en": "Minecraft Color Code Table (Click to insert §)",
    "ja": "Minecraft カラーコード表 (クリックして§を挿入)",
    "cn": "Minecraft 颜色代码表（点击插入§）"
  },
  "Xem nhiệm vụ và nộp nhiệm vụ hàng ngày": {
    "en": "View tasks and submit daily tasks",
    "ja": "タスクを表示し、毎日のタスクを送信します。",
    "cn": "查看任务并提交每日任务"
  },
  "Vui lòng chọn một bảng để xem dữ liệu": {
    "en": "Please select a table to view data",
    "ja": "データを表示するにはテーブルを選択してください。",
    "cn": "请选择表格查看数据"
  },
  "CURSED_BAIT (Mồi nguyền rủa vớt rác)": {
    "en": "CURSED_BAIT (Cursed bait to pick up trash)",
    "ja": "CURSED_BAIT (ゴミを拾うための呪われた餌)",
    "cn": "CURSED_BAIT（被诅咒的垃圾捡拾诱饵）"
  },
  "Đang tải danh sách server Minecraft": {
    "en": "Loading Minecraft server list",
    "ja": "Minecraft サーバー リストを読み込んでいます",
    "cn": "加载 Minecraft 服务器列表"
  },
  "Danh Sách Người Chơi Đang Trực Tuyến": {
    "en": "List of Online Players",
    "ja": "オンラインプレイヤーのリスト",
    "cn": "在线玩家列表"
  },
  "Mã ID Thành Tựu (duy nhất, không dấu)": {
    "en": "Achievement ID code (unique, unsigned)",
    "ja": "実績 ID コード (一意、署名なし)",
    "cn": "成就 ID 代码（唯一，未签名）"
  },
  "để bot tham gia voice và đọc tin nhắn": {
    "en": "Let the bot join the voice and read the message",
    "ja": "ボットに音声を加えてメッセージを読んでもらいましょう。",
    "cn": "让机器人加入语音并阅读消息"
  },
  "Sakura MC — Bảng Điều Khiển Console": {
    "en": "Sakura MC — Console Control Panel",
    "ja": "さくら MC — コンソールコントロールパネル",
    "cn": "Sakura MC — 控制台面板"
  },
  "Tự động sinh ra Bò, Cừu, Lợn, Gà, v.v": {
    "en": "Automatically spawn Cows, Sheep, Pigs, Chickens, etc",
    "ja": "牛、羊、豚、鶏などを自動的にスポーンします。",
    "cn": "自动生成牛、羊、猪、鸡等"
  },
  "và lưu file .jar vào máy tính của bạn": {
    "en": "and save the .jar file to your computer",
    "ja": ".jar ファイルをコンピュータに保存します。",
    "cn": "并将 .jar 文件保存到您的计算机"
  },
  "ID Máy Chủ (Guild ID) & Cấu Hình Kênh": {
    "en": "Server ID (Guild ID) & Channel Configuration",
    "ja": "サーバーID (ギルドID) とチャンネル構成",
    "cn": "服务器 ID（公会 ID）和频道配置"
  },
  "Lịch Sử Hội Thoại Ticket (Transcript)": {
    "en": "Ticket Conversation History (Transcript)",
    "ja": "チケットの会話履歴 (トランスクリプト)",
    "cn": "票证对话历史记录（文字记录）"
  },
  "Ban quản trị Sakura Bot có toàn quyền": {
    "en": "Sakura Bot Administration Board has full authority",
    "ja": "さくらボット管理委員会は以下の全権限を持っています。",
    "cn": "Sakura Bot 管理拥有完全权限"
  },
  "Quản Lý & Nạp Lại Cogs / Extensions": {
    "en": "Manage & Reload Cogs / Extensions",
    "ja": "コグ/拡張機能の管理とリロード",
    "cn": "管理和重新加载齿轮/扩展"
  },
  "để thêm Sakura vào server và thử lại": {
    "en": "to add Sakura to the server and try again",
    "ja": "サーバーにさくらを追加して再試行してください。",
    "cn": "将 Sakura 添加到服务器并重试"
  },
  "Phần Thưởng Cố Định Của Daily Code:": {
    "en": "Daily Code Fixed Rewards:",
    "ja": "毎日のコード固定報酬:",
    "cn": "每日代码固定奖励："
  },
  "Phần Thưởng Cố Định Của Daily Code": {
    "en": "Daily Code Fixed Rewards",
    "ja": "毎日のコード固定報酬",
    "cn": "每日代码固定奖励"
  },
  "Cần Câu Cá (Hỗ trợ Cường Hóa & Sao)": {
    "en": "Fishing Rod (Support Enhancement & Stars)",
    "ja": "釣り竿（サポート強化＆スター）",
    "cn": "钓鱼竿（支持增强和星星）"
  },
  "Pet ẩn (Chỉ mở khóa từ Rương/Event)": {
    "en": "Hidden Pet (Only unlocked from Chests/Events)",
    "ja": "隠しペット (チェスト/イベントからのみロック解除)",
    "cn": "隐藏宠物（仅从宝箱/活动中解锁）"
  },
  "Giông Bão Dữ Dội (Có thể quật cây)": {
    "en": "Severe Thunderstorms (Can knock down trees)",
    "ja": "激しい雷雨（木を倒す可能性があります）",
    "cn": "强雷暴（可以击倒树木）"
  },
  "GOD MODE 100% (Đập Cuốc & Sao 100%)": {
    "en": "GOD MODE 100% (Smash Pickaxe & Stars 100%)",
    "ja": "GOD MODE 100% (ツルハシとスターをスマッシュ 100%)",
    "cn": "神模式 100%（选择和明星粉碎 100%）"
  },
  "Hướng dẫn 3 kiểu khớp & ví dụ Regex": {
    "en": "Tutorial on 3 match types & Regex examples",
    "ja": "3 つの一致タイプと正規表現の例に関するチュートリアル",
    "cn": "3 种匹配类型和正则表达式示例指南"
  },
  "Các khu vực / Kênh câu cá được phép": {
    "en": "Permitted Fishing Areas/Channels",
    "ja": "許可された釣り場/水路",
    "cn": "允许捕鱼的区域/渠道"
  },
  "Đã Liên Kết Qua Plugin MyVaultAddon": {
    "en": "Linked via MyVaultAddon Plugin",
    "ja": "MyVaultAddon プラグイン経由でリンクされています",
    "cn": "通过 MyVaultAddon 插件链接"
  },
  "Hướng dẫn kết nối máy chủ qua Plugin": {
    "en": "Instructions for connecting to the server via Plugin",
    "ja": "プラグイン経由でサーバーに接続する手順",
    "cn": "通过插件连接服务器的说明"
  },
  ", chuyển đổi coins hai chiều tức thì": {
    "en": ", instant two-way coin conversion",
    "ja": "、即時の双方向コイン変換。",
    "cn": "，即时双向硬币兑换"
  },
  "Nhận phần thưởng điểm danh hàng ngày": {
    "en": "Receive daily attendance rewards",
    "ja": "毎日の出席報酬を受け取ります。",
    "cn": "领取每日出勤奖励"
  },
  "ID Người Dùng & Tên Hiển Thị Discord": {
    "en": "Discord User ID & Display Name",
    "ja": "DiscordのユーザーIDと表示名",
    "cn": "不一致的用户 ID 和显示名称"
  },
  "Cờ Vua AI Đa Cấp Độ — Sakura Game": {
    "en": "Multi-Level AI Chess — Sakura Game",
    "ja": "マルチレベル AI チェス — サクラゲーム",
    "cn": "多层次AI棋-樱花游戏"
  },
  "FREEZE_FISHING (Đóng băng cần câu)": {
    "en": "FREEZE_FISHING (Freeze fishing rods)",
    "ja": "FREEZE_FISHING (釣り竿を凍結)",
    "cn": "FREEZE_FISHING（冻结钓鱼竿）"
  },
  "Hiển thị ảnh quái vật troll bất ngờ": {
    "en": "Shows a picture of a surprise troll monster",
    "ja": "驚きのトロール モンスターの写真を表示します。",
    "cn": "显示一张令人惊讶的巨魔怪物的图片"
  },
  "Mô Tả Chi Tiết / Điều Kiện Đạt Được": {
    "en": "Detailed Description / Qualifications",
    "ja": "詳しい説明/資格",
    "cn": "详细描述/资格"
  },
  "Map ID Điểm Danh (MAP_DIEM_DANH_ID)": {
    "en": "Map Attendance ID (MAP_DIEM_DANH_ID)",
    "ja": "マップ出席 ID (MAP_DIEM_DANH_ID)",
    "cn": "地图出勤 ID (MAP_DIEM_DANH_ID)"
  },
  "Cấu hình Hệ thống Câu cá (Fishing)": {
    "en": "Fishing System Configuration (Fishing)",
    "ja": "釣りシステム構成（釣り）",
    "cn": "钓鱼系统配置（钓鱼）"
  },
  "Danh Sách Custom Keys Đã Thiết Lập": {
    "en": "List of Custom Keys Set Up",
    "ja": "設定されたカスタムキーのリスト",
    "cn": "自定义按键集列表"
  },
  "Đăng Bảng Reaction Role Lên Server": {
    "en": "Post the Reaction Role Table to the Server",
    "ja": "リアクションロールテーブルをサーバーにポストする",
    "cn": "将反应角色表发布到服务器"
  },
  "Ví dụ: Mở Rương Hải Tặc, Boss rơi": {
    "en": "For example: Open Pirate Chest, Boss falls",
    "ja": "例: 海賊の宝箱を開けると、ボスが倒れます",
    "cn": "例如：打开海盗宝箱，Boss掉落"
  },
  "Ví dụ: Rơi hiếm từ Rương Atlantis": {
    "en": "For example: Rare drop from Atlantis Chest",
    "ja": "例: アトランティスチェストからのレアドロップ",
    "cn": "示例：亚特兰蒂斯宝箱中的稀有掉落物"
  },
  "Xem menu lệnh quản trị & AutoMod →": {
    "en": "View admin command menu & AutoMod →",
    "ja": "管理コマンドメニューと AutoMod を表示 →",
    "cn": "请参阅管理命令菜单和 AutoMod →"
  },
  "Tạo & Tùy Biến Sakura Bio Profile": {
    "en": "Create & Customize Sakura Bio Profile",
    "ja": "さくらプロフィールの作成とカスタマイズ",
    "cn": "创建和自定义樱花生物档案"
  },
  "Kết quả truy vấn sẽ hiển thị ở đây": {
    "en": "Query results will be displayed here",
    "ja": "クエリ結果がここに表示されます。",
    "cn": "查询结果将显示在这里"
  },
  "Tốc Độ (35s vẽ, x2 điểm đoán sớm)": {
    "en": "Speed (35 seconds to draw, x2 early guess points)",
    "ja": "スピード (描画まで 35 秒、早期推測ポイント x2)",
    "cn": "速度（35秒绘制，x2早期猜测点）"
  },
  ". Nhấn Lưu là áp dụng ngay lập tức": {
    "en": ". Click Save to apply immediately",
    "ja": "。 「保存」をクリックしてすぐに適用します。",
    "cn": "。点击保存立即申请"
  },
  "Tại sao không thấy server của mình": {
    "en": "Why can't I see my server",
    "ja": "自分のサーバーが表示されないのはなぜですか",
    "cn": "为什么我看不到我的服务器？"
  },
  "Nội Dung Hoạt Động (Activity Text)": {
    "en": "Activity Text",
    "ja": "アクティビティテキスト",
    "cn": "活动文本（活动文本）"
  },
  "Mã Code (Tùy chọn hoặc ngẫu nhiên)": {
    "en": "Code (Optional or random)",
    "ja": "コード (オプションまたはランダム)",
    "cn": "代码（可选或随机）"
  },
  "Chìa Khóa Kim Cương (key_diamond)": {
    "en": "Diamond Key (key_diamond)",
    "ja": "ダイヤモンドの鍵 (key_diamond)",
    "cn": "钻石钥匙 (key_diamond)"
  },
  "Rương Ẩn / Rương Sự Kiện Đặc Biệt": {
    "en": "Hidden Chests / Special Event Chests",
    "ja": "隠しチェスト/特別イベントチェスト",
    "cn": "隐藏宝箱/特殊活动宝箱"
  },
  "Xem thống kê vi phạm spam gần đây": {
    "en": "View recent spam violation statistics",
    "ja": "最近のスパム違反統計を表示する",
    "cn": "查看最近的垃圾邮件违规统计信息"
  },
  "Vai trò cho Người dùng mới (User)": {
    "en": "Roles for New Users (User)",
    "ja": "新規ユーザーの役割 (ユーザー)",
    "cn": "新用户的角色（用户）"
  },
  "Gửi Tin Nhắn / Thông Báo Đến Kênh": {
    "en": "Send Message / Notification To Channel",
    "ja": "チャンネルにメッセージ/通知を送信",
    "cn": "向频道发送消息/通知"
  },
  "Nội Dung Tin Nhắn (Văn bản thường)": {
    "en": "Message Content (Normal Text)",
    "ja": "メッセージの内容 (通常のテキスト)",
    "cn": "消息内容（普通文本）"
  },
  "Tìm kiếm từ vựng trong từ điển...": {
    "en": "Search vocabulary in the dictionary...",
    "ja": "辞書で語彙を検索...",
    "cn": "在字典中搜索词汇..."
  },
  "Tìm kiếm từ vựng trong từ điển": {
    "en": "Search vocabulary in the dictionary",
    "ja": "辞書で語彙を検索",
    "cn": "在字典中搜索词汇"
  },
  "Nhập câu trả lời tự động của bot": {
    "en": "Enter the bot's automatic response",
    "ja": "ボットの自動応答を入力してください",
    "cn": "输入机器人的自动回复"
  },
  "Kênh Chat 2 Chiều (Discord <-> MC)": {
    "en": "2-Way Chat Channel (Discord <-> MC)",
    "ja": "双方向チャットチャンネル (Discord <-> MC)",
    "cn": "2 向聊天频道（Discord <-> MC）"
  },
  "Dịch chuyển về nhà đã đặt trước đó": {
    "en": "Teleport to the previously booked home",
    "ja": "以前に予約した家にテレポートします。",
    "cn": "传送到之前预订的家"
  },
  "Nội dung tệp sẽ xuất hiện ở đây": {
    "en": "File contents will appear here",
    "ja": "ファイルの内容がここに表示されます",
    "cn": "文件内容将出现在这里"
  },
  "Vật Tư Khai Khoáng (TNT, Đèn...)": {
    "en": "Mining Supplies (TNT, Lamp...)",
    "ja": "鉱山用品 (TNT、ランプなど)",
    "cn": "采矿用品（TNT、灯...）"
  },
  "Tỉ Lệ Quặng Siêu Hiếm (Netherite)": {
    "en": "Super Rare Ore (Netherite) Ratio",
    "ja": "スーパーレア鉱石（ネザライト）比率：",
    "cn": "超级稀有矿石（下界合金）比例"
  },
  "Mưa Rào Mát Lành (Tự tưới nước)": {
    "en": "Cool Showers (Self-watering)",
    "ja": "クールシャワー (自動給水)",
    "cn": "凉爽淋浴（自动浇水）"
  },
  "Nắng Gắt Hạn Hán (Đất khô nhanh)": {
    "en": "Severe Sun Drought (Soil dries quickly)",
    "ja": "ひどい日照り（土壌がすぐに乾く）",
    "cn": "极度干旱（土壤很快干燥）"
  },
  "Token Điểm Danh (TOKEN_DIEM_DANH)": {
    "en": "Attendance Token (TOKEN_DIEM_DAMN)",
    "ja": "出席トークン (TOKEN_DIEM_DAMN)",
    "cn": "出席令牌 (TOKEN_DIEM_DAMN)"
  },
  "luôn được miễn phí Vote vĩnh viễn": {
    "en": "Voting is always free forever",
    "ja": "投票はいつでも永久に無料です。",
    "cn": "投票永远免费"
  },
  "Phát Hành Mã Code Gacha Thủ Công": {
    "en": "Released Manual Gacha Codes",
    "ja": "手動ガチャコードを公開しました",
    "cn": "已发布手动扭蛋代码 代码"
  },
  "Đính Kèm Tệp / Hình Ảnh / Video:": {
    "en": "Attach Files / Images / Videos:",
    "ja": "ファイル/画像/ビデオを添付:",
    "cn": "附加文件/图像/视频："
  },
  "Đính Kèm Tệp / Hình Ảnh / Video": {
    "en": "Attach Files / Images / Videos",
    "ja": "ファイル/画像/ビデオを添付",
    "cn": "附加文件/图像/视频"
  },
  "Loại Nhẫn Cưới (Tên hoặc Mã Nhẫn)": {
    "en": "Type of Wedding Ring (Name or Ring Code)",
    "ja": "結婚指輪の種類 (名前またはリングコード)",
    "cn": "结婚戒指的类型（名称或戒指代码）"
  },
  "Sakura Bot — Discord Bot Đa Năng": {
    "en": "Sakura Bot — Multipurpose Discord Bot",
    "ja": "さくらボット — 多目的 Discord ボット",
    "cn": "Sakura Bot — 多用途 Discord 机器人"
  },
  "Chính sách Bảo mật — Sakura Bot": {
    "en": "Privacy Policy — Sakura Bot",
    "ja": "プライバシーポリシー — さくらボット",
    "cn": "隐私政策 — Sakura Bot"
  },
  "của bạn cho bất kỳ bên thứ ba nào": {
    "en": "yours to any third party",
    "ja": "あなたの所有物を第三者に譲渡します。",
    "cn": "您向任何第三方透露的"
  },
  "Hồ Sơ Cộng Đồng (Của Người Khác)": {
    "en": "Community Profile (Other People's)",
    "ja": "コミュニティプロフィール (他の人の)",
    "cn": "社区简介（其他人的）"
  },
  "Tạo & Thiết Kế Trang Sakura Bio": {
    "en": "Create & Design Sakura Bio Page",
    "ja": "サクラバイオページの作成とデザイン",
    "cn": "创建和设计 Sakura Bio 页面"
  },
  "Thực Hiện Cấp Phát / Điều Chỉnh": {
    "en": "Perform Allocation / Adjustment",
    "ja": "割り当て/調整を実行する",
    "cn": "进行分配/调整"
  },
  "Hết hạn sau (giờ, 0 = vĩnh viễn)": {
    "en": "Expires in (hours, 0 = forever)",
    "ja": "有効期限が切れます (時間、0 = 永久)",
    "cn": "过期时间（小时，0 = 永远）"
  },
  "Tên loài cá (Kèm emoji đại diện)": {
    "en": "Fish species name (with representative emoji)",
    "ja": "魚種名（代表的な絵文字付き）：",
    "cn": "鱼类名称（包括代表性表情符号）"
  },
  "Chìa Khóa Cổ Đại (key_ancient)": {
    "en": "Ancient Key (key_ancient)",
    "ja": "古代の鍵 (key_ancient)",
    "cn": "古代钥匙（key_ancient）"
  },
  "Hệ Số Đập Đồ (Refine Multiplier)": {
    "en": "Refine Multiplier",
    "ja": "乗数を調整",
    "cn": "精炼乘数"
  },
  "Hệ Số Tiến Sao (Star Multiplier)": {
    "en": "Star Multiplier",
    "ja": "スターマルチプライヤー",
    "cn": "星倍增器"
  },
  "Vận May Đào Mỏ (Sản lượng quặng)": {
    "en": "Mining Luck (Ore output)",
    "ja": "採掘運（鉱石産出量）：",
    "cn": "采矿运气（矿石产量）"
  },
  "Số ô chứa mở rộng (+extra slots)": {
    "en": "Number of expansion slots (+extra slots)",
    "ja": "拡張スロットの数 (+ 追加スロット)",
    "cn": "扩展插槽数量（+额外插槽）"
  },
  "Cả 2 người bị nổ trừ 50,000 coin": {
    "en": "Both people exploded minus 50,000 coins",
    "ja": "二人ともマイナス5万コイン爆発しました！",
    "cn": "两人都炸了，减去5万币"
  },
  "Bụi Sao Lấp Lánh (Tiến Cấp Sao)": {
    "en": "Sparkling Star Dust (Star Level Up)",
    "ja": "スパークリングスターダスト (スターレベルアップ)",
    "cn": "闪闪星尘（星进阶）"
  },
  ": tin nhắn chứa chuỗi → chặn. VD": {
    "en": ": message contains string → block. For example",
    "ja": ": メッセージには文字列→ブロックが含まれています。たとえば",
    "cn": "：消息包含字符串→块。例如"
  },
  "Danh Sách Giveaway Đang Diễn Ra": {
    "en": "Ongoing Giveaway List",
    "ja": "進行中のプレゼントリスト",
    "cn": "正在进行的赠品清单"
  },
  "Cấu Hình Khung Embed (Tùy Chọn)": {
    "en": "Embed Frame Configuration (Optional)",
    "ja": "埋め込みフレーム構成 (オプション)",
    "cn": "嵌入框架配置（可选）"
  },
  "Xem menu lệnh Level & Kinh tế →": {
    "en": "See Level & Economy command menu →",
    "ja": "レベルとエコノミーコマンドメニューを参照 →",
    "cn": "请参阅等级和经济命令菜单 →"
  },
  "Đang chuẩn bị xác thực Discord": {
    "en": "Preparing to authenticate Discord",
    "ja": "Discord を認証する準備をしています",
    "cn": "准备验证 Discord"
  },
  "Điều khoản Dịch vụ — Sakura Bot": {
    "en": "Terms of Service — Sakura Bot",
    "ja": "利用規約 — さくらボット",
    "cn": "服务条款 — Sakura Bot"
  },
  "Ẩn Danh (Giấu ký tự & độ dài)": {
    "en": "Anonymous (Hide characters & length)",
    "ja": "匿名 (文字と長さを非表示)",
    "cn": "匿名（隐藏字符和长度）"
  },
  "Chào mừng đến với Scribble It!": {
    "en": "Welcome to Scribble It!",
    "ja": "Scribble It へようこそ!",
    "cn": "欢迎来到涂鸦它！"
  },
  "Chào mừng đến với Scribble It": {
    "en": "Welcome to Scribble It",
    "ja": "Scribble It へようこそ",
    "cn": "欢迎来到涂鸦它"
  },
  "Sakura Bot — Hướng dẫn sử dụng": {
    "en": "Sakura Bot — Instructions for use",
    "ja": "さくらボット — 使用説明書",
    "cn": "樱花机器人 — 用户指南"
  },
  "Cường hóa / Đột phá (+0 - +300)": {
    "en": "Enhancement / Breakthrough (+0 - +300)",
    "ja": "強化/ブレークスルー (+0 - +300)",
    "cn": "增强/突破（+0 - +300）"
  },
  "Không cần chìa khóa (Mở tự do)": {
    "en": "No key needed (Open freely)",
    "ja": "鍵不要（自由に開けられます）",
    "cn": "无需钥匙（自由打开）"
  },
  "Vận May Câu Cá (Bắt cá hiếm/to)": {
    "en": "Fishing Luck (Catch rare/big fish)",
    "ja": "釣り運（珍しい魚・大きな魚が釣れる）：",
    "cn": "钓鱼运气（捕获稀有/大鱼）"
  },
  "Mồi ẩn (Kiếm từ sự kiện/rương)": {
    "en": "Hidden Lure (Earn from events/chests)",
    "ja": "隠しルアー (イベント/宝箱から獲得)",
    "cn": "隐藏的诱饵（从活动/宝箱中赚取）"
  },
  "BOMB (Bom nổ trừ tiền đôi bên)": {
    "en": "BOMB (Bomb explodes to deduct money from both sides)",
    "ja": "BOMB (爆弾が爆発して双方からお金を差し押さえます)",
    "cn": "BOMB（炸弹爆炸双方扣钱）"
  },
  "để xem trang trại và điều chỉnh": {
    "en": "to view the farm and make adjustments",
    "ja": "農場を表示して調整します。",
    "cn": "查看农场并进行调整"
  },
  "Tinh Thể End Crystal (Enchant)": {
    "en": "End Crystal (Enchant)",
    "ja": "エンドクリスタル (エンチャント)",
    "cn": "末影水晶（附魔）"
  },
  "Sương Giá Băng Phủ (Chậm lớn)": {
    "en": "Frost Covered (Slow growth)",
    "ja": "霜に覆われている (成長が遅い)",
    "cn": "霜冻覆盖（生长缓慢）"
  },
  "Thần Rèn (x5 Đập Cuốc, x3 Sao)": {
    "en": "Forge God (x5 Pickaxes, x3 Stars)",
    "ja": "フォージゴッド (ツルハシx5、スターx3)",
    "cn": "锻造之神（x5 镐，x3 星星）"
  },
  "Số Điện Thoại Zalo (ZALO_PHONE)": {
    "en": "Zalo Phone Number (ZALO_PHONE)",
    "ja": "Zalo 電話番号 (ZALO_PHONE)",
    "cn": "扎洛电话号码 (ZALO_PHONE)"
  },
  "Lưu Toàn Bộ Cấu Hình config.py": {
    "en": "Save All Configuration config.py",
    "ja": "すべての設定を保存 config.py",
    "cn": "保存整个配置 config.py"
  },
  "Nhập Discord User ID nông dân": {
    "en": "Enter Discord User ID farmer",
    "ja": "Discord ユーザー ID ファーマーを入力してください",
    "cn": "输入 Discord 用户 ID 农民"
  },
  "Xem menu lệnh Welcome & Role →": {
    "en": "See Welcome & Role command menu →",
    "ja": "「ようこそと役割」コマンド メニューを参照 →",
    "cn": "请参阅“欢迎和角色”命令菜单 →"
  },
  "Đăng nhập Discord — Sakura Bot": {
    "en": "Login to Discord — Sakura Bot",
    "ja": "Discordにログイン — さくらボット",
    "cn": "登录 Discord — Sakura Bot"
  },
  "Nhập tên người chơi Minecraft": {
    "en": "Enter Minecraft player name",
    "ja": "Minecraft のプレイヤー名を入力してください",
    "cn": "输入 Minecraft 玩家名称"
  },
  "Đang tải danh sách phân quyền": {
    "en": "Loading list of permissions",
    "ja": "権限のリストを読み込んでいます",
    "cn": "加载权限列表"
  },
  "Đang tải danh sách người chơi": {
    "en": "Loading player list",
    "ja": "プレイヤーリストを読み込んでいます",
    "cn": "正在加载玩家列表"
  },
  ", nhập biệt danh mới và bấm Lưu": {
    "en": ", enter a new nickname, and click Save",
    "ja": "をクリックし、新しいニックネームを入力し、「保存」をクリックします。",
    "cn": "，输入新的昵称，然后单击“保存”"
  },
  "Luyện Tập (Vẽ tự do cùng Bot)": {
    "en": "Practice (Draw freely with Bot)",
    "ja": "練習（ボットで自由に描く）",
    "cn": "练习（与Bot自由绘画）"
  },
  "Thủy cung tương tác sống động": {
    "en": "Lively interactive aquarium",
    "ja": "活気あふれるインタラクティブな水族館",
    "cn": "热闹的互动水族馆"
  },
  "Có thể kiếm từ đâu (Nguồn gốc)": {
    "en": "Where can you get it from (Origin)",
    "ja": "どこから入手できますか (起源)",
    "cn": "你可以从哪里得到它？ （起源）"
  },
  "Mã định danh ID (fish_bag_...)": {
    "en": "Identifier ID (fish_bag_...)",
    "ja": "識別子ID (fish_bag_...)",
    "cn": "ID标识符（fish_bag_...）"
  },
  "Mô tả hiệu ứng kỹ năng của Pet": {
    "en": "Description of Pet's skill effects",
    "ja": "ペットのスキル効果の説明",
    "cn": "宠物技能效果说明"
  },
  "CUSTOM_MSG (Thông điệp troll)": {
    "en": "CUSTOM_MSG (Troll message)",
    "ja": "CUSTOM_MSG (荒らしメッセージ)",
    "cn": "CUSTOM_MSG（巨魔消息）"
  },
  "Hủy Bỏ Cưỡng Chế (Về Tự Động)": {
    "en": "Forced Cancellation (Automatic Return)",
    "ja": "強制キャンセル（自動復帰）",
    "cn": "强制取消（自动返回）"
  },
  "Discord User ID của Người Chơi": {
    "en": "Discord User ID of the Player",
    "ja": "プレイヤーの Discord ユーザー ID",
    "cn": "玩家的 Discord 用户 ID"
  },
  "Thêm Trang Bị Khoáng Sản Mới": {
    "en": "Add New Mineral Equipment",
    "ja": "新しい鉱物装備を追加",
    "cn": "添加了新的矿物设备"
  },
  "Thêm Vật Phẩm Nông Nghiệp Mới": {
    "en": "Add New Agricultural Items",
    "ja": "新しい農業アイテムを追加",
    "cn": "添加新的农业项目"
  },
  "Mô Hình AI Mặc Định (AI_MODEL)": {
    "en": "Default AI Model (AI_MODEL)",
    "ja": "デフォルトの AI モデル (AI_MODEL)",
    "cn": "默认 AI 模型 (AI_MODEL)"
  },
  "ở tab Tổng quan để có hiệu lực": {
    "en": "in the Overview tab to take effect",
    "ja": "[概要] タブで有効にします。",
    "cn": "在概览选项卡中生效"
  },
  "Phát Sóng Mã Code & Ping Role": {
    "en": "Broadcast Code & Ping Role",
    "ja": "ブロードキャスト コードと Ping の役割",
    "cn": "广播代码和 Ping 角色"
  },
  "Ví dụ: Đạt mốc câu cá mùa hè": {
    "en": "For example: Reaching summer fishing milestone",
    "ja": "例: 夏釣りのマイルストーンに到達",
    "cn": "示例：达到夏季钓鱼里程碑"
  },
  "Ghi chú thêm về vật phẩm này": {
    "en": "Additional notes about this item",
    "ja": "この商品に関する追加の注意事項",
    "cn": "关于此项目的附加说明"
  },
  "Xem menu lệnh Ticket hỗ trợ →": {
    "en": "See the Support Ticket command menu →",
    "ja": "サポートチケットコマンドメニューを参照 →",
    "cn": "请参阅支持票命令菜单 →"
  },
  "Tìm kiếm tệp trong thư mục...": {
    "en": "Search for files in folders...",
    "ja": "フォルダー内のファイルを検索...",
    "cn": "搜索文件夹中的文件..."
  },
  "Tìm kiếm tệp trong thư mục": {
    "en": "Search for files in folders",
    "ja": "フォルダー内のファイルを検索",
    "cn": "搜索文件夹中的文件"
  },
  "Tìm kiếm người chơi / UUID...": {
    "en": "Search for players / UUID...",
    "ja": "プレーヤー/UUIDを検索...",
    "cn": "搜索玩家/UUID..."
  },
  "Tìm kiếm người chơi / UUID": {
    "en": "Search for players / UUID",
    "ja": "プレーヤー/UUIDを検索",
    "cn": "搜索玩家/UUID"
  },
  "Ý kiến đóng góp & trải nghiệm": {
    "en": "Opinions & experiences",
    "ja": "意見と経験",
    "cn": "意见和经验"
  },
  "Đang truy vấn cơ sở dữ liệu": {
    "en": "Querying the database",
    "ja": "データベースにクエリを実行しています",
    "cn": "查询数据库"
  },
  "Siêu Lớn 15×15 (Nối 5 Thắng)": {
    "en": "Super Large 15×15 (Connect 5 Wins)",
    "ja": "スーパーラージ 15×15 (5 つの勝利を接続)",
    "cn": "超大15×15（5刹连）"
  },
  "Hướng dẫn sử dụng Sakura Bot": {
    "en": "Instructions for using Sakura Bot",
    "ja": "さくらボットの使い方",
    "cn": "樱花机器人使用说明"
  },
  "Đang tải trạng thái các API": {
    "en": "Loading API status",
    "ja": "API ステータスを読み込み中",
    "cn": "API 的加载状态"
  },
  "Lượt dùng tối đa (0 = vô hạn)": {
    "en": "Maximum usage (0 = infinite)",
    "ja": "最大使用量 (0 = 無限)",
    "cn": "最大使用量（0 = 无限）"
  },
  "Chìa Khóa Yêu Cầu Để Mở Rương": {
    "en": "Key Required to Open Chest",
    "ja": "チェストを開けるには鍵が必要です",
    "cn": "打开宝箱所需的钥匙"
  },
  "Thần Rèn (x5 Đập Đồ, x3 Sao)": {
    "en": "Forge God (x5 Smashing Items, x3 Stars)",
    "ja": "フォージゴッド (x5 スマッシングアイテム、x3 スター)",
    "cn": "铁匠（x5 物品粉碎，x3 星星）"
  },
  "Không thể gia hạn (Tiêu hao)": {
    "en": "Cannot be renewed (Consumable)",
    "ja": "更新不可（消耗品）",
    "cn": "无法续订（消耗品）"
  },
  "REVERSE_TEXT (Nói ngược chữ)": {
    "en": "REVERSE_TEXT (Say words backwards)",
    "ja": "REVERSE_TEXT (単語を逆に言う)",
    "cn": "REVERSE_TEXT（倒着说单词）"
  },
  "Thêm Vật Phẩm Troll Vào Game": {
    "en": "Add Troll Items to the Game",
    "ja": "トロールアイテムをゲームに追加",
    "cn": "将巨魔物品添加到游戏中"
  },
  "Cập Nhật Dụng Cụ / Phân Bón": {
    "en": "Update Tools / Fertilizers",
    "ja": "ツール/肥料を更新",
    "cn": "更新工具/肥料"
  },
  "Chọn Thời Tiết Muốn Thiết Lập": {
    "en": "Select the Weather You Want to Set",
    "ja": "設定したい天気を選択してください",
    "cn": "选择您要设置的天气"
  },
  "Khởi Tạo & Lưu Thành Tựu Mới": {
    "en": "Create & Save New Achievements",
    "ja": "新しい実績を作成して保存",
    "cn": "创造并保存新成就"
  },
  "Thêm Từ Vựng Mới Vào Từ Điển": {
    "en": "Add New Vocabulary to Dictionary",
    "ja": "新しい語彙を辞書に追加",
    "cn": "将新词汇添加到词典中"
  },
  "Cổng Web Dashboard (WEB_PORT)": {
    "en": "Web Dashboard Port (WEB_PORT)",
    "ja": "Web ダッシュボード ポート (WEB_PORT)",
    "cn": "Web 仪表板端口 (WEB_PORT)"
  },
  "Kênh nhận thông báo Giftcode": {
    "en": "Channel to receive Giftcode notifications",
    "ja": "ギフトコード通知を受け取るチャンネル",
    "cn": "接收礼品代码通知的渠道"
  },
  "Các Bảng Role Đang Hoạt Động": {
    "en": "Active Role Tables",
    "ja": "アクティブな役割テーブル",
    "cn": "活跃角色表"
  },
  "Chỉnh Sửa Thông Tin Hôn Nhân": {
    "en": "Edit Marriage Information",
    "ja": "結婚情報を編集する",
    "cn": "编辑婚姻信息"
  },
  "Chỉnh Sửa Thuộc Tính Cần Câu": {
    "en": "Edit Fishing Rod Attributes",
    "ja": "釣り竿の属性を編集する",
    "cn": "编辑钓鱼竿属性"
  },
  "Kênh Ghi Log Server (Discord)": {
    "en": "Server Logging Channel (Discord)",
    "ja": "サーバーログチャンネル (Discord)",
    "cn": "服务器日志通道（Discord）"
  },
  "Cấp Quyền Cho Người Dùng Mới": {
    "en": "Grant Permissions to New Users",
    "ja": "新しいユーザーに権限を付与する",
    "cn": "授权新用户"
  },
  "Trạng thái kết nối & Xã hội": {
    "en": "Social & Connection Status",
    "ja": "ソーシャル＆コネクションステータス",
    "cn": "连接状态和社交"
  },
  "Zalo URL hoặc Số điện thoại": {
    "en": "Zalo URL or Phone number",
    "ja": "Zalo URLまたは電話番号",
    "cn": "Zalo 网址或电话号码"
  },
  "Lưu & Mở Trang Profile Ngay": {
    "en": "Save & Open Profile Page Now",
    "ja": "今すぐ保存してプロフィールページを開く",
    "cn": "立即保存并打开个人资料页面"
  },
  "Bàn Điều Khiển Truy Vấn SQL": {
    "en": "SQL Query Console",
    "ja": "SQLクエリコンソール",
    "cn": "SQL查询控制台"
  },
  "Không thể tải danh sách Cogs": {
    "en": "Unable to load Cogs list",
    "ja": "歯車リストをロードできません。",
    "cn": "无法加载齿轮列表"
  },
  "Kết quả sẽ xuất hiện ở đây": {
    "en": "The results will appear here",
    "ja": "結果はここに表示されます",
    "cn": "结果将出现在这里"
  },
  "Phát sóng kênh Giftcode bot": {
    "en": "Broadcast the Giftcode bot channel",
    "ja": "Giftcode ボットチャンネルをブロードキャストする",
    "cn": "广播 Giftcode 机器人频道"
  },
  "Buộc phát hành lại (Force)": {
    "en": "Forced re-release (Force)",
    "ja": "強制再解放（強制）",
    "cn": "强制重新发行（强制）"
  },
  "Thêm Vào Bách Khoa Toàn Thư": {
    "en": "Added to Encyclopedia",
    "ja": "百科事典に追加されました",
    "cn": "添加到百科全书"
  },
  "Tên Rương (kèm icon bắt mắt)": {
    "en": "Chest name (with eye-catching icon)",
    "ja": "チェスト名 (目を引くアイコン付き)",
    "cn": "宝箱名称（带有醒目的图标）"
  },
  "Chìa Khóa Đồng (key_bronze)": {
    "en": "Bronze Key (key_bronze)",
    "ja": "ブロンズキー (key_bronze)",
    "cn": "青铜钥匙 (key_bronze)"
  },
  "Chìa Khóa Vàng (key_golden)": {
    "en": "Golden Key (key_golden)",
    "ja": "ゴールデンキー (key_golden)",
    "cn": "金钥匙（key_golden）"
  },
  "God Mode Tiến Sao (1..20 ⭐)": {
    "en": "God Mode Tien Sao (1..20 ⭐)",
    "ja": "ゴッドモード ティエンサオ (1..20 ⭐)",
    "cn": "上帝模式天嫂 (1..20 ⭐)"
  },
  "Tỉ Lệ Biến Dị Địa Tầng Quặng": {
    "en": "Rate of Ore Stratigraphic Variation",
    "ja": "鉱石の層序変動の割合",
    "cn": "矿石地层变化率"
  },
  "Đá Phép Khảm Ngoc (Mở Dòng)": {
    "en": "Mosaic Magic Stone (Open Line)",
    "ja": "モザイク魔石(オープンライン)",
    "cn": "玉石马赛克魔法石（开放线）"
  },
  "Chọn Máy Chủ Discord Cần Nối": {
    "en": "Choose the Discord Server to Connect",
    "ja": "接続する Discord サーバーを選択してください",
    "cn": "选择要连接的 Discord 服务器"
  },
  "Quản Lý Phát Quà & Giveaway": {
    "en": "Gift Distribution & Giveaway Management",
    "ja": "ギフト配布と景品管理",
    "cn": "礼品分发和赠品管理"
  },
  "Chỉnh Sửa Cấp Độ & XP User": {
    "en": "Edit User Level & XP",
    "ja": "ユーザーレベルと XP を編集",
    "cn": "编辑用户级别和 XP"
  },
  "Chỉnh Sửa Vật Phẩm Cửa Hàng": {
    "en": "Edit Shop Items",
    "ja": "ショップアイテムを編集",
    "cn": "编辑商店商品"
  },
  "Sakura Bot • Hẹn gặp lại bạn": {
    "en": "Sakura Bot • See you soon",
    "ja": "さくらボット • また会いましょう！",
    "cn": "樱花机器人 • 很快再见"
  },
  "Sakura MC — Quản Lý Tệp Tin": {
    "en": "Sakura MC — File Manager",
    "ja": "さくら MC — ファイルマネージャー",
    "cn": "樱花MC — 文件管理器"
  },
  "Đang tải danh sách tệp tin": {
    "en": "Loading file list",
    "ja": "ファイルリストを読み込んでいます",
    "cn": "加载文件列表"
  },
  "Đang tải danh sách máy chủ": {
    "en": "Loading server list",
    "ja": "サーバーリストを読み込んでいます",
    "cn": "正在加载服务器列表"
  },
  "Đường dẫn bio của bạn sẽ là": {
    "en": "Your bio link will be",
    "ja": "あなたのバイオリンクは次のようになります",
    "cn": "您的生物链接将是"
  },
  "Quản Lý Tệp & Nạp Lại Cogs": {
    "en": "File Management & Cogs Reload",
    "ja": "ファイル管理と歯車のリロード",
    "cn": "管理文件和重新加载齿轮"
  },
  "TẠO PHÒNG RIÊNG & CÀI ĐẶT": {
    "en": "CREATE YOUR PRIVATE ROOM & SETUP",
    "ja": "プライベートルームを作成してセットアップ",
    "cn": "创建您的私人房间和设置"
  },
  "Đang quét danh sách phòng": {
    "en": "Scanning room list",
    "ja": "スキャンルームリスト",
    "cn": "扫描室列表"
  },
  "để mở bảng điều khiển riêng": {
    "en": "to open a separate control panel",
    "ja": "をクリックして、別のコントロール パネルを開きます。",
    "cn": "打开单独的控制面板"
  },
  "Coins (Tiền mặt phổ thông)": {
    "en": "Coins (Common Cash)",
    "ja": "コイン (共通現金)",
    "cn": "硬币（普通现金）"
  },
  "để xem kho đồ và điều chỉnh": {
    "en": "to view inventory and make adjustments",
    "ja": "在庫を表示し、調整を行います。",
    "cn": "查看库存并进行调整"
  },
  "Vật Phẩm Tiện Ích (Items)": {
    "en": "Utility Items (Items)",
    "ja": "ユーティリティアイテム (アイテム)",
    "cn": "实用物品（物品）"
  },
  "Số lượng (0 = Xóa khỏi kho)": {
    "en": "Quantity (0 = Removed from inventory)",
    "ja": "数量 (0 = 在庫から削除)",
    "cn": "数量（0 = 从库存中移除）"
  },
  "Phát Mã Daily Code Hôm Nay": {
    "en": "Distribute Daily Code Today",
    "ja": "デイリーコードを今すぐ配布",
    "cn": "立即分发每日代码"
  },
  "Mã định danh ID (chest_...)": {
    "en": "Identifier ID (chest_...)",
    "ja": "識別子ID (chest_...)",
    "cn": "标识符ID（胸部_...）"
  },
  "Chìa Khóa Bạc (key_silver)": {
    "en": "Silver Key (key_silver)",
    "ja": "シルバーキー (key_silver)",
    "cn": "银钥匙（key_silver）"
  },
  "Vật Phẩm Troll & Tiện Ích:": {
    "en": "Troll Items & Gadgets:",
    "ja": "トロールアイテムとガジェット:",
    "cn": "巨魔物品和实用工具："
  },
  "Vật Phẩm Troll & Tiện Ích": {
    "en": "Troll Items & Gadgets",
    "ja": "トロールアイテムとガジェット",
    "cn": "巨魔物品和小工具"
  },
  "God Mode Đập Đồ (+1..+150)": {
    "en": "God Mode Smash Items (+1..+150)",
    "ja": "ゴッドモードスマッシュアイテム (+1..+150)",
    "cn": "上帝模式粉碎物品（+1..+150）"
  },
  "Thêm Thú Cưng Vào Hệ Thống": {
    "en": "Add Pets to the System",
    "ja": "ペットをシステムに追加",
    "cn": "将宠物添加到系统中"
  },
  "VOICE_KICK (Đá khỏi voice)": {
    "en": "VOICE_KICK (Kick off voice)",
    "ja": "VOICE_KICK (キックオフボイス)",
    "cn": "VOICE_KICK（启动语音）"
  },
  "Túi Quặng Trong Khoang Đào": {
    "en": "Ore Bag In Digging Chamber",
    "ja": "採掘室の鉱石バッグ",
    "cn": "挖掘室矿袋"
  },
  "Chọn Thành Tựu Cần Thao Tác": {
    "en": "Select the Achievement that needs to be worked on",
    "ja": "取り組む必要がある実績を選択してください",
    "cn": "选择需要采取行动的成就"
  },
  "Danh Hiệu Độc Quyền (Title)": {
    "en": "Exclusive Title (Title)",
    "ja": "独占タイトル (タイトル)",
    "cn": "独家标题（Title）"
  },
  "Mã ID (viết liền không dấu)": {
    "en": "ID code (written immediately without accents)",
    "ja": "ID コード (アクセントなしで直接記述)",
    "cn": "ID 代码（不带变音符号）"
  },
  "+ Thêm kênh bỏ qua từ cấm": {
    "en": "+ Add channels that skip forbidden words",
    "ja": "+ 禁止ワードをスキップするチャンネルを追加",
    "cn": "+ 添加跳过禁用词的频道"
  },
  "Thêm / Cập nhật Custom Key": {
    "en": "Add/Update Custom Key",
    "ja": "カスタムキーの追加/更新",
    "cn": "添加/更新自定义密钥"
  },
  "Các Bản Sao Lưu Đã Lưu Trữ": {
    "en": "Archived Backups",
    "ja": "アーカイブされたバックアップ",
    "cn": "存档备份"
  },
  "Đăng Bảng Nội Quy Vào Kênh": {
    "en": "Post the Rules to the Channel",
    "ja": "ルールをチャンネルに投稿する",
    "cn": "将规则发布到频道"
  },
  "URL Hình Ảnh Embed (Banner)": {
    "en": "Embed Image URL (Banner)",
    "ja": "埋め込み画像 URL (バナー)",
    "cn": "嵌入图像 URL（横幅）"
  },
  "Dán link ảnh hoặc tải tệp": {
    "en": "Paste the image link or download the file",
    "ja": "画像のリンクを貼り付けるか、ファイルをダウンロードしてください",
    "cn": "粘贴图像链接或下载文件"
  },
  "Ví dụ: luatchoi, ip, link": {
    "en": "For example: luatchoi, ip, link",
    "ja": "例: ルアチョイ、ip、リンク",
    "cn": "例如：luatchoi、ip、链接"
  },
  "và lưu vào máy tính của bạn": {
    "en": "and save to your computer",
    "ja": "そしてコンピュータに保存します。",
    "cn": "并保存到您的计算机"
  },
  "Đi đến một điểm warp đã tạo": {
    "en": "Go to a created warp point",
    "ja": "作成したワープポイントに移動します。",
    "cn": "转到创建的扭曲点"
  },
  "Thứ tự hiển thị hiện tại:": {
    "en": "Current display order:",
    "ja": "現在の表示順序:",
    "cn": "当前显示顺序："
  },
  "Thứ tự hiển thị hiện tại": {
    "en": "Current display order",
    "ja": "現在の表示順序",
    "cn": "当前显示顺序"
  },
  "Đang tải dữ liệu tệp tin": {
    "en": "Loading file data",
    "ja": "ファイルデータをロード中",
    "cn": "加载文件数据"
  },
  "Chỉ đọc (Safe Read-Only)": {
    "en": "Safe Read-Only",
    "ja": "安全な読み取り専用",
    "cn": "安全只读"
  },
  "Chưa thực thi truy vấn nào": {
    "en": "No queries have been executed yet",
    "ja": "まだクエリは実行されていません。",
    "cn": "尚未执行任何查询"
  },
  "Lọc từ khóa trong bảng...": {
    "en": "Filter keywords in the table...",
    "ja": "表内のキーワードをフィルターします...",
    "cn": "过滤表中的关键字..."
  },
  "Lọc từ khóa trong bảng": {
    "en": "Filter keywords in the table",
    "ja": "表内のキーワードをフィルターします",
    "cn": "过滤表格中的关键字"
  },
  "Discord User ID (Bắt buộc)": {
    "en": "Discord User ID (Required)",
    "ja": "Discord ユーザー ID (必須)",
    "cn": "Discord 用户 ID（必填）"
  },
  "Bank (Tiền gửi Ngân hàng)": {
    "en": "Bank (Bank Deposit)",
    "ja": "銀行 (銀行預金)",
    "cn": "银行（银行存款）"
  },
  "Thú Cưng Đồng Hành (Pets)": {
    "en": "Companion Pets (Pets)",
    "ja": "コンパニオンペット (ペット)",
    "cn": "伴侣宠物（宠物）"
  },
  "Vật Phẩm Đặc Biệt & Troll": {
    "en": "Special Items & Trolls",
    "ja": "特別なアイテムとトロール",
    "cn": "特殊物品和巨魔"
  },
  "mục tra cứu trong hệ thống": {
    "en": "lookup item in the system",
    "ja": "システム内のルックアップ項目。",
    "cn": "系统中查找项目"
  },
  "Cần Câu Hiếm Trong Rương:": {
    "en": "Rare Fishing Rod in Chest:",
    "ja": "チェスト内のレアな釣り竿:",
    "cn": "宝箱中的稀有钓鱼竿："
  },
  "Cần Câu Hiếm Trong Rương": {
    "en": "Rare Fishing Rod in Chest",
    "ja": "チェスト内のレアな釣り竿",
    "cn": "宝箱里有稀有鱼竿"
  },
  "Mã định danh ID (bait_...)": {
    "en": "Identifier ID (bait_...)",
    "ja": "識別子ID (bait_...)",
    "cn": "标识符ID（bait_...）"
  },
  "Tên túi / thùng (kèm icon)": {
    "en": "Name of bag / box (with icon)",
    "ja": "バッグ/ボックスの名前 (アイコン付き)",
    "cn": "袋子/纸箱名称（带图标）"
  },
  "STEAL_COIN (Trộm tiền ví)": {
    "en": "STEAL_COIN (Wallet money theft)",
    "ja": "STEAL_COIN (ウォレットマネーの盗難)",
    "cn": "STEAL_COIN（钱包钱被盗）"
  },
  "JUMPSCARE (Hù ma dọa tim)": {
    "en": "JUMPSCARE (Heart-threatening scare)",
    "ja": "JUMPSCARE (心臓を脅かす恐怖)",
    "cn": "JUMPSCARE（吓到吓到心）"
  },
  "Thời gian hiệu lực còn lại": {
    "en": "Remaining validity period",
    "ja": "残りの有効期限",
    "cn": "剩余有效期"
  },
  "Thời Gian Cưỡng Chế (Phút)": {
    "en": "Enforcement Time (Minutes)",
    "ja": "施行時間 (分)",
    "cn": "执行时间（分钟）"
  },
  "Mở Khóa Toàn Bộ Bảo Tàng": {
    "en": "Unlock All Museums",
    "ja": "すべての博物館のロックを解除する",
    "cn": "解锁整个博物馆"
  },
  "Nối Server MC Với Discord": {
    "en": "Connect MC Server With Discord",
    "ja": "MCサーバーをDiscordに接続する",
    "cn": "使用 Discord 连接 MC 服务器"
  },
  "Tra Cứu & Quản Lý Từ Điển": {
    "en": "Look Up & Manage Dictionary",
    "ja": "辞書の検索と管理",
    "cn": "查找和管理词典"
  },
  "Không Phổ Biến (Uncommon)": {
    "en": "Uncommon",
    "ja": "珍しい",
    "cn": "不常见"
  },
  "Truyền Thuyết (Legendary)": {
    "en": "Legend",
    "ja": "伝説",
    "cn": "传奇"
  },
  "Hồ Sơ Bot Tại Máy Chủ Này": {
    "en": "Bot Profile On This Server",
    "ja": "このサーバー上のボットプロファイル",
    "cn": "此服务器上的机器人配置文件"
  },
  "nếu không muốn log nhóm đó": {
    "en": "If you don't want to log that group",
    "ja": "そのグループをログに記録したくない場合。",
    "cn": "如果您不想记录该组"
  },
  "DANH SÁCH MỐC ROLE HIỆN CÓ": {
    "en": "LIST OF CURRENT ROLE MARKET",
    "ja": "現在の役割市場のリスト",
    "cn": "当前角色市场列表"
  },
  "Role ping khi có Code mới": {
    "en": "Role ping when there is a new Code",
    "ja": "新しいコードがあるときにロールを ping する",
    "cn": "有新代码时角色 ping"
  },
  "Vai trò cho Bot mới (Bot)": {
    "en": "Roles for New Bots (Bot)",
    "ja": "新しいボットの役割 (ボット)",
    "cn": "新机器人的角色 (Bot)"
  },
  "Chưa có role nào được thêm": {
    "en": "No roles have been added yet",
    "ja": "まだ役割が追加されていません。",
    "cn": "尚未添加任何角色"
  },
  "để lấy mã liên kết 6 ký tự": {
    "en": "to get the 6-character link code",
    "ja": "6 文字のリンク コードを取得します。",
    "cn": "获取 6 个字符的链接代码"
  },
  "CHÀO MỪNG THÀNH VIÊN MỚI!": {
    "en": "WELCOME NEW MEMBER!",
    "ja": "新しいメンバーを歓迎します!",
    "cn": "欢迎新会员！"
  },
  "CHÀO MỪNG THÀNH VIÊN MỚI": {
    "en": "WELCOME NEW MEMBER",
    "ja": "新しいメンバーを歓迎します",
    "cn": "欢迎新会员"
  },
  "Xem Trước Trực Quan Bio": {
    "en": "Visual Bio Preview",
    "ja": "Visual Bio Preview",
    "cn": "生物视觉预览"
  },
  "Đang tải danh sách bảng": {
    "en": "Loading table list",
    "ja": "テーブルリストをロード中",
    "cn": "加载表列表"
  },
  "Đang tải danh sách Cogs": {
    "en": "Loading Cogs list",
    "ja": "歯車リストを読み込み中",
    "cn": "正在加载齿轮列表"
  },
  "Người chơi trong phòng (": {
    "en": "Players in the room (",
    "ja": "Players in the room (",
    "cn": "房间里的玩家（"
  },
  "Số từ được chọn mỗi lượt": {
    "en": "Number of words selected each turn",
    "ja": "Number of words selected each turn",
    "cn": "每轮选择的单词数"
  },
  "Câu hỏi thường gặp (FAQ)": {
    "en": "Frequently Asked Questions (FAQ)",
    "ja": "Frequently Asked Questions (FAQ)",
    "cn": "常见问题 (FAQ)"
  },
  "Chọn máy chủ để cấu hình": {
    "en": "Select server to configure",
    "ja": "Select server to configure",
    "cn": "选择要配置的服务器"
  },
  "Tất Cả Server / Toàn Cục": {
    "en": "All Servers / Whole Department",
    "ja": "All Servers / Whole Department",
    "cn": "所有服务器/整个部门"
  },
  "Xu (Tiền tệ Nạp/Premium)": {
    "en": "Coins (Deposit/Premium Currency)",
    "ja": "Coins (Deposit/Premium Currency)",
    "cn": "硬币（存款/高级货币）"
  },
  "Thiết lập chính xác (=)": {
    "en": "Correct setup (=)",
    "ja": "正しいセットアップ (=)",
    "cn": "正确设置(=)"
  },
  "Đang tải danh sách item": {
    "en": "Loading item list",
    "ja": "アイテムリストを読み込んでいます",
    "cn": "加载项目列表"
  },
  "Mặc Định (Cân Bằng Gốc)": {
    "en": "Default (Original Balanced)",
    "ja": "デフォルト (オリジナルバランス)",
    "cn": "默认（原始平衡）"
  },
  "Tỉ Lệ Rớt Rương Đại Dương": {
    "en": "Ocean Chest Drop Rate",
    "ja": "オーシャンチェストのドロップ率",
    "cn": "海洋宝箱掉落率"
  },
  "Mã định danh ID (rod_...)": {
    "en": "Identifier ID (rod_...)",
    "ja": "識別子ID (rod_...)",
    "cn": "标识符 ID (rod_...)"
  },
  "May mắn cộng thêm khi câu": {
    "en": "Bonus luck when fishing",
    "ja": "釣り時のボーナス運",
    "cn": "钓鱼时会增加运气"
  },
  "Mã định danh ID (pet_...)": {
    "en": "ID identifier (pet_...)",
    "ja": "ID識別子(pet_...)",
    "cn": "ID 标识符（pet_...）"
  },
  "STEAL_FISH (Trộm cá quý)": {
    "en": "STEAL_FISH (Stealing precious fish)",
    "ja": "STEAL_FISH (貴重な魚を盗む)",
    "cn": "STEAL_FISH（偷珍贵的鱼）"
  },
  "FAKE_NITRO (Hộp quà bẫy)": {
    "en": "FAKE_NITRO (Trap gift box)",
    "ja": "FAKE_NITRO (トラップギフトボックス)",
    "cn": "FAKE_NITRO（陷阱礼盒）"
  },
  "GHOST_PING (Tag ma quái)": {
    "en": "GHOST_PING (Ghost Tag)",
    "ja": "GHOST_PING (ゴーストタグ)",
    "cn": "GHOST_PING（幽灵标签）"
  },
  "Đặt Cấp Refine (+0..150)": {
    "en": "Set Refine Level (+0..150)",
    "ja": "リファインレベルの設定 (+0..150)",
    "cn": "设置精炼级别 (+0..150)"
  },
  "Thao Tác Quản Trị Thợ Mỏ": {
    "en": "Miner Administration Operations",
    "ja": "マイナー管理業務",
    "cn": "矿工管理操作"
  },
  "Biểu Tượng (Icon / Emoji)": {
    "en": "Icon (Icon / Emoji)",
    "ja": "アイコン (アイコン/絵文字)",
    "cn": "图标（图标/表情符号）"
  },
  "Quản Lý Minigame Nối Chữ": {
    "en": "Manage Letter Matching Minigame",
    "ja": "文字マッチングミニゲームの管理",
    "cn": "管理字母匹配小游戏"
  },
  "Trivia / Ai Là Triệu Phú": {
    "en": "Trivia / Who Wants to Be a Millionaire",
    "ja": "トリビア / 大富豪になりたい人",
    "cn": "琐事 / 谁想成为百万富翁"
  },
  "+ Thêm kênh bỏ qua spam": {
    "en": "+ Add channel to ignore spam",
    "ja": "+ スパムを無視するチャンネルを追加",
    "cn": "+ 添加忽略垃圾邮件的渠道"
  },
  "Ngưỡng dấu kết hợp (4-20)": {
    "en": "Combined mark threshold (4-20)",
    "ja": "結合マークしきい値 (4 ～ 20)",
    "cn": "组合分数阈值 (4-20)"
  },
  "Blacklist — Cấm dùng bot": {
    "en": "Blacklist — Forbidden to use bots",
    "ja": "ブラックリスト — ボットの使用を禁止します",
    "cn": "黑名单——禁止使用机器人"
  },
  "Điểm Tình Cảm (Affection)": {
    "en": "Affection Score (Affection)",
    "ja": "愛情スコア（愛情）：",
    "cn": "好感度（好感度）"
  },
  "Tìm tên, username, ID...": {
    "en": "Find name, username, ID...",
    "ja": "名前、ユーザー名、ID を検索...",
    "cn": "查找姓名、用户名、ID..."
  },
  "Tìm tên, username, ID": {
    "en": "Find name, username, ID",
    "ja": "名前、ユーザー名、ID を検索",
    "cn": "查找姓名、用户名、ID"
  },
  "Nhập nội dung thông báo": {
    "en": "Enter notification content",
    "ja": "通知内容を入力してください",
    "cn": "输入通知内容"
  },
  "Hồ Sơ Của Bạn (Của Mình)": {
    "en": "Your Profile (Mine)",
    "ja": "あなたのプロフィール (私の)",
    "cn": "你的个人资料（我的）"
  },
  "Sắp Xếp Thứ Tự Khối Bio": {
    "en": "Arrange Bio Block Order",
    "ja": "バイオブロックの注文を手配する",
    "cn": "安排生物区块顺序"
  },
  "Nhập văn bản cần xử lý": {
    "en": "Enter the text to be processed",
    "ja": "処理するテキストを入力してください",
    "cn": "输入要处理的文字"
  },
  "Cổ Điển (Chuẩn Skribbl)": {
    "en": "Classic (Skribbl Standard)",
    "ja": "クラシック (Skribbl スタンダード)",
    "cn": "经典（Skribbl 标准）"
  },
  "Cập Nhật Trạng Thái Bot": {
    "en": "Update Bot Status",
    "ja": "ボットのステータスを更新する",
    "cn": "更新机器人状态"
  },
  "Mã ID vật phẩm tùy chỉnh": {
    "en": "Custom Item ID",
    "ja": "カスタムアイテムID",
    "cn": "自定义商品 ID 代码"
  },
  "Huyền Thoại (Legendary)": {
    "en": "Legendary",
    "ja": "伝説の",
    "cn": "传奇"
  },
  "Tỉ lệ xuất hiện (Chance)": {
    "en": "Chance",
    "ja": "チャンス",
    "cn": "机会"
  },
  "Đang tải danh sách mồi": {
    "en": "Loading bait list",
    "ja": "餌リストを読み込んでいます",
    "cn": "正在加载诱饵列表"
  },
  "Đang tải danh sách pet": {
    "en": "Loading pet list",
    "ja": "ペットリストを読み込み中",
    "cn": "正在加载宠物列表"
  },
  "Đang tải danh sách cần": {
    "en": "Loading wish list",
    "ja": "ウィッシュリストを読み込んでいます",
    "cn": "正在加载愿望清单"
  },
  "Loại hiệu ứng (Key Lệnh)": {
    "en": "Effect type (Command Key)",
    "ja": "エフェクトタイプ（コマンドキー）：",
    "cn": "效果类型（命令键）"
  },
  "RENAME (Đổi biệt danh)": {
    "en": "RENAME (Change nickname)",
    "ja": "RENAME (ニックネームを変更)",
    "cn": "RENAME（更改昵称）"
  },
  "Số lần câu bị nguyền (VD": {
    "en": "Number of times the sentence is cursed (Example",
    "ja": "文が呪われた回数（例：",
    "cn": "句子被咒骂的次数（例如"
  },
  "Nắng Ấm Dịu Êm (Chuẩn)": {
    "en": "Warm and Soft Sunshine (Standard)",
    "ja": "暖かく柔らかな日差し（標準）",
    "cn": "柔和温暖的阳光（标准）"
  },
  "Tên Hiển Thị (kèm Emoji)": {
    "en": "Display Name (with Emoji)",
    "ja": "表示名 (絵文字付き)",
    "cn": "显示名称（带表情符号）"
  },
  "Prefix Mặc Định Toàn Cục": {
    "en": "Global Default Prefix",
    "ja": "グローバルデフォルトプレフィックス",
    "cn": "全局默认前缀"
  },
  "Bảng nội dung thông báo": {
    "en": "Notice content table",
    "ja": "お知らせ内容表",
    "cn": "通知目录"
  },
  "Số mention tối đa (2-15)": {
    "en": "Maximum number of mentions (2-15)",
    "ja": "メンションの最大数 (2 ～ 15)",
    "cn": "最大提及次数 (2-15)"
  },
  "Số lần lặp tối đa (2-10)": {
    "en": "Maximum number of repetitions (2-10)",
    "ja": "最大繰り返し回数 (2 ～ 10)",
    "cn": "最大重复次数 (2-10)"
  },
  "URL Icon Góc (Thumbnail)": {
    "en": "Corner Icon URL (Thumbnail)",
    "ja": "コーナーアイコンURL（サムネイル）：",
    "cn": "角图标 URL（缩略图）"
  },
  "Xem menu lệnh Âm nhạc →": {
    "en": "See Music command menu →",
    "ja": "音楽コマンドメニューを参照→",
    "cn": "请参阅音乐 → 命令菜单"
  },
  "Xem menu câu cá & chợ →": {
    "en": "See fishing & market menu →",
    "ja": "フィッシング＆マーケットメニューを見る →",
    "cn": "查看钓鱼和市场菜单 →"
  },
  "Tạo Trang Hồ Sơ Của Bạn": {
    "en": "Create Your Profile Page",
    "ja": "プロフィールページを作成する",
    "cn": "创建您的个人资料页面"
  },
  "Về Trang Chủ Sakura Bot": {
    "en": "Back to Sakura Bot Homepage",
    "ja": "さくらボットのホームページに戻る",
    "cn": "返回樱花机器人主页"
  },
  "Tài khoản — Sakura Bot": {
    "en": "Account — Sakura Bot",
    "ja": "アカウント — さくらボット",
    "cn": "账户 — 樱花机器人"
  },
  "Sắp Xếp Vị Trí Các Hộp": {
    "en": "Arrange the Location of Boxes",
    "ja": "ボックスの位置を調整する",
    "cn": "安排盒子的位置"
  },
  "Đang tải cấu trúc cột": {
    "en": "Loading column structure",
    "ja": "列構造を読み込んでいます",
    "cn": "装载柱结构"
  },
  "Game tích hợp trên web": {
    "en": "Game integrated on the web",
    "ja": "ウェブ上に統合されたゲーム",
    "cn": "游戏集成到网络上"
  },
  "Siêu Khó (Grandmaster)": {
    "en": "Super Hard (Grandmaster)",
    "ja": "スーパーハード (グランドマスター)",
    "cn": "超难（大师）"
  },
  "Thời gian vẽ mỗi lượt": {
    "en": "Drawing time per turn",
    "ja": "1ターンあたりの描画時間",
    "cn": "每回合绘图时间"
  },
  "Chọn 1 từ khóa dưới đây": {
    "en": "Choose 1 keyword below",
    "ja": "以下からキーワードを 1 つ選択してください",
    "cn": "选择下面 1 个关键字"
  },
  "Tiêu Chuẩn (1.5 - 6kg)": {
    "en": "Standard (1.5 - 6kg)",
    "ja": "標準 (1.5 - 6kg)",
    "cn": "标准（1.5 - 6公斤）"
  },
  "Phát Hành Giftcode Mới": {
    "en": "New Giftcode Released",
    "ja": "新しいギフトコードがリリースされました",
    "cn": "新礼包码已发布"
  },
  "Rơi từ Rương / Sự kiện": {
    "en": "Dropped from Chests / Events",
    "ja": "宝箱/イベントからドロップ",
    "cn": "从宝箱/活动中掉落"
  },
  "Tạo Rương Mới Vào Game": {
    "en": "Create a New Chest in the Game",
    "ja": "ゲーム内に新しいチェストを作成します",
    "cn": "在游戏中创建一个新宝箱"
  },
  "Rương Hải Tặc Atlantis": {
    "en": "Atlantis Pirate Chest",
    "ja": "アトランティス海賊チェスト",
    "cn": "亚特兰蒂斯海盗宝箱"
  },
  "Lưu Tỉ Lệ Vào Hệ Thống": {
    "en": "Save the Rate to the System",
    "ja": "レートをシステムに保存",
    "cn": "将费率保存到系统"
  },
  "May Mắn x2 (Tất Cả x2)": {
    "en": "Lucky x2 (All x2)",
    "ja": "ラッキー x2 (すべて x2)",
    "cn": "幸运x2（全部x2）"
  },
  "Tên Thú Cưng (kèm icon)": {
    "en": "Pet Name (with icon)",
    "ja": "ペットの名前 (アイコン付き)",
    "cn": "宠物名称（带图标）"
  },
  "Tên vật phẩm (kèm icon)": {
    "en": "Item name (with icon)",
    "ja": "項目名（アイコン付き）：",
    "cn": "项目名称（带图标）"
  },
  "MUTE (Cấm chat server)": {
    "en": "MUTE (Ban chat server)",
    "ja": "MUTE (チャットサーバーの禁止)",
    "cn": "静音（禁止聊天服务器）"
  },
  "Thông báo troll tự soạn": {
    "en": "Self-composed troll notification",
    "ja": "自作荒らし通知。",
    "cn": "自创的巨魔通知"
  },
  "Ngọc Trai Đen Huyền Bí": {
    "en": "Mysterious Black Pearl",
    "ja": "ミステリアスブラックパール",
    "cn": "神秘黑珍珠"
  },
  "Chọn Mùa Muốn Thiết Lập": {
    "en": "Select the Season You Want to Set Up",
    "ja": "設定したいシーズンを選択してください",
    "cn": "选择您要设置的季节"
  },
  "Nông Trại & Đồng Ruộng": {
    "en": "Farms & Fields",
    "ja": "農場と畑",
    "cn": "农场与田野"
  },
  "Cuốc Đào Mỏ (Pickaxe)": {
    "en": "Pickaxe",
    "ja": "つるはし",
    "cn": "镐"
  },
  "Lưu Cài Đặt Hoyo Codes": {
    "en": "Save Settings Hoyo Codes",
    "ja": "設定を保存 Hoyo コード",
    "cn": "保存设置 Hoyo 代码"
  },
  "Lưu Cấu Hình Minecraft": {
    "en": "Save Minecraft Configuration",
    "ja": "Minecraft の設定を保存する",
    "cn": "保存 Minecraft 配置"
  },
  "Tìm server theo tên...": {
    "en": "Search server by name...",
    "ja": "サーバーを名前で検索...",
    "cn": "按名称搜索服务器..."
  },
  "Tìm server theo tên": {
    "en": "Search server by name",
    "ja": "サーバーを名前で検索",
    "cn": "按名称查找服务器"
  },
  "CẢM ƠN SERVER BOOSTER!": {
    "en": "THANK YOU SERVER BOOSTER!",
    "ja": "サーバーブースターに感謝します!",
    "cn": "感谢服务器助推器！"
  },
  "CẢM ƠN SERVER BOOSTER": {
    "en": "THANK YOU SERVER BOOSTER",
    "ja": "サーバーブースターに感謝します",
    "cn": "感谢服务器助推器"
  },
  "Thời gian chạy (Uptime)": {
    "en": "Uptime",
    "ja": "稼働時間",
    "cn": "正常运行时间"
  },
  "Gửi Phản Hồi & Báo Lỗi": {
    "en": "Send Feedback & Report Errors",
    "ja": "フィードバックを送信してエラーを報告する",
    "cn": "发送反馈并报告错误"
  },
  "Thành Tựu & Danh Hiệu": {
    "en": "Achievements & Titles",
    "ja": "実績と称号",
    "cn": "成就与荣誉"
  },
  "Danh Hiệu Đã Mở Khóa": {
    "en": "Title Unlocked",
    "ja": "タイトルのロックが解除されました",
    "cn": "标题已解锁"
  },
  "Chưa kiểm tra cú pháp": {
    "en": "Haven't checked the syntax",
    "ja": "構文をチェックしていない",
    "cn": "没有检查语法"
  },
  "Mời Bạn (Online Room)": {
    "en": "Invite Friends (Online Room)",
    "ja": "友達を招待（オンラインルーム）",
    "cn": "邀请好友（在线房间）"
  },
  "Song ngữ (Việt - Anh)": {
    "en": "Bilingual (Vietnamese - English)",
    "ja": "バイリンガル (ベトナム語 - 英語)",
    "cn": "双语（越南语 - 英语）"
  },
  "Số vòng chơi (Rounds)": {
    "en": "Number of rounds (Rounds)",
    "ja": "ラウンド数(Rounds)",
    "cn": "轮数（轮次）"
  },
  "Bản 3×3 (Nối 3 Thắng)": {
    "en": "3×3 version (Connect 3 Wins)",
    "ja": "3×3 バージョン (3 つの勝利を接続)",
    "cn": "3×3版本（连接3个Thang）"
  },
  "Bảng Xếp Hạng Caro XO": {
    "en": "Caro XO Rankings",
    "ja": "カロ XO ランキング",
    "cn": "卡罗XO排名"
  },
  "Không Làm Phiền (DND)": {
    "en": "Do Not Disturb (DND)",
    "ja": "邪魔しないでください (DND)",
    "cn": "请勿打扰 (DND)"
  },
  "Tàng Hình (Invisible)": {
    "en": "Invisible (Invisible)",
    "ja": "インビジブル（不可視）",
    "cn": "隐形"
  },
  "Khổng Lồ (25 - 150kg)": {
    "en": "Giant (25 - 150kg)",
    "ja": "巨人 (25 - 150kg)",
    "cn": "巨型（25 - 150 公斤）"
  },
  "Thần Thoại (>= 150kg)": {
    "en": "Mythical (>= 150kg)",
    "ja": "神話級 (>= 150kg)",
    "cn": "神话（>=150kg）"
  },
  "Lưu Số Lượng Vật Phẩm": {
    "en": "Save Item Quantity",
    "ja": "アイテム数量を保存",
    "cn": "保存商品数量"
  },
  "cho toàn bộ người chơi": {
    "en": "for all players",
    "ja": "すべてのプレイヤーのために！",
    "cn": "对于所有玩家"
  },
  "Danh mục vật phẩm tặng": {
    "en": "List of gift items",
    "ja": "ギフトアイテム一覧：",
    "cn": "捐赠物品清单"
  },
  "Nhập Mã ID Tùy Chỉnh": {
    "en": "Enter Custom ID Code",
    "ja": "カスタムIDコードを入力してください",
    "cn": "输入自定义 ID 代码"
  },
  "Thú Cưng Trong Rương:": {
    "en": "Pets in the Chest:",
    "ja": "チェストの中のペット:",
    "cn": "箱子里的宠物："
  },
  "Thú Cưng Trong Rương": {
    "en": "Pets in the Chest",
    "ja": "チェストの中のペット",
    "cn": "箱子里的宠物"
  },
  "Tên cần câu (kèm icon)": {
    "en": "Fishing rod name (with icon)",
    "ja": "釣り竿名（アイコン付き）：",
    "cn": "鱼竿名称（带图标）"
  },
  "Thêm Cần Vào Hệ Thống": {
    "en": "Add Need to System",
    "ja": "システムにニーズを追加",
    "cn": "添加需要到系统"
  },
  "Tên mồi câu (kèm icon)": {
    "en": "Bait name (with icon)",
    "ja": "餌名 (アイコン付き)",
    "cn": "诱饵名称（带图标）"
  },
  "Thêm Mồi Vào Hệ Thống": {
    "en": "Add Bait to the System",
    "ja": "システムに餌を追加します",
    "cn": "向系统添加诱饵"
  },
  "Thêm Túi Vào Hệ Thống": {
    "en": "Add Bags to the System",
    "ja": "システムにバッグを追加する",
    "cn": "将袋子添加到系统中"
  },
  "FROG (Biến thành Ếch)": {
    "en": "FROG (Turn into a Frog)",
    "ja": "FROG (カエルに変身)",
    "cn": "青蛙（变成青蛙）"
  },
  "Mùa Màng & Thời Tiết": {
    "en": "Crops & Weather",
    "ja": "作物と天気",
    "cn": "农作物与天气"
  },
  "Bách Khoa Nông Nghiệp": {
    "en": "Agricultural Encyclopedia",
    "ja": "農業百科事典",
    "cn": "农业百科全书"
  },
  "Tạo Nông Sản Đột Biến": {
    "en": "Create Mutant Agricultural Products",
    "ja": "突然変異した農産物を作成する",
    "cn": "创造突变农产品"
  },
  "Dòng Enchant: Chưa có": {
    "en": "Enchant line: Not yet available",
    "ja": "エンチャントライン: まだ利用できません",
    "cn": "附魔线：暂未提供"
  },
  "Đặt Thăng Sao (0..20)": {
    "en": "Set Star Promotion (0..20)",
    "ja": "スタープロモーションを設定 (0..20)",
    "cn": "设置星增益 (0..20)"
  },
  "Hồi Phục 100% Thể Lực": {
    "en": "100% Physical Recovery",
    "ja": "100% 体力回復",
    "cn": "100% 体力恢复"
  },
  "Tên Thành Tựu Hiển Thị": {
    "en": "Achievement Name Displayed",
    "ja": "表示される実績名",
    "cn": "显示的成就名称"
  },
  "Bảng Xếp Hạng Nối Chữ": {
    "en": "Word Matching Chart",
    "ja": "単語一致チャート",
    "cn": "字母匹配表"
  },
  "Hạt Giống & Cây Trồng": {
    "en": "Seeds & Plants",
    "ja": "種子と植物",
    "cn": "种子和植物"
  },
  "Cấu hình Role Request": {
    "en": "Configure Role Request",
    "ja": "ロールリクエストを構成する",
    "cn": "配置角色请求"
  },
  "Lưu cấu hình MiniGame": {
    "en": "Save MiniGame configuration",
    "ja": "ミニゲーム設定を保存する",
    "cn": "保存小游戏配置"
  },
  "+ Thêm kênh miễn trừ": {
    "en": "+ Add exemption channel",
    "ja": "+ 除外チャネルを追加",
    "cn": "+ 添加豁免通道"
  },
  "Số emoji tối đa (3-30)": {
    "en": "Maximum number of emojis (3-30)",
    "ja": "絵文字の最大数 (3 ～ 30)",
    "cn": "表情符号最大数量（3-30）"
  },
  "Nút bấm (Button View)": {
    "en": "Button View",
    "ja": "ボタンビュー",
    "cn": "按钮视图"
  },
  "Liên Kết RCON & Query": {
    "en": "RCON Link & Query",
    "ja": "RCON リンクとクエリ",
    "cn": "RCON链接&查询"
  },
  "Kiểm Tra Kết Nối Live": {
    "en": "Check Live Connection",
    "ja": "ライブ接続を確認する",
    "cn": "检查实时连接"
  },
  "Khởi Tạo Giveaway Mới": {
    "en": "Start a New Giveaway",
    "ja": "新しいプレゼントを開始する",
    "cn": "创建新赠品"
  },
  "Ngày Cưới (YYYY-MM-DD)": {
    "en": "Wedding Date (YYYY-MM-DD)",
    "ja": "結婚式の日付 (YYYY-MM-DD)",
    "cn": "结婚日期（年-月-日）"
  },
  "Tìm theo ID hoặc Tên": {
    "en": "Search by ID or Name",
    "ja": "IDまたは名前で検索",
    "cn": "按 ID 或姓名搜索"
  },
  "Số MC Coin muốn nhận": {
    "en": "Number of MC Coins you want to receive",
    "ja": "受け取りたいMCコインの数",
    "cn": "您想收到的MC币数量"
  },
  "Tìm kiếm thành tựu...": {
    "en": "Looking for achievements...",
    "ja": "実績を求めて...",
    "cn": "寻找成就..."
  },
  "Tìm kiếm thành tựu": {
    "en": "Looking for achievements",
    "ja": "実績を求めて",
    "cn": "搜索成就"
  },
  "Mời Sakura vào Server": {
    "en": "Invite Sakura to the Server",
    "ja": "さくらをサーバーに招待する",
    "cn": "邀请小樱加入服务器"
  },
  "Tên hiển thị / Ghi chú": {
    "en": "Display Name / Notes",
    "ja": "表示名/メモ",
    "cn": "显示名称/注释"
  },
  "Máy chủ hỗ trợ Discord": {
    "en": "Discord supported servers",
    "ja": "Discord がサポートするサーバー",
    "cn": "服务器支持Discord"
  },
  "Kênh GitHub chính thức": {
    "en": "Official GitHub channel",
    "ja": "公式 GitHub チャンネル",
    "cn": "官方 GitHub 频道"
  },
  "Trung Bình (Kỳ Thủ)": {
    "en": "Average (Player)",
    "ja": "平均 (プレイヤー)",
    "cn": "平均（球员）"
  },
  "AI đang tính toán...": {
    "en": "AI is calculating...",
    "ja": "AIが計算中です...",
    "cn": "AI正在计算..."
  },
  "AI đang tính toán": {
    "en": "AI is calculating",
    "ja": "AIが計算中です",
    "cn": "AI正在计算"
  },
  "Bảng Xếp Hạng Cờ Vua": {
    "en": "Chess Rankings",
    "ja": "チェスランキング",
    "cn": "国际象棋排名"
  },
  "Số người chơi tối đa": {
    "en": "Maximum number of players",
    "ja": "最大プレイヤー数",
    "cn": "最大玩家人数"
  },
  "Chuẩn bị bảng vẽ...": {
    "en": "Prepare the drawing board...",
    "ja": "製図板を準備してください...",
    "cn": "准备画板..."
  },
  "Chuẩn bị bảng vẽ": {
    "en": "Prepare the drawing board",
    "ja": "製図板を準備してください",
    "cn": "准备画板"
  },
  "Nối Từ — Sakura Game": {
    "en": "Word Matching — Sakura Game",
    "ja": "単語マッチング — さくらゲーム",
    "cn": "匹配单词 — 樱花游戏"
  },
  "Cường hóa (+0 - +300)": {
    "en": "Enhance (+0 - +300)",
    "ja": "エンハンス (+0 ～ +300)",
    "cn": "增强 (+0 - +300)"
  },
  "Cấp Cần Câu Cho User": {
    "en": "Providing Fishing Rods to Users",
    "ja": "ユーザーへの釣り竿の提供",
    "cn": "为用户提供钓鱼竿"
  },
  "Vật phẩm ẩn (Secret)": {
    "en": "Hidden items (Secret)",
    "ja": "隠しアイテム（シークレット）",
    "cn": "隐藏物品（秘密）"
  },
  "Tỉ Lệ Rơi Khi Câu (%)": {
    "en": "Fishing Drop Rate (%)",
    "ja": "釣りドロップ率 (%)",
    "cn": "钓鱼掉落率(%)"
  },
  "Mồi Câu Trong Rương:": {
    "en": "Fishing Lures in the Chest:",
    "ja": "チェスト内の釣りルアー:",
    "cn": "箱子里的鱼饵："
  },
  "Mồi Câu Trong Rương": {
    "en": "Fishing Lures in the Chest",
    "ja": "チェスト内の釣りルアー",
    "cn": "胸部的鱼饵"
  },
  "Tỉ Lệ Cá Đột Biến Gen": {
    "en": "Rate of Genetically Mutated Fish",
    "ja": "遺伝子変異した魚の割合",
    "cn": "鱼类基因突变率"
  },
  "Nông Cụ & Lồng Kính": {
    "en": "Farm Tools & Glass Cages",
    "ja": "農具とガラスケージ",
    "cn": "农具和玻璃笼"
  },
  "Có hạn sử dụng (HSD)": {
    "en": "Expiry date (HSD)",
    "ja": "有効期限 (HSD)",
    "cn": "有效期（HSD）"
  },
  "Số phút đóng băng (VD": {
    "en": "Number of freezing minutes (eg",
    "ja": "フリーズする分数 (例",
    "cn": "冻结分钟数（例如"
  },
  "Thời hạn hiệu lực (VD": {
    "en": "Validity period (eg",
    "ja": "有効期間 (例",
    "cn": "有效期（例如"
  },
  "Tạo Cuốc / Quặng Mới": {
    "en": "Create New Pickaxe/Ore",
    "ja": "新しいつるはし/鉱石を作成",
    "cn": "创建新的镐/矿石"
  },
  "Tiến Hành Nối Server": {
    "en": "Proceed to connect to the server",
    "ja": "サーバーへの接続に進みます",
    "cn": "继续连接到服务器"
  },
  "Lưu Hồ Sơ Bot Server": {
    "en": "Save Bot Server Profile",
    "ja": "ボットサーバープロファイルを保存",
    "cn": "保存机器人服务器配置文件"
  },
  "Danh sách cấm server": {
    "en": "Server banned list",
    "ja": "サーバー禁止リスト",
    "cn": "服务器禁止列表"
  },
  "Trạng thái TempVoice": {
    "en": "TempVoice status",
    "ja": "TempVoice ステータス",
    "cn": "临时语音状态"
  },
  "Xóa tất cả kênh câu": {
    "en": "Delete all fishing channels",
    "ja": "すべての釣りチャンネルを削除します",
    "cn": "删除所有钓鱼频道"
  },
  "Thả Reaction (Emoji)": {
    "en": "Drop Reaction (Emoji)",
    "ja": "ドロップリアクション (絵文字)",
    "cn": "掉落反应（表情符号）"
  },
  "Chỉ số May mắn (Luck)": {
    "en": "Luck Index (Luck)",
    "ja": "運指数（運）：",
    "cn": "幸运指数（运气）"
  },
  "Cường Hóa (+0 - +300)": {
    "en": "Enhancement (+0 - +300)",
    "ja": "強化 (+0 ～ +300)",
    "cn": "增强（+0 - +300）"
  },
  "Chỉ Số May Mắn (Luck)": {
    "en": "Luck Index (Luck)",
    "ja": "運指数（運）：",
    "cn": "幸运指数（运气）"
  },
  "Tìm kiếm vật phẩm...": {
    "en": "Search for items...",
    "ja": "アイテムを検索...",
    "cn": "搜索项目..."
  },
  "Tìm kiếm vật phẩm": {
    "en": "Search for items",
    "ja": "アイテムを検索",
    "cn": "搜索项目"
  },
  "Số MC Coin muốn rút": {
    "en": "Number of MC Coins you want to withdraw",
    "ja": "出金したいMCコインの数",
    "cn": "您想要提取的MC币数量"
  },
  "TẠM BIỆT THÀNH VIÊN!": {
    "en": "GOODBYE MEMBERS!",
    "ja": "メンバーの皆さん、さようなら！",
    "cn": "再见会员！"
  },
  "TẠM BIỆT THÀNH VIÊN": {
    "en": "GOODBYE MEMBERS",
    "ja": "メンバーの皆さん、さようなら！",
    "cn": "再见会员"
  },
  "Trang chủ giới thiệu": {
    "en": "Introduction home page",
    "ja": "紹介ホームページ",
    "cn": "简介首页"
  },
  "Câu cá RPG Đại Dương": {
    "en": "Ocean RPG Fishing",
    "ja": "海洋 RPG 釣り",
    "cn": "海洋角色扮演钓鱼"
  },
  "Người chơi trực tuyến": {
    "en": "Online players",
    "ja": "オンラインプレイヤー",
    "cn": "在线玩家"
  },
  "của máy chủ Minecraft": {
    "en": "of the Minecraft server",
    "ja": "Minecraftサーバーの。",
    "cn": "Minecraft 服务器的"
  },
  "Báo lỗi (Bug Report)": {
    "en": "Bug Report",
    "ja": "バグレポート",
    "cn": "错误报告"
  },
  "Thông tin tài chính": {
    "en": "Financial information",
    "ja": "財務情報",
    "cn": "财务信息"
  },
  "Discord URL hoặc ID": {
    "en": "Discord URL or ID",
    "ja": "DiscordのURLまたはID",
    "cn": "不一致 URL 或 ID"
  },
  "Tìm kiếm tệp tin...": {
    "en": "Search files...",
    "ja": "ファイルを検索...",
    "cn": "搜索文件..."
  },
  "Tìm kiếm tệp tin": {
    "en": "Search files",
    "ja": "ファイルを検索",
    "cn": "搜索文件"
  },
  "Mời Bạn Chơi Cờ Vua": {
    "en": "Invite You to Play Chess",
    "ja": "チェスに招待します",
    "cn": "邀您下棋"
  },
  "Trực Tuyến (Online)": {
    "en": "Online",
    "ja": "オンライン",
    "cn": "在线（在线）"
  },
  "Danh Sách Thành Tựu": {
    "en": "List of Achievements",
    "ja": "実績リスト",
    "cn": "成就清单"
  },
  "Rương Báu & Hòm Quà": {
    "en": "Treasure Chest & Gift Box",
    "ja": "宝箱とギフトボックス",
    "cn": "宝箱和礼品盒"
  },
  "Khoáng Sản & Đá Quý": {
    "en": "Minerals & Gems",
    "ja": "鉱物と宝石",
    "cn": "矿物和宝石"
  },
  "Hạt Giống Nông Trại": {
    "en": "Farm Seeds",
    "ja": "農場の種子",
    "cn": "农场种子"
  },
  "Chọn vật phẩm cụ thể": {
    "en": "Select specific items",
    "ja": "特定の項目を選択します",
    "cn": "选择特定项目"
  },
  "Đang ẩn (Không bán)": {
    "en": "Hidden (Not for sale)",
    "ja": "隠し（非売品）",
    "cn": "隐藏（非卖品）"
  },
  "Mô tả vật phẩm troll": {
    "en": "Troll item description",
    "ja": "トロールアイテムの説明",
    "cn": "巨魔物品描述"
  },
  "Tùy chọn độ mạnh (VD": {
    "en": "Strength options (eg",
    "ja": "強度のオプション (例",
    "cn": "强度选项（例如"
  },
  "Số phút hiệu lực (VD": {
    "en": "Number of minutes of validity (eg",
    "ja": "有効期限の分数 (例",
    "cn": "有效分钟数（例如"
  },
  "Dụng Cụ & Phân Bón": {
    "en": "Tools & Fertilizers",
    "ja": "道具と肥料",
    "cn": "工具和肥料"
  },
  "Bách Khoa Mỏ Khoáng": {
    "en": "Mineral Mining Encyclopedia",
    "ja": "鉱物採掘百科事典",
    "cn": "矿产开采百科全书"
  },
  "Danh Mục & Cấp Phát": {
    "en": "Catalog & Allocation",
    "ja": "カタログと割り当て",
    "cn": "目录及分配"
  },
  "Đang tải từ điển...": {
    "en": "Loading dictionary...",
    "ja": "辞書を読み込み中...",
    "cn": "正在加载词典..."
  },
  "Đang tải từ điển": {
    "en": "Loading dictionary",
    "ja": "辞書を読み込み中",
    "cn": "加载字典"
  },
  "Thần Thoại (Mythic)": {
    "en": "Mythic",
    "ja": "ミシック",
    "cn": "神话"
  },
  "Đổi Trạng Thái Vote": {
    "en": "Change Vote Status",
    "ja": "投票ステータスを変更する",
    "cn": "更改投票状态"
  },
  "Đang tải danh sách": {
    "en": "Loading list",
    "ja": "リストを読み込んでいます",
    "cn": "加载列表"
  },
  "Tạo Bản Sao Lưu Mới": {
    "en": "Create New Backup",
    "ja": "新しいバックアップを作成する",
    "cn": "创建新备份"
  },
  "vào server Minecraft": {
    "en": "Go to the Minecraft server",
    "ja": "Minecraft サーバーに移動します。",
    "cn": "前往我的世界服务器"
  },
  "Bảng xếp hạng Level": {
    "en": "Level rankings",
    "ja": "レベルランキング",
    "cn": "等级排名"
  },
  "Tạo Profile Của Bạn": {
    "en": "Create Your Profile",
    "ja": "プロフィールを作成する",
    "cn": "创建您的个人资料"
  },
  "Chia Sẻ Bio Cá Nhân": {
    "en": "Share Personal Bio",
    "ja": "個人的な経歴を共有する",
    "cn": "分享个人简介"
  },
  "Miễn trừ trách nhiệm": {
    "en": "Disclaimer",
    "ja": "免責事項",
    "cn": "免责声明"
  },
  "Hôn Nhân & Cặp Đôi": {
    "en": "Marriage & Couples",
    "ja": "結婚とカップル",
    "cn": "婚姻与情侣"
  },
  "Mời bot vào server": {
    "en": "Invite bots to the server",
    "ja": "ボットをサーバーに招待する",
    "cn": "邀请机器人到服务器"
  },
  "Tổng Quan Hệ Thống": {
    "en": "System Overview",
    "ja": "システム概要",
    "cn": "系统概述"
  },
  "Chế độ người dùng:": {
    "en": "User Mode:",
    "ja": "ユーザーモード:",
    "cn": "用户模式："
  },
  "Chế độ người dùng": {
    "en": "User Mode",
    "ja": "ユーザーモード",
    "cn": "用户模式"
  },
  "Chọn Server Áp Dụng": {
    "en": "Select Applicable Server",
    "ja": "該当するサーバーを選択してください",
    "cn": "选择适用的服务器"
  },
  "Câu Cá & Thủy Cung": {
    "en": "Fishing & Aquarium",
    "ja": "釣りと水族館",
    "cn": "钓鱼和水族馆"
  },
  "Nông Trại & Mùa Vụ": {
    "en": "Farms & Crops",
    "ja": "農場と作物",
    "cn": "农场和农作物"
  },
  "Đột biến (Mutation)": {
    "en": "Mutation",
    "ja": "突然変異",
    "cn": "突变"
  },
  "Rương Báu (Chests)": {
    "en": "Chests",
    "ja": "チェスト",
    "cn": "宝箱"
  },
  "Dọn Sạch Thủy Cung": {
    "en": "Clean the Aquarium",
    "ja": "水族館を掃除する",
    "cn": "清洁水族馆"
  },
  "Nông Cụ & Công Cụ": {
    "en": "Farm Tools & Tools",
    "ja": "農具と工具",
    "cn": "农具及工具"
  },
  "Chỉ bán trong Shop": {
    "en": "Only sold in Shop",
    "ja": "ショップのみで販売",
    "cn": "仅在商店出售"
  },
  "Thần Thoại / Admin": {
    "en": "Mythology / Admin",
    "ja": "神話 / 管理者",
    "cn": "神话/管理员"
  },
  "Linh vật: Chưa đặt": {
    "en": "Mascot: Not set yet",
    "ja": "マスコット: まだ設定されていません",
    "cn": "吉祥物：尚未确定"
  },
  "Đang bán công khai": {
    "en": "On public sale",
    "ja": "一般販売中",
    "cn": "公开发售"
  },
  "Thần Thánh (Admin)": {
    "en": "Divine (Admin)",
    "ja": "ディバイン（管理者）",
    "cn": "圣灵（管理员）"
  },
  "SLAP (Tát bằng cá)": {
    "en": "SLAP (Slap with fish)",
    "ja": "SLAP (魚を叩く)",
    "cn": "SLAP（用鱼拍打）"
  },
  "Cứu Cây & Diệt Sâu": {
    "en": "Save Trees & Kill Pests",
    "ja": "木を守り、害虫を殺す",
    "cn": "拯救树木并杀死害虫"
  },
  "Cập Nhật Hạt Giống": {
    "en": "Update Seeds",
    "ja": "シードを更新する",
    "cn": "更新种子"
  },
  "Mùa Đông (Winter)": {
    "en": "Winter",
    "ja": "冬",
    "cn": "冬天"
  },
  "Cuốc Đào Trang Bị": {
    "en": "Equipped Digging Hoe",
    "ja": "装備された掘鍬",
    "cn": "设备 挖掘锄头"
  },
  "Tặng Quặng Vào Túi": {
    "en": "Give Ore Into Bag",
    "ja": "鉱石を袋に入れる",
    "cn": "将矿石装入袋中"
  },
  "Thêm Vật Tư Hầm Mỏ": {
    "en": "More Mining Supplies",
    "ja": "その他の採掘用品",
    "cn": "更多采矿用品"
  },
  "Làm mới người chơi": {
    "en": "Refresh players",
    "ja": "プレーヤーを更新する",
    "cn": "刷新玩家"
  },
  "Cộng Đồng & Xã Hội": {
    "en": "Community & Society",
    "ja": "コミュニティと社会",
    "cn": "社区与社会"
  },
  "Mầm Bệnh Cây Trồng": {
    "en": "Plant Pathogens",
    "ja": "植物病原体",
    "cn": "植物病原体"
  },
  "Blacklist toàn cục": {
    "en": "Global Blacklist",
    "ja": "グローバルブラックリスト",
    "cn": "全球黑名单"
  },
  "Lưu Cài Đặt Câu Cá": {
    "en": "Save Fishing Settings",
    "ja": "釣り設定を保存",
    "cn": "保存钓鱼设置"
  },
  "Thêm Role Vào Bảng": {
    "en": "Add Roles to the Table",
    "ja": "テーブルに役割を追加する",
    "cn": "将角色添加到表中"
  },
  "Chân Trang (Footer)": {
    "en": "Footer",
    "ja": "フッター",
    "cn": "页脚"
  },
  "Độ bền (Durability)": {
    "en": "Durability",
    "ja": "耐久性",
    "cn": "耐用性"
  },
  "An toàn & Bảo mật": {
    "en": "Safe & Secure",
    "ja": "安心安全",
    "cn": "安全与安保"
  },
  "AutoMod & Bảo mật": {
    "en": "AutoMod & Security",
    "ja": "AutoMod とセキュリティ",
    "cn": "汽车改装与安全"
  },
  "Kênh hỗ trợ Ticket": {
    "en": "Ticket support channel",
    "ja": "チケットサポートチャンネル",
    "cn": "票务支持渠道"
  },
  "Kênh hỗ trợ Discord": {
    "en": "Discord support channel",
    "ja": "Discord サポート チャネル",
    "cn": "不和谐支持频道"
  },
  "Câu Hỏi Thường Gặp": {
    "en": "Frequently Asked Questions",
    "ja": "よくある質問",
    "cn": "常见问题解答"
  },
  "Đổi tên hiển thị": {
    "en": "Change display name",
    "ja": "表示名を変更する",
    "cn": "更改显示名称"
  },
  "Tiến độ hoàn thành": {
    "en": "Completion progress",
    "ja": "完了の進捗状況",
    "cn": "进度已完成"
  },
  "Xuất Kết Quả JSON": {
    "en": "Export JSON Result",
    "ja": "JSON結果をエクスポート",
    "cn": "输出 JSON 结果"
  },
  "Cờ Vua Sakura AI": {
    "en": "Chess Sakura AI",
    "ja": "チェスさくらAI",
    "cn": "国际象棋樱花AI"
  },
  "Quy tắc thông minh": {
    "en": "Smart rules",
    "ja": "賢いルール",
    "cn": "智能规则"
  },
  "Nhập tên của bạn": {
    "en": "Enter your name",
    "ja": "あなたの名前を入力してください",
    "cn": "输入你的名字"
  },
  "Mời Bạn Chơi Caro": {
    "en": "We invite you to play Caro",
    "ja": "カロをプレイしてみませんか",
    "cn": "邀您玩卡罗"
  },
  "Chuyển Trạng Thái": {
    "en": "Change Status",
    "ja": "ステータス変更",
    "cn": "开关状态"
  },
  "To Lớn (6 - 25kg)": {
    "en": "Large (6 - 25kg)",
    "ja": "ラージ（6～25kg）",
    "cn": "大号（6 - 25 公斤）"
  },
  "Tất cả trạng thái": {
    "en": "All statuses",
    "ja": "すべてのステータス",
    "cn": "所有状态"
  },
  "Danh Mục Cửa Hàng": {
    "en": "Store Directory",
    "ja": "ストアディレクトリ",
    "cn": "商店目录"
  },
  "Không thể gia hạn": {
    "en": "Cannot be extended",
    "ja": "延長不可",
    "cn": "无法延长"
  },
  "Số tiền hoặc % (VD": {
    "en": "Amount or % (eg",
    "ja": "量または% (例",
    "cn": "金额或%（例如"
  },
  "Thiệt hại coin (VD": {
    "en": "Coin damage (eg",
    "ja": "コインのダメージ (例",
    "cn": "硬币损坏（例如"
  },
  "Mùa Xuân (Spring)": {
    "en": "Spring",
    "ja": "春",
    "cn": "春天"
  },
  "Các Loại Đột Biến": {
    "en": "Types of Mutations",
    "ja": "突然変異の種類",
    "cn": "突变类型"
  },
  "Sửa Tối Đa Độ Bền": {
    "en": "Maximum Repair Durability",
    "ja": "最大の修理耐久性",
    "cn": "修复最大耐久性"
  },
  "Lưu Cấu Hình Kênh": {
    "en": "Save Channel Configuration",
    "ja": "チャンネル設定を保存",
    "cn": "保存通道配置"
  },
  "Tạo Thành Tựu Mới": {
    "en": "Create New Achievements",
    "ja": "新しい実績を作成する",
    "cn": "创造新业绩"
  },
  "Thu Hồi Thành Tựu": {
    "en": "Withdraw Achievements",
    "ja": "実績を撤回する",
    "cn": "撤回成就"
  },
  "Danh Mục Phân Loại": {
    "en": "Classification Category",
    "ja": "分類カテゴリー",
    "cn": "类别 类别"
  },
  "Phân Bón Sinh Học": {
    "en": "Biological Fertilizer",
    "ja": "生物肥料",
    "cn": "生物肥料"
  },
  "Dụng Cụ Canh Tác": {
    "en": "Farming Tools",
    "ja": "農具",
    "cn": "农具"
  },
  "Làm Mới Danh Sách": {
    "en": "Refresh List",
    "ja": "リストを更新",
    "cn": "刷新列表"
  },
  "Người Dùng Thường": {
    "en": "Regular Users",
    "ja": "通常のユーザー",
    "cn": "普通用户"
  },
  "Đăng panel Ticket": {
    "en": "Post the Ticket panel",
    "ja": "チケットパネルを投稿する",
    "cn": "发布票务面板"
  },
  "Bảng cài đặt kênh": {
    "en": "Channel settings panel",
    "ja": "チャンネル設定パネル",
    "cn": "通道设置面板"
  },
  "Kênh Đăng Giveaway": {
    "en": "Giveaway Posting Channel",
    "ja": "プレゼント投稿チャンネル",
    "cn": "频道帖子赠品"
  },
  "Số phút, số tiền": {
    "en": "Number of minutes, amount of money",
    "ja": "時間や金額など",
    "cn": "分钟数、金额"
  },
  "Đăng Nhập Discord": {
    "en": "Login to Discord",
    "ja": "Discordにログイン",
    "cn": "登录不和谐"
  },
  "Xem thư viện ảnh": {
    "en": "View photo gallery",
    "ja": "フォトギャラリーを見る",
    "cn": "查看照片库"
  },
  "Hướng dẫn sử dụng": {
    "en": "Instructions for use",
    "ja": "使用説明書",
    "cn": "使用说明"
  },
  "Chi Tiết Quyền Hạn": {
    "en": "Power Details",
    "ja": "電力の詳細",
    "cn": "电源详情"
  },
  "Bật / Tắt Máy Chủ": {
    "en": "Enable/Disable Server",
    "ja": "サーバーを有効/無効にする",
    "cn": "启用/禁用服务器"
  },
  "Hướng dẫn cài đặt": {
    "en": "Installation instructions",
    "ja": "インストール手順",
    "cn": "安装说明"
  },
  "Xem Danh Sách Bio": {
    "en": "View Bio List",
    "ja": "略歴リストを見る",
    "cn": "查看简历列表"
  },
  "Gửi Phản Hồi Ngay": {
    "en": "Send Feedback Now",
    "ja": "今すぐフィードバックを送信",
    "cn": "立即发送反馈"
  },
  "Ủng Hộ Sakura Bot": {
    "en": "Support Sakura Bot",
    "ja": "さくらボットをサポート",
    "cn": "支持樱花机器人"
  },
  "Mã hóa & Giải mã": {
    "en": "Encoding & Decoding",
    "ja": "エンコードとデコード",
    "cn": "编码与解码"
  },
  "Khó (Kiện Tướng)": {
    "en": "Difficult (Grandmaster)",
    "ja": "難しい (グランドマスター)",
    "cn": "困难（宗师）"
  },
  "Ngôn ngữ từ vựng": {
    "en": "Vocabulary language",
    "ja": "語彙言語",
    "cn": "词汇语言"
  },
  "ĐẾN LƯỢT BẠN VẼ!": {
    "en": "IT'S YOUR TURN TO DRAW!",
    "ja": "あなたが絵を描く番です!",
    "cn": "轮到你抽奖了！"
  },
  "ĐẾN LƯỢT BẠN VẼ": {
    "en": "IT'S YOUR TURN TO DRAW",
    "ja": "あなたが絵を描く番です",
    "cn": "轮到你抽奖了"
  },
  "Mời Bạn Tham Gia": {
    "en": "We invite you to join",
    "ja": "ぜひご参加ください",
    "cn": "我们邀请您加入"
  },
  "Cấu hình server": {
    "en": "Server configuration",
    "ja": "サーバー構成",
    "cn": "服务器配置"
  },
  "Nối Từ & Trí Tuệ": {
    "en": "Word Connection & Wisdom",
    "ja": "言葉のつながりと知恵",
    "cn": "连接言语与智慧"
  },
  "Quản Lý Giftcode": {
    "en": "Giftcode Management",
    "ja": "ギフトコード管理",
    "cn": "礼品码管理"
  },
  "Xem Bể Thủy Cung": {
    "en": "See the Aquarium",
    "ja": "水族館を見る",
    "cn": "查看水族馆"
  },
  "Thao Túng Tỉ Lệ": {
    "en": "Scale Manipulation",
    "ja": "スケールの操作",
    "cn": "规模操纵"
  },
  "Phân hạng kích cỡ": {
    "en": "Size classification",
    "ja": "サイズ分類",
    "cn": "尺寸分类"
  },
  "Số sao (0 - 20 ⭐)": {
    "en": "Number of stars (0 - 20 ⭐)",
    "ja": "星の数 (0 - 20 ⭐)",
    "cn": "星星数量（0 - 20 ⭐）"
  },
  "Danh mục vật phẩm": {
    "en": "Item categories",
    "ja": "アイテムカテゴリ",
    "cn": "物品清单"
  },
  "Thêm Vào Gói Quà": {
    "en": "Add to Gift Wrapping",
    "ja": "ギフトラッピングに追加",
    "cn": "添加到礼品包装"
  },
  "Tiện Ích & Troll": {
    "en": "Gadgets & Trolls",
    "ja": "ガジェットとトロール",
    "cn": "小工具和巨魔"
  },
  "Loại tiền gia hạn": {
    "en": "Renewal currency",
    "ja": "更新通貨",
    "cn": "续订货币类型"
  },
  "Biệt danh mới (VD": {
    "en": "New nickname (eg",
    "ja": "新しいニックネーム (例",
    "cn": "新昵称（例如"
  },
  "Quản Lý Nông Dân": {
    "en": "Farmer Management",
    "ja": "農家の管理",
    "cn": "农民管理"
  },
  "Cập Nhật Hoa Màu": {
    "en": "Update Flower Colors",
    "ja": "花の色を更新",
    "cn": "更新花朵颜色"
  },
  "Thêm Nguyên Liệu": {
    "en": "Add Ingredients",
    "ja": "材料を追加する",
    "cn": "添加成分"
  },
  "Mùa Hạ (Summer)": {
    "en": "Summer",
    "ja": "夏",
    "cn": "夏季"
  },
  "Mùa Thu (Autumn)": {
    "en": "Autumn (Autumn)",
    "ja": "秋(秋)",
    "cn": "秋季（秋季）"
  },
  "Tạo Vật Phẩm Mới": {
    "en": "Create New Items",
    "ja": "新しいアイテムを作成する",
    "cn": "创建新项目"
  },
  "Khoáng Sản (Ore)": {
    "en": "Minerals (Ore)",
    "ja": "鉱物（鉱石）",
    "cn": "矿物（矿石）"
  },
  "Tạo Giveaway Mới": {
    "en": "Create New Giveaway",
    "ja": "新しい特典を作成する",
    "cn": "创建新赠品"
  },
  "Cài Đặt Máy Chủ": {
    "en": "Server Settings",
    "ja": "サーバー設定",
    "cn": "服务器设置"
  },
  "Prefix Của Server": {
    "en": "Server Prefix",
    "ja": "サーバープレフィックス",
    "cn": "服务器前缀"
  },
  "Danh sách global": {
    "en": "Global list",
    "ja": "グローバルリスト",
    "cn": "全局列表"
  },
  "Bắt Đầu Giveaway": {
    "en": "Start Giveaway",
    "ja": "プレゼントを開始",
    "cn": "开始赠品"
  },
  "Thời Lượng (Phút)": {
    "en": "Duration (Minutes)",
    "ja": "所要時間 (分)",
    "cn": "持续时间（分钟）"
  },
  "Quỹ Chung (Coins)": {
    "en": "General Fund (Coins)",
    "ja": "一般資金 (コイン)",
    "cn": "普通基金（硬币）"
  },
  "Số Sao (0 - 20 ⭐)": {
    "en": "Number of Stars (0 - 20 ⭐)",
    "ja": "星の数 (0 ～ 20 ⭐)",
    "cn": "星星数量（0 - 20 ⭐）"
  },
  "Mật Khẩu Quản Trị": {
    "en": "Admin Password",
    "ja": "管理者パスワード",
    "cn": "管理员密码"
  },
  "Thêm từ cấm mới": {
    "en": "Add new forbidden words",
    "ja": "新しい禁止用語を追加",
    "cn": "添加新的禁用词"
  },
  "Nhập Discord ID": {
    "en": "Enter Discord ID",
    "ja": "Discord IDを入力してください",
    "cn": "输入您的 Discord ID"
  },
  "Địa chỉ IP & Cổng": {
    "en": "IP Address & Port",
    "ja": "IPアドレスとポート",
    "cn": "IP地址和端口"
  },
  "Tải plugin ngay": {
    "en": "Download the plugin now",
    "ja": "今すぐプラグインをダウンロードしてください",
    "cn": "立即下载插件"
  },
  "Cập nhật lần cuối": {
    "en": "Last updated",
    "ja": "最終更新日",
    "cn": "最后更新"
  },
  "Của Người Khác (": {
    "en": "Other People's (",
    "ja": "他の人 (",
    "cn": "其他人的（"
  },
  "Coins tích lũy:": {
    "en": "Accumulated Coins:",
    "ja": "蓄積されたコイン:",
    "cn": "累积金币："
  },
  "Coins tích lũy": {
    "en": "Accumulated Coins",
    "ja": "蓄積されたコイン",
    "cn": "金币累积"
  },
  "Nối Từ & Đố Vui": {
    "en": "Word Matching & Fun Quiz",
    "ja": "単語マッチングと楽しいクイズ",
    "cn": "单词匹配和测验"
  },
  "Xã Hội & Cấp Độ": {
    "en": "Society & Level",
    "ja": "社会とレベル",
    "cn": "社会与水平"
  },
  "Xem Trước HTML": {
    "en": "HTML Preview",
    "ja": "HTML プレビュー",
    "cn": "预览 HTML"
  },
  "2 Người (Local)": {
    "en": "2 People (Local)",
    "ja": "2名（現地）",
    "cn": "2人（本地）"
  },
  "Copy Link Phòng": {
    "en": "Copy Room Link",
    "ja": "ルームリンクをコピー",
    "cn": "复制房间链接"
  },
  "Bot Sakura: Tắt": {
    "en": "Bot Sakura: Off",
    "ja": "ボットさくら: オフ",
    "cn": "机器人樱花：关闭"
  },
  "KẾT THÚC VÁN ĐẤU": {
    "en": "END OF THE GAME",
    "ja": "ゲーム終了！",
    "cn": "游戏结束"
  },
  "Gõ từ bạn đoán": {
    "en": "Type the word you guess",
    "ja": "推測した単語を入力してください",
    "cn": "输入你猜的单词"
  },
  "Thích nét vẽ này": {
    "en": "Love this drawing",
    "ja": "この絵が大好きです",
    "cn": "喜欢这幅画"
  },
  "Coins (Thường):": {
    "en": "Coins (Regular):",
    "ja": "コイン (通常):",
    "cn": "硬币（普通）："
  },
  "Coins (Thường)": {
    "en": "Coins (Regular)",
    "ja": "コイン (通常)",
    "cn": "硬币（普通）"
  },
  "Tất Cả Danh Mục": {
    "en": "All Categories",
    "ja": "すべてのカテゴリ",
    "cn": "所有类别"
  },
  "Quản Lý Cần Thủ": {
    "en": "Fishing Manager",
    "ja": "釣りマネージャー",
    "cn": "钓鱼经理"
  },
  "Xóa Sạch Giỏ Cá": {
    "en": "Clear Fish Basket",
    "ja": "クリアフィッシュバスケット",
    "cn": "透明鱼篮"
  },
  "Trọng lượng (kg)": {
    "en": "Weight (kg)",
    "ja": "重量 (kg)",
    "cn": "重量（公斤）"
  },
  "Tự động theo kg": {
    "en": "Automatically according to kg",
    "ja": "kgに応じて自動的に",
    "cn": "自动按公斤"
  },
  "Bé Tí (< 1.5kg)": {
    "en": "Tiny Baby (< 1.5kg)",
    "ja": "小さな赤ちゃん (< 1.5kg)",
    "cn": "婴儿钛 (< 1.5kg)"
  },
  "Mồi Câu (Baits)": {
    "en": "Baits",
    "ja": "餌",
    "cn": "诱饵"
  },
  "Thường (Common)": {
    "en": "Common",
    "ja": "共通",
    "cn": "常见"
  },
  "Đặt Lượt Thích": {
    "en": "Set Likes",
    "ja": "いいねを設定する",
    "cn": "设置喜欢"
  },
  "Phân cấp độ hiếm": {
    "en": "Rarity classification",
    "ja": "レア度分類",
    "cn": "稀有度等级分类"
  },
  "Cho phép gia hạn": {
    "en": "Extension allowed",
    "ja": "許可される拡張子",
    "cn": "允许延期"
  },
  "Số phút mute (VD": {
    "en": "Number of mute minutes (eg",
    "ja": "ミュートの分数 (例",
    "cn": "静音分钟数（例如"
  },
  "Cập Nhật Sâu Bọ": {
    "en": "Pest Update",
    "ja": "害虫の最新情報",
    "cn": "蠕虫更新"
  },
  "Vật Phẩm Custom": {
    "en": "Custom Items",
    "ja": "カスタムアイテム",
    "cn": "定制项目"
  },
  "Quét Server Mới": {
    "en": "Scan New Server",
    "ja": "新しいサーバーをスキャン",
    "cn": "新服务器扫描"
  },
  "Đang nạp BXH...": {
    "en": "Loading rankings...",
    "ja": "ランキングを読み込み中...",
    "cn": "正在加载排名..."
  },
  "Đang nạp BXH": {
    "en": "Loading rankings",
    "ja": "ランキングを読み込み中",
    "cn": "加载排名"
  },
  "trực tiếp từ bot": {
    "en": "directly from bots",
    "ja": "ボットから直接。",
    "cn": "直接来自机器人"
  },
  "Cấp Quyền Admin": {
    "en": "Grant Admin Rights",
    "ja": "管理者権限を付与する",
    "cn": "授予管理员权限"
  },
  "Đăng panel Role": {
    "en": "Post the Role panel",
    "ja": "役割パネルを投稿する",
    "cn": "发布角色面板"
  },
  "Cấu hình Ticket": {
    "en": "Ticket configuration",
    "ja": "チケットの構成",
    "cn": "门票配置"
  },
  "Bộ lọc nâng cao": {
    "en": "Advanced filters",
    "ja": "高度なフィルター",
    "cn": "高级过滤器"
  },
  "Cấu hình Level": {
    "en": "Level configuration",
    "ja": "レベル構成",
    "cn": "级别配置"
  },
  "Lưu Kênh Streak": {
    "en": "Save Streak Channel",
    "ja": "ストリークチャンネルを保存",
    "cn": "保存频道连续记录"
  },
  "Liên Kết Plugin": {
    "en": "Plugin Link",
    "ja": "プラグインリンク",
    "cn": "插件链接"
  },
  "Bảng điều khiển": {
    "en": "Control panel",
    "ja": "コントロールパネル",
    "cn": "控制面板"
  },
  "Mã nguồn GitHub": {
    "en": "GitHub source code",
    "ja": "GitHub ソースコード",
    "cn": "GitHub 源代码"
  },
  "Phiên bản / Core": {
    "en": "Version/Core",
    "ja": "バージョン/コア",
    "cn": "版本/核心"
  },
  "Quản Lý Cơ Bản": {
    "en": "Basic Management",
    "ja": "基本的な管理",
    "cn": "基础管理"
  },
  "Quản Lý Tệp Tin": {
    "en": "File Management",
    "ja": "ファイル管理",
    "cn": "文件管理"
  },
  "Đã cập nhật icon": {
    "en": "Updated icon",
    "ja": "アイコンを更新しました！",
    "cn": "更新了图标"
  },
  "Tải lên avatar": {
    "en": "Upload avatar",
    "ja": "アバターをアップロード",
    "cn": "上传头像"
  },
  "Lịch sử nước đi": {
    "en": "Move history",
    "ja": "移動履歴",
    "cn": "移动历史记录"
  },
  "Số ký tự gợi ý": {
    "en": "Suggested number of characters",
    "ja": "推奨文字数",
    "cn": "建议的字符数"
  },
  "Vẽ khó hiểu quá": {
    "en": "Drawing is so confusing",
    "ja": "絵を描くのはとても混乱します！",
    "cn": "画图太难理解了"
  },
  "Đang kiểm tra": {
    "en": "Checking",
    "ja": "確認中",
    "cn": "检查"
  },
  "Cấp Cá Vào Giỏ": {
    "en": "Add Fish to Basket",
    "ja": "魚をバスケットに追加",
    "cn": "将鱼添加到篮子中"
  },
  "Gói quà đã thêm": {
    "en": "Gift wrapping added",
    "ja": "ギフトラッピングを追加しました",
    "cn": "添加了礼品包装"
  },
  "Thú Cưng (Pet)": {
    "en": "Pets",
    "ja": "ペット",
    "cn": "宠物"
  },
  "Vật Phẩm Troll": {
    "en": "Troll Items",
    "ja": "トロールアイテム",
    "cn": "巨魔物品"
  },
  "Báu Vật & Khác": {
    "en": "Treasures & Other",
    "ja": "宝物とその他",
    "cn": "宝藏及其他"
  },
  "Mô tả rương báu": {
    "en": "Treasure chest description",
    "ja": "宝箱の説明",
    "cn": "宝箱描述"
  },
  "Tỉ Lệ Khi Câu:": {
    "en": "Fishing Ratio:",
    "ja": "釣り比率:",
    "cn": "钓鱼比例："
  },
  "Tỉ Lệ Khi Câu": {
    "en": "Fishing Ratio",
    "ja": "釣り比率",
    "cn": "钓鱼时的比例"
  },
  "Thêm Cá Vào Bể": {
    "en": "Add Fish to the Tank",
    "ja": "水槽に魚を追加する",
    "cn": "将鱼添加到鱼缸中"
  },
  "Túi Cá Mở Rộng": {
    "en": "Expandable Fish Bag",
    "ja": "拡張可能なフィッシュバッグ",
    "cn": "膨化鱼袋"
  },
  "Thời hạn (Ngày)": {
    "en": "Term (Day)",
    "ja": "期間 (日)",
    "cn": "期限（天）"
  },
  "Có thể gia hạn": {
    "en": "Can be extended",
    "ja": "延長可能",
    "cn": "可以延长"
  },
  "Tham số giá trị": {
    "en": "Value parameter",
    "ja": "値パラメータ",
    "cn": "数值参数"
  },
  "Quản Lý Thợ Mỏ": {
    "en": "Miner Management",
    "ja": "マイナー管理",
    "cn": "矿工管理"
  },
  "Tra Cứu Thợ Mỏ": {
    "en": "Miner Lookup",
    "ja": "マイナー検索",
    "cn": "矿工查询"
  },
  "Dọn Túi Quặng": {
    "en": "Clean Out the Ore Bag",
    "ja": "鉱石バッグを掃除する",
    "cn": "清空矿石袋"
  },
  "Các Loại Quặng": {
    "en": "Types of Ore",
    "ja": "鉱石の種類",
    "cn": "矿石类型"
  },
  "Đột Biến Quặng": {
    "en": "Ore Mutation",
    "ja": "鉱石の突然変異",
    "cn": "矿石突变"
  },
  "Toàn thời gian": {
    "en": "Full time",
    "ja": "フルタイム",
    "cn": "全职"
  },
  "Sâu Bọ Gây Hại": {
    "en": "Harmful Pests",
    "ja": "有害な害虫",
    "cn": "有害害虫"
  },
  "Ngôn Ngữ Server": {
    "en": "Server Language",
    "ja": "サーバー言語",
    "cn": "服务器语言"
  },
  "Cài đặt chung": {
    "en": "General settings",
    "ja": "一般設定",
    "cn": "常规设置"
  },
  "Thống kê nhanh": {
    "en": "Quick statistics",
    "ja": "簡単な統計",
    "cn": "快速统计"
  },
  "Key hướng dẫn": {
    "en": "Key instructions",
    "ja": "重要な指示",
    "cn": "关键说明"
  },
  "Cung hoàng đạo": {
    "en": "Zodiac",
    "ja": "黄道帯",
    "cn": "十二生肖"
  },
  "Auto-Mod đang": {
    "en": "Auto-Mod is",
    "ja": "自動MODは",
    "cn": "自动模式是"
  },
  "Kênh miễn trừ": {
    "en": "Exempt channel",
    "ja": "免除チャンネル",
    "cn": "豁免通道"
  },
  "Tối thiểu ký tự": {
    "en": "Minimum characters",
    "ja": "最小文字数",
    "cn": "最少字符数"
  },
  "Thực thi nhanh": {
    "en": "Fast execution",
    "ja": "高速実行",
    "cn": "快速执行"
  },
  "Tên Phần Thưởng": {
    "en": "Reward Name",
    "ja": "報酬名",
    "cn": "奖励名称"
  },
  "Lưu Level & XP": {
    "en": "Save Level & XP",
    "ja": "レベルとXPを保存",
    "cn": "保存等级和经验值"
  },
  "Độ Bền Hiện Tại": {
    "en": "Current Durability",
    "ja": "現在の耐久性",
    "cn": "当前耐久性"
  },
  "Nhập mật khẩu": {
    "en": "Enter password",
    "ja": "パスワードを入力してください",
    "cn": "输入密码"
  },
  "Bạn mới bắt đầu": {
    "en": "Are you just starting out",
    "ja": "始めたばかりですか？",
    "cn": "你才刚刚开始"
  },
  "Xem Người Chơi": {
    "en": "View Players",
    "ja": "プレーヤーを見る",
    "cn": "查看玩家"
  },
  "Lưu Phân Quyền": {
    "en": "Save Decentralization",
    "ja": "分散化を保存",
    "cn": "节省电量"
  },
  "Cam kết bảo mật": {
    "en": "Privacy commitment",
    "ja": "プライバシーへの取り組み",
    "cn": "保密承诺"
  },
  "Hợp tác & Khác": {
    "en": "Collaboration & Others",
    "ja": "コラボレーションとその他",
    "cn": "合作及其他"
  },
  "Về Phòng Chờ": {
    "en": "Back to the Waiting Room",
    "ja": "待合室に戻ります",
    "cn": "返回候诊室"
  },
  "Chơi Lại Ngay": {
    "en": "Play Again Now",
    "ja": "今すぐもう一度プレイ",
    "cn": "现在再玩一次"
  },
  "Đang kết nối": {
    "en": "Connecting",
    "ja": "接続中",
    "cn": "正在连接"
  },
  "Lệnh nổi bật": {
    "en": "Outstanding command",
    "ja": "優れたコマンド",
    "cn": "指挥出色"
  },
  "Xem danh sách": {
    "en": "See list",
    "ja": "リストを見る",
    "cn": "查看列表"
  },
  "Đơn Vị Tiền Tệ": {
    "en": "Currency",
    "ja": "通貨",
    "cn": "货币单位"
  },
  "Cộng thêm (+)": {
    "en": "Plus (+)",
    "ja": "プラス (+)",
    "cn": "加号 (+)"
  },
  "Chiều dài (cm)": {
    "en": "Length (cm)",
    "ja": "長さ (cm)",
    "cn": "长度（厘米）"
  },
  "Độ bền ban đầu": {
    "en": "Initial durability",
    "ja": "初期耐久性：",
    "cn": "初始耐久性"
  },
  "0 Lượt Thích": {
    "en": "0 Likes",
    "ja": "0 いいね",
    "cn": "0 赞"
  },
  "Làm Mới Daily": {
    "en": "Refresh Daily",
    "ja": "毎日更新",
    "cn": "每日刷新"
  },
  "Coins thưởng:": {
    "en": "Bonus Coins:",
    "ja": "ボーナスコイン:",
    "cn": "奖励金币："
  },
  "Coins thưởng": {
    "en": "Bonus Coins",
    "ja": "ボーナスコイン",
    "cn": "奖励金币"
  },
  "Nông Sản Chín": {
    "en": "Ripe Agricultural Products",
    "ja": "熟した農産物",
    "cn": "成熟农产品"
  },
  "Sử Thi (Epic)": {
    "en": "Epic",
    "ja": "Epic",
    "cn": "史诗"
  },
  "Sinh Vật Biển": {
    "en": "Marine Creatures",
    "ja": "Marine Creatures",
    "cn": "海洋生物"
  },
  "Coin Tối Thiểu": {
    "en": "Minimum Coins",
    "ja": "最小コイン",
    "cn": "最低硬币"
  },
  "Đổi Sức Chứa": {
    "en": "Change Capacity",
    "ja": "容量の変更",
    "cn": "改变容量"
  },
  "Tải Lại Tỉ Lệ": {
    "en": "Reload Rate",
    "ja": "リロード速度",
    "cn": "重载率"
  },
  "Tạo Vật Phẩm": {
    "en": "Item Creation",
    "ja": "Item Creation",
    "cn": "创建项目"
  },
  "Cuốc Khai Mỏ": {
    "en": "Mining Pickaxe",
    "ja": "Mining Pickaxe",
    "cn": "采矿镐"
  },
  "Vật Tư Hầm Mỏ": {
    "en": "Mining Supplies",
    "ja": "Mining Supplies",
    "cn": "采矿用品"
  },
  "Hoa màu ưu đãi": {
    "en": "Preferential flower colors",
    "ja": "優先される花の色",
    "cn": "优先选择花色"
  },
  "Tặng Cuốc Mới": {
    "en": "Free New Hoe",
    "ja": "新しいホーを無料で入手",
    "cn": "免费新锄头"
  },
  "Kênh Discord": {
    "en": "Discord channel",
    "ja": "Discordチャンネル",
    "cn": "不和谐频道"
  },
  "Xóa màn hình": {
    "en": "Clear screen",
    "ja": "画面をクリア",
    "cn": "清晰的屏幕"
  },
  "Cấp Thành Tựu": {
    "en": "Achievement Level",
    "ja": "達成レベル",
    "cn": "成就等级"
  },
  "Mô Tả Vật Phẩm": {
    "en": "Item Description",
    "ja": "商品説明",
    "cn": "项目描述"
  },
  "Xóa Màn Hình": {
    "en": "Clear Screen",
    "ja": "画面をクリア",
    "cn": "清晰的屏幕"
  },
  "Quản Trị Viên": {
    "en": "Administrator",
    "ja": "管理者",
    "cn": "管理员"
  },
  "Câu cá (Fish)": {
    "en": "Fishing (Fish)",
    "ja": "釣り（魚）",
    "cn": "钓鱼（鱼）"
  },
  "Gửi thông báo": {
    "en": "Send notification",
    "ja": "通知を送信する",
    "cn": "发送通知"
  },
  "Bỏ qua ở kênh": {
    "en": "Skip to the channel",
    "ja": "チャンネルにスキップ",
    "cn": "跳至频道"
  },
  "Lưu Auto Role": {
    "en": "Save Auto Role",
    "ja": "自動ロールを保存",
    "cn": "保存自动角色"
  },
  "Gửi Thông Báo": {
    "en": "Send Notification",
    "ja": "通知を送信",
    "cn": "发送通知"
  },
  "Cấp Độ (Level)": {
    "en": "Level",
    "ja": "レベル",
    "cn": "级别"
  },
  "Mô tả chi tiết": {
    "en": "Detailed description",
    "ja": "詳細な説明",
    "cn": "详细说明"
  },
  "Nhập số tiền": {
    "en": "Enter amount",
    "ja": "金額を入力してください",
    "cn": "输入金额"
  },
  "Tiện Ích Khác": {
    "en": "Other Utilities",
    "ja": "その他のユーティリティ",
    "cn": "其他实用程序"
  },
  "Miễn phí 100%": {
    "en": "100% Free",
    "ja": "完全無料",
    "cn": "100% 免费"
  },
  "Quản lý hồ sơ": {
    "en": "Profile management",
    "ja": "プロフィール管理",
    "cn": "档案管理"
  },
  "PID Tiến trình": {
    "en": "Process PID",
    "ja": "プロセス PID",
    "cn": "过程PID"
  },
  "Vai Trò (Role)": {
    "en": "Role",
    "ja": "役割",
    "cn": "角色"
  },
  "Xem hướng dẫn": {
    "en": "See instructions",
    "ja": "手順を参照",
    "cn": "查看说明"
  },
  "Tổng tài sản": {
    "en": "Total assets",
    "ja": "総資産",
    "cn": "总资产"
  },
  "Bảng Dữ Liệu": {
    "en": "Data Table",
    "ja": "データテーブル",
    "cn": "数据表"
  },
  "Truy Vấn SQL": {
    "en": "SQL Query",
    "ja": "SQLクエリ",
    "cn": "SQL查询"
  },
  "Cần tối thiểu": {
    "en": "Minimum required",
    "ja": "最低限必要なもの",
    "cn": "最低要求"
  },
  "BẮT ĐẦU CHƠI": {
    "en": "START PLAYING",
    "ja": "プレイを開始",
    "cn": "开始玩"
  },
  "Hết thời gian": {
    "en": "Time's up",
    "ja": "時間切れです！",
    "cn": "时间到了"
  },
  "Thợ Săn Số 1": {
    "en": "Number 1 Hunter",
    "ja": "ナンバー1ハンター",
    "cn": "排名第一的猎人"
  },
  "Số lượng thêm": {
    "en": "Extra Quantity",
    "ja": "追加数量",
    "cn": "额外数量"
  },
  "Chọn vật phẩm": {
    "en": "Select item",
    "ja": "項目を選択してください",
    "cn": "选择项目"
  },
  "Sức Chứa Bể": {
    "en": "Tank Capacity",
    "ja": "タンク容量",
    "cn": "水箱容量"
  },
  "Phân Bón Đất": {
    "en": "Soil Fertilizer",
    "ja": "土壌肥料",
    "cn": "土壤肥料"
  },
  "Mô tả loài cá": {
    "en": "Fish description",
    "ja": "魚の説明",
    "cn": "鱼种描述"
  },
  "Coins • Tỉ lệ": {
    "en": "Coins • Rate",
    "ja": "コイン • レート",
    "cn": "硬币 • 率"
  },
  "Tiền Thưởng:": {
    "en": "Bonus:",
    "ja": "ボーナス:",
    "cn": "奖金："
  },
  "Tiền Thưởng": {
    "en": "Bonus",
    "ja": "ボーナス",
    "cn": "奖金"
  },
  "Trạng Thái:": {
    "en": "Status:",
    "ja": "ステータス:",
    "cn": "状态："
  },
  "Chủ sở hữu ID": {
    "en": "Owner ID",
    "ja": "オーナーID",
    "cn": "所有者 ID"
  },
  "Hệ số Bán (x)": {
    "en": "Sales Factor (x)",
    "ja": "売上係数 (x)",
    "cn": "销售系数 (x)"
  },
  "Tưới Toàn Bộ": {
    "en": "Complete Irrigation",
    "ja": "完全な灌漑",
    "cn": "完整的灌溉"
  },
  "Hồ Sơ Thợ Mỏ": {
    "en": "Miner Profile",
    "ja": "マイナープロフィール",
    "cn": "矿工简介"
  },
  "Console Lệnh": {
    "en": "Console Command",
    "ja": "コンソールコマンド",
    "cn": "控制台命令"
  },
  "Người Chơi (": {
    "en": "Player (",
    "ja": "プレイヤー (",
    "cn": "玩家（"
  },
  "Thưởng Xu VIP": {
    "en": "VIP Coin Reward",
    "ja": "VIPコイン報酬：",
    "cn": "VIP金币奖励"
  },
  "Lưu Vật Phẩm": {
    "en": "Save Items",
    "ja": "アイテムを保存",
    "cn": "保存项目"
  },
  "Loại Vật Phẩm": {
    "en": "Item Type",
    "ja": "アイテムの種類",
    "cn": "项目类型"
  },
  "Ngôn ngữ bot": {
    "en": "Bot language",
    "ja": "ボット言語",
    "cn": "机器人语言"
  },
  "Lưu cấu hình": {
    "en": "Save configuration",
    "ja": "設定を保存する",
    "cn": "保存配置"
  },
  "Cấm dùng bot": {
    "en": "It is forbidden to use bots",
    "ja": "ボットの使用は禁止されています",
    "cn": "禁止使用机器人"
  },
  "Tiêu Đề Embed": {
    "en": "Embed Title",
    "ja": "タイトルを埋め込む",
    "cn": "嵌入标题"
  },
  "Lưu Hôn Nhân": {
    "en": "Save Marriage",
    "ja": "結婚を救う",
    "cn": "挽救婚姻"
  },
  "Độ Bền Tối Đa": {
    "en": "Maximum Durability",
    "ja": "最大の耐久性",
    "cn": "最大耐用性"
  },
  "AI luận giải": {
    "en": "AI explains",
    "ja": "AIが説明します",
    "cn": "人工智能解读"
  },
  "Đổi avatar": {
    "en": "Change avatar",
    "ja": "アバターを変更する",
    "cn": "更改头像"
  },
  "Danh hiệu:": {
    "en": "Title:",
    "ja": "タイトル:",
    "cn": "标题："
  },
  "Danh hiệu": {
    "en": "Title",
    "ja": "タイトル",
    "cn": "标题"
  },
  "Đào Khoáng": {
    "en": "Mineral Peaches",
    "ja": "ミネラルピーチ",
    "cn": "桃矿物质"
  },
  "Dễ (Tập Sự)": {
    "en": "Easy (Novice)",
    "ja": "簡単 (初心者)",
    "cn": "简单（新手）"
  },
  "Chế độ chơi": {
    "en": "Game mode",
    "ja": "ゲームモード",
    "cn": "播放模式"
  },
  "• Trạng thái": {
    "en": "• Status",
    "ja": "• ステータス",
    "cn": "• 状态"
  },
  "Trừ bớt (-)": {
    "en": "Subtract (-)",
    "ja": "減算 (-)",
    "cn": "减（-）"
  },
  "BXH Cao Thủ": {
    "en": "Master Ranking",
    "ja": "マスターランキング",
    "cn": "大师排名"
  },
  "Thêm Cá Mới": {
    "en": "Add New Fish",
    "ja": "新しい魚を追加",
    "cn": "添加新鱼"
  },
  "Xóa Túi Rác": {
    "en": "Clear Trash Bag",
    "ja": "透明なゴミ袋",
    "cn": "透明垃圾袋"
  },
  "Loại cần câu": {
    "en": "Fishing rod type",
    "ja": "釣り竿の種類",
    "cn": "鱼竿类型"
  },
  "Hiếm (Rare)": {
    "en": "Rare (Rare)",
    "ja": "レア（レア）",
    "cn": "稀有"
  },
  "Yêu Cầu Mở:": {
    "en": "Open Request:",
    "ja": "オープンリクエスト:",
    "cn": "开放请求："
  },
  "Yêu Cầu Mở": {
    "en": "Open Request",
    "ja": "オープンリクエスト",
    "cn": "开放请求"
  },
  "Dọn Sạch Bể": {
    "en": "Clean the Tank",
    "ja": "タンクを掃除する",
    "cn": "清洁水箱"
  },
  "Lượt Thích": {
    "en": "Likes",
    "ja": "いいね！",
    "cn": "喜欢"
  },
  "+May mắn (%)": {
    "en": "+Luck (%)",
    "ja": "+運(%)",
    "cn": "+运气（%）"
  },
  "Buff Mồi (%)": {
    "en": "Bait Buff (%)",
    "ja": "餌バフ (%)",
    "cn": "诱饵增益 (%)"
  },
  "Reset Vườn": {
    "en": "Reset the Garden",
    "ja": "庭をリセットする",
    "cn": "重置花园"
  },
  "Khu Vực Mỏ": {
    "en": "Mine Area",
    "ja": "鉱山エリア",
    "cn": "矿区"
  },
  "Thưởng Coins": {
    "en": "Bonus Coins",
    "ja": "ボーナスコイン",
    "cn": "奖励金币"
  },
  "Tải Ảnh Lên": {
    "en": "Upload Photos",
    "ja": "写真をアップロードする",
    "cn": "上传照片"
  },
  "Khi vi phạm": {
    "en": "When violating",
    "ja": "違反した場合",
    "cn": "违规后"
  },
  "Tỉ lệ caps %": {
    "en": "Caps ratio %",
    "ja": "キャップ率 %",
    "cn": "资本化率%"
  },
  "bên cạnh tên": {
    "en": "next to the name",
    "ja": "名前の横にあります。",
    "cn": "名字旁边"
  },
  "hoặc :pepe:": {
    "en": "or :pepe:",
    "ja": "または :pepe:",
    "cn": "或：佩佩："
  },
  "hoặc :pepe": {
    "en": "or :pepe",
    "ja": "または :pepe",
    "cn": "或：佩佩"
  },
  "Hỗ trợ 24/7": {
    "en": "24/7 support",
    "ja": "年中無休のサポート",
    "cn": "24/7 支持"
  },
  "• Thời gian": {
    "en": "• Time",
    "ja": "• 時間",
    "cn": "• Time"
  },
  "BXH Cờ Vua": {
    "en": "Chess rankings",
    "ja": "チェスランキング",
    "cn": "国际象棋排名"
  },
  "Chủ phòng:": {
    "en": "Room owner:",
    "ja": "ルームオーナー:",
    "cn": "房主："
  },
  "Chủ phòng": {
    "en": "Room owner",
    "ja": "ルームオーナー",
    "cn": "房主"
  },
  "BXH Nối Từ": {
    "en": "Word Connection Chart",
    "ja": "単語の接続表",
    "cn": "字连接图"
  },
  "Chờ (Idle)": {
    "en": "Wait (Idle)",
    "ja": "待機 (アイドル)",
    "cn": "空闲"
  },
  "Ngân Hàng:": {
    "en": "Bank:",
    "ja": "銀行:",
    "cn": "银行："
  },
  "Ngân Hàng": {
    "en": "Bank",
    "ja": "銀行",
    "cn": "银行"
  },
  "Ngẫu Nhiên": {
    "en": "Random",
    "ja": "ランダム",
    "cn": "随机"
  },
  "Xu thưởng:": {
    "en": "Bonus Coins:",
    "ja": "ボーナスコイン:",
    "cn": "奖励金币："
  },
  "Xu thưởng": {
    "en": "Bonus Coins",
    "ja": "ボーナスコイン",
    "cn": "奖励金币"
  },
  "Mồi Câu Cá": {
    "en": "Fishing Lure",
    "ja": "釣りルアー",
    "cn": "鱼饵"
  },
  "Làm Mới DS": {
    "en": "Refresh DS",
    "ja": "DSをリフレッシュ",
    "cn": "刷新DS"
  },
  "Coin Tối Đa": {
    "en": "Maximum Coins",
    "ja": "最大コイン数",
    "cn": "最多金币"
  },
  "Phí gia hạn": {
    "en": "Renewal fee",
    "ja": "更新料",
    "cn": "续订费"
  },
  "Hạt giống:": {
    "en": "Seeds:",
    "ja": "種子:",
    "cn": "种子："
  },
  "Hạt giống": {
    "en": "Seeds",
    "ja": "種子",
    "cn": "种子"
  },
  "• Phiên bản": {
    "en": "• Version",
    "ja": "• バージョン",
    "cn": "• 版本"
  },
  "Chọn Server": {
    "en": "Select Server",
    "ja": "サーバーを選択します",
    "cn": "选择服务器"
  },
  "Xem Tỉ Lệ": {
    "en": "See Rate",
    "ja": "料金を見る",
    "cn": "查看规模"
  },
  "Cấm global": {
    "en": "Ban globally",
    "ja": "世界的に禁止する",
    "cn": "全球禁止"
  },
  "Xanh dương": {
    "en": "Blue",
    "ja": "ブルー",
    "cn": "蓝色"
  },
  "Mô Tả Embed": {
    "en": "Embed Description",
    "ja": "埋め込み説明",
    "cn": "嵌入说明"
  },
  "Đơn vị tiền": {
    "en": "Currency unit",
    "ja": "通貨単位",
    "cn": "货币单位"
  },
  "Tên Cần Câu": {
    "en": "Fishing Rod Name",
    "ja": "釣り竿名",
    "cn": "鱼竿名称"
  },
  "Câu Cá RPG": {
    "en": "Fishing RPG",
    "ja": "釣りRPG",
    "cn": "钓鱼角色扮演游戏"
  },
  "Cần giúp đỡ": {
    "en": "Need help",
    "ja": "助けが必要ですか",
    "cn": "需要帮助"
  },
  "Toàn Quyền": {
    "en": "Full Authority",
    "ja": "全権限",
    "cn": "总督"
  },
  "Của Mình (": {
    "en": "Mine (",
    "ja": "わたしの（",
    "cn": "我的（"
  },
  "Dòng/trang": {
    "en": "Line/page",
    "ja": "行/ページ",
    "cn": "行/页"
  },
  "Vs AI Máy": {
    "en": "Vs AI Machine",
    "ja": "vs AIマシン",
    "cn": "VS 人工智能机器"
  },
  "Bách Khoa": {
    "en": "Bach Khoa",
    "ja": "バックコア",
    "cn": "巴赫科阿"
  },
  "Tạo Rương": {
    "en": "Create a Chest",
    "ja": "チェストを作成する",
    "cn": "创建一个箱子"
  },
  "Linh vật:": {
    "en": "Mascot:",
    "ja": "マスコット:",
    "cn": "吉祥物："
  },
  "Linh vật": {
    "en": "Mascot",
    "ja": "マスコット",
    "cn": "吉祥物"
  },
  "Rương Báu": {
    "en": "Treasure Chest",
    "ja": "宝箱",
    "cn": "宝箱"
  },
  "• Sức chứa": {
    "en": "• Capacity",
    "ja": "• 容量",
    "cn": "• 容量"
  },
  "Hạt Giống": {
    "en": "Seeds",
    "ja": "種子",
    "cn": "种子"
  },
  "Túi đồ ẩn": {
    "en": "Hidden storage pockets",
    "ja": "隠し収納ポケット",
    "cn": "隐藏的库存口袋"
  },
  "Đột biến:": {
    "en": "Mutation:",
    "ja": "突然変異:",
    "cn": "突变："
  },
  "Đột biến": {
    "en": "Mutation",
    "ja": "突然変異",
    "cn": "突变"
  },
  "Đổi Ô Đất": {
    "en": "Change Land Plot",
    "ja": "土地区画を変更する",
    "cn": "改变地块"
  },
  "Cuốc Đào": {
    "en": "Cuoc Dao",
    "ja": "クオック・ダオ",
    "cn": "措克岛"
  },
  "Đổi Coins": {
    "en": "Exchange Coins",
    "ja": "コインを交換する",
    "cn": "兑换硬币"
  },
  "Lệnh nhanh": {
    "en": "Quick command",
    "ja": "クイックコマンド",
    "cn": "快速命令"
  },
  "Đã setup:": {
    "en": "Already set up:",
    "ja": "すでにセットアップされています:",
    "cn": "已经设置："
  },
  "Đã setup": {
    "en": "Already set up",
    "ja": "すでにセットアップされています",
    "cn": "设置"
  },
  "Key có sẵn": {
    "en": "Available keys",
    "ja": "利用可能なキー",
    "cn": "钥匙可用"
  },
  "Lưu Level": {
    "en": "Save Level",
    "ja": "レベルを保存",
    "cn": "保存等级"
  },
  "Thêm kênh": {
    "en": "Add channels",
    "ja": "チャンネルを追加する",
    "cn": "添加频道"
  },
  "đã trỏ tới": {
    "en": "pointed to",
    "ja": "指摘したのは：",
    "cn": "指向"
  },
  "Cuộn cuối": {
    "en": "Final roll",
    "ja": "最終ロール",
    "cn": "最后一卷"
  },
  "Tải ngay": {
    "en": "Download now",
    "ja": "今すぐダウンロード",
    "cn": "立即下载"
  },
  "để chia sẻ": {
    "en": "to share",
    "ja": "共有するために。",
    "cn": "分享"
  },
  "Ví Coins": {
    "en": "Coins Wallet",
    "ja": "コインウォレット",
    "cn": "硬币钱包"
  },
  "Tổng cộng": {
    "en": "Total",
    "ja": "合計",
    "cn": "合计"
  },
  "Chưa nạp": {
    "en": "Not loaded yet",
    "ja": "まだロードされていません",
    "cn": "尚未加载"
  },
  "Lượt đánh": {
    "en": "Hits",
    "ja": "ヒット数",
    "cn": "命中"
  },
  "Nạp Cogs": {
    "en": "Recharge Cogs",
    "ja": "リチャージコグ",
    "cn": "负载齿轮"
  },
  "Kiểm tra": {
    "en": "Check",
    "ja": "チェック",
    "cn": "检查"
  },
  "Giải Trí": {
    "en": "Entertainment",
    "ja": "エンターテイメント",
    "cn": "娱乐"
  },
  "Toàn Cục": {
    "en": "Whole Department",
    "ja": "部門全体",
    "cn": "全系"
  },
  "Giá Coins": {
    "en": "Coins Price",
    "ja": "コイン価格",
    "cn": "价格硬币"
  },
  "Mở tự do": {
    "en": "Open freely",
    "ja": "自由にオープン",
    "cn": "自由开放"
  },
  "Linh Vật": {
    "en": "Mascot",
    "ja": "マスコット",
    "cn": "吉祥物"
  },
  "Loại tiền": {
    "en": "Currency",
    "ja": "通貨",
    "cn": "货币类型"
  },
  "Hoa màu:": {
    "en": "Flower color:",
    "ja": "花の色:",
    "cn": "花色："
  },
  "Hoa màu": {
    "en": "Flower color",
    "ja": "花の色",
    "cn": "彩色花朵"
  },
  "Bụi sao:": {
    "en": "Stardust:",
    "ja": "スターダスト:",
    "cn": "星尘："
  },
  "Bụi sao": {
    "en": "Stardust",
    "ja": "スターダスト",
    "cn": "星尘"
  },
  "Mầm Bệnh": {
    "en": "Pathogens",
    "ja": "病原体",
    "cn": "病原体"
  },
  "Tuần này": {
    "en": "This week",
    "ja": "今週",
    "cn": "本周"
  },
  "Trợ Giúp": {
    "en": "Help",
    "ja": "ヘルプ",
    "cn": "帮助"
  },
  "Lệnh Mod": {
    "en": "Mod command",
    "ja": "Modコマンド",
    "cn": "修改命令"
  },
  "Thực thi": {
    "en": "Execution",
    "ja": "実行",
    "cn": "执行"
  },
  "Để biết": {
    "en": "To know",
    "ja": "知ること",
    "cn": "要知道"
  },
  "Top Giàu": {
    "en": "Top Rich",
    "ja": "トップリッチ",
    "cn": "顶级富豪"
  },
  "Thêm mốc": {
    "en": "Add landmarks",
    "ja": "ランドマークを追加する",
    "cn": "添加地标"
  },
  "Gửi ngay": {
    "en": "Send now",
    "ja": "今すぐ送信",
    "cn": "立即发送"
  },
  "Màu Embed": {
    "en": "Embed Color",
    "ja": "埋め込み色",
    "cn": "嵌入颜色"
  },
  "Tiêu đề": {
    "en": "Title",
    "ja": "タイトル",
    "cn": "标题"
  },
  "Mã nguồn": {
    "en": "Source code",
    "ja": "ソースコード",
    "cn": "源代码"
  },
  "Chỉ Xem": {
    "en": "Just Watch",
    "ja": "見てください",
    "cn": "仅供查看"
  },
  "Tất Cả (": {
    "en": "All (",
    "ja": "全員（",
    "cn": "所有（"
  },
  "Nạp lại": {
    "en": "Recharge",
    "ja": "リチャージ",
    "cn": "重新加载"
  },
  "Giải mã": {
    "en": "Decoding",
    "ja": "デコード",
    "cn": "解码"
  },
  "Mời Bạn": {
    "en": "We invite you",
    "ja": "あなたを招待します",
    "cn": "邀请您"
  },
  "Cốt Lõi": {
    "en": "Core",
    "ja": "コア",
    "cn": "核心"
  },
  "Kinh Tế": {
    "en": "Economy",
    "ja": "経済",
    "cn": "经济学"
  },
  "Bảo Mật": {
    "en": "Security",
    "ja": "セキュリティ",
    "cn": "安全性"
  },
  "Số Lượng": {
    "en": "Quantity",
    "ja": "数量",
    "cn": "数量"
  },
  "Giỏ cá:": {
    "en": "Fish basket:",
    "ja": "魚かご:",
    "cn": "鱼篮："
  },
  "Giỏ cá": {
    "en": "Fish basket",
    "ja": "魚かご",
    "cn": "鱼篮"
  },
  "Số lượng": {
    "en": "Quantity",
    "ja": "数量",
    "cn": "数量"
  },
  "Cần Câu": {
    "en": "Fishing rod",
    "ja": "釣り竿",
    "cn": "钓鱼竿"
  },
  "Mồi Câu": {
    "en": "Fishing Bait",
    "ja": "釣り餌",
    "cn": "鱼饵"
  },
  "Level mở": {
    "en": "Open Level",
    "ja": "オープンレベル",
    "cn": "开放级别"
  },
  "Sâu bọ:": {
    "en": "Pests:",
    "ja": "害虫:",
    "cn": "害虫："
  },
  "Sâu bọ": {
    "en": "Pests",
    "ja": "害虫",
    "cn": "昆虫"
  },
  "Hiệu ứng": {
    "en": "Effects",
    "ja": "効果",
    "cn": "效果"
  },
  "Hoa Màu": {
    "en": "Colored Flowers",
    "ja": "色とりどりの花",
    "cn": "彩色花朵"
  },
  "Xanh lá": {
    "en": "Green",
    "ja": "緑",
    "cn": "绿色"
  },
  "Nạp Lại": {
    "en": "Reload",
    "ja": "リロード",
    "cn": "重新加载"
  },
  "Liên kết": {
    "en": "Link",
    "ja": "リンク",
    "cn": "链接"
  },
  "Rút bài": {
    "en": "Draw cards",
    "ja": "カードを引く",
    "cn": "抽卡"
  },
  "Hỗ trợ:": {
    "en": "Support:",
    "ja": "サポート:",
    "cn": "支持："
  },
  "Câu Cá": {
    "en": "Fishing",
    "ja": "釣り",
    "cn": "钓鱼"
  },
  "Mã hóa": {
    "en": "Encryption",
    "ja": "暗号化",
    "cn": "加密"
  },
  "Phòng:": {
    "en": "Room:",
    "ja": "部屋:",
    "cn": "房间："
  },
  "Phòng": {
    "en": "Room",
    "ja": "部屋",
    "cn": "房间"
  },
  "Đổ màu": {
    "en": "Color filling",
    "ja": "色の塗りつぶし",
    "cn": "倒颜色"
  },
  "Kết nối": {
    "en": "Connection",
    "ja": "接続",
    "cn": "连接"
  },
  "Loài cá": {
    "en": "Fish species",
    "ja": "魚種",
    "cn": "鱼种"
  },
  "THƯỜNG": {
    "en": "NORMAL",
    "ja": "ノーマル",
    "cn": "正常"
  },
  "Giá bán": {
    "en": "Price",
    "ja": "価格",
    "cn": "售价"
  },
  "May mắn": {
    "en": "Luck",
    "ja": "運",
    "cn": "幸运儿"
  },
  "Ô đất:": {
    "en": "Land plot:",
    "ja": "土地区画:",
    "cn": "土地面积："
  },
  "Ô đất": {
    "en": "Land plot",
    "ja": "土地区画",
    "cn": "噢土地"
  },
  "Sâu Bọ": {
    "en": "Insects",
    "ja": "昆虫",
    "cn": "虫子"
  },
  "Từ cấm": {
    "en": "Forbidden words",
    "ja": "禁止用語",
    "cn": "禁用词"
  },
  "Cặp Đôi": {
    "en": "Couple",
    "ja": "カップル",
    "cn": "情侣"
  },
  "Máy chủ": {
    "en": "Server",
    "ja": "サーバー",
    "cn": "服务器"
  },
  "Thoát": {
    "en": "Exit",
    "ja": "終了",
    "cn": "退出"
  },
  "Bút": {
    "en": "Pen",
    "ja": "ペン",
    "cn": "笔"
  },
  "Gợi ý": {
    "en": "Suggestion",
    "ja": "提案",
    "cn": "建议"
  },
  "Bảng": {
    "en": "Table",
    "ja": "表",
    "cn": "表"
  },
  "Mời": {
    "en": "Please",
    "ja": "お願いします",
    "cn": "请"
  },
  "Tẩy": {
    "en": "Eraser",
    "ja": "消しゴム",
    "cn": "橡皮擦"
  },
  "Tổng": {
    "en": "Total",
    "ja": "合計",
    "cn": "合计"
  },
  "Xám": {
    "en": "Gray",
    "ja": "グレー",
    "cn": "灰色"
  },
  "Hòa": {
    "en": "Draw",
    "ja": "描画",
    "cn": "抽奖"
  },
  "Đỏ": {
    "en": "Red",
    "ja": "レッド",
    "cn": "红色"
  },
  "Bạn có chắc chắn không?": {
    "en": "Are you sure?",
    "ja": "本当によろしいですか？",
    "cn": "你确定吗？"
  },
  "Bạn có chắc chắn không": {
    "en": "Are you sure",
    "ja": "本当によろしいですか",
    "cn": "你确定吗？"
  },
  "Bạn có chắc chắn muốn xóa không?": {
    "en": "Are you sure you want to delete?",
    "ja": "本当に削除しますか？",
    "cn": "您确定要删除吗？"
  },
  "Bạn có chắc chắn muốn xóa không": {
    "en": "Are you sure you want to delete",
    "ja": "本当に削除しますか",
    "cn": "您确定要删除吗？"
  },
  "Bạn có chắc chắn muốn thực hiện không?": {
    "en": "Are you sure you want to proceed?",
    "ja": "本当に実行しますか？",
    "cn": "您确定要这样做吗？"
  },
  "Bạn có chắc chắn muốn rời khỏi server này không?": {
    "en": "Are you sure you want to leave this server?",
    "ja": "このサーバーから退出してもよろしいですか？",
    "cn": "您确定要离开该服务器吗？"
  },
  "Thao tác này không thể hoàn tác": {
    "en": "This action cannot be undone",
    "ja": "この操作は取り消せません",
    "cn": "此操作无法撤消"
  },
  "Thao tác này không thể hoàn tác!": {
    "en": "This action cannot be undone!",
    "ja": "この操作は取り消せません！",
    "cn": "此操作无法撤消！"
  },
  "Xác nhận xóa": {
    "en": "Confirm deletion",
    "ja": "削除を確認",
    "cn": "确认删除"
  },
  "Xác nhận thực hiện": {
    "en": "Confirm action",
    "ja": "操作を確認",
    "cn": "确认实施"
  },
  "Đã sao chép vào bộ nhớ tạm": {
    "en": "Copied to clipboard",
    "ja": "クリップボードにコピーしました",
    "cn": "已复制到剪贴板"
  },
  "Đã sao chép vào bộ nhớ tạm!": {
    "en": "Copied to clipboard!",
    "ja": "クリップボードにコピーしました！",
    "cn": "已复制到剪贴板！"
  },
  "Sao chép thành công": {
    "en": "Copied successfully",
    "ja": "コピーに成功しました",
    "cn": "复制成功"
  },
  "Sao chép liên kết": {
    "en": "Copy link",
    "ja": "リンクをコピー",
    "cn": "复制链接"
  },
  "Lỗi kết nối máy chủ": {
    "en": "Server connection error",
    "ja": "サーバー接続エラー",
    "cn": "服务器连接错误"
  },
  "Không tìm thấy dữ liệu": {
    "en": "No data found",
    "ja": "データが見つかりません",
    "cn": "没有找到数据"
  },
  "Vui lòng nhập đầy đủ thông tin": {
    "en": "Please fill in all fields",
    "ja": "すべての項目を入力してください",
    "cn": "请输入完整信息"
  },
  "Cập nhật thành công!": {
    "en": "Updated successfully!",
    "ja": "正常に更新されました！",
    "cn": "更新成功！"
  },
  "Cập nhật thành công": {
    "en": "Updated successfully",
    "ja": "正常に更新されました",
    "cn": "更新成功"
  },
  "Lưu thành công!": {
    "en": "Saved successfully!",
    "ja": "正常に保存されました！",
    "cn": "保存成功！"
  },
  "Lưu thành công": {
    "en": "Saved successfully",
    "ja": "正常に保存されました",
    "cn": "保存成功"
  },
  "Lỗi khi lưu dữ liệu": {
    "en": "Error saving data",
    "ja": "データの保存中にエラーが発生しました",
    "cn": "保存数据时出错"
  },
  "Đang xử lý...": {
    "en": "Processing...",
    "ja": "処理中...",
    "cn": "处理中..."
  },
  "Đang xử lý": {
    "en": "Processing",
    "ja": "処理中",
    "cn": "加工"
  },
  "Đã lưu thay đổi": {
    "en": "Changes saved",
    "ja": "変更を保存しました",
    "cn": "更改已保存"
  },
  "Đã xảy ra lỗi, vui lòng thử lại sau!": {
    "en": "An error occurred, please try again later!",
    "ja": "エラーが発生しました。後でもう一度お試しください！",
    "cn": "发生错误，请稍后重试！"
  },
  "Không có quyền truy cập": {
    "en": "Access denied",
    "ja": "アクセスが拒否されました",
    "cn": "无法访问"
  },
  "Bạn không có quyền thực hiện thao tác này": {
    "en": "You do not have permission to perform this action",
    "ja": "この操作を実行する権限がありません",
    "cn": "您没有执行此操作的权限"
  },
  "Phiên hết hạn, chuyển về đăng nhập...": {
    "en": "Session expired, redirecting to login...",
    "ja": "セッションが期限切れです。ログインにリダイレクトしています...",
    "cn": "会话已过期，请切换回登录..."
  },
  "Đã làm mới dữ liệu chẩn đoán hệ thống!": {
    "en": "System diagnostics data refreshed!",
    "ja": "システム診断データが更新されました！",
    "cn": "系统诊断数据刷新！"
  },
  "Không thể làm mới chẩn đoán": {
    "en": "Failed to refresh diagnostics",
    "ja": "診断を更新できませんでした",
    "cn": "无法刷新诊断"
  },
  "Lỗi kết nối kiểm tra hệ thống": {
    "en": "System check connection error",
    "ja": "システムチェック接続エラー",
    "cn": "系统检查连接错误"
  },
  "Lỗi khi yêu cầu bot rời server": {
    "en": "Error requesting bot to leave server",
    "ja": "ボットのサーバー退出リクエスト中にエラーが発生しました",
    "cn": "要求机器人离开服务器时出错"
  },
  "Không thể tạo lời mời": {
    "en": "Could not create invite",
    "ja": "招待を作成できませんでした",
    "cn": "无法创建邀请"
  },
  "Nhập nội dung tìm kiếm...": {
    "en": "Enter search content...",
    "ja": "検索内容を入力...",
    "cn": "输入搜索内容..."
  },
  "Bạn có chắc chắn muốn thực hiện không": {
    "en": "Are you sure you want to proceed",
    "ja": "本当に実行しますか？",
    "cn": "您确定要这样做吗？"
  },
  "Bạn có chắc chắn muốn rời khỏi server này không": {
    "en": "Are you sure you want to leave this server",
    "ja": "このサーバーから退出してもよろしいですか？",
    "cn": "您确定要离开该服务器吗？"
  },
  "Đã xảy ra lỗi, vui lòng thử lại sau": {
    "en": "An error occurred, please try again later",
    "ja": "エラーが発生しました。後でもう一度お試しください！",
    "cn": "发生错误，请稍后重试"
  },
  "Phiên hết hạn, chuyển về đăng nhập": {
    "en": "Session expired, redirecting to login",
    "ja": "セッションが期限切れです。ログインにリダイレクトしています",
    "cn": "会话已过期，切换回登录"
  },
  "Đã làm mới dữ liệu chẩn đoán hệ thống": {
    "en": "System diagnostics data refreshed",
    "ja": "システム診断データが更新されました！",
    "cn": "刷新的系统诊断数据"
  },
  "Nhập nội dung tìm kiếm": {
    "en": "Enter search content",
    "ja": "検索内容を入力",
    "cn": "输入搜索内容"
  },
  "(mọi server — chỉ admin). Bị cấm sẽ không thực hiện được lệnh (trừ ).": {
    "en": "(all servers — admin only). If banned, orders cannot be executed (except ).",
    "ja": "(すべてのサーバー - 管理者のみ)。禁止された場合、注文は実行できません（を除く）。",
    "cn": "（所有服务器 - 仅限管理员）。如果被禁止，订单将无法执行（除）。"
  },
  ". Hệ thống tự động lọc chỉ hiện server bạn có quyền . User thường chỉ thấy server của mình, admin thấy toàn bộ.": {
    "en": ". The system automatically filters only the server you have permission to show. Users usually only see their server, admins see everything.",
    "ja": "。システムは、表示権限のあるサーバーのみを自動的にフィルタリングします。通常、ユーザーには自分のサーバーのみが表示され、管理者にはすべてが表示されます。",
    "cn": "。系统会自动过滤仅您有权显示的服务器。用户通常只能看到他们的服务器，管理员可以看到一切。"
  },
  ": biểu thức chính quy → ,": {
    "en": ": regular expression → ,",
    "ja": ": 正規表現 → 、",
    "cn": ": 正则表达式 → ,"
  },
  ": tin nhắn chứa chuỗi → chặn. VD: chặn \"con linh béo ú\"": {
    "en": ": message contains string → block. For example: block the \"fat spirit\"",
    "ja": ": メッセージには文字列→ブロックが含まれています。例: 「脂肪の霊」をブロックします。",
    "cn": "：消息包含字符串→块。例如：挡住“胖灵”"
  },
  "Biệt danh mới (VD: )": {
    "en": "New nickname (Example: )",
    "ja": "新しいニックネーム (例: )",
    "cn": "新昵称（例如： ）"
  },
  "Bạn có thể gõ trong kênh chat Discord hoặc truy cập mục": {
    "en": "You can type in the Discord chat channel or visit the section",
    "ja": "Discord チャット チャネルに入力するか、セクションにアクセスできます。",
    "cn": "您可以在 Discord 聊天频道中输入内容或访问该部分"
  },
  "Chủ sở hữu ID: • Sức chứa:": {
    "en": "Owner ID: • Capacity:",
    "ja": "所有者 ID: • 容量:",
    "cn": "所有者 ID： • 容量："
  },
  "Cài đặt plugin vào server Minecraft.": {
    "en": "Install the plugin to the Minecraft server.",
    "ja": "プラグインを Minecraft サーバーにインストールします。",
    "cn": "将插件安装到 Minecraft 服务器。"
  },
  "Dùng lệnh trong game để kết nối": {
    "en": "Use in-game commands to connect",
    "ja": "ゲーム内コマンドを使用して接続します",
    "cn": "使用游戏内命令进行连接"
  },
  "Dùng lệnh trên Discord để kết duyên": {
    "en": "Use commands on Discord to make love",
    "ja": "Discord のコマンドを使用してセックスする",
    "cn": "使用 Discord 上的命令做爱"
  },
  "Dùng prefix hoặc Discord Slash Commands": {
    "en": "Use prefix or Discord Slash Commands",
    "ja": "プレフィックスまたは Discord スラッシュ コマンドを使用する",
    "cn": "使用前缀或 Discord 斜杠命令"
  },
  "Hệ thống kỹ năng nội tại , ngồi nghỉ ngơi , sách phù phép và custom items độc quyền.": {
    "en": "Internal skill system, resting, spell book and exclusive custom items.",
    "ja": "内部スキルシステム、休息、魔法の本、そして専用のカスタムアイテム。",
    "cn": "内部技能系统、休息、法术书和专属定制物品。"
  },
  "Key hỗ trợ: {user} = tên thành viên, {server} = tên server, {user_name} = tên hiển thị": {
    "en": "Support key: {user} = member name, {server} = server name, {user_name} = display name",
    "ja": "サポートキー: {user} = メンバー名、{server} = サーバー名、{user_name} = 表示名",
    "cn": "支持键：{user} = 成员名称，{server} = 服务器名称，{user_name} = 显示名称"
  },
  "Không cần (hoặc nhập )": {
    "en": "No need (or import)",
    "ja": "必要ありません（またはインポート）",
    "cn": "不需要（或导入）"
  },
  "Kiểm tra file đã trỏ tới:": {
    "en": "Check the file pointed to:",
    "ja": "指定されているファイルを確認します。",
    "cn": "检查指向的文件："
  },
  "Liên kết tài khoản in-game với Discord SakuraBot qua lệnh , chuyển đổi coins hai chiều tức thì.": {
    "en": "Link in-game account with Discord SakuraBot via command, instant two-way coin conversion.",
    "ja": "コマンドを介してゲーム内アカウントを Discord のサクラボットにリンクし、即時に双方向のコイン変換を行います。",
    "cn": "通过命令将游戏内帐户与 Discord SakuraBot 链接，即时双向硬币转换。"
  },
  "Nhập mã kết nối tạo từ lệnh trong game Minecraft hoặc chọn trực tiếp server phát hiện bên dưới.": {
    "en": "Enter the connection code created from the command in the Minecraft game or directly select the detected server below.",
    "ja": "Minecraft ゲーム内のコマンドから作成した接続コードを入力するか、以下で検出されたサーバーを直接選択します。",
    "cn": "输入通过 Minecraft 游戏中的命令创建的连接代码或直接选择下面检测到的服务器。"
  },
  "Nạn nhân bị đông cứng không thể trong 10 phút. Bị chặn bởi Khiên hoặc Gương phản đòn!": {
    "en": "The victim is frozen solid for 10 minutes. Blocked by Shield or Counterattack Mirror!",
    "ja": "犠牲者は10分間凍りつく。シールドまたは反撃ミラーでブロックされる!",
    "cn": "受害者被冻僵了 10 分钟。被盾牌或反击镜格挡！"
  },
  "Prefix: hoặc": {
    "en": "Prefix: or",
    "ja": "プレフィックス: または",
    "cn": "前缀：或"
  },
  "Số lần câu bị nguyền (VD: )": {
    "en": "Number of times the sentence was cursed (Example: )",
    "ja": "文が呪われた回数（例： ）",
    "cn": "句子被咒骂的次数（例如： ）"
  },
  "Số phút hiệu lực (VD: )": {
    "en": "Number of minutes of validity (eg: )",
    "ja": "有効期限の分数 (例: )",
    "cn": "有效分钟数（例如： ）"
  },
  "Số phút mute (VD: )": {
    "en": "Number of mute minutes (eg: )",
    "ja": "ミュートの分数 (例: )",
    "cn": "静音分钟数（例如： ）"
  },
  "Số phút đóng băng (VD: )": {
    "en": "Number of freezing minutes (eg: )",
    "ja": "フリーズする分数 (例: )",
    "cn": "冻结分钟数（例如： ）"
  },
  "Số tiền hoặc % (VD: hoặc )": {
    "en": "Amount or % (eg: or )",
    "ja": "量または% (例: または )",
    "cn": "金额或%（例如： 或 ）"
  },
  "Thiệt hại coin (VD: )": {
    "en": "Coin damage (Example: )",
    "ja": "コインダメージ（例： ）",
    "cn": "硬币损坏（示例： ）"
  },
  "Thành viên quản lý kênh riêng bằng lệnh .. hoặc panel nút. Bot cần quyền": {
    "en": "Members manage private channels using commands .. or button panel. Bots need permissions",
    "ja": "メンバーはコマンド .. またはボタン パネルを使用してプライベート チャネルを管理します。ボットには権限が必要です",
    "cn": "成员使用命令或按钮面板管理私人频道。机器人需要权限"
  },
  "Thời hạn hiệu lực (VD: phút)": {
    "en": "Validity period (eg: minutes)",
    "ja": "有効期間（例：分）",
    "cn": "有效期（例如：分钟）"
  },
  "Tip: Bạn cũng có thể mở trực tiếp để chia sẻ.": {
    "en": "Tip: You can also open it directly to share.",
    "ja": "ヒント: 直接開いて共有することもできます。",
    "cn": "提示：您也可以直接打开分享。"
  },
  "Trong game, dùng lệnh để lấy mã liên kết 6 ký tự.": {
    "en": "In the game, use the command to get the 6-character link code.",
    "ja": "ゲーム内でコマンドを使用して 6 文字のリンク コードを取得します。",
    "cn": "游戏中使用指令获取6个字符的链接码。"
  },
  "Tùy chọn độ mạnh (VD: )": {
    "en": "Strength options (eg: )",
    "ja": "強度オプション (例: )",
    "cn": "强度选项（例如： ）"
  },
  "Web panel tích hợp trong bot (). Theo dõi trạng thái kết nối Discord.": {
    "en": "Web panel integrated in bot(). Monitor Discord connection status.",
    "ja": "bot() に統合された Web パネル。 Discordの接続ステータスを監視します。",
    "cn": "Web 面板集成在 bot() 中。监控 Discord 连接状态。"
  },
  "Đầy đủ các lệnh tiền tố và Slash commands được đồng bộ trực tiếp từ hệ thống.": {
    "en": "All prefix commands and Slash commands are synchronized directly from the system.",
    "ja": "すべてのプレフィックス コマンドとスラッシュ コマンドはシステムから直接同期されます。",
    "cn": "所有前缀命令和斜线命令均直接从系统同步。"
  },
  "• = mention thành viên": {
    "en": "• = mention member",
    "ja": "• = メンバーに言及する",
    "cn": "• = 提及会员"
  },
  "• = tag người boost": {
    "en": "• = tag the person who boosts",
    "ja": "• = ブーストする人にタグを付ける",
    "cn": "• = 标记提升的人"
  },
  "• = tên hiển thị của thành viên": {
    "en": "• = member's display name",
    "ja": "• = メンバーの表示名",
    "cn": "• = 成员的显示名称"
  },
  "• = tên server": {
    "en": "• = server name",
    "ja": "• = サーバー名",
    "cn": "• = 服务器名称"
  },
  "• = tên server trong thông báo boost": {
    "en": "• = server name in boost message",
    "ja": "• = ブースト メッセージ内のサーバー名",
    "cn": "• = boost 消息中的服务器名称"
  },
  "• Gõ hoặc để bot tham gia voice và đọc tin nhắn.": {
    "en": "• Type or let the bot join the voice and read the message.",
    "ja": "• メッセージを入力するか、ボットに音声に参加させてメッセージを読み上げます。",
    "cn": "• 输入或让机器人加入语音并阅读消息。"
  },
  "• 🤖 Có thể dùng lệnh Discord trực tiếp từ bot.": {
    "en": "• 🤖 Can use Discord commands directly from the bot.",
    "ja": "• 🤖 ボットから直接 Discord コマンドを使用できます。",
    "cn": "• 🤖 可以直接从机器人使用Discord 命令。"
  },
  "🌸 Sakura Bot • Prefix: hoặc": {
    "en": "🌸 Sakura Bot • Prefix: or",
    "ja": "🌸さくらボット • プレフィックス: または",
    "cn": "?? Sakura Bot • 前缀：或"
  },
  "💡 Bị cấm sẽ không dùng được lệnh bot (trừ để khiếu nại). Gỡ cấm bằng nút": {
    "en": "💡 If you are banned, you will not be able to use bot commands (except for complaints). Unblock with button",
    "ja": "💡 BANされた場合、ボットコマンドは使用できなくなります（苦情を除く）。ボタンでブロックを解除",
    "cn": "💡 如果您被禁止，您将无法使用机器人命令（投诉除外）。使用按钮解锁"
  },
  "(mọi server — chỉ admin). Bị cấm sẽ không thực hiện được lệnh (trừ )": {
    "en": "(all servers — admin only). If banned, orders cannot be executed (except )",
    "ja": "(すべてのサーバー - 管理者のみ)。禁止された場合、注文は実行できません（を除く）。",
    "cn": "（所有服务器 - 仅限管理员）。如果您被封禁，您将无法执行订单（除非）"
  },
  ". Hệ thống tự động lọc chỉ hiện server bạn có quyền . User thường chỉ thấy server của mình, admin thấy toàn bộ": {
    "en": ". The system automatically filters only the server you have permission to show. Users usually only see their server, admins see everything",
    "ja": "。システムは、表示権限のあるサーバーのみを自動的にフィルタリングします。通常、ユーザーには自分のサーバーのみが表示され、管理者にはすべてが表示されます。",
    "cn": "。系统会自动过滤仅您有权显示的服务器。用户通常只能看到他们的服务器，管理员可以看到一切"
  },
  "Chủ sở hữu ID: • Sức chứa": {
    "en": "Owner ID: • Capacity",
    "ja": "所有者 ID: • 容量",
    "cn": "所有者 ID： • 容量"
  },
  "Cài đặt plugin vào server Minecraft": {
    "en": "Install the plugin to the Minecraft server",
    "ja": "プラグインを Minecraft サーバーにインストールします。",
    "cn": "将插件安装到 Minecraft 服务器"
  },
  "Hệ thống kỹ năng nội tại , ngồi nghỉ ngơi , sách phù phép và custom items độc quyền": {
    "en": "Internal skill system, resting, spell book and exclusive custom items",
    "ja": "内部スキルシステム、休息、魔法の本、そして専用のカスタムアイテム。",
    "cn": "内部技能系统、休息、法术书和专属定制物品"
  },
  "Kiểm tra file đã trỏ tới": {
    "en": "Check the file pointed to",
    "ja": "指定されているファイルを確認します。",
    "cn": "检查指向的文件"
  },
  "Liên kết tài khoản in-game với Discord SakuraBot qua lệnh , chuyển đổi coins hai chiều tức thì": {
    "en": "Link in-game account with Discord SakuraBot via command, instant two-way coin conversion",
    "ja": "コマンドを介してゲーム内アカウントを Discord のサクラボットにリンクし、即時に双方向のコイン変換を行います。",
    "cn": "通过命令将游戏内帐户与Discord SakuraBot链接，即时双向硬币转换"
  },
  "Nhập mã kết nối tạo từ lệnh trong game Minecraft hoặc chọn trực tiếp server phát hiện bên dưới": {
    "en": "Enter the connection code created from the command in the Minecraft game or directly select the detected server below",
    "ja": "Minecraft ゲーム内のコマンドから作成した接続コードを入力するか、以下で検出されたサーバーを直接選択します。",
    "cn": "输入在 Minecraft 游戏中通过命令创建的连接代码或直接选择下面检测到的服务器"
  },
  "Nạn nhân bị đông cứng không thể trong 10 phút. Bị chặn bởi Khiên hoặc Gương phản đòn": {
    "en": "The victim is frozen solid for 10 minutes. Blocked by Shield or Counterattack Mirror",
    "ja": "犠牲者は10分間凍りつく。シールドまたは反撃ミラーでブロックされる",
    "cn": "受害者被冻僵了 10 分钟。被盾牌或反射镜阻挡"
  },
  "Tip: Bạn cũng có thể mở trực tiếp để chia sẻ": {
    "en": "Tip: You can also open it directly to share",
    "ja": "ヒント: 直接開いて共有することもできます。",
    "cn": "提示：也可以直接打开分享"
  },
  "Trong game, dùng lệnh để lấy mã liên kết 6 ký tự": {
    "en": "In the game, use the command to get the 6-character link code",
    "ja": "ゲーム内でコマンドを使用して 6 文字のリンク コードを取得します。",
    "cn": "游戏中使用命令获取6字符链接码"
  },
  "Web panel tích hợp trong bot (). Theo dõi trạng thái kết nối Discord": {
    "en": "Web panel integrated in bot(). Monitor Discord connection status",
    "ja": "bot() に統合された Web パネル。 Discordの接続ステータスを監視します。",
    "cn": "Web 面板集成在 bot() 中。监控 Discord 连接状态"
  },
  "Đầy đủ các lệnh tiền tố và Slash commands được đồng bộ trực tiếp từ hệ thống": {
    "en": "All prefix commands and Slash commands are synchronized directly from the system",
    "ja": "すべてのプレフィックス コマンドとスラッシュ コマンドはシステムから直接同期されます。",
    "cn": "所有前缀命令和斜杠命令直接从系统同步"
  },
  "• Gõ hoặc để bot tham gia voice và đọc tin nhắn": {
    "en": "• Type or let the bot join the voice and read the message",
    "ja": "• メッセージを入力するか、ボットに音声に参加させてメッセージを読み上げます。",
    "cn": "• 输入或让机器人加入语音并阅读消息"
  },
  "• 🤖 Có thể dùng lệnh Discord trực tiếp từ bot": {
    "en": "• 🤖 Can use Discord commands directly from the bot",
    "ja": "• 🤖 ボットから直接 Discord コマンドを使用できます。",
    "cn": "• 🤖 可以直接从机器人使用Discord 命令"
  },
  "Sakura Bot • Prefix: hoặc": {
    "en": "Sakura Bot • Prefix: or",
    "ja": "さくらボット • プレフィックス: または",
    "cn": "Sakura 机器人 • 前缀：或"
  },
  "Bị cấm sẽ không dùng được lệnh bot (trừ để khiếu nại). Gỡ cấm bằng nút": {
    "en": "If you are banned, you will not be able to use bot commands (except for complaints). Unblock with button",
    "ja": "BANされた場合、ボットコマンドは使用できなくなります（苦情を除く）。ボタンでブロックを解除",
    "cn": "如果您被禁止，您将无法使用机器人命令（投诉除外）。使用按钮解锁"
  },
  "Quản Trị Gacha": {
    "en": "Gacha Admin",
    "ja": "ガチャ管理",
    "cn": "扭蛋管理"
  },
  "Trung Tâm Quản Trị Waifu Gacha": {
    "en": "Waifu Gacha Admin Center",
    "ja": "嫁ガチャ管理センター",
    "cn": "外福扭蛋管理中心"
  },
  "Quản lý lượt roll, lượt claim, trao tặng thẻ anime tùy chỉnh (sao, print #), thu hồi thẻ và duyệt kho nhân vật.": {
    "en": "Manage rolls, claims, grant custom cards (stars, print #), revoke cards and browse character database.",
    "ja": "ロール回数、獲得枠の管理、カスタムカード付与（星、シリアル）、カード削除、キャラ一覧の閲覧。",
    "cn": "管理卷、索赔、奖励自定义动漫卡（明星、印刷#）、撤销卡和浏览角色库存。"
  },
  "Nhân Vật Trong Kho": {
    "en": "Characters in Pool",
    "ja": "登録キャラクター",
    "cn": "库存角色"
  },
  "Thẻ Đã Phát Hành": {
    "en": "Minted Cards",
    "ja": "発行済みカード",
    "cn": "已发行卡"
  },
  "Người Chơi Gacha": {
    "en": "Gacha Players",
    "ja": "ガチャプレイヤー",
    "cn": "扭蛋玩家"
  },
  "Tổng Lượt Roll": {
    "en": "Total Rolls",
    "ja": "総ロール数",
    "cn": "总卷数"
  },
  "Tổng Lượt Claim": {
    "en": "Total Claims",
    "ja": "総獲得数",
    "cn": "索赔总额"
  },
  "Đang Bán Chợ": {
    "en": "Market Listings",
    "ja": "マーケット出品中",
    "cn": "特价中"
  },
  "Quản Lý & Điều Khiển Người Chơi (User Manager)": {
    "en": "User Manager & Controls",
    "ja": "プレイヤー管理・操作",
    "cn": "用户经理"
  },
  "Tra Cứu Người Chơi": {
    "en": "Search Player",
    "ja": "プレイヤー検索",
    "cn": "玩家查询"
  },
  "Điều Chỉnh Lượt Roll": {
    "en": "Adjust Roll Count",
    "ja": "ロール回数の調整",
    "cn": "横滚调整"
  },
  "Điều Chỉnh Lượt Claim": {
    "en": "Adjust Claim Count",
    "ja": "獲得枠の調整",
    "cn": "调整索赔"
  },
  "Trao Tặng Thẻ Waifu Trực Tiếp Cho User": {
    "en": "Grant Waifu Card Directly to User",
    "ja": "ユーザーに直接嫁カードを付与",
    "cn": "直接向用户发放外福卡"
  },
  "Gõ tên để tìm & chọn nhân vật anime...": {
    "en": "Type to search & select anime character...",
    "ja": "アニメキャラクターを検索して選択...",
    "cn": "输入名称来查找并选择动漫角色..."
  },
  "Trao Thẻ Ngay": {
    "en": "Grant Card Now",
    "ja": "今すぐカードを付与",
    "cn": "立即提供您的卡"
  },
  "Danh Sách Thẻ Bài Của Người Dùng": {
    "en": "User's Card Collection",
    "ja": "ユーザーの所持カード一覧",
    "cn": "用户卡列表"
  },
  "Tra Cứu Danh Mục 558+ Nhân Vật Anime": {
    "en": "Browse 558+ Anime Characters Catalog",
    "ja": "558+アニメキャラクター図鑑検索",
    "cn": "查找超过 558 个动漫角色的目录"
  },
  "Tìm theo tên Romaji, tên gốc...": {
    "en": "Search by Romaji or native name...",
    "ja": "ローマ字または原名で検索...",
    "cn": "按罗马字名称、原名搜索..."
  },
  "Bảng Xếp Hạng Toàn Hệ Thống": {
    "en": "Global Leaderboards Hub",
    "ja": "全システムランキングハブ",
    "cn": "全系统排名"
  },
  "Bảng vinh danh thành tích cao thủ: Waifu Gacha, Cấp Độ, Voice Thoại, Câu Cá, Thành Tựu & Minigame.": {
    "en": "Hall of fame: Waifu Gacha, Levels, Voice Activity, Fishing, Achievements & Minigames.",
    "ja": "プレイヤー栄誉殿堂：嫁ガチャ、レベル、ボイス時間、釣り、実績、ミニゲーム。",
    "cn": "表彰大师成就的表格：Waifu Gacha、等级、声音、钓鱼、成就和迷你游戏。"
  },
  "BXH Waifu": {
    "en": "Waifu Ranking",
    "ja": "嫁ランキング",
    "cn": "外服排行榜"
  },
  "BXH Voice": {
    "en": "Voice Ranking",
    "ja": "ボイスランキング",
    "cn": "语音图"
  },
  "Quán Quân Sưu Tầm": {
    "en": "Top Collector Champion",
    "ja": "トップコレクター王者",
    "cn": "收藏品冠军"
  },
  "Tổng Thẻ Bài Sưu Tầm": {
    "en": "Total Cards Collected",
    "ja": "収集された総カード数",
    "cn": "收藏卡总数"
  },
  "Tổng Điểm Yêu Thích 💖": {
    "en": "Total Favourite Points 💖",
    "ja": "総お気に入りポイント 💖",
    "cn": "Total Favorite Score 💖"
  },
  "Top Nhà Sưu Tầm Waifu Điểm Cao Nhất": {
    "en": "Top Waifu Collectors by Points",
    "ja": "高得点嫁コレクタートップ",
    "cn": "Top Highest Scoring Waifu Collectors"
  },
  "Nhà Sưu Tầm": {
    "en": "Collector",
    "ja": "コレクター",
    "cn": "收藏家"
  },
  "Waifu Tiêu Biểu": {
    "en": "Featured Waifu",
    "ja": "代表的な嫁",
    "cn": "典型的外福"
  },
  "Tổng Số Thẻ": {
    "en": "Total Cards",
    "ja": "所持カード数",
    "cn": "卡牌总数"
  },
  "Gộp Sao (⭐)": {
    "en": "Star Merges (⭐)",
    "ja": "星合体 (⭐)",
    "cn": "组合星星 (⭐)"
  },
  "Tổng Điểm Yêu Thích": {
    "en": "Total Favourite Points",
    "ja": "総お気に入りポイント",
    "cn": "最喜爱总分"
  },
  "Quán Quân Kênh Thoại": {
    "en": "Top Voice Speaker",
    "ja": "ボイスチャンネル王者",
    "cn": "语音频道冠军"
  },
  "Tổng Thành Viên Hoạt Động": {
    "en": "Total Active Members",
    "ja": "総アクティブメンバー",
    "cn": "活跃会员总数"
  },
  "Bảng Xếp Hạng Thời Gian Kênh Thoại (Voice Activity)": {
    "en": "Voice Channel Activity Leaderboard",
    "ja": "ボイスチャンネル活動時間ランキング",
    "cn": "Voice Activity Time Chart"
  },
  "Toàn Bộ Máy Chủ": {
    "en": "All Servers (Global)",
    "ja": "すべてのサーバー (グローバル)",
    "cn": "整个服务器"
  },
  "Thời Gian Thoại": {
    "en": "Voice Duration",
    "ja": "通話時間",
    "cn": "通话时间"
  },
  "Tổng Số Giây": {
    "en": "Total Seconds",
    "ja": "総秒数",
    "cn": "总秒数"
  },
  "BXH Minigame": {
    "en": "Minigames Ranking",
    "ja": "ミニゲームランキング",
    "cn": "小游戏排行榜"
  },
  "BXH Cờ Ca-rô (XO)": {
    "en": "Tic-Tac-Toe (XO) Ranking",
    "ja": "五目並べ (XO) ランキング",
    "cn": "Checkered Flag (XO) rankings"
  },
  "BXH Cờ Vua (Chess)": {
    "en": "Chess Ranking",
    "ja": "チェスランキング",
    "cn": "国际象棋排名"
  },
  "BXH Nối Từ (Word Chain)": {
    "en": "Word Chain Ranking",
    "ja": "しりとりランキング",
    "cn": "字链图"
  },
  "Đổi Sao": {
    "en": "Change Stars",
    "ja": "星数変更",
    "cn": "更换星星"
  },
  "Xóa Thẻ": {
    "en": "Delete Card",
    "ja": "カード削除",
    "cn": "删除标签"
  },
  "Huyền Thoại": {
    "en": "Legendary",
    "ja": "レジェンド",
    "cn": "传奇"
  },
  "Sử Thi": {
    "en": "Epic",
    "ja": "エピック",
    "cn": "史诗"
  },
  "Làm Mới Số Liệu": {
    "en": "Refresh Stats",
    "ja": "数値を更新",
    "cn": "刷新数据"
  },
  "Trao Thẻ Cho User": {
    "en": "Grant Card to User",
    "ja": "ユーザーにカードを付与",
    "cn": "将卡交给用户"
  },
  "(Không có phản hồi từ console)": {
    "en": "(No response from console)",
    "ja": "(コンソールから応答がありません)",
    "cn": "（控制台无响应）"
  },
  "+5 điểm": {
    "en": "+5 points",
    "ja": "+5ポイント",
    "cn": "+5 点"
  },
  "-- Chọn vai trò nhận --": {
    "en": "-- Select recipient role --",
    "ja": "-- 受信者の役割を選択 --",
    "cn": "-- 选择收件人角色 --"
  },
  "-5 điểm": {
    "en": "-5 points",
    "ja": "-5ポイント",
    "cn": "-5分"
  },
  "/changepassword &lt;mật_khẩu_cũ&gt; &lt;mật_khẩu_mới&gt;": {
    "en": "/changepassword <old_password> <new_password>",
    "ja": "/changepassword <古いパスワード> <新しいパスワード>",
    "cn": "/changepassword <旧密码> <新密码>"
  },
  "/discord [link &lt;mã_liên_kết&gt; | transfer &lt;số_coin&gt; | status]": {
    "en": "/discord [link <link_code> | transfer <number_coin> | status]",
    "ja": "/discord [リンク <リンクコード> | <数値_コイン> を転送 |ステータス】",
    "cn": "/discord [链接 <链接代码> |转账 <number_coin> |状态]"
  },
  "/login &lt;mật_khẩu&gt;": {
    "en": "/login <password>",
    "ja": "/login <パスワード>",
    "cn": "/登录<密码>"
  },
  "/pay &lt;người_nhận&gt; &lt;số_tiền&gt;": {
    "en": "/pay <recipient> <amount>",
    "ja": "/pay <受取人> <金額>",
    "cn": "/pay <收款人> <金额>"
  },
  "/register &lt;mật_khẩu&gt; &lt;nhập_lại_mật_khẩu&gt;": {
    "en": "/register <password> <re-enter_password>",
    "ja": "/register <パスワード> <パスワードの再入力>",
    "cn": "/register <密码> <重新输入密码>"
  },
  "/setwarp &lt;tên_warp&gt;": {
    "en": "/setwarp <warp_name>",
    "ja": "/setwarp <ワープ名>",
    "cn": "/setwarp <扭曲名称>"
  },
  "/tên_bạn/profile": {
    "en": "/your_name/profile",
    "ja": "/あなたの名前/プロフィール",
    "cn": "/你的名字/个人资料"
  },
  "/warp &lt;tên_warp&gt;": {
    "en": "/warp <warp_name>",
    "ja": "/warp <ワープ名>",
    "cn": "/经线 <经线名称>"
  },
  "0 thẻ": {
    "en": "0 cards",
    "ja": "カード0枚",
    "cn": "0 张卡"
  },
  "1 ⭐ (Gốc x1)": {
    "en": "1 ⭐ (Original x1)",
    "ja": "1 ⭐ (オリジナル x1)",
    "cn": "1 ⭐（原版 x1）"
  },
  "2 ⭐ (Điểm x2)": {
    "en": "2 ⭐ (Score x2)",
    "ja": "2 ⭐ (スコア x2)",
    "cn": "2 ⭐（分数 x2）"
  },
  "3 ⭐ (Điểm x4)": {
    "en": "3 ⭐ (Score x4)",
    "ja": "3 ⭐ (スコア x4)",
    "cn": "3 ⭐（得分 x4）"
  },
  "4 ⭐ (Điểm x8)": {
    "en": "4 ⭐ (Score x8)",
    "ja": "4 ⭐ (スコア x8)",
    "cn": "4 ⭐（得分 x8）"
  },
  "5 ⭐ (Điểm x16)": {
    "en": "5 ⭐ (Score x16)",
    "ja": "5 ⭐ (スコア x16)",
    "cn": "5 ⭐（分数 x16）"
  },
  "Không có kênh gửi tin": {
    "en": "There is no sending channel",
    "ja": "送信チャンネルがありません",
    "cn": "没有发送通道"
  },
  "Không có kênh text": {
    "en": "There is no text channel",
    "ja": "テキストチャンネルはありません",
    "cn": "没有文字频道"
  },
  "(Không có đột biến)": {
    "en": "(No mutation)",
    "ja": "(突然変異なし)",
    "cn": "（无突变）"
  },
  "(Không tặng cần)": {
    "en": "(No gift)",
    "ja": "（プレゼントはありません）",
    "cn": "（无礼物）"
  },
  "(Không tặng mồi)": {
    "en": "(No bait given)",
    "ja": "（餌は与えませんでした）",
    "cn": "（不给饵料）"
  },
  "(Không tặng pet)": {
    "en": "(Do not give pets)",
    "ja": "（ペットには与えないでください）",
    "cn": "（请勿饲养宠物）"
  },
  "(Không tặng rương)": {
    "en": "(No chests given)",
    "ja": "(宝箱は与えられません)",
    "cn": "（没有提供宝箱）"
  },
  "-- Chọn kênh nhận tin --": {
    "en": "-- Select channel to receive news --",
    "ja": "-- ニュースを受信するチャンネルを選択してください --",
    "cn": "-- 选择接收新闻的频道 --"
  },
  "-- Chọn kênh tổ chức --": {
    "en": "-- Select organizational channel --",
    "ja": "-- 組織チャネルの選択 --",
    "cn": "-- 选择组织渠道 --"
  },
  "-- Chọn nhanh thợ mỏ (": {
    "en": "-- Quickly select miners (",
    "ja": "-- マイナーを素早く選択 (",
    "cn": "-- 快速选择矿工（"
  },
  "-- Trống = gửi tại kênh chat --": {
    "en": "-- Empty = sent to chat channel --",
    "ja": "-- 空 = チャット チャネルに送信 --",
    "cn": "-- 空 = 发送到聊天频道 --"
  },
  "Bể Thủy Cung hiện đang trống (cần thủ chưa thả con cá nào vào bể).": {
    "en": "The Aquarium tank is currently empty (anglers have not released any fish into the tank).",
    "ja": "水族館の水槽は現在空です（釣り人は水槽に魚を放していません）。",
    "cn": "水族馆的水箱目前是空的（钓鱼者尚未将任何鱼放入水箱中）。"
  },
  "Chưa có Custom Key nào được thiết lập.": {
    "en": "No Custom Key has been set yet.",
    "ja": "カスタムキーはまだ設定されていません。",
    "cn": "尚未设置自定义密钥。"
  },
  "Chưa có ai bị cấm toàn cục": {
    "en": "No one has been banned globally",
    "ja": "世界的に禁止された人はいない",
    "cn": "全球范围内尚未有人被禁止"
  },
  "Chưa có ai bị cấm ở server này": {
    "en": "No one has been banned from this server yet",
    "ja": "このサーバーからはまだ誰も禁止されていません",
    "cn": "尚未有人被禁止使用该服务器"
  },
  "Chưa có bản sao lưu nào. Bấm": {
    "en": "There are no backups yet. Click",
    "ja": "まだバックアップはありません。クリック",
    "cn": "还没有备份。点击"
  },
  "Chưa có bảng Reaction Role nào trong server.": {
    "en": "There is no Reaction Role table in the server yet.",
    "ja": "サーバーにはまだリアクション ロール テーブルがありません。",
    "cn": "服务器中还没有反应角色表。"
  },
  "Chưa có cần câu nào": {
    "en": "There are no fishing rods yet",
    "ja": "釣り竿はまだありません",
    "cn": "还没有钓鱼竿"
  },
  "Chưa có dữ liệu cho mục này.": {
    "en": "There is no data for this item.",
    "ja": "この項目にはデータがありません。",
    "cn": "没有该项目的数据。"
  },
  "Chưa có dữ liệu hoạt động voice nào.": {
    "en": "There is no voice activity data yet.",
    "ja": "音声アクティビティ データはまだありません。",
    "cn": "目前还没有语音活动数据。"
  },
  "Chưa có dữ liệu sưu tập Waifu nào.": {
    "en": "There is no Waifu collection data yet.",
    "ja": "Waifu コレクション データはまだありません。",
    "cn": "目前还没有Waifu收集数据。"
  },
  "Chưa có dữ liệu điểm số nối chữ.": {
    "en": "There is no word matching score data yet.",
    "ja": "単語一致スコア データはまだありません。",
    "cn": "目前还没有单词匹配分数数据。"
  },
  "Chưa có giveaway nào được tổ chức trên server này.": {
    "en": "No giveaways have been organized on this server yet.",
    "ja": "このサーバーではまだプレゼント企画が行われていません。",
    "cn": "该服务器上尚未组织任何赠品活动。"
  },
  "Chưa có mã Giftcode nào trong hệ thống.": {
    "en": "There are no Giftcodes in the system yet.",
    "ja": "システムにはまだギフトコードがありません。",
    "cn": "系统中还没有礼品代码。"
  },
  "Chưa có mồi câu nào": {
    "en": "No bait yet",
    "ja": "まだ餌はありません",
    "cn": "还没有诱饵"
  },
  "Chưa có mồi hoặc rương báu nào.": {
    "en": "There are no baits or treasure chests yet.",
    "ja": "まだ餌や宝箱はありません。",
    "cn": "目前还没有诱饵或宝箱。"
  },
  "Chưa có thành tích câu cá trong khu vực này.": {
    "en": "There are no fishing records in this area.",
    "ja": "この地域での釣行記録はありません。",
    "cn": "该地区没有任何捕捞记录。"
  },
  "Chưa có thú cưng nào": {
    "en": "No pets yet",
    "ja": "まだペットはいません",
    "cn": "还没有宠物"
  },
  "Chưa có vật phẩm tiện ích nào": {
    "en": "There are no utility items yet",
    "ja": "ユーティリティアイテムはまだありません",
    "cn": "还没有实用物品"
  },
  "Chưa có vật tư nào.": {
    "en": "No supplies yet.",
    "ja": "まだ物資はありません。",
    "cn": "还没有货源。"
  },
  "Chưa có ô đất nào.": {
    "en": "There are no plots of land yet.",
    "ja": "まだ土地はありません。",
    "cn": "目前还没有土地。"
  },
  "Chưa có": {
    "en": "Not yet",
    "ja": "まだ",
    "cn": "还没有"
  },
  "Chưa nối Guild": {
    "en": "Not connected to Guild yet",
    "ja": "まだギルドに接続されていません",
    "cn": "尚未连接到公会"
  },
  "Chưa sở hữu cần câu nào.": {
    "en": "Don't own any fishing rods yet.",
    "ja": "まだ釣り竿を持っていません。",
    "cn": "还没有任何钓鱼竿。"
  },
  "Chưa thiết lập mốc role nào. Đặt mốc level ở trên và chọn vai trò để tự động trao.": {
    "en": "No role milestones have been set yet. Set the level milestone above and select roles to automatically award.",
    "ja": "役割のマイルストーンはまだ設定されていません。上記のレベルマイルストーンを設定し、自動的に授与する役割を選択します。",
    "cn": "尚未设定角色里程碑。在上面设置级别里程碑并选择要自动奖励的角色。"
  },
  "Chưa đặt": {
    "en": "Not booked yet",
    "ja": "まだ予約されていません",
    "cn": "尚未预订"
  },
  "Chủ sở hữu tối cao": {
    "en": "Supreme owner",
    "ja": "最高の所有者",
    "cn": "至尊拥有者"
  },
  "Cần <a href=": {
    "en": "Need <a href=",
    "ja": "<a href= が必要です",
    "cn": "需要<a href="
  },
  "Danh dự": {
    "en": "Honor",
    "ja": "名誉",
    "cn": "荣誉资质"
  },
  "Giỏ cá của cần thủ đang trống.": {
    "en": "The angler's fish basket is empty.",
    "ja": "釣り人の魚かごは空です。",
    "cn": "钓鱼者的鱼篮是空的。"
  },
  "Gặp sự cố kết nối": {
    "en": "Having connection problems",
    "ja": "接続に問題がある",
    "cn": "有连接问题"
  },
  "Hiếm": {
    "en": "Rare",
    "ja": "珍しい",
    "cn": "稀有"
  },
  "Không có kênh thoại": {
    "en": "There are no voice channels",
    "ja": "音声チャンネルはありません",
    "cn": "没有语音频道"
  },
  "Không có người dùng nào phù hợp với bộ lọc.": {
    "en": "There are no users matching the filter.",
    "ja": "フィルターに一致するユーザーはいません。",
    "cn": "没有与过滤器匹配的用户。"
  },
  "Không có sự kiện giveaway nào đang diễn ra.": {
    "en": "There are no giveaway events currently underway.",
    "ja": "現在開催中のプレゼントイベントはありません。",
    "cn": "目前没有正在进行的赠品活动。"
  },
  "Không có thành tựu nào khớp bộ lọc.": {
    "en": "There are no achievements matching the filter.",
    "ja": "フィルターに一致する実績はありません。",
    "cn": "没有符合筛选条件的成就。"
  },
  "Không có thành viên": {
    "en": "No members",
    "ja": "メンバーがいません",
    "cn": "没有会员"
  },
  "Không thể tải BXH câu cá": {
    "en": "Unable to load fishing rankings",
    "ja": "釣りランキングを読み込めません",
    "cn": "无法加载钓鱼排名"
  },
  "Không thể tải danh sách thành tựu": {
    "en": "Unable to load achievements list",
    "ja": "実績リストをロードできません",
    "cn": "无法加载成就列表"
  },
  "Không thể tải dữ liệu thành tựu của người chơi này.": {
    "en": "This player's achievement data could not be loaded.",
    "ja": "このプレイヤーの実績データをロードできませんでした。",
    "cn": "无法加载该玩家的成就数据。"
  },
  "Không tìm thấy lệnh phù hợp.": {
    "en": "No matching command found.",
    "ja": "一致するコマンドが見つかりませんでした。",
    "cn": "未找到匹配的命令。"
  },
  "Không tìm thấy mục nào phù hợp với bộ lọc trong Bách Khoa.": {
    "en": "No items matching the filter were found in Bach Khoa.",
    "ja": "Bach Khoa にはフィルターに一致するアイテムが見つかりませんでした。",
    "cn": "在 Bach Khoa 找不到符合筛选条件的物品。"
  },
  "Không tìm thấy nhân vật nào phù hợp.": {
    "en": "No matching characters were found.",
    "ja": "一致する文字が見つかりませんでした。",
    "cn": "没有找到匹配的字符。"
  },
  "Không tìm thấy thành tựu phù hợp.": {
    "en": "No matching achievements found.",
    "ja": "一致する実績は見つかりませんでした。",
    "cn": "未找到匹配的成就。"
  },
  "Lỗi tải bảng xếp hạng": {
    "en": "Error loading rankings",
    "ja": "ランキングの読み込みエラー",
    "cn": "加载排名时出错"
  },
  "Người chơi này chưa có thẻ bài nào trong kho.": {
    "en": "This player does not have any cards in his inventory yet.",
    "ja": "このプレイヤーはまだインベントリにカードを持っていません。",
    "cn": "该玩家的库存中还没有任何卡牌。"
  },
  "Người chơi này chưa mở khóa thành tựu nào.": {
    "en": "This player has not unlocked any achievements yet.",
    "ja": "このプレイヤーはまだ実績を解除していません。",
    "cn": "该玩家尚未解锁任何成就。"
  },
  "Trưng bày": {
    "en": "Display",
    "ja": "ディスプレイ",
    "cn": "显示"
  },
  "Túi quặng đang trống.": {
    "en": "The ore bag is empty.",
    "ja": "鉱石袋は空です。",
    "cn": "矿石袋是空的。"
  },
  "ĐANG DÙNG": {
    "en": "IN USE",
    "ja": "使用中",
    "cn": "使用中"
  },
  "Đang tải Global Chat...": {
    "en": "Loading Global Chat...",
    "ja": "グローバル チャットを読み込んでいます...",
    "cn": "正在加载全球聊天..."
  },
  "Đang tải danh sách Giveaway...": {
    "en": "Loading Giveaway list...",
    "ja": "プレゼントリストを読み込んでいます...",
    "cn": "正在加载赠品列表..."
  },
  "Đang tải danh sách kênh...": {
    "en": "Loading channel list...",
    "ja": "チャンネルリストを読み込み中...",
    "cn": "正在加载频道列表..."
  },
  "Đang tải danh sách server...": {
    "en": "Loading server list...",
    "ja": "サーバーリストを読み込んでいます...",
    "cn": "正在加载服务器列表..."
  },
  "Đang tải danh sách thành tựu...": {
    "en": "Loading achievement list...",
    "ja": "実績リストを読み込んでいます...",
    "cn": "正在加载成就列表..."
  },
  "Đang tải dữ liệu cấp độ...": {
    "en": "Loading level data...",
    "ja": "レベルデータをロード中...",
    "cn": "正在加载关卡数据..."
  },
  "Đang tải dữ liệu cần thủ...": {
    "en": "Loading angler data...",
    "ja": "アングラーデータをロード中...",
    "cn": "正在加载钓鱼者数据..."
  },
  "Đang tải hồ sơ thành tựu...": {
    "en": "Loading achievement profile...",
    "ja": "実績プロファイルを読み込んでいます...",
    "cn": "正在加载成就资料..."
  },
  "Đang tải thành viên...": {
    "en": "Loading members...",
    "ja": "メンバーを読み込んでいます...",
    "cn": "正在加载会员..."
  },
  "Đã tắt (Offline)": {
    "en": "Disabled (Offline)",
    "ja": "無効 (オフライン)",
    "cn": "已禁用（离线）"
  },
  "đăng nhập để dùng Global Chat giữa các tài khoản 🌸": {
    "en": "Log in to use Global Chat between accounts 🌸",
    "ja": "アカウント間でグローバルチャットを使用するにはログインしてください 🌸",
    "cn": "登录后即可在帐户之间使用全局聊天 💕"
  },
  "Ổn định (Online)": {
    "en": "Stable (Online)",
    "ja": "安定した (オンライン)",
    "cn": "稳定（在线）"
  },
  "— Chưa chọn —${textChannels.map(c => `<option value=": {
    "en": "— Not selected —${textChannels.map(c => `<option value=",
    "ja": "— 未選択 —${textChannels.map(c => `<オプション値=",
    "cn": "— 未选择 —${textChannels.map(c => `<选项值="
  },
  "— Chọn Máy Chủ Discord —": {
    "en": "— Select Discord Server —",
    "ja": "— Discord サーバーの選択 —",
    "cn": "— 选择 Discord 服务器 —"
  },
  "— Không chọn kênh —": {
    "en": "— No channel selection —",
    "ja": "— チャンネル選択なし —",
    "cn": "— 无频道选择 —"
  },
  "— Mọi kênh / Chưa giới hạn —": {
    "en": "— All Channels / Unlimited —",
    "ja": "— 全チャンネル / 無制限 —",
    "cn": "— 所有频道/无限 —"
  },
  "— Vui lòng chọn Discord Server trước —": {
    "en": "— Please select Discord Server first —",
    "ja": "— 最初に Discord サーバーを選択してください —",
    "cn": "— 请先选择 Discord 服务器 —"
  },
  "⏳ HSD: ${item.duration_days} ngày (${item.renewable ?": {
    "en": "⏳ Expiration date: ${item.duration_days} days (${item.renewable ?",
    "ja": "⏳ 有効期限: ${item.duration_days} 日 (${item.renewable ?",
    "cn": "⏳ 到期日期：${item.duration_days} 天（${item.renewable ?"
  },
  "⏳ Đang gửi thử nghiệm mã code qua bot...": {
    "en": "⏳ Sending test code via bot...",
    "ja": "⏳ ボット経由でテストコードを送信...",
    "cn": "⏳ 通过机器人发送测试代码..."
  },
  "⏳ Đang nạp BXH nối chữ...": {
    "en": "⏳ Loading charts to connect letters...",
    "ja": "⏳ 文字を接続するためのチャートをロードしています...",
    "cn": "⏳ 正在加载图表以连接字母..."
  },
  "⏳ Đang nạp danh sách lệnh từ Plugin Sakura...": {
    "en": "⏳ Loading command list from Sakura Plugin...",
    "ja": "⏳ さくらプラグインからコマンドリストを読み込み中...",
    "cn": "⏳ 正在从 Sakura 插件加载命令列表..."
  },
  "⏳ Đang tải BXH Voice...": {
    "en": "⏳ Loading Voice chart...",
    "ja": "⏳ 音声チャートを読み込み中...",
    "cn": "⏳ 正在加载语音图表..."
  },
  "⏳ Đang tải Bảng Xếp Hạng Waifu...": {
    "en": "⏳ Loading Waifu Leaderboard...",
    "ja": "⏳ ワイフ リーダーボードを読み込んでいます...",
    "cn": "⏳ 正在加载 Waifu 排行榜..."
  },
  "⏳ Đang tải danh sách kênh...": {
    "en": "⏳ Loading channel list...",
    "ja": "⏳ チャンネルリストを読み込み中...",
    "cn": "⏳ 正在加载频道列表..."
  },
  "⏳ Đang tải danh sách người dùng & Admin web...": {
    "en": "⏳ Loading user list & web Admin...",
    "ja": "⏳ ユーザーリストと Web 管理者をロード中...",
    "cn": "⏳ 正在加载用户列表和网络管理..."
  },
  "⏳ Đang tải...": {
    "en": "⏳ Loading...",
    "ja": "⏳ 読み込み中...",
    "cn": "⏳ 加载中..."
  },
  "⏹️ Kết thúc sớm` :": {
    "en": "⏹️ Ending early`:",
    "ja": "⏹️早期終了します`:",
    "cn": "⏹️提早结束`:"
  },
  "⚠️ Khô": {
    "en": "⚠️ Dry",
    "ja": "⚠️ドライ",
    "cn": "⚠️干"
  },
  "⚠️ Link ảnh banner không tải được": {
    "en": "⚠️ Banner image link cannot be downloaded",
    "ja": "⚠️バナー画像リンクはダウンロードできません",
    "cn": "⚠️ 横幅图片链接无法下载"
  },
  "⚠️ Đầy lượt": {
    "en": "⚠️ Full turn",
    "ja": "⚠️フルターン",
    "cn": "⚠️全转"
  },
  "✨ Chín Mọng": {
    "en": "✨ Ripe Succulent",
    "ja": "✨熟した多肉植物",
    "cn": "✨ 成熟多肉"
  },
  "❌ Không thể tải kênh": {
    "en": "❌ Unable to load channel",
    "ja": "❌ チャンネルをロードできません",
    "cn": "❌ 无法加载频道"
  },
  "❌ Lỗi kết nối tải kênh": {
    "en": "❌ Channel download connection error",
    "ja": "❌ チャンネルダウンロード接続エラー",
    "cn": "❌ 频道下载连接错误"
  },
  "⭐ LINH VẬT BỂ": {
    "en": "⭐ TANK MASTER",
    "ja": "⭐タンクマスター",
    "cn": "⭐ 坦克大师"
  },
  "⭐ LINH VẬT` :": {
    "en": "⭐ MASTERS` :",
    "ja": "⭐マスター` :",
    "cn": "⭐ 大师`："
  },
  "＋ Thêm kênh...": {
    "en": "＋Add channel...",
    "ja": "＋チャンネルを追加...",
    "cn": "＋添加频道..."
  },
  "🏛️ Kính": {
    "en": "🏛️ Glasses",
    "ja": "🏛️ メガネ",
    "cn": "🏛️眼镜"
  },
  "🐛 Sâu": {
    "en": "🐛 Deep",
    "ja": "🐛 深い",
    "cn": "🐛 深"
  },
  "👑 CHỦ SỞ HỮU WEB": {
    "en": "👑 WEB OWNER",
    "ja": "👑 ウェブオーナー",
    "cn": "👑 网站所有者"
  },
  "👤 NGƯỜI DÙNG": {
    "en": "👤 USERS",
    "ja": "👤 ユーザー",
    "cn": "👤 用户"
  },
  "💧 Đất Ẩm": {
    "en": "💧 Moist Soil",
    "ja": "💧 湿った土壌",
    "cn": "💧潮湿的土壤"
  },
  "🔍 Không tìm thấy lệnh nào phù hợp với từ khóa.": {
    "en": "🔍 No commands found matching the keyword.",
    "ja": "🔍 キーワードに一致するコマンドが見つかりませんでした。",
    "cn": "🔍 未找到与关键字匹配的命令。"
  },
  "🔍 Không tìm thấy từ nào phù hợp.": {
    "en": "🔍 No suitable words found.",
    "ja": "🔍 適切な言葉が見つかりません。",
    "cn": "🔍 没有找到合适的词语。"
  },
  "🔴 Đã hết hạn": {
    "en": "🔴 Expired",
    "ja": "🔴期限切れ",
    "cn": "🔴已过期"
  },
  "🟢 Còn hạn": {
    "en": "🟢 Limited time",
    "ja": "🟢 期間限定",
    "cn": "🟢 时间有限"
  },
  "🥀 Héo Úa": {
    "en": "🥀 Withered",
    "ja": "🥀 枯れた",
    "cn": "🥀枯萎了"
  },
  "Backup từ Web Dashboard": {
    "en": "Backup from Web Dashboard",
    "ja": "Webダッシュボードからのバックアップ",
    "cn": "从 Web 仪表板备份"
  },
  "Biệt danh mới:": {
    "en": "New nickname:",
    "ja": "新しいニックネーム:",
    "cn": "新昵称："
  },
  "Bé Tí": {
    "en": "Baby Ti",
    "ja": "ベイビー・ティ",
    "cn": "蒂宝贝"
  },
  "Bình thường": {
    "en": "Normal",
    "ja": "ノーマル",
    "cn": "正常"
  },
  "Bạn có chắc chắn muốn RESET toàn bộ trang trại của nông dân này về mặc định không?": {
    "en": "Are you sure you want to RESET this farmer's entire farm to default?",
    "ja": "このファーマーのファーム全体をデフォルトにリセットしてもよろしいですか?",
    "cn": "您确定要将此农民的整个农场重置为默认值吗？"
  },
  "Bạn có chắc chắn muốn dọn sạch toàn bộ cá trong Thủy Cung của cần thủ này?": {
    "en": "Are you sure you want to clear out all the fish in this angler's Aquarium?",
    "ja": "この釣り人の水族館の魚をすべて一掃してもよろしいですか?",
    "cn": "您确定要清除该钓鱼者水族馆中的所有鱼吗？"
  },
  "Bạn có chắc chắn muốn kết thúc sớm giveaway này và quay thưởng ngay?": {
    "en": "Are you sure you want to end this giveaway early and draw prizes right away?",
    "ja": "このプレゼント企画を早めに終了して、すぐに賞品を抽選してもよろしいですか?",
    "cn": "您确定要提前结束本次抽奖并立即抽奖吗？"
  },
  "Bạn có chắc chắn muốn xóa dữ liệu giveaway này không?": {
    "en": "Are you sure you want to delete this giveaway data?",
    "ja": "このプレゼントデータを削除してもよろしいですか?",
    "cn": "您确定要删除此赠品数据吗？"
  },
  "Bạn có chắc muốn hủy liên kết server Minecraft này khỏi Discord Guild?": {
    "en": "Are you sure you want to unlink this Minecraft server from the Discord Guild?",
    "ja": "この Minecraft サーバーを Discord ギルドからリンク解除してもよろしいですか?",
    "cn": "您确定要取消此 Minecraft 服务器与 Discord Guild 的链接吗？"
  },
  "Bạn có chắc muốn kết thúc Giveaway này ngay bây giờ?": {
    "en": "Are you sure you want to end this Giveaway now?",
    "ja": "このプレゼントを今すぐ終了してもよろしいですか?",
    "cn": "您确定要立即结束此赠品吗？"
  },
  "Bạn có chắc muốn phát Daily Giftcode hôm nay ngay bây giờ?": {
    "en": "Are you sure you want to give today's Daily Giftcode right now?",
    "ja": "今日のデイリー ギフトコードを今すぐ贈ってもよろしいですか?",
    "cn": "您确定要立即提供今天的每日礼品代码吗？"
  },
  "Bạn có chắc muốn xóa Custom Key này?": {
    "en": "Are you sure you want to delete this Custom Key?",
    "ja": "このカスタム キーを削除してもよろしいですか?",
    "cn": "您确定要删除此自定义密钥吗？"
  },
  "Bạn có chắc muốn xóa bảng Reaction Role này khỏi server?": {
    "en": "Are you sure you want to delete this Reaction Role table from the server?",
    "ja": "このリアクション ロール テーブルをサーバーから削除してもよろしいですか?",
    "cn": "您确定要从服务器中删除此反应角色表吗？"
  },
  "Bạn có chắc muốn xóa con cá này khỏi giỏ đồ của người chơi?": {
    "en": "Are you sure you want to remove this fish from the player's inventory?",
    "ja": "この魚をプレイヤーの在庫から削除してもよろしいですか?",
    "cn": "您确定要从玩家的库存中删除这条鱼吗？"
  },
  "Bạn có chắc muốn xóa sạch toàn bộ cá trong Thủy Cung này không?": {
    "en": "Are you sure you want to wipe out all the fish in this Aquarium?",
    "ja": "この水族館の魚をすべて一掃してもよろしいですか?",
    "cn": "你确定要消灭这个水族馆里的所有鱼吗？"
  },
  "Bạn có chắc muốn xóa vĩnh viễn chú cá này khỏi Thủy Cung?": {
    "en": "Are you sure you want to permanently delete this fish from the Aquarium?",
    "ja": "この魚を水族館から完全に削除してもよろしいですか?",
    "cn": "您确定要从水族馆中永久删除这条鱼吗？"
  },
  "Bạn có chắc muốn xóa vĩnh viễn con cá này khỏi Thủy Cung?": {
    "en": "Are you sure you want to permanently remove this fish from the Aquarium?",
    "ja": "この魚を水族館から永久に削除してもよろしいですか?",
    "cn": "您确定要将这条鱼从水族馆永久移除吗？"
  },
  "Bạn không có quyền quản lý server này": {
    "en": "You do not have permission to manage this server",
    "ja": "このサーバーを管理する権限がありません",
    "cn": "您没有权限管理此服务器"
  },
  "BẢNG CHỌN VAI TRÒ": {
    "en": "ROLE SELECTION SHEET",
    "ja": "役割選択シート",
    "cn": "角色选择表"
  },
  "Bấm để chuyển sang xem giao diện như người dùng thường": {
    "en": "Click to switch to viewing the interface like a normal user",
    "ja": "クリックすると、通常のユーザーと同じインターフェイスの表示に切り替わります。",
    "cn": "点击切换到像普通用户一样查看界面"
  },
  "Bấm để quay lại toàn quyền Quản Trị Viên": {
    "en": "Click to return to full Administrator rights",
    "ja": "クリックすると完全な管理者権限に戻ります",
    "cn": "单击可返回完整的管理员权限"
  },
  "CUỐC +150 &amp; 20⭐": {
    "en": "HOOK +150 & 20⭐",
    "ja": "フック+150&20⭐",
    "cn": "钩+150 & 20⭐"
  },
  "Chuyển con cá này về lại giỏ cá": {
    "en": "Move this fish back to the fish basket",
    "ja": "この魚を魚かごに戻してください",
    "cn": "将此鱼移回鱼篮"
  },
  "Chuyển sang chế độ sáng": {
    "en": "Switch to bright mode",
    "ja": "明るいモードに切り替える",
    "cn": "切换到明亮模式"
  },
  "Chuyển sang chế độ tối": {
    "en": "Switch to dark mode",
    "ja": "ダークモードに切り替える",
    "cn": "切换到深色模式"
  },
  "Chào mừng {user} đến với {server}! 🌸 Hãy đọc luật và vui vẻ nhé~": {
    "en": "Welcome {user} to {server}! 🌸 Please read the rules and have fun~",
    "ja": "{user} を {server} にようこそ! 🌸 ルールを読んで楽しんでください~",
    "cn": "欢迎 {user} 访问 {server}！ 🌟请仔细阅读规则，祝大家玩得开心~"
  },
  "Chưa chọn kênh — TempVoice đang tắt.": {
    "en": "Channel not selected — TempVoice is off.",
    "ja": "チャンネルが選択されていません — TempVoice がオフになっています。",
    "cn": "未选择通道 — TempVoice 已关闭。"
  },
  "Chưa chọn loại đột biến hoặc hoa màu": {
    "en": "Haven't chosen any mutations or crops yet",
    "ja": "まだ突然変異や作物を選択していません",
    "cn": "尚未选择任何突变或作物"
  },
  "Chưa chọn server Minecraft": {
    "en": "Haven't selected a Minecraft server yet",
    "ja": "Minecraft サーバーをまだ選択していません",
    "cn": "尚未选择 Minecraft 服务器"
  },
  "Chưa chọn vật phẩm": {
    "en": "Item not selected yet",
    "ja": "項目はまだ選択されていません",
    "cn": "尚未选择项目"
  },
  "Chưa có cá": {
    "en": "No fish yet",
    "ja": "まだ魚がいない",
    "cn": "还没有鱼"
  },
  "Chưa có mô tả": {
    "en": "No description yet",
    "ja": "まだ説明がありません",
    "cn": "还没有描述"
  },
  "Chưa có tin nhắn Global nào — hãy là người đầu tiên!": {
    "en": "There are no Global messages yet — be the first!",
    "ja": "まだグローバル メッセージはありません — 最初になってください!",
    "cn": "还没有全球消息 - 成为第一个！"
  },
  "Chưa kết nối": {
    "en": "Not connected yet",
    "ja": "まだ接続されていません",
    "cn": "尚未连接"
  },
  "Chưa rõ": {
    "en": "Not clear yet",
    "ja": "まだ明確ではありません",
    "cn": "还不清楚"
  },
  "Chưa tải cấu hình": {
    "en": "Configuration not loaded yet",
    "ja": "構成はまだロードされていません",
    "cn": "配置尚未加载"
  },
  "Chế độ sáng (Light mode)": {
    "en": "Light mode",
    "ja": "ライトモード",
    "cn": "灯光模式"
  },
  "Chế độ tối (Dark mode)": {
    "en": "Dark mode",
    "ja": "ダークモード",
    "cn": "深色模式"
  },
  "Chế độ ĐỒNG BỘ (Sync Mode): Giữ nguyên tin nhắn hiện có và đồng bộ lại phân quyền/kênh thiếu sót.": {
    "en": "SYNC Mode: Preserve existing messages and re-synchronize missing permissions/channels.",
    "ja": "SYNC モード: 既存のメッセージを保持し、不足している権限/チャネルを再同期します。",
    "cn": "同步模式：保留现有消息并重新同步丢失的权限/通道。"
  },
  "Chỉ quản lý server có quyền": {
    "en": "Only server administrators have permission",
    "ja": "サーバー管理者のみが権限を持っています",
    "cn": "只有服务器管理员有权限"
  },
  "Chọn 1 hoặc nhiều thành viên": {
    "en": "Select 1 or more members",
    "ja": "1 人以上のメンバーを選択してください",
    "cn": "选择 1 名或多名成员"
  },
  "Chọn Kênh Confession trước khi bật": {
    "en": "Select Confession Channel before turning it on",
    "ja": "告白チャンネルをオンにする前に選択してください",
    "cn": "开启之前选择告白频道"
  },
  "Chọn kênh trước": {
    "en": "Select the channel first",
    "ja": "最初にチャンネルを選択してください",
    "cn": "首先选择频道"
  },
  "Chọn kênh và nhập nội dung": {
    "en": "Select channel and enter content",
    "ja": "チャンネルを選択してコンテンツを入力します",
    "cn": "选择频道并输入内容"
  },
  "Chọn kênh đăng panel": {
    "en": "Select the channel to post the panel",
    "ja": "パネルを投稿するチャンネルを選択してください",
    "cn": "选择发布面板的频道"
  },
  "Chọn kênh để clear": {
    "en": "Select channel to clear",
    "ja": "クリアするチャンネルを選択してください",
    "cn": "选择要清除的通道"
  },
  "Chọn mục cài đặt": {
    "en": "Select the installation item",
    "ja": "インストール項目を選択してください",
    "cn": "选择安装项"
  },
  "Chọn thành viên hoặc nhập ID": {
    "en": "Select member or enter ID",
    "ja": "メンバーを選択するかIDを入力してください",
    "cn": "选择会员或输入ID"
  },
  "Cá": {
    "en": "Fish",
    "ja": "魚",
    "cn": "鱼"
  },
  "Cá Biển": {
    "en": "Sea Fish",
    "ja": "海の魚",
    "cn": "海鱼"
  },
  "Cá Con Lạc Lối": {
    "en": "Lost Little Fish",
    "ja": "失われた小さな魚",
    "cn": "迷失的小鱼"
  },
  "Câu cá tự nhiên": {
    "en": "Natural fishing",
    "ja": "天然釣り",
    "cn": "自然钓鱼"
  },
  "Cường Hóa &amp; Tiến Sao": {
    "en": "Strengthening & Advancing Stars",
    "ja": "スターの強化と進化",
    "cn": "强化和提升明星"
  },
  "Cường Hóa Cuốc &amp; Tiến Cấp Sao": {
    "en": "Enhance Pickaxe & Level Up Stars",
    "ja": "つるはしを強化してスターをレベルアップ",
    "cn": "增强镐和升级星星"
  },
  "Cường hóa cuốc &amp; cần câu 100% thành công": {
    "en": "Enhanced pickaxe & fishing rod 100% successful",
    "ja": "強化されたつるはしと釣り竿は100%成功しました",
    "cn": "增强型镐和钓鱼竿 100% 成功"
  },
  "Cảm ơn {user} đã nâng cấp máy chủ {server}! 💖": {
    "en": "Thank you {user} for upgrading your {server}! 💖",
    "ja": "{user} さん、{server} をアップグレードしていただきありがとうございます。 💖",
    "cn": "感谢 {user} 升级您的 {server}！ 💖"
  },
  "Cảm ơn {user} đã nâng cấp máy chủ {server}! 💖 Bạn đã nhận các đặc quyền xịn sò!": {
    "en": "Thank you {user} for upgrading your {server}! 💖 You have received great perks!",
    "ja": "{user} さん、{server} をアップグレードしていただきありがとうございます。 💖 素晴らしい特典を受け取りました！",
    "cn": "感谢 {user} 升级您的 {server}！ 💖 你已经获得了丰厚的福利！"
  },
  "Cấp cần câu thành công": {
    "en": "Successfully issued fishing rods",
    "ja": "釣り竿の発行に成功しました",
    "cn": "成功发放鱼竿"
  },
  "Cấp phát kinh tế thành công!": {
    "en": "Successful economic allocation!",
    "ja": "経済的配分に成功しました！",
    "cn": "经济分配成功！"
  },
  "Cấp refine phải từ 0 đến 150!": {
    "en": "Refine level must be from 0 to 150!",
    "ja": "精錬レベルは 0 ～ 150 である必要があります。",
    "cn": "精炼等级必须在0到150之间！"
  },
  "Cần câu cá": {
    "en": "Fishing rod",
    "ja": "釣り竿",
    "cn": "钓鱼竿"
  },
  "Cần đăng nhập để chat Global": {
    "en": "Need to log in to chat Global",
    "ja": "チャットするにはログインが必要です グローバル",
    "cn": "需要登录才能聊天 Global"
  },
  "Cầu Nối Trò Chuyện Trực Tuyến (Discord &lt;—&gt; Minecraft)": {
    "en": "Online Chat Bridge (Discord <—> Minecraft)",
    "ja": "オンライン チャット ブリッジ (Discord <—> Minecraft)",
    "cn": "在线聊天桥（Discord <—> Minecraft）"
  },
  "Cập nhật Level & XP thành công!": {
    "en": "Updated Level & XP successfully!",
    "ja": "レベルとXPが正常に更新されました!",
    "cn": "等级和经验值更新成功！"
  },
  "Cập nhật cần câu thành công!": {
    "en": "Fishing rod update successful!",
    "ja": "釣り竿のアップデートが成功しました！",
    "cn": "鱼竿更新成功！"
  },
  "Cập nhật hôn lễ thành công!": {
    "en": "Successful wedding update!",
    "ja": "結婚式更新成功！",
    "cn": "婚礼更新成功！"
  },
  "Cập nhật quyền thành công!": {
    "en": "Updated permissions successfully!",
    "ja": "権限が正常に更新されました。",
    "cn": "更新权限成功！"
  },
  "Cập nhật trạng thái thành công!": {
    "en": "Status update successful!",
    "ja": "ステータス更新に成功しました!",
    "cn": "状态更新成功！"
  },
  "Cập nhật vật phẩm cửa hàng thành công!": {
    "en": "Shop items updated successfully!",
    "ja": "ショップアイテムが正常に更新されました。",
    "cn": "商店商品更新成功！"
  },
  "Cập nhật vật phẩm thành công": {
    "en": "Item updated successfully",
    "ja": "アイテムは正常に更新されました",
    "cn": "项目更新成功"
  },
  "Cửa Hàng Thú Cưng": {
    "en": "Pet Store",
    "ja": "ペットショップ",
    "cn": "宠物店"
  },
  "Cửa sổ spam 1-120": {
    "en": "Spam window 1-120",
    "ja": "スパムウィンドウ 1-120",
    "cn": "垃圾邮件窗口 1-120"
  },
  "Discord: chưa kết nối": {
    "en": "Discord: not connected",
    "ja": "Discord:接続されていません",
    "cn": "不和谐：未连接"
  },
  "Discord: chưa kết nối (tách web)": {
    "en": "Discord: not connected (separated web)",
    "ja": "Discord: 接続されていません (別のウェブ)",
    "cn": "Discord：未连接（独立网络）"
  },
  "Giá Burn": {
    "en": "Burn Price",
    "ja": "バーン価格",
    "cn": "销毁价格"
  },
  "Giá bán không được âm": {
    "en": "Selling price cannot be negative",
    "ja": "販売価格をマイナスにすることはできません",
    "cn": "售价不能为负数"
  },
  "Hiển thị lại trong shop": {
    "en": "Displayed again in the shop",
    "ja": "再度店頭に展示しました",
    "cn": "再次在商店中展示"
  },
  "ID không hợp lệ (15-22 số)": {
    "en": "Invalid ID (15-22 numbers)",
    "ja": "無効な ID (15 ～ 22 桁の数字)",
    "cn": "ID 无效（15-22 位数字）"
  },
  "Không có": {
    "en": "No",
    "ja": "いいえ",
    "cn": "否"
  },
  "Không có mô tả": {
    "en": "No description available",
    "ja": "説明がありません",
    "cn": "无可用描述"
  },
  "Không có quà": {
    "en": "No gifts",
    "ja": "ギフトなし",
    "cn": "没有礼物"
  },
  "Không gửi được": {
    "en": "Unable to send",
    "ja": "送信できません",
    "cn": "无法发送"
  },
  "Không phân loại": {
    "en": "Not classified",
    "ja": "未分類",
    "cn": "未分类"
  },
  "Không phản hồi": {
    "en": "No response",
    "ja": "応答なし",
    "cn": "没有回应"
  },
  "Không phản hồi (timeout) - bot chưa chạy": {
    "en": "Unresponsive (timeout) - bot is not running yet",
    "ja": "応答なし (タイムアウト) - ボットはまだ実行されていません",
    "cn": "无响应（超时）- 机器人尚未运行"
  },
  "Không thể ping đến máy chủ": {
    "en": "Unable to ping the server",
    "ja": "サーバーに ping を送信できません",
    "cn": "无法 ping 通服务器"
  },
  "Không thể thiết lập môi trường": {
    "en": "Unable to set up environment",
    "ja": "環境をセットアップできません",
    "cn": "无法设置环境"
  },
  "Không thể tạo": {
    "en": "Cannot create",
    "ja": "作成できません",
    "cn": "无法创建"
  },
  "Không thể tải server": {
    "en": "Could not load server",
    "ja": "サーバーをロードできませんでした",
    "cn": "无法加载服务器"
  },
  "Không thể tải thông tin server": {
    "en": "Unable to load server information",
    "ja": "サーバー情報を読み込めません",
    "cn": "无法加载服务器信息"
  },
  "Không thể đăng panel Role": {
    "en": "Cannot post Role panel",
    "ja": "役割パネルを投稿できません",
    "cn": "无法发布角色面板"
  },
  "Không thể đăng panel Ticket": {
    "en": "Cannot post Ticket panel",
    "ja": "チケットパネルを投稿できません",
    "cn": "无法发布工单面板"
  },
  "Không thực thi được lệnh": {
    "en": "Unable to execute command",
    "ja": "コマンドを実行できません",
    "cn": "无法执行命令"
  },
  "Không tìm thấy dữ liệu cần thủ": {
    "en": "No angler data found",
    "ja": "釣り人データが見つかりません",
    "cn": "未找到垂钓者数据"
  },
  "Không tìm thấy dữ liệu nông trại": {
    "en": "No farm data found",
    "ja": "ファームデータが見つかりません",
    "cn": "未找到农场数据"
  },
  "Không tìm thấy người chơi": {
    "en": "Player not found",
    "ja": "プレーヤーが見つかりません",
    "cn": "未找到玩家"
  },
  "Không tìm thấy người dùng": {
    "en": "User not found",
    "ja": "ユーザーが見つかりません",
    "cn": "未找到用户"
  },
  "Không tìm thấy thông tin cần này": {
    "en": "This required information could not be found",
    "ja": "この必須情報が見つかりませんでした",
    "cn": "找不到所需的信息"
  },
  "Không tìm thấy thông tin cặp đôi": {
    "en": "No couple information found",
    "ja": "カップル情報は見つかりませんでした",
    "cn": "没有找到情侣信息"
  },
  "Không tìm thấy thông tin máy chủ": {
    "en": "Server information not found",
    "ja": "サーバー情報が見つかりません",
    "cn": "未找到服务器信息"
  },
  "Không tìm thấy vật phẩm": {
    "en": "Item not found",
    "ja": "アイテムが見つかりません",
    "cn": "未找到项目"
  },
  "Không tải được file": {
    "en": "Unable to download file",
    "ja": "ファイルをダウンロードできません",
    "cn": "无法下载文件"
  },
  "Không xác định được ID Server!": {
    "en": "Unable to determine Server ID!",
    "ja": "サーバー ID を特定できません!",
    "cn": "无法确定服务器 ID！"
  },
  "Không xác định được ID nhân vật, hãy chọn từ danh sách gợi ý": {
    "en": "Unable to determine character ID, choose from the suggestion list",
    "ja": "キャラクター ID を決定できません。候補リストから選択してください",
    "cn": "无法确定角色 ID，请从建议列表中选择"
  },
  "Khổng Lồ": {
    "en": "Giant",
    "ja": "巨人",
    "cn": "巨人"
  },
  "Khởi tạo giveaway thành công!": {
    "en": "Created giveaway successfully!",
    "ja": "プレゼントの作成に成功しました！",
    "cn": "赠品创建成功！"
  },
  "Kênh Chat 2 Chiều (Discord &lt;-&gt; MC):": {
    "en": "2-Way Chat Channel (Discord <-> MC):",
    "ja": "双方向チャットチャンネル (Discord <-> MC):",
    "cn": "2 向聊天频道（Discord <-> MC）："
  },
  "Kênh này đã có trong danh sách": {
    "en": "This channel is already in the list",
    "ja": "このチャンネルはすでにリストにあります",
    "cn": "该频道已在列表中"
  },
  "Kênh đã có": {
    "en": "Channel is available",
    "ja": "チャンネルが利用可能です",
    "cn": "频道可用"
  },
  "Kết nối bình thường": {
    "en": "Connect normally",
    "ja": "正常に接続します",
    "cn": "连接正常"
  },
  "Liên kết server Minecraft thành công!": {
    "en": "Linked to Minecraft server successfully!",
    "ja": "Minecraft サーバーに正常にリンクされました。",
    "cn": "已成功链接到 Minecraft 服务器！"
  },
  "Logs WebSocket đóng, tự động kết nối lại sau 3s...": {
    "en": "Logs WebSocket closes, automatically reconnects after 3 seconds...",
    "ja": "WebSocket が閉じ、3 秒後に自動的に再接続するログを記録します...",
    "cn": "日志 WebSocket 关闭，3 秒后自动重新连接..."
  },
  "Lưu cấu hình kênh thành công!": {
    "en": "Saved channel configuration successfully!",
    "ja": "チャンネル設定が正常に保存されました。",
    "cn": "通道配置保存成功！"
  },
  "Lưu vật phẩm mới thành công!": {
    "en": "New item saved successfully!",
    "ja": "新しいアイテムが正常に保存されました。",
    "cn": "新项目保存成功！"
  },
  "Lượt Thích (💖)": {
    "en": "Likes (💖)",
    "ja": "いいね (💖)",
    "cn": "喜欢(💖)"
  },
  "Lượt thích không hợp lệ!": {
    "en": "Invalid likes!",
    "ja": "無効ないいね！",
    "cn": "点赞无效！"
  },
  "Lệnh đã được gửi thành công.": {
    "en": "The command has been sent successfully.",
    "ja": "コマンドは正常に送信されました。",
    "cn": "命令已成功发送。"
  },
  "Lỗi cấp phát kinh tế": {
    "en": "Economic allocation error",
    "ja": "経済的配分の誤り",
    "cn": "经济分配错误"
  },
  "Lỗi cập nhật": {
    "en": "Update error",
    "ja": "アップデートエラー",
    "cn": "更新错误"
  },
  "Lỗi cập nhật quyền": {
    "en": "Error updating permissions",
    "ja": "権限の更新中にエラーが発生しました",
    "cn": "更新权限时出错"
  },
  "Lỗi cập nhật trạng thái Anti": {
    "en": "Error updating Anti status",
    "ja": "アンチステータスの更新中にエラーが発生しました",
    "cn": "更新反状态时出错"
  },
  "Lỗi cập nhật điểm": {
    "en": "Error updating points",
    "ja": "ポイント更新エラー",
    "cn": "更新点时出错"
  },
  "Lỗi gửi mã code": {
    "en": "Error sending code",
    "ja": "コード送信エラー",
    "cn": "发送代码时出错"
  },
  "Lỗi gửi test": {
    "en": "Error sending test",
    "ja": "テスト送信エラー",
    "cn": "发送测试时出错"
  },
  "Lỗi gửi test code DEMO": {
    "en": "Error sending test code DEMO",
    "ja": "テストコード DEMO の送信中にエラーが発生しました",
    "cn": "发送测试代码DEMO时出错"
  },
  "Lỗi gửi tin nhắn": {
    "en": "Error sending message",
    "ja": "メッセージ送信エラー",
    "cn": "发送消息时出错"
  },
  "Lỗi hủy liên kết": {
    "en": "Unlink error",
    "ja": "リンク解除エラー",
    "cn": "取消链接错误"
  },
  "Lỗi khi cập nhật hôn lễ": {
    "en": "Error updating wedding ceremony",
    "ja": "結婚式の更新中にエラーが発生しました",
    "cn": "更新婚礼时出错"
  },
  "Lỗi khi cập nhật vật phẩm": {
    "en": "Error updating items",
    "ja": "アイテム更新エラー",
    "cn": "更新项目时出错"
  },
  "Lỗi khi hủy hôn nhân": {
    "en": "Error when canceling marriage",
    "ja": "結婚キャンセル時のエラー",
    "cn": "取消婚姻时出错"
  },
  "Lỗi khi kết thúc giveaway": {
    "en": "Error when ending giveaway",
    "ja": "プレゼント終了時のエラー",
    "cn": "结束赠品时出错"
  },
  "Lỗi khi thay đổi trạng thái": {
    "en": "Error when changing status",
    "ja": "ステータス変更時のエラー",
    "cn": "更改状态时出错"
  },
  "Lỗi khi xóa giveaway": {
    "en": "Error deleting giveaway",
    "ja": "プレゼントの削除中にエラーが発生しました",
    "cn": "删除赠品时出错"
  },
  "Lỗi khôi phục backup": {
    "en": "Error restoring backup",
    "ja": "バックアップの復元中にエラーが発生しました",
    "cn": "恢复备份时出错"
  },
  "Lỗi khởi tạo giveaway": {
    "en": "Error initializing giveaway",
    "ja": "プレゼントの初期化中にエラーが発生しました",
    "cn": "初始化赠品时出错"
  },
  "Lỗi kiểm tra kết nối": {
    "en": "Connection check error",
    "ja": "接続チェックエラー",
    "cn": "连接检查错误"
  },
  "Lỗi kết nối": {
    "en": "Connection error",
    "ja": "接続エラー",
    "cn": "连接错误"
  },
  "Lỗi kết nối:": {
    "en": "Connection error:",
    "ja": "接続エラー:",
    "cn": "连接错误："
  },
  "Lỗi kết thúc giveaway": {
    "en": "Error ending giveaway",
    "ja": "プレゼント終了エラー",
    "cn": "结束赠品时出错"
  },
  "Lỗi liên kết server": {
    "en": "Server connection error",
    "ja": "サーバー接続エラー",
    "cn": "服务器连接错误"
  },
  "Lỗi lưu": {
    "en": "Save error",
    "ja": "保存エラー",
    "cn": "保存错误"
  },
  "Lỗi lưu Auto Role": {
    "en": "Error saving Auto Role",
    "ja": "自動役割の保存中にエラーが発生しました",
    "cn": "保存自动角色时出错"
  },
  "Lỗi lưu Custom Key": {
    "en": "Error saving Custom Key",
    "ja": "カスタムキーの保存中にエラーが発生しました",
    "cn": "保存自定义密钥时出错"
  },
  "Lỗi lưu cài đặt": {
    "en": "Error saving settings",
    "ja": "設定の保存中にエラーが発生しました",
    "cn": "保存设置时出错"
  },
  "Lỗi lưu cấu hình": {
    "en": "Error saving configuration",
    "ja": "構成の保存中にエラーが発生しました",
    "cn": "保存配置时出错"
  },
  "Lỗi lưu cấu hình Hoyo Codes": {
    "en": "Error saving Hoyo Codes configuration",
    "ja": "Hoyo コード設定の保存中にエラーが発生しました",
    "cn": "保存 Hoyo 代码配置时出错"
  },
  "Lỗi lưu cấu hình Kênh Nội Quy": {
    "en": "Error saving Channel Rules configuration",
    "ja": "チャネル ルール設定の保存中にエラーが発生しました",
    "cn": "保存通道规则配置时出错"
  },
  "Lỗi lưu cấu hình Kênh Streak": {
    "en": "Error saving Streak Channel configuration",
    "ja": "ストリーク チャネル構成の保存中にエラーが発生しました",
    "cn": "保存 Streak Channel 配置时出错"
  },
  "Lỗi lưu cấu hình MiniGame": {
    "en": "Error saving MiniGame configuration",
    "ja": "ミニゲーム設定の保存中にエラーが発生しました",
    "cn": "保存小游戏配置时出错"
  },
  "Lỗi lưu cấu hình RCON": {
    "en": "Error saving RCON configuration",
    "ja": "RCON 構成の保存中にエラーが発生しました",
    "cn": "保存 RCON 配置时出错"
  },
  "Lỗi lưu cấu hình câu cá": {
    "en": "Error saving fishing configuration",
    "ja": "フィッシング設定の保存中にエラーが発生しました",
    "cn": "保存钓鱼配置时出错"
  },
  "Lỗi lưu cấu hình kênh": {
    "en": "Error saving channel configuration",
    "ja": "チャネル構成の保存中にエラーが発生しました",
    "cn": "保存通道配置时出错"
  },
  "Lỗi lưu cấu hình panel": {
    "en": "Error saving panel configuration",
    "ja": "パネル構成の保存中にエラーが発生しました",
    "cn": "保存面板配置时出错"
  },
  "Lỗi lưu cấu hình tỉ lệ": {
    "en": "Error saving scale configuration",
    "ja": "スケール設定の保存中にエラーが発生しました",
    "cn": "保存秤配置时出错"
  },
  "Lỗi lưu file": {
    "en": "Error saving file",
    "ja": "ファイルの保存中にエラーが発生しました",
    "cn": "保存文件时出错"
  },
  "Lỗi lưu hồ sơ bot": {
    "en": "Error saving bot profile",
    "ja": "ボット プロファイルの保存中にエラーが発生しました",
    "cn": "保存机器人配置文件时出错"
  },
  "Lỗi lưu vật phẩm": {
    "en": "Error saving items",
    "ja": "アイテムの保存中にエラーが発生しました",
    "cn": "保存项目时出错"
  },
  "Lỗi máy chủ": {
    "en": "Server error",
    "ja": "サーバーエラー",
    "cn": "服务器错误"
  },
  "Lỗi mạng:": {
    "en": "Network error:",
    "ja": "ネットワークエラー:",
    "cn": "网络错误："
  },
  "Lỗi parse log WS:": {
    "en": "WS log parse error:",
    "ja": "WS ログ解析エラー:",
    "cn": "WS日志解析错误："
  },
  "Lỗi test": {
    "en": "Test error",
    "ja": "テストエラー",
    "cn": "测试错误"
  },
  "Lỗi thao tác": {
    "en": "Operation error",
    "ja": "操作ミス",
    "cn": "操作错误"
  },
  "Lỗi thao tác Claim": {
    "en": "Claim operation error",
    "ja": "クレーム操作エラー",
    "cn": "索赔操作错误"
  },
  "Lỗi thao tác Roll": {
    "en": "Roll operation error",
    "ja": "ロール操作エラー",
    "cn": "卷筒操作错误"
  },
  "Lỗi thu hồi Admin": {
    "en": "Admin recall error",
    "ja": "管理者のリコールエラー",
    "cn": "管理员召回错误"
  },
  "Lỗi thêm Admin": {
    "en": "Error adding Admin",
    "ja": "管理者の追加エラー",
    "cn": "添加管理员时出错"
  },
  "Lỗi thêm mốc role": {
    "en": "Error adding role landmark",
    "ja": "ロールランドマークの追加中にエラーが発生しました",
    "cn": "添加角色地标时出错"
  },
  "Lỗi thêm từ": {
    "en": "Error adding words",
    "ja": "単語の追加中にエラーが発生しました",
    "cn": "添加单词时出错"
  },
  "Lỗi thực hiện thao tác": {
    "en": "Error performing operation",
    "ja": "操作実行中にエラーが発生しました",
    "cn": "执行操作时出错"
  },
  "Lỗi trao thẻ": {
    "en": "Error giving card",
    "ja": "カード付与エラー",
    "cn": "发卡时出错"
  },
  "Lỗi tạo Giveaway": {
    "en": "Error creating Giveaway",
    "ja": "プレゼント作成エラー",
    "cn": "创建赠品时出错"
  },
  "Lỗi tạo bản sao lưu": {
    "en": "Error creating backup",
    "ja": "バックアップ作成エラー",
    "cn": "创建备份时出错"
  },
  "Lỗi tạo bảng Reaction Role": {
    "en": "Error creating Reaction Role table",
    "ja": "リアクションロールテーブルの作成中にエラーが発生しました",
    "cn": "创建反应角色表时出错"
  },
  "Lỗi tạo giftcode": {
    "en": "Error generating giftcode",
    "ja": "ギフトコード生成エラー",
    "cn": "生成礼品码时出错"
  },
  "Lỗi tạo vật phẩm": {
    "en": "Error creating item",
    "ja": "アイテム作成エラー",
    "cn": "创建项目时出错"
  },
  "Lỗi tải": {
    "en": "Loading error",
    "ja": "読み込みエラー",
    "cn": "加载错误"
  },
  "Lỗi tải BXH Thành Tựu": {
    "en": "Error loading the Achievement Chart",
    "ja": "実績チャートのロード中にエラーが発生しました",
    "cn": "加载成就图表时出错"
  },
  "Lỗi tải Custom Keys": {
    "en": "Error loading Custom Keys",
    "ja": "カスタムキーの読み込みエラー",
    "cn": "加载自定义键时出错"
  },
  "Lỗi tải Daily Giftcode:": {
    "en": "Error downloading Daily Giftcode:",
    "ja": "デイリー ギフトコードのダウンロード中にエラーが発生しました:",
    "cn": "下载每日礼品代码时出错："
  },
  "Lỗi tải Giveaway": {
    "en": "Error loading Giveaway",
    "ja": "プレゼントの読み込みエラー",
    "cn": "加载赠品时出错"
  },
  "Lỗi tải Global Chat": {
    "en": "Error loading Global Chat",
    "ja": "グローバル チャットの読み込みエラー",
    "cn": "加载全局聊天时出错"
  },
  "Lỗi tải danh mục khoáng": {
    "en": "Error loading mineral list",
    "ja": "鉱物リストの読み込みエラー",
    "cn": "加载矿物列表时出错"
  },
  "Lỗi tải danh mục thành tựu": {
    "en": "Error loading achievement list",
    "ja": "実績リストの読み込みエラー",
    "cn": "加载成就列表时出错"
  },
  "Lỗi tải danh sách": {
    "en": "Error loading list",
    "ja": "リストのロード中にエラーが発生しました",
    "cn": "加载列表时出错"
  },
  "Lỗi tải danh sách Thủy Cung": {
    "en": "Error loading Aquarium list",
    "ja": "水族館リストの読み込みエラー",
    "cn": "加载水族馆列表时出错"
  },
  "Lỗi tải danh sách backup": {
    "en": "Error loading backup list",
    "ja": "バックアップ リストのロード中にエラーが発生しました",
    "cn": "加载备份列表时出错"
  },
  "Lỗi tải danh sách cửa hàng": {
    "en": "Error loading store list",
    "ja": "ストアリストの読み込みエラー",
    "cn": "加载商店列表时出错"
  },
  "Lỗi tải danh sách hôn lễ": {
    "en": "Error loading wedding list",
    "ja": "結婚式リストの読み込みエラー",
    "cn": "加载婚礼列表时出错"
  },
  "Lỗi tải danh sách mốc role": {
    "en": "Error loading list of role milestones",
    "ja": "役割マイルストーンのリストの読み込みエラー",
    "cn": "加载角色里程碑列表时出错"
  },
  "Lỗi tải danh sách server Minecraft": {
    "en": "Error loading Minecraft server list",
    "ja": "Minecraft サーバー リストの読み込みエラー",
    "cn": "加载 Minecraft 服务器列表时出错"
  },
  "Lỗi tải stats Gacha": {
    "en": "Error loading Gacha stats",
    "ja": "ガチャ統計の読み込みエラー",
    "cn": "加载扭蛋统计数据时出错"
  },
  "Lỗi xóa Custom Key": {
    "en": "Error deleting Custom Key",
    "ja": "カスタムキーの削除エラー",
    "cn": "删除自定义密钥时出错"
  },
  "Lỗi xóa bản sao lưu": {
    "en": "Error deleting backup",
    "ja": "バックアップの削除中にエラーが発生しました",
    "cn": "删除备份时出错"
  },
  "Lỗi xóa bảng": {
    "en": "Error deleting table",
    "ja": "テーブルの削除中にエラーが発生しました",
    "cn": "删除表时出错"
  },
  "Lỗi xóa mốc role": {
    "en": "Error deleting role landmark",
    "ja": "ロールランドマークの削除中にエラーが発生しました",
    "cn": "删除角色地标时出错"
  },
  "Lỗi xóa thẻ": {
    "en": "Error deleting card",
    "ja": "カード削除エラー",
    "cn": "删除卡时出错"
  },
  "Lỗi xóa từ": {
    "en": "Error deleting words",
    "ja": "単語の削除中にエラーが発生しました",
    "cn": "删除单词时出错"
  },
  "Lỗi xóa vật phẩm": {
    "en": "Error deleting items",
    "ja": "アイテムの削除中にエラーが発生しました",
    "cn": "删除项目时出错"
  },
  "Lỗi đăng bảng nội quy": {
    "en": "Error posting rules board",
    "ja": "ルール掲示板の投稿エラー",
    "cn": "发布规则板时出错"
  },
  "Lỗi đổi sao": {
    "en": "Change error",
    "ja": "変更エラー",
    "cn": "更改错误"
  },
  "Lỗi:": {
    "en": "Error:",
    "ja": "エラー:",
    "cn": "错误："
  },
  "Lỗi: ${escapeHtml(data.error)}": {
    "en": "Error: ${escapeHtml(data.error)}",
    "ja": "エラー: ${escapeHtml(data.error)}",
    "cn": "错误：${escapeHtml(data.error)}"
  },
  "Mã Thẻ": {
    "en": "Card Code",
    "ja": "カードコード",
    "cn": "卡代码"
  },
  "Mã không hợp lệ hoặc đã hết hạn": {
    "en": "Code is invalid or expired",
    "ja": "コードが無効か期限切れです",
    "cn": "代码无效或已过期"
  },
  "Mô Tả Nhiệm Vụ": {
    "en": "Task Description",
    "ja": "タスクの説明",
    "cn": "任务描述"
  },
  "Mật khẩu sai!": {
    "en": "Wrong password!",
    "ja": "パスワードが間違っています!",
    "cn": "密码错误！"
  },
  "Mồi câu chuyên dụng tăng tỷ lệ cắn câu hiếm": {
    "en": "Specialized bait increases the bite rate of rare fish",
    "ja": "特殊な餌で珍しい魚のバイト率を高めます",
    "cn": "专用饵料提高稀有鱼类的咬合率"
  },
  "Mở Console": {
    "en": "Open Console",
    "ja": "コンソールを開く",
    "cn": "打开控制台"
  },
  "Mở chat": {
    "en": "Open chat",
    "ja": "オープンチャット",
    "cn": "打开聊天室"
  },
  "Mở rương / Quà tặng": {
    "en": "Open chests/Gifts",
    "ja": "開いたチェスト/ギフト",
    "cn": "打开宝箱/礼物"
  },
  "Người dùng thông thường cần vote trên Top.gg để mở khóa các lệnh VIP trong 12h.": {
    "en": "Regular users need to vote on Top.gg to unlock VIP orders for 12 hours.",
    "ja": "一般ユーザーが 12 時間 VIP オーダーのロックを解除するには、Top.gg で投票する必要があります。",
    "cn": "普通用户需要在Top.gg上投票才能解锁12小时的VIP订单。"
  },
  "Ngưỡng spam 2-50": {
    "en": "Spam threshold 2-50",
    "ja": "スパムしきい値 2 ～ 50",
    "cn": "垃圾邮件阈值 2-50"
  },
  "Ngừng sinh trưởng": {
    "en": "Stop growing",
    "ja": "成長を止める",
    "cn": "停止生长"
  },
  "Ngừng sinh trưởng & khô cằn": {
    "en": "Stop growing & dry out",
    "ja": "成長を止めて乾燥させる",
    "cn": "停止生长并变干"
  },
  "Nhân Vật": {
    "en": "Character",
    "ja": "キャラクター",
    "cn": "性格"
  },
  "Nhấn để sao chép": {
    "en": "Click to copy",
    "ja": "クリックしてコピー",
    "cn": "点击复制"
  },
  "Nhẫn Cỏ": {
    "en": "Grass Ring",
    "ja": "グラスリング",
    "cn": "草环"
  },
  "Nhập Discord User ID (VD: 1144785664458637394)...": {
    "en": "Enter Discord User ID (Example: 1144785664458637394)...",
    "ja": "Discord ユーザー ID を入力してください (例: 1144785664458637394)...",
    "cn": "输入 Discord 用户 ID（示例：1144785664458637394）..."
  },
  "Nhập ID Cuốc muốn cấp (ví dụ: pick_wooden, pick_iron, pick_diamond, pick_netherite, pick_sakura):": {
    "en": "Enter the Pick ID you want to grant (eg pick_wooden, pick_iron, pick_diamond, pick_netherite, pick_sakura):",
    "ja": "付与する Pick ID を入力します (例: pick_wooden、pick_iron、pick_diamond、pick_netherite、pick_sakura):",
    "cn": "输入您想要授予的 Pick ID（例如 pick_wooden、pick_iron、pick_diamond、pick_netherite、pick_sakura）："
  },
  "Nhập ID Quặng (ví dụ: stone, iron, gold, diamond, netherite, ruby, amethyste, emerald):": {
    "en": "Enter the Ore ID (e.g. stone, iron, gold, diamond, netherite, ruby, amethyste, emerald):",
    "ja": "鉱石 ID (例: 石、鉄、金、ダイヤモンド、ネザライト、ルビー、アメジスト、エメラルド) を入力します。",
    "cn": "输入矿石 ID（例如石头、铁、金、钻石、下界合金、红宝石、紫水晶、祖母绿）："
  },
  "Nhập ID Vật tư (ví dụ: bomb, tnt, stamina_pot, drill, lucky_charm):": {
    "en": "Enter the Supplies ID (e.g. bomb, tnt, stamina_pot, drill, lucky_charm):",
    "ja": "サプライ ID を入力します (例: Bomb、TNT、stamin_pot、drill、lucky_charm):",
    "cn": "输入补给 ID（例如炸弹、tnt、stamina_pot、drill、lucky_charm）："
  },
  "Nhập ID hợp lệ": {
    "en": "Enter a valid ID",
    "ja": "有効なIDを入力してください",
    "cn": "输入有效身份证件"
  },
  "Nhập chiều dài (cm):": {
    "en": "Enter length (cm):",
    "ja": "長さ (cm) を入力してください:",
    "cn": "输入长度（厘米）："
  },
  "Nhập cân nặng (kg):": {
    "en": "Enter weight (kg):",
    "ja": "体重 (kg) を入力してください:",
    "cn": "输入体重（公斤）："
  },
  "Nhập cấp Cường Hóa mới (0 - 150):": {
    "en": "Enter new Enhance level (0 - 150):",
    "ja": "新しい強化レベルを入力してください (0 ～ 150):",
    "cn": "输入新的增强级别（0 - 150）："
  },
  "Nhập giá trị quy đổi Coins:": {
    "en": "Enter the Coins conversion value:",
    "ja": "コイン換算値を入力します:",
    "cn": "输入金币兑换值："
  },
  "Nhập mô tả / ghi chú cho bản sao lưu:": {
    "en": "Enter a description/note for the backup:",
    "ja": "バックアップの説明/メモを入力します。",
    "cn": "输入备份的描述/注释："
  },
  "Nhập số Sao mới (0 - 20 ⭐):": {
    "en": "Enter the new number of Stars (0 - 20 ⭐):",
    "ja": "新しい星の数を入力します (0 ～ 20 ⭐):",
    "cn": "输入新的星星数量（0 - 20 ⭐）："
  },
  "Nhập số lượng quặng muốn thêm:": {
    "en": "Enter the amount of ore you want to add:",
    "ja": "追加する鉱石の量を入力します。",
    "cn": "输入您要添加的矿石量："
  },
  "Nhập số lượng vật tư:": {
    "en": "Enter quantity of materials:",
    "ja": "材料の数量を入力してください:",
    "cn": "输入材料数量："
  },
  "Nhập số lượt thích mới cho Thủy Cung:": {
    "en": "Enter the number of new likes for Aquarium:",
    "ja": "Aquarium の新しい「いいね!」の数を入力してください:",
    "cn": "输入《水族馆》的新点赞数："
  },
  "Nhập số ô chứa tối đa cho Thủy Cung (1 - 100 ô):": {
    "en": "Enter the maximum number of cells for the Aquarium (1 - 100 cells):",
    "ja": "水族館の最大セル数を入力します (1 ～ 100 セル)。",
    "cn": "输入水族箱的最大单元数（1 - 100 个单元）："
  },
  "Nhập số ô chứa tối đa mới của Thủy Cung (1 - 100 ô):": {
    "en": "Enter the Aquarium's new maximum number of slots (1 - 100 slots):",
    "ja": "水族館の新しい最大スロット数 (1 ～ 100 スロット) を入力します。",
    "cn": "输入水族馆新的最大槽位数（1 - 100 个槽位）："
  },
  "Nhập tin nhắn Global... (cần login)": {
    "en": "Enter message Global... (login required)",
    "ja": "メッセージを入力してください グローバル... (ログインが必要です)",
    "cn": "输入消息 Global...（需要登录）"
  },
  "Nhập tin nhắn Sakura AI...": {
    "en": "Enter Sakura AI message...",
    "ja": "さくら AI メッセージを入力してください...",
    "cn": "输入樱花AI信息..."
  },
  "Nhập tên loài cá muốn thả vào Thủy Cung:": {
    "en": "Enter the name of the fish you want to release into the Aquarium:",
    "ja": "水族館に放したい魚の名前を入力してください:",
    "cn": "输入您想要放入水族馆的鱼的名称："
  },
  "Nhập độ hiếm (common, rare, epic, legendary, admin):": {
    "en": "Enter rarity (common, rare, epic, legendary, admin):",
    "ja": "レアリティ (コモン、レア、エピック、レジェンド、管理者) を入力します:",
    "cn": "输入稀有度（常见、稀有、史诗、传奇、管理员）："
  },
  "Nông trại: ${u.farm_crops} nông sản": {
    "en": "Farm: ${u.farm_crops} agricultural products",
    "ja": "農場: ${u.farm_crops} の農産物",
    "cn": "农场：${u.farm_crops}农产品"
  },
  "Nạp lại Cog": {
    "en": "Reload Cog",
    "ja": "Reload Cog",
    "cn": "重新加载齿轮"
  },
  "Nội dung file không được để trống!": {
    "en": "File content cannot be empty!",
    "ja": "ファイルの内容を空にすることはできません。",
    "cn": "文件内容不能为空！"
  },
  "Phát Daily Giftcode thành công!": {
    "en": "Distribute Daily Giftcode successfully!",
    "ja": "デイリーギフトコードの配布に成功しました!",
    "cn": "每日礼品码发放成功！"
  },
  "Phải bật ít nhất 1 kiểu (Công khai hoặc Ẩn danh)": {
    "en": "Must have at least 1 type enabled (Public or Anonymous)",
    "ja": "少なくとも 1 つのタイプを有効にする必要があります (パブリックまたは匿名)",
    "cn": "必须至少启用 1 种类型（公开或匿名）"
  },
  "Prefix 1-5 ký tự": {
    "en": "Prefix 1-5 characters",
    "ja": "Prefix 1-5 characters",
    "cn": "前缀 1-5 个字符"
  },
  "Print # (tùy chọn)": {
    "en": "Print # (optional)",
    "ja": "Print # (optional)",
    "cn": "打印#（可选）"
  },
  "Quà tặng trong game": {
    "en": "In-game gifts",
    "ja": "In-game gifts",
    "cn": "游戏内礼物"
  },
  "Quản lý File": {
    "en": "File Management",
    "ja": "ファイル管理",
    "cn": "文件管理"
  },
  "Quản trị viên hệ thống": {
    "en": "System administrator",
    "ja": "System administrator",
    "cn": "系统管理员"
  },
  "Regex lỗi:": {
    "en": "Regex error:",
    "ja": "Regex error:",
    "cn": "正则表达式错误："
  },
  "Rương / Sự kiện": {
    "en": "Chests / Events",
    "ja": "Chests / Events",
    "cn": "宝箱/活动"
  },
  "Rương Hỗn Loạn / Drop hiếm": {
    "en": "Rare Chaos Chest / Drop",
    "ja": "Rare Chaos Chest / Drop",
    "cn": "稀有混沌宝箱 / 掉落"
  },
  "Rương báu bí mật!": {
    "en": "Secret treasure chest!",
    "ja": "Secret treasure chest!",
    "cn": "秘密宝箱！"
  },
  "Rương kho báu chứa mồi, vật phẩm và pet quý": {
    "en": "Treasure chests contain bait, items and precious pets",
    "ja": "宝箱には餌、アイテム、大切なペットが入っています",
    "cn": "宝箱里有诱饵、物品和珍贵的宠物"
  },
  "Sakura Bot • Chúc bạn có những phút giây vui vẻ!": {
    "en": "Sakura Bot • Wish you have fun moments!",
    "ja": "さくらボット • 楽しいひとときをお過ごしください。",
    "cn": "Sakura Bot •祝您度过愉快的时光！"
  },
  "Server không phản hồi": {
    "en": "Server is not responding",
    "ja": "サーバーが応答していません",
    "cn": "服务器没有响应"
  },
  "Shop Cần Câu": {
    "en": "Can Cau Shop",
    "ja": "カンカウショップ",
    "cn": "芹菜店"
  },
  "Shop Mồi Câu": {
    "en": "Fishing Bait Shop",
    "ja": "釣り餌店",
    "cn": "鱼饵店"
  },
  "Shop Đồ Chơi": {
    "en": "Toy Shop",
    "ja": "おもちゃ屋",
    "cn": "玩具店"
  },
  "Sinh vật biển hoang dã": {
    "en": "Wild marine life",
    "ja": "野生の海洋生物",
    "cn": "野生海洋生物"
  },
  "Sản Lượng &amp; Độ Hiếm Quặng": {
    "en": "Ore Production & Rarity",
    "ja": "鉱石の生産量と希少性",
    "cn": "矿石产量和稀有度"
  },
  "Số Coin / %:": {
    "en": "Number of Coins / %:",
    "ja": "コイン数 / %:",
    "cn": "硬币数量/%："
  },
  "Số lần câu bị nguyền:": {
    "en": "Number of times the sentence was cursed:",
    "ja": "文が呪われた回数:",
    "cn": "被咒骂的次数："
  },
  "Số phút hiệu lực (VD: 10)": {
    "en": "Number of minutes of validity (Example: 10)",
    "ja": "有効時間分（例：10）",
    "cn": "有效分钟数（示例：10）"
  },
  "Số sao phải từ 0 đến 20!": {
    "en": "The number of stars must be from 0 to 20!",
    "ja": "星の数は 0 ～ 20 である必要があります。",
    "cn": "星星数量必须在0到20之间！"
  },
  "Số sao phải từ 1 đến 5": {
    "en": "The number of stars must be from 1 to 5",
    "ja": "星の数は 1 ～ 5 でなければなりません",
    "cn": "星星数量必须为 1 到 5"
  },
  "Số ô phải từ 1 đến 100!": {
    "en": "The number of cells must be from 1 to 100!",
    "ja": "セルの数は 1 ～ 100 でなければなりません。",
    "cn": "单元格数量必须在 1 到 100 之间！"
  },
  "Số ô đất phải nằm trong khoảng từ 4 đến 16": {
    "en": "The number of plots must be between 4 and 16",
    "ja": "プロットの数は 4 ～ 16 でなければなりません",
    "cn": "地块数量必须在 4 到 16 之间"
  },
  "Số điểm không hợp lệ": {
    "en": "Invalid points",
    "ja": "無効なポイント",
    "cn": "无效积分"
  },
  "Sự cố": {
    "en": "Incident",
    "ja": "事件",
    "cn": "事件"
  },
  "Tham số / Thông điệp:": {
    "en": "Parameter/Message:",
    "ja": "パラメータ/メッセージ:",
    "cn": "参数/消息："
  },
  "Thao Túng Tỉ Lệ Khai Thác Mỏ &amp; Cường Hóa Cuốc": {
    "en": "Manipulate Mining Rate & Enhance Pickaxe",
    "ja": "採掘速度を操作し、つるはしを強化する",
    "cn": "操纵采矿率并增强镐"
  },
  "Thao tác thành công": {
    "en": "Operation successful",
    "ja": "操作は成功しました",
    "cn": "操作成功"
  },
  "Thao tác thất bại": {
    "en": "Operation failed",
    "ja": "操作が失敗しました",
    "cn": "操作失败"
  },
  "Thiết lập ô đất thành công": {
    "en": "Set up the plot successfully",
    "ja": "プロットを正常にセットアップする",
    "cn": "情节设置成功"
  },
  "Thiếu ID cần": {
    "en": "Missing required ID",
    "ja": "必要なIDがありません",
    "cn": "缺少所需的 ID"
  },
  "Thiếu server ID": {
    "en": "Missing server ID",
    "ja": "サーバーIDがありません",
    "cn": "缺少服务器 ID"
  },
  "Thiếu server để lưu": {
    "en": "Lack of server to save",
    "ja": "保存するサーバーが不足しています",
    "cn": "缺少服务器来保存"
  },
  "Thiếu server để đăng panel": {
    "en": "Lack of server to post panels",
    "ja": "パネルを投稿するサーバーが不足している",
    "cn": "缺乏服务器来发布面板"
  },
  "Thu hồi cần thành công": {
    "en": "Recall needs to be successful",
    "ja": "リコールを成功させる必要がある",
    "cn": "召回必须成功"
  },
  "Thánh Câu Cóc": {
    "en": "Saint Coc",
    "ja": "サンコック",
    "cn": "圣科克"
  },
  "Thêm Thú Cưng thành công!": {
    "en": "Added Pet successfully!",
    "ja": "ペットの追加に成功しました!",
    "cn": "添加宠物成功！"
  },
  "Thêm cá mới thành công!": {
    "en": "Added new fish successfully!",
    "ja": "新しい魚の追加に成功しました！",
    "cn": "添加新鱼成功！"
  },
  "Thêm cá thành công": {
    "en": "Added fish successfully",
    "ja": "魚の追加に成功しました",
    "cn": "添加鱼成功"
  },
  "Thêm cần câu mới thành công!": {
    "en": "Added new fishing rod successfully!",
    "ja": "新しい釣り竿が無事追加されました！",
    "cn": "添加新鱼竿成功！"
  },
  "Thêm mồi câu mới thành công!": {
    "en": "Successfully added new bait!",
    "ja": "新しい餌の追加に成功しました！",
    "cn": "添加新诱饵成功！"
  },
  "Thêm túi mới thành công!": {
    "en": "Added new bag successfully!",
    "ja": "新しいバッグが正常に追加されました。",
    "cn": "添加新包成功！"
  },
  "Thêm vật phẩm troll thành công!": {
    "en": "Added troll item successfully!",
    "ja": "トロールアイテムの追加に成功しました！",
    "cn": "添加巨魔物品成功！"
  },
  "Thú cưng trợ thủ đắc lực bên cần thủ": {
    "en": "Pets are effective assistants to anglers",
    "ja": "ペットは釣り人の効果的なアシスタントです",
    "cn": "宠物是钓鱼者的得力助手"
  },
  "Thần Thoại": {
    "en": "Mythology",
    "ja": "神話",
    "cn": "神话"
  },
  "Thắng": {
    "en": "Win",
    "ja": "勝つ",
    "cn": "赢"
  },
  "Thực hiện thành công!": {
    "en": "Done successfully!",
    "ja": "無事完了しました！",
    "cn": "成功完成！"
  },
  "Thực thi lệnh thất bại": {
    "en": "Command execution failed",
    "ja": "コマンドの実行に失敗しました",
    "cn": "命令执行失败"
  },
  "Tiêu Chuẩn": {
    "en": "Standard",
    "ja": "標準",
    "cn": "标准型"
  },
  "Tiêu đề nút (vd: Tham Gia Discord)": {
    "en": "Button title (e.g. Join Discord)",
    "ja": "ボタンのタイトル (例: Discord に参加)",
    "cn": "按钮标题（例如加入 Discord）"
  },
  "Tiến trình khôi phục đang chạy ngầm": {
    "en": "The restore process is running in the background",
    "ja": "復元プロセスがバックグラウンドで実行されています",
    "cn": "恢复过程在后台运行"
  },
  "To Lớn": {
    "en": "Big Big",
    "ja": "ビッグビッグ",
    "cn": "大大大"
  },
  "Tra cứu thành công!": {
    "en": "Lookup successful!",
    "ja": "検索が成功しました!",
    "cn": "查找成功！"
  },
  "Trao thẻ thành công!": {
    "en": "Card awarded successfully!",
    "ja": "無事にカードが授与されました！",
    "cn": "发卡成功！"
  },
  "Trực tuyến": {
    "en": "Online",
    "ja": "オンライン",
    "cn": "在线"
  },
  "Tài khoản chưa có Discord ID liên kết": {
    "en": "The account does not have an associated Discord ID",
    "ja": "アカウントに関連付けられた Discord ID がありません",
    "cn": "该帐户没有关联的 Discord ID"
  },
  "Tác Phẩm": {
    "en": "Works",
    "ja": "作品",
    "cn": "作品"
  },
  "Tên Gốc": {
    "en": "Original Name",
    "ja": "元の名前",
    "cn": "原名"
  },
  "Tên Nhân Vật": {
    "en": "Character Name",
    "ja": "キャラクター名",
    "cn": "角色名称"
  },
  "Tên đặt cho nạn nhân": {
    "en": "Name given to the victim",
    "ja": "被害者に与えられた名前",
    "cn": "Name given to the victim"
  },
  "Tùy biến tỉ lệ đập đồ (+1..+150), tiến sao (1..20 ⭐), may mắn câu cá &amp; đào mỏ trực tiếp theo thời gian thực.": {
    "en": "Customize loot rate (+1..+150), earn stars (1..20 ⭐), fishing & mining luck directly in real time.",
    "ja": "略奪率 (+1..+150) をカスタマイズし、スター (1..20 ⭐) を獲得し、釣りと採掘の運をリアルタイムで直接カスタマイズします。",
    "cn": "自定义战利品率（+1..+150），赚取星星（1..20⭐），直接实时钓鱼和采矿运气。"
  },
  "Tùy chọn": {
    "en": "Options",
    "ja": "オプション",
    "cn": "选项"
  },
  "Tạm biệt {user} 👋 Hẹn gặp lại một ngày không xa!": {
    "en": "Goodbye {user} 👋 See you again one day soon!",
    "ja": "さようなら {user} 👋 またいつかお会いしましょう!",
    "cn": "再见{用户} 👋 很快有一天再见！"
  },
  "Tạo giftcode thành công!": {
    "en": "Create giftcode successfully!",
    "ja": "ギフトコードの作成に成功しました。",
    "cn": "创建礼品码成功！"
  },
  "Tạo link tham gia server": {
    "en": "Create a link to join the server",
    "ja": "サーバーに参加するためのリンクを作成します",
    "cn": "创建链接以加入服务器"
  },
  "Tạo rương báu mới thành công!": {
    "en": "Successfully created a new treasure chest!",
    "ja": "新しい宝箱の作成に成功しました！",
    "cn": "成功创建新宝箱！"
  },
  "Tạo thành tựu thành công!": {
    "en": "Create successful achievements!",
    "ja": "成功した実績を作りましょう！",
    "cn": "创造成功的业绩！"
  },
  "Tạo đột biến thành công": {
    "en": "Successfully created mutations",
    "ja": "突然変異が正常に作成されました",
    "cn": "成功创建突变"
  },
  "Tỉ lệ xuất hiện phải lớn hơn 0": {
    "en": "The occurrence rate must be greater than 0",
    "ja": "発生率は 0 より大きくなければなりません",
    "cn": "出现率必须大于0"
  },
  "Tối đa 200 từ": {
    "en": "Maximum 200 words",
    "ja": "最大200ワード",
    "cn": "Maximum 200 words"
  },
  "Từ Web": {
    "en": "From the Web",
    "ja": "ウェブから",
    "cn": "来自网络"
  },
  "Từ vựng phải gồm đúng 2 âm tiết (vd: hoa hồng, nhà cửa)": {
    "en": "Vocabulary must contain exactly 2 syllables (eg: rose, house)",
    "ja": "語彙には正確に 2 音節が含まれている必要があります (例: ローズ、ハウス)",
    "cn": "词汇必须恰好包含 2 个音节（例如：rose、house）"
  },
  "VD: 15000 hoặc 20%": {
    "en": "Example: 15000 or 20%",
    "ja": "例: 15000 または 20%",
    "cn": "Example: 15000 or 20%"
  },
  "VD: 8 ký tự trở lên và &gt;70% là hoa → xóa.": {
    "en": "For example: 8 characters or more and >70% are capital letters → delete.",
    "ja": "例: 8 文字以上かつ 70% 以上が大文字 → 削除。",
    "cn": "例如：8个字符或更多且>70%为大写字母→删除。"
  },
  "Video tiếp theo": {
    "en": "Next video",
    "ja": "次のビデオ",
    "cn": "下一个视频"
  },
  "Vui lòng chọn 1 kênh để thêm": {
    "en": "Please select a channel to add",
    "ja": "追加するチャンネルを選択してください",
    "cn": "请选择要添加的频道"
  },
  "Vui lòng chọn Discord Server trước!": {
    "en": "Please select Discord Server first!",
    "ja": "まずDiscordサーバーを選択してください。",
    "cn": "请先选择Discord服务器！"
  },
  "Vui lòng chọn Discord Server để gán kết nối RCON!": {
    "en": "Please select Discord Server to assign RCON connection!",
    "ja": "RCON 接続を割り当てるには Discord サーバーを選択してください。",
    "cn": "请选择Discord Server来分配RCON连接！"
  },
  "Vui lòng chọn Discord Server để liên kết!": {
    "en": "Please select Discord Server to link!",
    "ja": "リンクする Discord サーバーを選択してください。",
    "cn": "请选择Discord Server进行链接！"
  },
  "Vui lòng chọn Thủy Cung cần thủ trước!": {
    "en": "Please choose Aquarium anglers first!",
    "ja": "水族館釣り人はまず選んでください！",
    "cn": "请先选择水族馆钓鱼者！"
  },
  "Vui lòng chọn Thủy Cung trước!": {
    "en": "Please choose Aquarium first!",
    "ja": "まずは水族館を選んでください！",
    "cn": "请先选择水族馆！"
  },
  "Vui lòng chọn cần thủ trước": {
    "en": "Please choose the angler first",
    "ja": "まずは釣り人を選んでください",
    "cn": "请先选择垂钓者"
  },
  "Vui lòng chọn kênh gửi bảng": {
    "en": "Please choose a channel to send the board",
    "ja": "ボードを送信するチャンネルを選択してください",
    "cn": "请选择发送板子的渠道"
  },
  "Vui lòng chọn kênh tổ chức giveaway": {
    "en": "Please select the giveaway organization channel",
    "ja": "プレゼント組織チャネルを選択してください",
    "cn": "请选择赠品组织渠道"
  },
  "Vui lòng chọn kênh và nhập tên phần thưởng!": {
    "en": "Please select channel and enter reward name!",
    "ja": "チャンネルを選択し、報酬名を入力してください。",
    "cn": "请选择频道并输入奖励名称！"
  },
  "Vui lòng chọn loài cá": {
    "en": "Please select fish species",
    "ja": "魚種を選択してください",
    "cn": "请选择鱼种"
  },
  "Vui lòng chọn loại cần câu": {
    "en": "Please select fishing rod type",
    "ja": "釣竿の種類を選択してください",
    "cn": "请选择鱼竿类型"
  },
  "Vui lòng chọn nhân vật anime": {
    "en": "Please choose an anime character",
    "ja": "アニメキャラクターを選択してください",
    "cn": "请选择一个动漫角色"
  },
  "Vui lòng chọn server trước!": {
    "en": "Please choose a server first!",
    "ja": "最初にサーバーを選択してください。",
    "cn": "请先选择服务器！"
  },
  "Vui lòng chọn thành tựu": {
    "en": "Please select an achievement",
    "ja": "実績を選択してください",
    "cn": "请选择一项成就"
  },
  "Vui lòng chọn vai trò": {
    "en": "Please select a role",
    "ja": "役割を選択してください",
    "cn": "请选择角色"
  },
  "Vui lòng chọn và lưu kênh nội quy trước khi đăng": {
    "en": "Please select and save the channel rules before posting",
    "ja": "投稿する前にチャンネルルールを選択して保存してください",
    "cn": "发帖前请选择并保存频道规则"
  },
  "Vui lòng chọn vật phẩm": {
    "en": "Please select item",
    "ja": "項目を選択してください",
    "cn": "请选择项目"
  },
  "Vui lòng chọn vật phẩm muốn thêm!": {
    "en": "Please select the item you want to add!",
    "ja": "追加したい項目を選択してください！",
    "cn": "请选择您要添加的项目！"
  },
  "Vui lòng chọn ít nhất Mùa hoặc Thời tiết để thiết lập": {
    "en": "Please select at least Season or Weather to set up",
    "ja": "設定する季節または天気を少なくとも選択してください",
    "cn": "请至少选择季节或天气进行设置"
  },
  "Vui lòng nhập Discord User ID": {
    "en": "Please enter Discord User ID",
    "ja": "DiscordのユーザーIDを入力してください",
    "cn": "请输入Discord用户ID"
  },
  "Vui lòng nhập Discord User ID cần thủ!": {
    "en": "Please enter Discord User ID angler!",
    "ja": "DiscordのユーザーIDを入力してくださいアングラー！",
    "cn": "请输入Discord用户ID钓鱼者！"
  },
  "Vui lòng nhập Discord User ID hoặc Tên thợ mỏ!": {
    "en": "Please enter Discord User ID or Miner Name!",
    "ja": "DiscordのユーザーIDまたはマイナー名を入力してください。",
    "cn": "请输入Discord用户ID或矿工名！"
  },
  "Vui lòng nhập Discord User ID nông dân": {
    "en": "Please enter Discord User ID farmer",
    "ja": "Discord ユーザー ID を入力してください ファーマー",
    "cn": "请输入 Discord 用户 ID 农民"
  },
  "Vui lòng nhập Discord User ID!": {
    "en": "Please enter Discord User ID!",
    "ja": "DiscordのユーザーIDを入力してください！",
    "cn": "请输入Discord用户ID！"
  },
  "Vui lòng nhập ID và Tên vật phẩm": {
    "en": "Please enter Item ID and Name",
    "ja": "アイテムIDと名前を入力してください",
    "cn": "请输入商品 ID 和名称"
  },
  "Vui lòng nhập ID và Tên vật phẩm!": {
    "en": "Please enter Item ID and Name!",
    "ja": "アイテムIDと名前を入力してください。",
    "cn": "请输入商品 ID 和名称！"
  },
  "Vui lòng nhập Mã ID tùy chỉnh!": {
    "en": "Please enter Custom ID Code!",
    "ja": "カスタム ID コードを入力してください。",
    "cn": "请输入自定义 ID 代码！"
  },
  "Vui lòng nhập Mã ID và Tên thành tựu": {
    "en": "Please enter ID Code and Achievement Name",
    "ja": "IDコードと実績名を入力してください",
    "cn": "请输入ID代码和成就名称"
  },
  "Vui lòng nhập Username hoặc Discord User ID!": {
    "en": "Please enter Username or Discord User ID!",
    "ja": "ユーザー名またはDiscordのユーザーIDを入力してください。",
    "cn": "请输入用户名或Discord用户ID！"
  },
  "Vui lòng nhập lệnh console": {
    "en": "Please enter console command",
    "ja": "コンソールコマンドを入力してください",
    "cn": "请输入控制台命令"
  },
  "Vui lòng nhập lệnh trước khi gửi!": {
    "en": "Please enter your order before sending!",
    "ja": "送信する前に注文内容を入力してください。",
    "cn": "发送前请输入您的订单！"
  },
  "Vui lòng nhập mã code": {
    "en": "Please enter code",
    "ja": "コードを入力してください",
    "cn": "请输入代码"
  },
  "Vui lòng nhập mã code để test!": {
    "en": "Please enter code to test!",
    "ja": "テストするにはコードを入力してください。",
    "cn": "请输入代码进行测试！"
  },
  "Vui lòng nhập mã kết nối sinh từ lệnh /discord server link trong Minecraft": {
    "en": "Please enter the connection code generated from the /discord server link command in Minecraft",
    "ja": "Minecraft の /discord サーバー リンク コマンドから生成された接続コードを入力してください",
    "cn": "请输入 Minecraft 中 /discord 服务器链接命令生成的连接代码"
  },
  "Vui lòng nhập mã liên kết từ in-game (/discord server link)!": {
    "en": "Please enter the link code from in-game (/discord server link)!",
    "ja": "ゲーム内（/discordサーバーリンク）からリンクコードを入力してください！",
    "cn": "请输入游戏内的链接代码（/discord 服务器链接）！"
  },
  "Vui lòng nhập mốc level (>0) và chọn vai trò": {
    "en": "Please enter level milestone (>0) and select role",
    "ja": "レベルマイルストーン (>0) を入力し、役割を選択してください",
    "cn": "请输入级别里程碑 (>0) 并选择角色"
  },
  "Vui lòng nhập nội dung phản hồi hoặc chọn file đính kèm": {
    "en": "Please enter your response or select an attachment",
    "ja": "回答を入力するか、添付ファイルを選択してください",
    "cn": "请输入您的回复或选择附件"
  },
  "Vui lòng nhập nội dung, cấu hình embed hoặc đính kèm tệp!": {
    "en": "Please enter content, embed configuration or attach file!",
    "ja": "コンテンツを入力するか、設定を埋め込むか、ファイルを添付してください。",
    "cn": "请输入内容、嵌入配置或附加文件！"
  },
  "Vui lòng nhập phần thưởng giveaway": {
    "en": "Please enter a giveaway reward",
    "ja": "プレゼントの報酬を入力してください",
    "cn": "请输入赠品奖励"
  },
  "Vui lòng nhập số lượng hợp lệ (>= 0)!": {
    "en": "Please enter a valid quantity (>= 0)!",
    "ja": "有効な数量 (>= 0) を入力してください。",
    "cn": "请输入有效数量 (>= 0)！"
  },
  "Vui lòng nhập thời lượng (vd: 30m, 1h)": {
    "en": "Please enter duration (eg: 30m, 1h)",
    "ja": "継続時間を入力してください (例: 30 分、1 時間)",
    "cn": "请输入持续时间（例如：30m、1h）"
  },
  "Vui lòng nhập tên cần câu": {
    "en": "Please enter fishing rod name",
    "ja": "釣竿名を入力してください",
    "cn": "请输入鱼竿名称"
  },
  "Vui lòng nhập tên loài cá kèm emoji": {
    "en": "Please enter the fish species name with emoji",
    "ja": "魚種名を絵文字付きで入力してください",
    "cn": "请输入带有表情符号的鱼种名称"
  },
  "Vui lòng nhập tên mồi câu": {
    "en": "Please enter the bait name",
    "ja": "エサ名を入力してください",
    "cn": "请输入诱饵名称"
  },
  "Vui lòng nhập tên rương báu": {
    "en": "Please enter the name of the treasure chest",
    "ja": "宝箱の名前を入力してください",
    "cn": "请输入宝箱名称"
  },
  "Vui lòng nhập tên thú cưng": {
    "en": "Please enter your pet's name",
    "ja": "ペットの名前を入力してください",
    "cn": "请输入您的宠物的名字"
  },
  "Vui lòng nhập tên túi cá": {
    "en": "Please enter the name of the fish bag",
    "ja": "魚袋の名前を入力してください",
    "cn": "请输入鱼包名称"
  },
  "Vui lòng nhập tên vật phẩm troll": {
    "en": "Please enter troll item name",
    "ja": "トロールアイテム名を入力してください",
    "cn": "请输入巨魔物品名称"
  },
  "Vui lòng nhập từ cần thêm": {
    "en": "Please enter the word you need to add",
    "ja": "追加する必要がある単語を入力してください",
    "cn": "请输入您需要添加的单词"
  },
  "Vui lòng nhập từ khóa (keyword)": {
    "en": "Please enter keyword (keyword)",
    "ja": "キーワード（キーワード）を入力してください",
    "cn": "请输入关键字(keyword)"
  },
  "Vui lòng thêm ít nhất 1 role vào bảng": {
    "en": "Please add at least 1 role to the table",
    "ja": "少なくとも 1 つの役割をテーブルに追加してください",
    "cn": "请在表中添加至少 1 个角色"
  },
  "Vui lòng tra cứu người chơi trước": {
    "en": "Please look up the player first",
    "ja": "まずはプレーヤーを調べてください",
    "cn": "请先查找播放器"
  },
  "Vui lòng tra cứu nông dân trước": {
    "en": "Please look up farmers first",
    "ja": "まずは農家を調べてください",
    "cn": "请先查找农民"
  },
  "Vui lòng tra cứu thợ mỏ trước!": {
    "en": "Please look up miners first!",
    "ja": "まずはマイナーを調べてください！",
    "cn": "请先查一下矿工！"
  },
  "Vĩnh viễn": {
    "en": "Forever",
    "ja": "永遠に",
    "cn": "永远"
  },
  "Vật phẩm hỗ trợ hoặc troll tương tác người chơi": {
    "en": "Support items or trolls for player interaction",
    "ja": "プレイヤーとのインタラクションのためのサポートアイテムまたはトロール",
    "cn": "支持玩家互动的物品或巨魔"
  },
  "Vẽ hình theo từ khóa &amp; thi tài đoán từ real-time, hỗ trợ Multiplayer &amp; Bot Sakura": {
    "en": "Draw pictures according to keywords & compete in real-time word guessing, support Multiplayer & Sakura Bot",
    "ja": "キーワードに従って絵を描き、リアルタイムの単語推測で競い合い、マルチプレイヤーとさくらボットをサポート",
    "cn": "根据关键词画图并进行实时猜词比赛，支持多人游戏和樱花机器人"
  },
  "Vớt được khi câu cá": {
    "en": "Vớt được khi câu cá",
    "ja": "Vớt được khi câu cá",
    "cn": "Vớt được khi câu cá"
  },
  "WebSocket Console chưa kết nối hoặc đang kết nối lại...": {
    "en": "WebSocket Console chưa kết nối hoặc đang kết nối lại...",
    "ja": "WebSocket Console chưa kết nối hoặc đang kết nối lại...",
    "cn": "WebSocket Console chưa kết nối hoặc đang kết nối lại..."
  },
  "Xem ảnh gốc": {
    "en": "Xem ảnh gốc",
    "ja": "Xem ảnh gốc",
    "cn": "Xem ảnh gốc"
  },
  "Xin chào! Mình là Sakura 🌸 — hỏi gì mình cũng trả lời nhé!": {
    "en": "Xin chào! Mình là Sakura 🌸 — hỏi gì mình cũng trả lời nhé!",
    "ja": "Xin chào! Mình là Sakura 🌸 — hỏi gì mình cũng trả lời nhé!",
    "cn": "Xin chào! Mình là Sakura 🌸 — hỏi gì mình cũng trả lời nhé!"
  },
  "Xin lỗi, chưa trả lời được. Thử lại nhé!": {
    "en": "Xin lỗi, chưa trả lời được. Thử lại nhé!",
    "ja": "Xin lỗi, chưa trả lời được. Thử lại nhé!",
    "cn": "Xin lỗi, chưa trả lời được. Thử lại nhé!"
  },
  "Xóa con cá này khỏi giỏ": {
    "en": "Xóa con cá này khỏi giỏ",
    "ja": "Xóa con cá này khỏi giỏ",
    "cn": "Xóa con cá này khỏi giỏ"
  },
  "Xóa vĩnh viễn khỏi thủy cung": {
    "en": "Xóa vĩnh viễn khỏi thủy cung",
    "ja": "Xóa vĩnh viễn khỏi thủy cung",
    "cn": "Xóa vĩnh viễn khỏi thủy cung"
  },
  "\\n' + content; } } const blob = new Blob([content], { type: \"text/html;charset=utf-8\" }); const url = URL.createObjectURL(blob); window.open(url, \"_blank\"); } // ========================================== // DATABASE VIEWER LOGIC (.db, .sqlite, .sqlite3) // ========================================== async function openDatabaseFile(relPath) { if (isDirty) { if (!confirm(\"Bạn có thay đổi chưa lưu trong tệp code hiện tại. Hủy thay đổi và chuyển sang xem Database?\")) { return; } setDirty(false); } currentDbPath = (relPath || \"\").replace(/\\\\/g, \"/\"); document.getElementById(\"codeEditorContainer\").style.display = \"none\"; const dbContainer = document.getElementById(\"dbViewerContainer\"); dbContainer.style.display = \"flex\"; switchDbTab(\"table\"); document.getElementById(\"dbFilePath\").textContent = currentDbPath; document.querySelectorAll(\".bf-file-item\").forEach(el => { if (el.dataset.path === currentDbPath) el.classList.add(\"active\"); else el.classList.remove(\"active\"); }); showToast(`Đang đọc cấu trúc Database [${currentDbPath}]...`); await loadDatabaseSchema(currentDbPath); } function closeDatabaseView() { document.getElementById(\"dbViewerContainer\").style.display = \"none\"; document.getElementById(\"codeEditorContainer\").style.display = \"flex\"; currentDbPath = \"\"; } function refreshCurrentDatabase() { if (currentDbPath) { loadDatabaseSchema(currentDbPath); } } async function loadDatabaseSchema(relPath) { try { const url = `/api/admin/database/schema?path=${encodeURIComponent(relPath)}`; const res = await fetch(url); const data = await res.json(); if (data.ok) { currentDbSchema = data; const tables = data.tables || []; const byteSize = data.file_size || data.size || 0; document.getElementById(\"dbTablesCountBadge\").textContent = `• ${tables.length} bảng • ${formatBytes(byteSize)}`; const select = document.getElementById(\"dbTableSelect\"); select.innerHTML = \"\"; if (tables.length === 0) { select.innerHTML = `": {
    "en": "\\n' + content; } } const blob = new Blob([content], { type: \"text/html;charset=utf-8\" }); const url = URL.createObjectURL(blob); window.open(url, \"_blank\"); } // ========================================== // DATABASE VIEWER LOGIC (.db, .sqlite, .sqlite3) // ========================================== async function openDatabaseFile(relPath) { if (isDirty) { if (!confirm(\"Bạn có thay đổi chưa lưu trong tệp code hiện tại. Hủy thay đổi và chuyển sang xem Database?\")) { return; } setDirty(false); } currentDbPath = (relPath || \"\").replace(/\\\\/g, \"/\"); document.getElementById(\"codeEditorContainer\").style.display = \"none\"; const dbContainer = document.getElementById(\"dbViewerContainer\"); dbContainer.style.display = \"flex\"; switchDbTab(\"table\"); document.getElementById(\"dbFilePath\").textContent = currentDbPath; document.querySelectorAll(\".bf-file-item\").forEach(el => { if (el.dataset.path === currentDbPath) el.classList.add(\"active\"); else el.classList.remove(\"active\"); }); showToast(`Đang đọc cấu trúc Database [${currentDbPath}]...`); await loadDatabaseSchema(currentDbPath); } function closeDatabaseView() { document.getElementById(\"dbViewerContainer\").style.display = \"none\"; document.getElementById(\"codeEditorContainer\").style.display = \"flex\"; currentDbPath = \"\"; } function refreshCurrentDatabase() { if (currentDbPath) { loadDatabaseSchema(currentDbPath); } } async function loadDatabaseSchema(relPath) { try { const url = `/api/admin/database/schema?path=${encodeURIComponent(relPath)}`; const res = await fetch(url); const data = await res.json(); if (data.ok) { currentDbSchema = data; const tables = data.tables || []; const byteSize = data.file_size || data.size || 0; document.getElementById(\"dbTablesCountBadge\").textContent = `• ${tables.length} bảng • ${formatBytes(byteSize)}`; const select = document.getElementById(\"dbTableSelect\"); select.innerHTML = \"\"; if (tables.length === 0) { select.innerHTML = `",
    "ja": "\\n' + content; } } const blob = new Blob([content], { type: \"text/html;charset=utf-8\" }); const url = URL.createObjectURL(blob); window.open(url, \"_blank\"); } // ========================================== // DATABASE VIEWER LOGIC (.db, .sqlite, .sqlite3) // ========================================== async function openDatabaseFile(relPath) { if (isDirty) { if (!confirm(\"Bạn có thay đổi chưa lưu trong tệp code hiện tại. Hủy thay đổi và chuyển sang xem Database?\")) { return; } setDirty(false); } currentDbPath = (relPath || \"\").replace(/\\\\/g, \"/\"); document.getElementById(\"codeEditorContainer\").style.display = \"none\"; const dbContainer = document.getElementById(\"dbViewerContainer\"); dbContainer.style.display = \"flex\"; switchDbTab(\"table\"); document.getElementById(\"dbFilePath\").textContent = currentDbPath; document.querySelectorAll(\".bf-file-item\").forEach(el => { if (el.dataset.path === currentDbPath) el.classList.add(\"active\"); else el.classList.remove(\"active\"); }); showToast(`Đang đọc cấu trúc Database [${currentDbPath}]...`); await loadDatabaseSchema(currentDbPath); } function closeDatabaseView() { document.getElementById(\"dbViewerContainer\").style.display = \"none\"; document.getElementById(\"codeEditorContainer\").style.display = \"flex\"; currentDbPath = \"\"; } function refreshCurrentDatabase() { if (currentDbPath) { loadDatabaseSchema(currentDbPath); } } async function loadDatabaseSchema(relPath) { try { const url = `/api/admin/database/schema?path=${encodeURIComponent(relPath)}`; const res = await fetch(url); const data = await res.json(); if (data.ok) { currentDbSchema = data; const tables = data.tables || []; const byteSize = data.file_size || data.size || 0; document.getElementById(\"dbTablesCountBadge\").textContent = `• ${tables.length} bảng • ${formatBytes(byteSize)}`; const select = document.getElementById(\"dbTableSelect\"); select.innerHTML = \"\"; if (tables.length === 0) { select.innerHTML = `",
    "cn": "\\n' + content; } } const blob = new Blob([content], { type: \"text/html;charset=utf-8\" }); const url = URL.createObjectURL(blob); window.open(url, \"_blank\"); } // ========================================== // DATABASE VIEWER LOGIC (.db, .sqlite, .sqlite3) // ========================================== async function openDatabaseFile(relPath) { if (isDirty) { if (!confirm(\"Bạn có thay đổi chưa lưu trong tệp code hiện tại. Hủy thay đổi và chuyển sang xem Database?\")) { return; } setDirty(false); } currentDbPath = (relPath || \"\").replace(/\\\\/g, \"/\"); document.getElementById(\"codeEditorContainer\").style.display = \"none\"; const dbContainer = document.getElementById(\"dbViewerContainer\"); dbContainer.style.display = \"flex\"; switchDbTab(\"table\"); document.getElementById(\"dbFilePath\").textContent = currentDbPath; document.querySelectorAll(\".bf-file-item\").forEach(el => { if (el.dataset.path === currentDbPath) el.classList.add(\"active\"); else el.classList.remove(\"active\"); }); showToast(`Đang đọc cấu trúc Database [${currentDbPath}]...`); await loadDatabaseSchema(currentDbPath); } function closeDatabaseView() { document.getElementById(\"dbViewerContainer\").style.display = \"none\"; document.getElementById(\"codeEditorContainer\").style.display = \"flex\"; currentDbPath = \"\"; } function refreshCurrentDatabase() { if (currentDbPath) { loadDatabaseSchema(currentDbPath); } } async function loadDatabaseSchema(relPath) { try { const url = `/api/admin/database/schema?path=${encodeURIComponent(relPath)}`; const res = await fetch(url); const data = await res.json(); if (data.ok) { currentDbSchema = data; const tables = data.tables || []; const byteSize = data.file_size || data.size || 0; document.getElementById(\"dbTablesCountBadge\").textContent = `• ${tables.length} bảng • ${formatBytes(byteSize)}`; const select = document.getElementById(\"dbTableSelect\"); select.innerHTML = \"\"; if (tables.length === 0) { select.innerHTML = `"
  },
  "^linh.*béo$": {
    "en": "^linh.*béo$",
    "ja": "^linh.*béo$",
    "cn": "^linh.*béo$"
  },
  "`; return; } tables.forEach(t => { const opt = document.createElement(\"option\"); opt.value = t.name; const rCount = (t.row_count !== undefined && t.row_count !== null) ? t.row_count.toLocaleString() : \"0\"; const cCount = (t.columns && t.columns.length) ? t.columns.length : 0; opt.textContent = `${t.name} (${rCount} dòng, ${cCount} cột)`; select.appendChild(opt); }); // Chọn bảng đầu tiên hoặc giữ bảng hiện tại nếu còn tồn tại let targetTable = tables[0].name; if (currentDbTable && tables.some(t => t.name === currentDbTable)) { targetTable = currentDbTable; } currentDbTable = targetTable; select.value = targetTable; dbCurrentPage = 1; dbSearchKeyword = \"\"; document.getElementById(\"dbSearchInput\").value = \"\"; // Mặc định câu lệnh SQL mẫu cho console document.getElementById(\"dbSqlInput\").value = `SELECT * FROM \"${targetTable}\" LIMIT 20;`; await loadDatabaseTable(targetTable, 1, \"\"); showToast(`Đã nạp Database: ${tables.length} bảng`, \"success\"); } else { showToast(data.error || \"Không thể đọc cấu trúc database\", \"error\"); alert(`❌ ${data.error}`); } } catch (e) { console.error(\"loadDatabaseSchema error:\", e); showToast(\"Lỗi kết nối khi đọc database: \" + e.message, \"error\"); } } function onDbTableChange(tableName) { if (!tableName) return; currentDbTable = tableName; dbCurrentPage = 1; dbSearchKeyword = \"\"; document.getElementById(\"dbSearchInput\").value = \"\"; document.getElementById(\"dbSqlInput\").value = `SELECT * FROM \"${tableName}\" LIMIT 20;`; loadDatabaseTable(tableName, 1, \"\"); } async function loadDatabaseTable(tableName, page = 1, search = \"\") { if (!currentDbPath || !tableName) return; dbCurrentPage = page; dbSearchKeyword = search; const limit = dbPageSize; const offset = (page - 1) * limit; const thead = document.getElementById(\"dbTableHead\"); const tbody = document.getElementById(\"dbTableBody\"); const schemaBar = document.getElementById(\"dbSchemaBar\"); tbody.innerHTML = `": {
    "en": "`; return; } tables.forEach(t => { const opt = document.createElement(\"option\"); opt.value = t.name; const rCount = (t.row_count !== undefined && t.row_count !== null) ? t.row_count.toLocaleString() : \"0\"; const cCount = (t.columns && t.columns.length) ? t.columns.length : 0; opt.textContent = `${t.name} (${rCount} dòng, ${cCount} cột)`; select.appendChild(opt); }); // Chọn bảng đầu tiên hoặc giữ bảng hiện tại nếu còn tồn tại let targetTable = tables[0].name; if (currentDbTable && tables.some(t => t.name === currentDbTable)) { targetTable = currentDbTable; } currentDbTable = targetTable; select.value = targetTable; dbCurrentPage = 1; dbSearchKeyword = \"\"; document.getElementById(\"dbSearchInput\").value = \"\"; // Mặc định câu lệnh SQL mẫu cho console document.getElementById(\"dbSqlInput\").value = `SELECT * FROM \"${targetTable}\" LIMIT 20;`; await loadDatabaseTable(targetTable, 1, \"\"); showToast(`Đã nạp Database: ${tables.length} bảng`, \"success\"); } else { showToast(data.error || \"Không thể đọc cấu trúc database\", \"error\"); alert(`❌ ${data.error}`); } } catch (e) { console.error(\"loadDatabaseSchema error:\", e); showToast(\"Lỗi kết nối khi đọc database: \" + e.message, \"error\"); } } function onDbTableChange(tableName) { if (!tableName) return; currentDbTable = tableName; dbCurrentPage = 1; dbSearchKeyword = \"\"; document.getElementById(\"dbSearchInput\").value = \"\"; document.getElementById(\"dbSqlInput\").value = `SELECT * FROM \"${tableName}\" LIMIT 20;`; loadDatabaseTable(tableName, 1, \"\"); } async function loadDatabaseTable(tableName, page = 1, search = \"\") { if (!currentDbPath || !tableName) return; dbCurrentPage = page; dbSearchKeyword = search; const limit = dbPageSize; const offset = (page - 1) * limit; const thead = document.getElementById(\"dbTableHead\"); const tbody = document.getElementById(\"dbTableBody\"); const schemaBar = document.getElementById(\"dbSchemaBar\"); tbody.innerHTML = `",
    "ja": "`; return; } tables.forEach(t => { const opt = document.createElement(\"option\"); opt.value = t.name; const rCount = (t.row_count !== undefined && t.row_count !== null) ? t.row_count.toLocaleString() : \"0\"; const cCount = (t.columns && t.columns.length) ? t.columns.length : 0; opt.textContent = `${t.name} (${rCount} dòng, ${cCount} cột)`; select.appendChild(opt); }); // Chọn bảng đầu tiên hoặc giữ bảng hiện tại nếu còn tồn tại let targetTable = tables[0].name; if (currentDbTable && tables.some(t => t.name === currentDbTable)) { targetTable = currentDbTable; } currentDbTable = targetTable; select.value = targetTable; dbCurrentPage = 1; dbSearchKeyword = \"\"; document.getElementById(\"dbSearchInput\").value = \"\"; // Mặc định câu lệnh SQL mẫu cho console document.getElementById(\"dbSqlInput\").value = `SELECT * FROM \"${targetTable}\" LIMIT 20;`; await loadDatabaseTable(targetTable, 1, \"\"); showToast(`Đã nạp Database: ${tables.length} bảng`, \"success\"); } else { showToast(data.error || \"Không thể đọc cấu trúc database\", \"error\"); alert(`❌ ${data.error}`); } } catch (e) { console.error(\"loadDatabaseSchema error:\", e); showToast(\"Lỗi kết nối khi đọc database: \" + e.message, \"error\"); } } function onDbTableChange(tableName) { if (!tableName) return; currentDbTable = tableName; dbCurrentPage = 1; dbSearchKeyword = \"\"; document.getElementById(\"dbSearchInput\").value = \"\"; document.getElementById(\"dbSqlInput\").value = `SELECT * FROM \"${tableName}\" LIMIT 20;`; loadDatabaseTable(tableName, 1, \"\"); } async function loadDatabaseTable(tableName, page = 1, search = \"\") { if (!currentDbPath || !tableName) return; dbCurrentPage = page; dbSearchKeyword = search; const limit = dbPageSize; const offset = (page - 1) * limit; const thead = document.getElementById(\"dbTableHead\"); const tbody = document.getElementById(\"dbTableBody\"); const schemaBar = document.getElementById(\"dbSchemaBar\"); tbody.innerHTML = `",
    "cn": "`; return; } tables.forEach(t => { const opt = document.createElement(\"option\"); opt.value = t.name; const rCount = (t.row_count !== undefined && t.row_count !== null) ? t.row_count.toLocaleString() : \"0\"; const cCount = (t.columns && t.columns.length) ? t.columns.length : 0; opt.textContent = `${t.name} (${rCount} dòng, ${cCount} cột)`; select.appendChild(opt); }); // Chọn bảng đầu tiên hoặc giữ bảng hiện tại nếu còn tồn tại let targetTable = tables[0].name; if (currentDbTable && tables.some(t => t.name === currentDbTable)) { targetTable = currentDbTable; } currentDbTable = targetTable; select.value = targetTable; dbCurrentPage = 1; dbSearchKeyword = \"\"; document.getElementById(\"dbSearchInput\").value = \"\"; // Mặc định câu lệnh SQL mẫu cho console document.getElementById(\"dbSqlInput\").value = `SELECT * FROM \"${targetTable}\" LIMIT 20;`; await loadDatabaseTable(targetTable, 1, \"\"); showToast(`Đã nạp Database: ${tables.length} bảng`, \"success\"); } else { showToast(data.error || \"Không thể đọc cấu trúc database\", \"error\"); alert(`❌ ${data.error}`); } } catch (e) { console.error(\"loadDatabaseSchema error:\", e); showToast(\"Lỗi kết nối khi đọc database: \" + e.message, \"error\"); } } function onDbTableChange(tableName) { if (!tableName) return; currentDbTable = tableName; dbCurrentPage = 1; dbSearchKeyword = \"\"; document.getElementById(\"dbSearchInput\").value = \"\"; document.getElementById(\"dbSqlInput\").value = `SELECT * FROM \"${tableName}\" LIMIT 20;`; loadDatabaseTable(tableName, 1, \"\"); } async function loadDatabaseTable(tableName, page = 1, search = \"\") { if (!currentDbPath || !tableName) return; dbCurrentPage = page; dbSearchKeyword = search; const limit = dbPageSize; const offset = (page - 1) * limit; const thead = document.getElementById(\"dbTableHead\"); const tbody = document.getElementById(\"dbTableBody\"); const schemaBar = document.getElementById(\"dbSchemaBar\"); tbody.innerHTML = `"
  },
  "`; showToast(data.error || \"Không thể tải dữ liệu bảng\", \"error\"); } } catch (e) { console.error(\"loadDatabaseTable error:\", e); tbody.innerHTML = `": {
    "en": "`; showToast(data.error || \"Không thể tải dữ liệu bảng\", \"error\"); } } catch (e) { console.error(\"loadDatabaseTable error:\", e); tbody.innerHTML = `",
    "ja": "`; showToast(data.error || \"Không thể tải dữ liệu bảng\", \"error\"); } } catch (e) { console.error(\"loadDatabaseTable error:\", e); tbody.innerHTML = `",
    "cn": "`; showToast(data.error || \"Không thể tải dữ liệu bảng\", \"error\"); } } catch (e) { console.error(\"loadDatabaseTable error:\", e); tbody.innerHTML = `"
  },
  "`; showToast(data.error || \"Lỗi truy vấn SQL\", \"error\"); } } catch (e) { statusEl.textContent = \"❌ Lỗi kết nối máy chủ\"; showToast(\"Lỗi kết nối khi gửi truy vấn SQL\", \"error\"); } } function exportCurrentTable(format) { if (!currentTableData || !currentTableData.rows || currentTableData.rows.length === 0) { alert(\"Không có dữ liệu trong bảng để xuất!\"); return; } const filename = `${currentDbTable || 'database'}_data.${format}`; if (format === \"json\") { const jsonStr = JSON.stringify(currentTableData.rows, null, 2); downloadFileBlob(jsonStr, filename, \"application/json\"); } else if (format === \"csv\") { const cols = currentTableData.columns; let csv = cols.map(c => `\"${String(c).replace(/\"/g, '\"\"')}\"`).join(\",\") + \"\\n\"; currentTableData.rows.forEach(row => { const rowVals = cols.map(c => { const v = row[c]; if (v === null || v === undefined) return '\"\"'; return `\"${String(v).replace(/\"/g, '\"\"')}\"`; }); csv += rowVals.join(\",\") + \"\\n\"; }); downloadFileBlob(csv, filename, \"text/csv;charset=utf-8;\"); } } function exportSqlQueryResult() { if (!lastQueryResult || !lastQueryResult.rows) return; const jsonStr = JSON.stringify(lastQueryResult.rows, null, 2); downloadFileBlob(jsonStr, `sql_result_${Date.now()}.json`, \"application/json\"); } function downloadFileBlob(content, filename, mimeType) { const blob = new Blob([content], { type: mimeType }); const url = URL.createObjectURL(blob); const a = document.createElement(\"a\"); a.href = url; a.download = filename; document.body.appendChild(a); a.click(); document.body.removeChild(a); URL.revokeObjectURL(url); showToast(`Đã tải xuống tệp ${filename}!`, \"success\"); } // ========================================== // API CALLS: COG RELOADER // ========================================== async function loadCogsSummary() { try { const res = await fetch(\"/api/admin/cogs/list\"); const data = await res.json(); if (data.ok) { document.getElementById(\"loadedCogsCount\").textContent = `${data.loaded_count}/${data.total_cogs}`; document.getElementById(\"modalCogsTotal\").textContent = data.total_cogs; } } catch (e) {} } async function reloadSpecificCog(extName) { showToast(`Đang nạp lại Cog ${extName}...`); try { const res = await fetch(\"/api/admin/cogs/reload\", { method: \"POST\", headers: { \"Content-Type\": \"application/json\" }, body: JSON.stringify({ extension: extName }) }); const data = await res.json(); if (data.ok) { showToast(data.message || `Đã nạp lại ${extName}!`, \"success\"); loadCogsSummary(); } else { alert(`❌ NẠP LẠI THẤT BẠI:\\n\\n${data.error}`); showToast(`Lỗi nạp lại ${extName}`, \"error\"); } } catch (e) { showToast(\"Lỗi kết nối khi nạp lại Cog\", \"error\"); } } async function reloadAllCogs() { if (!confirm(\"Bạn có chắc chắn muốn nạp lại TOÀN BỘ Cogs của SakuraBot không?\")) { return; } showToast(\"Đang nạp lại toàn bộ Cogs, vui lòng đợi...\"); try { const res = await fetch(\"/api/admin/cogs/reload\", { method: \"POST\", headers: { \"Content-Type\": \"application/json\" }, body: JSON.stringify({ extension: \"all\", sync_tree: false }) }); const data = await res.json(); if (data.ok) { alert(`✅ KẾT QUẢ NẠP LẠI TOÀN BỘ:\\n\\n• Thành công: ${data.reloaded_count} extensions\\n• Thất bại: ${data.failed_count} extensions`); showToast(data.message, \"success\"); loadCogsSummary(); } else { let errDetail = (data.failed || []).map(f => `• ${f.extension}: ${f.error}`).join(\"\\n\"); alert(`⚠️ NẠP LẠI CÓ LỖI:\\n\\n${errDetail || data.error}`); showToast(\"Một số Cog nạp lại thất bại\", \"error\"); } } catch (e) { showToast(\"Lỗi kết nối máy chủ\", \"error\"); } } async function syncSlashTree() { if (!confirm(\"Đồng bộ lại cây lệnh Slash Commands (bot.tree.sync()) lên Discord?\")) return; showToast(\"Đang đồng bộ lệnh Slash lên Discord...\"); try { const res = await fetch(\"/api/admin/cogs/sync-tree\", { method: \"POST\" }); const data = await res.json(); if (data.ok) { alert(data.message); showToast(data.message, \"success\"); } else { alert(`❌ Lỗi đồng bộ: ${data.error}`); showToast(\"Lỗi đồng bộ cây lệnh\", \"error\"); } } catch (e) { showToast(\"Lỗi mạng khi đồng bộ lệnh\", \"error\"); } } async function openCogsModal() { document.getElementById(\"cogsModal\").classList.add(\"active\"); const tbody = document.getElementById(\"cogsTableBody\"); tbody.innerHTML = `": {
    "en": "`; showToast(data.error || \"Lỗi truy vấn SQL\", \"error\"); } } catch (e) { statusEl.textContent = \"❌ Lỗi kết nối máy chủ\"; showToast(\"Lỗi kết nối khi gửi truy vấn SQL\", \"error\"); } } function exportCurrentTable(format) { if (!currentTableData || !currentTableData.rows || currentTableData.rows.length === 0) { alert(\"Không có dữ liệu trong bảng để xuất!\"); return; } const filename = `${currentDbTable || 'database'}_data.${format}`; if (format === \"json\") { const jsonStr = JSON.stringify(currentTableData.rows, null, 2); downloadFileBlob(jsonStr, filename, \"application/json\"); } else if (format === \"csv\") { const cols = currentTableData.columns; let csv = cols.map(c => `\"${String(c).replace(/\"/g, '\"\"')}\"`).join(\",\") + \"\\n\"; currentTableData.rows.forEach(row => { const rowVals = cols.map(c => { const v = row[c]; if (v === null || v === undefined) return '\"\"'; return `\"${String(v).replace(/\"/g, '\"\"')}\"`; }); csv += rowVals.join(\",\") + \"\\n\"; }); downloadFileBlob(csv, filename, \"text/csv;charset=utf-8;\"); } } function exportSqlQueryResult() { if (!lastQueryResult || !lastQueryResult.rows) return; const jsonStr = JSON.stringify(lastQueryResult.rows, null, 2); downloadFileBlob(jsonStr, `sql_result_${Date.now()}.json`, \"application/json\"); } function downloadFileBlob(content, filename, mimeType) { const blob = new Blob([content], { type: mimeType }); const url = URL.createObjectURL(blob); const a = document.createElement(\"a\"); a.href = url; a.download = filename; document.body.appendChild(a); a.click(); document.body.removeChild(a); URL.revokeObjectURL(url); showToast(`Đã tải xuống tệp ${filename}!`, \"success\"); } // ========================================== // API CALLS: COG RELOADER // ========================================== async function loadCogsSummary() { try { const res = await fetch(\"/api/admin/cogs/list\"); const data = await res.json(); if (data.ok) { document.getElementById(\"loadedCogsCount\").textContent = `${data.loaded_count}/${data.total_cogs}`; document.getElementById(\"modalCogsTotal\").textContent = data.total_cogs; } } catch (e) {} } async function reloadSpecificCog(extName) { showToast(`Đang nạp lại Cog ${extName}...`); try { const res = await fetch(\"/api/admin/cogs/reload\", { method: \"POST\", headers: { \"Content-Type\": \"application/json\" }, body: JSON.stringify({ extension: extName }) }); const data = await res.json(); if (data.ok) { showToast(data.message || `Đã nạp lại ${extName}!`, \"success\"); loadCogsSummary(); } else { alert(`❌ NẠP LẠI THẤT BẠI:\\n\\n${data.error}`); showToast(`Lỗi nạp lại ${extName}`, \"error\"); } } catch (e) { showToast(\"Lỗi kết nối khi nạp lại Cog\", \"error\"); } } async function reloadAllCogs() { if (!confirm(\"Bạn có chắc chắn muốn nạp lại TOÀN BỘ Cogs của SakuraBot không?\")) { return; } showToast(\"Đang nạp lại toàn bộ Cogs, vui lòng đợi...\"); try { const res = await fetch(\"/api/admin/cogs/reload\", { method: \"POST\", headers: { \"Content-Type\": \"application/json\" }, body: JSON.stringify({ extension: \"all\", sync_tree: false }) }); const data = await res.json(); if (data.ok) { alert(`✅ KẾT QUẢ NẠP LẠI TOÀN BỘ:\\n\\n• Thành công: ${data.reloaded_count} extensions\\n• Thất bại: ${data.failed_count} extensions`); showToast(data.message, \"success\"); loadCogsSummary(); } else { let errDetail = (data.failed || []).map(f => `• ${f.extension}: ${f.error}`).join(\"\\n\"); alert(`⚠️ NẠP LẠI CÓ LỖI:\\n\\n${errDetail || data.error}`); showToast(\"Một số Cog nạp lại thất bại\", \"error\"); } } catch (e) { showToast(\"Lỗi kết nối máy chủ\", \"error\"); } } async function syncSlashTree() { if (!confirm(\"Đồng bộ lại cây lệnh Slash Commands (bot.tree.sync()) lên Discord?\")) return; showToast(\"Đang đồng bộ lệnh Slash lên Discord...\"); try { const res = await fetch(\"/api/admin/cogs/sync-tree\", { method: \"POST\" }); const data = await res.json(); if (data.ok) { alert(data.message); showToast(data.message, \"success\"); } else { alert(`❌ Lỗi đồng bộ: ${data.error}`); showToast(\"Lỗi đồng bộ cây lệnh\", \"error\"); } } catch (e) { showToast(\"Lỗi mạng khi đồng bộ lệnh\", \"error\"); } } async function openCogsModal() { document.getElementById(\"cogsModal\").classList.add(\"active\"); const tbody = document.getElementById(\"cogsTableBody\"); tbody.innerHTML = `",
    "ja": "`; showToast(data.error || \"Lỗi truy vấn SQL\", \"error\"); } } catch (e) { statusEl.textContent = \"❌ Lỗi kết nối máy chủ\"; showToast(\"Lỗi kết nối khi gửi truy vấn SQL\", \"error\"); } } function exportCurrentTable(format) { if (!currentTableData || !currentTableData.rows || currentTableData.rows.length === 0) { alert(\"Không có dữ liệu trong bảng để xuất!\"); return; } const filename = `${currentDbTable || 'database'}_data.${format}`; if (format === \"json\") { const jsonStr = JSON.stringify(currentTableData.rows, null, 2); downloadFileBlob(jsonStr, filename, \"application/json\"); } else if (format === \"csv\") { const cols = currentTableData.columns; let csv = cols.map(c => `\"${String(c).replace(/\"/g, '\"\"')}\"`).join(\",\") + \"\\n\"; currentTableData.rows.forEach(row => { const rowVals = cols.map(c => { const v = row[c]; if (v === null || v === undefined) return '\"\"'; return `\"${String(v).replace(/\"/g, '\"\"')}\"`; }); csv += rowVals.join(\",\") + \"\\n\"; }); downloadFileBlob(csv, filename, \"text/csv;charset=utf-8;\"); } } function exportSqlQueryResult() { if (!lastQueryResult || !lastQueryResult.rows) return; const jsonStr = JSON.stringify(lastQueryResult.rows, null, 2); downloadFileBlob(jsonStr, `sql_result_${Date.now()}.json`, \"application/json\"); } function downloadFileBlob(content, filename, mimeType) { const blob = new Blob([content], { type: mimeType }); const url = URL.createObjectURL(blob); const a = document.createElement(\"a\"); a.href = url; a.download = filename; document.body.appendChild(a); a.click(); document.body.removeChild(a); URL.revokeObjectURL(url); showToast(`Đã tải xuống tệp ${filename}!`, \"success\"); } // ========================================== // API CALLS: COG RELOADER // ========================================== async function loadCogsSummary() { try { const res = await fetch(\"/api/admin/cogs/list\"); const data = await res.json(); if (data.ok) { document.getElementById(\"loadedCogsCount\").textContent = `${data.loaded_count}/${data.total_cogs}`; document.getElementById(\"modalCogsTotal\").textContent = data.total_cogs; } } catch (e) {} } async function reloadSpecificCog(extName) { showToast(`Đang nạp lại Cog ${extName}...`); try { const res = await fetch(\"/api/admin/cogs/reload\", { method: \"POST\", headers: { \"Content-Type\": \"application/json\" }, body: JSON.stringify({ extension: extName }) }); const data = await res.json(); if (data.ok) { showToast(data.message || `Đã nạp lại ${extName}!`, \"success\"); loadCogsSummary(); } else { alert(`❌ NẠP LẠI THẤT BẠI:\\n\\n${data.error}`); showToast(`Lỗi nạp lại ${extName}`, \"error\"); } } catch (e) { showToast(\"Lỗi kết nối khi nạp lại Cog\", \"error\"); } } async function reloadAllCogs() { if (!confirm(\"Bạn có chắc chắn muốn nạp lại TOÀN BỘ Cogs của SakuraBot không?\")) { return; } showToast(\"Đang nạp lại toàn bộ Cogs, vui lòng đợi...\"); try { const res = await fetch(\"/api/admin/cogs/reload\", { method: \"POST\", headers: { \"Content-Type\": \"application/json\" }, body: JSON.stringify({ extension: \"all\", sync_tree: false }) }); const data = await res.json(); if (data.ok) { alert(`✅ KẾT QUẢ NẠP LẠI TOÀN BỘ:\\n\\n• Thành công: ${data.reloaded_count} extensions\\n• Thất bại: ${data.failed_count} extensions`); showToast(data.message, \"success\"); loadCogsSummary(); } else { let errDetail = (data.failed || []).map(f => `• ${f.extension}: ${f.error}`).join(\"\\n\"); alert(`⚠️ NẠP LẠI CÓ LỖI:\\n\\n${errDetail || data.error}`); showToast(\"Một số Cog nạp lại thất bại\", \"error\"); } } catch (e) { showToast(\"Lỗi kết nối máy chủ\", \"error\"); } } async function syncSlashTree() { if (!confirm(\"Đồng bộ lại cây lệnh Slash Commands (bot.tree.sync()) lên Discord?\")) return; showToast(\"Đang đồng bộ lệnh Slash lên Discord...\"); try { const res = await fetch(\"/api/admin/cogs/sync-tree\", { method: \"POST\" }); const data = await res.json(); if (data.ok) { alert(data.message); showToast(data.message, \"success\"); } else { alert(`❌ Lỗi đồng bộ: ${data.error}`); showToast(\"Lỗi đồng bộ cây lệnh\", \"error\"); } } catch (e) { showToast(\"Lỗi mạng khi đồng bộ lệnh\", \"error\"); } } async function openCogsModal() { document.getElementById(\"cogsModal\").classList.add(\"active\"); const tbody = document.getElementById(\"cogsTableBody\"); tbody.innerHTML = `",
    "cn": "`; showToast(data.error || \"Lỗi truy vấn SQL\", \"error\"); } } catch (e) { statusEl.textContent = \"❌ Lỗi kết nối máy chủ\"; showToast(\"Lỗi kết nối khi gửi truy vấn SQL\", \"error\"); } } function exportCurrentTable(format) { if (!currentTableData || !currentTableData.rows || currentTableData.rows.length === 0) { alert(\"Không có dữ liệu trong bảng để xuất!\"); return; } const filename = `${currentDbTable || 'database'}_data.${format}`; if (format === \"json\") { const jsonStr = JSON.stringify(currentTableData.rows, null, 2); downloadFileBlob(jsonStr, filename, \"application/json\"); } else if (format === \"csv\") { const cols = currentTableData.columns; let csv = cols.map(c => `\"${String(c).replace(/\"/g, '\"\"')}\"`).join(\",\") + \"\\n\"; currentTableData.rows.forEach(row => { const rowVals = cols.map(c => { const v = row[c]; if (v === null || v === undefined) return '\"\"'; return `\"${String(v).replace(/\"/g, '\"\"')}\"`; }); csv += rowVals.join(\",\") + \"\\n\"; }); downloadFileBlob(csv, filename, \"text/csv;charset=utf-8;\"); } } function exportSqlQueryResult() { if (!lastQueryResult || !lastQueryResult.rows) return; const jsonStr = JSON.stringify(lastQueryResult.rows, null, 2); downloadFileBlob(jsonStr, `sql_result_${Date.now()}.json`, \"application/json\"); } function downloadFileBlob(content, filename, mimeType) { const blob = new Blob([content], { type: mimeType }); const url = URL.createObjectURL(blob); const a = document.createElement(\"a\"); a.href = url; a.download = filename; document.body.appendChild(a); a.click(); document.body.removeChild(a); URL.revokeObjectURL(url); showToast(`Đã tải xuống tệp ${filename}!`, \"success\"); } // ========================================== // API CALLS: COG RELOADER // ========================================== async function loadCogsSummary() { try { const res = await fetch(\"/api/admin/cogs/list\"); const data = await res.json(); if (data.ok) { document.getElementById(\"loadedCogsCount\").textContent = `${data.loaded_count}/${data.total_cogs}`; document.getElementById(\"modalCogsTotal\").textContent = data.total_cogs; } } catch (e) {} } async function reloadSpecificCog(extName) { showToast(`Đang nạp lại Cog ${extName}...`); try { const res = await fetch(\"/api/admin/cogs/reload\", { method: \"POST\", headers: { \"Content-Type\": \"application/json\" }, body: JSON.stringify({ extension: extName }) }); const data = await res.json(); if (data.ok) { showToast(data.message || `Đã nạp lại ${extName}!`, \"success\"); loadCogsSummary(); } else { alert(`❌ NẠP LẠI THẤT BẠI:\\n\\n${data.error}`); showToast(`Lỗi nạp lại ${extName}`, \"error\"); } } catch (e) { showToast(\"Lỗi kết nối khi nạp lại Cog\", \"error\"); } } async function reloadAllCogs() { if (!confirm(\"Bạn có chắc chắn muốn nạp lại TOÀN BỘ Cogs của SakuraBot không?\")) { return; } showToast(\"Đang nạp lại toàn bộ Cogs, vui lòng đợi...\"); try { const res = await fetch(\"/api/admin/cogs/reload\", { method: \"POST\", headers: { \"Content-Type\": \"application/json\" }, body: JSON.stringify({ extension: \"all\", sync_tree: false }) }); const data = await res.json(); if (data.ok) { alert(`✅ KẾT QUẢ NẠP LẠI TOÀN BỘ:\\n\\n• Thành công: ${data.reloaded_count} extensions\\n• Thất bại: ${data.failed_count} extensions`); showToast(data.message, \"success\"); loadCogsSummary(); } else { let errDetail = (data.failed || []).map(f => `• ${f.extension}: ${f.error}`).join(\"\\n\"); alert(`⚠️ NẠP LẠI CÓ LỖI:\\n\\n${errDetail || data.error}`); showToast(\"Một số Cog nạp lại thất bại\", \"error\"); } } catch (e) { showToast(\"Lỗi kết nối máy chủ\", \"error\"); } } async function syncSlashTree() { if (!confirm(\"Đồng bộ lại cây lệnh Slash Commands (bot.tree.sync()) lên Discord?\")) return; showToast(\"Đang đồng bộ lệnh Slash lên Discord...\"); try { const res = await fetch(\"/api/admin/cogs/sync-tree\", { method: \"POST\" }); const data = await res.json(); if (data.ok) { alert(data.message); showToast(data.message, \"success\"); } else { alert(`❌ Lỗi đồng bộ: ${data.error}`); showToast(\"Lỗi đồng bộ cây lệnh\", \"error\"); } } catch (e) { showToast(\"Lỗi mạng khi đồng bộ lệnh\", \"error\"); } } async function openCogsModal() { document.getElementById(\"cogsModal\").classList.add(\"active\"); const tbody = document.getElementById(\"cogsTableBody\"); tbody.innerHTML = `"
  },
  "`; try { const url = `/api/admin/database/table-data?path=${encodeURIComponent(currentDbPath)}&table=${encodeURIComponent(tableName)}&limit=${limit}&offset=${offset}&search=${encodeURIComponent(search)}`; const res = await fetch(url); const data = await res.json(); if (data.ok) { currentTableData = data; // Render Schema Pill Bar (An toàn có fallback) schemaBar.innerHTML = \"\"; const colsList = data.schema || (currentDbSchema && currentDbSchema.tables ? (currentDbSchema.tables.find(t => t.name === tableName)?.columns || []) : []); if (colsList && colsList.length) { colsList.forEach(col => { const pill = document.createElement(\"span\"); pill.className = \"bf-col-pill\" + (col.pk ? \" pk\" : \"\"); pill.innerHTML = `": {
    "en": "`; try { const url = `/api/admin/database/table-data?path=${encodeURIComponent(currentDbPath)}&table=${encodeURIComponent(tableName)}&limit=${limit}&offset=${offset}&search=${encodeURIComponent(search)}`; const res = await fetch(url); const data = await res.json(); if (data.ok) { currentTableData = data; // Render Schema Pill Bar (An toàn có fallback) schemaBar.innerHTML = \"\"; const colsList = data.schema || (currentDbSchema && currentDbSchema.tables ? (currentDbSchema.tables.find(t => t.name === tableName)?.columns || []) : []); if (colsList && colsList.length) { colsList.forEach(col => { const pill = document.createElement(\"span\"); pill.className = \"bf-col-pill\" + (col.pk ? \" pk\" : \"\"); pill.innerHTML = `",
    "ja": "`; try { const url = `/api/admin/database/table-data?path=${encodeURIComponent(currentDbPath)}&table=${encodeURIComponent(tableName)}&limit=${limit}&offset=${offset}&search=${encodeURIComponent(search)}`; const res = await fetch(url); const data = await res.json(); if (data.ok) { currentTableData = data; // Render Schema Pill Bar (An toàn có fallback) schemaBar.innerHTML = \"\"; const colsList = data.schema || (currentDbSchema && currentDbSchema.tables ? (currentDbSchema.tables.find(t => t.name === tableName)?.columns || []) : []); if (colsList && colsList.length) { colsList.forEach(col => { const pill = document.createElement(\"span\"); pill.className = \"bf-col-pill\" + (col.pk ? \" pk\" : \"\"); pill.innerHTML = `",
    "cn": "`; try { const url = `/api/admin/database/table-data?path=${encodeURIComponent(currentDbPath)}&table=${encodeURIComponent(tableName)}&limit=${limit}&offset=${offset}&search=${encodeURIComponent(search)}`; const res = await fetch(url); const data = await res.json(); if (data.ok) { currentTableData = data; // Render Schema Pill Bar (An toàn có fallback) schemaBar.innerHTML = \"\"; const colsList = data.schema || (currentDbSchema && currentDbSchema.tables ? (currentDbSchema.tables.find(t => t.name === tableName)?.columns || []) : []); if (colsList && colsList.length) { colsList.forEach(col => { const pill = document.createElement(\"span\"); pill.className = \"bf-col-pill\" + (col.pk ? \" pk\" : \"\"); pill.innerHTML = `"
  },
  "`; } } function closeCogsModal() { document.getElementById(\"cogsModal\").classList.remove(\"active\"); } // ========================================== // CREATE / DELETE / RENAME / UPLOAD // ========================================== async function promptCreateFile(isDir) { const typeLabel = isDir ? \"Thư mục\" : \"Tệp tin\"; const name = prompt(`Nhập tên ${typeLabel} mới cần tạo trong ${currentPath || \"thư mục gốc\"}:`); if (!name) return; try { const res = await fetch(\"/api/admin/bot-files/create\", { method: \"POST\", headers: { \"Content-Type\": \"application/json\" }, body: JSON.stringify({ path: currentPath, name: name, is_dir: isDir }) }); const data = await res.json(); if (data.ok) { showToast(data.message, \"success\"); loadDirectory(currentPath); } else { alert(`❌ ${data.error}`); } } catch (e) { showToast(\"Lỗi khi tạo\", \"error\"); } } async function promptDelete(relPath, isDir) { const typeLabel = isDir ? \"thư mục\" : \"tệp\"; if (!confirm(`Bạn có chắc chắn muốn xóa vĩnh viễn ${typeLabel} [${relPath}] không? Thao tác này không thể hoàn tác!`)) { return; } try { const res = await fetch(\"/api/admin/bot-files/delete\", { method: \"POST\", headers: { \"Content-Type\": \"application/json\" }, body: JSON.stringify({ path: relPath }) }); const data = await res.json(); if (data.ok) { showToast(data.message, \"success\"); if (activeFilePath === relPath) { activeFilePath = \"\"; setEditorContent(\"\", \".txt\"); document.getElementById(\"editorFilePath\").textContent = \"Chưa mở tệp nào\"; document.getElementById(\"cogBanner\").style.display = \"none\"; } if (currentDbPath === relPath) { closeDatabaseView(); } loadDirectory(currentPath); } else { alert(`❌ ${data.error}`); } } catch (e) { showToast(\"Lỗi khi xóa\", \"error\"); } } async function promptRename(relPath, oldName) { const newName = prompt(`Nhập tên mới cho [${oldName}]:`, oldName); if (!newName || newName === oldName) return; try { const res = await fetch(\"/api/admin/bot-files/rename\", { method: \"POST\", headers: { \"Content-Type\": \"application/json\" }, body: JSON.stringify({ path: relPath, new_name: newName }) }); const data = await res.json(); if (data.ok) { showToast(data.message, \"success\"); if (activeFilePath === relPath) { activeFilePath = data.path; document.getElementById(\"editorFilePath\").textContent = data.path; } if (currentDbPath === relPath) { currentDbPath = data.path; document.getElementById(\"dbFilePath\").textContent = data.path; } loadDirectory(currentPath); } else { alert(`❌ ${data.error}`); } } catch (e) { showToast(\"Lỗi khi đổi tên\", \"error\"); } } async function uploadFiles(files) { if (!files || files.length === 0) return; const formData = new FormData(); formData.append(\"path\", currentPath); for (let i = 0; i": {
    "en": "`; } } function closeCogsModal() { document.getElementById(\"cogsModal\").classList.remove(\"active\"); } // ========================================== // CREATE / DELETE / RENAME / UPLOAD // ========================================== async function promptCreateFile(isDir) { const typeLabel = isDir ? \"Thư mục\" : \"Tệp tin\"; const name = prompt(`Nhập tên ${typeLabel} mới cần tạo trong ${currentPath || \"thư mục gốc\"}:`); if (!name) return; try { const res = await fetch(\"/api/admin/bot-files/create\", { method: \"POST\", headers: { \"Content-Type\": \"application/json\" }, body: JSON.stringify({ path: currentPath, name: name, is_dir: isDir }) }); const data = await res.json(); if (data.ok) { showToast(data.message, \"success\"); loadDirectory(currentPath); } else { alert(`❌ ${data.error}`); } } catch (e) { showToast(\"Lỗi khi tạo\", \"error\"); } } async function promptDelete(relPath, isDir) { const typeLabel = isDir ? \"thư mục\" : \"tệp\"; if (!confirm(`Bạn có chắc chắn muốn xóa vĩnh viễn ${typeLabel} [${relPath}] không? Thao tác này không thể hoàn tác!`)) { return; } try { const res = await fetch(\"/api/admin/bot-files/delete\", { method: \"POST\", headers: { \"Content-Type\": \"application/json\" }, body: JSON.stringify({ path: relPath }) }); const data = await res.json(); if (data.ok) { showToast(data.message, \"success\"); if (activeFilePath === relPath) { activeFilePath = \"\"; setEditorContent(\"\", \".txt\"); document.getElementById(\"editorFilePath\").textContent = \"Chưa mở tệp nào\"; document.getElementById(\"cogBanner\").style.display = \"none\"; } if (currentDbPath === relPath) { closeDatabaseView(); } loadDirectory(currentPath); } else { alert(`❌ ${data.error}`); } } catch (e) { showToast(\"Lỗi khi xóa\", \"error\"); } } async function promptRename(relPath, oldName) { const newName = prompt(`Nhập tên mới cho [${oldName}]:`, oldName); if (!newName || newName === oldName) return; try { const res = await fetch(\"/api/admin/bot-files/rename\", { method: \"POST\", headers: { \"Content-Type\": \"application/json\" }, body: JSON.stringify({ path: relPath, new_name: newName }) }); const data = await res.json(); if (data.ok) { showToast(data.message, \"success\"); if (activeFilePath === relPath) { activeFilePath = data.path; document.getElementById(\"editorFilePath\").textContent = data.path; } if (currentDbPath === relPath) { currentDbPath = data.path; document.getElementById(\"dbFilePath\").textContent = data.path; } loadDirectory(currentPath); } else { alert(`❌ ${data.error}`); } } catch (e) { showToast(\"Lỗi khi đổi tên\", \"error\"); } } async function uploadFiles(files) { if (!files || files.length === 0) return; const formData = new FormData(); formData.append(\"path\", currentPath); for (let i = 0; i",
    "ja": "`; } } function closeCogsModal() { document.getElementById(\"cogsModal\").classList.remove(\"active\"); } // ========================================== // CREATE / DELETE / RENAME / UPLOAD // ========================================== async function promptCreateFile(isDir) { const typeLabel = isDir ? \"Thư mục\" : \"Tệp tin\"; const name = prompt(`Nhập tên ${typeLabel} mới cần tạo trong ${currentPath || \"thư mục gốc\"}:`); if (!name) return; try { const res = await fetch(\"/api/admin/bot-files/create\", { method: \"POST\", headers: { \"Content-Type\": \"application/json\" }, body: JSON.stringify({ path: currentPath, name: name, is_dir: isDir }) }); const data = await res.json(); if (data.ok) { showToast(data.message, \"success\"); loadDirectory(currentPath); } else { alert(`❌ ${data.error}`); } } catch (e) { showToast(\"Lỗi khi tạo\", \"error\"); } } async function promptDelete(relPath, isDir) { const typeLabel = isDir ? \"thư mục\" : \"tệp\"; if (!confirm(`Bạn có chắc chắn muốn xóa vĩnh viễn ${typeLabel} [${relPath}] không? Thao tác này không thể hoàn tác!`)) { return; } try { const res = await fetch(\"/api/admin/bot-files/delete\", { method: \"POST\", headers: { \"Content-Type\": \"application/json\" }, body: JSON.stringify({ path: relPath }) }); const data = await res.json(); if (data.ok) { showToast(data.message, \"success\"); if (activeFilePath === relPath) { activeFilePath = \"\"; setEditorContent(\"\", \".txt\"); document.getElementById(\"editorFilePath\").textContent = \"Chưa mở tệp nào\"; document.getElementById(\"cogBanner\").style.display = \"none\"; } if (currentDbPath === relPath) { closeDatabaseView(); } loadDirectory(currentPath); } else { alert(`❌ ${data.error}`); } } catch (e) { showToast(\"Lỗi khi xóa\", \"error\"); } } async function promptRename(relPath, oldName) { const newName = prompt(`Nhập tên mới cho [${oldName}]:`, oldName); if (!newName || newName === oldName) return; try { const res = await fetch(\"/api/admin/bot-files/rename\", { method: \"POST\", headers: { \"Content-Type\": \"application/json\" }, body: JSON.stringify({ path: relPath, new_name: newName }) }); const data = await res.json(); if (data.ok) { showToast(data.message, \"success\"); if (activeFilePath === relPath) { activeFilePath = data.path; document.getElementById(\"editorFilePath\").textContent = data.path; } if (currentDbPath === relPath) { currentDbPath = data.path; document.getElementById(\"dbFilePath\").textContent = data.path; } loadDirectory(currentPath); } else { alert(`❌ ${data.error}`); } } catch (e) { showToast(\"Lỗi khi đổi tên\", \"error\"); } } async function uploadFiles(files) { if (!files || files.length === 0) return; const formData = new FormData(); formData.append(\"path\", currentPath); for (let i = 0; i",
    "cn": "`; } } function closeCogsModal() { document.getElementById(\"cogsModal\").classList.remove(\"active\"); } // ========================================== // CREATE / DELETE / RENAME / UPLOAD // ========================================== async function promptCreateFile(isDir) { const typeLabel = isDir ? \"Thư mục\" : \"Tệp tin\"; const name = prompt(`Nhập tên ${typeLabel} mới cần tạo trong ${currentPath || \"thư mục gốc\"}:`); if (!name) return; try { const res = await fetch(\"/api/admin/bot-files/create\", { method: \"POST\", headers: { \"Content-Type\": \"application/json\" }, body: JSON.stringify({ path: currentPath, name: name, is_dir: isDir }) }); const data = await res.json(); if (data.ok) { showToast(data.message, \"success\"); loadDirectory(currentPath); } else { alert(`❌ ${data.error}`); } } catch (e) { showToast(\"Lỗi khi tạo\", \"error\"); } } async function promptDelete(relPath, isDir) { const typeLabel = isDir ? \"thư mục\" : \"tệp\"; if (!confirm(`Bạn có chắc chắn muốn xóa vĩnh viễn ${typeLabel} [${relPath}] không? Thao tác này không thể hoàn tác!`)) { return; } try { const res = await fetch(\"/api/admin/bot-files/delete\", { method: \"POST\", headers: { \"Content-Type\": \"application/json\" }, body: JSON.stringify({ path: relPath }) }); const data = await res.json(); if (data.ok) { showToast(data.message, \"success\"); if (activeFilePath === relPath) { activeFilePath = \"\"; setEditorContent(\"\", \".txt\"); document.getElementById(\"editorFilePath\").textContent = \"Chưa mở tệp nào\"; document.getElementById(\"cogBanner\").style.display = \"none\"; } if (currentDbPath === relPath) { closeDatabaseView(); } loadDirectory(currentPath); } else { alert(`❌ ${data.error}`); } } catch (e) { showToast(\"Lỗi khi xóa\", \"error\"); } } async function promptRename(relPath, oldName) { const newName = prompt(`Nhập tên mới cho [${oldName}]:`, oldName); if (!newName || newName === oldName) return; try { const res = await fetch(\"/api/admin/bot-files/rename\", { method: \"POST\", headers: { \"Content-Type\": \"application/json\" }, body: JSON.stringify({ path: relPath, new_name: newName }) }); const data = await res.json(); if (data.ok) { showToast(data.message, \"success\"); if (activeFilePath === relPath) { activeFilePath = data.path; document.getElementById(\"editorFilePath\").textContent = data.path; } if (currentDbPath === relPath) { currentDbPath = data.path; document.getElementById(\"dbFilePath\").textContent = data.path; } loadDirectory(currentPath); } else { alert(`❌ ${data.error}`); } } catch (e) { showToast(\"Lỗi khi đổi tên\", \"error\"); } } async function uploadFiles(files) { if (!files || files.length === 0) return; const formData = new FormData(); formData.append(\"path\", currentPath); for (let i = 0; i"
  },
  "`; } } function searchCurrentTable() { const kw = document.getElementById(\"dbSearchInput\").value.trim(); loadDatabaseTable(currentDbTable, 1, kw); } function clearDbSearch() { document.getElementById(\"dbSearchInput\").value = \"\"; loadDatabaseTable(currentDbTable, 1, \"\"); } function changeDbPage(delta) { const newPage = dbCurrentPage + delta; if (newPage >= 1) { loadDatabaseTable(currentDbTable, newPage, dbSearchKeyword); } } function goToDbPage(target) { if (!currentTableData) return; const totalPages = Math.max(1, Math.ceil(currentTableData.total_rows / dbPageSize)); if (target === \"last\") { loadDatabaseTable(currentDbTable, totalPages, dbSearchKeyword); } else { const pageNum = parseInt(target, 10) || 1; loadDatabaseTable(currentDbTable, Math.max(1, Math.min(pageNum, totalPages)), dbSearchKeyword); } } function changeDbPageSize(val) { dbPageSize = parseInt(val, 10) || 50; loadDatabaseTable(currentDbTable, 1, dbSearchKeyword); } function switchDbTab(tab) { const tableTab = document.getElementById(\"dbTableTab\"); const sqlTab = document.getElementById(\"dbSqlTab\"); const btnTable = document.getElementById(\"dbTabBtnTable\"); const btnSql = document.getElementById(\"dbTabBtnSql\"); if (tab === \"table\") { tableTab.style.display = \"flex\"; sqlTab.style.display = \"none\"; btnTable.classList.add(\"active\"); btnSql.classList.remove(\"active\"); } else { tableTab.style.display = \"none\"; sqlTab.style.display = \"flex\"; btnTable.classList.remove(\"active\"); btnSql.classList.add(\"active\"); } } function insertSqlSample(sampleId) { const t = currentDbTable || \"sqlite_master\"; if (sampleId === 1) { document.getElementById(\"dbSqlInput\").value = `SELECT * FROM \"${t}\" LIMIT 20;`; } else if (sampleId === 2) { document.getElementById(\"dbSqlInput\").value = `SELECT count(*) AS total_rows FROM \"${t}\";`; } else if (sampleId === 3) { document.getElementById(\"dbSqlInput\").value = `SELECT name, type FROM sqlite_master WHERE type IN ('table', 'view') ORDER BY name;`; } } async function runDbSqlQuery() { if (!currentDbPath) return; const query = document.getElementById(\"dbSqlInput\").value.trim(); if (!query) { showToast(\"Vui lòng nhập câu lệnh SQL\", \"error\"); return; } const statusEl = document.getElementById(\"dbSqlStatus\"); const thead = document.getElementById(\"dbSqlTableHead\"); const tbody = document.getElementById(\"dbSqlTableBody\"); const exportBtn = document.getElementById(\"dbSqlExportBtn\"); statusEl.textContent = \"⏳ Đang thực thi truy vấn SQL...\"; tbody.innerHTML = `": {
    "en": "`; } } function searchCurrentTable() { const kw = document.getElementById(\"dbSearchInput\").value.trim(); loadDatabaseTable(currentDbTable, 1, kw); } function clearDbSearch() { document.getElementById(\"dbSearchInput\").value = \"\"; loadDatabaseTable(currentDbTable, 1, \"\"); } function changeDbPage(delta) { const newPage = dbCurrentPage + delta; if (newPage >= 1) { loadDatabaseTable(currentDbTable, newPage, dbSearchKeyword); } } function goToDbPage(target) { if (!currentTableData) return; const totalPages = Math.max(1, Math.ceil(currentTableData.total_rows / dbPageSize)); if (target === \"last\") { loadDatabaseTable(currentDbTable, totalPages, dbSearchKeyword); } else { const pageNum = parseInt(target, 10) || 1; loadDatabaseTable(currentDbTable, Math.max(1, Math.min(pageNum, totalPages)), dbSearchKeyword); } } function changeDbPageSize(val) { dbPageSize = parseInt(val, 10) || 50; loadDatabaseTable(currentDbTable, 1, dbSearchKeyword); } function switchDbTab(tab) { const tableTab = document.getElementById(\"dbTableTab\"); const sqlTab = document.getElementById(\"dbSqlTab\"); const btnTable = document.getElementById(\"dbTabBtnTable\"); const btnSql = document.getElementById(\"dbTabBtnSql\"); if (tab === \"table\") { tableTab.style.display = \"flex\"; sqlTab.style.display = \"none\"; btnTable.classList.add(\"active\"); btnSql.classList.remove(\"active\"); } else { tableTab.style.display = \"none\"; sqlTab.style.display = \"flex\"; btnTable.classList.remove(\"active\"); btnSql.classList.add(\"active\"); } } function insertSqlSample(sampleId) { const t = currentDbTable || \"sqlite_master\"; if (sampleId === 1) { document.getElementById(\"dbSqlInput\").value = `SELECT * FROM \"${t}\" LIMIT 20;`; } else if (sampleId === 2) { document.getElementById(\"dbSqlInput\").value = `SELECT count(*) AS total_rows FROM \"${t}\";`; } else if (sampleId === 3) { document.getElementById(\"dbSqlInput\").value = `SELECT name, type FROM sqlite_master WHERE type IN ('table', 'view') ORDER BY name;`; } } async function runDbSqlQuery() { if (!currentDbPath) return; const query = document.getElementById(\"dbSqlInput\").value.trim(); if (!query) { showToast(\"Vui lòng nhập câu lệnh SQL\", \"error\"); return; } const statusEl = document.getElementById(\"dbSqlStatus\"); const thead = document.getElementById(\"dbSqlTableHead\"); const tbody = document.getElementById(\"dbSqlTableBody\"); const exportBtn = document.getElementById(\"dbSqlExportBtn\"); statusEl.textContent = \"⏳ Đang thực thi truy vấn SQL...\"; tbody.innerHTML = `",
    "ja": "`; } } function searchCurrentTable() { const kw = document.getElementById(\"dbSearchInput\").value.trim(); loadDatabaseTable(currentDbTable, 1, kw); } function clearDbSearch() { document.getElementById(\"dbSearchInput\").value = \"\"; loadDatabaseTable(currentDbTable, 1, \"\"); } function changeDbPage(delta) { const newPage = dbCurrentPage + delta; if (newPage >= 1) { loadDatabaseTable(currentDbTable, newPage, dbSearchKeyword); } } function goToDbPage(target) { if (!currentTableData) return; const totalPages = Math.max(1, Math.ceil(currentTableData.total_rows / dbPageSize)); if (target === \"last\") { loadDatabaseTable(currentDbTable, totalPages, dbSearchKeyword); } else { const pageNum = parseInt(target, 10) || 1; loadDatabaseTable(currentDbTable, Math.max(1, Math.min(pageNum, totalPages)), dbSearchKeyword); } } function changeDbPageSize(val) { dbPageSize = parseInt(val, 10) || 50; loadDatabaseTable(currentDbTable, 1, dbSearchKeyword); } function switchDbTab(tab) { const tableTab = document.getElementById(\"dbTableTab\"); const sqlTab = document.getElementById(\"dbSqlTab\"); const btnTable = document.getElementById(\"dbTabBtnTable\"); const btnSql = document.getElementById(\"dbTabBtnSql\"); if (tab === \"table\") { tableTab.style.display = \"flex\"; sqlTab.style.display = \"none\"; btnTable.classList.add(\"active\"); btnSql.classList.remove(\"active\"); } else { tableTab.style.display = \"none\"; sqlTab.style.display = \"flex\"; btnTable.classList.remove(\"active\"); btnSql.classList.add(\"active\"); } } function insertSqlSample(sampleId) { const t = currentDbTable || \"sqlite_master\"; if (sampleId === 1) { document.getElementById(\"dbSqlInput\").value = `SELECT * FROM \"${t}\" LIMIT 20;`; } else if (sampleId === 2) { document.getElementById(\"dbSqlInput\").value = `SELECT count(*) AS total_rows FROM \"${t}\";`; } else if (sampleId === 3) { document.getElementById(\"dbSqlInput\").value = `SELECT name, type FROM sqlite_master WHERE type IN ('table', 'view') ORDER BY name;`; } } async function runDbSqlQuery() { if (!currentDbPath) return; const query = document.getElementById(\"dbSqlInput\").value.trim(); if (!query) { showToast(\"Vui lòng nhập câu lệnh SQL\", \"error\"); return; } const statusEl = document.getElementById(\"dbSqlStatus\"); const thead = document.getElementById(\"dbSqlTableHead\"); const tbody = document.getElementById(\"dbSqlTableBody\"); const exportBtn = document.getElementById(\"dbSqlExportBtn\"); statusEl.textContent = \"⏳ Đang thực thi truy vấn SQL...\"; tbody.innerHTML = `",
    "cn": "`; } } function searchCurrentTable() { const kw = document.getElementById(\"dbSearchInput\").value.trim(); loadDatabaseTable(currentDbTable, 1, kw); } function clearDbSearch() { document.getElementById(\"dbSearchInput\").value = \"\"; loadDatabaseTable(currentDbTable, 1, \"\"); } function changeDbPage(delta) { const newPage = dbCurrentPage + delta; if (newPage >= 1) { loadDatabaseTable(currentDbTable, newPage, dbSearchKeyword); } } function goToDbPage(target) { if (!currentTableData) return; const totalPages = Math.max(1, Math.ceil(currentTableData.total_rows / dbPageSize)); if (target === \"last\") { loadDatabaseTable(currentDbTable, totalPages, dbSearchKeyword); } else { const pageNum = parseInt(target, 10) || 1; loadDatabaseTable(currentDbTable, Math.max(1, Math.min(pageNum, totalPages)), dbSearchKeyword); } } function changeDbPageSize(val) { dbPageSize = parseInt(val, 10) || 50; loadDatabaseTable(currentDbTable, 1, dbSearchKeyword); } function switchDbTab(tab) { const tableTab = document.getElementById(\"dbTableTab\"); const sqlTab = document.getElementById(\"dbSqlTab\"); const btnTable = document.getElementById(\"dbTabBtnTable\"); const btnSql = document.getElementById(\"dbTabBtnSql\"); if (tab === \"table\") { tableTab.style.display = \"flex\"; sqlTab.style.display = \"none\"; btnTable.classList.add(\"active\"); btnSql.classList.remove(\"active\"); } else { tableTab.style.display = \"none\"; sqlTab.style.display = \"flex\"; btnTable.classList.remove(\"active\"); btnSql.classList.add(\"active\"); } } function insertSqlSample(sampleId) { const t = currentDbTable || \"sqlite_master\"; if (sampleId === 1) { document.getElementById(\"dbSqlInput\").value = `SELECT * FROM \"${t}\" LIMIT 20;`; } else if (sampleId === 2) { document.getElementById(\"dbSqlInput\").value = `SELECT count(*) AS total_rows FROM \"${t}\";`; } else if (sampleId === 3) { document.getElementById(\"dbSqlInput\").value = `SELECT name, type FROM sqlite_master WHERE type IN ('table', 'view') ORDER BY name;`; } } async function runDbSqlQuery() { if (!currentDbPath) return; const query = document.getElementById(\"dbSqlInput\").value.trim(); if (!query) { showToast(\"Vui lòng nhập câu lệnh SQL\", \"error\"); return; } const statusEl = document.getElementById(\"dbSqlStatus\"); const thead = document.getElementById(\"dbSqlTableHead\"); const tbody = document.getElementById(\"dbSqlTableBody\"); const exportBtn = document.getElementById(\"dbSqlExportBtn\"); statusEl.textContent = \"⏳ Đang thực thi truy vấn SQL...\"; tbody.innerHTML = `"
  },
  "`; }); tbody.innerHTML = tbHtml; } // Cập nhật Pagination & Stats const totalRows = data.total_rows || 0; const totalPages = Math.max(1, Math.ceil(totalRows / dbPageSize)); const startIdx = totalRows === 0 ? 0 : offset + 1; const endIdx = Math.min(offset + rows.length, totalRows); document.getElementById(\"dbRowStats\").textContent = `${totalRows.toLocaleString()} dòng`; document.getElementById(\"dbPaginationInfo\").textContent = `Dòng ${startIdx.toLocaleString()} - ${endIdx.toLocaleString()} trong tổng số ${totalRows.toLocaleString()} dòng`; document.getElementById(\"dbCurrentPageBadge\").textContent = `Trang ${page} / ${totalPages}`; document.getElementById(\"dbFirstBtn\").disabled = page": {
    "en": "`; }); tbody.innerHTML = tbHtml; } // Cập nhật Pagination & Stats const totalRows = data.total_rows || 0; const totalPages = Math.max(1, Math.ceil(totalRows / dbPageSize)); const startIdx = totalRows === 0 ? 0 : offset + 1; const endIdx = Math.min(offset + rows.length, totalRows); document.getElementById(\"dbRowStats\").textContent = `${totalRows.toLocaleString()} dòng`; document.getElementById(\"dbPaginationInfo\").textContent = `Dòng ${startIdx.toLocaleString()} - ${endIdx.toLocaleString()} trong tổng số ${totalRows.toLocaleString()} dòng`; document.getElementById(\"dbCurrentPageBadge\").textContent = `Trang ${page} / ${totalPages}`; document.getElementById(\"dbFirstBtn\").disabled = page",
    "ja": "`; }); tbody.innerHTML = tbHtml; } // Cập nhật Pagination & Stats const totalRows = data.total_rows || 0; const totalPages = Math.max(1, Math.ceil(totalRows / dbPageSize)); const startIdx = totalRows === 0 ? 0 : offset + 1; const endIdx = Math.min(offset + rows.length, totalRows); document.getElementById(\"dbRowStats\").textContent = `${totalRows.toLocaleString()} dòng`; document.getElementById(\"dbPaginationInfo\").textContent = `Dòng ${startIdx.toLocaleString()} - ${endIdx.toLocaleString()} trong tổng số ${totalRows.toLocaleString()} dòng`; document.getElementById(\"dbCurrentPageBadge\").textContent = `Trang ${page} / ${totalPages}`; document.getElementById(\"dbFirstBtn\").disabled = page",
    "cn": "`; }); tbody.innerHTML = tbHtml; } // Cập nhật Pagination & Stats const totalRows = data.total_rows || 0; const totalPages = Math.max(1, Math.ceil(totalRows / dbPageSize)); const startIdx = totalRows === 0 ? 0 : offset + 1; const endIdx = Math.min(offset + rows.length, totalRows); document.getElementById(\"dbRowStats\").textContent = `${totalRows.toLocaleString()} dòng`; document.getElementById(\"dbPaginationInfo\").textContent = `Dòng ${startIdx.toLocaleString()} - ${endIdx.toLocaleString()} trong tổng số ${totalRows.toLocaleString()} dòng`; document.getElementById(\"dbCurrentPageBadge\").textContent = `Trang ${page} / ${totalPages}`; document.getElementById(\"dbFirstBtn\").disabled = page"
  },
  "`; }); tbody.innerHTML = tbHtml; } showToast(`Truy vấn SQL thành công (${data.rows.length} dòng)`, \"success\"); } else { statusEl.innerHTML = `❌": {
    "en": "`; }); tbody.innerHTML = tbHtml; } showToast(`Truy vấn SQL thành công (${data.rows.length} dòng)`, \"success\"); } else { statusEl.innerHTML = `❌",
    "ja": "`; }); tbody.innerHTML = tbHtml; } showToast(`Truy vấn SQL thành công (${data.rows.length} dòng)`, \"success\"); } else { statusEl.innerHTML = `❌",
    "cn": "`; }); tbody.innerHTML = tbHtml; } showToast(`Truy vấn SQL thành công (${data.rows.length} dòng)`, \"success\"); } else { statusEl.innerHTML = `❌"
  },
  "câu": {
    "en": "câu",
    "ja": "câu",
    "cn": "câu"
  },
  "hạ cấp Người Dùng Thường": {
    "en": "hạ cấp Người Dùng Thường",
    "ja": "hạ cấp Người Dùng Thường",
    "cn": "hạ cấp Người Dùng Thường"
  },
  "linh béo": {
    "en": "linh béo",
    "ja": "linh béo",
    "cn": "linh béo"
  },
  "navigatePath(\"\"); bar.appendChild(rootSpan); if (!p) return; const parts = p.split(\"/\"); let accum = \"\"; parts.forEach(part => { accum += (accum ? \"/\" : \"\") + part; const curAccum = accum; const sep = document.createTextNode(\" / \"); bar.appendChild(sep); const link = document.createElement(\"span\"); link.className = \"bf-crumb-link\"; link.textContent = part; link.onclick = () => navigatePath(curAccum); bar.appendChild(link); }); } function updateTabHighlight(p) { document.querySelectorAll(\".bf-tab-btn\").forEach(btn => { const txt = btn.textContent.trim(); if (!p && txt.includes(\"Tất Cả\")) btn.classList.add(\"active\"); else if (p && txt.includes(p.split(\"/\")[0])) btn.classList.add(\"active\"); else btn.classList.remove(\"active\"); }); } function filterFiles(keyword) { const kw = (keyword || \"\").toLowerCase(); document.querySelectorAll(\".bf-file-item\").forEach(item => { const nameEl = item.querySelector(\".bf-item-name\"); if (nameEl) { const name = nameEl.textContent.toLowerCase(); item.style.display = name.includes(kw) ? \"flex\" : \"none\"; } }); } async function loadBotStatus() { try { const res = await fetch(\"/api/bot/status\"); const data = await res.json(); const pill = document.getElementById(\"botStatusPill\"); const text = document.getElementById(\"botStatusText\"); if (data.running) { text.textContent = `Bot Online (${data.username || \"Sakura\"})`; pill.style.borderColor = \"rgba(80, 250, 123, 0.4)\"; } else { text.textContent = \"Bot Offline\"; pill.style.borderColor = \"rgba(255, 85, 85, 0.4)\"; pill.querySelector(\"span\").textContent = \"🔴\"; } } catch (e) {} } function getFileIcon(ext) { const icons = { \".py\": \"🐍\", \".json\": \"📋\", \".html\": \"🌐\", \".css\": \"🎨\", \".js\": \"📜\", \".txt\": \"📄\", \".md\": \"📝\", \".yml\": \"⚙️\", \".yaml\": \"⚙️\", \".env\": \"🔒\", \".log\": \"📰\", \".db\": \"🗄️\", \".sqlite\": \"🗄️\", \".sqlite3\": \"🗄️\", \".sql\": \"💾\", \".png\": \"🖼️\", \".jpg\": \"🖼️\", \".jpeg\": \"🖼️\", \".webp\": \"🖼️\", \".svg\": \"🎨\", \".ico\": \"🎯\", \".bmp\": \"🖼️\", \".avif\": \"🖼️\", \".gif\": \"🎞️\", \".mp4\": \"🎬\", \".webm\": \"🎬\", \".mov\": \"🎬\", \".mkv\": \"🎬\", \".avi\": \"🎬\", \".mp3\": \"🎵\", \".wav\": \"🎵\", \".ogg\": \"🎵\", \".m4a\": \"🎵\", \".flac\": \"🎵\" }; return icons[ext] || \"📄\"; } function formatBytes(bytes) { if (!bytes || bytes": {
    "en": "navigatePath(\"\"); bar.appendChild(rootSpan); if (!p) return; const parts = p.split(\"/\"); let accum = \"\"; parts.forEach(part => { accum += (accum ? \"/\" : \"\") + part; const curAccum = accum; const sep = document.createTextNode(\" / \"); bar.appendChild(sep); const link = document.createElement(\"span\"); link.className = \"bf-crumb-link\"; link.textContent = part; link.onclick = () => navigatePath(curAccum); bar.appendChild(link); }); } function updateTabHighlight(p) { document.querySelectorAll(\".bf-tab-btn\").forEach(btn => { const txt = btn.textContent.trim(); if (!p && txt.includes(\"Tất Cả\")) btn.classList.add(\"active\"); else if (p && txt.includes(p.split(\"/\")[0])) btn.classList.add(\"active\"); else btn.classList.remove(\"active\"); }); } function filterFiles(keyword) { const kw = (keyword || \"\").toLowerCase(); document.querySelectorAll(\".bf-file-item\").forEach(item => { const nameEl = item.querySelector(\".bf-item-name\"); if (nameEl) { const name = nameEl.textContent.toLowerCase(); item.style.display = name.includes(kw) ? \"flex\" : \"none\"; } }); } async function loadBotStatus() { try { const res = await fetch(\"/api/bot/status\"); const data = await res.json(); const pill = document.getElementById(\"botStatusPill\"); const text = document.getElementById(\"botStatusText\"); if (data.running) { text.textContent = `Bot Online (${data.username || \"Sakura\"})`; pill.style.borderColor = \"rgba(80, 250, 123, 0.4)\"; } else { text.textContent = \"Bot Offline\"; pill.style.borderColor = \"rgba(255, 85, 85, 0.4)\"; pill.querySelector(\"span\").textContent = \"🔴\"; } } catch (e) {} } function getFileIcon(ext) { const icons = { \".py\": \"🐍\", \".json\": \"📋\", \".html\": \"🌐\", \".css\": \"🎨\", \".js\": \"📜\", \".txt\": \"📄\", \".md\": \"📝\", \".yml\": \"⚙️\", \".yaml\": \"⚙️\", \".env\": \"🔒\", \".log\": \"📰\", \".db\": \"🗄️\", \".sqlite\": \"🗄️\", \".sqlite3\": \"🗄️\", \".sql\": \"💾\", \".png\": \"🖼️\", \".jpg\": \"🖼️\", \".jpeg\": \"🖼️\", \".webp\": \"🖼️\", \".svg\": \"🎨\", \".ico\": \"🎯\", \".bmp\": \"🖼️\", \".avif\": \"🖼️\", \".gif\": \"🎞️\", \".mp4\": \"🎬\", \".webm\": \"🎬\", \".mov\": \"🎬\", \".mkv\": \"🎬\", \".avi\": \"🎬\", \".mp3\": \"🎵\", \".wav\": \"🎵\", \".ogg\": \"🎵\", \".m4a\": \"🎵\", \".flac\": \"🎵\" }; return icons[ext] || \"📄\"; } function formatBytes(bytes) { if (!bytes || bytes",
    "ja": "navigatePath(\"\"); bar.appendChild(rootSpan); if (!p) return; const parts = p.split(\"/\"); let accum = \"\"; parts.forEach(part => { accum += (accum ? \"/\" : \"\") + part; const curAccum = accum; const sep = document.createTextNode(\" / \"); bar.appendChild(sep); const link = document.createElement(\"span\"); link.className = \"bf-crumb-link\"; link.textContent = part; link.onclick = () => navigatePath(curAccum); bar.appendChild(link); }); } function updateTabHighlight(p) { document.querySelectorAll(\".bf-tab-btn\").forEach(btn => { const txt = btn.textContent.trim(); if (!p && txt.includes(\"Tất Cả\")) btn.classList.add(\"active\"); else if (p && txt.includes(p.split(\"/\")[0])) btn.classList.add(\"active\"); else btn.classList.remove(\"active\"); }); } function filterFiles(keyword) { const kw = (keyword || \"\").toLowerCase(); document.querySelectorAll(\".bf-file-item\").forEach(item => { const nameEl = item.querySelector(\".bf-item-name\"); if (nameEl) { const name = nameEl.textContent.toLowerCase(); item.style.display = name.includes(kw) ? \"flex\" : \"none\"; } }); } async function loadBotStatus() { try { const res = await fetch(\"/api/bot/status\"); const data = await res.json(); const pill = document.getElementById(\"botStatusPill\"); const text = document.getElementById(\"botStatusText\"); if (data.running) { text.textContent = `Bot Online (${data.username || \"Sakura\"})`; pill.style.borderColor = \"rgba(80, 250, 123, 0.4)\"; } else { text.textContent = \"Bot Offline\"; pill.style.borderColor = \"rgba(255, 85, 85, 0.4)\"; pill.querySelector(\"span\").textContent = \"🔴\"; } } catch (e) {} } function getFileIcon(ext) { const icons = { \".py\": \"🐍\", \".json\": \"📋\", \".html\": \"🌐\", \".css\": \"🎨\", \".js\": \"📜\", \".txt\": \"📄\", \".md\": \"📝\", \".yml\": \"⚙️\", \".yaml\": \"⚙️\", \".env\": \"🔒\", \".log\": \"📰\", \".db\": \"🗄️\", \".sqlite\": \"🗄️\", \".sqlite3\": \"🗄️\", \".sql\": \"💾\", \".png\": \"🖼️\", \".jpg\": \"🖼️\", \".jpeg\": \"🖼️\", \".webp\": \"🖼️\", \".svg\": \"🎨\", \".ico\": \"🎯\", \".bmp\": \"🖼️\", \".avif\": \"🖼️\", \".gif\": \"🎞️\", \".mp4\": \"🎬\", \".webm\": \"🎬\", \".mov\": \"🎬\", \".mkv\": \"🎬\", \".avi\": \"🎬\", \".mp3\": \"🎵\", \".wav\": \"🎵\", \".ogg\": \"🎵\", \".m4a\": \"🎵\", \".flac\": \"🎵\" }; return icons[ext] || \"📄\"; } function formatBytes(bytes) { if (!bytes || bytes",
    "cn": "navigatePath(\"\"); bar.appendChild(rootSpan); if (!p) return; const parts = p.split(\"/\"); let accum = \"\"; parts.forEach(part => { accum += (accum ? \"/\" : \"\") + part; const curAccum = accum; const sep = document.createTextNode(\" / \"); bar.appendChild(sep); const link = document.createElement(\"span\"); link.className = \"bf-crumb-link\"; link.textContent = part; link.onclick = () => navigatePath(curAccum); bar.appendChild(link); }); } function updateTabHighlight(p) { document.querySelectorAll(\".bf-tab-btn\").forEach(btn => { const txt = btn.textContent.trim(); if (!p && txt.includes(\"Tất Cả\")) btn.classList.add(\"active\"); else if (p && txt.includes(p.split(\"/\")[0])) btn.classList.add(\"active\"); else btn.classList.remove(\"active\"); }); } function filterFiles(keyword) { const kw = (keyword || \"\").toLowerCase(); document.querySelectorAll(\".bf-file-item\").forEach(item => { const nameEl = item.querySelector(\".bf-item-name\"); if (nameEl) { const name = nameEl.textContent.toLowerCase(); item.style.display = name.includes(kw) ? \"flex\" : \"none\"; } }); } async function loadBotStatus() { try { const res = await fetch(\"/api/bot/status\"); const data = await res.json(); const pill = document.getElementById(\"botStatusPill\"); const text = document.getElementById(\"botStatusText\"); if (data.running) { text.textContent = `Bot Online (${data.username || \"Sakura\"})`; pill.style.borderColor = \"rgba(80, 250, 123, 0.4)\"; } else { text.textContent = \"Bot Offline\"; pill.style.borderColor = \"rgba(255, 85, 85, 0.4)\"; pill.querySelector(\"span\").textContent = \"🔴\"; } } catch (e) {} } function getFileIcon(ext) { const icons = { \".py\": \"🐍\", \".json\": \"📋\", \".html\": \"🌐\", \".css\": \"🎨\", \".js\": \"📜\", \".txt\": \"📄\", \".md\": \"📝\", \".yml\": \"⚙️\", \".yaml\": \"⚙️\", \".env\": \"🔒\", \".log\": \"📰\", \".db\": \"🗄️\", \".sqlite\": \"🗄️\", \".sqlite3\": \"🗄️\", \".sql\": \"💾\", \".png\": \"🖼️\", \".jpg\": \"🖼️\", \".jpeg\": \"🖼️\", \".webp\": \"🖼️\", \".svg\": \"🎨\", \".ico\": \"🎯\", \".bmp\": \"🖼️\", \".avif\": \"🖼️\", \".gif\": \"🎞️\", \".mp4\": \"🎬\", \".webm\": \"🎬\", \".mov\": \"🎬\", \".mkv\": \"🎬\", \".avi\": \"🎬\", \".mp3\": \"🎵\", \".wav\": \"🎵\", \".ogg\": \"🎵\", \".m4a\": \"🎵\", \".flac\": \"🎵\" }; return icons[ext] || \"📄\"; } function formatBytes(bytes) { if (!bytes || bytes"
  },
  "nhập từ/cụm/regex...": {
    "en": "nhập từ/cụm/regex...",
    "ja": "nhập từ/cụm/regex...",
    "cn": "nhập từ/cụm/regex..."
  },
  "rơi": {
    "en": "rơi",
    "ja": "rơi",
    "cn": "rơi"
  },
  "rương": {
    "en": "rương",
    "ja": "rương",
    "cn": "rương"
  },
  "s!play &lt;bài&gt;": {
    "en": "s!play &lt;bài&gt;",
    "ja": "s!play &lt;bài&gt;",
    "cn": "s!play &lt;bài&gt;"
  },
  "s!trans vi &lt;nội dung&gt;": {
    "en": "s!trans en <content>",
    "ja": "s!trans en <コンテンツ>",
    "cn": "s!trans en <内容>"
  },
  "s!tts &lt;nội dung&gt;": {
    "en": "s!tts <content>",
    "ja": "s!tts <コンテンツ>",
    "cn": "s!tts <内容>"
  },
  "thăng cấp Quản Trị Viên (Admin)": {
    "en": "Promoted to Administrator (Admin)",
    "ja": "管理者(Admin)に昇格",
    "cn": "晋升为管理员（Admin）"
  },
  "vd: 🥭 Quả Xoài Vàng": {
    "en": "eg: 🥭 Golden Mango",
    "ja": "例: 🥭 ゴールデンマンゴー",
    "cn": "例如：🥭金芒果"
  },
  "| Yêu cầu Lv.": {
    "en": "| Requires Lv.",
    "ja": "|必要Lv.",
    "cn": "|需要Lv."
  },
  "ĐANG TEST...": {
    "en": "TESTING...",
    "ja": "テスト中...",
    "cn": "测试..."
  },
  "Đang gửi bảng Reaction Role...": {
    "en": "Sending the Reaction Role table...",
    "ja": "リアクションロールテーブルを送信しています...",
    "cn": "正在发送反应角色表..."
  },
  "Đang gửi bảng nội quy vào kênh...": {
    "en": "Sending rules sheet to channel...",
    "ja": "ルールシートをチャンネルに送信中...",
    "cn": "正在向频道发送规则表..."
  },
  "Đang hoạt động — vào kênh sẽ tạo phòng riêng": {
    "en": "Active — entering a channel will create a private room",
    "ja": "アクティブ — チャンネルに入るとプライベート ルームが作成されます",
    "cn": "活动 — 进入频道将创建私人房间"
  },
  "Đang khởi chạy tiến trình khôi phục...": {
    "en": "Initiating recovery process...",
    "ja": "回復プロセスを開始しています...",
    "cn": "正在启动恢复过程..."
  },
  "Đang kiểm tra RCON...": {
    "en": "Checking RCON...",
    "ja": "RCONをチェック中...",
    "cn": "正在检查 RCON..."
  },
  "Đang phát Daily Giftcode...": {
    "en": "Playing Daily Giftcode...",
    "ja": "デイリーギフトコードをプレイしています...",
    "cn": "正在播放每日礼品代码..."
  },
  "Đang phát sóng mã code...": {
    "en": "Broadcasting code...",
    "ja": "放送コード...",
    "cn": "广播代码..."
  },
  "Đang tạo bản sao lưu máy chủ, vui lòng đợi...": {
    "en": "Creating server backup, please wait...",
    "ja": "サーバーのバックアップを作成しています。お待ちください...",
    "cn": "正在创建服务器备份，请稍候..."
  },
  "Đang tắt — chọn kênh để bật": {
    "en": "Off — select the channel to turn on",
    "ja": "オフ — オンにするチャンネルを選択します",
    "cn": "关 — 选择要打开的通道"
  },
  "Đang xem trước góc nhìn người dùng": {
    "en": "Previewing from the user's perspective",
    "ja": "ユーザーの視点からのプレビュー",
    "cn": "从用户的角度预览"
  },
  "Điều chỉnh tỉ lệ đập cuốc (+150 &amp; 20⭐), sản lượng khoáng sản và tỉ lệ đột biến mỏ đá quý. Đồng bộ toàn hệ thống.": {
    "en": "Adjusted pickaxe strike rate (+150 & 20⭐), mineral output and gem mine mutation rate. Synchronize the entire system.",
    "ja": "つるはしの攻撃率 (+150 & 20⭐)、鉱物生産量、宝石鉱山の突然変異率を調整しました。システム全体を同期します。",
    "cn": "调整了镐命中率（+150 & 20⭐）、矿物产量和宝石矿变异率。同步整个系统。"
  },
  "Điểm": {
    "en": "Point",
    "ja": "ポイント",
    "cn": "点"
  },
  "Điểm 💖": {
    "en": "Score 💖",
    "ja": "スコア 💖",
    "cn": "得分💖"
  },
  "Đã chuyển cá về giỏ đồ": {
    "en": "Fish has been moved to the shopping cart",
    "ja": "魚はショッピングカートに移動されました",
    "cn": "鱼已移至购物车"
  },
  "Đã cập nhật cấp sao": {
    "en": "Updated star level",
    "ja": "スターレベルを更新しました",
    "cn": "更新星级"
  },
  "Đã cập nhật sức chứa Thủy Cung": {
    "en": "Updated Aquarium capacity",
    "ja": "水族館の収容人数を更新しました",
    "cn": "更新的水族馆容量"
  },
  "Đã cập nhật điểm thành công!": {
    "en": "Points updated successfully!",
    "ja": "ポイント更新成功！",
    "cn": "积分更新成功！"
  },
  "Đã dọn sạch Thủy Cung": {
    "en": "Cleaned the Aquarium",
    "ja": "水族館の掃除をしました",
    "cn": "清理了水族馆"
  },
  "Đã dọn sạch túi rác": {
    "en": "Trash bags emptied",
    "ja": "ゴミ袋を空にしました",
    "cn": "垃圾袋已清空"
  },
  "Đã enchant ${u.enchant_count} dòng thuộc tính": {
    "en": "enchanted ${u.enchant_count} attribute line",
    "ja": "エンチャントされた ${u.enchant_count} 属性行",
    "cn": "附魔 ${u.enchant_count} 属性行"
  },
  "Đã gửi mã code lên kênh thành công!": {
    "en": "Code has been sent to the channel successfully!",
    "ja": "コードがチャンネルに正常に送信されました。",
    "cn": "代码已成功发送至频道！"
  },
  "Đã gửi test": {
    "en": "Test sent",
    "ja": "テストが送信されました",
    "cn": "测试已发送"
  },
  "Đã gửi thông báo test tới kênh Discord": {
    "en": "Test notification sent to Discord channel",
    "ja": "テスト通知が Discord チャネルに送信される",
    "cn": "发送到 Discord 频道的测试通知"
  },
  "Đã gửi thông báo đến channel thành công!": {
    "en": "Notification sent to channel successfully!",
    "ja": "通知がチャンネルに正常に送信されました。",
    "cn": "通知已成功发送至频道！"
  },
  "Đã gửi thông báo!": {
    "en": "Notification sent!",
    "ja": "通知が送信されました!",
    "cn": "通知已发送！"
  },
  "Đã hủy cuộc hôn nhân thành công!": {
    "en": "The marriage was successfully annulled!",
    "ja": "無事に婚約破棄が完了しました！",
    "cn": "婚姻成功宣告无效！"
  },
  "Đã hủy cấu hình kênh này (Nhớ bấm Lưu thay đổi)": {
    "en": "This channel has been configured (Remember to click Save changes)",
    "ja": "このチャネルは構成されています (忘れずに「変更を保存」をクリックしてください)",
    "cn": "该频道已配置（记得点击保存更改）"
  },
  "Đã hủy liên kết máy chủ": {
    "en": "Unlinked server",
    "ja": "リンクされていないサーバー",
    "cn": "未链接的服务器"
  },
  "Đã kích hoạt môi trường mới!": {
    "en": "New environment enabled!",
    "ja": "新しい環境が可能になりました！",
    "cn": "新环境启用！"
  },
  "Đã kết thúc giveaway": {
    "en": "Giveaway has ended",
    "ja": "プレゼントは終了しました",
    "cn": "赠品已结束"
  },
  "Đã kết thúc giveaway thành công!": {
    "en": "The giveaway has ended successfully!",
    "ja": "プレゼント企画無事終了しました！",
    "cn": "赠品活动圆满结束！"
  },
  "Đã lưu Audit Logs": {
    "en": "Audit Logs saved",
    "ja": "監査ログが保存されました",
    "cn": "已保存审核日志"
  },
  "Đã lưu Auto-Moderation": {
    "en": "Auto-Moderation saved",
    "ja": "自動モデレーションが保存されました",
    "cn": "自动审核已保存"
  },
  "Đã lưu Confession": {
    "en": "Confessions saved",
    "ja": "自白が保存されました",
    "cn": "口供已保存"
  },
  "Đã lưu Level & Economy": {
    "en": "Saved Level & Economy",
    "ja": "保存されたレベルとエコノミー",
    "cn": "保存级别和经济性"
  },
  "Đã lưu TempVoice": {
    "en": "Saved TempVoice",
    "ja": "保存されたTempVoice",
    "cn": "已保存的临时语音"
  },
  "Đã lưu cài đặt Hoyo Codes!": {
    "en": "Hoyo Codes settings saved!",
    "ja": "Hoyo コードの設定が保存されました!",
    "cn": "Hoyo 代码设置已保存！"
  },
  "Đã lưu cài đặt server!": {
    "en": "Server settings saved!",
    "ja": "サーバー設定が保存されました!",
    "cn": "服务器设置已保存！"
  },
  "Đã lưu cài đặt!": {
    "en": "Settings saved!",
    "ja": "設定が保存されました!",
    "cn": "设置已保存！"
  },
  "Đã lưu cấu hình Auto Role": {
    "en": "Auto Role configuration saved",
    "ja": "自動役割設定が保存されました",
    "cn": "已保存自动角色配置"
  },
  "Đã lưu cấu hình Kênh Nội Quy": {
    "en": "Rules Channel configuration saved",
    "ja": "ルール チャネル設定が保存されました",
    "cn": "规则 通道配置已保存"
  },
  "Đã lưu cấu hình Kênh Streak": {
    "en": "Streak Channel configuration saved",
    "ja": "ストリークチャンネル設定が保存されました",
    "cn": "已保存 Streak 通道配置"
  },
  "Đã lưu cấu hình MiniGame": {
    "en": "MiniGame configuration saved",
    "ja": "ミニゲーム設定が保存されました",
    "cn": "小游戏配置已保存"
  },
  "Đã lưu cấu hình RCON thành công!": {
    "en": "RCON configuration saved successfully!",
    "ja": "RCON 設定が正常に保存されました。",
    "cn": "RCON配置保存成功！"
  },
  "Đã lưu cấu hình Welcome / Goodbye / Boost": {
    "en": "Welcome/Goodbye/Boost configuration saved",
    "ja": "ようこそ/さようなら/ブースト構成が保存されました",
    "cn": "欢迎/再见/Boost 配置已保存"
  },
  "Đã lưu cấu hình câu cá": {
    "en": "Fishing configuration saved",
    "ja": "釣り設定が保存されました",
    "cn": "钓鱼配置已保存"
  },
  "Đã lưu cấu hình panel Role & Ticket": {
    "en": "Role & Ticket panel configuration saved",
    "ja": "ロールとチケットパネルの設定が保存されました",
    "cn": "角色和工单面板配置已保存"
  },
  "Đã lưu cấu hình thành công!": {
    "en": "Configuration saved successfully!",
    "ja": "構成は正常に保存されました。",
    "cn": "配置保存成功！"
  },
  "Đã lưu hồ sơ bot thành công": {
    "en": "Bot profile saved successfully",
    "ja": "ボットプロファイルが正常に保存されました",
    "cn": "机器人配置文件保存成功"
  },
  "Đã lưu trực tiếp file config.py!": {
    "en": "Saved directly to the config.py file!",
    "ja": "config.py ファイルに直接保存されました。",
    "cn": "直接保存到config.py文件中！"
  },
  "Đã mở": {
    "en": "Opened",
    "ja": "開いた",
    "cn": "已开通"
  },
  "Đã thay đổi trạng thái yêu cầu vote!": {
    "en": "Changed vote request status!",
    "ja": "投票リクエストのステータスが変更されました。",
    "cn": "更改投票请求状态！"
  },
  "Đã thu hồi quyền Admin!": {
    "en": "Admin rights revoked!",
    "ja": "管理者権限が剥奪されました!",
    "cn": "管理员权限被撤销！"
  },
  "Đã thêm Admin web thành công!": {
    "en": "Web Admin added successfully!",
    "ja": "Web管理者が正常に追加されました。",
    "cn": "Web管理员添加成功！"
  },
  "Đã thêm Custom Key thành công": {
    "en": "Custom Key added successfully",
    "ja": "カスタムキーが正常に追加されました",
    "cn": "自定义密钥添加成功"
  },
  "Đã thêm kênh câu cá (Hãy bấm Lưu Cài Đặt)": {
    "en": "Fishing channel added (Click Save Settings)",
    "ja": "釣りチャンネルを追加しました (「設定を保存」をクリック)",
    "cn": "已添加钓鱼频道（点击保存设置）"
  },
  "Đã thêm mốc thưởng role!": {
    "en": "Added role bonus milestones!",
    "ja": "役割ボーナスのマイルストーンを追加しました!",
    "cn": "添加了角色奖励里程碑！"
  },
  "Đã thêm từ thành công!": {
    "en": "Word added successfully!",
    "ja": "単語が正常に追加されました。",
    "cn": "词添加成功！"
  },
  "Đã thêm vai trò vào danh sách": {
    "en": "Added roles to the list",
    "ja": "リストに役割を追加しました",
    "cn": "将角色添加到列表中"
  },
  "Đã tạo Giveaway thành công!": {
    "en": "Giveaway successfully created!",
    "ja": "プレゼントが正常に作成されました!",
    "cn": "赠品创建成功！"
  },
  "Đã tạo bản sao lưu thành công!": {
    "en": "Backup created successfully!",
    "ja": "バックアップが正常に作成されました。",
    "cn": "备份创建成功！"
  },
  "Đã tạo bảng Reaction Role thành công!": {
    "en": "Reaction Role table created successfully!",
    "ja": "リアクションロールテーブルが正常に作成されました。",
    "cn": "反应 角色表创建成功！"
  },
  "Đã xóa Custom Key": {
    "en": "Custom Key removed",
    "ja": "カスタムキーが削除されました",
    "cn": "自定义密钥已删除"
  },
  "Đã xóa Giftcode": {
    "en": "Giftcode removed",
    "ja": "ギフトコードが削除されました",
    "cn": "礼品代码已删除"
  },
  "Đã xóa bản sao lưu": {
    "en": "Deleted backup",
    "ja": "削除されたバックアップ",
    "cn": "已删除备份"
  },
  "Đã xóa bảng Reaction Role": {
    "en": "Deleted the Reaction Role table",
    "ja": "リアクションロールテーブルを削除しました",
    "cn": "删除了反应角色表"
  },
  "Đã xóa cá khỏi Thủy Cung": {
    "en": "Removed fish from the Aquarium",
    "ja": "水族館から魚を撤去した",
    "cn": "从水族馆中取出鱼"
  },
  "Đã xóa cá khỏi giỏ": {
    "en": "Removed fish from basket",
    "ja": "魚をカゴから取り出した",
    "cn": "从篮子里取出鱼"
  },
  "Đã xóa giveaway thành công!": {
    "en": "Giveaway successfully deleted!",
    "ja": "プレゼントは正常に削除されました。",
    "cn": "赠品已成功删除！"
  },
  "Đã xóa mốc role": {
    "en": "Role landmark removed",
    "ja": "役割ランドマークが削除されました",
    "cn": "角色地标已移除"
  },
  "Đã xóa thẻ": {
    "en": "Tag removed",
    "ja": "タグが削除されました",
    "cn": "标签已删除"
  },
  "Đã xóa toàn bộ cá": {
    "en": "All fish removed",
    "ja": "魚は全て撤去",
    "cn": "所有鱼都被移除"
  },
  "Đã xóa tất cả kênh câu (Cho phép mọi kênh)": {
    "en": "All fishing channels removed (All channels allowed)",
    "ja": "すべての釣りチャンネルが削除されました (すべてのチャンネルが許可されました)",
    "cn": "删除所有钓鱼频道（允许所有频道）"
  },
  "Đã xóa từ thành công!": {
    "en": "Word deleted successfully!",
    "ja": "Word が正常に削除されました。",
    "cn": "Word删除成功！"
  },
  "Đã xóa vật phẩm thành công!": {
    "en": "Item deleted successfully!",
    "ja": "アイテムは正常に削除されました。",
    "cn": "项目删除成功！"
  },
  "Đã đăng bảng nội quy thành công!": {
    "en": "Rules table posted successfully!",
    "ja": "ルールテーブルが正常に投稿されました。",
    "cn": "规则表发布成功！"
  },
  "Đã đăng panel Role thành công": {
    "en": "Role panel posted successfully",
    "ja": "役割パネルが正常に投稿されました",
    "cn": "角色面板发布成功"
  },
  "Đã đăng panel Ticket thành công": {
    "en": "Ticket panel posted successfully",
    "ja": "チケットパネルが正常に投稿されました",
    "cn": "票务面板发布成功"
  },
  "Đã đưa Mùa & Thời Tiết về chu kỳ tự động": {
    "en": "Returned Season & Weather to automatic cycle",
    "ja": "季節と天気を自動サイクルに戻しました",
    "cn": "将季节和天气返回到自动循环"
  },
  "Đóng menu": {
    "en": "Close the menu",
    "ja": "メニューを閉じる",
    "cn": "关闭菜单"
  },
  "Đăng bảng nội quy cùng nút bấm xác minh vào kênh đã chọn?": {
    "en": "Post rules and verification button to selected channel?",
    "ja": "ルールと確認ボタンを選択したチャンネルに投稿しますか?",
    "cn": "将规则和验证按钮发布到所选频道？"
  },
  "Đăng nhập thành công!": {
    "en": "Log in successfully!",
    "ja": "ログインに成功しました！",
    "cn": "登录成功！"
  },
  "Đường dẫn URL (https://...)": {
    "en": "URL (https://...)",
    "ja": "URL（https://...）",
    "cn": "网址（https://...）"
  },
  "Đất Trống": {
    "en": "Empty Land",
    "ja": "空き地",
    "cn": "空地"
  },
  "để lưu cấu trúc server.": {
    "en": "to save the server structure.",
    "ja": "サーバー構造を保存します。",
    "cn": "保存服务器结构。"
  },
  "Ảnh quá lớn! Vui lòng chọn tệp nhỏ hơn 8MB.": {
    "en": "Photo is too big! Please choose files smaller than 8MB.",
    "ja": "写真が大きすぎます！ 8MB 未満のファイルを選択してください。",
    "cn": "照片太大了！请选择小于 8MB 的文件。"
  },
  "Ấp từ Rương Thần Thoại": {
    "en": "Hamlet from the Mythical Chest",
    "ja": "神話の宝箱から出てきたハムレット",
    "cn": "神话宝箱中的哈姆雷特"
  },
  "Ẩn khỏi shop người chơi": {
    "en": "Hidden from the player shop",
    "ja": "プレイヤーショップから隠されています",
    "cn": "隐藏在玩家商店中"
  },
  "Ổn định": {
    "en": "Stable",
    "ja": "安定した",
    "cn": "稳定"
  },
  "ổn": {
    "en": "okay",
    "ja": "わかりました",
    "cn": "好的"
  },
  "— Chưa đặt —": {
    "en": "— Not booked —",
    "ja": "— 予約されていません —",
    "cn": "— 未预订 —"
  },
  "— Không phân loại —": {
    "en": "— Uncategorized —",
    "ja": "— 未分類 —",
    "cn": "— 未分类 —"
  },
  "⌨️ Danh Sách Lệnh Sakura Bot": {
    "en": "⌨️ Sakura Bot Command List",
    "ja": "⌨️ さくらボットコマンドリスト",
    "cn": "⌨️ Sakura 机器人命令列表"
  },
  "⏳ ĐANG TEST...": {
    "en": "⏳ TESTING...",
    "ja": "⏳ テスト中...",
    "cn": "⏳ 测试..."
  },
  "⏳ Đang kiểm tra cú pháp và lưu...": {
    "en": "⏳ Checking syntax and saving...",
    "ja": "⏳ 構文をチェックして保存しています...",
    "cn": "⏳ 检查语法并保存..."
  },
  "⏳ Đang kiểm tra kết nối Server Minecraft & RCON...": {
    "en": "⏳ Checking Minecraft & RCON Server connection...",
    "ja": "⏳ Minecraft と RCON サーバーの接続を確認しています...",
    "cn": "⏳ 正在检查 Minecraft 和 RCON 服务器连接..."
  },
  "⏳ Đang kiểm tra kết nối live tới máy chủ...": {
    "en": "⏳ Checking live connection to the server...",
    "ja": "⏳ サーバーへのライブ接続を確認しています...",
    "cn": "⏳ 正在检查与服务器的实时连接..."
  },
  "⏳ Đang lưu cấu hình và kết nối thử qua RCON...": {
    "en": "⏳ Saving configuration and test connection via RCON...",
    "ja": "⏳ 設定を保存し、RCON 経由で接続をテストしています...",
    "cn": "⏳ 通过 RCON 保存配置和测试连接..."
  },
  "⏳ Đang nạp dữ liệu bảng [${escapeHtml(tableName)}]...": {
    "en": "⏳ Loading table data [${escapeHtml(tableName)}]...",
    "ja": "⏳ テーブル データ [${escapeHtml(tableName)}] をロードしています...",
    "cn": "⏳ 正在加载表格数据 [${escapeHtml(tableName)}]..."
  },
  "⏳ Đang tra cứu Thủy Cung cần thủ...": {
    "en": "⏳ Looking up the Fisherman's Aquarium...",
    "ja": "⏳ フィッシャーマンズ水族館を見上げると…",
    "cn": "⏳ 寻找渔人水族馆..."
  },
  "⏳ Đang tra cứu thông tin thợ mỏ...": {
    "en": "⏳ Looking up miner information...",
    "ja": "⏳ マイナー情報を調べています...",
    "cn": "⏳ 查找矿工信息..."
  },
  "⏳ Đang tạo...": {
    "en": "⏳ Creating...",
    "ja": "⏳ 作成中...",
    "cn": "⏳ 创建..."
  },
  "⏳ Đang xử lý liên kết máy chủ...": {
    "en": "⏳ Processing server link...",
    "ja": "⏳ サーバーリンクを処理中...",
    "cn": "⏳ 正在处理服务器链接..."
  },
  "⏳ Đang đăng...": {
    "en": "⏳ Posting...",
    "ja": "⏳ 投稿中...",
    "cn": "⏳ 发帖..."
  },
  "☀️ Bùa Thái Dương": {
    "en": "☀️ Thai Duong Charm",
    "ja": "☀️ タイズオンチャーム",
    "cn": "☀️ 泰国阳符"
  },
  "☀️ Đã chuyển sang Giao diện Sáng (Sakura Pastel)": {
    "en": "☀️ Switched to Bright Theme (Sakura Pastel)",
    "ja": "☀️明るいテーマ（サクラパステル）に切り替えました",
    "cn": "☀️ 切换为明亮主题（樱花粉彩）"
  },
  "☄️ Mảnh Thiên Thạch Vũ Trụ": {
    "en": "☄️ Cosmic Meteor Fragment",
    "ja": "☄️ 宇宙流星の破片",
    "cn": "☄️宇宙流星碎片"
  },
  "⚓ Rương Tàu Đắm Cổ": {
    "en": "⚓ Ancient Shipwreck Chest",
    "ja": "⚓ 古代の難破船チェスト",
    "cn": "⚡ 古代沉船宝箱"
  },
  "⚔️ Trang bị": {
    "en": "⚔️ Equipment",
    "ja": "⚔️装備",
    "cn": "⚔️设备"
  },
  "⚙️ Cài Đặt Hệ Thống": {
    "en": "⚙️ System Settings",
    "ja": "⚙️ システム設定",
    "cn": "⚙️系统设置"
  },
  "⚙️ Cần Câu Sắt (+16 Luck)": {
    "en": "⚙️ Iron Fishing Rod (+16 Luck)",
    "ja": "⚙️ 鉄の釣り竿 (+16 幸運)",
    "cn": "⚙️ 铁钓鱼竿（+16 运气）"
  },
  "⚙️ Quặng Sắt Tôi Rèn": {
    "en": "⚙️ Forged Iron Ore",
    "ja": "⚙️ 鍛造鉄鉱石",
    "cn": "⚙️ 锻造铁矿石"
  },
  "⚙️ TẠO PHÒNG RIÊNG &amp; CÀI ĐẶT": {
    "en": "⚙️ CREATE YOUR PRIVATE ROOM & SETUP",
    "ja": "⚙️ プライベートルームを作成してセットアップ",
    "cn": "⚙️ 创建您的私人房间和设置"
  },
  "⚙️ Đặt": {
    "en": "⚙️ Set",
    "ja": "⚙️セット",
    "cn": "⚙️套装"
  },
  "⚠️ CẢNH BÁO: Bạn có chắc chắn muốn XÓA SẠCH toàn bộ cá trong giỏ của người chơi này?": {
    "en": "⚠️ WARNING: Are you sure you want to CLEANSE all the fish in this player's basket?",
    "ja": "⚠️ 警告: このプレイヤーのバスケットの中の魚をすべて浄化してもよろしいですか?",
    "cn": "⚠️警告：您确定要清理该玩家篮子里的所有鱼吗？"
  },
  "⚡ Kỹ Năng & Thử Thách": {
    "en": "⚡ Skills & Challenges",
    "ja": "⚡ スキルと課題",
    "cn": "⚡ 技能与挑战"
  },
  "⚡ Phân Bón Siêu Tốc": {
    "en": "⚡ Super Fast Fertilizer",
    "ja": "⚡ 超速効肥料",
    "cn": "⚡ 超快速肥料"
  },
  "⚡ Đang Bật Cưỡng Chế (Override)": {
    "en": "⚡ Override is on",
    "ja": "⚡ オーバーライドがオンになっています",
    "cn": "⚡ 覆盖已开启"
  },
  "⚡ Đã nạp Preset Mặc Định (1.0x). Đang lưu...": {
    "en": "⚡ Loaded Default Preset (1.0x). Saving...",
    "ja": "⚡ デフォルトのプリセット (1.0x) がロードされました。保存中...",
    "cn": "⚡ 已加载默认预设 (1.0x)。保存..."
  },
  "⚪ Đã tắt": {
    "en": "⚪ Disabled",
    "ja": "⚪ 無効",
    "cn": "⚪ 残疾人"
  },
  "⚪ Đã tắt (tắt)": {
    "en": "⚪ Disabled (turned off)",
    "ja": "⚪ 無効 (オフ)",
    "cn": "⚪ 禁用（关闭）"
  },
  "⛏️ Cuốc Sắt Tôi Luyện (+50 Luck)": {
    "en": "⛏️ Tempered Iron Pickaxe (+50 Luck)",
    "ja": "⛏️ 強化鉄のつるはし (+50 幸運)",
    "cn": "⛏️ 淬火铁镐（+50 运气）"
  },
  "⛏️ Quản Trị Hệ Thống Khoáng Sản": {
    "en": "⛏️ Mineral System Management",
    "ja": "⛏️ミネラルシステム管理",
    "cn": "⛏️ 矿物系统管理"
  },
  "⛏️ Quản Trị Hệ Thống Minecraft Server": {
    "en": "⛏️ Minecraft Server System Administration",
    "ja": "⛏️ Minecraft サーバー システム管理",
    "cn": "⛏️ Minecraft 服务器系统管理"
  },
  "✅ Bật Toàn Cục": {
    "en": "✅ Enable Global",
    "ja": "✅ グローバルを有効にする",
    "cn": "✅ 启用全球"
  },
  "✅ Thao tác thành công!": {
    "en": "✅ Operation successful!",
    "ja": "✅ 作戦成功！",
    "cn": "✅ 手术成功！"
  },
  "✅ Đã hủy liên kết máy chủ Minecraft!": {
    "en": "✅ Unlinked Minecraft server!",
    "ja": "✅ Minecraft サーバーのリンクが解除されました!",
    "cn": "✅ 取消链接 Minecraft 服务器！"
  },
  "✅ Đã lưu cấu hình kết nối Minecraft!": {
    "en": "✅ Minecraft connection configuration saved!",
    "ja": "✅ Minecraft の接続設定が保存されました!",
    "cn": "✅ Minecraft 连接配置已保存！"
  },
  "✅ Đã lưu cấu hình tỉ lệ & God Mode thành công!": {
    "en": "✅ Scale configuration & God Mode saved successfully!",
    "ja": "✅ スケール構成とゴッドモードが正常に保存されました!",
    "cn": "✅ 秤配置和上帝模式保存成功！"
  },
  "✅ Đã tải ảnh đại diện vào khung xem trước! Hãy nhấn Lưu Hồ Sơ để áp dụng.": {
    "en": "✅ Avatar uploaded to preview! Click Save Profile to apply.",
    "ja": "✅ アバターがプレビューにアップロードされました! 「プロファイルを保存」をクリックして適用します。",
    "cn": "✅ 头像已上传预览！单击“保存个人资料”进行应用。"
  },
  "✓ Đã chép": {
    "en": "✓ Copied",
    "ja": "✓ コピーされました",
    "cn": "✓ 已复制"
  },
  "✨ Cần Tinh Tú Thần Thoại (+280 Luck)": {
    "en": "✨ Need Mythical Stars (+280 Luck)",
    "ja": "✨ 神話の星が必要 (+280 運)",
    "cn": "✨ 需要神话之星（+280 运气）"
  },
  "✨ Dùng s!help để xem lệnh • /dashboard để cấu hình server": {
    "en": "✨ Use s!help to view the command • /dashboard to configure the server",
    "ja": "✨ s!help を使用してコマンドを表示します。 • /dashboard を使用してサーバーを構成します。",
    "cn": "✨ 使用 s!help 查看命令 • /dashboard 配置服务器"
  },
  "✨ Hiển thị trong Bách Khoa": {
    "en": "✨ Displayed in Bach Khoa",
    "ja": "✨バックコアに展示中",
    "cn": "✨ 显示在 Bach Khoa"
  },
  "✨ Mồi Dạ Quang (+35 Luck)": {
    "en": "✨ Luminous Lure (+35 Luck)",
    "ja": "✨ 発光ルアー (+35 運)",
    "cn": "✨ 发光诱饵（+35 运气）"
  },
  "✨ Tùy Chỉnh": {
    "en": "✨ Customizable",
    "ja": "✨カスタマイズ可能",
    "cn": "✨ 可定制"
  },
  "❌ Lỗi": {
    "en": "❌ Error",
    "ja": "❌ エラー",
    "cn": "❌ 错误"
  },
  "❌ Lỗi kết nối khi tra cứu thợ mỏ!": {
    "en": "❌ Connection error when looking up miners!",
    "ja": "❌ マイナーを検索するときに接続エラーが発生しました!",
    "cn": "❌查找矿机时连接错误！"
  },
  "❌ Lỗi: ${escapeHtml(e.message || \"Lỗi kết nối khi tải bảng\")}": {
    "en": "❌ Error: ${escapeHtml(e.message || \"Connection error when loading table\")}",
    "ja": "❌ エラー: ${escapeHtml(e.message || \"テーブル読み込み時の接続エラー\")}",
    "cn": "❌ 错误：${escapeHtml(e.message || \"加载表时连接错误\")}"
  },
  "❌ Thao tác thất bại": {
    "en": "❌ Operation failed",
    "ja": "❌ 操作が失敗しました",
    "cn": "❌ 操作失败"
  },
  "❤️‍🔥 Trái Tim Địa Mẫu Gaia": {
    "en": "❤️‍🔥 Heart of Earth Mother Gaia",
    "ja": "❤️‍🔥 ハート・オブ・アース マザーガイア",
    "cn": "❤️‍🔥 地球母亲盖亚之心"
  },
  "➕ Cộng": {
    "en": "➕ Plus",
    "ja": "➕ プラス",
    "cn": "➕ 加号"
  },
  "⬛ Than Đá Hắc Thạch": {
    "en": "⬛ Obsidian Coal",
    "ja": "⬛ 黒曜石石炭",
    "cn": "⬛ 黑曜石煤"
  },
  "🃏 0 Thẻ": {
    "en": "🃏 0 Cards",
    "ja": "🃏 カード0枚",
    "cn": "🃏 0 张卡片"
  },
  "🃏 Thẻ Đã Phát Hành": {
    "en": "🃏 Card Issued",
    "ja": "🃏カード発行済み",
    "cn": "🃏 卡已发行"
  },
  "🌀 Mồi Vực Thẳm (+130 Luck)": {
    "en": "🌀 Abyss Lure (+130 Luck)",
    "ja": "🌀 アビス ルアー (+130 運)",
    "cn": "🌀 深渊诱饵（+130 运气）"
  },
  "🌌 Chìa Khóa Hư Không": {
    "en": "🌌 Key to the Void",
    "ja": "🌌 虚空への鍵",
    "cn": "🌌 虚空之匙"
  },
  "🌌 Cuốc Thần Thoại Khởi Nguyên (+1200 Luck)": {
    "en": "🌌 Mythical Pickaxe (+1200 Luck)",
    "ja": "🌌 神話のつるはし (+1200 幸運)",
    "cn": "🌌 神话镐（+1200 运气）"
  },
  "🌌 Cần Thần Tinh Tú Astral (+350 Luck)": {
    "en": "🌌 Need Astral Star Spirit (+350 Luck)",
    "ja": "🌌 アストラルスタースピリットが必要 (+350 幸運)",
    "cn": "🌌需要星辰之灵（+350幸运）"
  },
  "🌌 Hạt Nhân Hư Không The End": {
    "en": "🌌 Nucleus Void The End",
    "ja": "🌌 ニュークリアス・ボイド・ジ・エンド",
    "cn": "🌌 核心虚空终结"
  },
  "🌌 Rương Hư Không Vĩnh Hằng": {
    "en": "🌌 Eternal Void Chest",
    "ja": "🌌 永遠の虚無チェスト",
    "cn": "🌌 永恒虚空宝箱"
  },
  "🌍 Toàn Bộ Máy Chủ": {
    "en": "🌍 Entire Server",
    "ja": "🌍 サーバー全体",
    "cn": "🌍整个服务器"
  },
  "🌙 Đã chuyển sang Giao diện Tối": {
    "en": "🌙 Switched to Dark Theme",
    "ja": "🌙 ダークテーマに切り替えました",
    "cn": "🌙切换到黑暗主题"
  },
  "🌟 Bình Tưới Thần Thoại": {
    "en": "🌟 Mythical Watering Can",
    "ja": "🌟 神話上のじょうろ",
    "cn": "🌟 神话喷壶"
  },
  "🌟 Mồi Tiên Dược Thiên Giới (+500 Luck)": {
    "en": "🌟 Heavenly Elixir Lure (+500 Luck)",
    "ja": "🌟 ヘブンリーエリクサー ルアー (+500 幸運)",
    "cn": "🌟 天丹药饵（+500 幸运）"
  },
  "🌟 Tinh Hoa Thần Biển (+260 Luck)": {
    "en": "🌟 Sea Spirit Essence (+260 Luck)",
    "ja": "🌟 海の精霊のエッセンス (+260 運)",
    "cn": "🌟 海灵精华（+260 幸运）"
  },
  "🌧️ Bùa Gọi Mưa": {
    "en": "🌧️ Rain Calling Talisman",
    "ja": "🌧️ 雨を呼ぶタリスマン",
    "cn": "🌧️ 呼雨符"
  },
  "🌶️ Hạt Giống Ớt Cay": {
    "en": "🌶️ Hot Chili Seeds",
    "ja": "🌶️ ホットチリシード",
    "cn": "🌶️辣椒籽"
  },
  "🌶️ Ớt Chỉ Thiên Đỏ": {
    "en": "🌶️ Red Chili Pepper",
    "ja": "🌶️赤唐辛子",
    "cn": "🌶️红辣椒"
  },
  "🌸 Chào mừng đến với Sakura — chúc bạn một ngày tuyệt vời!": {
    "en": "🌸 Welcome to Sakura — have a wonderful day!",
    "ja": "🌸 さくらへようこそ — 素晴らしい一日をお過ごしください!",
    "cn": "⭐ 欢迎来到樱花 - 祝您度过美好的一天！"
  },
  "🌸 Quản Trị Hệ Thống Waifu Gacha": {
    "en": "🌸 Waifu Gacha System Administration",
    "ja": "🌸ワイフガチャシステム管理",
    "cn": "😍 Waifu Gacha 系统管理"
  },
  "🌸 Sakura Bot — Hầu gái Yandere của bạn đã sẵn sàng!": {
    "en": "🌸 Sakura Bot — Your Yandere maid is ready!",
    "ja": "🌸 さくらボット — あなたのヤンデレメイドが完成しました！",
    "cn": "🎈樱花机器人 — 你的病态女仆已准备好！"
  },
  "🌸 Tích Hợp SakuraBot": {
    "en": "🌸 Integrating SakuraBot",
    "ja": "🌸SakuraBotの統合",
    "cn": "🎈 集成 SakuraBot"
  },
  "🌹 Hoa Hồng Tình Yêu": {
    "en": "🌹 Love Rose",
    "ja": "🌹 ラブローズ",
    "cn": "🌹爱玫瑰"
  },
  "🌹 Hạt Giống Hoa Hồng": {
    "en": "🌹 Rose Seeds",
    "ja": "🌹 バラの種",
    "cn": "🌹 玫瑰种子"
  },
  "🌻 Hoa Hướng Dương Rạng Rỡ": {
    "en": "🌻 Radiant Sunflowers",
    "ja": "🌻 輝くひまわり",
    "cn": "🌻 灿烂的向日葵"
  },
  "🌻 Hạt Giống Hướng Dương": {
    "en": "🌻 Sunflower Seeds",
    "ja": "🌻 ヒマワリの種",
    "cn": "🌻 葵花籽"
  },
  "🌽 Bắp Ngô Vàng Óng": {
    "en": "🌽 Golden Corn",
    "ja": "🌽 ゴールデンコーン",
    "cn": "🌽黄金玉米"
  },
  "🌽 Hạt Giống Bắp Ngô": {
    "en": "🌽 Corn Seeds",
    "ja": "🌽 トウモロコシの種子",
    "cn": "🌽 玉米种子"
  },
  "🌾 Bó Lúa Mì Vàng": {
    "en": "🌾 Golden Wheat Bundle",
    "ja": "🌾 黄金の小麦バンドル",
    "cn": "🌾 金色小麦捆绑包"
  },
  "🌾 Hạt Giống Lúa Mì": {
    "en": "🌾 Wheat Seeds",
    "ja": "🌾小麦の種子",
    "cn": "🌾 小麦种子"
  },
  "🌾 Phân Bón Bội Thu": {
    "en": "🌾 Bountiful Fertilizer",
    "ja": "🌾 豊富な肥料",
    "cn": "🌾 丰富的肥料"
  },
  "🌿 Phân Hữu Cơ Vi Sinh": {
    "en": "🌿 Microbial Organic Fertilizer",
    "ja": "🌿微生物有機肥料",
    "cn": "🌿微生物有机肥"
  },
  "🍀 Đã nạp Preset May Mắn x2. Đang lưu...": {
    "en": "🍀 Loaded with Lucky Preset x2. Saving...",
    "ja": "🍀 Luckyプリセットx2が搭載されています。保存中...",
    "cn": "🍀 加载幸运预设 x2。正在保存..."
  },
  "🍄 Bào Tử Nấm Hương": {
    "en": "🍄 Shiitake Mushroom Spores",
    "ja": "🍄しいたけの胞子",
    "cn": "🍄 香菇孢子"
  },
  "🍄 Nấm Hương Rừng Sâu": {
    "en": "🍄 Deep Forest Shiitake Mushroom",
    "ja": "🍄深い森のしいたけ",
    "cn": "🍄 深林香菇"
  },
  "🍅 Cà Chua Mọng Đỏ": {
    "en": "🍅 Red Juicy Tomatoes",
    "ja": "🍅 真っ赤なジューシートマト",
    "cn": "🍅 红色多汁的西红柿"
  },
  "🍅 Hạt Giống Cà Chua": {
    "en": "🍅 Tomato Seeds",
    "ja": "🍅トマトの種",
    "cn": "🍅 番茄种子"
  },
  "🍇 Chùm Nho Tím Mộng": {
    "en": "🍇 Bunch of Purple Grapes",
    "ja": "🍇 紫色のブドウの房",
    "cn": "🍇 一串紫葡萄"
  },
  "🍇 Hạt Giống Nho Tím": {
    "en": "🍇 Purple Grape Seeds",
    "ja": "🍇 紫色のブドウの種",
    "cn": "🍇紫葡萄籽"
  },
  "🍉 Hạt Giống Dưa Hấu": {
    "en": "🍉 Watermelon Seeds",
    "ja": "🍉 スイカの種",
    "cn": "🍉 西瓜籽"
  },
  "🍉 Quả Dưa Hấu Khổng Lồ": {
    "en": "🍉 Giant Watermelon",
    "ja": "🍉 巨大スイカ",
    "cn": "🍉 巨型西瓜"
  },
  "🍌 Bẫy Vỏ Chuối Trơn Trượt": {
    "en": "🍌 Slippery Banana Peel Trap",
    "ja": "🍌 滑りやすいバナナの皮のトラップ",
    "cn": "🍌 滑香蕉皮陷阱"
  },
  "🍏 Hạt Giống Táo Vàng": {
    "en": "🍏 Golden Apple Seeds",
    "ja": "🍏 黄金のリンゴの種",
    "cn": "🍏 金苹果种子"
  },
  "🍏 Táo Vàng Hoàng Gia": {
    "en": "🍏 Royal Golden Apple",
    "ja": "🍏 ロイヤルゴールデンアップル",
    "cn": "🍏皇家金苹果"
  },
  "🍑 Hạt Giống Đào Tiên": {
    "en": "🍑 Peach Seeds",
    "ja": "🍑 桃の種",
    "cn": "🍑 桃子"
  },
  "🍑 Đào Tiên Bồng Lai": {
    "en": "🍑 Dao Tien Bong Lai",
    "ja": "🍑 ダオ・ティエン・ボンライ",
    "cn": "🍑 稻田邦莱"
  },
  "🍓 Dâu Tây Đà Lạt": {
    "en": "🍓 Dalat Strawberries",
    "ja": "🍓ダラットイチゴ",
    "cn": "🍓 大叻草莓"
  },
  "🍓 Hạt Giống Dâu Tây": {
    "en": "🍓 Strawberry Seeds",
    "ja": "🍓イチゴの種",
    "cn": "🍓 草莓种子"
  },
  "🍫 Hộp Socola Tình Yêu": {
    "en": "🍫 Love Chocolate Box",
    "ja": "🍫 ラブチョコレートボックス",
    "cn": "🍫 爱巧克力盒"
  },
  "🎁 Hộp Quà Bí Ẩn": {
    "en": "🎁 Mystery Gift Box",
    "ja": "🎁 ミステリーギフトボックス",
    "cn": "🎁 神秘礼盒"
  },
  "🎁 Trao Thẻ Ngay": {
    "en": "🎁 Give Your Card Now",
    "ja": "🎁 今すぐカードを渡してください",
    "cn": "🎁 立即提供您的卡"
  },
  "🎁 Trao Tặng Thẻ Waifu Trực Tiếp Cho User": {
    "en": "🎁 Give Waifu Cards Directly to Users",
    "ja": "🎁 Waifu カードをユーザーに直接与える",
    "cn": "🎁 将外福卡直接赠送给用户"
  },
  "🎉 Quản Lý Giveaway Máy Chủ": {
    "en": "🎉 Manage Server Giveaway",
    "ja": "🎉 サーバープレゼントを管理する",
    "cn": "🎉 管理服务器赠品"
  },
  "🎋 Cần Câu Tre Dẻo (+8 Luck)": {
    "en": "🎋 Flexible Bamboo Fishing Rod (+8 Luck)",
    "ja": "🎋 柔軟な竹釣り竿 (+8 幸運)",
    "cn": "🎋 灵活的竹竿钓鱼竿（+8 运气）"
  },
  "🎒 Túi & Tiện Ích": {
    "en": "🎒 Bags & Gadgets",
    "ja": "🎒 バッグとガジェット",
    "cn": "🎒 包袋和小玩意"
  },
  "🎒 Túi Đồ": {
    "en": "🎒 Stuff Bag",
    "ja": "🎒 スタッフバッグ",
    "cn": "🎒 东西袋"
  },
  "🎖️ BXH Thành Tựu": {
    "en": "🎖️ Achievement chart",
    "ja": "🎖️ 達成チャート",
    "cn": "🎖️成就图表"
  },
  "🎙️ Quán Quân Kênh Thoại": {
    "en": "🎙️ Voice Channel Champion",
    "ja": "🎙️ ボイスチャンネルチャンピオン",
    "cn": "🎙️ 语音频道冠军"
  },
  "🎟️ Vé Số Đại Dương": {
    "en": "🎟️ Ocean Lottery Tickets",
    "ja": "🎟️ オーシャン宝くじチケット",
    "cn": "🎟️海洋彩票"
  },
  "🎣 BXH Câu Cá": {
    "en": "🎣 Fishing rankings",
    "ja": "🎣 釣りランキング",
    "cn": "🎣 钓鱼排名"
  },
  "🎣 Bảng Xếp Hạng Cần Thủ Câu Cá": {
    "en": "🎣 Fishing Angler Rankings",
    "ja": "🎣 釣り人ランキング",
    "cn": "🎣 钓鱼者排行榜"
  },
  "🎣 Cần Câu Gỗ (Cơ bản)": {
    "en": "🎣 Wooden Fishing Rod (Basic)",
    "ja": "🎣 木製釣り竿 (ベーシック)",
    "cn": "🎣 木制钓鱼竿（基本）"
  },
  "🎨 Scribble It! — Trò chơi Vẽ &amp; Đoán từ như Skribbl.io": {
    "en": "🎨 Scribble It! — Drawing & Guessing Word Games like Skribbl.io",
    "ja": "🎨 落書きしてみよう！ — Skribbl.io のような描画と推測の単語ゲーム",
    "cn": "🎨 乱写乱画！ — 像 Skribbl.io 这样的绘画和猜测文字游戏"
  },
  "🎭 Trò Đùa": {
    "en": "🎭 Jokes",
    "ja": "🎭 ジョーク",
    "cn": "🎭 笑话"
  },
  "🎮 TikTok Auto Download • Level & Economy • AutoMod đã bật": {
    "en": "🎮 TikTok Auto Download • Level & Economy • AutoMod enabled",
    "ja": "🎮 TikTok自動ダウンロード • レベルとエコノミー • AutoModが有効",
    "cn": "🎮 TikTok 自动下载 • 级别和经济性 • 启用 AutoMod"
  },
  "🎲 Casino & Kinh Tế": {
    "en": "🎲 Casino & Economics",
    "ja": "🎲 カジノと経済",
    "cn": "🎲 赌场与经济"
  },
  "🎲 Tổng Lượt Roll": {
    "en": "🎲 Total Rolls",
    "ja": "🎲 総ロール数",
    "cn": "🎲 总卷数"
  },
  "🎲 Điều Chỉnh Lượt Roll": {
    "en": "🎲 Adjust Roll Number",
    "ja": "🎲 ロール番号を調整する",
    "cn": "🎲 调整卷数"
  },
  "🎴 Danh Sách Thẻ Bài Của Người Dùng (": {
    "en": "🎴 User's Card List (",
    "ja": "🎴 ユーザーのカードリスト (",
    "cn": "🎴 用户卡列表（"
  },
  "🎴 Nhân Vật Trong Kho": {
    "en": "🎴 Characters in Stock",
    "ja": "🎴 在庫キャラクター",
    "cn": "🎴 库存角色"
  },
  "🏆 Bảng Xếp Hạng & Kinh Tế Server": {
    "en": "🏆 Server Economy & Rankings",
    "ja": "🏆 サーバーエコノミーとランキング",
    "cn": "🏆 服务器经济和排名"
  },
  "🏆 Bảng Xếp Hạng Sakura": {
    "en": "🏆 Sakura Rankings",
    "ja": "🏆さくらランキング",
    "cn": "🏆樱花排行榜"
  },
  "🏆 Bảng Xếp Hạng Thợ Săn Thành Tựu Sakura": {
    "en": "🏆 Sakura Achievement Hunter Rankings",
    "ja": "🏆サクラアチーブメントハンターランキング",
    "cn": "🏆 小樱成就猎人排名"
  },
  "🏆 Level & Kinh Tế": {
    "en": "🏆 Level & Economy",
    "ja": "🏆レベルと経済",
    "cn": "🏆 水平与经济"
  },
  "🏆 Quản Trị Hệ Thống Thành Tựu": {
    "en": "🏆 System Administration Achievements",
    "ja": "🏆 システム管理の実績",
    "cn": "🏆 系统管理成就"
  },
  "🏛️ Lồng Kính Bảo Vệ": {
    "en": "🏛️ Protective Glass Cage",
    "ja": "🏛️ 保護ガラスケージ",
    "cn": "🏛️防护玻璃笼"
  },
  "🏪 Đang Bán Chợ": {
    "en": "🏪 On Sale at Market",
    "ja": "🏪 マーケットで販売中",
    "cn": "🏪 市场有售"
  },
  "🏮 Đèn Soi Mỏ Siêu Sáng (+60 Luck)": {
    "en": "🏮 Super Bright Mining Lamp (+60 Luck)",
    "ja": "🏮 超明るい採掘ランプ (+60 運)",
    "cn": "🏮 超亮矿灯（+60 运气）"
  },
  "🏰 Quản Lý Máy Chủ Discord": {
    "en": "🏰 Manage Discord Server",
    "ja": "🏰 Discordサーバーを管理する",
    "cn": "🏰 管理 Discord 服务器"
  },
  "🐉 Cần Long Vương Tối Cao (+600 Luck)": {
    "en": "🐉 Can the Supreme Dragon King (+600 Luck)",
    "ja": "🐉 至高の竜王ができる (+600 幸運)",
    "cn": "🐉至尊龙王能否（+600幸运）"
  },
  "🐉 Rồng Đại Dương (+55 Luck, +35% Mồi)": {
    "en": "🐉 Ocean Dragon (+55 Luck, +35% Lure)",
    "ja": "🐉 オーシャンドラゴン (+55 運、+35% ルアー)",
    "cn": "🐉 海龙（+55 运气，+35% 诱饵）"
  },
  "🐉 Thần Thoại (&gt;= 150kg)": {
    "en": "🐉 Mythical (>= 150kg)",
    "ja": "🐉 神話級 (>= 150kg)",
    "cn": "🐉 神话（>= 150kg）"
  },
  "🐙 Chìa Khóa Vực Thẳm": {
    "en": "🐙 Key to the Abyss",
    "ja": "🐙 深淵への鍵",
    "cn": "🐙 通往深渊的钥匙"
  },
  "🐙 Rương Thủy Quái Vực Sâu": {
    "en": "🐙 Abyssal Water Monster Chest",
    "ja": "🐙 深海水モンスターチェスト",
    "cn": "🐙 深渊水怪宝箱"
  },
  "🐙 Tiểu Kraken Vực Sâu (+80 Luck, +45% Mồi)": {
    "en": "🐙 Little Abyss Kraken (+80 Luck, +45% Lure)",
    "ja": "🐙 リトルアビスクラーケン (+80 運、+45% ルアー)",
    "cn": "🐙 小深渊海妖（+80 运气，+45% 诱惑）"
  },
  "🐟 Bé Tí (&lt; 1.5kg)": {
    "en": "🐟 Tiny Baby (< 1.5kg)",
    "ja": "🐟 小さな赤ちゃん (< 1.5kg)",
    "cn": "🐟 小宝宝（<1.5公斤）"
  },
  "🐟 Cá Biển": {
    "en": "🐟 Sea Fish",
    "ja": "🐟 海の魚",
    "cn": "🐟 海鱼"
  },
  "🐟 Cá Hồi Tát Mặt": {
    "en": "🐟 Face Slapping Salmon",
    "ja": "🐟 顔を平手打ちするサーモン",
    "cn": "🐟 打脸鲑鱼"
  },
  "🐟 Cá Koi Nhật Bản": {
    "en": "🐟 Japanese Koi fish",
    "ja": "🐟 日本の鯉",
    "cn": "🐟 日本锦鲤"
  },
  "🐢 Rùa Cổ Đại (+30 Luck, +25% Mồi)": {
    "en": "🐢 Ancient Turtle (+30 Luck, +25% Lure)",
    "ja": "🐢 古代のカメ (+30 運、+25% ルアー)",
    "cn": "🐢 远古龟（+30 运气，+25% 诱饵）"
  },
  "🐧 Cánh Cụt Băng (+22 Luck, +20% Mồi)": {
    "en": "🐧 Ice Penguin (+22 Luck, +20% Lure)",
    "ja": "🐧 アイスペンギン (+22 運、+20% ルアー)",
    "cn": "🐧 冰企鹅（+22 运气，+20% 诱饵）"
  },
  "🐬 Cá Heo Thần Sóng (+40 Luck, +30% Mồi)": {
    "en": "🐬 Wave God Dolphin (+40 Luck, +30% Lure)",
    "ja": "🐬 波神イルカ (+40 運、+30% ルアー)",
    "cn": "🐬 波神海豚（+40 运气，+30% 诱饵）"
  },
  "🐱 Mèo Biển (+8 Luck, +10% Mồi)": {
    "en": "🐱 Sea Cat (+8 Luck, +10% Lure)",
    "ja": "🐱 ウミネコ (+8 運、+10% ルアー)",
    "cn": "🐱 海猫（+8 运气，+10% 诱饵）"
  },
  "🐸 Thuốc Biến Nạn Nhân Thành Ếch": {
    "en": "🐸 Medicine that turns victims into frogs",
    "ja": "🐸被害者をカエルに変える薬",
    "cn": "🐸 将受害者变成青蛙的药物"
  },
  "🐾 Thú Cưng": {
    "en": "🐾 Pets",
    "ja": "🐾 ペット",
    "cn": "🐾 宠物"
  },
  "👁️ XEM TRƯỚC: User Thường": {
    "en": "👁️ PREVIEW: Normal User",
    "ja": "👁️ プレビュー: 一般ユーザー",
    "cn": "👁️预览：普通用户"
  },
  "👁️ Đã chuyển sang Góc Nhìn Người Dùng Thường (User View Preview)!": {
    "en": "👁️ Switched to User View Preview!",
    "ja": "👁️ ユーザービュープレビューに切り替えました!",
    "cn": "👁️ 切换到用户视图预览！"
  },
  "👑 ADMIN - Toàn quyền": {
    "en": "👑 ADMIN - Full authority",
    "ja": "👑 ADMIN - 全権限",
    "cn": "👑 ADMIN - 全权"
  },
  "👑 Chìa Khóa Hoàng Gia": {
    "en": "👑 Royal Key",
    "ja": "👑 ロイヤルキー",
    "cn": "👑 皇家钥匙"
  },
  "👑 Chủ Bot (@linhxinh_dev)": {
    "en": "👑 Bot Owner (@linhxinh_dev)",
    "ja": "👑 ボット所有者 (@linhxinh_dev)",
    "cn": "👑 机器人所有者 (@linhxinh_dev)"
  },
  "👑 Cần Câu Vàng (+38 Luck)": {
    "en": "👑 Golden Fishing Rod (+38 Luck)",
    "ja": "👑 黄金の釣り竿 (+38 運)",
    "cn": "👑 金鱼竿（+38 运气）"
  },
  "👑 GOD MODE 100% (Đập Cuốc &amp; Sao 100%)": {
    "en": "👑 GOD MODE 100% (Smash Pickaxe & Stars 100%)",
    "ja": "👑 GOD MODE 100% (ツルハシとスターをスマッシュ 100%)",
    "cn": "👑 上帝模式 100%（粉碎镐和星星 100%）"
  },
  "👑 GOD MODE 100% (Đập Đồ &amp; Sao Không Trượt)": {
    "en": "👑 GOD MODE 100% (Smash Things & Stars Don't Slip)",
    "ja": "👑 GOD MODE 100% (スマッシュシングス&スターは滑らない)",
    "cn": "👑 上帝模式 100%（粉碎物体且星星不滑落）"
  },
  "👑 Quản Trị & Cấu Hình OP": {
    "en": "👑 OP Administration & Configuration",
    "ja": "👑 OPの管理と構成",
    "cn": "👑 OP 管理和配置"
  },
  "👑 Quản Trị Hệ Thống Câu Cá": {
    "en": "👑 Fishing System Administration",
    "ja": "👑 釣りシステム管理",
    "cn": "👑 渔业系统管理"
  },
  "👑 Rương Hoàng Gia Lộng Lẫy": {
    "en": "👑 Splendid Royal Chest",
    "ja": "👑 素晴らしいロイヤルチェスト",
    "cn": "👑 华丽的皇家宝箱"
  },
  "👑 Thoát Góc Nhìn User": {
    "en": "👑 Exit User Perspective",
    "ja": "👑 ユーザー視点を終了",
    "cn": "👑 退出用户视角"
  },
  "👑 Đã kích hoạt GOD MODE 100%! Đang lưu...": {
    "en": "👑 100% GOD MODE activated! Saving...",
    "ja": "👑 100% GOD モードが有効化されました!保存中...",
    "cn": "👑 100%上帝模式激活！正在保存..."
  },
  "👑 Đã quay lại Góc Nhìn Quản Trị Viên (Admin View)!": {
    "en": "👑 Returned to Admin View!",
    "ja": "👑 管理者ビューに戻りました!",
    "cn": "👑 返回管理视图！"
  },
  "👤 USER - Server của bạn": {
    "en": "👤 USER - Your server",
    "ja": "👤 ユーザー - あなたのサーバー",
    "cn": "👤 用户 - 您的服务器"
  },
  "👥 Người Chơi Gacha": {
    "en": "👥 Gacha Player",
    "ja": "👥 ガチャプレイヤー",
    "cn": "👥 扭蛋玩家"
  },
  "👥 Quản Trị Danh Sách Admin Web (Phân Quyền)": {
    "en": "👥 Managing the Web Admin List (Decentralization)",
    "ja": "👥 Web 管理者リストの管理 (分散化)",
    "cn": "👥 管理 Web 管理员列表（去中心化）"
  },
  "👻 Thẻ Ghost Ping Bí Ẩn": {
    "en": "👻 Mysterious Ghost Ping Card",
    "ja": "👻 神秘的なゴーストピンカード",
    "cn": "👻 神秘幽灵平卡"
  },
  "💀 Cần Tử Thần Vực Thẳm (+210 Luck)": {
    "en": "💀 Abyss Death Needle (+210 Luck)",
    "ja": "💀 アビスデスニードル (+210 幸運)",
    "cn": "💀 深渊死亡针（+210 幸运）"
  },
  "💍 Nhẫn Bạc Tình Yêu Vĩnh Cửu": {
    "en": "💍 Eternal Love Silver Ring",
    "ja": "💍 永遠の愛のシルバーリング",
    "cn": "💍 永恒的爱银戒指"
  },
  "💍 Nhẫn Vàng Hoàng Triều": {
    "en": "💍 Royal Dynasty Gold Ring",
    "ja": "💍 ロイヤルダイナスティゴールドリング",
    "cn": "💍皇家王朝金戒指"
  },
  "💍 Nhẫn Đồng Đôi Kết Hôn": {
    "en": "💍 Married Couple Bronze Ring",
    "ja": "💍 夫婦のブロンズリング",
    "cn": "💍 已婚情侣青铜戒指"
  },
  "💍 Quản Trị Hệ Thống Hôn Lễ & Cặp Đôi": {
    "en": "💍 Wedding & Couple System Administration",
    "ja": "💍 ウェディング＆カップルシステム管理",
    "cn": "💍 婚礼及情侣系统管理"
  },
  "💎 Cuốc Kim Cương Sắc Lẹm (+220 Luck)": {
    "en": "💎 Sharp Diamond Pickaxe (+220 Luck)",
    "ja": "💎 鋭いダイヤモンドのつるはし (+220 幸運)",
    "cn": "💎 锋利的钻石镐（+220 运气）"
  },
  "💎 Cần Câu Kim Cương (+75 Luck)": {
    "en": "💎 Diamond Fishing Rod (+75 Luck)",
    "ja": "💎 ダイヤモンド釣り竿 (+75 運)",
    "cn": "💎 钻石钓鱼竿（+75 运气）"
  },
  "💎 Kim Cương Tinh Khiết": {
    "en": "💎 Pure Diamond",
    "ja": "💎 ピュアダイヤモンド",
    "cn": "💎纯钻石"
  },
  "💎 Nhẫn Kim Cương Đính Hôn": {
    "en": "💎 Diamond Engagement Ring",
    "ja": "💎 ダイヤモンドの婚約指輪",
    "cn": "💎 钻石订婚戒指"
  },
  "💎 Rương Kho Báu Mẫu": {
    "en": "💎 Sample Treasure Chest",
    "ja": "💎 サンプル宝箱",
    "cn": "💎 宝箱样本"
  },
  "💎 Thẻ Fake Nitro Rickroll": {
    "en": "💎 Fake Nitro Rickroll Card",
    "ja": "💎 偽ニトロリックロールカード",
    "cn": "💎 假 Nitro Rickroll 卡"
  },
  "💐 Bó Hoa Hồng Lãng Mạn": {
    "en": "💐 Romantic Rose Bouquet",
    "ja": "💐 ロマンチックなバラの花束",
    "cn": "💐浪漫玫瑰花束"
  },
  "💖 0 Điểm": {
    "en": "💖 0 Points",
    "ja": "💖 0 ポイント",
    "cn": "💖 0 分"
  },
  "💖 Phân Kích Rễ Hồi Sinh": {
    "en": "💖 Revitalizing Root Division",
    "ja": "💖 根幹部門の活性化",
    "cn": "💖 振兴根部"
  },
  "💖 Tổng Lượt Claim": {
    "en": "💖 Total Claims",
    "ja": "💖 総クレーム数",
    "cn": "💖 索赔总额"
  },
  "💖 Xã Hội": {
    "en": "💖 Society",
    "ja": "💖 社会",
    "cn": "💖 社会"
  },
  "💖 Điều Chỉnh Lượt Claim": {
    "en": "💖 Adjust Number of Claims",
    "ja": "💖 クレーム数を調整する",
    "cn": "💖 调整索赔数量"
  },
  "💣 Khối Thuốc Nổ TNT Thượng Hạng": {
    "en": "💣 Premium TNT Explosive Block",
    "ja": "💣 プレミアム TNT 爆発ブロック",
    "cn": "💣 优质 TNT 炸药块"
  },
  "💣 Thẻ Bom Hẹn Giờ Troll": {
    "en": "💣 Troll Time Bomb Card",
    "ja": "💣 トロール時限爆弾カード",
    "cn": "💣 巨魔定时炸弹卡"
  },
  "💧 Nước Mắt Tiên Cá (+105 Luck)": {
    "en": "💧 Mermaid's Tears (+105 Luck)",
    "ja": "💧 人魚の涙 (+105 幸運)",
    "cn": "💧 人鱼之泪（+105 运气）"
  },
  "💬 Giao Tiếp & Cấp Độ": {
    "en": "💬 Communication & Levels",
    "ja": "💬 コミュニケーションとレベル",
    "cn": "💬 沟通与水平"
  },
  "💬 Global Chat giữa các tài khoản — bấm icon 💬 góc dưới để chat!": {
    "en": "💬 Global Chat between accounts — click the icon 💬 in the bottom corner to chat!",
    "ja": "💬 アカウント間のグローバル チャット — チャットするには、下隅にあるアイコン 💬 をクリックしてください。",
    "cn": "💬 帐户之间的全球聊天 — 单击底角的图标 💬 进行聊天！"
  },
  "💬 Kênh Chat 2 Chiều (Discord &lt;-&gt; Minecraft):": {
    "en": "💬 2-Way Chat Channel (Discord <-> Minecraft):",
    "ja": "💬 双方向チャットチャンネル (Discord <-> Minecraft):",
    "cn": "💬 2 向聊天频道（Discord <-> Minecraft）："
  },
  "💰 Kinh Tế & Tiền Tệ": {
    "en": "💰 Economy & Currency",
    "ja": "💰 経済と通貨",
    "cn": "💰 经济与货币"
  },
  "💵 Cấp Phát Kinh Tế Cho Người Dùng": {
    "en": "💵 Economic Provision for Users",
    "ja": "💵 ユーザーへの経済的提供",
    "cn": "💵 为用户提供经济保障"
  },
  "📋 Danh Sách Người Dùng &amp; Quản Trị Viên Web": {
    "en": "📋 List of Users & Web Admins",
    "ja": "📋 ユーザーとウェブ管理者のリスト",
    "cn": "📋 用户和网络管理员列表"
  },
  "📎 Tệp đính kèm (Ảnh, File tài liệu, Zip... &lt; 25MB)": {
    "en": "📎 Attachments (Photos, Document Files, Zip... < 25MB)",
    "ja": "📎 添付ファイル (写真、ドキュメントファイル、Zip... < 25MB)",
    "cn": "📎 附件（照片、文档文件、Zip...< 25MB）"
  },
  "📜 Live Console & Nhật Ký": {
    "en": "📜 Live Console & Log",
    "ja": "📜 ライブコンソールとログ",
    "cn": "📜 实时控制台和日志"
  },
  "📝 Thẻ Đổi Biệt Danh Nickname": {
    "en": "📝 Nickname Change Card",
    "ja": "📝 ニックネーム変更カード",
    "cn": "📝 昵称变更卡"
  },
  "📦 Các Lệnh Khác": {
    "en": "📦 Other Commands",
    "ja": "📦 その他のコマンド",
    "cn": "📦 其他命令"
  },
  "📦 Hộp Quà Lừa Tình Hù Dọa": {
    "en": "📦 Scare Love Cheat Gift Box",
    "ja": "📦 スケアラブチートギフトボックス",
    "cn": "📦 吓爱作弊礼盒"
  },
  "📦 Rương Gỗ Trôi Dạt": {
    "en": "📦 Driftwood Chest",
    "ja": "📦 流木チェスト",
    "cn": "📦 浮木箱"
  },
  "📦 Tiêu hao": {
    "en": "📦 Consumption",
    "ja": "📦 消費",
    "cn": "📦消费"
  },
  "🔀 Thẻ Đảo Ngược Ngôn Từ": {
    "en": "🔀 Word Reversal Card",
    "ja": "🔀 単語反転カード",
    "cn": "🔀 单词反转卡"
  },
  "🔄 Làm Mới Số Liệu": {
    "en": "🔄 Refresh Data",
    "ja": "🔄 データを更新",
    "cn": "🔄 刷新数据"
  },
  "🔇 Thẻ Khóa Mõm (Timeout 30s)": {
    "en": "🔇 Muzzle Lock Card (Timeout 30s)",
    "ja": "🔇 マズルロックカード (タイムアウト30秒)",
    "cn": "🔇枪口锁卡（超时30秒）"
  },
  "🔊 Thẻ Trục Xuất Khỏi Voice": {
    "en": "🔊 Voice Expulsion Card",
    "ja": "🔊 音声排除カード",
    "cn": "🔊 语音驱逐卡"
  },
  "🔌 Lệnh Plugin Sakura & Hướng Dẫn Kết Nối": {
    "en": "🔌 Sakura Plugin Commands & Connection Instructions",
    "ja": "🔌 さくらプラグインのコマンドと接続手順",
    "cn": "🔌 Sakura 插件命令和连接说明"
  },
  "🔍 Tra Cứu Người Chơi": {
    "en": "🔍 Look Up Players",
    "ja": "🔍 プレーヤーを検索",
    "cn": "🔍 查找玩家"
  },
  "🔍 Tìm kiếm tên hoặc mô tả thành tựu...": {
    "en": "🔍 Search for achievement names or descriptions...",
    "ja": "🔍 実績の名前または説明を検索します...",
    "cn": "🔍 搜索成就名称或描述..."
  },
  "🔐 Mã hóa &amp; Giải mã": {
    "en": "🔐 Encoding & Decoding",
    "ja": "🔐 エンコードとデコード",
    "cn": "🔐 编码与解码"
  },
  "🔑 Chìa Khóa Bạc": {
    "en": "🔑 Silver Key",
    "ja": "🔑 銀の鍵",
    "cn": "🔑 银钥匙"
  },
  "🔥 Phượng Hoàng Lửa Đại Dương (+80 Luck)": {
    "en": "🔥 Ocean Fire Phoenix (+80 Luck)",
    "ja": "🔥 オーシャン ファイアー フェニックス (+80 運)",
    "cn": "🔥 海火凤凰（+80 运气）"
  },
  "🔨 Đã nạp Preset Thần Rèn (+5x đập đồ). Đang lưu...": {
    "en": "🔨 Loaded with God of Forging Preset (+5x smashing items). Saving...",
    "ja": "🔨 God of Forging プリセットがロードされています (+5x 破壊アイテム)。保存中...",
    "cn": "🔨 装载了锻造之神预设（+5x 粉碎物品）。正在保存..."
  },
  "🔮 Cuốc Tinh Thể Vô Cực (+700 Luck)": {
    "en": "🔮 Infinity Crystal Pickaxe (+700 Luck)",
    "ja": "🔮 インフィニティクリスタルつるはし (+700 幸運)",
    "cn": "🔮无限水晶镐（+700 运气）"
  },
  "🔮 Cần Vô Cực Hư Không (+1200 Luck)": {
    "en": "🔮 Need Infinity Void (+1200 Luck)",
    "ja": "🔮 インフィニティボイドが必要 (+1200 幸運)",
    "cn": "🔮 需要无限虚空（+1200 运气）"
  },
  "🔮 Ngọc Trai Cổ Đại": {
    "en": "🔮 Ancient Pearl",
    "ja": "🔮古代の真珠",
    "cn": "🔮古珍珠"
  },
  "🔮 Rương Ẩn Đặc Biệt": {
    "en": "🔮 Special Hidden Chest",
    "ja": "🔮 特別な隠しチェスト",
    "cn": "🔮特殊隐藏宝箱"
  },
  "🔱 Cần Hải Thần Poseidon (+160 Luck)": {
    "en": "🔱 Need the Sea God Poseidon (+160 Luck)",
    "ja": "🔱 海神ポセイドンが必要 (+160 幸運)",
    "cn": "🔱需要海神波塞冬（+160幸运）"
  },
  "🔲 Hắc Diện Thạch Hắc Ám": {
    "en": "🔲 Dark Obsidian",
    "ja": "🔲 ダークオブシディアン",
    "cn": "🔲 黑曜石"
  },
  "🔴 Bot tắt": {
    "en": "🔴 Bot turns off",
    "ja": "🔴 ボットがオフになる",
    "cn": "🔴 机器人关闭"
  },
  "🔴 Gặp sự cố (sự cố)": {
    "en": "🔴 Having trouble (crash)",
    "ja": "🔴 トラブル（クラッシュ）",
    "cn": "🔴 遇到麻烦（崩溃）"
  },
  "🔴 Hồng Ngọc Huyết Long": {
    "en": "🔴 Blood Dragon Ruby",
    "ja": "🔴ブラッドドラゴンルビー",
    "cn": "🔴血龙红宝石"
  },
  "🔴 LỖI KẾT NỐI": {
    "en": "🔴 CONNECTION ERROR",
    "ja": "🔴 接続エラー",
    "cn": "🔴 连接错误"
  },
  "🔴 THẦN THOẠI": {
    "en": "🔴 MYTH",
    "ja": "🔴 神話",
    "cn": "🔴神话"
  },
  "🔴 Tắt Yêu Cầu Vote": {
    "en": "🔴 Turn off Request Vote",
    "ja": "🔴 投票リクエストをオフにする",
    "cn": "🔴 关闭请求投票"
  },
  "🔴 ĐANG TẮT (Tạm tắt do bot chưa duyệt)": {
    "en": "🔴 CURRENTLY OFF (Temporarily turned off because the bot hasn't approved yet)",
    "ja": "🔴 現在オフ (ボットがまだ承認していないため、一時的にオフになっています)",
    "cn": "🔴当前已关闭（由于机器人尚未批准而暂时关闭）"
  },
  "🔴 Đã hết hạn (sau 20h30)": {
    "en": "🔴 Expired (after 8:30 p.m.)",
    "ja": "🔴 期限切れ（20:30以降）",
    "cn": "🔴已过期（晚上8:30之后）"
  },
  "🔵 HIẾM": {
    "en": "🔵 RARE",
    "ja": "🔵 珍しい",
    "cn": "🔵 稀有"
  },
  "🔶 Hoàng Ngọc Topaz": {
    "en": "🔶 Hoang Ngoc Topaz",
    "ja": "🔶 ホアンゴックトパーズ",
    "cn": "🔶 黄玉黄玉"
  },
  "🔷 Lam Ngọc Biển Cả": {
    "en": "🔷 Sea Turquoise",
    "ja": "🔷 シーターコイズ",
    "cn": "🔷 海绿松石"
  },
  "🕵️ Ẩn Danh (Giấu ký tự &amp; độ dài)": {
    "en": "🕵️ Anonymous (Hide characters & length)",
    "ja": "🕵️ 匿名 (文字と長さを非表示)",
    "cn": "🕵️匿名（隐藏字符和长度）"
  },
  "🖤 Cuốc Netherite Dung Nham (+400 Luck)": {
    "en": "🖤 Lava Netherite Pickaxe (+400 Luck)",
    "ja": "🖤 溶岩ネザライトのつるはし (+400 幸運)",
    "cn": "🖤 熔岩下界合金镐（+400 运气）"
  },
  "🖤 Cần Hắc Diện Thạch (+55 Luck)": {
    "en": "🖤 Need Obsidian (+55 Luck)",
    "ja": "🖤 黒曜石が必要 (+55 運)",
    "cn": "🖤 需要黑曜石（+55 运气）"
  },
  "🗝️ Chìa Khóa Tàu Cổ": {
    "en": "🗝️ Ancient Ship Key",
    "ja": "🗝️ 古代の船の鍵",
    "cn": "🗝️古船钥匙"
  },
  "🗺️ Bản Đồ Kho Báu (+100% Luck)": {
    "en": "🗺️ Treasure Map (+100% Luck)",
    "ja": "🗺️ 宝の地図 (+100% 運)",
    "cn": "🗺️ 藏宝图（+100% 运气）"
  },
  "🗿 Đá Trấn Hải (Bảo Toàn Bền)": {
    "en": "🗿 Tran Hai Stone (Durable Preservation)",
    "ja": "🗿 トランハイストーン (耐久性のある保存)",
    "cn": "🗿 陈海石（持久保存）"
  },
  "🚀 Dịch Chuyển & Nhà Cửa": {
    "en": "🚀 Moving & Housing",
    "ja": "🚀 引っ越しと住居",
    "cn": "🚀 搬家和住房"
  },
  "🚜 Quản Trị Hệ Thống Nông Trại": {
    "en": "🚜 Farm System Administration",
    "ja": "🚜 ファームシステム管理",
    "cn": "🚜 农场系统管理"
  },
  "🛑 Tắt Toàn Cục": {
    "en": "🛑 Turn Off Globally",
    "ja": "🛑 グローバルにオフにする",
    "cn": "🛑 全局关闭"
  },
  "🛒 Quản Trị Hệ Thống Cửa Hàng & Sáng Tạo Vật Phẩm": {
    "en": "🛒 Store System Management & Item Creation",
    "ja": "🛒 ストアシステム管理とアイテム作成",
    "cn": "🛒 商店系统管理和商品创建"
  },
  "🛡️ Bảo Mật & Hệ Thống Anti": {
    "en": "🛡️ Security & Anti System",
    "ja": "🛡️ セキュリティとアンチシステム",
    "cn": "🛡️ 安全与反系统"
  },
  "🛡️ Khiên Bảo Vệ Miễn Nhiễm Troll": {
    "en": "🛡️ Troll Immunity Shield",
    "ja": "🛡️ トロール免疫シールド",
    "cn": "🛡️巨魔免疫盾"
  },
  "🛡️ Sinh Tồn & Lãnh Thổ": {
    "en": "🛡️ Survival & Territory",
    "ja": "🛡️ サバイバルと領土",
    "cn": "🛡️ 生存与领土"
  },
  "🟡 Chưa phát hôm nay": {
    "en": "🟡 Not distributed today",
    "ja": "🟡 本日は配布されません",
    "cn": "🟡今天没有分发"
  },
  "🟡 HUYỀN THOẠI": {
    "en": "🟡 LEGENDARY",
    "ja": "🟡 伝説の",
    "cn": "🟡传奇"
  },
  "🟢 Bot đang chạy": {
    "en": "🟢 Bot is running",
    "ja": "🟢 ボットが実行中です",
    "cn": "🟢 机器人正在运行"
  },
  "🟢 Bật Yêu Cầu Vote": {
    "en": "🟢 Turn on Vote Request",
    "ja": "🟢 投票リクエストをオンにする",
    "cn": "🟢 开启投票请求"
  },
  "🟢 Ngọc Lục Bảo Đế Vương": {
    "en": "🟢 Imperial Emerald",
    "ja": "🟢 インペリアルエメラルド",
    "cn": "🟢 帝王祖母绿"
  },
  "🟢 ĐANG BẬT": {
    "en": "🟢 IS ON",
    "ja": "🟢がオンです",
    "cn": "🟢 已开启"
  },
  "🟢 Đang hoạt động": {
    "en": "🟢 Active",
    "ja": "🟢 アクティブ",
    "cn": "🟢 活跃"
  },
  "🟢 Đã Kết Nối (Hoạt Động)": {
    "en": "🟢 Connected (Active)",
    "ja": "🟢 接続済み (アクティブ)",
    "cn": "🟢 已连接（活动）"
  },
  "🟢 Ổn định (ổn)": {
    "en": "🟢 Stable (fine)",
    "ja": "🟢 安定（良好）",
    "cn": "🟢稳定（良好）"
  },
  "🟣 SỬ THI": {
    "en": "🟣 EPIC",
    "ja": "🟣 エピック",
    "cn": "🟣 史诗般的"
  },
  "🟣 Thạch Anh Tím Hoàng Triều": {
    "en": "🟣 Royal Amethyst",
    "ja": "🟣 ロイヤルアメジスト",
    "cn": "🟣 皇家紫水晶"
  },
  "🟫 Đồng Thô Cổ Điển": {
    "en": "🟫 Classic Raw Copper",
    "ja": "🟫 クラシックな生銅",
    "cn": "🟫 经典原铜"
  },
  "🤖 Cấu Hình AI & Voice TTS": {
    "en": "🤖 AI & Voice TTS Configuration",
    "ja": "🤖 AI と音声 TTS 構成",
    "cn": "🤖 AI 和语音 TTS 配置"
  },
  "🤖 Cần Cơ Khí Thủy Triều (+105 Luck)": {
    "en": "🤖 Need Tidal Mechanic (+105 Luck)",
    "ja": "🤖 潮汐力士が必要 (+105 運)",
    "cn": "🤖 需要潮汐机械师（+105 运气）"
  },
  "🥇 Quán Quân Sưu Tầm": {
    "en": "🥇 Collection Champion",
    "ja": "🥇 コレクションチャンピオン",
    "cn": "🥇 收藏冠军"
  },
  "🥈 Bình Tưới Bạc": {
    "en": "🥈 Silver Watering Can",
    "ja": "🥈 銀のじょうろ",
    "cn": "🥈 银色喷壶"
  },
  "🥈 Bạc Ánh Trăng": {
    "en": "🥈 Moonlight Silver",
    "ja": "🥈 ムーンライトシルバー",
    "cn": "🥈 月光银"
  },
  "🥕 Cà Rốt Giòn Ngọt": {
    "en": "🥕 Sweet and Crispy Carrot",
    "ja": "🥕 甘くてシャキシャキしたニンジン",
    "cn": "🥕 香甜脆脆的胡萝卜"
  },
  "🥕 Hạt Giống Cà Rốt": {
    "en": "🥕 Carrot Seeds",
    "ja": "🥕 ニンジンの種",
    "cn": "🥕 胡萝卜种子"
  },
  "🥬 Cây Cải Thìa Xanh": {
    "en": "🥬 Green Bok Choy",
    "ja": "🥬 青梗菜",
    "cn": "🥬 绿白菜"
  },
  "🥬 Hạt Giống Cải Thìa": {
    "en": "🥬 Bok Choy Seeds",
    "ja": "🥬チンゲンサイの種子",
    "cn": "🥬 白菜种子"
  },
  "🦊 Hồ Ly Cửu Vĩ Tinh Tú (+150 Luck, x2 Giá)": {
    "en": "🦊 Nine-Tailed Star Fox (+150 Luck, x2 Price)",
    "ja": "🦊 九尾のスターフォックス (+150 幸運、x2 価格)",
    "cn": "🦊 九尾星狐（+150 运气，x2 价格）"
  },
  "🦑 Xúc Tu Kraken (+160 Luck)": {
    "en": "🦑 Kraken Tentacles (+160 Luck)",
    "ja": "🦑 クラーケンの触手 (+160 幸運)",
    "cn": "🦑 海妖触手（+160 运气）"
  },
  "🦖 Hóa Thạch Rồng Tiền Sử": {
    "en": "🦖 Prehistoric Dragon Fossils",
    "ja": "🦖 先史時代のドラゴンの化石",
    "cn": "🦖 史前龙化石"
  },
  "🦦 Rái Cá Lặn (+15 Luck, +15% Mồi)": {
    "en": "🦦 Diving Otter (+15 Luck, +15% Lure)",
    "ja": "🦦 ダイビングカワウソ (+15 運、+15% ルアー)",
    "cn": "🦦 潜水水獭（+15 运气，+15% 诱饵）"
  },
  "🦹 Bàn Tay Đạo Tặc Móc Trộm Cá": {
    "en": "🦹 Thief's Hand Stealing Fish",
    "ja": "🦹 魚を盗む泥棒の手",
    "cn": "🦹贼手偷鱼"
  },
  "🧄 Củ Tỏi Tía Thơm": {
    "en": "🧄 Fragrant Purple Garlic",
    "ja": "🧄香り豊かな紫にんにく",
    "cn": "🧄 香喷喷的紫蒜"
  },
  "🧄 Hạt Giống Tỏi Thơm": {
    "en": "🧄 Fragrant Garlic Seeds",
    "ja": "🧄 香りのよいニンニクの種",
    "cn": "🧄 香蒜籽"
  },
  "🧅 Củ Hành Tây Ngọt": {
    "en": "🧅 Sweet Onion",
    "ja": "🧅 スイートオニオン",
    "cn": "🧅 甜洋葱"
  },
  "🧅 Hạt Giống Hành Tây": {
    "en": "🧅 Onion Seeds",
    "ja": "🧅 タマネギの種",
    "cn": "🧅 洋葱种子"
  },
  "🧊 Bom Băng Giá Khóa Cần 2m": {
    "en": "🧊 Frost Bomb Lock Needs 2m",
    "ja": "🧊 フロストボムロックには2m必要",
    "cn": "🧊 冰霜炸弹锁需要2m"
  },
  "🧤 Bao Tay Nhà Nông": {
    "en": "🧤 Farmer's Gloves",
    "ja": "🧤 農家の手袋",
    "cn": "🧤 农民手套"
  },
  "🧨 Kíp Nổ Dynamite Mini": {
    "en": "🧨 Dynamite Mini Detonator",
    "ja": "🧨 ダイナマイト ミニ起爆装置",
    "cn": "🧨 迷你炸药雷管"
  },
  "🧪 Dầu Bôi Trơn Mũi Khoan (CD 4s)": {
    "en": "🧪 Drill Bit Lubricant (CD 4s)",
    "ja": "🧪 ドリルビット潤滑剤 (CD 4)",
    "cn": "🧪 钻头润滑剂 (CD 4s)"
  },
  "🧰 Tiện Ích": {
    "en": "🧰 Utilities",
    "ja": "🧰 ユーティリティ",
    "cn": "🧰 实用工具"
  },
  "🧱 Kim Loại Netherite Địa Ngục": {
    "en": "🧱 Hellish Netherite Metal",
    "ja": "🧱 地獄のネザライトメタル",
    "cn": "🧱 地狱下界金属"
  },
  "🧵 Nối Từ": {
    "en": "🧵 Connecting Words",
    "ja": "🧵 接続する言葉",
    "cn": "🧵 连接单词"
  },
  "🧸 Gấu Bông Đáng Yêu": {
    "en": "🧸 Lovely Teddy Bear",
    "ja": "🧸 素敵なテディベア",
    "cn": "🧸 可爱的泰迪熊"
  },
  "🧿 Lapis Thần Bí": {
    "en": "🧿 Mystical Lapis",
    "ja": "🧿 神秘的なラピス",
    "cn": "🧿 神秘的青金石"
  },
  "🩸 Mồi Huyết Phượng Hoàng (+150 Luck)": {
    "en": "🩸 Phoenix Blood Lure (+150 Luck)",
    "ja": "🩸 フェニックス ブラッド ルアー (+150 幸運)",
    "cn": "🩸 凤凰血饵（+150 运气）"
  },
  "🩸 Mồi Máu Rồng (+80 Luck)": {
    "en": "🩸 Dragon Blood Lure (+80 Luck)",
    "ja": "🩸 ドラゴンブラッド ルアー (+80 運)",
    "cn": "🩸 龙血诱饵（+80 运气）"
  },
  "🪐 Mồi Lõi Vũ Trụ (+300 Luck)": {
    "en": "🪐 Cosmic Core Lure (+300 Luck)",
    "ja": "🪐 コズミックコア ルアー (+300 運)",
    "cn": "🪐 宇宙核心诱饵（+300 运气）"
  },
  "🪐 Mồi Vũ Trụ (+350 Luck)": {
    "en": "🪐 Cosmic Lure (+350 Luck)",
    "ja": "🪐 コズミック ルアー (+350 運)",
    "cn": "🪐 宇宙诱饵（+350 运气）"
  },
  "🪙 Cuốc Vàng Hoàng Kim (+110 Luck)": {
    "en": "🪙 Golden Pickaxe (+110 Luck)",
    "ja": "🪙 黄金のつるはし (+110 幸運)",
    "cn": "🪙 金镐（+110 运气）"
  },
  "🪙 Mồi Hoàng Kim (+200 Luck)": {
    "en": "🪙 Golden Lure (+200 Luck)",
    "ja": "🪙 ゴールデンルアー (+200 幸運)",
    "cn": "🪙 黄金诱饵（+200 运气）"
  },
  "🪙 Rương Bạc Chìm Biển Sâu": {
    "en": "🪙 Deep Sea Sunken Silver Chest",
    "ja": "🪙 深海に沈んだ銀の宝箱",
    "cn": "🪙 深海沉没银箱"
  },
  "🪙 Vàng Khối Tinh Khiết": {
    "en": "🪙 Pure Solid Gold",
    "ja": "🪙 純金",
    "cn": "🪙纯金"
  },
  "🪙 Vảy Rồng Vàng (+50% Giá Cá)": {
    "en": "🪙 Golden Dragon Scale (+50% Fish Price)",
    "ja": "🪙 ゴールデンドラゴンの鱗 (+50% 魚の価格)",
    "cn": "🪙金龙鳞片（+50%鱼价）"
  },
  "🪙 Đồng Bộ & Quy Đổi Coins Discord &lt;-&gt; Minecraft": {
    "en": "🪙 Synchronize & Convert Coins Discord <-> Minecraft",
    "ja": "🪙 コインの同期と変換 Discord <-> Minecraft",
    "cn": "🪙 同步和转换硬币 Discord <-> Minecraft"
  },
  "🪞 Gương Phản Chiếu Đòn Troll": {
    "en": "🪞 Troll Attack Mirror",
    "ja": "🪞 トロール攻撃ミラー",
    "cn": "🪞 巨魔攻击镜子"
  },
  "🪣 Bình Tưới Đồng": {
    "en": "🪣 Copper Watering Can",
    "ja": "🪣 銅製じょうろ",
    "cn": "🪣 铜喷壶"
  },
  "🪨 Cuốc Đá Trầm Tích (+20 Luck)": {
    "en": "🪨 Sediment Rock Pickaxe (+20 Luck)",
    "ja": "🪨 堆積岩のつるはし (+20 運)",
    "cn": "🪨 沉积岩镐（+20 运气）"
  },
  "🪨 Đá Hoa Cương": {
    "en": "🪨 Granite",
    "ja": "🪨 花崗岩",
    "cn": "🪨 花岗岩"
  },
  "🪱 Mồi Câu Nguyền Rủa 100% Rác": {
    "en": "🪱 Cursed Fishing Lure 100% Garbage",
    "ja": "🪱 呪われた釣りルアー 100% ゴミ",
    "cn": "🪱 被诅咒的鱼饵 100% 垃圾"
  },
  "🪱 Mồi Hiếm (+10 Luck)": {
    "en": "🪱 Rare Lure (+10 Luck)",
    "ja": "🪱 レア ルアー (+10 運)",
    "cn": "🪱 稀有诱饵（+10 运气）"
  },
  "🪱 Mồi Huyền Thoại (+55 Luck)": {
    "en": "🪱 Legendary Lure (+55 Luck)",
    "ja": "🪱 伝説のルアー (+55 運)",
    "cn": "🪱 传奇鱼饵（+55 运气）"
  },
  "🪱 Mồi Sử Thi (+22 Luck)": {
    "en": "🪱 Epic Lure (+22 Luck)",
    "ja": "🪱 エピック ルアー (+22 運)",
    "cn": "🪱 史诗诱饵（+22 运气）"
  },
  "🪱 Mồi Thường (+3 Luck)": {
    "en": "🪱 Normal Lure (+3 Luck)",
    "ja": "🪱 ノーマルルアー (+3 運)",
    "cn": "🪱 普通诱饵（+3 运气）"
  },
  "🪵 Cuốc Gỗ Sơ Cấp": {
    "en": "🪵 Beginner Wooden Hoe",
    "ja": "🪵 初心者用木鍬",
    "cn": "🪵初级木锄头"
  },
  "🪷 Hạt Giống Sen Tuyết": {
    "en": "🪷 Snow Lotus Seeds",
    "ja": "🪷 雪蓮の種",
    "cn": "🪷 雪莲子"
  },
  "🪷 Tuyết Liên Vạn Năm": {
    "en": "🪷 Ten Thousand Years of Snow",
    "ja": "🪷 一万年の雪",
    "cn": "🪷万年雪"
  },
  "🪸 Cần San Hô Cổ (+26 Luck)": {
    "en": "🪸 Ancient Coral Needle (+26 Luck)",
    "ja": "🪸 古代サンゴの針 (+26 幸運)",
    "cn": "🪸 远古珊瑚针（+26 运气）"
  },
  "🪸 Rương San Hô": {
    "en": "🪸 Coral Chest",
    "ja": "🪸 サンゴチェスト",
    "cn": "🪸 珊瑚箱"
  }
};

  
  const LOWER_PHRASES = {};
  for (const k in PHRASES) {
    LOWER_PHRASES[k.toLowerCase()] = PHRASES[k];
  }

  
  const EMOJI_PREFIX_REGEX = /^([\p{Extended_Pictographic}\u200d\uFE0F\u20E3\u2600-\u2B55\u2300-\u23FF]|\s)+/u;
  const EMOJI_SUFFIX_REGEX = /([\p{Extended_Pictographic}\u200d\uFE0F\u20E3\u2600-\u2B55\u2300-\u23FF]|\s)+$/u;
  const TRAILING_PUNCT_REGEX = /([:!?.,…]+)$/;
  const TRAILING_COUNT_REGEX = /(\s*[\(\[]\d+.*?[\)\]])$/;

  
  const COMPOUND_PATTERNS = [
    { vi: /^Thời gian hoạt động:\s*/i, en: "Active Uptime: ", ja: "稼働時間: ", cn: "运行时间: " },
    { vi: /^Thời gian hoạt động\s*:\s*/i, en: "Active Uptime: ", ja: "稼働時間: ", cn: "运行时间: " },
    { vi: /^Độ trễ:\s*/i, en: "Latency: ", ja: "遅延: ", cn: "延迟: " },
    { vi: /^Độ trễ\s*:\s*/i, en: "Latency: ", ja: "遅延: ", cn: "延迟: " },
    { vi: /^Số người:\s*/i, en: "Users: ", ja: "人数: ", cn: "人数: " },
    { vi: /^Cấp độ:\s*/i, en: "Level: ", ja: "レベル: ", cn: "等级: " },
    { vi: /^Điểm số:\s*/i, en: "Score: ", ja: "スコア: ", cn: "分数: " },
    { vi: /^Trạng thái:\s*/i, en: "Status: ", ja: "状態: ", cn: "状态: " },
    { vi: /^Bộ ảnh gồm:\s*/i, en: "Album contains: ", ja: "アルバム写真数: ", cn: "相册包含: " },
    { vi: /^Đang xem:\s*/i, en: "Viewing: ", ja: "表示中: ", cn: "正在查看: " },
    { vi: /^Kênh:\s*/i, en: "Channel: ", ja: "チャンネル: ", cn: "频道: " },
    { vi: /^Nhạc nền:\s*/i, en: "Music: ", ja: "音楽: ", cn: "背景音乐: " },
    { vi: /^Âm thanh nền:\s*/i, en: "Background Audio: ", ja: "BGM: ", cn: "背景音频: " }
  ];

  function getStoredLanguage() {
    try {
      const saved = localStorage.getItem(LANG_STORAGE_KEY);
      if (saved && LANGUAGES[saved]) return saved;
    } catch (e) {}
    try {
      const browserLang = (navigator.language || navigator.userLanguage || '').toLowerCase();
      if (browserLang.startsWith('vi')) return 'vi';
      if (browserLang.startsWith('ja')) return 'ja';
      if (browserLang.startsWith('zh') || browserLang.startsWith('cn')) return 'cn';
      if (browserLang.startsWith('en')) return 'en';
    } catch (e) {}
    return 'vi';
  }

  function getPhrase(text, targetLang) {
    if (!text || targetLang === 'vi') return text;
    
    if (PHRASES[text] && PHRASES[text][targetLang]) {
      return PHRASES[text][targetLang];
    }
    
    const lower = text.toLowerCase();
    if (LOWER_PHRASES[lower] && LOWER_PHRASES[lower][targetLang]) {
      return LOWER_PHRASES[lower][targetLang];
    }
    return null;
  }

  
  function translateString(str, targetLang) {
    if (!str || typeof str !== 'string') return str;
    if (targetLang === 'vi') return str;

    const trimmed = str.trim();
    if (!trimmed) return str;

    const leadingWs = str.match(/^\s*/)[0];
    const trailingWs = str.match(/\s*$/)[0];

    
    const normalized = trimmed.replace(/\s+/g, ' ');

    
    let direct = getPhrase(normalized, targetLang);
    if (direct) {
      return leadingWs + direct + trailingWs;
    }

    
    let clean = normalized;
    let prefixEmoji = '';
    let suffixEmoji = '';
    let suffixCount = '';
    let suffixPunct = '';

    const mEmojiStart = clean.match(EMOJI_PREFIX_REGEX);
    if (mEmojiStart) {
      prefixEmoji = mEmojiStart[0];
      clean = clean.slice(prefixEmoji.length).trim();
    }

    const mEmojiEnd = clean.match(EMOJI_SUFFIX_REGEX);
    if (mEmojiEnd && clean.length > mEmojiEnd[0].length) {
      suffixEmoji = mEmojiEnd[0];
      clean = clean.slice(0, -suffixEmoji.length).trim();
    }

    const mCount = clean.match(TRAILING_COUNT_REGEX);
    if (mCount) {
      suffixCount = mCount[0];
      clean = clean.slice(0, -suffixCount.length).trim();
    }

    const mPunct = clean.match(TRAILING_PUNCT_REGEX);
    if (mPunct) {
      suffixPunct = mPunct[0];
      clean = clean.slice(0, -suffixPunct.length).trim();
    }

    let matchStripped = getPhrase(clean, targetLang);
    if (matchStripped) {
      return leadingWs + prefixEmoji + matchStripped + suffixPunct + suffixCount + suffixEmoji + trailingWs;
    }

    
    for (const p of COMPOUND_PATTERNS) {
      if (p.vi.test(normalized)) {
        const prefix = p[targetLang] || p.en;
        const remainder = normalized.replace(p.vi, '');
        return leadingWs + prefix + remainder + trailingWs;
      }
    }

    return str;
  }

  
  let isTranslating = false;
  function translateDOM(root, targetLang) {
    if (!root || isTranslating || typeof document === 'undefined') return;
    isTranslating = true;

    try {
      
      if (typeof document.createTreeWalker === 'function') {
        const walker = document.createTreeWalker(
          root,
          NodeFilter.SHOW_TEXT,
          {
            acceptNode: function (node) {
              if (!node || !node.nodeValue) return NodeFilter.FILTER_REJECT;
              const parent = node.parentElement;
              if (!parent) return NodeFilter.FILTER_REJECT;
              const tag = parent.tagName;
              if (tag === 'SCRIPT' || tag === 'STYLE' || tag === 'NOSCRIPT' || tag === 'CODE' || tag === 'PRE' || tag === 'TEXTAREA') {
                return NodeFilter.FILTER_REJECT;
              }
              if (parent.hasAttribute('data-no-i18n') || parent.closest('[data-no-i18n]')) {
                return NodeFilter.FILTER_REJECT;
              }
              if (node.nodeValue.trim().length === 0) {
                return NodeFilter.FILTER_SKIP;
              }
              return NodeFilter.FILTER_ACCEPT;
            }
          }
        );

        let textNode;
        while ((textNode = walker.nextNode())) {
          if (textNode._sakuraOrig === undefined) {
            textNode._sakuraOrig = textNode.nodeValue;
          }

          if (targetLang === 'vi') {
            if (textNode.nodeValue !== textNode._sakuraOrig) {
              textNode.nodeValue = textNode._sakuraOrig;
            }
          } else {
            const translated = translateString(textNode._sakuraOrig, targetLang);
            if (translated && translated !== textNode.nodeValue) {
              textNode.nodeValue = translated;
            }
          }
        }
      }

      
      if (typeof root.querySelectorAll === 'function') {
        const elementsWithAttrs = (root === document.body ? document : root).querySelectorAll(
          '[placeholder], [title], [aria-label], input[type="button"], input[type="submit"], input[type="reset"], [data-i18n], [data-i18n-placeholder], [data-i18n-title], [data-i18n-html]'
        );

        elementsWithAttrs.forEach(el => {
          
          if (el.hasAttribute('data-i18n')) {
            const k = el.getAttribute('data-i18n');
            const phrase = getPhrase(k, targetLang) || getPhrase(el.textContent.trim(), targetLang);
            if (phrase) el.textContent = phrase;
          }
          if (el.hasAttribute('data-i18n-html')) {
            const k = el.getAttribute('data-i18n-html');
            const phrase = getPhrase(k, targetLang);
            if (phrase) el.innerHTML = phrase;
          }

          
          const placeholder = el.getAttribute('placeholder');
          if (placeholder) {
            if (el._sakuraOrigPlaceholder === undefined) {
              el._sakuraOrigPlaceholder = placeholder;
            }
            if (targetLang === 'vi') {
              el.setAttribute('placeholder', el._sakuraOrigPlaceholder);
            } else {
              el.setAttribute('placeholder', translateString(el._sakuraOrigPlaceholder, targetLang));
            }
          }

          
          const title = el.getAttribute('title');
          if (title && !el.classList.contains('lang-switch-btn')) {
            if (el._sakuraOrigTitle === undefined) {
              el._sakuraOrigTitle = title;
            }
            if (targetLang === 'vi') {
              el.setAttribute('title', el._sakuraOrigTitle);
            } else {
              el.setAttribute('title', translateString(el._sakuraOrigTitle, targetLang));
            }
          }

          
          const ariaLabel = el.getAttribute('aria-label');
          if (ariaLabel && !el.classList.contains('lang-switch-btn')) {
            if (el._sakuraOrigAria === undefined) {
              el._sakuraOrigAria = ariaLabel;
            }
            if (targetLang === 'vi') {
              el.setAttribute('aria-label', el._sakuraOrigAria);
            } else {
              el.setAttribute('aria-label', translateString(el._sakuraOrigAria, targetLang));
            }
          }

          
          if (el.tagName === 'INPUT' && (el.type === 'button' || el.type === 'submit' || el.type === 'reset')) {
            if (el._sakuraOrigValue === undefined) {
              el._sakuraOrigValue = el.value;
            }
            if (targetLang === 'vi') {
              el.value = el._sakuraOrigValue;
            } else {
              el.value = translateString(el._sakuraOrigValue, targetLang);
            }
          }
        });
      }
    } finally {
      isTranslating = false;
    }
  }

  
  function applyLanguage(lang, showToast = false) {
    if (!LANGUAGES[lang]) lang = 'vi';
    try {
      localStorage.setItem(LANG_STORAGE_KEY, lang);
    } catch (e) {}

    if (typeof document !== 'undefined' && document.documentElement) {
      document.documentElement.setAttribute('lang', lang);
    }

    const langMeta = LANGUAGES[lang];

    
    if (typeof document !== 'undefined' && document.querySelectorAll) {
      document.querySelectorAll('.lang-switch-dropdown').forEach(dropdown => {
        const flagEl = dropdown.querySelector('.lang-flag');
        const codeEl = dropdown.querySelector('.lang-code');
        const btn = dropdown.querySelector('.lang-switch-btn');
        if (flagEl) flagEl.textContent = langMeta.flag;
        if (codeEl) codeEl.textContent = langMeta.code;
        if (btn) btn.setAttribute('title', `Language / Ngôn ngữ: ${langMeta.name}`);

        dropdown.querySelectorAll('.lang-option').forEach(opt => {
          const optLang = opt.getAttribute('data-lang');
          const isActive = optLang === lang;
          opt.classList.toggle('active', isActive);
          const checkEl = opt.querySelector('.lang-check');
          if (checkEl) checkEl.textContent = isActive ? '✓' : '';
        });
      });
    }

    
    if (typeof document !== 'undefined' && document.body) {
      translateDOM(document.body, lang);
    }

    
    if (typeof window !== 'undefined' && typeof window.dispatchEvent === 'function' && typeof CustomEvent === 'function') {
      window.dispatchEvent(new CustomEvent('sakuraLanguageChange', { detail: { lang, meta: langMeta } }));
    }

    if (showToast && typeof window !== 'undefined' && typeof window.showToast === 'function') {
      const toastMsg = lang === 'vi' ? '🌐 Đã chuyển ngôn ngữ sang Tiếng Việt' : (lang === 'ja' ? '🌐 言語を日本語に変更しました' : (lang === 'cn' ? '🌐 语言已切换为中文' : '🌐 Changed language to English'));
      window.showToast(toastMsg, 'info');
    }
  }

  
  function createLanguageDropdownElement(isFloating = false) {
    const currentLang = getStoredLanguage();
    const meta = LANGUAGES[currentLang] || LANGUAGES['vi'];

    const container = document.createElement('div');
    container.className = isFloating ? 'lang-switch-dropdown floating-lang-switch' : 'lang-switch-dropdown';
    container.setAttribute('data-sakura-injected', 'true');

    container.innerHTML = `
      <button type="button" class="lang-switch-btn" aria-label="Language / Ngôn ngữ" title="Language: ${meta.name}">
        <span class="lang-flag">${meta.flag}</span>
        <span class="lang-code">${meta.code}</span>
        <span class="lang-arrow">▾</span>
      </button>
      <div class="lang-menu">
        <button type="button" class="lang-option ${currentLang === 'vi' ? 'active' : ''}" data-lang="vi">
          <span>🇻🇳 Tiếng Việt</span>
          <span class="lang-check">${currentLang === 'vi' ? '✓' : ''}</span>
        </button>
        <button type="button" class="lang-option ${currentLang === 'en' ? 'active' : ''}" data-lang="en">
          <span>🇬🇧 English</span>
          <span class="lang-check">${currentLang === 'en' ? '✓' : ''}</span>
        </button>
        <button type="button" class="lang-option ${currentLang === 'ja' ? 'active' : ''}" data-lang="ja">
          <span>🇯🇵 日本語</span>
          <span class="lang-check">${currentLang === 'ja' ? '✓' : ''}</span>
        </button>
        <button type="button" class="lang-option ${currentLang === 'cn' ? 'active' : ''}" data-lang="cn">
          <span>🇨🇳 中文</span>
          <span class="lang-check">${currentLang === 'cn' ? '✓' : ''}</span>
        </button>
      </div>
    `;

    bindDropdownEvents(container);
    return container;
  }

  function bindDropdownEvents(container) {
    const btn = container.querySelector('.lang-switch-btn');
    if (!btn) return;

    btn.addEventListener('click', (e) => {
      e.stopPropagation();
      document.querySelectorAll('.lang-switch-dropdown.open').forEach(d => {
        if (d !== container) d.classList.remove('open');
      });
      container.classList.toggle('open');
    });

    container.querySelectorAll('.lang-option').forEach(opt => {
      opt.addEventListener('click', (e) => {
        e.stopPropagation();
        const selectedLang = opt.getAttribute('data-lang');
        applyLanguage(selectedLang, true);
        container.classList.remove('open');
      });
    });
  }

  function setupLanguageSwitchers() {
    if (typeof document === 'undefined' || !document.querySelectorAll) return;

    
    document.querySelectorAll('.lang-switch-dropdown').forEach(dropdown => {
      bindDropdownEvents(dropdown);
    });

    let switcherCount = document.querySelectorAll('.lang-switch-dropdown').length;

    
    document.querySelectorAll('.theme-toggle-btn').forEach(themeBtn => {
      const parent = themeBtn.parentElement;
      if (!parent) return;
      if (!parent.querySelector('.lang-switch-dropdown')) {
        const newDropdown = createLanguageDropdownElement(false);
        if (themeBtn.nextSibling) {
          parent.insertBefore(newDropdown, themeBtn.nextSibling);
        } else {
          parent.appendChild(newDropdown);
        }
        switcherCount++;
      }
    });

    
    if (switcherCount === 0) {
      const navTarget = document.querySelector('nav, .navbar, .top-header, .header-right, .account-nav, .tk-nav');
      if (navTarget) {
        const newDropdown = createLanguageDropdownElement(false);
        navTarget.appendChild(newDropdown);
      } else if (document.body) {
        const floatingDropdown = createLanguageDropdownElement(true);
        document.body.appendChild(floatingDropdown);
      }
    }

    
    document.addEventListener('click', () => {
      document.querySelectorAll('.lang-switch-dropdown.open').forEach(d => {
        d.classList.remove('open');
      });
    });
  }

  
  let observerTimeout = null;
  function setupMutationObserver() {
    if (typeof window === 'undefined' || !window.MutationObserver || typeof document === 'undefined' || !document.body) return;

    const observer = new MutationObserver(() => {
      const currentLang = getStoredLanguage();
      if (currentLang === 'vi' || isTranslating) return;

      if (observerTimeout) clearTimeout(observerTimeout);
      observerTimeout = setTimeout(() => {
        translateDOM(document.body, currentLang);
      }, 120);
    });

    observer.observe(document.body, { childList: true, subtree: true });
  }

  
  function setupToastInterceptor() {
    if (typeof window !== 'undefined' && typeof window.showToast === 'function') {
      const originalShowToast = window.showToast;
      window.showToast = function (msg, type) {
        const currentLang = getStoredLanguage();
        const translated = (currentLang !== 'vi' && typeof msg === 'string') ? translateString(msg, currentLang) : msg;
        return originalShowToast(translated, type);
      };
    }
  }

  
  const initialLang = getStoredLanguage();
  if (typeof document !== 'undefined' && document.documentElement) {
    document.documentElement.setAttribute('lang', initialLang);
  }

  
  if (typeof window !== 'undefined') {
    window.sakuraT = function (keyOrText) {
      const lang = (typeof document !== 'undefined' && document.documentElement && document.documentElement.getAttribute('lang')) || getStoredLanguage();
      return translateString(keyOrText, lang) || keyOrText;
    };
    window.t = window.sakuraT;
    window.setSakuraLanguage = applyLanguage;
    window.getSakuraLanguage = () => (typeof document !== 'undefined' && document.documentElement && document.documentElement.getAttribute('lang')) || getStoredLanguage();
    window.SAKURA_LANGUAGES = LANGUAGES;
    window.SAKURA_PHRASES = PHRASES;
  }

  
  function loadAsyncTranslations() {
    if (typeof fetch !== 'function') return;
    fetch('/static/js/translations.json')
      .then(r => r.json())
      .then(data => {
        if (data && typeof data === 'object') {
          Object.assign(PHRASES, data);
          for (const k in data) {
            LOWER_PHRASES[k.toLowerCase()] = data[k];
          }
          const curLang = getStoredLanguage();
          if (curLang !== 'vi' && typeof document !== 'undefined' && document.body) {
            translateDOM(document.body, curLang);
          }
        }
      })
      .catch(() => {});
  }

  
  function init() {
    setupLanguageSwitchers();
    applyLanguage(initialLang, false);
    setupMutationObserver();
    setupToastInterceptor();
    loadAsyncTranslations();
  }

  if (typeof document !== 'undefined') {
    if (document.readyState === 'loading') {
      document.addEventListener('DOMContentLoaded', init);
    } else {
      init();
    }
  }
})();
