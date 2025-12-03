import json
import os
from typing import Optional, Dict, Any, List

from components.semantic_utils import text_to_vector, cosine_similarity


class IdentityRouter:
    """
    Maps free-form user questions to canonical identity slots using:
      - string pattern matching
      - simple semantic similarity between query and canonical questions.
    """

    def __init__(self, patterns_path: str = "src/components/identity/identity_patterns.json"):
        self.patterns: List[Dict[str, Any]] = []
        self._load_patterns(patterns_path)

    def _load_patterns(self, path: str):
        full = os.path.expanduser(path)
        if not os.path.exists(full):
            return
        with open(full, "r") as f:
            self.patterns = json.load(f)

    def route(self, query: str) -> Optional[str]:
        """
        Return canonical slot id (e.g., 'who_are_you') if this is an identity-style question,
        otherwise None.
        """
        if not self.patterns:
            return None

        q_lower = query.lower().strip()

        # 1) Direct pattern substring match
        for entry in self.patterns:
            slot_id = entry.get("id")
            pats = entry.get("patterns", [])
            for p in pats:
                if p in q_lower:
                    return slot_id

        # 2) Semantic similarity with canonical_question field
        best_id: Optional[str] = None
        best_score = 0.0
        q_vec = text_to_vector(q_lower)

        for entry in self.patterns:
            slot_id = entry.get("id")
            canon_q = entry.get("canonical_question", "")
            if not slot_id or not canon_q:
                continue
            canon_vec = text_to_vector(canon_q.lower())
            score = cosine_similarity(q_vec, canon_vec)
            if score > best_score:
                best_score = score
                best_id = slot_id

        # Require a small minimum similarity to avoid false positives
        if best_id is not None and best_score >= 0.12:
            return best_id

        return None
