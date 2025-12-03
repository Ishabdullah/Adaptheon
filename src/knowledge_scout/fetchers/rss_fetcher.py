import feedparser
from typing import Optional
from .base import BaseFetcher, FetchResult, FetchSource

class RSSFetcher(BaseFetcher):
    """
    Fetches fresh news-style information from curated RSS feeds.
    Good for: current events, crypto/market context, tech/science stories.
    """

    def __init__(self):
        # Three example feeds (tech, science/tech, crypto/markets)
        self.feeds = [
            # Tech / general computing news (Ars Technica)
            "https://feeds.arstechnica.com/arstechnica/index",
            # Science & technology headlines (ScienceDaily top tech)
            "https://www.sciencedaily.com/rss/top/technology.xml",
            # Cryptocurrency / blockchain news (one curated crypto feed)
            "https://newsbtc.com/feed",
        ]

    def fetch(self, query: str) -> Optional[FetchResult]:
        query_lower = query.lower()
        print("    [RSS] Scanning {} feeds...".format(len(self.feeds)))

        best_entry = None
        best_score = 0.0
        best_feed_url = None

        for feed_url in self.feeds:
            try:
                parsed = feedparser.parse(feed_url)
                if parsed.bozo:
                    continue

                for entry in parsed.entries[:15]:
                    title = getattr(entry, "title", "") or ""
                    summary = getattr(entry, "summary", "") or ""
                    text = (title + " " + summary).lower()

                    # Simple keyword match scoring
                    score = 0.0
                    for token in query_lower.split():
                        if token in text:
                            score += 1.0

                    if score > best_score and len(summary) > 40:
                        best_score = score
                        best_entry = entry
                        best_feed_url = feed_url

            except Exception as e:
                print("    [RSS] Error reading feed {}: {}".format(feed_url, e))
                continue

        if not best_entry or best_score == 0.0:
            print("    [RSS] ✗ No relevant articles found")
            return None

        title = getattr(best_entry, "title", "").strip()
        summary = getattr(best_entry, "summary", "").strip()
        link = getattr(best_entry, "link", None)

        print("    [RSS] ✓ Found: '{}'".format(title))
        # Confidence is light: it depends on keyword overlap only
        confidence = min(0.75, 0.35 + 0.05 * best_score)

        return FetchResult(
            query=query,
            summary=title + ": " + summary,
            source=FetchSource.LOCAL_RSS,
            confidence=confidence,
            url=link or best_feed_url,
        )
