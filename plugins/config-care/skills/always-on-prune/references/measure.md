# Measuring before you move anything — attribution, the tier, the roster

Load at the start of a pass, before any per-file decision: `SKILL.md` steps 1 and 2 say *run these*;
this is what each script answers, how it lies, and what to do with the number. All scripts sit in the
skill root (one level up from this file). Record your own results in `~/.claude/local/always-on-prune/instance.md`.

## Step 1 — attribute first: this may not be your problem at all

**Before measuring the resident tier, find out whether it is where your consumption actually goes.**
Running these first is what stops the skill being an expensive way to save nothing:

```bash
python3 usage-attribution.py [days]   # resident tier as a share of ALL consumption
python3 where-the-bar-goes.py [days]  # spend by session size, and by subagent model
```

On the setup this was built from, residency was **not** the dominant term: the tier was ~10% of context
tokens and a hard prune of it moved under 1% of consumption, while subagent model choice and long-running
sessions accounted for the overwhelming majority **If your attribution
looks like that, stop and go fix routing and session length instead.** Come back only if resident bytes
are genuinely a meaningful share — or if you run a subagent-heavy workload, where the resident prefix is a
much larger fraction of a fresh agent's context than of a long session's.

That check costs two commands. Skipping it is how a pass optimises a rounding error.

## Step 2 — measure the tier itself

Four more scripts. Run them all; they take seconds and they routinely overturn the plan you would
otherwise have written.

```bash
python3 measure-resident-cost.py [days]   # what a resident KB actually costs, on real traffic
python3 overlap.py                        # where the tier repeats itself or repeats a skill
python3 lookup-moment.py --skills … --situation …   # whether a given pref can move into a skill
python3 relocation-economics.py [days]    # whether moving it down actually saves, after cache pricing
```

**`relocation-economics.py` is the one that could sink the pass:** it measures **f**, the share of
sessions that load each destination, and where in the session that load lands. Pass `--dests` with your
own destinations; the default list is this machine's. A destination that loads early in nearly every
session is one where relocation loses, and it will say so. An f of zero is a warning, not a saving
(`SKILL.md` step 5).

**`measure-resident-cost.py` reframes the conversation:** it converts "this tier feels like a lot" into a
dollar figure per file, from real requests split into cold-prefix writes and cached reads. **Read its
docstring before trusting its output** — the obvious way to compute this overstates by ~12x, and it
explains why. It and `overlap.py` default to `~/.claude/memory` as the preference store (`--prefs-dir` if
yours is elsewhere), and both refuse to report a zero from a missing directory, which would be
indistinguishable from a real empty tier. Its model price table is guaranteed to go stale, and cache reads
are not a flat 0.1x on every model: check the table and `CR_MULT` in the scripts before quoting a dollar
figure.

### Two measurements before the per-file work

**Frontmatter is not resident.** `---` blocks are stripped when preferences are expanded into context;
only bodies load. Verify that on the machine you are on rather than assuming, then measure bodies, not
file sizes — a checker counting file bytes overstates by whatever fraction of the store is frontmatter,
and `measure-resident-cost.py` prints both totals so the gap is visible. Fixing the checker is free and
can be worth more than several cuts.

**The skill roster is the other half, and it is usually uncounted.** Every skill's name and description
sits in the system prompt on every request. Measure it:

```bash
python3 - <<'PY'
import glob, os, re
tot = 0
pats = ["~/.claude/skills/*/SKILL.md", "~/.claude/plugins/cache/*/*/*/skills/*/SKILL.md"]
for p in [f for g in pats for f in glob.glob(os.path.expanduser(g))]:
    m = re.search(r"^---\n(.*?)\n---", open(p, errors="replace").read(6000), re.S)
    if not m: continue
    d = re.search(r"^description:\s*(.*?)(?=\n[a-z_]+:|\Z)", m.group(1), re.S | re.M)
    if d: tot += len(" ".join(d.group(1).split()))
print("skill roster resident bytes:", tot)
PY
```

Measured on the setup this was built from, the roster came out the same order of magnitude as the entire
preference tier — **a large minority of the always-on budget, and no tooling was counting it**. Run it before assuming the prefs are where the weight is. But treat it differently from
prose: a description's length is *functional* — that text is what makes the skill trigger at all, and a
skill that stops firing is worth nothing. Report the number, cut only descriptions visibly padded or
redundant with a sibling, and to cut deeper, measure triggering with whatever eval tooling the setup has
rather than by eye.

### A roster over the listing budget is a triggering outage, not a cost problem

Claude Code caps each description at 1,536 chars and the whole listing at 1% of the context window
(`skillListingMaxDescChars`, `skillListingBudgetFraction`, vendor doc); over budget it keeps every *name*
but drops descriptions starting with the least-invoked skills. So the rarely-used skills — the ones that
most need a description to fire — silently go name-only. Look at a live session's skill listing: names
with no description, or descriptions ending in "…", mean long descriptions elsewhere are breaking
triggering here, and trimming them is a fix rather than a saving. After trimming, check the skills still
fire: `trigger-test.sh` in the skill root runs each prompt in a fresh headless session (its header lists
the traps that make it lie).

To read the listing after an edit without restarting, ask a fresh `claude -p` (no tool calls) to print
every skill that appears with no description. Leave `Skill` out of `--disallowedTools`: disallowing it
removes the listing entirely, and the session then reports that there is nothing to read. Check the
answer against names you already know are name-only.

## Do not write another measurer — that half is already taken

Read these before building anything:

- **ctxlint** (`@yawlabs/ctxlint`, github.com/YawLabs/ctxlint) — has a `tier-tokens` check that tracks
  always-loaded files separately, with per-file and combined budgets. Small project; the machine-readable
  rule specs are the part worth stealing.
- **AgentLinter** (agentlinter.com) — context-budget estimator whose rules are literally named "context
  bloat" and "progressive disclosure".
- **Claude Code's own `/doctor`** — proposes trims to a checked-in instruction file, cutting what is
  derivable from the codebase and keeping pitfalls and rationale.

What is genuinely unclaimed is the **decision** — which rung a passage belongs in, and why. That is what
this skill is. The scripts exist because the decision needs numbers, not because nobody else can count
tokens.
