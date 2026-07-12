from abc import ABC, abstractmethod

class IAIExtractor(ABC):
    @abstractmethod
    def extract_opportunity(self, raw_text: str, metadata: dict = None) -> dict:
        """
        Takes raw text and optional metadata, and extracts structured opportunity data as a dictionary.
        """
        pass
