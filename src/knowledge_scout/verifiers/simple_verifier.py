from .base import BaseVerifier, VerificationResult
from ..fetchers.base import FetchResult, FetchSource

class SimpleVerifier(BaseVerifier):
    def verify(self, fetch_result: FetchResult) -> VerificationResult:
        """
        Verifies fetch results based on source quality, citations, and content.
        """
        reasons = []
        confidence = 0.0

        # Evaluate source reliability
        if fetch_result.source == FetchSource.PERPLEXITY_API:
            confidence = 0.8
            reasons.append("Reliable API source.")
        elif fetch_result.source == FetchSource.LOCAL_RSS:
            confidence = 0.5
            reasons.append("RSS feed source (may vary in quality).")
        elif fetch_result.source == FetchSource.CACHE:
            confidence = 0.7
            reasons.append("Cached data (previously verified).")
        else:  # Fallback
            confidence = 0.0
            reasons.append("Fallback source - no reliable data found.")

        # Adjust for citation quality
        num_citations = len(fetch_result.citations)
        if num_citations >= 2:
            confidence = min(1.0, confidence + 0.15)
            reasons.append(f"Well-cited ({num_citations} sources).")
        elif num_citations == 1:
            reasons.append("Single citation provided.")
        else:
            confidence = max(0.0, confidence - 0.2)
            reasons.append("No citations - reduced confidence.")
            
        # Check answer completeness
        if len(fetch_result.answer) < 25:
            confidence = max(0.0, confidence - 0.4)
            reasons.append("Answer too brief - likely incomplete.")

        # Check staleness
        if fetch_result.is_stale:
            confidence = 0.0
            reasons.append("Data marked as stale.")

        is_verified = confidence >= 0.5

        return VerificationResult(
            is_verified=is_verified,
            confidence=round(confidence, 2),
            reason=" ".join(reasons)
        )
