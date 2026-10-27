"""Shared helpers for the capcut-story-film scripts: project loading, time references, framing math.

Two clocks are used everywhere:
  narration clock  seconds from the first sample of the narration file (what words.json and every plan file use)
  film clock       narration clock + project["pre"] (seconds of black / ambience before the voice starts)

Time references (anywhere a time is expected in plan/*.json):
  12.5            a plain number (narration clock)
  "s12"           start of scene 12 (plan/scenes.json); "e12" = its end;   "s12+0.4", "e3-1" add an offset
  "w:idea"        start of the first spoken word "idea";  "w:idea#2" its 2nd occurrence;  "w:idea@80" first one at/after 80 s
  "w:idea.end"    end of that word;  "w:idea+0.2" add an offset;  combine: "w:stop@100.end+0.1"
"""
import json, os, re, sys, math

SKILL = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
W, H = 1920, 1080                                   # canvas (16:9). 9:16 projects set project["canvas"] = [1080, 1920]


def die(msg):
    print('ERROR: ' + msg, file=sys.stderr); sys.exit(1)


def load(path, default=None):
    if not os.path.exists(path):
        if default is not None: return default
        die(f'missing {path}')
    return json.load(open(path))


def save(path, obj):
    os.makedirs(os.path.dirname(path) or '.', exist_ok=True)
    json.dump(obj, open(path, 'w'), indent=1, ensure_ascii=False)


class Project:
    def __init__(self, root):
        self.root = os.path.abspath(root)
        if not os.path.exists(self.p('project.json')): die(f'{root} is not a project (no project.json). Run scripts/new_project.py first.')
        self.cfg = load(self.p('project.json'))
        self.pre = float(self.cfg.get('pre', 1.5))
        self.fps = int(self.cfg.get('fps', 30))
        self.canvas = tuple(self.cfg.get('canvas', [W, H]))
        self._words = self._scenes = None

    def p(self, *a): return os.path.join(self.root, *a)

    @property
    def words(self):
        if self._words is None:
            self._words = load(self.p('qa/words.json'), [])
            if not self._words: self._words = self.planned_words()
        return self._words

    def planned_words(self):
        """before the voice exists: spread each scene's narration evenly over its provisional time (plan/scenes.json),
        so word references can be linted and previewed. transcribe.py replaces this with the real timing."""
        sc, script = load(self.p('plan/scenes.json'), []), load(self.p('plan/script.json'), [])
        if not sc or not all(s.get('provisional') for s in sc): return []
        text = {s['scene']: s.get('narration', '') for s in script}; out = []
        for s in sc:
            ws = [w for w in text.get(s['scene'], '').replace('-', ' ').split() if norm(w)]
            if not ws: continue
            a, b = s['start'] + 0.35, s['end'] - 0.6; step = (b - a) / len(ws)
            out += [{'w': w, 's': round(a + k * step, 3), 'e': round(a + (k + 0.8) * step, 3), 'planned': True} for k, w in enumerate(ws)]
        if out: self.provisional = True
        return out

    provisional = False

    @property
    def scenes(self):
        if self._scenes is None: self._scenes = {s['scene']: s for s in load(self.p('plan/scenes.json'), [])}
        return self._scenes

    def image(self, pid):
        im = self.cfg['images'].get(pid)
        if not im: die(f'unknown picture id "{pid}" (known: {", ".join(sorted(self.cfg["images"]))})')
        return im

    # ------------------------------------------------------------------ time references
    def t(self, ref):
        if ref is None: return None
        if isinstance(ref, (int, float)): return float(ref)
        s = str(ref).strip()
        try: return float(s)
        except ValueError: pass
        m = re.fullmatch(r'([se])(\d+)([+-][\d.]+)?', s)
        if m:
            sc = self.scenes.get(int(m.group(2)))
            if not sc: die(f'time "{s}": no scene {m.group(2)} in plan/scenes.json')
            return round((sc['start'] if m.group(1) == 's' else sc['end']) + float(m.group(3) or 0), 4)
        m = re.fullmatch(r"w:([A-Za-z0-9']+)(?:#(\d+))?(?:@([\d.]+))?(\.end)?([+-][\d.]+)?", s)
        if m:
            key, nth, after, end, off = m.group(1).lower(), int(m.group(2) or 1), float(m.group(3) or -1e9), m.group(4), float(m.group(5) or 0)
            hits = [w for w in self.words if norm(w['w']) == norm(key) and w['s'] >= after - 1e-6]
            if len(hits) < nth: die(f'time "{s}": the word "{key}" (occurrence {nth}, after {after:g}) is not in qa/words.json')
            w = hits[nth - 1]
            return round((w['e'] if end else w['s']) + off, 4)
        die(f'cannot read time reference "{s}"')

    def resolve(self, obj, keys=('t', 't0', 't1', 'in', 'out', 'at', 'from', 'to', 'start', 'end')):
        """resolve every time reference found under the given key names (recursively); key-frame lists are handled by callers"""
        if isinstance(obj, dict):
            return {k: (self.t(v) if k in keys and isinstance(v, (str, int, float)) and not isinstance(v, bool) else self.resolve(v, keys)) for k, v in obj.items()}
        if isinstance(obj, list): return [self.resolve(v, keys) for v in obj]
        return obj


def norm(w):
    return re.sub(r"[^a-z0-9']", '', w.lower().replace('’', "'"))


# ---------------------------------------------------------------------- framing math (CapCut's picture transform)
# A picture of size w x h is fitted inside the canvas at scale 1. A framing (fx, fy, z) puts the point (fx, fy) of the
# picture (0..1 from its top-left) at the canvas centre at zoom z. CapCut stores position in half-canvas units (x 1 =
# right edge, y 1 = TOP edge) and scale as a plain factor of the fitted size.
def fit(w, h, cw=W, ch=H):
    a = w / h
    return (cw, cw / a) if a >= cw / ch else (ch * a, ch)


def place(fx, fy, z, w, h, bounds=(0, 0, 1, 1), cw=W, ch=H):
    """clamped CapCut transform (x, y, scale) so the picture always covers the canvas and stays inside bounds"""
    Wd, Hd = fit(w, h, cw, ch)
    b = bounds
    z = max(z, cw / (Wd * (b[2] - b[0])) + 1e-4, ch / (Hd * (b[3] - b[1])) + 1e-4)
    hx, hy = cw / (2 * Wd * z), ch / (2 * Hd * z)
    fx = min(max(fx, b[0] + hx), b[2] - hx)
    fy = min(max(fy, b[1] + hy), b[3] - hy)
    return round((0.5 - fx) * Wd * z / (cw / 2), 5), round((fy - 0.5) * Hd * z / (ch / 2), 5), round(z, 5)


def visible_rect(x, y, s, w, h, cw=W, ch=H):
    """inverse of place(): the picture region (x0, y0, x1, y1 in 0..1) the canvas shows for a CapCut transform"""
    Wd, Hd = fit(w, h, cw, ch)
    fx = 0.5 - x * (cw / 2) / (Wd * s); fy = 0.5 + y * (ch / 2) / (Hd * s)
    hx, hy = cw / (2 * Wd * s), ch / (2 * Hd * s)
    return fx - hx, fy - hy, fx + hx, fy + hy


def frame_at(keys, t):
    """linear framing between keys [(t, fx, fy, z)]; past the last key the last move continues (dissolve tails)"""
    if len(keys) == 1 or t <= keys[0][0]: return tuple(keys[0][1:])
    for a, b in zip(keys, keys[1:]):
        if t <= b[0]:
            u = (t - a[0]) / max(1e-9, b[0] - a[0]); return tuple(a[i] + (b[i] - a[i]) * u for i in (1, 2, 3))
    a, b = keys[-2], keys[-1]
    u = (t - a[0]) / max(1e-9, b[0] - a[0]); return tuple(a[i] + (b[i] - a[i]) * u for i in (1, 2, 3))


def shake_offsets(t0, t1, amp, hz=10.0, decay=0.0, seed=1.0):
    """handheld / impact shake as framing offsets [(t, dfx, dfy)] (amp in picture fractions)"""
    out, t, k = [], t0, 0
    while t <= t1 + 1e-9:
        u = (t - t0) / max(1e-6, t1 - t0); g = amp * (math.exp(-decay * u * 5) if decay else 1)
        out.append((round(t, 4), g * math.sin(k * 2.3 + seed), g * math.cos(k * 1.7 + seed * 0.4))); k += 1; t += 1 / hz
    return out


def capcut_root():
    """CapCut desktop's project folder (macOS first, then Windows); override with $CAPCUT_DRAFTS"""
    env = os.environ.get('CAPCUT_DRAFTS')
    if env: return env
    for c in ('~/Movies/CapCut/User Data/Projects/com.lveditor.draft',
              os.path.join(os.environ.get('LOCALAPPDATA', ''), 'CapCut/User Data/Projects/com.lveditor.draft')):
        c = os.path.expanduser(c)
        if os.path.isdir(c): return c
    die('CapCut project folder not found. Open CapCut once, or set CAPCUT_DRAFTS to the com.lveditor.draft folder.')


def media_root(project):
    """where media must live so sandboxed CapCut (macOS) can read it: ~/Movies/CapCut/<project name> media"""
    base = os.environ.get('CAPCUT_MEDIA') or os.path.expanduser('~/Movies/CapCut')
    return os.path.join(base, f"{project.cfg['name']} media")
