"""
Data.gov Fetcher - U.S. Open Government Data
Production-grade access to federal datasets
"""

from .base_fetcher import BaseFetcher, FetchResult, FetchStatus

class DataGovFetcher(BaseFetcher):
    """
    Fetches datasets from Data.gov catalog
    Excellent for: government datasets, statistics, open data
    """

    def _setup(self):
        self.base_url = "https://catalog.data.gov/api/3/action"

    def fetch(self, query: str) -> FetchResult:
        """Search for government datasets"""
        try:
            url = f"{self.base_url}/package_search"
            params = {
                'q': query,
                'rows': 1
            }

            data = self._make_request(url, params=params)
            if not data or not data.get('result', {}).get('results'):
                return FetchResult(
                    status=FetchStatus.NOT_FOUND,
                    data={},
                    confidence=0.0
                )

            dataset = data['result']['results'][0]
            title = dataset.get('title', 'Unknown')
            notes = dataset.get('notes', 'No description')
            organization = dataset.get('organization', {}).get('title', 'Unknown')
            metadata_created = dataset.get('metadata_created', 'Unknown')

            # Clean notes
            clean_notes = self._clean_text(notes, max_length=200)

            return FetchResult(
                status=FetchStatus.FOUND,
                data={
                    "title": title,
                    "organization": organization,
                    "created": metadata_created,
                    "description": notes
                },
                summary=f"{title} (by {organization}): {clean_notes}",
                confidence=0.80,
                source="datagov",
                url=f"https://catalog.data.gov/dataset/{dataset.get('name', '')}"
            )

        except Exception as e:
            return FetchResult(
                status=FetchStatus.ERROR,
                data={},
                error=str(e),
                confidence=0.0
            )
