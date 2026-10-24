# Assume the panel is lying, then check

Load before calling any dashboard done, and whenever a number on it will be acted on — stage 5 of `SKILL.md`. This is
what separates a dashboard from a decoration: every trap below *(incident)* shipped a plausible wrong number that a
human caught later. A check is proved by listing what the query actually read — the series set, the coverage, the
response object — never by the number looking reasonable.

## The number

**Aggregate deliberately.** The obvious aggregation is often wrong by a clean integer factor, which makes it look
plausible. A volume mounted on five nodes is reported five times — `sum()` quintuples it, `max by (...)` is correct.
Before shipping any `sum()`, list the series set rather than assuming what it contains.

**Check field coverage before summing a field.** A field present on only half the documents sums to half the truth,
silently — and two datasets with different coverage are not comparable to each other either. In SQL,
`count(col)::float / count(*)` (`count(col)` skips NULLs) costs one query and is not optional.

**Confirm the field means what its name suggests.** Two date fields both fully populated, both plausible, answering
different questions — "when the sensor took the reading" versus "when the gateway uploaded it" — give completely different charts
and neither looks broken. Pick with the question in hand.

**Read what the query actually returned, not what you asked for.** A server's request handler can carry default work
(facets, includes) the query never named, so "the same thing" through two mechanisms is not the same question. The
response object says so. A timing comparison between two mechanisms is only valid if both were asked the same question.
Measured case: 11.9 s against 1.6 s, all of it hidden default facets.

## Absence

**A failed collection renders differently from a real zero.** Export a separate `up`/`scrape_success` gauge, render
unknown as `—` with a tooltip, and make "no data" visually distinct from "zero" — a probe that stores `0` on failure
makes a broken collector and a healthy system identical.

**`No data` is ambiguous, and worse the more the dashboard matters.** It means either "this broke" or "this was never
wired up", and the panel cannot say which. On a *backup* dashboard the difference is everything: a section of `No data`
panels read as "backups have stopped reporting" when the real cause was a metric family that needs a push gateway
nobody deployed — and it had been that way long enough that nobody trusted the dashboard. **Delete a panel whose metric
is not plumbed, or put the reason in the panel description** — an honest absence beats a permanent false alarm.

**A threshold or reference line needs a citable source.** One written from memory is confidently wrong for every input
and the panel gives no hint; omit the row rather than guess.

## The cost: time panel queries in two passes, and report the second

A dashboard's panels mostly read one window of one table, so **the first query to touch that window pays the cold-cache
cost for every panel after it** — and that cost lands on whichever panel happens to run first, an ordering artifact,
not a property of the panel. Measured on a Postgres-backed dashboard: pass one said 10.45 s for a panel that pass two put
at **0.63 s**, a 16× error, and the panel it accused was one of the cheapest on the page. The single-pass total was
20.8 s against a warm 11.1 s.

It fails in the direction that gets acted on: an inflated worst-panel number reads as "near the timeout, go optimise
it", so the ordering artifact gets a fix and the real worst panel keeps its cover. Run the whole set twice against a
live database and read the second — and if only one pass is possible, say the numbers are cold rather than quoting them
as the dashboard's cost. (`bug-hunt`'s `references/oracles/performance.md` points here for any multi-query timing.)

## The pixels: render it and read it

Load the dashboard in the target Grafana version and read the rendered page — `headless-render` covers doing this
without a browser on the host, and a browser integration works when you have one. Every Angular-panel and schema finding
derived from JSON is a *prediction* about rendering; an audit that never rendered anything should say so.

**A whole class of defect is invisible to every static check, because it is about pixels.** Measured on a live
dashboard that scored **13 metrics referenced, 0 absent** — a clean bill of health from static analysis:

- **Seven of eight stat titles truncated to one letter**: `P…` `T…` `R…` `L…` `C…` `C…` `C…`. Three were identical. The
  numbers were fine and completely unidentifiable.
- **Three panels reading `N/A`**, styled exactly like the panels reading real values, beside a `0 B` that could equally
  have been a real zero or another missing measurement.
- **A table showing raw label columns** — `container`, `endpoint`, `instance`, `job` — with the only useful column
  pushed off the right edge behind a scrollbar, and a leaked transformation control rendering as page furniture below
  it.

None of that is detectable from the JSON, from metric coverage, or from panel types. **Budget the render step; it is not
optional polish.** And **wait for the page to settle** before judging it — the same dashboard was entirely blank at 8 s
and fully populated at 19 s, so an early screenshot manufactures a defect that is not there.
