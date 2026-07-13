import logging
import uuid
from datetime import datetime
from core.ports.input_adapter import IInputAdapter
from core.ports.ai_extractor import IAIExtractor
from core.ports.repository import IRepository
from domain.opportunity import OpportunityCase, Interaction, InteractionType
from typing import Optional
from core.ingestion.normalizer import DomainNormalizer
from core.intelligence.scorer import OpportunityScorer
from core.ingestion.deduplicator import DuplicateDetector

logger = logging.getLogger(__name__)

class IngestionPipeline:
    def __init__(
        self, 
        repository: IRepository[OpportunityCase], 
        ai_extractor: IAIExtractor,
        scorer: OpportunityScorer = None,
        deduplicator: DuplicateDetector = None
    ):
        self.repository = repository
        self.ai_extractor = ai_extractor
        self.scorer = scorer
        self.deduplicator = deduplicator

    def ingest(self, adapter: IInputAdapter, **kwargs) -> OpportunityCase:
        payloads = adapter.collect(**kwargs)
        if payloads:
            return self._ingest_single(payloads[0])
        raise ValueError("Adapter returned empty list on single ingest.")
        
    def ingest_batch(self, adapter: IInputAdapter, **kwargs) -> list[OpportunityCase]:
        mark_read = kwargs.pop("mark_read", False)
        payloads = adapter.collect(**kwargs)
            
        results = []
        fail_count = 0
        skipped_count = 0
        skipped_sender_count = 0
        
        import time
        from rich.console import Console
        console = Console()
        
        NOISE_SENDER_PATTERNS = ["no-reply@accounts.google.com"]
        
        for i, payload in enumerate(payloads):
            if i > 0:
                time.sleep(13) # Rate limit safety
                
            if payload.get("content") and payload["content"].strip():
                sender = payload.get("metadata", {}).get("sender", "").lower()
                if any(noise in sender for noise in NOISE_SENDER_PATTERNS):
                    skipped_sender_count += 1
                    subject = payload.get("metadata", {}).get("subject", "Unknown Subject")
                    console.print(f"[bold cyan]Skipped (sender filter):[/bold cyan] '{subject}' from '{sender}'")
                    if mark_read and hasattr(adapter, 'acknowledge'):
                        adapter.acknowledge(payload)
                    continue

                try:
                    res = self._ingest_single(payload)
                    if res is None:
                        skipped_count += 1
                        subject = payload.get("metadata", {}).get("subject", "Unknown Subject")
                        console.print(f"[bold cyan]Skipped (not job-related):[/bold cyan] '{subject}'")
                    else:
                        results.append(res)
                        
                    if mark_read and hasattr(adapter, 'acknowledge'):
                        adapter.acknowledge(payload)
                except Exception as e:
                    fail_count += 1
                    subject = payload.get("metadata", {}).get("subject", "Unknown Subject")
                    error_sender = payload.get("metadata", {}).get("sender", "Unknown Sender")
                    console.print(f"[bold red]Extraction Failed:[/bold red] '{subject}' from '{error_sender}'. Error: {e}")
                    
        total = len(payloads)
        if total > 0:
            console.print(f"\n[bold yellow]Batch Summary:[/bold yellow] {total} emails read, {len(results)} ingested, {fail_count} failed extraction, {skipped_count} skipped (not job-related), {skipped_sender_count} skipped (sender filter) — see log above")
            
        return results

    def _ingest_single(self, payload: dict) -> Optional[OpportunityCase]:
        raw_text = payload.get("content", "")
        metadata = payload.get("metadata", {})
        
        # Step 2: AI Extractor & Normalization
        extracted_json = self.ai_extractor.extract_opportunity(raw_text, metadata=metadata)
        
        is_job = extracted_json.get("is_job_opportunity")
        title = extracted_json.get("title")
        company = extracted_json.get("company")
        
        if is_job is False:
            return None
            
        if not title and not company:
            return None
            
        if title in [None, "", "Unknown Title", "Unknown"] and company in [None, "", "Unknown Company", "Unknown", "Google"]:
            return None
            
        opportunity_case = DomainNormalizer.normalize(extracted_json, raw_text, metadata=metadata)
            
        # Step 3: Confidence Scoring
        if self.scorer:
            try:
                scoring_result = self.scorer.score(opportunity_case)
                score_val = scoring_result.get("score")
                notes_val = scoring_result.get("analysis_notes")
                
                if score_val is not None:
                    # Enforce constraint 0.0 to 1.0
                    opportunity_case.confidence_score = max(0.0, min(1.0, float(score_val)))
                    
                if notes_val:
                    analysis_interaction = Interaction(
                        id=str(uuid.uuid4()),
                        interaction_type=InteractionType.Other,
                        interaction_date=datetime.utcnow(),
                        notes=f"[AI Scoring Analysis]: {notes_val}"
                    )
                    opportunity_case.interactions.append(analysis_interaction)
            except Exception as e:
                logger.error(f"Scoring failed, proceeding without score: {e}")
                opportunity_case.confidence_score = None
                
        # Step 4: Duplicate Detection
        if self.deduplicator:
            try:
                self.deduplicator.check_for_duplicates(opportunity_case)
            except Exception as e:
                logger.error(f"Deduplication check failed: {e}")
        
        # Step 5: Repository Save
        self.repository.save(opportunity_case)
        
        return opportunity_case
