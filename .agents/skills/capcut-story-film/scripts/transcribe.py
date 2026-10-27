#!/usr/bin/env python3
"""Word timings for the narration -> qa/words.json  [{"w": "Never", "s": 31.85, "e": 32.40}, ...]  (narration clock)

  python3 scripts/transcribe.py <project> [--engine auto|whisper-dtw|hyperframes] [--model small.en]

Engines:
  whisper-dtw   whisper.cpp (`whisper-cli`) with DTW token timestamps: the most exact. Used automatically when whisper-cli
                and a ggml model (~/.cache/whisper-models/ggml-<model>.bin or $WHISPER_MODEL) are installed.
  hyperframes   `npx hyperframes transcribe` (no extra install). Its word starts are looser, so they are refined.
Refinement (both): any word that follows >= 120 ms of quiet snaps to the measured acoustic onset (level rising 18 dB over
the noise floor) within -0.30/+0.12 s (whisper-dtw) or -0.45/+0.35 s (hyperframes); bunched words are respread by length;
a word ends where the next starts or where the level falls back to quiet.
Check the result: the script prints the transcript; fix misheard names in qa/words.json by hand (keep the times).
"""
import argparse, json, os, shutil, subprocess, sys
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import Project, save, die

ap = argparse.ArgumentParser(); ap.add_argument('project'); ap.add_argument('--engine', default='auto'); ap.add_argument('--model', default='small.en')
a = ap.parse_args()
P = Project(a.project); voice = P.p(P.cfg['narration']); qa = P.p('qa'); os.makedirs(qa, exist_ok=True)
HF = os.environ.get('HF_VERSION', '0.7.109')

model = os.environ.get('WHISPER_MODEL') or os.path.expanduser(f'~/.cache/whisper-models/ggml-{a.model}.bin')
engine = a.engine
if engine == 'auto': engine = 'whisper-dtw' if shutil.which('whisper-cli') and os.path.exists(model) else 'hyperframes'

wav16 = os.path.join(qa, 'narration-16k.wav')
subprocess.run(['ffmpeg', '-v', 'error', '-y', '-i', voice, '-ar', '16000', '-ac', '1', wav16], check=True)
raw = subprocess.run(['ffmpeg', '-v', 'error', '-i', voice, '-f', 's16le', '-ac', '1', '-ar', '16000', '-'], capture_output=True, check=True).stdout
x = np.frombuffer(raw, np.int16).astype(np.float32) / 32768
hop = 160; n = len(x) // hop
db = 20 * np.log10(np.sqrt((x[:n * hop].reshape(n, hop) ** 2).mean(axis=1)) + 1e-9)
floor = np.percentile(db, 10); loud = db >= floor + 18
onsets = np.array([i * 0.01 for i in range(15, n) if loud[i] and not loud[i - 15:i].any()])

words = []
if engine == 'whisper-dtw':
    base = os.path.join(qa, 'whisper-dtw')
    dtw = os.path.basename(model).replace('ggml-', '').replace('.bin', '')
    subprocess.run(['whisper-cli', '-m', model, '-f', wav16, '-ml', '1', '-sow', '-ojf', '-of', base, '--dtw', dtw, '-nfa', '-np'], check=True, capture_output=True)
    for seg in json.load(open(base + '.json'))['transcription']:
        toks = [t for t in seg.get('tokens', []) if not t['text'].startswith('[')]
        if not seg['text'].strip() or not toks: continue
        s = toks[0]['t_dtw'] / 100 - 0.07                      # DTW starts run ~0.07 s late
        if seg['text'].startswith(' ') or not words: words.append({'w': seg['text'].strip(), 's': s})
        else: words[-1]['w'] += seg['text'].strip()
    win = (-0.30, 0.12)
else:
    r = subprocess.run(['npx', '-y', f'hyperframes@{HF}', 'transcribe', voice, '--json', '-d', qa], capture_output=True, text=True)
    if r.returncode: die('hyperframes transcribe failed:\n' + r.stderr[-1500:])
    for w in json.load(open(os.path.join(qa, 'transcript.json'))):
        if w.get('text', '').strip(): words.append({'w': w['text'].strip(), 's': float(w['start'])})
    win = (-0.45, 0.35)
if not words: die('no words found in the narration')

snapped = 0
for w in words:
    near = onsets[(onsets >= w['s'] + win[0]) & (onsets <= w['s'] + win[1])]
    if len(near): w['s'] = float(near[np.argmin(np.abs(near - w['s']))]); snapped += 1
for i in range(1, len(words)):
    if words[i]['s'] <= words[i - 1]['s']: words[i]['s'] = words[i - 1]['s'] + 0.02
i = 0                                                          # spread runs that DTW bunched into ~40 ms
while i < len(words) - 1:
    j = i
    while j + 1 < len(words) - 1 and words[j + 1]['s'] - words[j]['s'] < 0.06: j += 1
    if j > i:
        A, B = words[i]['s'], words[j + 1]['s']
        if 0 < B - A < 2.5:
            L = [max(2, len(w['w'])) for w in words[i:j + 1]]; tot = sum(L); acc = 0
            for k in range(i, j + 1): words[k]['s'] = A + (B - A) * acc / tot; acc += L[k - i]
    i = j + 1
for i, w in enumerate(words):
    nxt = words[i + 1]['s'] if i + 1 < len(words) else w['s'] + 0.6
    k0, k1 = int(w['s'] * 100), int(nxt * 100)
    q = next((k for k in range(k0 + 8, min(k1, k0 + 120)) if not loud[k:k + 12].any()), None)
    w['e'] = round(min(nxt, q * 0.01 if q else nxt), 3); w['s'] = round(w['s'], 3)
save(P.p('qa/words.json'), words)
print(f'{engine}: {len(words)} words, {snapped} snapped to measured onsets -> qa/words.json')
line = []
for w in words:
    line.append(f"{w['w']}@{w['s']:.2f}")
    if w['w'][-1] in '.?!': print('  ' + ' '.join(line)); line = []
if line: print('  ' + ' '.join(line))
