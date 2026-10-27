---
name: animated-background
description: Put the kit's animated background behind any scene, in any colour - a dark tinted ground, a glowing horizon, a grid floor sliding toward the camera and drifting motes. Use for every scene unless the person asks for a plain or transparent background.
---

# Animated background

- Load `assets/backdrop.js` after `assets/stage.js`. Give the scene a background layer and a content layer above it:
  `<div id="bg" class="clip" ...></div>` then `<div id="fg" class="clip" ...></div>` (higher `data-track-index`, `z-index`).
- `const bg = BG.make(document.getElementById('bg'), { color: '#E8743C', motes: 24, seed: 7, grid: true })`, then
  `BG.live(tl, bg, DURATION)` on the scene's timeline. It moves for the whole clip.
- The colour is the person's choice: ask once per video and use it everywhere (cards, rims, the accent word).
  `bg.setColor('#4FA3FF')` changes it mid-scene.
- For a graphics overlay on someone's footage (DaVinci Resolve), leave the background out: see the `resolve-overlay` skill.
