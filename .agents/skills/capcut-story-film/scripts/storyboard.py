#!/usr/bin/env python3
"""Storyboard of the planned camera: qa/storyboard-<n>.jpg, every shot's FIRST and LAST frame exactly as CapCut will
frame it (same clamping math as the builder), labelled with id, time, length, transition and note.

  python3 scripts/storyboard.py <project>

Look at every pair before building: is the subject in frame at both ends? does the move go somewhere meaningful? do
neighbouring shots differ (scale, direction, subject)? any black bars or panel seams showing? Fix edit.json and re-run.
"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import Project, place, visible_rect, frame_at
from planfile import resolve_edit
from PIL import Image, ImageDraw, ImageFont

P = Project(sys.argv[1] if len(sys.argv) > 1 else '.'); R = resolve_edit(P)
cw, ch = P.canvas
def font(n):
    for f in ('/System/Library/Fonts/Supplemental/Arial Bold.ttf', '/Library/Fonts/Arial Bold.ttf', 'C:/Windows/Fonts/arialbd.ttf'):
        if os.path.exists(f): return ImageFont.truetype(f, n)
    return ImageFont.load_default()
F1, F2 = font(22), font(17)
tw = 400; th = round(tw * ch / cw); per = 8
cache = {}
def frame(pid, fx, fy, z, b):
    im = cache.setdefault(pid, Image.open(P.p(P.image(pid)['file'])).convert('RGB'))
    x, y, s = place(fx, fy, z, im.width, im.height, b, cw, ch)
    x0, y0, x1, y1 = visible_rect(x, y, s, im.width, im.height, cw, ch)
    box = (x0 * im.width, y0 * im.height, x1 * im.width, y1 * im.height)
    return im.crop(tuple(round(v) for v in box)).resize((tw, th))
pages = [R['shots'][i:i + per] for i in range(0, len(R['shots']), per)]
for n, shots in enumerate(pages, 1):
    sheet = Image.new('RGB', (tw * 2 + 40, (th + 56) * len(shots) + 10), (24, 24, 26)); d = ImageDraw.Draw(sheet)
    for i, s in enumerate(shots):
        y = 10 + i * (th + 56)
        a = frame(s['base_pic'], *frame_at(s['keys'], s['t0']), s['bounds']); b = frame(s['base_pic'], *frame_at(s['keys'], s['t1']), s['bounds'])
        sheet.paste(a, (10, y + 46)); sheet.paste(b, (tw + 30, y + 46))
        d.text((10, y + 4), f"{s['id']}  {s.get('plate', s['pic'])}  {s['t0']:.2f}s +{s['t1'] - s['t0']:.2f}s  in: {' '.join(map(str, s['in']))}", font=F1, fill=(255, 214, 0))
        d.text((10, y + 27), s.get('note', '')[:90], font=F2, fill=(210, 210, 210))
    sheet.save(P.p(f'qa/storyboard-{n}.jpg'), quality=82)
print(f'{len(pages)} page(s): qa/storyboard-1.jpg ... (left = first frame, right = last frame of each shot)')
