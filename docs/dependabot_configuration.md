# Dependabot Configuration Documentation (#477)

This document describes the automated dependency update configuration for DevLink using GitHub Dependabot.

---

## Configuration Overview

Dependabot is configured via `.github/dependabot.yml` to automatically monitor and create Pull Requests for outdated dependencies across all package ecosystems in the repository.

### Configured Ecosystems

1. **Root `npm` Packages (`/`)**
   - **Ecosystem**: `npm`
   - **Target Directory**: `/`
   - **Schedule**: Weekly on Mondays at 04:00 UTC
   - **Labels**: `dependencies`, `javascript`
   - **Commit Prefix**: `chore(deps)`

2. **Frontend `npm` Packages (`/frontend`)**
   - **Ecosystem**: `npm`
   - **Target Directory**: `/frontend`
   - **Schedule**: Weekly on Mondays at 04:00 UTC
   - **Labels**: `dependencies`, `frontend`
   - **Commit Prefix**: `chore(deps-frontend)`

3. **Backend Python Packages (`/backend`)**
   - **Ecosystem**: `pip`
   - **Target Directory**: `/backend`
   - **Schedule**: Weekly on Mondays at 04:00 UTC
   - **Labels**: `dependencies`, `backend`
   - **Commit Prefix**: `chore(deps-backend)`

4. **GitHub Actions Workflows (`/`)**
   - **Ecosystem**: `github-actions`
   - **Target Directory**: `/`
   - **Schedule**: Weekly on Mondays at 04:00 UTC
   - **Labels**: `dependencies`, `github-actions`
   - **Commit Prefix**: `chore(deps-actions)`

---

## Pull Request Policy

- **Open PR Limit**: Maximum 10 active open Dependabot PRs per ecosystem to prevent repository noise.
- **Commit Conventions**: Conventional commits format with explicit scope prefixes.
