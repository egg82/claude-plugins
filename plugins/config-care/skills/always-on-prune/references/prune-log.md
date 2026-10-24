# The relocation log and the byte floor

Load when you are about to append to `prune-log.jsonl`, re-record the floor in `baseline.txt` (both live in `~/.claude/local/always-on-prune/`), or answer
*"was this deleted or relocated?"* about a file that got smaller. `SKILL.md` step 5 states the rule (log
every relocation in the same edit that moves the text); this is the schema and why it is shaped this way.

## Why a log at all

A prune is invisible to everything downstream: a later reader — or a sync tool — sees only that the
resident file got *smaller*, which is indistinguishable from content being lost. *(incident)* That
ambiguity has cost real work on a paired setup, where a sync read pruned memories as stale and nearly
undid the prune. One append-only line per moved chunk prevents it.

## Schema

```
{"date":"YYYY-MM-DD","source":"memory/<file>.md","destination":"skills/<skill>/references/<file>.md",
 "phrase":"<a distinctive phrase from the moved text>","why":"<one line>"}
```

**`phrase` is the load-bearing field:** it lets anyone mechanically answer *"was this deleted or
relocated?"* by grepping the destination. `baseline.txt` records the byte floor and nothing about which
text went where, so it cannot answer that question.

**The file's own header must say it is not a complete history** — records exist only from the pass that
introduced the log onward, and a relocation with no line is not evidence of a deletion. An incomplete log
that reads as authoritative is the falsely-clean failure this skill's siblings warn about.

## The floor, and one record or two

The growth ratchet (`SKILL.md` step 6) compares against a recorded byte floor. Where the floor lives in a
separate file from the log, **a prune means two appends, and the second is the one that gets forgotten** —
a setup that split them failed exactly that way, nobody updating the floor for six days while the store
grew. The better shape folds the floor into the log as a `{"type":"baseline","bytes":N}` record, so
recording a prune and re-recording the floor are one append. Record in your own `~/.claude/local/always-on-prune/instance.md` which shape your
machine uses, and whether the checker has been converged.

**Re-record the floor only after a real prune review, never to silence the ratchet.** Resetting it to
today's number launders unreviewed growth into the floor, which is the one thing the ratchet exists to
prevent. Take the number from `measure-resident-cost.py`'s printed total rather than a second counter that
can disagree with the first.
