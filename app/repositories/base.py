from abc import ABC, abstractmethod
from typing import List, Optional, Generic, TypeVar

T = TypeVar("T")

class BaseRepository(ABC, Generic[T]):
    """Generic abstract base repository class representing persistence operations."""
    
    @abstractmethod
    def save(self, entity: T) -> T:
        """Saves an entity to persistence.
        
        Args:
            entity: Object data models.
            
        Returns:
            The saved object entity.
        """
        pass

    @abstractmethod
    def get_by_id(self, entity_id: str) -> Optional[T]:
        """Loads a saved entity by unique ID lookup.
        
        Args:
            entity_id: The lookup ID.
            
        Returns:
            The matching entity if found, otherwise None.
        """
        pass

    @abstractmethod
    def list_all(self) -> List[T]:
        """Lists all stored entities in repository path.
        
        Returns:
            List of stored entities.
        """
        pass
