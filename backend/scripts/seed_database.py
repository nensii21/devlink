"""Populate a development database with realistic demo data.

Running the migrations leaves you with 50-odd empty tables, which means every
screen in the app renders its empty state: the dashboard has nothing to show,
search returns nothing, and messaging needs two users and a conversation before
it does anything at all. Reviewing a frontend change meant hand-registering
users and creating projects through the API every time the database was reset.

This fills in the core object graph so the app is usable immediately.

Usage:
    python -m scripts.seed_database
    python -m scripts.seed_database --users 30 --projects 40
    python -m scripts.seed_database --reset
    python -m scripts.seed_database --dry-run

Every demo account uses the same password, the ``DEMO_PASSWORD`` constant
below. It is deliberately not echoed at the end of a run.

Two properties worth relying on:

  * **Deterministic.** The RNG is seeded with a fixed value, so the same flags
    produce the same fixtures on every machine. Screenshots in a PR are
    comparable, and "it works on my data" stops being a thing.

  * **Idempotent.** Rows are matched on a natural key (email, slug, name) and
    updated rather than duplicated, so re-running is safe. `--reset` removes
    previously seeded rows first, identified by the marker below.

Everything it creates is tagged with SEED_MARKER, which is what makes a
targeted `--reset` possible without touching rows you created by hand.
"""

from __future__ import annotations

import argparse
import random
import sys
import uuid
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path

from sqlalchemy import delete, select
from sqlalchemy.orm import Session

# Allow `python scripts/seed_database.py` as well as `python -m scripts...`.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.core.config import settings  # noqa: E402
from app.core.security import hash_password  # noqa: E402
from app.database.session import SessionLocal  # noqa: E402
from app.models.application import Application, ApplicationStatus  # noqa: E402
from app.models.bookmark import Bookmark, BookmarkTargetType  # noqa: E402
from app.models.builder_flare import BuilderFlare, FlareStatus  # noqa: E402
from app.models.conversation import Conversation, ConversationType  # noqa: E402
from app.models.conversation_member import (  # noqa: E402
    ConversationMember,
    ConversationRole,
)
from app.models.message import Message, MessageType  # noqa: E402
from app.models.notification import (  # noqa: E402
    Notification,
    NotificationChannel,
    NotificationPriority,
    NotificationStatus,
    NotificationType,
)
from app.models.project import Project, ProjectStage, ProjectVisibility  # noqa: E402
from app.models.project_member import MemberRole, ProjectMember  # noqa: E402
from app.models.skill import Skill  # noqa: E402
from app.models.user import User  # noqa: E402
from app.models.user_skill import SkillLevel, UserSkill  # noqa: E402

# Stamped into every seeded user's bio and every seeded project's description
# so `--reset` can find them again without a dedicated column.
SEED_MARKER = "[demo]"

# Fixed, so two contributors running the same command get the same database.
RANDOM_SEED = 20260806

DEMO_PASSWORD = "DevlinkDemo!2026"

DEFAULT_USERS = 12
DEFAULT_PROJECTS = 18

# Anchor for every generated timestamp. Also fixed -- a seeder that used
# `now()` would produce a different database on every run and break the
# determinism the tests rely on.
EPOCH = datetime(2026, 8, 1, 12, 0, 0, tzinfo=timezone.utc)

FIRST_NAMES = [
    "Aditi",
    "Bruno",
    "Chen",
    "Daniela",
    "Ejiro",
    "Farah",
    "Goran",
    "Hina",
    "Ivan",
    "Jamila",
    "Kwame",
    "Lucia",
    "Mateo",
    "Nadia",
    "Omar",
    "Priya",
    "Quentin",
    "Rosa",
    "Sanjay",
    "Tomas",
    "Ulla",
    "Viktor",
    "Wen",
    "Yara",
]

LAST_NAMES = [
    "Almeida",
    "Bhatt",
    "Costa",
    "Dubois",
    "Eriksen",
    "Fontaine",
    "Gupta",
    "Haddad",
    "Ibrahim",
    "Jensen",
    "Kowalski",
    "Larsen",
    "Moreau",
    "Nakamura",
    "Okonkwo",
    "Petrov",
    "Quesada",
    "Rossi",
    "Silva",
    "Tanaka",
]

LOCATIONS = [
    "Bengaluru, IN",
    "Lisbon, PT",
    "Berlin, DE",
    "Toronto, CA",
    "Nairobi, KE",
    "São Paulo, BR",
    "Warsaw, PL",
    "Singapore, SG",
    "Austin, US",
    "Dublin, IE",
]

HEADLINES = [
    "Backend engineer who likes boring, reliable systems",
    "Frontend developer focused on accessibility",
    "Full-stack builder shipping small tools",
    "Data engineer turned product engineer",
    "Infrastructure engineer, Kubernetes wrangler",
    "Mobile developer exploring the web again",
    "Designer who codes, badly but enthusiastically",
    "Security engineer with an interest in supply chains",
]

ROLES = [
    "Backend Engineer",
    "Frontend Engineer",
    "Full-Stack Engineer",
    "DevOps Engineer",
    "Data Engineer",
    "Product Designer",
    "Mobile Engineer",
    "Security Engineer",
]

EXPERIENCE_LEVELS = ["junior", "mid", "senior", "lead"]

# (name, category) -- category feeds the skill filters on the builders page.
SKILLS = [
    ("Python", "language"),
    ("TypeScript", "language"),
    ("Go", "language"),
    ("Rust", "language"),
    ("SQL", "language"),
    ("Java", "language"),
    ("React", "frontend"),
    ("Vue", "frontend"),
    ("Tailwind CSS", "frontend"),
    ("FastAPI", "backend"),
    ("Django", "backend"),
    ("Node.js", "backend"),
    ("PostgreSQL", "database"),
    ("Redis", "database"),
    ("MongoDB", "database"),
    ("Docker", "devops"),
    ("Kubernetes", "devops"),
    ("Terraform", "devops"),
    ("GitHub Actions", "devops"),
    ("AWS", "cloud"),
    ("Figma", "design"),
    ("Accessibility", "design"),
    ("Machine Learning", "data"),
    ("Pandas", "data"),
]

PROJECT_TITLES = [
    "Open Recipe Index",
    "Transit Delay Tracker",
    "Habit Streaks",
    "Changelog Digest",
    "Local Library Finder",
    "Invoice Splitter",
    "Rainfall Dashboard",
    "Podcast Clipper",
    "Bike Route Planner",
    "Study Group Matcher",
    "Grocery Price Watch",
    "Air Quality Map",
    "Meeting Cost Timer",
    "Plant Care Reminder",
    "Ticket Triage Bot",
    "Portfolio Builder",
    "Language Exchange Board",
    "Repo Health Report",
    "Volunteer Shift Board",
    "Expense Sharing Ledger",
]

PROJECT_TAGLINES = [
    "A small tool that does one thing properly",
    "Scratching an itch that turned into a real project",
    "Weekend build that got out of hand",
    "Replacing a spreadsheet with something maintainable",
    "An excuse to learn the stack, now genuinely useful",
]

TECH_STACKS = [
    "FastAPI, PostgreSQL, React",
    "Django, Redis, HTMX",
    "Go, SQLite, Svelte",
    "Node.js, MongoDB, Next.js",
    "Rust, PostgreSQL, Tauri",
]

FLARE_ROLES = [
    ("Backend Engineer", "Own the API surface and the data model."),
    ("Frontend Engineer", "Build the dashboard and the settings screens."),
    ("Designer", "Shape the visual language and the empty states."),
    ("DevOps Engineer", "Set up CI, staging, and the deploy pipeline."),
]

MESSAGE_SNIPPETS = [
    "Hey! Saw your project, the approach to caching is interesting.",
    "Happy to help with the frontend if you still need a hand.",
    "Do you have a roadmap written down anywhere?",
    "I opened a PR for the flaky test, let me know what you think.",
    "Are you planning to support Postgres 16?",
    "That last release made a real difference to load times.",
]


@dataclass
class SeedCounts:
    """Tally of what a run inserted, updated, or skipped."""

    users: int = 0
    skills: int = 0
    user_skills: int = 0
    projects: int = 0
    members: int = 0
    flares: int = 0
    applications: int = 0
    conversations: int = 0
    messages: int = 0
    notifications: int = 0
    bookmarks: int = 0

    def total(self) -> int:
        return sum(
            (
                self.users,
                self.skills,
                self.user_skills,
                self.projects,
                self.members,
                self.flares,
                self.applications,
                self.conversations,
                self.messages,
                self.notifications,
                self.bookmarks,
            )
        )

    def render(self) -> str:
        rows = [
            ("users", self.users),
            ("skills", self.skills),
            ("user skills", self.user_skills),
            ("projects", self.projects),
            ("project members", self.members),
            ("builder flares", self.flares),
            ("applications", self.applications),
            ("conversations", self.conversations),
            ("messages", self.messages),
            ("notifications", self.notifications),
            ("bookmarks", self.bookmarks),
        ]
        width = max(len(label) for label, _ in rows)

        return "\n".join(f"  {label:<{width}}  {count:>5}" for label, count in rows)


def slugify(value: str) -> str:
    cleaned = "".join(char.lower() if char.isalnum() else "-" for char in value)

    while "--" in cleaned:
        cleaned = cleaned.replace("--", "-")

    return cleaned.strip("-")


class Seeder:
    def __init__(
        self,
        db: Session,
        *,
        user_count: int,
        project_count: int,
        quiet: bool = False,
    ) -> None:
        self.db = db
        self.user_count = user_count
        self.project_count = project_count
        self.quiet = quiet
        self.counts = SeedCounts()

    def log(self, message: str) -> None:
        if not self.quiet:
            print(message)

    def stable_uuid(self, key: str) -> uuid.UUID:
        """A UUID derived from a natural key, identical on every run."""
        return uuid.uuid5(uuid.NAMESPACE_URL, f"devlink-seed/{key}")

    def rng_for(self, key: str) -> random.Random:
        """A generator seeded from a natural key.

        One shared sequential generator is the obvious design and it is wrong
        here, because it makes the seeder non-idempotent. On a second run the
        existence checks skip work, skipping the random draws that work would
        have made, which shifts every later draw along -- so the second run
        picks different project members and different bookmarks and inserts
        them as new rows.

        Deriving a generator per entity removes the ordering dependence: the
        values a given project or user gets depend only on its own key, not on
        what happened to be created before it.
        """
        return random.Random(f"{RANDOM_SEED}/{key}")

    # ------------------------------------------------------------------
    # Users and skills
    # ------------------------------------------------------------------

    def seed_skills(self) -> list[Skill]:
        skills: list[Skill] = []

        for name, category in SKILLS:
            normalized = name.lower()
            existing = self.db.scalar(
                select(Skill).where(Skill.normalized_name == normalized)
            )

            if existing is None:
                existing = Skill(
                    id=self.stable_uuid(f"skill/{normalized}"),
                    name=name,
                    normalized_name=normalized,
                    slug=slugify(name),
                    category=category,
                )
                self.db.add(existing)
                self.counts.skills += 1

            skills.append(existing)

        self.db.flush()
        return skills

    def seed_users(self) -> list[User]:
        users: list[User] = []
        password_hash = hash_password(DEMO_PASSWORD)

        for index in range(self.user_count):
            first = FIRST_NAMES[index % len(FIRST_NAMES)]
            last = LAST_NAMES[index % len(LAST_NAMES)]
            username = f"{first.lower()}{last.lower()}"
            email = f"{username}@example.com"

            existing = self.db.scalar(select(User).where(User.email == email))

            if existing is None:
                existing = User(id=self.stable_uuid(f"user/{email}"), email=email)
                self.db.add(existing)
                self.counts.users += 1

            rng = self.rng_for(f"user/{email}")

            existing.username = username
            existing.first_name = first
            existing.last_name = last
            existing.password_hash = password_hash
            existing.headline = rng.choice(HEADLINES)
            existing.bio = (
                f"{SEED_MARKER} {first} builds things in public and is usually "
                "somewhere between two side projects."
            )
            existing.location = rng.choice(LOCATIONS)
            existing.role = rng.choice(ROLES)
            existing.experience_level = rng.choice(EXPERIENCE_LEVELS)
            existing.github_url = f"https://github.com/{username}"
            existing.open_to_work = rng.random() < 0.4
            existing.is_active = True
            existing.is_verified = True
            existing.email_verified_at = EPOCH - timedelta(days=index + 1)
            existing.last_login = EPOCH - timedelta(hours=index)

            users.append(existing)

        # A predictable superuser, so admin routes are reachable without
        # hand-editing a row.
        admin_email = "admin@example.com"
        admin = self.db.scalar(select(User).where(User.email == admin_email))

        if admin is None:
            admin = User(id=self.stable_uuid(f"user/{admin_email}"), email=admin_email)
            self.db.add(admin)
            self.counts.users += 1

        admin.username = "admin"
        admin.first_name = "Ada"
        admin.last_name = "Admin"
        admin.password_hash = password_hash
        admin.bio = f"{SEED_MARKER} Demo administrator account."
        admin.is_active = True
        admin.is_verified = True
        admin.is_superuser = True
        admin.system_role = "admin"
        users.append(admin)

        self.db.flush()
        return users

    def seed_user_skills(self, users: list[User], skills: list[Skill]) -> None:
        for user in users:
            rng = self.rng_for(f"user-skills/{user.id}")
            chosen = rng.sample(skills, k=rng.randint(3, 6))

            for skill in chosen:
                existing = self.db.scalar(
                    select(UserSkill).where(
                        UserSkill.user_id == user.id,
                        UserSkill.skill_id == skill.id,
                    )
                )

                if existing is not None:
                    continue

                self.db.add(
                    UserSkill(
                        id=self.stable_uuid(f"user-skill/{user.id}/{skill.id}"),
                        user_id=user.id,
                        skill_id=skill.id,
                        level=self.rng_for(f"user-skill/{user.id}/{skill.id}").choice(
                            list(SkillLevel)
                        ),
                        years_of_experience=self.rng_for(
                            f"user-skill-years/{user.id}/{skill.id}"
                        ).randint(1, 9),
                    )
                )
                self.counts.user_skills += 1

        self.db.flush()

    # ------------------------------------------------------------------
    # Projects, membership, flares, applications
    # ------------------------------------------------------------------

    def seed_projects(self, users: list[User]) -> list[Project]:
        projects: list[Project] = []

        for index in range(self.project_count):
            title = PROJECT_TITLES[index % len(PROJECT_TITLES)]

            # Titles repeat once the count exceeds the list, so the slug -- the
            # natural key here -- has to stay unique.
            if index >= len(PROJECT_TITLES):
                title = f"{title} {index // len(PROJECT_TITLES) + 1}"

            slug = slugify(title)
            owner = users[index % len(users)]

            existing = self.db.scalar(select(Project).where(Project.slug == slug))

            if existing is None:
                existing = Project(
                    id=self.stable_uuid(f"project/{slug}"),
                    slug=slug,
                    owner_id=owner.id,
                )
                self.db.add(existing)
                self.counts.projects += 1

            rng = self.rng_for(f"project/{slug}")

            existing.title = title
            existing.tagline = rng.choice(PROJECT_TAGLINES)
            existing.description = (
                f"{SEED_MARKER} {title} started as a small utility and grew into "
                "something worth maintaining. Looking for collaborators who enjoy "
                "well-tested code and small pull requests."
            )
            existing.stage = rng.choice(list(ProjectStage))
            existing.visibility = (
                ProjectVisibility.PRIVATE
                if rng.random() < 0.15
                else ProjectVisibility.PUBLIC
            )
            existing.tech_stack = rng.choice(TECH_STACKS)
            existing.language = rng.choice(["Python", "TypeScript", "Go", "Rust"])
            existing.experience = rng.choice(EXPERIENCE_LEVELS)
            existing.is_remote = True
            existing.is_paid = rng.random() < 0.2
            existing.is_open_source = rng.random() < 0.7
            existing.tags = rng.sample(
                ["web", "cli", "data", "devtools", "mobile", "ai", "docs"], k=3
            )
            existing.repository_url = f"https://github.com/devlink-demo/{slug}"
            existing.hiring = rng.random() < 0.6
            existing.stars = rng.randint(0, 240)
            existing.views = rng.randint(10, 3200)
            existing.is_published = True
            existing.is_featured = index < 3

            projects.append(existing)

        self.db.flush()
        return projects

    def seed_members(self, projects: list[Project], users: list[User]) -> None:
        for project in projects:
            rng = self.rng_for(f"members/{project.id}")
            others = [user for user in users if user.id != project.owner_id]
            team = [project.owner_id] + [
                user.id for user in rng.sample(others, k=rng.randint(1, 4))
            ]

            for position, user_id in enumerate(team):
                existing = self.db.scalar(
                    select(ProjectMember).where(
                        ProjectMember.project_id == project.id,
                        ProjectMember.user_id == user_id,
                    )
                )

                if existing is not None:
                    continue

                self.db.add(
                    ProjectMember(
                        id=self.stable_uuid(f"member/{project.id}/{user_id}"),
                        project_id=project.id,
                        user_id=user_id,
                        role=(
                            MemberRole.OWNER
                            if position == 0
                            else self.rng_for(
                                f"member-role/{project.id}/{user_id}"
                            ).choice([MemberRole.CONTRIBUTOR, MemberRole.MAINTAINER])
                        ),
                        is_active=True,
                    )
                )
                self.counts.members += 1

            project.team_size = len(team)

        self.db.flush()

    def seed_flares(self, projects: list[Project]) -> list[BuilderFlare]:
        flares: list[BuilderFlare] = []

        # Only the hiring projects advertise a role, which is what makes the
        # flares page look like real data rather than a uniform grid.
        for project in [p for p in projects if p.hiring]:
            rng = self.rng_for(f"flare/{project.slug}")
            role, description = rng.choice(FLARE_ROLES)
            key = f"flare/{project.slug}/{slugify(role)}"
            flare_id = self.stable_uuid(key)

            existing = self.db.get(BuilderFlare, flare_id)

            if existing is None:
                existing = BuilderFlare(
                    id=flare_id,
                    project_id=project.id,
                    created_by=project.owner_id,
                )
                self.db.add(existing)
                self.counts.flares += 1

            existing.title = f"{role} for {project.title}"
            existing.description = f"{SEED_MARKER} {description}"
            existing.role = role
            existing.location = "Remote"
            existing.commitment = rng.choice(
                ["a few hours a week", "part-time", "flexible"]
            )
            existing.experience_level = rng.choice(EXPERIENCE_LEVELS)
            existing.openings = rng.randint(1, 3)
            existing.status = FlareStatus.OPEN
            existing.remote = True

            flares.append(existing)

        self.db.flush()
        return flares

    def seed_applications(self, flares: list[BuilderFlare], users: list[User]) -> None:
        for flare in flares:
            rng = self.rng_for(f"applications/{flare.id}")
            candidates = [user for user in users if user.id != flare.created_by]

            for applicant in rng.sample(
                candidates, k=min(rng.randint(1, 3), len(candidates))
            ):
                # There is a unique constraint on (applicant_id, project_id),
                # so a user who already applied to this project is skipped
                # rather than inserted again.
                existing = self.db.scalar(
                    select(Application).where(
                        Application.applicant_id == applicant.id,
                        Application.project_id == flare.project_id,
                    )
                )

                if existing is not None:
                    continue

                self.db.add(
                    Application(
                        id=self.stable_uuid(f"application/{flare.id}/{applicant.id}"),
                        applicant_id=applicant.id,
                        project_id=flare.project_id,
                        flare_id=flare.id,
                        status=self.rng_for(
                            f"application-status/{flare.id}/{applicant.id}"
                        ).choice(list(ApplicationStatus)),
                        message=(
                            f"{SEED_MARKER} I have worked on something similar and "
                            "would like to help. Happy to start with a small issue."
                        ),
                        github_url=applicant.github_url,
                    )
                )
                self.counts.applications += 1

        self.db.flush()

    # ------------------------------------------------------------------
    # Conversations, notifications, bookmarks
    # ------------------------------------------------------------------

    def seed_conversations(self, users: list[User]) -> None:
        # Direct conversations between consecutive pairs, so every seeded user
        # has at least one thread waiting when they sign in.
        for index in range(0, len(users) - 1, 2):
            first, second = users[index], users[index + 1]
            key = f"conversation/{first.id}/{second.id}"
            rng = self.rng_for(key)
            conversation_id = self.stable_uuid(key)

            conversation = self.db.get(Conversation, conversation_id)

            if conversation is None:
                conversation = Conversation(
                    id=conversation_id,
                    type=ConversationType.DIRECT,
                    created_by=first.id,
                    is_active=True,
                )
                self.db.add(conversation)
                self.counts.conversations += 1
                self.db.flush()

            for participant in (first, second):
                member_id = self.stable_uuid(
                    f"conversation-member/{conversation_id}/{participant.id}"
                )

                if self.db.get(ConversationMember, member_id) is None:
                    self.db.add(
                        ConversationMember(
                            id=member_id,
                            conversation_id=conversation_id,
                            user_id=participant.id,
                            role=(
                                ConversationRole.OWNER
                                if participant.id == first.id
                                else ConversationRole.MEMBER
                            ),
                        )
                    )

            for position in range(rng.randint(2, 5)):
                message_id = self.stable_uuid(f"message/{conversation_id}/{position}")

                if self.db.get(Message, message_id) is not None:
                    continue

                sender = first if position % 2 == 0 else second
                self.db.add(
                    Message(
                        id=message_id,
                        conversation_id=conversation_id,
                        sender_id=sender.id,
                        type=MessageType.TEXT,
                        content=self.rng_for(
                            f"message-body/{conversation_id}/{position}"
                        ).choice(MESSAGE_SNIPPETS),
                        created_at=EPOCH - timedelta(minutes=30 * (5 - position)),
                    )
                )
                self.counts.messages += 1

        self.db.flush()

    def seed_notifications(self, users: list[User], projects: list[Project]) -> None:
        for user in users:
            rng = self.rng_for(f"notifications/{user.id}")

            for position in range(rng.randint(2, 5)):
                notification_id = self.stable_uuid(f"notification/{user.id}/{position}")

                if self.db.get(Notification, notification_id) is not None:
                    continue

                entry_rng = self.rng_for(f"notification/{user.id}/{position}")
                project = entry_rng.choice(projects)
                notification_type = entry_rng.choice(
                    [
                        NotificationType.PROJECT_INVITE,
                        NotificationType.APPLICATION,
                        NotificationType.MESSAGE,
                        NotificationType.FOLLOW,
                    ]
                )

                self.db.add(
                    Notification(
                        id=notification_id,
                        recipient_id=user.id,
                        type=notification_type,
                        channel=NotificationChannel.DATABASE,
                        status=NotificationStatus.SENT,
                        priority=NotificationPriority.NORMAL,
                        title=notification_type.value.replace("_", " ").title(),
                        message=f"{SEED_MARKER} Activity on {project.title}.",
                        action_url=f"/projects/{project.slug}",
                        is_read=entry_rng.random() < 0.5,
                        created_at=EPOCH - timedelta(hours=position * 3),
                    )
                )
                self.counts.notifications += 1

        self.db.flush()

    def seed_bookmarks(self, users: list[User], projects: list[Project]) -> None:
        for user in users:
            rng = self.rng_for(f"bookmarks/{user.id}")

            for project in rng.sample(projects, k=min(3, len(projects))):
                existing = self.db.scalar(
                    select(Bookmark).where(
                        Bookmark.user_id == user.id,
                        Bookmark.target_id == project.id,
                    )
                )

                if existing is not None:
                    continue

                self.db.add(
                    Bookmark(
                        id=self.stable_uuid(f"bookmark/{user.id}/{project.id}"),
                        user_id=user.id,
                        target_type=BookmarkTargetType.PROJECT,
                        target_id=project.id,
                    )
                )
                self.counts.bookmarks += 1

        self.db.flush()

    # ------------------------------------------------------------------
    # Entry points
    # ------------------------------------------------------------------

    def run(self) -> SeedCounts:
        self.log("Seeding skills...")
        skills = self.seed_skills()

        self.log("Seeding users...")
        users = self.seed_users()

        self.log("Seeding user skills...")
        self.seed_user_skills(users, skills)

        self.log("Seeding projects...")
        projects = self.seed_projects(users)

        self.log("Seeding project members...")
        self.seed_members(projects, users)

        self.log("Seeding builder flares...")
        flares = self.seed_flares(projects)

        self.log("Seeding applications...")
        self.seed_applications(flares, users)

        self.log("Seeding conversations and messages...")
        self.seed_conversations(users)

        self.log("Seeding notifications...")
        self.seed_notifications(users, projects)

        self.log("Seeding bookmarks...")
        self.seed_bookmarks(users, projects)

        return self.counts


def reset_seed_data(db: Session, *, quiet: bool = False) -> int:
    """Delete previously seeded rows, leaving hand-created data alone.

    Seeded users and projects carry SEED_MARKER in their bio/description.
    Deleting those two cascades to everything hanging off them -- members,
    flares, applications, messages, notifications, bookmarks -- because the
    foreign keys are all ON DELETE CASCADE.
    """
    project_ids = list(
        db.scalars(select(Project.id).where(Project.description.contains(SEED_MARKER)))
    )
    user_ids = list(db.scalars(select(User.id).where(User.bio.contains(SEED_MARKER))))

    # Core DELETE rather than session.delete(). The ORM would first try to
    # detach dependent rows by nulling their foreign keys, which fails against
    # the NOT NULL columns here:
    #
    #     IntegrityError: NOT NULL constraint failed: bookmarks.user_id
    #
    # Going straight to the database lets the ON DELETE CASCADE the schema
    # already declares do the work. SQLite needs `PRAGMA foreign_keys=ON` for
    # that, which tests/conftest.py sets; Postgres always enforces it.
    if project_ids:
        db.execute(delete(Project).where(Project.id.in_(project_ids)))

    if user_ids:
        db.execute(delete(User).where(User.id.in_(user_ids)))

    # Whatever the session still has loaded now points at deleted rows.
    db.expire_all()
    db.flush()

    removed = len(project_ids) + len(user_ids)

    if not quiet:
        print(
            f"Removed {len(user_ids)} seeded users and {len(project_ids)} seeded "
            "projects (cascades cover the rest)."
        )

    return removed


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="seed_database",
        description="Populate a development database with demo data.",
    )
    parser.add_argument(
        "--users",
        type=int,
        default=DEFAULT_USERS,
        help=f"How many demo users to create (default: {DEFAULT_USERS}).",
    )
    parser.add_argument(
        "--projects",
        type=int,
        default=DEFAULT_PROJECTS,
        help=f"How many demo projects to create (default: {DEFAULT_PROJECTS}).",
    )
    parser.add_argument(
        "--reset",
        action="store_true",
        help="Delete previously seeded rows before inserting.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Report what would be written, then roll back.",
    )
    parser.add_argument(
        "--quiet",
        action="store_true",
        help="Only print the final summary. Intended for CI.",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Required to run when ENVIRONMENT is production.",
    )

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.users < 2:
        parser.error("--users must be at least 2 (conversations need a pair)")

    if args.projects < 1:
        parser.error("--projects must be at least 1")

    environment = (settings.ENVIRONMENT or "").lower()

    if environment in {"production", "prod"} and not args.force:
        print(
            f"Refusing to seed: ENVIRONMENT is {settings.ENVIRONMENT!r}.\n"
            "This writes demo users with a published password. Pass --force if "
            "you are certain.",
            file=sys.stderr,
        )
        return 2

    db = SessionLocal()

    try:
        if args.reset:
            reset_seed_data(db, quiet=args.quiet)

        seeder = Seeder(
            db,
            user_count=args.users,
            project_count=args.projects,
            quiet=args.quiet,
        )
        counts = seeder.run()

        if args.dry_run:
            db.rollback()
            print("\nDry run -- nothing was committed. Would have written:")
            print(counts.render())
            return 0

        db.commit()

    except Exception:
        db.rollback()
        raise

    finally:
        db.close()

    print("\nSeeded:")
    print(counts.render())

    if counts.total() == 0:
        print("\nEverything was already present -- nothing to do.")
    else:
        print(f"\n{counts.total()} rows written.")

    # The shared password is deliberately not echoed here. It is a local
    # fixture rather than a secret, but printing it trips CodeQL's clear-text
    # logging rule on every scan, and an alert that is always present is an
    # alert nobody reads. It is named in the DEMO_PASSWORD constant above and
    # written down in docs/environment-setup.md, which covers the same need.
    print(
        "\nSign in with any demo account:\n"
        "  admin@example.com          (superuser)\n"
        "  aditialmeida@example.com   (regular user)\n"
        "\nThe shared password is the DEMO_PASSWORD constant in this script, "
        "and is listed in docs/environment-setup.md."
    )

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
