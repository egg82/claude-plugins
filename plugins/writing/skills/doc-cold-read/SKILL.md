---
name: doc-cold-read
description: "Adversarially cold-read a document (README, ADR, design doc, wiki page, spec) the way a stranger will — leaked deliberation, insider shorthand, low-density prose, false claims, staleness from editing — and decide when it should be split. Use before a doc is \"done\", when reviewing someone's doc for clarity, when a doc reads like walking into the middle of a conversation, and after any burst of editing."
---

# Cold-read a doc the way a stranger will

A document's author is the worst judge of whether it stands alone: they hold all the context, so
the leaks are invisible to them. The fix is to hand the doc to readers who have *none* of that
context and watch where they stall. This is especially valuable on LLM-written docs, which tend to
read as a compression of the session that produced them rather than a record written for someone
who wasn't there.

## The method

1. **Pin the audience in one line.** Who is the intended reader and how did they arrive? (e.g.
   "an engineer joining later who needs to know what was decided and why"; "a user hitting an
   error who found this by searching"). That single line is the only context the readers get.
2. **Spawn 2-3 subagents, each given ONLY the document text + that one audience line.** Paste the
   full text into the prompt. Do **not** give them a file path or repo access — if they can roam,
   they reabsorb the missing context and the test is void. They must judge from the text alone.
3. **Give each a different lens** (below) so they don't all find the same thing.
4. **Ask each for:** a one-line verdict, the 3-6 worst spots (short exact quotes + why each
   tripped them), and what the doc does well.
5. **Synthesize.** The strong signal is **convergence**: when independent readers with no shared
   context flag the same spot or the same cut line, that's not opinion, it's reproducible.

## The lenses

- **Target reader, following it cold.** Can they come away with what they needed without
  backtracking or feeling they overheard half a conversation? Where do they stall?
- **Skeptical editor, hunting leak and over-detail.** Conversational/process residue (cross-refs,
  dates, ticket/PR numbers, status amendments, "agent" instructions), undefined jargon used before
  introduction, and dense passages where the reader wades through a lot to extract one fact. Where
  does the doc stop being what it claims to be (e.g. a decision record) and become something else
  (a build journal)?
- **Wrong-audience reader** (optional, when the doc risks attracting the wrong person). Does it
  signal who it's for fast, or will the wrong reader waste time?
- **Reader of the parts you did NOT just edit** (use after any burst of writing). Take the
  sections you did not open today and check each claim against what is true now. This lens needs
  repo access and so breaks the no-context rule above — run it yourself rather than handing it to
  a cold reader, whose whole value is not knowing.

## What it catches

- **Conversation leak** — artifacts that mean something only to people who were in the room:
  ticket/PR numbers, dated "slices," "survived N review rounds," forward-references to decisions
  that undo this one, instructions aimed at the authoring agent.
- **Insider jargon before introduction** — a name or acronym ("Fork A", an internal subsystem)
  used as if the reader already knows it.
- **Build-journal drift** — a doc that starts as a clean decision/overview and degrades into a
  status log partway down. Cold readers reliably name the exact line where it happens.
- **Conclusion-as-opening** — the doc opens on its dense summary (because the author already holds
  the context) instead of building the frame for a stranger.
- **Uniform low density** — every sentence equally elaborated, so skimming fails and the reader
  must read all of it to find the load-bearing 10%.
- **Fabricated, and never true** — distinct from stale, and caught by nothing a test can run. An
  audit of a batch of written-up explanations returned most **fabricated** or
  wrong-actor; one appeared in a page *title* (a plausible-sounding failure cause — a
  phrase with zero occurrences in the corpus it claimed to describe, and zero in the wiki). 331
  tests passed throughout and every one of them would still have passed. **A sentence asserting
  something about the world is not executed by anything**, so the only check is a reader who knows
  the domain — which is why a domain expert reading the page found in one sitting what CI could
  not find in a month. Staleness is caught by re-reading against current state; fabrication is
  caught only by someone who could contradict it. Applies equally to manifest comments and README
  claims, which are the same shape with no reviewer at all.
- **Superseded in place** — a sentence that was true when written and quietly stopped being true
  when its subject moved on. A threshold described as "deliberately uncalibrated" hours after it
  was calibrated; a handover file presenting last week's figures as current. Note the mechanism:
  it is usually a *second* copy of something already corrected elsewhere, so the correction and
  the stale text live apart and only one gets updated.

  **A wholly superseded document is harder to catch than one stale sentence, not easier**, and this
  is what makes the lens worth running deliberately. A single false line sits in text that disagrees
  with it, so there is something to snag on. A handover file whose every figure belongs to last
  week's world is *internally consistent* — the corpus size, the percentage and the failure count
  all corroborate each other, and all are wrong together. **Consistency is not evidence of
  currency**, so this one check cannot be answered from the text at all: pick the two or three
  load-bearing numbers and read them off the live system.

  A summary word can go superseded the same way a figure does. Four merge requests were handed over
  as "three cosmetic MRs and a docs split," and that adjective was the whole reason not to hold a
  deployment pin. It was fair when written and had stopped being precise by the time a fourth branch
  merged behind it — the label stayed fixed while the set it covered grew. The sentence that should
  have carried the decision was **"`module_a.py`, `module_b.py` and `schema.yaml` are
  untouched"**: same conclusion, one command to falsify, and it cannot silently acquire new members.
- **A self-describing count nothing will ever contradict** — "33 items" drifted across a
  README, a CLAUDE.md, two JSON manifests and a skill, and was wrong again within the hour because a
  note was added while the count was being corrected; "30 URLs" was dutifully corrected to "31 URLs"
  in a document whose links a reader can simply count — real verification effort spent on a fact
  with no consumer. Assume the reader can count; keep a number only where it *is* the argument, and
  keep it beside the thing it counts.
- **Duplication by adjacency** — two sections on one subject, written days apart, that do not
  contradict. Nothing flags them because nothing is wrong; the reader simply has to work out
  whether they are one topic or two. Merging usually loses nothing, because the second was written
  without re-reading the first.

**Both of the above are produced by editing**, which is why the moment to look is *just after* a
burst of writing, on the parts you did not touch — exactly when it feels least necessary, because
you have only just been over the file.

## When the answer is "this is more than one document"

A cold read assumes the unit is right and asks whether it reads well. Sometimes the unit is wrong,
and no amount of editing fixes it. **Ask this explicitly, because nothing else will prompt it:** does
this file hold sections that go stale for *different reasons*?

The tell is not length. It is a table of contents whose entries answer to different masters — some
sections that no code change could contradict, sitting beside sections that describe how a specific
module behaves today.

**Split by what would invalidate each section, never by topic.** Topic-splitting produces files that
all rot at once. Routing by invalidation puts each piece where its own subject will drag it along:

- **Nothing can contradict it** — principles, refusals, the reasons behind conventions. Stays in the
  design doc. This is the part that earns a `docs/` directory.
- **The code beside it changes** — a module's contract, a rendering rule, a caching behaviour. Move it
  next to that code. The argument is mechanical rather than aesthetic: a doc in the directory moves
  with `git mv`, appears in the diff that changes its subject, and dies when its subject dies. A
  separate `docs/` tree does none of that and rots silently. (`knowledge-routing` carries the
  principle; this is where you apply it to a doc that already exists.)
- **The list that keeps getting re-litigated** — "deliberately not built", rejected proposals — wants
  its own file. It is the content a reader most needs to find, and it is always the part buried
  deepest inside a section about something else.
- **Narration of how the doc itself changed** — "the withholding that was removed", "the non-goal was
  too broad". This is changelog wearing a design doc's clothes. Git already has it.

**Do not reach for ADRs by reflex.** They are the obvious answer and usually the wrong one here: an
ADR log is append-only and never retires, so a reader asking "why does this behave this way *now*"
has to read all of them and diff them mentally. ADRs fit where the decision *history* is the product
— an audit trail, a team that re-opens settled questions. They do not fit where the question is
"how does this thing work today".

**And say in the commit whether you are establishing a convention or following one.** A repo with one
doc has no convention, so whatever you choose becomes it; leaving that implicit makes the next person
guess, and they will guess differently.

## Acting on the findings

The cold read **points; you decide.** Readers with no context will raise some criticism that's
actually wrong — weigh each finding, don't reflexively accept or dismiss. If a reader doubts a
*fact* you can't immediately refute, go verify it against the source rather than hand-wave. The fix
for most findings is subtractive: cut the residue, move operational detail to where it belongs
(changelog/runbook), state the thing once, and lead with what-it-is-and-why.

## Relationship to other skills

This is a **standalone gate** for any finished doc, and it also decides whether the doc should be several docs — see the split section above. The `repo-readme` and
`confluence-kb-docs` skills bake a similar cold-read in as their *final authoring step* — use those
when writing a doc from scratch, and this one to audit a doc that already exists (including someone
else's). For prose that reads as model-written (a stock phrase, an appended ", and ..." beat, a
knowing aside), `writing-craft` supplies the tells list and the editing pass; this skill owns the
doc's structure and whether a stranger can follow it.
