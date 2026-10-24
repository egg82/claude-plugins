---
paths:
  - ".claude/projects/**/memory/**/*.md"
  - ".claude/memory/**/*.md"
  - "**/.claude/projects/**/memory/**/*.md"
  - "**/.claude/memory/**/*.md"
---

# Before writing or editing a memory file

> **This file loads on READ, not on WRITE.** Path-scoped rules are not injected when a new
> matching file is *created* (anthropics/claude-code#23478, closed as not-planned), so this rule
> is absent at exactly the moment a new memory is written. The `memory-write-gate` PreToolUse
> hook is the deterministic backstop — it rejects any memory that neither carries a `check:` nor
> declares `type: user`/`type: feedback`, untyped notes included, and it blocks an edit that
> *removes* a `check:`. `*/MEMORY.md` is always exempt. It also refuses a write it cannot
> *read* — a payload naming a memory file but carrying no content, `new_string` or `edits[]` the
> hook understands — because the alternative is judging the change by the file's OLD contents.
> `MultiEdit` is covered: its fragments live in `edits[]`, not at the top level.
> Treat this file as the explanation; treat the hook as the enforcement.


Every rule here has a failure behind it. They're included because a bare directive gets skipped
under pressure and a directive with a scar attached doesn't.

## First: does this belong here at all?

Memory is the **last** resort. A fact about a file belongs in a doc beside that file; a fact
serving a skill belongs in that skill; a per-item verdict belongs in a keyed log. See
`knowledge-routing`.

**Why this needs stating:** memory is the destination the harness names, so it wins by default even
when it's the worst fit. Left alone, that default accumulates project status journals, build logs
and operational runbooks in a store meant for cross-cutting facts — none of which are memories, and
each of which had an obvious better home at the moment it was written.

## Keep it short, keep the Why

Write memories tight, but keep the Why and How-to-apply on `feedback` and `project` notes — make them
concise rather than dropping them. The length target is the tightest note you already have: pick one
and match it, rather than aiming at an abstraction.

## The probe test — it decides routing mechanically

A memory describing a system **must** carry a `check:`: a cheap, read-only, non-interactive command
that would prove it wrong.

```yaml
---
name: <tool>-owns-<thing>-config
check: "ls -d ~/<gitops-repo>/*/<tool>"
type: project
---
```

**Why:** an audit found memories asserting things that had stopped being true — an app named the
wrong cluster (it had moved a day after the memory was written), a memory declaring a stack
"★ PROJECT COMPLETE ★" that had been torn out days later, an automation named as a systemd timer
that was disabled and replaced by a scheduled job, a migration recorded as "BLOCKED — do NOT
enable" that had shipped weeks earlier. **Every one had a sub-second probe that would have caught
it, and none needed judgment.** `kubectl get ns <the-namespace>` would have taken 200ms.

**If you cannot write a probe, it is not a memory.** It's a genuine preference (`prefer-subtraction`
has no falsifier — correctly), or, far more often, a fact that belongs *with its subject*, where the
subject's repo makes it checkable. Take that branch and don't write the memory.

**Probe the BEHAVIOUR, not the precondition.** A memory saying "a single-instance CNPG cluster
blocks a node drain" is about how CNPG behaves — it stays true whether or not you currently have
one. Probing `does a single-instance cluster exist?` makes the memory report stale every time the
fleet is *healthy*, which trains you to ignore the checker. If the only probe you can write tests
whether the situation currently applies rather than whether the claim holds, that's a signal the
fact is **method** and belongs in the relevant skill, not in memory.

**Only `project` and `reference` memories need probes.** `user` and `feedback` are preferences,
stances and physical facts — they have no falsifier by design. **A forced probe on one of those is
worse than none**: it passes forever, proves nothing, and makes the scheduled check report green
over a claim nobody has validated. False confidence bought with real effort.

**When a fact genuinely can't be falsified by a command but *is* about a system, say so
explicitly** with `check: "n/a — <reason>"`. That distinguishes *deliberately unprobeable* from
*nobody got to it yet*, which are otherwise identical to a checker and to a future reader. Real
reasons that qualify: physical measurements you'd re-measure rather than query, browser-session
state, research notes making no claim about a live system, and a file whose individual entries each
state their own verification (a probe on the container would be circular).

**Probes must not depend on an interactive shell.** `command -v <tool>` over `ssh -o BatchMode=yes`
fails for tools that exist, because a non-interactive shell never sources the profile that puts
`~/.local/bin` on PATH. That exact probe reported a correct memory as stale within a minute of being
written. Use explicit paths (`ls .local/bin/glab`), and when a probe fails, **suspect the probe
before the memory.**

## Verify coverage by concept, never by phrase

Before deleting a memory as "already covered", confirm the target actually covers it — and search
for the *idea*, not a string.

**Why:** a grep for `"raw, not padded"` returned 0 against a file that said `RAW aspect` — the fact
was fully present and nearly got duplicated. Separately, `grep -E "a\|b"` returned 0 for everything
because `\|` is a literal pipe in ERE, and that silently produced a whole table of false gaps. **A
zero from a probe you wrote is a fact about your probe.** Make it prove it can return non-zero.

## Hard limits — exceeding them drops content at load

`MEMORY.md` loads only its **first 200 lines and first 25KB**. Past either cap, content is **not
loaded at all**.

It is not silent, but the signal is easy to miss. Claude Code measures the index after Claude writes
it: past **80%** of either cap it asks for a compaction to under **70%**; over a cap the write still
succeeds and Claude Code returns an `Error:` telling Claude to rewrite the index. Separately, a
`> WARNING:` line is appended to the truncated content at load. Both are tied to Claude's own write
and load — nothing is claimed about a hand-edited file.

**Why this is urgent rather than tidy:** the failure mode isn't a nag you can ignore for a while —
it's entries silently ceasing to exist while the file still looks completely normal. An index that
has drifted past the cap gives no indication that the bottom of it stopped loading.

Keep the index a **router**: one short hook plus a link, never content. Growth means move entries
out — *not* compact the hooks, which on a synced fleet makes each host rewrite them differently into
a whole-file divergence.

**`check:` may sit at the top level or nested under `metadata:`.** The harness normalizes memory
frontmatter on write and may move it, so both the gate and the checker accept either form. Don't
"fix" a nested one.

## Deleting beats updating

**Why:** a stale doc a human skims and ignores is one an agent reads as **ground truth and
propagates into code**. Published work also finds bounded memory beats unbounded by wide margins.
Never leave a memory describing something removed or replaced — that is strictly worse than having
nothing.

## On a synced fleet, delete everywhere in one pass

*Applies only where config is mirrored by an rsync-style union sync. If it crosses by git, skip to
the `rm -f` paragraph, which is universal.*

Union sync **never deletes**. Anything removed on one host is resurrected from a peer on the next
run unless removed on all of them.

**Why the batching matters:** a per-item `ssh` loop is worth avoiding regardless — sshd's
`MaxStartups` will throttle a burst, and the resulting `banner exchange` timeouts read exactly like
the host being down. But note how that diagnosis actually went: it was asserted repeatedly because
it matched a known pattern, and the real cause turned out to be the client machine sitting on an isolated
network. **Matching a known pattern is not evidence.** The tell was ignored — a throttle that
clears in seconds does not explain six consecutive failures then six consecutive successes with no
backoff between them. Batch the deletions into a single remote script per host.
Also note `rm -f "-<encoded-path>/x.md"` **fails**: Claude Code encodes a project directory's
name from its absolute path, so on some layouts those directory names begin with a hyphen, so `rm`
parses the path as options while `[ -f ]` on the same string succeeds — a naive loop reports
deletions that never happened. Use `--` or absolute paths, and check the exit status rather than
counting attempts.
