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
from src.execution.action_firewall import VassalOpsActionFirewall
from src.ingestion.secret_redactor import redact_secrets
from src.execution.macro_recorder import VassalOpsMacroRecorder

pyautogui.FAILSAFE = True
pyautogui.PAUSE = 0.05

def load_runtime_config() -> dict:
    """Reads model host/port/name from config.json with safe defaults."""
    defaults = {
        "active_model": "llama3",
        "host_address": "127.0.0.1",
        "port_mapping": 11434,
    }
    config_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "config.json")
    try:
        with open(config_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        model_cfg = data.get("model_configuration", {})
        return {
            "active_model": model_cfg.get("active_model", defaults["active_model"]),
            "host_address": model_cfg.get("host_address", defaults["host_address"]),
            "port_mapping": int(model_cfg.get("port_mapping", defaults["port_mapping"])),
        }
    except Exception as e:
        print(f"[VassalOps] Warning: could not load config.json ({e}); using defaults.")
        return defaults

RUNTIME_CONFIG = load_runtime_config()

class VassalOpsState(TypedDict):
    raw_user_input: str; captured_context: str; extracted_entities: Dict
    normalized_intent: Dict; proposed_actions: List[Dict]; approval_status: str

import sqlite3
db_connection = sqlite3.connect("gm_memory.db", check_same_thread=False)
memory = SqliteSaver(db_connection)

from src.execution.ollama_guard import VassalOpsOllamaGuard

# Initialize and verify local server node integrity before state graph assembly
ollama_guard = VassalOpsOllamaGuard(port=RUNTIME_CONFIG["port_mapping"])
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
action_firewall = VassalOpsActionFirewall()

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
    safe_text = redact_secrets(extracted_text)
    return {"captured_context": f"OCR Visual Text Map: '{safe_text}' | Frame Anchor: {cached_frame_path}", "extracted_entities": scraped_entities}

def parse_intent_node(state: VassalOpsState) -> Dict:
    print("[VassalOps] [Brain Active] Fetching local source context and processing Ollama instruction traces...")
    
    user_raw = state['raw_user_input'].lower().strip()

    # Local date/time answers without model round-trip
    if any(k in user_raw for k in ("what date", "what's the date", "whats the date", "what time", "what's the time", "whats the time", "current date", "current time")):
        import datetime
        now = datetime.datetime.now().strftime("%A, %B %d, %Y %I:%M %p")
        steps = [{"type": "speak_log", "payload": f"The current date and time is {now}."}]
        return {"normalized_intent": {"steps": steps}, "proposed_actions": steps, "approval_status": "pending"}

    # Propose learn/fetch only — side effects run after Approve in execute_macros_node
    if "learn" in user_raw:
        macro_name = automation_router.extract_macro_filename(state["raw_user_input"], "learn")
        steps = [
            {"type": "learn_macro", "payload": macro_name},
            {"type": "speak_log", "payload": f"Ready to record macro '{macro_name}'. After Approve, perform the task then press Escape to stop."},
        ]
        return {"normalized_intent": {"steps": steps}, "proposed_actions": steps, "approval_status": "pending"}

    if "fetch" in user_raw or "run macro" in user_raw:
        keyword = "fetch" if "fetch" in user_raw else "run macro"
        macro_name = automation_router.extract_macro_filename(state["raw_user_input"], "fetch" if "fetch" in user_raw else "run")
        if keyword == "run macro" and macro_name == "recorded_macro.json":
            # Prefer text after "run macro"
            macro_name = automation_router.extract_macro_filename(state["raw_user_input"].lower().replace("run macro", "fetch", 1), "fetch")
        steps = [
            {"type": "run_saved_macro", "payload": macro_name},
            {"type": "speak_log", "payload": f"Ready to replay macro '{macro_name}' after you Approve."},
        ]
        return {"normalized_intent": {"steps": steps}, "proposed_actions": steps, "approval_status": "pending"}

    host = RUNTIME_CONFIG["host_address"]
    port = RUNTIME_CONFIG["port_mapping"]
    model_name = RUNTIME_CONFIG["active_model"]
    ollama_url = f"http://{host}:{port}/api/generate"
    system_prompt = (
        "You are VassalOps, a desktop automation planner. "
        "Return ONLY JSON with a top-level 'steps' array. Each step is "
        "{\"type\": one of type_text|press_key|press_hotkey|click_element|speak_log|run_backup|sort_intel|extract_intel, "
        "\"payload\": string}. "
        "For simple questions (facts, greetings), use a single speak_log step. "
        "Keep payloads brief. Do not invent click_element targets you are unsure about."
    )
    safe_context = redact_secrets(state.get("captured_context") or "")
    safe_user_input = redact_secrets(state.get("raw_user_input") or "")
    prompt_payload = f"Sensed Screen OCR Layout: {safe_context}\nUser Intent Input: {safe_user_input}"
    structured_steps = None
    
    try:
        payload = {"model": model_name, "prompt": f"{system_prompt}\n\n{prompt_payload}", "stream": False, "format": "json"}
        response = requests.post(ollama_url, json=payload, timeout=60).json()
        raw_response = response.get('response', '{}').strip()
        parsed_json = json.loads(raw_response)
        if isinstance(parsed_json, dict) and "steps" in parsed_json and isinstance(parsed_json["steps"], list):
            structured_steps = parsed_json
            print(f"[VassalOps Diagnostic] Ollama model '{model_name}' response schema validated.")
        else:
            print("[VassalOps Diagnostic Warning] Malformed JSON fields returned from model. Activating recovery rules...")
    except Exception as e:
        print(f"[VassalOps Diagnostic Error] JSON validation trace hit a processing hurdle: {e}")
        steps = [{"type": "speak_log", "payload": f"I could not reach the local model '{model_name}'. Check Ollama is running and config.json active_model is installed."}]
        return {"normalized_intent": {"steps": steps}, "proposed_actions": steps, "approval_status": "pending"}
        
    if not structured_steps:
        steps = [{"type": "speak_log", "payload": "Hello! How can I help you automate your PC today?"}]
        structured_steps = {'steps': steps}
        
    return {"normalized_intent": structured_steps, "proposed_actions": structured_steps.get("steps", []), "approval_status": "pending"}

def safety_gate_condition(state: VassalOpsState) -> str:
    return "execute_macros" if state.get("approval_status") == "approved" else END

def execute_macros_node(state: VassalOpsState) -> Dict:
    print("\n[VassalOps] [ToolRouter] Dispatching approved automation steps...")
    time.sleep(0.2)
    
    from src.execution.tool_router import VassalOpsToolRouter
    tool_router = VassalOpsToolRouter()
    
    for step in state["proposed_actions"]:
        verdict = action_firewall.verify_step(step)
        if verdict["status"] != "VERIFIED":
            print(f" [Firewall] Rejected step: {verdict['reason']}")
            continue

        action_type = step["type"]; payload = step.get("payload", "")
        
        if action_type == "run_backup":
            mcp_result = tool_router.call_tool("run_backup")
            print(f" [ToolRouter] {mcp_result['message']}")
        elif action_type == "sort_intel":
            mcp_result = tool_router.call_tool("sort_intel")
            print(f" [ToolRouter] {mcp_result['message']}")
        elif action_type == "learn_macro":
            recorder = VassalOpsMacroRecorder(output_filename=str(payload))
            recorder.start_recording()
            print(f" [Macro] Recording started for {payload}")
        elif action_type == "run_saved_macro":
            player = VassalOpsMacroPlayer(target_filename=str(payload))
            ok = player.execute_replay()
            print(f" [Macro] Replay {'succeeded' if ok else 'failed'} for {payload}")
        elif action_type == "extract_intel": data_extractor.export_scraped_entities(state["extracted_entities"])
        elif action_type == "click_element" and "." in str(payload):
            app_key, element_key = str(payload).split(".", 1)
            if app_key not in operator_bridge.layouts: profiler.profile_active_window(app_key); operator_bridge.layouts = operator_bridge._load_layouts()
            bootstrapper.ensure_application_running(app_key); operator_bridge.execute_targeted_click(app_key, element_key)
        elif action_type == "type_text": operator_bridge.execute_text_input(payload, press_enter=False)
        elif action_type == "press_key": pyautogui.press(payload)
        elif action_type == "press_hotkey": operator_bridge.execute_system_hotkey(payload)
        elif action_type == "speak_log": print(f"[VassalOps Output] {payload}")

    return {}
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
        cleaned = user_input.lower().strip()
        
        # Intercept and route conversational ambient diagnostic questions instantly
        if "health" in cleaned or "optimize system" in cleaned or "check system" in cleaned:
            from src.execution.diagnostics_engine import VassalOpsMainDirectorAgent
            director = VassalOpsMainDirectorAgent()
            return director.run_agent_health_check()
            
        # Intercept and trigger the automated regression proving bench
        elif "regression" in cleaned or "verify patch" in cleaned or "run test" in cleaned:
            from src.execution.regression_tester import VassalOpsRegressionTester
            tester = VassalOpsRegressionTester()
            report = tester.prove_proposed_fix("Calibrate coordinate clipping boundaries and inject safety latency padding")
            
            output = "### VassalOps Proving & Regression Bench Report\n"
            output += f"- **Verification Result:** {'✅ PASS - Safe to Merge' if report['success'] else '❌ FAIL - Regressions Detected'}\n"
            output += f"- **Benchmark Accuracy Score:** {report['score']}\n\n"
            output += "#### Executed Test Cases:\n"
            for item in report["detailed_run"]:
                output += f"- `{item['case_id']}`: **{item['status']}**\n"
            return output
            
        # Intercept and trigger the newly added advanced automated sleep-time memory loop
        elif "sleep" in cleaned or "optimize memory" in cleaned or "update memory" in cleaned:
            from src.execution.diagnostics_engine import VassalOpsMainDirectorAgent
            director = VassalOpsMainDirectorAgent()
            result_msg = director.execute_sleeptime_compute()
            
            output = "### VassalOps Sleep-Time Compute Active\n"
            output += f"- **Trace Target:** Meta-inspecting previous internal framework execution steps.\n"
            output += f"- **Loop Status:** {result_msg}\n\n"
            output += "💡 *Notice: The long-term preference directives inside `storage/agent.md` have been updated dynamically based on system experience graphs.*"
            return output
            
        try:
            print(f"[UI Input Received] processing: {user_input}")
            thread_id = "vassalops_default_session"
            initial_state = {
                "raw_user_input": user_input,
                "captured_context": "",
                "extracted_entities": {},
                "normalized_intent": {},
                "proposed_actions": [],
                "approval_status": "pending"
            }
            config = {"configurable": {"thread_id": thread_id}}
            vassalops_engine.invoke(initial_state, config=config)
            current_state = vassalops_engine.get_state(config).values
            proposed = current_state.get("proposed_actions") or []
            return json.dumps({
                "status": "pending_approval",
                "thread_id": thread_id,
                "proposed_actions": proposed,
                "message": "Review the proposed steps, then Approve or Reject."
            })
        except Exception as e:
            return f"Error executing action: {str(e)}"

    def confirm_plan(self, approved: bool) -> str:
        """Bot-sitter gate: execute or discard the pending plan for the UI session."""
        thread_id = "vassalops_default_session"
        config = {"configurable": {"thread_id": thread_id}}
        try:
            snapshot = vassalops_engine.get_state(config)
            current_state = dict(snapshot.values) if snapshot and snapshot.values else {}
            proposed = current_state.get("proposed_actions") or []

            if not proposed:
                return "No pending plan to confirm."

            if not approved:
                current_state["approval_status"] = "rejected"
                print("[VassalOps] Plan rejected by bot-sitter.")
                return "Plan rejected. No desktop actions were executed."

            current_state["approval_status"] = "approved"
            print("[VassalOps] Plan approved by bot-sitter. Executing macros...")
            execute_macros_node(current_state)
            return "Action executed successfully."
        except Exception as e:
            return f"Error confirming plan: {str(e)}"

def force_win32_window_icon():
    """Win32 Kernel Hack: Forces Windows to paint vassal_icon.ico onto the title bar frame directly."""
    import ctypes
    import time
    
    # Give pywebview a brief moment to draw the window canvas frame shell
    time.sleep(1.0)
    
    # Define underlying Win32 API user functions and constants
    user32 = ctypes.windll.user32
    WM_SETICON = 0x0080
    ICON_SMALL = 0
    ICON_BIG = 1
    LR_LOADFROMFILE = 0x00000010
    IMAGE_ICON = 1
    
    # Locate the active system window handle matching our exact canvas title property
    hwnd = user32.FindWindowW(None, "VassalOps")
    if hwnd:
        icon_path = os.path.abspath("storage/dashboard/vassal_icon.ico")
        if os.path.exists(icon_path):
            # Read and compile the icon file directly into a Windows system graphics handle
            hicon = user32.LoadImageW(0, icon_path, IMAGE_ICON, 0, 0, LR_LOADFROMFILE)
            if hicon:
                # Force-send structural messages to the OS layout to paint the icon on the title bar
                user32.SendMessageW(hwnd, WM_SETICON, ICON_SMALL, hicon)
                user32.SendMessageW(hwnd, WM_SETICON, ICON_BIG, hicon)
                print("[VassalOps Win32] Success: System title bar icon forced via kernel memory handles.")

if __name__ == "__main__":
    import webview
    import threading
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
    
    # Spawn our native Win32 icon injector quietly on a background thread
    threading.Thread(target=force_win32_window_icon, daemon=True).start()
    
    webview.start()
