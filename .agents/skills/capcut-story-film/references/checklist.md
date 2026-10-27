# Make a story film with Claude, Google Flow and CapCut

You pick a story (or let Claude suggest one). Claude writes the storyboard, records the narration, generates the
pictures in Google Flow, then builds a finished CapCut project with zooms, transitions, captions, motion graphics, music
and sound effects. You review it in CapCut and export.

**You need:** a Mac, a Claude account, a Google account (Google Flow gives every account free daily credits, and still
pictures have cost 0 credits so far), Google Chrome, and the free CapCut desktop app. Optional: a free Google AI Studio
key for the best narration voices.

> **Windows:** built and tested on Mac. It should also work on Windows, but that has not been tested yet.

Each step is marked:
- **YOU** = only you can do it (installing an app, signing in, a system setting).
- **ASK CLAUDE** = paste the quoted line into Claude Code. Claude does the work and asks before it installs or changes anything.

Where a step differs, the **Mac** and **Windows** versions are listed separately. Otherwise it is the same on both.

---

## PART A. One-time setup

**1. YOU: install Claude Code and sign in.**
- **Mac:** get it from claude.com/code, open it once and sign in.
- **Windows:** get the Windows installer from claude.com/code and follow its steps. If it asks for Git for Windows, install that too. Then open **PowerShell** and type `claude` to sign in.

**2. YOU: install CapCut (free).** Download the desktop app for your system from capcut.com, open it once, then quit it.
Then switch off automatic updates: **CapCut > Settings > General > Software update > "Get notified about updates"**
(not "Automatic updates"), and Save. When CapCut later shows a "Version update" window, close it; do not click
**Install now**. The skill builds projects for the CapCut version it was tested with (9.1 on Mac); a newer version
can break that.
- **Windows:** the same setting should be under Settings > General (not checked on Windows). Quit CapCut fully: check
  the system tray (bottom right, the ^ arrow) and right-click the CapCut icon > Quit if it is still running.

**3. YOU: save the skill file.** Save `capcut-story-film.zip` in your **Downloads** folder. Leave it zipped.
- **Windows:** that is `C:\Users\<your name>\Downloads`.

**4. YOU: make a working folder and open Claude Code in it.** Claude Code only sees the folder you open it in. Use a new empty folder called **Story Films** on your Desktop.
- **Mac:** open **Terminal**, type `cd ~/Desktop/"Story Films"`, press Enter, then type `claude` and press Enter.
- **Windows:** in File Explorer, create the folder on your Desktop. Right-click it and choose **Open in Terminal** (Windows 11). On Windows 10, open PowerShell and type `cd "$HOME\Desktop\Story Films"`. Then type `claude` and press Enter. If your Desktop is synced by OneDrive the path is `$HOME\OneDrive\Desktop\Story Films`; "Open in Terminal" avoids having to know.
- **Either system, Claude desktop app:** start a new session and choose the **Story Films** folder when it asks.

**5. ASK CLAUDE: install the skill.** Paste:
> "Install the skill from capcut-story-film.zip in my Downloads folder. Put it in my Claude skills folder (.claude/skills in my user folder), then confirm it is installed."

You approve the file writes when Claude asks. If Claude does not see the skill afterwards, quit Claude Code and reopen it in the same folder.
- **Windows:** the skills folder is `C:\Users\<your name>\.claude\skills`.

**6. ASK CLAUDE: install the tools the skill needs, including the Google Flow connection.**
- **Mac, paste:**
  > "Set up capcut-story-film. Run its check, show me what is missing, and install it only after I say yes."
- **Windows, paste:**
  > "Set up capcut-story-film on Windows with its setup.ps1. Show me what is missing and install it only after I say yes."

Claude shows a list and you say yes once. It can include Homebrew (Mac), Node, Python with two add-ons, ffmpeg,
whisper.cpp with its speech model (466 MB), git, Chrome, and the **Flow MCP** (the connector that lets Claude use
Google Flow; Claude downloads it, builds it and adds it to Claude Code). The animation renderer (HyperFrames) needs no
separate install; it downloads the first time it runs.
- **Mac:** your Mac may ask for your password (Homebrew's installer needs it), and may ask to install Apple's Command
  Line Tools.
- **Windows:** Windows may show a "Do you want to allow this app to make changes?" box. Choose Yes. Close and reopen PowerShell after installs so the new tools are found.

**7. YOU: restart Claude Code, then sign in to Google Flow.** Quit Claude Code and reopen it in the **Story Films**
folder (step 4); it loads the Flow connection when a session starts. Then ask Claude:
> "Open the Flow sign-in window."

Claude runs the Flow MCP's sign-in (`npm run login`), which opens a separate Chrome window. Sign in to Google there
yourself, open or create a Flow project, and leave the window open. Claude never types your password.

**8. YOU (optional, best voices): add a free Google AI Studio key.** Get one at aistudio.google.com/apikey. Ask Claude
to "open Flow Studio", then paste the key in **Voice > Google AI Studio key > Save key**. Never paste the key into the
chat. Without a key, Claude can use your computer's own voices.

**9. YOU: let Claude see your screen (used to check the finished CapCut project).**
- **Mac:** System Settings > Privacy & Security. Switch on **Screen Recording** and **Accessibility** for the app you run Claude Code in (Terminal or the Claude app). The Mac usually asks the first time. You may need to quit and reopen that app.
- **Windows:** there are no switches to flip. If Claude says it cannot view or control CapCut, open the project yourself and do the checks in Part B step 12 by eye.

**10. ASK CLAUDE: final check.** Same on both. Paste:
> "Run the capcut-story-film check and tell me anything still missing or out of date, including the CapCut version."

You are ready when it reports no problems (warnings about optional items are fine).

**11. Optional, after your first film:** type `/fewer-permission-prompts` so safe, repeated approvals stop appearing.

---

## PART B. Each new film

1. **Start.** Say: "Use the capcut-story-film skill to make a new film." Claude asks your settings in one question:
   length, story idea (or "suggest ideas"), genre, visual style, **16:9 or 9:16**, male or female narrator, type of
   ending. (The prompt Claude follows is in the skill at `references/master-prompt.md` if you want to read it.)
2. **Pick a story.** With "suggest ideas" Claude proposes seven and ranks the best three. Choose one.
3. **Review the storyboard.** Check the story, the narration and the scene count. Ask for changes now. Nothing has been generated yet, so this costs nothing.
4. **Voice.** Claude records one free test line in the storyboard's narrator voice. You listen and approve the voice, then it records the full narration. Listen to all of it. Claude tells you the real length, which now replaces the planned length.
   - **You approve:** the voice (and any credits, though this voice route is free).
5. **Reference images.** Claude generates one picture of each recurring character, place and key object, so they look the same in every scene. Review them and ask for any weak one to be redone.
   - **You approve:** the credit quote.
6. **Scene images.** One still per scene, made all at once in a single batch with your reference characters, places and objects attached, so they look the same everywhere. A scene can show several characters together. A 5-minute film is about 50 scenes.
   - **You approve:** the credit quote for the whole batch. Claude asks again before raising any spending cap.
7. **Coverage check.** Claude shows a contact sheet and lists any scene without a picture, then regenerates only those (and any you flag).
8. **Build.** Claude continues on its own: timing from the voice, camera moves, motion graphics, music and sound.
9. **Soundtrack preview.** Claude sends an MP3 of the music and sound effects under the voice before building the project. Say what to change. Ask for the shot storyboard (first and last frame of every shot) if you want to see it.
10. **Close CapCut** (or leave it on its home screen) when Claude asks. The project is written while it is closed.
11. **Claude checks the project in CapCut** (Mac, with screen access) and tells you what to look at.
12. **Open the project in CapCut and check:**
    - no "Link media" dialog appears
    - scrub through the key moments
    - the Export button says **Export**, not "Join Pro"
    - **Audio** is ticked in the export settings
    - captions fit the screen (34 characters per line, two lines at most)
13. **Give your notes.** Claude fixes them and rebuilds under a new project name.
14. **Export from CapCut.** Optional extras: a subtitle (SRT) file for YouTube, thumbnail stills.
15. **Clean up.** Claude moves scratch files and caches to the **Trash** (Mac) or **Recycle Bin** (Windows). It never empties it. Keep the project and its media until you have uploaded.

Already have your own script, pictures or narration? Tell Claude; it skips the matching steps.

---

## PART C. Everything you may be asked to approve

| When | What you will see | Your call |
|---|---|---|
| Any step | Claude Code asks permission to run a command, write a file, or use a tool for the first time | Allow once, or allow always for safe repeats |
| Setup | The list of tools to install | One yes. Mac: password may be requested. Windows: a "make changes" box appears |
| Setup | Adding the Flow connector to Claude Code | Yes, then restart Claude Code |
| Setup | Google Flow sign-in in its own Chrome window | You do this; Claude cannot |
| Setup and build | Mac only: Screen Recording, Accessibility, or file-access prompts | Allow for the app running Claude Code |
| Voice | A free test line, then the full recording | Yes after you like the test line |
| Images | Credit quote for references, then for the scene batch. Claude asks again before raising any spending cap | Yes, or ask for fewer images |
| Build | "Close CapCut before I write the project" | Close it |
| Checking CapCut | Claude takes control of the screen to look at CapCut. Some dialogs (Link media, Export) need it to take full control to dismiss them | Allow. To take your computer back, tell Claude "let me take over" |
| Cleanup | Moving files to the Trash or Recycle Bin | Yes. Claude never deletes permanently and never empties it |
| Always | Your original files are never edited or deleted | Nothing to approve |
