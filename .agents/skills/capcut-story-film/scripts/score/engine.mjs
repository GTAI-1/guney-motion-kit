// Score + sound-design synthesizer for capcut-story-film (48 kHz stereo, deterministic, free). A film's cue sheet
// (plan/cue.mjs) calls these functions with NARRATION-clock times; run.mjs renders two stems for CapCut:
// renders/audio/score.wav and renders/audio/sfx.wav (ducked under the voice, levels set for a voice at 0 dB).
//
// MUSIC  drone(t0,t1,midi,g,{attack,release})        sub + fifth, breathing            (low bed, 26 = D1, 29 = F1)
//        pad(t0,t1,notes,g,{attack,release,cut:[a,b],send})  detuned-saw strings, moving low-pass (chords)
//        tone(t0,t1,midi,g,{attack,release})         high glassy sustained tone, tremolo (mystery)
//        piano(t,midi,vel,{len,sus,pan})             additive piano note (isolated notes, motifs, arpeggios)
//        arp(t0,t1,notes,step,vel,{grow})            piano arpeggio through notes every step seconds
//        boom(t,g,{len,d})  thud(t,g)                cinematic low hit / short hit (titles, key words, impacts)
//        riser(t0,t1,g)                              noise + tone sweep into a hit
//        ostinato(t0,t1,seq,bpm,g,{ramp,cut})        staccato low strings (tension, momentum)
//        heartbeat(t0,t1,period,g)                   lub-dub thumps (dread, decision)
//        whum(t,g)                                   soft low swell for lights / flashes / signals (never a ping)
// SFX    wind(t0,t1,g,{fade,muffle})  rain(t0,t1,g)  fire(t0,t1,g)  rumble(t0,t1,g)  crowd(t0,t1,g)  hum(t0,t1,f,g,{rise})
//        train(t0,t1,g,{speed:fn,muffle,fade,fadeOut}) rail joints, chuffs, rumble (any vehicle rhythm)
//        steps(times,g,{surface:'frost'|'stone'|'wood'})  crunch(t,g)  clunk(t,g,{f})  creak(t0,d,g)  glass(t,g)
//        screech(t0,t1,g)  shudder(t0,t1,g)  hiss(t0,d,g)  whoosh(t0,d,g)  rustle(t0,t1,g)  scrape(t0,t1,g)
//        relay(t,g)  birdsong(t0,t1,g)  chirp(t,f0,f1,d,g)
// MIX    silence(t0,t1)  nothing from the score in this window (a dramatic stop); duck(dbScore, dbSfx)
// HELP   chord('Dm', octave=3) -> midi notes ('C','Cm','Cdim','Csus4','Cadd9','C7','Cmaj7','Cm7'); midi('A4') -> 69
import fs from 'node:fs';
const SR = 48000, TAU = Math.PI * 2;
export const mtof = (m) => 440 * Math.pow(2, (m - 69) / 12);
const NOTE = { C: 0, 'C#': 1, Db: 1, D: 2, 'D#': 3, Eb: 3, E: 4, F: 5, 'F#': 6, Gb: 6, G: 7, 'G#': 8, Ab: 8, A: 9, 'A#': 10, Bb: 10, B: 11 };
export const midi = (s) => { const m = /^([A-G][#b]?)(-?\d)$/.exec(s); return 12 * (+m[2] + 1) + NOTE[m[1]]; };
export function chord(name, octave = 3) {
  const m = /^([A-G][#b]?)(.*)$/.exec(name), root = 12 * (octave + 1) + NOTE[m[1]];
  const Q = { '': [0, 4, 7], m: [0, 3, 7], dim: [0, 3, 6], sus4: [0, 5, 7], sus2: [0, 2, 7], add9: [0, 4, 7, 14], madd9: [0, 3, 7, 14], 7: [0, 4, 7, 10], maj7: [0, 4, 7, 11], m7: [0, 3, 7, 10] };
  return (Q[m[2]] || Q['']).map((i) => root + i);
}
function rng(seed) { let a = seed >>> 0; return () => { a = (a + 0x6d2b79f5) | 0; let t = Math.imul(a ^ (a >>> 15), 1 | a); t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t; return ((t ^ (t >>> 14)) >>> 0) / 4294967296; }; }
const db = (d) => Math.pow(10, d / 20);
const sm = (u) => (u <= 0 ? 0 : u >= 1 ? 1 : u * u * (3 - 2 * u));
const env = (t, a, d) => Math.min(1, t / a) * Math.exp(-t / d);
function bq() { let x1 = 0, x2 = 0, y1 = 0, y2 = 0, b0 = 1, b1 = 0, b2 = 0, a1 = 0, a2 = 0;
  return { set(type, f, q = 0.707) { const w = TAU * Math.min(Math.max(f, 15), SR * 0.45) / SR, c = Math.cos(w), s = Math.sin(w), al = s / (2 * q), a0 = 1 + al;
      if (type === 'lp') { b0 = (1 - c) / 2; b1 = 1 - c; b2 = b0; } else if (type === 'hp') { b0 = (1 + c) / 2; b1 = -(1 + c); b2 = b0; } else { b0 = al; b1 = 0; b2 = -al; }
      b0 /= a0; b1 /= a0; b2 /= a0; a1 = -2 * c / a0; a2 = (1 - al) / a0; return this; },
    run(x) { const y = b0 * x + b1 * x1 + b2 * x2 - a1 * y1 - a2 * y2; x2 = x1; x1 = x; y2 = y1; y1 = y; return y; } }; }

export function createScore({ length, pre }) {
  const N = Math.ceil(length * SR), R = rng(777), nz = () => R() * 2 - 1;
  const bus = () => [new Float32Array(N), new Float32Array(N)];
  const MUS = bus(), MUSV = bus(), SFX = bus(), SFXV = bus(), SIL = [];
  let duckS = 5, duckX = 2;
  const I = (t) => Math.round((t + pre) * SR);
  const put = (b, i, l, r) => { if (i >= 0 && i < N) { b[0][i] += l; b[1][i] += r; } };
  function saw() { let ph = R(); return (f) => { const dt = f / SR; ph += dt; if (ph >= 1) ph -= 1; let v = 2 * ph - 1;
    if (ph < dt) { const t = ph / dt; v -= t + t - t * t - 1; } else if (ph > 1 - dt) { const t = (ph - 1) / dt; v -= t * t + t + t + 1; } return v; }; }
  const api = {};
  // ---------------------------------------------------------------- music
  api.pad = (t0, t1, notes, g = 1, o = {}) => {
    const A = o.attack ?? 1.6, Rl = o.release ?? 2.2, i0 = I(t0), i1 = I(t1) + Math.round(Rl * SR), cut = o.cut ?? [700, 1400], send = o.send ?? 0.45;
    for (const [k, m] of notes.entries()) {
      const vs = [-0.11, -0.04, 0.03, 0.09, 0.0].map((d, j) => ({ o: saw(), d, pan: (j - 2) / 2.5 * 0.7 })), fl = bq(), fr = bq(), hp = bq().set('hp', 60), hp2 = bq().set('hp', 60);
      const f0 = mtof(m), dur = (i1 - i0) / SR, gn = g / Math.sqrt(notes.length) * 0.16;
      for (let i = Math.max(0, i0), n = i - i0; i < i1 && i < N; i++, n++) {
        const t = n / SR, rel = t > t1 - t0 ? 1 - (t - (t1 - t0)) / Rl : 1, e = sm(t / A) * Math.max(0, rel);
        if ((n & 63) === 0) { const c = cut[0] + (cut[1] - cut[0]) * (0.5 - 0.5 * Math.cos(Math.PI * Math.min(1, t / Math.max(0.1, dur * 0.6)))); fl.set('lp', c, 0.8); fr.set('lp', c * 1.04, 0.8); }
        const vib = 1 + 0.0025 * Math.sin(TAU * 4.6 * t + k); let L = 0, Rr = 0;
        for (const v of vs) { const s = v.o(f0 * (1 + v.d / 100 * 6) * vib); L += s * (0.5 - v.pan * 0.5); Rr += s * (0.5 + v.pan * 0.5); }
        L = hp.run(fl.run(L)) * e * gn; Rr = hp2.run(fr.run(Rr)) * e * gn; put(MUS, i, L, Rr); put(MUSV, i, L * send, Rr * send); } }
  };
  api.drone = (t0, t1, m, g = 1, o = {}) => { const i0 = I(t0), i1 = I(t1), A = o.attack ?? 3, Rl = o.release ?? 3, f = mtof(m); let ph = 0, ph2 = 0;
    for (let i = Math.max(0, i0); i < i1 && i < N; i++) { const t = (i - i0) / SR, T = (i1 - i0) / SR, e = sm(t / A) * sm((T - t) / Rl) * (0.8 + 0.2 * Math.sin(TAU * 0.11 * t));
      ph += f / SR; ph2 += f * 1.5 / SR; const v = (Math.sin(TAU * ph) + 0.35 * Math.sin(TAU * ph2) + 0.12 * Math.sin(TAU * 2 * ph)) * e * g * 0.35; put(MUS, i, v, v); } };
  api.tone = (t0, t1, m, g = 1, o = {}) => { const i0 = I(t0), i1 = I(t1), f = mtof(m), A = o.attack ?? 2, Rl = o.release ?? 2; let ph = 0;
    for (let i = Math.max(0, i0); i < i1 && i < N; i++) { const t = (i - i0) / SR, T = (i1 - i0) / SR, e = sm(t / A) * sm((T - t) / Rl) * (0.7 + 0.3 * Math.sin(TAU * 5.2 * t));
      ph += f / SR; const v = (Math.sin(TAU * ph) + 0.2 * Math.sin(TAU * 2.01 * ph)) * e * g * 0.06; put(MUS, i, v * 0.8, v); put(MUSV, i, v * 0.9, v * 0.9); } };
  api.piano = (t, m, vel = 0.7, o = {}) => { const i0 = I(t), f = mtof(m), B = 0.00035, len = Math.round((o.len ?? 5.5) * SR), pan = o.pan ?? 0, parts = [];
    for (let k = 1; k <= 12; k++) { const fk = f * k * Math.sqrt(1 + B * k * k); if (fk > 15000) break; parts.push({ f: fk, a: Math.pow(k, -1.25) * (k === 1 ? 1 : 0.8), d: 1 / (0.35 + 0.45 * k), ph: R() }); }
    const lp = bq().set('lp', 2500 + 3000 * vel);
    for (let n = 0; n < len; n++) { const i = i0 + n; if (i >= N) break; const tt = n / SR; let v = 0;
      for (const p of parts) v += p.a * Math.sin(TAU * (p.ph + p.f * tt)) * Math.exp(-tt / (p.d * (o.sus ?? 2.2)));
      if (n < 0.004 * SR) v += nz() * 0.4 * (1 - n / (0.004 * SR));
      v = lp.run(v) * Math.min(1, tt / 0.002) * vel * 0.11; put(MUS, i, v * (1 - pan) * 0.9, v * (1 + pan) * 0.9); put(MUSV, i, v * 0.8, v * 0.8); } };
  api.arp = (t0, t1, notes, step = 0.3, vel = 0.35, o = {}) => { for (let k = 0, t = t0; t < t1; t += step, k++) api.piano(t, notes[k % notes.length], vel * (o.grow ? 0.6 + 0.4 * (t - t0) / (t1 - t0) : 1), { len: 2.5, sus: 1.4, pan: k % 2 ? 0.25 : -0.25 }); };
  api.boom = (t, g = 1, o = {}) => { const i0 = I(t), len = Math.round((o.len ?? 3) * SR), lp = bq().set('lp', 180), hp = bq().set('hp', 2500); let ph = 0;
    for (let n = 0; n < len; n++) { const tt = n / SR, i = i0 + n; if (i >= N) break; ph += (32 + 40 * Math.exp(-tt / 0.09)) / SR;
      const v = (Math.tanh(1.6 * Math.sin(TAU * ph)) * Math.exp(-tt / (o.d ?? 1.1)) * 0.9 + lp.run(nz()) * Math.exp(-tt / 0.4) * 2.2 + hp.run(nz()) * Math.exp(-tt / 0.18) * 0.12) * g * 0.42 * Math.min(1, tt / 0.003);
      put(MUS, i, v, v); put(MUSV, i, v * 0.35, v * 0.35); } };
  api.thud = (t, g = 1) => api.boom(t, g * 0.7, { len: 1.4, d: 0.35 });
  api.riser = (t0, t1, g = 1) => { const i0 = I(t0), i1 = I(t1), bp = bq(), bp2 = bq(), o = saw();
    for (let i = Math.max(0, i0); i < i1 && i < N; i++) { const u = (i - i0) / (i1 - i0), n = i - i0;
      if ((n & 31) === 0) { bp.set('bp', 300 + 5000 * u * u, 2.5); bp2.set('bp', 320 + 5200 * u * u, 2.5); }
      const e = Math.pow(u, 2.2) * g * 0.5, s = o(110 * Math.pow(4, u)) * 0.05 * u; put(MUS, i, (bp.run(nz()) + s) * e, (bp2.run(nz()) + s) * e); } };
  api.ostinato = (t0, t1, seq, bpm = 100, g = 1, o = {}) => { const step = 60 / bpm / 2; let k = 0;
    for (let t = t0; t < t1; t += step, k++) { const m = seq[k % seq.length], i0 = I(t), len = Math.round(step * 0.9 * SR), osc = saw(), osc2 = saw(), lp = bq().set('lp', o.cut ?? 900, 1.2);
      const acc = k % 4 === 0 ? 1 : 0.72, ramp = o.ramp ? 0.55 + 0.45 * (t - t0) / (t1 - t0) : 1;
      for (let n = 0; n < len; n++) { const i = i0 + n, tt = n / SR; if (i >= N) break; const f = mtof(m), e = Math.min(1, tt / 0.012) * Math.exp(-tt / (step * 0.55));
        const v = lp.run(osc(f) + 0.6 * osc2(f * 1.005)) * e * g * acc * ramp * 0.06; put(MUS, i, v * 0.9, v); put(MUSV, i, v * 0.4, v * 0.4); } } };
  const thudSoft = (t, g) => { const i0 = I(t), len = Math.round(0.35 * SR); let ph = 0;
    for (let n = 0; n < len; n++) { const i = i0 + n, tt = n / SR; if (i >= N) break; ph += (48 + 25 * Math.exp(-tt / 0.03)) / SR; const v = Math.sin(TAU * ph) * Math.exp(-tt / 0.11) * g * 0.3; put(MUS, i, v, v); } };
  api.heartbeat = (t0, t1, period = 0.8, g = 1) => { for (let t = t0; t < t1; t += period) { thudSoft(t, g); thudSoft(t + 0.17 * period / 0.78, g * 0.6); } };
  api.whum = (t, g = 0.5) => { const i0 = I(t), len = Math.round(0.9 * SR), bp = bq().set('bp', 600, 0.8); let ph = 0;
    for (let n = 0; n < len; n++) { const i = i0 + n, tt = n / SR; if (i >= N) break; ph += (95 - 25 * tt) / SR; const e = env(tt, 0.02, 0.22);
      const v = (Math.sin(TAU * ph) * 0.9 + bp.run(nz()) * 0.3) * e * g * 0.35; put(MUS, i, v, v); put(MUSV, i, v * 0.6, v * 0.6); } };
  // ---------------------------------------------------------------- sound effects
  api.wind = (t0, t1, g = 1, o = {}) => { const i0 = I(t0), i1 = I(t1), A = o.fade ?? 1.5, b1 = bq(), b2 = bq(), lp = bq().set('lp', 220), lp2 = bq().set('lp', 230), mu = bq().set('lp', o.muffle ?? 20000), mu2 = bq().set('lp', o.muffle ?? 20000);
    for (let i = Math.max(0, i0), n = i - i0; i < i1 && i < N; i++, n++) { const t = n / SR, T = (i1 - i0) / SR;
      const gust = 0.55 + 0.45 * Math.sin(TAU * 0.13 * t + 1) * Math.sin(TAU * 0.07 * t + 2), e = sm(t / A) * sm((T - t) / A) * g * gust;
      if ((n & 63) === 0) { const c = 500 + 700 * gust; b1.set('bp', c, 1.4); b2.set('bp', c * 1.08, 1.4); }
      put(SFX, i, mu.run(b1.run(nz()) * 0.9 + lp.run(nz()) * 2.2) * e * 0.25, mu2.run(b2.run(nz()) * 0.9 + lp2.run(nz()) * 2.2) * e * 0.25); } };
  api.rumble = (t0, t1, g = 1) => { const i0 = I(t0), i1 = I(t1), lp = bq().set('lp', 90), lp2 = bq().set('lp', 95);
    for (let i = Math.max(0, i0); i < i1 && i < N; i++) { const t = (i - i0) / SR, T = (i1 - i0) / SR, e = sm(t / 0.8) * sm((T - t) / 0.8) * g; put(SFX, i, lp.run(nz()) * 2 * e, lp2.run(nz()) * 2 * e); } };
  api.rain = (t0, t1, g = 1) => { const i0 = I(t0), i1 = I(t1), hp = bq().set('hp', 1200), hp2 = bq().set('hp', 1300), lp = bq().set('lp', 7000), r = rng(5);
    for (let i = Math.max(0, i0); i < i1 && i < N; i++) { const t = (i - i0) / SR, T = (i1 - i0) / SR, e = sm(t / 1.2) * sm((T - t) / 1.2) * g;
      const drop = r() < 0.004 ? (r() * 2 - 1) * 1.5 : 0; put(SFX, i, lp.run(hp.run(nz()) * 0.35 + drop) * e * 0.3, hp2.run(nz()) * 0.35 * e * 0.3); } };
  api.fire = (t0, t1, g = 1) => { const i0 = I(t0), i1 = I(t1), lp = bq().set('lp', 600), r = rng(9);
    for (let i = Math.max(0, i0); i < i1 && i < N; i++) { const t = (i - i0) / SR, T = (i1 - i0) / SR, e = sm(t / 1) * sm((T - t) / 1) * g;
      const crack = r() < 0.0012 ? (r() * 2 - 1) * 3 : 0; const v = (lp.run(nz()) * 0.8 + crack) * e * 0.25; put(SFX, i, v, v * 0.9); } };
  api.crowd = (t0, t1, g = 0.3) => { const i0 = I(t0), i1 = I(t1), b = [bq().set('bp', 380, 1.5), bq().set('bp', 900, 1.8), bq().set('bp', 1500, 2)];
    for (let i = Math.max(0, i0); i < i1 && i < N; i++) { const t = (i - i0) / SR, T = (i1 - i0) / SR; let v = 0; b.forEach((f, k) => { v += f.run(nz()) * (0.6 + 0.4 * Math.sin(TAU * (2.5 + k * 1.3) * t + k)); });
      v *= sm(t / 0.5) * sm((T - t) / 0.5) * g * 0.35; put(SFX, i, v, v * 0.95); } };
  api.hum = (t0, t1, f, g, o = {}) => { const i0 = I(t0), i1 = I(t1); let ph = 0;
    for (let i = Math.max(0, i0); i < i1 && i < N; i++) { const t = (i - i0) / SR, T = (i1 - i0) / SR, e = sm(t / (o.attack ?? 1)) * sm((T - t) / (o.release ?? 1)) * (o.rise ? Math.min(1, t / T * 1.4) : 1);
      ph += f * (o.rise ? 0.8 + 0.2 * Math.min(1, t / T * 1.5) : 1) / SR; const v = (Math.sin(TAU * ph) + 0.4 * Math.sin(TAU * 2 * ph) + 0.2 * Math.sin(TAU * 3 * ph)) * e * g * 0.12; put(SFX, i, v, v); } };
  const clack = (t, g, muffle) => { const i0 = I(t), len = Math.round(0.12 * SR), hp = bq().set('hp', 900), lp = bq().set('lp', muffle); let ph = 0;
    for (let n = 0; n < len; n++) { const i = i0 + n, tt = n / SR; if (i >= N) break; ph += 95 / SR;
      const v = lp.run(hp.run(nz()) * Math.exp(-tt / 0.012) * 0.8 + Math.sin(TAU * ph) * Math.exp(-tt / 0.045) * 0.9) * g; put(SFX, i, v * 0.95, v); } };
  const chuff = (t, g, muffle) => { const i0 = I(t), len = Math.round(0.3 * SR), bp = bq().set('bp', 900, 0.7), lp = bq().set('lp', muffle);
    for (let n = 0; n < len; n++) { const i = i0 + n, tt = n / SR; if (i >= N) break; const v = lp.run(bp.run(nz())) * env(tt, 0.01, 0.07) * g; put(SFX, i, v, v * 0.95); } };
  api.train = (t0, t1, g = 1, o = {}) => { const speed = o.speed ?? (() => 1), muffle = o.muffle ?? 9000, A = o.fade ?? 0.8, B = o.fadeOut ?? A, i0 = I(t0), i1 = I(t1), lp = bq().set('lp', 110), lp2 = bq().set('lp', 115);
    for (let i = Math.max(0, i0), n = i - i0; i < i1 && i < N; i++, n++) { const t = n / SR, T = (i1 - i0) / SR, e = sm(t / A) * sm((T - t) / B) * g * (0.4 + 0.6 * speed(t0 + t)); put(SFX, i, lp.run(nz()) * 1.6 * e, lp2.run(nz()) * 1.6 * e); }
    let pos = 0, joint = 0, ch = 0;
    for (let t = t0; t < t1; t += 0.005) { const s = speed(t); pos += s * 0.005; const lvl = sm((t - t0) / A) * sm((t1 - t) / B) * g;
      if (pos >= joint) { if (lvl > 0.001) { clack(t, lvl * 0.5, muffle); clack(t + 0.13 / Math.max(0.3, s), lvl * 0.42, muffle); } joint += o.joint ?? 1.15; }
      if (pos >= ch) { if (lvl > 0.001) chuff(t, lvl * 0.22 * s, muffle * 0.6); ch += o.chuff ?? 0.31; } } };
  api.relay = (t, g = 0.4) => { const i0 = I(t), len = Math.round(0.05 * SR), bp = bq().set('bp', 1800, 1.5);
    for (let n = 0; n < len; n++) { const v = bp.run(nz()) * Math.exp(-n / SR / 0.006) * g * 0.5; put(SFX, i0 + n, v, v); } };
  api.rustle = (t0, t1, g = 0.5) => { const r = rng(Math.round(t0 * 100) + 7), bp = bq().set('bp', 3200, 0.8);
    for (let t = t0; t < t1; t += 0.01 + r() * 0.03) { const i0 = I(t), len = Math.round((0.01 + r() * 0.04) * SR), a = r() * g * sm((t - t0) / 0.1) * sm((t1 - t) / 0.15);
      for (let n = 0; n < len; n++) { const v = bp.run(nz()) * a * (1 - n / len) * 0.4; put(SFX, i0 + n, v, v * (0.7 + 0.3 * r())); } } };
  api.scrape = (t0, t1, g = 0.5) => { const i0 = I(t0), i1 = I(t1), bp = bq().set('bp', 700, 2), bp2 = bq().set('bp', 1450, 4);
    for (let i = Math.max(0, i0); i < i1 && i < N; i++) { const u = (i - i0) / (i1 - i0), grit = R() < 0.02 ? 1.8 : 1, v = (bp.run(nz()) + 0.5 * bp2.run(nz())) * grit * Math.sin(Math.PI * u) * g * 0.5; put(SFX, i, v, v); } };
  api.clunk = (t, g = 0.7, o = {}) => { const i0 = I(t), len = Math.round(0.6 * SR), lp = bq().set('lp', 900), fs_ = o.f ?? [92, 310, 540], ph = fs_.map(() => 0);
    for (let n = 0; n < len; n++) { const i = i0 + n, tt = n / SR; if (i >= N) break; let v = lp.run(nz()) * Math.exp(-tt / 0.03) * 1.2;
      fs_.forEach((f, k) => { ph[k] += f / SR; v += Math.sin(TAU * ph[k]) * Math.exp(-tt / (k ? 0.08 : 0.16)) * (k ? 0.35 : 0.9); });
      v *= g * 0.45; put(SFX, i, v, v); put(SFXV, i, v * 0.4, v * 0.4); } };
  api.glass = (t, g = 0.5) => { const r = rng(4242), hp = bq().set('hp', 2500);
    for (let n = 0; n < 0.35 * SR; n++) { const v = hp.run(nz()) * Math.exp(-n / SR / 0.09) * g * 0.6; put(SFX, I(t) + n, v, v); put(SFXV, I(t) + n, v * 0.3, v * 0.3); }
    for (let k = 0; k < 26; k++) { const tt = t + Math.pow(r(), 1.8) * 0.7, f = 2800 + r() * 6500, d = 0.02 + r() * 0.09, a = (0.15 + r() * 0.3) * g, pan = r() * 2 - 1; let ph = 0;
      for (let n = 0; n < d * 5 * SR; n++) { ph += f / SR; const v = Math.sin(TAU * ph) * Math.exp(-n / SR / d) * a * 0.25; put(SFX, I(tt) + n, v * (1 - pan * 0.6), v * (1 + pan * 0.6)); } } };
  api.screech = (t0, t1, g = 0.5) => { const i0 = I(t0), i1 = I(t1), fs_ = [1850, 2730, 3920, 5100], ph = fs_.map(() => 0), bp = bq().set('bp', 4200, 1.2), r = rng(99); let wob = 0, wt = 0;
    for (let i = Math.max(0, i0); i < i1 && i < N; i++) { const t = (i - i0) / SR, T = (i1 - i0) / SR, e = sm(t / 0.25) * sm((T - t) / 0.5);
      if ((i & 255) === 0) wt = (r() * 2 - 1) * 0.02; wob += (wt - wob) * 0.0008; let v = 0;
      fs_.forEach((f, k) => { ph[k] += f * (1 + wob * (k + 1) - 0.05 * t / T) / SR; v += Math.sin(TAU * ph[k]) * [0.5, 0.35, 0.22, 0.12][k]; });
      v = (v * (0.6 + 0.4 * Math.abs(Math.sin(TAU * 31 * t + Math.sin(TAU * 7 * t)))) + bp.run(nz()) * 0.5) * e * g * 0.22; put(SFX, i, v, v * 0.9); put(SFXV, i, v * 0.5, v * 0.5); } };
  api.shudder = (t0, t1, g = 0.7) => { const i0 = I(t0), i1 = I(t1), lp = bq().set('lp', 90), o = saw(), bp = bq().set('bp', 260, 3);
    for (let i = Math.max(0, i0); i < i1 && i < N; i++) { const t = (i - i0) / SR, T = (i1 - i0) / SR, e = sm(t / 0.15) * Math.pow(1 - t / T, 1.3) * g * (0.6 + 0.4 * Math.sin(TAU * 9 * t));
      const v = (lp.run(nz()) * 3 + bp.run(o(68 + 6 * Math.sin(TAU * 3 * t))) * 0.6) * e * 0.4; put(SFX, i, v, v); } };
  api.hiss = (t0, d, g = 0.4) => { const i0 = I(t0), len = Math.round(d * SR), hp = bq().set('hp', 2200), hp2 = bq().set('hp', 2300);
    for (let n = 0; n < len; n++) { const i = i0 + n, tt = n / SR; if (i >= N) break; const e = Math.min(1, tt / 0.05) * Math.pow(1 - tt / d, 1.5) * g * 0.35; put(SFX, i, hp.run(nz()) * e, hp2.run(nz()) * e); } };
  api.whoosh = (t0, d, g = 0.3) => { const i0 = I(t0), len = Math.round(d * SR), bp = bq(), bp2 = bq();
    for (let n = 0; n < len; n++) { const u = n / len; if ((n & 31) === 0) { bp.set('bp', 300 + 2500 * Math.sin(Math.PI * u), 1.2); bp2.set('bp', 320 + 2600 * Math.sin(Math.PI * u), 1.2); }
      const e = Math.sin(Math.PI * u) ** 2 * g * 0.5; put(SFX, i0 + n, bp.run(nz()) * e * (1 - u * 0.5), bp2.run(nz()) * e * (0.5 + u * 0.5)); } };
  api.crunch = (t, g = 0.4, f = 2200) => { const i0 = I(t), len = Math.round(0.22 * SR), bp = bq().set('bp', f, 0.9), r = rng(Math.round(t * 1000) + 3);
    for (let n = 0; n < len; n++) { const tt = n / SR, imp = r() < 0.08 ? (r() * 2 - 1) * 3 : 0; const v = bp.run(nz() * 0.5 + imp) * env(tt, 0.008, 0.07) * g * 0.35; put(SFX, i0 + n, v, v); } };
  api.steps = (times, g = 0.4, o = {}) => { const f = { frost: 2200, snow: 1800, stone: 900, wood: 500, gravel: 2600 }[o.surface || 'frost'] || 2000; for (const t of times) api.crunch(t, g, f); };
  api.creak = (t0, d, g = 0.4) => { const i0 = I(t0), len = Math.round(d * SR), o = saw(), bp = bq().set('bp', 900, 6);
    for (let n = 0; n < len; n++) { const tt = n / SR, f = 120 + 60 * Math.sin(Math.PI * tt / d) + 8 * Math.sin(TAU * 23 * tt), e = Math.sin(Math.PI * tt / d) * (R() < 0.3 ? 1 : 0.75);
      const v = bp.run(o(f)) * e * g * 0.3; put(SFX, i0 + n, v, v); put(SFXV, i0 + n, v * 0.3, v * 0.3); } };
  api.chirp = (t, f0, f1, d, g) => { const i0 = I(t), len = Math.round(d * SR); let ph = 0;
    for (let n = 0; n < len; n++) { const u = n / len, f = f0 + (f1 - f0) * u; ph += f / SR; const e = Math.sin(Math.PI * u) ** 1.5;
      const v = (Math.sin(TAU * ph) + 0.25 * Math.sin(TAU * 2 * ph)) * e * g * 0.12; put(SFX, i0 + n, v * 0.8, v); put(SFXV, i0 + n, v * 0.6, v * 0.6); } };
  api.birdsong = (t0, t1, g = 0.5) => { const r = rng(31); let t = t0;
    while (t < t1) { const kind = r(), notes = 3 + Math.floor(r() * 5);
      for (let k = 0; k < notes; k++) { const f0 = 2600 + r() * 2200, up = r() < 0.5; if (kind < 0.5) api.chirp(t, f0, up ? f0 * 1.45 : f0 * 0.7, 0.05 + r() * 0.04, g); else api.chirp(t, f0 * 1.2, f0 * 0.9, 0.03, g * 0.8); t += kind < 0.5 ? 0.09 + r() * 0.05 : 0.045; }
      t += 0.5 + r() * 1.2; } };
  api.silence = (t0, t1) => SIL.push([t0, t1]);
  api.duck = (s, x) => { duckS = s; duckX = x; };
  api.chord = chord; api.midi = midi;
  // ---------------------------------------------------------------- render
  function reverb(src, room, damp) {
    const combs = [1557, 1617, 1491, 1422, 1277, 1356, 1188, 1116].map((n) => Math.round(n * SR / 44100)), aps = [556, 441, 341, 225].map((n) => Math.round(n * SR / 44100)), out = bus();
    for (let ch = 0; ch < 2; ch++) { const x = src[ch], y = out[ch], sp = ch ? 23 : 0;
      const cb = combs.map((n) => ({ b: new Float32Array(n + sp), i: 0, f: 0 })), ab = aps.map((n) => ({ b: new Float32Array(n + sp), i: 0 }));
      for (let i = 0; i < N; i++) { const inp = x[i] * 0.015; let s = 0;
        for (const c of cb) { const o = c.b[c.i]; c.f = o * (1 - damp) + c.f * damp; c.b[c.i] = inp + c.f * room; c.i = (c.i + 1) % c.b.length; s += o; }
        for (const a of ab) { const o = a.b[a.i]; const v = -s + o; a.b[a.i] = s + o * 0.5; a.i = (a.i + 1) % a.b.length; s = v; }
        y[i] = s; } }
    return out;
  }
  function wav(path, b) { const buf = Buffer.alloc(44 + N * 6); buf.write('RIFF', 0); buf.writeUInt32LE(36 + N * 6, 4); buf.write('WAVEfmt ', 8); buf.writeUInt32LE(16, 16);
    buf.writeUInt16LE(1, 20); buf.writeUInt16LE(2, 22); buf.writeUInt32LE(SR, 24); buf.writeUInt32LE(SR * 6, 28); buf.writeUInt16LE(6, 32); buf.writeUInt16LE(24, 34); buf.write('data', 36); buf.writeUInt32LE(N * 6, 40);
    let o = 44; for (let i = 0; i < N; i++) for (let ch = 0; ch < 2; ch++) { const v = Math.round(Math.max(-1, Math.min(1, b[ch][i])) * 8388607); buf.writeIntLE(v, o, 3); o += 3; }
    fs.writeFileSync(path, buf); }
  api.render = ({ voice, scorePath, sfxPath, scorePeak = -19, sfxPeak = -15, music = null }) => {
    const mv = reverb(MUSV, 0.88, 0.35), sv = reverb(SFXV, 0.75, 0.4);
    const duck = new Float32Array(N);                                   // the voice as a side-chain (film clock)
    if (voice) { let lev = 0; for (let i = 0; i < N; i++) { const vi = Math.round((i / SR - pre) * voice.sr); const x = vi >= 0 && vi < voice.data.length ? Math.abs(voice.data[vi]) : 0;
      lev = x > lev ? lev + (x - lev) * 0.002 : lev + (x - lev) * 0.00004; duck[i] = Math.min(1, lev / 0.06); } }
    for (const [a, b] of SIL) for (let ch = 0; ch < 2; ch++) for (let i = Math.max(0, I(a)); i < Math.min(N, I(b)); i++) { const u = Math.min(1, (i - I(a)) / (0.25 * SR)); mv[ch][i] *= 1 - u; MUS[ch][i] = 0; }
    const finish = (dry, wet, duckDb, peakDb) => { const o = bus(); let pk = 1e-9;
      for (let ch = 0; ch < 2; ch++) for (let i = 0; i < N; i++) { const v = (dry[ch][i] + wet[ch][i]) * db(-duckDb * duck[i]); o[ch][i] = v; pk = Math.max(pk, Math.abs(v)); }
      const k = db(peakDb) / pk; for (let ch = 0; ch < 2; ch++) for (let i = 0; i < N; i++) o[ch][i] *= k; return o; };
    if (!music) wav(scorePath, finish(MUS, mv, duckS, scorePeak));
    wav(sfxPath, finish(SFX, sv, duckX, sfxPeak));
  };
  return api;
}
