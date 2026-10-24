# Grounding a verdict in your own sessions — the transcript method and its traps

Open this before grepping or reading session transcripts for whether a tool's pain is real for you.

## Your sessions

Grep the transcripts for whether this pain is real for you:
`grep -rliE "<pain-specific-terms>" ~/.claude/projects/ --include='*.jsonl'` (potentially hundreds
of session logs, one dir per project).

**Session logs are per-machine — `claude-fleet-sync` mirrors `~/.claude` config but NOT the
`projects/*.jsonl` transcripts — so a local-only grep sees one box's history.** Run the same grep over
the fleet (`for h in $HOSTS; do ssh "$h" '…'; done`) and sum; a null/low local
result is an incomplete probe, not a finding, until the other boxes are covered.

**A grep count is triage, not a verdict, for any *behavioral* pain ("do I do TDD / spec-first /
X-driven dev").** A practice can be pervasive with zero of the vocabulary you guessed, and the keyword
present without the practice. Use grep to *locate* candidate sessions, then READ a sample to confirm
the practice is really there or really absent — a count answers "is this word here," never "do I work
this way." When you read, sample two spots: the opening prompt (what a session was *for*) AND a spread
of turns from mid- and late-session, since sessions pivot — an opener says where a session started,
not where it went.

The `--include` is load-bearing: per-project `memory/*.md` files live under that same path and would
otherwise inflate the count with memory, not sessions. If "spec drift" or "skill sprawl" never shows
up across months of sessions, the tool is solving someone else's problem.

**Trap:** the skill list, CLAUDE.md, and the memory index are injected into every session as
system-reminders — so *any* term that also appears in them matches nearly every file as boilerplate.
That's the obvious generic ones ("skill", "hook", "agent") **and** pain-specific terms that happen to
live in your memory. Switching to a specific term doesn't escape the trap. Before trusting any count,
windowed-spot-check that hits are real user/assistant discussion, not the injected block:
`grep -rhoE '.{0,40}<term>.{0,40}' ~/.claude/projects/ --include='*.jsonl' | sort | uniq -c | sort -rn`
— one high-count context = injected boilerplate (discount it); many count-1 contexts = real discussion.

## If the tool targets the interaction itself

(Making conversations easier, prompting flow, context handling, "less back-and-forth".)
Keyword-presence isn't enough — you have to characterize **how the user actually chats with Claude**,
and that only comes from *reading* real sessions, not grepping them. If there are hundreds, fan out:
point a few `Explore`/`general-purpose` subagents at batches of `~/.claude/projects/*/*.jsonl` and have
them extract the interaction pattern — does the user spec upfront or iterate live, terse or detailed,
how often do they course-correct, where does the friction actually sit, what do they repeat by hand.
Then test the tool's premise against that reality: it only helps if it improves a pattern the user
*actually has*. A slick fix for back-and-forth they don't do is a skip.
