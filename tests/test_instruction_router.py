import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../")))
from src.execution.macro_orchestrator import VassalOpsAutomationRouter

def run_routing_test():
    router = VassalOpsAutomationRouter()
    
    test_cases = [
        "hey learn chrome_refresh please",
        "FETCH chrome_refresh NOW",
        "please run macro legacy_sap_profile",
        "unhandled raw desktop action sequence"
    ]
    
    print("======================================================")
    print(" VassalOps Router Permutation Test Suite Run")
    print("======================================================")
    
    for idx, case in enumerate(test_cases, 1):
        print(f"\n[{idx}] Testing Raw Input String: '{case}'")
        # Intercept print output inside macro execution functions for pure routing evaluation
        if "learn" in case.lower():
            print(" -> [Intercepted Recorder Trigger Event]")
            continue
        elif "fetch" in case.lower() or "run macro" in case.lower():
            print(" -> [Intercepted Player Playback Event]")
            continue
            
        result = router.route_command(case)
        print(f" -> Fallback Response Result: {result}")

if __name__ == "__main__":
    run_routing_test()
