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
<!-- The observed problem and who it affects, with the number that shows it (40 failed requests an
     hour, 9 of 10 nightly runs timing out). For a bug: the trigger and the old behaviour. Link the issue. -->

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
| **Screenshots** | something a user sees changes (`references/screenshots.md`) |
| **Diagram** | the test in `references/diagrams.md` passes |

Infra / GitOps changes: always give After merge (the live check) and Rollback when anything stateful moves
(`references/infra.md`).

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

## Which reference

| Situation | Load |
|---|---|
| Manifests, Terraform or Ansible (blast radius, After merge, Rollback) | `references/infra.md` |
| Considering a table, snippet, quoted output, `<details>` or checklist | `references/blocks.md` |
| The PR changes control flow across several components (diagram?) | `references/diagrams.md` |
| Something a user sees changes (capture, upload, recordings) | `references/screenshots.md` |

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
  unexpanded (all three happen);
- no local or scratch paths in image links or text, and any diagram renders.

Return the URL. Creating it does not mean merging it or enabling auto-merge.
