# The building blocks (`lib/`, copied into each project's `assets/`)

Load what a scene needs in its `<head>` (paths relative to the project folder), in this order: `gsap.min.js`, `stage.js`,
`kit-config.js`, then the pieces below; styles: `fonts.css`. The starter (`templates/starter/index.html`) uses all of them.

## `stage.js`: the frame clock (`window.STAGE`)
- `STAGE.driver(duration, frame)` returns the paused GSAP timeline HyperFrames plays; `frame(t)` is called every frame and
  must depend only on `t`. Register it: `window.__timelines['<id>'] = tl`. Add GSAP tweens to the same `tl` freely.
- Helpers: `seg(t, a, b)` (0..1 progress), `lerp`, `clamp`, easings (`E.outExpo`, `E.inOutCubic`, `E.outCubic`, ...),
  `spring`, `impact`, seeded random `mulberry32(seed)` and `hash`.

## `backdrop.js`: the animated background (`window.BG`)
- `bg = BG.make(el, { color, motes, seed, grid })`, then `BG.live(tl, bg, duration)`; `bg.setColor(hex)` any time.

## `text.js`: large animated text (`window.TX`)
- `TX.typeOn(tl, el, at, perLetter)`, `TX.slam(tl, el, at)`, `TX.words(tl, el, at, gap)`. Each returns its end time.

## `cards.js`: 3D-style elements (`window.CARD`)
- `c = CARD.make(parent, { x, y, w, h, depth, color, html })`, `CARD.build(tl, c, at, 'below'|'left'|'right'|'above')`,
  `CARD.tilt(tl, c, duration)`.

## `build.js`: graphics that build themselves (`window.BUILD`)
- `f = BUILD.frame(parent, { x, y, w, h, r, color })` + `BUILD.drawFrame(tl, f, at, dur)`: an outline that draws on.
- `BUILD.pieces(tl, elements, at, step)`: the parts arrive one at a time, each from its own direction.

## `claudewin.js`: Claude-style window (`window.CW`)
- `W = CW.make(parent, { title, x, y, w, h })`; `W.type`, `W.send`, `W.reply`, `W.zoom`; `CW.live(tl, W, duration)`.

## Sound
- `sfx/` (copied to `assets/audio/sfx/`): keystrokes, click, pop, thunk, rise, swish, whoosh. Mix a cue sheet with
  `node ../../tools/audio/sfxmix.mjs events.json <length> out.wav raw`.
