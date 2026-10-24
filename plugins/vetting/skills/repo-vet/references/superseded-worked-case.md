# Worked case: superseded-not-abandoned, and the two wrong-first diagnoses

Referenced from `SKILL.md`'s "Redundant systems" section, "Superseded, not abandoned" bullet.

A pipeline caching model-written summaries of catalogue listings decided "can these summaries be reused after this change" with a field-by-field diff
AND a stored digest of the rendered prompt. The digest covers everything the model sees; the diff
compared fields all inside that same rendered prompt — so it was not merely redundant but *worse
than* redundant. The prompt renders only some of those fields, so the diff refused to carry summaries
forward on a display-only rename, on a change to content the prompt truncates away, and on edits to
retired entries: three changes the prompt reproduces byte-identically.

- **A fossil is not usually unreachable, and that is the version that is easy to picture.** The
  first diagnosis claimed the diff "sat behind an `if system is not None` that both production call
  sites always satisfy. Dead for months." Both halves fail: the guard gated only the digest and the
  diff ran as its **sibling**, and a condition every call site satisfies makes code *reachable*, not
  dead. **Trace the fall-through, not the condition** — parse the function rather than reading
  indentation. Note the shape of the error, since it recurs: "dead code" is a more satisfying
  finding than "redundant code", so it is the one you reach for.
- **Do not retire the old mechanism on "strictly stronger" alone — check whether the new one fails
  OPEN anywhere.** The digest was read from a side table with `if row and ...`, which skips silently
  when the row is absent, and absent was an ordinary state rather than a corrupt one. So the weaker,
  over-triggering diff was simultaneously the **only** guard on that path. Both statements were true
  at once: the old mechanism was less accurate AND load-bearing. That is an ordering, not a veto — it
  could not go until the new one was made sound.
