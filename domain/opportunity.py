from enum import Enum
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, Dict, Any, List
import uuid

class OpportunityStatus(Enum):
    DETECTED = 'Detected'
    EVALUATING = 'Evaluating'
    PREPARING = 'Preparing'
    APPLIED = 'Applied'
    INTERVIEWS = 'Interview(s)'
    OFFER = 'Offer'
    CLOSED = 'Closed'

@dataclass
class OpportunityCase:
    title: str
    company: str
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    status: OpportunityStatus = OpportunityStatus.DETECTED
    confidence_score: Optional[float] = None
    raw_ingestion_data: Optional[Dict[str, Any]] = None
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)

    def transition_to(self, new_status: OpportunityStatus) -> None:
        valid_transitions = {
            OpportunityStatus.DETECTED: [OpportunityStatus.EVALUATING, OpportunityStatus.CLOSED],
            OpportunityStatus.EVALUATING: [OpportunityStatus.PREPARING, OpportunityStatus.CLOSED],
            OpportunityStatus.PREPARING: [OpportunityStatus.APPLIED, OpportunityStatus.CLOSED],
            OpportunityStatus.APPLIED: [OpportunityStatus.INTERVIEWS, OpportunityStatus.CLOSED],
            OpportunityStatus.INTERVIEWS: [OpportunityStatus.OFFER, OpportunityStatus.CLOSED],
            OpportunityStatus.OFFER: [OpportunityStatus.CLOSED],
            OpportunityStatus.CLOSED: []
        }
        
        if new_status not in valid_transitions[self.status]:
            raise ValueError(f"Invalid transition from {self.status.value} to {new_status.value}")
        
        self.status = new_status
        self.updated_at = datetime.utcnow()

class IOpportunityRepository:
    def save(self, opportunity: OpportunityCase) -> None:
        raise NotImplementedError

    def find_by_id(self, id: str) -> Optional[OpportunityCase]:
        raise NotImplementedError

    def find_all(self) -> List[OpportunityCase]:
        raise NotImplementedError

    def find_by_status(self, status: OpportunityStatus) -> List[OpportunityCase]:
        raise NotImplementedError
