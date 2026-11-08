---
name: home-dir-layout
description: Never create directories or loose files directly in ~; scratch, worktrees and cleanup holding each get one conventional home
metadata:
  type: feedback
---

**Never create a directory or loose file directly in `~`.** Left to improvise, each session invents its own
top-level spot, and a home directory ends up with a hundred screenshot dirs, probe dirs and bundles.

- **Scratch** (screenshots, probes, venvs, notes, downloads for research): `~/scratch/<project>/<topic>/`. The
  session scratchpad is `/tmp`, which a reboot empties, so durable scratch goes here instead.
- **Git worktrees:** `~/worktrees/<repo>-<branch>/`.
- **Cleanup holding** (things moved aside instead of `rm`, per [[preserve-before-destroying]]):
  `~/scratch/.holding-YYYYMMDD/`; sweep it once nothing has asked for its contents back.
- Remove your own scratch and worktrees when the work merges; a path a doc, skill or memory points at is not scratch.

These paths are a suggested convention; substitute your own, but keep to one. Relates to
[[assume-the-checkout-is-shared]].
