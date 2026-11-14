#!/usr/bin/env python3
"""vo.py — synthesize every narration line in the scenes before filming.

    python3 vo.py <scene>...        (cwd = the build dir; voice settings from PROMO_SPEC)

Lines are the string literals in `d.say("...")` calls, so keep them literal. Each is
synthesized once per voice and cached in vo/, and vo/index.json maps text -> {file, dur},
which the Director reads during capture so a scene's pacing follows its narration.

Voice settings, from the video spec:
    "voice": {"engine": "kokoro", "id": "am_michael", "speed": 1.0}
    "voice": {"engine": "elevenlabs", "id": "<voice id>", "model": "eleven_multilingual_v2",
              "stability": 0.4, "style": 0.3}
The ElevenLabs key is read from ~/.config/promo-video/elevenlabs.key and never printed.

    "take": "one"   (ElevenLabs only) voice the whole script in ONE request and cut it into
                    lines, instead of one request per line. Separately generated lines each come
                    out a little different, which an owner heard as "recorded on different days".
                    Lines are joined in scene order (build.sh passes the cut order), cut at the
                    midpoint of each gap using the character alignment the API returns, and
                    written to the same per-line cache paths. Any line missing re-voices all of
                    them, since a line from another take would bring the mismatch back.
"""
import base64, hashlib, json, os, re, subprocess, sys, urllib.request

spec = json.load(open(os.environ["PROMO_SPEC"])) if os.environ.get("PROMO_SPEC") else {}
voice = spec.get("voice") or {"engine": "kokoro", "id": "am_michael", "speed": 1.0}
TTS = os.path.expanduser("~/.local/share/promo-video/tts")
os.makedirs("vo", exist_ok=True)

# d.say("...") in scenes, and card({ voice: "..." }) in title cards
SAY = re.compile(r"""(?:\bd\.say\(\s*|\bvoice:\s*)(["'`])((?:\\.|(?!\1).)*)\1""", re.S)
lines = []
for s in sys.argv[1:]:
    for m in SAY.finditer(open(f"scenes/{s}.mjs").read()):
        text = m.group(2).encode().decode("unicode_escape") if "\\" in m.group(2) else m.group(2)
        if text not in lines:
            lines.append(text)

def duration(path):
    return float(subprocess.check_output(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", path]))

def kokoro(text, out):
    text = re.sub(r"\[[^\]]*\]\s*", "", text)             # Kokoro would read delivery tags aloud
    subprocess.run([f"{TTS}/venv/bin/python", f"{TTS}/say.py", "--voice", voice["id"],
                    "--speed", str(voice.get("speed", 1.0)), "--out", out, text], check=True, stdout=subprocess.DEVNULL)

def elevenlabs(text, out):
    key = open(os.path.expanduser("~/.config/promo-video/elevenlabs.key")).read().strip()
    body = {"text": text, "model_id": voice.get("model", "eleven_multilingual_v2"),
            "voice_settings": {k: voice[k] for k in ("stability", "similarity_boost", "style", "speed") if k in voice}}
    req = urllib.request.Request(
        f"https://api.elevenlabs.io/v1/text-to-speech/{voice['id']}?output_format=mp3_44100_128",
        data=json.dumps(body).encode(), headers={"xi-api-key": key, "Content-Type": "application/json"})
    mp3 = out[:-4] + ".mp3"
    with urllib.request.urlopen(req, timeout=120) as r, open(mp3, "wb") as f:
        f.write(r.read())
    subprocess.run(["ffmpeg", "-loglevel", "error", "-y", "-i", mp3, "-ac", "1", out], check=True)
    os.remove(mp3)

def trim(path):
    """Cut leading/trailing silence. A take can carry seconds of it (one hook line ended in
    2.2s of dead air), and the scene waits out the whole clip. Idempotent, so cached lines
    are re-trimmed harmlessly on every run."""
    tmp = path[:-4] + ".trim.wav"
    edge = "silenceremove=start_periods=1:start_threshold=-45dB:start_silence=0.08"
    subprocess.run(["ffmpeg", "-loglevel", "error", "-y", "-i", path, "-af",
                    f"{edge},areverse,{edge},areverse", tmp], check=True)
    os.replace(tmp, path)

def split_take(texts, resp, paths, fade=0.02):
    """Cut one with-timestamps response into per-line wavs at the midpoints between lines."""
    a = resp["alignment"]
    joined = "\n\n".join(texts)
    if "".join(a["characters"]) != joined:
        raise SystemExit("vo: alignment text does not match the script; refusing to guess cut points")
    spans, at = [], 0
    for t in texts:
        spans.append((a["character_start_times_seconds"][at], a["character_end_times_seconds"][at + len(t) - 1]))
        at += len(t) + 2
    full = "vo/take.wav"
    mp3 = "vo/take.mp3"
    open(mp3, "wb").write(base64.b64decode(resp["audio_base64"]))
    subprocess.run(["ffmpeg", "-loglevel", "error", "-y", "-i", mp3, "-ac", "1", full], check=True)
    os.remove(mp3)
    end = duration(full)
    cuts = [0.0] + [(spans[i][1] + spans[i + 1][0]) / 2 for i in range(len(spans) - 1)] + [end]
    for i, path in enumerate(paths):
        s, e = cuts[i], cuts[i + 1]
        # Seek on the INPUT. With -ss after -i, the filter sees the take's own timestamps, so the
        # fade-out (st= is clip-relative) silences everything past the first ~st seconds of the
        # take: on ffmpeg 6.1 every line after the second came out as silence of the right length.
        subprocess.run(["ffmpeg", "-loglevel", "error", "-y", "-ss", f"{s:.3f}", "-to", f"{e:.3f}", "-i", full,
                        "-af", f"afade=t=in:d={fade},afade=t=out:st={max(e - s - fade, 0):.3f}:d={fade}", path],
                       check=True)
        # A silent clip has a plausible duration, so only its level can show the cut failed.
        vd = subprocess.run(["ffmpeg", "-hide_banner", "-i", path, "-af", "volumedetect", "-f", "null", "-"],
                            capture_output=True, text=True).stderr
        mean = re.search(r"mean_volume: (-?[\d.]+) dB", vd)
        if not mean or float(mean.group(1)) < -60:
            raise SystemExit(f"vo: line {i + 1} cut from the take is silent ({texts[i][:50]!r})")

def elevenlabs_take(texts, paths):
    key = open(os.path.expanduser("~/.config/promo-video/elevenlabs.key")).read().strip()
    body = {"text": "\n\n".join(texts), "model_id": voice.get("model", "eleven_multilingual_v2"),
            "voice_settings": {k: voice[k] for k in ("stability", "similarity_boost", "style", "speed") if k in voice}}
    req = urllib.request.Request(
        f"https://api.elevenlabs.io/v1/text-to-speech/{voice['id']}/with-timestamps?output_format=mp3_44100_128",
        data=json.dumps(body).encode(), headers={"xi-api-key": key, "Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=300) as r:
        split_take(texts, json.load(r), paths)

ENGINES = {"kokoro": kokoro, "elevenlabs": elevenlabs}
index = {}
keys = [hashlib.sha1(json.dumps([voice, t], sort_keys=True).encode()).hexdigest()[:16] for t in lines]
if voice.get("take") == "one":
    if voice["engine"] != "elevenlabs":
        raise SystemExit("vo: \"take\": \"one\" needs the elevenlabs engine (it relies on its alignment)")
    if not all(os.path.exists(f"vo/{k}.wav") for k in keys):
        elevenlabs_take(lines, [f"vo/{k}.wav" for k in keys])
for text, key in zip(lines, keys):
    path = f"vo/{key}.wav"
    if not os.path.exists(path):
        ENGINES[voice["engine"]](text, path)
    trim(path)
    index[text] = {"file": path, "dur": duration(path)}
json.dump(index, open("vo/index.json", "w"), indent=1)
print(f"vo: {len(lines)} lines, {sum(v['dur'] for v in index.values()):.1f}s, {voice['engine']}:{voice['id']}")
