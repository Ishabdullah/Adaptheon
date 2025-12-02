import json
import os
import datetime

class MemorySystem:
    def __init__(self):
        self.mem_path = "data/memory/"
        self.layers = {
            "episodic": [],
            "semantic": {},
            "procedural": [],
            "preference": {},
            "graph_context": []
        }
        self.load_memory()

    def load_memory(self):
        # MVP: Load from JSON. Phase 2: Move to Graph DB
        if os.path.exists(self.mem_path + "core_memory.json"):
            with open(self.mem_path + "core_memory.json", "r") as f:
                self.layers = json.load(f)
        else:
            print("[System] Creating new Neural Pathways...")
            self.save_memory()

    def save_memory(self):
        if not os.path.exists(self.mem_path):
            os.makedirs(self.mem_path)
        with open(self.mem_path + "core_memory.json", "w") as f:
            json.dump(self.layers, f, indent=4)

    def add_episodic(self, user_input, system_response):
        """Phase 1: Store conversation turns"""
        entry = {
            "timestamp": str(datetime.datetime.now()),
            "input": user_input,
            "response": system_response
        }
        self.layers["episodic"].append(entry)
        # Keep minimal for MVP (Last 50 interactions)
        if len(self.layers["episodic"]) > 50:
            self.layers["episodic"].pop(0)
        self.save_memory()

    def update_preference(self, key, value):
        """Phase 1: Learn user likes/dislikes"""
        self.layers["preference"][key] = value
        self.save_memory()

    def get_context(self):
        """Returns the working context for the Meta-Core"""
        return {
            "recent_history": self.layers["episodic"][-3:],
            "user_preferences": self.layers["preference"]
        }
