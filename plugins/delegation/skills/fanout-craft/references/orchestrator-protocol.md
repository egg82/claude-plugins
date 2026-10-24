# Orchestrating peer sessions: the idle protocol, and verifying peer hand-offs

When running as orchestrator over peer Claude sessions, **the whole fleet can go idle with work
outstanding and nothing will ever wake it.** A peer that finishes and has no armed waiter just
stops; so does the orchestrator. The user then has to notice and poke someone, which is the job they
delegated.

**The protocol, as the user set it: peers tell the main session when they are done AND have nothing
waiting that should wake them — so the orchestrator knows it must send work.**

- **Peer, on finishing:** send *done, nothing armed* or *done, waiting on X*. Not bare "done" — the
  distinction between waiting and inert is the entire signal.
- **Peer, on arming a waiter:** say so then, not only when finishing. A peer sat on a harness-tracked
  waiter for hours without mentioning it, and from outside that is indistinguishable from inert.
- **Orchestrator, on receiving it:** send work, or say plainly that resting is correct. Never leave
  the fleet parked and looking busy.

**Re-send it after every compaction, and do not rely on that.** It is a conversational agreement, so
it lives only in context and compaction eats it — three times in one night across three sessions.
Anything that must be remembered after a context reset eventually will not be, so **also write it
where the peer reloads it**: the working repo's `CLAUDE.md`, which auto-loads for any session in that
directory. Prose in a chat message is the weakest possible home for a rule that must survive
compaction ([[knowledge-routing]]).

**The same applies to the work queue, not just the protocol.** A session that compacts mid-queue
loses the queue, because it only existed in its scrollback — so the queue belongs in a repo file too
(`NEXT.md`), with enough reasoning per item that a reader with no context can evaluate it rather than
re-litigate it.

**The tell that it has already failed:** you are composing a status summary and no peer has messaged
you in a while, or the user asks whether the idleness is intentional. Before ending a turn where a peer
might be finishing, ask what is armed — theirs and yours. A harness-tracked waiter
(`run_in_background`, `Monitor`) is the only thing that reliably wakes a session;
[[shell-gotchas]] covers the detached-process version of the same trap.

**Duplicate the wake-up rather than dividing it.** Two sessions each assuming the other owns a step
is the failure that produced most of this. When a handoff matters, arm your own backstop *and* say
that you have, so the redundancy is visible instead of looking like distrust.

**Verify anything a peer hands you before passing it to the user — and a GOOD peer is the dangerous
case.** Three times in one session I relayed a peer's value unchecked and each was wrong: a list of
"the user's open items" (two already settled, so the user had to correct me), a claim about which gate was
blocking a merge (the project setting was the opposite), and an image tag one character short (CI
builds `g` + 8 hex; a person copying it gets an ImagePullBackOff with a name that looks right). Every
one was a cheap check I had already run correctly earlier in the same session.

The mechanism is not sloppiness, it is that **a peer report arrives structured, confident and
sourced, so it reads as already-verified** — the same thing [[verify-dont-anchor]] says about a claim
that comes with reasoning attached. It got worse *because* the peers were good: they caught several
of my errors that day, so their reliability was high and relaying felt safe. **High peer accuracy
raises the cost of the misses rather than lowering it**, because nothing in the exchange looks
different when one is wrong.

Two specifics that carried the whole failure: **a peer's list of the USER's open items is the worst
thing to relay** — you have no independent basis for any of it and the user is the only authority;
ask the user or say who told you. And **never construct or retype an identifier a peer wrote** — read it
off the artifact (`git rev-parse`, list the registry tag), because a truncated sha and a correct one
are indistinguishable by eye.

**How to apply:** treat "all peers quiet" as a state to act on, not a lull.
