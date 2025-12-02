import feedparser
import time
from datetime import datetime, timedelta
from .base import FetchResult, FetchSource, Citation

class RSSFetcher:
    def __init__(self):
        self.sources = [
            {
                'name': 'HackerNews',
                'url': 'https://news.ycombinator.com/rss',
                'category': 'tech'
            },
            {
                'name': 'ArXiv-AI',
                'url': 'http://export.arxiv.org/rss/cs.AI',
                'category': 'ai'
            },
            {
                'name': 'Nature',
                'url': 'http://feeds.nature.com/nature/rss/current',
                'category': 'science'
            },
            {
                'name': 'BBC',
                'url': 'http://feeds.bbci.co.uk/news/rss.xml',
                'category': 'general'
            }
        ]
        
    def fetch(self, query):
        print(f"    [RSS] Scanning feeds for: '{query}'")
        start_time = time.time()
        
        # Categorize query (simple keyword matching)
        category = self._categorize_query(query)
        relevant_sources = [s for s in self.sources 
                          if s['category'] == category or category == 'general']
        
        articles = []
        for source in relevant_sources[:2]:  # Limit to 2 sources for speed
            try:
                feed = feedparser.parse(source['url'])
                for entry in feed.entries[:10]:  # Top 10 per source
                    articles.append({
                        'title': entry.get('title', ''),
                        'link': entry.get('link', ''),
                        'summary': entry.get('summary', ''),
                        'published': entry.get('published', ''),
                        'source': source['name']
                    })
            except Exception as e:
                print(f"    [RSS] Failed to fetch {source['name']}: {e}")
                continue
        
        if not articles:
            return None
        
        # Find most relevant articles
        relevant = self._rank_articles(articles, query)[:3]
        
        if not relevant:
            return None
        
        # Synthesize answer from top articles
        answer = self._synthesize_answer(relevant, query)
        
        fetch_time = int((time.time() - start_time) * 1000)
        
        return FetchResult(
            answer=answer,
            citations=[Citation(
                title=a['title'],
                url=a['link'],
                relevance=a['relevance']
            ) for a in relevant],
            raw_data='

'.join([a['summary'] for a in relevant]),
            source=FetchSource.LOCAL_RSS,
            fetch_time=fetch_time,
            is_stale=False
        )
    
    def _categorize_query(self, query):
        query_lower = query.lower()
        if any(word in query_lower for word in ['ai', 'machine learning', 'neural', 'llm', 'model']):
            return 'ai'
        elif any(word in query_lower for word in ['tech', 'software', 'coding', 'programming']):
            return 'tech'
        elif any(word in query_lower for word in ['science', 'research', 'study']):
            return 'science'
        return 'general'
    
    def _rank_articles(self, articles, query):
        """Simple relevance scoring"""
        query_words = set(query.lower().split())
        
        for article in articles:
            title_words = set(article['title'].lower().split())
            summary_words = set(article['summary'].lower().split())
            
            # Calculate word overlap
            title_overlap = len(query_words & title_words) / len(query_words) if query_words else 0
            summary_overlap = len(query_words & summary_words) / len(query_words) if query_words else 0
            
            # Weighted relevance
            article['relevance'] = (title_overlap * 0.7 + summary_overlap * 0.3)
        
        # Filter and sort
        return [a for a in articles if a['relevance'] > 0.3][:5]
    
    def _synthesize_answer(self, articles, query):
        """Create a coherent answer from multiple articles"""
        if len(articles) == 1:
            return f"According to {articles[0]['source']}: {articles[0]['summary'][:200]}..."
        
        intro = f"Based on recent sources, here's what I found about '{query}':

"
        summaries = []
        
        for i, article in enumerate(articles, 1):
            summary = article['summary'][:150].strip()
            summaries.append(f"{i}. {article['source']}: {summary}...")
        
        return intro + '
'.join(summaries)
