from dataclasses import dataclass
from typing import List
from enum import Enum

class FetchSource(Enum):
    CACHE = "cache"
    LOCAL_RSS = "local_rss"
    PERPLEXITY_API = "perplexity_api"
    FALLBACK = "fallback"

@dataclass
class Citation:
    title: str
    url: str
    relevance: float  # 0.0-1.0

@dataclass
class FetchResult:
    answer: str
    citations: List[Citation]
    raw_data: str
    source: FetchSource
    fetch_time: int  # milliseconds
    is_stale: bool = False
