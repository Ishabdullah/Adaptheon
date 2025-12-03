import os
from typing import List, Dict, Any, Optional

try:
    from qdrant_client import QdrantClient  # type: ignore
    HAVE_QDRANT = True
except Exception:
    QdrantClient = None  # type: ignore
    HAVE_QDRANT = False


class EmbeddingStore:
    """
    Vector memory.
    If qdrant-client is available, uses Qdrant local mode with FastEmbed.
    Otherwise falls back to an in-memory list so the system still runs.
    """

    def __init__(self, path: Optional[str] = None, collection_name: str = "semantic_knowledge"):
        self.collection_name = collection_name
        self.memory_points: List[Dict[str, Any]] = []

        if HAVE_QDRANT:
            base_path = path or "data/vector_store"
            os.makedirs(base_path, exist_ok=True)
            try:
                self.client = QdrantClient(path=base_path)
            except Exception:
                self.client = None
        else:
            self.client = None

    def add_document(self, doc_id: Optional[str], text: str, metadata: Optional[Dict[str, Any]] = None):
        if not text:
            return
        if self.client is None:
            # Fallback: store in simple list
            self.memory_points.append(
                {
                    "id": doc_id,
                    "text": text,
                    "metadata": metadata or {},
                }
            )
            return

        from uuid import uuid4

        if doc_id is None:
            doc_id = uuid4().hex
        docs = [text]
        metas = [metadata or {}]
        ids = [doc_id]
        try:
            self.client.add(
                collection_name=self.collection_name,
                documents=docs,
                metadata=metas,
                ids=ids,
            )
        except Exception:
            return

    def search_similar_text(self, query: str, limit: int = 5) -> List[Dict[str, Any]]:
        if not query:
            return []

        if self.client is None:
            # Very simple fallback: return recent memory points, no real similarity
            return self.memory_points[-limit:]

        try:
            result = self.client.query(
                collection_name=self.collection_name,
                query_text=query,
                limit=limit,
            )
        except Exception:
            return []

        hits: List[Dict[str, Any]] = []
        for point in getattr(result, "points", []):
            payload = getattr(point, "payload", {}) or {}
            score = getattr(point, "score", 0.0)
            hits.append(
                {
                    "id": getattr(point, "id", None),
                    "payload": payload,
                    "score": score,
                }
            )
        return hits
