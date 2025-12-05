"""
Wikidata Fetcher - Structured Knowledge Base
Production-grade SPARQL queries for factual information
"""

from typing import Dict, Any
from .base_fetcher import BaseFetcher, FetchResult, FetchStatus

try:
    from SPARQLWrapper import SPARQLWrapper, JSON
    SPARQL_AVAILABLE = True
except ImportError:
    SPARQL_AVAILABLE = False

class WikidataFetcher(BaseFetcher):
    """
    Fetches structured knowledge from Wikidata using SPARQL.
    Excellent for: facts, dates, relationships, identifiers
    """

    def _setup(self):
        self.endpoint = "https://query.wikidata.org/sparql"
        if SPARQL_AVAILABLE:
            self.sparql = SPARQLWrapper(self.endpoint)
            self.sparql.setReturnFormat(JSON)
            self.sparql.agent = 'Adaptheon/2.0'

    def fetch(self, query: str) -> FetchResult:
        """
        Query Wikidata for structured knowledge
        """
        if not SPARQL_AVAILABLE:
            return FetchResult(
                status=FetchStatus.ERROR,
                data={},
                error="SPARQLWrapper not installed"
            )

        try:
            # Try to identify what the query is asking for
            query_lower = query.lower()

            # Example: "who is the president of the united states"
            if "president" in query_lower and "united states" in query_lower:
                return self._get_current_us_president()

            # Example: "population of tokyo"
            if "population" in query_lower:
                location = self._extract_location(query)
                if location:
                    return self._get_population(location)

            # Example: "who is X" or "what is X"
            if query_lower.startswith(("who is", "what is")):
                entity = query[7:].strip().strip('?')
                return self._get_entity_description(entity)

            # Fallback: search for any mention
            return self._search_entity(query)

        except Exception as e:
            return FetchResult(
                status=FetchStatus.ERROR,
                data={},
                error=str(e)
            )

    def _get_current_us_president(self) -> FetchResult:
        """Get current US president from Wikidata"""
        sparql_query = """
        SELECT ?personLabel WHERE {
          wd:Q30 p:P6 ?statement.
          ?statement ps:P6 ?person.
          FILTER NOT EXISTS { ?statement pq:P582 ?end }
          SERVICE wikibase:label { bd:serviceParam wikibase:language "en". }
        }
        LIMIT 1
        """

        try:
            self.sparql.setQuery(sparql_query)
            results = self.sparql.query().convert()

            if results.get("results", {}).get("bindings"):
                person = results["results"]["bindings"][0]["personLabel"]["value"]
                return FetchResult(
                    status=FetchStatus.FOUND,
                    data={"president": person, "country": "United States"},
                    summary=f"The current President of the United States is {person}.",
                    confidence=0.95,
                    source="wikidata",
                    url="https://www.wikidata.org/wiki/Q30"
                )

        except Exception as e:
            pass

        return FetchResult(
            status=FetchStatus.NOT_FOUND,
            data={},
            confidence=0.0
        )

    def _get_population(self, location: str) -> FetchResult:
        """Get population for a location"""
        # Simplified - in production would do entity resolution first
        sparql_query = f"""
        SELECT ?cityLabel ?population WHERE {{
          ?city ?label "{location}"@en.
          ?city wdt:P1082 ?population.
          SERVICE wikibase:label {{ bd:serviceParam wikibase:language "en". }}
        }}
        ORDER BY DESC(?population)
        LIMIT 1
        """

        try:
            self.sparql.setQuery(sparql_query)
            results = self.sparql.query().convert()

            if results.get("results", {}).get("bindings"):
                binding = results["results"]["bindings"][0]
                city = binding["cityLabel"]["value"]
                pop = binding["population"]["value"]
                return FetchResult(
                    status=FetchStatus.FOUND,
                    data={"location": city, "population": int(pop)},
                    summary=f"The population of {city} is approximately {int(pop):,}.",
                    confidence=0.85,
                    source="wikidata"
                )

        except Exception:
            pass

        return FetchResult(status=FetchStatus.NOT_FOUND, data={}, confidence=0.0)

    def _get_entity_description(self, entity: str) -> FetchResult:
        """Get description of an entity"""
        sparql_query = f"""
        SELECT ?itemLabel ?desc WHERE {{
          ?item ?label "{entity}"@en.
          ?item schema:description ?desc.
          FILTER (lang(?desc) = "en")
          SERVICE wikibase:label {{ bd:serviceParam wikibase:language "en". }}
        }}
        LIMIT 1
        """

        try:
            self.sparql.setQuery(sparql_query)
            results = self.sparql.query().convert()

            if results.get("results", {}).get("bindings"):
                binding = results["results"]["bindings"][0]
                label = binding.get("itemLabel", {}).get("value", entity)
                desc = binding.get("desc", {}).get("value", "")
                return FetchResult(
                    status=FetchStatus.FOUND,
                    data={"entity": label, "description": desc},
                    summary=desc,
                    confidence=0.80,
                    source="wikidata"
                )

        except Exception:
            pass

        return FetchResult(status=FetchStatus.NOT_FOUND, data={}, confidence=0.0)

    def _search_entity(self, query: str) -> FetchResult:
        """Fallback: basic entity search"""
        # Simplified search - production would use Wikidata API
        return FetchResult(
            status=FetchStatus.NOT_FOUND,
            data={},
            confidence=0.0
        )

    def _extract_location(self, query: str) -> str:
        """Extract location name from query"""
        # Simple extraction - in production would use NER
        query_lower = query.lower()
        if "of" in query_lower:
            parts = query_lower.split("of")
            if len(parts) > 1:
                return parts[1].strip().strip('?').title()
        return ""
