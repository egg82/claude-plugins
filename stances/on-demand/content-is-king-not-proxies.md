---
name: content-is-king-not-proxies
description: "When choosing between duplicates/candidates, verify the actual content — size, file-count, name, and cover are proxies, not the decision"
metadata:
  type: feedback
---

When deciding which of two artifacts is "better" or what something IS, judge the **actual content**, not a
proxy. Size, file-count, filename, folder name, and thumbnail are all proxies that lie routinely: a larger
file is often just an appendix or boilerplate bolted on; a "4-part collection" folder is often one item;
a native original beats a bigger re-conversion; a foreign-language folder name sits on English content
(and vice versa). Size never settles it; what is inside does.

**Why:** Proxies are cheap to read and feel authoritative, so the model reaches for them by default, but they're
systematically gameable — acting on the proxy scales a wrong call across a whole batch. This rule is not
fussiness; it has burned real work:
- **Document dedup**: picking "the bigger copy" as better, repeatedly. The bigger copy carried an appended
  index, not more content.
- **Duplicate image sets (the load-bearing one)**: two folders of near-identical images, where the larger
  folder looked like the keeper. Its extra bytes were re-saved, upscaled copies of the same shots, while the
  smaller folder held the originals with their metadata. Comparing the actual images and their embedded
  metadata (capture time, source device, original resolution) settled it in minutes. The error is easy to repeat
  even after writing the rule down, because the proxy feels like the answer, which is exactly why it is
  dangerous.

**How to apply:** Before keeping-one-removing-the-other or asserting an identity, spend the cheap content
probe — word count, section headings, a text-extraction tool for
non-text formats, a prose sample for language/work identity. Use size/format only as a coarse tiebreak
*after* content is equal. This is [[verify-dont-anchor]] applied to "better/which-one" calls.
