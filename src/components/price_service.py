import requests
from components.time_service import get_now


class PriceService:
    """
    Fetch live crypto prices using public CoinGecko API.
    """

    def __init__(self):
        self.base_url = "https://api.coingecko.com/api/v3/simple/price"
        self.name_to_id = {
            "bitcoin": "bitcoin",
            "btc": "bitcoin",
            "ethereum": "ethereum",
            "eth": "ethereum",
        }

    def _normalize_asset(self, asset_name):
        name = asset_name.lower().strip()
        if name in self.name_to_id:
            return self.name_to_id[name]
        return name.replace(" ", "-")

    def get_price(self, asset_name):
        asset_id = self._normalize_asset(asset_name)
        params = {
            "ids": asset_id,
            "vs_currencies": "usd",
        }
        try:
            resp = requests.get(self.base_url, params=params, timeout=10)
        except Exception:
            return None

        if resp.status_code != 200:
            return None

        try:
            data = resp.json()
        except Exception:
            return None

        if asset_id not in data:
            return None
        entry = data[asset_id]
        if "usd" not in entry:
            return None

        now = get_now()
        return {
            "asset": asset_name,
            "asset_id": asset_id,
            "price_usd": entry["usd"],
            "as_of_date": now["date"],
            "as_of_time": now["time"],
        }
