#!/usr/bin/env python3
"""Measure the sound before building: per-2-second levels of score, effects and voice (film clock), the integrated
loudness and true peak of the full mix, and renders/soundtrack-preview.mp3 (voice + score + effects) to send early.

  python3 scripts/levels.py <project>

Targets (voice at 0 dB, untouched): under speech the score sits 12-16 dB below the voice, effects 14-18 dB below; in
gaps and at the climax the score may come up to 6-8 dB below the voice level. Silence windows must read -70 dB or less.
"""
import json, os, subprocess, sys
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import Project

P = Project(sys.argv[1] if len(sys.argv) > 1 else '.')
def load(p, delay=0.0):
    x = np.frombuffer(subprocess.run(['ffmpeg', '-v', 'error', '-i', p, '-ac', '1', '-ar', '16000', '-f', 'f32le', '-'], capture_output=True).stdout, np.float32)
    return np.concatenate([np.zeros(int(delay * 16000), np.float32), x])
S, X, V = load(P.p('renders/audio/score.wav')), load(P.p('renders/audio/sfx.wav')), load(P.p(P.cfg['narration']), P.pre)
n = min(len(S), len(X)) // 16000
r = lambda a, i: 20 * np.log10(np.sqrt(np.mean(a[i * 16000:(i + 2) * 16000] ** 2)) + 1e-9) if i * 16000 < len(a) else -99
print('film_s   score    sfx  voice   (dBFS RMS, 2 s windows)')
for i in range(0, n, 2): print(f'{i:6d} {r(S, i):7.1f} {r(X, i):6.1f} {r(V, i):6.1f}')
mix = P.p('qa/mix-preview.wav')
subprocess.run(['ffmpeg', '-v', 'error', '-y', '-i', P.p('renders/audio/score.wav'), '-i', P.p('renders/audio/sfx.wav'), '-i', P.p(P.cfg['narration']), '-filter_complex',
                f"[2:a]aresample=48000,aformat=channel_layouts=stereo,adelay={int(P.pre * 1000)}:all=1[v];[0:a][1:a][v]amix=inputs=3:normalize=0:duration=longest[m]",
                '-map', '[m]', '-c:a', 'pcm_s24le', mix], check=True)
out = subprocess.run(['ffmpeg', '-hide_banner', '-i', mix, '-af', 'ebur128=peak=true', '-f', 'null', '-'], capture_output=True, text=True).stderr
I = [l for l in out.splitlines() if l.strip().startswith('I:')][-1].split()[1]; TP = [l for l in out.splitlines() if l.strip().startswith('Peak:')][-1].split()[1]
subprocess.run(['ffmpeg', '-v', 'error', '-y', '-i', mix, '-c:a', 'libmp3lame', '-b:a', '256k', P.p('renders/soundtrack-preview.mp3')], check=True)
print(f'full mix: {I} LUFS integrated, true peak {TP} dBFS  -> renders/soundtrack-preview.mp3')
print('(YouTube plays at about -14 LUFS; raise the whole mix in CapCut only if the true peak stays under -1 dBFS)')
