"""
Yahoo Finance Fetcher - Stock Market Data
Production-grade financial data retrieval
"""

import logging
from .base_fetcher import BaseFetcher, FetchResult, FetchStatus

logger = logging.getLogger('Adaptheon.YahooFinanceFetcher')


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
            logger.info(f"Extracted ticker '{ticker}' from query '{query}'")

            if not ticker:
                logger.warning(f"Could not extract ticker from query: {query}")
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

            logger.info(f"Fetching from Yahoo Finance: {url}")
            data = self._make_request(url, params=params)

            if not data:
                logger.error(f"No data returned from Yahoo Finance for ticker {ticker}")
                return FetchResult(
                    status=FetchStatus.NOT_FOUND,
                    data={},
                    summary=f"Yahoo Finance returned no data for {ticker}",
                    confidence=0.0
                )

            if 'chart' not in data:
                logger.error(f"Invalid response from Yahoo Finance (no 'chart' field): {data}")
                return FetchResult(
                    status=FetchStatus.NOT_FOUND,
                    data={},
                    summary=f"Invalid Yahoo Finance response for {ticker}",
                    confidence=0.0
                )

            if not data['chart'].get('result'):
                error_msg = data['chart'].get('error', {}).get('description', 'Unknown error')
                logger.error(f"Yahoo Finance error for {ticker}: {error_msg}")
                return FetchResult(
                    status=FetchStatus.NOT_FOUND,
                    data={},
                    summary=f"Yahoo Finance error: {error_msg}",
                    confidence=0.0
                )

            result = data['chart']['result'][0]
            meta = result.get('meta', {})

            current_price = meta.get('regularMarketPrice')
            previous_close = meta.get('previousClose')
            currency = meta.get('currency', 'USD')

            if not current_price:
                logger.warning(f"No current price found for {ticker} in Yahoo Finance response")
                return FetchResult(
                    status=FetchStatus.NOT_FOUND,
                    data={},
                    summary=f"No price data available for {ticker}",
                    confidence=0.0
                )

            # Calculate change (use 0 if no previous close)
            if previous_close:
                change = current_price - previous_close
                change_pct = (change / previous_close) * 100
            else:
                change = 0.0
                change_pct = 0.0

            logger.info(f"Successfully fetched {ticker}: ${current_price:.2f}")

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

        except KeyError as e:
            logger.error(f"Missing expected field in Yahoo Finance response for {ticker}: {e}")
            return FetchResult(
                status=FetchStatus.ERROR,
                data={},
                error=f"Invalid response structure: {e}",
                confidence=0.0
            )
        except Exception as e:
            logger.error(f"Unexpected error fetching {ticker} from Yahoo Finance: {e}")
            return FetchResult(
                status=FetchStatus.ERROR,
                data={},
                error=str(e),
                confidence=0.0
            )

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
            "NVIDIA": "NVDA",
            "ALIBABA": "BABA",
            "BERKSHIRE": "BRK-B",
            "JPMORGAN": "JPM",
            "JOHNSON": "JNJ",
            "VISA": "V",
            "WALMART": "WMT",
            "MASTERCARD": "MA",
            "UNITEDHEALTH": "UNH",
            "PROCTER": "PG",
            "HOME DEPOT": "HD",
            "BANK OF AMERICA": "BAC",
            "DISNEY": "DIS",
            "ADOBE": "ADBE",
            "CISCO": "CSCO",
            "NETFLIX": "NFLX",
            "PEPSICO": "PEP",
            "COCA-COLA": "KO",
            "INTEL": "INTC",
            "ORACLE": "ORCL",
            "SALESFORCE": "CRM"
        }

        # Check for direct company name matches
        for company, ticker in ticker_map.items():
            if company in query_upper:
                return ticker

        # Check for existing ticker symbols (2-5 uppercase letters)
        words = query_upper.split()
        for word in words:
            word_clean = word.strip('.,!?')
            if 2 <= len(word_clean) <= 5 and word_clean.isalpha():
                # Might be a ticker - but skip common query words
                if word_clean in ["STOCK", "PRICE", "CURRENT", "THE", "OF", "IS", "WHAT", "WHATS"]:
                    continue
                return word_clean

        return ""
