#!/usr/bin/env python3
"""Build the cinematic glasses ad from Flow clips. Run: python3 -I build.py <scratch_dir> <out_mp4>"""
import json, os, subprocess, sys

S = sys.argv[1]
OUT = sys.argv[2]
FF = "/opt/homebrew/bin/ffmpeg"
SEG = os.path.join(S, "seg")
os.makedirs(SEG, exist_ok=True)

# (source, start, duration, zoom) zoom>0 push-in, <0 pull-out
shots = [
    ("C", 0.15, 3.10, 0.07),   # 1 establishing forest tea room
    ("A", 3.05, 3.35, 0.05),   # 2 frontal wide
    ("C", 3.35, 3.20, 0.05),   # 3 low dolly, cushion + jar
    ("A", 0.00, 2.90, 0.06),   # 5 first glimpse of glasses
    ("B", 0.10, 3.15, 0.05),   # 6 overhead table with glasses
    ("E", 0.00, 2.95, 0.08),   # 7 HERO glasses
    ("E", 3.05, 2.85, 0.06),   # 8 macro texture
    ("B", 3.35, 3.20, 0.04),   # 9 side, tea tray
    ("B", 6.70, 3.25, 0.04),   # 10 rack focus foreground
    ("E", 6.00, 4.00, -0.06),  # 12 pull back to forest
]
# transitions between shot i and i+1: (type, duration)
trans = [
    ("fade", 0.8), ("fade", 0.8), ("fade", 0.7), ("fade", 0.6),
    ("fadewhite", 0.9),  # into hero
    ("fade", 0.4), ("fade", 0.6), ("fade", 0.6),
    ("fade", 0.9),  # into final pull-back
]
END_CARD = 4.6
END_FADE = 1.2

GRADE = ("eq=contrast=1.07:saturation=0.88:gamma=0.98,"
         "colorbalance=rs=-0.03:bs=0.04:rh=0.05:gh=0.01:bh=-0.04,"
         "curves=all='0/0.03 0.25/0.22 0.75/0.78 1/0.97'")

def run(cmd):
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode:
        print(r.stderr[-3000:]); sys.exit(1)

# 1. render each graded, moving shot
for i, (src, st, d, z) in enumerate(shots):
    if z >= 0:
        zexpr = f"(1+{z}*t/{d})"
    else:
        zexpr = f"(1+{-z}*(1-t/{d}))"
    vf = (f"scale=3840:2160:flags=lanczos,"
          f"scale=w='trunc(3840*{zexpr}/2)*2':h='trunc(2160*{zexpr}/2)*2':eval=frame:flags=bicubic,"
          f"crop=3840:2160,scale=1920:1080:flags=lanczos,{GRADE},fps=24,format=yuv420p,setsar=1")
    af = f"aformat=sample_rates=48000:channel_layouts=stereo,afade=in:d=0.05,afade=out:st={d-0.05}:d=0.05"
    run([FF, "-v", "error", "-y", "-ss", str(st), "-t", str(d), "-i", os.path.join(S, "src", f"{src}.mp4"),
         "-vf", vf, "-af", af, "-c:v", "libx264", "-crf", "12", "-preset", "fast", "-c:a", "pcm_s16le",
         os.path.join(SEG, f"s{i:02d}.mov")])
    print("shot", i + 1, "done", flush=True)

# end card: black with silence
run([FF, "-v", "error", "-y", "-f", "lavfi", "-i", f"color=black:s=1920x1080:r=24:d={END_CARD}",
     "-f", "lavfi", "-i", f"anullsrc=r=48000:cl=stereo", "-t", str(END_CARD),
     "-c:v", "libx264", "-crf", "12", "-pix_fmt", "yuv420p", "-c:a", "pcm_s16le", os.path.join(SEG, "s99.mov")])

durs = [s[2] for s in shots] + [END_CARD]
trans_all = trans + [("fadeblack", END_FADE)]

# 2. offsets
offsets, acc = [], durs[0]
for k, (_, td) in enumerate(trans_all):
    off = acc - td
    offsets.append(off)
    acc = off + durs[k + 1]
total = acc
starts = [0.0] + offsets  # timeline start of each shot
types = [t for t, _ in trans_all]
hero_i = types.index("fadewhite")
coll_i = types.index("fadeblack")
macro_i = [k for k, s in enumerate(shots) if s[0] == "E" and abs(s[1] - 3.05) < 0.01][0]
info = {"total": total, "starts": starts, "hero": offsets[hero_i], "collection": offsets[coll_i] if coll_i < len(types) - 1 else None,
        "endcard": offsets[-1], "macro": starts[macro_i]}
json.dump(info, open(os.path.join(S, "timeline.json"), "w"), indent=1)
print(json.dumps(info))

# 3. xfade chain
files = [os.path.join(SEG, f"s{i:02d}.mov") for i in range(len(shots))] + [os.path.join(SEG, "s99.mov")]
inputs = []
for f in files:
    inputs += ["-i", f]
fc, vprev, aprev = [], "0:v", "0:a"
for k, (tt, td) in enumerate(trans_all):
    vo, ao = f"v{k}", f"a{k}"
    fc.append(f"[{vprev}][{k+1}:v]xfade=transition={tt}:duration={td}:offset={offsets[k]:.4f}[{vo}]")
    fc.append(f"[{aprev}][{k+1}:a]acrossfade=d={td}:c1=tri:c2=tri[{ao}]")
    vprev, aprev = vo, ao
run([FF, "-v", "error", "-y", *inputs, "-filter_complex", ";".join(fc), "-map", f"[{vprev}]", "-map", f"[{aprev}]",
     "-c:v", "libx264", "-crf", "12", "-preset", "fast", "-c:a", "pcm_s16le", os.path.join(S, "assembled.mov")])
print("assembled", flush=True)
