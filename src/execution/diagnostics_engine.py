import sys
import os
import json
import time

# Dynamically ensure top-level project module access
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../")))

class VassalOpsScreenerSubAgent:
    """Screener Sub-Agent: Low-cost rapid parser that flags explicit anomalies across logs."""
    def analyze_full_trace(self, thread_id: str, raw_data: str) -> dict:
        has_clipping = "clipping" in raw_data.lower() or "warning" in raw_data.lower()
        has_crash = "error" in raw_data.lower() or "exception" in raw_data.lower()
        
        severity = "low"
        if has_crash: severity = "high"
        elif has_clipping: severity = "medium"
        
        return {
            "thread_id": thread_id,
            "anomaly_detected": (has_clipping or has_crash),
            "type": "Runtime Process Crash" if has_crash else "Hardware Bounding Drift" if has_clipping else "None",
            "severity": severity,
            "raw_snippet": raw_data[:120]
        }

class VassalOpsVerifierSubAgent:
    """Verifier Sub-Agent: References agent.md workspace files to drop noise."""
    def __init__(self, memory_path: str = "storage/agent.md"):
        self.memory_path = memory_path

    def verify_issue(self, screening_report: dict) -> bool:
        if os.path.exists(self.memory_path):
            with open(self.memory_path, "r", encoding="utf-8") as f:
                memory_text = f.read()
            if "IGNORE_ANOMALIES_UNDER_SEVERITY: Low" in memory_text and screening_report["severity"] == "low":
                return False
        return screening_report["anomaly_detected"]

class VassalOpsMainDirectorAgent:
    """Main Director Agent: Core orchestrator managing broad analytical insight, actionability, and memory rewrite loops."""
    def __init__(self, memory_path: str = "storage/agent.md"):
        self.memory_path = memory_path
        self.screener = VassalOpsScreenerSubAgent()
        self.verifier = VassalOpsVerifierSubAgent(memory_path)

    def execute_sleeptime_compute(self) -> str:
        """Sleeptime Compute Pattern: Analyzes execution trends and rewrites agent.md long-term memory profiles."""
        print("[VassalOps Engine] Activating Sleep-Time Compute Memory Loop...")
        time.sleep(0.4)
        
        # Meta-Tracing: Scan the log system history state
        mock_history = [
            "WARNING: Point (1950, 1200) outside display boundaries. Clipping bounds applied.",
            "CRITICAL ERROR: TypeError inside window instantiation."
        ]
        
        new_discoveries = 0
        for log in mock_history:
            if "clipping" in log.lower():
                new_discoveries += 1

        if new_discoveries > 0 and os.path.exists(self.memory_path):
            try:
                # Autonomously optimize the agent overview memory file based on the trace history analysis
                with open(self.memory_path, "a", encoding="utf-8") as f:
                    f.write(f"\n\n## Autonomously Learned Skill Properties ({time.strftime('%Y-%m-%d')})\n")
                    f.write("- AUTO_LATENCY_DELAY_PADDING: Enabled due to coordinate bounding drift trends detected during sleeptime compute.\n")
                return "Memory Optimization Successful: Dynamic skill padding appended to your agent.md file configuration."
            except Exception as e:
                return f"Memory Loop Bottleneck: {str(e)}"
        return "Sleep-time trace analysis pass completed. No memory modifications required."

    def run_agent_health_check(self) -> str:
        """Combines the best of Insights and Poly: Runs a full trace scan and compiles an actionable report."""
        mock_traces = [
            {"id": "trace_01", "log": "SUCCESS: Macro step executed flawlessly inside pyautogui bounds."},
            {"id": "trace_02", "log": "WARNING: Point (1950, 1200) outside display boundaries. Clipping bounds applied."},
            {"id": "trace_03", "log": "CRITICAL ERROR: TypeError create_window() got an unexpected keyword argument 'icon'."}
        ]
        
        total_analyzed = len(mock_traces)
        verified_issues = []
        
        for trace in mock_traces:
            report = self.screener.analyze_full_trace(trace["id"], trace["log"])
            if report["anomaly_detected"] and self.verifier.verify_issue(report):
                verified_issues.append(report)
                
        output = f"### VassalOps Core Health & Optimization Report\n"
        output += f"- **Traces Screened:** {total_analyzed} execution logs parsed cleanly.\n"
        output += f"- **Actionable Issues Located:** {len(verified_issues)} active anomalies clustered.\n\n"
        
        if verified_issues:
            output += "#### Active Issue Inbox Queue:\n"
            for issue in verified_issues:
                output += f"1. **[{issue['severity'].upper()}] {issue['type']}** detected on session `{issue['thread_id']}`. *Proposed Shadow Fix:* Run autonomous latency calibration.\n"
        else:
            output += "✅ **System Health Pristine:** All background operation matrices are within nominal parameters.\n"
            
        return output

if __name__ == "__main__":
    director = VassalOpsMainDirectorAgent()
    print(director.run_agent_health_check())
    print(director.execute_sleeptime_compute())
