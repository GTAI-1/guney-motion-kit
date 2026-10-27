# Plan file formats

All times are on the NARRATION clock (0 = first sample of the narration file). The film adds `project.pre` seconds of
pre-roll in front. Anywhere a time is expected you may write a time reference:

| Reference | Means |
|---|---|
| `12.5` | 12.5 s |
| `"s12"`, `"e12"` | start / end of scene 12 (plan/scenes.json) |
| `"s12+0.4"`, `"e30-2.6"` | with an offset |
| `"w:idea"` | start of the first spoken "idea" (qa/words.json, case and punctuation ignored) |
| `"w:never#2"` | its 2nd occurrence |
| `"w:train@81"` | first occurrence at/after 81 s |
| `"w:stop.end"` | end of the word |
| `"w:light@43-0.03"` | combine: occurrence after 43 s, minus 0.03 s |

Repeated words: "w:never" means the FIRST "never" anywhere in the narration (maybe a different sentence). For any word
that could occur twice, anchor it: `"w:never@81"`. layers.py prints the words each type line picked and warns when a line
spans more than 6 s of narration.

## project.json (written by new_project.py; edit `look` freely)

```json
{ "name": "The Lighthouse Keeper", "fps": 30, "canvas": [1920, 1080], "pre": 1.5,
  "narration": "input/narration.wav", "narration_dur": 149.24, "music": null,
  "images": { "s01": { "file": "input/images/s01.jpg", "w": 2752, "h": 1536, "source_px": [1376, 768] } },
  "look": { "captions": { "font": "assets/fonts/Montserrat-SemiBold.otf", "size": 9.5, "y": -0.74, "max_chars": 34 },
            "letterbox": 2.0, "vignette": true } }
```
`look.captions: false` turns captions off; `letterbox`: 2.0, 2.39 or null; vertical films ignore the letterbox.

## plan/script.json (you write it from the user's script)

```json
[{ "scene": 1, "act": "ACT 1: THE WORLD THAT NEVER STOPS", "narration": "The last train on Earth had been moving for two hundred years.",
   "visual": "A breathtaking aerial shot...", "camera": "Epic aerial establishing shot. Slow cinematic descent.", "sound": null }]
```
Scenes without narration are allowed (placed between neighbours by align.py).

## plan/edit.json (the shots)

```json
{ "shots": [
    { "id": "01", "pic": "s01", "t0": "s1", "t1": "s2",
      "keys": [["s1", 0.46, 0.30, 1.42], ["s2", 0.40, 0.56, 1.08]],
      "in": ["dip", "black", 0, 1.9], "note": "aerial descent onto the trestle" },
    { "id": "10a", "pic": "p10", "t0": "s10", "t1": 50.62, "bounds": [0.0, 0.125, 0.497, 0.875],
      "keys": [["s10", 0.245, 0.42, 2.05], [50.62, 0.25, 0.38, 2.22]], "in": ["cut"], "note": "left panel of a diptych" },
    { "id": "22a", "pic": "s22", "t0": "s22", "t1": 105.25, "keys": [...], "in": ["cut"],
      "shake": [{ "from": "w:pulled", "to": 105.25, "amp": 0.010, "hz": 10, "decay": 0.5 }] },
    { "id": "23", "pic": "s23", "t0": "s23", "t1": "s24", "keys": [["s23", 0.5, 0.5, 1.01]], "in": ["cut"], "still": true }
  ],
  "fade_out": ["e30-2.6", "e30-0.4"],
  "no_caption": [[0.0, 1.95], [31.7, 33.4]],
  "captions": true }
```
- Shots must be contiguous: each `t0` equals the previous `t1`; the first starts at 0 (it also covers the pre-roll).
- `pic`: a picture id from project.json, or a plate id from layers.json (then the shot plays the living plate).
- `keys`: `[time, fx, fy, zoom]`, at least one; fx/fy 0..1 of the picture; zoom 1 = fitted.
- `in`: `["cut"]`, `["dissolve", seconds]`, `["flash", "white"|"red"|"black", up, down]`, `["dip", "black"|"white", out, in]`.
- `bounds`: picture region the frame must stay inside (diptychs, letterboxed pictures).
- `shake`: list of `{from, to, amp (picture fraction), hz, decay (0 = constant), seed}`.
- `still: true` silences the "no camera move" lint warning when stillness is intended.

## plan/layers.json (motion graphics)

```json
{ "layers": [
  { "id": "title", "kind": "type", "style": "title", "glow": "150,190,255", "backdrop": "center", "out": 4.6,
    "lines": [{ "from": "w:the", "to": "w:train", "y": 360 }, { "words": [["ON EARTH", "w:on"]], "y": 572 }] },
  { "id": "key1", "kind": "type", "style": "key", "glow": "red", "out": 33.9,
    "lines": [{ "from": "w:never@31", "to": "w:train@31", "y": 455 }] },
  { "id": "act2", "kind": "type", "backdrop": "top", "t0": "s11+0.05", "out": "s11+3.4",
    "lines": [{ "text": "ACT II", "t": "s11+0.15", "class": "kick", "y": 118 },
              { "text": "THE FORGOTTEN INSTRUCTION", "t": "s11+0.5", "stagger": 0.22, "class": "card", "y": 190 }] },
  { "id": "label", "kind": "type", "backdrop": "top", "t0": "s18+0.15", "out": "s18+2.7", "glow": "255,210,150",
    "lines": [{ "typed": "200 YEARS EARLIER", "t": "s18+0.3", "cps": 18, "class": "typed", "y": 120 }] },
  { "id": "snow1", "kind": "snow", "t0": "s1", "t1": "s4" },
  { "id": "sparks1", "kind": "sparks", "t0": 105.3, "t1": "s23", "peak": "w:screamed" },
  { "id": "p10", "kind": "plate", "pic": "s10",
    "patches": [{ "x": 0.252, "y": 0.285, "r": 0.105, "rgb": "49,72,91", "a": { "scale": 0.95, "of": { "inv": { "flashes": { "times": [46.7, 47.0, 47.3] } } } } }],
    "lights": [{ "x": 0.252, "y": 0.285, "r": 0.22, "rgb": "cold", "star": 0.15, "a": { "flashes": { "times": [46.7, 47.0, 47.3], "decay": 0.12 } } }] }
]}
```

### type layers
- Line sources (pick one): `from`/`to` (spoken words between two times, upper-cased, each on its own word time; `case: "as-is"`
  keeps case), `words` (explicit `[text, time]` pairs), `text` + `t` (+ `stagger` seconds between words), `typed` + `t`
  (+ `cps`) for a typewriter label.
- Line options: `y` (top in px), `class` (`kick` small mono kicker, `mid` smaller display, `card` act-card size, `small`,
  `typed`, `hand` Caveat, `serif` Instrument Serif, `sig` cool white), `style` (`stamp` = scale-in hit, `rise` = blur-up),
  `flash: ["WORD"]` (that word flares with the glow colour).
- Layer options: `style` (`key` makes lines stamp), `glow` (colour name or "r,g,b"), `backdrop` (`center`, `top`, `bottom`,
  `none`), `t0` (default 0.3 s before the first word), `out` (exit start; default 1.6 s after the last word), `out_dur`,
  `font` (display face), `ink` (text colour).

### effect layers
`snow`, `blizzard` (snow + fog), `rain` (`wind`), `dust` (`n`), `embers` (`rgb`, `n`), `sparks` (`peak`, `ox`, `oy` origin
px), `burn` (`mid` seconds to the white peak; place it over a cut), `oldfilm` (grain, flicker, scratches, sepia, vignette).
All: `t0`, `t1`, optional `seed`. A layer starting at 0 starts with the film (covers the pre-roll).

### plate layers (living pictures)
`pic` (picture id) + `lights` and/or `patches`; the shots that use the plate are found in edit.json. Positions x, y are
fractions of the picture; r is a fraction of its width.
- light: `{x, y, r, rgb, a, star (streak length), thick, core (0..0.45 hot core; larger values are clamped), rect: [w, h] (soft rectangle, e.g. a window)}`
- patch (darkens, to hide a baked-in light): `{x, y, r, rgb ("auto" samples the colour just outside the patch; make r cover the light's whole halo), a, core, sy (squash), rot (degrees)}`
- envelope `a` (brightness over time; times are narration-clock references):
  number | `{"keys": [[t, v], ...]}` | `{"pulse": {period, duty, t0, t1, lo, hi, soft}}` (outside t0..t1 it holds `lo`, so use `lo: 0` or keys for a light that must be off before its word) | `{"flashes": {times: [...], hi, lo, attack, decay}}`
  | `{"beat": {period, t0, t1, lo, hi}}` (lub-dub) | `{"flicker": {lo, hi, rate, seed}}` | `{"inv": env}` | `{"max": [env, ...]}`
  | `{"scale": k, "of": env}` | `[env, env]` (multiplied).
- colour names: amber, red, cold, warm, lantern, blue, green, white, fire, gold, or "r,g,b".

## plan/cue.mjs (sound)

```js
export default function (s) {
  const { t, pad, drone, piano, boom, thud, silence, chord, wind, steps, birdsong } = s;
  drone(-1.5, 42, 26, 1.0, { attack: 3.5 });                    // D1 bed under act 1
  pad(0, 12, chord('Dm'), 0.8, { cut: [380, 900] });             // chords: chord('Bb', 2), chord('Fadd9')...
  for (const w of ['never', 'stop', 'the', 'train']) thud(t(`w:${w}@31`), 0.7);   // hits on the key line
  silence(t('s23'), 118.9);                                      // the turn: no score
  wind(-1.5, 18.6, 1.0); steps([114.05, 114.62], 0.45, { surface: 'frost' }); birdsong(t('w:bird'), 127.5, 0.5);
}
```
Full API at the top of `scripts/score/engine.mjs`. Gains: the stems are normalised (score peak -19 dBFS, effects
-15 dBFS) after ducking, so balance instruments against each other inside the cue sheet, then check `levels.py`.

## Storyboard v2 (from references/master-prompt.md) -> plan files

`python3 scripts/ingest_storyboard.py <storyboard.md> <P>` does this mapping. It writes a first draft; you then direct
it (camera focus points after seeing the pictures, light positions, the score). The old input (a script with VISUAL /
CAMERA / NARRATION / SOUND per scene, plus the user's own pictures and narration) still works: write `plan/script.json`
by hand as before and skip the ingest.

| Storyboard field | Goes to | How |
|---|---|---|
| A. Title, aspect ratio | `project.json` (draft if none exists), `generate.json` | title = project name and CapCut name; 9:16 -> vertical canvas |
| A. Narrator, B. narrator voice direction | `plan/voice.json` | `direction` is the `style` note for text to speech; `gender` picks the voice |
| B. Style suffix | `generate.json` `style_suffix` | appended unchanged to every image prompt that lacks it (warned) |
| B. Reference image prompts | `generate.json` `references` | `{name, id: "ref-<name>", prompt}`; bullets labelled `REF <name>` |
| C. Scene number and times | `plan/scenes.json` | **provisional** (`"provisional": true`); align.py replaces them from the recorded voice |
| C. Act headings | `plan/script.json` `act` | act changes get a dip to black |
| C. Image prompt | `generate.json` `scenes` + `script.json` `visual` | id `s01`, `s02`...; `refs` = references named in the prompt (`(REF Ada)`) |
| C. Editor move | `plan/edit.json` shot keys | push-in, pull-out, pan, tilt, hold, drift -> the camera recipes of creative-direction.md; speed sets the zoom change (slow 0.18, medium 0.28, abrupt 0.38); neighbouring repeats are mirrored; "static hold, then ..." becomes a two-stage move |
| C. Animated atmosphere | `plan/layers.json` | snow, blizzard, rain, dust, embers, sparks, film burn, old film -> effect layers over the scene (merged across neighbours; "throughout" = whole film). Lights ("the lamp switches on at the word light", "pulses", "flickers", "one after another") -> a **draft** plate per scene with the right envelope on the named word |
| C. Narrator | `plan/script.json` `narration` | "No narration" -> empty (a silent scene) |
| C. Sound design, E. audio direction | `plan/cue.mjs` | wind, drone, piano, steps, creak, click, whum, riser, strings, voices, rain, fire, birds, glass, boom, heartbeat, silence -> engine calls at the scene or the cue word; section E kept as comments |
| D. Voice-over script | `plan/narration.txt` | the exact text for text to speech; `[pause]` -> "..." |
| F. Title | `layers.json` type `title` | spoken -> built word by word on the words; not spoken -> word by word after the line it follows; split into lines of at most 16 characters |
| F. Act card | `layers.json` type, `backdrop: top` | "ACT II: THE ANSWER" -> kicker "ACT II" + card "THE ANSWER" at the scene start |
| F. Key phrase / stamp | `layers.json` type `style: key` | stamped on its spoken words (`from`/`to`), plus a `no_caption` range so the words are not shown twice |
| F. Date / place label | `layers.json` typed label | typewriter at the scene start |
| F. End card | `layers.json` type | after the last spoken word, held to the end |
| G.4 Match-cut pairs | `generate.json` `match_pairs` + `scenes[].match`, `edit.json` | the second scene reuses the first one's camera recipe, enters on a dissolve, and is generated with the first picture as an extra reference |

**Word anchors before the voice exists.** The ingest writes `"w:light"` for the first time a word is spoken and
`"w:light#2"` for later ones (counted over the whole narration), so repeated words point at the right occurrence. A
cue word that is a different form of a spoken word ("light" vs "lights") is matched to that form. Until
`transcribe.py` runs, word times are estimated by spreading each scene's words over its planned time (lint and
layers work, marked provisional). After transcription, check the words each type line picked (layers.py prints them);
use `"w:word@<seconds>"` if an occurrence count ever lands on the wrong one (an ad-libbed extra word, for example).

**Draft layers.** A layer with `"draft": true` is left out of the build (lint lists it). Light plates are drafts until
you place each light from `qa/grid/<id>.jpg` (x, y, r), add a patch if the light is baked into the picture, delete
`draft`, and point the shot at the plate (`"pic": "p03"`). Each draft carries a `todo` with the cue.

### plan/generate.json

```json
{ "title": "The Keeper of the Last Lamp", "slug": "the-keeper-of-the-last-lamp", "aspect_ratio": "16:9",
  "style_suffix": "Cinematic still, 35mm anamorphic lens, ...", "flow_folder": "~/flow-mcp-out/the-keeper-of-the-last-lamp",
  "references": [{ "name": "Ada", "id": "ref-ada", "prompt": "A woman in her late fifties ... no logos." }],
  "scenes": [{ "id": "s01", "scene": 1, "prompt": "... no logos.", "refs": ["ref-lighthouse"] },
             { "id": "s06", "scene": 6, "prompt": "...", "refs": ["ref-lighthouse"], "match": "s01" }],
  "match_pairs": [["s01", "s06"]] }
```

### plan/voice.json

`{ "direction": "Calm, low, warm female voice, slow...", "gender": "female", "words": 53, "planned_seconds": 36, "planned_wpm": 88 }`
