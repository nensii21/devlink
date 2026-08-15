Hi maintainers, this PR is ready for review! 🚀

### Technical Analysis
This PR fulfills Issue #997 by introducing a full calendar subsystem:
1. **Backend Integration (Core Architecture & DB)**: Added a new project_calendar_events relational table with Alembic migration. 
2. **Aggregation Service**: Implemented a service layer in FastAPI that aggregates ProjectCalendarEvent data alongside existing Milestone deadlines, normalizing them into a unified CalendarEvent schema.
3. **Frontend Integration**: Implemented a eact-big-calendar wrapper on the frontend connected via TanStack query.

Since this implements **core backend logic changes** (new schemas, unified routing API, new tables and migrations), as well as significant UI components, I kindly request this be classified with **Level 3** and **good-backend** for ECSoC '26 points.

Thanks!
