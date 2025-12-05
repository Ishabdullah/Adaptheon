"""
Yahoo Finance Fetcher - Stock Market Data
Production-grade financial data retrieval
"""

from .base_fetcher import BaseFetcher, FetchResult, FetchStatus

class YahooFinanceFetcher(BaseFetcher):
    """
    Fetches stock market data from Yahoo Finance
    Excellent for: stock prices, market data, company information
    """

    def _setup(self):
        self.base_url = "https://query1.finance.yahoo.com/v8/finance/chart"

    def fetch(self, query: str) -> FetchResult:
        """Get stock price information"""
        try:
            # Extract ticker symbol from query
            ticker = self._extract_ticker(query)
            if not ticker:
                return FetchResult(
                    status=FetchStatus.NOT_FOUND,
                    data={},
                    summary="Could not identify stock ticker",
                    confidence=0.0
                )

            url = f"{self.base_url}/{ticker}"
            params = {
                'interval': '1d',
                'range': '1d'
            }

            data = self._make_request(url, params=params)
            if not data or 'chart' not in data:
                return FetchResult(
                    status=FetchStatus.NOT_FOUND,
                    data={},
                    confidence=0.0
                )

            result = data['chart']['result'][0]
            meta = result['meta']
            quote = result['indicators']['quote'][0]

            current_price = meta.get('regularMarketPrice')
            previous_close = meta.get('previousClose')
            currency = meta.get('currency', 'USD')

            if current_price and previous_close:
                change = current_price - previous_close
                change_pct = (change / previous_close) * 100

                return FetchResult(
                    status=FetchStatus.FOUND,
                    data={
                        "symbol": ticker.upper(),
                        "price": current_price,
                        "currency": currency,
                        "previous_close": previous_close,
                        "change": change,
                        "change_percent": change_pct
                    },
                    summary=f"{ticker.upper()} is trading at {currency} {current_price:.2f} ({change:+.2f}, {change_pct:+.2f}%)",
                    confidence=0.90,
                    source="yahoo_finance",
                    url=f"https://finance.yahoo.com/quote/{ticker}"
                )

        except Exception as e:
            return FetchResult(
                status=FetchStatus.ERROR,
                data={},
                error=str(e),
                confidence=0.0
            )

        return FetchResult(status=FetchStatus.NOT_FOUND, data={}, confidence=0.0)

    def _extract_ticker(self, query: str) -> str:
        """Extract stock ticker from query"""
        query_upper = query.upper()

        # Common company to ticker mappings
        ticker_map = {
            "APPLE": "AAPL",
            "MICROSOFT": "MSFT",
            "GOOGLE": "GOOGL",
            "AMAZON": "AMZN",
            "TESLA": "TSLA",
            "META": "META",
            "FACEBOOK": "META",
            "NETFLIX": "NFLX",
            "NVIDIA": "NVDA"
        }

        # Check for direct company name matches
        for company, ticker in ticker_map.items():
            if company in query_upper:
                return ticker

        # Check for existing ticker symbols (3-5 uppercase letters)
        words = query_upper.split()
        for word in words:
            word_clean = word.strip('.,!?')
            if 2 <= len(word_clean) <= 5 and word_clean.isalpha():
                # Might be a ticker
                if word_clean in ["STOCK", "PRICE", "CURRENT", "THE", "OF", "IS", "WHAT"]:
                    continue
                return word_clean

        return ""
