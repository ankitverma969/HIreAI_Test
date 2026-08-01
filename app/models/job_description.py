
from pydantic import BaseModel, Field


class JobDescription(BaseModel):
    """Pydantic model representing a parsed, structured Job Description."""
    id: str = Field(description="Unique identifier for the job posting/description")
    title: str = Field(description="Job title (e.g. Senior Software Engineer)")
    role: str | None = Field(default=None, description="Extracted targeted role designation")
    raw_content: str = Field(description="Sanitized preprocessed full text of the job description")
    required_skills: list[str] = Field(default_factory=list, description="Must-have target technical skills")
    preferred_skills: list[str] = Field(default_factory=list, description="Nice-to-have supplementary skills")
    education_requirements: list[str] = Field(default_factory=list, description="Required degrees or academic fields")
    minimum_experience_years: float | None = Field(default=None, description="Minimum relevant work experience in years")
    responsibilities: list[str] = Field(default_factory=list, description="Responsibilities list or bullets description")
    nice_to_have: list[str] = Field(default_factory=list, description="Preferred nice-to-have qualifications")
    location: str | None = Field(default=None, description="Target job work location / remote designation")
    employment_type: str | None = Field(default=None, description="Employment duration type (e.g. Full-time, Contract)")
    keywords: list[str] = Field(default_factory=list, description="Core extracted semantic keywords")
    soft_skills: list[str] = Field(default_factory=list, description="Targeted soft-skills or domain attributes (e.g., leadership)")
