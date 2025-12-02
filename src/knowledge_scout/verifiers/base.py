from dataclasses import dataclass
from typing import List

@dataclass
class VerificationResult:
    confidence: float  # 0.0-1.0
    passed: bool
    logic_score: float
    semantic_score: float
    entropy_score: float
    violations: List[str]
    needs_review: bool
