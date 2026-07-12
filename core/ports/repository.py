from abc import ABC, abstractmethod
from typing import TypeVar, Generic, Optional

T = TypeVar('T')

class IRepository(Generic[T], ABC):
    @abstractmethod
    def save(self, entity: T) -> None:
        """Saves the entity, updating if it exists or inserting if it does not."""
        pass
        
    @abstractmethod
    def update(self, entity: T) -> None:
        """Explicitly updates an existing entity."""
        pass

    @abstractmethod
    def get_by_business_id(self, business_id: str) -> Optional[T]:
        """Retrieves an entity by its business_id."""
        pass

    @abstractmethod
    def delete(self, business_id: str) -> None:
        """Deletes an entity by its business_id."""
        pass
        
    @abstractmethod
    def get_all(self, status: Optional[Any] = None) -> list[T]:
        """Retrieves all entities, optionally filtered by status."""
        pass
        
    @abstractmethod
    def get_pending_reminders(self) -> list[tuple[Any, str, str]]:
        """Optimized read query for pending reminders. Returns (Reminder, Title, Business_ID)."""
        pass

    @abstractmethod
    def get_pipeline_analytics(self) -> dict:
        """Executes read-only aggregation SQL queries to return pipeline funnel metrics."""
        pass

    @abstractmethod
    def search(self, keyword: str) -> list[T]:
        """Searches across critical text fields (Title, Company, Interaction Notes, Contact Names)."""
        pass

    @abstractmethod
    def get_global_network(self) -> list[dict]:
        """Retrieves a consolidated read-only network graph of contacts and counts."""
        pass
