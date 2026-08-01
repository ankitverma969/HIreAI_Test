from pathlib import Path
from typing import Set
from app.core.constants import SUPPORTED_FILE_EXTENSIONS

def is_supported_file(filename: str) -> bool:
    """Verifies if the uploaded document has a supported extension.
    
    Args:
        filename: Name of the file.
        
    Returns:
        True if the file extension is supported, False otherwise.
    """
    ext = Path(filename).suffix.lower()
    return ext in SUPPORTED_FILE_EXTENSIONS


def get_file_type(filename: str) -> str:
    """Extracts extension as normalized file type keyword.
    
    Args:
        filename: Name of the file.
        
    Returns:
        Normalized file extension string (e.g. .pdf).
    """
    return Path(filename).suffix.lower()
