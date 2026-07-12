from typing import Any
from core.ports.input_adapter import IInputAdapter

class ManualTextAdapter(IInputAdapter):
    def process(self, raw_data: Any) -> str:
        if not isinstance(raw_data, str):
            raise ValueError("ManualTextAdapter expects a string payload")
        return raw_data.strip()
