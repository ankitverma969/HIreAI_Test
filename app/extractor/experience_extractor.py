import re

from loguru import logger

from app.extractor.skills_extractor import extract_skills
from app.models.candidate import WorkExperience

# Regex to find date ranges (e.g., "Jan 2020 - Dec 2022", "02/2019 - Present", "2018 - 2020")
DATE_RANGE_REGEX = re.compile(
    r"\b((?:Jan(?:uary)?|Feb(?:ruary)?|Mar(?:ch)?|Apr(?:il)?|May|Jun(?:e)?|Jul(?:y)?|Aug(?:ust)?|Sep(?:tember)?|Oct(?:ober)?|Nov(?:ember)?|Dec(?:ember)?)[a-z.]*[\s.]*\d{4}|\d{1,2}/\d{4}|\d{4})\s*(?:-|–|—|to)\s*((?:Jan(?:uary)?|Feb(?:ruary)?|Mar(?:ch)?|Apr(?:il)?|May|Jun(?:e)?|Jul(?:y)?|Aug(?:ust)?|Sep(?:tember)?|Oct(?:ober)?|Nov(?:ember)?|Dec(?:ember)?)[a-z.]*[\s.]*\d{4}|\d{1,2}/\d{4}|\d{4}|Present|Current|Now)\b",
    re.IGNORECASE,
)

ROLE_KEYWORDS = re.compile(
    r"\b(?:Developer|Engineer|Architect|Manager|Specialist|Analyst|Consultant|Lead|Director|Administrator|Designer|Intern|Officer|Practitioner|Founder|Assistant|Associate)\b",
    re.IGNORECASE,
)

EXPERIENCE_SECTION_HEADERS = re.compile(
    r"(?i)^[#\s-]*(?:work experience|professional experience|experience|employment history|work history|internships?|career history)\s*$"
)

SECTION_BOUNDARY_HEADERS = re.compile(
    r"(?i)^[#\s-]*(?:projects?|personal projects?|key projects?|academic projects?|education|certificates?|certifications?|achievements?|awards?|skills?|technical skills?|summary|professional summary|objective|publications?|research|volunteer(?:ing)?|languages?)\s*$"
)

MONTHS_MAP = {
    "jan": 1,
    "feb": 2,
    "mar": 3,
    "apr": 4,
    "may": 5,
    "jun": 6,
    "jul": 7,
    "aug": 8,
    "sep": 9,
    "oct": 10,
    "nov": 11,
    "dec": 12,
}


def parse_date(date_str: str) -> tuple[int, int]:
    """Parses a date string (month-year or year) into (year, month)."""
    clean_str = date_str.strip().lower()

    if clean_str in ("present", "current", "now"):
        return 2026, 8

    match_slash = re.match(r"(\d{1,2})/(\d{4})", clean_str)
    if match_slash:
        return int(match_slash.group(2)), int(match_slash.group(1))

    match_year = re.match(r"^(\d{4})$", clean_str)
    if match_year:
        return int(match_year.group(1)), 1

    for name, month_num in MONTHS_MAP.items():
        if name in clean_str:
            year_match = re.search(r"(\d{4})", clean_str)
            if year_match:
                return int(year_match.group(1)), month_num

    year_match = re.search(r"(\d{4})", clean_str)
    if year_match:
        return int(year_match.group(1)), 1

    return 2026, 8


def calculate_months_duration(start_str: str, end_str: str) -> int:
    """Calculates difference in months between two date descriptors."""
    start_year, start_month = parse_date(start_str)
    end_year, end_month = parse_date(end_str)
    months = (end_year - start_year) * 12 + (end_month - start_month) + 1
    return max(1, months)


def calculate_total_experience(experiences: list[WorkExperience]) -> float:
    """Calculates overall years of experience based on structured intervals."""
    if not experiences:
        return 0.0

    total_months = 0
    for exp in experiences:
        if exp.start_date and exp.end_date:
            total_months += calculate_months_duration(exp.start_date, exp.end_date)

    return round(total_months / 12.0, 1)


def _clean_heading_text(value: str) -> str:
    value = DATE_RANGE_REGEX.sub("", value)
    value = re.sub(r"^[-*•o\s]+", "", value).strip()
    value = re.sub(r"\s+", " ", value)
    return value.strip(" -|")


def _is_boundary_header(line: str) -> bool:
    return bool(SECTION_BOUNDARY_HEADERS.match(line.strip()))


def _looks_like_position_header(line: str) -> bool:
    clean = _clean_heading_text(line)
    if not clean or len(clean) > 120:
        return False
    if "github" in clean.lower() or clean.lower() == "live":
        return False
    return bool(
        ROLE_KEYWORDS.search(clean)
        or re.search(r"\s+-\s+", clean)
        or re.search(r"\s+(?:at|@)\s+", clean, flags=re.IGNORECASE)
    )


def _extract_experience_section(lines: list[str]) -> list[str]:
    """Returns the work-experience block, falling back to all lines when no header exists."""
    start_idx = None
    for idx, line in enumerate(lines):
        if EXPERIENCE_SECTION_HEADERS.match(line.strip()):
            start_idx = idx + 1
            break

    if start_idx is None:
        return lines

    section_lines = []
    for line in lines[start_idx:]:
        stripped = line.strip()
        if stripped and _is_boundary_header(stripped):
            break
        section_lines.append(line)
    return section_lines


def _parse_company_role(header_line: str, context_text: str) -> tuple[str | None, str | None]:
    clean = _clean_heading_text(header_line)
    company = None
    role = None

    at_match = re.search(
        r"(?P<role>.+?)\s+(?:at|@)\s+(?P<company>[A-Z][A-Za-z0-9 .,&()/-]{2,})$",
        clean,
        re.IGNORECASE,
    )
    if at_match:
        role = at_match.group("role").strip(" -|")
        company = at_match.group("company").strip(" -|")
    elif re.search(r"\s+-\s+", clean):
        left, right = re.split(r"\s+-\s+", clean, maxsplit=1)
        company = left.strip(" -|")
        role = right.strip(" -|")
    elif ROLE_KEYWORDS.search(clean):
        role = clean

    if not role:
        role_match = ROLE_KEYWORDS.search(context_text)
        role = role_match.group(0).strip() if role_match else None

    if not company:
        company_pattern = re.compile(r"\bat\s+([A-Z][a-zA-Z0-9\s&]{2,30})\b")
        comp_match = company_pattern.search(context_text)
        if comp_match:
            company = comp_match.group(1).strip()

    return (
        re.sub(r"\s+", " ", company).strip() if company else None,
        re.sub(r"\s+", " ", role).strip() if role else None,
    )


def _duration_description(start_date: str, end_date: str) -> str:
    months = calculate_months_duration(start_date, end_date)
    years = months // 12
    rem_months = months % 12
    if years > 0:
        return f"{years} yr {rem_months} mos" if rem_months > 0 else f"{years} yr"
    return f"{months} months"


def _collect_responsibilities(lines: list[str], line_idx: int) -> list[str]:
    resp_lines = []
    scan_idx = line_idx + 1
    while scan_idx < len(lines):
        scan_line = lines[scan_idx].strip()
        next_line = lines[scan_idx + 1].strip() if scan_idx + 1 < len(lines) else ""

        if (
            DATE_RANGE_REGEX.search(scan_line)
            or _is_boundary_header(scan_line)
            or (DATE_RANGE_REGEX.search(next_line) and _looks_like_position_header(scan_line))
        ):
            break

        if scan_line.startswith(("-", "*", "•", "o")):
            resp_lines.append(scan_line.lstrip("-*•o ").strip())
        elif resp_lines and len(scan_line) > 10:
            resp_lines.append(scan_line)
        elif len(resp_lines) > 3 or (not scan_line and resp_lines):
            break
        scan_idx += 1
    return resp_lines


def extract_experience(text: str) -> list[WorkExperience]:
    """Scans and parses chronological work history items from candidate text."""
    logger.debug("Running experience timeline extractor...")
    experience_list: list[WorkExperience] = []

    if not text:
        return experience_list

    lines = _extract_experience_section(text.splitlines())

    for line_idx, line in enumerate(lines):
        match = DATE_RANGE_REGEX.search(line)
        if not match:
            continue

        start_date_str = match.group(1).strip()
        end_date_str = match.group(2).strip()
        current_company = end_date_str.lower() in ("present", "current", "now")

        start_idx = max(0, line_idx - 1)
        end_idx = min(len(lines), line_idx + 5)
        context_lines = lines[start_idx:end_idx]
        context_text = " \n ".join(context_lines)

        preceding_line = lines[max(0, line_idx - 1)]
        header_line = preceding_line if _looks_like_position_header(preceding_line) else line
        company, role = _parse_company_role(header_line, context_text)

        responsibilities = _collect_responsibilities(lines, line_idx)
        responsibility_text = "\n".join(responsibilities) if responsibilities else None
        tech_context = f"{context_text}\n{responsibility_text or ''}"

        exp_item = WorkExperience(
            company=company or "Company details",
            role=role or "Professional Role",
            start_date=start_date_str,
            end_date=end_date_str,
            current_company=current_company,
            duration=_duration_description(start_date_str, end_date_str),
            responsibilities=responsibility_text,
            technology_stack=extract_skills(tech_context),
        )

        if not any(e.start_date == exp_item.start_date and e.company == exp_item.company for e in experience_list):
            experience_list.append(exp_item)

    logger.debug(f"Experience extraction completed. Found {len(experience_list)} periods.")
    return experience_list
