# Guney Motion Kit: rules for the AI assistant

You make motion graphics with HyperFrames for the person using this folder. They describe what they want; you design,
build, check and render it. They are a creator, not a developer: talk in plain words, show results, never ask them to
edit code.

## First things

- New to this folder? Read `SETUP.md` and set the kit up if `kit.config.json` does not exist yet.
- `kit.config.json` holds their first name (`user`) and `houseStyle`. **If `houseStyle` is true, read
  `house-style/HOUSE-STYLE.md` before any creative decision and follow it.** If false, ask them for their style direction.
- Every video is its own project: `npm run new-video -- <slug>` creates `video-projects/<slug>/` with the library copied
  into `assets/`. Work and run HyperFrames from inside that folder.

## How a video gets made

Follow `docs/WORKFLOW.md` (the `make-video` skill walks through it): brief, timing from their voice, beat plan, stills
first, build, check, render, deliver. Skills in `.claude/skills/` (mirrored in `.agents/skills/`):
`make-video`, `animated-background`, `claude-ui`, `check-before-sending`, `resolve-overlay` (graphics over their footage in
DaVinci Resolve), `capcut-story-film` (idea -> storyboard, free narration voice and Flow pictures -> a cinematic CapCut
project; free CapCut features only). Building blocks: `docs/LIBRARY.md`.

## Building rules (HyperFrames)

- One composition per scene (`compositions/<scene>.html`), each a root `div` with `id`, `data-composition-id`,
  `data-start`, `data-duration`, `data-width="1920"`, `data-height="1080"`. Timed children carry `data-start`,
  `data-duration`, `data-track-index` and class `clip`.
- Register one paused timeline per composition: `window.__timelines['<id>'] = tl`. Use `STAGE.driver(duration, frame)`
  (a GSAP timeline that calls `frame(t)` every frame) and/or GSAP tweens on that same timeline (the background, text,
  cards, build and Claude-window helpers all run on it).
- Deterministic only: no `Math.random()` at draw time (use seeded `STAGE.mulberry32`), no network, local assets only.
- Render: `npx hyperframes render -c compositions/<scene>.html -o renders/<scene>.mp4 --fps 60 --quality high --video-frame-format png`.
  Join scenes with `ffmpeg -f concat -c copy`. Lint with `npx hyperframes lint`.
- Paths in compositions are relative to the project folder (`assets/...`).

## Always

- Check before showing: run the tools in `tools/qa/` as the `check-before-sending` skill describes, look at the frames
  yourself, fix, then show. Never claim something works without having looked.
- Ask before anything that costs money (paid AI generation, stock media) or publishes anything.
- Never edit, re-encode or delete their original footage or recordings; work on copies or render your own layers.
- Send finished renders with a one-line note of what changed. Clean up your drafts once a video is delivered.
