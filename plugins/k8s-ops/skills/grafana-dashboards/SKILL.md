---
name: grafana-dashboards
description: "Find, vet, adapt or build a Grafana dashboard someone will actually read — reuse-vs-build, layout that survives a glance, query traps that ship wrong numbers, dashboards as code. Use when creating a dashboard or panel, importing one, auditing stale/empty dashboards, a dashboard is slow or nobody looks at it, before building any monitoring view, or choosing USE vs RED vs golden signals. NOT alert rules or general charts (dataviz)."
---

# Build a dashboard someone will read

Most dashboards fail quietly. They render, the panels have data, and nobody opens them — or worse,
somebody opens one during an incident and it answers a question they weren't asking.

Two failures dominate, and neither is aesthetic:

- **The dashboard was built before anyone said what decision it supports**, so it shows what was
  easy to query.
- **A panel is confidently wrong.** The query succeeded, the number is plausible, and it is off by
  half. Nothing in the UI distinguishes this from a correct panel — stage 5 is about making it distinguish.

`~/.claude/local/grafana-dashboards/instance.md`, if present, holds the environment-specific parts: how dashboards are
provisioned here, datasource UIDs, verified metric traps, and the worked cases behind the references.

**Which reference:**

| Stage | Load |
|---|---|
| 1 — importing or adapting an existing dashboard (grafana.com, a mixin, a repo); `vet-dashboard.py` | `references/sourcing-and-vetting.md` |
| 3–4 — building panels: a grid of stat tiles, aggregation, `rate`/`increase`, links, tables, panel types | `references/panel-and-query-traps.md` |
| 5 — before calling it done; a number someone will act on; a slow dashboard; the render check | `references/panel-truth-checks.md` |
| Chart form, colour palettes, stat tiles in general | the `dataviz` skill |
| A data-heavy page that looks dead or sterile | the `ui-craft` skill |

## 1. First decide whether to build anything

**Reuse beats authoring, and the bar for "reuse" is lower than people assume** — an upstream
dashboard tracks its own project's metric renames, which is the maintenance cost you are really
choosing between.

Order of preference:

1. **The project's own dashboard**, shipped in its repo or Helm chart. It moves when the metric
   names move.
2. **A monitoring mixin** (`kubernetes-mixin`, `ceph-mixin`, the `monitoring-mixins` ecosystem).
   Actively maintained, but jsonnet-gated — a Prometheus maintainer conceded "nobody wants to
   learn it." Pull the rendered `dashboards_out/` JSON and skip the toolchain.
3. **grafana.com**, vetted mechanically — download counts are worthless; `updatedAt` and
   `schemaVersion` discriminate. Run `vet-dashboard.py` beside this file (metric existence, Angular
   panels, import cruft, panel count); details and the API traps in the sourcing reference.
4. **Steal the layout, write your own queries** — the middle ground, and the one most often
   skipped. It applies whenever the *questions* are standard but the *data model* is yours: a
   bespoke schema, a custom exporter, an app-specific table. Its panel inventory, sectioning and
   choice of visualisation transfer, and the popular ones have had far more eyes on their layout
   than a first draft of yours will. **Read the JSON of the two or three best and take the panels
   you lack** — and expect the merge to run both ways (worked case in the sourcing reference).
5. **Author it from scratch** — only for what nobody else can have: an app's business metrics,
   blackbox probes against your own endpoints, a custom exporter, queue depths, content statistics.

**Before authoring, ask whether the app already ships this view.** Many applications have a
statistics page far better than what you would rebuild — and it is maintained by someone else. The
question is not "could Grafana show this" but "what does Grafana add that the app's own UI does
not?" Usually the honest answer is: cross-app comparison, infrastructure context the app cannot
see, and history the app does not keep. That is a narrow, valuable gap — and it is a *small*
dashboard, not a suite. If you are past ~8 panels re-implementing an app's own stats page, stop.

**A dashboard for something you do not run is worse than no dashboard.** It reads as "broken"
rather than "not applicable", and it survives for years because nobody can tell the difference.
Scope what you provision to what each environment actually runs.

## 2. Name the question before choosing panels

**Match the framing to the thing being watched.** This selection rule is settled and quotable:

| Subject | Framing | |
|---|---|---|
| Hardware / resources | **USE** — Utilisation, Saturation, Errors | "tells you how happy your machines are" |
| Request-driven services | **RED** — Rate, Errors, Duration | "tells you how happy your users are" |
| Either, plus saturation | **Four Golden Signals** (Grafana calls it REDS) | |
| **Batch / pipeline jobs** | **freshness, correctness, coverage, throughput** | none of the above three apply |

That last row is the one people get wrong. Pipelines are not request-driven and are not hardware;
the SRE Workbook's data-processing chapter covers them, and the reason is that "the pipeline can
eventually complete all work even if it breaks." **Freshness is the metric that matters and the
one worth alerting on**: `time() - <job>_last_success_timestamp_seconds`. A failure counter cannot
fire when the job stopped being *scheduled* at all.

**Alerts detect; dashboards investigate.** Grafana's own position, and it has a corollary that
saves a lot of work: alert on symptoms (RED), investigate causes (USE). Anything merely true —
headroom, utilisation, latency that is fine — belongs on a dashboard and not in a channel.

**The strongest evidence in this entire field says signal quality dominates pixels.** From clinical
and process-control alarm management: 80–99% of ICU monitor alarms are false or non-actionable, and
the interventions that worked were *threshold and timing* changes, not better displays — lowering
one limit with a **15-second delay cut alarms by over 80%**. EEMUA 191 records that a flood
condition leads to "the operator abandoning the use of the system." **`for: 5m` on a rule
outperforms any layout change you can make.** If a dashboard exists to compensate for noisy alerts,
fix the alerts.

## 3. Lay it out for a human

**Density is not the sin — undifferentiated density is.** Grafana's own community-voted showcase
praises winners for "an abundance of information" and "hundreds of metrics"; the praise always
attaches to the *structure* that survives it — rows, sections, a bird's-eye layer. Nobody praises
minimalism, and no source anywhere states a panel-count limit. What is fatal is not quantity, it is
a comparison hidden behind a tab, a dropdown, or a collapsed row.

**Build two tiers.** The most-endorsed structural choice in the research, arrived at independently
by Grafana's judges and by Hacker News: *simple answers in big type at the top for someone who is
not an engineer, detailed metrics below for someone investigating*. The HN version: "dashboards
should tell a story… even for someone who's on their first week."

**A dashboard cannot be a notification mechanism.** Change blindness is the relevant result and it
is robust: a slow drift produces no motion transient and is simply not seen, and any change across
a refresh, a tab switch, or a look-away is masked exactly like the flicker paradigm. So a panel
showing only a current value is showing the one thing a human is worst at monitoring. **Encode
deltas, baseline bands, and trend shape** — convert an undetectable temporal change into a
detectable spatial one. The Stat panel's percent-change field is the cheapest version of this and
is routinely missed.

**Alert state must differ on exactly one otherwise-unused channel.** If "bad" is signalled by both
colour and position, and colour is also used decoratively for series identity, you have built a
conjunction search — and detection time then scales with panel count. This is the mechanism behind
*grey by default, colour by exception*. Spend colour on status; use it for nothing else.

**Colour must not be the only encoding.** ~8% of men are colourblind, and the recorded operational
failure is not theoretical — someone screenshotting a dashboard into a photo editor mid-incident to
tell two series apart. Pair every colour with a shape, position, label, or explicit value.

**Check that the threshold points the same way the metric does.** A default "high is bad" threshold
applied to a metric where high is *good* inverts the meaning, and nothing warns you. Seen live: an
"Avg uptime per node" panel rendering every node's uptime in alarm red, because a long uptime
tripped a high-value threshold. **Every tile red** and **every tile green** are the same defect —
colour that has stopped carrying information. If a status colour never varies, delete it or fix the
threshold; a panel where everything is green teaches people to stop looking.

**A Stat fed a multi-series query renders one tile per series — count the series, then the distinct
values.** When tiles ≫ distinct values, show the exception instead (one number, a sorted table, a
time series). This and the rest of panel and query craft are in `references/panel-and-query-traps.md`.

## 4. Panel and query craft

Load `references/panel-and-query-traps.md`. The rules that fire on every panel: **`$__rate_interval`**,
never `$__interval` or a hardcoded window; **inventory is a gauge, ingest is a counter**; **repeat
rows/panels from a template variable** rather than duplicating dashboards; **drill-down links carry
the time range and variables** or they land on the wrong host at the wrong time.

## 5. Assume the panel is lying, then check

Load `references/panel-truth-checks.md` before calling it done. In one line each: **list the series
set before any `sum()`**; **check field coverage and field meaning**; **read what the query actually
returned**; **a failed collection renders differently from a real zero** (`—`, not `0`; delete or
explain an unplumbed `No data` panel); **time panel queries in two passes and quote the second**;
and **render it in the target Grafana version and read it**, after the page has settled — a whole
class of defect is only visible in pixels.

## 6. Store it as code

**Raw JSON in git, generated into a ConfigMap, picked up by the Grafana sidecar.** For anything
short of a multi-team estate this beats every alternative, because it adds no new components.

Skip grafana-operator, Terraform, Crossplane, grafonnet and the Foundation SDK unless you have the
problem they solve, which is **templating the same dashboard across many environments**. A homelab
or a single cluster does not have that problem.

Settings that matter: `allowUiUpdates: false` (so the UI cannot silently fork provisioned JSON),
`searchNamespace: ALL` if dashboards live beside their apps, a **pinned datasource UID constant**,
a **pinned dashboard `uid`**, and `id` stripped. Generate ConfigMaps with the name-suffix hash
disabled — the sidecar keys off the label, and a hash churns a new ConfigMap per edit and orphans
the old one.

**Round-tripping is the hard part, and 2026 changed it.** Dashboard **schema v2 is GA and on by
default**; a v1 dashboard silently migrates to v2 on load, so edit-in-UI-then-export is a one-way
ratchet on your stored JSON. **Do not use "Export for sharing externally"** on your own dashboards
— it emits an import template whose `${DS_PROMETHEUS}` file provisioning cannot resolve. Pull with
`gcx` (`grizzly` is archived, `grafanactl` was the interim name), or point Git Sync at a separate
repo your GitOps controller does not reconcile.

**Write down why a dashboard came from where it came from**, next to the dashboards. Sourcing
decisions expire — upstream moves, a maintained alternative appears, a component gets removed from
the fleet — and the note is the only thing that tells the next person the decision was *made*
rather than defaulted into. Keep it beside the JSON, not in a memory or a wiki, and re-check
"no good upstream exists" verdicts on a clock.

## Checklist

- [ ] Does a maintained upstream or app-native view already answer this? Is the gap really this big?
- [ ] `updatedAt` and `schemaVersion` checked; download count ignored
- [ ] Every referenced metric resolves to a non-zero series in the target environment
- [ ] No Angular panel types; no `__inputs`/`__requires`; no foreign datasource UID; panel count > 0
- [ ] The framing matches the subject (USE / RED / golden signals / pipeline freshness)
- [ ] Big answers at the top, detail below
- [ ] Status colour is on one otherwise-unused channel, and is never the only encoding
- [ ] Panels encode change, not just current value
- [ ] `$__rate_interval` used; inventory is a gauge; aggregation verified against the real series set
- [ ] Field coverage checked before any `sum()`; date field confirmed to mean what you need
- [ ] A failed collection renders differently from a real zero
- [ ] Loaded and read in the target Grafana version
- [ ] Provisioned from git with pinned uid, `allowUiUpdates: false`, and a note saying where it came from
