from pydantic import BaseModel, Field, field_validator


class ScoreBreakdown(BaseModel):
    """Component level scores out of 100 representing match percentages."""
    skill_match: float = Field(default=0.0, description="Skill similarity match percentage (0.0 to 100.0)")
    keyword_match: float = Field(default=0.0, description="Keyword overlap match percentage (0.0 to 100.0)")
    experience_match: float = Field(default=0.0, description="Experience alignment match percentage (0.0 to 100.0)")
    project_match: float = Field(default=0.0, description="Project alignment match percentage (0.0 to 100.0)")
    education_match: float = Field(default=0.0, description="Education requirements match percentage (0.0 to 100.0)")
    certification_match: float = Field(default=0.0, description="Certification credentials match percentage (0.0 to 100.0)")
    semantic_similarity: float = Field(default=0.0, description="Overall semantic cosine similarity (0.0 to 100.0)")

    @field_validator(
        "skill_match", "keyword_match", "experience_match", "project_match",
        "education_match", "certification_match", "semantic_similarity"
    )
    @classmethod
    def validate_score_range(cls, val: float) -> float:
        if not (0.0 <= val <= 100.0):
            raise ValueError("Score components must be between 0.0 and 100.0")
        return val


class Score(BaseModel):
    """Aggregate candidate match score metrics."""
    overall_score: float = Field(default=0.0, description="Weighted average score (0.0 to 100.0)")
    breakdown: ScoreBreakdown = Field(default_factory=ScoreBreakdown)
    confidence_score: float = Field(default=0.0, description="Score calculation confidence index (0.0 to 100.0)")
    reasoning: str = Field(default="", description="Detailed qualitative reasoning explaining score decisions")
    matched_skills: list[str] = Field(default_factory=list, description="Candidate skills matching job requirements")
    missing_skills: list[str] = Field(default_factory=list, description="Job requirements not found on candidate profile")

    @field_validator("overall_score", "confidence_score")
    @classmethod
    def validate_overall_score(cls, val: float) -> float:
        if not (0.0 <= val <= 100.0):
            raise ValueError("Scores must be between 0.0 and 100.0")
        return val


class Ranking(BaseModel):
    """Ranked item linking scoring evaluation with candidate meta."""
    candidate_id: str = Field(description="Foreign key ID link to the Candidate profile")
    candidate_name: str = Field(description="Name of the candidate evaluated")
    rank: int = Field(description="Ordinal ranking assignment (e.g. 1, 2, 3)")
    score: Score = Field(description="Calculated score schema")
