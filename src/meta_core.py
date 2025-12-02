from components.memory import MemorySystem
from components.llm_interface import LanguageSystem
from components.hrm import HierarchicalReasoningMachine
from components.knowledge_scout import KnowledgeScout
from components.semantic_utils import text_to_vector, cosine_similarity


class MetaCognitiveCore:
    def __init__(self):
        print("[SYSTEM] Booting Adaptheon Phase 2.0...")
        self.memory = MemorySystem()
        self.llm = LanguageSystem(model_path=None)  # simulation mode
        self.hrm = HierarchicalReasoningMachine()
        self.scout = KnowledgeScout()
        print("[SYSTEM] All Cognitive Modules Online.")

    def _lookup_semantic(self, topic):
        key = "knowledge_{}".format(topic.replace(" ", "_"))
        semantic = self.memory.layers.get("semantic", {})
        return key, semantic.get(key)

    def _related_topics(self, topic, base_summary):
        """
        Tiny semantic search: use cosine similarity over simple word vectors
        to find 1-3 related knowledge items.
        """
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
        # Sort by similarity, pick top 3
        scores.sort(key=lambda x: x[1], reverse=True)
        top = [name for name, _ in scores[:3]]
        return " You might also ask about: " + ", ".join(top) + "."

    def run_cycle(self, user_input):
        intent = self.llm.parse_intent(user_input)
        context = self.memory.get_context()
        logic_output = self.hrm.process(intent, context)

        action = logic_output.get("action")
        final_response = ""

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

        elif action == "RETURN_KNOWLEDGE":
            topic = logic_output.get("topic", "").strip()
            key, fact = self._lookup_semantic(topic)
            if fact is None:
                final_response = "I thought I knew about '{}', but I cannot find it in memory yet.".format(topic)
            else:
                summary = fact.get("summary", "")
                source = fact.get("metadata", {}).get("source", "memory")
                rewritten = self.llm.rewrite_from_sources(
                    question=topic,
                    raw_summary=summary,
                    source_label=source
                )
                final_response = rewritten + self._related_topics(topic, summary)

        elif action == "TRIGGER_SCOUT":
            topic = logic_output["topic"]
            print("[Meta-Core] Unknown topic '{}', launching Scout...".format(topic))
            scout_result = self.scout.search(topic)
            if scout_result["status"] == "FOUND":
                key = "knowledge_{}".format(topic.replace(" ", "_"))
                metadata = {
                    "source": scout_result["source"],
                    "confidence": scout_result["confidence"],
                    "url": scout_result.get("url"),
                }
                if hasattr(self.memory, "add_semantic"):
                    self.memory.add_semantic(key, scout_result["summary"], metadata)

                rewritten = self.llm.rewrite_from_sources(
                    question=topic,
                    raw_summary=scout_result["summary"],
                    source_label=scout_result["source"]
                )
                final_response = rewritten
            else:
                final_response = scout_result["summary"]

        else:
            final_response = self.llm.generate(user_input)

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
