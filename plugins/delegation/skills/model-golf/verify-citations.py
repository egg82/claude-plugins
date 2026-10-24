#!/usr/bin/env python3
"""Verify the citations in bug-hunt answers against the real source files.

The failure mode that matters when judging a cheap model is a confident finding at a
file:line that does not say what the agent claims. Prose plausibility can't catch that;
reading the cited line can. This resolves each citation and prints the actual source so
the claim is judged against the code rather than against how convincing it sounds.
Resolving a citation proves the pointer is real, not that the claim is true — read the
printed source line and judge the claim against it.

TEMPLATE — carries constants from the run it came from. Replace before reuse:
  $GOLF_REPO   repo root the citations are resolved against — REQUIRED, no default.
  $GOLF_PKG    package subpath under it — REQUIRED, no default. The example shape is a
               Java package; swap the CITE regex too for another language.
  HUNT_FP      the prompt substring identifying which agents ran the hunt.
The two paths have no fallback on purpose: a wrong root resolves nothing, and "every
citation is fabricated" is exactly the verdict this script exists to reach honestly.
"""
import json, glob, os, re, collections

ROOT = os.path.expanduser("~/.claude/projects")


def _required_env(name, hint):
    v = os.environ.get(name)
    if not v:
        raise SystemExit(f"set ${name} — {hint}")
    return os.path.expanduser(v)


REPO = _required_env("GOLF_REPO", "the repo root the cited files live under")
PKG = os.environ.get("GOLF_PKG")
if not PKG or PKG.startswith("<"):
    raise SystemExit("set $GOLF_PKG — the package subpath under $GOLF_REPO, "
                     "e.g. lib/src/main/java/com/example/pkg")
if not os.path.isdir(REPO):
    raise SystemExit(f"$GOLF_REPO is not a directory: {REPO} — every citation would print "
                     "FILE NOT FOUND, which is indistinguishable from a fabricating model")
if not os.path.isdir(os.path.join(REPO, PKG)):
    raise SystemExit(f"$GOLF_REPO/$GOLF_PKG is not a directory: {os.path.join(REPO, PKG)}")

# Distinctive substring of the bug-hunt prompt — replace with yours.
HUNT_FP = os.environ.get("GOLF_HUNT_FP", "<distinctive substring of your bug-hunt prompt>")

CITE = re.compile(r"([A-Za-z0-9_/.\-]*[A-Za-z0-9_]+\.java)\s*[:#]\s*(\d+)")


def resolve(fname):
    """Map a possibly-partial path to a real file under the package."""
    base = os.path.basename(fname)
    hits = glob.glob(os.path.join(REPO, PKG, "**", base), recursive=True)
    if not hits:
        hits = glob.glob(os.path.join(REPO, "**", base), recursive=True)
    return hits[0] if hits else None


def line_at(path, n):
    try:
        with open(path, errors="replace") as f:
            lines = f.readlines()
    except OSError:
        return None, 0
    if 1 <= n <= len(lines):
        return lines[n - 1].rstrip(), len(lines)
    return None, len(lines)


def bughunt_agents():
    """agentId -> model, for agents whose prompt was the BUGHUNT task."""
    out = {}
    for path in glob.glob(ROOT + "/**/*.jsonl", recursive=True):
        for line in open(path, errors="replace"):
            if PKG.split("/main/java/")[-1] not in line:
                continue
            try:
                d = json.loads(line)
            except Exception:
                continue
            t = d.get("toolUseResult")
            if isinstance(t, dict) and t.get("agentId") and HUNT_FP in (t.get("prompt") or ""):
                out[t["agentId"]] = None
    for aid in list(out):
        meta = glob.glob(f"{ROOT}/*/*/subagents/agent-{aid}.meta.json")
        if meta:
            try:
                out[aid] = json.load(open(meta[0])).get("model") or "inherited"
            except Exception:
                pass
    return out


def final_text(aid):
    hits = glob.glob(f"{ROOT}/*/*/subagents/agent-{aid}.jsonl")
    if not hits:
        return ""
    final = ""
    for line in open(hits[0], errors="replace"):
        if '"assistant"' not in line:
            continue
        try:
            d = json.loads(line)
        except Exception:
            continue
        m = d.get("message") or {}
        if m.get("role") != "assistant":
            continue
        txt = "".join(b.get("text", "") for b in (m.get("content") or [])
                      if isinstance(b, dict) and b.get("type") == "text")
        if txt.strip():
            final = txt
    return final


agents = bughunt_agents()
if not agents:
    # SystemExit with a MESSAGE exits 1; a bare `raise SystemExit` exits 0, which reports
    # "citations verified" to any wrapper gating on the status while nothing was checked. The
    # printed line was honest and the exit status was not, and automation only reads one of them.
    # Same falsely-clean shape grade.py refuses below.
    raise SystemExit("no BUGHUNT agents found yet — runner still in flight; nothing was verified")

summary = collections.defaultdict(lambda: {"cites": 0, "resolved": 0, "in_range": 0})
for aid, model in sorted(agents.items(), key=lambda kv: str(kv[1])):
    text = final_text(aid)
    cites = CITE.findall(text)
    print(f"\n=== {model or '?'}  agent {aid[:12]}  ({len(cites)} citations) ===")
    seen = set()
    for fname, num in cites:
        key = (os.path.basename(fname), num)
        if key in seen:
            continue
        seen.add(key)
        summary[model]["cites"] += 1
        path = resolve(fname)
        if not path:
            print(f"  ✗ {fname}:{num}  FILE NOT FOUND")
            continue
        summary[model]["resolved"] += 1
        src, total = line_at(path, int(num))
        if src is None:
            print(f"  ✗ {os.path.basename(path)}:{num}  OUT OF RANGE (file has {total} lines)")
            continue
        summary[model]["in_range"] += 1
        print(f"  · {os.path.basename(path)}:{num}  ->  {src.strip()[:96]}")

print("\n=== citation integrity by model ===")
print(f"{'model':14} {'cites':>6} {'file ok':>8} {'line ok':>8}")
for m, s in summary.items():
    print(f"{str(m):14} {s['cites']:>6} {s['resolved']:>8} {s['in_range']:>8}")
