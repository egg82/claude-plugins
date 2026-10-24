---
name: skill-authoring-craft
description: "Writing and evaluating skills: live-system skills script the EDGES (gather JSON → model judges in prose → dry-runnable apply), record no-op verdicts, and eval baselines are never unguided"
metadata:
  type: feedback
---

**Skills that touch live systems: a script gathers into JSON → the model judges in prose → a script
applies, with `--dry-run` on write paths.** Structure sits on the input and action sides; the
judgment is the deliberately unstructured middle. Don't invert it into "model emits structured
findings → script renders a report": when the deliverable is an action against a live system, the
action must be deterministic and replayable, and a rendered report is a byproduct nobody reads.
Without this shape a skill defaults to markdown-only (judgment evaporates, nothing replayable) or
schema-first (fixed fields inflate short findings). Encoding the judgment in code makes it brittle.

**Record the no-op verdict.** Where re-running is the point AND the common verdict writes nothing,
the skill needs a decisions ledger: an acting verdict persists itself, "looked, it's fine" leaves no
trace and gets re-derived every run — burning fan-out, crowding a capped candidate list, sometimes
landing on a different, wrong answer. Record evidence, not just a verdict, and never let an
unattended/scheduled run write the ledger — an unreviewed entry hides an item forever.

**Eval baselines are never unguided.** A subagent inherits CLAUDE.md, global memory and the memory
index, so a "no-skill" arm measures the skill's **body** against its **description** plus everything
ambient. Read a small with-vs-without delta as "the description already carried it", not "the skill
is useless". Use opaque run names for A/B arms ([[subagent-paths-prime-results]]).

Pairs with [[prefer-subtraction]] and [[user-forcing-function-style]].
