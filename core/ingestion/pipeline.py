import logging
import uuid
from datetime import datetime
from core.ports.input_adapter import IInputAdapter
from core.ports.ai_extractor import IAIExtractor
from core.ports.repository import IRepository
from domain.opportunity import OpportunityCase, Interaction, InteractionType
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

    def ingest(self, adapter: IInputAdapter, raw_data: any) -> OpportunityCase:
        raw_text = adapter.process(raw_data)
        if isinstance(raw_text, list):
            # If adapter returns a list but single ingest called, just take the first one or fail.
            if raw_text:
                raw_text = raw_text[0]
            else:
                raise ValueError("Adapter returned empty list on single ingest.")
        return self._ingest_single(raw_text)
        
    def ingest_batch(self, adapter: IInputAdapter, raw_data: any = None) -> list[OpportunityCase]:
        raw_texts = adapter.process(raw_data)
        if not isinstance(raw_texts, list):
            raw_texts = [raw_texts]
            
        results = []
        for text in raw_texts:
            if text and text.strip():
                results.append(self._ingest_single(text))
        return results

    def _ingest_single(self, raw_text: str) -> OpportunityCase:
        # Step 2: AI Extractor & Normalization
        try:
            extracted_json = self.ai_extractor.extract_opportunity(raw_text)
            opportunity_case = DomainNormalizer.normalize(extracted_json, raw_text)
        except Exception as e:
            logger.error(f"AI Extraction failed: {e}")
            opportunity_case = DomainNormalizer.fallback(raw_text, str(e))
            
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
