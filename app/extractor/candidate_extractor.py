import hashlib
import re
import time
from datetime import datetime
from typing import Any

from loguru import logger

from app.extractor.certification_extractor import extract_certifications
from app.extractor.contact_extractor import extract_contacts
from app.extractor.education_extractor import extract_education
from app.extractor.experience_extractor import (
    calculate_total_experience,
    extract_experience,
)
from app.extractor.project_extractor import extract_projects
from app.extractor.skills_extractor import extract_skills
from app.extractor.summary_extractor import extract_summary
from app.models.candidate import Candidate, CandidateMetadata
from app.utils.validators import (
    validate_email_address,
    validate_extracted_candidate,
    validate_phone_number,
)

# Standard language indicators to match
LANGUAGES_DATABASE = ["English", "Spanish", "French", "German", "Mandarin", "Hindi", "Japanese", "Russian", "Portuguese", "Italian", "Arabic", "Bengali"]

def extract_candidate_name(text: str) -> str | None:
    """Extracts candidate name by analyzing top lines.

    Args:
        text: Sanitized preprocessed document text.

    Returns:
        The extracted candidate name (or None).
    """
    lines = text.splitlines()
    for line in lines[:5]:
        clean = line.strip()
        if not clean:
            continue

        # Skip if contains contact details
        if "@" in clean or "+" in clean or "github.com" in clean.lower() or "linkedin.com" in clean.lower():
            continue

        # Remove bullet marks
        clean = re.sub(r"^[-*•o\s]+", "", clean).strip()

        # Valid name: 2 to 4 words containing only letters
        words = clean.split()
        if 2 <= len(words) <= 4 and all(re.match(r"^[A-Za-z]+$", w) for w in words):
            return clean

    return None


def extract_languages(text: str) -> list[str]:
    """Matches and parses languages from full text.

    Args:
        text: Sanitized preprocessed document text.

    Returns:
        List of matched languages.
    """
    found = []
    text_lower = text.lower()
    for lang in LANGUAGES_DATABASE:
        pattern = rf"\b{re.escape(lang.lower())}\b"
        if re.search(pattern, text_lower):
            found.append(lang)
    return found


def generate_candidate_id(name: str | None, email: str | None) -> str:
    """Generates unique deterministic candidate UUID-like tracking ID.

    Args:
        name: Name string.
        email: Email string.

    Returns:
        String hash ID.
    """
    # Deterministic generation using name & email if available, otherwise fallback to timestamp UUID
    seed = f"{name or 'candidate'}-{email or 'noemail'}"
    return hashlib.md5(seed.encode("utf-8")).hexdigest()[:16]


class CandidateExtractor:
    """Orchestrator pipeline module coordinating resume information extraction."""

    @staticmethod
    async def extract_candidate_profile(
        parsed_doc: dict[str, Any]
    ) -> Candidate:
        """Runs the hybrid regex/NLP parsing pipeline to extract candidate profiles.

        Args:
            parsed_doc: Output metadata from ParserService.parse_document.

        Returns:
            Validated structured Candidate Pydantic object.

        Raises:
            ValidationException: If parsed core candidate fields fail checks.
        """
        start_time = time.perf_counter()

        file_name = parsed_doc["file_name"]
        file_size = parsed_doc["file_size"]
        pages = parsed_doc["pages"]
        parser_used = parsed_doc["parser_used"]
        parsed_doc["raw_text"]
        cleaned_text = parsed_doc["cleaned_text"]

        logger.info(f"Triggering candidate details extraction for '{file_name}'")

        # 1. Extract contact details
        contacts = extract_contacts(cleaned_text)
        email = contacts["email"]
        phone = contacts["phone"]

        # Normalize and validate contacts if present
        validated_email = None
        if email:
            try:
                validated_email = validate_email_address(email)
            except Exception:
                # Let it fallback to None or let validation catch it if critical
                pass

        validated_phone = None
        if phone:
            try:
                validated_phone = validate_phone_number(phone)
            except Exception:
                pass

        # 2. Extract name
        name = extract_candidate_name(cleaned_text)

        # Validate overall parsed readability status
        validate_extracted_candidate(name, validated_email, validated_phone, cleaned_text)

        # 3. Extract remaining fields
        summary = extract_summary(cleaned_text)
        skills = extract_skills(cleaned_text)
        experience = extract_experience(cleaned_text)
        education = extract_education(cleaned_text)
        projects = extract_projects(cleaned_text)
        certifications = extract_certifications(cleaned_text)
        languages = extract_languages(cleaned_text)

        # Calculate experience metric
        total_exp = calculate_total_experience(experience)

        # Generate metadata
        duration = time.perf_counter() - start_time + parsed_doc["processing_time"]
        meta = CandidateMetadata(
            file_name=file_name,
            file_size=file_size,
            pages=pages,
            parser_used=parser_used,
            processing_time=duration,
            extraction_timestamp=datetime.utcnow()
        )

        cand_id = generate_candidate_id(name, validated_email)

        logger.info(
            f"Candidate profile parsed successfully. Name: '{name}', "
            f"ID: {cand_id}, Total Experience: {total_exp} years."
        )

        return Candidate(
            id=cand_id,
            full_name=name or "Candidate Name",
            email=validated_email,
            phone=validated_phone,
            location=contacts["location"],
            linkedin=contacts["linkedin"],
            github=contacts["github"],
            portfolio=contacts["portfolio"],
            summary=summary,
            skills=skills,
            experience=experience,
            education=education,
            projects=projects,
            certifications=certifications,
            languages=languages,
            total_experience_years=total_exp,
            raw_resume_text=cleaned_text,
            metadata=meta
        )
