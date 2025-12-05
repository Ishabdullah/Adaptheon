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

        # Identity questions - handle first
        if self._is_identity_question(text_lower):
            return self._handle_identity(text_lower)

        # Typed queries
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

    def _is_identity_question(self, text: str) -> bool:
        """Check if query is asking about Adaptheon's identity"""
        identity_patterns = [
            "who are you",
            "what are you",
            "what can you do",
            "what do you do",
            "how do you work",
            "how does this work",
            "tell me about yourself",
            "what is adaptheon",
            "what's adaptheon",
        ]
        return any(pattern in text for pattern in identity_patterns)

    def _handle_identity(self, text: str) -> dict:
        """Generate natural language response to identity questions"""
        response = ""

        if "who are you" in text or "what are you" in text or "what is adaptheon" in text or "what's adaptheon" in text:
            response = (
                "I am Adaptheon, a modular reasoning system built to explore, learn, and adapt. "
                "I combine memory systems, knowledge retrieval, and local language models to provide "
                "contextual, on-device intelligence. My architecture includes episodic memory for conversations, "
                "semantic memory for facts, and a Knowledge Scout that searches 24+ specialized data sources "
                "including Wikipedia, arXiv, GitHub, financial markets, weather services, and more."
            )

        elif "what can you do" in text or "what do you do" in text:
            response = (
                "I can help with many tasks: (1) Answer questions by searching specialized knowledge sources, "
                "(2) Get real-time data like stock prices, cryptocurrency values, and weather, "
                "(3) Remember our conversations and learn from corrections you provide, "
                "(4) Search academic papers, GitHub repositories, books, music, sports data, and more, "
                "(5) Plan multi-step tasks and reason about complex queries, "
                "(6) Track your preferences and adapt my responses based on what you've taught me. "
                "I work entirely on your device using local LLMs for privacy."
            )

        elif "how do you work" in text or "how does this work" in text:
            response = (
                "My architecture has several layers: (1) Intent Analysis - I parse your question to understand "
                "what you're asking, (2) Memory Systems - I check episodic (conversation history), semantic "
                "(learned facts), and preference layers, (3) Knowledge Scout - Routes queries to 24+ specialized "
                "fetchers (Wikipedia, arXiv, GitHub, finance APIs, weather, sports, etc.), (4) Reasoning Engine (HRM) - "
                "Plans multi-step tasks and coordinates responses, (5) Local LLM - Uses Qwen or Gemma models "
                "running via llama.cpp for natural language generation. Everything runs on-device for privacy."
            )

        elif "tell me about yourself" in text:
            response = (
                "I'm Adaptheon Phase 2.0, an experimental adaptive reasoning system. I was designed to combine "
                "the best of local AI (privacy, speed) with web-scale knowledge (accuracy, freshness). "
                "I maintain multiple memory layers, can search dozens of specialized data sources, "
                "and learn from your corrections. My goal is to be a helpful, transparent AI assistant that "
                "gets smarter over time by learning from our interactions."
            )

        else:
            # Fallback for other identity-related questions
            response = (
                "I'm Adaptheon, your on-device AI assistant with access to 24+ knowledge sources "
                "and multi-layered memory systems."
            )

        return {
            "action": "IDENTITY_RESPONSE",
            "response": response
        }
