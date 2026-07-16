import sys
import os
import json
import time

# Dynamically ensure top-level project module access
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../")))

from src.ingestion.job_trainer import VassalOpsJobTrainer

def compile_meta_existential_context():
    trainer = VassalOpsJobTrainer()
    
    role_title = "VassalOps Core Orchestration Layer"
    # Ingraining our exact development context directly into the local model memory framework
    meta_description = """
    You are the world's first ubiquitous VassalOps computing extension. 
    Your operational context is building the machine that multiplies output. 
    You work on: multi-process background task daemons, layout profiling, web coordinate scaling, and safe macro injection loops.
    Your mission: Observe user action paths, map out custom web elements with the layout profiler, and execute complex tool chains autonomously.
    Stack context: LangGraph state machines, SQLite audit ledgers, WebSockets, Win32 window processes, and Claude Code environments.
    """
    
    print(f"[VassalOps Meta] Compiling core framework existential context parameters...")
    profile_path = trainer.ingest_job_description(role_title, meta_description)
    print(f"[VassalOps Meta] Core design matrix successfully ingrained at: {profile_path}")

if __name__ == "__main__":
    compile_meta_existential_context()




