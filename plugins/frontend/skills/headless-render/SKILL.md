---
name: headless-render
description: "Render an HTML page to a screenshot and actually look at it, on a host with no browser installed. Use whenever work produces HTML a human will see — dashboard, report, generated page, published artifact, UI under evaluation — before calling it done; also to check hover/focus/dark mode, pages filled by fetch, SPA routes, a page behind a login, or whether a feature is findable on a cold first visit. NOT for driving a page or asserting on clicks (claude-in-chrome)."
---

# Headless render

**Write `~/.claude/local/headless-render/instance.md` and read it first** — it says which mechanism THIS host
needs, and it is the one thing here that cannot be handed to you: a machine with no browser on
`PATH` uses the podman + Firefox recipe below, while a machine with a real browser should drive that
instead, since it can interact and this cannot. Record which of the two yours is, once. (No
`instance.md` ships with this skill. Until you write
one, work from the recipes below and expect to re-decide that question every time.)

Then **Read the PNG**. Rendering it and not looking at it is the same as not rendering it.

The belief worth naming, because it is what stops this happening at all: **absence from `PATH`
bounds what is installed, not what is reachable.**

## Why this is not optional

Logic assertions do not catch what a glance catches, and the gap is not marginal:

- A dashboard shipped on DOM-shim assertions alone displayed **an unresolved account ID as an ordinary
  username**. The shim could not have caught it; the render made it obvious immediately.
- A column of `—` where every value should have been a date passed `node --check`, a DOM-shim pass
  **and** a markup validator, and was obvious on screen.

Both are the same shape: the cheap checks verify that code *ran*, not that the output *reads*
correctly. So the ladder is worth climbing in order, but the top rung is the one that finds the
embarrassing defect.

## The ladder, cheapest first

| check | catches | blind to |
|---|---|---|
| `node --check` on the extracted `<script>` | syntax errors | every logic error |
| `eval` behind a ~40-line DOM shim, assert on computed numbers | wrong values, filter-state bugs | anything visual |
| dump `innerHTML`, feed to Python's `html.parser` | unbalanced tags the shim swallows | layout, palette, overflow |
| **render + look** | everything above, plus what a reader will actually see | interaction, other viewports |

A page that renders inside a vendor dashboard or report module has extra constraints of its
own — check whether your setup has a skill covering that platform's specific rendering quirks.

## Gotchas that cost time

Full worked incidents (measured, with the tells that separate a real defect from the instrument) are
in `references/gotchas.md` — read it before diagnosing any of these, since the fix is rarely
obvious from the one-line version:

- `prefers-color-scheme` does not apply under `--screenshot` — copy the page, swap the media query for
  `@media all`, shoot the copy.
- `:hover`/`:focus`/`:target` never fire under `--screenshot` — rewrite the selector into a real class
  on a middle element instead.
- An SPA needs `index.html` fallback for routes but NOT for `/api/*`, or a 200-with-HTML masquerades
  as a broken data response.
- A fetch/XHR page needs `file://` abandoned (serve over HTTP) AND `load` delayed (a slow `<img>`, a
  threaded server) or you photograph the pre-fetch state — several distinct ways to get the same wrong
  picture, and reading the server log is what tells them apart. Never patch this with a synchronous XHR.
- `--timeout=<ms>` is a cap, not a delay; `--virtual-time-budget` hangs forever against a live poll; a
  click harness's timer must fire inside the slow image's delay.
- Make any injected probe report itself into the page (a `<pre>`) — a screenshot can't read a console,
  and a failed-to-install probe is pixel-identical to an ignored click.
- To click a real control, wait for `DOMContentLoaded` (inline scripts run before `defer`red ones);
  when a click seems to do nothing, add a second listener beside the app's to tell "app ignored it"
  from "event never arrived."
- A canvas scene becomes pickable *later* than it becomes visible, and later still as you add layers —
  gate on two consecutive agreeing surveys, never a frame count. Hit-testing also needs an occlusion
  control, or off-screen/behind-geometry misses read as defects.
- Hoisting a section into view needs `:not([hidden])` in the exemption selector, or `display: revert`
  un-hides everything real hiding logic hid.
- Restarting a live app's server before trusting a shot — a stale process and a failed change produce
  an identical screenshot.
- `glxtest: Unable to open a connection to the X server` on stderr is harmless noise.
- A page with no `<meta charset>` served by `python -m http.server` (no charset in the header)
  renders UTF-8 as mojibake (`ðŸ` for emoji). If the real host adds the charset, serve with an
  explicit `text/html; charset=utf-8` before calling it a page defect.
- CSS fade-ins (`animation: … both`) are often photographed mid-fade, so a line looks faint or
  missing. Before reporting low contrast, re-shoot with `prefers-reduced-motion` forced or past the
  animation, and compare against a non-animated element in the same shot.
- Runs can exceed two minutes; give the call a long timeout.
- `--network=none` is deliberate — a page going blank without network is a finding about the page.

## Reading the result

Look for **content that is present but wrong**, not just for a broken page — an unresolved
identifier rendered as an ordinary value, a `—` where a number belongs, a legend disagreeing with
its series. Those are what the cheap checks structurally cannot see.

**One viewport proves one viewport.** Render narrow too if the page claims to be responsive.

**Headless Chromium will not lay out narrower than 500px** (both `--headless=new` and `=old`,
measured on Chromium 153): `--window-size=390,…` renders a 500px layout and crops the image to
390, so a "phone" shot never crosses a phone breakpoint and looks plausible anyway. Assert
`document.documentElement.clientWidth` equals the width you asked for; below 500, load the page
in an `<iframe>` of the real width inside a 500px window and crop to it.

**Two more headless-screenshot traps** (measured on Chromium 153, `--screenshot`): a page scrolled
before capture draws `position: fixed` elements in the wrong place, so capture from `scrollY` 0.
And a harness still running past Chromium's `--timeout` cap hangs the whole run with no image;
send the harness's findings to the server's log with a `fetch`, so a hang still leaves the result.
`content-visibility: auto` blanks a `full_page` shot (shoot the viewport). Load timings and `elementFromPoint`
hit-tests are not `--screenshot` questions either: drive a real navigation. Both are in `references/gotchas.md`.

**And shoot the COLD page — the state a first-time visitor lands on, before any click, any pick,
any typed query.** Everything above is about a rendered thing being *wrong*; this is about it being
*unreachable*, which no amount of looking at the working feature can reveal.

Worked case: a PDF export shipped and the user reported not finding it. The endpoint returned a
valid PDF, the button called it correctly, and the button sat inside a view whose entry link was
rendered `hidden` until at least one row had been ticked — using checkboxes in a 22px column headed
by an unlabelled `+`. Three gates in front of one feature. Every check run against it passed,
because the feature worked perfectly once you were already inside it.

**The trap is that verifying a feature means exercising it, and exercising it means putting the page
into the state where it is reachable** — so the act of testing destroys the condition you needed to
observe. "I tested it" therefore carries no information at all here, and no more careful look at the
shots you already have will help; it needs its own shot.

Two things make the cold page cheap to get and easy to skip. It usually needs no fixtures, no server
and no delayed `load` — header chrome and empty states render before any fetch resolves, so
`file://` on the raw template is often enough. And an empty state is the least interesting picture
the page can produce, which is exactly why nobody takes it.

So: **before calling a UI feature done, render the page as if you had never used it and find the
feature in the picture.** If you cannot point at it, neither can the user. Then read the empty
states you landed on — a blank panel is a wasted chance to say how to fill it.

## When not to bother

A page nobody will look at, a fragment with no styling, or a change confined to text content that a
test already covers. The reflex is for work someone will read on a screen, not for every file that
happens to contain HTML.

## Pages behind a login

A screenshot tool cannot log in, and the obvious workarounds are worse than the real one.

**Do not reach for the app's own image endpoint.** A vendor dashboard's image endpoint returned a rendered PNG in
older versions and returns *JSON* in newer ones — the charts are drawn client-side now. A `.png` file that is
actually JSON looks like a successful fetch until you open it.

**Seed the session cookie into a throwaway Firefox profile.** Log in with `urllib`/`curl` to get the
cookie, write it into the profile's `cookies.sqlite`, then screenshot with that profile:

```python
db = sqlite3.connect(f"{profile}/cookies.sqlite")
db.execute("""INSERT INTO moz_cookies
  (originAttributes,name,value,host,path,expiry,lastAccessed,creationTime,
   isSecure,isHttpOnly,inBrowserElement,sameSite,schemeMap,isPartitionedAttributeSet)
  VALUES ('', ?, ?, ?, '/', ?, ?, ?, 1, 1, 0, 0, 2, 0)""", (...))
```

The profile must already exist — run Firefox once against any URL to create it, then check the
`moz_cookies` schema before inserting, since columns vary by version. Use a throwaway profile
directory, never the user's: a real profile may be in use by a running browser.

**Behind an auth proxy that trusts an identity header, add it per request, not per context.**
Playwright's `extraHTTPHeaders` goes on every request, third-party ones included, so a header like
`X-Forwarded-Preferred-Username` triggers a CORS preflight that Google Fonts rejects: the page renders
in fallback fonts and looks subtly wrong rather than broken. Use `page.route()` to add the header only
to the app's own origin.

**Never enable a guest/anonymous account to get a screenshot.** It is a security change to a live
system for a picture, and it is easy to forget to undo.

## Scope

Any HTML a human will look at qualifies — vendor report templates, generated dashboards, a published
artifact, a candidate app's UI stood up under `repo-vet`. The reflex is the point: **when the
deliverable is something someone will read on a screen, look at it on a screen before saying it is
done.**
