# Plain language and accessible text

Text that must work for readers with low literacy, cognitive or learning disabilities, screen-reader users,
non-native readers and machine translation. Public-sector content in the US must be written this way by law (the
Plain Writing Act of 2010), and much of it helps every reader.

**When this reader is in the audience, these rules win.** Several rules elsewhere in this skill are craft for
fiction, lore and game voice, and they become access barriers here. Decide per venue which audience governs, and
where both apply (a game's help text, a public service with a voice), give the stylish line a literal fallback.

## Where it overrides the rest of the skill

| Rule elsewhere | Plain-language rule | Source |
|---|---|---|
| Leave the last step to the reader (SKILL.md) | Say the implied thing in words. Instructions, errors and safety text state every step and consequence | policy, W3C COGA, https://www.w3.org/TR/coga-usable/ |
| A colour-coded gain, loss or state in a game or dashboard | Colour is never the only carrier of meaning; add text, shape, icon or pattern | policy, WCAG 1.4.1, below |
| Figurative lines, implied turns, wry understatement (`world-lines.md`, `humour.md`) | Literal wording. Metaphor, idiom, irony and jokes that carry meaning are barriers for people with social or communication disabilities | policy, COGA |
| Terse effect lines and unexplained mechanics (`game-ui-text.md`) | A plain explanation one tap away: a tooltip or help line that says what the thing does | opinion, inference from WCAG 3.1.5 |
| Varying the word for the same thing (good prose) | Same word for the same thing, every time: "End", never "End" here and "Terminate" there | policy, Inclusion Europe, below |
| The short everyday word (`editing-pass.md`) | The word this audience knows. Short is a proxy for familiar, and the proxy fails on rare short words | practitioner, readability critiques, below |
| Short native verbs ("look up", "carry out") | For non-native readers and translation, one single verb ("find", "do"); phrasal verbs have many meanings | opinion, global-English guides, below |

The last row is a real tension: native plain-English advice favours short phrasal verbs, global-English advice
removes them (opinion, Techscribe, via the global-English summary below). Choose by who reads most.

Models write idiom and phrasal verbs freely ("dive into", "unlock", "navigate") and rotate synonyms for one thing,
so a model draft tends to break two of these rules (judgement).

## Sentences and words

From the US federal plain-language guidelines (policy, https://digital.gov/guides/plain-language/writing):

- **Name the actor; active voice.** Address the reader as "you" and the organisation as "we" (a support agent
  replying to one person writes "I", `work-and-support-messages.md`). Passive is fine where the only actor is the
  law itself.
- **Present tense** where it is true.
- **Turn hidden verbs back into verbs.** A noun in -ment, -tion or -ance after make, take, give or have is a verb
  in disguise: "We make a decision on each claim" becomes "We decide each claim". This is the nominalisation tell
  in `llm-tells.md`.
- **Short sentences and short sections,** with a short summary at the top of anything long (policy, COGA).
- **For machine translation,** keep sentences under about 25 words, write full sentences without fragments, avoid
  chaining clauses with "which" or "although", and keep noun stacks to about three words (opinion, vendor guides
  via https://businesswritingblog.com/global-communication/plain-english-for-international-readers/).
- **Replace idiom, slang and culture-bound phrases** ("circle back") with literal wording (same source).

## Instructions, errors and numbers

- **Step-by-step instructions and specific errors that say exactly what to do** (policy, COGA). Illustration (ours,
  not W3C's): "Invalid input" becomes "Enter a date like this: 05/04/2024".
- **Explain unusual controls and what happens when you use them,** in plain words (COGA).
- **Give a words alternative to percentages and figures** where possible; some readers confuse them (COGA).
- **Keep accents and diacritics** that speech synthesis needs to pronounce a word (COGA).

## Reading level

- **WCAG asks for supplemental content when text needs more than lower-secondary reading ability** (school years 7
  to 9), setting aside names and titles: a plain summary, illustrations, a spoken version or an easier version
  (policy, WCAG 3.1.5, Level AAA, so aspirational, https://www.w3.org/WAI/WCAG21/Understanding/reading-level.html).
  It prescribes no formula; teachers can judge level against local standards.
- **A readability score is a screen, never a target.** Rewriting to lower a grade score does not raise
  comprehension, writers learn to game the score, and formulas ignore organisation, layout and whether a word is
  familiar to this audience (practitioner, snippet, Kern and Redish via Government of Canada,
  https://nos-langues.canada.ca/en/blogue-blog/readability-formulas-eng). Flesch-Kincaid is a fair coarse check on
  adult text (same source). A model can hit any score while the text stays unclear, which is the same reason this
  skill never gates prose with a regex.

## Colour

Colour must not be the only way to convey information, show an action, prompt a response or tell elements apart
(policy, WCAG 1.4.1, Level A, https://www.w3.org/WAI/WCAG21/Understanding/use-of-color.html). Fields marked
required or in error by colour alone fail; links told apart by colour alone fail; alt text that leaves out what
the colour meant fails. Green-for-valid and red-for-invalid still need a second indicator even at good contrast.
"Required fields are red" becomes a "required" label or an icon. In a game or dashboard, gains in green and losses
in red still carry a sign or word.

## Alt text

From WebAIM (practitioner, https://webaim.org/techniques/alttext/):

- **Decorative images get empty alt** (`alt=""`). Test: remove the image; if no meaning is lost, it is decorative.
- **A few words,** rarely a sentence or two. Never "image of" or "graphic of", and never a repeat of the caption or
  nearby text.
- **A linked or button image describes the destination or function** ("Search", "PDF"), never the picture. An image
  that is a link's only content must have alt text.
- **A logo is the company name,** without the word "logo".
- **Charts and maps get a short phrase saying what they are,** with the data in a nearby table or the body text.

Models tend to write long alt text that opens "An image of..." (judgement); check for it.

## Easy read and testing

- **Easy-read text is reviewed by people with intellectual disabilities.** That review is what separates real easy
  read from simplified text ("Do not write for us without us") (policy, snippet, Inclusion Europe,
  https://www.inclusion-europe.eu/easy-to-read-standards-guidelines/).
- **Testing with the audience is part of the plain-language standard** (policy, https://digital.gov/guides/plain-language).
  A model, or the writer, cannot stand in for these readers; recruit them (`judging.md`).

## Where the evidence is thin

COGA was read only in part, with its detailed language and error patterns unread; the European easy-read rules
and the formula critiques were seen only in summaries; the global-English rules come from vendor blogs. None of the
override table was tested with readers. The WCAG criteria and the federal guidelines were read in full.
