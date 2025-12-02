import json
import os
import time
from typing import Optional
from .base import BaseFetcher, FetchResult, FetchSource

class CacheFetcher(BaseFetcher):
    """
    First line of defense: check if we already know this.
    Prevents redundant network calls and speeds up responses.
    """
    def __init__(self, cache_path="data/cache/knowledge_cache.json"):
        self.cache_path = cache_path
        self.cache = self._load_cache()
    
    def _load_cache(self):
        if os.path.exists(self.cache_path):
            try:
                with open(self.cache_path, 'r') as f:
                    return json.load(f)
            except json.JSONDecodeError:
                print("    [Cache] Warning: corrupted cache, rebuilding...")
                return {}
        return {}
    
    def _save_cache(self):
        os.makedirs(os.path.dirname(self.cache_path), exist_ok=True)
        with open(self.cache_path, 'w') as f:
            json.dump(self.cache, f, indent=2)
    
    def fetch(self, query: str) -> Optional[FetchResult]:
        key = query.lower().strip()
        
        if key in self.cache:
            cached = self.cache[key]
            print(f"    [Cache] ✓ Hit: '{query}'")
            return FetchResult(
                query=query,
                summary=cached['summary'],
                source=FetchSource.CACHE,
                confidence=cached.get('confidence', 0.95),
                url=cached.get('url'),
                timestamp=cached.get('timestamp', 0)
            )
        
        print(f"    [Cache] ✗ Miss: '{query}'")
        return None
    
    def store(self, result: FetchResult):
        """Save a new fact to cache"""
        key = result.query.lower().strip()
        self.cache[key] = {
            'summary': result.summary,
            'confidence': result.confidence,
            'url': result.url,
            'timestamp': result.timestamp
        }
        self._save_cache()
        print(f"    [Cache] Stored: '{result.query}'")
