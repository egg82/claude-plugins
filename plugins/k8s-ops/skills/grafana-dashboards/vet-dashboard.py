#!/usr/bin/env python3
"""Vet Grafana dashboards mechanically, before adopting or after inheriting them.

Two modes:

  remote  — score candidates on grafana.com before importing one
              vet-dashboard.py remote 315 1860 13659

  local   — score dashboard JSON you already have, and (optionally) check every
            metric it references against a live Prometheus
              vet-dashboard.py local path/to/*.json
              vet-dashboard.py local --prom-cmd 'kubectl --context <ctx> get --raw
                  "/api/v1/namespaces/prometheus/services/kube-prometheus-stack-prometheus:http-web/proxy{path}"' \
                  kustomization/dashboards/base/*.json

The --prom-cmd template gets {path} substituted; anything that prints the Prometheus
HTTP API response to stdout works (curl against a port-forward is equally fine).

Reports, never edits. A dashboard with panels but zero extracted metrics is flagged
LOUDLY as a probe failure rather than reported as a clean result -- an empty finding
from a broken extractor looks exactly like a healthy dashboard.
"""
import argparse, collections, json, re, subprocess, sys, urllib.parse, urllib.request

# Panel types removed with AngularJS in Grafana 12. Core ones force-migrate to React;
# third-party ones were pulled from the catalogue and cannot be recovered.
ANGULAR = {"graph", "singlestat", "table-old", "grafana-piechart-panel",
           "grafana-singlestat-panel", "natel-discrete-panel", "heatmap-old",
           "grafana-worldmap-panel", "briangann-gauge-panel"}

# PromQL metric names. Deliberately permissive on the left, then filtered: it is far
# safer to over-collect and drop known non-metrics than to silently miss a family.
METRIC_RE = re.compile(r'\b([a-zA-Z_][a-zA-Z0-9_]*(?::[a-zA-Z0-9_:]+)*)\s*(?=[{(\[]|\s|$)')
NOT_METRICS = {
    # PromQL keywords, functions and aggregations -- not metric names.
    "sum", "avg", "min", "max", "count", "count_values", "stddev", "stdvar", "topk",
    "bottomk", "quantile", "group", "rate", "irate", "increase", "delta", "idelta",
    "deriv", "predict_linear", "holt_winters", "abs", "ceil", "floor", "round",
    "clamp", "clamp_max", "clamp_min", "exp", "ln", "log2", "log10", "sqrt", "sgn",
    "absent", "absent_over_time", "changes", "resets", "scalar", "vector", "time",
    "timestamp", "day_of_month", "day_of_week", "day_of_year", "days_in_month",
    "hour", "minute", "month", "year", "label_replace", "label_join", "sort",
    "sort_desc", "sort_by_label", "sort_by_label_desc", "histogram_quantile",
    "histogram_count", "histogram_sum", "histogram_fraction", "last_over_time",
    "avg_over_time", "min_over_time", "max_over_time", "sum_over_time",
    "count_over_time", "quantile_over_time", "stddev_over_time", "stdvar_over_time",
    "present_over_time", "mad_over_time", "by", "without", "on", "ignoring",
    "group_left", "group_right", "offset", "bool", "and", "or", "unless", "if",
    "info", "double_exponential_smoothing", "pi", "rad", "deg", "acos", "asin",
    "atan", "cos", "sin", "tan", "acosh", "asinh", "atanh", "cosh", "sinh", "tanh",
    "le", "inf", "nan",
}


def load_dashboard(obj):
    """Return the dashboard dict from either a raw export or an API envelope."""
    if isinstance(obj, str):
        obj = json.loads(obj)
    if isinstance(obj, dict) and "json" in obj and "panels" not in obj:
        inner = obj["json"]
        return json.loads(inner) if isinstance(inner, str) else (inner or {})
    return obj or {}


def walk_panels(d):
    """All panels, including those nested in rows (old schema) and collapsed rows."""
    out = []
    stack = list(d.get("panels") or [])
    for r in d.get("rows") or []:                 # schemaVersion < 16
        stack.extend(r.get("panels") or [])
    while stack:
        p = stack.pop()
        out.append(p)
        stack.extend(p.get("panels") or [])       # collapsed row children
    return out


# Datasource identifiers that are never "foreign": Grafana's built-in specials and the
# conventional provisioned UIDs. Matched case-insensitively, since old schemas reference a
# datasource by display NAME ("Prometheus") rather than by uid.
KNOWN_DS = {"prometheus", "grafana", "loki", "alertmanager", "tempo", "influxdb", "elasticsearch",
            "default", "-- grafana --", "-- mixed --", "-- dashboard --",
            "grafana-postgresql-datasource",
            # Grafana's server-side EXPRESSION datasource (legacy numeric id -100). Built in,
            # resolves in every Grafana with no provisioning, and present in perfectly portable
            # dashboards that reference nothing foreign. Measured against a real corpus: before the
            # case-insensitivity fix above, 0 foreign-uid flags; after it, 2 — and BOTH were
            # `__expr__`. A signature that could never fire became one that fired only on false
            # positives, which is worse than the bug it replaced.
            "__expr__", "-100"}


def datasource_uids(d):
    """Every datasource a dashboard references, by uid (new schema) or name (old).

    Scoped to `datasource` values on purpose. A blob-wide search for `"uid"` also matches the
    dashboard's OWN uid, library panels and annotation queries, so it reports the dashboard
    itself as a foreign datasource. And filtering that noise by `uid.isupper()` -- which is what
    this used to do -- only ever caught SHOUTING uids like Grafana Cloud's PBFA97CFB590B2093:
    modern auto-generated UIDs are lowercase or mixed case, so a dashboard bound to a foreign
    datasource vetted perfectly clean. That is the falsely-clean shape this script exists to
    prevent, produced by the script itself.
    """
    out = set()

    def walk(o):
        if isinstance(o, dict):
            for k, v in o.items():
                if k == "datasource":
                    if isinstance(v, dict) and isinstance(v.get("uid"), str):
                        out.add(v["uid"])
                    elif isinstance(v, str) and v.strip():
                        out.add(v)
                else:
                    walk(v)
        elif isinstance(o, list):
            for x in o:
                walk(x)

    walk(d)
    return out


def foreign_ds(d):
    """Referenced datasources that are neither built-in nor a template variable."""
    return sorted(u for u in datasource_uids(d)
                  if not u.startswith("$") and u.lower() not in KNOWN_DS)


def expressions(panels):
    for p in panels:
        for t in p.get("targets") or []:
            for key in ("expr", "query", "rawSql"):
                v = t.get(key)
                if isinstance(v, str) and v.strip():
                    yield v


def metrics_in(exprs):
    """Returns (resolvable_metrics, unresolvable).

    'Unresolvable' are names built by interpolating a dashboard variable into the
    metric itself (`${prefix}_audit_log_request_count`). They cannot be checked
    against Prometheus without expanding the variable, so they are reported
    separately -- counting them as ABSENT would blame the dashboard for a limit of
    this script.
    """
    found, unresolvable = set(), set()
    for e in exprs:
        # Strip string literals so label VALUES are not mistaken for metric names.
        e = re.sub(r'"[^"]*"|\'[^\']*\'', " ", e)
        # Mark variable interpolations BEFORE stripping brace blocks, otherwise
        # `${prefix}_foo` degrades into the fragment `_foo` and looks like a metric.
        e = re.sub(r'\$\{[^}]*\}|\$[A-Za-z_][A-Za-z0-9_]*', "\x00", e)
        # Strip label matcher blocks, whose keys are labels, not metrics.
        e = re.sub(r'\{[^}]*\}', " ", e)
        for m in re.findall(r'\x00([a-zA-Z0-9_]+)|([a-zA-Z_][a-zA-Z0-9_]*(?::[a-zA-Z0-9_:]+)*)'
                            r'\s*(?=[{(\[]|\s|$|\x00)', e):
            var_glued, plain = m
            if var_glued:
                unresolvable.add("${…}" + var_glued)
                continue
            if not plain:
                continue
            base = plain.split(":")[-1] if ":" in plain else plain
            # PromQL keywords are lowercase, but dashboards write `OR`/`BY` freely.
            if plain.lower() in NOT_METRICS or base.lower() in NOT_METRICS:
                continue
            if plain[0].isdigit():
                continue
            if plain.startswith("_"):
                unresolvable.add(plain)      # interpolation residue
                continue
            found.add(plain)
    return found, unresolvable


def _prom(prom_cmd, path):
    out = subprocess.run(prom_cmd.replace("{path}", path), shell=True,
                         capture_output=True, text=True, timeout=180)
    if out.returncode != 0:
        sys.exit(f"prom-cmd failed ({out.returncode}): {out.stderr.strip()[:300]}")
    try:
        return json.loads(out.stdout)["data"]
    except Exception as e:
        sys.exit(f"prom-cmd returned unparseable output: {e}\n{out.stdout[:300]}")


def prom_metric_names(prom_cmd):
    """Metric names that exist ANYWHERE in the retention window.

    Deliberately NOT the final answer -- see live_metrics(). A name is listed here
    for as long as retention holds any sample, so a family that stopped being
    emitted days ago still appears. Scoring a dashboard on this list alone passes
    panels that render empty forever.
    """
    data = _prom(prom_cmd, "/api/v1/label/__name__/values")
    # A probe that CAN'T return a real answer must not be read as 'nothing is missing'.
    if len(data) < 100:
        sys.exit(f"prom-cmd returned only {len(data)} metric names -- refusing to "
                 "score dashboards against a probe that looks broken.")
    print(f"# Prometheus knows {len(data):,} metric names in its retention window",
          file=sys.stderr)
    return set(data)


def live_metrics(prom_cmd, names):
    """Of `names`, which have series RIGHT NOW.

    One instant query rather than N: count by (__name__) over an anchored regex
    alternation. This is the check that catches a metric whose name survives in the
    label list but whose series stopped -- four panels on one dashboard here would
    have shipped permanently empty had the name list been trusted.
    """
    if not names:
        return set()
    live, batch = set(), 120
    ordered = sorted(names)
    for i in range(0, len(ordered), batch):
        chunk = ordered[i:i + batch]
        expr = 'count by (__name__) ({__name__=~"%s"})' % "|".join(
            re.escape(n) for n in chunk)
        data = _prom(prom_cmd, "/api/v1/query?query=" + urllib.parse.quote(expr))
        for s in data.get("result", []):
            live.add(s["metric"]["__name__"])
    print(f"# {len(live)}/{len(names)} referenced metrics have live series right now",
          file=sys.stderr)
    return live


def report_local(paths, known, live):
    hdr = f"{'dashboard':<34} {'panels':>6} {'schema':>6} {'metrics':>7} {'absent':>6}  flags"
    print(hdr); print("-" * len(hdr))
    for path in paths:
        try:
            d = load_dashboard(json.load(open(path)))
        except Exception as e:
            print(f"{path[:34]:<34} PARSE FAILED: {e}"); continue
        panels = [p for p in walk_panels(d) if p.get("type") != "row"]
        types = collections.Counter(p.get("type") for p in panels)
        ang = sorted(t for t in types if t in ANGULAR)
        mets, unres = metrics_in(expressions(panels))

        flags = []
        if not panels:
            flags.append("ZERO-PANELS(parse-failure signature)")
        if ang:
            flags.append(f"ANGULAR:{','.join(ang)}")
        if d.get("__inputs"):
            flags.append("__inputs")
        if d.get("__requires"):
            flags.append("__requires")
        blob = json.dumps(d)
        if "${DS_" in blob:
            flags.append("${DS_*}")
        for uid in foreign_ds(d):
            flags.append(f"foreign-uid:{uid}")
        if panels and not mets and not unres:
            flags.append("!! NO METRICS EXTRACTED -- probe suspect, verify by hand")
        if unres:
            flags.append(f"var-built:{len(unres)}(unverifiable)")

        absent = "n/a" if known is None else ""
        if known is not None and mets:
            # Two distinct failures, reported separately because the fixes differ:
            # a name Prometheus has never heard of is usually a wrong metric name or
            # a component you don't run; a name that exists but has no live series
            # means the emitter stopped, and the panel renders empty forever.
            gone = sorted(m for m in mets if m not in known)
            stale = sorted(m for m in mets if m in known and m not in live)
            absent = str(len(gone) + len(stale))
            if gone:
                flags.append("unknown=" + ",".join(gone[:4]) + ("…" if len(gone) > 4 else ""))
            if stale:
                flags.append("no-live-series=" + ",".join(stale[:4]) + ("…" if len(stale) > 4 else ""))

        name = (d.get("title") or path.split("/")[-1])[:33]
        print(f"{name:<34} {len(panels):>6} {str(d.get('schemaVersion')):>6} "
              f"{len(mets):>7} {absent:>6}  {' '.join(flags)}")
    if known is None:
        # An unrun check must not render like a passed one: an `n/a` absent column reads as
        # "nothing missing" when it means "nobody looked". STDOUT and AFTER the table on
        # purpose -- the usual invocation is `> report.txt`, and on stderr the caveat is
        # dropped from the saved artifact, which is the falsely-clean failure this prevents.
        print("absent=n/a: no --prom-cmd, so no metric was checked against Prometheus. "
              "UNCHECKED, not clean.")


def report_remote(ids):
    for did in ids:
        try:
            with urllib.request.urlopen(f"https://grafana.com/api/dashboards/{did}",
                                        timeout=25) as r:
                env = json.load(r)
        except Exception as e:
            print(f"{did:>7} FETCH FAILED: {e}"); continue
        d = load_dashboard(env)
        panels = [p for p in walk_panels(d) if p.get("type") != "row"]
        types = collections.Counter(p.get("type") for p in panels)
        ang = sorted(t for t in types if t in ANGULAR)
        gv = next((r.get("version") for r in (d.get("__requires") or [])
                   if r.get("type") == "grafana"), "?")
        print(f"{env['id']:>7} rev{env.get('revision','?'):<3} "
              f"dl={env.get('downloads',0):<10,} upd={str(env.get('updatedAt'))[:10]} "
              f"schema={d.get('schemaVersion')} needsGrafana={gv} "
              f"rating={env.get('reviewsAvgRating')}({env.get('reviewsCount')}) "
              f"panels={len(panels)} ANGULAR={','.join(ang) or '-'} "
              f":: {str(env.get('name'))[:40]} [{str(env.get('orgName'))[:18]}]")


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("mode", choices=["remote", "local"])
    ap.add_argument("targets", nargs="+", help="dashboard ids (remote) or json paths (local)")
    ap.add_argument("--prom-cmd", help="shell command template with {path}, for the absent-metric check")
    a = ap.parse_args()
    if a.mode == "remote":
        report_remote(a.targets)
    else:
        known = live = None
        if a.prom_cmd:
            known = prom_metric_names(a.prom_cmd)
            wanted = set()
            for t in a.targets:
                try:
                    dd = load_dashboard(json.load(open(t)))
                except Exception:
                    continue
                m, _ = metrics_in(expressions([p for p in walk_panels(dd)
                                               if p.get("type") != "row"]))
                wanted |= m
            live = live_metrics(a.prom_cmd, wanted & known)
        report_local(a.targets, known, live)
