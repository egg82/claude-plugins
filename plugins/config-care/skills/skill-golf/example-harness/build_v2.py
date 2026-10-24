#!/usr/bin/env python3
"""Build search-craft-v2 = v1 verbatim + a pre-flight card at the top. One variable: placement."""
import os, re, shutil, sys

USAGE = "usage: build_v2.py SRC_SKILL_DIR DST_SKILL_DIR   (or set SRC and DST in the environment)"
SRC = os.path.expanduser(sys.argv[1] if len(sys.argv) > 2 else os.environ.get("SRC", ""))
DST = os.path.expanduser(sys.argv[2] if len(sys.argv) > 2 else os.environ.get("DST", ""))
if not SRC or not DST:
    sys.exit(USAGE)

CARD = """
## ⚡ Pre-flight — apply to EVERY query, before you press enter

Five questions. All five are restatements of rules below; none is new. If you read nothing else in
this file, read this.

1. **The title test — would a page plausibly be TITLED with these words?** If a token only describes
   your uncertainty ("also counts toward", "which is better", "does X support Y"), cut it. If it
   would appear in a page title — an identifier, a product name, a named event, an error literal —
   keep it however long the query gets. *(§1 "judge waste, not length" + §51 + §110)*

2. **Is this one question?** If the need contains "and", or two nouns you'd accept separate answers
   for, it is two queries. Split before issuing, not after it fails. *(§110)*

3. **Am I supplying a value I am trying to learn?** A query containing a candidate answer retrieves
   the pages containing it and cannot falsify it. A number is fine as a *constraint*, never as the
   *answer*. To relate two things, name both and let the corpus supply the relationship. *(§51)*

4. **Do I have the term of art yet?** If you cannot name the thing in its own vocabulary, no wording
   will work. Go find a taxonomy or category index first and harvest the words, then search. *(§2)*

5. **Am I trying to prove an absence?** You cannot search for a missing feature — nobody writes
   "this umbrella has no vent", and negation-as-a-word does not exclude. Enumerate the line or read
   the spec table instead. *(§107, extended)*

**If the results disappoint, do NOT reword first.** Read the failure shape: zero → the query;
junk → the index or your vocabulary; good pages that lack the answer → **the question**. *(§5)*

---
"""


def main():
    src_skill = os.path.join(SRC, "SKILL.md")
    s = open(src_skill).read()
    assert len(s) > 5000, "v1 SKILL.md unexpectedly short -- wrong file?"
    assert "Pre-flight" not in s, "source already has a Pre-flight card -- give it a pre-card v1"

    # anchor: insert the card immediately after the H1 title line
    m = re.search(r"^# Search craft\s*$", s, re.M)
    assert m, "NO MATCH: '# Search craft' H1 anchor not found in v1"

    head, tail = s[: m.end()], s[m.end():]
    out = head + "\n" + CARD.strip() + "\n" + tail
    assert CARD.strip() in out, "NO MATCH: card not present after insert"
    assert len(out) > len(s), "output not longer than input -- insert did nothing"

    # rename the skill in frontmatter so both can coexist and be addressed separately
    out2 = out.replace("name: search-craft\n", "name: search-craft-v2\n", 1)
    assert out2 != out, "NO MATCH: frontmatter name line 'name: search-craft'"

    if os.path.isdir(DST):
        shutil.rmtree(DST)
    os.makedirs(DST)
    for f in os.listdir(SRC):
        if f == "SKILL.md":
            continue
        srcp = os.path.join(SRC, f)
        if os.path.isfile(srcp):
            shutil.copy2(srcp, os.path.join(DST, f))
            print("  copied companion:", f)
    open(os.path.join(DST, "SKILL.md"), "w").write(out2)

    # verify the ONLY differences are the card and the name line
    v1_lines = s.splitlines()
    v2_lines = out2.splitlines()
    card_lines = CARD.strip().splitlines()
    assert len(v2_lines) == len(v1_lines) + len(card_lines) + 1, (
        f"line-count delta wrong: v1={len(v1_lines)} v2={len(v2_lines)} card={len(card_lines)}")
    print("  ok: v1 lines", len(v1_lines), "-> v2 lines", len(v2_lines))
    print("  ok: wrote", os.path.join(DST, "SKILL.md"))


if __name__ == "__main__":
    main()
