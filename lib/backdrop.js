// backdrop.js (free kit): an animated background in any colour. A dark ground tinted by your colour, a soft glow on the
// horizon, a grid floor sliding toward the camera and drifting motes. It never stops moving, so a held frame never looks frozen.
//   const bg = BG.make(rootEl, { color: '#E8743C', motes: 24, seed: 7, grid: true })
//   BG.live(tl, bg, duration)     keeps it moving on the composition's own timeline (or call bg.update(t) inside frame(t))
//   bg.setColor('#4FA3FF')        change the colour at any time
// Put your content in a layer above it (a sibling element with a higher z-index).
(function () {
  const CSS = `
  .bg-root { position: absolute; inset: 0; overflow: hidden; background: #07070A; }
  .bg-ground { position: absolute; inset: 0; background: radial-gradient(ellipse 90% 70% at 50% 64%, rgba(var(--bg-rgb), 0.20), rgba(7,7,10,0) 70%), #07070A; }
  .bg-glow { position: absolute; left: 50%; top: 58%; width: 1500px; height: 260px; margin: -130px 0 0 -750px; border-radius: 50%;
             background: radial-gradient(ellipse at center, rgba(var(--bg-rgb), 0.55), rgba(var(--bg-rgb), 0) 70%); filter: blur(30px); }
  .bg-floorwrap { position: absolute; left: -40%; right: -40%; top: 60%; height: 900px; perspective: 700px; perspective-origin: 50% 0;
                  -webkit-mask-image: linear-gradient(180deg, transparent 0%, #000 22%, #000 70%, transparent 100%); mask-image: linear-gradient(180deg, transparent 0%, #000 22%, #000 70%, transparent 100%); }
  .bg-floor { position: absolute; inset: 0; transform-origin: 50% 0; transform: rotateX(72deg);
              background-image: linear-gradient(rgba(var(--bg-rgb), 0.45) 2px, transparent 2px), linear-gradient(90deg, rgba(var(--bg-rgb), 0.45) 2px, transparent 2px);
              background-size: 110px 110px; }
  .bg-mote { position: absolute; border-radius: 50%; background: rgba(var(--bg-rgb), 0.9); box-shadow: 0 0 8px rgba(var(--bg-rgb), 0.8); }
  .bg-vig { position: absolute; inset: 0; background: radial-gradient(ellipse 75% 70% at 50% 50%, transparent 55%, rgba(0,0,0,0.55) 100%); }`;
  function css() { if (document.getElementById('bg-css')) return; const s = document.createElement('style'); s.id = 'bg-css'; s.textContent = CSS; document.head.appendChild(s); }
  const mk = (cls, parent) => { const d = document.createElement('div'); d.className = cls; parent.appendChild(d); return d; };
  const rgb = (hex) => { const n = parseInt(hex.replace('#', ''), 16); return `${(n >> 16) & 255}, ${(n >> 8) & 255}, ${n & 255}`; };

  function make(root, { color = '#E8743C', motes = 24, seed = 7, grid = true } = {}) {
    css(); root.classList.add('bg-root'); root.style.setProperty('--bg-rgb', rgb(color));
    mk('bg-ground', root); const glow = mk('bg-glow', root);
    let floor = null; if (grid) floor = mk('bg-floor', mk('bg-floorwrap', root));
    const rnd = STAGE.mulberry32(seed), list = [];
    for (let i = 0; i < motes; i++) { const m = mk('bg-mote', root), s = 1.5 + rnd() * 3;
      Object.assign(m.style, { left: (rnd() * 1920).toFixed(0) + 'px', top: (80 + rnd() * 860).toFixed(0) + 'px', width: s.toFixed(1) + 'px', height: s.toFixed(1) + 'px' });
      list.push({ m, p: rnd() * 6.28, a: 20 + rnd() * 40, o: 0.25 + rnd() * 0.5 }); }
    mk('bg-vig', root);
    return { root, glow, floor, motes: list,
      setColor(c) { root.style.setProperty('--bg-rgb', rgb(c)); },
      // everything is a function of t: the grid slides, the glow breathes, the motes drift
      update(t) {
        if (floor) floor.style.backgroundPosition = `0px ${(t * 60).toFixed(1)}px`;
        glow.style.opacity = (0.8 + 0.2 * Math.sin(t * 0.9)).toFixed(3);
        list.forEach((q) => { q.m.style.transform = `translate(${(Math.cos(q.p + t * 0.25) * q.a).toFixed(1)}px, ${(-t * 6 + Math.sin(q.p + t * 0.4) * q.a * 0.5).toFixed(1)}px)`;
          q.m.style.opacity = (q.o * (0.6 + 0.4 * Math.sin(q.p * 3 + t * 1.3))).toFixed(3); });
      } };
  }
  function live(tl, bg, dur) { const d = { t: 0 }; tl.fromTo(d, { t: 0 }, { t: dur, duration: dur, ease: 'none', onUpdate: () => bg.update(d.t) }, 0); bg.update(0); }
  window.BG = { make, live };
})();
