// text.js (free kit): large animated text, three presets. Each adds tweens to your composition's timeline.
//   TX.typeOn(tl, el, at, perLetter = 0.045)   letters appear one by one, like typing (returns the time it ends)
//   TX.slam(tl, el, at)                        the whole line drops in hard and settles
//   TX.words(tl, el, at, gap = 0.12)           words rise in one after another out of a soft blur (returns the end time)
// Use big type: 120 px or more for key phrases so it reads on a phone.
(function () {
  const split = (el, by) => { const text = el.textContent; el.textContent = '';
    return (by === 'word' ? text.split(/(\s+)/) : [...text]).map((s) => { const sp = document.createElement('span'); sp.textContent = s;
      sp.style.display = 'inline-block'; sp.style.whiteSpace = 'pre'; el.appendChild(sp); return sp; }); };
  function typeOn(tl, el, at, per = 0.045) {
    const chars = split(el, 'char'); tl.set(chars, { opacity: 0 }, 0);
    chars.forEach((c, i) => tl.set(c, { opacity: 1 }, at + i * per));
    return at + chars.length * per;
  }
  function slam(tl, el, at) {
    tl.set(el, { opacity: 0 }, 0);
    tl.fromTo(el, { opacity: 0, scale: 1.6, filter: 'blur(14px)' }, { opacity: 1, scale: 1, filter: 'blur(0px)', duration: 0.28, ease: 'expo.in', immediateRender: false }, at);
    tl.fromTo(el, { y: 0 }, { y: 6, duration: 0.08, yoyo: true, repeat: 1, ease: 'power1.out', immediateRender: false }, at + 0.28);
    return at + 0.44;
  }
  function words(tl, el, at, gap = 0.12) {
    const ws = split(el, 'word').filter((w) => w.textContent.trim()); tl.set(ws, { opacity: 0 }, 0);
    ws.forEach((w, i) => tl.fromTo(w, { opacity: 0, y: 40, filter: 'blur(8px)' }, { opacity: 1, y: 0, filter: 'blur(0px)', duration: 0.35, ease: 'power3.out', immediateRender: false }, at + i * gap));
    return at + ws.length * gap + 0.35;
  }
  window.TX = { typeOn, slam, words };
})();
