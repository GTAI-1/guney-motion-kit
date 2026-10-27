// Render a film's sound from its cue sheet:  node scripts/score/run.mjs <project>
// Loads <project>/plan/cue.mjs (export default function (s) { ... }), gives it the engine API plus time helpers that
// understand the same references as the plan files, renders renders/audio/score.wav (skipped when project.json has
// "music": the user's own track is prepared by scripts/music_bed.py instead) and renders/audio/sfx.wav.
//   s.t('w:idea'), s.t('s12+0.4'), s.t('e30')       time references (narration clock)
//   s.words, s.scenes                                the transcript and the scene table
//   s.END                                            last scene's end;  s.PRE  pre-roll seconds
import fs from 'node:fs';
import path from 'node:path';
import { pathToFileURL } from 'node:url';
import { createScore } from './engine.mjs';
const root = path.resolve(process.argv[2] || '.');
const cfg = JSON.parse(fs.readFileSync(path.join(root, 'project.json'), 'utf8'));
const words = JSON.parse(fs.readFileSync(path.join(root, 'qa/words.json'), 'utf8'));
const scenes = Object.fromEntries(JSON.parse(fs.readFileSync(path.join(root, 'plan/scenes.json'), 'utf8')).map((s) => [s.scene, s]));
const norm = (w) => w.toLowerCase().replace(/’/g, "'").replace(/[^a-z0-9']/g, '');
function t(ref) {
  if (typeof ref === 'number') return ref;
  const s = String(ref).trim(); if (!isNaN(+s)) return +s;
  let m = /^([se])(\d+)([+-][\d.]+)?$/.exec(s);
  if (m) { const sc = scenes[+m[2]]; if (!sc) throw new Error(`no scene ${m[2]}`); return (m[1] === 's' ? sc.start : sc.end) + +(m[3] || 0); }
  m = /^w:([A-Za-z0-9']+)(?:#(\d+))?(?:@([\d.]+))?(\.end)?([+-][\d.]+)?$/.exec(s);
  if (m) { const hits = words.filter((w) => norm(w.w) === norm(m[1]) && w.s >= +(m[3] ?? -1e9) - 1e-6); const w = hits[(+m[2] || 1) - 1];
    if (!w) throw new Error(`word "${m[1]}" not found (${s})`); return (m[4] ? w.e : w.s) + +(m[5] || 0); }
  throw new Error(`cannot read time reference ${s}`);
}
const END = Math.max(...Object.values(scenes).map((s) => s.end));
const layersFile = path.join(root, 'plan/layers.resolved.json');
const tailLayers = fs.existsSync(layersFile) ? Math.max(0, ...JSON.parse(fs.readFileSync(layersFile, 'utf8')).layers.map((l) => l.t0 + l.dur)) : 0;
const length = Math.max(END, tailLayers) + cfg.pre + 2.5;
const S = createScore({ length, pre: cfg.pre });
const cue = (await import(pathToFileURL(path.join(root, 'plan/cue.mjs')).href)).default;
await cue({ ...S, t, words, scenes, END, PRE: cfg.pre, music: !!cfg.music });
// the voice for ducking
const raw = fs.readFileSync(path.join(root, cfg.narration)); let off = 12, data = null, sr = 48000, ch = 1, bits = 16;
while (off < raw.length - 8) { const id = raw.toString('ascii', off, off + 4), sz = raw.readUInt32LE(off + 4);
  if (id === 'fmt ') { ch = raw.readUInt16LE(off + 10); sr = raw.readUInt32LE(off + 12); bits = raw.readUInt16LE(off + 22); }
  if (id === 'data') { const n = Math.floor(sz / (bits / 8) / ch); data = new Float32Array(n);
    for (let i = 0; i < n; i++) data[i] = bits === 16 ? raw.readInt16LE(off + 8 + i * 2 * ch) / 32768 : bits === 24 ? raw.readIntLE(off + 8 + i * 3 * ch, 3) / 8388608 : raw.readFloatLE(off + 8 + i * 4 * ch); break; }
  off += 8 + sz + (sz & 1); }
fs.mkdirSync(path.join(root, 'renders/audio'), { recursive: true });
S.render({ voice: data ? { data, sr } : null, scorePath: path.join(root, 'renders/audio/score.wav'), sfxPath: path.join(root, 'renders/audio/sfx.wav'), music: cfg.music });
console.log(`sound rendered: ${length.toFixed(2)} s (film clock) -> renders/audio/${cfg.music ? '' : 'score.wav + '}sfx.wav`);
