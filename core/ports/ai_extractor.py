from abc import ABC, abstractmethod

class IAIExtractor(ABC):
    @abstractmethod
    def extract_opportunity(self, raw_text: str) -> dict:
        """
        Takes raw text and extracts structured opportunity data as a dictionary.
        """
        pass
