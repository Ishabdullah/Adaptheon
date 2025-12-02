from dataclasses import dataclass
from typing import Optional
from enum import Enum
import abc
import time

class FetchSource(Enum):
    """Identifies where information came from"""
    CACHE = "cache"
    LOCAL_RSS = "local_rss"
    WEB_SCRAPE = "web_scrape"
    WIKIPEDIA = "wikipedia"

@dataclass
class FetchResult:
    """Standardized container for fetched information"""
    query: str
    summary: str
    source: FetchSource
    confidence: float  # 0.0 to 1.0
    url: Optional[str] = None
    timestamp: float = 0.0
    
    def __post_init__(self):
        if self.timestamp == 0.0:
            self.timestamp = time.time()

class BaseFetcher(abc.ABC):
    """Abstract base for all fetcher implementations"""
    
    @abc.abstractmethod
    def fetch(self, query: str) -> Optional[FetchResult]:
        """Attempt to fetch information for the given query"""
        pass
    
    def is_available(self) -> bool:
        """Check if this fetcher can currently operate"""
        return True
