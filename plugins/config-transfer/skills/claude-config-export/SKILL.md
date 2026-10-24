---
name: claude-config-export
description: "Package Claude Code config (skills, memories, hooks, CLAUDE.md prefs) into a scrubbed, generalized bundle for a DIFFERENT trust domain — a second machine you don't control, a friend, a public share. Use for \"package my skills and memory for my other machine\", \"export my claude config\", \"share my setup\". Consuming a bundle is claude-config-import; own machines are claude-fleet-sync."
---

# Claude Code config export (cross-boundary)

BLUF: move the *portable* parts of a Claude Code setup — the behavioral prefs, generalizable
working-style + ops lessons, and reusable skills — across a trust boundary (between two machines you keep separate,
one person to another, private to public) so both setups behave consistently. The recipient **judges
and imports** (with `claude-config-import`); you never force a wholesale copy. Because the
environments differ, everything is **scrubbed and generalized** first: secrets, hostnames, IPs,
internal domains, personal/organisation names, home paths, and environment-only services must not cross.

**Not `claude-fleet-sync`.** That unions config across machines the user fully controls and keeps
their specifics intact. This skill crosses a boundary where those specifics are exactly what must be
stripped. If the two machines are the same trust domain, use `claude-fleet-sync` instead.

This is the **producer** side. The consumer side — reconciling a received bundle against the local
setup — is the separate `claude-config-import` skill.

> **If either machine holds marked or regulated data** (confidential documents, personal or health
> data), list its markings in a file and run the sweep with `MARKINGS=<file>`,
> exclude by default rather than generalize (if a memory or skill ever touched the controlled
> material, drop it; a paraphrase can still leak), and have a person review the bundle before it
> leaves.

## 1. Inventory
List what exists: `~/.claude/skills/`, `~/.claude/memory/` (the CLAUDE.md-imported prefs), the
project auto-memory dir + its `MEMORY.md`, `~/.claude/hooks/`, and `~/.claude/CLAUDE.md`.

**Derive every list from disk; never hand-type one.** A copy loop driven by a typed list of names
silently ships whatever you left out — the omission is invisible because nothing errors. A hook
dropped this way can stay documented in four places and only a cold read catches it. Iterate the real
directory, and afterwards `diff` the source listing against the bundle's.

## 2. Classify each item (the judgment)
Sort every skill and memory into one of these. When unsure whether something is portable, ask what a
stranger in the *other* environment gains from it — if the answer is "nothing without this specific
setup," exclude it.

- **Behavioral core (always include):** the always-on prefs that shape *how* Claude works (push back
  vs hedge, prefer subtraction, verify-don't-anchor, distill-don't-dump, etc.). Highest value.
- **Portable working-style memories:** generalizable lessons about doing the work (eval hygiene,
  delegation patterns, skill design, capture discipline). Include.
- **Generalizable ops/tech lessons:** an incident memory whose *lesson* transfers even though it
  happened on specific infra (a k8s/DB/cert gotcha). Include **after generalizing** (step 3).
- **Reusable skills:** domain-agnostic ones (repo tooling, doc writing, bug hunting) always;
  domain-specific ops skills (k8s/Talos/etc.) if the recipient does that kind of work.
- **Hook SCRIPTS (include — they are usually the most valuable thing in the bundle):** a hook is a
  lesson that stopped being advice, and its header comment carries the incident that produced it. They
  port cleanly because they are self-contained and address everything relative to `~/.claude`. Ship a
  `settings.example.json` carrying **only** the `hooks` block, with paths as `"$HOME/.claude/hooks/…"`
  — that expands, because a `command` with no `args` field runs in shell form. State per hook whether
  it fails open or closed, and **verify that against the script** rather than from intent: a
  correctness gate that swallows its own errors fails open, and installed-but-inert is indistinguishable
  from working.
- **EXCLUDE:** environment-inventory memories (topology, node lists, per-service config), personal/
  confidential services, anything with secrets, and the rest of `settings.json` — the permission
  allowlist, `env`, plugins and marketplaces are environment-specific, and the allowlist in particular
  leaks hostnames and internal tool names. Record the excluded *categories* in the README so the
  recipient knows nothing was hidden by mistake.

## 3. Generalize — don't drop
When a portable lesson names a host/service/secret, **rewrite it into a generic form** (`<host>`,
`example.com`, "a cluster", "the app's own error table") rather than dropping the whole lesson. Also
**distill incident residue** — strip dates, ticket/PR numbers, commit SHAs, run-counts, status
amendments ("RESOLVED 2026-…"), and originSession metadata down to the reusable lesson. A transferred
memory is a distilled fact, not a build journal. (For regulated data this rule inverts — see the
callout above; drop, don't paraphrase.)

## 4. Assemble
Copy with `python3 freshness-gate.py stage <bundle> <source> <bundle-path>` (a file or a whole dir) —
it copies and records the source's sha256 in the bundle's `MANIFEST.json`, which is what step 5's
freshness check reads. A file copied any other way has no record and fails that check. Lay the bundle
out with tiered subfolders so the recipient can judge a whole tier at a glance,
e.g. `memory/{cross-project-prefs,working-style,infra-ops,linux-generic}/` and `skills/<name>/` (whole
dirs, including any `references/`). Strip process-residue frontmatter lines:
`sed -i '/^  originSessionId:/d; /^  modified:/d; /^  node_type:/d' <file>`.
Drop dev-only cruft skills don't need to run (e.g. `evals/`, `__pycache__/`, `*.pyc`) — and a bundle
must be **all text**: never ship a compiled binary (a `.pyc` built from pre-scrub source can carry
real hostnames in its string table). Don't ship the source `MEMORY.md` index — the recipient maintains
their own.

## 5. Verify with the sweep (the gate — do NOT skip)
Run the bundled script against the finished bundle:
```
./scrub-sweep.sh <bundle-dir> [env-patterns-file] [allowlist-file]
```
The env-patterns and allowlist files are your own, kept in `~/.claude/local/claude-config-export/`.
Put YOUR environment's tokens in the env-patterns file — hostnames, domains, organisation/client names,
internal tool + script names, usernames, and your own names. That's where the real hits are; the
script's built-ins (secrets, private IPs, emails, home paths) are only a floor. For marked data,
add `MARKINGS=<file>` (your organisation's document markings, matched case-sensitively). The gate also **fails on any binary file** in
the bundle. **Sweep twice**: a first pass for hosts/IPs, then a second for product/tool/script names
— residue hides in *illustrative examples* (a lesson generalized in the body still name-drops the real
app in a "for instance"). Iterate until it returns PASS. Genuine false positives (a public domain a
skill legitimately cites) go in the allowlist.

**A hit is a question, not a finding: it says a pattern matched, not that the thing is sensitive.**
Before excluding an item over a hit, say what the matched token actually identifies and who it
exposes — a whole skill can be withheld for "naming an individual" who was the exporter themselves.

**On a repeat bundle, inherit the previous one's scrubbed copies.** Keep the last shipped bundle on
disk, reuse the copies that still correspond to current content, and re-scrub only what moved on.
It also preserves the previous round's cold-read fixes, which a fresh copy silently discards.

**Do NOT decide that by mtime** — a bundle copy is always newer than its source, so an mtime test
says *inherit* forever and content edits silently stop propagating (it ships stale hooks under the
same version number). `freshness-gate.py` decides it instead, by hash: the source sha256 recorded in
`MANIFEST.json` at staging must equal the source's sha256 now. Different is **stale** (update the
staged copy, re-scrub, then `freshness-gate.py record <bundle> <source> <bundle-path>` to re-pin it);
no record is **unknown** and fails too. `scrub-sweep.sh` runs it, so a clean scrub also means a current
one. A base bundle staged before `MANIFEST.json` existed comes back all-unknown: re-stage, or `record`
each file once you have checked its staged copy against the current source.

**Re-copying from the source undoes the scrub — every time.** If you update a bundled file by
copying the local original over it, you reintroduce every token you generalized, silently. Either
re-generalize after any re-copy, or edit the bundle copy directly and never re-copy. **Always re-run
the sweep after touching the bundle at all**, not just once at the end — it is the only thing that
catches this.

The failure modes behind each of these rules are in `references/incidents.md`. Read `references/sweep-internals.md` when a
gate result surprises you, before editing the scripts or allowlist, or before re-implementing the allowlist re-test
(POSIX bracket-class trap).

## 5b. Adversarial cold-read (the pass the regex CANNOT do — never skip)
The sweep only catches *known tokens*. It cannot catch **semantic leaks**: an anecdote that
fingerprints the person or employer without a keyword, a named-but-unlisted internal project, a
distinctive infra combination, or a lesson quietly gutted by over-scrubbing. Delegate one or more
**cold** agents (fresh context — do NOT prime them that it's "already clean"; that invites a
rubber-stamp) over the finished bundle, each with a distinct hostile lens:
- **residual identifying/sensitive data** — read as an adversary trying to fingerprint the origin
  environment/person/employer from what's left;
- **generalization quality** — did scrubbing break coherence, orphan a reference, or leave a note too
  thin to be worth shipping;
- **scoping** (give this one the full *source* inventory too) — anything included that shouldn't be,
  a portable item wrongly excluded, or mis-tiered.

**A test fixture or benchmark corpus built from real activity is a leak the sweep cannot see, and
it is the worst content in the bundle.** A fixture corpus mined from one person's real activity passes
several sweeps, because personal queries contain no hostname. The same applies to any
recorded-real-input corpus: hook test fixtures carrying real service names and internal script names,
captured commands, sample logs. **So enumerate every fixture, corpus and sample in the bundle and
read the values, not the code.** They are safe to rewrite — a fixture only has to preserve the
*shape* the code keys on, never the subject — and the suite passing afterwards is the proof that you
preserved it.

**Hand every cold agent the PREVIOUS bundle's finding list, and tell it to re-check each finding's
SHAPE rather than the file it was found in.** A finding is never about one file; it is about a *kind*
of content, and remediation scoped to the filename in the finding fixes one member of the population.
The next pass has to go looking for the rest of the kind. Adding the terms to your env-patterns file
is the backstop, not the method, since the next leak will be a category nobody has a pattern for
either.

**Dropping an instance file can gut the skill beside it.** An `instance.md` is supposed to hold only
what is environment-specific, but skills drift, and excluding one can leave a SKILL.md that no longer
says how to do the thing — with no error and a passing sweep. After excluding any companion file,
read the parent skill and confirm it still tells you how to do the thing.
Act on the findings, then re-run the sweep (step 5). A self-review by the same context that did the
scrubbing is anchored and misses its own leaks — the cold pass is the point. Re-run the cold pass on
any items you add or change afterward. Never let a PASS from step 5 substitute for step 5b.

## 6. README
Write a `README.md` at the bundle root: it's the handoff to the recipient. Include — what's inside by
tier and the suggested action per tier; the excluded categories; a pointer to `claude-config-import`
for consuming it. If the transfer is meant to be two-way, ask the recipient to export an equivalent
bundle back (with `claude-config-export`, same exclude/scrub/generalize/sweep discipline). State
plainly that the recipient is the judge.

## The NO-SHIP marker is a hard gate

Some items are person-specific or carry private reasoning — how to pitch findings to a named maintainer,
a named security contact, evidence about individual users. Those must never enter a bundle, a repo, or a
marketplace seed pack, and **prose saying so is not enforcement**: the person packaging the bundle is
exactly the person who won't re-read the file.

So such files carry the marker as an **HTML comment directly under their frontmatter** — the literal
form, which is what the gate matches:

```
<!-- NO-SHIP: person-specific / private context. Must never enter a transfer bundle, a repo, or a marketplace seed pack. -->
```

`scrub-sweep.sh` **exits 1 and names them** if any appear in the bundle directory, before it does any
token matching — a marked file is not a token to review, it is a file that must not be in the tree.
Add the marker whenever you write something in that category; don't rely on remembering at export time.

**Match the form, not this description.** Narrowing the check to a bare `NO-SHIP` on its own line —
which is what "a literal marker" sounds like — matches *none* of the real files and silently disables
the gate. The check is scoped to the head of the file so that prose *about* the marker (this section)
doesn't trip it; verify any change to it against actual marked files, never a fixture you wrote to
match your change. `test-sweep.sh` covers both directions.

## Publishing to a public repo

The same discipline applies when the destination is a public repository rather than another machine:
stage with `freshness-gate.py`, run the sweep with your own names in the patterns, do the cold read,
and honour NO-SHIP. A repo is also where the strictest reader lands, so read it as a stranger would:
per-user companion files (instance data, logs, local baselines) stay out of it, and anything a skill
expects to find "beside" itself must either ship or be documented as the user's own. One workable
layout is a plugin marketplace (one directory per plugin, each with its skills), which lets people
install a piece at a time.

**A rewritten example has two more ends than the paragraph you changed.** Grep the whole skill for
the case's other mentions: a summary line can keep the old domain while its reference file moves to a
new one, so the case reads in both. And a case moved into an invented domain is no longer measured:
drop "real", "Evidence:" and kept counts, and label it an illustrative composite. Cold-read the diff
with a fresh agent before the gates.

## Stop rule: converge, don't ping-pong

A sync is finished when both sides **behave** the same way — not when neither side has any remaining
observation. Reviewing a bundle always generates findings, and a pair that starts a new transfer for
each one never converges.

**The gate is on the TRIP, not on the payload.** Two separate questions, and only the first is
restrictive:

1. **Does this justify a trip at all?** Only these do: a bug producing wrong behaviour, silent
   failure or data loss; a security issue; a factual correction to something the other party is
   actively shipping; or genuinely new method. Never start a transfer to deliver wording
   preferences, restructuring opinions, naming quibbles, counts, acknowledgements, or unverified
   hunches. **If a review produced only those, the correct output is "nothing to send back" — say it
   plainly and stop.**

2. **A bundle is going anyway — what goes in it?** *Everything portable*, nits included. Once a
   transfer is happening for a real reason (or on a routine sync), the marginal cost of another file
   is nothing and the cost of holding it back is another trip later. Do not hand-pick a minimal
   payload out of restraint; that is how a "small" fix bundle becomes three trips.

So: **batch, don't trickle.** Findings wait in your own `PENDING-FINDINGS.md`, kept in
`~/.claude/local/claude-config-export/`. Read it when assembling, fold what is still true into the
bundle's `FINDINGS.md`, then empty it. They ride along with the next bundle that was going
regardless. The only findings that may interrupt to start their own transfer are a security bug and
data loss.

This applies to **every** pair of machines using an export/import skill — config, infrastructure
repos, anything else.

## Two-way transfers
A transfer between two setups you maintain can run both ways: after the recipient imports, it exports
its own side back, and both setups **converge** over time. Each side always scrubs its own specifics
before sending. Consuming a bundle (reconcile-by-function, merge-don't-duplicate) is the
`claude-config-import` skill's job.

Which machines are paired, where a bundle physically crosses, whether either side handles controlled
data, and what shipped last time are instance data: keep them in `~/.claude/local/claude-config-export/INSTANCE.md`,
not in this skill.
