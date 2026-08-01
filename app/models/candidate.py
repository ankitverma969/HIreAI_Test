from pydantic import BaseModel, EmailStr, Field


class WorkExperience(BaseModel):
    """Pydantic model representing a candidate's work history item."""

    company: str | None = Field(
        default=None, description="Name of the company/organization"
    )
    role: str | None = Field(default=None, description="Job title / role")
    duration_months: int | None = Field(default=None, description="Duration in months")
    description: str | None = Field(
        default=None, description="Brief details about responsibilities"
    )


class Education(BaseModel):
    """Pydantic model representing educational history."""

    institution: str | None = Field(
        default=None, description="Name of school or university"
    )
    degree: str | None = Field(
        default=None, description="Degree obtained (e.g., BSc, MSc)"
    )
    field_of_study: str | None = Field(
        default=None, description="Major subject or field"
    )
    graduation_year: int | None = Field(
        default=None, description="Graduation completion year"
    )


class CandidateProfile(BaseModel):
    """Detailed candidate profile structured from resume parsing."""

    name: str | None = Field(default=None, description="Extracted candidate full name")
    email: EmailStr | None = Field(
        default=None, description="Extracted candidate email address"
    )
    phone: str | None = Field(
        default=None, description="Extracted candidate phone number"
    )
    skills: list[str] = Field(
        default_factory=list, description="Extracted technical and soft skills"
    )
    experience: list[WorkExperience] = Field(
        default_factory=list, description="Extracted employment history"
    )
    education: list[Education] = Field(
        default_factory=list, description="Extracted academic background"
    )
    certifications: list[str] = Field(
        default_factory=list, description="Extracted professional certifications"
    )


class Candidate(BaseModel):
    """Entity representing a resume evaluation file."""

    id: str = Field(description="Unique hash or UUID for candidate tracking")
    filename: str = Field(description="Name of the resume document uploaded")
    file_type: str = Field(description="File format extension (e.g., .pdf, .docx)")
    raw_content: str | None = Field(
        default=None, description="Raw text parsed from resume"
    )
    profile: CandidateProfile | None = Field(
        default=None, description="Parsed structured details"
    )
