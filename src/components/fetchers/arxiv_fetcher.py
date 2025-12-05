"""
arXiv Fetcher - Academic Papers and Research
Production-grade academic literature search
"""

import xml.etree.ElementTree as ET
from .base_fetcher import BaseFetcher, FetchResult, FetchStatus

class ArxivFetcher(BaseFetcher):
    """
    Fetches academic papers from arXiv.org
    Excellent for: research papers, scientific queries, academic topics
    """

    def _setup(self):
        self.base_url = "http://export.arxiv.org/api/query"

    def fetch(self, query: str) -> FetchResult:
        """Search arXiv for relevant academic papers"""
        try:
            params = {
                'search_query': f'all:{query}',
                'start': 0,
                'max_results': 3,
                'sortBy': 'relevance',
                'sortOrder': 'descending'
            }

            response = self.session.get(self.base_url, params=params, timeout=10)
            response.raise_for_status()

            # Parse XML response
            root = ET.fromstring(response.content)
            ns = {'atom': 'http://www.w3.org/2005/Atom'}

            entries = root.findall('atom:entry', ns)
            if not entries:
                return FetchResult(
                    status=FetchStatus.NOT_FOUND,
                    data={},
                    confidence=0.0
                )

            # Get first (most relevant) entry
            entry = entries[0]
            title = entry.find('atom:title', ns).text.strip()
            summary = entry.find('atom:summary', ns).text.strip()
            published = entry.find('atom:published', ns).text[:10]
            link = entry.find('atom:id', ns).text

            authors = [author.find('atom:name', ns).text
                      for author in entry.findall('atom:author', ns)]

            clean_summary = self._clean_text(summary, max_length=300)

            return FetchResult(
                status=FetchStatus.FOUND,
                data={
                    "title": title,
                    "authors": authors,
                    "published": published,
                    "abstract": summary
                },
                summary=f"{title} ({published}): {clean_summary}",
                confidence=0.85,
                source="arxiv",
                url=link
            )

        except Exception as e:
            return FetchResult(
                status=FetchStatus.ERROR,
                data={},
                error=str(e),
                confidence=0.0
            )
