import sys
import os
import json

# Dynamically ensure top-level project module access
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../")))

from src.execution.backup_manager import VassalOpsBackupManager
from src.execution.data_sorter import VassalOpsDataSorter


class VassalOpsToolRouter:
    """In-process tool dispatcher for backup/sort utilities (not MCP process isolation)."""

    def __init__(self):
        self.backup_mgr = VassalOpsBackupManager()
        self.data_sorter = VassalOpsDataSorter()
        print("[VassalOps ToolRouter] Local tool dispatcher initialized.")

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
        """Dispatches a named tool to the matching local handler."""
        print(f"[VassalOps ToolRouter] Call Request Received -> Tool: {tool_name}")
        try:
            if tool_name == "run_backup":
                self.backup_mgr.execute_directory_backup()
                return {"status": "success", "message": "Directory backup sequence executed via ToolRouter."}
            elif tool_name == "sort_intel":
                self.data_sorter.run_sort_and_optimize()
                return {"status": "success", "message": "Data optimization stream completed via ToolRouter."}
            else:
                return {"status": "error", "message": f"Unknown tool footprint: {tool_name}"}
        except Exception as e:
            return {"status": "error", "message": f"Tool execution failure: {str(e)}"}


if __name__ == "__main__":
    router = VassalOpsToolRouter()
    print(json.dumps(router.list_tools(), indent=2))
