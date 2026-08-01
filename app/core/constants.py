from pathlib import Path

# Base Paths
BASE_DIR = Path(__file__).resolve().parent.parent.parent
DATA_DIR = BASE_DIR / "data"
OUTPUT_DIR = BASE_DIR / "outputs"

JOB_DESCRIPTIONS_DIR = DATA_DIR / "job_descriptions"
RESUMES_DIR = DATA_DIR / "resumes"

CSV_OUTPUT_DIR = OUTPUT_DIR / "csv"
JSON_OUTPUT_DIR = OUTPUT_DIR / "json"
REPORTS_OUTPUT_DIR = OUTPUT_DIR / "reports"

# Supported Models & Formats
SUPPORTED_FILE_EXTENSIONS = {".pdf", ".docx", ".txt"}

# Default Weight Settings for Resume Scoring
DEFAULT_SKILL_WEIGHT = 0.4
DEFAULT_EXPERIENCE_WEIGHT = 0.3
DEFAULT_EDUCATION_WEIGHT = 0.2
DEFAULT_CERTIFICATION_WEIGHT = 0.1

# API Constants
API_V1_PREFIX = "/api/v1"
HEALTH_CHECK_PATH = "/health"
VERSION_CHECK_PATH = "/version"
