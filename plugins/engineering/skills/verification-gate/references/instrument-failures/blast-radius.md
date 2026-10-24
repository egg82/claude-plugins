# Blast radius: a fix's siblings, an addition's readers, a move's two ends

Part 1 of the [instrument-failure case files](../instrument-failures.md) (from `verify-dont-anchor`).
Load it when a fix is about to be propagated to every site a grep found, when a value set or schema
gains a member, or when something moves between homes. Every case here is a change whose correctness
was checked where it was made, and whose effect landed somewhere nobody checked — or a sweep that
condemned correct code because the grep hit looked like evidence.

### A grep for the SHAPE yields candidates, and over-correction is the likelier next mistake

After a guard of the form `if row and row[0] != digest` was fixed at one call site, grepping for its
shape found four sites and exactly one was a defect; the others rendered absence as absent, two of
them documenting why. My first discriminator was "does this guard REFUSE or REPORT" — and a peer
showed it gets four of six right and would send someone to break a *fifth* site my grep had missed
entirely, because that one spells the guard `if not row or not row[0]` and `if row and` cannot see
it. That site refuses, and skipping on absence is nonetheless correct there.

**And the tell is usually already in the function.** The one real defect had computed
`available = count(*) ... where version = previous_version` and returned early if it was zero — so
twelve lines above the guard, it had *proven the rows existed*, and then treated a missing
side-table row as "nothing to check".

So the checkable question at every hit is **does anything else in scope already establish that the
subject exists?** If yes, absence is missing evidence and must not be skipped. Triage each hit that
way before changing any of them — the fix propagating into correct code is harder to notice than the
original bug, because it looks like diligence.

### …and where that tell is absent, because the subject is REGISTRATION state

The entry above says the tell is usually already in the function. This is the class where it is not —
where the honest answer to "does anything in scope establish that the subject exists?" is **no**, and
skipping on absence is nonetheless correct.

A self-hosted app's container entrypoint seeded several files from defaults baked into the image
into its data volume on start. Some guarded on a checksum mismatch; others on `[ -e "$dest" ] ||`.
I grepped the shape, got all of them, and reported the existence-checks as defects that would strand
stale defaults across an image upgrade. A peer refuted them. One guard's destination is not a
default — it holds the instance's **registration** with an upstream push relay, a keypair the relay
has on file, and overwriting it on a registered instance makes the relay reject every notification
it sends: an outage no local check can see and that redeploying cannot fix. The guard was
load-bearing.

**Nothing in that file could have told me.** The line reads `seed /defaults/relay → /data/relay`;
the script establishes nothing about the subject; there is no twelve-lines-above proof to find. The
discriminator lived in prose elsewhere, outside the file being reviewed.

So carry a second question for this class: **does the destination hold state that a REMOTE system
also knows about** — a registration, a node identity, a licence activation, a pairing, a client
credential that was never issued? If yes, "absent" means *this instance was never registered*,
absence-means-skip is protective, and the code cannot tell you either way; the answer is in the
upstream service's or the consumer's documentation.

Note which way this one runs. I was not too credulous about a guard, I was too eager to **condemn**
one — and the shape-grep is what supplied the confidence, because a populated hit list feels like
evidence. It arrives looking like thoroughness, and what it produces is a write-up naming somebody
else's working code as broken.

### Widening a value set changes the readers you never edited

A "decided" set filtered on one value of a status column, unremarkable across three states; a fourth
state was added by a new writer. A reader phrased as "whatever is in the table" would then suppress
every item any round had ever put in that new state, and its sibling would refuse every adoption
forever. Neither reader needed an edit: correct before, correct after, wrong only relative to a
domain that moved underneath them.

What makes it worth a rule rather than a note is that **the failure renders as the designed-normal
state.** "Discovery proposed nothing this week" is the *expected* outcome most weeks in that system,
so total suppression failure and a healthy quiet week are the same observation. Nothing would have
reported it.

### A move has two ends, and checking the read side feels like checking the move

A candidates block moved out of a YAML file into a table. The readers were verified onto the table
and the deployment gated on that — and the WRITER in the same running image still appended at an
anchor defined by the block that no longer existed, so it inserted into the neighbouring section
instead and the file failed validation. Caught only because someone executed the old writer against
the new file.
