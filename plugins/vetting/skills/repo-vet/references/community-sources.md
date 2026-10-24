# Where community sentiment actually lives, and how to reach it

Read this before the sentiment sweep. It records which sources work, which are blocked, and — most importantly — which ones return **convincing garbage** that reads like a real negative result.

Every path below was verified by actually running it, but access changes constantly — re-verify a path before trusting a null from it.

## The rule that matters most

**A null result is only evidence of absence if the probe could have shown the thing.**

Every source below can return "no results" for reasons that have nothing to do with your question: a frozen index, a blocked crawler, a hostname that doesn't exist, a fuzzy-matched query. Before writing "no reports exist," run a **control query** — something you know should match. If the control comes back empty too, your probe is broken and the null is meaningless.

The clearest example: a search for a project returned zero results from an index frozen two years before that project was created. That is not "nobody discusses it." Reporting it as a finding would have been wrong in a way nobody downstream could detect.

## This list is a floor, not a checklist

What follows is where *self-hosted infrastructure* discussion tends to live, verified by actually
trying it. It is deliberately non-comprehensive, and for anything outside that niche it's the wrong
list — a Python library lives on PyPI stats, Stack Overflow, and language forums; a vendor tool lives
in its own Discourse or Discord; a desktop app lives in distro bug trackers. **Work out where *this*
project's users congregate and go there too.**

The reliable way to find those venues is to follow the project rather than guess: its README and docs
usually link a chat, forum, or subreddit; release announcements show where the maintainer talks to
users; issue threads cite the places reporters came from; and a packaging ecosystem (AUR, nixpkgs,
Homebrew, TrueNAS/Unraid app catalogues, Proxmox helper scripts) carries maintainer notes and user
complaints that never reach GitHub. For anything established enough to have one, **Wikipedia** is
worth a look — it carries history, forks, licence changes, and controversies that a repo's own
README will never mention.

Also check any "awesome-*" list for the *specific* niche rather than only the general one.

### Before recording anything as blocked: send a browser User-Agent

This one line has now rescued two sources that were written off as hard-blocked. Reddit and selfh.st
both return 403 to a default client and **200 with real content** to:

```
-A 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0 Safari/537.36'
```

Try that before concluding a site refuses you.

### selfh.st (the self-hosted newsletter) — verified reachable

With the UA above, all 200:

| URL | What it is |
|---|---|
| `https://selfh.st/rss/` (= `/feed/`) | RSS, ~25 recent items — fastest way to see if a project got covered |
| `https://selfh.st/newsletter/` (= `/weekly/`) | Newsletter archive |
| `https://selfh.st/` | Main site |

Coverage in the weekly is a real signal — a curator chose to feature it.

**Caveat, found the hard way:** `https://selfh.st/apps/` returns 200 but is a **JS-rendered shell** —
the app catalogue is not in the HTML, so grepping it returns zero for *everything*. A control grep for
two apps certain to be catalogued came back 0, which is how the trap was caught. If you need that directory,
render it headless; don't grep it. (`.../static/build/apps/partners.json` is sponsors, not the
catalogue; the catalogue endpoint wasn't found from the page's JavaScript bundle.)

If you find a venue that works and isn't recorded here, add it — this file is meant to accumulate.

## Works well

### Lemmy — the most productive source by far

Open JSON API, no auth. This is where self-hosted tooling is actually discussed now.

```
https://lemmy.world/api/v3/search?q=<term>&type_=All&limit=50
https://lemmy.world/api/v3/post?id=<id>
https://lemmy.world/api/v3/comment/list?post_id=<id>
```

Federation means querying one instance reaches content from many others (lemmy.ml, programming.dev, sopuli.xyz, infosec.pub, lemmy.ca, mander.xyz, piefed.social — and Mastodon). Query `lemmy.world` first; if the topic has a niche instance that hosts its main community, query that one too.

Two gotchas:
- Passing `sort=Top` returns HTTP 400. Omit it.
- Search **fuzzy-matches** and coined product names are the worst case — a short invented name is a substring of, or a near-miss for, ordinary words in unrelated posts (and in other languages). Post-filter results for the exact token or you'll report noise as signal.

Announcement threads are especially valuable: comments on a maintainer's own launch post reveal both reception and how they handle criticism.

### GitHub REST + search API

Reliable via `gh`. Use it for commit distribution, issue authorship, release cadence, and issue content. Two things it's uniquely good at:

- `GET /repos/<owner>/<repo>/issues/<n>` returning **HTTP 410** proves an issue was *deleted*, not closed. That's a strong maintainer-conduct signal you can verify directly rather than repeating hearsay.
- Comparing the default branch's last commit against the repo's `pushed_at` — divergence means side-branch activity is inflating apparent liveness.

Note that GitHub computes some stats asynchronously; a contributor/commit-stats endpoint can return empty on first call and populate on retry. Don't read that empty as zero.

### Hacker News

```
https://hn.algolia.com/api/v1/search?query=<term>
```

Works, no auth. Near-zero signal for self-hosted homelab tooling — expect one hit across a dozen tools. Cheap enough to run; don't expect much.

### awesome-selfhosted

Grep the raw README rather than fetching the rendered site:

```
https://raw.githubusercontent.com/awesome-selfhosted/awesome-selfhosted/master/README.md
```

**Always run a control probe** — grep for a long-established tool in the same category, one you are certain is listed, and confirm a non-zero count plus a plausible line count. Without that, a failed download looks identical to "not listed."

**Network/infra monitoring tools (Zabbix, LibreNMS, NetXMS, Observium, NetBox, …) are not in this
list at all — it delegates the whole category.** The README's own "Monitoring & Status Pages"
section says outright: "Please visit awesome-sysadmin/Monitoring". A control probe for e.g. Zabbix
here will legitimately return zero even though the list is fine — that's not a broken fetch, it's
the wrong list. For this category fetch
`https://raw.githubusercontent.com/awesome-foss/awesome-sysadmin/master/README.md` instead (control:
`nagios` should hit).

Interpretation: presence means somebody curated it. Absence is weak evidence for anything under a year old — inclusion requires a human to open a PR, so young projects are missing by default, not by rejection.

### Reddit — `old.reddit.com` over curl with a browser UA (REGRESSED, re-probe before relying on it)

**Reddit content is still reachable — via the self-hosted SearXNG (next section). Read that first;
the rest of this section is why the direct paths fail.**

**Status at time of writing: this path now returns a login gate, not content.** Every URL shape below —
subreddit search, sitewide search, and a plain subreddit listing that involves no search at all —
comes back HTTP 200, ~352KB, `<title>Welcome to Reddit</title>`, zero `data-fullname` markers. The
uniform response size across three unrelated URLs is the tell: that is one interstitial being served
for everything, not three empty result sets.

Established independently twice on the same day: a subagent hit it mid-sweep and confirmed with a
popular-tool control, then a separate probe reproduced it with a different control and a listing page.
**Check the title, not the HTTP status** — the gate returns 200, so a status check alone reads as
success.

The consequence for a sweep: r/networking, r/homelab, r/selfhosted and r/sysadmin are unreachable by
every documented direct method, and `WebSearch` with `site:reddit.com` is blocked too (controlled
with a well-known head-to-head comparison query, which returned no reddit.com results despite being one of
the most-discussed comparisons online). Say so in coverage gaps rather than reporting a thin Reddit
read as a null. Lemmy (above) also picks up a lot of the same homelab/selfhosted traffic via
federation and is worth leaning on harder.

**Do not delete the recipe below.** This source has already been written off as hard-blocked once and
rescued by a single changed request detail (the `old.` host plus a browser UA), so its reachability is
known to swing. The method is worth one probe on any future sweep. Run the control first
(`old.reddit.com/r/homelab/`, expect a real listing, not "Welcome to Reddit"); if a subreddit listing
returns real `data-fullname` markers, the gate is gone and the notes below apply again as written.

**What it looked like when it worked**, verified at ~1,900 comments across 24 threads with zero blocks — real HTML, not challenge pages or SPA shells. Reddit blocks by user-agent and on the modern domain; `old.reddit.com` fetched with a normal browser UA was not blocked.

```bash
UA='Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0 Safari/537.36'

# Thread with full comment tree
curl -sL -A "$UA" 'https://old.reddit.com/r/<sub>/comments/<id>/?limit=500&sort=top'

# Search — sitewide or restricted to one subreddit
curl -sL -A "$UA" 'https://old.reddit.com/search?q=<term>'
curl -sL -A "$UA" 'https://old.reddit.com/r/<sub>/search?q=<term>&restrict_sr=on'

# A user's comment history
curl -sL -A "$UA" 'https://old.reddit.com/user/<name>/'
```

Search is the real unlock — it finds threads you didn't already know about, which is what turns this from "verify one link" into an actual sweep.

**Removed threads survive at their direct URL.** A post showing `[ Removed by moderator ]` still returns all its comments. Removal only **deindexes** it — so search returns nothing while a direct fetch returns 208KB of intact discussion. If you know the thread ID, fetch it; never conclude a removed thread is unrecoverable because search came up empty. This is the sharpest form of the null-result trap in this file: two probes against the same object disagree, and only one of them is right.

Still broken, don't bother: `www.reddit.com` and `api.reddit.com` (403), `.json` on any URL (403), `WebSearch` with `allowed_domains: reddit.com` (hard 400 — crawler blocked by UA), Redlib/LibReddit public instances (8 tried, all Anubis/Cloudflare/dead), reveddit (empty).

### SearXNG (self-hosted) — how to reach Reddit now, and a general fallback index

The instance at `https://<searxng-host>/search` accepts `format=json` and returns
`title` / `url` / `content` per result. It reaches Reddit content that every direct path above now
refuses, because it queries upstream engines rather than fetching reddit.com:

```bash
curl -s --max-time 30 \
  --data-urlencode "q=site:reddit.com <terms>" \
  --data-urlencode "format=json" \
  "https://<searxng-host>/search"
```

Verified: a `site:reddit.com <niche tool> <category>` query returned 20 subreddit threads with dates and snippets, including recent ones — so the index is live,
not a frozen mirror like PullPush. This is the instrument to reach for when `WebSearch` with
`site:reddit.com` returns nothing.

**Know what it does and does not buy you.** You get search-result snippets: titles, URLs, dates, and
a sentence or two. You do **not** get comment bodies or vote counts, and the thread URLs it returns
are still unfetchable. So this restores *discovery* — which tools operators name, how often, and
what the recurring complaints are — and not the close reading that the old `old.reddit.com` recipe
allowed. Label conclusions drawn from it as snippet-level, and do not write "an operator reports"
unless the operator's words are inside the snippet.

Being self-hosted, it is also not rate-limited against you and has no crawler-UA block to work
around — worth trying for any index that has started refusing you, not only Reddit. Query-building
and the rest of this instance's routing live in `search-craft`'s `references/tool-routing.md` (record your own in `~/.claude/local/search-craft/`).

## Blocked or broken

### PullPush — the dangerous one

```
https://api.pullpush.io/reddit/search/submission/?q=<term>
https://api.pullpush.io/reddit/search/comment/?q=<term>
```

Returns **HTTP 200 with well-formed JSON**, which makes it look authoritative. Its index is **frozen at 2025-05-19**.

Anything created after that date returns zero results *structurally*. It also happily returns stale unrelated matches — a query for one tool returned 2022 posts about a JavaScript variable with a similar name.

Verify the freeze yourself before relying on it: query a busy subreddit for its newest indexed posts and look at the dates. It remains useful for pre-May-2025 topics and useless for anything newer.

### Others

- **A project's "official forum" that does not exist.** A plausible-sounding forum hostname for a well-known project was invented, then repeated as a source — it had no DNS record at all. Resolve a hostname before reporting that its content was empty.
- **DuckDuckGo HTML** — blocked. **Marginalia** — 302. (Both worth one retry with a browser UA before
  believing it — that's what un-blocked Reddit and selfh.st.)
- **Wayback** — intermittent 503s; retry before concluding no captures exist.

## What community sentiment is actually good for

**It tells you about people, not about defects.** Use it for maintainer conduct, abandonment,
migration patterns, and adoption cost — things only users who lived with the tool can know. Do not
lean on it to find bugs; that's what reading and running the code is for. The crowd is confident and
frequently aimed at the wrong target:

- One project drew a malware accusation that spread widely and got a thread removed. The accusation
  traced to a single uncorroborated reporter, two other users independently monitored its traffic and
  found nothing — and the tool's real defect, discovered only by reading the code, was that its logger
  silently discarded every error it raised, which is why a crashing *dependency* went undiagnosed for
  a month.
- Another drew a much-upvoted "AI slop" verdict that turned out to be an evidence-free drive-by on an
  unrelated thread, factually wrong on a checkable detail, with zero replies. Meanwhile the finding
  that actually disqualified it — a live pre-auth SSRF on the only installable version, with the fix
  stranded on an unreleased branch — was mentioned by nobody, because it took reading the auth
  middleware to see. The sentiment pass would have cleared it; a claim that a project carries an unpatched
  vulnerability has to be settled in the source tree and the release history, never in the thread.

So: when sentiment and code inspection disagree about *quality*, trust the code. When they disagree
about *whether the maintainer will still be here in a year*, trust the community. And treat a loud
accusation as a lead to verify yourself, never as a finding to repeat — say who claimed it, whether
anyone corroborated it, and what your own check found.

## Reading what you find

- **Runners vs upvoters.** A launch thread with hundreds of upvotes can contain four or five people who actually ran the thing. Only that second number predicts anything. Count it separately and report it separately.
- **Volume, stated honestly.** In niches this small, two comments is not a consensus and one critic is not a verdict. Write "one person said X" when that's what happened.
- **Check whether accusations were investigated.** Claims get repeated far more than they get tested. In one case a malware accusation was independently checked by two users who monitored container traffic and found nothing — the accusation and its refutation carry very different weight, and only reporting the first would badly mislead.
- **Separate verified from secondhand.** "Users on Lemmy describing a Reddit thread nobody could read" is not the same as having read the thread. Label it.
