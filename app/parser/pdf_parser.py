from pathlib import Path

import fitz  # PyMuPDF
from loguru import logger

from app.core.exceptions import ParsingException
from app.parser.base_parser import BaseParser


class PDFParser(BaseParser):
    """Document parser implementation for PDF documents."""

    def parse(self, file_path: Path) -> str:
        """Extracts text from PDF files using PyMuPDF.

        Args:
            file_path: Filesystem path to PDF.

        Returns:
            Extracted text content.

        Raises:
            ParsingException: If pdf is corrupt or has no extractable text.
        """
        try:
            logger.info(f"Parsing PDF document: '{file_path.name}'")
            doc = fitz.open(file_path)

            text_parts = []
            for _i, page in enumerate(doc):
                page_text = page.get_text()
                text_parts.append(page_text)

            doc.close()
            full_text = "\n".join(text_parts)

            if not full_text.strip():
                raise ParsingException(f"PDF document contains no readable text: '{file_path.name}'")

            return full_text
        except Exception as e:
            if isinstance(e, ParsingException):
                raise e
            logger.error(f"Error parsing PDF file '{file_path.name}': {str(e)}")
            raise ParsingException(f"Failed to parse PDF document '{file_path.name}': {str(e)}") from e

    def get_page_count(self, file_path: Path) -> int:
        """Helper to get page count of target PDF.

        Args:
            file_path: Filesystem path to PDF.

        Returns:
            Number of pages.
        """
        try:
            doc = fitz.open(file_path)
            count = len(doc)
            doc.close()
            return count
        except Exception as e:
            logger.warning(f"Unable to read page count of '{file_path.name}': {str(e)}")
            return 0
