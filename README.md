<p align="center">
  <img src="docs/screenshots/hero-banner.png" alt="DevLink" width="100%">
</p>

<h2 align="center">DevLink</h2>

<p align="center">Open-source platform for developer collaboration, project discovery, and team formation.</p>

<p align="center">
  <a href="https://github.com/nensii21/devlink/actions"><img src="https://img.shields.io/github/actions/workflow/status/nensii21/devlink/ci.yml?branch=main&style=flat-square&label=build" alt="Build"></a>
  <a href="https://github.com/nensii21/devlink/releases"><img src="https://img.shields.io/github/v/release/nensii21/devlink?style=flat-square" alt="Release"></a>
  <a href="https://github.com/nensii21/devlink/blob/main/LICENSE"><img src="https://img.shields.io/github/license/nensii21/devlink?style=flat-square" alt="License"></a>
  <a href="https://hub.docker.com"><img src="https://img.shields.io/badge/docker-ready-blue?style=flat-square&logo=docker" alt="Docker"></a>
  <a href="https://react.dev"><img src="https://img.shields.io/badge/react-19-blue?style=flat-square&logo=react" alt="React"></a>
  <a href="https://fastapi.tiangolo.com"><img src="https://img.shields.io/badge/fastapi-0.110-green?style=flat-square&logo=fastapi" alt="FastAPI"></a>
  <a href="https://github.com/nensii21/devlink/stargazers"><img src="https://img.shields.io/github/stars/nensii21/devlink?style=flat-square" alt="Stars"></a>
  <a href="https://github.com/nensii21/devlink/graphs/contributors"><img src="https://img.shields.io/github/contributors/nensii21/devlink?style=flat-square" alt="Contributors"></a>
</p>

---

## Table of Contents

- [Overview](#overview)
- [Screenshots](#screenshots)
- [Features](#features)
- [Tech Stack](#tech-stack)
- [Getting Started](#getting-started)
- [Environment Variables](#environment-variables)
- [Available Scripts](#available-scripts)
- [Project Structure](#project-structure)
- [Deployment](#deployment)
- [Testing](#testing)
- [Security](#security)
- [Roadmap](#roadmap)
- [Contributing](#contributing)
- [Acknowledgements](#acknowledgements)
- [License](#license)

---

## Overview

DevLink is an open-source developer collaboration platform. It helps developers find project collaborators, apply to open-source projects, communicate in real time, and build portfolios backed by linked GitHub activity.

**Current Status:** Active development — early release, open to contributors. See [Roadmap](#roadmap) for planned features.

**Documentation:**
- [Architecture](docs/architecture.md)
- [API Reference](docs/api.md)
- [Development Setup](docs/development.md)
- [Deployment Guide](docs/deployment.md)
- [Coding Standards](docs/coding-standards.md)
- [WebSockets](docs/WEBSOCKETS.md)

---

## Screenshots

| Dashboard | Project Marketplace |
| :---: | :---: |
| ![Dashboard](docs/screenshots/dashboard.png) | ![Projects](docs/screenshots/projects.png) |

| Direct Messaging | Builder Activity Feed |
| :---: | :---: |
| ![Messaging](docs/screenshots/messaging.png) | ![Feed](docs/screenshots/feed.png) |

| Authentication | Mobile View |
| :---: | :---: |
| ![Login](docs/screenshots/login.png) | ![Mobile](docs/screenshots/mobile.png) |

---

## Features

| Feature | Description |
| :--- | :--- |
| Developer Profiles | Portfolio pages with skills, GitHub stats, experience, and social links |
| Project Marketplace | Browse, post, and apply to open-source projects and team openings |
| Team Applications | Structured role-based application flow with status tracking |
| Real-Time Messaging | WebSocket-powered direct messaging with presence indicators |
| Builder Activity Feed | Community updates, project announcements, and contributor flares |
| Search & Discovery | Full-text search across developers, projects, issues, and skills |
| Repository Linking | Link GitHub repositories to project profiles |
| Bookmarks & Saved Searches | Save projects and store custom search queries |
| Notifications | Real-time event notifications delivered via WebSockets |

```text
                    Browser

## Tech Stack

### Frontend
| Technology | Version |
| :--- | :--- |
| React | 19 |
| TypeScript | 5.8 |
| Vite | 8 |
| Tailwind CSS | v4 |
| TanStack Router | v1 |
| TanStack Query | v5 |
| Framer Motion | 12 |

### Backend
| Technology | Version |
| :--- | :--- |
| Python | 3.11+ |
| FastAPI | 0.110 |
| Pydantic | v2 |
| SQLAlchemy | 2.0 |
| Asyncpg | — |

### Database & Infrastructure
| Technology | Role |
| :--- | :--- |
| PostgreSQL 15+ | Primary relational database |
| Redis 7+ | Cache, Pub/Sub, task broker |
| Celery | Asynchronous task processing |

### DevOps
| Technology | Role |
| :--- | :--- |
| Docker & Docker Compose | Containerization and local environment |
| DevContainers | VS Code & GitHub Codespaces support |
| GitHub Actions | CI/CD pipelines |

---

## Getting Started

### Prerequisites

- Node.js 20+
- Python 3.11+
- Docker & Docker Compose (recommended)
- PostgreSQL 15+ and Redis 7+ (if running without Docker)

### Option 1: Docker Compose

```bash
git clone https://github.com/nensii21/devlink.git
cd devlink
docker-compose -f docker-compose.dev.yml up --build
```

- Frontend: `http://localhost:5173`
- Backend API: `http://localhost:8000`
- Swagger UI: `http://localhost:8000/docs`

### Option 2: Manual Setup

```bash
git clone https://github.com/nensii21/devlink.git
cd devlink
```

**Backend:**

```bash
cd backend
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env            # configure your variables
alembic upgrade head
uvicorn app.main:app --reload
```

**Frontend:**

```bash
cd frontend
npm install
cp .env.example .env            # configure your variables
npm run dev
```

---

## Environment Variables

### Backend (`backend/.env`)

| Variable | Required | Description |
| :--- | :---: | :--- |
| `DATABASE_URL` | Yes | PostgreSQL connection string |
| `REDIS_URL` | Yes | Redis connection URI |
| `SECRET_KEY` | Yes | Secret key for JWT signing |
| `ENVIRONMENT` | No | `development`, `staging`, or `production` |
| `GITHUB_CLIENT_ID` | No | GitHub OAuth App client ID |
| `GITHUB_CLIENT_SECRET` | No | GitHub OAuth App client secret |
| `CORS_ORIGINS` | No | Allowed CORS origins (JSON list) |

### Frontend (`frontend/.env`)

| Variable | Required | Description |
| :--- | :---: | :--- |
| `VITE_API_URL` | Yes | Backend API base URL |
| `VITE_APP_NAME` | No | Application display name |

---

## Available Scripts

### Frontend

```bash
npm run dev        # Start development server
npm run build      # Build production bundle
npm run test       # Run unit tests (Vitest)
npm run lint       # Run ESLint
npm run format     # Format with Prettier
npm run typecheck  # TypeScript type check
```

### Backend

```bash
uvicorn app.main:app --reload          # Start development server
pytest                                 # Run test suite
pytest --cov=app                       # Run with coverage
alembic upgrade head                   # Apply migrations
alembic revision --autogenerate -m ""  # Generate migration
```

---

## Project Structure

```
devlink/
├── .devcontainer/          # DevContainer configuration
├── .github/                # GitHub Actions workflows and templates
├── backend/
│   ├── alembic/            # Database migrations
│   ├── app/
│   │   ├── core/           # Config, security, events, cache
│   │   ├── middleware/      # Rate limiting, headers, request ID
│   │   ├── models/         # SQLAlchemy ORM models
│   │   ├── routers/        # API route handlers
│   │   ├── schemas/        # Pydantic validation schemas
│   │   ├── services/       # Business logic layer
│   │   └── main.py         # Application entrypoint
│   ├── tests/
│   ├── Dockerfile
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── api/            # HTTP client modules
│   │   ├── components/     # UI components
│   │   ├── hooks/          # Custom React hooks
│   │   └── routes/         # Page routes
│   ├── Dockerfile
│   └── package.json
├── docs/                   # Documentation files
├── docker-compose.dev.yml
├── CONTRIBUTING.md
└── README.md
```

---

## Deployment

### Docker Compose (Local / Self-Hosted)

```bash
docker-compose -f docker-compose.dev.yml up --build
```

See [docker-compose.dev.yml](docker-compose.dev.yml) for full service configuration (PostgreSQL, Redis, Backend, Frontend).

### DevContainers

Open in VS Code and select **Remote-Containers: Reopen in Container**, or launch directly in [GitHub Codespaces](https://codespaces.new/nensii21/devlink). The `.devcontainer/` setup installs dependencies and forwards all ports automatically.

### Cloud Platforms

- **Frontend:** Deploy `frontend/` to [Vercel](https://vercel.com) or [Netlify](https://netlify.com).
- **Backend:** Deploy `backend/Dockerfile` to [Render](https://render.com), [Railway](https://railway.app), or AWS ECS.
- **Database:** Use managed PostgreSQL (e.g. AWS RDS, Supabase) and managed Redis (e.g. Upstash, Redis Cloud).

Full deployment instructions: [docs/deployment.md](docs/deployment.md)

---

## Testing

**Backend:**

```bash
cd backend
pytest -v
pytest --cov=app --cov-report=term-missing
```

**Frontend:**

```bash
cd frontend
npm run test
npm run typecheck
```

---

## Security

- Passwords hashed with Bcrypt.
- JWT-based authentication with access and refresh tokens.
- GitHub OAuth 2.0 support.
- Rate limiting via `SlowAPI` middleware.
- Security headers enforced (CSP, HSTS, X-Frame-Options, X-Content-Type-Options).
- Input validation via Pydantic v2.
- Parameterized queries through SQLAlchemy ORM.

To report a vulnerability, see [SECURITY.md](SECURITY.md).

---

## Roadmap

| Version | Features | Status |
| :--- | :--- | :--- |
| `v0.1.0` | User auth, profiles, project marketplace, GitHub OAuth | Completed |
| `v0.2.0` | WebSocket messaging, notifications, team applications, repo linking | Completed |
| `v0.3.0` | Builder activity feed, saved searches, bookmark collections, search improvements | In Progress |
| `v0.4.0` | Organization workspaces, issue tracking, project analytics | Planned |
| `v1.0.0` | Mobile application, public API, extended integrations | Planned |

---

## Contributing

Contributions are welcome. Please read [CONTRIBUTING.md](CONTRIBUTING.md) and [CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md) before submitting a pull request.

```bash
git checkout -b feat/your-feature
git commit -m "feat(scope): description"
git push origin feat/your-feature
```

Use [Conventional Commits](https://www.conventionalcommits.org/) for commit messages.

Nensi Patel

## Acknowledgements

- [FastAPI](https://fastapi.tiangolo.com) — backend framework
- [React](https://react.dev) — frontend library
- [TanStack](https://tanstack.com) — routing and data fetching
- [Radix UI](https://www.radix-ui.com) — accessible UI primitives
- [SQLAlchemy](https://www.sqlalchemy.org) — ORM and async database access
- All contributors and ECSoc 2026 participants

---

## License

MIT License — see [LICENSE](LICENSE) for details.
