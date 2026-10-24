# Research findings, with sources

Gathered while reorganizing a Claude Code setup whose memory store had become a catch-all. Recorded
so the same searches don't get re-run. Three angles: agent-memory architectures, community
conventions, and documentation drift.

Treat every claim as *as-found* — re-check anything load-bearing, especially version-gated behaviour.

## Verified platform behaviour (check against your own version)

These were confirmed against official docs **and** by finding the strings in the installed binary.
They drive most of the design decisions below.

- **`MEMORY.md` is hard-capped at 200 lines OR 25KB.** Content past either cap is **not loaded**.
  Claude Code measures the index after Claude writes it — near a limit it reminds Claude to shorten it,
  over a limit the write still succeeds but Claude Code returns an error telling Claude to rewrite the
  index. This is the single most important one: the file shows nothing either way, so an index that has
  grown past the cap stops working while still looking fine.
- **`@path` imports in `CLAUDE.md` expand inline at session start and count in full.** Imports are
  organizational only — they do **not** defer or reduce token cost. There is no lazy import form.
- **`.claude/rules/*.md` with `paths:` frontmatter loads only when a matching file is read.** Both
  `~/.claude/rules/` (user) and `.claude/rules/` (project). This is the real lever for
  conditional instructions. Globs are relative to the working directory — worth adding `**/`-prefixed
  variants if sessions start in varying directories.
- **Subdirectory `CLAUDE.md` loads on demand**, not at launch; working-directory and ancestor files
  load at start.
- **`claudeMdExcludes`** (settings) glob-excludes CLAUDE.md files and rules dirs by absolute path —
  useful in a monorepo to skip other teams' instructions.
- **`InstructionsLoaded` hook** fires when instruction files load, with matchers including
  `path_glob_match`. Side-effect only (exit code ignored) — good for logging what actually loaded.
- **All skill descriptions load at session start**; `disable-model-invocation: true` in a skill's
  frontmatter drops it to zero cost until manually invoked.
- **Plugin `userConfig`** — declared in `plugin.json`, prompted per user at enable, substituted as
  `${user_config.KEY}`, sensitive values to the keychain, and substitutable into skill bodies. It is
  the *only* real mechanism for per-user values in a shared plugin. Skill bodies otherwise have no
  variables beyond `${CLAUDE_SKILL_DIR}` and backtick command injection.

Docs: <https://code.claude.com/docs/en/memory>, <https://code.claude.com/docs/en/hooks>,
<https://code.claude.com/docs/en/plugins-reference>

## Agent memory architectures — mostly solving a different problem

**Headline: don't adopt a memory server or vector DB for operational knowledge.** That category
extracts durable facts from *conversation transcripts* and recalls them later. The failure mode in a
hand-authored ops knowledge base is different — knowledge going stale because the *world* changed,
not because retrieval missed.

The benchmarks backing those products are also contested:

- Letta's own benchmarking found a **filesystem + grep agent at 74.0% vs mem0's graph variant at
  68.5%**, concluding simpler tools are likelier to be well-represented in training data —
  <https://www.letta.com/blog/benchmarking-ai-agent-memory/>
- Zep's teardown of mem0's SOTA claim, including that a plain full-context baseline beats it on the
  standard benchmark — <https://blog.getzep.com/lies-damn-lies-statistics-is-mem0-really-sota-in-agent-memory/>

**Ideas worth stealing anyway:**

- **Ground each memory to a checkable anchor plus a `check` command**, validated without spending
  tokens. The `mex` project does this with `grounds_to` frontmatter — <https://github.com/mex-memory/mex>
  This is the highest-value idea in the whole space and is what the `check:` convention here is
  based on.
- **Assign lifetime by semantic category.** Bounded memory measurably beat unbounded (39% vs 13% in
  one published domain, 51% vs 32% in another) —
  <https://tianpan.co/blog/2026-04-12-the-forgetting-problem-when-agent-memory-becomes-a-liability>
- **Bi-temporal validity** rather than overwrite — Graphiti closes a fact's validity window instead
  of deleting it (<https://arxiv.org/html/2501.13956v1>). Steal the *discipline* ("true as of X,
  here's what would end it"); skip the graph database.
- **Index as router, not catalog** — Anthropic's own context-engineering guidance is to keep
  lightweight identifiers and load at runtime, which "avoids stale indexing" —
  <https://www.anthropic.com/engineering/effective-context-engineering-for-ai-agents>
- **Separate the write path from the GC path**, and filter staleness at read time rather than
  trusting write-time hygiene — <https://arxiv.org/pdf/2606.15903>

**Do not rely on the model noticing its own stale context.** On the STALE benchmark the best model
scored ~55%, with *implicit conflict* (later evidence invalidating a claim without contradicting it
outright) the dominant failure — <https://arxiv.org/abs/2605.06527>. Invalidation has to be
structural.

## Documentation drift — what actually works

**Colocation buys opportunity, not correctness.** Code comments are maximally colocated and still
rot; mined across ~1,500 systems, with inconsistent comment changes ~1.5× likelier to be
bug-introducing — <https://www.inf.usi.ch/lanza/Downloads/Wen2019a.pdf>,
<https://arxiv.org/pdf/2409.10781>. Proximity means drift *can* be caught in review, not that it will
be. Still worth it — a doc that moves with `git mv` can't name the wrong directory — just don't
expect it to be sufficient.

Practitioner criticism of docs-as-code is that the tooling gets adopted while the process doesn't —
<https://thisisimportant.net/posts/docs-as-code-broken-promise/>

**Staleness detection, weakest to strongest:**

1. **Git age heuristics** (doc last-touched vs code last-touched) — trivially self-buildable, high
   false-positive rate. This is what the bundled `hygiene.py docs` check does; treat it as a smoke
   detector, not a verdict.
2. **Anchored drift linting** — the only mechanically sound version: bind a doc to `path#Symbol@sha`,
   resolve via tree-sitter, compare AST fingerprints. Stated limits: unsupported languages fall back
   to text diffs, nothing detects semantic wrongness, and nothing stops re-stamping the SHA without
   reading — <https://fiberplane.com/blog/drift-documentation-linter/>
3. **Executable documentation — the only mechanism that cannot lie.** Rust doc-tests, `mdbook test`,
   Python `doctest`/Sphinx doctest, `byexample` (<https://pypi.org/project/byexample/>), and `cog`
   for generating doc sections from the source of truth (<https://nedbatchelder.com/code/cog/>).
   Limited to snippet-shaped content — architecture, rationale and ops procedure can't be doctested.
4. **Prose linters and link checkers** (Vale <https://vale.sh/>, markdownlint, lychee) check style and
   reachability, never truth.

**Documentation debt emits no automated signal** — unlike test or type failures, nothing breaks when
a page describes a removed feature.

**ADRs: keep the writing, distrust the maintenance.** The supersede convention degrades because
people update one side and forget the other, and ADRs written after shipping become compliance
theatre — <https://reflectrally.com/architecture-decision-logs/>,
<https://www.jonoherrington.com/blog/how-to-write-adrs-that-actually-get-used>. If a fact will be
*revised* rather than *replaced*, prefer an editable doc beside its subject over a numbered immutable
record.

**Diátaxis** is a useful analytical lens with honest limits — content often doesn't fit one quadrant,
and it doesn't cover runbooks, decision records or changelogs, which are operator genres rather than
user-learning genres — <https://diataxis.fr/>, <https://diataxis.fr/complex-hierarchies/>

## The conclusion that reframes everything

**A stale doc a human skims and ignores is one an agent reads as ground truth and propagates into
code.** Heavy LLM assistance inverts the cost of keeping something "just in case", which makes
**deletion the primary maintenance action** rather than updating. Dead documentation describing
removed features is worse than absent documentation, and there is no team-knowledge safety net
catching it.

## Community conventions worth knowing

- **`/doctor` includes a CLAUDE.md trim check.** Its heuristic is the most portable deletion rule
  found: cut what the agent can derive from the codebase (directory layouts, dependency lists,
  architecture overviews); keep pitfalls, rationale, and conventions that differ from tool defaults.
- **Size targets people actually cite:** under ~300 lines, with root files far smaller; prefer
  `file:line` pointers over inlined snippets because snippets rot —
  <https://www.humanlayer.dev/blog/writing-a-good-claude-md>
- **Committed vs agent-local splits by authorship**, not by project: `CLAUDE.md` committed for shared
  standards, `CLAUDE.local.md` gitignored for personal values, auto-memory machine-local.
- **No converged convention exists for skills carrying instance config.** Plugin `userConfig` is the
  only real mechanism; most repos gitignore a `.env` with a tracked `.env.example`.
- **Audit tooling is thin and young.** Worth knowing: `agents-lint` verifies that referenced paths and
  scripts still exist (<https://github.com/giacomo/agents-lint>) — the idea behind the bundled
  dangling-reference check. Nothing real exists yet for contradiction detection across memory files
  or for memory pruning.
- **Skill preload cost is real**: one popular collection was measured preloading ~22k tokens (~11% of
  context) rather than the ~1.4k the progressive-disclosure model implies.
