import os
import sqlite3
import sys

# Ensure modules can be resolved
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from infrastructure.repositories.sqlite_opportunity_repo import SqliteOpportunityRepository
from core.ingestion.pipeline import IngestionPipeline

def initialize_database(db_path: str, schema_path: str):
    os.makedirs(os.path.dirname(db_path), exist_ok=True)
    with open(schema_path, 'r') as f:
        schema_sql = f.read()
    
    with sqlite3.connect(db_path) as conn:
        conn.executescript(schema_sql)
        conn.commit()

def run_integration_test():
    db_path = "data/database/test_cios.db"
    schema_path = "infrastructure/database/schema.sql"
    
    initialize_database(db_path, schema_path)
    
    repo = SqliteOpportunityRepository(db_path)
    pipeline = IngestionPipeline(repo)
    
    dummy_job_description = "We are looking for a highly skilled Software Architect..."
    
    opportunity = pipeline.process(dummy_job_description)
    
    saved_opp = repo.find_by_id(opportunity.id)
    
    assert saved_opp is not None, "Opportunity was not saved"
    assert saved_opp.title == "Software Architect", "Title mismatch"
    assert saved_opp.status.value == "Detected", "Initial status should be Detected"
    
    # Cleanup test db
    if os.path.exists(db_path):
        os.remove(db_path)

if __name__ == "__main__":
    run_integration_test()
