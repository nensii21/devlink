# Contributing to DevLink

Thank you for contributing to DevLink!

DevLink is an open-source developer collaboration platform that helps developers connect, build projects, showcase portfolios, and contribute to open source. The project is beginner-friendly and welcomes students, open-source enthusiasts, and ECSoc 2026 contributors.

Whether you're fixing bugs, improving documentation, designing UI, or implementing new features, every contribution helps make DevLink better.

---

# Before You Start

Before contributing, please:

- Read the README.md
- Read the CODE_OF_CONDUCT.md
- Check existing Issues before creating a new one
- Comment on an issue before starting work
- Wait until a maintainer assigns the issue
- Keep pull requests focused on a single issue
- Follow the project's coding standards

For ECSoc participants, please mention **ECSoc 2026** in your issue or pull request.

---

# Good First Contribution Areas

New contributors can start with:

- Documentation improvements
- Landing page enhancements
- UI consistency fixes
- Responsive design improvements
- Accessibility improvements
- Dark Mode
- Loading Skeletons
- Form validation
- API documentation
- Bug fixes
- Testing improvements

Look for labels such as:

- good first issue
- frontend
- backend
- documentation
- accessibility
- enhancement
- help wanted
- ecsoc

---

# Tech Stack

## Frontend

- Next.js 15
- React 19
- TypeScript
- Tailwind CSS v4
- React Hook Form
- Zod

## Backend

- Python
- FastAPI
- PostgreSQL
- SQLAlchemy
- JWT Authentication
- OAuth

## Realtime

- WebSockets

## AI

- OpenAI API
- MCP (Model Context Protocol)

## DevOps

- Docker
- GitHub Actions
- Vercel

---

# Local Setup

## Prerequisites

- Python 3.11+
- Node.js 20+
- npm
- Git
- Docker (Optional)

Clone the repository

```bash
git clone https://github.com/<org>/devlink.git

cd devlink
```

Backend

```bash
cd backend

python -m venv venv

source venv/bin/activate

pip install -r requirements.txt

uvicorn app.main:app --reload
```

Frontend

```bash
cd frontend

npm install

npm run dev
```

---

# Project Structure

```
frontend/
    src/
        app/
        components/
        pages/
        hooks/
        lib/

backend/
    app/
        api/
        models/
        schemas/
        services/
        core/

docs/

.github/
```

---

# Development Workflow

1. Fork the repository.

2. Create a branch.

Example

```
feature/profile-card

fix/navbar-overflow

docs/api-documentation
```

3. Make your changes.

4. Test your changes.

5. Commit using Conventional Commits.

6. Push your branch.

7. Open a Pull Request.

---

# Pull Request Guidelines

Every PR should include:

- Clear description
- Linked issue

Example

```
Closes #45
```

Include

- Screenshots for UI changes
- Testing performed
- Notes if required

Keep pull requests small and reviewable.

---

# Commit Message Convention

Use Conventional Commits.

Examples

```
feat(profile): add profile completion widget

fix(auth): resolve JWT refresh issue

docs(api): update authentication endpoints

refactor(ui): reuse button component
```

Allowed commit types

- feat
- fix
- docs
- style
- refactor
- test
- chore

---

# Testing

Frontend

```bash
npm run lint

npm run build
```

Backend

```bash
pytest
```
## 🌱 Contributor Mentorship Program
New to open source or our codebase? Check out our [Contributor Mentorship Program](./docs/mentorship/README.md) for step-by-step beginner roadmaps, weekly checklists, and dedicated mentor guidance!

Please ensure:

- No TypeScript errors
- No Python errors
- Build succeeds
- Existing functionality is not broken

---

# Coding Guidelines

## Frontend

- Use TypeScript
- Use functional React components
- Reuse existing UI components
- Keep components modular
- Follow the design system
- Maintain accessibility

## Backend

- Follow PEP8
- Use type hints
- Write reusable services
- Keep API responses consistent
- Validate request data

---

# Accessibility

All new UI should:

- Support keyboard navigation
- Include ARIA labels
- Use semantic HTML
- Maintain WCAG AA color contrast
- Display visible focus states

---

# Documentation

If your PR changes:

- API
- Setup
- Environment variables
- Folder structure

please update the documentation accordingly.

---

# Issue Assignment Policy

To ensure fair participation:

- Comment before starting work.
- Wait until a maintainer assigns the issue.
- Do not submit PRs for unassigned issues.
- Inactive issues may be reassigned after a reasonable period.

---

# Code Review

Maintainers will review:

- Code quality
- Performance
- Accessibility
- Responsiveness
- Documentation
- Testing

Requested changes should be addressed in the same pull request.

---

# ECSoc Contribution Scoring

Difficulty labels

- beginner
- intermediate
- advanced
- critical

Area labels

- frontend
- backend
- documentation
- AI
- UI/UX
- accessibility
- authentication
- DevOps
- testing

Quality labels

- clean
- exceptional

These labels are applied by maintainers after review.

---

# What Not To Commit

Do **not** commit:

```
node_modules/

dist/

build/

coverage/

.pytest_cache/

__pycache__/

.env

.env.local

.vscode/

.idea/

*.log
```

Generated files should remain ignored by Git.

---

# Need Help?

If you need assistance:

- Ask your question in the GitHub Issue.
- Use Pull Request comments for implementation discussions.
- Be respectful and constructive when interacting with other contributors.

---

# Thank You

Thank you for contributing to DevLink and being part of the ECSoc 2026 community.

Every contribution—big or small—helps build a better platform for developers around the world.
