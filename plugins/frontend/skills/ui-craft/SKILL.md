---
name: ui-craft
description: "How to make a web UI look and feel genuinely good — data-dense, colourful, alive — without trading away honesty. Use when building or redesigning a dashboard, stats page, leaderboard or any data-heavy front end; when a page \"looks dead\", \"bare\" or \"not as good as <site>\"; matching a reference site's look; a figure has no label or unit; or before a site-wide visual pass. NOT rendering mechanics (headless-render)."
---

# UI craft

The method for taking a working data UI from "fine" to "I want to use this". Learned on a project that
went from a white, table-shaped page to a dense, colourful analytics-site look in one evening, and paid for every step.

**Read `~/.claude/local/ui-craft/preferences.md` if you keep one** — the person's own taste (target look,
theme, density), kept separate so this method stays portable; none ships, record your own. Without it, ask what the
reference sites are before choosing a look.

**An existing house style outranks those preferences.** Where the repo already has sibling pages, or belongs to someone else, copy its tokens and layout vocabulary and apply this method *inside* it; the honesty rules (§4) apply everywhere, the target look only where nothing is established yet.

## 1. Brief against real screenshots, never a description

A description of a reference is a lossy summary, and an agent optimises the summary. Briefed from a
remembered description, one pass built "stat tiles"; the real pages had the headline numbers **top
right of the header**, a **two-column body with a narrow right rail**, and **bars inside cells** — none
of which the description carried.

- **Capture with a real browser** when one is reachable. Popular sites block headless browsers (a CDN
  403, a bot challenge), and the block page is a plausible small PNG: **look at every capture** before
  using it. Never try to get past a bot check; use the real browser, or ask the person for screenshots.
- Capture the whole page top to bottom, and a site from the product's own domain as a **baseline**:
  it shows what "sterile" looks like, and often that is what you have now.
- Hand the images to whoever builds the page as the acceptance target ("match this structure"), with
  your summary demoted to a hint about where to look.
- **When a restyle keeps landing on "a few graphs on top of a table", the structure is the problem and whoever built it cannot see past it.** Brief two or three clean-room designers with only the real payloads, the API schema, the product's purpose and the honesty rules (no code, no screenshots of the current site), each on a different lens (the work someone does, the entities they argue about, one picture of everything). Render every mockup yourself, then take each one's best layer: on one dashboard the job board, the entity pages and the cross-check came from three different designs, and no single one was right on its own.

## 2. Diagnose the gap by measuring, not by eye

Run computed-style measurements on the reference and on your page before deciding what to change —
leaf-text font-size histogram, the distinct colours used for numbers, image count, text-element count,
content width. **The gap is usually not where taste says.** Measured once: type size was identical
(11–13px on both), so "denser text" would have fixed nothing. The real gaps were 0 images vs dozens,
1 colour for numbers vs 4 meaning-carrying ones, and half the information per screen.

## 3. What makes a data UI feel alive

- **Each page's content picks its own layout.** One house shape for every page, with charts added
  to it, still reads as a table, and as a generated one. A ranking gets a hero chart and a
  top-three strip, an entity a profile card, a version history a timeline, an event log a
  filterable feed. A chart earns its place because the data supports it, never because a page looked empty.
  The chart's form, colours and marks are `dataviz`; button, label and error wording is `writing-craft`'s
  `references/ui-text.md`.
- **A picture on every entity.** People, teams, items — use the imagery you have. Where an entity has
  none, **generate an avatar**: deterministic from its id, inline SVG (zero requests), a shape and
  monogram in its own colour.
- **Colour that means something**, on two channels that never mix: *status* (ok/warn/bad — a state)
  and *value* (good/neutral/bad — a judgement of a number), plus a percentile ramp. Every value colour
  needs **a reference the data supplies** — a sign, 50%, a rating's start, the percentile among what is
  on screen — **never an invented threshold**. Too few values to rank: render neutral. A number with a **natural scale** (a score out of 100, a disk %, a pass ratio) takes its colour from where it sits on that scale, not its rank: ranking a tight cluster (75-81 of 100) paints 76 red beside a blue 76.5, a gap the scale says is nothing. Value runs
  blue/red, not green/red, which stays readable under common colour-vision deficiencies and keeps
  it off status green. An identity colour gets a second cue (a shape per tier), so colour is never
  the only signal.
- **A badge in a panel's header qualifies the whole panel; a badge on a row sets that row apart.**
  A caveat repeated identically down every row moves to the header, and moves back the moment
  only some rows carry it. A banner holding nothing but a badge is never the answer.
- **A meter in the cell**, under the number, so a column reads at a glance.
- **Density**: ~12–13px rows, a wide main column plus a narrow rail for side panels, stacking on a phone.
- **Dark first** where colour should pop; keep light working.
- **Interactivity**: a hover card on every entity reference, tabs for a page's sections, row hovers,
  a row that expands in place rather than a modal. Three things it tends to break: hover-only
  content needs a focus and tap path or it doesn't exist on a phone; a tooltip is a rendering
  surface, so an unknown inside it is still a dash; and an animation may follow a reorder but never
  cross-fades one number into a different one. Open popups in the top layer (`popover`): a row
  dimmed with `opacity` makes a stacking context, and an open hint inside it painted under every
  later row.
- **Interaction is consistent, or it feels broken.** No control reloads the page (a reload loses the
  reader's place); every control updates in place. All view state — date range, tab, filters, selections
  — lives in the URL, so reload, back and a shared link land in the same spot. Every selection has a
  visible clear: a chart range that can only be cleared by reloading was reported as a bug, and was.
- **One row of tabs per page.** Secondary choices (date range, units, weighting) are compact controls on
  one line, not a second or third tab row. A crowded header makes every new feature feel like clutter.
  The nav never wraps: it collapses to a menu first, so re-render desktop width whenever a link joins it.
- **Style native controls; never rebuild them.** Selects, number inputs, sliders and disclosures all
  get house styling, but a JS-rebuilt dropdown loses keyboard, screen-reader and phone-picker
  behaviour. Style the closed control everywhere, and the open menu where
  `appearance: base-select` is supported. Declare `color-scheme` per theme, or the browser's own
  menus, spinners and scrollbars stay light on a dark page.
- **Don't hand-roll what a maintained library does** (syntax highlighting, markdown). Vendor it, pin
  the version, check the file byte-for-byte against the registry's published integrity, and load it
  only where it's used.
- Copy the reference's *roles and structure*, not its brand palette or font, and skip its commercial
  chrome (mega-navs, ads, app banners, splash art that fights contrast). Borrow its conventions, not
  its jargon: a stranger following a shared link reads "Unrated", not the team's grading codes.

## 4. Honesty rules that survive any restyle

Looks are never bought with these. **An honesty state reads as an apology until it is a convention
the reader already knows**, so render it as one: a short record is "Unrated · 2 of 3 reviews", a
missed week a hatched pip (never a gap or a zero), a verified version a badge, a feature a thing
cannot do a disabled slot with its reason. They stop being special cases and become furniture.

- **No mystery numbers.** Every figure has a label, a unit, or an on-demand hint. A number with no unit
  once shipped as a variance read as points ("86 pts" that was 86 pts²).
- **Redesign, don't explain.** If a thing needs a paragraph, the layout is wrong. No new explanatory text.
  The usual source is the spec: a writer copies a design doc's behaviour sentences ("each result says why it matched", "the button is absent where...") into labels, palette entries and empty states, and the owner reads the result as over-explained copy. Labels are 1-3 words, state badges one word, errors one line of what happened and what to do. A doc sentence is never UI copy.
- **Unknown renders as unknown** (a dash with its reason), never 0, never a guess.
- **A count of periods names which periods** when the reader holds a calendar: "1 mo" in month 4
  read as the project being a month old; "sprint 3" answered it.
- **Gate tiny samples.** A rate over 2 orders is not a fact; below a stated minimum, show unknown and
  the count. A number carries its sample size at meta weight ("96% · n=3"). A real but early number
  (provisional) is shown lighter with its progress ("4.2?"), not withheld: withholding it left a
  whole board looking dead.
- **An arbitrary order never reads as a rank.** Name up to two tied leaders and count the rest; no
  top-three strip for a three-way tie.
- **A non-linear scale shows its ticks.** A power scale that un-crushes a tight cluster otherwise
  quietly exaggerates small gaps.
- **Raw errors never reach the page.** An API's error detail can be an array, and `new Error(array)`
  rendered "[object Object],[object Object]".
- **Never blend numbers of different trust** (self-reported vs measured, forecast vs actual): side by
  side, tagged, never averaged into one figure.
- **Evidence strength is drawn, never captioned.** A ranking built on one week of data and one built on
  seven years must LOOK different: interval width, overlap, placement. A badge, hint or caveat
  beside a misleading chart is not a fix. The reader who has to hover, or join two tables, to learn
  that fifth is really first has been misled. The test is what a visitor *does* after the first
  chart: there, they would have picked the wrong vendor.
- **Several rankings need one headline.** When a site ranks the same entities several ways (this
  month, all time, per region, weighted), the first view answers "who's best" from the best-supported
  evidence, and every other ranking reads as a lens on it, never as a rival verdict. A 1st, 3rd, 4.6
  and #1 for the same entity on four screens is a defect even when each is right on its own terms.
  Names that sound alike ("Overall" vs "All regions") must not name different things.
- **Empty states state their true reason.** "Needs more data" when the real cause is a filter nobody
  can pass is a lie in the artifact.
- **Default to the newest thing that has data**, not an empty "current" — a page opening on nothing
  reads as dead even when the data is one click away. Offer only choices the current state can
  fill: a month listed because an old record had data opened an empty room.
- **A benchmark that doesn't compete is marked wherever things are ordered.** Put it inside the
  existing tables as an unranked, labelled row, not on a board of its own. Then check every sorted
  view: charts, "best in tier" cards, top-N lists. The one you miss shows it as #1.
- **An old record never reads as current.** A superseded version's page opens with a banner that
  says so and links to the live one, and it leaves off anything won across versions (ranks, medals).
- **A display heuristic keys on a real property, never on one producer's output shape.** A fold
  labelled "inherited from…" split files on class position, which fit one uploader's bundles and
  mislabelled everyone else's code.
- **User-supplied content renders sanitized:** raw HTML off, a sanitizer over the output, links
  limited to http, https, mailto and in-page anchors.
- **A page makes no third-party fetch on the visitor's behalf.** Images render only from your own
  origin, through one gate, even if an unmirrored URL slips into the data. A token-bearing link keeps
  the token in the fragment, and analytics drops query and fragment: a tracker that reads `location`
  would otherwise have received a password-reset token.

## 5. Design for ten times the entities

Anything drawn once per entity breaks at scale: an N×N matrix at 100 is 10,000 cells, one lane or
line per entity becomes a wall. The pattern — how big stats sites handle hundreds of products:
**top N by default, search and pin for the rest, and a visible count of what is hidden** (never silent
truncation). An N×N view gets a *one-vs-the-field* default and a small matrix only for pinned or top
entries. Build a 10x fixture and look at it.

## 6. Verify like a user

The rendering mechanics are `headless-render`; hunting a page's defects (states nobody opened, keyboard, screen
reader) is `bug-hunt`'s `references/oracles/ui-and-accessibility.md`. This section is what a restyle must check.

- Render with **real data** (a read-only GET proxy to production works when local data is thin) and
  with a **scale fixture**; label fixture screenshots as such, since their numbers are made up.
  When the change is in the API as well, proxy to the BRANCH's server instead: run it read-only beside production (a throwaway instance from an existing deployment's template, the changed modules mounted over the installed package) and point the proxy at that. It is the only way to check that new endpoints agree with the numbers the page already shows, on the data that matters.
- Every screenshot at desktop width **beside its reference**, plus phone and the second theme. Look
  at each one; the bugs are found by looking (overlapping labels, stretched charts, a dead panel).
- **And one SHORT window (~800px tall).** A tall capture hides anything capped by viewport height. A sticky rail with `max-height: calc(100vh - ...)` and `overflow: auto` holds panels that are flex children with `overflow: hidden`, so they shrink to fit and clip their own contents instead of the rail scrolling. Every 1,500px-tall screenshot looked fine, and a user's laptop showed the sources list cut in half. The fix is `flex: none` on the rail's panels.
- **Render with the longest real names**, not whatever the fixture happened to use. A supplier called
  "Harrow & Fenwick Precision Fastenings Ltd" ran straight out of its summary card after a redesign
  every screenshot of which used short names. No text may escape its container: wrap or clamp,
  with the full string on hover and tap. At phone width, a name column squeezed by number columns
  clipped every name to one letter: let names wrap and narrow the numbers. A header for a column
  hidden on phones hides with it.
- **Render through the real server, headers included.** A page rendered from a static file looked
  finished, while the same page as served was completely unstyled: the route's content-security
  policy blocked its inline styles.
- **Open every screenshot yourself, including ones a delegate called "clean".** That unstyled page
  was reported as "clean, readable, dark-friendly", and its own screenshot showed otherwise.
- Visual claims from an automated browser need `document.visibilityState === "visible"`.
- **Walk the flows as a new user, unhappy paths included**: sign up, the emailed link, wrong
  password, expired token, and 404/422/500/offline on each page. Ten minutes of real use found three
  defects no test had: a verification email with no link in it, a signed-out page asking for an API
  key, and verification that didn't sign you in.
- **Enumerate the unknown states and screenshot each** (abstained, unmeasured, dormant, withheld,
  not built yet). A restyle loses them silently, because no one photographs a state they forgot.
- **Watch the network, not just the pixels.** A panel whose request sends a parameter the API never
  accepted fails silently and simply reads as empty, which looks like missing data; it shipped twice.
  A test that checks every client call site against the real routes catches the class.
- Count what the redesign costs: images and API requests per page, lazy-load below the fold,
  explicit width and height to stop layout shift. **Requests never scale with rows**: a list is one
  bulk call, never one per entity.

## 7. Sequence

A visual pass before performance work (images add requests, so tune the final shape), and a security
pass after performance (so a speed-up cannot quietly undo a protection). Features before all three.
