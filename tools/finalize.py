#!/usr/bin/env python3
"""Final pass: letterbox, vignette, grain, titles, music mix. Usage: finalize.py <scratch> <out.mp4>"""
import json, os, subprocess, sys
S, OUT = sys.argv[1], sys.argv[2]
FF = "/opt/homebrew/bin/ffmpeg"
tl = json.load(open(os.path.join(S, "timeline.json")))
T = round(tl["total"], 3)
m = tl["macro"]          # macro shot start -> tagline 2
e = tl["endcard"] + 0.6  # end card fully black
titles = [  # (png, show_from, fade_in_start, fade_in_dur, fade_out_start, fade_out_dur)
    ("t1.png", 0.8, 0.9, 0.9, 3.6, 0.8),
    ("t2.png", m + 0.25, m + 0.35, 0.7, m + 3.45, 0.7),
    ("t3.png", e - 0.1, e, 1.2, T - 1.05, 1.0),
    ("t4.png", e + 0.6, e + 0.7, 1.0, T - 1.05, 1.0),
]
args = [FF, "-v", "error", "-y", "-i", os.path.join(S, "assembled.mov"), "-i", os.path.join(S, "music_dry.wav")]
fc = ["[0:v]crop=1920:804:0:138,pad=1920:1080:0:138:black,vignette=angle=PI/4.5,noise=c0s=7:c0f=t+u,fade=in:st=0:d=1.2[o0]"]
prev = "o0"
for k, (png, show, fi, fid, fo, fod) in enumerate(titles):
    args += ["-loop", "1", "-framerate", "24", "-t", str(T), "-i", os.path.join(S, "txt", png)]
    fc.append(f"[{k+2}:v]format=rgba,fade=in:st={fi:.3f}:d={fid}:alpha=1,fade=out:st={fo:.3f}:d={fod}:alpha=1[t{k}]")
    fc.append(f"[{prev}][t{k}]overlay=0:0:enable='between(t,{show:.3f},{fo+fod+0.05:.3f})'[o{k+1}]")
    prev = f"o{k+1}"
fc.append(f"[{prev}]format=yuv420p[v]")
fc.append("[1:a]aecho=0.8:0.88:70|150|290|470:0.32|0.24|0.16|0.10,lowpass=f=11000[mus]")
fc.append("[0:a]highpass=f=90,volume=2.2[amb]")
fc.append(f"[mus][amb]amix=inputs=2:duration=first:normalize=0,atrim=0:{T},loudnorm=I=-16:TP=-1.5:LRA=11,aresample=48000[a]")
args += ["-filter_complex", ";".join(fc), "-map", "[v]", "-map", "[a]", "-t", str(T),
         "-c:v", "libx264", "-crf", "18", "-preset", "slow", "-profile:v", "high", "-c:a", "aac", "-b:a", "192k",
         "-movflags", "+faststart", OUT]
r = subprocess.run(args, capture_output=True, text=True)
if r.returncode:
    print(r.stderr[-3000:]); sys.exit(1)
print("ok", T)
