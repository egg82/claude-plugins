# Traps, each hit once already

- **Headless `requestFullscreen()` shrinks the page to an 800x600 "screen".** The frames came out 800x600 and were
  stretched to 16:9, so the shots looked blurry and over-zoomed while nothing errored. A full-screen view should
  be filmed through the site's CSS fallback: stub `Element.prototype.requestFullscreen` to reject in an init script,
  and assert the canvas width equals `innerWidth`.
- **A card's `ms` runs alongside its `voice`, not after it.** A card is as long as the longer of the two, so a
  line timed to fade in at 3.4s on a 4s voice was still half-transparent when the clip ended. Set `ms` past
  the voice plus the last line's fade.
- **`page.clock.install()` fakes `performance.now`, and the fake lags real time under a busy page** (0.74× measured
  while filming a busy canvas scene). Anything a scene drives from it, such as a scripted camera or an in-page clock,
  drifts behind the narration, which is paced on the real clock. A three-line exchange ran out past the end of
  its shot. Drive in-page motion from `document.timeline.currentTime`, which is not faked, and check it once:
  log the in-page elapsed time against `d.now()`.
- **A local server's health check can pass against someone else's server.** Another session took a staging port.
  The promo's own container failed to bind, `curl /healthz` answered "up" from the other one, and the scene
  filmed the wrong app until its fact check fired. Check that the container you started is running, not just
  that something answers on the port.
- **A `frame: false` scene has no window edge for captions to straddle.** `camera.py` now sits them above the
  bottom safe area instead of half off the frame.

- **Position the drawn cursor with the CSS `translate` property, never `transform`.** The
  click-squash uses `scale`, which is applied on top of `transform`, so it shrinks the
  cursor's position toward the page origin and the cursor jumps up-left on every click.
  Fixed in `director.mjs`; the control run showed a 161px jump.
- **An off-screen target takes the click somewhere else, silently.** The mouse acts at
  viewport coordinates. Fixed: the Director scrolls a target into view before acting.
  Before that fix, a scene "added two items" and filmed an empty panel.
- **A live site is slowest right after a deploy.** Two setups that normally take seconds
  timed out at 30s just after the site shipped. `setup()` is off camera, so give its waits
  60s; a timeout there costs a retry, not a frame.
- **A client-side route change is a `pushState`, not a load.** `waitForURL` waits for a
  `load` that never comes; wait on a DOM condition that proves the new state has rendered
  (for example, a link whose href extends the current URL).
- **Know the mechanics of the interaction you film.** On a task board with a work-in-progress
  limit, the scene dragged a card into a column already at its limit, so the card bounced back
  and "add one more" showed nothing. Choose the spot where the follow-up is visible.
- **A state where all the data agrees is not a demo.** A survey where every respondent chose the
  same answer renders one full bar and nothing to compare. Stage a split one.
- **A "loading…" state on camera is missed polish, and the owner sees every one.** Three
  layers now handle it:
  - `d.prewarm(sel)` in setup loads a hover card off camera, so on camera it opens already
    filled (sites cache them).
  - `d.startAt(x, y)` in setup places the cursor so its first move doesn't cross cards.
  - Every hover, click and park still waits out any loading, fast-forwarded.

  Capture then **measures** it: every scene reports its on-camera "loading…" seconds and
  warns if they're not zero. Sampled frames missed this twice; the number didn't.
- **A string predicate fails under a strict CSP, and `.catch(() => {})` hid that for a
  whole evening.** `waitForFunction("…")` needs `unsafe-eval`, which this site forbids, so
  the loading wait threw every time and the swallow made it a no-op. Pass real functions,
  and never swallow a wait's error: a timeout may warn, anything else throws.
- **Resting the cursor on a card or row opens hover popups.** `park()` after clicking tiles.
- **Zooming into a full-width row crops its label off.** Wide targets want zoom ≤1.15 or a
  `spot` without much zoom.
- **Captions over the window cover the data.** They straddle the window's bottom edge.
- **Web fonts load late in a fresh page**, so cards and captions silently fall back. Cards
  now throw if the font isn't loaded.
- **CDP screencast is good enough.** It only emits frames on paint, but it runs at about
  60fps while anything moves, and the engine gives each frame its real duration. A virtual
  display with ffmpeg capture is not needed. Playwright's `recordVideo` is (fixed VP8 at 1 Mbit/s).
- **playwright-recast** (the nearest off-the-shelf tool, trace to polished video) worked,
  but in the comparison it captured before images loaded, left a loading popover in
  frame and rendered at 30fps. Its idle speed-up idea is worth borrowing. Its README
  describes APIs the published npm version lacks, so trust the installed `.d.ts` over it.
