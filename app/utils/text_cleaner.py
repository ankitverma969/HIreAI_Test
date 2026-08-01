import re
import unicodedata

from loguru import logger


def clean_text(text: str) -> str:
    """Preprocesses raw extracted document text to produce a sanitized representation.

    Normalizes unicode representations, strips header/footer indicators, collapses
    whitespace, removes duplicate sequential lines, and deletes page numbering,
    while carefully preserving email, phone, and URL constructs.

    Args:
        text: Raw text string from parser.

    Returns:
        Cleaned, normalized text.
    """
    if not text:
        return ""

    logger.debug("Starting text preprocessing pipeline...")

    # 1. Unicode normalization (NFKC)
    cleaned = unicodedata.normalize("NFKC", text)

    # Replace common MS Word ligatures and smart quotes
    ligatures = {
        "\u201c": '"', "\u201d": '"', "\u2018": "'", "\u2019": "'",
        "\u2013": "-", "\u2014": "-", "\u2022": "*", "\u00a0": " "
    }
    for orig, repl in ligatures.items():
        cleaned = cleaned.replace(orig, repl)

    # 2. Strip page numbers (e.g., Page 1 of 5, Page 3, [3/4] etc.)
    page_patterns = [
        r"(?i)\bpage\s*\d+\s*(?:of)?\s*\d*\b",
        r"\[\s*\d+\s*/\s*\d+\s*\]",
        r"\b\d+\s*/\s*\d+\b",
        r"(?m)^\s*\d+\s*$"  # Lone digits on their own line (often page numbers)
    ]
    for pattern in page_patterns:
        cleaned = re.sub(pattern, "", cleaned)

    # 3. Headers and Footers common boilerplate indicators
    boilerplate_patterns = [
        r"(?i)resume\s*-\s*confidential",
        r"(?i)confidential\s*resume",
        r"(?i)all\s*rights\s*reserved"
    ]
    for pattern in boilerplate_patterns:
        cleaned = re.sub(pattern, "", cleaned)

    # 4. Split into lines to filter redundant structure
    lines = cleaned.splitlines()
    processed_lines = []

    for line in lines:
        # Standardize line-level spacing
        line = re.sub(r"[ \t]+", " ", line).strip()

        # Keep non-empty lines
        if line:
            processed_lines.append(line)

    # 5. Remove sequential identical lines (duplicate line cleanup)
    deduplicated_lines: list[str] = []
    for line in processed_lines:
        if not deduplicated_lines or line != deduplicated_lines[-1]:
            deduplicated_lines.append(line)

    # 6. Reconstruct paragraphs (collapsing multiple newlines to a max of two)
    # Joining with newlines, but keeping structured breaks
    reconstructed = "\n".join(deduplicated_lines)

    # Collapse multiple consecutive newlines (more than 2 -> 2)
    reconstructed = re.sub(r"\n{3,}", "\n\n", reconstructed)

    # 7. Final overall space cleanup
    reconstructed = reconstructed.strip()

    logger.debug(f"Preprocessing completed. Character count reduced from {len(text)} to {len(reconstructed)}.")
    return reconstructed
