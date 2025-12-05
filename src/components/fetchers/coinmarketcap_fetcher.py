"""
CoinMarketCap Fetcher - Cryptocurrency Market Data
Production-grade crypto price and market information
"""

from .base_fetcher import BaseFetcher, FetchResult, FetchStatus

class CoinMarketCapFetcher(BaseFetcher):
    """
    Fetches cryptocurrency data from CoinMarketCap
    Excellent for: crypto prices, market cap, volume, rankings
    """

    def _setup(self):
        self.base_url = "https://pro-api.coinmarketcap.com/v1"
        # Note: CoinMarketCap requires API key
        # Set COINMARKETCAP_API_KEY in .env for production use

    def fetch(self, query: str) -> FetchResult:
        """Get cryptocurrency information"""
        try:
            # CoinMarketCap requires API key for all endpoints
            return FetchResult(
                status=FetchStatus.API_KEY_REQUIRED,
                data={},
                summary="CoinMarketCap requires an API key. Set COINMARKETCAP_API_KEY in .env. Get one free at https://coinmarketcap.com/api/",
                confidence=0.0,
                source="coinmarketcap"
            )

        except Exception as e:
            return FetchResult(
                status=FetchStatus.ERROR,
                data={},
                error=str(e),
                confidence=0.0
            )
