from abc import ABC, abstractmethod

from app.models.candidate import Candidate


class BaseCandidateExtractor(ABC):
    """Abstract Base Class for extracting structured fields from raw text."""

    @abstractmethod
    async def extract(self, raw_text: str) -> Candidate:
        """Processes raw text using LLM or NLP techniques to structure the profile.

        Args:
            raw_text: Raw string text extracted from a resume.

        Returns:
            Structured CandidateProfile.

        Raises:
            LLMException: If the extraction fails due to downstream failures.
        """
        pass
