---
name: claude-ui
description: Show a chat window in the style of the Claude desktop app - title bar, conversation, composer - with the person's words typed in, replies arriving line by line and zooms onto the part being explained. Use whenever a video shows Claude or a chat interface.
---

# Claude-style window

- Load `assets/claudewin.js` (after `assets/stage.js`). `const W = CW.make(layer, { title, x, y, w, h })`.
- Script it on the scene's clock: `W.type(at, 'their prompt', 0.03)` (letter by letter in the composer), `W.send(at)`
  (it becomes their bubble), `W.reply(at, ['line one', 'line two'], 0.35)`, then `CW.live(tl, W, DURATION)`.
- Zoom onto what is being explained: `W.zoom(at, 0.5, W.lines[0], 1.7)`; `W.zoom(at, 0.5, null)` zooms back out. The zoom
  never goes so far that the part is cut.
- Type their words as they say them, when there is a voiceover. Show the whole window first, then zoom in.
- Let the outline draw on (`BUILD.frame` + `BUILD.drawFrame`) and the window rise in, so it builds on screen.
