from typing import Dict, Any
from domain.opportunity import OpportunityCase, IOpportunityRepository

class IngestionPipeline:
    def __init__(self, repository: IOpportunityRepository):
        self.repository = repository

    def _mock_ai_extraction(self, raw_text: str) -> Dict[str, Any]:
        return {
            "title": "Software Architect",
            "company": "Tech Corp Inc.",
            "extracted_skills": ["Python", "Architecture", "System Design"]
        }

    def _mock_confidence_analysis(self, extracted_data: Dict[str, Any]) -> float:
        return 0.92

    def process(self, raw_text: str) -> OpportunityCase:
        try:
            extracted_data = self._mock_ai_extraction(raw_text)
            confidence = self._mock_confidence_analysis(extracted_data)
            
            opportunity = OpportunityCase(
                title=extracted_data["title"],
                company=extracted_data["company"],
                confidence_score=confidence,
                raw_ingestion_data={"source_text": raw_text, "extracted": extracted_data}
            )
            
            self.repository.save(opportunity)
            return opportunity
            
        except Exception as e:
            raise RuntimeError(f"Ingestion pipeline failed: {str(e)}") from e
