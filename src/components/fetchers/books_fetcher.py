import requests
from typing import Dict, Any, Optional, List


class BooksFetcher:
    """
    Books / literature domain fetcher.
    Uses OpenLibrary search + works API to answer book/author questions.
    """

    def __init__(self):
        self.base = "https://openlibrary.org"

    def _search(self, query: str, limit: int = 3) -> Optional[List[Dict[str, Any]]]:
        url = self.base + "/search.json"
        params = {"q": query, "limit": limit}
        try:
            resp = requests.get(url, params=params, timeout=10)
        except Exception:
            return None
        if resp.status_code != 200:
            return None
        try:
            data = resp.json()
        except Exception:
            return None
        docs = data.get("docs") or []
        return docs[:limit]

    def _format_result(self, docs: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
        if not docs:
            return None
        d = docs[0]
        title = d.get("title") or ""
        authors = d.get("author_name") or []
        author_part = ""
        if authors:
            author_part = " by " + ", ".join(authors)
        year = d.get("first_publish_year")
        year_part = (" (" + str(year) + ")") if year else ""
        subjects = d.get("subject") or []
        subject_part = ""
        if subjects:
            subject_part = " Subjects include: " + ", ".join(subjects[:5]) + "."
        key = d.get("key")  # e.g., "/works/OL12345W"
        url = self.base + key if key else None
        summary = title + author_part + year_part + "." + subject_part
        return {
            "status": "FOUND",
            "summary": summary,
            "confidence": 0.85,
            "url": url,
            "metadata": {
                "source": "openlibrary",
                "work_key": key,
                "authors": authors,
                "year": year,
            },
        }

    def fetch(self, query: str) -> Dict[str, Any]:
        docs = self._search(query, limit=3)
        formatted = self._format_result(docs or [])
        if formatted:
            return formatted
        return {
            "status": "NOT_FOUND",
            "summary": "",
            "confidence": 0.0,
            "url": None,
            "metadata": {},
        }
