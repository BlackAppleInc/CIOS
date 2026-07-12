import os
from typing import Any, List
from pypdf import PdfReader
from core.ports.input_adapter import IInputAdapter, RawPayload

class PdfAdapter(IInputAdapter):
    def collect(self, **kwargs) -> List[RawPayload]:
        """
        Expects kwargs to contain a 'raw_data' which is a valid file path to a PDF.
        Extracts text and returns it in a RawPayload.
        """
        raw_data = kwargs.get("raw_data")
        
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
            
        return [{
            "source": "pdf",
            "metadata": {"file_path": raw_data},
            "content": "\n".join(extracted_text)
        }]
