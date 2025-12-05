import os
import json

from components.fetchers.fetcher_registry import FetcherRegistry
from components.fetchers.base_fetcher import FetchStatus


class KnowledgeScout:
    """
    Curiosity engine - Enhanced with Production-Grade Fetchers.
    Uses cache + comprehensive domain-specific fetchers
    to fill in missing knowledge and feed semantic memory.
    """

    def __init__(self):
        print("  [Scout] Initializing production-grade fetcher registry...")
        self.cache_path = "data/cache/knowledge_cache.json"
        self._load_cache()
        # Use the new FetcherRegistry with 24+ domain-specific fetchers
        self.registry = FetcherRegistry()
        print(f"  [Scout] {self.registry.get_stats()['total_fetchers']} fetchers registered")

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
        """
        Search for knowledge using intelligent fetcher routing.
        Returns best result from cache or production-grade fetchers.
        """
        q_key = query.strip().lower()

        # Check cache first
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
        print(f"    [Scout] Routing query to specialized fetchers...")

        # Use FetcherRegistry to intelligently route and fetch
        # Registry returns up to 3 most relevant fetchers
        max_fetchers = 3
        if policy and policy.get("max_fetchers"):
            max_fetchers = policy["max_fetchers"]

        results = self.registry.fetch(query, max_fetchers=max_fetchers)

        # Filter by policy if specified
        if policy and policy.get("require_numeric"):
            results = [r for r in results if any(ch.isdigit() for ch in r.summary)]

        # Apply source preference bonus
        if policy and policy.get("prefer_source"):
            preferred = policy["prefer_source"]
            for result in results:
                if result.source in preferred:
                    result.confidence += 0.1

        if not results:
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

        # Get best result (already sorted by confidence in registry)
        best = results[0]

        # Cache the result
        self.cache[q_key] = {
            "summary": best.summary,
            "source": best.source,
            "confidence": best.confidence,
            "url": best.url,
        }
        self._save_cache()

        print(f"    [Scout] ✓ Found via {best.source} (confidence: {best.confidence:.2f})")

        return {
            "status": "FOUND",
            "summary": best.summary,
            "source": best.source,
            "confidence": best.confidence,
            "url": best.url,
        }
