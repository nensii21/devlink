"""add organization member roles

Revision ID: 622221f708e8
Revises: d4e5f6a7b8c9
Create Date: 2026-08-11 12:10:45.222215

"""

from typing import Sequence, Union

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "622221f708e8"
down_revision: Union[str, Sequence[str], None] = "d4e5f6a7b8c9"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    with op.get_context().autocommit_block():
        op.execute("ALTER TYPE orgmemberrole ADD VALUE IF NOT EXISTS 'recruiter'")
        op.execute("ALTER TYPE orgmemberrole ADD VALUE IF NOT EXISTS 'maintainer'")

    op.create_index(
        "idx_organization_members_org_role",
        "organization_members",
        ["organization_id", "role"],
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index(
        "idx_organization_members_org_role", table_name="organization_members"
    )
