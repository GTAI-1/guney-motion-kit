"""Read and resolve the two plan files Claude writes for every film (formats: references/plan-formats.md):
  plan/edit.json    the shots (picture, start/end, framing keys, transition in, bounds, shake), fade out, caption gaps
  plan/layers.json  the motion-graphics layers (type, screen effects, living plates)
All times may be time references (see common.py); resolve_* returns plain narration-clock seconds.
"""
import os
from common import Project, load, save, die, shake_offsets

TRANSITIONS = {'cut': 0, 'dissolve': 1, 'flash': 3, 'dip': 3}


def resolve_layers(P):
    L = load(P.p('plan/layers.json'), {'layers': []})
    out = []
    for x in L.get('layers', []):
        if x.get('draft'): continue                      # draft layers (e.g. lights not yet placed) are left out of the build
        y = dict(x)
        for k in ('t0', 't1', 'out', 'in'):
            if k in y: y[k] = P.t(y[k])
        out.append(y)
    return out


def resolve_edit(P):
    E = load(P.p('plan/edit.json'))
    plates = {x['id']: x for x in resolve_layers(P) if x.get('kind') == 'plate'}
    shots = []
    for s in E['shots']:
        r = dict(s); r['t0'] = P.t(s['t0']); r['t1'] = P.t(s['t1'])
        r['keys'] = [[P.t(k[0])] + [float(v) for v in k[1:]] for k in s['keys']]
        tin = s.get('in', ['cut'])
        if isinstance(tin, str): tin = [tin]
        r['in'] = tin
        pid = s['pic']
        if pid in plates:
            r['plate'] = pid; base = plates[pid]['pic']; r['base_pic'] = base
        else:
            r['base_pic'] = pid
        P.image(r['base_pic'])
        r['bounds'] = s.get('bounds', [0, 0, 1, 1])
        sh = []
        for z in s.get('shake', []):
            sh += shake_offsets(P.t(z['from']), P.t(z['to']), float(z.get('amp', 0.006)), float(z.get('hz', 10)), float(z.get('decay', 0)), float(z.get('seed', 1)))
        r['shake'] = sh
        shots.append(r)
    out = {'shots': shots, 'plates': plates,
           'fade_out': [P.t(v) for v in E['fade_out']] if E.get('fade_out') else None,
           'no_caption': [[P.t(a), P.t(b)] for a, b in E.get('no_caption', [])],
           'captions': E.get('captions', True)}
    return out


def lint(P, R, verbose=True):
    """returns (errors, warnings)"""
    err, warn = [], []
    S = R['shots']
    if not S: err.append('no shots')
    if S and abs(S[0]['t0']) > 1e-6: err.append(f"first shot must start at 0 (starts {S[0]['t0']})")
    for a, b in zip(S, S[1:]):
        if abs(a['t1'] - b['t0']) > 1e-3: err.append(f"gap/overlap between shot {a['id']} (ends {a['t1']:.3f}) and {b['id']} (starts {b['t0']:.3f})")
    ids = [s['id'] for s in S]
    if len(set(ids)) != len(ids): err.append('duplicate shot ids')
    scenes = P.scenes
    if scenes and S:
        end = max(sc['end'] for sc in scenes.values())
        if abs(S[-1]['t1'] - end) > 0.05: warn.append(f"last shot ends {S[-1]['t1']:.2f}, last scene ends {end:.2f}")
    for i, s in enumerate(S):
        d = s['t1'] - s['t0']
        if d < 0.5: warn.append(f"shot {s['id']} is only {d:.2f} s")
        if d > 9: warn.append(f"shot {s['id']} holds {d:.1f} s: consider a second angle, a crop of the same picture, or a two-stage move")
        for k in s['keys']:
            if not (s['t0'] - 1e-3 <= k[0] <= s['t1'] + 1e-3): warn.append(f"shot {s['id']}: key at {k[0]:.2f} is outside the shot")
            if not (0 <= k[1] <= 1 and 0 <= k[2] <= 1): err.append(f"shot {s['id']}: focus {k[1]},{k[2]} must be 0..1")
            if k[3] < 1.0 or k[3] > 3.0: warn.append(f"shot {s['id']}: zoom {k[3]} (keep 1.0-2.4)")
        im = P.image(s['base_pic']); src_w = im.get('source_px', [im['w']])[0]
        zmax = max(k[3] for k in s['keys']); bw = s['bounds'][2] - s['bounds'][0]
        eff = src_w / zmax * bw / P.canvas[0] if bw < 1 else src_w / zmax / P.canvas[0]
        if eff < 0.5: warn.append(f"shot {s['id']}: at zoom {zmax} only {src_w / zmax:.0f} source px span the frame (soft); zoom less or use a sharper picture")
        t = s['in']
        if t[0] not in TRANSITIONS: err.append(f"shot {s['id']}: unknown transition {t[0]}")
        elif len(t) - 1 != TRANSITIONS[t[0]]: err.append(f"shot {s['id']}: transition {t} needs {TRANSITIONS[t[0]]} values")
        if t[0] == 'dissolve' and i and t[1] > min(d, S[i - 1]['t1'] - S[i - 1]['t0']) * 0.6: warn.append(f"shot {s['id']}: dissolve {t[1]} s is long for these shots")
        if t[0] in ('flash', 'dip') and t[1] not in ('black', 'white', 'red'): err.append(f"shot {s['id']}: {t[0]} colour must be black, white or red")
        moves = set((round(k[1], 2), round(k[2], 2), round(k[3], 2)) for k in s['keys'])
        if len(moves) == 1 and not s['shake'] and d > 2.5 and not s.get('still'):
            warn.append(f"shot {s['id']} has no camera move (add \"still\": true if the stillness is the point)")
    drafts = [x['id'] for x in load(P.p('plan/layers.json'), {'layers': []}).get('layers', []) if x.get('draft')]
    if drafts: warn.append(f"draft layers left out of the build until finished: {', '.join(drafts)} (see their \"todo\")")
    return err, warn
