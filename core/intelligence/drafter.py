import os
import json
from pathlib import Path
from datetime import datetime
from domain.opportunity import OpportunityCase
from core.ports.llm_provider import ILLMProvider

class ExecutiveDrafter:
    """
    Synthesizes case history into context-aware, highly professional drafts 
    for follow-ups, thank-you notes, and negotiation counter-offers.
    """
    def __init__(self, llm_provider: ILLMProvider, profile_path: str = "data/user_profile.json"):
        self.provider = llm_provider
        self.profile_path = profile_path
        self.export_dir = Path("data/exports/drafts")
        self.export_dir.mkdir(parents=True, exist_ok=True)

    def _load_profile(self) -> dict:
        if not os.path.exists(self.profile_path):
            return {}
        with open(self.profile_path, 'r', encoding='utf-8') as f:
            return json.load(f)

    def draft_communication(self, opportunity: OpportunityCase, intent: str) -> tuple[str, str]:
        profile = self._load_profile()
        
        interactions_summary = []
        contacts_seen = {}
        for i in opportunity.interactions:
            i_dict = {
                "date": i.interaction_date.strftime("%Y-%m-%d"),
                "type": i.interaction_type.value,
                "notes": i.notes
            }
            if i.contact:
                contact_name = f"{i.contact.first_name or ''} {i.contact.last_name or ''}".strip()
                i_dict["contact_name"] = contact_name
                contacts_seen[contact_name] = {
                    "email": i.contact.email,
                    "phone": i.contact.phone
                }
            interactions_summary.append(i_dict)
        
        opp_data = {
            "title": opportunity.title,
            "company": opportunity.company,
            "status": opportunity.status.value,
            "interactions": interactions_summary,
            "associated_contacts": contacts_seen
        }
        
        prompt = f"""
You are an elite executive assistant and communications drafter.
Draft a highly professional, concise, and data-driven email regarding an ongoing job opportunity.
Tone requirements: Senior Executive tone. Confident, concise, devoid of fluff, direct.

Identify the primary stakeholder (e.g., Headhunter, Hiring Manager, Recruiter) from the associated_contacts and address the email specifically to them.

Intent of the email: {intent}

User Profile Context (for reference):
{json.dumps(profile, indent=2)}

Opportunity & Historical Context:
{json.dumps(opp_data, indent=2)}

Output ONLY the raw email text (Subject line included at the top). Do not include markdown code blocks or conversational fillers.
"""
        draft_text = self.provider.generate_text(prompt)
        
        # Clean markdown code blocks if the model wrapped it anyway
        if draft_text.startswith("```"):
            lines = draft_text.split('\n')
            if len(lines) > 2:
                draft_text = "\n".join(lines[1:-1]).strip()
        
        # Save to file
        filename = f"Draft_{opportunity.id}_{intent}.md"
        dest_path = self.export_dir / filename
        
        with open(dest_path, "w", encoding="utf-8") as f:
            f.write(draft_text)
            
        return draft_text, str(dest_path.resolve())
