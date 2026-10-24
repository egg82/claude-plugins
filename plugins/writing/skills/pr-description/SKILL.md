---
name: pr-description
description: "Write a pull/merge request description a reviewer understands in a minute — Why, How (with what was verified), a small flow diagram, screenshots for UI — and publish it with gh or glab. Use when opening a PR or MR, asked to \"write the PR description\" or \"make a PR/MR\", or adding a diagram to one. NOT commit messages or reviewing a PR (/code-review)."
---

# PR / MR descriptions a reviewer can read

The reviewer has not seen the conversation, the ticket thread or the agent's work. The description is
the only context they get, and a diagram of the changed flow tells them where to look faster than any
paragraph.

## The body: four sections, in order

```markdown
## Why?
<!-- The concrete problem and who it affects. For a bug: the trigger and the old behaviour. Link the issue. -->

## How?
<!-- The resulting behaviour and the one implementation choice that matters. Then what was verified,
     with the actual result, and any gap. -->

<details open>
<summary><strong>Diagram</strong></summary>

<!-- One sentence: what the reviewer should notice. Then the diagram. -->

</details>

## Screenshots
<!-- Before/after table for changed UI, labelled images for new UI, "N/A: no visual change" otherwise.
     If they should exist but couldn't be captured, say what is missing — that is not N/A. -->
```

- Describe the **whole branch diff** against the merge base, not the last commit.
- No file-by-file inventory, no pasted logs, no narration of how the agent got there. The prose
  gets `writing-craft`'s editing pass; an issue rather than a PR follows `bug-hunt`'s `references/filing.md`.
- A small change gets a short body; the sections stay, the prose shrinks. If the repo has a PR
  template, fit these sections into it rather than replacing it.
- Keep the blank lines after `</summary>` and before `</details>`, or the Markdown inside won't render.

## The diagram

Draw **the behaviour this PR changes**, not the system. A Mermaid `flowchart TD`: plain rectangular
boxes with short verb-led labels, conditions on the edges, the real branches and loops and no invented
ones. Put independent paths side by side (`subgraph`) when comparing them is the point, e.g. write
path vs read path. If nothing has a flow or relationship worth showing, say so in one line.

**Render it and look at it before publishing** — Mermaid silently produces unreadable layouts:

```bash
podman run --rm -v "$dir":/data:Z ghcr.io/mermaid-js/mermaid-cli/mermaid-cli:11.4.2 \
  -i /data/flow.mmd -o /data/flow.png -b white
```

(`$dir` must be writable by the container user; `chmod 777` a scratch dir. Use `mmdc` directly where
it is installed.) Then Read the PNG and check labels, clipping and that it matches the final code.

**Embedding:** GitHub and GitLab both render a ` ```mermaid ` block in descriptions — use that by
default; it stays editable and needs no upload. Upload the PNG instead when the host doesn't render
Mermaid, or when readers mostly see the PR somewhere that won't (email notifications, some mobile apps):

- **GitLab** (checked with glab 1.112): `glab api --method POST "projects/:id/uploads" --form
  "file=@flow.png"` returns JSON whose `markdown` field is a ready `![flow](/uploads/...)` line.
- **GitHub:** `gh pr create --attach <file>` with matching `![alt](<same path>)` in the body replaces
  the path with an uploaded URL. Needs gh ≥ 2.99; check `gh pr create --help` for `--attach`.

Never send private architecture to a public diagram-rendering service; render locally.

## Capturing screenshots

Real captures of the PR build, and of the base build for "before" — never edit the DOM to stage one.
Same viewport, data and theme on both sides. Synthetic data; nothing secret or customer-identifying in
frame. `headless-render` covers capturing on a machine with no browser. Don't commit them to the repo.

## Publish, then read it back

Write the body to a file, then:

```bash
glab mr create --source-branch "$head" --target-branch "$base" --title "$title" --description "$(cat "$body")" --yes
gh pr create --base "$base" --head "$head" --title "$title" --body-file "$body"
```

Check for an existing PR/MR on that branch first; update it instead of opening a duplicate (fetch its
current body and keep a human's edits). Then read back the published title, body, branches and URL —
no local paths left in image links, the diagram renders — and return the URL. Creating it does not
mean merging it or enabling auto-merge.
