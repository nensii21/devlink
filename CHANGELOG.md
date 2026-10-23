# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added

- Added initial `CHANGELOG.md` following the Keep a Changelog specification.
- Organization logo and cover image management for organization workspaces.
- Notification preferences for managing application, message, and activity alerts.
- GitHub contribution insights linking contributor activity to project profiles.
- Project collaboration metrics with dark/light mode support and mock fallback.
- Team activity timeline tracking team contributions over time.
- Peer testimonials on developer profiles.
- Publishable release notes for projects.
- Pinned projects backed by a real API.
- Project time tracking so owners can see where effort goes.
- Contribution streaks and activity heatmap on profiles.
- Read receipts for direct messages.
- Profile avatar camera capture and cropping.
- Improved billing dashboard.
- Automatic activity feed generation.
- Apply to projects feature.
- Organization member roles and permissions.
- Redesigned bookmarks as compact collections.
- Global search across developers, projects, posts, and organizations.
- Report User feature.
- Recently viewed projects.
- Live search suggestions.
- Optimistic updates for user actions.

### Changed

- Standardized border radius and elevation tokens across the UI.
- Reduced unnecessary dashboard card wrappers.
- Changed collaboration metrics accent and highlight colors to cyan.
- Render Outlet instead of throwing notFound when a project is unavailable.

### Deprecated

- None.

### Removed

- None.

### Fixed

- Resolved typecheck/lint failures for the organization branding PR.
- Fixed syntax errors in tracked files.
- Fixed stepValue error.
- Fixed frontend build and backend migrations.
- Fixed useEffect hook missing dependency warning.
- Fixed syntax and duplicate key errors in services and profile.
- Fixed import path in the collaboration metrics route.
- Fixed import path in the team activity route.
- Fixed CI build errors (missing lottie-web dependency, frontend typecheck, backend format).
- Fixed require-star workflow shell syntax.
- Added the missing project_milestones table.
- Stopped testimonial enums from being created twice.
- Stopped release enums from being created twice.

### Security

- None.

---

## Maintenance

This changelog is maintained manually by contributors. Entries are added as pull requests are merged to `main`, following the [Keep a Changelog](https://keepachangelog.com/en/1.1.0/) format. There is no automated release process or changelog tooling, and no versioned release has been cut yet; until the first release, all recent changes are listed under `[Unreleased]`. Versioned entries are added when a release is cut.
