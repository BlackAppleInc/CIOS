from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional

@dataclass
class Company:
    id: str  # business_id
    name: str
    website: Optional[str] = None
    industry: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
