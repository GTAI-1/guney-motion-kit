---
name: resolve-overlay
description: Put the motion graphics directly over the person's footage in DaVinci Resolve - render the graphics with a transparent background and place them on a new track above their edit. Use when they edit in Resolve and want the graphics on their timeline.
---

# Graphics over footage in DaVinci Resolve

1. Build the graphics without the animated background (no `BG.make`), on a transparent page:
   `html, body { background: transparent; }`. Keep everything clear of the speaker's face.
2. Time the graphics to their edit: get word timings of their voice and use their timeline's clock.
3. Render with transparency: `npx hyperframes render -o renders/overlay.mov --format mov --fps 30` (match their timeline's frame
   rate). Check a few frames before placing it.
4. With Resolve open on their timeline (Preferences > System > General > External scripting using: Local):
   `python3 ../../tools/resolve/place.py renders/overlay.mov --at 00:00:10:00` puts it on a new video track above their
   footage, starting at that timecode. Their own clips are never changed or exported.
5. They review it in Resolve and export themselves.
