from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field, EmailStr

class WorkExperience(BaseModel):
    """Pydantic model representing a candidate's work history item."""
    company: Optional[str] = Field(default=None, description="Name of the company/organization")
    role: Optional[str] = Field(default=None, description="Job title / role")
    duration_months: Optional[int] = Field(default=None, description="Duration in months")
    description: Optional[str] = Field(default=None, description="Brief details about responsibilities")


class Education(BaseModel):
    """Pydantic model representing educational history."""
    institution: Optional[str] = Field(default=None, description="Name of school or university")
    degree: Optional[str] = Field(default=None, description="Degree obtained (e.g., BSc, MSc)")
    field_of_study: Optional[str] = Field(default=None, description="Major subject or field")
    graduation_year: Optional[int] = Field(default=None, description="Graduation completion year")


class CandidateProfile(BaseModel):
    """Detailed candidate profile structured from resume parsing."""
    name: Optional[str] = Field(default=None, description="Extracted candidate full name")
    email: Optional[EmailStr] = Field(default=None, description="Extracted candidate email address")
    phone: Optional[str] = Field(default=None, description="Extracted candidate phone number")
    skills: List[str] = Field(default_factory=list, description="Extracted technical and soft skills")
    experience: List[WorkExperience] = Field(default_factory=list, description="Extracted employment history")
    education: List[Education] = Field(default_factory=list, description="Extracted academic background")
    certifications: List[str] = Field(default_factory=list, description="Extracted professional certifications")


class Candidate(BaseModel):
    """Entity representing a resume evaluation file."""
    id: str = Field(description="Unique hash or UUID for candidate tracking")
    filename: str = Field(description="Name of the resume document uploaded")
    file_type: str = Field(description="File format extension (e.g., .pdf, .docx)")
    raw_content: Optional[str] = Field(default=None, description="Raw text parsed from resume")
    profile: Optional[CandidateProfile] = Field(default=None, description="Parsed structured details")
