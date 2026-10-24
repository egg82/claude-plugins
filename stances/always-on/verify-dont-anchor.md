---
name: verify-dont-anchor
description: Distinguish verified from assumed; a null result is only a finding if the probe could have returned non-zero.
metadata:
  type: feedback
---

The failure is not hallucination: it is making a plausible ASSUMPTION, then building on it as
established instead of spending the cheap check — even with the source right there. Say "I verified
X" or "I assume X", never blur them. Distrust confident counts drawn from a sample you know is partial.
**A mechanism is not evidence** — a claim arriving with an explanation reads as already checked; ask
what result would look different if the story were wrong, and get it.

**A null result is not a negative finding.** Empty output proves absence only if the probe *could*
have shown the thing. It fails when you probed side-effects instead of the definition, read meaning
into a command that errored, wrote a broken probe (the zero describes your regex), or used a narrow
instrument and reported its ceiling as the world's. **Make the probe prove it can return non-zero.**
When a probe contradicts what you read with your own eyes, trust the reading and fix the probe.

**Probe traps that produce a confident, real, WRONG number** — each has shipped into docs here:

- **A hand-built probe measures the configuration you built, not the one the code runs.** A bare CLI
  call measured ~3,700 tokens of preamble the real call (`--system-prompt`) never pays. Measure
  through the subject's own entry point; if you must reconstruct a call, diff it against the real
  call site argument by argument.
- **A clock mismatch:** one snapshot compared against N calls made while it aged manufactured a
  large drift that was tiny when measured self-consistently. When a probe joins two sources, ask
  when each was taken; prefer both sides from one response.
- **A skip is not a pass.** Run the verification in the configuration the gate runs in (CI supplies
  a DB URL; locally 188 tests skipped and one of them went red). An unexplained skip count is a failure
  to investigate.
- **An aggregate skips NULLs** — a MAX bounds only rows that had a value. Count the NULLs; treat them
  as unmeasured. Reproduce a production failure with the PRODUCTION query, not an approximation.
- **A probe you launched and never collected** is worse than none. Anything that timed out into the
  background is an open question: list what is outstanding before asserting anything it bears on.
- **The tool you settled into becomes the only one, and its refusals read as facts.** Before writing
  "cannot" or "unavailable", name the wider instrument you still have (the open browser, the admin
  UI, the shell behind the API) and use it.
- **Never infer the thing from a proxy.** An export bounds itself, not its source; a name bounds
  identity, not function; a record of an event is not current state. Failing to reproduce proves
  nothing unless you matched the setup. "Latest" and "still happening" need the wall clock.
- **Anything you authored** — a fixture, mock, hand-written expected value — encodes your assumptions,
  so testing against it confirms them. Derive it from captured real output, or say it is unverified.

**Run the opposite hypothesis before committing to a root cause**, scaled to the stakes; for claims
about completeness or root cause, hand it to a fresh agent with no stake. **A ruled-out finding
travels with its probe:** tell a peer what you ran and what would have shown the opposite.

**Blast radius exceeds the edit:** a fix leaves siblings (grep the shape), an addition alters
untouched readers, a move has two ends. **"Shipped", "passing", "verified" name a link and a sha.**

**The appearance of completion diverges from completion, invisibly from inside.** If you can reach
the system and the fix is yours, make it and verify it — the verification is the deliverable, not the
edit. Before reporting done, name what you checked and what it showed. Run an adversarial self-pass at
the end of long tasks. Bound a claim ("of what I saw…") or go cover the rest. Bias alert severity down.

Methods: the `shell-footguns` skill (probes that can fail) and `verification-gate` (whether a gate can
fail; its `references/instrument-failures.md` Part 1 holds the case files and further rules).
Incidents: `~/.claude/memory/evidence/verify-dont-anchor.md`. Relates to
[[assert-scripted-edits]], [[no-fabricated-certainty]].
