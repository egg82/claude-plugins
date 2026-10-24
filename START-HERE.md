# Start here (instructions for Claude)

Your user pointed you at this file so that you can look at how they actually use Claude Code and
tell them which parts of this repo to take, adapt or leave. Do the work below, then give them the
table in step 6. Do not install anything until they have seen the table and said which rows to apply.

The repo is `https://github.com/egg82/claude-plugins` (marketplace name `egg82`). Raw files are under
`https://raw.githubusercontent.com/egg82/claude-plugins/main/`.

## 1. Get the catalog

If the repo is already checked out, use that: a directory holding `CATALOG.md` and a
`.claude-plugin/marketplace.json` whose `name` is `egg82` (the clone may have any directory name).
Otherwise either
`git clone https://github.com/egg82/claude-plugins` into a scratch directory, or fetch
`CATALOG.md` from the raw URL; fetch `stances/always-on/<name>.md` when you need a stance's text.

`CATALOG.md` has, for every plugin, skill, hook and stance: what it does, what it needs, and
"Signals" you can look for. Its last section is a generated cross-reference block: which items name
which others. Read all of it.

## 2. Look at their setup

Read, never modify. Names and counts are what you need; never print values.

- `~/.claude/CLAUDE.md` and its `@imports`, `~/.claude/memory/`, project memory under
  `~/.claude/projects/*/memory/`
- `~/.claude/skills/` and installed plugins (`claude plugin list`). A skill or hook with the
  same name as a catalog item may be a hand-copied version of it; compare the file to the repo's
  before treating it as their own.
- the `hooks` block of `~/.claude/settings.json` (event, matcher, script name only), plus
  `CLAUDE_CODE_SHELL` and the model/plan settings if present

## 3. Look at their history

Transcripts are `~/.claude/projects/<dir>/<session>.jsonl`, one JSON object per line. Project
directory names often start with `-`, so list them with
`find ~/.claude/projects -maxdepth 2 -name '*.jsonl' -printf '%T@ %p\n' | sort -rn | head -40`
rather than a shell glob, and skip `subagents/` directories (those are subagent transcripts and
would double-count). Sample the 40 most recent; say how many you sampled. Parse the JSON rather
than grepping raw lines, and count sessions (not lines) per signal:

- Bash commands: `tool_use` blocks with `name == "Bash"`; count tool names in `input.command`
  (`kubectl`, `flux`, `talosctl`, `vault`, `ssh`, `nohup`, `gh`, `glab`, `podman`, `docker`)
- `Agent` calls (and whether `input.model` is set), `WebSearch` calls, `Skill` calls
- Write/Edit targets (`input.file_path`): `*.md`, `*.html`, `*.sh`, memory files
- failed Bash runs: a `tool_result` with `is_error: true` whose `tool_use_id` matches a Bash
  `tool_use` id in the same file
- compaction: lines with `isCompactSummary: true`; if none of the sampled sessions has one, say
  "not detected", not zero
- the user's own messages (`type: "user"` with text content, not tool results): corrections
  ("no, I meant", "that's wrong"), "sounds like AI", "is that finished?", "you forgot". These are
  rough phrase counts; report them as such

Counts per signal, plus at most a short paraphrase of what the user said. Do not quote transcript
content, do not print secrets, env or file contents, and do not repeat other people's content you
find in them. If a signal has zero hits, say zero; do not guess from vibes. A grep that returns
nothing proves nothing until you have checked it can match (run it once against a known positive).

## 4. Match by function, not by name

For each catalog item, check whether they already have something that does the same job under
another name: a skill of their own, a memory file, a hook, an installed plugin. Judge by what the
file does, not its filename. To keep this affordable, compare descriptions first (a skill's
`description:` frontmatter, a memory file's first paragraph, a hook's header comment) and read a
whole file only where the descriptions overlap. If they have an equivalent, the answer is "skip, you have it" or
"merge": name their file and say what the repo's version adds or lacks. Do not recommend a
duplicate.

## 5. Check what would break

Several hooks refuse tool calls. Before recommending any plugin with hooks, check it against their
machine, and turn each conflict into a Leave or Adapt row with the reason:

- **Their Bash tool's shell.** `CLAUDE_CODE_SHELL` in `settings.json` `env`, else their login shell.
  If it is zsh, `shell-safety`'s gate blocks correct zsh and misses broken zsh: Leave it, or Adapt by
  setting `CLAUDE_CODE_SHELL` to bash, which changes how every Bash call runs, so say so.
- **Their memory notes' types.** Count `type:` values in the frontmatter of `~/.claude/memory/`
  and `~/.claude/projects/*/memory/` notes (top level, or nested under `metadata:`), skipping
  `MEMORY.md`. Notes that are `project`, `reference` or carry no type, and have no `check:` line,
  are the kind `memory-discipline` refuses to write from now on; say how many they have.
- **Hooks they already run** on the same event and matcher: two gates on `PreToolUse` `Bash` both
  fire. Name the overlap.
- **Tools a hook needs:** `python3` and `git` for all of them, `gitleaks` for `secret-guard`, GNU
  userland (`timeout`, `stat -c`, `realpath -e`); on macOS without GNU coreutils, say the hooks are
  untested there.
- **`spawn-model-gate`** refuses every subagent spawn that names no model. If their transcripts
  show `Agent` calls without `model`, say that their current habit will be blocked.

## 6. Report: take / adapt / leave

One table, one row per plugin, plus a row for any single skill, hook or stance whose verdict
differs from its plugin's. Put items with no signal and no overlap in a single "Leave" line listing
their names. If nothing comes out as Take or Adapt, say so plainly and stop there:

| Item | Verdict | Why (from their history) | Comes with it |
|---|---|---|---|

- **Take**: it fits and the history shows the need. Reason is a count or a paraphrase, for example
  "kubectl in many of the 40 sampled sessions".
- **Adapt**: it fits but carries the author's conventions. Say exactly what to change: a stance
  assuming a flat-rate Max plan, a hook with token thresholds for a 1M window, a rule assuming the
  Bash tool is configured as bash, a Fable-model rule in `spawn-model-gate`, runbooks written for
  Talos/Flux. A stance is copied, so adapting means editing their copy.
- **Have it**: they already run this item or an equivalent. Name their file; if the repo's
  version differs, say in a line what it adds, and offer the diff rather than a reinstall.
- **Leave**: no signal, or contradicts something they do. One short reason.
- **Comes with it**: from the cross-reference block. If a hook's message names a skill in another
  plugin, or a stance tells Claude to load a skill, list that dependency and say whether they have
  it. Taking `search-read-the-failure` without `search-craft` does nothing, for instance.

Stances are opinions. Say plainly that they should delete any they disagree with, and that the
"Take" rows for stances are suggestions about fit, not a claim that the opinion is right.

Then give the commands for exactly the rows they take, not the whole repo:

```
/plugin marketplace add egg82/claude-plugins
/plugin install <plugin>@egg82            # once per plugin; plugins install whole
git clone https://github.com/egg82/claude-plugins    # if not already cloned
claude-plugins/stances/install.sh                    # lists what it would copy
claude-plugins/stances/install.sh --apply <name> <name>   # copies and adds the @import lines
```

`install.sh` checks every name before copying anything, never overwrites an existing memory file,
and does not import a file it skipped, so a note of theirs with the same name stays as it was. On-demand
stances, `rules/` and `prompts/` are not installed by it; tell them where to copy those and what
to wire up (project memory index, `.claude/rules/`, or paste the prompt).

End by asking which rows they want applied. Apply only those.

## 7. Updating (when they run this again)

Plugins and copied stances update differently:

- **Plugins**: `/plugin marketplace update egg82`, then `/plugin update <plugin>@egg82`.
- **Stances are copies.** `/plugin update` does not touch them. For each stance in
  `~/.claude/memory/` whose name matches a file in the repo's `stances/always-on/` (or the other
  stance directories), diff their copy against the repo's current version.
  - Identical: say nothing.
  - Differs and the user never edited theirs (it matches an older repo version; check
    `git log -p -- stances/...` in a clone): show what changed upstream in a line or two and offer
    to overwrite.
  - Differs and they edited it: show the upstream change and their edits side by side, and offer a
    merge that keeps their edits. Never overwrite a locally edited stance without asking.
  - Removed upstream: tell them, and let them decide; do not delete their copy.
  - New upstream since last time: run steps 2 to 6 for only those items.
- `install.sh` skips files that already exist, so updating a stance means copying the file
  yourself after they agree; the `@import` line is already in place if they installed it with
  `install.sh`.
