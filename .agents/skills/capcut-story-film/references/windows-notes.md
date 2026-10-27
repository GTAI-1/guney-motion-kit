# Windows notes (phase 2: researched, NOT tested)

The skill was built and tested on a Mac. Nothing in this file has been run on Windows. It collects what is known, what is
unknown, and the safest code that could be written without a Windows machine. Treat it as the README for the Windows
port: whoever tests it first should fill in every "unknown" below and remove the word "untested" only where it passed.

## What already works the same (by design, still untested on Windows)

- The planning scripts are plain Python and use `os.path` (ingest, transcribe, align, lint, storyboard, contact, layers,
  levels, collect_pictures, new_project). `common.capcut_root()` already looks in `%LOCALAPPDATA%` after the Mac folder.
- The score engine is plain Node. HyperFrames renders through `npx` on any system with Node 22 and Chrome.
- The Flow MCP supports Windows according to its own README (Chrome, Windows speech voices for `engine: "mac"`, the
  Recycle Bin), also not yet run on a real PC by its author.
- Claude Code on Windows runs its shell commands in Git Bash, so `bash scripts/render_layers.sh` should run there.
- **`python3`**: Windows installs `python` and `py`; `python3` may open the Microsoft Store instead. On Windows run the
  scripts with `py` (or `python`) wherever SKILL.md says `python3`.

## 1. Transparent motion-graphics layers (the main Mac-only part)

On the Mac, overlays are HEVC with premultiplied alpha through `hevc_videotoolbox`. Windows ffmpeg builds have no
VideoToolbox, and no common Windows encoder writes HEVC with alpha. Options, with the ffmpeg command for each
(input: the ProRes 4444 `.mov` HyperFrames renders with `--format mov`):

| Option | Command | Does CapCut for Windows import it with transparency? |
|---|---|---|
| **ProRes 4444 MOV** (straight alpha) | `ffmpeg -i in.mov -c:v prores_ks -profile:v 4444 -pix_fmt yuva444p10le -alpha_bits 16 -vendor apl0 out.mov` | Unknown, needs a Windows test. CapCut on Mac imports it correctly (larger files). |
| VP9 WebM with alpha | `ffmpeg -i in.mov -c:v libvpx-vp9 -pix_fmt yuva420p -b:v 0 -crf 24 -auto-alt-ref 0 out.webm` | Unknown, needs a Windows test. |
| No alpha: overlay on black + Screen blend | `ffmpeg -i in.mov -filter_complex "color=black:s=1920x1080:r=30[b];[b][0]overlay=shortest=1,format=yuv420p" -c:v libx264 -crf 16 out.mp4` then set the clip's blend mode to Screen in CapCut | Imports surely (plain H.264). Unknown: whether Screen blend is free on Windows and whether a code-written draft can set it (needs the blend field in draft_info.json). Works only for light-on-dark layers (glows, snow, type); dark shadows vanish. |
| No alpha: pre-composed shots | render each shot's picture move plus its layers into one video per shot in HyperFrames | Imports surely. Loses editability of the camera keys and layers in CapCut; heavier render. |

**Recommended default for the first Windows test: ProRes 4444.** `render_layers.sh` already keeps the ProRes file
when the HEVC encode fails (it does on Windows), so no code change is needed for the test. If CapCut for Windows shows
black instead of transparency, switch to pre-composed shots (the only route with no open questions).

## 2. CapCut project folder and format on Windows

- Folder (widely reported, not verified here): `%LOCALAPPDATA%\CapCut\User Data\Projects\com.lveditor.draft`, one folder
  per project. `CAPCUT_DRAFTS` overrides it.
- **Encryption: unknown for current CapCut International on Windows.** Third-party reports say the Chinese edition
  (JianYing) encrypts `draft_content.json` from version 6 and that JianYing 9.0 on Windows re-encrypts legacy mirror
  files when a project closes while `draft_info.json` stays plain; one guide says CapCut International does not encrypt.
  CapCut 9.1 on Mac reads and keeps our plain `draft_info.json`. If the Windows edition encrypts, code-written projects
  will not open there, and this skill will not try to break that encryption. First test: build a 3-scene project and
  open it in CapCut for Windows; then close CapCut and check whether `draft_info.json` is still readable JSON.
- Media paths inside the draft are written as absolute paths; Windows paths with drive letters and backslashes are
  untested in CapCut's media list.

## 3. Media location rule

`~/Movies` is a Mac sandbox rule: CapCut on Mac cannot read media outside it. No equivalent restriction is known on
Windows (CapCut there is a normal desktop app). The builder still copies media to `%USERPROFILE%\Movies\CapCut\<name>
media` (created if missing), which is harmless. `CAPCUT_MEDIA` overrides it. Unknown until tested.

## 4. Checking the project in CapCut

The computer-use checks in SKILL.md step 9 were built on macOS. On Windows, give the user the manual checklist instead
(Part B step 11 of `checklist.md`): open the project from the home screen, no "Link media" dialog, scrub the title, key
lines, act changes and end card, the Export button reads "Export" (not "Join Pro"), Audio ticked, captions fit.

## 5. Installer

`scripts/setup.ps1` mirrors `setup.sh` with winget (Node LTS `OpenJS.NodeJS.LTS`, Python `Python.Python.3.12`, ffmpeg
`Gyan.FFmpeg`, Git `Git.Git`, Chrome `Google.Chrome`), pip for Pillow and numpy, the official whisper.cpp release zip
(`whisper-bin-x64.zip` from github.com/ggml-org/whisper.cpp, which contains `whisper-cli.exe`, added to the user PATH),
the same `ggml-small.en.bin` model, and the Flow MCP via `git clone` + `npm install` + `npm run build` +
`claude mcp add --scope user flow -- node <folder>\dist\index.js`. Same modes: check (default), `-DryRun`,
`-Install` (asks once), `-Yes`, `-NoRender`. **Untested; not even syntax-checked** (no PowerShell on the Mac it was
written on). Run: `powershell -ExecutionPolicy Bypass -File scripts\setup.ps1`.

## 6. First Windows test, in order

1. `setup.ps1` (check), then `-Install` on a clean PC; note every failure.
2. Ingest `examples/storyboard-v2-sample.md`, lint (needs no CapCut).
3. Voice with `flow_narrate` (`engine: "mac"` uses Windows voices), 3 test pictures, transcribe, align, layers, render.
4. Build the project; open it in CapCut for Windows: does it open, are overlays transparent (ProRes), do the keyframes
   and captions play, is the Export button free?
5. Close CapCut; is `draft_info.json` still plain JSON?
6. Write the results here and in the checklist.

Sources for the reports above (third-party, unverified): github.com/renezander030/capcut-cli issue 148 (JianYing 9.0
Windows encryption capture); gist.github.com/renezander030 (draft schema cheat sheet); voyager.so/blog/capcut-mcp
(version limits); github.com/emosheeep/capcut-export (Windows draft folder).
