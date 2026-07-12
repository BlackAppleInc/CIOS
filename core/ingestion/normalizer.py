import uuid
from datetime import datetime
from domain.opportunity import OpportunityCase, OpportunityStatus, Interaction, InteractionType
from domain.contact import Contact

class DomainNormalizer:
    @staticmethod
    def normalize(extracted_dict: dict, raw_text: str) -> OpportunityCase:
        title = extracted_dict.get("title") or "Unknown Title"
        company = extracted_dict.get("company") or "Unknown Company"
        confidence = extracted_dict.get("confidence_score", 0.5)
        
        opportunity = OpportunityCase(
            id=str(uuid.uuid4()),
            title=title,
            company=company,
            status=OpportunityStatus.Detected,
            confidence_score=float(confidence),
            raw_ingestion_data={"original_raw_text": raw_text, "extracted_json": extracted_dict},
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        
        contacts = extracted_dict.get("contacts", [])
        for c in contacts:
            contact = Contact(
                id=str(uuid.uuid4()),
                first_name=c.get("first_name", "") or "Unknown",
                last_name=c.get("last_name", ""),
                email=c.get("email", ""),
                phone=c.get("phone", "")
            )
            interaction = Interaction(
                id=str(uuid.uuid4()),
                interaction_type=InteractionType.Other,
                interaction_date=datetime.utcnow(),
                notes=extracted_dict.get("notes", "Extracted by AI"),
                contact=contact
            )
            opportunity.interactions.append(interaction)
            
        return opportunity
        
    @staticmethod
    def fallback(raw_text: str, error_msg: str) -> OpportunityCase:
        return OpportunityCase(
            id=str(uuid.uuid4()),
            title="Unknown Title (AI Failure)",
            company="Unknown Company",
            status=OpportunityStatus.Detected,
            confidence_score=0.0,
            raw_ingestion_data={"original_raw_text": raw_text, "error": error_msg},
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
