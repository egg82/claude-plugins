#!/usr/bin/env python3
"""Detect search-craft (SKILL.md) violations in web-search query strings.

check(query) -> [{"rule": ..., "evidence": ...}, ...]

Design stance, stated once because it governs every threshold below:
these detectors are *precision-first*. Each rule's real question is epistemic
("is the searcher supplying a value they are trying to learn?") and a query
string only carries a proxy for it. Where the proxy is ambiguous the detector
stays silent, because a noisy eval metric is worse than a narrow one.

Standard library only. Nothing from the corpus is read at import time.
"""

import json
import os
import re
import sys

# --------------------------------------------------------------------------
# shared vocabulary
# --------------------------------------------------------------------------

# SearXNG-style bangs (!se !oa !hn !gh !arx !yt !wp ...).
# Matched generically: "!" + short lowercase token at a word start.
BANG_RE = re.compile(r"(?<![\w!])![a-z][a-z0-9]{0,7}\b")

# Engine operators. "-site:" is a legitimate operator exclusion, NOT the
# "-term" foot-gun in SKILL.md §107, so it is stripped before negation-checking.
OPERATOR_RE = re.compile(
    r"-?\b(?:site|filetype|inurl|intitle|intext|ext|allintitle|before|after|lang|url)\s*:\s*\S+",
    re.I,
)

STOPWORDS = {
    "a", "an", "the", "of", "for", "to", "in", "on", "at", "by", "with",
    "and", "or", "is", "are", "was", "were", "be", "been", "as", "from",
    "that", "this", "it", "its", "which", "does", "do", "did", "has", "have",
}

# Units that make "<number><unit>" read as a measurement rather than an id.
UNITS = (
    r"mm|cm|km|m|nm|um|µm|in|inch|inches|ft|feet|mil|thou|"
    r"hrs?|hours?|mins?|minutes?|secs?|seconds?|ms|days?|weeks?|months?|years?|"
    r"kg|g|mg|lbs?|lb|oz|ml|l|gal|"
    r"c|f|k|degrees?|deg|"
    r"v|mv|kv|a|ma|w|kw|mw|hz|khz|mhz|ghz|rpm|psi|bar|nm|"
    r"kb|mb|gb|tb|kib|mib|gib|bps|kbps|mbps|gbps|"
    r"px|pt|%"
)
NUM_UNIT_RE = re.compile(r"\b(\d+(?:[.,]\d+)?)\s?(" + UNITS + r")\b", re.I)

# Attribute nouns whose value a searcher is typically trying to LEARN.
# Deliberately short: these are the ones where pre-supplying a number is the
# §51 trap. Spec nouns you routinely *filter* on (width, pack size, price)
# are intentionally absent.
LEARN_ATTRS = {
    "bore", "thickness", "diameter", "clearance", "tolerance", "default",
    "defaults", "maximum", "minimum", "max", "min", "limit", "spacing",
    "pitch", "torque", "capacity", "threshold", "ceiling", "cap",
    "duration", "runtime", "length",
}

# Independent attribute nouns, for the compound rule. A query naming three of
# these is asking for three separate table cells (SKILL.md §110).
ATTR_NOUNS = {
    "size", "thickness", "length", "diameter", "width", "height", "weight",
    "depth", "capacity", "temperature", "voltage", "wattage", "pressure",
    "torque", "speed", "bore", "pitch", "clearance", "price", "cost",
    "duration", "runtime", "spacing", "resolution", "bandwidth", "latency",
    "throughput", "lifespan", "warranty", "width", "tolerance", "density",
}

NEGATION_WORDS = {"no", "not", "never", "without", "excluding", "except",
                  "isn't", "doesn't", "don't", "aren't", "cannot", "can't"}

UUID_RE = re.compile(
    r"\b[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}\b", re.I)
# Absolute paths anchored on real filesystem roots, so that a URL path
# ("site:github.com/<org>/<repo>") is not mistaken for one.
ABS_PATH_RE = re.compile(
    r"(?<![\w.])/(?:usr|home|var|opt|etc|tmp|mnt|srv|proc|sys|root|bin|sbin|lib|dev|Users|Volumes|Applications)/\S+")
WIN_PATH_RE = re.compile(r"\b[A-Za-z]:\\\\?[^\s\"]+")
LONG_DIGITS_RE = re.compile(r"(?<!\d)\d{4,}(?!\d)")
HOSTNAME_RE = re.compile(
    r"\b(?:[a-z0-9-]+\.){1,}[a-z0-9-]+\b(?![\w.])", re.I)

# Contexts in which a number is an identifier/filter, never a sought value.
ID_CONTEXT_RE = re.compile(
    r"\b(cve|isbn|issn|patent|patents|issue|issues|pr|bug|ticket|docket|"
    r"model|part|sku|serial|version|v|rev|revision|build|rfc|iso|ansi|din|"
    r"errno|err|code|port|number|no|nr|#)\b\.?\s*$", re.I)

QUOTED_SPAN_RE = re.compile(r"\"([^\"]*)\"")
# A quoted span that is *only* a number, optionally with one unit word.
BARE_NUMERIC_RE = re.compile(r"^\s*(\d+(?:[.,]\d{1,3})*(?:\.\d+)?)\s*(" + UNITS + r")?\s*$", re.I)
YEAR_RE = re.compile(r"(?<!\d)(20(?:2[4-7]))(?!\d)")


def _strip_ops(q):
    """Remove bangs and engine operators, leaving the human part of the query."""
    return OPERATOR_RE.sub(" ", BANG_RE.sub(" ", q))


def _looks_like_identifier(value):
    """Comma-grouped or 7+ digit bare integers read as patent/part/PID numbers.

    This is why '1,234,567' (a part number) does not flag while '65530'
    (SKILL.md §53's vm.max_map_count trap) does. Erring toward silence.
    """
    if "," in value:
        return True
    digits = re.sub(r"\D", "", value)
    return "." not in value and len(digits) >= 7


# --------------------------------------------------------------------------
# rules
# --------------------------------------------------------------------------

def _r_expected_answer(q):
    """SKILL.md §51 — a candidate value for the thing being looked up.

    Two shapes, both narrow on purpose:
      (a) a quoted span that is nothing but a number (+ optional unit),
          where either the number carries no unit at all (a bare literal like
          "65530" is never something you *decided on* and filtered by) or the
          query also names an attribute the searcher is trying to LEARN;
      (b) an unquoted number+unit sitting next to such an attribute noun
          (bore, thickness, default, max, duration...).

    That "either" is what separates §71's two halves: `"60mm" refractor lens`
    is a filter and stays silent, `telescope focal length "900mm"` names the very
    attribute it pre-supplies and fires.

    Explicitly NOT flagged: years, model/part/version/CVE/ISBN/issue numbers,
    product names containing digits ("Series 9 Router", "Model 1200", "Class 2 Cable"),
    pack counts, and spec numbers used as filters ("12 cm width") — §71 says
    a number is fine when it is a constraint. When in doubt this stays quiet.
    """
    out = []
    stripped = _strip_ops(q)
    tokens = re.findall(r"[A-Za-z']+", stripped.lower())
    attrs = LEARN_ATTRS & set(tokens)

    for m in QUOTED_SPAN_RE.finditer(q):
        span = m.group(1)
        bm = BARE_NUMERIC_RE.match(span)
        if not bm:
            continue
        value, unit = bm.group(1), bm.group(2)
        if YEAR_RE.search(value) and not unit:
            continue                      # a bare year is the baked-year rule
        if not unit and _looks_like_identifier(value):
            continue
        if unit and not attrs:
            continue                      # §71: a united number alone is a filter
        before = q[max(0, m.start() - 24):m.start()].rstrip()
        if ID_CONTEXT_RE.search(before):
            continue
        out.append({"rule": "expected-answer",
                    "evidence": '"%s"' % span})

    if attrs:
        for m in NUM_UNIT_RE.finditer(stripped):
            # skip if this number is inside a quoted span (already handled)
            if q.count('"', 0, q.find(m.group(0)) if m.group(0) in q else 0) % 2 == 1:
                continue
            frag = m.group(0)
            if any(d["evidence"].strip('"') == frag for d in out):
                continue
            out.append({"rule": "expected-answer",
                        "evidence": "%s next to '%s'" % (frag, sorted(attrs)[0])})
            break
    return out


def _r_compound(q):
    """SKILL.md §110 — two independent asks bundled into one query.

    Fires only on *independent attributes* (tent packed weight + floor width +
    pole length). A genuine "X vs Y" comparison is a legitimate single
    question and is never flagged on the strength of 'vs' alone.
    """
    stripped = _strip_ops(q)
    words = re.findall(r"[A-Za-z]+", stripped.lower())
    present = [w for w in words if w in ATTR_NOUNS]
    distinct = sorted(set(present))
    if len(distinct) >= 3:
        return [{"rule": "compound",
                 "evidence": "3+ independent attributes: " + ", ".join(distinct)}]
    if len(distinct) == 2:
        # two attributes explicitly conjoined ("... size and thickness ...")
        pat = re.compile(
            r"\b(%s)\b(?:\s+\w+){0,3}?\s+(?:and|or|plus|,)\s+(?:\w+\s+){0,3}?\b(%s)\b"
            % ("|".join(distinct), "|".join(distinct)), re.I)
        m = pat.search(stripped)
        if m and m.group(1).lower() != m.group(2).lower():
            return [{"rule": "compound", "evidence": m.group(0).strip()}]
    return []


def _r_negation_word(q):
    """SKILL.md §107 — negation as a plain word does not exclude anything,
    and '-term' removes exactly the pages that would have answered you.

    Operator exclusions ('-site:x.com') are legitimate and are stripped first.
    Only lowercase negations count, so titles ('Never Go Back', 'No Country
    for Old Men') do not fire.
    """
    out = []
    stripped = OPERATOR_RE.sub(" ", q)
    for w in re.findall(r"(?<![\w'-])([a-z']+)(?![\w'])", stripped):
        if w in NEGATION_WORDS:
            out.append({"rule": "negation-word", "evidence": w})
            break
    for m in re.finditer(r"(?<![\w:/-])-([A-Za-z][A-Za-z0-9']{2,})\b", stripped):
        out.append({"rule": "negation-word", "evidence": m.group(0)})
        break
    return out


def _r_whole_query_quoted(q):
    """SKILL.md §245 — a whole query in one pair of quotes asserts a verbatim
    phrase no page contains, and reliably returns zero.

    Only bangs are stripped, not operators: `site:reddit.com "Acme Total
    Trail Stove Stand"` is an entity quote scoped to a site, which §238 endorses.
    And §245's complaint is about a *long* quoted query, so a quoted phrase
    under four words (a plausible multi-word proper noun) stays silent.
    """
    body = BANG_RE.sub(" ", q).strip()
    if len(body) > 2 and body.startswith('"') and body.endswith('"') \
            and body.count('"') == 2 and len(body.strip('"').split()) >= 4:
        return [{"rule": "whole-query-quoted", "evidence": body}]
    return []


def _r_baked_year(q):
    """SKILL.md §306 — a bare year filters for pages containing that literal,
    discarding current pages that do not."""
    m = YEAR_RE.search(q)
    return [{"rule": "baked-year", "evidence": m.group(1)}] if m else []


def _r_machine_noise(q):
    """SKILL.md §87 — strip what your machine wrote (paths, PIDs, UUIDs,
    hostnames); keep what the software wrote (symbols, codes, literals).

    Paths and UUIDs count anywhere in the query. PID-shaped digit runs and
    hostnames count only inside a quoted span, where they are pinning an
    error literal to one machine's run.
    """
    out = []
    for rx, label in ((UUID_RE, "uuid"), (ABS_PATH_RE, "path"), (WIN_PATH_RE, "path")):
        m = rx.search(q)
        if m:
            out.append({"rule": "machine-noise",
                        "evidence": "%s: %s" % (label, m.group(0))})
            break
    for span in QUOTED_SPAN_RE.findall(q):
        if len(span.split()) < 2:
            continue                       # a lone quoted token is an entity
        m = LONG_DIGITS_RE.search(span)
        if m and not YEAR_RE.fullmatch(m.group(0)):
            out.append({"rule": "machine-noise",
                        "evidence": "pid-like %s in %r" % (m.group(0), span)})
            break
        h = HOSTNAME_RE.search(span)
        if h and "." in h.group(0) and not re.match(r"^\d", h.group(0)):
            out.append({"rule": "machine-noise",
                        "evidence": "hostname %s in %r" % (h.group(0), span)})
            break
    return out


def _r_over_long(q):
    """WEAK signal. SKILL.md §41 says judge waste, not length — technical
    queries legitimately run long. Reported as advisory only; do not use this
    rule alone as an eval metric."""
    body = _strip_ops(q)
    body = body.replace('"', " ")
    toks = [t for t in re.findall(r"[A-Za-z0-9.'%-]+", body)
            if t.lower() not in STOPWORDS and len(t) > 1]
    if len(toks) > 15:
        return [{"rule": "over-long",
                 "evidence": "%d meaningful tokens (WEAK signal)" % len(toks)}]
    return []


RULES = (_r_expected_answer, _r_compound, _r_negation_word,
         _r_whole_query_quoted, _r_baked_year, _r_machine_noise, _r_over_long)

RULE_IDS = ("expected-answer", "compound", "negation-word",
            "whole-query-quoted", "baked-year", "machine-noise", "over-long")


def check(query):
    """Return a list of {"rule", "evidence"} violations for one query string."""
    if not isinstance(query, str):
        raise TypeError("query must be a str")
    out = []
    for fn in RULES:
        out.extend(fn(query))
    return out


# --------------------------------------------------------------------------
# tests: every rule gets a must-flag AND a must-not-flag case
# --------------------------------------------------------------------------
# (rule_id, query, should_flag)
TESTS = [
    # expected-answer
    ("expected-answer", '"vm.max_map_count" "65530" default', True),
    ("expected-answer", 'aquarium filter tank capacity "75 L" "100 L"', True),
    ("expected-answer", 'tent pole maximum diameter 9mm spec', True),
    ("expected-answer", '"60mm" refractor telescope lens', False),          # constraint, §71
    ("expected-answer", 'CVE-2024-3094 xz backdoor advisory', False),
    ("expected-answer", 'Acme R7 headlamp firmware version "1.08.02" changelog', False),
    ("expected-answer", '"Acme StormShell" independent lab test', False),
    ("expected-answer", 'Acme Q4 tent 3 inch stake depth', False),
    ("expected-answer", '!yd "1,234,567" tent zipper "slider pull"', False),  # part no.

    # compound
    ("compound", 'Acme tent packed weight floor width pole length', True),
    ("compound", 'pole length and floor width', True),
    ("compound", 'carbon vs fiberglass pole flex damping panel study', False),
    ("compound", 'Acme vs Contoso tent durability owners', False),
    ("compound", 'Contoso binocular prism coating transmission spec sheet', False),

    # negation-word
    ("negation-word", 'Java -coffee language', True),
    ("negation-word", 'ffmpeg concat without re-encoding audio', True),
    ("negation-word", 'Acme umbrella "no vent" canopy', True),
    ("negation-word", '"acme widgets" tent -site:acmewidgets.example forum', False),
    ("negation-word", 'bookstore "The Never Ending Query" paperback edition', False),
    ("negation-word", 'Java coffee origin', False),

    # whole-query-quoted
    ("whole-query-quoted", '"how do I set the max map count on linux"', True),
    ("whole-query-quoted", '!yd "containerd failed to create shim task on rhel 9"', True),
    ("whole-query-quoted", '"Acme Studio" Contoso export settings', False),
    ("whole-query-quoted", '"Acme" "Contoso" tent comparison', False),
    ("whole-query-quoted", 'site:reddit.com "Acme Trail Stove Stand"', False),

    # baked-year
    ("baked-year", 'best self-hosted RSS reader 2026', True),
    ("baked-year", 'Acme Widget Pro release notes published 2026', True),
    ("baked-year", 'best self-hosted RSS reader comparison', False),
    ("baked-year", 'RFC 6749 OAuth 2.0 framework published 2012', False),

    # machine-noise
    ("machine-noise", '"FileNotFoundError: [Errno 2] No such file or directory: \'/opt/app/config.yaml\'"', True),
    ("machine-noise", 'flux reconcile "kustomization 3f2a1b7c-9d4e-4a11-b8c2-77e0f1a2b3c4 failed"', True),
    ("machine-noise", 'containerd "failed to create shim task" runc', False),
    ("machine-noise", 'site:github.com/<org>/<repo> "unsupported codec" issue', False),

    # over-long
    ("over-long", 'RFC 9111 heuristic freshness 10 percent rule cache lifetime Last-Modified age browsers apply 10 percent of age default definition', True),
    ("over-long", '!yd why does the kubernetes cluster autoscaler refuse to scale down a node that has a pod using local ephemeral storage attached without any poddisruptionbudget configured anywhere', True),
    ("over-long", 'Vendorco Kestrel telescope eyepiece 2 inch barrel', False),
    ("over-long", 'Contoso binocular prism coating', False),
]


def run_tests():
    failures = 0
    print("=" * 78)
    print("DETECTOR TESTS  (every rule must prove it fires AND stays silent)")
    print("=" * 78)
    for rule_id, query, should_flag in TESTS:
        fired = any(v["rule"] == rule_id for v in check(query))
        ok = fired == should_flag
        if not ok:
            failures += 1
        print("%-4s %-19s %-9s %s" % (
            "PASS" if ok else "FAIL",
            rule_id,
            "must-flag" if should_flag else "must-NOT",
            query if len(query) <= 76 else query[:73] + "...",
        ))
    print("-" * 78)
    print("%d/%d cases passed, %d failed" % (len(TESTS) - failures, len(TESTS), failures))
    return failures


# --------------------------------------------------------------------------
# corpus scoring
# --------------------------------------------------------------------------

def score_corpus(path):
    with open(path) as fh:
        rows = json.load(fh)
    queries = [r["q"] for r in rows if isinstance(r.get("q"), str)]
    counts = {r: 0 for r in RULE_IDS}
    examples = {r: [] for r in RULE_IDS}
    clean = 0
    for q in queries:
        hits = check(q)
        if not hits:
            clean += 1
        seen = set()
        for h in hits:
            if h["rule"] in seen:
                continue
            seen.add(h["rule"])
            counts[h["rule"]] += 1
            if len(examples[h["rule"]]) < 3:
                examples[h["rule"]].append((q, h["evidence"]))

    n = len(queries)
    print()
    print("=" * 78)
    print("CORPUS: %s  (%d queries)" % (os.path.basename(path), n))
    print("=" * 78)
    print("%-20s %7s %8s" % ("rule", "count", "rate"))
    print("-" * 78)
    for r in RULE_IDS:
        print("%-20s %7d %7.1f%%" % (r, counts[r], 100.0 * counts[r] / n))
    print("-" * 78)
    print("%-20s %7d %7.1f%%" % ("clean (no rule)", clean, 100.0 * clean / n))

    for r in RULE_IDS:
        print()
        print("--- %s: 3 examples ---" % r)
        if not examples[r]:
            print("    (no violations found in corpus)")
        for q, ev in examples[r]:
            print("    q: %s" % (q if len(q) <= 110 else q[:107] + "..."))
            print("    ^ %s" % ev)
    return counts, n


if __name__ == "__main__":
    failures = run_tests()
    here = os.path.dirname(os.path.abspath(__file__))
    corpus = sys.argv[1] if len(sys.argv) > 1 else os.path.join(here, "atomic.json")
    if os.path.exists(corpus):
        score_corpus(corpus)
    else:
        print("\n(corpus not found at %s — skipping scoring)" % corpus)
    sys.exit(1 if failures else 0)
