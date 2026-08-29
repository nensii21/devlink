"""add user_email_verified to the auditaction enum

An administrator marking an address verified without a confirmation token is a
distinct event from the account being activated, and it is the one that decides
whether the verified badge renders. It needs its own value rather than being
folded into ``user_activated``.

Revision ID: a3f7c1d29b48
Revises: 1c63e6c28cf8
Create Date: 2026-08-26 16:40:00.000000

"""

from alembic import op

# revision identifiers, used by Alembic.
revision = "a3f7c1d29b48"
down_revision = "1c63e6c28cf8"
branch_labels = None
depends_on = None


ENUM_NAME = "auditaction"
NEW_VALUE = "user_email_verified"


def upgrade() -> None:
    bind = op.get_bind()

    # SQLite (the test database) has no enum types -- the column is a VARCHAR
    # with a CHECK constraint that SQLAlchemy renders from the Python enum, so
    # there is nothing to alter and nothing to guard against.
    if bind.dialect.name != "postgresql":
        return

    # ALTER TYPE ... ADD VALUE cannot run inside a transaction block on
    # PostgreSQL below 12, and alembic wraps migrations in one. IF NOT EXISTS
    # additionally makes this safe to re-run against a database where the value
    # was already added by an autogenerate pass.
    with op.get_context().autocommit_block():
        op.execute(f"ALTER TYPE {ENUM_NAME} ADD VALUE IF NOT EXISTS '{NEW_VALUE}'")


def downgrade() -> None:
    # PostgreSQL has no ALTER TYPE ... DROP VALUE. Removing it would mean
    # recreating the type and rewriting every column that uses it, which would
    # fail anyway for any row already carrying the value. Leaving an unused
    # label in place is harmless.
    pass
