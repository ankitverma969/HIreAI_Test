from pathlib import Path

from app.core.exceptions import ParsingException
from app.parser.base_parser import BaseParser
from app.parser.docx_parser import DocxParser
from app.parser.pdf_parser import PDFParser
from app.parser.text_parser import TextParser


class ParserFactory:
    """Factory module selecting target document parsers based on file suffixes."""

    @staticmethod
    def get_parser(file_path: Path) -> BaseParser:
        """Determines and constructs the appropriate parser.

        Args:
            file_path: Target document path.

        Returns:
            The mapped parser object.

        Raises:
            ParsingException: If file format extension is unsupported.
        """
        suffix = file_path.suffix.lower()

        if suffix == ".pdf":
            return PDFParser()
        elif suffix == ".docx":
            return DocxParser()
        elif suffix in (".txt", ".md", ".json"):
            return TextParser()
        else:
            raise ParsingException(f"Unsupported document format extension '{suffix}' for file '{file_path.name}'")
