from abc import ABC, abstractmethod
from typing import Optional, Dict, Any

class BaseLLMClient(ABC):
    """Abstract Base Class defining standard chat or completion wrapper endpoints."""
    
    @abstractmethod
    async def generate_completion(
        self, 
        prompt: str, 
        system_instruction: Optional[str] = None,
        json_mode: bool = False,
        temperature: float = 0.0
    ) -> str:
        """Invokes upstream generative language models.
        
        Args:
            prompt: User message prompt.
            system_instruction: Optional system instruction prompt.
            json_mode: Flag ensuring response strictly compiles to JSON syntax.
            temperature: Degree of exploration sampling.
            
        Returns:
            The raw text string result.
            
        Raises:
            LLMException: If upstream service fails.
        """
        pass
