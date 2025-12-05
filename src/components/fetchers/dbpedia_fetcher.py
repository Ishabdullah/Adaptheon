"""
DBpedia Fetcher - Structured Wikipedia Knowledge
Production-grade semantic web data extraction
"""

from .base_fetcher import BaseFetcher, FetchResult, FetchStatus

class DBpediaFetcher(BaseFetcher):
    """
    Fetches structured data from DBpedia (Wikipedia as structured data)
    Excellent for: entity properties, relationships, factual data
    """

    def _setup(self):
        self.sparql_endpoint = "https://dbpedia.org/sparql"
        self.lookup_url = "https://lookup.dbpedia.org/api/search"

    def fetch(self, query: str) -> FetchResult:
        """Query DBpedia for structured knowledge"""
        try:
            # First, lookup entity
            params = {
                'query': query,
                'format': 'json',
                'maxResults': 1
            }

            data = self._make_request(self.lookup_url, params=params)
            if not data or not data.get('docs'):
                return FetchResult(
                    status=FetchStatus.NOT_FOUND,
                    data={},
                    confidence=0.0
                )

            entity = data['docs'][0]
            label = entity.get('label', ['Unknown'])[0] if isinstance(entity.get('label'), list) else entity.get('label', 'Unknown')
            description = entity.get('comment', ['No description'])[0] if isinstance(entity.get('comment'), list) else entity.get('comment', 'No description')
            categories = entity.get('category', [])[:3]  # Top 3 categories
            resource_uri = entity.get('resource', [''])[0] if isinstance(entity.get('resource'), list) else entity.get('resource', '')

            return FetchResult(
                status=FetchStatus.FOUND,
                data={
                    "label": label,
                    "description": description,
                    "categories": categories,
                    "uri": resource_uri
                },
                summary=f"{label}: {description[:200]}",
                confidence=0.85,
                source="dbpedia",
                url=resource_uri if resource_uri else "https://dbpedia.org"
            )

        except Exception as e:
            return FetchResult(
                status=FetchStatus.ERROR,
                data={},
                error=str(e),
                confidence=0.0
            )
