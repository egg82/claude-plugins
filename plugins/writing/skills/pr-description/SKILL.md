---
name: pr-description
description: "Write a pull/merge request — title, scope and description — that a reviewer understands in a minute, and publish it with gh or glab. Use when opening a PR or MR, asked to \"write the PR description\" or \"make a PR/MR\", or deciding whether a PR needs a diagram, screenshots, a table or a checklist. NOT commit messages or reviewing a PR (/code-review)."
---

# PR / MR descriptions a reviewer can read

The reader has not seen the conversation, the plan file, the queue or the agent's work: the owner
skimming history months later, or a reviewer deciding whether to merge. The description is the only
context they get, so it has to stand on its own.

## Follow the repo's convention first

Use the baseline below **unless the repo already has a convention of its own**: a PR/MR template
(`.github/pull_request_template.md`, `.gitlab/merge_request_templates/`), or a shape its human-written
PRs share. Then follow that and fit nothing extra into it. Descriptions an agent wrote from this skill
are not a convention: copying them only repeats the baseline, extras included.

## The baseline

**Scope:** one change a reviewer can hold in their head. If the title needs "and" or a list, or the
body needs more than a screen to explain the change, it is two PRs. A refactor the change needs goes
first, in its own PR or at least its own commit.

**Title:** the change in the imperative, under about 70 characters, naming the behaviour rather than
the file ("Retry API calls after a 429", not "Update client.py"). Use the repo's prefix style
(`fix:`, `feat(api):`) if its history has one; don't introduce one. Never truncate with "…".

**Body:**

```markdown
<One or two sentences: what changes for a user or operator, in words a stranger understands.>

## Why
<!-- The observed problem and who it affects, with the number that shows it (the error rate,
     how often it happens). For a bug: the trigger and the old behaviour. Link the issue. -->

## How
<!-- The resulting behaviour and the one implementation choice that matters, with the alternative
     ruled out if that is the question a reviewer will ask. -->

## Verified
<!-- What was observed, and what would have shown the opposite. What was NOT verified, said plainly. -->
```

Conditional sections, added only when their condition holds. When it doesn't, leave the section out;
never write "N/A":

| Section | Add it when |
|---|---|
| **Risk** | the change can break something beyond its own tests: a migration, deleted data, a config or schema other code reads, a behaviour users rely on |
| **After merge** | a human or a deploy must do something, or there is a live check to run once it ships |
| **Rollback** | reverting the merge is not enough on its own (data migrated, resources deleted, external state changed) |
| **Screenshots** | something a user sees changes ([below](#screenshots-and-recordings)) |
| **Diagram** | the [diagram test](#when-a-diagram-earns-its-place) passes |

**Infra / GitOps changes** (manifests, Terraform, Ansible) need less prose and more of the conditional
sections: name the blast radius (which site, cluster or service), let **Verified** show what the
dry run, plan or rendered diff produced, and always give **After merge** (the live check) and
**Rollback** when anything stateful moves.

If one part needs the reviewer's judgement (a threshold, a naming choice, a tradeoff), say which, in
one line. It is the cheapest way to get a useful review.

### What to leave out

Each of these is common in agent-written PRs and none helps the reader:

- **References only the agent can resolve.** "Open-work item 14", "plan step 6", "the fit pass",
  "the owner decided at 14:02". A reader without the plan file can't tell why the PR
  exists. Say the thing itself; if an issue exists, link it and gloss it in a few words.
- **Paths that won't exist for the reader**: scratch files, `/tmp`, the build host's screenshot
  directory, claude.ai session links. Attach the evidence, or say it isn't attached.
- **Agent-process narration.** Mutant counts, "blind suite", "a fresh agent's voice pass",
  "orchestrator review". Say what behaviour is now pinned by tests and whether a defect turned up.
- **Design reasoning.** A "fit pass", rejected alternatives at length, "later systems". Put it in the
  repo's decisions doc and link it; keep one line here.
- File-by-file inventories (the diff has them), pasted logs (quote the line that matters), and
  narration of how the work went.

Prose gets `writing-craft`'s editing pass. An issue rather than a PR follows `bug-hunt`'s
`references/filing.md`.

### Length

Scale with the change. A five-line fix is three short lines: what broke, the cause, what was run.
Write one sentence per heading for small changes. A body past one screen means the PR wants splitting
or the reasoning belongs in a decisions doc.

### Mechanics

- Describe the **whole branch diff** against the merge base, not the last commit, and update the
  description when review changes the code.
- **A closing phrase anywhere in the body closes that issue on merge**: `Closes #7`, `Fixes #7`,
  `Resolves #7`, even inside backticks or in a sentence about a different change. Write one only on
  the line meant to close; elsewhere say "issue 7".

## Blocks: when each earns its place

| Block | Use when | Skip when |
|---|---|---|
| Table | comparing before/after measurements, or options against a benchmark | there is one number (say it in the sentence) |
| Code snippet | the reader needs a new API shape, config key or command | it restates the diff |
| Quoted output | one or two lines are the evidence for a claim in Verified | it is a log dump |
| `<details>` | bulk the reader may want but needn't read: a long log, generated output, a group of screenshots, with a visible summary line above it | it would hide the why, the risk or the after-merge step |
| Checklist | the repo's template has one | never add one yourself. An author ticks their own boxes without reading them; a step that must happen goes under **After merge** as a sentence |
| Screenshots / recording | a visible change; see below | the change isn't visible |
| Diagram | the test below passes | almost always |

Keep blank lines after `</summary>` and before `</details>`, or the Markdown inside won't render.

## When a diagram earns its place

Draw one only when the PR changes **control flow the reviewer would otherwise rebuild in their head
from several files**: new or reordered branches across three or more components, a retry or fallback
loop, a state machine, or two paths whose difference is the point (write vs read). Skip it for a change
inside one function, a straight sequence (a numbered list says it), a single decision, UI layout,
config, dependencies, renames, docs and test-only changes. If the flow fits in one sentence, write the
sentence. A diagram that restates the How bullets one for one is the commonest failure.

Draw **the behaviour this PR changes**, not the system. A Mermaid `flowchart TD`: plain rectangular
boxes with short verb-led labels, conditions on the edges, the real branches and loops and no invented
ones. Put independent paths side by side (`subgraph`) when comparing them is the point. Put it under a
`## Diagram` heading after `## How`, with one sentence first on what the reviewer should notice.

**Render it and look at it before publishing**, because Mermaid silently produces unreadable layouts:

```bash
podman run --rm -v "$dir":/data:Z ghcr.io/mermaid-js/mermaid-cli/mermaid-cli:11.4.2 \
  -i /data/flow.mmd -o /data/flow.png -b white
```

(`$dir` must be writable by the container user; `chmod 777` a scratch dir. Use `mmdc` directly where
it is installed.) Then Read the PNG and check labels, clipping and that it matches the final code.

**Embedding:** GitHub and GitLab both render a ` ```mermaid ` block in descriptions. Use that by
default; it stays editable and needs no upload. Upload the PNG only when readers mostly see the PR
somewhere that won't render it (email notifications, some mobile apps). Never send private architecture
to a public diagram-rendering service; render locally.

## Screenshots and recordings

For a visible change only. Real captures of the PR build, and of the base build for "before"; never
edit the DOM to stage one. Same UI state, viewport, data and theme on both sides, side by side in a
table. Use a short recording or GIF only when the change is an interaction or animation a still can't
show, and keep the stills too. Synthetic data; nothing secret in frame. `headless-render` covers
capturing on a machine with no browser. Don't commit them to the repo, and if they should exist but
couldn't be captured, say what is missing.

**Uploading** (a filename in the body is not an image):

- **GitLab** (checked with glab 1.112): `glab api --method POST "projects/:id/uploads" --form
  "file=@shot.png"` returns JSON whose `markdown` field is a ready `![shot](/uploads/...)` line.
- **GitHub:** `gh pr create --attach <file>` with matching `![alt](<same path>)` in the body replaces
  the path with an uploaded URL. Needs gh ≥ 2.99; check `gh pr create --help` for `--attach`. Without
  it, say the screenshots are not attached rather than listing their filenames.

## Publish, then read it back

Write the body to a file, then:

```bash
glab mr create --source-branch "$head" --target-branch "$base" --title "$title" --description "$(cat "$body")" --yes
gh pr create --base "$base" --head "$head" --title "$title" --body-file "$body"
```

Never `glab mr create --fill`: on a single commit whose body is only its trailer, it publishes a
description that is just `Co-Authored-By: …`.

Check for an existing PR/MR on that branch first; update it instead of opening a duplicate (fetch its
current body and keep a human's edits). Then **read back** the published title and body and check:

- the body is the one you wrote: not empty, not only an attribution line, no literal `$(` left
  unexpanded;
- no local or scratch paths in image links or text, and any diagram renders.

Return the URL. Creating it does not mean merging it or enabling auto-merge.
