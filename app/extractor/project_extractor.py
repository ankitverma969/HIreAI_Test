import re

from loguru import logger

from app.extractor.skills_extractor import extract_skills
from app.models.candidate import Project

# Regex to find project blocks or bullet markers
PROJECT_MARKER = re.compile(r"(?i)\b(?:project|portfolio)\b")
PROJECT_DATE_REGEX = re.compile(r"\b((?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z.]*[\s.]*\d{4}|\d{4})\b", re.IGNORECASE)

def extract_projects(text: str) -> list[Project]:
    """Scans and extracts structured personal or academic projects from text.

    Args:
        text: Sanitized preprocessed document text.

    Returns:
        List of structured Project models.
    """
    logger.debug("Running project details extractor...")
    projects_list: list[Project] = []

    if not text:
        return projects_list

    lines = text.splitlines()
    in_project_section = False
    project_lines: list[str] = []

    # Identify project section block
    for line in lines:
        line_strip = line.strip()
        if not line_strip:
            continue

        # Detect if we hit the Projects section header
        if re.search(r"(?i)^[#\s-]*(?:projects|personal projects|key projects|academic projects|notable projects)\s*$", line_strip):
            in_project_section = True
            continue
        elif in_project_section and re.match(r"(?i)^[A-Z\s]{4,20}$", line_strip) and "project" not in line_strip.lower():
            # Stop if we hit a new uppercase section (e.g. EXPERIENCE, EDUCATION)
            in_project_section = False

        if in_project_section:
            project_lines.append(line_strip)

    # If no explicit project section was found, search for project keyword lines
    if not project_lines:
        for idx, line in enumerate(lines):
            if PROJECT_MARKER.search(line) and len(line) < 60:
                # Grab a few surrounding lines as project context
                start = idx
                end = min(len(lines), idx + 4)
                project_lines.extend(lines[start:end])
                if len(project_lines) > 15:  # Cap details
                    break

    # Parse project blocks from collected lines
    current_proj_name = None
    current_desc: list[str] = []
    current_tech: list[str] = []
    current_duration = None

    for line in project_lines:
        # Check if line looks like a project title/header (bullet point or start of a block)
        # E.g. "o Resume Screener - Jan 2026", "Portfolio App: built..."
        is_title = False
        duration_match = PROJECT_DATE_REGEX.search(line)
        duration = duration_match.group(0) if duration_match else None

        # Strip markers
        clean_line = re.sub(r"^[-*•o\s]+", "", line).strip()

        if (len(clean_line) < 50 and any(kw in clean_line.lower() for kw in ("project", "system", "app", "application", "tool", "website", "portal", "bot"))) or clean_line.endswith(":") or (duration and len(clean_line) < 80):
            is_title = True

        if is_title:
            # Save previous project if any
            if current_proj_name:
                projects_list.append(Project(
                    project_name=current_proj_name,
                    description=" ".join(current_desc) if current_desc else "Project details",
                    technologies_used=current_tech,
                    duration=current_duration
                ))
            # Reset trackers
            current_proj_name = clean_line.split("-")[0].split(":")[0].strip()
            current_proj_name = re.sub(r"\s*\([^)]*\)", "", current_proj_name).strip()
            current_desc = []
            current_tech = extract_skills(line)
            current_duration = duration
        else:
            if current_proj_name:
                current_desc.append(clean_line)
                # Accumulate tech stack
                current_tech.extend(extract_skills(line))

    # Append the last project
    if current_proj_name:
        # Remove duplicates from list
        current_tech = sorted(list(set(current_tech)))
        projects_list.append(Project(
            project_name=current_proj_name,
            description=" ".join(current_desc) if current_desc else "Project details",
            technologies_used=current_tech,
            duration=current_duration
        ))

    logger.debug(f"Project extraction completed. Found {len(projects_list)} projects.")
    return projects_list
