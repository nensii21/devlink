"""Structural checks on the Alembic revision graph.

The graph has broken twice in the same two ways, and both times it went
unnoticed until someone tried to set up a fresh database:

  * More than one head. `alembic upgrade head` refuses to guess which head you
    meant and exits non-zero, so local setup and any deploy step that runs it
    both fail. This happens whenever two branches are authored in parallel and
    neither rebases onto the other's revision.

  * More than one base. A revision authored with `down_revision = None` becomes
    a second root instead of a link in the chain. Alembic still runs it, but
    its position in the ordering is whatever the topological sort produces --
    so a revision that alters a table can land before the revision that creates
    it, and only on some runs.

Neither is caught by the test suite, because the tests build their schema with
`Base.metadata.create_all` rather than by running migrations. Hence this check.

It reads the versions directory directly and never opens a database
connection, so it is cheap enough to run in CI on every pull request.

Usage:
    python -m scripts.check_migration_graph
    python -m scripts.check_migration_graph --verbose

Exits 0 when the graph is linear-enough (exactly one head, exactly one base)
and 1 otherwise, printing the offending revisions.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from alembic.config import Config
from alembic.script import ScriptDirectory
from alembic.util.exc import CommandError as AlembicError

BACKEND_ROOT = Path(__file__).resolve().parent.parent
ALEMBIC_INI = BACKEND_ROOT / "alembic.ini"


def load_script_directory() -> ScriptDirectory:
    """Build a ScriptDirectory without touching settings or the database.

    `alembic/env.py` imports the application settings, which in turn wants a
    DATABASE_URL. None of that is needed to read revision metadata, so the
    config is constructed directly from alembic.ini and the script location is
    resolved relative to the backend root. That keeps the check runnable in a
    bare CI container with no services started.
    """
    config = Config(str(ALEMBIC_INI))

    script_location = config.get_main_option("script_location") or "alembic"
    config.set_main_option(
        "script_location",
        str((BACKEND_ROOT / script_location).resolve()),
    )

    return ScriptDirectory.from_config(config)


def describe(script: ScriptDirectory, revision: str) -> str:
    """Render `<revision> (<file name>) - <message>` for an error listing."""
    try:
        rev = script.get_revision(revision)
    except AlembicError:  # pragma: no cover - only hit on an unresolvable id
        return revision

    file_name = Path(rev.path).name if rev.path else "<unknown file>"
    message = (rev.doc or "").strip().splitlines()
    summary = message[0] if message else "<no message>"

    return f"{revision} ({file_name}) - {summary}"


def check_single_head(script: ScriptDirectory, errors: list[str]) -> list[str]:
    heads = list(script.get_heads())

    if len(heads) > 1:
        listing = "\n".join(f"    {describe(script, h)}" for h in sorted(heads))
        errors.append(
            f"Found {len(heads)} heads, expected 1:\n{listing}\n"
            "\n"
            "    `alembic upgrade head` cannot resolve a target while more than\n"
            "    one head exists. Rebase your revision onto the current head, or\n"
            "    if both branches are already merged upstream, run:\n"
            "\n"
            "        alembic merge -m 'merge <topic> heads' heads\n"
        )

    return heads


def check_single_base(script: ScriptDirectory, errors: list[str]) -> list[str]:
    bases = list(script.get_bases())

    if len(bases) > 1:
        listing = "\n".join(f"    {describe(script, b)}" for b in sorted(bases))
        errors.append(
            f"Found {len(bases)} bases, expected 1:\n{listing}\n"
            "\n"
            "    A revision with `down_revision = None` starts a second root of\n"
            "    the graph, so its position in the run order is whatever the\n"
            "    topological sort happens to produce. Set `down_revision` to the\n"
            "    revision it actually depends on.\n"
        )

    return bases


def check_reachable(
    script: ScriptDirectory, heads: list[str], errors: list[str]
) -> None:
    """Every revision on disk should be an ancestor of some head.

    A revision that is not reachable from any head never runs. That usually
    means a `down_revision` was typo'd or a revision was renamed without its
    children being updated, and the symptom is a migration that silently does
    nothing.
    """
    if not heads:
        return

    reachable = {rev.revision for rev in script.iterate_revisions(heads, "base")}
    on_disk = {rev.revision for rev in script.walk_revisions()}

    orphans = on_disk - reachable
    if orphans:
        listing = "\n".join(f"    {describe(script, o)}" for o in sorted(orphans))
        errors.append(
            f"Found {len(orphans)} revision(s) unreachable from any head:\n{listing}\n"
            "\n"
            "    These never run. Check for a typo in `down_revision`, or for a\n"
            "    revision that was renamed without updating its children.\n"
        )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Verify the Alembic revision graph has one head and one base."
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Print the resolved head, base, and revision count on success.",
    )
    args = parser.parse_args(argv)

    script = load_script_directory()
    errors: list[str] = []

    heads = check_single_head(script, errors)
    bases = check_single_base(script, errors)
    check_reachable(script, heads, errors)

    if errors:
        print("Alembic revision graph check failed.\n", file=sys.stderr)
        for error in errors:
            print(error, file=sys.stderr)
        return 1

    if args.verbose:
        total = sum(1 for _ in script.walk_revisions())
        print(f"head:      {heads[0] if heads else '<none>'}")
        print(f"base:      {bases[0] if bases else '<none>'}")
        print(f"revisions: {total}")

    print("Alembic revision graph OK: 1 head, 1 base, no unreachable revisions.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
