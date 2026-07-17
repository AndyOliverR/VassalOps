import os
import sys
import json
import random

class VassalOpsIssueBench:
    """IssueBench Generator: Compiles synthetic failure test environments for offline benchmark evals [0:1.191, 0:1.197]."""
    def __init__(self, task_file: str = "storage/issue_bench_tasks.json"):
        self.task_file = task_file
        os.makedirs("storage", exist_ok=True)
        print("[VassalOps Bench] Synthetic IssueBench Harness online [0:1.191].")

    def generate_synthetic_benchmark_suite(self):
        """Generates mock macro failure cases to stress-test regression boundaries safely [0:1.194, 0:1.197]."""
        print(" [IssueBench] Generating synthetic mutation sets across macro profiles...")
        
        # Base templates derived from real-world trace metadata rules [0:1.480]
        synthetic_suite = {
            "benchmark_version": "2026.2.1",
            "tasks": [
                {
                    "task_id": "synthetic_drift_01",
                    "category": "Coordinate Alignment Drift",
                    "raw_trace_log": "WARNING: Click targeted at (2560, 1440) falls outside monitor resolution grid.",
                    "mutation_injected": "Out of bounds screen boundary clipping drift [0:1.197]."
                },
                {
                    "task_id": "synthetic_lag_02",
                    "category": "Process Latency Breach",
                    "raw_trace_log": "CRITICAL: Execution delay exceeded 45.0 seconds waiting for system window focus.",
                    "mutation_injected": "Artificial delay padding breach [0:1.197]."
                }
            ]
        }
        
        with open(self.task_file, "w", encoding="utf-8") as f:
            json.dump(synthetic_suite, f, indent=2)
        print(f" [IssueBench] Success: Written {len(synthetic_suite['tasks'])} synthetic profiles to {self.task_file} [0:1.191].")
        return len(synthetic_suite['tasks'])

if __name__ == "__main__":
    bench = VassalOpsIssueBench()
    bench.generate_synthetic_benchmark_suite()
