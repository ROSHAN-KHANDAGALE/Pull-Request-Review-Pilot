import re
import httpx
from fastapi import HTTPException
from app.config import settings

class GitHubService:
    def __init__(self):
        """ 
        GitHub requires specific headers to return the raw diff format
        """

        headers = {
            "Authorization": f"Bearer {settings.github_token}",
            "Accept": "application/vnd.github.v3.diff",
            "X-GitHub-Api-Version": "2022-11-28",
        }
        self.client = httpx.AsyncClient(headers=headers, timeout=30.0)

    def parse_pr_url(self, pr_url: str) -> tuple[str, str, int]:
        """
        Parses owner, repo, and pr_number from a GitHub pull request URL.
        Expected format: https://github.com/owner/repo/pull/123
        """

        pattern = r"https://github\.com/([^/]+)/([^/]+)/pull/(\d+)"
        match = re.match(pattern, pr_url)
        
        if not match:
            raise ValueError(f"Invalid GitHub PR URL format: {pr_url}")
            
        owner, repo, pr_number = match.groups()
        return owner, repo, int(pr_number)

    async def fetch_diff(self, pr_url: str) -> str:
        """
        Fetches the raw diff of a pull request from GitHub.
        """

        owner, repo, pr_number = self.parse_pr_url(pr_url)
        url = f"https://api.github.com/repos/{owner}/{repo}/pulls/{pr_number}"

        try:
            response = await self.client.get(url)
        except httpx.RequestError as exc:
            raise HTTPException(status_code=502, detail=f"Could not connect to GitHub: {str(exc)}")

        if response.status_code != 200:
            raise HTTPException(status_code=502, detail=f"GitHub API error: {response.status_code} - {response.text}")

        return response.text

    async def close(self):
        """
        Closes the underlying HTTPX client.
        """
        
        await self.client.aclose()