import pytest

from app.core.exceptions import ValidationException
from app.utils.validators import (
    validate_email_address,
    validate_extracted_candidate,
    validate_phone_number,
)


def test_validate_email_address_valid() -> None:
    """Verifies correct email normalization."""
    assert validate_email_address(" John.Doe@Example.com ") == "john.doe@example.com"


def test_validate_email_address_invalid() -> None:
    """Verifies invalid email format raises exception."""
    with pytest.raises(ValidationException):
        validate_email_address("not-an-email")


def test_validate_phone_number_valid() -> None:
    """Verifies phone number parsing succeeds with clean formatting."""
    assert validate_phone_number("+1 (555) 123-4567") == "+1 (555) 123-4567"


def test_validate_phone_number_invalid() -> None:
    """Verifies too short or long digit sequence raises exception."""
    with pytest.raises(ValidationException):
        # Only 4 digits
        validate_phone_number("1234")


def test_validate_extracted_candidate_missing() -> None:
    """Verifies exception raised when name, email, and phone are all missing."""
    with pytest.raises(ValidationException):
        validate_extracted_candidate(None, None, None, "Unstructured candidate description text without contact information.")


def test_validate_extracted_candidate_empty_text() -> None:
    """Verifies empty parsed text content raises exception."""
    with pytest.raises(ValidationException):
        validate_extracted_candidate("John Doe", "john@example.com", "1234567890", "")
