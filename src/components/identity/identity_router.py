import json
import os
from typing import Optional, Dict, Any, List

from components.semantic_utils import text_to_vector, cosine_similarity


class IdentityRouter:
    """
    Maps free-form user questions to canonical identity slots using:
      - string pattern matching
      - simple semantic similarity between query and canonical questions,
    but only when the question clearly refers to the assistant (you/your/Adaptheon).
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

    def _targets_assistant(self, q_lower: str) -> bool:
        """
        Return True only if the question is clearly about the assistant's identity or role.
        """
        if "adaptheon" in q_lower:
            return True
        pronouns = ["who are you", "what are you", "what is your purpose", "your purpose", "you do", "your limitations", "your limits", "how do you work", "how do you function", "how do you operate", "where does your knowledge come from", "where do you get your information"]
        for p in pronouns:
            if p in q_lower:
                return True
        # Generic "you" + a verb, but only if it doesn't contain clear third-party entities/teams
        if "you" in q_lower or "your" in q_lower or "yourself" in q_lower:
            # Heuristic: if it also clearly mentions sports teams, treat as non-identity
            sports_tokens = ["giants", "patriots", "jets", "cowboys", "eagles", "nfl", "nba", "mlb", "premier league"]
            if any(tok in q_lower for tok in sports_tokens):
                return False
            return True
        return False

    def route(self, query: str) -> Optional[str]:
        """
        Return canonical slot id (e.g., 'who_are_you') if this is an identity-style question,
        otherwise None.
        """
        if not self.patterns:
            return None

        q_lower = query.lower().strip()

        # Only proceed if the question clearly targets the assistant
        if not self._targets_assistant(q_lower):
            return None

        # Explicitly let "what can you do" style questions go to normal capability handling
        capability_phrases = [
            "what can you do",
            "what are you capable of",
            "what can u do",
            "what do you do for me",
            "how can you help me",
        ]
        for phrase in capability_phrases:
            if phrase in q_lower:
                return None

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

        # Require a decent similarity, but only after assistant-targeting check
        if best_id is not None and best_score >= 0.12:
            return best_id

        return None
