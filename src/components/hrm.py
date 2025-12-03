import time
import string


class HierarchicalReasoningMachine:
    """
    Logic Cortex (Phase 2).
    Handles planning, memory, knowledge, corrections, search hints,
    and typed queries like prices and weather.
    """

    def __init__(self):
        pass

    def process(self, intent_data, memory_context):
        intent_type = intent_data["type"]
        content = intent_data["content"]
        print("[HRM] Analyzing Intent: {}".format(intent_type))

        text_lower = content.lower()

        # Typed queries first
        if "current price of" in text_lower or "price of" in text_lower:
            # crude asset extraction: after "price of"
            raw = text_lower
            if "current price of" in raw:
                raw = raw.split("current price of", 1)[1]
            elif "price of" in raw:
                raw = raw.split("price of", 1)[1]
            asset = raw.strip().strip(string.punctuation)
            return {
                "action": "PRICE_QUERY",
                "asset": asset,
            }

        if "weather" in text_lower:
            return {
                "action": "WEATHER_QUERY",
                "location_hint": content,
            }

        if intent_type == "PLANNING":
            return self._generate_plan(content)

        elif intent_type == "MEMORY_WRITE":
            fact = content.replace("remember", "").strip()
            return {
                "action": "SAVE_PREFERENCE",
                "key": "user_fact",
                "value": fact,
                "response": "I have stored that in your preference memory.",
            }

        elif intent_type == "MEMORY_READ":
            prefs = memory_context.get("user_preferences", {})
            return {
                "action": "RETRIEVE",
                "data": prefs,
                "response": "Here is what I currently know about you: {}".format(prefs),
            }

        elif "what is" in text_lower or "define" in text_lower:
            raw = (
                text_lower
                .replace("what is", "")
                .replace("define", "")
            )
            topic = raw.strip().strip(string.punctuation)
            key = "knowledge_{}".format(topic.replace(" ", "_"))

            semantic = memory_context.get("semantic", {})
            if key in semantic:
                return {
                    "action": "RETURN_KNOWLEDGE",
                    "topic": topic
                }
            else:
                return {
                    "action": "TRIGGER_SCOUT",
                    "topic": topic,
                    "response": "I do not have this in local memory yet. Launching Knowledge Scout.",
                }

        elif intent_type == "CORRECTION":
            semantic = memory_context.get("semantic", {})
            best_topic = None
            for k in semantic.keys():
                if not k.startswith("knowledge_"):
                    continue
                name = k.replace("knowledge_", "").replace("_", " ")
                if name in text_lower:
                    best_topic = name
                    break

            return {
                "action": "VERIFY_AND_UPDATE",
                "topic": best_topic,
                "user_correction": content,
            }

        elif intent_type == "SEARCH_HINT":
            return {
                "action": "UPDATE_SEARCH_POLICY",
                "instruction": content,
            }

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
