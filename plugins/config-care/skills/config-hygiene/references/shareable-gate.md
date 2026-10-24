# Gating a copy that leaves this machine

Load before publishing a plugin or marketplace repo, or handing over a transfer bundle.

```
python3 hygiene.py shareable --share-root DIR --names A,B
```

`shareable` is the only mode aimed at a *copy* rather than at this setup: a published plugin, a repo
someone installs from, a bundle heading to another machine. Its findings are refusals, not judgment
calls — each is a failure that already shipped once.

- **A `NO-SHIP` marker**, under the frontmatter. Prose saying "don't share this" is not enforcement:
  the person packaging the copy is the one person guaranteed not to re-read the file.
- **In a copied memory pack**: a `type: user` note (the installer's agent reads it as a fact about
  *itself*), a `check:` line (arbitrary shell on someone else's machine), or a memory that is neither
  `type: user|feedback` nor carrying a `check:` — the write gate travelling in the same copy will
  refuse the very file you shipped.
- **A name**, matched as a whole word, case-insensitively, **in every file and not just the docs**.
  Anchor it: an unanchored `Ed` matches "fix**ed**", and a checker that cries wolf is one people learn
  to bypass. The non-markdown half is load-bearing — copying a skill directory takes its companion
  data with it, and a JSON file full of other people's names is the likeliest thing to leak past a
  markdown-only scan.
- **Pronoun wreckage** (`you is`, `to you instead`): the debris of generalizing a name with a blanket
  substitution. Rewrite the sentence, then grep for the debris.
- **Duplicate `^##` heading strings** — a graft bounded at one end only. Complementary to the
  `numbering` check, which keys on (level, number): there the colliding sections share a number and
  differ in title, here they share the title. Neither finds the other's case.
- **Manifest drift**, if the copy is a marketplace: `plugin.json` and `marketplace.json` must agree on
  name, version, description and keywords, and every listed plugin must exist. Someone reads the
  marketplace description while *choosing*, so a promise there is the one that actually misleads.

**Graft a function together with its wiring, in one edit.** Lifting a `def` out of a working file and
adding its registration separately manufactures a defect the source never had. Before blaming a source
you grafted from for a mode that "does nothing," run the source — a mode accepted by `choices` but
never dispatched reports nothing, which reads as clean. Not gateable — "is this graft complete" needs
the whole file's semantics — but it is one command.
