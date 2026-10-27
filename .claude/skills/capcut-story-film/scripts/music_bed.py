#!/usr/bin/env python3
"""Fit the user's own music track to the film -> renders/audio/score.wav (used instead of a composed score)

  python3 scripts/music_bed.py <project> [--start 0] [--gain -14] [--duck 6] [--fade-in 2] [--fade-out 4] [--silence 108.4,118.9]

Trims (or loops) the track to the film length, fades it in and out, ducks it DUCK dB under the narration with a
side-chain compressor, and mutes it inside optional --silence windows (narration clock, e.g. a dramatic stop).
Only use music the user owns or has the right to use.
"""
import argparse, json, os, subprocess, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import Project, die

ap = argparse.ArgumentParser(); ap.add_argument('project'); ap.add_argument('--start', type=float, default=0); ap.add_argument('--gain', type=float, default=-14)
ap.add_argument('--duck', type=float, default=6); ap.add_argument('--fade-in', type=float, default=2); ap.add_argument('--fade-out', type=float, default=4)
ap.add_argument('--silence', action='append', default=[])
a = ap.parse_args(); P = Project(a.project)
if not P.cfg.get('music'): die('project.json has no "music"')
scenes = list(P.scenes.values()); end = max(s['end'] for s in scenes)
lay = json.load(open(P.p('plan/layers.resolved.json')))['layers'] if os.path.exists(P.p('plan/layers.resolved.json')) else []
length = max([end] + [l['t0'] + l['dur'] for l in lay]) + P.pre + 2.5
mute = ''.join(f",volume=enable='between(t,{float(x.split(',')[0]) + P.pre},{float(x.split(',')[1]) + P.pre})':volume=0" for x in a.silence)
th = 10 ** (-a.duck / 20)
fc = (f"[0:a]aresample=48000,aformat=channel_layouts=stereo,atrim=start={a.start},asetpts=PTS-STARTPTS,aloop=loop=-1:size=2e9,atrim=0:{length:.3f},"
      f"volume={a.gain}dB,afade=t=in:st=0:d={a.fade_in},afade=t=out:st={length - a.fade_out:.3f}:d={a.fade_out}{mute}[m];"
      f"[1:a]aresample=48000,aformat=channel_layouts=stereo,adelay={int(P.pre * 1000)}:all=1,apad[v];"
      f"[m][v]sidechaincompress=threshold=0.03:ratio=6:attack=40:release=600:makeup=1[d]")
os.makedirs(P.p('renders/audio'), exist_ok=True)
r = subprocess.run(['ffmpeg', '-v', 'error', '-y', '-i', P.p(P.cfg['music']), '-i', P.p(P.cfg['narration']), '-filter_complex', fc, '-map', '[d]',
                    '-t', f'{length:.3f}', '-c:a', 'pcm_s24le', P.p('renders/audio/score.wav')], capture_output=True, text=True)
if r.returncode: die(r.stderr[-1200:])
print(f'renders/audio/score.wav: {length:.2f} s, {a.gain} dB, ducked {a.duck} dB under the voice')
