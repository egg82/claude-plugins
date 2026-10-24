---
name: fanout-craft
description: "How to delegate to subagents or peer sessions so it stays affordable and nothing gets lost — the brief, model per agent, breadth over depth, durable findings, collecting results, reading a run's cost. Use BEFORE spawning subagents for research, sweeps or parallel investigation; before setting up a controller session over other sessions; and when a fan-out returned less than it should. NOT whether you may fan out."
---

# Fan-out craft

The authorization to fan out is a standing one and lives in memory. This is the method: how to spend
that authorization without burning a rate-limit window or losing the work at the end.

**The cost model, because it is not intuitive.** A fan-out costs roughly `agents × turns × context`.
The first term is the one people watch and the last is the one that bites: every agent re-reads its
entire context on every turn, so a research agent that has fetched twenty pages pays for those twenty
pages again on turn 21, and on turn 50 — one research run spent 57% of a five-hour Max window this way.
Cached input is discounted (0.1x), not free.

The lever with the best ratio is therefore **turns and context per agent**, not agent count. A wide,
flat fan-out of short-lived agents is cheap. A narrow, deep one of long-lived agents is not.

**Builders hit the same wall by being resumed.** A writer handed follow-up after follow-up (measure, then
fix the ceiling, then clean the history, then rebase) grows into the deep shape, for hours (the user's observation: very
large, long work on one subagent usually uses more tokens than splitting it up). Split at the brief: one bounded item
per agent, and a follow-up that doesn't need the agent's accumulated context goes to a fresh agent with a
short handoff (branch, sha, what's left). Resume only for a quick fix inside what it just built.

**More often they get there on a single brief** — nearly every very long agent measured was never
resumed. Their briefs were already "steps", but each step was still open-ended ("tune
until green") or several items in one ("fix D1–D4", "build X and Y"). Size a step the way a reviewer sizes
a PR: one item, with a stop condition the agent can check. When the stop condition is "until it
works", also give it a budget and a handoff file to write when the budget runs out.

**Which reference to load:**

| situation | file |
|---|---|
| quoting a model ratio, or doubting the §1 rule after a model release | `references/model-choice-evidence.md` (re-measure with `model-golf`) |
| briefing a child that edits code or owns resources | `references/brief-writers.md` |
| briefing a research, review or audit child | `references/brief-readers.md` |
| a child that runs slow work, touches credentials or approvals, or might spawn | `references/brief-hazards.md` |
| a brief rule sounds arguable | `references/brief-incidents.md` |
| starting or driving a peer session (§4b) | `references/peer-sessions.md` |
| coordinating several peer sessions | `references/orchestrator-protocol.md` |

## 1. Choose the model per agent

**Read this section's own failure first, because it is the one that actually happens.** This rule and
its measurements have been in this skill, correct, and a 14-agent fan-out was still run with `model` omitted on
every single call — so all 14 inherited the session's Opus, at a cost that hit the session cap. Most of
those agents were bounded single-source work that sonnet clears at 94%.

The lesson is not "the guidance was missing." It was resident, in a loaded skill, named explicitly by
the memory that authorises fan-out. **Omitting `model` is a decision that does not feel like one** —
inheriting is silent, costs nothing at the call site, and shows up only on a bill. So treat an
unspecified `model` as an error in the brief, the same way you would treat a missing output path.

**That is now enforced, not advised.** The delegation plugin's `spawn-model-gate` hook is wired as a
`PreToolUse(Agent)` hook and blocks a spawn that omits `model`. Two exemptions: `subagent_type: "fork"`
(a fork ignores a `model` override by design, so the rule cannot be satisfied) and an agent type whose
own definition sets `model:` in its frontmatter (the definition is the deliberate choice). It separately
blocks a Fable caller spawning Fable, explicitly or by inheritance, and it fails open on anything it
cannot parse.

**It also refuses `opus` unless the prompt says why.** Naming opus is no longer sufficient: the spawn
must carry `[opus: <reason>]`, because opus subagents have been the largest single line of usage on
a typical setup by a wide margin (record your own dated figures and re-measure command in
`~/.claude/local/fanout-craft/instance.md`). Sonnet or haiku need no justification. The token is greppable, so whether the
stated reasons were real is itself auditable later — and one edit is the whole cost of overriding it,
which is deliberate: this is a nudge with teeth, not a prohibition.

The `Agent` tool takes `model` (`opus` / `sonnet` / `haiku` / `fable`); the default is to inherit the
session's, which is exactly what the gate above refuses — name one.
**It does NOT take `effort`** — that parameter exists on `Workflow`, not `Agent`, and passing it to a
spawn is silently dropped, so the agent runs at the session effort no matter what the call says. Don't
label a run with an effort it never had.

**The measured tables** (opus / sonnet / haiku with model varied and everything else held identical;
on bounded single-source work sonnet passed 94% to opus's 100%, and on the Opus 5.5 re-run all three
tied) are in `references/model-choice-evidence.md` — read it before quoting any ratio. To re-measure on
your own workload after a model release, use the `model-golf` skill. What the runs show, in one line each:

- **Cheap models hold on bounded single-source work and break on multi-source aggregation.**
- **Judge by cost, not token count** — haiku took more turns and was still cheaper.
- **On open-ended work opus expands scope** (half its extra findings came from files outside the
  package it was told to examine). Bound the scope explicitly in the brief when you spawn opus.
- **On a subscription the constraint is the one weekly pool**, and the per-model meter is a sub-cap
  on it, not a separate allowance.

So: **haiku for bounded, verifiable, single-source work; sonnet as the default worker; opus when the
agent itself must decide what "done" means** — synthesis, ambiguity, cross-source aggregation.

## 2. Write the brief

**Name the skill, don't summarize it.** A subagent that merely sees a skill in its listing usually does
not open it — measured at 9 of 25 on one fan-out, every one of which had it listed. Write *"load the
`<name>` skill first"* into the prompt. Don't paste the skill's rules into the brief instead: that copy
drifts the moment the skill is edited, the same defect as a button wired to nothing.

**Constraints in the brief land; constraints elsewhere often don't.** This is the single most reliable
finding about briefs. Anything the run genuinely depends on goes in the prompt text, even if it is also
written somewhere the agent theoretically reads.

**When the target exists as an ARTIFACT, brief against the artifact — never against someone's list
about it.** A screenshot of the desired result, a reference implementation, a captured known-good
output: hand the child the thing itself and say "match this". A summary of it, however good, is a
lossy projection, and the agent optimises the projection. (A reviewer's thirteen-item list that never
mentioned structure: `references/brief-incidents.md`.)

The tell is a brief that cites a document when a file would do: "per the review", "as the notes say",
"following the audit". If the artifact is on disk, name its path and make matching it the acceptance
criterion. Keep the summary as a ranked hint about *where to start*, not as the definition of done.

**The harder version: the summary you wrote YOURSELF, from memory, with no document to notice.**
The tell above assumes a write-up exists to point at. It does not fire when *you* are the write-up —
and recalling something well feels exactly like having it. **Actually look at the references,
generalize the design, then conform it to the app.**

So: **before briefing from a description, ask where the real thing is.** On disk, at a URL, in a
running system, in a screenshot you could take. If it is reachable, reaching it is the brief. And
when the reference is *several* things, say so explicitly — what they share is the generalizable
grammar, what is unique to one is that one's signature, and an agent told to match "the style"
will otherwise clone whichever it saw first.

**Before dispatching from a written queue, check the item is still open.** A queue entry is a claim
about the codebase from whenever it was written, and nothing marks it stale when someone ships it
without deleting the entry. Measured in one afternoon: two agents in a row were sent after items
that had shipped days earlier, and each spent its whole run proving so. One grep or one API call
answers "is this still true?" — run it before writing the brief, not inside it.

**Every brief also carries these lines** — each one exists because a child without it failed; the
detail and the incident are in the `references/` file named:

- **Spawning:** *"you are a LEAF agent: do not spawn subagents, and no forks"* — nothing enforces it, and
  a fork inherits the parent's worktree, containers and credentials (`brief-hazards.md`).
- **Refusals:** *"if the permission classifier denies something, do not route around it; say what you
  needed and carry on without it."* Work that needs the user's approval stays in the parent: approvals
  do not cross into a subagent (`brief-hazards.md`).
- **Waiting:** no `run_in_background`, no `Monitor`, no foreground `sleep`; blocking calls in small
  batches, and `timeout: 600000` with calls split under 10 minutes for suites and builds — or the child
  returns "waiting for…" and nothing else (`brief-hazards.md`).
- **Its own namespace:** a scratch subdirectory per agent, not just a unique final output path
  (`brief-readers.md`).
- **A findings path, written as it goes** — even, especially, for a read-only agent (`brief-readers.md`;
  filename rule in §4).
- **For readers:** a numeric budget (`~12 searches and ~10 fetches, then report`), "a well-supported null
  is a valid answer", and for research *"load the `search-craft` skill before your first search"*
  (`brief-readers.md`).
- **For writers:** a worktree under `$HOME` (not the scratchpad), its own test database and port, explicit
  worker counts, a commit after each verified step, and *"never raise a held count or loosen a check to
  pass"* — that rule is owned by `agentic-engineering` (`brief-writers.md`).
- **No `ps` while credentialed commands run** — argv leaks bearer tokens into the transcript; hand secrets
  over by file or env var (`brief-hazards.md`).

## 3. Prefer breadth at the top to depth underneath

**Partition the work first, then hand out the partitions.** Reading a whole tree solo defeats the
point: coverage should be a property of how the work was dealt out, not of what caught one agent's
eye.

**Enumerate the slice, and count afterwards.** An agent given twelve named files reads twelve; one given "the repo" reports on the exciting tenth. A named slice that came back empty is a finding; an unnamed one is indistinguishable from wandering. Afterwards count items covered against the source population: per-item success and consistent yield both look healthy while a fifth of the work is missing.

**A partition cuts the caller from the callee.** Each child reports honestly about half a defect, and "not in my files" gets heard as "not in the app". The seam is the parent's job and it is a pass, not a hope: when a slice reports a defect in something with callers, grep the whole tree for them yourself. Briefing children to look outside their slice spends the coverage the partition bought.

**Search-shaped work (bug hunts, audits) is the exception: duplicate, don't partition.** Run N identical briefs (only the findings path differs) so run-to-run variance does the work; the measured gain is in `bug-hunt`. Children write branches and findings, not MRs or issues; the parent dedupes the union by claim and files once, or the overlap reaches the reviewer as duplicate MRs. Asked for "two hunts", splitting the tree in half buys coverage but throws away the second draw. An open-ended hunt is opus work by §1 (`[opus: ...]`), not sonnet: when the MRs go to a reviewer who cannot catch a wrong fix, the weaker model's precision is the cost that matters.

**The discriminator is independence, not count.** One agent per *distinct source* — a site, a host, an
index — is real parallelism: the I/O overlaps and each agent meets a different rate limiter.
Re-delegating the same question one level down is not; it adds hops and contends for the resource the
parent was already waiting on. Ten agents across ten hosts ran fine in the same session where nineteen
queued behind one rate limiter — serialization wearing a fan-out costume, and indistinguishable from
real parallelism on the roster.

**When a child discovers breadth nobody could have predicted, it returns the work-list upward rather
than spawning.** "Research the competitor landscape" turns up twelve brands that deserve an agent each
— but the parent spawning them is blind to how many siblings already exist and how much of the window
is gone. The root can see both. A returned list of twelve names costs a few hundred tokens; the subtree
it replaces cost 189 million on the run this was learned from.

This is the scout-then-fan-out shape: discover the work-list cheaply, then fan out over it deliberately.

## 4. Keep the findings when an agent dies

**What the harness already does for you.** Every subagent transcript is persisted beside the session
(`<project>/<session>/subagents/agent-<id>.jsonl`), with a sidecar carrying `agentType`, `description`,
`toolUseId` and `spawnDepth`. A finished child's work therefore survives its parent's death on its own.
Don't build a relay upward to protect against that; the storage exists already, and a relay buys
attention rather than durability.

**Where it stops, and this is the sharp edge: the harness keeps text the child actually emitted.** An
agent killed mid-tool-call, having produced only tool calls and no prose, leaves nothing behind. One
reported run burned 5.8M tokens across 146 agents and kept none of it.

**So on any long or tool-heavy fan-out, brief children to write findings to a file as they go and
return a pointer, not a payload.** This is Anthropic's published multi-agent guidance, and it *lowers*
total token use rather than raising it: references stop large outputs being copied through conversation
history at every level.

**But do not name that file `findings.md`.** The Write tool refuses report-shaped `.md` filenames for
subagents — *"Do NOT Write report/summary/findings/analysis .md files"* — so a brief that says "write
your findings to `findings.md`" produces children that silently cannot persist anything and dump the
whole payload into the return channel instead. That is precisely the durability this section is trying
to buy, lost to a filename. Observed on an audit fan-out where two of five children hit it; both
reported it only in passing, so a brief can fail this way without looking broken. Ask for a data-shaped
artifact instead — `<area>-findings.jsonl`, `<area>-notes.txt`, one record per finding — which also
survives being concatenated across siblings.

**Locally, finished children are captured automatically.** A `SubagentStop` hook
(the delegation plugin's `subagent-digest` hook) appends each child's final message to
`~/.claude/agent-digests/<session-id>.jsonl` at zero token cost. After a session is killed, that file
is where the digests are. Note two observed quirks, both contradicting the documented payload:
`stop_reason` is `null` even on a clean finish, and `transcript_path` refers to the *parent* session —
the agent's own transcript arrives as `agent_transcript_path`.

**Whether the hook fires when a child is killed by a usage limit is untested.** Do not assume that
coverage.

## 4b. Peer SESSIONS, when the work should not land in your context

A subagent's report comes back **into** your context; a peer session's does not. That single
difference decides which to reach for, and it matters more than it sounds, because a controller's
context is re-read on every one of its subsequent requests.

**Reach for a peer session when** the work is long-running, spans a repo or checkout you are not in,
or would return a large artifact you only need the conclusion of. The classic shape is a controller
coordinating one session per repo — the answer to "these two repos should really be one" without
merging them. **Reach for a subagent when** you want the findings in hand to reason over immediately,
and the volume is small enough that absorbing it is fine.

**A peer session is not the cheap option for bounded work — it is the more expensive one** (~1.4x
on a matched pair, same payload). It wins only when the alternative is a large payload landing in your
context, or a long-running job whose whole transcript would otherwise accumulate there. For a task that
fits in 150 words either way, take the subagent. So the decision is not "which is cheaper" — it is
**whether you want the work in your context**. If you need to reason over the detail immediately, take
the subagent and cap its report. If you only need the conclusion, or the work is large and
long-running, a peer keeps the whole transcript out of your context permanently, which is the part no
briefing discipline can replicate.

**How to start and drive one** — `claude --bg` (local, message channel) versus a chosen
`--session-id` driven by `claude -p --resume` (works over SSH too), the SSH traps, the flags a worker
needs, and the matched measurement — is in `references/peer-sessions.md`. Read it before starting one.

**The one thing that does not come for free: completion.** A subagent's finish notifies you
automatically. A peer session's does not — nothing wakes you when it is done, so a controller that
assumes otherwise either blocks or silently proceeds on stale state. So make it part of the protocol
in the very first message:

- tell each peer to **message you back when it finishes**, and to say so explicitly if it is
  stopping early or blocked, rather than going quiet;
- **cap the reply length in the brief**. A peer that returns a transcript has thrown away the entire
  benefit; ask for a conclusion, and a pointer to a file for anything longer;
- keep a list of who you dispatched and what you are still waiting on, and **name outstanding peers
  when you report** — an unanswered peer is an open question, not a null result;
- if a peer needs to be sequenced after another, say so when you dispatch it, or wake it yourself
  when its dependency lands. There is no scheduler doing this for you.
- **"Done" is not enough: peers say *done, nothing armed* or *done, waiting on X*** — the difference
  is the whole signal, and on receiving it you send work or say resting is correct. The fleet can go
  idle all at once with work outstanding and nothing will wake it.
- **The protocol dies in compaction** — write it, and the queue, into the working repo (`CLAUDE.md`,
  `NEXT.md`), not only into a chat message.
- **Verify what a peer hands you before relaying it to the user** — a good peer is the dangerous
  case. Never relay a peer's list of the user's open items; never retype an identifier a peer wrote.

When coordinating peers, read `references/orchestrator-protocol.md` — the full protocol and the
incidents behind each rule.

**Permission boundaries are per-session**: never ask a peer to do something blocked in your own
session — that launders the user's decision, and the correct move is to surface it to the user instead.

## 5. Collect, and check the cost afterwards

**An agent showing `completed` is not proof it delivered.** Read what came back before treating a topic
as covered; a stalled or truncated agent reports the same status as a finished one.

**A writer's code change gets a conformance check before you merge it:** the review checklist in the `agentic-engineering` skill (honest ledgers, structure separate from behaviour, tests proven able to fail, design narrowed). The writer's tests carry correctness; do not re-review it for taste.

**Anything you just started is load, and a measurement inside its wake measures the wake.** Your own children running queries (an endpoint read 2.25s mid-fan-out, 0.3s after), and equally a deploy, restart, migration, backfill, cache flush or VACUUM (an absurdly slow reading sixty seconds after a rollout). It is a plausibly slow number, exactly what a performance hunt hopes for, so it gets a real-code cause attached. Take baselines before or after, never during, and before believing a latency ask the system what else is running (`pg_stat_activity`, `top`, queue depth, run list). Same for any shared thing the children hammer: an API, a rate-limited upstream, a CI runner, the disk.

**Don't exit while a child is live** — and if you must, name what is outstanding, so the caller reads a
gap as a gap rather than as a null result.

**After an expensive run, the sidecars tell you what actually happened.** `spawnDepth` across
`subagents/*.meta.json` shows immediately whether depth held:

```
python3 - <<'PY'
import json, glob, collections
c = collections.Counter()
for f in glob.glob("<project>/<session>/subagents/*.meta.json"):
    c[json.load(open(f)).get("spawnDepth")] += 1
print(sorted(c.items()))
PY
```

A healthy research run is mostly depth 1. On the run behind this skill it was 7 / 15 / 30 across depths
1 / 2 / 3, with 84% of the spend below the depth actually requested.
