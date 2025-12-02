import time
import string

class HierarchicalReasoningMachine:
    """
    Logic Cortex (Phase 1.5).
    Can:
    - Plan
    - Read/write memory
    - Decide when to trigger Knowledge Scout
    - Reuse known facts from semantic memory
    """
    def __init__(self):
        pass

    def process(self, intent_data, memory_context):
        intent_type = intent_data["type"]
        content = intent_data["content"]
        print("[HRM] Analyzing Intent: {}".format(intent_type))

        # 1. Planning
        if intent_type == "PLANNING":
            return self._generate_plan(content)

        # 2. Memory write (simple preference / fact)
        elif intent_type == "MEMORY_WRITE":
            fact = content.replace("remember", "").strip()
            return {
                "action": "SAVE_PREFERENCE",
                "key": "user_fact",
                "value": fact,
                "response": "I have stored that in your preference memory.",
            }

        # 3. Memory read
        elif intent_type == "MEMORY_READ":
            prefs = memory_context.get("user_preferences", {})
            return {
                "action": "RETRIEVE",
                "data": prefs,
                "response": "Here is what I currently know about you: {}".format(prefs),
            }

        # 4. Knowledge query: "what is X" / "define X"
        elif "what is" in content.lower() or "define" in content.lower():
            raw = (
                content.lower()
                .replace("what is", "")
                .replace("define", "")
            )
            topic = raw.strip().strip(string.punctuation)
            key = "knowledge_{}".format(topic.replace(" ", "_"))

            semantic = memory_context.get("semantic", {})
            if key in semantic:
                # We know this topic; Meta-Core will decide how to phrase the answer
                return {
                    "action": "RETURN_KNOWLEDGE",
                    "topic": topic
                }
            else:
                # Not known yet → trigger Knowledge Scout
                return {
                    "action": "TRIGGER_SCOUT",
                    "topic": topic,
                    "response": "I do not have this in local memory yet. Launching Knowledge Scout.",
                }

        # 5. Default conversational path
        else:
            return {
                "action": "CONVERSE",
                "response": "Processing via standard conversational loop.",
            }

    def _generate_plan(self, content):
        steps = [
            "Analyze constraint parameters.",
            "Query Knowledge Scout for missing variables.",
            "Optimize execution path based on available knowledge.",
        ]
        print("[HRM] Decomposing task into {} steps.".format(len(steps)))
        time.sleep(0.5)
        return {
            "action": "EXECUTE_PLAN",
            "plan_steps": steps,
            "response": "I have constructed a basic plan for this task.",
        }
