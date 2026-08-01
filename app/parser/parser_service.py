import time
from pathlib import Path
from typing import Any

from loguru import logger

from app.core.exceptions import ParsingException
from app.parser.parser_factory import ParserFactory
from app.parser.pdf_parser import PDFParser
from app.utils.text_cleaner import clean_text


class ParserService:
    """Orchestrates parsing workflows, metrics extraction, and text normalization."""

    @staticmethod
    async def parse_document(file_path: Path) -> dict[str, Any]:
        """Reads, parses, cleanses, and logs document ingestion statistics.

        Args:
            file_path: Absolute path to target document.

        Returns:
            Dictionary payload containing raw, clean text, and processing metadata.

        Raises:
            ParsingException: If parsing fails or extension is invalid.
        """
        start_time = time.perf_counter()

        if not file_path.exists():
            logger.error(f"Ingestion failed: File does not exist at path '{file_path}'")
            raise ParsingException(f"Target file not found: '{file_path.name}'")

        file_size = file_path.stat().st_size
        logger.info(f"Loaded file '{file_path.name}' ({file_size} bytes)")

        # Select parser
        try:
            parser = ParserFactory.get_parser(file_path)
            logger.info(f"Selected parser '{parser.__class__.__name__}' for file '{file_path.name}'")
        except ParsingException as e:
            logger.warning(f"Failed to identify parser for file '{file_path.name}': {str(e)}")
            raise e

        # Parse text content
        raw_text = parser.parse(file_path)
        logger.debug(f"Raw text extracted from '{file_path.name}' (Length: {len(raw_text)})")

        # Clean text content
        cleaned_text = clean_text(raw_text)
        logger.debug(f"Sanitized text compiled for '{file_path.name}' (Length: {len(cleaned_text)})")

        # Calculate page counts if PDF
        pages = 0
        if isinstance(parser, PDFParser):
            pages = parser.get_page_count(file_path)

        duration = time.perf_counter() - start_time
        logger.info(
            f"Parsing pipeline complete for '{file_path.name}' in {duration:.4f}s. "
            f"Parser: {parser.__class__.__name__}, Pages: {pages}"
        )

        return {
            "file_name": file_path.name,
            "file_size": file_size,
            "pages": pages,
            "parser_used": parser.__class__.__name__,
            "processing_time": duration,
            "raw_text": raw_text,
            "cleaned_text": cleaned_text
        }
