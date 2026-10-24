# Briefing a READER child — research, review, audit

Load before briefing a child whose job is to find things out: research, a review, an audit, a sweep.
`SKILL.md` §2 lists the one-line rules; this is the detail. Research children should also be told to
load `search-craft` before their first web search.

**A read-only agent needs a findings path too, and "read only" is how you forget to give it one.**
*(incident)* Three review agents were briefed with *"Read only. Do not edit anything, and do not write
files anywhere"* — a sensible-looking instruction for an auditor, and it deleted the one mechanism that
would have preserved their work. Two of the three were then killed by a usage limit and left nothing at
all; the third had finished and its report survived only because it returned in time. Two full audit
passes had to be abandoned. The instruction you want is narrower than the one that comes to mind:
**read-only with respect to the subject, writable with respect to its own findings.** Name the findings
path and carve it out of the prohibition, e.g. *"do not modify anything under `<subject>`; append your
findings to `<scratch>/<area>-findings.jsonl` as you go"* — data-shaped, for the filename reason in
`SKILL.md` §4. A reviewer that cannot write is a reviewer whose work is only as durable as its last turn.

**State the budget as a number.** "Be thorough" has no upper bound and will be interpreted generously.
`~12 searches and ~10 fetches, then report with what you have` is a constraint an agent can satisfy.

**Say what to do when the answer isn't there.** Without it, an agent treats a null as a failure and keeps
going. *"A well-supported null is a valid answer — report it rather than padding"* prevents a long tail of
increasingly desperate queries.

**Give each agent its own scratch namespace, not just its own final output path.** Siblings pointed at
one shared directory independently reach for the same obvious names. *(incident)* Two miners on the same
run both wrote `scan.py` and `out2.txt`, and one clobbered the other's script *mid-execution*. The final
reports were uniquely named, so nothing in the brief looked wrong; only the working files collided. Hand
each agent a subdirectory, or tell it to prefix every scratch file with its source id. (Writers collide
the same way on databases: `brief-writers.md`.)
