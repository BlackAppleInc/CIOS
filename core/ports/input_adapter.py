from abc import ABC, abstractmethod
from typing import Any, Union, List, TypedDict, Dict

class RawPayload(TypedDict):
    source: str
    metadata: Dict[str, Any]
    content: str

class IInputAdapter(ABC):
    """
    Port for defining how the system ingests data from external sources.
    Adapters convert raw formats (e.g. text, PDFs, Emails) into a list of RawPayload.
    """
    
    @abstractmethod
    def collect(self, **kwargs) -> List[RawPayload]:
        """Collects the raw external data and returns payloads for the pipeline."""
        pass

    def acknowledge(self, payload: RawPayload) -> None:
        """Called by the pipeline when a payload is successfully processed or permanently skipped."""
        pass
