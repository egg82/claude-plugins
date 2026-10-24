#!/usr/bin/env bash
# build.sh — render one video of a project.
#
#   build.sh <promo-dir> <video> [--reuse]
#
# <promo-dir> holds theme.json, scenes/*.mjs, assets/ and videos/<video>.json:
#   { "cut": ["intro", "fadeblack", "lab", "smoothleft", "outro"], "sound": true, "music": null,
#     "output": [1080, 1350], "viewport": [900, 900] }
# "cut" alternates scene names and ffmpeg xfade transition names. "output" is the frame
# size (default 1920x1080); "viewport" the browser's CSS size (default 1280x720), which
# sets the window's shape inside the frame.
# --reuse skips capturing scenes that already have a render (to iterate on the edit only).
#
# Frames and renders live in a cache dir, one per output size, not in the project; the
# final mp4 and a contact sheet of it are written there too, and their paths printed last.
set -euo pipefail
ENGINE="$(cd "$(dirname "$0")" && pwd)"
PROMO="$(cd "$1" && pwd)"; VIDEO=$2; REUSE=${3:-}
PW_VERSION=1.56.0
IMAGE=mcr.microsoft.com/playwright:v${PW_VERSION}-noble
spec="$PROMO/videos/$VIDEO.json"
field() { python3 -c "import json,sys; v=json.load(open(sys.argv[1])).get(sys.argv[2]); print('' if v is None else (' '.join(map(str,v)) if isinstance(v,list) else str(v).lower() if isinstance(v,bool) else v))" "$spec" "$1"; }
read -r OW OH <<< "$(field output)"; OW=${OW:-1920}; OH=${OH:-1080}
read -r VW VH <<< "$(field viewport)"; VW=${VW:-1280}; VH=${VH:-720}
SAFE=$(field safe); SAFE=${SAFE:-0.048 0.048 0}
export PROMO_OW=$OW PROMO_OH=$OH PROMO_VW=$VW PROMO_VH=$VH PROMO_SAFE=$SAFE
ROOT=$(git -C "$PROMO" rev-parse --show-toplevel 2>/dev/null || dirname "$PROMO")
WORK="${XDG_CACHE_HOME:-$HOME/.cache}/promo-video/$(basename "$ROOT")/${OW}x${OH}-${VW}x${VH}"
mkdir -p "$WORK"
cp "$ENGINE"/*.mjs "$ENGINE"/*.py "$ENGINE"/assemble.sh "$WORK"/
rm -rf "$WORK/scenes" "$WORK/assets"
cp -r "$PROMO/scenes" "$WORK/scenes"
[ -d "$PROMO/assets" ] && cp -r "$PROMO/assets" "$WORK/assets"
cp "$PROMO/theme.json" "$WORK/theme.json"
cd "$WORK"
if [ ! -d node_modules/playwright ]; then
  [ -f package.json ] || echo '{"type":"module","private":true}' > package.json
  npm i -s "playwright@$PW_VERSION"
fi

read -r -a cut <<< "$(field cut)"
scenes=(); for ((i=0; i<${#cut[@]}; i+=2)); do scenes+=("${cut[$i]}"); done
sound=$(field sound)

# Narration first: capture needs every line's length to pace the scenes.
if grep -qs 'd\.say(' $(printf 'scenes/%s.mjs ' "${scenes[@]}"); then
  PROMO_SPEC="$spec" python3 vo.py $(printf '%s\n' "${scenes[@]}" | sort -u)
fi

todo=()
for s in $(printf '%s\n' "${scenes[@]}" | sort -u); do
  [ "$REUSE" = "--reuse" ] && [ -f "out/$s/framed.mp4" ] && continue
  todo+=("$s")
done
for s in "${todo[@]}"; do
  # a live site has slow moments: one retry before giving up on a scene
  for attempt in 1 2; do
    if podman run --rm -v "$WORK":/w:Z -w /w --ipc=host -e PROMO_OW -e PROMO_OH -e PROMO_VW -e PROMO_VH -e PROMO_SAFE \
        "$IMAGE" node capture.mjs "$s"; then break; fi
    [ "$attempt" = 2 ] && { echo "capture failed twice: $s" >&2; exit 1; }
    echo "capture failed: $s, retrying" >&2
  done
done
pids=()
for s in "${todo[@]}"; do python3 camera.py "out/$s" & pids+=($!); done
for p in "${pids[@]}"; do wait "$p"; done

silent="$VIDEO-silent.mp4"; final="$VIDEO.mp4"
bash assemble.sh "$silent" "${cut[@]}"
if [ "$sound" = "true" ]; then
  PROMO_SPEC="$spec" PROMO_DIR="$PROMO" python3 sfx.py "$VIDEO.wav" 0.6 "${cut[@]}"
  # -16 LUFS integrated, -1.5 dBTP: the usual target for web and social video
  # -t, not -shortest: with an audio filter in the chain -shortest let the audio overrun
  ffmpeg -loglevel error -y -i "$silent" -i "$VIDEO.wav" -c:v copy \
    -af "loudnorm=I=-16:TP=-1.5:LRA=11" -c:a aac -ac 2 -ar 48000 -b:a 192k \
    -t "$(ffprobe -v error -show_entries format=duration -of csv=p=0 "$silent")" "$final"
else
  cp "$silent" "$final"
fi

# Contact sheet: eight frames spread across the cut, for looking at before calling it done.
D=$(ffprobe -v error -show_entries format=duration -of csv=p=0 "$final")
bash "$ENGINE/sheet.sh" "$final" "$VIDEO-sheet.png" > /dev/null
echo "video: $WORK/$final ($(printf '%.1f' "$D")s)"
echo "sheet: $WORK/$VIDEO-sheet.png"
