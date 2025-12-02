from components.memory import MemorySystem
from components.llm_interface import LanguageSystem
from components.hrm import HierarchicalReasoningMachine
from knowledge_scout.scout import KnowledgeScout
import time

class MetaCognitiveCore:
    def __init__(self):
        print("
[SYSTEM] Booting Adaptheon Phase 2.0...")
        print("[SYSTEM] Initializing Neural Pathways...")
        self.memory = MemorySystem()
        
        print("[SYSTEM] Loading Language System...")
        self.llm = LanguageSystem()
        
        print("[SYSTEM] Activating Reasoning Engine...")
        self.hrm = HierarchicalReasoningMachine()
        
        print("[SYSTEM] Deploying Knowledge Scout (Advanced)...")
        self.scout = KnowledgeScout(self.memory)
        
        print("[SYSTEM] ✓ All Cognitive Modules Online.
")

    def run_cycle(self, user_input):
        print(f"─── [Cycle Start] ───")
        
        # 1. Parse
        intent = self.llm.parse_intent(user_input)
        
        # 2. Context
        context = self.memory.get_context()
        
        # 3. Reason
        logic_output = self.hrm.process(intent, context)
        
        # 4. Execute
        final_response = ""
        
        if logic_output["action"] == "SAVE_PREFERENCE":
            self.memory.update_preference(logic_output["key"], logic_output["value"])
            final_response = logic_output["response"]
            
        elif logic_output["action"] == "EXECUTE_PLAN":
            final_response = f"{logic_output['response']}
Steps:
" + '
'.join(logic_output['plan_steps'])
            
        elif logic_output["action"] == "RETRIEVE":
            final_response = logic_output["response"]
            
        elif logic_output["action"] == "TRIGGER_SCOUT":
            # Advanced Scout with verification
            print(f"  [Meta-Core] Uncertainty detected. Authorizing Scout...")
            scout_result = self.scout.scout(logic_output["topic"])
            
            if scout_result['stored']:
                final_response = f"✓ New knowledge acquired:

{scout_result['answer']}

"
                final_response += f"Confidence: {scout_result['confidence']:.0%} | "
                final_response += f"Source: {scout_result['source']} | "
                final_response += f"Time: {scout_result['time_ms']}ms"
                
                if scout_result['citations']:
                    final_response += f"

Sources:"
                    for i, cit in enumerate(scout_result['citations'][:3], 1):
                        final_response += f"
{i}. {cit['title']}"
            else:
                final_response = f"Scout found: {scout_result['answer']}

"
                final_response += f"(Confidence: {scout_result['confidence']:.0%} - below storage threshold)"
            
        else:
            final_response = self.llm.generate(user_input)

        # 5. Episodic Write
        self.memory.add_episodic(user_input, final_response)
        
        print(f"─── [Cycle End] ───
")
        return final_response

if __name__ == "__main__":
    core = MetaCognitiveCore()
    print("Adaptheon Phase 2 is online. (Type 'quit' to exit)
")
    print("Try asking: 'What is GGUF quantization?' or 'What's new in AI?'
")
    
    while True:
        try:
            u_input = input("> ")
            if u_input.lower() in ["quit", "exit"]:
                print("
[SYSTEM] Entering hibernation state...")
                break
            
            response = core.run_cycle(u_input)
            print(f"
[Adaptheon]:
{response}
")
            print("="*60)
            
        except KeyboardInterrupt:
            print("

[SYSTEM] Emergency shutdown initiated...")
            break
        except Exception as e:
            print(f"
[ERROR] {e}")
            print("System recovered. Continuing...")
