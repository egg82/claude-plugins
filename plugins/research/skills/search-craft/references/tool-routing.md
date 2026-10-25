# Search routing — tool-by-tool notes

Partly environment-specific: the SearXNG sections are optional, for people who run their own instance, and the
engine-health figures were measured on one. Everything from **Reddit** downwards is
platform behaviour and applies anywhere. The method lives in `SKILL.md`; this is which tool to reach for and how each
one fails here.

## Which tool

| use | for |
|---|---|
| **WebSearch** | general web, finding canonical docs. Better index than the local SearXNG for open-web questions — it found kernel.org docs SearXNG missed entirely |
| **SearXNG bangs** | indexes WebSearch doesn't cover: Hacker News, man pages, package registries, Docker Hub, arXiv, PubMed, Semantic Scholar, Lemmy, lobste.rs, NVD |
| **SearXNG + yandex** | anything needing **honoured quotes or `site:`** |
| **`curl`** | Reddit, Discourse forums, Stack Exchange API, any site with a JSON endpoint |
| **`gh` / `glab`** | GitHub and GitLab — real APIs beat searching for them |
| **`repo1.maven.org/maven2/<group/path>/<artifact>/maven-metadata.xml`** | Maven artifact existence and latest version. **Not** `search.maven.org/solrsearch`: its index is stale (it has reported a published artifact NOT FOUND, and year-old versions for others) |
| **Chrome** | last resort: anti-bot walls and anything needing a login |

**WebSearch's synthesized prose blends sources of different vintages and states the blend
confidently.** Trust its links; verify its summary. It also filters `allowed_domains` /
`blocked_domains`, which is more reliable than a `site:` operator.

## SearXNG (optional, if you run SearXNG)

Assumes a SearXNG instance with the rate-limiter off and `json` format enabled; point
`SEARXNG_URL` at yours. Bang names are configurable, so check yours.

Helper: `sx.py` in the skill directory (one level up from this file).

    python3 sx.py 'QUERY'
    python3 sx.py '!hn rust'                      # bang pins one engine
    python3 sx.py 'foo' 'categories=it'
    python3 sx.py 'foo' 'time_range=year&pageno=2'
    python3 sx.py --no-prefs 'foo'                # compare against server defaults

It prints `unresponsive_engines`, query suggestions, and the per-result `engines` field. **Use
them — they are the difference between "nothing exists" and "my engines are dead."** WebSearch
exposes no equivalent, so a zero there is uninterpretable.

### Bangs — each one below was confirmed by checking which engine actually ran

**An unknown bang is not an error.** SearXNG passes it through as literal query text and runs the
default engines, so a wrong bang returns plausible results from the wrong place. `!so`, `!au`,
`!scholar`, `!lobsters`, `!go` and `!re` all look like they work and none of them exist.
**Confirm via the per-result `engines` field, never by "it returned results."**

| bang | engine | good for |
|---|---|---|
| `!yd` | yandex | **the operator workhorse** — quotes, `site:`, `-word`, `OR` |
| `!hn` | Hacker News | practitioner opinion; supports `time_range` |
| `!lo` | lobste.rs | technical discussion |
| `!st` `!ubuntu` `!su` | Stack Overflow, AskUbuntu, SuperUser | error messages; `[tag]` works |
| `!gh` `!gl` | GitHub, GitLab | **repos, not issues**; `user:` `org:` `repo:` `in:name` work |
| `!man` | mankier | man pages — **single command name only**, two words → 0 |
| `!mdn` `!msl` | MDN, Microsoft Learn | web platform / Azure docs |
| `!npm` `!crates` `!dh` | npm, crates.io, Docker Hub | package + image metadata |
| `!arx` `!se` `!oa` | arXiv, Semantic Scholar, OpenAlex | papers — `!se` gives PDF links |
| `!nvd` | NVD | **exact CVE ID only**; keyword queries return 0 |
| `!wp` | Wikipedia | answer lands in `infoboxes`, **not** `results` |
| `!bi` | bing | general fallback — **operators do not work at all** |

Dead here: `!gos` (Google Scholar), `!pypi` and `!al` (arch wiki) return 0 silently; `!qw` is
CAPTCHA-bound. There is no Google engine (only `!goc`, currently blocked), no Reddit, no Stack
Exchange beyond the three above.

**Bangs stack:** `!st !gh ebpf` runs both and returns results from each.

### Categories beat bangs for breadth

Non-tab categories run **all** member engines including default-disabled ones — the highest-leverage
single call on a typical instance:

    categories=packages   → 11 registries at once (npm, crates, pkg.go.dev, hex, pub.dev, …)
    categories=repos      → github + gitlab + sourcehut
    categories=q&a        → Stack Overflow plus the Discourse forums

Tab categories (`general`, `it`, `science`, `news`, `images`, `videos`, `files`, `social media`,
`map`, `music`) run only the default-enabled engines.

### Bangs bypass preferences entirely

`!hn`, `!mdn`, `!man`, `!npm`, `!crates`, `!dh`, `!bi` return full results whether or not the engine
is enabled in the prefs blob — verified identical with and without. Preferences only govern the
engine blend for an **un-banged** category search. **So never edit preferences just to reach an
engine.** Use a bang.

### Tuned preferences

A curated engine selection travels as a zlib+urlsafe-base64 blob. `/tmp` is ephemeral — keep a
durable copy under `~/.claude/local/search-craft/`.

**Send it as a `preferences=` POST field.** The `Cookie: preferences=…` header is **stripped by some reverse proxies and tunnels** and silently ignored — you get plausible results from the wrong engine set with
no error. `sx.py` handles this.

### Engine behaviour — they are not interchangeable

- **yandex honours quoted phrases and `site:`.** It is the precision engine here.
- **bing ignores quoted phrases.** `"fs-verity"` returned *Farming Simulator*; `"zone transfer"`
  returned *Zone Casino*. Adding bing to the general blend measurably **degraded** precise technical
  queries — blended metasearch re-ranks across engines, so one low-precision engine spends the
  top-five slots. Tried and reverted.
- `site:` returns **zero** through bing.
- General engines here are CAPTCHA/rate-limit fragile — DuckDuckGo, Startpage, Google CSE, Mojeek and
  Brave all suspend under load. Yandex is the most reliable.
- **`filetype:`/`ext:` do NOT work on yandex — use its native `mime:pdf`.**
- **`-site:domain` on yandex is actively wrong** — it returns hits *from* the excluded domain.
- `intitle:` biases rather than constrains; `inurl:` works but collapses results to a handful.

### Silent-failure traps — everything here returns plausible output while being wrong

- **An unavailable engine in `engines=` does not error** — SearXNG runs the whole category instead.
  `engines=wikipedia&categories=general` returned ten results, none from Wikipedia.
- **An invalid bang behaves the same way** — passed through as literal query text. `!re` returns
  junk that reads as "the tool is bad" rather than "my invocation was invalid." Bitten twice.
- **`unresponsive_engines: []` does not mean success.** Several engines return `n=0` with no error.
  Check `len(results)` too.
- **`time_range` on an engine that doesn't support it silently zeroes the result set.**
- **A typo in `engines=` silently falls back to the whole default set.**

**Always check the per-result `engines` field before believing where a result came from.**

Live health, rather than guessing: `curl -s "$SEARXNG_URL/stats/errors" | python3 -m json.tool`

### Fragility is concentrated in the general-web engines

Measured under load, then again an hour later:

| class | behaviour |
|---|---|
| **General web** (google cse, startpage, brave, qwant, mojeek, ddg) | scrape consumer search sites that fight bots. Suspend under concurrent load, **stay down for tens of minutes**, and escalate if you retry immediately. Four of six were still dead an hour after the burst; DuckDuckGo recovered on its own. |
| **Specialized** (hackernews, github, stackoverflow, mankier, npm, crates.io, docker hub, mdn, lobste.rs, askubuntu, pubmed, arxiv, semantic scholar) | real APIs. **10/10 healthy** during the same window in which the general pool was down. |

So the split is **by engine class, not by budget**:

- **General web → WebSearch.** Better index, reliable, and it's what the session budget is for.
- **Named/specialized index → SearXNG bangs.** Not rate-limit fragile, and WebSearch can't reach
  them anyway.

Don't fan out concurrent agents onto the *general* category — they share one egress IP, and you'll suspend
every upstream at once. Bang-scoped agent work is fine.

**Retry is not the fix.** Recovery happens on a tens-of-minutes timescale, so it can't rescue a live
search, and immediate retry lengthens the suspension. The move is to **notice**: `unresponsive_engines`
tells you the pool degraded, so report "4 of 6 engines were down" instead of passing off a thin
result set as a finding. That detection is the one thing WebSearch genuinely cannot do.

## Reddit — plain curl, no browser

    curl -sL -A '<browser UA>' 'https://old.reddit.com/search?q=<terms>&sort=new&t=year'
    curl -sL -A '<browser UA>' 'https://old.reddit.com/r/<sub>/comments/<id>/'

Verified: search → 200, thread → 200 with the full comment tree. Strip tags and read it.
Search params: `q`, `sort=new|top|relevance`, `t=day|week|month|year|all`, `restrict_sr=on`.

**Reddit's own search is better than its reputation** — current to within hours, correctly scoped.
Its weakness is ranking title-matching *question* threads above answer quality, so sort by Top
rather than trusting rank order. It has no comment search and caps around 250 results.

### Rate limiting — the 429 is a quota, not a block, and it tells you the wait

A burst of a dozen fetches exhausts it. The 429 carries `x-ratelimit-used: 100`,
`x-ratelimit-remaining: 0.0` and **`x-ratelimit-reset: <seconds>`** — read that header and sleep it
off. Blind exponential backoff wastes the whole session: six retries at 8/16/24/32/40s never got
through because the real window was 113s, and the wait **escalates** if you keep hammering (saw it
go 93s → 468s in one session). The 429 body is empty and `curl -w '%{http_code}'` alone won't show
you the reset, so fetch with `-D` and parse the headers.

    curl -sL -D /dev/stderr -A '<browser UA>' "$url"   # then regex x-ratelimit-reset out of stderr

**Cache every 200 to disk keyed by URL.** Re-running a script after a throttle otherwise re-spends
quota on pages you already have.

| route | result |
|---|---|
| **`curl` on `old.reddit.com` HTML** | **200 — full content, search and threads** |
| `curl` on the same path + `.json` | **403** — the API is blocked, the HTML is not |
| `www.reddit.com` | SPA shell, no content without JS |
| `WebSearch(allowed_domains=["reddit.com"])` | hard error — blocked at the tool layer |
| `WebFetch` on reddit.com / old.reddit.com | refused at the tool layer |
| `safereddit.com`, redlib mirrors | HTTP **200** — Anubis proof-of-work challenge, not content |
| SearXNG snippets | URLs only; `content` is the "site owner hides the description" placeholder |

**Three distinct blocks, don't conflate them:** the *tool layer* refuses reddit.com (`WebSearch`,
`WebFetch`); *Reddit* blocks its `.json` API from this IP; and neither says anything about what
other search engines index. The HTML is open to an ordinary UA.

> I originally concluded "curl gets 403, so Reddit needs Chrome" after testing **only** the `.json`
> endpoint — one variant, generalized to a whole site, adding a browser dependency that was never
> required. Probe the thing you are actually claiming about.

Fallbacks, if Reddit's own search comes up short:

- **Google `site:reddit.com`** — current, correctly dated, and the only engine indexing
  **comment-level** anchors.
- **Historical / deleted / date-ranged:** the Arctic Shift API
  (`arctic-shift.photon-reddit.com/api/posts/search?subreddit=&after=&before=&author=`) was current
  to within hours. **PullPush is a trap** — HTTP 200, well-formed JSON, over a corpus frozen a year
  back, so it returns clean empty sets indistinguishable from "no match."
- **Bing-family engines have NOT lost Reddit — they serve a frozen pre-lockdown corpus.** Newest
  Reddit content surfaced: Bing **2023-04**, Qwant **2024-04**. DuckDuckGo inherits Bing's index, so
  assume the same. **This is worse than an empty result set:** the results look perfectly normal and
  are silently two to three years old, with no visible age. Do not use them for anything where
  currency matters.
- **Mojeek's Reddit index is frozen too** while its general index is current — a zero from it means
  nothing.

Ignore the widely-repeated claim that Reddit's `robots.txt` allows Google and blocks everyone else.
It is `Disallow: /` for **every** agent, Google included — access is contractual and invisible in
robots.txt.

## Chrome

Real browser with the user's session. Needed only for anti-bot walls and logins — **not** for
Reddit.

**Construct the query as a URL and `navigate` to it — never type into a search box.** Typing is
slow, non-reproducible, and steals focus from the user, so their keystrokes can land in the field
mid-query and silently corrupt it. A corrupted query returns plausible results, so the damage is
invisible. Every major search UI accepts its query as URL params.

**`navigate` without an explicit `tabId` grabs the first tab in the MCP group**, which may belong to
another session or another agent. Call `tabs_context_mcp` first or `tabs_create_mcp` your own, and
close what you open.

**Chrome is shared with the user.** Don't fan out browser-driving agents while they're working, and
treat any finding an agent gathered by typing into a box as suspect.

## Shopping and parametric catalogs

- **Amazon** — does not hard-AND; it silently relaxes an over-specified query and re-ranks by sales
  velocity, so failure arrives as confident junk rather than zero. **Check the facet rail first** —
  it varies wildly by category, and where the constraint has no facet (many categories offer only
  Brand/Price/Reviews), *keep the spec in the query* and plan to read listings. Removing it measurably
  made things worse: 2-of-10 correct became 0-of-10. Working surface: `k=` query, `i=<dept>` (narrows
  hard), `rh=` facets, `s=price-asc-rank`; quotes are a **true ordered phrase** (`"cast iron"` ≫
  `"iron cast"`); `-term` excludes. If the binding constraint is a hard spec, leave for a
  parametric supplier.
- **Digi-Key / Mouser / McMaster** — search is a token-AND over text: use it for **part numbers and
  nouns only, never constraints.** A spec sentence returns zero; an exact MPN jumps straight to the
  product page. Filters are the interface. Mouser's API cannot filter parametrically at all. Grainger
  bans crawlers in `robots.txt` — out of bounds.

## Code search

**GitHub runs TWO engines and they do not share syntax.**

- *Modern* (`path:` globs, `symbol:`, `/regex/`, `AND`/`OR`/`NOT`, parens) is **web-UI only and needs
  a login**. Unauthenticated requests return 0.
- *Legacy* is what `gh search code` and `GET /search/code` hit. Working set: `filename:`,
  `extension:`, `language:`, `path:` (substring, **not** globs), `repo:`/`org:`/`user:`, quoted
  phrases, AND by default. `symbol:` and `/regex/` match as **literal text**; parens + `NOT` return
  HTTP 422. Login required, ~10 req/min, ≤100 results, default branch only.
- **Silent coverage holes on the legacy index.** `repo:<big/repo>` can return **0 for every term**
  while `org:<same-org>` returns hundreds. A zero from `gh search code` is not evidence the code
  doesn't exist — confirm with `org:`, or clone and `git grep`.
- **For a repo you can clone, `git grep` beats both.**

grep.app is alive but bot-challenged (429). searchcode.com is alive; its old API is gone.
Sourcegraph is enterprise-only — no free tier.

## Forums

- **Discourse** (many OSS and hardware-vendor communities) — the best native search around, and
  reachable unauthenticated as JSON:

      curl -s 'https://<forum>/search.json?q=<terms>+category:<cat>+order:latest'

  AND-joined, stemmed, last term prefix-matched. `in:title|first|pinned|wiki`, `category:`,
  `#cat:sub`, **`tags:a+b` = AND vs `tags:a,b` = OR**, `-tags:`, `user:`/`@`, `before:`/`after:`,
  `status:open|closed|noreplies`, `min_posts:`, `min_views:`, `filetypes:`,
  `order:latest|views|likes`. Quotes enforce word order. **Page-caps at 50 — never read that as a
  total.**
- **Stack Exchange** — use the API; the web UI bot-challenges. `/search/excerpts` is the best
  endpoint. Traps: web-UI operators inside `q=` are treated as literal text, unknown params are
  silently ignored, and `min`/`max` bind to the **sort field**, not to score.
**Bad operators fail in OPPOSITE directions across forum platforms — both invisibly.** Discourse
treats an unknown `foo:bar` as a literal search term and returns **0 results**, which reads as
"never discussed." Reddit **silently ignores** it and returns the unfiltered baseline, which reads
as "the filter applied." Verify the operator, not the plausibility of the output.

- **Lemmy** — strict AND, and **never quote** (a quoted phrase can return 0 where unquoted returns
  20). Instances disagree on coverage and the largest is not the best — union two or three.

## Adoption rate of this skill, and how to re-measure it

Instance data, kept here rather than in `SKILL.md` so the number can move without editing the method.

At authoring time 9 of 25 research subagents never opened the skill despite seeing it listed. A
later sweep of one machine's transcripts found 12 of 15 searching sessions loading it. The rule in `SKILL.md` — name the skill in the brief — is what changed, and
it stands regardless of the current figure.

Re-measure by counting transcripts that issued a search against those that also invoked the skill:

```bash
cd ~/.claude/projects
with=$(grep -rl '"skill":"search-craft"' . | sort -u | wc -l)
any=$(grep -rlE '"name":"WebSearch"' . | sort -u | wc -l)
echo "loaded in $with of $any searching transcripts"
```

## `WebFetch` on a PDF: the file is already on disk

`WebFetch` hands the raw bytes to the summarizer, which sees a compressed object stream and reports
the document "corrupted or improperly encoded" — but the tool has **already saved the PDF** and
prints the path (`…/tool-results/webfetch-*.pdf`). That message is a *parse* failure, not a retrieval
failure: do not re-fetch, do not go looking for an HTML version.

```bash
pdftotext -layout "$SAVED_PATH" - | grep -n -i -E 'term|term2'
```

`pdftotext` is on PATH here. Extension-service and agency publications are overwhelmingly PDFs, so
this is the normal path to their text, and it beats the summarizer anyway — you get the bytes to
quote instead of a précis of them (`SKILL.md` §12).

## `allowed_domains` can silently fall back

Restricting to a single narrow host that has no matching pages returned an **unrestricted** result
set (all `ncbi.nlm.nih.gov`) rather than zero — so a domain filter is not proof the results came from
that domain. Multi-domain lists honoured the filter in the same session. Check the hostnames of what
came back before reading a filtered search as evidence about that site.

## Known gap in `sx.py`

`!wp` (Wikipedia) returns its answer in the **`infoboxes`** field, but the shipped helper prints only
`results` — so `!wp <term>` shows `results=0` and looks like a miss when the answer is present in the
payload. Read the raw JSON for that bang, or extend the helper, rather than concluding the engine
failed.
