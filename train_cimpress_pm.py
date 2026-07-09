import sys
import os

# Dynamically ensure top-level project module access
sys.path.append(os.path.abspath(os.path.dirname(__file__)))

from src.ingestion.job_trainer import VassalOpsJobTrainer

def deploy_cimpress_training():
    trainer = VassalOpsJobTrainer()
    
    role_title = "Senior Product Manager - Supplier Product Data"
    role_description = """
    Company: Cimpress (Mass Customization Platform - MCP)
    Domain: Product Catalog / Supplier PIM (Product Information Management)
    Core Responsibilities: Own the product strategy for Supplier Product Data models, APIs, and supplier integrations. 
    Drive AI-enabled transformation: Data mapping, data quality detection, attribute recommendations, anomaly detection, and AI-assisted workflows with human review, confidence thresholds, and risk controls.
    Systems Scope: Attributes, pricing, supplier inventory feeds, fulfillment configuration, production constraints, and product launch workflows.
    Tech Requirements: Strong technical fluency with data models, system constraints, platform tradeoffs, internal data enrichment pipelines, and SaaS commerce backends.
    """
    
    print(f"[VassalOps Core] Injecting platform cognitive parameters for '{role_title}'...")
    profile_path = trainer.ingest_job_description(role_title, role_description)
    print(f"[VassalOps Core] Cimpress platform profile successfully compiled at: {profile_path}")

if __name__ == "__main__":
    deploy_cimpress_training()


