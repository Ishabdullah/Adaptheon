import os
import time
import requests
from typing import Dict, Any, Optional, List


class FlightFetcher:
    """
    Transportation / flights domain fetcher.
    Uses AviationStack when AVIATIONSTACK_API_KEY is set, otherwise OpenSky for basic state.
    """

    def __init__(self):
        self.aviation_key = os.environ.get("AVIATIONSTACK_API_KEY")
        self.aviation_base = "https://api.aviationstack.com/v1"
        self.opensky_base = "https://opensky-network.org/api"

    # --- AviationStack helpers (commercial flights, requires key) ---

    def _aviationstack_flights(self, flight_iata: Optional[str] = None, limit: int = 3) -> Optional[List[Dict[str, Any]]]:
        if not self.aviation_key:
            return None
        url = self.aviation_base + "/flights"
        params: Dict[str, Any] = {
            "access_key": self.aviation_key,
            "limit": limit,
        }
        if flight_iata:
            params["flight_iata"] = flight_iata.upper()
        try:
            resp = requests.get(url, params=params, timeout=10)
        except Exception:
            return None
        if resp.status_code != 200:
            return None
        try:
            data = resp.json()
        except Exception:
            return None
        return data.get("data") or data.get("results") or []

    def _format_aviationstack(self, flights: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
        if not flights:
            return None
        f = flights[0]
        airline = (f.get("airline") or {}).get("name") or ""
        flight = f.get("flight") or {}
        flight_iata = flight.get("iata") or flight.get("icao") or ""
        dep = f.get("departure") or {}
        arr = f.get("arrival") or {}

        dep_airport = dep.get("airport") or ""
        dep_iata = dep.get("iata") or ""
        dep_sched = dep.get("scheduled") or dep.get("estimated") or ""
        arr_airport = arr.get("airport") or ""
        arr_iata = arr.get("iata") or ""
        arr_sched = arr.get("scheduled") or arr.get("estimated") or ""

        status = f.get("flight_status") or ""
        status_part = f" Status: {status}." if status else ""
        route_part = f"{airline} flight {flight_iata} from {dep_airport} ({dep_iata}) to {arr_airport} ({arr_iata})."
        time_part = ""
        if dep_sched or arr_sched:
            time_part = " Scheduled departure: {}. Scheduled arrival: {}.".format(dep_sched or "unknown", arr_sched or "unknown")

        summary = route_part + time_part + status_part
        url = None  # AviationStack does not give a direct URL

        return {
            "status": "FOUND",
            "summary": summary,
            "confidence": 0.88,
            "url": url,
            "metadata": {
                "source": "aviationstack",
                "airline": airline,
                "flight_iata": flight_iata,
                "departure": {
                    "airport": dep_airport,
                    "iata": dep_iata,
                    "scheduled": dep_sched,
                },
                "arrival": {
                    "airport": arr_airport,
                    "iata": arr_iata,
                    "scheduled": arr_sched,
                },
                "status": status,
            },
        }

    # --- OpenSky helpers (live ADS-B state, research/non-commercial) ---

    def _opensky_states(self, icao24: Optional[str] = None) -> Optional[List[Any]]:
        url = self.opensky_base + "/states/all"
        params: Dict[str, Any] = {}
        if icao24:
            params["icao24"] = icao24.lower()
        try:
            resp = requests.get(url, params=params, timeout=10)
        except Exception:
            return None
        if resp.status_code != 200:
            return None
        try:
            data = resp.json()
        except Exception:
            return None
        return data.get("states") or []

    def _format_opensky(self, states: List[Any]) -> Optional[Dict[str, Any]]:
        if not states:
            return None
        s = states[0]
        # OpenSky state vector format from docs:
        # [0] icao24, [1] callsign, [2] origin_country, [3] time_position, [4] last_contact,
        # [5] longitude, [6] latitude, [7] baro_altitude, [8] on_ground, [9] velocity, [10] heading, ...
        icao24 = s[0]
        callsign = (s[1] or "").strip()
        country = s[2]
        lon = s[5]
        lat = s[6]
        on_ground = bool(s[8])
        velocity = s[9]
        heading = s[10]
        status = "on the ground" if on_ground else "in the air"
        summary = f"Aircraft {callsign or icao24} from {country} is currently {status}"
        if lat is not None and lon is not None:
            summary += f" near latitude {lat:.2f}, longitude {lon:.2f}"
        if velocity is not None:
            summary += f" at a speed of about {velocity:.1f} m/s"
        if heading is not None:
            summary += f" heading {heading:.1f} degrees"
        summary += "."

        return {
            "status": "FOUND",
            "summary": summary,
            "confidence": 0.75,
            "url": None,
            "metadata": {
                "source": "opensky",
                "icao24": icao24,
                "callsign": callsign,
            },
        }

    def fetch(self, query: str) -> Dict[str, Any]:
        """
        High-level flight fetch.
        If query contains something like 'AA100' use AviationStack flight_iata.
        Otherwise, try OpenSky state by treating the token as callsign/icao24.
        """
        tokens = query.upper().split()
        flight_code = None
        for t in tokens:
            # Heuristic: 2-3 letters + 2-4 digits -> flight code
            prefix = "".join(ch for ch in t if ch.isalpha())
            suffix = "".join(ch for ch in t if ch.isdigit())
            if 2 <= len(prefix) <= 3 and 2 <= len(suffix) <= 4:
                flight_code = prefix + suffix
                break

        # Try AviationStack if configured and we recognized a flight code
        if self.aviation_key and flight_code:
            flights = self._aviationstack_flights(flight_iata=flight_code, limit=3)
            formatted = self._format_aviationstack(flights or [])
            if formatted:
                return formatted

        # Fallback: OpenSky, using first token that looks like callsign/icao24
        icao = None
        for t in tokens:
            if len(t) >= 3 and len(t) <= 8:
                icao = t.lower()
                break

        if icao:
            states = self._opensky_states(icao24=icao)
        else:
            states = self._opensky_states()

        formatted_state = self._format_opensky(states or [])
        if formatted_state:
            return formatted_state

        return {
            "status": "NOT_FOUND",
            "summary": "",
            "confidence": 0.0,
            "url": None,
            "metadata": {},
        }
