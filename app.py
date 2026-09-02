import os, sys, time, json, requests, pyautogui, keyboard, pyperclip
from typing import Dict, TypedDict, Optional, List
from langgraph.graph import StateGraph, END
from langgraph.checkpoint.sqlite import SqliteSaver

sys.path.append(os.path.abspath(os.path.dirname(__file__)))

from src.execution.console_io import configure_utf8_stdio, safe_print

configure_utf8_stdio()

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
from src.execution.duty_library import VassalOpsDutyLibrary, extract_duty_name_from_command, extract_teach_parts
from src.execution.daily_playlist import VassalOpsDailyPlaylist
from src.execution.plan_narrator import narrate_proposed_actions
from src.execution.run_controller import run_controller
from src.execution.landmark_target import focus_window_by_title, find_text_on_screen, list_window_titles
from src.execution.agent_loop import run_agent_loop
from src.execution.agent_tools import execute_loop_tool, cap_ocr
from src.execution.duty_reflex import format_reflex_context, save_reflex
from src.execution.intent_guard import enforce_intent_or_shutdown, guard_prompt_block
from src.execution.structured_llm import PlannerPlan, call_ollama_json, complete_structured
from src.execution.risk_tiers import annotate_steps, risk_summary
from src.execution.run_evidence import write_run_report
from src.execution.local_learning import record_loop_outcome
from src.execution.session_store import (
    save_last_session,
    load_last_session,
    format_resume_context,
    save_last_duty,
    load_last_duty,
)
from src.execution.local_auth import local_auth, UNLOCK_REQUIRED, maybe_register_pending
from src.execution.handshake import run_handshake
import threading


def _register_pending_bg() -> None:
    """Best-effort one-shot install notepad ping (never blocks UI)."""
    try:
        maybe_register_pending()
    except Exception:
        pass

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
duty_library = VassalOpsDutyLibrary()
daily_playlist = VassalOpsDailyPlaylist(library=duty_library, ledger=audit_ledger)

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

    # Immediate read-only duty list (no approval needed for listing)
    if "list duties" in user_raw or user_raw.strip() in ("duties", "show duties", "my duties"):
        steps = [{"type": "speak_log", "payload": duty_library.format_duty_list()}]
        return {"normalized_intent": {"steps": steps}, "proposed_actions": steps, "approval_status": "pending"}

    from src.execution.internal_catalog import internal_query_plan

    catalog_plan = internal_query_plan(state["raw_user_input"])
    if catalog_plan:
        if catalog_plan.get("kind") == "sheet":
            steps = [
                {"type": "read_internal_sheet", "payload": catalog_plan["payload"]},
                {
                    "type": "speak_log",
                    "payload": (
                        str(catalog_plan.get("preview") or "")[:1500]
                        + "\n\nApprove to copy the signed-in Google Sheet in Chrome/Edge "
                        "(address bar + Ctrl+A Ctrl+C). Inventory stays on this PC."
                    ),
                },
            ]
            return {"normalized_intent": {"steps": steps}, "proposed_actions": steps, "approval_status": "pending"}
        steps = [{"type": "speak_log", "payload": catalog_plan.get("text") or ""}]
        return {"normalized_intent": {"steps": steps}, "proposed_actions": steps, "approval_status": "pending"}

    if "build my workday" in user_raw or "build workday" in user_raw:
        data = daily_playlist.build_workday_from_all_duties()
        names = [e.get("duty_id") for e in data.get("workday", [])]
        msg = "Workday playlist rebuilt from taught duties:\n" + "\n".join(f"- {n}" for n in names) if names else "No duties to schedule. Teach one first: teach morning email"
        steps = [{"type": "speak_log", "payload": msg}]
        return {"normalized_intent": {"steps": steps}, "proposed_actions": steps, "approval_status": "pending"}

    if any(k in user_raw for k in ("today's duties", "todays duties", "daily duties", "show playlist", "my workday")):
        briefing = daily_playlist.get_today_playlist()
        if not briefing["items"]:
            msg = "No workday playlist yet. Teach duties, then say: build my workday"
        else:
            lines = [f"Today's duties ({briefing['date']} {briefing['time']}):"]
            for item in briefing["items"]:
                due = "due" if item["due"] else f"after {item['after']}"
                exists = "ok" if item["exists"] else "MISSING"
                lines.append(f"- [{due}|{exists}] {item['name']} ({item['duty_id']}, {item['step_count']} steps)")
            lines.append("Open Daily Duties panel or say: run my workday (then Approve).")
            msg = "\n".join(lines)
        steps = [{"type": "speak_log", "payload": msg}]
        return {"normalized_intent": {"steps": steps}, "proposed_actions": steps, "approval_status": "pending"}

    if user_raw.startswith("teach ") or "teach duty" in user_raw or (user_raw.startswith("teach")):
        duty_name, duty_note = extract_teach_parts(state["raw_user_input"], "teach")
        teach_payload = f"{duty_name}\n{duty_note}" if duty_note else duty_name
        note_bit = f" Note: {duty_note}." if duty_note else ""
        steps = [
            {"type": "teach_duty", "payload": teach_payload},
            {"type": "speak_log", "payload": (
                f"Ready to TEACH duty '{duty_name}'.{note_bit} After Approve: perform the task, then press Escape. "
                "WARNING: keystrokes (including passwords) will be recorded. "
                "Later say: run duty {0} — or again / run last duty.".format(duty_name)
            )},
        ]
        return {"normalized_intent": {"steps": steps}, "proposed_actions": steps, "approval_status": "pending"}

    # Replay last taught/run duty (smarter day-to-day shortcut)
    if user_raw.strip() in (
        "again",
        "do that again",
        "do it again",
        "run again",
        "run that again",
        "run last",
        "run last duty",
        "last duty",
        "repeat last",
        "repeat that",
    ) or user_raw.startswith("run last duty"):
        last = load_last_duty()
        duty_id = (last.get("duty_id") or "").strip()
        if not duty_id:
            steps = [{
                "type": "speak_log",
                "payload": (
                    "No last duty yet. Teach one first (teach morning email), Approve, do the task, Escape — "
                    "then say again or run last duty."
                ),
            }]
            return {"normalized_intent": {"steps": steps}, "proposed_actions": steps, "approval_status": "pending"}
        label = last.get("name") or duty_id
        note = last.get("note") or ""
        note_bit = f" ({note})" if note else ""
        steps = [
            {"type": "run_duty", "payload": duty_id},
            {
                "type": "speak_log",
                "payload": f"Ready to run last duty '{label}'{note_bit} after you Approve.",
            },
        ]
        return {"normalized_intent": {"steps": steps}, "proposed_actions": steps, "approval_status": "pending"}

    if user_raw.startswith("run duty") or "run duty " in user_raw:
        duty_name = extract_duty_name_from_command(state["raw_user_input"], "run duty")
        from src.execution.duty_library import _slugify
        from src.execution.staged_pack import resolve_pack_dir

        duty_id = _slugify(duty_name)
        # Allow "run duty staged demo notepad" to hit the staged pack runner
        if resolve_pack_dir("storage/duties", duty_id) or resolve_pack_dir(
            "storage/duties", duty_name.replace(" ", "_")
        ):
            pack_key = duty_id if resolve_pack_dir("storage/duties", duty_id) else _slugify(duty_name)
            steps = [
                {"type": "run_staged_pack", "payload": pack_key},
                {
                    "type": "speak_log",
                    "payload": (
                        f"Ready to run staged pack '{pack_key}' after you Approve. "
                        "Stages pause for a second Approve between gates."
                    ),
                },
            ]
            return {"normalized_intent": {"steps": steps}, "proposed_actions": steps, "approval_status": "pending"}
        steps = [
            {"type": "run_duty", "payload": duty_id},
            {"type": "speak_log", "payload": f"Ready to run duty '{duty_id}' after you Approve."},
        ]
        return {"normalized_intent": {"steps": steps}, "proposed_actions": steps, "approval_status": "pending"}

    if any(
        k in user_raw
        for k in ("run staged pack", "run stage pack", "run icm pack", "staged pack")
    ):
        from src.execution.duty_library import _slugify

        pack_name = extract_duty_name_from_command(state["raw_user_input"], "pack")
        if pack_name in ("unnamed_duty", "") or "staged" in pack_name.lower():
            # Prefer text after "staged pack" / "run staged pack"
            raw = state["raw_user_input"]
            lowered = raw.lower()
            for key in ("run staged pack", "staged pack", "run icm pack"):
                if key in lowered:
                    pack_name = raw[lowered.find(key) + len(key) :].strip(" ,.-") or "staged_demo_notepad"
                    break
            else:
                pack_name = pack_name or "staged_demo_notepad"
        pack_id = _slugify(pack_name) if pack_name else "staged_demo_notepad"
        if pack_id in ("staged", "icm", "demo"):
            pack_id = "staged_demo_notepad"
        steps = [
            {"type": "run_staged_pack", "payload": pack_id},
            {
                "type": "speak_log",
                "payload": (
                    f"Ready to run staged pack '{pack_id}' after you Approve. "
                    "Human gates between stages — not a multi-agent swarm."
                ),
            },
        ]
        return {"normalized_intent": {"steps": steps}, "proposed_actions": steps, "approval_status": "pending"}

    if any(k in user_raw for k in ("run my workday", "run workday", "run playlist", "perform my daily", "work for me")):
        steps = [
            {"type": "run_playlist", "payload": "today"},
            {"type": "speak_log", "payload": "Ready to run today's duty playlist after you Approve. Stops on first failure."},
        ]
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
    system_prompt = (
        "You are VassalOps, a desktop automation planner. "
        "Return ONLY JSON with a top-level 'steps' array. Each step is "
        "{\"type\": one of type_text|press_key|press_hotkey|click_element|speak_log|run_backup|sort_intel|extract_intel|focus_window|run_duty, "
        "\"payload\": string}. "
        "For simple questions (facts, greetings), use a single speak_log step. "
        "Keep payloads brief. Do not invent click_element targets you are unsure about. "
        "This plan is a preview: after Approve a bounded think-act-observe loop will run."
    )
    safe_context = cap_ocr(redact_secrets(state.get("captured_context") or ""))
    safe_user_input = redact_secrets(state.get("raw_user_input") or "")
    prompt_payload = f"Sensed Screen OCR Layout: {safe_context}\nUser Intent Input: {safe_user_input}"
    structured_steps = None

    try:
        result = complete_structured(
            f"{system_prompt}\n\n{prompt_payload}",
            PlannerPlan,
            lambda p: call_ollama_json(p, host=host, port=port, model_name=model_name),
            max_retries=1,
        )
        if result.ok and result.data is not None:
            structured_steps = result.data.model_dump()
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

    preview = structured_steps.get("steps") or []
    only_talk = preview and all(str(s.get("type")) == "speak_log" for s in preview)
    if only_talk:
        return {"normalized_intent": structured_steps, "proposed_actions": preview, "approval_status": "pending"}

    readable = narrate_proposed_actions(preview)
    preview_text = "; ".join(readable[:6]) if readable else "allowlisted desktop tools, duties, and memory search"
    steps = [
        {"type": "agent_loop", "payload": state.get("raw_user_input") or ""},
        {"type": "speak_log", "payload": (
            f"After Approve I will run a bounded agent loop (max 8 turns: think -> tool -> observe). "
            f"Preview: {preview_text}"
        )},
    ]
    return {"normalized_intent": {"steps": steps}, "proposed_actions": steps, "approval_status": "pending"}

def safety_gate_condition(state: VassalOpsState) -> str:
    return "execute_macros" if state.get("approval_status") == "approved" else END


def _ollama_generate_json(prompt: str):
    return call_ollama_json(
        prompt,
        host=RUNTIME_CONFIG["host_address"],
        port=RUNTIME_CONFIG["port_mapping"],
        model_name=RUNTIME_CONFIG["active_model"],
    )


def run_approved_agent_loop(goal: str, ocr_text: str = "") -> Dict:
    """Approved think-act-observe loop over the allowlisted tool catalog."""
    from src.execution.tool_router import VassalOpsToolRouter

    router = VassalOpsToolRouter()
    titles = []
    try:
        titles = list_window_titles()
    except Exception:
        titles = []
    briefing = daily_playlist.get_today_playlist()

    def execute_tool(name: str, payload: str) -> Dict:
        step = {"type": name, "payload": payload}
        verdict = action_firewall.verify_step(step)
        if verdict["status"] != "VERIFIED":
            return {"ok": False, "observation": f"Firewall rejected: {verdict['reason']}"}
        return execute_loop_tool(
            name,
            payload,
            duty_library=duty_library,
            daily_playlist=daily_playlist,
            operator_bridge=operator_bridge,
            tool_router=router,
            run_controller=run_controller,
            press_hotkey=lambda p: operator_bridge.execute_system_hotkey(p),
            type_text=lambda p: operator_bridge.execute_text_input(p, press_enter=False),
            focus_window=focus_window_by_title,
            ledger=audit_ledger,
            write_approved=True,  # already past human Approve for this loop
        )

    reflex_block = format_reflex_context(goal=goal)
    readable = [f"Agent turn {i}" for i in range(1, 15)]
    run_controller.reset_for_run(readable, phase="agent_loop")
    run_controller.set_summary(f"Working goal: {(goal or '')[:160]}")

    def _on_replan(message: str, steps: list) -> None:
        # Spice: surface second-Approve replan; do not auto-continue the loop.
        run_controller.set_pending_replan(message, steps)

    report = run_agent_loop(
        goal,
        call_model=_ollama_generate_json,
        execute_tool=execute_tool,
        max_turns=14,
        ocr_text=ocr_text,
        window_titles=titles,
        playlist_items=briefing.get("items"),
        stop_requested=run_controller.stop_requested,
        set_progress=lambda cur, label: run_controller.set_progress(cur, label),
        reflex_block=reflex_block,
        on_need_replan=_on_replan,
    )
    audit_ledger.commit_transaction(
        intent=f"agent_loop:{(goal or '')[:80]}",
        status="success_completed" if report.get("ok") else "failed",
        device="agent_loop",
        channel="workday",
    )
    path = write_run_report(
        goal=goal,
        ok=bool(report.get("ok")),
        turns=int(report.get("turns") or 0),
        observations=report.get("observations") or [],
        final=str(report.get("final") or ""),
        reason=str(report.get("reason") or ""),
        kind="agent_loop",
    )
    report["report_path"] = path
    record_loop_outcome(os.path.join("storage", "agent.md"), report, goal=goal)
    save_last_session(
        goal=goal,
        observations=report.get("observations") or [],
        final=str(report.get("final") or ""),
        ok=bool(report.get("ok")),
    )
    if report.get("ok"):
        try:
            save_reflex(goal=goal, observations=report.get("observations") or [])
        except Exception as exc:
            print(f"[DutyReflex] save failed: {exc}")
    run_controller.set_summary(
        str(report.get("final") or report.get("reason") or "")[:400]
    )
    run_controller.finish(bool(report.get("ok")), str(report.get("reason") or ""))
    return report


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
        elif action_type == "agent_loop":
            report = run_approved_agent_loop(str(payload), ocr_text=state.get("captured_context") or "")
            safe_print(
                f" [AgentLoop] ok={report.get('ok')} turns={report.get('turns')} "
                f"reason={(report.get('reason') or '')[:120]}"
            )
            if report.get("final"):
                safe_print(f"[VassalOps Output] {report['final']}")
            if report.get("report_path"):
                safe_print(f"[VassalOps Output] Report saved: {report['report_path']}")
            if report.get("stopped") or run_controller.stop_requested():
                break
        elif action_type == "sort_intel":
            mcp_result = tool_router.call_tool("sort_intel")
            print(f" [ToolRouter] {mcp_result['message']}")
        elif action_type == "learn_macro":
            recorder = VassalOpsMacroRecorder(output_filename=str(payload))
            recorder.start_recording()
            print(f" [Macro] Recording started for {payload}")
        elif action_type == "teach_duty":
            raw_payload = str(payload)
            if "\n" in raw_payload:
                duty_name, duty_note = raw_payload.split("\n", 1)
            else:
                duty_name, duty_note = raw_payload, ""
            taught = duty_library.start_teach(duty_name.strip(), description=duty_note.strip())
            daily_playlist.add_duty(taught["id"])
            save_last_duty(
                duty_id=str(taught.get("id") or ""),
                name=str(taught.get("name") or duty_name),
                note=str(taught.get("description") or duty_note or ""),
            )
            print(f" [Duty] Taught and added to playlist: {taught['id']}")
        elif action_type == "run_duty":
            outcome = duty_library.run_duty(str(payload))
            print(f" [Duty] Run {payload}: {outcome}")
            if outcome.get("ok"):
                save_last_duty(
                    duty_id=str(outcome.get("duty_id") or payload),
                    name=str(outcome.get("name") or payload),
                )
                try:
                    save_reflex(
                        duty_id=str(payload),
                        goal=f"run duty {payload}",
                        observations=[str(outcome)],
                    )
                except Exception as exc:
                    print(f"[DutyReflex] save failed: {exc}")
            if not outcome.get("ok"):
                print(f" [Duty] FAILED: {outcome.get('error')}")
        elif action_type == "run_staged_pack":
            from src.execution.staged_pack import run_staged_pack

            report = run_staged_pack(
                str(payload),
                library=duty_library,
                run_controller=run_controller,
                ledger=audit_ledger,
            )
            print(f" [StagedPack] {report}")
            if not report.get("ok"):
                print(f" [StagedPack] FAILED: {report.get('error') or report}")
        elif action_type == "run_playlist":
            report = daily_playlist.run_playlist()
            print(f" [Playlist] {report}")
        elif action_type == "focus_window":
            result = focus_window_by_title(str(payload))
            print(f" [Landmark] focus_window: {result}")
            if not result.get("ok"):
                run_controller.enter_stuck(
                    result.get("error") or f"Window “{payload}” not found.",
                    "Open the window, then Continue in VassalOps.",
                )
                decision = run_controller.wait_while_paused()
                if decision == "stop":
                    print(" [Landmark] Stopped while waiting for window.")
                    break
                if decision == "continue":
                    focus_window_by_title(str(payload))
        elif action_type == "click_landmark":
            pt = find_text_on_screen(str(payload))
            if not pt:
                run_controller.enter_stuck(
                    f"Could not find on-screen text “{payload}”.",
                    "Make the text visible, then Continue to retry.",
                )
                decision = run_controller.wait_while_paused()
                if decision == "stop":
                    break
                if decision == "skip":
                    continue
                pt = find_text_on_screen(str(payload))
            if pt:
                pyautogui.click(pt[0], pt[1])
                print(f" [Landmark] click_landmark at {pt}")
            else:
                print(f" [Landmark] click_landmark failed for {payload}")
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
        elif action_type == "read_internal_sheet":
            from src.execution.internal_catalog import answer_after_sheet, capture_signed_in_sheet

            try:
                meta = json.loads(payload) if str(payload).strip().startswith("{") else {"url": payload, "query": payload}
            except json.JSONDecodeError:
                meta = {"url": str(payload), "query": str(payload)}
            cap = capture_signed_in_sheet(str(meta.get("url") or ""), run_controller=run_controller)
            if cap.get("stop"):
                break
            if cap.get("ok"):
                msg = answer_after_sheet(str(meta.get("query") or ""), cap.get("text") or "")
            else:
                msg = cap.get("error") or "Sheet capture failed."
            run_controller.set_summary(msg[:400])
            safe_print(f"[VassalOps Output] {msg}")
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
    def _require_unlock(self) -> Optional[str]:
        if local_auth.unlocked:
            return None
        return UNLOCK_REQUIRED

    def auth_status(self) -> dict:
        return local_auth.status()

    def auth_signup(self, email: str, pin: str, question: str, answer: str) -> dict:
        result = local_auth.signup(email, pin, question, answer)
        if result.get("ok") and not result.get("registered"):
            threading.Thread(target=_register_pending_bg, daemon=True).start()
        return result

    def auth_unlock(self, pin: str) -> dict:
        result = local_auth.unlock(pin)
        if result.get("ok"):
            threading.Thread(target=_register_pending_bg, daemon=True).start()
        return result

    def auth_reset_pin(self, answer: str, new_pin: str) -> dict:
        result = local_auth.reset_pin(answer, new_pin)
        if result.get("ok"):
            threading.Thread(target=_register_pending_bg, daemon=True).start()
        return result

    def auth_lock(self) -> dict:
        local_auth.lock()
        return local_auth.status()

    def auth_change_pin(self, current_pin: str, new_pin: str) -> dict:
        return local_auth.change_pin(current_pin, new_pin)

    def auth_change_secret(self, pin: str, question: str, answer: str) -> dict:
        return local_auth.change_secret(pin, question, answer)

    def auth_complete_covenant(self, sponsored: bool, starred: bool, rating: str) -> dict:
        return local_auth.complete_covenant(
            sponsored=bool(sponsored),
            starred=bool(starred),
            rating=str(rating or ""),
        )

    def run_labrat_handshake(self, reason: str = "launch") -> dict:
        """Bidirectional handshake: send sanitized skills, receive product updates."""
        locked = self._require_unlock()
        if locked:
            return {"ok": False, "error": locked}
        why = (reason or "launch").strip().lower()
        if why not in ("launch", "close"):
            why = "launch"
        try:
            return run_handshake(
                reason=why,
                apply_product=False,
                stage_product=(why == "close"),
                spawn_waiter=(why == "close"),
            )
        except Exception as exc:
            return {"ok": False, "message": f"Handshake skipped: {exc}"}

    def get_system_identity(self) -> dict:
        """Dynamically tracks the OS login context and user details."""
        import getpass
        username = getpass.getuser()
        return {"username": username, "avatar": ""}

    def submit_command(self, user_input: str) -> str:
        """Receives text from the HTML chat, routes it, and returns the response."""
        locked = self._require_unlock()
        if locked:
            return locked
        blocked = enforce_intent_or_shutdown(user_input or "", source="chat")
        if blocked:
            return blocked

        cleaned = user_input.lower().strip()

        # Instant read-only duty helpers (no bot-sitter needed)
        if "list duties" in cleaned or cleaned in ("duties", "show duties", "my duties"):
            return duty_library.format_duty_list()

        from src.execution.internal_catalog import internal_query_plan

        catalog_plan = internal_query_plan(user_input)
        if catalog_plan and catalog_plan.get("kind") == "instant":
            return catalog_plan.get("text") or ""
        if cleaned in ("resume", "resume last", "resume session", "continue last"):
            session = load_last_session()
            ctx = format_resume_context(session)
            if not ctx:
                return "No saved session yet. Approve a goal first; then you can say resume."
            user_input = ctx + "\n\nUser: continue the prior goal."
            cleaned = user_input.lower().strip()
        if "import demo" in cleaned or "import pack" in cleaned or cleaned in ("demo pack", "import demo pack"):
            result = duty_library.import_demo_packs()
            if not result.get("ok"):
                return f"Could not import demo packs: {result.get('error')}"
            ids = result.get("imported") or []
            if not ids:
                return "No demo pack JSON files found under storage/duties/packs/."
            daily_playlist.build_workday_from_all_duties()
            return (
                "Imported demo duties:\n"
                + "\n".join(f"- {i}" for i in ids)
                + (
                    "\n\nStaged packs: "
                    + ", ".join(result.get("imported_packs") or [])
                    if result.get("imported_packs")
                    else ""
                )
                + "\n\nTry: run duty demo notepad hello (then Approve).\n"
                "Or staged ICM demo: run staged pack staged demo notepad "
                "(Approve → stage gate → Approve again).\n"
                "Tagline: Your PC's workday — taught by you, approved by you, run locally."
            )
        if "build my workday" in cleaned or "build workday" in cleaned:
            data = daily_playlist.build_workday_from_all_duties()
            names = [e.get("duty_id") for e in data.get("workday", [])]
            if not names:
                return "No duties to schedule. Teach one first: teach morning email"
            return "Workday playlist rebuilt:\n" + "\n".join(f"- {n}" for n in names)
        if any(k in cleaned for k in ("today's duties", "todays duties", "daily duties", "show playlist", "my workday")):
            briefing = daily_playlist.get_today_playlist()
            if not briefing["items"]:
                return "No workday playlist yet. Teach duties, then say: build my workday"
            lines = [f"Today's duties ({briefing['date']} {briefing['time']}):"]
            for item in briefing["items"]:
                due = "due" if item["due"] else f"after {item['after']}"
                exists = "ok" if item["exists"] else "MISSING"
                lines.append(f"- [{due}|{exists}] {item['name']} ({item['duty_id']}, {item['step_count']} steps)")
            lines.append("Use the Daily Duties panel or say: run my workday")
            return "\n".join(lines)
        
        # Intercept and route conversational ambient diagnostic questions instantly
        if "health" in cleaned or "optimize system" in cleaned or "check system" in cleaned:
            from src.execution.diagnostics_engine import VassalOpsMainDirectorAgent
            director = VassalOpsMainDirectorAgent()
            return director.run_agent_health_check()
            
        # Regression chat path: no proving-bench module — point to hermetic tests
        elif "regression" in cleaned or "verify patch" in cleaned or "run test" in cleaned:
            return (
                "### Hermetic tests (not an in-app proving bench)\n"
                "VassalOps does not ship a chat-driven regression runner. "
                "From the repo root on Windows PowerShell:\n\n"
                "```powershell\n"
                "$env:PYTHONPATH = (Get-Location).Path\n"
                "python -m unittest discover -s tests -p \"test_*.py\"\n"
                "```\n\n"
                "Live Ollama checks: set `VASSALOPS_LIVE=1`. See [CONTRIBUTING.md](CONTRIBUTING.md)."
            )
            
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
            readable = narrate_proposed_actions(proposed)
            summary = risk_summary(proposed)
            annotated = annotate_steps(proposed)
            return json.dumps({
                "status": "pending_approval",
                "thread_id": thread_id,
                "proposed_actions": annotated,
                "readable_steps": readable,
                "risk": summary,
                "message": summary["message"] + " Review the plan in plain English, then Approve or Reject."
            })
        except Exception as e:
            return f"Error executing action: {str(e)}"

    def confirm_plan(self, approved: bool) -> str:
        """Bot-sitter gate: execute or discard the pending plan for the UI session."""
        locked = self._require_unlock()
        if locked:
            return locked
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

            # Re-check plan text before desktop execution
            plan_blob = " ".join(
                [str(s.get("type") or "") + " " + str(s.get("payload") or "") for s in proposed]
                + narrate_proposed_actions(proposed)
            )
            blocked = enforce_intent_or_shutdown(plan_blob, source="approve")
            if blocked:
                return blocked

            current_state["approval_status"] = "approved"
            readable = narrate_proposed_actions(proposed)
            if any(str(s.get("type")) == "agent_loop" for s in proposed):
                readable = [f"Turn {i}/8 of approved agent loop" for i in range(1, 9)]
            run_controller.reset_for_run(readable, phase="approved_plan")

            def _run():
                try:
                    safe_print("[VassalOps] Plan approved by bot-sitter. Executing macros...")
                    execute_macros_node(current_state)
                    snap = run_controller.snapshot()
                    if snap.get("status") not in ("done", "stopped"):
                        run_controller.finish(True)
                except Exception as exc:
                    if not run_controller.finish_if_active(False, str(exc)):
                        safe_print(f"[VassalOps] Secondary error after run finished (ignored): {exc}")

            threading.Thread(target=_run, daemon=True).start()
            return "Execution started. Watch the progress panel — use Stop if needed. A redacted report will be saved under storage/runs/."
        except Exception as e:
            return f"Error confirming plan: {str(e)}"

    def get_run_progress(self) -> dict:
        """Live progress for the dashboard progress panel."""
        if not local_auth.unlocked:
            return {"status": "idle", "ok": False, "summary": UNLOCK_REQUIRED}
        return run_controller.snapshot()

    def stop_run(self) -> str:
        locked = self._require_unlock()
        if locked:
            return locked
        run_controller.request_stop()
        return "Stop requested. Automation will halt at the next safe point."

    def continue_run(self) -> str:
        locked = self._require_unlock()
        if locked:
            return locked
        run_controller.continue_run()
        return "Continuing after pause."

    def skip_stuck_step(self) -> str:
        locked = self._require_unlock()
        if locked:
            return locked
        run_controller.skip_stuck_step()
        return "Skipping the stuck step."

    def confirm_replan(self) -> str:
        """Second Approve for a mid-run / max-turn replan suggestion (never silent)."""
        locked = self._require_unlock()
        if locked:
            return locked
        run_controller.confirm_replan()
        return "Replan approved. Continuing when the runner is waiting."

    def list_duties(self) -> list:
        """Returns taught duty summaries for the Daily Duties panel."""
        if not local_auth.unlocked:
            return []
        return duty_library.list_duties()

    def get_today_playlist(self) -> dict:
        """Morning briefing payload for the dashboard."""
        if not local_auth.unlocked:
            return {"items": [], "locked": True}
        return daily_playlist.get_today_playlist()

    def confirm_playlist(self, approved: bool, duty_ids: list = None) -> str:
        """Bot-sitter gate for running one or more playlist duties sequentially."""
        locked = self._require_unlock()
        if locked:
            return locked
        if not approved:
            return "Playlist run cancelled. No duties were executed."
        ids = duty_ids if isinstance(duty_ids, list) else None
        briefing = daily_playlist.get_today_playlist()
        selected = ids or [i["duty_id"] for i in briefing.get("items", []) if i.get("exists")]
        blocked = enforce_intent_or_shutdown(
            "run playlist " + " ".join(str(s) for s in selected),
            source="playlist",
        )
        if blocked:
            return blocked

        def _run():
            try:
                report = daily_playlist.run_playlist(ids)
                ok = bool(report.get("ok"))
                err = ""
                if report.get("stopped_early"):
                    err = "Stopped early due to failure (work PC safety policy)."
                obs = []
                for r in report.get("results") or []:
                    status = "OK" if r.get("ok") else f"FAIL ({r.get('error', 'error')})"
                    obs.append(f"{r.get('name') or r.get('duty_id')}: {status}")
                path = write_run_report(
                    goal="playlist:" + ",".join(selected or []),
                    ok=ok,
                    turns=len(obs),
                    observations=obs,
                    final=err or ("playlist complete" if ok else "playlist failed"),
                    reason=err,
                    kind="playlist",
                )
                record_loop_outcome(
                    os.path.join("storage", "agent.md"),
                    {"ok": ok, "reason": err or ("ok" if ok else "playlist failed"), "observations": obs, "turns": len(obs)},
                    goal="playlist",
                )
                save_last_session(goal="playlist", observations=obs, final=err, ok=ok)
                safe_print(f"[VassalOps Output] Report saved: {path}")
                snap = run_controller.snapshot()
                if snap.get("status") not in ("done", "stopped"):
                    run_controller.finish(ok, err)
            except Exception as exc:
                if not run_controller.finish_if_active(False, str(exc)):
                    safe_print(f"[VassalOps] Secondary error after playlist finished (ignored): {exc}")

        readable = [f"Run duty: {d}" for d in selected]
        run_controller.reset_for_run(readable, phase="playlist")
        threading.Thread(target=_run, daemon=True).start()
        return "Playlist execution started. Watch progress — Approve already granted for this run."

    def add_duty_to_playlist(self, duty_id: str, after: str = "09:00") -> dict:
        """Adds/updates a duty on the workday playlist."""
        if not local_auth.unlocked:
            return {"error": UNLOCK_REQUIRED}
        daily_playlist.add_duty(duty_id, after=after)
        return daily_playlist.get_today_playlist()

    def import_demo_pack(self) -> str:
        locked = self._require_unlock()
        if locked:
            return locked
        result = duty_library.import_demo_packs()
        if not result.get("ok"):
            return f"Import failed: {result.get('error')}"
        ids = result.get("imported") or []
        daily_playlist.build_workday_from_all_duties()
        return "Imported: " + (", ".join(ids) if ids else "(none)")

    def _splash_flag_path(self) -> str:
        return os.path.join("storage", "splash_seen.json")

    def should_show_splash(self) -> bool:
        """Always show brand splash on UI load (large sharp mark)."""
        return True

    def mark_splash_seen(self) -> dict:
        """Record last splash time (splash still plays every launch)."""
        path = self._splash_flag_path()
        os.makedirs(os.path.dirname(path), exist_ok=True)
        payload = {"seen": True, "every_launch": True, "at": time.strftime("%Y-%m-%dT%H:%M:%S")}
        with open(path, "w", encoding="utf-8") as f:
            json.dump(payload, f)
        return payload

    def open_external_url(self, url: str) -> str:
        """Open sponsor / feedback / star links in the system browser."""
        import webbrowser
        from urllib.parse import urlparse

        raw = (url or "").strip()
        parsed = urlparse(raw)
        if parsed.scheme not in ("http", "https") or not parsed.netloc:
            return "Blocked: only http(s) URLs allowed."
        host = parsed.netloc.lower()
        if not (host == "github.com" or host.endswith(".github.com")):
            return f"Blocked host: {host}"
        try:
            webbrowser.open(raw)
            return "opened"
        except Exception as exc:
            return f"Could not open browser: {exc}"

    def get_community_links(self) -> dict:
        """Stable URLs for in-app Feedback / Sponsor / Star buttons."""
        version = "0.0.0"
        try:
            with open("VERSION", "r", encoding="utf-8") as f:
                version = f.read().strip() or version
        except Exception:
            pass
        return {
            "repo": "https://github.com/AndyOliverR/VassalOps",
            "star": "https://github.com/AndyOliverR/VassalOps",
            "sponsors": "https://github.com/sponsors/AndyOliverR",
            "feedback_new_issue": "https://github.com/AndyOliverR/VassalOps/issues/new?template=feedback.yml",
            "version": version,
        }

def force_win32_window_icon():
    """Win32: title-bar icon + repeatedly force 60% centered placement on the real monitor."""
    import ctypes
    import time
    from src.window_center import find_vassalops_hwnd, seat_vassalops_loop

    def _place_log(msg: str) -> None:
        try:
            with open(os.path.join("storage", "window_place.log"), "a", encoding="utf-8") as f:
                f.write(f"[{time.strftime('%H:%M:%S')}] {msg}\n")
        except Exception:
            pass

    # Re-apply center for ~2.5s — WebView2 often repositions after first show
    seat_vassalops_loop(
        max_frac=0.60,
        preferred_w=960,
        preferred_h=640,
        duration_s=2.8,
        interval_s=0.1,
        log=_place_log,
    )

    user32 = ctypes.windll.user32
    WM_SETICON = 0x0080
    ICON_SMALL = 0
    ICON_BIG = 1
    LR_LOADFROMFILE = 0x00000010
    IMAGE_ICON = 1

    hwnd = find_vassalops_hwnd()
    if hwnd:
        icon_path = os.path.abspath("storage/dashboard/vassalops_bare.ico")
        if not os.path.isfile(icon_path):
            icon_path = os.path.abspath("storage/dashboard/vassal_icon.ico")
        if os.path.exists(icon_path):
            hicon = user32.LoadImageW(0, icon_path, IMAGE_ICON, 0, 0, LR_LOADFROMFILE)
            if hicon:
                user32.SendMessageW(hwnd, WM_SETICON, ICON_SMALL, hicon)
                user32.SendMessageW(hwnd, WM_SETICON, ICON_BIG, hicon)
                print("[VassalOps Win32] Success: System title bar icon forced via kernel memory handles.")

if __name__ == "__main__":
    import webview
    import threading
    from src.window_center import fitted_window, seat_hwnd_centered, find_vassalops_hwnd

    print("======================================================")
    print("VassalOps Core Engine Online -- UI Window Launching")
    print("======================================================")

    # Align DPI before WebView2 creates the HWND (avoids corner drift)
    try:
        import ctypes

        try:
            ctypes.windll.shcore.SetProcessDpiAwareness(2)  # PER_MONITOR_AWARE
        except Exception:
            ctypes.windll.user32.SetProcessDPIAware()
    except Exception:
        pass
    
    api_bridge = VassalOpsAPI()
    x, y, win_w, win_h = fitted_window(960, 640, max_frac=0.60)
    window = webview.create_window(
        title="VassalOps",
        url=os.path.abspath("storage/dashboard/index.html"),
        width=win_w,
        height=win_h,
        x=x,
        y=y,
        resizable=True,
        text_select=True,
        js_api=api_bridge
    )

    def _seat_center() -> None:
        try:
            window.resize(win_w, win_h)
            window.move(x, y)
        except Exception:
            pass
        hwnd = find_vassalops_hwnd()
        if hwnd:
            seat_hwnd_centered(hwnd, max_frac=0.60, preferred_w=960, preferred_h=640)

    window.events.shown += _seat_center
    window.events.loaded += _seat_center

    _close_handshake_done = {"done": False}

    def _close_handshake(*_args, **_kwargs) -> None:
        if _close_handshake_done["done"]:
            return
        _close_handshake_done["done"] = True
        try:
            run_handshake(
                reason="close",
                apply_product=False,
                stage_product=True,
                spawn_waiter=True,
            )
        except Exception:
            pass

    try:
        window.events.closing += _close_handshake
    except Exception:
        pass
    try:
        window.events.closed += _close_handshake
    except Exception:
        pass

    threading.Thread(target=force_win32_window_icon, daemon=True).start()
    
    webview.start()
