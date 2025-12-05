"""
NewsAPI Fetcher - Breaking News and Headlines
Production-grade news aggregation
"""

from .base_fetcher import BaseFetcher, FetchResult, FetchStatus

class NewsAPIFetcher(BaseFetcher):
    """
    Fetches news headlines from NewsAPI
    Excellent for: breaking news, headlines, news search
    """

    def _setup(self):
        self.base_url = "https://newsapi.org/v2"
        # Note: NewsAPI requires API key for most features
        # Set NEWSAPI_KEY in .env for production use

    def fetch(self, query: str) -> FetchResult:
        """Search for news articles"""
        try:
            # NewsAPI requires API key
            return FetchResult(
                status=FetchStatus.API_KEY_REQUIRED,
                data={},
                summary="NewsAPI requires an API key. Set NEWSAPI_KEY in .env file. Get one free at https://newsapi.org",
                confidence=0.0,
                source="newsapi"
            )

        except Exception as e:
            return FetchResult(
                status=FetchStatus.ERROR,
                data={},
                error=str(e),
                confidence=0.0
            )
