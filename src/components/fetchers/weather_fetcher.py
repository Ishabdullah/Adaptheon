import requests
from .base_fetcher import BaseFetcher


class WeatherFetcher(BaseFetcher):
    """
    Simple Open-Meteo-based weather fetcher using requests.
    Expects latitude and longitude in the query string as 'lat,lon'
    (e.g., "41.71,-72.65"). You can adapt this later to use GPS or geocoding.
    """

    def __init__(self):
        self.base_url = "https://api.open-meteo.com/v1/forecast"

    def fetch(self, query: str):
        try:
            parts = query.split(",")
            if len(parts) != 2:
                return {"status": "NOT_FOUND", "data": {}, "confidence": 0.0}
            lat = float(parts[0].strip())
            lon = float(parts[1].strip())
        except Exception:
            return {"status": "NOT_FOUND", "data": {}, "confidence": 0.0}

        params = {
            "latitude": lat,
            "longitude": lon,
            "current_weather": "true",
        }
        try:
            resp = requests.get(self.base_url, params=params, timeout=10)
        except Exception:
            return {"status": "NOT_FOUND", "data": {}, "confidence": 0.0}

        if resp.status_code != 200:
            return {"status": "NOT_FOUND", "data": {}, "confidence": 0.0}

        try:
            data = resp.json()
        except Exception:
            return {"status": "NOT_FOUND", "data": {}, "confidence": 0.0}

        cw = data.get("current_weather")
        if not cw:
            return {"status": "NOT_FOUND", "data": {}, "confidence": 0.0}

        return {
            "status": "FOUND",
            "data": cw,
            "confidence": 0.9,
        }
