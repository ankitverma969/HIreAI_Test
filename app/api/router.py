import csv
import json
import time
from datetime import datetime
from pathlib import Path
from typing import Any

from fastapi import (
    APIRouter,
    File,
    HTTPException,
    UploadFile,
    WebSocket,
    WebSocketDisconnect,
    status,
)
from fastapi.responses import FileResponse
from loguru import logger
from pydantic import BaseModel

from app.core.config import settings
from app.exporters.report_exporter import ReportExporter
from app.graph.hiring_assistant import (
    comparison_graph,
    executive_hiring_graph,
    recruiter_chat_graph,
)
from app.graph.workflow import app_graph
from app.models.candidate import Candidate
from app.models.hiring_assistant import (
    AuditRecord,
    CandidateComparisonResponse,
    CandidateExplainabilityResponse,
    ChatMessage,
    ChatRequest,
    ChatResponse,
    ComparisonRequest,
    ConfidenceExplanation,
    HiringAnalyticsResponse,
    HiringInsightsResponse,
    HiringReportResponse,
    ExecutiveSummaryResponse,
    GraphExecutionResponse,
    PromptHistoryRecord,
    RequirementCoverageItem,
    RequirementMapping,
    ResumeQualityAnalysis,
    ScoreContribution,
    TraceStep,
)
from app.models.job_description import JobDescription
from app.models.report import Report
from app.models.response import SuccessResponse
from app.prompts.loader import PromptLoader

router = APIRouter()

# In-memory session store (no database, as per requirements)
RESULTS_STORE: dict[str, Report] = {}
CANDIDATE_STORE: dict[str, Candidate] = {}
JOB_DESCRIPTION_STORE: dict[str, JobDescription] = {}
LLM_ANALYSIS_STORE: dict[str, dict[str, Any]] = {}
CHAT_HISTORY_STORE: dict[str, list[ChatMessage]] = {}
GRAPH_TRACE_STORE: dict[str, GraphExecutionResponse] = {}
AUDIT_LOG_STORE: list[AuditRecord] = []
PROMPT_HISTORY_STORE: list[PromptHistoryRecord] = []
GLOBAL_STATE: dict[str, Any] = {
    "last_report_id": None
}

SCORING_WEIGHTS = {
    "Skill Match": 35.0,
    "Experience": 25.0,
    "Projects": 15.0,
    "Education": 10.0,
    "Semantic Similarity": 10.0,
    "Certifications": 5.0,
    "Keyword Match": 0.0,
    "Resume Completeness": 0.0,
    "Confidence": 0.0,
}

class ScreenPayload(BaseModel):
    job_description_path: str
    resumes_paths: list[str]


async def _build_executive_report() -> HiringReportResponse:
    """Runs the executive hiring intelligence graph for the latest session."""
    report_id = GLOBAL_STATE.get("last_report_id")
    if not report_id or report_id not in RESULTS_STORE:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No screening report found. Run screening before requesting executive intelligence.",
        )

    final_state = await executive_hiring_graph.ainvoke(
        {
            "report_id": report_id,
            "job_description": JOB_DESCRIPTION_STORE.get(report_id),
            "candidates": CANDIDATE_STORE,
            "report": RESULTS_STORE[report_id],
            "llm_analysis": LLM_ANALYSIS_STORE,
            "errors": [],
        }
    )
    errors = final_state.get("errors") or []
    if errors:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="; ".join(errors),
        )

    response = final_state.get("response")
    if not isinstance(response, HiringReportResponse):
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Executive intelligence workflow completed without a report payload.",
        )
    return response


def _executive_markdown(report: HiringReportResponse) -> str:
    """Formats the executive report as Markdown."""
    summary = report.executive_summary
    analytics = report.analytics
    insights = report.insights

    lines = [
        "# Executive Hiring Intelligence Report",
        "",
        f"**Report ID:** `{report.report_id}`",
        f"**Generated At:** {report.generated_at.isoformat()}",
        f"**Role:** {analytics.job_title or 'Not listed'}",
        "",
        "## Overall Hiring Summary",
        "",
        summary.overall_hiring_summary,
        "",
        f"**Average Experience:** {summary.average_experience} years",
        f"**Average Skill Match:** {summary.average_skill_match}%",
        f"**Overall Recommendation:** {summary.overall_recommendation}",
        "",
        "## Top Candidates",
        "",
        "| Rank | Candidate | Score | Skill Match | Confidence | Recommendation |",
        "|------|-----------|------:|------------:|-----------:|----------------|",
    ]
    for candidate in summary.top_candidates:
        lines.append(
            f"| {candidate.rank} | {candidate.candidate_name} | {candidate.overall_score}% "
            f"| {candidate.skill_match}% | {candidate.confidence_score}% | {candidate.recommendation} |"
        )

    lines.extend(["", "## Top Skills", ""])
    lines.extend(f"- {item.name}: {item.count}" for item in summary.top_skills)
    lines.extend(["", "## Most Missing Skills", ""])
    lines.extend(f"- {item.name}: {item.count}" for item in summary.most_missing_skills)
    lines.extend(["", "## Hiring Risks", ""])
    lines.extend(f"- {risk}" for risk in summary.hiring_risks)
    lines.extend(["", "## Interview Priorities", ""])
    lines.extend(f"- {priority}" for priority in summary.interview_priorities)
    lines.extend(["", "## Team Fit Analysis", ""])
    for fit in insights.team_fit:
        target = fit.candidate_name or "No clear candidate"
        lines.append(f"- **{fit.category}:** {target}. {fit.explanation}")
    lines.extend(["", "## Interview Plan", ""])
    for item in insights.interview_plan:
        lines.append(f"### {item.interview_order}. {item.candidate_name}")
        lines.append(f"- Expected difficulty: {item.expected_difficulty}")
        lines.append(f"- Focus areas: {', '.join(item.focus_areas)}")
        lines.append(f"- Red flags: {', '.join(item.red_flags)}")
        lines.append("")
    return "\n".join(lines).strip() + "\n"


def _analytics_csv(report: HiringReportResponse, output_path: Path) -> str:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    analytics = report.analytics
    with open(output_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["Metric", "Name", "Count", "Value"])
        writer.writerow(["Average Resume Score", "", "", analytics.average_resume_score])
        writer.writerow(["Average Experience", "", "", analytics.average_experience])
        writer.writerow(["Average Skill Match", "", "", analytics.average_skill_match])
        for section_name, rows in [
            ("Recommendation Distribution", analytics.recommendation_distribution),
            ("Skill Frequency", analytics.skill_frequency),
            ("Experience Distribution", analytics.experience_distribution),
            ("Education Distribution", analytics.education_distribution),
            ("Technology Distribution", analytics.technology_distribution),
            ("Top Programming Languages", analytics.top_programming_languages),
            ("Top Frameworks", analytics.top_frameworks),
            ("Cloud Skills", analytics.cloud_skills),
            ("AI Skills", analytics.ai_skills),
        ]:
            for row in rows:
                writer.writerow([section_name, row.name, row.count, ""])
    return str(output_path.absolute())


def _write_simple_pdf(lines: list[str], output_path: Path) -> str:
    output_path.parent.mkdir(parents=True, exist_ok=True)

    def escape_pdf_text(value: str) -> str:
        return value.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")

    y = 780
    text_ops = ["BT", "/F1 10 Tf"]
    for line in lines[:65]:
        text_ops.append(f"1 0 0 1 50 {y} Tm ({escape_pdf_text(line[:95])}) Tj")
        y -= 14
    text_ops.append("ET")
    stream = "\n".join(text_ops).encode("latin-1", errors="replace")
    objects = [
        b"<< /Type /Catalog /Pages 2 0 R >>",
        b"<< /Type /Pages /Kids [3 0 R] /Count 1 >>",
        b"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] /Resources << /Font << /F1 4 0 R >> >> /Contents 5 0 R >>",
        b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>",
        b"<< /Length " + str(len(stream)).encode("ascii") + b" >>\nstream\n" + stream + b"\nendstream",
    ]

    pdf = bytearray(b"%PDF-1.4\n")
    offsets = [0]
    for index, obj in enumerate(objects, start=1):
        offsets.append(len(pdf))
        pdf.extend(f"{index} 0 obj\n".encode("ascii"))
        pdf.extend(obj)
        pdf.extend(b"\nendobj\n")
    xref_start = len(pdf)
    pdf.extend(f"xref\n0 {len(objects) + 1}\n".encode("ascii"))
    pdf.extend(b"0000000000 65535 f \n")
    for offset in offsets[1:]:
        pdf.extend(f"{offset:010d} 00000 n \n".encode("ascii"))
    pdf.extend(
        f"trailer << /Size {len(objects) + 1} /Root 1 0 R >>\nstartxref\n{xref_start}\n%%EOF\n".encode("ascii")
    )
    output_path.write_bytes(bytes(pdf))
    return str(output_path.absolute())


def _recommendation_from_score(score_value: float) -> str:
    if score_value >= 90.0:
        return "Strong Hire"
    if score_value >= 80.0:
        return "Hire"
    if score_value >= 70.0:
        return "Consider"
    if score_value >= 60.0:
        return "Review"
    return "Reject"


def _latest_report() -> tuple[str, Report]:
    report_id = GLOBAL_STATE.get("last_report_id")
    if not report_id or report_id not in RESULTS_STORE:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No screening report found. Run screening before requesting explainability data.",
        )
    return report_id, RESULTS_STORE[report_id]


def _ranking_for_candidate(report: Report, candidate_id: str) -> Any:
    for ranking in report.rankings:
        if ranking.candidate_id == candidate_id:
            return ranking
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail=f"Candidate '{candidate_id}' does not have ranking results.",
    )


def _quality_status(value: float) -> str:
    if value >= 85:
        return "Excellent"
    if value >= 70:
        return "Good"
    if value >= 50:
        return "Average"
    return "Poor"


def _score_contribution(section: str, percentage: float, explanation: str) -> ScoreContribution:
    maximum = SCORING_WEIGHTS[section]
    earned = (percentage / 100.0) * maximum if maximum else 0.0
    return ScoreContribution(
        section=section,
        earned_points=round(earned, 2),
        maximum_points=maximum,
        percentage=round(float(percentage), 1),
        explanation=explanation,
    )


def _build_score_contributions(candidate: Candidate, ranking: Any) -> list[ScoreContribution]:
    breakdown = ranking.score.breakdown
    completeness_checks = [
        candidate.email is not None,
        candidate.phone is not None,
        candidate.location is not None,
        candidate.summary is not None,
        bool(candidate.experience),
        bool(candidate.education),
        bool(candidate.projects),
        bool(candidate.skills),
    ]
    completeness = (sum(1 for item in completeness_checks if item) / len(completeness_checks)) * 100.0
    return [
        _score_contribution("Skill Match", breakdown.skill_match, "Weighted score contribution from required and preferred skill overlap."),
        _score_contribution("Experience", breakdown.experience_match, "Weighted score contribution from experience relevance and years alignment."),
        _score_contribution("Education", breakdown.education_match, "Weighted score contribution from degree and education requirement alignment."),
        _score_contribution("Projects", breakdown.project_match, "Weighted score contribution from project evidence aligned to the JD."),
        _score_contribution("Certifications", breakdown.certification_match, "Weighted score contribution from certification evidence."),
        _score_contribution("Semantic Similarity", breakdown.semantic_similarity, "Weighted score contribution from resume-to-JD semantic similarity."),
        _score_contribution("Keyword Match", breakdown.keyword_match, "Diagnostic keyword overlap. It is shown for transparency and does not change the weighted score."),
        _score_contribution("Resume Completeness", completeness, "Diagnostic resume completeness based on parsed sections and contact metadata."),
        _score_contribution("Confidence", ranking.score.confidence_score, "Diagnostic confidence from completeness, extraction quality, and score stability."),
    ]


def _build_requirement_mapping(candidate: Candidate, jd: JobDescription | None, ranking: Any) -> RequirementMapping:
    required = jd.required_skills if jd else ranking.score.missing_skills + ranking.score.matched_skills
    candidate_skills = {skill.lower(): skill for skill in candidate.skills}
    text = candidate.raw_resume_text.lower()
    mapping = RequirementMapping()

    for requirement in required:
        req_lower = requirement.lower()
        if req_lower in candidate_skills:
            mapping.fully_matched.append(
                RequirementCoverageItem(
                    requirement=requirement,
                    status="Fully Matched",
                    evidence=f"Extracted skill: {candidate_skills[req_lower]}",
                )
            )
        elif req_lower in text:
            mapping.partially_matched.append(
                RequirementCoverageItem(
                    requirement=requirement,
                    status="Partially Matched",
                    evidence="Mention found in resume text but not normalized as an extracted skill.",
                )
            )
        else:
            mapping.missing.append(
                RequirementCoverageItem(
                    requirement=requirement,
                    status="Missing",
                    evidence="No explicit candidate evidence found.",
                )
            )

    preferred = jd.preferred_skills if jd else []
    for requirement in preferred:
        req_lower = requirement.lower()
        if req_lower in candidate_skills and all(item.requirement != requirement for item in mapping.fully_matched):
            mapping.fully_matched.append(
                RequirementCoverageItem(
                    requirement=requirement,
                    status="Fully Matched",
                    evidence=f"Preferred skill extracted: {candidate_skills[req_lower]}",
                )
            )
        elif req_lower in text:
            mapping.partially_matched.append(
                RequirementCoverageItem(
                    requirement=requirement,
                    status="Partially Matched",
                    evidence="Preferred skill appears in resume text.",
                )
            )
    return mapping


def _resume_quality(candidate: Candidate) -> ResumeQualityAnalysis:
    missing = []
    if not candidate.email or not candidate.phone:
        missing.append("Contact Information")
    if not candidate.projects:
        missing.append("Projects")
    if not candidate.education:
        missing.append("Education")
    if not candidate.experience:
        missing.append("Experience")
    if not candidate.summary:
        missing.append("Summary")

    checks = [
        bool(candidate.email and candidate.phone),
        bool(candidate.projects),
        bool(candidate.education),
        bool(candidate.experience),
        bool(candidate.summary),
        len(candidate.raw_resume_text.split()) >= 120,
    ]
    completeness = (sum(1 for item in checks if item) / len(checks)) * 100.0
    return ResumeQualityAnalysis(
        rating=_quality_status(completeness),
        completeness=round(completeness, 1),
        formatting="Good" if len(candidate.raw_resume_text.splitlines()) >= 4 else "Average",
        contact_information="Good" if candidate.email and candidate.phone else "Poor",
        project_details="Good" if candidate.projects else "Poor",
        education_quality="Good" if candidate.education else "Poor",
        experience_quality="Good" if candidate.experience else "Poor",
        missing_sections=missing,
    )


def _confidence_explanation(candidate: Candidate, ranking: Any) -> ConfidenceExplanation:
    score = ranking.score
    completeness = _resume_quality(candidate).completeness
    extraction_quality = 100.0 if candidate.email and candidate.phone else 80.0 if candidate.email or candidate.phone else 50.0
    stability = max(0.0, 100.0 - abs(score.breakdown.semantic_similarity - score.breakdown.skill_match) * 1.5)
    parsing = min(100.0, 70.0 + (10.0 if candidate.skills else 0.0) + (10.0 if candidate.experience else 0.0) + (10.0 if candidate.education else 0.0))
    factors = [
        ScoreContribution(section="Missing Data", earned_points=round(completeness, 1), maximum_points=100.0, percentage=round(completeness, 1), explanation="Completeness of required resume sections and contact metadata."),
        ScoreContribution(section="Parsing Confidence", earned_points=round(parsing, 1), maximum_points=100.0, percentage=round(parsing, 1), explanation="Whether parsers extracted core resume sections successfully."),
        ScoreContribution(section="Extraction Quality", earned_points=round(extraction_quality, 1), maximum_points=100.0, percentage=round(extraction_quality, 1), explanation="Availability of validated identity and contact fields."),
        ScoreContribution(section="Similarity Stability", earned_points=round(stability, 1), maximum_points=100.0, percentage=round(stability, 1), explanation="Closeness between semantic similarity and skill-match signals."),
    ]
    return ConfidenceExplanation(
        confidence_score=score.confidence_score,
        rating=_quality_status(score.confidence_score),
        factors=factors,
        explanation=(
            f"Confidence is {score.confidence_score}% because the resume has {_quality_status(completeness).lower()} completeness, "
            f"{_quality_status(extraction_quality).lower()} extraction quality, and {_quality_status(stability).lower()} similarity stability."
        ),
    )


def _trace_step(name: str, timing: dict[str, float], order: int, input_size: int, output_size: int) -> TraceStep:
    duration = timing.get(name, 0.0)
    return TraceStep(
        name=name,
        status="success",
        execution_time=round(duration, 4),
        input_size=input_size,
        output_size=output_size,
        retry_count=0,
        failure_reason=None,
        execution_order=order,
    )


def _build_graph_trace(report_id: str, final_state: dict[str, Any]) -> GraphExecutionResponse:
    timing = final_state.get("timing") or {}
    candidates = final_state.get("candidates") or []
    report = final_state.get("report")
    node_specs = [
        ("validate_input", 1),
        ("parse_jd", 2),
        ("load_resumes", 3),
        ("generate_embeddings", 4),
        ("semantic_similarity", 5),
        ("rule_based_scoring", 6),
        ("llm_analysis", 7),
        ("candidate_recommendation", 8),
        ("ranking", 9),
        ("report_generation", 10),
    ]
    timeline = [
        _trace_step(
            name=node_name,
            timing=timing,
            order=order,
            input_size=len(candidates) if order >= 3 else 1,
            output_size=len(report.rankings) if report and order >= 9 else len(candidates),
        )
        for node_name, order in node_specs
    ]
    total_time = round(sum(step.execution_time for step in timeline), 4)
    return GraphExecutionResponse(
        report_id=report_id,
        timeline=timeline,
        performance_metrics={
            "total_execution_time": total_time,
            "node_count": float(len(timeline)),
            "average_node_time": round(total_time / len(timeline), 4) if timeline else 0.0,
            "retry_count": 0.0,
        },
    )


def _build_ai_trace(candidate: Candidate, graph_trace: GraphExecutionResponse) -> list[TraceStep]:
    if not graph_trace.timeline:
        fallback_steps = [
            ("Resume Parsed", len(candidate.raw_resume_text), 1),
            ("Skills Extracted", len(candidate.raw_resume_text), len(candidate.skills)),
            ("Embeddings Generated", len(candidate.skills), 1),
            ("Similarity Calculated", 1, 1),
            ("Scores Generated", 1, 1),
            ("Explanation Generated", 1, 1),
            ("Ranking Completed", 1, 1),
        ]
        return [
            TraceStep(
                name=name,
                status="success",
                execution_time=round(candidate.metadata.processing_time if order == 1 else 0.0, 4),
                input_size=input_size,
                output_size=output_size,
                execution_order=order,
            )
            for order, (name, input_size, output_size) in enumerate(fallback_steps, start=1)
        ]

    name_map = {
        "parse_jd": "Job Description Parsed",
        "load_resumes": "Resume Parsed",
        "generate_embeddings": "Embeddings Generated",
        "semantic_similarity": "Similarity Calculated",
        "rule_based_scoring": "Scores Generated",
        "llm_analysis": "Explanation Generated",
        "ranking": "Ranking Completed",
    }
    output = []
    order = 1
    for step in graph_trace.timeline:
        if step.name in name_map:
            output.append(
                TraceStep(
                    name=name_map[step.name],
                    status=step.status,
                    execution_time=step.execution_time,
                    input_size=step.input_size,
                    output_size=step.output_size,
                    retry_count=step.retry_count,
                    failure_reason=step.failure_reason,
                    execution_order=order,
                )
            )
            order += 1
    if not any(step.name == "Skills Extracted" for step in output):
        output.insert(
            2,
            TraceStep(
                name="Skills Extracted",
                status="success",
                execution_time=round(candidate.metadata.processing_time, 4),
                input_size=len(candidate.raw_resume_text),
                output_size=len(candidate.skills),
                execution_order=3,
            ),
        )
        for idx, step in enumerate(output, start=1):
            step.execution_order = idx
    return output


def _audit_record(report: Report, candidate: Candidate, ranking: Any) -> AuditRecord:
    return AuditRecord(
        candidate_id=candidate.id,
        candidate_name=candidate.full_name or ranking.candidate_name,
        jd_id=report.job_description_id,
        model_used=settings.MODEL_NAME,
        embedding_model=settings.EMBEDDING_MODEL,
        weights_used={key: value for key, value in SCORING_WEIGHTS.items() if value > 0},
        similarity_scores={
            "skill_match": ranking.score.breakdown.skill_match,
            "keyword_match": ranking.score.breakdown.keyword_match,
            "experience_match": ranking.score.breakdown.experience_match,
            "project_match": ranking.score.breakdown.project_match,
            "education_match": ranking.score.breakdown.education_match,
            "certification_match": ranking.score.breakdown.certification_match,
            "semantic_similarity": ranking.score.breakdown.semantic_similarity,
            "confidence_score": ranking.score.confidence_score,
        },
        recommendation=_recommendation_from_score(ranking.score.overall_score),
        version=settings.APP_VERSION,
    )


def _record_prompt_history(
    prompt_name: str,
    prompt: str,
    structured_output: dict[str, Any],
    execution_time: float,
) -> None:
    def sanitize_text(value: str) -> str:
        sanitized = value
        for secret in (settings.OPENAI_API_KEY, settings.GROQ_API_KEY, settings.GEMINI_API_KEY):
            if secret:
                sanitized = sanitized.replace(secret, "[REDACTED]")
        return sanitized

    def sanitize_payload(value: dict[str, Any]) -> dict[str, Any]:
        serialized = sanitize_text(json.dumps(value, default=str))
        return json.loads(serialized)

    safe_prompt = sanitize_text(prompt)
    for secret in (settings.OPENAI_API_KEY, settings.GROQ_API_KEY, settings.GEMINI_API_KEY):
        if secret:
            safe_prompt = safe_prompt.replace(secret, "[REDACTED]")
    safe_output = sanitize_payload(structured_output)
    PROMPT_HISTORY_STORE.append(
        PromptHistoryRecord(
            id=f"prompt-{len(PROMPT_HISTORY_STORE) + 1}",
            prompt_name=prompt_name,
            prompt=safe_prompt,
            llm_response="Structured output generated by the configured LLM or deterministic fallback.",
            structured_output=safe_output,
            execution_time=round(execution_time, 4),
            token_usage={
                "prompt_tokens": max(1, len(safe_prompt.split())),
                "completion_tokens": max(1, len(json.dumps(safe_output, default=str).split())),
            },
        )
    )


def _explain_candidate(candidate_id: str) -> CandidateExplainabilityResponse:
    report_id, report = _latest_report()
    if candidate_id not in CANDIDATE_STORE:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Candidate '{candidate_id}' not found.")
    candidate = CANDIDATE_STORE[candidate_id]
    ranking = _ranking_for_candidate(report, candidate_id)
    jd = JOB_DESCRIPTION_STORE.get(report_id)
    contributions = _build_score_contributions(candidate, ranking)
    mapping = _build_requirement_mapping(candidate, jd, ranking)
    quality = _resume_quality(candidate)
    confidence = _confidence_explanation(candidate, ranking)
    graph_trace = GRAPH_TRACE_STORE.get(report_id) or GraphExecutionResponse(report_id=report_id)
    audit = _audit_record(report, candidate, ranking)
    if not any(record.candidate_id == audit.candidate_id and record.jd_id == audit.jd_id for record in AUDIT_LOG_STORE):
        AUDIT_LOG_STORE.append(audit)

    visual_data = {
        "waterfall": [item.model_dump() for item in contributions if item.maximum_points > 0],
        "radar": [
            {"metric": item.section, "value": item.percentage}
            for item in contributions
            if item.section in {"Skill Match", "Experience", "Education", "Projects", "Certifications", "Semantic Similarity", "Confidence"}
        ],
        "skill_heatmap": [
            {"skill": item.requirement, "status": item.status}
            for item in mapping.fully_matched + mapping.partially_matched + mapping.missing
        ],
        "requirement_coverage": {
            "fully_matched": len(mapping.fully_matched),
            "partially_matched": len(mapping.partially_matched),
            "missing": len(mapping.missing),
        },
        "score_contribution_chart": [
            {"section": item.section, "earned": item.earned_points, "max": item.maximum_points}
            for item in contributions
        ],
        "confidence_gauge": {"value": confidence.confidence_score, "rating": confidence.rating},
    }

    return CandidateExplainabilityResponse(
        candidate_id=candidate.id,
        candidate_name=candidate.full_name or ranking.candidate_name,
        jd_id=report.job_description_id,
        overall_score=ranking.score.overall_score,
        recommendation=_recommendation_from_score(ranking.score.overall_score),
        score_contributions=contributions,
        requirement_mapping=mapping,
        visual_data=visual_data,
        resume_quality=quality,
        confidence_explanation=confidence,
        ai_trace=_build_ai_trace(candidate, graph_trace),
        audit_record=audit,
        recommendation_reasoning=ranking.score.reasoning,
    )


# WebSocket Connection Manager
class ConnectionManager:
    def __init__(self) -> None:
        self.active_connections: list[WebSocket] = []

    async def connect(self, websocket: WebSocket) -> None:
        await websocket.accept()
        self.active_connections.append(websocket)
        logger.info(f"WebSocket client connected. Total connections: {len(self.active_connections)}")

    def disconnect(self, websocket: WebSocket) -> None:
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
            logger.info(f"WebSocket client disconnected. Remaining: {len(self.active_connections)}")

    async def send_personal_message(self, message: dict[str, Any], websocket: WebSocket) -> None:
        try:
            await websocket.send_json(message)
        except Exception as e:
            logger.error(f"Error sending message: {str(e)}")

    async def broadcast(self, message: dict[str, Any]) -> None:
        for connection in list(self.active_connections):
            try:
                await connection.send_json(message)
            except Exception as e:
                logger.error(f"Failed to broadcast to connection: {str(e)}")
                self.disconnect(connection)

manager = ConnectionManager()


@router.get("/", response_model=SuccessResponse[dict[str, str]])
async def root() -> SuccessResponse[dict[str, str]]:
    """Root endpoint welcoming users to the screening service."""
    return SuccessResponse(
        message=f"Welcome to the {settings.APP_NAME} Service",
        data={"status": "online", "documentation": "/docs"},
    )


@router.get("/health", response_model=SuccessResponse[dict[str, str]])
async def health() -> SuccessResponse[dict[str, str]]:
    """Health check endpoint checking application viability."""
    return SuccessResponse(
        message="System status healthy",
        data={"status": "healthy", "timestamp": datetime.utcnow().isoformat()},
    )


@router.get("/version", response_model=SuccessResponse[dict[str, str]])
async def version() -> SuccessResponse[dict[str, str]]:
    """Version check endpoint returning current release metadata."""
    return SuccessResponse(
        message="Version check succeeded",
        data={"app_name": settings.APP_NAME, "version": settings.APP_VERSION},
    )


# WebSocket endpoint for progress updates
@router.websocket("/ws")
async def websocket_progress(websocket: WebSocket) -> None:
    await manager.connect(websocket)
    try:
        # Keep connection open and handle client pings
        while True:
            await websocket.receive_text()
            # Echo back ping to confirm connection is healthy
            await websocket.send_json({"type": "pong", "timestamp": datetime.utcnow().isoformat()})
    except WebSocketDisconnect:
        manager.disconnect(websocket)
    except Exception as e:
        logger.error(f"WebSocket error: {str(e)}")
        manager.disconnect(websocket)


# Upload Job Description
@router.post("/job-description/upload")
async def upload_job_description(file: UploadFile = File(...)) -> SuccessResponse[dict[str, Any]]:  # noqa: B008
    """Saves uploaded Job Description file to temporary uploads folder."""
    try:
        upload_dir = Path("data/uploads")
        upload_dir.mkdir(parents=True, exist_ok=True)

        # Keep original extension
        ext = Path(file.filename or "jd.txt").suffix or ".txt"
        file_path = upload_dir / f"jd_{int(time.time())}{ext}"

        content = await file.read()
        with open(file_path, "wb") as f:
            f.write(content)

        logger.info(f"Job Description uploaded successfully: {file_path}")
        return SuccessResponse(
            message="Job description uploaded successfully.",
            data={
                "filename": file.filename,
                "saved_path": str(file_path.absolute()),
                "size_bytes": len(content)
            }
        )
    except Exception as e:
        logger.error(f"Failed to upload Job Description: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to upload JD: {str(e)}"
        ) from e


# Upload Multiple Resumes
@router.post("/resumes/upload")
async def upload_resumes(files: list[UploadFile] = File(...)) -> SuccessResponse[list[dict[str, Any]]]:  # noqa: B008
    """Saves multiple resume uploads to temporary folders."""
    try:
        upload_dir = Path("data/uploads")
        upload_dir.mkdir(parents=True, exist_ok=True)

        uploaded_details = []
        for file in files:
            Path(file.filename or "resume.pdf").suffix or ".pdf"
            file_path = upload_dir / f"resume_{int(time.time())}_{file.filename}"

            content = await file.read()
            with open(file_path, "wb") as f:
                f.write(content)

            uploaded_details.append({
                "filename": file.filename,
                "saved_path": str(file_path.absolute()),
                "size_bytes": len(content)
            })

        logger.info(f"Uploaded {len(uploaded_details)} resumes successfully.")
        return SuccessResponse(
            message="Resumes uploaded successfully.",
            data=uploaded_details
        )
    except Exception as e:
        logger.error(f"Failed to upload resumes: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to upload resumes: {str(e)}"
        ) from e


# Screen Resumes endpoint with WebSockets updates
@router.post("/screen")
async def screen_resumes(payload: ScreenPayload) -> SuccessResponse[dict[str, Any]]:
    """Runs the LangGraph candidate screening workflow, streaming node execution via WebSocket."""
    logger.info(f"Initiating screening pipeline for JD: {payload.job_description_path} with {len(payload.resumes_paths)} candidates.")

    from app.graph import AgentState
    initial_state: AgentState = {
        "job_description_path": payload.job_description_path,
        "resumes_paths": payload.resumes_paths,
        "job_description_raw": None,
        "candidates_input": [],
        "job_description": None,
        "candidates": [],
        "jd_embedding": None,
        "candidate_embeddings": {},
        "candidate_experience_embeddings": {},
        "candidate_project_embeddings": {},
        "candidate_education_embeddings": {},
        "scores": {},
        "llm_analysis": {},
        "recommendations": {},
        "rankings": [],
        "report": None,
        "metadata": {},
        "timing": {},
        "errors": [],
        "export_paths": {}
    }

    # Broadcast start screening event
    await manager.broadcast({
        "type": "progress",
        "stage": "validate_input",
        "status": "in_progress",
        "message": "Initiating candidate screening pipeline validation checks..."
    })

    try:
        final_state: AgentState = initial_state

        # Execute the StateGraph using .astream to send live node execution progress updates!
        async for chunk in app_graph.astream(initial_state, stream_mode="updates"):
            # chunk contains mapping from node_name -> state update
            node_name = list(chunk.keys())[0]
            logger.info(f"LangGraph node completed: {node_name}")

            # Map node names to UI descriptive stages
            stage_messages = {
                "validate_input": "Inputs validated. File structure matches requirements.",
                "parse_jd": "Job Description document parsed and structured.",
                "load_resumes": "Candidate resume documents parsed and extracted.",
                "embedding_generation": "Generating sentence-transformers dense vector embeddings...",
                "similarity_calculation": "Calculating cosine similarity index score maps...",
                "score_generation": "Applying rule-based scoring engines and weights...",
                "reasoning_generation": "Generating AI Recruiter strengths, weaknesses, and interview questions...",
                "recommendation": "Aggregating candidate final decision suggestions...",
                "ranking": "Sorting candidates deterministically based on match values...",
                "report_generation": "Compiling final ATS reports and statistics."
            }

            msg = stage_messages.get(node_name, f"Processed phase {node_name} successfully.")

            # Broadcast update
            await manager.broadcast({
                "type": "progress",
                "stage": node_name,
                "status": "completed",
                "message": msg
            })

            # Aggregate final state chunks
            for key, val in chunk[node_name].items():
                final_state[key] = val  # type: ignore [literal-required]

        # Retrieve report
        report = final_state.get("report")
        if not report:
            error_msgs = "; ".join(final_state.get("errors") or ["Unknown workflow termination."])
            raise ValueError(f"Screening workflow terminated without report: {error_msgs}")

        assert isinstance(report, Report)

        # Store report & candidates in memory cache
        report_id = report.job_description_id or f"REP_{int(time.time())}"
        RESULTS_STORE[report_id] = report
        GLOBAL_STATE["last_report_id"] = report_id
        GRAPH_TRACE_STORE[report_id] = _build_graph_trace(report_id, dict(final_state))

        job_description = final_state.get("job_description")
        if isinstance(job_description, JobDescription):
            JOB_DESCRIPTION_STORE[report_id] = job_description

        candidates_list = final_state.get("candidates") or []
        assert isinstance(candidates_list, list)

        for cand in candidates_list:
            assert isinstance(cand, Candidate)
            CANDIDATE_STORE[cand.id] = cand

        # Store structured LLM qualitative analysis details
        for cand_id, val in final_state.get("llm_analysis", {}).items():
            LLM_ANALYSIS_STORE[cand_id] = val
            prompt = (
                "candidate_analysis\n"
                f"job_description_id={report_id}\n"
                f"candidate_id={cand_id}\n"
                "Source prompt template is managed by PromptLoader."
            )
            _record_prompt_history(
                "candidate_analysis",
                prompt,
                val,
                final_state.get("timing", {}).get("llm_analysis", 0.0),
            )

        for ranking in report.rankings:
            candidate = CANDIDATE_STORE.get(ranking.candidate_id)
            if candidate:
                AUDIT_LOG_STORE.append(_audit_record(report, candidate, ranking))

        # Broadcast completed status
        await manager.broadcast({
            "type": "completed",
            "stage": "completed",
            "status": "success",
            "message": "Screening completed successfully!",
            "report_id": report_id
        })

        return SuccessResponse(
            message="Resume screening completed successfully.",
            data={
                "report_id": report_id,
                "candidates_count": len(report.rankings),
                "job_title": report.job_title
            }
        )
    except Exception as e:
        logger.error(f"Screening pipeline error: {str(e)}")
        await manager.broadcast({
            "type": "error",
            "stage": "failed",
            "status": "error",
            "message": f"Screening failed: {str(e)}"
        })
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Screening workflow failed: {str(e)}"
        ) from e


@router.post("/compare", response_model=SuccessResponse[CandidateComparisonResponse])
async def compare_candidates(
    payload: ComparisonRequest,
) -> SuccessResponse[CandidateComparisonResponse]:
    """Compares two or three candidates using existing report scores and analysis."""
    report_id = GLOBAL_STATE.get("last_report_id")
    if not report_id or report_id not in RESULTS_STORE:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No screening report found. Run screening before comparing candidates.",
        )

    initial_state = {
        "candidate_ids": payload.candidate_ids,
        "candidates": CANDIDATE_STORE,
        "report": RESULTS_STORE[report_id],
        "llm_analysis": LLM_ANALYSIS_STORE,
        "comparison_items": [],
        "chart_data": {},
        "errors": [],
    }

    final_state = await comparison_graph.ainvoke(initial_state)
    errors = final_state.get("errors") or []
    if errors:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="; ".join(errors),
        )

    response = final_state.get("response")
    if not isinstance(response, CandidateComparisonResponse):
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Comparison workflow completed without a response payload.",
        )

    return SuccessResponse(
        message="Candidate comparison generated successfully.",
        data=response,
    )


@router.post("/chat", response_model=SuccessResponse[ChatResponse])
async def recruiter_chat(payload: ChatRequest) -> SuccessResponse[ChatResponse]:
    """Answers recruiter questions using only current screening session data."""
    report_id = GLOBAL_STATE.get("last_report_id")
    report = RESULTS_STORE.get(report_id) if report_id else None
    job_description = JOB_DESCRIPTION_STORE.get(report_id) if report_id else None
    history = CHAT_HISTORY_STORE.get(payload.session_id, [])

    final_state = await recruiter_chat_graph.ainvoke(
        {
            "session_id": payload.session_id,
            "question": payload.question,
            "job_description": job_description,
            "candidates": CANDIDATE_STORE,
            "report": report,
            "llm_analysis": LLM_ANALYSIS_STORE,
            "history": history,
            "errors": [],
        }
    )

    updated_history = final_state.get("updated_history") or []
    CHAT_HISTORY_STORE[payload.session_id] = updated_history

    answer = final_state.get("answer")
    if answer is None:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Recruiter chat workflow completed without an answer.",
        )

    return SuccessResponse(
        message="Recruiter assistant response generated.",
        data=ChatResponse(
            session_id=payload.session_id,
            message=answer,
            history=updated_history,
        ),
    )


@router.get("/chat/history", response_model=SuccessResponse[dict[str, Any]])
async def get_chat_history(session_id: str = "default") -> SuccessResponse[dict[str, Any]]:
    """Returns chat messages persisted for the current in-memory session."""
    return SuccessResponse(
        message="Chat history retrieved.",
        data={
            "session_id": session_id,
            "messages": CHAT_HISTORY_STORE.get(session_id, []),
        },
    )


@router.delete("/chat/history", response_model=SuccessResponse[dict[str, Any]])
async def clear_chat_history(session_id: str = "default") -> SuccessResponse[dict[str, Any]]:
    """Clears chat history for a recruiter assistant session."""
    CHAT_HISTORY_STORE[session_id] = []
    return SuccessResponse(
        message="Chat history cleared.",
        data={"session_id": session_id, "messages": []},
    )


@router.get("/explain/{candidate_id}", response_model=SuccessResponse[CandidateExplainabilityResponse])
async def explain_candidate(candidate_id: str) -> SuccessResponse[CandidateExplainabilityResponse]:
    """Returns explainable AI details for one candidate decision."""
    explanation = _explain_candidate(candidate_id)
    _record_prompt_history(
        "candidate_explainability",
        f"Explain candidate_id={candidate_id} using stored scores, JD requirements, and parsed resume fields.",
        explanation.model_dump(),
        0.0,
    )
    return SuccessResponse(
        message="Candidate explainability generated successfully.",
        data=explanation,
    )


@router.get("/audit", response_model=None)
async def get_audit_log(
    search: str | None = None,
    recommendation: str | None = None,
    sort_by: str = "timestamp",
    order: str = "desc",
    format: str = "json",
) -> Any:
    """Returns searchable, sortable decision audit records."""
    _latest_report()
    records = list(AUDIT_LOG_STORE)
    if not records:
        report_id, report = _latest_report()
        for ranking in report.rankings:
            candidate = CANDIDATE_STORE.get(ranking.candidate_id)
            if candidate:
                records.append(_audit_record(report, candidate, ranking))
        AUDIT_LOG_STORE.extend(records)

    if search:
        query = search.lower()
        records = [
            record
            for record in records
            if query in record.candidate_id.lower()
            or query in record.candidate_name.lower()
            or query in record.jd_id.lower()
        ]
    if recommendation:
        records = [
            record
            for record in records
            if record.recommendation.lower() == recommendation.lower()
        ]

    reverse = order.lower() != "asc"
    if sort_by in {"timestamp", "candidate_name", "recommendation", "jd_id"}:
        records = sorted(records, key=lambda record: getattr(record, sort_by), reverse=reverse)

    if format.lower() == "csv":
        out_path = Path("data/outputs/xai/audit_log.csv")
        out_path.parent.mkdir(parents=True, exist_ok=True)
        with open(out_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(["Timestamp", "Candidate ID", "Candidate Name", "JD ID", "Recommendation", "Model", "Embedding Model", "Version"])
            for record in records:
                writer.writerow([
                    record.timestamp.isoformat(),
                    record.candidate_id,
                    record.candidate_name,
                    record.jd_id,
                    record.recommendation,
                    record.model_used,
                    record.embedding_model,
                    record.version,
                ])
        return FileResponse(path=out_path, filename="decision_audit_log.csv", media_type="text/csv")

    return SuccessResponse(
        message="Audit log retrieved successfully.",
        data={"records": [record.model_dump() for record in records]},
    )


@router.get("/graph/execution", response_model=SuccessResponse[GraphExecutionResponse])
async def get_graph_execution() -> SuccessResponse[GraphExecutionResponse]:
    """Returns observable LangGraph execution details for the latest run."""
    report_id, _report = _latest_report()
    graph = GRAPH_TRACE_STORE.get(report_id) or GraphExecutionResponse(report_id=report_id)
    return SuccessResponse(
        message="Graph execution retrieved successfully.",
        data=graph,
    )


@router.get("/graph/timeline", response_model=SuccessResponse[dict[str, Any]])
async def get_graph_timeline() -> SuccessResponse[dict[str, Any]]:
    """Returns the LangGraph node timeline for the latest run."""
    report_id, _report = _latest_report()
    graph = GRAPH_TRACE_STORE.get(report_id) or GraphExecutionResponse(report_id=report_id)
    return SuccessResponse(
        message="Graph timeline retrieved successfully.",
        data={
            "report_id": report_id,
            "timeline": [step.model_dump() for step in graph.timeline],
            "performance_metrics": graph.performance_metrics,
        },
    )


@router.get("/prompt-history", response_model=SuccessResponse[dict[str, Any]])
async def get_prompt_history() -> SuccessResponse[dict[str, Any]]:
    """Returns sanitized prompt-inspector records."""
    if not PROMPT_HISTORY_STORE:
        for key, template in PromptLoader.TEMPLATES.items():
            _record_prompt_history(
                key,
                template,
                {"schema": "template_only", "api_keys": "redacted"},
                0.0,
            )
    return SuccessResponse(
        message="Prompt history retrieved successfully.",
        data={"records": [record.model_dump() for record in PROMPT_HISTORY_STORE]},
    )


@router.get("/analytics", response_model=SuccessResponse[HiringAnalyticsResponse])
async def get_hiring_analytics() -> SuccessResponse[HiringAnalyticsResponse]:
    """Returns recruitment analytics for the latest screening report."""
    executive_report = await _build_executive_report()
    return SuccessResponse(
        message="Hiring analytics generated successfully.",
        data=executive_report.analytics,
    )


@router.get("/executive-summary", response_model=SuccessResponse[ExecutiveSummaryResponse])
async def get_executive_summary() -> SuccessResponse[ExecutiveSummaryResponse]:
    """Returns the executive hiring summary for the latest screening report."""
    executive_report = await _build_executive_report()
    return SuccessResponse(
        message="Executive summary generated successfully.",
        data=executive_report.executive_summary,
    )


@router.get("/insights", response_model=SuccessResponse[HiringInsightsResponse])
async def get_hiring_insights() -> SuccessResponse[HiringInsightsResponse]:
    """Returns team fit, risk, and interview-planning insights."""
    executive_report = await _build_executive_report()
    return SuccessResponse(
        message="Hiring insights generated successfully.",
        data=executive_report.insights,
    )


@router.get("/hiring-report", response_model=None)
async def get_hiring_report(
    format: str = "json",
    download: bool = False,
) -> Any:
    """Returns or downloads the complete executive hiring intelligence report."""
    executive_report = await _build_executive_report()
    normalized_format = format.lower().strip()

    if normalized_format == "json" and not download:
        return SuccessResponse(
            message="Executive hiring report generated successfully.",
            data=executive_report.model_dump(),
        )

    out_dir = Path("data/outputs/executive")
    timestamp = datetime.utcnow().strftime("%Y%m%d%H%M%S")

    if normalized_format == "csv":
        out_path = out_dir / f"hiring_analytics_{timestamp}.csv"
        _analytics_csv(executive_report, out_path)
        return FileResponse(
            path=out_path,
            filename="hiring_analytics.csv",
            media_type="text/csv",
        )

    if normalized_format in {"markdown", "md"}:
        out_path = out_dir / f"executive_hiring_report_{timestamp}.md"
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(_executive_markdown(executive_report), encoding="utf-8")
        return FileResponse(
            path=out_path,
            filename="executive_hiring_report.md",
            media_type="text/markdown",
        )

    if normalized_format == "pdf":
        markdown_lines = _executive_markdown(executive_report).splitlines()
        out_path = out_dir / f"executive_hiring_report_{timestamp}.pdf"
        _write_simple_pdf(markdown_lines, out_path)
        return FileResponse(
            path=out_path,
            filename="executive_hiring_report.pdf",
            media_type="application/pdf",
        )

    if normalized_format == "json":
        out_path = out_dir / f"hiring_analytics_{timestamp}.json"
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(
            json.dumps(executive_report.analytics.model_dump(), indent=2, default=str),
            encoding="utf-8",
        )
        return FileResponse(
            path=out_path,
            filename="hiring_analytics.json",
            media_type="application/json",
        )

    raise HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail="Unsupported report format. Use json, csv, markdown, or pdf.",
    )


# Retrieve current screening results
@router.get("/results")
async def get_results() -> SuccessResponse[dict[str, Any]]:
    """Retrieves the rankings and score breakdowns from the latest screening report."""
    report_id = GLOBAL_STATE.get("last_report_id")
    if not report_id or report_id not in RESULTS_STORE:
        return SuccessResponse(
            message="No screening results found.",
            data={"rankings": [], "job_title": None, "report_id": None}
        )

    report = RESULTS_STORE[report_id]
    return SuccessResponse(
        message="Rankings and screening results retrieved.",
        data={
            "report_id": report_id,
            "job_title": report.job_title,
            "evaluation_timestamp": report.evaluation_timestamp.isoformat(),
            "rankings": [r.model_dump() for r in report.rankings]
        }
    )


# Retrieve single candidate profile
@router.get("/candidate/{candidate_id}")
async def get_candidate_details(candidate_id: str) -> SuccessResponse[dict[str, Any]]:
    """Retrieves candidate structured profile matching ID."""
    if candidate_id not in CANDIDATE_STORE:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Candidate with ID '{candidate_id}' not found."
        )

    candidate = CANDIDATE_STORE[candidate_id]

    # Retrieve score matching candidate from last report
    report_id = GLOBAL_STATE.get("last_report_id")
    score_details = None
    if report_id and report_id in RESULTS_STORE:
        report = RESULTS_STORE[report_id]
        for ranking in report.rankings:
            if ranking.candidate_id == candidate_id:
                score_details = ranking.score.model_dump()
                break

    return SuccessResponse(
        message="Candidate details retrieved.",
        data={
            "profile": candidate.model_dump(),
            "score": score_details,
            "analysis": LLM_ANALYSIS_STORE.get(candidate_id)
        }
    )


# Download files
@router.get("/download/csv")
async def download_csv() -> FileResponse:
    """Generates and downloads CSV format report."""
    report_id = GLOBAL_STATE.get("last_report_id")
    if not report_id or report_id not in RESULTS_STORE:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No screening reports found to export."
        )

    report = RESULTS_STORE[report_id]
    out_dir = Path("data/outputs")
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / "screening_report.csv"

    exporter = ReportExporter()
    exporter.export_csv(report, str(out_path))

    return FileResponse(
        path=out_path,
        filename="resume_screening_report.csv",
        media_type="text/csv"
    )


@router.get("/download/json")
async def download_json() -> FileResponse:
    """Generates and downloads JSON format report."""
    report_id = GLOBAL_STATE.get("last_report_id")
    if not report_id or report_id not in RESULTS_STORE:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No screening reports found to export."
        )

    report = RESULTS_STORE[report_id]
    out_dir = Path("data/outputs")
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / "screening_report.json"

    exporter = ReportExporter()
    exporter.export_json(report, str(out_path))

    return FileResponse(
        path=out_path,
        filename="resume_screening_report.json",
        media_type="application/json"
    )


@router.get("/download/report")
async def download_report() -> FileResponse:
    """Generates and downloads Markdown format report."""
    report_id = GLOBAL_STATE.get("last_report_id")
    if not report_id or report_id not in RESULTS_STORE:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No screening reports found to export."
        )

    report = RESULTS_STORE[report_id]
    out_dir = Path("data/outputs")
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / "screening_report.md"

    exporter = ReportExporter()
    exporter.export_markdown_report(report, str(out_path))

    return FileResponse(
        path=out_path,
        filename="resume_screening_report.md",
        media_type="text/markdown"
    )
