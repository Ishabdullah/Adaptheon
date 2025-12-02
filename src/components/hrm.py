import time

class HierarchicalReasoningMachine:
    """
    The Logic Cortex.
    Receives structured data, performs logic/planning, returns structure.
    Does not 'talk', it 'thinks'.
    """
    def __init__(self):
        pass

    def process(self, intent_data, memory_context):
        """
        The core thinking loop.
        """
        print(f"  [HRM] Analyzing Intent: {intent_data['type']}")
        
        if intent_data["type"] == "PLANNING":
            return self._generate_plan(intent_data["content"])
        
        elif intent_data["type"] == "MEMORY_WRITE":
            # Logic: Extract the fact to be saved
            fact = intent_data["content"].replace("remember", "").strip()
            return {"action": "SAVE_PREFERENCE", "key": "user_fact", "value": fact, "response": "I've etched that into my semantic memory."}
        
        elif intent_data["type"] == "MEMORY_READ":
            prefs = memory_context.get("user_preferences", {})
            return {"action": "RETRIEVE", "data": prefs, "response": f"Consulting graph... I know this about you: {prefs}"}
            
        else:
            return {"action": "CONVERSE", "response": "Processing via standard conversational loop."}

    def _generate_plan(self, content):
        """
        Symbolic logic for breaking down tasks.
        """
        steps = [
            "1. Analyze constraint parameters.",
            "2. Query Knowledge Scout for missing vars.",
            "3. Optimize execution path."
        ]
        print("  [HRM] Decomposing task...")
        time.sleep(0.5) # Simulate compute
        return {
            "action": "EXECUTE_PLAN", 
            "plan_steps": steps, 
            "response": "I have constructed a logic chain for this."
        }
