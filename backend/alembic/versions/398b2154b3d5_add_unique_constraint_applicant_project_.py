"""add_unique_constraint_applicant_project_status

Revision ID: 398b2154b3d5
Revises: 1003a1b2c3d4
Create Date: 2026-08-25 22:38:30.909878

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '398b2154b3d5'
down_revision: Union[str, Sequence[str], None] = '1003a1b2c3d4'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Drop old unique constraint on (applicant_id, project_id)
    op.drop_constraint(
        "uq_applicant_project",
        "applications",
        type_="unique",
    )
    # Create new unique constraint on (applicant_id, project_id, status)
    op.create_unique_constraint(
        "uq_applicant_project_status",
        "applications",
        ["applicant_id", "project_id", "status"],
    )


def downgrade() -> None:
    """Downgrade schema."""
    # Drop new unique constraint
    op.drop_constraint(
        "uq_applicant_project_status",
        "applications",
        type_="unique",
    )
    # Recreate old unique constraint
    op.create_unique_constraint(
        "uq_applicant_project",
        "applications",
        ["applicant_id", "project_id"],
    )