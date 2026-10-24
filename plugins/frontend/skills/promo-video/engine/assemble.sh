#!/usr/bin/env bash
# Join the rendered segments with xfade transitions: assemble.sh out.mp4 seg1 T1 seg2 T2 seg3 ... (T = transition name)
set -euo pipefail
out=$1; shift
D=0.6
inputs=(); segs=(); trans=()
while [ $# -gt 0 ]; do segs+=("$1"); shift; [ $# -gt 0 ] && { trans+=("$1"); shift; }; done
dur() { ffprobe -v error -show_entries format=duration -of csv=p=0 "$1"; }
fc=""; prev="[0:v]"; acc=$(dur "out/${segs[0]}/framed.mp4")
for i in "${!segs[@]}"; do inputs+=(-i "out/${segs[$i]}/framed.mp4"); done
for ((i=1; i<${#segs[@]}; i++)); do
  off=$(python3 -c "print(round($acc - $D, 3))")
  fc+="${prev}[$i:v]xfade=transition=${trans[$((i-1))]}:duration=$D:offset=$off[v$i];"
  prev="[v$i]"
  acc=$(python3 -c "print($acc - $D + $(dur "out/${segs[$i]}/framed.mp4"))")
done
ffmpeg -loglevel error -y "${inputs[@]}" -filter_complex "${fc%;}" -map "$prev" -c:v libx264 -crf 16 -preset medium -pix_fmt yuv420p -r 60 "$out"
echo "$out: $(dur "$out")s"
