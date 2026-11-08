# Feel and look: controls, buttons, visuals, polish

How input should feel in the hand and how a game should read to the eye. Feedback to events (juice, effects, reduced
motion) is `feedback.md`; screen layout and touch targets are `game-ui.md`. Sources: `evidence/feel-and-look.jsonl`.
The touch-latency primaries were reached as abstracts only, and no developer gives frame counts for coyote time,
buffering or hitstop.

## Latency hurts precise, deadlined actions most

- The more precise the action (a small target) and the tighter its deadline, the more lag hurts; selecting from a menu
  tolerates it, aiming at a small moving target doesn't (research, Claypool & Claypool MMSys 2010 for size and
  deadline effects, bots, so it shows score impact, not perception; snippet, Claypool & Claypool CACM 2006 for the menu
  contrast).
- Touch: dragging performance fell as latency rose (1, 10, 25, 50 ms; n=45), worse for smaller or farther targets, and
  every step except 1 vs 10 ms was significant; commercial devices had up to 125 ms (research, Jota et al. CHI 2013,
  full). Noticing it depends on the task and the screen. Mean just-noticeable latency: direct drag 11 ms, indirect drag
  55 ms, direct tap 69 ms, indirect tap 96 ms (research, Deber et al. CHI 2015, full; 14 people, a lab rig). Jota
  measured only the tap case: mean 64 ms, range 20-100, nobody noticed under 20 ms (n=20). So "drag lag noticed from
  about 5-10 ms" fits 11 ms direct (Ng 2 and 6 ms, via Deber); "taps under about 24 ms unnoticed" is Deber's
  paraphrase of Jota's 20 ms, which was the floor for everyone, while the typical person tolerates about 64-69 ms.
  Removing one 60 Hz frame (16.7 ms) is noticeable in direct drag and mostly not in tapping below 33 ms (research,
  Deber, full).
- Nielsen's 100 ms (`feedback.md`) is the ceiling for "the system reacted", not a target for direct manipulation (inference).

Rules: give each input a latency budget by its target size and deadline; the strictest get the most engineering. Show
the press on the next frame and never wait on a network round trip to show it (inference).

## Forgive timing the player can't perceive

- Celeste's makers describe many forgiveness windows: a jump shortly after leaving a ledge (coyote time), a jump pressed
  just before landing that fires on landing (buffering), wall-jumps from 2 px away, lift momentum kept "a few frames".
  They give no frame counts (developer, Thorson via Gigazine summary of the 2020 thread). Its ten Assist Mode options also widen timing in
  the player's favour (`difficulty.md`). Community starting values (about 5 frames coyote, about 7 buffer at 60 fps) are third-party
  and disagree (unverified).
- On a hit, Sakurai freezes both parties for the same time, longer for stronger hits up to a hard cap, less for
  projectiles, with a shake that keeps hitboxes fixed; he keeps it short because in free-for-alls other players act
  during the freeze (developer, Famitsu column, fan translation; no frame counts).
- "The feel of the PC should always take precedence over the aesthetics of the animations": player wind-ups short,
  enemy wind-ups long (practitioner, Game Anim; the page does not name its author in the fetched text).

Rules: forgive what the player meant; scale hit-freeze with impact, cap it, and weigh it against anyone still acting;
telegraph the enemy, never the player's own action. Tune windows by playtest from the community values.

## Every control has distinct states, and none is carried by colour or haptics alone

- Enabled, pressed, focused and disabled each look different (inference). A disabled control gets a second signal
  beyond grey (a lock, "Not available") (guideline, Xbox XAG 103). Material's state-layer opacities could not be
  fetched (unverified).
- Haptics: one pattern per meaning, strength matched to the animation, short, sparing, optional, and the game fully
  playable without them: "often the best haptic experience is one that people may not be conscious of, but miss when
  it's turned off" (guideline, Apple HIG, full).
- Tactile feedback on a touch keyboard gave more text entered and fewer errors when static; on a moving train only
  errors corrected improved, though users liked it; tactile brought finger entry close to a physical keyboard (snippet,
  Brewster et al. CHI 2007; Hoggan et al. CHI 2008). A later unnamed York study found no effect on speed or accuracy
  (snippet). Haptics aid satisfaction and error recovery; accuracy gains are not proven (inference).
- No peer-reviewed study of UI button sounds was found. Practitioner advice: a sound says what the player did and what
  happened, in a tone that matches the game (practitioner, Audiokinetic, snippet). Varying repeated sounds, keeping
  the set small and letting players mute are inference.

## Read by silhouette first, then colour

- Valve checked all nine Team Fortress 2 classes as pure silhouettes during concept, because identifying a class is
  core to play; then emphasised silhouettes with rim highlights, pushed shadows cool instead of black, dropped
  high-frequency detail and raised value contrast. Teams differ on three axes: red warm, natural, angular; blue cool,
  industrial, orthogonal. Photoreal detail "can overpower" the designer's ability to emphasise what matters (developer,
  Mitchell, Francke & Eng NPAR 2007, full; design rationale, no player data).
- Colour never carries information alone: pair it with shape, pattern, icon or text, let players recolour where colour
  is the main signal, check with a simulator and then with colour-blind players (guideline, Game Accessibility
  Guidelines, basic; Xbox XAG 103).
- Contrast: 4.5:1 for text and UI elements, 3:1 for large text and for text on disabled elements, 7:1 in a
  high-contrast mode, measured against the worst part of a busy background (guideline, Xbox XAG 102).
- A colour-blind-safe categorical set designed by Okabe & Ito: #E69F00 #56B4E9 #009E73 #F0E442 #0072B2 #D55E00
  #CC79A7 #000000 (snippet, package docs; original page not reached). Eight hues are hard to tell apart in
  play, so still add shape or label (inference).

Rule: if a thing matters in play, a player must be able to name it from its outline, in greyscale.

## A pleasant look raises perceived usability, not actual usability

- People rate attractive interfaces as easier to use: apparent usability correlated with beauty across 26 ATM layouts,
  ratings without use (snippet, Kurosu & Kashimura 1995). Sources conflict on the sample and number: a Wikipedia
  snippet gives 252 raters and r=.589; Monk & Lelos's introduction gives 156 students and r of about 0.6 (research,
  Monk & Lelos 2007, partial). A cosmetic change alone raised usability ratings of can openers in Experiments 1 and 3 of
  the three (research, Monk & Lelos 2007, partial; abstract and introduction read). After use, aesthetics shifted
  perceived usability while actual usability did not (snippet, Tractinsky et al. 2000).
- No game-specific replication was found; a review notes very few studies address game visual aesthetics (snippet).

Rule: spend art effort first on the first screen and the controls, where looks may buy patience (inference); never
count on looks to cover a real usability problem.

## Polish is consistency plus small things missed only when absent; schedule it

- Developers define polish as consistency of experience (Darrah) and small unseen things (Kowalkowski, Rubalcalba).
  Polish is not leftover buffer (Fergusson); list every item, estimate it, rank by effect on play, set the quality bar in
  advance, and triage late fixes because each can add bugs (developer, Game Developer 2009 interviews with Darrah,
  Kowalkowski, Rubalcalba, Fergusson, Dwyer).
- No source for polish cost was found: the one polish-cost talk found (Bithell, GDC 2015) has nothing on cost in its
  description, and circulating percentages are unsourced (unverified).

Rule for a small team: polish the most repeated input and the first minute first (inference).

## What the evidence cannot say

Touch latency thresholds from the primaries (PDFs unreadable); developer-stated frame counts for coyote time,
buffering or hitstop; any source applying Disney's principles or camera feel to games; a peer-reviewed study of UI
sound; a game replication of the aesthetic-usability effect; polish cost figures. Nothing here was tested in gamified
apps.
