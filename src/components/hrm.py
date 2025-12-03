import time
import string


class HierarchicalReasoningMachine:
    """
    Logic Cortex (Phase 2).
    Handles planning, memory, knowledge, corrections, search hints,
    typed queries like prices and weather, and basic time-awareness.
    """

    def __init__(self):
        pass

    def _is_time_sensitive(self, text_lower):
        keywords = [
            "current",
            "today",
            "right now",
            "now",
            "latest",
            "recent",
            "this week",
            "this month",
            "this year",
            "tonight",
        ]
        for kw in keywords:
            if kw in text_lower:
                return True
        if text_lower.startswith("who is"):
            return True
        if "who won" in text_lower or "score of" in text_lower or "final score" in text_lower:
            return True
        return False

    def process(self, intent_data, memory_context):
        intent_type = intent_data["type"]
        content = intent_data["content"]
        print("[HRM] Analyzing Intent: {}".format(intent_type))

        text_lower = content.lower()
        time_sensitive = self._is_time_sensitive(text_lower)

        # Special self-queries
        if "what is my name" in text_lower or "do you know my name" in text_lower:
            return {
                "action": "GET_USER_NAME",
            }

        # SEARCH_HINT: handle before typed tools so it doesn't get treated as PRICE_QUERY
        if intent_type == "SEARCH_HINT":
            return {
                "action": "UPDATE_SEARCH_POLICY",
                "instruction": content,
            }

        # Typed queries only for CHAT, not for SEARCH_HINT/MEMORY/etc.
        if intent_type == "CHAT":
            if "current price of" in text_lower or "price of" in text_lower:
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

        # Time-sensitive "who is ..." knowledge queries
        if text_lower.startswith("who is"):
            raw = text_lower.replace("who is", "", 1)
            topic = raw.strip().strip(string.punctuation)
            return {
                "action": "TRIGGER_SCOUT",
                "topic": topic,
                "time_sensitive": True,
            }

        # Sports / event queries
        if "who won" in text_lower or "score of" in text_lower or "final score" in text_lower:
            topic = content.strip()
            return {
                "action": "TRIGGER_SCOUT",
                "topic": topic,
                "time_sensitive": True,
            }

        if intent_type == "PLANNING":
            return self._generate_plan(content)

        elif intent_type == "MEMORY_WRITE":
            # Special handling for "my name is ..."
            if "my name is" in text_lower:
                after = text_lower.split("my name is", 1)[1].strip()
                # Keep original casing from content by aligning indices if possible
                idx = content.lower().find("my name is")
                if idx >= 0:
                    name_part = content[idx + len("my name is"):].strip()
                else:
                    name_part = after
                name_clean = name_part.strip(string.punctuation + " ")
                return {
                    "action": "SAVE_PREFERENCE",
                    "key": "user_name",
                    "value": name_clean,
                    "response": "I will remember that your name is {}.".format(name_clean),
                }

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
            if not time_sensitive and key in semantic:
                return {
                    "action": "RETURN_KNOWLEDGE",
                    "topic": topic
                }
            else:
                return {
                    "action": "TRIGGER_SCOUT",
                    "topic": topic,
                    "time_sensitive": time_sensitive,
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
