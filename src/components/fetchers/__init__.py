"""
Adaptheon Fetchers Package
Production-grade domain-specific information retrieval modules
"""

from .base_fetcher import BaseFetcher, FetchResult, FetchStatus

# Knowledge & Reference
from .wikidata_fetcher import WikidataFetcher
from .dbpedia_fetcher import DBpediaFetcher

# Academic & Research
from .arxiv_fetcher import ArxivFetcher
from .semantic_scholar_fetcher import SemanticScholarFetcher

# Development & Tech
from .github_fetcher import GithubFetcher
from .huggingface_fetcher import HuggingFaceFetcher

# Finance & Crypto
from .yahoo_finance_fetcher import YahooFinanceFetcher
from .coinmarketcap_fetcher import CoinMarketCapFetcher

# Weather & Location
from .open_meteo_fetcher import OpenMeteoFetcher

# Media & Entertainment
from .tmdb_fetcher import TMDBFetcher
from .openlibrary_fetcher import OpenLibraryFetcher
from .musicbrainz_fetcher import MusicBrainzFetcher

# Social & News
from .reddit_fetcher import RedditFetcher
from .newsapi_fetcher import NewsAPIFetcher

# Sports
from .thesportsdb_fetcher import TheSportsDBFetcher

# Business & Corporate
from .opencorporates_fetcher import OpenCorporatesFetcher

# Government & Public Data
from .usagov_fetcher import USAGovFetcher
from .datagov_fetcher import DataGovFetcher
from .fbi_crime_fetcher import FBICrimeFetcher

# International Organizations
from .worldbank_fetcher import WorldBankFetcher
from .eurostat_fetcher import EurostatFetcher
from .who_fetcher import WHOFetcher

# Transportation
from .opensky_fetcher import OpenSkyFetcher

__all__ = [
    # Base
    'BaseFetcher',
    'FetchResult',
    'FetchStatus',

    # Knowledge & Reference
    'WikidataFetcher',
    'DBpediaFetcher',

    # Academic & Research
    'ArxivFetcher',
    'SemanticScholarFetcher',

    # Development & Tech
    'GithubFetcher',
    'HuggingFaceFetcher',

    # Finance & Crypto
    'YahooFinanceFetcher',
    'CoinMarketCapFetcher',

    # Weather & Location
    'OpenMeteoFetcher',

    # Media & Entertainment
    'TMDBFetcher',
    'OpenLibraryFetcher',
    'MusicBrainzFetcher',

    # Social & News
    'RedditFetcher',
    'NewsAPIFetcher',

    # Sports
    'TheSportsDBFetcher',

    # Business & Corporate
    'OpenCorporatesFetcher',

    # Government & Public Data
    'USAGovFetcher',
    'DataGovFetcher',
    'FBICrimeFetcher',

    # International Organizations
    'WorldBankFetcher',
    'EurostatFetcher',
    'WHOFetcher',

    # Transportation
    'OpenSkyFetcher',
]
