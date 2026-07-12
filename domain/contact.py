from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional
from domain.company import Company

@dataclass
class Contact:
    id: str  # business_id
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    company: Optional[Company] = None
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
