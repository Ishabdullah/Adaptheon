from typing import Optional, Dict, Any
from SPARQLWrapper import SPARQLWrapper, JSON  # type: ignore

from .truth_types import TruthResult, SourceTier, SourceKind, SourceTraceEntry


class WikidataClient:
    """
    Primary structured source for entity facts via Wikidata SPARQL endpoint.
    Uses SPARQLWrapper as recommended in Wikidata Python examples.
    """

    def __init__(self):
        self.endpoint = "https://query.wikidata.org/sparql"

    def _run_sparql(self, query: str) -> Optional[Dict[str, Any]]:
        sparql = SPARQLWrapper(self.endpoint)
        sparql.setQuery(query)
        sparql.setReturnFormat(JSON)
        try:
            result = sparql.query().convert()
            return result
        except Exception:
            return None

    def _entity_search(self, label: str, limit: int = 1) -> Optional[str]:
        q = (
            "SELECT ?item WHERE { "
            "?item rdfs:label "" + label.replace('"', '\\"') + ""@en . "
            "} LIMIT " + str(limit)
        )
        data = self._run_sparql(q)
        if not data:
            return None
        bindings = data.get("results", {}).get("bindings", [])
        if not bindings:
            return None
        item = bindings[0].get("item", {})
        return item.get("value")

    def _entity_summary(self, entity_iri: str) -> Optional[str]:
        q = (
            "SELECT ?label ?desc WHERE { "
            "<" + entity_iri + "> rdfs:label ?label . "
            "FILTER (lang(?label) = "en") "
            "OPTIONAL { <" + entity_iri + "> schema:description ?desc . FILTER (lang(?desc) = "en") } "
            "} LIMIT 1"
        )
        data = self._run_sparql(q)
        if not data:
            return None
        bindings = data.get("results", {}).get("bindings", [])
        if not bindings:
            return None
        row = bindings[0]
        label = row.get("label", {}).get("value", "")
        desc = row.get("desc", {}).get("value", "")
        if desc:
            return label + " — " + desc
        return label

    def lookup_entity(self, query: str) -> Optional[TruthResult]:
        """
        Try to resolve a general entity (person, organization, place, etc.)
        into a canonical summary using Wikidata.
        """
        entity_iri = self._entity_search(query)
        if not entity_iri:
            return None

        summary = self._entity_summary(entity_iri)
        if not summary:
            return None

        trace = [
            SourceTraceEntry(
                tier=SourceTier.PRIMARY,
                kind=SourceKind.WIKIDATA,
                name="Wikidata",
                url=entity_iri,
                confidence=0.85,
                note="Entity label and description from Wikidata"
            )
        ]

        return TruthResult(
            status="FOUND",
            query=query,
            canonical_summary=summary,
            confidence=0.85,
            primary_source=SourceKind.WIKIDATA,
            tier=SourceTier.PRIMARY,
            snippets=[summary],
            source_trace=trace,
            violations=[],
            metadata={"entity_iri": entity_iri},
        )
