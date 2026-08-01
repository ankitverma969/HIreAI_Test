import re

from loguru import logger

from app.extractor.skills_extractor import extract_skills
from app.models.candidate import WorkExperience

# Regex to find date ranges (e.g., "Jan 2020 - Dec 2022", "02/2019 - Present", "2018 - 2020")
DATE_RANGE_REGEX = re.compile(
    r"\b((?:Jan(?:uary)?|Feb(?:ruary)?|Mar(?:ch)?|Apr(?:il)?|May|Jun(?:e)?|Jul(?:y)?|Aug(?:ust)?|Sep(?:tember)?|Oct(?:ober)?|Nov(?:ember)?|Dec(?:ember)?)[a-z.]*[\s.]*\d{4}|\d{1,2}/\d{4}|\d{4})\s*(?:-|–|to)\s*((?:Jan(?:uary)?|Feb(?:ruary)?|Mar(?:ch)?|Apr(?:il)?|May|Jun(?:e)?|Jul(?:y)?|Aug(?:ust)?|Sep(?:tember)?|Oct(?:ober)?|Nov(?:ember)?|Dec(?:ember)?)[a-z.]*[\s.]*\d{4}|\d{1,2}/\d{4}|\d{4}|Present|Current|Now)\b",
    re.IGNORECASE
)

# Common title words to identify roles
ROLE_KEYWORDS = re.compile(
    r"\b(?:Developer|Engineer|Architect|Manager|Specialist|Analyst|Consultant|Lead|Director|Administrator|Designer|Intern|Officer|Practitioner)\b",
    re.IGNORECASE
)

# Months lookup for parsing
MONTHS_MAP = {
    "jan": 1, "feb": 2, "mar": 3, "apr": 4, "may": 5, "jun": 6,
    "jul": 7, "aug": 8, "sep": 9, "oct": 10, "nov": 11, "dec": 12
}

def parse_date(date_str: str) -> tuple[int, int]:
    """Parses a date string (month-year or year) into (year, month).

    Args:
        date_str: The date text.

    Returns:
        Tuple of (year, month).
    """
    clean_str = date_str.strip().lower()

    # Check for "Present" reference (defaulting to August 2026 as local time metadata states 2026-08-01)
    if clean_str in ("present", "current", "now"):
        return 2026, 8

    # Match MM/YYYY
    match_slash = re.match(r"(\d{1,2})/(\d{4})", clean_str)
    if match_slash:
        return int(match_slash.group(2)), int(match_slash.group(1))

    # Match YYYY only
    match_year = re.match(r"^(\d{4})$", clean_str)
    if match_year:
        return int(match_year.group(1)), 1

    # Match Month Name YYYY
    for name, month_num in MONTHS_MAP.items():
        if name in clean_str:
            year_match = re.search(r"(\d{4})", clean_str)
            if year_match:
                return int(year_match.group(1)), month_num

    # Fallback default
    year_match = re.search(r"(\d{4})", clean_str)
    if year_match:
        return int(year_match.group(1)), 1

    return 2026, 8


def calculate_months_duration(start_str: str, end_str: str) -> int:
    """Calculates difference in months between two date descriptors.

    Args:
        start_str: Start date.
        end_str: End date.

    Returns:
        Number of months.
    """
    start_year, start_month = parse_date(start_str)
    end_year, end_month = parse_date(end_str)
    months = (end_year - start_year) * 12 + (end_month - start_month) + 1
    return max(1, months)  # Minimum 1 month


def calculate_total_experience(experiences: list[WorkExperience]) -> float:
    """Calculates overall years of experience based on structured intervals.

    Args:
        experiences: List of work experience models.

    Returns:
        Total years of experience as float rounded to 1 decimal place.
    """
    if not experiences:
        return 0.0

    total_months = 0
    # In simple aggregation, we sum durations. Future phases can de-duplicate overlapping spans
    for exp in experiences:
        if exp.start_date and exp.end_date:
            total_months += calculate_months_duration(exp.start_date, exp.end_date)

    years = total_months / 12.0
    return round(years, 1)


def extract_experience(text: str) -> list[WorkExperience]:
    """Scans and parses chronological work history items from candidate text.

    Args:
        text: Sanitized preprocessed document text.

    Returns:
        List of structured WorkExperience models.
    """
    logger.debug("Running experience timeline extractor...")
    experience_list: list[WorkExperience] = []

    if not text:
        return experience_list

    lines = text.splitlines()

    # Search dates ranges
    for line_idx, line in enumerate(lines):
        match = DATE_RANGE_REGEX.search(line)
        if match:
            start_date_str = match.group(1).strip()
            end_date_str = match.group(2).strip()

            current_company = end_date_str.lower() in ("present", "current", "now")

            # Estimate months
            months = calculate_months_duration(start_date_str, end_date_str)
            years = months // 12
            rem_months = months % 12

            duration_desc = f"{months} months"
            if years > 0:
                duration_desc = f"{years} yr {rem_months} mos" if rem_months > 0 else f"{years} yr"

            # Scan context around date match (usually 1 line above and 4 lines below)
            start_idx = max(0, line_idx - 1)
            end_idx = min(len(lines), line_idx + 5)
            context_lines = lines[start_idx:end_idx]
            context_text = " \n ".join(context_lines)

            # Find role / job title
            role_match = ROLE_KEYWORDS.search(context_text)
            role = role_match.group(0).strip() if role_match else None

            # If role not found in immediate context, check same line
            if not role:
                same_line_role = ROLE_KEYWORDS.search(line)
                if same_line_role:
                    role = same_line_role.group(0).strip()

            # Guess Company: Search for uppercase entity names in line or preceding line
            # Common pattern: "Role at Company" or "Company - Role"
            company = None
            company_pattern = re.compile(r"\bat\s+([A-Z][a-zA-Z0-9\s&]{2,30})\b")

            preceding_line = lines[max(0, line_idx - 1)]
            comp_match = company_pattern.search(preceding_line)
            if not comp_match:
                comp_match = company_pattern.search(line)

            if comp_match:
                company = comp_match.group(1).strip()
            else:
                # Fallback: scan context line for capitalized word sequence excluding role
                for cl in [lines[max(0, line_idx-1)], line]:
                    cl_clean = re.sub(r"(?i)\bat\b", "", cl)
                    words = re.findall(r"\b([A-Z][A-Za-z0-9&]{2,30})\b", cl_clean)
                    filtered_words = [w for w in words if w.lower() not in ("present", "current", "education", "experience")]
                    if role:
                        role_words = role.split()
                        filtered_words = [w for w in filtered_words if w not in role_words]
                    if filtered_words:
                        company = " ".join(filtered_words[:2])
                        break

            # Get responsibilities (lines starting with bullet points below date range line)
            resp_lines = []
            scan_idx = line_idx + 1
            while scan_idx < len(lines):
                scan_line = lines[scan_idx].strip()
                # Stop if we hit a new date range or new section header
                if DATE_RANGE_REGEX.search(scan_line) or re.match(r"(?i)^[A-Z\s]{4,20}$", scan_line):
                    break
                if scan_line.startswith(("-", "*", "•", "o")):
                    resp_lines.append(scan_line.lstrip("-*•o ").strip())
                elif len(resp_lines) > 0 and len(scan_line) > 10:
                    # Append description lines
                    resp_lines.append(scan_line)
                elif len(resp_lines) > 3 or (len(scan_line) == 0 and len(resp_lines) > 0):
                    break
                scan_idx += 1

            responsibilities = "\n".join(resp_lines) if resp_lines else None

            # Extract technologies used in context
            tech_stack = extract_skills(context_text)

            # Create model
            exp_item = WorkExperience(
                company=company or "Company details",
                role=role or "Professional Role",
                start_date=start_date_str,
                end_date=end_date_str,
                current_company=current_company,
                duration=duration_desc,
                responsibilities=responsibilities,
                technology_stack=tech_stack
            )

            # Deduplicate by dates
            if not any(e.start_date == exp_item.start_date and e.company == exp_item.company for e in experience_list):
                experience_list.append(exp_item)

    logger.debug(f"Experience extraction completed. Found {len(experience_list)} periods.")
    return experience_list
