"""
GitHub Fetcher - Development and Repository Information
Production-grade GitHub API integration
"""

from .base_fetcher import BaseFetcher, FetchResult, FetchStatus

class GithubFetcher(BaseFetcher):
    """
    Fetches information from GitHub API
    Excellent for: repositories, developers, trending projects
    """

    def _setup(self):
        self.api_base = "https://api.github.com"

    def fetch(self, query: str) -> FetchResult:
        """Search GitHub for repositories or users"""
        try:
            query_lower = query.lower()

            # Determine if searching for repo or user
            if "repository" in query_lower or "repo" in query_lower:
                return self._search_repos(query)
            elif "user" in query_lower or "developer" in query_lower:
                return self._search_users(query)
            else:
                # Default to repo search
                return self._search_repos(query)

        except Exception as e:
            return FetchResult(
                status=FetchStatus.ERROR,
                data={},
                error=str(e),
                confidence=0.0
            )

    def _search_repos(self, query: str) -> FetchResult:
        """Search for repositories"""
        # Extract search terms
        search_terms = query.replace("repository", "").replace("repo", "").strip()

        url = f"{self.api_base}/search/repositories"
        params = {
            'q': search_terms,
            'sort': 'stars',
            'order': 'desc',
            'per_page': 1
        }

        data = self._make_request(url, params=params)
        if not data or not data.get('items'):
            return FetchResult(
                status=FetchStatus.NOT_FOUND,
                data={},
                confidence=0.0
            )

        repo = data['items'][0]
        return FetchResult(
            status=FetchStatus.FOUND,
            data={
                "name": repo['full_name'],
                "description": repo.get('description', ''),
                "stars": repo['stargazers_count'],
                "language": repo.get('language', 'Unknown'),
                "url": repo['html_url']
            },
            summary=f"{repo['full_name']}: {repo.get('description', 'No description')} ({repo['stargazers_count']} stars)",
            confidence=0.80,
            source="github",
            url=repo['html_url']
        )

    def _search_users(self, query: str) -> FetchResult:
        """Search for users"""
        search_terms = query.replace("user", "").replace("developer", "").strip()

        url = f"{self.api_base}/search/users"
        params = {
            'q': search_terms,
            'sort': 'followers',
            'order': 'desc',
            'per_page': 1
        }

        data = self._make_request(url, params=params)
        if not data or not data.get('items'):
            return FetchResult(
                status=FetchStatus.NOT_FOUND,
                data={},
                confidence=0.0
            )

        user = data['items'][0]
        return FetchResult(
            status=FetchStatus.FOUND,
            data={
                "username": user['login'],
                "profile_url": user['html_url'],
                "type": user['type']
            },
            summary=f"GitHub user: {user['login']}",
            confidence=0.75,
            source="github",
            url=user['html_url']
        )
