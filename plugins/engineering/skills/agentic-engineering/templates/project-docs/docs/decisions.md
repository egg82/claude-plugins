<!-- Template. Design rules as distilled decisions, not a build journal. Delete these comments. -->
# Decisions

<!-- Optional opening: the north star / who it is for, in a short paragraph. -->
**North star: a recipe tracker that gets out of the way.** For one household cooking from a few dozen recipes; it
never asks for more than the person has.

<!-- Optional glossary: terms used across the docs, each pointing at where it is defined. -->
## Words used here

- **Pantry:** the ingredients on hand, kept by the shopping list (`docs/systems.md`, "Pricing and units").

<!-- One section per decision. Heading is the rule, stated as a claim. Body: the rule, then why, in a few lines.
A change of mind edits the section in place and leaves a dated "Superseded" note; a rejected option says why it
lost. Rules a session must obey even unread are promoted to a CLAUDE.md bullet that points back here. -->
## Estimates are ranges

Cooking times are shown as a range ("20 to 30 min"), never a single figure. Recipes vary by stove and cook; one
number reads as a promise and a miss reads as failure. The range comes from the recipe's own field, not from
parsing its text.

- **Rejected:** a per-user speed multiplier. It needed history nobody has early on and made the same recipe show
  different times to two people at one table.

## Ratings live on the cook, not the recipe

(Owner, 2026-03-02.) A rating is one person's, so it is stored per person.

**Superseded on 2026-04-10: a shared household rating was added** beside the personal one, because the pair
chose dinners together. The personal rating stays; the household figure is shown on the recipe list only.
