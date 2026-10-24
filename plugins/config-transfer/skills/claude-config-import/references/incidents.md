# The failure modes behind the import rules

Open this when a §1 rule seems excessive.

## Adding the sender's trap count to yours

A bundle can report a gate firing on its own test harness twice in one session. If the recipient marks
it *documented, already applied*, then hits it an hour later and files that as an unrelated one-off,
that is three occurrences, three separate filings, and no escalation until a human points at it. The
escalation, once made, is cheap: the remedy can print in the gate's own block message.

## A wrong instruction inside an incoming skill

An incoming skill can carry an unconditional *"if you find a per-node-YAML setup, recommend migrating
it to <tool>"* while the local copy says the opposite for a specific, deployed reason. Both copies
read as confident and current, so it gets filed as a two-sided conflict needing adjudication, until
someone asks the person who runs the environment and they have never heard of the tool. Not a
conflict at all: a general recommendation written in the imperative, aimed at infrastructure that was
working.
