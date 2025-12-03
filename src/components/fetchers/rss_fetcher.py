import feedparser
from typing import List, Dict, Any
from .base_fetcher import BaseFetcher


class RSSFetcher(BaseFetcher):
    """
    RSS / news fetcher scanning curated feeds for query matches.
    """

    def __init__(self, feeds: List[str] = None):
        self.feeds = feeds or []

    def fetch(self, query: str) -> Dict[str, Any]:
        q = query.lower().strip()
        results: List[Dict[str, Any]] = []
        for feed_url in self.feeds:
            try:
                feed = feedparser.parse(feed_url)
                for entry in getattr(feed, "entries", []):
                    title = getattr(entry, "title", "") or ""
                    summary = getattr(entry, "summary", "") or ""
                    if q in title.lower() or q in summary.lower():
                        results.append(
                            {
                                "title": title,
                                "link": getattr(entry, "link", None),
                                "published": getattr(entry, "published", None),
                            }
                        )
            except Exception:
                continue

        if results:
            return {
                "status": "FOUND",
                "data": results,
                "confidence": 0.8,
            }
        return {
            "status": "NOT_FOUND",
            "data": [],
            "confidence": 0.0,
        }
