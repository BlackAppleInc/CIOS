from typing import Any, List
from core.ports.input_adapter import IInputAdapter, RawPayload

class ManualTextAdapter(IInputAdapter):
    def collect(self, **kwargs) -> List[RawPayload]:
        raw_data = kwargs.get("raw_data")
        if not isinstance(raw_data, str):
            raise ValueError("ManualTextAdapter expects a string payload in raw_data")
        
        return [{
            "source": "manual",
            "metadata": {},
            "content": raw_data.strip()
        }]
