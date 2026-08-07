import unittest
from unittest.mock import MagicMock, patch
from src.execution.tool_router import VassalOpsToolRouter


class TestToolRouter(unittest.TestCase):
    def test_list_tools_contains_backup_and_sort(self):
        with patch("src.execution.tool_router.VassalOpsBackupManager"), \
             patch("src.execution.tool_router.VassalOpsDataSorter"):
            router = VassalOpsToolRouter()
            tools = router.list_tools()["tools"]
            names = {t["name"] for t in tools}
            self.assertIn("run_backup", names)
            self.assertIn("sort_intel", names)

    def test_unknown_tool_returns_error(self):
        with patch("src.execution.tool_router.VassalOpsBackupManager"), \
             patch("src.execution.tool_router.VassalOpsDataSorter"):
            router = VassalOpsToolRouter()
            result = router.call_tool("does_not_exist")
            self.assertEqual(result["status"], "error")

    def test_run_backup_dispatches(self):
        with patch("src.execution.tool_router.VassalOpsBackupManager") as Backup, \
             patch("src.execution.tool_router.VassalOpsDataSorter"):
            backup_instance = MagicMock()
            Backup.return_value = backup_instance
            router = VassalOpsToolRouter()
            result = router.call_tool("run_backup")
            self.assertEqual(result["status"], "success")
            backup_instance.execute_directory_backup.assert_called_once()


if __name__ == "__main__":
    unittest.main()
