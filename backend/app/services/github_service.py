import httpx
from bs4 import BeautifulSoup
from collections import defaultdict
from app.core.config import settings
from fastapi import HTTPException


class GitHubService:
    BASE_URL = "https://api.github.com"

    @classmethod
    def _get_headers(cls):
        headers = {"Accept": "application/vnd.github.v3+json"}
        if settings.GITHUB_API_TOKEN:
            headers["Authorization"] = f"token {settings.GITHUB_API_TOKEN}"
        return headers

    @classmethod
    async def get_profile(cls, username: str):
        async with httpx.AsyncClient() as client:
            resp = await client.get(
                f"{cls.BASE_URL}/users/{username}", headers=cls._get_headers()
            )
            if resp.status_code == 404:
                raise HTTPException(status_code=404, detail="GitHub user not found")
            resp.raise_for_status()
            data = resp.json()
            return {
                "username": data.get("login"),
                "avatar_url": data.get("avatar_url"),
                "name": data.get("name"),
                "followers": data.get("followers", 0),
                "following": data.get("following", 0),
                "public_repos": data.get("public_repos", 0),
            }

    @classmethod
    async def get_repositories(cls, username: str):
        async with httpx.AsyncClient() as client:
            resp = await client.get(
                f"{cls.BASE_URL}/users/{username}/repos?sort=updated&per_page=100",
                headers=cls._get_headers(),
            )
            if resp.status_code == 404:
                return []
            resp.raise_for_status()
            repos = resp.json()

            result = []
            for r in repos:
                result.append(
                    {
                        "id": r.get("id"),
                        "name": r.get("name"),
                        "description": r.get("description"),
                        "language": r.get("language"),
                        "stargazers_count": r.get("stargazers_count", 0),
                        "forks_count": r.get("forks_count", 0),
                        "updated_at": r.get("updated_at"),
                        "html_url": r.get("html_url"),
                    }
                )
            return result

    @classmethod
    async def get_stats(cls, username: str):
        async with httpx.AsyncClient() as client:
            headers = cls._get_headers()

            # 1. Get total PRs
            prs_resp = await client.get(
                f"{cls.BASE_URL}/search/issues?q=author:{username}+type:pr",
                headers=headers,
            )
            prs_count = (
                prs_resp.json().get("total_count", 0)
                if prs_resp.status_code == 200
                else 0
            )

            # 2. Get total Issues
            issues_resp = await client.get(
                f"{cls.BASE_URL}/search/issues?q=author:{username}+type:issue",
                headers=headers,
            )
            issues_count = (
                issues_resp.json().get("total_count", 0)
                if issues_resp.status_code == 200
                else 0
            )

            # 3. Get Repos for stars and languages
            repos_resp = await client.get(
                f"{cls.BASE_URL}/users/{username}/repos?per_page=100", headers=headers
            )
            repos = repos_resp.json() if repos_resp.status_code == 200 else []

            stars = sum((r.get("stargazers_count", 0) for r in repos))

            language_counts = defaultdict(int)
            for r in repos:
                lang = r.get("language")
                if lang:
                    language_counts[lang] += 1

            total_langs = sum(language_counts.values())
            languages = []
            if total_langs > 0:
                for lang, count in sorted(
                    language_counts.items(), key=lambda x: x[1], reverse=True
                )[:5]:
                    languages.append(
                        {
                            "name": lang,
                            "percentage": round((count / total_langs) * 100, 1),
                            "count": count,
                        }
                    )

            # Get followers from profile
            profile_resp = await client.get(
                f"{cls.BASE_URL}/users/{username}", headers=headers
            )
            followers = (
                profile_resp.json().get("followers", 0)
                if profile_resp.status_code == 200
                else 0
            )

            return {
                "total_prs": prs_count,
                "total_issues": issues_count,
                "total_stars": stars,
                "followers": followers,
                "languages": languages,
            }

    @classmethod
    async def get_contributions(cls, username: str):
        # Fallback to parsing GitHub's public contribution graph HTML
        # because the API doesn't expose it easily without GraphQL + Token
        async with httpx.AsyncClient() as client:
            resp = await client.get(
                f"https://github.com/users/{username}/contributions"
            )
            if resp.status_code != 200:
                return []

            try:
                soup = BeautifulSoup(resp.text, "html.parser")
                days = soup.find_all("td", {"class": "ContributionCalendar-day"})

                contributions = []
                for day in days:
                    date = day.get("data-date")
                    level = day.get("data-level")  # 0 to 4
                    if date and level is not None:
                        # Extract count from tooltip ID if possible, else we estimate based on level
                        count = 0
                        if level == "0":
                            count = 0
                        elif level == "1":
                            count = 1
                        elif level == "2":
                            count = 5
                        elif level == "3":
                            count = 10
                        elif level == "4":
                            count = 20

                        # More accurate count if the id exists
                        tool_id = day.get("id")
                        if tool_id:
                            tooltip = soup.find("tool-tip", {"for": tool_id})
                            if tooltip:
                                text = tooltip.text.strip()
                                if text.startswith("No contributions"):
                                    count = 0
                                else:
                                    try:
                                        count = int(text.split(" ")[0].replace(",", ""))
                                    except:
                                        pass

                        contributions.append(
                            {"date": date, "count": count, "level": int(level)}
                        )
                return contributions
            except Exception as e:
                print(f"Failed to scrape github contributions: {e}")
                return []
