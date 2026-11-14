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
  `~/scratch/.holding-YYYYMMDD/`; sweep the items you put there, by name, once nothing has asked for them back; never delete the whole
  directory in one go. **Never sweep it in the session that filled it**, even when told "delete them": a reference scan
  misses citations written as globs and docs sitting beside the item, and a cleanup can lose a remediation script that way.
- Remove your own scratch and worktrees when the work merges; a path a doc, skill or memory points at is not scratch.

These paths are a suggested convention; substitute your own, but keep to one. Relates to
[[assume-the-checkout-is-shared]].
