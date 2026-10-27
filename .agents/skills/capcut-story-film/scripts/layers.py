#!/usr/bin/env python3
"""Turn plan/layers.json into HyperFrames compositions (compositions/<id>.html, engine assets/lt.js) and
plan/layers.resolved.json (id, kind, start on the narration clock, duration, size, alpha, render file).

  python3 scripts/layers.py <project>

Layer kinds (full format with examples: references/plan-formats.md):
  type      title / key line / act card / label / end card: words enter one at a time on their spoken times
  snow | blizzard | rain | dust | embers | sparks | burn | oldfilm      screen-space effects (transparent)
  plate     a "living" picture: the still with lights that live inside it (blinks, flashes, pulses, glows),
            rendered at picture size; the shots that use it (edit.json "pic": "<plate id>") zoom and pan it in CapCut
"""
import json, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import Project, save, die
from planfile import resolve_layers, resolve_edit

P = Project(sys.argv[1] if len(sys.argv) > 1 else '.')
CW, CH = P.canvas
COLORS = {'amber': '255,170,60', 'red': '255,40,28', 'cold': '225,238,255', 'warm': '255,196,120', 'lantern': '255,190,110',
          'blue': '170,215,255', 'green': '120,255,170', 'white': '255,255,255', 'fire': '255,140,40', 'gold': '255,200,120'}
col = lambda c: COLORS.get(c, c) if isinstance(c, str) else ','.join(map(str, c))
BACKDROPS = {'center': 'radial-gradient(ellipse 72% 46% at 50% 52%, rgba(0,0,0,0.46), rgba(0,0,0,0) 72%)',
             'top': 'linear-gradient(180deg, rgba(0,0,0,0.58) 0%, rgba(0,0,0,0.25) 30%, rgba(0,0,0,0) 50%)',
             'bottom': 'linear-gradient(0deg, rgba(0,0,0,0.58) 0%, rgba(0,0,0,0.25) 30%, rgba(0,0,0,0) 50%)', None: None, 'none': None}
HEAD = """<!doctype html>
<!-- {note} -->
<html lang="en"><head><meta charset="utf-8"><title>{id}</title>
<script src="assets/gsap.min.js"></script><script src="assets/lt.js"></script>
<link rel="stylesheet" href="assets/fonts.css">
<style>
  html, body {{ margin: 0; width: {w}px; height: {h}px; overflow: hidden; background: {bg}; }}
  #lt {{ position: absolute; inset: 0; overflow: hidden; }}
  .lt-back {{ position: absolute; inset: 0; opacity: 0; }}
  .lt-row {{ position: absolute; left: 50%; transform: translateX(-50%); transform-origin: 50% 0; white-space: nowrap; display: flex; gap: 0.26em;
            font: 900 {big}px/1 '{display}', sans-serif; letter-spacing: 0.07em; color: {ink};
            text-shadow: 0 0 34px rgba({glow},0.55), 0 0 4px rgba(255,255,255,0.35), 0 3px 22px rgba(0,0,0,0.65); }}
  .lt-word {{ display: inline-block; will-change: transform, opacity, filter; }}
  .kick {{ font: 700 50px/1 'JetBrains Mono', monospace; letter-spacing: 0.45em; color: #D9E1EC; }}
  .mid {{ font-size: {mid}px; }}
  .card {{ font-size: {card}px; letter-spacing: 0.06em; }}
  .small {{ font-size: {small}px; }}
  .typed {{ font: 700 78px/1 'JetBrains Mono', monospace; letter-spacing: 0.18em; color: #F6E7CC; gap: 0; }}
  .hand {{ font: 700 {card}px/1 'Caveat', cursive; letter-spacing: 0.01em; }}
  .serif {{ font: 400 {card}px/1 'Instrument Serif', serif; letter-spacing: 0.01em; }}
  .lt-cur {{ display: inline-block; width: 0.55em; height: 0.92em; margin-left: 0.12em; background: currentColor; vertical-align: -0.1em; }}
  .sig {{ color: #EEF6FF; }}
</style></head>
<body>
<div class="fontwarm" style="position:absolute;opacity:0;font:900 20px 'Big Shoulders Display'">a<span style="font:700 20px 'JetBrains Mono'">a</span><span style="font:700 20px Caveat">a</span></div>
<div id="root" data-composition-id="{id}" data-start="0" data-duration="{dur}" data-width="{w}" data-height="{h}">
  <div id="lt" class="clip" data-start="0" data-duration="{dur}" data-track-index="0"></div>
</div>
<script>LT.boot({cfg});</script>
</body></html>
"""
vertical = CH > CW
SIZES = dict(big=150 if vertical else 170, mid=120 if vertical else 140, card=96 if vertical else 118, small=64 if vertical else 80)
layers_out = []


def write(id, kind, t0, dur, cfg, note, w=CW, h=CH, alpha=True, glow='150,190,255', bg='transparent', display='Big Shoulders Display', ink='#F4EFE6'):
    dur = round(dur, 3)
    c = dict(cfg, id=id, kind=kind, dur=dur, w=w, h=h, t0=t0)
    open(P.p(f'compositions/{id}.html'), 'w').write(HEAD.format(id=id, note=note.replace('--', '-'), w=w, h=h, dur=dur, cfg=json.dumps(c), glow=glow, bg=bg,
                                                                 display=display, ink=ink, **SIZES))
    layers_out.append({'id': id, 'kind': kind, 't0': round(t0, 3), 'dur': dur, 'w': w, 'h': h, 'alpha': alpha,
                       'file': f'renders/layers/{id}.{"mov" if alpha else "mp4"}'})


def spoken(a, b, case='upper'):
    out = []
    for w in P.words:
        if a - 0.01 <= w['s'] <= b + 0.01:
            tx = w['w'].strip('.,;:!?"“”')
            out.append([tx.upper() if case == 'upper' else tx, w['s']])
    if not out: die(f'no spoken words between {a} and {b}')
    return out


E = resolve_edit(P)
shots_by_pic = {}
for i, s in enumerate(E['shots']):
    if 'plate' in s: shots_by_pic.setdefault(s['plate'], []).append(i)

for L in resolve_layers(P):
    id, kind = L['id'], L['kind']
    if kind == 'type':
        lines, times = [], []
        for ln in L['lines']:
            row = {'y': ln.get('y', 455), 'cls': ln.get('class', ''), 'style': ln.get('style', 'stamp' if L.get('style') == 'key' else 'rise')}
            if 'typed' in ln:
                t = P.t(ln['t']); row.update(typed=ln['typed'], t=t, cps=ln.get('cps', 18)); times.append(t)
            else:
                if 'from' in ln: ws = spoken(P.t(ln['from']), P.t(ln['to']), ln.get('case', 'upper'))
                elif 'words' in ln: ws = [[w[0], P.t(w[1])] for w in ln['words']]
                else:
                    t = P.t(ln['t']); ws = [[x, t + i * ln.get('stagger', 0.22)] for i, x in enumerate(ln['text'].split())]
                row['words'] = [{'text': x, 't': t, **({'flash': True} if x in ln.get('flash', []) else {})} for x, t in ws]
                times += [t for _, t in ws]
            lines.append(row)
            shown = row['typed'] if 'typed' in row else ' '.join(w['text'] for w in row['words'])
            rt = [row['t']] if 'typed' in row else [w['t'] for w in row['words']]
            print(f"  {id}: \"{shown}\" at {min(rt):.2f}-{max(rt):.2f} s")
        if max(times) - min(times) > 6: print(f'WARNING: {id} spans {max(times) - min(times):.1f} s of narration: is a repeated word picking the wrong occurrence? use "w:word@<time>"')
        t0 = L.get('t0', min(times) - 0.3); out = L.get('out', max(times) + 1.6); od = L.get('out_dur', 0.45)
        for row in lines:
            if 'typed' in row: row['t'] = round(row['t'] - t0, 3)
            else:
                for w in row['words']: w['t'] = round(w['t'] - t0, 3)
        write(id, 'type', t0, out - t0 + od + 0.05, {'lines': lines, 'out': round(out - t0, 3), 'outDur': od, 'glow': col(L.get('glow', 'cold')),
              'backdrop': BACKDROPS.get(L.get('backdrop', 'center'), L.get('backdrop')), 'backIn': 0.0, 'maxw': CW - 240},
              L.get('note', f'type layer {id}'), glow=col(L.get('glow', 'cold')), display=L.get('font', 'Big Shoulders Display'), ink=L.get('ink', '#F4EFE6'))
    elif kind in ('snow', 'blizzard', 'rain', 'dust', 'embers', 'sparks', 'burn', 'oldfilm'):
        t0 = L['t0']; t1 = L.get('t1', t0 + L.get('dur', 1.0))
        if t0 <= 0 and L.get('from_film_start', True): t0 = -P.pre                  # starts with the film (covers the pre-roll)
        cfg = {k: v for k, v in L.items() if k not in ('id', 'kind', 't0', 't1', 'note')}
        if 'peak' in cfg: cfg['peak'] = round(P.t(cfg['peak']) - t0, 3)
        if 'rgb' in cfg: cfg['rgb'] = col(cfg['rgb'])
        eng = {'blizzard': 'snow'}.get(kind, kind)
        if kind == 'blizzard':
            cfg.setdefault('fog', True)
            cfg.setdefault('layers', [{'n': 420, 's': [1.4, 2.8], 'v': [260, 380], 'a': 0.6, 'wind': -1.1}, {'n': 200, 's': [3, 4.8], 'v': [420, 560], 'a': 0.8, 'wind': -1.2},
                                      {'n': 18, 's': [6, 10], 'v': [760, 940], 'a': 0.18, 'wind': -1.3, 'blur': True}])
        if kind == 'snow': cfg.setdefault('fadeIn', 0.0 if t0 <= -P.pre + 1e-6 else 0.4)
        if kind == 'burn': cfg.setdefault('mid', 0.3)
        if kind == 'sparks': cfg.setdefault('ox', CW * 0.83); cfg.setdefault('oy', CH * 0.9)
        write(id, eng, t0, t1 - t0 + (0.5 if kind in ('snow', 'blizzard') else 0), cfg, L.get('note', f'{kind} layer {id}'))
    elif kind == 'plate':
        if id in P.cfg['images']: die(f'plate id "{id}" is also a picture id: give the plate its own id (e.g. "live-{id}")')
        idx = shots_by_pic.get(id)
        if not idx: print(f'note: plate {id} is not used by any shot in edit.json; skipped'); continue
        S = E['shots']; a = S[idx[0]]['t0']; b = S[idx[-1]]['t1']
        nxt = S[idx[-1] + 1] if idx[-1] + 1 < len(S) else None
        tail = nxt['in'][1] if nxt and nxt['in'][0] == 'dissolve' else 0
        im = P.image(L['pic']); w, h = im['w'] - im['w'] % 2, im['h'] - im['h'] % 2
        def local(spec):
            """envelope times (narration clock, references allowed) -> plate-local seconds"""
            if isinstance(spec, list): return [local(s) for s in spec]
            if not isinstance(spec, dict): return spec
            o = {}
            for k, v in spec.items():
                if k == 'keys': o[k] = [[round(P.t(t) - a, 3), val] for t, val in v]
                elif k == 'times': o[k] = [round(P.t(t) - a, 3) for t in v]
                elif k in ('t0', 't1'): o[k] = round(P.t(v) - a, 3)
                elif isinstance(v, (dict, list)): o[k] = local(v)
                else: o[k] = v
            return o
        lights = [dict(l, rgb=col(l.get('rgb', 'warm')), a=local(l.get('a', 1))) for l in L.get('lights', [])]
        def ring_rgb(q):
            # "auto": the mean colour of a thin ring just outside the patch, so the patch matches its surroundings
            from PIL import Image
            import numpy as np
            im = np.asarray(Image.open(P.p(P.cfg['images'][L['pic']]['file'])).convert('RGB').reduce(4)).astype(float)
            h, w, _ = im.shape; yy, xx = np.mgrid[0:h, 0:w]; d = np.hypot(xx - q['x'] * w, yy - q['y'] * h) / w
            m = im[(d > q['r'] * 1.05) & (d < q['r'] * 1.3)].mean(0)
            return ','.join(str(int(v)) for v in m)
        patches = [dict(q, rgb=ring_rgb(q) if q.get('rgb') == 'auto' else col(q.get('rgb', '40,50,60')), a=local(q.get('a', 1))) for q in L.get('patches', [])]
        write(id, 'plate', a, b - a + tail + 0.1, {'img': P.cfg['images'][L['pic']]['file'], 'lights': lights, 'patches': patches},
              L.get('note', f'living plate {id} on {L["pic"]}'), w=w, h=h, alpha=False, bg='#000')
    else:
        die(f'unknown layer kind "{kind}" ({id})')

save(P.p('plan/layers.resolved.json'), {'pre': P.pre, 'layers': layers_out})
for x in layers_out: print(f"{x['id']:12s} {x['kind']:8s} t0 {x['t0']:8.2f}  dur {x['dur']:6.2f}  {x['w']}x{x['h']} {'alpha' if x['alpha'] else 'opaque'}")
print(f'{len(layers_out)} layers -> compositions/*.html; render with scripts/render_layers.sh')
