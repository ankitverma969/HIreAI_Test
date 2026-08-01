import re

from loguru import logger

from app.extractor.skills_database import SKILL_SYNONYMS


def extract_skills(text: str) -> list[str]:
    """Scans and detects standardized candidate technical skills from text.

    Utilizes boundary-safe regular expressions to prevent substring matches (e.g.
    preventing 'Go' from matching in 'Google') and maps raw occurrences to standard
    canonical terms (e.g. 'js' and 'java script' both resolve to 'JavaScript').

    Args:
        text: Preprocessed text content.

    Returns:
        Sorted list of standardized canonical skills.
    """
    logger.debug("Running skills extractor...")
    if not text:
        return []

    text_lower = text.lower()
    detected_skills = set()

    # Sort synonyms by length descending so longer phrases match first
    # (e.g. "machine learning" is matched and resolved before "ml")
    sorted_synonyms = sorted(SKILL_SYNONYMS.keys(), key=len, reverse=True)

    for synonym in sorted_synonyms:
        escaped_syn = re.escape(synonym)
        canonical_name = SKILL_SYNONYMS[synonym]

        # Check if the synonym includes special characters (+, #, .)
        if any(char in synonym for char in ("+", "#", ".")):
            # Use custom boundary check (disallowing letters/numbers around it)
            pattern = rf"(?<![a-zA-Z0-9])({escaped_syn})(?![a-zA-Z0-9])"
        else:
            # Use standard word boundaries
            pattern = rf"\b{escaped_syn}\b"

        if re.search(pattern, text_lower):
            detected_skills.add(canonical_name)

    sorted_list = sorted(list(detected_skills))
    logger.debug(f"Skills extraction completed. Detected {len(sorted_list)} skills.")
    return sorted_list
