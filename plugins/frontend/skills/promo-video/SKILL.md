---
name: promo-video
description: "Make a short, polished promo video of a real website or web app entirely from code — scripted browser, eased cursor, zooming camera, captions, title cards, optional sound — rendered to 1080p60 mp4 with no manual recording. Use when someone wants a promo, launch, demo or explainer video of their site, or says an agent driving a browser \"would make a neat video if it were smoother\". Starts by interviewing the owner. NOT AI-generated footage, NOT screenshots (headless-render)."
---

# Promo video

A real site, filmed by a script. The script decides; the capture performs at human pace;
post-production adds the camera, captions and sound. Every frame of UI is real.

`engine/` is the method and stays generic. Each project keeps its own **promo dir**
(`theme.json`, `scenes/`, `assets/`, `videos/`, `brief.md`) in its repo, because scenes go
stale when the site changes, not when this method does. Record what this host has (container
image, browser, ffmpeg, CPU count) in `~/.claude/local/promo-video/instance.md`; none ships.

## 1. Interview the owner first

**Do not choose the pitch yourself.** The README's tagline is not necessarily the video's
pitch. The first cut built this way sold a site on its integrity rule, and the owner's
answer was that the selling point is the platform and what you can do with it. A
polished video of the wrong message has to be redone from scratch.

Explore the site first (screenshot the main pages), so each question arrives with a
proposal the owner can react to rather than a blank. Ask in prose, two or three at a time,
not as forced multiple-choice:

- **What is it, in their words**, one sentence, for someone who has never heard of it.
- **Who is this video for?** One audience per video. Users and builders/contributors are
  usually two videos with different hooks, and trying to serve both makes a tour.
- **What do they think is coolest?** The two or three moments they'd show a friend. These
  become the beats. Offer your candidate list from the exploration; they will correct it.
- **Where will it play?** Social feeds autoplay muted, so captions carry it. A landing
  page can run longer. A README embed should be short and loop.
- **Sound:** none, effects, or effects plus a music file they supply. None of these is the
  default. Some videos are better silent. Picking and levelling effects or music is `audio-curation`;
  voice-over and narration lines follow `writing-craft`'s `references/speech-and-scripts.md`.
- **Off limits:** anything unfinished, private, or about to change.
- **Demo or story?** For a game or any world with characters, offer a narrated story trailer instead of the
  captioned demo (§2, "Demo or story trailer"). Someone outside video work will answer on feel, so cut a
  short draft rather than describing the two.

Write the answers to `<promo-dir>/brief.md` so the next cut doesn't re-ask.

## 2. Storyboard

For 30–45s (sourced from practitioner writeups of SaaS launch videos; no controlled study):

| time | what |
|---|---|
| 0–3s | Hook: on-screen text naming the problem or the payoff, never a logo bumper |
| 3–35s | One to three beats from the owner's "coolest" list, each one continuous interaction |
| last 3–5s | One call to action: name plus URL. Only one ask |

- **A beat is something happening on screen**, not a page being shown. Filtering, typing,
  dragging and a table reflowing all beat a static pan across a dashboard.
- **Every caption must be true.** Check each claim against the page or the code (what a
  badge means, what a number counts) before filming it. A promo is still an artifact that
  asserts things.
- **Build the story around real data, and guard it.** A scene's `setup()` should assert that
  the facts the captions depend on are still on the page, and throw if they have moved.
  Filming stale claims is worse than failing.

### Demo or story trailer: ask which

The storyboard above makes a **demo**: captioned beats over the UI, cards between them. It suits a tool and
reads like a slide deck. When the thing is a world (a game, a simulation, anything with characters), the owner
may want a **story trailer** instead. Three cuts of one game's trailer converged on these rules, and its owner
rated the last one the best:

- **About 95% story.** Write it from the product's own content (its in-game history log, real events). The core
  mechanic is one beat inside the story, and the hint of agency is the last line. End on a wry button line over the title.
- **Cut the picture to the voice.** Narration runs almost the whole time over music, with breaths of about a
  second. A shot ends when its line does. Picture that outlasts the voice reads as dead air, and stripping
  lines to "let the footage breathe" made the cut feel empty. Here, a narrator describing what's on screen is
  fine; that advice comes from talks, not trailers. When an on-screen event has to finish (a speech bubble),
  time a short line after it so the voice lands on it.
- **The camera flows.** Frame each shot before filming starts, so no clip opens on the app's own view. Use
  linear drifts that keep one direction across cuts, and follow characters moving that way. An ease-in-out
  filmed from its start reads as a lurch.
- **Captions are short echoes of each line,** never a transcript and never a long silence without one.
- Craft sources: Derek Lieu's game-trailer blog (picture to voice, eye trace, cut on motion, long shots for
  cozy games) and Walter Murch (cut where a thought ends).

Scripted in-world cameras and a staged world live in the project, not here. `references/traps.md` covers the clock traps.

## 3. Write scenes

A scene is `scenes/<name>.mjs` exporting `setup(page, d)` (navigate and wait; not recorded)
and `act(page, d)` (recorded). `d` is the Director:

| call | does |
|---|---|
| `d.click(sel, {zoom})` | eased cursor travel, press, ripple, click; camera zooms to the target |
| `d.hover(sel, {zoom, spot, below})` | travel and dwell. `spot` dims everything else in post. `below` rests the cursor under the target so it doesn't cover the text |
| `d.type(text)` | human cadence, per character |
| `d.drag(sel, from, to)` | slider drag between fractions of its width |
| `d.scrollTo(sel)` | eased scroll |
| `d.wide()` | camera back out to the full frame |
| `d.park(x, y)` | move the cursor somewhere neutral |
| `d.caption(text, secs)` | caption pill composited in post |
| `await d.say(text)` | narration line, also shown as the caption; the next line waits for this one |
| `d.accent()` | marks the beat the story turns on; sounds only if the spec names an accent sample |
| `await d.fastForward(fn)` | whatever `fn` waits for (a slow server, a re-render) plays at 20x, effectively a cut; later cues are retimed |
| `d.prewarm(sel)` / `d.startAt(x, y)` | setup only: load a hover card off camera / place the cursor before filming |
| `d.select(sel, value)` | pick from a `<select>`: the cursor clicks it, the value is set (a native dropdown never paints headless) |

**The camera fits the target, then keeps the cursor in frame.** `zoom` is a ceiling: it
never zooms tighter than keeps the whole target visible, and the spot where the cursor
rests stays inside the frame. So zooming on a full-width row gives little zoom. To push
in tight, target the small thing the eye should land on (a name, a value, a cell),
not the row or panel around it.

Every action scrolls its target into view first (eased), so a scene never has to.
`setup()` may stage state off camera (build a list, make a few selections) and should throw
if the state it needs isn't there. A guard is only worth having once you've seen it fire.

Title cards: `import { card, words, logo } from "../cards.mjs"`; see its header for the
vocabulary. `videos/<name>.json` lists the cut as alternating scene and
[xfade transition](https://trac.ffmpeg.org/wiki/Xfade) names, plus `sound`, `music`,
and the format: `output` (frame px), `viewport` (browser CSS px, which sets the window's
shape) and `safe` (top, bottom and side fractions a platform's overlays cover).

## Formats

One set of scenes renders to any number of formats. Write a video file per placement,
never one compromise master.

| placement | output | safe (top, bottom, side) | viewport that reads well |
|---|---|---|---|
| landing page, YouTube, README | 1920×1080 | default | 1280×720 |
| Facebook/Instagram Feed | 1080×1350 (4:5) | default | 900×900 |
| Reels / Stories | 1080×1920 (9:16) | 0.14, 0.35, 0.06 | 900×900 |

The Meta figures come from its ads guide ([feed](https://www.facebook.com/business/ads-guide/video),
[reels](https://www.facebook.com/business/ads-guide/update/video/instagram-reels)): Reels
keeps the top 14%, bottom 35% and 6% each side free of text; Stories is 14% top and 20%
bottom, so Reels' numbers cover both. The guide requires a fixed frame rate and stereo
AAC, and caps neither at 30fps. "Fifteen seconds or less" for ads is practitioner
consensus, not a Meta page. Keep ads to one or two beats.

A narrower viewport makes the site lay itself out for the frame. Check what its
responsive layout does at that width before filming, since it may be a different page.

**Start at 16:9 for a desktop-first site.** A dense desktop page squeezed into a 9:16
window reads as tiny text however the camera zooms (the owner's verdict on the first
Reels cut). A 16:9 cut can also run 45–60s, which lets the beats breathe. Treat the tall
shapes as later cut-downs of beats that already work, filmed at tighter zooms.

## Voiceover

**Captions alone are not enough.** A viewer who didn't watch the captions came away
confused. Narrate: `await d.say("…")` speaks a line and shows it as the caption, and
`card({ voice: "…" })` speaks over a title card. `vo.py` synthesizes every line before
filming, so each scene is paced by its narration: a line waits for the previous one, and
the scene waits for its last line. Lines must be string literals. Set the voice per video:
`"voice": {"engine": "kokoro", "id": "am_fenrir", "speed": 1.05}` for drafts (local,
Apache-2.0, ~1x realtime; `~/.local/share/promo-video/tts/`), or `"engine": "elevenlabs"`
for finals (key file `~/.config/promo-video/elevenlabs.key`; better intonation). Write
lines for someone who has never seen the site, and check every claim against the page.

**Kokoro reads flat, and listeners hear it: "no question tone".** Measured on one hook
line, Kokoro's pitch *fell* 32% on "…ready to ship it?", while four ElevenLabs v3 voices
rose 25–44%. So use ElevenLabs (`"model": "eleven_v3"`) for anything shipped, and steer
delivery with inline tags: `d.say("[curious] Think you can…? [confident] Prove it.")`. The
tags are stripped from captions (and from Kokoro's input). Check the account's plan
before a commercial use: as understood here (not verified), the free tier doesn't
include a commercial licence.

## Sound

Sound is optional per video; decide it in the interview. **Every effect is tied to
something visibly moving and starts when the motion starts.** Viewers hear every
mismatch: a "pop" under a fade, a whoosh that started after the camera move it belonged
to, a "boom" nothing on screen explained. So:

- click → every click
- whoosh, as long as the move → every scroll that travels, and every *sliding* transition
  from its first frame
- nothing → fades
- pop → a card's `pops` (the logo popping in)
- accent → only if the spec names a sample; there is no default boom

**Music follows the subject, not the medium.** "Modern tech launch" music under a
cooking site was "very off". Match the domain's own register (for cooking,
warm acoustic). The music ducks ~10 dB under narration, and the mix is
loudness-normalized to −16 LUFS. A CC0/free-licence kit lives
at `~/.local/share/promo-video/sound-kit/` with `SOURCES.tsv` recording each file's
licence. **For anything published under someone's name, a licence must allow commercial use.**
Read the licence itself, not a summary of it, before the video ships.

## 4. Build and look

```bash
bash <this-skill-dir>/engine/build.sh <promo-dir> <video> [--reuse]
```

It prints the mp4 and a contact sheet. **Read the sheet**, and pull extra frames around
any beat in question (`engine/sheet.sh <clip.mp4>` gives eight timestamped frames of any
clip, e.g. `out/<scene>/framed.mp4` in the cache dir).

**Before scripting, scout.** Send one reader agent per audience to find interactions that
look good in motion, each reporting ranked beats with *verified* selectors and screenshots,
and ask whoever built the site what is finished, what is buggy and what is about to change.
The pages that look best are usually in an applied state (a filter chosen, items added,
settings saved), which a plain page survey never reaches. `--reuse` re-edits without re-capturing. A sheet cannot show motion
or sound, so say so when handing over, and ask the owner to watch for the things a still
frame hides.

## Traps, each hit once already

Cursor positioning, off-screen clicks, post-deploy slowness, client-side routing, "loading…" states,
CSP-blocked wait predicates, and the CDP-vs-recordVideo/playwright-recast comparison are all in
`references/traps.md` — read it before scripting a scene, since most of these look like a normal bug
rather than a filming defect until you already know the shape.
