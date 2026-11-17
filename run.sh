#!/bin/zsh
# Rebuild the ad from the five Google Flow clips.
# Usage: ./run.sh <clips_dir> [out.mp4]
set -e
ROOT="${0:A:h}"
CLIPS="${1:?usage: ./run.sh <clips_dir> [out.mp4]}"
OUT="${2:-$ROOT/build/stillness_ad.mp4}"
W="$ROOT/build"
mkdir -p "$W/src" "$W/txt"

link() { local f=( "$CLIPS"/$~2(N) ); [[ -n "$f" ]] || { echo "missing clip: $2"; exit 1; }; ln -sf "${f[1]:A}" "$W/src/$1.mp4"; }
link A 'Creating_film_from_reference_images_*.mp4'
link B 'Generating_forest_tea_room_short*.mp4'
link C 'Generating_forest_tea_room_video_*.mp4'
link D 'Glasses_on_stone_table_*.mp4'
link E '森林茶室眼鏡短片生成_*.mp4'

cp "$ROOT"/titles/t*.png "$W/txt/"   # pre-rendered title cards (regenerate with tools/text.swift)

python3 -I "$ROOT/tools/build.py" "$W" "$OUT"
python3 -I "$ROOT/tools/music.py" "$W/timeline.json" "$W/music_dry.wav"
python3 -I "$ROOT/tools/finalize.py" "$W" "$OUT"
echo "done: $OUT"
