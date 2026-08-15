"""create testimonials table

Revision ID: d9e2b7c4f183
Revises: d4e5f6a7b8c9
Create Date: 2026-08-10 21:35:00.000000

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql
from sqlalchemy.dialects.postgresql import UUID

# revision identifiers, used by Alembic.
revision: str = "d9e2b7c4f183"
down_revision: Union[str, Sequence[str], None] = "d4e5f6a7b8c9"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

# create_type=False: the types are created explicitly in upgrade() with
# checkfirst, so create_table must not try to emit CREATE TYPE a second time.
relationship_enum = postgresql.ENUM(
    "COLLABORATOR",
    "MENTOR",
    "MENTEE",
    "CLIENT",
    "TEAMMATE",
    name="testimonialrelationship",
    create_type=False,
)
status_enum = postgresql.ENUM(
    "PENDING",
    "APPROVED",
    "HIDDEN",
    name="testimonialstatus",
    create_type=False,
)


def upgrade() -> None:
    bind = op.get_bind()
    relationship_enum.create(bind, checkfirst=True)
    status_enum.create(bind, checkfirst=True)

    op.create_table(
        "testimonials",
        sa.Column("id", UUID(as_uuid=True), nullable=False),
        # Who it is about.
        sa.Column("subject_id", UUID(as_uuid=True), nullable=False),
        # Who wrote it.
        sa.Column("author_id", UUID(as_uuid=True), nullable=False),
        # The collaboration it came out of. SET NULL because the testimonial is
        # about the person, not the project.
        sa.Column("project_id", UUID(as_uuid=True), nullable=True),
        sa.Column("relationship", relationship_enum, nullable=False),
        sa.Column("body", sa.Text(), nullable=False),
        sa.Column("status", status_enum, nullable=False),
        sa.Column(
            "is_featured", sa.Boolean(), server_default=sa.text("false"), nullable=False
        ),
        # When the subject last approved or hid it.
        sa.Column("responded_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["subject_id"], ["users.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["author_id"], ["users.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["project_id"], ["projects.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
        # One testimonial per author per subject. Someone with an opinion worth
        # stating twice can edit the one they already wrote.
        sa.UniqueConstraint(
            "author_id", "subject_id", name="uq_testimonials_author_subject"
        ),
        # Nobody writes a testimonial about themselves.
        sa.CheckConstraint("author_id <> subject_id", name="ck_testimonials_not_self"),
    )

    op.create_index(
        op.f("ix_testimonials_subject_id"), "testimonials", ["subject_id"], unique=False
    )
    op.create_index(
        op.f("ix_testimonials_author_id"), "testimonials", ["author_id"], unique=False
    )
    op.create_index(
        op.f("ix_testimonials_project_id"), "testimonials", ["project_id"], unique=False
    )
    op.create_index(
        op.f("ix_testimonials_status"), "testimonials", ["status"], unique=False
    )

    # The public profile listing: one subject's approved testimonials.
    op.create_index(
        "ix_testimonials_subject_status",
        "testimonials",
        ["subject_id", "status"],
        unique=False,
    )
    # The author's own "what have I written" view.
    op.create_index(
        "ix_testimonials_author_created",
        "testimonials",
        ["author_id", "created_at"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("ix_testimonials_author_created", table_name="testimonials")
    op.drop_index("ix_testimonials_subject_status", table_name="testimonials")
    op.drop_index(op.f("ix_testimonials_status"), table_name="testimonials")
    op.drop_index(op.f("ix_testimonials_project_id"), table_name="testimonials")
    op.drop_index(op.f("ix_testimonials_author_id"), table_name="testimonials")
    op.drop_index(op.f("ix_testimonials_subject_id"), table_name="testimonials")
    op.drop_table("testimonials")

    bind = op.get_bind()
    status_enum.drop(bind, checkfirst=True)
    relationship_enum.drop(bind, checkfirst=True)
