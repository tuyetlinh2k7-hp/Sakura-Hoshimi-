/**
 * 🌸 SAKURA BOT - VISUAL EFFECTS & THEME ENGINE
 * Includes:
 * 1. Falling Sakura Petals Particle Canvas
 * 2. Swaying Cherry Blossom Branches (SVG Decor)
 * 3. Animated Bot Avatar Helper
 * 4. Light / Dark Mode Theme Manager with Persistence
 */

(function () {
  'use strict';

  /* =========================================================
     1. THEME MANAGER (Light & Dark Mode)
     ========================================================= */
  const THEME_KEY = 'sakura_theme';

  function getPreferredTheme() {
    const saved = localStorage.getItem(THEME_KEY);
    if (saved === 'light' || saved === 'dark') return saved;
    // Default to dark mode (standard for gaming/discord bot aesthetic)
    return 'dark';
  }

  function applyTheme(theme, animate = false) {
    if (animate) {
      document.documentElement.classList.add('theme-transitioning');
      setTimeout(() => {
        document.documentElement.classList.remove('theme-transitioning');
      }, 400);
    }
    document.documentElement.setAttribute('data-theme', theme);
    localStorage.setItem(THEME_KEY, theme);

    // Update all theme toggle buttons on the page (emoji only)
    document.querySelectorAll('.theme-toggle-btn').forEach(btn => {
      const isDark = theme === 'dark';
      btn.setAttribute('aria-label', isDark ? 'Chuyển sang chế độ sáng' : 'Chuyển sang chế độ tối');
      btn.setAttribute('title', isDark ? 'Chế độ sáng (Light mode)' : 'Chế độ tối (Dark mode)');

      const iconEl = btn.querySelector('.theme-icon') || btn;
      if (iconEl) {
        iconEl.innerHTML = isDark
          ? '<span class="theme-icon-moon">🌙</span>'
          : '<span class="theme-icon-sun">☀️</span>';
      }

      const textEl = btn.querySelector('.theme-text');
      if (textEl) {
        textEl.remove();
      }
    });

    // Notify listeners
    window.dispatchEvent(new CustomEvent('sakuraThemeChange', { detail: { theme } }));
  }

  function toggleTheme() {
    const current = document.documentElement.getAttribute('data-theme') || 'dark';
    const next = current === 'dark' ? 'light' : 'dark';
    applyTheme(next, true);

    if (window.showToast) {
      const isDark = next === 'dark';
      let msg = isDark ? '🌙 Đã chuyển sang Giao diện Tối' : '☀️ Đã chuyển sang Giao diện Sáng (Sakura Pastel)';
      if (window.sakuraT) {
        const lang = window.getSakuraLanguage ? window.getSakuraLanguage() : 'vi';
        if (lang === 'en') {
          msg = isDark ? '🌙 Switched to Dark Theme' : '☀️ Switched to Light Theme (Sakura Pastel)';
        } else if (lang === 'ja') {
          msg = isDark ? '🌙 ダークモードに切り替えました' : '☀️ ライトモードに切り替えました';
        }
      }
      window.showToast(msg, 'info');
    }
  }

  // Expose global methods
  window.toggleSakuraTheme = toggleTheme;
  window.setSakuraTheme = applyTheme;

  // Apply immediately to avoid FOUC
  const initialTheme = getPreferredTheme();
  document.documentElement.setAttribute('data-theme', initialTheme);

  // Auto load i18n engine if missing
  if (!window.sakuraT && !document.querySelector('script[src*="i18n.js"]')) {
    const s = document.createElement('script');
    s.src = '/static/js/i18n.js';
    s.async = false;
    document.head.appendChild(s);
  }

  /* =========================================================
     2. SWAYING SAKURA BRANCHES (IMAGE ASSET)
     ========================================================= */
  function createSakuraBranchImage() {
    const img = document.createElement('img');
    img.src = '/images/sakura-branch.png';
    img.alt = 'Cherry blossom branch';
    img.className = 'sakura-branch-image';
    img.draggable = false;
    img.style.transform = 'rotate(-90deg)';
    return img.outerHTML;
  }

  function initSakuraBranches() {
    if (document.querySelector('.sakura-branch-container')) return;

    const container = document.createElement('div');
    container.className = 'sakura-branch-container';
    container.setAttribute('aria-hidden', 'true');

    const leftBranch = document.createElement('div');
    leftBranch.className = 'sakura-branch-decor branch-top-left';
    leftBranch.innerHTML = createSakuraBranchImage();

    container.appendChild(leftBranch);
    document.body.appendChild(container);
  }

  /* =========================================================
     3. FALLING SAKURA PETALS PARTICLE CANVAS
     ========================================================= */
  class SakuraPetalsCanvas {
    constructor() {
      this.canvas = null;
      this.ctx = null;
      this.petals = [];
      this.trailPetals = [];
      this.burstPetals = [];
      this.sparkles = [];
      this.maxPetals = 32;
      this.maxTrailPetals = 45;
      this.width = window.innerWidth;
      this.height = window.innerHeight;
      this.mouseX = 0;
      this.mouseY = 0;
      this.lastTrailX = 0;
      this.lastTrailY = 0;
      this.lastTrailTime = 0;
      this.lastBurstTime = 0;
      this.windForce = 0;
      this.targetWindForce = 0;
      this.animId = null;
      this.isRunning = false;
      this.init();
    }

    init() {
      if (document.getElementById('sakuraCanvas')) return;

      this.canvas = document.createElement('canvas');
      this.canvas.id = 'sakuraCanvas';
      this.canvas.className = 'sakura-petals-canvas';
      this.canvas.setAttribute('aria-hidden', 'true');
      document.body.appendChild(this.canvas);
      this.ctx = this.canvas.getContext('2d');

      this.resize();
      this.createPetals();
      this.bindEvents();
      this.start();
    }

    resize() {
      this.width = window.innerWidth;
      this.height = window.innerHeight;
      if (this.canvas) {
        this.canvas.width = this.width;
        this.canvas.height = this.height;
      }
    }

    createPetals() {
      this.petals = [];
      // Adjust petal count based on screen size (fewer on mobile for max performance)
      const count = this.width < 768 ? 16 : this.maxPetals;
      for (let i = 0; i < count; i++) {
        this.petals.push(this.newPetal(Math.random() * this.width, Math.random() * this.height));
      }
    }

    newPetal(x = null, y = null) {
      const size = Math.random() * 9 + 8; // 8 to 17px
      return {
        x: x !== null ? x : Math.random() * (this.width + 100) - 50,
        y: y !== null ? y : -20 - Math.random() * 50,
        size: size,
        speedX: Math.random() * 1.5 + 0.8,
        speedY: Math.random() * 1.2 + 0.8,
        flip: Math.random() * Math.PI,
        flipSpeed: Math.random() * 0.03 + 0.015,
        angle: Math.random() * Math.PI * 2,
        angleSpeed: (Math.random() - 0.5) * 0.02,
        opacity: Math.random() * 0.45 + 0.55,
        colorType: Math.floor(Math.random() * 3), // 0: soft pink, 1: vibrant pink, 2: white-pink
        swayPhase: Math.random() * Math.PI * 2,
        swaySpeed: Math.random() * 0.02 + 0.01
      };
    }

    spawnTrailPetal(x, y) {
      const now = performance.now();
      const dist = Math.hypot(x - this.lastTrailX, y - this.lastTrailY);
      if (dist < 14 && now - this.lastTrailTime < 45) return;
      this.lastTrailX = x;
      this.lastTrailY = y;
      this.lastTrailTime = now;

      if (this.trailPetals.length >= this.maxTrailPetals) {
        this.trailPetals.shift();
      }

      const count = Math.random() > 0.4 ? 2 : 1;
      for (let i = 0; i < count; i++) {
        const angle = Math.random() * Math.PI * 2;
        const speed = Math.random() * 1.2 + 0.4;
        this.trailPetals.push({
          x: x + (Math.random() - 0.5) * 12,
          y: y + (Math.random() - 0.5) * 12,
          size: Math.random() * 6 + 7, // 7-13px
          speedX: Math.cos(angle) * speed + (Math.random() - 0.5) * 0.6,
          speedY: Math.sin(angle) * speed + 0.8, // gentle fall
          flip: Math.random() * Math.PI,
          flipSpeed: Math.random() * 0.04 + 0.02,
          angle: Math.random() * Math.PI * 2,
          angleSpeed: (Math.random() - 0.5) * 0.04,
          opacity: Math.random() * 0.3 + 0.7,
          fadeSpeed: Math.random() * 0.018 + 0.012,
          colorType: Math.floor(Math.random() * 3)
        });
      }
    }

    spawnBurst(x, y) {
      const now = performance.now();
      if (now - this.lastBurstTime < 80) return; // Debounce rapid spam
      this.lastBurstTime = now;

      const petalCount = this.width < 768 ? 12 : 18;
      for (let i = 0; i < petalCount; i++) {
        const angle = (i / petalCount) * Math.PI * 2 + (Math.random() - 0.5) * 0.6;
        const speed = Math.random() * 4.5 + 2.5;
        this.burstPetals.push({
          x: x,
          y: y,
          size: Math.random() * 8 + 8, // 8-16px
          speedX: Math.cos(angle) * speed,
          speedY: Math.sin(angle) * speed - 1.8, // explosive initial upward lift
          gravity: 0.12,
          friction: 0.94,
          flip: Math.random() * Math.PI,
          flipSpeed: Math.random() * 0.08 + 0.03,
          angle: Math.random() * Math.PI * 2,
          angleSpeed: (Math.random() - 0.5) * 0.08,
          opacity: 1.0,
          fadeSpeed: Math.random() * 0.018 + 0.012,
          colorType: Math.floor(Math.random() * 3)
        });
      }

      // Add sparkling glowing blossom dust
      const sparkleCount = this.width < 768 ? 6 : 10;
      for (let i = 0; i < sparkleCount; i++) {
        const sAngle = Math.random() * Math.PI * 2;
        const sSpeed = Math.random() * 5.0 + 1.5;
        this.sparkles.push({
          x: x,
          y: y,
          vx: Math.cos(sAngle) * sSpeed,
          vy: Math.sin(sAngle) * sSpeed - 1.0,
          radius: Math.random() * 2.2 + 1.2,
          opacity: 1.0,
          color: Math.random() > 0.4 ? '#ff79c6' : '#ffffff'
        });
      }
    }

    bindEvents() {
      window.addEventListener('resize', () => this.resize(), { passive: true });

      // Cursor trail on mouse move
      window.addEventListener('mousemove', (e) => {
        const deltaX = (e.clientX - (this.mouseX || e.clientX)) * 0.05;
        this.targetWindForce = Math.max(-2, Math.min(3, deltaX));
        this.mouseX = e.clientX;
        this.mouseY = e.clientY;
        this.spawnTrailPetal(e.clientX, e.clientY);
      }, { passive: true });

      // Finger trail and swipe on mobile touch
      window.addEventListener('touchmove', (e) => {
        if (e.touches && e.touches[0]) {
          const t = e.touches[0];
          this.spawnTrailPetal(t.clientX, t.clientY);
        }
      }, { passive: true });

      // Flower petal burst on click / tap (works on both PC click & phone tap)
      window.addEventListener('pointerdown', (e) => {
        // e.clientX & e.clientY are supported across mouse, touch, and pen
        this.spawnBurst(e.clientX, e.clientY);
      }, { passive: true });

      // Pause when page is hidden
      document.addEventListener('visibilitychange', () => {
        if (document.hidden) {
          this.stop();
        } else {
          this.start();
        }
      });
    }

    drawPetal(petal) {
      const ctx = this.ctx;
      ctx.save();
      ctx.translate(petal.x, petal.y);
      ctx.rotate(petal.angle);
      // 3D flip effect
      ctx.scale(Math.cos(petal.flip), 1);
      ctx.globalAlpha = Math.max(0, petal.opacity);

      // Color gradients
      const r = petal.size;
      const grad = ctx.createLinearGradient(-r / 2, -r / 2, r / 2, r / 2);
      if (petal.colorType === 0) {
        grad.addColorStop(0, '#ffffff');
        grad.addColorStop(0.4, '#ffc2e2');
        grad.addColorStop(1, '#ff79c6');
      } else if (petal.colorType === 1) {
        grad.addColorStop(0, '#fff0f5');
        grad.addColorStop(0.5, '#ff94c2');
        grad.addColorStop(1, '#ff2a85');
      } else {
        grad.addColorStop(0, '#ffffff');
        grad.addColorStop(0.6, '#ffe4f0');
        grad.addColorStop(1, '#ffb6c1');
      }

      ctx.fillStyle = grad;
      ctx.shadowColor = 'rgba(255, 121, 198, 0.4)';
      ctx.shadowBlur = 4;

      // Draw elegant cherry petal shape (curved heart/teardrop notch)
      ctx.beginPath();
      ctx.moveTo(0, -r);
      ctx.bezierCurveTo(r * 0.8, -r * 0.9, r * 1.1, -r * 0.1, r * 0.5, r * 0.8);
      ctx.bezierCurveTo(r * 0.2, r * 1.0, -r * 0.2, r * 1.0, -r * 0.5, r * 0.8);
      ctx.bezierCurveTo(-r * 1.1, -r * 0.1, -r * 0.8, -r * 0.9, 0, -r);
      ctx.closePath();
      ctx.fill();

      ctx.restore();
    }

    update() {
      // Wind smoothing
      this.windForce += (this.targetWindForce - this.windForce) * 0.05;
      this.targetWindForce *= 0.96;

      // Background ambient falling petals
      const len = this.petals.length;
      for (let i = 0; i < len; i++) {
        const p = this.petals[i];
        p.swayPhase += p.swaySpeed;
        const sway = Math.sin(p.swayPhase) * 1.2;

        p.x += p.speedX + sway + this.windForce;
        p.y += p.speedY;
        p.flip += p.flipSpeed;
        p.angle += p.angleSpeed;

        // Reset if off-screen
        if (p.y > this.height + 30 || p.x > this.width + 50 || p.x < -60) {
          this.petals[i] = this.newPetal(Math.random() * (this.width + 60) - 30, -20);
        }
      }

      // Cursor trail petals update
      for (let i = this.trailPetals.length - 1; i >= 0; i--) {
        const p = this.trailPetals[i];
        p.x += p.speedX;
        p.y += p.speedY;
        p.flip += p.flipSpeed;
        p.angle += p.angleSpeed;
        p.opacity -= p.fadeSpeed;
        if (p.opacity <= 0 || p.y > this.height + 25) {
          this.trailPetals.splice(i, 1);
        }
      }

      // Click / tap burst petals update
      for (let i = this.burstPetals.length - 1; i >= 0; i--) {
        const p = this.burstPetals[i];
        p.x += p.speedX;
        p.y += p.speedY;
        p.speedY += p.gravity;
        p.speedX *= p.friction;
        p.speedY *= p.friction;
        p.flip += p.flipSpeed;
        p.angle += p.angleSpeed;
        p.opacity -= p.fadeSpeed;
        if (p.opacity <= 0 || p.y > this.height + 30) {
          this.burstPetals.splice(i, 1);
        }
      }

      // Sparkles update
      for (let i = this.sparkles.length - 1; i >= 0; i--) {
        const s = this.sparkles[i];
        s.x += s.vx;
        s.y += s.vy;
        s.vx *= 0.92;
        s.vy *= 0.92;
        s.opacity -= 0.035;
        if (s.opacity <= 0) {
          this.sparkles.splice(i, 1);
        }
      }
    }

    render() {
      if (!this.ctx) return;
      this.ctx.clearRect(0, 0, this.width, this.height);

      // 1. Falling ambient petals
      const len = this.petals.length;
      for (let i = 0; i < len; i++) {
        this.drawPetal(this.petals[i]);
      }

      // 2. Cursor/touch trail petals
      for (let i = 0; i < this.trailPetals.length; i++) {
        this.drawPetal(this.trailPetals[i]);
      }

      // 3. Click/tap burst petals
      for (let i = 0; i < this.burstPetals.length; i++) {
        this.drawPetal(this.burstPetals[i]);
      }

      // 4. Burst sparkling dust
      for (let i = 0; i < this.sparkles.length; i++) {
        const s = this.sparkles[i];
        this.ctx.save();
        this.ctx.globalAlpha = Math.max(0, s.opacity);
        this.ctx.fillStyle = s.color;
        this.ctx.shadowColor = '#ff79c6';
        this.ctx.shadowBlur = 6;
        this.ctx.beginPath();
        this.ctx.arc(s.x, s.y, s.radius, 0, Math.PI * 2);
        this.ctx.fill();
        this.ctx.restore();
      }
    }

    loop() {
      if (!this.isRunning) return;
      this.update();
      this.render();
      this.animId = requestAnimationFrame(() => this.loop());
    }

    start() {
      if (this.isRunning) return;
      this.isRunning = true;
      this.loop();
    }

    stop() {
      this.isRunning = false;
      if (this.animId) cancelAnimationFrame(this.animId);
    }
  }

  /* =========================================================
     4. BOT AVATAR ANIMATION ENHANCER
     ========================================================= */
  function enhanceBotAvatars() {
    const avatarSelectors = [
      '.brand-logo',
      '.hero-card img',
      '.landing-logo',
      '#accAvatar',
      '.avatar-bot',
      '.bot-avatar'
    ];

    avatarSelectors.forEach(sel => {
      document.querySelectorAll(sel).forEach(img => {
        if (!img.classList.contains('bot-avatar-animated')) {
          img.classList.add('bot-avatar-animated');

          // Wrap in glowing aura container if parent is not already aura
          const parent = img.parentElement;
          if (parent && !parent.classList.contains('avatar-aura-wrapper')) {
            parent.classList.add('avatar-aura-wrapper');
          }
        }
      });
    });
  }

  /* =========================================================
     5. INITIALIZATION
     ========================================================= */
  function init() {
    // 1. Apply theme
    applyTheme(getPreferredTheme());

    // 2. Initialize swaying branches
    initSakuraBranches();

    // 3. Initialize falling petals
    window.sakuraPetalsEngine = new SakuraPetalsCanvas();

    // 4. Enhance avatars
    enhanceBotAvatars();

    // 5. Setup theme toggle buttons
    document.querySelectorAll('.theme-toggle-btn').forEach(btn => {
      btn.addEventListener('click', (e) => {
        e.preventDefault();
        toggleTheme();
      });
    });
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }
  // Top marquee running text
  try{
    if(!localStorage.getItem('sakura_marquee_dismissed')){
      const bar=document.createElement('div');
      bar.className='sakura-marquee'; bar.id='sakuraMarquee';
      const track=document.createElement('div'); track.className='sakura-marquee-track';
      const items=[
        '🌸 Sakura Bot — Hầu gái Yandere của bạn đã sẵn sàng!',
        '✨ Dùng s!help để xem lệnh • /dashboard để cấu hình server',
        '🎮 TikTok Auto Download • Level & Economy • AutoMod đã bật',
        '💬 Global Chat giữa các tài khoản — bấm icon 💬 góc dưới để chat!',
        '🌸 Chào mừng đến với Sakura — chúc bạn một ngày tuyệt vời!'
      ];
      const row=items.map(t=>`<span class="sakura-marquee-item">${t}</span><span>•</span>`).join('');
      track.innerHTML=row+row; // duplicate for seamless
      const close=document.createElement('button'); close.className='sakura-marquee-close'; close.innerHTML='✕'; close.onclick=()=>{ bar.remove(); document.body.classList.remove('has-marquee'); localStorage.setItem('sakura_marquee_dismissed','1'); };
      bar.appendChild(track); bar.appendChild(close); document.body.prepend(bar); document.body.classList.add('has-marquee');
    }
  }catch(e){}
  // Auto-load floating chat widget (góc dưới)
  try{
    const s=document.createElement('script');
    s.src='/static/js/chat-widget.js'; s.async=true;
    document.head.appendChild(s);
  }catch(e){}

})();
