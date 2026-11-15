# Designing the check: the three shapes, history, boundary, generative inputs, lint rules

Load when you are deciding what a gate should check and where it lives (`SKILL.md` steps 1-3 and 9). `SKILL.md`
carries each step's rule; this file carries the worked detail, incidents and "why". Making the check able to fail
(steps 4, 5, 8): `making-it-fail.md`; harness and fixtures (6, 7): `harness-and-fixtures.md`; error profiles and
adoption (10, 11): `error-profiles-and-adoption.md`.

## The failure behind every green check: the three shapes

The question in `SKILL.md` (*what would this print if it could see nothing at all — and is that "pass"?*) is the
design-time twin of "make the probe prove it can return non-zero": that one is a control you run afterwards, this one is
a sentence you can apply to a check that does not exist yet.

Wire the blind case to a **third** outcome — `UNKNOWN`, non-zero, distinct from both pass and fail.
Not because it catches more, but because of what a passing blind check *does*: it converts an
unverified assumption into apparent evidence, silently, every run, for as long as nobody looks. A
history-based check written this way was about to be wired into a container with no `git`; the
`UNKNOWN` exit is the only reason its author did not see green and conclude the wiring was correct.
**A blind check that fails costs you a debugging session. A blind check that passes teaches
something false.**

Three real shapes, all found the hard way:

- **It examined nothing.** A checker globbed `<lib>/*.sh` non-recursively; a refactor
  moved thousands of lines into a subdirectory and they left its view entirely. The only
  signal was a *count* the gate printed — suppressions honoured dropped 8 to 5. Without
  that number it would have gone on reporting a clean pass over a fifth of the code.
  **Make a gate report what it examined, not just its verdict** — file count, rule hits,
  suppressions granted. A verdict alone cannot distinguish "clean" from "empty".
- **It stopped before reaching the thing it tests.** A test invoked a CLI end-to-end to
  prove a dispatch worked. The CI container runs as root, the program refuses to run as
  root, so the test stopped at that guard and passed — on a tree where all five paths it
  covered were dead. **A test that invokes a program end-to-end inherits every guard that
  program has**, and CI trips guards a developer's shell never sees. Exercise the unit, or
  assert you got past the guard.
- **It was right about the wrong thing.** A reachability rule flagged a module for calling
  a function defined elsewhere — correctly, except the module sourced that file itself. A
  static rule over a dynamically-loaded codebase must follow the loading, and decline to
  judge what it cannot resolve rather than guessing.

## Step 1: defect classes from the repo's own history

A class fixed **more than once, in different files** is the signature of a missing gate — someone patched the instance
and the sibling kept the bug.

```bash
git log --oneline --all | grep -iE 'fix|revert|hotfix|broke' | head -60
git log --merges --oneline -40                    # MR titles are often franker
git log -p -S '<suspect idiom>' --oneline         # when did this shape appear/leave
glab mr list --all --per-page 60 ; gh pr list -L 60
```

Read the diffs, not just the subjects. Cluster them. Rank by "has this bitten, and how
badly" — not by how neat a rule would be. In one real audit the dominant class was
*reporting success after a failed step* (5 of 11 MRs), which no first-principles list
had included; the pretty rules that got written first covered classes that had never
occurred.

Traps here:

- **Check the disposition of every citation.** A rule justified by tickets that turn
  out to be closed-as-intended is a rule that will fire on correct code forever. Open
  the ticket. No tool does this for you.
- **A class needs more than one instance, or it is a regression test in costume.** A
  grep for one literal string passes forever and catches nothing while looking like
  coverage.
- **When you find the class fixed once, `git log -S` the guard and check every site that
  commit touched.** The sharpest case is a commit that fixed some sites *while editing the
  others*: one audit found `mv` unguarded in both halves of an installer, and the commit
  that added exactly that guard to two siblings had edited these two functions, skipping
  the move eight lines below. Siblings, fix and omission, one diff.
- **Splitting a file creates a class that did not exist before it.** Symbols that shared a
  scope now cross a module boundary, and a lazily-loaded one is only missing at runtime:
  three shipped in one split — a dispatcher calling into five modules nothing sourced, a
  guard function called from a module that did not load its definition, and a variable read
  in the entrypoint but assigned only in one module, fatal under `set -u`. If you split
  something, add a check that loads each piece the way production loads it.

## Step 2: the boundary

Getting this wrong is the most expensive mistake available, because you end up trying to unit-test a
disk resize or hoping a linter catches a runtime contract.

| bucket | what belongs | what it costs |
|---|---|---|
| **Static check** | shapes in the source: a discarded exit status, an idiom that misbehaves on empty input, a config key that doesn't exist in the schema, an inventory that won't cover new files | cheap, instant, no environment |
| **Unit test** | pure logic and the *argument construction and gating* around a destructive call — validators, parsers, canonicalisers, retry ladders, slug builders | cheap if the code is reachable; see step 4 |
| **Integration / real host / VM** | the destructive call itself, external-service contracts, anything needing real state | slow, but the only thing that proves it |

The line is *what the test may mutate*, and the config-management world draws it
by directory, not by cleverness: Ansible says "don't unit test your playbook";
ChefSpec says outright it "can't actually tell you if a cookbook is doing the right
thing"; Puppet Litmus requires dedicated throw-away machines. **`lvresize` belongs in
the VM run — but the function that decides whether to call it, and with what, is a
unit test and should be one.**

And know what static analysis genuinely cannot see. Verified examples: shellcheck
finds *nothing* in a bash-4ism defect history (`declare -A` under `#!/bin/bash` is
legal; there is no bash-version target); kubeconform is blind to any field under
`x-kubernetes-preserve-unknown-fields: true`, which is where chart values and plugin
config live. Test the blindness before you rely on the tool.

## Step 3: generative, not enumerated

> Could this fire on code nobody has written yet, in a file that doesn't exist yet?

If the answer is no, it is a **characterization test** (Feathers) wearing a linter's
UI: it describes today's tree and can never tighten. Concretely:

- **Discover inputs, never list them.** Glob the directory; identify commands by
  shebang; derive the file↔check mapping from disk. A hardcoded list of seven files
  means the eighth is silently unexamined — and the hook may still *run*, reporting a
  clean pass on a file it never opened.
- **Invert allowlist-shaped defaults.** `STRICT = {…}` exempts anything unlisted.
  List the *exceptions* (`EXEMPT = {…}`) so a new thing gets the strict standard by
  default. Defaults-not-matching-intent is the single largest complaint developers
  report about analyzers (Christakis & Bird, ASE 2016).
- **Don't anchor patterns to statement start.** Calls hide inside one-line function
  bodies and after `&&`. `^\s*err\s+"` misses `f() { err "…"; }`.
- **Refuse to report a clean pass on an empty input set.** If the check found fewer
  files than the repo must contain, exit non-zero with "I examined nothing". This is
  the failure mode users hate most and nobody instruments.
- **Force a decision on new additions.** "Every function in the module is classified
  as wrapper / viewer / probe" fires on the commit that adds an unclassified one. That
  is a completeness invariant on your own config, and it is the good kind of
  structural rule.
- **When agents write the code, a different agent writes the tests, from the contract.**
  Tests an agent writes for its own change were measured to change nothing (arXiv
  2602.07900: mostly print statements), while LLM-written property tests from a stated
  property found real bugs (arXiv 2510.09907). So: properties derived from the written
  contract, each tagged with the clause it checks (a failing property may be a contract
  bug, not a code bug), by an agent that never saw the implementation. Isolation measurably
  helps (`agentic-engineering`'s `references/evidence.md`); whether a co-written suite beside
  the blind one adds anything is unmeasured, so write one suite per contract and check it with
  the mutation probe (step 5, `making-it-fail.md`).
- **For an HTTP API, this step is the `api-contract-first` skill's "The tests worth having"**: each
  iterates a population read from the served schema (every endpoint, every field, every error) and
  asserts that population was non-empty.

## Step 9: a rule that survives a deadline

For lint rules specifically, precision beats coverage — trust is the currency and false positives
spend it permanently:

- Score a rule on **developer action**, not analyzer correctness. Google's "effective
  false positive" is *any report where the user chooses not to act* — a true finding
  nobody fixes counts against you.
- **A blocking rule gets a zero-FP budget**; a commenting rule gets roughly 10%
  (Tricorder, CACM 2018; convergent with the ~20% false-positive rate Coverity reports as *typical for its
  stable checkers* — not a blanket ceiling — noting "when
  forced to choose between more bugs or fewer false positives we choose the latter").
- **The first two or three findings set the reputation permanently** (Bessey et al.,
  CACM 2010: "if the first N reports are false positives (N = 3?), people tend to utter
  variants on 'This tool sucks.'"). Ordering matters more than the aggregate rate.
- **"Is the fix a one-liner?" is a rule-quality criterion.** Error Prone's bar for
  on-by-default is "swap these arguments", not "introduce a subclass". A finding whose
  cheapest resolution is a ritual (an empty test file to satisfy a coverage rule) is
  an effective false positive even when true.
- **Prefer error-or-nothing to a warning tier.** A tier people may ignore will be
  ignored, and then trains them to ignore the channel.
- **Never overload a construct that already means something.** A suppression must be
  an inert comment naming the rule and a reason — `# no-check: <rule> - <why>`. Reusing
  `|| true` as an opt-out silently grants amnesty to every pre-existing instance and
  makes "I wrote this deliberately" indistinguishable from "I wrote this to shut you
  up". Print the suppressions you honour so the debt stays countable, and flag stale
  ones (`--warn-unused-ignores`, `RUF100`, `nolintlint`).
- **Don't hand-roll what exists upstream.** A local "shebang without +x" rule is
  strictly worse than `pre-commit-hooks`' `check-shebang-scripts-are-executable`,
  which covers the whole repo for no code.
