#!/usr/bin/env python3
"""Read a storyboard written with references/master-prompt.md (sections A to H) and write the film's first plan.

  python3 scripts/ingest_storyboard.py <storyboard.md> <project dir> [--force]

Writes (field mapping: references/plan-formats.md, "Storyboard v2"):
  plan/storyboard.json   everything parsed, for reference
  plan/script.json       one entry per scene (narration, visual, camera, sound, act)
  plan/scenes.json       PROVISIONAL scene times from the storyboard (align.py replaces them from the recorded voice)
  plan/narration.txt     section D, cleaned for text to speech;  plan/voice.json  narrator direction + gender
  plan/generate.json     the picture list: reference images, then one still per scene (ids s01, s02...), style suffix
                         appended, references named per scene, match-cut pairs, aspect ratio
  plan/edit.json         first-draft shots: one per scene, camera keys from the editor move, transitions (dip in,
                         dips at act changes, dissolves on match cuts), fade out. Refine after looking at the pictures.
  plan/layers.json       effects from "Animated atmosphere", type from section F (title word by word, act cards, key
                         phrases stamped on their words, end card); lights become DRAFT plates waiting for positions
  plan/cue.mjs           a first cue sheet from "Sound design" and section E (wind, drone, piano, silence, whum...)
  project.json           only if the folder has none: a DRAFT project (planned pictures, no narration yet) so the
                         plan can be linted now; new_project.py --update fills in the real pictures and voice later.
Word anchors use occurrence numbers ("w:light#2") so they work before the voice exists.
"""
import argparse, json, os, re, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import save, die, norm

ap = argparse.ArgumentParser()
ap.add_argument('storyboard'); ap.add_argument('project'); ap.add_argument('--force', action='store_true', help='overwrite existing plan files')
a = ap.parse_args()
md = open(a.storyboard, encoding='utf-8').read().replace('\r\n', '\n')
root = os.path.abspath(a.project)
warnings = []
def warn(m):
    if m not in warnings: warnings.append(m)

# ------------------------------------------------------------------ sections A..H
sec, cur = {}, None
for line in md.split('\n'):
    m = re.match(r'^\s*#{1,4}\s*\**\s*([A-H])[.)]\s+(.*)$', line)
    if m: cur = m.group(1); sec[cur] = []; continue
    if cur: sec[cur].append(line)
sec = {k: '\n'.join(v).strip() for k, v in sec.items()}
if 'C' not in sec: die('no section C (scene-by-scene storyboard) found. Is this a storyboard from references/master-prompt.md?')

def field(text, label):
    m = re.search(r'\*\*\s*' + label + r'\s*:?\s*\*\*\s*:?\s*(.+)', text, re.I)
    return m.group(1).strip() if m else None

ov = sec.get('A', '')
title = field(ov, 'Title') or os.path.basename(root)
aspect = (field(ov, 'Aspect ratio') or '16:9').strip()
aspect = '9:16' if '9:16' in aspect else '16:9'
narrator = field(ov, 'Narrator') or ''
bible = sec.get('B', '')
voice_dir = field(bible, r'Narrator voice direction') or narrator
gender = 'female' if re.search(r'\bfemale|woman\b', narrator + voice_dir, re.I) else 'male' if re.search(r'\bmale|man\b', narrator + voice_dir, re.I) else 'any'

suffix = None
m = re.search(r'Style suffix\s*:?\**\s*:?\s*(.+)', bible, re.I)
if m: suffix = m.group(1).strip().strip('*').strip().strip('"').strip()
if not suffix: warn('no style suffix found in section B')

# reference images: bullets labelled "REF <name>", or any labelled bullet under a "reference" heading in section B
refs, under = [], False
for line in bible.split('\n'):
    if re.search(r'reference', line, re.I) and not line.lstrip().startswith('-'): under = True; continue
    m = re.match(r'^\s*[-*]\s*\*\*\s*(REF\s+)?([^*:]+?)\s*:?\s*\*\*\s*:?\s*(.+)$', line)
    if m and (m.group(1) or under) and len(m.group(3)) > 40:
        name = m.group(2).strip()
        refs.append({'name': name, 'id': 'ref-' + re.sub(r'[^a-z0-9]+', '-', name.lower()).strip('-'), 'prompt': m.group(3).strip()})
    elif under and line.strip() and not line.lstrip().startswith('-'): under = False

# ------------------------------------------------------------------ scenes
def secs(s):
    p = [float(x) for x in s.strip().split(':')]
    return p[0] * 60 + p[1] if len(p) == 2 else p[0] * 3600 + p[1] * 60 + p[2] if len(p) == 3 else p[0]

LABELS = {'prompt': r'Image prompt', 'move': r'(?:Editor move|Camera(?: move)?)', 'atmos': r'Animated atmosphere',
          'narr': r'(?:Narrator|Narration)', 'sound': r'Sound(?: design)?'}
scenes, act = [], None
blocks = re.split(r'(?m)^(?=\s*\**\s*SCENE\s+\d+)', sec['C'])
for b in blocks:
    head = re.match(r'\s*\**\s*SCENE\s+(\d+)\s*\|\s*([\d:.]+)\s*[\u2013\u2014-]+\s*([\d:.]+)', b)
    if not head:
        for line in b.split('\n'):
            m = re.match(r'^\s*(?:#{1,6}\s*|\*\*)\s*(ACT\s+[^*]+?)\s*\**\s*$', line, re.I)
            if m: act = m.group(1).strip()
        continue
    body = b[head.end():]
    pos = sorted((m.start(), m.end(), k) for k, lab in LABELS.items() for m in [re.search(r'\*\*\s*' + lab + r'\s*:?\s*\*\*\s*:?', body, re.I)] if m)
    f = {}
    for i, (s0, s1, k) in enumerate(pos):
        txt = body[s1:pos[i + 1][0] if i + 1 < len(pos) else len(body)]
        txt = re.split(r'(?m)^\s*(?:#{1,6}\s|\*\*\s*ACT\s)', txt)[0]
        f[k] = ' '.join(txt.split()).strip()
    nxt_act = re.findall(r'(?m)^\s*(?:#{1,6}\s*|\*\*)\s*(ACT\s+[^*\n]+?)\s*\**\s*$', body, re.I)
    narr = (f.get('narr') or '').strip().strip('"“”').strip()
    if re.fullmatch(r'\(?\s*no narration\.?\s*\)?', narr, re.I) or narr.lower().startswith('no narration'): narr = ''
    atm = f.get('atmos') or ''
    if re.fullmatch(r'none\.?', atm.strip(), re.I): atm = ''
    n = int(head.group(1))
    scenes.append({'scene': n, 'start': secs(head.group(2)), 'end': secs(head.group(3)), 'act': act, 'prompt': f.get('prompt', ''),
                   'move': f.get('move', ''), 'atmos': atm, 'narration': narr, 'sound': f.get('sound', '')})
    for k in ('prompt', 'move'):
        if not f.get(k): warn(f'scene {n}: no {LABELS[k]}')
    if nxt_act: act = nxt_act[-1].strip()
if not scenes: die('no scenes found in section C (expected "**SCENE 1 | 0:00-0:06**" headers)')
nums = [s['scene'] for s in scenes]
if nums != list(range(1, len(scenes) + 1)): warn(f'scene numbers are not 1..{len(scenes)} in order: {nums}')
for s in scenes:
    if s['end'] <= s['start']: warn(f"scene {s['scene']}: end {s['end']} is not after start {s['start']}")
N = len(scenes)
sid = lambda n: f's{n:02d}'

# ------------------------------------------------------------------ narration and word anchors
vo = sec.get('D', '').strip()
tts = re.sub(r'\[(?:pause|beat|long pause)[^\]]*\]|\((?:pause|beat)[^)]*\)', '...', vo, flags=re.I)
tts = '\n\n'.join(' '.join(p.split()) for p in re.split(r'\n\s*\n', tts) if p.strip())
if not tts: tts = '\n\n'.join(s['narration'] for s in scenes if s['narration']); warn('no section D: narration.txt built from the scene lines')
toks = []                                   # (scene, word) in spoken order
for s in scenes:
    toks += [(s['scene'], norm(w)) for w in s['narration'].replace('-', ' ').split() if norm(w)]

def anchor(word, scene):
    """time reference for a word spoken in (or nearest after) a scene: w:word#k, k = occurrence in the whole narration"""
    w = norm(word); occ = 0
    if w not in {t for _, t in toks}:                      # "light" -> "lights", "lit" stays unmatched (warned)
        forms = sorted({t for _, t in toks if t.startswith(w) and len(t) - len(w) <= 3}, key=len)
        if forms: w = forms[0]
    for sc, t in toks:
        if t == w:
            occ += 1
            if sc >= scene: return f'w:{w}#{occ}' if occ > 1 else f'w:{w}'
    return None

def quoted(text):
    return re.findall(r'["“‘\']([A-Za-z][A-Za-z\']*)["”’\']', text)

def scene_word(text, n):
    for q in quoted(text):
        r = anchor(q, n)
        if r: return r
        warn(f'scene {n}: the word "{q}" is not in the narration from this scene on; using a scene time instead')
    return None

# ------------------------------------------------------------------ match cuts (section G item 4, or "same angle as scene N")
pairs = set()
for m in re.finditer(r'scenes?\s+(\d+)\s*(?:and|&|/|,)\s*(?:scene\s+)?(\d+)', sec.get('G', ''), re.I):
    if 'match' in sec['G'][max(0, m.start() - 400):m.end() + 200].lower(): pairs.add(tuple(sorted((int(m.group(1)), int(m.group(2))))))
for s in scenes:
    m = re.search(r'(?:same (?:angle|framing|composition) as|matching|match(?:es)?)\s+scene\s+(\d+)', s['prompt'] + ' ' + s['move'], re.I)
    if m and int(m.group(1)) != s['scene']: pairs.add(tuple(sorted((int(m.group(1)), s['scene']))))
pairs = sorted(p for p in pairs if 1 <= p[0] <= N and 1 <= p[1] <= N and p[0] != p[1])
partner = {b: a_ for a_, b in pairs}

# ------------------------------------------------------------------ generation list
EXPLICIT = any(re.search(r'\bREF\s+\w', s['prompt']) for s in scenes)   # prompts name references as "(REF Ada)"
def refs_in(text):
    out = []
    for r in refs:
        rx = (r'\bREF\s+' if EXPLICIT else r'\b') + re.escape(r['name']) + r'\b'
        if re.search(rx, text, re.I): out.append(r['id'])
    return out

gen_scenes = []
for s in scenes:
    p = s['prompt']
    if suffix and not p.rstrip(' .').endswith(suffix.rstrip(' .')):
        warn(f"scene {s['scene']}: prompt did not end with the style suffix; appended it")
        p = p.rstrip() + ' ' + suffix
    if re.search(r'\b(text|sign|signage|logo|caption|letters|words)\b', re.sub(r'no text|no logos?|no signage|no readable text', '', p, flags=re.I), re.I):
        warn(f"scene {s['scene']}: the prompt mentions text/signs/logos; image generators garble text")
    g = {'id': sid(s['scene']), 'scene': s['scene'], 'prompt': p, 'refs': refs_in(s['prompt'])}
    if s['scene'] in partner: g['match'] = sid(partner[s['scene']]); g['note'] = f"same framing as {sid(partner[s['scene']])}: pass that picture as a reference too"
    gen_scenes.append(g)
for r in refs:
    if suffix and not r['prompt'].rstrip(' .').endswith(suffix.rstrip(' .')): r['prompt'] = r['prompt'].rstrip() + ' ' + suffix
slug = re.sub(r'[^a-z0-9]+', '-', title.lower()).strip('-')[:40] or 'story-film'
generate = {'title': title, 'slug': slug, 'aspect_ratio': aspect, 'style_suffix': suffix,
            'flow_folder': f'~/flow-mcp-out/{slug}', 'references': refs, 'scenes': gen_scenes, 'match_pairs': [[sid(x), sid(y)] for x, y in pairs]}

# ------------------------------------------------------------------ edit plan (first draft)
def speed(t):
    t = t.lower()
    return 0.38 if re.search(r'abrupt|fast|quick|sudden|snap', t) else 0.28 if re.search(r'medium|steady|moderate', t) else 0.18

def recipe(move):
    """editor move text -> (kind, key list as [(u, fx, fy, z)], u = 0..1 along the shot), following creative-direction.md"""
    t = move.lower(); dz = speed(t)
    right = 'left' not in t or t.find('right') > -1 and t.find('right') < t.find('left')
    if re.search(r'pull[- ]?(out|back)|zoom out|reveal', t):
        return 'pull', [(0, 0.48, 0.45, 1.16 + dz), (1, 0.5, 0.5, 1.03)]
    if re.search(r'push[- ]?in|zoom in|push toward|move in', t):
        if re.search(r'static|hold', t) and re.search(r'then', t):
            return 'hold-push', [(0, 0.5, 0.48, 1.04), (0.4, 0.5, 0.48, 1.04), (1, 0.5, 0.45, 1.04 + dz)]
        return 'push', [(0, 0.5, 0.48, 1.04), (1, 0.5, 0.45, 1.04 + dz)]
    if re.search(r'\btilt', t):
        up = 'down' not in t or ('up' in t and t.find('up') < t.find('down'))
        return 'tilt', [(0, 0.5, 0.70 if up else 0.38, 1.4), (1, 0.5, 0.38 if up else 0.70, 1.28)]
    if re.search(r'\bpan|truck|slide', t):
        return 'pan', [(0, 0.40 if right else 0.60, 0.5, 1.22), (1, 0.60 if right else 0.40, 0.5, 1.22)]
    if re.search(r'drift', t):
        if re.search(r'static|hold', t):
            return 'hold-drift', [(0, 0.48, 0.5, 1.10), (0.45, 0.48, 0.5, 1.10), (1, 0.56 if right else 0.40, 0.48, 1.10 + dz * 0.6)]
        return 'drift', [(0, 0.45 if right else 0.55, 0.52, 1.10), (1, 0.55 if right else 0.45, 0.46, 1.10 + dz * 0.7)]
    if re.search(r'static|hold|still|locked', t):
        return 'still', [(0, 0.5, 0.5, 1.02)]
    warn(f'editor move not recognised, using a gentle push-in: "{move[:60]}"')
    return 'push', [(0, 0.5, 0.48, 1.04), (1, 0.5, 0.46, 1.16)]

shots, prev_kind = [], None
for i, s in enumerate(scenes):
    n = s['scene']; kind, ks = recipe(s['move'])
    if n in partner:                                      # matched framing: same recipe as its partner
        kind, ks = recipe(scenes[partner[n] - 1]['move'])
    if kind == prev_kind and kind in ('push', 'pull', 'pan', 'drift') and n not in partner:
        ks = [(u, 1 - fx if kind in ('pan', 'drift') else fx, fy, z) for u, fx, fy, z in ks]   # neighbours differ: mirror direction
        if kind in ('push', 'pull'): ks = [(u, fx + (0.06 if j else 0), fy, z) for j, (u, fx, fy, z) in enumerate(ks)]
    prev_kind = kind
    dur = s['end'] - s['start']
    t0 = 0 if i == 0 else f's{n}'; t1 = f's{n + 1}' if i + 1 < N else f'e{n}'
    def at(u):
        if u <= 0: return t0
        if u >= 1: return t1
        return f's{n}+{round(min(2.4, dur * u), 2)}' if i else round(min(2.4, dur * u), 2)
    keys = [[at(u), round(fx, 3), round(fy, 3), round(z, 3)] for u, fx, fy, z in ks]
    if i == 0: tin = ['dip', 'black', 0, 1.6]
    elif n in partner: tin = ['dissolve', 0.8]
    elif s['act'] != scenes[i - 1]['act']: tin = ['dip', 'black', 0.45, 0.65]
    elif re.search(r'\bflash', s['atmos'] + ' ' + s['move'], re.I): tin = ['flash', 'white', 0.08, 0.35]
    else: tin = ['cut']
    shot = {'id': f'{n:02d}', 'pic': sid(n), 't0': t0, 't1': t1, 'keys': keys, 'in': tin, 'note': f"{kind}: {s['move'][:80]}"}
    if kind == 'still': shot['still'] = True
    if re.search(r'shake|impact|slam|crash|explo', s['move'] + ' ' + s['atmos'], re.I):
        shot['shake'] = [{'from': t0, 'to': at(0.3), 'amp': 0.012, 'hz': 11, 'decay': 0.5}]
    shots.append(shot)
edit = {'shots': shots, 'fade_out': [f'e{N}-2.2', f'e{N}-0.3'], 'no_caption': [], 'captions': True}

# ------------------------------------------------------------------ layers: atmosphere effects, draft plates, graphics
layers, plates = [], []
EFFECTS = [('blizzard', r'blizzard'), ('snow', r'\bsnow'), ('rain', r'\brain\b|downpour|drizzle'), ('dust', r'\bdust|motes'),
           ('embers', r'\bembers?|\bash\b|cinders'), ('sparks', r'\bsparks?\b'), ('burn', r'film burn|light leak'),
           ('oldfilm', r'old film|archival|scratches|sepia')]
LIGHT = r'\blight|lamp|lantern|glow|pulse|flicker|flash|blink|window|beacon|switch(?:es)? on|turns? on|appears'
effect_runs = {}
for s in scenes:
    n, t = s['scene'], s['atmos']
    if not t: continue
    whole = re.search(r'throughout|whole film|entire film', t, re.I)
    for kind, rx in EFFECTS:
        if re.search(rx, t, re.I):
            if kind == 'snow' and re.search(r'blizzard', t, re.I): continue
            effect_runs.setdefault(kind, []).append((1, N) if whole else (n, n))
    for sent in re.split(r'(?<=[.;])\s+', t):
        if not re.search(LIGHT, sent, re.I) or re.fullmatch(r'\s*(film )?grain[^.]*\.?', sent, re.I): continue
        if re.search(r'old film|film grain|film burn|archival|sepia', sent, re.I): continue   # film texture, not a light in the picture
        if not re.search(r'light|lamp|lantern|glow|pulse|flicker|flash|blink|window|beacon', sent, re.I): continue
        w = scene_word(sent, n) or f's{n}+0.6'
        col = 'warm' if re.search(r'lamp|lantern|warm|amber|fire|candle', sent, re.I) else 'red' if re.search(r'\bred\b', sent, re.I) else 'cold'
        many = re.search(r'one after another|in sequence|one by one|then a second|another', sent, re.I)
        if re.search(r'flicker', sent, re.I): env = {'flicker': {'lo': 0.55, 'hi': 1.0, 'rate': 9, 'seed': n}}
        elif re.search(r'pulse|blink|throb', sent, re.I): env = {'max': [{'flashes': {'times': [w], 'decay': 0.5}}, {'pulse': {'period': 1.4, 'duty': 0.5, 't0': w, 't1': f'e{n}', 'lo': 0.2, 'hi': 0.85, 'soft': 0.4}}]}
        elif re.search(r'flash', sent, re.I): env = {'flashes': {'times': [w], 'decay': 0.14}}
        else: env = {'keys': [[w if w.startswith('s') else f'{w}-0.05', 0], [f'{w}+0.3' if w.startswith('w:') else f's{n}+0.9', 1]]}
        lights = [{'x': 0.5, 'y': 0.42, 'r': 0.16, 'rgb': col, 'a': env}]
        if many:
            for k in range(1, 3):
                lights.append({'x': 0.5 + 0.08 * k, 'y': 0.46, 'r': 0.10, 'rgb': col, 'a': {'keys': [[f's{n}+{1.0 + 0.7 * k:.1f}', 0], [f's{n}+{1.3 + 0.7 * k:.1f}', 1]]}})
        plates.append({'id': f'p{n:02d}', 'kind': 'plate', 'pic': sid(n), 'draft': True,
                       'todo': f'place each light on the picture (read qa/grid/{sid(n)}.jpg: x, y = fractions; r = size), add a patch if the light is baked in and must start dark, then delete "draft" and set shot {n:02d} "pic" to "p{n:02d}". Cue: {sent.strip()}',
                       'lights': lights})
for kind, runs in effect_runs.items():                     # merge neighbouring scenes into one layer
    runs = sorted(set(runs)); merged = []
    for x, y in runs:
        if merged and x <= merged[-1][1] + 1: merged[-1] = (merged[-1][0], max(y, merged[-1][1]))
        else: merged.append((x, y))
    for k, (x, y) in enumerate(merged):
        L = {'id': f'{kind}{k + 1}', 'kind': kind, 't0': 0 if x == 1 else f's{x}', 't1': f'e{y}'}
        if kind == 'burn': L['mid'] = 0.5
        layers.append(L)

def lines_of(text, maxc=16):
    out, cur = [], ''
    for w in text.split():
        if cur and len(cur) + 1 + len(w) > maxc: out.append(cur); cur = w
        else: cur = (cur + ' ' + w).strip()
    return out + ([cur] if cur else [])

def spoken_span(text, n):
    """if the phrase is spoken (from scene n on), return (first word ref, last word ref)"""
    ws = [norm(w) for w in text.split() if norm(w)]
    if not ws: return None
    flat = [t for _, t in toks]; sc_of = [sc for sc, _ in toks]
    for k in range(len(flat) - len(ws) + 1):
        if flat[k:k + len(ws)] == ws and sc_of[k] >= n:
            occ = lambda j: sum(1 for x in flat[:j + 1] if x == flat[j])
            ref = lambda j: f'w:{flat[j]}#{occ(j)}' if occ(j) > 1 else f'w:{flat[j]}'
            return ref(k), ref(k + len(ws) - 1)
    return None

def last_word_ref(n):
    sc = [t for c, t in toks if c == n]
    if not sc: return None
    k = max(j for j, (c, _) in enumerate(toks) if c == n); w = toks[k][1]
    occ = sum(1 for _, t in toks[:k + 1] if t == w)
    return f'w:{w}#{occ}.end' if occ > 1 else f'w:{w}.end'

def first_sentence_end(n):
    s = scenes[n - 1]['narration']
    first = re.split(r'(?<=[.!?])\s', s)[0]
    ws = [norm(w) for w in first.split() if norm(w)]
    if not ws: return None
    k = [j for j, (c, _) in enumerate(toks) if c == n][len(ws) - 1]; w = toks[k][1]
    occ = sum(1 for _, t in toks[:k + 1] if t == w)
    return f'w:{w}#{occ}.end' if occ > 1 else f'w:{w}.end'

TOP, CANVAS_H = (118, 190), 1920 if aspect == '9:16' else 1080
counts = {}
for line in sec.get('F', '').split('\n'):
    if not re.match(r'^\s*[-*\d]', line): continue
    low = line.lower()
    q = re.findall(r'["“]([^"”]+)["”]', line)
    if not q: continue
    text = q[0].strip()
    m = re.search(r'scene\s+(\d+)', low); n = int(m.group(1)) if m else 1
    n = min(max(n, 1), N)
    wref = None
    m = re.search(r'\bon\s+["“‘\']([A-Za-z\']+)["”’\']', line)
    if m: wref = anchor(m.group(1), n)
    def lid(base):
        counts[base] = counts.get(base, 0) + 1
        return base if counts[base] == 1 else f'{base}{counts[base]}'
    if 'act' in low and 'card' in low:
        kick, _, rest = text.partition(':')
        lines = [{'text': kick.strip().upper(), 't': f's{n}+0.15', 'class': 'kick', 'y': TOP[0]}]
        if rest.strip(): lines.append({'text': rest.strip().upper(), 't': f's{n}+0.5', 'stagger': 0.22, 'class': 'card', 'y': TOP[1]})
        layers.append({'id': lid('act'), 'kind': 'type', 'backdrop': 'top', 't0': f's{n}+0.05', 'out': f's{n}+3.2', 'lines': lines})
    elif re.search(r'key phrase|key line|stamp|tagline', low):
        span = spoken_span(text, n)
        if span:
            layers.append({'id': lid('key'), 'kind': 'type', 'style': 'key', 'glow': 'warm', 'lines': [{'from': span[0], 'to': span[1], 'y': round(CANVAS_H * 0.42)}]})
            edit['no_caption'].append([f'{span[0]}-0.3', f'{span[1]}.end+1.6'.replace('.end.end', '.end')])
        else:
            t = wref or f's{n}+0.4'
            layers.append({'id': lid('key'), 'kind': 'type', 'style': 'key', 'glow': 'warm', 'lines': [{'text': text.upper(), 't': t, 'stagger': 0.25, 'y': round(CANVAS_H * 0.42)}]})
    elif re.search(r'date|location|place|time stamp|label|years', low):
        layers.append({'id': lid('label'), 'kind': 'type', 'backdrop': 'top', 't0': f's{n}+0.15', 'out': f's{n}+2.7',
                       'lines': [{'typed': text.upper(), 't': f's{n}+0.3', 'cps': 18, 'class': 'typed', 'y': 120}]})
    elif re.search(r'title|end card|credit|closing', low):
        end = 'end card' in low or 'closing' in low or 'credit' in low
        span = None if end else spoken_span(text, n)
        rows = lines_of(text.upper())
        y0 = round(CANVAS_H / 2 - (len(rows) * 190) / 2)
        if span:
            layers.append({'id': lid('title'), 'kind': 'type', 'style': 'title', 'glow': '150,190,255', 'backdrop': 'center', 'lines': [{'from': span[0], 'to': span[1], 'y': y0}]})
            edit['no_caption'].append([f'{span[0]}-0.3', f'{span[1]}.end+1.6'])
        else:
            if wref: t = wref
            elif re.search(r'after the (last|final) line', low) or end: t = (last_word_ref(n) or f's{n}') + '+0.5'
            elif 'after the first line' in low: t = (first_sentence_end(n) or f's{n}') + '+0.3'
            else: t = f's{n}+0.6'
            t = t.replace('.end+', '.end+')
            L = {'id': lid('end' if end else 'title'), 'kind': 'type', 'style': 'title', 'glow': '150,190,255', 'backdrop': 'center',
                 'lines': [{'text': r, 't': t if k == 0 else f'{t}+{0.25 * len(rows[0].split()) * k + 0.1:.2f}'.replace('+-', '-'), 'stagger': 0.25, 'y': y0 + 200 * k} for k, r in enumerate(rows)]}
            if end: L['out'] = f'e{N}-0.4'
            layers.append(L)
    else:
        warn(f'section F line not recognised (title, act card, key phrase, label or end card): {line.strip()[:70]}')
layers += plates

# time refs like "w:x#2.end+0.5" are valid; tidy "w:x.end+0.3+0.25" (two offsets) into one number
def tidy(ref):
    if not isinstance(ref, str): return ref
    m = re.fullmatch(r'(.+?)([+-][\d.]+)([+-][\d.]+)', ref)
    return f'{m.group(1)}{float(m.group(2)) + float(m.group(3)):+.2f}' if m else ref
for L in layers:
    for ln in L.get('lines', []):
        if 't' in ln: ln['t'] = tidy(ln['t'])

# ------------------------------------------------------------------ sound: a first cue sheet
E = sec.get('E', '')
cue = ["// First draft cue sheet written by ingest_storyboard.py from the storyboard's Sound design lines and section E.",
       '// Times are references (scene starts, spoken words). Refine it like a composer: see references/creative-direction.md.',
       'export default function (s) {',
       '  const { t, END, pad, drone, tone, piano, arp, boom, thud, riser, ostinato, heartbeat, whum, silence, chord, midi,',
       '          wind, rain, fire, rumble, crowd, steps, crunch, clunk, creak, glass, whoosh, rustle, birdsong } = s;']
drone_on, wind_on, sil = [], [], []
for s in scenes:
    n, t = s['scene'], s['sound'].lower()
    a0, a1 = 's1' if n == 1 else f's{n}', f'e{n}'
    acc = scene_word(s['atmos'], n) if s['atmos'] else None
    q = quoted(s['sound']); acc = (anchor(q[0], n) if q else None) or acc
    hit = f"t('{acc}')" if acc else f"t('s{n}') + 0.4"
    cue.append(f"  // scene {n}: {s['sound'][:110]}")
    if re.search(r'silence|silent|cut out|drops? out', t): sil.append(n)
    if re.search(r'\bwind|gust|ice\b', t): wind_on.append(n)
    if re.search(r'drone|low bed|low hum', t) and not re.search(r'drone (?:cut|stops|drops)|cut(?:s)? out', t): drone_on.append(n)
    if re.search(r'piano', t): cue.append(f"  piano({hit}, midi('A4'), 0.55, {{ len: 4 }});")
    if re.search(r'footstep|steps', t): cue.append(f"  steps([0.6, 1.6, 2.6, 3.6].map((d) => t('s{n}') + d), 0.4, {{ surface: '{'wood' if 'wood' in t else 'frost' if re.search('snow|frost|ice', t) else 'stone'}' }});")
    if re.search(r'creak', t): cue.append(f"  creak(t('s{n}') + 1.2, 0.9, 0.3);")
    if re.search(r'click|clunk|metal|lever|latch|door', t): cue.append(f"  clunk({hit} - 0.1, 0.5);")
    if re.search(r'whum|swell of light|glow', t): cue.append(f"  whum({hit}, 0.7);")
    if re.search(r'riser|building|build', t): cue.append(f"  riser({hit}, t('e{n}'), 0.6);")
    if re.search(r'boom|impact|\bhit\b|slam', t): cue.append(f"  boom({hit}, 0.8);")
    if re.search(r'heartbeat', t): cue.append(f"  heartbeat(t('{a0}'), t('{a1}'), 0.9, 0.6);")
    if re.search(r'string|swell|warm', t): cue.append(f"  pad(t('{a0}'), END, chord('F'), 0.8, {{ attack: 2.5 }}); pad(t('{a0}') + 2, END, chord('C', 4), 0.4, {{ attack: 3 }});")
    if re.search(r'voices|crowd|children|people', t): cue.append(f"  crowd(t('{a0}') + 1, t('{a1}'), 0.22);")
    if re.search(r'\brain', t): cue.append(f"  rain(t('{a0}'), t('{a1}'), 0.6);")
    if re.search(r'fire|crackl', t): cue.append(f"  fire(t('{a0}'), t('{a1}'), 0.5);")
    if re.search(r'bird', t): cue.append(f"  birdsong(t('{a0}') + 0.5, t('{a1}'), 0.4);")
    if re.search(r'glass|shatter', t): cue.append(f"  glass({hit}, 0.5);")
    if re.search(r'whoosh|rush', t): cue.append(f"  whoosh({hit} - 0.3, 0.8, 0.4);")
def runs(ns):
    out = []
    for n in sorted(set(ns)):
        if out and n == out[-1][1] + 1: out[-1][1] = n
        else: out.append([n, n])
    return out
if re.search(r'wind[^.]*(under everything|throughout|whole film)', bible, re.I): wind_on = list(range(1, N + 1))
for x, y in runs(wind_on):
    st = '-1.5' if x == 1 else "t('s%d')" % x
    cue.append(f"  wind({st}, t('e{y}'), {0.9 if y < N else 0.7}, {{ fade: 2 }});")
for x, y in runs(drone_on):
    st = '-1.0' if x == 1 else "t('s%d')" % x
    cue.append(f"  drone({st}, t('e{y}'), 26, 0.9, {{ attack: 3 }});")
for x, y in runs(sil): cue.append(f"  silence(t('s{x}'), t('e{y}'));")
for L in layers:
    if L['kind'] == 'type' and L.get('style') == 'key' and 'from' in L['lines'][0]:
        cue.append(f"  thud(t('{L['lines'][0]['from']}'), 0.7);  // hit on the key phrase")
    if L['kind'] == 'type' and L['id'] == 'title':
        ln = L['lines'][0]; cue.append(f"  boom(t('{ln.get('from') or ln.get('t')}'), 0.6);  // the title lands")
if E: cue.append('  // Section E (audio direction):\n' + '\n'.join('  //   ' + l.strip() for l in E.split('\n') if l.strip()))
cue.append('}')

# ------------------------------------------------------------------ write
plan = os.path.join(root, 'plan'); os.makedirs(plan, exist_ok=True)
for f in ('script.json', 'edit.json', 'layers.json', 'cue.mjs', 'generate.json'):
    if os.path.exists(os.path.join(plan, f)) and not a.force: die(f'{plan}/{f} exists; pass --force to overwrite the plan')
save(os.path.join(plan, 'storyboard.json'), {'title': title, 'aspect_ratio': aspect, 'narrator': narrator, 'voice_direction': voice_dir,
     'style_suffix': suffix, 'references': refs, 'scenes': scenes, 'match_pairs': pairs, 'sections': {k: v for k, v in sec.items() if k in 'ABEFGH'}})
save(os.path.join(plan, 'script.json'), [{'scene': s['scene'], 'act': s['act'], 'narration': s['narration'], 'visual': s['prompt'],
     'camera': s['move'], 'sound': s['sound'] or None, 'atmosphere': s['atmos'] or None} for s in scenes])
save(os.path.join(plan, 'scenes.json'), [{'scene': s['scene'], 'start': s['start'], 'end': s['end'], 'dur': round(s['end'] - s['start'], 3),
     'text': s['narration'], 'provisional': True} for s in scenes])
open(os.path.join(plan, 'narration.txt'), 'w').write(tts + '\n')
words = len(re.findall(r"[A-Za-z0-9']+", tts)); planned = scenes[-1]['end']
save(os.path.join(plan, 'voice.json'), {'direction': ' '.join(voice_dir.split()), 'gender': gender, 'words': words, 'planned_seconds': planned,
     'planned_wpm': round(words / planned * 60) if planned else None})
save(os.path.join(plan, 'generate.json'), generate)
save(os.path.join(plan, 'edit.json'), edit)
save(os.path.join(plan, 'layers.json'), {'layers': layers})
open(os.path.join(plan, 'cue.mjs'), 'w').write('\n'.join(cue) + '\n')
if not os.path.exists(os.path.join(root, 'project.json')):
    vert = aspect == '9:16'; w, h = (1536, 2752) if vert else (2752, 1536)
    save(os.path.join(root, 'project.json'), {
        'name': title, 'draft': True, 'fps': 30, 'canvas': [1080, 1920] if vert else [1920, 1080], 'pre': 1.5,
        'narration': None, 'narration_dur': planned, 'music': None,
        'images': {sid(s['scene']): {'file': f"input/images/{sid(s['scene'])}.jpg", 'w': w, 'h': h, 'source_px': [w // 2, h // 2], 'planned': True} for s in scenes},
        'look': {'captions': {'font': 'assets/fonts/Montserrat-SemiBold.otf', 'size': 9.5, 'y': -0.74, 'max_chars': 34},
                 'letterbox': None if vert else 2.0, 'vignette': True}})
    made = 'project.json (draft) + '
else: made = ''

print(f'"{title}": {N} scenes, {planned:.1f} s planned, {aspect}, {len(refs)} reference images, {len(pairs)} match-cut pair(s)')
print(f'narration: {words} words ({round(words / planned * 60) if planned else 0} words per minute planned); voice: {gender}; direction: {voice_dir[:90]}')
print(f'wrote {made}plan/: storyboard.json script.json scenes.json (provisional) narration.txt voice.json generate.json edit.json layers.json cue.mjs')
print(f"  shots: {len(shots)}; layers: {sum(1 for L in layers if not L.get('draft'))} ready + {len(plates)} draft light plate(s) to place after the pictures exist")
for w in warnings: print('warning:', w)
print('next: python3 scripts/lint_edit.py', root)
