"""
Unit tests for `.github/scripts/check_workflows.py`.

The script runs against the real `.github/workflows/` on every pull request,
which is the check that matters. These cover the judgements it makes, which
that run cannot: that it says yes to a workflow with a real step and no to one
without, that the scaffolding list does not accidentally swallow something
substantive, and that every required status-check context still has a job
producing it.

That last one is not hypothetical. Deleting the four hollow workflows was the
obvious cleanup and would have been an outage: `lint`, `security`, `ci` and
`typecheck` are required contexts on `main`, and a required context that never
reports is not a failing check -- it is a pull request that can never merge,
for everybody, until an admin edits the ruleset.
"""

from __future__ import annotations

import importlib.util
from pathlib import Path

import pytest

yaml = pytest.importorskip("yaml")

REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPT = REPO_ROOT / ".github" / "scripts" / "check_workflows.py"


def _load():
    spec = importlib.util.spec_from_file_location("check_workflows", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


check_workflows = _load()


# ---------------------------------------------------------------------------
# Scaffolding
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "uses",
    [
        "actions/checkout@v4",
        "actions/checkout@v7",
        "actions/setup-node@v7",
        "actions/setup-python@v5",
        "actions/cache@v4",
    ],
)
def test_setup_actions_are_scaffolding(uses):
    assert check_workflows.is_scaffolding({"uses": uses}) is True


def test_version_is_ignored_when_matching(uses="actions/checkout@some-sha"):
    """
    Matched on the part before the `@`, so a Dependabot bump does not need an
    edit here -- and pinning to a SHA, which is the recommendation, still
    matches.
    """
    assert check_workflows.is_scaffolding({"uses": uses}) is True


@pytest.mark.parametrize(
    "step",
    [
        {"run": "npx tsc --noEmit"},
        {"run": "echo hello"},
        {"uses": "github/codeql-action/analyze@v3"},
        {"uses": "actions/github-script@v7"},
        {"uses": "actions/upload-artifact@v4"},
    ],
)
def test_real_steps_are_not_scaffolding(step):
    assert check_workflows.is_scaffolding(step) is False


def test_a_run_step_is_substantive_even_if_it_also_uses_an_action():
    assert (
        check_workflows.is_scaffolding({"run": "true", "uses": "actions/checkout@v4"})
        is False
    )


# ---------------------------------------------------------------------------
# Counting steps in a job
# ---------------------------------------------------------------------------


def test_a_checkout_only_job_has_no_substantive_steps():
    """The exact shape of the four hollow workflows."""
    job = yaml.safe_load(
        """
        runs-on: ubuntu-latest
        steps:
          - uses: actions/checkout@v4
        """
    )

    assert check_workflows.substantive_steps(job) == 0


def test_setup_without_a_check_is_still_nothing():
    """
    The tempting near-miss: install everything, then forget to run the tool.
    """
    job = yaml.safe_load(
        """
        runs-on: ubuntu-latest
        steps:
          - uses: actions/checkout@v4
          - uses: actions/setup-node@v7
          - uses: actions/cache@v4
        """
    )

    assert check_workflows.substantive_steps(job) == 0


def test_a_job_that_runs_something_counts_it():
    job = yaml.safe_load(
        """
        runs-on: ubuntu-latest
        steps:
          - uses: actions/checkout@v4
          - uses: actions/setup-node@v7
          - run: npm ci
          - run: npx tsc --noEmit
        """
    )

    assert check_workflows.substantive_steps(job) == 2


def test_a_reusable_workflow_job_counts_as_a_check():
    """
    `jobs.x.uses` delegates the steps to another file. Still a real check, just
    not one defined here -- and treating it as hollow would be wrong.
    """
    job = yaml.safe_load("uses: ./.github/workflows/reusable.yml")

    assert check_workflows.substantive_steps(job) == 1


def test_a_job_with_no_steps_at_all_is_hollow():
    assert check_workflows.substantive_steps({"runs-on": "ubuntu-latest"}) == 0


def test_a_malformed_step_does_not_crash_the_check():
    """
    Neither `run` nor `uses`. Counted as not-a-check rather than raising --
    this script's job is to fail a pull request with a readable message, not to
    traceback on one.
    """
    job = {"steps": [{"name": "just a label"}]}

    assert check_workflows.substantive_steps(job) == 0


# ---------------------------------------------------------------------------
# The repository as it stands
# ---------------------------------------------------------------------------


def test_every_workflow_in_this_repository_passes():
    """
    Duplicates what CI does, so a hollow workflow fails locally too -- before
    the pull request, which is when it is cheapest to notice.
    """
    import os

    cwd = os.getcwd()
    os.chdir(REPO_ROOT)
    try:
        assert check_workflows.main() == 0
    finally:
        os.chdir(cwd)


# ---------------------------------------------------------------------------
# Required status-check contexts
# ---------------------------------------------------------------------------


def test_every_required_context_has_a_job_producing_it():
    """
    A job's context is its `name:`, or its id when it has none. Rename either
    and the context stops reporting.
    """
    import os

    cwd = os.getcwd()
    os.chdir(REPO_ROOT)
    try:
        assert check_workflows.main() == 0
    finally:
        os.chdir(cwd)


def test_the_required_contexts_are_the_ones_branch_protection_asks_for():
    """
    Pinned literally. The list in the script is mirrored from
    `gh api repos/nensii21/devlink/rules/branches/main` because a fork running
    this in a pull request has no token that can read repository rules.

    If branch protection changes, this test is the thing that has to be edited
    on purpose rather than the script drifting silently.
    """
    assert check_workflows.REQUIRED_CONTEXTS == {
        "backend",
        "check-star",
        "ci",
        "frontend",
        "lint",
        "security",
        "typecheck",
    }


@pytest.mark.parametrize("context", sorted(check_workflows.REQUIRED_CONTEXTS))
def test_a_job_exists_for_each_required_context(context):
    """
    Same ground as the sweep above, one context at a time, so a failure names
    the check that stopped reporting instead of listing all seven.
    """
    produced = set()

    for path in sorted((REPO_ROOT / ".github" / "workflows").glob("*.y*ml")):
        raw = path.read_text()
        if not raw.strip():
            continue
        document = yaml.safe_load(raw)
        for job_id, job in (document.get("jobs") or {}).items():
            if isinstance(job, dict):
                produced.add(job.get("name") or job_id)

    assert context in produced, (
        f"no job produces the required status check {context!r} -- branch "
        "protection will wait for it forever"
    )


# ---------------------------------------------------------------------------
# The known-hollow allowlist
# ---------------------------------------------------------------------------


def test_known_hollow_entries_still_exist():
    """
    Stops the allowlist outliving the files it excuses.
    """
    workflows = REPO_ROOT / ".github" / "workflows"
    missing = [
        name for name in check_workflows.KNOWN_HOLLOW if not (workflows / name).exists()
    ]

    assert missing == [], (
        f"KNOWN_HOLLOW names workflows that no longer exist: {missing}"
    )


def test_known_hollow_entries_are_actually_still_hollow():
    """
    The other direction: once `lint.yml` gets a real step it should come off
    the list, not sit there quietly excusing a workflow that no longer needs
    excusing. A skip rather than a failure -- somebody fixing it is the good
    outcome and should not turn CI red.
    """
    workflows = REPO_ROOT / ".github" / "workflows"
    fixed = []

    for name in check_workflows.KNOWN_HOLLOW:
        document = yaml.safe_load((workflows / name).read_text())
        jobs = (document or {}).get("jobs") or {}
        if all(
            check_workflows.substantive_steps(job) > 0
            for job in jobs.values()
            if isinstance(job, dict)
        ):
            fixed.append(name)

    if fixed:
        pytest.skip(
            f"KNOWN_HOLLOW entries that now do real work: {fixed} -- remove them."
        )


def test_each_known_hollow_entry_says_why():
    for name, reason in check_workflows.KNOWN_HOLLOW.items():
        assert reason.strip(), f"{name} is allowlisted with no reason given"


def test_no_workflow_file_is_empty():
    """
    `release-drafter.yml` was zero bytes. GitHub reports that as a broken
    workflow rather than as an absent one, so it showed up in the Actions tab
    as a permanent error.
    """
    empty = [
        path.name
        for path in sorted((REPO_ROOT / ".github" / "workflows").glob("*.y*ml"))
        if not path.read_text().strip()
    ]

    assert empty == [], f"empty workflow files: {empty}"


# ---------------------------------------------------------------------------
# Test suites (#1316)
# ---------------------------------------------------------------------------
#
# A workflow can run three real steps and still leave the repository's tests on
# the floor. `frontend-ci.yml` installed, built and compared the route tree --
# hollow-check-clean, green tick, and 726 vitest tests it had never run. These
# cover the judgements that catch that.


def _splits_to(run: str) -> list[str]:
    return list(check_workflows.commands_in(run))


@pytest.mark.parametrize(
    ("run", "expected"),
    [
        ("npm run test", ["npm run test"]),
        ("cd backend && pytest", ["cd backend", "pytest"]),
        ("npm ci\nnpm run build\nnpm run test", ["npm ci", "npm run build", "npm run test"]),
        ("black --check . ; pytest", ["black --check .", "pytest"]),
        ("pytest || echo failed", ["pytest", "echo failed"]),
        ("CI=true npm run test", ["npm run test"]),
        ("  \n  npm run test  \n  ", ["npm run test"]),
    ],
)
def test_run_blocks_split_into_commands(run, expected):
    assert _splits_to(run) == expected


def test_a_pipe_separates_commands_but_an_or_is_not_two_pipes():
    assert _splits_to("cat x | grep y") == ["cat x", "grep y"]
    assert _splits_to("pytest || true") == ["pytest", "true"]


def _runs_suite(name: str, run: str) -> bool:
    """Whether this `run:` block runs the named suite, the way `main` asks."""
    suite = check_workflows.SUITES[name]
    return any(
        suite.pattern.match(command) for command in check_workflows.commands_in(run)
    )


@pytest.mark.parametrize(
    "run",
    [
        "npm run test",
        "npx vitest run",
        "vitest run --exclude e2e",
        "CI=1 npm run test",
        "npm ci\nnpm run build\nnpm run test",
    ],
)
def test_frontend_suite_is_recognised(run):
    assert _runs_suite("frontend", run) is True


@pytest.mark.parametrize(
    "run",
    [
        # A different suite: Playwright needs browsers and a server.
        "npm run test:e2e",
        # Naming the package is not running it.
        "npm install vitest",
        "npm ci",
        "npm run build",
    ],
)
def test_frontend_suite_is_not_recognised_in(run):
    assert _runs_suite("frontend", run) is False


@pytest.mark.parametrize(
    "run",
    [
        "pytest",
        "pytest -q",
        "python -m pytest",
        "python3.12 -m pytest tests/",
        "cd backend && pytest",
    ],
)
def test_backend_suite_is_recognised(run):
    assert _runs_suite("backend", run) is True


@pytest.mark.parametrize(
    "run",
    [
        # The line that made the first draft of this check pass for the wrong
        # reason: `backend-ci.yml` installs pytest in a step that gates, and
        # runs it in a step that does not. Reading the install as a run made
        # the backend suite look gated and hid the `continue-on-error`.
        "pip install black ruff mypy pytest",
        "pip install -r requirements.txt",
        "pytest-cov --version",
    ],
)
def test_backend_suite_is_not_recognised_in(run):
    assert _runs_suite("backend", run) is False


def _document(steps, job_extra=None):
    job = {"runs-on": "ubuntu-latest", "steps": steps}
    job.update(job_extra or {})
    return {"jobs": {"job": job}}


def test_a_plain_step_gates():
    document = _document([{"run": "npm run test"}])
    assert list(check_workflows.iter_run_steps(document)) == [("npm run test", True)]


def test_continue_on_error_on_the_step_means_it_does_not_gate():
    document = _document([{"run": "pytest", "continue-on-error": True}])
    assert list(check_workflows.iter_run_steps(document)) == [("pytest", False)]


def test_continue_on_error_on_the_job_means_its_steps_do_not_gate():
    document = _document([{"run": "pytest"}], {"continue-on-error": True})
    assert list(check_workflows.iter_run_steps(document)) == [("pytest", False)]


def test_steps_without_a_run_are_ignored():
    document = _document([{"uses": "actions/checkout@v4"}, {"run": "pytest"}])
    assert list(check_workflows.iter_run_steps(document)) == [("pytest", True)]


def test_a_suite_nobody_runs_is_a_problem():
    problems = check_workflows.suite_problems({"backend": [False]})

    assert len(problems) == 1
    assert "frontend unit tests" in problems[0]


def test_a_suite_that_only_runs_under_continue_on_error_is_a_problem():
    problems = check_workflows.suite_problems({"frontend": [False], "backend": [False]})

    assert len(problems) == 1
    assert "continue-on-error" in problems[0]
    assert "frontend unit tests" in problems[0]


def test_one_gating_invocation_is_enough():
    """Running a suite twice, once advisory, is not a fault."""
    assert (
        check_workflows.suite_problems({"frontend": [False, True], "backend": [False]})
        == []
    )


def test_a_known_ungated_suite_that_starts_gating_must_lose_its_entry():
    """
    The one direction that has to be an error rather than a skip: a debt that
    has been paid off and still has a note saying it has not is a lie the next
    reader will believe.
    """
    problems = check_workflows.suite_problems({"frontend": [True], "backend": [True]})

    assert len(problems) == 1
    assert "stale" in problems[0]


def test_the_repositorys_own_workflows_satisfy_the_suite_check():
    """The check that actually matters, run here so a failure names itself."""
    workflows = REPO_ROOT / ".github" / "workflows"
    invocations: dict[str, list[bool]] = {}

    for path in sorted(workflows.glob("*.y*ml")):
        document = yaml.safe_load(path.read_text())
        if not isinstance(document, dict):
            continue
        for run, gates in check_workflows.iter_run_steps(document):
            for command in check_workflows.commands_in(run):
                for name, suite in check_workflows.SUITES.items():
                    if suite.pattern.match(command):
                        invocations.setdefault(name, []).append(gates)

    assert check_workflows.suite_problems(invocations) == []


def test_each_known_ungated_entry_names_a_real_suite():
    unknown = set(check_workflows.KNOWN_UNGATED) - set(check_workflows.SUITES)

    assert unknown == set(), f"KNOWN_UNGATED names suites that do not exist: {unknown}"


def test_each_known_ungated_entry_says_why():
    for name, reason in check_workflows.KNOWN_UNGATED.items():
        assert reason.strip(), f"{name} is allowlisted with no reason given"
