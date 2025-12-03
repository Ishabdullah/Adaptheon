import requests
from pycoingecko import CoinGeckoAPI
from .base_fetcher import BaseFetcher


class FinanceFetcher(BaseFetcher):
    """
    Finance fetcher using Yahoo Finance (unofficial HTTP) for stocks/ETFs
    and CoinGecko for crypto, without yfinance or curl_cffi.
    """

    def __init__(self):
        self.cg = CoinGeckoAPI()
        self.yahoo_url = "https://query1.finance.yahoo.com/v7/finance/quote"

    def _fetch_yahoo_quote(self, symbol: str):
        params = {"symbols": symbol}
        try:
            resp = requests.get(self.yahoo_url, params=params, timeout=10)
        except Exception:
            return None
        if resp.status_code != 200:
            return None
        try:
            data = resp.json()
        except Exception:
            return None
        result = data.get("quoteResponse", {}).get("result", [])
        if not result:
            return None
        return result[0]

    def fetch(self, query: str):
        q = query.strip().upper()

        # Try Yahoo Finance for stock/ETF/indices
        quote = self._fetch_yahoo_quote(q)
        if quote:
            return {
                "status": "FOUND",
                "data": quote,
                "confidence": 0.9,
            }

        # Try crypto via CoinGecko by id (e.g. 'bitcoin', 'ethereum')
        try:
            data = self.cg.get_coin_by_id(query.strip().lower())
            if data:
                return {
                    "status": "FOUND",
                    "data": data,
                    "confidence": 0.8,
                }
        except Exception:
            pass

        return {
            "status": "NOT_FOUND",
            "data": {},
            "confidence": 0.0,
        }
