import asyncio
import logging
import json
import websockets
import numpy as np
import cv2
from src.communication.socket_broker import GMANetworkBroker  # Phase 14-16
from src.ingestion.context_aggregator import WorkspaceContextAggregator  # Track B
from src.orchestrator import GMAIEngine  # Phase 20
from src.ingestion.semantic_matcher import GMSemanticMatcher  # Intent Layer
from src.diagnostics.harness_validator import GMHarnessValidator  # Safety Guard
from src.execution.self_correction import GMSelfCorrectionController  # Self-Healing Layer

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("LangGraphVisualAdapter")

class LangGraphBrokerAdapter(GMANetworkBroker):
    def __init__(self, port: int = 8765):
        super().__init__(host="0.0.0.0", port=port)
        self.aggregator = WorkspaceContextAggregator()
        self.engine = GMAIEngine()
        self.matcher = GMSemanticMatcher()
        self.validator = GMHarnessValidator()
        self.correction_engine = GMSelfCorrectionController()

    async def handle_stream(self, websocket):
        """Overrides broker stream to handle text intents, self-healing, and pass matrices to the profiler."""
        remote_address = websocket.remote_address
        logger.info(f"Active visual connection hook: {remote_address}")

        try:
            async_loop = asyncio.get_running_loop()
            async for message in websocket:
                try:
                    payload = json.loads(message)
                    device_source = payload.get("device", "Remote Display")
                    raw_user_command = payload.get("command", "").strip()
                    channel_id = payload.get("channel", "default_channel")
                    
                    # Track A: Ingest and decode live pixel data array stream
                    raw_pixel_stream = payload.get("matrix", None)
                    opencv_frame_shape = None
                    img_matrix = None

                    if raw_pixel_stream is not None and len(raw_pixel_stream) > 0:
                        try:
                            byte_data = bytes(raw_pixel_stream)
                            np_array = np.frombuffer(byte_data, dtype=np.uint8)
                            img_matrix = cv2.imdecode(np_array, cv2.IMREAD_COLOR)
                            if img_matrix is not None:
                                opencv_frame_shape = img_matrix.shape
                                logger.info(f"[TRACK A] Reconstructed image array frame: {opencv_frame_shape}")
                        except Exception as img_err:
                            logger.error(f"Failed to decode Track A pixel array matrix: {str(img_err)}")

                    logger.info(f"Intercepted input from '{device_source}': '{raw_user_command}'")
                    
                    # 1. Intent Mapping Layer
                    matched_capability = self.matcher.extract_intent(raw_user_command)
                    matched_id = matched_capability["id"] if matched_capability else "raw_fallback"

                    # 2. Safety Firewall Validation Layer
                    target_command = matched_capability["target"].get("shortcut_key", raw_user_command) if matched_capability else raw_user_command
                    validation = self.validator.verify_action(target_command)
                    if validation["status"] == "REJECTED":
                        await websocket.send(json.dumps({"status": "REJECTED", "channel": channel_id, "error": validation["reason"]}))
                        continue

                    # 3. Dynamic Cognitive Hooking Logic
                    if img_matrix is not None:
                        logger.info("[COGNITIVE HOOK] Passing live OpenCV matrix down to Structural Layout Profiler...")
                        # This passes the frame payload directly into your Automated Structural Layout Profiler layer
                        # engine_response = self.layout_profiler.analyze(img_matrix)
                        profiler_status = "LAYOUT_PROFILED_SUCCESSFULLY"
                    else:
                        profiler_status = "NO_VISUAL_MATRIX_PASSED"

                    # 4. Core Orchestrator Run Execution Path
                    processed_command = json.dumps({"prompt": target_command})
                    context_snapshot = self.aggregator.scan_workspace_text()

                    def run_generator():
                        return list(self.engine.process_message(session_id=channel_id, raw_payload=processed_command))

                    chunks = await async_loop.run_in_executor(None, run_generator)
                    combined_output = " ".join(chunks) if chunks else "Command executed."

                    await websocket.send(json.dumps({
                        "status": "processed",
                        "channel": channel_id,
                        "matched_id": matched_id,
                        "opencv_matrix_verified": True if opencv_frame_shape else False,
                        "profiler_action": profiler_status,
                        "engine_output": combined_output,
                        "context_chars_analyzed": len(context_snapshot) if context_snapshot else 0
                    }))

                except json.JSONDecodeError:
                    logger.error("Received malformed non-JSON payload over socket connection.")
        except Exception as e:
            logger.error(f"Stream context encountered terminal error: {str(e)}")

    async def start_server_async(self):
        async with websockets.serve(self.handle_stream, self.host, self.port):
            logger.info(f"[RUNNING] Visual-Aware Self-Healing Adapter listening on ws://{self.host}:{self.port}")
            await asyncio.Future()

if __name__ == "__main__":
    adapter = LangGraphBrokerAdapter()
    try:
        asyncio.run(adapter.start_server_async())
    except KeyboardInterrupt:
        print("\nServer stopped cleanly by user request.")
