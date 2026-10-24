#!/usr/bin/env python3
"""SearXNG CLI against your own SearXNG instance, optionally with tuned preferences.

usage: sx.py "QUERY" [extra&url&params]

  sx.py '"connection reset" nginx upstream'
  sx.py '!gh nftables conntrack'              # bang pins one engine
  sx.py 'foo' 'categories=it'                 # general|it|science|news|social+media|videos|images|files|map|music
  sx.py 'foo' 'time_range=year&pageno=2'
  sx.py --no-prefs 'foo'                      # compare against server defaults

Set SEARXNG_URL to your instance's /search endpoint. A SearXNG instance must have
`search.formats: [html, json]` in its settings.yml for the JSON API to answer at all.

Preferences (engine/category weighting tuned in the SearXNG UI, then copied out of the
`preferences` cookie) are optional: drop the blob in `prefs.txt` beside this script, or
point SEARXNG_PREFS at it. They are sent as a POST field rather than a Cookie header,
which survives proxies that strip cookies and avoids an unwieldy GET param.
"""
import os, sys, json, urllib.parse, urllib.request

BASE = os.environ.get("SEARXNG_URL", "")
if not BASE or "example.com" in BASE:
    # No default endpoint on purpose: posting at a placeholder host fails in a way that
    # reads as "my instance is down / has no JSON API", which is the wrong diagnosis.
    raise SystemExit("set $SEARXNG_URL to your instance's /search endpoint "
                     "(and give it `search.formats: [html, json]` in settings.yml)")
PREF_FILES = [
    p for p in (
        os.environ.get("SEARXNG_PREFS"),
        os.path.join(os.path.dirname(os.path.abspath(__file__)), "prefs.txt"),
    ) if p
]


def load_prefs():
    for path in PREF_FILES:
        try:
            with open(path) as f:
                return "".join(f.read().split())
        except OSError:
            continue
    return None


def main():
    argv = sys.argv[1:]
    use_prefs = True
    if argv and argv[0] == "--no-prefs":
        use_prefs = False
        argv = argv[1:]
    if not argv:
        print(__doc__)
        return 1

    fields = {"q": argv[0], "format": "json"}
    if len(argv) > 1:
        for k, v in urllib.parse.parse_qsl(argv[1]):
            fields[k] = v
    prefs = load_prefs() if use_prefs else None
    if prefs:
        fields["preferences"] = prefs

    body = urllib.parse.urlencode(fields).encode()
    req = urllib.request.Request(BASE, data=body, headers={"Accept": "application/json"})
    with urllib.request.urlopen(req, timeout=60) as r:
        d = json.load(r)

    res = d.get("results", [])
    print("QUERY: %s   results=%d   prefs=%s" % (d.get("query"), len(res), bool(prefs)))
    for s in d.get("suggestions", [])[:6]:
        print("  suggest: %s" % s)
    for u in d.get("unresponsive_engines", []):
        print("  DEAD ENGINE: %s" % (u,))
    for a in d.get("answers", []):
        print("  ANSWER: %s" % (a,))
    for i, r in enumerate(res[:20], 1):
        print("\n[%d] %s" % (i, r.get("title", "")))
        print("    %s" % r.get("url", ""))
        c = (r.get("content") or "").replace("\n", " ").strip()
        if c:
            print("    %s" % c[:320])
        print("    engines=%s date=%s" % (r.get("engines"), r.get("publishedDate")))
    return 0


if __name__ == "__main__":
    sys.exit(main())
