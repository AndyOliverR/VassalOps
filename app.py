import os, sys, time, json, requests, pyautogui, keyboard, pyperclip
from typing import Dict, TypedDict, Optional, List
from langgraph.graph import StateGraph, END
from langgraph.checkpoint.sqlite import SqliteSaver

sys.path.append(os.path.abspath(os.path.dirname(__file__)))

from src.ingestion.screen_capture import ScreenContextLayer
from src.ingestion.ocr_reader import VassalOpsScreenOCRReader
from src.execution.action_bridge import SystemOperatorBridge
from src.communication.voice_ledger import VassalOpsVoiceAuditor
from src.execution.app_bootstrapper import VassalOpsAppBootstrapper
from src.execution.macro_player import VassalOpsMacroPlayer
from src.ingestion.layout_profiler import VassalOpsLayoutProfiler
from src.execution.data_extractor import VassalOpsDataExtractor
from src.execution.data_sorter import VassalOpsDataSorter
from src.execution.backup_manager import VassalOpsBackupManager
from src.ingestion.context_aggregator import WorkspaceContextAggregator
from src.execution.audit_ledger import VassalOpsAuditLedger
from src.execution.macro_orchestrator import VassalOpsAutomationRouter

pyautogui.FAILSAFE = True
pyautogui.PAUSE = 0.05

class VassalOpsState(TypedDict):
    raw_user_input: str; captured_context: str; extracted_entities: Dict
    normalized_intent: Dict; proposed_actions: List[Dict]; approval_status: str

import sqlite3
db_connection = sqlite3.connect("gm_memory.db", check_same_thread=False)
memory = SqliteSaver(db_connection)

from src.execution.ollama_guard import VassalOpsOllamaGuard

# Initialize and verify local server node integrity before state graph assembly
ollama_guard = VassalOpsOllamaGuard()
ollama_guard.ensure_service_active()

screen_layer = ScreenContextLayer()
ocr_engine = VassalOpsScreenOCRReader()
operator_bridge = SystemOperatorBridge()
voice_auditor = VassalOpsVoiceAuditor()
bootstrapper = VassalOpsAppBootstrapper()
macro_player = VassalOpsMacroPlayer()
profiler = VassalOpsLayoutProfiler()
data_extractor = VassalOpsDataExtractor()
data_sorter = VassalOpsDataSorter()
backup_manager = VassalOpsBackupManager()
workspace_aggregator = WorkspaceContextAggregator()
audit_ledger = VassalOpsAuditLedger()
automation_router = VassalOpsAutomationRouter()

def capture_context_node(state: VassalOpsState) -> Dict:
    print("\n[VassalOps] [Eyes Active] Snapshotting screen and running OCR pattern trace matching...")
    cached_frame_path, drift_detected = screen_layer.capture_full_display()
    if not drift_detected and state.get("captured_context"):
        print("[VassalOps Tracker] Screen layout is static. Reusing previous frame context to save CPU cycles.")
        return {"captured_context": state["captured_context"], "extracted_entities": state.get("extracted_entities", {"urls":[],"emails":[],"windows_paths":[],"numerical_ledgers":[]})}
    
    extracted_text = ocr_engine.extract_text_from_matrix(cached_frame_path)
    if not extracted_text.strip() or "SYSTEM_FALLBACK" in extracted_text:
        clipboard_text = pyperclip.paste().strip()
        extracted_text = f"[OCR Fallback/Clipboard] {clipboard_text if clipboard_text else 'General UI Canvas Focus'}"
    
    scraped_entities = ocr_engine.extract_structural_entities(extracted_text)
    return {"captured_context": f"OCR Visual Text Map: '{extracted_text}' | Frame Anchor: {cached_frame_path}", "extracted_entities": scraped_entities}

def parse_intent_node(state: VassalOpsState) -> Dict:
    print("[VassalOps] [Brain Active] Fetching local source context and processing Ollama instruction traces...")
    
    # Intercept keyword macro workflows ('learn' / 'fetch') early to bypass LLM processing latency
    user_raw = state['raw_user_input'].lower().strip()
    if "learn" in user_raw or "fetch" in user_raw or "run macro" in user_raw:
        router_response = automation_router.route_command(state['raw_user_input'])
        steps = [{"type": "speak_log", "payload": router_response}]
        structured_steps = {'steps': steps}
        return {"normalized_intent": structured_steps, "proposed_actions": steps, "approval_status": "approved"}

    live_codebase_context = workspace_aggregator.scan_workspace_text()
    ollama_url = "http://localhost:11434/api/generate"
    system_prompt = "You are VassalOps, a seamless extension of the human mind. Convert the instruction directly into an optimization automation directive structure. Keep conversational outputs brief, direct, and simple. Do not hallucinate historical traces."
    prompt_payload = f"Sensed Screen OCR Layout: {state['captured_context']}\nUser Intent Input: {state['raw_user_input']}"
    structured_steps = None
    
    try:
        payload = {"model": "llama3", "prompt": f"{system_prompt}\n\n{prompt_payload}", "stream": False, "format": "json"}
        response = requests.post(ollama_url, json=payload, timeout=15).json()
        raw_response = response.get('response', '{}').strip()
        parsed_json = json.loads(raw_response)
        if isinstance(parsed_json, dict) and "steps" in parsed_json and isinstance(parsed_json["steps"], list):
            structured_steps = parsed_json
            print("[VassalOps Diagnostic] Ollama response schema validated successfully.")
        else:
            print("[VassalOps Diagnostic Warning] Malformed JSON fields returned from model. Activating recovery rules...")
    except Exception as e:
        print(f"[VassalOps Diagnostic Error] JSON validation trace hit a processing hurdle: {e}")
        
    if not structured_steps:
        steps = [{"type": "type_text", "payload": "echo Hello! How can I help you automate your PC today?"}]
        structured_steps = {'steps': steps}
        
    return {"normalized_intent": structured_steps, "proposed_actions": structured_steps.get("steps", []), "approval_status": "pending"}

def safety_gate_condition(state: VassalOpsState) -> str:
    return "execute_macros" if state.get("approval_status") == "approved" else END

def execute_macros_node(state: VassalOpsState) -> Dict:
    print("\n[VassalOps] [MCP Client Active] Connecting to Universal Tool Server...")
    time.sleep(1.0)
    
    # Instantiate our decoupled local Model Context Protocol engine server
    from src.execution.mcp_server import VassalOpsMCPServer
    mcp_bridge = VassalOpsMCPServer()
    
    for step in state["proposed_actions"]:
        action_type = step["type"]; payload = step["payload"]
        
        # Route core automated processes directly through our isolated MCP server handlers
        if action_type == "run_backup":
            mcp_result = mcp_bridge.call_tool("run_backup")
            print(f" [MCP Response] {mcp_result['message']}")
        elif action_type == "sort_intel":
            mcp_result = mcp_bridge.call_tool("sort_intel")
            print(f" [MCP Response] {mcp_result['message']}")
            
        # Keep specialized UI-bound and tracking functions running on standard system hooks
        elif action_type == "extract_intel": data_extractor.export_scraped_entities(state["extracted_entities"])
        elif action_type == "run_saved_macro": macro_player.execute_replay()
        elif action_type == "click_element" and "." in payload:
            app_key, element_key = payload.split(".", 1)
            if app_key not in operator_bridge.layouts: profiler.profile_active_window(app_key); operator_bridge.layouts = operator_bridge._load_layouts()
            bootstrapper.ensure_application_running(app_key); operator_bridge.execute_targeted_click(app_key, element_key)
        elif action_type == "type_text": operator_bridge.execute_text_input(payload, press_enter=False)
        elif action_type == "press_key": pyautogui.press(payload)
        elif action_type == "press_hotkey": operator_bridge.execute_system_hotkey(payload)
        elif action_type == "speak_log": print(f"[VassalOps Output] {payload}")

workflow = StateGraph(VassalOpsState)
workflow.add_node("capture_context", capture_context_node)
workflow.add_node("parse_intent", parse_intent_node)
workflow.add_node("execute_macros", execute_macros_node)
workflow.set_entry_point("capture_context")
workflow.add_edge("capture_context", "parse_intent")
workflow.add_conditional_edges("parse_intent", safety_gate_condition, {"execute_macros": "execute_macros", END: END})
workflow.add_edge("execute_macros", END)
vassalops_engine = workflow.compile(checkpointer=memory)

class VassalOpsAPI:
    def get_system_identity(self) -> dict:
        """Dynamically tracks the OS login context and user details."""
        import getpass
        username = getpass.getuser()
        return {"username": username, "avatar": ""}

    def submit_command(self, user_input: str) -> str:
        """Receives text from the HTML chat, routes it, and returns the response."""
        try:
            print(f"[UI Input Received] processing: {user_input}")
            initial_state = {
                "raw_user_input": user_input,
                "captured_context": "",
                "extracted_entities": {},
                "normalized_intent": {},
                "proposed_actions": [],
                "approval_status": "approved"
            }
            config = {"configurable": {"thread_id": "vassalops_default_session"}}
            vassalops_engine.invoke(initial_state, config=config)
            return "Action executed successfully."
        except Exception as e:
            return f"Error executing action: {str(e)}"

if __name__ == "__main__":
    import webview
    print("======================================================")
    print("VassalOps Core Engine Online -- UI Window Launching")
    print("======================================================")
    
    api_bridge = VassalOpsAPI()
    window = webview.create_window(
        title="VassalOps",
        url=os.path.abspath("storage/dashboard/index.html"),
        width=1200,
        height=800,
        resizable=True,
        text_select=True,
        js_api=api_bridge
    )
    
    # Pass the absolute path to your custom icon file directly inside the start function loop
    icon_target = os.path.abspath("storage/dashboard/vassal_icon.ico")
    webview.start(icon=icon_target)

