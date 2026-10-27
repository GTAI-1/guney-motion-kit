---
name: check-before-sending
description: Check a scene or render before showing it - stills at the key moments, a contact sheet of the render, and a scan for a blank first frame, black frames and one-frame pops. Use before sending any render or still to the person.
---

# Check before sending

Run from the project folder.

```sh
node ../../tools/qa/snap.mjs compositions/<scene>.html <id> qa/shots 0.5 2 4 6      # stills at chosen times
python3 ../../tools/qa/pngstrip.py qa/shots/*.png                                   # (stills look right in a browser)
python3 ../../tools/qa/scan.py <name>                                               # renders/<name>.mp4: black frames, pops
node ../../tools/qa/evalat.mjs compositions/<scene>.html <id> "<js expression>" 1 2   # inspect anything at a time
ffmpeg -i renders/<name>.mp4 -vf "select='not(mod(n\,30))',scale=480:-1,tile=4x3" -frames:v 1 qa/sheet.jpg   # contact sheet
```

Then look at the stills and the sheet yourself:
- the first and last frame, and every change of layout;
- every text readable on a phone and fully inside the frame; nothing over the speaker's face;
- every element builds on screen (nothing pops in), nothing waits empty, the background is moving.

Fix what you see, render again, check again. Only then show it, with a one-line note of what it is.
