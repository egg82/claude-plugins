---
name: repo-readme
description: "Write a genuinely good, human-readable README (or docs/ tree) for a code repository — what it is, why it exists, how to use or contribute. Use when creating a README, replacing GitLab/GitHub \"Getting started\" boilerplate, revising one, or structuring a repo's docs. NOT Confluence pages (confluence-kb-docs), CLAUDE.md files, or a cold-read review (doc-cold-read)."
---

# Writing a genuinely good repo README

A README is the front door to a codebase. The reader almost always wants one of three
things: to **understand** what this is and whether it's relevant to them, to **use** it, or
to **contribute** to it. The craft is to serve all three from one page (or one page plus a
`docs/` tree) without making any of them wade through the others' material.

**Think of this as a cross between `/init` and a Confluence guide page.** You do the same
deep repo-dive `/init` does -- explore the code, find the build/test commands, the
architecture, the conventions, the key files. But the output is different: instead of a
`CLAUDE.md` written *for an agent* (minimal, behavior-guiding, only the non-discoverable
facts), you write a `README.md` (and/or `docs/*.md`) *for a human* -- an oriented, top-down
guide. The two have opposite economies: an agent manual omits what the agent can discover
itself; a human guide *hands the reader the orientation* they'd otherwise have to reverse-
engineer. But human prose still has to be **lean** -- plain, no padding, specific detail only
where it's actually needed. If the repo has a CLAUDE.md (or other agent-instruction file),
remember **humans don't read it** -- it's the agent's manual, not a human doc, and you must
never send a human reader there. Keep *all* human-facing depth in human-oriented `.md` files
(the README plus `docs/*.md`). The agent manual is a parallel surface that may share facts but
exists for a different reader; mine it for ground truth, don't link humans to it.

The portable companion file is `readme-style.md` -- the voice, the top-down skeleton, the
split-into-multiple-docs rule, and the anti-patterns. Load it before drafting.

## Start with the audience -- it drives the whole shape

Before drafting, answer these. The shape of the README falls out of the answers.

1. **Who is the reader?** For a public/shared repo the default is a **prospective or new
   contributor** -- someone who has a specific interest in this project, language, or topic
   and wants to get oriented fast. But it's often a mix: an **evaluator** deciding whether to
   adopt or depend on it (wants "what is this, is it maintained, what does it cost me"), a
   **user** who just wants to run it (wants install + usage), and a **maintainer/contributor**
   (wants the architecture and the build/test/PR workflow). Identify the primary reader and
   serve them at the top; serve the others in clearly separated, lower sections.
2. **How did they land here?** A README reader usually arrives by **browsing the repo** (they
   followed a link, a dependency, a search result) -- so unlike a search-arrival they don't
   have an error in hand; they have a *question*: "what is this and does it concern me?" Answer
   that in the first two sentences, before anything else. A smaller group arrived because they
   were **told to build/run/contribute** -- they need the steps in order, lower down.
3. **What do they want, and how fast?** The browsing reader wants the **50k-foot view now** --
   one paragraph that lets them decide to keep reading or leave. The user wants a
   **copy-pasteable path to a running thing**. The contributor wants the **mental model of how
   the repo is laid out** before any command. Each is served by going **top-down**: widest
   framing first, narrowing to specifics as the reader commits.

### Dive the repo first -- the `/init`-style discovery pass

This is the non-negotiable verify step, and it's the same exploration `/init` does. For
anything but a tiny repo, fan it out across **1-3 subagents in parallel** and have them report
back; you stay the synthesizer. What to find:

- **What it is and what it produces** -- the top-level purpose, the artifact(s) it builds or
  the service it runs. This becomes the 50k-foot view.
- **The existing README and docs** -- is the README real or host-platform boilerplate (the
  GitLab/GitHub "Getting started" scaffold) to replace wholesale? Inventory `docs/**`,
  `CONTRIBUTING.md`, `ARCHITECTURE.md`, a wiki -- so you **link, don't duplicate**. Read any
  `CLAUDE.md` / agent file for the facts it captures, but treat it as **background only**:
  humans don't read it, so it's a source for you, never a link target for the reader.
- **Build / run / test commands** -- the real entry points and how someone goes from clone to
  a running or built thing. Confirm against `Makefile` / `package.json` / `pyproject.toml` /
  `go.mod` / `Cargo.toml` / scripts and any tool's `--help`.
- **Prerequisites** -- toolchain, auth/logins, env vars, sibling checkouts, network/VPN. These
  are the most-missed thing in a README; hunt for them deliberately.
- **The architecture / mental model** -- the component boundaries, the data or build flow, the
  core concepts a contributor needs before changing anything.
- **Conventions and pitfalls** -- what's project-specific or surprising; key files that
  exemplify the patterns.

Reading the code answers most of "who is this for and how is it used" *and* gives you the
ground truth every command, flag, path, and count must match. Never transcribe something you
haven't confirmed against the source.

**Ask the triggering user for intent you can't derive.** Is this aimed primarily at
contributors, evaluators, or end users? One README, or should the deep material split into
`docs/`? Is there a coexisting doc (a CLAUDE.md, a wiki) to point at rather than duplicate?
Offer concrete options with a recommendation. One good round up front beats a draft on a wrong
assumption. Prefer reading the repo for *facts you can check*; ask the user for *intent you
can't*.

## The workflow that worked

0. **Analyze the audience (above), then pin scope.** Decide *before drafting*: one README, or
   a top-level README plus a `docs/` tree? (See "When to split" in `readme-style.md`.)
   Re-shaping a finished single-file README into a multi-doc set later means re-cutting half of
   it. **Where and how finely to split is partly taste** -- when there's a reasonable range
   (front-door + 2 docs vs. 3 vs. a pure index), don't just guess: put 2-4 concrete structures
   to the user with a recommendation and let them pick. It's a cheap question that prevents an
   expensive re-shape.
1. **Verify before writing.** Confirm every command, flag, path, version, and count against
   the real files and `--help`. If a claim is testable with a no-side-effect probe (a
   `--help`, a `--dry-run`, a read-only subcommand), run it instead of guessing. Tested ground
   truth beats expectation, including the user's; surface contradictions rather than smoothing
   them over.
2. **Draft to the file** (`README.md`, or `docs/<name>.md`). Keep the H1. This is both the
   review artifact and the lasting source of truth.
3. **Iterate note-by-note with the user**, editor-style. Expect framing/tone notes, not just
   fact corrections.
4. **Scrub conversational leakage.** Read the whole draft cold and delete anything that
   answers the chat rather than the reader (see anti-patterns in `readme-style.md`). Then run
   `writing-craft`'s editing pass (`references/editing-pass.md`) over the prose for model tells.
5. **Adversarial cold read, before calling it done.** Spin up 2-3 subagents with **no
   knowledge of this conversation** and have each read the finished draft cold, the way a real
   reader would. Give each only the draft text plus the one-line declared audience & intent,
   and a *different lens* so they don't all find the same thing:
   - **The target reader following it cold** -- can a prospective contributor/user actually get
     oriented and reach a running build from this page alone? Where do they stall, backtrack,
     or not know whether they're in the right place? What prerequisite, env var, or access
     requirement is assumed but unstated?
   - **A skeptical technical fact-checker** *with repo access* -- deliberately the opposite of
     [doc-cold-read]'s readers, who must have **no** access so they can't reabsorb the context the
     test is measuring. Both rules are right: a cold reader with access voids the cold read, and a
     fact-checker without access can only guess. Keep the roles in separate agents -- challenge every command, flag,
     path, version, and count against the actual code. What's asserted but unverified,
     overstated, or contradicted by the source? (This lens is the one that catches a README
     drifting from the code.)
   - *(when the repo risks the wrong reader)* **a wrong-audience reader** -- does the page signal
     who it's for fast, or will an end user / the wrong person waste time? Any leakage, jokey
     headings, decorative emoji, or shade at alternative tooling?

   Their job is to *find what you've gone blind to*. Then **you weigh each finding and apply
   only the valid ones** -- a cold reader lacks context and will raise some criticism that's
   actually wrong; don't reflexively accept or dismiss. If they surface a factual doubt you
   can't immediately refute, go re-verify against the source (back to step 1).
6. **Commit / hand off only on an explicit go.** A README change is a code change -- treat it
   like one (branch if on the default branch, follow the repo's commit conventions). Don't
   commit or push without the user saying so.

## Non-negotiables

Each is spelled out in `readme-style.md`; this is the checklist to run the draft against.

- **Top-down, depth at the bottom** -- the 50k-foot view comes before any command.
- **The first two sentences answer "what is this and does it concern me."**
- **Lean; detail only where it's needed** -- spend words on the non-obvious, not on what `--help` shows.
- **Right-size each doc** -- don't let one sprawl, don't shatter into thin stubs; applies recursively.
- **Accuracy must not rot** -- every command/flag/path verified; no hand-maintained counts or
  version matrices unless the live source of truth is pointed at right beside them.
- **No condescension; no shade at coexisting or past tooling.**
- **Minimize emoji** -- at most one project icon, plus ⚠️ on a destructive step.
- **Cold-readable** -- nothing that answers the chat instead of the reader.
- **Replace host-platform boilerplate wholesale.**
- **Humans don't read the agent manual** -- never link a human reader to a CLAUDE.md.
