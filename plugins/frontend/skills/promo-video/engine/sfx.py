#!/usr/bin/env python3
"""sfx.py — build the sound track for an assembled cut.

    python3 sfx.py out.wav XFADE scene1 transition1 scene2 ...     (cwd = the build dir)

Every effect is tied to something visibly moving and starts when the motion starts; a
sound that matches nothing on screen reads as a mistake (a "pop" under a fade, a boom
under a caption). So:
  click       every real click
  whoosh      every scroll that travels, as long as the scroll; every sliding transition
              from its first frame. Fades get nothing: there is no motion to hear.
  pop         a card's `pops` (the logo popping in)
  accent      a `d.accent()` cue, only if the spec names a sample (no default: a stock
              "impact" rarely matches what is on screen)
plus the narration (`d.say`) and a music bed that ducks under it. Samples and music come
from the video spec (PROMO_SPEC; paths relative to PROMO_DIR, or absolute/~):
    "sfx": {"click": "...", "whoosh": "...", "pop": "...", "accent": "..."},
    "music": "...", "music_start": 0, "music_gain": 0.45
Unnamed click/whoosh/pop are synthesized. build.sh loudness-normalizes the final mix.
"""
import json, os, subprocess, sys, wave
import numpy as np

SR = 48000
out, XF, cut = sys.argv[1], float(sys.argv[2]), sys.argv[3:]
segs, trans = cut[0::2], cut[1::2]
spec = json.load(open(os.environ["PROMO_SPEC"])) if os.environ.get("PROMO_SPEC") else {}
base = os.environ.get("PROMO_DIR", ".")
FADES = ("fade", "fadeblack", "fadewhite", "fadegrays", "dissolve")

def resolve(p):
    p = os.path.expanduser(p)
    return p if os.path.isabs(p) else os.path.join(base, p)

def dur(p):
    return float(subprocess.check_output(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", p]))

def load(path, seconds=None, start=0.0):
    cmd = ["ffmpeg", "-loglevel", "error", "-ss", str(start), "-i", path]
    if seconds:
        cmd += ["-t", str(seconds)]
    raw = subprocess.check_output(cmd + ["-f", "f32le", "-ac", "1", "-ar", str(SR), "-"])
    x = np.frombuffer(raw, np.float32).astype(np.float64)
    if not len(x):
        raise SystemExit(f"sfx: {path} decoded to nothing")
    return x / (np.max(np.abs(x)) or 1)                 # every sample at the same peak

def fit(sig, seconds):
    """Trim a sample to `seconds` with a short fade, so a whoosh lasts as long as its move."""
    n = min(len(sig), int(seconds * SR))
    s = sig[:n].copy(); f = min(n, int(0.12 * SR))
    s[-f:] *= np.linspace(1, 0, f)
    return s

# ---- synthesized fallbacks ----------------------------------------------------------------
rng = np.random.default_rng(7)

def tick():
    n = int(0.05 * SR); t = np.arange(n) / SR
    return np.sin(2 * np.pi * 2300 * t) * np.exp(-t * 180) + rng.standard_normal(n) * np.exp(-t * 400) * 0.3

def whoosh(length=1.2):
    n = int(length * SR); x = rng.standard_normal(n)
    out = np.zeros(n); y = 0.0
    shape = np.sin(np.linspace(0, np.pi, n)) ** 1.6
    for i in range(n):                                   # a lowpass that opens mid-swell
        y += (0.02 + 0.25 * shape[i]) * (x[i] - y); out[i] = y
    return out * shape / (np.max(np.abs(out * shape)) or 1)

def pop():
    n = int(0.12 * SR); t = np.arange(n) / SR
    return np.sin(2 * np.pi * (500 + 900 * np.exp(-t * 40)) * t) * np.exp(-t * 35)

kit = {k: resolve(v) for k, v in spec.get("sfx", {}).items()}
CLICK = load(kit["click"]) if "click" in kit else tick()
WHOOSH = load(kit["whoosh"]) if "whoosh" in kit else whoosh()
POP = load(kit["pop"]) if "pop" in kit else pop()
ACCENT = load(kit["accent"]) if "accent" in kit else None
LEVEL = {"click": 0.25, "whoosh": 0.4, "pop": 0.35, "accent": 0.5}

# ---- place everything on the cut's timeline ----------------------------------------------
durs = [dur(f"out/{s}/framed.mp4") for s in segs]
total = sum(durs) - XF * (len(segs) - 1)
fx = np.zeros(int(total * SR))                           # exactly the picture: the music's fade must end with it
vo = np.zeros_like(fx)
speaking = np.zeros_like(fx)                             # 1 while a line is being spoken

def add(track, sig, at, gain):
    i = int(max(0, at) * SR); j = min(len(track), i + len(sig))
    if j > i:
        track[i:j] += sig[: j - i] * gain

off = 0.0
for k, (s, d) in enumerate(zip(segs, durs)):
    for c in json.load(open(f"out/{s}/cues.json"))["cues"]:
        at = off + c["t"]
        if c["kind"] == "say":
            v = load(os.path.abspath(c["file"]))          # vo/ lives in the build dir, not PROMO_DIR
            add(vo, v, at, 0.95)
            speaking[int(at * SR): int(at * SR) + len(v)] = 1.0
        elif c["kind"] == "click":
            add(fx, CLICK, at + 0.07, LEVEL["click"])
        elif c["kind"] == "scroll" and c.get("dist", 0) > 120:   # a nudge is not a move
            add(fx, fit(WHOOSH, c.get("dur", 1.0) + 0.25), at, LEVEL["whoosh"])
        elif c["kind"] == "pop":
            add(fx, POP, at, LEVEL["pop"])
        elif c["kind"] == "accent" and ACCENT is not None:
            add(fx, ACCENT, at, LEVEL["accent"])
    if k < len(trans) and trans[k] not in FADES:          # slides move; fades don't
        add(fx, fit(WHOOSH, XF + 0.3), off + d - XF, LEVEL["whoosh"])
    off += d - XF

voiced = speaking.any()
if voiced:
    fx *= 0.7                                            # effects sit under a voice, not on it
mix = fx + vo
if spec.get("music"):
    m = load(resolve(spec["music"]), total, spec.get("music_start", 0))
    m = m[: len(fx)] * spec.get("music_gain", 0.45)
    fi, fo = int(0.4 * SR), int(1.8 * SR)
    m[:fi] *= np.linspace(0, 1, fi); m[-fo:] *= np.linspace(1, 0, fo)
    if voiced:
        # duck the music ~10 dB under speech, easing in and out
        k1 = int(0.15 * SR); k2 = int(0.4 * SR)
        duck = np.convolve(speaking, np.ones(k1) / k1, mode="same")
        duck = np.clip(np.convolve(duck, np.ones(k2) / k2, mode="same") * 3, 0, 1)
        m = m * (1 - 0.68 * duck[: len(m)])
    mix = mix.copy(); mix[: len(m)] += m

mix = mix / (np.max(np.abs(mix)) or 1) * 0.89
with wave.open(out, "wb") as w:
    w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR)
    w.writeframes((mix * 32767).astype(np.int16).tobytes())
print(f"{out}: {total:.1f}s" + (f", music {os.path.basename(spec['music'])}" if spec.get("music") else "")
      + (", voiced" if voiced else ""))
