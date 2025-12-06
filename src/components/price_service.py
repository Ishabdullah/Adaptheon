"""
Production-Grade Price Service for Stocks and Crypto
Handles live price queries with multiple fallback sources
"""

import requests
import logging
from components.time_service import get_now
from components.fetchers.yahoo_finance_fetcher import YahooFinanceFetcher
from components.fetchers.base_fetcher import FetchStatus

logger = logging.getLogger('Adaptheon.PriceService')


class PriceService:
    """
    Fetch live prices for stocks and crypto with fallback sources.

    Primary sources:
    - Stocks: Yahoo Finance
    - Crypto: CoinGecko

    Fallback sources:
    - Crypto: CoinMarketCap (if available)
    """

    def __init__(self):
        # Stock price fetcher
        self.yahoo_fetcher = YahooFinanceFetcher()

        # Crypto endpoints
        self.coingecko_url = "https://api.coingecko.com/api/v3/simple/price"

        # Crypto name normalization
        self.crypto_map = {
            "bitcoin": "bitcoin",
            "btc": "bitcoin",
            "ethereum": "ethereum",
            "eth": "ethereum",
            "cardano": "cardano",
            "ada": "cardano",
            "solana": "solana",
            "sol": "solana",
            "dogecoin": "dogecoin",
            "doge": "dogecoin",
            "polkadot": "polkadot",
            "dot": "polkadot",
        }

        # Stock indicators (if these words are in query, it's likely a stock)
        self.stock_indicators = [
            "stock", "shares", "nasdaq", "dow", "s&p", "nyse",
            "apple", "microsoft", "google", "amazon", "tesla",
            "meta", "facebook", "netflix", "nvidia"
        ]

    def _is_stock_query(self, asset_name: str) -> bool:
        """Determine if query is for stock or crypto"""
        asset_lower = asset_name.lower()

        # Check for stock indicators
        for indicator in self.stock_indicators:
            if indicator in asset_lower:
                return True

        # Check if it's a known crypto
        if asset_lower in self.crypto_map or asset_lower.replace(" ", "-") in self.crypto_map.values():
            return False

        # Check if it looks like a stock ticker (2-5 uppercase letters)
        words = asset_name.upper().split()
        for word in words:
            word_clean = word.strip('.,!?')
            if 2 <= len(word_clean) <= 5 and word_clean.isalpha():
                return True

        # Default to stock for ambiguous cases
        return True

    def get_price(self, asset_name: str):
        """
        Get current price for stock or crypto asset.

        Args:
            asset_name: Asset name or ticker (e.g., "Amazon", "AMZN", "Bitcoin", "BTC")

        Returns:
            dict with price data or None if failed
        """
        if not asset_name or not asset_name.strip():
            logger.warning("Empty asset name provided")
            return None

        asset_name = asset_name.strip()
        is_stock = self._is_stock_query(asset_name)

        if is_stock:
            logger.info(f"Fetching stock price for: {asset_name}")
            return self._get_stock_price(asset_name)
        else:
            logger.info(f"Fetching crypto price for: {asset_name}")
            return self._get_crypto_price(asset_name)

    def _get_stock_price(self, asset_name: str):
        """Get stock price using Yahoo Finance"""
        try:
            # Use Yahoo Finance fetcher
            result = self.yahoo_fetcher.fetch(f"stock price {asset_name}")

            if result.status == FetchStatus.FOUND:
                now = get_now()
                return {
                    "asset": asset_name,
                    "asset_id": result.data.get("symbol", asset_name.upper()),
                    "price_usd": result.data.get("price"),
                    "currency": result.data.get("currency", "USD"),
                    "change": result.data.get("change"),
                    "change_percent": result.data.get("change_percent"),
                    "previous_close": result.data.get("previous_close"),
                    "as_of_date": now["date"],
                    "as_of_time": now["time"],
                    "source": "yahoo_finance",
                    "asset_type": "stock"
                }
            else:
                logger.warning(f"Yahoo Finance failed for {asset_name}: {result.error or 'NOT_FOUND'}")
                return None

        except Exception as e:
            logger.error(f"Error fetching stock price for {asset_name}: {e}")
            return None

    def _get_crypto_price(self, asset_name: str):
        """Get crypto price using CoinGecko (with fallback potential)"""
        # Normalize crypto name
        asset_id = self._normalize_crypto(asset_name)

        # Try CoinGecko
        result = self._fetch_from_coingecko(asset_id, asset_name)
        if result:
            return result

        logger.warning(f"All crypto price sources failed for {asset_name}")
        return None

    def _normalize_crypto(self, asset_name: str) -> str:
        """Normalize crypto asset name to CoinGecko ID"""
        name = asset_name.lower().strip()

        # Check direct mapping
        if name in self.crypto_map:
            return self.crypto_map[name]

        # Try as-is with hyphens
        return name.replace(" ", "-")

    def _fetch_from_coingecko(self, asset_id: str, original_name: str):
        """Fetch price from CoinGecko API"""
        params = {
            "ids": asset_id,
            "vs_currencies": "usd",
            "include_24hr_change": "true"
        }

        try:
            resp = requests.get(self.coingecko_url, params=params, timeout=10)

            if resp.status_code != 200:
                logger.warning(f"CoinGecko returned status {resp.status_code} for {asset_id}")
                return None

            data = resp.json()

            if asset_id not in data:
                logger.warning(f"CoinGecko has no data for {asset_id}")
                return None

            entry = data[asset_id]
            if "usd" not in entry:
                logger.warning(f"CoinGecko response missing USD price for {asset_id}")
                return None

            now = get_now()

            return {
                "asset": original_name,
                "asset_id": asset_id,
                "price_usd": entry["usd"],
                "change_24h_percent": entry.get("usd_24h_change"),
                "as_of_date": now["date"],
                "as_of_time": now["time"],
                "currency": "USD",
                "source": "coingecko",
                "asset_type": "crypto"
            }

        except requests.exceptions.Timeout:
            logger.error(f"CoinGecko request timeout for {asset_id}")
            return None
        except requests.exceptions.RequestException as e:
            logger.error(f"CoinGecko network error for {asset_id}: {e}")
            return None
        except Exception as e:
            logger.error(f"CoinGecko parsing error for {asset_id}: {e}")
            return None
