# Peer SESSIONS — mechanics and measurements

Detail behind `SKILL.md` §4b. Open it before starting or driving a peer session.

Discover peers with `ListAgents`; address them by the name it prints.

**You can start and drive them yourself — none of this needs a human at a terminal.** There are two
distinct modes, they are alternatives rather than complements, and the choice determines whether the
worker can live on another machine. All of the below is tested, including the parts that failed.

**Mode A — `--bg`, for a worker you want in the message channel.**

```bash
cd /path/to/other/repo && claude --bg --model sonnet "<bounded prompt>"
```

Starts a background session **in that directory** and returns immediately; it then appears in
`ListAgents` as `bg` and takes `SendMessage` by name, round-trip confirmed. `claude agents --json`
lists every session with its `cwd`. **Local machine only** — see below.

One sharp edge: a *running* `--bg` agent **cannot** be resumed from the CLI. `--resume` on one errors
out and tells you to attach (needs a TTY) or `--fork-session` (which branches a copy rather than
continuing the original). So `--bg` buys you the message channel at the cost of CLI drivability.

**Mode B — a session id you choose, for a worker you drive by CLI.**

```bash
SID=$(uuidgen)
claude -p --session-id "$SID" --model haiku "<first task>"
claude -p --resume    "$SID" --model haiku "<follow-up, same conversation>"
```

This is the general mechanism and the more capable one. No TTY, no socket, full conversational
continuity across invocations — verified by having turn 1 memorise a token and turn 2 recall it.
Because you pick the id up front, there is nothing to discover: the address is whatever you generated.

**Across machines, Mode B works and Mode A does not.** Peer discovery uses unix sockets under
`/run/user/<uid>/cc-socks` on the **local** machine, so a session on another host never appears in
your `ListAgents` and cannot be messaged. But driving one over SSH with `--session-id` / `--resume`
works exactly as it does locally, continuity included — confirmed on a second host, in a chosen
directory, on a cheap model, across two turns.

Two traps when doing that over SSH, both hit here:

- **Use the absolute path to the binary.** A non-interactive SSH shell does not source the profile
  that puts `~/.local/bin` on `PATH`, so `command -v claude` reports it missing when it is plainly
  installed. That null nearly got filed as "not supported".
- **Give the call a real timeout.** Two `-p` turns comfortably exceed a default two-minute tool
  timeout, and the second turn silently never ran.

**`--model` and `--effort` are accepted in both modes**, and that is the cost lever. A human-opened
interactive session runs whatever the default is — often the expensive model. A worker you start can
be `sonnet` or `haiku`, which is worth doing. It does **not** reverse the matched-pair measurement
below — that one held the model constant (checked before dispatch, not assumed) and the peer still
cost ~1.4x more, so the peer's disadvantage is structural, not a model artifact. Starting a worker
yourself removes the *accidental* premium of an expensive default on top of it; it does not make a
peer the cheap option. Other flags a worker may need: `--add-dir`, `--settings`, `--agents`,
`--append-system-prompt`, `--permission-mode`.

**How far apart are they, actually? Measured, matched.** Same task, byte-identical prompts, the same
150-word cap, both on the same model (checked before dispatch, not assumed) — so the only difference
left is the mechanism:

| | subagent | peer session |
|---|---|---|
| requests | 5 | 9 |
| tool calls | 2 | 5 |
| delegate-side spend | 0.81 units | **1.13 units** |
| payload returned | ~1.1k chars | ~1.1k chars |

**The peer cost ~1.4x MORE, and returned the same amount.** A peer pays a full session's startup —
its own system prompt and resident prefix — where a subagent starts leaner. With the caps matched,
the returned payloads were indistinguishable, which retrospectively demolishes an earlier unmatched
comparison here that had claimed a large peer advantage: that ratio was measuring the briefing, not
the mechanism, and it was wrong.

Quality was comparable and neither dominated: on an identical audit task both correctly enumerated
every rule and both independently found the same real over-match; each then found one further defect
the other missed, and both of those were confirmed by execution. Two independent readings of the same
artifact were worth more than either alone — which is an argument for pairing them, not for choosing.

What is *structurally* different, and cannot be briefed away:

- a subagent's report is **forced** into the controller's context — you cannot opt out of receiving it;
- a peer's transcript **never enters yours at all**, and you choose what to ask back;
- a subagent's completion notifies you; a peer's does not.

**A peer is a whole session**, so it pays its own resident prefix and its own context growth;
splitting work across peers cuts the *quadratic* re-read term that makes long sessions expensive, but
it does not make the fixed per-request overhead disappear. Modelled on one machine's real sessions,
splitting into four cut context tokens re-read to ~29% of actual, while the share attributable to the
irreducible resident prefix rose from 6% to 20% — which is why trimming residency and splitting
sessions are complements, not alternatives.
