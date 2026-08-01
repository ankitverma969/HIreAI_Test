from typing import Annotated, TypedDict

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

    # Processed states
    job_description: JobDescription | None
    candidates: list[Candidate]

    # Embedding values
    jd_embedding: list[float] | None
    candidate_embeddings: dict[str, list[float]]

    # Scored results
    scores: dict[str, Score]
    rankings: list[Ranking]
    report: Report | None

    # Reducer accumulator for execution issues
    errors: Annotated[list[str], merge_errors]
