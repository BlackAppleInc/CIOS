import enum
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, Any, List

from domain.contact import Contact
from domain.company import Company
from domain.lifecycle import LifecycleException

class OpportunityStatus(enum.Enum):
    Detected = "Detected"
    Evaluating = "Evaluating"
    Preparing = "Preparing"
    Applied = "Applied"
    Interview = "Interview"
    Offer = "Offer"
    Closed = "Closed"

class InteractionType(enum.Enum):
    Email = "Email"
    Call = "Call"
    Meeting = "Meeting"
    LinkedIn = "LinkedIn"
    Other = "Other"

class ApplicationEventType(enum.Enum):
    Submission = "Submission"
    InterviewScheduled = "InterviewScheduled"
    InterviewCompleted = "InterviewCompleted"
    OfferReceived = "OfferReceived"
    Rejected = "Rejected"
    Withdrawn = "Withdrawn"
    OfferDeclined = "OfferDeclined"
    OfferAccepted = "OfferAccepted"

@dataclass
class CVVersion:
    id: str
    name: str
    file_path: str
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)

@dataclass
class ApplicationEvent:
    id: str
    event_type: ApplicationEventType
    event_date: datetime
    notes: Optional[str] = None
    cv_version: Optional[CVVersion] = None
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)

@dataclass
class Interaction:
    id: str
    interaction_type: InteractionType
    interaction_date: datetime
    notes: Optional[str] = None
    contact: Optional[Contact] = None
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)

@dataclass
class Reminder:
    id: str
    remind_at: datetime
    description: str
    is_completed: bool = False
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)

@dataclass
class Document:
    id: str
    name: str
    file_path: str
    document_type: str
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)

@dataclass
class Offer:
    id: str
    base_salary: float
    bonus_percentage: float
    equity_value: float
    benefits_summary: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)

@dataclass
class OpportunityCase:
    id: str
    title: str
    company: str
    status: OpportunityStatus
    confidence_score: float
    raw_ingestion_data: Any
    created_at: datetime
    updated_at: datetime
    
    # Aggregate children
    interactions: List[Interaction] = field(default_factory=list)
    events: List[ApplicationEvent] = field(default_factory=list)
    reminders: List[Reminder] = field(default_factory=list)
    documents: List[Document] = field(default_factory=list)
    offers: List[Offer] = field(default_factory=list)

    # Structured detail fields (optional — all default to None for backward-compat)
    location: Optional[str] = None
    salary_min: Optional[float] = None
    salary_max: Optional[float] = None
    expires_at: Optional[datetime] = None
    experience_required: Optional[str] = None
    source_platform: Optional[str] = None

    def __post_init__(self):
        if not self.title or not str(self.title).strip():
            raise ValueError("Title cannot be empty")
        if not self.company or not str(self.company).strip():
            raise ValueError("Company cannot be empty")

    def transition_to(self, new_status: OpportunityStatus):
        if new_status == OpportunityStatus.Closed:
            self.status = new_status
            self.updated_at = datetime.utcnow()
            return
            
        status_order = list(OpportunityStatus)
        current_index = status_order.index(self.status)
        new_index = status_order.index(new_status)

        if new_index < current_index:
            raise LifecycleException(f"Invalid state transition from {self.status.name} to {new_status.name}. Cannot move backwards.")
        
        # Prevent jumping states
        if new_index > current_index + 1:
             raise LifecycleException(f"Invalid state transition from {self.status.name} to {new_status.name}. Must follow sequential lifecycle.")

        self.status = new_status
        self.updated_at = datetime.utcnow()

    def add_interaction(self, interaction: Interaction):
        self.interactions.append(interaction)
        self.updated_at = datetime.utcnow()
        
    def add_event(self, event: ApplicationEvent):
        self.events.append(event)
        self.updated_at = datetime.utcnow()
        
    def add_reminder(self, reminder: Reminder):
        self.reminders.append(reminder)
        self.updated_at = datetime.utcnow()

    def add_document(self, document: Document):
        self.documents.append(document)
        self.updated_at = datetime.utcnow()

    def add_offer(self, offer: Offer):
        self.offers.append(offer)
        self.updated_at = datetime.utcnow()
