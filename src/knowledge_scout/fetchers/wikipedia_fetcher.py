import requests
from .base import BaseFetcher, FetchResult, FetchSource


class WikipediaFetcher(BaseFetcher):
    """
    Fetch summaries from Wikipedia using the MediaWiki search API.
    More robust than guessing a page URL directly.
    """

    def __init__(self, language="en"):
        self.language = language
        self.api_url = "https://{}.wikipedia.org/w/api.php".format(language)

    def _search_title(self, query):
        params = {
            "action": "query",
            "list": "search",
            "srsearch": query,
            "format": "json",
        }
        try:
            resp = requests.get(self.api_url, params=params, timeout=10)
        except Exception:
            return None
        if resp.status_code != 200:
            return None
        try:
            data = resp.json()
        except Exception:
            return None
        search = data.get("query", {}).get("search", [])
        if not search:
            return None
        return search[0].get("title")

    def _get_extract(self, title):
        params = {
            "action": "query",
            "prop": "extracts",
            "explaintext": 1,
            "exintro": 1,
            "titles": title,
            "format": "json",
        }
        try:
            resp = requests.get(self.api_url, params=params, timeout=10)
        except Exception:
            return None
        if resp.status_code != 200:
            return None
        try:
            data = resp.json()
        except Exception:
            return None
        pages = data.get("query", {}).get("pages", {})
        if not pages:
            return None
        page = list(pages.values())[0]
        extract = page.get("extract", "")
        if not extract:
            return None
        return extract

    def _canonical_fallback_title(self, query_lower):
        """
        Heuristic fallback for high-value concepts when search fails.
        """
        # US president: try canonical page
        if "president of the united states" in query_lower:
            return "President of the United States"
        return None

    def fetch(self, query: str):
        print("    [Wikipedia] Searching for: '{}'".format(query))
        query_lower = query.lower()

        # First try direct search on the raw query
        title = self._search_title(query)

        # If that fails, try a canonical fallback for known patterns
        if not title:
            fallback = self._canonical_fallback_title(query_lower)
            if fallback:
                print("    [Wikipedia] Using canonical fallback title: '{}'".format(fallback))
                title = fallback

        if not title:
            print("    [Wikipedia] ✗ No search results")
            return None

        extract = self._get_extract(title)
        if not extract:
            print("    [Wikipedia] ✗ No extract for '{}'".format(title))
            return None

        url_title = title.replace(" ", "_")
        url = "https://{}.wikipedia.org/wiki/{}".format(self.language, url_title)

        print("    [Wikipedia] ✓ Found page: '{}'".format(title))

        base_conf = 0.75
        if len(extract) < 200:
            base_conf -= 0.1
        if query_lower in title.lower():
            base_conf += 0.05
        confidence = max(0.5, min(0.9, base_conf))

        return FetchResult(
            query=query,
            summary=extract,
            source=FetchSource.WIKIPEDIA,
            confidence=confidence,
            url=url,
        )
