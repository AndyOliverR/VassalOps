import os
import sys
import platform
import shutil

class GMTelemetrySensor:
    def get_system_diagnostics(self) -> dict:
        """Gather real-time performance telemetry matrix profiles from the host PC."""
        try:
            total, used, free = shutil.disk_usage("C:\\")
            return {
                "os_platform": platform.system(),
                "os_release": platform.release(),
                "python_version": sys.version.split()[0],
                "disk_total_gb": round(total / (1024**3), 2),
                "disk_free_gb": round(free / (1024**3), 2),
                "workspace_directory": os.path.abspath(os.getcwd())
            }
        except Exception as e:
            return {"error": f"Telemetry sampling structural failure: {str(e)}"}
            
    def format_telemetry_report(self) -> str:
        """Convert system stats into a clean text block for the engine context."""
        diag = self.get_system_diagnostics()
        if "error" in diag:
            return diag["error"]
            
        return (
            f"[SYSTEM TELEMETRY DATA]\n"
            f"- OS Platform: {diag['os_platform']} (v{diag['os_release']})\n"
            f"- Python Runtime Version: {diag['python_version']}\n"
            f"- Disk Allocation (C:): {diag['disk_free_gb']} GB Free / {diag['disk_total_gb']} GB Total\n"
            f"- Core Path: {diag['workspace_directory']}"
        )

