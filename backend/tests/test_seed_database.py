"""Tests for the development database seeder.

The two properties that matter are idempotency and determinism. Both are easy
to break by accident and neither is obvious from reading the code -- the first
version of this seeder used a single sequential RNG and looked completely
correct, but a second run produced 144 extra rows because the existence checks
skipped random draws and shifted every later one along.
"""

from __future__ import annotations

import pytest
from sqlalchemy import func, select

from app.models.application import Application
from app.models.bookmark import Bookmark
from app.models.builder_flare import BuilderFlare
from app.models.conversation import Conversation
from app.models.message import Message
from app.models.notification import Notification
from app.models.project import Project
from app.models.project_member import ProjectMember
from app.models.skill import Skill
from app.models.user import User
from app.models.user_skill import UserSkill
from scripts.seed_database import (
    DEMO_PASSWORD,
    SEED_MARKER,
    Seeder,
    build_parser,
    reset_seed_data,
    slugify,
)

SEEDED_MODELS = [
    User,
    Skill,
    UserSkill,
    Project,
    ProjectMember,
    BuilderFlare,
    Application,
    Conversation,
    Message,
    Notification,
    Bookmark,
]


def row_counts(db) -> dict[str, int]:
    return {
        model.__name__: db.scalar(select(func.count()).select_from(model))
        for model in SEEDED_MODELS
    }


def seed(db, *, users: int = 6, projects: int = 5) -> None:
    Seeder(db, user_count=users, project_count=projects, quiet=True).run()
    db.commit()


class TestSeeding:
    def test_populates_every_table_it_claims_to(self, db):
        seed(db)

        counts = row_counts(db)

        for name, count in counts.items():
            assert count > 0, f"{name} is still empty after seeding"

    def test_creates_the_requested_number_of_users_plus_admin(self, db):
        seed(db, users=6)

        # Six demo users plus the superuser.
        assert db.scalar(select(func.count()).select_from(User)) == 7

    def test_creates_a_superuser_with_the_documented_credentials(self, db):
        seed(db)

        admin = db.scalar(select(User).where(User.email == "admin@example.com"))

        assert admin is not None
        assert admin.is_superuser is True
        assert admin.system_role == "admin"
        assert admin.password_hash

    def test_every_project_has_an_owner_member_row(self, db):
        seed(db)

        for project in db.scalars(select(Project)):
            owner_row = db.scalar(
                select(ProjectMember).where(
                    ProjectMember.project_id == project.id,
                    ProjectMember.user_id == project.owner_id,
                )
            )
            assert owner_row is not None, f"{project.slug} has no owner member row"

    def test_seeded_rows_carry_the_marker(self, db):
        seed(db)

        for user in db.scalars(select(User).where(User.bio.isnot(None))):
            assert SEED_MARKER in user.bio

        for project in db.scalars(select(Project)):
            assert SEED_MARKER in project.description

    def test_applications_reference_a_flare_on_the_same_project(self, db):
        seed(db)

        for application in db.scalars(select(Application)):
            flare = db.get(BuilderFlare, application.flare_id)

            assert flare is not None
            assert flare.project_id == application.project_id

    def test_every_conversation_has_at_least_two_messages(self, db):
        seed(db)

        for conversation in db.scalars(select(Conversation)):
            count = db.scalar(
                select(func.count())
                .select_from(Message)
                .where(Message.conversation_id == conversation.id)
            )
            assert count >= 2


class TestIdempotency:
    def test_second_run_adds_nothing(self, db):
        seed(db)
        after_first = row_counts(db)

        seed(db)
        after_second = row_counts(db)

        assert after_second == after_first

    def test_third_run_still_adds_nothing(self, db):
        """Two runs can agree by luck; three is a real check on convergence."""
        seed(db)
        seed(db)
        baseline = row_counts(db)

        seed(db)

        assert row_counts(db) == baseline

    def test_rerunning_does_not_duplicate_a_user(self, db):
        seed(db)
        seed(db)

        emails = list(db.scalars(select(User.email)))

        assert len(emails) == len(set(emails))

    def test_rerunning_does_not_duplicate_a_project_slug(self, db):
        seed(db)
        seed(db)

        slugs = list(db.scalars(select(Project.slug)))

        assert len(slugs) == len(set(slugs))


class TestDeterminism:
    def test_same_inputs_produce_the_same_ids(self, db):
        """Two contributors running the same command get the same database."""
        seed(db, users=6, projects=5)
        first_ids = sorted(str(uid) for uid in db.scalars(select(User.id)))
        first_slugs = sorted(db.scalars(select(Project.slug)))

        reset_seed_data(db, quiet=True)
        db.commit()

        seed(db, users=6, projects=5)

        assert sorted(str(uid) for uid in db.scalars(select(User.id))) == first_ids
        assert sorted(db.scalars(select(Project.slug))) == first_slugs

    def test_same_inputs_produce_the_same_profile_content(self, db):
        seed(db, users=6, projects=5)
        before = {
            user.email: (user.headline, user.location, user.role)
            for user in db.scalars(select(User))
        }

        reset_seed_data(db, quiet=True)
        db.commit()
        seed(db, users=6, projects=5)

        after = {
            user.email: (user.headline, user.location, user.role)
            for user in db.scalars(select(User))
        }

        assert after == before


class TestReset:
    def test_removes_seeded_users_and_projects(self, db):
        seed(db)
        assert db.scalar(select(func.count()).select_from(Project)) > 0

        reset_seed_data(db, quiet=True)
        db.commit()

        assert db.scalar(select(func.count()).select_from(Project)) == 0
        assert db.scalar(select(func.count()).select_from(User)) == 0

    def test_cascades_to_dependent_rows(self, db):
        seed(db)

        reset_seed_data(db, quiet=True)
        db.commit()

        for model in (ProjectMember, BuilderFlare, Application, Message, Bookmark):
            remaining = db.scalar(select(func.count()).select_from(model))
            assert remaining == 0, f"{model.__name__} survived the reset"

    def test_leaves_hand_created_rows_alone(self, db):
        """`--reset` must not be a `TRUNCATE` in disguise."""
        mine = User(
            email="real.person@example.com",
            username="realperson",
            first_name="Real",
            last_name="Person",
            password_hash="not-a-real-hash",
            bio="I wrote this row myself.",
        )
        db.add(mine)
        db.commit()

        seed(db)
        reset_seed_data(db, quiet=True)
        db.commit()

        survivor = db.scalar(
            select(User).where(User.email == "real.person@example.com")
        )

        assert survivor is not None

    def test_reset_then_seed_restores_the_same_counts(self, db):
        seed(db)
        before = row_counts(db)

        reset_seed_data(db, quiet=True)
        db.commit()
        seed(db)

        assert row_counts(db) == before


class TestSkillsAreShared:
    def test_skills_are_not_duplicated_per_user(self, db):
        seed(db)

        names = list(db.scalars(select(Skill.normalized_name)))

        assert len(names) == len(set(names))


class TestArgumentParsing:
    def test_defaults(self):
        args = build_parser().parse_args([])

        assert args.users > 0
        assert args.projects > 0
        assert args.reset is False
        assert args.dry_run is False
        assert args.force is False

    def test_counts_are_configurable(self):
        args = build_parser().parse_args(["--users", "30", "--projects", "40"])

        assert (args.users, args.projects) == (30, 40)

    @pytest.mark.parametrize("flag", ["--reset", "--dry-run", "--quiet", "--force"])
    def test_flags_are_accepted(self, flag):
        args = build_parser().parse_args([flag])

        assert getattr(args, flag.lstrip("-").replace("-", "_")) is True


class TestSlugify:
    @pytest.mark.parametrize(
        "value,expected",
        [
            ("Open Recipe Index", "open-recipe-index"),
            ("Air Quality Map", "air-quality-map"),
            ("Repo  Health   Report", "repo-health-report"),
            ("Node.js Tools", "node-js-tools"),
            ("  Leading and trailing  ", "leading-and-trailing"),
        ],
    )
    def test_produces_url_safe_slugs(self, value, expected):
        assert slugify(value) == expected


class TestDemoPassword:
    def test_is_not_trivially_weak(self):
        """It is published in the docs, so it must not look like a real one.

        It still has to satisfy the registration rules, since a contributor
        will paste it into the login form.
        """
        assert len(DEMO_PASSWORD) >= 12
        assert any(char.isupper() for char in DEMO_PASSWORD)
        assert any(char.isdigit() for char in DEMO_PASSWORD)
        assert not DEMO_PASSWORD.isalnum()
