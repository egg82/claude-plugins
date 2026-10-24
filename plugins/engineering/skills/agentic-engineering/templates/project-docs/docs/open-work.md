<!-- Template. The queue, kept true: swept against the code for done or never-built claims. Delete these comments. -->
# Open work

<!-- Opening: ordering rule and deletion rule. Any standing coordination rules (agent slots, who pushes when) go here. -->
The queue, top first. Delete an item when it ships; design rules live in `decisions.md`.

<!-- Items are numbered, bold lead-in naming the work. Then: what is left (not what shipped), what it waits on,
and for anything that adds a new kind of thing a "Fits into:" line naming the systems.md row it extends, or why
none fits. Sub-bullets for sub-steps. Blocked work says what blocks it and who unblocks it. -->
1. **Shopping list merges duplicate ingredients.** Two recipes both asking for "onion" show two lines; sum them
   when units convert. Left: the merge rule for incompatible units (cups against grams).
   - Fits into: Unit conversion (`systems.md`); the list calls `to_grams` instead of its own table, which removes
     that row's duplicate.
2. **Import from a recipe site.** Waits on the user choosing the first site to support. A new importer per site is
   a new kind of thing, so: Fits into: nothing in `systems.md` (no row owns parsing outside text); a "Recipe
   source" row is added with a Null Object that imports nothing.
3. **Backup restore test.** Dump exists; a restore into a scratch database has never been run.

<!-- Reference rows an agent needs and cannot derive: repo, CI, live site, canvases, downloads outside the repo. -->
## Where things are

| What | Where |
|---|---|
| Repo, CI | `example/recipes` on the git host; pipeline and deploy in `docs/engineering.md` |
| Live site | https://recipes.example.test (deploy config in the cluster repo) |
