"""Add case-insensitive normalized skill names.

Existing case/whitespace variants are merged before the unique index is added.
User and project associations are repointed to the earliest skill record.
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

from app.utils.skill_names import clean_skill_name, normalize_skill_name

revision: str = "7a9e8f1d2c3b"
down_revision: Union[str, Sequence[str], None] = "398a2154b3d5"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    columns = {column["name"] for column in inspector.get_columns("skills")}
    if "normalized_name" not in columns:
        op.add_column(
            "skills", sa.Column("normalized_name", sa.String(100), nullable=True)
        )

    rows = bind.execute(
        sa.text("SELECT id, name FROM skills ORDER BY created_at, id")
    ).fetchall()
    canonical: dict[str, object] = {}
    for skill_id, name in rows:
        display_name = clean_skill_name(name)
        normalized_name = normalize_skill_name(display_name)
        winner = canonical.get(normalized_name)
        if winner is None:
            canonical[normalized_name] = skill_id
            bind.execute(
                sa.text(
                    "UPDATE skills SET name = :name, normalized_name = :normalized_name "
                    "WHERE id = :id"
                ),
                {
                    "id": skill_id,
                    "name": display_name,
                    "normalized_name": normalized_name,
                },
            )
            continue

        for table in ("user_skills", "project_skills"):
            owner_column = "user_id" if table == "user_skills" else "project_id"
            bind.execute(
                sa.text(
                    f"DELETE FROM {table} AS duplicate "
                    f"WHERE duplicate.skill_id = :duplicate AND EXISTS ("
                    f"SELECT 1 FROM {table} AS winner "
                    f"WHERE winner.skill_id = :winner "
                    f"AND winner.{owner_column} = duplicate.{owner_column})"
                ),
                {"winner": winner, "duplicate": skill_id},
            )
            bind.execute(
                sa.text(
                    f"UPDATE {table} SET skill_id = :winner WHERE skill_id = :duplicate"
                ),
                {"winner": winner, "duplicate": skill_id},
            )
        bind.execute(sa.text("DELETE FROM skills WHERE id = :id"), {"id": skill_id})

    op.alter_column("skills", "normalized_name", nullable=False)
    if not any(
        index["name"] == "ix_skills_normalized_name"
        for index in sa.inspect(bind).get_indexes("skills")
    ):
        op.create_index(
            "ix_skills_normalized_name", "skills", ["normalized_name"], unique=True
        )


def downgrade() -> None:
    op.drop_index("ix_skills_normalized_name", table_name="skills")
    op.drop_column("skills", "normalized_name")
