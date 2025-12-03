import os
import requests
from typing import Dict, Any, Optional


class CrimeFetcher:
    """
    Crime / justice domain fetcher.
    Uses FBI Crime Data API (UCR) for high-level offense counts by year and state.
    """

    def __init__(self):
        self.base = "https://api.usa.gov/crime/fbi/sapi"
        # Optional API key via FBI_CRIME_API_KEY (proxied through api.data.gov)
        self.api_key = os.environ.get("FBI_CRIME_API_KEY")

    def _state_offense_count(self, state_abbr: str, offense: str, year: int) -> Optional[Dict[str, Any]]:
        # Endpoint pattern from FBI Crime Data API: /api/summarized/state/{state}/{offense}/{from}/{to}
        url = f"{self.base}/api/summarized/state/{state_abbr}/{offense}/{year}/{year}"
        params: Dict[str, Any] = {}
        if self.api_key:
            params["API_KEY"] = self.api_key
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
        rows = data.get("results") or []
        return rows[0] if rows else None

    def fetch(self, query: str) -> Dict[str, Any]:
        """
        Very simple heuristic: expect pattern like 'murder rate in NY 2019' or 'robbery in CA 2020'.
        Maps a few common offense tokens to UCR offense codes.
        """
        q = query.lower()
        # Map simple tokens to FBI offense codes
        offense_map = {
            "murder": "violent-crime",
            "homicide": "violent-crime",
            "robbery": "robbery",
            "burglary": "burglary",
            "property crime": "property-crime",
            "aggravated assault": "aggravated-assault",
        }
        chosen_offense = "violent-crime"
        for token, code in offense_map.items():
            if token in q:
                chosen_offense = code
                break

        # crude state and year extraction
        state = None
        for abbr in ["AL","AK","AZ","AR","CA","CO","CT","DE","FL","GA","HI","ID","IL","IN","IA","KS","KY","LA","ME","MD","MA","MI","MN","MS","MO","MT","NE","NV","NH","NJ","NM","NY","NC","ND","OH","OK","OR","PA","RI","SC","SD","TN","TX","UT","VT","VA","WA","WV","WI","WY"]:
            if f" {abbr.lower()} " in " " + q + " ":
                state = abbr
                break
        # Try common full names for a couple of states
        if state is None:
            if "new york" in q:
                state = "NY"
            elif "california" in q:
                state = "CA"
            elif "texas" in q:
                state = "TX"

        year = None
        for tok in q.split():
            if tok.isdigit() and len(tok) == 4:
                try:
                    y = int(tok)
                    if 1985 <= y <= 2100:
                        year = y
                        break
                except Exception:
                    continue

        if not state or not year:
            return {
                "status": "NOT_FOUND",
                "summary": "",
                "confidence": 0.0,
                "url": None,
                "metadata": {},
            }

        row = self._state_offense_count(state, chosen_offense, year)
        if not row:
            return {
                "status": "NOT_FOUND",
                "summary": "",
                "confidence": 0.0,
                "url": None,
                "metadata": {},
            }

        offense_name = row.get("offense") or chosen_offense.replace("-", " ")
        value = row.get("actual") or row.get("offense_count")
        population = row.get("population")
        rate = None
        if value is not None and population:
            try:
                rate = (value / population) * 100000.0
            except Exception:
                rate = None

        val_part = f"{value:,}" if isinstance(value, int) else str(value)
        summary = f"In {year}, reported {offense_name} incidents in {state} totaled about {val_part}"
        if rate is not None:
            summary += f", or roughly {rate:.1f} incidents per 100,000 people"
        summary += "."

        url = f"https://crime-data-explorer.fr.cloud.gov/pages/explorer/state/{state}/{chosen_offense.replace('-', '_')}?year={year}"

        return {
            "status": "FOUND",
            "summary": summary,
            "confidence": 0.82,
            "url": url,
            "metadata": {
                "source": "fbi_crime_data",
                "state": state,
                "year": year,
                "offense": chosen_offense,
                "value": value,
                "population": population,
                "rate_per_100k": rate,
            },
        }
