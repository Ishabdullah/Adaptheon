import json
import time

class AdaptheonCore:
    """
    Minimal core for on-device adaptive reasoning and memory.

    This class simulates an Adaptive Core capable of storing contextual 
    memory and performing basic, state-based reasoning.
    """
    
    # Simple dictionary to simulate persistent memory
    MEMORY_STORE = {}
    
    def __init__(self, user_id: str):
        # A unique identifier for the user or device session
        self.user_id = user_id
        # Load memory on startup (or initialize if non-existent)
        self._load_memory()

    def _load_memory(self):
        """Simulates loading memory from disk (placeholder)."""
        print(f"[{time.time():.2f}] Core initialized for User: {self.user_id}")
        if not self.MEMORY_STORE:
             self.MEMORY_STORE = {
                "last_context": "Starting fresh.",
                "reasoning_cycles": 0,
                "timestamp": time.time()
            }
        print(f"  > Loaded Memory: {json.dumps(self.MEMORY_STORE)}")

    def store_context(self, new_data: dict):
        """Stores new context into the memory."""
        self.MEMORY_STORE["last_context"] = new_data.get("context", self.MEMORY_STORE["last_context"])
        self.MEMORY_STORE["timestamp"] = time.time()
        print(f"[{time.time():.2f}] Stored new context.")

    def perform_reasoning(self, input_query: str) -> str:
        """
        Simulates basic reasoning based on the current context/memory.
        """
        self.MEMORY_STORE["reasoning_cycles"] += 1
        last_context = self.MEMORY_STORE["last_context"]
        cycles = self.MEMORY_STORE["reasoning_cycles"]
        
        # Simple rule-based reasoning for MVP
        if "hello" in input_query.lower():
            response = f"Hello! I remember my last context was: '{last_context}'. This is cycle #{cycles}."
        elif "forget" in input_query.lower():
             response = "Context reset initiated."
             self.store_context({"context": "Fresh start after reset."})
        else:
            response = f"Query received. Current context: '{last_context}'. Waiting for further instructions."
        
        return response

if __name__ == "__main__":
    # Example Usage
    core = AdaptheonCore(user_id="Ishabdullah-S24U")
    
    # 1. First interaction
    response1 = core.perform_reasoning("Hi there! What's the plan today?")
    print(f"\n[Response 1]: {response1}")
    
    # 2. Store new information (new context)
    core.store_context({"context": "The primary objective is mobile AI optimization."})
    
    # 3. Second interaction using the new context
    response2 = core.perform_reasoning("Is the project focused on speed?")
    print(f"\n[Response 2]: {response2}")
    
    # 4. Third interaction
    response3 = core.perform_reasoning("Forget everything.")
    print(f"\n[Response 3]: {response3}")
