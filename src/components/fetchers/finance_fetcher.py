import yfinance as yf
from pycoingecko import CoinGeckoAPI
from .base_fetcher import BaseFetcher


class FinanceFetcher(BaseFetcher):
    """
    Finance fetcher using Yahoo Finance for stocks and CoinGecko for crypto.
    """

    def __init__(self):
        self.cg = CoinGeckoAPI()

    def fetch(self, query: str):
        q = query.strip()
        # Try stock / ETF first
        try:
            ticker = yf.Ticker(q)
            info = ticker.info
            if info and "shortName" in info:
                return {
                    "status": "FOUND",
                    "data": info,
                    "confidence": 0.9,
                }
        except Exception:
            pass

        # Try crypto by id (e.g., 'bitcoin', 'ethereum')
        try:
            data = self.cg.get_coin_by_id(q.lower())
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
