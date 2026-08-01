import re

from loguru import logger

from app.models.candidate import Certification

CERT_PROVIDERS = ["AWS", "Google", "Microsoft", "Cisco", "Oracle", "IBM", "Coursera", "Udemy", "Scrum Alliance", "PMI"]
CERT_DATE_REGEX = re.compile(r"\b((?:19|20)\d{2})\b")

def split_cert_line(line: str) -> list[str]:
    """Splits a single line into separate certification strings if it contains multiple mentions.

    Args:
        line: Raw line text.

    Returns:
        List of split certification strings.
    """
    lower = line.lower()
    mentions = lower.count("certified") + lower.count("certification") + lower.count("certificate")

    # If multiple cert-related words exist, or multiple providers, split by comma or semicolon
    provider_count = sum(1 for p in CERT_PROVIDERS if p.lower() in lower)

    if mentions > 1 or (mentions >= 1 and provider_count > 1):
        parts = re.split(r"[,;]+", line)
        cleaned_parts = []
        for part in parts:
            part_strip = part.strip()
            if len(part_strip) > 5:
                cleaned_parts.append(part_strip)
        if cleaned_parts:
            return cleaned_parts

    return [line]


def extract_certifications(text: str) -> list[Certification]:
    """Scans and extracts candidate professional certifications from text.

    Args:
        text: Sanitized preprocessed document text.

    Returns:
        List of structured Certification models.
    """
    logger.debug("Running certifications extractor...")
    certifications: list[Certification] = []

    if not text:
        return certifications

    lines = text.splitlines()
    in_cert_section = False
    cert_lines = []

    # 1. Look for explicit Certifications section
    for line in lines:
        line_strip = line.strip()
        if not line_strip:
            continue

        if re.search(r"(?i)^[#\s-]*(?:certifications|licenses|credentials|courses|training)\s*$", line_strip):
            in_cert_section = True
            continue
        elif in_cert_section and re.match(r"(?i)^[A-Z\s]{4,20}$", line_strip) and "cert" not in line_strip.lower():
            in_cert_section = False

        if in_cert_section:
            cert_lines.append(line_strip)

    # Process collected cert lines
    raw_candidates = []
    for line in cert_lines:
        clean_line = re.sub(r"^[-*•o\s]+", "", line).strip()
        if len(clean_line) >= 3:
            raw_candidates.extend(split_cert_line(clean_line))

    # 2. Fallback scan if section not found
    if not raw_candidates:
        for line in lines:
            if any(k in line.lower() for k in ("certified", "certification", "certificate")):
                clean_line = re.sub(r"^[-*•o\s]+", "", line).strip()
                if 10 < len(clean_line) < 150:
                    raw_candidates.extend(split_cert_line(clean_line))

    # Parse name, provider, and date from raw candidates
    for item in raw_candidates:
        if len(item) < 5 or len(item) > 100:
            continue

        # Parse date
        date_match = CERT_DATE_REGEX.search(item)
        issue_date = date_match.group(1) if date_match else None

        # Strip date from name text
        name_text = item
        if issue_date:
            name_text = re.sub(rf"\b{issue_date}\b", "", name_text).strip(" ,()-")

        # Guess provider
        provider = None
        for p in CERT_PROVIDERS:
            if p.lower() in name_text.lower():
                provider = p
                break

        # Deduplicate
        if not any(c.certification_name == name_text for c in certifications):
            certifications.append(Certification(
                certification_name=name_text,
                provider=provider or "Authorized Provider",
                issue_date=issue_date
            ))

    logger.debug(f"Certification extraction completed. Found {len(certifications)} items.")
    return certifications
