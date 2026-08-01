from typing import List, Optional
from pydantic import BaseModel, Field

class JobDescription(BaseModel):
    """Pydantic model representing a parsed or inputted Job Description."""
    id: str = Field(description="Unique identifier for the job posting/description")
    title: str = Field(description="Job title (e.g. Senior Software Engineer)")
    raw_content: str = Field(description="Raw unstructured text of the job description")
    required_skills: List[str] = Field(default_factory=list, description="Must-have target skills")
    preferred_skills: List[str] = Field(default_factory=list, description="Nice-to-have supplementary skills")
    minimum_experience_years: Optional[float] = Field(default=None, description="Minimum relevant work experience in years")
    education_requirements: List[str] = Field(default_factory=list, description="Required degrees or fields")
