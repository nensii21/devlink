#!/usr/bin/env python3
"""
Refuse workflows that report success without checking anything.

Four of them shipped: CI, Lint, Type Check and Security Scan were each a
`runs-on` and an `actions/checkout`, and each put a green tick on every pull
request. A reviewer reading four green ticks reasonably concludes the branch
builds, lints, type checks and has been scanned. None of that was true, and
nothing about the ticks said so (#1248).

A missing check is visible -- somebody notices the absence and asks. A passing
check that does nothing is the opposite: it is a positive signal, it is wrong,
and there is nothing on the pull request page that could tip anyone off.

What counts as "actually runs something": a job needs at least one step that is
not a checkout, a language setup, or a cache restore. Those three are
scaffolding -- necessary, and never the point of a workflow on their own.

Two shapes are refused outright:

* an empty workflow file (`release-drafter.yml` was zero bytes, which GitHub
  reports as a broken workflow rather than as no workflow);
* a workflow whose jobs are all scaffolding.

Two are still hollow and cannot simply be deleted -- see `KNOWN_HOLLOW`.

The other half of this script is `REQUIRED_CONTEXTS`. A job's status-check
context is its `name:`, or its id when it has none, and `main` requires seven
of them by name. Rename a job and its context stops reporting; because a
missing context is not a failing one, every pull request then waits forever on
a check that will never arrive. That is a repository-wide outage caused by a
one-word edit, so it is worth a test.

Deliberately not clever. It does not try to judge whether a step is a *good*
check, only whether one exists and still answers to the name `main` expects.
"""

from __future__ import annotations

import sys
from pathlib import Path

import yaml

WORKFLOWS = Path(".github/workflows")

#: Status-check contexts that branch protection on `main` requires.
#:
#: Mirrored here rather than read from the API because the check has to work on
#: a fork, in a pull request, without a token that can see repository rules.
#: Kept in sync by hand; `gh api repos/<owner>/<repo>/rules/branches/main` is
#: the source of truth.
#:
#: The reason this list exists at all: four of these seven belonged to
#: workflows that checked nothing, and the obvious cleanup -- delete them --
#: would have removed the contexts along with the files. A required context
#: that never reports is not a failing check, it is a pull request that can
#: never merge, for everybody, until an admin edits the ruleset.
REQUIRED_CONTEXTS = frozenset(
    {
        "backend",
        "check-star",
        "ci",
        "frontend",
        "lint",
        "security",
        "typecheck",
    }
)

#: Workflows that still check nothing, and why they are not deleted.
#:
#: Both are required contexts. Deleting either blocks every pull request in the
#: repository, so they stay until they have real content -- which for `lint`
#: means deciding what to do about 3354 pre-existing `ruff` findings and 672
#: `eslint` ones, and for `security` means #1244's dependency auditing landing
#: first. Neither is a decision that belongs in the same change as this one.
#:
#: An entry here is a debt with a name attached, not a permanent exemption.
KNOWN_HOLLOW = {
    "lint.yml": "required status check; needs a lint baseline decision (#1248)",
    "security.yml": "required status check; superseded by #1244's dependency-security.yml",
}

#: Actions that set a job up rather than check anything. Matched on the part
#: before the `@`, so version bumps do not need edits here.
SCAFFOLDING = {
    "actions/checkout",
    "actions/setup-node",
    "actions/setup-python",
    "actions/setup-java",
    "actions/setup-go",
    "actions/cache",
    "actions/cache/restore",
    "actions/download-artifact",
    "astral-sh/setup-uv",
    "pnpm/action-setup",
}


def is_scaffolding(step: dict) -> bool:
    """Whether this step only prepares the runner."""
    if "run" in step:
        return False

    uses = step.get("uses")
    if not isinstance(uses, str):
        # A step with neither `run` nor `uses` is malformed; let the caller
        # treat it as not-a-check rather than crashing here.
        return True

    return uses.split("@", 1)[0] in SCAFFOLDING


def substantive_steps(job: dict) -> int:
    steps = job.get("steps")
    if not isinstance(steps, list):
        # Reusable workflows (`uses:` at job level) delegate their steps
        # elsewhere; that is a real check, just not one defined here.
        return 1 if "uses" in job else 0

    return sum(
        1 for step in steps if isinstance(step, dict) and not is_scaffolding(step)
    )


def main() -> int:
    if not WORKFLOWS.is_dir():
        print(f"::error::{WORKFLOWS} does not exist")
        return 1

    problems: list[str] = []
    contexts: set[str] = set()
    checked = 0

    for path in sorted(WORKFLOWS.glob("*.y*ml")):
        raw = path.read_text()

        if not raw.strip():
            problems.append(
                f"{path} is empty. GitHub reports an empty workflow file as a "
                "broken workflow, not as an absent one -- delete it instead."
            )
            continue

        try:
            document = yaml.safe_load(raw)
        except yaml.YAMLError as error:
            problems.append(f"{path} is not valid YAML: {error}")
            continue

        if not isinstance(document, dict):
            problems.append(f"{path} does not parse to a mapping.")
            continue

        jobs = document.get("jobs")
        if not isinstance(jobs, dict) or not jobs:
            problems.append(f"{path} defines no jobs.")
            continue

        for name, job in jobs.items():
            if isinstance(job, dict):
                contexts.add(job.get("name") or name)

        if path.name in KNOWN_HOLLOW:
            continue

        checked += 1

        hollow = [
            name
            for name, job in jobs.items()
            if isinstance(job, dict) and substantive_steps(job) == 0
        ]
        if hollow:
            problems.append(
                f"{path}: job(s) {', '.join(sorted(hollow))} check out the "
                "repository and stop. A workflow that reports success without "
                "asserting anything is worse than no workflow -- give it a "
                "real step, or delete the file."
            )

    missing = REQUIRED_CONTEXTS - contexts
    if missing:
        problems.append(
            "no job produces the required status check(s) "
            f"{', '.join(sorted(missing))}. A job's context is its `name:`, or "
            "its id when it has none -- renaming or deleting one removes the "
            "context, and branch protection then waits forever on a check that "
            "never arrives. Restore the name, or have an admin update the "
            "ruleset first."
        )

    if problems:
        print("::error::One or more workflows do not check anything.")
        for problem in problems:
            print(f"  - {problem}")
        return 1

    known = ", ".join(sorted(KNOWN_HOLLOW))
    print(f"{checked} workflows checked; each runs at least one real step.")
    print(f"All {len(REQUIRED_CONTEXTS)} required status checks are produced.")
    if KNOWN_HOLLOW:
        print(f"Still hollow, tracked in KNOWN_HOLLOW: {known}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
