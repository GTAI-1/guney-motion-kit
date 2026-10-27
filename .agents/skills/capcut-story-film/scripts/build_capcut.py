#!/usr/bin/env python3
"""Build the CapCut project from the plan:  python3 scripts/build_capcut.py <project> [--name "Film title"] [--no-captions]

Reads project.json, plan/edit.json (+ plan/layers.json, renders/layers/*, renders/audio/*, qa/words.json) and writes a new
CapCut project (never overwrites one). Track stack, bottom to top:
  V1  pictures: stills and living plates with zoom/position keyframes (shot 1 also covers the pre-roll), black at the end
  V2  dissolve tails: a copy of the outgoing shot fading out over the next, its camera move continued
  FX  screen effects (snow, rain, dust, embers, sparks, old film)      [as many tracks as overlaps need]
  SOL flash / dip / fade solids and film burns                         [as many tracks as overlaps need]
  TYP type layers (title, key lines, cards, labels, end card)          [as many tracks as overlaps need]
  FRM letterbox + vignette frame (project.json look.letterbox / look.vignette)
  T1  captions: CapCut text, phrase by phrase on the spoken words, never wider than the frame
  A1  narration (0 dB, starts at the pre-roll)   A2  score / music   A3  sound effects
Media are copied to ~/Movies/CapCut/<name> media/ first (CapCut on macOS is sandboxed and cannot read the Desktop).
CapCut must be closed or on its home screen while this runs; open the project from the home screen afterwards.
"""
import argparse, json, os, re, shutil, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import Project, load, save, die, place, frame_at, media_root
from planfile import resolve_edit, lint
from capcut import Draft
from PIL import Image
import numpy as np

ap = argparse.ArgumentParser(); ap.add_argument('project'); ap.add_argument('--name'); ap.add_argument('--no-captions', action='store_true')
a = ap.parse_args()
P = Project(a.project); CW, CH = P.canvas; PRE = P.pre; F = lambda t: round(t + PRE, 4)
R = resolve_edit(P); err, warn = lint(P, R)
if err: die('plan/edit.json has errors (run scripts/lint_edit.py):\n  ' + '\n  '.join(err))
LY = {x['id']: x for x in load(P.p('plan/layers.resolved.json'), {'layers': []})['layers']}
look = P.cfg.get('look', {})
MED = media_root(P)
for d in ('images', 'layers', 'audio', 'solids', 'fonts'): os.makedirs(os.path.join(MED, d), exist_ok=True)


def sync(src, dst):
    if not os.path.exists(src): die(f'missing {src}')
    if not os.path.exists(dst) or os.path.getmtime(dst) < os.path.getmtime(src) or os.path.getsize(dst) != os.path.getsize(src): shutil.copy2(src, dst)
    return dst


# ---------------------------------------------------------------- media into CapCut's reach
for pid, im in P.cfg['images'].items(): sync(P.p(im['file']), os.path.join(MED, 'images', os.path.basename(im['file'])))
for x in LY.values():
    if os.path.exists(P.p(x['file'])): sync(P.p(x['file']), os.path.join(MED, 'layers', os.path.basename(x['file'])))
    else: die(f"layer {x['id']} is not rendered ({x['file']}): run scripts/render_layers.sh")
audio = {}
for k, f in (('narration', P.cfg['narration']), ('score', 'renders/audio/score.wav'), ('sfx', 'renders/audio/sfx.wav')):
    if os.path.exists(P.p(f)): audio[k] = sync(P.p(f), os.path.join(MED, 'audio', os.path.basename(f)))
font = look.get('captions', {}).get('font', 'assets/fonts/Montserrat-SemiBold.otf')
font = sync(P.p(font), os.path.join(MED, 'fonts', os.path.basename(font))) if os.path.exists(P.p(font)) else ''
for name, rgb in (('black', (0, 0, 0)), ('white', (255, 250, 240)), ('red', (190, 20, 12))):
    p = os.path.join(MED, 'solids', f'{name}-{CW}x{CH}.png')
    if not os.path.exists(p): Image.new('RGB', (CW, CH), rgb).save(p)
solid = lambda c: os.path.join(MED, 'solids', f'{c}-{CW}x{CH}.png')
frame_png = None
if look.get('letterbox') or look.get('vignette', True):
    lb = float(look.get('letterbox') or 0); frame_png = os.path.join(MED, 'solids', f'frame-{CW}x{CH}-{lb:g}-{int(bool(look.get("vignette", True)))}.png')
    if not os.path.exists(frame_png):
        yy, xx = np.mgrid[0:CH, 0:CW]; dd = np.hypot((xx - CW / 2) / (CW / 2), (yy - CH / 2) / (CH / 2))
        al = (np.clip((dd - 0.75) / 0.75, 0, 1) ** 1.6 * 150) if look.get('vignette', True) else np.zeros((CH, CW))
        if lb and CW > CH:
            bar = int(round((CH - CW / lb) / 2)); al[:bar] = 255; al[CH - bar:] = 255
        Image.fromarray(np.dstack([np.zeros((CH, CW, 3), np.uint8), al.astype(np.uint8)])).save(frame_png)


def pic(pid):
    if pid in LY: return os.path.join(MED, 'layers', os.path.basename(LY[pid]['file'])), LY[pid]['w'], LY[pid]['h'], False
    im = P.image(pid); return os.path.join(MED, 'images', os.path.basename(im['file'])), im['w'], im['h'], True


def keyset(shot, t0, t1, w, h):
    ks = shot['keys']; extra = shot['shake']; b = shot['bounds']
    times = sorted({round(t0, 4), round(t1, 4)} | {round(k[0], 4) for k in ks if t0 < k[0] < t1} | {e[0] for e in extra if t0 <= e[0] <= t1})
    sh = {e[0]: (e[1], e[2]) for e in extra}; out = {'x': [], 'y': [], 'scale': []}
    for t in times:
        fx, fy, z = frame_at(ks, t); dx, dy = sh.get(t, (0, 0)); x, y, s = place(fx + dx, fy + dy, z, w, h, b, CW, CH)
        for k, v in (('x', x), ('y', y), ('scale', s)): out[k].append((round(t - t0, 4), v))
    return out


d = Draft(a.name or P.cfg['name'], canvas=(CW, CH))
V1, V2 = d.track('video'), d.track('video', True)
groups = {g: [d.track('video', True)] for g in ('FX', 'SOL', 'TYP')}
FRM = d.track('video', True); CAP = d.track('text'); A1, A2, A3 = d.track('audio'), d.track('audio'), d.track('audio')


def free(group, a0, b0):
    for t in groups[group]:
        if all(b0 <= s['target_timerange']['start'] / 1e6 + 1e-3 or a0 >= (s['target_timerange']['start'] + s['target_timerange']['duration']) / 1e6 - 1e-3 for s in t['segments']): return t
    t = d.track('video', True); d.tracks.remove(t); d.tracks.insert(d.tracks.index(groups[group][-1]) + 1, t); groups[group].append(t); return t


S = R['shots']; END_F = F(S[-1]['t1'])
for i, s in enumerate(S):
    path, w, h, photo = pic(s['pic']); a0 = 0.0 if i == 0 else F(s['t0']); b0 = F(s['t1'])
    src = 0.0 if photo else round(s['t0'] - LY[s['pic']]['t0'], 4)
    ks = keyset(s, s['t0'], s['t1'], w, h)
    if i == 0 and PRE > 0: ks = {k: [(0.0, v[0][1])] + [(tt + PRE, vv) for tt, vv in v] for k, v in ks.items()}   # covers the pre-roll
    d.media(V1, path, a0, b0 - a0, w, h, photo=photo, src=0.0 if (photo or i == 0) else src, length=None if photo else LY[s['pic']]['dur'],
            scale=ks['scale'][0][1], x=ks['x'][0][1], y=ks['y'][0][1], keys=ks)
    tin = s['in']; tcut = F(s['t0'])
    if tin[0] == 'dissolve' and i:
        p = S[i - 1]; D = float(tin[1]); pp, pw, ph, pphoto = pic(p['pic'])
        ks = keyset(p, p['t1'], p['t1'] + D, pw, ph); ks['alpha'] = [(0.0, 1.0), (round(D * 0.5, 4), 0.62), (D, 0.0)]
        psrc = 0.0 if pphoto else round(p['t1'] - LY[p['pic']]['t0'], 4)
        d.media(V2, pp, tcut, D, pw, ph, photo=pphoto, src=psrc, length=None if pphoto else LY[p['pic']]['dur'],
                scale=ks['scale'][0][1], x=ks['x'][0][1], y=ks['y'][0][1], keys=ks)
    elif tin[0] in ('flash', 'dip'):
        col, up, dn = tin[1], float(tin[2]), float(tin[3])
        if i == 0: a1, keys = 0.0, {'alpha': [(0.0, 1.0), (round(PRE * 0.3, 4), 1.0), (round(PRE * 0.3 + dn, 4), 0.0)]}; length = PRE * 0.3 + dn
        else: a1, keys = tcut - up, {'alpha': [(0.0, 0.0), (round(up, 4), 1.0), (round(up + dn, 4), 0.0)]}; length = up + dn
        d.media(free('SOL', a1, a1 + length), solid(col), a1, length, CW, CH, photo=True, alpha=keys['alpha'][0][1], keys=keys)
if R['fade_out']:
    fa, fb = F(R['fade_out'][0]), F(R['fade_out'][1])
    d.media(free('SOL', fa, END_F), solid('black'), fa, END_F - fa, CW, CH, photo=True, alpha=0.0, keys={'alpha': [(0.0, 0.0), (round(fb - fa, 4), 1.0)]})
tail_end = max([END_F] + [F(x['t0']) + x['dur'] for x in LY.values() if x['kind'] != 'plate'])
if tail_end > END_F + 0.05: d.media(V1, solid('black'), END_F, round(tail_end - END_F, 4), CW, CH, photo=True)

for x in LY.values():
    if x['kind'] == 'plate': continue
    a1 = max(0.0, F(x['t0'])); dur = round(x['dur'] - (a1 - F(x['t0'])), 4)
    grp = 'TYP' if x['kind'] == 'type' else 'SOL' if x['kind'] == 'burn' else 'FX'
    d.media(free(grp, a1, a1 + dur), os.path.join(MED, 'layers', os.path.basename(x['file'])), a1, dur, x['w'], x['h'], src=round(a1 - F(x['t0']), 4), length=x['dur'])
if frame_png: d.media(FRM, frame_png, 0.0, tail_end, CW, CH, photo=True)

# ---------------------------------------------------------------- captions
cues = []
cap = look.get('captions', {})
if R['captions'] and not a.no_captions and cap is not False:
    MAXL = int(cap.get('max_chars', 34 if CW > CH else 22)); SIZE = float(cap.get('size', 9.5 if CW > CH else 8.5)); Y = float(cap.get('y', -0.74 if CW > CH else -0.55))
    words = [w for w in P.words if not any(x <= w['s'] <= y for x, y in R['no_caption'])]
    phr, cur = [], []
    for k, w in enumerate(words):
        cur.append(w); nxt = words[k + 1] if k + 1 < len(words) else None
        if re.search(r'[.,?!;:]$', w['w']) or not nxt or nxt['s'] - w['e'] > 0.6: phr.append(cur); cur = []
    caps = []
    for p in phr:
        while p:
            take, n = [], 0
            for w in p:
                if n + len(w['w']) + (1 if take else 0) > 2 * MAXL: break
                take.append(w); n += len(w['w']) + (1 if len(take) > 1 else 0)
            if not take: take = p[:1]
            caps.append(take); p = p[len(take):]
    merged = []
    for c in caps:
        if merged and len(' '.join(w['w'] for w in merged[-1] + c)) <= MAXL and c[0]['s'] - merged[-1][-1]['e'] < 0.35: merged[-1] = merged[-1] + c
        else: merged.append(c)
    def lines(t):
        if len(t) <= MAXL + 2: return t
        ws = t.split(' '); best = None
        for i in range(1, len(ws)):
            l1, l2 = ' '.join(ws[:i]), ' '.join(ws[i:]); sc = abs(len(l1) - len(l2)) - (8 if re.search(r'[,.]$', l1) else 0)
            if max(len(l1), len(l2)) <= MAXL + 4 and (best is None or sc < best[0]): best = (sc, l1, l2)
        return best[1] + '\n' + best[2] if best else t
    for k, c in enumerate(merged):
        t0 = F(c[0]['s']) - 0.05; nxt = F(merged[k + 1][0]['s']) - 0.08 if k + 1 < len(merged) else 1e9
        t1 = min(F(c[-1]['e']) + 0.6, nxt); t1 = max(t1, min(t0 + 0.7, nxt))
        cues.append((round(max(0, t0), 3), round(t1, 3), lines(' '.join(w['w'] for w in c))))
    for t0, t1, tx in cues: d.text(CAP, tx, t0, round(t1 - t0, 3), size=SIZE, font=font, y=Y)

# ---------------------------------------------------------------- sound
if 'narration' in audio: d.audio(A1, audio['narration'], PRE, P.cfg['narration_dur'], P.cfg['narration_dur'])
for k, tr in (('score', A2), ('sfx', A3)):
    if k in audio:
        import subprocess
        L = float(subprocess.run(['ffprobe', '-v', 'error', '-show_entries', 'format=duration', '-of', 'csv=p=0', audio[k]], capture_output=True, text=True).stdout)
        d.audio(tr, audio[k], 0.0, min(L, tail_end + 2.0), L)

folder = d.save(backup_dir=P.p('qa/capcut-backups'))
info = {'name': d.final_name, 'folder': folder, 'media': MED, 'shots': len(S), 'layers': len(LY), 'captions': len(cues), 'length': round(tail_end, 2),
        'longest_caption_line': max((len(l) for _, _, t in cues for l in t.split('\n')), default=0)}
save(P.p('qa/capcut-build.json'), info)
for w_ in warn: print('warning:', w_)
print(f"CapCut project \"{d.final_name}\": {len(S)} shots, {len(LY)} layers, {len(cues)} captions, {tail_end:.2f} s\n  {folder}\n  media: {MED}")
print('next: python3 scripts/verify_capcut.py', a.project)
