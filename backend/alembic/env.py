from logging.config import fileConfig

from alembic import context
from sqlalchemy import engine_from_config
from sqlalchemy import pool

from app.core.config import settings
from app.database.base import Base

# Import every model here
from app.models.user import User
from app.models.project import Project
from app.models.skill import Skill
from app.models.user_skill import UserSkill
from app.models.project_skill import ProjectSkill
from app.models.project_member import ProjectMember
from app.models.builder_flare import BuilderFlare
from app.models.application import Application
from app.models.conversation import Conversation
from app.models.conversation_member import ConversationMember
from app.models.message import Message
from app.models.notification import Notification
from app.models.repository import Repository
from app.models.follower import Follower
from app.models.bookmark import Bookmark
from app.models.organization import Organization
from app.models.activity import Activity
from app.models.refresh_token import RefreshToken
from app.models.audit_log import AuditLog

config = context.config

config.set_main_option(
    "sqlalchemy.url",
    settings.DATABASE_URL,
)

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata


def run_migrations_offline():

    context.configure(
        url=settings.DATABASE_URL,
        target_metadata=target_metadata,
        literal_binds=True,
        compare_type=True,
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online():

    connectable = engine_from_config(
        config.get_section(config.config_ini_section),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:

        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            compare_type=True,
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()

else:
    run_migrations_online()
