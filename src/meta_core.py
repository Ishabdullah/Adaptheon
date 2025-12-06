import os
import json
import uuid
import logging

from components.memory import MemorySystem
from components.llm_interface import LanguageSystem
from components.hrm import HierarchicalReasoningMachine
from components.knowledge_scout import KnowledgeScout
from components.semantic_utils import text_to_vector, cosine_similarity
from components.time_service import get_now
from components.price_service import PriceService
from components.weather_service import WeatherService
from components.location_service import LocationService
from components.temporal_awareness import get_temporal_system_hint, KNOWLEDGE_CUTOFF
from components.feedback_store import FeedbackStore
from components.feedback_detector import FeedbackDetector
from components.feedback_context import get_relevant_feedback, build_feedback_context_snippet
from components.tool_learning import ToolLearningEngine


class MetaCognitiveCore:
    def __init__(self):
        print("[SYSTEM] Booting Adaptheon Phase 2.0...")

        # Core cognitive modules
        self.memory = MemorySystem()
        self.llm = LanguageSystem(model_path=None)
        self.hrm = HierarchicalReasoningMachine()
        self.scout = KnowledgeScout()
        self.price_service = PriceService()
        self.weather_service = WeatherService()
        self.location_service = LocationService()

        # Feedback and learning system
        self.feedback_store = FeedbackStore()
        self.feedback_detector = FeedbackDetector()
        self.tool_learning = ToolLearningEngine(self.feedback_store)

        # Conversation tracking
        self.current_conversation = None
        self.turn_counter = 0

        # Response tracking
        self.last_topic = None
        self.last_summary = None
        self.last_source = None

        # Logging setup
        os.makedirs("data/logs", exist_ok=True)
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s [%(levelname)s] %(message)s',
            handlers=[
                logging.FileHandler('data/logs/adaptheon.log'),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger('Adaptheon')

        print("[SYSTEM] All Cognitive Modules Online.")
        print(f"[SYSTEM] Feedback system initialized")

    def _lookup_semantic(self, topic):
        key = "knowledge_{}".format(topic.replace(" ", "_"))
        semantic = self.memory.layers.get("semantic", {})
        return key, semantic.get(key)

    def _related_topics(self, topic, base_summary):
        semantic = self.memory.layers.get("semantic", {})
        if not semantic:
            return ""
        base_vec = text_to_vector(base_summary)
        scores = []
        for k, fact in semantic.items():
            if not k.startswith("knowledge_"):
                continue
            name = k.replace("knowledge_", "").replace("_", " ")
            if name == topic:
                continue
            vec_dict = fact.get("vector", {})
            other_vec = {w: int(c) for w, c in vec_dict.items()}
            sim = cosine_similarity(base_vec, other_vec)
            if sim > 0.15:
                scores.append((name, sim))
        if not scores:
            return ""
        scores.sort(key=lambda x: x[1], reverse=True)
        top = [name for name, _ in scores[:3]]
        return " You might also ask about: " + ", ".join(top) + "."

    def _log_dispute(self, topic, user_text, old_fact, scout_result):
        path = "data/memory/disputes.json"
        os.makedirs(os.path.dirname(path), exist_ok=True)
        if os.path.exists(path):
            with open(path, "r") as f:
                try:
                    data = json.load(f)
                except json.JSONDecodeError:
                    data = []
        else:
            data = []

        entry = {
            "topic": topic,
            "user_correction": user_text,
            "old_summary": old_fact.get("summary") if old_fact else None,
            "old_metadata": old_fact.get("metadata") if old_fact else None,
            "scout_status": scout_result.get("status"),
            "scout_summary": scout_result.get("summary"),
            "scout_source": scout_result.get("source"),
            "scout_confidence": scout_result.get("confidence"),
        }
        data.append(entry)
        with open(path, "w") as f:
            json.dump(data, f, indent=4)

    def _select_policy_for_query(self, query):
        policies = self.memory.layers.get("search_policies", [])
        q_lower = query.lower()
        for p in policies:
            pat = p.get("pattern", "").lower()
            if pat and pat in q_lower:
                return p.get("rules", {})
        return None

    def run_cycle(self, user_input):
        # Create conversation if needed
        if not self.current_conversation:
            self.current_conversation = self.feedback_store.create_conversation(
                metadata={"device": "termux", "model": "qwen-1.5b"}
            )
            self.turn_counter = 0
            self.logger.info(f"Started conversation {self.current_conversation.id[:8]}")

        # Add user turn
        user_turn = self.feedback_store.add_turn(
            conversation_id=self.current_conversation.id,
            role="user",
            content=user_input,
            turn_index=self.turn_counter
        )
        self.turn_counter += 1

        # Get conversation history for feedback detection
        recent_turns = self.feedback_store.get_turns(self.current_conversation.id)

        # FEEDBACK DETECTION
        feedback_detection = self.feedback_detector.detect_feedback(user_input, recent_turns)
        if feedback_detection and feedback_detection.is_feedback:
            self.logger.info(f"Feedback detected: types={feedback_detection.feedback_types}, "
                            f"severity={feedback_detection.severity}")

            # Save feedback
            event, extraction = self.feedback_store.save_feedback(
                conversation_id=self.current_conversation.id,
                target_turn_id=feedback_detection.target_turn_id,
                raw_text=user_input,
                feedback_types=feedback_detection.feedback_types,
                severity=feedback_detection.severity,
                corrected_facts=feedback_detection.corrected_facts,
                preferred_tools=feedback_detection.preferred_tools,
                style_prefs=feedback_detection.style_prefs,
                time_sensitivity_notes=feedback_detection.time_sensitivity_notes
            )

            self.logger.info(f"Saved feedback event {event.id[:8]}")

        # GET RELEVANT FEEDBACK FOR CONTEXT
        relevant_feedback = get_relevant_feedback(
            conversation_id=self.current_conversation.id,
            current_query=user_input,
            feedback_store=self.feedback_store,
            max_results=5
        )

        feedback_context = build_feedback_context_snippet(relevant_feedback, max_length=500)

        if feedback_context:
            self.logger.info(f"Injecting feedback context ({len(relevant_feedback)} items)")

        # Parse intent and get logic output
        intent = self.llm.parse_intent(user_input)
        context = self.memory.get_context()
        logic_output = self.hrm.process(intent, context)

        action = logic_output.get("action")
        time_sensitive = logic_output.get("time_sensitive", False)
        temporal_info = logic_output.get("temporal_info", {})
        domain = logic_output.get("domain")  # For tool recommendations
        final_response = ""

        # Tool recommendation from learning
        if domain:
            tool_recommendations = self.tool_learning.get_tool_recommendation(user_input, domain)
            if tool_recommendations:
                self.logger.info(f"Tool recommendations for {domain}: {tool_recommendations}")

        # Log temporal query handling
        if time_sensitive:
            print("[Meta-Core] ⏰ Time-sensitive query detected (cutoff: {})".format(KNOWLEDGE_CUTOFF))
            print("[Meta-Core] ⚠ Will use external sources, not base LLM knowledge")

        if action == "SAVE_PREFERENCE":
            self.memory.update_preference(
                logic_output["key"],
                logic_output["value"]
            )
            final_response = logic_output["response"]

        elif action == "EXECUTE_PLAN":
            steps = logic_output.get("plan_steps", [])
            steps_text = " | ".join(steps)
            final_response = logic_output["response"] + " | Steps: " + steps_text

        elif action == "RETRIEVE":
            final_response = logic_output["response"]

        elif action == "PRICE_QUERY":
            asset = logic_output.get("asset", "").strip()
            self.logger.info(f"[PRICE_QUERY] Fetching price for: {asset}")

            price_data = self.price_service.get_price(asset)

            if not price_data:
                self.logger.warning(f"[PRICE_QUERY] Failed to fetch price for: {asset}")
                final_response = "I could not fetch a reliable live price for '{}' right now. This might be due to: (1) the asset name/ticker being unrecognized, (2) the API being temporarily unavailable, or (3) a network issue. Please try again or verify the asset name.".format(asset)
            else:
                asset_type = price_data.get("asset_type", "asset")
                source = price_data.get("source", "market data")

                # Build detailed summary
                if asset_type == "stock":
                    ticker = price_data.get("asset_id", asset)
                    price = price_data["price_usd"]
                    currency = price_data.get("currency", "USD")
                    change = price_data.get("change")
                    change_pct = price_data.get("change_percent")

                    summary = "As of {} {} UTC, {} (ticker: {}) is trading at {} {:.2f}".format(
                        price_data["as_of_date"],
                        price_data["as_of_time"],
                        asset,
                        ticker,
                        currency,
                        price
                    )

                    if change is not None and change_pct is not None:
                        summary += ", {}{:.2f} ({}{:.2f}%) from previous close".format(
                            "+" if change >= 0 else "",
                            change,
                            "+" if change_pct >= 0 else "",
                            change_pct
                        )

                    summary += " (source: {})".format(source)

                else:  # crypto
                    price = price_data["price_usd"]
                    change_24h = price_data.get("change_24h_percent")

                    summary = "As of {} {} UTC, {} is trading at USD ${:.2f}".format(
                        price_data["as_of_date"],
                        price_data["as_of_time"],
                        asset,
                        price
                    )

                    if change_24h is not None:
                        summary += ", {}{:.2f}% change in 24h".format(
                            "+" if change_24h >= 0 else "",
                            change_24h
                        )

                    summary += " (source: {})".format(source)

                self.logger.info(f"[PRICE_QUERY] Success: {ticker if asset_type == 'stock' else asset} = {price}")

                # Inject feedback context into temporal hint
                system_instruction_with_feedback = feedback_context + get_temporal_system_hint() if time_sensitive else feedback_context

                # Add temporal hint for time-sensitive queries
                rewritten = self.llm.rewrite_from_sources(
                    question="current price of " + asset,
                    raw_summary=summary,
                    source_label=source,
                    temporal_hint=system_instruction_with_feedback if system_instruction_with_feedback else (get_temporal_system_hint() if time_sensitive else None)
                )
                final_response = rewritten

        elif action == "WEATHER_QUERY":
            loc = self.location_service.get_location_details()
            if loc:
                lat = loc["latitude"]
                lon = loc["longitude"]
                place = loc.get("label", "your area")
                weather = self.weather_service.get_current_weather(lat, lon)
            else:
                place = "your area"
                weather = self.weather_service.get_current_weather()

            if not weather:
                final_response = "I could not fetch reliable weather data right now."
            else:
                summary = "As of {} {} at {}, the temperature is {:.1f} degrees Fahrenheit with wind speed {:.1f} miles per hour.".format(
                    weather["as_of_date"],
                    weather["as_of_time"],
                    place,
                    weather["temperature_f"],
                    weather["windspeed_mph"],
                )
                # Inject feedback context into temporal hint
                system_instruction_with_feedback = feedback_context + get_temporal_system_hint() if time_sensitive else feedback_context

                # Add temporal hint for time-sensitive queries
                rewritten = self.llm.rewrite_from_sources(
                    question="current weather",
                    raw_summary=summary,
                    source_label="live_weather",
                    temporal_hint=system_instruction_with_feedback if system_instruction_with_feedback else (get_temporal_system_hint() if time_sensitive else None)
                )
                final_response = rewritten

        elif action == "RETURN_KNOWLEDGE":
            topic = logic_output.get("topic", "").strip()
            key, fact = self._lookup_semantic(topic)
            if fact is None:
                final_response = "I thought I knew about '{}', but I cannot find it in memory yet.".format(topic)
            else:
                # If query is time-sensitive but we have cached knowledge, warn and re-scout
                if time_sensitive:
                    print("[Meta-Core] ⚠ Cached knowledge exists but query is time-sensitive - re-scouting...")
                    policy = self._select_policy_for_query(topic)
                    scout_result = self.scout.search(topic, policy=policy, ignore_cache=True)
                    if scout_result["status"] == "FOUND":
                        # Update cache with fresh data
                        metadata = {
                            "source": scout_result["source"],
                            "confidence": scout_result["confidence"],
                            "url": scout_result.get("url"),
                            "refreshed_for_temporal": True,
                        }
                        if hasattr(self.memory, "add_semantic"):
                            self.memory.add_semantic(key, scout_result["summary"], metadata)
                        rewritten = self.llm.rewrite_from_sources(
                            question=topic,
                            raw_summary=scout_result["summary"],
                            source_label=scout_result["source"],
                            temporal_hint=get_temporal_system_hint()
                        )
                        final_response = rewritten
                        self.last_topic = topic
                        self.last_summary = scout_result["summary"]
                        self.last_source = scout_result["source"]
                    else:
                        final_response = "This query is time-sensitive, but I could not fetch updated information. Please try again."
                else:
                    # Use cached knowledge for non-temporal queries
                    summary = fact.get("summary", "")
                    source = fact.get("metadata", {}).get("source", "memory")
                    rewritten = self.llm.rewrite_from_sources(
                        question=topic,
                        raw_summary=summary,
                        source_label=source
                    )
                    final_response = rewritten + self._related_topics(topic, summary)
                    self.last_topic = topic
                    self.last_summary = summary
                    self.last_source = source

        elif action == "TRIGGER_SCOUT":
            topic = logic_output["topic"]
            domain = logic_output.get("domain")  # Get domain hint from HRM (e.g., "sports")
            query_type = logic_output.get("query_type")  # Get query type (e.g., "sports_roster")

            if domain:
                print("[Meta-Core] {} query for '{}' (type: {}), launching Scout...".format(
                    domain.upper(), topic, query_type or "general"))
            else:
                print("[Meta-Core] Unknown topic '{}', launching Scout...".format(topic))

            policy = self._select_policy_for_query(topic)
            # For time-sensitive queries, skip cache and fetch fresh data
            # Pass domain hint to enable sports fast path and other domain-specific routing
            scout_result = self.scout.search(topic, policy=policy, ignore_cache=time_sensitive, domain=domain)

            # Log tool use event for scout search
            self.feedback_store.add_tool_use_event(
                conversation_id=self.current_conversation.id,
                turn_id=user_turn.id,
                tool_name="scout_search",
                inputs={"topic": topic, "domain": domain, "query_type": query_type, "ignore_cache": time_sensitive},
                output_summary=scout_result.get("summary", "")[:200],
                success=scout_result["status"] == "FOUND",
                error=None if scout_result["status"] == "FOUND" else "NOT_FOUND"
            )

            if scout_result["status"] == "FOUND":
                key = "knowledge_{}".format(topic.replace(" ", "_"))
                metadata = {
                    "source": scout_result["source"],
                    "confidence": scout_result["confidence"],
                    "url": scout_result.get("url"),
                }
                if hasattr(self.memory, "add_semantic"):
                    self.memory.add_semantic(key, scout_result["summary"], metadata)

                # Inject feedback context into temporal hint
                system_instruction_with_feedback = feedback_context + get_temporal_system_hint() if time_sensitive else feedback_context

                # Add temporal hint for time-sensitive queries
                rewritten = self.llm.rewrite_from_sources(
                    question=topic,
                    raw_summary=scout_result["summary"],
                    source_label=scout_result["source"],
                    temporal_hint=system_instruction_with_feedback if system_instruction_with_feedback else (get_temporal_system_hint() if time_sensitive else None)
                )
                final_response = rewritten
                self.last_topic = topic
                self.last_summary = scout_result["summary"]
                self.last_source = scout_result["source"]
            else:
                final_response = scout_result["summary"]

        elif action == "VERIFY_AND_UPDATE":
            topic = logic_output.get("topic")
            user_corr = logic_output.get("user_correction", "")
            if not topic and self.last_topic:
                topic = self.last_topic

            if not topic:
                final_response = "I am not sure which fact you are correcting. Please say, for example, 'That's wrong about Samsung...'."
            else:
                print("[Meta-Core] Verifying user correction on '{}'...".format(topic))
                key, old_fact = self._lookup_semantic(topic)
                policy = self._select_policy_for_query(topic)
                scout_result = self.scout.search(topic, policy=policy)
                self._log_dispute(topic, user_corr, old_fact, scout_result)

                if scout_result["status"] == "FOUND":
                    metadata_updates = {
                        "corrected": True,
                        "corrected_by_user": True,
                        "last_correction_text": user_corr,
                        "last_correction_source": scout_result["source"],
                        "last_correction_confidence": scout_result["confidence"],
                    }
                    if old_fact is not None:
                        old_fact["summary"] = scout_result["summary"]
                        old_meta = old_fact.get("metadata", {})
                        old_meta.update(metadata_updates)
                        old_fact["metadata"] = old_meta
                        vec = text_to_vector(scout_result["summary"])
                        old_fact["vector"] = {w: int(c) for w, c in vec.items()}
                        self.memory.save_memory()
                    else:
                        if hasattr(self.memory, "add_semantic"):
                            self.memory.add_semantic(
                                key,
                                scout_result["summary"],
                                metadata_updates
                            )

                    final_response = "Thanks for the correction. I have updated what I know about '{}' based on your feedback and new sources.".format(topic)
                else:
                    final_response = "I logged your correction about '{}', but my Scout could not confirm new information yet. I will treat this as an open question.".format(topic)

        elif action == "UPDATE_SEARCH_POLICY":
            instr = logic_output.get("instruction", "")
            text = instr.lower()
            if "current price" in text or "price of" in text:
                pattern = "current price of"
                rules = {
                    "require_numeric": True,
                    "prefer_source": ["local_rss"],
                }
                self.memory.add_search_policy(pattern, rules)
                final_response = "Understood. I will adjust how I search for current prices to focus on numeric information and relevant feeds."
            else:
                pattern = "what is"
                rules = {}
                self.memory.add_search_policy(pattern, rules)
                final_response = "I have recorded your search preference and will use it in future lookups."

        elif action == "IDENTITY_RESPONSE":
            # Identity questions handled directly by HRM
            final_response = logic_output.get("response", "I am Adaptheon.")

        else:
            # Fallback for unhandled actions (CONVERSE, etc.)
            # SAFETY CHECK: Never use base LLM for time-sensitive queries
            if time_sensitive:
                print("[Meta-Core] ⚠ WARNING: Time-sensitive query reached fallback handler!")
                print("[Meta-Core] This should have been routed to external sources by HRM.")
                final_response = (
                    "I detected this is a time-sensitive query that requires current information, "
                    "but I'm unable to search for fresh data right now. Please rephrase your "
                    "question or try again."
                )
            else:
                final_response = self.llm.generate(user_input)

        # Add assistant turn to feedback store
        assistant_turn = self.feedback_store.add_turn(
            conversation_id=self.current_conversation.id,
            role="assistant",
            content=final_response,
            turn_index=self.turn_counter
        )
        self.turn_counter += 1

        # Add to episodic memory
        self.memory.add_episodic(user_input, final_response)
        return final_response


if __name__ == "__main__":
    core = MetaCognitiveCore()
    print("Adaptheon Phase 2.0 is listening. Type 'quit' to exit.")
    while True:
        try:
            text = input("> ")
            if text.lower() in ("quit", "exit"):
                print("[SYSTEM] Shutting down.")
                break
            reply = core.run_cycle(text)
            print("[Adaptheon]: {}".format(reply))
        except KeyboardInterrupt:
            print("[SYSTEM] Interrupt received, exiting.")
            break
        except Exception as e:
            print("[ERROR] {}".format(e))
