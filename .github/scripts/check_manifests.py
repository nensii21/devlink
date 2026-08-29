#!/usr/bin/env python3
"""
Refuse dependency manifests that nothing builds and nothing watches.

The repository root carried `package.json` naming the project
`cryptoviz-core`, depending on `next`, `react`, `react-dom`, `bcryptjs`,
`@noble/curves`, `@noble/hashes` and `dompurify`. None of them are imported
anywhere here; DevLink's frontend is React 19 on TanStack Start with its own
manifest, and the backend is FastAPI (#1401).

It sat there for weeks because nothing in the repository disagreed with it.
Worse, two things agreed with it:

* `.github/dependabot.yml` had been rewritten to watch it *instead of*
  `frontend/`, `backend/` and the workflow actions, so ten pull request slots
  a week went to packages nobody imports -- labelled `security-audit` -- while
  the real dependency trees went unwatched.
* `dependency-security.yml` ran `npm ci`, `npm audit --audit-level=high`,
  `license-checker` and a CycloneDX SBOM build against it. All four passed.
  None of them had looked at anything that ships.

That last one is the reason this script exists rather than a one-line
`.gitignore` entry. `check_workflows.py` (#1248) refuses a workflow that
reports success without checking anything; this refuses the level below,
where a workflow does run a real command against the wrong tree. From the
pull request page the two are indistinguishable, and both read as assurance.

Three rules, each the negative of something that actually happened:

1. **Every manifest is installed by some workflow.** A manifest no CI job
   installs is one nobody has verified resolves, builds, or is even parseable.
2. **Every manifest is watched by Dependabot.** Otherwise its dependencies
   quietly stop receiving security updates, which is invisible: no PR arrives,
   and no PR arriving looks exactly like nothing needing an update.
3. **Every Dependabot entry points at a manifest that exists.** A `directory`
   with nothing in it produces no updates and no error.
4. **Every `package.json` names a project this repository knows about.** The
   root one said `cryptoviz-core`. Rules 1--3 would not have caught it: it was
   installed by a workflow and watched by Dependabot. It was covered. It was
   just not ours, and the only thing in the file that said so was the name.

   `KNOWN_PACKAGE_NAMES` below is the allow-list. A new manifest fails until
   somebody adds its name -- which is the point. That edit is the moment a
   human reads the name and decides whether it belongs here, and it is the
   moment that did not happen in 4661ea27.

Deliberately not clever. It does not judge whether a dependency is *needed* --
that requires understanding the code, and a wrong answer here blocks
everybody's pull requests. It asks only whether something in the repository is
responsible for each manifest.

Usage:
    python3 .github/scripts/check_manifests.py
    python3 .github/scripts/check_manifests.py --self-test
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path
from typing import Any, Iterable

import yaml

REPO_ROOT = Path(__file__).resolve().parents[2]
WORKFLOWS = REPO_ROOT / ".github" / "workflows"
DEPENDABOT = REPO_ROOT / ".github" / "dependabot.yml"

#: Manifest filenames, mapped to the Dependabot ecosystem that watches them.
MANIFESTS = {
    "package.json": "npm",
    "requirements.txt": "pip",
}

#: Directories that hold generated or vendored manifests. A manifest under one
#: of these is an artifact, not something anyone maintains, so the three rules
#: do not apply to it.
#:
#: `.output` and `dist` are build products; `.vite` is a dependency
#: pre-bundling cache. All three have been committed here at one time or
#: another (#1348), which is its own problem -- but not this script's, and it
#: should not fail the build twice for one mistake.
IGNORED_PARTS = frozenset(
    {
        "node_modules",
        "dist",
        "build",
        ".output",
        ".vite",
        ".venv",
        "venv",
        "site-packages",
        "__pycache__",
        ".git",
    }
)

#: `name` values a `package.json` in this repository may carry.
#:
#: Not a style rule. The root manifest named itself `cryptoviz-core` and
#: nothing in the repository disagreed with it for weeks, because a name is
#: the only part of a manifest that says which project it belongs to and
#: nothing was reading it (#1401).
#:
#: `tanstack_start_ts` is the TanStack Start scaffold's default and predates
#: this check. It is a poor name for DevLink's frontend and worth changing,
#: but renaming a package is not this change's business -- it is listed so
#: this script reports the problem it was written for rather than a
#: pre-existing one.
KNOWN_PACKAGE_NAMES = frozenset(
    {
        "devlink",
        "devlink-frontend",
        "tanstack_start_ts",
    }
)

#: Commands that count as installing a manifest's dependencies.
INSTALL_MARKERS = (
    "npm ci",
    "npm install",
    "npm i ",
    "yarn install",
    "pnpm install",
    "pip install",
    "uv pip install",
    "uv sync",
    "poetry install",
)


# ---------------------------------------------------------------------------
# Reading the repository
# ---------------------------------------------------------------------------


def tracked_files() -> list[str]:
    """
    Paths git knows about.

    Reading from git rather than walking the tree keeps the answer aligned
    with what a reviewer sees in the diff: an untracked `package.json` in
    somebody's working copy is not the repository's problem, and a tracked one
    is, regardless of whether `.gitignore` would have matched it.
    """
    result = subprocess.run(
        ["git", "ls-files", "-z"],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=True,
    )
    return [p for p in result.stdout.split("\0") if p]


def is_ignored(path: str) -> bool:
    return bool(IGNORED_PARTS.intersection(Path(path).parts))


def find_manifests(paths: Iterable[str]) -> dict[str, str]:
    """
    Map each tracked manifest's directory to its ecosystem.

    Directories are normalised to Dependabot's spelling: `/` for the root,
    `/frontend` for a subdirectory. That is what the config uses, and
    comparing the two forms was where a hand-written version of this check
    went wrong first.
    """
    found: dict[str, str] = {}
    for path in paths:
        if is_ignored(path):
            continue
        name = Path(path).name
        ecosystem = MANIFESTS.get(name)
        if ecosystem is None:
            continue
        parent = str(Path(path).parent)
        directory = "/" if parent == "." else f"/{parent}"
        found[directory] = ecosystem
    return found


# ---------------------------------------------------------------------------
# Reading the workflows
# ---------------------------------------------------------------------------


def _step_directory(
    step: dict, job_default: str | None, workflow_default: str | None
) -> str:
    """
    The directory a step runs in.

    GitHub resolves `working-directory` at three levels, innermost first. The
    root manifest was installed by a workflow with no `working-directory` at
    all, which is why the default matters as much as the explicit case.
    """
    raw = (
        step.get("working-directory")
        or job_default
        or workflow_default
        or "."
    )
    raw = str(raw).strip().rstrip("/")
    if raw in ("", ".", "./"):
        return "/"
    return "/" + raw.lstrip("./").lstrip("/")


def installed_directories() -> dict[str, set[str]]:
    """
    Directories each workflow installs dependencies in.

    Keyed by workflow filename so a failure can name the file to look at.
    """
    installs: dict[str, set[str]] = {}
    if not WORKFLOWS.is_dir():
        return installs

    for path in sorted(WORKFLOWS.glob("*.y*ml")):
        raw = path.read_text()
        if not raw.strip():
            continue
        try:
            doc = yaml.safe_load(raw)
        except yaml.YAMLError:
            # `check_workflows.py` owns reporting unparseable workflows.
            continue
        if not isinstance(doc, dict):
            continue

        workflow_default = (
            (doc.get("defaults") or {}).get("run", {}).get("working-directory")
        )

        for job in (doc.get("jobs") or {}).values():
            if not isinstance(job, dict):
                continue
            job_default = (
                (job.get("defaults") or {}).get("run", {}).get("working-directory")
            )

            for step in job.get("steps") or []:
                if not isinstance(step, dict):
                    continue
                run = step.get("run")
                if not isinstance(run, str):
                    continue
                if not any(marker in run for marker in INSTALL_MARKERS):
                    continue
                directory = _step_directory(step, job_default, workflow_default)
                installs.setdefault(path.name, set()).add(directory)

    return installs


# ---------------------------------------------------------------------------
# Reading dependabot.yml
# ---------------------------------------------------------------------------


def dependabot_entries() -> list[tuple[str, str]]:
    """`(ecosystem, directory)` pairs, normalised the same way as manifests."""
    if not DEPENDABOT.is_file():
        return []

    doc = yaml.safe_load(DEPENDABOT.read_text())
    if not isinstance(doc, dict):
        return []

    entries: list[tuple[str, str]] = []
    for update in doc.get("updates") or []:
        if not isinstance(update, dict):
            continue
        ecosystem = update.get("package-ecosystem")
        directory = update.get("directory")
        if not ecosystem or not directory:
            continue
        directory = str(directory).rstrip("/") or "/"
        if not directory.startswith("/"):
            directory = "/" + directory
        entries.append((str(ecosystem), directory))
    return entries


# ---------------------------------------------------------------------------
# Rule 4: does this manifest say it belongs here?
# ---------------------------------------------------------------------------


def package_name(manifest_path: Path) -> str | None:
    """
    The `name` field of a `package.json`, or `None` if it has none.

    An unparseable manifest returns `None` and is reported as unnamed, which
    is the right outcome either way: `npm ci` would fail on it too.
    """
    try:
        doc = json.loads(manifest_path.read_text())
    except (OSError, json.JSONDecodeError):
        return None
    name = doc.get("name")
    return name if isinstance(name, str) and name.strip() else None


def manifest_path_for(directory: str) -> Path:
    """Absolute path to the `package.json` for a normalised directory."""
    if directory == "/":
        return REPO_ROOT / "package.json"
    return REPO_ROOT / directory.lstrip("/") / "package.json"


# ---------------------------------------------------------------------------
# The checks
# ---------------------------------------------------------------------------


def check(
    manifests: dict[str, str],
    installs: dict[str, set[str]],
    entries: list[tuple[str, str]],
    foreign: Iterable[tuple[str, str | None]] = (),
) -> list[str]:
    """Return one message per problem found. Empty means the tree is fine."""
    problems: list[str] = []

    installed = {d for dirs in installs.values() for d in dirs}
    watched = {(eco, directory) for eco, directory in entries}
    watched_dirs = {directory for _, directory in entries}

    # Rule 1 -- somebody builds it.
    for directory, ecosystem in sorted(manifests.items()):
        if directory not in installed:
            problems.append(
                f"{directory} has a {ecosystem} manifest that no workflow "
                f"installs. A manifest nothing builds is one nobody has "
                f"checked resolves -- which is how a manifest for an "
                f"unrelated project sat at the root for weeks (#1401). "
                f"Either add a job that installs it, or remove it."
            )

    # Rule 2 -- somebody watches it.
    for directory, ecosystem in sorted(manifests.items()):
        if (ecosystem, directory) not in watched:
            problems.append(
                f"{directory} has a {ecosystem} manifest that "
                f".github/dependabot.yml does not watch. Its dependencies "
                f"would stop receiving security updates silently: no pull "
                f"request arrives, and none arriving looks exactly like "
                f"nothing needing one."
            )

    # Rule 3 -- what is watched exists.
    for ecosystem, directory in sorted(set(entries)):
        if ecosystem not in MANIFESTS.values():
            # github-actions and docker are not directory-manifest ecosystems.
            continue
        if manifests.get(directory) != ecosystem:
            problems.append(
                f".github/dependabot.yml watches {ecosystem} in {directory}, "
                f"where there is no tracked {ecosystem} manifest. That entry "
                f"produces no updates and no error."
            )

    # Rule 4 -- it says it belongs here.
    for directory, name in sorted(foreign, key=lambda pair: pair[0]):
        described = f"names itself `{name}`" if name else "declares no `name`"
        where = "package.json" if directory == "/" else f"{directory}/package.json"
        problems.append(
            f"{where} {described}, which is not in "
            f"KNOWN_PACKAGE_NAMES. If this manifest belongs to DevLink, add "
            f"the name to .github/scripts/check_manifests.py. If it does not, "
            f"it should not be here -- the root manifest said "
            f"`cryptoviz-core` and passed every other rule in this file "
            f"(#1401)."
        )

    # A directory a workflow installs but nothing declares is usually a typo
    # in `working-directory`, and it fails at a confusing place if left.
    for workflow, dirs in sorted(installs.items()):
        for directory in sorted(dirs):
            if directory not in manifests and directory not in watched_dirs:
                problems.append(
                    f"{workflow} installs dependencies in {directory}, where "
                    f"there is no tracked manifest. Check the "
                    f"`working-directory` on that step."
                )

    return problems


def main() -> int:
    paths = tracked_files()
    manifests = find_manifests(paths)
    installs = installed_directories()
    entries = dependabot_entries()

    foreign: list[tuple[str, str | None]] = []
    for directory, ecosystem in manifests.items():
        if ecosystem != "npm":
            continue
        name = package_name(manifest_path_for(directory))
        if name not in KNOWN_PACKAGE_NAMES:
            foreign.append((directory, name))

    problems = check(manifests, installs, entries, foreign)

    for problem in problems:
        print(f"::error::{problem}")

    if problems:
        print(f"\n{len(problems)} manifest problem(s).")
        return 1

    print(
        f"OK: {len(manifests)} manifest(s), each installed by a workflow and "
        f"watched by Dependabot."
    )
    for directory, ecosystem in sorted(manifests.items()):
        print(f"  {directory:<12} {ecosystem}")
    return 0


# ---------------------------------------------------------------------------
# Self-test
# ---------------------------------------------------------------------------
#
# Embedded rather than dropped in `tests/`, because no workflow runs `tests/`
# -- adding a suite there would be one more thing that looks checked and is
# not, which is the exact failure this file is about. `ci.yml` runs
# `--self-test` and then the real check.


def _self_test() -> int:
    failures: list[str] = []

    def expect(name: str, condition: bool) -> None:
        if not condition:
            failures.append(name)

    # --- the bug this script was written for --------------------------------
    expect(
        "an unbuilt, unwatched root manifest is refused",
        len(check({"/": "npm"}, {}, [])) == 2,
    )
    expect(
        "a manifest installed but unwatched is refused",
        any(
            "does not watch" in p
            for p in check({"/": "npm"}, {"ci.yml": {"/"}}, [])
        ),
    )
    expect(
        "a manifest watched but never installed is refused",
        any(
            "no workflow installs" in p
            for p in check({"/": "npm"}, {}, [("npm", "/")])
        ),
    )
    expect(
        "a fully covered manifest passes",
        check({"/frontend": "npm"}, {"ci.yml": {"/frontend"}}, [("npm", "/frontend")])
        == [],
    )

    # --- dependabot pointing at nothing -------------------------------------
    expect(
        "a dependabot entry with no manifest is refused",
        any("no tracked npm manifest" in p for p in check({}, {}, [("npm", "/gone")])),
    )
    expect(
        "github-actions needs no manifest",
        check({}, {}, [("github-actions", "/")]) == [],
    )
    expect(
        "docker needs no manifest",
        check({}, {}, [("docker", "/backend")]) == [],
    )
    expect(
        "an ecosystem mismatch is refused",
        any(
            "no tracked pip manifest" in p
            for p in check(
                {"/backend": "pip"},
                {"ci.yml": {"/backend"}},
                [("pip", "/backend"), ("pip", "/frontend")],
            )
        ),
    )

    # --- working-directory resolution ---------------------------------------
    expect(
        "an explicit step working-directory wins",
        _step_directory({"working-directory": "frontend"}, "backend", "docs")
        == "/frontend",
    )
    expect(
        "a job default is used when the step has none",
        _step_directory({}, "backend", "docs") == "/backend",
    )
    expect(
        "a workflow default is the last resort",
        _step_directory({}, None, "docs") == "/docs",
    )
    expect(
        "no directory anywhere means the root",
        _step_directory({}, None, None) == "/",
    )
    expect(
        "'.' means the root",
        _step_directory({"working-directory": "."}, None, None) == "/",
    )
    expect(
        "a trailing slash is not a different directory",
        _step_directory({"working-directory": "./frontend/"}, None, None)
        == "/frontend",
    )

    # --- manifest discovery -------------------------------------------------
    expect(
        "manifests are found and normalised",
        find_manifests(["package.json", "frontend/package.json"])
        == {"/": "npm", "/frontend": "npm"},
    )
    expect(
        "requirements.txt is a pip manifest",
        find_manifests(["backend/requirements.txt"]) == {"/backend": "pip"},
    )
    expect(
        "vendored and generated manifests are ignored",
        find_manifests(
            [
                "frontend/node_modules/x/package.json",
                "dist/package.json",
                "frontend/.output/package.json",
                ".vite/deps/package.json",
            ]
        )
        == {},
    )

    # --- rule 4: the manifest that started this ----------------------------
    expect(
        "an unrecognised package name is refused",
        any(
            "cryptoviz-core" in p or "not in KNOWN_PACKAGE_NAMES" in p
            for p in check(
                {"/": "npm"},
                {"ci.yml": {"/"}},
                [("npm", "/")],
                foreign=[("/", "cryptoviz-core")],
            )
        ),
    )
    expect(
        "a manifest with no name is refused",
        any(
            "declares no `name`" in p
            for p in check(
                {"/": "npm"},
                {"ci.yml": {"/"}},
                [("npm", "/")],
                foreign=[("/", None)],
            )
        ),
    )
    expect(
        "the frontend's own name is allowed",
        "tanstack_start_ts" in KNOWN_PACKAGE_NAMES,
    )
    expect(
        "a covered manifest with a known name passes",
        check(
            {"/frontend": "npm"},
            {"ci.yml": {"/frontend"}},
            [("npm", "/frontend")],
            foreign=[],
        )
        == [],
    )

    # --- a typo'd working-directory -----------------------------------------
    expect(
        "installing where nothing is declared is refused",
        any(
            "Check the `working-directory`" in p
            for p in check(
                {"/frontend": "npm"},
                {"ci.yml": {"/frontend", "/frontned"}},
                [("npm", "/frontend")],
            )
        ),
    )

    for name in failures:
        print(f"::error::self-test failed: {name}")

    if failures:
        print(f"\n{len(failures)} self-test failure(s).")
        return 1

    print("Self-test OK.")
    return 0


if __name__ == "__main__":
    if "--self-test" in sys.argv:
        raise SystemExit(_self_test())
    raise SystemExit(main())
