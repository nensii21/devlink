"""
AI Repository Quality Analyzer Service.

Analyzes GitHub repositories and generates an overall quality score based on:
- README quality
- Documentation
- License
- Test coverage
- CI/CD setup
- Recent activity
- Open issues

Uses the GitHub API for data collection and OpenAI for generating suggestions.
"""

from __future__ import annotations

import logging
import re
from datetime import datetime, timezone
from typing import Any

# pyrefly: ignore [missing-import]
import httpx

# pyrefly: ignore [missing-import]
from openai import OpenAI

from app.core.cache import cache_manager
from app.core.config import settings
from app.schemas.repository_quality import (
    ImprovementSuggestion,
    MetricScore,
    QualityMetric,
    RepositoryInfo,
    RepositoryQualityResponse,
)

logger = logging.getLogger(__name__)

CACHE_TTL = 1800  # 30 minutes

# Metric weights (must sum to 1.0)
METRIC_WEIGHTS: dict[QualityMetric, float] = {
    QualityMetric.README: 0.20,
    QualityMetric.DOCUMENTATION: 0.15,
    QualityMetric.LICENSE: 0.10,
    QualityMetric.TEST_COVERAGE: 0.20,
    QualityMetric.CI_CD: 0.15,
    QualityMetric.RECENT_ACTIVITY: 0.10,
    QualityMetric.OPEN_ISSUES: 0.10,
}


def _parse_github_url(url: str) -> tuple[str, str]:
    """Extract owner and repo name from a GitHub URL."""
    url = url.strip().rstrip("/")
    url = re.sub(r"\.git$", "", url)

    patterns = [
        r"github\.com/([^/]+)/([^/]+)$",
        r"github\.com/([^/]+)/([^/]+)/?$",
    ]

    for pattern in patterns:
        match = re.search(pattern, url)
        if match:
            return match.group(1), match.group(2)

    raise ValueError(f"Invalid GitHub URL: {url}")


class RepositoryQualityService:
    """Service for analyzing GitHub repository quality."""

    @staticmethod
    def analyze_repository(repository_url: str) -> RepositoryQualityResponse:
        """
        Analyze a GitHub repository and return a quality report.

        Results are cached for 30 minutes.
        """
        cache_key = f"repo_quality:{repository_url.lower().rstrip('/')}"
        cached = cache_manager.get(cache_key)
        if cached is not None:
            return RepositoryQualityResponse(**cached)

        owner, name = _parse_github_url(repository_url)
        repo_data = RepositoryQualityService._fetch_repo_data(owner, name)
        readme_content = RepositoryQualityService._fetch_readme(owner, name)
        file_tree = RepositoryQualityService._fetch_file_tree(owner, name)
        recent_commits = RepositoryQualityService._fetch_recent_commits(owner, name)
        workflows = RepositoryQualityService._fetch_workflows(owner, name)
        contributors = RepositoryQualityService._fetch_contributors(owner, name)

        repo_info = RepositoryInfo(
            stars=repo_data.get("stargazers_count", 0),
            forks=repo_data.get("forks_count", 0),
            open_issues=repo_data.get("open_issues_count", 0),
            language=repo_data.get("language"),
            description=repo_data.get("description"),
            default_branch=repo_data.get("default_branch", "main"),
            last_push=repo_data.get("pushed_at"),
            topics=repo_data.get("topics", []),
        )

        metrics = RepositoryQualityService._compute_metrics(
            repo_data=repo_data,
            readme_content=readme_content,
            file_tree=file_tree,
            recent_commits=recent_commits,
            workflows=workflows,
            contributors=contributors,
        )

        overall_score = sum(m.score * m.weight for m in metrics) / sum(
            m.weight for m in metrics
        )

        grade = RepositoryQualityService._score_to_grade(overall_score)

        suggestions = RepositoryQualityService._generate_suggestions(
            metrics=metrics,
            repo_info=repo_info,
            readme_content=readme_content,
            file_tree=file_tree,
        )

        summary = RepositoryQualityService._generate_summary(
            repository_url=repository_url,
            repo_info=repo_info,
            metrics=metrics,
            overall_score=overall_score,
            grade=grade,
        )

        response = RepositoryQualityResponse(
            repository_url=repository_url,
            owner=owner,
            name=name,
            overall_score=round(overall_score, 2),
            grade=grade,
            metrics=metrics,
            suggestions=suggestions,
            summary=summary,
            repository_info=repo_info,
        )

        cache_manager.set(cache_key, response.model_dump(), ttl=CACHE_TTL)
        return response

    @staticmethod
    def _fetch_repo_data(owner: str, name: str) -> dict[str, Any]:
        """Fetch repository metadata from GitHub API."""
        try:
            with httpx.Client(timeout=15) as client:
                resp = client.get(
                    f"https://api.github.com/repos/{owner}/{name}",
                    headers={"Accept": "application/vnd.github.v3+json"},
                )
                resp.raise_for_status()
                return resp.json()
        except Exception as e:
            logger.error("Failed to fetch repo data: %s", e)
            return {}

    @staticmethod
    def _fetch_readme(owner: str, name: str) -> str:
        """Fetch README content from GitHub API."""
        try:
            with httpx.Client(timeout=15) as client:
                resp = client.get(
                    f"https://api.github.com/repos/{owner}/{name}/readme",
                    headers={
                        "Accept": "application/vnd.github.v3.raw",
                    },
                )
                if resp.status_code == 200:
                    return resp.text
        except Exception as e:
            logger.error("Failed to fetch README: %s", e)
        return ""

    @staticmethod
    def _fetch_file_tree(owner: str, name: str) -> list[str]:
        """Fetch the top-level file tree."""
        try:
            with httpx.Client(timeout=15) as client:
                resp = client.get(
                    f"https://api.github.com/repos/{owner}/{name}/contents/",
                    headers={"Accept": "application/vnd.github.v3+json"},
                )
                if resp.status_code == 200:
                    return [item.get("name", "") for item in resp.json()]
        except Exception as e:
            logger.error("Failed to fetch file tree: %s", e)
        return []

    @staticmethod
    def _fetch_recent_commits(owner: str, name: str) -> list[dict[str, Any]]:
        """Fetch recent commits."""
        try:
            with httpx.Client(timeout=15) as client:
                resp = client.get(
                    f"https://api.github.com/repos/{owner}/{name}/commits",
                    params={"per_page": 10},
                    headers={"Accept": "application/vnd.github.v3+json"},
                )
                if resp.status_code == 200:
                    return resp.json()
        except Exception as e:
            logger.error("Failed to fetch commits: %s", e)
        return []

    @staticmethod
    def _fetch_workflows(owner: str, name: str) -> list[dict[str, Any]]:
        """Fetch GitHub Actions workflows."""
        try:
            with httpx.Client(timeout=15) as client:
                resp = client.get(
                    f"https://api.github.com/repos/{owner}/{name}/actions/workflows",
                    headers={"Accept": "application/vnd.github.v3+json"},
                )
                if resp.status_code == 200:
                    return resp.json().get("workflows", [])
        except Exception as e:
            logger.error("Failed to fetch workflows: %s", e)
        return []

    @staticmethod
    def _fetch_contributors(owner: str, name: str) -> list[dict[str, Any]]:
        """Fetch contributor count."""
        try:
            with httpx.Client(timeout=15) as client:
                resp = client.get(
                    f"https://api.github.com/repos/{owner}/{name}/contributors",
                    params={"per_page": 1, "anon": "true"},
                    headers={"Accept": "application/vnd.github.v3+json"},
                )
                if resp.status_code == 200:
                    link_header = resp.headers.get("link", "")
                    match = re.search(r'page=(\d+)>; rel="last"', link_header)
                    if match:
                        return [{"total_pages": int(match.group(1))}]
                    return resp.json()
        except Exception as e:
            logger.error("Failed to fetch contributors: %s", e)
        return []

    @staticmethod
    def _compute_metrics(
        repo_data: dict,
        readme_content: str,
        file_tree: list[str],
        recent_commits: list[dict],
        workflows: list[dict],
        contributors: list[dict],
    ) -> list[MetricScore]:
        """Compute all quality metric scores."""
        return [
            RepositoryQualityService._score_readme(readme_content),
            RepositoryQualityService._score_documentation(file_tree),
            RepositoryQualityService._score_license(file_tree),
            RepositoryQualityService._score_test_coverage(file_tree),
            RepositoryQualityService._score_ci_cd(workflows, file_tree),
            RepositoryQualityService._score_recent_activity(recent_commits),
            RepositoryQualityService._score_open_issues(
                repo_data.get("open_issues_count", 0),
                repo_data.get("stargazers_count", 1),
            ),
        ]

    @staticmethod
    def _score_readme(readme_content: str) -> MetricScore:
        """Score README quality based on length, sections, and formatting."""
        weight = METRIC_WEIGHTS[QualityMetric.README]
        if not readme_content:
            return MetricScore(
                metric=QualityMetric.README,
                score=0.0,
                label="README",
                description="No README found.",
                weight=weight,
            )

        score = 0.0
        reasons = []

        length = len(readme_content)
        if length > 3000:
            score += 0.3
            reasons.append("comprehensive length")
        elif length > 1000:
            score += 0.2
            reasons.append("adequate length")
        elif length > 200:
            score += 0.1
            reasons.append("short but present")
        else:
            reasons.append("very short README")

        headings = re.findall(r"^#{1,3}\s+.+", readme_content, re.MULTILINE)
        if len(headings) >= 5:
            score += 0.3
            reasons.append("well-structured with sections")
        elif len(headings) >= 2:
            score += 0.2
            reasons.append("has some sections")
        elif headings:
            score += 0.1
            reasons.append("minimal sections")

        if re.search(r"```[\s\S]*?```", readme_content):
            score += 0.15
            reasons.append("includes code examples")

        if re.search(r"!\[.*\]\(.*\)", readme_content):
            score += 0.1
            reasons.append("includes images/badges")

        has_badges = bool(re.search(r"shields\.io|img\.shields|badge", readme_content))
        if has_badges:
            score += 0.05
            reasons.append("has badges")

        has_install = bool(
            re.search(
                r"(installation|install|setup|getting started)", readme_content, re.I
            )
        )
        if has_install:
            score += 0.1
            reasons.append("includes installation instructions")

        score = min(1.0, score)

        return MetricScore(
            metric=QualityMetric.README,
            score=round(score, 2),
            label="README",
            description=f"README quality: {', '.join(reasons) if reasons else 'minimal'}.",
            weight=weight,
        )

    @staticmethod
    def _score_documentation(file_tree: list[str]) -> MetricScore:
        """Score documentation presence."""
        weight = METRIC_WEIGHTS[QualityMetric.DOCUMENTATION]
        doc_indicators = {"docs", "documentation", "wiki", "guide", "guides"}
        file_lower = {f.lower() for f in file_tree}

        has_docs_dir = bool(doc_indicators & file_lower)
        has_readme = any(f.lower() in ("readme.md", "readme") for f in file_tree)
        has_changelog = any(
            f.lower() in ("changelog.md", "changelog", "changes.md", "history.md")
            for f in file_tree
        )
        has_contributing = any(
            f.lower() in ("contributing.md", "contributing", "contribute.md")
            for f in file_tree
        )

        score = 0.0
        reasons = []

        if has_docs_dir:
            score += 0.4
            reasons.append("dedicated docs directory")
        if has_readme:
            score += 0.2
            reasons.append("README present")
        if has_changelog:
            score += 0.2
            reasons.append("changelog present")
        if has_contributing:
            score += 0.2
            reasons.append("contributing guide present")

        score = min(1.0, score)

        return MetricScore(
            metric=QualityMetric.DOCUMENTATION,
            score=round(score, 2),
            label="Documentation",
            description=f"Documentation: {', '.join(reasons) if reasons else 'no documentation found'}.",
            weight=weight,
        )

    @staticmethod
    def _score_license(file_tree: list[str]) -> MetricScore:
        """Score license presence."""
        weight = METRIC_WEIGHTS[QualityMetric.LICENSE]
        file_lower = {f.lower() for f in file_tree}
        has_license = any(
            f in ("license", "license.md", "license.txt", "license.mit")
            for f in file_lower
        )

        score = 1.0 if has_license else 0.0

        return MetricScore(
            metric=QualityMetric.LICENSE,
            score=score,
            label="License",
            description=(
                "License file is present." if has_license else "No license file found."
            ),
            weight=weight,
        )

    @staticmethod
    def _score_test_coverage(file_tree: list[str]) -> MetricScore:
        """Score test presence based on file tree indicators."""
        weight = METRIC_WEIGHTS[QualityMetric.TEST_COVERAGE]
        file_lower = {f.lower() for f in file_tree}

        test_dirs = {"test", "tests", "__tests__", "spec", "specs", "test suite"}
        has_test_dir = bool(test_dirs & file_lower)

        has_test_files = any(
            f.endswith(
                (
                    ".test.js",
                    ".test.ts",
                    ".spec.js",
                    ".spec.ts",
                    "_test.go",
                    "test_*.py",
                )
            )
            for f in file_tree
        )

        has_coverage_config = any(
            f
            in (
                ".nycrc",
                ".nycrc.json",
                "jest.config.js",
                "jest.config.ts",
                "vitest.config.ts",
                ".coveragerc",
            )
            for f in file_lower
        )

        score = 0.0
        reasons = []

        if has_test_dir:
            score += 0.4
            reasons.append("dedicated test directory")
        if has_test_files:
            score += 0.3
            reasons.append("test files present at root")
        if has_coverage_config:
            score += 0.3
            reasons.append("coverage configuration found")

        score = min(1.0, score)

        return MetricScore(
            metric=QualityMetric.TEST_COVERAGE,
            score=round(score, 2),
            label="Test Coverage",
            description=f"Tests: {', '.join(reasons) if reasons else 'no tests detected'}.",
            weight=weight,
        )

    @staticmethod
    def _score_ci_cd(workflows: list[dict], file_tree: list[str]) -> MetricScore:
        """Score CI/CD setup based on GitHub Actions and config files."""
        weight = METRIC_WEIGHTS[QualityMetric.CI_CD]
        file_lower = {f.lower() for f in file_tree}

        has_workflows = len(workflows) > 0
        has_github_actions = ".github" in file_lower
        has_ci_configs = any(
            f
            in (
                ".travis.yml",
                ".circleci",
                "jenkinsfile",
                "gitlab-ci.yml",
                "azure-pipelines.yml",
            )
            for f in file_lower
        )

        score = 0.0
        reasons = []

        if has_workflows:
            score += 0.6
            reasons.append(f"{len(workflows)} workflow(s) configured")
        elif has_github_actions:
            score += 0.3
            reasons.append("GitHub Actions directory present")
        if has_ci_configs:
            score += 0.4
            reasons.append("CI config files found")

        score = min(1.0, score)

        return MetricScore(
            metric=QualityMetric.CI_CD,
            score=round(score, 2),
            label="CI/CD",
            description=f"CI/CD: {', '.join(reasons) if reasons else 'no CI/CD detected'}.",
            weight=weight,
        )

    @staticmethod
    def _score_recent_activity(recent_commits: list[dict]) -> MetricScore:
        """Score recent activity based on commit recency."""
        weight = METRIC_WEIGHTS[QualityMetric.RECENT_ACTIVITY]

        if not recent_commits:
            return MetricScore(
                metric=QualityMetric.RECENT_ACTIVITY,
                score=0.1,
                label="Recent Activity",
                description="No recent commits found.",
                weight=weight,
            )

        now = datetime.now(timezone.utc)
        days_ago = []

        for commit in recent_commits[:5]:
            date_str = commit.get("commit", {}).get("author", {}).get("date")
            if date_str:
                try:
                    commit_date = datetime.fromisoformat(
                        date_str.replace("Z", "+00:00")
                    )
                    days = (now - commit_date).days
                    days_ago.append(days)
                except (ValueError, TypeError):
                    pass

        if not days_ago:
            return MetricScore(
                metric=QualityMetric.RECENT_ACTIVITY,
                score=0.1,
                label="Recent Activity",
                description="Could not parse commit dates.",
                weight=weight,
            )

        avg_days = sum(days_ago) / len(days_ago)

        if avg_days <= 7:
            score = 1.0
            desc = "very active (daily commits)"
        elif avg_days <= 30:
            score = 0.8
            desc = "active (weekly commits)"
        elif avg_days <= 90:
            score = 0.5
            desc = "moderate activity"
        elif avg_days <= 365:
            score = 0.3
            desc = "low activity"
        else:
            score = 0.1
            desc = "inactive for over a year"

        return MetricScore(
            metric=QualityMetric.RECENT_ACTIVITY,
            score=score,
            label="Recent Activity",
            description=f"Activity: {desc} (avg {avg_days:.0f} days since last commits).",
            weight=weight,
        )

    @staticmethod
    def _score_open_issues(open_issues: int, stars: int) -> MetricScore:
        """Score issue management based on open issue ratio."""
        weight = METRIC_WEIGHTS[QualityMetric.OPEN_ISSUES]

        if stars == 0:
            stars = 1

        ratio = open_issues / stars

        if ratio <= 0.05:
            score = 1.0
            desc = "excellent issue management"
        elif ratio <= 0.1:
            score = 0.8
            desc = "good issue management"
        elif ratio <= 0.2:
            score = 0.5
            desc = "moderate issue backlog"
        elif ratio <= 0.5:
            score = 0.3
            desc = "large issue backlog"
        else:
            score = 0.1
            desc = "very large issue backlog"

        return MetricScore(
            metric=QualityMetric.OPEN_ISSUES,
            score=score,
            label="Open Issues",
            description=f"Issues: {desc} ({open_issues} open, ratio {ratio:.2f}).",
            weight=weight,
        )

    @staticmethod
    def _score_to_grade(score: float) -> str:
        """Convert a 0-1 score to a letter grade."""
        percentage = score * 100
        if percentage >= 90:
            return "A"
        elif percentage >= 70:
            return "B"
        elif percentage >= 50:
            return "C"
        elif percentage >= 30:
            return "D"
        return "F"

    @staticmethod
    def _generate_suggestions(
        metrics: list[MetricScore],
        repo_info: RepositoryInfo,
        readme_content: str,
        file_tree: list[str],
    ) -> list[ImprovementSuggestion]:
        """Generate improvement suggestions based on low-scoring metrics."""
        suggestions = []

        for metric in metrics:
            if metric.score >= 0.7:
                continue

            if metric.metric == QualityMetric.README:
                if metric.score < 0.3:
                    suggestions.append(
                        ImprovementSuggestion(
                            priority="high",
                            category=QualityMetric.README,
                            title="Add a comprehensive README",
                            description=(
                                "Create a detailed README with project overview, "
                                "installation instructions, usage examples, and "
                                "contribution guidelines."
                            ),
                        )
                    )
                elif metric.score < 0.7:
                    suggestions.append(
                        ImprovementSuggestion(
                            priority="medium",
                            category=QualityMetric.README,
                            title="Improve README structure",
                            description=(
                                "Add more sections (installation, usage, API docs), "
                                "code examples, and badges to the README."
                            ),
                        )
                    )

            elif metric.metric == QualityMetric.DOCUMENTATION:
                suggestions.append(
                    ImprovementSuggestion(
                        priority="medium",
                        category=QualityMetric.DOCUMENTATION,
                        title="Add documentation",
                        description=(
                            "Create a docs/ directory with detailed guides, "
                            "API documentation, and a changelog."
                        ),
                    )
                )

            elif metric.metric == QualityMetric.LICENSE:
                suggestions.append(
                    ImprovementSuggestion(
                        priority="high",
                        category=QualityMetric.LICENSE,
                        title="Add a license file",
                        description=(
                            "Add a LICENSE or LICENSE.md file to clarify "
                            "usage rights. Common choices: MIT, Apache 2.0, GPL."
                        ),
                    )
                )

            elif metric.metric == QualityMetric.TEST_COVERAGE:
                suggestions.append(
                    ImprovementSuggestion(
                        priority="high",
                        category=QualityMetric.TEST_COVERAGE,
                        title="Add tests",
                        description=(
                            "Create a test suite with unit and integration tests. "
                            "Set up coverage reporting with tools like Jest, Vitest, "
                            "or pytest-cov."
                        ),
                    )
                )

            elif metric.metric == QualityMetric.CI_CD:
                suggestions.append(
                    ImprovementSuggestion(
                        priority="medium",
                        category=QualityMetric.CI_CD,
                        title="Set up CI/CD pipeline",
                        description=(
                            "Configure GitHub Actions for automated testing, "
                            "linting, and deployment on every push and PR."
                        ),
                    )
                )

            elif metric.metric == QualityMetric.RECENT_ACTIVITY:
                suggestions.append(
                    ImprovementSuggestion(
                        priority="medium",
                        category=QualityMetric.RECENT_ACTIVITY,
                        title="Increase activity",
                        description=(
                            "The repository appears inactive. Consider merging "
                            "open PRs, addressing issues, or adding new features "
                            "to show the project is maintained."
                        ),
                    )
                )

            elif metric.metric == QualityMetric.OPEN_ISSUES:
                suggestions.append(
                    ImprovementSuggestion(
                        priority="low",
                        category=QualityMetric.OPEN_ISSUES,
                        title="Address open issues",
                        description=(
                            f"There are {repo_info.open_issues} open issues. "
                            "Consider triaging, closing stale issues, or "
                            "prioritizing critical fixes."
                        ),
                    )
                )

        return suggestions

    @staticmethod
    def _generate_summary(
        repository_url: str,
        repo_info: RepositoryInfo,
        metrics: list[MetricScore],
        overall_score: float,
        grade: str,
    ) -> str:
        """Generate an AI-powered summary using OpenAI."""
        if not settings.OPENAI_API_KEY:
            return RepositoryQualityService._fallback_summary(
                repo_info, metrics, overall_score, grade
            )

        try:
            client = OpenAI(api_key=settings.OPENAI_API_KEY)

            metrics_text = "\n".join(
                f"- {m.label}: {m.score:.0%} — {m.description}" for m in metrics
            )

            prompt = (
                f"Analyze the quality of this GitHub repository and provide a "
                f"brief 2-3 sentence summary.\n\n"
                f"Repository: {repository_url}\n"
                f"Stars: {repo_info.stars}, Forks: {repo_info.forks}, "
                f"Language: {repo_info.language or 'N/A'}\n"
                f"Overall Score: {overall_score:.0%} (Grade: {grade})\n\n"
                f"Metrics:\n{metrics_text}\n\n"
                f"Write a concise, professional summary highlighting strengths "
                f"and areas for improvement."
            )

            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {
                        "role": "system",
                        "content": (
                            "You are a repository quality analyst. "
                            "Provide concise, actionable summaries."
                        ),
                    },
                    {"role": "user", "content": prompt},
                ],
                max_tokens=300,
                temperature=0.3,
            )

            return response.choices[0].message.content.strip()

        except Exception as e:
            logger.error("OpenAI summary generation failed: %s", e)
            return RepositoryQualityService._fallback_summary(
                repo_info, metrics, overall_score, grade
            )

    @staticmethod
    def _fallback_summary(
        repo_info: RepositoryInfo,
        metrics: list[MetricScore],
        overall_score: float,
        grade: str,
    ) -> str:
        """Generate a simple summary without AI."""
        weak_areas = [m.label for m in metrics if m.score < 0.5]
        strong_areas = [m.label for m in metrics if m.score >= 0.7]

        parts = [
            f"This repository has an overall quality score of {overall_score:.0%} (Grade: {grade})."
        ]

        if strong_areas:
            parts.append(f"Strengths include {', '.join(strong_areas)}.")
        if weak_areas:
            parts.append(f"Areas for improvement: {', '.join(weak_areas)}.")

        return " ".join(parts)
