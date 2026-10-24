# Brief hazards — how a well-meant child returns nothing, leaks, or makes your decisions

Load before briefing any child that runs slow work (suites, builds, long probes), handles credentials,
touches a live system that needs approval, or might spawn. `SKILL.md` §2 lists the one-line rules.

## Backgrounding — the commonest empty return

**Forbid backgrounding explicitly, or a child doing slow work delivers nothing.** The child launches its
work with `run_in_background` (or arms a `Monitor`), then ends its turn to wait — and a child's turn
ending IS its completion, so the parent receives a completion notification whose entire content is
*"waiting for the background task before grading."* The work usually finished moments later, ungraded and
unreported. *(incident)* This hit **four separate children in one session**, two of which had already
been told not to use a foreground `sleep` — forbidding only `sleep` leaves backgrounding as the obvious
remaining way to wait, so that instruction alone steers them into this. Write all three: *"do NOT use
`run_in_background`, do NOT start a `Monitor`, do NOT use foreground `sleep` — make blocking synchronous
calls in small batches (4-6), read each batch, then run the next, so the results are in hand when you
report."* When a child does return a "waiting for…" message, **resume it by name rather than
respawning** — its context and its finished work are intact, and a fresh agent would redo the calls.

**Forbidding it is not enough when the work is long: the harness backgrounds it for them.** A foreground
Bash call that outruns its timeout (default 2 min, max 10) is moved to the background automatically, and
the child then waits on it exactly as if it had asked to. *(incident)* Four children briefed
with all three prohibitions still returned "waiting on background work", each because a full test suite
(7–10 min) crossed the default timeout. So for any child that runs suites or builds, the brief must also
say: *"pass `timeout: 600000` on long commands, and split work so each call finishes inside 10 minutes
(e.g. one test directory per call)."*

## Credentials in argv

**Tell a child never to run `ps` while credentialed commands are in flight.** A child that runs `ps aux`
— to check on its own background job, say — while an HTTP request carries a bearer token on the command
line prints the live token straight into its transcript on disk. Credentials in argv are readable by
anything on the box, so the brief can prevent this with one sentence — and better still, hand the secret
over by file or environment variable (a config file, or an `@file` header form) so argv never holds it at
all. A `ps` listing is a credential surface in general, not only for children.

## Spawning and forks

**Tell it whether it may spawn.** Default to *"you are a LEAF agent: do not spawn subagents"*. An agent
told nothing re-delegates reflexively.

**That sentence is advisory; nothing enforces it.** `agent-depth-gate.sh` lets a depth-1 agent spawn by
design, and a fork counts as a spawn it permits. *(incident)* A "LEAF" writer spawned a fork for a
one-line connectivity probe; the fork edited the parent's files, dropped the parent's working database,
and ignored two stop messages. A fork inherits everything the parent holds — worktree, containers,
credentials in context — so name "no forks" explicitly, and treat a child's report of a helper as a
signal to check its resources, not as colour.

## Refusals and permission-gated work

**Say what to do when an action is refused.** *"If the permission classifier denies something, do not
route around it; say what you needed and carry on without it."* A child briefed only with the goal treats
a denial as an obstacle. *(incident)* Denied a credential read, one pulled the data out another way. It
was well-behaved and read-only, and it was still the user's decision being made for them.

**Permission-gated work cannot be delegated — approvals do not cross into a subagent.** The auto-mode
classifier decides using the USER'S MESSAGES IN THE CURRENT CONTEXT. A subagent has its own context and
its own message history, and the user's approvals are not in it. So a permission the user granted *you*
does not reach a child, and **you cannot grant it on their behalf** — the same boundary as permission
laundering, seen from the other side. Work that needs an approval must run in the session where that
approval was given. (A child that spent 35 minutes on denials the parent cleared in four:
`brief-incidents.md`.)

- **The tell is silence, not an error.** Nothing in the parent's view distinguished "working carefully on
  a live IdP" from "looping on denials". The child was never going to finish, and would have burned its
  whole budget looking busy. If a child on credential-adjacent work has produced nothing after a few
  minutes, **check the external system for its effects** rather than waiting — and give the probe a
  control, so an empty result means absence rather than a broken check.
- **Do the credential-adjacent step yourself; delegate the parts around it.** Token minting, IdP and
  registry configuration, secret-store writes, anything a classifier could read as credential handling —
  keep in the parent. Research, file authoring, manifest generation and verification all delegate fine.
- **Trying it yourself after a child was denied is not laundering.** Laundering is routing *your* denial
  through someone else. A child's denial is a fact about the child's context; running the call in the
  context that actually holds the approval is the correct move, and often the only one.
- **When you retake a child's task, stop the child first.** Two actors creating objects in one system is
  how you get duplicates in something that must be created once. Kill it, then re-check the target for
  anything it landed late, before you create.
