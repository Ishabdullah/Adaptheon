import time

class HierarchicalReasoningMachine:
    """
    The Logic Cortex (Phase 1 Upgraded).
    Now capable of identifying 'Unknowns' and requesting Research.
    """
    def __init__(self):
        pass

    def process(self, intent_data, memory_context):
        intent_type = intent_data["type"]
        print(f"  [HRM] Analyzing Intent: {intent_type}")
        
        # 1. PLANNING
        if intent_type == "PLANNING":
            return self._generate_plan(intent_data["content"])
        
        # 2. MEMORY WRITE
        elif intent_type == "MEMORY_WRITE":
            fact = intent_data["content"].replace("remember", "").strip()
            return {
                "action": "SAVE_PREFERENCE", 
                "key": "user_fact", 
                "value": fact, 
                "response": "I've etched that into my semantic memory."
            }
        
        # 3. MEMORY READ
        elif intent_type == "MEMORY_READ":
            prefs = memory_context.get("user_preferences", {})
            return {
                "action": "RETRIEVE", 
                "data": prefs, 
                "response": f"Consulting graph... I know this about you: {prefs}"
            }

        # 4. RESEARCH / LEARNING (New)
        elif "what is" in intent_data["content"] or "define" in intent_data["content"]:
            # Logic: If I don't have it in memory, I must scout.
            topic = intent_data["content"].replace("what is", "").replace("define", "").strip()
            return {
                "action": "TRIGGER_SCOUT",
                "topic": topic,
                "response": "I do not have this in local memory. Deploying Knowledge Scout."
            }
            
        # 5. DEFAULT CONVERSATION
        else:
            return {"action": "CONVERSE", "response": "Processing via standard conversational loop."}

    def _generate_plan(self, content):
        steps = [
            "1. Analyze constraint parameters.",
            "2. Query Knowledge Scout for missing vars.",
            "3. Optimize execution path."
        ]
        time.sleep(0.5) 
        return {
            "action": "EXECUTE_PLAN", 
            "plan_steps": steps, 
            "response": "I have constructed a logic chain for this."
        }
