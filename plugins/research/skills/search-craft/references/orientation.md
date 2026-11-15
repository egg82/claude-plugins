# Orientation: naming the authority, finding the term of art (§0, §2)

Load when you cannot yet name the governing body or the vocabulary of the thing, when the attribute you
want is rarely written down, or when you can only describe the thing (image, meme, song, gadget).

## 0. Can you name the authority?

**Ask this first; the answer decides which half of this file applies.**

*Yes, you can name the governing body / canonical doc / upstream project.* Put the name in the query
and go — you will usually be reading the real source in one step, and most of what follows is moot.

*No, you cannot.* You are in **orientation**; §2 is your section. Don't fire the specific question
yet — you don't have the words it must be asked in.

**Both routes fail, differently.** Naming from memory is fast and fails *silently* when the memory is
wrong: you search confidently for the wrong body, find something plausible, and nothing in the
process can catch it — so spend one query confirming it governs *your* case. Reconstructing
bottom-up cannot fail that way and costs roughly 30x (measured: 3 searches vs ~90 minutes).

Third trap: an authoritative source **written for a different role than yours**. Compliance guidance
may hold your answer encoded as a filing requirement. Prefer the most authoritative source *written
for someone in your position* — usually the practitioner/extension layer that exists to translate.

## 2. Aim at what is certainly documented

Pages are **bundles of attributes, not answers to questions.** When the attribute you want is rarely
written down, **add** one that always is, and collect what you wanted off the same page. A part's package type is on every distributor page; its thermal resistance often isn't.

**Add, don't substitute.** Keep the distinctive entity — it carries the discrimination that keeps you
out of the generic retail/SEO cluster. The common attribute only steers you to the right page *type*.

    ✓ Acme Zeta-9 operating temperature    (entity + certain attribute)
    ✗ industrial sensor operating temperature (attribute alone → retail listings)

**When you can only DESCRIBE the thing, search where it was USED.** An image, meme, song or gadget
you saw once: its appearance is not indexed, so description-shaped queries cannot match however many
synonyms you try. Its *context* is indexed — what it replied to, which community it circulated in.

**Ask the requester for usage context, not a better description.** "What was it a reply to?" beats
"what did it look like?". Measured on a real image hunt: twelve description-shaped queries found
nothing in ~40 minutes; one detail — *it was posted as a reply in one recurring complaint thread* —
bounded it to 298 threads and found it. Two traps hit on the way: the human was asked about art style
and platform (both worthless), and a caption that felt decisive returned zero because people post the
image **bare**, with no text to match.

**The dangerous vocabulary gap is the one that reads as ordinary English.** Jargon that *looks* like
jargon gets looked up; a term of art built from common words does not. `blast radius` parses as a
physical explosion and silently becomes a wrong model, while `idempotency-key` in the same sentence got queried
within seconds. So ask **"which ordinary-looking words here might be technical?"**

**The tell is cheap: restate the ask and diff it against the original. A detail that appears in your
restatement but not the source means you mis-parsed a term of art**, not that memory slipped. Observed:
a restatement gained "unprocessed" from reading *raw* as a property of the data — pointing at the
misread word forty minutes before it surfaced on its own.

**If you don't know the term of art, no query will work** — you cannot type a word you don't have.
Stop describing the thing and go find a **taxonomy**: a category index, spec sheet, docs table of
contents, "list of" page. Harvest the vocabulary, then search properly.
