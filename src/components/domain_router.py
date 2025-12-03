import json
import os
from typing import Dict, Any, Optional


class DomainRouter:
    """
    Routes normalized query types/domains to configured primary/secondary/tertiary sources
    from the external Super-Catalog.
    """

    def __init__(self, config_path: str = "src/config/external_sources.json"):
        self.config_path = os.path.expanduser(config_path)
        self.domains: Dict[str, Any] = {}
        self._load()

    def _load(self):
        if not os.path.exists(self.config_path):
            self.domains = {}
            return
        with open(self.config_path, "r") as f:
            self.domains = json.load(f)

    def get_domain(self, domain: str) -> Optional[Dict[str, Any]]:
        """
        Return the domain entry (with primary/secondary/tertiary) or None.
        """
        return self.domains.get(domain)

    def get_sources(self, domain: str) -> Dict[str, Any]:
        """
        Get tiered sources for a domain, with empty lists if unknown.
        Returns dict: {"primary": [...], "secondary": [...], "tertiary": [...]}
        """
        entry = self.get_domain(domain)
        if not entry:
            return {"primary": [], "secondary": [], "tertiary": []}
        return {
            "primary": entry.get("primary", []),
            "secondary": entry.get("secondary", []),
            "tertiary": entry.get("tertiary", []),
        }
