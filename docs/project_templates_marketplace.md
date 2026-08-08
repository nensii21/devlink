# Project Templates Marketplace Documentation (#596)

DevLink **Project Templates Marketplace** allows developers to publish, discover, star, and clone production-ready project blueprints and starters.

---

## 1. Features

- **Browse & Search**: Filter templates by category (`web-app`, `mobile-app`, `ai-ml`, `cli-tool`, `backend-service`, `library`, `other`), tech stack tags, or full-text query.
- **Sorting**: Order templates by `popular` (stars & clone count), `clones` (most cloned), or `recent` (latest published).
- **Clone Template**: Single-click clone that initializes a new DevLink `Project` pre-configured with the template's details, category, and tech stack.
- **Star & Favorite**: Authenticated users can favorite templates with live counter updates.
- **Publish Template**: Users can publish open-source starters or proprietary project blueprints with tech stack tags, feature lists, repository links, and live demo URLs.

---

## 2. Architecture & Data Model

- **Model**: `ProjectTemplate` and `ProjectTemplateFavorite` in `backend/app/models/project_template.py`
- **Service**: `ProjectTemplateService` in `backend/app/services/project_template_service.py`
- **Router**: `backend/app/routers/project_templates.py`
- **Frontend Route**: `frontend/src/routes/_app.templates.tsx`
- **Frontend API Module**: `frontend/src/api/modules/projectTemplates.ts`

---

## 3. API Reference

### 1. List & Search Templates
`GET /api/templates?search={search}&category={category}&sort_by={popular|recent|clones}&skip=0&limit=20`

### 2. Get Template Details
`GET /api/templates/{template_id}`

### 3. Create / Publish Template
`POST /api/templates`

**Request Body:**
```json
{
  "title": "Next.js Fullstack SaaS Starter",
  "description": "A modern production-ready starter with Auth, Stripe, and PostgreSQL.",
  "category": "web-app",
  "tech_stack": ["Next.js", "TailwindCSS", "PostgreSQL"],
  "features": ["OAuth Authentication", "Subscription Billing", "Dark Mode"],
  "repository_url": "https://github.com/example/starter",
  "demo_url": "https://starter-demo.example.com"
}
```

### 4. Toggle Favorite
`POST /api/templates/{template_id}/favorite`

**Response:**
```json
{
  "success": true,
  "is_favorited": true,
  "stars_count": 6
}
```

### 5. Clone Template into Project
`POST /api/templates/{template_id}/clone`

**Request Body:**
```json
{
  "new_project_title": "My Custom SaaS App"
}
```

**Response:** Returns newly initialized `Project` model response.

---

## 4. Running Tests

Execute backend unit & integration tests:
```bash
cd backend
./venv/bin/pytest tests/test_project_templates_marketplace.py -v
```

Expected output: **4 passed**.
