import os
import requests
from typing import Dict, Any, Optional, List


class MediaFetcher:
    """
    Movies / TV / anime domain fetcher.
    Uses TMDB when TMDB_API_KEY is set, otherwise falls back to TVMaze.
    """

    def __init__(self):
        self.tmdb_key = os.environ.get("TMDB_API_KEY")
        self.tmdb_base = "https://api.themoviedb.org/3"
        self.tvmaze_base = "https://api.tvmaze.com"

    # --- TMDB helpers ---

    def _tmdb_search_multi(self, query: str, limit: int = 3) -> Optional[List[Dict[str, Any]]]:
        if not self.tmdb_key:
            return None
        url = self.tmdb_base + "/search/multi"
        params = {
            "api_key": self.tmdb_key,
            "query": query,
            "include_adult": "false",
            "language": "en-US",
            "page": 1,
        }
        try:
            resp = requests.get(url, params=params, timeout=10)
        except Exception:
            return None
        if resp.status_code != 200:
            return None
        try:
            data = resp.json()
        except Exception:
            return None
        results = data.get("results") or []
        return results[:limit]

    def _format_tmdb_result(self, items: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
        if not items:
            return None
        it = items[0]
        media_type = it.get("media_type")
        title = it.get("title") or it.get("name") or ""
        overview = it.get("overview") or ""
        year = None
        date_str = it.get("release_date") or it.get("first_air_date")
        if date_str and len(date_str) >= 4:
            try:
                year = int(date_str[:4])
            except Exception:
                year = None
        vote = it.get("vote_average")
        vote_part = ""
        if vote is not None:
            vote_part = f" TMDB user rating: {vote:.1f}/10."
        year_part = f" ({year})" if year else ""
        summary = f"{title}{year_part}. {overview}{vote_part}"
        url = None
        tmdb_id = it.get("id")
        if tmdb_id and media_type in ("movie", "tv"):
            url = f"https://www.themoviedb.org/{media_type}/{tmdb_id}"
        return {
            "status": "FOUND",
            "summary": summary,
            "confidence": 0.9,
            "url": url,
            "metadata": {
                "source": "tmdb",
                "media_type": media_type,
                "tmdb_id": tmdb_id,
                "year": year,
            },
        }

    # --- TVMaze helpers (no key required) ---

    def _tvmaze_search_shows(self, query: str, limit: int = 3) -> Optional[List[Dict[str, Any]]]:
        url = self.tvmaze_base + "/search/shows"
        params = {"q": query}
        try:
            resp = requests.get(url, params=params, timeout=10)
        except Exception:
            return None
        if resp.status_code != 200:
            return None
        try:
            data = resp.json()
        except Exception:
            return None
        return data[:limit]

    def _format_tvmaze_result(self, items: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
        if not items:
            return None
        it = items[0]
        show = it.get("show") or {}
        name = show.get("name") or ""
        summary_html = show.get("summary") or ""
        # Strip basic HTML tags from summary
        summary_txt = (
            summary_html.replace("<p>", " ")
            .replace("</p>", " ")
            .replace("<b>", "")
            .replace("</b>", "")
            .replace("<i>", "")
            .replace("</i>", "")
        ).strip()
        premiered = show.get("premiered")
        year = None
        if premiered and len(premiered) >= 4:
            try:
                year = int(premiered[:4])
            except Exception:
                year = None
        genres = show.get("genres") or []
        genre_part = ""
        if genres:
            genre_part = " Genres: " + ", ".join(genres) + "."
        year_part = f" ({year})" if year else ""
        summary = f"{name}{year_part}. {summary_txt}{genre_part}"
        url = show.get("url")
        return {
            "status": "FOUND",
            "summary": summary,
            "confidence": 0.8,
            "url": url,
            "metadata": {
                "source": "tvmaze",
                "tvmaze_id": show.get("id"),
                "year": year,
            },
        }

    def fetch(self, query: str) -> Dict[str, Any]:
        """
        High-level media fetch.
        Prefers TMDB when API key is present; falls back to TVMaze otherwise.
        """
        # Try TMDB first if configured
        items = self._tmdb_search_multi(query, limit=3)
        formatted = self._format_tmdb_result(items or [])
        if formatted:
            return formatted

        # Fallback: TVMaze shows
        tv_items = self._tvmaze_search_shows(query, limit=3)
        formatted_tv = self._format_tvmaze_result(tv_items or [])
        if formatted_tv:
            return formatted_tv

        return {
            "status": "NOT_FOUND",
            "summary": "",
            "confidence": 0.0,
            "url": None,
            "metadata": {},
        }
