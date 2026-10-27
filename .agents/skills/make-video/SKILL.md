---
name: make-video
description: Make a motion-graphics video or clip with this kit, end to end - brief, timing from the voice, beat plan, stills, build on the animated background, check, render, finish. Use when the person asks for a video, intro, reel, ad, explainer, or motion graphics for their footage.
---

# Make a video

1. Read `kit.config.json`. If `houseStyle` is true, read `house-style/HOUSE-STYLE.md` now and follow it throughout.
2. **Brief** in one message: topic, audience, length, where it goes, what they have (script, voiceover, talking-head edit,
   screen recordings, reference video, brand colours) and the background colour. Do not ask about things you can decide.
3. `npm run new-video -- <slug>` and work inside `video-projects/<slug>/`.
4. **Timing:** with a voiceover, get word timings (any word-level transcript) into `assets/vo-times.js` as
   `window.VO = { <section>: { base, words: [{ w, s, e }] } }`. Every visual lands on its word.
5. **Beat plan** in `plan/BEATS.md`: per beat the words, what is shown (what each key word names, as an animated object),
   layout, key phrase (1 to 3 words), sounds. Neighbouring beats must look different. Show it to them.
6. **Stills first** for any new direction (2 to 4 frames with `node ../../tools/qa/snap.mjs`), then build.
7. **Build** each scene in `compositions/` on the animated background (`animated-background` skill): big text with
   `assets/text.js`, 3D-style cards with `assets/cards.js`, build-on outlines and pieces with `assets/build.js`, Claude windows
   with `claude-ui`; motion with `STAGE.driver` + GSAP tweens on the same timeline (`docs/LIBRARY.md`). Every element enters
   on its own, filled in.
8. **Check** (`check-before-sending`), render (`--fps 60 --quality high --video-frame-format png`), join sections, mix
   sound (`tools/audio/sfxmix.mjs`), send the review render with a one-line summary.
9. Apply notes, re-check, re-send. When approved, deliver the MP4, or put the graphics over their footage in DaVinci Resolve (`resolve-overlay`). Clean up drafts after.
