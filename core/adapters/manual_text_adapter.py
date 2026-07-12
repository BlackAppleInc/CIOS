from typing import Any
from core.ports.input_adapter import IInputAdapter, NormalizedInput

class ManualTextAdapter(IInputAdapter):
    def extract_raw_data(self, source: Any) -> NormalizedInput:
        if not isinstance(source, str):
            raise ValueError("ManualTextAdapter expects a string source")
        return NormalizedInput(
            raw_text=source,
            source_type='manual',
            metadata={}
        )
