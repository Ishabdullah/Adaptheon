import json
import os
import datetime
from components.semantic_utils import text_to_vector

class MemorySystem:
    def __init__(self):
        self.mem_path = "data/memory/"
        self.layers = {
            "episodic": [],
            "semantic": {},      # concept / fact store
            "procedural": [],
            "preference": {},
            "graph_context": []
        }
        self.load_memory()

    def load_memory(self):
        path = os.path.join(self.mem_path, "core_memory.json")
        if os.path.exists(path):
            with open(path, "r") as f:
                self.layers = json.load(f)
        else:
            print("[System] Creating new Neural Pathways...")
            self.save_memory()

    def save_memory(self):
        os.makedirs(self.mem_path, exist_ok=True)
        path = os.path.join(self.mem_path, "core_memory.json")
        with open(path, "w") as f:
            json.dump(self.layers, f, indent=4)

    def add_episodic(self, user_input, system_response):
        entry = {
            "timestamp": str(datetime.datetime.now()),
            "input": user_input,
            "response": system_response,
        }
        self.layers["episodic"].append(entry)
        if len(self.layers["episodic"]) > 50:
            self.layers["episodic"].pop(0)
        self.save_memory()

    def update_preference(self, key, value):
        self.layers["preference"][key] = value
        self.save_memory()

    def add_semantic(self, key, summary, metadata=None):
        """
        Store factual knowledge in semantic memory, with a tiny vector
        representation for similarity search.
        """
        if metadata is None:
            metadata = {}
        # Precompute a simple bag-of-words vector
        vec = text_to_vector(summary)
        # Convert Counter to plain dict for JSON
        vec_dict = {k: int(v) for k, v in vec.items()}

        self.layers["semantic"][key] = {
            "summary": summary,
            "metadata": metadata,
            "timestamp": str(datetime.datetime.now()),
            "vector": vec_dict,
        }
        self.save_memory()

    def get_semantic(self, key):
        return self.layers["semantic"].get(key)

    def get_context(self):
        return {
            "recent_history": self.layers["episodic"][-3:],
            "user_preferences": self.layers["preference"],
            "semantic": self.layers["semantic"],
        }
