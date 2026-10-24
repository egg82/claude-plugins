# Gotchas that cost time

- **`prefers-color-scheme` prefs do not apply under `--screenshot`.** Setting the Firefox pref does
  nothing. To check a dark palette, copy the page and swap `@media (prefers-color-scheme: dark)`
  for `@media all`, then shoot the copy. Checking only the light theme is how a dark-mode
  regression ships.
- **`:hover`, `:focus` and `:target` never fire under `--screenshot` — rewrite the selector instead.**
  Same trick as the dark-mode one above, generalised: copy the page, replace `tr:hover` with
  `tr.hovered` in the CSS, add that class to one element, and shoot the copy. The state then exists
  without a pointer. This found a real bug that no assertion could see — a `background` on `tr:hover`
  painting over a `border-collapse: collapse` shared border, so hovering a row deleted the line between
  it and its neighbour, intermittently, because the shared edge belongs to only one of the two rows.
  **Pick a MIDDLE element**, so there is a neighbour on each side; a first or last one hides half the
  defect. And build a minimal standalone page with the real stylesheet when the crop keeps missing the
  element — full control of the geometry beats hunting for a y-offset in a long page.
- **A client-side-routed SPA needs the server to fall back to `index.html`, and to NOT fall back for
  the API.** Two rules, and the second is the one that bites. `python3 -m http.server` 404s
  `/projects/7/settings` because no such file exists, so you cannot photograph any route but `/` — override
  `translate_path` to return `index.html` for anything that is not a real file, which is what nginx's
  `try_files $uri /index.html` does in production. But apply that fallback to `/api/*` as well and
  every data request returns **a web page with status 200**, which the app parses as JSON: it then
  renders its error or empty state, and you photograph what looks exactly like a page whose data is
  broken. Serve `/api/*` (and `/ws/`, `/healthz`) as a real 404 with a JSON body instead, so each
  page takes its own honest error path. The tell is in the server log — `"GET /api/me" 200` when
  there is no backend within a thousand miles. Worth knowing that this is a real production bug
  class and not a quirk of the harness: a catch-all fallback in front of `/metrics` returns the app
  shell with a 200 and `Content-Type: text/html`, so a monitoring scraper gets a web page and no
  error.
  **When only the chrome is under test — a nav, a header, a tab state — none of this matters**, since
  those render before any fetch resolves. Decide which you are shooting before building the server.
- **A page that fetches its data needs `file://` abandoned AND `load` delayed, or you photograph the
  pre-fetch page.** Two separate obstacles, and each one alone produces the same picture — the
  server-rendered state, which reads as "the interaction did nothing" and is very often the exact defect
  being investigated. First, `fetch` on a `file://` page is blocked, so serve over HTTP: run
  `python3 -m http.server` **inside** the container and point Firefox at `127.0.0.1`, which works fine
  under `--network=none` because loopback is in the container's own netns. Second, `--screenshot` fires
  at `load`, which arrives before an async `.then` has run. Delay `load` with a slow subresource — a
  handler that sleeps, requested as **`<img src="/slow.png">`**.
  **Not a `<script src>`:** that blocks *parsing*, and a page's own `defer`red script therefore runs
  *after* the delay rather than during it, leaving its fetch in flight exactly as before. An image does
  not block parsing but `load` still waits for it, which puts the delay on the correct side.
  **Serve it from a THREADED server, or the sleep starves the fetch you are waiting for.**
  `python3 -m http.server` and a bare `socketserver.TCPServer` are single-threaded, so a handler that
  sleeps 6s blocks the data request behind it — and you photograph the pre-fetch page for a third
  distinct reason, with the same picture as the two above. Use `ThreadingHTTPServer`. The tell is the
  in-page log: the data request resolving *after* your own t+2500ms snapshot on a localhost request
  that should be instant. I wrote this handler knowing what it was for and still made it serial; the
  instrument manufactured the symptom it was built to detect.
  **And the delay only works if the fetch is already in flight when `load` fires.** A page whose
  script requests its data *on* the `load` event puts the request on the far side of the delay: the
  slow image holds `load` back, `load` then fires, the screenshot is taken, and the fetch is issued
  after it. The tell is in the server log — the data request timestamped at the same instant the
  slow resource completed, rather than before it. Read that log; the picture alone is identical to
  the fetch-blocked case above and to a page that ignored its data. There is no `--screenshot`
  delay to add on that side, so either move the page's own hook earlier in a copy (which
  manufactures its own risk) or drop the browser and assert on the values under node — and say
  which one you did.

  **Do not "fix" this by overriding `fetch` with a synchronous XHR.** It resolves the data before the
  page's own init has read the URL, so the state machine runs in an order it never runs in — in the case
  that taught me this, the app's `applyFilters()` fired with an empty filter and its closing
  `writeUrl()` rewrote the address bar *without the query*, after which the page correctly rendered an
  unfiltered view. Hours attributed to the page belonged to the instrument. A hand-rolled thenable also
  will not flatten a returned promise the way a real one does, so `.then(r => r.json())` hands the next
  handler the wrapper and every field reads `undefined`.
- **Chromium's `--timeout=<ms>` is a CAP, not a delay — the slow-subresource trick above still
  applies.** It stops loading after that long; a page that reaches `load` sooner is photographed at
  `load`, pre-fetch. Measured, and I first wrote the opposite here: two renders showed data
  and I credited the flag, when the proxy serving them injected a 3.5s image — dropping the image gave
  "Loading…" on the same flag. So keep the slow image and set `--timeout` above its delay.
  **`--virtual-time-budget` is no substitute:** it waits for the page to go idle, and a page with a live
  countdown or poll never does — the run hung until killed, twice.
  **A click harness whose timer outlives the capture never fires, and looks like a blocked
  script.** I attributed one such no-op to CSP and wrote that here; the page had no CSP — the 5s
  `setTimeout` simply ran after the `load`-time screenshot. Keep a harness's delay inside the slow
  image's. (A `script-src` CSP does drop inline scripts, so a harness file is still the safer form.)
- **Timing a page load is a different instrument from shooting one.** Firefox's `--screenshot` mode holds fetch results back: on a dashboard page every boot request's `responseEnd` was ~650 ms and its `fetch` promise resolved at ~5,500 ms, in the old and new code alike, so it read as a constant cost of the app. Resource timings were right; anything downstream of a promise was wrong. For timings drive a real navigation (Playwright), and prove each probe can read non-zero first: a `PerformanceObserver('longtask')` reported nothing for a deliberate 300 ms block, while a 10 ms `setInterval` heartbeat recording gaps over 50 ms read 308.
- **`content-visibility: auto` blanks a `full_page` screenshot.** Chromium skips the panels while it captures, so every panel renders empty, including the one at the top. Stepping the viewport down the page with a shot at each stop shows them painting. Shoot the viewport.
  When the question is *what the page sent* rather than *what it shows*, drive Chromium over DevTools (`--remote-debugging-port=9222 --remote-allow-origins=*`, then
  `Network.requestWillBeSent` via `websocket-client`) — the payload is the evidence, not a screenshot.
  **Analytics backends drop `HeadlessChrome` as a bot**, so an end-to-end analytics check records
  nothing until you pass a normal `--user-agent` — a zero that describes the probe, not the tracker.
- **Make the probe report itself, in the page.** A screenshot cannot read a console, and an instrument
  that silently failed to install is pixel-identical to a page that ignored its data — I could not tell
  those apart for two screenshots. Append a `<pre>` at `load` with what the probe did.
- **To photograph a state that needs a click, inject a script that clicks the real control — but an
  inline `<script>` runs BEFORE a `defer`red one, so it fires before the page has wired any
  handlers.** This is the way to reach a tab, an accordion or a disclosure that `--screenshot`
  cannot: call `.click()` on the actual button, so the page's own code does the work and no markup
  is rewritten — strictly better than hand-swapping `hidden` attributes, which manufactures its own
  defects. The trap is ordering. **`defer` is ignored on an inline script**, so a probe appended
  after `<script src="app.js" defer>` executes at parse time while `app.js` waits for parsing to
  finish: every `.click()` lands on an element with no listener and silently does nothing. Wrap the
  probe in `document.addEventListener('DOMContentLoaded', …)` — after deferred scripts, before `load`.
  **What earns this a rule is how it renders: as a defect in the page.** A tab that will not switch
  reads as broken switcher markup, and I had a shot of the *default* panel sitting under a tab row
  where a different tab had been clicked — indistinguishable from a real bug. Only the self-reporting
  `<pre>` separated them, by saying `tab: clicked` and `panel hidden=true` in the same breath, which
  is not a state the page can reach on its own and so accuses the instrument. **So log the control you
  clicked AND the state you expected it to change** — `clicked` on its own would have confirmed the
  wrong conclusion. Beware also reading that state synchronously right after the click: a change the
  page applies asynchronously still reads stale, and the probe then disagrees with the screenshot.
- **When the clicked thing does not respond, install a SECOND handler beside the app's and click
  once.** "The app ignored the event" and "the synthetic event never reached the app" produce the
  same picture — an unchanged page — and the previous bullet's logging cannot separate them, because
  it reports what the *probe* did, never whether anything received it. A duplicate listener on the
  same element, wired the way the app wires its own, splits the two in one run: if the control fires
  and the app does not, the app is at fault and the instrument is exonerated; if neither fires, the
  page was never tested at all and the shot is worthless. Cheap because it is the app's own wiring
  copied, so it needs no new understanding of the page. Measured on a 3D star chart where clicking two
  of three label layers silently did nothing: the control fired and correctly identified the entity under
  the cursor, which localised the bug to the app's dispatcher in a single render instead of another
  pass of theorising about hit targets. Generalises past canvases — any framework that synthesises
  its own click from pointer events (map libraries, charting libraries, custom widgets) has this
  ambiguity, and the duplicate listener resolves it.
- **A scene becomes pickable LATER than it becomes visible, and "later" grows as you add
  layers — so a fixed frame or time gate that was late enough stops being late enough.**
  A textured marker (a billboard, a sprite) is not hit-testable until its texture reaches the
  renderer's atlas, which is a separate async step from the entity existing and from the
  frame being drawn. Measured on the same star chart: one layer picked 6/6 when surveyed at ~12s;
  after two more layers were added the same survey reported **0/5 with the pick returning
  `nothing`** — and a re-survey at +38s in the same run reported **4/4**. Nothing was broken.
  **Two renders were spent hunting a regression that did not exist, and a third nearly
  "fixed" it by degrading a feature.**
  The tell is `nothing` rather than *some other object*: if a decorative layer were stealing
  the hit you would get that layer's id back, so a bare `nothing` at a spot where something
  is drawn means not-yet-pickable rather than occluded. **Gate on the scene proving itself
  — re-survey and require two consecutive agreeing results, or wait until a layer you know
  works is pickable — never on a frame count, which measures the instrument's patience
  rather than the scene's readiness.**
- **And when the app draws into a canvas, hit-testing needs its own control for OCCLUSION.** A
  projection helper will happily convert a world position on the far side of a sphere (or behind any
  other geometry) into an on-screen pixel, where the thing is correctly unhittable. Without a
  visibility test, "18 of 30 did not respond to a click" reads as a defect when most of those 18 are
  simply behind the world — so report the rate over the candidates that *could* have been hit, not
  over everything you projected. Getting this wrong sends you fixing hit-target sizes that were never
  the problem.
- **Hit-testing is not a `--screenshot` question.** `elementFromPoint` at `load` under `--screenshot` returned different elements for byte-identical SVG pages: one copy hit the shapes, a copy in another directory hit only the container. Use Playwright (in a container with browsers installed) on a settled page, make real `mouse.click`s at the points, record `e.target` with a capture listener, and run old vs new.
- **When you hoist a section to fit one viewport, exempt `[hidden]`.** `--screenshot` ignores a fragment
  scroll, so the way to photograph something 5000px down is a copy of the page with
  `.wrap > * { display: none !important }` and `#target ~ * { display: revert !important }`. But
  `display: revert !important` **beats the UA's `[hidden] { display: none }`**, so that second rule
  forces every correctly-hidden element visible. Mine invented two defects in one shot — a stale empty
  state above a full table, and an empty bordered box — both of which I started diagnosing. Write
  `#target ~ *:not([hidden])`. The general form: **before believing what a rewritten copy shows you,
  shoot the unrewritten page too.** One control run separates the page from the instrument.
- **When photographing a LIVE app, restart the server before believing the shot.** A dev server
  started before your edit is still serving the old code, and **a stale process and a change that
  did not work produce an identical screenshot** — there is nothing in the picture to tell them
  apart. Cost an entire diagnosis pass on a result-ordering fix: the rows came back sorted exactly
  as the *previous* code specified, which reads as "my ORDER BY is wrong" rather than "the dev server has
  been up for an hour with no auto-reload". The tell, if you have one, is that the output matches
  the old behaviour *precisely* rather than being merely wrong — a broken change usually produces
  something new, while a stale process reproduces the past perfectly. Cheaper than looking for that
  tell: bounce the process, or assert the build identifier the page serves.
- **`glxtest: Unable to open a connection to the X server` on stderr is harmless.** It is not the
  reason your screenshot is missing; look for a real error.
- **Runs can exceed two minutes.** Give the Bash call a long timeout or background it, or the
  harness kills a run that was about to succeed and it reads as a failure of the technique.
- **`--network=none` is deliberate.** The page must be self-contained anyway; if it renders blank
  without network, that is a finding about the page, not a reason to open egress.
