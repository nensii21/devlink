"""
Advanced Matchmaking Engine.
Implements Gale-Shapley stable matching for bi-directional market pairing, team capacity balancing, and conflict avoidance.
"""

from typing import List, Dict, Any, Optional, Set
from dataclasses import dataclass, field
from enum import Enum


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
    availability_hours_per_week: int = 10
    conflicts: List[str] = field(default_factory=list)  # project_ids to avoid


@dataclass
class ProjectMatchCriteria:
    project_id: str
    title: str
    required_skills: List[str]
    preferred_timezone_offset: Optional[int] = None
    min_experience_level: ExperienceLevel = ExperienceLevel.INTERMEDIATE
    min_hours_per_week: int = 5
    capacity: int = 1  # Number of developers needed
    conflicts: List[str] = field(default_factory=list)  # user_ids to avoid


@dataclass
class MatchResult:
    project_id: str
    developer_ids: List[str]
    match_quality_metrics: Dict[str, float]
    explanation: str


@dataclass
class MatchmakingResponse:
    matches: List[MatchResult]
    unmatched_projects: List[str]
    unmatched_developers: List[str]


class MatchmakingService:
    """Core logic for stable bi-directional matching between developers and projects."""

    EXPERIENCE_WEIGHTS: Dict[ExperienceLevel, float] = {
        ExperienceLevel.BEGINNER: 0.5,
        ExperienceLevel.INTERMEDIATE: 0.75,
        ExperienceLevel.SENIOR: 0.95,
        ExperienceLevel.LEAD: 1.0,
    }

    def _calculate_base_score(self, developer: DeveloperCandidate, project: ProjectMatchCriteria) -> float:
        """Calculates a baseline compatibility score between a developer and a project."""
        # 1. Skill Overlap (0.0 - 1.0)
        req_set = {s.lower() for s in project.required_skills}
        dev_set = {s.lower() for s in developer.skills}
        skill_score = len(req_set.intersection(dev_set)) / len(req_set) if req_set else 1.0

        # 2. Timezone Proximity (0.0 - 1.0)
        tz_score = 1.0
        if project.preferred_timezone_offset is not None:
            diff = abs(developer.timezone_offset - project.preferred_timezone_offset)
            diff = min(diff, 24 - diff)
            tz_score = max(0.0, 1.0 - (diff / 12.0) * 0.25)

        # 3. Experience Compatibility
        c_weight = self.EXPERIENCE_WEIGHTS.get(developer.experience_level, 0.5)
        m_weight = self.EXPERIENCE_WEIGHTS.get(project.min_experience_level, 0.5)
        exp_score = 1.0 if c_weight >= m_weight else max(0.0, c_weight / m_weight)

        # 4. Availability penalty
        avail_factor = 1.0 if developer.availability_hours_per_week >= project.min_hours_per_week else 0.7

        return ((skill_score * 0.65) + (tz_score * 0.20) + (exp_score * 0.15)) * avail_factor

    def _has_conflict(self, developer: DeveloperCandidate, project: ProjectMatchCriteria) -> bool:
        """Checks if either party has blacklisted the other."""
        return project.project_id in developer.conflicts or developer.user_id in project.conflicts

    def execute_stable_match(
        self, developers: List[DeveloperCandidate], projects: List[ProjectMatchCriteria]
    ) -> MatchmakingResponse:
        """
        Executes a modified Gale-Shapley (Deferred Acceptance) algorithm.
        Projects propose to developers. Developers can accept multiple projects up to capacity 1 (for simplicity here, devs are 1:1, projects are 1:N).
        """
        dev_map = {d.user_id: d for d in developers}
        proj_map = {p.project_id: p for p in projects}

        # Generate preference lists based on scores
        # project_id -> list of user_ids (sorted by score descending)
        proj_prefs: Dict[str, List[str]] = {}
        for p in projects:
            scores = []
            for d in developers:
                if not self._has_conflict(d, p):
                    scores.append((d.user_id, self._calculate_base_score(d, p)))
            scores.sort(key=lambda x: x[1], reverse=True)
            proj_prefs[p.project_id] = [u for u, s in scores if s > 0] # Must have some compatibility

        # user_id -> dict of {project_id: score} for O(1) comparison when receiving proposals
        dev_prefs: Dict[str, Dict[str, float]] = {}
        for d in developers:
            dev_prefs[d.user_id] = {}
            for p in projects:
                if not self._has_conflict(d, p):
                    dev_prefs[d.user_id][p.project_id] = self._calculate_base_score(d, p)

        # State tracking for algorithm
        # Proposers (Projects) track how many slots they need to fill and who they've proposed to
        free_projects = {p.project_id: p.capacity for p in projects}
        proj_next_proposal_idx = {p.project_id: 0 for p in projects}

        # Acceptors (Developers) track their current match (assuming developers only take 1 project)
        dev_current_match: Dict[str, str] = {} # user_id -> project_id

        # Run Gale-Shapley
        while True:
            # Find a project that still needs developers and hasn't exhausted its preference list
            proposing_proj = None
            for pid, needed in free_projects.items():
                if needed > 0 and proj_next_proposal_idx[pid] < len(proj_prefs[pid]):
                    proposing_proj = pid
                    break

            if not proposing_proj:
                break # All projects are either full or have exhausted their preferences

            # Propose to the next developer on the list
            idx = proj_next_proposal_idx[proposing_proj]
            target_dev = proj_prefs[proposing_proj][idx]
            proj_next_proposal_idx[proposing_proj] += 1

            current_match = dev_current_match.get(target_dev)
            
            if not current_match:
                # Developer is free, accepts proposal
                dev_current_match[target_dev] = proposing_proj
                free_projects[proposing_proj] -= 1
            else:
                # Developer is already matched, compare preferences
                score_new = dev_prefs[target_dev][proposing_proj]
                score_current = dev_prefs[target_dev][current_match]
                
                if score_new > score_current:
                    # Developer prefers new project, breaks current match
                    dev_current_match[target_dev] = proposing_proj
                    free_projects[proposing_proj] -= 1
                    free_projects[current_match] += 1 # Previous project needs a replacement
                else:
                    # Developer rejects proposal (proposing_proj's free count remains unchanged)
                    pass

        # Build output format
        final_matches: Dict[str, List[str]] = {p.project_id: [] for p in projects}
        for dev_id, proj_id in dev_current_match.items():
            final_matches[proj_id].append(dev_id)

        response_matches = []
        for p in projects:
            matched_devs = final_matches[p.project_id]
            if not matched_devs:
                continue
                
            # Generate explanation for the team
            avg_score = sum(dev_prefs[d][p.project_id] for d in matched_devs) / len(matched_devs)
            
            explanation = f"Matched {len(matched_devs)} developer(s) fulfilling capacity {p.capacity}. "
            if avg_score > 0.85:
                explanation += "Exceptional skill and timezone overlap."
            elif avg_score > 0.6:
                explanation += "Solid skill alignment and adequate availability."
            else:
                explanation += "Partial match based on available candidates."

            response_matches.append(MatchResult(
                project_id=p.project_id,
                developer_ids=matched_devs,
                match_quality_metrics={"average_team_score": round(avg_score, 3)},
                explanation=explanation
            ))

        unmatched_devs = [d.user_id for d in developers if d.user_id not in dev_current_match]
        unmatched_projs = [p.project_id for p in projects if free_projects[p.project_id] == p.capacity]

        return MatchmakingResponse(
            matches=response_matches,
            unmatched_projects=unmatched_projs,
            unmatched_developers=unmatched_devs
        )


matchmaking_service = MatchmakingService()
