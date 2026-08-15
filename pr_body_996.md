# Pull Request

## Summary

This pull request introduces milestone ownership tracking. It allows users to assign specific project members as owners of a milestone, providing better accountability and tracking. 

---

## Related Issue

Fixes #996

---

## Type of Change

- [ ] Bug fix
- [x] New feature
- [ ] Documentation update
- [ ] Performance improvement
- [ ] Refactoring
- [x] UI/UX enhancement
- [ ] Tests
- [ ] Other

---

## Changes Made

- **Backend / Database**: Created Alembic migration ea6d6738e0b0 to add owner_id (UUID, nullable, SET NULL on delete) to project_milestones table.
- **Backend / Models**: Added owner_id field and owner relationship mapping in Milestone SQLAlchemy model.
- **Backend / Schemas**: Updated MilestoneCreate, MilestoneUpdate and MilestoneResponse schemas to include owner_id and nested owner output details.
- **Backend / Services**: Updated ProjectMilestoneService.create_milestone and update_milestone to handle assigning owner_id.
- **Frontend**: Updated ProjectDashboard.tsx to include an **Assign Owner** dropdown in the Milestone Creation Modal.
- **Frontend**: Updated the milestone item renderer in the dashboard to show the owner's avatar and name alongside the milestone title.

---

## Screenshots (if applicable)

*N/A*

---

## Testing

- [x] Tested locally
- [x] Existing tests pass
- [ ] Added new tests
- [x] UI verified
- [ ] Cross-browser tested (if applicable)

Additional testing notes: Confirmed typecheck and formatting passes.

---

## Checklist

- [x] My code follows the project's coding standards.
- [x] I have tested my changes locally.
- [x] I have updated the documentation where necessary.
- [x] My changes do not introduce new warnings or errors.
- [x] I have reviewed my own code.
- [x] This pull request focuses on a single feature or fix.
- [x] I have linked the related issue.

---

## Additional Notes

*None*
