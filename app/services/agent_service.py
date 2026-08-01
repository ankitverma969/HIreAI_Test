from abc import ABC, abstractmethod
from typing import List
from app.models.report import Report

class BaseAgentService(ABC):
    """Orchestrates job parsing, resume screening, scoring, ranking, and exporting."""
    
    @abstractmethod
    async def run_screening_workflow(
        self, 
        job_description_path: str, 
        resumes_paths: List[str]
    ) -> Report:
        """Triggers the full LangGraph-driven candidate screening workflow process.
        
        Args:
            job_description_path: Path to the target Job Description file.
            resumes_paths: Paths to the target Candidate Resumes.
            
        Returns:
            The compiled Report details containing scores and ranks.
            
        Raises:
            ResumeAgentException: For any processing failure.
        """
        pass
