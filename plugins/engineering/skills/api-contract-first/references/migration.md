# Migrating an API that already ships

1. **Type the endpoints that need no shape change first.** Most do not. This is the cheapest,
   highest-value half and it cannot break anything.
2. **Add the new resources alongside, and keep the old paths working**, marked deprecated, implemented
   as thin calls into the SAME internal function. Two code paths serving the same numbers is how a
   deprecation window becomes two APIs that quietly disagree.
3. **Leave the superseded blob untyped if typing it means a union of five shapes** — but exempt it from
   your schema test by PATH, never by "is deprecated", or the next untyped endpoint dodges the check by
   carrying that flag.
4. **Do not rename wire fields in the same pass.** Model the inconsistency as it is and write it down.
   Renaming under cover of adding types is how a typing pass becomes a breaking change nobody reviewed
   as one. (One app's histograms carry `count` where its bars carry `value`, for the same quantity, and
   a third model overloads `value` as a string. All three still ship.)

**The exception, and it is worth taking when it applies: an API nobody has integrated against yet is
free.** Rule 4 exists because a rename costs consumers. With no consumers it costs nothing, and the
window closes permanently the first time someone writes a client. If the repo is new, do the renames
now and do them all at once.
