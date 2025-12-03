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
            "-no-cnv",
            "-st",
        ]

        try:
            proc = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
            )
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
        """
        Generic text generation.
        Uses a simple Question/Answer pattern and returns only the answer text.
        """
        if not self.use_llm:
            return "[LLM Simulation] " + prompt

        if system_instruction:
            full_prompt = system_instruction + " Question: " + prompt + " Answer:"
        else:
            full_prompt = "Question: " + prompt + " Answer:"

        raw_output = self._call_llm(full_prompt, max_tokens=64, temperature=0.7)

        if "Answer:" in raw_output:
            answer_part = raw_output.split("Answer:", 1)[1].strip()
        else:
            answer_part = raw_output.strip()

        return answer_part

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

    def rewrite_from_sources(self, question, raw_summary, source_label):
        """
        Rewrite retrieved text (Wikipedia/RSS/local corpus/live tools) in Adaptheon's voice.
        Uses local Qwen model when available and returns only the final answer text.
        """
        if not self.use_llm:
            base = "Here is a concise explanation of '{}', based on {}: ".format(question, source_label)
            return base + raw_summary

        prompt = "Source text: " + raw_summary + " Question: " + question + " Instruction: Answer the question clearly and naturally in at most 2 sentences. Do not repeat the instructions or metadata. Only output the answer text. Answer:"

        raw_output = self._call_llm(prompt, max_tokens=80, temperature=0.5)

        if "Answer:" in raw_output:
            answer_part = raw_output.split("Answer:", 1)[1].strip()
        else:
            answer_part = raw_output.strip()

        if "Source text:" in answer_part:
            idx = answer_part.rfind("Source text:")
            answer_part = answer_part[idx + len("Source text:"):].strip()

        return answer_part
