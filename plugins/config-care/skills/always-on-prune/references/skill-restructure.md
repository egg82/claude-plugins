# Restructuring skills — splitting one, and deduplicating across many

The skill-body rung of this skill's ladder, done as a project: a skill whose `SKILL.md` carries its own catalogue, or a
set of skills that each carry a copy of the same rule. Nothing here is a cut; everything moves, and the work is proving
that it moved.

## The target shape

- **`SKILL.md`** holds the concept, the steps, the rules that must fire every time, and a **"which reference" table**
  (the situation → the file to load). A stranger loading only `SKILL.md` can run the method and knows when to open
  each reference.
- **`references/<kind>.md`** holds one catalogue each — per-kind traps, oracles, checks, layers, anomaly classes —
  loaded only when that kind is live. Each opens with when to load it and what proves a finding of that kind.
- **`instance.md`** in `~/.claude/local/<skill-name>/` (or the skill's existing companion files) holds what goes stale when the world moves: hostnames,
  IPs, ids, counts from one run, dated incidents. The method must survive being handed to someone else.
- Mark which rules came from a real incident and which are untried practice, so a reader can weight them.
- Exemplars: `writing-craft` and `bug-hunt` (`references/oracles/`).

## Find the seam before cutting

Split only where a skill mixes **a generic method** with **a catalogue of kinds**. Length alone is not a seam: a long
skill that is one linear procedure (a sync, an import) stays whole, and so does a short focused one. A good tell is a
section the agent reads in full every time but uses one row of. Steps run on every pass stay inline even when long.

## Move, never lose

1. **Back up** every skill about to change to a dated holding directory first; the backup is what the loss check
   reads.
2. **Writers cap at 2–3**, each owning whole skills, briefed with the target shape, the exemplars, the proposed cut
   (as a proposal, not an order), and "move, never lose". Edits go through Edit/Write, never shell writes.
3. **A fresh agent runs the loss check**, never the writer: old files paragraph by paragraph against the whole new
   set, every rule, command, number and incident located or listed as missing, changed values flagged; then a cold
   read for broken references (`§4c`, "trap 5", "the method file" all go stale when content moves) and table rows
   whose file doesn't cover the row. *(incident)* On `bug-hunt` the writer's own check passed and the fresh agent
   still found seventeen dropped items. Verify the checker's claims too: one called a correct pointer a contradiction
   because it read the wrong section of the target file.
4. **Re-run the drift scanners** (`config-hygiene`'s `hygiene.py skills`) and update any known-benign rows that
   described content which has now moved.

## Deduplicating across skills

- **Pick one owner per rule** — the skill that holds its state or its incidents. Every other copy becomes a pointer
  that still states the rule in a sentence or two, so it fires when nobody opens the owner.
- **A pointer must resolve wherever the skill travels.** Before collapsing a copy in a skill that crosses a trust
  boundary (an exported set, another machine), confirm the owner exists there too; a copy that looks redundant may
  be the only one the other machine has.
- **Never cite personal memory names inside a skill that gets exported** — inline the rule, or point at another
  skill.
- An audit claim of duplication is a hypothesis: two tables can share a shape and route different things.

## Auditing many skills at once

Fan out read-only readers by cluster (engineering, meta/docs, infra, hobby), each reading its skills in full against
the exemplars and reporting four lists: split candidates with line ranges, misplaced sections, duplication with an
owner, missing cross-references. Treat line numbers and verdicts as leads to verify; fix outright defects (a stray
fence, a dangling reference, an instruction that contradicts the tool) in the same pass, and bring design calls
(merging skills, policy contradictions) to the person.
