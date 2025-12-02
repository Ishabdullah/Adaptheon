import time
from knowledge_scout.fetchers.cache_fetcher import CacheFetcher
from knowledge_scout.fetchers.rss_fetcher import RSSFetcher
from knowledge_scout.fetchers.wikipedia_fetcher import WikipediaFetcher

class KnowledgeScout:
    """
    Phase 1.5: Multi-layer information retrieval system.
    Tries: Cache → Wikipedia → RSS in order of reliability.
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
        """
        print(f"    [Scout] Deploying agents for: '{query}'...")
        
        for fetcher in self.fetchers:
            result = fetcher.fetch(query)
            
            if result:
                # Cache network results for future use
                if result.source != "cache":
                    self.cache.store(result)
                
                return {
                    "status": "FOUND",
                    "summary": result.summary,
                    "source": result.source.value,
                    "confidence": result.confidence,
                    "url": result.url
                }
        
        # All fetchers failed
        return {
            "status": "NOT_FOUND",
            "summary": f"I couldn't find reliable information about '{query}'.",
            "source": "none",
            "confidence": 0.0
        }
