# Developer Insights Dashboard (#614)

Personalized dashboard summarizing user activity, engagement metrics, contribution streak, and AI match rate on DevLink.

## Display Metrics
- Projects created
- Applications submitted
- Profile views
- Followers gained
- Messages sent
- Contribution streak
- AI match success rate

## API Endpoint
`GET /api/developer-insights?range=30d`

## How to Test
1. **Backend Tests**: `pytest backend/tests/test_developer_insights.py`
2. **Frontend UI**: Navigate to `/insights` route.
