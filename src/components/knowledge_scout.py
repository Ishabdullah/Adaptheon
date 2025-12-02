import time
from knowledge_scout.fetchers.cache_fetcher import CacheFetcher
from knowledge_scout.fetchers.rss_fetcher import RSSFetcher
from knowledge_scout.fetchers.wikipedia_fetcher import WikipediaFetcher
from knowledge_scout.fetchers.base import FetchSource

class KnowledgeScout:
    """
    Phase 1.5: Multi-layer information retrieval system.
    Order: Cache → Wikipedia → RSS.
    """
    def __init__(self):
        print("  [Scout] Initializing fetcher layers...")
        self.cache = CacheFetcher()
        self.wikipedia = WikipediaFetcher()
        self.rss = RSSFetcher()
        
        # Ordered by speed and reliability
        self.fetchers = [
            self.cache,
            self.wikipedia,
            self.rss
        ]
    
    def search(self, query: str):
        """
        Waterfall search: try each fetcher until one succeeds.
        Returns a simple dict for the Meta-Core.
        """
        print("    [Scout] Deploying agents for: '{}'...".format(query))
        
        for fetcher in self.fetchers:
            result = fetcher.fetch(query)
            
            if result:
                # Cache everything except cache hits themselves
                if result.source is not FetchSource.CACHE:
                    self.cache.store(result)
                
                return {
                    "status": "FOUND",
                    "summary": result.summary,
                    "source": result.source.value,
                    "confidence": result.confidence,
                    "url": result.url,
                }
        
        # All fetchers failed
        return {
            "status": "NOT_FOUND",
            "summary": "I couldn't find reliable information about '{}'.".format(query),
            "source": "none",
            "confidence": 0.0,
            "url": None,
        }
