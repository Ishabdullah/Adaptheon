from enum import Enum
from dataclasses import dataclass
from typing import Optional


class FetchSource(Enum):
    WIKIPEDIA = "wikipedia"
    LOCAL_RSS = "local_rss"
    LOCAL_CORPUS = "local_corpus"


@dataclass
class FetchResult:
    query: str
    summary: str
    source: FetchSource
    confidence: float
    url: Optional[str] = None


class BaseFetcher:
    def fetch(self, query: str) -> Optional[FetchResult]:
        raise NotImplementedError
