#!/usr/bin/env python3
"""Create a story-film project folder, or fill in a draft one.

  python3 scripts/new_project.py <project dir> --name "The Lighthouse Keeper" --images <folder> --narration <audio file>
                                 [--music <audio file>] [--script <text/markdown file>] [--vertical] [--pre 1.5]
  python3 scripts/new_project.py <project dir> --update [--images <folder>] [--narration <audio file>] [--music <file>]
      adds or replaces pictures / narration / music in an existing project (e.g. the draft ingest_storyboard.py wrote).
      Pictures replace the planned entries with the same id (s01.png -> s01); the plan files are kept.

Copies the inputs (never touches the originals): images into input/images/ (upscaled 2x with Lanczos + light sharpening
when narrower than 2000 px, so close-up zooms stay crisp), narration and music into input/. Writes project.json (picture
ids = file names), the HyperFrames scaffolding for the motion-graphics layers (assets/, hyperframes.json, meta.json),
and empty plan/ qa/ renders/ folders.
"""
import argparse, json, os, re, shutil, subprocess, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import SKILL, save, die

ap = argparse.ArgumentParser()
ap.add_argument('dir'); ap.add_argument('--name'); ap.add_argument('--images')
ap.add_argument('--narration'); ap.add_argument('--music'); ap.add_argument('--script')
ap.add_argument('--update', action='store_true', help='add/replace inputs of an existing (or draft) project')
ap.add_argument('--vertical', action='store_true'); ap.add_argument('--pre', type=float, default=1.5)
ap.add_argument('--no-upscale', action='store_true')
ap.add_argument('--number', action='store_true', help='name pictures i01, i02... in file-name order (mapping printed and kept in project.json)')
a = ap.parse_args()

root = os.path.abspath(a.dir)
pj = os.path.join(root, 'project.json')
old = json.load(open(pj)) if os.path.exists(pj) else None
if old and not a.update: die(f'{root} already has a project.json (use --update to add pictures or narration to it)')
if not old and not (a.name and a.images and a.narration): die('a new project needs --name, --images and --narration (or use --update on a draft project)')
for d in ('input/images', 'plan', 'qa', 'renders/layers', 'renders/audio', 'compositions', 'assets/fonts'):
    os.makedirs(os.path.join(root, d), exist_ok=True)

try:
    from PIL import Image
except ImportError:
    die('Pillow missing: python3 -m pip install --user pillow numpy')

EXT = ('.jpg', '.jpeg', '.png', '.webp')
images = {}
files = [f for f in sorted(os.listdir(a.images)) if f.lower().endswith(EXT) and not f.startswith('.')] if a.images else []
for n, f in enumerate(files, 1):
    pid = f'i{n:02d}' if a.number else (re.sub(r'[^a-z0-9]+', '-', os.path.splitext(f)[0].lower()).strip('-')[:48] or 'img')
    while pid in images: pid += '-b'
    src = os.path.join(a.images, f); dst = os.path.join(root, 'input/images', pid + '.jpg')
    im = Image.open(src).convert('RGB')
    w, h = im.size
    if not a.no_upscale and max(w, h) < 2000:
        im = im.resize((w * 2, h * 2), Image.LANCZOS)
        from PIL import ImageFilter
        im = im.filter(ImageFilter.UnsharpMask(radius=2, percent=55, threshold=2))
    im.save(dst, quality=93)
    images[pid] = {'file': f'input/images/{pid}.jpg', 'w': im.size[0], 'h': im.size[1], 'source': f, 'source_px': [w, h]}
if a.images and not images: die(f'no images in {a.images}')

def copy_audio(src, name):
    if not src: return None
    dst = os.path.join(root, 'input', name)
    subprocess.run(['ffmpeg', '-v', 'error', '-y', '-i', src, '-ar', '48000', dst], check=True)
    return f'input/{name}'

narr = copy_audio(a.narration, 'narration.wav') or (old or {}).get('narration')
dur = float(subprocess.run(['ffprobe', '-v', 'error', '-show_entries', 'format=duration', '-of', 'csv=p=0', os.path.join(root, narr)],
                           capture_output=True, text=True).stdout.strip()) if narr else (old or {}).get('narration_dur')
music = copy_audio(a.music, 'music.wav') or (old or {}).get('music')
if a.script: shutil.copy(a.script, os.path.join(root, 'input', 'script' + os.path.splitext(a.script)[1]))

cfg = {
    'name': a.name, 'fps': 30, 'canvas': [1080, 1920] if a.vertical else [1920, 1080], 'pre': a.pre,
    'narration': narr, 'narration_dur': round(dur, 3) if dur else None, 'music': music,
    'images': images,
    'look': {'captions': {'font': 'assets/fonts/Montserrat-SemiBold.otf', 'size': 9.5, 'y': -0.74, 'max_chars': 34},
             'letterbox': 2.0, 'vignette': True},
}
if old:                                                    # update: keep everything, replace what was given
    planned_dur = old.get('narration_dur') if old.get('narration') is None else None
    cfg = dict(old); cfg['images'] = {**old.get('images', {}), **images}; cfg['narration'] = narr; cfg['narration_dur'] = round(dur, 3) if dur else None
    cfg['music'] = music
    if a.name: cfg['name'] = a.name
    still = sorted(k for k, v in cfg['images'].items() if v.get('planned'))
    if narr and not still: cfg.pop('draft', None)
    if a.narration and planned_dur: print(f'  narration {dur:.2f} s recorded vs {planned_dur:.2f} s planned ({(dur - planned_dur) / planned_dur * 100:+.0f} %)')
    if still: print(f"  still planned (no picture yet): {', '.join(still)}")
    if not narr: print('  no narration yet')
save(pj, cfg)

# motion-graphics engine + fonts (HyperFrames compositions are rendered from this folder)
for f in ('lt.js', 'gsap.min.js'): shutil.copy(os.path.join(SKILL, 'assets', f), os.path.join(root, 'assets', f))
for f in os.listdir(os.path.join(SKILL, 'assets/fonts')): shutil.copy(os.path.join(SKILL, 'assets/fonts', f), os.path.join(root, 'assets/fonts', f))
shutil.copy(os.path.join(SKILL, 'assets/fonts.css'), os.path.join(root, 'assets/fonts.css'))
open(os.path.join(root, 'hyperframes.json'), 'w').write(json.dumps({'$schema': 'https://hyperframes.heygen.com/schema/hyperframes.json', 'paths': {'blocks': 'compositions', 'assets': 'assets'}}, indent=2))
cw, ch = cfg['canvas']
open(os.path.join(root, 'meta.json'), 'w').write(json.dumps({'id': os.path.basename(root), 'name': cfg['name'], 'width': cw, 'height': ch, 'fps': 30}, indent=2))
if old:
    print(f'updated {root}: {len(images)} picture(s){", narration" if a.narration else ""}{", music" if a.music else ""}')
    print('next:', 'python3 scripts/transcribe.py ' + root if a.narration else 'python3 scripts/contact.py ' + root); sys.exit(0)
print(f'project {root}\n  {len(images)} pictures, narration {dur:.2f} s{", music" if music else ""}')
if a.number:
    for k, v in images.items(): print(f'  {k} = {v["source"]}')
small = [k for k, v in images.items() if max(v['source_px']) < 1600]
if small: print(f'  note: {len(small)} pictures are under 1600 px at source; keep their zooms gentle (z <= 1.6)')
print('next: python3 scripts/transcribe.py', root)
