from abc import ABC, abstractmethod
from typing import Dict, Any


class BaseFetcher(ABC):
    """
    Base class for all domain-specific fetchers.
    Each fetcher must implement fetch() returning dict with 'status', 'data', 'confidence'.
    """

    @abstractmethod
    def fetch(self, query: str) -> Dict[str, Any]:
        pass
