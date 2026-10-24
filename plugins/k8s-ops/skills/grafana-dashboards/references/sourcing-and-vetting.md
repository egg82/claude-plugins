# Sourcing and vetting an off-the-shelf dashboard

Load when choosing between the project's own dashboard, a mixin, grafana.com, or stealing a layout — i.e. stage 1 of
`SKILL.md`, before importing anything. A vetting finding is proved by a field read from the API or the JSON, never by
reputation or download count.

## Vet mechanically, not by download count

**Download counts are worthless as a quality signal.** Measured on grafana.com's public API:

| id | dashboard | downloads | last updated | schema | Angular panels |
|---|---|---|---|---|---|
| 1860 | Node Exporter Full | 141M | 2026-04-11 | 41 | none |
| 13659 | Blackbox Exporter | 51M | 2020-12-31 | 26 | `graph` |
| 315 | Kubernetes cluster monitoring | 22.7M | 2023-03-20 | **12** | `graph`, `singlestat` |

Dashboard 315 has 22.7 million downloads and declares a Grafana 3.1.1 requirement with panels stored under `rows`.
**`updatedAt` and `schemaVersion` are the only two fields that discriminate.** Ratings have sample sizes in the single
digits.

**The API.** `https://grafana.com/api/dashboards/<id>` is unauthenticated and returns both fields. Pull a dashboard's
JSON with `/api/dashboards/<id>/revisions/latest/download` (what "steal the layout" needs).

**The search parameter is `filter=`, not `search=` — and send nothing else alongside it.** *(incident)* Adding the
obvious `&orderBy=downloads&direction=desc&limit=12` returns `{"items":[]}` with HTTP 200, indistinguishable from a
niche that genuinely has no dashboards. Measured: `?filter=netflow` returns 8 results; the same query with those three
parameters returns 0, and the empty set is what would have been written up. Control-probe any empty result against
`/api/dashboards/1860` before concluding a field is bare — that is what caught it.

## Four checks before adopting

All cheap, all mechanical:

- **Does it reference metrics you actually have?** Extract the expressions, query your
  `/api/v1/label/__name__/values`, and count how many resolve to zero series. The single highest-yield check, and the
  one nobody runs.
- **Angular panels.** Grafana 12 removed AngularJS entirely. Flag `"type": "graph"`, `"singlestat"`, `"table-old"`,
  `"grafana-piechart-panel"`. Core types force-migrate to React; third-party Angular plugins were pulled from the
  catalogue and are **unrecoverable**.
- **Import cruft.** A downloaded dashboard carries `__inputs`/`__requires` binding its datasource through the
  interactive import wizard — which file provisioning never runs. Left in, every panel comes up unbound. Strip them and
  rewrite `${DS_*}` to your datasource UID. Also grep for hardcoded foreign UIDs; Grafana Cloud's `PBFA97CFB590B2093`
  shows up in exported dashboards surprisingly often. Grep case-insensitively and on the `datasource` field, not on
  `"uid"`: auto-generated UIDs are lowercase or mixed (`adg1f3kqrxxx`), and a dashboard-as-code pins its own `uid` too,
  so an uppercase-only grep misses the modern ones and a blob-wide one flags itself.
- **Panel count.** A dashboard that failed to parse still writes a perfectly valid file — with no panels in it. Count
  them after any conversion; zero is the parse-failure signature.

**`vet-dashboard.py` (beside `SKILL.md`) runs all four.** `vet-dashboard.py remote <id>…` scores grafana.com candidates
before you import one; `vet-dashboard.py local <json>…` scores JSON you already have. Adding `--prom-cmd` (any shell
template printing the Prometheus HTTP API to stdout, with `{path}` substituted) turns on the metric-existence check;
without it the `absent` column reads `n/a` rather than blank, because an unrun check must not look like a passed one.
It reports and never edits, and it shouts when a dashboard has panels but zero extracted metrics — an empty finding
from a broken extractor otherwise looks exactly like a healthy dashboard.

## Steal the layout, write your own queries — a worked case

*(incident)* A Postgres-backed flow dashboard, where no upstream could ever run. grafana.com's pmacct-derived one split
*top source hosts* from *top destination hosts* where the local draft had only host-pairs, and carried a
traffic-share-by-exporter panel it lacked entirely. Both were adopted as questions; neither query survived. What did
**not** transfer was equally clear: panels needing data we do not collect (AS numbers, GeoIP) or a plugin we do not
have (Sankey). The traffic goes both ways — none of the public ones had a freshness panel, so the local framing was the
better half of the merge.

## Verdicts expire

**Re-check "no good upstream exists" verdicts on a clock.** That judgement expires silently. *(incident)* Two recorded
here went stale within about a year — upstream had moved directory, or a maintained alternative had appeared — and the
note explaining the decision outlived its truth.
