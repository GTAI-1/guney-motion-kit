"""Write CapCut desktop projects from code (verified on CapCut 9.1 for macOS; format notes: references/capcut-internals.md).

    from capcut import Draft
    d = Draft('My Film', canvas=(1920, 1080))
    v = d.track('video'); d.media(v, '/path/pic.jpg', 0, 5, 2752, 1536, photo=True, keys={'scale': [(0, 1.3), (5, 1.05)]})
    folder = d.save()

Rules this writer enforces (each one cost a broken project once):
  * every segment sits on the 30 fps frame grid with source length == timeline length and speed 1.0; otherwise CapCut
    reads the clip as 0.9-1.05x speed and switches on Optical flow, a Pro export feature ("Join Pro to export")
  * a project is never overwritten: an existing name gets " (2)", " (3)"... (CapCut also caches media lists by path)
  * media paths must be readable by CapCut (macOS sandbox: keep them under ~/Movies); build_capcut.py copies them there
Keyframes: common_keyframes [{property_type: KFTypeScaleX | KFTypePositionX | KFTypePositionY | KFTypeAlpha | KFTypeRotation,
keyframe_list: [{time_offset: us from the segment start, values: [v], curveType: 0}]}]; position in half-canvas units.
"""
import json, uuid, copy, os, shutil, time
from common import SKILL, capcut_root

T = json.load(open(os.path.join(SKILL, 'templates/cc-templates.json')))
SKEL = os.path.join(SKILL, 'templates/skeleton')
U = lambda: str(uuid.uuid4()).upper()
FPS = 30
fr = lambda s: int(round(s * FPS))
fus = lambda f: int(round(f * 1_000_000 / FPS))
us = lambda s: int(round(s * 1_000_000))


def _refs(owner, materials, keep=None):
    ids = []
    for kind, obj in T[owner]:
        if keep is not None and kind not in keep: continue
        o = copy.deepcopy(obj); o['id'] = U()
        if kind == 'material_animations': o['animations'] = []
        if kind == 'audio_fades': o['fade_in_duration'] = 0; o['fade_out_duration'] = 0
        if kind == 'speeds': o.update(speed=1.0, mode=0, curve_speed=None)
        materials.setdefault(kind, []).append(o); ids.append(o['id'])
    return ids


def _kf(prop, pts):
    ctl = lambda: {'id': U(), 'x': 0.0, 'y': 0.0}
    return {'id': U(), 'material_id': '', 'property_type': prop,
            'keyframe_list': [{'curveType': 0, 'graph': None, 'id': U(), 'left_control': ctl(), 'right_control': ctl(),
                               'string_value': '', 'time_offset': us(t), 'values': [float(v)]} for t, v in pts]}


KF = {'scale': 'KFTypeScaleX', 'x': 'KFTypePositionX', 'y': 'KFTypePositionY', 'alpha': 'KFTypeAlpha', 'rot': 'KFTypeRotation'}


class Draft:
    def __init__(self, name, canvas=(1920, 1080), fps=30.0):
        self.name = name.strip()
        self.d = json.load(open(os.path.join(SKEL, 'draft_info.base.json'))); self.d['fps'] = fps; self.d['name'] = ''
        self.d['canvas_config'] = {'ratio': 'original', 'width': canvas[0], 'height': canvas[1], 'background': None}
        self.m = self.d['materials']
        for k, v in self.m.items():
            if isinstance(v, list): v.clear()
        self.tracks = []

    def track(self, kind, overlay=False):
        t = copy.deepcopy(T['track']); t.update(id=U(), type=kind, flag=2 if (overlay and kind == 'video') else 0, segments=[])
        self.tracks.append(t); return t

    def _seg(self, track, tmpl, mat_id, refs, start, dur, src=None, maxsrc=None):
        a, b = fr(start), fr(start + dur)
        if src is not None and maxsrc is not None: b = min(b, a + int(maxsrc * FPS + 1e-6) - fr(src))
        if b <= a: b = a + 1
        d = fus(b) - fus(a)
        s = copy.deepcopy(T[tmpl]); s.update(id=U(), material_id=mat_id, extra_material_refs=refs, common_keyframes=[], speed=1.0,
                                            keyframe_refs=[], target_timerange={'start': fus(a), 'duration': d})
        s['source_timerange'] = None if src is None else {'start': fus(fr(src)), 'duration': d}
        track['segments'].append(s); return s

    def _visual(self, s, scale=1.0, x=0.0, y=0.0, alpha=1.0, keys=None):
        s['clip'] = {'scale': {'x': scale, 'y': scale}, 'rotation': 0.0, 'transform': {'x': x, 'y': y},
                     'flip': {'vertical': False, 'horizontal': False}, 'alpha': alpha}
        s['uniform_scale'] = {'on': True, 'value': 1.0}
        dur = s['target_timerange']['duration'] / 1e6
        for prop, pts in (keys or {}).items():
            pts = [(min(max(0.0, t), dur), v) for t, v in pts]
            s['common_keyframes'].append(_kf(KF[prop], pts))
        return s

    def media(self, track, path, start, dur, w, h, photo=False, src=0.0, length=None, volume=0.0, **vis):
        mat = copy.deepcopy(T['video_mat'])
        mat.update(id=U(), type='photo' if photo else 'video', path=path, width=w, height=h, has_audio=False,
                   material_name=os.path.basename(path), local_material_id=str(uuid.uuid4()),
                   duration=10_800_000_000 if photo else us(length))
        self.m['videos'].append(mat)
        s = self._seg(track, 'video_seg', mat['id'], _refs('video_refs', self.m), start, dur, src, None if photo else length)
        s['volume'] = volume
        return self._visual(s, **vis)

    def text(self, track, txt, start, dur, size=9.5, font='', color=(1, 1, 1), shadow=True, align=1, spacing=0.0, **vis):
        mat = copy.deepcopy(T['text_mat'])
        hexc = '#%02x%02x%02x' % tuple(round(c * 255) for c in color)
        style = {'fill': {'content': {'solid': {'color': list(color)}, 'render_type': 'solid'}}, 'range': [0, len(txt)],
                 'useLetterColor': True, 'size': size, 'font': {'path': font, 'id': ''}}
        if shadow:
            style['shadows'] = [{'content': {'solid': {'color': [0, 0, 0]}, 'render_type': 'solid'}, 'diffuse': 0.12, 'alpha': 0.6, 'distance': 2.0, 'angle': -45.0}]
        mat.update(id=U(), content=json.dumps({'styles': [style], 'text': txt}), font_path=font, font_resource_id='', font_id='', font_size=size,
                   text_color=hexc, has_shadow=shadow, shadow_color='#000000' if shadow else '', shadow_alpha=0.6, shadow_smoothing=0.12,
                   shadow_distance=2.0, alignment=align, letter_spacing=spacing, base_content='', check_flag=7)
        self.m['texts'].append(mat)
        s = self._seg(track, 'text_seg', mat['id'], _refs('text_refs', self.m, keep={'material_animations'}), start, dur)
        return self._visual(s, **vis)

    def audio(self, track, path, start, dur, length, src=0.0, volume=1.0):
        mat = copy.deepcopy(T['audio_mat'])
        mat.update(id=U(), path=path, name=os.path.basename(path), duration=us(length), music_id=str(uuid.uuid4()), local_material_id=str(uuid.uuid4()), wave_points=[])
        self.m['audios'].append(mat)
        s = self._seg(track, 'audio_seg', mat['id'], _refs('audio_refs', self.m, keep={'speeds', 'placeholder_infos', 'audio_fades', 'sound_channel_mappings', 'vocal_separations'}),
                      start, dur, src, length)
        s['volume'] = volume; s['clip'] = None; s['uniform_scale'] = None
        return s

    # ------------------------------------------------------------------ write the project folder
    def save(self, backup_dir=None):
        ri = {'video': 0, 'text': 14000, 'audio': 0}
        self.tracks = [t for t in self.tracks if t['segments']]
        for n, t in enumerate(self.tracks):
            for s in t['segments']:
                s['track_render_index'] = n; s['render_index'] = (ri[t['type']] + n) if t['type'] != 'audio' else 0
                assert s['speed'] == 1.0 and (s['source_timerange'] is None or s['source_timerange']['duration'] == s['target_timerange']['duration'])
        assert all(m['speed'] == 1.0 for m in self.m.get('speeds', []))
        self.d['tracks'] = self.tracks
        end = max(s['target_timerange']['start'] + s['target_timerange']['duration'] for t in self.tracks for s in t['segments'])
        self.d['duration'] = end
        root = capcut_root(); rp = os.path.join(root, 'root_meta_info.json')
        r = json.load(open(rp)) if os.path.exists(rp) else {'all_draft_store': [], 'draft_ids': 0, 'root_path': root}
        names = {x.get('draft_name') for x in r.get('all_draft_store', [])}
        name, k = self.name, 2
        while name in names or os.path.exists(os.path.join(root, name)): name = f'{self.name} ({k})'; k += 1
        self.final_name = name
        folder = os.path.join(root, name); now = int(time.time() * 1_000_000)
        tl, pid, did = U(), U(), U()
        for sub in ('adjust_mask', 'common_attachment', 'matting', 'qr_upload', 'smart_crop', 'subdraft', 'Resources/audioAlg', 'Resources/videoAlg', f'Timelines/{tl}'):
            os.makedirs(os.path.join(folder, sub), exist_ok=True)
        for f in ('draft_biz_config.json', 'draft_agency_config.json', 'key_value.json'):
            shutil.copy(os.path.join(SKEL, f), os.path.join(folder, f))
        for f in ('draft.extra', 'template.tmp'):
            shutil.copy(os.path.join(SKEL, 'Timelines/TIMELINE', f), os.path.join(folder, f'Timelines/{tl}', f))
        open(os.path.join(folder, 'timeline_layout.json'), 'w').write(open(os.path.join(SKEL, 'timeline_layout.json')).read().replace('TIMELINE_ID', tl))
        pj = json.loads(open(os.path.join(SKEL, 'Timelines/project.json')).read().replace('TIMELINE_ID', tl))
        pj['id'] = pid; pj['create_time'] = pj['update_time'] = now
        for x in pj['timelines']: x['create_time'] = x['update_time'] = now
        for f in ('Timelines/project.json', 'Timelines/project.json.bak'): json.dump(pj, open(os.path.join(folder, f), 'w'))
        open(os.path.join(folder, 'draft_settings'), 'w').write(f'[General]\ndraft_create_time={now // 1_000_000}\ndraft_last_edit_time={now // 1_000_000}\nreal_edit_keys=1\nreal_edit_seconds=0\n')
        self.d['id'] = tl
        body = json.dumps(self.d, ensure_ascii=False)
        for f in ('draft_info.json', 'template-2.tmp', f'Timelines/{tl}/draft_info.json', f'Timelines/{tl}/template-2.tmp'):
            open(os.path.join(folder, f), 'w').write(body)
        meta = json.load(open(os.path.join(SKEL, 'draft_meta_info.json')))
        meta.update(draft_id=did, draft_name=name, draft_fold_path=folder, draft_root_path=root, tm_duration=end, tm_draft_create=now, tm_draft_modified=now)
        json.dump(meta, open(os.path.join(folder, 'draft_meta_info.json'), 'w'), ensure_ascii=False)
        if backup_dir and os.path.exists(rp):
            os.makedirs(backup_dir, exist_ok=True); shutil.copy(rp, os.path.join(backup_dir, f'root_meta_info.before-{int(time.time())}.json'))
        e = json.load(open(os.path.join(SKEL, 'root_entry.json')))
        e.update(draft_id=did, draft_name=name, draft_fold_path=folder, draft_root_path=root, draft_json_file=os.path.join(folder, 'draft_info.json'),
                 draft_cover=os.path.join(folder, 'draft_cover.jpg'), tm_draft_create=now, tm_draft_modified=now, tm_duration=end)
        r.setdefault('all_draft_store', []).insert(0, e)
        if isinstance(r.get('draft_ids'), int): r['draft_ids'] += 1
        r.setdefault('root_path', root)
        json.dump(r, open(rp, 'w'), ensure_ascii=False)
        return folder
