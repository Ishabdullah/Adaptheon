from typing import Optional


class IdentityParaphraser:
    """
    Uses the existing LanguageSystem instance to paraphrase canonical identity answers.
    Keeps meaning fixed, wording slightly varied, and limits length to 1–3 non-redundant sentences.
    """

    def __init__(self, llm):
        self.llm = llm

    def _split_sentences(self, text: str):
        text = text.replace("?", ".").replace("!", ".")
        parts = [s.strip() for s in text.split(".") if s.strip()]
        return parts

    def _limit_and_dedupe(self, text: str, max_sentences: int = 3) -> str:
        if not text:
            return text
        parts = self._split_sentences(text)
        if not parts:
            return text.strip()

        seen = set()
        kept = []
        for s in parts:
            key = s.lower().strip()
            if key in seen:
                continue
            seen.add(key)
            kept.append(s)
            if len(kept) >= max_sentences:
                break

        if not kept:
            return text.strip()

        out = ". ".join(kept).strip()
        if not out.endswith("."):
            out = out + "."
        return out

    def paraphrase(self, slot_id: str, base_text: str) -> str:
        """
        Given a canonical identity slot and base text, return a short paraphrase.
        If LLM is unavailable, return a trimmed, deduplicated version of the base text.
        """
        if not getattr(self.llm, "use_llm", False):
            return self._limit_and_dedupe(base_text, max_sentences=3)

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
            return self._limit_and_dedupe(base_text, max_sentences=3)

        return self._limit_and_dedupe(answer_part, max_sentences=3)
