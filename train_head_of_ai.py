import sys
import os

# Dynamically ensure top-level project module access
sys.path.append(os.path.abspath(os.path.dirname(__file__)))

from src.ingestion.job_trainer import VassalOpsJobTrainer

def deploy_head_of_ai_training():
    trainer = VassalOpsJobTrainer()
    
    role_title = "Head of AI"
    role_description = """
    You own AI engineering for our client delivery business.
    Lead the projects. Own technical direction on client work end to end: scope, architecture, and making sure it ships and holds up in production.
    Build the machine. Stand up the workflows, guardrails, SOPs, and tooling that let a small, senior team deliver.
    Lead and build a 10x team. Hire, level up, and direct a lean pod where 5 people do the work of 50.
    Turn a 4-week project into a 4-day sprint with Claude Code workflows, AI agent teams, and systems thinking that multiply output.
    Work on: workflow automation, AI agents (sales, ops, comms), RAG and document Q&A, LLM integrations, data enrichment pipelines.
    Tech Landscape: Frontier and open models, embeddings, memory, agentic systems (tool use, orchestration, evals), fine-tuning, computer use, full-stack range, infra, reliability, and custom workflow engines.
    """
    
    print(f"[VassalOps Core] Injecting high-level cognitive blueprint text for '{role_title}'...")
    profile_path = trainer.ingest_job_description(role_title, role_description)
    print(f"[VassalOps Core] Role successfully compiled into local brain memory maps at: {profile_path}")

if __name__ == "__main__":
    deploy_head_of_ai_training()


