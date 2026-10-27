# Free vs Pro in CapCut (what this skill uses and avoids)

## Used (free, written directly into the project)
| Building block | How it is used |
|---|---|
| Photo and video clips on the main track | every shot; living plates are short MP4s |
| Overlay video tracks with transparency | type, weather/film effects, film burns, dissolve tails |
| Keyframes: scale, position, opacity | the camera (zoom/pan), dissolves (opacity of the outgoing copy), flashes and dips (solids) |
| Solid colour images | flashes (white/red), dips and fades (black), the end hold |
| A transparent PNG frame | 2:1 letterbox + vignette over everything |
| Text clips with a local font | captions |
| Audio clips | narration, score, effects |
| Export up to 4K, H.264 / HEVC | the user's export |

## Avoided (Pro or account-bound)
| Feature | Why it appears / how we avoid it |
|---|---|
| Optical flow | switched on automatically when clips are slightly sped up or slowed down: we keep every clip at exactly 1x on the frame grid |
| AI ultra HD (export) | upscaling at export: keep it off; we upscale small pictures ourselves at project creation |
| Store effects, filters, transitions, animations, text templates, stickers | resource ids per account, many Pro: replaced by our own layers and keyframes |
| Pro fonts | we ship open-licence fonts and point captions at a local file |
| AI features (auto reframe, retouch, voice changers, AI captions) | not needed: captions come from our word timings |

## Before telling the user it is ready
Open Export: the button must read **Export**. If it reads "Join Pro to export", look for a diamond (Pro) marker in the
export panel (usually Optical flow): rebuild after fixing the cause (never just tell the user to subscribe).
