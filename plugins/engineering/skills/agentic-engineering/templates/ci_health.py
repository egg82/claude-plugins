#!/usr/bin/env python3
"""Report a repository's CI health from its last days of runs, and keep one open issue per problem.

    python ci_health.py --repo OWNER/NAME --budget-min 10 [--days 7] [--workflow CI] [--test-jobs REGEX] [--dry-run]

Two numbers, from the pull-request runs of the last --days:
  budget  the wall clock of successful runs (created to the last job's finish), median and worst, against --budget-min
  reruns  runs with a later attempt that passed whose FIRST attempt failed a test job (a job matching --test-jobs that
          concluded `failure`: a run cancelled by a newer push or a label is not one), with the failing test ids from
          that attempt's log. A rerun that passed is a flaky test, or a test that depends on the runner.
Over budget, or any rerun: one open issue per kind (labels ci-health-budget, ci-health-reruns) is created or its body
replaced, never duplicated. Otherwise one logfmt line, exit 0. A forge error exits 1 with its message.

Standard library only, no import from the repository it runs in: copy this file. Everything that speaks to the forge is
`GitHub` below (the `gh` CLI, which needs GH_TOKEN with actions: read and issues: write); a GitLab variant implements the
same six methods over `glab api` and nothing else changes. A run that did not finish has no wall clock and is skipped.
"""
import argparse
import json
import re
import statistics
import subprocess
import sys
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Any, Callable, Protocol

KINDS = {"budget": "CI: pull requests over the wall-clock budget", "reruns": "CI: runs that failed a test job and passed on rerun"}
LABEL = "ci-health-{}"


@dataclass(frozen=True)
class Run:
    id: int
    attempt: int
    conclusion: str
    wall_min: float
    url: str


@dataclass(frozen=True)
class FailedJob:
    name: str
    url: str
    log: str


class Forge(Protocol):
    def pr_runs(self, since: datetime, workflow: str) -> list[Run]: ...
    def failed_jobs(self, run: Run, attempt: int, name: re.Pattern[str]) -> list[FailedJob]: ...
    def open_issue(self, kind: str) -> int | None: ...
    def create_issue(self, kind: str, title: str, body: str) -> int: ...
    def update_issue(self, number: int, title: str, body: str) -> None: ...
    def close_issue(self, number: int, comment: str) -> None: ...


Gh = Callable[[list[str]], str]


def gh_cli(args: list[str]) -> str:
    done = subprocess.run(["gh", *args], capture_output=True, text=True, check=False)
    if done.returncode != 0:
        sys.exit(f"gh {' '.join(args[:3])} failed: {done.stderr.strip()[-300:]}")
    return done.stdout


def parse(text: str) -> datetime:
    return datetime.fromisoformat(text.replace("Z", "+00:00"))


class GitHub:
    """The forge calls, over `gh` (replaceable by `gh` as a function for a test that serves captured responses)."""

    def __init__(self, repo: str, gh: Gh = gh_cli) -> None:
        self.repo, self.gh = repo, gh

    def lines(self, path: str, *fields: str, jq: str) -> list[dict[str, Any]]:
        out = self.gh(["api", "-X", "GET", f"repos/{self.repo}/{path}", *fields, "--paginate", "--jq", jq])
        return [json.loads(line) for line in out.splitlines() if line.strip()]

    def pr_runs(self, since: datetime, workflow: str) -> list[Run]:
        raw = self.lines("actions/runs", "-f", "event=pull_request", "-f", f"created=>={since:%Y-%m-%d}", "-f", "per_page=100",
                         jq=".workflow_runs[]")
        return [Run(r["id"], r["run_attempt"], r["conclusion"] or "", (parse(r["updated_at"]) - parse(r["created_at"])).total_seconds() / 60,
                    r["html_url"]) for r in raw
                if r["name"] == workflow and r["status"] == "completed" and parse(r["created_at"]) >= since]

    def failed_jobs(self, run: Run, attempt: int, name: re.Pattern[str]) -> list[FailedJob]:
        jobs = self.lines(f"actions/runs/{run.id}/attempts/{attempt}/jobs", jq=".jobs[]")
        return [FailedJob(j["name"], j["html_url"], self.gh(["api", "--allow-escape-sequences", f"repos/{self.repo}/actions/jobs/{j['id']}/logs"]))
                for j in jobs if j["conclusion"] == "failure" and name.search(j["name"])]

    def open_issue(self, kind: str) -> int | None:
        found = json.loads(self.gh(["issue", "list", "-R", self.repo, "--label", LABEL.format(kind), "--state", "open", "--json", "number"]))
        return int(found[0]["number"]) if found else None

    def create_issue(self, kind: str, title: str, body: str) -> int:
        self.gh(["label", "create", LABEL.format(kind), "-R", self.repo, "--force", "--description", "opened by ci_health.py"])
        url = self.gh(["issue", "create", "-R", self.repo, "--title", title, "--body", body, "--label", LABEL.format(kind)]).strip()
        return int(url.rsplit("/", 1)[-1])

    def update_issue(self, number: int, title: str, body: str) -> None:
        self.gh(["issue", "edit", str(number), "-R", self.repo, "--title", title, "--body", body])

    def close_issue(self, number: int, comment: str) -> None:
        self.gh(["issue", "close", str(number), "-R", self.repo, "--comment", comment])


def failing_tests(log: str) -> list[str]:
    """The test ids a job's log names: pytest's `FAILED <id>` and `ERROR <id>` lines (a teardown failure, the per-test
    time ceiling's among them, is an ERROR), else, for a test killed by pytest-timeout (which prints no summary), the
    last test frame in the stack it dumps after its banner."""
    found = list(dict.fromkeys(re.findall(r"\b(?:FAILED|ERROR) (\S+::\S+)", log)))
    if found or "Timeout +" not in log:
        return found
    frames = re.findall(r'/(tests/[\w/.-]+\.py)", line \d+, in (test_\w+)', log.split("Timeout +", 1)[1])
    return [f"{path}::{name} (timeout)" for path, name in frames[-1:]]


def median_worst(runs: list[Run]) -> tuple[float, float] | None:
    ok = [r.wall_min for r in runs if r.conclusion == "success"]
    return (statistics.median(ok), max(ok)) if ok else None


def reruns(forge: Forge, runs: list[Run], test_jobs: re.Pattern[str]) -> list[tuple[Run, list[FailedJob]]]:
    """Runs that passed on a later attempt, with the test jobs their first attempt failed (those with none are left out)."""
    found = [(r, forge.failed_jobs(r, 1, test_jobs)) for r in runs if r.attempt > 1 and r.conclusion == "success"]
    return [(r, jobs) for r, jobs in found if jobs]


def budget_body(stats: tuple[float, float], budget: float, days: int, runs: list[Run]) -> str:
    slow = sorted((r for r in runs if r.conclusion == "success" and r.wall_min > budget), key=lambda r: -r.wall_min)[:10]
    rows = "\n".join(f"- {r.wall_min:.0f} min: {r.url}" for r in slow)
    return (f"Pull-request runs of the last {days} days that passed: median {stats[0]:.1f} min, worst {stats[1]:.1f} min; "
            f"the budget is {budget:g} min.\n\nSlowest over it:\n{rows}\n")


def rerun_body(found: list[tuple[Run, list[FailedJob]]], days: int) -> str:
    out = [f"Pull-request runs of the last {days} days whose first attempt failed a test job and that passed on a later attempt:\n"]
    for run, jobs in found:
        out.append(f"- {run.url}")
        for job in jobs:
            ids = failing_tests(job.log)
            out.append(f"  - {job.name} ({job.url}): " + (", ".join(f"`{i}`" for i in ids) if ids else "no test id in the log"))
    return "\n".join(out) + "\n"


def upsert(forge: Forge, kind: str, body: str, dry: bool) -> str:
    if dry:
        return "dry-run"
    number = forge.open_issue(kind)
    if number is None:
        return f"created #{forge.create_issue(kind, KINDS[kind], body)}"
    forge.update_issue(number, KINDS[kind], body)
    return f"updated #{number}"


def settle(forge: Forge, kind: str, comment: str, dry: bool) -> str:
    """Close the kind's open issue once tonight shows no problem, so a cleared problem's body never reads as current."""
    number = None if dry else forge.open_issue(kind)
    if number is None:
        return ""
    forge.close_issue(number, comment)
    return f"closed #{number}"


def run(forge: Forge, budget: float, days: int, workflow: str, test_jobs: re.Pattern[str], dry: bool, now: datetime) -> int:
    runs = forge.pr_runs(now - timedelta(days=days), workflow)
    stats, found = median_worst(runs), reruns(forge, runs, test_jobs)
    actions: list[str] = []
    if stats is not None and stats[0] > budget:
        actions.append("budget " + upsert(forge, "budget", budget_body(stats, budget, days, runs), dry))
    elif stats is not None and (done := settle(forge, "budget", f"Median back to {stats[0]:.1f} min, within the {budget:g} min budget.", dry)):
        actions.append("budget " + done)
    if found:
        actions.append("reruns " + upsert(forge, "reruns", rerun_body(found, days), dry))
    elif runs and (done := settle(forge, "reruns", f"No pull-request run of the last {days} days passed only on a rerun.", dry)):
        actions.append("reruns " + done)
    median, worst = (f"{stats[0]:.1f}", f"{stats[1]:.1f}") if stats else ("unknown", "unknown")
    print(f"event=ci_health days={days} pr_runs={sum(r.conclusion == 'success' for r in runs)} median_min={median} worst_min={worst} "
          f"budget_min={budget:g} reruns_passed={len(found)} issues={';'.join(actions) or 'none'}")
    return 0


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--repo", required=True)
    ap.add_argument("--budget-min", type=float, required=True)
    ap.add_argument("--days", type=int, default=7)
    ap.add_argument("--workflow", default="CI")
    ap.add_argument("--test-jobs", default=r"^test")  # pass your own test-job names
    ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args(argv)
    return run(GitHub(a.repo), a.budget_min, a.days, a.workflow, re.compile(a.test_jobs), a.dry_run, datetime.now(timezone.utc))


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
