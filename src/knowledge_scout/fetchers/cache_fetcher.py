import json
import os
import time
from datetime import datetime, timedelta
from .base import FetchResult, FetchSource, Citation

class CacheFetcher:
    def __init__(self, cache_dir="data/cache", ttl_hours=24):
        self.cache_dir = cache_dir
        self.ttl_hours = ttl_hours
        os.makedirs(cache_dir, exist_ok=True)
        
    def _get_cache_path(self, query):
        # Simple hash for filename
        cache_key = str(abs(hash(query.lower().strip())))
        return os.path.join(self.cache_dir, f"{cache_key}.json")
    
    def fetch(self, query):
        cache_path = self._get_cache_path(query)
        
        if not os.path.exists(cache_path):
            return None
            
        try:
            with open(cache_path, 'r') as f:
                cached = json.load(f)
            
            # Check TTL
            cached_time = datetime.fromisoformat(cached['timestamp'])
            if datetime.now() - cached_time > timedelta(hours=self.ttl_hours):
                print(f"    [Cache] Entry stale, TTL expired")
                return None
            
            print(f"    [Cache] HIT! Returning cached result (age: {datetime.now() - cached_time})")
            
            return FetchResult(
                answer=cached['answer'],
                citations=[Citation(**c) for c in cached['citations']],
                raw_data=cached.get('raw_data', ''),
                source=FetchSource.CACHE,
                fetch_time=5,
                is_stale=False
            )
        except Exception as e:
            print(f"    [Cache] Error reading cache: {e}")
            return None
    
    def store(self, query, result):
        """Store a fetch result in cache"""
        cache_path = self._get_cache_path(query)
        
        cache_data = {
            'query': query,
            'timestamp': datetime.now().isoformat(),
            'answer': result.answer,
            'citations': [{'title': c.title, 'url': c.url, 'relevance': c.relevance} 
                         for c in result.citations],
            'raw_data': result.raw_data,
            'source': result.source.value
        }
        
        with open(cache_path, 'w') as f:
            json.dump(cache_data, f, indent=2)
