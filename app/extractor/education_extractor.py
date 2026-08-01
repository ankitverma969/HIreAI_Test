import re

from loguru import logger

from app.models.candidate import Education

DEGREE_PATTERNS = [
    (r"(?i)\bph\.?d\b|\bdoctor\s+of\s+philosophy\b", "Ph.D."),
    (r"(?i)\bm\.?tech\b|\bm\.?e\b|\bmaster\s+of\s+technology\b|\bmaster\s+of\s+engineering\b", "M.Tech"),
    (r"(?i)\bm\.?s\.?\b|\bm\.?sc\b|\bmaster\s+of\s+science\b", "M.S."),
    (r"(?i)\bm\.?b\.?a\b|\bmaster\s+of\s+business\s+administration\b", "MBA"),
    (r"(?i)\bb\.?tech\b|\bb\.?e\b|\bbachelor\s+of\s+technology\b|\bbachelor\s+of\s+engineering\b", "B.Tech"),
    (r"(?i)\bb\.?s\.?\b|\bb\.?sc\b|\bbachelor\s+of\s+science\b", "B.S."),
    (r"(?i)\bb\.?a\b|\bbachelor\s+of\s+arts\b", "B.A."),
    (r"(?i)\bb\.?b\.?a\b|\bbachelor\s+of\s+business\s+administration\b", "B.B.A."),
    (r"(?i)\bdiploma\b|\bassociate\b", "Diploma"),
]

# Patterns to scan surrounding text
YEAR_REGEX = re.compile(r"\b(19\d{2}|20[0-2]\d)\b")
CGPA_REGEX = re.compile(r"\b([0-9]\.[0-9]{1,2})\s*(?:/\s*10)?\s*(?:cgpa|gpa)?\b", re.IGNORECASE)
PERCENTAGE_REGEX = re.compile(r"\b(\d{2}(?:\.\d{1,2})?)\s*%\b")
INSTITUTION_REGEX = re.compile(
    r"\b[A-Za-z0-9\s&]+(?:University|College|Institute|Academy|School|IIT|NIT|IIIT|BITS|Polytechnic)\b",
    re.IGNORECASE
)

def extract_education(text: str) -> list[Education]:
    """Extracts structured academic items from the text.

    Args:
        text: Sanitized preprocessed document text.

    Returns:
        List of structured Education models.
    """
    logger.debug("Running education extractor...")
    education_list: list[Education] = []

    if not text:
        return education_list

    lines = text.splitlines()

    # Track which lines we process to prevent duplicates

    # Iterate through text lines searching for degree keywords
    for line_idx, line in enumerate(lines):
        for pattern, canonical_degree in DEGREE_PATTERNS:
            match = re.search(pattern, line)
            if match:
                # Degree found! Grab context from line and 2 lines above/below
                context_lines = []
                start = max(0, line_idx - 2)
                end = min(len(lines), line_idx + 3)

                for idx in range(start, end):
                    context_lines.append(lines[idx])

                context_text = " \n ".join(context_lines)

                # Extract year
                year_match = YEAR_REGEX.search(context_text)
                grad_year = int(year_match.group(1)) if year_match else None

                # Extract CGPA
                cgpa_match = CGPA_REGEX.search(context_text)
                cgpa: float | None = None
                if cgpa_match:
                    try:
                        cgpa = float(cgpa_match.group(1))
                        # Limit to logical 10.0 scale if it matches standard CGPA pattern
                        if cgpa > 10.0:
                            cgpa = None
                    except ValueError:
                        pass

                # Extract Percentage
                pct_match = PERCENTAGE_REGEX.search(context_text)
                percentage: float | None = None
                if pct_match:
                    try:
                        percentage = float(pct_match.group(1))
                    except ValueError:
                        pass

                # Extract University/College
                inst_match = INSTITUTION_REGEX.search(context_text)
                institution = inst_match.group(0).strip() if inst_match else None

                # Parse distinction between College and University
                university = None
                college = None

                if institution:
                    if "university" in institution.lower():
                        university = institution
                    else:
                        college = institution

                # Create structured model
                edu_item = Education(
                    degree=canonical_degree,
                    university=university,
                    college=college,
                    cgpa=cgpa,
                    percentage=percentage,
                    graduation_year=grad_year
                )

                # Deduplicate very similar items
                if not any(e.degree == edu_item.degree and e.university == edu_item.university for e in education_list):
                    education_list.append(edu_item)

                break  # Matched one degree type for this line, move to next line

    # Fallback search if no degrees matched but a university was mentioned
    if not education_list:
        inst_matches = INSTITUTION_REGEX.findall(text)
        for inst in inst_matches:
            inst_clean = inst.strip()
            # Avoid repeating
            if not any(e.university == inst_clean or e.college == inst_clean for e in education_list):
                edu_item = Education(
                    degree="Degree / Certificate",
                    university=inst_clean if "university" in inst_clean.lower() else None,
                    college=inst_clean if "university" not in inst_clean.lower() else None
                )
                education_list.append(edu_item)
                if len(education_list) >= 2:  # Cap fallback items
                    break

    logger.debug(f"Education extraction completed. Found {len(education_list)} items.")
    return education_list
