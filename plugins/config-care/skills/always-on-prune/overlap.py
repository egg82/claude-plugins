#!/usr/bin/env python3
"""Where does the always-on tier repeat itself, or repeat a skill?

Shingle overlap on normalised word 8-grams. Not a semantic measure — it finds text actually reused,
which is the case where one copy can go. A low score is NOT evidence of no duplication (two files can
say the same thing in different words), so this narrows where to look; it does not decide anything.
"""
import argparse, glob, os, re, sys, collections

ap = argparse.ArgumentParser(description=__doc__.splitlines()[0],
                             formatter_class=argparse.RawDescriptionHelpFormatter)
ap.add_argument("--prefs-dir", default="~/.claude/memory",
                help="directory of resident preference files (*.md). Default is this machine's "
                     "convention; a CLAUDE.md @import can point anywhere, so check yours.")
a = ap.parse_args()

N = 8
MEM = os.path.expanduser(a.prefs_dir)
SKILLS = os.path.expanduser("~/.claude/skills")
HOOKS = os.path.expanduser("~/.claude/hooks")

if not os.path.isdir(MEM):
    sys.exit(f"INCONCLUSIVE — preference directory does not exist: {MEM}\n"
             f"  Nothing was compared. Point --prefs-dir at the directory your CLAUDE.md @imports.")
pref_files = sorted(glob.glob(os.path.join(MEM, "*.md")))
if not pref_files:
    sys.exit(f"INCONCLUSIVE — no *.md files in {MEM}\n"
             f"  An empty table here would be indistinguishable from a tier with no overlap, so "
             f"nothing is reported. Point --prefs-dir at the directory your CLAUDE.md @imports.")

def shingles(text):
    w = re.findall(r"[a-z0-9]+", text.lower())
    return {" ".join(w[i:i + N]) for i in range(max(0, len(w) - N + 1))}

mem = {}
for p in pref_files:
    mem[os.path.basename(p)[:-3]] = shingles(open(p, errors="replace").read())

print("=== memory <-> memory: shared 8-grams (both directions shown as % of the SMALLER file) ===")
names = sorted(mem)
pairs = []
for i, a in enumerate(names):
    for b in names[i + 1:]:
        inter = mem[a] & mem[b]
        if not inter:
            continue
        denom = min(len(mem[a]), len(mem[b])) or 1
        pairs.append((len(inter) / denom, len(inter), a, b))
for frac, n, a, b in sorted(pairs, reverse=True)[:12]:
    print(f"  {frac:5.1%}  {n:4} grams   {a}  <->  {b}")
if not pairs:
    print("  none — no two prefs share an 8-gram")

print("\n=== memory -> skills/hooks: how much of each pref's text appears in a skill or hook? ===")
corpus = {}
for p in glob.glob(os.path.join(SKILLS, "*", "*.md")) + \
         glob.glob(os.path.join(SKILLS, "*", "*", "*.md")) + \
         glob.glob(os.path.join(HOOKS, "*.sh")):
    corpus[os.path.relpath(p, os.path.expanduser("~/.claude"))] = shingles(
        open(p, errors="replace").read())

rows = []
for name, sh in mem.items():
    if not sh:
        continue
    best, bestfile = 0.0, "-"
    union = set()
    for f, s in corpus.items():
        inter = sh & s
        if inter:
            union |= inter
            frac = len(inter) / len(sh)
            if frac > best:
                best, bestfile = frac, f
    rows.append((len(union) / len(sh), best, bestfile, name))

for anyfrac, best, bestfile, name in sorted(rows, reverse=True):
    flag = "  <-- most of this text already exists elsewhere" if anyfrac >= 0.20 else ""
    print(f"  {anyfrac:5.1%} of {name:34} appears somewhere; best single: {best:5.1%} {bestfile}{flag}")

print("\nRead this as a pointer, not a verdict: a high score on a pref whose JOB is to make you load")
print("that skill is expected and correct. A high score on a pref restating the skill's METHOD is a cut.")
