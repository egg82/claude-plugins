---
name: assert-scripted-edits
description: "Writes go through Write/Edit, not Bash — the auto-mode 'prefer Bash over the file tools' instruction is scoped to READS only; and where a scripted edit is genuinely right, assert every substitution landed, because one that matches nothing fails silently"
metadata:
  type: feedback
---

**The auto-mode "prefer Bash for file changes" instruction is right for reads and wrong for writes —
overridden here.** Use Write/Edit to author and edit files; Bash to read them and for bulk `cp`/`mv`.
A Bash write skips every `Write|Edit` hook, renders no diff for review, no-ops silently where Edit
fails loudly, and pushes file content through a shell string (backticks and `$(...)` inside it
execute). Enforced for memory and skill paths by `[gate:memory-write-via-bash]`.

**Edit's guarantee covers the anchor, not the replacement.** Every line inside `old_string` that you
are not deliberately changing must appear in `new_string` — otherwise it is deleted, the tool reports
success, and the diff reads as the change you meant. This shipped once: a `finish_sync_run(...)` call
vanished inside a wide anchor, the job ran fine but never recorded finishing, and 591 tests passed.
Use the smallest unique anchor; when one must span a call, grep the call count afterwards. General
form: *the work completing and the record of it completing are different events* — when a system
works but its dashboard says stale, suspect the recording.

**When a scripted edit is right** (many mechanical steps, or one edit applied across files):

```python
def rep(path, old, new, label):
    s = open(path).read()
    n = s.count(old)
    assert n == 1, "NOT UNIQUE (%d): %s" % (n, label)   # 0 catches NO MATCH too
    open(path, "w").write(s.replace(old, new, 1))
    print("  ok (written):", label)                      # printed AFTER the bytes land
```

- Re-read and write per call, `path` as an argument — accumulating into one global and writing at the
  end lets a late assert discard earlier edits whose `ok` lines already printed. A confirmation
  printed before the durable write is a claim about intent, not state.
- **The assert proves the anchor, never the edit.** Re-read the file after writing and check the NEW
  text is present — a hand-rolled version once wrote the unmodified string back, byte-identical, and
  "nothing to commit" looked like an environment problem.
- `== 1`, not `>= 1` or `in`: a shorter-indented anchor is a substring of a deeper one. Anchor on
  whole lines (include the newline); derive anchors from the file (`cat -n`/`cat -A`), never retype
  from displayed output. For anything spanning a line break use Python or Edit, never `sed`.
- A unique anchor can still be in the wrong function when siblings share a line — include an
  enclosing line, or print each changed site beside its containing function.
- Line tools can't see a phrase that wraps: verify multi-line edits against the file flattened to one
  line, strip line prefixes (`#`, `>`, diff `+`) first, and run a control phrase you know wraps —
  a false zero on a read-back reads as "didn't land" and invites a duplicate.
- A write API that **returns** a status (`$model->save()`, `bulk_update` counts, HTTP 200 with an
  error body) is the same trap: print what it returned, or re-read the record — never your intent.
- A file that exists to be diffed: edit its text, never round-trip it through a parser/formatter.
  Then load the result with the parser that consumes it; for logic (SQL, rules, DSLs) run the real
  engine — a hand-written double confirms your intent instead of checking it.
- A code snippet in an always-loaded memory is a template that gets copied: hold it to a higher bar
  than the prose.

Full reasoning: `verification-gate`'s `references/instrument-failures.md` Part 3. Relates to [[verify-dont-anchor]].
