import requests
from typing import Dict, Any, Optional, List


class ScienceFetcher:
    """
    Science / academic domain fetcher.
    Uses Semantic Scholar for paper search and arXiv as fallback.
    """

    def __init__(self):
        self.semantic_base = "https://api.semanticscholar.org/graph/v1/paper/search"
        self.arxiv_base = "http://export.arxiv.org/api/query"

    def _semantic_scholar_search(self, query: str, limit: int = 3) -> Optional[List[Dict[str, Any]]]:
        params = {
            "query": query,
            "limit": limit,
            "fields": "title,abstract,year,authors,url,isOpenAccess"
        }
        try:
            resp = requests.get(self.semantic_base, params=params, timeout=10)
        except Exception:
            return None
        if resp.status_code != 200:
            return None
        try:
            data = resp.json()
        except Exception:
            return None
        return data.get("data") or []

    def _format_semantic_result(self, papers: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
        if not papers:
            return None
        p = papers[0]
        title = p.get("title") or ""
        abstract = p.get("abstract") or ""
        year = p.get("year")
        url = p.get("url")
        authors = p.get("authors") or []
        auth_names = [a.get("name") for a in authors if a.get("name")]
        author_part = ""
        if auth_names:
            author_part = " by " + ", ".join(auth_names)
        year_part = (" (" + str(year) + ")") if year else ""
        summary = title + author_part + year_part + ". " + abstract
        return {
            "status": "FOUND",
            "summary": summary,
            "confidence": 0.9,
            "url": url,
            "metadata": {
                "source": "semantic_scholar",
                "paper_id": p.get("paperId"),
                "year": year,
            },
        }

    def _arxiv_search(self, query: str, max_results: int = 3) -> Optional[str]:
        params = {
            "search_query": "all:" + query,
            "start": 0,
            "max_results": max_results,
        }
        try:
            resp = requests.get(self.arxiv_base, params=params, timeout=10)
        except Exception:
            return None
        if resp.status_code != 200:
            return None
        try:
            text = resp.text
        except Exception:
            return None
        # Very simple extraction: take first <entry><title> and <summary>
        title = None
        summary = None
        t_start = text.find("<entry>")
        if t_start == -1:
            return None
        seg = text[t_start:]
        t1 = seg.find("<title>")
        t2 = seg.find("</title>")
        s1 = seg.find("<summary>")
        s2 = seg.find("</summary>")
        if t1 != -1 and t2 != -1:
            title = seg[t1 + len("<title>"):t2].strip()
        if s1 != -1 and s2 != -1:
            summary = seg[s1 + len("<summary>"):s2].strip()
        if not title and not summary:
            return None
        combined = ""
        if title:
            combined += title.strip() + ". "
        if summary:
            combined += summary.strip()
        return combined or None

    def fetch(self, query: str) -> Dict[str, Any]:
        """
        High-level fetch for research-style questions.
        """
        # Try Semantic Scholar
        papers = self._semantic_scholar_search(query, limit=3)
        formatted = self._format_semantic_result(papers or [])
        if formatted:
            return formatted

        # Fallback: arXiv
        arxiv_summary = self._arxiv_search(query, max_results=3)
        if arxiv_summary:
            return {
                "status": "FOUND",
                "summary": arxiv_summary,
                "confidence": 0.7,
                "url": None,
                "metadata": {
                    "source": "arxiv",
                },
            }

        return {
            "status": "NOT_FOUND",
            "summary": "",
            "confidence": 0.0,
            "url": None,
            "metadata": {},
        }
