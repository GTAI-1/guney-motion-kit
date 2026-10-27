// SFX-only mix (no music bed): place cues, sum without normalisation, set the peak to -9 dBFS.
// Usage: node plan/sfxmix.mjs <events.json> <length> <out.wav> [raw]   (raw: no normalisation, the cue gains are absolute)
import { spawnSync } from 'node:child_process';
import { readFileSync } from 'node:fs';
const [evf, len, out, mode] = process.argv.slice(2), events = JSON.parse(readFileSync(evf, 'utf8'));
const inputs = ['-f', 'lavfi', '-t', len, '-i', 'anullsrc=r=48000:cl=stereo'], parts = [], labels = ['[0:a]'];
events.forEach((e, i) => { inputs.push('-i', e.file); const ms = Math.round(e.t * 1000);
  const trim = e.max ? `atrim=0:${e.max},afade=t=out:st=${Math.max(0, e.max - 0.05)}:d=0.05,` : '';
  parts.push(`[${i + 1}:a]aresample=48000,aformat=channel_layouts=stereo,${trim}volume=${e.gain},adelay=${ms}|${ms}[e${i}]`); labels.push(`[e${i}]`); });
parts.push(`${labels.join('')}amix=inputs=${labels.length}:normalize=0:duration=first,atrim=0:${len}[m]`);
const tmp = out.replace(/\.wav$/, '.raw.wav');
let r = spawnSync('ffmpeg', ['-v', 'error', '-y', ...inputs, '-filter_complex', parts.join(';'), '-map', '[m]', '-c:a', 'pcm_s24le', tmp], { encoding: 'utf8' });
if (r.status) { console.error(r.stderr); process.exit(1); }
r = spawnSync('ffmpeg', ['-v', 'info', '-i', tmp, '-af', 'volumedetect', '-f', 'null', '-'], { encoding: 'utf8' });
const peak = +(/max_volume: (-?[\d.]+) dB/.exec(r.stderr) || [0, 0])[1], gain = mode === 'raw' ? 0 : -9 - peak;
r = spawnSync('ffmpeg', ['-v', 'error', '-y', '-i', tmp, '-af', `volume=${gain}dB`, '-c:a', 'pcm_s24le', out], { encoding: 'utf8' });
spawnSync('rm', ['-f', tmp]);
console.log(`${out}: ${events.length} cues, peak ${peak} dB` + (mode === 'raw' ? ' (raw)' : ' -> -9 dBFS'));
