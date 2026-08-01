import re

from loguru import logger

# Section headers representing professional summary
SUMMARY_HEADERS = re.compile(
    r"(?i)^[#\s-]*(?:summary|professional summary|objective|career objective|profile|about me|overview)\s*$"
)

def extract_summary(text: str) -> str | None:
    """Extracts qualitative candidate professional summary or objective text block.

    Args:
        text: Sanitized preprocessed document text.

    Returns:
        The extracted summary string (or None).
    """
    logger.debug("Running summary extractor...")
    if not text:
        return None

    lines = text.splitlines()
    summary_lines = []
    in_summary_section = False

    for _idx, line in enumerate(lines):
        line_strip = line.strip()
        if not line_strip:
            continue

        if SUMMARY_HEADERS.match(line_strip):
            in_summary_section = True
            continue
        elif in_summary_section and re.match(r"(?i)^[A-Z\s]{4,20}$", line_strip):
            # Stop if we reach a new major section header (e.g. SKILLS, EDUCATION)
            in_summary_section = False
            break

        if in_summary_section:
            summary_lines.append(line_strip)

    # Combine lines
    summary = " ".join(summary_lines).strip()

    # Fallback: if no summary section was matched, extract the first paragraph (if sensible)
    if not summary:
        fallback_lines = []
        for line in lines[:8]:  # Look in the top 8 lines
            line_strip = line.strip()
            # Skip short contact lines or names (usually under 60 chars with no punctuation)
            if len(line_strip) > 50 and not re.search(r"@|\+|github\.com|linkedin\.com", line_strip):
                fallback_lines.append(line_strip)
                if len(fallback_lines) >= 2:
                    break
        if fallback_lines:
            summary = " ".join(fallback_lines).strip()

    # Cap size of summary to a reasonable length
    if summary:
        summary = summary[:600]
        logger.debug(f"Extracted summary snippet of length {len(summary)}.")
        return summary

    logger.debug("No professional summary found.")
    return None
