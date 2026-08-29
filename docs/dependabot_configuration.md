# Dependabot Configuration Documentation (#477)

This document describes the automated dependency update configuration for DevLink using GitHub Dependabot.

---

## Configuration Overview

Dependabot is configured via `.github/dependabot.yml` to automatically monitor and create Pull Requests for outdated dependencies across all package ecosystems in the repository.

### Configured Ecosystems

1. **Frontend `npm` Packages (`/frontend`)**
   - **Ecosystem**: `npm`
   - **Target Directory**: `/frontend`
   - **Schedule**: Weekly on Mondays at 04:00 UTC
   - **Labels**: `dependencies`, `frontend`
   - **Commit Prefix**: `chore(deps-frontend)`

2. **Backend Python Packages (`/backend`)**
   - **Ecosystem**: `pip`
   - **Target Directory**: `/backend`
   - **Schedule**: Weekly on Mondays at 04:00 UTC
   - **Labels**: `dependencies`, `backend`
   - **Commit Prefix**: `chore(deps-backend)`

3. **GitHub Actions Workflows (`/`)**
   - **Ecosystem**: `github-actions`
   - **Target Directory**: `/`
   - **Schedule**: Weekly on Mondays at 04:00 UTC
   - **Labels**: `dependencies`, `github-actions`
   - **Commit Prefix**: `chore(deps-actions)`

4. **Backend Container Images (`/backend`)**
   - **Ecosystem**: `docker`
   - **Target Directory**: `/backend`
   - **Schedule**: Weekly on Mondays at 04:00 UTC
   - **Labels**: `dependencies`, `docker`
   - **Commit Prefix**: `chore(deps-docker)`

> [!NOTE]
> There is no root `npm` entry. The repository root carried a `package.json`
> belonging to an unrelated project, and between 21 August and #1401 this file
> watched *only* that manifest — the three ecosystems above had been removed,
> so nothing was watching the frontend, the backend or the workflow actions.
> The root manifest is gone. `.github/scripts/check_manifests.py` now fails
> the build if a manifest exists that no workflow installs, that Dependabot
> does not watch, or that names a project this repository does not recognise.

---

## Pull Request Policy

- **Open PR Limit**: Maximum 10 active open Dependabot PRs per ecosystem to prevent repository noise.
- **Commit Conventions**: Conventional commits format with explicit scope prefixes.
