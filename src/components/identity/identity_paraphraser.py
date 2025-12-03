from typing import Optional


class IdentityParaphraser:
    """
    Uses the existing LanguageSystem instance to paraphrase canonical identity answers.
    Keeps meaning fixed, wording slightly varied, and limits length to 1–3 sentences.
    """

    def __init__(self, llm):
        self.llm = llm

    def _limit_sentences(self, text: str, max_sentences: int = 3) -> str:
        if not text:
            return text
        # Normalize sentence boundaries
        tmp = text.replace("?", ".").replace("!", ".")
        parts = [s.strip() for s in tmp.split(".") if s.strip()]
        if not parts:
            return text.strip()
        kept = parts[:max_sentences]
        out = ". ".join(kept).strip()
        if not out.endswith("."):
            out = out + "."
        return out

    def paraphrase(self, slot_id: str, base_text: str) -> str:
        """
        Given a canonical identity slot and base text, return a short paraphrase.
        If LLM is unavailable, return the base text directly.
        """
        if not getattr(self.llm, "use_llm", False):
            return self._limit_sentences(base_text, max_sentences=3)

        prompt = (
            "You are Adaptheon, a modular AI truth engine. "
            "Paraphrase the following description about yourself in 1 to 3 sentences. "
            "Keep the meaning and claims exactly the same. "
            "Do not add new capabilities or speculate. "
            "Text: " + base_text + " Answer:"
        )

        # Call low-level LLM to avoid extra wrappers; allow enough tokens, then trim.
        raw_output = self.llm._call_llm(prompt, max_tokens=220, temperature=0.4)  # type: ignore[attr-defined]

        if "Answer:" in raw_output:
            answer_part = raw_output.split("Answer:", 1)[1].strip()
        else:
            answer_part = raw_output.strip()

        if not answer_part:
            return self._limit_sentences(base_text, max_sentences=3)

        return self._limit_sentences(answer_part, max_sentences=3)
