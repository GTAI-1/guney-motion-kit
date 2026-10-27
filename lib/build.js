// build.js (free kit): graphics that build themselves on screen instead of popping in.
//   BUILD.frame(parentEl, { x, y, w, h, r: 24, color })  a glowing outline; BUILD.drawFrame(tl, f, at, dur) draws it on from a corner
//   BUILD.pieces(tl, els, at, step = 0.12)               the parts arrive one at a time, each from its own direction, out of a blur
// One thing at a time: let each piece land before the next starts.
(function () {
  const NS = 'http://www.w3.org/2000/svg';
  function frame(parent, { x = 0, y = 0, w = 400, h = 300, r = 24, color = '#E8743C', width = 3 } = {}) {
    const svg = document.createElementNS(NS, 'svg'); svg.setAttribute('width', w + 12); svg.setAttribute('height', h + 12);
    Object.assign(svg.style, { position: 'absolute', left: x - 6 + 'px', top: y - 6 + 'px', overflow: 'visible', filter: `drop-shadow(0 0 10px ${color})` });
    const rect = document.createElementNS(NS, 'rect'); [['x', 6], ['y', 6], ['width', w], ['height', h], ['rx', r], ['ry', r], ['fill', 'none'], ['stroke', color], ['stroke-width', width]].forEach(([k, v]) => rect.setAttribute(k, v));
    const len = 2 * (w + h) - (8 - 2 * Math.PI) * r; rect.style.strokeDasharray = len; rect.style.strokeDashoffset = len;
    svg.appendChild(rect); parent.appendChild(svg); return { svg, rect, len };
  }
  function drawFrame(tl, f, at, dur = 0.6) { tl.fromTo(f.rect, { strokeDashoffset: f.len }, { strokeDashoffset: 0, duration: dur, ease: 'power2.inOut', immediateRender: false }, at); return at + dur; }
  const DIRS = [{ y: 60 }, { x: -80 }, { x: 80 }, { y: -60 }];
  function pieces(tl, els, at, step = 0.12) {
    tl.set(els, { opacity: 0 }, 0);
    els.forEach((el, i) => tl.fromTo(el, { opacity: 0, x: 0, y: 0, ...DIRS[i % 4], scale: 0.9, filter: 'blur(10px)' },
      { opacity: 1, x: 0, y: 0, scale: 1, filter: 'blur(0px)', duration: 0.45, ease: 'expo.out', immediateRender: false }, at + i * step));
    return at + els.length * step + 0.45;
  }
  window.BUILD = { frame, drawFrame, pieces };
})();
