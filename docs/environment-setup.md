# DevLink Environment Setup & Onboarding Guide

Welcome to the DevLink Developer Onboarding & Setup Guide! This comprehensive guide provides step-by-step instructions for installing required software, configuring environment variables, setting up the frontend and backend locally, troubleshooting common issues, and resolving errors.

---

## 1. Required Software & Prerequisites

Before setting up DevLink, verify that your machine has the following tools installed:

| Software | Required Version | Download / Installation Link | Purpose |
| :--- | :--- | :--- | :--- |
| **Node.js** | `v20.0.0` or higher | [nodejs.org](https://nodejs.org/) | Frontend runtime & package manager |
| **npm** / **Bun** | `v10.0.0`+ / `v1.0`+ | Included with Node.js | Dependency management |
| **Python** | `v3.11.0` or higher | [python.org](https://www.python.org/) | Backend FastAPI engine |
| **Git** | `v2.30.0` or higher | [git-scm.com](https://git-scm.com/) | Source control |
| **Docker & Docker Compose** | *(Optional)* | [docker.com](https://www.docker.com/) | Containerized development environment |

---

## 2. Environment Variables Guide

DevLink relies on environment variables for API configuration, database connectivity, and security keys.

### Backend Environment Variables (`backend/.env`)

Copy `backend/.env.example` to `backend/.env`:

```bash
cd backend
cp .env.example .env
```

Key backend configuration parameters:

```ini
# Application Configuration
PROJECT_NAME="DevLink API"
VERSION="1.0.0"
API_V1_STR="/api/v1"

# Database Configuration (PostgreSQL or SQLite fallback)
DATABASE_URL="postgresql://postgres:postgres@localhost:5432/devlink_db"

# Security & JWT Authentication
SECRET_KEY="your-super-secret-key-change-in-production"
ALGORITHM="HS256"
ACCESS_TOKEN_EXPIRE_MINUTES=115200

# CORS Allowed Origins
BACKEND_CORS_ORIGINS=["http://localhost:5173", "http://localhost:3000"]

# OpenAI API Key (For AI Matching & Recommendations)
OPENAI_API_KEY="sk-proj-your-openai-api-key"
```

### Frontend Environment Variables (`frontend/.env`)

Copy `frontend/.env.example` to `frontend/.env`:

```bash
cd frontend
cp .env.example .env
```

Key frontend configuration parameters:

```ini
# Base REST API URL (Leave blank to use mock seed data for offline frontend dev)
VITE_API_BASE_URL="http://localhost:8000/api/v1"

# Enable Feature Flags
VITE_ENABLE_ANALYTICS=false
VITE_APP_TITLE="DevLink — Where Builders Connect"
```

---

## 3. Step-by-Step Local Setup

### Option A: Standard Local Setup (Recommended)

#### Step 1: Clone the Repository
```bash
git clone https://github.com/Babin123456/devlink.git
cd devlink
```

#### Step 2: Backend Setup (FastAPI + Python)
```bash
cd backend

# Create a Python virtual environment
python -m venv venv

# Activate the virtual environment:
# Linux/macOS:
source venv/bin/activate
# Windows (PowerShell):
# .\venv\Scripts\Activate.ps1
# Windows (Command Prompt):
# venv\Scripts\activate.bat

# Install backend dependencies
pip install --upgrade pip
pip install -r requirements.txt

# Start the FastAPI reload development server
uvicorn app.main:app --reload --port 8000
```
*The FastAPI REST API and interactive Swagger documentation will be available at `http://localhost:8000/docs`.*

#### Step 3: Frontend Setup (React 19 + TanStack Router + Vite)
Open a new terminal window:
```bash
cd devlink/frontend

# Install dependencies
npm install

# Start the Vite development server
npm run dev
```
*The DevLink web application will launch at `http://localhost:5173`.*

#### Step 4: Seed Demo Data (recommended)

A freshly migrated database is empty, which means every screen renders its
empty state: the dashboard has nothing to show, search returns nothing, and
messaging needs two users and a conversation before it does anything at all.

```bash
cd devlink/backend
python -m scripts.seed_database
```

That populates users, skills, projects, memberships, builder flares,
applications, conversations with messages, notifications, and bookmarks. Then
sign in with any demo account:

| Account | Role |
| --- | --- |
| `admin@example.com` | superuser — admin routes are reachable |
| `aditialmeida@example.com` | regular user |

The password for every demo account is `DevlinkDemo!2026`, and the script
prints it at the end of a run.

**Options**

| Flag | Effect |
| --- | --- |
| `--users N`, `--projects N` | Control how much data is generated |
| `--reset` | Delete previously seeded rows first, then re-seed |
| `--dry-run` | Report what would be written and roll back |
| `--quiet` | Only print the summary |
| `--force` | Required if `ENVIRONMENT` is `production` |

Two things worth knowing:

- **Re-running is safe.** Rows are matched on a natural key and updated rather
  than duplicated, so `python -m scripts.seed_database` twice leaves the same
  database as running it once.
- **The output is deterministic.** The same flags produce the same users,
  projects, and IDs on every machine, so a screenshot in a pull request means
  the same thing to the reviewer as it did to you.

`--reset` only removes rows the seeder created — they are tagged with a `[demo]`
marker — so anything you made by hand while testing survives.

> The script refuses to run when `ENVIRONMENT=production`, because it writes
> accounts whose password is published in this document.

---

### Option B: Docker Compose Setup

If you have Docker installed, you can start the entire stack (PostgreSQL + FastAPI Backend + React Frontend) with one command:

```bash
# From the root workspace directory
docker-compose -f docker-compose.dev.yml up --build
```

---

## 4. Troubleshooting Guide

If you encounter issues during setup, follow this diagnostic workflow:

1. **Verify Software Versions**: Run `node -v`, `npm -v`, `python --version`, and `git --version` to ensure version constraints are satisfied.
2. **Check Port Availability**: Ensure ports `5173` (Frontend) and `8000` (Backend) are not occupied by other background services.
3. **Reinstall Dependencies**: If packages fail to resolve, remove lock files and reinstall:
   ```bash
   # Frontend reset
   cd frontend && rm -rf node_modules package-lock.json && npm install

   # Backend reset
   cd backend && rm -rf venv && python -m venv venv && pip install -r requirements.txt
   ```
4. **Inspect Terminal Logs**: Review backend Uvicorn logs and browser developer console output for explicit stack traces.

---

## 5. Common Errors & Resolution Matrix

| Error Message / Symptom | Root Cause | Resolution |
| :--- | :--- | :--- |
| `ModuleNotFoundError: No module named 'app'` | Virtual environment not active or executed from wrong folder | Activate venv (`source venv/bin/activate`) and run uvicorn from `backend/` directory. |
| `Error: listen EADDRINUSE: address already in use :::5173` | Port 5173 is occupied by another process | Stop the running process or start Vite on custom port: `npm run dev -- --port 5174`. |
| `CORS Error: Access to fetch has been blocked by CORS policy` | Frontend origin is missing from backend `BACKEND_CORS_ORIGINS` | Add `"http://localhost:5173"` to `BACKEND_CORS_ORIGINS` list in `backend/.env`. |
| `psycopg2.OperationalError: could not connect to server` | PostgreSQL service is not running or wrong `DATABASE_URL` | Start local Postgres service or fallback to SQLite in `backend/.env`. |
| `npm ERR! code ERESOLVE / peer dependency conflict` | Package manager version mismatch | Run `npm install --legacy-peer-deps` or use Node 20+. |
| `husky - pre-commit script failed (code 1)` | Staged code fails ESLint or Prettier formatting | Run `npm run format` and `npm run lint` in `frontend/` to fix style warnings before committing. |
| `TypeError: Cannot read properties of undefined` | Missing required environment variable | Verify `.env` file exists in `frontend/` and `backend/` with all necessary keys. |
| `tsc --noEmit failed with exit code 1` | TypeScript type check errors in frontend components | Run `npm run typecheck` in `frontend/` to pinpoint type errors and resolve annotations. |

---

## Related Onboarding Documents
* [Development Guide](development.md)
* [Architecture Documentation](architecture.md)
* [Deployment Guide](deployment.md)
* [Coding Standards](coding-standards.md)
