import os
import sqlite3
from typing import Optional, Dict, Any, List
from datetime import datetime


class GraphMemory:
    """
    Long-term graph memory using SQLite.
    Stores nodes (entities/topics) and edges (relationships).
    """

    def __init__(self, db_path: str = "data/graph/graph.db"):
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        self.db_path = db_path
        self._init_db()

    def _init_db(self):
        conn = sqlite3.connect(self.db_path)
        cur = conn.cursor()
        cur.execute(
            "CREATE TABLE IF NOT EXISTS nodes ("
            "id INTEGER PRIMARY KEY AUTOINCREMENT,"
            "key TEXT UNIQUE,"
            "label TEXT,"
            "type TEXT,"
            "created_at TEXT"
            ")"
        )
        cur.execute(
            "CREATE TABLE IF NOT EXISTS edges ("
            "id INTEGER PRIMARY KEY AUTOINCREMENT,"
            "src INTEGER,"
            "dst INTEGER,"
            "relation TEXT,"
            "weight REAL,"
            "created_at TEXT,"
            "FOREIGN KEY(src) REFERENCES nodes(id),"
            "FOREIGN KEY(dst) REFERENCES nodes(id)"
            ")"
        )
        conn.commit()
        conn.close()

    def _get_or_create_node(self, key: str, label: Optional[str], node_type: str) -> int:
        conn = sqlite3.connect(self.db_path)
        cur = conn.cursor()
        cur.execute("SELECT id FROM nodes WHERE key = ?", (key,))
        row = cur.fetchone()
        if row:
            node_id = row[0]
        else:
            ts = datetime.utcnow().isoformat()
            cur.execute(
                "INSERT INTO nodes (key, label, type, created_at) VALUES (?, ?, ?, ?)",
                (key, label or key, node_type, ts),
            )
            node_id = cur.lastrowid
            conn.commit()
        conn.close()
        return node_id

    def add_edge(self, src_key: str, dst_key: str, relation: str, weight: float = 1.0):
        src_id = self._get_or_create_node(src_key, src_key, "topic")
        dst_id = self._get_or_create_node(dst_key, dst_key, "entity")
        conn = sqlite3.connect(self.db_path)
        cur = conn.cursor()
        ts = datetime.utcnow().isoformat()
        cur.execute(
            "INSERT INTO edges (src, dst, relation, weight, created_at) VALUES (?, ?, ?, ?, ?)",
            (src_id, dst_id, relation, weight, ts),
        )
        conn.commit()
        conn.close()

    def upsert_entity_from_truth(self, topic: str, truth: Dict[str, Any]):
        """
        Store topic and primary source link into graph from a TruthResult-like dict.
        """
        topic_key = "topic:" + topic.replace(" ", "_")
        self._get_or_create_node(topic_key, topic, "topic")

        meta = truth.get("truth_result")
        if not meta:
            return
        entity_iri = None
        try:
            entity_iri = meta.metadata.get("entity_iri")
        except Exception:
            entity_iri = None

        if entity_iri:
            src_key = topic_key
            dst_key = "entity:" + entity_iri
            self.add_edge(src_key, dst_key, "HAS_ENTITY", 1.0)

    def neighbors(self, topic: str, limit: int = 10) -> List[Dict[str, Any]]:
        topic_key = "topic:" + topic.replace(" ", "_")
        conn = sqlite3.connect(self.db_path)
        cur = conn.cursor()
        cur.execute("SELECT id FROM nodes WHERE key = ?", (topic_key,))
        row = cur.fetchone()
        if not row:
            conn.close()
            return []
        topic_id = row[0]
        cur.execute(
            "SELECT n2.key, n2.label, e.relation, e.weight "
            "FROM edges e "
            "JOIN nodes n2 ON e.dst = n2.id "
            "WHERE e.src = ? "
            "ORDER BY e.weight DESC, e.id DESC "
            "LIMIT ?",
            (topic_id, limit),
        )
        rows = cur.fetchall()
        conn.close()
        out: List[Dict[str, Any]] = []
        for k, label, rel, w in rows:
            out.append(
                {
                    "key": k,
                    "label": label,
                    "relation": rel,
                    "weight": w,
                }
            )
        return out
