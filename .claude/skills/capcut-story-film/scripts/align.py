#!/usr/bin/env python3
"""Lock every scene of the script to the narration -> plan/scenes.json

  python3 scripts/align.py <project> [--lead 0.35] [--tail 3.0]

Reads plan/script.json, a list of scenes in order:
  [{"scene": 1, "narration": "The last train on Earth had been moving for 200 years.", "visual": "...", "camera": "...",
    "sound": "...", "act": "ACT 1: THE WORLD THAT NEVER STOPS"}, ...]
and qa/words.json. The scene texts and the spoken words are aligned as token sequences (the narrator may ad-lib, skip or
say numbers differently; unmatched words are fine). A scene starts LEAD seconds before its first spoken word (scene 1 at 0)
and ends where the next begins; the last scene holds TAIL seconds after the final word (room for the ending).
Prints each scene's start, length and spoken text so you can see the pacing at a glance.
"""
import argparse, difflib, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import Project, load, save, norm, die

ap = argparse.ArgumentParser(); ap.add_argument('project'); ap.add_argument('--lead', type=float, default=0.35); ap.add_argument('--tail', type=float, default=3.0)
a = ap.parse_args()
P = Project(a.project)
script = load(P.p('plan/script.json')); W = P.words
if not W: die('qa/words.json is empty: run transcribe.py first')
NUM = {'zero': '0', 'one': '1', 'two': '2', 'three': '3', 'four': '4', 'five': '5', 'six': '6', 'seven': '7', 'eight': '8', 'nine': '9', 'ten': '10',
       'eleven': '11', 'twelve': '12', 'thirteen': '13', 'fourteen': '14', 'fifteen': '15', 'sixteen': '16', 'seventeen': '17', 'eighteen': '18',
       'nineteen': '19', 'twenty': '20', 'thirty': '30', 'forty': '40', 'fifty': '50', 'hundred': '100', 'thousand': '1000'}
tok = lambda s: [NUM.get(norm(x), norm(x)) for x in s.replace('\u2014', ' ').replace('-', ' ').split() if norm(x)]
st, owner = [], []
for i, sc in enumerate(script):
    t = tok(sc.get('narration', '')); st += t; owner += [i] * len(t)
wt = [NUM.get(norm(w['w']), norm(w['w'])) for w in W]
sm = difflib.SequenceMatcher(None, st, wt, autojunk=False)
m = {}
for b in sm.get_matching_blocks():
    for k in range(b.size): m[b.a + k] = b.b + k
first, last = {}, {}
for si, wi in sorted(m.items()):
    sc = owner[si]; first.setdefault(sc, wi); last[sc] = wi
out, missing = [], []
for i, sc in enumerate(script):
    if i not in first:                                     # a scene with no narration: placed between its neighbours below
        missing.append(sc['scene']); out.append({'scene': sc['scene'], 'start': None, 'first': None, 'last_word_end': None, 'text': ''}); continue
    k0, k1 = first[i], last[i]
    out.append({'scene': sc['scene'], 'start': 0.0 if i == 0 else round(W[k0]['s'] - a.lead, 3), 'first': W[k0]['s'], 'last_word_end': W[k1]['e'],
                'text': ' '.join(w['w'] for w in W[k0:k1 + 1])})
if out[0]['start'] is None: out[0]['start'] = 0.0
for i, s in enumerate(out):
    if s['start'] is None:
        j = next((k for k in range(i + 1, len(out)) if out[k]['start'] is not None), None)
        prev = out[i - 1]['start']; nxt = out[j]['start'] if j is not None else W[-1]['e'] + a.tail
        gap = j - i + 1 if j is not None else len(out) - i + 1
        s['start'] = round(prev + (nxt - prev) / gap, 3)
for i, s in enumerate(out):
    s['end'] = out[i + 1]['start'] if i + 1 < len(out) else round(W[-1]['e'] + a.tail, 3); s['dur'] = round(s['end'] - s['start'], 3)
save(P.p('plan/scenes.json'), out)
for s in out: print(f"{s['scene']:3d} {s['start']:7.2f} {s['dur']:5.2f}s  {s['text'][:90]}")
print(f'{len(out)} scenes, film length {out[-1]["end"] + P.pre:.2f} s (with {P.pre} s pre-roll)')
if missing: print('WARNING: no spoken words matched scenes', missing, '- they have no narration: give them time by hand in edit.json')
