# Replace Mock Profile Data with Real User Data (#723)

Replaces mock and placeholder profile and project data with real dynamic backend data.

## Features

1. **Backend Endpoints**:
   - `GET /api/users/by-username/{username}`: Looks up user profile by username with privacy filtering.
   - `GET /api/projects/user/{user_id}`: Lists published projects owned by a specific user.

2. **Frontend Dynamic Data**:
   - Fetches user profile via `usersApi.getByUsername(username)` with React Query.
   - Fetches user projects via `projectsApi.byUser(user.id)`.
   - Removed hardcoded mock arrays (`builders`, `projects.slice(0, 4)`).

3. **Loading & Empty States**:
   - Loading skeleton loaders for profile banner, avatar, header, and cards.
   - Graceful empty states for user projects with direct action to create a new project.
   - Experience and skills empty states handled gracefully.
