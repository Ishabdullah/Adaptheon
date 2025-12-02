class LanguageSystem:
    """
    Minimal Phase 2 language layer.
    Right now this is simulation-only; later you can wire in llama.cpp.
    """
    def __init__(self, model_path=None):
        self.model_path = model_path
        self.real_model_loaded = False  # flip when you add a real model

    def generate(self, prompt, system_instruction=None):
        """
        Generic text generation stub.
        """
        if not self.real_model_loaded:
            return "[LLM Simulation] " + prompt
        return "[LLM Real] " + prompt

    def parse_intent(self, user_input):
        """
        Simple intent parser for routing.
        """
        text = user_input.lower()
        if "plan" in text or "schedule" in text:
            return {"type": "PLANNING", "content": user_input}
        elif "remember" in text:
            return {"type": "MEMORY_WRITE", "content": user_input}
        elif "who am i" in text or "what do you know" in text:
            return {"type": "MEMORY_READ", "content": user_input}
        else:
            # HRM itself looks for 'what is' / 'define' inside content
            return {"type": "CHAT", "content": user_input}

    def rewrite_from_sources(self, question, raw_summary, source_label):
        """
        Rewrite retrieved knowledge into Adaptheon's own voice.
        For now, a simple formatted summary.
        """
        if not self.real_model_loaded:
            return "Here is a concise explanation of '{}', based on {}: {}".format(
                question, source_label, raw_summary
            )
        return "[LLM Real Rewrite] " + raw_summary
