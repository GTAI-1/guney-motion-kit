// stage.js (free kit): the frame clock and the math every scene uses. Everything a scene draws is a pure function of time t,
// so any frame renders on its own. STAGE.driver(duration, frame) returns one paused GSAP timeline that calls frame(t).
(function () {
  // ---------- math ----------
  const clamp = (x, a = 0, b = 1) => Math.min(b, Math.max(a, x));
  const lerp = (a, b, u) => a + (b - a) * u;
  const seg = (t, a, b) => clamp((t - a) / (b - a));
  const E = {
    lin: (u) => u, outCubic: (u) => 1 - Math.pow(1 - u, 3), inCubic: (u) => u * u * u, outQuad: (u) => 1 - (1 - u) * (1 - u), inQuad: (u) => u * u,
    inOutCubic: (u) => (u < 0.5 ? 4 * u * u * u : 1 - Math.pow(-2 * u + 2, 3) / 2), inOutSine: (u) => -(Math.cos(Math.PI * u) - 1) / 2,
    outExpo: (u) => (u >= 1 ? 1 : 1 - Math.pow(2, -10 * u)), inExpo: (u) => (u <= 0 ? 0 : Math.pow(2, 10 * u - 10)),
    inOutExpo: (u) => (u <= 0 ? 0 : u >= 1 ? 1 : u < 0.5 ? Math.pow(2, 20 * u - 10) / 2 : (2 - Math.pow(2, -20 * u + 10)) / 2),
    outQuint: (u) => 1 - Math.pow(1 - u, 5), inOutQuint: (u) => (u < 0.5 ? 16 * u ** 5 : 1 - Math.pow(-2 * u + 2, 5) / 2),
    outBack: (u, s = 1.7) => 1 + (s + 1) * Math.pow(u - 1, 3) + s * Math.pow(u - 1, 2),
  };
  // damped spring step response (0 -> 1 with overshoot); d = seconds since the step
  function spring(d, f = 3.2, z = 0.42) {
    if (d <= 0) return 0; const w = 2 * Math.PI * f, wd = w * Math.sqrt(1 - z * z);
    return 1 - Math.exp(-z * w * d) * (Math.cos(wd * d) + ((z * w) / wd) * Math.sin(wd * d));
  }
  // squash on impact: [sx, sy] d seconds after a landing; k = how hard
  function impact(d, k = 0.3, decay = 0.07, f = 7.5) {
    if (d < 0 || d > 0.6) return [1, 1];
    const e = Math.exp(-d / decay) * Math.cos(2 * Math.PI * f * d), sy = 1 - k * e;
    return [1 / Math.sqrt(Math.max(0.3, sy)), sy];
  }
  function mulberry32(a) { return () => { a |= 0; a = (a + 0x6d2b79f5) | 0; let t = Math.imul(a ^ (a >>> 15), 1 | a); t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t; return ((t ^ (t >>> 14)) >>> 0) / 4294967296; }; }
  const hash = (n) => { const x = Math.sin(n * 127.1 + 311.7) * 43758.5453; return x - Math.floor(x); };

  // ---------- driver: one paused timeline that calls frame(t) ----------
  function driver(dur, frame) {
    const tl = gsap.timeline({ paused: true }), drv = { t: 0 };
    tl.fromTo(drv, { t: 0 }, { t: dur, duration: dur, ease: 'none', onUpdate: () => frame(drv.t) }, 0);
    frame(0);
    // fonts and canvases that were not ready at registration: draw the current time again once they are
    if (document.fonts && document.fonts.ready) document.fonts.ready.then(() => { try { frame(drv.t); } catch (err) { console.error(err); } });
    // HyperFrames re-dispatches hf-seek after it swaps the current video frames in; redraw then so screens are not a frame late
    window.addEventListener('hf-seek', (e) => { const d = e && e.detail; const t = d && Number.isFinite(+d.time) ? +d.time : drv.t; try { frame(t); } catch (err) { console.error(err); } });
    return tl;
  }

  window.STAGE = { clamp, lerp, seg, E, spring, impact, mulberry32, hash, driver };
})();
