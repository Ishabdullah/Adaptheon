"""
Open-Meteo Weather Fetcher - Production-Grade Weather Data
Free weather API without API key requirements
"""

from .base_fetcher import BaseFetcher, FetchResult, FetchStatus

class OpenMeteoFetcher(BaseFetcher):
    """
    Fetches weather data from Open-Meteo API
    Excellent for: current weather, forecasts, historical data
    """

    def _setup(self):
        self.base_url = "https://api.open-meteo.com/v1/forecast"
        self.geocoding_url = "https://geocoding-api.open-meteo.com/v1/search"

    def fetch(self, query: str) -> FetchResult:
        """Get weather information for a location"""
        try:
            # Extract location from query
            location = self._extract_location(query)
            if not location:
                return FetchResult(
                    status=FetchStatus.NOT_FOUND,
                    data={},
                    summary="Could not identify location",
                    confidence=0.0
                )

            # Geocode location
            coords = self._geocode_location(location)
            if not coords:
                return FetchResult(
                    status=FetchStatus.NOT_FOUND,
                    data={},
                    summary=f"Could not find coordinates for {location}",
                    confidence=0.0
                )

            # Fetch weather data
            params = {
                'latitude': coords['lat'],
                'longitude': coords['lon'],
                'current_weather': 'true',
                'temperature_unit': 'fahrenheit',
                'windspeed_unit': 'mph'
            }

            data = self._make_request(self.base_url, params=params)
            if not data or 'current_weather' not in data:
                return FetchResult(
                    status=FetchStatus.NOT_FOUND,
                    data={},
                    confidence=0.0
                )

            weather = data['current_weather']
            return FetchResult(
                status=FetchStatus.FOUND,
                data={
                    "location": coords['name'],
                    "temperature": weather['temperature'],
                    "windspeed": weather['windspeed'],
                    "weather_code": weather['weathercode'],
                    "time": weather['time']
                },
                summary=f"{coords['name']}: {weather['temperature']}°F, {weather['windspeed']} mph wind",
                confidence=0.90,
                source="open_meteo",
                url=f"https://open-meteo.com/en/docs"
            )

        except Exception as e:
            return FetchResult(
                status=FetchStatus.ERROR,
                data={},
                error=str(e),
                confidence=0.0
            )

    def _geocode_location(self, location: str) -> dict:
        """Convert location name to coordinates"""
        params = {
            'name': location,
            'count': 1,
            'language': 'en',
            'format': 'json'
        }

        data = self._make_request(self.geocoding_url, params=params)
        if not data or not data.get('results'):
            return None

        result = data['results'][0]
        return {
            'lat': result['latitude'],
            'lon': result['longitude'],
            'name': result['name']
        }

    def _extract_location(self, query: str) -> str:
        """Extract location from query"""
        query_lower = query.lower()

        # Remove common weather-related words
        for word in ['weather', 'temperature', 'forecast', 'in', 'at', 'for', 'what', 'is', 'the']:
            query_lower = query_lower.replace(word, '')

        location = query_lower.strip().strip('?').strip()
        return location.title() if location else ""
