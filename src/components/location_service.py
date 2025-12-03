import json
import subprocess
import requests


class LocationService:
    """
    Get device GPS via termux-location and reverse-geocode via Nominatim.
    """

    def __init__(self):
        self.reverse_url = "https://nominatim.openstreetmap.org/reverse"

    def get_gps(self):
        """
        Call termux-location once and return latitude/longitude.
        Requires termux-api and Termux:API app with location permission.
        """
        try:
            proc = subprocess.run(
                ["termux-location", "-p", "gps", "-r", "once"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                timeout=15,
            )
        except Exception:
            return None

        if proc.returncode != 0:
            return None

        try:
            data = json.loads(proc.stdout)
        except Exception:
            return None

        lat = data.get("latitude")
        lon = data.get("longitude")
        if lat is None or lon is None:
            return None

        return {
            "latitude": float(lat),
            "longitude": float(lon),
        }

    def reverse_geocode(self, latitude, longitude):
        """
        Use Nominatim reverse API to get address details for given coords.
        """
        params = {
            "lat": latitude,
            "lon": longitude,
            "format": "json",
            "addressdetails": 1,
        }
        headers = {
            "User-Agent": "Adaptheon/1.0 (Termux) - reverse geocoding client"
        }
        try:
            resp = requests.get(self.reverse_url, params=params, headers=headers, timeout=10)
        except Exception:
            return None

        if resp.status_code != 200:
            return None

        try:
            data = resp.json()
        except Exception:
            return None

        addr = data.get("address", {})
        label = data.get("display_name") or ""

        return {
            "raw": data,
            "address": addr,
            "label": label,
        }

    def get_location_details(self):
        """
        Combine GPS and reverse geocoding into a single location descriptor.
        """
        gps = self.get_gps()
        if not gps:
            return None

        rev = self.reverse_geocode(gps["latitude"], gps["longitude"])
        if not rev:
            label = "your area"
        else:
            label = rev["label"] or "your area"

        return {
            "latitude": gps["latitude"],
            "longitude": gps["longitude"],
            "label": label,
            "address": rev.get("address") if rev else {},
        }
