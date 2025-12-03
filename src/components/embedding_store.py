import os
from typing import List, Dict, Any, Optional
from uuid import uuid4

from qdrant_client import QdrantClient  # type: ignore


class EmbeddingStore:
    """
    Vector memory using Qdrant local mode with FastEmbed.
    Stores and searches text chunks for semantic similarity.
    """

    def __init__(self, path: Optional[str] = None, collection_name: str = "semantic_knowledge"):
        base_path = path or "data/vector_store"
        os.makedirs(base_path, exist_ok=True)
        self.collection_name = collection_name
        self.client = QdrantClient(path=base_path)

    def add_document(self, doc_id: Optional[str], text: str, metadata: Optional[Dict[str, Any]] = None):
        if not text:
            return
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
            # Swallow errors to avoid breaking main flow
            return

    def search_similar_text(self, query: str, limit: int = 5) -> List[Dict[str, Any]]:
        if not query:
            return []
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
