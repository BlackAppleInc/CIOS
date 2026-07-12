import os
import json
from pydantic import BaseModel
from typing import List
from domain.opportunity import OpportunityCase
from core.ports.llm_provider import ILLMProvider

class StrategyBlueprint(BaseModel):
    key_selling_points: List[str]
    company_risks: List[str]
    potential_objections: List[str]
    mitigation_strategy: str
    strategic_questions: List[str]

class InterviewStrategist:
    """
    Synthesizes the user's profile and an opportunity case to generate 
    a strategic coaching and negotiation blueprint.
    """
    def __init__(self, llm_provider: ILLMProvider, profile_path: str = "data/user_profile.json"):
        self.provider = llm_provider
        self.profile_path = profile_path

    def _load_profile(self) -> dict:
        if not os.path.exists(self.profile_path):
            return {}
        with open(self.profile_path, 'r', encoding='utf-8') as f:
            return json.load(f)

    def generate_strategy(self, opportunity: OpportunityCase) -> dict:
        profile = self._load_profile()
        
        interactions_summary = [
            {
                "date": i.interaction_date.strftime("%Y-%m-%d"),
                "type": i.interaction_type.value,
                "notes": i.notes
            } for i in opportunity.interactions
        ]
        
        documents_summary = [
            {
                "name": d.name,
                "type": d.document_type
            } for d in opportunity.documents
        ]
        
        opp_data = {
            "title": opportunity.title,
            "company": opportunity.company,
            "status": opportunity.status.value,
            "confidence_score": opportunity.confidence_score,
            "raw_data": opportunity.raw_ingestion_data,
            "interactions": interactions_summary,
            "documents": documents_summary
        }
        
        prompt = f"""
You are an elite executive career strategist. Analyze the following job opportunity against the user's career preferences and generate a strategic briefing.
Return a STRICTLY valid JSON object (no markdown formatting, no backticks).

User Profile:
{json.dumps(profile, indent=2)}

Opportunity Details:
{json.dumps(opp_data, indent=2)}
"""
        response_model = self.provider.generate_structured_data(prompt, StrategyBlueprint)
        return response_model.model_dump()
