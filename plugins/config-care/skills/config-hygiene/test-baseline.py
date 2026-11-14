"""Cases for the growth ratchet's baseline source (read_baseline, and check_prefs on top of it).

The log record wins over baseline.txt; a missing baseline is "unwatched" and an unreadable one is
"INERT", never clean. Run: python3 test-baseline.py
"""
import contextlib
import importlib.util
import io
import json
import pathlib
import sys
import tempfile

spec = importlib.util.spec_from_file_location(
    "hyg", str(pathlib.Path(__file__).resolve().parent / "hygiene.py"))
assert spec and spec.loader
h = importlib.util.module_from_spec(spec)
spec.loader.exec_module(h)

BIG = "x" * 10000


def home(log=None, txt=None, pref_bytes=10000):
    """A fake ~/.claude with one imported pref, plus the always-on-prune files given."""
    root = pathlib.Path(tempfile.mkdtemp())
    (root / "memory").mkdir()
    (root / "memory" / "p.md").write_text(("y" * pref_bytes) + "\n")
    (root / "CLAUDE.md").write_text("@~/.claude/memory/p.md\n".replace("~/.claude", str(root)))
    sk = root / "skills" / "always-on-prune"
    sk.mkdir(parents=True)
    if log is not None:
        (sk / "prune-log.jsonl").write_text(log)
    if txt is not None:
        (sk / "baseline.txt").write_text(txt)
    return root


def run(root):
    out = io.StringIO()
    with contextlib.redirect_stdout(out):
        h.check_prefs(root / "memory")
    return out.getvalue()


def rec(**kw):
    return json.dumps({"type": "baseline", **kw}) + "\n"


FAILS = []


def case(name, ok):
    print(("ok   " if ok else "FAIL ") + name)
    if not ok:
        FAILS.append(name)


# read_baseline
r = home(log=rec(bytes=100, roster=50))
case("log record read", h.read_baseline(r / "skills" / "always-on-prune") == (100, 50, "prune-log.jsonl"))
r = home(log=rec(bytes=100) + rec(bytes=200), txt="999\n999\n")
case("last log record wins over earlier record and baseline.txt",
     h.read_baseline(r / "skills" / "always-on-prune")[0] == 200)
r = home(log='{"type":"header"}\n{"date":"x"}\n', txt="300 # a\n400 # b\n")
case("log without a baseline record falls back to baseline.txt",
     h.read_baseline(r / "skills" / "always-on-prune") == (300, 400, "baseline.txt"))
r = home()
case("no source gives None", h.read_baseline(r / "skills" / "always-on-prune") is None)
for label, kw in (("string bytes", {"bytes": "12"}), ("missing bytes", {}), ("bool bytes", {"bytes": True})):
    r = home(log=json.dumps({"type": "baseline", **kw}) + "\n", txt="300\n400\n")
    try:
        h.read_baseline(r / "skills" / "always-on-prune")
        case(f"unreadable record raises, not falls back ({label})", False)
    except (ValueError, IndexError, TypeError, KeyError):
        case(f"unreadable record raises, not falls back ({label})", True)

# check_prefs, end to end. A control first: the ratchet must be able to fire.
out = run(home(log=rec(bytes=100, roster=10 ** 9), pref_bytes=10000))
case("growth past the log baseline is flagged", "pref bodies have grown" in out)
out = run(home(log=rec(bytes=100000, roster=10 ** 9)))
case("growth within the log baseline stays quiet", "have grown" not in out and "baseline" not in out)
out = run(home())
case("no baseline is flagged as unwatched", "growth is unwatched" in out)
out = run(home(txt="not a number\n"))
case("unparseable baseline.txt is flagged INERT", "INERT" in out)
out = run(home(log=rec(bytes="12")))
case("unparseable log record is flagged INERT", "INERT" in out)
out = run(home(log=rec(bytes=100000)))
case("log record with no roster says roster growth is unwatched", "no roster figure" in out)

sys.exit(1 if FAILS else 0)
