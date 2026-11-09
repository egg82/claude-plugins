# Game screens, HUD and touch

Layout and controls of a game screen, not a data page (that is `ui-craft`). Sources: `evidence/game-ui.jsonl` and `evidence/legibility.jsonl`. No
developer postmortem on how a growing game screen was designed was found.

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

Hodent splits game UX into two pillars, usability and a second one she names gameflow ("engage-ability" is her later
wording: blog index, book chapter titles), and rejects the misconception that UX distorts design intent (practitioner,
celiahodent.com, read). Her definition: usability is "removing or at least alleviating all the frustrations and
confusion the player could experience while playing the game", if they are not intended by design (practitioner,
celiahodent.com, read). "I didn't know what to tap"
and "I knew and didn't care" need different fixes: diagnose which before changing the screen.

## Show the state and its consequence together, before commitment, in small numbers

Into the Breach's makers made telegraphed enemy attacks "a core mechanic" so failure is clear (developer, Justin Ma;
`legibility.md`), and "a push to be more deterministic in the moment-to-moment gameplay" (practitioner, PC Gamer
quoting Matthew Davis). Outcome previews before commitment, and health and damage rarely above single digits so one
screenshot holds the whole state, are reviewers' descriptions (opinion; the postmortem is behind the GDC Vault).

Rule: a number the player must compute from two others is a UI defect. Precompute it and print it beside the thing it
affects.

## A growing interface grows in one place at a time, each addition with its reason

- A Dark Room opens on a title, two lines and one button, and adds elements slowly so the interface's growth mirrors
  the world's; critics flag that minimalism with no direction loses some players (opinion, no developer account).
- One idle developer's write-up reports hiding sections until a threshold, pruning side panels nobody used, players asking to see the
  next unlock so they can plan, and confusion when a displayed unlock requirement didn't match when content really
  appeared (practitioner, devlogs, snippet).
- An idle-game taxonomy lists UI among its features but reports no interface findings in the abstract (research,
  Alharthi et al. CHI 2018, abstract only).

Pattern, supported only by those snippets: reveal on first relevance, show the next gate truthfully, retire unused
panels.

## Touch is a different device, not a small mouse

- Grip: 49% one-handed, 36% cradled, 15% two-handed, changing with the task, sometimes every few seconds (research,
  Hoober 2013, among the 780 of 1,333 observed users who touched the screen). His later correction: the thumb-reach drawings are "a bit of a lie because I
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
- Mobile browsers: `vh`/`lvh` assume the browser's toolbars retracted, so content can hide behind them when they show;
  `svh` assumes them expanded; `dvh` tracks the live state and is "not stable even while the viewport itself is
  unchanged", and browsers need not animate it (guideline, W3C CSS Values 4, partly read). Inference: `dvh` can shift
  layout as toolbars move; `svh` vs `dvh` for a bottom bar is a design call, not a spec dispute. A bottom-pinned bar also needs
  `viewport-fit=cover` and `env(safe-area-inset-bottom)` (practitioner, snippet; that spec not checked).
- A VoiceOver user found a long-running browser idle game's mouseover text and assign links unusable (verbatim,
  AppleVis, snippet).

## Accessibility basics for any screen game

Readable default font size; high contrast between text and background; no essential information by colour alone or
sound alone; text advanced at the player's pace; start without multiple menu levels; all UI reachable with the
gameplay's input method; save all settings; avoid flicker. Most complained about (not necessarily most needed):
remapping, text size, colour blindness, subtitles. The source gives no pixel sizes or ratios, so none are added here (guideline, Game Accessibility
Guidelines, basic tier).

## The settings menu

- TotalBiscuit gave Borderlands 2's options menu its own video in 2012, as a model PC menu (practitioner, "What a PC
  Options menu is supposed to look like", captions read in full). What he checked: a field-of-view slider with numbers
  (70-110; 90 "industry standard for PC"); every resolution; HUD size and bounds adjustable, since console HUDs are
  sized for a television "half the room away"; windowed mode and vsync; a frame cap with several values including
  unlimited and 120; graphics detected from the hardware with granular overrides; separate music, effects and dialogue
  levels; mute when minimised; push-to-talk; toggle or hold for aiming; training messages can be turned off; mouse
  smoothing off by default ("quite frankly terrible"); full key rebinding with a reset. His GTA V port report adds raw
  mouse input by default and an on-menu video-memory meter, which he caught over-reporting under SLI (practitioner,
  2015, captions). A missing FOV slider was a hard stop for him, partly for motion sickness (snippet, tweets).
- PCGamingWiki's guide for reviewing a PC port checks: video settings, flagging a missing field-of-view slider in
  first- and third-person games; controls, testing mouse acceleration and key customisation; audio, checking
  subtitles, closed captions and volume sliders (practitioner, PCGamingWiki PC Report guide, read in full).
- A port developer's own launcher: "Every single option has a description text, and often it also shows visual
  comparisons"; a choice with no reason to pick less (16x anisotropic filtering) becomes a checkbox; unlimited frame
  rate is offered at "your own risk" (developer, Durante, Trails of Cold Steel PC).
- Settings reachable before starting and during play, effects previewed in the menu, one quality preset plus
  per-element control, master and per-channel volume, a keybind reset, a prompt before leaving unsaved (practitioner,
  Giguere checklist, Game Developer 2018, experience-based).
- Two of Pinelle et al.'s ten heuristics are settings: "Allow users to customize video and audio settings, difficulty
  and game speed" and "Provide intuitive and customizable input mappings". Customisation was a small share of review
  complaints, 11 of 285 problems (research, CHI 2008, read in full).
- Remember every setting between sessions (guideline, Game Accessibility Guidelines, basic). Offer accessibility
  settings as the first screen at first launch, or meet the guidelines by default (guideline, XAG 112, Minecraft
  Dungeons). Presets that set every recommended option, each still adjustable afterwards (developer, Naughty Dog, The
  Last of Us Part II).
- On mobile: defaults that suit most players, detected rather than asked for; "Minimize the number of settings";
  don't repeat system accessibility settings (guideline, Apple HIG Settings, 2024).
- Users do change settings: 92% of 101 word-processor users customised something within 28 days (research, Page et
  al. CHI 1996; self-selected, not games). "Nobody changes defaults" is folklore; bad defaults still cost, since 44%
  removed default buttons. What stops people is time (63% of 51 users) and difficulty (33%); what starts them is
  an upgrade that changed things (43%), noticing their own repetition (43%) or annoyance (41%). Users customise to make
  new versions "be like the old", so a patch that resets settings or keybinds undoes the work they protect (research,
  Mackay CHI 1991, read in full; Unix staff, not games).
- Display changes commonly revert after about 15 seconds unless confirmed, and users call the window too short (snippet,
  desktop OS bug trackers; no game source).

Rules: PC players treat a missing setting as a defect, not a simplification. Detect the defaults, then expose the
granular control behind them, each with a line saying what it does and what it costs, and a preview where it shows.
Comfort settings (FOV, motion blur, camera shake, HUD scale) are accessibility, not polish. Mobile and casual games
take Apple's side: fewer settings, better defaults (inference from the platform split above).

## What the evidence cannot say

Not found: Game UI Database pattern findings; any study of settings-menu design in games (presets vs granular, search,
live preview); Digital Foundry's praise of specific settings menus (unverified); developer accounts from Frostpunk, Darkest Dungeon, Slay the Spire, Melvor
Idle or Cookie Clicker on their screens.
