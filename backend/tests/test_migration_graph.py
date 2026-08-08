"""Structural tests for the Alembic revision graph.

The rest of the suite builds its schema with `Base.metadata.create_all`, so
nothing here otherwise exercises the migrations. That is how the graph came to
have two heads and two bases without a single test going red.

These tests read revision metadata only. No database connection is opened, so
they run in the same bare environment as the rest of the suite.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from scripts.check_migration_graph import load_script_directory

BACKEND_ROOT = Path(__file__).resolve().parent.parent
VERSIONS_DIR = BACKEND_ROOT / "alembic" / "versions"


@pytest.fixture(scope="module")
def script():
    return load_script_directory()


def test_graph_has_exactly_one_head(script):
    """`alembic upgrade head` cannot resolve a target when there are several.

    This is the failure that made a fresh local setup impossible:

        FAILED: Multiple head revisions are present for given argument 'head'
    """
    heads = list(script.get_heads())

    assert len(heads) == 1, (
        f"Expected 1 head, found {len(heads)}: {sorted(heads)}. "
        "Rebase your revision onto the current head, or add a merge revision "
        "with `alembic merge -m '...' heads`."
    )


def test_graph_has_exactly_one_base(script):
    """A revision with `down_revision = None` becomes a second root.

    Alembic still runs it, but its position is decided by the topological sort
    rather than by a declared dependency, so a revision that alters a table can
    be ordered before the revision that creates it.
    """
    bases = list(script.get_bases())

    assert len(bases) == 1, (
        f"Expected 1 base, found {len(bases)}: {sorted(bases)}. "
        "Set `down_revision` to the revision this one actually depends on "
        "instead of leaving it as None."
    )


def test_every_revision_is_reachable_from_head(script):
    """A revision no head can reach never runs.

    Usually the sign of a typo in `down_revision`, or of a revision renamed
    without its children being updated.
    """
    heads = list(script.get_heads())
    reachable = {rev.revision for rev in script.iterate_revisions(heads, "base")}
    on_disk = {rev.revision for rev in script.walk_revisions()}

    assert on_disk == reachable, (
        f"Unreachable revisions: {sorted(on_disk - reachable)}. "
        "These are on disk but no head descends from them, so they never run."
    )


def test_revision_ids_are_unique(script):
    """Two files claiming the same revision id silently shadow one another."""
    seen: dict[str, list[str]] = {}

    for rev in script.walk_revisions():
        seen.setdefault(rev.revision, []).append(Path(rev.path).name)

    duplicates = {rev: files for rev, files in seen.items() if len(files) > 1}

    assert not duplicates, f"Duplicate revision ids: {duplicates}"


def test_advanced_project_filters_runs_after_projects_exists():
    """Regression guard for the orphaned second base.

    523764cd8096 alters `projects`; 3d3fd43150c1 creates it. The dependency was
    previously unrecorded, which left the ordering up to the topological sort.
    """
    script_dir = load_script_directory()
    revision = script_dir.get_revision("523764cd8096")

    ancestors = {
        rev.revision for rev in script_dir.iterate_revisions(revision.revision, "base")
    }

    assert "3d3fd43150c1" in ancestors, (
        "523764cd8096 adds columns to `projects` but does not descend from "
        "3d3fd43150c1, the revision that creates the table."
    )


def test_no_revision_drops_an_unnamed_constraint():
    """`op.drop_constraint(None, ...)` cannot compile.

    Postgres accepts an unnamed `ADD UNIQUE` on the way up and generates a name
    itself, so the problem only surfaces on downgrade:

        CompileError: Can't emit DROP CONSTRAINT for constraint
        UniqueConstraint(); it has no name
    """
    offenders = []

    for path in sorted(VERSIONS_DIR.glob("*.py")):
        source = path.read_text(encoding="utf-8")
        if (
            "op.drop_constraint(None" in source
            or "op.create_unique_constraint(None" in source
        ):
            offenders.append(path.name)

    assert not offenders, (
        f"These revisions create or drop a constraint with a name of None: "
        f"{offenders}. Name the constraint explicitly so the downgrade can "
        "compile."
    )
