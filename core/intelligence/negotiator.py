import os
import json
from pydantic import BaseModel
from typing import List, Optional
from domain.opportunity import OpportunityCase, Offer
from core.ports.llm_provider import ILLMProvider

class NegotiationAnalysis(BaseModel):
    financial_gap_analysis: str
    leverage_points: List[str]
    suggested_counter_offer_strategy: str
    risk_factors: List[str]

class NegotiationStrategist:
    """
    Evaluates an offer against baseline requirements to formulate a highly logical, data-driven negotiation strategy.
    """
    def __init__(self, llm_provider: ILLMProvider, profile_path: str = "data/user_profile.json"):
        self.provider = llm_provider
        self.profile_path = profile_path

    def _load_profile(self) -> dict:
        if not os.path.exists(self.profile_path):
            return {}
        with open(self.profile_path, 'r', encoding='utf-8') as f:
            return json.load(f)

    def evaluate_offer(self, opportunity: OpportunityCase, offer: Offer) -> str:
        profile = self._load_profile()
        
        opp_context = {
            "title": opportunity.title,
            "company": opportunity.company,
            "confidence_score": opportunity.confidence_score
        }
        
        offer_context = {
            "base_salary": offer.base_salary,
            "bonus_percentage": offer.bonus_percentage,
            "equity_value": offer.equity_value,
            "benefits_summary": offer.benefits_summary
        }
        

        
        prompt = f"""
You are an elite executive negotiation strategist.
Evaluate the following job offer against the user's baseline constraints.
Tone requirements: Cold, analytical, concise executive tone. No fluff. Optimization is strictly for ROI and leverage mapping.

User Profile Context (Baseline Constraints):
{json.dumps(profile, indent=2)}

Opportunity Context:
{json.dumps(opp_context, indent=2)}

Offer Financial Data:
{json.dumps(offer_context, indent=2)}

Output a strict JSON matching the required schema.
"""
        response_model = self.provider.generate_structured_data(prompt, NegotiationAnalysis)
        return response_model.model_dump_json()
