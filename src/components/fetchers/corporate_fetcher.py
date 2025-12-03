import os
import requests
from typing import Dict, Any, Optional, List


class CorporateFetcher:
    """
    Business / corporate domain fetcher.
    Uses OpenCorporates API to search companies and return core registration info.
    """

    def __init__(self):
        self.base = "https://api.opencorporates.com/v0.4"
        # Optional API token via OPENCORPORATES_API_TOKEN for higher rate limits
        self.api_token = os.environ.get("OPENCORPORATES_API_TOKEN")

    def _search_companies(self, query: str, limit: int = 3) -> Optional[List[Dict[str, Any]]]:
        url = self.base + "/companies/search"
        params: Dict[str, Any] = {
            "q": query,
            "per_page": limit,
        }
        if self.api_token:
            params["api_token"] = self.api_token
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
        results = (data.get("results") or {}).get("companies") or []
        return results[:limit]

    def _format_company(self, companies: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
        if not companies:
            return None
        cwrap = companies[0]
        c = cwrap.get("company") or {}
        name = c.get("name") or ""
        number = c.get("company_number") or ""
        juris = c.get("jurisdiction_code") or ""
        status = c.get("current_status") or ""
        incorp = c.get("incorporation_date") or ""
        addr = c.get("registered_address_in_full") or ""
        oc_url = c.get("opencorporates_url") or ""
        status_part = f" The current status is {status}." if status else ""
        incorp_part = f" Incorporated on {incorp}." if incorp else ""
        addr_part = f" Registered address: {addr}." if addr else ""
        summary = f"{name} (company number {number}) is registered in jurisdiction '{juris}'.{status_part}{incorp_part}{addr_part}"
        return {
            "status": "FOUND",
            "summary": summary,
            "confidence": 0.86,
            "url": oc_url or None,
            "metadata": {
                "source": "opencorporates",
                "name": name,
                "company_number": number,
                "jurisdiction_code": juris,
                "status": status,
                "incorporation_date": incorp,
            },
        }

    def fetch(self, query: str) -> Dict[str, Any]:
        companies = self._search_companies(query, limit=3)
        formatted = self._format_company(companies or [])
        if formatted:
            return formatted
        return {
            "status": "NOT_FOUND",
            "summary": "",
            "confidence": 0.0,
            "url": None,
            "metadata": {},
        }
