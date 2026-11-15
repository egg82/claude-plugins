# Screenshots and recordings

Load when something a user sees changes in the PR.

For a visible change only. Real captures of the PR build, and of the base build for "before"; never
edit the DOM to stage one. Same UI state, viewport, data and theme on both sides, side by side in a
table. Use a short recording or GIF only when the change is an interaction or animation a still can't
show, and keep the stills too. Synthetic data; nothing secret in frame. `headless-render` covers
capturing on a machine with no browser. Don't commit them to the repo, and if they should exist but
couldn't be captured, say what is missing.

**Uploading** (a filename in the body is not an image):

- **GitLab** (checked with glab 1.112): `glab api --method POST "projects/:id/uploads" --form
  "file=@shot.png"` returns JSON whose `markdown` field is a ready `![shot](/uploads/...)` line.
- **GitHub:** `gh pr create --attach <file>` with matching `![alt](<same path>)` in the body replaces
  the path with an uploaded URL. Needs gh ≥ 2.99; check `gh pr create --help` for `--attach`. Without
  it, say the screenshots are not attached rather than listing their filenames.
