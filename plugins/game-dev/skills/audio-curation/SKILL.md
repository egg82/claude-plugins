---
name: audio-curation
description: "Choose, cut, level and place sound effects, ambience and music for an app or game when you cannot hear them. Use when picking SFX or music from packs or freesound, assigning tracks to scenes, building a listening page for a human to judge, or when a human says sounds are \"off\", on the wrong action, \"too long\" or \"sound like glass\". NOT synthesising tones or mixing music."
---

# Curating audio you cannot hear

You are deaf to the files. Everything here exists because picks made by proxy (filename, a feature
vector, a model's caption) were confidently wrong in front of the one person who could hear them.
**The human's ears are the only ground truth; your job is to put few, well-justified, comparable
candidates in front of them.** Record your own GPU and captioning-tool recipes in `~/.claude/local/audio-curation/instance.md`.

## 1. Select by what the source page says, then measure to confirm

- **A filename is what the author called a sound, not what it sounds like.** Picks made by filename
  failed the listening pass, several matched to the wrong action. Read the freesound page: description, tags, comments, rating. Prefer
  pages that state material, number of hits, mic distance and processing.
- **It is foley: the sound must read as the thing beside the picture, not be the thing** (film gravel
  is crocs on pop-rocks). Judge CHARACTER (attack, dull or ringing, number of events, length,
  texture), never source. A chocolate or celery snap can be a twig breaking; a mug set down on wood can be
  a door knock. Rejecting a candidate for its source is the wrong axis.
- **Then measure:** onset count (one hit or six?), spectral centroid (glass reads ~3,600–4,200 Hz,
  wood ~600–1,300 Hz), length. Measurement confirms the description; it never replaces it.
- **Cutting the "strongest onset" from a long take picks the loudest event, which in a paper-rustle
  recording is often a desk bump.** Check the cut's character, not just its length; ignore onsets
  within ~60 ms of each other or the cut truncates to 20 ms.

## 2. Audio-captioning models are a coarse screen, not an ear

Measured against clips a human had already judged:

- Good at **category**: applause, a chant, glass, a cow, footsteps. Use it to reject the wrong kind of
  sound before a human hears it.
- Bad at **pitch direction** (heard a falling scale as "one note"), **counts** (invents "ten
  events"), and synthetic UI sounds (a laser as "a rod striking").
- **A leading prompt poisons it**: listing materials made every caption "a hard object striking…".
  Ask neutrally; validate every new prompt on clips with known human verdicts first (`model-golf` has
  the method for grading a grader).
- Model choice mattered more than prompt: Qwen2-Audio-7B-Instruct beat Audio Flamingo 3 (HF port),
  which heard a chant as a whistle. Re-check before assuming either still holds.
- Music mood and energy ("calm night", "busy market") are category-like, so a captioner is a fair
  check on titles; pair it with measured tempo, onset rate and dynamics.

## 3. Rules that came from a human wincing

- **Celebratory sounds never fall in pitch.** A falling interval reads as failure, a lost life.
  Filter by **measured pitch slope**, not a rise/fall summary (two jingles both summarised "level"
  sloped +5.2 and −5.7). Falling is allowed only where falling means something neutral (closing).
- **A synthesised instrument out of tune is worse than none** (a detuned pluck was the one sound a listener found painful): check the pitch of
  every generated note against its target; Karplus-Strong plucks run sharp.
- **Length budget, each sound bounded by its animation:** UI under 0.3 s, a tap ~0.5 s, level-up
  ~1.5 s, ceremonies ~3 s. A sound that outlasts its animation by seconds gets cut.
- **Sci-fi UI packs sound like lasers in a fantasy world.** Exclude by pack, not by file.
- **One file per candidate.** Several sounds stitched together, or a 6-second clip of many clinks,
  cannot be judged as the one sound it would be in use.

## 4. Level before anyone compares, with a measurement that can fail

- An unlevelled preview set spanned 43 dB; quiet clips "sounded like silence" and others shouted.
  Level every candidate to a common loudness before a human listens (background ambience about
  −28 LUFS, music loops −20, stingers −18).
- **ffmpeg's `ebur128` filter printed `I: 0.0 LUFS` on every file while failing** ("Error
  reinitializing filters" further down the log), and a script applied −20 dB to everything. Measure
  with `loudnorm=print_format=json` (`input_i`, `input_tp`), reject values outside −70…0, and print the
  before and after per file so a column of identical numbers is visible.
- Level loops with a **plain gain**, never compression or `loudnorm` re-encoding, or the loop seam
  breaks; cap the gain so true peak stays under −1 dBTP.
- Slugging titles into one folder collides (a loop and a stinger both named "Victory"); keep kinds in
  separate folders and assert the output count equals the input count.

## 5. Put it in front of the human well

- A listening-room page: sections by job, 2–3 candidates per job, each labelled with its source and,
  where available, what the captioner heard, so the human can calibrate the machine too.
- Ask about what they hear, record their words verbatim beside the rule it produced (the project's
  audio doc), and re-run selection for the jobs they reject, never just swap in the next-ranked file.
- Licences: read them word for word (CC0, CC BY attribution text, paid-pack "no redistribution");
  a paid asset never goes in a public image. Sprites and other art assets follow the same
  pick-don't-make and no-public-image rules. Render the listening-room page and look at it before
  sending it (`headless-render`).
