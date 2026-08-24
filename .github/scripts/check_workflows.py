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

`SUITES` is the same idea one level up. A workflow can run a real step and
still leave the repository's actual tests on the floor: `frontend-ci.yml`
installed, built, and compared the route tree -- three substantive steps, a
green tick, and 726 vitest tests that no workflow had ever executed (#1316).
Two ways for a suite to stop mattering, and this checks both:

* nothing invokes it, which is what happened to the frontend suite;
* something invokes it under `continue-on-error: true`, which is what still
  happens to `pytest` -- the job reports success whatever the tests say.

`KNOWN_UNGATED` is the second case with a name attached, the same way
`KNOWN_HOLLOW` is for workflows. An entry there is a debt, not an exemption,
and the script says so when one is paid off.

Deliberately not clever. It does not try to judge whether a step is a *good*
check, only whether one exists and still answers to the name `main` expects.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path
from typing import Iterator, NamedTuple

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


class Suite(NamedTuple):
    """
    A test suite the repository ships, and how to spot it being run.

    A `NamedTuple` rather than a dataclass so this module can be exec'd
    straight from its path -- which is how `tests/test_check_workflows.py`
    loads it, and how anyone poking at it from a REPL will. `@dataclass`
    resolves its annotations through `sys.modules[cls.__module__]`, which is
    `None` for a module loaded that way, and raises during class creation.
    """

    #: What to call it in an error message.
    description: str
    #: Where the suite lives, so the message points somewhere useful.
    home: str
    #: Matched against each command in the `run:` of every step.
    pattern: re.Pattern


#: Suites that must be invoked by some workflow, and must gate when they are.
#:
#: Deliberately a short hand-maintained list rather than anything that goes
#: looking. The failure this catches is a suite quietly falling out of CI, and
#: a discovery mechanism that can also miss a suite would inherit the same
#: blind spot.
#:
#: Patterns are anchored to the start of a *command*, not matched anywhere in
#: the `run:` block, because the difference matters:
#:
#:     pip install black ruff mypy pytest     <- names it, does not run it
#:     pytest                                 <- runs it
#:
#: `npm run test` is matched without a trailing `:`, so `npm run test:e2e` --
#: a different suite, needing browsers and a server -- does not satisfy this.
SUITES = {
    "frontend": Suite(
        description="frontend unit tests (vitest)",
        home="frontend/package.json -> scripts.test",
        pattern=re.compile(
            r"^(?:npx\s+)?(?:npm\s+run\s+test(?![\w:.-])|vitest(?![\w.-]))"
        ),
    ),
    "backend": Suite(
        description="backend tests (pytest)",
        home="backend/tests/ and backend/app/tests/",
        pattern=re.compile(r"^(?:[\w./-]*python[\w.]*\s+-m\s+)?pytest(?![\w.-])"),
    ),
}

#: Suites that run but do not gate, and why that is not fixed here.
#:
#: `backend-ci.yml` has carried `continue-on-error: true` on its `pytest` step
#: since the workflow was written, so the `backend` context is green whatever
#: the tests say. Taking the flag off is the right end state and is not a
#: one-line change: it turns the existing failures on `main` into a blocked
#: repository, which has to be dealt with first and separately.
#:
#: An entry here is a debt with a name attached. The script fails when a suite
#: listed here starts gating, so paying one off cannot leave the note behind.
KNOWN_UNGATED = {
    "backend": (
        "`pytest` runs in backend-ci.yml under `continue-on-error: true`; "
        "removing that needs the failing tests on `main` dealt with first"
    ),
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


#: Shell operators that end one command and begin the next, plus the newlines
#: of a `run: |` block. Splitting on these is what lets the suite patterns
#: anchor to `^` and still see the second half of `cd backend && pytest`.
_COMMAND_SEPARATOR = re.compile(r"[\n;]|&&|\|\||(?<!\|)\|(?!\|)")

#: A leading `FOO=bar ` assignment is part of the invocation, not a different
#: command. `CI=true npm run test` is running the suite.
_ENV_PREFIX = re.compile(r"^(?:\w+=\S*\s+)*")


def commands_in(run: str) -> Iterator[str]:
    """Split a `run:` block into the individual commands it executes."""
    for fragment in _COMMAND_SEPARATOR.split(run):
        command = _ENV_PREFIX.sub("", fragment.strip())
        if command:
            yield command


def iter_run_steps(document: dict) -> Iterator[tuple[str, bool]]:
    """
    Yield ``(command, gates)`` for every `run:` step in a workflow document.

    ``gates`` is False when the step or its job carries
    ``continue-on-error: true``, which makes the job report success regardless
    of what the step returned. Both levels matter: the flag is legal on either
    and means the same thing for our purposes.
    """
    jobs = document.get("jobs")
    if not isinstance(jobs, dict):
        return

    for job in jobs.values():
        if not isinstance(job, dict):
            continue

        job_gates = job.get("continue-on-error") is not True

        steps = job.get("steps")
        if not isinstance(steps, list):
            continue

        for step in steps:
            if not isinstance(step, dict):
                continue
            command = step.get("run")
            if isinstance(command, str):
                yield command, job_gates and step.get("continue-on-error") is not True


def suite_problems(invocations: dict[str, list[bool]]) -> list[str]:
    """
    Turn what was found into the complaints worth making.

    ``invocations`` maps a suite name to one entry per step that runs it, each
    saying whether that step gates. A suite is satisfied by *any* gating
    invocation -- running it twice, once under `continue-on-error`, is fine.
    """
    problems: list[str] = []

    for name, suite in SUITES.items():
        found = invocations.get(name, [])

        if not found:
            problems.append(
                f"nothing in {WORKFLOWS} runs the {suite.description}. The "
                f"suite exists ({suite.home}) and no pull request has ever "
                "been told what it thinks. A test nobody runs is worse than a "
                "test nobody wrote: it reads as coverage on the pull request "
                "page while asserting nothing."
            )
            continue

        gates = any(found)

        if not gates and name not in KNOWN_UNGATED:
            problems.append(
                f"the {suite.description} runs, but every invocation is under "
                "`continue-on-error: true`, so the job reports success "
                "whatever the tests say. Drop the flag, or add an entry to "
                "KNOWN_UNGATED saying why not."
            )
        elif gates and name in KNOWN_UNGATED:
            problems.append(
                f"the {suite.description} now gates, so its KNOWN_UNGATED "
                "entry is stale. Remove it -- a tracked debt that has been "
                "paid off is the one kind of entry that must not linger."
            )

    return problems


def main() -> int:
    if not WORKFLOWS.is_dir():
        print(f"::error::{WORKFLOWS} does not exist")
        return 1

    problems: list[str] = []
    contexts: set[str] = set()
    invocations: dict[str, list[bool]] = {}
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

        # Scanned before the KNOWN_HOLLOW skip below: a workflow excused from
        # the hollow check is still a place a suite could be run from.
        for run, gates in iter_run_steps(document):
            for command in commands_in(run):
                for suite_name, suite in SUITES.items():
                    if suite.pattern.match(command):
                        invocations.setdefault(suite_name, []).append(gates)

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

    problems.extend(suite_problems(invocations))

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
    print(f"All {len(SUITES)} test suites are run by a workflow.")
    if KNOWN_HOLLOW:
        print(f"Still hollow, tracked in KNOWN_HOLLOW: {known}")
    if KNOWN_UNGATED:
        print(
            f"Runs but does not gate, tracked in KNOWN_UNGATED: "
            f"{', '.join(sorted(KNOWN_UNGATED))}"
        )
    return 0


if __name__ == "__main__":
    sys.exit(main())
