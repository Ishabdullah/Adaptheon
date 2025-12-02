from .cache_fetcher import CacheFetcher
from .rss_fetcher import RSSFetcher
from .perplexity_fetcher import PerplexityFetcher
from .base import FetchResult, FetchSource

class FetcherChain:
    def __init__(self):
        self.cache = CacheFetcher()
        self.rss = RSSFetcher()
        self.perplexity = PerplexityFetcher()

    def fetch(self, query):
        print(f"\n[Fetcher Chain] Initiating fetch sequence...")
        
        # Try cache first (fastest)
        result = self.cache.fetch(query)
        if result:
            return result
        
        # Try RSS (fast, no API cost)
        result = self.rss.fetch(query)
        if result:
            # Cache for next time
            self.cache.store(query, result)
            return result
        
        # Try Perplexity (slow, costs money)
        result = self.perplexity.fetch(query)
        if result:
            self.cache.store(query, result)
            return result
        
        # Fallback
        print("  [Fetcher Chain] All fetchers failed")
        return FetchResult(
            answer="I couldn't find reliable information about that.",
            citations=[],
            raw_data="",
            source=FetchSource.FALLBACK,
            fetch_time=0,
            is_stale=True
        )
