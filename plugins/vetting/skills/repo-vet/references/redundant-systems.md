## Redundant systems -- one fact with two homes

A dead button is a claim with NO wiring; this is a claim with TWO, and both work. A sweep of
a couple of repos turned up many instances, of which **nearly all had nothing that would notice a divergence.** That
ratio is the finding; the count is not. Each addition is locally justifiable, and nothing in the moment
asks whether the fact already has a home. Pair the sweep with the doc pass -- a good share of those were prose
asserting something the code contradicted, the same defect with a sentence as the second home.

- **The write-only mirror.** A YAML file and a database table holding the same records, a loader that
  upserts on every run, and no reader on the table side. **Check the READ side -- grep for a `select`,
  not for the table name**, because a match proves a reference and not a behaviour. In the measured
  case a migration's own comment claimed the UI could join against the table and nothing ever did. Same
  shape in build config: one dependency list hand-written into `pyproject.toml`, the Dockerfile and CI,
  with a comment claiming they "float to match" and no check -- already diverged on one package.
- **A constant dressed as a variable.** A field whose type permits five values and whose data holds
  exactly one, rendered as a badge and offered as a filter. **Tests cannot catch this -- the
  computation is right and only the interpretation is false**; the instrument is comparing the field's
  DOMAIN against its actual DISTRIBUTION. Three instances in one repo, one load-bearing in a safety
  argument in a module docstring (a claim that the UI already renders it as provisional), where the rendered
  value was the model's default and every record carried it.
- **Built and never exercised** (a dead-button variant): a subsystem that works, is reachable, and has
  never run -- a UI section gated on a status no record has ever held, an import path with
  no caller, a config branch nothing selects. Latent-by-design and abandoned are indistinguishable
  from the code: in the measured sweep an auditing agent called one "a correctly-gated latent feature,
  not a miswiring" and the repo's owner called it dead weight, both defensibly. **Ask the owner, not
  the code**, and write the answer down as a comment either way.
- **Superseded, not abandoned** -- the rule stays in SKILL.md; the worked case is
  `superseded-worked-case.md`.
