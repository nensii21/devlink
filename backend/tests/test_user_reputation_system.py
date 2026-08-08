"""
Unit & Integration Tests for User Reputation System (#597)
"""
from __future__ import annotations

import uuid
from datetime import datetime, timezone
from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.models.reputation import ReputationLog
from app.models.user import User
from app.schemas.reputation import (
    LeaderboardResponse,
    ReputationAwardRequest,
    ReputationLogResponse,
    ReputationSummaryResponse,
)
from app.services.reputation_service import (
    ACTION_POINTS,
    ReputationService,
    calculate_rank_tier,
)


class TestUserReputationSystem:
    def test_calculate_rank_tier_thresholds(self):
        assert calculate_rank_tier(0) == "Novice 🥉"
        assert calculate_rank_tier(45) == "Novice 🥉"
        assert calculate_rank_tier(50) == "Contributor 🥈"
        assert calculate_rank_tier(150) == "Contributor 🥈"
        assert calculate_rank_tier(200) == "Builder 🥇"
        assert calculate_rank_tier(450) == "Builder 🥇"
        assert calculate_rank_tier(500) == "Mentor 💎"
        assert calculate_rank_tier(999) == "Mentor 💎"
        assert calculate_rank_tier(1000) == "Legend 👑"
        assert calculate_rank_tier(2500) == "Legend 👑"

    def test_award_reputation_updates_score_and_creates_log(self):
        db = MagicMock()
        user_id = uuid.uuid4()

        mock_user = User(
            id=user_id,
            username="repuser",
            email="repuser@example.com",
            reputation_score=0,
        )
        db.scalar.return_value = mock_user

        # 1. Award Merged PR (+50)
        updated_user, log1 = ReputationService.award_reputation(
            db=db,
            user_id=user_id,
            action="merged_pull_request",
            description="Merged feature PR #123",
        )
        assert updated_user.reputation_score == 50
        assert log1.points == 50
        assert log1.action == "merged_pull_request"

        # 2. Award Completed Project (+100) -> total 150
        updated_user, log2 = ReputationService.award_reputation(
            db=db,
            user_id=user_id,
            action="completed_project",
        )
        assert updated_user.reputation_score == 150
        assert log2.points == 100

        # 3. Award Mentor Recognition (+30) -> total 180
        updated_user, log3 = ReputationService.award_reputation(
            db=db,
            user_id=user_id,
            action="mentor_recognition",
        )
        assert updated_user.reputation_score == 180
        assert log3.points == 30

    def test_get_user_reputation_summary(self):
        db = MagicMock()
        user_id = uuid.uuid4()

        mock_user = User(
            id=user_id,
            username="summaryuser",
            email="summaryuser@example.com",
            reputation_score=250,
        )
        db.scalar.return_value = mock_user

        log1 = ReputationLog(
            id=uuid.uuid4(),
            user_id=user_id,
            action="completed_project",
            points=100,
            description="Project DevLink",
            created_at=datetime.now(timezone.utc),
        )
        db.scalars.return_value.all.return_value = [log1]

        summary = ReputationService.get_user_reputation_summary(db, user_id=user_id)

        assert summary.user_id == user_id
        assert summary.reputation_score == 250
        assert summary.rank_tier == "Builder 🥇"
        assert len(summary.recent_logs) == 1
        assert summary.recent_logs[0].action == "completed_project"

    def test_leaderboard_ranking_order(self):
        db = MagicMock()

        user1 = User(
            id=uuid.uuid4(),
            username="legend_dev",
            reputation_score=1200,
            created_at=datetime.now(timezone.utc),
        )
        user2 = User(
            id=uuid.uuid4(),
            username="builder_dev",
            reputation_score=350,
            created_at=datetime.now(timezone.utc),
        )

        db.scalar.return_value = 2
        db.scalars.return_value.all.return_value = [user1, user2]

        leaderboard = ReputationService.get_leaderboard(db, skip=0, limit=10)

        assert leaderboard.total == 2
        assert len(leaderboard.entries) == 2
        assert leaderboard.entries[0].username == "legend_dev"
        assert leaderboard.entries[0].rank == 1
        assert leaderboard.entries[0].rank_tier == "Legend 👑"
        assert leaderboard.entries[1].username == "builder_dev"
        assert leaderboard.entries[1].rank == 2
        assert leaderboard.entries[1].rank_tier == "Builder 🥇"
