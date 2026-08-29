"""
Guards that every Python source file under ``backend/`` is well-formed.

Why this exists
---------------

Three modules shipped to ``main`` with syntax errors and nobody noticed:

* ``app/routers/users.py`` -- two request handlers spliced into one
* ``app/schemas/user.py``  -- a field indented one level too deep
* ``app/utils/uploads.py`` -- a ``def`` swallowed by the following ``def``

All three came out of one merge (``e2be7a58``) that kept both sides of every
conflicting hunk without leaving a conflict marker behind, so the result reads
as plausible code right up until the parser sees it. ``app/routers/users.py``
is registered on the v1 router, which means the application could not import
and every endpoint was down.

Nothing caught it. The tests that would have failed all import ``app.main``
transitively, so they errored at *collection*, and a collection error is easy
to read as "the environment is wrong" rather than "the code is broken".

These tests fail loudly, cheaply, and without importing anything, so the same
class of damage cannot reach ``main`` again:

* :func:`test_every_source_file_parses` compiles every file with :mod:`ast`.
  No imports, no database, no settings -- it works in a bare checkout.
* :func:`test_no_conflict_markers` catches the ordinary version of the same
  accident, where the markers *are* left in.
* :func:`test_no_duplicate_top_level_definitions` catches the quieter version:
  a name bound twice at module or class scope, where the second binding
  silently discards the first. That is a live bug in this repo today
  (``PROJECT_ROLE_PERMISSIONS`` in ``app/core/rbac.py``), so the known cases
  are listed in :data:`KNOWN_DUPLICATE_DEFINITIONS` and the test asserts no
  *new* ones appear.
* :func:`test_sources_are_utf8` catches files committed in another encoding,
  which is how ``check_pr.py`` came to fail with "source code string cannot
  contain null bytes".
"""

from __future__ import annotations

import ast
import re
import warnings
from collections import Counter
from pathlib import Path
from typing import Iterator

import pytest

# ``backend/tests/test_source_integrity.py`` -> ``backend/``
BACKEND_ROOT = Path(__file__).resolve().parent.parent
REPO_ROOT = BACKEND_ROOT.parent

#: Directories that are not ours to police.
EXCLUDED_DIR_NAMES = frozenset(
    {
        "__pycache__",
        ".git",
        ".mypy_cache",
        ".pytest_cache",
        ".ruff_cache",
        ".venv",
        "venv",
        "env",
        "node_modules",
        "site-packages",
        "backups",
        "clients",
    }
)

#: Conflict markers, anchored to the start of a line. ``=======`` needs the
#: full-line anchor because a row of equals signs is also a common comment
#: divider; the other two are unambiguous.
CONFLICT_MARKER_PATTERNS = (
    re.compile(r"^<<<<<<< ", re.MULTILINE),
    re.compile(r"^>>>>>>> ", re.MULTILINE),
    re.compile(r"^={7}$", re.MULTILINE),
    re.compile(r"^\|{7} ", re.MULTILINE),
)

#: Duplicate top-level bindings that exist today and are tracked by their own
#: issue. Anything not on this list is a regression. Entries are
#: ``(path relative to backend/, name)``.
KNOWN_DUPLICATE_DEFINITIONS: frozenset[tuple[str, str]] = frozenset(
    {
        # https://github.com/nensii21/devlink/issues/1197
        ("app/core/rbac.py", "PROJECT_ROLE_PERMISSIONS"),
    }
)


def _iter_python_files(root: Path) -> Iterator[Path]:
    """Every ``.py`` file under ``root``, skipping vendored/generated trees."""
    for path in sorted(root.rglob("*.py")):
        if any(part in EXCLUDED_DIR_NAMES for part in path.parts):
            continue
        yield path


def _relative(path: Path) -> str:
    """A short, stable label for assertion messages."""
    try:
        return str(path.relative_to(BACKEND_ROOT))
    except ValueError:
        return str(path.relative_to(REPO_ROOT))


PYTHON_FILES = list(_iter_python_files(BACKEND_ROOT))


def test_the_scan_found_files() -> None:
    """A guard on the guard.

    If the glob silently matched nothing -- a moved test file, a renamed
    directory -- every test below would pass vacuously and the protection
    would be gone without anyone noticing.
    """
    assert len(PYTHON_FILES) > 50, (
        f"Only found {len(PYTHON_FILES)} Python files under {BACKEND_ROOT}. "
        "The scan root is probably wrong."
    )


@pytest.mark.parametrize("path", PYTHON_FILES, ids=_relative)
def test_every_source_file_parses(path: Path) -> None:
    """Every module is syntactically valid Python.

    Deliberately :func:`ast.parse` rather than ``import``: parsing needs no
    settings, no database and no third-party packages, so this stays fast and
    stays green in a bare checkout. It is the check that ``main`` failed.
    """
    source = path.read_text(encoding="utf-8")

    try:
        ast.parse(source, filename=str(path))
    except SyntaxError as exc:
        pytest.fail(
            f"{_relative(path)} does not parse: "
            f"line {exc.lineno}, {exc.msg}\n"
            f"    {(exc.text or '').strip()}"
        )


@pytest.mark.parametrize("path", PYTHON_FILES, ids=_relative)
def test_no_conflict_markers(path: Path) -> None:
    """No unresolved merge conflict markers are committed."""
    source = path.read_text(encoding="utf-8")

    for pattern in CONFLICT_MARKER_PATTERNS:
        match = pattern.search(source)
        if match:
            line_no = source[: match.start()].count("\n") + 1
            pytest.fail(
                f"{_relative(path)}:{line_no} contains an unresolved merge "
                f"conflict marker: {match.group(0).strip()!r}"
            )


@pytest.mark.parametrize("path", PYTHON_FILES, ids=_relative)
def test_sources_are_utf8(path: Path) -> None:
    """Every source file decodes as UTF-8 with no BOM and no null bytes.

    A UTF-16-encoded ``.py`` file looks fine in most editors and dies at the
    interpreter with "source code string cannot contain null bytes".
    """
    raw = path.read_bytes()

    assert b"\x00" not in raw, (
        f"{_relative(path)} contains null bytes -- it is probably saved as "
        "UTF-16. Re-save it as UTF-8."
    )

    assert not raw.startswith(
        b"\xef\xbb\xbf"
    ), f"{_relative(path)} starts with a UTF-8 BOM. Save it without one."

    try:
        raw.decode("utf-8")
    except UnicodeDecodeError as exc:
        pytest.fail(f"{_relative(path)} is not valid UTF-8: {exc}")


def _top_level_bindings(tree: ast.Module) -> Counter[str]:
    """Count module-scope bindings of each name.

    Only the forms where a second binding silently discards the first are
    counted:

    * ``def f(): ...`` / ``async def f(): ...`` / ``class F: ...``
    * ``NAME = ...`` and ``NAME: T = ...`` where the value is a literal
      container

    A plain re-assignment such as ``x = 1`` then ``x = 2`` is normal code, so
    only *definition-shaped* bindings are considered: functions, classes, and
    assignments whose value is a dict/list/set/tuple display or a ``frozenset``
    call. Those are lookup tables, and a duplicated lookup table is always a
    mistake.
    """
    counts: Counter[str] = Counter()

    def is_table(value: ast.expr) -> bool:
        if isinstance(value, (ast.Dict, ast.List, ast.Set, ast.Tuple)):
            return True
        return (
            isinstance(value, ast.Call)
            and isinstance(value.func, ast.Name)
            and value.func.id in {"frozenset", "set", "dict", "list", "tuple"}
        )

    for node in tree.body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            counts[node.name] += 1
        elif isinstance(node, ast.Assign) and is_table(node.value):
            for target in node.targets:
                if isinstance(target, ast.Name):
                    counts[target.id] += 1
        elif (
            isinstance(node, ast.AnnAssign)
            and isinstance(node.target, ast.Name)
            and node.value is not None
            and is_table(node.value)
        ):
            counts[node.target.id] += 1

    return counts


def _class_method_bindings(tree: ast.Module) -> list[tuple[str, str]]:
    """``(class name, method name)`` for every method defined more than once."""
    duplicates: list[tuple[str, str]] = []

    for node in ast.walk(tree):
        if not isinstance(node, ast.ClassDef):
            continue

        counts: Counter[str] = Counter()
        for item in node.body:
            if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)):
                counts[item.name] += 1

        duplicates.extend(
            (node.name, name) for name, count in counts.items() if count > 1
        )

    return duplicates


@pytest.mark.parametrize("path", PYTHON_FILES, ids=_relative)
def test_no_duplicate_top_level_definitions(path: Path) -> None:
    """A name is not defined twice at module scope.

    The second definition wins and the first becomes unreachable, which is how
    a merge that keeps both sides survives review: the file parses, the tests
    pass, and half the code in it is dead.
    """
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    rel = _relative(path)

    offenders = [
        name
        for name, count in _top_level_bindings(tree).items()
        if count > 1 and (rel, name) not in KNOWN_DUPLICATE_DEFINITIONS
    ]

    assert not offenders, (
        f"{rel} defines these names more than once at module scope, so the "
        f"earlier definition is dead: {', '.join(sorted(offenders))}"
    )


@pytest.mark.parametrize("path", PYTHON_FILES, ids=_relative)
def test_no_duplicate_methods(path: Path) -> None:
    """A class does not define the same method twice."""
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))

    duplicates = _class_method_bindings(tree)

    assert (
        not duplicates
    ), f"{_relative(path)} defines these methods more than once: " + ", ".join(
        f"{cls}.{method}" for cls, method in sorted(duplicates)
    )


def test_known_duplicate_list_has_no_stale_entries() -> None:
    """Report entries in :data:`KNOWN_DUPLICATE_DEFINITIONS` that are fixed.

    Without some pressure, an allowance stays on the list forever after the bug
    it covers is gone, quietly re-opening the hole for that name.

    This **warns rather than fails**, deliberately. A stale entry means somebody
    fixed a bug: the list can only ever be too permissive, never too strict, so
    the failure mode is mild. Failing here would mean the PR that fixes a
    duplicate turns CI red until a second PR deletes one line from this file —
    making a green build depend on the merge order of two otherwise unrelated
    changes, which is a worse outcome than a warning.
    """
    stale: list[tuple[str, str]] = []

    for rel, name in sorted(KNOWN_DUPLICATE_DEFINITIONS):
        path = BACKEND_ROOT / rel
        if not path.exists():
            stale.append((rel, name))
            continue

        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        if _top_level_bindings(tree).get(name, 0) <= 1:
            stale.append((rel, name))

    if stale:
        warnings.warn(
            "These entries in KNOWN_DUPLICATE_DEFINITIONS are fixed and can be "
            "removed from the list: "
            + ", ".join(f"{rel}::{name}" for rel, name in stale),
            stacklevel=2,
        )
