#!/usr/bin/env bash
# hook-version: 1
# Stop gate: this session wrote HTML a human will look at, and never looked at it.
#
# WHY THIS IS A HOOK AND NOT A MEMORY: it WAS a memory, whose whole content was "render it and look
# at it before calling it done, and note that podman gives you a browser on a host with no browser."
# The failure it addresses is *not knowing to look*, which is exactly the thing a resident sentence
# is bad at and a Stop hook is good at — the check belongs at the moment the work is about to be
# called done, not on every request for the whole session. The recipe it pointed at lives in the
# `headless-render` skill; this supplies the trigger the memory was paying resident rent for.
#
# WHAT COUNTS AS LOOKING: a `--screenshot` render, a `Read` of an image, or an obvious browser
# driver. Any one of them means the question was asked, and the hook stays quiet. It does NOT try to
# judge whether the screenshot was any good.
#
# WHAT IS EXCLUDED, so it does not nag on work no human will view: files under test/, tests/,
# fixture(s)/, __snapshots__/, node_modules/, .git/, and any path inside a scratch/tmp directory.
# A fixture is written to be parsed, not read, and a gate that fires on those gets switched off.
#
# FIRES ONCE PER SESSION, stamped. Exit 2 returns the nudge; exit 3 means the hook found not one
# structured message block in the transcript — the file is empty or its shape is no longer what this
# scan expects — and says so rather than passing silently, because a gate that cannot see is not a
# gate that found nothing. A session whose turns are all plain text is CLEAN, not inert: it has
# blocks, they are just never tool_use. Do not conflate those; the second is the common case and a
# gate that cries inert on it is a gate that gets switched off.
set -uo pipefail

payload=$(cat 2>/dev/null || true)
[ -n "$payload" ] || exit 0

HOOK_PAYLOAD="$payload" python3 - <<'PY'
import json, os, pathlib, re, sys

try:
    d = json.loads(os.environ["HOOK_PAYLOAD"])
except Exception:
    sys.exit(0)

tp = d.get("transcript_path") or ""
if not tp or not os.path.exists(tp):
    sys.exit(0)

SKIP = re.compile(r"(^|/)(tests?|fixtures?|__snapshots__|node_modules|\.git|scratchpad|tmp)(/|$)", re.I)
WRITERS = {"Write", "Edit", "MultiEdit", "NotebookEdit"}
LOOKED = re.compile(r"--screenshot|playwright|puppeteer|chromedriver|selenium", re.I)

# No substring pre-filter on the line before parsing it. Measured on the largest transcript in the
# store (87MB / 20k lines) a full parse is ~0.33s and the filter saved nothing — while making the
# health count below a count of *filter-passing* blocks rather than of blocks, which is what made a
# text-only session report inert.
written, looked, blocks = [], False, 0
try:
    for line in open(tp, errors="replace"):
        try:
            rec = json.loads(line)
        except Exception:
            continue
        content = (rec.get("message") or {}).get("content")
        if not isinstance(content, list):
            continue
        for c in content:
            if not isinstance(c, dict):
                continue
            blocks += 1
            if c.get("type") != "tool_use":
                continue
            name, inp = c.get("name") or "", c.get("input") or {}
            fp = str(inp.get("file_path") or "")
            if name in WRITERS and re.search(r"\.html?$", fp, re.I) and not SKIP.search(fp):
                written.append(fp)
            elif name == "Read" and re.search(r"\.(png|jpe?g|webp)$", fp, re.I):
                looked = True
            elif name == "Bash" and LOOKED.search(str(inp.get("command") or "")):
                looked = True
            elif name.startswith("mcp__claude-in-chrome"):
                looked = True
except OSError:
    sys.exit(0)

if not blocks:
    sys.stderr.write("── html-render gate ── not one structured message block found in the "
                     "transcript; the check did not run. This is INERT, not clean.\n")
    sys.exit(3)

if looked or not written:
    sys.exit(0)

stamp = pathlib.Path(os.path.expanduser("~/.claude/.html-render-checked")) / \
        (d.get("session_id") or os.path.basename(tp))
try:
    stamp.parent.mkdir(parents=True, exist_ok=True)
    if stamp.exists():
        sys.exit(0)
    stamp.write_text("fired\n")
except OSError:
    sys.exit(0)

uniq = sorted(set(written))
sys.stderr.write(
    "This session wrote %d HTML file(s) a human will eventually look at, and nothing in it "
    "rendered or viewed one:\n\n  %s\n\n"
    "\"The logic is verified\" is not the same claim as \"I looked at it\", and has already missed "
    "defects a glance caught. There is no browser on PATH here, which is the assumption that "
    "normally stops this happening — and it is wrong: `podman` plus a desktop image gives a "
    "headless Firefox with no install. Load the `headless-render` skill for the command, the "
    "theme-pref trap, and the cheaper checks that come first. If this HTML genuinely has no human "
    "reader, say so explicitly. One nudge per session; this will not fire again.\n"
    % (len(uniq), "\n  ".join(uniq[:6]))
)
sys.exit(2)
PY
rc=$?
[ "$rc" -eq 2 ] && exit 2
# 3 = inert. Non-blocking, but exit 1 is what puts the line in front of the operator; on exit 0 the
# harness discards stderr and the warning would be invisible.
[ "$rc" -eq 3 ] && exit 1
exit 0
