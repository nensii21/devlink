### Summary
This PR implements the new Pro Subscription feature, adding billing and gating functionality. It closes #1001.

### Motivation
Closes #1001

To monetize the platform and provide premium features, we are introducing a Pro subscription tier that gates advanced analytics and limits the number of project applications for free users.

### Changes
- **Backend Models & DB**:
  - Created `backend/app/models/user_subscription.py`: Defines the `UserSubscription` model mapped to the `user_subscriptions` table.
  - Modified `backend/app/models/user.py`: Added relationship to `UserSubscription`.
  - Created `backend/alembic/versions/2b3c4d5ea1f2_create_user_subscriptions_table.py`: Alembic migration script for the new table.
- **Backend API & Dependencies**:
  - Created `backend/app/routers/subscriptions.py`: Added endpoints for `GET /me` (subscription info) and `POST /upgrade` (mock upgrade).
  - Modified `backend/app/main.py`: Registered the new subscriptions router.
  - Modified `backend/app/dependencies.py`: Created `get_pro_user` dependency to check active Pro status.
- **Backend Gating**:
  - Modified `backend/app/routers/profile_views.py`: Gated `GET /me` endpoint with `get_pro_user`.
  - Modified `backend/app/routers/applications.py`: Enforced a limit of 3 applications for non-Pro users in `create_application`.
- **Frontend Integration**:
  - Created `frontend/src/api/modules/subscriptions.ts`: API wrapper for subscriptions.
  - Created `frontend/src/components/settings/SubscriptionSection.tsx`: Billing and upgrade UI component.
  - Modified `frontend/src/routes/_app.settings.tsx`: Replaced hardcoded billing section with `SubscriptionSection`.
  - Modified `frontend/src/routes/_app.profile-analytics.tsx`: Implemented 403 error handling to display a Pro upgrade prompt.
  - Modified `frontend/src/features/projects/components/ApplyModal.tsx`: Handled 403 error for application limit, displaying a Pro upgrade prompt in the modal.
  - Modified `frontend/src/api/modules/auth.ts`: Added `is_pro` to the `AuthUser` interface.

### Acceptance Criteria
- [x] Create `UserSubscription` model (user_id, stripe_customer_id, tier, status)
- [x] Create Alembic migration for the new table
- [x] Add `/api/subscriptions/me` and `/api/subscriptions/upgrade` endpoints
- [x] Limit free users to max 3 project applications
- [x] Block free users from accessing Profile Views (return 403)
- [x] Frontend: Add "Billing" tab in Settings
- [x] Frontend: Show "Upgrade to Pro" modal when hitting application limits or viewing restricted analytics

### Impact & Side Effects
No breaking changes. Free users who already have >3 applications will be blocked from creating new ones but existing applications remain untouched.

### How to Test
1. Make sure to run `uv run alembic upgrade head`.
2. Login as a free user. Try to apply to 4 projects; the 4th application should show the "Upgrade to Pro" limit modal.
3. Try to access the "Analytics" tab; it should show the "Profile Analytics is a Pro feature" prompt.
4. Go to Settings -> Billing and click "Upgrade Now". It should mock-upgrade your account to Pro.
5. Re-test the above; they should now succeed.

### Quality Checklist
- [x] I have run the linter and tests locally
- [x] I have updated the documentation (if applicable)
- [x] I have added/updated relevant tests
