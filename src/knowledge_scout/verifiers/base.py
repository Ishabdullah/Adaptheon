from dataclasses import dataclass
from abc import ABC, abstractmethod
from ..fetchers.base import FetchResult

@dataclass
class VerificationResult:
    is_verified: bool
    confidence: float  # 0.0 to 1.0
    reason: str

class BaseVerifier(ABC):
    @abstractmethod
    def verify(self, fetch_result: FetchResult) -> VerificationResult:
        """Analyzes a FetchResult and returns a VerificationResult."""
        pass
