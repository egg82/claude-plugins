#!/usr/bin/env python3
"""Is there a LOOKUP MOMENT for a resident preference — or must it stay resident?

The question that decides every cut. If someone will realise they need this and can go fetch the
skill, the content belongs in the skill. If the failure mode is *not knowing to look*, a trigger has
to stay resident and only the catalog moves.

This makes that testable instead of arguable. Give it the skills that would cover the situation and a
regex matching the situation as it appears in a transcript; it counts how often the situation arose
with none of those skills loaded.

    lookup-moment.py --skills git-workflow \
                     --situation 'git\\s+(rebase|reset|push)' \
                     --narrow '--force|--hard' [--days 60]

Reading the result:
  many situations, few loads  -> NO lookup moment. Keep a resident trigger; move the detail.
  loads track situations      -> the skill is reliably reached. Move the whole thing.

TWO TRAPS, both hit while writing this, both of which produce a confident wrong zero.

1. **Do not match the skill's NAME in the transcript text.** A resident memory that mentions the skill
   is injected into every session, so a name-match flag is true from line 1 of every transcript and
   the probe can never return non-zero. The first version of this script did exactly that and reported
   a clean 0. A skill is LOADED when the Skill tool is invoked or its SKILL.md is Read — nothing else.

2. **A zero downstream means nothing if a stage upstream is also zero.** Every stage is printed, so a
   final zero can be told apart from a broken regex or an empty corpus.

The `--situation` regex is yours to get right, and it will be loose. Read the sample hits it prints
before believing the count: a handful of false positives is fine for a directional answer, but if the
samples are all unrelated, the number is measuring your regex.

WHAT THE SAMPLES ARE. They are verbatim excerpts of real commands out of the transcript store — that
is exactly why they are worth reading, and also why they are not shareable output. They can carry
hostnames, paths, tokens, and anything else that was typed on this machine. Read them in the terminal
and judge the regex from them; do not paste them into a findings file, a report, a ticket, or anything
that leaves the host. Quote the counts, not the samples.
"""
import argparse, collections, glob, json, os, re, time

ap = argparse.ArgumentParser()
ap.add_argument("--skills", required=True,
                help="comma-separated skill names that would cover this situation")
ap.add_argument("--situation", required=True,
                help="regex matching the situation in a Bash command / tool input")
ap.add_argument("--narrow", default="",
                help="optional second regex the situation must ALSO match, to cut false positives")
ap.add_argument("--days", type=int, default=60)
ap.add_argument("--samples", type=int, default=10)
ap.add_argument("--include-prompts", action="store_true",
                help="also search Agent-tool prompts, not just Bash commands (usually not what you "
                     "want: it lets an investigation into this question count itself as evidence)")
a = ap.parse_args()

SKILLS = tuple(s.strip() for s in a.skills.split(",") if s.strip())
SIT = re.compile(a.situation, re.I)
NARROW = re.compile(a.narrow, re.I) if a.narrow else None
CUTOFF = time.time() - a.days * 86400

def is_load(blk):
    """A real load: Skill(<name>), or a Read of that skill's own files."""
    if not isinstance(blk, dict) or blk.get("type") != "tool_use":
        return False
    inp = blk.get("input") or {}
    if blk.get("name") == "Skill" and str(inp.get("skill", "")).strip() in SKILLS:
        return True
    if blk.get("name") == "Read":
        p = str(inp.get("file_path", ""))
        return any(f"/skills/{s}/" in p for s in SKILLS)
    return False

stats = collections.Counter()
hits = []
for f in glob.glob(os.path.expanduser("~/.claude/projects/*/*.jsonl")):
    try:
        if os.path.getmtime(f) < CUTOFF:
            continue
    except OSError:
        continue
    stats["sessions"] += 1
    loaded = False
    unprotected = None
    for line in open(f, errors="replace"):
        if '"tool_use"' not in line:
            continue
        try:
            d = json.loads(line)
        except Exception:
            continue
        for blk in (d.get("message") or {}).get("content") or []:
            if is_load(blk):
                loaded = True
                stats["loads"] += 1
                continue
            if not isinstance(blk, dict) or blk.get("type") != "tool_use":
                continue
            inp = blk.get("input") or {}
            # Bash commands only, by default. An earlier version also searched `prompt`, which
            # matched the briefs of subagents spawned to work ON this question — the investigation
            # counting itself as evidence. Opt into prompts with --include-prompts if you mean to.
            text = str(inp.get("command") or "")
            if not text and a.include_prompts:
                text = str(inp.get("prompt") or "")
            if not text or not SIT.search(text):
                continue
            stats["situations"] += 1
            if NARROW and not NARROW.search(text):
                continue
            stats["narrowed"] += 1
            if not loaded and unprotected is None:
                unprotected = " ".join(text.split())[:110]
    if unprotected:
        stats["sessions_unprotected"] += 1
        hits.append((os.path.basename(f)[:8], unprotected))

print(f"  corpus                              : {stats['sessions']} sessions, last {a.days}d")
print(f"  real loads of {','.join(SKILLS):20}: {stats['loads']}   <- probe CAN see a load")
print(f"  situation matches                   : {stats['situations']}   <- probe CAN see the situation")
if NARROW:
    print(f"  ...surviving --narrow               : {stats['narrowed']}")
print(f"  sessions hitting it with NO load    : {stats['sessions_unprotected']}")
print("\n  sample hits — READ THESE before believing the count.")
print("  Verbatim transcript commands: judge the regex from them, do not copy them off this host.")
for sid, cmd in hits[:a.samples]:
    print(f"    {sid}  {cmd}")

n = stats["narrowed"] if NARROW else stats["situations"]
print()
if n == 0 or stats["loads"] == 0:
    print("  INCONCLUSIVE — a stage upstream is zero, so the final number says nothing about the world.")
elif stats["sessions_unprotected"] >= 2:
    print("  NO LOOKUP MOMENT. Keep a resident TRIGGER; move the catalog into the skill.")
else:
    print("  The skill is reliably reached first. Safe to move the whole thing into it.")
