from typing import TypedDict, List, Dict, Optional, Annotated
import operator
from app.models.job_description import JobDescription
from app.models.candidate import Candidate
from app.models.score import Score, Ranking
from app.models.report import Report

def merge_errors(left: List[str], right: List[str]) -> List[str]:
    """Helper reducer function to aggregate processing errors."""
    return left + right


class AgentState(TypedDict):
    """Workflow state schema traversed by LangGraph nodes."""
    job_description_path: Optional[str]
    resumes_paths: List[str]
    
    # Processed states
    job_description: Optional[JobDescription]
    candidates: List[Candidate]
    
    # Embedding values
    jd_embedding: Optional[List[float]]
    candidate_embeddings: Dict[str, List[float]]
    
    # Scored results
    scores: Dict[str, Score]
    rankings: List[Ranking]
    report: Optional[Report]
    
    # Reducer accumulator for execution issues
    errors: Annotated[List[str], merge_errors]
