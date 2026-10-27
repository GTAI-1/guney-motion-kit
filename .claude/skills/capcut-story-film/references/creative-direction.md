# Creative direction: turning stills and a voice into a film

The audience must never feel "slideshow". A slideshow shows pictures one after another; a film shows a CAMERA that
looks for something, cuts that answer the words, light that changes, sound that breathes, and a shape (calm, build,
turn, release). Everything below serves that.

## 1. Read the story first (plan/BEATS.md)

Fill this page before touching a shot. It takes ten minutes and decides everything.

```
LOGLINE      one sentence: who wants what, what stands in the way, what changes
THEME        the idea under the plot ("an incomplete rule kept them moving for generations")
ACTS         Act 1 (world + normal) / Act 2 (disturbance, investigation) / Act 3 (decision, consequence, new world)
TURNS        the 2-4 moments where the story pivots (scene + spoken word): these get the biggest craft
KEY LINES    the 1-3 sentences the film is about: they become on-screen type (stamped, word-synced) and score hits
REVEALS      what must stay hidden until when ("no humans before scene 27", "pods only in scene 29")
MOTIFS       objects/lights/sounds that return (the signal light, the rule, the photograph): plan their callbacks
CONTINUITY   screen direction of travel, time of day, weather, colour temperature per act
EMOTION      the curve, scene by scene, 1-10 (calm 2, curiosity 4, dread 7, release 9...)
SOUND ARC    bed per act, hits, silences, the climax
```

## 2. Audit the pictures

- Coverage: one picture per scene minimum. Scenes over ~6 s need a second angle: another picture, a crop of the same
  picture (detail insert, face from a wide shot), the other panel of a diptych, or a two-stage move inside one picture.
- Missing scenes: cover with a crop from a neighbour, a type beat over a related picture, or (if the user has an image
  tool) a generated picture matched to the references. Say what you did.
- Resolution: source width / zoom = pixels across the frame. Keep it above ~900 for 1080p (lint warns). Small sources
  are upscaled 2x at project creation, which helps, but tight crops of small pictures stay soft: zoom less.
- Hazards: letterboxed pictures, split panels, baked-in text, black bars: give those shots `bounds`.
- Light sources in the picture (lamps, screens, windows, signals, lanterns, sun, pod windows): candidates for living plates.
- Character consistency: if a face changes between pictures, cut past it fast or frame it smaller.

## 3. Camera grammar (framing recipes)

A key is `[t, fx, fy, z]`: point (fx, fy) of the picture at the frame centre at zoom z. CapCut moves linearly between
keys. The builder clamps so the picture always covers the frame. Typical zoom range 1.02-1.8 (2.2 only for sharp
pictures or diptych halves). Moves of 0.15-0.4 zoom over 4-6 s read as cinematic; faster reads as urgent.

| Move | Use it for | Keys pattern |
|---|---|---|
| Establishing descent | opening a world, arriving | start high (fy .30) at z 1.4, end on the subject (fy .55) at z 1.08 |
| Pull-back reveal | scale, loneliness, "the loop never ends" | start tight on subject z 1.6, end z 1.0-1.05 centred |
| Push-in | emotion, realisation, the line that matters | z 1.03 -> 1.25-1.35 toward eyes/hands, end on the face |
| Truck (lateral) | a character beside a window, a train passing | same z (1.2-1.3), fx .38 -> .62 (follow screen direction) |
| Tilt | boots to face, ground to sky, object to person | same fx, fy .75 -> .35, z 1.6 -> 1.35 |
| Rack (two-stage) | object then person ("the light, then his face") | key 1 on the object, hold, key 2 on the face at the spoken word |
| Telephoto crop | a distant thing that matters (a tower, a sign) | z 2.0-2.2 on it, tiny drift; use bounds on panels |
| Handheld unease | alarms, panic, uncertainty | base move + `shake` amp .003-.005, hz 3 |
| Impact shake | brakes, hits, explosions, slams | `shake` amp .010-.016, hz 10-12, decay .5 |
| Dead still | the turn: after the stop, the moment of silence | ONE key, `"still": true`: the contrast IS the effect |
| Crane up | hope, reveal of a landscape | fy .74 -> .45, z 1.4 -> 1.04 |
| Match framing | generations, time passing, "same place, new person" | identical keys on similarly composed pictures, short dissolves |
| Detail insert | hands, an object the narrator names | crop of a wider picture at z 1.8-2.1 on the object |
| Follow the gaze | a character looks at X -> next shot is X | end the look shot leaning toward X; open the next on X |

Rules:
- Start every move before its line and land the important frame ON the word (two-stage keys at word times).
- Alternate: in, out, lateral, in... Never three pushes in a row; never the same scale on both sides of a cut.
- Respect screen direction: if the train travels left to right, trucks and pans follow it until a deliberate reversal.
- Keep the subject inside the frame at the first AND last key (the storyboard shows both).
- Faster moves and shorter shots as tension rises; slower and longer as the story releases.

## 4. Cutting grammar

| Transition | Means | Typical |
|---|---|---|
| cut | the default inside a sequence; tension; action | `["cut"]` |
| dissolve | time passes, place changes, softness, memory | `["dissolve", 0.4-0.9]` |
| dip to black | act break, before a reveal, a breath | `["dip", "black", 0.25, 0.35]` |
| flash white | memory, flashback, light, a revelation | `["flash", "white", 0.06, 0.5]` |
| flash red | danger, the rule, an alarm | `["flash", "red", 0.06, 0.45]` |
| film burn (layer) | into / out of a flashback | `burn` layer over the cut, with a hard cut under it |
| match cut | identity across time (conductors across generations) | same framing + 0.15-0.2 s dissolve |
| open from black | the film's first shot | `["dip", "black", 0, 1.9]` on shot 1 |

- Every scene's picture changes 0.35 s before its narration line (align.py does it).
- Action sequences: one shot per action verb ("He pulled. The wheels screamed. The engine shuddered." = 3 shots).
- Silence after a stop: a hard cut to a dead-still shot, no music, one environmental sound.

## 5. Pacing

- Average shot 4-6 s in calm acts, 1.5-3 s in action, 6-8 s in the final release.
- The turn gets time: hold 4-6 s on the still shot after the climax.
- The ending: a long pull-back, fade to black over the last ~2.5 s, then an end card on black (3-4 s).
- A pre-roll of ~1.5 s (black + ambience) before the voice makes the first frame feel intentional.

## 6. Motion graphics (plan/layers.json)

On-screen text is rare and therefore strong:
- Title: when the narrator says the title, the title builds word by word on those words (no separate title card needed).
- Key lines: the rule/thesis, stamped one word at a time (style "key"), each on its spoken word. A key line can RETURN
  later and be completed (callback) - the most powerful type moment in a story.
- Act cards: a small kicker ("ACT II") then the act name, top of frame, over the first 3 s of the act.
- Labels: time/place ("200 YEARS EARLIER") typed like a typewriter.
- End card: the title again on black, warm.
- Captions are CapCut text (not a layer); suppress them (`no_caption`) where type already says those words.

Environment effects make stills feel alive. Match the picture: snow/blizzard (cold exteriors), rain (night, sorrow),
dust (old interiors, lamp light), embers (fire, warmth, night magic), sparks (metal, brakes, welding), old film (any
flashback), film burn (into/out of the past). Effects fade in/out; never across a scene they don't belong to.

Living plates are the signature move: a picture rendered with lights that act on cue.
- A signal that flashes "three times, a pause, three more" exactly on those words.
- A warning light that breathes; a heartbeat-red wash before a decision.
- Lamps/lanterns that flicker; pod windows or carriage lights that switch on one after another (awakening).
- A baked-in light hidden by a patch (the sky colour around it, sampled from the grid) until "a light appeared".
Light positions come from the 5 % grids. Keep glows soft and additive; never darken large areas.

Type rules: one line never wraps (the engine auto-fits to the frame), words enter one at a time (blur to sharp, no
bounce), a dark soft backdrop behind central type, exits fade with blur. Fonts: Big Shoulders Display 900 (display),
JetBrains Mono (labels), Caveat (hand-written stories), Instrument Serif (literary).

## 7. Captions

Phrase by phrase on the spoken words, max 34 characters per line (22 in 9:16), max 2 balanced lines, bottom (y -0.74),
white with a tight shadow, Montserrat SemiBold. Small phrases merge with the next when they fit one line.

## 8. Sound design (plan/cue.mjs)

Map emotions to instruments: drone = vast/cold; tone = mystery; isolated piano = intimacy, memory, discovery;
ostinato = momentum, a ticking clock; heartbeat = a decision; boom/thud = impact, a key word; riser = approach;
silence = the turning point; major pad and arpeggios = hope, resolution.
- Hits on every word of a key line; a boom when the title lands; a riser into the climax.
- The turning point: cut the score to nothing (`silence(t0, t1)`) and let one sound live (steam, wind, a bird).
- Foley for every on-screen action the narration names (a door, steps, paper, glass, a lever, a bird).
- Environment beds per location (wind outside, muffled rumble inside a vehicle, crowd in a flashback).
- Key: a minor key for the cold/mystery acts, its relative major for the release (D minor -> F major).
- Levels: voice untouched at 0 dB; score 12-16 dB under the voice while speaking, up to 6-8 dB under in gaps and at
  the climax; effects 14-18 dB under. `levels.py` measures it; adjust gains in the cue sheet, not by ear guesses.

## 9. The premium checklist (before delivery)

- [ ] Every shot has a reason to move (or a reason to be still) and lands its key frame on a word.
- [ ] No two neighbouring shots share scale and direction; no three pushes in a row.
- [ ] Each act has a different texture (colour, effects, pace, sound bed).
- [ ] Key lines on screen, stamped on their words; the callback completes the line.
- [ ] Living plates where the story names a light; effects match each environment.
- [ ] Silence at the turn; hits on key words; foley for named actions; voice clean on top.
- [ ] No duplicated words on screen; captions fit; type never wraps; nothing small.
- [ ] Storyboard, layer sheets and CapCut frames all looked at; export button reads "Export".
