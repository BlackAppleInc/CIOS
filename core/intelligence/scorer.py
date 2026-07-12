import os
import json
from pydantic import BaseModel
from domain.opportunity import OpportunityCase
from core.ports.llm_provider import ILLMProvider

class ScoringResult(BaseModel):
    score: float
    analysis_notes: str

class OpportunityScorer:
    def __init__(self, llm_provider: ILLMProvider, profile_path: str = "data/user_profile.json"):
        self.provider = llm_provider
        self.profile_path = profile_path

    def _load_profile(self) -> dict:
        if not os.path.exists(self.profile_path):
            return {}
        with open(self.profile_path, 'r', encoding='utf-8') as f:
            return json.load(f)

    def score(self, opportunity: OpportunityCase) -> dict:
        """
        Evaluates the opportunity against the user's career profile.
        Returns a dict with 'score' (float) and 'analysis_notes' (str).
        """
        profile = self._load_profile()
        
        opp_data = {
            "title": opportunity.title,
            "company": opportunity.company,
            "raw_data": opportunity.raw_ingestion_data
        }
        
        prompt = f"""
You are an expert career advisor.
Evaluate the following job opportunity against the user's career profile.
Return a STRICTLY valid JSON object (no markdown, no backticks).

User Profile:
{json.dumps(profile, indent=2)}

Opportunity Details:
{json.dumps(opp_data, indent=2)}
"""
        response_model = self.provider.generate_structured_data(prompt, ScoringResult)
        return response_model.model_dump()
