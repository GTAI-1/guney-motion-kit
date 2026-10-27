#!/bin/bash
# capcut-story-film doctor and installer (macOS).
#   bash scripts/setup.sh              check only (default): a table of what is ready, changes nothing
#   bash scripts/setup.sh --dry-run    print exactly what --install would do, change nothing
#   bash scripts/setup.sh --install    show the list, ask ONCE, then install only the missing pieces
#   bash scripts/setup.sh --install --yes   same, without the question (only after the user said yes in chat)
#   add --no-render to skip the small HyperFrames test render (it downloads a browser the first time, ~2 min)
# Safe to run again any time: nothing already installed is touched, nothing is ever deleted, no sudo is used.
# Install writes a plain log to ./capcut-story-film-setup.log in the current folder.
set -u
MODE=check; YES=0; RENDER=1
for a in "$@"; do case "$a" in --check) MODE=check;; --dry-run) MODE=dry;; --install) MODE=install;; --yes) YES=1;; --no-render) RENDER=0;;
  *) echo "unknown option $a (use --check, --dry-run or --install)"; exit 2;; esac; done
SKILL="$(cd "$(dirname "$0")/.." && pwd)"
CFG="$SKILL/skill.config.json"
cfgval() { python3 -c "import json,sys;print(json.load(open('$CFG')).get('$1',''))" 2>/dev/null; }
FLOW_REPO="${FLOW_MCP_REPO:-$(cfgval flow_mcp_repo)}"
FLOW_DIR="${FLOW_MCP_DIR:-$HOME/flow-mcp}"
HF="${HF_VERSION:-0.7.109}"
MODEL="${WHISPER_MODEL:-$HOME/.cache/whisper-models/ggml-small.en.bin}"
MODEL_URL="https://huggingface.co/ggerganov/whisper.cpp/resolve/main/ggml-small.en.bin"
CAPCUT_TESTED="9.1"
LOG="$PWD/capcut-story-film-setup.log"

ROWS=(); TODO=(); fails=0
row() { ROWS+=("$1|$2|$3"); if [ "$2" = "MISSING" ]; then fails=$((fails+1)); fi; return 0; }
todo() { TODO+=("$1"); }        # "description::command"
brew_bin() { [ -x /opt/homebrew/bin/brew ] && echo /opt/homebrew/bin/brew || { [ -x /usr/local/bin/brew ] && echo /usr/local/bin/brew; } || command -v brew; }
command -v brew >/dev/null || { [ -n "$(brew_bin)" ] && eval "$("$(brew_bin)" shellenv)" 2>/dev/null; }   # fresh installs: put brew on PATH
# Pillow/numpy install route: Homebrew's Python refuses pip installs (PEP 668), so use its formulae; Apple's Python: pip --user
pymods() { case "$(command -v python3)" in /opt/homebrew/*|/usr/local/*) echo "brew install pillow numpy";; *) echo "python3 -m pip install --user pillow numpy";; esac; }

# ------------------------------------------------------------------ checks
if [ "$(uname)" = "Darwin" ]; then row "macOS" OK "$(sw_vers -productVersion)"
else row "macOS" MISSING "built and tested on macOS; on Windows use scripts/setup.ps1 (untested)"; fi

if [ -n "$(brew_bin)" ]; then row "Homebrew" OK "$("$(brew_bin)" --version | head -1)"
else row "Homebrew" MISSING "the Mac package manager used to install the tools below"
  todo "Homebrew (asks for your Mac password: Homebrew's own installer needs it to create its folder)::/bin/bash -c \"\$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)\""; fi

if command -v node >/dev/null && [ "$(node -p 'process.versions.node.split(".")[0]')" -ge 22 ]; then row "Node.js 22+" OK "$(node -v)"
else row "Node.js 22+" MISSING "$(command -v node >/dev/null && echo "have $(node -v); " )runs HyperFrames, the score engine and the Flow MCP"; todo "Node.js::brew install node"; fi

if command -v python3 >/dev/null; then row "Python 3" OK "$(python3 --version 2>&1 | cut -d' ' -f2)"
  if python3 -c "import PIL, numpy" 2>/dev/null; then row "Pillow + numpy" OK "python3 modules"
  else row "Pillow + numpy" MISSING "picture and audio maths"; todo "Pillow and numpy (Python modules)::$(pymods)"; fi
else row "Python 3" MISSING "runs the planning scripts"; todo "Python 3::brew install python"; row "Pillow + numpy" MISSING "after Python"; todo "Pillow and numpy::brew install pillow numpy"; fi

if command -v ffmpeg >/dev/null && command -v ffprobe >/dev/null; then
  row "ffmpeg + ffprobe" OK "$(ffmpeg -version | head -1 | cut -d' ' -f3)"
  if ffmpeg -hide_banner -encoders 2>/dev/null | grep -q hevc_videotoolbox; then row "HEVC VideoToolbox encoder" OK "transparent overlays for CapCut"
  else row "HEVC VideoToolbox encoder" MISSING "this ffmpeg lacks it; Homebrew's ffmpeg has it"; todo "ffmpeg (Homebrew build, with VideoToolbox)::brew install ffmpeg"; fi
else row "ffmpeg + ffprobe" MISSING "audio, video and transparent overlays"; row "HEVC VideoToolbox encoder" MISSING "comes with Homebrew's ffmpeg"; todo "ffmpeg::brew install ffmpeg"; fi

if command -v whisper-cli >/dev/null; then row "whisper.cpp (whisper-cli)" OK "word timing from the voice"
else row "whisper.cpp (whisper-cli)" MISSING "exact word timing (without it: slower, less exact fallback)"; todo "whisper.cpp::brew install whisper-cpp"; fi
if [ -f "$MODEL" ]; then row "Whisper model small.en" OK "$(du -h "$MODEL" | cut -f1)"
else row "Whisper model small.en" MISSING "466 MB speech model for whisper-cli"; todo "Whisper model ggml-small.en.bin (466 MB download from Hugging Face)::mkdir -p \"$(dirname "$MODEL")\" && curl -L --fail -o \"$MODEL.part\" \"$MODEL_URL\" && mv \"$MODEL.part\" \"$MODEL\""; fi

CC=/Applications/CapCut.app/Contents/Info.plist
if [ -f "$CC" ]; then v=$(defaults read "$CC" CFBundleShortVersionString 2>/dev/null)
  case "$v" in "$CAPCUT_TESTED"|"$CAPCUT_TESTED".*) row "CapCut desktop" OK "$v (the version this skill was tested with)";;
    *) row "CapCut desktop" WARN "$v installed; tested with $CAPCUT_TESTED. Builds may still work: check the first project closely";; esac
  D="${CAPCUT_DRAFTS:-$HOME/Movies/CapCut/User Data/Projects/com.lveditor.draft}"
  [ -d "$D" ] && row "CapCut projects folder" OK "found" || row "CapCut projects folder" MISSING "open CapCut once (you), then run this again"
else row "CapCut desktop" MISSING "install it yourself from capcut.com (free), open it once, quit it"; fi

if command -v git >/dev/null && git --version >/dev/null 2>&1; then row "git" OK "$(git --version | cut -d' ' -f3)"
else row "git" MISSING "downloads the Flow MCP; comes with Apple's Command Line Tools"; todo "git (Apple Command Line Tools; a macOS window asks you to confirm)::xcode-select --install"; fi

if [ -d "/Applications/Google Chrome.app" ]; then row "Google Chrome" OK "Flow is driven in its own Chrome window"
else row "Google Chrome" MISSING "needed by the Flow MCP"; todo "Google Chrome::brew install --cask google-chrome"; fi

if command -v claude >/dev/null; then
  FL=$(claude mcp get flow 2>/dev/null)
  if echo "$FL" | grep -q "Connected"; then row "Flow MCP" OK "registered and connected"
  elif [ -n "$FL" ]; then row "Flow MCP" WARN "registered but not connected: restart Claude Code; sign in with 'npm run login' in $FLOW_DIR"
  else row "Flow MCP" MISSING "lets Claude make the voice and pictures in Google Flow"
    if [ -z "$FLOW_REPO" ]; then todo "Flow MCP: no source set. Put its git URL in skill.config.json (flow_mcp_repo) or FLOW_MCP_REPO::false"
    else
      [ -f "$FLOW_DIR/package.json" ] || todo "Flow MCP: download it to $FLOW_DIR (not Desktop/Documents/Downloads: macOS blocks those)::git clone \"$FLOW_REPO\" \"$FLOW_DIR\""
      todo "Flow MCP: install its parts and build it::cd \"$FLOW_DIR\" && npm install && npm run build"
      todo "Flow MCP: add it to Claude Code for every folder::claude mcp add --scope user flow -- node \"$FLOW_DIR/dist/index.js\""
    fi; fi
  if [ -f "$HOME/.flow-mcp/gemini-key" ] || [ -n "${GEMINI_API_KEY:-}" ]; then row "Google AI Studio key" OK "free narration voices (key not shown)"
  else row "Google AI Studio key" WARN "optional: for Google's narration voices. You paste it in Flow Studio > Voice yourself (never in chat)"; fi
else row "Claude Code CLI" WARN "the 'claude' command is not on PATH, so the Flow MCP check is skipped (the desktop app is fine)"; fi

M="$HOME/Movies"; if [ -d "$M" ] && [ -w "$M" ]; then row "~/Movies writable" OK "CapCut can only read media from here"
else row "~/Movies writable" MISSING "CapCut reads media only from ~/Movies"; fi
free=$(df -g "$HOME" | awk 'NR==2{print $4}')
[ "${free:-0}" -ge 10 ] && row "Free disk space" OK "${free} GB" || row "Free disk space" WARN "${free} GB free; a film needs about 2-5 GB while building"

if [ $RENDER = 1 ] && command -v npx >/dev/null && command -v ffprobe >/dev/null; then
  T=$(mktemp -d "${TMPDIR:-/tmp}/csf-check.XXXX"); mkdir -p "$T/compositions"
  mkdir -p "$T/assets"; cp "$SKILL/assets/gsap.min.js" "$T/assets/"
  echo '{"paths":{"blocks":"compositions","assets":"assets"}}' > "$T/hyperframes.json"
  cat > "$T/compositions/t.html" <<'HTML'
<!doctype html><html><head><meta charset="utf-8"><script src="assets/gsap.min.js"></script></head>
<body style="margin:0;width:320px;height:180px;background:#123">
<div id="t" data-composition-id="t" data-start="0" data-duration="0.5" data-width="320" data-height="180" style="position:relative;width:320px;height:180px">
<div id="b" style="position:absolute;left:20px;top:70px;width:40px;height:40px;background:#fc0"></div></div>
<script>window.__timelines = window.__timelines || {}; const tl = gsap.timeline({ paused: true }); tl.to('#b', { x: 240, duration: 0.5, ease: 'none' }, 0); window.__timelines['t'] = tl;</script>
</body></html>
HTML
  if (cd "$T" && perl -e "alarm 300; exec @ARGV" npx -y hyperframes@$HF render -c compositions/t.html -o t.mp4 --fps 10 --quiet >"$T/log" 2>&1) && [ -s "$T/t.mp4" ]; then row "HyperFrames test render" OK "hyperframes@$HF"
  else row "HyperFrames test render" WARN "did not finish (first run downloads a browser; see $T/log)"; fi
else row "HyperFrames test render" SKIP "$([ $RENDER = 0 ] && echo 'skipped (--no-render)' || echo 'needs Node and ffmpeg first')"; fi

# ------------------------------------------------------------------ report
printf "\ncapcut-story-film check\n\n%-28s %-8s %s\n" "ITEM" "STATUS" "DETAIL"
printf "%-28s %-8s %s\n" "----" "------" "------"
for r in "${ROWS[@]}"; do IFS='|' read -r a b c <<<"$r"; printf "%-28s %-8s %s\n" "$a" "$b" "$c"; done
echo
if [ ${#TODO[@]} -eq 0 ]; then
  [ $fails = 0 ] && echo "Ready. Nothing to install." || echo "Nothing this script can install; the MISSING items above are yours to do (see DETAIL)."
  exit $([ $fails = 0 ] && echo 0 || echo 1)
fi
echo "An install would do these, in order:"
i=1; for t in "${TODO[@]}"; do printf "  %d. %s\n     %s\n" $i "${t%%::*}" "${t#*::}"; i=$((i+1)); done
[ $MODE = check ] && { echo; echo "Nothing was changed. To install: bash scripts/setup.sh --install"; exit 1; }
[ $MODE = dry ] && { echo; echo "Dry run: nothing was changed."; exit 1; }

if [ $YES = 0 ]; then printf "\nInstall all of the above? [y/N] "; read -r ans; case "$ans" in y|Y|yes|YES) ;; *) echo "Nothing installed."; exit 1;; esac; fi
echo "capcut-story-film setup $(date)" >> "$LOG"
for t in "${TODO[@]}"; do
  d="${t%%::*}"; c="${t#*::}"; echo; echo "==> $d"; echo "==> $d" >> "$LOG"; echo "\$ $c" >> "$LOG"
  if bash -c "$c" >> "$LOG" 2>&1; then echo "    done"; echo "    done" >> "$LOG"
    command -v brew >/dev/null || { [ -n "$(brew_bin)" ] && eval "$("$(brew_bin)" shellenv)" 2>/dev/null; }
  else echo "    FAILED (details in $LOG)"; echo "    FAILED" >> "$LOG"; fi
done
echo; echo "Log: $LOG"
if printf '%s\n' "${TODO[@]}" | grep -q "claude mcp add"; then
  echo "Flow MCP added. Quit Claude Code and reopen it in this same folder (it loads MCP servers when a session starts),"
  echo "then sign in to Google Flow once:  cd \"$FLOW_DIR\" && npm run login   and run this check again."
else echo "Run the check again:  bash scripts/setup.sh"; fi
