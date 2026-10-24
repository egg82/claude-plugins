# claude-plugins

Skills, hooks and always-on preferences from my Claude Code setup, split into small plugins so you can
take the parts you want and leave the rest.

## What is it?

I use Claude Code for nearly everything I build outside of [Fetcharr](https://github.com/egg82/fetcharr): a
Kubernetes homelab, a couple of apps that agents write most of the code for, and a lot of shell work. When a
session went wrong in a way that would happen again, I wrote the fix down. A method became a skill. A rule Claude
kept skipping became a hook, which the harness runs whether or not the model remembers it. Preferences about how I
like to work went into short memory files that load in every session; I call those stances.

This repo is that collection, with everything specific to my own machines and network taken out. Claude Code sessions
wrote most of the text from real incidents, and I decided what it should say. It's one person's opinions. They've
worked for me, and some of them won't fit how you work.

The Kubernetes and workstation runbooks assume Talos, Flux, CloudNativePG and bootc, so they only help if you run
those. The rest applies more widely: checking a fix works before calling it done, docs a stranger can follow,
subagents that don't eat your usage, shell commands that can't report success when they failed.

## Where to start

Some of these hooks refuse tool calls, and whether one suits you depends on things only your own setup can answer:
which shell your Bash tool runs, what kinds of memory notes you keep, which hooks you already have. So the
recommended start is to let your own Claude look before you install anything. Paste this into a session:

```
Read https://github.com/egg82/claude-plugins/blob/main/START-HERE.md and follow it.
```

It reads `CATALOG.md`, then your `~/.claude` (your `CLAUDE.md`, memory, skills, hooks and a sample of recent
session transcripts) on your machine. It sends nothing anywhere and changes nothing. You get back a table of what to
take, adapt or leave, each with a reason taken from how you work and a note of anything that would conflict with
your setup. It installs only the rows you pick. Run the same line later and it shows you what changed upstream.

If you'd rather read than delegate, [`CATALOG.md`](CATALOG.md) has every item: what it does, what it needs, whether
it can block anything, and what in your setup would suggest you want it.

## Installing by hand

```
/plugin marketplace add egg82/claude-plugins
/plugin install writing@egg82
```

`egg82` is the marketplace name. A plugin turns on its skills and its hooks together, and `/plugin disable
<plugin>@egg82` turns both off. Skills from a plugin are namespaced (`writing:writing-craft`), so they won't collide
with skills you already have.

| Plugin | What it's for | Hooks | Blocks anything? |
|---|---|---|---|
| `engineering` | Keeping a codebase agents write well designed: size gates, ledgers that may only shrink, tests proven able to fail, bug hunts proven by running them | `held-ledger-raise-gate` | holds a turn's end once |
| `vetting` | Deciding whether to adopt something: an unfamiliar repo, a third-party project, a hyped AI tool, a self-hosted app | none | no |
| `writing` | Prose that doesn't read as model-written; READMEs, PR descriptions and wiki pages | none | no |
| `frontend` | Web UIs and dashboards, rendered and looked at before they're called done; promo videos of a site | `html-render-gate` | holds a turn's end once |
| `game-dev` | Game design method; choosing sound you can't hear | none | no |
| `shell-safety` | Shell commands whose result would lie, scripts linted as they're written, background jobs nobody waits on | `bash-footgun-gate`, `script-lint`, `detached-work-gate` | yes: Bash calls |
| `secret-guard` | Secrets redacted from command output before the model sees them | `secret-redact` | no |
| `research` | Web searches that find the answer | `search-craft-gate` | yes: the 1st and 4th search until the skill loads |
| `delegation` | Subagents that stay affordable; a checkout shared safely with other sessions | `agent-depth-gate`, `spawn-model-gate`, `subagent-digest`, `shared-checkout-backstop` | yes: subagent spawns |
| `config-care` | Keeping a Claude Code setup lean: a drift report at session start (plus an optional monthly sweep), always-on load pruning, skill audits | `hygiene-sessionstart` | no |
| `memory-discipline` | Strict rules for memory notes, and lessons routed to where they belong | `memory-write-gate`, `memory-bash-write-backstop`, `route-lesson-gate` | yes: memory writes |
| `config-transfer` | Moving Claude Code config between machines, or to someone else as a scrubbed bundle | none | no |
| `continuity` | Surviving compaction (when Claude Code summarises a long conversation to free context): the time on every prompt, a handoff written before and read back after | `prompt-clock`, `precompact-snapshot`, `postcompact-handoff` | no |
| `k8s-ops` | Kubernetes runbooks: triage, sizing, secrets, storage, ingress, Talos, Flux, CloudNativePG, Grafana | none | no |
| `linux-workstation` | bootc/OSTree workstations, LUKS with TPM unlock, NVIDIA driver failures | none | no |

If you only want to try one, `writing` has no hooks, so nothing in it can get in your way.

### Before you turn on a hook

- **`shell-safety` assumes the Bash tool runs bash.** I set this in `~/.claude/settings.json`:

  ```json
  { "env": { "CLAUDE_CODE_SHELL": "/usr/bin/bash" } }
  ```

  If yours runs zsh (the macOS default), the gate will block correct zsh and miss broken zsh. Set the variable or
  skip the plugin.
- **`memory-discipline` refuses some memory notes Claude Code writes on its own.** A note must be `type: user` or
  `type: feedback`, or carry a `check:` line, so Claude Code's own `project` and `reference` notes get refused until
  they have one. Install it only if you want that rule.
- **`spawn-model-gate` refuses a subagent spawn that doesn't name a model**, and an `opus` spawn whose prompt
  doesn't say why. That's the point of it, but it will stop a habit you may have.
- **When a hook blocks, Claude sees the reason** and usually retries a different way. "Holds a turn's end once"
  means a Stop hook makes Claude address something once before finishing, then lets it go.
- **Every hook fails open except `memory-write-gate`.** If one can't read its input, it lets the call through, so a
  broken hook looks the same as no hook. `memory-write-gate` fails closed: if `python3` is missing, it blocks
  memory writes.
- **They need `python3`, `git` and GNU userland** (Linux is what they're tested on). `secret-redact` needs
  [gitleaks](https://github.com/gitleaks/gitleaks) on your `PATH` or in `~/.local/bin`; without it, it only redacts
  values it saw fetched from a secret store.
- **Some keep state** under `~/.claude/` (dotfiles like `.lesson-routed`, `HANDOFF-*.md`, `state/`,
  `agent-digests/`) and per-skill files in `~/.claude/local/<skill>/`.

### Stances

Stances live in [`stances/`](stances/), outside the plugins, because a plugin can't add lines to your `CLAUDE.md`.
They're opinions, so copy only the ones you agree with:

```
git clone https://github.com/egg82/claude-plugins
cd claude-plugins/stances
./install.sh                                          # lists what's there; changes nothing
./install.sh --apply prefer-subtraction verify-dont-anchor
```

`install.sh` copies each named file into `~/.claude/memory/` and adds an `@~/.claude/memory/<name>.md` line to
`~/.claude/CLAUDE.md`. If you already have a file with that name, it leaves yours alone and doesn't import it. To
remove a stance, delete the file and its line. Some stances point at an `evidence/` file of incidents that isn't in
this repo; the rule stands without it.

`stances/on-demand/` holds notes for a project's memory directory rather than every session, `stances/rules/` holds
the rule file `memory-discipline` is written against, and `stances/prompts/` has a prompt for cutting LLM cruft out
of a repo.

### Docs templates for a repo agents write

The `agentic-engineering` skill (in `engineering`) ships skeletons for the docs I keep in every repo where agents
write the code: a short `CLAUDE.md` that points to `docs/engineering.md`, `docs/systems.md`, `docs/decisions.md`
and `docs/open-work.md`. They're in
[`plugins/engineering/skills/agentic-engineering/templates/project-docs/`](plugins/engineering/skills/agentic-engineering/templates/project-docs/),
with a README on the order to fill them in.

## Checking that it works

Each hook with a test suite has a `test-*.sh` beside it, and the larger gates keep theirs with their skill. From a
clone:

```
bash plugins/shell-safety/skills/shell-footguns/test-gate.sh
bash plugins/secret-guard/hooks/test-secret-redact.sh
```

If you installed through the marketplace, the same files are under `~/.claude/plugins/cache/egg82/<plugin>/<version>/`.

To check that a suite is really testing something, point it at a hook that doesn't exist with `GATE=` or `HOOK=`;
every case should fail.

## Keeping up to date

```
/plugin marketplace update egg82
/plugin update <plugin>@egg82
```

Stances are copies, so plugin updates don't reach them. Run the `START-HERE.md` line again and it compares your
copies with the current ones and offers to merge, keeping any edits you made.

Some skills mention `skill-creator`, which is Anthropic's plugin, not part of this repo.

## License

MIT. See [`LICENSE`](LICENSE).
