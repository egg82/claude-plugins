# Making the check able to fail: reachability, mutation and novelty probes, assertions that cannot fail

Load when you are proving a gate or test can go red (`SKILL.md` steps 4, 5 and 8). Bash specifics for step 4:
`bash-and-bats.md`; controls and doubles that lie: `controls-that-lie.md`; harness and fixtures:
`harness-and-fixtures.md`.

## Step 4: reachability

The most common reason important logic has no tests is mechanical, not cultural: the entry point runs
on import or on source, so a test cannot reach a function without running the program. Guard the entry
point, one line per file. Bash specifics: `bash-and-bats.md`.

## Step 5: break it on purpose

**A mechanical scan generates leads and settles nothing.** Over one session, hand-written detectors
over shell source produced four false positives — two from picking the wrong function where a module
defined two near-identically-named writers, one from a path guard that never matched because names
were package-relative, one from a regex anchored to statement start. Every real defect that session
came from reading the code. Use scans to decide *where to look*; never report their output as a
finding, and when handing them to someone else, label them unverified and say the scanner has a
false-positive history.

**Mutation probe (does the gate fail when the code is wrong?)** Seed a small fault, run the gate,
confirm it goes red, revert. Do this for every assertion you care about. First-order mutants are
usually enough (the Coupling Effect — a hypothesis, not a settled result; the mutation-testing
literature treats higher-order mutation as open): invert a condition, delete a cleanup line, change
`>=` to `>`, make a validator `return 0`, drop a loop.

**"Red" means an assertion failed, not a nonzero exit.** pytest exits 1 for failed tests, 2 when
interrupted (xdist with `-x` reports a first failure this way), 4 on a usage error (`-p no:xdist`
against a config that passes `-n`), 5 when nothing was collected. A runner that counts any nonzero
exit as a kill once scored eight of eight on a usage error. Count a kill only on exit 1 *and* a
`FAILED` line naming a test, and print that line; a mutant whose failure is an exception from your own
malformed edit (a SQL error, a NameError) is broken, not killed.

**Novelty probe (does the gate fire on what doesn't exist yet?)** Write a *new* file containing one
instance of every class the gate claims to catch. Run the gate. Delete it. If the file was invisible,
your inputs are enumerated somewhere.

Do this work in a **copy of the tree**, never in place: a run killed mid-mutant restores nothing (a run
that died with its session left a planted mutant in the worktree, one commit from shipping). A session taking over checks every tree a mutation run used with `git status` first. If you
must mutate in place, verify the restore — a `git checkout` from the wrong directory fails silently,
and a safety mechanism you removed to test a guard is a safety mechanism that is now gone.

**And check the restore's SCOPE, not just that it worked — a revert wide enough to include the fix
under test reports the fix working.** Before each seed, assert that the fix is present in the tree and
that the suite is **green before the mutation**; commit the fix before running the harness over it,
and revert only the file you mutated. (Incident: `controls-that-lie.md`.)

Survivors of these probes are the real findings. Expect them to be embarrassing: in one audit, five of
nineteen seeded faults survived a suite that looked good, including "the cancel path triggers the
destructive action instead of aborting".

## Step 8: the assertion that cannot fail

- `[ ! -e "$file" ]` passes when the file was **never created** — so the cleanup you
  meant to test is unexercised. Verify the precondition really occurs.
- "Is the output parseable JSON" cannot fail if the code has a fallback that always
  emits parseable JSON. Assert a field you passed in.
- A pure-absence check on a tool's output passes when the tool **errored and printed
  nothing**. Pair every absence assertion with a positive control in the same test.
- Asserting on a **log string** couples the test to prose; a copy-edit makes it
  vacuously true. Assert on a counter, a status, or a value the code owns.
- A test that **skips** in the environment where it matters has zero coverage there.
  `[ "$EUID" -ne 0 ] || skip` in a root CI container means the privilege gate is never
  tested. Drop privileges (`setpriv`) instead of skipping.
- **In a hand-rolled runner, the summary line and the exit expression must be the last lines of
  the file.** Cases appended below them are left out of the counts *and* silently become the
  script's exit status, because a shell exits with whatever ran last — so a bare
  `[ "$fail" -eq 0 ]` sitting in the middle of a file gates nothing at all. One gate grew a new
  rule block underneath its own summary, stranded 8 cases outside the totals, and went on
  reporting green while printing a real failure on screen. A clean run cannot distinguish
  "correctly green" from "always green"; only injecting a case that *must* fail can. End with an
  explicit `exit`, and prove the non-zero.
- **For a monitoring rule, the mirror: the alert that cannot be QUIET.** Before trusting an alert,
  query its metric's history (`min_over_time` over retention) and confirm the quiet state has
  actually occurred; and check whether the signal **flaps** before choosing `for:` — when the
  emitter is slower than the evaluator, the window belongs in the expression. (Incidents and the
  second-metric fix: `controls-that-lie.md`.)
