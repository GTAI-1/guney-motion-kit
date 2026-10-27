#!/usr/bin/env python3
"""Check a built CapCut project before opening it:  python3 scripts/verify_capcut.py <project> [--draft "Name"]

Checks (from qa/capcut-build.json, or the named project): every segment on the 30 fps grid at exactly 1x (else CapCut
switches on Pro-only Optical flow); every media file exists and sits under ~/Movies (sandbox); pictures cover the frame
at every keyframe; main track contiguous from 0; no overlaps inside a track; caption lines within the limit; layer files
are transparent-capable (HEVC/ProRes) where they need alpha. Prints OK or the problems, then the in-CapCut checklist.
"""
import argparse, json, os, subprocess, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import Project, load, capcut_root, visible_rect

ap = argparse.ArgumentParser(); ap.add_argument('project'); ap.add_argument('--draft'); a = ap.parse_args()
P = Project(a.project); info = load(P.p('qa/capcut-build.json'), {})
folder = os.path.join(capcut_root(), a.draft) if a.draft else info.get('folder')
if not folder or not os.path.exists(folder): print('project folder not found:', folder); sys.exit(1)
D = json.load(open(os.path.join(folder, 'draft_info.json')))
mats = {m['id']: m for k in ('videos', 'audios', 'texts') for m in D['materials'].get(k, [])}
speeds = {m['id']: m['speed'] for m in D['materials'].get('speeds', [])}
prob, notes = [], []
CW, CH = D['canvas_config']['width'], D['canvas_config']['height']
movies = os.path.realpath(os.path.expanduser('~/Movies'))
for n, t in enumerate(D['tracks']):
    segs = sorted(t['segments'], key=lambda s: s['target_timerange']['start'])
    for s in segs:
        tr, sr = s['target_timerange'], s.get('source_timerange')
        f = tr['start'] * 30 / 1e6
        if abs(f - round(f)) > 0.02: prob.append(f'track {n}: segment off the frame grid at {tr["start"] / 1e6:.3f} s')
        if s.get('speed', 1) != 1.0 or (sr and sr['duration'] != tr['duration']) or any(speeds.get(r, 1.0) != 1.0 for r in s['extra_material_refs']):
            prob.append(f'track {n}: segment at {tr["start"] / 1e6:.2f} s is not 1x speed (Optical flow / Pro)')
        m = mats.get(s['material_id'])
        if m and m.get('path'):
            if not os.path.exists(m['path']): prob.append(f'missing media: {m["path"]}')
            elif not os.path.realpath(m['path']).startswith(movies) and sys.platform == 'darwin': notes.append(f'outside ~/Movies (CapCut may not read it): {m["path"]}')
        if m and m.get('type') == 'text':
            body = json.loads(m['content'])['text']; L = max(len(l) for l in body.split('\n'))
            if L > 40 and CW > CH: prob.append(f'caption line {L} chars: "{body[:40]}..."')
    for x, y in zip(segs, segs[1:]):
        if x['target_timerange']['start'] + x['target_timerange']['duration'] > y['target_timerange']['start'] + 2: prob.append(f'track {n}: overlap at {y["target_timerange"]["start"] / 1e6:.2f} s')
main = sorted(D['tracks'][0]['segments'], key=lambda s: s['target_timerange']['start'])
if main and main[0]['target_timerange']['start'] != 0: prob.append('main track does not start at 0')
for x, y in zip(main, main[1:]):
    if abs(x['target_timerange']['start'] + x['target_timerange']['duration'] - y['target_timerange']['start']) > 2: prob.append(f'gap in the main track at {y["target_timerange"]["start"] / 1e6:.2f} s')
# pictures cover the frame at every keyframe (main + tails)
for t in D['tracks'][:2]:
    for s in t['segments']:
        m = mats.get(s['material_id']); kf = {k['property_type']: k['keyframe_list'] for k in s['common_keyframes']}
        if not m or 'KFTypeScaleX' not in kf or not m.get('width') or m['width'] in (CW,) and m['height'] == CH: continue
        for i, k in enumerate(kf['KFTypeScaleX']):
            sc = k['values'][0]; x = kf.get('KFTypePositionX', [{'values': [0]}])[min(i, len(kf.get('KFTypePositionX', [0])) - 1)]['values'][0]
            y = kf.get('KFTypePositionY', [{'values': [0]}])[min(i, len(kf.get('KFTypePositionY', [0])) - 1)]['values'][0]
            x0, y0, x1, y1 = visible_rect(x, y, sc, m['width'], m['height'], CW, CH)
            if x0 < -0.002 or y0 < -0.002 or x1 > 1.002 or y1 > 1.002: prob.append(f'{os.path.basename(m["path"])}: frame not covered at key {i} (shows the edge)')
for m in D['materials'].get('videos', []):
    if m['path'].endswith('.mov'):
        c = subprocess.run(['ffprobe', '-v', 'error', '-select_streams', 'v', '-show_entries', 'stream=codec_name', '-of', 'csv=p=0', m['path']], capture_output=True, text=True).stdout.strip()
        if c not in ('hevc', 'prores'): prob.append(f'{os.path.basename(m["path"])}: {c} has no alpha (needs HEVC alpha or ProRes 4444)')
dur = D['duration'] / 1e6
print(f'"{os.path.basename(folder)}": {len(D["tracks"])} tracks, {sum(len(t["segments"]) for t in D["tracks"])} segments, {dur:.2f} s')
for x in sorted(set(notes)): print('note:', x)
for x in sorted(set(prob)): print('PROBLEM:', x)
print('OK' if not prob else f'{len(set(prob))} problems')
print("""in CapCut (closed or home screen when building; then):
  1. open the project from the home screen; no "Link media" dialog should appear
  2. scrub 6-10 key moments (title, each key line, each act change, the climax, the end card) and look at the frame
  3. Export panel: the button must read "Export" (not "Join Pro to export"), Audio ticked, H.264 MP4 for YouTube""")
sys.exit(1 if prob else 0)
