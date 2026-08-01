import re

from loguru import logger

from app.extractor.education_extractor import DEGREE_PATTERNS
from app.extractor.skills_extractor import extract_skills
from app.models.job_description import JobDescription

# Keywords representing soft skills
SOFT_SKILLS_DATABASE = [
    "communication", "leadership", "collaboration", "teamwork", "problem solving",
    "critical thinking", "adaptability", "creativity", "work ethic", "interpersonal",
    "time management", "conflict resolution", "negotiation", "mentoring"
]

EMPLOYMENT_TYPES = ["Full-time", "Part-time", "Contract", "Internship", "Temporary", "Freelance"]

def extract_jd_title(text: str) -> str:
    """Extracts job role/title from the top lines of text.

    Args:
        text: Sanitized job description text.

    Returns:
        Job title string, defaults to 'Software Engineer' if not matched.
    """
    lines = text.splitlines()
    for line in lines[:5]:
        clean = line.strip()
        if not clean:
            continue

        # Match explicit headers
        match_pref = re.search(r"(?i)^(?:job\s+)?title\s*:\s*(.+)$", clean)
        if match_pref:
            return match_pref.group(1).strip()

        match_role = re.search(r"(?i)^role\s*:\s*(.+)$", clean)
        if match_role:
            return match_role.group(1).strip()

        # Default fallback to first non-empty short line (if looks like a title)
        if 5 < len(clean) < 60 and not re.search(r"\b(?:we|are|looking|for|company|description)\b", clean, re.IGNORECASE):
            return clean

    return "Software Engineer"


def extract_jd_experience(text: str) -> float | None:
    """Extracts minimum years of experience required.

    Args:
        text: Sanitized job description text.

    Returns:
        Experience years required (or None).
    """
    pattern = re.compile(
        r"\b(?:minimum|at\s+least|required|have|need)\s*(?:of)?\s*(\d+(?:\.\d+)?)\+?\s*(?:years|yrs)\b",
        re.IGNORECASE
    )
    match = pattern.search(text)
    if match:
        try:
            return float(match.group(1))
        except ValueError:
            pass

    # Fallback to simple numbers before "years of experience"
    fallback = re.search(r"\b(\d+)\+?\s*(?:years|yrs)\s+(?:of\s+)?experience\b", text, re.IGNORECASE)
    if fallback:
        try:
            return float(fallback.group(1))
        except ValueError:
            pass

    return None


def extract_jd_soft_skills(text: str) -> list[str]:
    """Matches common soft skills inside description text.

    Args:
        text: Sanitized job description text.

    Returns:
        List of matched soft skills.
    """
    found = []
    text_lower = text.lower()
    for skill in SOFT_SKILLS_DATABASE:
        pattern = rf"\b{re.escape(skill)}\b"
        if re.search(pattern, text_lower):
            found.append(skill.title())
    return found


def extract_jd_sections(text: str) -> dict[str, list[str]]:
    """Splits job description text into logical lists of lines by section headers.

    Args:
        text: Sanitized job description text.

    Returns:
        Dictionary mapping section names to lists of string lines.
    """
    lines = text.splitlines()
    sections: dict[str, list[str]] = {
        "requirements": [],
        "preferences": [],
        "responsibilities": []
    }

    current_section = None

    for line in lines:
        line_strip = line.strip()
        if not line_strip:
            continue

        # Match header indicators
        if re.search(r"(?i)^[#\s-]*(?:requirements|what\s+you\s+need|qualifications|required\s+skills|skills\s+required)\s*$", line_strip):
            current_section = "requirements"
            continue
        elif re.search(r"(?i)^[#\s-]*(?:preferred\s+qualifications|preferred\s+skills|preferred|nice\s+to\s+have|pluses|plus)\s*$", line_strip):
            current_section = "preferences"
            continue
        elif re.search(r"(?i)^[#\s-]*(?:responsibilities|what\s+you\s+will\s+do|duties|role\s+description|key\s+responsibilities)\s*$", line_strip):
            current_section = "responsibilities"
            continue
        elif re.match(r"(?i)^[A-Z\s]{4,20}$", line_strip):
            # Hit another generic uppercase header, reset
            current_section = None

        if current_section and not line_strip.startswith("#"):
            sections[current_section].append(line_strip)

    return sections


class JobDescriptionExtractor:
    """Extractor class structuring unstructured job description text."""

    @staticmethod
    def extract_job_description(
        jd_id: str,
        text_content: str
    ) -> JobDescription:
        """Parses and structures job description contents.

        Args:
            jd_id: Job posting ID.
            text_content: Sanitized preprocessed document text.

        Returns:
            JobDescription model.
        """
        logger.info(f"Triggering Job Description extraction for ID '{jd_id}'")

        title = extract_jd_title(text_content)
        min_years = extract_jd_experience(text_content)
        soft_skills = extract_jd_soft_skills(text_content)

        # 1. Employment Type lookup
        employment_type = None
        text_lower = text_content.lower()
        for et in EMPLOYMENT_TYPES:
            if rf"\b{et.lower()}\b" in text_lower:
                employment_type = et
                break

        # 2. Location lookup
        location = "Onsite"
        if "remote" in text_lower:
            location = "Remote"
        elif "hybrid" in text_lower:
            location = "Hybrid"
        else:
            loc_match = re.search(r"(?i)(?:location|office|based in)\s*:\s*([a-zA-Z\s,]{2,30})\b", text_content)
            if loc_match:
                location = loc_match.group(1).strip()

        # 3. Education Requirements lookup
        edu_reqs = []
        for pattern, canonical_degree in DEGREE_PATTERNS:
            if re.search(pattern, text_content):
                edu_reqs.append(canonical_degree)

        # 4. Segment sections
        sections = extract_jd_sections(text_content)

        # Extract skills per section
        req_skills = []
        pref_skills = []

        if sections["requirements"]:
            req_skills = extract_skills("\n".join(sections["requirements"]))
        if sections["preferences"]:
            pref_skills = extract_skills("\n".join(sections["preferences"]))

        # Fallback: if no section division found, match all skills to required
        all_detected_skills = extract_skills(text_content)
        if not req_skills:
            req_skills = all_detected_skills

        # 5. Clean lists of responsibilities
        resp_bullets = []
        for line in sections["responsibilities"]:
            clean = re.sub(r"^[-*•o\s]+", "", line).strip()
            if len(clean) > 10:
                resp_bullets.append(clean)

        nice_to_have = []
        for line in sections["preferences"]:
            clean = re.sub(r"^[-*•o\s]+", "", line).strip()
            if len(clean) > 10:
                nice_to_have.append(clean)

        # Compile keywords
        keywords = sorted(list(set(req_skills + pref_skills + edu_reqs)))

        logger.info(f"JD parsed successfully. Title: '{title}', Min Experience: {min_years} years.")

        return JobDescription(
            id=jd_id,
            title=title,
            role=title,
            raw_content=text_content,
            required_skills=req_skills,
            preferred_skills=pref_skills,
            education_requirements=edu_reqs,
            minimum_experience_years=min_years,
            responsibilities=resp_bullets,
            nice_to_have=nice_to_have,
            location=location,
            employment_type=employment_type or "Full-time",
            keywords=keywords,
            soft_skills=soft_skills
        )
