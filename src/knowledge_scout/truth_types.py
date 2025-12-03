from enum import Enum
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional


class SourceTier(Enum):
    PRIMARY = "primary"
    SECONDARY = "secondary"
    TERTIARY = "tertiary"


class SourceKind(Enum):
    WIKIDATA = "wikidata"
    WIKIPEDIA = "wikipedia"
    DBPEDIA = "dbpedia"
    NEWS_RSS = "news_rss"
    FINANCE = "finance"
    CRYPTO = "crypto"
    WEATHER = "weather"
    SPORTS = "sports"
    GOVERNMENT_API = "government_api"
    OPEN_DATA = "open_data"
    COMMUNITY = "community"
    LOCAL_CORPUS = "local_corpus"
    OTHER = "other"


@dataclass
class SourceTraceEntry:
    tier: SourceTier
    kind: SourceKind
    name: str
    url: Optional[str] = None
    confidence: float = 0.0
    note: str = ""


@dataclass
class TruthResult:
    status: str
    query: str
    canonical_summary: str
    confidence: float
    primary_source: SourceKind
    tier: SourceTier
    snippets: List[str] = field(default_factory=list)
    source_trace: List[SourceTraceEntry] = field(default_factory=list)
    violations: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
