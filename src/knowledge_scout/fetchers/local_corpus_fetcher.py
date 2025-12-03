import os
import re
from typing import Optional
from .base import BaseFetcher, FetchResult, FetchSource

WORD_RE = re.compile(r"w+")

class LocalCorpusFetcher(BaseFetcher):
    """
    Searches local .txt files under data/corpus/ for relevant content.
    Good for: your own notes, curated explanations, offline docs.
    """

    def __init__(self, base_dir="data/corpus"):
        self.base_dir = base_dir

    def _score(self, text: str, query: str) -> float:
        text_lower = text.lower()
        score = 0.0
        for token in WORD_RE.findall(query.lower()):
            if token in text_lower:
                score += 1.0
        return score

    def fetch(self, query: str) -> Optional[FetchResult]:
        if not os.path.isdir(self.base_dir):
            return None

        best_path = None
        best_snippet = None
        best_score = 0.0

        for name in os.listdir(self.base_dir):
            if not name.endswith(".txt"):
                continue
            path = os.path.join(self.base_dir, name)
            try:
                with open(path, "r", encoding="utf-8", errors="ignore") as f:
                    text = f.read()
            except Exception:
                continue

            score = self._score(text, query)
            if score <= best_score:
                continue

            # Take first ~500 chars as summary, join lines with spaces
            flat = " ".join(text.splitlines()).strip()
            if len(flat) > 500:
                flat = flat[:500].rstrip() + "..."
            best_path = path
            best_snippet = flat
            best_score = score

        if not best_snippet:
            return None

        print("    [LocalCorpus] ✓ Hit in {}".format(os.path.basename(best_path)))
        confidence = min(0.9, 0.4 + 0.05 * best_score)

        return FetchResult(
            query=query,
            summary=best_snippet,
            source=FetchSource.LOCAL_CORPUS,
            confidence=confidence,
            url=best_path,
        )
