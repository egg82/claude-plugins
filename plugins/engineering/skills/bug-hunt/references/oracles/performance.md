# Performance oracles — a number against a budget

Load for a performance hunt or any finding whose harm is "slow", "heavy" or "expensive". The oracle is a measured cost
compared with a budget or with the work actually needed: queries per request against the rows shown, bytes sent
against bytes used, CI minutes against the critical path. The universal tell is **a cost that scales with rows, frames,
users or time while the visible result does not change.** "This looks slow" is not a finding; a number with the profile
that explains it is.

## Cover the whole path, dealt by layer

A user action crosses every layer below, and hunts drift to whichever is easiest to read. Write one shared list of
user actions (the most-opened page first), deal finders out **by layer** over that list so their numbers join up, and
start from field data when the app has it (real-user timings per load: network phases, app marks, first frame, cache
hits). Add it when it doesn't. *(incident)* A lab run on a fast desktop on the same network missed a 10–15 s load
for users on slow connections whose server side took 3.5 s.

| Layer | Measure | Tells |
|---|---|---|
| **Database** | queries per request; `EXPLAIN (ANALYZE, BUFFERS)` of the slowest; rows read vs returned; `pg_stat_statements` totals | N+1 (an ORM lazy load in a loop), a seq scan on a growing table, an index defeated by a cast or function, `OFFSET` pagination, `count(*)` used as an existence check, `SELECT *` feeding one field, a lock held across a network call |
| **API** | requests per screen and per idle minute; sequential round trips before first paint; payload bytes vs fields the client reads; 304 rate | a write followed by a refetch, a list endpoint returning whole objects, polling faster than the data changes, no `ETag`/`Last-Modified`, no batch form so clients loop |
| **Caches** | hit rate per tier; cost of a miss; behaviour on expiry under concurrent load | a key missing a dimension (also a correctness bug), a stampede when a hot key expires, a failure cached as a value, a cache invalidated by every write, eviction under real churn |
| **Server compute** | profile through the real entry point (`py-spy`, `perf`, a JVM's `async-profiler` or JFR); per-request and per-job cost | work redone per request that could be done once, blocking I/O inside an async loop, serialization dominating the profile, a regex with nested quantifiers on user text (also a ReDoS) |
| **External calls and spend** | calls per user action to paid APIs and LLMs; tokens per call; retries per failure | one action fanning out to N paid calls, a whole history resent per LLM call, retries multiplying spend on a failing upstream, a result that could be cached by input |
| **Page load** | TTFB, first contentful and largest paint, time to interactive; bytes and requests (Lighthouse, a WebPageTest or DevTools trace on a throttled profile) | a render-blocking script or font, a JS bundle carrying a whole library for one function, unsized or full-resolution images, hashed assets without long-lived cache headers |
| **Runtime** | FPS and frame-time percentiles over a long idle and the busiest scene; long tasks; heap over an hour | re-render per keystroke, layout thrash (read-write-read of layout in a loop), timers still running in a background tab, listeners added per mount and never removed |
| **Latency** | round trips per action under injected delay (below) | UI state set only after an `await`; a busy flag that blocks every other control while one request is out |
| **Bandwidth** | bytes per screen and per idle hour; compression on the wire | re-downloading what could be kept, audio and images in formats several times the needed size, uncompressed JSON |
| **CI** | wall time per job and the critical path; cache reuse; image size and layer pulls; `pytest --durations` | dependencies installed from scratch each run, a Dockerfile copying source before installing deps (every commit busts the cache), serial jobs that don't depend on each other, tests that `sleep`, the same suite run twice under two job names |

**Latency, in detail.** Local harnesses talk to localhost, so every hunt sees zero latency and the defect is invisible
to all of them. For each user action count the *sequential* round trips before its visible result and whether it
blocks other actions, then run it under 300–500 ms per request (a fetch wrapper or a delaying proxy) and screenshot
~50 ms after the action. *(incident)* Four hunts, two on performance, measured server time and frame time; a tester
on a slow connection found a tap that took two long round trips to show. What a dropped or failed request does is
`resilience.md`.

## Proof

A finding is proven by **a count or plan that a fix would change** — queries per request, rows scanned, call count,
bytes — or **complexity shown at two sizes**. Quote a latency only measured twice, cold and warm separately, with what
else was running (`top -bn1 | head -15`) beside it.

The test that lands a fix **asserts the count**, never a wall-clock bound. Never assert a query *plan* on a scratch
table either *(incident)*: several indexes cost alike on a tiny table and the tie-break differs by machine (one such
test passed locally and failed in CI). Pin what can silently break instead (a partial index's predicate repeated in the
query) and carry the planner's real preference as a production-copy measurement in the commit message.

## Traps that produce a confident wrong number

- **"Read-only" is not harmless against production.** A read is load, and a perf hunt fires the slowest reads there
  are. *(incident)* Three agents timing routes and `EXPLAIN ANALYZE`-ing the slowest reads at once used up every
  connection slot on a small shared Postgres, and real users' logins queued and timed out for about a quarter of an
  hour; the "replica" one agent picked by hostname was an alias repointed at the primary for maintenance that morning.
  Before briefing one: read the database's limits and headroom (`max_connections` included); let ONE agent send heavy requests, serialized; pick the
  replica by role label at every call; give every probe a client timeout and a session `statement_timeout`, because an
  abandoned request's query keeps running.
- **Hammer a copy, not the cluster** *(incident, same episode)*. `pg_dump -Fc` from the replica, restored into a local container with production's
  limits (`--memory`, `--cpus`, `shared_buffers`), one container per execution agent so their timings don't measure
  each other; keep production for light confirmation after the fix ships. Then turn on `log_min_duration_statement` and `auto_explain` (with `log_analyze`) and replay every route
  once: the whole slow-statement inventory, with plans and JIT time, in one pass. Never set
  `session_preload_libraries` to `''` — libpq then fails every new connection with `could not access file ""`; use
  `RESET`.
- **A seeded fixture is not production's shape.** *(incident)* One seed wrote one parent row per kind and few children
  per entity, and hid the two largest costs. Real row counts and skew, or say the numbers are from a toy.
- **A rootless-podman published port is not a latency instrument.** *(incident)* The forward stalls ~208 ms at response
  sizes between 8 and 65 KB. Time server-side or from inside the container's network namespace
  (`verification-gate`'s `instrument-failures.md`).
- **The first query to touch a window pays everyone's cold cache.** *(incident)* Timing a set of queries over one
  table once blamed a panel at 10.45 s that a second pass put at 0.63 s. Run the set twice and quote the second, or say
  the numbers are cold (`grafana-dashboards`' `references/panel-truth-checks.md`).
- **Concurrent agents share the host.** A correctness hunter or a writer on the same box contaminates wall-clock
  timings; prefer counts and plans, and say what else was running.
- **A fix can move cost rather than remove it.** *(incident)* A cache fix took a drill-down from three builds to one by
  building more per request, and made the landing page several hundred ms slower; its own build-count tests could not
  see it. Before merging, time the app's most-opened path before and after on the production copy, not only the path
  the finding named.

## Impact

Value is cost × frequency on the paths people actually use: a 2 s saving on a page opened once a month loses to 80 ms
on the landing page. Answer impact's WHO / HOW OFTEN with the field data or access logs, not with the route's name.
