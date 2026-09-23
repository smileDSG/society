/* ============================================================
 * 象罔社团 · v3 交互脚本
 * 1) 滚动进度  2) 导航高亮/汉堡  3) 粒子网络  4) 光标聚光
 * 5) 卡片 3D 倾斜  6) 数字滚动  7) 打字机  8) 滚动浮现  9) 筛选
 * ============================================================ */
(function () {
  'use strict';
  // 尽早打标：CSS 只在 .js 存在时才隐藏内容，脚本挂了也不会白屏
  document.documentElement.classList.add('js');
  const $ = (s, r) => (r || document).querySelector(s);
  const $$ = (s, r) => Array.from((r || document).querySelectorAll(s));
  const reduced = window.matchMedia('(prefers-reduced-motion: reduce)').matches;

  /* ---------- 1. 滚动进度 ---------- */
  const prog = $('#prog');
  const nav = $('nav');
  const onScroll = () => {
    const h = document.documentElement;
    const p = h.scrollTop / (h.scrollHeight - h.clientHeight || 1);
    if (prog) prog.style.width = (p * 100).toFixed(2) + '%';
    if (nav) nav.classList.toggle('scrolled', h.scrollTop > 30);
    const tb = $('#top-btn');
    if (tb) tb.classList.toggle('show', h.scrollTop > 600);
  };
  window.addEventListener('scroll', onScroll, { passive: true });
  onScroll();

  /* ---------- 2. 导航 ---------- */
  const burger = $('.burger');
  const links = $('.nav-links');
  if (burger && links) {
    burger.addEventListener('click', () => links.classList.toggle('open'));
    links.addEventListener('click', e => { if (e.target.tagName === 'A') links.classList.remove('open'); });
  }

  const secIds = $$('.nav-links a[href^="#"]').map(a => a.getAttribute('href').slice(1)).filter(Boolean);
  if (secIds.length && 'IntersectionObserver' in window) {
    const map = new Map(secIds.map(id => [id, $(`.nav-links a[href="#${id}"]`)]));
    const io = new IntersectionObserver(entries => {
      entries.forEach(e => {
        if (e.isIntersecting) {
          $$('.nav-links a').forEach(a => a.classList.remove('on'));
          const a = map.get(e.target.id);
          if (a) a.classList.add('on');
        }
      });
    }, { rootMargin: '-45% 0px -50% 0px' });
    secIds.forEach(id => { const el = document.getElementById(id); if (el) io.observe(el); });
  }

  /* ---------- 3. 粒子网络（Hero 背景） ---------- */
  const cv = $('#net');
  if (cv && !reduced) {
    const ctx = cv.getContext('2d');
    let w = 0, h = 0, dpr = Math.min(window.devicePixelRatio || 1, 2);
    let pts = [];
    const mouse = { x: -9999, y: -9999 };
    const resize = () => {
      const r = cv.parentElement.getBoundingClientRect();
      w = r.width; h = r.height;
      cv.width = w * dpr; cv.height = h * dpr;
      ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
      const n = Math.min(78, Math.round(w * h / 15000));
      pts = Array.from({ length: n }, () => ({
        x: Math.random() * w, y: Math.random() * h,
        vx: (Math.random() - .5) * .28, vy: (Math.random() - .5) * .28,
        r: Math.random() * 1.6 + .7
      }));
    };
    const draw = () => {
      ctx.clearRect(0, 0, w, h);
      for (let i = 0; i < pts.length; i++) {
        const p = pts[i];
        p.x += p.vx; p.y += p.vy;
        if (p.x < 0 || p.x > w) p.vx *= -1;
        if (p.y < 0 || p.y > h) p.vy *= -1;
        ctx.beginPath();
        ctx.arc(p.x, p.y, p.r, 0, Math.PI * 2);
        ctx.fillStyle = 'rgba(160,220,255,.75)';
        ctx.fill();
        for (let j = i + 1; j < pts.length; j++) {
          const q = pts[j];
          const dx = p.x - q.x, dy = p.y - q.y;
          const d = Math.hypot(dx, dy);
          if (d < 132) {
            ctx.beginPath();
            ctx.moveTo(p.x, p.y); ctx.lineTo(q.x, q.y);
            ctx.strokeStyle = `rgba(90,190,255,${(1 - d / 132) * .32})`;
            ctx.lineWidth = 1;
            ctx.stroke();
          }
        }
        const md = Math.hypot(p.x - mouse.x, p.y - mouse.y);
        if (md < 155) {
          ctx.beginPath();
          ctx.moveTo(p.x, p.y); ctx.lineTo(mouse.x, mouse.y);
          ctx.strokeStyle = `rgba(53,230,255,${(1 - md / 155) * .55})`;
          ctx.lineWidth = 1.1;
          ctx.stroke();
        }
      }
      requestAnimationFrame(draw);
    };
    resize();
    window.addEventListener('resize', resize);
    const host = cv.parentElement;
    host.addEventListener('mousemove', e => {
      const r = host.getBoundingClientRect();
      mouse.x = e.clientX - r.left; mouse.y = e.clientY - r.top;
    });
    host.addEventListener('mouseleave', () => { mouse.x = mouse.y = -9999; });
    requestAnimationFrame(draw);
  }

  /* ---------- 4. 光标聚光 ---------- */
  $$('.spot').forEach(el => {
    el.addEventListener('mousemove', e => {
      const r = el.getBoundingClientRect();
      el.style.setProperty('--mx', (e.clientX - r.left) + 'px');
      el.style.setProperty('--my', (e.clientY - r.top) + 'px');
    });
  });

  /* ---------- 5. 卡片 3D 倾斜 ---------- */
  if (!reduced && window.matchMedia('(hover:hover)').matches) {
    $$('.tilt').forEach(el => {
      const inner = el.querySelector('.beam-in') || el.firstElementChild || el;
      el.addEventListener('mousemove', e => {
        const r = el.getBoundingClientRect();
        const x = (e.clientX - r.left) / r.width - .5;
        const y = (e.clientY - r.top) / r.height - .5;
        inner.style.transform = `perspective(900px) rotateX(${(-y * 5).toFixed(2)}deg) rotateY(${(x * 6).toFixed(2)}deg) translateZ(0)`;
      });
      el.addEventListener('mouseleave', () => { inner.style.transform = ''; });
    });
  }

  /* ---------- 6. 数字滚动 ---------- */
  const countUp = el => {
    const target = parseFloat(el.dataset.count);
    const suffix = el.dataset.suffix || '';
    if (reduced) { el.textContent = target + suffix; return; }
    const dur = 1200, t0 = performance.now();
    const step = now => {
      const p = Math.min((now - t0) / dur, 1);
      const e = 1 - Math.pow(1 - p, 3);
      el.textContent = Math.round(target * e) + suffix;
      if (p < 1) requestAnimationFrame(step);
    };
    requestAnimationFrame(step);
  };

  /* ---------- 7. 打字机 ---------- */
  const typer = $('[data-typer]');
  if (typer && !reduced) {
    const words = typer.dataset.typer.split('|');
    let wi = 0, ci = 0, del = false;
    const out = typer.querySelector('.tw');
    const tick = () => {
      const w = words[wi];
      if (!del) {
        out.textContent = w.slice(0, ++ci);
        if (ci === w.length) { del = true; return setTimeout(tick, 1700); }
      } else {
        out.textContent = w.slice(0, --ci);
        if (ci === 0) { del = false; wi = (wi + 1) % words.length; }
      }
      setTimeout(tick, del ? 42 : 92);
    };
    tick();
  }

  /* ---------- 8. 滚动浮现 ---------- */
  if ('IntersectionObserver' in window) {
    const io = new IntersectionObserver(es => {
      es.forEach(e => {
        if (e.isIntersecting) {
          e.target.classList.add('in');
          $$('[data-count]', e.target).forEach(countUp);
          io.unobserve(e.target);
        }
      });
    }, { threshold: .12, rootMargin: '0px 0px -8% 0px' });
    $$('.rv').forEach(el => io.observe(el));
    $$('[data-count]').forEach(el => { if (!el.closest('.rv')) countUp(el); });
  } else {
    $$('.rv').forEach(el => el.classList.add('in'));
  }

  /* ---------- 9. 列表页筛选 ---------- */
  const fbar = $('.filters');
  if (fbar) {
    const items = $$('[data-cat]');
    fbar.addEventListener('click', e => {
      const b = e.target.closest('button');
      if (!b) return;
      $$('button', fbar).forEach(x => x.classList.remove('on'));
      b.classList.add('on');
      const v = b.dataset.f;
      items.forEach(it => {
        it.style.display = (v === 'all' || it.dataset.cat === v) ? '' : 'none';
      });
    });
  }

  /* ---------- 回到顶部 ---------- */
  const tb = $('#top-btn');
  if (tb) tb.addEventListener('click', () => window.scrollTo({ top: 0, behavior: 'smooth' }));

  /* ---------- 终端卡逐行浮现 ---------- */
  $$('.term-body .ln').forEach((el, i) => { el.style.animationDelay = (0.25 + i * 0.12) + 's'; });

  /* ---------- 10. 自定义光标 + 磁吸按钮 ---------- */
  const fine = window.matchMedia('(hover:hover) and (pointer:fine)').matches;
  if (fine && !reduced) {
    const dot = document.createElement('span');
    const ring = document.createElement('span');
    dot.className = 'cur-dot'; ring.className = 'cur-ring';
    document.body.appendChild(dot); document.body.appendChild(ring);
    document.body.classList.add('cur-hide');
    let mx = -100, my = -100, rx = -100, ry = -100, ready = false;
    const paint = (el, x, y) => { el.style.transform = 'translate3d(' + x + 'px,' + y + 'px,0) translate(-50%,-50%)'; };
    paint(dot, mx, my); paint(ring, rx, ry);
    dot.style.opacity = ring.style.opacity = '0';
    addEventListener('mousemove', e => {
      if (!ready) { ready = true; dot.style.opacity = ring.style.opacity = '1'; rx = e.clientX; ry = e.clientY; }
      mx = e.clientX; my = e.clientY;
      paint(dot, mx, my);
    });
    (function loop() {
      rx += (mx - rx) * .16; ry += (my - ry) * .16;
      paint(ring, rx, ry);
      requestAnimationFrame(loop);
    })();
    document.addEventListener('mouseover', e => {
      ring.classList.toggle('big', !!e.target.closest('a,button,.btn,.nav-cta'));
    });
    addEventListener('mouseleave', () => { dot.style.opacity = ring.style.opacity = '0'; });
    addEventListener('mouseenter', () => { dot.style.opacity = ring.style.opacity = '1'; });

    $$('.btn, .nav-cta').forEach(el => {
      el.addEventListener('mousemove', e => {
        const r = el.getBoundingClientRect();
        const x = (e.clientX - r.left) / r.width - .5;
        const y = (e.clientY - r.top) / r.height - .5;
        el.style.transform = 'translate(' + (x * 16).toFixed(1) + 'px,' + (y * 12).toFixed(1) + 'px)';
      });
      el.addEventListener('mouseleave', () => { el.style.transform = ''; });
    });
  }

  /* ---------- 11. 导航滑动药丸 ---------- */
  const navUl = $('.nav-links');
  if (navUl) {
    const pill = document.createElement('i');
    pill.className = 'nav-pill';
    navUl.appendChild(pill);
    const move = el => {
      if (!el) { pill.style.opacity = '0'; return; }
      const p = el.getBoundingClientRect(), b = navUl.getBoundingClientRect();
      pill.style.width = p.width + 'px';
      pill.style.transform = 'translateX(' + (p.left - b.left) + 'px)';
      pill.style.opacity = '1';
    };
    $$('a', navUl).forEach(a => {
      a.addEventListener('mouseenter', () => move(a));
      a.addEventListener('focus', () => move(a));
    });
    navUl.addEventListener('mouseleave', () => move($('.nav-links a.on')));
    const sync = () => { if (!navUl.matches(':hover')) move($('.nav-links a.on')); };
    new MutationObserver(sync).observe(navUl, { subtree: true, attributes: true, attributeFilter: ['class'] });
    addEventListener('resize', sync);
    setTimeout(sync, 150);
  }

  /* ---------- 12. 首屏标题悬停乱码 ---------- */
  const h1 = $('.hero h1');
  if (h1 && !reduced) {
    const pool = '01<>/{}[]#$%&*+=_ABCDEFGHJKLMNPQRSTUVWXYZ象罔写代码做东西';
    const spans = $$('.w', h1);
    const orig = spans.map(s => s.textContent);
    let raf = null;
    h1.addEventListener('mouseenter', () => {
      cancelAnimationFrame(raf);
      let frame = 0;
      const total = spans.length * 2 + 12;
      const step = () => {
        spans.forEach((s, i) => {
          const start = i * 2;
          if (frame < start) return;
          if (frame < start + 7 && Math.random() < .55) {
            s.textContent = pool[(Math.random() * pool.length) | 0];
          } else {
            s.textContent = orig[i];
          }
        });
        if (++frame < total) raf = requestAnimationFrame(step);
        else spans.forEach((s, i) => { s.textContent = orig[i]; });
      };
      step();
    });
  }

  /* ---------- 外部链接安全 ---------- */
  $$('a[target="_blank"]').forEach(a => {
    if (!/rel=/.test(a.outerHTML)) a.setAttribute('rel', 'noopener');
  });

  /* ============================================================
   * 迷你终端（Hero 右侧）—— 敲命令认识象罔
   * 演出数据来自同一份 build 数据，这里做演示用，写死不求同步
   * ============================================================ */
  const term = $('[data-term]');
  if (term) {
    const out = term.querySelector('[data-term-out]');
    const input = term.querySelector('[data-term-in]');
    const CMD_MAP = {
      help: [
        ['可用命令', 'c'],
        ['  help      显示这份帮助', 'dim'],
        ['  who       象罔是谁', 'dim'],
        ['  projects  我们在做什么', 'dim'],
        ['  stack     用些什么技术', 'dim'],
        ['  join      查怎么加入', 'dim'],
        ['  clear     清屏', 'dim'],
      ],
      who: [
        ['象罔 · XIANGWANG', 'hl'],
        ['出处：《庄子·天地》「象罔得珠」——', 'dim'],
        ['无心而求，反而得之。', 'dim'],
        ['我们是一群在动手折腾中撞见好东西的计算机社团。', 'dim'],
      ],
      projects: [
        ['当前在研', 'hl'],
        ['  OpenClaw       智能体底座（研究）', 'dim'],
        ['  科研智能体     想法 → 可投稿论文（旗舰）', 'dim'],
        ['  教育智能体     备课 / 批改 / 答疑', 'dim'],
        ['  专利智能体     专利与文献检索', 'dim'],
        ['  官网          其实就是你现在在的这个站点', 'ok'],
      ],
      stack: [
        ['语言 / 框架', 'hl'],
        ['  Python · TypeScript · FastAPI · Vue 3', 'dim'],
        ['方向', 'hl'],
        ['  Web 全栈 · LLM / RAG · Agent · 科研 Harness', 'dim'],
      ],
      join: [
        ['欢迎加入象罔！', 'hl'],
        ['  面向全校 · 不限专业 · 零基础可入', 'ok'],
        ['向下滚动到「招新」区，或直接点按钮报名 →', 'dim'],
      ],
      ls: [['正在列出 ~/xiangwang …', 'dim'], ['  ideas/    代码/    demo/   docs/', 'ok'],
        ['（放轻松，这只是个小彩蛋）', 'c']],
      sudo: [['你胆子不小 😏 这里没有 sudo，只有动手做。', 'warn']],
      sysinfo: [['象罔 OS  v2026', 'ok'], ['内核：知索不得，象罔得之', 'dim'],
        ['运行时长：每周都在发生', 'dim']],
      github: [['github.com/xiangwang-club', 'ok'], ['所有自研项目均开源。', 'dim']],
      '❓': [],
    };

    const banner = [
      ['象罔@club 交互终端 v1.0', 'hl'],
      ['在这里敲几个字，它不会咬你。', 'c'],
      ['输入 help 查看命令，开始了解我们 ↓', 'c'],
    ];

    const printLine = (text, cls) => {
      const d = document.createElement('div');
      d.className = 'clit-line ' + (cls || '');
      d.textContent = text;
      out.appendChild(d);
      out.scrollTop = out.scrollHeight;
      return d;
    };
    const boot = () => banner.forEach(([t, c]) => printLine(t, c));

    const run = raw => {
      const v = (raw || '').trim().split(/\s+/);
      const name = (v[0] || '').toLowerCase();
      printLine('$ ' + raw, '');
      let cc;
      if (!name) cc = [['（空输入也要有回应？输入 help 试试）', 'c']];
      else if (name === 'clear') { out.innerHTML = ''; return; }
      else if (name in CMD_MAP) cc = CMD_MAP[name];
      else cc = [['未识别的命令: ' + name + '  —— 输入 help 看看有哪些。', 'warn']];
      cc.forEach(([t, c]) => printLine(t, c));
    };

    boot();
    input.addEventListener('keydown', e => {
      if (e.key === 'Enter') { run(input.value); input.value = ''; }
    });
    input.addEventListener('mouseenter', () => input.focus());
  }
})();
