from datetime import datetime

from pydantic import BaseModel, EmailStr, Field


class WorkExperience(BaseModel):
    """Pydantic model representing structured professional experience."""
    company: str | None = Field(default=None, description="Name of the employing company")
    role: str | None = Field(default=None, description="Job title / role")
    start_date: str | None = Field(default=None, description="Employment start date description")
    end_date: str | None = Field(default=None, description="Employment end date description (or 'Present')")
    current_company: bool = Field(default=False, description="Flag indicating current employment status")
    duration: str | None = Field(default=None, description="Text description of duration")
    responsibilities: str | None = Field(default=None, description="Bullet points of job responsibilities")
    technology_stack: list[str] = Field(default_factory=list, description="Skills or technologies utilized in this role")


class Education(BaseModel):
    """Pydantic model representing structured academic qualifications."""
    degree: str | None = Field(default=None, description="Extracted degree title (e.g. B.Tech, Master)")
    university: str | None = Field(default=None, description="Name of the university")
    college: str | None = Field(default=None, description="Name of the college (if distinct from university)")
    cgpa: float | None = Field(default=None, description="Extracted Cumulative Grade Point Average")
    percentage: float | None = Field(default=None, description="Extracted marks percentage")
    graduation_year: int | None = Field(default=None, description="Academic completion year")


class Project(BaseModel):
    """Pydantic model representing structured candidate projects."""
    project_name: str | None = Field(default=None, description="Title of the project")
    description: str | None = Field(default=None, description="Project summary description")
    technologies_used: list[str] = Field(default_factory=list, description="List of libraries/tools used")
    duration: str | None = Field(default=None, description="Time duration of project")


class Certification(BaseModel):
    """Pydantic model representing structured certifications."""
    certification_name: str | None = Field(default=None, description="Title of certification")
    provider: str | None = Field(default=None, description="Issuing organization")
    issue_date: str | None = Field(default=None, description="Date of issuance")


class CandidateMetadata(BaseModel):
    """Execution metadata logged for file ingestion operations."""
    file_name: str = Field(description="Name of the ingested file")
    file_size: int = Field(description="Size of document in bytes")
    pages: int = Field(description="Page count of document (0 if plain text)")
    parser_used: str = Field(description="Name of parser module utilized")
    processing_time: float = Field(description="Ingestion processing time in seconds")
    extraction_timestamp: datetime = Field(default_factory=datetime.utcnow, description="Datetime when parsing completed")


class Candidate(BaseModel):
    """Fully parsed and validated structured candidate object."""
    id: str = Field(description="Unique hash or UUID for candidate tracking")
    full_name: str | None = Field(default=None, description="Candidate full name")
    email: EmailStr | None = Field(default=None, description="Candidate email address")
    phone: str | None = Field(default=None, description="Candidate phone number")
    location: str | None = Field(default=None, description="Candidate location")
    linkedin: str | None = Field(default=None, description="URL path to LinkedIn profile")
    github: str | None = Field(default=None, description="URL path to GitHub profile")
    portfolio: str | None = Field(default=None, description="URL path to personal portfolio website")
    summary: str | None = Field(default=None, description="Professional candidate overview")
    skills: list[str] = Field(default_factory=list, description="Extracted normalized candidate skills")
    experience: list[WorkExperience] = Field(default_factory=list, description="Chronological professional history")
    education: list[Education] = Field(default_factory=list, description="Structured educational background")
    projects: list[Project] = Field(default_factory=list, description="Personal or professional projects list")
    certifications: list[Certification] = Field(default_factory=list, description="Professional certification credentials")
    languages: list[str] = Field(default_factory=list, description="Languages spoken by candidate")
    total_experience_years: float = Field(default=0.0, description="Calculated overall years of experience")
    raw_resume_text: str = Field(description="Preprocessed sanitized full-text content of the resume")
    metadata: CandidateMetadata = Field(description="Ingestion metadata logs")
