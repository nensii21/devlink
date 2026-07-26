# DevLink Development Guide

Welcome to the DevLink Development Guide. This document provides clear technical details regarding project folder structure, coding style standards, local development workflows, running automated tests, and debugging procedures.

---

## 1. Folder Structure

DevLink follows a clean modular directory layout separating frontend UI components from backend service modules.

```
devlink/
├── .github/              # Issue templates, PR templates, and GitHub Action workflows
├── docs/                 # System architecture, deployment, and contribution documentation
├── frontend/             # Next.js / React TypeScript frontend application
│   ├── src/
│   │   ├── api/          # API integration modules and HTTP client callers
│   │   ├── assets/       # Static assets, SVG icons, and images
│   │   ├── components/   # UI components grouped by domain (auth, chat, profile, project, shared, ui)
│   │   ├── hooks/        # Custom React hooks (useAuth, useDebounce, useTeamMatch, etc.)
│   │   ├── lib/          # Helper utilities, validation schemas (Zod), and formatters
│   │   ├── matching/     # Client-side matching algorithm & scoring engine logic
│   │   ├── routes/       # Application routing configuration and pages
│   │   ├── services/     # Frontend data fetching services
│   │   ├── types/        # TypeScript type definitions and interfaces
│   │   └── test-setup.ts # Testing setup configuration (Vitest / React Testing Library)
│   ├── package.json
│   ├── tsconfig.json
│   └── vite.config.ts
├── backend/              # Python FastAPI backend application
│   ├── app/
│   │   ├── api/          # FastAPI REST endpoint routes
│   │   ├── core/         # Security, JWT, hashing, database engine configuration
│   │   ├── db/           # SQLAlchemy models and database session setup
│   │   ├── schemas/      # Pydantic data validation schemas
│   │   ├── services/     # Business logic services and external API wrappers
│   │   └── main.py       # FastAPI application entry point
│   ├── alembic/          # Database schema migrations
│   ├── tests/            # Pytest suite for backend testing
│   ├── requirements.txt
│   └── pyproject.toml
└── README.md
```

---

## 2. Coding Style

### Frontend Guidelines
* **TypeScript First**: Strict mode enabled. Explicitly type component props, hook return values, and API responses. Avoid using `any`.
* **Functional Components**: Write functional React components using hooks.
* **Component Modularity**: Keep components small, focused, and organized by feature directory.
* **Styling**: Use utility classes (Tailwind CSS v4) adhering to existing spacing, color palette, and typography design tokens.

### Backend Guidelines
* **PEP 8 Compliance**: Follow standard Python code formatting.
* **Type Hints**: Annotate all function signatures and parameters using type annotations.
* **Pydantic Validation**: Pass incoming JSON payloads through Pydantic schemas before processing in service layers.
* **Explicit Exceptions**: Raise appropriate HTTPExceptions (e.g. `400 Bad Request`, `401 Unauthorized`, `404 Not Found`) with descriptive details.

---

## 3. Local Development

### Setting Up Environment Variables

Ensure `.env` files exist in both `backend/` and `frontend/` folders (refer to [Deployment Guide](deployment.md#environment-variables) for configuration parameters).

### Backend Development Server

```bash
cd backend
python -m venv venv

# Activate virtual environment:
# Linux/macOS:
source venv/bin/activate
# Windows:
# venv\Scripts\activate

pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

The interactive API documentation (Swagger UI) is accessible at `http://localhost:8000/docs`.

### Frontend Development Server

```bash
cd frontend
npm install
npm run dev
```

The frontend application runs on `http://localhost:5173`.

---

## 4. Running Tests

### Frontend Testing (Vitest & React Testing Library)

To execute frontend unit and integration tests:

```bash
cd frontend

# Run tests once
npm test

# Run tests in watch mode
npm run test:watch

# Check linting & type consistency
npm run lint
```

### Backend Testing (Pytest)

To execute backend unit and API integration tests:

```bash
cd backend
source venv/bin/activate

# Run pytest suite
pytest

# Run pytest with coverage report
pytest --cov=app tests/
```

---

## 5. Debugging

### Debugging the Frontend
* **React Developer Tools**: Inspect component hierarchy, props, state, and context values.
* **Browser Console & Network Tab**: Monitor outgoing API requests, HTTP status responses, payload formatting, and console output.
* **VS Code Debugger**: Add launch configuration for Chrome/Edge debugging in `.vscode/launch.json`.

### Debugging the Backend
* **FastAPI Auto-Reload & Logs**: View server logs directly in the terminal where `uvicorn app.main:app --reload` is running.
* **Python Debugger (`breakpoint()`)**: Insert standard `breakpoint()` calls in Python service or router files to pause execution and inspect variables in the terminal shell.
* **VS Code FastAPI Debugger**: Configure `.vscode/launch.json`:

```json
{
  "version": "0.2.0",
  "configurations": [
    {
      "name": "Python: FastAPI",
      "type": "debugpy",
      "request": "launch",
      "module": "uvicorn",
      "args": ["app.main:app", "--reload", "--port", "8000"],
      "jinja": true,
      "justMyCode": true
    }
  ]
}
```

---

## Related Documents
* [Architecture Documentation](architecture.md)
* [Deployment Guide](deployment.md)
* [Coding Standards](coding-standards.md)
