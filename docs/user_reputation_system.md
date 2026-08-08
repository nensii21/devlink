# User Reputation System (#597)

The User Reputation System rewards active, trustworthy, and helpful community members across DevLink.

---

## 1. Overview & Point Sources

Reputation points are awarded automatically or manually logged for key community contributions:

| Action | Points | Description |
| :--- | :---: | :--- |
| `merged_pull_request` | **+50 pts** | Merging pull requests into open source projects |
| `completed_project` | **+100 pts** | Successfully delivering or publishing projects |
| `community_contribution` | **+25 pts** | Helping maintain or contribute to community assets |
| `helpful_discussion` | **+15 pts** | Resolving discussions, Q&A, or code reviews |
| `profile_completion` | **+10 pts** | Completing developer profile details |
| `mentor_recognition` | **+30 pts** | Mentoring fellow developers or peer recognition |

---

## 2. Rank Tier Levels

Users unlock rank tiers based on their aggregate reputation score:

| Reputation Score | Rank Tier | Badge |
| :--- | :--- | :---: |
| `0 – 49 pts` | **Novice** | 🥉 |
| `50 – 199 pts` | **Contributor** | 🥈 |
| `200 – 499 pts` | **Builder** | 🥇 |
| `500 – 999 pts` | **Mentor** | 💎 |
| `1000+ pts` | **Legend** | 👑 |

---

## 3. API Reference

### `GET /api/reputation/me`
Retrieves current user's reputation score, rank tier, and recent activity logs.

### `GET /api/reputation/user/{user_id}`
Retrieves a specific user's reputation summary and recent logs.

### `GET /api/reputation/leaderboard`
Fetches top community members ordered by `reputation_score` descending.

### `POST /api/reputation/award`
Awards reputation points to a user.
```json
{
  "action": "merged_pull_request",
  "description": "Merged PR #597 User Reputation System"
}
```

---

## 4. Testing & Verification

Run the Python pytest suite:
```bash
cd backend && ./venv/bin/pytest tests/test_user_reputation_system.py -v
```
