"""
OpenCorporates Fetcher - Corporate Registry Data
Production-grade company information
"""

from .base_fetcher import BaseFetcher, FetchResult, FetchStatus

class OpenCorporatesFetcher(BaseFetcher):
    """
    Fetches corporate information from OpenCorporates
    Excellent for: company data, directors, filings, jurisdictions
    """

    def _setup(self):
        self.base_url = "https://api.opencorporates.com/v0.4"

    def fetch(self, query: str) -> FetchResult:
        """Search for company information"""
        try:
            company_name = query.replace("company", "").replace("corporation", "").strip()

            url = f"{self.base_url}/companies/search"
            params = {
                'q': company_name,
                'per_page': 1
            }

            data = self._make_request(url, params=params)
            if not data or not data.get('results', {}).get('companies'):
                return FetchResult(
                    status=FetchStatus.NOT_FOUND,
                    data={},
                    confidence=0.0
                )

            company_data = data['results']['companies'][0]['company']
            name = company_data.get('name', 'Unknown')
            jurisdiction = company_data.get('jurisdiction_code', 'Unknown')
            company_number = company_data.get('company_number', 'Unknown')
            status = company_data.get('current_status', 'Unknown')
            company_type = company_data.get('company_type', 'Unknown')
            incorporation_date = company_data.get('incorporation_date', 'Unknown')

            return FetchResult(
                status=FetchStatus.FOUND,
                data={
                    "name": name,
                    "jurisdiction": jurisdiction,
                    "company_number": company_number,
                    "status": status,
                    "type": company_type,
                    "incorporated": incorporation_date
                },
                summary=f"{name} ({jurisdiction}): {status}, incorporated {incorporation_date}",
                confidence=0.80,
                source="opencorporates",
                url=company_data.get('opencorporates_url', '')
            )

        except Exception as e:
            return FetchResult(
                status=FetchStatus.ERROR,
                data={},
                error=str(e),
                confidence=0.0
            )
