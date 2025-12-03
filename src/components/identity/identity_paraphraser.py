from typing import Optional


class IdentityParaphraser:
    """
    Uses the existing LanguageSystem instance to paraphrase canonical identity answers.
    Keeps meaning fixed, wording slightly varied.
    """

    def __init__(self, llm):
        self.llm = llm

    def paraphrase(self, slot_id: str, base_text: str) -> str:
        """
        Given a canonical identity slot and base text, return a short paraphrase.
        If LLM is unavailable, return the base text directly.
        """
        if not getattr(self.llm, "use_llm", False):
            return base_text

        prompt = (
            "You are Adaptheon, a modular AI truth engine. "
            "Paraphrase the following description about yourself in 1 to 3 sentences. "
            "Keep the meaning and claims exactly the same. "
            "Do not add new capabilities or speculate. "
            "Text: " + base_text + " Answer:"
        )

        # Call low-level LLM to avoid extra Question/Answer wrappers
        raw_output = self.llm._call_llm(prompt, max_tokens=160, temperature=0.4)  # type: ignore[attr-defined]

        if "Answer:" in raw_output:
            answer_part = raw_output.split("Answer:", 1)[1].strip()
        else:
            answer_part = raw_output.strip()

        if not answer_part:
            return base_text

        return answer_part
