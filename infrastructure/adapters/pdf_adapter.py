import os
from typing import Any
from pypdf import PdfReader
from core.ports.input_adapter import IInputAdapter

class PdfAdapter(IInputAdapter):
    def process(self, raw_data: Any) -> str:
        """
        Expects raw_data to be a valid file path to a PDF.
        Extracts text and returns it.
        """
        if not isinstance(raw_data, str) or not os.path.exists(raw_data):
            raise ValueError(f"PdfAdapter expects a valid file path, got: {raw_data}")
            
        if not raw_data.lower().endswith(".pdf"):
            raise ValueError("File must be a PDF")
            
        extracted_text = []
        try:
            reader = PdfReader(raw_data)
            for page in reader.pages:
                text = page.extract_text()
                if text:
                    extracted_text.append(text)
        except Exception as e:
            raise ValueError(f"Failed to extract text from PDF: {e}") from e
            
        if not extracted_text:
            raise ValueError("No text could be extracted from the PDF")
            
        return "\n".join(extracted_text)
