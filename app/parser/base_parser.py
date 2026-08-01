from abc import ABC, abstractmethod
from pathlib import Path


class BaseParser(ABC):
    """Abstract Base Class specifying interfaces for document files parsing."""

    @abstractmethod
    def parse(self, file_path: Path) -> str:
        """Parses document from path and extracts raw string content.

        Args:
            file_path: Absolute path to the source document.

        Returns:
            Extracted text content from the file.

        Raises:
            ParsingException: If parsing fails.
        """
        pass
