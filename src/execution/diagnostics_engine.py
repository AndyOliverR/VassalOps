import sys
import os
import time

# Dynamically ensure top-level project module access
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../")))

from src.execution.audit_ledger import VassalOpsAuditLedger


def ensure_agent_memory_file(memory_path: str) -> None:
    """Creates a minimal agent.md preference schema if the file is missing."""
    directory = os.path.dirname(memory_path)
    if directory and not os.path.exists(directory):
        os.makedirs(directory, exist_ok=True)
    if os.path.exists(memory_path):
        return
    with open(memory_path, "w", encoding="utf-8") as f:
        f.write("# VassalOps Agent Long-Term Preferences\n\n")
        f.write("IGNORE_ANOMALIES_UNDER_SEVERITY: Low\n\n")
        f.write("## Skill Properties\n")
        f.write("- AUTO_LATENCY_DELAY_PADDING: Disabled\n")


class VassalOpsScreenerSubAgent:
    """Screener Sub-Agent: Low-cost rapid parser that flags explicit anomalies across logs."""
    def analyze_full_trace(self, thread_id: str, raw_data: str) -> dict:
        has_clipping = "clipping" in raw_data.lower() or "warning" in raw_data.lower()
        has_crash = "error" in raw_data.lower() or "exception" in raw_data.lower() or "fail" in raw_data.lower()
        
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
        ensure_agent_memory_file(self.memory_path)
        if os.path.exists(self.memory_path):
            with open(self.memory_path, "r", encoding="utf-8") as f:
                memory_text = f.read()
            if "IGNORE_ANOMALIES_UNDER_SEVERITY: Low" in memory_text and screening_report["severity"] == "low":
                return False
        return screening_report["anomaly_detected"]


class VassalOpsMainDirectorAgent:
    """Main Director Agent: Core orchestrator managing broad analytical insight, actionability, and memory rewrite loops."""
    def __init__(self, memory_path: str = "storage/agent.md", ledger: VassalOpsAuditLedger = None):
        self.memory_path = memory_path
        self.ledger = ledger or VassalOpsAuditLedger()
        self.screener = VassalOpsScreenerSubAgent()
        self.verifier = VassalOpsVerifierSubAgent(memory_path)
        ensure_agent_memory_file(self.memory_path)

    def _load_trace_logs(self, limit: int = 20) -> list:
        """Builds screenable log strings from real audit ledger rows."""
        rows = self.ledger.fetch_recent_intents(limit=limit)
        traces = []
        for row in rows:
            log = f"[{row.get('execution_status', 'UNKNOWN')}] channel={row.get('channel_id')} intent={row.get('command_intent')}"
            traces.append({
                "id": f"audit_{row.get('id')}",
                "log": log,
            })
        return traces

    def execute_sleeptime_compute(self) -> str:
        """Sleep-time compute: analyzes audit ledger trends and rewrites agent.md preferences."""
        print("[VassalOps Engine] Activating Sleep-Time Compute Memory Loop...")
        ensure_agent_memory_file(self.memory_path)
        time.sleep(0.4)

        traces = self._load_trace_logs(limit=20)
        if not traces:
            return "Sleep-time trace analysis pass completed. No audit ledger rows available yet."

        new_discoveries = 0
        for trace in traces:
            report = self.screener.analyze_full_trace(trace["id"], trace["log"])
            if report["anomaly_detected"] and self.verifier.verify_issue(report):
                if report["severity"] in ("medium", "high"):
                    new_discoveries += 1

        if new_discoveries > 0:
            try:
                with open(self.memory_path, "a", encoding="utf-8") as f:
                    f.write(f"\n\n## Autonomously Learned Skill Properties ({time.strftime('%Y-%m-%d')})\n")
                    f.write("- AUTO_LATENCY_DELAY_PADDING: Enabled due to anomaly trends detected in audit ledger during sleeptime compute.\n")
                    f.write(f"- AUDIT_ANOMALIES_REVIEWED: {new_discoveries}\n")
                return "Memory Optimization Successful: Dynamic skill padding appended to your agent.md file configuration."
            except Exception as e:
                return f"Memory Loop Bottleneck: {str(e)}"
        return "Sleep-time trace analysis pass completed. No memory modifications required."

    def run_agent_health_check(self) -> str:
        """Runs a full audit-ledger scan and compiles an actionable report."""
        traces = self._load_trace_logs(limit=20)
        total_analyzed = len(traces)
        verified_issues = []

        for trace in traces:
            report = self.screener.analyze_full_trace(trace["id"], trace["log"])
            if report["anomaly_detected"] and self.verifier.verify_issue(report):
                verified_issues.append(report)

        output = "### VassalOps Core Health & Optimization Report\n"
        output += f"- **Traces Screened:** {total_analyzed} audit ledger rows parsed.\n"
        output += f"- **Actionable Issues Located:** {len(verified_issues)} active anomalies clustered.\n\n"

        if total_analyzed == 0:
            output += "No audit ledger history yet. Run a few automation tasks, then re-check health.\n"
        elif verified_issues:
            output += "#### Active Issue Inbox Queue:\n"
            for issue in verified_issues:
                output += f"1. **[{issue['severity'].upper()}] {issue['type']}** detected on session `{issue['thread_id']}`. *Proposed Shadow Fix:* Review recent automation intents in the audit ledger.\n"
        else:
            output += "**System Health Pristine:** All background operation matrices are within nominal parameters.\n"

        return output


if __name__ == "__main__":
    director = VassalOpsMainDirectorAgent()
    print(director.run_agent_health_check())
    print(director.execute_sleeptime_compute())
