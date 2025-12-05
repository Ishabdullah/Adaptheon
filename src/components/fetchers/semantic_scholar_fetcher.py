"""
Semantic Scholar Fetcher - Academic Research Papers
Production-grade AI-powered academic search
"""

from .base_fetcher import BaseFetcher, FetchResult, FetchStatus

class SemanticScholarFetcher(BaseFetcher):
    """
    Fetches academic papers from Semantic Scholar
    Excellent for: research papers, citations, influential papers
    """

    def _setup(self):
        self.base_url = "https://api.semanticscholar.org/graph/v1"

    def fetch(self, query: str) -> FetchResult:
        """Search for academic papers"""
        try:
            url = f"{self.base_url}/paper/search"
            params = {
                'query': query,
                'limit': 1,
                'fields': 'title,authors,year,abstract,citationCount,influentialCitationCount,url'
            }

            data = self._make_request(url, params=params)
            if not data or not data.get('data'):
                return FetchResult(
                    status=FetchStatus.NOT_FOUND,
                    data={},
                    confidence=0.0
                )

            paper = data['data'][0]
            title = paper.get('title', 'Unknown')
            authors = [a.get('name', 'Unknown') for a in paper.get('authors', [])]
            year = paper.get('year', 'Unknown')
            abstract = paper.get('abstract', 'No abstract available')
            citations = paper.get('citationCount', 0)
            influential_citations = paper.get('influentialCitationCount', 0)
            paper_url = paper.get('url', '')

            # Clean abstract
            clean_abstract = self._clean_text(abstract, max_length=250)

            return FetchResult(
                status=FetchStatus.FOUND,
                data={
                    "title": title,
                    "authors": authors,
                    "year": year,
                    "citations": citations,
                    "influential_citations": influential_citations,
                    "abstract": abstract
                },
                summary=f"{title} ({year}) by {', '.join(authors[:3])}. Citations: {citations}. {clean_abstract}",
                confidence=0.90,
                source="semantic_scholar",
                url=paper_url
            )

        except Exception as e:
            return FetchResult(
                status=FetchStatus.ERROR,
                data={},
                error=str(e),
                confidence=0.0
            )
