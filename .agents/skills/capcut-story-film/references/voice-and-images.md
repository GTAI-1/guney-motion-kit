# Voice, reference images and scene images (through the Flow MCP)

The front half of the pipeline, in a fixed order: **voice first** (the recording sets the real runtime before any
picture is made), then **reference images**, then **one still per scene**. Every step has a review gate, and nothing
that could cost credits runs without a yes.

The Flow MCP drives Google Flow in its own Chrome window, signed in as the user. Tools used here:
`flow_status` (sign-in, plan, credits), `flow_voices` + `flow_narrate` (voice), `flow_generate` (pictures, with
references and a credit cap), `flow_wait` (collect results), `flow_retry`, `flow_agent_images` (fast batch, see below).
The user never types tool names; you call them.

Before starting: `flow_status`. If it says the user must sign in or open a project, tell them in plain words and wait.

## Skip paths

- The user already has a narration file: skip step 1, run `new_project.py <P> --update --narration <file>`.
- The user already has pictures: skip steps 2 and 3; put them in `<P>/media/stills/` named by scene id (`s01.png`...)
  or use `new_project.py --number` for a plain folder, then `contact.py`.
- The user has neither a storyboard nor wants one (the old way: script + pictures + narration, like the train film):
  start at SKILL.md step 2. Nothing here is required.

## 1. Voice (free: Google AI Studio voices through `flow_narrate`)

`flow_narrate` records narration with `engine: "gemini"` (Google AI Studio text to speech, the same voices Flow offers)
for free with a free AI Studio key, no credits, up to 400 characters per take (longer scripts are recorded in takes and joined, step 3). `engine: "mac"` uses a voice installed on the computer
(also free, lower quality; fine for a timing guide). Flow's own in-app voice generation costs credits: do not use it
unless the user asks for it and approves the cost.

The key: `flow_voices` reports whether one is set up. If not, tell the user: get a free key at
aistudio.google.com/apikey and paste it into Flow Studio > Voice > Google AI Studio key > Save key (or set
`GEMINI_API_KEY`). **Never ask for the key in chat.**

Steps:
1. `flow_voices`; pick a voice that fits `plan/voice.json` (gender and direction). Say which and why in one line.
2. **Test line.** Tell the user: "I'll record one test line so you can hear the voice before the full narration. It
   is free." Then `flow_narrate` with `project: "<slug>"`, `engine: "gemini"`, `voice`, `style` = the one-line voice
   direction from `plan/voice.json` (the storyboard's narrator direction), and `text` = the first sentence or two of
   `plan/narration.txt`. Send the file (SendUserFile) and wait for approval. Try another voice or style if asked.
3. **Full narration.** `flow_narrate` takes **at most 400 characters per take**, so record `plan/narration.txt` in
   takes: split it at paragraph breaks, keeping each take under 400 characters and cutting at the "..." pause marks
   wherever possible, same voice and style for every take (add "softer and slower" to the last take if the storyboard
   asks for it). Then trim each take's edge silence, even out their loudness and join them, with 0.7 s between
   paragraphs and 1.6 s at each "..." pause:
   ```bash
   # per take: trim leading/trailing silence, mono 48 kHz
   ffmpeg -i narration-02.m4a -af "silenceremove=start_periods=1:start_threshold=-45dB:start_silence=0.08,areverse,silenceremove=start_periods=1:start_threshold=-45dB:start_silence=0.15,areverse" -ar 48000 -ac 1 t02.wav
   # check each take's loudness (ebur128 "I:"); lift any take more than 0.5 dB quieter with -af volume=<dB>dB
   # gaps: ffmpeg -f lavfi -i anullsrc=r=48000:cl=mono -t 1.6 gap-1.6.wav ; list.txt: file 't02.wav' / file 'gap-0.7.wav' / ...
   ffmpeg -f concat -safe 0 -i list.txt -c pcm_s16le narration-joined.wav
   ```
4. Attach it: `python3 scripts/new_project.py <P> --update --narration <the .m4a or .wav>`. It converts to
   `input/narration.wav` and prints **recorded length vs planned length**. Tell the user both numbers in one line
   ("2:41 recorded, 3:00 planned: the film will be 2:41 plus a few seconds of opening and ending").
5. Send the full narration for a listen before spending anything on pictures.

If `flow_narrate` is not available (an older Flow MCP, or Flow not installed): say so plainly, and ask the user for a
narration file (record it themselves or with any text-to-speech tool). The train film was made that way.

## 2. Reference images

One per recurring character, place and key object: `plan/generate.json` -> `references` (name, id, prompt with the
style suffix already appended).

1. Tell the user the list ("3 reference images: Ada, the lighthouse, the lamp") and what they cost. Stills have been
   0 credits on Flow's default image model; confirm with Flow's quote (step 4) before generating.
2. `flow_generate` with `project: "<slug>-refs"`, one scene per reference: `type: "image"`, `prompt`, `aspect_ratio`
   (from generate.json; a character reads best at the film's ratio too), `max_credits: 0`, no `model` (Flow's default
   image model) unless the user picked one. `flow_wait` until finished.
3. Copy the results so the Flow MCP can read them later as references: they already sit under `~/flow-mcp-out/` (the
   only place the Flow MCP can read from; it cannot read ~/Desktop or ~/Documents, macOS blocks it). Keep them there,
   named by reference id: `~/flow-mcp-out/<slug>-refs/ref-ada.png`. Also copy them into `<P>/media/refs/` for the record.
4. **Review gate:** send all reference images together and ask: "Do these look right? Anything to change before I make
   the scenes?" Regenerate only the ones the user flags. Do not continue until they say go.

## 3. Scene images

One still per scene, from `plan/generate.json` -> `scenes` (ids s01, s02...). Each prompt already ends with the
style suffix, unchanged. Keep the aspect ratio chosen in the settings.

1. **Quote and ask.** Tell the user: "Next: <N> scene pictures. Flow quotes stills at <X> credits each (<total> in
   all). OK to go ahead?" Get Flow's real price first (step 4). Wait for a yes.
2. **Batch: one agent-mode request for every scene.** `flow_agent_images` with `project: "<slug>"`, `scenes` (the
   prompts, in order), `aspect_ratio`, `references` (every reference image with a short name, e.g.
   `{image: "asset:<title>", name: "Ines"}`; use `asset:<title>` for references already in the Flow project so nothing
   is uploaded again; up to 10) and `scene_references` (one list of names per scene, empty for none; a match-cut scene
   also lists its partner's finished picture). Flow's agent renders the whole batch in parallel, a few minutes for 30
   scenes, 0 credits. Scenes that fail are asked of the agent again, then made one by one with their references; for
   any still missing, run the batch again with just those scenes. Several characters can be attached at once, so a
   scene can show more than one character together.
   - Older Flow MCP builds have no `references` on `flow_agent_images` (the tool description says "no reference
     images"): then use `flow_generate` with per-scene `reference_images` (max 3; one paced job per scene, about
     1.5 minutes each) and suggest updating the Flow MCP.
3. **Collect.** `python3 scripts/collect_pictures.py <P> --from ~/flow-mcp-out/<slug>` copies `scene-01.png`... to
   `<P>/media/stills/s01.png`... (pairing files with the scene ids in order; pass `--ids` for a partial batch, `--map`
   for exact names). Then `python3 scripts/new_project.py <P> --update --images <P>/media/stills`.
4. **Coverage check.** `python3 scripts/contact.py <P>`: the contact sheet (`qa/pictures.jpg`), the scene-to-picture
   map, and the list of scenes still MISSING. Look at the sheet: off-model faces, text in the picture, wrong framing for
   the planned move, a match-cut pair that does not match. Regenerate only the missing or broken scenes (same call shape,
   only those scenes), collect with `--ids`, update, check again. Send the contact sheet to the user.

## 4. Credits: always quote first, never raise a cap silently

- `flow_status` shows the plan and credits left; say the balance before a batch.
- `flow_generate` reads Flow's own quote for every scene before spending and **skips** any scene quoted above
  `max_credits` (nothing spent). Run picture batches with `max_credits: 0` unless the user approved a price: free stills
  go through, and anything Flow wants to charge for is skipped and reported instead of paid. Show that quote to the
  user, ask, and only then rerun with the approved cap.
- Never raise a cap on your own. If a quote exceeds the approved cap (it happened once: 15 credits quoted against a
  12 credit cap), stop, show the number, and ask.
- Voice through `engine: "gemini"` or `"mac"` costs nothing; say so when you ask for the test line.

## 5. Then

`python3 scripts/transcribe.py <P>` and `python3 scripts/align.py <P>` replace the provisional scene times with the
recorded ones; the plan's scene and word references follow automatically. Continue with SKILL.md step 5 (study the
pictures), finishing the draft camera keys and placing the draft lights.
