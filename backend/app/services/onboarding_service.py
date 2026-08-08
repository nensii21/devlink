from app.schemas.onboarding import OnboardingRequest, OnboardingResponse, BeginnerIssue

class OnboardingService:
    @staticmethod
    def get_onboarding_guidance(payload: OnboardingRequest) -> OnboardingResponse:
        structure = [
            "backend/app/routers/ - API route controllers and endpoints",
            "backend/app/services/ - Business logic and AI service integrations",
            "backend/app/schemas/ - Pydantic validation models",
            "frontend/src/components/ - Reusable UI components",
            "frontend/src/routes/ - TanStack file-based routing structure"
        ]

        issues = [
            BeginnerIssue(title="Fix minor styling and padding issues in TopNavbar", issue_url="#102", labels=["good first issue", "frontend"]),
            BeginnerIssue(title="Add unit tests for search keyword fallback service", issue_url="#115", labels=["good first issue", "backend"])
        ]

        docs = [
            "CONTRIBUTING.md - Contribution guidelines and PR workflow",
            "ARCHITECTURE.md - High-level system design overview",
            "CODING_STANDARDS.md - Linting, formatting, and style guide"
        ]

        standards = [
            "Follow PEP 8 for Python code and strict TypeScript typing on the frontend.",
            "Ensure all code changes pass pre-commit hooks (eslint, prettier, ruff).",
            "Reference related issue numbers in commit messages and pull requests."
        ]

        return OnboardingResponse(
            project_overview=f"Welcome! As a {payload.experience_level} contributor with experience in {', '.join(payload.user_skills) or 'development'}, this custom guide is tailored to help you make your first contribution seamlessly.",
            project_structure=structure,
            beginner_issues=issues,
            relevant_docs=docs,
            coding_standards=standards
        )
    