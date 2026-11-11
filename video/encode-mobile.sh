#!/usr/bin/env bash
# Encode a Bao-style muted mobile mp4: 480x480, 24fps, H.264 Constrained Baseline,
# yuv420p bt709, no audio, crf 28, slow preset + the same x264 tweaks as the
# existing Thầy Bao / Cô Bao mobile clips.
set -euo pipefail
if [[ $# -lt 2 ]]; then
  echo "usage: $0 <input.mp4> <output.mp4>" >&2
  exit 1
fi
IN="$1"
OUT="$2"
mkdir -p "$(dirname "$OUT")"
ffmpeg -y -hide_banner -loglevel error \
  -i "$IN" \
  -an \
  -vf "scale=480:480:flags=lanczos,setsar=1,fps=24,format=yuv420p" \
  -c:v libx264 -preset slow -profile:v baseline -level 3.1 \
  -pix_fmt yuv420p \
  -colorspace bt709 -color_primaries bt709 -color_trc bt709 -color_range tv \
  -crf 28 \
  -x264-params "me=hex:deblock=-3,-3:psy-rd=2.00,0.70:aq-strength=1.20" \
  -movflags +faststart \
  "$OUT"
echo "encoded $OUT"
