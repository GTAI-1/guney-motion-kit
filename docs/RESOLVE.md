# Graphics over your footage in DaVinci Resolve

1. Build the graphics without the animated background, on a transparent page (`html, body { background: transparent; }`),
   timed to your edit, clear of your face.
2. Render with transparency at your timeline's frame rate:
   `npx hyperframes render -o renders/overlay.mov --format mov --fps 30`
3. In Resolve: Preferences > System > General > External scripting using: **Local** (once). Open your timeline, then from
   the project folder: `python3 ../../tools/resolve/place.py renders/overlay.mov --at 00:00:10:00`
   It adds a new video track above your footage and places the graphics there. Your own clips are never changed.
4. Watch it in Resolve and export as usual.
