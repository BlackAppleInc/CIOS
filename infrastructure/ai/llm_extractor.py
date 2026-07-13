import os
import json
from google import genai
from google.genai import types

from core.ports.ai_extractor import IAIExtractor

class GeminiAIExtractor(IAIExtractor):
    def __init__(self):
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise ValueError("GEMINI_API_KEY environment variable is missing")
        self.client = genai.Client(api_key=api_key)

    def extract_opportunity(self, raw_text: str, metadata: dict = None) -> dict:
        metadata_context = ""
        if metadata:
            metadata_context = f"\nMetadata Context:\n{json.dumps(metadata, indent=2)}\n"
            
        prompt = f"""
You are an expert HR data extraction assistant.
Extract the opportunity details from the following raw text and return a strictly valid JSON object.
Do NOT include markdown formatting, backticks, or any explanation around the JSON.

Expected JSON schema:
{{
  "is_job_opportunity": boolean (true if this is a job posting/offer, false otherwise),
  "title": "Job Title (string, null if not a job opportunity)",
  "company": "Company Name (string, null if not a job opportunity)",
  "confidence_score": 0.0 to 1.0 (float),
  "source_platform": "Origin platform string (e.g., 'LinkedIn', 'Tecoloco', 'Computrabajo', 'Direct Email', etc., null if not detected. Deduce by checking email domain or sender in metadata context and terms in raw text)",
  "expires_at": "Application deadline or expiration date in YYYY-MM-DD format (string, null if not found)",
  "contacts": [
    {{
      "first_name": "string",
      "last_name": "string",
      "email": "string",
      "phone": "string"
    }}
  ],
  "notes": "Any other context or notes (string)"
}}

IMPORTANT: If the email is clearly NOT a job opportunity (e.g., security alerts, newsletters, receipts, generic notices), set "is_job_opportunity" to false and leave title and company empty or null.

{metadata_context}
Raw text to extract from:
---
{raw_text}
---
"""
        response = self.client.models.generate_content(
            model='gemini-flash-latest',
            contents=prompt,
        )
        text = response.text.strip()
        
        # Clean up any markdown code blocks if the LLM includes them
        if text.startswith("```json"):
            text = text[7:]
        if text.startswith("```"):
            text = text[3:]
        if text.endswith("```"):
            text = text[:-3]
            
        text = text.strip()
        
        try:
            return json.loads(text)
        except json.JSONDecodeError as e:
            raise ValueError(f"LLM did not return valid JSON: {text}") from e
