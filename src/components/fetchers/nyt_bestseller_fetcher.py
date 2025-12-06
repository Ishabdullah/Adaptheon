"""
NYT Bestseller Fetcher - Current Bestseller Lists
Uses free NYT RSS feeds for bestseller data
"""

import feedparser
import logging
from datetime import datetime, timedelta
from .base_fetcher import BaseFetcher, FetchResult, FetchStatus

logger = logging.getLogger('Adaptheon.NYTBestsellerFetcher')


class NYTBestsellerFetcher(BaseFetcher):
    """
    Fetches current NYT bestseller lists from RSS feeds.
    No API key required - uses free RSS feeds.

    Lists available:
    - Fiction (Combined Print & E-Book)
    - Nonfiction (Combined Print & E-Book)
    - Hardcover Fiction
    - Hardcover Nonfiction
    """

    def _setup(self):
        # NYT Bestseller RSS feeds (free, no API key required)
        self.feeds = {
            "fiction": "https://www.nytimes.com/books/best-sellers/combined-print-and-e-book-fiction.xml",
            "nonfiction": "https://www.nytimes.com/books/best-sellers/combined-print-and-e-book-nonfiction.xml",
            "hardcover_fiction": "https://www.nytimes.com/books/best-sellers/hardcover-fiction.xml",
            "hardcover_nonfiction": "https://www.nytimes.com/books/best-sellers/hardcover-nonfiction.xml",
        }

        # Cache for bestseller lists (short TTL since lists update weekly)
        self.cache = {}
        self.cache_ttl = timedelta(hours=12)  # 12 hour cache (lists update weekly anyway)

    def fetch(self, query: str) -> FetchResult:
        """
        Fetch NYT bestseller information.

        Handles queries like:
        - "NYT bestseller"
        - "New York Times #1 book"
        - "newest fiction bestseller"
        - "latest nonfiction bestseller"
        """
        try:
            query_lower = query.lower()

            # Determine which list to query
            list_type = "fiction"  # Default to fiction

            if any(word in query_lower for word in ["nonfiction", "non-fiction", "non fiction"]):
                list_type = "nonfiction"
            elif any(word in query_lower for word in ["hardcover fiction"]):
                list_type = "hardcover_fiction"
            elif any(word in query_lower for word in ["hardcover nonfiction", "hardcover non-fiction"]):
                list_type = "hardcover_nonfiction"

            # Extract rank if specified (#1, #2, top 5, etc.)
            rank = 1  # Default to #1
            if "#1" in query_lower or "number 1" in query_lower or "number one" in query_lower:
                rank = 1
            elif "#2" in query_lower or "number 2" in query_lower or "number two" in query_lower:
                rank = 2
            elif "#3" in query_lower or "number 3" in query_lower or "number three" in query_lower:
                rank = 3

            # Determine if user wants top N or just one book
            want_top_n = any(phrase in query_lower for phrase in [
                "top 5", "top five", "top 3", "top three", "top 10", "top ten", "list"
            ])

            if "top 5" in query_lower or "top five" in query_lower:
                num_results = 5
            elif "top 3" in query_lower or "top three" in query_lower:
                num_results = 3
            elif "top 10" in query_lower or "top ten" in query_lower:
                num_results = 10
            else:
                num_results = 1 if not want_top_n else 5

            logger.info(f"Fetching {list_type} bestsellers (rank: {rank}, results: {num_results})")

            # Fetch bestseller list
            bestsellers = self._fetch_list(list_type)

            if not bestsellers:
                logger.warning(f"No bestsellers found for {list_type}")
                return FetchResult(
                    status=FetchStatus.NOT_FOUND,
                    data={},
                    summary="Unable to fetch NYT bestseller list at this time. The feed may be temporarily unavailable.",
                    confidence=0.0,
                    source="nyt_bestseller"
                )

            # Build response
            if want_top_n:
                # Return top N books
                books = bestsellers[:num_results]
                summary_parts = [f"NYT Bestseller List ({list_type.replace('_', ' ').title()}):"]

                for i, book in enumerate(books, 1):
                    title = book["title"]
                    author = book["author"]
                    summary_parts.append(f"{i}. {title} by {author}")

                summary = "\n".join(summary_parts)
                confidence = 0.90
            else:
                # Return single book at specified rank
                if rank > len(bestsellers):
                    return FetchResult(
                        status=FetchStatus.NOT_FOUND,
                        data={},
                        summary=f"Bestseller list only has {len(bestsellers)} books, but you requested rank #{rank}.",
                        confidence=0.0,
                        source="nyt_bestseller"
                    )

                book = bestsellers[rank - 1]  # rank is 1-indexed
                title = book["title"]
                author = book["author"]
                description = book.get("description", "")

                summary = f"#{rank} NYT Bestseller ({list_type.replace('_', ' ').title()}): {title} by {author}"
                if description:
                    summary += f"\n\n{description}"

                confidence = 0.95
                books = [book]

            # Prepare structured data
            data = {
                "list_type": list_type,
                "rank": rank,
                "books": books,
                "count": len(books)
            }

            logger.info(f"Found {len(books)} bestseller(s) from {list_type} list")

            return FetchResult(
                status=FetchStatus.FOUND,
                data=data,
                summary=summary,
                confidence=confidence,
                source="nyt_bestseller",
                url=books[0]["link"] if books and books[0].get("link") else None
            )

        except Exception as e:
            logger.error(f"Error fetching NYT bestsellers: {e}")
            return FetchResult(
                status=FetchStatus.ERROR,
                data={},
                error=str(e),
                confidence=0.0,
                source="nyt_bestseller"
            )

    def _fetch_list(self, list_type: str) -> list:
        """
        Fetch bestseller list from NYT RSS feed.

        Returns:
            List of dicts with keys: title, author, link, description
        """
        # Check cache first
        cache_key = f"nyt_{list_type}"
        if cache_key in self.cache:
            cached_time, cached_books = self.cache[cache_key]
            if datetime.now() - cached_time < self.cache_ttl:
                logger.info(f"Using cached NYT {list_type} bestsellers")
                return cached_books

        # Fetch fresh data
        feed_url = self.feeds.get(list_type)
        if not feed_url:
            logger.error(f"Unknown list type: {list_type}")
            return []

        try:
            logger.info(f"Fetching NYT {list_type} from: {feed_url}")
            feed = feedparser.parse(feed_url)

            # Check if feed was parsed successfully
            if feed.bozo:
                logger.warning(f"NYT {list_type} feed parsing had issues: {feed.bozo_exception}")

            if not feed.entries:
                logger.warning(f"NYT {list_type} returned no entries")
                return []

            books = []
            for entry in feed.entries[:15]:  # Get top 15 books
                book = {
                    "title": entry.get("title", "No title"),
                    "author": self._extract_author(entry),
                    "link": entry.get("link", ""),
                    "description": entry.get("summary", entry.get("description", ""))
                }
                books.append(book)

            # Cache the results
            self.cache[cache_key] = (datetime.now(), books)

            logger.info(f"Successfully fetched {len(books)} books from NYT {list_type}")
            return books

        except Exception as e:
            logger.error(f"Error fetching NYT {list_type} list: {e}")
            return []

    def _extract_author(self, entry: dict) -> str:
        """
        Extract author name from RSS entry.
        NYT format often has "by Author Name" in the title or summary.
        """
        # Try to extract from author field
        if entry.get("author"):
            return entry["author"]

        # Try to extract from "by Author Name" pattern in title
        title = entry.get("title", "")
        if " by " in title:
            # Format: "Book Title by Author Name"
            parts = title.split(" by ")
            if len(parts) == 2:
                return parts[1].strip()

        # Try to extract from summary
        summary = entry.get("summary", "")
        if " by " in summary:
            # Extract text after "by" and before next punctuation
            after_by = summary.split(" by ", 1)[1]
            # Take until first period or comma
            for delimiter in [".", ",", "\n"]:
                if delimiter in after_by:
                    return after_by.split(delimiter)[0].strip()
            return after_by[:50].strip()  # Limit to 50 chars

        return "Unknown Author"
