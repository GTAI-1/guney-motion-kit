// capcut-story-film: one engine for every motion-graphics layer that goes into the CapCut project.
// Each composition (written by scripts/layers.py) calls LT.boot(cfg). Time t is local to the layer (0 = its first frame);
// cfg.t0 is the layer's start on the NARRATION clock, so narration times convert with t = T - cfg.t0.
//   kind 'type'    : words that enter one at a time (blur to sharp), lines, kicker, typed labels, exit
//   kind 'snow'    : three depths of falling snow (+ fog gusts for a blizzard)
//   kind 'rain'    : slanted rain streaks in depth, splash glints near the bottom
//   kind 'embers'  : glowing embers / fireflies rising and drifting
//   kind 'dust'    : warm motes drifting in lamp light
//   kind 'sparks'  : brake sparks flying from the wheels
//   kind 'burn'    : film-burn light leak that covers a cut
//   kind 'oldfilm' : grain, flicker, scratches, specks, sepia wash and vignette for the flashback
//   kind 'plate'   : a picture with lights that live inside it (blinks, flashes, pulses), rendered at picture size
// Everything is a pure function of t (seeded randomness only), so any frame renders the same every time.
(function () {
  const clamp = (v, a = 0, b = 1) => Math.max(a, Math.min(b, v));
  const seg = (t, a, b) => (b <= a ? (t >= a ? 1 : 0) : clamp((t - a) / (b - a)));
  const outExpo = (u) => (u >= 1 ? 1 : 1 - Math.pow(2, -10 * u));
  const inOut = (u) => (u < 0.5 ? 4 * u * u * u : 1 - Math.pow(-2 * u + 2, 3) / 2);
  function rng(seed) { let a = seed >>> 0; return () => { a = (a + 0x6d2b79f5) | 0; let t = Math.imul(a ^ (a >>> 15), 1 | a); t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t; return ((t ^ (t >>> 14)) >>> 0) / 4294967296; }; }
  const hash = (i, j = 0) => { const r = rng((i * 73856093) ^ (j * 19349663) ^ 0x9e3779b9); r(); return r(); };

  // envelopes: number | {keys:[[t,v]..]} | {pulse:{period,duty,t0,t1,lo,hi,soft}} | {flashes:{times,hi,lo,attack,decay}}
  //            | {beat:{period,t0,t1,lo,hi}} (lub-dub) | {flicker:{lo,hi,rate,seed}} ; arrays multiply
  function env(spec, t) {
    if (spec == null) return 1;
    if (typeof spec === 'number') return spec;
    if (Array.isArray(spec)) return spec.reduce((m, s) => m * env(s, t), 1);
    if (spec.inv) return 1 - env(spec.inv, t);
    if (spec.max) return Math.max(...spec.max.map((s) => env(s, t)));
    if (spec.scale) return spec.scale * env(spec.of, t);
    if (spec.keys) { const k = spec.keys; if (t <= k[0][0]) return k[0][1]; for (let i = 1; i < k.length; i++) if (t <= k[i][0]) { const u = (t - k[i - 1][0]) / (k[i][0] - k[i - 1][0]); return k[i - 1][1] + (k[i][1] - k[i - 1][1]) * inOut(u); } return k[k.length - 1][1]; }
    if (spec.pulse) { const p = spec.pulse; if (t < (p.t0 ?? -1e9) || t > (p.t1 ?? 1e9)) return p.lo ?? 0;
      const ph = (((t - (p.t0 ?? 0)) / p.period) % 1 + 1) % 1, s = p.soft ?? 0.08, d = p.duty ?? 0.5;
      const on = ph < d ? Math.min(1, ph / s, (d - ph) / s) : 0; return (p.lo ?? 0) + ((p.hi ?? 1) - (p.lo ?? 0)) * clamp(on); }
    if (spec.flashes) { const f = spec.flashes; let v = f.lo ?? 0;
      for (const ft of f.times) { const d = t - ft; if (d > -(f.attack ?? 0.03) && d < 3) v = Math.max(v, d < 0 ? (f.hi ?? 1) * (1 + d / (f.attack ?? 0.03)) : (f.lo ?? 0) + ((f.hi ?? 1) - (f.lo ?? 0)) * Math.exp(-d / (f.decay ?? 0.15))); }
      return v; }
    if (spec.beat) { const b = spec.beat; if (t < (b.t0 ?? -1e9) || t > (b.t1 ?? 1e9)) return b.lo ?? 0; const ph = ((t - (b.t0 ?? 0)) / b.period) % 1;
      const k = Math.exp(-Math.pow((ph - 0.0) / 0.07, 2)) + 0.6 * Math.exp(-Math.pow((ph - 0.22) / 0.07, 2)); return (b.lo ?? 0) + ((b.hi ?? 1) - (b.lo ?? 0)) * clamp(k); }
    if (spec.flicker) { const f = spec.flicker, i = Math.floor(t * (f.rate ?? 12)), u = t * (f.rate ?? 12) - i;
      const a = hash(i, f.seed ?? 1), b = hash(i + 1, f.seed ?? 1); return (f.lo ?? 0.8) + ((f.hi ?? 1) - (f.lo ?? 0.8)) * (a + (b - a) * u); }
    return 1;
  }

  function canvas(root, w, h, z = 1) { const c = document.createElement('canvas'); c.width = w; c.height = h; Object.assign(c.style, { position: 'absolute', left: 0, top: 0, width: w + 'px', height: h + 'px', zIndex: z }); root.appendChild(c); return c; }
  function glow(ctx, x, y, r, rgb, a, core = 0.18) {
    core = Math.min(Math.max(core, 0.02), 0.45);   // a core past the 0.5 stop inverts the gradient into a ring
    if (a <= 0.002 || r <= 0) return; const g = ctx.createRadialGradient(x, y, 0, x, y, r);
    g.addColorStop(0, `rgba(${rgb},${a})`); g.addColorStop(core, `rgba(${rgb},${a * 0.55})`); g.addColorStop(0.5, `rgba(${rgb},${a * 0.16})`); g.addColorStop(1, `rgba(${rgb},0)`);
    ctx.fillStyle = g; ctx.fillRect(x - r, y - r, 2 * r, 2 * r); }
  function star(ctx, x, y, len, rgb, a, angles = [0, 90, 35, -35], thick = 3) {
    if (a <= 0.002) return;
    for (const ang of angles) { ctx.save(); ctx.translate(x, y); ctx.rotate(ang * Math.PI / 180); const L = ang % 90 === 0 ? len : len * 0.55;
      const g = ctx.createLinearGradient(-L, 0, L, 0); g.addColorStop(0, `rgba(${rgb},0)`); g.addColorStop(0.5, `rgba(${rgb},${a})`); g.addColorStop(1, `rgba(${rgb},0)`);
      ctx.fillStyle = g; ctx.fillRect(-L, -thick / 2, 2 * L, thick); ctx.restore(); } }

  // ---------------------------------------------------------------- type
  function buildType(root, cfg) {
    const W = cfg.w, H = cfg.h, items = [];
    if (cfg.backdrop) { const b = document.createElement('div'); b.className = 'lt-back'; b.style.background = cfg.backdrop; root.appendChild(b); items.push({ el: b, kind: 'back' }); }
    for (const ln of cfg.lines) {
      const row = document.createElement('div'); row.className = 'lt-row ' + (ln.cls || ''); row.style.top = ln.y + 'px'; root.appendChild(row);
      if (ln.typed) { const s = document.createElement('span'); s.className = 'lt-typed'; row.appendChild(s); const cur = document.createElement('i'); cur.className = 'lt-cur'; row.appendChild(cur);
        items.push({ kind: 'typed', el: s, cur, text: ln.typed, t: ln.t, cps: ln.cps || 22 }); continue; }
      for (const w of ln.words) { const s = document.createElement('span'); s.className = 'lt-word'; s.textContent = w.text; row.appendChild(s);
        items.push({ kind: 'word', el: s, t: w.t, style: ln.style || 'rise', flash: w.flash }); }
    }
    // fit every row inside the safe width (mobile-first: big, but never past the frame); measured once the fonts are in
    const fit = () => { for (const row of root.querySelectorAll('.lt-row')) { const max = cfg.maxw || W - 240, wpx = row.offsetWidth; row.style.transform = wpx > max ? `translateX(-50%) scale(${(max / wpx).toFixed(4)})` : 'translateX(-50%)'; } };
    return (t) => {
      fit();
      const out = cfg.out != null ? inOut(seg(t, cfg.out, cfg.out + (cfg.outDur || 0.45))) : 0;
      for (const it of items) {
        if (it.kind === 'back') { it.el.style.opacity = (Math.min(seg(t, cfg.backIn ?? 0, (cfg.backIn ?? 0) + 0.5), 1 - out)).toFixed(3); continue; }
        if (it.kind === 'typed') { const n = Math.max(0, Math.min(it.text.length, Math.floor((t - it.t) * it.cps) + 1)); it.el.textContent = t >= it.t ? it.text.slice(0, n) : '';
          it.cur.style.opacity = t >= it.t - 0.4 && out < 0.5 && (n < it.text.length || Math.floor(t * 2.2) % 2 === 0) ? 1 : 0; it.el.parentNode.style.opacity = (1 - out).toFixed(3); continue; }
        const u = seg(t, it.t - 0.02, it.t + (it.style === 'stamp' ? 0.26 : 0.6)), e = outExpo(u), vis = t >= it.t - 0.02 ? 1 : 0;
        let tf, blur, ls;
        if (it.style === 'stamp') { tf = `scale(${(1.22 - 0.22 * e).toFixed(4)})`; blur = 9 * (1 - e); }
        else { tf = `translateY(${(26 * (1 - e) - 14 * out).toFixed(2)}px)`; blur = 14 * (1 - e); }
        blur += 10 * out;
        it.el.style.opacity = (vis * Math.min(1, e * 1.4) * (1 - out)).toFixed(3);
        it.el.style.transform = tf; it.el.style.filter = blur > 0.05 ? `blur(${blur.toFixed(2)}px)` : 'none';
        if (it.flash) { const f = Math.exp(-Math.max(0, t - it.t) / 0.35) * vis; it.el.style.textShadow = `0 0 ${(30 + 70 * f).toFixed(1)}px rgba(${cfg.glow},${(0.55 + 0.45 * f).toFixed(3)}), 0 0 ${(6 + 20 * f).toFixed(1)}px rgba(255,255,255,${(0.4 + 0.6 * f).toFixed(3)})`; }
      }
    };
  }

  // ---------------------------------------------------------------- particles
  function buildSnow(root, cfg) {
    const W = cfg.w, H = cfg.h, c = canvas(root, W, H), ctx = c.getContext('2d'), r = rng(cfg.seed || 11);
    const L = (cfg.layers || [{ n: 260, s: [1.4, 2.6], v: [150, 240], a: 0.55, wind: -0.55 }, { n: 120, s: [2.8, 4.4], v: [260, 380], a: 0.75, wind: -0.6 }, { n: 14, s: [5, 9], v: [520, 700], a: 0.16, wind: -0.7, blur: true }]);
    const P = []; for (const l of L) for (let i = 0; i < l.n; i++) P.push({ l, x: r() * W, y: r() * H, s: l.s[0] + r() * (l.s[1] - l.s[0]), v: l.v[0] + r() * (l.v[1] - l.v[0]), ph: r() * 6.28, sw: 10 + r() * 30 });
    const fog = cfg.fog ? Array.from({ length: 6 }, () => ({ x: r() * W, y: r() * H, rr: 420 + r() * 520, v: 180 + r() * 220, a: 0.025 + r() * 0.035 })) : [];
    return (t) => {
      ctx.clearRect(0, 0, W, H); const fade = Math.min(seg(t, 0, cfg.fadeIn ?? 0.6), 1 - seg(t, cfg.dur - (cfg.fadeOut ?? 0.6), cfg.dur));
      for (const f of fog) { const x = ((f.x - f.v * 1.1 * t) % (W + 2 * f.rr) + W + 2 * f.rr) % (W + 2 * f.rr) - f.rr; glow(ctx, x, f.y + 40 * Math.sin(t * 0.7 + f.x), f.rr, '235,242,250', f.a * fade, 0.3); }
      for (const p of P) {
        const dx = p.l.wind * p.v * t, dy = p.v * t; let x = p.x + dx + p.sw * Math.sin(t * 1.3 + p.ph), y = p.y + dy;
        x = ((x % (W + 40)) + W + 40) % (W + 40) - 20; y = ((y % (H + 40)) + H + 40) % (H + 40) - 20;
        const a = p.l.a * fade;
        if (p.l.blur) { glow(ctx, x, y, p.s * 1.6, '245,248,255', a, 0.35); continue; }
        ctx.strokeStyle = `rgba(245,248,255,${a})`; ctx.lineWidth = p.s; ctx.lineCap = 'round';
        const k = 0.022; ctx.beginPath(); ctx.moveTo(x, y); ctx.lineTo(x - p.l.wind * p.v * k, y - p.v * k); ctx.stroke();
      }
    };
  }
  function buildRain(root, cfg) {
    const W = cfg.w, H = cfg.h, c = canvas(root, W, H), ctx = c.getContext('2d'), r = rng(cfg.seed || 13), n = cfg.n || 420, wind = cfg.wind ?? -0.22;
    const P = Array.from({ length: n }, () => ({ x: r() * W, y: r() * H, z: 0.3 + r() * 0.7 }));
    return (t) => { ctx.clearRect(0, 0, W, H); const fade = Math.min(seg(t, 0, cfg.fadeIn ?? 0.5), 1 - seg(t, cfg.dur - (cfg.fadeOut ?? 0.5), cfg.dur));
      ctx.lineCap = 'round';
      for (const p of P) { const v = 1500 + 1700 * p.z, len = 18 + 46 * p.z; let x = p.x + wind * v * t, y = p.y + v * t;
        x = ((x % (W + 60)) + W + 60) % (W + 60) - 30; y = ((y % (H + 80)) + H + 80) % (H + 80) - 40;
        ctx.strokeStyle = `rgba(210,225,240,${(0.12 + 0.3 * p.z) * fade})`; ctx.lineWidth = 0.8 + 1.6 * p.z;
        ctx.beginPath(); ctx.moveTo(x, y); ctx.lineTo(x - wind * len, y - len); ctx.stroke();
        if (p.z > 0.85 && y > H * 0.82) glow(ctx, x, y, 6, '220,235,255', 0.25 * fade, 0.3); } };
  }
  function buildEmbers(root, cfg) {
    const W = cfg.w, H = cfg.h, c = canvas(root, W, H), ctx = c.getContext('2d'), r = rng(cfg.seed || 17), rgb = cfg.rgb || '255,160,70';
    const P = Array.from({ length: cfg.n || 70 }, () => ({ x: r() * W, y: r() * H, s: 1.5 + r() * 3.5, v: 30 + r() * 90, ph: r() * 6.28, f: 0.3 + r() * 0.9 }));
    return (t) => { ctx.clearRect(0, 0, W, H); ctx.globalCompositeOperation = 'lighter'; const fade = Math.min(seg(t, 0, 0.8), 1 - seg(t, cfg.dur - 0.8, cfg.dur));
      for (const p of P) { const x = ((p.x + 50 * Math.sin(t * p.f + p.ph) + 20 * t) % W + W) % W, y = ((p.y - p.v * t) % (H + 40) + H + 40) % (H + 40) - 20;
        const tw = 0.55 + 0.45 * Math.sin(t * 3.3 + p.ph * 4); glow(ctx, x, y, p.s * 3, rgb, 0.7 * tw * fade, 0.25); }
      ctx.globalCompositeOperation = 'source-over'; };
  }
  function buildDust(root, cfg) {
    const W = cfg.w, H = cfg.h, c = canvas(root, W, H), ctx = c.getContext('2d'), r = rng(cfg.seed || 5);
    const P = Array.from({ length: cfg.n || 90 }, () => ({ x: r() * W, y: r() * H, s: 1 + r() * 3.5, big: r() < 0.12, ph: r() * 6.28, f: 0.1 + r() * 0.25, a: 0.25 + r() * 0.5 }));
    return (t) => { ctx.clearRect(0, 0, W, H); ctx.globalCompositeOperation = 'lighter';
      const fade = Math.min(seg(t, 0, 1), 1 - seg(t, cfg.dur - 1, cfg.dur));
      for (const p of P) { const x = p.x + 60 * Math.sin(t * p.f + p.ph) + 14 * t, y = p.y - 18 * t + 40 * Math.sin(t * p.f * 0.7 + p.ph * 2);
        const tw = 0.6 + 0.4 * Math.sin(t * 2.1 + p.ph * 3); const xx = ((x % W) + W) % W, yy = ((y % H) + H) % H;
        if (p.big) glow(ctx, xx, yy, 18 + p.s * 6, '255,214,150', 0.10 * tw * fade, 0.5); else glow(ctx, xx, yy, p.s * 2.2, '255,226,170', p.a * tw * fade, 0.3); }
      ctx.globalCompositeOperation = 'source-over'; };
  }
  function buildSparks(root, cfg) {
    const W = cfg.w, H = cfg.h, c = canvas(root, W, H), ctx = c.getContext('2d'), r = rng(cfg.seed || 21);
    const S = []; const rate = (t) => 30 + 260 * Math.exp(-Math.pow((t - (cfg.peak ?? 0.3)) / 1.1, 2));
    let tt = 0; while (tt < cfg.dur) { const life = 0.35 + r() * 0.6, ang = (200 + r() * 55) * Math.PI / 180, sp = 900 + r() * 1500;
      S.push({ t0: tt, life, x: (cfg.ox ?? 1640) + (r() - 0.5) * 360, y: (cfg.oy ?? 960) + (r() - 0.5) * 140, vx: Math.cos(ang) * sp, vy: Math.sin(ang) * sp * 0.75 - 200, w: 1.2 + r() * 2.4 });
      tt += 1 / rate(tt); }
    return (t) => { ctx.clearRect(0, 0, W, H); ctx.globalCompositeOperation = 'lighter'; const fade = 1 - seg(t, cfg.dur - 0.5, cfg.dur);
      for (const s of S) { const a = t - s.t0; if (a < 0 || a > s.life) continue; const u = a / s.life;
        const x = s.x + s.vx * a, y = s.y + s.vy * a + 900 * a * a, px = s.x + s.vx * Math.max(0, a - 0.035), py = s.y + s.vy * Math.max(0, a - 0.035) + 900 * Math.max(0, a - 0.035) ** 2;
        const al = (1 - u) * fade; ctx.strokeStyle = `rgba(255,${Math.round(150 + 90 * (1 - u))},${Math.round(60 * (1 - u))},${al})`; ctx.lineWidth = s.w; ctx.lineCap = 'round';
        ctx.beginPath(); ctx.moveTo(px, py); ctx.lineTo(x, y); ctx.stroke(); glow(ctx, x, y, 10, '255,190,90', 0.35 * al); }
      glow(ctx, cfg.ox ?? 1640, cfg.oy ?? 960, 420, '255,140,40', 0.22 * fade * (0.7 + 0.3 * env({ flicker: { lo: 0.6, hi: 1, rate: 18, seed: 3 } }, t)));
      ctx.globalCompositeOperation = 'source-over'; };
  }
  function buildBurn(root, cfg) {
    const W = cfg.w, H = cfg.h, c = canvas(root, W, H), ctx = c.getContext('2d'), D = cfg.dur, mid = cfg.mid ?? D * 0.35;
    return (t) => { ctx.clearRect(0, 0, W, H);
      const a = t < mid ? inOut(seg(t, 0, mid)) : 1 - inOut(seg(t, mid, D));
      const x = -300 + (W + 900) * seg(t, 0, D) ** 0.8;
      glow(ctx, x, H * 0.55, 1400 * (0.5 + a), '255,150,60', 0.85 * a, 0.25);
      glow(ctx, x + 300, H * 0.4, 900 * (0.4 + a), '255,225,170', 0.9 * a, 0.3);
      ctx.fillStyle = `rgba(255,244,228,${(Math.pow(a, 2.2) * 0.95).toFixed(3)})`; ctx.fillRect(0, 0, W, H); };
  }
  function buildOldFilm(root, cfg) {
    const W = cfg.w, H = cfg.h, c = canvas(root, W, H), ctx = c.getContext('2d');
    const gw = 640, gh = 360, g = document.createElement('canvas'); g.width = gw; g.height = gh; const gx = g.getContext('2d'), img = gx.createImageData(gw, gh);
    const vig = ctx.createRadialGradient(W / 2, H / 2, H * 0.35, W / 2, H / 2, H * 1.05); vig.addColorStop(0, 'rgba(20,12,4,0)'); vig.addColorStop(1, 'rgba(20,12,4,0.62)');
    return (t) => { ctx.clearRect(0, 0, W, H); const fr = Math.floor(t * 24), fade = Math.min(seg(t, 0, 0.25), 1 - seg(t, cfg.dur - 0.25, cfg.dur));
      ctx.fillStyle = `rgba(112,78,38,${(0.2 * fade).toFixed(3)})`; ctx.fillRect(0, 0, W, H);                         // sepia wash
      const fl = env({ flicker: { lo: -1, hi: 1, rate: 24, seed: 9 } }, t); ctx.fillStyle = fl > 0 ? `rgba(255,240,210,${(0.05 * fl * fade).toFixed(3)})` : `rgba(0,0,0,${(-0.07 * fl * fade).toFixed(3)})`; ctx.fillRect(0, 0, W, H);
      const r = rng(1000 + fr), d = img.data; for (let i = 0; i < d.length; i += 4) { const v = r() * 255; d[i] = d[i + 1] = d[i + 2] = v; d[i + 3] = 34 * fade; }
      gx.putImageData(img, 0, 0); ctx.imageSmoothingEnabled = true; ctx.drawImage(g, 0, 0, W, H);
      const rs = rng(5000 + Math.floor(t * 8)); for (let k = 0; k < 3; k++) if (rs() < 0.55) { const x = rs() * W; ctx.fillStyle = `rgba(240,230,210,${(0.18 * fade).toFixed(3)})`; ctx.fillRect(x, 0, 1.5 + rs() * 1.5, H); }
      const rd = rng(9000 + fr); for (let k = 0; k < 6; k++) { ctx.fillStyle = `rgba(20,14,8,${(0.5 * fade).toFixed(3)})`; ctx.beginPath(); ctx.arc(rd() * W, rd() * H, 1 + rd() * 3.5, 0, 6.29); ctx.fill(); }
      ctx.globalAlpha = fade; ctx.fillStyle = vig; ctx.fillRect(0, 0, W, H); ctx.globalAlpha = 1; };
  }

  // ---------------------------------------------------------------- plates (picture space, units = fractions of the picture)
  function buildPlate(root, cfg) {
    const W = cfg.w, H = cfg.h; const im = document.createElement('img'); im.src = cfg.img; Object.assign(im.style, { position: 'absolute', left: 0, top: 0, width: W + 'px', height: H + 'px' }); root.appendChild(im);
    const c = canvas(root, W, H, 2), ctx = c.getContext('2d');
    return (t) => { ctx.clearRect(0, 0, W, H);
      for (const p of cfg.patches || []) { const a = env(p.a, t); if (a <= 0.002) continue; ctx.save(); ctx.translate(p.x * W, p.y * H); ctx.rotate((p.rot || 0) * Math.PI / 180); ctx.scale(1, p.sy || 1);
        const r = p.r * W, g = ctx.createRadialGradient(0, 0, 0, 0, 0, r); g.addColorStop(0, `rgba(${p.rgb},${a})`); g.addColorStop(p.core ?? 0.45, `rgba(${p.rgb},${a * 0.85})`); g.addColorStop(1, `rgba(${p.rgb},0)`);
        ctx.fillStyle = g; ctx.fillRect(-r, -r, 2 * r, 2 * r); ctx.restore(); }
      ctx.globalCompositeOperation = 'lighter';
      for (const l of cfg.lights || []) { const a = env(l.a, t); if (a <= 0.002) continue; const r = l.r * W * (l.grow ? 1 + (env(l.grow, t)) : 1);
        if (l.rect) { ctx.save(); ctx.translate(l.x * W, l.y * H); ctx.scale(l.rect[0] * W / (l.rect[1] * H), 1); glow(ctx, 0, 0, l.rect[1] * H * 0.75, l.rgb, a, 0.45); ctx.restore(); }
        else glow(ctx, l.x * W, l.y * H, r, l.rgb, a, l.core ?? 0.18);
        if (l.star) star(ctx, l.x * W, l.y * H, l.star * W, l.rgb, a * 0.9, l.angles, l.thick || 4); }
      ctx.globalCompositeOperation = 'source-over'; };
  }

  const KINDS = { type: buildType, snow: buildSnow, rain: buildRain, embers: buildEmbers, dust: buildDust, sparks: buildSparks, burn: buildBurn, oldfilm: buildOldFilm, plate: buildPlate };
  window.LT = { env, boot(cfg) {
    const root = document.getElementById('lt'); const draw = KINDS[cfg.kind](root, cfg);
    const tl = gsap.timeline({ paused: true }), drv = { t: 0 };
    tl.fromTo(drv, { t: 0 }, { t: cfg.dur, duration: cfg.dur, ease: 'none', onUpdate: () => draw(drv.t) }, 0);
    if (document.fonts && document.fonts.ready) document.fonts.ready.then(() => draw(drv.t));
    window.addEventListener('hf-seek', (e) => { const d = e && e.detail; draw(d && Number.isFinite(+d.time) ? +d.time : drv.t); }); window.__timelines = window.__timelines || {}; window.__timelines[cfg.id] = tl; draw(0);
  } };
})();
