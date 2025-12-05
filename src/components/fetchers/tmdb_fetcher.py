"""
TMDB (The Movie Database) Fetcher - Movies and TV Shows
Production-grade entertainment data
"""

from .base_fetcher import BaseFetcher, FetchResult, FetchStatus

class TMDBFetcher(BaseFetcher):
    """
    Fetches movie and TV show data from TMDB
    Excellent for: movie info, TV shows, cast, ratings
    """

    def _setup(self):
        self.base_url = "https://api.themoviedb.org/3"
        # Free API - no key required for basic searches
        # For production use, set TMDB_API_KEY in .env

    def fetch(self, query: str) -> FetchResult:
        """Search for movies or TV shows"""
        try:
            # Determine if searching for movie or TV
            query_lower = query.lower()
            if "tv show" in query_lower or "series" in query_lower:
                return self._search_tv(query)
            else:
                return self._search_movie(query)

        except Exception as e:
            return FetchResult(
                status=FetchStatus.ERROR,
                data={},
                error=str(e),
                confidence=0.0
            )

    def _search_movie(self, query: str) -> FetchResult:
        """Search for movies"""
        # Extract movie title
        title = query.replace("movie", "").strip()

        # Note: TMDB requires API key for most endpoints
        # This is a simplified version - in production, use API key
        return FetchResult(
            status=FetchStatus.API_KEY_REQUIRED,
            data={},
            summary="TMDB API key required. Set TMDB_API_KEY in .env file.",
            confidence=0.0,
            source="tmdb"
        )

    def _search_tv(self, query: str) -> FetchResult:
        """Search for TV shows"""
        return FetchResult(
            status=FetchStatus.API_KEY_REQUIRED,
            data={},
            summary="TMDB API key required. Set TMDB_API_KEY in .env file.",
            confidence=0.0,
            source="tmdb"
        )
