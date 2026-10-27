#!/usr/bin/env python3
"""Look at the pictures before planning: qa/pictures.jpg (every picture, labelled with its id) and qa/grid/<id>.jpg
(each picture with a 5 % grid and labels, to read focus points, faces and light sources as fractions 0..1).

  python3 scripts/contact.py <project> [--ids s01,s07]

With plan/generate.json (storyboard films) it also prints the scene-to-picture map and the scenes still missing a
picture (planned entries in project.json), and draws them as MISSING cells: regenerate only those.

Read the grids to choose framing keys (fx, fy) and where lights sit for living plates. Note letterboxed pictures, split
panels (diptychs) and baked-in black bars: those shots need "bounds" in edit.json so the camera never shows them.
"""
import argparse, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import Project
from PIL import Image, ImageDraw, ImageFont

ap = argparse.ArgumentParser(); ap.add_argument('project'); ap.add_argument('--ids'); a = ap.parse_args()
P = Project(a.project); ids = a.ids.split(',') if a.ids else sorted(P.cfg['images'])
missing = [i for i in ids if P.cfg['images'].get(i, {}).get('planned') or not os.path.exists(P.p(P.image(i)['file']))]
if os.path.exists(P.p('plan/generate.json')):
    import json
    for g in json.load(open(P.p('plan/generate.json')))['scenes']:
        im = P.cfg['images'].get(g['id'], {}); src = im.get('source', '-') if g['id'] not in missing else 'MISSING'
        print(f"  scene {g['scene']:3d}  {g['id']:6s} {src}")
def font(n):
    for f in ('/System/Library/Fonts/Supplemental/Arial Bold.ttf', '/Library/Fonts/Arial Bold.ttf', 'C:/Windows/Fonts/arialbd.ttf'):
        if os.path.exists(f): return ImageFont.truetype(f, n)
    return ImageFont.load_default()
F40, F16 = font(36), font(16)
os.makedirs(P.p('qa/grid'), exist_ok=True)
tw, th, cols = 640, 360, 3
rows = (len(ids) + cols - 1) // cols
sheet = Image.new('RGB', (tw * cols, th * rows), (20, 20, 20))
for n, pid in enumerate(ids):
    if pid in missing:
        cell = Image.new('RGB', (tw, th), (60, 14, 14)); d = ImageDraw.Draw(cell); d.text((20, 140), f'{pid} MISSING', font=F40, fill=(255, 120, 120))
        sheet.paste(cell, ((n % cols) * tw, (n // cols) * th)); continue
    im = Image.open(P.p(P.image(pid)['file'])).convert('RGB')
    t = im.copy(); t.thumbnail((tw, th)); cell = Image.new('RGB', (tw, th), (20, 20, 20)); cell.paste(t, ((tw - t.width) // 2, (th - t.height) // 2))
    d = ImageDraw.Draw(cell); lab = pid[:22]; d.rectangle((0, 0, 14 + 21 * len(lab), 46), fill=(0, 0, 0)); d.text((8, 4), lab, font=F40, fill=(255, 214, 0))
    sheet.paste(cell, ((n % cols) * tw, (n // cols) * th))
    g = im.resize((1376, round(1376 * im.height / im.width))); dg = ImageDraw.Draw(g); gw, gh = g.size
    for k in range(1, 20):
        c = (0, 255, 255) if k % 2 == 0 else (255, 255, 0)
        dg.line((gw * k / 20, 0, gw * k / 20, gh), fill=c); dg.line((0, gh * k / 20, gw, gh * k / 20), fill=c)
        dg.text((gw * k / 20 + 2, 2), str(k * 5), font=F16, fill=c); dg.text((2, gh * k / 20 + 2), str(k * 5), font=F16, fill=c)
    g.save(P.p(f'qa/grid/{pid}.jpg'), quality=82)
sheet.save(P.p('qa/pictures.jpg'), quality=85)
if missing: print(f'MISSING pictures ({len(missing)}): {", ".join(missing)}: regenerate only these, then collect_pictures.py + new_project.py --update')
print(f'qa/pictures.jpg ({len(ids)} pictures) and qa/grid/<id>.jpg (5 % grid: read positions as fractions)')
