import re

from email_validator import EmailNotValidError, validate_email
from loguru import logger

from app.core.exceptions import ValidationException


def validate_email_address(email: str) -> str:
    """Validates and normalizes an email address.

    Args:
        email: Email string to check.

    Returns:
        Normalized email string.

    Raises:
        ValidationException: If email is invalid.
    """
    if not email:
        raise ValidationException("Email address cannot be empty")

    try:
        # Disable DNS check (check_deliverability=False) for static validation speed
        validated = validate_email(email.strip(), check_deliverability=False)
        return str(validated.normalized).lower()
    except EmailNotValidError as e:
        logger.warning(f"Email validation failed for '{email}': {str(e)}")
        raise ValidationException(f"Invalid email structure: {str(e)}") from e


def validate_phone_number(phone: str) -> str:
    """Validates if the phone number string matches global or local standards.

    Args:
        phone: Phone number string.

    Returns:
        Cleaned and normalized phone string.

    Raises:
        ValidationException: If phone string has no numbers or is format invalid.
    """
    if not phone:
        raise ValidationException("Phone number cannot be empty")

    cleaned = phone.strip()

    # Strip common formatting chars to get pure digits
    digits = re.sub(r"\D", "", cleaned)

    # Reject if too short (less than 7 digits) or too long (more than 15 digits)
    if not (7 <= len(digits) <= 15):
        logger.warning(f"Phone validation failed for '{phone}': digits length {len(digits)} out of bounds.")
        raise ValidationException("Phone number must contain between 7 and 15 digits")

    return cleaned


def validate_extracted_candidate(name: str | None, email: str | None, phone: str | None, text_content: str | None) -> None:
    """Validates that candidate parsing yielded core readable results.

    Args:
        name: Candidate full name.
        email: Candidate email.
        phone: Candidate phone number.
        text_content: Raw parsed resume text.

    Raises:
        ValidationException: If text is empty or all core contacts are missing.
    """
    if not text_content or not text_content.strip():
        raise ValidationException("Resume parsed content is empty or unreadable")

    # An enterprise screening pipeline requires at least some contact/identity details
    if not name and not email and not phone:
        raise ValidationException(
            "Candidate details are invalid: Unable to extract Name, Email, or Phone. Document might be unreadable."
        )

    logger.debug("Candidate payload verification complete.")
