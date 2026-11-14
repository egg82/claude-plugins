# A queue on a forge: the standard layout

On GitLab, GitHub or any forge, the queue is the forge's issues, labels and board; `docs/open-work.md`
only in a repo with no forge, and never both. A repo still on its queue file moves over with the last
section below. Use the layout below **unless the repo already has a working layout of its own** (labels, a board, a
status field people use): then follow that one and don't add a second. "Working" means in use: open
issues carry its labels, or its board has cards. An unused label set counts as nothing.

## GitLab

Scoped labels (`::`), so an issue holds exactly one state. Three families, every issue carrying one of each:

| Label | Colour | Description |
|---|---|---|
| `workflow::ready` | `#1f75cb` | Nothing stands in the way; take it from the top |
| `workflow::in progress` | `#108548` | Someone is working on it now |
| `workflow::blocked` | `#dd2b0e` | Waits on another repo, person or decision; the issue says which |
| `type::bug` | `#D9534F` | The app does something wrong |
| `type::feature` | `#428BCA` | Something the app does that it didn't |
| `type::chore` | `#8E8E8E` | Checks, releases, CI and upkeep with no change to what the app does |
| `type::docs` | `#5CB85C` | Docs only |
| `area::<part>` | `#6699CC`, all alike | Which part it touches; one per top-level part, named in the repo's own words |

`type` separates a defect from new work: a fix-history audit samples `type::bug`, and every bug's MR
lands with the test that would have caught it.

One board named **Work**, with a list per `workflow::` label in the order above; GitLab adds Open and Closed itself.

```bash
P=<project id>
glab api -X POST projects/$P/labels -f name='workflow::ready' -f color='#1f75cb' -f description='Can be worked on now'
# ... the other labels ...
B=$(glab api -X POST projects/$P/boards -f name=Work | jq .id)
glab api -X POST projects/$P/boards/$B/lists -F label_id=<id of workflow::ready>   # then in progress, blocked
```

## GitHub

GitHub labels have no scoping, so nothing stops an issue holding two states. State lives in a
**Projects** (v2) board named **Work**, in its built-in **Status** field; labels carry area and type:

| GitLab | GitHub |
|---|---|
| `workflow::ready` / `in progress` / `blocked` | Status: **Ready**, **In progress**, **Blocked**, **Done** |
| `area::<part>` | label `area: <part>` |
| `type::bug` / `feature` / `chore` / `docs` | labels `type: bug` etc., same colours |
| board "Work" | project "Work", linked to the repo, board layout grouped by Status |
| a checklist across steps | sub-issues (`addSubIssue`) |
| "Closes #n" | the same keywords, in the PR description |

```bash
# Needs the project scope once: gh auth refresh -s project   (run once by the person; it opens a browser)
gh label create "area: catalog" --color 6699cc --description "..."
N=$(gh project create --owner <owner> --title Work --format json | jq .number)
gh project link $N --owner <owner> --repo <owner>/<repo>
gh project field-list $N --owner <owner> --format json     # the Status field's id
gh api graphql -f query='mutation($f:ID!){ updateProjectV2Field(input:{fieldId:$f, singleSelectOptions:[
  {name:"Ready",color:BLUE,description:"Can be worked on now"},
  {name:"In progress",color:GREEN,description:"Someone is working on it"},
  {name:"Blocked",color:RED,description:"Waiting on something outside this repo; the issue says what"},
  {name:"Done",color:PURPLE,description:""}]}){ projectV2Field{ ... on ProjectV2SingleSelectField { options { name } } } } }' -f f=<status field id>
gh issue create --title "..." --body-file body.md --label "area: catalog" --project Work
```

- **`singleSelectOptions` REPLACES the whole option list**, so items set to an option not in the new
  list lose their Status. Set it on a fresh project, or include every option in use.
- In the project's settings (web UI only), turn on the built-in workflows "Item closed → Done",
  "Pull request merged → Done" and "Auto-add to project", so new issues land on the board.

## The issues

- **Title:** the work, as an outcome.
- **Body:** what's left (not what shipped), what's known with dates, the next concrete step, and for a
  blocked issue a closing **Blocked on:** line naming what it waits for. Work that adds a new kind of
  thing carries a **Fits into:** line naming what it extends.
- Design rules stay in `docs/decisions.md`; an issue links to the section rather than restating it.

## Working the queue

- Pick from `workflow::ready`, move the issue to `workflow::in progress`, and open an MR/PR whose
  description says `Closes #n`, so merging closes it. **Only when the MR finishes the whole issue**: an item moved
  from a queue file often lists several "left:" bullets, and `Closes` on one bullet closes them all (an issue once closed
  with its admin page unbuilt). Otherwise write `Part of #n`, and delete the shipped bullet from the issue at
  merge. Check the issue's body before writing the keyword into a writer's brief.
- An item finished outside an MR (a question answered, a decision made) gets a closing comment saying what settled it.
- Work that lands in another repo is queued there, and the issue here links to it.
- Cite an issue by number (`#4`), never a position on the board.
- `CLAUDE.md` names the board as the queue.

## Moving a queue file onto the forge

One issue per item, carrying the item's text. Label it, add it to the board, delete the file, and
repoint every doc and comment that names it (grep for the filename; a citation gate's planned-marker
list may name it too).

**Keep the file's order** when it was a priority order: the ready list sorts by manual position
(`glab issue list --order relative_position --sort asc`). **The reorder API reads backwards:**
`PUT issues/<iid>/reorder -f move_before_id=<global id of the issue that goes BEFORE this one>`
(`move_after_id` names the one that comes after). Using `move_after_id` for "put it after the previous
one" reversed a five-item queue; read the order back and compare it with the file.

- **GitLab's REST issue JSON has no `relative_position` field**, so `jq .relative_position` reads null on every issue
  whether or not positions are set. Read positions through GraphQL (`issues(sort: RELATIVE_POSITION_ASC){ nodes{ iid
  relativePosition } }`) and check they are non-null and strictly ascending. Issues created one at a time in file
  order already get ascending positions, so a fresh board needs no reorder calls.
- **Repointing citations:** the filename grep finds only citations that name the file. Bare item numbers (a systems
  inventory's "Planned" cell holding `36`, "item 34" in a plan doc, `(37)` in a comment) need their own search. Before
  mapping a number to its issue, check what item N was at the commit that wrote the citation (`git blame` the line,
  `git show <commit>:<queue file>`): a title that narrowed as work shipped is the same item; a citation of an item already
  deleted points at nothing, so drop it rather than invent a target. Applied migrations and dated audit records are
  history: leave their text alone.
