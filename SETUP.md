# Setting up the kit (for the AI assistant)

The person has opened this folder in their assistant and asked you to set it up. Do these steps in order, run the commands
yourself, explain each one in a short plain sentence, and stop to help if one fails.

0. **If the kit is not here yet** (they pasted the download sentence into an empty folder), download it into this folder
   without needing Git: `curl -L -o kit.zip https://github.com/GTAI-1/guney-motion-kit/archive/refs/heads/main.zip`,
   unzip it, rename the folder to `guney-motion-kit`, delete the zip, and work inside that folder from now on.
1. **Install what is missing, yourself.** They should not have to install anything by hand. Check `node -v` (needs 22 or
   newer) and `ffmpeg -version` / `ffprobe -version`, then install only what is missing, without admin rights where possible:
   - **Mac:** with Homebrew (`brew -v` works): `brew install node ffmpeg`. Without Homebrew: put Node 22 from
     https://nodejs.org/dist/latest-v22.x/ (the `darwin-arm64` or `darwin-x64` `.tar.gz`) in `~/.local/node` and FFmpeg +
     FFprobe static builds from https://evermeet.cx/ffmpeg/ in `~/.local/bin`, then add both to `PATH` in `~/.zshrc`.
   - **Windows:** `winget install OpenJS.NodeJS.LTS Gyan.FFmpeg` (they may need to click Yes once), then open a new terminal.
   - **Linux:** Node 22 from nodejs.org (or `nvm`), `sudo apt install ffmpeg`.
   - Python 3 is only needed later for the checking and Resolve tools (`pip install numpy pillow`).
   Tell them in one line what you are installing and why. If a step truly needs their password or a click (a system
   dialog), say exactly what to type or click.
2. **Ask two questions** (in one message):
   - their first name (Claude windows in their videos greet them with it);
   - whether to turn on the **Guney house style**. In one line: an animated background that never stops moving, graphics
     that build on screen instead of static slides, big phone-readable type, one element at a time, and every video
     checked before it is shown. Recommend yes for a first video; they can change it any time.
3. **Run setup with their answers:** `npm run setup -- --name "<name>" --house-style on` (or `off`).
   It installs the packages, downloads the render browser, writes `kit.config.json` and syncs `CLAUDE.md`, `GEMINI.md`
   and `.agents/skills/` from `AGENTS.md` and `.claude/skills/`.
4. **Make and render the starter:**
   ```sh
   npm run new-video -- hello
   cd video-projects/hello
   npx hyperframes render -o renders/hello.mp4 --fps 60 --quality high
   ```
   Open `renders/hello.mp4` for them (Mac: `open renders/hello.mp4`). It is 10 seconds: the animated background, a typed title,
   two 3D-style cards, and a Claude-style window that types a prompt and zooms onto the answer.
5. **Tell them they are ready**, in three lines: how to ask for a video ("Make me a 15-second intro about ..."), that they
   can share a script, voiceover, screen recordings or a reference video, and that every new video starts with
   `npm run new-video -- <name>`.

If the house style is on, read `house-style/HOUSE-STYLE.md` before the first creative decision of any video.
