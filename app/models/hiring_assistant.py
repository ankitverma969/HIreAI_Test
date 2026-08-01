from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field, field_validator


class ComparisonRequest(BaseModel):
    """Request payload for comparing two or three ranked candidates."""

    candidate_ids: list[str] = Field(
        min_length=2,
        max_length=3,
        description="Candidate IDs selected for side-by-side comparison.",
    )

    @field_validator("candidate_ids")
    @classmethod
    def validate_unique_ids(cls, value: list[str]) -> list[str]:
        if len(set(value)) != len(value):
            raise ValueError("Candidate IDs must be unique")
        return value


class CandidateComparisonItem(BaseModel):
    """Flattened candidate metrics used by tables and charts."""

    candidate_id: str
    candidate_name: str
    rank: int | None = None
    recommendation: str
    overall_score: float
    skill_match: float
    experience_match: float
    education_match: float
    project_match: float
    certification_match: float
    semantic_similarity: float
    confidence_score: float
    total_experience_years: float
    matched_skills: list[str] = Field(default_factory=list)
    missing_skills: list[str] = Field(default_factory=list)
    strengths: list[str] = Field(default_factory=list)
    weaknesses: list[str] = Field(default_factory=list)


class ComparisonHighlights(BaseModel):
    """Named winners for key recruiter comparison dimensions."""

    best_candidate_id: str | None = None
    best_candidate_name: str | None = None
    most_experienced_id: str | None = None
    most_experienced_name: str | None = None
    highest_skill_match_id: str | None = None
    highest_skill_match_name: str | None = None
    most_complete_resume_id: str | None = None
    most_complete_resume_name: str | None = None


class AIComparisonSummary(BaseModel):
    """Structured executive comparison returned by the LLM layer."""

    executive_comparison: str
    why_ranked_higher: str
    strength_comparison: str
    risk_comparison: str
    interview_recommendation: str
    hiring_recommendation: str


class CandidateComparisonResponse(BaseModel):
    """Complete comparison payload for the frontend."""

    candidates: list[CandidateComparisonItem]
    highlights: ComparisonHighlights
    ai_summary: AIComparisonSummary
    chart_data: dict[str, Any] = Field(default_factory=dict)


class ChatRequest(BaseModel):
    """Question payload for the AI recruiter chat."""

    question: str = Field(min_length=1, description="Recruiter question.")
    session_id: str = Field(default="default", description="In-memory chat session ID.")


class ChatMessage(BaseModel):
    """Single chat turn persisted for the active browser session."""

    role: str
    content: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    metadata: dict[str, Any] = Field(default_factory=dict)


class ChatAnswer(BaseModel):
    """Structured response produced by the recruiter chat graph."""

    answer_markdown: str
    direct_answer: str
    unavailable: bool = False
    confidence: float = Field(default=0.0, ge=0.0, le=100.0)
    cited_candidates: list[str] = Field(default_factory=list)
    cited_fields: list[str] = Field(default_factory=list)
    follow_up_suggestions: list[str] = Field(default_factory=list)


class ChatResponse(BaseModel):
    """API response payload for a recruiter chat turn."""

    session_id: str
    message: ChatAnswer
    history: list[ChatMessage]


class KeyCount(BaseModel):
    """Named aggregate count used by executive charts and summaries."""

    name: str
    count: int


class ExecutiveCandidate(BaseModel):
    """Candidate row for executive shortlist views."""

    candidate_id: str
    candidate_name: str
    rank: int
    overall_score: float
    recommendation: str
    skill_match: float
    confidence_score: float


class DiversityMetrics(BaseModel):
    """Non-protected diversity signals derived only from explicit resume data."""

    locations: list[KeyCount] = Field(default_factory=list)
    languages: list[KeyCount] = Field(default_factory=list)
    education_levels: list[KeyCount] = Field(default_factory=list)
    resume_file_types: list[KeyCount] = Field(default_factory=list)


class ExecutiveSummaryResponse(BaseModel):
    """One-click executive hiring summary for the latest screening report."""

    overall_hiring_summary: str
    top_candidates: list[ExecutiveCandidate] = Field(default_factory=list)
    top_skills: list[KeyCount] = Field(default_factory=list)
    most_missing_skills: list[KeyCount] = Field(default_factory=list)
    hiring_risks: list[str] = Field(default_factory=list)
    interview_priorities: list[str] = Field(default_factory=list)
    diversity_metrics: DiversityMetrics = Field(default_factory=DiversityMetrics)
    average_experience: float = 0.0
    average_skill_match: float = 0.0
    overall_recommendation: str


class TeamFitRecommendation(BaseModel):
    """Named best-fit recommendation for a hiring dimension."""

    category: str
    candidate_id: str | None = None
    candidate_name: str | None = None
    explanation: str
    evidence: list[str] = Field(default_factory=list)


class HiringRiskItem(BaseModel):
    """Risk surfaced from existing score breakdown and resume completeness signals."""

    category: str
    severity: str
    description: str
    affected_candidates: list[str] = Field(default_factory=list)
    mitigation: str


class InterviewPlanItem(BaseModel):
    """Structured interview plan for a ranked candidate."""

    candidate_id: str
    candidate_name: str
    interview_order: int
    focus_areas: list[str] = Field(default_factory=list)
    technical_questions: list[str] = Field(default_factory=list)
    behavioral_questions: list[str] = Field(default_factory=list)
    red_flags: list[str] = Field(default_factory=list)
    expected_difficulty: str


class HiringAnalyticsResponse(BaseModel):
    """Dashboard-ready recruitment analytics for the latest screening report."""

    job_title: str | None = None
    total_candidates: int = 0
    average_resume_score: float = 0.0
    average_experience: float = 0.0
    average_skill_match: float = 0.0
    recommendation_distribution: list[KeyCount] = Field(default_factory=list)
    skill_frequency: list[KeyCount] = Field(default_factory=list)
    experience_distribution: list[KeyCount] = Field(default_factory=list)
    education_distribution: list[KeyCount] = Field(default_factory=list)
    technology_distribution: list[KeyCount] = Field(default_factory=list)
    top_programming_languages: list[KeyCount] = Field(default_factory=list)
    top_frameworks: list[KeyCount] = Field(default_factory=list)
    cloud_skills: list[KeyCount] = Field(default_factory=list)
    ai_skills: list[KeyCount] = Field(default_factory=list)


class HiringInsightsResponse(BaseModel):
    """Executive insight payload combining team fit, risks, and interview planning."""

    team_fit: list[TeamFitRecommendation] = Field(default_factory=list)
    risks: list[HiringRiskItem] = Field(default_factory=list)
    interview_plan: list[InterviewPlanItem] = Field(default_factory=list)
    executive_insights: list[str] = Field(default_factory=list)


class HiringReportResponse(BaseModel):
    """Complete executive hiring intelligence report."""

    report_id: str
    generated_at: datetime = Field(default_factory=datetime.utcnow)
    executive_summary: ExecutiveSummaryResponse
    analytics: HiringAnalyticsResponse
    insights: HiringInsightsResponse


class ScoreContribution(BaseModel):
    """Explainable score contribution row for a candidate."""

    section: str
    earned_points: float
    maximum_points: float
    percentage: float
    explanation: str


class RequirementCoverageItem(BaseModel):
    """Requirement mapping result between JD and candidate evidence."""

    requirement: str
    status: str
    evidence: str


class RequirementMapping(BaseModel):
    """Full/partial/missing JD requirement coverage."""

    fully_matched: list[RequirementCoverageItem] = Field(default_factory=list)
    partially_matched: list[RequirementCoverageItem] = Field(default_factory=list)
    missing: list[RequirementCoverageItem] = Field(default_factory=list)


class ResumeQualityAnalysis(BaseModel):
    """Resume quality explanation based on available parsed data."""

    rating: str
    completeness: float
    formatting: str
    contact_information: str
    project_details: str
    education_quality: str
    experience_quality: str
    missing_sections: list[str] = Field(default_factory=list)


class ConfidenceExplanation(BaseModel):
    """Explains why the confidence score has its value."""

    confidence_score: float
    rating: str
    factors: list[ScoreContribution] = Field(default_factory=list)
    explanation: str


class TraceStep(BaseModel):
    """Execution trace step for candidate or graph observability."""

    name: str
    status: str
    execution_time: float
    input_size: int = 0
    output_size: int = 0
    retry_count: int = 0
    failure_reason: str | None = None
    execution_order: int


class AuditRecord(BaseModel):
    """Immutable-style audit record for a screening decision."""

    timestamp: datetime = Field(default_factory=datetime.utcnow)
    candidate_id: str
    candidate_name: str
    jd_id: str
    model_used: str
    embedding_model: str
    weights_used: dict[str, float]
    similarity_scores: dict[str, float]
    recommendation: str
    version: str


class PromptHistoryRecord(BaseModel):
    """Sanitized prompt-inspector record."""

    id: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    prompt_name: str
    prompt: str
    llm_response: str
    structured_output: dict[str, Any] = Field(default_factory=dict)
    execution_time: float
    token_usage: dict[str, int] = Field(default_factory=dict)


class CandidateExplainabilityResponse(BaseModel):
    """Complete XAI payload for a candidate decision."""

    candidate_id: str
    candidate_name: str
    jd_id: str
    overall_score: float
    recommendation: str
    score_contributions: list[ScoreContribution]
    requirement_mapping: RequirementMapping
    visual_data: dict[str, Any] = Field(default_factory=dict)
    resume_quality: ResumeQualityAnalysis
    confidence_explanation: ConfidenceExplanation
    ai_trace: list[TraceStep]
    audit_record: AuditRecord
    recommendation_reasoning: str


class GraphExecutionResponse(BaseModel):
    """Observable LangGraph execution data for the latest screening run."""

    report_id: str | None = None
    timeline: list[TraceStep] = Field(default_factory=list)
    performance_metrics: dict[str, float] = Field(default_factory=dict)
