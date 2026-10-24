#!/usr/bin/env python3
"""camera.py — turn a capture's frames + camera cues into a framed, zooming 1080p60 clip.

    python3 camera.py out/<scene>        (cwd = the build dir, holding theme.json)

The camera follows the Director's cues with a critically damped spring (so it eases in
and out and never snaps), and the page sits as a rounded "window" on a backdrop. A scene
captured with `frame: false` (a title card) passes through full-bleed with no camera.
"""
import json, os, subprocess, sys, math
import numpy as np
from PIL import Image, ImageDraw, ImageFilter

d = sys.argv[1]
meta = json.load(open(f"{d}/cues.json"))
theme = json.load(open("theme.json"))
NO_FRAME = not meta.get("frame", True)
NO_ZOOM = NO_FRAME

def rgb(h):
    h = h.lstrip("#")
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))
SW, SH = meta["W"] * meta["DSF"], meta["H"] * meta["DSF"]   # source pixels
S = meta["DSF"]
FPS = 60
OW, OH = int(os.environ.get("PROMO_OW", 1920)), int(os.environ.get("PROMO_OH", 1080))
SAFE_BOTTOM = float(os.environ.get("PROMO_SAFE", "0.048 0.048 0").split()[1])
if NO_FRAME:
    WX, WY, WW, WH = 0, 0, OW, OH
else:
    # the window: the page's own aspect, as large as fits inside the safe area (PROMO_SAFE =
    # "top bottom side" fractions a platform's overlays cover), leaving room under it for a
    # caption to straddle its bottom edge
    top, bottom, side = map(float, os.environ.get("PROMO_SAFE", "0.048 0.048 0").split())
    side = max(side, 0.083 if OW > OH else 0.055)
    y0, y1 = OH * top, OH * (1 - bottom) - 40
    WW = int(OW * (1 - 2 * side)); WH = int(WW * meta["H"] / meta["W"])
    if WH > y1 - y0:
        WH = int(y1 - y0); WW = int(WH * meta["W"] / meta["H"])
    WW -= WW % 2; WH -= WH % 2
    WX, WY = (OW - WW) // 2, int(y0 + (y1 - y0 - WH) / 2)
RADIUS = 18

# ---- backdrop: the theme's page colour with a soft glow of each accent ------------------
def backdrop():
    y, x = np.mgrid[0:OH, 0:OW].astype(np.float32)
    base = np.zeros((OH, OW, 3), np.float32)
    base[:] = rgb(theme["bg"])
    def glow(cx, cy, r, col, k):
        g = np.exp(-(((x - cx) ** 2 + (y - cy) ** 2) / (2 * r * r)))[..., None]
        return g * np.array(col, np.float32) * k
    base += glow(OW * 0.12, OH * 0.05, 520, rgb(theme["accent"]), 0.33)
    base += glow(OW * 0.92, OH * 0.98, 620, rgb(theme.get("accent2", theme["accent"])), 0.30)
    img = Image.fromarray(np.clip(base, 0, 255).astype(np.uint8))
    if not NO_FRAME:
        sh = Image.new("L", (OW, OH), 0)
        ImageDraw.Draw(sh).rounded_rectangle((WX, WY + 22, WX + WW, WY + WH + 22), RADIUS, fill=170)
        sh = sh.filter(ImageFilter.GaussianBlur(34))
        img = Image.composite(Image.new("RGB", (OW, OH), (0, 0, 0)), img, sh)
    return img

BG = backdrop()
MASK = Image.new("L", (WW, WH), 0)
ImageDraw.Draw(MASK).rounded_rectangle((0, 0, WW - 1, WH - 1), RADIUS, fill=255)

# ---- camera path ------------------------------------------------------------------------
cues = meta["cues"]
N = int(math.ceil(meta["duration"] * FPS))

def visible(z):
    """Source-pixel size of the crop at zoom z (same arithmetic as the render loop)."""
    cw = SW / z; ch = cw * WH / WW
    if ch > SH / z:
        ch = SH / z; cw = ch * WW / WH
    return min(cw, SW), min(ch, SH)

def aim(r, want, pt):
    """Zoom and centre for a focus cue. Never tighter than keeps the whole target in frame
    (zooming a wide row into its middle crops the label and the value, the parts people
    read), and the cursor's resting point is always kept inside the frame."""
    PAD = 1.12
    z = want
    while z > 1.0:
        vw, vh = visible(z)
        if r["width"] * S * PAD <= vw and r["height"] * S * PAD <= vh:
            break
        z -= 0.02
    z = max(1.0, z)
    vw, vh = visible(z)
    cx, cy = (r["x"] + r["width"] / 2) * S, (r["y"] + r["height"] / 2) * S
    if pt:                                       # nudge so the cursor sits within the inner 80%
        px, py = pt["x"] * S, pt["y"] * S
        cx = min(max(cx, px - vw * 0.4), px + vw * 0.4)
        cy = min(max(cy, py - vh * 0.4), py + vh * 0.4)
    return z, cx, cy

def target_at(t):
    z, cx, cy = 1.0, SW / 2, SH / 2
    for c in cues:
        if c["t"] > t + 0.15:          # lead slightly: start moving as the cursor sets off
            break
        if c["kind"] == "focus" and c["rect"] and c["zoom"] > 1:
            z, cx, cy = aim(c["rect"], c["zoom"], c.get("pt"))
        elif c["kind"] in ("wide", "scroll") or (c["kind"] == "focus" and c["zoom"] <= 1):
            z, cx, cy = 1.0, SW / 2, SH / 2
    return z, cx, cy

def springs():
    # critically damped spring, stepped per frame; omega sets how lazy the camera is
    omega = 5.2
    z, x, y = 1.0, SW / 2, SH / 2
    vz = vx = vy = 0.0
    dt = 1 / FPS
    out = []
    for i in range(N):
        tz, tx, ty = (1.0, SW / 2, SH / 2) if NO_ZOOM else target_at(i / FPS)
        for _ in range(4):
            h = dt / 4
            for (p, v, tgt, name) in ((z, vz, tz, "z"), (x, vx, tx, "x"), (y, vy, ty, "y")):
                a = -2 * omega * v - omega * omega * (p - tgt)
                v += a * h; p += v * h
                if name == "z": z, vz = p, v
                elif name == "x": x, vx = p, v
                else: y, vy = p, v
        out.append((z, x, y))
    return out

path = springs()

# ---- captions: pre-rendered pills, faded and lifted in over the window --------------------
CAPS = []
caps = [x for x in cues if x["kind"] == "caption"]
for k, c in enumerate(caps):
    p = f"{d}/cap_{k}.png"
    # a new caption ends the previous one, so two pills never stack in the same spot
    end = min(c["t"] + c["dur"], caps[k + 1]["t"]) if k + 1 < len(caps) else c["t"] + c["dur"]
    if os.path.exists(p):
        CAPS.append((c["t"], end - c["t"], Image.open(p).convert("RGBA")))

# ---- spotlight: dim all but the target while the camera rests on a `spot` cue -------------
FOCUS = [c for c in cues if c["kind"] in ("focus", "wide", "scroll")]

def spot_alpha(t):
    for j, c in enumerate(FOCUS):
        if not c.get("spot"):
            continue
        start = c["t"] + 0.45                     # after the cursor has arrived
        end = FOCUS[j + 1]["t"] if j + 1 < len(FOCUS) else meta["duration"]
        if start <= t <= end:
            return (min(1.0, (t - start) / 0.3, max(0.0, (end - t) / 0.25)), c["rect"])
    return None

def draw_captions(frame, t):
    for (ct, dur, img) in CAPS:
        if not (ct <= t <= ct + dur):
            continue
        a = min(1.0, (t - ct) / 0.28, (ct + dur - t) / 0.28)
        e = 1 - (1 - a) ** 3
        lift = int(18 * (1 - e))
        im = img.copy()
        im.putalpha(im.getchannel("A").point(lambda v: int(v * e)))
        x = (OW - im.width) // 2
        y = WY + WH - im.height // 2 + lift                # straddles the window's bottom edge
        if NO_FRAME:                                       # full bleed has no edge to straddle: sit above the safe area
            y = int(OH * (1 - SAFE_BOTTOM)) - im.height - int(OH * 0.04) + lift
        frame.alpha_composite(im, (x, y)) if frame.mode == "RGBA" else frame.paste(im, (x, y), im)

# ---- render -------------------------------------------------------------------------------
dec = subprocess.Popen(
    ["ffmpeg", "-loglevel", "error", "-f", "concat", "-safe", "0", "-i", f"{d}/frames/list.txt",
     "-vf", f"fps={FPS},scale={SW}:{SH}", "-f", "rawvideo", "-pix_fmt", "rgb24", "-"],
    stdout=subprocess.PIPE)
enc = subprocess.Popen(
    ["ffmpeg", "-loglevel", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{OW}x{OH}",
     "-r", str(FPS), "-i", "-", "-c:v", "libx264", "-crf", "15", "-preset", "medium",
     "-pix_fmt", "yuv420p", f"{d}/framed.mp4"],
    stdin=subprocess.PIPE)
fsize = SW * SH * 3
aspect = WW / WH
i = 0
while True:
    buf = dec.stdout.read(fsize)
    if len(buf) < fsize:
        break
    z, cx, cy = path[min(i, len(path) - 1)]
    cw = SW / z; ch = cw / aspect
    if ch > SH / z:                      # source aspect differs slightly from the window's
        ch = SH / z; cw = ch * aspect
    cw, ch = min(cw, SW), min(ch, SH)
    x0 = min(max(cx - cw / 2, 0), SW - cw); y0 = min(max(cy - ch / 2, 0), SH - ch)
    src = Image.frombuffer("RGB", (SW, SH), buf, "raw", "RGB", 0, 1)
    win = src.resize((WW, WH), Image.LANCZOS, box=(x0, y0, x0 + cw, y0 + ch))
    a = spot_alpha(i / FPS)
    if a:
        r = a[1]; k = WW / cw
        pad = 10
        bx = ((r["x"] * S - x0) * k - pad, (r["y"] * S - y0) * k - pad,
              ((r["x"] + r["width"]) * S - x0) * k + pad, ((r["y"] + r["height"]) * S - y0) * k + pad)
        m = Image.new("L", (WW, WH), int(150 * a[0]))
        ImageDraw.Draw(m).rounded_rectangle(bx, 12, fill=0)
        win = Image.composite(Image.new("RGB", (WW, WH), (4, 6, 10)), win, m.filter(ImageFilter.GaussianBlur(6)))
    frame = BG.copy()
    frame.paste(win, (WX, WY), MASK)
    draw_captions(frame, i / FPS)
    enc.stdin.write(frame.tobytes())
    i += 1
enc.stdin.close(); enc.wait(); dec.wait()
print(f"{d}/framed.mp4: {i} frames")
