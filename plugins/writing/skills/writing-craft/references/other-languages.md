# Writing in other languages

Register, politeness, address and naming outside English, and what is known about LLM tells in other languages.

**Most of this skill's tells were measured on English.** The word lists, the em-dash rates, "not X but Y", the
participial tails and the reader-clue studies all come from English text. Don't translate the English list and
apply it: German uses a dash (the Gedankenstrich) as ordinary punctuation, and a Japanese sentence has no "-ing"
tail to cut. For another language, build the list by the method in `llm-tells.md` from native human text of the same
kind, and judge with native readers who use LLMs heavily.

## Register is set per market and product

Microsoft publishes a style guide for each locale, about a hundred of them, with separate guides for Spanish in
Spain, Mexico, the US and a neutral variant, for French in France and Canada, and for Portuguese in Brazil and
Portugal; each fixes address form, tone, punctuation and terms (policy,
https://learn.microsoft.com/en-us/globalization/reference/microsoft-style-guides). So the decision is per market,
and within a market per product: Zulip's German guide uses informal du for a chat product where Windows uses Sie
(practitioner, snippet, https://zulip.readthedocs.io/en/8.4/translating/german.html). Where the project has a
locale style guide, it governs; otherwise start from the vendor guide for that locale.

## Per language

These are Microsoft's product-text rules unless noted, read in full. They are a starting point for UI and
help text; fiction and marketing set their own register.

**Japanese** (policy, https://download.microsoft.com/download/8c2f9704-5bd0-4422-8d29-58afb0146545/jpn-jpn-StyleGuide.pdf)
- Body text, dialogs and messages in polite desu-masu form; requests to act as 〜してください; titles and buttons as
  noun phrases.
- No honorific (sonkeigo) or humble (kenjogo) forms in general text, and no stiff written-language vocabulary.
- **Leave the second person out.** When it's needed, name the role (ユーザー, 管理者) or use お客様 in
  customer-facing text; use あなた only after asking whether it is needed and whether it sounds rude. Translating
  every English "you" as あなた reads as translated (inference from the guide's warning).

**German** (policy, https://download.microsoft.com/download/330db0a1-dc5e-41a6-81d4-c6c97c280db4/deu-deu-StyleGuide.pdf)
- Formal Sie for adults, informal du for under-18s; address the reader as Sie and the company as wir in place of
  impersonal "Benutzer", though wir can sound odd, so check the context.
- Active voice with imperative or indicative; subjunctive and passive sound formal. "Benutzer können den Zeitpunkt
  festlegen" becomes "Sie bestimmen, wann neue Updates installiert werden sollen."
- German quotation marks „ “ and the Gedankenstrich (en dash).

**Spanish, neutral** (policy, https://download.microsoft.com/download/4/3/1/431d9836-40dc-4f2b-aafc-def5c7b5d0f3/spa-neu-StyleGuide.pdf)
- Tú or usted is decided per product; the modern voice leans to tú, with ustedes as the plural, never vosotros.
- Prefer impersonal constructions over "tú" in every sentence: "Operation failed!" becomes "No se pudo realizar la
  operación." with no exclamation.
- Keep the opening ¿ and ¡; adjectives of nationality are lower case.

**French, Chinese and others:** no style guide was read. Microsoft's guides for France and Canada exist and are the
place to start.

## Names and address

From W3C's guide to personal names (policy, https://www.w3.org/International/questions/qa-personal-names):

- **Family name first** in Japan, Korea, Hungary and China. Spanish names carry two family names, Brazilian names up
  to four, Russian names a patronymic. Many people in southern India, Malaysia and Indonesia have one name only.
- **In forms, don't require a family name** or label fields "first" and "last"; keep the case and spaces the person
  entered.
- **Address follows the culture.** Given-name address can imply acquaintance; Germans expect titles; an honorific is
  normal in Japanese; Icelanders use the given name even with strangers. Ask how the person wants to be addressed.
- A model defaults to the US pattern ("Hi [First name]", "Dear Mr. [Last name]") and splits every name in two
  (inference).

## Email across cultures

Cultural background measurably shapes what people want from email in formality, promptness, precision, and how much
is about the task versus the relationship (measured, snippet, Holtbruegge, Weldon and Rogers 2013,
https://open.fau.de/handle/openfau/4606). Earlier literature puts American and Japanese styles at opposite ends of
directness and German more direct than American; Japanese address mirrors hierarchy; American first-name use doesn't
signal intimacy (opinion, a thesis summarising others, snippet,
https://www.kuwi.europa-uni.de/de/lehrstuhl/ehemalige_professoren/sw2/forschung/tabu/weterfuehrende_informationen/studentische_arbeiten/Martina_Skalski.pdf).
The likely model failure is one warm, hedged, American template sent to everyone (judgement). Greetings and sign-offs that
`conversational-and-web-copy.md` says to drop are required in formal and much non-English email.

## LLM tells measured in other languages

Thin, and mostly invisible to readers:

- **An English accent.** LLM output in French and Chinese leans toward English vocabulary and syntax by corpus
  naturalness measures (measured, snippet, https://arxiv.org/abs/2410.15956). A native reader hears it as
  translated; fix it with a native editor or exemplars written in the language, not translated into it.
- **Chinese answers run long and narrow.** On thousands of Chinese questions, early-2023 ChatGPT answers were about
  twice as long in open and medical questions, with a smaller vocabulary than human answers (measured, snippet, HC3,
  https://arxiv.org/abs/2301.07597).
- **Japanese stylometry separates them; readers can't.** Function-word rate, comma placement right after は and
  particle sequences told GPT-3.5 and GPT-4 academic papers from human ones with over 90% accuracy, and the
  authors conclude humans cannot reliably tell (measured, Zaitsu and Jin, PLOS ONE 2023,
  https://www.ncbi.nlm.nih.gov/pmc/articles/PMC10411719/). The direction of each difference was not reported, so
  these can't become an editor's flag list.
- **Readers who see many samples do catch it, across languages.** Annotators averaged 87.6% over nine languages and
  nine domains; the widest gaps were concreteness, cultural nuance and variety (measured, snippet, Wang et al., ACL
  2026, https://aclanthology.org/2026.acl-long.639/). Concrete, locally specific detail is the fix that transfers.

## Where the evidence is thin

Three languages' product style guides were read; nothing on French, Chinese, Korean, Arabic or Hindi register.
Measured tells exist for Japanese academic text, Chinese answers and French and Chinese naturalness, none of them an
editor's list. Treat everything here as a starting point and get a native reader.
