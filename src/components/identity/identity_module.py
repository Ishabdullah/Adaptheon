from typing import Dict, Any

from .identity_canon import IDENTITY_CANON
from .identity_router import IdentityRouter
from .identity_paraphraser import IdentityParaphraser


class IdentityModule:
    """
    Handles Adaptheon identity/purpose/self-description questions.
    """

    def __init__(self, llm):
        self.router = IdentityRouter()
        self.paraphraser = IdentityParaphraser(llm)

    def handle(self, query: str) -> Dict[str, Any]:
        """
        Returns:
          {"handled": bool, "response": str}
        If handled is False, Meta-Core should fall back to normal routing.
        """
        slot_id = self.router.route(query)
        if not slot_id:
            return {"handled": False, "response": ""}

        entry = IDENTITY_CANON.get(slot_id)
        if not entry:
            return {"handled": False, "response": ""}

        base_text = entry.get("base", "")
        if not base_text:
            return {"handled": False, "response": ""}

        resp = self.paraphraser.paraphrase(slot_id, base_text)
        return {"handled": True, "response": resp}
