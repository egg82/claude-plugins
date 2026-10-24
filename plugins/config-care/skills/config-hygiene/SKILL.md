---
name: config-hygiene
description: "Report drift in a Claude Code setup — outgrown memory indexes, skills carrying instance data, docs their directory has moved past, unregistered hooks. Use for a periodic tidy-up of skills/memory/docs, when a memory index feels bloated or triggers a compaction nudge, before sharing a skill, or as the scheduled hygiene check. Also gates a copy leaving this machine (plugin, marketplace repo, transfer bundle) for NO-SHIP markers and leaked names. Reports only."
---

# Config hygiene

Three kinds of drift, one scanner. **It reports; it never edits** — every finding needs a judgment
call about where the content should have gone.

```
python3 hygiene.py all <repo> [<repo> ...]
python3 hygiene.py memory | skills | refs | probes | imports | hooks | numbering | testiso | docs REPO... | doccontent REPO...
python3 hygiene.py shareable --share-root DIR --names A,B
```

`probes` is a **no-op unless `HYGIENE_RUN_PROBES` is exactly `1`** (any other value, including
`0`, is treated as a refusal) — it executes shell from memory
frontmatter, so it refuses by default. A run without that variable prints `SKIPPED`, which is not the
same as "every probe passed".

## What each mode reports

Detail, and what to do about each finding: `references/checks.md`.

| mode | flags |
|---|---|
| `memory` | dangling index bullets, orphan files, an index over ~12KB, a memory over 8KB; unimported or missing always-on prefs; `MEMORY.md` near its load caps |
| `imports` | the always-loaded set: an import naming a missing file, a file nobody imports, total bytes (printed even when clean) |
| `skills` | `SKILL.md` content that goes stale on its own schedule — dates, hard counts, IPs, MACs |
| `probes` | memories whose `check:` command fails — suspect the probe first |
| `docs` | a doc whose directory has commits more than 30 days newer than the doc |
| `doccontent` | repo docs carrying dates, status words and run counts |
| `hooks` | a registered hook with no script, and a script no registration references |
| `refs` | `[[links]]` in skills and companions pointing at a memory or skill that doesn't exist |
| `numbering` | colliding (level, number) headings, or numbers out of order after a graft |
| `testiso` | a test suite mutating the real `$HOME` |
| `shareable` | refusals on a copy leaving this machine (`references/shareable-gate.md`) |

`section-inventory.py` is not a mode: it diffs a file's per-section inventory before and after your own
edit (`references/checks.md`).

## Which reference

| The situation is... | Load |
|---|---|
| A mode reported something and you need to judge it | `references/checks.md` |
| Something doesn't obviously fit; extending the scheme this audits — where each kind of fact belongs, and the evidence behind each mechanism | `references/knowledge-organization.md` |
| First install, or a store that has already drifted into a catch-all | `references/first-run.md` |
| The `mine-repeat-traps.py` line appeared at SessionStart; deciding where a recurring trap is enforced | `references/repeat-traps.md` |
| Publishing a plugin or marketplace repo, or handing over a transfer bundle | `references/shareable-gate.md` |
| Platform behaviour, agent-memory architectures, documentation-drift mechanisms ranked weakest to strongest | `references/findings-and-sources.md` |
| Enforcement mechanisms that fail silently, verifier error profiles, multi-agent and review evidence — **tiered `[V]/[M]/[P]/[Ø]`; don't repeat a claim without checking its tier** | `references/collaboration-and-enforcement.md` |
| Several people share the setup | `references/recommendations-for-a-shared-setup.md` |

The last three are the evidence base, with source URLs, so the same searches don't get re-run.

## Traps that keep biting

`mine-repeat-traps.py` answers what the other checks cannot: **which lessons are already written down
and still being hit?** A trap that recurs after being documented is proof the prose is not working,
and the fix is never to write it again more emphatically — promote it to a gate only when it is both
frequent AND statically provable. Routing table and the miner's blind spots: `references/repeat-traps.md`.

## Does a memory actually change behaviour? — `memory-ab.py`

Asks **before** you edit: does this memory move behaviour at all, and did trimming it break anything?

```
python3 memory-ab.py run   <config.json> --reps 7
python3 memory-ab.py score <config.json>
```

Configs, trim candidates and run data live in `~/.claude/ab-runs/`, not here — run data is one
person's prompts, and a skill dir gets copied whole when shared. The docstring carries the config
format. It spends money (`--max-usd` caps it).

- Each experiment declares its `labels` and its `aligned` label; the judge answers through
  `--json-schema` with one of them, and anything else is tallied as **unscored**, never as a miss.
  `memory-ab.py selftest` runs the scoring path against recorded replies without a call.

- Arms: memory injected, absent, and **replaced by an unrelated memory of similar size** — the
  placebo arm is the one that matters. All tools are disallowed, or the control goes and reads the
  memory it should lack.
- **The mode worth reaching for is trim validation**: `arms` at the live file and a candidate; it
  referees the candidate against the **original** ("did I make this worse", not "is it good"). DO NOT
  SHIP only when significantly worse; UNVALIDATED when the prompt cannot referee.
- **Prefer the pre-registered probe set** (write your own, one per rule): situated probes with
  headroom, mechanical graders, each with a `good` (1.0) and `null` (0.0) fixture asserted by
  `selftest()` — necessary, not sufficient.
- **Purpose-written placebos** (`ab-variants/placebo-*.md`) beat a real memory as placebo, which can
  turn out relevant and become a second treatment arm.
- **A ceiling proves nothing** — if the control scores full marks the prompt was too easy. Build
  prompts where the un-memoried baseline fails.
- **A null here is weak evidence** — turn one of a clean, tool-free session; a memory redundant on
  turn 1 may be load-bearing on turn 80. Cross-check a null against real transcripts before acting.

## Autonomous scheduled mode

There is **no `--auto` flag** — the script takes only a mode and paths. "Autonomous mode" is a
behavioral instruction to whoever invokes it: **change nothing.** Run every
check, then write the findings to **`~/.claude/.hygiene-report`** — one finding per line, newest run
replacing the file entirely. Write the file even when clean (a single `clean` line), so a missing
file means the job didn't run rather than found nothing.

**Why the file matters more than the report:** a scheduled check that logs to the scheduler is a
check nobody reads. The `SessionStart` hook surfaces `.hygiene-report` into context at the start of
the next session, which is the only moment anyone can act on it. Findings that don't reach an agent
or a human don't exist.

Also verify **fleet parity** in this mode — the nightly sync reports success even when a per-host
step silently misses, so compare file counts and index size across hosts and report any divergence
as a finding.

**Scheduling the sweep.** `systemd/` holds an optional `claude-hygiene.service` and `.timer`: copy both
into `~/.config/systemd/user/`, point `ExecStart` at your copy of `run-sweep.sh`, and
`systemctl --user enable --now claude-hygiene.timer`. Cron works equally well.

**Verdicts already reached live in `known-benign.md` beside this file (shipped seeds) and in your own
`~/.claude/local/config-hygiene/known-benign.md` — read both before judging a
hit, and add new verdicts to your own copy, since `/plugin update` replaces the shipped one.** A "looked at it, it's fine" writes nothing anywhere else,
so it is the one conclusion guaranteed to be re-derived at full cost every sweep.

## The scanner is coarse in both directions

**"Clean" means the *detectable* forms of drift are absent, not that the docs are good.** A zero is
a statement about the patterns being scanned for. Read the thing before concluding it's fine.

**And a hit is not automatically a problem.** The `skills` check counts numbers and dates without
understanding them, so it cannot distinguish:

- a **hard cap or protocol constant** (`200 lines`, `25KB`, a port, a threshold) — these don't drift
  with the world, they *are* the world, and they belong
- a **measurement of current state** (`~1580 items`, `currently 14 entries`) — genuine rot
- a date or figure **quoted as an example of the anti-pattern** — a false positive by construction

Judge each hit against the real test: *does this detail change what the reader does?* If it does,
keep it regardless of the score. The score is a prompt to look, not a verdict.
