# Working with Database Migrations

DevLink uses [Alembic](https://alembic.sqlalchemy.org/) for schema migrations.
Revisions live in `backend/alembic/versions/` and Postgres is the only
supported target — several revisions use Postgres-specific types (`JSONB`,
enums) and `ALTER TYPE`.

## Running migrations

```bash
cd backend
alembic upgrade head        # bring a database up to the latest revision
alembic downgrade base      # tear it all the way back down
alembic current             # what this database has applied
alembic heads               # the tip(s) of the revision graph
alembic history             # the full graph
```

`DATABASE_URL` comes from your `.env`. To point at a throwaway database for a
one-off run, set it inline:

```bash
DATABASE_URL="postgresql+psycopg://devlink@127.0.0.1:5432/scratch" alembic upgrade head
```

## The one rule: rebase onto the current head

Alembic revisions form a linked list. Each one records the revision it builds
on in `down_revision`, and a revision nobody builds on is a **head**.

`alembic upgrade head` refuses to run when there is more than one head:

```
FAILED: Multiple head revisions are present for given argument 'head';
please specify a specific target revision, '<branchname>@head' to narrow to a
specific head, or 'heads' for all heads
```

This happens whenever two people write a revision at the same time. Both set
`down_revision` to whatever was tip when they started, the graph forks, and
whoever merges second leaves `main` in a state where no one can set up a
database.

So, before you open a pull request that adds a revision:

```bash
git fetch origin main
git rebase origin/main
cd backend
alembic heads               # should print exactly one revision
```

If your revision is now behind, edit its `down_revision` to point at the
current head and re-run the check.

### If two heads are already on main

Do not rewrite anyone's `down_revision` — that changes history for databases
that already applied it. Add a merge revision instead:

```bash
cd backend
alembic merge -m "merge <topic> heads" heads
```

A merge revision has no `op.*` calls. It exists only to give the two branches a
common descendant, which is what makes it safe to apply to a database that has
already run either side.

## Things that bite

### Never leave `down_revision = None`

That makes your revision a second **base** — a second root of the graph rather
than a link in the chain. Alembic still runs it, but its position is decided by
the topological sort rather than by a declared dependency. A revision that
alters a table can end up ordered before the revision that creates it, and it
will fail on a fresh database while appearing to work on yours.

`523764cd8096` shipped this way. It adds five columns to `projects` without
declaring that `3d3fd43150c1` (which creates the table) must run first.

### Name every constraint

```python
op.create_unique_constraint(None, "users", ["microsoft_id"])   # don't
op.drop_constraint(None, "users", type_="unique")              # cannot compile
```

Postgres accepts an unnamed `ADD UNIQUE` on the way up and invents a name, so
the problem only shows up on downgrade:

```
CompileError: Can't emit DROP CONSTRAINT for constraint UniqueConstraint();
it has no name
```

Pass a name explicitly. If you are fixing an existing revision, use the name
Postgres would have generated — `<table>_<column>_key` — so databases that
already applied it drop the constraint they actually have.

### Watch for parallel branches that touch the same table

Two revisions on different branches can each be correct and still be
incompatible. `d87970cbb1e6` drops five columns from `activities`;
`e1d173dca5be`, on a sibling branch, creates indexes on those same columns.
Both orderings failed.

When your revision depends on one from another branch but should not be its
child, use `depends_on`:

```python
down_revision = "7a9e8f1d2c3b"
depends_on = ("e1d173dca5be",)
```

That constrains the ordering without changing the parentage.

### Drop enum types after the tables that use them

```python
op.drop_table("hackathon_scores")
op.execute("DROP TYPE IF EXISTS submissionstatus")   # too early
```

`submissionstatus` is the status column of `hackathon_submissions`, which is
dropped later, so this raises `cannot drop type submissionstatus because other
objects depend on it`. Drop the type after the last table that references it.

## What CI checks

`.github/workflows/migrations.yml` runs on any PR that touches
`backend/alembic/` or `backend/app/models/`:

1. `python -m scripts.check_migration_graph` — asserts exactly one head,
   exactly one base, and no revision unreachable from head. No database needed,
   so it fails fast with a readable message.
2. `alembic upgrade head` against a real Postgres 16 service, then a sanity
   check that the expected tables exist, then `alembic downgrade base`.

You can run the first locally at any time:

```bash
cd backend
python -m scripts.check_migration_graph --verbose
```

The same assertions are also covered by `backend/tests/test_migration_graph.py`,
so they run as part of the normal test suite.

## Known limitation

`alembic downgrade base` drops every table but leaves the enum types behind —
14 of them at the time of writing (`projectstage`, `activitytype`,
`auditaction`, and so on). Most revisions create their enums implicitly via
`sa.Enum(...)` in a `create_table` and never drop them.

The practical effect is that upgrading a database that has been downgraded to
base fails with `type "projectstage" already exists`. Drop and recreate the
database instead of reusing it:

```bash
dropdb devlink && createdb devlink && alembic upgrade head
```
