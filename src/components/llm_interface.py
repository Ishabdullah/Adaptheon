import os
import subprocess


class LanguageSystem:
    """
    Local Qwen GGUF via llama.cpp CLI (Termux-safe: no multiline string expressions).
    """

    def __init__(self, model_path=None, llama_bin_path=None):
        default_model = os.path.expanduser("~/Adaptheon/models/qwen/qwen2-1.5b-q4_k_m.gguf")
        default_bin = os.path.expanduser("~/Adaptheon/llama.cpp/build/bin/llama-cli")

        self.model_path = model_path or default_model
        self.llama_bin = llama_bin_path or default_bin

        self.use_llm = False
        if os.path.exists(self.llama_bin) and os.path.exists(self.model_path):
            self.use_llm = True
            print("[LLM] Using local llama.cpp binary at '{}' with model '{}'".format(self.llama_bin, self.model_path))
        else:
            print("[LLM] Local model or binary not found, using simulation mode.")
            print("      Expected binary: {}".format(self.llama_bin))
            print("      Expected model:  {}".format(self.model_path))

    def _call_llm(self, prompt, max_tokens=64, temperature=0.7):
        """
        Call llama.cpp CLI binary with a prompt via subprocess.
        Uses -no-cnv and -st to avoid interactive chat mode and run a single turn.
        """
        if not self.use_llm:
            return "[LLM Simulation] " + prompt

        cmd = [
            self.llama_bin,
            "-m", self.model_path,
            "-p", prompt,
            "--n-predict", str(max_tokens),
            "--temp", str(temperature),
            "-no-cnv",        # disable conversation mode [web:256][web:260]
            "-st",            # single-turn, non-interactive [web:256]
        ]

        try:
            proc = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
            )
            # Add a timeout so we don't hang forever on bad runs
            out, err = proc.communicate(timeout=40)

            if proc.returncode != 0:
                return "[LLM Error] Return code {}. Stderr: {}".format(proc.returncode, err)

            text = out.strip()
            if not text:
                return "[LLM Empty Output]"
            return text

        except subprocess.TimeoutExpired:
            proc.kill()
            return "[LLM Error] Timeout during generation."
        except FileNotFoundError:
            return "[LLM Error] llama.cpp binary not found at: {}".format(self.llama_bin)
        except Exception as e:
            return "[LLM Error] {}".format(e)

    def generate(self, prompt, system_instruction=None):
        if not self.use_llm:
            return "[LLM Simulation] " + prompt

        if system_instruction:
            full_prompt = system_instruction + " User: " + prompt + " Assistant:"
        else:
            full_prompt = "User: " + prompt + " Assistant:"

        return self._call_llm(full_prompt, max_tokens=64, temperature=0.7)

    def parse_intent(self, user_input):
        text = user_input.lower().strip()

        # Search hint / meta-instruction patterns
        if (("from now on" in text) or ("when i ask" in text) or ("when i say" in text) or ("in the future" in text)) and ("search" in text or "look for" in text or "focus on" in text or "prioritize" in text or "check" in text):
            return {"type": "SEARCH_HINT", "content": user_input}

        # Correction patterns
        if (text.startswith("that's wrong")
            or text.startswith("thats wrong")
            or "you are wrong" in text
            or "you're wrong" in text
            or "youre wrong" in text
            or "that is wrong" in text
            or "not correct" in text
            or "incorrect" in text
            or text.startswith("correction:")):
            return {"type": "CORRECTION", "content": user_input}

        if "plan" in text or "schedule" in text:
            return {"type": "PLANNING", "content": user_input}
        elif "remember" in text:
            return {"type": "MEMORY_WRITE", "content": user_input}
        elif "who am i" in text or "what do you know" in text:
            return {"type": "MEMORY_READ", "content": user_input}
        else:
            return {"type": "CHAT", "content": user_input}
    def rewrite_from_sources(self, question, raw_summary, source_label, temporal_hint=None):
        """
        Rewrite raw summary from sources into natural language.

        Args:
            question: User's original question
            raw_summary: Raw text from sources
            source_label: Label indicating source type
            temporal_hint: Optional temporal awareness hint for time-sensitive queries
        """
        if not self.use_llm:
            base = "Here is a concise explanation of '{}', based on {}: ".format(question, source_label)
            return base + raw_summary

        header = "You are Adaptheon's language cortex. Explain things clearly and briefly using only the given source text."

        # Add temporal hint if provided (for time-sensitive queries)
        if temporal_hint:
            header = temporal_hint + " " + header

        line_q = "Question: " + question
        line_src_label = "Source label: " + str(source_label)
        line_src_text = "Source text: " + raw_summary
        task = "Task: Rewrite the source text into a clear, natural answer to the question. Be concise, accurate, and avoid strange symbols or citation markers."

        prompt = header + " " + line_q + " " + line_src_label + " " + line_src_text + " " + task

        return self._call_llm(prompt, max_tokens=80, temperature=0.5)
