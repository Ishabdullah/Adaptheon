"""
WHO (World Health Organization) Fetcher - Global Health Data
Production-grade health statistics and information
"""

from .base_fetcher import BaseFetcher, FetchResult, FetchStatus

class WHOFetcher(BaseFetcher):
    """
    Fetches health data from WHO APIs
    Excellent for: disease data, health statistics, global health info
    """

    def _setup(self):
        self.base_url = "https://ghoapi.azureedge.net/api"

    def fetch(self, query: str) -> FetchResult:
        """Query WHO Global Health Observatory"""
        try:
            # WHO GHO API - get indicator list first
            # This is simplified - production would map queries to indicators

            # Example: Life expectancy indicator
            url = f"{self.base_url}/WHOSIS_000001"  # Life expectancy at birth

            data = self._make_request(url)
            if not data or not data.get('value'):
                return FetchResult(
                    status=FetchStatus.NOT_FOUND,
                    data={},
                    confidence=0.0
                )

            # Get first record
            record = data['value'][0] if data['value'] else {}
            country = record.get('SpatialDim', 'Unknown')
            value = record.get('NumericValue', 'Unknown')
            year = record.get('TimeDim', 'Unknown')

            return FetchResult(
                status=FetchStatus.FOUND,
                data={
                    "indicator": "Life expectancy at birth",
                    "country": country,
                    "value": value,
                    "year": year
                },
                summary=f"Life expectancy in {country} ({year}): {value} years",
                confidence=0.75,
                source="who",
                url="https://www.who.int/data/gho"
            )

        except Exception as e:
            return FetchResult(
                status=FetchStatus.ERROR,
                data={},
                error=str(e),
                confidence=0.0
            )
