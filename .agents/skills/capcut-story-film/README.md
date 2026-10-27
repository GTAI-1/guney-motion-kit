# capcut-story-film

A Claude Code skill that makes a narrated story film in CapCut. From an idea, Claude writes the storyboard, records the
narration with a free text-to-speech voice, generates the reference and scene pictures in Google Flow (through the Flow
MCP), and builds a cinematic, fully editable CapCut project using only free CapCut features. It also works from your own
script, pictures and narration. Claude directs it like a short film: every picture gets
motivated zooms and pans timed to your words, cuts and transitions follow the story, lights inside the pictures blink
and flash on cue, titles and key lines land on the spoken words, weather and film effects match each scene, captions are
timed to your voice, and an original score with sound design is composed for it. You open the project in CapCut, watch,
tweak anything you like, and export.

Built and tested on Mac. It should also work on Windows, but that has not been tested yet.

**Step by step for first-timers: `references/checklist.md`.**

## What you need
- A Mac with CapCut desktop (free) opened at least once, Google Chrome, Claude Code
- A Google account for Google Flow (free daily credits; still pictures have cost 0 credits so far)
- Optional: a free Google AI Studio key for the best narration voices (pasted into Flow Studio, never into a chat)
- The tools the check installs for you after one yes: Homebrew, Node 22+, Python 3 with Pillow and numpy, ffmpeg,
  whisper.cpp and its model, the Flow MCP. Check: `bash scripts/setup.sh`; install: `bash scripts/setup.sh --install`.

## Install
Copy this whole folder into `~/.claude/skills/` (for all your projects) or into a project's `.claude/skills/`. It works
from any folder, including an empty one.

## Use
New film from an idea:
> Use the capcut-story-film skill to make a new film.

Claude asks your settings (length, genre, style, 16:9 or 9:16, narrator, ending), writes the storyboard for your review,
records a test line of the voice, then the narration, shows you the reference pictures, quotes the credits for the scene
pictures, and builds the film. The scene pictures are made all at once in a single Flow batch with your reference
characters, places and objects attached, so faces and places stay the same in every scene, and a scene can show several
characters together. Long narrations are recorded in parts and joined, so you never hear the seams. From your own material:
> Use the capcut-story-film skill. My script is in story.md, the pictures are in ~/Pictures/my-story, the narration is
> ~/Desktop/narration.wav. Title: "The Lighthouse". 16:9 with captions.

Claude will plan the film (beat sheet, shot list, storyboard), build the motion graphics and the sound, send you a
soundtrack preview, write the CapCut project, check it, and tell you what to look at. Changes ("make the ending
longer", "less zoom on scene 4", "use my own music") are applied to the plan and rebuilt as a new project.

## What is inside
- `SKILL.md` the workflow Claude follows; `references/` the master prompt, the checklist, voice and pictures, the craft
  (creative direction), formats, CapCut internals, free vs Pro, Windows notes, and a full case study;
  `examples/` a sample storyboard and the real plan files of a finished film
- `skill.config.json` where the Flow MCP is downloaded from, the tested CapCut version, the HyperFrames version
- `scripts/` setup (doctor and installer), storyboard ingest, picture collection, intake, word timing, scene alignment, shot linting and storyboards, motion-graphics layers, sound engine,
  CapCut project writer and verifier
- `assets/` the motion-graphics engine and open-licence fonts; `templates/` an empty CapCut project skeleton

## Notes
- Your original files are never modified; a new CapCut project is created each build (existing ones are never overwritten).
- Only use pictures, narration and music you have the rights to.
- Fonts: SIL Open Font License (see `assets/fonts/LICENSES.md`). GSAP: free standard license (gsap.com).
