#!/usr/bin/env bash
# sheet.sh <video.mp4> [out.png] — 8 timestamped frames spread across a clip, 4x2, for looking at.
set -euo pipefail
in=$1; out=${2:-${in%.mp4}-sheet.png}
tmp=$(mktemp -d); trap 'rm -rf "$tmp"' EXIT
D=$(ffprobe -v error -show_entries format=duration -of csv=p=0 "$in")
args=()
for i in 0 1 2 3 4 5 6 7; do
  t=$(python3 -c "print(round($D * ($i + 0.5) / 8, 2))")
  ffmpeg -loglevel error -y -ss "$t" -i "$in" -frames:v 1 \
    -vf "scale=480:-1,drawtext=text='$t s':x=10:y=10:fontsize=24:fontcolor=yellow:box=1:boxcolor=black@0.5" "$tmp/$i.png"
  args+=(-i "$tmp/$i.png")
done
ffmpeg -loglevel error -y "${args[@]}" -filter_complex "[0][1][2][3]hstack=4[a];[4][5][6][7]hstack=4[b];[a][b]vstack" "$out"
echo "$out"
