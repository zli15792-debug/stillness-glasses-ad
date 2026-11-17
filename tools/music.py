#!/usr/bin/env python3
"""Synthesize an original ambient piano + pad score timed to timeline.json. Usage: music.py <timeline.json> <out.wav>"""
import array, json, math, random, sys, wave

tl = json.load(open(sys.argv[1]))
SR = 44100
TOTAL = tl["total"] + 0.5
HERO = tl["hero"] + 0.45          # white flash peak
HAS_COLL = tl.get("collection") is not None
COLL = (tl["collection"] if HAS_COLL else tl["starts"][-2]) + 0.45  # act-3 change
END = tl["endcard"] + 0.6
N = int(TOTAL * SR)
L = array.array("d", bytes(8 * N))
R = array.array("d", bytes(8 * N))
TAU = 2 * math.pi
random.seed(7)

def hz(m):
    return 440.0 * 2 ** ((m - 69) / 12)

def add(t0, samples_fn, dur, pan=0.0, gain=1.0):
    i0 = max(0, int(t0 * SR)); i1 = min(N, int((t0 + dur) * SR))
    gl = gain * math.cos((pan + 1) * math.pi / 4); gr = gain * math.sin((pan + 1) * math.pi / 4)
    for i in range(i0, i1):
        v = samples_fn((i - t0 * SR) / SR)
        L[i] += v * gl; R[i] += v * gr

def pad_tone(f, t0, t1, amp, pan):
    att, rel = 1.4, 1.8
    dur = t1 - t0 + rel
    w1, w2, w3 = TAU * f, TAU * f * 1.0035, TAU * f * 2
    def fn(t):
        e = min(1.0, t / att); e = e * e * (3 - 2 * e)
        if t > t1 - t0:
            r = 1 - (t - (t1 - t0)) / rel; e *= max(0.0, r) ** 2
        trem = 1 + 0.08 * math.sin(TAU * 0.23 * t + f)
        return amp * e * trem * (math.sin(w1 * t) + 0.6 * math.sin(w2 * t) + 0.12 * math.sin(w3 * t))
    add(t0, fn, dur, pan)

def pluck(m, t0, amp, pan):
    f = hz(m)
    def fn(t):
        a = min(1.0, t / 0.004)
        s = 0.0
        for k in (1, 2, 3, 4):
            s += math.sin(TAU * f * k * t) * math.exp(-t * (1.3 + 1.1 * k)) / (k ** 1.6)
        return amp * a * s
    add(t0, fn, 3.2, pan)

def boom(t0, amp):
    ph = [0.0]
    def fn(t):
        f = 28 + 42 * math.exp(-t * 3.0)
        ph[0] += TAU * f / SR
        return amp * math.sin(ph[0]) * math.exp(-t * 1.5) * min(1, t / 0.006)
    add(t0, fn, 3.0, 0.0)
    lp = [0.0]
    def nz(t):
        lp[0] += 0.08 * (random.uniform(-1, 1) - lp[0])
        return amp * 1.8 * lp[0] * math.exp(-t * 7)
    add(t0, nz, 0.8, 0.0)

def swell(t_hit, length, amp):
    lp = [0.0]
    def fn(t):
        x = t / length
        c = 0.01 + 0.25 * x * x
        lp[0] += c * (random.uniform(-1, 1) - lp[0])
        return amp * (x ** 2.5) * lp[0]
    add(t_hit - length, fn, length, 0.0)

# chord schedule: (start, end, pad notes, bass)
D, B, G, A, E = 50, 47, 43, 45, 40
q = HERO / 4
h = (COLL - HERO) / 3
c = (END - COLL) / 2
B1, B2, B3 = q, 2 * q, 3 * q
H1, H2 = HERO + h, HERO + 2 * h
C1 = COLL + c
chords = [
    (0.0, B1, [50, 54, 57, 61], 38),             # Dmaj7
    (B1, B2, [47, 50, 54, 57], 35),              # Bm7
    (B2, B3, [43, 47, 50, 54], 31),              # Gmaj7
    (B3, HERO, [45, 50, 52, 57], 33),            # Asus4
    (HERO, H1, [50, 57, 64, 66], 38),            # Dadd9 bright
    (H1, H2, [47, 54, 57, 62], 35),              # Bm7
    (H2, COLL, [43, 50, 54, 59], 31),            # Gmaj7
    (COLL, C1, [52, 55, 59, 62, 66], 28),        # Em9
    (C1, END, [45, 50, 52, 57], 33),             # Asus4
    (END, TOTAL, [50, 54, 57, 61, 64], 38),      # Dmaj9 final
]
for idx, (t0, t1, notes, bass) in enumerate(chords):
    for j, m in enumerate(notes):
        pad_tone(hz(m), t0, t1, 0.030, -0.5 + j / max(1, len(notes) - 1))
    pad_tone(hz(bass), t0, t1, 0.040, 0.0)

# piano arpeggios (upper octave chord tones)
def arp(t0, t1, notes, step, amp, start_pan=-0.35):
    seq = [n + 12 for n in notes] + [notes[1] + 24]
    t, k = t0, 0
    while t < t1 - 0.05:
        pluck(seq[k % len(seq)], t + random.uniform(-0.015, 0.015), amp * random.uniform(0.8, 1.0),
              start_pan if k % 2 == 0 else -start_pan)
        t += step; k += 1

arp(1.0, B1, chords[0][2], 1.5, 0.11)
arp(B1, B2, chords[1][2], 1.0, 0.11)
arp(B2, B3, chords[2][2], 1.0, 0.12)
arp(B3, HERO - 0.9, chords[3][2], 0.75, 0.12)
arp(HERO, H1, chords[4][2], 0.5, 0.13)
arp(H1, H2, chords[5][2], 0.5, 0.12)
arp(H2, COLL - 0.3, chords[6][2], 0.5, 0.11)
arp(COLL + 0.1, C1, chords[7][2], 0.75, 0.12)
arp(C1, END - 0.5, chords[8][2], 0.75, 0.11)
for m, dt in ((74, 0.0), (69, 0.9), (78, 1.8)):   # final bell-like notes
    pluck(m, END + dt, 0.14, -0.2 + 0.2 * (dt > 0))

swell(HERO, 2.0, 0.55)
boom(HERO, 0.55)
if HAS_COLL:
    boom(COLL, 0.30)
boom(END, 0.38)

# master fade-out and write 16-bit
peak = max(max(abs(x) for x in L), max(abs(x) for x in R)) or 1
g = 0.85 / peak
fade0 = TOTAL - 3.0
out = array.array("h", bytes(4 * N))
for i in range(N):
    t = i / SR
    f = 1.0 if t < fade0 else max(0.0, 1 - (t - fade0) / 3.0) ** 1.5
    out[2 * i] = int(max(-1, min(1, L[i] * g * f)) * 32767)
    out[2 * i + 1] = int(max(-1, min(1, R[i] * g * f)) * 32767)
w = wave.open(sys.argv[2], "wb"); w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR)
w.writeframes(out.tobytes()); w.close()
print("music ok", TOTAL)
