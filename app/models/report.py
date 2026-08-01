from datetime import datetime

from pydantic import BaseModel, Field

from app.models.score import Ranking


class Report(BaseModel):
    """Aggregate evaluation report listing overall matching outcomes."""

    job_description_id: str = Field(
        description="ID of the job description used for analysis"
    )
    job_title: str = Field(description="Title of job evaluated")
    evaluation_timestamp: datetime = Field(
        default_factory=datetime.utcnow,
        description="UTC time when processing completed",
    )
    rankings: list[Ranking] = Field(
        default_factory=list, description="Sorted list of candidates from best to worst"
    )
    exported_files: dict[str, str] = Field(
        default_factory=dict,
        description="Mapping of report export formats to generated file paths",
    )
