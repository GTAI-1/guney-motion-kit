#!/usr/bin/env python3
"""Copy generated pictures into the film's picture folder under their scene ids, then report coverage.

  python3 scripts/collect_pictures.py <project> --from <folder> [--ids s03,s07,...] [--map scene-01=s01,scene-02=s02]
  python3 scripts/collect_pictures.py <project> --check

Flow saves stills as ~/flow-mcp-out/<folder>/scene-01.png, scene-02.png ... in the order of the batch that made them.
Default: the files in --from (sorted by name) go to the scene ids of plan/generate.json in order; --ids gives the ids of
a partial batch (a regeneration of missing scenes); --map names each file exactly. Copies only (the originals stay),
into <project>/media/stills/<id>.<ext>; an existing picture with that id is moved to media/stills/replaced/<id>.<n>.<ext> (kept, not deleted).
--check (or after copying) lists which scenes of plan/generate.json have a picture and which are still missing.
Then: python3 scripts/new_project.py <project> --update --images <project>/media/stills
"""
import argparse, json, os, shutil, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import die

ap = argparse.ArgumentParser(); ap.add_argument('project'); ap.add_argument('--from', dest='src'); ap.add_argument('--ids'); ap.add_argument('--map')
ap.add_argument('--check', action='store_true'); a = ap.parse_args()
root = os.path.abspath(a.project); gen = os.path.join(root, 'plan/generate.json')
if not os.path.exists(gen): die('no plan/generate.json (run ingest_storyboard.py first)')
G = json.load(open(gen)); want = [s['id'] for s in G['scenes']]
dst = os.path.join(root, 'media/stills'); os.makedirs(dst, exist_ok=True)
EXT = ('.png', '.jpg', '.jpeg', '.webp')
if a.src and not a.check:
    src = os.path.expanduser(a.src)
    files = sorted(f for f in os.listdir(src) if f.lower().endswith(EXT) and not f.startswith('.'))
    if a.map: pairs = [tuple(x.split('=')) for x in a.map.split(',')]; pairs = [(next(f for f in files if os.path.splitext(f)[0] == k or f == k), v) for k, v in pairs]
    else:
        ids = a.ids.split(',') if a.ids else want
        if len(files) != len(ids): print(f'note: {len(files)} files for {len(ids)} ids; pairing in order, extra ones ignored')
        pairs = list(zip(files, ids))
    for f, pid in pairs:
        ext = os.path.splitext(f)[1].lower()
        for old in [x for x in os.listdir(dst) if os.path.splitext(x)[0] == pid and x.lower().endswith(EXT)]:
            rep = os.path.join(dst, 'replaced'); os.makedirs(rep, exist_ok=True); k = 1
            while os.path.exists(os.path.join(rep, f'{pid}.{k}{os.path.splitext(old)[1]}')): k += 1
            os.rename(os.path.join(dst, old), os.path.join(rep, f'{pid}.{k}{os.path.splitext(old)[1]}'))
        shutil.copy2(os.path.join(src, f), os.path.join(dst, pid + ext)); print(f'  {f} -> media/stills/{pid}{ext}')
have = {os.path.splitext(x)[0] for x in os.listdir(dst) if x.lower().endswith(EXT) }
missing = [i for i in want if i not in have]
print(f'{len(want) - len(missing)} of {len(want)} scenes have a picture' + (f'; missing: {", ".join(missing)}' if missing else ''))
sys.exit(1 if missing else 0)
