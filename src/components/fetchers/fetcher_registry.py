"""
Fetcher Registry - Centralized Management of All Domain Fetchers
Intelligent routing and fetcher selection
"""

from typing import Dict, List, Optional, Type
from .base_fetcher import BaseFetcher, FetchResult, FetchStatus

# Import all fetchers
from .wikidata_fetcher import WikidataFetcher
from .dbpedia_fetcher import DBpediaFetcher
from .arxiv_fetcher import ArxivFetcher
from .semantic_scholar_fetcher import SemanticScholarFetcher
from .github_fetcher import GithubFetcher
from .huggingface_fetcher import HuggingFaceFetcher
from .yahoo_finance_fetcher import YahooFinanceFetcher
from .coinmarketcap_fetcher import CoinMarketCapFetcher
from .open_meteo_fetcher import OpenMeteoFetcher
from .tmdb_fetcher import TMDBFetcher
from .openlibrary_fetcher import OpenLibraryFetcher
from .nyt_bestseller_fetcher import NYTBestsellerFetcher
from .musicbrainz_fetcher import MusicBrainzFetcher
from .reddit_fetcher import RedditFetcher
from .newsapi_fetcher import NewsAPIFetcher
from .thesportsdb_fetcher import TheSportsDBFetcher
from .opencorporates_fetcher import OpenCorporatesFetcher
from .usagov_fetcher import USAGovFetcher
from .datagov_fetcher import DataGovFetcher
from .fbi_crime_fetcher import FBICrimeFetcher
from .worldbank_fetcher import WorldBankFetcher
from .eurostat_fetcher import EurostatFetcher
from .who_fetcher import WHOFetcher
from .opensky_fetcher import OpenSkyFetcher


class FetcherRegistry:
    """
    Central registry for all domain-specific fetchers.
    Provides intelligent routing based on query analysis.
    """

    def __init__(self):
        self.fetchers: Dict[str, BaseFetcher] = {}
        self.domain_keywords: Dict[str, List[str]] = {}
        self._initialize_fetchers()

    def _initialize_fetchers(self):
        """Initialize all fetchers and their domain keywords"""

        # Knowledge & Reference
        self.register_fetcher('wikidata', WikidataFetcher(),
                            ['who is', 'what is', 'president', 'population', 'fact', 'when was'])
        self.register_fetcher('dbpedia', DBpediaFetcher(),
                            ['entity', 'properties', 'categories', 'resource'])

        # Academic & Research
        self.register_fetcher('arxiv', ArxivFetcher(),
                            ['paper', 'research', 'arxiv', 'study', 'scientific'])
        self.register_fetcher('semantic_scholar', SemanticScholarFetcher(),
                            ['academic', 'citation', 'scholar', 'publication'])

        # Development & Tech
        self.register_fetcher('github', GithubFetcher(),
                            ['repository', 'repo', 'github', 'developer', 'code'])
        self.register_fetcher('huggingface', HuggingFaceFetcher(),
                            ['model', 'dataset', 'huggingface', 'ml', 'ai', 'transformer'])

        # Finance & Crypto
        self.register_fetcher('yahoo_finance', YahooFinanceFetcher(),
                            ['stock', 'ticker', 'share', 'nasdaq', 'dow', 'apple', 'microsoft', 'tesla'])
        self.register_fetcher('coinmarketcap', CoinMarketCapFetcher(),
                            ['crypto', 'cryptocurrency', 'bitcoin', 'ethereum', 'coin'])

        # Weather & Location
        self.register_fetcher('open_meteo', OpenMeteoFetcher(),
                            ['weather', 'temperature', 'forecast', 'climate'])

        # Media & Entertainment
        self.register_fetcher('tmdb', TMDBFetcher(),
                            ['movie', 'film', 'tv show', 'series', 'actor'])
        self.register_fetcher('openlibrary', OpenLibraryFetcher(),
                            ['book', 'author', 'isbn', 'library', 'novel'])
        self.register_fetcher('nyt_bestseller', NYTBestsellerFetcher(),
                            ['bestseller', 'best seller', 'nyt', 'new york times', 'top book'])
        self.register_fetcher('musicbrainz', MusicBrainzFetcher(),
                            ['artist', 'album', 'music', 'song', 'band'])

        # Social & News
        self.register_fetcher('reddit', RedditFetcher(),
                            ['reddit', 'subreddit', 'r/', 'trending post'])
        self.register_fetcher('newsapi', NewsAPIFetcher(),
                            ['news', 'headline', 'breaking'])

        # Sports
        self.register_fetcher('thesportsdb', TheSportsDBFetcher(),
                            ['team', 'league', 'sports', 'nfl', 'nba', 'soccer'])

        # Business & Corporate
        self.register_fetcher('opencorporates', OpenCorporatesFetcher(),
                            ['company', 'corporation', 'business', 'corporate'])

        # Government & Public Data
        self.register_fetcher('usagov', USAGovFetcher(),
                            ['usa.gov', 'federal', 'government service'])
        self.register_fetcher('datagov', DataGovFetcher(),
                            ['data.gov', 'dataset', 'government data', 'open data'])
        self.register_fetcher('fbi_crime', FBICrimeFetcher(),
                            ['crime', 'fbi', 'criminal', 'justice'])

        # International Organizations
        self.register_fetcher('worldbank', WorldBankFetcher(),
                            ['gdp', 'world bank', 'development', 'economy'])
        self.register_fetcher('eurostat', EurostatFetcher(),
                            ['eu', 'europe', 'eurostat', 'european union'])
        self.register_fetcher('who', WHOFetcher(),
                            ['health', 'who', 'disease', 'pandemic', 'medical'])

        # Transportation
        self.register_fetcher('opensky', OpenSkyFetcher(),
                            ['flight', 'aircraft', 'aviation', 'plane'])

    def register_fetcher(self, name: str, fetcher: BaseFetcher, keywords: List[str]):
        """Register a fetcher with its domain keywords"""
        self.fetchers[name] = fetcher
        self.domain_keywords[name] = [k.lower() for k in keywords]

    def route_query(self, query: str) -> List[str]:
        """
        Analyze query and return ordered list of fetcher names to try.
        Returns fetchers most likely to have relevant information.
        """
        query_lower = query.lower()
        scores: Dict[str, int] = {}

        # Score each fetcher based on keyword matches
        for fetcher_name, keywords in self.domain_keywords.items():
            score = 0
            for keyword in keywords:
                if keyword in query_lower:
                    # Longer keywords get higher weight
                    score += len(keyword.split())

            if score > 0:
                scores[fetcher_name] = score

        # Sort by score (highest first)
        sorted_fetchers = sorted(scores.items(), key=lambda x: x[1], reverse=True)
        return [name for name, score in sorted_fetchers]

    def fetch(self, query: str, max_fetchers: int = 3) -> List[FetchResult]:
        """
        Execute query across relevant fetchers.
        Returns list of results sorted by confidence.
        """
        results = []

        # Get prioritized fetcher list
        fetcher_names = self.route_query(query)

        # If no matches, try top general-purpose fetchers
        if not fetcher_names:
            fetcher_names = ['wikidata', 'dbpedia', 'semantic_scholar']

        # Query fetchers in priority order
        for fetcher_name in fetcher_names[:max_fetchers]:
            if fetcher_name in self.fetchers:
                try:
                    result = self.fetchers[fetcher_name].fetch(query)
                    if result.status == FetchStatus.FOUND:
                        results.append(result)
                except Exception as e:
                    # Log error but continue with other fetchers
                    print(f"Error in {fetcher_name}: {e}")
                    continue

        # Sort by confidence
        results.sort(key=lambda r: r.confidence, reverse=True)
        return results

    def get_fetcher(self, name: str) -> Optional[BaseFetcher]:
        """Get specific fetcher by name"""
        return self.fetchers.get(name)

    def list_fetchers(self) -> List[str]:
        """List all registered fetcher names"""
        return list(self.fetchers.keys())

    def get_stats(self) -> Dict[str, int]:
        """Get registry statistics"""
        return {
            'total_fetchers': len(self.fetchers),
            'total_keywords': sum(len(kw) for kw in self.domain_keywords.values())
        }
