"""
A guard against undefined names in `app/`.

`ExportService.collect_user_data` shipped with a bare `builder_flares` in it
and took every export route down. Ruff finds that class of mistake in about a
second:

    $ ruff check --select F821 app/
    app/services/export_service.py:65:28: F821 Undefined name `builder_flares`

Nothing ran it. `lint.yml` checks out the repository and stops (#1248), and
`ruff` in `.pre-commit-config.yaml` only sees files that are staged in a
working tree where someone installed the hooks.

So the check lives here instead, where `pytest` already runs it. That is not
where a linter belongs long-term -- when `lint.yml` becomes real this should
move -- but a check that runs in the wrong place beats one that does not run.

Scope is deliberately one rule. This is not "lint the backend": `ruff check
app/` reports 3354 findings, almost all formatting, and turning that on is a
separate decision. F821 is the subset that means *this line raises when it is
reached*, so it can be enforced today with no baseline at all -- except for
the two below, which have a fix already in flight.
"""

from __future__ import annotations

import json
import shutil
import subprocess
from pathlib import Path

import pytest

BACKEND_ROOT = Path(__file__).resolve().parents[1]

#: Sites that are known-broken and already have a PR open. Listed as
#: ``(path, message)`` so an entry cannot quietly cover a *different* undefined
#: name in the same file.
#:
#: Both are `Optional` used in a module that never imports it, reported in
#: #1236 and fixed in #1238. When that merges, these two lines come out and the
#: allowlist should be empty -- at which point this list should be deleted
#: rather than kept around as a place to put things.
KNOWN_UNFIXED = {
    ("app/routers/analytics.py", "Undefined name `Optional`"),
    ("app/routers/projects.py", "Undefined name `Optional`"),
}


def _ruff_findings(rule: str, target: str) -> list[dict]:
    """Run ruff for one rule and return its findings as dicts."""
    completed = subprocess.run(
        [
            "ruff",
            "check",
            "--select",
            rule,
            "--no-cache",
            "--output-format",
            "json",
            target,
        ],
        cwd=BACKEND_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )

    # ruff exits 1 when it finds something, which is not an error here.
    if completed.returncode not in (0, 1):
        pytest.fail(
            f"ruff failed to run (exit {completed.returncode}):\n{completed.stderr}"
        )

    return json.loads(completed.stdout or "[]")


def _relative(finding: dict) -> str:
    return str(Path(finding["filename"]).resolve().relative_to(BACKEND_ROOT))


@pytest.fixture(scope="module")
def undefined_names() -> list[dict]:
    if shutil.which("ruff") is None:
        pytest.skip("ruff is not installed")
    return _ruff_findings("F821", "app")


def test_no_new_undefined_names(undefined_names):
    """
    Every F821 in `app/` is either fixed or on the allowlist above.

    The failure message prints file, line and name, because "ruff found
    something" is not actionable and the whole point of this test is that
    somebody reads its output.
    """
    unexpected = [
        finding
        for finding in undefined_names
        if (_relative(finding), finding["message"]) not in KNOWN_UNFIXED
    ]

    if unexpected:
        lines = "\n".join(
            f"  {_relative(f)}:{f['location']['row']}:{f['location']['column']}: "
            f"{f['message']}"
            for f in sorted(unexpected, key=_relative)
        )
        pytest.fail(
            "Undefined names in app/. Each of these raises NameError when the "
            "line is reached:\n"
            f"{lines}\n\n"
            "If the name only appears in an annotation it is latent rather "
            "than live, but it still breaks `get_type_hints()` and any schema "
            "generation that walks it -- import it rather than allowlisting it."
        )


def test_allowlist_only_covers_what_it_claims(undefined_names):
    """
    Stops the allowlist from being a place things go to be forgotten.

    A stale entry is not a failure -- #1238 landing is the good outcome, and
    this test should not turn red the moment it does. It warns instead, so the
    dead line gets noticed at the next test run rather than at the next audit.
    """
    live = {(_relative(f), f["message"]) for f in undefined_names}
    stale = KNOWN_UNFIXED - live

    if stale:
        listed = ", ".join(sorted(path for path, _ in stale))
        pytest.skip(
            f"KNOWN_UNFIXED has entries that are now fixed ({listed}) -- "
            "remove them from the allowlist."
        )


def test_the_export_service_specifically_is_clean():
    """
    The regression this file was written for, pinned by name.

    Redundant with the sweep above while the sweep passes, and not redundant
    the day someone widens the allowlist.
    """
    if shutil.which("ruff") is None:
        pytest.skip("ruff is not installed")

    findings = _ruff_findings("F821", "app/services/export_service.py")

    assert findings == [], (
        "app/services/export_service.py has an undefined name again: "
        f"{[f['message'] for f in findings]}"
    )
