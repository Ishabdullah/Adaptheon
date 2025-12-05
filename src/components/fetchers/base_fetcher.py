"""
Base Fetcher Infrastructure for Adaptheon
Production-grade foundation for all domain-specific fetchers
"""

from abc import ABC, abstractmethod
from enum import Enum
from dataclasses import dataclass
from typing import Dict, Any, Optional
import requests
from datetime import datetime

class FetchStatus(Enum):
    """Status codes for fetch operations"""
    FOUND = "FOUND"
    NOT_FOUND = "NOT_FOUND"
    ERROR = "ERROR"
    RATE_LIMITED = "RATE_LIMITED"
    API_KEY_REQUIRED = "API_KEY_REQUIRED"

@dataclass
class FetchResult:
    """Standardized result from any fetcher"""
    status: FetchStatus
    data: Dict[str, Any]
    summary: Optional[str] = None
    confidence: float = 0.0
    source: Optional[str] = None
    url: Optional[str] = None
    timestamp: Optional[str] = None
    error: Optional[str] = None

    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.utcnow().isoformat()

class BaseFetcher(ABC):
    """
    Abstract base class for all domain-specific fetchers.

    All fetchers must implement:
    - fetch(query) -> FetchResult
    - Proper error handling
    - Rate limiting respect
    - Schema validation
    """

    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Adaptheon/2.0 (Educational Research System)'
        })
        self._setup()

    def _setup(self):
        """Override to perform fetcher-specific setup"""
        pass

    @abstractmethod
    def fetch(self, query: str) -> FetchResult:
        """
        Fetch information for the given query.

        Args:
            query: User's information request

        Returns:
            FetchResult with status, data, and metadata
        """
        pass

    def _make_request(self, url: str, params: Optional[Dict] = None,
                     headers: Optional[Dict] = None, timeout: int = 10) -> Optional[Dict]:
        """
        Make a robust HTTP request with error handling

        Args:
            url: Target URL
            params: Query parameters
            headers: Additional headers
            timeout: Request timeout in seconds

        Returns:
            JSON response dict or None on failure
        """
        try:
            req_headers = self.session.headers.copy()
            if headers:
                req_headers.update(headers)

            response = self.session.get(
                url,
                params=params,
                headers=req_headers,
                timeout=timeout
            )

            if response.status_code == 429:
                return None  # Rate limited

            response.raise_for_status()

            return response.json() if 'json' in response.headers.get('content-type', '') else None

        except requests.Timeout:
            return None
        except requests.RequestException:
            return None
        except ValueError:  # JSON decode error
            return None

    def _clean_text(self, text: str, max_length: int = 500) -> str:
        """Clean and truncate text"""
        if not text:
            return ""
        text = ' '.join(text.split())  # Normalize whitespace
        if len(text) > max_length:
            text = text[:max_length].rsplit(' ', 1)[0] + '...'
        return text
