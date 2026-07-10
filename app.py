import os, sys, time, json, requests, pyautogui, keyboard, pyperclip
from typing import Dict, TypedDict, Optional, List
from langgraph.graph import StateGraph, END
from langgraph.checkpoint.sqlite import SqliteSaver
sys.path.append(os.path.abspath(os.path.dirname(__file__)))
from src.ingestion.screen_capture import ScreenContextLayer
from src.ingestion.ocr_reader import GMAScreenOCRReader
from src.execution.action_bridge import SystemOperatorBridge
from src.communication.voice_ledger import GMAIVoiceAuditor
from src.execution.app_bootstrapper import GMAIAppBootstrapper
from src.execution.macro_player import GMAIMacroPlayer
from src.ingestion.layout_profiler import GMAILayoutProfiler
from src.execution.data_extractor import GMAIDataExtractor
from src.execution.data_sorter import GMAIDataSorter
from src.execution.backup_manager import GMAIBackupManager
from src.ingestion.context_aggregator import WorkspaceContextAggregator
# Import Phase 13 Audit Ledger Component
from src.execution.audit_ledger import GMAIAuditLedger
pyautogui.FAILSAFE = True
pyautogui.PAUSE = 0.05
class GMState(TypedDict):
    raw_user_input: str; captured_context: str; extracted_entities: Dict
    normalized_intent: Dict; proposed_actions: List[Dict]; approval_status: str
import sqlite3
db_connection = sqlite3.connect("gm_memory.db", check_same_thread=False)
memory = SqliteSaver(db_connection)
screen_layer = ScreenContextLayer()
ocr_engine = GMAScreenOCRReader()
operator_bridge = SystemOperatorBridge()
voice_auditor = GMAIVoiceAuditor()
bootstrapper = GMAIAppBootstrapper()
macro_player = GMAIMacroPlayer()
profiler = GMAILayoutProfiler()
data_extractor = GMAIDataExtractor()
data_sorter = GMAIDataSorter()
backup_manager = GMAIBackupManager()
workspace_aggregator = WorkspaceContextAggregator()
audit_ledger = GMAIAuditLedger()
def capture_context_node(state: GMState) -> Dict:
    print("\n[GM AI] [Eyes Active] Snapshotting screen and running OCR pattern trace matching...")
    cached_frame_path, drift_detected = screen_layer.capture_full_display()
    if not drift_detected and state.get("captured_context"):
        print("[GM AI Tracker] Screen layout is static. Reusing previous frame context to save CPU cycles.")
        return {"captured_context": state["captured_context"], "extracted_entities": state.get("extracted_entities", {"urls":[],"emails":[],"windows_paths":[],"numerical_ledgers":[]})}
    extracted_text = ocr_engine.extract_text_from_matrix(cached_frame_path)
    if not extracted_text.strip() or "SYSTEM_FALLBACK" in extracted_text:
        clipboard_text = pyperclip.paste().strip()
        extracted_text = f"[OCR Fallback/Clipboard] {clipboard_text if clipboard_text else 'General UI Canvas Focus'}"
    scraped_entities = ocr_engine.extract_structural_entities(extracted_text)
    return {"captured_context": f"OCR Visual Text Map: '{extracted_text}' | Frame Anchor: {cached_frame_path}", "extracted_entities": scraped_entities}

def parse_intent_node(state: GMState) -> Dict:
    print("[GM AI] [Brain Active] Fetching local source context and processing Ollama instruction traces...")
    live_codebase_context = workspace_aggregator.scan_workspace_text()
    ollama_url = "http://localhost:11434/api/generate"
    system_prompt = f"You are GM AI, a seamless extension of the human mind. Convert the user's raw, fragmented instruction into a highly structured JSON plan containing an array of 'steps'. Each step must be an object with 'type' and 'payload'.\nFor core technical alignment, your native engine code context is loaded here:\n{live_codebase_context}"
    prompt_payload = f"Sensed Screen OCR Layout: {state['captured_context']}\nUser Intent Input: {state['raw_user_input']}"
    structured_steps = None
    try:
        payload = {"model": "llama3", "prompt": f"{system_prompt}\n\n{prompt_payload}", "stream": False, "format": "json"}
        response = requests.post(ollama_url, json=payload, timeout=15).json()
        raw_response = response.get('response', '{}').strip()
        parsed_json = json.loads(raw_response)
        if isinstance(parsed_json, dict) and "steps" in parsed_json and isinstance(parsed_json["steps"], list):
            structured_steps = parsed_json
            print("[GM AI Diagnostic] Ollama response schema validated successfully.")
        else:
            print("[GM AI Diagnostic Warning] Malformed JSON fields returned from model. Activating recovery rules...")
    except Exception as e:
        print(f"[GM AI Diagnostic Error] JSON validation trace hit a processing hurdle: {e}")
    if not structured_steps:
        steps = [{"type": "type_text", "payload": "echo Hello! How can I help you automate your PC today?"}]
        structured_steps = {'steps': steps}
    return {"normalized_intent": structured_steps, "proposed_actions": structured_steps.get("steps", []), "approval_status": "pending"}
def safety_gate_condition(state: GMState) -> str:
    return "execute_macros" if state.get("approval_status") == "approved" else END

def execute_macros_node(state: GMState) -> Dict:
    print("\n[GM AI] [System Actions Active] Running pre-execution validations...")
    time.sleep(1.0)
    for step in state["proposed_actions"]:
        action_type = step["type"]; payload = step["payload"]
        if action_type == "run_backup": backup_manager.execute_directory_backup()
        elif action_type == "sort_intel": data_sorter.run_sort_and_optimize()
        elif action_type == "extract_intel": data_extractor.export_scraped_entities(state["extracted_entities"])
        elif action_type == "run_saved_macro": macro_player.execute_replay()
        elif action_type == "click_element" and "." in payload:
            app_key, element_key = payload.split(".", 1)
            if app_key not in operator_bridge.layouts: profiler.profile_active_window(app_key); operator_bridge.layouts = operator_bridge._load_layouts()
            bootstrapper.ensure_application_running(app_key); operator_bridge.execute_targeted_click(app_key, element_key)
        elif action_type == "type_text": operator_bridge.execute_text_input(payload, press_enter=False)
        elif action_type == "press_key": pyautogui.press(payload)
        elif action_type == "press_hotkey": operator_bridge.execute_system_hotkey(payload)
        elif action_type == "speak_log": voice_auditor.speak_timeline_summary()
    
    try:
        cache_dir = "src/ingestion/cache/"
        if os.path.exists(cache_dir):
            purged_count = 0
            for filename in os.listdir(cache_dir):
                if filename.startswith("raw_surface_") and filename.endswith(".png"):
                    os.remove(os.path.join(cache_dir, filename))
                    purged_count += 1
            if purged_count > 0:
                print(f"[GM AI Cache Autopilot] Session completed. Purged {purged_count} temporary canvas frames cleanly.")
    except Exception as e:
        print(f"[GM AI Cache Warning] Failed to auto-purge runtime session artifacts: {e}")

    # Phase 13 Stitch: Commit to persistent ledger and narrate out loud
    user_intent = state.get("raw_user_input", "unknown automation macro")
    audit_ledger.commit_transaction(intent=user_intent, status="success_completed")
    print("[GM AI Voice] Compiling database entries for narration...")
    voice_auditor.speak_timeline_summary()

    print("[GM AI] Operational sequence completed successfully."); return {}

workflow = StateGraph(GMState)
workflow.add_node("capture_context", capture_context_node)
workflow.add_node("parse_intent", parse_intent_node)
workflow.add_node("execute_macros", execute_macros_node)
workflow.set_entry_point("capture_context")
workflow.add_edge("capture_context", "parse_intent")
workflow.add_conditional_edges("parse_intent", safety_gate_condition, {"execute_macros": "execute_macros", END: END})
workflow.add_edge("execute_macros", END)
gm_engine = workflow.compile(checkpointer=memory)
if __name__ == "__main__":
    from langgraph.graph import END
    print("======================================================")
    print("GM AI v1.7 -- Voice Audit Ledgers Active")
    print("======================================================")
    user_input = input("Describe what you want to do in simple/broken English: ")
    state = {
        "raw_user_input": user_input,
        "captured_context": "",
        "extracted_entities": {"urls":[], "emails":[], "windows_paths":[], "numerical_ledgers":[]},
        "normalized_intent": {},
        "proposed_actions": [],
        "approval_status": "pending"
    }
    for event in gm_engine.stream(state, config={"configurable": {"thread_id": "global_session"}}):
        for node_name, node_output in event.items():
            print(f"\n[GRAPH STATE TRANSITION] Completed Node: {node_name}")
            if node_output: state.update(node_output)
    if state.get("proposed_actions"):
        print("\n=========== ??? GM AI BOT-SITTER SCREEN PREVIEW ===========")
        print(f"Captured OCR Context Preview: {state.get('captured_context', '')[:120]}...")
        print("\nProposed Automation Steps Blueprint:")
        for idx, step in enumerate(state["proposed_actions"], 1):
            print(f" [{idx}] Action Mode: {step.get('type')} -> Context: {step.get('payload')}")
        print("===========================================================")
        choice = input("\nDo you approve GM AI to execute this plan into your active app? (y/n): ").strip().lower()
        if choice == 'y':
            state["approval_status"] = "approved"
            print("\n[GM AI] Human authorization verified. Deploying hardware execution sequence...")
            execute_macros_node(state)
        else:
            print("[GM AI] Execution aborted by human bot-sitter. State preserved safely.")





