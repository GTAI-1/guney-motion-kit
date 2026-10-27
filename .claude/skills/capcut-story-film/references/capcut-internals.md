# CapCut internals (desktop 9.x, verified on macOS)

## Where projects live
- macOS: `~/Movies/CapCut/User Data/Projects/com.lveditor.draft/<project name>/`
- Windows: `%LOCALAPPDATA%\CapCut\User Data\Projects\com.lveditor.draft\<project name>\` (format is the same; untested)
- Override with `CAPCUT_DRAFTS=<folder>`. The home screen lists projects from `root_meta_info.json` in that folder.

A project folder holds `draft_info.json` (the timeline: plain JSON), a copy under `Timelines/<timeline id>/draft_info.json`,
`template-2.tmp` copies of both, `draft_meta_info.json` (name, id, paths, media list), `Timelines/project.json`, and a few
small config files. `scripts/capcut.py` writes all of them from `templates/skeleton/` (an empty 9.x project) and
`templates/cc-templates.json` (segment/material shapes), registers the project in `root_meta_info.json` (a backup of the
old registry goes to `<P>/qa/capcut-backups/`), and never touches an existing project.

## Timeline JSON essentials
- Times in microseconds. Tracks are drawn in list order (later = on top); `render_index` follows the same order.
- Video track `flag: 0` = main track (must start at 0 and be contiguous), `flag: 2` = overlay tracks.
- Segment: `target_timerange {start, duration}`, `source_timerange` (null for text), `speed`, `clip {scale, transform {x, y}, alpha}`,
  `uniform_scale`, `common_keyframes`, `extra_material_refs` (speeds, canvases, placeholders, sound mappings, colours...).
- Material types: `photo` (duration 10800000000), `video` (real duration), `extract_music` (audio), `text` (content JSON
  with styles: fill colour, size, font path, shadows).
- Keyframes: `common_keyframes: [{property_type, keyframe_list: [{time_offset (us from segment start), values: [v],
  curveType: 0}]}]`; properties `KFTypeScaleX` (uniform scale when `uniform_scale.on`), `KFTypePositionX`, `KFTypePositionY`,
  `KFTypeAlpha`, `KFTypeRotation`. CapCut interpolates linearly and keeps these keys through its own re-save.

## Units and framing
- Scale 1 = the picture fitted inside the canvas (a 16:9 picture fills a 16:9 canvas).
- Position in half-canvas units: x = 1 moves the centre to the right edge; **y = 1 moves it UP** to the top edge.
- To put picture point (fx, fy) at the centre at zoom z: x = (0.5 - fx) * Wfit * z / (W/2), y = (fy - 0.5) * Hfit * z / (H/2).
- Coverage: the picture covers the frame while |x| <= (z*Wfit - W)/W and |y| <= (z*Hfit - H)/H; `common.place()` clamps every
  key to that, and `verify_capcut.py` re-checks the written project.

## Traps (each one broke a real project)
1. **Optical flow = Pro.** If any clip's source length differs from its timeline length (even by a fraction of a frame),
   CapCut reads it as a 0.9-1.05x speed change and turns on Optical flow for export, a Pro feature: the export button
   becomes "Join Pro to export". Fix: every segment on the 30 fps grid, source length == timeline length, speed 1.0
   (the writer enforces it). Turning the toggle off in the export panel also works, but fix the project instead.
2. **Sandbox.** CapCut on macOS cannot read files on the Desktop or in Downloads ("File not accessible", Link media
   dialog). Keep all media under `~/Movies` (the builder copies to `~/Movies/CapCut/<name> media/`).
3. **Premultiplied HEVC alpha.** CapCut composites HEVC-with-alpha as premultiplied. Encode overlays with
   `-vf format=rgba,premultiply=inplace=1,format=bgra -c:v hevc_videotoolbox -alpha_quality 0.9 -tag:v hvc1`, or soft glows
   (snow bokeh, fog, light blooms) turn into solid white discs. ProRes 4444 also works (straight alpha) but is huge.
4. **Media cache by path.** CapCut remembers a project's media list by its folder path. Deleting a project and writing a
   new one under the same name brings the old files back as "missing". Never reuse a name (the writer adds " (2)").
   If it happens, put the old files back at their old paths, or cancel the dialog (it is drawn by another process:
   computer-use needs full-screen control to click Cancel).
5. **Write while closed.** CapCut keeps the open project in memory and saves it over the files when it closes. Build
   only while CapCut is quit or on its home screen; reopen the project afterwards.
6. **Export panel defaults are sticky per user.** One account had Audio UNTICKED (silent exports) and HEVC (Alpha) MOV
   selected. Always check: Audio ticked, H.264 MP4 for YouTube, the button reads "Export".
7. **Text.** `font_path` may point at any readable font file (the builder copies Montserrat SemiBold next to the media).
   Size 12 is about 52 px per character on a 1080p canvas: size 9.5 with 34 characters fits with margins. Keep the
   shadow tight (diffuse 0.12, alpha 0.6) or it smears into a dark band on bright frames.
8. **Store resources.** Effects, transitions, filters, stickers and text templates from CapCut's library are referenced by
   resource ids that must be downloaded per account and are often Pro. This skill never uses them: looks come from our
   own layers, solids and keyframes, which are always free.

## Checking inside CapCut with computer use (optional)
- Background control works: `app_screenshot` the editor, click the timeline ruler (y about 439 in a 1280x720 window) to
  seek, `app_zoom` the player to read the frame. The playhead snaps to cut points, so aim slightly inside a shot.
- Dialogs (Link media, Export) belong to another process: background clicks do not reach them; request full-screen
  control briefly, click, release.
- Never export or change the user's account settings without asking.
