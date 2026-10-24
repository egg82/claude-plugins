# First run: the store you already have

Load on a first install, or when reorganizing a setup that has drifted into using memory as a
catch-all.

**Assume the store is already a mess.** Anyone installing this has been writing notes into the one labelled
destination for months, so the gate and the scanner only stop it getting *worse*. Clearing the backlog is a
separate, one-off pass — offer it, don't assume it.

Order matters, and every step here exists because skipping it cost something:

1. **Absorb before you delete.** If the setup is synced across machines, collect the union first —
   otherwise you sort an incomplete set and a peer reintroduces the rest. Deleting locally and syncing
   later either resurrects the file or destroys a richer copy you never read; on the run this procedure
   came from, most peer-unique files were ones already deleted on the other box, and the rest were notes
   that box had never seen.
2. **Classify by what would make each note wrong**, not by what it is about. Use the routing table in
   `knowledge-organization.md`. Expect the answer to be "not memory" far more often than feels
   right.
3. **Verify coverage by concept before deleting anything.** Search for the *idea*, not a phrase — a grep
   for one wording returns zero against a note that says the same thing differently. And make the probe
   prove it can return non-zero before you believe a zero; a zero from a probe you wrote is a fact about
   your probe.
4. **Route, then delete. Don't leave both copies.** Two homes for one fact is worse than the original mess,
   because now they diverge silently. **Delete dead things outright:** anything describing a system that
   was removed or replaced is worse than nothing. Check the claim against reality before preserving it —
   completed migrations and finished projects are the most common finds. **Salvage narrowly:** a large
   memory usually yields two or three durable facts and a lot of journal. Move the facts; drop the
   narrative.
5. **Re-point what pointed at it.** Deleting a note leaves dangling `[[links]]` in the notes and skills that
   referenced it. Run `refs` after every batch. Committed files that reference agent-local memory by name
   are unresolvable to anyone else, including a fresh clone.
6. **Propagate deletions everywhere in one pass**, if synced. Union sync never deletes — anything removed
   on one host is resurrected from a peer on the next run unless removed everywhere. Batch it into a single
   remote command per host rather than a per-item loop, which both trips sshd's `MaxStartups` and reads as
   the host being down.
7. **Probe the survivors last.** Probing notes you are about to delete is wasted work — and write each
   probe **by running it**, never by reading the note. A probe derived from what a note claims tests your
   assumption, not the system.

**The two things that will surprise you.** First, most of what looks like memory is *method* — it belongs
in a skill, and the tell is that you cannot write a falsifying command for it. Second, **deletion is the
main event.** Expect the store to shrink substantially rather than be rewritten; a note describing
something that was removed or replaced is strictly worse than no note.

**A pass like this is judgement-heavy, so give it room.** It is dominated by *reading*, and quality drops
sharply once context runs short — do it across several focused sessions rather than one long one, and keep
a running list of what is left so the next session starts oriented instead of re-deriving.
