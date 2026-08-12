## Summary

Closes #997

Adds a calendar view to projects to display deadlines, sprints, hackathons, meetings, and milestones.

## Changes

- Created \ackend/app/models/project_calendar_event.py\ and Alembic migration to store arbitrary project calendar events (sprints, meetings, etc.).
- Created \ackend/app/schemas/project_calendar_event.py\ and \ackend/app/routers/project_calendar.py\.
- Created \ackend/app/services/project_calendar_service.py\ to aggregate actual calendar events and existing project milestones into a unified response list.
- Installed \eact-big-calendar\ and \date-fns\ in the frontend.
- Created \rontend/src/features/projects/components/ProjectCalendar.tsx\ to render events natively.
- Modified \rontend/src/routes/_app.projects.\.tsx\ to include a new "Calendar" tab in the project workspace view.

## Acceptance Criteria

- [x] Calendar shows Sprint dates
- [x] Calendar shows Milestones
- [x] Calendar shows Hackathons
- [x] Calendar shows Meetings
- [x] Calendar shows Due dates

## Impact & Side Effects

No breaking changes or side effects.

## How to Test

1. Check out this branch.
2. Run \
pm run dev\ and \uvicorn app.main:app --reload\.
3. Go to a project page and click the "Calendar" tab.
4. Verify the calendar renders without errors.

## Quality Checklist

- [x] Linting and type checking pass
- [x] Tests pass locally
