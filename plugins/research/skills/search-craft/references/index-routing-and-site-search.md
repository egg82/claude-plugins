# Routing to the right index, and site-native search (§7, §10)

Load when deciding where an answer lives before writing the query, or when using a site's own search box
(shopping catalogs, code and forum platforms). Per-engine operators and tool routes are in
`tool-routing.md` (your own notes go in `~/.claude/local/search-craft/`).

## 7. Route to the index before crafting the query

Switching index beats improving the query, repeatedly. Ask "where does this kind of answer *live*?"
before "what words do I type?"

| question | index |
|---|---|
| how do I call this poorly-documented API? | code search — check which engine you're on (`references/tool-routing.md`) |
| does real code use this flag, and how? | `git grep` on a local clone beats every hosted code search |
| is this a known bug? | the project's issue tracker, with its qualifiers |
| exact error string | a lexical index, not a reworded web search |
| CLI flag semantics | the man page |
| long-lived OSS design rationale | the mailing-list archive |
| what do practitioners think? | HN; Reddit via the route in `references/tool-routing.md` |
| official behaviour / defaults | the vendor's own docs or wiki — go there directly |
| a table of per-item values | find the table, fetch it, read it — don't ask search for one row |
| a conference talk or video critic (GDC, YouTube essays) | the talk's own captions: `yt-dlp --skip-download --write-auto-subs --sub-langs "en.*"` on the uploaded video, beside a `ytsearch5:"<title>"` lookup. A paywalled GDC Vault listing is often free on GDC's YouTube channel. After a burst YouTube answers 429; the page's "Show transcript" panel in a live browser still works |

**Retrieve-then-grep beats query-by-query.** When one thread or archive plainly *is* the topic, pull
the whole thing and search it locally.

**Some communities have no public index at all** (chat-first projects on closed platforms). That's a gap, not a
query problem — say so instead of grinding.

## 10. Site-native search is a different game

A site's own search box is usually a catalog matcher over titles and tags, not a semantic index.

**On shopping catalogs the pollution is inverted.** The problem isn't that your query is too wordy —
it's that the *documents* are, because sellers keyword-stuff titles. So adding terms matches more
junk, not less, and quoting is unreliable because your phrase appears inside stuffed titles of
irrelevant products.

**Read the facet rail before writing the query:**

- constraint is a **facet** → drop it from the query, filter instead
- constraint is **indexed text** → keep it in the query
- constraint is **neither** → the site can't answer; read listings by hand, or leave for a parametric
  supplier

Facet coverage varies wildly by category on the same site. Tested: an over-specified
query (`Acme umbrella "no vent" canopy`) had 2 of 10 correct — and *removing* the spec made it 0 of 10, because that category has no size
filter. "Shorten and filter" is only right when the filter exists.

**Check the field exists at all.** Searching a brand on a platform that stores no brand field cannot
work, however phrased. **Many catalog engines never return zero** — gibberish can return four figures
— so a non-empty result set is not evidence anything matched.

**Native search for facets; `site:` for text.** Native search owns the filters and pagination but
typically indexes title and tags only, so anything in a description is reachable only via a general
engine. Code and forum platforms are the opposite: real syntax, and precision pays.
