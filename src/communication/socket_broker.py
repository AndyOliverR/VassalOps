import sys
import os
import asyncio
import json

# Dynamically ensure top-level project module access
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../")))

try:
    import websockets
except ImportError:
    raise ImportError("Dependency missing. Please run: pip install websockets")

# Import the core LangGraph state engine, the execute node, and our audit tracker
from app import vassalops_engine, execute_macros_node
from src.execution.audit_ledger import VassalOpsAuditLedger
from src.execution.background_scheduler import VassalOpsBackgroundDaemon


def _load_broker_runtime_config():
    """Reads localhost bind settings and shared auth token from config.json."""
    defaults = {
        "broker_bind_host": "127.0.0.1",
        "broker_port": 8765,
        "broker_auth_token": "",
    }
    config_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../config.json"))
    try:
        with open(config_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        boundaries = data.get("runtime_boundaries", {})
        return {
            "broker_bind_host": boundaries.get("broker_bind_host", defaults["broker_bind_host"]),
            "broker_port": int(boundaries.get("broker_port", defaults["broker_port"])),
            "broker_auth_token": boundaries.get("broker_auth_token", defaults["broker_auth_token"]),
        }
    except Exception as e:
        print(f"[VassalOps Broker] Warning: failed to load config.json ({e}); using localhost defaults.")
        return defaults


class GMANetworkBroker:
    def __init__(self, host: str = None, port: int = None, auth_token: str = None):
        runtime = _load_broker_runtime_config()
        self.host = host if host is not None else runtime["broker_bind_host"]
        self.port = port if port is not None else runtime["broker_port"]
        self.auth_token = auth_token if auth_token is not None else runtime["broker_auth_token"]
        self.ledger = VassalOpsAuditLedger()
        self.daemon_guard = VassalOpsBackgroundDaemon(check_interval_sec=10.0)
        print(f"[VassalOps Broker] Initialized Remote Macro Execution Broker on {self.host}:{self.port}")

    def verify_broker_token(self, payload: dict) -> dict:
        """Rejects payloads that omit or mismatch the shared broker auth token."""
        expected = (self.auth_token or "").strip()
        if not expected:
            return {
                "status": "ERROR",
                "msg": "Broker auth token is not configured in config.json runtime_boundaries.broker_auth_token",
            }
        provided = payload.get("token", "")
        if provided != expected:
            return {"status": "ERROR", "msg": "Unauthorized: missing or invalid broker token"}
        return {"status": "OK"}

    async def handle_stream(self, websocket):
        """Intercepts telemetry, extracts channel partition IDs, and runs workflows with physical macro injection."""
        remote_address = websocket.remote_address
        print(f"\n[VassalOps Broker] Active network connection hook: {remote_address}")

        try:
            async for message in websocket:
                try:
                    payload = json.loads(message)
                    auth_result = self.verify_broker_token(payload)
                    if auth_result["status"] != "OK":
                        await websocket.send(json.dumps(auth_result))
                        continue

                    device_source = payload.get("device", "Remote Display")
                    remote_intent = payload.get("command", "").strip()
                    channel_id = payload.get("channel", f"channel_{device_source.replace(' ', '_').lower()}")

                    print(f"\n[VassalOps Network Task] Received via Channel '{channel_id}' [{device_source}]: '{remote_intent}'")

                    if remote_intent:
                        print(f"[VassalOps Broker] Initializing state graph pipeline loop...")
                        thread_config = {"configurable": {"thread_id": f"session_{channel_id}"}}
                        initial_state = {
                            "raw_user_input": remote_intent,
                            "captured_context": "",
                            "extracted_entities": {},
                            "normalized_intent": {},
                            "proposed_actions": [],
                            "approval_status": "pending",
                        }

                        for event in vassalops_engine.stream(initial_state, thread_config):
                            pass

                        current_state = dict(vassalops_engine.get_state(thread_config).values)

                        print(f"\n=========== WIRELESS CONFIRMATION: CHANNEL [{channel_id.upper()}] ===========")
                        print(f"Origin Device: {device_source}")
                        print(f"Captured Text Context: '{current_state.get('captured_context', '')}'")
                        print("\nGenerated Remote Automation Steps Blueprint:")
                        for idx, step in enumerate(current_state.get('proposed_actions', []), 1):
                            print(f" [{idx}] Action Mode: {step['type']} -> Context: {step['payload']}")
                        print("====================================================================")

                        response = {
                            "id": "NEW",
                            "device": device_source,
                            "channel": channel_id,
                            "command": remote_intent,
                            "status": "AWAITING_HUMAN_CONFIRMATION"
                        }
                        await websocket.send(json.dumps(response))

                        user_approval = input("\n[Bot-Sitter Authorization] Approve this wireless remote plan? (y/n): ")
                        if user_approval.lower() == 'y':
                            current_state["approval_status"] = "approved"
                            print("\n[VassalOps Broker] Wireless approval signed. Injecting hardware execution chain...")

                            # Phase 19 Fix: Explicitly fire macro execution module to trigger mouse/keyboard commands locally
                            execute_macros_node(current_state)

                            self.ledger.commit_transaction(intent=remote_intent, status="success_completed", device=device_source, channel=channel_id)
                            print(f"[VassalOps Broker] Task successfully executed on channel: {channel_id}")
                        else:
                            self.ledger.commit_transaction(intent=remote_intent, status="rejected_by_user", device=device_source, channel=channel_id)
                            print(f"[VassalOps Broker] Task rejected on channel: {channel_id}")

                except json.JSONDecodeError:
                    await websocket.send(json.dumps({"status": "ERROR", "msg": "Invalid JSON structural format"}))

        except websockets.exceptions.ConnectionClosed:
            print(f"[VassalOps Broker] Closed network connection loop for: {remote_address}")

    async def main_loop(self):
        async with websockets.serve(self.handle_stream, self.host, self.port):
            print("[VassalOps Broker] Multi-Tenant Gateway Online. Ready...")
            self.daemon_guard.start()
            await asyncio.Future()

    def start_server(self):
        try:
            asyncio.run(self.main_loop())
        except KeyboardInterrupt:
            print("\n[VassalOps Broker] Shutting down network listeners cleanly.")
            self.daemon_guard.stop()

if __name__ == "__main__":
    broker = GMANetworkBroker()
    broker.start_server()
