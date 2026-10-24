# Correctness oracles — the code disagrees with itself

Load on every hunt. The oracle here is self-consistency: the code, its siblings, its docs and its own tests already
state what it should do, so where two of them disagree at least one is wrong — no spec, no argument about intent.
Proof is a failing test or a repro script that shows the wrong value.

## Run what the project ships, first

Cheapest oracle per minute, and the one a hunt most often walks straight past. Mechanical and self-proving, and they
cost minutes.

- **Run the suite and read it as the executable spec.** Green says where the bugs *aren't*; a failing or skipped test
  says where someone already knew. Check `xfail`/skip markers and commented-out cases — a skipped test is a bug someone
  filed against themselves and lost. Then invert it: the behaviour with *no* test is where the defect lives, and
  "which public entrypoint has no adversarial-input test?" is a better lead than a page of reading.
- **Turn on what's configured but not enforced.** `go vet`, `staticcheck`, `-race`, `mypy`/`pyright` strict, `ruff`,
  `clippy`, ASAN/UBSAN, compiler warnings. On Go or Rust the race detector and vet usually outproduce an hour of
  reading, and findings arrive with a `file:line` and a mechanical argument attached.
- **Mind the error profile before you trust a zero.** A linter tuned to near-silence, a suite that never imports the
  module you care about, a checker in permissive mode: the clean result describes the configuration. Break something
  on purpose and watch it complain (`verification-gate` for the method).

## Differential — the same logic implemented N times

The highest-yield oracle and the one most often left unused. Per-provider adapters, per-platform backends, N similar
routes: **the implementations should agree, so where they disagree one is wrong.** Line the siblings up and diff the
*logic*, not the text — the same guard, null handling, ordering, error path. Look hardest at negations and boundary
operators: a `!` present in four siblings and absent in the fifth is a bug nearly every time. Divergence clusters, so
when sibling 3 is wrong check 4 and 5. A **log message that disagrees with the condition it sits under** is the same
oracle in miniature, and doubly worth reporting: the logs have been lying to everyone who debugged this before you.

**For a fork it is the primary oracle, and mechanical:** apply the patches, then `git diff base HEAD` per file is the
exact delta the fork introduced. Upstream's own equivalent code in the tree (a bundled reference implementation) is a
free line-by-line spec. The differential *labels* origin; it does not gate scope.

## Doc-vs-code, in the direction that bites

Trace a documented flag or behaviour to the code that consumes it. Not "is it wired" (repo-vet's dead-button pass) but
**"does it do what the sentence says"**: a setting that reaches a handler and does the opposite, is read into a variable
nothing branches on, or is consumed only on a path that cannot execute. The subtle instance is a knob unreachable *as
shipped* *(incident)*: a correct UID-remap behind an `if running as root` guard, in an image that drops to a fixed
non-root user at build time. Every piece was individually right; only "can this line execute as shipped?" found it.
Say which piece is wrong — "correct but unreachable" and "broken" get fixed differently.

## Invariants the code states about itself

If every other access to a field takes a lock, the one that doesn't is a bug you can point at without arguing
thread-safety in the abstract. Same shape: a resource closed on three paths and leaked on the fourth, a cleanup five
callers do and one skips, a nullable checked everywhere but once. You are showing the codebase agreed on a rule and
broke it.

## Contract tests written blind

Where siblings and docs are silent, the stated contract is the oracle. Hand a fresh agent only the interface and its
contract, never the implementation, and have it write tests and properties; whatever goes red is a lead the
implementation-aware tests could not see. *(incident)* In a habit-tracking app, a blind property test found an undo bug the
existing suite missed, and property tests written from a contract find real bugs at a measured rate
(`agentic-engineering` §5 and its `references/evidence.md`). A mutation pass over a module points the same oracle at the
tests: a guard whose planted mutants all survive is untested, and untested protective code is where to look next.
*(incident)* A guard that stopped a bad fetch from mass-deleting records had no test at all (`agentic-engineering`'s
`references/cases.md`).

## Lenses

- **Error and failure paths** — the best mundane yield: a bare `except`, a `catch` that logs and continues, an ignored
  error return, a shadowed `err`, the wrong exception type caught, a `finally` that masks the original, a retry that
  eats the terminal failure. Tell: the caller cannot distinguish success from silent loss.
- **Algorithmic cost on a hot path** — an O(n²) loop, a query without a limit, a whole-collection scan per item. These
  are first-class defects on their own merits, not the consolation bin for a demoted finding; measure them by
  `performance.md`.
- **Boundary and arithmetic** — off-by-one in slices and ranges, inclusive/exclusive mismatch, empty / one / exactly-N
  inputs, overflow and truncation, negative and zero, float where decimal belongs, unicode length vs byte length. Tell:
  a comparison or index whose edge nobody tested.
- **Concurrency and lifecycle** — TOCTOU, lock ordering, missed wakeup, iteration during mutation, cancellation not
  propagated, a task or connection leaked on the error path, non-reentrancy, a shared mutable default. Tell: state
  reachable from two schedulables where only one path was written with the other in mind.
- **Silent defaults that hide missing wiring** — a Null Object, a no-op fallback or an empty-list default stands in
  when a system was never registered, so the feature does nothing and nothing complains. *(incident)* one app shipped
  this twice (`agentic-engineering`'s `references/cases.md`). Tell: a default registered at import that no test
  replaces, or a fallback path with no log line.
- **Config and default semantics** — a wrong default, precedence in the wrong order (flag / env / file / default), a
  falsy-but-valid `0`/`""`/`false` clobbered by an `or`-style default, a units mismatch (ms vs s), validation after use.
- **Time, encoding, locale** — wall clock where monotonic belongs, timezone and DST assumptions, timestamp precision,
  normalization and case-folding, locale-dependent formatting or sorting on a machine path.
- **Crash oracle** — unguarded throw sites (cast, null-deref, index, division, recursion, get-or-throw) reachable from
  a user action, tick or async callback, then caught-and-logged vs escapes-the-loop. A *dedicated* pass, partitioned by
  surface; crashes are patch-fast. On a library: an exception outside the documented error hierarchy escapes a public
  entrypoint on hostile input — a property or fuzz pass proves the batch at once.
- **Round-trip fidelity** — serialize ↔ deserialize ↔ *migrate*: a strict throw that eats the batch, silent field loss,
  a count clamp, a format-version change that doesn't survive the trip back. The migrate axis is the one people skip.
- **Transaction and rollback integrity** — does cancel *fully* roll back? Tell: mutation before the event, a cancel
  branch that doesn't restore, effects committed before the check, a discarded return. The dupe/loss workhorse in a
  game economy; the same shape as a DB transaction whose scope ends before its side effects do.
- **Usage-driven / API-contract gap** — start from what real consumers *do* with an API and work back. Its unique yield
  is the internally consistent implementation (the differential saw nothing) that violates a consumer's reasonable
  assumption: immutability, thread-safety, cancel-rollback, round-trip, confidentiality. Platform fault is in;
  consumer misuse is out.
- **Systems in hiding — count the deciders, not the copies** — one *decision* (who is present, when a line is said, how
  often something may happen, what the user is told) made by several pieces of code each with its own rule, so nothing
  is literally copied. List the decisions the product makes, then every piece of code making each; more than one
  decider is a system in hiding, and a fix that had to touch N callers is the tell. *(incident)* On a booking app, copy-hunting
  found two discount calculators that shared constants and missed four reminder schedulers that shared nothing, found
  only when a one-rule change had to edit four callers.
