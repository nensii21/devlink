# Intelligent Matchmaking & Recommendation Engine Specification

## 1. Executive Summary
DevLink's Intelligent Matchmaking & Recommendation Engine is an automated pairing and recommendation system designed to bridge the gap between open-source projects seeking contributors and developers looking for relevant projects or mentorship.

---

## 2. Core Problem Statement
Finding the right contributors or open-source repositories often relies on manual keyword searching and serendipitous discovery. Maintainers experience high turnover and contributor drop-off when tasks do not align with contributor capabilities, working timezones, or domain interests.

---

## 3. High-Level System Architecture
The Matchmaking Engine operates across four primary pipeline stages:
1. **Profile & Repository Vectorization**: Extracts semantic concepts, skill tags, repository topics, commit languages, and developer experience tiers into dense vector embeddings.
2. **Multi-Factor Scoring Matrix**: Evaluates candidates across skill relevance, timezone alignment, historical responsiveness, and active workload capacity.
3. **Diversity & Serendipity Filter**: Implements dynamic ranking penalties to prevent maintainer fatigue and avoid recommending the same top 5% profiles exclusively.
4. **Caching & Retrieval Layer**: Stores precomputed affinity matrices with an invalidation TTL tied to profile updates and project milestone completions.

---

## 4. Scoring Algorithm & Mathematical Formulation

### 4.1 Skill Overlap Coefficient ($S_{\text{skill}}$)
Given a candidate's verified skills $S_c$ and a project's required skills $S_p$:
$$S_{\text{skill}} = \frac{|S_c \cap S_p|}{|S_p|}$$

### 4.2 Timezone Proximity Factor ($S_{\text{tz}}$)
Given UTC offsets $T_c$ and $T_p$:
$$\Delta T = \min(|T_c - T_p|, 24 - |T_c - T_p|)$$
$$S_{\text{tz}} = 1.0 - \min\left(\frac{\Delta T}{12}, 1.0\right) \times 0.25$$

### 4.3 Composite Match Score ($S_{\text{final}}$)
$$S_{\text{final}} = \text{clamp}\left(0.0, 1.0, (S_{\text{skill}} \times 0.70) + (S_{\text{tz}} \times 0.20) + (S_{\text{exp}} \times 0.10)\right)$$

---

## 5. API Endpoint Specifications

### 5.1 Project Match Recommendations
- **Endpoint**: `GET /api/v1/recommendations/projects`
- **Authentication**: Bearer JWT (Developer or Contributor role)
- **Query Parameters**:
  - `limit` (integer, default: 20): Maximum results to return.
  - `offset` (integer, default: 0): Pagination offset.
  - `min_score` (float, default: 0.5): Minimum similarity threshold.
- **Response Shape**:
```json
{
  "total": 42,
  "results": [
    {
      "project_id": "proj_123",
      "title": "Distributed Task Queue",
      "match_score": 0.895,
      "skill_breakdown": {
        "matching_skills": ["python", "redis", "fastapi"],
        "missing_skills": ["docker"]
      },
      "timezone_diff_hours": 2
    }
  ]
}
```

### 5.2 Candidate Match Recommendations for Maintainers
- **Endpoint**: `GET /api/v1/recommendations/candidates/{project_id}`
- **Authentication**: Bearer JWT (Project Maintainer/Owner role)
- **Response Shape**:
```json
{
  "project_id": "proj_123",
  "candidates": [
    {
      "user_id": "usr_998",
      "username": "alex_dev",
      "match_score": 0.94,
      "skills": ["python", "redis", "fastapi", "docker"],
      "experience_level": "senior"
    }
  ]
}
```

---

## 6. Data Models and Schema Definitions
- `DeveloperCandidate`: Encapsulates user identifier, verified skills, timezone, activity metrics, and match score.
- `ProjectMatchCriteria`: Encapsulates target project identifiers, required/preferred skill sets, timezone preferences, and complexity rating.
- `MatchFeedback`: Captures explicit user interactions (accept, dismiss, bookmark) for continuous reinforcement learning.

---

## 7. Security, Rate Limiting & Privacy Considerations
- **PII Scrubbing**: Contact details and private repository insights are excluded from public matchmaking scoring.
- **Opt-out Mechanism**: Developers can set their availability to `invisible` or `not_looking` to exclude themselves from scoring calculations.
- **Rate Limiting**: Recommendation endpoints are limited to 60 requests per minute per IP/user token.

---

## 8. Rollout Plan & Milestones
- **Phase 1**: Deterministic skill overlap and timezone weighting (Current PR).
- **Phase 2**: Vector embedding integration with pgvector / Sentence-BERT.
- **Phase 3**: Reinforcement learning from implicit accept/reject feedback.
