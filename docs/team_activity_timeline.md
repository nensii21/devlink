# Team Activity Timeline (#616)

Real-time chronological activity stream for project teams on DevLink.

## Activity Types
- Member Joined
- Member Left
- Role Updated
- Project Updated
- Milestone Completed
- New Discussion
- File Uploaded

## API Endpoint
`GET /api/projects/{project_id}/activity-timeline`

## How to Test
1. **Backend Tests**: `pytest backend/tests/test_team_activity_timeline.py`
2. **Frontend UI**: Navigate to `/projects/1/activity` route.
