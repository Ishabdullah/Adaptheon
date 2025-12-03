import os
import json
from typing import List, Dict, Any, Optional, Tuple
from components.semantic_utils import text_to_vector, cosine_similarity


class EmbeddingStore:
    """
    Very small in-process vector store backed by a JSON file.
    Stores documents as bag-of-words vectors using text_to_vector and supports
    top-k cosine similarity search. This is enough for local RAG-style retrieval.[web:643][web:646]
    """

    def __init__(self, path: str = "data/vector_store.json"):
        self.path = path
        self.docs: Dict[str, Dict[str, Any]] = {}
        self._load()

    def _load(self):
        os.makedirs(os.path.dirname(self.path), exist_ok=True)
        if os.path.exists(self.path):
            try:
                with open(self.path, "r") as f:
                    self.docs = json.load(f)
            except Exception:
                self.docs = {}
        else:
            self.docs = {}

    def _save(self):
        with open(self.path, "w") as f:
            json.dump(self.docs, f, indent=2)

    def add_document(self, doc_id: str, text: str, metadata: Optional[Dict[str, Any]] = None):
        """
        Store or update a document and its vector representation.
        """
        vec = text_to_vector(text)
        self.docs[doc_id] = {
            "text": text,
            "vector": {w: int(c) for w, c in vec.items()},
            "metadata": metadata or {},
        }
        self._save()

    def query(self, query_text: str, top_k: int = 3, min_score: float = 0.15) -> List[Tuple[str, float, Dict[str, Any]]]:
        """
        Return top-k (doc_id, score, payload) for documents most similar to query_text.[web:645][web:660]
        """
        if not self.docs:
            return []

        q_vec = text_to_vector(query_text)
        results: List[Tuple[str, float, Dict[str, Any]]] = []
        for doc_id, payload in self.docs.items():
            vec_dict = payload.get("vector", {})
            other_vec = {w: int(c) for w, c in vec_dict.items()}
            score = cosine_similarity(q_vec, other_vec)
            if score >= min_score:
                results.append(
                    (
                        doc_id,
                        score,
                        {
                            "text": payload.get("text", ""),
                            "metadata": payload.get("metadata", {}),
                        },
                    )
                )

        results.sort(key=lambda x: x[1], reverse=True)
        return results[:top_k]
