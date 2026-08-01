from abc import ABC, abstractmethod
from pathlib import Path


class BaseResumeParser(ABC):
    """Abstract Base Class defining interface for document loaders/parsers."""

    @abstractmethod
    def parse(self, file_path: Path) -> str:
        """Parses a resume file and extracts raw text content.

        Args:
            file_path: The filesystem path to the target document.

        Returns:
            The raw text content extracted from the document.

        Raises:
            ParsingException: If parsing fails.
        """
        pass
