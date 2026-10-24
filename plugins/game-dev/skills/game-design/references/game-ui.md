# Game screens, HUD and touch

Layout and controls of a game screen, not a data page (that is `ui-craft`). Sources: `evidence/game-ui.jsonl`. No
developer postmortem on how an idle game's screen grows was found.

## Place each element on two axes, and treat a plain HUD as an honest fallback

- Fagerholt and Lorentzon cross fiction (does the element exist in the story world?) with space (is it in the game's
  geometry?). Their final map has six categories: non-diegetic (the HUD), meta-perception, meta-representation,
  geometric, diegetic, and signifiers (subtle world cues, like smoke from a weapon about to break). The popular
  four-word version is a later summary, not the thesis's list (research, Chalmers thesis 2009, first-person shooters
  only).
- The more competitive the game, the more a clear overlay is reasonable ("ambiguous information should be avoided"
  where fast decisions matter); the more plausible the world, the more a stray HUD element hurts; a world that admits
  being artificial tolerates them (research, same).

Rule: ask per element whether bringing it into the world costs legibility. Where it does, keep a plain control and spend
the fiction on its words and art. The evidence is from shooters, not management or idle games.

## "Can they use it" and "do they want to" are separate failures

Usability is "removing or at least alleviating all the frustrations and confusion the player could experience while
playing the game, if they are not intended by design"; the second pillar is engage-ability (gameflow in her blog).
Usability "is not about distorting the intended experience" (practitioner, Hodent's blog). "I didn't know what to tap"
and "I knew and didn't care" need different fixes: diagnose which before changing the screen.

## Show the state and its consequence together, before commitment, in small numbers

Into the Breach is credited with showing every enemy intent and previewing outcomes before the player commits, with
health and damage rarely above single digits, so one screenshot holds the whole state (opinion, reviewers; postmortem
seen as a listing only). Verified line: "a push to be more deterministic in the moment-to-moment gameplay"
(practitioner, PC Gamer quoting Matthew Davis).

Rule: a number the player must compute from two others is a UI defect. Precompute it and print it beside the thing it
affects.

## A growing interface grows in one place at a time, each addition with its reason

- A Dark Room opens on a title, two lines and one button, and adds elements slowly so the interface's growth mirrors
  the world's; critics flag that minimalism with no direction loses some players (opinion, no developer account).
- Idle developers report hiding sections until a threshold, pruning side panels nobody used, players asking to see the
  next unlock so they can plan, and confusion when a displayed unlock requirement didn't match when content really
  appeared (practitioner, devlogs, snippet).
- An idle-game taxonomy lists UI among its features but reports no interface findings in the abstract (research,
  Alharthi et al. CHI 2018, abstract only).

Pattern, supported only by those snippets: reveal on first relevance, show the next gate truthfully, retire unused
panels.

## Touch is a different device, not a small mouse

- Grip: 49% one-handed, 36% cradled, 15% two-handed, changing with the task, sometimes every few seconds (research,
  Hoober 2013, 1,333 observations). His later correction: the thumb-reach drawings are "a bit of a lie because I
  over-assumed. People touch the center of the screen. More, more quickly, more accurately, and by preference. Not the
  corners or edges." and "Please, please everyone ignore those drawings." (verbatim). Centre targets can be "as small as
  7 millimeters" against "about 12 millimeters" in corners, sized to hold 95% of observed taps; keep dangerous actions
  away from common ones (research, Hoober 2017).
- So a thumb-reach map is not where controls must live: primary content and actions near the centre, secondary actions
  along the top and bottom edges, dangerous ones apart, and test on devices. Hoober calls pixel standards "useless" and
  the platforms' sizes convenience more than human factors: the figures below are floors, not finger measurements.
- Target size: WCAG 2.2 2.5.8, at least 24 x 24 CSS px or a 24 px non-overlapping circle; 2.5.5 stricter for important
  controls (guideline). Apple: hit region "at least 44x44 pt", with a 28x28 pt minimum in its control table
  (guideline). Android: "at least 48dpx48dp. Larger is even better", padding counts, small targets "separated by 8dp
  of space or more" (guideline). Game Accessibility Guidelines: interactive elements "large and well spaced,
  particularly on small or touch screens" (guideline).
- Hover: touch has no persistent hover. Fixes: tap to toggle and tap elsewhere to dismiss, long-press, or gate
  hover-only content behind a hover-capability media query (practitioner, snippet). WCAG 1.4.13 is written for pointer
  and keyboard focus and never mentions touch (guideline). Rule: anything that matters is reachable with no hover;
  hover may only repeat it.
- Mobile browsers: `100vh` is the large viewport and overflows while the address bar shows; `dvh` tracks the live
  viewport, `svh` the smallest; a bottom-pinned bar needs `viewport-fit=cover` and `env(safe-area-inset-bottom)`.
  Sources disagree on `dvh` vs `svh` for bottom bars, and `dvh` can shift layout (practitioner, snippet).
- A VoiceOver user found a long-running browser idle game's mouseover text and assign links unusable (verbatim,
  AppleVis, snippet).

## Accessibility basics for any screen game

Readable default font size; high contrast between text and background; no essential information by colour alone or
sound alone; text advanced at the player's pace; start without multiple menu levels; all UI reachable with the
gameplay's input method; save all settings; avoid flicker. Most complained about: remapping, text size, colour
blindness, subtitles. The source gives no pixel sizes or ratios, so none are added here (guideline, Game Accessibility
Guidelines, basic tier).

## What the evidence cannot say

Not found: Game UI Database pattern findings; developer accounts from Frostpunk, Darkest Dungeon, Slay the Spire, Melvor
Idle or Cookie Clicker on their screens.
