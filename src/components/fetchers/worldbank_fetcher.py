"""
World Bank Fetcher - Global Development Data
Production-grade economic and development indicators
"""

from .base_fetcher import BaseFetcher, FetchResult, FetchStatus

class WorldBankFetcher(BaseFetcher):
    """
    Fetches development indicators from World Bank API
    Excellent for: GDP, population, economic data, country statistics
    """

    def _setup(self):
        self.base_url = "https://api.worldbank.org/v2"

    def fetch(self, query: str) -> FetchResult:
        """Query World Bank indicators"""
        try:
            query_lower = query.lower()

            # Determine indicator based on query
            indicator = None
            if "gdp" in query_lower:
                indicator = "NY.GDP.MKTP.CD"  # GDP (current US$)
            elif "population" in query_lower:
                indicator = "SP.POP.TOTL"  # Population, total
            elif "life expectancy" in query_lower:
                indicator = "SP.DYN.LE00.IN"  # Life expectancy at birth

            if not indicator:
                return FetchResult(
                    status=FetchStatus.NOT_FOUND,
                    data={},
                    summary="Could not determine indicator type",
                    confidence=0.0
                )

            # Extract country code (simplified - US as default)
            country_code = "USA"  # Default to USA

            url = f"{self.base_url}/country/{country_code}/indicator/{indicator}"
            params = {
                'format': 'json',
                'per_page': 1,
                'date': '2022:2023'  # Recent years
            }

            response = self.session.get(url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()

            if not data or len(data) < 2 or not data[1]:
                return FetchResult(
                    status=FetchStatus.NOT_FOUND,
                    data={},
                    confidence=0.0
                )

            record = data[1][0]
            value = record.get('value')
            year = record.get('date')
            country_name = record.get('country', {}).get('value', 'Unknown')
            indicator_name = record.get('indicator', {}).get('value', 'Unknown')

            if value is None:
                return FetchResult(
                    status=FetchStatus.NOT_FOUND,
                    data={},
                    confidence=0.0
                )

            # Format value based on indicator
            if "GDP" in indicator_name:
                formatted_value = f"${value/1e12:.2f} trillion"
            elif "Population" in indicator_name:
                formatted_value = f"{value/1e6:.1f} million"
            else:
                formatted_value = f"{value:.2f}"

            return FetchResult(
                status=FetchStatus.FOUND,
                data={
                    "country": country_name,
                    "indicator": indicator_name,
                    "value": value,
                    "year": year
                },
                summary=f"{country_name} {indicator_name} ({year}): {formatted_value}",
                confidence=0.85,
                source="worldbank",
                url=f"https://data.worldbank.org/indicator/{indicator}"
            )

        except Exception as e:
            return FetchResult(
                status=FetchStatus.ERROR,
                data={},
                error=str(e),
                confidence=0.0
            )
