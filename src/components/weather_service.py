import requests
from components.time_service import get_now


class WeatherService:
    """
    Fetch current weather using Open-Meteo (no API key).
    Default fallback location: near Wethersfield, CT.
    """

    def __init__(self, latitude=41.71, longitude=-72.65):
        self.base_url = "https://api.open-meteo.com/v1/forecast"
        self.default_lat = latitude
        self.default_lon = longitude

    def get_current_weather(self, latitude=None, longitude=None):
        """
        Get current weather for the given coordinates or default location.
        """
        lat = self.default_lat if latitude is None else latitude
        lon = self.default_lon if longitude is None else longitude

        params = {
            "latitude": lat,
            "longitude": lon,
            "current_weather": "true",
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

        cw = data.get("current_weather")
        if not cw:
            return None

        temp_c = cw.get("temperature")
        if temp_c is None:
            return None

        # Celsius to Fahrenheit
        temp_f = temp_c * 9.0 / 5.0 + 32.0

        wind_kmh = cw.get("windspeed")
        if wind_kmh is None:
            wind_kmh = 0.0

        # km/h to mph
        wind_mph = wind_kmh * 0.621371

        now = get_now()
        return {
            "temperature_c": temp_c,
            "temperature_f": temp_f,
            "windspeed_kmh": wind_kmh,
            "windspeed_mph": wind_mph,
            "winddirection": cw.get("winddirection"),
            "weather_code": cw.get("weathercode"),
            "as_of_date": now["date"],
            "as_of_time": now["time"],
        }
