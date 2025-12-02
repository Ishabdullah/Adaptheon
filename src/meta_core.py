from components.memory import MemorySystem
from components.llm_interface import LanguageSystem
from components.hrm import HierarchicalReasoningMachine
import time

class MetaCognitiveCore:
    """
    The Prefrontal Cortex.
    Routes data between LLM, HRM, and Memory.
    """
    def __init__(self):
        print("\n[SYSTEM] Booting Adaptheon Phase 0.1...")
        self.memory = MemorySystem()
        self.llm = LanguageSystem()
        self.hrm = HierarchicalReasoningMachine()
        print("[SYSTEM] Neural Pathways Online.\n")

    def run_cycle(self, user_input):
        print(f"─── [Input Received] ───")
        
        # 1. LLM: Parse input into structured intent
        intent = self.llm.parse_intent(user_input)
        
        # 2. Memory: Fetch relevant context
        context = self.memory.get_context()
        
        # 3. HRM: Execute Logic on the structured data
        logic_output = self.hrm.process(intent, context)
        
        # 4. Meta-Core: Execute actions based on HRM output
        final_response = ""
        
        if logic_output["action"] == "SAVE_PREFERENCE":
            self.memory.update_preference(logic_output["key"], logic_output["value"])
            final_response = logic_output["response"]
            
        elif logic_output["action"] == "EXECUTE_PLAN":
            final_response = f"{logic_output['response']}\nSteps: {logic_output['plan_steps']}"
            
        elif logic_output["action"] == "RETRIEVE":
            final_response = logic_output["response"]
            
        else:
            # Fallback to LLM generation (Simulated for Phase 0)
            final_response = self.llm.generate(user_input)

        # 5. Episodic Write: Save the loop
        self.memory.add_episodic(user_input, final_response)
        
        return final_response

if __name__ == "__main__":
    core = MetaCognitiveCore()
    print("Adaptheon is listening. (Type 'quit' to exit)")
    
    while True:
        try:
            u_input = input("\n> ")
            if u_input.lower() in ["quit", "exit"]:
                break
            
            response = core.run_cycle(u_input)
            print(f"\n[Adaptheon]: {response}")
            
        except KeyboardInterrupt:
            print("\n[SYSTEM] Hibernating...")
            break
