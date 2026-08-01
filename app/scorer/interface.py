from abc import ABC, abstractmethod

from app.models.candidate import Candidate
from app.models.job_description import JobDescription
from app.models.score import Score


class BaseCandidateScorer(ABC):
    """Abstract Base Class defining the resume ranking scoring interface."""

    @abstractmethod
    def calculate_score(self, candidate: Candidate, jd: JobDescription) -> Score:
        """Calculates candidate matching scores against job requirements.

        Args:
            candidate: Struct of candidate credentials.
            jd: Target job description.

        Returns:
            Calculated score containing breakdown and matching metrics.

        Raises:
            ScoringException: If score calculations fail.
        """
        pass
