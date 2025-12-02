import os
import requests
import time
from .base import FetchResult, FetchSource, Citation

class PerplexityFetcher:
    def __init__(self):
        self.api_key = os.environ.get('PERPLEXITY_API_KEY')
        self.enabled = self.api_key is not None
        
    def fetch(self, query):
        if not self.enabled:
            print("    [Perplexity] API key not set, skipping")
            return None
        
        print(f"    [Perplexity] Querying API...")
        start_time = time.time()
        
        try:
            response = requests.post(
                'https://api.perplexity.ai/chat/completions',
                headers={
                    'Authorization': f'Bearer {self.api_key}',
                    'Content-Type': 'application/json'
                },
                json={
                    'model': 'sonar-reasoning',
                    'messages': [
                        {'role': 'system', 'content': 'You are a factual research assistant. Be concise.'},
                        {'role': 'user', 'content': query}
                    ],
                    'temperature': 0.2,
                    'max_tokens': 500
                },
                timeout=10
            )
            
            if response.status_code != 200:
                print(f"    [Perplexity] API error: {response.status_code}")
                return None
            
            data = response.json()
            answer = data['choices'][0]['message']['content']
            citations_raw = data.get('citations', [])
            
            fetch_time = int((time.time() - start_time) * 1000)
            
            return FetchResult(
                answer=answer,
                citations=[Citation(
                    title=c.get('title', 'Source'),
                    url=c.get('url', ''),
                    relevance=0.9
                ) for c in citations_raw],
                raw_data=answer,
                source=FetchSource.PERPLEXITY_API,
                fetch_time=fetch_time,
                is_stale=False
            )
            
        except Exception as e:
            print(f"    [Perplexity] Error: {e}")
            return None
