// cards.js (free kit): 3D-style elements in CSS. A card is a panel with real thickness (edge faces), a soft shadow and a glowing
// rim, standing in a perspective scene, so it can tilt, flip and turn while it builds on screen.
//   const c = CARD.make(parentEl, { x, y, w, h, depth: 24, color: '#E8743C', html: '<h2>Hello</h2>' })
//   CARD.build(tl, c, at, from = 'below')   rises in from 'below' | 'left' | 'right' | 'above' with a flip, its rim draws on
//   CARD.tilt(tl, c, dur)                   a slow turn for the whole clip so it never sits still
(function () {
  const CSS = `
  .cd-scene { position: absolute; perspective: 1400px; }
  .cd { position: absolute; inset: 0; transform-style: preserve-3d; }
  .cd-face { position: absolute; inset: 0; border-radius: 22px; background: linear-gradient(160deg, #22222A, #121216); color: #F3F1EC;
             box-shadow: 0 40px 80px rgba(0,0,0,0.5); overflow: hidden; font: 600 40px/1.2 'Inter', sans-serif; padding: 44px; box-sizing: border-box; display: flex; flex-direction: column; justify-content: center; }
  .cd-face::after { content: ''; position: absolute; inset: 0; border-radius: inherit; border: 2px solid rgba(var(--cd-rgb), 0.9);
                    box-shadow: inset 0 0 24px rgba(var(--cd-rgb), 0.35), 0 0 24px rgba(var(--cd-rgb), 0.45); clip-path: inset(0 calc(100% * (1 - var(--rim, 1))) 0 0); }
  .cd-edge { position: absolute; background: linear-gradient(180deg, rgba(var(--cd-rgb), 0.55), #0A0A0D); }`;
  function css() { if (document.getElementById('cd-css')) return; const s = document.createElement('style'); s.id = 'cd-css'; s.textContent = CSS; document.head.appendChild(s); }
  const rgb = (hex) => { const n = parseInt(hex.replace('#', ''), 16); return `${(n >> 16) & 255}, ${(n >> 8) & 255}, ${n & 255}`; };
  function make(parent, { x = 660, y = 340, w = 600, h = 400, depth = 24, color = '#E8743C', html = '' } = {}) {
    css(); const scene = document.createElement('div'); scene.className = 'cd-scene'; Object.assign(scene.style, { left: x + 'px', top: y + 'px', width: w + 'px', height: h + 'px' });
    const card = document.createElement('div'); card.className = 'cd'; card.style.setProperty('--cd-rgb', rgb(color)); scene.appendChild(card);
    // the thickness: four edge faces behind the front face
    [[0, 0, w, depth, `rotateX(90deg) translateZ(${-depth / 2}px)`, 'top'], [0, h - depth, w, depth, `rotateX(-90deg) translateZ(${-depth / 2}px)`, 'bottom'],
     [0, 0, depth, h, `rotateY(-90deg) translateZ(${-depth / 2}px)`, 'left'], [w - depth, 0, depth, h, `rotateY(90deg) translateZ(${-depth / 2}px)`, 'right']].forEach(([l, t, ew, eh, tr, side]) => {
      const e = document.createElement('div'); e.className = 'cd-edge'; Object.assign(e.style, { left: l + 'px', top: t + 'px', width: ew + 'px', height: eh + 'px', transform: tr,
        transformOrigin: side === 'top' ? '50% 0' : side === 'bottom' ? '50% 100%' : side === 'left' ? '0 50%' : '100% 50%' }); card.appendChild(e); });
    const face = document.createElement('div'); face.className = 'cd-face'; face.innerHTML = html; face.style.transform = 'translateZ(0px)'; card.appendChild(face);
    parent.appendChild(scene); return { scene, card, face };
  }
  const FROM = { below: { y: 260, rotationX: 55 }, above: { y: -260, rotationX: -55 }, left: { x: -340, rotationY: -55 }, right: { x: 340, rotationY: 55 } };
  function build(tl, c, at, from = 'below') {
    tl.set(c.card, { opacity: 0 }, 0);
    tl.fromTo(c.card, { opacity: 0, x: 0, y: 0, rotationX: 0, rotationY: 0, ...FROM[from], scale: 0.85 }, { opacity: 1, x: 0, y: 0, rotationX: 0, rotationY: 0, scale: 1, duration: 0.7, ease: 'power4.out', immediateRender: false }, at);
    tl.fromTo(c.face, { '--rim': 0 }, { '--rim': 1, duration: 0.6, ease: 'power2.inOut', immediateRender: false }, at + 0.2);
    return at + 0.8;
  }
  function tilt(tl, c, dur) { tl.fromTo(c.scene, { rotationY: -7, rotationX: 4 }, { rotationY: 7, rotationX: -3, duration: dur, ease: 'sine.inOut' }, 0); }
  window.CARD = { make, build, tilt };
})();
