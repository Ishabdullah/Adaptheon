import time
import string
from components.temporal_awareness import detect_temporal_intent, should_use_external_sources


class HierarchicalReasoningMachine:
    """
    Logic Cortex (Phase 2).
    Handles planning, memory, knowledge, corrections, search hints,
    and typed queries like prices and weather.
    Enhanced with sports domain detection and identity/status question handling.
    """

    def __init__(self):
        pass

    def _is_time_sensitive_identity_question(self, text_lower: str) -> tuple:
        """
        Detect questions asking for current identity or status.
        These are always time-sensitive because the answer changes over time.

        Returns: (bool, str) - (is_identity_question, reason)
        """
        # Role/position queries (inherently status-based and time-sensitive)
        role_keywords = [
            "quarterback", "qb", "pitcher", "coach", "manager",
            "ceo", "president", "governor", "mayor",
            "captain", "leader", "head coach", "starting", "starter"
        ]

        for role in role_keywords:
            if role in text_lower:
                return True, f"role_query:{role}"

        # Present tense identity patterns
        identity_patterns = [
            ("who is the current", "present_tense_current"),
            ("who's the current", "present_tense_current"),
            ("who are the current", "present_tense_current"),
            ("what is the current", "present_tense_current"),
            ("what's the current", "present_tense_current"),
            ("who is the", "present_tense"),  # "who is the quarterback"
            ("who's the", "present_tense"),
            ("what is the latest", "latest_status"),
            ("what's the latest", "latest_status"),
            ("who won", "recent_result"),
            ("what is today's", "today_status"),
            ("what's today's", "today_status"),
        ]

        for pattern, reason in identity_patterns:
            if pattern in text_lower:
                return True, reason

        # Explicit temporal markers
        temporal_markers = [
            "right now", "at this moment", "this year", "this season",
            "last night", "yesterday", "today", "currently",
            "as of now", "at the moment"
        ]

        for marker in temporal_markers:
            if marker in text_lower:
                return True, f"temporal_marker:{marker}"

        return False, ""

    def _detect_sports_query(self, text_lower: str) -> tuple:
        """
        Detect if a query is about sports and return (is_sports, query_type).

        Returns: (bool, str) - (is_sports, query_type)
        """
        # Sports team names (common ones)
        sports_teams = [
            "giants", "cowboys", "patriots", "steelers", "packers",
            "lakers", "celtics", "warriors", "heat", "bulls",
            "yankees", "red sox", "dodgers", "mets", "cubs",
            "rangers", "bruins", "blackhawks", "maple leafs",
        ]

        # Sports keywords and their query types
        sports_keywords = {
            "quarterback": "sports_roster",
            "qb": "sports_roster",
            "nfl": "sports_result",
            "nba": "sports_result",
            "nhl": "sports_result",
            "mlb": "sports_result",
            "premier league": "sports_result",
            "soccer": "sports_result",
            "football": "sports_result",
            "basketball": "sports_result",
            "hockey": "sports_result",
            "baseball": "sports_result",
            "game score": "sports_result",
            "who won": "sports_result",
            "score of": "sports_result",
            "last night's game": "sports_result",
            "today's game": "sports_result",
            "coach": "sports_roster",
            "player": "sports_roster",
            "team": "sports_result",
            "pitcher": "sports_roster",
            "goalie": "sports_roster",
            "starting lineup": "sports_roster",
        }

        # Check for team names first
        for team in sports_teams:
            if team in text_lower:
                # Determine query type based on context
                if any(word in text_lower for word in ["who is", "who's", "quarterback", "coach", "player", "roster"]):
                    return True, "sports_roster"
                else:
                    return True, "sports_result"

        # Check for sports keywords
        for keyword, query_type in sports_keywords.items():
            if keyword in text_lower:
                return True, query_type

        return False, None

    def _detect_news_query(self, text_lower: str) -> tuple:
        """
        Detect if a query is asking for latest breaking news.

        Returns: (bool, str) - (is_news_query, query_type)
        """
        # Generic breaking news patterns (high confidence)
        generic_news_patterns = [
            "latest news",
            "breaking news",
            "top news",
            "current news",
            "whats happening",
            "what's happening",
            "recent news",
            "today's news",
            "news today",
            "headlines",
            "top headlines",
            "latest headlines",
        ]

        for pattern in generic_news_patterns:
            if pattern in text_lower:
                return True, "news_general"

        # Topic-specific news patterns
        topic_news_patterns = [
            "news about",
            "latest on",
            "breaking story",
            "recent developments",
        ]

        for pattern in topic_news_patterns:
            if pattern in text_lower:
                return True, "news_topic"

        return False, None

    def process(self, intent_data, memory_context):
        intent_type = intent_data["type"]
        content = intent_data["content"]
        print("[HRM] Analyzing Intent: {}".format(intent_type))

        # TEMPORAL AWARENESS: Detect if query is time-sensitive
        temporal_info = detect_temporal_intent(content)
        time_sensitive = temporal_info['is_after_cutoff']

        if time_sensitive:
            print("[HRM] ⏰ Temporal query detected: {}".format(temporal_info['reason']))
            print("[HRM] ⚠ Query requires external sources (after cutoff {})".format(temporal_info['cutoff_date']))

        text_lower = content.lower()

        # ENHANCED TEMPORAL: Check for identity/status questions (always time-sensitive)
        is_identity_status, identity_reason = self._is_time_sensitive_identity_question(text_lower)
        if is_identity_status:
            time_sensitive = True
            print("[HRM] 🎯 Identity/status query detected: {}".format(identity_reason))

        # SPORTS DETECTION (HIGH PRIORITY) - route before generic checks
        is_sports, sports_query_type = self._detect_sports_query(text_lower)
        if is_sports:
            print("[HRM] ⚽ Sports query detected: type={}".format(sports_query_type))
            return {
                "action": "TRIGGER_SCOUT",
                "domain": "sports",
                "query_type": sports_query_type,
                "time_sensitive": True,
                "time_sensitive_reason": "sports_always_live",
                "topic": content.strip(),
                "temporal_info": temporal_info,
            }

        # NEWS DETECTION (HIGH PRIORITY) - route breaking news queries
        is_news, news_query_type = self._detect_news_query(text_lower)
        if is_news:
            print("[HRM] 📰 News query detected: type={}".format(news_query_type))
            return {
                "action": "TRIGGER_SCOUT",
                "domain": "news",
                "query_type": news_query_type,
                "time_sensitive": True,
                "time_sensitive_reason": "news_always_current",
                "topic": content.strip(),
                "temporal_info": temporal_info,
            }

        # BESTSELLER DETECTION - route to NYT bestseller lists
        is_bestseller = any(phrase in text_lower for phrase in [
            "bestseller", "best seller", "best-seller",
            "nyt #", "new york times #",
            "top book", "newest book", "latest book"
        ])

        if is_bestseller and any(word in text_lower for word in ["nyt", "new york times", "bestseller", "best seller"]):
            print("[HRM] 📚 Bestseller query detected")
            return {
                "action": "TRIGGER_SCOUT",
                "domain": "bestseller",
                "query_type": "bestseller_list",
                "time_sensitive": True,
                "time_sensitive_reason": "bestseller_lists_update_weekly",
                "topic": content.strip(),
                "temporal_info": temporal_info,
            }

        # Identity questions - handle first (Adaptheon self-identity only)
        if self._is_identity_question(text_lower):
            result = self._handle_identity(text_lower)
            result['time_sensitive'] = False  # Identity is static
            result['temporal_info'] = temporal_info
            return result

        # Typed queries - these are ALWAYS time-sensitive
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
                "time_sensitive": True,  # Prices are always current
                "temporal_info": temporal_info,
            }

        if "weather" in text_lower:
            return {
                "action": "WEATHER_QUERY",
                "location_hint": content,
                "time_sensitive": True,  # Weather is always current
                "temporal_info": temporal_info,
            }

        if intent_type == "PLANNING":
            result = self._generate_plan(content)
            result['time_sensitive'] = time_sensitive
            result['temporal_info'] = temporal_info
            return result

        elif intent_type == "MEMORY_WRITE":
            fact = content.replace("remember", "").strip()
            return {
                "action": "SAVE_PREFERENCE",
                "key": "user_fact",
                "value": fact,
                "response": "I have stored that in your preference memory.",
                "time_sensitive": False,  # Memory write is not time-sensitive
                "temporal_info": temporal_info,
            }

        elif intent_type == "MEMORY_READ":
            prefs = memory_context.get("user_preferences", {})
            return {
                "action": "RETRIEVE",
                "data": prefs,
                "response": "Here is what I currently know about you: {}".format(prefs),
                "time_sensitive": False,  # Memory read is not time-sensitive
                "temporal_info": temporal_info,
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
            if key in semantic and not time_sensitive:
                # Only use cached knowledge if NOT time-sensitive
                return {
                    "action": "RETURN_KNOWLEDGE",
                    "topic": topic,
                    "time_sensitive": False,
                    "temporal_info": temporal_info,
                }
            else:
                return {
                    "action": "TRIGGER_SCOUT",
                    "topic": topic,
                    "response": "I do not have this in local memory yet. Launching Knowledge Scout.",
                    "time_sensitive": time_sensitive,
                    "temporal_info": temporal_info,
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
                "time_sensitive": time_sensitive,
                "temporal_info": temporal_info,
            }

        elif intent_type == "SEARCH_HINT":
            return {
                "action": "UPDATE_SEARCH_POLICY",
                "instruction": content,
                "time_sensitive": False,
                "temporal_info": temporal_info,
            }

        else:
            # CRITICAL: If query is time-sensitive but not caught by specific patterns,
            # trigger scout search to get fresh external data instead of using base LLM
            if time_sensitive:
                # Extract a reasonable topic from the query for scout search
                # Remove common question words to get the core topic
                topic = content.lower()
                for word in ["who is", "what is", "who's", "what's", "tell me about", "the current", "current"]:
                    topic = topic.replace(word, "")
                topic = topic.strip()

                return {
                    "action": "TRIGGER_SCOUT",
                    "topic": topic,
                    "response": "This query is time-sensitive. Launching Knowledge Scout for fresh data.",
                    "time_sensitive": True,
                    "temporal_info": temporal_info,
                }
            else:
                return {
                    "action": "CONVERSE",
                    "response": "Processing via standard conversational loop.",
                    "time_sensitive": False,
                    "temporal_info": temporal_info,
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
