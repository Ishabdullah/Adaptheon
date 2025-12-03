import time
import string


class HierarchicalReasoningMachine:
    """
    Logic Cortex (Phase 2).
    Handles planning, memory, knowledge, corrections, search hints,
    typed queries like prices and weather, basic time-awareness,
    and lightweight domain/query_type tagging for the Super-Catalog.
    """

    def __init__(self):
        pass

    def _is_time_sensitive(self, text_lower: str) -> bool:
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

    def _guess_domain_and_type(self, text_lower: str):
        """
        Rough domain/query_type classifier used to hint DomainRouter.
        Returns (domain, query_type) or (None, None).
        """
        # Sports
        if ("who won" in text_lower
            or "final score" in text_lower
            or "score of" in text_lower
            or "giants" in text_lower
            or "nfl" in text_lower
            or "nba" in text_lower
            or "mlb" in text_lower
            or "premier league" in text_lower):
            return "sports", "sports_result"

        # Weather
        if "weather" in text_lower or "temperature" in text_lower:
            return "weather", "weather_current"

        # Finance / crypto
        if "stock" in text_lower or "ticker" in text_lower or "pe ratio" in text_lower:
            return "finance_markets", "stock_info"
        if "bitcoin" in text_lower or "btc" in text_lower or "ethereum" in text_lower or "eth" in text_lower:
            return "crypto", "crypto_price"
        if "price of" in text_lower or "current price" in text_lower:
            # Generic price question; domain resolved later by asset symbol
            return "finance_markets", "price_query"

        # Politics / government
        if ("governor" in text_lower
            or "senator" in text_lower
            or "congress" in text_lower
            or "parliament" in text_lower
            or "prime minister" in text_lower
            or "president of" in text_lower
            or "election" in text_lower):
            return "politics_government", "office_holder_or_election"

        # Science / academic
        if ("paper" in text_lower
            or "research" in text_lower
            or "citation" in text_lower
            or "semantic scholar" in text_lower
            or "arxiv" in text_lower):
            return "science_academic", "paper_search"

        # Media / entertainment
        if ("movie" in text_lower
            or "film" in text_lower
            or "tv show" in text_lower
            or "episode" in text_lower
            or "anime" in text_lower
            or "series" in text_lower):
            return "media_entertainment", "media_info"

        # Books / literature
        if ("book" in text_lower
            or "novel" in text_lower
            or "isbn" in text_lower
            or "author" in text_lower and "book" in text_lower):
            return "books_literature", "book_info"

        # Music
        if ("song" in text_lower
            or "track" in text_lower
            or "album" in text_lower
            or "artist" in text_lower and "music" in text_lower):
            return "music", "music_info"

        # Transportation
        if ("flight" in text_lower
            or "airport" in text_lower
            or "airline" in text_lower
            or "arrival" in text_lower and "flight" in text_lower):
            return "transportation", "flight_status"

        # AI / tech
        if ("model" in text_lower and "ai" in text_lower) or "huggingface" in text_lower or "github" in text_lower:
            return "ai_tech", "ai_model_or_repo"

        # Default: general entities / concepts
        if ("what is" in text_lower
            or "who is" in text_lower
            or "define" in text_lower
            or "tell me about" in text_lower):
            return "general", "entity_or_concept"

        return None, None

    def process(self, intent_data, memory_context):
        intent_type = intent_data["type"]
        content = intent_data["content"]
        print("[HRM] Analyzing Intent: {}".format(intent_type))

        text_lower = content.lower()
        time_sensitive = self._is_time_sensitive(text_lower)
        domain, query_type = self._guess_domain_and_type(text_lower)

        # Special self-queries
        if "what is my name" in text_lower or "do you know my name" in text_lower:
            return {
                "action": "GET_USER_NAME",
                "domain": "general",
                "query_type": "user_identity",
            }

        # SEARCH_HINT: handle before typed tools so it doesn't get treated as PRICE_QUERY
        if intent_type == "SEARCH_HINT":
            return {
                "action": "UPDATE_SEARCH_POLICY",
                "instruction": content,
                "domain": domain,
                "query_type": "search_hint",
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

                # Refine domain: crypto vs finance_markets
                asset_l = asset.lower()
                if asset_l in ("btc", "bitcoin", "eth", "ethereum", "sol", "solana"):
                    domain_local = "crypto"
                else:
                    domain_local = domain or "finance_markets"

                return {
                    "action": "PRICE_QUERY",
                    "asset": asset,
                    "domain": domain_local,
                    "query_type": "price_query",
                }

            if "weather" in text_lower:
                return {
                    "action": "WEATHER_QUERY",
                    "location_hint": content,
                    "domain": "weather",
                    "query_type": "weather_current",
                }

        # Time-sensitive "who is ..." knowledge queries
        if text_lower.startswith("who is"):
            raw = text_lower.replace("who is", "", 1)
            topic = raw.strip().strip(string.punctuation)
            dom, qtype = domain or "general", query_type or "entity_or_concept"
            return {
                "action": "TRIGGER_SCOUT",
                "topic": topic,
                "time_sensitive": True,
                "domain": dom,
                "query_type": qtype,
            }

        # Sports / event queries
        if "who won" in text_lower or "score of" in text_lower or "final score" in text_lower:
            topic = content.strip()
            return {
                "action": "TRIGGER_SCOUT",
                "topic": topic,
                "time_sensitive": True,
                "domain": "sports",
                "query_type": "sports_result",
            }

        if intent_type == "PLANNING":
            plan = self._generate_plan(content)
            plan["domain"] = domain
            plan["query_type"] = "planning"
            return plan

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
                    "domain": "general",
                    "query_type": "user_identity_write",
                }

            fact = content.replace("remember", "").strip()
            return {
                "action": "SAVE_PREFERENCE",
                "key": "user_fact",
                "value": fact,
                "response": "I have stored that in your preference memory.",
                "domain": "general",
                "query_type": "user_preference_write",
            }

        elif intent_type == "MEMORY_READ":
            prefs = memory_context.get("user_preferences", {})
            return {
                "action": "RETRIEVE",
                "data": prefs,
                "response": "Here is what I currently know about you: {}".format(prefs),
                "domain": "general",
                "query_type": "user_memory_read",
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
                    "topic": topic,
                    "domain": domain or "general",
                    "query_type": query_type or "entity_or_concept",
                }
            else:
                return {
                    "action": "TRIGGER_SCOUT",
                    "topic": topic,
                    "time_sensitive": time_sensitive,
                    "response": "I do not have this in local memory yet. Launching Knowledge Scout.",
                    "domain": domain or "general",
                    "query_type": query_type or "entity_or_concept",
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
                "domain": domain or "general",
                "query_type": "correction",
            }

        else:
            return {
                "action": "CONVERSE",
                "response": "Processing via standard conversational loop.",
                "domain": domain,
                "query_type": "chat",
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
