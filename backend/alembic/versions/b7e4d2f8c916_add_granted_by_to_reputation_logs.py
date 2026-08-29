"""add granted_by_id to reputation_logs

``ReputationLog`` recorded who *received* points and had no column for who
granted them, so a manual adjustment could not be attributed to anyone.
``granted_by_id`` is nullable: entries the platform awards itself have no human
actor, and neither does any row that already exists.

``reputation_logs`` is also one of the tables that ``app/models`` declares and
no migration ever created -- see #1235 -- so ``alembic upgrade head`` produces a
database without it, and an unconditional ``ALTER TABLE`` here fails with
``relation "reputation_logs" does not exist``. This migration therefore creates
the table when it is absent and only adds the column when it is already there.
That is a little more than the title promises, but a migration that cannot run
against a migrated database is not a migration -- and it means ``downgrade``
drops the table, since no earlier revision has it.

Revision ID: b7e4d2f8c916
Revises: 1c63e6c28cf8
Create Date: 2026-08-26 17:30:00.000000

"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy import inspect
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "b7e4d2f8c916"
down_revision = "1c63e6c28cf8"
branch_labels = None
depends_on = None

TABLE = "reputation_logs"
COLUMN = "granted_by_id"
INDEX = "ix_reputation_logs_granted_by_id"


def _table_exists(bind) -> bool:
    return TABLE in inspect(bind).get_table_names()


def _column_exists(bind) -> bool:
    return COLUMN in {c["name"] for c in inspect(bind).get_columns(TABLE)}


def _create_table() -> None:
    """Create ``reputation_logs`` in the shape ``app/models/reputation.py`` declares."""
    op.create_table(
        TABLE,
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            nullable=False,
        ),
        sa.Column(
            "user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("action", sa.String(length=50), nullable=False),
        sa.Column("points", sa.Integer(), nullable=False),
        sa.Column("description", sa.String(length=255), nullable=True),
        sa.Column(
            COLUMN,
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
    )
    op.create_index("ix_reputation_logs_user_id", TABLE, ["user_id"])
    op.create_index("ix_reputation_logs_action", TABLE, ["action"])
    op.create_index(INDEX, TABLE, [COLUMN])


def _add_column(bind) -> None:
    op.add_column(
        TABLE,
        sa.Column(COLUMN, postgresql.UUID(as_uuid=True), nullable=True),
    )
    op.create_index(INDEX, TABLE, [COLUMN])

    # SQLite cannot add a foreign key to an existing table with ALTER, and the
    # test database is SQLite. The constraint is skipped there; the column and
    # the index -- which is what queries need -- are created either way.
    if bind.dialect.name == "postgresql":
        op.create_foreign_key(
            "fk_reputation_logs_granted_by_id_users",
            TABLE,
            "users",
            [COLUMN],
            ["id"],
            ondelete="SET NULL",
        )


def upgrade() -> None:
    bind = op.get_bind()

    if not _table_exists(bind):
        _create_table()
        return

    if not _column_exists(bind):
        _add_column(bind)


def downgrade() -> None:
    """Drop the table.

    No earlier revision knows about ``reputation_logs`` -- the model was added
    without a migration -- so the state this reverts to is one where the table
    does not exist, and dropping it is the honest inverse. Leaving it behind
    also breaks ``alembic downgrade base``: its foreign key to ``users`` blocks
    ``DROP TABLE users`` further down the chain.

    Reputation history is lost on downgrade, which is what "downgrade past the
    revision that introduced the table" means. Take a backup first.
    """
    bind = op.get_bind()

    if not _table_exists(bind):
        return

    op.drop_table(TABLE)
