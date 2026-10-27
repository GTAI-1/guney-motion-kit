// claudewin.js (free kit): a chat window in the style of the Claude desktop app: title bar, conversation, composer. Your words
// type into the composer and send as a bubble, the reply comes in line by line, and the view zooms onto the part you talk about.
//   const W = CW.make(parentEl, { title: 'My project', x: 360, y: 140, w: 1200, h: 800 })
//   W.type(at, 'Make me an intro', 0.04)   typed into the composer, letter by letter      W.send(at)   it becomes your bubble
//   W.reply(at, ['First line', 'Second line'], 0.35)   the answer arrives line by line
//   W.zoom(at, dur, el, 1.8)   zoom onto an element of the window (W.lines[0], W.composer, ...), never so far that it is cut;
//                              W.zoom(at, dur, null) zooms back out
//   CW.live(tl, W, duration)   runs it on the composition's timeline (or call W.update(t) inside frame(t))
(function () {
  const CSS = `
  .cw-view { position: absolute; overflow: hidden; border-radius: 22px; box-shadow: 0 50px 110px rgba(0,0,0,0.55); }
  .cw { position: absolute; left: 0; top: 0; background: #1F1E1D; color: #ECEAE5; font: 400 30px/1.45 'Inter', sans-serif; transform-origin: 0 0; }
  .cw-bar { height: 62px; display: flex; align-items: center; gap: 12px; padding: 0 24px; background: #171716; border-bottom: 1px solid #2C2B29; }
  .cw-bar i { width: 14px; height: 14px; border-radius: 50%; background: #3A3936; }
  .cw-bar span { margin-left: 14px; font-size: 22px; color: #B9B6AE; }
  .cw-chat { position: absolute; left: 0; right: 0; top: 62px; bottom: 150px; padding: 34px 48px; overflow: hidden; display: flex; flex-direction: column; justify-content: flex-end; }
  .cw-me { align-self: flex-end; max-width: 72%; background: #2E2D2A; border-radius: 18px; padding: 14px 22px; margin: 0 0 26px; }
  .cw-line { margin: 0 0 14px; width: fit-content; max-width: 100%; }
  .cw-dot { display: inline-block; width: 14px; height: 14px; border-radius: 50%; background: #D97757; margin-right: 14px; vertical-align: middle; }
  .cw-comp { position: absolute; left: 40px; right: 40px; bottom: 34px; height: 84px; border-radius: 18px; background: #2A2927; border: 1px solid #3A3936;
             display: flex; align-items: center; padding: 0 26px; color: #8E8B84; }
  .cw-comp b { font-weight: 400; color: #ECEAE5; }
  .cw-caret { display: inline-block; width: 2.5px; height: 32px; background: #ECEAE5; margin-left: 2px; vertical-align: middle; }`;
  function css() { if (document.getElementById('cw-css')) return; const s = document.createElement('style'); s.id = 'cw-css'; s.textContent = CSS; document.head.appendChild(s); }
  const mk = (cls, parent, html) => { const d = document.createElement('div'); d.className = cls; if (html != null) d.innerHTML = html; parent.appendChild(d); return d; };
  function make(parent, { title = 'New chat', x = 360, y = 140, w = 1200, h = 800, placeholder = 'Reply to Claude...' } = {}) {
    css(); const S = STAGE;
    const view = mk('cw-view', parent); Object.assign(view.style, { left: x + 'px', top: y + 'px', width: w + 'px', height: h + 'px' });
    const el = mk('cw', view); Object.assign(el.style, { width: w + 'px', height: h + 'px' });
    mk('cw-bar', el, `<i></i><i></i><i></i><span>${title}</span>`);
    const chat = mk('cw-chat', el), comp = mk('cw-comp', el), ev = [], lines = [];
    const W = { view, el, chat, composer: comp, lines, events: ev,
      type(at, text, per = 0.04) { ev.push({ k: 'type', at, text, per }); return at + text.length * per; },
      send(at) { const b = mk('cw-me', chat); b.style.display = 'none'; ev.push({ k: 'send', at, b }); return at; },
      reply(at, list, per = 0.35) { list.forEach((s, i) => { const l = mk('cw-line', chat, (i === 0 ? '<span class="cw-dot"></span>' : '') + s); l.style.display = 'none'; lines.push(l); ev.push({ k: 'line', at: at + i * per, l }); });
        return at + list.length * per; },
      zoom(at, dur, target, s = 1.8) { ev.push({ k: 'zoom', at, dur, target, s }); return at + dur; },
      update(t) {
        // the composer: the newest typed text before its send, then empty
        let txt = '', sentText = null;
        ev.forEach((e) => { if (e.k === 'type' && t >= e.at) { txt = e.text.slice(0, Math.min(e.text.length, Math.floor((t - e.at) / e.per) + 1)); sentText = e.text; }
          if (e.k === 'send') { e.b.style.display = t >= e.at ? '' : 'none'; if (t >= e.at && sentText && e.b.textContent !== sentText) e.b.textContent = sentText; if (t >= e.at) txt = ''; }
          if (e.k === 'line') e.l.style.display = t >= e.at ? '' : 'none'; });
        const typing = txt.length > 0, html = typing ? `<b>${txt}</b><span class="cw-caret"></span>` : placeholder;
        if (comp.innerHTML !== html) comp.innerHTML = html;
        // the zoom: ease between the previous and the newest zoom target
        let cur = { s: 1, cx: w / 2, cy: h / 2 }, prev = cur, u = 1;
        ev.filter((e) => e.k === 'zoom' && t >= e.at).forEach((e) => { prev = cur; const r = e.target ? box(e.target, el) : null;
          cur = r ? { s: Math.min(e.s, (w * 0.86) / Math.max(1, r.w)), cx: r.x + r.w / 2, cy: r.y + r.h / 2 } : { s: 1, cx: w / 2, cy: h / 2 }; u = S.E.inOutCubic(S.seg(t, e.at, e.at + e.dur)); });
        const s = S.lerp(prev.s, cur.s, u), cx = S.lerp(prev.cx, cur.cx, u), cy = S.lerp(prev.cy, cur.cy, u);
        const tx = Math.min(0, Math.max(w - w * s, w / 2 - cx * s)), ty = Math.min(0, Math.max(h - h * s, h / 2 - cy * s));
        el.style.transform = `translate(${tx.toFixed(1)}px, ${ty.toFixed(1)}px) scale(${s.toFixed(4)})`;
      } };
    return W;
  }
  function box(node, root) { const d = node.style.display; let x = 0, y = 0, n = node; while (n && n !== root) { x += n.offsetLeft; y += n.offsetTop; n = n.offsetParent; } return { x, y, w: node.offsetWidth, h: node.offsetHeight }; }
  function live(tl, W, dur) { const d = { t: 0 }; tl.fromTo(d, { t: 0 }, { t: dur, duration: dur, ease: 'none', onUpdate: () => W.update(d.t) }, 0); W.update(0); }
  window.CW = { make, live };
})();
