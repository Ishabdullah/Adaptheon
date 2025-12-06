"""
NewsAPI Fetcher - Breaking News and Headlines
Uses free RSS feeds from Reuters, AP, and Google News
"""

import feedparser
import logging
from datetime import datetime, timedelta
from .base_fetcher import BaseFetcher, FetchResult, FetchStatus

logger = logging.getLogger('Adaptheon.NewsAPIFetcher')


class NewsAPIFetcher(BaseFetcher):
    """
    Fetches latest breaking news from multiple RSS sources.
    No API key required - uses free RSS feeds.

    Sources (in priority order):
    1. Reuters World News RSS
    2. AP News Top Stories RSS
    3. Google News RSS
    """

    def _setup(self):
        # RSS feed URLs (free, no API key required)
        self.sources = [
            {
                "name": "Reuters",
                "url": "https://www.reutersagency.com/feed/?taxonomy=best-topics&post_type=best",
                "backup_url": "http://feeds.reuters.com/reuters/topNews"
            },
            {
                "name": "AP News",
                "url": "https://www.apnews.com/apf-topnews"
            },
            {
                "name": "Google News",
                "url": "https://news.google.com/rss"
            }
        ]

        # Cache for headlines (short TTL since news changes quickly)
        self.cache = {}
        self.cache_ttl = timedelta(minutes=5)  # 5 minute cache

    def fetch(self, query: str) -> FetchResult:
        """
        Fetch latest breaking news headlines.

        For generic queries like "latest news" or "breaking news",
        returns top headlines. For specific queries, filters headlines.
        """
        try:
            query_lower = query.lower()

            # Determine if this is a generic "latest news" query or specific topic
            is_generic_news = any(phrase in query_lower for phrase in [
                "latest news", "breaking news", "top news", "current news",
                "whats happening", "what's happening", "recent news"
            ])

            # Extract topic if present (for filtering)
            topic = None
            if not is_generic_news:
                # Remove common news query words to get topic
                topic_words = query_lower.replace("news about", "").replace("latest", "").replace("breaking", "").replace("news", "").strip()
                if topic_words:
                    topic = topic_words

            logger.info(f"Fetching news - Generic: {is_generic_news}, Topic: {topic}")

            # Try each source in priority order
            for source_config in self.sources:
                source_name = source_config["name"]

                # Check cache first
                cache_key = f"{source_name}:latest"
                if cache_key in self.cache:
                    cached_time, cached_headlines = self.cache[cache_key]
                    if datetime.now() - cached_time < self.cache_ttl:
                        logger.info(f"Using cached headlines from {source_name}")
                        headlines = cached_headlines
                    else:
                        # Cache expired, fetch fresh
                        headlines = self._fetch_from_source(source_config)
                        if headlines:
                            self.cache[cache_key] = (datetime.now(), headlines)
                else:
                    # No cache, fetch fresh
                    headlines = self._fetch_from_source(source_config)
                    if headlines:
                        self.cache[cache_key] = (datetime.now(), headlines)

                if not headlines:
                    continue  # Try next source

                # Filter by topic if specified
                if topic:
                    filtered = [h for h in headlines if topic in h["title"].lower() or topic in h.get("summary", "").lower()]
                    if filtered:
                        headlines = filtered
                    else:
                        # No matching headlines, try next source
                        continue

                # Build summary from top headlines
                summary_parts = []
                if is_generic_news:
                    summary_parts.append(f"Latest breaking news from {source_name}:")
                else:
                    summary_parts.append(f"Latest news about '{topic}' from {source_name}:")

                # Include top 5 headlines
                for i, headline in enumerate(headlines[:5], 1):
                    title = headline["title"]
                    # Clean up title (remove source name if present)
                    if " - " in title:
                        title = title.split(" - ")[0].strip()
                    summary_parts.append(f"{i}. {title}")

                summary = "\n".join(summary_parts)

                # Prepare structured data
                data = {
                    "headlines": headlines[:5],
                    "source": source_name,
                    "topic": topic,
                    "count": len(headlines[:5])
                }

                logger.info(f"Found {len(headlines)} headlines from {source_name}")

                return FetchResult(
                    status=FetchStatus.FOUND,
                    data=data,
                    summary=summary,
                    confidence=0.85 if is_generic_news else 0.75,  # Higher confidence for generic news
                    source=source_name.lower().replace(" ", "_"),
                    url=headlines[0]["link"] if headlines else None
                )

            # All sources failed
            logger.warning("All news sources failed to return headlines")
            return FetchResult(
                status=FetchStatus.NOT_FOUND,
                data={},
                summary="Unable to fetch latest news headlines at this time. News sources may be temporarily unavailable.",
                confidence=0.0,
                source="newsapi"
            )

        except Exception as e:
            logger.error(f"Error fetching news: {e}")
            return FetchResult(
                status=FetchStatus.ERROR,
                data={},
                error=str(e),
                confidence=0.0,
                source="newsapi"
            )

    def _fetch_from_source(self, source_config: dict) -> list:
        """
        Fetch headlines from a single RSS source.

        Returns:
            List of dicts with keys: title, link, published, summary
        """
        source_name = source_config["name"]
        url = source_config["url"]

        try:
            logger.info(f"Fetching from {source_name}: {url}")
            feed = feedparser.parse(url)

            # Check if feed was parsed successfully
            if feed.bozo:  # bozo=True means parsing had issues
                logger.warning(f"{source_name} feed parsing had issues: {feed.bozo_exception}")
                # Try backup URL if available
                if "backup_url" in source_config:
                    logger.info(f"Trying backup URL for {source_name}")
                    url = source_config["backup_url"]
                    feed = feedparser.parse(url)

            if not feed.entries:
                logger.warning(f"{source_name} returned no entries")
                return []

            headlines = []
            for entry in feed.entries[:10]:  # Get top 10 headlines
                headline = {
                    "title": entry.get("title", "No title"),
                    "link": entry.get("link", ""),
                    "published": entry.get("published", ""),
                    "summary": entry.get("summary", entry.get("description", ""))
                }
                headlines.append(headline)

            logger.info(f"Successfully fetched {len(headlines)} headlines from {source_name}")
            return headlines

        except Exception as e:
            logger.error(f"Error fetching from {source_name}: {e}")
            return []
