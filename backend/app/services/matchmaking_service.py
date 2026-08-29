"""
Matchmaking and recommendation service module.
Provides candidate ranking, similarity calculations, and scoring algorithms for projects and developers.
"""

from typing import List, Dict, Any, Optional, Set
from dataclasses import dataclass, field
from enum import Enum
import math


class ExperienceLevel(str, Enum):
    BEGINNER = "beginner"
    INTERMEDIATE = "intermediate"
    SENIOR = "senior"
    LEAD = "lead"


@dataclass
class DeveloperCandidate:
    user_id: str
    username: str
    skills: List[str]
    experience_level: ExperienceLevel = ExperienceLevel.INTERMEDIATE
    timezone_offset: int = 0
    bio: str = ""
    availability_hours_per_week: int = 10
    match_score: float = 0.0
    matched_skills: List[str] = field(default_factory=list)
    missing_skills: List[str] = field(default_factory=list)


@dataclass
class ProjectMatchCriteria:
    project_id: str
    title: str
    required_skills: List[str]
    preferred_skills: List[str] = field(default_factory=list)
    preferred_timezone_offset: Optional[int] = None
    min_experience_level: ExperienceLevel = ExperienceLevel.INTERMEDIATE
    min_hours_per_week: int = 5


class MatchmakingService:
    """Core logic for calculating match scores between developers and projects."""

    EXPERIENCE_WEIGHTS: Dict[ExperienceLevel, float] = {
        ExperienceLevel.BEGINNER: 0.5,
        ExperienceLevel.INTERMEDIATE: 0.75,
        ExperienceLevel.SENIOR: 0.95,
        ExperienceLevel.LEAD: 1.0,
    }

    @staticmethod
    def calculate_skill_overlap(
        candidate_skills: List[str], required_skills: List[str]
    ) -> Dict[str, Any]:
        """Calculates exact skill matches and missing requirements."""
        if not required_skills:
            return {"score": 1.0, "matched": [], "missing": []}

        candidate_set: Set[str] = {s.strip().lower() for s in candidate_skills if s}
        required_set: Set[str] = {s.strip().lower() for s in required_skills if s}

        matched = list(candidate_set.intersection(required_set))
        missing = list(required_set.difference(candidate_set))
        score = len(matched) / len(required_set) if required_set else 1.0

        return {"score": score, "matched": matched, "missing": missing}

    @staticmethod
    def calculate_timezone_proximity(
        candidate_offset: Optional[int], target_offset: Optional[int]
    ) -> float:
        """Calculates a normalized 0.0 - 1.0 proximity score based on UTC offset delta."""
        if candidate_offset is None or target_offset is None:
            return 1.0

        diff = abs(candidate_offset - target_offset)
        diff = min(diff, 24 - diff)
        return max(0.0, 1.0 - (diff / 12.0) * 0.25)

    def calculate_experience_compatibility(
        self, candidate_level: ExperienceLevel, min_level: ExperienceLevel
    ) -> float:
        """Evaluates whether candidate meets or exceeds the required experience tier."""
        c_weight = self.EXPERIENCE_WEIGHTS.get(candidate_level, 0.5)
        m_weight = self.EXPERIENCE_WEIGHTS.get(min_level, 0.5)
        if c_weight >= m_weight:
            return 1.0
        return max(0.0, c_weight / m_weight)

    def rank_candidates(
        self, criteria: ProjectMatchCriteria, candidates: List[DeveloperCandidate]
    ) -> List[DeveloperCandidate]:
        """Ranks a list of candidate developers against the given project criteria."""
        ranked: List[DeveloperCandidate] = []

        for candidate in candidates:
            skill_info = self.calculate_skill_overlap(candidate.skills, criteria.required_skills)
            tz_score = self.calculate_timezone_proximity(
                candidate.timezone_offset, criteria.preferred_timezone_offset
            )
            exp_score = self.calculate_experience_compatibility(
                candidate.experience_level, criteria.min_experience_level
            )

            # Availability check
            avail_factor = 1.0 if candidate.availability_hours_per_week >= criteria.min_hours_per_week else 0.7

            # Composite weighted score
            composite = (
                (skill_info["score"] * 0.65)
                + (tz_score * 0.20)
                + (exp_score * 0.15)
            ) * avail_factor

            candidate.match_score = round(max(0.0, min(1.0, composite)), 3)
            candidate.matched_skills = sorted(skill_info["matched"])
            candidate.missing_skills = sorted(skill_info["missing"])
            ranked.append(candidate)

        return sorted(ranked, key=lambda c: c.match_score, reverse=True)


matchmaking_service = MatchmakingService()
