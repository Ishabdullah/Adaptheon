import os
import json
from typing import Optional, Dict, Any, List

from components.domain_router import DomainRouter
from components.fetchers.sports_fetcher import SportsFetcher
from components.fetchers.science_fetcher import ScienceFetcher
from components.fetchers.books_fetcher import BooksFetcher
from knowledge_scout.truth_types import (
    TruthResult,
    SourceTier,
    SourceKind,
    SourceTraceEntry,
)
from knowledge_scout.wikidata_client import WikidataClient
from knowledge_scout.fetchers.wikipedia_fetcher import WikipediaFetcher
from knowledge_scout.fetchers.rss_fetcher import RSSFetcher
from knowledge_scout.fetchers.local_corpus_fetcher import LocalCorpusFetcher


class KnowledgeScout:
    """
    Truth engine / curiosity engine.
    Tiered, structured retrieval with Wikidata as primary, Wikipedia/RSS/Local as fallbacks.
    Domain-aware via DomainRouter, with domain-specific fast paths (sports, science, books) and
    a guard against hallucinated sports winners.
    """

    def __init__(self):
        print("  [Scout] Initializing fetcher layers...")
        self.cache_path = "data/cache/knowledge_cache.json"
        self.unknowns_path = "data/cache/unknowns.json"
        self._load_cache()
        self.domain_router = DomainRouter()
        self.sports = SportsFetcher()
        self.science = ScienceFetcher()
        self.books = BooksFetcher()
        self.wikidata = WikidataClient()
        self.wikipedia = WikipediaFetcher()
        self.rss = RSSFetcher()
        self.local_corpus = LocalCorpusFetcher()

    def _load_cache(self):
        os.makedirs("data/cache", exist_ok=True)
        if os.path.exists(self.cache_path):
            with open(self.cache_path, "r") as f:
                try:
                    self.cache: Dict[str, Any] = json.load(f)
                except json.JSONDecodeError:
                    self.cache = {}
        else:
            self.cache = {}

        if os.path.exists(self.unknowns_path):
            with open(self.unknowns_path, "r") as f:
                try:
                    self.unknowns: List[Dict[str, Any]] = json.load(f)
                except json.JSONDecodeError:
                    self.unknowns = []
        else:
            self.unknowns = []

    def _save_cache(self):
        with open(self.cache_path, "w") as f:
            json.dump(self.cache, f, indent=2)
        with open(self.unknowns_path, "w") as f:
            json.dump(self.unknowns, f, indent=2)

    def _record_unknown(self, query: str, reason: str):
        entry = {
            "query": query,
            "reason": reason,
        }
        self.unknowns.append(entry)
        self._save_cache()

    def _from_cache(self, q_key: str) -> Optional[TruthResult]:
        entry = self.cache.get(q_key)
        if not entry:
            return None
        return TruthResult(
            status=entry.get("status", "FOUND"),
            query=entry.get("query", q_key),
            canonical_summary=entry.get("canonical_summary", ""),
            confidence=entry.get("confidence", 0.7),
            primary_source=SourceKind(entry.get("primary_source", "wikipedia")),
            tier=SourceTier(entry.get("tier", "secondary")),
            snippets=entry.get("snippets", []),
            source_trace=[
                SourceTraceEntry(
                    tier=SourceTier(t["tier"]),
                    kind=SourceKind(t["kind"]),
                    name=t.get("name", ""),
                    url=t.get("url"),
                    confidence=t.get("confidence", 0.0),
                    note=t.get("note", ""),
                )
                for t in entry.get("source_trace", [])
            ],
            violations=entry.get("violations", []),
            metadata=entry.get("metadata", {}),
        )

    def _to_cache(self, res: TruthResult):
        trace_list = []
        for t in res.source_trace:
            trace_list.append(
                {
                    "tier": t.tier.value,
                    "kind": t.kind.value,
                    "name": t.name,
                    "url": t.url,
                    "confidence": t.confidence,
                    "note": t.note,
                }
            )
        self.cache[res.query.strip().lower()] = {
            "status": res.status,
            "query": res.query,
            "canonical_summary": res.canonical_summary,
            "confidence": res.confidence,
            "primary_source": res.primary_source.value,
            "tier": res.tier.value,
            "snippets": res.snippets,
            "source_trace": trace_list,
            "violations": res.violations,
            "metadata": res.metadata,
        }
        self._save_cache()

    def search(
        self,
        query: str,
        policy: Dict[str, Any] = None,
        ignore_cache: bool = False,
        domain: Optional[str] = None,
        query_type: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Domain-aware search over primary/secondary/tertiary knowledge sources.
        'domain' and 'query_type' are hints from HRM/DomainRouter.
        """
        q_key = query.strip().lower()

        if domain:
            _ = self.domain_router.get_sources(domain)

        # Sports domain fast path
        if domain == "sports" and query_type == "sports_result":
            sports_res = self.sports.fetch_result(query)
            if sports_res.get("status") == "FOUND":
                tr = TruthResult(
                    status="FOUND",
                    query=query,
                    canonical_summary=sports_res["summary"],
                    confidence=sports_res.get("confidence", 0.88),
                    primary_source=SourceKind.OTHER,
                    tier=SourceTier.PRIMARY,
                    snippets=[sports_res["summary"]],
                    source_trace=[
                        SourceTraceEntry(
                            tier=SourceTier.PRIMARY,
                            kind=SourceKind.OTHER,
                            name="SportsAPI",
                            url=sports_res.get("url"),
                            confidence=sports_res.get("confidence", 0.88),
                            note="ESPN/TheSportsDB sports result stack",
                        )
                    ],
                    violations=[],
                    metadata=sports_res.get("metadata", {}),
                )
                self._to_cache(tr)
                return {
                    "status": tr.status,
                    "summary": tr.canonical_summary,
                    "source": tr.primary_source.value,
                    "confidence": tr.confidence,
                    "url": tr.metadata.get("url"),
                    "truth_result": tr,
                }

        # Science/academic fast path
        if domain == "science_academic" and query_type == "paper_search":
            sci_res = self.science.fetch(query)
            if sci_res.get("status") == "FOUND":
                tr = TruthResult(
                    status="FOUND",
                    query=query,
                    canonical_summary=sci_res["summary"],
                    confidence=sci_res.get("confidence", 0.9),
                    primary_source=SourceKind.OTHER,
                    tier=SourceTier.PRIMARY,
                    snippets=[sci_res["summary"]],
                    source_trace=[
                        SourceTraceEntry(
                            tier=SourceTier.PRIMARY,
                            kind=SourceKind.OTHER,
                            name="ScienceAPI",
                            url=sci_res.get("url"),
                            confidence=sci_res.get("confidence", 0.9),
                            note="Semantic Scholar/arXiv science stack",
                        )
                    ],
                    violations=[],
                    metadata=sci_res.get("metadata", {}),
                )
                self._to_cache(tr)
                return {
                    "status": tr.status,
                    "summary": tr.canonical_summary,
                    "source": tr.primary_source.value,
                    "confidence": tr.confidence,
                    "url": tr.metadata.get("url"),
                    "truth_result": tr,
                }

        # Books/literature fast path
        if domain == "books_literature" and query_type == "book_info":
            book_res = self.books.fetch(query)
            if book_res.get("status") == "FOUND":
                tr = TruthResult(
                    status="FOUND",
                    query=query,
                    canonical_summary=book_res["summary"],
                    confidence=book_res.get("confidence", 0.85),
                    primary_source=SourceKind.OTHER,
                    tier=SourceTier.PRIMARY,
                    snippets=[book_res["summary"]],
                    source_trace=[
                        SourceTraceEntry(
                            tier=SourceTier.PRIMARY,
                            kind=SourceKind.OTHER,
                            name="BooksAPI",
                            url=book_res.get("url"),
                            confidence=book_res.get("confidence", 0.85),
                            note="OpenLibrary books stack",
                        )
                    ],
                    violations=[],
                    metadata=book_res.get("metadata", {}),
                )
                self._to_cache(tr)
                return {
                    "status": tr.status,
                    "summary": tr.canonical_summary,
                    "source": tr.primary_source.value,
                    "confidence": tr.confidence,
                    "url": tr.metadata.get("url"),
                    "truth_result": tr,
                }

        if not ignore_cache:
            cached = self._from_cache(q_key)
            if cached:
                print("    [Cache] ✓ Hit: '{}'".format(q_key))
                return {
                    "status": cached.status,
                    "summary": cached.canonical_summary,
                    "source": cached.primary_source.value,
                    "confidence": cached.confidence,
                    "url": cached.metadata.get("entity_iri") or None,
                    "truth_result": cached,
                }
            else:
                print("    [Cache] ✗ Miss: '{}'".format(q_key))
        else:
            print("    [Cache] ↷ Bypassing cache for time-sensitive query '{}'".format(q_key))

        # Tier 1: Wikidata (structured)
        primary = self.wikidata.lookup_entity(query)
        if primary:
            self._to_cache(primary)
            return {
                "status": "FOUND",
                "summary": primary.canonical_summary,
                "source": primary.primary_source.value,
                "confidence": primary.confidence,
                "url": primary.metadata.get("entity_iri"),
                "truth_result": primary,
            }

        # Tier 2: Local corpus + Wikipedia
        local_result = self.local_corpus.fetch(query)
        wiki_result = self.wikipedia.fetch(query)
        rss_result = self.rss.fetch(query)

        candidates: List[TruthResult] = []
        if local_result is not None:
            tr = TruthResult(
                status="FOUND",
                query=query,
                canonical_summary=local_result.summary,
                confidence=local_result.confidence + 0.05,
                primary_source=SourceKind.LOCAL_CORPUS,
                tier=SourceTier.SECONDARY,
                snippets=[local_result.summary],
                source_trace=[
                    SourceTraceEntry(
                        tier=SourceTier.SECONDARY,
                        kind=SourceKind.LOCAL_CORPUS,
                        name="LocalCorpus",
                        url=None,
                        confidence=local_result.confidence,
                        note="Local text corpus",
                    )
                ],
                violations=[],
                metadata={"path": getattr(local_result, "path", None)},
            )
            candidates.append(tr)

        if wiki_result is not None:
            tr = TruthResult(
                status="FOUND",
                query=query,
                canonical_summary=wiki_result.summary,
                confidence=wiki_result.confidence + 0.05,
                primary_source=SourceKind.WIKIPEDIA,
                tier=SourceTier.SECONDARY,
                snippets=[wiki_result.summary],
                source_trace=[
                    SourceTraceEntry(
                        tier=SourceTier.SECONDARY,
                        kind=SourceKind.WIKIPEDIA,
                        name="Wikipedia",
                        url=wiki_result.url,
                        confidence=wiki_result.confidence,
                        note="Wikipedia extract",
                    )
                ],
                violations=[],
                metadata={"url": wiki_result.url},
            )
            candidates.append(tr)

        # Tier 3: RSS/news as last resort
        if rss_result is not None:
            tr = TruthResult(
                status="FOUND",
                query=query,
                canonical_summary=rss_result.summary,
                confidence=rss_result.confidence,
                primary_source=SourceKind.NEWS_RSS,
                tier=SourceTier.TERTIARY,
                snippets=[rss_result.summary],
                source_trace=[
                    SourceTraceEntry(
                        tier=SourceTier.TERTIARY,
                        kind=SourceKind.NEWS_RSS,
                        name="RSS",
                        url=rss_result.url,
                        confidence=rss_result.confidence,
                        note="News RSS snippet",
                    )
                ],
                violations=[],
                metadata={"url": rss_result.url},
            )
            candidates.append(tr)

        # Apply simple numeric policy filter if needed
        if policy and candidates:
            if policy.get("require_numeric"):
                filtered: List[TruthResult] = []
                for r in candidates:
                    if any(ch.isdigit() for ch in r.canonical_summary):
                        filtered.append(r)
                if filtered:
                    candidates = filtered

        # Sports safety guard: do not hallucinate winners from generic news
        if candidates:
            lower_q = q_key
            sports_like = ("who won" in lower_q) or ("score of" in lower_q) or ("giants" in lower_q) or ("nfl" in lower_q)
            only_news = all(r.primary_source == SourceKind.NEWS_RSS for r in candidates)
            if sports_like and only_news:
                self._record_unknown(query, "Only NEWS_RSS candidates for sports-like query")
                candidates = []

        if not candidates:
            self._record_unknown(query, "No candidates from Wikidata/Wikipedia/RSS/Local")
            not_found = TruthResult(
                status="NOT_FOUND",
                query=query,
                canonical_summary="I could not find reliable information about '{}' yet.".format(query),
                confidence=0.0,
                primary_source=SourceKind.OTHER,
                tier=SourceTier.TERTIARY,
                snippets=[],
                source_trace=[],
                violations=["NO_CANDIDATES"],
                metadata={},
            )
            self._to_cache(not_found)
            return {
                "status": "NOT_FOUND",
                "summary": not_found.canonical_summary,
                "source": not_found.primary_source.value,
                "confidence": not_found.confidence,
                "url": None,
                "truth_result": not_found,
            }

        best = sorted(candidates, key=lambda r: r.confidence, reverse=True)[0]
        self._to_cache(best)

        return {
            "status": "FOUND",
            "summary": best.canonical_summary,
            "source": best.primary_source.value,
            "confidence": best.confidence,
            "url": best.metadata.get("url") or best.metadata.get("entity_iri"),
            "truth_result": best,
        }
