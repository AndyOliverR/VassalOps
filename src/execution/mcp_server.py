import sys
import os
import json

# Dynamically ensure top-level project module access
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../")))

from src.execution.backup_manager import VassalOpsBackupManager
from src.execution.data_sorter import VassalOpsDataSorter

class VassalOpsMCPServer:
    def __init__(self):
        self.backup_mgr = VassalOpsBackupManager()
        self.data_sorter = VassalOpsDataSorter()
        print("[VassalOps MCP] Universal Context Server initialized.")

    def list_tools(self) -> dict:
        """Exposes runtime discoverability schemas so the agent knows what tools exist."""
        return {
            "tools": [
                {
                    "name": "run_backup",
                    "description": "Executes a secure local storage directory backup sequence.",
                    "input_schema": {"type": "object", "properties": {}}
                },
                {
                    "name": "sort_intel",
                    "description": "Triggers algorithmic sorting and optimization pipelines.",
                    "input_schema": {"type": "object", "properties": {}}
                }
            ]
        }

    def call_tool(self, tool_name: str, arguments: dict = None) -> dict:
        """Safely executes a disconnected external process tool over standard JSON tokens."""
        print(f"[VassalOps MCP] Call Request Received -> Tool: {tool_name}")
        try:
            if tool_name == "run_backup":
                self.backup_mgr.execute_directory_backup()
                return {"status": "success", "message": "Directory backup sequence executed safely via MCP."}
            elif tool_name == "sort_intel":
                self.data_sorter.run_sort_and_optimize()
                return {"status": "success", "message": "Data optimization stream completed via MCP."}
            else:
                return {"status": "error", "message": f"Unknown tool footprint: {tool_name}"}
        except Exception as e:
            return {"status": "error", "message": f"Tool execution failure: {str(e)}"}

if __name__ == "__main__":
    # Standard terminal interaction loop for testing raw input/output handshakes
    server = VassalOpsMCPServer()
    print(json.dumps(server.list_tools(), indent=2))
