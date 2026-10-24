# UI and microcopy

Buttons, labels, tooltips, errors, empty states, confirmations, permission prompts, onboarding and voice prompts in
a product. Game UI (effect lines, counters, waits, blocked actions, end-of-content) adds its own rules in
`game-ui-text.md`; text for low-literacy, cognitive-disability or non-native readers follows `plain-language.md`
first. Layout, colour and placement belong to `ui-craft`; this file covers the words.

A model's default UI register is the same "Something went wrong. Please try again." on every failure, a welcome
carousel, an exclamation on every empty list (judgement).

## What the style guides agree on

Read across product guides (Microsoft, Google, Chrome DevTools, GOV.UK, Grafana, Mailchimp, Atlassian, Intuit),
game guides (OpenTTD, Battle for Wesnoth) and Xbox's accessibility rules (policy, sources at the end).

- **A button names what it does:** a verb, one or two words, four at most; never "OK" when a specific word exists
  ("Delete game", "Save changes", "Create order" over "New order").
- **Drop the object the screen already names.** On a board's own page the button is "Edit", not "Edit board"; add
  the noun only when the screen holds several things the verb could act on. Models write each string as if it stood
  alone, so a redundant object noun is a model tell in UI (judgement, one reader). Where a
  screen-reader user would hear the button out of context, put the full phrase in the accessible name
  (`aria-label="Edit board"`) and keep the visible label short (policy, WCAG 2.4.6 headings and labels).
- **Sentence case everywhere;** title case only for proper names. No all-caps for emphasis, and offer sentence case
  where the design uses caps.
- **Labels and headings take no full stop** and no colon after a label.
- **A tooltip is one or two lines,** describes what happens when the option is on, and an icon button always has
  one.
- **No jokes in errors.** "If you're unsure, keep a straight face"; forced humour is worse than none.
- **A confirmation names the action and its consequence** ("Use Google's location service?" over "Are you sure?").
- **Numbers as the screen shows them,** numerals for values, amounts and percentages; avoid K/M/B unless space
  forces it ("8.21K has the same number of characters as 8,210").
- **A limit is stated plainly:** "Name must be 35 characters or less", "Shorten the filename to 64 characters or
  less". (A game may turn a cap into a consequence in its own voice; that is a voice choice, `game-ui-text.md`.)
- **Colour never carries meaning alone** (policy, WCAG 1.4.1; `plain-language.md`, colour).
- **Voice stays constant; tone moves** with the reader's state, from serious when they are upset to light when
  things go well. Get to the point and cut every excess word.

## Errors

- **Say how to fix it, not what the user did wrong.** "Enter a name", not "You didn't enter a name" or "Invalid
  filename". An empty field gets an instruction, a too-long entry a description ("Name must be 35 characters or
  less") (policy, GOV.UK, Google, DevTools).
- **Be specific; "try again" only when nothing more specific exists.** "Try reducing this file to 30 MB or less"
  over "Your file's too big". Give timing when it is known. Log error codes rather than showing them. Plain words
  at about a fifth-to-eighth-grade level (policy, Intuit, https://contentdesign.intuit.com/product-and-ui/errors/).
- **Never invent a cause.** If the cause is unknown, say something went wrong and give a next step ("Try again, or
  contact support if it keeps happening"); a plausible guess ("due to a network timeout") is a model habit (policy,
  Atlassian, https://atlassian.design/foundations/content/designing-messages/error-messages).
- **What happened, the consequence, the next step,** in one or two sentences; a title of three or four words that
  the body doesn't repeat; an imperative button, not "OK" (policy, Atlassian).
- **Match tone to severity.** Casual only for a minor slip (policy, Intuit). Whether to say "we" when the fault is
  the product's is unsettled (below).
- **"Please", "sorry", "oops" and "invalid" mostly go,** in English product UI: "sorry" makes an error sound severe
  and "please" makes a required step sound optional (policy, Atlassian, Google, GOV.UK). This does not carry to a
  support reply, where an apology with a repair works (`work-and-support-messages.md`), or to locales whose house
  style is polite by default, such as Japanese desu-masu (`other-languages.md`).

## Empty states

Three jobs (practitioner, NN/g, https://www.nngroup.com/articles/empty-state-interface-design): say what the
system is doing (no entries, or still loading), teach what belongs here and how it gets filled, and give a direct
path to the task. "Star your favorites to list them here." does all three; "No records" shown while content is
still loading does none.

- A short title, one or two sentences on why it is empty and where to go next, one primary action with a specific
  verb (policy, snippets, Atlassian and Shopify Polaris, https://polaris.shopify.com/components/empty-state).
- A completed queue can celebrate. An exclamation on every empty list ("All caught up!") is the generic version.

## Onboarding

**Tutorials for simple apps don't help.** In NN/g's test of 70 users on four iOS apps, task success was 91% for
those who read the tutorial and 94% for those who skipped it (no significant difference), and readers rated the
app harder to use (4.92 against 5.49 of 7) (measured, https://www.nngroup.com/articles/mobile-tutorials/). Spend
the words on the interface itself and on help in context, where the user is about to act. Four apps, iOS only, so
treat it as strong evidence against the welcome carousel, not against teaching a complex tool.

## Permission prompts

**One complete sentence naming what the data is used for.** Apple's guidance asks for a brief, specific purpose
string in sentence case, and App Review rejects vague ones (policy, snippet; the HIG page did not load). "Records
during the night to detect snoring sounds" is the shape; "We need access to your camera to enhance your
experience" is the generic one.

## Voice interfaces

- **Plain words and contractions; the one-breath test.** Read the line aloud; if you must pause for breath, cut.
  "I can help." over "I'd like to be able to help you"; "Ready?" over "Do you want to continue?" (policy, Alexa,
  https://developer.amazon.com/en-US/blogs/alexa/alexa-skills-kit/2019/08/five-benchmarks-for-writing-dialog-that-sounds-great-to-alexa-customers).
- **Vary what users hear every session:** two to five variants for each of the three to five prompts heard most.
  One fixed greeting per launch is the model default (judgement).
- **Don't read a menu aloud.** Say what is possible and steer toward a useful answer; long responses are hard to
  follow and remember (policy, snippet, Alexa Voice Design Guide). Writing for the ear generally is in
  `speech-and-scripts.md`.

## Length and where the eye is

- **Text on the control is the text that gets read.** During a task the eyes go to what the hand acts on next
  (measured, Land 2006,
  https://www.cis.rit.edu/pelz/scanpaths/papers/eye-movements-every-day-life-land-2006.pdf). Put the words a user
  must read on or against the control.
- **Start the line with the word that matters;** a line's first words get the most fixations (practitioner,
  https://www.nngroup.com/articles/f-shaped-pattern-reading-web-content/).
- **Blocks over two lines stay under about 80 characters wide,** and text must scale to 200% without losing content
  (policy, Xbox XAG 101). Short game-log medians are not a target for help text or body copy (`game-ui-text.md`).

## Where the guides disagree

Pick one rule per product and hold it across screens; a model left to choose per screen will drift (judgement).

- **"We" or "you" in errors:** Intuit allows "we" when the fault is ours ("We need to fix some things on our end.
  Sign out and try again later."); Atlassian's page says address the reader
  as "you"; Google says don't blame "you". Unresolved.
- **Apologies:** Atlassian, Google and Salesforce say rarely; Microsoft (snippet) allows "sorry" for a burdensome
  task or a serious consequence.
- **Small numbers in running text:** OpenTTD and Microsoft spell out one to nine; GOV.UK and DevTools always use
  numerals. All agree on numerals for values and in tight UI.
- **Contractions:** DevTools, Microsoft and Alexa use them; GOV.UK avoids negative ones (can't, don't).
- **Colons:** Wesnoth ends an instruction with one ("Choose your preferred language:"); Grafana bans them after
  labels. They describe different things, a prompt and a field label.
- **The last sentence of a tooltip:** Wesnoth drops its full stop; most guides don't say.

Sources: https://wiki.openttd.org/en/Development/Manual%20of%20style, https://wiki.wesnoth.org/UI_Style_Guide,
https://chromium.googlesource.com/devtools/devtools-frontend/+show/main/docs/styleguide/ux/writing.md,
https://design-system.service.gov.uk/components/error-message/,
https://guidance.publishing.service.gov.uk/writing-to-gov-uk-standards/style-guides/a-to-z-style-guide/,
https://learn.microsoft.com/en-us/style-guide/numbers,
https://learn.microsoft.com/en-us/style-guide/brand-voice-above-all-simple-human,
https://developers.google.com/tech-writing/error-messages/set-tone,
https://grafana.com/docs/writers-toolkit/write/style-guide/ux-writing/, https://styleguide.mailchimp.com/voice-and-tone/,
https://devdocs.xbox.com/build/game-principles/accessibility/xag-deep-dives/xag-101-text-display.md.
Not obtained: Material Design 3 and Apple HIG writing pages (JS-rendered), Podmajersky, Winters; forms, settings and
notifications have no evidence rows yet.
