from pathlib import Path

from loguru import logger

from app.core.exceptions import ParsingException
from app.parser.base_parser import BaseParser


class TextParser(BaseParser):
    """Document parser implementation for plain text documents."""

    def parse(self, file_path: Path) -> str:
        """Reads plain text from files with robust encoding checks.

        Args:
            file_path: Filesystem path to text file.

        Returns:
            Extracted text content.

        Raises:
            ParsingException: If reading files fail.
        """
        try:
            logger.info(f"Parsing Text document: '{file_path.name}'")

            # Try UTF-8 encoding
            try:
                with open(file_path, encoding="utf-8") as f:
                    text = f.read()
            except UnicodeDecodeError:
                logger.debug(f"UTF-8 decode failed for '{file_path.name}'. Trying Latin-1 fallback.")
                # Fallback to Latin-1
                with open(file_path, encoding="latin-1") as f:
                    text = f.read()

            if not text.strip():
                raise ParsingException(f"Text file contains no content: '{file_path.name}'")

            return text
        except Exception as e:
            if isinstance(e, ParsingException):
                raise e
            logger.error(f"Error parsing Text file '{file_path.name}': {str(e)}")
            raise ParsingException(f"Failed to parse Text document '{file_path.name}': {str(e)}") from e
