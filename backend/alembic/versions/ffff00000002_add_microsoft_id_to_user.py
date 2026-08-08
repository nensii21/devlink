"""Add microsoft_id to user

Revision ID: ffff00000002
Revises: ffff00000001
Create Date: 2026-08-03

The unique constraint was originally created and dropped with a name of None.
Postgres tolerates that on the way up -- `ALTER TABLE ... ADD UNIQUE (col)`
is valid and the server names the constraint `users_microsoft_id_key` -- but
the way back down fails to compile at all:

    sqlalchemy.exc.CompileError: Can't emit DROP CONSTRAINT for constraint
    UniqueConstraint(); it has no name

Naming it explicitly fixes the downgrade. The name chosen is exactly the one
Postgres already generated, so databases that applied this revision before the
fix drop the constraint they actually have.

"""

from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = "ffff00000002"
down_revision: Union[str, Sequence[str], None] = "ffff00000001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


UNIQUE_CONSTRAINT_NAME = "users_microsoft_id_key"


def upgrade() -> None:
    op.add_column(
        "users", sa.Column("microsoft_id", sa.String(length=100), nullable=True)
    )
    op.create_unique_constraint(UNIQUE_CONSTRAINT_NAME, "users", ["microsoft_id"])


def downgrade() -> None:
    op.drop_constraint(UNIQUE_CONSTRAINT_NAME, "users", type_="unique")
    op.drop_column("users", "microsoft_id")
