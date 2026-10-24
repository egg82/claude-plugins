# Part 3 — scripted edits that silently did not apply (from `assert-scripted-edits`)

Part 3 of the [instrument-failure case files](../instrument-failures.md). Load it when an edit is
made by script, `sed`, a parser round-trip or a framework write API, when a read-back of an edit
returns zero, or when a probe script might be reading a different checkout. The last case, a port
forward distorting latency, sits here by origin; it is a measurement-path failure like those in
[wrong-instrument.md](wrong-instrument.md).

**A non-unique anchor takes the first match, not the right one.** `replace(old, new, 1)` silently
took the FIRST match: a module had two same-named methods on different classes, and six new
properties I wrote landed on the wrong one. I had written the uniqueness assert as `>= 1` by hand
while composing the very edit it existed to protect, which made it decoration — only the feature's
own arithmetic tests found the misplacement, because nothing checks placement.

**A substring anchor passes while the insert lands at the wrong nesting level.** A shorter-indented
anchor **is a substring** of a longer-indented line, so `assert old in s` passed even though the
match was not the occurrence I meant. I had retyped an anchor from output that had gone through
`sed 's/^/  /'`, used 4 spaces where the file had 2, and produced invalid YAML. Deriving the anchor
from the file itself, rather than from displayed output, is what would have caught it.

**Two ways a scripted edit silently did nothing, in one session.** A multi-line replacement stopped
matching because an earlier edit had rewrapped the target lines, so a filter-state block was never
added and the page threw at runtime. Separately, a `sed` fix for a typo spanning a newline quietly
did nothing — `sed` cannot match across a newline at all — so the typo shipped and I only "re-fixed"
it later. Both cost far more than an assert on the match would have.

**A framework's write API can return failure instead of raising it.** `$shift->save()` in
Laravel returns `false` when a model event vetoes the write, with no exception and no output, so a
loop printing `"moved X"` after calling it reports success for writes that never happened. I moved a
batch of shifts to the following week in a staff-rota app and one silently stayed put, found only an
hour later when I re-listed the week — the script's own output had said the move worked.

**A hand-written config block can be wrong in ways a schema-read misses.** Writing a block by hand, I
invented five things at once — two keys absent from the model, a third with the wrong name, and two
values outside a `Literal`. One `model_validate` run inside the deployed image caught all five before
a build, cheaper than any manual review and strictly better than reading the schema, which is how I
produced the five mistakes in the first place. The loader was strict on purpose: that project had
adopted `extra: "forbid"` after a silently-ignored key cost it a batch of recorded decisions.

**A confirmation printed before the durable write is a claim about intent, not about state.** An
earlier version of the `rep()` helper accumulated into a module-level `s` and left the caller to
write once at the end. An assertion in the LAST replacement therefore discarded every earlier one,
while their `ok:` lines were already on screen: three replacements printed `ok:`, the fourth raised,
the write never ran, and the file had none of the four. The transcript said the edit succeeded and
the file disagreed. Reading and writing the file on every call also keeps anchors valid against the
*current* file, which is what the re-derive rule already asks for.

**The displayed output you type an anchor from is usually your own, stripped.** The idiom for showing
numbered source — `sed -n 'a,bp' f | awk '{printf "%d\t%s\n", N+NR, substr($0, index($0,$2))}'` —
drops field 1, which strips the leading whitespace off every line. Anchors typed from it are wrong by
however much the file was indented; it cost two round trips in one session, 4-vs-2 and 6-vs-4 spaces.
`cat -n`, or `cat -A` when the whitespace is the thing you are about to depend on. Deliberately NOT
gated: the `assert` fired loudly and immediately both times, at the cost of one retry, so the trap is
self-limiting — and a hook on `index($0,$2)` would fire on legitimate field-stripping, which is how a
gate gets switched off.

**A line-oriented read-back reports a false zero on a multi-line edit.** Verifying an applied edit
with `grep -c` returns 0 for text that is present, because the phrase wraps in the file. Caught live:
two phrases just written both reported 0, three paragraphs above the sentence explaining why. The
false zero does not read as a broken probe — it reads as *the edit did not land*, so the indicated
fix is to apply it again, producing the duplicate the read-back existed to catch.

**And the FIX for that has the same failure, which is why this needs a control rather than a better
idiom.** The prescribed replacement is to flatten the file — `re.sub(r"\s+", " ", s).count(phrase)`.
On a YAML **comment** block that is still wrong: flattening whitespace leaves the `#` sitting
mid-phrase, so a phrase that plainly exists in the file counts 0. Measured while verifying a rewritten
comment block: `grep -c` false-zeroed twice, then the flatten false-zeroed on three separate phrases
at once — and *three zeroes agreeing* is what made it briefly convincing that content was missing.
Strip the line prefix before flattening (`re.sub(r"(?m)^\s*#\s?", "", s)`), and generalise it: `>` in
quoted mail, `+`/`-` in a diff, a timestamp in a log.

The transferable part is not the regex. **Both spellings of this probe fail toward zero, so a zero
can never distinguish "absent" from "my instrument is broken."** The only thing that separates them
is a control — count a phrase you already know wraps in that file, and treat a 0 there as a verdict
on the probe. That is what caught it on the third attempt; nothing about the second attempt looked
wrong.

**A parser round-trip applies your change and reflows everything else.** Adding eight entries to a
YAML data file through `yaml.safe_dump` produced **2088 insertions and 1368 deletions**; the same
change written as a text edit was **412 and 9**. Nothing was wrong with the content — but the file
was in git specifically so a change to it could be reviewed, and a whole-file reflow buries the two
lines that matter among 1300 that did not.

**A fake engine confirms whatever you already believe, because it encodes the semantics in doubt.**
Reasoning about a migration's increment logic, a peer stood up the real thing instead — podman plus a
registry pull-through, every migration applied, then the six behaviours that mattered executed
against it: first observation, a later round incrementing, a same-day re-run NOT incrementing, a
backdated round neither incrementing nor rewinding, a human decision surviving the counter moving,
and a pre-migration row starting from 1. Kept afterwards as gated tests. A schema-valid `case`
expression, merge condition or window function can still decide the wrong thing, and a hand-written
double cannot disagree with you about it.

**`python <file>` and `python - <<EOF` resolve imports differently, so a scratchpad script edited the
wrong checkout.** Working in a `git worktree` with the venv symlinked from the main clone, a scripted
rename of 19 keyword arguments — driven by `import app.models` to learn which names were models —
applied **12 and silently skipped 7**. The assert at the bottom (`total >= 19`) is the only reason it
surfaced at all.

The cause: **`python /path/to/script.py` puts THE SCRIPT'S OWN directory on `sys.path[0]`**, not the
working directory. The script lived in a scratchpad, so the import fell through to the editable
install and loaded the **other checkout's** copy — the pre-rewrite models. The identical code pasted
as a heredoc works, because `python -` puts `''` (the cwd) there instead. Proven by printing
`sys.path[0]` and `M.__file__` under both invocations side by side.

**The shape is what earns it a case file: it applied to exactly the subset of models whose names
existed in BOTH versions.** The names present before the rewrite were renamed correctly; the ones the
rewrite had introduced were skipped. So the output was a coherent-looking partial success, every line
it printed was true, and nothing errored.

**And the control did not catch it, because the control was almost the right check.** The script
asserted `len(models) > 30`, which proves *a* models module imported, not *the* one. The correct
control is one line, and it asserts identity rather than plausibility:

```python
assert pathlib.Path(M.__file__).resolve().is_relative_to(pathlib.Path.cwd().resolve()), \
    "reading %s, not this worktree" % M.__file__
```

Generalises past Python: **whenever two checkouts of one project exist on a machine — a worktree, a
second clone, an editable install — which one a tool is reading is a fact to verify, not to assume.**
Same family as the rule that a tool you have is not a tool the thing running your code has; this is
that pointed at a *path* rather than at an environment.

**The explicit-path variant, and the tell that catches it without the control.** A scratchpad probe
written *before* the worktree existed opened with `sys.path.insert(0, "<home>/<project>")` — correct
that day, and afterwards a permanent pointer at the wrong tree. Re-run after a long pass of
deliberate renames, it printed **output byte-identical to the pre-edit run**. So take that as the
signal: **a re-run after substantive edits that has not changed AT ALL is evidence about the
instrument before it is evidence about the code — diff the two runs rather than reading the second
one.** It matters because of the direction this fails in: the probe returns *the previous answer*,
which reads as "none of your edits worked" and sends you to debug an edit that was fine. A stale
probe and a failed edit are the same observation. Cheapest fix is to stop hard-coding the tree at
all — `sys.argv[1]`, or `PYTHONPATH=.` with the probe run from the worktree.

Deliberately not gated: a command string cannot tell whether a script file imports the project it
sits beside, and a gate on "running a .py from outside cwd" would fire constantly on correct work.
Relates to Part 1's rule ([probe-rules.md](probe-rules.md)) that a cheap adjacent proxy is what a
wrong check feels like from the inside — and to `assert-scripted-edits`, whose per-label printing and
final count assert is the only reason a silent wrong edit became a visible one.

### A published podman port added a 208 ms stall that looked like the query

A performance hunt timed statements from a Python client through a rootless podman container's
published port (`-p 55462:5432`). At certain sizes every statement took ~208 ms: exactly the
"plausibly slow" number a hunt hopes for, and two candidate findings rested on it. The control
settled it: the same client and statements inside the container's network namespace
(`podman unshare nsenter -t <pid> -n`) never stalled. The port forward (pasta) stalls requests AND
responses in narrow bands about 8.4 KB apart between 8 KB and ~65 KB, and it repeats at the same
size, so **the minimum of N runs does not filter it**. A round-number size sweep landed in the bands
and read as "everything 8-65 KB is slow". It also sat under a published figure: a host-page mean of
60 ms through the port against 33 ms in the namespace, so a doc's "3.4x faster" became unproven.

**A latency taken through a forwarder measures the forwarder too.** Prefer server-side numbers
(`explain (analyze, buffers)`, `auto_explain`) or a client inside the namespace, and when a
duration is suspiciously uniform across unrelated statements, suspect the path before the query.
Same family as "a suspiciously uniform per-item value is the instrument" (`no-fabricated-certainty`).
