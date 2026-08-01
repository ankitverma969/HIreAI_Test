from typing import Annotated, Any, TypedDict

from app.models.candidate import Candidate
from app.models.job_description import JobDescription
from app.models.report import Report
from app.models.score import Ranking, Score


def merge_errors(left: list[str], right: list[str]) -> list[str]:
    """Helper reducer function to aggregate processing errors."""
    return left + right


class AgentState(TypedDict):
    """Workflow state schema traversed by LangGraph nodes."""
    job_description_path: str | None
    resumes_paths: list[str]

    # Raw content inputs (if reading from text)
    job_description_raw: str | None
    candidates_input: list[Candidate]

    # Processed entity structures
    job_description: JobDescription | None
    candidates: list[Candidate]

    # Embeddings results maps (ID -> List[float])
    jd_embedding: list[float] | None
    candidate_embeddings: dict[str, list[float]]  # raw text embeddings
    candidate_experience_embeddings: dict[str, list[float]]
    candidate_project_embeddings: dict[str, list[float]]
    candidate_education_embeddings: dict[str, list[float]]

    # Evaluations and structured scores
    scores: dict[str, Score]
    llm_analysis: dict[str, dict[str, Any]]  # ID -> dict representing structured analysis
    recommendations: dict[str, str]  # ID -> recommendation decision (Strong Hire, etc.)
    rankings: list[Ranking]
    report: Report | None

    # Operational execution logs
    metadata: dict[str, Any]
    timing: dict[str, float]  # NodeName -> execution duration in seconds
    errors: Annotated[list[str], merge_errors]
    export_paths: dict[str, str]
