---
name: capcut-story-film
description: Make a narrated story film in CapCut from an idea - Claude writes the storyboard (master prompt), records the narration with a free text-to-speech voice and generates reference and scene images through the Flow MCP, then builds a cinematic, fully editable CapCut project with only free CapCut features - every picture keyframed with motivated zooms and pans, cuts locked to the spoken words, dissolves/flashes/dips, living pictures whose lights switch on at a named word, titles built word by word, act cards, weather and film effects, word-timed captions, and a code-composed score with sound design. Also works from the user's own script, pictures and narration. Use when someone wants to make a short film or story video, animate a story, storyboard, AI-image collection or slideshow in CapCut, or "make my images feel like a movie".
---

# Story film in CapCut

You are the writer, director, editor, motion designer and composer. Input: an idea (or the user's own script, pictures
and narration). Output: a new CapCut desktop project that already plays like a film and stays editable, plus a
soundtrack preview. Free CapCut features only (keyframes, transparent overlay tracks, text, audio) and our own code-made
layers and sound. You never export from CapCut; the user does.

The bar is "a professionally directed short film, not a slideshow". Read `references/creative-direction.md` before
planning anything; it is the craft. `examples/storyboard-v2-sample.md` is a sample storyboard. Formats: `references/plan-formats.md`. CapCut details and
traps: `references/capcut-internals.md`. Free vs Pro: `references/free-vs-pro.md`. Voice and pictures:
`references/voice-and-images.md`. The user's own step-by-step guide: `references/checklist.md`.

**Paths.** `<SKILL>` is this skill's folder (the one holding this SKILL.md); run every script as
`python3 <SKILL>/scripts/...` (or `bash`, `node`) from the user's working folder. `<P>` is the film's folder: unless the
user names a place, `./story-films/<slug>` inside the folder Claude Code was opened in. Nothing depends on any other
kit or folder. Built and tested on Mac; it should also work on Windows, but that has not been tested yet
(`references/windows-notes.md`).

## What the user will be asked (say each one in plain words before it happens)

Before each of these, tell the user in one plain sentence what is about to happen and what they will see:
1. **Claude Code permission prompts** the first time you run a command, write a file or use a tool ("Claude Code will ask
   to let me run the setup check; allow it").
2. **The install list** from `setup.sh --install`: one yes covers the whole list. Homebrew may ask for their Mac password.
3. **Adding the Flow MCP** to Claude Code (a permission prompt), then a restart of Claude Code in the same folder.
4. **Google Flow sign-in**: they sign in to Google in the Flow Chrome window themselves (`npm run login` in the Flow MCP
   folder). You never type their password.
5. **macOS prompts**: Screen Recording and Accessibility (for checking CapCut on screen), and file-access prompts
   ("Claude wants to access files in your Movies folder").
6. **Voice**: a free test line first, their approval of the voice, then the full narration. Any credits: asked first.
7. **Credit quotes**: for the reference images, then for the scene batch. You never raise a spending cap on your own.
8. **"Close CapCut (or leave it on its home screen) before I write the project."**
9. **Full-screen control** when checking CapCut: some dialogs (Link media, Export) need it. "Let me take over" gives
   them their computer back.
10. **Trash moves** when cleaning up: files go to the Trash, never deleted permanently, and the Trash is never emptied.

## 0. Setup (once per machine)

`bash <SKILL>/scripts/setup.sh` (check only, changes nothing) prints a table: macOS, Homebrew, Node 22+, Python 3 with
Pillow and numpy, ffmpeg with the VideoToolbox HEVC encoder, whisper.cpp and its small.en model, CapCut (version vs the
tested 9.1: a different version is a warning, not a stop) and its projects folder, Chrome, git, the Flow MCP (registered
and connected), the Google AI Studio key (optional, never shown), `~/Movies` writable, free disk, and a tiny HyperFrames
test render. `--dry-run` shows what an install would do. To install: tell the user the list, get one yes in chat, then
`bash <SKILL>/scripts/setup.sh --install --yes` (it logs to `./capcut-story-film-setup.log`, never deletes, never uses
sudo; Homebrew's own installer asks for the Mac password). If it added the Flow MCP, the user must quit Claude Code,
reopen it in the same folder (MCP servers load when a session starts) and sign in to Flow once (`npm run login` in the
Flow MCP folder, default `~/flow-mcp`); then run the check again. CapCut itself, the Flow sign-in and the macOS privacy
switches are the user's to do.

## A. Settings and storyboard (new films)

1. Ask the settings in ONE grouped question (skip any the user already gave): length, story idea (or "suggest ideas"),
   genre, visual style, aspect ratio 16:9 or 9:16, male or female narrator, type of ending. Never guess the aspect ratio
   or the length.
2. Write the storyboard by following `references/master-prompt.md` exactly (sections A to H). For "suggest ideas":
   seven concepts, the best three ranked, then wait for the choice.
3. Save it as `<P>/storyboard.md` and **show it for review** (the story, the narration, the scene count). Nothing has
   been generated yet, so changes cost nothing. Revise until the user says go.
4. `python3 <SKILL>/scripts/ingest_storyboard.py <P>/storyboard.md <P>` -> the plan files (provisional timing), a draft
   `project.json`, `plan/generate.json` (pictures to make), `plan/narration.txt`, `plan/voice.json`. Then
   `python3 <SKILL>/scripts/lint_edit.py <P>`: 0 errors before going on. Read its warnings.

## B. Voice, reference images, scene images (references/voice-and-images.md)

In this order, each with its gate: (1) voice: free test line with the storyboard's one-line voice direction, approval,
full narration, attach with `new_project.py <P> --update --narration <file>`, report recorded vs planned length;
(2) reference images: say the count and Flow's quote, generate, **show them for review**; (3) scene images: **credit
quote and a yes**, then ALL scenes in one agent-mode request (`flow_agent_images` with `references` and
`scene_references`, the style suffix in every prompt; scenes may show several characters together), `collect_pictures.py`, `new_project.py --update
--images`, `contact.py` for the contact sheet and the missing list, regenerate only what is missing or broken.
Skip any step the user already has material for.

## 1. Brief (own-material films: one message, then decide the rest yourself)

Storyboard films already have all of this: go to step 4. Otherwise collect: the story/script (scenes with visuals and narration lines if they have them), the folder of pictures, the
narration audio, optional music they own, the title, 16:9 or 9:16, captions yes/no. Do not ask about anything you can
decide (camera, transitions, type, sound): that is your job. If pictures are missing for some scenes, say which and
offer to cover them (a crop or second angle of another picture, a generated image if they have an image tool, or a
type/effects beat) rather than stopping.

## 2. Project (own-material films; storyboard films already have one)

`python3 <SKILL>/scripts/new_project.py <P> --name "<Title>" --images <folder> --narration <file> [--music <file>] [--script <file>] [--vertical]`
Copies inputs (never edits originals), upscales small pictures 2x (Lanczos + light sharpening) for crisp zooms, writes
`project.json` (picture ids = file names; captions, letterbox 2:1 and vignette defaults under `look`). Unless the user
names a place, use `./story-films/<slug>` in the current working folder. Long picture file names? Add `--number` (ids i01, i02...
in file-name order) or rename copies to scene ids (s01, s02...) first: ids appear in every plan file.

## 3. Read the story like a director

Storyboard films: `plan/script.json` exists; write `plan/BEATS.md` from the storyboard's overview and synopsis.
Otherwise write `<P>/plan/script.json` (one entry per scene: narration, visual, camera, sound, act). Then write `<P>/plan/BEATS.md`
using the beat-sheet template in `references/creative-direction.md`: logline, acts and turning points, the emotional
curve, the KEY LINES (the 1-3 sentences the film is about), reveals that must wait, motifs, light/colour progression,
and the sound arc. Every later decision serves this page.

## 4. Timing from the voice

`python3 <SKILL>/scripts/transcribe.py <P>` -> `qa/words.json` (fix misheard names by hand, keep times), then
`python3 <SKILL>/scripts/align.py <P>` -> `plan/scenes.json`: each scene starts 0.35 s before its first spoken word; the last
holds 3 s. Shot lengths now come from the narration, not from the script's nominal durations.

## 5. Study the pictures

`python3 <SKILL>/scripts/contact.py <P>` -> `qa/pictures.jpg` + `qa/grid/<id>.jpg` (5 % grids). Look at every grid. Note per
picture: subject positions (faces, eyes, hands, the object the line names), light sources (for living plates), screen
direction, panels/diptychs/black bars (need `bounds`), source resolution (zoom limit), and which pictures can yield a
second shot (a crop, a detail insert, the other half of a diptych).

## 6. Direct the edit -> plan/edit.json

Storyboard films start from the ingest's draft (one shot per scene, recipes from the editor moves, focus at the frame
centre): set the focus points from the grids, split long scenes, add impacts, keep the storyboard's intent.
One entry per shot: picture, start, end, framing keys `[t, fx, fy, zoom]`, transition in, optional bounds/shake/still.
Use time references (`"s12"`, `"w:idea"`, `"w:stop@100+0.2"`) so cuts land on words. Follow the camera grammar, cutting
grammar and pacing rules in `references/creative-direction.md` (a few non-negotiables: every shot moves with a purpose
unless stillness IS the point; neighbouring shots differ in scale or direction; split scenes longer than ~6 s into two
shots or a two-stage move; rapid cuts on action verbs; dissolves for time/place, dips for act breaks, flashes for memory
or light, hard cuts inside tension).
Check: `python3 <SKILL>/scripts/lint_edit.py <P>` (0 errors; read every warning), then `python3 <SKILL>/scripts/storyboard.py <P>` and
LOOK at every first/last frame pair. Iterate until every pair is a frame you would choose.

## 7. Motion graphics -> plan/layers.json

Storyboard films start from the ingest's layers: finish each draft light plate (its `todo` says how), check the title
and key-phrase words, add what the story needs beyond the list.

Titles (word-synced to the narrator saying them), the key lines (stamped word by word), act cards, time/place labels,
an end card; environment effects that match the pictures (snow, blizzard, rain, dust, embers, sparks, film burn, old
film); and living plates (a picture with lights that blink, flash, pulse or switch on in sequence exactly on the words;
a patch can hide a baked-in light until its moment). Add `no_caption` ranges in edit.json wherever type already shows
the spoken words (never show the same words twice).
`python3 <SKILL>/scripts/layers.py <P>` then `bash <SKILL>/scripts/render_layers.sh <P>`; look at every `qa/layers/<id>.jpg`.

## 8. Sound -> plan/cue.mjs (or the user's music)

Storyboard films start from the ingest's draft cue sheet: compose it properly (motifs, chords, the sound arc).

Compose with the engine (`<SKILL>/scripts/score/engine.mjs`: pads, drones, tones, piano, arpeggios, hits, risers, ostinato,
heartbeat, whums; wind, rain, fire, vehicles, steps, doors, glass, brakes, birdsong, crowds...) following the sound arc
in BEATS.md: hits on key words, silence at the turning point, foley for on-screen actions. `node <SKILL>/scripts/score/run.mjs <P>`.
With their own music: `python3 <SKILL>/scripts/music_bed.py <P>` (fits, fades and ducks it) and keep the cue sheet for effects.
`python3 <SKILL>/scripts/levels.py <P>` -> levels table + `renders/soundtrack-preview.mp3`. Send the MP3 early for a vibe check.

## 9. Build and verify

CapCut closed or on its home screen. `python3 <SKILL>/scripts/build_capcut.py <P>` writes a NEW project (never overwrites; a
taken name gets "(2)") and copies media to `~/Movies/CapCut/<name> media/`. `python3 <SKILL>/scripts/verify_capcut.py <P>` must
say OK. Then in CapCut: open it from the home screen (no "Link media" dialog), scrub the title, every key line, each act
change, the climax and the end card; open Export and confirm the button reads **Export** (not "Join Pro to export") and
Audio is ticked. If you can control the screen (computer use), do these checks yourself and look at the frames;
otherwise give the user this exact checklist.

## 10. Deliver and revise

Tell the user, briefly: the project name, length, what is in it (shots, effects, type, sound), anything soft or
compromised (low-resolution pictures on tight zooms, missing scenes covered), and how to export (H.264 MP4, 1080p or 4K,
Audio ticked). Notes from the user: fix them in the plan files and rebuild; build_capcut.py always writes a NEW project name (never
reuse a name: CapCut caches media by path). Old builds can be moved to the Trash from CapCut's home screen by the user.

## Non-negotiables

- Free only. Never reference CapCut store effects, transitions, text templates, stickers, Pro fonts or AI features.
  Every clip at exactly 1x on the 30 fps grid (the builder enforces it) or CapCut turns on Pro-only Optical flow.
- Mobile-first: big type (titles 150-170 px at 1080p, labels 50 px+), captions max 34 characters per line, 2 lines.
- Words drive everything: cuts, type entrances, light cues, hits. No element enters on a nominal time if a word exists.
- One idea per on-screen line; elements enter one at a time; nothing duplicated (type vs captions).
- Never edit the user's original files. Never overwrite an existing CapCut project. Never spend money or credits without
  a quote and a yes. Never raise a credit cap on your own. Never ask for passwords or API keys in chat.
- Look before you claim: storyboard, layer sheets, verify output and (when possible) CapCut frames.
