# Editable User Profile Feature (#721)

Allows users to update their profile information directly from their profile page.

## Key Features

1. **Edit Profile Button**:
   - Rendered on `/_app/profile/$username` when viewing own profile.
   - Opens `EditProfileModal`.

2. **Editable Information**:
   - **Basic Info**: First Name, Last Name, Username Handle, Profile Image URL, Headline/Tagline.
   - **Bio & Role**: Detailed Bio, Current Role/Title, Company, Location, Experience Level (Beginner to Lead).
   - **Skills**: Dynamic skill tags input with add/remove functionality.
   - **Social Links**: Personal Website, GitHub, LinkedIn, Twitter/X, and Portfolio URLs.

3. **Backend API (`PUT /api/users/me`)**:
   - Handles profile updates with username availability validation.
   - Syncs user skill tags in database (`UserSkill` table).
   - Records profile update activity.

4. **Validation & UX**:
   - Full URL format validation with helpful error messages.
   - Immediate cache invalidation (`["user"]`, `["currentUser"]`, `["profile"]`).
   - Smooth navigation if username handle is changed.
