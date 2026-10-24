# Panel and query traps

Load when building or reviewing individual panels and their queries — stage 3–4 of `SKILL.md`. These are the panels
that render, have data, and say the wrong thing or nothing useful. A finding here is proved by arithmetic on what the
panel actually shows (series count, distinct values, row count), not by how it looks.

## A wall of numbers is the commonest wrong panel; the test is arithmetic

A Stat panel fed a multi-series query silently renders **one tile per series**. Nobody chooses this; it happens when a
`sum by(...)` returns more labels than the author had when they built it. The result looks deliberate and is almost
always wrong.

**The test: count the series, then count the distinct values.** *(incident)* Two live panels here: one rendered 26
tiles carrying **2** distinct values (three names were the whole message), another 9 tiles in **2 cohorts** carrying one
fact. Because every tile is the same size and colour, the outliers are *harder*
to find than in a sorted list — the design buries its own signal, while the captions shrink to a few illegible pixels.

**And the outliers are often noise.** *(incident, same panel)* Chasing the outliers led to an aggregation bug, not a
finding. **A `sum by()` that drops a label which distinguishes different *kinds* of thing produces a number that is
arithmetically valid and semantically meaningless** — and a reader who investigates the variance spends an hour
reaching "no finding". Before shipping an aggregation, list the label set you are summing over and ask whether every
member means the same kind of thing.

**When tiles ≫ distinct values, the information is the exception, so show the exception:**

- **One number** — `count(x != <expected>)`, or the `min()` where only the worst matters. "Nothing has restarted" is a
  single stat, not nine; the minimum uptime is the only one that can be bad.
- **A table sorted ascending**, so outliers land at the top and every row keeps its label.
- **A time series**, when the shape is the point — restarts show up as sawtooth drops, which a current-value tile cannot
  show at all (change blindness, `SKILL.md` stage 3).
- **A bar gauge**, if you genuinely need per-item comparison at a glance.

**Ask what a reader does differently based on this panel.** If the honest answer is "nothing, unless one of them is
odd", the panel's job is to surface odd ones — and a uniform grid is the worst available tool for that.

**A Stat showing a cumulative counter's last value ignores the dashboard time picker entirely.** *(incident)* A
jobs-since-the-operator-started counter: "Last 7 days" changes nothing while strongly implying it does. Either scope it
(`increase(...[$__range])`) or say in the title that it is a lifetime total.

## Query craft

**`$__rate_interval`, not `$__interval` or a hardcoded window.** It resolves to
`max($__interval + scrape_interval, 4 × scrape_interval)` and fixes two silent failures: panels going "No data" when you
zoom in, and counter increments falling between windows — which produces a *wrong* number, not an empty one.

**Inventory is a gauge; ingest is a counter.** "How many items exist" must be a gauge — a counter that decreases on
delete or dedupe reads as a reset, and `rate()`/`increase()` will silently add a phantom increase. Keep both if you want
both questions answered. And `increase()` extrapolates to window edges, so it returns **non-integers from whole-number
counters**; set decimals to 0 or explain the fraction.

**Repeat, don't duplicate.** Template variables with repeating rows/panels are the officially named anti-sprawl
mechanism — "you don't need a separate dashboard for each node." Folders and tags are secondary to this, not a
substitute for it.

**Drill-down is links, not a primitive.** Dashboard link if it applies to most panels, panel link for a specific panel,
**data link for a specific series or single measurement**. Carry the time range and variables across
(`${__url_time_range}`, `var-<name>=${__field.labels.instance}`, `${__data.fields["col"]}`) or the drill-down lands on
the wrong host at the wrong time — which looks like working navigation and is worse than a dead link. Dashboard links
defined **by tag** auto-populate, so an overview never has to enumerate its children.

## Panel mechanics that bite

- **Value mappings bypass unit and decimal formatting.** A mapped value renders raw.
- **Percentage thresholds compute against the panel's Min/Max**, so set those explicitly or the thresholds mean nothing.
- **"Bars over time" is the Time series panel with Draw style = Bars**, not the Bar chart panel. Grafana says so
  explicitly, and people reach for the wrong one constantly.
- **Table + `Time series to table` gives sparkline cells** — the highest-value panel for any "inventory with trend"
  view, and much better than N separate stat panels.
- **Size a table by its row count, not by what looks balanced in the grid.** *(incident)* A table with more rows than fit
  gets a vertical scrollbar, the scrollbar consumes horizontal room, and the *last* column — in a sorted table usually
  the value everything else exists to qualify — slides out of view behind a horizontal scrollbar. Widening the panel
  does not fix it and neither does pinning column widths; both were tried on the same panel before the actual fix,
  which was **enough height for every row**. Count the rows the query returns, then give the panel that many.
- **State timeline is the right panel for job runs**, because a gap reads differently from a failure. A bar chart of
  successes cannot show "it never ran."

## Layout rules quoted backwards

- **The F-pattern is not a target.** Nielsen Norman explicitly call it **bad and preventable** — what the eye falls back
  on when a layout gives it nothing to grab. Design for their "layer-cake" pattern, where headings do the navigation.
- **Miller's 7±2 governs what you make someone *remember*, not how many panels may be *visible*.** Simultaneous
  visibility removes cognitive load, so putting things on one screen is the fix, not the problem.
- **Group with borders and rows, not proximity alone.** Common region is a stronger grouping cue than spacing, and rows
  give you the collapsing and repeating machinery for free.
