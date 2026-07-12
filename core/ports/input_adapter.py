from abc import ABC, abstractmethod
from typing import Any, Union, List

class IInputAdapter(ABC):
    """
    Port for defining how the system ingests data from external sources.
    Adapters convert raw formats (e.g. text, PDFs, Emails) into a standard string or list of strings.
    """
    
    @abstractmethod
    def process(self, raw_data: Any) -> Union[str, List[str]]:
        """Processes the raw external data and returns string payload(s) for the pipeline."""
        pass
