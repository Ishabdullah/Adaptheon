import os
import json
from typing import Dict, Any, List


class GraphMemory:
    """
    Simple in-process knowledge graph for entities and relations.
    Stores nodes and edges in JSON and can return 1–2 hop neighborhoods
    around a topic for GraphRAG-style retrieval.[web:647][web:489]
    """

    def __init__(self, path: str = "data/graph/memory_graph.json"):
        self.path = path
        self.graph: Dict[str, Any] = {
            "nodes": {},
            "edges": [],
        }
        self._load()

    def _load(self):
        os.makedirs(os.path.dirname(self.path), exist_ok=True)
        if os.path.exists(self.path):
            try:
                with open(self.path, "r") as f:
                    self.graph = json.load(f)
            except Exception:
                self.graph = {"nodes": {}, "edges": []}
        else:
            self.graph = {"nodes": {}, "edges": []}

    def _save(self):
        with open(self.path, "w") as f:
            json.dump(self.graph, f, indent=2)

    def upsert_entity_from_truth(self, topic: str, scout_result: Dict[str, Any]):
        """
        Store or update a node for 'topic' plus a lightweight edge to its primary source.[web:483][web:491]
        """
        nodes = self.graph["nodes"]
        if topic not in nodes:
            nodes[topic] = {
                "label": topic,
                "summary": scout_result.get("summary", ""),
                "metadata": {
                    "source": scout_result.get("source"),
                    "confidence": scout_result.get("confidence"),
                    "url": scout_result.get("url"),
                },
            }
        else:
            node = nodes[topic]
            node["summary"] = scout_result.get("summary", node.get("summary", ""))
            meta = node.get("metadata", {})
            meta.update(
                {
                    "source": scout_result.get("source"),
                    "confidence": scout_result.get("confidence"),
                    "url": scout_result.get("url"),
                }
            )
            node["metadata"] = meta

        # Simple edge: topic -> primary_source
        src = topic
        dst = scout_result.get("source") or "external_source"
        edge = {
            "source": src,
            "target": dst,
            "predicate": "SUPPORTED_BY",
        }
        self.graph["edges"].append(edge)
        self._save()

    def neighborhood(self, topic: str, max_hops: int = 1) -> Dict[str, Any]:
        """
        Return a small neighborhood (nodes + edges) around topic for answer conditioning.[web:489][web:663]
        """
        nodes = self.graph["nodes"]
        edges = self.graph["edges"]
        if topic not in nodes:
            return {"nodes": {}, "edges": []}

        included_nodes = {topic: nodes[topic]}
        included_edges: List[Dict[str, Any]] = []

        for e in edges:
            if e["source"] == topic or e["target"] == topic:
                included_edges.append(e)
                if e["source"] in nodes:
                    included_nodes.setdefault(e["source"], nodes[e["source"]])
                if e["target"] in nodes:
                    included_nodes.setdefault(e["target"], nodes[e["target"]])

        return {
            "nodes": included_nodes,
            "edges": included_edges,
        }
