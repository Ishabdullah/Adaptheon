import feedparser
from typing import Optional
from .base import BaseFetcher, FetchResult, FetchSource

class RSSFetcher(BaseFetcher):
    """
    Fetches current information from RSS feeds.
    Good for tech news, blogs, and timely information.
    """
    def __init__(self):
        # Curated list of reliable feeds
        self.feeds = [
            "https://news.ycombinator.com/rss",
            "https://www.theverge.com/rss/index.xml",
            "https://techcrunch.com/feed/"
        ]
    
    def fetch(self, query: str) -> Optional[FetchResult]:
        print(f"    [RSS] Scanning {len(self.feeds)} feeds...")
        
        query_terms = set(query.lower().split())
        best_match = None
        best_score = 0
        
        for feed_url in self.feeds:
            try:
                feed = feedparser.parse(feed_url)
                
                for entry in feed.entries[:15]:  # Check recent entries
                    title = entry.get('title', '').lower()
                    summary = entry.get('summary', entry.get('description', ''))
                    
                    # Calculate relevance score
                    score = sum(1 for term in query_terms if term in title)
                    score += sum(0.5 for term in query_terms if term in summary.lower())
                    
                    if score > best_score:
                        best_score = score
                        best_match = {
                            'title': entry.get('title', ''),
                            'summary': summary[:300],
                            'link': entry.get('link', '')
                        }
            
            except Exception as e:
                print(f"    [RSS] Feed error: {e}")
                continue
        
        if best_match and best_score > 0:
            print(f"    [RSS] ✓ Found: '{best_match['title']}'")
            return FetchResult(
                query=query,
                summary=f"{best_match['title']}: {best_match['summary']}",
                source=FetchSource.LOCAL_RSS,
                confidence=min(0.6 + (best_score * 0.1), 0.9),
                url=best_match['link']
            )
        
        print(f"    [RSS] ✗ No relevant articles found")
        return None
