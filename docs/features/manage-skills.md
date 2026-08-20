# Allow Users to Manage Skills (#724)

Enables users to manage, reorder, and organize their skills across technical categories with backend persistence and autocomplete suggestions.

## Features

1. **CRUD Operations**:
   - **Create**: Add skills with category, proficiency level (Beginner, Intermediate, Advanced, Expert), and years of experience.
   - **Read**: Display skills categorized in developer skill matrix and profile views.
   - **Update**: In-place edit for proficiency level, category, and years of experience.
   - **Delete**: Remove skills easily.
   - **Reorder**: Change the order of skills with Move Up / Move Down buttons.

2. **Skill Search / Autocomplete**:
   - Autocomplete skill name input querying `/api/skills/search/{keyword}`.
   - Quick-select chips for popular suggestions (TypeScript, React, Python, Docker, etc.).

3. **Prevent Duplicates**:
   - Case-insensitive duplicate detection before adding to the skill matrix.
   - Warning banner/message displayed when duplicate is detected.
   - Backend deduplication guard in `SkillMatrixService`.

4. **Backend Persistence**:
   - Persists via `PUT /api/skills-matrix/me` and synchronizes with user profile skills in `PUT /api/users/me`.
