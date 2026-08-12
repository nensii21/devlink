Hi maintainers!

I have implemented the complete Pro Subscription flow from the backend models (and migrations) up to the frontend UI gating for limits.

### Technical Analysis
- **Core Architecture Change:** Introduced the `UserSubscription` model and tied it to a global `get_pro_user` dependency in `backend/app/dependencies.py` which effectively checks active subscriptions globally without tight coupling.
- **Core Backend Feature:** The application creation process in `backend/app/routers/applications.py` now enforces strict limits for non-pro users by aggregating database state (`func.count`).
- **Core Backend Feature:** The Profile Views feature (`routers/profile_views.py`) is completely gated behind the dependency at the route level.
- **Frontend Refactoring:** Cleanly replaced the hardcoded `Settings` Billing tab with a data-driven React Query component, managing proper error boundaries (`403` catches) and UI overlays.

Given this PR heavily touches core database abstractions, dependency injection for backend access controls, and cross-stack feature gating, I believe it qualifies for the **Level 3** and **good-backend** / **good-ui** ECSoC26 points.

Could you please review and assign the `ECSoC26`, `Level 3`, `good-backend`, and `good-ui` labels? Thank you!
