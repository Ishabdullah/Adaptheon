"""
OpenSky Network Fetcher - Flight Tracking Data
Production-grade aviation data
"""

from .base_fetcher import BaseFetcher, FetchResult, FetchStatus

class OpenSkyFetcher(BaseFetcher):
    """
    Fetches real-time flight data from OpenSky Network
    Excellent for: flight tracking, aircraft positions, airports
    """

    def _setup(self):
        self.base_url = "https://opensky-network.org/api"

    def fetch(self, query: str) -> FetchResult:
        """Get flight information"""
        try:
            # Get all flights (or filter by bounding box)
            url = f"{self.base_url}/states/all"

            data = self._make_request(url)
            if not data or not data.get('states'):
                return FetchResult(
                    status=FetchStatus.NOT_FOUND,
                    data={},
                    summary="No flight data available",
                    confidence=0.0
                )

            # Get first available flight
            flight = data['states'][0]
            # States format: [icao24, callsign, origin_country, time_position, last_contact,
            #                 longitude, latitude, baro_altitude, on_ground, velocity, ...]

            callsign = flight[1].strip() if flight[1] else 'Unknown'
            country = flight[2] if flight[2] else 'Unknown'
            altitude = flight[7] if flight[7] else 0
            velocity = flight[9] if flight[9] else 0

            return FetchResult(
                status=FetchStatus.FOUND,
                data={
                    "callsign": callsign,
                    "country": country,
                    "altitude_meters": altitude,
                    "velocity_m/s": velocity,
                    "total_flights_tracked": len(data['states'])
                },
                summary=f"Flight {callsign} from {country} at {altitude}m altitude. Total {len(data['states'])} flights tracked.",
                confidence=0.75,
                source="opensky",
                url="https://opensky-network.org"
            )

        except Exception as e:
            return FetchResult(
                status=FetchStatus.ERROR,
                data={},
                error=str(e),
                confidence=0.0
            )
