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

    def _fetch_sports_priority(self, query: str):
        """
        Sports-specific fetch with prioritized routing and source quality ranking.

        Priority order (MUST be respected, don't just pick highest confidence):
        1. TheSportsDB/ESPN (authoritative sports APIs)
        2. Wikipedia/DBpedia (structured general knowledge)
        3. NewsAPI (sports news)
        4. Reddit (social discussion - LOWEST priority, never for roster/identity queries)

        Roster queries (who is quarterback, coach, etc.) NEVER use social media.
        """
        query_lower = query.lower()

        # Detect query type for source filtering
        is_roster_query = any(keyword in query_lower for keyword in [
            "quarterback", "qb", "coach", "pitcher", "player", "goalie",
            "who is", "who's the", "starting", "roster"
        ])

        # Tier 1: Sports APIs (always try first for roster queries)
        tier1_sources = ['thesportsdb']

        for source in tier1_sources:
            fetcher = self.registry.get_fetcher(source)
            if fetcher:
                try:
                    result = fetcher.fetch(query)
                    if result.status == FetchStatus.FOUND:
                        # For roster queries, accept TheSportsDB even with low confidence
                        # (it provides team info even if roster data limited)
                        print(f"    [Scout] ✓ Sports API result from {source} (confidence: {result.confidence:.2f})")
                        return [result]
                except Exception as e:
                    print(f"    [Scout] ⚠ Error in {source}: {e}")

        # Tier 2: Structured knowledge bases (good for general facts)
        tier2_sources = ['wikidata', 'dbpedia']

        if not is_roster_query:  # Only for non-roster queries
            for source in tier2_sources:
                fetcher = self.registry.get_fetcher(source)
                if fetcher:
                    try:
                        result = fetcher.fetch(query)
                        if result.status == FetchStatus.FOUND and result.confidence >= 0.6:
                            print(f"    [Scout] ✓ Knowledge base result from {source}")
                            return [result]
                    except Exception as e:
                        print(f"    [Scout] ⚠ Error in {source}: {e}")

        # Tier 3: News (only for recent events, not roster queries)
        tier3_sources = ['newsapi']

        if not is_roster_query:
            for source in tier3_sources:
                fetcher = self.registry.get_fetcher(source)
                if fetcher:
                    try:
                        result = fetcher.fetch(query)
                        if result.status == FetchStatus.FOUND and result.confidence >= 0.5:
                            print(f"    [Scout] ✓ News result from {source}")
                            return [result]
                    except Exception as e:
                        print(f"    [Scout] ⚠ Error in {source}: {e}")

        # Tier 4: Social media (LOWEST priority, NEVER for roster queries)
        # Explicitly reject Reddit for roster/identity queries
        if is_roster_query:
            print(f"    [Scout] ⚠ Roster query failed - sports APIs did not return data")
            print(f"    [Scout] → Refusing to use Reddit/social for identity questions")
            return []

        # For non-roster queries, Reddit might be okay for trending topics
        tier4_sources = ['reddit']

        for source in tier4_sources:
            fetcher = self.registry.get_fetcher(source)
            if fetcher:
                try:
                    result = fetcher.fetch(query)
                    if result.status == FetchStatus.FOUND and result.confidence >= 0.7:
                        # Additional validation: summary should mention key query terms
                        summary_lower = result.summary.lower()
                        query_keywords = [w for w in query_lower.split() if len(w) > 3]
                        matches = sum(1 for kw in query_keywords if kw in summary_lower)

                        if matches >= 2:  # At least 2 query keywords in result
                            print(f"    [Scout] ✓ Social result from {source} (validated)")
                            return [result]
                        else:
                            print(f"    [Scout] ✗ Rejected {source} - low relevance")
                except Exception as e:
                    print(f"    [Scout] ⚠ Error in {source}: {e}")

        print(f"    [Scout] ✗ All sports sources failed for query")
        return []

    def _fetch_news_priority(self, query: str):
        """
        News-specific fetch with prioritized routing.

        Priority order:
        1. NewsAPI (RSS from Reuters, AP, Google News)
        2. Reddit (for trending topics - if relevant)
        3. Wikipedia/DBpedia (for background context)
        """
        query_lower = query.lower()

        # Tier 1: News APIs (always try first)
        tier1_sources = ['newsapi']

        for source in tier1_sources:
            fetcher = self.registry.get_fetcher(source)
            if fetcher:
                try:
                    result = fetcher.fetch(query)
                    if result.status == FetchStatus.FOUND:
                        print(f"    [Scout] ✓ News result from {source} (confidence: {result.confidence:.2f})")
                        return [result]
                except Exception as e:
                    print(f"    [Scout] ⚠ Error in {source}: {e}")

        # Tier 2: Reddit (only for topic-specific news, not generic "latest news")
        is_generic_news = any(phrase in query_lower for phrase in [
            "latest news", "breaking news", "top news", "current news", "headlines"
        ])

        if not is_generic_news:
            tier2_sources = ['reddit']

            for source in tier2_sources:
                fetcher = self.registry.get_fetcher(source)
                if fetcher:
                    try:
                        result = fetcher.fetch(query)
                        if result.status == FetchStatus.FOUND and result.confidence >= 0.7:
                            # Validate relevance
                            summary_lower = result.summary.lower()
                            query_keywords = [w for w in query_lower.split() if len(w) > 3]
                            matches = sum(1 for kw in query_keywords if kw in summary_lower)

                            if matches >= 2:
                                print(f"    [Scout] ✓ Social news result from {source}")
                                return [result]
                            else:
                                print(f"    [Scout] ✗ Rejected {source} - low relevance")
                    except Exception as e:
                        print(f"    [Scout] ⚠ Error in {source}: {e}")

        # Tier 3: Knowledge bases (for context on news topics)
        tier3_sources = ['wikidata', 'dbpedia']

        if not is_generic_news:
            for source in tier3_sources:
                fetcher = self.registry.get_fetcher(source)
                if fetcher:
                    try:
                        result = fetcher.fetch(query)
                        if result.status == FetchStatus.FOUND and result.confidence >= 0.6:
                            print(f"    [Scout] ✓ Background context from {source}")
                            return [result]
                    except Exception as e:
                        print(f"    [Scout] ⚠ Error in {source}: {e}")

        print(f"    [Scout] ✗ All news sources failed for query")
        return []

    def search(self, query: str, policy: dict = None, ignore_cache: bool = False, domain: str = None):
        """
        Search for knowledge using intelligent fetcher routing.
        Returns best result from cache or production-grade fetchers.

        Args:
            query: Search query string
            policy: Optional search policy with preferences
            ignore_cache: If True, bypass cache and fetch fresh data (for time-sensitive queries)
            domain: Optional domain hint (e.g., "sports", "finance", "weather") for prioritized routing
        """
        q_key = query.strip().lower()

        # Check cache first (unless explicitly told to ignore it for time-sensitive queries)
        if not ignore_cache and q_key in self.cache:
            print("    [Cache] ✓ Hit: '{}'".format(q_key))
            entry = self.cache[q_key]
            return {
                "status": "FOUND",
                "summary": entry.get("summary", ""),
                "source": entry.get("source", "unknown"),
                "confidence": entry.get("confidence", 0.7),
                "url": entry.get("url"),
            }

        if ignore_cache and q_key in self.cache:
            print("    [Cache] ⏰ Bypassing cache for time-sensitive query: '{}'".format(q_key))
        else:
            print("    [Cache] ✗ Miss: '{}'".format(q_key))

        # SPORTS FAST PATH: Prioritize TheSportsDB for sports queries
        if domain == "sports":
            print("    [Scout] ⚽ Sports domain detected - prioritizing TheSportsDB...")
            results = self._fetch_sports_priority(query)
        # NEWS FAST PATH: Prioritize NewsAPI for news queries
        elif domain == "news":
            print("    [Scout] 📰 News domain detected - prioritizing NewsAPI...")
            results = self._fetch_news_priority(query)
        else:
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
