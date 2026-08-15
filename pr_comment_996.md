Hi maintainers! 👋

I've completed the implementation for issue #996 (Milestone tracking for projects). 

### ECSoC26 Label Request
Based on the official ECSoC guidelines, this PR involves Core/Architecture backend changes:
- Created Alembic database migration to update project_milestones schema with owner_id and foreign key constraint.
- Updated SQLAlchemy models and relationships.
- Updated FastAPI Pydantic schemas and ProjectMilestoneService to correctly handle owner_id.

I kindly request the following labels to be added to this PR:
- ECSoC26
- Level 3
- good-backend

Thanks for reviewing!
