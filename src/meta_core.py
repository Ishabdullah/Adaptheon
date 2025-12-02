from components.memory import MemorySystem
from components.llm_interface import LanguageSystem
from components.hrm import HierarchicalReasoningMachine
from components.knowledge_scout import KnowledgeScout
import time

class MetaCognitiveCore:
    def __init__(self):
        print("\n[SYSTEM] Booting Adaptheon Phase 1.0...")
        self.memory = MemorySystem()
        self.llm = LanguageSystem()
        self.hrm = HierarchicalReasoningMachine()
        self.scout = KnowledgeScout() # The new module
        print("[SYSTEM] All Cognitive Modules Online.\n")

    def run_cycle(self, user_input):
        print(f"─── [Input Received] ───")
        
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
            final_response = f"{logic_output['response']}\nSteps: {logic_output['plan_steps']}"
            
        elif logic_output["action"] == "RETRIEVE":
            final_response = logic_output["response"]
            
        elif logic_output["action"] == "TRIGGER_SCOUT":
            # The Meta-Core pauses to let the Scout run
            print(f"  [Meta-Core] Unknown entity detected. Authorizing Scout launch...")
            scout_result = self.scout.search(logic_output["topic"])
            
            if scout_result["status"] == "FOUND":
                # Learn the new fact immediately
                self.memory.update_preference(f"knowledge_{logic_output['topic']}", scout_result["summary"])
                final_response = f"Scout returned: {scout_result['summary']} (Source: {scout_result['source']})"
            else:
                final_response = "The Scout returned empty-handed."
            
        else:
            final_response = self.llm.generate(user_input)

        # 5. Episodic Write
        self.memory.add_episodic(user_input, final_response)
        
        return final_response

if __name__ == "__main__":
    core = MetaCognitiveCore()
    print("Adaptheon Phase 1 is listening. (Type 'quit' to exit)")
    
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
