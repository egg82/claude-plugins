# UI and accessibility oracles — render it and look

Load when the target has a front end a person uses. Reading the template finds little: the defects are in what the
browser actually draws, at sizes, themes, inputs and states the author never opened. The oracle is the rendered page
compared with what it claims to show and with what a keyboard, a screen reader or a phone can do with it. Proof is a
screenshot, an accessibility-tree dump or an automated audit result, taken through the real build (`headless-render`
for the method; `claude-in-chrome` for driving interactions).

## Run what ships, first

- **`axe-core`** (via Playwright, or Lighthouse's accessibility audit) over every route in every state you can reach.
  It catches missing names, bad contrast, broken ARIA and form labels mechanically; it cannot judge whether the name is
  *right*, and many WCAG criteria can't be automated at all, so a clean run bounds itself.
- **The HTML validator** over the rendered DOM: duplicate ids, nesting errors and unclosed elements break assistive
  tech before they break the eye.

## Lenses

- **Unknown rendered as a value.** A missing, stale or timed-out figure shown as `0`, a green tick or a blank that
  reads as "none" (honesty rules in `ui-craft`). Kill the data source and screenshot.
- **States nobody opened.** Empty, loading, error, one item, ten thousand items, a 60-character name, a name in Arabic
  or with emoji, a value of zero and a negative one. Each is a screenshot, and the differential applies: if four list
  pages have an empty state and the fifth shows a bare table header, that is the bug.
- **Sizes and themes.** Phone width (no horizontal scroll, nothing clipped, tap targets at least 24 px), 200% zoom,
  dark mode, reduced motion. A colour defined for light only shows up as dark-on-dark.
- **Keyboard only.** Tab through every route: every control reachable, focus visible, order matching the layout, no
  trap inside a modal or menu, Escape closes what it opened, focus returns where it was.
- **Screen-reader names.** Dump the accessibility tree: an icon button with no name, a chart with no text alternative,
  an image whose alt repeats the caption, live updates (a toast, a counter) with no `aria-live` so they are never
  announced.
- **Forms.** Errors announced and tied to their field, input preserved after a failed submit, autofill and paste
  allowed on credentials, the right `inputmode` and `autocomplete` on phone, email and one-time codes.
- **Discoverability.** A feature that works but a first-time visitor cannot find. Shoot the cold first-visit page and
  ask where each documented feature's entry point is (`headless-render` covers the method).
- **Copy that contradicts behaviour.** A button labelled "Save" that also publishes, a confirmation that names the wrong
  consequence, an error that says "try again" for a failure that will never succeed (`writing-craft`'s
  `references/ui-text.md` for the wording itself).

## Traps

- **A backgrounded tab stops drawing.** Before any visual claim from a live browser, assert
  `document.visibilityState === "visible"`; rAF-driven canvas, charts and maps stop silently while screenshots still
  return — *(incident)* this once produced a published false defect report (`headless-render`).
- **A dev server is not the build.** Minification, CSP, base paths and asset hashing change behaviour; render the
  production build.
- **Taste is not a finding.** "Could look nicer" belongs to `ui-craft`; a defect here is something a user cannot do,
  cannot see, or is told wrongly.
