"""add unique constraint for applications

Revision ID: 398a2154b3d5
Revises: add_unique_constraint_applicant_project
Create Date: 2026-07-09 21:40:36.723685

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "398a2154b3d5"
down_revision: Union[str, Sequence[str], None] = "c14aa06f723a"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_unique_constraint(
        "uq_applicant_project",
        "applications",
        ["applicant_id", "project_id"],
    )


def downgrade() -> None:
    op.drop_constraint(
        "uq_applicant_project",
        "applications",
        type_="unique",
    )
