import requests
from typing import Optional, Dict, Any


class OfficeHolderClient:
    """
    Minimal Wikidata SPARQL client for 'current office-holder' questions.
    Examples: 'governor of Texas', 'president of France', 'mayor of London'.
    """

    def __init__(self):
        self.endpoint = "https://query.wikidata.org/sparql"
        self.headers = {
            "User-Agent": "Adaptheon/1.0 (on-device truth engine; AI research)",
            "Accept": "application/sparql-results+json",
        }

    def _run_sparql(self, query: str) -> Optional[Dict[str, Any]]:
        try:
            resp = requests.get(
                self.endpoint,
                params={"query": query, "format": "json"},
                headers=self.headers,
                timeout=15,
            )
        except Exception:
            return None
        if resp.status_code != 200:
            return None
        try:
            return resp.json()
        except Exception:
            return None

    def _build_query(self, office_label: str, area_label: Optional[str]) -> str:
        """
        Uses position held (P39) with end time (P582) absent to approximate 'current' office holder.[web:628][web:637]
        """
        if area_label:
            area_filter = f'VALUES ?areaLabelRaw {{"{area_label}"@en}}'
        else:
            area_filter = ""

        return f"""
        SELECT ?person ?personLabel ?officeLabel ?areaLabel ?start WHERE {{
          ?person p:P39 ?pos .
          ?pos ps:P39 ?office .
          OPTIONAL {{ ?pos pq:P131 ?area . }}
          OPTIONAL {{ ?pos pq:P580 ?start . }}
          FILTER NOT EXISTS {{ ?pos pq:P582 ?end . }}

          ?office rdfs:label ?officeLabel FILTER (LANG(?officeLabel) = "en") .
          FILTER(CONTAINS(LCASE(STR(?officeLabel)), LCASE("{office_label}")))

          OPTIONAL {{
            ?area rdfs:label ?areaLabel FILTER (LANG(?areaLabel) = "en") .
          }}

          {area_filter}

          SERVICE wikibase:label {{ bd:serviceParam wikibase:language "en". }}
        }}
        ORDER BY DESC(?start)
        LIMIT 1
        """

    def lookup_current_holder(self, office_label: str, area_label: Optional[str] = None) -> Optional[Dict[str, Any]]:
        sparql = self._build_query(office_label, area_label)
        data = self._run_sparql(sparql)
        if not data:
            return None
        bindings = data.get("results", {}).get("bindings", [])
        if not bindings:
            return None
        row = bindings[0]

        def get_val(name: str) -> Optional[str]:
            v = row.get(name)
            if not v:
                return None
            return v.get("value")

        person = get_val("personLabel")
        office = get_val("officeLabel")
        area = get_val("areaLabel") or area_label
        start = get_val("start")
        person_uri = get_val("person")

        return {
            "person": person,
            "office": office,
            "area": area,
            "start": start,
            "person_uri": person_uri,
        }
