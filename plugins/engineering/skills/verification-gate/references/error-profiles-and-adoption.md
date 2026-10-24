# Error profiles, adoption checks, sources

Detail behind `SKILL.md` steps 10 and 11.

## The error-direction evidence (step 10)

A wrong verifier does not fail neutrally — it misleads, and a wrong critique gets acted on about as
readily as a right one. So establish a check's **error profile** before relying on it: does it cry
wolf, or does it wave things through? The two are not symmetric and they call for opposite
responses. The same self-checking technique has measurably helped in one domain and destroyed
performance in another: an **84.45% false-positive rate** on Blocksworld (*Can Large Language Models
Really Improve by Self-critiquing Their Own Plans?*, <https://arxiv.org/abs/2310.08118>, Table 2)
against a **95.8% false-negative rate** on graph colouring (*On the Self-Verification Limitations of
Large Language Models on Reasoning and Planning Tasks*, <https://arxiv.org/abs/2402.08115>). The
method was not the variable, the domain was.

**Quote that pair carefully.** The two figures come from different papers four months apart, and in
the later one's own Blocksworld row the FPR is 18.55% — so it is evidence that the error *direction*
is domain-dependent, not a within-experiment comparison. `config-hygiene`'s
`references/collaboration-and-enforcement.md` carries the full caveats, including what not to quote
from 2310.08118; read it before requoting either number.

## A gate's "am I inert?" signal computed from its filtered input (step 10)

- **A gate's own "am I inert?" signal must not be computed from the gate's filtered input** — or it
  reports on the filter and calls that a verdict about the world. A Stop hook that warned "no
  tool_use entries parsed; this is INERT, not clean" counted only tool_use inside lines passing a
  keyword pre-filter, so two ordinary sessions tripped it: one whose turns were all plain text (no
  tool calls to find) and one that made 37 real calls, all to tools absent from the keyword list.
  Across 462 stored transcripts the branch would have fired 12 times, every one of them false and
  none for the reason it existed. Derive the health count from the *widest* structure the scan
  depends on — here, message blocks of any type — so "I saw nothing" and "there was nothing" stay
  distinguishable. And check the pre-filter is buying what you think: this one saved nothing
  measurable (~0.33s to parse the 87MB transcript either way) while creating the bug.

## The adoption checks nobody thinks to run (step 11)

- **Does one job actually execute?** A pipeline can produce four runs and zero executed
  jobs — stale runners, and `only_allow_merge_if_pipeline_succeeds: false` means red
  wouldn't block anyway. Ship it noisy-but-running before shipping it blocking.
- **Does it match how code arrives?** A `merge_request_event`-only job in a repo with
  merges forming a small fraction of a repo's commits covers only that fraction of changes.
- **Is the tooling pinned?** An unpinned linter in a blocking job turns the default
  branch red with no code change.
- **Is the diff computation correct under CI's clone?** A shallow clone (`GIT_DEPTH`)
  breaks `git diff origin/main...HEAD` when the merge base is deeper — and a `|| true`
  then turns the failure into a green "nothing changed". Use the platform's
  merge-base variable, filter deletions (`--diff-filter=ACMR`), and fail when the file
  count is zero for a non-empty diff.
- **Is the gate's own code tested?** Hundreds of lines of check logic with no fixture
  suite is the same unverified code you are asking others not to write. The best
  pattern seen in the wild: the check runs its own tests *before* gating, and carries a
  canary (a minimum expected match count) so it fails if its parser goes blind.
- **Is an invariant BETWEEN two artifacts actually tested?** Two files that must agree — a helper
  duplicated across a reader and a writer, a hook and the doc listing its rules, a schema and its
  fixture — drift silently, because nothing executes the agreement. A sync tool's `apply.py` carried
  the comment *"Must match gather.py's set exactly, or a recorded hash never matches the one gather
  computes"*, and then did not match it: every item carrying a `__pycache__` recorded a hash the
  reader could never reproduce and reported `changed` forever, however many times it was recorded.
  The comment was correct, prominent and load-bearing, and prevented nothing. The tell is that the
  failure looks like ordinary staleness rather than a bug, so it gets re-recorded instead of
  diagnosed. Compute both sides and compare them in a test, or delete one copy and import it. A
  sibling gate suite does this well: it fails when the hook's rule ids and the skill's documented
  ids disagree, so the two cannot part without something going red.

## Sources worth reading directly

Sadowski et al., *Lessons from Building Static Analysis Tools at Google* (CACM 2018) ·
Bessey et al., *A Few Billion Lines of Code Later* (CACM 2010) · Beck, *Test Desiderata*
· DeMillo, Lipton & Sayward (IEEE Computer 1978, coupling effect) · *Software Engineering at
Google* ch. 11-14 (test sizes, doubles, larger tests) · Meszaros, *xUnit Test Patterns*
· Christakis & Bird, *What Developers Want and Need from Program Analysis* (ASE 2016) ·
Luo et al., *An Empirical Analysis of Flaky Tests* (FSE 2014) · Fowler,
*Eradicating Non-Determinism in Tests* · van Deursen et al., *Refactoring Test Code*
(test smells) · bats-core docs (`run` semantics, `bats_pipe`) · ShellCheck SC2314
