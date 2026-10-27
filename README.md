# Guney Motion Kit

Make animated motion graphics for your videos by describing them to an AI assistant. The kit runs on
[HyperFrames](https://hyperframes.heygen.com) (HeyGen's open-source HTML-to-video engine) and adds everything we use for
YouTube videos: an animated background in any colour, big animated text, 3D-style elements and graphics that build
themselves on screen, Claude-style interface animations with zooms, sound effects, a frame-checking process, a house
style, and a way to put the graphics over your footage in DaVinci Resolve.

## Start here

You need the Claude desktop app with a paid Claude plan (Codex or Antigravity work too). You do not install anything
else yourself: Claude does it.

1. **Open the Claude desktop app** and click **Code**.
2. **Choose a folder** for it to work in. Your Desktop is fine.
3. **Paste this sentence** and press Enter:

   ```
   Download the Guney Motion Kit from https://github.com/GTAI-1/guney-motion-kit into this folder, then read its SETUP.md and set it up for me. Install anything that's missing.
   ```
4. **Click Allow** when Claude asks to run a command. It downloads the kit, installs Node.js and FFmpeg if you don't have
   them, and gets the render browser.
5. **Answer two questions:** your first name, and whether you want the Guney house style (say yes).
6. **Watch the starter video** it renders (10 seconds). Then ask for your first video:
   `Make me a 15-second intro for my video about <your topic>.`

Already have the folder? Open it in Claude Code (or Codex / Antigravity) and paste `Read SETUP.md and set this kit up for me.`

## What's inside

| Folder | What it is |
|---|---|
| `lib/` | The building blocks every new video gets: the frame clock (`stage.js`), the animated background (`backdrop.js`), big animated text (`text.js`), 3D-style cards (`cards.js`), graphics that build themselves (`build.js`) and the Claude-style window with zooms (`claudewin.js`). |
| `fonts/`, `sfx/` | Free fonts and a sound-effects set (keystrokes, clicks, pops, whooshes). |
| `templates/starter/` | The starter video every new project begins from. |
| `tools/` | Frame checking (`qa/`), the sound mixer (`audio/`) and the DaVinci Resolve overlay (`resolve/`). |
| `house-style/` | The house style: optional rules for how videos look, move, sound and get checked. |
| `docs/` | How a video gets made (`WORKFLOW.md`), what each building block does (`LIBRARY.md`), graphics over footage in Resolve (`RESOLVE.md`). |
| `.claude/skills/` | Skills the assistant loads for each job (mirrored to `.agents/skills/` for Codex). |

## Commands

```sh
npm run setup                   # check tools, install, choose your name and house style
npm run new-video -- my-video   # start a new project in video-projects/my-video
npm run check                   # quick health check (renders the starter for 1 second)
npm run sync                    # after editing AGENTS.md or a skill: refresh CLAUDE.md, GEMINI.md, .agents/skills
```

## Credits and licenses

HyperFrames (Apache-2.0, HeyGen), GSAP (GreenSock standard no-charge license), Puppeteer (Apache-2.0).
Fonts are free (SIL Open Font License and similar). Claude is a trademark of Anthropic; the kit's chat window is a look-alike drawn from scratch and
ships no Anthropic logos or fonts.

The kit itself is licensed under GPL-3.0 (see LICENSE).
