# Project Collaboration Metrics (#620)

Tracks collaboration metrics for project owners on DevLink.

## Tracked Metrics
- Active members
- Daily activity
- Response times
- Messages exchanged
- Tasks completed
- Applications received

## API Endpoint
`GET /api/projects/{project_id}/collaboration-metrics`

## How to Test
1. **Backend Tests**: `pytest backend/tests/test_project_collaboration_metrics.py`
2. **Frontend UI**: Navigate to `/projects/1/collaboration-metrics` route.
