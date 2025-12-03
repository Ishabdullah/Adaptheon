import os
import json

from knowledge_scout.fetchers.base import FetchSource
from knowledge_scout.fetchers.wikipedia_fetcher import WikipediaFetcher
from knowledge_scout.fetchers.rss_fetcher import RSSFetcher
from knowledge_scout.fetchers.local_corpus_fetcher import LocalCorpusFetcher


class KnowledgeScout:
    """
    Curiosity engine.
    Uses cache + local corpus + web sources (Wikipedia, RSS)
    to fill in missing knowledge and feed semantic memory.
    """

    def __init__(self):
        print("  [Scout] Initializing fetcher layers...")
        self.cache_path = "data/cache/knowledge_cache.json"
        self._load_cache()
        self.wikipedia = WikipediaFetcher()
        self.rss = RSSFetcher()
        self.local_corpus = LocalCorpusFetcher()

    def _load_cache(self):
        os.makedirs("data/cache", exist_ok=True)
        if os.path.exists(self.cache_path):
            with open(self.cache_path, "r") as f:
                try:
                    self.cache = json.load(f)
                except json.JSONDecodeError:
                    self.cache = {}
        else:
            self.cache = {}

    def _save_cache(self):
        with open(self.cache_path, "w") as f:
            json.dump(self.cache, f, indent=2)

    def search(self, query: str, policy: dict = None):
        q_key = query.strip().lower()

        if q_key in self.cache:
            print("    [Cache] ✓ Hit: '{}'".format(q_key))
            entry = self.cache[q_key]
            return {
                "status": "FOUND",
                "summary": entry.get("summary", ""),
                "source": entry.get("source", "unknown"),
                "confidence": entry.get("confidence", 0.7),
                "url": entry.get("url"),
            }

        print("    [Cache] ✗ Miss: '{}'".format(q_key))

        local_result = self.local_corpus.fetch(query)
        wiki_result = self.wikipedia.fetch(query)
        rss_result = self.rss.fetch(query)

        candidates = [r for r in [local_result, wiki_result, rss_result] if r is not None]

        # Apply simple policy filters before scoring
        if policy:
            require_numeric = bool(policy.get("require_numeric", False))
            if require_numeric:
                filtered = []
                for r in candidates:
                    if any(ch.isdigit() for ch in r.summary):
                        filtered.append(r)
                if filtered:
                    candidates = filtered

        if not candidates:
            self.cache[q_key] = {
                "summary": "I could not find reliable information about '{}' yet.".format(query),
                "source": "none",
                "confidence": 0.0,
                "url": None,
            }
            self._save_cache()
            return {
                "status": "NOT_FOUND",
                "summary": self.cache[q_key]["summary"],
                "source": "none",
                "confidence": 0.0,
                "url": None,
            }

        def score(r):
            bonus = 0.0
            # Prefer local corpus slightly
            if r.source == FetchSource.LOCAL_CORPUS:
                bonus += 0.05
            # Policy-based source preference
            if policy:
                prefer_src = policy.get("prefer_source")
                if prefer_src and isinstance(prefer_src, list):
                    src_val = r.source.value if hasattr(r.source, "value") else str(r.source)
                    if src_val in prefer_src:
                        bonus += 0.1
            return r.confidence + bonus

        best = sorted(candidates, key=score, reverse=True)[0]
        source_value = best.source.value if hasattr(best.source, "value") else str(best.source)

        self.cache[q_key] = {
            "summary": best.summary,
            "source": source_value,
            "confidence": best.confidence,
            "url": best.url,
        }
        self._save_cache()

        return {
            "status": "FOUND",
            "summary": best.summary,
            "source": source_value,
            "confidence": best.confidence,
            "url": best.url,
        }
