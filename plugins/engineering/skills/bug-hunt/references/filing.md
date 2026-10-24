# Filing upstream — contribution policy, commenting instead of filing, and the pre-send pass

Open this when the findings are going to **someone else's** tracker (not a repo you maintain), before
you draft anything.

## Will this project accept what you're about to write?

Read `CONTRIBUTING.md`, the issue templates, and the last twenty closed issues.

Shared policies live in the **org-level `.github` repo**, and a repo that adopted one has no
`CONTRIBUTING.md` of its own -- so checking only the repo in front of you returns a confident "no
policy found" that is simply wrong. Fetch both, explicitly:

```bash
gh api repos/<owner>/<repo>/contents/CONTRIBUTING.md --jq .content | base64 -d
gh api repos/<owner>/.github/contents/CONTRIBUTING.md --jq .content | base64 -d
```

**A 404 on the first means nothing** -- it's the normal case for an inherited policy. Conclude "no
policy" only after the *second* command returns a file you actually read. The failure is silent and
asymmetric: a false "no policy" means drafting a batch for a project that closes it on sight -- one
run reported the org repo "says nothing either way" about a project whose ban sat at line 20 of that
exact file. If neither fetch returns content, say you checked and found none -- not that none exists.

Some projects ban AI-assisted contributions outright, closing such PRs and issues "regardless of code
quality or correctness." Disclosure doesn't rescue you -- a disclosed AI-generated issue is exactly
what that policy rejects. When you find one the deliverable changes: **not a draft to file**, but a
reproduction the user can run and a diagnosis they can rewrite in their own words. Say plainly that's
why. The finding still has value -- they may want the fix for their own fork, or report it properly
themselves.

## "Declining to file" usually means COMMENTING, not dropping

A near-duplicate is the common outcome, and the right move is to add what the existing thread lacks
rather than either opening a rival issue or binning the work. Search your own prior issues too, not
just other people's — a match against something you filed yourself is still a match. Read the matched
thread to the end: the staleness that makes your new evidence worth posting is usually in the closing
comment, not the body (an old model id, a rule whose stated mechanism newer evidence disproves,
numbers from a validation that's since been superseded). A comment supplying the missing evidence and
correcting the stale detail is worth more than a new issue, and costs the maintainer one notification
instead of a triage decision.

## Before it goes out

**Cold-read it as the maintainer.** Hand the draft *and the repo* to a fresh subagent told to be the
maintainer receiving this issue -- someone who knows the code and didn't do your investigation. Ask:
is it obvious within seconds what's broken; could you act without re-deriving something the reporter
should have supplied; is anything wrong, overstated or presumptuous; what would you reply. Tell it to
be blunt -- diplomatic feedback here is worthless. This works for the same reason a fresh verifier
does: you can't see the context you left out, because you still have it. If you rewrite after the
read, read again; the check only covers the text you ship. (Worth borrowing whenever the writeup will
be read by anyone but you, even on your own repo.)

Point it at **sentences true of every issue report**, which carry no information and signal the
writeup was assembled rather than written. "This is not fixed" -- of course it isn't, that's what an
issue is. "Reported, not patched", "hope this helps", and any narration of your own reporting process
are the same family. The general tell: if a sentence would survive being pasted into an unrelated
issue, it isn't doing anything.

**Confirm with the user before any `gh`/`glab` write.** Issues are public and permanent the moment
they land, they land under the user's name, and they may want to file by hand or reword. This
confirmation is real, not ceremonial. Raise AI-disclosure as part of the same decision: default to a
brief line when the project has any stated position, since quietly omitting it there costs more than
the disclosure does. And take an explicit "just point me at it" seriously -- some people are fixing
their own bug on purpose.

```bash
gh issue create -R <owner>/<repo> -t "<title>" -F draft.md
glab issue create -t "<title>" -d "$(cat draft.md)" --yes     # GitLab: no -F
```

Filing a self-referencing batch: a bare `#N` auto-links to issue N, so cross-reference by name, or fix the numbers after the issues exist.

**Corrections after filing go in a comment, not the body.** Edit the body to stand as the current best
statement of the bug, and put what changed in a comment, where anyone who already read it will see. A
"correction to my original report" paragraph inside an edited body is incoherent to every later
reader, since the version it corrects is gone.