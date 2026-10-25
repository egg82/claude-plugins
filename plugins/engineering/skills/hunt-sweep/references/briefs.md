# Hunter brief templates

Every lane shares the RESOURCES and RULES blocks; only TASK differs. Fill every `<placeholder>` from
the assignment table. Wave 2 uses the same text with its own `<id>`, worktree, port and paths.

## Shared header

```
[opus: open-ended hunt; the hunter decides what counts as a real defect, and precision matters]
   (drop this line if you chose a model other than opus)

Load the `bug-hunt` skill first, then the `agentic-engineering` skill. Follow bug-hunt's method, and
read its `references/oracles/correctness.md` and `references/oracles/<lane>.md` before hunting.
<correctness lane only, when the repo has the surface: "Also read oracles/resilience.md /
state-over-time.md / ui-and-accessibility.md / llm-features.md"; keep only the live ones>

Load these when your hunt reaches the layer, not up front:
<paste the rows of SKILL.md's layer-skill table that apply to this lane, as "layer: `skill`" lines>
```

## TASK — correctness lane

```
**Task:** a GENERAL bug hunt of <repo> (<one line on what it is and its stack>). Scope is every
layer: DB queries and migrations, the API, the frontend, CI (<ci file>, the test gates and their
controls), the Dockerfile and image, scripts and jobs, and the seams between them. Hunt for
correctness bugs and requirement gaps against the repo's own stated contracts (<the files that state
them: CLAUDE.md rules, engineering doc, design docs>). Not style, not "could be cleaner", not defensive
additions. You MUST confirm every finding by EXECUTING the code (a failing test or a repro script);
a finding you cannot demonstrate by running something is not a finding. A short well-supported list,
or a null, is a valid answer; do not pad.
```

## TASK — performance lane

```
**Task:** a PERFORMANCE hunt of <repo> (<one line>). Scope is every layer: DB queries, indexes and
migrations, the API, the frontend, CI (job time, caching, image rebuilds, redundant jobs or steps, slow
tests), the Dockerfile and image, scripts and jobs, calls to external APIs, and the seams between
them. Read <the repo's measurement docs and benches> first. Each finding must be proven by execution
with a count or plan that a fix would change (query count, rows scanned, EXPLAIN ANALYZE, call count,
complexity shown at two sizes); not "this looks slow". For CI, read the config and produce local
evidence such as `pytest --durations`; don't call the CI server's API. A short well-supported list,
or a null, is a valid answer; do not pad.

**Measurement hygiene:** a correctness hunter runs concurrently on this host, so wall-clock timings
are contaminated by its load. Prefer counts and plans. If you must quote a latency, measure it twice
spaced apart, report cold and warm separately, and note what else was running (`top -bn1 | head -15`).
```

## TASK — security lane (only when the repo has the surface)

```
**Task:** a SECURITY hunt of <repo> (<one line>). Read bug-hunt's `references/oracles/security.md`
first; it is your method. The live surface is: <auth/identity mechanism and roles>; <every permitted
write to an external system and the guard on it>; <where untrusted input enters (host-supplied
output, request params, uploaded files) and where it lands (SQL, HTML, external writes)>. Ask what an
attacker or a hostile host controls and what that reaches. You MUST confirm every finding by
EXECUTING it locally against your own instance; nothing live. A short well-supported list, or a
null, is a valid answer; do not pad.
```

## RESOURCES

```
**Your resources (yours alone):**
- Worktree: `<worktree>` (detached at <base ref> <sha>). Work ONLY there; never touch the main
  checkout or other worktrees. <If editable install:> run with `PYTHONPATH=<worktree>` and prove it:
  `<python> -c "import <pkg>; print(<pkg>.__file__)"` must print a path under the worktree.
- Database: `<DB URL env var>=<url with your port>`. Do not use any other database or container.
- Findings: append one JSON record per finding to `<scratch>/hunts/<id>-findings.jsonl` AS YOU GO
  (fields: title, file_line, mechanism, repro (command + observed vs expected, or the measured
  figure), severity, confidence). Scripts go under `<scratch>/hunts/<id>/`. You may add test files in
  your worktree to prove a bug, but do not commit, push, or open MRs/issues.

**Siblings:** <the other lane's hunter> is running at the same time in `<its worktree>` on port
<its port>. Don't touch its resources.
```

## RULES

```
**Rules:**
- Read-only with respect to the outside world: never run <the repo's commands that reach production,
  vendor APIs, clusters or the live site, by name>. No credentials; if something needs one, note it
  and move on. If the permission classifier denies something, do not route around it; say what you
  needed and carry on.
- Explicit worker counts (`pytest -n 2` at most) if the venv has pytest-xdist; check before writing
  this line into a brief — without xdist `-n` is an argument error, and serial is the only option. Each Bash call finishes within 10 minutes
  (timeout 600000, one test dir per call).
- Never raise a held count or loosen a check.
- Memory probes stop at about 300 MB RSS: show growth at two or three small sizes and extrapolate. On a shared
  host, three hunters plus one probe pushing a server toward 600 MB OOM-killed the orchestrating session.
- You are a LEAF agent: do not spawn subagents, no forks. Do NOT use `run_in_background`, do NOT
  start a Monitor, do NOT use foreground `sleep`; make blocking calls in small batches.
- Budget: roughly 2 hours of work; then report with what you have.

**Report back** (short): the findings file path, and per confirmed finding one line: title,
file:line, how proven (or the measured figure). Also list hypotheses you killed and the probe that
killed each.
```
