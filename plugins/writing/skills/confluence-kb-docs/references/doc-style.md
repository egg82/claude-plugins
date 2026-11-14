# Doc style traps

The audience thesis is in `SKILL.md`; these are the traps it does not cover. The first is a safety trap in
any doc with shell snippets.

## Placeholders in shell blocks

**Never put `<angle-bracket>` placeholders in a shell code block.** `<` and `>` are redirection operators anywhere in a word,
so a pasted `rm -rf /home/<user>/.thing` does not fail cleanly telling the reader to substitute. Verified three ways: with no file
named `user` in the cwd the command never runs (`bash: user: No such file or directory`); with one present it parses to
`rm -rf /home/` plus redirects; and a flag form (`cmd -u <user> -f PATTERN`) exits 0 having swallowed `-f PATTERN` into
a file named `-f` and run with the wrong argv. A doc that ships this has shipped a delete-every-home-directory command. Instead,
assign a real example value to a variable on its own line (`TARGET_USER=jdoe   # EDIT this line`), reference `"$TARGET_USER"`
afterwards, and add a guard that fails loudly (`[ -d "/home/$TARGET_USER" ] || echo STOP`); better, derive the value so nothing
needs substituting. Angle brackets are fine in prose and inside single quotes (an `awk` program), never bare in a pasted command.

## Troubleshooting page shape

Open with the symptom, bolded, ideally the exact error text a reader would search for. Offer an anchor jump to the fix at once, and
reassure on data safety in the same breath if true. Fix first, theory last: put the explanation in a "Why this happens" section at the
bottom labelled "you don't need any of this to apply the fix above". Close with a one-line summary, a "Confirm it worked" check and a short
list of near-miss error variants.

## Anti-patterns caught in review

- **Conversational leakage**: reassurances and asides that defend a design decision answer an objection the reader never raised.
- **Parenthetical asides that editorialize** explain the system's reasoning, not the reader's task.
- **A decision table whose heading contradicts its rows** ("reach for the escape hatch when" over rows of easy built-in tools).
- **One example name reused everywhere** (`dev` for every container) teaches a bad habit; name examples for their purpose.
- **Burying the must-read**: a rule that prevents a common mistake goes before the commands; people copy-paste and skip prose.
- **Don't document mechanism the user never touches**: show the command as typed, not the wrapper under it.
- Section numbers that drift when sections are reordered ("see section N").
