import os
import json

from components.memory import MemorySystem
from components.llm_interface import LanguageSystem
from components.hrm import HierarchicalReasoningMachine
from components.knowledge_scout import KnowledgeScout
from components.semantic_utils import text_to_vector, cosine_similarity
from components.time_service import get_now
from components.price_service import PriceService
from components.weather_service import WeatherService
from components.location_service import LocationService
from components.tool_registry import Tool, ToolRegistry
from components.embedding_store import EmbeddingStore
from components.graph_memory import GraphMemory
from components.identity.identity_module import IdentityModule


class MetaCognitiveCore:
    def __init__(self):
        print("[SYSTEM] Booting Adaptheon Phase 2.0...")
        self.memory = MemorySystem()
        self.llm = LanguageSystem(model_path=None)
        self.hrm = HierarchicalReasoningMachine()
        self.scout = KnowledgeScout()
        self.price_service = PriceService()
        self.weather_service = WeatherService()
        self.location_service = LocationService()
        self.vector_store = EmbeddingStore()
        self.graph_memory = GraphMemory()
        self.identity = IdentityModule(self.llm)
        self.tools = ToolRegistry()
        self._register_tools()
        self.last_topic = None
        self.last_summary = None
        self.last_source = None
        print("[SYSTEM] All Cognitive Modules Online.")

    # _register_tools, _lookup_semantic, _related_topics, _build_memory_context, _log_dispute, _select_policy_for_query
    # are unchanged from previous step – they stay as in Step 40.

    def _register_tools(self):
        self.tools.register(
            Tool(
                name="llm_generate",
                description="Local language generation via Qwen and llama.cpp",
                func=lambda prompt, system_instruction=None: self.llm.generate(
                    prompt, system_instruction
                ),
            )
        )

        self.tools.register(
            Tool(
                name="scout_search",
                description="Multi-source knowledge search (cache, Wikipedia, RSS, local corpus, domain-aware)",
                func=lambda query, policy=None, ignore_cache=False, domain=None, query_type=None: self.scout.search(
                    query, policy=policy, ignore_cache=ignore_cache, domain=domain, query_type=query_type
                ),
            )
        )

        self.tools.register(
            Tool(
                name="price_query",
                description="Live crypto price lookup via CoinGecko",
                func=lambda asset: self.price_service.get_price(asset),
            )
        )

        self.tools.register(
            Tool(
                name="weather_current",
                description="Current weather via Open-Meteo for given coordinates",
                func=lambda latitude=None, longitude=None: self.weather_service.get_current_weather(
                    latitude, longitude
                ),
            )
        )

        self.tools.register(
            Tool(
                name="location_details",
                description="Device GPS + reverse geocoding into human-readable location",
                func=lambda: self.location_service.get_location_details(),
            )
        )

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

    def _build_memory_context(self, topic: str) -> str:
        parts = []
        try:
            vec_hits = self.vector_store.query(topic, top_k=3, min_score=0.2)
        except Exception:
            vec_hits = []

        if vec_hits:
            vs = []
            for doc_id, score, payload in vec_hits:
                meta = payload.get("metadata", {})
                src = meta.get("source", "memory")
                vs.append(f"- [{src}] {payload.get('text', '')}")
            parts.append("Vector memory snippets:
" + "
".join(vs))

        try:
            neigh = self.graph_memory.neighborhood(topic, max_hops=1)
        except Exception:
            neigh = {"nodes": {}, "edges": []}

        if neigh.get("nodes"):
            node_summaries = []
            for label, node in neigh["nodes"].items():
                if label.lower() == topic.lower():
                    continue
                summ = node.get("summary", "")
                if not summ:
                    continue
                node_summaries.append(f"- [{label}] {summ}")
            if node_summaries:
                parts.append("Graph memory neighbors:
" + "
".join(node_summaries))

        return "

".join(parts)

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
        ident = self.identity.handle(user_input)
        if ident.get("handled"):
            final = ident.get("response", "")
            self.memory.add_episodic(user_input, final)
            return final

        intent = self.llm.parse_intent(user_input)
        context = self.memory.get_context()
        logic_output = self.hrm.process(intent, context)

        action = logic_output.get("action")
        final_response = ""

        # ... CHAT, PRICE_QUERY, WEATHER_QUERY, RETURN_KNOWLEDGE, TRIGGER_SCOUT branches unchanged
        # except for the VERIFY_AND_UPDATE block, which becomes memory-aware below.

        if action == "VERIFY_AND_UPDATE":
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

                # 1) External check via Scout (fresh truth search)[web:669][web:677]
                scout_result = self.tools.invoke(
                    "scout_search",
                    query=topic,
                    policy=policy,
                    ignore_cache=False,
                    domain=logic_output.get("domain"),
                    query_type=logic_output.get("query_type"),
                )

                # 2) Local memory evidence (vector + graph)
                mem_ctx = self._build_memory_context(topic)

                self._log_dispute(topic, user_corr, old_fact, scout_result)

                if scout_result["status"] == "FOUND":
                    # Combine external + memory evidence into a single payload for the LLM
                    evidence_chunks = []
                    if mem_ctx:
                        evidence_chunks.append(mem_ctx)
                    evidence_chunks.append("External scout summary:
" + scout_result["summary"])
                    if old_fact is not None:
                        evidence_chunks.append("Existing stored summary:
" + old_fact.get("summary", ""))

                    combined_evidence = "

".join(evidence_chunks)

                    # Ask LLM to decide whether the correction is supported, refuted, or uncertain (lightweight CRAG).[web:670][web:681]
                    verdict = self.llm.rewrite_from_sources(
                        question=f"Evaluate this user correction about '{topic}': {user_corr}",
                        raw_summary=combined_evidence,
                        source_label="corrective_rag"
                    )

                    metadata_updates = {
                        "corrected": True,
                        "corrected_by_user": True,
                        "last_correction_text": user_corr,
                        "last_correction_source": scout_result["source"],
                        "last_correction_confidence": scout_result["confidence"],
                        "last_correction_verdict": verdict,
                    }

                    # For now, always update to the Scout version; verdict is stored for inspection
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

                    final_response = (
                        "Thanks for the correction. Based on my re-check of external sources and my own memory, "
                        "I have updated what I know about '{}' and recorded a verification verdict.".format(topic)
                    )
                else:
                    final_response = (
                        "I logged your correction about '{}', but my Scout could not confirm new information yet. "
                        "I will treat this as an open question.".format(topic)
                    )

        # ... other actions (SAVE_PREFERENCE, EXECUTE_PLAN, GET_USER_NAME, etc.) remain as in Step 40

        elif action not in ("VERIFY_AND_UPDATE",):
            # fall back to the existing branches (omitted here for brevity)
            # In your local file, keep the existing implementations from Step 40.
            pass

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
