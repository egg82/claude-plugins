# Voice, structure & decisions for repo READMEs

The house style for a genuinely good repository README. Portable craft. `SKILL.md` has the
audience thesis and the workflow; this file is the craft that follows from it.

## Audience -> structure

A README serves a mixed-but-predictable crowd, and the shape is a **funnel**: widest framing
at the top, narrowing as the reader commits. The reader self-selects how far down they go.

| Reader & intent | What they need | Where it lives on the page |
| --- | --- | --- |
| Browsing -- "what is this, does it concern me?" | One-paragraph 50k-foot view; what it is, why it exists, who it's for | The first two sentences, above everything |
| Evaluating -- "should I adopt/depend on this?" | Scope, status, what it costs to run, key constraints | High, right after the intro |
| Using -- "I just want to run it" | Prerequisites, then a copy-pasteable path to a running thing | Upper-middle: quick start + prerequisites |
| Contributing -- "how is this laid out and how do I change it?" | The mental model / architecture, then build-test-PR workflow | Middle-to-lower: layout, then how-to |
| Looking something up | Scannable reference (commands, flags, config) | Lower: tables, or a `docs/` reference page |
| Going deep -- "how does the tricky part actually work?" | The real internals, one subsystem at a time | Bottom, or split into `docs/` |

The single rule that makes this work: **never make the primary reader wade through the
secondary reader's material.** The browsing reader who'd leave after one paragraph shouldn't
have to scroll past build internals to find out what the project is. That's why depth goes at
the bottom.

The reader is **not** assumed to be a novice -- a repo README's default reader is technical
and has a specific interest. Match the vocabulary to them. Precise terms are welcome; what's
out of place is *unexplained project-specific* jargon up top (a subsystem name, an internal
acronym) before the concept behind it has been introduced.

## Voice

- **Plain, concrete, present-tense.** "This builds the container images the service runs on" beats "This
  repository is intended to facilitate the construction of operating system artifacts." Say
  what it *is*, not what it's "intended to" be.
- **Lead with the thing, not the meta.** Open on what the project does, not on "Welcome to the
  X repository. This README will describe...". Cut throat-clearing.
- **Lean -- detail only where it's needed.** Say it once and move on. Spend words on the
  non-obvious (a gotcha, a subtle ordering, the *why*); spend almost none restating what the
  code or a `--help` already shows. Prefer a table or a five-line tree to a paragraph. If a
  sentence doesn't help the reader *understand, use, or change* the project, cut it.
- **No condescension.** State the capability; don't comment on the reader's instincts or
  history.
- **No shade at a coexisting option or past tooling.** Where two supported approaches exist
  they're different-but-equal -- no "old/new/legacy/replaces/migrating." State the present-tense
  fact.
- **Minimize emoji.** At most a single project icon, plus the occasional ⚠️ on a genuinely
  destructive or irreversible step (a command that pushes, deletes, or can't be undone). None
  in headings, bullets, or prose. When unsure, none.
- **Don't overstate.** Distinguish "needs network" from "needs the VPN," "should work" from
  "verified." Note when something is optional or has a fallback.
- **Show the command as the user types it.** Don't surface plumbing the reader never touches.
  If the entry point is `./build.sh`, document that, not the fifteen flags it wraps.
- **Cold-readable.** Every line makes sense to a first-time reader. Scrub anything that answers
  *you* (the chat) instead of the reader.

## Structure (the proven skeleton)

The default for a single-file README serving a mixed audience. It is a top-down funnel. Let a
single-intent repo (a pure library, a pure CLI) reshape it -- don't force sections that don't
earn their place.

1. **Title + one-line tagline** -- the project name and a single sentence on what it is.
2. **The 50k-foot view** -- one short paragraph: what this is, why it exists, what it produces,
   who it's for. End it with a one-line "if you just want to *use* this / this isn't the page
   for X" redirect when the repo risks attracting the wrong reader.
3. **The short version / quick start** -- the 3-6 commands that get someone from clone to a
   running or built thing. Lead with any **must-read safety or destructive-action warning**
   *before* the commands (people copy-paste and skip prose). This is the highest-value real
   estate; keep it copy-pasteable.
4. **Prerequisites / "before you build"** -- everything that must be true before the quick
   start works: toolchain, auth/logins, env vars, sibling checkouts, network/VPN. A missing
   prerequisites section is the most common reason a reader stalls -- collect them in one place,
   don't scatter them through the doc.
5. **What's in here** -- a short annotated map of the top-level layout (a tree with one comment
   per entry). This is the contributor's first orientation.
6. **The mental model / architecture** -- how the pieces fit, the data/build flow, the core
   concepts. Diagrams (ASCII or linked images) earn their place here. This is what a contributor
   needs before they can change anything.
7. **How it works** -- the genuinely non-obvious mechanics, one subsystem at a time. Each
   subsection leads with a one-liner of what it does before the detail.
8. **Using it / common tasks** -- a reference table of "goal -> command," plus the knobs
   (flags, env vars) and where logs/output go.
9. **CI / validation / testing** -- how the project is checked, and what a contributor must keep
   in sync.
10. **The deepest / most specialized topic last** (or moved to `docs/`), with a "most people
    never need this" lead-in.
11. **Where to go deeper** -- pointers to `docs/`, the wiki, or the live source of truth
    (`run X --help` / `run X --show-...`). Never to a CLAUDE.md -- that's the agent's file, not
    the human's.

Not every repo needs all eleven. A library README might be: tagline -> install -> usage
example -> API reference link -> contributing. A CLI: tagline -> install -> the commands ->
config -> contributing. Keep the funnel; drop the sections that don't apply.

## When to split into multiple docs

**Right-size every doc.** The goal isn't "short" -- it's that no single doc sprawls into a long
scroll the reader has to wade through, *and* the project isn't shattered into a confetti of thin
files the reader has to chase. Both fail the reader the same way: they can't find their thing.
The README is not "everything about the project on one page"; it's the **50k-foot view + quick
start + a map of where everything lives.** A topic grows big enough to make the reader scroll
past unrelated material -> it moves to its own doc and the README links to it. A "doc" is too
thin to exist on its own -> fold it back into a section of a larger page.

This applies **recursively**. A topic doc (a "building" guide, an architecture deep-dive) that
sprawls splits the same way -- a long `docs/build.md` becomes `docs/build.md` (the overview +
map) plus `docs/build/packaging.md`, `docs/build/releases.md`, etc. The same reader-can't-find-it
problem exists at every level; apply the same fix at every level.

Triggers to split a topic out:

- The page is long enough that something near the top (the quick start, the architecture) scrolls
  off before a related section appears.
- There are several **distinct deep topics** different readers want (a build/release guide, an
  architecture deep-dive, a configuration reference, a contributing guide) -- each wants its own
  page and its own audience.
- A subsystem has enough internals to stand alone.

When you split:

- The parent page (README, or a topic doc's index) keeps the **orientation and the map**: the
  framing, the quick start, the layout, and a short signposted list of links ("Architecture ->
  docs/architecture.md", "Building & releasing -> docs/build.md"). The reader finds the right
  deep doc in one glance, without scrolling.
- Each child doc is itself top-down: it **re-states its own scope and audience in its first
  lines** (a reader may land on it directly from a search or a link), then goes deep -- and
  splits again if it gets long.
- Use the names the ecosystem expects so they're discoverable: `CONTRIBUTING.md`,
  `docs/architecture.md`, `docs/build.md` (or `RELEASING.md`), `docs/configuration.md`.

The one counter-force: **don't fragment a small thing.** Two screens of README beats five files
the reader has to chase. The test is always "can the reader find their thing without scrolling
past stuff they don't care about" -- not "maximize the number of files." Split when length
buries; consolidate when fragmentation scatters.

**And where the line falls is partly taste.** Two sensible people will draw the boundaries
differently (does CI get its own page or fold into the build doc? does the architecture diagram
stay on the front page or move out?). When there's a reasonable range, don't silently pick --
offer the user 2-4 concrete structures with a recommendation and let them choose. Cheap to ask,
expensive to re-shape after the fact.

## Anti-patterns (caught in review)

- **Host-platform boilerplate left in place** -- the GitLab/GitHub "Add your files / Getting
  started / Integrate with your tools" scaffold. It says nothing about the project. Replace the
  whole thing, don't edit around it.
- **Throat-clearing intro** -- "Welcome to this repository. In this document we will..." Open
  on what the project does.
- **Burying the 50k-foot view** -- starting with install steps or a wall of badges before the
  reader knows what the thing is. The "what is this" comes first.
- **Scattered prerequisites** -- auth, env vars, and required sibling checkouts mentioned
  incidentally in three different sections. Collect them in one "before you build" block above
  the first real command.
- **Counts and version matrices that drift** -- "supports 44 modules," "works on Python 3.8-3.11"
  hand-typed and never updated. Either point at the live source (`run X to list them`) right
  there, or cut the number.
- **Commands that don't match the code** -- a copy-pasted command block with a flag that was
  renamed, or a path that moved. Every command is verified against `--help` / the source. This
  is the failure the fact-checker lens exists to catch.
- **Documenting plumbing the reader never touches** -- the internal wrapper's fifteen flags when
  the user only ever types `./build.sh`.
- **Conversational leakage** -- text that answers the chat, not the reader: "no need to do X
  first," "the one thing people miss," reassurances that defend a design decision nobody
  questioned. Delete or rewrite to a direct statement.
- **Decorative emoji** -- anything beyond the lone project icon or a ⚠️ on a destructive step.
- **Shade at tooling** -- "the legacy build script," "unlike the old approach." State what the
  current thing does.
- **Drifting cross-references** -- "see the section above," "as described in docs/foo" pointing
  at something that moved or never existed. Anchor links must resolve; doc links must point at
  real files.
- **Sending humans to the agent manual** -- a CLAUDE.md is written for an agent; humans don't
  read it. Don't link a human reader there for depth, and don't assume they'll find facts that
  only live there. Put the exhaustive *human* version in a `docs/*.md` file and link that.
