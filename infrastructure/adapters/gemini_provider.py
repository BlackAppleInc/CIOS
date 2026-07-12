import os
from pydantic import BaseModel
from google import genai
from core.ports.llm_provider import ILLMProvider

class GeminiProvider(ILLMProvider):
    def __init__(self, api_key: str = None):
        key = api_key or os.getenv("GEMINI_API_KEY")
        if not key:
            raise ValueError("GEMINI_API_KEY environment variable is missing")
        self.client = genai.Client(api_key=key)

    def generate_text(self, prompt: str) -> str:
        response = self.client.models.generate_content(
            model='gemini-2.5-flash',
            contents=prompt,
        )
        return response.text.strip()

    def generate_structured_data(self, prompt: str, response_model: type[BaseModel]) -> BaseModel:
        schema = response_model.model_json_schema()
        gemini_schema = self._translate_schema(schema)
        
        response = self.client.models.generate_content(
            model='gemini-2.5-flash',
            contents=prompt,
            config={'response_mime_type': 'application/json', 'response_schema': gemini_schema}
        )
        
        # Parse the JSON response into the Pydantic model
        return response_model.model_validate_json(response.text.strip())

    def _translate_schema(self, json_schema: dict) -> dict:
        """
        Translates a standard JSON Schema dictionary (as emitted by Pydantic)
        into Gemini's required response_schema dialect.
        """
        schema_type = json_schema.get("type", "object").upper()
        gemini_s = {"type": schema_type}
        
        if schema_type == "OBJECT" and "properties" in json_schema:
            gemini_s["properties"] = {
                k: self._translate_schema(v) 
                for k, v in json_schema["properties"].items()
            }
            if "required" in json_schema:
                gemini_s["required"] = json_schema["required"]
        elif schema_type == "ARRAY" and "items" in json_schema:
            gemini_s["items"] = self._translate_schema(json_schema["items"])
            
        return gemini_s
