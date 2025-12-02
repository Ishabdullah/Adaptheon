from .logic_verifier import LogicVerifier
from .semantic_verifier import SemanticVerifier
from .base import VerificationResult

class CompositeVerifier:
    """Combines all verification layers"""
    def __init__(self, memory):
        self.logic = LogicVerifier(memory)
        self.semantic = SemanticVerifier()
        
        # Weights for ensemble
        self.weights = {
            'logic': 0.45,
            'semantic': 0.55
        }
    
    def verify(self, answer, citations, context):
        """Run all verifiers and combine scores"""
        
        logic_result = self.logic.verify(answer, citations, context)
        semantic_result = self.semantic.verify(answer, citations, context)
        
        # Weighted average
        final_confidence = (
            logic_result.confidence * self.weights['logic'] +
            semantic_result.confidence * self.weights['semantic']
        )
        
        all_violations = logic_result.violations + semantic_result.violations
        
        return VerificationResult(
            confidence=final_confidence,
            passed=final_confidence > 0.65,
            logic_score=logic_result.confidence,
            semantic_score=semantic_result.confidence,
            entropy_score=0.0,  # Phase 3
            violations=all_violations,
            needs_review=final_confidence < 0.50 or len(all_violations) > 2
        )
