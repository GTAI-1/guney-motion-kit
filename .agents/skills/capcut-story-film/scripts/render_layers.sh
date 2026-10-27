#!/bin/bash
# Render the motion-graphics layers listed in plan/layers.resolved.json (run scripts/layers.py first).
#   bash scripts/render_layers.sh <project> [id ...]          (no ids = all layers)
# Transparent layers: HyperFrames -> ProRes 4444 -> HEVC with PREMULTIPLIED alpha (CapCut composites HEVC alpha as
# premultiplied; straight alpha turns soft glows into solid white discs). Plates: H.264 MP4 at picture size.
# Then a QA sheet per layer: qa/layers/<id>.jpg (9 frames spread over the whole layer). Look at every sheet before building.
set -u
P=$(cd "$1" && pwd); shift
HF=${HF_VERSION:-0.7.109}
cd "$P" && mkdir -p renders/layers renders/tmp qa/layers
IDS=${@:-$(python3 -c "import json;print(' '.join(x['id'] for x in json.load(open('plan/layers.resolved.json'))['layers']))")}
fail=0
for id in $IDS; do
  alpha=$(python3 -c "import json;print([x for x in json.load(open('plan/layers.resolved.json'))['layers'] if x['id']=='$id'][0]['alpha'])")
  if [ "$alpha" = "True" ]; then
    npx -y hyperframes@$HF render -c compositions/$id.html -o renders/tmp/$id.mov --format mov --fps 30 --quality high --quiet > renders/tmp/$id.log 2>&1 \
      || { echo "FAIL $id (see renders/tmp/$id.log)"; fail=1; continue; }
    ffmpeg -v error -y -i renders/tmp/$id.mov -vf "format=rgba,premultiply=inplace=1,format=bgra" \
      -c:v hevc_videotoolbox -alpha_quality 0.9 -b:v 16M -tag:v hvc1 renders/layers/$id.mov \
      || { echo "FAIL $id: HEVC alpha encode (needs macOS VideoToolbox; on other systems keep the ProRes file)"; cp renders/tmp/$id.mov renders/layers/$id.mov; }
    dur=$(ffprobe -v error -show_entries format=duration -of csv=p=0 renders/tmp/$id.mov)
    ffmpeg -v error -y -i renders/tmp/$id.mov -vf "fps=9/$dur,scale=480:-1,pad=480:270:(ow-iw)/2:(oh-ih)/2:color=0x3a3f47,tile=3x3" -frames:v 1 qa/layers/$id.jpg 2>/dev/null
    rm -f renders/tmp/$id.mov renders/tmp/$id.log
  else
    npx -y hyperframes@$HF render -c compositions/$id.html -o renders/layers/$id.mp4 --fps 30 --quality high --quiet > renders/tmp/$id.log 2>&1 \
      || { echo "FAIL $id (see renders/tmp/$id.log)"; fail=1; continue; }
    dur=$(ffprobe -v error -show_entries format=duration -of csv=p=0 renders/layers/$id.mp4)
    ffmpeg -v error -y -i renders/layers/$id.mp4 -vf "fps=9/$dur,scale=480:-1,tile=3x3" -frames:v 1 qa/layers/$id.jpg 2>/dev/null
    rm -f renders/tmp/$id.log
  fi
  echo "done $id"
done
exit $fail
