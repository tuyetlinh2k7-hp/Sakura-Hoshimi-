


const state = {
    token: localStorage.getItem('sakura_auth_token') || '',
    activeTab: 'dashboard',
    botStatus: {},
    guilds: [],
    levels: [],
    antiSettings: {},
    mcStatus: {},
    allCommands: [],
    activeCmdCategory: 'all',
    logsWs: null,
    cpuHistory: [0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
    ramHistory: [0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
    chartInstance: null,
    currentUser: null,
    isAdmin: false,
    previewAsUser: localStorage.getItem('sakura_preview_as_user') === 'true',
    adminUsersList: [],
    adminUsersFilter: 'all',
    adminFishing: { activeSubTab: 'user', fishList: [], catalogs: {}, mutations: [], currentUser: null },
    adminFarm: { activeSubTab: 'user', currentUser: null, catalogs: null, currentCatTab: 'seeds' },
    adminMinecraft: { servers: [], currentServer: null, activeSubTab: 'terminal', ws: null }
};


async function checkAuthAndApplyRole() {
    if (!state.token) {
        const cookieMatch = document.cookie.match(/sakura_token=([^;]+)/);
        if (cookieMatch) state.token = cookieMatch[1];
    }
    if (!state.token) {
        location.href = '/login';
        return false;
    }
    try {
        const res = await fetch('/api/auth/me', { headers: { 'Authorization': `Bearer ${state.token}` } });
        if (res.status === 401) {
            localStorage.removeItem('sakura_auth_token');
            location.href = '/login';
            return false;
        }
        const data = await res.json();
        if (!data.ok) {
            localStorage.removeItem('sakura_auth_token');
            location.href = '/login';
            return false;
        }
        state.currentUser = data.user;
        state.user = data.user;
        state.isAdmin = !!data.user.is_admin;
        applyRoleUI();
        return true;
    } catch (e) {
        console.error('Auth check failed', e);
        return true; 
    }
}
function applyRoleUI() {
    const u = state.currentUser || {};
    const uName = String(u.username || '').toLowerCase();
    const dTag = String(u.discord_tag || (u.extra && u.extra.discord_tag) || '').toLowerCase();
    const isOwner = !!(u.is_owner || (u.extra && u.extra.is_owner) || uName.includes('linhxinh_dev') || dTag.includes('linhxinh_dev') || uName === 'owner' || uName === 'linhxinh');
    const isRealAdmin = state.isAdmin || isOwner;
    state.isOwner = isOwner;
    state.isRealAdmin = isRealAdmin;

    
    const isPreview = isRealAdmin && state.previewAsUser;
    const effectiveAdmin = isRealAdmin && !isPreview;

    const roleBadge = document.getElementById('roleBadge');
    const ownerHeaderBadge = document.getElementById('ownerHeaderBadge');
    const ownerCrownBadge = document.getElementById('ownerCrownBadge');
    const userNameEl = document.getElementById('currentUserName');
    const userRoleEl = document.getElementById('currentUserRole');
    const userAvatarEl = document.getElementById('currentUserAvatar');
    const banner = document.getElementById('userLimitedBanner');
    const btnPreview = document.getElementById('btnToggleUserPreview');
    const previewBanner = document.getElementById('userPreviewStickyBanner');

    
    if (btnPreview) {
        if (isRealAdmin) {
            btnPreview.style.display = 'inline-flex';
            if (isPreview) {
                btnPreview.innerHTML = '👑 Thoát Góc Nhìn User';
                btnPreview.style.background = 'linear-gradient(135deg, #f59e0b, #d97706)';
                btnPreview.title = 'Bấm để quay lại toàn quyền Quản Trị Viên';
            } else {
                btnPreview.innerHTML = '👁️ Góc Nhìn User';
                btnPreview.style.background = 'linear-gradient(135deg, #3b82f6, #1d4ed8)';
                btnPreview.title = 'Bấm để chuyển sang xem giao diện như người dùng thường';
            }
        } else {
            btnPreview.style.display = 'none';
        }
    }

    if (previewBanner) {
        previewBanner.style.display = isPreview ? 'flex' : 'none';
    }

    if (isPreview) {
        if (ownerHeaderBadge) ownerHeaderBadge.style.display = 'none';
        if (ownerCrownBadge) ownerCrownBadge.style.display = 'none';
        if (roleBadge) {
            roleBadge.style.display = 'inline-flex';
            roleBadge.textContent = '👁️ XEM TRƯỚC: User Thường';
            roleBadge.className = 'badge badge-green';
        }
        if (userRoleEl) userRoleEl.textContent = 'Đang xem trước góc nhìn người dùng';
    } else if (isOwner) {
        if (ownerHeaderBadge) ownerHeaderBadge.style.display = 'inline-flex';
        if (ownerCrownBadge) ownerCrownBadge.style.display = 'inline-block';
        if (roleBadge) {
            roleBadge.style.display = 'none';
        }
        if (userRoleEl) userRoleEl.textContent = '👑 Chủ Bot (@linhxinh_dev)';
    } else {
        if (ownerHeaderBadge) ownerHeaderBadge.style.display = 'none';
        if (ownerCrownBadge) ownerCrownBadge.style.display = 'none';
        if (roleBadge) {
            roleBadge.style.display = 'inline-flex';
            roleBadge.textContent = isRealAdmin ? '👑 ADMIN - Toàn quyền' : '👤 USER - Server của bạn';
            roleBadge.className = isRealAdmin ? 'badge badge-sakura' : 'badge badge-green';
        }
        if (userRoleEl) {
            userRoleEl.textContent = isRealAdmin ? 'Quản trị viên hệ thống' : 'Chỉ quản lý server có quyền';
        }
    }

    if (userNameEl) userNameEl.textContent = u.username || '—';
    if (userAvatarEl && u) {
        const av = u.avatar || `https://cdn.discordapp.com/embed/avatars/0.png`;
        userAvatarEl.src = av;
        userAvatarEl.alt = u.username || 'User';
    }
    if (banner) banner.style.display = effectiveAdmin ? 'none' : 'block';

    
    document.querySelectorAll('[data-admin-only="true"]').forEach(el => {
        el.style.display = effectiveAdmin ? '' : 'none';
    });
    document.querySelectorAll('.admin-only').forEach(el => {
        el.style.display = effectiveAdmin ? '' : 'none';
    });

    
    document.querySelectorAll('.owner-only, [data-owner-only="true"]').forEach(el => {
        el.style.display = (isOwner && !isPreview) ? '' : 'none';
    });

    
    if (!effectiveAdmin) {
        const adminTabs = ['anti', 'add_economy', 'admin_fishing', 'admin_shop', 'admin_marriage', 'admin_farm', 'admin_mining', 'admin_minecraft', 'admin_achievements', 'wordchain', 'giveaways', 'console', 'settings', 'admin_users'];
        if (adminTabs.includes(state.activeTab)) {
            switchTab('guilds');
        }
    }
    if (state.levels && state.levels.length) {
        renderLevelsTable(state.levels);
    }
}
async function doLogout() {
    try {
        await fetch('/api/auth/logout', { method: 'POST', headers: { 'Authorization': `Bearer ${state.token}` } });
    } catch (e) { }
    localStorage.removeItem('sakura_auth_token');
    localStorage.removeItem('sakura_user');
    document.cookie = 'sakura_token=; path=/; max-age=0';
    location.href = '/login';
}


function showToast(message, type = 'info') {
    const container = document.getElementById('toastContainer');
    if (!container) return;
    const toast = document.createElement('div');
    toast.className = 'toast-message';

    let icon = '🌸';
    if (type === 'success') icon = '✅';
    if (type === 'error') icon = '❌';
    if (type === 'warning') icon = '⚠️';

    toast.innerHTML = `<span>${icon}</span><span>${message}</span>`;
    container.appendChild(toast);

    setTimeout(() => {
        toast.style.opacity = '0';
        toast.style.transform = 'translateY(10px)';
        toast.style.transition = 'all 0.3s ease';
        setTimeout(() => toast.remove(), 300);
    }, 4000);
}


async function apiRequest(endpoint, method = 'GET', body = null) {
    let actualMethod = 'GET';
    let actualBody = null;
    let customHeaders = {};

    if (typeof method === 'object' && method !== null) {
        actualMethod = method.method || 'GET';
        actualBody = method.body !== undefined ? method.body : null;
        if (method.headers) customHeaders = method.headers;
    } else {
        actualMethod = method;
        actualBody = body;
    }

    const headers = {
        'Content-Type': 'application/json',
        ...customHeaders
    };
    if (state.token) {
        headers['Authorization'] = `Bearer ${state.token}`;
    }

    const options = { method: actualMethod, headers };
    if (actualBody !== null && actualBody !== undefined) {
        options.body = (typeof actualBody === 'string') ? actualBody : JSON.stringify(actualBody);
    }

    try {
        const response = await fetch(endpoint, options);
        if (response.status === 401) {
            
            if (!window._authRedirecting) {
                window._authRedirecting = true;
                showToast('Phiên hết hạn, chuyển về đăng nhập...', 'warning');
                setTimeout(() => location.href = '/login', 900);
            }
            return { ok: false, error: 'Unauthorized', status: 401 };
        }
        if (response.status === 403) {
            const data = await response.json().catch(() => ({}));
            showToast(data.error || 'Bạn không có quyền thực hiện thao tác này', 'error');
            return { ok: false, error: data.error || 'Forbidden', status: 403 };
        }
        
        let data;
        try {
            data = await response.json();
        } catch (err) {
            const text = await response.text().catch(()=> '');
            console.warn(`Non-JSON response ${endpoint} [${response.status}]:`, text.slice(0,500));
            
            const m = text.match(/<title[^>]*>([^<]+)<\/title>/i);
            const hint = m ? m[1].trim() : text.trim().slice(0,120);
            
            return { ok: false, error: hint || err.message || `Lỗi ${response.status}`, status: response.status };
        }
        return data;
    } catch (e) {
        console.error(`API Error [${endpoint}]:`, e);
        return { ok: false, error: e.message };
    }
}


function toggleMobileMenu(force) {
    const sb = document.querySelector('.sidebar');
    const ov = document.getElementById('mobileOverlay');
    if (!sb) return;
    const open = force !== undefined ? force : !sb.classList.contains('mobile-open');
    sb.classList.toggle('mobile-open', open);
    if (ov) ov.classList.toggle('active', open);
    document.body.style.overflow = open ? 'hidden' : '';
}

function setupNavigation() {
    const navItems = document.querySelectorAll('.nav-item');
    navItems.forEach(item => {
        item.addEventListener('click', (e) => {
            const tabName = item.getAttribute('data-tab');
            if (!tabName) return;
            e.preventDefault();
            switchTab(tabName);
            
            if (window.innerWidth <= 992) toggleMobileMenu(false);
        });
    });
}

function switchTab(tabName) {
    if (tabName === 'levels' || tabName === 'fishing_lb' || tabName === 'achievements_lb') {
        switchTab('leaderboards');
        const subMap = { levels: 'levels', fishing_lb: 'fishing', achievements_lb: 'achievements' };
        switchLeaderboardSubTab(subMap[tabName] || 'waifu');
        return;
    }
    state.activeTab = tabName;

    
    document.querySelectorAll('.nav-item').forEach(item => {
        if (item.getAttribute('data-tab') === tabName) {
            item.classList.add('active');
        } else {
            item.classList.remove('active');
        }
    });

    
    document.querySelectorAll('.tab-content').forEach(tab => {
        if (tab.id === `tab-${tabName}`) {
            tab.classList.add('active');
        } else {
            tab.classList.remove('active');
        }
    });

    
    const titleMap = {
        dashboard: '📊 Tổng Quan Hệ Thống',
        guilds: '🏰 Quản Lý Máy Chủ Discord',
        commands: '⌨️ Danh Sách Lệnh Sakura Bot',
        anti: '🛡️ Bảo Mật & Hệ Thống Anti',
        add_economy: '💵 Cấp Phát Kinh Tế Cho Người Dùng',
                leaderboards: '🏆 Bảng Xếp Hạng Sakura',
        admin_gacha: '🌸 Quản Trị Hệ Thống Waifu Gacha',
        levels: '🏆 Bảng Xếp Hạng & Kinh Tế Server',
        fishing_lb: '🎣 Bảng Xếp Hạng Cần Thủ Câu Cá',
        admin_fishing: '👑 Quản Trị Hệ Thống Câu Cá',
        admin_farm: '🚜 Quản Trị Hệ Thống Nông Trại',
        admin_mining: '⛏️ Quản Trị Hệ Thống Khoáng Sản',
        plugin_guide: '🔌 Lệnh Plugin Sakura & Hướng Dẫn Kết Nối',
        wordchain: '🔤 Quản Lý Minigame Nối Chữ',
        admin_minecraft: '⛏️ Quản Trị Hệ Thống Minecraft Server',
        giveaways: '🎉 Quản Lý Giveaway Máy Chủ',
        ai_tts: '🤖 Cấu Hình AI & Voice TTS',
        console: '📜 Live Console & Nhật Ký',
        settings: '⚙️ Cài Đặt Hệ Thống',
        admin_users: '👥 Quản Trị Danh Sách Admin Web (Phân Quyền)',
        admin_achievements: '🏆 Quản Trị Hệ Thống Thành Tựu',
        achievements_lb: '🏆 Bảng Xếp Hạng Thợ Săn Thành Tựu Sakura',
        admin_shop: '🛒 Quản Trị Hệ Thống Cửa Hàng & Sáng Tạo Vật Phẩm',
        admin_marriage: '💍 Quản Trị Hệ Thống Hôn Lễ & Cặp Đôi'
    };
    const titleEl = document.getElementById('pageTitle');
    if (titleEl) titleEl.innerText = titleMap[tabName] || 'Sakura Bot Dashboard';

    
    if (tabName === 'guilds') loadGuilds();
    if (tabName === 'commands') loadBotCommands();
    if (tabName === 'anti') loadAntiSettings();
    if (tabName === 'add_economy') initAddEconomyForm();
    if (tabName === 'leaderboards') initLeaderboardsTab();
    if (tabName === 'admin_gacha') initAdminGachaTab();
    if (tabName === 'levels') loadLevels();
    if (tabName === 'fishing_lb') loadFishingLeaderboard();
    if (tabName === 'admin_fishing') initAdminFishingTab();
    if (tabName === 'admin_farm') initAdminFarmTab();
    if (tabName === 'admin_mining') initAdminMiningTab();
    if (tabName === 'plugin_guide') loadPluginCommands();
    if (tabName === 'wordchain') loadWordChainManagement();
    if (tabName === 'admin_minecraft') initAdminMinecraftTab();
    if (tabName === 'giveaways') initGiveawaysTab();
    if (tabName === 'admin_users') loadAdminUsersList();
    if (tabName === 'admin_achievements') afLoadAchievementsCatalog();
    if (tabName === 'achievements_lb') loadAchievementsLeaderboard();
    if (tabName === 'admin_shop') loadAdminShopItems();
    if (tabName === 'admin_marriage') loadAdminMarriages();
    if (tabName === 'settings') loadSystemSettings();
}


async function fetchStatus() {
    const res = await apiRequest('/api/status');
    if (!res.ok) return;

    state.botStatus = res.bot;
    const sys = res.system;

    
    if (res.bot && res.bot.avatar) {
        document.querySelectorAll('.brand-logo, .bot-avatar-animated, .brand-logo-img').forEach(img => {
            if (img.tagName === 'IMG' && img.src !== res.bot.avatar) {
                img.src = res.bot.avatar;
                img.onerror = function() {
                    this.onerror = null;
                    this.src = '/images/avatar-bot.jpg';
                };
            }
        });
    }

    
    const presenceDot = document.getElementById('presenceDot');
    const botStatusText = document.getElementById('botStatusText');
    const botUserTag = document.getElementById('botUserTag');
    const headerPing = document.getElementById('headerPing');
    const headerUptime = document.getElementById('headerUptime');

    const curLang = (window.getSakuraLanguage ? window.getSakuraLanguage() : 'vi');
    const onlineText = curLang === 'en' ? 'Online' : (curLang === 'ja' ? 'オンライン' : 'Trực tuyến');
    const minUnit = curLang === 'en' ? 'min' : (curLang === 'ja' ? '分' : 'phút');
    if (res.bot.online) {
        presenceDot.className = 'presence-dot online';
        botStatusText.innerText = onlineText;
        botUserTag.innerText = res.bot.username;
    } else {
        presenceDot.className = 'presence-dot';
        botStatusText.innerText = 'Offline';
        botUserTag.innerText = 'Sakura Bot';
    }

    const mobilePing = document.getElementById('mobilePing');
    const mobileUptime = document.getElementById('mobileUptime');
    if (headerPing) headerPing.innerText = `${res.bot.latency} ms`;
    if (mobilePing) mobilePing.innerText = `${res.bot.latency} ms`;
    if (headerUptime) {
        const uptimeMin = Math.floor(res.bot.uptime / 60);
        headerUptime.innerText = `${uptimeMin} `;
        if (mobileUptime) mobileUptime.innerText = `${uptimeMin} `;
    }

    
    const statGuilds = document.getElementById('statGuilds');
    const statUsers = document.getElementById('statUsers');
    const statChannels = document.getElementById('statChannels');
    const statCogs = document.getElementById('statCogs');

    if (statGuilds) statGuilds.innerText = res.bot.guilds_count;
    if (statUsers) statUsers.innerText = res.bot.users_count.toLocaleString();
    if (statChannels) statChannels.innerText = res.bot.channels_count;
    if (statCogs) statCogs.innerText = res.bot.cogs_count;

    
    state.cpuHistory.push(sys.cpu_percent);
    state.cpuHistory.shift();
    state.ramHistory.push(sys.ram_percent);
    state.ramHistory.shift();

    if (state.chartInstance) {
        state.chartInstance.data.datasets[0].data = state.cpuHistory;
        state.chartInstance.data.datasets[1].data = state.ramHistory;
        state.chartInstance.update('none');
    }

    
    if (res.admin_details) {
        renderAdminDiagnostics(res.admin_details);
    }
}


function renderAdminDiagnostics(data) {
    if (!data) return;
    state.adminDiagnostics = data;

    
    const l = data.lavalink;
    if (l) {
        const badge = document.getElementById('lavalinkStatusBadge');
        const stateText = document.getElementById('lavalinkStateText');
        const pingText = document.getElementById('lavalinkPingText');
        const verText = document.getElementById('lavalinkVersionText');
        const playersText = document.getElementById('lavalinkPlayersText');
        const hostDisp = document.getElementById('lavalinkHostDisplay');
        const errorDetail = document.getElementById('lavalinkErrorDetail');
        const lastCheck = document.getElementById('lavalinkLastCheck');

        if (hostDisp) hostDisp.innerText = `${l.host}:${l.port}`;

        if (l.state_label === 'ổn' || l.status === 'on') {
            if (badge) {
                badge.innerText = '🟢 Ổn định (ổn)';
                badge.style.background = 'rgba(80, 250, 123, 0.15)';
                badge.style.color = '#50fa7b';
                badge.style.border = '1px solid rgba(80, 250, 123, 0.35)';
            }
            if (stateText) {
                stateText.innerHTML = '<span style="color:#50fa7b;font-weight:700">Ổn định (Online)</span>';
            }
        } else if (l.state_label === 'tắt' || l.status === 'off') {
            if (badge) {
                badge.innerText = '⚪ Đã tắt (tắt)';
                badge.style.background = 'rgba(255, 255, 255, 0.08)';
                badge.style.color = '#a1a1aa';
                badge.style.border = '1px solid rgba(255, 255, 255, 0.2)';
            }
            if (stateText) {
                stateText.innerHTML = '<span style="color:#a1a1aa;font-weight:700">Đã tắt (Offline)</span>';
            }
        } else {
            
            if (badge) {
                badge.innerText = '🔴 Gặp sự cố (sự cố)';
                badge.style.background = 'rgba(255, 85, 85, 0.15)';
                badge.style.color = '#ff5555';
                badge.style.border = '1px solid rgba(255, 85, 85, 0.35)';
            }
            if (stateText) {
                stateText.innerHTML = '<span style="color:#ff5555;font-weight:700">Gặp sự cố kết nối</span>';
            }
        }

        if (pingText) pingText.innerText = (l.latency_ms > 0 ? `${l.latency_ms} ms` : '—');
        if (verText) verText.innerText = l.version || 'v4';
        if (playersText) playersText.innerText = `${l.active_players || 0} phòng phát`;
        if (errorDetail) errorDetail.innerText = l.detail || (l.status === 'on' ? 'Kết nối bình thường' : 'Chưa kết nối');
        if (lastCheck) {
            const dt = new Date();
            lastCheck.innerText = `Cập nhật: ${dt.toLocaleTimeString()}`;
        }
    }

    
    const apis = data.apis || [];
    const apisList = document.getElementById('apisStatusList');
    const summaryBadge = document.getElementById('apisHealthSummaryBadge');
    const apisLastCheck = document.getElementById('apisLastCheck');

    if (apisList && apis.length > 0) {
        let healthyCount = 0;
        apisList.innerHTML = apis.map(api => {
            const isHealthy = api.status === 'on';
            if (isHealthy) healthyCount++;
            const isError = api.status === 'error';
            
            let statusPill = '';
            if (isHealthy) {
                statusPill = `<span class="badge" style="background:rgba(80,250,123,0.12);color:#50fa7b;border:1px solid rgba(80,250,123,0.3)">🟢 ${api.status_label || 'Ổn định'}</span>`;
            } else if (isError) {
                statusPill = `<span class="badge" style="background:rgba(255,85,85,0.15);color:#ff5555;border:1px solid rgba(255,85,85,0.3)">🔴 ${api.status_label || 'Sự cố'}</span>`;
            } else {
                statusPill = `<span class="badge" style="background:rgba(255,255,255,0.08);color:#a1a1aa;border:1px solid rgba(255,255,255,0.2)">⚪ ${api.status_label || 'Tắt'}</span>`;
            }

            const latencyDisp = api.latency_ms > 0 ? `<span style="font-size:.75rem;color:var(--accent-cyan);font-weight:600">${api.latency_ms}ms</span>` : '';

            return `
                <div style="display:flex;align-items:center;justify-content:space-between;padding:8px 12px;background:rgba(255,255,255,0.02);border:1px solid var(--border-subtle);border-radius:8px;gap:10px">
                    <div style="display:flex;align-items:center;gap:10px;min-width:0">
                        <span style="font-size:1.15rem;flex-shrink:0">${api.icon || '🔗'}</span>
                        <div style="min-width:0">
                            <div style="font-size:.85rem;font-weight:600;color:var(--text-main);white-space:nowrap;overflow:hidden;text-overflow:ellipsis">
                                ${api.name}
                            </div>
                            <div style="font-size:.72rem;color:var(--text-muted);white-space:nowrap;overflow:hidden;text-overflow:ellipsis">
                                ${api.category} • ${api.note || ''}
                            </div>
                        </div>
                    </div>
                    <div style="display:flex;align-items:center;gap:8px;flex-shrink:0">
                        ${latencyDisp}
                        ${statusPill}
                    </div>
                </div>
            `;
        }).join('');

        if (summaryBadge) {
            summaryBadge.innerText = `${healthyCount}/${apis.length} Hoạt động`;
            summaryBadge.className = healthyCount === apis.length ? 'badge badge-green' : (healthyCount > 0 ? 'badge badge-warning' : 'badge badge-danger');
        }
        if (apisLastCheck) {
            const dt = new Date();
            apisLastCheck.innerText = `Cập nhật: ${dt.toLocaleTimeString()}`;
        }
    }

    
    const b = data.bot_details;
    if (b) {
        const setVal = (id, val) => {
            const el = document.getElementById(id);
            if (el && val !== undefined && val !== null) el.innerText = val;
        };

        setVal('botDiagPid', `PID: ${b.pid}`);
        setVal('botDiagDiscordVer', `discord.py v${b.discord_version}`);
        setVal('botDiagPythonVer', `Python ${b.python_version}`);
        setVal('botDiagOs', `${b.os_platform} (${b.architecture})`);
        setVal('botDiagMem', `${b.memory_rss_mb} MB`);
        setVal('botDiagCpu', `CPU bot: ${b.cpu_percent}%`);
        setVal('botDiagUptime', b.uptime_str);
        setVal('botDiagStarted', `Khởi động: ${b.started_at}`);
        setVal('botDiagDbStatus', `${b.db_name} (${b.db_status})`);
        setVal('botDiagDbSize', `Dung lượng: ${b.db_size}`);
        setVal('botDiagVoice', `${b.voice_count} kênh voice`);
        setVal('botDiagShards', `Shards: ${b.shards_count} | Ping: ${b.latency_ms}ms`);
        setVal('botDiagCmds', `${b.commands_count} lệnh đăng ký`);
        setVal('botDiagCogs', `${b.cogs_count} cogs / modules`);
        setVal('botDiagCogsSummaryCount', b.cogs_count);

        const pillsContainer = document.getElementById('botDiagCogsPills');
        if (pillsContainer && b.cogs_list && b.cogs_list.length > 0) {
            pillsContainer.innerHTML = b.cogs_list.map(cog => `
                <span class="badge" style="background:rgba(189,147,249,0.12);color:var(--accent-purple);border:1px solid rgba(189,147,249,0.25);font-size:.75rem;padding:4px 8px;border-radius:6px">
                    🧩 ${cog}
                </span>
            `).join('');
        }
    }
}

async function refreshAdminDiagnostics(isManual = false) {
    const btn = document.getElementById('btnRefreshDiagnostics');
    const icon = document.getElementById('iconRefreshDiag');
    if (btn) btn.disabled = true;
    if (icon) icon.classList.add('rotating');

    try {
        const res = await apiRequest('/api/admin/system-health?refresh=1');
        if (res.ok && res.diagnostics) {
            renderAdminDiagnostics(res.diagnostics);
            if (isManual) showToast('Đã làm mới dữ liệu chẩn đoán hệ thống!', 'success');
        } else {
            if (isManual) showToast(res.error || 'Không thể làm mới chẩn đoán', 'error');
        }
    } catch (e) {
        console.error('refreshAdminDiagnostics error:', e);
        if (isManual) showToast('Lỗi kết nối kiểm tra hệ thống', 'error');
    } finally {
        if (btn) btn.disabled = false;
        if (icon) icon.classList.remove('rotating');
    }
}

function initPerformanceChart() {
    const ctx = document.getElementById('performanceChart');
    if (!ctx) return;

    state.chartInstance = new Chart(ctx, {
        type: 'line',
        data: {
            labels: ['', '', '', '', '', '', '', '', '', 'Hiện tại'],
            datasets: [
                {
                    label: 'CPU Usage (%)',
                    data: state.cpuHistory,
                    borderColor: '#ff79c6',
                    backgroundColor: 'rgba(255, 121, 198, 0.15)',
                    borderWidth: 2,
                    tension: 0.4,
                    fill: true
                },
                {
                    label: 'RAM Usage (%)',
                    data: state.ramHistory,
                    borderColor: '#8be9fd',
                    backgroundColor: 'rgba(139, 233, 253, 0.1)',
                    borderWidth: 2,
                    tension: 0.4,
                    fill: true
                }
            ]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: { labels: { color: '#94a3b8', font: { family: 'Outfit' } } }
            },
            scales: {
                y: {
                    min: 0,
                    max: 100,
                    grid: { color: 'rgba(255, 255, 255, 0.05)' },
                    ticks: { color: '#64748b' }
                },
                x: {
                    grid: { display: false },
                    ticks: { color: '#64748b' }
                }
            }
        }
    });
}


async function loadGuilds() {
    const container = document.getElementById('guildsList');
    if (!container) return;
    container.innerHTML = '<div style="color: var(--text-muted);">Đang tải danh sách server...</div>';

    const res = await apiRequest('/api/guilds');
    if (!res.ok || !res.guilds) {
        container.innerHTML = `<div style="color: var(--accent-red);">Không thể tải danh sách server (${res.error || 'Lỗi'})</div>`;
        return;
    }

    state.guilds = res.guilds;
    const emptyEl = document.getElementById('guildsEmpty');
    if (res.guilds.length === 0) {
        container.innerHTML = '';
        if (emptyEl) emptyEl.style.display = 'block';
        return;
    }
    if (emptyEl) emptyEl.style.display = 'none';

    let html = '';
    const isAdmin = !!(res.is_admin || state.isAdmin || (state.currentUser && (state.currentUser.is_admin || state.currentUser.role === 'admin' || state.currentUser.username === 'admin')) || (state.user && (state.user.is_admin || state.user.role === 'admin')));
    res.guilds.forEach(g => {
        const safeName = (g.name || '').replace(/'/g, "\\'");
        const adminButtons = isAdmin ? `
            <button class="btn btn-secondary btn-sm" onclick="createGuildInvite('${g.id}', this)" title="Tạo link tham gia server">🔗 Tham gia</button>
            <button class="btn btn-danger btn-sm" style="background: rgba(255,85,85,0.15); color: #ff5555; border: 1px solid rgba(255,85,85,0.3);" onclick="leaveGuild('${g.id}', '${safeName}')" title="Buộc bot rời server này">🚪 Rời server</button>
        ` : '';

        // MEE6-style card with banner + overlapping icon
        html += `
        <div class="guild-card mee" data-name="${g.name.toLowerCase()}">
            <div class="guild-banner"></div>
            <div class="guild-card-body">
                <img src="${g.icon}" class="guild-icon mee" alt="${g.name}">
                <div class="guild-title-row">
                    <h4 title="${g.name}">${g.name}</h4>
                    <span class="badge badge-green">${g.language.toUpperCase()}</span>
                </div>
                <div class="guild-meta">
                    <span>👥 ${g.member_count.toLocaleString()} thành viên</span>
                    <span>•</span>
                    <span>🏷️ ${g.prefix}</span>
                </div>
                <div class="guild-badges">
                    <span class="badge">ID: ${g.id.slice(0, 6)}…</span>
                    <span class="badge badge-sakura">${g.channel_count || 0} kênh</span>
                </div>
                <div class="guild-actions">
                    <a href="/dashboard/${g.id}" class="btn btn-primary btn-sm" style="text-decoration:none" onclick="openGuildDrawer('${g.id}'); history.pushState(null,'','/dashboard/${g.id}'); return false;">⚙️ Cấu hình</a>
                    ${adminButtons}
                    <button class="btn btn-secondary btn-sm" onclick="openSendMessageModal('${g.id}', '${safeName}')">📢 Gửi</button>
                </div>
            </div>
        </div>
        `;
    });
    container.innerHTML = html;
}

async function leaveGuild(guildId, guildName) {
    if (!confirm(`⚠️ Bạn có chắc chắn muốn cho Sakura Bot rời khỏi server "${guildName}" (ID: ${guildId}) không?`)) {
        return;
    }
    const res = await apiRequest(`/api/guilds/${guildId}/leave`, 'POST');
    if (res.ok) {
        showToast(res.message || `Bot đã rời khỏi ${guildName}`, 'success');
        loadGuilds();
    } else {
        showToast(res.error || 'Lỗi khi yêu cầu bot rời server', 'error');
    }
}

async function createGuildInvite(guildId, button) {
    const originalText = button.textContent;
    button.disabled = true;
    button.textContent = '⏳ Đang tạo...';
    const res = await apiRequest(`/api/guilds/${guildId}/invite`, 'POST');
    button.disabled = false;
    button.textContent = originalText;
    if (res.ok && res.url) {
        window.open(res.url, '_blank', 'noopener');
        showToast(`Đã tạo lời mời từ #${res.channel}`, 'success');
    } else {
        showToast(res.error || 'Không thể tạo lời mời', 'warning');
    }
}

async function openGuildModal(guildId) {
    const res = await apiRequest(`/api/guilds/${guildId}`);
    if (!res.ok) {
        showToast('Không thể tải thông tin server', 'error');
        return;
    }

    const g = res.guild;
    document.getElementById('guildModalTitle').innerText = `⚙️ Cài đặt Server: ${g.name}`;
    document.getElementById('guildModalId').value = g.id;
    document.getElementById('guildModalPrefix').value = g.prefix;
    document.getElementById('guildModalLang').value = g.language;

    // Render channels dropdown
    const chSelect = document.getElementById('msgChannelSelect');
    if (chSelect) {
        const isCategory = c => String(c.type) === '4' || String(c.type).toLowerCase().includes('category');
        const isVoice = c => {
            const type = String(c.type).toLowerCase();
            return type === '2' || type === '13' || type.includes('voice') || type.includes('stage');
        };
        const sendableChannels = g.channels.filter(c => !isCategory(c));
        chSelect.innerHTML = buildGroupedChannelHTML(sendableChannels, '<option>Không có kênh gửi tin</option>');
    }

    document.getElementById('guildSettingsModal').classList.add('active');
}

// === New MEE6-style Drawer handlers ===
function filterGuildCards() {
    const q = (document.getElementById('guildSearch')?.value || '').toLowerCase();
    document.querySelectorAll('.guild-card.mee').forEach(c => {
        const name = c.getAttribute('data-name') || '';
        c.style.display = name.includes(q) ? '' : 'none';
    });
}
function doInvite() {
    window.open('/bot', '_blank');
}
async function openGuildDrawer(guildId, pushUrl = true) {
    const res = await apiRequest(`/api/guilds/${guildId}`);
    if (!res.ok) {
        if (res.status === 403) showToast('Bạn không có quyền quản lý server này', 'error');
        else showToast('Không thể tải server', 'error');
        // nếu là deep link mà bị 403 thì quay về /dashboard
        if (window.location.pathname.startsWith('/dashboard/')) history.replaceState(null, '', '/dashboard');
        return;
    }
    const g = res.guild;
    _amGuildId = String(g.id);
    document.getElementById('drawerGuildId').value = g.id;
    document.getElementById('drawerGuildName').innerText = g.name;
    document.getElementById('drawerGuildMeta').innerText = `ID ${g.id} • ${g.member_count} thành viên • ${g.channels.length} kênh`;
    document.getElementById('drawerGuildIcon').src = g.icon || 'https://cdn.discordapp.com/embed/avatars/0.png';
    document.getElementById('drawerPrefix').value = g.prefix;
    document.getElementById('drawerLang').value = g.language;
    document.getElementById('drawerMemberCount').innerText = `${g.member_count} mems`;
    const chPreview = document.getElementById('drawerChannelsPreview');
    if (chPreview) chPreview.innerText = `${g.channels.length} kênh • ${g.roles.length} roles`;
    // keep full channel list globally for lookups (text + voice)
    _amChannels = g.channels.slice();
    // Phân loại kênh: text-like = tất cả ngoại trừ voice/category • voice = voice/stage
    const isVoiceType = (t)=>{ const s=String(t).toLowerCase(); return s==='2' || s==='13' || s.includes('voice') || s.includes('stage'); };
    const isCategoryType = (t)=>{ const s=String(t).toLowerCase(); return s==='4' || s.includes('category'); };
    let textChannels = g.channels.filter(c => !isVoiceType(c.type) && !isCategoryType(c.type));
    let voiceChannels = g.channels.filter(c => isVoiceType(c.type));
    // Fallback: nếu filter quá chặt khiến rỗng mà server có kênh → hiện tất cả (trừ category) để không bị thiếu
    if(!textChannels.length && g.channels.length){
        textChannels = g.channels.filter(c => !isCategoryType(c.type));
    }
    if(!voiceChannels.length){
        // thử tìm theo tên nếu type lạ: tên chứa 🔊 hoặc category voice?
        voiceChannels = g.channels.filter(c => /voice|thoại|vc/i.test(c.name));
    }
    const textGrouped = buildGroupedChannelHTML(textChannels, '');
    const messageGrouped = buildGroupedChannelHTML(textChannels.concat(voiceChannels), '');
    const voiceGrouped = buildGroupedChannelHTML(voiceChannels, '');
    // Audit Logs group also uses text channels (same as welcome etc) – populate 5 audit selects with same textGrouped
    const auditIds=['auditMessage','auditMember','auditJoin','auditVoice','auditServer'];
    auditIds.forEach(id=>{
        const el=document.getElementById(id);
        if(el){
            // keep current value until loadAudit overwrites
            const cur=el.value;
            el.innerHTML='<option value="">— Tắt —</option>' + (textGrouped || '<option>Không có kênh text</option>');
            if(cur) el.value=cur;
        }
    });
    console.log('[Sakura] Channels:', g.channels.length, 'text:', textChannels.length, 'voice:', voiceChannels.length, g.channels.slice(0,3));
    ['welcomeChannel','goodbyeChannel','logChannel', 'announceChannel', 'modChannelId','leverAnnounceChannel',
     'fishFishingChannel', 'fishCodeChannel', 'streakChannel', 'giveawayChannel', 'ruleChannel'].forEach(id => {
        const el = document.getElementById(id); if (!el) return;
        let empty = '<option value="">-- Trống = gửi tại kênh chat --</option>';
        if (id === 'welcomeChannel' || id === 'goodbyeChannel') empty = '<option value="">— Không đặt —</option>';
        else if (id === 'fishFishingChannel') empty = '<option value="">— Mọi kênh / Chưa giới hạn —</option>';
        else if (id === 'fishCodeChannel') empty = '<option value="">— Không đặt kênh riêng —</option>';
        else if (id === 'streakChannel') empty = '<option value="">— Tắt hệ thống Streak —</option>';
        else if (id === 'giveawayChannel') empty = '<option value="">-- Chọn kênh tổ chức --</option>';
        else if (id === 'ruleChannel') empty = '<option value="">— Chọn kênh nội quy —</option>';
        el.innerHTML = empty + (textGrouped || '<option>Không có kênh text</option>');
    });
    // Populate role selectors across new panels
    const rolesGrouped = (g.roles || []).map(r => `<option value="${r.id}">${escapeHtml(r.name)}</option>`).join('');
    const fillRoleSelect = (id, emptyText) => {
        const el = document.getElementById(id);
        if (!el) return;
        const cur = el.value;
        el.innerHTML = `<option value="">${emptyText}</option>` + rolesGrouped;
        if (cur) el.value = cur;
    };
    fillRoleSelect('newLevelRewardRole', '-- Chọn vai trò nhận --');
    fillRoleSelect('fishCodeRole', '— Không ping role —');
    fillRoleSelect('autoRoleUser', '— Không tự động gán —');
    fillRoleSelect('autoRoleBot', '— Không tự động gán —');
    fillRoleSelect('ruleRole', '— Chọn Role thành viên —');

    // Nạp select cho Hoyo Code
    ['genshin', 'hsr', 'zzz', 'nte', 'endfield'].forEach(game => {
        const chEl = document.getElementById(`hoyoChannel_${game}`);
        if (chEl) {
            const curVal = chEl.value;
            chEl.innerHTML = '<option value="">-- Chưa cài đặt --</option>' + (textGrouped || '');
            if (curVal) chEl.value = curVal;
        }
        fillRoleSelect(`hoyoRole_${game}`, '-- Không ping role --');
    });

    // Nạp select cho Wordchain
    const wcSel = document.getElementById('wordchainChannel');
    if (wcSel) {
        const curWc = wcSel.value;
        wcSel.innerHTML = '<option value="">— Chưa chọn —</option>' + (textGrouped || '');
        if (curWc) wcSel.value = curWc;
    }

    // Nạp select cho Minecraft Per-Server connection
    const mcChatSel = document.getElementById('gmcChatChannel');
    if (mcChatSel) {
        const curMcChat = mcChatSel.value;
        mcChatSel.innerHTML = '<option value="">— Chưa chọn kênh chat —</option>' + (textGrouped || '');
        if (curMcChat) mcChatSel.value = curMcChat;
    }
    const mcLogSel = document.getElementById('gmcLogChannel');
    if (mcLogSel) {
        const curMcLog = mcLogSel.value;
        mcLogSel.innerHTML = '<option value="">— Chưa chọn kênh log —</option>' + (textGrouped || '');
        if (curMcLog) mcLogSel.value = curMcLog;
    }

    const messageSelect = document.getElementById('msgChannelSelect');
    if (messageSelect) {
        messageSelect.innerHTML = '<option value="">-- Chọn kênh nhận tin --</option>' + (messageGrouped || '<option>Không có kênh gửi tin</option>');
    }
    // TempVoice voice selector
    const tvSel=document.getElementById('tempVoiceChannel');
    if(tvSel){
        tvSel.innerHTML = '<option value="">— Tắt TempVoice —</option>' + (voiceGrouped || '<option value="">Không có kênh thoại</option>');
    }
    // Confession text selectors
    ['cfsChannel','cfsLogChannel','cfsPostChannel'].forEach(id=>{
        const el=document.getElementById(id); if(!el) return;
        const isPost=id==='cfsPostChannel';
        const empty=isPost? '<option value="">-- Theo kênh Confession --</option>' : '<option value="">-- Chọn kênh --</option>';
        el.innerHTML = empty + (textGrouped || '<option>Không có kênh text</option>');
    });
    document.getElementById('guildDrawer').classList.add('active');
    switchDrawerPanel('general');
    loadServerConfig(g.id);
    loadBotProfile(g.id);
    loadWelcome(g.id);
    loadTempVoice(g.id);
    loadConfession(g.id);
    loadAuditLogs(g.id);
    loadBlacklist(g.id);
    loadLeverConfig(g.id);
    loadLevelRoles(g.id);
    loadFishingConfig(g.id);
    loadCustomKeys(g.id);
    loadBackups(g.id);
    loadAutoRole(g.id);
    loadStreakConfig(g.id);
    loadGiveawayConfig(g.id);
    loadRuleConfig(g.id);
    loadModCommands(g.id);
    loadModMembers(g.id);
    loadAutomod(g.id);
    loadPanelConfig(g.id);
    loadMinigameConfig(g.id);
    loadGuildMcConnection(g.id);
    onModActionChange();
    if (pushUrl && window.location.pathname !== `/dashboard/${guildId}`) {
        history.pushState({ guildId }, '', `/dashboard/${guildId}`);
    }
}
function closeGuildDrawer() {
    document.getElementById('guildDrawer').classList.remove('active');
    // quay về /dashboard nếu đang ở deep link
    if (window.location.pathname.match(/^\/dashboard\/\d+$/)) {
        history.pushState(null, '', '/dashboard');
    }
}
function handleDashboardDeepLink() {
    const m = window.location.pathname.match(/^\/dashboard\/(\d+)$/);
    if (m) {
        const gid = m[1];
        // đảm bảo đã load guilds xong mới mở
        // nếu chưa có guild data thì đợi 500ms thử lại
        if (state.guilds.length === 0) {
            setTimeout(() => handleDashboardDeepLink(), 600);
        } else {
            switchTab('guilds');
            openGuildDrawer(gid, false);
        }
    }
}
function switchDrawerPanel(name) {
    document.querySelectorAll('.drawer-panel').forEach(p => p.style.display = p.id === 'panel-' + name ? 'block' : 'none');
    document.querySelectorAll('.drawer-nav-btn').forEach(b => b.classList.toggle('active', b.dataset.panel === name));
    const sel=document.getElementById('drawerMobileSelect'); if(sel && sel.value!==name) sel.value=name;
    // cuộn lên đầu main khi đổi tab trên đt
    const main=document.querySelector('.drawer-main'); if(main && window.innerWidth<=768) main.scrollTop=0;
    const currentGuildId = document.getElementById('drawerGuildId')?.value || _amGuildId;
    if(name==='moderation' && currentGuildId) { // refresh automod khi mở tab
        // nếu chưa có config thì load, nếu có thì render lại kênh
        if(!_amConfig) loadAutomod(currentGuildId);
    }
    if(name==='tempvoice' && currentGuildId){
        loadTempVoice(currentGuildId);
    }
    if(name==='confession' && currentGuildId){
        loadConfession(currentGuildId);
    }
    if(name==='logging' && currentGuildId){
        loadAuditLogs(currentGuildId);
    }
    if(name==='blacklist' && currentGuildId){
        loadBlacklist(currentGuildId);
    }
    if(name==='role-ticket' && currentGuildId){
        loadPanelConfig(currentGuildId);
    }
    if(name==='minigame' && currentGuildId){
        loadMinigameConfig(currentGuildId);
    }
    if(name==='general' && currentGuildId){
        loadBotProfile(currentGuildId);
    }
    if(name==='level' && currentGuildId){
        loadLevelRoles(currentGuildId);
    }
    if(name==='fish' && currentGuildId){
        loadFishingConfig(currentGuildId);
    }
    if(name==='custom-keys' && currentGuildId){
        loadCustomKeys(currentGuildId);
    }
    if(name==='backups' && currentGuildId){
        loadBackups(currentGuildId);
    }
    if(name==='autorole' && currentGuildId){
        loadAutoRole(currentGuildId);
    }
    if(name==='streak' && currentGuildId){
        loadStreakConfig(currentGuildId);
    }
    if(name==='giveaway' && currentGuildId){
        loadGiveawayConfig(currentGuildId);
    }
    if(name==='rule' && currentGuildId){
        loadRuleConfig(currentGuildId);
    }
    if(name==='reaction-role' && currentGuildId){
        loadReactionRolesList(currentGuildId);
    }
    if(name==='hoyo' && currentGuildId){
        loadHoyoConfig(currentGuildId);
    }
    if(name==='minecraft' && currentGuildId){
        loadGuildMcConnection(currentGuildId);
    }
}
function toggleSwitch(el) { el.classList.toggle('on'); }

async function loadMinigameConfig(guildId) {
    const res = await apiRequest(`/api/guilds/${guildId}/minigame-config`);
    if (!res.ok) return;
    const cfg = res.config || {};
    const guildRes = await apiRequest(`/api/guilds/${guildId}`);
    if (!guildRes.ok || !guildRes.guild) return;
    const guild = guildRes.guild;
    const textChannels = (guild.channels || []).filter(c => String(c.type) !== '2' && String(c.type) !== '4' && String(c.type) !== '13');
    const fillChannel = (id, val) => {
        const el = document.getElementById(id);
        if (!el) return;
        el.innerHTML = `<option value="">— Chưa chọn —</option>${textChannels.map(c => `<option value="${c.id}">#${c.name}</option>`).join('')}`;
        if (val) el.value = String(val);
    };
    fillChannel('wordchainChannel', cfg.wordchain_channel_id);
    fillChannel('trieuphuChannel', cfg.trieuphu_channel_id);
    fillChannel('xoChannel', cfg.xo_channel_id);
    fillChannel('chessChannel', cfg.chess_channel_id);

    const tarotMode = document.getElementById('tarotMode');
    const zodiacMode = document.getElementById('zodiacMode');
    if (tarotMode) tarotMode.value = (cfg.tarot_enabled === false || cfg.tarot_enabled === 'false') ? 'off' : 'on';
    if (zodiacMode) zodiacMode.value = (cfg.zodiac_enabled === false || cfg.zodiac_enabled === 'false') ? 'off' : 'on';
}

async function saveMinigameConfig() {
    const guildId = document.getElementById('drawerGuildId')?.value;
    if (!guildId) return showToast('Thiếu server để lưu', 'warning');
    const payload = {
        wordchain_channel_id: document.getElementById('wordchainChannel')?.value || null,
        trieuphu_channel_id: document.getElementById('trieuphuChannel')?.value || null,
        xo_channel_id: document.getElementById('xoChannel')?.value || null,
        chess_channel_id: document.getElementById('chessChannel')?.value || null,
        tarot_enabled: document.getElementById('tarotMode')?.value === 'on',
        zodiac_enabled: document.getElementById('zodiacMode')?.value === 'on'
    };
    const res = await apiRequest(`/api/guilds/${guildId}/minigame-config`, 'POST', payload);
    if (res.ok) {
        showToast('Đã lưu cấu hình MiniGame', 'success');
        await loadMinigameConfig(guildId);
    } else {
        showToast(res.error || 'Lỗi lưu cấu hình MiniGame', 'error');
    }
}

async function loadPanelConfig(guildId) {
    const res = await apiRequest(`/api/guilds/${guildId}/panel-config`);
    if (!res.ok) return;
    const cfg = res.config || {};
    const guildRes = await apiRequest(`/api/guilds/${guildId}`);
    if (!guildRes.ok || !guildRes.guild) return;
    const guild = guildRes.guild;
    const textChannels = (guild.channels || []).filter(c => String(c.type) !== '2' && String(c.type) !== '4' && String(c.type) !== '13').map(c => `<option value="${c.id}">#${c.name}</option>`).join('');
    const roleOptions = (guild.roles || []).map(r => `<option value="${r.id}">${r.name}</option>`).join('');
    const fillChannel = (id, val) => {
        const el = document.getElementById(id);
        if (!el) return;
        el.innerHTML = `<option value="">— Không đặt —</option>${textChannels}`;
        if (val) el.value = String(val);
    };
    const fillRole = (id, val) => {
        const el = document.getElementById(id);
        if (!el) return;
        el.innerHTML = `<option value="">— Chưa chọn —</option>${roleOptions}`;
        if (val) el.value = String(val);
    };
    fillChannel('rolePanelChannel', cfg.role_panel_channel_id);
    fillChannel('roleApprovalChannel', cfg.role_approval_channel_id);
    fillChannel('ticketPanelChannel', cfg.ticket_panel_channel_id);
    fillChannel('ticketLogChannel', cfg.ticket_log_channel_id);
    fillRole('ticketSupportRole', cfg.ticket_support_role_id);
}

async function savePanelConfig() {
    const guildId = document.getElementById('drawerGuildId')?.value;
    if (!guildId) return showToast('Thiếu server để lưu', 'warning');
    const payload = {
        role_panel_channel_id: document.getElementById('rolePanelChannel')?.value || null,
        role_approval_channel_id: document.getElementById('roleApprovalChannel')?.value || null,
        ticket_panel_channel_id: document.getElementById('ticketPanelChannel')?.value || null,
        ticket_log_channel_id: document.getElementById('ticketLogChannel')?.value || null,
        ticket_support_role_id: document.getElementById('ticketSupportRole')?.value || null
    };
    const res = await apiRequest(`/api/guilds/${guildId}/panel-config`, 'POST', payload);
    if (res.ok) {
        showToast('Đã lưu cấu hình panel Role & Ticket', 'success');
        await loadPanelConfig(guildId);
    } else {
        showToast(res.error || 'Lỗi lưu cấu hình panel', 'error');
    }
}

async function postRolePanel() {
    const guildId = document.getElementById('drawerGuildId')?.value;
    if (!guildId) return showToast('Thiếu server để đăng panel', 'warning');
    const payload = {
        action: 'post_role_panel',
        role_panel_channel_id: document.getElementById('rolePanelChannel')?.value || null,
        role_approval_channel_id: document.getElementById('roleApprovalChannel')?.value || null
    };
    const res = await apiRequest(`/api/guilds/${guildId}/panel-config`, 'POST', payload);
    if (res.ok) {
        showToast('Đã đăng panel Role thành công', 'success');
    } else {
        showToast(res.error || 'Không thể đăng panel Role', 'error');
    }
}

async function postTicketPanel() {
    const guildId = document.getElementById('drawerGuildId')?.value;
    if (!guildId) return showToast('Thiếu server để đăng panel', 'warning');
    const payload = {
        action: 'post_ticket_panel',
        ticket_panel_channel_id: document.getElementById('ticketPanelChannel')?.value || null,
        ticket_log_channel_id: document.getElementById('ticketLogChannel')?.value || null,
        ticket_support_role_id: document.getElementById('ticketSupportRole')?.value || null
    };
    const res = await apiRequest(`/api/guilds/${guildId}/panel-config`, 'POST', payload);
    if (res.ok) {
        showToast('Đã đăng panel Ticket thành công', 'success');
    } else {
        showToast(res.error || 'Không thể đăng panel Ticket', 'error');
    }
}

function updateAdvVisibility(){
    const pairs=[
        ['amAntiInvite','amAdvInviteSettings','block'],
        ['amAntiLink','amAdvLinkSettings','block'],
        ['amAntiMention','amAdvMentionSettings','flex'],
        ['amAntiCaps','amAdvCapsSettings','block'],
        ['amAntiEmoji','amAdvEmojiSettings','flex'],
        ['amAntiDuplicate','amAdvDuplicateSettings','block'],
        ['amAntiZalgo','amAdvZalgoSettings','block'],
    ];
    pairs.forEach(([swId, boxId, disp])=>{
        const sw=document.getElementById(swId);
        const box=document.getElementById(boxId);
        if(!sw || !box) return;
        const on=sw.classList.contains('on');
        box.style.display= on ? disp : 'none';
        // ensure flex panels keep flex when shown
        if(on && disp==='flex') box.style.display='flex';
    });
}
// ========== Auto-Moderation (như hình Reine - pastel pink) ==========
let _amConfig = null;
let _amChannels = [];
let _amGuildId = null;

async function loadAutomod(guildId){
    _amGuildId = guildId;
    const res = await apiRequest(`/api/guilds/${guildId}/automod`);
    if(!res.ok){
        const box=document.getElementById('amWordsList');
        if(box) box.innerHTML=`<div style="color:var(--accent-red);font-size:.85rem">Không tải được automod: ${res.error||'lỗi'}</div>`;
        return;
    }
    _amConfig = res.automod;
    // cache channels for pickers (keep full if already loaded)
    try{
        if(!_amChannels || !_amChannels.length){
            const gRes = await apiRequest(`/api/guilds/${guildId}`);
            if(gRes.ok && gRes.guild){
                _amChannels = (gRes.guild.channels||[]);
            }
        }
    }catch(e){}
    renderAutomod(_amConfig);
    populateAmChannelSelects();
}
function escapeHtmlAttr(s){ return String(s).replace(/&/g,'&amp;').replace(/"/g,'&quot;').replace(/</g,'&lt;'); }

function buildGroupedChannelHTML(channels, emptyLabel){
    if(!channels || !channels.length) return emptyLabel ? `<option>${emptyLabel}</option>` : '';
    const groups={};
    channels.forEach(c=>{
        const cat=(c.category && String(c.category).trim()) || '— Không phân loại —';
        if(!groups[cat]) groups[cat]=[];
        groups[cat].push(c);
    });
    
    const cats=Object.keys(groups).sort((a,b)=>{
        if(a.includes('Không phân loại')) return 1;
        if(b.includes('Không phân loại')) return -1;
        return a.localeCompare(b,'vi');
    });
    let html='';
    cats.forEach(cat=>{
        const list=groups[cat].sort((a,b)=> a.name.localeCompare(b.name,'vi'));
        html+=`<optgroup label="${escapeHtmlAttr(cat)}">`;
        list.forEach(c=>{
            const tl=String(c.type).toLowerCase();
            const isVoice = tl==='2' || tl==='13' || tl.includes('voice') || tl.includes('stage');
            const isAnnounce = tl==='5' || tl.includes('announcement') || tl.includes('news');
            const icon = isVoice ? '🔊' : (isAnnounce ? '📢' : '#');
            const nameEsc=escapeHtml(c.name);
            html+=`<option value="${c.id}">${icon} ${nameEsc}</option>`;
        });
        html+='</optgroup>';
    });
    return html;
}
function populateAmChannelSelects(){
    const isVoiceType = (t)=>{ const s=String(t).toLowerCase(); return s==='2' || s==='13' || s.includes('voice') || s.includes('stage'); };
    const isCategoryType = (t)=>{ const s=String(t).toLowerCase(); return s==='4' || s.includes('category'); };
    let textOnly = _amChannels.filter(c=> !isVoiceType(c.type) && !isCategoryType(c.type));
    if(!textOnly.length && _amChannels.length) textOnly = _amChannels.filter(c=> !isCategoryType(c.type));
    const grouped = buildGroupedChannelHTML(textOnly, '');
    ['amExemptSelect','amWordsBypassSelect','amSpamBypassSelect'].forEach(id=>{
        const el=document.getElementById(id);
        if(el){
            const cur=el.value;
            el.innerHTML='<option value="">＋ Thêm kênh...</option>'+ (grouped || '<option>Không có kênh text</option>');
            if(cur) el.value=cur;
        }
    });
}
function renderAutomod(cfg){
    const setSw=(id,val)=>{const el=document.getElementById(id); if(el) el.classList.toggle('on', !!val);};
    setSw('amExemptToggle', cfg.exempt_enabled);
    setSw('amWordsWarnToggle', cfg.words_violation?.warn_enabled);
    setSw('amWordsExemptToggle', cfg.words_bypass_enabled);
    setSw('amSpamWarnToggle', cfg.spam?.violation?.warn_enabled);
    setSw('amSpamExemptToggle', cfg.spam?.bypass_enabled);
    setSw('amAntiInvite', cfg.advanced?.anti_invite);
    setSw('amAntiLink', cfg.advanced?.anti_link);
    setSw('amAntiMention', cfg.advanced?.anti_mention);
    setSw('amAntiCaps', cfg.advanced?.anti_caps);
    setSw('amAntiEmoji', cfg.advanced?.anti_emoji);
    setSw('amAntiDuplicate', cfg.advanced?.anti_duplicate);
    setSw('amAntiZalgo', cfg.advanced?.anti_zalgo);
    
    const vw=document.getElementById('amWordsWarn'); if(vw) vw.value=cfg.words_violation?.warns||5;
    const vt=document.getElementById('amWordsTimeout'); if(vt) vt.value=cfg.words_violation?.timeout||5;
    const st=document.getElementById('amSpamThreshold'); if(st) st.value=cfg.spam?.threshold||5;
    const sw=document.getElementById('amSpamWindow'); if(sw) sw.value=cfg.spam?.window||5;
    const spw=document.getElementById('amSpamWarn'); if(spw) spw.value=cfg.spam?.violation?.warns||5;
    const spt=document.getElementById('amSpamTimeout'); if(spt) spt.value=cfg.spam?.violation?.timeout||5;
    
    const notice=document.getElementById('amGlobalOffNotice');
    if(notice) notice.style.display = cfg.global_enabled===false ? 'block' : 'none';
    
    renderAmWords(cfg.words||[]);
    
    renderAmChannels('amExemptChannels', cfg.exempt_channels||[], 'exempt');
    renderAmChannels('amWordsExemptChannels', cfg.words_bypass_channels||[], 'words');
    renderAmChannels('amSpamExemptChannels', cfg.spam?.bypass_channels||[], 'spam');
    
    const advs=cfg.advanced_settings||{};
    const setVal=(id,v)=>{ const el=document.getElementById(id); if(el) el.value=v; };
    const setChk=(id,v)=>{ const el=document.getElementById(id); if(el) el.checked=!!v; };
    setVal('amMentionLimit', advs.mention_limit ?? 4);
    setVal('amCapsMin', advs.caps_min ?? 8);
    setVal('amCapsPercent', advs.caps_percent ?? 70);
    setVal('amEmojiLimit', advs.emoji_limit ?? 7);
    setVal('amDuplicateLimit', advs.duplicate_limit ?? 3);
    setVal('amZalgoLimit', advs.zalgo_limit ?? 6);
    setChk('amInviteAllowOwn', advs.invite_allow_own ?? true);
    const wlEl=document.getElementById('amLinkWhitelist');
    if(wlEl){
        const list=Array.isArray(advs.link_whitelist) ? advs.link_whitelist : [];
        wlEl.value=list.join('\n');
    }
    updateAdvVisibility();
}
function renderAmWords(words){
    const box=document.getElementById('amWordsList');
    if(!box) return;
    if(!words.length){
        box.innerHTML=`<div style="padding:12px;text-align:center;color:var(--text-dim);border:1.5px dashed #ffd6e7;border-radius:12px;background:rgba(255,240,245,0.4)">Chưa có từ cấm nào — nhấn <b>Thêm từ</b> để bắt đầu.</div>`;
        return;
    }
    box.innerHTML = words.map((w,i)=>`
        <div class="am-word-row">
            <input class="am-word-input" value="${escapeHtml(w.word||w.text||'')}" placeholder="nhập từ/cụm/regex..." oninput="_amConfig.words[${i}].word=this.value" />
            <select class="am-select" onchange="_amConfig.words[${i}].type=this.value" title="Kiểu khớp">
                <option value="contains" ${w.type==='contains'?'selected':''}>Chứa từ</option>
                <option value="exact" ${w.type==='exact'?'selected':''}>Chính xác</option>
                <option value="regex" ${w.type==='regex'?'selected':''}>Regex</option>
            </select>
            <button class="btn btn-secondary btn-sm" style="padding:6px 10px" onclick="removeAmWord(${i})" title="Xóa">✕</button>
        </div>
    `).join('');
}
function addAmWord(){
    if(!_amConfig) _amConfig={words:[]};
    if(!_amConfig.words) _amConfig.words=[];
    if(_amConfig.words.length>=200) return showToast('Tối đa 200 từ','warning');
    _amConfig.words.push({word:'', type:'contains'});
    renderAmWords(_amConfig.words);
    
    setTimeout(()=>{ const inputs=document.querySelectorAll('#amWordsList .am-word-input'); if(inputs.length) inputs[inputs.length-1].focus(); },50);
}
function removeAmWord(idx){
    if(!_amConfig||!_amConfig.words) return;
    _amConfig.words.splice(idx,1);
    renderAmWords(_amConfig.words);
}
function getChannelById(id){
    return _amChannels.find(x=> String(x.id)===String(id)) || null;
}
function chNameById(id){
    const c=getChannelById(id);
    return c? '#'+c.name : id;
}
function renderAmChannels(containerId, ids, type){
    const el=document.getElementById(containerId);
    if(!el) return;
    if(!ids.length){ el.innerHTML=''; return; }
    el.innerHTML = ids.map(id=>{
        const c=getChannelById(id);
        const icon = c ? (String(c.type).includes('2') ? '🔊 ' : '# ') : '# ';
        const name = c ? escapeHtml(c.name) : escapeHtml(String(id));
        const cat = c && c.category ? `<span class="am-chip-cat">${escapeHtml(c.category)}</span>` : '';
        return `<span class="am-chip selected" onclick="removeAmChannel('${type}','${id}')" title="${c ? escapeHtmlAttr((c.category? c.category+' • ':'') + c.name) : ''}">${icon}${name}${cat} <span style="font-weight:800; margin-left:4px">×</span></span>`;
    }).join('');
}
function addAmChannel(type, selectId){
    const sel=document.getElementById(selectId);
    if(!sel || !sel.value) return showToast('Chọn kênh trước','warning');
    const id=String(sel.value);
    if(type==='exempt'){
        _amConfig.exempt_channels = _amConfig.exempt_channels||[];
        if(_amConfig.exempt_channels.includes(id)) return showToast('Kênh đã có','warning');
        _amConfig.exempt_channels.push(id);
        renderAmChannels('amExemptChannels', _amConfig.exempt_channels,'exempt');
    } else if(type==='words'){
        _amConfig.words_bypass_channels = _amConfig.words_bypass_channels||[];
        if(_amConfig.words_bypass_channels.includes(id)) return showToast('Kênh đã có','warning');
        _amConfig.words_bypass_channels.push(id);
        renderAmChannels('amWordsExemptChannels', _amConfig.words_bypass_channels,'words');
    } else if(type==='spam'){
        if(!_amConfig.spam) _amConfig.spam={bypass_channels:[]};
        _amConfig.spam.bypass_channels = _amConfig.spam.bypass_channels||[];
        if(_amConfig.spam.bypass_channels.includes(id)) return showToast('Kênh đã có','warning');
        _amConfig.spam.bypass_channels.push(id);
        renderAmChannels('amSpamExemptChannels', _amConfig.spam.bypass_channels,'spam');
    }
    sel.value='';
}
function addAmExempt(){ addAmChannel('exempt','amExemptSelect'); }
function addAmWordsBypass(){ addAmChannel('words','amWordsBypassSelect'); }
function addAmSpamBypass(){ addAmChannel('spam','amSpamBypassSelect'); }
function removeAmChannel(type, id){
    if(type==='exempt'){ _amConfig.exempt_channels = (_amConfig.exempt_channels||[]).filter(x=> x!==id); renderAmChannels('amExemptChannels', _amConfig.exempt_channels,'exempt'); }
    else if(type==='words'){ _amConfig.words_bypass_channels = (_amConfig.words_bypass_channels||[]).filter(x=> x!==id); renderAmChannels('amWordsExemptChannels', _amConfig.words_bypass_channels,'words'); }
    else if(type==='spam'){ _amConfig.spam.bypass_channels = (_amConfig.spam.bypass_channels||[]).filter(x=> x!==id); renderAmChannels('amSpamExemptChannels', _amConfig.spam.bypass_channels,'spam'); }
}
async function saveAutomod(){
    if(!_amGuildId || !_amConfig) return showToast('Chưa tải cấu hình','warning');
    
    _amConfig.exempt_enabled = document.getElementById('amExemptToggle')?.classList.contains('on');
    _amConfig.words_violation = {
        warn_enabled: document.getElementById('amWordsWarnToggle')?.classList.contains('on'),
        warns: parseInt(document.getElementById('amWordsWarn')?.value)||5,
        timeout: parseInt(document.getElementById('amWordsTimeout')?.value)||5
    };
    _amConfig.words_bypass_enabled = document.getElementById('amWordsExemptToggle')?.classList.contains('on');
    _amConfig.spam = {
        threshold: parseInt(document.getElementById('amSpamThreshold')?.value)||5,
        window: parseInt(document.getElementById('amSpamWindow')?.value)||5,
        violation: {
            warn_enabled: document.getElementById('amSpamWarnToggle')?.classList.contains('on'),
            warns: parseInt(document.getElementById('amSpamWarn')?.value)||5,
            timeout: parseInt(document.getElementById('amSpamTimeout')?.value)||5
        },
        bypass_enabled: document.getElementById('amSpamExemptToggle')?.classList.contains('on'),
        bypass_channels: _amConfig.spam?.bypass_channels||[]
    };
    _amConfig.advanced = {
        anti_invite: document.getElementById('amAntiInvite')?.classList.contains('on'),
        anti_link: document.getElementById('amAntiLink')?.classList.contains('on'),
        anti_mention: document.getElementById('amAntiMention')?.classList.contains('on'),
        anti_caps: document.getElementById('amAntiCaps')?.classList.contains('on'),
        anti_emoji: document.getElementById('amAntiEmoji')?.classList.contains('on'),
        anti_duplicate: document.getElementById('amAntiDuplicate')?.classList.contains('on'),
        anti_zalgo: document.getElementById('amAntiZalgo')?.classList.contains('on')
    };
    _amConfig.advanced_settings = {
        mention_limit: parseInt(document.getElementById('amMentionLimit')?.value)||4,
        caps_min: parseInt(document.getElementById('amCapsMin')?.value)||8,
        caps_percent: parseInt(document.getElementById('amCapsPercent')?.value)||70,
        emoji_limit: parseInt(document.getElementById('amEmojiLimit')?.value)||7,
        duplicate_limit: parseInt(document.getElementById('amDuplicateLimit')?.value)||3,
        zalgo_limit: parseInt(document.getElementById('amZalgoLimit')?.value)||6,
        link_whitelist: (document.getElementById('amLinkWhitelist')?.value || '').split(/[\n,]+/).map(s=>s.trim()).filter(Boolean),
        invite_allow_own: !!document.getElementById('amInviteAllowOwn')?.checked
    };
    
    _amConfig.words = (_amConfig.words||[]).filter(w=> (w.word||w.text||'').trim() );
    
    _amConfig.words = _amConfig.words.map(w=>({word: String(w.word||w.text||'').trim().slice(0,80), type: ['contains','exact','regex'].includes(w.type)? w.type:'contains'}));
    
    for(const w of _amConfig.words){
        if(w.type==='regex'){
            try{ new RegExp(w.word); }catch(e){ return showToast('Regex lỗi: '+w.word+' — '+e.message,'error'); }
        }
    }
    if(_amConfig.spam.threshold<2||_amConfig.spam.threshold>50) return showToast('Ngưỡng spam 2-50','warning');
    if(_amConfig.spam.window<1||_amConfig.spam.window>120) return showToast('Cửa sổ spam 1-120','warning');
    const res = await apiRequest(`/api/guilds/${_amGuildId}/automod`,'POST', _amConfig);
    if(res.ok){ showToast(res.message||'Đã lưu Auto-Moderation','success'); _amConfig=res.automod||_amConfig; renderAutomod(_amConfig); }
    else showToast(res.error||'Lỗi lưu','error');
}
async function saveGuildSettingsFromDrawer() {
    const guildId = document.getElementById('drawerGuildId').value;
    const prefix = document.getElementById('drawerPrefix').value.trim();
    if(prefix && (prefix.length<1 || prefix.length>5)) return showToast('Prefix 1-5 ký tự','warning');
    const language = document.getElementById('drawerLang').value;
    const admin_only = document.getElementById('switchAdminOnly')?.classList.contains('on')||false;
    const automod_enabled = document.getElementById('switchAutomod')?.classList.contains('on')||false;
    const leveling_enabled = document.getElementById('switchLeveling')?.classList.contains('on')||false;
    const economy_enabled = document.getElementById('switchEconomy')?.classList.contains('on')||false;
    const tiktok_enabled = document.getElementById('switchTiktok')?.classList.contains('on')||false;
    const res = await apiRequest(`/api/guilds/${guildId}/settings`, 'POST', { prefix, language, admin_only, automod_enabled, leveling_enabled, economy_enabled, tiktok_enabled });
    if (res.ok) {
        showToast('Đã lưu cài đặt!', 'success');
        const prefixInput = document.getElementById('drawerPrefix');
        const languageSelect = document.getElementById('drawerLang');
        if (prefixInput) prefixInput.value = prefix || 's!';
        if (languageSelect) languageSelect.value = language || 'vi';
        await loadServerConfig(guildId);
        await loadGuilds();
    } else {
        showToast(res.error || 'Lỗi lưu', 'error');
    }
}
async function loadServerConfig(guildId){
    const res = await apiRequest(`/api/guilds/${guildId}/server-config`);
    if(!res.ok) return;
    const c=res.config||{};
    if(document.getElementById('drawerPrefix')) document.getElementById('drawerPrefix').value=c.prefix||'s!';
    if(document.getElementById('drawerLang')) document.getElementById('drawerLang').value=c.language||'vi';
    const setSw=(id,val)=>{const el=document.getElementById(id); if(el) el.classList.toggle('on', !!val);};
    setSw('switchAdminOnly', c.admin_only); setSw('switchAutomod', c.automod_enabled); setSw('switchLeveling', c.leveling_enabled); setSw('switchEconomy', c.economy_enabled); setSw('switchTiktok', c.tiktok_enabled);
}
function togglePlaceholderGuide(){
    const guide=document.getElementById('placeholderGuide');
    if(!guide) return;
    guide.style.display = (guide.style.display === 'none' || !guide.style.display) ? 'block' : 'none';
}
let currentWelcomeSubTab = 'welcome';

function switchWelcomeSubTab(sub) {
    currentWelcomeSubTab = sub;
    const panes = {
        'welcome': document.getElementById('wcSubPaneWelcome'),
        'goodbye': document.getElementById('wcSubPaneGoodbye'),
        'boost': document.getElementById('wcSubPaneBoost')
    };
    const btns = {
        'welcome': document.getElementById('btnWcTabWelcome'),
        'goodbye': document.getElementById('btnWcTabGoodbye'),
        'boost': document.getElementById('btnWcTabBoost')
    };
    const previewCards = {
        'welcome': document.getElementById('wcPreviewCardWelcome'),
        'goodbye': document.getElementById('wcPreviewCardGoodbye'),
        'boost': document.getElementById('wcPreviewCardBoost')
    };
    Object.keys(panes).forEach(k => {
        if (panes[k]) panes[k].style.display = (k === sub ? 'block' : 'none');
        if (btns[k]) btns[k].classList.toggle('active', k === sub);
        if (previewCards[k]) previewCards[k].style.display = (k === sub ? 'block' : 'none');
    });
    renderWelcomePreview();
}

function updateChannelBadge(selectId) {
    const sel = document.getElementById(selectId);
    const nameEl = document.getElementById(selectId + 'Name');
    if (!sel || !nameEl) return;
    if (sel.value) {
        const opt = sel.options[sel.selectedIndex];
        nameEl.textContent = opt ? (opt.textContent.trim() || sel.value) : sel.value;
        nameEl.style.color = 'var(--accent-cyan)';
    } else {
        nameEl.textContent = 'Chưa cấu hình';
        nameEl.style.color = 'var(--text-muted)';
    }
}

function clearChannelSetup(selectId) {
    const sel = document.getElementById(selectId);
    if (sel) {
        sel.value = '';
        updateChannelBadge(selectId);
        if (typeof renderWelcomePreview === 'function') renderWelcomePreview();
        showToast('Đã hủy cấu hình kênh này (Nhớ bấm Lưu thay đổi)', 'info');
    }
}

function renderWelcomePreview() {
    const getChannelName = (selId) => {
        const sel = document.getElementById(selId);
        if (!sel || !sel.value) return '— Chưa đặt —';
        const opt = sel.options[sel.selectedIndex];
        return opt ? opt.textContent.trim() : sel.value;
    };
    const replaceKeys = (text, userName = 'SakuraMember', server = 'Sakura Paradise') => {
        return (text || '')
            .replace(/\{user\}/gi, `<span style="color:var(--accent-pink);font-weight:600">@${userName}</span>`)
            .replace(/\{user_name\}/gi, userName)
            .replace(/\{server\}/gi, server)
            .replace(/\{guild_name\}/gi, server)
            .replace(/\{mention\}/gi, `<span style="color:var(--accent-pink);font-weight:600">@${userName}</span>`);
    };

    const previewChan = document.getElementById('welcomePreviewChannels');
    const previewBox = document.getElementById('welcomePreviewMessage');
    const previewImg = document.getElementById('welcomePreviewImage');
    if (!previewBox) return;

    let title = '', msg = '', footer = '', img = '', thumb = '', col = '#FF79C6', chName = '';
    if (currentWelcomeSubTab === 'goodbye') {
        title = document.getElementById('goodbyeTitle')?.value || '👋 TẠM BIỆT THÀNH VIÊN!';
        msg = document.getElementById('goodbyeMsg')?.value || 'Tạm biệt {user} 👋 Hẹn gặp lại một ngày không xa!';
        footer = document.getElementById('goodbyeFooter')?.value || 'Sakura Bot • Hẹn gặp lại bạn';
        img = document.getElementById('goodbyeImage')?.value?.trim();
        thumb = document.getElementById('goodbyeThumb')?.value?.trim();
        col = document.getElementById('goodbyeColor')?.value || '#FF5555';
        chName = getChannelName('goodbyeChannel');
    } else if (currentWelcomeSubTab === 'boost') {
        title = document.getElementById('boostTitle')?.value || '🚀 CẢM ƠN SERVER BOOSTER!';
        msg = document.getElementById('boostMsg')?.value || 'Cảm ơn {user} đã nâng cấp máy chủ {server}! 💖 Bạn đã nhận các đặc quyền xịn sò!';
        footer = document.getElementById('boostFooter')?.value || 'Sakura Bot • Server Boost Supporter';
        img = document.getElementById('boostImage')?.value?.trim();
        thumb = document.getElementById('boostThumb')?.value?.trim();
        col = document.getElementById('boostColor')?.value || '#FF79C6';
        chName = getChannelName('boostChannel');
    } else {
        title = document.getElementById('welcomeTitle')?.value || '🌸 CHÀO MỪNG THÀNH VIÊN MỚI!';
        msg = document.getElementById('welcomeMsg')?.value || 'Chào mừng {user} đến với {server}! 🌸 Hãy đọc luật và vui vẻ nhé~';
        footer = document.getElementById('welcomeFooter')?.value || 'Sakura Bot • Chúc bạn có những phút giây vui vẻ!';
        img = document.getElementById('welcomeImage')?.value?.trim();
        thumb = document.getElementById('welcomeThumb')?.value?.trim();
        col = document.getElementById('welcomeColor')?.value || '#FF79C6';
        chName = getChannelName('welcomeChannel');
    }

    if (previewChan) {
        previewChan.innerHTML = `Đang xem cấu hình: <b style="color:var(--accent-pink)">${currentWelcomeSubTab.toUpperCase()}</b> • Kênh gửi: <b>${chName}</b>`;
    }

    previewBox.style.borderLeft = `4px solid ${col}`;
    previewBox.innerHTML = `
        <div style="display:flex;justify-content:space-between;align-items:flex-start;gap:10px">
            <div style="flex:1">
                <div style="font-weight:800;font-size:1.05rem;color:${col};margin-bottom:6px">${escapeHtml(title)}</div>
                <div style="font-size:.88rem;color:var(--text-main);line-height:1.6;white-space:pre-wrap">${replaceKeys(msg)}</div>
            </div>
            ${thumb ? `<img src="${escapeHtml(thumb)}" style="width:52px;height:52px;border-radius:10px;object-fit:cover;border:1px solid var(--border-glass)" onerror="this.style.display='none'">` : ''}
        </div>
        ${footer ? `<div style="margin-top:10px;font-size:.75rem;color:var(--text-muted);border-top:1px solid rgba(255,255,255,0.06);padding-top:6px">📌 ${escapeHtml(footer)}</div>` : ''}
    `;

    if (previewImg) {
        if (img) {
            previewImg.innerHTML = `<img src="${escapeHtml(img)}" style="max-width:100%;max-height:180px;border-radius:10px;margin-top:10px;object-fit:cover;border:1px solid var(--border-glass)" onerror="this.outerHTML='<div style=\\'color:var(--accent-red);font-size:.75rem\\'>⚠️ Link ảnh banner không tải được</div>'">`;
        } else {
            previewImg.innerHTML = '';
        }
    }
}

async function loadWelcome(guildId){
    const res=await apiRequest(`/api/guilds/${guildId}/welcome`);
    if(!res.ok) return;
    const w=res.welcome||{};
    if(document.getElementById('welcomeChannel')) document.getElementById('welcomeChannel').value=w.channel_id||'';
    if(document.getElementById('goodbyeChannel')) document.getElementById('goodbyeChannel').value=w.goodbye_channel||'';
    if(document.getElementById('boostChannel')) document.getElementById('boostChannel').value=w.boost_channel||'';
    if(document.getElementById('switchBoostMessage')) {
        const boostEnabled = !!w.boost_message;
        document.getElementById('switchBoostMessage').classList.toggle('on', boostEnabled);
    }
    
    if(document.getElementById('welcomeTitle')) document.getElementById('welcomeTitle').value=w.welcome_title||'';
    if(document.getElementById('welcomeColor')) document.getElementById('welcomeColor').value=w.welcome_color||'#FF79C6';
    if(document.getElementById('welcomeMsg')) document.getElementById('welcomeMsg').value=w.message||'';
    if(document.getElementById('welcomeFooter')) document.getElementById('welcomeFooter').value=w.welcome_footer||'';
    if(document.getElementById('welcomeImage')) document.getElementById('welcomeImage').value=w.welcome_image||'';
    if(document.getElementById('welcomeThumb')) document.getElementById('welcomeThumb').value=w.welcome_thumb||'';

    
    if(document.getElementById('goodbyeTitle')) document.getElementById('goodbyeTitle').value=w.goodbye_title||'';
    if(document.getElementById('goodbyeColor')) document.getElementById('goodbyeColor').value=w.goodbye_color||'#FF5555';
    if(document.getElementById('goodbyeMsg')) document.getElementById('goodbyeMsg').value=w.goodbye_message||'';
    if(document.getElementById('goodbyeFooter')) document.getElementById('goodbyeFooter').value=w.goodbye_footer||'';
    if(document.getElementById('goodbyeImage')) document.getElementById('goodbyeImage').value=w.goodbye_image||'';
    if(document.getElementById('goodbyeThumb')) document.getElementById('goodbyeThumb').value=w.goodbye_thumb||'';

    
    if(document.getElementById('boostTitle')) document.getElementById('boostTitle').value=w.boost_title||'';
    if(document.getElementById('boostColor')) document.getElementById('boostColor').value=w.boost_color||'#FF79C6';
    if(document.getElementById('boostMsg')) document.getElementById('boostMsg').value=w.boost_message_text||'';
    if(document.getElementById('boostFooter')) document.getElementById('boostFooter').value=w.boost_footer||'';
    if(document.getElementById('boostImage')) document.getElementById('boostImage').value=w.boost_image||'';
    if(document.getElementById('boostThumb')) document.getElementById('boostThumb').value=w.boost_thumb||'';

    updateChannelBadge('welcomeChannel');
    updateChannelBadge('goodbyeChannel');
    updateChannelBadge('boostChannel');
    renderWelcomePreview();
}

async function saveWelcome(){
    const gid=document.getElementById('drawerGuildId').value;
    const boostToggle=document.getElementById('switchBoostMessage');
    const body={
        channel_id: document.getElementById('welcomeChannel')?.value||null,
        welcome_title: document.getElementById('welcomeTitle')?.value||'',
        welcome_color: document.getElementById('welcomeColor')?.value||'#FF79C6',
        message: document.getElementById('welcomeMsg')?.value||'',
        welcome_footer: document.getElementById('welcomeFooter')?.value||'',
        welcome_image: document.getElementById('welcomeImage')?.value?.trim()||'',
        welcome_thumb: document.getElementById('welcomeThumb')?.value?.trim()||'',

        goodbye_channel: document.getElementById('goodbyeChannel')?.value||null,
        goodbye_title: document.getElementById('goodbyeTitle')?.value||'',
        goodbye_color: document.getElementById('goodbyeColor')?.value||'#FF5555',
        goodbye_message: document.getElementById('goodbyeMsg')?.value||'',
        goodbye_footer: document.getElementById('goodbyeFooter')?.value||'',
        goodbye_image: document.getElementById('goodbyeImage')?.value?.trim()||'',
        goodbye_thumb: document.getElementById('goodbyeThumb')?.value?.trim()||'',

        boost_channel: document.getElementById('boostChannel')?.value||null,
        boost_message: !!(boostToggle && boostToggle.classList.contains('on')),
        boost_title: document.getElementById('boostTitle')?.value||'',
        boost_color: document.getElementById('boostColor')?.value||'#FF79C6',
        boost_message_text: document.getElementById('boostMsg')?.value||'',
        boost_footer: document.getElementById('boostFooter')?.value||'',
        boost_image: document.getElementById('boostImage')?.value?.trim()||'',
        boost_thumb: document.getElementById('boostThumb')?.value?.trim()||''
    };
    const res=await apiRequest(`/api/guilds/${gid}/welcome`,'POST',body);
    if(res.ok) {
        showToast('Đã lưu cấu hình Welcome / Goodbye / Boost','success');
        updateChannelBadge('welcomeChannel');
        updateChannelBadge('goodbyeChannel');
        updateChannelBadge('boostChannel');
        renderWelcomePreview();
    } else showToast(res.error||'Lỗi','error');
}
async function testWelcome(kind){
    const gid=document.getElementById('drawerGuildId').value;
    
    await saveWelcome();
    const res=await apiRequest(`/api/guilds/${gid}/welcome/test`,'POST',{kind});
    if(res.ok) showToast(res.message||'Đã gửi test','success'); else showToast(res.error||'Lỗi test','error');
}

async function loadTempVoice(guildId){
    const sel=document.getElementById('tempVoiceChannel');
    const status=document.getElementById('tempVoiceStatus');
    const badge=document.getElementById('tempVoiceBadge');
    const preview=document.getElementById('tempVoicePreview');
    if(status) status.textContent='Đang tải...';
    const res=await apiRequest(`/api/guilds/${guildId}/tempvoice`);
    if(!res.ok){
        if(status) status.textContent='Lỗi tải';
        return;
    }
    const cid=res.tempvoice?.channel_id || '';
    if(sel) sel.value = cid ? String(cid) : '';
    const isOn=!!cid;
    if(badge) { badge.textContent=isOn?'🟢 Đang bật':'⚪ Đã tắt'; badge.className=isOn?'badge badge-green':'badge badge-sakura'; }
    if(status) status.textContent=isOn? 'Đang hoạt động — vào kênh sẽ tạo phòng riêng' : 'Đang tắt — chọn kênh để bật';
    if(preview){
        if(isOn){
            const ch=_amChannels.find(c=> String(c.id)===String(cid)) || _amChannels.find(c=> String(c.id)===String(cid));
            
            const name = ch ? ch.name : cid;
            preview.innerHTML=`Kênh Join to Create: <b>🔊 ${escapeHtml(name)}</b> • Khi thành viên vào sẽ tạo kênh cùng category, rời thì tự xóa.`;
        } else {
            preview.textContent='Chưa chọn kênh — TempVoice đang tắt.';
        }
    }
}
async function saveTempVoice(){
    const gid=document.getElementById('drawerGuildId').value;
    const cid=document.getElementById('tempVoiceChannel')?.value || null;
    
    const body={channel_id: cid ? String(cid) : null};
    const res=await apiRequest(`/api/guilds/${gid}/tempvoice`,'POST',body);
    if(res.ok){ showToast(res.message||'Đã lưu TempVoice','success'); loadTempVoice(gid); }
    else showToast(res.error||'Lỗi','error');
}

async function loadConfession(guildId){
    const res=await apiRequest(`/api/guilds/${guildId}/confession`);
    if(!res.ok) return;
    const c=res.confession||{};
    const setSw=(id,v)=>{const el=document.getElementById(id); if(el) el.classList.toggle('on', !!v);};
    setSw('cfsEnabled', c.enabled);
    setSw('cfsAllowPublic', c.allow_public);
    setSw('cfsAllowAnon', c.allow_anonymous);
    setSw('cfsThread', c.create_thread);
    setSw('cfsAnonReply', c.anon_reply);
    if(document.getElementById('cfsChannel')) document.getElementById('cfsChannel').value = c.confession_channel_id ? String(c.confession_channel_id) : '';
    if(document.getElementById('cfsLogChannel')) document.getElementById('cfsLogChannel').value = c.log_channel_id ? String(c.log_channel_id) : '';
    
    if(document.getElementById('cfsPostChannel') && !document.getElementById('cfsPostChannel').value){
        
    }
}
async function saveConfession(){
    const gid=document.getElementById('drawerGuildId').value;
    const body={
        enabled: document.getElementById('cfsEnabled')?.classList.contains('on'),
        confession_channel_id: document.getElementById('cfsChannel')?.value || null,
        log_channel_id: document.getElementById('cfsLogChannel')?.value || null,
        allow_public: document.getElementById('cfsAllowPublic')?.classList.contains('on'),
        allow_anonymous: document.getElementById('cfsAllowAnon')?.classList.contains('on'),
        create_thread: document.getElementById('cfsThread')?.classList.contains('on'),
        anon_reply: document.getElementById('cfsAnonReply')?.classList.contains('on'),
    };
    if(body.enabled && !body.confession_channel_id) return showToast('Chọn Kênh Confession trước khi bật','warning');
    if(!body.allow_public && !body.allow_anonymous) return showToast('Phải bật ít nhất 1 kiểu (Công khai hoặc Ẩn danh)','warning');
    const res=await apiRequest(`/api/guilds/${gid}/confession`,'POST',body);
    if(res.ok){ showToast(res.message||'Đã lưu Confession','success'); }
    else showToast(res.error||'Lỗi','error');
}
async function postConfessionPanel(){
    const gid=document.getElementById('drawerGuildId').value;
    const ch = document.getElementById('cfsPostChannel')?.value || document.getElementById('cfsChannel')?.value || null;
    if(!ch) return showToast('Chọn kênh đăng panel','warning');
    const btn=document.querySelector('button[onclick="postConfessionPanel()"]');
    if(btn){ btn.disabled=true; btn.textContent='⏳ Đang đăng...'; }
    const res=await apiRequest(`/api/guilds/${gid}/confession/panel`,'POST',{channel_id: String(ch)});
    if(btn){ btn.disabled=false; btn.textContent='✈️ Đăng panel'; }
    const st=document.getElementById('cfsPostStatus');
    if(res.ok){ showToast(res.message,'success'); if(st) st.textContent='✅ '+res.message; }
    else { showToast(res.error||'Lỗi','error'); if(st) st.textContent='❌ '+(res.error||'Lỗi'); }
}

async function loadAuditLogs(guildId){
    const res=await apiRequest(`/api/guilds/${guildId}/audit`);
    if(!res.ok) return;
    const a=res.audit||{};
    const setVal=(id, val)=>{
        const el=document.getElementById(id);
        if(el) el.value = val ? String(val) : '';
    };
    setVal('auditMessage', a.message);
    setVal('auditMember', a.member);
    setVal('auditJoin', a.join);
    setVal('auditVoice', a.voice);
    setVal('auditServer', a.server);
}
async function saveAuditLogs(){
    const gid=document.getElementById('drawerGuildId').value;
    const body={
        message: document.getElementById('auditMessage')?.value || null,
        member: document.getElementById('auditMember')?.value || null,
        join: document.getElementById('auditJoin')?.value || null,
        voice: document.getElementById('auditVoice')?.value || null,
        server: document.getElementById('auditServer')?.value || null,
    };
    const res=await apiRequest(`/api/guilds/${gid}/audit`,'POST',body);
    if(res.ok) showToast(res.message||'Đã lưu Audit Logs','success');
    else showToast(res.error||'Lỗi','error');
}

let _blMembersCache=[], _blSelectedIds=new Set(), _blGuildCache=[], _blGlobalCache=[];
async function loadBlacklist(guildId){
    const res=await apiRequest(`/api/guilds/${guildId}/blacklist`);
    if(!res.ok){
        const el=document.getElementById('blServerList');
        if(el) el.innerHTML=`<div style="color:var(--accent-red); font-size:.85rem">Lỗi tải: ${res.error||'?'}</div>`;
        return;
    }
    _blGuildCache=res.guild_blacklist||[];
    _blGlobalCache=res.global_blacklist||[];
    
    
    if(_modMembersCache && _modMembersCache.length){
        _blMembersCache=_modMembersCache.slice();
    } else if(_blMembersCache.length===0){
        
        try{
            const mres=await apiRequest(`/api/guilds/${guildId}/members`);
            if(mres.ok) _blMembersCache=mres.members||[];
        }catch{}
    }
    if(document.getElementById('blServerMemberTotal')) document.getElementById('blServerMemberTotal').textContent=_blMembersCache.length;
    _blSelectedIds.clear();
    const tid=document.getElementById('blServerTargetId');
    if(tid) tid.value='';
    const custom=document.getElementById('blServerCustomId');
    if(custom) custom.value='';
    updateBlSelectedInfo();
    renderBlacklistMembers(_blMembersCache);
    renderGuildBlacklist(_blGuildCache);
    renderGlobalBlacklist(_blGlobalCache);
    
    const gsec=document.getElementById('blGlobalSection');
    if(gsec) gsec.style.display = res.is_admin ? 'block' : 'none';
    if(document.getElementById('blServerCount')) document.getElementById('blServerCount').textContent=_blGuildCache.length;
    if(document.getElementById('blServerListCount')) document.getElementById('blServerListCount').textContent=_blGuildCache.length;
    if(document.getElementById('blGlobalCount')) document.getElementById('blGlobalCount').textContent=_blGlobalCache.length;
}
function renderBlacklistMembers(list){
    const el=document.getElementById('blServerMemberList');
    if(!el) return;
    if(!list.length){ el.innerHTML='<div style="padding:12px; text-align:center; color:var(--text-dim)">Không có thành viên</div>'; return; }
    el.innerHTML=list.map(m=>{
        const sel=_blSelectedIds.has(m.id);
        return `<div class="member-option ${sel?'selected':''}" data-id="${m.id}" onclick="selectBlacklistMember('${m.id}', event)" style="display:flex; gap:10px; align-items:center; padding:8px 10px; border-radius:10px; cursor:pointer; transition:.15s; background:${sel?'rgba(255,121,198,0.12)':'transparent'}; border:1px solid ${sel?'var(--sakura-pink)':'transparent'}">
            <input type="checkbox" ${sel?'checked':''} onclick="event.stopPropagation(); selectBlacklistMember('${m.id}', event)" style="width:16px; height:16px; accent-color:var(--sakura-pink)">
            <img src="${m.avatar||'https://cdn.discordapp.com/embed/avatars/0.png'}" style="width:32px; height:32px; border-radius:50%; object-fit:cover; border:1px solid var(--border-subtle); flex-shrink:0" onerror="this.src='https://cdn.discordapp.com/embed/avatars/0.png'">
            <div style="flex:1; min-width:0"><div style="font-weight:600; font-size:.9rem; white-space:nowrap; overflow:hidden; text-overflow:ellipsis">${m.name} ${m.bot?'<span style=\"font-size:.7rem; background:var(--accent-purple); color:#fff; padding:1px 5px; border-radius:5px; margin-left:4px\">BOT</span>':''}</div><div style="font-size:.78rem; color:var(--text-dim); white-space:nowrap; overflow:hidden; text-overflow:ellipsis">@${m.username} • ${m.id}</div></div>
            <span style="color:var(--sakura-pink); font-size:1rem; opacity:${sel?1:0}">✓</span>
        </div>`;
    }).join('');
}
function filterBlacklistMembers(){
    const q=(document.getElementById('blServerSearch')?.value||'').toLowerCase();
    if(!q) return renderBlacklistMembers(_blMembersCache);
    const f=_blMembersCache.filter(m=> m.name.toLowerCase().includes(q) || m.username.toLowerCase().includes(q) || m.id.includes(q));
    renderBlacklistMembers(f);
}
function selectBlacklistMember(id, e){
    if(e) e.preventDefault();
    if(_blSelectedIds.has(id)) _blSelectedIds.delete(id); else _blSelectedIds.add(id);
    const tid=document.getElementById('blServerTargetId');
    if(tid) tid.value=Array.from(_blSelectedIds).join(',');
    const custom=document.getElementById('blServerCustomId');
    if(custom) custom.value='';
    updateBlSelectedInfo();
    const q=(document.getElementById('blServerSearch')?.value||'').toLowerCase();
    const list=q? _blMembersCache.filter(x=> x.name.toLowerCase().includes(q)||x.username.toLowerCase().includes(q)||x.id.includes(q)) : _blMembersCache;
    renderBlacklistMembers(list);
}
function updateBlSelectedInfo(){
    const info=document.getElementById('blServerSelectedInfo');
    if(!info) return;
    if(_blSelectedIds.size===0){ info.style.display='none'; return; }
    const names=Array.from(_blSelectedIds).map(id=>{ const m=_blMembersCache.find(x=>x.id===id); return m? m.name : id; });
    info.style.display='block';
    info.innerHTML=`Đã chọn <strong>${_blSelectedIds.size}</strong>: ${names.slice(0,3).join(', ')}${names.length>3?' +'+(names.length-3):''} <a href="#" onclick="_blSelectedIds.clear();document.getElementById('blServerTargetId').value='';updateBlSelectedInfo();renderBlacklistMembers(_blMembersCache);return false;" style="color:var(--sakura-pink); margin-left:8px">Xóa chọn</a>`;
}
function renderGuildBlacklist(list){
    const el=document.getElementById('blServerList');
    if(!el) return;
    if(!list.length){ el.innerHTML='<div style="padding:12px; text-align:center; color:var(--text-dim); border:1.5px dashed var(--border-subtle); border-radius:10px">Chưa có ai bị cấm ở server này</div>'; return; }
    el.innerHTML=list.map(u=>`<div style="display:flex; justify-content:space-between; align-items:center; padding:10px 12px; background:var(--bg-card); border:1px solid var(--border-glass); border-radius:12px">
        <div style="display:flex; gap:10px; align-items:center; min-width:0">
            <img src="${u.avatar||'https://cdn.discordapp.com/embed/avatars/0.png'}" style="width:36px; height:36px; border-radius:50%; object-fit:cover; border:1.5px solid var(--border-glass); flex-shrink:0" onerror="this.src='https://cdn.discordapp.com/embed/avatars/0.png'">
            <div style="min-width:0"><div style="font-weight:700; font-size:.9rem; white-space:nowrap; overflow:hidden; text-overflow:ellipsis">${escapeHtml(u.name)}</div><div style="font-size:.78rem; color:var(--text-dim)">${u.id}</div></div>
        </div>
        <button class="btn btn-secondary btn-sm" onclick="removeGuildBlacklist('${u.id}')" style="flex-shrink:0">🔓 Mở</button>
    </div>`).join('');
}
function renderGlobalBlacklist(list){
    const el=document.getElementById('blGlobalList');
    if(!el) return;
    if(!list.length){ el.innerHTML='<div style="padding:12px; text-align:center; color:var(--text-dim); border:1.5px dashed var(--border-subtle); border-radius:10px">Chưa có ai bị cấm toàn cục</div>'; return; }
    el.innerHTML=list.map(u=>`<div style="display:flex; justify-content:space-between; align-items:center; padding:10px 12px; background:rgba(255, 85, 85, 0.06); border:1px solid rgba(255,85,85,0.2); border-radius:12px">
        <div style="display:flex; gap:10px; align-items:center; min-width:0">
            <img src="${u.avatar||'https://cdn.discordapp.com/embed/avatars/0.png'}" style="width:36px; height:36px; border-radius:50%; object-fit:cover; border:1.5px solid rgba(255,85,85,0.3); flex-shrink:0" onerror="this.src='https://cdn.discordapp.com/embed/avatars/0.png'">
            <div style="min-width:0"><div style="font-weight:700; font-size:.9rem">${escapeHtml(u.name)}</div><div style="font-size:.78rem; color:var(--text-dim)">${u.id} • global</div></div>
        </div>
        <button class="btn btn-danger btn-sm" onclick="removeGlobalBlacklist('${u.id}')" style="flex-shrink:0">🔓 Mở global</button>
    </div>`).join('');
}
async function addGuildBlacklist(){
    const gid=document.getElementById('drawerGuildId').value;
    const custom=(document.getElementById('blServerCustomId')?.value||'').trim();
    const selVal=(document.getElementById('blServerTargetId')?.value||'').trim();
    const raw = custom || selVal;
    if(!raw) return showToast('Chọn thành viên hoặc nhập ID','warning');
    const ids=raw.split(/[,\s]+/).map(s=>s.trim()).filter(Boolean).filter(s=>/^\d{15,22}$/.test(s));
    if(!ids.length) return showToast('ID không hợp lệ (15-22 số)','warning');
    let ok=0, fail=0;
    for(const uid of ids){
        const res=await apiRequest(`/api/guilds/${gid}/blacklist`,'POST',{action:'add', user_id:uid});
        if(res.ok) ok++; else { fail++; showToast(res.error||'Lỗi '+uid,'error'); }
    }
    if(ok) { showToast(`Đã cấm ${ok} user ở server`,'success'); loadBlacklist(gid); }
    if(fail) showToast(`${fail} lỗi`,'warning');
}
async function removeGuildBlacklist(uid){
    const gid=document.getElementById('drawerGuildId').value;
    if(!confirm(`Mở cấm ${uid} ở server này?`)) return;
    const res=await apiRequest(`/api/guilds/${gid}/blacklist`,'POST',{action:'remove', user_id:uid});
    if(res.ok){ showToast(res.message||'Đã mở','success'); loadBlacklist(gid); } else showToast(res.error||'Lỗi','error');
}
async function addGlobalBlacklist(){
    const uid=(document.getElementById('blGlobalId')?.value||'').trim();
    if(!uid || !/^\d{15,22}$/.test(uid)) return showToast('Nhập ID hợp lệ','warning');
    const res=await apiRequest(`/api/blacklist/global`,'POST',{action:'add', user_id:uid});
    if(res.ok){ showToast(res.message,'success'); document.getElementById('blGlobalId').value=''; const gid=document.getElementById('drawerGuildId').value; if(gid) loadBlacklist(gid); else loadGlobalOnly(); } else showToast(res.error||'Lỗi','error');
}
async function removeGlobalBlacklist(uid){
    if(!confirm(`Mở cấm global ${uid}?`)) return;
    const res=await apiRequest(`/api/blacklist/global`,'POST',{action:'remove', user_id:uid});
    if(res.ok){ showToast(res.message,'success'); const gid=document.getElementById('drawerGuildId').value; if(gid) loadBlacklist(gid); } else showToast(res.error||'Lỗi','error');
}
async function loadGlobalOnly(){
    const res=await apiRequest(`/api/blacklist/global`);
    if(res.ok) renderGlobalBlacklist(res.global_blacklist||[]);
}
async function loadLeverConfig(guildId){
    const res = await apiRequest(`/api/guilds/${guildId}/level-config`);
    if(!res.ok) return;
    const cfg=res.config||{}; const cnt=res.counts||{}; const topL=res.top_level||[]; const topR=res.top_rich||[];
    const setSw=(id,v)=>{const el=document.getElementById(id); if(el) el.classList.toggle('on', !!v);};
    setSw('leverExp', cfg.exp_enabled); setSw('leverVoiceExp', cfg.voice_exp); setSw('leverAnnounce', cfg.level_up_announce);
    if(document.getElementById('leverAnnounceChannel')) document.getElementById('leverAnnounceChannel').value=cfg.announce_channel||'';
    if(document.getElementById('leverCountLevel')) document.getElementById('leverCountLevel').innerText=cnt.level||0;
    if(document.getElementById('leverCountEcon')) document.getElementById('leverCountEcon').innerText=cnt.economy||0;
    const tl=document.getElementById('leverTopLevel'); if(tl){
        tl.innerHTML = topL.length? topL.map((r,i)=>{
            const id = r.id ?? r[0] ?? '—';
            const name = r.name ?? r.id ?? r[0] ?? id;
            const avatar = r.avatar ?? 'https://cdn.discordapp.com/embed/avatars/0.png';
            const xp = r.xp ?? r[1] ?? 0;
            const level = r.level ?? r[2] ?? 0;
            return `<div style="display:flex;justify-content:space-between;align-items:center;padding:8px 10px;background:var(--bg-card);border:1px solid var(--border-subtle);border-radius:10px"><span style="display:flex;gap:8px;align-items:center"><img src="${avatar}" style="width:28px;height:28px;border-radius:50%;object-fit:cover" onerror="this.src='https://cdn.discordapp.com/embed/avatars/0.png'"><span>${name}</span><span style="color:var(--text-dim);font-size:.75rem">${id!==name? id:''}</span></span><span>${xp} EXP • Lv${level}</span></div>`;
        }).join('') : '<div style="color:var(--text-dim)">Chưa có dữ liệu</div>';
    }
    const tr=document.getElementById('leverTopRich'); if(tr){
        tr.innerHTML = topR.length? topR.map((r,i)=>{
            const name = r.name ?? r.id ?? r[0] ?? '—';
            const avatar = r.avatar ?? 'https://cdn.discordapp.com/embed/avatars/0.png';
            const coins = r.coins ?? r[1] ?? 0;
            return `<div style="display:flex;justify-content:space-between;align-items:center;padding:8px 10px;background:var(--bg-card);border:1px solid var(--border-subtle);border-radius:10px"><span style="display:flex;gap:8px;align-items:center"><img src="${avatar}" style="width:28px;height:28px;border-radius:50%;object-fit:cover" onerror="this.src='https://cdn.discordapp.com/embed/avatars/0.png'"><span>${name}</span></span><span>${coins} 🪙</span></div>`;
        }).join('') : '<div style="color:var(--text-dim)">Chưa có dữ liệu</div>';
    }
}
async function saveLeverConfig(){
    const gid=document.getElementById('drawerGuildId').value;
    const body={exp_enabled: document.getElementById('leverExp')?.classList.contains('on'), voice_exp: document.getElementById('leverVoiceExp')?.classList.contains('on'), level_up_announce: document.getElementById('leverAnnounce')?.classList.contains('on'), announce_channel: document.getElementById('leverAnnounceChannel')?.value||null};
    const res=await apiRequest(`/api/guilds/${gid}/level-config`,'POST',body);
    if(res.ok) showToast('Đã lưu Level & Economy','success'); else showToast(res.error||'Lỗi','error');
}
function openSendMessageFromDrawer() {
    document.getElementById('sendMsgModal').classList.add('active');
}
async function sendAnnounceFromDrawer() {
    const channelId = document.getElementById('announceChannel').value;
    const content = document.getElementById('announceText').value.trim();
    if (!channelId || !content) return showToast('Chọn kênh và nhập nội dung', 'warning');
    const res = await apiRequest('/api/channel/send', 'POST', { channel_id: channelId, content });
    if (res.ok) { showToast('Đã gửi thông báo!', 'success'); document.getElementById('announceText').value = ''; }
    else showToast(res.error || 'Lỗi', 'error');
}


async function loadModCommands(guildId) {
    const box = document.getElementById('modCommandsList');
    if (!box) return;
    box.innerHTML = '<div style="color:var(--text-muted)">Đang tải...</div>';
    const res = await apiRequest(`/api/mod/commands?guild_id=${guildId}`);
    if (!res.ok) { box.innerHTML = `<div style="color:var(--accent-red)">${res.error || 'Lỗi tải'}</div>`; return; }
    
    const cats = res.categories || {};
    const cmds = res.commands || [];
    let html = '';
    
    const order = ['member', 'voice', 'utility'];
    for (const cat of order) {
        const catInfo = cats[cat] || { label: cat };
        const catCmds = cmds.filter(c => c.category === cat);
        if (catCmds.length === 0) continue;
        html += `<div style="margin:12px 0 8px;font-weight:700;color:${catInfo.color || 'var(--text-main)'}">${catInfo.label}</div>`;
        for (const c of catCmds) {
            html += `<div style="display:flex;justify-content:space-between;align-items:center;padding:10px 12px;background:rgba(255,255,255,0.03);border:1px solid var(--border-subtle);border-radius:10px;margin-bottom:8px">
                <div>
                    <strong>${c.name}</strong> <span style="color:var(--text-dim);font-size:.8rem">${c.slash} ${c.prefix !== '—' ? '• ' + c.prefix : ''}</span>
                    <div style="font-size:.82rem;color:var(--text-muted)">${c.desc} <span style="font-size:.7rem;color:var(--text-dim)">(${c.perm})</span></div>
                </div>
                <div class="switch ${c.enabled ? 'on' : ''}" onclick="toggleModCmd('${guildId}','${c.id}', this)"></div>
            </div>`;
        }
    }
    html += `<div style="margin-top:10px;font-size:.78rem;color:var(--text-dim)">Đã loại trừ lệnh MC (minecraft.py • is_mc_admin) khỏi web.</div>`;
    box.innerHTML = html;
}
async function toggleModCmd(guildId, cmdId, el) {
    const enabled = !el.classList.contains('on');
    
    el.classList.toggle('on');
    const res = await apiRequest('/api/mod/commands', 'POST', { guild_id: guildId, cmd_id: cmdId, enabled });
    if (res.ok) showToast(`${enabled ? 'Bật' : 'Tắt'} ${cmdId} thành công`, 'success');
    else { el.classList.toggle('on'); showToast(res.error || 'Lỗi', 'error'); }
}
function onModActionChange() {
    const act = document.getElementById('modQuickAction').value;
    document.getElementById('modMinutesGroup').style.display = act === 'mute' ? 'block' : 'none';
    document.getElementById('modClearGroup').style.display = act === 'clear' ? 'block' : 'none';
}
let _modMembersCache=[], _selectedMemberIds=new Set();
async function loadModMembers(guildId){
    const listEl=document.getElementById('modMemberList'); const cnt=document.getElementById('modMemberCount');
    if(!listEl) return;
    listEl.innerHTML='<div style="padding:12px;text-align:center;color:var(--text-muted)">Đang tải thành viên...</div>';
    const res=await apiRequest(`/api/guilds/${guildId}/members`);
    if(!res.ok){ listEl.innerHTML=`<div style="padding:12px;text-align:center;color:var(--accent-red)">${res.error||'Lỗi tải'}</div>`; if(cnt) cnt.textContent='0'; return; }
    _modMembersCache=res.members||[];
    if(cnt) cnt.textContent=_modMembersCache.length;
    _selectedMemberIds.clear(); document.getElementById('modTargetId').value=''; updateSelectedInfo();
    renderModMembers(_modMembersCache);
}
function renderModMembers(list){
    const listEl=document.getElementById('modMemberList');
    if(!list.length){ listEl.innerHTML='<div style="padding:12px;text-align:center;color:var(--text-dim)">Không có thành viên</div>'; return; }
    listEl.innerHTML=list.map(m=>{
        const sel=_selectedMemberIds.has(m.id);
        return `
        <div class="member-option ${sel?'selected':''}" data-id="${m.id}" onclick="selectModMember('${m.id}', event)" style="display:flex;gap:10px;align-items:center;padding:8px 10px;border-radius:10px;cursor:pointer;transition:.15s;background:${sel?'rgba(255,121,198,0.12)':'transparent'};border:1px solid ${sel?'var(--sakura-pink)':'transparent'}">
            <input type="checkbox" ${sel?'checked':''} onclick="event.stopPropagation(); selectModMember('${m.id}', event)" style="width:16px;height:16px;accent-color:var(--sakura-pink)">
            <img src="${m.avatar||'https://cdn.discordapp.com/embed/avatars/0.png'}" style="width:32px;height:32px;border-radius:50%;object-fit:cover;border:1px solid var(--border-subtle);flex-shrink:0" onerror="this.src='https://cdn.discordapp.com/embed/avatars/0.png'">
            <div style="flex:1;min-width:0">
                <div style="font-weight:600;font-size:.9rem;white-space:nowrap;overflow:hidden;text-overflow:ellipsis">${m.name} ${m.bot?'<span style="font-size:.7rem;background:var(--accent-purple);color:#fff;padding:1px 5px;border-radius:5px;margin-left:4px">BOT</span>':''}</div>
                <div style="font-size:.78rem;color:var(--text-dim);white-space:nowrap;overflow:hidden;text-overflow:ellipsis">@${m.username} • ${m.id}</div>
            </div>
            <span style="color:var(--sakura-pink);font-size:1rem;opacity:${sel?1:0}">✓</span>
        </div>`;
    }).join('');
}
function filterModMembers2(){
    const q=(document.getElementById('modMemberSearch2')?.value||'').toLowerCase();
    if(!q) return renderModMembers(_modMembersCache);
    const filtered=_modMembersCache.filter(m=> m.name.toLowerCase().includes(q) || m.username.toLowerCase().includes(q) || m.id.includes(q));
    renderModMembers(filtered);
}
function selectModMember(id, e){
    if(e) e.preventDefault();
    if(_selectedMemberIds.has(id)) _selectedMemberIds.delete(id); else _selectedMemberIds.add(id);
    document.getElementById('modTargetId').value=Array.from(_selectedMemberIds).join(',');
    document.getElementById('modTargetIdCustom').value='';
    updateSelectedInfo();
    
    const q=(document.getElementById('modMemberSearch2')?.value||'').toLowerCase();
    const list=q? _modMembersCache.filter(x=> x.name.toLowerCase().includes(q)||x.username.toLowerCase().includes(q)||x.id.includes(q)) : _modMembersCache;
    renderModMembers(list);
}
function updateSelectedInfo(){
    const info=document.getElementById('modSelectedInfo');
    if(!info) return;
    if(_selectedMemberIds.size===0){ info.style.display='none'; return; }
    const names=Array.from(_selectedMemberIds).map(id=>{ const m=_modMembersCache.find(x=>x.id===id); return m? m.name : id; });
    info.style.display='block';
    info.innerHTML=`Đã chọn <strong>${_selectedMemberIds.size}</strong>: ${names.slice(0,3).join(', ')}${names.length>3?' +'+(names.length-3):''} <a href="#" onclick="_selectedMemberIds.clear();document.getElementById('modTargetId').value='';updateSelectedInfo();renderModMembers(_modMembersCache);return false;" style="color:var(--sakura-pink);margin-left:8px">Xóa chọn</a> <span style="margin-left:8px;cursor:pointer" onclick="selectAllModMembers()">Chọn tất cả (lọc)</span>`;
}
function selectAllModMembers(){
    const q=(document.getElementById('modMemberSearch2')?.value||'').toLowerCase();
    const list=q? _modMembersCache.filter(m=> m.name.toLowerCase().includes(q)||m.username.toLowerCase().includes(q)||m.id.includes(q)) : _modMembersCache;
    list.forEach(m=> _selectedMemberIds.add(m.id));
    document.getElementById('modTargetId').value=Array.from(_selectedMemberIds).join(',');
    updateSelectedInfo(); renderModMembers(list);
}

function filterModMembers(){ filterModMembers2(); }
async function executeModAction() {
    const guildId = document.getElementById('drawerGuildId').value;
    const action = document.getElementById('modQuickAction').value;
    const customRaw = document.getElementById('modTargetIdCustom')?.value.trim();
    const selVal = document.getElementById('modTargetId')?.value.trim();
    const raw = customRaw || selVal || '';
    
    const ids = raw.split(/[,\s]+/).map(s=>s.trim()).filter(Boolean);
    const targetSingle = ids[0]||'';
    const reason = document.getElementById('modReason').value.trim() || 'Từ Web';
    const minutes = document.getElementById('modMinutes').value;
    const amount = document.getElementById('modAmount').value.trim();
    const channel_id = document.getElementById('modChannelId').value;
    if (action !== 'clear' && !ids.length) return showToast('Chọn 1 hoặc nhiều thành viên', 'warning');
    if (action === 'clear' && !channel_id) return showToast('Chọn kênh để clear', 'warning');
    
    if(ids.length > 1 && action !== 'clear'){
        if(!confirm(`Thực thi ${action} cho ${ids.length} thành viên?`)) return;
        let ok=0, fail=0;
        for(const tid of ids){
            const payload = { guild_id: guildId, action, target_id: tid, reason, minutes: parseInt(minutes) || 10, amount, channel_id };
            const res = await apiRequest('/api/mod/action', 'POST', payload);
            if(res.ok) ok++; else fail++;
        }
        showToast(`Xong: ${ok} thành công, ${fail} lỗi`, fail?'warning':'success');
        return;
    }
    const payload = { guild_id: guildId, action, target_id: targetSingle, reason, minutes: parseInt(minutes) || 10, amount, channel_id };
    const res = await apiRequest('/api/mod/action', 'POST', payload);
    if (res.ok) showToast(res.message || 'Thành công', 'success');
    else showToast(res.error || 'Lỗi', 'error');
}

async function saveGuildSettings() {
    const guildId = document.getElementById('guildModalId').value;
    const prefix = document.getElementById('guildModalPrefix').value;
    const language = document.getElementById('guildModalLang').value;

    const res = await apiRequest(`/api/guilds/${guildId}/settings`, 'POST', { prefix, language });
    if (res.ok) {
        showToast('Đã lưu cài đặt server!', 'success');
        document.getElementById('guildSettingsModal').classList.remove('active');
        loadGuilds();
    } else {
        showToast(res.error || 'Lỗi lưu cài đặt', 'error');
    }
}

function openSendMessageModal(guildId, guildName) {
    openGuildModal(guildId).then(() => {
        document.getElementById('sendMsgModal').classList.add('active');
    });
}

async function sendChannelMessage() {
    const channelId = document.getElementById('msgChannelSelect').value;
    const content = document.getElementById('msgContent').value;
    const embedTitle = document.getElementById('msgEmbedTitle')?.value || '';
    const embedDesc = document.getElementById('msgEmbedDesc')?.value || '';
    const embedColor = document.getElementById('msgEmbedColor')?.value || '#ff79c6';
    const embedImage = document.getElementById('msgEmbedImage')?.value || '';
    const embedThumb = document.getElementById('msgEmbedThumb')?.value || '';
    const embedFooter = document.getElementById('msgEmbedFooter')?.value || '';
    const fileInput = document.getElementById('msgFileInput');
    const file = fileInput?.files?.[0];

    if (!content && !embedTitle && !embedDesc && !file && !embedImage) {
        showToast('Vui lòng nhập nội dung, cấu hình embed hoặc đính kèm tệp!', 'warning');
        return;
    }

    let res;
    if (file) {
        const formData = new FormData();
        formData.append('channel_id', channelId);
        if (content) formData.append('content', content);
        if (embedTitle) formData.append('embed_title', embedTitle);
        if (embedDesc) formData.append('embed_desc', embedDesc);
        if (embedColor) formData.append('embed_color', embedColor);
        if (embedImage) formData.append('embed_image', embedImage);
        if (embedThumb) formData.append('embed_thumbnail', embedThumb);
        if (embedFooter) formData.append('embed_footer', embedFooter);
        formData.append('file', file);

        try {
            const resp = await fetch('/api/channel/send', {
                method: 'POST',
                headers: state.token ? { 'Authorization': `Bearer ${state.token}` } : {},
                body: formData
            });
            res = await resp.json();
        } catch (err) {
            res = { ok: false, error: err.message };
        }
    } else {
        const payload = {
            channel_id: channelId,
            content: content
        };
        if (embedTitle || embedDesc || embedImage || embedThumb || embedFooter) {
            payload.embed = {
                title: embedTitle,
                description: embedDesc,
                color: embedColor,
                image: embedImage,
                thumbnail: embedThumb,
                footer: embedFooter
            };
        }
        res = await apiRequest('/api/channel/send', 'POST', payload);
    }

    if (res.ok) {
        showToast('Đã gửi thông báo đến channel thành công!', 'success');
        document.getElementById('sendMsgModal').classList.remove('active');
        document.getElementById('msgContent').value = '';
        if (document.getElementById('msgEmbedTitle')) document.getElementById('msgEmbedTitle').value = '';
        if (document.getElementById('msgEmbedDesc')) document.getElementById('msgEmbedDesc').value = '';
        if (document.getElementById('msgEmbedImage')) document.getElementById('msgEmbedImage').value = '';
        if (document.getElementById('msgEmbedThumb')) document.getElementById('msgEmbedThumb').value = '';
        if (document.getElementById('msgEmbedFooter')) document.getElementById('msgEmbedFooter').value = '';
        if (fileInput) fileInput.value = '';
    } else {
        showToast(res.error || 'Lỗi gửi tin nhắn', 'error');
    }
}


async function triggerBotAction(action, payload = {}) {
    const res = await apiRequest('/api/bot/action', 'POST', { action, ...payload });
    if (res.ok) {
        showToast(res.message, 'success');
    } else {
        showToast(res.error || 'Lỗi thực hiện thao tác', 'error');
    }
}
async function refreshBotConnection() {
    const badge = document.getElementById('botConnBadge');
    const proc = document.getElementById('botProcStatus');
    const disc = document.getElementById('botDiscordStatus');
    const pid = document.getElementById('botPidInfo');
    const detail = document.getElementById('botConnDetail');
    if (badge) badge.innerText = 'Đang kiểm tra...';
    
    const controller = new AbortController();
    const t = setTimeout(() => controller.abort(), 2500);
    let res;
    try {
        const token = state.token || (document.cookie.match(/sakura_token=([^;]+)/) || [])[1] || '';
        const headers = { 'Content-Type': 'application/json' };
        if (token) headers['Authorization'] = 'Bearer ' + token;
        const r = await fetch('/api/bot/connection', { headers, signal: controller.signal });
        clearTimeout(t);
        res = await r.json();
        if (!r.ok) res = { ok: false, error: res.error || 'Lỗi' };
        else res.ok = true;
    } catch (e) {
        clearTimeout(t);
        if (e.name === 'AbortError') {
            if (badge) { badge.innerText = '🔴 Bot tắt'; badge.className = 'badge badge-sakura'; }
            if (proc) proc.innerText = 'Process: OFF';
            if (disc) disc.innerText = 'Discord: chưa kết nối';
            if (detail) detail.innerText = 'Không phản hồi (timeout) - bot chưa chạy';
            return;
        }
        res = await apiRequest('/api/bot/connection');
    }
    if (!res.ok) { if (badge) badge.innerText = '❌ Lỗi'; if (detail) detail.innerText = res.error || 'Unauthorized'; return; }
    const b = res.bot;
    const p = b.process || {};
    if (badge) badge.innerText = p.running ? '🟢 Bot đang chạy' : '🔴 Bot tắt';
    if (badge) badge.className = p.running ? 'badge badge-green' : 'badge badge-sakura';
    if (proc) proc.innerText = `Process: ${p.running ? 'ON (' + p.mode + ')' : 'OFF'}`;
    if (disc) disc.innerText = b.discord ? `Discord: ${b.discord.username} • ${b.discord.guilds} guilds` : 'Discord: chưa kết nối (tách web)';
    if (pid) pid.innerText = `PID: ${p.pid || '—'}`;
    if (detail) detail.innerText = `Mode: ${p.mode} • Web standalone: ${b.web_standalone ? 'có' : 'không'} • Quyền điều khiển: ${b.can_control ? 'admin' : 'không'}`;
}



async function loadBotCommands() {
    const grid = document.getElementById('commandsGrid');
    if (!grid) return;
    grid.innerHTML = `
        <div style="text-align:center; padding:40px; color:var(--text-muted); grid-column:1/-1">
            <div class="spinner" style="margin:0 auto 12px"></div>
            Đang đồng bộ lệnh từ bot...
        </div>`;

    const res = await apiRequest('/api/bot/commands');
    if (!res.ok || !res.commands) {
        grid.innerHTML = `<div style="text-align:center; padding:30px; color:var(--accent-red); grid-column:1/-1">Không thể tải danh sách lệnh (${res.error || 'Lỗi kết nối'})</div>`;
        return;
    }

    state.allCommands = res.commands;
    const badge = document.getElementById('commandsTotalBadge');
    if (badge) badge.textContent = `${res.total || res.commands.length} lệnh`;

    filterCommands();
}

function setCmdCategory(cat) {
    state.activeCmdCategory = cat;
    document.querySelectorAll('#cmdCategoryPills .cmd-pill').forEach(btn => {
        const text = btn.getAttribute('onclick') || '';
        btn.classList.toggle('active', text.includes(`'${cat}'`));
    });
    filterCommands();
}

function filterCommands() {
    const q = (document.getElementById('cmdSearchInput')?.value || '').trim().toLowerCase();
    const cat = state.activeCmdCategory || 'all';

    let filtered = state.allCommands || [];
    if (cat !== 'all') {
        filtered = filtered.filter(c => c.category === cat);
    }
    if (q) {
        filtered = filtered.filter(c => {
            const name = (c.name || '').toLowerCase();
            const syntax = (c.syntax || '').toLowerCase();
            const desc = (c.description || '').toLowerCase();
            const catName = (c.category || '').toLowerCase();
            const aliases = Array.isArray(c.aliases) ? c.aliases.join(' ').toLowerCase() : '';
            return name.includes(q) || syntax.includes(q) || desc.includes(q) || catName.includes(q) || aliases.includes(q);
        });
    }

    renderBotCommands(filtered);
}

function renderBotCommands(commands) {
    const grid = document.getElementById('commandsGrid');
    const emptyEl = document.getElementById('commandsEmpty');
    if (!grid) return;

    if (!commands || commands.length === 0) {
        grid.innerHTML = '';
        if (emptyEl) emptyEl.style.display = 'block';
        return;
    }
    if (emptyEl) emptyEl.style.display = 'none';

    const catBadgeStyles = {
        fishing: { bg: 'rgba(255,107,157,0.18)', color: '#ff6b9d', icon: '🎣' },
        core: { bg: 'rgba(189,147,249,0.18)', color: '#bd93f9', icon: '✨' },
        economy: { bg: 'rgba(255,184,108,0.18)', color: '#ffb86c', icon: '💰' },
        music: { bg: 'rgba(139,233,253,0.18)', color: '#8be9fd', icon: '🎵' },
        moderation: { bg: 'rgba(255,85,85,0.18)', color: '#ff5555', icon: '🛡️' },
        utility: { bg: 'rgba(80,250,123,0.18)', color: '#50fa7b', icon: '⚙️' },
        games: { bg: 'rgba(241,250,140,0.18)', color: '#f1fa8c', icon: '🎮' },
        owner: { bg: 'linear-gradient(135deg, rgba(255,215,0,0.3) 0%, rgba(255,140,0,0.3) 100%)', color: '#ffd700', icon: '👑' }
    };

    grid.innerHTML = commands.map(cmd => {
        const style = catBadgeStyles[cmd.category] || { bg: 'rgba(255,255,255,0.08)', color: '#f8f8f2', icon: '🌸' };
        const isOwnerCmd = cmd.category === 'owner';
        const aliasesHtml = (cmd.aliases && cmd.aliases.length) 
            ? `<div class="cmd-aliases"><b>Bí danh:</b> ${cmd.aliases.map(a => `<code class="cmd-alias-tag">${escapeHtml(a)}</code>`).join(' ')}</div>` 
            : '';
        const exampleHtml = cmd.example 
            ? `<div class="cmd-example"><b>Ví dụ:</b> <code>${escapeHtml(cmd.example)}</code></div>` 
            : '';

        return `
        <div class="cmd-card ${isOwnerCmd ? 'cmd-owner-card' : ''}">
            <div class="cmd-card-header">
                <div class="cmd-name-row">
                    <span class="cmd-icon">${style.icon}</span>
                    <strong class="cmd-name">${escapeHtml(cmd.name)}</strong>
                </div>
                <span class="cmd-cat-badge" style="background:${style.bg}; color:${style.color}">
                    ${escapeHtml((cmd.category || '').toUpperCase())}
                </span>
            </div>
            <div class="cmd-syntax-box" onclick="copyCommandCode('${escapeHtml(cmd.syntax)}', this)" title="Nhấn để sao chép">
                <code>${escapeHtml(cmd.syntax)}</code>
                <button class="cmd-copy-btn" onclick="event.stopPropagation(); copyCommandCode('${escapeHtml(cmd.syntax)}', this)">📋 Chép</button>
            </div>
            <div class="cmd-desc">${escapeHtml(cmd.description)}</div>
            ${aliasesHtml}
            ${exampleHtml}
            <div class="cmd-footer">
                <span class="cmd-perm-badge">🔒 Quyền: ${escapeHtml(cmd.permissions || 'Thành viên')}</span>
            </div>
        </div>
        `;
    }).join('');
}

function copyCommandCode(text, el) {
    if (!text) return;
    navigator.clipboard.writeText(text).then(() => {
        showToast(`Đã sao chép: ${text}`, 'success');
        const btn = el && el.tagName === 'BUTTON' ? el : (el ? el.querySelector('.cmd-copy-btn') : null);
        if (btn) {
            const old = btn.textContent;
            btn.textContent = '✓ Đã chép';
            btn.style.color = '#50fa7b';
            setTimeout(() => {
                btn.textContent = old;
                btn.style.color = '';
            }, 1800);
        }
    }).catch(() => {
        showToast(`Lệnh: ${text}`, 'info');
    });
}


async function loadAntiSettings() {
    const res = await apiRequest('/api/anti/settings');
    if (!res.ok) return;

    state.antiSettings = res;
    state.globalAntiEnabled = res.global_enabled !== false;

    const badge = document.getElementById('globalAntiBadge');
    const btn = document.getElementById('btnToggleGlobalAnti');
    if (badge && btn) {
        if (state.globalAntiEnabled) {
            badge.className = 'badge badge-green';
            badge.innerText = 'Đang Bật';
            btn.className = 'btn btn-secondary';
            btn.innerText = '🛑 Tắt Toàn Cục';
        } else {
            badge.className = 'badge badge-red';
            badge.innerText = 'Đã Tắt';
            btn.className = 'btn btn-primary';
            btn.innerText = '✅ Bật Toàn Cục';
        }
    }

    
    const wordsContainer = document.getElementById('forbiddenWordsList');
    if (wordsContainer && res.forbidden_words) {
        wordsContainer.innerHTML = res.forbidden_words.map(w => `
            <span class="badge badge-sakura" style="font-size: 0.85rem; padding: 6px 12px; display: inline-flex; align-items: center; gap: 8px;">
                ${w}
                <span style="cursor: pointer; font-weight: bold;" onclick="removeForbiddenWord('${w}')">×</span>
            </span>
        `).join('');
    }
}

async function toggleGlobalAnti() {
    const newStatus = !state.globalAntiEnabled;
    const res = await apiRequest('/api/anti/settings', 'POST', {
        type: 'global',
        data: { enabled: newStatus }
    });
    if (res.ok) {
        showToast(res.message || `Đã ${newStatus ? 'bật' : 'tắt'} toàn cục hệ thống Anti!`, 'success');
        loadAntiSettings();
    } else {
        showToast(res.error || 'Lỗi cập nhật trạng thái Anti', 'error');
    }
}

async function addForbiddenWord() {
    const input = document.getElementById('newForbiddenWord');
    const word = input ? input.value.trim() : '';
    if (!word) return;

    const currentWords = state.antiSettings.forbidden_words || [];
    if (!currentWords.includes(word)) {
        currentWords.push(word);
        const res = await apiRequest('/api/anti/settings', 'POST', {
            type: 'forbidden_words',
            data: currentWords
        });
        if (res.ok) {
            showToast(`Đã thêm từ cấm '${word}'!`, 'success');
            input.value = '';
            loadAntiSettings();
        }
    }
}

async function removeForbiddenWord(word) {
    let currentWords = state.antiSettings.forbidden_words || [];
    currentWords = currentWords.filter(w => w !== word);
    const res = await apiRequest('/api/anti/settings', 'POST', {
        type: 'forbidden_words',
        data: currentWords
    });
    if (res.ok) {
        showToast(`Đã xóa từ cấm '${word}'!`, 'info');
        loadAntiSettings();
    }
}


function initAddEconomyForm() {
    const sel = document.getElementById('econGuildSelect');
    if (!sel) return;
    sel.innerHTML = '<option value="0">🌍 Tất Cả Server / Toàn Cục</option>' + 
        (state.guilds || []).map(g => `<option value="${g.id}">🏰 ${g.name} (${g.id})</option>`).join('');
}

async function submitEconomyAdjustment() {
    const userId = document.getElementById('econUserId').value.trim();
    const guildId = document.getElementById('econGuildSelect').value;
    const currency = document.getElementById('econCurrencySelect').value;
    const action = document.getElementById('econActionSelect').value;
    const amountVal = document.getElementById('econAmount').value.trim();

    if (!userId) {
        showToast('Vui lòng nhập Discord User ID!', 'warning');
        return;
    }
    const amount = parseInt(amountVal);
    if (isNaN(amount) || amount < 0) {
        showToast('Vui lòng nhập số lượng hợp lệ (>= 0)!', 'warning');
        return;
    }

    const res = await apiRequest('/api/economy/adjust', 'POST', {
        user_id: userId,
        guild_id: guildId,
        currency: currency,
        action: action,
        amount: amount
    });

    if (res.ok) {
        showToast(res.message || 'Cấp phát kinh tế thành công!', 'success');
        document.getElementById('econAmount').value = '';
        if (state.activeTab === 'levels') loadLevels();
    } else {
        showToast(res.error || 'Lỗi cấp phát kinh tế', 'error');
    }
}


async function loadLevels() {
    const tbody = document.getElementById('levelsTableBody');
    if (!tbody) return;
    tbody.innerHTML = '<tr><td colspan="7" style="text-align: center;">Đang tải dữ liệu cấp độ...</td></tr>';

    const res = await apiRequest('/api/levels');
    if (!res.ok || !res.users) {
        tbody.innerHTML = '<tr><td colspan="7" style="text-align: center; color: var(--accent-red);">Lỗi tải bảng xếp hạng</td></tr>';
        return;
    }

    state.levels = res.users;
    renderLevelsTable(res.users);
}

function renderLevelsTable(users) {
    const tbody = document.getElementById('levelsTableBody');
    if (!tbody) return;

    const isEffectiveAdmin = (state.isAdmin || state.isRealAdmin) && !state.previewAsUser;
    const actionTh = document.getElementById('levelsActionTh');
    if (actionTh) actionTh.style.display = isEffectiveAdmin ? '' : 'none';

    if (users.length === 0) {
        tbody.innerHTML = `<tr><td colspan="${isEffectiveAdmin ? 7 : 6}" style="text-align: center; color: var(--text-dim);">Chưa có dữ liệu người dùng</td></tr>`;
        return;
    }

    tbody.innerHTML = users.map((u, idx) => `
        <tr>
            <td>
                <span class="badge ${idx < 3 ? 'badge-sakura' : ''}" style="font-weight: 700;">#${idx + 1}</span>
            </td>
            <td><strong>${u.user_id}</strong></td>
            <td>
                <div style="display:flex;align-items:center;gap:8px;">
                    ${u.avatar ? `<img src="${u.avatar}" style="width:26px;height:26px;border-radius:50%;object-fit:cover;" onerror="this.style.display='none'">` : '<span style="font-size:1.1rem">👤</span>'}
                    <span>${escapeHtml(u.username || 'User')}</span>
                </div>
            </td>
            <td><span class="badge badge-green">Lv. ${u.level}</span></td>
            <td>${(u.xp || 0).toLocaleString()} XP</td>
            <td>🪙 ${(u.coins || 0).toLocaleString()} Coin<br><small style="color:var(--text-subtle)">💠 ${(u.xu || 0).toLocaleString()} Xu</small></td>
            ${isEffectiveAdmin ? `
            <td style="text-align: right;">
                <button class="btn btn-secondary btn-sm" onclick="openEditLevelModal('${u.user_id}', ${u.level}, ${u.xp})">✏️ Sửa Level</button>
            </td>` : ''}
        </tr>
    `).join('');
}

function searchLevels() {
    const query = document.getElementById('levelSearchInput').value.trim().toLowerCase();
    if (!query) {
        renderLevelsTable(state.levels);
        return;
    }
    const filtered = state.levels.filter(u => 
        (u.user_id && u.user_id.toLowerCase().includes(query)) ||
        (u.username && u.username.toLowerCase().includes(query))
    );
    renderLevelsTable(filtered);
}

function openEditLevelModal(userId, level, xp) {
    document.getElementById('editLevelUserId').value = userId;
    document.getElementById('editLevelNum').value = level;
    document.getElementById('editLevelXp').value = xp;
    document.getElementById('editLevelModal').classList.add('active');
}

async function saveUserLevel() {
    const userId = document.getElementById('editLevelUserId').value;
    const level = parseInt(document.getElementById('editLevelNum').value) || 1;
    const xp = parseInt(document.getElementById('editLevelXp').value) || 0;

    const res = await apiRequest('/api/levels/update', 'POST', {
        user_id: userId,
        level,
        xp
    });

    if (res.ok) {
        showToast('Cập nhật Level & XP thành công!', 'success');
        document.getElementById('editLevelModal').classList.remove('active');
        loadLevels();
    } else {
        showToast(res.error || 'Lỗi cập nhật', 'error');
    }
}


state.fishingLbType = 'global';

function setFishingLbType(type) {
    state.fishingLbType = type;
    const btnG = document.getElementById('btnFishLbGlobal');
    const btnL = document.getElementById('btnFishLbLocal');
    const selG = document.getElementById('fishLbGuildSelect');

    if (type === 'global') {
        if (btnG) btnG.classList.add('active');
        if (btnL) btnL.classList.remove('active');
        if (selG) selG.style.display = 'none';
    } else {
        if (btnG) btnG.classList.remove('active');
        if (btnL) btnL.classList.add('active');
        if (selG) {
            selG.style.display = 'inline-block';
            if (selG.children.length === 0 && state.guilds) {
                selG.innerHTML = state.guilds.map(g => `<option value="${g.id}">${g.name}</option>`).join('');
            }
        }
    }
    loadFishingLeaderboard();
}

async function loadFishingLeaderboard() {
    const tbody = document.getElementById('fishingLbTableBody');
    if (!tbody) return;
    tbody.innerHTML = '<tr><td colspan="7" style="text-align: center;">Đang tải dữ liệu cần thủ...</td></tr>';

    const type = state.fishingLbType || 'global';
    let url = `/api/fishing/leaderboard?type=${type}`;
    if (type === 'local') {
        const selG = document.getElementById('fishLbGuildSelect');
        const gid = selG?.value || (state.guilds?.[0]?.id || '');
        if (gid) url += `&guild_id=${gid}`;
    }

    const res = await apiRequest(url);
    if (!res.ok || !res.users) {
        tbody.innerHTML = '<tr><td colspan="7" style="text-align: center; color: var(--accent-red);">Không thể tải BXH câu cá</td></tr>';
        return;
    }

    if (res.users.length === 0) {
        tbody.innerHTML = '<tr><td colspan="7" style="text-align: center; color: var(--text-dim);">Chưa có thành tích câu cá trong khu vực này.</td></tr>';
        return;
    }

    tbody.innerHTML = res.users.map((u, idx) => {
        const starBadge = u.stars > 0 ? `<span class="badge" style="background: linear-gradient(135deg, #f59e0b, #ef4444); color: #fff; font-weight: bold; margin-left: 4px; box-shadow: 0 0 8px rgba(245, 158, 11, 0.5);">⭐x${u.stars}</span>` : '';
        const refineBadge = u.refine > 0 ? `<span class="badge" style="background: ${u.refine >= 100 ? '#ec4899' : '#3b82f6'}; color: #fff; font-weight: bold; margin-left: 4px;">+${u.refine}</span>` : '';
        const enchantBadge = u.enchant_count > 0 ? `<span class="badge" style="background: #8b5cf6; color: #fff; margin-left: 4px;" title="Đã enchant ${u.enchant_count} dòng thuộc tính">✨ ${u.enchant_count}D</span>` : '';
        const farmBadge = u.farm_crops > 0 ? `<span class="badge" style="background: #10b981; color: #fff; margin-left: 4px;" title="Nông trại: ${u.farm_crops} nông sản">🌾 ${u.farm_crops}</span>` : '';

        return `
        <tr>
            <td>
                <span class="badge ${idx < 3 ? 'badge-sakura' : ''}" style="font-weight: 700;">#${idx + 1}</span>
            </td>
            <td>
                <div style="display:flex;align-items:center;gap:8px;">
                    ${u.avatar ? `<img src="${u.avatar}" style="width:28px;height:28px;border-radius:50%;object-fit:cover;" onerror="this.style.display='none'">` : '<span style="font-size:1.2rem">🎣</span>'}
                    <div>
                        <strong>${u.username}</strong>
                        ${starBadge}
                    </div>
                </div>
            </td>
            <td><code>${u.user_id}</code></td>
            <td><strong>${u.total_caught.toLocaleString()}</strong> con</td>
            <td>${u.biggest_weight > 0 ? `⚖️ <strong>${u.biggest_weight}kg</strong> (${u.biggest_name})` : '—'}</td>
            <td>💰 ${(u.total_earned || 0).toLocaleString()} Coin</td>
            <td>
                <div style="display:flex;align-items:center;flex-wrap:wrap;gap:4px;">
                    <span class="badge badge-green">${u.rod_name || u.equipped_rod}</span>
                    ${refineBadge}
                    ${enchantBadge}
                    ${farmBadge}
                </div>
            </td>
        </tr>
    `;
    }).join('');
}


function initGiveawaysTab() {
    const sel = document.getElementById('gwGuildSelect');
    if (!sel) return;
    if (state.guilds && state.guilds.length > 0) {
        sel.innerHTML = state.guilds.map(g => `<option value="${g.id}">🏰 ${g.name}</option>`).join('');
        loadGuildGiveaways();
    } else {
        loadGuilds().then(() => {
            if (sel && state.guilds) {
                sel.innerHTML = state.guilds.map(g => `<option value="${g.id}">🏰 ${g.name}</option>`).join('');
                loadGuildGiveaways();
            }
        });
    }
}

async function loadGuildGiveaways() {
    const sel = document.getElementById('gwGuildSelect');
    const guildId = sel ? sel.value : null;
    const tbody = document.getElementById('giveawaysTableBody');
    if (!tbody || !guildId) return;

    tbody.innerHTML = '<tr><td colspan="7" style="text-align: center;">Đang tải danh sách Giveaway...</td></tr>';
    const res = await apiRequest(`/api/guilds/${guildId}/giveaways`);
    if (!res.ok || !res.giveaways) {
        tbody.innerHTML = `<tr><td colspan="7" style="text-align: center; color: var(--accent-red);">${res.error || 'Lỗi tải danh sách giveaway'}</td></tr>`;
        return;
    }

    if (res.giveaways.length === 0) {
        tbody.innerHTML = '<tr><td colspan="7" style="text-align: center; color: var(--text-dim);">Chưa có giveaway nào được tổ chức trên server này.</td></tr>';
        return;
    }

    tbody.innerHTML = res.giveaways.map(gw => {
        const isRunning = gw.status === 'running';
        const endDate = new Date(gw.end_time * 1000).toLocaleString('vi-VN');
        return `
        <tr>
            <td><code>${gw.message_id}</code></td>
            <td><strong>🎁 ${gw.prize}</strong></td>
            <td>${gw.winners_count} người</td>
            <td>👥 ${gw.participants_count} vé</td>
            <td><span class="badge ${isRunning ? 'badge-green' : 'badge-sakura'}">${isRunning ? 'Đang diễn ra' : 'Đã kết thúc'}</span></td>
            <td>${endDate}</td>
            <td style="text-align: right;">
                ${isRunning ? `<button class="btn btn-secondary btn-sm" onclick="endGiveaway('${guildId}', '${gw.message_id}')" style="margin-right:6px">⏹️ Kết thúc sớm</button>` : ''}
                <button class="btn btn-danger btn-sm" onclick="deleteGiveaway('${guildId}', '${gw.message_id}')">🗑️ Xóa</button>
            </td>
        </tr>
        `;
    }).join('');
}

async function openCreateGiveawayModal() {
    const selG = document.getElementById('gwGuildSelect');
    const guildId = selG ? selG.value : null;
    if (!guildId) {
        showToast('Vui lòng chọn server trước!', 'warning');
        return;
    }

    const chSel = document.getElementById('gwChannelSelect');
    if (chSel) {
        chSel.innerHTML = '<option value="">Đang tải danh sách kênh...</option>';
        const gRes = await apiRequest(`/api/guilds/${guildId}`);
        if (gRes.ok && gRes.channels) {
            chSel.innerHTML = gRes.channels
                .filter(c => c.type === 'text')
                .map(c => `<option value="${c.id}"># ${c.name}</option>`).join('');
        }
    }
    document.getElementById('createGiveawayModal').classList.add('active');
}

async function submitCreateGiveaway() {
    const selG = document.getElementById('gwGuildSelect');
    const guildId = selG ? selG.value : null;
    const channelId = document.getElementById('gwChannelSelect').value;
    const prize = document.getElementById('gwPrize').value.trim();
    const winners = parseInt(document.getElementById('gwWinners').value) || 1;
    const duration = parseInt(document.getElementById('gwDuration').value) || 60;

    if (!channelId || !prize) {
        showToast('Vui lòng chọn kênh và nhập tên phần thưởng!', 'warning');
        return;
    }

    const res = await apiRequest(`/api/guilds/${guildId}/giveaways/create`, 'POST', {
        channel_id: channelId,
        prize: prize,
        winners_count: winners,
        duration_minutes: duration
    });

    if (res.ok) {
        showToast(res.message || 'Khởi tạo giveaway thành công!', 'success');
        document.getElementById('createGiveawayModal').classList.remove('active');
        document.getElementById('gwPrize').value = '';
        loadGuildGiveaways();
    } else {
        showToast(res.error || 'Lỗi khởi tạo giveaway', 'error');
    }
}

async function endGiveaway(guildId, msgId) {
    if (!confirm('Bạn có chắc chắn muốn kết thúc sớm giveaway này và quay thưởng ngay?')) return;
    const res = await apiRequest(`/api/guilds/${guildId}/giveaways/${msgId}/end`, 'POST');
    if (res.ok) {
        showToast(res.message || 'Đã kết thúc giveaway thành công!', 'success');
        loadGuildGiveaways();
    } else {
        showToast(res.error || 'Lỗi khi kết thúc giveaway', 'error');
    }
}

async function deleteGiveaway(guildId, msgId) {
    if (!confirm('Bạn có chắc chắn muốn xóa dữ liệu giveaway này không?')) return;
    const res = await apiRequest(`/api/guilds/${guildId}/giveaways/${msgId}`, 'DELETE');
    if (res.ok) {
        showToast(res.message || 'Đã xóa giveaway thành công!', 'success');
        loadGuildGiveaways();
    } else {
        showToast(res.error || 'Lỗi khi xóa giveaway', 'error');
    }
}


async function loadSystemSettings() {
    await loadConfigSettings();
    await loadRawConfigFile();
    await loadVoteToggleStatus();
}

async function loadVoteToggleStatus() {
    try {
        const res = await apiRequest('/api/vote/toggle-status');
        const badge = document.getElementById('voteStatusBadge');
        const desc = document.getElementById('voteStatusDesc');
        const btn = document.getElementById('btnToggleVote');
        if (res && res.ok) {
            if (res.enabled) {
                if (badge) { badge.textContent = '🟢 ĐANG BẬT'; badge.className = 'badge badge-green'; }
                if (desc) desc.textContent = 'Người dùng thông thường cần vote trên Top.gg để mở khóa các lệnh VIP trong 12h.';
                if (btn) btn.textContent = '🔴 Tắt Yêu Cầu Vote';
            } else {
                if (badge) { badge.textContent = '🔴 ĐANG TẮT (Tạm tắt do bot chưa duyệt)'; badge.className = 'badge badge-yellow'; }
                if (desc) desc.textContent = 'Mọi người dùng đều có thể sử dụng các lệnh (/math, /translate, /music volume, /xemboi) tự do không cần vote.';
                if (btn) btn.textContent = '🟢 Bật Yêu Cầu Vote';
            }
        }
    } catch(e) {}
}

async function toggleVoteSystem() {
    try {
        const res = await apiRequest('/api/vote/toggle', 'POST', {});
        if (res && res.ok) {
            showToast(res.message || 'Đã thay đổi trạng thái yêu cầu vote!', 'success');
            loadVoteToggleStatus();
        } else {
            showToast((res && res.error) || 'Lỗi khi thay đổi trạng thái', 'error');
        }
    } catch(e) {
        showToast('Lỗi kết nối máy chủ', 'error');
    }
}

async function loadConfigSettings() {
    const res = await apiRequest('/api/config');
    if (!res.ok || !res.config) return;

    const c = res.config;
    if (document.getElementById('cfgDiscordToken')) document.getElementById('cfgDiscordToken').value = c.TOKEN || '';
    if (document.getElementById('cfgPrefix')) document.getElementById('cfgPrefix').value = c.PREFIX || 's!';
    if (document.getElementById('cfgOwnerId')) document.getElementById('cfgOwnerId').value = c.OWNER_ID || '';
    if (document.getElementById('cfgLogChannel')) document.getElementById('cfgLogChannel').value = c.LOG_CHANNEL_ID || '';
    if (document.getElementById('cfgAdminRoles')) {
        const roles = Array.isArray(c.ADMIN_ROLE_IDS) ? c.ADMIN_ROLE_IDS.join(', ') : (c.ADMIN_ROLE_IDS || '');
        document.getElementById('cfgAdminRoles').value = roles;
    }
    if (document.getElementById('cfgZaloPhone')) document.getElementById('cfgZaloPhone').value = c.ZALO_PHONE || '';
    if (document.getElementById('cfgOwnerTag')) document.getElementById('cfgOwnerTag').value = c.OWNER_DISCORD_TAG || '';
    if (document.getElementById('cfgWebPort')) document.getElementById('cfgWebPort').value = c.WEB_PORT || 10272;
    if (document.getElementById('cfgWebPassword')) document.getElementById('cfgWebPassword').value = c.WEB_PASSWORD || '';
    if (document.getElementById('cfgClientId')) document.getElementById('cfgClientId').value = c.DISCORD_CLIENT_ID || '';
    if (document.getElementById('cfgClientSecret')) document.getElementById('cfgClientSecret').value = c.DISCORD_CLIENT_SECRET || '';
    if (document.getElementById('cfgRedirectUri')) document.getElementById('cfgRedirectUri').value = c.DISCORD_REDIRECT_URI || '';

    
    if (document.getElementById('cfgAiModel')) document.getElementById('cfgAiModel').value = c.AI_MODEL || 'sensenova/sensenova-6.8-flash-lite';
    if (document.getElementById('cfgGeminiKey')) document.getElementById('cfgGeminiKey').value = c.GEMINI_API_KEY || '';
    if (document.getElementById('cfgGroqKey')) document.getElementById('cfgGroqKey').value = c.GROQ_API_KEY || '';
    if (document.getElementById('cfgOpenAIKey')) document.getElementById('cfgOpenAIKey').value = c.OPENAI_API_KEY || '';
    if (document.getElementById('cfgXkiroKey')) document.getElementById('cfgXkiroKey').value = c.XKIRO_API_KEY || '';
    if (document.getElementById('cfgPkmcKey')) document.getElementById('cfgPkmcKey').value = c.PKMC_API_KEY || '';

    
    if (document.getElementById('cfgLavalinkHost')) document.getElementById('cfgLavalinkHost').value = c.LAVALINK_HOST || '';
    if (document.getElementById('cfgLavalinkPort')) document.getElementById('cfgLavalinkPort').value = c.LAVALINK_PORT || 2334;
    if (document.getElementById('cfgLavalinkPassword')) document.getElementById('cfgLavalinkPassword').value = c.LAVALINK_PASSWORD || '';
    if (document.getElementById('cfgFalixKey')) document.getElementById('cfgFalixKey').value = c.FALIX_API_KEY || '';
    if (document.getElementById('cfgTokenDiemDanh')) document.getElementById('cfgTokenDiemDanh').value = c.TOKEN_DIEM_DANH || '';
    if (document.getElementById('cfgMapDiemDanhId')) document.getElementById('cfgMapDiemDanhId').value = c.MAP_DIEM_DANH_ID || '';
}

async function saveSystemConfig() {
    const payload = {
        TOKEN: document.getElementById('cfgDiscordToken')?.value || '',
        PREFIX: document.getElementById('cfgPrefix')?.value || 's!',
        OWNER_ID: document.getElementById('cfgOwnerId')?.value || '',
        LOG_CHANNEL_ID: document.getElementById('cfgLogChannel')?.value || '',
        ZALO_PHONE: document.getElementById('cfgZaloPhone')?.value || '',
        OWNER_DISCORD_TAG: document.getElementById('cfgOwnerTag')?.value || '',
        WEB_PORT: document.getElementById('cfgWebPort')?.value || 10272,
        WEB_PASSWORD: document.getElementById('cfgWebPassword')?.value || '',
        DISCORD_CLIENT_ID: document.getElementById('cfgClientId')?.value || '',
        DISCORD_CLIENT_SECRET: document.getElementById('cfgClientSecret')?.value || '',
        DISCORD_REDIRECT_URI: document.getElementById('cfgRedirectUri')?.value || '',

        AI_MODEL: document.getElementById('cfgAiModel')?.value || '',
        GEMINI_API_KEY: document.getElementById('cfgGeminiKey')?.value || '',
        GROQ_API_KEY: document.getElementById('cfgGroqKey')?.value || '',
        OPENAI_API_KEY: document.getElementById('cfgOpenAIKey')?.value || '',
        XKIRO_API_KEY: document.getElementById('cfgXkiroKey')?.value || '',
        PKMC_API_KEY: document.getElementById('cfgPkmcKey')?.value || '',

        LAVALINK_HOST: document.getElementById('cfgLavalinkHost')?.value || '',
        LAVALINK_PORT: document.getElementById('cfgLavalinkPort')?.value || 2334,
        LAVALINK_PASSWORD: document.getElementById('cfgLavalinkPassword')?.value || '',
        FALIX_API_KEY: document.getElementById('cfgFalixKey')?.value || '',
        TOKEN_DIEM_DANH: document.getElementById('cfgTokenDiemDanh')?.value || '',
        MAP_DIEM_DANH_ID: document.getElementById('cfgMapDiemDanhId')?.value || ''
    };

    const res = await apiRequest('/api/config', 'POST', payload);
    if (res.ok) {
        showToast(res.message || 'Đã lưu cấu hình thành công!', 'success');
        loadRawConfigFile();
    } else {
        showToast(res.error || 'Lỗi lưu cấu hình', 'error');
    }
}

async function loadRawConfigFile() {
    const editor = document.getElementById('cfgRawEditor');
    const status = document.getElementById('cfgRawStatusText');
    if (!editor) return;

    try {
        const res = await apiRequest('/api/admin/config-raw');
        if (res.ok && res.content !== undefined) {
            editor.value = res.content;
            if (status) status.innerText = `Đã nạp file config.py (${res.content.split('\n').length} dòng)`;
        } else {
            if (status) status.innerText = `Lỗi: ${res.error || 'Không tải được file'}`;
        }
    } catch (e) {
        if (status) status.innerText = `Lỗi mạng khi nạp config.py`;
    }
}

async function saveRawConfigFile() {
    const editor = document.getElementById('cfgRawEditor');
    const status = document.getElementById('cfgRawStatusText');
    if (!editor) return;

    const content = editor.value;
    if (!content.trim()) {
        showToast('Nội dung file không được để trống!', 'warning');
        return;
    }

    if (status) status.innerText = '⏳ Đang kiểm tra cú pháp và lưu...';
    const res = await apiRequest('/api/admin/config-raw', 'POST', { content });
    if (res.ok) {
        showToast(res.message || 'Đã lưu trực tiếp file config.py!', 'success');
        if (status) status.innerText = `✅ Đã lưu thành công lúc ${new Date().toLocaleTimeString()}`;
        loadConfigSettings();
    } else {
        showToast(`❌ ${res.error || 'Lỗi lưu file'}`, 'error');
        if (status) status.innerText = `❌ ${res.error}`;
    }
}


function setupLogsWebSocket() {
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    let wsUrl = `${protocol}//${window.location.host}/ws/logs`;
    if (state.token) wsUrl += `?token=${encodeURIComponent(state.token)}`;

    state.logsWs = new WebSocket(wsUrl);

    state.logsWs.onmessage = (event) => {
        try {
            const msg = JSON.parse(event.data);
            if (msg.type === 'log') {
                appendLogEntry(msg.data);
            }
        } catch (e) {
            console.error('Lỗi parse log WS:', e);
        }
    };

    state.logsWs.onclose = () => {
        console.log('Logs WebSocket đóng, tự động kết nối lại sau 3s...');
        setTimeout(setupLogsWebSocket, 3000);
    };
}

function appendLogEntry(log) {
    const logsContainer = document.getElementById('consoleLogsBody');
    if (!logsContainer) return;

    const row = document.createElement('div');
    row.className = 'log-row';
    row.innerHTML = `
        <span class="log-time">[${log.time}]</span>
        <span class="log-level ${log.level}">${log.level}</span>
        <span class="log-msg">${escapeHtml(log.message)}</span>
    `;
    logsContainer.appendChild(row);

    
    logsContainer.scrollTop = logsContainer.scrollHeight;
}

function clearConsoleLogs() {
    const logsContainer = document.getElementById('consoleLogsBody');
    if (logsContainer) logsContainer.innerHTML = '';
}

function sendConsoleCommand() {
    const input = document.getElementById('consoleCmdInput');
    const cmd = input ? input.value.trim() : '';
    if (!cmd) return;
    if (!state.logsWs || state.logsWs.readyState !== WebSocket.OPEN) {
        showToast('WebSocket Console chưa kết nối hoặc đang kết nối lại...', 'warning');
        return;
    }

    state.logsWs.send(JSON.stringify({ type: 'cmd', cmd }));
    input.value = '';
}

function sendConsoleQuickCmd(cmd) {
    if (!state.logsWs || state.logsWs.readyState !== WebSocket.OPEN) {
        showToast('WebSocket Console chưa kết nối hoặc đang kết nối lại...', 'warning');
        return;
    }
    state.logsWs.send(JSON.stringify({ type: 'cmd', cmd }));
}

function escapeHtml(str) {
    return str.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");
}


function openLoginModal() {
    
    if (!window._authRedirecting) {
        window._authRedirecting = true;
        location.href = '/login';
    }
}

async function performLogin() {
    const pwdInput = document.getElementById('loginPassword');
    const password = pwdInput ? pwdInput.value.trim() : '';

    const res = await apiRequest('/api/login', 'POST', { password });
    if (res.ok) {
        state.token = res.token;
        localStorage.setItem('sakura_auth_token', res.token);
        showToast('Đăng nhập thành công!', 'success');
        document.getElementById('loginModal').classList.remove('active');
        fetchStatus();
        switchTab(state.activeTab);
    } else {
        showToast(res.message || 'Mật khẩu sai!', 'error');
    }
}


function setupModals() {
    document.querySelectorAll('.modal-overlay').forEach(modal => {
        modal.addEventListener('click', (e) => {
            if (e.target === modal && modal.id !== 'loginModal') {
                modal.classList.remove('active');
            }
        });
    });
}

function closeModal(modalId) {
    const el = document.getElementById(modalId);
    if (el) el.classList.remove('active');
}


document.addEventListener('DOMContentLoaded', async () => {
    setupNavigation();
    setupModals();
    initPerformanceChart();
    const authed = await checkAuthAndApplyRole();
    if (!authed) return;
    setupLogsWebSocket();
    fetchStatus();
    setInterval(fetchStatus, 3000);
    refreshBotConnection();
    setInterval(refreshBotConnection, 10000);
    
    if (window.location.pathname.match(/^\/dashboard\/\d+$/)) {
        
        await loadGuilds();
        handleDashboardDeepLink();
    }
    
    window.addEventListener('popstate', () => {
        const mm = window.location.pathname.match(/^\/dashboard\/(\d+)$/);
        if (mm) openGuildDrawer(mm[1], false);
        else closeGuildDrawer();
    });
    
    window.addEventListener('sakuraThemeChange', (e) => {
        const isLight = e.detail && e.detail.theme === 'light';
        if (state.chartInstance) {
            state.chartInstance.options.plugins.legend.labels.color = isLight ? '#5e526c' : '#94a3b8';
            if (state.chartInstance.options.scales && state.chartInstance.options.scales.y) {
                state.chartInstance.options.scales.y.grid.color = isLight ? 'rgba(0,0,0,0.06)' : 'rgba(255, 255, 255, 0.05)';
                state.chartInstance.options.scales.y.ticks.color = isLight ? '#8b8099' : '#64748b';
                state.chartInstance.options.scales.x.ticks.color = isLight ? '#8b8099' : '#64748b';
            }
            state.chartInstance.update('none');
        }
    });
});




state.adminFishing = {
    activeSubTab: 'user',
    activeDexCat: 'all',
    fishList: [],
    catalogs: {},
    currentUser: null
};

const RARITY_BADGES = {
    common: { label: '⚪ THƯỜNG', color: '#94a3b8', bg: 'rgba(148,163,184,0.15)', border: 'rgba(148,163,184,0.3)' },
    rare: { label: '🔵 HIẾM', color: '#38bdf8', bg: 'rgba(56,189,248,0.15)', border: 'rgba(56,189,248,0.3)' },
    epic: { label: '🟣 SỬ THI', color: '#c084fc', bg: 'rgba(192,132,252,0.15)', border: 'rgba(192,132,252,0.3)' },
    legendary: { label: '🟡 HUYỀN THOẠI', color: '#facc15', bg: 'rgba(250,204,21,0.15)', border: 'rgba(250,204,21,0.3)' },
    admin: { label: '🔴 THẦN THOẠI', color: '#f43f5e', bg: 'rgba(244,63,94,0.15)', border: 'rgba(244,63,94,0.35)' }
};

function initAdminFishingTab() {
    loadAdminFishList();
    if (state.adminFishing.currentUser) {
        loadAdminFishUser();
    }
    afOnGiftcodeCategoryChange();
}

function switchAdminFishTab(subTab) {
    state.adminFishing.activeSubTab = subTab;
    const tabs = ['user', 'codes', 'dailycode', 'list', 'add', 'chest', 'aquarium', 'rates', 'achievements'];
    tabs.forEach(t => {
        let name = t.charAt(0).toUpperCase() + t.slice(1);
        if (t === 'dailycode') name = 'DailyCode';
        const btn = document.getElementById(`btnAfSub${name}`);
        const view = document.getElementById(`afView${name}`);
        if (btn) btn.classList.toggle('active', t === subTab);
        if (view) view.style.display = (t === subTab) ? 'block' : 'none';
    });

    if (subTab === 'aquarium') loadAdminAquariumList();
    else if (subTab === 'achievements') afLoadAchievementsCatalog();
    else if (subTab === 'codes') {
        loadAdminFishGiftcodes();
        afOnGiftcodeCategoryChange();
        loadAdminDailyGiftcode();
    }
    else if (subTab === 'dailycode') loadAdminDailyGiftcode();
    else if (subTab === 'list') renderAdminFishTable();
    else if (subTab === 'add') afUpdateNewFishPreview();
    else if (subTab === 'chest') {
        afPopulateChestPools();
        afUpdateNewChestPreview();
    }
    else if (subTab === 'rates') {
        loadGameRates();
    }
}

async function loadAdminFishList() {
    const res = await apiRequest('/api/fishing/admin/fish-list');
    if (!res.ok) return;

    state.adminFishing.fishList = res.fish || [];
    state.adminFishing.catalogs = res.catalogs || {};
    state.adminFishing.mutations = res.mutations || [];

    
    const fishSel = document.getElementById('afAddFishSelect');
    if (fishSel) {
        fishSel.innerHTML = state.adminFishing.fishList.map(f => {
            return `<option value="${escapeHtml(f.name)}" data-price="${f.price}" data-rarity="${f.rarity}">${escapeHtml(f.name)} (${f.rarity}) — ${Number(f.price).toLocaleString()} Coin</option>`;
        }).join('');
    }

    
    const mutSel = document.getElementById('afAddMutationSelect');
    if (mutSel) {
        mutSel.innerHTML = '<option value="" data-multi="1.0">(Không có đột biến)</option>' +
            (res.mutations || []).map(m => `<option value="${escapeHtml(m.name)}" data-multi="${m.price_multi}">${escapeHtml(m.name)} (x${m.price_multi} giá)</option>`).join('');
    }

    afRecalculateFishPrice();

    
    const rodSel = document.getElementById('afAddRodSelect');
    const gcRodSel = document.getElementById('afGcRodSelect');
    const rods = res.catalogs?.rods || {};
    const rodOptions = Object.entries(rods).map(([id, r]) => {
        return `<option value="${id}">${escapeHtml(r.name || id)} (Độ bền: ${r.durability}, May mắn: +${r.luck})</option>`;
    }).join('');
    if (rodSel) rodSel.innerHTML = rodOptions;
    if (gcRodSel) gcRodSel.innerHTML = '<option value="">(Không tặng cần)</option>' + rodOptions;

    
    const baits = res.catalogs?.baits || {};
    const gcBaitSel = document.getElementById('afGcBaitSelect');
    if (gcBaitSel) {
        gcBaitSel.innerHTML = '<option value="">(Không tặng mồi)</option>' +
            Object.entries(baits).map(([id, b]) => `<option value="${id}">${escapeHtml(b.name || id)} (+${b.luck} may mắn)</option>`).join('');
    }

    
    const chests = res.catalogs?.chests || {};
    const gcChestSel = document.getElementById('afGcChestSelect');
    if (gcChestSel) {
        gcChestSel.innerHTML = '<option value="">(Không tặng rương)</option>' +
            Object.entries(chests).map(([id, c]) => `<option value="${id}">${escapeHtml(c.name || id)}</option>`).join('');
    }

    
    const pets = res.catalogs?.pets || {};
    const gcPetSel = document.getElementById('afGcPetSelect');
    if (gcPetSel) {
        gcPetSel.innerHTML = '<option value="">(Không tặng pet)</option>' +
            Object.entries(pets).map(([id, p]) => `<option value="${id}">${escapeHtml(p.name || id)}</option>`).join('');
    }

    afOnCategoryChange();
    afPopulateChestPools();
    renderAdminFishTable();
}

function afRecalculateFishPrice() {
    const sel = document.getElementById('afAddFishSelect');
    if (!sel || !sel.selectedOptions.length) return;
    const opt = sel.selectedOptions[0];
    const basePrice = parseInt(opt.getAttribute('data-price') || '100');
    const weight = parseFloat(document.getElementById('afAddFishWeight')?.value || '2.5');

    let sizeMulti = 1.0;
    let autoSizeName = "Tiêu Chuẩn";
    if (weight < 1.5) {
        sizeMulti = 0.75;
        autoSizeName = "Bé Tí";
    } else if (weight < 6.0) {
        sizeMulti = 1.0;
        autoSizeName = "Tiêu Chuẩn";
    } else if (weight < 25.0) {
        sizeMulti = 1.5;
        autoSizeName = "To Lớn";
    } else if (weight < 150.0) {
        sizeMulti = 2.3;
        autoSizeName = "Khổng Lồ";
    } else {
        sizeMulti = Math.max(4.0, +(4.0 * Math.sqrt(weight / 150.0)).toFixed(2));
        autoSizeName = "Thần Thoại";
    }

    const sizeNameSel = document.getElementById('afAddFishSizeName');
    let chosenSizeName = autoSizeName;
    if (sizeNameSel) {
        if (sizeNameSel.value && sizeNameSel.value !== 'auto') {
            chosenSizeName = sizeNameSel.value;
            if (chosenSizeName === 'Bé Tí') sizeMulti = 0.75;
            else if (chosenSizeName === 'Tiêu Chuẩn') sizeMulti = 1.0;
            else if (chosenSizeName === 'To Lớn') sizeMulti = 1.5;
            else if (chosenSizeName === 'Khổng Lồ') sizeMulti = 2.3;
            else if (chosenSizeName === 'Thần Thoại') sizeMulti = Math.max(4.0, +(4.0 * Math.sqrt(weight / 150.0)).toFixed(2));
        }
    }

    const lengthInput = document.getElementById('afAddFishLength');
    if (lengthInput && (!lengthInput.dataset.manual || lengthInput.dataset.manual === 'false')) {
        lengthInput.value = (Math.cbrt(Math.max(0.1, weight)) * 16.0).toFixed(1);
    }

    const mutSel = document.getElementById('afAddMutationSelect');
    let mutMulti = 1.0;
    if (mutSel && mutSel.selectedOptions.length) {
        mutMulti = parseFloat(mutSel.selectedOptions[0].getAttribute('data-multi') || '1.0');
    }

    const finalPrice = Math.max(20, Math.round(basePrice * sizeMulti * mutMulti));
    const priceInput = document.getElementById('afAddFishPrice');
    if (priceInput) {
        priceInput.value = finalPrice;
    }
    const badge = document.getElementById('afPriceCalcBadge');
    if (badge) {
        badge.textContent = `(Gốc: ${basePrice.toLocaleString()} × Kích cỡ ${sizeMulti}x [${chosenSizeName}] × Đột biến ${mutMulti}x)`;
    }
}

function afOnSizeSelectChange() {
    const sizeNameSel = document.getElementById('afAddFishSizeName');
    const weightInput = document.getElementById('afAddFishWeight');
    if (sizeNameSel && weightInput && sizeNameSel.value !== 'auto') {
        const val = sizeNameSel.value;
        if (val === 'Bé Tí' && parseFloat(weightInput.value) >= 1.5) weightInput.value = '1.0';
        else if (val === 'Tiêu Chuẩn' && (parseFloat(weightInput.value) < 1.5 || parseFloat(weightInput.value) >= 6.0)) weightInput.value = '3.5';
        else if (val === 'To Lớn' && (parseFloat(weightInput.value) < 6.0 || parseFloat(weightInput.value) >= 25.0)) weightInput.value = '15.0';
        else if (val === 'Khổng Lồ' && (parseFloat(weightInput.value) < 25.0 || parseFloat(weightInput.value) >= 150.0)) weightInput.value = '60.0';
        else if (val === 'Thần Thoại' && parseFloat(weightInput.value) < 150.0) weightInput.value = '250.0';
    }
    afRecalculateFishPrice();
}

function afOnFishSelectChange() {
    const sel = document.getElementById('afAddFishSelect');
    if (!sel || !sel.selectedOptions.length) return;
    const opt = sel.selectedOptions[0];
    const rarity = opt.getAttribute('data-rarity') || 'common';
    const weightInput = document.getElementById('afAddFishWeight');
    if (weightInput) {
        if (rarity === 'common') weightInput.value = (Math.random() * 2 + 1).toFixed(1);
        else if (rarity === 'rare') weightInput.value = (Math.random() * 8 + 3).toFixed(1);
        else if (rarity === 'epic') weightInput.value = (Math.random() * 25 + 10).toFixed(1);
        else if (rarity === 'legendary') weightInput.value = (Math.random() * 150 + 40).toFixed(1);
        else if (rarity === 'admin') weightInput.value = (Math.random() * 1200 + 300).toFixed(1);
    }
    afRecalculateFishPrice();
}

function afOnCategoryChange() {
    const catSel = document.getElementById('afItemCategorySelect');
    const itemSel = document.getElementById('afItemIdSelect');
    if (!catSel || !itemSel) return;
    const cat = catSel.value;
    const catalogs = state.adminFishing.catalogs || {};
    let items = {};
    if (cat === 'baits') items = catalogs.baits || {};
    else if (cat === 'chests') items = catalogs.chests || {};
    else if (cat === 'items') items = catalogs.items || {};
    else if (cat === 'pets') items = catalogs.pets || {};

    itemSel.innerHTML = Object.entries(items).map(([id, it]) => {
        return `<option value="${id}">${escapeHtml(it.name || id)}</option>`;
    }).join('');
}


async function loadAdminFishUser() {
    const input = document.getElementById('afSearchUserId');
    const uid = input ? input.value.trim() : '';
    if (!uid) {
        showToast('Vui lòng nhập Discord User ID', 'warning');
        return;
    }

    const res = await apiRequest(`/api/fishing/admin/user?user_id=${encodeURIComponent(uid)}`);
    if (!res.ok) return;

    state.adminFishing.currentUser = res;

    const placeholder = document.getElementById('afUserPlaceholder');
    const detail = document.getElementById('afUserDetail');
    if (placeholder) placeholder.style.display = 'none';
    if (detail) detail.style.display = 'block';

    const avatar = document.getElementById('afUserAvatar');
    if (avatar) avatar.src = res.avatar || 'https://cdn.discordapp.com/embed/avatars/0.png';

    const nameEl = document.getElementById('afUserName');
    if (nameEl) nameEl.innerText = res.username || `User ${res.user_id}`;

    const idEl = document.getElementById('afUserDiscordId');
    if (idEl) idEl.innerText = res.user_id;

    const coinsEl = document.getElementById('afUserCoins');
    if (coinsEl) coinsEl.innerText = Number(res.coins || 0).toLocaleString();

    const xuEl = document.getElementById('afUserXu');
    if (xuEl) xuEl.innerText = Number(res.xu || 0).toLocaleString();

    const bankEl = document.getElementById('afUserBank');
    if (bankEl) bankEl.innerText = Number(res.bank || 0).toLocaleString();

    const bagCount = (res.fish_bag || []).length;
    const maxBag = res.max_bag || 30;
    const bagUsageEl = document.getElementById('afUserBagUsage');
    if (bagUsageEl) bagUsageEl.innerText = `${bagCount}/${maxBag}`;

    const bagCountText = document.getElementById('afBagCountText');
    if (bagCountText) bagCountText.innerText = bagCount;

    
    const tbody = document.getElementById('afFishBagTableBody');
    if (tbody) {
        if (!res.fish_bag || res.fish_bag.length === 0) {
            tbody.innerHTML = '<tr><td colspan="7" style="text-align:center; padding:30px; color:var(--text-dim);">Giỏ cá của cần thủ đang trống.</td></tr>';
        } else {
            tbody.innerHTML = res.fish_bag.map((f, idx) => {
                const r = RARITY_BADGES[f.rarity] || RARITY_BADGES.common;
                const timeStr = f.time ? new Date(f.time * 1000).toLocaleString('vi-VN') : '—';
                const mutStr = f.mutation ? `<span class="badge" style="background:rgba(255,105,180,0.18); color:var(--accent-pink);">${escapeHtml(f.mutation)}</span>` : '<span style="color:var(--text-dim); font-size:0.8rem;">—</span>';
                return `
                    <tr>
                        <td style="font-weight:600; color:var(--text-dim);">${idx + 1}</td>
                        <td>
                            <strong style="color:var(--text-main);">${escapeHtml(f.name || 'Cá')}</strong>
                            <div style="margin-top:2px;"><span class="badge" style="background:${r.bg}; color:${r.color}; border:1px solid ${r.border}; font-size:0.7rem;">${r.label}</span></div>
                        </td>
                        <td>${f.weight || 0} kg <span style="color:var(--text-dim); font-size:0.75rem;">(${f.length || 0} cm)</span></td>
                        <td>${mutStr}</td>
                        <td style="color:#ffd700; font-weight:600;">${Number(f.price || 0).toLocaleString()}</td>
                        <td style="font-size:0.78rem; color:var(--text-dim);">${timeStr}</td>
                        <td>
                            <button class="btn btn-danger btn-sm" onclick="afRemoveUserFish(${idx})" title="Xóa con cá này khỏi giỏ">
                                🗑️ Xóa
                            </button>
                        </td>
                    </tr>
                `;
            }).join('');
        }
    }

    
    const aqCountEl = document.getElementById('afAquariumCountText');
    const aqMaxEl = document.getElementById('afAquariumMaxSlots');
    const aqLikesEl = document.getElementById('afAquariumLikesBadge');
    const aqFavBadge = document.getElementById('afAquariumFavBadge');
    const aqFavName = document.getElementById('afAquariumFavName');

    const aquarium = res.aquarium || [];
    const aqSlots = res.aquarium_slots || 6;
    if (aqCountEl) aqCountEl.innerText = aquarium.length;
    if (aqMaxEl) aqMaxEl.innerText = aqSlots;
    if (aqLikesEl) aqLikesEl.innerText = `❤️ ${res.aquarium_likes || 0} Lượt Thích`;

    const favIdx = res.aquarium_favorite;
    if (favIdx !== null && favIdx !== undefined && aquarium[favIdx] && aqFavBadge && aqFavName) {
        aqFavBadge.style.display = 'inline-block';
        aqFavName.innerText = aquarium[favIdx].name || 'Cá';
    } else if (aqFavBadge) {
        aqFavBadge.style.display = 'none';
    }

    const aqTbody = document.getElementById('afAquariumTableBody');
    if (aqTbody) {
        if (aquarium.length === 0) {
            aqTbody.innerHTML = '<tr><td colspan="7" style="text-align:center; padding:30px; color:var(--text-dim);">Bể Thủy Cung hiện đang trống (cần thủ chưa thả con cá nào vào bể).</td></tr>';
        } else {
            aqTbody.innerHTML = aquarium.map((f, idx) => {
                const r = RARITY_BADGES[f.rarity] || RARITY_BADGES.common;
                const isFav = (favIdx === idx);
                const mutStr = f.mutation ? `<span class="badge" style="background:rgba(255,105,180,0.18); color:var(--accent-pink);">${escapeHtml(f.mutation)}</span>` : '<span style="color:var(--text-dim); font-size:0.8rem;">—</span>';
                return `
                    <tr>
                        <td style="font-weight:600; color:var(--text-dim);">${idx + 1}</td>
                        <td>
                            <strong style="color:var(--text-main); font-size: 0.95rem;">${escapeHtml(f.name || 'Cá')}</strong>
                            <div style="margin-top:2px;"><span class="badge" style="background:${r.bg}; color:${r.color}; border:1px solid ${r.border}; font-size:0.7rem;">${r.label}</span></div>
                        </td>
                        <td>${f.weight || 0} kg <span style="color:var(--text-dim); font-size:0.75rem;">(${f.length || 0} cm)</span></td>
                        <td>${mutStr}</td>
                        <td style="color:#ffd700; font-weight:600;">${Number(f.price || 0).toLocaleString()} Coin</td>
                        <td>
                            ${isFav ? '<span class="badge" style="background:rgba(255,215,0,0.2); color:#ffd700; border:1px solid rgba(255,215,0,0.4);">⭐ LINH VẬT BỂ</span>' : '<span style="color:var(--text-dim); font-size:0.8rem;">Trưng bày</span>'}
                        </td>
                        <td>
                            <div style="display:flex; gap:6px;">
                                <button class="btn btn-secondary btn-sm" onclick="afMoveAquariumFishToBag(${idx})" title="Chuyển con cá này về lại giỏ cá">
                                    🎒 Về Giỏ
                                </button>
                                <button class="btn btn-danger btn-sm" onclick="afRemoveAquariumFish(${idx})" title="Xóa vĩnh viễn khỏi thủy cung">
                                    🗑️ Xóa
                                </button>
                            </div>
                        </td>
                    </tr>
                `;
            }).join('');
        }
    }

    
    const rodsBody = document.getElementById('afRodsTableBody');
    if (rodsBody) {
        const rodsObj = res.rods || {};
        if (Object.keys(rodsObj).length === 0) {
            rodsBody.innerHTML = '<tr><td colspan="6" style="text-align:center; padding:20px; color:var(--text-dim);">Chưa sở hữu cần câu nào.</td></tr>';
        } else {
            rodsBody.innerHTML = Object.entries(rodsObj).map(([id, r]) => {
                const isEquipped = (res.equipped_rod === id);
                return `
                    <tr>
                        <td>
                            <strong>${escapeHtml(r.name || id)}</strong>
                            ${isEquipped ? ' <span class="badge badge-sakura" style="font-size:0.68rem;">ĐANG DÙNG</span>' : ''}
                        </td>
                        <td><span style="color:var(--accent-cyan); font-weight:bold;">+${r.refine || 0}</span></td>
                        <td><span style="color:#ffb86c; font-weight:bold;">${r.stars || 0} ⭐</span></td>
                        <td>${r.durability || 0} / ${r.max_durability || 0}</td>
                        <td style="color:#ffd700;">+${r.luck || 0}</td>
                        <td style="white-space: nowrap;">
                            <button class="btn btn-secondary btn-sm" onclick="afEditUserRod('${id}')" style="margin-right:4px;">
                                ✏️ Sửa
                            </button>
                            <button class="btn btn-danger btn-sm" onclick="afRemoveUserRod('${id}')" title="Thu hồi cần">
                                🗑️ Thu Hồi
                            </button>
                        </td>
                    </tr>
                `;
            }).join('');
        }
    }

    
    const invPills = document.getElementById('afInventoryPills');
    if (invPills) {
        let html = '';
        const catalogs = state.adminFishing.catalogs || {};
        const baits = res.baits || {};
        const chests = res.chests || {};
        const items = res.items || {};
        const pets = res.pets || [];

        Object.entries(baits).forEach(([bid, count]) => {
            const bname = catalogs.baits?.[bid]?.name || bid;
            html += `
                <div style="background:rgba(0,0,0,0.3); border:1px solid var(--border-subtle); border-radius:10px; padding:8px 12px; display:flex; align-items:center; gap:8px;">
                    <span>${escapeHtml(bname)}: <strong style="color:var(--accent-pink);">${Number(count).toLocaleString()}</strong></span>
                    <button class="btn btn-secondary btn-sm" style="padding:2px 6px; font-size:0.75rem;" onclick="afQuickAdjustItem('baits', '${bid}', ${count + 10})">+10</button>
                    <button class="btn btn-danger btn-sm" style="padding:2px 6px; font-size:0.75rem;" onclick="afQuickAdjustItem('baits', '${bid}', 0)">Xóa</button>
                </div>
            `;
        });

        Object.entries(chests).forEach(([cid, count]) => {
            const cname = catalogs.chests?.[cid]?.name || cid;
            html += `
                <div style="background:rgba(0,0,0,0.3); border:1px solid var(--border-subtle); border-radius:10px; padding:8px 12px; display:flex; align-items:center; gap:8px;">
                    <span>${escapeHtml(cname)}: <strong style="color:#ffd700;">${Number(count).toLocaleString()}</strong></span>
                    <button class="btn btn-secondary btn-sm" style="padding:2px 6px; font-size:0.75rem;" onclick="afQuickAdjustItem('chests', '${cid}', ${count + 1})">+1</button>
                    <button class="btn btn-danger btn-sm" style="padding:2px 6px; font-size:0.75rem;" onclick="afQuickAdjustItem('chests', '${cid}', 0)">Xóa</button>
                </div>
            `;
        });

        pets.forEach(pid => {
            const pname = catalogs.pets?.[pid]?.name || pid;
            const isEq = (res.equipped_pet === pid);
            html += `
                <div style="background:rgba(0,0,0,0.3); border:1px solid rgba(255,105,180,0.4); border-radius:10px; padding:8px 12px; display:flex; align-items:center; gap:8px;">
                    <span>🐾 ${escapeHtml(pname)} ${isEq ? '<span class="badge badge-sakura" style="font-size:0.65rem;">EQUIPPED</span>' : ''}</span>
                    <button class="btn btn-danger btn-sm" style="padding:2px 6px; font-size:0.75rem;" onclick="afQuickAdjustItem('pets', '${pid}', 0)">Xóa</button>
                </div>
            `;
        });

        if (!html) html = '<div style="color:var(--text-dim); padding:10px;">Chưa có mồi hoặc rương báu nào.</div>';
        invPills.innerHTML = html;
    }
}

function loadAdminFishSelfUser() {
    const input = document.getElementById('afSearchUserId');
    if (!input) return;
    const uid = state.user?.discord_id || state.user?.user_id || '1144785664458637394';
    input.value = uid;
    loadAdminFishUser();
}

async function afSubmitAddFish() {
    if (!state.adminFishing.currentUser) return showToast('Vui lòng chọn cần thủ trước', 'warning');
    const sel = document.getElementById('afAddFishSelect');
    if (!sel || !sel.value) return showToast('Vui lòng chọn loài cá', 'warning');

    const opt = sel.selectedOptions[0];
    const fish_name = opt.value;
    const rarity = opt.getAttribute('data-rarity') || 'common';
    const basePrice = parseInt(opt.getAttribute('data-price') || '100');
    const mutation = document.getElementById('afAddMutationSelect')?.value || null;
    const weight = parseFloat(document.getElementById('afAddFishWeight')?.value || '2.5');
    const count = parseInt(document.getElementById('afAddFishCount')?.value || '1');
    const priceInput = document.getElementById('afAddFishPrice');
    let price = (priceInput && parseInt(priceInput.value) > 0) ? parseInt(priceInput.value) : 0;
    if (price <= 0) {
        
        let sizeMulti = 1.0;
        if (weight < 1.5) sizeMulti = 0.75;
        else if (weight < 6.0) sizeMulti = 1.0;
        else if (weight < 25.0) sizeMulti = 1.5;
        else if (weight < 150.0) sizeMulti = 2.3;
        else sizeMulti = Math.max(4.0, +(4.0 * Math.sqrt(weight / 150.0)).toFixed(2));

        const mutSel = document.getElementById('afAddMutationSelect');
        let mutMulti = 1.0;
        if (mutSel && mutSel.selectedOptions.length) {
            mutMulti = parseFloat(mutSel.selectedOptions[0].getAttribute('data-multi') || '1.0');
        }
        price = Math.max(20, Math.round(basePrice * sizeMulti * mutMulti));
    }

    let size_name = "Tiêu Chuẩn";
    if (weight < 1.5) size_name = "Bé Tí";
    else if (weight < 6.0) size_name = "Tiêu Chuẩn";
    else if (weight < 25.0) size_name = "To Lớn";
    else if (weight < 150.0) size_name = "Khổng Lồ";
    else size_name = "Thần Thoại";

    const customSizeName = document.getElementById('afAddFishSizeName')?.value;
    if (customSizeName && customSizeName !== 'auto') {
        size_name = customSizeName;
    }
    const customLength = parseFloat(document.getElementById('afAddFishLength')?.value || '0');

    const res = await apiRequest('/api/fishing/admin/user/action', 'POST', {
        action: 'add_fish',
        user_id: state.adminFishing.currentUser.user_id,
        fish_name,
        rarity,
        price,
        weight,
        size_name,
        length: customLength > 0 ? customLength : +(Math.cbrt(Math.max(0.1, weight)) * 16.0).toFixed(1),
        mutation,
        count
    });

    if (res.ok) {
        showToast(res.message || 'Thêm cá thành công', 'success');
        loadAdminFishUser();
    }
}

async function afRemoveUserFish(idx) {
    if (!state.adminFishing.currentUser) return;
    if (!confirm('Bạn có chắc muốn xóa con cá này khỏi giỏ đồ của người chơi?')) return;

    const res = await apiRequest('/api/fishing/admin/user/action', 'POST', {
        action: 'remove_fish',
        user_id: state.adminFishing.currentUser.user_id,
        index: idx
    });

    if (res.ok) {
        showToast(res.message || 'Đã xóa cá khỏi giỏ', 'success');
        loadAdminFishUser();
    }
}


async function afMoveAquariumFishToBag(idx) {
    if (!state.adminFishing.currentUser) return;
    const uid = state.adminFishing.currentUser.user_id;
    const res = await apiRequest('/api/fishing/admin/user/action', 'POST', {
        action: 'remove_aquarium_fish',
        user_id: uid,
        index: idx,
        to_bag: true
    });
    if (res.ok) {
        showToast(res.message || 'Đã chuyển cá về giỏ đồ', 'success');
        loadAdminFishUser();
    } else {
        showToast(res.error || 'Lỗi thao tác', 'error');
    }
}

async function afRemoveAquariumFish(idx) {
    if (!confirm('Bạn có chắc muốn xóa vĩnh viễn con cá này khỏi Thủy Cung?')) return;
    if (!state.adminFishing.currentUser) return;
    const uid = state.adminFishing.currentUser.user_id;
    const res = await apiRequest('/api/fishing/admin/user/action', 'POST', {
        action: 'remove_aquarium_fish',
        user_id: uid,
        index: idx,
        to_bag: false
    });
    if (res.ok) {
        showToast(res.message || 'Đã xóa cá khỏi Thủy Cung', 'success');
        loadAdminFishUser();
    } else {
        showToast(res.error || 'Lỗi thao tác', 'error');
    }
}

async function afClearUserAquarium() {
    if (!confirm('Bạn có chắc chắn muốn dọn sạch toàn bộ cá trong Thủy Cung của cần thủ này?')) return;
    if (!state.adminFishing.currentUser) return;
    const uid = state.adminFishing.currentUser.user_id;
    const res = await apiRequest('/api/fishing/admin/user/action', 'POST', {
        action: 'clear_aquarium',
        user_id: uid
    });
    if (res.ok) {
        showToast(res.message || 'Đã dọn sạch Thủy Cung', 'success');
        loadAdminFishUser();
    } else {
        showToast(res.error || 'Lỗi thao tác', 'error');
    }
}

async function afPromptSetAquariumSlots() {
    if (!state.adminFishing.currentUser) return;
    const current = state.adminFishing.currentUser.aquarium_slots || 6;
    const val = prompt('Nhập số ô chứa tối đa cho Thủy Cung (1 - 100 ô):', current);
    if (val === null) return;
    const num = parseInt(val, 10);
    if (isNaN(num) || num < 1 || num > 100) {
        showToast('Số ô phải từ 1 đến 100!', 'warning');
        return;
    }
    const uid = state.adminFishing.currentUser.user_id;
    const res = await apiRequest('/api/fishing/admin/user/action', 'POST', {
        action: 'set_aquarium_slots',
        user_id: uid,
        slots: num
    });
    if (res.ok) {
        showToast(res.message || 'Đã cập nhật sức chứa Thủy Cung', 'success');
        loadAdminFishUser();
    } else {
        showToast(res.error || 'Lỗi thao tác', 'error');
    }
}

async function afClearUserFishBag() {
    if (!state.adminFishing.currentUser) return;
    if (!confirm('⚠️ CẢNH BÁO: Bạn có chắc chắn muốn XÓA SẠCH toàn bộ cá trong giỏ của người chơi này?')) return;

    const res = await apiRequest('/api/fishing/admin/user/action', 'POST', {
        action: 'clear_fish_bag',
        user_id: state.adminFishing.currentUser.user_id
    });

    if (res.ok) {
        showToast(res.message || 'Đã xóa toàn bộ cá', 'success');
        loadAdminFishUser();
    }
}

async function afSubmitAddRod() {
    if (!state.adminFishing.currentUser) return showToast('Vui lòng chọn cần thủ trước', 'warning');
    const rod_id = document.getElementById('afAddRodSelect')?.value;
    if (!rod_id) return showToast('Vui lòng chọn loại cần câu', 'warning');

    const refine = parseInt(document.getElementById('afAddRodRefine')?.value || '0');
    const stars = parseInt(document.getElementById('afAddRodStars')?.value || '0');
    const durabilityInput = document.getElementById('afAddRodDurability');
    const durability = durabilityInput && durabilityInput.value ? parseInt(durabilityInput.value) : undefined;

    const res = await apiRequest('/api/fishing/admin/user/action', 'POST', {
        action: 'add_rod',
        user_id: state.adminFishing.currentUser.user_id,
        rod_id,
        refine,
        stars,
        durability
    });

    if (res.ok) {
        showToast(res.message || 'Cấp cần câu thành công', 'success');
        loadAdminFishUser();
    }
}

async function afRemoveUserRod(rod_id) {
    if (!state.adminFishing.currentUser) return;
    if (!confirm(`Bạn có chắc muốn thu hồi cần câu ${rod_id} của người chơi?`)) return;

    const res = await apiRequest('/api/fishing/admin/user/action', 'POST', {
        action: 'remove_rod',
        user_id: state.adminFishing.currentUser.user_id,
        rod_id
    });

    if (res.ok) {
        showToast(res.message || 'Thu hồi cần thành công', 'success');
        loadAdminFishUser();
    }
}

async function afSubmitSetItem() {
    if (!state.adminFishing.currentUser) return showToast('Vui lòng chọn cần thủ trước', 'warning');
    const cat = document.getElementById('afItemCategorySelect')?.value || 'baits';
    const item_id = document.getElementById('afItemIdSelect')?.value;
    if (!item_id) return showToast('Vui lòng chọn vật phẩm', 'warning');
    const quantity = parseInt(document.getElementById('afItemQuantity')?.value || '0');

    const res = await apiRequest('/api/fishing/admin/user/action', 'POST', {
        action: 'set_item',
        user_id: state.adminFishing.currentUser.user_id,
        category: cat,
        item_id,
        quantity
    });

    if (res.ok) {
        showToast(res.message || 'Cập nhật vật phẩm thành công', 'success');
        loadAdminFishUser();
    }
}

async function afQuickAdjustItem(cat, item_id, quantity) {
    if (!state.adminFishing.currentUser) return;
    const res = await apiRequest('/api/fishing/admin/user/action', 'POST', {
        action: 'set_item',
        user_id: state.adminFishing.currentUser.user_id,
        category: cat,
        item_id,
        quantity
    });
    if (res.ok) {
        showToast(res.message || 'Cập nhật thành công', 'success');
        loadAdminFishUser();
    }
}

async function afClearUserTrash() {
    if (!state.adminFishing.currentUser) return;
    const res = await apiRequest('/api/fishing/admin/user/action', 'POST', {
        action: 'clear_trash',
        user_id: state.adminFishing.currentUser.user_id
    });
    if (res.ok) {
        showToast(res.message || 'Đã dọn sạch túi rác', 'success');
        loadAdminFishUser();
    }
}


async function loadAdminFishGiftcodes() {
    const res = await apiRequest('/api/fishing/admin/giftcodes');
    if (!res.ok) return;

    const list = res.giftcodes || [];
    const countEl = document.getElementById('afGcCountText');
    if (countEl) countEl.innerText = list.length;

    const tbody = document.getElementById('afGiftcodesTableBody');
    if (!tbody) return;

    if (list.length === 0) {
        tbody.innerHTML = '<tr><td colspan="6" style="text-align:center; padding:30px; color:var(--text-dim);">Chưa có mã Giftcode nào trong hệ thống.</td></tr>';
        return;
    }

    tbody.innerHTML = list.map(c => {
        let statusBadge = '<span class="badge badge-success">🟢 Còn hạn</span>';
        if (c.is_expired) statusBadge = '<span class="badge badge-danger">🔴 Đã hết hạn</span>';
        else if (c.is_full) statusBadge = '<span class="badge badge-warning">⚠️ Đầy lượt</span>';

        const rew = c.rewards || {};
        const rewParts = [];
        if (rew.coins) rewParts.push(`💰 +${Number(rew.coins).toLocaleString()} Coins`);
        if (rew.xu) rewParts.push(`🪙 +${Number(rew.xu).toLocaleString()} Xu`);
        if (rew.rods && rew.rods.length) {
            const rodStr = rew.rods.map(r => {
                if (typeof r === 'object') {
                    const st = (r.refine || r.stars) ? ` (+${r.refine || 0} | ${r.stars || 0}⭐)` : '';
                    return `${escapeHtml(r.name || r.id)}${st}`;
                }
                return escapeHtml(r);
            }).join(', ');
            rewParts.push(`🎣 Cần: ${rodStr}`);
        }
        if (rew.picks && rew.picks.length) {
            const pickStr = rew.picks.map(p => {
                if (typeof p === 'object') {
                    const st = (p.refine || p.stars) ? ` (+${p.refine || 0} | ${p.stars || 0}⭐)` : '';
                    return `${escapeHtml(p.name || p.id)}${st}`;
                }
                return escapeHtml(p);
            }).join(', ');
            rewParts.push(`⛏️ Cuốc: ${pickStr}`);
        }
        if (rew.pets && rew.pets.length) {
            const petStr = rew.pets.map(p => {
                if (typeof p === 'object') {
                    const st = (p.refine || p.stars) ? ` (${p.stars || 0}⭐ | +${p.refine || 0})` : '';
                    return `${escapeHtml(p.name || p.id)}${st}`;
                }
                return escapeHtml(p);
            }).join(', ');
            rewParts.push(`🐾 Pet: ${petStr}`);
        }
        if (rew.baits && Object.keys(rew.baits).length) {
            rewParts.push(`🪱 Mồi: ` + Object.entries(rew.baits).map(([k, v]) => `${k} x${v}`).join(', '));
        }
        if (rew.chests && Object.keys(rew.chests).length) {
            rewParts.push(`📦 Rương: ` + Object.entries(rew.chests).map(([k, v]) => `${k} x${v}`).join(', '));
        }
        if (rew.items && Object.keys(rew.items).length) {
            rewParts.push(`✨ Tiện ích: ` + Object.entries(rew.items).map(([k, v]) => `${k} x${v}`).join(', '));
        }
        if (rew.ores && Object.keys(rew.ores).length) {
            rewParts.push(`💎 Quặng: ` + Object.entries(rew.ores).map(([k, v]) => `${k} x${v}`).join(', '));
        }
        if (rew.supplies && Object.keys(rew.supplies).length) {
            rewParts.push(`🧨 Vật tư: ` + Object.entries(rew.supplies).map(([k, v]) => `${k} x${v}`).join(', '));
        }
        if (rew.farm_seeds && Object.keys(rew.farm_seeds).length) {
            rewParts.push(`🌱 Hạt giống: ` + Object.entries(rew.farm_seeds).map(([k, v]) => `${k} x${v}`).join(', '));
        }
        if (rew.farm_crops && Object.keys(rew.farm_crops).length) {
            rewParts.push(`🌾 Nông sản: ` + Object.entries(rew.farm_crops).map(([k, v]) => `${k} x${v}`).join(', '));
        }
        if (rew.custom_items && rew.custom_items.length) {
            const cStr = rew.custom_items.map(ci => `${ci.name || ci.id} x${ci.amount || 1}`).join(', ');
            rewParts.push(`🏷️ Custom: ${cStr}`);
        }

        const expStr = c.expires_at > 0 ? new Date(c.expires_at * 1000).toLocaleString('vi-VN') : 'Vĩnh viễn';
        const usesStr = `${c.used_count || 0} / ${c.max_uses > 0 ? c.max_uses : '∞'}`;

        return `
            <tr>
                <td><strong style="color:var(--accent-pink); font-size:1rem; letter-spacing:0.5px;">${escapeHtml(c.code)}</strong></td>
                <td style="font-size:0.82rem;">${rewParts.join('<br>') || 'Không có quà'}</td>
                <td><span style="font-weight:600;">${usesStr}</span></td>
                <td style="font-size:0.82rem; color:var(--text-dim);">${expStr}</td>
                <td>${statusBadge}</td>
                <td>
                    <button class="btn btn-danger btn-sm" onclick="afDeleteGiftcode('${escapeHtml(c.code)}')">
                        🗑️ Xóa
                    </button>
                </td>
            </tr>
        `;
    }).join('');
}

const GIFTCODE_ITEMS_CATALOG = {
    
    rods: [
        { id: 'rod_wood', name: '🎣 Cần Câu Gỗ (Cơ bản)' },
        { id: 'rod_bamboo', name: '🎋 Cần Câu Tre Dẻo (+8 Luck)' },
        { id: 'rod_iron', name: '⚙️ Cần Câu Sắt (+16 Luck)' },
        { id: 'rod_coral', name: '🪸 Cần San Hô Cổ (+26 Luck)' },
        { id: 'rod_gold', name: '👑 Cần Câu Vàng (+38 Luck)' },
        { id: 'rod_obsidian', name: '🖤 Cần Hắc Diện Thạch (+55 Luck)' },
        { id: 'rod_diamond', name: '💎 Cần Câu Kim Cương (+75 Luck)' },
        { id: 'rod_mecha', name: '🤖 Cần Cơ Khí Thủy Triều (+105 Luck)' },
        { id: 'rod_poseidon', name: '🔱 Cần Hải Thần Poseidon (+160 Luck)' },
        { id: 'rod_abyssal_reaper', name: '💀 Cần Tử Thần Vực Thẳm (+210 Luck)' },
        { id: 'rod_starlight', name: '✨ Cần Tinh Tú Thần Thoại (+280 Luck)' },
        { id: 'rod_astral_god', name: '🌌 Cần Thần Tinh Tú Astral (+350 Luck)' },
        { id: 'rod_dragon_emperor', name: '🐉 Cần Long Vương Tối Cao (+600 Luck)' },
        { id: 'rod_infinity_void', name: '🔮 Cần Vô Cực Hư Không (+1200 Luck)' }
    ],
    picks: [
        { id: 'pick_wooden', name: '🪵 Cuốc Gỗ Sơ Cấp' },
        { id: 'pick_stone', name: '🪨 Cuốc Đá Trầm Tích (+20 Luck)' },
        { id: 'pick_iron', name: '⛏️ Cuốc Sắt Tôi Luyện (+50 Luck)' },
        { id: 'pick_gold', name: '🪙 Cuốc Vàng Hoàng Kim (+110 Luck)' },
        { id: 'pick_diamond', name: '💎 Cuốc Kim Cương Sắc Lẹm (+220 Luck)' },
        { id: 'pick_netherite', name: '🖤 Cuốc Netherite Dung Nham (+400 Luck)' },
        { id: 'pick_crystal', name: '🔮 Cuốc Tinh Thể Vô Cực (+700 Luck)' },
        { id: 'pick_cosmic', name: '🌌 Cuốc Thần Thoại Khởi Nguyên (+1200 Luck)' }
    ],

    
    pets: [
        { id: 'cat_pet', name: '🐱 Mèo Biển (+8 Luck, +10% Mồi)' },
        { id: 'otter_pet', name: '🦦 Rái Cá Lặn (+15 Luck, +15% Mồi)' },
        { id: 'penguin_pet', name: '🐧 Cánh Cụt Băng (+22 Luck, +20% Mồi)' },
        { id: 'turtle_pet', name: '🐢 Rùa Cổ Đại (+30 Luck, +25% Mồi)' },
        { id: 'dolphin_pet', name: '🐬 Cá Heo Thần Sóng (+40 Luck, +30% Mồi)' },
        { id: 'dragon_pet', name: '🐉 Rồng Đại Dương (+55 Luck, +35% Mồi)' },
        { id: 'kraken_pet', name: '🐙 Tiểu Kraken Vực Sâu (+80 Luck, +45% Mồi)' },
        { id: 'pet_phoenix', name: '🔥 Phượng Hoàng Lửa Đại Dương (+80 Luck)' },
        { id: 'pet_celestial_fox', name: '🦊 Hồ Ly Cửu Vĩ Tinh Tú (+150 Luck, x2 Giá)' }
    ],

    
    baits: [
        { id: 'bait_normal', name: '🪱 Mồi Thường (+3 Luck)' },
        { id: 'bait_rare', name: '🪱 Mồi Hiếm (+10 Luck)' },
        { id: 'bait_epic', name: '🪱 Mồi Sử Thi (+22 Luck)' },
        { id: 'bait_glow', name: '✨ Mồi Dạ Quang (+35 Luck)' },
        { id: 'bait_legend', name: '🪱 Mồi Huyền Thoại (+55 Luck)' },
        { id: 'bait_dragon', name: '🩸 Mồi Máu Rồng (+80 Luck)' },
        { id: 'bait_mermaid_tear', name: '💧 Nước Mắt Tiên Cá (+105 Luck)' },
        { id: 'bait_abyss', name: '🌀 Mồi Vực Thẳm (+130 Luck)' },
        { id: 'bait_kraken_tentacle', name: '🦑 Xúc Tu Kraken (+160 Luck)' },
        { id: 'bait_golden', name: '🪙 Mồi Hoàng Kim (+200 Luck)' },
        { id: 'bait_godly_essence', name: '🌟 Tinh Hoa Thần Biển (+260 Luck)' },
        { id: 'bait_cosmic', name: '🪐 Mồi Vũ Trụ (+350 Luck)' },
        { id: 'bait_phoenix_blood', name: '🩸 Mồi Huyết Phượng Hoàng (+150 Luck)' },
        { id: 'bait_cosmic_core', name: '🪐 Mồi Lõi Vũ Trụ (+300 Luck)' },
        { id: 'bait_celestial_ambrosia', name: '🌟 Mồi Tiên Dược Thiên Giới (+500 Luck)' }
    ],
    chests: [
        { id: 'chest_wood', name: '📦 Rương Gỗ Trôi Dạt' },
        { id: 'chest_coral', name: '🪸 Rương San Hô' },
        { id: 'chest_silver', name: '🪙 Rương Bạc Chìm Biển Sâu' },
        { id: 'chest_shipwreck', name: '⚓ Rương Tàu Đắm Cổ' },
        { id: 'chest_gold', name: '👑 Rương Hoàng Gia Lộng Lẫy' },
        { id: 'chest_abyss', name: '🐙 Rương Thủy Quái Vực Sâu' },
        { id: 'chest_void', name: '🌌 Rương Hư Không Vĩnh Hằng' }
    ],
    ores: [
        { id: 'ore_stone', name: '🪨 Đá Hoa Cương' },
        { id: 'ore_coal', name: '⬛ Than Đá Hắc Thạch' },
        { id: 'ore_copper', name: '🟫 Đồng Thô Cổ Điển' },
        { id: 'ore_iron', name: '⚙️ Quặng Sắt Tôi Rèn' },
        { id: 'ore_silver', name: '🥈 Bạc Ánh Trăng' },
        { id: 'ore_lapis', name: '🧿 Lapis Thần Bí' },
        { id: 'ore_gold', name: '🪙 Vàng Khối Tinh Khiết' },
        { id: 'gem_amethyst', name: '🟣 Thạch Anh Tím Hoàng Triều' },
        { id: 'gem_topaz', name: '🔶 Hoàng Ngọc Topaz' },
        { id: 'gem_emerald', name: '🟢 Ngọc Lục Bảo Đế Vương' },
        { id: 'gem_ruby', name: '🔴 Hồng Ngọc Huyết Long' },
        { id: 'gem_sapphire', name: '🔷 Lam Ngọc Biển Cả' },
        { id: 'gem_diamond', name: '💎 Kim Cương Tinh Khiết' },
        { id: 'ore_obsidian', name: '🔲 Hắc Diện Thạch Hắc Ám' },
        { id: 'fossil_ancient', name: '🦖 Hóa Thạch Rồng Tiền Sử' },
        { id: 'ore_meteorite', name: '☄️ Mảnh Thiên Thạch Vũ Trụ' },
        { id: 'ore_netherite', name: '🧱 Kim Loại Netherite Địa Ngục' },
        { id: 'heart_of_earth', name: '❤️‍🔥 Trái Tim Địa Mẫu Gaia' },
        { id: 'void_singularity', name: '🌌 Hạt Nhân Hư Không The End' }
    ],
    supplies: [
        { id: 'tnt_small', name: '🧨 Kíp Nổ Dynamite Mini' },
        { id: 'tnt_large', name: '💣 Khối Thuốc Nổ TNT Thượng Hạng' },
        { id: 'miner_lantern', name: '🏮 Đèn Soi Mỏ Siêu Sáng (+60 Luck)' },
        { id: 'drill_fuel', name: '🧪 Dầu Bôi Trơn Mũi Khoan (CD 4s)' }
    ],

    
    farm_seeds: [
        { id: 'seed_wheat', name: '🌾 Hạt Giống Lúa Mì' },
        { id: 'seed_carrot', name: '🥕 Hạt Giống Cà Rốt' },
        { id: 'seed_bokchoy', name: '🥬 Hạt Giống Cải Thìa' },
        { id: 'seed_tomato', name: '🍅 Hạt Giống Cà Chua' },
        { id: 'seed_onion', name: '🧅 Hạt Giống Hành Tây' },
        { id: 'seed_garlic', name: '🧄 Hạt Giống Tỏi Thơm' },
        { id: 'seed_corn', name: '🌽 Hạt Giống Bắp Ngô' },
        { id: 'seed_chili', name: '🌶️ Hạt Giống Ớt Cay' },
        { id: 'seed_strawberry', name: '🍓 Hạt Giống Dâu Tây' },
        { id: 'seed_watermelon', name: '🍉 Hạt Giống Dưa Hấu' },
        { id: 'seed_mushroom', name: '🍄 Bào Tử Nấm Hương' },
        { id: 'seed_grape', name: '🍇 Hạt Giống Nho Tím' },
        { id: 'seed_sunflower', name: '🌻 Hạt Giống Hướng Dương' },
        { id: 'seed_rose', name: '🌹 Hạt Giống Hoa Hồng' },
        { id: 'seed_golden_apple', name: '🍏 Hạt Giống Táo Vàng' },
        { id: 'seed_peach', name: '🍑 Hạt Giống Đào Tiên' },
        { id: 'seed_snow_lotus', name: '🪷 Hạt Giống Sen Tuyết' }
    ],
    farm_crops: [
        { id: 'crop_wheat', name: '🌾 Bó Lúa Mì Vàng' },
        { id: 'crop_carrot', name: '🥕 Cà Rốt Giòn Ngọt' },
        { id: 'crop_bokchoy', name: '🥬 Cây Cải Thìa Xanh' },
        { id: 'crop_tomato', name: '🍅 Cà Chua Mọng Đỏ' },
        { id: 'crop_onion', name: '🧅 Củ Hành Tây Ngọt' },
        { id: 'crop_garlic', name: '🧄 Củ Tỏi Tía Thơm' },
        { id: 'crop_corn', name: '🌽 Bắp Ngô Vàng Óng' },
        { id: 'crop_chili', name: '🌶️ Ớt Chỉ Thiên Đỏ' },
        { id: 'crop_strawberry', name: '🍓 Dâu Tây Đà Lạt' },
        { id: 'crop_watermelon', name: '🍉 Quả Dưa Hấu Khổng Lồ' },
        { id: 'crop_mushroom', name: '🍄 Nấm Hương Rừng Sâu' },
        { id: 'crop_grape', name: '🍇 Chùm Nho Tím Mộng' },
        { id: 'crop_sunflower', name: '🌻 Hoa Hướng Dương Rạng Rỡ' },
        { id: 'crop_rose', name: '🌹 Hoa Hồng Tình Yêu' },
        { id: 'crop_golden_apple', name: '🍏 Táo Vàng Hoàng Gia' },
        { id: 'crop_peach', name: '🍑 Đào Tiên Bồng Lai' },
        { id: 'crop_snow_lotus', name: '🪷 Tuyết Liên Vạn Năm' }
    ],
    farm_tools: [
        { id: 'watering_can_copper', name: '🪣 Bình Tưới Đồng' },
        { id: 'watering_can_silver', name: '🥈 Bình Tưới Bạc' },
        { id: 'watering_can_mythic', name: '🌟 Bình Tưới Thần Thoại' },
        { id: 'farmer_gloves', name: '🧤 Bao Tay Nhà Nông' },
        { id: 'greenhouse_cover', name: '🏛️ Lồng Kính Bảo Vệ' },
        { id: 'rain_talisman', name: '🌧️ Bùa Gọi Mưa' },
        { id: 'sun_talisman', name: '☀️ Bùa Thái Dương' }
    ],
    fertilizers: [
        { id: 'fertilizer_organic', name: '🌿 Phân Hữu Cơ Vi Sinh' },
        { id: 'fertilizer_speed', name: '⚡ Phân Bón Siêu Tốc' },
        { id: 'fertilizer_yield', name: '🌾 Phân Bón Bội Thu' },
        { id: 'fertilizer_revive', name: '💖 Phân Kích Rễ Hồi Sinh' }
    ],
    items: [
        { id: 've_so', name: '🎟️ Vé Số Đại Dương' },
        { id: 'bomb_card', name: '💣 Thẻ Bom Hẹn Giờ Troll' },
        { id: 'shield', name: '🛡️ Khiên Bảo Vệ Miễn Nhiễm Troll' },
        { id: 'rename_card', name: '📝 Thẻ Đổi Biệt Danh Nickname' },
        { id: 'voice_kick', name: '🔊 Thẻ Trục Xuất Khỏi Voice' },
        { id: 'mute_card', name: '🔇 Thẻ Khóa Mõm (Timeout 30s)' },
        { id: 'ghost_ping', name: '👻 Thẻ Ghost Ping Bí Ẩn' },
        { id: 'banana_peel', name: '🍌 Bẫy Vỏ Chuối Trơn Trượt' },
        { id: 'magic_mirror', name: '🪞 Gương Phản Chiếu Đòn Troll' },
        { id: 'mystery_box', name: '🎁 Hộp Quà Bí Ẩn' },
        { id: 'reverse_card', name: '🔀 Thẻ Đảo Ngược Ngôn Từ' },
        { id: 'freeze_card', name: '🧊 Bom Băng Giá Khóa Cần 2m' },
        { id: 'steal_fish_card', name: '🦹 Bàn Tay Đạo Tặc Móc Trộm Cá' },
        { id: 'fake_nitro', name: '💎 Thẻ Fake Nitro Rickroll' },
        { id: 'frog_potion', name: '🐸 Thuốc Biến Nạn Nhân Thành Ếch' },
        { id: 'slap_fish', name: '🐟 Cá Hồi Tát Mặt' },
        { id: 'cursed_bait', name: '🪱 Mồi Câu Nguyền Rủa 100% Rác' },
        { id: 'troll_box', name: '📦 Hộp Quà Lừa Tình Hù Dọa' },
        { id: 'key_silver', name: '🔑 Chìa Khóa Bạc' },
        { id: 'key_shipwreck', name: '🗝️ Chìa Khóa Tàu Cổ' },
        { id: 'key_gold', name: '👑 Chìa Khóa Hoàng Gia' },
        { id: 'key_abyss', name: '🐙 Chìa Khóa Vực Thẳm' },
        { id: 'key_void', name: '🌌 Chìa Khóa Hư Không' },
        { id: 'pearl_ancient', name: '🔮 Ngọc Trai Cổ Đại' },
        { id: 'treasure_map', name: '🗺️ Bản Đồ Kho Báu (+100% Luck)' },
        { id: 'relic_sea_stone', name: '🗿 Đá Trấn Hải (Bảo Toàn Bền)' },
        { id: 'relic_golden_scale', name: '🪙 Vảy Rồng Vàng (+50% Giá Cá)' },
        { id: 'ring_bronze', name: '💍 Nhẫn Đồng Đôi Kết Hôn' },
        { id: 'ring_silver', name: '💍 Nhẫn Bạc Tình Yêu Vĩnh Cửu' },
        { id: 'ring_gold', name: '💍 Nhẫn Vàng Hoàng Triều' },
        { id: 'ring_diamond', name: '💎 Nhẫn Kim Cương Đính Hôn' },
        { id: 'love_chocolate', name: '🍫 Hộp Socola Tình Yêu' },
        { id: 'love_flower', name: '💐 Bó Hoa Hồng Lãng Mạn' },
        { id: 'love_teddy', name: '🧸 Gấu Bông Đáng Yêu' }
    ]
};

function afOnGiftcodeCategoryChange() {
    const cat = document.getElementById('afGcCatSelect')?.value || 'rods';
    const itemSel = document.getElementById('afGcItemSelect');
    const itemGroup = document.getElementById('afGcItemSelectGroup');
    const customGroup = document.getElementById('afGcCustomIdGroup');
    const gearExtra = document.getElementById('afGcGearExtraOptions');
    const amtInput = document.getElementById('afGcAmtInput');

    
    if (cat === 'custom_id') {
        if (itemGroup) itemGroup.style.display = 'none';
        if (customGroup) customGroup.style.display = 'block';
    } else {
        if (itemGroup) itemGroup.style.display = 'block';
        if (customGroup) customGroup.style.display = 'none';
    }

    
    const isGear = (cat === 'rods' || cat === 'picks' || cat === 'pets' || cat === 'custom_id');
    if (gearExtra) {
        gearExtra.style.display = isGear ? 'flex' : 'none';
    }

    if (!itemSel) return;

    let items = GIFTCODE_ITEMS_CATALOG[cat] ? [...GIFTCODE_ITEMS_CATALOG[cat]] : [];

    
    const dynFishing = state.adminFishing?.catalogs || {};
    if (cat === 'rods' && dynFishing.rods) {
        const existingIds = new Set(items.map(it => it.id));
        Object.entries(dynFishing.rods).forEach(([id, r]) => {
            if (!existingIds.has(id)) items.push({ id, name: r.name || id });
        });
    } else if (cat === 'baits' && dynFishing.baits) {
        const existingIds = new Set(items.map(it => it.id));
        Object.entries(dynFishing.baits).forEach(([id, b]) => {
            if (!existingIds.has(id)) items.push({ id, name: b.name || id });
        });
    } else if (cat === 'chests' && dynFishing.chests) {
        const existingIds = new Set(items.map(it => it.id));
        Object.entries(dynFishing.chests).forEach(([id, c]) => {
            if (!existingIds.has(id)) items.push({ id, name: c.name || id });
        });
    } else if (cat === 'pets' && dynFishing.pets) {
        const existingIds = new Set(items.map(it => it.id));
        Object.entries(dynFishing.pets).forEach(([id, p]) => {
            if (!existingIds.has(id)) items.push({ id, name: p.name || id });
        });
    }

    itemSel.innerHTML = items.map(it => `<option value="${it.id}">${escapeHtml(it.name)}</option>`).join('');

    
    if ((cat === 'rods' || cat === 'picks' || cat === 'pets') && amtInput) {
        amtInput.value = '1';
    }
}

function afAddGiftcodeItem() {
    const cat = document.getElementById('afGcCatSelect')?.value || 'rods';
    const itemSel = document.getElementById('afGcItemSelect');
    const amt = Math.max(1, parseInt(document.getElementById('afGcAmtInput')?.value || '1', 10));

    let itemId = '';
    let itemName = '';

    if (cat === 'custom_id') {
        itemId = document.getElementById('afGcCustomIdInput')?.value.trim();
        if (!itemId) {
            showToast('Vui lòng nhập Mã ID tùy chỉnh!', 'warning');
            return;
        }
        itemName = `🏷️ Custom: ${itemId}`;
    } else {
        itemId = itemSel?.value;
        itemName = itemSel?.options[itemSel.selectedIndex]?.text || itemId;
        if (!itemId) {
            showToast('Vui lòng chọn vật phẩm muốn thêm!', 'warning');
            return;
        }
    }

    const refine = Math.min(300, Math.max(0, parseInt(document.getElementById('afGcRefineInput')?.value || '0', 10)));
    const stars = Math.min(20, Math.max(0, parseInt(document.getElementById('afGcStarsInput')?.value || '0', 10)));

    if (!state.adminFishing.giftcodeRewards) state.adminFishing.giftcodeRewards = [];

    const isGear = (cat === 'rods' || cat === 'picks' || cat === 'pets' || cat === 'custom_id');
    if (isGear && (refine > 0 || stars > 0)) {
        state.adminFishing.giftcodeRewards.push({
            category: cat,
            id: itemId,
            name: itemName,
            amount: amt,
            refine: refine,
            stars: stars
        });
    } else {
        const existing = state.adminFishing.giftcodeRewards.find(r => r.category === cat && r.id === itemId && (r.refine || 0) === refine && (r.stars || 0) === stars);
        if (existing) {
            existing.amount += amt;
        } else {
            state.adminFishing.giftcodeRewards.push({
                category: cat,
                id: itemId,
                name: itemName,
                amount: amt,
                refine: refine,
                stars: stars
            });
        }
    }

    renderGiftcodeRewardsList();
    const gearTag = (refine > 0 || stars > 0) ? ` (+${refine} | ${stars}⭐)` : '';
    showToast(`Đã thêm ${amt}x ${itemName}${gearTag} vào mã code!`, 'success');
}

function afRemoveGiftcodeItem(idx) {
    if (!state.adminFishing.giftcodeRewards) return;
    state.adminFishing.giftcodeRewards.splice(idx, 1);
    renderGiftcodeRewardsList();
}

function renderGiftcodeRewardsList() {
    const container = document.getElementById('afGcRewardsContainer');
    const badge = document.getElementById('afGcItemCountBadge');
    if (!container) return;

    const rewards = state.adminFishing.giftcodeRewards || [];
    if (badge) badge.innerText = `${rewards.length} phần thưởng`;

    if (rewards.length === 0) {
        container.innerHTML = '<div id="afGcRewardsEmptyText" style="font-size: 0.8rem; color: var(--text-dim); width: 100%; text-align: center;">Chưa thêm vật phẩm đính kèm nào (mã chỉ tặng tiền/xu nếu có).</div>';
        return;
    }

    container.innerHTML = rewards.map((r, i) => {
        const isEquipment = (r.category === 'rods' || r.category === 'picks');
        const isPet = (r.category === 'pets');
        const isFarm = (r.category === 'farm_seeds' || r.category === 'farm_crops' || r.category === 'farm_tools' || r.category === 'fertilizers');
        const isCustom = (r.category === 'custom_id');

        const badgeStyle = isEquipment 
            ? 'background: rgba(168, 85, 247, 0.2); border: 1px solid rgba(168, 85, 247, 0.45); color: #c084fc;' 
            : isPet 
            ? 'background: rgba(236, 72, 153, 0.2); border: 1px solid rgba(236, 72, 153, 0.45); color: #f472b6;' 
            : isFarm
            ? 'background: rgba(34, 197, 94, 0.2); border: 1px solid rgba(34, 197, 94, 0.45); color: #4ade80;'
            : isCustom
            ? 'background: rgba(245, 158, 11, 0.2); border: 1px solid rgba(245, 158, 11, 0.45); color: #fbbf24;'
            : 'background: rgba(56, 189, 248, 0.15); border: 1px solid rgba(56, 189, 248, 0.35); color: #38bdf8;';
            
        const typeLabel = isEquipment ? '⚔️ Trang bị' : isPet ? '🐾 Thú cưng' : isFarm ? '🌾 Nông trại' : isCustom ? '🛠️ Custom' : '📦 Tiêu hao';

        const gearDetail = (r.refine > 0 || r.stars > 0) 
            ? `<span style="background: rgba(0,0,0,0.3); padding: 1px 5px; border-radius: 4px; font-size: 0.72rem; color: #fde047; margin-left: 4px;">(+${r.refine || 0} | ${r.stars || 0}⭐)</span>` 
            : '';

        return `
            <div style="display: inline-flex; align-items: center; gap: 6px; padding: 4px 10px; ${badgeStyle} border-radius: 20px; font-size: 0.8rem;">
                <span style="font-size: 0.7rem; opacity: 0.85; text-transform: uppercase;">[${typeLabel}]</span>
                <strong>${escapeHtml(r.name)}</strong>${gearDetail}
                <span style="background: rgba(255,255,255,0.18); padding: 1px 6px; border-radius: 10px; font-weight: 700; color: #ffd700;">x${r.amount}</span>
                <button type="button" onclick="afRemoveGiftcodeItem(${i})" style="background: none; border: none; color: #ef4444; font-weight: bold; cursor: pointer; padding: 0 2px;" title="Xóa">✕</button>
            </div>
        `;
    }).join('');
}

function afGenerateRandomCode() {
    const chars = 'ABCDEFGHJKLMNPQRSTUVWXYZ23456789';
    let code = 'SAKURA-';
    for (let i = 0; i < 6; i++) {
        code += chars.charAt(Math.floor(Math.random() * chars.length));
    }
    const input = document.getElementById('afGcCode');
    if (input) input.value = code;
}

async function afSubmitCreateGiftcode() {
    const code = document.getElementById('afGcCode')?.value.trim().toUpperCase();
    const coins = parseInt(document.getElementById('afGcCoins')?.value || '0', 10);
    const xu = parseInt(document.getElementById('afGcXu')?.value || '0', 10);
    const max_uses = parseInt(document.getElementById('afGcMaxUses')?.value || '0', 10);
    const hours = parseFloat(document.getElementById('afGcHours')?.value || '24');
    const broadcast = document.getElementById('afGcBroadcast')?.checked ?? true;

    const baits = {};
    const chests = {};
    const rods = [];
    const picks = [];
    const pets = [];
    const items = {};
    const ores = {};
    const supplies = {};
    const farm_seeds = {};
    const farm_crops = {};
    const farm_tools = {};
    const fertilizers = {};
    const custom_items = [];

    const rewardsList = state.adminFishing.giftcodeRewards || [];
    rewardsList.forEach(r => {
        const refine = r.refine || 0;
        const stars = r.stars || 0;

        if (r.category === 'baits') baits[r.id] = (baits[r.id] || 0) + r.amount;
        else if (r.category === 'chests') chests[r.id] = (chests[r.id] || 0) + r.amount;
        else if (r.category === 'rods') {
            for (let i = 0; i < r.amount; i++) {
                if (refine > 0 || stars > 0) {
                    rods.push({ id: r.id, name: r.name, refine: refine, stars: stars });
                } else {
                    rods.push(r.id);
                }
            }
        }
        else if (r.category === 'picks') {
            for (let i = 0; i < r.amount; i++) {
                if (refine > 0 || stars > 0) {
                    picks.push({ id: r.id, name: r.name, refine: refine, stars: stars });
                } else {
                    picks.push(r.id);
                }
            }
        }
        else if (r.category === 'pets') {
            for (let i = 0; i < r.amount; i++) {
                if (refine > 0 || stars > 0) {
                    pets.push({ id: r.id, name: r.name, refine: refine, stars: stars });
                } else {
                    pets.push(r.id);
                }
            }
        }
        else if (r.category === 'items') items[r.id] = (items[r.id] || 0) + r.amount;
        else if (r.category === 'ores') ores[r.id] = (ores[r.id] || 0) + r.amount;
        else if (r.category === 'supplies') supplies[r.id] = (supplies[r.id] || 0) + r.amount;
        else if (r.category === 'farm_seeds') farm_seeds[r.id] = (farm_seeds[r.id] || 0) + r.amount;
        else if (r.category === 'farm_crops') farm_crops[r.id] = (farm_crops[r.id] || 0) + r.amount;
        else if (r.category === 'farm_tools') farm_tools[r.id] = (farm_tools[r.id] || 0) + r.amount;
        else if (r.category === 'fertilizers') fertilizers[r.id] = (fertilizers[r.id] || 0) + r.amount;
        else if (r.category === 'custom_id') {
            custom_items.push({
                id: r.id,
                name: r.name,
                amount: r.amount,
                refine: refine,
                stars: stars
            });
        }
    });

    const res = await apiRequest('/api/fishing/admin/giftcodes/create', 'POST', {
        code,
        coins,
        xu,
        max_uses,
        hours,
        broadcast,
        baits,
        chests,
        rods,
        picks,
        pets,
        items,
        ores,
        supplies,
        farm_seeds,
        farm_crops,
        farm_tools,
        fertilizers,
        custom_items
    });

    if (res.ok) {
        showToast(res.message || 'Tạo giftcode thành công!', 'success');
        state.adminFishing.giftcodeRewards = [];
        renderGiftcodeRewardsList();
        loadAdminFishGiftcodes();
        afGenerateRandomCode();
    } else {
        showToast(res.error || 'Lỗi tạo giftcode', 'error');
    }
}

async function afDeleteGiftcode(code) {
    if (!confirm(`Bạn có chắc muốn xóa vĩnh viễn Giftcode [${code}]?`)) return;
    const res = await apiRequest('/api/fishing/admin/giftcodes/delete', 'POST', { code });
    if (res.ok) {
        showToast(res.message || 'Đã xóa Giftcode', 'success');
        loadAdminFishGiftcodes();
    }
}

async function loadAdminDailyGiftcode() {
    const res = await apiRequest('/api/fishing/admin/daily-giftcode');
    if (!res.ok) {
        showToast('Lỗi tải Daily Giftcode: ' + (res.error || 'Thất bại'), 'error');
        return;
    }
    const d = res.daily || {};
    const codeDisplay = document.getElementById('dailyCodeDisplay');
    const usesDisplay = document.getElementById('dailyUsesDisplay');
    const statusBadge = document.getElementById('dailyStatusBadge');
    const expiryDisplay = document.getElementById('dailyExpiryDisplay');

    if (codeDisplay) codeDisplay.innerText = d.today_code_name || '—';
    if (usesDisplay) usesDisplay.innerText = `${(d.used_count || 0).toLocaleString()} / ${(d.max_uses || 1000).toLocaleString()}`;

    if (statusBadge) {
        if (!d.exists) {
            statusBadge.className = 'badge badge-warning';
            statusBadge.innerText = '🟡 Chưa phát hôm nay';
        } else if (d.is_expired) {
            statusBadge.className = 'badge badge-danger';
            statusBadge.innerText = '🔴 Đã hết hạn (sau 20h30)';
        } else {
            statusBadge.className = 'badge badge-success';
            statusBadge.innerText = '🟢 Đang hoạt động';
        }
    }

    if (expiryDisplay && d.data && d.data.expires_at) {
        const expDate = new Date(d.data.expires_at * 1000);
        expiryDisplay.innerText = `Đến ${expDate.toLocaleTimeString('vi-VN')} (${expDate.toLocaleDateString('vi-VN')})`;
    }
}

async function generateDailyGiftcodeNow() {
    const force = document.getElementById('dailyForceCheck')?.checked || false;
    const broadcast = document.getElementById('dailyBroadcastCheck')?.checked || true;

    if (!confirm('Bạn có chắc muốn phát Daily Giftcode hôm nay ngay bây giờ?')) return;

    showToast('Đang phát Daily Giftcode...', 'info');
    const res = await apiRequest('/api/fishing/admin/daily-giftcode/generate', 'POST', {
        force: force,
        broadcast: broadcast
    });

    if (res.ok) {
        showToast(res.message || 'Phát Daily Giftcode thành công!', 'success');
        loadAdminDailyGiftcode();
    } else {
        showToast('Lỗi: ' + (res.error || 'Không thể tạo'), 'error');
    }
}


function afToggleHiddenBox(prefix) {
    const chk = document.getElementById(`${prefix}Hidden`);
    const box = document.getElementById(`${prefix}SourceBox`);
    if (box) box.style.display = (chk && chk.checked) ? 'block' : 'none';
}

function afToggleExpiryBox(prefix) {
    const chk = document.getElementById(`${prefix}HasExpiry`);
    const box = document.getElementById(`${prefix}ExpiryBox`);
    if (box) box.style.display = (chk && chk.checked) ? 'block' : 'none';
}

function afToggleCheatSheet() {
    const el = document.getElementById('afCheatSheetContent');
    if (el) el.style.display = (el.style.display === 'none') ? 'block' : 'none';
}

function afUpdateTrollActionHint() {
    const sel = document.getElementById('afNewTrollActionKey');
    const valInput = document.getElementById('afNewTrollActionVal');
    const label = document.getElementById('afNewTrollActionValLabel');
    if (!sel || !valInput) return;
    const key = sel.value;
    if (['FREEZE_FISHING', 'MUTE', 'FROG', 'REVERSE_TEXT'].includes(key)) {
        if (label) label.innerText = 'Thời lượng (Phút):';
        valInput.value = '10';
        valInput.placeholder = 'Số phút hiệu lực (VD: 10)';
    } else if (key === 'STEAL_COIN' || key === 'BOMB') {
        if (label) label.innerText = 'Số Coin / %:';
        valInput.value = '15000';
        valInput.placeholder = 'VD: 15000 hoặc 20%';
    } else if (key === 'RENAME') {
        if (label) label.innerText = 'Biệt danh mới:';
        valInput.value = 'Cá Con Lạc Lối';
        valInput.placeholder = 'Tên đặt cho nạn nhân';
    } else if (key === 'CURSED_BAIT') {
        if (label) label.innerText = 'Số lần câu bị nguyền:';
        valInput.value = '3';
        valInput.placeholder = 'VD: 3';
    } else {
        if (label) label.innerText = 'Tham số / Thông điệp:';
        valInput.value = 'Troll!';
        valInput.placeholder = 'Tùy chọn';
    }
}

function afSwitchDexCategory(cat) {
    state.adminFishing.activeDexCat = cat || 'all';
    const catKeys = ['all', 'fish', 'rod', 'bait', 'pet', 'chest', 'troll', 'item'];
    catKeys.forEach(k => {
        const btn = document.getElementById(`afDexCat${k.charAt(0).toUpperCase() + k.slice(1)}`);
        if (btn) btn.classList.toggle('active', k === state.adminFishing.activeDexCat);
    });
    afFilterFishList();
}

function renderAdminFishTable() {
    afFilterFishList();
}

function afFilterFishList() {
    const fishList = state.adminFishing.fishList || [];
    const catalogs = state.adminFishing.catalogs || {};
    const search = (document.getElementById('afFishSearchInput')?.value || '').toLowerCase().trim();
    const rarityFilter = document.getElementById('afFishRarityFilter')?.value || 'all';
    const originFilter = document.getElementById('afDexOriginFilter')?.value || 'all';
    const cat = state.adminFishing.activeDexCat || 'all';

    
    const allItems = [];

    
    fishList.forEach(f => {
        allItems.push({
            type: 'fish',
            typeLabel: '🐟 Cá Biển',
            id: f.name,
            name: f.name || 'Cá Biển',
            rarity: (f.rarity || 'common').toLowerCase(),
            priceText: `${Number(f.price || 0).toLocaleString()} Coins`,
            statText: `Tỉ lệ câu: ${f.chance || 0}%`,
            desc: f.description || 'Sinh vật biển hoang dã',
            is_hidden: !!f.is_hidden,
            obtain_source: f.obtain_source || 'Câu cá tự nhiên',
            has_expiry: false,
            duration_days: 0
        });
    });

    
    Object.entries(catalogs.rods || {}).forEach(([id, r]) => {
        allItems.push({
            type: 'rod',
            typeLabel: '🎣 Cần Câu',
            id: id,
            name: r.name || id,
            rarity: (r.rarity || 'rare').toLowerCase(),
            priceText: `${Number(r.price || 0).toLocaleString()} ${r.currency === 'xu' ? '💎 Xu' : '🪙 Coins'}`,
            statText: `May mắn: +${r.luck || 0} | Độ bền: ${r.durability || 100}`,
            desc: `${r.desc || 'Cần câu cá'}${r.level ? ' | Yêu cầu Lv.' + r.level : ''}`,
            is_hidden: !!r.is_hidden,
            obtain_source: r.obtain_source || (r.is_hidden ? 'Rương / Sự kiện' : 'Shop Cần Câu'),
            has_expiry: !!r.has_expiry,
            duration_days: r.duration_days || 0,
            renewable: r.renewable !== false
        });
    });

    
    Object.entries(catalogs.baits || {}).forEach(([id, b]) => {
        allItems.push({
            type: 'bait',
            typeLabel: '🪱 Mồi Câu',
            id: id,
            name: b.name || id,
            rarity: 'rare',
            priceText: `${Number(b.price || 0).toLocaleString()} ${b.currency === 'xu' ? '💎 Xu' : '🪙 Coins'}`,
            statText: `May mắn: +${b.luck || 0}`,
            desc: b.desc || 'Mồi câu chuyên dụng tăng tỷ lệ cắn câu hiếm',
            is_hidden: !!b.is_hidden,
            obtain_source: b.obtain_source || (b.is_hidden ? 'Mở rương / Quà tặng' : 'Shop Mồi Câu'),
            has_expiry: !!b.has_expiry,
            duration_days: b.duration_days || 0,
            renewable: !!b.renewable
        });
    });

    
    Object.entries(catalogs.pets || {}).forEach(([id, p]) => {
        allItems.push({
            type: 'pet',
            typeLabel: '🐾 Thú Cưng',
            id: id,
            name: p.name || id,
            rarity: 'epic',
            priceText: `${Number(p.price || 0).toLocaleString()} ${p.currency === 'coins' ? '🪙 Coins' : '💎 Xu'}`,
            statText: `Luck +${p.luck || 0}% | Mồi +${p.bait_bonus || 0}% | Bán x${p.price_multiplier || 1.0}`,
            desc: p.desc || 'Thú cưng trợ thủ đắc lực bên cần thủ',
            is_hidden: !!p.is_hidden,
            obtain_source: p.obtain_source || (p.is_hidden ? 'Ấp từ Rương Thần Thoại' : 'Cửa Hàng Thú Cưng'),
            has_expiry: !!p.has_expiry,
            duration_days: p.duration_days || 0,
            renewable: p.renewable !== false
        });
    });

    
    Object.entries(catalogs.chests || {}).forEach(([id, c]) => {
        allItems.push({
            type: 'chest',
            typeLabel: '📦 Rương Báu',
            id: id,
            name: c.name || id,
            rarity: 'legendary',
            priceText: c.req_key ? `Cần ${c.req_key}` : '🔓 Mở Tự Do',
            statText: `Rơi: ${c.chance || 0}% | Tiền: ${Number(c.min_coins || 0).toLocaleString()}~${Number(c.max_coins || 0).toLocaleString()}`,
            desc: c.desc || 'Rương kho báu chứa mồi, vật phẩm và pet quý',
            is_hidden: !!c.is_hidden,
            obtain_source: c.obtain_source || 'Vớt được khi câu cá',
            has_expiry: false,
            duration_days: 0
        });
    });

    
    Object.entries(catalogs.items || {}).forEach(([id, it]) => {
        allItems.push({
            type: (it.action_key || id.includes('troll') || id.includes('frog') || id.includes('slap')) ? 'troll' : 'item',
            typeLabel: (it.action_key || id.includes('troll')) ? '🃏 Vật Phẩm Troll' : '🎒 Túi & Tiện Ích',
            id: id,
            name: it.name || id,
            rarity: 'admin',
            priceText: `${Number(it.price || 0).toLocaleString()} ${it.currency === 'xu' ? '💎 Xu' : '🪙 Coins'}`,
            statText: it.action_key ? `Key: ${it.action_key}` : (it.extra_slots ? `+${it.extra_slots} Ô chứa` : 'Tiện ích'),
            desc: it.desc || 'Vật phẩm hỗ trợ hoặc troll tương tác người chơi',
            is_hidden: !!it.is_hidden,
            obtain_source: it.obtain_source || (it.is_hidden ? 'Rương Hỗn Loạn / Drop hiếm' : 'Shop Đồ Chơi'),
            has_expiry: !!it.has_expiry,
            duration_days: it.duration_days || 0,
            renewable: !!it.renewable
        });
    });

    
    const filtered = allItems.filter(item => {
        
        if (cat !== 'all') {
            if (cat === 'troll' && item.type !== 'troll') return false;
            if (cat === 'item' && item.type !== 'item') return false;
            if (cat !== 'troll' && cat !== 'item' && item.type !== cat) return false;
        }

        
        if (rarityFilter !== 'all' && item.rarity !== rarityFilter) return false;

        
        if (originFilter === 'hidden' && !item.is_hidden) return false;
        if (originFilter === 'shop' && item.is_hidden) return false;
        if (originFilter === 'drop' && !item.obtain_source.toLowerCase().includes('câu') && !item.obtain_source.toLowerCase().includes('rơi') && !item.obtain_source.toLowerCase().includes('rương')) return false;

        
        if (search) {
            const str = `${item.name} ${item.desc} ${item.id} ${item.obtain_source}`.toLowerCase();
            if (!str.includes(search)) return false;
        }

        return true;
    });

    const totalEl = document.getElementById('afFishTotalCount');
    if (totalEl) totalEl.innerText = filtered.length;

    const tbody = document.getElementById('afFishTableBody');
    if (!tbody) return;

    if (filtered.length === 0) {
        tbody.innerHTML = '<tr><td colspan="7" style="text-align:center; padding:30px; color:var(--text-dim);">Không tìm thấy mục nào phù hợp với bộ lọc trong Bách Khoa.</td></tr>';
        return;
    }

    tbody.innerHTML = filtered.map((item, idx) => {
        const r = RARITY_BADGES[item.rarity] || RARITY_BADGES.common;
        
        let originBadge = '';
        if (item.is_hidden) {
            originBadge = `<span class="badge" style="background:rgba(236,72,153,0.15); color:var(--sakura-pink); border:1px solid rgba(236,72,153,0.3); font-size:0.75rem;" title="${escapeHtml(item.obtain_source)}">🔮 Ẩn (${escapeHtml(item.obtain_source)})</span>`;
        } else {
            originBadge = `<span class="badge" style="background:rgba(34,197,94,0.15); color:#4ade80; border:1px solid rgba(34,197,94,0.3); font-size:0.75rem;">🛒 Shop (${escapeHtml(item.priceText)})</span>`;
        }

        let expiryBadge = '';
        if (item.has_expiry) {
            expiryBadge = `<span style="display:inline-block; font-size:0.75rem; color:#f59e0b; background:rgba(245,158,11,0.1); padding:2px 6px; border-radius:4px; margin-top:3px; border:1px solid rgba(245,158,11,0.25);">⏳ HSD: ${item.duration_days} ngày (${item.renewable ? 'Gia hạn được' : 'Không gia hạn'})</span>`;
        } else {
            expiryBadge = `<span style="display:inline-block; font-size:0.72rem; color:var(--text-dim); margin-top:3px;">♾️ Vĩnh viễn</span>`;
        }

        return `
            <tr>
                <td style="color:var(--text-dim); font-size:0.85rem;">${idx + 1}</td>
                <td>
                    <strong style="color:var(--text-main); font-size:0.95rem;">${escapeHtml(item.name)}</strong>
                    <div style="font-size:0.76rem; color:var(--text-dim); font-family:monospace;">${escapeHtml(item.id)}</div>
                </td>
                <td><span class="badge" style="background:rgba(255,255,255,0.06); color:var(--text-main); font-size:0.78rem;">${item.typeLabel}</span></td>
                <td><span class="badge" style="background:${r.bg}; color:${r.color}; border:1px solid ${r.border}; font-size:0.78rem;">${r.label}</span></td>
                <td>${originBadge}</td>
                <td style="color:var(--accent-cyan); font-weight:500; font-size:0.85rem;">${escapeHtml(item.statText)}</td>
                <td style="font-size:0.82rem; color:var(--text-dim); max-width:280px;">
                    <div>${escapeHtml(item.desc)}</div>
                    <div>${expiryBadge}</div>
                </td>
            </tr>
        `;
    }).join('');
}


function afUpdateNewChestPreview() {
    const name = document.getElementById('afNewChestName')?.value.trim() || '💎 Rương Kho Báu Mẫu';
    const id = document.getElementById('afNewChestId')?.value.trim() || 'chest_custom';
    const chance = parseFloat(document.getElementById('afNewChestChance')?.value || '3.5');
    const minCoin = parseInt(document.getElementById('afNewChestMinCoin')?.value || '10000');
    const maxCoin = parseInt(document.getElementById('afNewChestMaxCoin')?.value || '50000');
    const reqKey = document.getElementById('afNewChestReqKey')?.value || '';
    const desc = document.getElementById('afNewChestDesc')?.value.trim() || 'Rương báu bí mật!';
    const isHidden = !!document.getElementById('afNewChestHidden')?.checked;

    const titleEl = document.getElementById('afPreviewChestTitle');
    if (titleEl) titleEl.innerText = name;

    const idEl = document.getElementById('afPreviewChestId');
    if (idEl) idEl.innerText = id;

    const descEl = document.getElementById('afPreviewChestDesc');
    if (descEl) descEl.innerText = desc;

    const badgeEl = document.getElementById('afPreviewChestBadge');
    if (badgeEl) badgeEl.innerText = `${chance}% Drop`;

    const keyEl = document.getElementById('afPreviewChestKey');
    if (keyEl) keyEl.innerText = reqKey ? `🗝️ ${reqKey}` : '🔓 Mở tự do';

    const coinsEl = document.getElementById('afPreviewChestCoins');
    if (coinsEl) coinsEl.innerText = `${Number(minCoin).toLocaleString()} ~ ${Number(maxCoin).toLocaleString()} Coins`;

    const rateEl = document.getElementById('afPreviewChestRate');
    if (rateEl) rateEl.innerText = `${chance}% cơ hội vớt khi câu`;

    const statusEl = document.getElementById('afPreviewChestStatus');
    if (statusEl) {
        if (isHidden) {
            statusEl.innerText = '🔮 Rương Ẩn Đặc Biệt';
            statusEl.style.color = '#ec4899';
        } else {
            statusEl.innerText = '✨ Hiển thị trong Bách Khoa';
            statusEl.style.color = '#38bdf8';
        }
    }
}


function afPopulateChestPools() {
    const catalogs = state.adminFishing.catalogs || {};

    
    const baitBox = document.getElementById('afChestPoolBaits');
    if (baitBox) {
        const baits = catalogs.baits || {};
        const entries = Object.entries(baits);
        if (entries.length === 0) {
            baitBox.innerHTML = '<span style="color:var(--text-dim); font-size:0.8rem;">Chưa có mồi câu nào</span>';
        } else {
            baitBox.innerHTML = entries.map(([id, b]) => `
                <label style="display:inline-flex; align-items:center; gap:5px; font-size:0.8rem; background:rgba(255,255,255,0.03); padding:4px 8px; border-radius:6px; cursor:pointer;">
                    <input type="checkbox" name="afChestBaitChoice" value="${id}">
                    <span>${escapeHtml(b.name || id)}</span>
                </label>
            `).join('');
        }
    }

    
    const petBox = document.getElementById('afChestPoolPets');
    if (petBox) {
        const pets = catalogs.pets || {};
        const entries = Object.entries(pets);
        if (entries.length === 0) {
            petBox.innerHTML = '<span style="color:var(--text-dim); font-size:0.8rem;">Chưa có thú cưng nào</span>';
        } else {
            petBox.innerHTML = entries.map(([id, p]) => `
                <label style="display:inline-flex; align-items:center; gap:5px; font-size:0.8rem; background:rgba(255,255,255,0.03); padding:4px 8px; border-radius:6px; cursor:pointer;">
                    <input type="checkbox" name="afChestPetChoice" value="${id}">
                    <span>${escapeHtml(p.name || id)}</span>
                </label>
            `).join('');
        }
    }

    
    const rodBox = document.getElementById('afChestPoolRods');
    if (rodBox) {
        const rods = catalogs.rods || {};
        const entries = Object.entries(rods);
        if (entries.length === 0) {
            rodBox.innerHTML = '<span style="color:var(--text-dim); font-size:0.8rem;">Chưa có cần câu nào</span>';
        } else {
            rodBox.innerHTML = entries.map(([id, r]) => `
                <label style="display:inline-flex; align-items:center; gap:5px; font-size:0.8rem; background:rgba(255,255,255,0.03); padding:4px 8px; border-radius:6px; cursor:pointer;">
                    <input type="checkbox" name="afChestRodChoice" value="${id}">
                    <span>${escapeHtml(r.name || id)}</span>
                </label>
            `).join('');
        }
    }

    
    const itemBox = document.getElementById('afChestPoolItems');
    if (itemBox) {
        const items = catalogs.items || {};
        const entries = Object.entries(items);
        if (entries.length === 0) {
            itemBox.innerHTML = '<span style="color:var(--text-dim); font-size:0.8rem;">Chưa có vật phẩm tiện ích nào</span>';
        } else {
            itemBox.innerHTML = entries.map(([id, it]) => `
                <label style="display:inline-flex; align-items:center; gap:5px; font-size:0.8rem; background:rgba(255,255,255,0.03); padding:4px 8px; border-radius:6px; cursor:pointer;">
                    <input type="checkbox" name="afChestItemChoice" value="${id}">
                    <span>${escapeHtml(it.name || id)}</span>
                </label>
            `).join('');
        }
    }
}

function afUpdateNewFishPreview() {
    const name = document.getElementById('afNewFishName')?.value.trim() || 'Cá Mẫu';
    const rarity = document.getElementById('afNewFishRarity')?.value || 'common';
    const price = parseInt(document.getElementById('afNewFishPrice')?.value || '50000');
    const chance = parseFloat(document.getElementById('afNewFishChance')?.value || '25');
    const desc = document.getElementById('afNewFishDesc')?.value.trim() || 'Mô tả sinh vật biển sẽ xuất hiện tại đây.';

    const r = RARITY_BADGES[rarity] || RARITY_BADGES.common;
    const box = document.getElementById('afPreviewBox');
    if (box) {
        box.style.borderColor = r.color;
        box.style.boxShadow = `0 0 25px ${r.bg}`;
    }

    const title = document.getElementById('afPreviewTitle');
    if (title) title.innerText = name;

    const badge = document.getElementById('afPreviewBadge');
    if (badge) {
        badge.innerText = r.label;
        badge.style.background = r.bg;
        badge.style.color = r.color;
        badge.style.border = `1px solid ${r.border}`;
    }

    const priceEl = document.getElementById('afPreviewPrice');
    if (priceEl) priceEl.innerText = Number(price).toLocaleString();

    const chanceEl = document.getElementById('afPreviewChance');
    if (chanceEl) chanceEl.innerText = chance;

    const descEl = document.getElementById('afPreviewDesc');
    if (descEl) descEl.innerText = desc;
}

async function afSubmitAddNewFish() {
    const name = document.getElementById('afNewFishName')?.value.trim();
    if (!name) return showToast('Vui lòng nhập tên loài cá kèm emoji', 'warning');

    const rarity = document.getElementById('afNewFishRarity')?.value || 'common';
    const price = parseInt(document.getElementById('afNewFishPrice')?.value || '0');
    const chance = parseFloat(document.getElementById('afNewFishChance')?.value || '0');
    const description = document.getElementById('afNewFishDesc')?.value.trim();

    if (price < 0) return showToast('Giá bán không được âm', 'warning');
    if (chance <= 0) return showToast('Tỉ lệ xuất hiện phải lớn hơn 0', 'warning');

    const res = await apiRequest('/api/fishing/admin/add-fish', 'POST', {
        name,
        rarity,
        price,
        chance,
        description
    });

    if (res.ok) {
        showToast(res.message || 'Thêm cá mới thành công!', 'success');
        document.getElementById('afNewFishName').value = '';
        document.getElementById('afNewFishDesc').value = '';
        await loadAdminFishList();
        switchAdminFishTab('list');
    }
}


async function afSubmitAddNewRod() {
    const name = document.getElementById('afNewRodName')?.value.trim();
    if (!name) return showToast('Vui lòng nhập tên cần câu', 'warning');
    const id = document.getElementById('afNewRodId')?.value.trim();
    const price = parseInt(document.getElementById('afNewRodPrice')?.value || '10000');
    const currency = document.getElementById('afNewRodCurrency')?.value || 'coins';
    const level = parseInt(document.getElementById('afNewRodLevel')?.value || '1');
    const luck = parseInt(document.getElementById('afNewRodLuck')?.value || '10');
    const durability = parseInt(document.getElementById('afNewRodDurability')?.value || '100');
    const rarity = document.getElementById('afNewRodRarity')?.value || 'common';

    const is_hidden = !!document.getElementById('afNewRodHidden')?.checked;
    const obtain_source = document.getElementById('afNewRodSource')?.value.trim();
    const has_expiry = !!document.getElementById('afNewRodHasExpiry')?.checked;
    const duration_days = parseInt(document.getElementById('afNewRodDurationDays')?.value || '7');
    const renewable = document.getElementById('afNewRodRenewable')?.value === 'true';
    const renew_price = parseInt(document.getElementById('afNewRodRenewPrice')?.value || '20000');
    const renew_currency = document.getElementById('afNewRodRenewCurrency')?.value || 'coins';

    const res = await apiRequest('/api/fishing/admin/add-rod', 'POST', {
        id, name, price, currency, level, luck, durability, rarity,
        is_hidden, obtain_source, has_expiry, duration_days, renewable, renew_price, renew_currency
    });

    if (res.ok) {
        showToast(res.message || 'Thêm cần câu mới thành công!', 'success');
        const nEl = document.getElementById('afNewRodName'); if (nEl) nEl.value = '';
        const idEl = document.getElementById('afNewRodId'); if (idEl) idEl.value = '';
        await loadAdminFishList();
    }
}


async function afSubmitAddNewBait() {
    const name = document.getElementById('afNewBaitName')?.value.trim();
    if (!name) return showToast('Vui lòng nhập tên mồi câu', 'warning');
    const id = document.getElementById('afNewBaitId')?.value.trim();
    const price = parseInt(document.getElementById('afNewBaitPrice')?.value || '1000');
    const currency = document.getElementById('afNewBaitCurrency')?.value || 'coins';
    const luck = parseInt(document.getElementById('afNewBaitLuck')?.value || '10');

    const is_hidden = !!document.getElementById('afNewBaitHidden')?.checked;
    const obtain_source = document.getElementById('afNewBaitSource')?.value.trim();
    const has_expiry = !!document.getElementById('afNewBaitHasExpiry')?.checked;
    const duration_days = parseInt(document.getElementById('afNewBaitDurationDays')?.value || '3');
    const renewable = document.getElementById('afNewBaitRenewable')?.value === 'true';
    const renew_price = parseInt(document.getElementById('afNewBaitRenewPrice')?.value || '5000');
    const renew_currency = document.getElementById('afNewBaitRenewCurrency')?.value || 'coins';

    const res = await apiRequest('/api/fishing/admin/add-bait', 'POST', {
        id, name, price, currency, luck,
        is_hidden, obtain_source, has_expiry, duration_days, renewable, renew_price, renew_currency
    });

    if (res.ok) {
        showToast(res.message || 'Thêm mồi câu mới thành công!', 'success');
        const nEl = document.getElementById('afNewBaitName'); if (nEl) nEl.value = '';
        const idEl = document.getElementById('afNewBaitId'); if (idEl) idEl.value = '';
        await loadAdminFishList();
    }
}


async function afSubmitAddNewBag() {
    const name = document.getElementById('afNewBagName')?.value.trim();
    if (!name) return showToast('Vui lòng nhập tên túi cá', 'warning');
    const id = document.getElementById('afNewBagId')?.value.trim();
    const price = parseInt(document.getElementById('afNewBagPrice')?.value || '50000');
    const currency = document.getElementById('afNewBagCurrency')?.value || 'coins';
    const extra_slots = parseInt(document.getElementById('afNewBagSlots')?.value || '50');

    const is_hidden = !!document.getElementById('afNewBagHidden')?.checked;
    const obtain_source = document.getElementById('afNewBagSource')?.value.trim();
    const has_expiry = !!document.getElementById('afNewBagHasExpiry')?.checked;
    const duration_days = parseInt(document.getElementById('afNewBagDurationDays')?.value || '30');
    const renewable = document.getElementById('afNewBagRenewable')?.value === 'true';
    const renew_price = parseInt(document.getElementById('afNewBagRenewPrice')?.value || '50000');
    const renew_currency = document.getElementById('afNewBagRenewCurrency')?.value || 'coins';

    const res = await apiRequest('/api/fishing/admin/add-bag', 'POST', {
        id, name, price, currency, extra_slots,
        is_hidden, obtain_source, has_expiry, duration_days, renewable, renew_price, renew_currency
    });

    if (res.ok) {
        showToast(res.message || 'Thêm túi mới thành công!', 'success');
        const nEl = document.getElementById('afNewBagName'); if (nEl) nEl.value = '';
        const idEl = document.getElementById('afNewBagId'); if (idEl) idEl.value = '';
        await loadAdminFishList();
    }
}


async function afSubmitAddNewPet() {
    const name = document.getElementById('afNewPetName')?.value.trim();
    if (!name) return showToast('Vui lòng nhập tên thú cưng', 'warning');
    const id = document.getElementById('afNewPetId')?.value.trim();
    const price = parseInt(document.getElementById('afNewPetPrice')?.value || '250000');
    const currency = document.getElementById('afNewPetCurrency')?.value || 'xu';
    const luck = parseInt(document.getElementById('afNewPetLuck')?.value || '35');
    const bait_bonus = parseInt(document.getElementById('afNewPetBaitBonus')?.value || '20');
    const price_multiplier = parseFloat(document.getElementById('afNewPetPriceMulti')?.value || '1.25');
    const desc = document.getElementById('afNewPetDesc')?.value.trim();

    const is_hidden = !!document.getElementById('afNewPetHidden')?.checked;
    const obtain_source = document.getElementById('afNewPetSource')?.value.trim();
    const has_expiry = !!document.getElementById('afNewPetHasExpiry')?.checked;
    const duration_days = parseInt(document.getElementById('afNewPetDurationDays')?.value || '30');
    const renewable = document.getElementById('afNewPetRenewable')?.value === 'true';
    const renew_price = parseInt(document.getElementById('afNewPetRenewPrice')?.value || '50000');
    const renew_currency = document.getElementById('afNewPetRenewCurrency')?.value || 'xu';

    const res = await apiRequest('/api/fishing/admin/add-pet', 'POST', {
        id, name, price, currency, luck, bait_bonus, price_multiplier, desc,
        is_hidden, obtain_source, has_expiry, duration_days, renewable, renew_price, renew_currency
    });

    if (res.ok) {
        showToast(res.message || 'Thêm Thú Cưng thành công!', 'success');
        const nEl = document.getElementById('afNewPetName'); if (nEl) nEl.value = '';
        const idEl = document.getElementById('afNewPetId'); if (idEl) idEl.value = '';
        await loadAdminFishList();
    }
}


async function afSubmitAddNewTrollItem() {
    const name = document.getElementById('afNewTrollName')?.value.trim();
    if (!name) return showToast('Vui lòng nhập tên vật phẩm troll', 'warning');
    const id = document.getElementById('afNewTrollId')?.value.trim();
    const price = parseInt(document.getElementById('afNewTrollPrice')?.value || '30000');
    const currency = document.getElementById('afNewTrollCurrency')?.value || 'coins';
    const action_key = document.getElementById('afNewTrollActionKey')?.value || 'FREEZE_FISHING';
    const action_val = document.getElementById('afNewTrollActionVal')?.value.trim() || '10';
    const desc = document.getElementById('afNewTrollDesc')?.value.trim();

    const is_hidden = !!document.getElementById('afNewTrollHidden')?.checked;
    const obtain_source = document.getElementById('afNewTrollSource')?.value.trim();
    const has_expiry = !!document.getElementById('afNewTrollHasExpiry')?.checked;
    const duration_days = parseInt(document.getElementById('afNewTrollDurationDays')?.value || '7');
    const renewable = document.getElementById('afNewTrollRenewable')?.value === 'true';
    const renew_price = parseInt(document.getElementById('afNewTrollRenewPrice')?.value || '10000');
    const renew_currency = document.getElementById('afNewTrollRenewCurrency')?.value || 'coins';

    const res = await apiRequest('/api/fishing/admin/add-troll-item', 'POST', {
        id, name, price, currency, action_key, action_val, desc,
        is_hidden, obtain_source, has_expiry, duration_days, renewable, renew_price, renew_currency
    });

    if (res.ok) {
        showToast(res.message || 'Thêm vật phẩm troll thành công!', 'success');
        const nEl = document.getElementById('afNewTrollName'); if (nEl) nEl.value = '';
        const idEl = document.getElementById('afNewTrollId'); if (idEl) idEl.value = '';
        await loadAdminFishList();
    }
}


async function afSubmitAddNewChest() {
    const name = document.getElementById('afNewChestName')?.value.trim();
    if (!name) return showToast('Vui lòng nhập tên rương báu', 'warning');
    const id = document.getElementById('afNewChestId')?.value.trim();
    const chance = parseFloat(document.getElementById('afNewChestChance')?.value || '3.5');
    const min_coins = parseInt(document.getElementById('afNewChestMinCoin')?.value || '10000');
    const max_coins = parseInt(document.getElementById('afNewChestMaxCoin')?.value || '50000');
    const req_key = document.getElementById('afNewChestReqKey')?.value.trim();
    const desc = document.getElementById('afNewChestDesc')?.value.trim();

    const is_hidden = !!document.getElementById('afNewChestHidden')?.checked;
    const obtain_source = document.getElementById('afNewChestSource')?.value.trim();

    
    const baits = Array.from(document.querySelectorAll('input[name="afChestBaitChoice"]:checked')).map(el => el.value);
    const pets = Array.from(document.querySelectorAll('input[name="afChestPetChoice"]:checked')).map(el => el.value);
    const rods = Array.from(document.querySelectorAll('input[name="afChestRodChoice"]:checked')).map(el => el.value);
    const items = Array.from(document.querySelectorAll('input[name="afChestItemChoice"]:checked')).map(el => el.value);

    const res = await apiRequest('/api/fishing/admin/add-chest', 'POST', {
        id, name, chance, min_coins, max_coins, req_key, desc,
        baits, pets, rods, items,
        is_hidden, obtain_source
    });

    if (res.ok) {
        showToast(res.message || 'Tạo rương báu mới thành công!', 'success');
        const nEl = document.getElementById('afNewChestName'); if (nEl) nEl.value = '';
        const idEl = document.getElementById('afNewChestId'); if (idEl) idEl.value = '';
        await loadAdminFishList();
    }
}




function initAdminFarmTab() {
    loadAdminFarmCatalogs();
    if (state.adminFarm && state.adminFarm.currentUser) {
        loadAdminFarmUser();
    }
}

function switchAdminFarmTab(subTab) {
    state.adminFarm.activeSubTab = subTab;
    const tabs = ['user', 'env', 'catalogs'];
    tabs.forEach(t => {
        let name = t.charAt(0).toUpperCase() + t.slice(1);
        const btn = document.getElementById(`btnFarmSub${name}`);
        const view = document.getElementById(`farmView${name}`);
        if (btn) btn.classList.toggle('active', t === subTab);
        if (view) view.style.display = (t === subTab) ? 'block' : 'none';
    });

    if (subTab === 'catalogs') {
        switchCatalogTab(state.adminFarm.currentCatTab || 'seeds');
    }
}

async function loadAdminFarmCatalogs() {
    const res = await apiRequest('/api/farm/admin/catalogs');
    if (!res.ok) return;

    state.adminFarm.catalogs = res;

    
    const seedSel = document.getElementById('farmAddSeedSelect');
    if (seedSel && res.seeds) {
        seedSel.innerHTML = Object.entries(res.seeds).map(([id, s]) => {
            return `<option value="${id}">${escapeHtml(s.name || id)} (Lớn: ${Math.round((s.grow_seconds||300)/60)}p)</option>`;
        }).join('');
    }

    
    const cropSel = document.getElementById('farmAddCropSelect');
    const mutCropSel = document.getElementById('farmAddMutCropSelect');
    if (cropSel && res.crops) {
        const cropOpts = Object.entries(res.crops).map(([id, c]) => {
            return `<option value="${id}">${escapeHtml(c.name || id)} (${Number(c.sell_price||0).toLocaleString()}c)</option>`;
        }).join('');
        cropSel.innerHTML = cropOpts;
        if (mutCropSel) mutCropSel.innerHTML = cropOpts;
    }

    
    const mutSel = document.getElementById('farmAddMutSelect');
    if (mutSel && res.mutations) {
        mutSel.innerHTML = res.mutations.map(m => {
            return `<option value="${m.id}">${m.prefix} ${escapeHtml(m.name)} (x${m.price_multi} giá)</option>`;
        }).join('');
    }

    
    const toolSel = document.getElementById('farmAddToolSelect');
    if (toolSel && res.tools) {
        toolSel.innerHTML = Object.entries(res.tools).map(([id, t]) => {
            return `<option value="${id}">${escapeHtml(t.name || id)} (${t.type})</option>`;
        }).join('');
    }

    const pestSel = document.getElementById('farmAddPestSelect');
    if (pestSel && res.pests) {
        pestSel.innerHTML = Object.entries(res.pests).map(([id, p]) => {
            return `<option value="${id}">${escapeHtml(p.name || id)} (Bán: ${Number(p.sell_price||0).toLocaleString()}c)</option>`;
        }).join('');
    }

    
    const env = res.current_env;
    if (env) {
        const s = env.season || {};
        const w = env.weather || {};
        const sTitle = document.getElementById('farmEnvSeasonTitle');
        const sDesc = document.getElementById('farmEnvSeasonDesc');
        const sCrops = document.getElementById('farmEnvSeasonCrops');
        if (sTitle) sTitle.innerHTML = s.name || '—';
        if (sDesc) sDesc.innerText = s.desc || '—';
        if (sCrops) sCrops.innerText = (s.favored_crops || []).join(', ') || 'Không có';

        const wTitle = document.getElementById('farmEnvWeatherTitle');
        const wDesc = document.getElementById('farmEnvWeatherDesc');
        const wEffect = document.getElementById('farmEnvWeatherEffect');
        if (wTitle) wTitle.innerHTML = w.name || '—';
        if (wDesc) wDesc.innerText = w.desc || '—';
        if (wEffect) wEffect.innerText = `Tốc độ: x${w.speed_multi || 1.0} (${w.effect || 'Bình thường'})`;

        const ovStatus = document.getElementById('farmEnvOverrideStatus');
        const ovTime = document.getElementById('farmEnvOverrideTime');
        if (ovStatus) {
            ovStatus.innerText = env.is_override ? '⚡ Đang Bật Cưỡng Chế (Override)' : 'Đang chạy theo chu kỳ tự nhiên';
            ovStatus.style.color = env.is_override ? '#ff69b4' : '#32cd32';
        }
        if (ovTime) {
            ovTime.innerText = env.is_override ? `${Math.round(env.override_remaining / 60)} phút` : '0 phút';
        }
    }
}

async function loadAdminFarmUser() {
    const input = document.getElementById('farmSearchUserId');
    const userId = input ? input.value.trim() : '';
    if (!userId) {
        return showToast('Vui lòng nhập Discord User ID nông dân', 'warning');
    }

    const res = await apiRequest(`/api/farm/admin/user?user_id=${userId}`);
    if (!res.ok) {
        return showToast(res.error || 'Không tìm thấy dữ liệu nông trại', 'error');
    }

    state.adminFarm.currentUser = res;

    const placeholder = document.getElementById('farmUserPlaceholder');
    const detail = document.getElementById('farmUserDetail');
    if (placeholder) placeholder.style.display = 'none';
    if (detail) detail.style.display = 'block';

    const av = document.getElementById('farmUserAvatar');
    const name = document.getElementById('farmUserName');
    const discId = document.getElementById('farmUserDiscordId');
    if (av) av.src = res.avatar;
    if (name) name.innerText = res.username;
    if (discId) discId.innerText = res.user_id;

    
    const plotsCount = document.getElementById('farmUserPlotsCount');
    const cropsCount = document.getElementById('farmUserCropsCount');
    const mutCount = document.getElementById('farmUserMutationsCount');
    const seedsCount = document.getElementById('farmUserSeedsCount');
    const pestsCount = document.getElementById('farmUserPestsCount');
    const starCount = document.getElementById('farmUserStardustCount');

    const totalCrops = Object.values(res.crops || {}).reduce((a, b) => a + b, 0);
    const totalSeeds = Object.values(res.seeds || {}).reduce((a, b) => a + b, 0);
    const totalPests = Object.values(res.pests || {}).reduce((a, b) => a + b, 0);

    if (plotsCount) plotsCount.innerText = `${res.plots_count || 4}/16`;
    if (cropsCount) cropsCount.innerText = totalCrops;
    if (mutCount) mutCount.innerText = (res.mutated_crops || []).length;
    if (seedsCount) seedsCount.innerText = totalSeeds;
    if (pestsCount) pestsCount.innerText = totalPests;
    if (starCount) starCount.innerText = res.materials?.stardust_dust || 0;

    const plotsBadge = document.getElementById('farmPlotsStatusBadge');
    if (plotsBadge) plotsBadge.innerText = `${res.plots_count || 4} Ô Đất`;

    renderAdminFarmPlots(res.plots || []);
}

function loadAdminFarmSelfUser() {
    const input = document.getElementById('farmSearchUserId');
    const selfId = state.currentUser ? (state.currentUser.discord_id || state.currentUser.id) : null;
    if (selfId && input) {
        input.value = selfId;
        loadAdminFarmUser();
    } else if (input) {
        showToast('Tài khoản chưa có Discord ID liên kết', 'warning');
    }
}

function renderAdminFarmPlots(plots) {
    const container = document.getElementById('farmPlotsContainer');
    if (!container) return;

    if (!plots || plots.length === 0) {
        container.innerHTML = '<div style="color: var(--text-dim); padding: 20px;">Chưa có ô đất nào.</div>';
        return;
    }

    const catalogs = state.adminFarm.catalogs || {};
    const seeds = catalogs.seeds || {};

    container.innerHTML = plots.map(p => {
        const isPlanted = !!p.seed;
        const sInfo = seeds[p.seed] || {};
        const plantName = isPlanted ? (sInfo.name || p.seed) : 'Đất Trống';
        const pct = p.progress_pct || 0;
        const isReady = !!p.is_ready;

        let statusBadges = [];
        if (p.wilted) statusBadges.push('<span class="badge" style="background: rgba(255,69,0,0.2); color: #ff4500;">🥀 Héo Úa</span>');
        else if (isReady) statusBadges.push('<span class="badge" style="background: rgba(50,205,50,0.2); color: #32cd32;">✨ Chín Mọng</span>');
        else if (isPlanted) statusBadges.push(`<span class="badge badge-sakura">${pct}%</span>`);

        if (p.watered) statusBadges.push('<span class="badge" style="background: rgba(0,191,255,0.15); color: #00bfff;">💧 Đất Ẩm</span>');
        else if (isPlanted) statusBadges.push('<span class="badge" style="background: rgba(255,165,0,0.2); color: #ffa500;">⚠️ Khô</span>');

        if (p.pests) statusBadges.push('<span class="badge" style="background: rgba(255,99,71,0.2); color: #ff6347;">🐛 Sâu</span>');
        if (p.greenhouse) statusBadges.push('<span class="badge" style="background: rgba(147,112,219,0.2); color: #ba55d3;">🏛️ Kính</span>');

        const barColor = isReady ? '#32cd32' : p.wilted ? '#ff4500' : 'var(--accent-pink)';

        return `
            <div style="background: rgba(255,255,255,0.03); border: 1px solid rgba(255,255,255,0.08); border-radius: 10px; padding: 12px; display: flex; flex-direction: column; gap: 8px;">
                <div style="display: flex; justify-content: space-between; align-items: center;">
                    <strong style="color: var(--text-dim); font-size: 0.8rem;">Ô ĐẤT #${p.id}</strong>
                    <div style="display: flex; gap: 4px; flex-wrap: wrap;">${statusBadges.join('')}</div>
                </div>
                <div style="font-weight: 600; font-size: 0.95rem; color: ${isPlanted ? 'var(--text-main)' : 'var(--text-dim)'};">${escapeHtml(plantName)}</div>
                ${isPlanted ? `
                    <div style="background: rgba(0,0,0,0.3); border-radius: 6px; height: 8px; overflow: hidden; position: relative;">
                        <div style="background: ${barColor}; width: ${Math.min(100, pct)}%; height: 100%; transition: width 0.3s;"></div>
                    </div>
                ` : `
                    <div style="font-size: 0.78rem; color: var(--text-dim); font-style: italic;">Sẵn sàng gieo hạt</div>
                `}
            </div>
        `;
    }).join('');
}

async function adminFarmQuickAction(action) {
    if (!state.adminFarm.currentUser) return showToast('Vui lòng tra cứu nông dân trước', 'warning');
    const userId = state.adminFarm.currentUser.user_id;

    if (action === 'clear_farm' && !confirm('Bạn có chắc chắn muốn RESET toàn bộ trang trại của nông dân này về mặc định không?')) {
        return;
    }

    const res = await apiRequest('/api/farm/admin/user/action', 'POST', { user_id: userId, action: action });

    if (res.ok) {
        showToast(res.message || 'Thao tác thành công', 'success');
        await loadAdminFarmUser();
    } else {
        showToast(res.error || 'Thao tác thất bại', 'error');
    }
}

async function adminFarmPromptPlots() {
    if (!state.adminFarm.currentUser) return showToast('Vui lòng tra cứu nông dân trước', 'warning');
    const userId = state.adminFarm.currentUser.user_id;
    const cur = state.adminFarm.currentUser.plots_count || 4;
    const ans = prompt(`Nhập số ô đất muốn thiết lập (từ 4 đến 16 ô) cho User ${userId}:`, cur);
    if (!ans) return;
    const num = parseInt(ans);
    if (isNaN(num) || num < 4 || num > 16) {
        return showToast('Số ô đất phải nằm trong khoảng từ 4 đến 16', 'warning');
    }

    const res = await apiRequest('/api/farm/admin/user/action', 'POST', { user_id: userId, action: 'set_plots', amount: num });

    if (res.ok) {
        showToast(res.message || 'Thiết lập ô đất thành công', 'success');
        await loadAdminFarmUser();
    } else {
        showToast(res.error || 'Thao tác thất bại', 'error');
    }
}

async function adminFarmAddItem(actionType) {
    if (!state.adminFarm.currentUser) return showToast('Vui lòng tra cứu nông dân trước', 'warning');
    const userId = state.adminFarm.currentUser.user_id;

    let itemId = '', qty = 1;
    if (actionType === 'add_seed') {
        itemId = document.getElementById('farmAddSeedSelect')?.value;
        qty = parseInt(document.getElementById('farmAddSeedQty')?.value || '1');
    } else if (actionType === 'add_crop') {
        itemId = document.getElementById('farmAddCropSelect')?.value;
        qty = parseInt(document.getElementById('farmAddCropQty')?.value || '1');
    } else if (actionType === 'add_tool') {
        itemId = document.getElementById('farmAddToolSelect')?.value;
        qty = parseInt(document.getElementById('farmAddToolQty')?.value || '1');
    } else if (actionType === 'add_pest') {
        itemId = document.getElementById('farmAddPestSelect')?.value;
        qty = parseInt(document.getElementById('farmAddPestQty')?.value || '1');
    } else if (actionType === 'add_material') {
        itemId = document.getElementById('farmAddMatSelect')?.value;
        qty = parseInt(document.getElementById('farmAddMatQty')?.value || '1');
    }

    if (!itemId) return showToast('Chưa chọn vật phẩm', 'warning');

    const res = await apiRequest('/api/farm/admin/user/action', 'POST', { user_id: userId, action: actionType, item_id: itemId, amount: qty });

    if (res.ok) {
        showToast(res.message || 'Cập nhật thành công', 'success');
        await loadAdminFarmUser();
    } else {
        showToast(res.error || 'Thao tác thất bại', 'error');
    }
}

async function adminFarmAddMutation() {
    if (!state.adminFarm.currentUser) return showToast('Vui lòng tra cứu nông dân trước', 'warning');
    const userId = state.adminFarm.currentUser.user_id;

    const mutId = document.getElementById('farmAddMutSelect')?.value;
    const cropId = document.getElementById('farmAddMutCropSelect')?.value;
    const qty = parseInt(document.getElementById('farmAddMutQty')?.value || '1');

    if (!mutId || !cropId) return showToast('Chưa chọn loại đột biến hoặc hoa màu', 'warning');

    const res = await apiRequest('/api/farm/admin/user/action', 'POST', { user_id: userId, action: 'add_mutated_crop', mutation_id: mutId, crop_id: cropId, amount: qty });

    if (res.ok) {
        showToast(res.message || 'Tạo đột biến thành công', 'success');
        await loadAdminFarmUser();
    } else {
        showToast(res.error || 'Thao tác thất bại', 'error');
    }
}

async function adminFarmApplyEnvironment() {
    const seasonId = document.getElementById('farmSetSeasonSelect')?.value;
    const weatherId = document.getElementById('farmSetWeatherSelect')?.value;
    const dur = parseInt(document.getElementById('farmSetDuration')?.value || '120');

    if (!seasonId && !weatherId) {
        return showToast('Vui lòng chọn ít nhất Mùa hoặc Thời tiết để thiết lập', 'warning');
    }

    const res = await apiRequest('/api/farm/admin/environment', 'POST', { season_id: seasonId, weather_id: weatherId, duration_minutes: dur });

    if (res.ok) {
        showToast(res.message || 'Đã kích hoạt môi trường mới!', 'success');
        await loadAdminFarmCatalogs();
    } else {
        showToast(res.error || 'Không thể thiết lập môi trường', 'error');
    }
}

async function adminFarmResetEnvironment() {
    const res = await apiRequest('/api/farm/admin/environment', 'POST', { season_id: null, weather_id: null, duration_minutes: 0 });

    if (res.ok) {
        showToast('Đã đưa Mùa & Thời Tiết về chu kỳ tự động', 'success');
        await loadAdminFarmCatalogs();
    }
}

function switchCatalogTab(catType) {
    state.adminFarm.currentCatTab = catType;
    const tabs = ['seeds', 'crops', 'mutations', 'pests', 'diseases', 'tools', 'custom'];
    tabs.forEach(t => {
        let name = t.charAt(0).toUpperCase() + t.slice(1);
        const btn = document.getElementById(`btnCat${name}`);
        if (btn) btn.classList.toggle('active', t === catType);
    });
    renderCatalogTable(catType);
}

function renderCatalogTable(catType) {
    const container = document.getElementById('farmCatalogTableContainer');
    if (!container) return;
    const catalogs = state.adminFarm.catalogs || {};

    if (catType === 'seeds') {
        const list = Object.entries(catalogs.seeds || {});
        container.innerHTML = `
            <table class="data-table" style="width: 100%;">
                <thead>
                    <tr>
                        <th>Tên Hạt Giống</th>
                        <th>Nông Sản Thu Được</th>
                        <th>Giá Mua</th>
                        <th>Sản Lượng</th>
                        <th>Thời Gian Chín</th>
                        <th>Mô Tả</th>
                    </tr>
                </thead>
                <tbody>
                    ${list.map(([id, s]) => `
                        <tr>
                            <td><strong>${escapeHtml(s.name || id)}</strong></td>
                            <td>${escapeHtml(s.crop_name || s.crop_id)}</td>
                            <td><span style="color: #ffd700;">${Number(s.price||s.seed_price||0).toLocaleString()}c</span></td>
                            <td>${s.yield_min || 2} - ${s.yield_max || 5} bó</td>
                            <td>${Math.round((s.grow_seconds||300)/60)} phút</td>
                            <td style="font-size: 0.82rem; color: var(--text-dim);">${escapeHtml(s.desc || '')}</td>
                        </tr>
                    `).join('')}
                </tbody>
            </table>
        `;
    } else if (catType === 'crops') {
        const list = Object.entries(catalogs.crops || {});
        container.innerHTML = `
            <table class="data-table" style="width: 100%;">
                <thead>
                    <tr>
                        <th>Tên Nông Sản</th>
                        <th>Hạt Giống Gốc</th>
                        <th>Giá Bán Ra</th>
                        <th>Mùa Ưu Đãi</th>
                        <th>Mô Tả</th>
                    </tr>
                </thead>
                <tbody>
                    ${list.map(([id, c]) => `
                        <tr>
                            <td><strong>${escapeHtml(c.name || id)}</strong></td>
                            <td><code>${c.seed_id || ''}</code></td>
                            <td><span style="color: #00ffff;">${Number(c.sell_price||0).toLocaleString()}c</span></td>
                            <td>${escapeHtml((c.preferred_seasons || []).join(', '))}</td>
                            <td style="font-size: 0.82rem; color: var(--text-dim);">${escapeHtml(c.desc || '')}</td>
                        </tr>
                    `).join('')}
                </tbody>
            </table>
        `;
    } else if (catType === 'mutations') {
        const list = catalogs.mutations || [];
        container.innerHTML = `
            <table class="data-table" style="width: 100%;">
                <thead>
                    <tr>
                        <th>Loại Đột Biến 🧬</th>
                        <th>Tiền Tố Hiển Thị</th>
                        <th>Bội Số Giá Bán</th>
                        <th>Độ Bền Hồi Phục</th>
                        <th>Tỉ Lệ Rơi</th>
                        <th>Mô Tả Hiệu Ứng</th>
                    </tr>
                </thead>
                <tbody>
                    ${list.map(m => `
                        <tr>
                            <td><strong style="color: #ff69b4;">${escapeHtml(m.name)}</strong></td>
                            <td><span class="badge" style="background: rgba(255,105,180,0.15); color: #ff69b4;">${m.prefix}</span></td>
                            <td><strong style="color: #ffd700;">x${m.price_multi} Lần</strong></td>
                            <td><span style="color: #32cd32;">+${m.buff_durability || 40} Độ Bền</span></td>
                            <td>Trọng số ${m.weight}</td>
                            <td style="font-size: 0.82rem; color: var(--text-dim);">${escapeHtml(m.desc || '')}</td>
                        </tr>
                    `).join('')}
                </tbody>
            </table>
        `;
    } else if (catType === 'pests') {
        const list = Object.entries(catalogs.pests || {});
        container.innerHTML = `
            <table class="data-table" style="width: 100%;">
                <thead>
                    <tr>
                        <th>Loại Sâu Bọ 🐛</th>
                        <th>Giá Bán Thương Gia</th>
                        <th>May Mắn Khi Làm Mồi</th>
                        <th>Mô Tả</th>
                    </tr>
                </thead>
                <tbody>
                    ${list.map(([id, p]) => `
                        <tr>
                            <td><strong>${escapeHtml(p.name || id)}</strong></td>
                            <td><span style="color: #ffd700;">${Number(p.sell_price||0).toLocaleString()}c</span></td>
                            <td><span style="color: #32cd32;">+${p.bait_luck || 0} Luck</span></td>
                            <td style="font-size: 0.82rem; color: var(--text-dim);">${escapeHtml(p.desc || '')}</td>
                        </tr>
                    `).join('')}
                </tbody>
            </table>
        `;
    } else if (catType === 'diseases') {
        const list = Object.entries(catalogs.diseases || {});
        container.innerHTML = `
            <table class="data-table" style="width: 100%;">
                <thead>
                    <tr>
                        <th>Tên Mầm Bệnh 🦠</th>
                        <th>Mã Định Danh</th>
                        <th>Triệu Chứng / Tác Động</th>
                        <th>Thuốc / Dụng Cụ Chữa Trị</th>
                        <th>Mô Tả</th>
                    </tr>
                </thead>
                <tbody>
                    ${list.map(([id, d]) => `
                        <tr>
                            <td><strong style="color: #ff6347;">${escapeHtml(d.name || id)}</strong></td>
                            <td><code>${escapeHtml(id)}</code></td>
                            <td><span class="badge" style="background: rgba(255,99,71,0.15); color: #ff6347;">${escapeHtml(d.effect || 'Ngừng sinh trưởng')}</span></td>
                            <td><span style="color: #32cd32;">🧪 ${escapeHtml(d.cure_item || 'pesticide_bio')}</span></td>
                            <td style="font-size: 0.82rem; color: var(--text-dim);">${escapeHtml(d.desc || '')}</td>
                        </tr>
                    `).join('')}
                </tbody>
            </table>
        `;
    } else if (catType === 'tools') {
        const list = Object.entries(catalogs.tools || {});
        container.innerHTML = `
            <table class="data-table" style="width: 100%;">
                <thead>
                    <tr>
                        <th>Tên Dụng Cụ / Phân Bón 🛠️</th>
                        <th>Phân Loại</th>
                        <th>Giá Bán Shop</th>
                        <th>Mô Tả Chức Năng</th>
                    </tr>
                </thead>
                <tbody>
                    ${list.map(([id, t]) => `
                        <tr>
                            <td><strong>${escapeHtml(t.name || id)}</strong></td>
                            <td><span class="badge badge-sakura">${t.type || 'tool'}</span></td>
                            <td><span style="color: #ffd700;">${Number(t.price||0).toLocaleString()}c</span></td>
                            <td style="font-size: 0.82rem; color: var(--text-dim);">${escapeHtml(t.desc || '')}</td>
                        </tr>
                    `).join('')}
                </tbody>
            </table>
        `;
    } else if (catType === 'custom') {
        const customData = catalogs.custom_items || {};
        const allCustom = [];
        ['seeds', 'fertilizers', 'tools', 'pests', 'diseases'].forEach(cat => {
            Object.entries(customData[cat] || {}).forEach(([id, item]) => {
                allCustom.push({ category: cat, id, item });
            });
        });
        if (allCustom.length === 0) {
            container.innerHTML = `
                <div style="text-align: center; padding: 36px 20px; color: var(--text-dim);">
                    <div style="font-size: 2.5rem; margin-bottom: 10px;">✨</div>
                    <div style="font-size: 1.05rem; font-weight: 600; color: var(--text-main); margin-bottom: 6px;">Chưa có vật phẩm tùy chỉnh nào</div>
                    <div>Admin có thể tạo thêm cây trồng, phân bón mới, dụng cụ, sâu bọ và mầm bệnh độc quyền.</div>
                    <button class="btn btn-primary btn-sm" style="margin-top: 14px; background: linear-gradient(135deg, #10b981, #059669); border:none;" onclick="adminFarmOpenCreateItemModal()">
                        ➕ Bắt Đầu Tạo Vật Phẩm Mới
                    </button>
                </div>
            `;
        } else {
            container.innerHTML = `
                <table class="data-table" style="width: 100%;">
                    <thead>
                        <tr>
                            <th>Phân Loại</th>
                            <th>Mã ID</th>
                            <th>Tên Vật Phẩm</th>
                            <th>Giá / Chỉ Số</th>
                            <th>Mô Tả</th>
                            <th style="text-align: right;">Hành Động</th>
                        </tr>
                    </thead>
                    <tbody>
                        ${allCustom.map(c => `
                            <tr>
                                <td><span class="badge badge-sakura">${escapeHtml(c.category)}</span></td>
                                <td><code>${escapeHtml(c.id)}</code></td>
                                <td><strong>${escapeHtml(c.item.name || c.id)}</strong></td>
                                <td><span style="color: #ffd700;">${c.item.price ? Number(c.item.price).toLocaleString() + 'c' : (c.item.effect || '—')}</span></td>
                                <td style="font-size: 0.82rem; color: var(--text-dim);">${escapeHtml(c.item.desc || '')}</td>
                                <td style="text-align: right;">
                                    <button class="btn btn-danger btn-xs" onclick="adminFarmDeleteCustomItem('${c.category}', '${c.id}')">🗑️ Xóa</button>
                                </td>
                            </tr>
                        `).join('')}
                    </tbody>
                </table>
            `;
        }
    }
}


function adminFarmOpenCreateItemModal() {
    const modal = document.getElementById('modalCreateFarmItem');
    if (!modal) return;
    modal.style.display = 'flex';
    adminFarmChangeCategoryForm();
}

function adminFarmCloseCreateItemModal() {
    const modal = document.getElementById('modalCreateFarmItem');
    if (modal) modal.style.display = 'none';
}

function adminFarmChangeCategoryForm() {
    const cat = document.getElementById('farmNewItemCategory')?.value || 'seed';
    const fields = document.getElementById('farmDynamicItemFields');
    if (!fields) return;

    if (cat === 'seed') {
        fields.innerHTML = `
            <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 12px; margin-bottom: 12px;">
                <div class="form-group" style="margin-bottom:0">
                    <label>Tên Nông Sản Thu Hoạch:</label>
                    <input type="text" id="farmNewCropName" class="form-control" placeholder="vd: 🥭 Quả Xoài Vàng">
                </div>
                <div class="form-group" style="margin-bottom:0">
                    <label>Giá Mua Hạt Giống (Coins):</label>
                    <input type="number" id="farmNewPrice" class="form-control" value="5000" min="0">
                </div>
            </div>
            <div style="display: grid; grid-template-columns: 1fr 1fr 1fr; gap: 10px; margin-bottom: 12px;">
                <div class="form-group" style="margin-bottom:0">
                    <label>Thời Gian Lớn (Giây):</label>
                    <input type="number" id="farmNewGrowSec" class="form-control" value="600" min="10">
                </div>
                <div class="form-group" style="margin-bottom:0">
                    <label>Sản Lượng (Min - Max):</label>
                    <div style="display:flex; gap:6px;">
                        <input type="number" id="farmNewYieldMin" class="form-control" value="2" min="1">
                        <input type="number" id="farmNewYieldMax" class="form-control" value="5" min="1">
                    </div>
                </div>
                <div class="form-group" style="margin-bottom:0">
                    <label>Giá Bán Nông Sản (Coins):</label>
                    <input type="number" id="farmNewSellPrice" class="form-control" value="3500" min="0">
                </div>
            </div>
        `;
    } else if (cat === 'fertilizer') {
        fields.innerHTML = `
            <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 12px; margin-bottom: 12px;">
                <div class="form-group" style="margin-bottom:0">
                    <label>Giá Bán (Coins):</label>
                    <input type="number" id="farmNewPrice" class="form-control" value="8000" min="0">
                </div>
                <div class="form-group" style="margin-bottom:0">
                    <label>Tăng Tốc Sinh Trưởng (%):</label>
                    <input type="number" id="farmNewSpeedBonus" class="form-control" value="0.5" step="0.1" min="0.1" max="2.0">
                </div>
            </div>
        `;
    } else if (cat === 'tool') {
        fields.innerHTML = `
            <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 12px; margin-bottom: 12px;">
                <div class="form-group" style="margin-bottom:0">
                    <label>Giá Bán (Coins):</label>
                    <input type="number" id="farmNewPrice" class="form-control" value="50000" min="0">
                </div>
                <div class="form-group" style="margin-bottom:0">
                    <label>Thời Gian Giữ Ẩm (Giờ):</label>
                    <input type="number" id="farmNewWaterHours" class="form-control" value="8" min="1">
                </div>
            </div>
        `;
    } else if (cat === 'pest') {
        fields.innerHTML = `
            <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 12px; margin-bottom: 12px;">
                <div class="form-group" style="margin-bottom:0">
                    <label>Giá Bán Shop (Coins):</label>
                    <input type="number" id="farmNewPrice" class="form-control" value="3000" min="0">
                </div>
                <div class="form-group" style="margin-bottom:0">
                    <label>May Mắn Khi Làm Mồi Câu (+Luck):</label>
                    <input type="number" id="farmNewBaitLuck" class="form-control" value="25" min="0">
                </div>
            </div>
        `;
    } else if (cat === 'disease') {
        fields.innerHTML = `
            <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 12px; margin-bottom: 12px;">
                <div class="form-group" style="margin-bottom:0">
                    <label>Triệu Chứng / Tác Động:</label>
                    <input type="text" id="farmNewDiseaseEffect" class="form-control" value="Ngừng sinh trưởng & khô cằn">
                </div>
                <div class="form-group" style="margin-bottom:0">
                    <label>Thuốc Điều Trị Cần Dùng:</label>
                    <input type="text" id="farmNewDiseaseCure" class="form-control" value="pesticide_bio">
                </div>
            </div>
        `;
    }
}

async function adminFarmSaveCustomItem() {
    const category = document.getElementById('farmNewItemCategory')?.value;
    const id = document.getElementById('farmNewItemId')?.value?.trim();
    const name = document.getElementById('farmNewItemName')?.value?.trim();
    const desc = document.getElementById('farmNewItemDesc')?.value?.trim() || '';

    if (!id || !name) {
        return showToast('Vui lòng nhập ID và Tên vật phẩm', 'warning');
    }

    const payload = { category, id, name, desc };
    if (category === 'seed') {
        payload.crop_name = document.getElementById('farmNewCropName')?.value?.trim() || name;
        payload.price = parseInt(document.getElementById('farmNewPrice')?.value || '5000');
        payload.grow_seconds = parseInt(document.getElementById('farmNewGrowSec')?.value || '600');
        payload.yield_min = parseInt(document.getElementById('farmNewYieldMin')?.value || '2');
        payload.yield_max = parseInt(document.getElementById('farmNewYieldMax')?.value || '5');
        payload.sell_price = parseInt(document.getElementById('farmNewSellPrice')?.value || '3500');
    } else if (category === 'fertilizer') {
        payload.price = parseInt(document.getElementById('farmNewPrice')?.value || '8000');
        payload.speed_bonus = parseFloat(document.getElementById('farmNewSpeedBonus')?.value || '0.5');
    } else if (category === 'tool') {
        payload.price = parseInt(document.getElementById('farmNewPrice')?.value || '50000');
        payload.water_duration = parseInt(document.getElementById('farmNewWaterHours')?.value || '8') * 3600;
        payload.tool_type = 'tool';
    } else if (category === 'pest') {
        payload.sell_price = parseInt(document.getElementById('farmNewPrice')?.value || '3000');
        payload.bait_luck = parseInt(document.getElementById('farmNewBaitLuck')?.value || '25');
    } else if (category === 'disease') {
        payload.effect = document.getElementById('farmNewDiseaseEffect')?.value?.trim() || 'Ngừng sinh trưởng';
        payload.cure_item = document.getElementById('farmNewDiseaseCure')?.value?.trim() || 'pesticide_bio';
    }

    const res = await apiRequest('/api/farm/admin/item/create', 'POST', payload);
    if (res.ok) {
        showToast(res.message || 'Lưu vật phẩm mới thành công!', 'success');
        adminFarmCloseCreateItemModal();
        await loadAdminFarmCatalogs();
        switchCatalogTab('custom');
    } else {
        showToast(res.error || 'Lỗi lưu vật phẩm', 'error');
    }
}

async function adminFarmDeleteCustomItem(category, itemId) {
    if (!confirm(`Bạn có chắc chắn muốn xóa vật phẩm tùy chỉnh '${itemId}'?`)) return;
    const res = await apiRequest('/api/farm/admin/item/delete', 'POST', { category, id: itemId });
    if (res.ok) {
        showToast(res.message || 'Đã xóa vật phẩm thành công!', 'success');
        await loadAdminFarmCatalogs();
        switchCatalogTab('custom');
    } else {
        showToast(res.error || 'Lỗi xóa vật phẩm', 'error');
    }
}



function updateBotProfileLivePreview() {
    const nickVal = document.getElementById('botProfileNick')?.value.trim() || 'Sakura Bot';
    const avVal = document.getElementById('botProfileAvatarUrl')?.value.trim();
    const bannerVal = document.getElementById('botProfileBanner')?.value.trim();
    const bioVal = document.getElementById('botProfileBio')?.value.trim() || '🌸 Trợ lý Discord đa năng cho server của bạn.';

    const prevNick = document.getElementById('botProfilePreviewNick');
    if (prevNick) prevNick.innerText = nickVal;

    const prevBio = document.getElementById('botProfilePreviewBio');
    if (prevBio) prevBio.innerText = bioVal;

    const prevAv = document.getElementById('botProfileAvatar');
    if (prevAv && avVal) {
        prevAv.src = avVal;
    }

    const prevBanner = document.getElementById('botProfilePreviewBanner');
    if (prevBanner) {
        if (bannerVal) {
            prevBanner.style.backgroundImage = `url('${bannerVal}')`;
        } else {
            prevBanner.style.backgroundImage = 'linear-gradient(135deg, #ec4899, #8b5cf6)';
        }
    }
}

async function loadBotProfile(guildId) {
    const gid = guildId || document.getElementById('drawerGuildId')?.value;
    if (!gid) return;
    const res = await apiRequest(`/api/guilds/${gid}/bot-profile`);
    if (!res.ok) return;
    const av = document.getElementById('botProfileAvatar');
    if (av && res.avatar) av.src = res.avatar;
    const avInput = document.getElementById('botProfileAvatarUrl');
    if (avInput) avInput.value = res.avatar || '';
    const nick = document.getElementById('botProfileNick');
    if (nick) nick.value = res.nick || '';
    const banner = document.getElementById('botProfileBanner');
    if (banner) banner.value = res.banner || '';
    const bio = document.getElementById('botProfileBio');
    if (bio) bio.value = res.bio || '';
    updateBotProfileLivePreview();
}

function uploadBotProfileAvatarFile(input) {
    if (!input || !input.files || !input.files[0]) return;
    const file = input.files[0];
    if (file.size > 8 * 1024 * 1024) {
        showToast('Ảnh quá lớn! Vui lòng chọn tệp nhỏ hơn 8MB.', 'warning');
        return;
    }
    const reader = new FileReader();
    reader.onload = function(e) {
        const dataUrl = e.target.result;
        const avInput = document.getElementById('botProfileAvatarUrl');
        if (avInput) avInput.value = dataUrl;
        const avImg = document.getElementById('botProfileAvatar');
        if (avImg) avImg.src = dataUrl;
        updateBotProfileLivePreview();
        showToast('✅ Đã tải ảnh đại diện vào khung xem trước! Hãy nhấn Lưu Hồ Sơ để áp dụng.', 'info');
    };
    reader.readAsDataURL(file);
}

async function saveBotProfile() {
    const gid = document.getElementById('drawerGuildId')?.value;
    if (!gid) return showToast('Thiếu server ID', 'warning');
    const nick = document.getElementById('botProfileNick')?.value.trim();
    const avatar = document.getElementById('botProfileAvatarUrl')?.value.trim();
    const banner = document.getElementById('botProfileBanner')?.value.trim();
    const bio = document.getElementById('botProfileBio')?.value.trim();
    const res = await apiRequest(`/api/guilds/${gid}/bot-profile`, 'POST', { nick, avatar, banner, bio });
    if (res.ok) {
        showToast(res.message || 'Đã lưu hồ sơ bot thành công', 'success');
        await loadBotProfile(gid);
    } else {
        showToast(res.error || 'Lỗi lưu hồ sơ bot', 'error');
    }
}




async function loadLevelRoles(guildId) {
    const gid = guildId || document.getElementById('drawerGuildId')?.value;
    if (!gid) return;
    const box = document.getElementById('levelRolesList');
    if (!box) return;
    const res = await apiRequest(`/api/guilds/${gid}/level-roles`);
    if (!res.ok) {
        box.innerHTML = `<div style="color:var(--accent-red);font-size:.85rem">${res.error || 'Lỗi tải danh sách mốc role'}</div>`;
        return;
    }
    let roles = res.roles || [];
    if (!Array.isArray(roles)) {
        roles = Object.entries(roles).map(([k, v]) => ({ level: k, role_id: v, role_name: v }));
    }
    if (!roles.length) {
        box.innerHTML = '<div style="color:var(--text-dim);font-size:.85rem;padding:8px 0">Chưa thiết lập mốc role nào. Đặt mốc level ở trên và chọn vai trò để tự động trao.</div>';
        return;
    }
    roles.sort((a, b) => parseInt(a.level) - parseInt(b.level));
    box.innerHTML = roles.map(r => `
        <div style="display:flex;justify-content:space-between;align-items:center;padding:10px 14px;background:var(--bg-card);border:1px solid var(--border-subtle);border-radius:10px">
            <div style="display:flex;align-items:center;gap:10px">
                <span class="badge badge-sakura" style="font-weight:700">Level ${r.level}</span>
                <span style="font-weight:600">@${escapeHtml(r.role_name || r.role_id)}</span>
                <span style="color:var(--text-dim);font-size:.75rem">(${r.role_id})</span>
            </div>
            <button class="btn btn-secondary btn-sm" style="color:var(--accent-red);border-color:rgba(239,68,68,0.3)" onclick="deleteLevelRole(${r.level})">🗑️ Xóa</button>
        </div>
    `).join('');
}

async function addLevelRole() {
    const gid = document.getElementById('drawerGuildId')?.value;
    if (!gid) return showToast('Thiếu server ID', 'warning');
    const level = parseInt(document.getElementById('newLevelRewardNum')?.value);
    const role_id = document.getElementById('newLevelRewardRole')?.value;
    if (!level || level < 1 || !role_id) {
        return showToast('Vui lòng nhập mốc level (>0) và chọn vai trò', 'warning');
    }
    const res = await apiRequest(`/api/guilds/${gid}/level-roles`, 'POST', { level, role_id });
    if (res.ok) {
        showToast(res.message || 'Đã thêm mốc thưởng role!', 'success');
        document.getElementById('newLevelRewardNum').value = '';
        await loadLevelRoles(gid);
    } else {
        showToast(res.error || 'Lỗi thêm mốc role', 'error');
    }
}

async function deleteLevelRole(level) {
    const gid = document.getElementById('drawerGuildId')?.value;
    if (!gid) return;
    if (!confirm(`Bạn có chắc muốn xóa phần thưởng role ở mốc Level ${level}?`)) return;
    const res = await apiRequest(`/api/guilds/${gid}/level-roles/${level}`, 'DELETE');
    if (res.ok) {
        showToast('Đã xóa mốc role', 'success');
        await loadLevelRoles(gid);
    } else {
        showToast(res.error || 'Lỗi xóa mốc role', 'error');
    }
}



let currentFishingChannels = [];

function renderFishingChannelsTags() {
    const box = document.getElementById('fishChannelsBadges');
    if (!box) return;
    if (!currentFishingChannels.length) {
        box.innerHTML = '<span style="color:var(--text-muted);font-size:.82rem">Chưa giới hạn kênh câu cá (Thành viên có thể câu ở mọi kênh)</span>';
        return;
    }
    const sel = document.getElementById('fishFishingChannelSelect');
    const chMap = {};
    if (sel) {
        Array.from(sel.options).forEach(o => { if (o.value) chMap[o.value] = o.textContent.trim(); });
    }
    box.innerHTML = currentFishingChannels.map(cid => `
        <span class="badge" style="background:rgba(255,121,198,0.15);border:1px solid rgba(255,121,198,0.4);color:var(--accent-pink);font-size:.82rem;padding:4px 10px;border-radius:8px;display:inline-flex;align-items:center;gap:6px">
            #${escapeHtml(chMap[cid] || cid)}
            <button type="button" onclick="removeFishingChannelTag('${cid}')" style="background:none;border:none;color:var(--accent-red);cursor:pointer;font-size:.9rem;padding:0;line-height:1">✖</button>
        </span>
    `).join('');
}

function addFishingChannelTag() {
    const sel = document.getElementById('fishFishingChannelSelect');
    if (!sel || !sel.value) return showToast('Vui lòng chọn 1 kênh để thêm', 'warning');
    const cid = String(sel.value);
    if (!currentFishingChannels.includes(cid)) {
        currentFishingChannels.push(cid);
        renderFishingChannelsTags();
        showToast('Đã thêm kênh câu cá (Hãy bấm Lưu Cài Đặt)', 'info');
    } else {
        showToast('Kênh này đã có trong danh sách', 'warning');
    }
}

function removeFishingChannelTag(cid) {
    currentFishingChannels = currentFishingChannels.filter(c => String(c) !== String(cid));
    renderFishingChannelsTags();
}

function clearAllFishingChannels() {
    if (!currentFishingChannels.length) return;
    currentFishingChannels = [];
    renderFishingChannelsTags();
    showToast('Đã xóa tất cả kênh câu (Cho phép mọi kênh)', 'info');
}

async function loadFishingConfig(guildId) {
    const gid = guildId || document.getElementById('drawerGuildId')?.value;
    if (!gid) return;
    const res = await apiRequest(`/api/guilds/${gid}/fishing-config`);
    if (!res.ok) return;
    const cfg = res.config || res;
    
    
    if (Array.isArray(cfg.fishing_channels)) {
        currentFishingChannels = cfg.fishing_channels.map(String);
    } else if (cfg.fishing_channel_id) {
        currentFishingChannels = [String(cfg.fishing_channel_id)];
    } else {
        currentFishingChannels = [];
    }
    renderFishingChannelsTags();

    const cCh = document.getElementById('fishCodeChannel');
    if (cCh) {
        cCh.value = cfg.code_channel_id ? String(cfg.code_channel_id) : '';
        updateChannelBadge('fishCodeChannel');
    }
    const cRole = document.getElementById('fishCodeRole');
    if (cRole && cfg.code_role_id) cRole.value = String(cfg.code_role_id);
    const sw = document.getElementById('switchFishAllowOutside');
    if (sw) sw.classList.toggle('on', !!cfg.allow_outside);
}

async function saveFishingConfig() {
    const gid = document.getElementById('drawerGuildId')?.value;
    if (!gid) return showToast('Thiếu server ID', 'warning');
    const body = {
        fishing_channels: currentFishingChannels,
        fishing_channel_id: currentFishingChannels[0] || null,
        code_channel_id: document.getElementById('fishCodeChannel')?.value || null,
        code_role_id: document.getElementById('fishCodeRole')?.value || null,
        allow_outside: document.getElementById('switchFishAllowOutside')?.classList.contains('on')
    };
    const res = await apiRequest(`/api/guilds/${gid}/fishing-config`, 'POST', body);
    if (res.ok) {
        showToast(res.message || 'Đã lưu cấu hình câu cá', 'success');
        updateChannelBadge('fishCodeChannel');
        await loadFishingConfig(gid);
    } else {
        showToast(res.error || 'Lỗi lưu cấu hình câu cá', 'error');
    }
}




async function loadCustomKeys(guildId) {
    const gid = guildId || document.getElementById('drawerGuildId')?.value;
    if (!gid) return;
    const box = document.getElementById('customKeysList');
    if (!box) return;
    const res = await apiRequest(`/api/guilds/${gid}/custom-keys`);
    if (!res.ok) {
        box.innerHTML = `<div style="color:var(--accent-red);font-size:.85rem">${res.error || 'Lỗi tải Custom Keys'}</div>`;
        return;
    }
    const keys = res.keys || [];
    if (!keys.length) {
        box.innerHTML = '<div style="color:var(--text-dim);font-size:.85rem;padding:8px 0">Chưa có Custom Key nào được thiết lập.</div>';
        return;
    }
    box.innerHTML = keys.map(k => `
        <div style="display:flex;justify-content:space-between;align-items:flex-start;padding:12px 14px;background:var(--bg-card);border:1px solid var(--border-subtle);border-radius:10px">
            <div style="flex:1;margin-right:12px">
                <div style="display:flex;align-items:center;gap:8px;margin-bottom:6px">
                    <span class="badge badge-sakura" style="font-weight:700">${escapeHtml(k.keyword)}</span>
                    <span class="badge" style="background:rgba(255,255,255,0.06);font-size:.72rem">${k.match_type === 'exact' ? 'Chính xác' : 'Chứa từ'}</span>
                </div>
                ${k.response ? `<div style="font-size:.88rem;color:var(--text-main);white-space:pre-wrap;margin-bottom:6px">${escapeHtml(k.response)}</div>` : ''}
                ${k.file_name ? `
                    <div style="display:inline-flex;align-items:center;gap:6px;font-size:.8rem;padding:4px 8px;background:rgba(255,255,255,0.05);border-radius:6px">
                        📎 <a href="/api/guilds/${gid}/custom-keys/file/${encodeURIComponent(k.file_path ? k.file_path.split(/[\\\\/]/).pop() : k.file_name)}" target="_blank" style="color:var(--sakura-pink);text-decoration:none">${escapeHtml(k.file_name)}</a>
                        <span style="color:var(--text-dim)">(${Math.round((k.file_size || 0) / 1024)} KB)</span>
                    </div>
                ` : ''}
            </div>
            <button class="btn btn-secondary btn-sm" style="color:var(--accent-red);border-color:rgba(239,68,68,0.3)" onclick="deleteCustomKey('${k.id}')">🗑️ Xóa</button>
        </div>
    `).join('');
}

async function saveCustomKey() {
    const gid = document.getElementById('drawerGuildId')?.value;
    if (!gid) return showToast('Thiếu server ID', 'warning');
    const keyword = document.getElementById('customKeyWord')?.value.trim();
    const match_type = document.getElementById('customKeyMatchType')?.value || 'exact';
    const response = document.getElementById('customKeyResponse')?.value.trim();
    const fileInput = document.getElementById('customKeyFile');

    if (!keyword) return showToast('Vui lòng nhập từ khóa (keyword)', 'warning');
    if (!response && (!fileInput || !fileInput.files.length)) {
        return showToast('Vui lòng nhập nội dung phản hồi hoặc chọn file đính kèm', 'warning');
    }

    const fd = new FormData();
    fd.append('keyword', keyword);
    fd.append('match_type', match_type);
    fd.append('response', response);
    if (fileInput && fileInput.files.length) {
        fd.append('file', fileInput.files[0]);
    }

    try {
        const resp = await fetch(`/api/guilds/${gid}/custom-keys`, {
            method: 'POST',
            body: fd,
            credentials: 'include'
        });
        const data = await resp.json().catch(() => ({ ok: false, error: 'Lỗi máy chủ' }));
        if (data.ok) {
            showToast(data.message || 'Đã thêm Custom Key thành công', 'success');
            document.getElementById('customKeyWord').value = '';
            document.getElementById('customKeyResponse').value = '';
            if (fileInput) fileInput.value = '';
            await loadCustomKeys(gid);
        } else {
            showToast(data.error || 'Lỗi lưu Custom Key', 'error');
        }
    } catch (e) {
        showToast('Lỗi mạng: ' + e.message, 'error');
    }
}

async function deleteCustomKey(keyId) {
    const gid = document.getElementById('drawerGuildId')?.value;
    if (!gid) return;
    if (!confirm('Bạn có chắc muốn xóa Custom Key này?')) return;
    const res = await apiRequest(`/api/guilds/${gid}/custom-keys/${keyId}`, 'DELETE');
    if (res.ok) {
        showToast('Đã xóa Custom Key', 'success');
        await loadCustomKeys(gid);
    } else {
        showToast(res.error || 'Lỗi xóa Custom Key', 'error');
    }
}




async function loadBackups(guildId) {
    const gid = guildId || document.getElementById('drawerGuildId')?.value;
    if (!gid) return;
    const box = document.getElementById('backupsListTable');
    if (!box) return;
    const res = await apiRequest(`/api/guilds/${gid}/backups`);
    if (!res.ok) {
        box.innerHTML = `<div style="color:var(--accent-red);font-size:.85rem">${res.error || 'Lỗi tải danh sách backup'}</div>`;
        return;
    }
    const backups = res.backups || [];
    if (!backups.length) {
        box.innerHTML = '<div style="color:var(--text-dim);font-size:.85rem;padding:8px 0">Chưa có bản sao lưu nào. Bấm "Tạo Bản Sao Lưu Mới" để lưu cấu trúc server.</div>';
        return;
    }
    box.innerHTML = backups.map(b => {
        const sizeKb = Math.round((b.size || 0) / 1024);
        return `
            <div style="display:flex;justify-content:space-between;align-items:center;padding:12px 14px;background:var(--bg-card);border:1px solid var(--border-subtle);border-radius:10px;gap:12px;flex-wrap:wrap">
                <div>
                    <div style="font-weight:700;color:var(--text-main);margin-bottom:4px">📦 ${escapeHtml(b.filename)}</div>
                    <div style="font-size:.78rem;color:var(--text-dim)">
                        Tạo lúc: ${escapeHtml(b.created_at || '—')} • Kích thước: ${sizeKb} KB
                        ${b.channels ? `• ${b.channels} kênh` : ''} ${b.roles ? `• ${b.roles} roles` : ''}
                    </div>
                </div>
                <div style="display:flex;gap:8px;flex-wrap:wrap">
                    <button class="btn btn-secondary btn-sm" onclick="restoreBackup('${b.filename}', true)">🔄 Đồng bộ (Sync)</button>
                    <button class="btn btn-secondary btn-sm" style="color:var(--accent-orange)" onclick="restoreBackup('${b.filename}', false)">⚠️ Khôi phục sạch</button>
                    <a href="/api/guilds/${gid}/backups/${encodeURIComponent(b.filename)}/download" class="btn btn-secondary btn-sm" download>📥 Tải file</a>
                    <button class="btn btn-secondary btn-sm" style="color:var(--accent-red);border-color:rgba(239,68,68,0.3)" onclick="deleteBackup('${b.filename}')">🗑️</button>
                </div>
            </div>
        `;
    }).join('');
}

async function promptCreateBackup() {
    const gid = document.getElementById('drawerGuildId')?.value;
    if (!gid) return showToast('Thiếu server ID', 'warning');
    const desc = prompt('Nhập mô tả / ghi chú cho bản sao lưu:', 'Backup từ Web Dashboard');
    if (desc === null) return;
    showToast('Đang tạo bản sao lưu máy chủ, vui lòng đợi...', 'info');
    const res = await apiRequest(`/api/guilds/${gid}/backups/create`, 'POST', { description: desc });
    if (res.ok) {
        showToast(res.message || 'Đã tạo bản sao lưu thành công!', 'success');
        await loadBackups(gid);
    } else {
        showToast(res.error || 'Lỗi tạo bản sao lưu', 'error');
    }
}

async function restoreBackup(filename, syncMode) {
    const gid = document.getElementById('drawerGuildId')?.value;
    if (!gid) return;
    const modeDesc = syncMode
        ? 'Chế độ ĐỒNG BỘ (Sync Mode): Giữ nguyên tin nhắn hiện có và đồng bộ lại phân quyền/kênh thiếu sót.'
        : 'Chế độ LÀM MỚI (Wipe Mode): Cấu trúc kênh/role cũ sẽ được dọn dẹp để tái tạo lại hoàn toàn như lúc backup.';
    if (!confirm(`Xác nhận khôi phục bản '${filename}'?\n\n${modeDesc}`)) return;
    showToast('Đang khởi chạy tiến trình khôi phục...', 'info');
    const res = await apiRequest(`/api/guilds/${gid}/backups/restore`, 'POST', { filename, sync_mode: syncMode });
    if (res.ok) {
        showToast(res.message || 'Tiến trình khôi phục đang chạy ngầm', 'success');
    } else {
        showToast(res.error || 'Lỗi khôi phục backup', 'error');
    }
}

async function deleteBackup(filename) {
    const gid = document.getElementById('drawerGuildId')?.value;
    if (!gid) return;
    if (!confirm(`Bạn có chắc muốn xóa bản sao lưu ${filename}?`)) return;
    const res = await apiRequest(`/api/guilds/${gid}/backups/${encodeURIComponent(filename)}`, 'DELETE');
    if (res.ok) {
        showToast('Đã xóa bản sao lưu', 'success');
        await loadBackups(gid);
    } else {
        showToast(res.error || 'Lỗi xóa bản sao lưu', 'error');
    }
}




async function loadAutoRole(guildId) {
    const gid = guildId || document.getElementById('drawerGuildId')?.value;
    if (!gid) return;
    const res = await apiRequest(`/api/guilds/${gid}/autorole`);
    if (!res.ok) return;
    const cfg = res.config || {};
    const uEl = document.getElementById('autoRoleUser');
    if (uEl && cfg.user_role_id) uEl.value = String(cfg.user_role_id);
    const bEl = document.getElementById('autoRoleBot');
    if (bEl && cfg.bot_role_id) bEl.value = String(cfg.bot_role_id);
}

async function saveAutoRole() {
    const gid = document.getElementById('drawerGuildId')?.value;
    if (!gid) return showToast('Thiếu server ID', 'warning');
    const body = {
        user_role_id: document.getElementById('autoRoleUser')?.value || null,
        bot_role_id: document.getElementById('autoRoleBot')?.value || null
    };
    const res = await apiRequest(`/api/guilds/${gid}/autorole`, 'POST', body);
    if (res.ok) {
        showToast(res.message || 'Đã lưu cấu hình Auto Role', 'success');
        await loadAutoRole(gid);
    } else {
        showToast(res.error || 'Lỗi lưu Auto Role', 'error');
    }
}




async function loadStreakConfig(guildId) {
    const gid = guildId || document.getElementById('drawerGuildId')?.value;
    if (!gid) return;
    const res = await apiRequest(`/api/guilds/${gid}/streak`);
    if (!res.ok) return;
    const cfg = res.config || {};
    const chEl = document.getElementById('streakChannel');
    if (chEl && cfg.channel_id) chEl.value = String(cfg.channel_id);
    const cntEl = document.getElementById('streakActiveCount');
    if (cntEl) cntEl.innerText = `${cfg.active_users || 0} thành viên`;
}

async function saveStreakConfig() {
    const gid = document.getElementById('drawerGuildId')?.value;
    if (!gid) return showToast('Thiếu server ID', 'warning');
    const channel_id = document.getElementById('streakChannel')?.value || null;
    const res = await apiRequest(`/api/guilds/${gid}/streak`, 'POST', { channel_id });
    if (res.ok) {
        showToast(res.message || 'Đã lưu cấu hình Kênh Streak', 'success');
        await loadStreakConfig(gid);
    } else {
        showToast(res.error || 'Lỗi lưu cấu hình Kênh Streak', 'error');
    }
}




async function loadGiveawayConfig(guildId) {
    const gid = guildId || document.getElementById('drawerGuildId')?.value;
    if (!gid) return;
    const box = document.getElementById('activeGiveawaysList');
    if (!box) return;
    const res = await apiRequest(`/api/guilds/${gid}/giveaways`);
    if (!res.ok) {
        box.innerHTML = `<div style="color:var(--accent-red);font-size:.85rem">${res.error || 'Lỗi tải Giveaway'}</div>`;
        return;
    }
    const gws = res.giveaways || [];
    if (!gws.length) {
        box.innerHTML = '<div style="color:var(--text-dim);font-size:.85rem;padding:8px 0">Không có sự kiện giveaway nào đang diễn ra.</div>';
        return;
    }
    box.innerHTML = gws.map(gw => `
        <div style="display:flex;justify-content:space-between;align-items:center;padding:12px 14px;background:var(--bg-card);border:1px solid var(--border-subtle);border-radius:10px;gap:12px;flex-wrap:wrap">
            <div>
                <div style="font-weight:700;color:var(--text-main);margin-bottom:4px">🎁 ${escapeHtml(gw.prize || 'Phần thưởng')}</div>
                <div style="font-size:.78rem;color:var(--text-dim)">
                    Kênh: #${escapeHtml(gw.channel_name || gw.channel_id)} • ${gw.winners || 1} người thắng • Kết thúc: ${escapeHtml(gw.end_time || gw.ends_at || '—')}
                </div>
            </div>
            <button class="btn btn-secondary btn-sm" style="color:var(--accent-orange)" onclick="endGuildGiveaway('${gw.message_id || gw.id}')">🏁 Kết thúc sớm</button>
        </div>
    `).join('');
}

async function createQuickGiveaway() {
    const gid = document.getElementById('drawerGuildId')?.value;
    if (!gid) return showToast('Thiếu server ID', 'warning');
    const channel_id = document.getElementById('giveawayChannel')?.value;
    const duration = document.getElementById('giveawayDuration')?.value.trim();
    const prize = document.getElementById('giveawayPrize')?.value.trim();
    const winners = parseInt(document.getElementById('giveawayWinners')?.value || '1');

    if (!channel_id) return showToast('Vui lòng chọn kênh tổ chức giveaway', 'warning');
    if (!duration) return showToast('Vui lòng nhập thời lượng (vd: 30m, 1h)', 'warning');
    if (!prize) return showToast('Vui lòng nhập phần thưởng giveaway', 'warning');

    const res = await apiRequest(`/api/guilds/${gid}/giveaways/create`, 'POST', {
        channel_id, duration, prize, winners
    });
    if (res.ok) {
        showToast(res.message || 'Đã tạo Giveaway thành công!', 'success');
        document.getElementById('giveawayPrize').value = '';
        document.getElementById('giveawayDuration').value = '';
        await loadGiveawayConfig(gid);
    } else {
        showToast(res.error || 'Lỗi tạo Giveaway', 'error');
    }
}

async function endGuildGiveaway(msgId) {
    const gid = document.getElementById('drawerGuildId')?.value;
    if (!gid) return;
    if (!confirm('Bạn có chắc muốn kết thúc Giveaway này ngay bây giờ?')) return;
    const res = await apiRequest(`/api/guilds/${gid}/giveaways/${msgId}/end`, 'POST', {});
    if (res.ok) {
        showToast(res.message || 'Đã kết thúc giveaway', 'success');
        await loadGiveawayConfig(gid);
    } else {
        showToast(res.error || 'Lỗi kết thúc giveaway', 'error');
    }
}




async function loadRuleConfig(guildId) {
    const gid = guildId || document.getElementById('drawerGuildId')?.value;
    if (!gid) return;
    const res = await apiRequest(`/api/guilds/${gid}/rule-config`);
    if (!res.ok) return;
    const cfg = res.config || {};
    const chEl = document.getElementById('ruleChannel');
    if (chEl && cfg.channel_id) chEl.value = String(cfg.channel_id);
    const rEl = document.getElementById('ruleRole');
    if (rEl && cfg.role_id) rEl.value = String(cfg.role_id);
}

async function saveRuleConfig() {
    const gid = document.getElementById('drawerGuildId')?.value;
    if (!gid) return showToast('Thiếu server ID', 'warning');
    const body = {
        channel_id: document.getElementById('ruleChannel')?.value || null,
        role_id: document.getElementById('ruleRole')?.value || null
    };
    const res = await apiRequest(`/api/guilds/${gid}/rule-config`, 'POST', body);
    if (res.ok) {
        showToast(res.message || 'Đã lưu cấu hình Kênh Nội Quy', 'success');
        await loadRuleConfig(gid);
    } else {
        showToast(res.error || 'Lỗi lưu cấu hình Kênh Nội Quy', 'error');
    }
}

async function publishRuleEmbed() {
    const gid = document.getElementById('drawerGuildId')?.value;
    if (!gid) return showToast('Thiếu server ID', 'warning');
    const chId = document.getElementById('ruleChannel')?.value;
    if (!chId) return showToast('Vui lòng chọn và lưu kênh nội quy trước khi đăng', 'warning');
    if (!confirm('Đăng bảng nội quy cùng nút bấm xác minh vào kênh đã chọn?')) return;
    showToast('Đang gửi bảng nội quy vào kênh...', 'info');
    const res = await apiRequest(`/api/guilds/${gid}/rule-config/publish`, 'POST', {});
    if (res.ok) {
        showToast(res.message || 'Đã đăng bảng nội quy thành công!', 'success');
    } else {
        showToast(res.error || 'Lỗi đăng bảng nội quy', 'error');
    }
}




let currentRrRoles = [];

function renderRrRolesTags() {
    const box = document.getElementById('rrConfiguredRolesBox');
    if (!box) return;
    if (!currentRrRoles.length) {
        box.innerHTML = '<span style="font-size:.82rem;color:var(--text-dim)">Chưa có role nào được thêm.</span>';
        return;
    }
    box.innerHTML = currentRrRoles.map((r, idx) => `
        <div style="background:rgba(255,255,255,0.06);border:1px solid var(--border-glass);padding:6px 12px;border-radius:8px;display:inline-flex;align-items:center;gap:8px;font-size:.85rem">
            <span>${escapeHtml(r.emoji_str || '⭐')}</span>
            <span style="font-weight:600">@${escapeHtml(r.role_name || r.label || r.role_id)}</span>
            <span class="badge" style="font-size:.7rem">${r.style}</span>
            <button type="button" onclick="removeRrRoleItem(${idx})" style="background:none;border:none;color:var(--accent-red);cursor:pointer;font-size:.9rem;padding:0;line-height:1">✖</button>
        </div>
    `).join('');
}

function addRrRoleItem() {
    const roleSel = document.getElementById('rrRoleSelect');
    if (!roleSel || !roleSel.value) return showToast('Vui lòng chọn vai trò', 'warning');
    const role_id = roleSel.value;
    const role_name = roleSel.options[roleSel.selectedIndex]?.textContent?.trim() || role_id;
    const emoji_str = document.getElementById('rrEmojiInput')?.value?.trim() || '⭐';
    const label = document.getElementById('rrLabelInput')?.value?.trim() || role_name;
    const style = document.getElementById('rrStyleSelect')?.value || 'secondary';

    currentRrRoles.push({ role_id, role_name, emoji_str, emoji: emoji_str, label, style });
    renderRrRolesTags();
    const eIn = document.getElementById('rrEmojiInput'); if (eIn) eIn.value = '';
    const lIn = document.getElementById('rrLabelInput'); if (lIn) lIn.value = '';
    showToast('Đã thêm vai trò vào danh sách', 'info');
}

function removeRrRoleItem(idx) {
    currentRrRoles.splice(idx, 1);
    renderRrRolesTags();
}

async function submitCreateReactionRole() {
    const gid = document.getElementById('drawerGuildId')?.value;
    if (!gid) return showToast('Thiếu server ID', 'warning');
    const channel_id = document.getElementById('rrChannel')?.value;
    if (!channel_id) return showToast('Vui lòng chọn kênh gửi bảng', 'warning');
    if (!currentRrRoles.length) return showToast('Vui lòng thêm ít nhất 1 role vào bảng', 'warning');

    const body = {
        channel_id,
        type: document.getElementById('rrType')?.value || 'button',
        mode: document.getElementById('rrMode')?.value || 'multi',
        title: document.getElementById('rrTitle')?.value || 'BẢNG CHỌN VAI TRÒ',
        description: document.getElementById('rrDesc')?.value || '',
        color: document.getElementById('rrColor')?.value || '#5865F2',
        image_url: document.getElementById('rrBanner')?.value?.trim() || '',
        roles: currentRrRoles
    };

    showToast('Đang gửi bảng Reaction Role...', 'info');
    const res = await apiRequest(`/api/guilds/${gid}/reaction-roles/create`, 'POST', body);
    if (res.ok) {
        showToast(res.message || 'Đã tạo bảng Reaction Role thành công!', 'success');
        currentRrRoles = [];
        renderRrRolesTags();
        await loadReactionRolesList(gid);
    } else {
        showToast(res.error || 'Lỗi tạo bảng Reaction Role', 'error');
    }
}

async function loadReactionRolesList(guildId) {
    const gid = guildId || document.getElementById('drawerGuildId')?.value;
    if (!gid) return;
    const box = document.getElementById('rrExistingPanelsList');
    if (!box) return;
    const res = await apiRequest(`/api/guilds/${gid}/reaction-roles`);
    if (!res.ok) {
        box.innerHTML = `<div style="color:var(--accent-red);font-size:.85rem">${res.error || 'Lỗi tải danh sách'}</div>`;
        return;
    }
    const panels = res.panels || [];
    if (!panels.length) {
        box.innerHTML = '<div style="color:var(--text-dim);font-size:.85rem">Chưa có bảng Reaction Role nào trong server.</div>';
        return;
    }
    box.innerHTML = panels.map(p => `
        <div style="display:flex;justify-content:space-between;align-items:center;padding:12px 14px;background:var(--bg-card);border:1px solid var(--border-glass);border-radius:10px">
            <div>
                <div style="font-weight:700;font-size:.92rem;color:var(--text-main)">${escapeHtml(p.title || 'Reaction Role')}</div>
                <div style="font-size:.78rem;color:var(--text-muted);margin-top:2px">
                    Kênh: <b style="color:var(--accent-cyan)">#${p.channel_id}</b> • Msg: <code>${p.message_id}</code> • Chế độ: <b>${p.mode}</b> • ${p.roles?.length || 0} roles
                </div>
            </div>
            <button class="btn btn-secondary btn-sm" style="color:var(--accent-red);border-color:rgba(239,68,68,0.3)" onclick="deleteReactionRole('${p.message_id}')">🗑️ Xóa bảng</button>
        </div>
    `).join('');
}

async function deleteReactionRole(msgId) {
    const gid = document.getElementById('drawerGuildId')?.value;
    if (!gid) return;
    if (!confirm('Bạn có chắc muốn xóa bảng Reaction Role này khỏi server?')) return;
    const res = await apiRequest(`/api/guilds/${gid}/reaction-roles/${msgId}`, 'DELETE');
    if (res.ok) {
        showToast('Đã xóa bảng Reaction Role', 'success');
        await loadReactionRolesList(gid);
    } else {
        showToast(res.error || 'Lỗi xóa bảng', 'error');
    }
}




const HOYO_GAMES = ['genshin', 'hsr', 'zzz', 'nte', 'endfield'];

async function loadHoyoConfig(guildId) {
    const gid = guildId || document.getElementById('drawerGuildId')?.value;
    if (!gid) return;
    const res = await apiRequest(`/api/guilds/${gid}/hoyo-config`);
    if (!res.ok) return;
    const configs = res.configs || {};
    HOYO_GAMES.forEach(game => {
        const c = configs[game] || {};
        const chEl = document.getElementById(`hoyoChannel_${game}`);
        if (chEl) chEl.value = c.channel_id ? String(c.channel_id) : '';
        const roleEl = document.getElementById(`hoyoRole_${game}`);
        if (roleEl) roleEl.value = c.role_id ? String(c.role_id) : '';
    });
}

async function saveHoyoConfig() {
    const gid = document.getElementById('drawerGuildId')?.value;
    if (!gid) return showToast('Thiếu server ID', 'warning');
    const configs = {};
    HOYO_GAMES.forEach(game => {
        const chEl = document.getElementById(`hoyoChannel_${game}`);
        const roleEl = document.getElementById(`hoyoRole_${game}`);
        configs[game] = {
            channel_id: chEl?.value || null,
            role_id: roleEl?.value || null
        };
    });
    const res = await apiRequest(`/api/guilds/${gid}/hoyo-config`, 'POST', { configs });
    if (res.ok) {
        showToast(res.message || 'Đã lưu cài đặt Hoyo Codes!', 'success');
        await loadHoyoConfig(gid);
    } else {
        showToast(res.error || 'Lỗi lưu cấu hình Hoyo Codes', 'error');
    }
}

async function submitPostHoyoCode() {
    const gid = document.getElementById('drawerGuildId')?.value;
    if (!gid) return showToast('Thiếu server ID', 'warning');
    const game = document.getElementById('hoyoPostGame')?.value || 'genshin';
    const code = document.getElementById('hoyoPostCode')?.value?.trim();
    if (!code) return showToast('Vui lòng nhập mã code', 'warning');
    const rewards = document.getElementById('hoyoPostRewards')?.value?.trim() || 'Quà tặng trong game';
    const hours = parseInt(document.getElementById('hoyoPostHours')?.value) || 48;

    showToast('Đang phát sóng mã code...', 'info');
    const res = await apiRequest(`/api/guilds/${gid}/hoyo-post-code`, 'POST', {
        game,
        game_key: game,
        code,
        rewards,
        hours
    });
    if (res.ok) {
        showToast(res.message || 'Đã gửi mã code lên kênh thành công!', 'success');
        const cIn = document.getElementById('hoyoPostCode'); if (cIn) cIn.value = '';
    } else {
        showToast(res.error || 'Lỗi gửi mã code', 'error');
    }
}

async function testHoyoDemoCode(gameKey) {
    const gid = document.getElementById('drawerGuildId')?.value;
    if (!gid) return showToast('Thiếu server ID', 'warning');
    const chEl = document.getElementById(`hoyoChannel_${gameKey}`);
    const roleEl = document.getElementById(`hoyoRole_${gameKey}`);
    const channel_id = chEl?.value;
    const role_id = roleEl?.value;
    if (!channel_id) return showToast(`Vui lòng chọn kênh thông báo cho ${gameKey.toUpperCase()} trước khi test!`, 'warning');

    showToast(`Đang gửi test code DEMO cho ${gameKey.toUpperCase()}...`, 'info');
    const res = await apiRequest(`/api/guilds/${gid}/hoyo-test-code`, 'POST', {
        game: gameKey,
        game_key: gameKey,
        channel_id: channel_id,
        role_id: role_id,
        code: 'DEMO',
        save: true
    });
    if (res.ok) {
        showToast(res.message || `Đã gửi code DEMO thành công!`, 'success');
    } else {
        showToast(res.error || 'Lỗi gửi test code DEMO', 'error');
    }
}





async function initAdminMinecraftTab() {
    await loadAdminMcGuildOptions();
    await loadAdminMinecraftServers();
    setupMcWebSocket();
}

async function loadAdminMcGuildOptions() {
    if (!state.guilds || !state.guilds.length) {
        try {
            const res = await apiRequest('/api/guilds');
            if (res.ok && Array.isArray(res.guilds)) {
                state.guilds = res.guilds;
            }
        } catch (e) {
            console.error('Error fetching guilds for MC admin:', e);
        }
    }
    const guilds = state.guilds || [];
    const opts = ['<option value="">— Chọn Máy Chủ Discord —</option>', ...guilds.map(g => `<option value="${g.id}">${escapeHtml(g.name)} (${g.id})</option>`)].join('');

    const sDirect = document.getElementById('mcDirectGuildSelect');
    const sRcon = document.getElementById('mcRconDirectGuildSelect');
    const sDetail = document.getElementById('mcDetailGuildSelect');
    if (sDirect) sDirect.innerHTML = opts;
    if (sRcon) sRcon.innerHTML = opts;
    if (sDetail) sDetail.innerHTML = opts;
}

function switchMcLinkMethod(method) {
    const btnPlugin = document.getElementById('btnMcLinkTabPlugin');
    const btnRcon = document.getElementById('btnMcLinkTabRcon');
    const panePlugin = document.getElementById('mcLinkPanePlugin');
    const paneRcon = document.getElementById('mcLinkPaneRcon');

    if (method === 'rcon') {
        if (btnPlugin) btnPlugin.classList.remove('active');
        if (btnRcon) btnRcon.classList.add('active');
        if (panePlugin) panePlugin.style.display = 'none';
        if (paneRcon) paneRcon.style.display = 'block';
    } else {
        if (btnPlugin) btnPlugin.classList.add('active');
        if (btnRcon) btnRcon.classList.remove('active');
        if (panePlugin) panePlugin.style.display = 'block';
        if (paneRcon) paneRcon.style.display = 'none';
    }
}

async function submitDirectMcLink() {
    const code = document.getElementById('mcDirectLinkCode')?.value?.trim();
    const guild_id = document.getElementById('mcDirectGuildSelect')?.value;

    if (!code) {
        return showToast('Vui lòng nhập mã kết nối sinh từ lệnh /discord server link trong Minecraft', 'warning');
    }
    if (!guild_id) {
        return showToast('Vui lòng chọn Discord Server để liên kết!', 'warning');
    }

    const payload = { guild_id };
    if (code.toUpperCase().startsWith('MCLINK-')) {
        payload.code = code.toUpperCase();
    } else {
        payload.server_id = code;
    }

    showToast('⏳ Đang xử lý liên kết máy chủ...', 'info');
    const res = await apiRequest('/api/mc/admin/server/link', 'POST', payload);
    if (res.ok) {
        showToast(res.message || 'Liên kết server Minecraft thành công!', 'success');
        const codeInput = document.getElementById('mcDirectLinkCode');
        if (codeInput) codeInput.value = '';
        await loadAdminMinecraftServers();
    } else {
        showToast(res.error || 'Lỗi liên kết server', 'error');
    }
}

async function submitDirectRconLink() {
    const host = document.getElementById('mcRconDirectHost')?.value?.trim() || '127.0.0.1';
    const port = parseInt(document.getElementById('mcRconDirectPort')?.value || '25565', 10);
    const rcon_port = parseInt(document.getElementById('mcRconDirectRconPort')?.value || '25575', 10);
    const rcon_password = document.getElementById('mcRconDirectPass')?.value || '';
    const guild_id = document.getElementById('mcRconDirectGuildSelect')?.value;

    if (!guild_id) {
        return showToast('Vui lòng chọn Discord Server để gán kết nối RCON!', 'warning');
    }

    showToast('⏳ Đang lưu cấu hình và kết nối thử qua RCON...', 'info');
    const res = await apiRequest(`/api/guilds/${guild_id}/mc-connection`, 'POST', {
        host,
        port,
        rcon_port,
        rcon_password,
        enabled: true
    });

    if (res.ok) {
        showToast(res.message || 'Đã lưu cấu hình RCON thành công!', 'success');
        await loadAdminMinecraftServers();
    } else {
        showToast(res.error || 'Lỗi lưu cấu hình RCON', 'error');
    }
}

async function loadAdminMinecraftServers() {
    const res = await apiRequest('/api/mc/admin/servers');
    if (!res.ok) {
        return showToast(res.error || 'Lỗi tải danh sách server Minecraft', 'error');
    }

    const servers = res.servers || [];
    state.adminMinecraft.servers = servers;

    const countBadge = document.getElementById('mcServersCountBadge');
    if (countBadge) countBadge.innerText = `${servers.length} Server`;

    renderAdminMinecraftServers(servers);
}

function renderAdminMinecraftServers(servers) {
    const grid = document.getElementById('mcServersGrid');
    if (!grid) return;

    if (!servers || servers.length === 0) {
        grid.innerHTML = `
            <div style="grid-column: 1 / -1; text-align: center; padding: 40px 20px; color: var(--text-dim);">
                <div style="font-size: 3rem; margin-bottom: 12px;">⛏️</div>
                <div style="font-size: 1.1rem; font-weight: 600; color: var(--text-main); margin-bottom: 6px;">Chưa phát hiện server Minecraft nào</div>
                <div style="max-width: 500px; margin: 0 auto; line-height: 1.6;">
                    Bạn có thể liên kết server bằng cách nhập <strong>Mã Plugin</strong> (gõ <code>/discord server link</code> trong Minecraft) hoặc điền thông tin <strong>RCON Console</strong> ở khung phía trên!
                </div>
            </div>
        `;
        return;
    }

    grid.innerHTML = servers.map(s => {
        const isOnline = !!s.is_online;
        const statusColor = isOnline ? '#10b981' : '#ef4444';
        const statusText = isOnline ? 'ONLINE' : 'OFFLINE';
        const isRcon = s.protocol === 'rcon';
        const protoBadge = isRcon
            ? `<span class="badge" style="background: rgba(245, 158, 11, 0.15); color: #f59e0b; border: 1px solid rgba(245, 158, 11, 0.3);">⚡ RCON</span>`
            : `<span class="badge" style="background: rgba(16, 185, 129, 0.15); color: #10b981; border: 1px solid rgba(16, 185, 129, 0.3);">🔌 PLUGIN</span>`;
        const guildName = s.guild_name ? `🏰 ${escapeHtml(s.guild_name)}` : '<span style="color:var(--text-dim);">Chưa nối Guild</span>';
        const onlineCount = s.online_players ? (Array.isArray(s.online_players) ? s.online_players.length : s.player_count || 0) : (s.player_count || 0);
        const maxPlayers = s.max_players || 50;
        const tps = Number(s.tps || 20.0).toFixed(1);

        return `
            <div class="glass-card" style="border: 1px solid var(--border-glass); background: var(--bg-card); cursor: pointer; transition: all 0.2s;" onclick="openMcServerDetail('${escapeHtml(s.server_key)}')" onmouseover="this.style.borderColor='var(--sakura-pink)'" onmouseout="this.style.borderColor='var(--border-glass)'">
                <div style="display: flex; justify-content: space-between; align-items: flex-start; gap: 10px; margin-bottom: 10px;">
                    <div>
                        <div style="font-weight: 700; font-size: 1.05rem; color: var(--text-main); display: flex; align-items: center; gap: 6px;">
                            <span>🎮</span> ${escapeHtml(s.server_name || s.server_key)}
                        </div>
                        <div style="font-size: 0.8rem; color: var(--text-dim); margin-top: 2px;">
                            ${escapeHtml(s.server_ip || '127.0.0.1')}:${s.server_port || 25565}
                        </div>
                    </div>
                    <div style="display: flex; gap: 6px; align-items: center;">
                        ${protoBadge}
                        <span class="badge" style="background: rgba(${isOnline ? '16,185,129' : '239,68,68'}, 0.15); color: ${statusColor}; border: 1px solid ${statusColor}44;">
                            ● ${statusText}
                        </span>
                    </div>
                </div>

                <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 8px; margin: 12px 0; font-size: 0.82rem;">
                    <div style="padding: 6px 10px; background: rgba(255,255,255,0.03); border-radius: 6px;">
                        <span style="color: var(--text-dim);">Online:</span>
                        <strong style="color: #38bdf8; margin-left: 4px;">${onlineCount}/${maxPlayers}</strong>
                    </div>
                    <div style="padding: 6px 10px; background: rgba(255,255,255,0.03); border-radius: 6px;">
                        <span style="color: var(--text-dim);">TPS:</span>
                        <strong style="color: #10b981; margin-left: 4px;">${tps}</strong>
                    </div>
                </div>

                <div style="display: flex; justify-content: space-between; align-items: center; border-top: 1px solid var(--border-subtle); padding-top: 10px; font-size: 0.8rem;">
                    <div style="white-space: nowrap; overflow: hidden; text-overflow: ellipsis; max-width: 190px;">
                        ${guildName}
                    </div>
                    <div>
                        <button class="btn btn-secondary btn-xs" onclick="event.stopPropagation(); openMcServerDetail('${escapeHtml(s.server_key)}')">
                            🔍 Chi Tiết
                        </button>
                    </div>
                </div>
            </div>
        `;
    }).join('');
}

async function openMcServerDetail(serverKey) {
    const modal = document.getElementById('mcServerDetailModal');
    if (!modal) return;

    let server = (state.adminMinecraft.servers || []).find(s => s.server_key === serverKey);

    try {
        const res = await apiRequest(`/api/mc/admin/server/detail?server_id=${encodeURIComponent(serverKey)}`);
        if (res.ok && res.server) {
            server = res.server;
        }
    } catch (e) {}

    if (!server) {
        return showToast('Không tìm thấy thông tin máy chủ', 'error');
    }

    state.adminMinecraft.selectedServerKey = serverKey;
    state.adminMinecraft.selectedDetailServer = server;

    const nameEl = document.getElementById('mcDetailServerName');
    const protoEl = document.getElementById('mcDetailProtocolBadge');
    const statusEl = document.getElementById('mcDetailStatusBadge');
    const hostPortEl = document.getElementById('mcDetailHostPort');
    const tpsEl = document.getElementById('mcDetailTps');
    const playersEl = document.getElementById('mcDetailPlayers');
    const pingEl = document.getElementById('mcDetailPing');
    const verEl = document.getElementById('mcDetailVersion');

    const isOnline = !!server.is_online;
    const isRcon = server.protocol === 'rcon';

    if (nameEl) nameEl.innerText = server.server_name || server.server_key;
    if (protoEl) {
        protoEl.innerText = isRcon ? '⚡ RCON' : '🔌 PLUGIN';
        protoEl.style.background = isRcon ? 'rgba(245,158,11,0.2)' : 'rgba(16,185,129,0.2)';
        protoEl.style.color = isRcon ? '#f59e0b' : '#10b981';
    }
    if (statusEl) {
        statusEl.innerText = isOnline ? '● ONLINE' : '● OFFLINE';
        statusEl.style.background = isOnline ? 'rgba(16,185,129,0.2)' : 'rgba(239,68,68,0.2)';
        statusEl.style.color = isOnline ? '#10b981' : '#ef4444';
    }
    if (hostPortEl) hostPortEl.innerText = `${server.server_ip || '127.0.0.1'}:${server.server_port || 25565}`;
    if (tpsEl) tpsEl.innerText = Number(server.tps || 20.0).toFixed(1);

    const onlineCount = server.online_players ? (Array.isArray(server.online_players) ? server.online_players.length : server.player_count || 0) : (server.player_count || 0);
    const maxPlayers = server.max_players || 50;
    if (playersEl) playersEl.innerText = `${onlineCount} / ${maxPlayers}`;
    if (pingEl) pingEl.innerText = server.ping != null ? `${server.ping} ms` : '-- ms';
    if (verEl) verEl.innerText = server.version || 'Paper 1.20+';

    
    const guildSel = document.getElementById('mcDetailGuildSelect');
    if (guildSel) {
        if (!state.guilds || !state.guilds.length) {
            await loadAdminMcGuildOptions();
        }
        guildSel.value = server.guild_id ? String(server.guild_id) : '';
    }

    
    const consoleAddrEl = document.getElementById('mcDetailConsoleAddress');
    const consoleCodeEl = document.getElementById('mcDetailConsoleCode');
    if (consoleAddrEl) {
        consoleAddrEl.innerText = server.console_address || `${server.server_ip || '127.0.0.1'}:${server.rcon_port || server.server_port || 25575}`;
    }
    if (consoleCodeEl) {
        consoleCodeEl.innerText = server.console_code || server.rcon_password || server.server_key || '••••••••';
    }

    
    const consoleOutEl = document.getElementById('mcDetailConsoleOutput');
    if (consoleOutEl) {
        consoleOutEl.innerHTML = `[Console sẵn sàng cho ${escapeHtml(server.server_name || server.server_key)}. Nhập lệnh bên dưới để điều khiển máy chủ...]`;
    }

    
    await loadChannelsForAdminMc(server.guild_id, server.chat_channel_id, server.log_channel_id, 'mcDetailChatSelect', 'mcDetailLogSelect');

    modal.style.display = 'flex';
}

function closeMcServerDetailModal() {
    const modal = document.getElementById('mcServerDetailModal');
    if (modal) modal.style.display = 'none';
}

async function sendMcDetailConsoleCommand(customCmd = null) {
    const inputEl = document.getElementById('mcDetailConsoleInput');
    const outputEl = document.getElementById('mcDetailConsoleOutput');
    const serverKey = state.adminMinecraft.selectedServerKey;
    if (!serverKey) return showToast('Chưa chọn server Minecraft', 'warning');

    const cmd = (customCmd !== null ? customCmd : (inputEl ? inputEl.value : '')).trim();
    if (!cmd) return showToast('Vui lòng nhập lệnh console', 'warning');

    if (inputEl && customCmd === null) inputEl.value = '';

    const timeStr = new Date().toLocaleTimeString();
    if (outputEl) {
        outputEl.innerHTML += `\n<span style="color:#38bdf8;">[${timeStr}] &gt; ${escapeHtml(cmd)}</span>`;
        outputEl.scrollTop = outputEl.scrollHeight;
    }

    try {
        const res = await apiRequest('/api/mc/admin/server/command', 'POST', {
            server_id: serverKey,
            command: cmd
        });

        if (outputEl) {
            if (res.ok) {
                const out = res.output ? res.output.trim() : (res.message || 'Lệnh đã được gửi thành công.');
                outputEl.innerHTML += `\n<span style="color:#10b981;">[${timeStr}] ${escapeHtml(out)}</span>`;
            } else {
                outputEl.innerHTML += `\n<span style="color:#ef4444;">[${timeStr}] LỖI: ${escapeHtml(res.error || 'Thực thi lệnh thất bại')}</span>`;
            }
            outputEl.scrollTop = outputEl.scrollHeight;
        }
    } catch (e) {
        if (outputEl) {
            outputEl.innerHTML += `\n<span style="color:#ef4444;">[${timeStr}] LỖI KẾT NỐI: ${escapeHtml(e.message || String(e))}</span>`;
            outputEl.scrollTop = outputEl.scrollHeight;
        }
    }
}

function sendMcDetailQuickCommand(cmd) {
    sendMcDetailConsoleCommand(cmd);
}

async function onMcDetailGuildChanged() {
    const guildSel = document.getElementById('mcDetailGuildSelect');
    const guildId = guildSel ? guildSel.value : '';
    await loadChannelsForAdminMc(guildId, null, null, 'mcDetailChatSelect', 'mcDetailLogSelect');
}

async function loadChannelsForAdminMc(guildId, selectedChatId = null, selectedLogId = null, chatElId = 'mcDetailChatSelect', logElId = 'mcDetailLogSelect') {
    const chatSel = document.getElementById(chatElId);
    const logSel = document.getElementById(logElId);
    if (!chatSel || !logSel) return;

    if (!guildId) {
        chatSel.innerHTML = '<option value="">— Vui lòng chọn Discord Server trước —</option>';
        logSel.innerHTML = '<option value="">— Vui lòng chọn Discord Server trước —</option>';
        return;
    }

    chatSel.innerHTML = '<option value="">⏳ Đang tải danh sách kênh...</option>';
    logSel.innerHTML = '<option value="">⏳ Đang tải danh sách kênh...</option>';

    try {
        const res = await apiRequest(`/api/guilds/${guildId}`);
        if (!res.ok || !res.guild) {
            chatSel.innerHTML = '<option value="">❌ Không thể tải kênh</option>';
            logSel.innerHTML = '<option value="">❌ Không thể tải kênh</option>';
            return;
        }

        const rawChannels = res.guild.channels || [];
        const isVoice = (t) => { const s = String(t).toLowerCase(); return s === '2' || s === '13' || s.includes('voice'); };
        const isCategory = (t) => { const s = String(t).toLowerCase(); return s === '4' || s.includes('category'); };
        let textChannels = rawChannels.filter(c => !isVoice(c.type) && !isCategory(c.type));
        if (!textChannels.length && rawChannels.length) {
            textChannels = rawChannels.filter(c => !isCategory(c.type));
        }

        let channelOpts = '<option value="">— Không chọn kênh —</option>';
        channelOpts += textChannels.map(c => {
            const cat = c.category ? ` [${escapeHtml(c.category)}]` : '';
            return `<option value="${c.id}"># ${escapeHtml(c.name)}${cat}</option>`;
        }).join('');

        chatSel.innerHTML = channelOpts;
        logSel.innerHTML = channelOpts;

        if (selectedChatId) chatSel.value = String(selectedChatId);
        if (selectedLogId) logSel.value = String(selectedLogId);
    } catch (e) {
        chatSel.innerHTML = '<option value="">❌ Lỗi kết nối tải kênh</option>';
        logSel.innerHTML = '<option value="">❌ Lỗi kết nối tải kênh</option>';
    }
}

async function testMcDetailServerLive() {
    const serverKey = state.adminMinecraft.selectedServerKey;
    if (!serverKey) return showToast('Chưa chọn server Minecraft', 'warning');

    const statusEl = document.getElementById('mcDetailStatusBadge');
    const pingEl = document.getElementById('mcDetailPing');
    const tpsEl = document.getElementById('mcDetailTps');

    if (statusEl) { statusEl.innerText = 'ĐANG TEST...'; statusEl.style.color = '#facc15'; }

    showToast('⏳ Đang kiểm tra kết nối live tới máy chủ...', 'info');
    const res = await apiRequest('/api/mc/admin/server/test', 'POST', { server_id: serverKey });
    if (res.ok) {
        const s = res.server || {};
        const isOnline = !!s.online;

        if (statusEl) {
            statusEl.innerText = isOnline ? '● ONLINE' : '● OFFLINE';
            statusEl.style.color = isOnline ? '#10b981' : '#ef4444';
            statusEl.style.background = isOnline ? 'rgba(16,185,129,0.2)' : 'rgba(239,68,68,0.2)';
        }
        if (pingEl) pingEl.innerText = isOnline ? `${s.latency_ms || 0} ms` : '-- ms';
        if (tpsEl && s.tps) tpsEl.innerText = Number(s.tps).toFixed(1);

        if (isOnline) {
            showToast(`✅ Server phản hồi tốt! Ping: ${s.latency_ms || 0}ms`, 'success');
        } else {
            showToast(`❌ Không thể kết nối tới server: ${s.error || 'Server offline'}`, 'error');
        }
    } else {
        showToast(res.error || 'Lỗi kiểm tra kết nối', 'error');
    }
}

async function saveMcDetailChannels() {
    const serverKey = state.adminMinecraft.selectedServerKey;
    if (!serverKey) return showToast('Chưa chọn server Minecraft', 'warning');

    const guild_id = document.getElementById('mcDetailGuildSelect')?.value || null;
    const chat_channel_id = document.getElementById('mcDetailChatSelect')?.value || null;
    const log_channel_id = document.getElementById('mcDetailLogSelect')?.value || null;

    if (!guild_id) {
        return showToast('Vui lòng chọn Discord Server để liên kết!', 'warning');
    }

    const res = await apiRequest('/api/mc/admin/server/config', 'POST', {
        server_id: serverKey,
        guild_id,
        chat_channel_id,
        log_channel_id
    });

    if (res.ok) {
        showToast(res.message || 'Lưu cấu hình kênh thành công!', 'success');
        await loadAdminMinecraftServers();
    } else {
        showToast(res.error || 'Lỗi lưu cấu hình kênh', 'error');
    }
}

async function unlinkSelectedMcServer() {
    const serverKey = state.adminMinecraft.selectedServerKey;
    if (!serverKey) return showToast('Chưa chọn server Minecraft', 'warning');
    const guild_id = document.getElementById('mcDetailGuildSelect')?.value || '';

    if (!confirm(`Bạn có chắc chắn muốn hủy liên kết máy chủ "${serverKey}"?`)) return;

    const res = await apiRequest('/api/mc/admin/server/unlink', 'POST', { server_id: serverKey, guild_id });
    if (res.ok) {
        showToast(res.message || 'Đã hủy liên kết máy chủ', 'success');
        closeMcServerDetailModal();
        await loadAdminMinecraftServers();
    } else {
        showToast(res.error || 'Lỗi hủy liên kết', 'error');
    }
}


function selectAdminMinecraftServer(serverKey) {
    openMcServerDetail(serverKey);
}
function openLinkMcServerModal(serverKey = '') {
    openMcServerDetail(serverKey);
}
function closeLinkMcServerModal() {
    closeMcServerDetailModal();
}

function setupMcWebSocket() {
    if (state.adminMinecraft.ws) return;
    try {
        const proto = location.protocol === 'https:' ? 'wss:' : 'ws:';
        const wsUrl = `${proto}//${location.host}/ws/logs?token=${encodeURIComponent(state.token)}`;
        const ws = new WebSocket(wsUrl);
        state.adminMinecraft.ws = ws;

        ws.onclose = () => {
            state.adminMinecraft.ws = null;
        };
    } catch (e) {
        console.warn('MC WS init error', e);
    }
}




async function testHoyoCode(gameKey) {
    const input = document.getElementById(`hoyoTestCode_${gameKey}`);
    const resBox = document.getElementById(`hoyoTestResult_${gameKey}`);
    if (!input) return;
    const code = input.value.trim();
    if (!code) {
        showToast('Vui lòng nhập mã code để test!', 'warning');
        return;
    }
    const guildId = document.getElementById('drawerGuildId') ? document.getElementById('drawerGuildId').value : null;
    if (!guildId) {
        showToast('Không xác định được ID Server!', 'error');
        return;
    }
    if (resBox) {
        resBox.style.display = 'block';
        resBox.innerHTML = '<span style="color:var(--text-dim);">⏳ Đang gửi thử nghiệm mã code qua bot...</span>';
    }
    const res = await apiRequest(`/api/guilds/${guildId}/hoyo-test-code`, 'POST', { game: gameKey, code });
    if (res.ok) {
        showToast(`✅ Đã test code ${code} thành công!`, 'success');
        if (resBox) {
            resBox.innerHTML = `<span style="color:var(--accent-green);">✅ Test thành công: ${escapeHtml(res.message || 'Đã gửi thông báo test tới kênh Discord')}</span>`;
        }
    } else {
        showToast(`❌ Thất bại: ${res.error || 'Lỗi gửi test'}`, 'error');
        if (resBox) {
            resBox.innerHTML = `<span style="color:var(--accent-red);">❌ Lỗi: ${escapeHtml(res.error || 'Không gửi được')}</span>`;
        }
    }
}




state.adminMining = {
    activeSubTab: 'user',
    catalogs: {},
    currentCatTab: 'picks',
    currentUser: null
};

function switchAdminMiningTab(sub) {
    state.adminMining.activeSubTab = sub;
    const userPane = document.getElementById('amPaneUser');
    const catPane = document.getElementById('amPaneCatalog');
    const ratesPane = document.getElementById('amPaneRates');
    const btnUser = document.getElementById('btnAmSubUser');
    const btnCat = document.getElementById('btnAmSubCatalog');
    const btnRates = document.getElementById('btnAmSubRates');

    if (userPane) userPane.style.display = sub === 'user' ? 'block' : 'none';
    if (catPane) catPane.style.display = sub === 'catalog' ? 'block' : 'none';
    if (ratesPane) ratesPane.style.display = sub === 'rates' ? 'block' : 'none';

    if (btnUser) btnUser.classList.toggle('active', sub === 'user');
    if (btnCat) btnCat.classList.toggle('active', sub === 'catalog');
    if (btnRates) btnRates.classList.toggle('active', sub === 'rates');

    if (sub === 'catalog') {
        loadMiningCatalogs();
    } else if (sub === 'rates') {
        loadGameRates();
    }
}

async function loadMiningCatalogs() {
    const res = await apiRequest('/api/mining/admin/catalogs');
    if (!res.ok) {
        showToast(res.error || 'Lỗi tải danh mục khoáng', 'error');
        return;
    }
    state.adminMining.catalogs = res.catalogs || {
        picks: res.picks,
        ores: res.ores,
        zones: res.zones,
        supplies: res.supplies,
        mutations: res.mutations
    };
    renderMiningCatalogContent();
}

function switchMiningCatalogCategory(cat) {
    state.adminMining.currentCatTab = cat;
    const btns = {
        picks: 'btnAmCatPicks',
        ores: 'btnAmCatOres',
        zones: 'btnAmCatZones',
        supplies: 'btnAmCatSupplies',
        mutations: 'btnAmCatMutations'
    };
    Object.keys(btns).forEach(k => {
        const b = document.getElementById(btns[k]);
        if (b) b.classList.toggle('active', k === cat);
    });
    renderMiningCatalogContent();
}

function renderMiningCatalogContent() {
    const container = document.getElementById('amCatalogTableContainer') || document.getElementById('miningCatalogContainer');
    if (!container) return;
    const cat = state.adminMining.currentCatTab || 'picks';
    const raw = (state.adminMining.catalogs && state.adminMining.catalogs[cat]) || {};
    const items = Array.isArray(raw) ? raw : Object.entries(raw).map(([k, v]) => ({ id: k, ...(typeof v === 'object' ? v : { val: v }) }));

    if (items.length === 0) {
        container.innerHTML = '<div style="text-align:center;padding:40px;color:var(--text-dim)">Chưa có dữ liệu cho mục này.</div>';
        return;
    }

    container.innerHTML = `
        <div style="display: grid; grid-template-columns: repeat(auto-fill, minmax(280px, 1fr)); gap: 14px;">
            ${items.map(it => {
                const icon = it.emoji || (cat === 'picks' ? '⛏️' : cat === 'ores' ? '💎' : cat === 'zones' ? '🗺️' : cat === 'supplies' ? '🧨' : '🧬');
                const price = it.price || it.sell_price || it.buy_price || 0;
                const rarity = it.rarity || '';
                const rBadge = RARITY_BADGES[rarity] || { bg: 'rgba(255,255,255,0.06)', color: 'var(--text-main)', label: rarity || 'Tiêu chuẩn' };
                return `
                    <div class="glass-card" style="padding: 14px; border-radius: 10px; display: flex; flex-direction: column; gap: 8px;">
                        <div style="display: flex; align-items: center; gap: 10px;">
                            <span style="font-size: 1.8rem;">${icon}</span>
                            <div style="flex: 1; min-width: 0;">
                                <strong style="color: var(--sakura-pink); font-size: 1rem; display: block; overflow: hidden; text-overflow: ellipsis; white-space: nowrap;">${escapeHtml(it.name || it.id)}</strong>
                                <div style="font-size: 0.75rem; color: var(--text-dim);">ID: <code>${escapeHtml(it.id)}</code></div>
                            </div>
                            ${rarity ? `<span class="badge" style="background:${rBadge.bg}; color:${rBadge.color}; font-size: 0.7rem;">${rBadge.label}</span>` : ''}
                        </div>
                        <div style="font-size: 0.82rem; color: var(--text-color); flex: 1;">${escapeHtml(it.desc || it.description || 'Không có mô tả')}</div>
                        <div style="display: flex; justify-content: space-between; align-items: center; font-size: 0.8rem; border-top: 1px solid rgba(255,255,255,0.06); padding-top: 8px; margin-top: 4px;">
                            <span style="color: #ffd700; font-weight: 700;">💰 ${Number(price).toLocaleString()} Coins</span>
                            ${it.durability ? `<span style="color: #38bdf8;">🛡️ Bền: ${it.durability}</span>` : ''}
                            ${it.fortune ? `<span style="color: #4ade80;">🍀 Fortune: +${it.fortune}</span>` : ''}
                            ${it.depth_req ? `<span style="color: #c084fc;">⬇️ ${it.depth_req}m</span>` : ''}
                        </div>
                    </div>
                `;
            }).join('')}
        </div>
    `;
}

async function loadAdminMiningUsersList() {
    const sel = document.getElementById('amQuickUserSelect');
    if (!sel) return;
    try {
        const res = await apiRequest('/api/mining/admin/users');
        if (res.ok && Array.isArray(res.users)) {
            sel.innerHTML = '<option value="">-- Chọn nhanh thợ mỏ (' + res.users.length + ') --</option>' +
                res.users.map(u => `<option value="${escapeHtml(u.user_id)}">${escapeHtml(u.username)} (${Number(u.total_mined || 0).toLocaleString()} quặng)</option>`).join('');
            
            
            if (!state.adminMining.currentUser && res.users.length > 0) {
                const firstUser = res.users[0];
                const input = document.getElementById('amSearchUserId');
                if (input && (!input.value || input.value === '1144785664458637394' || input.value === 'auto')) {
                    input.value = firstUser.user_id;
                    amSearchUser(firstUser.user_id);
                }
            }
        }
    } catch (e) {
        console.error('Error loading mining users:', e);
    }
}

function amOnQuickUserChange() {
    const sel = document.getElementById('amQuickUserSelect');
    const input = document.getElementById('amSearchUserId');
    if (sel && sel.value) {
        if (input) input.value = sel.value;
        amSearchUser(sel.value);
    }
}

async function initAdminMiningTab() {
    await loadMiningCatalogs();
    await loadAdminMiningUsersList();
    const sel = document.getElementById('amQuickUserSelect');
    const input = document.getElementById('amSearchUserId');
    if (state.adminMining.currentUser && state.adminMining.currentUser.user_id) {
        amSearchUser(state.adminMining.currentUser.user_id);
    } else if (sel && sel.value) {
        if (input) input.value = sel.value;
        amSearchUser(sel.value);
    } else {
        const adminId = state.session?.discord_id || state.currentUser?.id || state.user?.discord_id || state.user?.user_id || 'auto';
        if (input && !input.value) input.value = adminId;
        amSearchUser(adminId);
    }
}

function amLoadSelfUser() {
    const adminId = state.session?.discord_id || state.currentUser?.id || state.user?.discord_id || state.user?.user_id || 'auto';
    const input = document.getElementById('amSearchUserId');
    if (input) input.value = adminId;
    amSearchUser(adminId);
}

async function amSearchUser(targetUid = null) {
    const input = document.getElementById('amSearchUserId') || document.getElementById('amUserIdInput');
    const uid = (targetUid !== null && targetUid !== undefined && targetUid !== '') ? String(targetUid) : (input ? input.value.trim() : (state.adminMining.currentUser?.user_id || ''));
    if (!uid) {
        showToast('Vui lòng nhập Discord User ID hoặc Tên thợ mỏ!', 'warning');
        return;
    }
    if (input) input.value = uid;

    
    const match = uid.match(/\b\d{6,22}\b/);
    const cleanId = match ? match[0] : uid.replace(/[<@!#>\s]/g, '').trim();

    showToast('⏳ Đang tra cứu thông tin thợ mỏ...', 'info');

    try {
        const res = await apiRequest(`/api/mining/admin/user?user_id=${encodeURIComponent(cleanId || uid)}`);
        if (!res.ok) {
            showToast(`❌ ${res.error || 'Không tìm thấy người dùng'}`, 'error');
            return;
        }

        state.adminMining.currentUser = { user_id: res.user_id || cleanId, ...res.data };
        renderMiningUserProfile(res);
        showToast(`✅ Đã tải thông tin thợ mỏ: ${res.username || res.user_id}`, 'success');
    } catch (err) {
        console.error('amSearchUser error:', err);
        showToast('❌ Lỗi kết nối khi tra cứu thợ mỏ!', 'error');
    }
}

function renderMiningUserProfile(res) {
    const data = res.data || {};
    const infoContainer = document.getElementById('amUserInfoContainer');
    if (infoContainer) infoContainer.style.display = 'block';

    const avatarEl = document.getElementById('amUserAvatar');
    if (avatarEl) avatarEl.src = res.avatar || 'https://cdn.discordapp.com/embed/avatars/0.png';

    const nameEl = document.getElementById('amUserName');
    if (nameEl) nameEl.innerText = res.username || `User ${res.user_id}`;

    const idEl = document.getElementById('amUserId');
    if (idEl) idEl.innerText = `ID: ${res.user_id}`;

    const badgeEl = document.getElementById('amUserBadge');
    if (badgeEl) badgeEl.innerText = (data.zone ? data.zone.toUpperCase().replace('_', ' ') : 'HANG ĐẤT');

    const depthEl = document.getElementById('amUserDepth');
    if (depthEl) depthEl.innerText = `${data.stats?.depth || 0}m`;

    const staminaEl = document.getElementById('amUserStamina');
    if (staminaEl) staminaEl.innerText = `${data.stamina !== undefined ? data.stamina : 100} / ${data.max_stamina || 100}`;

    const minedEl = document.getElementById('amUserTotalMined');
    if (minedEl) minedEl.innerText = Number(data.stats?.total_mined || 0).toLocaleString();

    const museumCount = Array.isArray(data.museum) ? data.museum.length : Object.keys(data.museum || {}).length;
    const museumEl = document.getElementById('amUserMuseumCount');
    if (museumEl) museumEl.innerText = `${museumCount} mẫu vật`;

    
    const eqPickId = data.equipped_pick || 'pick_wooden';
    const pick = data.picks?.[eqPickId] || { name: eqPickId, refine: 0, stars: 0, durability: 60, max_durability: 60 };

    const pickNameEl = document.getElementById('amPickName');
    if (pickNameEl) pickNameEl.innerText = pick.name || eqPickId;

    const pickStarsEl = document.getElementById('amPickStars');
    if (pickStarsEl) pickStarsEl.innerText = `${pick.stars || 0}⭐`;

    const pickRefineEl = document.getElementById('amPickRefine');
    if (pickRefineEl) pickRefineEl.innerText = `+${pick.refine || 0}`;

    const durText = document.getElementById('amPickDurabilityText');
    if (durText) durText.innerText = `${pick.durability || 0} / ${pick.max_durability || 60}`;

    const durBar = document.getElementById('amPickDurabilityBar');
    if (durBar) {
        const maxD = pick.max_durability || 60;
        const curD = pick.durability || 0;
        const pct = Math.max(0, Math.min(100, Math.round((curD / maxD) * 100)));
        durBar.style.width = `${pct}%`;
        durBar.style.background = pct > 50 ? '#4ade80' : pct > 20 ? '#fbbf24' : '#ef4444';
    }

    const enchantEl = document.getElementById('amPickEnchantText');
    if (enchantEl) {
        enchantEl.innerText = pick.enchant ? `✨ Dòng Enchant: ${pick.enchant}` : '✨ Dòng Enchant: Chưa có';
    }

    
    const oreBag = data.ore_bag || [];
    const bagCountEl = document.getElementById('amBagCount');
    if (bagCountEl) bagCountEl.innerText = `${oreBag.length}/${data.max_bag || 30} viên`;

    const oresContainer = document.getElementById('amOresContainer');
    if (oresContainer) {
        if (oreBag.length === 0) {
            oresContainer.innerHTML = '<div style="grid-column: 1 / -1; padding: 20px; text-align: center; color: var(--text-dim);">Túi quặng đang trống.</div>';
        } else {
            oresContainer.innerHTML = oreBag.map((ore, idx) => {
                const r = RARITY_BADGES[ore.rarity] || RARITY_BADGES.common;
                return `
                    <div style="background: rgba(255,255,255,0.03); border: 1px solid var(--border-glass); border-radius: 8px; padding: 10px; display: flex; flex-direction: column; gap: 4px;">
                        <strong style="color: var(--text-main); font-size: 0.9rem;">${escapeHtml(ore.name || ore.id)}</strong>
                        <div style="font-size: 0.75rem; color: var(--text-dim);">${ore.weight || 1} kg ${ore.depth ? `(${ore.depth}m)` : ''}</div>
                        <span class="badge" style="background:${r.bg}; color:${r.color}; font-size:0.7rem; align-self: flex-start;">${r.label}</span>
                    </div>
                `;
            }).join('');
        }
    }

    
    const supplies = data.supplies || {};
    const suppliesContainer = document.getElementById('amSuppliesContainer');
    if (suppliesContainer) {
        const entries = Object.entries(supplies);
        if (entries.length === 0) {
            suppliesContainer.innerHTML = '<div style="padding: 10px; text-align: center; color: var(--text-dim);">Chưa có vật tư nào.</div>';
        } else {
            suppliesContainer.innerHTML = entries.map(([sid, cnt]) => `
                <div style="display: flex; justify-content: space-between; align-items: center; padding: 8px 12px; background: rgba(255,255,255,0.03); border-radius: 6px; border: 1px solid var(--border-glass);">
                    <span style="font-weight: 600; color: var(--text-main);">${escapeHtml(sid)}</span>
                    <strong style="color: #ffd700;">x${Number(cnt).toLocaleString()}</strong>
                </div>
            `).join('');
        }
    }
}

async function amActionDirect(action, extraPayload = {}) {
    if (!state.adminMining.currentUser) {
        showToast('Vui lòng tra cứu thợ mỏ trước!', 'warning');
        return;
    }
    const uid = state.adminMining.currentUser.user_id;
    const res = await apiRequest('/api/mining/admin/user/action', 'POST', {
        user_id: uid,
        action,
        ...extraPayload
    });
    if (res.ok) {
        showToast('✅ Thao tác thành công!', 'success');
        amSearchUser(uid);
    } else {
        showToast(`❌ Thất bại: ${res.error || 'Lỗi thao tác'}`, 'error');
    }
}

async function amActionPrompt(action) {
    if (!state.adminMining.currentUser) {
        showToast('Vui lòng tra cứu thợ mỏ trước!', 'warning');
        return;
    }
    const curr = state.adminMining.currentUser;
    const eqPick = curr.picks?.[curr.equipped_pick] || {};

    if (action === 'repair_pick') {
        amActionDirect('repair_pick');
        return;
    } else if (action === 'set_refine') {
        const val = prompt('Nhập cấp Cường Hóa mới (0 - 150):', eqPick.refine || 0);
        if (val === null) return;
        const num = parseInt(val, 10);
        if (isNaN(num) || num < 0 || num > 150) {
            showToast('Cấp refine phải từ 0 đến 150!', 'warning');
            return;
        }
        amActionDirect('set_refine', { refine: num });
    } else if (action === 'set_stars') {
        const val = prompt('Nhập số Sao mới (0 - 20 ⭐):', eqPick.stars || 0);
        if (val === null) return;
        const num = parseInt(val, 10);
        if (isNaN(num) || num < 0 || num > 20) {
            showToast('Số sao phải từ 0 đến 20!', 'warning');
            return;
        }
        amActionDirect('set_stars', { stars: num });
    } else if (action === 'give_pick') {
        const pickId = prompt('Nhập ID Cuốc muốn cấp (ví dụ: pick_wooden, pick_iron, pick_diamond, pick_netherite, pick_sakura):', 'pick_diamond');
        if (!pickId) return;
        amActionDirect('give_pick', { pick_id: pickId.trim() });
    } else if (action === 'add_ore') {
        const oreId = prompt('Nhập ID Quặng (ví dụ: stone, iron, gold, diamond, netherite, ruby, amethyste, emerald):', 'diamond');
        if (!oreId) return;
        const amount = prompt('Nhập số lượng quặng muốn thêm:', '10');
        if (amount === null) return;
        amActionDirect('add_ore', { ore_id: oreId.trim(), count: parseInt(amount, 10) || 1 });
    } else if (action === 'add_supply') {
        const supId = prompt('Nhập ID Vật tư (ví dụ: bomb, tnt, stamina_pot, drill, lucky_charm):', 'tnt');
        if (!supId) return;
        const amount = prompt('Nhập số lượng vật tư:', '5');
        if (amount === null) return;
        amActionDirect('add_supply', { supply_id: supId.trim(), count: parseInt(amount, 10) || 1 });
    } else if (action === 'unlock_museum') {
        amActionDirect('unlock_museum');
    }
}

function amOpenCreateItemModal() {
    const modal = document.getElementById('amCreateItemModal') || document.getElementById('modalCreateMiningItem');
    if (modal) {
        modal.classList.add('active');
        modal.style.display = 'flex';
        amOnChangeNewItemType();
    }
}

function amCloseCreateItemModal() {
    const modal = document.getElementById('amCreateItemModal') || document.getElementById('modalCreateMiningItem');
    if (modal) {
        modal.classList.remove('active');
        modal.style.display = 'none';
    }
}

function amOnChangeNewItemType() {
    const type = document.getElementById('amNewItemType')?.value || 'pickaxe';
    const isPick = (type === 'pickaxe' || type === 'pick');
    const pickGroup = document.getElementById('amPickaxeExtraFields') || document.getElementById('amPickFields');
    const oreGroup = document.getElementById('amOreExtraFields') || document.getElementById('amOreFields');
    if (pickGroup) pickGroup.style.display = isPick ? 'block' : 'none';
    if (oreGroup) oreGroup.style.display = isPick ? 'none' : 'block';
}

async function amSubmitCreateItem() {
    const type = document.getElementById('amNewItemType')?.value || 'pickaxe';
    const id = document.getElementById('amNewItemId')?.value.trim();
    const name = document.getElementById('amNewItemName')?.value.trim();
    const isPick = (type === 'pickaxe' || type === 'pick');
    const priceInput = document.getElementById('amNewItemPrice') || (isPick ? document.getElementById('amNewPickPrice') : document.getElementById('amNewOrePrice'));
    const price = parseInt(priceInput?.value || '0', 10);
    const desc = document.getElementById('amNewItemDesc')?.value.trim() || '';

    if (!id || !name) {
        showToast('Vui lòng nhập ID và Tên vật phẩm!', 'warning');
        return;
    }

    const payload = { type: isPick ? 'pickaxe' : 'ore', id, name, price, desc };
    if (isPick) {
        const duraInput = document.getElementById('amNewItemDura') || document.getElementById('amNewPickDurability');
        const speedInput = document.getElementById('amNewItemSpeed') || document.getElementById('amNewPickPower');
        const fortuneInput = document.getElementById('amNewItemFortune') || document.getElementById('amNewPickLuck');
        const depthInput = document.getElementById('amNewItemDepth');
        payload.durability = parseInt(duraInput?.value || '100', 10);
        payload.speed = parseFloat(speedInput?.value || '1.0');
        payload.power = payload.speed;
        payload.fortune = parseFloat(fortuneInput?.value || '0');
        payload.luck = payload.fortune;
        payload.depth = depthInput?.value.trim() || '0m';
    } else {
        const rarityInput = document.getElementById('amNewItemRarity') || document.getElementById('amNewOreRarity');
        payload.rarity = rarityInput?.value || 'common';
    }

    const res = await apiRequest('/api/mining/admin/item/create', 'POST', payload);
    if (res.ok) {
        showToast(`✅ Tạo vật phẩm ${name} thành công!`, 'success');
        amCloseCreateItemModal();
        if (typeof loadMiningCatalogs === 'function') {
            loadMiningCatalogs();
        }
    } else {
        showToast(`❌ Thất bại: ${res.error || 'Lỗi tạo vật phẩm'}`, 'error');
    }
}




function updateRateSliderLabel(sliderId) {
    const slider = document.getElementById(sliderId);
    if (!slider) return;
    const val = parseFloat(slider.value).toFixed(1);
    const label = document.getElementById(`${sliderId}Val`);
    if (label) label.textContent = `${val}x`;
    const numInput = document.getElementById(`${sliderId}Num`);
    if (numInput && numInput.value !== slider.value) {
        numInput.value = slider.value;
    }
}

function syncRateNumToSlider(sliderId) {
    const numInput = document.getElementById(`${sliderId}Num`);
    const slider = document.getElementById(sliderId);
    if (!numInput || !slider) return;
    slider.value = numInput.value;
    const label = document.getElementById(`${sliderId}Val`);
    if (label) label.textContent = `${parseFloat(slider.value).toFixed(1)}x`;
}

function syncRateSliders(keySuffix, val) {
    ['gr', 'amGr'].forEach(prefix => {
        const slider = document.getElementById(`${prefix}${keySuffix}`);
        const num = document.getElementById(`${prefix}${keySuffix}Num`);
        const lbl = document.getElementById(`${prefix}${keySuffix}Val`);
        if (slider) slider.value = val;
        if (num) num.value = val;
        if (lbl) lbl.textContent = `${parseFloat(val).toFixed(1)}x`;
    });
}

function syncRateSwitches(keySuffix, isActive) {
    ['gr', 'amGr'].forEach(prefix => {
        const sw = document.getElementById(`${prefix}${keySuffix}`);
        if (sw) sw.classList.toggle('on', !!isActive);
    });
}

async function loadGameRates() {
    try {
        const res = await apiRequest('/api/admin/rates');
        if (!res.ok || !res.rates) return;
        const r = res.rates;

        syncRateSwitches('GodModeRefine', !!r.god_mode_refine);
        syncRateSwitches('GodModeStar', !!r.god_mode_star);

        syncRateSliders('RefineMult', r.refine_mult ?? 1.0);
        syncRateSliders('StarMult', r.star_mult ?? 1.0);
        syncRateSliders('FishingLuckMult', r.fishing_luck_mult ?? 1.0);
        syncRateSliders('FishingMutMult', r.fishing_mutation_mult ?? 1.0);
        syncRateSliders('FishingChestMult', r.fishing_chest_mult ?? 1.0);
        syncRateSliders('MiningLuckMult', r.mining_luck_mult ?? 1.0);
        syncRateSliders('MiningRareMult', r.mining_rare_mult ?? 1.0);
        syncRateSliders('MiningMutMult', r.mining_mutation_mult ?? 1.0);
    } catch (err) {
        console.error('Error loading game rates:', err);
    }
}

async function saveGameRates() {
    const getSwitch = (id1, id2) => {
        const el = document.getElementById(id1) || document.getElementById(id2);
        return el ? el.classList.contains('on') : false;
    };
    const getFloat = (id1, id2, def = 1.0) => {
        const el = document.getElementById(id1) || document.getElementById(id2);
        return el ? parseFloat(el.value) || def : def;
    };

    const payload = {
        god_mode_refine: getSwitch('grGodModeRefine', 'amGrGodModeRefine'),
        god_mode_star: getSwitch('grGodModeStar', 'amGrGodModeStar'),
        refine_mult: getFloat('grRefineMult', 'amGrRefineMult', 1.0),
        star_mult: getFloat('grStarMult', 'amGrStarMult', 1.0),
        fishing_luck_mult: getFloat('grFishingLuckMult', 'amGrFishingLuckMult', 1.0),
        fishing_mutation_mult: getFloat('grFishingMutMult', 'amGrFishingMutMult', 1.0),
        fishing_chest_mult: getFloat('grFishingChestMult', 'amGrFishingChestMult', 1.0),
        mining_luck_mult: getFloat('grMiningLuckMult', 'amGrMiningLuckMult', 1.0),
        mining_rare_mult: getFloat('grMiningRareMult', 'amGrMiningRareMult', 1.0),
        mining_mutation_mult: getFloat('grMiningMutMult', 'amGrMiningMutMult', 1.0),
    };

    const res = await apiRequest('/api/admin/rates', 'POST', payload);
    if (res.ok) {
        showToast('✅ Đã lưu cấu hình tỉ lệ & God Mode thành công!', 'success');
        loadGameRates();
    } else {
        showToast(`❌ Thất bại: ${res.error || 'Lỗi lưu cấu hình tỉ lệ'}`, 'error');
    }
}

function applyRatePreset(preset) {
    if (preset === 'default') {
        syncRateSwitches('GodModeRefine', false);
        syncRateSwitches('GodModeStar', false);
        syncRateSliders('RefineMult', 1.0);
        syncRateSliders('StarMult', 1.0);
        syncRateSliders('FishingLuckMult', 1.0);
        syncRateSliders('FishingMutMult', 1.0);
        syncRateSliders('FishingChestMult', 1.0);
        syncRateSliders('MiningLuckMult', 1.0);
        syncRateSliders('MiningRareMult', 1.0);
        syncRateSliders('MiningMutMult', 1.0);
        showToast('⚡ Đã nạp Preset Mặc Định (1.0x). Đang lưu...', 'info');
    } else if (preset === 'luck2x') {
        syncRateSwitches('GodModeRefine', false);
        syncRateSwitches('GodModeStar', false);
        syncRateSliders('RefineMult', 2.0);
        syncRateSliders('StarMult', 2.0);
        syncRateSliders('FishingLuckMult', 2.0);
        syncRateSliders('FishingMutMult', 2.0);
        syncRateSliders('FishingChestMult', 2.0);
        syncRateSliders('MiningLuckMult', 2.0);
        syncRateSliders('MiningRareMult', 2.0);
        syncRateSliders('MiningMutMult', 2.0);
        showToast('🍀 Đã nạp Preset May Mắn x2. Đang lưu...', 'info');
    } else if (preset === 'forge5x') {
        syncRateSwitches('GodModeRefine', false);
        syncRateSwitches('GodModeStar', false);
        syncRateSliders('RefineMult', 5.0);
        syncRateSliders('StarMult', 3.0);
        syncRateSliders('FishingLuckMult', 2.0);
        syncRateSliders('FishingMutMult', 2.0);
        syncRateSliders('FishingChestMult', 2.0);
        syncRateSliders('MiningLuckMult', 2.0);
        syncRateSliders('MiningRareMult', 2.0);
        syncRateSliders('MiningMutMult', 2.0);
        showToast('🔨 Đã nạp Preset Thần Rèn (+5x đập đồ). Đang lưu...', 'info');
    } else if (preset === 'godmode') {
        syncRateSwitches('GodModeRefine', true);
        syncRateSwitches('GodModeStar', true);
        syncRateSliders('RefineMult', 10.0);
        syncRateSliders('StarMult', 10.0);
        syncRateSliders('FishingLuckMult', 5.0);
        syncRateSliders('FishingMutMult', 5.0);
        syncRateSliders('FishingChestMult', 5.0);
        syncRateSliders('MiningLuckMult', 5.0);
        syncRateSliders('MiningRareMult', 5.0);
        syncRateSliders('MiningMutMult', 5.0);
        showToast('👑 Đã kích hoạt GOD MODE 100%! Đang lưu...', 'success');
    }
    saveGameRates();
}




function switchGuildMcSubTab(sub) {
    const btnRcon = document.getElementById('btnGmcTabRcon') || document.getElementById('btnGuildMcRcon');
    const btnPlugin = document.getElementById('btnGmcTabPlugin') || document.getElementById('btnGuildMcPlugin');
    const tabRcon = document.getElementById('gmcSubPaneRcon') || document.getElementById('tabGuildMcRcon');
    const tabPlugin = document.getElementById('gmcSubPanePlugin') || document.getElementById('tabGuildMcPlugin');

    if (btnRcon) btnRcon.classList.toggle('active', sub === 'rcon');
    if (btnPlugin) btnPlugin.classList.toggle('active', sub === 'plugin');
    if (tabRcon) tabRcon.style.display = sub === 'rcon' ? 'block' : 'none';
    if (tabPlugin) tabPlugin.style.display = sub === 'plugin' ? 'block' : 'none';
}

async function loadGuildMcConnection(guildId) {
    if (!guildId) return;
    const res = await apiRequest(`/api/guilds/${guildId}/mc-connection`);
    if (!res.ok) return;

    const data = res.data || res.config || {};
    const rcon = data.rcon || { host: data.rcon_host || data.host, port: data.rcon_port, password: data.rcon_password };
    const plugin = data.plugin || { api_key: data.api_key };

    const setVal = (id, val) => {
        const el = document.getElementById(id);
        if (el) el.value = val !== undefined && val !== null ? val : '';
    };

    setVal('gmcHost', data.host || '');
    setVal('gmcPort', data.port || 25565);
    setVal('gmcRconPort', rcon.port || data.rcon_port || 25575);
    setVal('gmcRconPassword', rcon.password || data.rcon_password || '');
    setVal('gmcQueryPort', data.query_port || 25565);
    setVal('gmcApiKey', plugin.api_key || '');

    
    const mcChatSel = document.getElementById('gmcChatChannel');
    const mcLogSel = document.getElementById('gmcLogChannel');
    if (mcChatSel && mcChatSel.options.length <= 1) {
        try {
            const gRes = await apiRequest(`/api/guilds/${guildId}`);
            if (gRes.ok && gRes.guild && gRes.guild.channels) {
                const isCat = (t) => String(t).toLowerCase() === '4' || String(t).includes('category');
                const isV = (t) => String(t).toLowerCase() === '2' || String(t).toLowerCase() === '13';
                const tChans = gRes.guild.channels.filter(c => !isCat(c.type) && !isV(c.type));
                let optsChat = '<option value="">— Chưa chọn kênh chat —</option>';
                let optsLog = '<option value="">— Chưa chọn kênh log —</option>';
                tChans.forEach(c => {
                    const tag = c.category ? ` [${c.category}]` : '';
                    optsChat += `<option value="${c.id}"># ${escapeHtml(c.name)}${tag}</option>`;
                    optsLog += `<option value="${c.id}"># ${escapeHtml(c.name)}${tag}</option>`;
                });
                mcChatSel.innerHTML = optsChat;
                if (mcLogSel) mcLogSel.innerHTML = optsLog;
            }
        } catch(e) {}
    }

    const savedChat = data.chat_channel_id || data.chat_channel || '';
    const savedLog = data.log_channel_id || data.log_channel || '';
    if (mcChatSel && savedChat) mcChatSel.value = String(savedChat);
    if (mcLogSel && savedLog) mcLogSel.value = String(savedLog);

    const autoSyncSwitch = document.getElementById('gmcSwitchAutoSync');
    if (autoSyncSwitch) {
        autoSyncSwitch.classList.toggle('on', data.auto_sync_chat !== false);
    }

    
    const connectedCard = document.getElementById('gmcPluginConnectedCard');
    const connectedName = document.getElementById('gmcPluginServerName');
    try {
        const sRes = await apiRequest('/api/mc/admin/servers');
        if (sRes.ok && Array.isArray(sRes.servers)) {
            const linkedServer = sRes.servers.find(s => String(s.guild_id) === String(guildId));
            if (linkedServer && connectedCard) {
                connectedCard.style.display = 'block';
                if (connectedName) connectedName.innerText = `Máy chủ: ${linkedServer.server_name || linkedServer.server_id} (${linkedServer.server_ip || linkedServer.ip}:${linkedServer.server_port || linkedServer.port}) • TPS: ${linkedServer.tps || 20.0}`;
            } else if (connectedCard) {
                connectedCard.style.display = 'none';
            }
        }
    } catch (e) {}
}

async function saveGuildMcConnection() {
    const guildId = document.getElementById('drawerGuildId')?.value;
    if (!guildId) return;

    const hostVal = document.getElementById('gmcHost')?.value.trim() || '';
    const portVal = parseInt(document.getElementById('gmcPort')?.value || '25565', 10);
    const rconPortVal = parseInt(document.getElementById('gmcRconPort')?.value || '25575', 10);
    const rconPassVal = document.getElementById('gmcRconPassword')?.value || '';
    const chatChVal = document.getElementById('gmcChatChannel')?.value || '';
    const logChVal = document.getElementById('gmcLogChannel')?.value || '';
    const autoSync = document.getElementById('gmcSwitchAutoSync')?.classList.contains('on') ?? true;

    const payload = {
        mode: 'rcon',
        host: hostVal,
        port: portVal,
        query_port: parseInt(document.getElementById('gmcQueryPort')?.value || '25565', 10),
        chat_channel_id: chatChVal,
        log_channel_id: logChVal,
        chat_channel: chatChVal,
        log_channel: logChVal,
        auto_sync_chat: autoSync,
        rcon_host: hostVal,
        rcon_port: rconPortVal,
        rcon_password: rconPassVal,
        rcon: {
            host: hostVal,
            port: rconPortVal,
            password: rconPassVal
        },
        plugin: {
            api_key: document.getElementById('gmcApiKey')?.value.trim() || ''
        }
    };

    const res = await apiRequest(`/api/guilds/${guildId}/mc-connection`, 'POST', payload);
    if (res.ok) {
        showToast('✅ Đã lưu cấu hình kết nối Minecraft!', 'success');
        await loadGuildMcConnection(guildId);
        testGuildMcConnection();
    } else {
        showToast(`❌ Thất bại: ${res.error || 'Lỗi lưu cấu hình'}`, 'error');
    }
}

async function testGuildMcConnection() {
    const guildId = document.getElementById('drawerGuildId')?.value;
    if (!guildId) return;

    const card = document.getElementById('gmcStatusCard');
    if (card) card.style.display = 'block';

    const sBadge = document.getElementById('gmcLiveStatusBadge');
    const sPing = document.getElementById('gmcLivePing');
    const sVer = document.getElementById('gmcLiveVersion');
    const sPlayers = document.getElementById('gmcLivePlayers');
    const sRcon = document.getElementById('gmcLiveRcon');
    const sMotd = document.getElementById('gmcLiveMotd');

    if (sBadge) { sBadge.style.background = '#64748b'; sBadge.innerText = '⏳ ĐANG TEST...'; }
    if (sRcon) { sRcon.style.color = '#facc15'; sRcon.innerText = 'Đang kiểm tra RCON...'; }

    const hostVal = document.getElementById('gmcHost')?.value.trim() || '';
    const portVal = parseInt(document.getElementById('gmcPort')?.value || '25565', 10);
    const rconPortVal = parseInt(document.getElementById('gmcRconPort')?.value || '25575', 10);
    const rconPassVal = document.getElementById('gmcRconPassword')?.value || '';

    const testPayload = {
        host: hostVal,
        port: portVal,
        rcon_host: hostVal,
        rcon_port: rconPortVal,
        rcon_password: rconPassVal,
        rcon: {
            host: hostVal,
            port: rconPortVal,
            password: rconPassVal
        }
    };

    showToast('⏳ Đang kiểm tra kết nối Server Minecraft & RCON...', 'info');
    const res = await apiRequest(`/api/guilds/${guildId}/mc-connection/test`, 'POST', testPayload);
    if (res.ok) {
        const s = res.server || {};
        const r = res.rcon || {};

        if (s.online) {
            if (sBadge) { sBadge.style.background = '#22c55e'; sBadge.innerText = '🟢 SERVER ONLINE'; }
            if (sPing) sPing.innerText = `Ping: ${s.latency_ms || 0} ms`;
            if (sVer) sVer.innerText = `Phiên bản: ${s.version || 'Paper/Spigot'}`;
            if (sPlayers) sPlayers.innerText = `${s.players_online || 0} / ${s.players_max || 0}`;
            if (sMotd) sMotd.innerText = s.motd || '—';
        } else {
            if (sBadge) { sBadge.style.background = '#ef4444'; sBadge.innerText = '🔴 SERVER OFFLINE'; }
            if (sPing) sPing.innerText = 'Ping: Timeout / Refused';
            if (sVer) sVer.innerText = s.error ? `Lỗi: ${s.error}` : 'Không phản hồi';
            if (sPlayers) sPlayers.innerText = '0 / 0';
            if (sMotd) sMotd.innerText = s.error || 'Không thể ping đến máy chủ';
        }

        if (r.connected) {
            if (sRcon) { sRcon.style.color = '#22c55e'; sRcon.innerText = '🟢 Đã Kết Nối (Hoạt Động)'; }
            showToast(`✅ Server & RCON hoạt động tốt! Ping: ${s.latency_ms || 0}ms`, 'success');
        } else {
            if (sRcon) { sRcon.style.color = '#ef4444'; sRcon.innerText = `🔴 Lỗi: ${r.message || 'Thất bại'}`; }
            if (s.online) {
                showToast(`⚠️ Server Online (${s.latency_ms || 0}ms) nhưng RCON thất bại: ${r.message}`, 'warning');
            } else {
                showToast(`❌ Server không phản hồi: ${s.error || r.message}`, 'error');
            }
        }
    } else {
        if (sBadge) { sBadge.style.background = '#ef4444'; sBadge.innerText = '🔴 LỖI KẾT NỐI'; }
        if (sRcon) { sRcon.style.color = '#ef4444'; sRcon.innerText = res.error || 'Lỗi'; }
        showToast(`❌ Kiểm tra thất bại: ${res.error || 'Server không phản hồi'}`, 'error');
    }
}

async function sendGuildMcCommand() {
    const guildId = document.getElementById('drawerGuildId')?.value;
    const input = document.getElementById('gmcRconCmdInput') || document.getElementById('gmcCmdInput');
    const cmd = input ? input.value.trim() : '';
    if (!guildId || !cmd) return showToast('Vui lòng nhập lệnh trước khi gửi!', 'warning');

    const outBox = document.getElementById('gmcRconOutputBox');
    if (outBox) {
        outBox.style.display = 'block';
        outBox.innerText = `> ${cmd}
[Đang gửi lệnh...]`;
    }

    const res = await apiRequest(`/api/guilds/${guildId}/mc-connection/command`, 'POST', { command: cmd });
    if (res.ok) {
        const out = res.output || res.response || res.message || '(Không có phản hồi từ console)';
        showToast(`✅ Đã gửi lệnh thành công!`, 'success');
        if (outBox) {
            outBox.style.display = 'block';
            outBox.innerText = `> ${cmd}
${out}`;
        }
        if (input) input.value = '';
    } else {
        const err = res.error || 'Không thực thi được lệnh';
        showToast(`❌ Lỗi: ${err}`, 'error');
        if (outBox) {
            outBox.style.display = 'block';
            outBox.innerText = `> ${cmd}
❌ [LỖI] ${err}`;
        }
    }
}

async function submitGuildMcPluginLinkCode() {
    const guildId = document.getElementById('drawerGuildId')?.value;
    const input = document.getElementById('gmcPluginLinkCode') || document.getElementById('gmcLinkCodeInput');
    const code = input ? input.value.trim().toUpperCase() : '';
    if (!code) {
        showToast('Vui lòng nhập mã liên kết từ in-game (/discord server link)!', 'warning');
        return;
    }
    if (!guildId) {
        showToast('Vui lòng chọn Discord Server trước!', 'warning');
        return;
    }
    const res = await apiRequest('/api/mc/admin/server/link', 'POST', { guild_id: guildId, code: code });
    if (res.ok) {
        showToast(`✅ Đã nối thành công Minecraft Server với Discord!`, 'success');
        if (input) input.value = '';
        await loadGuildMcConnection(guildId);
    } else {
        showToast(`❌ Thất bại: ${res.error || 'Mã không hợp lệ hoặc đã hết hạn'}`, 'error');
    }
}

async function unlinkGuildMcPlugin() {
    if (!confirm('Bạn có chắc muốn hủy liên kết server Minecraft này khỏi Discord Guild?')) return;
    const guildId = document.getElementById('drawerGuildId')?.value;
    if (!guildId) return;
    const res = await apiRequest('/api/mc/admin/server/unlink', 'POST', { guild_id: guildId });
    if (res.ok) {
        showToast('✅ Đã hủy liên kết máy chủ Minecraft!', 'success');
        await loadGuildMcConnection(guildId);
    } else {
        showToast(res.error || 'Lỗi hủy liên kết', 'error');
    }
}




state.pluginCommands = [];
state.pluginCategories = [];

async function loadPluginCommands() {
    const container = document.getElementById('pluginCommandsContainer');
    const tbody = document.getElementById('pluginCommandsTableBody');
    if (container) container.innerHTML = '<div style="text-align:center;padding:30px;color:var(--text-dim)">⏳ Đang nạp danh sách lệnh từ Plugin Sakura...</div>';
    if (tbody) tbody.innerHTML = '<tr><td colspan="4" style="text-align:center;padding:20px;color:var(--text-dim)">⏳ Đang nạp danh sách lệnh từ Plugin Sakura...</td></tr>';

    const res = await apiRequest('/api/bot/plugin-commands');
    if (!res.ok) {
        const errHtml = `<div style="text-align:center;padding:24px;color:var(--accent-red);background:rgba(239,68,68,0.08);border-radius:12px">❌ ${escapeHtml(res.error || 'Không thể tải lệnh plugin')}</div>`;
        if (container) container.innerHTML = errHtml;
        if (tbody) tbody.innerHTML = `<tr><td colspan="4" style="text-align:center;color:var(--accent-red)">❌ ${escapeHtml(res.error || 'Không thể tải lệnh plugin')}</td></tr>`;
        return;
    }

    state.pluginCommands = res.commands || [];
    state.pluginCategories = res.categories || [];
    renderPluginCommandsTable(state.pluginCommands);
}

function filterPluginCommandsTable() {
    const q = (document.getElementById('pluginCmdSearch')?.value || document.getElementById('pluginCommandsSearch')?.value || '').toLowerCase().trim();
    if (!q) {
        renderPluginCommandsTable(state.pluginCommands);
        return;
    }
    const filtered = state.pluginCommands.filter(c => {
        const name = (c.name || c.command || '').toLowerCase();
        const desc = (c.description || '').toLowerCase();
        const cat = (c.category || '').toLowerCase();
        const perm = (c.permission || '').toLowerCase();
        const aliases = (c.aliases || []).join(' ').toLowerCase();
        return name.includes(q) || desc.includes(q) || cat.includes(q) || perm.includes(q) || aliases.includes(q);
    });
    renderPluginCommandsTable(filtered);
}

function renderPluginCommandsTable(commands) {
    const container = document.getElementById('pluginCommandsContainer');
    const tbody = document.getElementById('pluginCommandsTableBody');

    if (tbody) {
        if (!commands || commands.length === 0) {
            tbody.innerHTML = '<tr><td colspan="4" style="text-align:center;padding:24px;color:var(--text-dim)">Không tìm thấy lệnh phù hợp.</td></tr>';
        } else {
            tbody.innerHTML = commands.map(c => `
                <tr>
                    <td><strong style="color:var(--sakura-light);font-size:1rem;"><code>/${escapeHtml(c.command || c.name)}</code></strong></td>
                    <td><span class="badge badge-secondary">${escapeHtml(c.category || 'chung')}</span></td>
                    <td>${escapeHtml(c.description || 'Chưa có mô tả')}</td>
                    <td><span style="font-size:0.8rem;color:var(--text-dim);"><code>${escapeHtml(c.permission || 'sakura.use')}</code></span></td>
                </tr>
            `).join('');
        }
    }

    if (!container) return;

    if (!commands || commands.length === 0) {
        container.innerHTML = '<div style="text-align:center;padding:36px;color:var(--text-dim);background:var(--bg-card);border:1px solid var(--border-glass);border-radius:12px;">🔍 Không tìm thấy lệnh nào phù hợp với từ khóa.</div>';
        return;
    }

    
    const catTitles = {
        economy: '💰 Kinh Tế & Tiền Tệ',
        teleport: '🚀 Dịch Chuyển & Nhà Cửa',
        survival: '🛡️ Sinh Tồn & Lãnh Thổ',
        skills: '⚡ Kỹ Năng & Thử Thách',
        admin: '👑 Quản Trị & Cấu Hình OP',
        bot: '🌸 Tích Hợp SakuraBot',
        other: '📦 Các Lệnh Khác'
    };

    const grouped = {};
    commands.forEach(cmd => {
        const cat = cmd.category || 'other';
        if (!grouped[cat]) grouped[cat] = [];
        grouped[cat].push(cmd);
    });

    let html = '';
    for (const [catKey, cmdList] of Object.entries(grouped)) {
        const title = catTitles[catKey] || `📂 ${catKey.toUpperCase()}`;
        html += `
        <div style="background:var(--bg-card);border:1px solid var(--border-glass);border-radius:14px;overflow:hidden;box-shadow:0 4px 20px rgba(0,0,0,0.15)">
            <div style="padding:12px 18px;background:rgba(255,255,255,0.03);border-bottom:1px solid var(--border-glass);display:flex;justify-content:space-between;align-items:center">
                <div style="font-weight:700;font-size:1rem;color:var(--sakura-light)">${escapeHtml(title)}</div>
                <span class="badge badge-sakura" style="font-size:0.75rem">${cmdList.length} lệnh</span>
            </div>
            <div style="overflow-x:auto">
                <table class="table" style="margin-bottom:0;width:100%">
                    <thead>
                        <tr>
                            <th style="width:200px">Lệnh & Cú Pháp</th>
                            <th style="width:260px">Quyền Hạn (Permission)</th>
                            <th>Mô Tả & Chức Năng</th>
                        </tr>
                    </thead>
                    <tbody>
                        ${cmdList.map(c => {
                            const cName = c.command || c.name;
                            const aliasesHtml = (c.aliases && c.aliases.length > 0)
                                ? `<div style="margin-top:4px;display:flex;gap:4px;flex-wrap:wrap">
                                    <span style="font-size:0.7rem;color:var(--text-dim)">Alias:</span>
                                    ${c.aliases.map(a => `<code style="font-size:0.72rem;background:rgba(255,255,255,0.06);padding:1px 5px;border-radius:4px;color:var(--accent-cyan)">/${escapeHtml(a)}</code>`).join('')}
                                   </div>`
                                : '';
                            return `
                            <tr>
                                <td style="vertical-align:top">
                                    <div style="font-weight:700;font-size:0.95rem;color:var(--sakura-pink)">
                                        <code>/${escapeHtml(cName)}</code>
                                    </div>
                                    ${c.usage && c.usage !== `/${cName}` ? `<div style="font-size:0.78rem;color:var(--text-dim);margin-top:2px"><code>${escapeHtml(c.usage)}</code></div>` : ''}
                                    ${aliasesHtml}
                                </td>
                                <td style="vertical-align:top">
                                    <code style="font-size:0.78rem;background:rgba(168,85,247,0.12);color:#c084fc;padding:2px 6px;border-radius:4px;word-break:break-all">
                                        ${escapeHtml(c.permission || `sakura.${cName}`)}
                                    </code>
                                </td>
                                <td style="vertical-align:top;color:var(--text-main);font-size:0.88rem">
                                    ${escapeHtml(c.description || 'Chưa có mô tả')}
                                </td>
                            </tr>
                            `;
                        }).join('')}
                    </tbody>
                </table>
            </div>
        </div>
        `;
    }

    container.innerHTML = html;
}




state.wordChain = {
    page: 1,
    limit: 30,
    total: 0,
    pages: 1,
    query: '',
    words: [],
    leaderboard: []
};

async function loadWordChainManagement() {
    await Promise.all([
        loadWordChainStats(),
        loadWordChainWords(1),
        loadWordChainLeaderboard()
    ]);
}

async function loadWordChainStats() {
    const res = await apiRequest('/api/wordchain/stats');
    if (res.ok) {
        const tw = document.getElementById('wcTotalWordsCount');
        const ag = document.getElementById('wcActiveGamesCount');
        const tp = document.getElementById('wcTotalPlayersCount');
        if (tw) tw.innerText = Number(res.total_words || 0).toLocaleString();
        if (ag) ag.innerText = Number(res.active_games || 0).toLocaleString();
        if (tp) tp.innerText = Number(res.total_players || 0).toLocaleString();
    }
}

async function loadWordChainWords(page = 1, query = '') {
    state.wordChain.page = page;
    state.wordChain.query = query !== undefined ? query : state.wordChain.query;
    const tbody = document.getElementById('wcWordsTableBody');
    if (tbody) tbody.innerHTML = '<tr><td colspan="2" style="text-align:center;padding:20px;color:var(--text-dim)">⏳ Đang tải từ điển...</td></tr>';

    const qParam = encodeURIComponent(state.wordChain.query || '');
    const res = await apiRequest(`/api/wordchain/words?page=${page}&limit=${state.wordChain.limit}&q=${qParam}`);
    if (!res.ok) {
        if (tbody) tbody.innerHTML = `<tr><td colspan="2" style="text-align:center;color:var(--accent-red)">❌ ${escapeHtml(res.error || 'Lỗi tải từ điển')}</td></tr>`;
        return;
    }

    state.wordChain.words = res.words || [];
    state.wordChain.total = res.total || 0;
    state.wordChain.pages = res.pages || 1;

    
    const pInfo = document.getElementById('wcPaginationInfo');
    if (pInfo) {
        pInfo.innerText = `Trang ${page} / ${state.wordChain.pages} (${state.wordChain.total.toLocaleString()} từ)`;
    }
    const prevBtn = document.getElementById('wcPrevPageBtn');
    const nextBtn = document.getElementById('wcNextPageBtn');
    if (prevBtn) prevBtn.disabled = page <= 1;
    if (nextBtn) nextBtn.disabled = page >= state.wordChain.pages;

    if (!state.wordChain.words.length) {
        if (tbody) tbody.innerHTML = '<tr><td colspan="2" style="text-align:center;padding:24px;color:var(--text-dim)">🔍 Không tìm thấy từ nào phù hợp.</td></tr>';
        return;
    }

    if (tbody) {
        tbody.innerHTML = state.wordChain.words.map(w => `
            <tr>
                <td style="font-weight:600;font-size:0.95rem;color:var(--text-main)">
                    <code>${escapeHtml(w)}</code>
                </td>
                <td style="text-align:center">
                    <button type="button" class="btn btn-secondary btn-xs" style="color:var(--accent-red);border-color:rgba(239,68,68,0.3)" onclick="deleteWordChainWord('${escapeHtml(w)}')">
                        🗑️ Xóa
                    </button>
                </td>
            </tr>
        `).join('');
    }
}

function changeWcPage(delta) {
    const newPage = state.wordChain.page + delta;
    if (newPage >= 1 && newPage <= state.wordChain.pages) {
        loadWordChainWords(newPage);
    }
}

function searchWordChainWords() {
    const q = (document.getElementById('wcSearchInput')?.value || '').trim();
    loadWordChainWords(1, q);
}

function resetWordChainSearch() {
    const inEl = document.getElementById('wcSearchInput');
    if (inEl) inEl.value = '';
    loadWordChainWords(1, '');
}

async function submitAddWordChainWord() {
    const inEl = document.getElementById('wcNewWordInput');
    const word = inEl?.value?.trim().toLowerCase();
    if (!word) return showToast('Vui lòng nhập từ cần thêm', 'warning');

    const tokens = word.split(/\s+/);
    if (tokens.length !== 2) {
        return showToast('Từ vựng phải gồm đúng 2 âm tiết (vd: hoa hồng, nhà cửa)', 'warning');
    }

    showToast(`Đang thêm từ '${word}'...`, 'info');
    const res = await apiRequest('/api/wordchain/words/add', 'POST', { word });
    if (res.ok) {
        showToast(res.message || 'Đã thêm từ thành công!', 'success');
        if (inEl) inEl.value = '';
        await loadWordChainStats();
        await loadWordChainWords(1, '');
    } else {
        showToast(res.error || 'Lỗi thêm từ', 'error');
    }
}

async function deleteWordChainWord(word) {
    if (!confirm(`Bạn có chắc muốn xóa từ "${word}" khỏi từ điển nối chữ?`)) return;

    showToast(`Đang xóa từ '${word}'...`, 'info');
    const res = await apiRequest('/api/wordchain/words/delete', 'POST', { word });
    if (res.ok) {
        showToast(res.message || 'Đã xóa từ thành công!', 'success');
        await loadWordChainStats();
        await loadWordChainWords(state.wordChain.page);
    } else {
        showToast(res.error || 'Lỗi xóa từ', 'error');
    }
}

async function loadWordChainLeaderboard() {
    const lbType = document.getElementById('wcLbTypeSelect')?.value || 'all';
    const tbody = document.getElementById('wcLeaderboardTableBody');
    if (tbody) tbody.innerHTML = '<tr><td colspan="4" style="text-align:center;padding:20px;color:var(--text-dim)">⏳ Đang nạp BXH nối chữ...</td></tr>';

    const res = await apiRequest(`/api/wordchain/leaderboard?type=${lbType}`);
    if (!res.ok) {
        if (tbody) tbody.innerHTML = `<tr><td colspan="4" style="text-align:center;color:var(--accent-red)">❌ ${escapeHtml(res.error || 'Lỗi tải BXH')}</td></tr>`;
        return;
    }

    const items = res.leaderboard || [];
    if (!items.length) {
        if (tbody) tbody.innerHTML = '<tr><td colspan="4" style="text-align:center;padding:24px;color:var(--text-dim)">Chưa có dữ liệu điểm số nối chữ.</td></tr>';
        return;
    }

    if (tbody) {
        tbody.innerHTML = items.map((item, idx) => {
            let rankBadge = `<span style="font-weight:700;color:var(--text-dim)">#${item.rank}</span>`;
            if (item.rank === 1) rankBadge = '🥇';
            else if (item.rank === 2) rankBadge = '🥈';
            else if (item.rank === 3) rankBadge = '🥉';

            const avatarSrc = item.avatar || 'https://raw.githubusercontent.com/twitter/twemoji/master/assets/72x72/1f338.png';

            return `
            <tr>
                <td style="text-align:center;font-size:1.1rem">${rankBadge}</td>
                <td>
                    <div style="display:flex;align-items:center;gap:10px">
                        <img src="${avatarSrc}" style="width:32px;height:32px;border-radius:50%;border:1px solid var(--border-glass);object-fit:cover" onerror="this.src='https://raw.githubusercontent.com/twitter/twemoji/master/assets/72x72/1f338.png'">
                        <div>
                            <div style="font-weight:700;font-size:0.92rem;color:var(--text-main)">${escapeHtml(item.username)}</div>
                            <div style="font-size:0.75rem;color:var(--text-muted)"><code>${item.user_id}</code></div>
                        </div>
                    </div>
                </td>
                <td style="text-align:right">
                    <span class="badge badge-sakura" style="font-size:0.9rem;font-weight:700">${Number(item.score).toLocaleString()} điểm</span>
                </td>
                <td style="text-align:center">
                    <div style="display:inline-flex;gap:4px">
                        <button type="button" class="btn btn-secondary btn-xs" onclick="promptAdjustWcScore('${item.user_id}', 5)" title="+5 điểm">➕</button>
                        <button type="button" class="btn btn-secondary btn-xs" onclick="promptAdjustWcScore('${item.user_id}', -5)" title="-5 điểm">➖</button>
                    </div>
                </td>
            </tr>
            `;
        }).join('');
    }
}

async function promptAdjustWcScore(userId, defaultDelta) {
    const input = prompt(`Nhập số điểm cần điều chỉnh cho User ${userId} (số âm để trừ):`, defaultDelta);
    if (input === null) return;
    const delta = parseInt(input);
    if (isNaN(delta) || delta === 0) return showToast('Số điểm không hợp lệ', 'warning');

    const lbType = document.getElementById('wcLbTypeSelect')?.value || 'all';
    showToast(`Đang điều chỉnh điểm...`, 'info');
    const res = await apiRequest('/api/wordchain/scores/adjust', 'POST', {
        user_id: userId,
        delta: delta,
        type: lbType
    });
    if (res.ok) {
        showToast(res.message || 'Đã cập nhật điểm thành công!', 'success');
        await loadWordChainLeaderboard();
    } else {
        showToast(res.error || 'Lỗi cập nhật điểm', 'error');
    }
}








state.adminFishing.currentAquariumUser = null;

async function loadAdminAquariumList() {
    const res = await apiRequest('/api/fishing/admin/aquariums');
    if (!res.ok) {
        showToast(res.error || 'Lỗi tải danh sách Thủy Cung', 'error');
        return;
    }
    const list = res.aquariums || [];
    const countBadge = document.getElementById('afAqTotalCountBadge');
    if (countBadge) countBadge.innerText = `${list.length} Bể Cá`;

    const tbody = document.getElementById('afAqAllTableBody');
    if (!tbody) return;

    if (list.length === 0) {
        tbody.innerHTML = `<tr><td colspan="6" style="text-align: center; padding: 30px; color: var(--text-dim);">Chưa có cần thủ nào nuôi cá trong Thủy Cung.</td></tr>`;
        return;
    }

    tbody.innerHTML = list.map(aq => {
        return `
            <tr style="border-bottom: 1px solid rgba(255,255,255,0.04); transition: background 0.2s;" onmouseover="this.style.background='rgba(255,255,255,0.02)'" onmouseout="this.style.background='transparent'">
                <td style="padding: 12px 10px;">
                    <div style="display: flex; align-items: center; gap: 10px;">
                        <img src="${aq.avatar || 'https://cdn.discordapp.com/embed/avatars/0.png'}" style="width: 38px; height: 38px; border-radius: 50%; object-fit: cover; border: 2px solid #06b6d4;">
                        <div>
                            <strong style="color: var(--text-main); font-size: 0.95rem;">${escapeHtml(aq.username)}</strong>
                            <div style="font-size: 0.75rem; color: var(--text-dim);">${aq.tank_preview && aq.tank_preview.length ? aq.tank_preview.map(f => f.name).join(', ') : 'Chưa có cá'}</div>
                        </div>
                    </div>
                </td>
                <td style="padding: 12px 10px;"><code style="font-size: 0.8rem; background: rgba(0,0,0,0.3); padding: 2px 6px; border-radius: 4px;">${aq.user_id}</code></td>
                <td style="padding: 12px 10px; text-align: center;">
                    <span class="badge" style="background: rgba(6,182,212,0.15); color: #38bdf8; font-weight: 700;">${aq.fish_count} / ${aq.slots} ô</span>
                </td>
                <td style="padding: 12px 10px;">
                    <span style="color: #fde047; font-size: 0.88rem;">${aq.mascot ? `⭐ ${escapeHtml(aq.mascot)}` : '<span style="color: var(--text-dim);">Chưa đặt</span>'}</span>
                </td>
                <td style="padding: 12px 10px; text-align: center;">
                    <span class="badge" style="background: rgba(244,63,94,0.15); color: #fb7185; font-weight: 700;">❤️ ${aq.likes}</span>
                </td>
                <td style="padding: 12px 10px; text-align: right;">
                    <button class="btn btn-primary btn-sm" onclick="afInspectAquarium('${aq.user_id}')" style="background: #0284c7; border: none;">🔍 Xem Bể Cá</button>
                </td>
            </tr>
        `;
    }).join('');
}

async function afInspectAquarium(userId) {
    const input = document.getElementById('afAqSearchUserId');
    if (input) input.value = userId;
    await afSearchAquarium();
    
    const container = document.getElementById('afAqDetailContainer');
    if (container) container.scrollIntoView({ behavior: 'smooth', block: 'start' });
}

async function afSearchAquarium() {
    const input = document.getElementById('afAqSearchUserId');
    const uid = input ? input.value.trim() : '';
    if (!uid) {
        showToast('Vui lòng nhập Discord User ID cần thủ!', 'warning');
        return;
    }
    const cleanId = uid.replace(/[<@!>]/g, '');
    showToast('⏳ Đang tra cứu Thủy Cung cần thủ...', 'info');

    const res = await apiRequest(`/api/fishing/admin/user?user_id=${cleanId}`);
    if (!res.ok) {
        showToast(res.error || 'Không tìm thấy dữ liệu cần thủ', 'error');
        return;
    }

    state.adminFishing.currentAquariumUser = { user_id: cleanId, ...res };
    renderAquariumView(res);
}

function afLoadAdminAquarium() {
    const adminId = state.session?.discord_id || '1144785664458637394';
    const input = document.getElementById('afAqSearchUserId');
    if (input) input.value = adminId;
    afSearchAquarium();
}

function renderAquariumView(res) {
    const udata = res.data || {};
    const placeholder = document.getElementById('afAqUserPlaceholder');
    const detail = document.getElementById('afAqDetailContainer');
    if (placeholder) placeholder.style.display = 'none';
    if (detail) detail.style.display = 'block';

    const av = document.getElementById('afAqOwnerAvatar');
    if (av) av.src = res.avatar || 'https://cdn.discordapp.com/embed/avatars/0.png';

    const nameEl = document.getElementById('afAqOwnerName');
    if (nameEl) nameEl.innerText = res.username || `User ${res.user_id}`;

    const idEl = document.getElementById('afAqOwnerId');
    if (idEl) idEl.innerText = res.user_id;

    const likesCount = udata.aquarium_likes !== undefined ? (Array.isArray(udata.aquarium_likes) ? udata.aquarium_likes.length : Number(udata.aquarium_likes)) : (res.aquarium_likes || 0);
    const likesBadge = document.getElementById('afAqLikesBadge');
    if (likesBadge) likesBadge.innerText = `❤️ ${likesCount} Lượt Thích`;

    const tank = udata.aquarium || res.aquarium || [];
    const maxSlots = udata.aquarium_slots || res.aquarium_slots || 6;
    const capText = document.getElementById('afAqCapacityText');
    if (capText) capText.innerText = `${tank.length} / ${maxSlots} ô`;

    const favIdx = udata.aquarium_favorite !== undefined ? udata.aquarium_favorite : res.aquarium_favorite;
    const mascotBadge = document.getElementById('afAqMascotBadge');
    let mascotName = null;
    if (favIdx !== null && favIdx !== undefined && favIdx >= 0 && favIdx < tank.length) {
        mascotName = tank[favIdx].name;
    }
    if (mascotBadge) {
        mascotBadge.innerText = mascotName ? `⭐ Linh vật: ${mascotName}` : '⭐ Linh vật: Chưa đặt';
        mascotBadge.style.color = mascotName ? '#fde047' : '#94a3b8';
    }

    
    const grid = document.getElementById('afAqFishGrid');
    if (!grid) return;

    if (tank.length === 0) {
        grid.innerHTML = `
            <div style="grid-column: 1 / -1; padding: 40px 20px; text-align: center; color: #bae6fd;">
                <div style="font-size: 2.5rem; margin-bottom: 8px;">🌊🫧</div>
                <div style="font-size: 1.05rem; font-weight: 600;">Bể Thủy Cung đang trống</div>
                <div style="font-size: 0.85rem; color: #7dd3fc; margin-top: 4px;">Cần thủ chưa thả chú cá nào vào bể. Nhấn nút <strong>Thêm Cá Vào Bể</strong> phía trên để thả cá vào!</div>
            </div>
        `;
        return;
    }

    grid.innerHTML = tank.map((f, idx) => {
        const isFav = idx === favIdx;
        const r = RARITY_BADGES[f.rarity] || RARITY_BADGES.common;
        return `
            <div class="glass-card" style="background: rgba(15, 23, 42, 0.65); border: 1px solid ${isFav ? '#facc15' : 'rgba(56, 189, 248, 0.3)'}; border-radius: 12px; padding: 14px; display: flex; flex-direction: column; gap: 8px; position: relative; box-shadow: ${isFav ? '0 0 16px rgba(250, 204, 21, 0.35)' : 'none'};">
                ${isFav ? `<span style="position: absolute; top: -8px; right: 10px; background: linear-gradient(135deg, #f59e0b, #d97706); color: #fff; font-size: 0.68rem; font-weight: 800; padding: 2px 8px; border-radius: 12px; box-shadow: 0 2px 8px rgba(0,0,0,0.4);">⭐ LINH VẬT</span>` : ''}
                <div style="display: flex; align-items: center; gap: 10px;">
                    <span style="font-size: 2rem;">🐟</span>
                    <div style="flex: 1; min-width: 0;">
                        <strong style="color: ${isFav ? '#fde047' : '#e0f2fe'}; font-size: 1rem; display: block; overflow: hidden; text-overflow: ellipsis; white-space: nowrap;">${escapeHtml(f.name || 'Cá')}</strong>
                        <span class="badge" style="background:${r.bg}; color:${r.color}; font-size: 0.68rem; padding: 2px 6px;">${r.label}</span>
                    </div>
                </div>
                <div style="font-size: 0.8rem; color: #bae6fd; display: flex; flex-direction: column; gap: 2px; background: rgba(0,0,0,0.25); padding: 8px; border-radius: 6px;">
                    <div>📏 Kích thước: <strong>${f.length || '—'} cm</strong> (${f.size_name || 'Tiêu Chuẩn'})</div>
                    <div>⚖️ Cân nặng: <strong>${f.weight || '—'} kg</strong></div>
                    ${f.mutation ? `<div style="color: #ec4899;">🧬 Đột biến: <strong>${escapeHtml(f.mutation)}</strong></div>` : ''}
                    <div>💰 Giá trị ước tính: <strong style="color: #ffd700;">${Number(f.price || 0).toLocaleString()} Coins</strong></div>
                </div>
                <div style="display: flex; gap: 6px; flex-wrap: wrap; margin-top: auto; padding-top: 6px;">
                    <button class="btn btn-secondary btn-sm" onclick="afAquariumMoveToBag(${idx})" style="flex: 1; font-size: 0.75rem; padding: 4px 6px;">📥 Về Giỏ</button>
                    <button class="btn btn-secondary btn-sm" onclick="afAquariumSetMascot(${idx})" style="font-size: 0.75rem; padding: 4px 6px; ${isFav ? 'background: #ca8a04; color: #fff;' : ''}">${isFav ? '⭐ Đã chọn' : '⭐ Linh Vật'}</button>
                    <button class="btn btn-danger btn-sm" onclick="afAquariumRemoveFish(${idx})" style="font-size: 0.75rem; padding: 4px 6px;">🗑️ Xóa</button>
                </div>
            </div>
        `;
    }).join('');
}

async function afAquariumAction(action, payload = {}) {
    if (!state.adminFishing.currentAquariumUser) {
        showToast('Vui lòng chọn Thủy Cung cần thủ trước!', 'warning');
        return;
    }
    const uid = state.adminFishing.currentAquariumUser.user_id;
    const res = await apiRequest('/api/fishing/admin/user/action', 'POST', {
        user_id: uid,
        action,
        ...payload
    });
    if (res.ok) {
        showToast(res.message || '✅ Thao tác thành công!', 'success');
        await afSearchAquarium();
        loadAdminAquariumList();
    } else {
        showToast(res.error || '❌ Thao tác thất bại', 'error');
    }
}

async function afAquariumMoveToBag(idx) {
    afAquariumAction('remove_aquarium_fish', { index: idx, to_bag: true });
}

async function afAquariumRemoveFish(idx) {
    if (!confirm('Bạn có chắc muốn xóa vĩnh viễn chú cá này khỏi Thủy Cung?')) return;
    afAquariumAction('remove_aquarium_fish', { index: idx, to_bag: false });
}

async function afAquariumSetMascot(idx) {
    afAquariumAction('set_aquarium_favorite', { index: idx });
}

async function afPromptSetAquariumSlotsView() {
    const curr = state.adminFishing.currentAquariumUser?.data?.aquarium_slots || 6;
    const val = prompt('Nhập số ô chứa tối đa mới của Thủy Cung (1 - 100 ô):', curr);
    if (val === null) return;
    const slots = parseInt(val, 10);
    if (isNaN(slots) || slots < 1 || slots > 100) {
        showToast('Số ô phải từ 1 đến 100!', 'warning');
        return;
    }
    afAquariumAction('set_aquarium_slots', { slots });
}

async function afPromptSetAquariumLikesView() {
    const curr = state.adminFishing.currentAquariumUser?.data?.aquarium_likes || 0;
    const currentCount = Array.isArray(curr) ? curr.length : Number(curr || 0);
    const val = prompt('Nhập số lượt thích mới cho Thủy Cung:', currentCount);
    if (val === null) return;
    const likes = parseInt(val, 10);
    if (isNaN(likes) || likes < 0) {
        showToast('Lượt thích không hợp lệ!', 'warning');
        return;
    }
    afAquariumAction('set_aquarium_likes', { likes });
}

async function afClearAquariumView() {
    if (!confirm('Bạn có chắc muốn xóa sạch toàn bộ cá trong Thủy Cung này không?')) return;
    afAquariumAction('clear_aquarium');
}

async function afAddFishToAquariumModal() {
    if (!state.adminFishing.currentAquariumUser) {
        showToast('Vui lòng chọn Thủy Cung trước!', 'warning');
        return;
    }
    const name = prompt('Nhập tên loài cá muốn thả vào Thủy Cung:', '🐟 Cá Koi Nhật Bản');
    if (!name) return;
    const rarity = prompt('Nhập độ hiếm (common, rare, epic, legendary, admin):', 'legendary') || 'rare';
    const weight = parseFloat(prompt('Nhập cân nặng (kg):', '3.5')) || 2.0;
    const length = parseFloat(prompt('Nhập chiều dài (cm):', '45.0')) || 30.0;
    const price = parseInt(prompt('Nhập giá trị quy đổi Coins:', '5000'), 10) || 1000;

    afAquariumAction('add_aquarium_fish', {
        fish_name: name.trim(),
        rarity: rarity.trim().toLowerCase(),
        weight: weight,
        length: length,
        price: price
    });
}





function toggleUserViewPreview() {
    if (!state.isRealAdmin) return;
    state.previewAsUser = !state.previewAsUser;
    localStorage.setItem('sakura_preview_as_user', state.previewAsUser ? 'true' : 'false');
    applyRoleUI();
    if (state.previewAsUser) {
        showToast('👁️ Đã chuyển sang Góc Nhìn Người Dùng Thường (User View Preview)!', 'info');
    } else {
        showToast('👑 Đã quay lại Góc Nhìn Quản Trị Viên (Admin View)!', 'success');
    }
}




async function loadAdminUsersList() {
    const tbody = document.getElementById('adminUsersTableBody');
    if (!tbody) return;
    tbody.innerHTML = '<tr><td colspan="5" style="text-align:center; padding:30px; color:var(--text-dim);">⏳ Đang tải danh sách người dùng & Admin web...</td></tr>';

    const res = await apiRequest('/api/admin/users');
    if (!res.ok) {
        tbody.innerHTML = `<tr><td colspan="5" style="text-align:center; padding:30px; color:#ef4444;">❌ ${escapeHtml(res.error || 'Không có quyền truy cập')}</td></tr>`;
        return;
    }

    state.adminUsersList = res.users || [];
    renderAdminUsersTable();
}

function filterAdminUsersTable(filter) {
    state.adminUsersFilter = filter;
    ['All', 'Admin', 'Normal'].forEach(f => {
        const btn = document.getElementById(`btnFilterUsers${f}`);
        if (btn) btn.classList.toggle('active', f.toLowerCase() === filter.toLowerCase() || (f === 'Normal' && filter === 'user'));
    });
    renderAdminUsersTable();
}

function renderAdminUsersTable() {
    const tbody = document.getElementById('adminUsersTableBody');
    const badge = document.getElementById('adminUsersCountBadge');
    if (!tbody) return;

    let users = state.adminUsersList || [];
    const filter = state.adminUsersFilter || 'all';

    if (filter === 'admin') {
        users = users.filter(u => u.role === 'admin' || u.is_owner);
    } else if (filter === 'user') {
        users = users.filter(u => u.role !== 'admin' && !u.is_owner);
    }

    if (badge) badge.textContent = `${users.length} Thành Viên`;

    if (users.length === 0) {
        tbody.innerHTML = '<tr><td colspan="5" style="text-align:center; padding:30px; color:var(--text-dim);">Không có người dùng nào phù hợp với bộ lọc.</td></tr>';
        return;
    }

    let html = '';
    users.forEach(u => {
        const isOwner = !!u.is_owner;
        const isAdmin = u.role === 'admin';
        const av = u.avatar || 'https://cdn.discordapp.com/embed/avatars/0.png';
        const tag = u.discord_tag || u.username;
        const did = u.discord_id || '—';

        let roleBadgeHtml = '';
        if (isOwner) {
            roleBadgeHtml = '<span class="badge" style="background: linear-gradient(135deg, #f59e0b, #d97706); color:#fff; font-weight:700;">👑 CHỦ SỞ HỮU WEB</span>';
        } else if (isAdmin) {
            roleBadgeHtml = '<span class="badge" style="background: rgba(16, 185, 129, 0.2); color:#10b981; border:1px solid rgba(16, 185, 129, 0.4); font-weight:700;">⭐ ADMIN WEB</span>';
        } else {
            roleBadgeHtml = '<span class="badge" style="background: rgba(148, 163, 184, 0.15); color:#94a3b8; border:1px solid rgba(148, 163, 184, 0.3);">👤 NGƯỜI DÙNG</span>';
        }

        let actionBtnHtml = '';
        if (isOwner) {
            actionBtnHtml = '<span style="font-size:0.8rem; color:var(--text-dim); font-style:italic;">Chủ sở hữu tối cao</span>';
        } else if (isAdmin) {
            actionBtnHtml = `<button class="btn btn-danger btn-xs" onclick="submitRemoveAdminWeb('${escapeHtml(u.username)}')" style="white-space:nowrap;">🔻 Thu Hồi Admin</button>`;
        } else {
            actionBtnHtml = `<button class="btn btn-primary btn-xs" onclick="setWebUserRole('${escapeHtml(u.username)}', 'admin')" style="background:linear-gradient(135deg, #10b981, #059669); border:none; white-space:nowrap;">⭐ Cấp Quyền Admin</button>`;
        }

        html += `
            <tr style="border-bottom: 1px solid rgba(255,255,255,0.05);">
                <td style="padding: 10px;">
                    <div style="display:flex; align-items:center; gap:10px;">
                        <img src="${escapeHtml(av)}" style="width:34px; height:34px; border-radius:50%; object-fit:cover; border:1.5px solid var(--border-glass);" onerror="this.src='https://cdn.discordapp.com/embed/avatars/0.png'">
                        <div style="font-weight:600; font-size:0.9rem; color:var(--text-main);">${escapeHtml(u.username)}</div>
                    </div>
                </td>
                <td style="padding: 10px; font-size:0.86rem; color:var(--text-color);">${escapeHtml(tag)}</td>
                <td style="padding: 10px; font-family:monospace; font-size:0.82rem; color:#38bdf8;">${escapeHtml(did)}</td>
                <td style="padding: 10px; text-align:center;">${roleBadgeHtml}</td>
                <td style="padding: 10px; text-align:right;">${actionBtnHtml}</td>
            </tr>
        `;
    });

    tbody.innerHTML = html;
}

async function setWebUserRole(username, role) {
    if (!username) return;
    const actionLabel = role === 'admin' ? 'thăng cấp Quản Trị Viên (Admin)' : 'hạ cấp Người Dùng Thường';
    if (!confirm(`Xác nhận ${actionLabel} cho tài khoản "${username}"?`)) return;

    const res = await apiRequest('/api/admin/users/role', 'POST', { username, role });
    if (res.ok) {
        showToast(res.message || 'Cập nhật quyền thành công!', 'success');
        loadAdminUsersList();
    } else {
        showToast(`❌ Thất bại: ${res.error || 'Lỗi cập nhật quyền'}`, 'error');
    }
}

async function submitAddAdminWeb() {
    const input = document.getElementById('targetAdminInput');
    const target = input ? input.value.trim() : '';
    if (!target) {
        showToast('Vui lòng nhập Username hoặc Discord User ID!', 'warning');
        return;
    }

    const res = await apiRequest('/api/admin/users/add-admin', 'POST', { target });
    if (res.ok) {
        showToast(res.message || 'Đã thêm Admin web thành công!', 'success');
        if (input) input.value = '';
        loadAdminUsersList();
    } else {
        showToast(`❌ Thất bại: ${res.error || 'Lỗi thêm Admin'}`, 'error');
    }
}

async function submitRemoveAdminWeb(target) {
    if (!target) return;
    if (!confirm(`Bạn có chắc chắn muốn thu hồi quyền Admin của "${target}" không?`)) return;

    const res = await apiRequest('/api/admin/users/remove-admin', 'POST', { target });
    if (res.ok) {
        showToast(res.message || 'Đã thu hồi quyền Admin!', 'success');
        loadAdminUsersList();
    } else {
        showToast(`❌ Thất bại: ${res.error || 'Lỗi thu hồi Admin'}`, 'error');
    }
}






function afEditUserRod(rodId) {
    if (!state.adminFishing.currentUser) return showToast('Chưa chọn cần thủ', 'warning');
    const rods = state.adminFishing.currentUser.rods || {};
    const rod = rods[rodId];
    if (!rod) return showToast('Không tìm thấy thông tin cần này', 'warning');

    const modal = document.getElementById('afEditRodModal');
    if (!modal) return;

    document.getElementById('afEditRodId').value = rodId;
    document.getElementById('afEditRodName').value = rod.name || rodId;
    document.getElementById('afEditRodRefine').value = rod.refine !== undefined ? rod.refine : 0;
    document.getElementById('afEditRodStars').value = rod.stars !== undefined ? rod.stars : 0;
    document.getElementById('afEditRodDurability').value = rod.durability !== undefined ? rod.durability : 100;
    document.getElementById('afEditRodMaxDurability').value = rod.max_durability !== undefined ? rod.max_durability : 100;
    document.getElementById('afEditRodLuck').value = rod.luck !== undefined ? rod.luck : 5;
    document.getElementById('afEditRodEquipped').checked = (state.adminFishing.currentUser.equipped_rod === rodId);

    modal.classList.add('active');
    modal.style.display = 'flex';
}

function afCloseEditRodModal() {
    const modal = document.getElementById('afEditRodModal');
    if (modal) {
        modal.classList.remove('active');
        modal.style.display = 'none';
    }
}

async function afSubmitEditRod() {
    if (!state.adminFishing.currentUser) return showToast('Chưa chọn cần thủ', 'warning');
    const rod_id = document.getElementById('afEditRodId').value;
    if (!rod_id) return showToast('Thiếu ID cần', 'warning');

    const name = document.getElementById('afEditRodName').value.trim();
    const refine = parseInt(document.getElementById('afEditRodRefine').value || '0');
    const stars = parseInt(document.getElementById('afEditRodStars').value || '0');
    const durability = parseInt(document.getElementById('afEditRodDurability').value || '100');
    const max_durability = parseInt(document.getElementById('afEditRodMaxDurability').value || '100');
    const luck = parseInt(document.getElementById('afEditRodLuck').value || '0');
    const is_equipped = document.getElementById('afEditRodEquipped').checked;

    const res = await apiRequest('/api/fishing/admin/user/action', 'POST', {
        action: 'update_rod',
        user_id: state.adminFishing.currentUser.user_id,
        rod_id,
        name,
        refine,
        stars,
        durability,
        max_durability,
        luck,
        is_equipped
    });

    if (res.ok) {
        showToast(res.message || 'Cập nhật cần câu thành công!', 'success');
        afCloseEditRodModal();
        loadAdminFishUser();
    }
}


state.adminFishing.achievements = [];

async function afLoadAchievementsCatalog() {
    const res = await apiRequest('/api/achievements/admin/list', 'GET');
    if (!res.ok) return showToast(res.error || 'Lỗi tải danh mục thành tựu', 'error');
    state.adminFishing.achievements = res.achievements || [];
    const countEl = document.getElementById('afAchTotalCount');
    if (countEl) countEl.textContent = state.adminFishing.achievements.length;

    
    const targetSel = document.getElementById('afAchSelectTarget');
    if (targetSel) {
        targetSel.innerHTML = state.adminFishing.achievements.map(a => {
            return `<option value="${a.id}">${a.icon || '🏆'} ${escapeHtml(a.name)} [${a.id}]</option>`;
        }).join('');
    }

    afFilterAchievementsList();
}

function afFilterAchievementsList() {
    const query = (document.getElementById('afAchSearch')?.value || '').toLowerCase().trim();
    const cat = document.getElementById('afAchFilterCat')?.value || 'all';
    const tbody = document.getElementById('afAchievementsTableBody');
    if (!tbody) return;

    const list = (state.adminFishing.achievements || []).filter(a => {
        if (cat !== 'all' && a.category !== cat) return false;
        if (query) {
            const str = (a.name + ' ' + a.id + ' ' + (a.desc || '')).toLowerCase();
            if (!str.includes(query)) return false;
        }
        return true;
    });

    if (list.length === 0) {
        tbody.innerHTML = '<tr><td colspan="7" style="text-align:center; padding:24px; color:var(--text-dim);">Không có thành tựu nào khớp bộ lọc.</td></tr>';
        return;
    }

    const catLabels = {
        fishing: '🎣 Câu Cá',
        mining: '⛏️ Đào Khoáng',
        farming: '🌾 Nông Trại',
        casino_gacha: '🎲 Casino',
        words_trivia: '🧵 Nối Từ',
        social_level: '💖 Xã Hội'
    };

    tbody.innerHTML = list.map(a => {
        const rewards = [];
        if (a.reward_coins) rewards.push(`🪙 <strong>${a.reward_coins.toLocaleString()}</strong>c`);
        if (a.reward_xu) rewards.push(`💎 <strong>${a.reward_xu}</strong>x`);
        if (a.reward_title) rewards.push(`🏷️ [${escapeHtml(a.reward_title)}]`);
        const rewStr = rewards.length ? rewards.join(' • ') : 'Danh dự';

        return `
            <tr>
                <td style="font-size:1.3rem; text-align:center;">${a.icon || '🏆'}</td>
                <td><strong>${escapeHtml(a.name)}</strong></td>
                <td><code style="font-size:0.75rem; background:rgba(0,0,0,0.3); padding:2px 6px; border-radius:4px;">${escapeHtml(a.id)}</code></td>
                <td><span class="badge" style="font-size:0.72rem; background:rgba(255,255,255,0.06);">${catLabels[a.category] || a.category}</span></td>
                <td style="font-size:0.82rem; color:var(--text-dim); max-width:280px;">${escapeHtml(a.desc || '—')}</td>
                <td style="font-size:0.82rem;">${rewStr}</td>
                <td><span class="badge ${a.id.startsWith('custom_') ? 'badge-sakura' : ''}" style="font-size:0.68rem;">${a.id.startsWith('custom_') ? 'TÙY CHỈNH' : 'GỐC'}</span></td>
            </tr>
        `;
    }).join('');
}

async function afSubmitAddAchievement() {
    const id = document.getElementById('afAchId')?.value.trim();
    const name = document.getElementById('afAchName')?.value.trim();
    const icon = document.getElementById('afAchIcon')?.value.trim() || '🏆';
    const category = document.getElementById('afAchCategory')?.value || 'fishing';
    const desc = document.getElementById('afAchDesc')?.value.trim() || '';
    const reward_coins = parseInt(document.getElementById('afAchCoins')?.value || '0');
    const reward_xu = parseInt(document.getElementById('afAchXu')?.value || '0');
    const reward_title = document.getElementById('afAchTitle')?.value.trim() || '';

    if (!id || !name) return showToast('Vui lòng nhập Mã ID và Tên thành tựu', 'warning');

    const res = await apiRequest('/api/achievements/admin/add', 'POST', {
        id,
        name,
        icon,
        category,
        desc,
        reward_coins,
        reward_xu,
        reward_title
    });

    if (res.ok) {
        showToast(res.message || 'Tạo thành tựu thành công!', 'success');
        document.getElementById('afAchId').value = '';
        document.getElementById('afAchName').value = '';
        document.getElementById('afAchDesc').value = '';
        document.getElementById('afAchTitle').value = '';
        afLoadAchievementsCatalog();
        switchAchSubTab('list');
    }
}

function switchAchSubTab(subTab) {
    const isList = subTab === 'list';
    const btnList = document.getElementById('btnAchSubList');
    const btnCreate = document.getElementById('btnAchSubCreate');
    const viewList = document.getElementById('achSubViewList');
    const viewCreate = document.getElementById('achSubViewCreate');

    if (btnList) btnList.classList.toggle('active', isList);
    if (btnCreate) btnCreate.classList.toggle('active', !isList);
    if (viewList) viewList.style.display = isList ? 'block' : 'none';
    if (viewCreate) viewCreate.style.display = isList ? 'none' : 'block';

    if (isList) {
        afLoadAchievementsCatalog();
    }
}

async function afSubmitUserAchievementAction(action) {
    const user_id = document.getElementById('afAchUserTargetId')?.value.trim();
    const ach_id = document.getElementById('afAchSelectTarget')?.value;
    if (!user_id) return showToast('Vui lòng nhập Discord User ID', 'warning');
    if (!ach_id) return showToast('Vui lòng chọn thành tựu', 'warning');

    const res = await apiRequest('/api/achievements/admin/user/action', 'POST', {
        action,
        user_id,
        ach_id
    });

    if (res.ok) {
        showToast(res.message || 'Thực hiện thành công!', 'success');
    }
}





state.adminFishing.shopItems = [];

function switchShopSubTab(subTab) {
    const isList = subTab === 'list';
    const btnList = document.getElementById('btnShopSubList');
    const btnCreate = document.getElementById('btnShopSubCreate');
    const viewList = document.getElementById('shopSubViewList');
    const viewCreate = document.getElementById('shopSubViewCreate');

    if (btnList) btnList.classList.toggle('active', isList);
    if (btnCreate) btnCreate.classList.toggle('active', !isList);
    if (viewList) viewList.style.display = isList ? 'block' : 'none';
    if (viewCreate) viewCreate.style.display = isList ? 'none' : 'block';

    if (isList) {
        loadAdminShopItems();
    }
}

async function loadAdminShopItems() {
    const res = await apiRequest('/api/shop/admin/items', 'GET');
    if (!res.ok) return showToast(res.error || 'Lỗi tải danh sách cửa hàng', 'error');

    state.adminFishing.shopItems = res.items || [];

    const totalEl = document.getElementById('afShopTotalCount');
    const visEl = document.getElementById('afShopVisibleCount');
    const hidEl = document.getElementById('afShopHiddenCount');

    const total = state.adminFishing.shopItems.length;
    const hidden = state.adminFishing.shopItems.filter(i => i.is_hidden).length;
    const visible = total - hidden;

    if (totalEl) totalEl.textContent = total;
    if (visEl) visEl.textContent = visible;
    if (hidEl) hidEl.textContent = hidden;

    renderAdminShopTable();
}

function renderAdminShopTable() {
    const tbody = document.getElementById('afShopTableBody');
    if (!tbody) return;

    const search = (document.getElementById('afShopSearchInput')?.value || '').toLowerCase().trim();
    const catFilter = document.getElementById('afShopCategoryFilter')?.value || '';

    let items = state.adminFishing.shopItems || [];

    if (search) {
        items = items.filter(i =>
            (i.name && i.name.toLowerCase().includes(search)) ||
            (i.id && i.id.toLowerCase().includes(search)) ||
            (i.desc && i.desc.toLowerCase().includes(search))
        );
    }

    if (catFilter) {
        items = items.filter(i => i.category === catFilter);
    }

    if (items.length === 0) {
        tbody.innerHTML = `<tr><td colspan="7" style="text-align:center; padding: 28px; color: var(--text-dim);">Không tìm thấy vật phẩm nào trong cửa hàng.</td></tr>`;
        return;
    }

    const catLabels = {
        'rod': '🎣 Cần Câu',
        'bait': '🪱 Mồi Câu',
        'pet': '🐾 Thú Cưng',
        'bag': '🎒 Túi Đồ',
        'utility': '🧰 Tiện Ích',
        'troll': '🎭 Trò Đùa',
        'custom': '✨ Tùy Chỉnh'
    };

    tbody.innerHTML = items.map(item => {
        const catBadge = catLabels[item.category] || item.category || 'Vật Phẩm';
        const isHidden = Boolean(item.is_hidden);
        const currIcon = item.currency === 'xu' ? '💎 Xu' : '🪙 Coins';
        const priceDisplay = `<strong style="color: ${item.currency === 'xu' ? '#00e5ff' : 'var(--accent-gold)'}; font-size: 0.95rem;">${Number(item.price || 0).toLocaleString()}</strong> <span style="font-size: 0.78rem; color: var(--text-dim);">${currIcon}</span>`;

        let statsDesc = '';
        if (item.category === 'rod') {
            statsDesc = `<div style="font-size: 0.78rem; color: #50fa7b; margin-bottom: 2px;">May mắn: <strong>+${item.luck || 0}%</strong> | Độ bền: <strong>${item.durability || 0}</strong></div>`;
        }
        if (item.desc) {
            statsDesc += `<div style="font-size: 0.78rem; color: var(--text-dim); line-height: 1.3;">${escapeHtml(item.desc)}</div>`;
        }
        if (!statsDesc) statsDesc = `<span style="color: var(--text-dim); font-size: 0.78rem;">—</span>`;

        const statusBadge = isHidden
            ? `<span class="badge" style="background: rgba(255, 85, 85, 0.15); color: #ff5555; border: 1px solid rgba(255,85,85,0.3); font-size: 0.75rem;">🔴 Đang Ẩn</span>`
            : `<span class="badge" style="background: rgba(80, 250, 123, 0.15); color: #50fa7b; border: 1px solid rgba(80,250,123,0.3); font-size: 0.75rem;">🟢 Hiển Thị</span>`;

        const toggleBtn = isHidden
            ? `<button class="btn btn-sm btn-success" title="Hiển thị lại trong shop" onclick="afToggleShopItemHide('${escapeHtml(item.id)}', false)">👁️ Hiện</button>`
            : `<button class="btn btn-sm btn-danger" title="Ẩn khỏi shop người chơi" onclick="afToggleShopItemHide('${escapeHtml(item.id)}', true)">🙈 Ẩn</button>`;

        return `
            <tr>
                <td>
                    <div style="display: flex; align-items: center; gap: 8px;">
                        <span style="font-size: 1.3rem;">${item.icon || '📦'}</span>
                        <strong>${escapeHtml(item.name || item.id)}</strong>
                    </div>
                </td>
                <td><code style="color: var(--accent-cyan); font-size: 0.8rem;">${escapeHtml(item.id)}</code></td>
                <td><span class="badge badge-secondary" style="font-size: 0.75rem;">${catBadge}</span></td>
                <td>${priceDisplay}</td>
                <td style="max-width: 260px;">${statsDesc}</td>
                <td>${statusBadge}</td>
                <td style="text-align: right;">
                    <div style="display: flex; gap: 6px; justify-content: flex-end;">
                        <button class="btn btn-secondary btn-sm" onclick="afEditShopItem('${escapeHtml(item.id)}')">✏️ Sửa</button>
                        ${toggleBtn}
                    </div>
                </td>
            </tr>
        `;
    }).join('');
}

async function afToggleShopItemHide(itemId, isHidden) {
    const res = await apiRequest('/api/shop/admin/toggle-hide', 'POST', {
        item_id: itemId,
        is_hidden: isHidden
    });
    if (res.ok) {
        showToast(res.message || 'Cập nhật trạng thái thành công!', 'success');
        loadAdminShopItems();
    } else {
        showToast(res.error || 'Lỗi khi thay đổi trạng thái', 'error');
    }
}

function afEditShopItem(itemId) {
    const item = (state.adminFishing.shopItems || []).find(i => i.id === itemId);
    if (!item) return showToast('Không tìm thấy vật phẩm', 'warning');

    document.getElementById('afEditShopItemId').value = item.id || '';
    document.getElementById('afEditShopItemName').value = item.name || '';
    document.getElementById('afEditShopItemPrice').value = item.price || 0;
    document.getElementById('afEditShopItemCurrency').value = item.currency || 'coins';
    document.getElementById('afEditShopItemLuck').value = item.luck || 0;
    document.getElementById('afEditShopItemDurability').value = item.durability || 0;
    document.getElementById('afEditShopItemDesc').value = item.desc || '';
    document.getElementById('afEditShopItemHidden').checked = Boolean(item.is_hidden);

    const gearRow = document.getElementById('afEditShopGearRow');
    if (gearRow) {
        gearRow.style.display = (item.category === 'rod' || item.luck !== undefined || item.durability !== undefined) ? 'grid' : 'none';
    }

    const modal = document.getElementById('afEditShopItemModal');
    if (modal) {
        modal.classList.add('active');
        modal.style.display = 'flex';
    }
}

function afCloseEditShopItemModal() {
    const modal = document.getElementById('afEditShopItemModal');
    if (modal) {
        modal.classList.remove('active');
        modal.style.display = 'none';
    }
}

async function afSubmitEditShopItem() {
    const itemId = document.getElementById('afEditShopItemId')?.value;
    if (!itemId) return;

    const name = document.getElementById('afEditShopItemName')?.value.trim();
    const price = parseInt(document.getElementById('afEditShopItemPrice')?.value || '0');
    const currency = document.getElementById('afEditShopItemCurrency')?.value || 'coins';
    const luck = parseInt(document.getElementById('afEditShopItemLuck')?.value || '0');
    const durability = parseInt(document.getElementById('afEditShopItemDurability')?.value || '0');
    const desc = document.getElementById('afEditShopItemDesc')?.value.trim();
    const isHidden = document.getElementById('afEditShopItemHidden')?.checked || false;

    const res = await apiRequest('/api/shop/admin/update', 'POST', {
        item_id: itemId,
        name,
        price,
        currency,
        luck,
        durability,
        desc,
        is_hidden: isHidden
    });

    if (res.ok) {
        showToast(res.message || 'Cập nhật vật phẩm cửa hàng thành công!', 'success');
        afCloseEditShopItemModal();
        loadAdminShopItems();
    } else {
        showToast(res.error || 'Lỗi khi cập nhật vật phẩm', 'error');
    }
}





state.adminFishing.marriages = [];

async function loadAdminMarriages() {
    const res = await apiRequest('/api/marriage/admin/list', 'GET');
    if (!res.ok) return showToast(res.error || 'Lỗi tải danh sách hôn lễ', 'error');

    state.adminFishing.marriages = res.couples || [];

    const totalEl = document.getElementById('afMarriageTotalCount');
    const countCard = document.getElementById('afMarriageCountCard');
    const fundCard = document.getElementById('afMarriageFundCard');
    const topCard = document.getElementById('afMarriageTopCouple');

    const total = state.adminFishing.marriages.length;
    let totalFund = 0;
    let topCouple = null;

    state.adminFishing.marriages.forEach(c => {
        totalFund += (c.common_fund || 0);
        if (!topCouple || (c.affection || 0) > (topCouple.affection || 0)) {
            topCouple = c;
        }
    });

    if (totalEl) totalEl.textContent = total;
    if (countCard) countCard.textContent = `${total} cặp đôi`;
    if (fundCard) fundCard.textContent = `${totalFund.toLocaleString()} coins`;
    if (topCard) {
        if (topCouple) {
            topCard.innerHTML = `<span style="font-size: 0.9rem;">${escapeHtml(topCouple.user_a_name || topCouple.user_a)} & ${escapeHtml(topCouple.user_b_name || topCouple.user_b)}</span> <span style="font-size: 0.75rem; color: #ff79c6;">(${topCouple.affection || 0} ❤️)</span>`;
        } else {
            topCard.textContent = '—';
        }
    }

    renderAdminMarriageTable();
}

function renderAdminMarriageTable() {
    const tbody = document.getElementById('afMarriageTableBody');
    if (!tbody) return;

    const search = (document.getElementById('afMarriageSearchInput')?.value || '').toLowerCase().trim();
    let couples = state.adminFishing.marriages || [];

    if (search) {
        couples = couples.filter(c =>
            (c.user_a && c.user_a.includes(search)) ||
            (c.user_b && c.user_b.includes(search)) ||
            (c.user_a_name && c.user_a_name.toLowerCase().includes(search)) ||
            (c.user_b_name && c.user_b_name.toLowerCase().includes(search)) ||
            (c.ring && c.ring.toLowerCase().includes(search))
        );
    }

    if (couples.length === 0) {
        tbody.innerHTML = `<tr><td colspan="7" style="text-align:center; padding: 28px; color: var(--text-dim);">Chưa có cặp đôi nào kết hôn hoặc không tìm thấy kết quả.</td></tr>`;
        return;
    }

    tbody.innerHTML = couples.map(c => {
        const userADisplay = c.user_a_name ? `${escapeHtml(c.user_a_name)} (<code style="font-size:0.75rem;">${c.user_a}</code>)` : `<code style="font-size:0.78rem;">${c.user_a}</code>`;
        const userBDisplay = c.user_b_name ? `${escapeHtml(c.user_b_name)} (<code style="font-size:0.75rem;">${c.user_b}</code>)` : `<code style="font-size:0.78rem;">${c.user_b}</code>`;

        const ringDisplay = `<span style="font-size: 1.1rem;">💍</span> <strong>${escapeHtml(c.ring || 'Nhẫn Cỏ')}</strong>`;
        const dateDisplay = `
            <div>${escapeHtml(c.wedding_date || 'Chưa rõ')}</div>
            <div style="font-size: 0.75rem; color: #50fa7b; margin-top: 2px;">⏳ ${c.days_together || 0} ngày bên nhau</div>
        `;
        const affectionDisplay = `<strong style="color: #ff79c6; font-size: 0.95rem;">${(c.affection || 0).toLocaleString()}</strong> <span style="font-size: 0.8rem;">❤️</span>`;
        const fundDisplay = `<strong style="color: var(--accent-gold); font-size: 0.95rem;">${Number(c.common_fund || 0).toLocaleString()}</strong> <span style="font-size: 0.75rem; color: var(--text-dim);">coins</span>`;

        return `
            <tr>
                <td>
                    <div style="display: flex; flex-direction: column; gap: 4px;">
                        <div style="display: flex; align-items: center; gap: 6px;">
                            <span style="color: var(--sakura-pink);">👤</span>
                            <span>${userADisplay}</span>
                        </div>
                        <div style="display: flex; align-items: center; gap: 6px;">
                            <span style="color: #bd93f9;">👥</span>
                            <span>${userBDisplay}</span>
                        </div>
                    </div>
                </td>
                <td>${ringDisplay}</td>
                <td>${dateDisplay}</td>
                <td>${affectionDisplay}</td>
                <td>${fundDisplay}</td>
                <td><span class="badge" style="background: rgba(255, 121, 198, 0.15); color: #ff79c6; border: 1px solid rgba(255,121,198,0.3); font-size: 0.75rem;">💑 Hôn Nhân Hạnh Phúc</span></td>
                <td style="text-align: right;">
                    <div style="display: flex; gap: 6px; justify-content: flex-end;">
                        <button class="btn btn-secondary btn-sm" onclick="afEditMarriage('${escapeHtml(c.couple_key)}')">✏️ Sửa</button>
                        <button class="btn btn-danger btn-sm" onclick="afDivorceMarriage('${escapeHtml(c.couple_key)}')">💔 Ly Hôn</button>
                    </div>
                </td>
            </tr>
        `;
    }).join('');
}

function afEditMarriage(coupleKey) {
    const couple = (state.adminFishing.marriages || []).find(c => c.couple_key === coupleKey);
    if (!couple) return showToast('Không tìm thấy thông tin cặp đôi', 'warning');

    document.getElementById('afEditMarriageKey').value = couple.couple_key || '';
    const labelEl = document.getElementById('afEditMarriageCoupleLabel');
    if (labelEl) {
        labelEl.value = `${couple.user_a_name || couple.user_a} 💕 ${couple.user_b_name || couple.user_b}`;
    }
    const ringEl = document.getElementById('afEditMarriageRing');
    if (ringEl) ringEl.value = couple.ring || 'Nhẫn Cỏ';
    const affEl = document.getElementById('afEditMarriageAffection');
    if (affEl) affEl.value = couple.affection || 0;
    const coinsEl = document.getElementById('afEditMarriageCommonCoins');
    if (coinsEl) coinsEl.value = couple.common_fund || 0;
    const dateEl = document.getElementById('afEditMarriageDate');
    if (dateEl) dateEl.value = couple.wedding_date || '';

    const modal = document.getElementById('afEditMarriageModal');
    if (modal) {
        modal.classList.add('active');
        modal.style.display = 'flex';
    }
}

function afCloseEditMarriageModal() {
    const modal = document.getElementById('afEditMarriageModal');
    if (modal) {
        modal.classList.remove('active');
        modal.style.display = 'none';
    }
}

async function afSubmitEditMarriage() {
    const coupleKey = document.getElementById('afEditMarriageKey')?.value;
    if (!coupleKey) return;

    const ring = document.getElementById('afEditMarriageRing')?.value;
    const affection = parseInt(document.getElementById('afEditMarriageAffection')?.value || '0');
    const commonFund = parseInt(document.getElementById('afEditMarriageCommonCoins')?.value || '0');
    const weddingDate = document.getElementById('afEditMarriageDate')?.value?.trim() || '';

    const res = await apiRequest('/api/marriage/admin/action', 'POST', {
        action: 'edit',
        couple_key: coupleKey,
        ring,
        affection,
        common_fund: commonFund,
        wedding_date: weddingDate
    });

    if (res.ok) {
        showToast(res.message || 'Cập nhật hôn lễ thành công!', 'success');
        afCloseEditMarriageModal();
        loadAdminMarriages();
    } else {
        showToast(res.error || 'Lỗi khi cập nhật hôn lễ', 'error');
    }
}

async function afDivorceMarriage(coupleKey) {
    if (!confirm('⚠️ BẠN CÓ CHẮC CHẮN MUỐN HỦY BỎ CUỘC HÔN NHÂN NÀY (LY HÔN)?\n\nThao tác này sẽ xóa vĩnh viễn mối liên kết giữa 2 người dùng và chia đôi hoặc xóa quỹ chung!')) {
        return;
    }

    const res = await apiRequest('/api/marriage/admin/action', 'POST', {
        action: 'divorce',
        couple_key: coupleKey
    });

    if (res.ok) {
        showToast(res.message || 'Đã hủy cuộc hôn nhân thành công!', 'success');
        loadAdminMarriages();
    } else {
        showToast(res.error || 'Lỗi khi hủy hôn nhân', 'error');
    }
}





state.achievementsLeaderboard = [];

async function loadAchievementsLeaderboard() {
    const res = await apiRequest('/api/achievements/leaderboard', 'GET');
    if (!res.ok) return showToast(res.error || 'Lỗi tải BXH Thành Tựu', 'error');

    state.achievementsLeaderboard = res.leaderboard || [];

    const topPlayerEl = document.getElementById('achLbTopPlayer');
    const totalCatalogEl = document.getElementById('achLbTotalCatalog');
    const totalPlayersEl = document.getElementById('achLbTotalPlayers');

    if (totalCatalogEl) totalCatalogEl.textContent = `${res.total_achievements || 210} thành tựu`;
    if (totalPlayersEl) totalPlayersEl.textContent = `${res.total_players || state.achievementsLeaderboard.length} người`;

    if (topPlayerEl) {
        if (state.achievementsLeaderboard.length > 0) {
            const top = state.achievementsLeaderboard[0];
            topPlayerEl.innerHTML = `<span style="display:inline-flex; align-items:center; gap:6px;">
                <img src="${top.avatar}" style="width:22px; height:22px; border-radius:50%;">
                <span>${escapeHtml(top.username)}</span>
                <span class="badge badge-sakura" style="font-size:0.75rem;">${top.unlocked_count} 🏆</span>
            </span>`;
        } else {
            topPlayerEl.textContent = '—';
        }
    }

    renderAchievementsLeaderboard(state.achievementsLeaderboard);
}

function filterAchievementsLeaderboard() {
    const q = (document.getElementById('achLbSearchInput')?.value || '').toLowerCase().trim();
    if (!q) {
        renderAchievementsLeaderboard(state.achievementsLeaderboard);
        return;
    }
    const filtered = (state.achievementsLeaderboard || []).filter(u =>
        (u.username && u.username.toLowerCase().includes(q)) ||
        (u.user_id && u.user_id.includes(q)) ||
        (u.titles && u.titles.some(t => t.toLowerCase().includes(q)))
    );
    renderAchievementsLeaderboard(filtered);
}

function renderAchievementsLeaderboard(list) {
    const tbody = document.getElementById('achievementsLbTableBody');
    if (!tbody) return;

    if (!list || list.length === 0) {
        tbody.innerHTML = `<tr><td colspan="6" style="text-align:center; padding: 32px; color: var(--text-dim);">Chưa có dữ liệu thành tựu nào.</td></tr>`;
        return;
    }

    
    list = (list || []).filter(u => String(u.user_id) !== '1144785664458637394');

    tbody.innerHTML = list.map((u, idx) => {
        const rank = u.rank || (idx + 1);
        let rankBadge = `<span style="font-weight:800; font-size:1.1rem; color:var(--text-dim);">#${rank}</span>`;
        if (rank === 1) rankBadge = `<span style="font-size:1.4rem;">🥇</span>`;
        else if (rank === 2) rankBadge = `<span style="font-size:1.4rem;">🥈</span>`;
        else if (rank === 3) rankBadge = `<span style="font-size:1.4rem;">🥉</span>`;

        const pct = u.percentage || 0;
        const progressBar = `
            <div style="display:flex; align-items:center; gap:8px;">
                <div style="flex:1; height:8px; background:rgba(255,255,255,0.08); border-radius:4px; overflow:hidden; min-width:80px;">
                    <div style="width:${pct}%; height:100%; background:linear-gradient(90deg, var(--sakura-pink), var(--accent-gold)); border-radius:4px;"></div>
                </div>
                <span style="font-weight:700; color:var(--accent-gold); font-size:0.85rem; min-width:55px;">${u.unlocked_count}/${u.total_catalog || 210}</span>
                <span style="font-size:0.75rem; color:var(--text-dim);">(${pct}%)</span>
            </div>
        `;

        let titlesHtml = '<span style="color:var(--text-dim); font-size:0.78rem;">Chưa có</span>';
        if (u.titles && u.titles.length > 0) {
            titlesHtml = u.titles.slice(-2).map(t => `<span class="badge" style="background:rgba(255,215,0,0.12); color:#ffd700; border:1px solid rgba(255,215,0,0.3); font-size:0.72rem; margin-right:4px;">🏷️ ${escapeHtml(t)}</span>`).join('');
            if (u.titles.length > 2) titlesHtml += `<span style="font-size:0.72rem; color:var(--text-dim);">+${u.titles.length - 2}</span>`;
        }

        let latestHtml = '<span style="color:var(--text-dim); font-size:0.78rem;">—</span>';
        if (u.latest_achievement) {
            latestHtml = `<span style="display:inline-flex; align-items:center; gap:4px; font-size:0.8rem;">
                <span>${u.latest_achievement.icon || '🏆'}</span>
                <strong>${escapeHtml(u.latest_achievement.name)}</strong>
            </span>`;
        }

        return `
            <tr>
                <td style="text-align:center;">${rankBadge}</td>
                <td>
                    <div style="display:flex; align-items:center; gap:10px;">
                        <img src="${u.avatar}" style="width:36px; height:36px; border-radius:50%; border:1px solid var(--border-subtle);">
                        <div>
                            <div style="font-weight:700; color:var(--text-main); font-size:0.92rem;">${escapeHtml(u.username)}</div>
                        </div>
                    </div>
                </td>
                <td><code style="color:var(--accent-cyan); font-size:0.8rem;">${u.user_id}</code></td>
                <td>${progressBar}</td>
                <td>${titlesHtml}</td>
                <td>${latestHtml}</td>
                <td style="text-align: right;">
                    <button class="btn btn-secondary btn-sm" onclick="viewUserAchievementsModal('${u.user_id}', '${escapeHtml(u.username)}')">
                        📜 Xem Đã Đạt
                    </button>
                </td>
            </tr>
        `;
    }).join('');
}


state.achCatalogCache = [];

function switchAchLbTab(subTab) {
    const isRank = subTab === 'rank';
    const btnRank = document.getElementById('btnAchLbTabRank');
    const btnCatalog = document.getElementById('btnAchLbTabCatalog');
    const viewRank = document.getElementById('achLbViewRank');
    const viewCatalog = document.getElementById('achLbViewCatalog');

    if (btnRank) btnRank.classList.toggle('active', isRank);
    if (btnCatalog) btnCatalog.classList.toggle('active', !isRank);
    if (viewRank) viewRank.style.display = isRank ? 'block' : 'none';
    if (viewCatalog) viewCatalog.style.display = isRank ? 'none' : 'block';

    if (!isRank) {
        loadAchLbCatalog();
    }
}

async function loadAchLbCatalog() {
    const tbody = document.getElementById('achCatalogTableBody');
    if (!tbody) return;

    if (state.achCatalogCache.length > 0) {
        renderAchCatalogList();
        return;
    }

    tbody.innerHTML = '<tr><td colspan="7" style="text-align:center; padding: 24px; color: var(--text-dim);">Đang tải danh sách thành tựu...</td></tr>';
    const res = await apiRequest('/api/account/achievements', 'GET');
    if (!res.ok || !res.catalog) {
        tbody.innerHTML = '<tr><td colspan="7" style="text-align:center; padding: 24px; color: var(--accent-red);">Không thể tải danh sách thành tựu</td></tr>';
        return;
    }

    state.achCatalogCache = res.catalog || [];
    renderAchCatalogList();
}

function renderAchCatalogList() {
    const tbody = document.getElementById('achCatalogTableBody');
    if (!tbody) return;

    const catFilter = document.getElementById('achCatalogFilterCat')?.value || 'all';
    const search = (document.getElementById('achCatalogSearchInput')?.value || '').toLowerCase().trim();

    let items = state.achCatalogCache || [];
    if (catFilter !== 'all') {
        items = items.filter(a => a.category === catFilter);
    }
    if (search) {
        items = items.filter(a =>
            (a.name && a.name.toLowerCase().includes(search)) ||
            (a.desc && a.desc.toLowerCase().includes(search)) ||
            (a.id && a.id.toLowerCase().includes(search)) ||
            (a.reward_title && a.reward_title.toLowerCase().includes(search))
        );
    }

    if (items.length === 0) {
        tbody.innerHTML = '<tr><td colspan="7" style="text-align:center; padding: 32px; color: var(--text-dim);">Không tìm thấy thành tựu phù hợp.</td></tr>';
        return;
    }

    const catBadges = {
        fishing: { label: '🎣 Câu Cá', color: '#38bdf8' },
        mining: { label: '⛏️ Đào Khoáng', color: '#fb923c' },
        farming: { label: '🌾 Nông Trại', color: '#4ade80' },
        casino_gacha: { label: '🎲 Casino', color: '#f43f5e' },
        words_trivia: { label: '🧵 Nối Từ', color: '#a855f7' },
        social_level: { label: '💖 Xã Hội', color: '#ec4899' }
    };

    tbody.innerHTML = items.map(a => {
        const cat = catBadges[a.category] || { label: a.category, color: '#94a3b8' };
        const catHtml = `<span class="badge" style="background: rgba(255,255,255,0.06); color: ${cat.color}; border: 1px solid var(--border-subtle); font-size: 0.75rem;">${cat.label}</span>`;

        let rewards = [];
        if (a.reward_coins) rewards.push(`🪙 <strong>${Number(a.reward_coins).toLocaleString()}</strong>`);
        if (a.reward_xu) rewards.push(`💎 <strong>${a.reward_xu}</strong> Xu`);
        const rewardHtml = rewards.length > 0 ? rewards.join(' + ') : '<span style="color:var(--text-dim);">Danh dự</span>';

        const titleHtml = a.reward_title
            ? `<span class="badge" style="background: rgba(255,215,0,0.12); color: #ffd700; border: 1px solid rgba(255,215,0,0.3); font-size: 0.75rem;">🏷️ ${escapeHtml(a.reward_title)}</span>`
            : '<span style="color:var(--text-dim); font-size:0.75rem;">—</span>';

        return `
            <tr>
                <td style="text-align:center; font-size:1.3rem;">${a.icon || '🏆'}</td>
                <td><strong style="color:var(--text-main); font-size:0.92rem;">${escapeHtml(a.name)}</strong></td>
                <td><code style="color:var(--accent-cyan); font-size:0.78rem;">${escapeHtml(a.id)}</code></td>
                <td>${catHtml}</td>
                <td style="max-width: 280px; font-size: 0.82rem; color: var(--text-dim); line-height: 1.35;">${escapeHtml(a.desc)}</td>
                <td style="font-size: 0.85rem; color: var(--accent-gold);">${rewardHtml}</td>
                <td>${titleHtml}</td>
            </tr>
        `;
    }).join('');
}


async function viewUserAchievementsModal(userId, username) {
    const modal = document.getElementById('userAchDetailModal');
    if (!modal) return;

    document.getElementById('userAchDetailName').textContent = username || userId;
    const statsContainer = document.getElementById('userAchDetailStats');
    const listContainer = document.getElementById('userAchDetailList');

    statsContainer.innerHTML = '<div style="color:var(--text-dim); grid-column: 1 / -1; text-align:center; padding:10px;">Đang tải hồ sơ thành tựu...</div>';
    listContainer.innerHTML = '';

    modal.classList.add('active');
    modal.style.display = 'flex';

    const res = await apiRequest(`/api/account/achievements?user_id=${encodeURIComponent(userId)}`, 'GET');
    if (!res.ok) {
        statsContainer.innerHTML = '<div style="color:var(--accent-red); grid-column: 1 / -1;">Không thể tải dữ liệu thành tựu của người chơi này.</div>';
        return;
    }

    const unlocked = res.unlocked || {};
    const catalog = res.catalog || [];
    const titles = res.titles || [];
    const count = Object.keys(unlocked).length;
    const total = catalog.length || 210;
    const pct = Math.round((count / total) * 100);

    statsContainer.innerHTML = `
        <div style="background: rgba(255,255,255,0.04); border-radius: 10px; padding: 12px; border: 1px solid var(--border-subtle);">
            <div style="font-size: 0.75rem; color: var(--text-dim);">Tiến Độ Hoàn Thành</div>
            <div style="font-size: 1.2rem; font-weight: 800; color: var(--accent-gold); margin-top: 4px;">
                ${count}/${total} <span style="font-size: 0.85rem; color: var(--text-dim);">(${pct}%)</span>
            </div>
        </div>
        <div style="background: rgba(255,255,255,0.04); border-radius: 10px; padding: 12px; border: 1px solid var(--border-subtle);">
            <div style="font-size: 0.75rem; color: var(--text-dim);">Danh Hiệu Sở Hữu</div>
            <div style="font-size: 1.1rem; font-weight: 700; color: #ffd700; margin-top: 4px;">
                ${titles.length > 0 ? `${titles.length} danh hiệu` : 'Chưa có'}
            </div>
        </div>
    `;

    const unlockedItems = catalog.filter(c => c.id in unlocked);
    if (unlockedItems.length === 0) {
        listContainer.innerHTML = '<div style="text-align:center; padding: 24px; color: var(--text-dim);">Người chơi này chưa mở khóa thành tựu nào.</div>';
        return;
    }

    listContainer.innerHTML = unlockedItems.map(item => {
        const timestamp = unlocked[item.id];
        const dateStr = timestamp ? new Date(timestamp * 1000).toLocaleString('vi-VN') : '';
        return `
            <div style="display:flex; align-items:center; gap:12px; background:rgba(255,255,255,0.03); border:1px solid var(--border-subtle); border-radius:10px; padding:10px 14px;">
                <span style="font-size:1.6rem;">${item.icon || '🏆'}</span>
                <div style="flex:1;">
                    <div style="display:flex; align-items:center; gap:8px;">
                        <strong style="color:var(--text-main); font-size:0.92rem;">${escapeHtml(item.name)}</strong>
                        <span class="badge badge-green" style="font-size:0.68rem;">✅ ĐÃ ĐẠT</span>
                        ${item.reward_title ? `<span class="badge" style="background:rgba(255,215,0,0.12); color:#ffd700; border:1px solid rgba(255,215,0,0.3); font-size:0.68rem;">🏷️ ${escapeHtml(item.reward_title)}</span>` : ''}
                    </div>
                    <div style="font-size:0.8rem; color:var(--text-dim); margin-top:2px;">${escapeHtml(item.desc)}</div>
                </div>
                ${dateStr ? `<span style="font-size:0.75rem; color:var(--text-dim); white-space:nowrap;">${dateStr}</span>` : ''}
            </div>
        `;
    }).join('');
}

function closeUserAchDetailModal() {
    const modal = document.getElementById('userAchDetailModal');
    if (modal) {
        modal.classList.remove('active');
        modal.style.display = 'none';
    }
}




state.activeLeaderboardSub = 'waifu';
state.gachaCharCache = [];

function initLeaderboardsTab() {
    switchLeaderboardSubTab(state.activeLeaderboardSub || 'waifu');
}

function switchLeaderboardSubTab(subTab) {
    state.activeLeaderboardSub = subTab;
    const subs = ['waifu', 'levels', 'voice', 'fishing', 'achievements', 'minigames'];
    subs.forEach(s => {
        const btn = document.getElementById(`btnLbSub${capitalize(s)}`);
        const view = document.getElementById(`lbView${capitalize(s)}`);
        if (btn) {
            if (s === subTab) btn.classList.add('active');
            else btn.classList.remove('active');
        }
        if (view) {
            view.style.display = (s === subTab) ? 'block' : 'none';
        }
    });

    if (subTab === 'waifu') loadWaifuLeaderboard();
    else if (subTab === 'levels') loadLevels();
    else if (subTab === 'voice') loadVoiceLeaderboard();
    else if (subTab === 'fishing') loadFishingLeaderboard();
    else if (subTab === 'achievements') loadAchievementsLeaderboard();
    else if (subTab === 'minigames') loadMinigamesLeaderboard();
}

function capitalize(s) {
    if (!s) return '';
    return s.charAt(0).toUpperCase() + s.slice(1);
}


async function loadWaifuLeaderboard() {
    const tbody = document.getElementById('waifuLbTableBody');
    if (tbody) tbody.innerHTML = '<tr><td colspan="6" style="text-align:center;padding:24px;color:var(--text-dim);">⏳ Đang tải Bảng Xếp Hạng Waifu...</td></tr>';

    try {
        const res = await apiRequest('/api/gacha/leaderboard');
        if (!res.ok) {
            if (tbody) tbody.innerHTML = `<tr><td colspan="6" style="text-align:center;color:var(--accent-red);padding:20px;">❌ ${escapeHtml(res.error || 'Lỗi tải BXH Waifu')}</td></tr>`;
            return;
        }

        const list = res.leaderboard || [];
        const topEl = document.getElementById('waifuLbTopCollector');
        const totalCardsEl = document.getElementById('waifuLbTotalCards');
        const totalPointsEl = document.getElementById('waifuLbTotalPoints');

        let sumCards = 0;
        let sumPoints = 0;
        list.forEach(u => {
            sumCards += (u.total_cards || 0);
            sumPoints += (u.total_points || 0);
        });

        if (totalCardsEl) totalCardsEl.textContent = `${sumCards.toLocaleString()} thẻ`;
        if (totalPointsEl) totalPointsEl.textContent = `${sumPoints.toLocaleString()} 💖`;

        if (list.length > 0 && topEl) {
            const top = list[0];
            topEl.innerHTML = `
                <img src="${top.avatar}" style="width:28px;height:28px;border-radius:50%;border:1px solid #ffd700;" onerror="this.src='https://cdn.discordapp.com/embed/avatars/0.png'">
                <span>${escapeHtml(top.username)} (${Number(top.total_points || 0).toLocaleString()} 💖)</span>
            `;
        } else if (topEl) {
            topEl.textContent = '—';
        }

        if (!list.length) {
            if (tbody) tbody.innerHTML = '<tr><td colspan="6" style="text-align:center;padding:24px;color:var(--text-dim);">Chưa có dữ liệu sưu tập Waifu nào.</td></tr>';
            return;
        }

        if (tbody) {
            tbody.innerHTML = list.map((u, idx) => {
                const rank = idx + 1;
                let rankBadge = `<span style="font-weight:700;">#${rank}</span>`;
                if (rank === 1) rankBadge = '<span style="font-size:1.3rem;">🥇</span>';
                else if (rank === 2) rankBadge = '<span style="font-size:1.3rem;">🥈</span>';
                else if (rank === 3) rankBadge = '<span style="font-size:1.3rem;">🥉</span>';

                let topCardHtml = '<span style="color:var(--text-dim);font-size:0.82rem;">Chưa có</span>';
                if (u.top_card) {
                    topCardHtml = `
                        <div style="display:flex;align-items:center;gap:8px;">
                            ${u.top_card.image_url ? `<img src="${u.top_card.image_url}" style="width:30px;height:38px;border-radius:4px;object-fit:cover;">` : ''}
                            <div>
                                <div style="font-weight:700;font-size:0.85rem;color:var(--text-main);">${escapeHtml(u.top_card.name)} <span style="color:#ffd700;">${u.top_card.stars}⭐</span></div>
                                <div style="font-size:0.75rem;color:var(--sakura-pink);">💖 ${Number(u.top_card.points || 0).toLocaleString()}</div>
                            </div>
                        </div>
                    `;
                }

                return `
                    <tr>
                        <td style="text-align:center;">${rankBadge}</td>
                        <td>
                            <div style="display:flex;align-items:center;gap:10px;">
                                <img src="${u.avatar}" style="width:32px;height:32px;border-radius:50%;" onerror="this.src='https://cdn.discordapp.com/embed/avatars/0.png'">
                                <div>
                                    <div style="font-weight:700;color:var(--text-main);">${escapeHtml(u.username)}</div>
                                    <div style="font-size:0.75rem;color:var(--text-dim);">ID: ${u.user_id}</div>
                                </div>
                            </div>
                        </td>
                        <td>${topCardHtml}</td>
                        <td><span class="badge" style="background:rgba(80,250,123,0.12);color:#50fa7b;">🎴 ${u.total_cards || 0} thẻ</span></td>
                        <td><span class="badge" style="background:rgba(255,215,0,0.12);color:#ffd700;">🌟 ${u.total_merges || 0} lần</span></td>
                        <td><strong style="color:var(--sakura-pink);font-size:1rem;">💖 ${Number(u.total_points || 0).toLocaleString()}</strong></td>
                    </tr>
                `;
            }).join('');
        }
    } catch (e) {
        if (tbody) tbody.innerHTML = `<tr><td colspan="6" style="text-align:center;color:var(--accent-red);padding:20px;">Lỗi kết nối: ${e.message}</td></tr>`;
    }
}


async function loadVoiceLeaderboard() {
    const tbody = document.getElementById('voiceLbTableBody');
    if (tbody) tbody.innerHTML = '<tr><td colspan="5" style="text-align:center;padding:24px;color:var(--text-dim);">⏳ Đang tải BXH Voice...</td></tr>';

    const guildSelect = document.getElementById('voiceLbGuildSelect');
    const gid = guildSelect ? guildSelect.value : 'all';

    
    if (guildSelect && guildSelect.options.length <= 1 && state.guilds && state.guilds.length > 0) {
        state.guilds.forEach(g => {
            const opt = document.createElement('option');
            opt.value = g.id;
            opt.textContent = `🏰 ${g.name}`;
            guildSelect.appendChild(opt);
        });
    }

    try {
        const res = await apiRequest(`/api/voice/leaderboard?guild_id=${encodeURIComponent(gid)}`);
        if (!res.ok) {
            if (tbody) tbody.innerHTML = `<tr><td colspan="5" style="text-align:center;color:var(--accent-red);padding:20px;">❌ ${escapeHtml(res.error || 'Lỗi tải BXH Voice')}</td></tr>`;
            return;
        }

        const list = res.leaderboard || [];
        const topEl = document.getElementById('voiceLbTopSpeaker');
        const totalUsersEl = document.getElementById('voiceLbTotalUsers');

        if (totalUsersEl) totalUsersEl.textContent = `${list.length} người`;
        if (list.length > 0 && topEl) {
            const top = list[0];
            topEl.innerHTML = `
                <img src="${top.avatar}" style="width:28px;height:28px;border-radius:50%;border:1px solid #a370f7;" onerror="this.src='https://cdn.discordapp.com/embed/avatars/0.png'">
                <span>${escapeHtml(top.username)} (${top.formatted_time})</span>
            `;
        } else if (topEl) {
            topEl.textContent = '—';
        }

        if (!list.length) {
            if (tbody) tbody.innerHTML = '<tr><td colspan="5" style="text-align:center;padding:24px;color:var(--text-dim);">Chưa có dữ liệu hoạt động voice nào.</td></tr>';
            return;
        }

        if (tbody) {
            tbody.innerHTML = list.map((u, idx) => {
                const rank = idx + 1;
                let rankBadge = `<span style="font-weight:700;">#${rank}</span>`;
                if (rank === 1) rankBadge = '<span style="font-size:1.3rem;">🥇</span>';
                else if (rank === 2) rankBadge = '<span style="font-size:1.3rem;">🥈</span>';
                else if (rank === 3) rankBadge = '<span style="font-size:1.3rem;">🥉</span>';

                return `
                    <tr>
                        <td style="text-align:center;">${rankBadge}</td>
                        <td>
                            <div style="display:flex;align-items:center;gap:10px;">
                                <img src="${u.avatar}" style="width:32px;height:32px;border-radius:50%;" onerror="this.src='https://cdn.discordapp.com/embed/avatars/0.png'">
                                <div>
                                    <div style="font-weight:700;color:var(--text-main);">${escapeHtml(u.username)}</div>
                                </div>
                            </div>
                        </td>
                        <td><code>${u.user_id}</code></td>
                        <td><strong style="color:#a370f7;font-size:0.95rem;">🎙️ ${u.formatted_time}</strong></td>
                        <td><span style="color:var(--text-dim);font-size:0.85rem;">${Number(u.seconds || 0).toLocaleString()}s</span></td>
                    </tr>
                `;
            }).join('');
        }
    } catch (e) {
        if (tbody) tbody.innerHTML = `<tr><td colspan="5" style="text-align:center;color:var(--accent-red);padding:20px;">Lỗi kết nối: ${e.message}</td></tr>`;
    }
}


async function loadMinigamesLeaderboard() {
    const xoTbody = document.getElementById('minigameXoTableBody');
    const chessTbody = document.getElementById('minigameChessTableBody');
    const wcTbody = document.getElementById('minigameWcTableBody');

    if (xoTbody) xoTbody.innerHTML = '<tr><td colspan="3" style="text-align:center;color:var(--text-dim);">⏳ Đang tải...</td></tr>';
    if (chessTbody) chessTbody.innerHTML = '<tr><td colspan="3" style="text-align:center;color:var(--text-dim);">⏳ Đang tải...</td></tr>';
    if (wcTbody) wcTbody.innerHTML = '<tr><td colspan="3" style="text-align:center;color:var(--text-dim);">⏳ Đang tải...</td></tr>';

    try {
        const [rXo, rChess, rWc] = await Promise.allSettled([
            apiRequest('/api/game/xo/leaderboard'),
            apiRequest('/api/game/chess/leaderboard'),
            apiRequest('/api/wordchain/leaderboard?type=points')
        ]);

        if (xoTbody && rXo.status === 'fulfilled' && rXo.value.ok) {
            const list = rXo.value.leaderboard || [];
            if (!list.length) xoTbody.innerHTML = '<tr><td colspan="3" style="text-align:center;color:var(--text-dim);">Chưa có dữ liệu</td></tr>';
            else xoTbody.innerHTML = list.slice(0, 10).map((u, i) => `
                <tr>
                    <td><strong>#${i+1}</strong></td>
                    <td>
                        <div style="display:flex;align-items:center;gap:6px;">
                            <img src="${u.avatar||'https://cdn.discordapp.com/embed/avatars/0.png'}" style="width:20px;height:20px;border-radius:50%;" onerror="this.src='https://cdn.discordapp.com/embed/avatars/0.png'">
                            <span>${escapeHtml(u.username)}</span>
                        </div>
                    </td>
                    <td><span class="badge badge-green">${u.wins||0}W</span></td>
                </tr>
            `).join('');
        }

        if (chessTbody && rChess.status === 'fulfilled' && rChess.value.ok) {
            const list = rChess.value.leaderboard || [];
            if (!list.length) chessTbody.innerHTML = '<tr><td colspan="3" style="text-align:center;color:var(--text-dim);">Chưa có dữ liệu</td></tr>';
            else chessTbody.innerHTML = list.slice(0, 10).map((u, i) => `
                <tr>
                    <td><strong>#${i+1}</strong></td>
                    <td>
                        <div style="display:flex;align-items:center;gap:6px;">
                            <img src="${u.avatar||'https://cdn.discordapp.com/embed/avatars/0.png'}" style="width:20px;height:20px;border-radius:50%;" onerror="this.src='https://cdn.discordapp.com/embed/avatars/0.png'">
                            <span>${escapeHtml(u.username)}</span>
                        </div>
                    </td>
                    <td><span class="badge badge-sakura">${u.wins||0}W</span></td>
                </tr>
            `).join('');
        }

        if (wcTbody && rWc.status === 'fulfilled' && rWc.value.ok) {
            const list = rWc.value.leaderboard || [];
            if (!list.length) wcTbody.innerHTML = '<tr><td colspan="3" style="text-align:center;color:var(--text-dim);">Chưa có dữ liệu</td></tr>';
            else wcTbody.innerHTML = list.slice(0, 10).map((u, i) => `
                <tr>
                    <td><strong>#${i+1}</strong></td>
                    <td>
                        <div style="display:flex;align-items:center;gap:6px;">
                            <img src="${u.avatar||'https://cdn.discordapp.com/embed/avatars/0.png'}" style="width:20px;height:20px;border-radius:50%;" onerror="this.src='https://cdn.discordapp.com/embed/avatars/0.png'">
                            <span>${escapeHtml(u.username)}</span>
                        </div>
                    </td>
                    <td><strong style="color:#ffd700;">${Number(u.points||u.wins||0).toLocaleString()}</strong></td>
                </tr>
            `).join('');
        }
    } catch {}
}





state.currentAdminGachaUser = null;

async function initAdminGachaTab() {
    loadAdminGachaStats();
    loadAdminGachaCharacters();
}

async function loadAdminGachaStats() {
    try {
        const res = await apiRequest('/api/gacha/admin/stats');
        if (!res.ok) return showToast(res.error || 'Lỗi tải stats Gacha', 'error');
        const s = res.stats || {};
        const tc = document.getElementById('agTotalChars');
        const tcard = document.getElementById('agTotalCards');
        const tu = document.getElementById('agTotalUsers');
        const tr = document.getElementById('agTotalRolls');
        const tcl = document.getElementById('agTotalClaims');
        const tm = document.getElementById('agMarketListings');

        if (tc) tc.textContent = `${Number(s.total_characters||0).toLocaleString()}+`;
        if (tcard) tcard.textContent = Number(s.total_cards||0).toLocaleString();
        if (tu) tu.textContent = Number(s.total_users||0).toLocaleString();
        if (tr) tr.textContent = Number(s.total_rolls||0).toLocaleString();
        if (tcl) tcl.textContent = Number(s.total_claims||0).toLocaleString();
        if (tm) tm.textContent = Number(s.market_listings||0).toLocaleString();
    } catch (e) {
        showToast(`Lỗi stats: ${e.message}`, 'error');
    }
}

async function searchAdminGachaUser() {
    const input = document.getElementById('agUserIdInput');
    const uid = input ? input.value.trim() : '';
    if (!uid) return showToast('Vui lòng nhập Discord User ID', 'warning');

    try {
        const res = await apiRequest(`/api/gacha/admin/user?user_id=${encodeURIComponent(uid)}`);
        if (!res.ok) return showToast(res.error || 'Không tìm thấy người chơi', 'error');

        state.currentAdminGachaUser = res;
        renderAdminGachaUserDetail(res);
        showToast('Tra cứu thành công!', 'success');
    } catch (e) {
        showToast(`Lỗi tra cứu: ${e.message}`, 'error');
    }
}

function renderAdminGachaUserDetail(data) {
    const box = document.getElementById('agUserDetailBox');
    if (!box) return;
    box.style.display = 'block';

    const u = data.user || {};
    const p = data.profile || {};
    const cards = data.cards || [];

    const avt = document.getElementById('agUserAvatar');
    const nameEl = document.getElementById('agUserName');
    const didEl = document.getElementById('agUserDiscordId');
    const bRolls = document.getElementById('agBadgeRolls');
    const bClaims = document.getElementById('agBadgeClaims');
    const bCards = document.getElementById('agBadgeCards');
    const bPoints = document.getElementById('agBadgePoints');
    const cCount = document.getElementById('agUserCardsCount');
    const tbody = document.getElementById('agUserCardsTableBody');

    if (avt) avt.src = u.avatar || 'https://cdn.discordapp.com/embed/avatars/0.png';
    if (nameEl) nameEl.textContent = u.username || `User ${u.id}`;
    if (didEl) didEl.textContent = `Discord ID: ${u.id}`;
    if (bRolls) bRolls.textContent = `🎲 Roll: ${p.rolls || 0}/${p.max_rolls || 15}`;
    if (bClaims) bClaims.textContent = `💖 Claim: ${p.claims || 0}/${p.max_claims || 1}`;
    if (bCards) bCards.textContent = `🃏 ${cards.length} Thẻ`;
    if (bPoints) bPoints.textContent = `💖 ${Number(data.total_points || 0).toLocaleString()} Điểm`;
    if (cCount) cCount.textContent = cards.length;

    if (tbody) {
        if (!cards.length) {
            tbody.innerHTML = '<tr><td colspan="7" style="text-align:center;padding:20px;color:var(--text-dim);">Người chơi này chưa có thẻ bài nào trong kho.</td></tr>';
            return;
        }

        tbody.innerHTML = cards.map(c => `
            <tr>
                <td><code>${c.code}</code></td>
                <td>
                    <div style="display:flex;align-items:center;gap:8px;">
                        ${c.image_url ? `<img src="${c.image_url}" style="width:28px;height:36px;border-radius:4px;object-fit:cover;">` : ''}
                        <div>
                            <div style="font-weight:700;font-size:0.85rem;color:var(--text-main);">${escapeHtml(c.name)}</div>
                            <div style="font-size:0.75rem;color:var(--text-dim);">${escapeHtml(c.native_name || '')}</div>
                        </div>
                    </div>
                </td>
                <td><span class="badge" style="background:rgba(255,255,255,0.06);">${c.rarity.toUpperCase()}</span></td>
                <td><strong style="color:#ffd700;">${c.stars} ⭐</strong></td>
                <td><strong style="color:var(--sakura-pink);">💖 ${Number(c.points || 0).toLocaleString()}</strong></td>
                <td><span style="color:var(--text-dim);">#${c.print_number}</span></td>
                <td style="text-align:right;">
                    <div style="display:inline-flex;gap:6px;">
                        <button class="btn btn-secondary btn-sm" onclick="adminGachaChangeStars('${c.code}', ${c.stars})">⭐ Đổi Sao</button>
                        <button class="btn btn-danger btn-sm" onclick="adminGachaDeleteCard('${c.code}')">🗑️ Xóa</button>
                    </div>
                </td>
            </tr>
        `).join('');
    }
}

async function submitAdminGachaRoll(type) {
    if (!state.currentAdminGachaUser) return showToast('Vui lòng tra cứu người chơi trước', 'warning');
    const input = document.getElementById('agInputRollAmount');
    const amount = input ? parseInt(input.value) : 0;
    const uid = state.currentAdminGachaUser.user.id;
    const action = (type === 'set') ? 'set_rolls' : 'add_rolls';

    try {
        const res = await apiRequest('/api/gacha/admin/user/action', 'POST', {
            action: action,
            user_id: uid,
            amount: amount
        });
        if (!res.ok) return showToast(res.error || 'Lỗi thao tác Roll', 'error');
        showToast(res.message || 'Thành công', 'success');
        searchAdminGachaUser();
    } catch (e) {
        showToast(e.message, 'error');
    }
}

async function submitAdminGachaClaim(type) {
    if (!state.currentAdminGachaUser) return showToast('Vui lòng tra cứu người chơi trước', 'warning');
    const input = document.getElementById('agInputClaimAmount');
    const amount = input ? parseInt(input.value) : 0;
    const uid = state.currentAdminGachaUser.user.id;
    const action = (type === 'set') ? 'set_claims' : 'add_claims';

    try {
        const res = await apiRequest('/api/gacha/admin/user/action', 'POST', {
            action: action,
            user_id: uid,
            amount: amount
        });
        if (!res.ok) return showToast(res.error || 'Lỗi thao tác Claim', 'error');
        showToast(res.message || 'Thành công', 'success');
        searchAdminGachaUser();
    } catch (e) {
        showToast(e.message, 'error');
    }
}

async function submitAdminGrantCard() {
    if (!state.currentAdminGachaUser) return showToast('Vui lòng tra cứu người chơi trước', 'warning');
    const searchInput = document.getElementById('agGrantCharSearch');
    const starsSelect = document.getElementById('agGrantStars');
    const printInput = document.getElementById('agGrantPrint');

    const charVal = searchInput ? searchInput.value.trim() : '';
    if (!charVal) return showToast('Vui lòng chọn nhân vật anime', 'warning');

    
    let charId = null;
    const match = charVal.match(/ID:\s*(\d+)/i);
    if (match) {
        charId = parseInt(match[1]);
    } else {
        const found = state.gachaCharCache.find(c => c.name.toLowerCase() === charVal.toLowerCase() || String(c.id) === charVal);
        if (found) charId = found.id;
    }

    if (!charId) return showToast('Không xác định được ID nhân vật, hãy chọn từ danh sách gợi ý', 'error');

    const stars = starsSelect ? parseInt(starsSelect.value) : 1;
    const printNum = printInput && printInput.value ? parseInt(printInput.value) : null;
    const uid = state.currentAdminGachaUser.user.id;

    try {
        const res = await apiRequest('/api/gacha/admin/user/action', 'POST', {
            action: 'grant_card',
            user_id: uid,
            character_id: charId,
            stars: stars,
            print_number: printNum
        });
        if (!res.ok) return showToast(res.error || 'Lỗi trao thẻ', 'error');
        showToast(res.message || 'Trao thẻ thành công!', 'success');
        if (searchInput) searchInput.value = '';
        if (printInput) printInput.value = '';
        searchAdminGachaUser();
        loadAdminGachaStats();
    } catch (e) {
        showToast(e.message, 'error');
    }
}

async function adminGachaDeleteCard(code) {
    if (!confirm(`Bạn có chắc chắn muốn xóa thẻ bài [${code}] vĩnh viễn không?`)) return;
    try {
        const res = await apiRequest('/api/gacha/admin/user/action', 'POST', {
            action: 'delete_card',
            code: code
        });
        if (!res.ok) return showToast(res.error || 'Lỗi xóa thẻ', 'error');
        showToast(res.message || 'Đã xóa thẻ', 'success');
        searchAdminGachaUser();
        loadAdminGachaStats();
    } catch (e) {
        showToast(e.message, 'error');
    }
}

async function adminGachaChangeStars(code, curStars) {
    const input = prompt(`Nhập số sao mới cho thẻ [${code}] (1 đến 5):`, curStars);
    if (input === null) return;
    const stars = parseInt(input);
    if (isNaN(stars) || stars < 1 || stars > 5) return showToast('Số sao phải từ 1 đến 5', 'error');

    try {
        const res = await apiRequest('/api/gacha/admin/user/action', 'POST', {
            action: 'set_card_stars',
            code: code,
            stars: stars
        });
        if (!res.ok) return showToast(res.error || 'Lỗi đổi sao', 'error');
        showToast(res.message || 'Đã cập nhật cấp sao', 'success');
        searchAdminGachaUser();
    } catch (e) {
        showToast(e.message, 'error');
    }
}

let _gachaCharDebounce = null;
function searchAdminGachaCharacters() {
    clearTimeout(_gachaCharDebounce);
    _gachaCharDebounce = setTimeout(() => {
        const input = document.getElementById('agCharSearchInput');
        loadAdminGachaCharacters(input ? input.value.trim() : '');
    }, 300);
}

async function loadAdminGachaCharacters(search = '') {
    const tbody = document.getElementById('agCharactersTableBody');
    const datalist = document.getElementById('agCharDataList');

    try {
        const res = await apiRequest(`/api/gacha/characters?search=${encodeURIComponent(search)}&limit=50`);
        if (!res.ok) return;

        const chars = res.characters || [];
        state.gachaCharCache = chars;

        if (datalist && (!search || datalist.children.length === 0)) {
            datalist.innerHTML = chars.map(c => `
                <option value="${escapeHtml(c.name)} (ID: ${c.id})">${escapeHtml(c.name)} - ${escapeHtml(c.media_title||'')} (${c.rarity})</option>
            `).join('');
        }

        if (tbody) {
            if (!chars.length) {
                tbody.innerHTML = '<tr><td colspan="7" style="text-align:center;padding:20px;color:var(--text-dim);">Không tìm thấy nhân vật nào phù hợp.</td></tr>';
                return;
            }

            const rarityMap = {
                legendary: '<span class="badge" style="background:rgba(255,215,0,0.15);color:#ffd700;">Huyền Thoại</span>',
                epic: '<span class="badge" style="background:rgba(155,89,182,0.15);color:#9b59b6;">Sử Thi</span>',
                rare: '<span class="badge" style="background:rgba(52,152,219,0.15);color:#3498db;">Hiếm</span>',
                common: '<span class="badge" style="background:rgba(149,165,166,0.15);color:#95a5a6;">Thường</span>'
            };

            const burnPrices = { legendary: 500, epic: 150, rare: 50, common: 15 };

            tbody.innerHTML = chars.map(c => `
                <tr>
                    <td>${c.image_url ? `<img src="${c.image_url}" style="width:36px;height:48px;border-radius:4px;object-fit:cover;">` : '—'}</td>
                    <td><strong style="color:var(--text-main);">${escapeHtml(c.name)}</strong></td>
                    <td><span style="color:var(--text-dim);font-size:0.85rem;">${escapeHtml(c.native_name||'')}</span></td>
                    <td><span style="font-size:0.82rem;">${escapeHtml(c.media_title||'')}</span></td>
                    <td>${rarityMap[c.rarity] || c.rarity}</td>
                    <td><strong style="color:var(--sakura-pink);">💖 ${Number(c.favourites||0).toLocaleString()}</strong></td>
                    <td><span style="color:#ffd700;">${burnPrices[c.rarity]||15}🪙</span></td>
                </tr>
            `).join('');
        }
    } catch {}
}
