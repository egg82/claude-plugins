flagcheck: can this grader tell human-written short lines from model-written ones?

The writing-craft skill lets another model family screen text for LLM tells only after it
separates known-human lines from known-model lines. This measures that. Python 3.12, stdlib only.

FILES
  flagcheck.py     the instrument
  controls.jsonl   NOT SHIPPED. 60 labelled lines (30 human, 30 model); fields id, text, label, kind, source.
                   Rebuild it from the CONTROLS recipe at the bottom of this file.
  instance.json    NOT SHIPPED (machine-specific). Create it: a JSON map of provider name to the path of a
                   systemd-creds file; get_key() in flagcheck.py shows the exact lookup.

SETUP
  instance.json maps each provider to a systemd-creds file made with --name=api-key.
  The key is decrypted in-process via `sudo -n systemd-creds decrypt`; it is never in argv,
  output or the results files. Without systemd-creds, change get_key() in flagcheck.py.

RUN
  (Commands run from the skill directory, the one that holds SKILL.md.)
  Dry run (fake grader: "machine" if the line has an em dash or "not just"; no key, no network):
    python3 -I scripts/flagcheck.py scripts/controls.jsonl --dry-run --out /tmp/dry

  Live:
    python3 -I scripts/flagcheck.py scripts/controls.jsonl --grader gemini --out ~/flagcheck-gemini
    python3 -I scripts/flagcheck.py scripts/controls.jsonl --grader gemini --flatten --out ~/flagcheck-gemini-flat

  Flags: --gemini-model (default gemini-pro-latest), --openai-model (default gpt-5; openai
  grader is written but untested), --seed, --batch-size (default 20), --flatten, --grader
  repeatable. Output: <out>.jsonl (one record per grader and line) and <out>.txt (summary).

  --flatten sends every line with its first letter lowercased and final period dropped. The
  controls differ in surface form (A Dark Room's lines are lowercase and unpunctuated; most
  model lines are capitalised and end in a period), so a grader can score well on that alone.
  A grader should clear the bar with and without --flatten.

HOW IT GRADES
  Lines are shuffled by seed and cut into even batches of about 20. The grader sees only numbered
  text, never labels or ids. Each batch is sent twice, forward and reversed, to expose position
  effects. The grader returns, per line, a verdict (human or machine), a confidence 0-1, and the
  exact phrase that gives the line away (or "none"). A line the grader skips or answers invalidly
  counts as no_answer and stays out of TPR/FPR.

METRICS (labelled lines only; "unknown" lines are graded and listed but not scored)
  TPR  share of model lines called machine.
  FPR  share of human lines called machine.
  TPR - FPR  the separation. Zero is a coin flip; a grader that says "machine" to everything
       has TPR 1 and FPR 1.
  confusion  tp (model, machine), fn (model, human), fp (human, machine), tn (human, human).
  order agreement  share of lines given the same verdict forward and reversed. Low agreement
       means position effects.
  Most-quoted phrases  with how often each was quoted on human and on model lines. A phrase
       quoted on human lines is a false lead. The report also counts quoted phrases that do not
       appear verbatim in their line (the grader made them up).

THE RULE
  A grader is usable for flagging only if on these controls its TPR is well above its FPR in
  both orders (and with --flatten). Otherwise its verdicts are noise, and its quoted phrases are
  not leads. With 30 lines per side, one rate moves about 0.03 per line and its sampling error
  is around 0.09, so a gap of a few lines is not separation. Re-prove when the kind of text
  changes; these controls are terse game-UI lines.

CONTROLS
  Human (30): verbatim from published games that predate 2022. A Dark Room events/room.js and
  events/outside.js (github.com/doublespeakgames/adarkroom; both last changed 2020-05-28),
  Kittens Game res/i18n/en.json at commit e7f5df6 (2021-12-15), Universal Paperclips
  main.js and projects.js (2017, decisionproblem.com/paperclips). Candy Box 2 was not used.
  Model (30): written by Claude Sonnet for this set, for the same kinds of slot in a similar
  game, in its natural style, not disguised.
  Kinds, equal in both halves: log 8, label 8, effect 7, flavour 7.
  Median length: human 32 characters, model 35. Human lines starting lowercase: 12 of 30;
  model: 0 of 30. Ending in a period: human 3, model 22. Kittens Game flavour is jokey, the
  model flavour lines are not; that is a topic cue to watch for in the phrase table.

ADDING A GRADER
  Write make_<name>(model) returning a function Grader = Callable[[list[(int, str)]],
  dict[int, Verdict]] that sends PROMPT + numbered(items) and returns parse_results(text) of a
  JSON object {"results": [{n, verdict, confidence, phrase}, ...]}. Add the credential path to
  instance.json, the name to build_grader() and to the --grader choices.
