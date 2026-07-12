import os
import sqlite3

from infrastructure.database.connection import DatabaseConnectionManager
from infrastructure.repositories.sqlite_opportunity_repo import SqliteOpportunityRepository
from infrastructure.adapters.manual_text_adapter import ManualTextAdapter
from infrastructure.ai.llm_extractor import GeminiAIExtractor
from core.ingestion.pipeline import IngestionPipeline

def initialize_database(db_path: str, schema_path: str):
    if os.path.exists(db_path):
        os.remove(db_path) # Fresh start for E2E test
        
    with sqlite3.connect(db_path) as conn:
        with open(schema_path, 'r', encoding='utf-8') as f:
            schema_script = f.read()
            conn.executescript(schema_script)
            
def main():
    db_path = "test_cios.db"
    schema_path = "infrastructure/database/schema.sql"
    
    # 0. Setup DB schema
    print("Initializing Database...")
    initialize_database(db_path, schema_path)
    
    # 1. Setup DB Connection & Repository
    conn_manager = DatabaseConnectionManager(db_path)
    repo = SqliteOpportunityRepository(conn_manager)
    
    # 2. Setup AI Extractor & Scorer
    print("Initializing AI Extractor & Scorer...")
    try:
        from core.intelligence.scorer import OpportunityScorer
        from infrastructure.adapters.gemini_provider import GeminiProvider
        provider = GeminiProvider()
        extractor = GeminiAIExtractor()
        scorer = OpportunityScorer(llm_provider=provider)
    except ValueError as e:
        print(f"FAILED TO START AI: {e}")
        print("Please set the GEMINI_API_KEY environment variable and try again.")
        return
        
    # 3. Setup Deduplicator
    print("Initializing Deduplicator...")
    from core.ingestion.deduplicator import DuplicateDetector
    deduplicator = DuplicateDetector(repository=repo)
        
    # 4. Setup Pipeline
    pipeline = IngestionPipeline(
        repository=repo, 
        ai_extractor=extractor, 
        scorer=scorer,
        deduplicator=deduplicator
    )
    
    # 5. Setup Adapter
    text_adapter = ManualTextAdapter()
    
    # 5. Messy, unstructured real-world job description block
    raw_text = """
    Hey, I saw this job on HackerNews. 
    It's for a Senior Backend Engineer at a company called 'Pied Piper'.
    They are looking for someone with strong Python and compression algorithms experience.
    You should reach out to Richard Hendricks. His email is richard@piedpiper.com and phone is 555-0199.
    Looks super promising!
    """
    
    print("Ingesting unstructured raw text via AI pipeline (Attempt 1)...")
    
    # 7. Run Pipeline - First Pass
    opportunity_1 = pipeline.ingest(adapter=text_adapter, raw_data=raw_text)
    
    print(f"\n--- SUCCESS: INGESTED OPPORTUNITY 1 ---")
    print(f"ID: {opportunity_1.id}")
    
    print("\nIngesting the EXACT same raw text to test deduplication (Attempt 2)...")
    
    # 8. Run Pipeline - Second Pass
    opportunity_2 = pipeline.ingest(adapter=text_adapter, raw_data=raw_text)
    
    print(f"\n--- SUCCESS: INGESTED OPPORTUNITY 2 (Should be flagged) ---")
    print(f"ID: {opportunity_2.id}")
    
    duplicate_warning_found = any("[WARNING]: Potential duplicate detected" in (i.notes or "") for i in opportunity_2.interactions)
    if duplicate_warning_found:
        print("\n--- DEDUPLICATION TEST: PASSED ---")
        print(f"Opportunity 2 was successfully flagged as a duplicate and forced to {opportunity_2.status.value} status.")
    else:
        print("\n--- DEDUPLICATION TEST: FAILED ---")
        print("Opportunity 2 was NOT flagged as a duplicate.")
        
    print("\nVerifying persistence in database...")
    saved_opp = repo.get_by_business_id(opportunity_1.id)
    if saved_opp:
        print("--- DATABASE VERIFICATION: PASSED ---")
        print(f"Loaded: '{saved_opp.title}' at '{saved_opp.company}'")
        
        # Test State Transition Programmatically
        print("\nTesting State Transition (Detected -> Evaluating)...")
        from domain.opportunity import OpportunityStatus
        saved_opp.transition_to(OpportunityStatus.Evaluating)
        repo.update(saved_opp)
        
        verified_opp = repo.get_by_business_id(saved_opp.id)
        if verified_opp.status == OpportunityStatus.Evaluating:
            print("--- STATE TRANSITION TEST: PASSED ---")
        else:
            print("--- STATE TRANSITION TEST: FAILED ---")
    else:
        print("--- DATABASE VERIFICATION: FAILED ---")

if __name__ == "__main__":
    main()
