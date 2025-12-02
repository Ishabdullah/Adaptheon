import requests
from bs4 import BeautifulSoup
import re
from typing import Optional
from .base import BaseFetcher, FetchResult, FetchSource

class WikipediaFetcher(BaseFetcher):
    """
    Fetches reliable, structured information from Wikipedia.
    Best for factual queries about concepts, people, places.
    """
    def __init__(self):
        self.headers = {
            'User-Agent': 'Adaptheon/1.0 (Educational Project; Python/3.11)'
        }
    
    def fetch(self, query: str) -> Optional[FetchResult]:
        # Format query for Wikipedia URL
        formatted = query.replace(' ', '_')
        url = f"https://en.wikipedia.org/wiki/{formatted}"
        
        print(f"    [Wikipedia] Fetching: {url}")
        
        try:
            response = requests.get(url, headers=self.headers, timeout=5)
            
            if response.status_code == 404:
                print(f"    [Wikipedia] ✗ Article not found")
                return None
            
            response.raise_for_status()
            soup = BeautifulSoup(response.content, 'lxml')
            
            # Find the main content
            content = soup.find(id='mw-content-text')
            if not content:
                return None
            
            # Get first substantial paragraph
            for p in content.find_all('p', recursive=False):
                text = p.get_text(strip=True)
                if len(text) > 100:  # Skip short paragraphs
                    # Clean up citation markers
                    text = re.sub(r'\[\d+\]', '', text)
                    text = re.sub(r'\s+', ' ', text)
                    
                    print(f"    [Wikipedia] ✓ Extracted summary")
                    return FetchResult(
                        query=query,
                        summary=text,
                        source=FetchSource.WIKIPEDIA,
                        confidence=0.85,
                        url=url
                    )
            
            return None
        
        except requests.RequestException as e:
            print(f"    [Wikipedia] Network error: {e}")
            return None
        except Exception as e:
            print(f"    [Wikipedia] Parse error: {e}")
            return None
