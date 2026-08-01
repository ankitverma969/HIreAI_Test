import re

import spacy
from loguru import logger

# Regex patterns for contact fields
EMAIL_REGEX = re.compile(r"\b[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}\b")
PHONE_REGEX = re.compile(
    r"(?<!\w)(?:\+?\d{1,3}[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}(?!\w)"
)
LINKEDIN_REGEX = re.compile(
    r"\b(?:https?://)?(?:www\.)?linkedin\.com/in/[a-zA-Z0-9_-]+/?\b", re.IGNORECASE
)
GITHUB_REGEX = re.compile(
    r"\b(?:https?://)?(?:www\.)?github\.com/[a-zA-Z0-9_-]+/?\b", re.IGNORECASE
)
PORTFOLIO_REGEX = re.compile(
    r"\b(?:https?://)?(?:www\.)?(?:[a-zA-Z0-9_-]+\.)+(?:com|org|net|io|me|dev|co)(?:/[a-zA-Z0-9_.-]+)*/?\b",
    re.IGNORECASE
)

# Load spaCy model globally
try:
    nlp = spacy.load("en_core_web_sm")
except OSError:
    logger.warning("en_core_web_sm not found. Falling back to blank model.")
    nlp = spacy.blank("en")

def extract_contacts(text: str) -> dict[str, str | None]:
    """Extracts email, phone, LinkedIn, GitHub, portfolio URL, and location from text.

    Args:
        text: Sanitized preprocessed document text.

    Returns:
        Dictionary mapping contact keys to their extracted value string (or None).
    """
    logger.debug("Running contact details extractor...")

    contacts: dict[str, str | None] = {
        "email": None,
        "phone": None,
        "linkedin": None,
        "github": None,
        "portfolio": None,
        "location": None
    }

    if not text:
        return contacts

    # 1. Email extraction
    email_match = EMAIL_REGEX.search(text)
    if email_match:
        contacts["email"] = email_match.group(0).strip()

    # 2. Phone extraction
    phone_match = PHONE_REGEX.search(text)
    if phone_match:
        contacts["phone"] = phone_match.group(0).strip()

    # 3. LinkedIn extraction
    linkedin_match = LINKEDIN_REGEX.search(text)
    if linkedin_match:
        contacts["linkedin"] = linkedin_match.group(0).strip()

    # 4. GitHub extraction
    github_match = GITHUB_REGEX.search(text)
    if github_match:
        contacts["github"] = github_match.group(0).strip()

    # 5. Portfolio/Website extraction
    # Filter out email, linkedin, and github from general URL results
    urls = PORTFOLIO_REGEX.findall(text)
    for url in urls:
        url_str = url.strip()
        if "linkedin.com" not in url_str and "github.com" not in url_str and "@" not in url_str:
            contacts["portfolio"] = url_str
            break  # Grab first valid portfolio website match

    # 6. Location extraction using spaCy GPE (Geopolitical Entities) and regex fallbacks
    doc = nlp(text[:2000])  # Scan first 2000 characters (where contact info resides)
    gpes = [ent.text.strip() for ent in doc.ents if ent.label_ == "GPE"]

    # Also look for patterns like "Location: City, State" or "Address: City, State"
    loc_pattern = re.compile(
        r"(?i)(?:location|address|address:|reside in|based in|residence)\s*:\s*([a-zA-Z\s,]+)\b"
    )
    loc_match = loc_pattern.search(text[:2000])

    if loc_match:
        contacts["location"] = loc_match.group(1).strip()
    elif gpes:
        # Standardize if we get a few matching locations, join them or take the primary
        # For example, "New York, USA" or "San Francisco, CA"
        contacts["location"] = ", ".join(list(dict.fromkeys(gpes[:2])))

    logger.debug(f"Contact extraction details completed: {contacts}")
    return contacts
