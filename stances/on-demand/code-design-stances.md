---
name: code-design-stances
description: "Opinionated code-design stances beyond prefer-subtraction: decoupling patterns, where the help is (often tests), no CI gates on doc wording, comments generous on APIs and minimal elsewhere"
metadata:
  type: feedback
---

Extends the code-design passage in `prefer-subtraction` (service locators, small functions, checked
types, generated files apart, no regex over prose). These are the author's preferences; delete what
doesn't match your user's.

- **Decoupling patterns earn their keep by leaving fewer places for a bug to start and making the
  ones that do get in quicker to track down.** Nystrom's *Game Programming Patterns* and the GoF are the reference,
  alongside general good practice.
- **Find where the user is weaker, and help there.** A developer strong at design and weak at tests
  gets the most from tests: blind contract tests from an agent that never read the implementation,
  property tests, and mutation runs that prove the suite can fail. Hand-built, interface-first apps are
  often the ones with none.
- **No CI gate fails on the wording of a doc** — no exceptions, however narrow the pattern looks.
  Gates check code, paths, symbols and counts; prose conventions are checked in review.
- **Comments: generous on APIs, minimal everywhere else.** API surfaces (interfaces, public
  functions, wire models) get the contract, purpose and what an implementer needs. Implementation code
  gets only the occasional "a future maintainer will want to optimize this out but shouldn't, because
  Y and Z". No decision history, no "it used to...", no story of a bug; that goes in the commit or
  decisions doc. Opus in particular over-comments, so put this rule in every writer's brief.

**Why:** preferences, not universal law; in a repo with its own conventions follow the repo
([[match-existing-house-style]]). Method, gate templates and evidence: the `agentic-engineering`
skill; load it before structuring an agent-built app or adding tests.
