import typing
from pydantic import BaseModel

class ILLMProvider(typing.Protocol):
    def generate_text(self, prompt: str) -> str:
        """Generates plain text response for a given prompt."""
        ...

    def generate_structured_data(self, prompt: str, response_model: type[BaseModel]) -> BaseModel:
        """Generates a structured response strictly conforming to the given Pydantic model."""
        ...
