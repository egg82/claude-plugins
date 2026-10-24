---
name: bootc-version-scan
description: Scan git repos for PINNED dependency versions that have drifted behind upstream — container base images (bootc/Dockerfile FROM refs), kernel package pins, ARG *_VERSION tool pins, Ansible Galaxy collections + roles, and role-var tool versions — check each against its upstream latest, and push anything behind to a webhook. Use to check for available updates to a container image stack or provisioning repo, or as a scheduled update-notifier. Reports; does not edit the repos.
---

# Pinned-version drift scan

Find pinned versions that have a newer upstream release, and notify if any are behind. The `bootcver.py` helper does the mechanical parts (git hygiene, pin extraction, webhook push); **you** resolve each pin's upstream, fetch the latest, compare, and decide what's worth flagging.

Only **pinned** versions are checkable. A dependency fetched at `releases/latest`, `HEAD`, or `main` self-updates on every build — there is no "current version" to compare, so it is *undecidable* rather than up-to-date, and `scan` drops those pins rather than reporting them green. This is a *notifier*, not Renovate: it reports and pushes a message, it does **not** edit the repos or open MRs.

## Configuration (do this first)

`REPOS` in `bootcver.py` ships as **placeholders**. Point it at real checkouts either by editing that dict, or per run:

```bash
export PINSCAN_REPOS="images=~/path/to/image-repo,provisioning=~/path/to/ansible-repo"
# or, equivalently, on each invocation (the flag goes BEFORE the subcommand):
python3 bootcver.py --repo images=~/path/to/image-repo scan
```

Other env knobs: `PINSCAN_BRANCH` (default branch to sync to, default `main`), `PINSCAN_INTERNAL_REGISTRIES` (comma-separated registry hosts to ignore — an image *you* build has no upstream release to compare against), `PINSCAN_WEBHOOK` + `PINSCAN_WEBHOOK_FIELD` (notification target; the field defaults to `text`, some chat webhooks want `content`).

## 0. Always start on the default branch + pull (this touches git repos)

```bash
python3 bootcver.py sync
```
Puts each configured repo on its default branch and fast-forward-pulls. A **dirty** repo is left untouched — it won't pull over local work; note it and scan what's there. A *failed* pull is reported loudly on stderr, because scanning a stale checkout otherwise reports identically to an up-to-date one.

## 1. Extract the pins

```bash
python3 bootcver.py scan
```
Returns JSON in three groups:
- **containerfiles** — from every `Containerfile*`/`Dockerfile*` in the configured repos: `base-image` (`ref`, e.g. `<registry>/<org>/<image>:9.8`), `kernel` (an `ARG` whose name contains `KERNEL`), and `github-or-other` (any other `ARG *_VERSION`, with `github_candidates` = every `github.com/owner/repo` URL in that file — a hint, not gospel).
- **requirements** — `galaxy-collection` / `galaxy-role` from a repo-root `requirements.yml`.
- **role_vars** — `<tool>_version:` pins from Ansible role `vars/`.

Build-time-templated refs (`${VAR}`, `__PLACEHOLDER__`), `:latest`, and multi-stage `AS` aliases are skipped — none of them name a fixed version.

## 2. Resolve each pin's upstream and check the latest

Per group (do the checks in parallel where you can; GitHub unauthenticated is 60 requests/hr, enough for this):
- **base-image** — list the registry's tags and find the newest matching stream, ignoring `latest`/floating tags. Registry tag listings: quay.io exposes `https://quay.io/api/v1/repository/<org>/<image>/tag/?limit=50`; Docker Hub `https://hub.docker.com/v2/repositories/<org>/<image>/tags?page_size=50`; anything else, `skopeo list-tags docker://<ref>`. Compare only within the same stream — a tag on a different versioning track is not "newer", it's incomparable (see below).
- **kernel** — a kernel package pin resolves against the *package repository* it comes from, not GitHub: fetch that repo's package index (e.g. an el9 RPM directory listing) and find the newest build matching the pinned flavor/suffix.
- **github ARG / role_var** — identify the repo (use `github_candidates`, or read the `releases/download/${VER}/…` URL in the same file; a role var maps to the repo used in that role's tasks). Then `https://api.github.com/repos/<owner>/<repo>/releases/latest` → `.tag_name`. **Not every `*_VERSION` is a GitHub release** — a Python tool is usually PyPI (`https://pypi.org/pypi/<name>/json` → `.info.version`), and language-ecosystem pins resolve to their own registry. Check where the artifact is actually fetched from before assuming GitHub.
- **galaxy-collection / galaxy-role** — `https://galaxy.ansible.com/api/v3/plugin/ansible/content/published/collections/index/<ns>/<name>/` for collections, or the role's Galaxy page, for the latest version.

Compare current vs latest as versions (strip a leading `v`; ignore pre-releases/rc/beta unless the pin itself is one). A pin equal-or-newer than upstream is fine. If the two values are not on the same versioning scheme — a date-based track vs a semver track, a rename of the release series — say **"cannot compare"** rather than guessing a direction; a guessed direction is worse than a reported gap.

## 3. Report + notify

Print a concise report to **stdout** always (it's the run log): each outdated pin as `name: current → latest`, and a one-line "N up to date" summary. Then, **only if something is behind**, push it:
```bash
python3 bootcver.py notify "$(printf 'pinned updates available:\n%s' '<the outdated list>')"
```
`notify` reads the URL from `$PINSCAN_WEBHOOK`; it exits non-zero and prints the message if no webhook is set. Keep the message tight (one line per outdated pin: `tool current → latest`). If nothing is behind, send nothing.

## Autonomous vs interactive

Same procedure both ways — it only pulls, reads, and notifies (no repo edits), so it's safe full-auto. In **interactive** mode, after reporting you may offer to bump the pins the human approves (edit the `ARG`/`requirements.yml`/var, and note that a real image rebuild or provisioning run is what actually applies it) — but never auto-edit on a scheduled run. Verify a flagged update is real before pushing (a mis-resolved repo or a pre-release can false-positive) — a noisy notifier gets ignored.

Bumping has traps the scan cannot see:
- **Kernel:** a kernel pin that appears in every workstation/desktop image must move in all of them together, because child images that dkms-build a GPU driver compile against the kernel-devel their parent installed. The real risk is the driver failing to compile, so run `nvidia-dkms-check.sh` (beside this file) with the current pin first as a control before bumping. Pins older than the newest few survive via the kernel repo's archive, so a stale pin is not a broken build.
- **Anything the provisioning payload references by path** (a library loaded from a fixed directory via a symlink the base image creates): grep the provisioning repo for the old version string before bumping.
- **A service whose upgrade path has required stops** (a self-hosted git forge, say): moving its version pin upgrades the live instance on the next image update and can make every older backup unrestorable. Bump only on the human's say-so, and never skip a required stop in the vendor's upgrade-path file.
- **Pulling a pushed image to inspect packages can cost 17-27 GB each**, and a workstation disk can already be nearly full. Pull one at a time and remove it immediately.
