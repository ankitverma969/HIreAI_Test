from collections import Counter
from typing import Any, TypedDict, cast

from langgraph.graph import END, StateGraph
from loguru import logger
from pydantic import BaseModel, Field

from app.extractor.skills_database import SKILL_CATEGORIES
from app.llm.client import get_llm_client
from app.models.candidate import Candidate
from app.models.hiring_assistant import (
    AIComparisonSummary,
    CandidateComparisonItem,
    CandidateComparisonResponse,
    ChatAnswer,
    ChatMessage,
    ComparisonHighlights,
    DiversityMetrics,
    ExecutiveCandidate,
    ExecutiveSummaryResponse,
    HiringAnalyticsResponse,
    HiringInsightsResponse,
    HiringReportResponse,
    HiringRiskItem,
    InterviewPlanItem,
    KeyCount,
    TeamFitRecommendation,
)
from app.models.job_description import JobDescription
from app.models.report import Report
from app.models.score import Ranking
from app.prompts.loader import PromptLoader

NOT_ENOUGH_INFORMATION = "The uploaded resumes do not contain enough information."


class ComparisonState(TypedDict, total=False):
    candidate_ids: list[str]
    candidates: dict[str, Candidate]
    report: Report | None
    llm_analysis: dict[str, dict[str, Any]]
    comparison_items: list[CandidateComparisonItem]
    highlights: ComparisonHighlights
    ai_summary: AIComparisonSummary
    chart_data: dict[str, Any]
    response: CandidateComparisonResponse
    errors: list[str]


class RecruiterChatState(TypedDict, total=False):
    session_id: str
    question: str
    job_description: JobDescription | None
    candidates: dict[str, Candidate]
    report: Report | None
    llm_analysis: dict[str, dict[str, Any]]
    history: list[ChatMessage]
    context: dict[str, Any]
    answer: ChatAnswer
    updated_history: list[ChatMessage]
    errors: list[str]


class ExecutiveHiringState(TypedDict, total=False):
    report_id: str
    job_description: JobDescription | None
    candidates: dict[str, Candidate]
    report: Report | None
    llm_analysis: dict[str, dict[str, Any]]
    analytics: HiringAnalyticsResponse
    summary: ExecutiveSummaryResponse
    risks: list[HiringRiskItem]
    insights: HiringInsightsResponse
    response: HiringReportResponse
    errors: list[str]


class ExecutiveNarrative(BaseModel):
    """Structured LLM narrative for executive hiring intelligence."""

    overall_hiring_summary: str
    hiring_risks: list[str] = Field(default_factory=list)
    interview_priorities: list[str] = Field(default_factory=list)
    overall_recommendation: str
    executive_insights: list[str] = Field(default_factory=list)


def _rankings_by_candidate(report: Report | None) -> dict[str, Ranking]:
    if not report:
        return {}
    return {ranking.candidate_id: ranking for ranking in report.rankings}


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


def _candidate_name(candidate: Candidate | None) -> str | None:
    return candidate.full_name if candidate and candidate.full_name else None


def _build_comparison_item(
    candidate: Candidate,
    ranking: Ranking,
    analysis: dict[str, Any] | None,
) -> CandidateComparisonItem:
    score = ranking.score
    breakdown = score.breakdown
    recommendation = (analysis or {}).get("recommendation") or _recommendation_from_score(
        score.overall_score
    )

    return CandidateComparisonItem(
        candidate_id=candidate.id,
        candidate_name=candidate.full_name or "Candidate Name",
        rank=ranking.rank,
        recommendation=recommendation,
        overall_score=score.overall_score,
        skill_match=breakdown.skill_match,
        experience_match=breakdown.experience_match,
        education_match=breakdown.education_match,
        project_match=breakdown.project_match,
        certification_match=breakdown.certification_match,
        semantic_similarity=breakdown.semantic_similarity,
        confidence_score=score.confidence_score,
        total_experience_years=candidate.total_experience_years,
        matched_skills=score.matched_skills,
        missing_skills=score.missing_skills,
        strengths=list((analysis or {}).get("strengths") or []),
        weaknesses=list((analysis or {}).get("weaknesses") or []),
    )


def candidate_comparison_node(state: ComparisonState) -> ComparisonState:
    """CandidateComparisonNode: loads existing scores into comparison rows."""
    candidate_ids = state.get("candidate_ids") or []
    candidates = state.get("candidates") or {}
    rankings = _rankings_by_candidate(state.get("report"))
    analysis = state.get("llm_analysis") or {}
    errors: list[str] = []
    items: list[CandidateComparisonItem] = []

    if not 2 <= len(candidate_ids) <= 3:
        errors.append("Select exactly 2 or 3 candidates to compare.")

    for candidate_id in candidate_ids:
        candidate = candidates.get(candidate_id)
        ranking = rankings.get(candidate_id)
        if not candidate:
            errors.append(f"Candidate '{candidate_id}' was not found in the current session.")
            continue
        if not ranking:
            errors.append(f"Candidate '{candidate_id}' does not have ranking results.")
            continue
        items.append(_build_comparison_item(candidate, ranking, analysis.get(candidate_id)))

    if errors:
        return {**state, "errors": errors, "comparison_items": items}

    best = max(items, key=lambda item: item.overall_score)
    experienced = max(items, key=lambda item: item.total_experience_years)
    skill = max(items, key=lambda item: item.skill_match)
    complete = max(items, key=lambda item: item.confidence_score)

    highlights = ComparisonHighlights(
        best_candidate_id=best.candidate_id,
        best_candidate_name=best.candidate_name,
        most_experienced_id=experienced.candidate_id,
        most_experienced_name=experienced.candidate_name,
        highest_skill_match_id=skill.candidate_id,
        highest_skill_match_name=skill.candidate_name,
        most_complete_resume_id=complete.candidate_id,
        most_complete_resume_name=complete.candidate_name,
    )

    return {
        **state,
        "comparison_items": items,
        "highlights": highlights,
        "errors": [],
    }


def _fallback_comparison_summary(
    items: list[CandidateComparisonItem],
    highlights: ComparisonHighlights,
) -> AIComparisonSummary:
    ordered = sorted(items, key=lambda item: item.overall_score, reverse=True)
    top = ordered[0]
    runner_up = ordered[1] if len(ordered) > 1 else ordered[0]

    top_edges = []
    if top.skill_match >= runner_up.skill_match:
        top_edges.append("skill alignment")
    if top.experience_match >= runner_up.experience_match:
        top_edges.append("experience alignment")
    if top.confidence_score >= runner_up.confidence_score:
        top_edges.append("resume completeness confidence")

    edge_text = ", ".join(top_edges) if top_edges else "the existing weighted score"
    missing = top.missing_skills or runner_up.missing_skills
    risk_text = (
        f"Key risks to validate are missing skills such as {', '.join(missing[:5])}."
        if missing
        else "The available scoring output does not flag major required-skill gaps."
    )

    return AIComparisonSummary(
        executive_comparison=(
            f"{top.candidate_name} is the strongest option among the selected candidates "
            f"with an overall score of {top.overall_score}%."
        ),
        why_ranked_higher=(
            f"{top.candidate_name} ranks above {runner_up.candidate_name} because the "
            f"existing scoring results show stronger {edge_text}. No new score was calculated."
        ),
        strength_comparison=(
            f"{highlights.highest_skill_match_name or top.candidate_name} has the highest "
            "skill-match signal, while "
            f"{highlights.most_experienced_name or top.candidate_name} has the most experience."
        ),
        risk_comparison=risk_text,
        interview_recommendation=(
            f"Interview {top.candidate_name} first, then use targeted questions to validate "
            "the missing-skills and project-depth gaps shown in the comparison table."
        ),
        hiring_recommendation=(
            f"Prioritize {top.candidate_name} for the role based on the existing ranking, "
            "confidence, and score breakdown."
        ),
    )


def comparison_analysis_node(state: ComparisonState) -> ComparisonState:
    """Uses structured LLM output to explain existing comparison results."""
    items = state.get("comparison_items") or []
    highlights = state.get("highlights") or ComparisonHighlights()
    errors = state.get("errors") or []
    if errors or not items:
        return {**state, "errors": errors}

    fallback = _fallback_comparison_summary(items, highlights)
    try:
        llm = get_llm_client()
        structured_llm = llm.with_structured_output(AIComparisonSummary)
        prompt = PromptLoader.get_prompt(
            "candidate_comparison",
            comparison_rows="\n".join(item.model_dump_json() for item in items),
            highlights=highlights.model_dump_json(),
        )
        result = structured_llm.invoke(prompt)
        summary = cast(AIComparisonSummary, result)

        if summary.executive_comparison.lower().startswith("mock "):
            summary = fallback
    except Exception as exc:
        logger.warning(f"Comparison LLM explanation failed, using deterministic explanation: {exc}")
        summary = fallback

    return {**state, "ai_summary": summary}


def comparison_visualization_node(state: ComparisonState) -> ComparisonState:
    """Builds chart-friendly data without changing business scores."""
    items = state.get("comparison_items") or []
    errors = state.get("errors") or []
    if errors:
        return {**state, "errors": errors}

    metric_keys = [
        ("Overall", "overall_score"),
        ("Skills", "skill_match"),
        ("Experience", "experience_match"),
        ("Education", "education_match"),
        ("Projects", "project_match"),
        ("Certifications", "certification_match"),
        ("Semantic", "semantic_similarity"),
        ("Confidence", "confidence_score"),
    ]

    radar = []
    for label, key in metric_keys:
        row: dict[str, Any] = {"metric": label}
        for item in items:
            row[item.candidate_name] = getattr(item, key)
        radar.append(row)

    bars = [
        {
            "candidate_id": item.candidate_id,
            "candidate_name": item.candidate_name,
            "overall_score": item.overall_score,
            "skill_match": item.skill_match,
            "experience_match": item.experience_match,
            "confidence_score": item.confidence_score,
        }
        for item in items
    ]

    all_skills = sorted({skill for item in items for skill in item.matched_skills + item.missing_skills})
    heatmap = [
        {
            "skill": skill,
            **{
                item.candidate_name: (
                    "matched"
                    if skill in item.matched_skills
                    else "missing"
                    if skill in item.missing_skills
                    else "not_applicable"
                )
                for item in items
            },
        }
        for skill in all_skills
    ]

    breakdown = [
        {
            "candidate_id": item.candidate_id,
            "candidate_name": item.candidate_name,
            "metrics": {
                "skill_match": item.skill_match,
                "experience_match": item.experience_match,
                "education_match": item.education_match,
                "project_match": item.project_match,
                "certification_match": item.certification_match,
                "semantic_similarity": item.semantic_similarity,
                "confidence_score": item.confidence_score,
            },
        }
        for item in items
    ]

    return {
        **state,
        "chart_data": {
            "radar": radar,
            "bars": bars,
            "skill_heatmap": heatmap,
            "score_breakdown": breakdown,
        },
    }


def comparison_response_node(state: ComparisonState) -> ComparisonState:
    errors = state.get("errors") or []
    if errors:
        return {**state, "errors": errors}
    response = CandidateComparisonResponse(
        candidates=state.get("comparison_items") or [],
        highlights=state.get("highlights") or ComparisonHighlights(),
        ai_summary=state.get("ai_summary")
        or _fallback_comparison_summary(
            state.get("comparison_items") or [],
            state.get("highlights") or ComparisonHighlights(),
        ),
        chart_data=state.get("chart_data") or {},
    )
    return {**state, "response": response}


def context_retrieval_node(state: RecruiterChatState) -> RecruiterChatState:
    """ContextRetrievalNode: selects only current session entities relevant to a question."""
    question = (state.get("question") or "").strip()
    question_lower = question.lower()
    report = state.get("report")
    candidates = state.get("candidates") or {}
    rankings = _rankings_by_candidate(report)
    history = state.get("history") or []

    focus_ids: list[str] = []
    for candidate_id, candidate in candidates.items():
        name = (candidate.full_name or "").lower()
        first_name = name.split()[0] if name else ""
        if name and name in question_lower:
            focus_ids.append(candidate_id)
        elif first_name and first_name in question_lower:
            focus_ids.append(candidate_id)

    if not focus_ids and any(token in question_lower for token in ("they", "their", "them", "he", "she")):
        for message in reversed(history):
            cited = message.metadata.get("cited_candidates") if message.metadata else None
            if cited:
                focus_ids = [cid for cid in cited if cid in candidates]
                break

    if not focus_ids and "first" in question_lower and report and report.rankings:
        focus_ids = [report.rankings[0].candidate_id]

    context = {
        "question": question,
        "question_lower": question_lower,
        "focus_candidate_ids": focus_ids,
        "rankings": rankings,
        "report": report,
        "candidates": candidates,
        "job_description": state.get("job_description"),
        "llm_analysis": state.get("llm_analysis") or {},
    }
    return {**state, "context": context}


def _candidate_skill_match(candidate: Candidate, term: str) -> bool:
    term_lower = term.lower()
    if any(term_lower == skill.lower() for skill in candidate.skills):
        return True
    return term_lower in candidate.raw_resume_text.lower()


def _extract_skill_query(question_lower: str) -> str | None:
    known_terms = [
        "python",
        "aws",
        "machine learning",
        "react",
        "docker",
        "langgraph",
        "fastapi",
        "sql",
        "postgresql",
        "kubernetes",
        "typescript",
    ]
    for term in known_terms:
        if term in question_lower:
            return term
    return None


def _ranking_line(ranking: Ranking) -> str:
    return (
        f"{ranking.candidate_name} is ranked #{ranking.rank} with an overall score "
        f"of {ranking.score.overall_score}% and confidence {ranking.score.confidence_score}%."
    )


def _ranking_rationale_markdown(
    ranking: Ranking,
    analysis: dict[str, Any] | None = None,
) -> str:
    breakdown = ranking.score.breakdown
    strengths = list((analysis or {}).get("strengths") or [])[:3]
    missing = ranking.score.missing_skills[:5]

    rows = [
        f"**{ranking.candidate_name}** is ranked #{ranking.rank} based on the existing screening report.",
        "",
        f"- Overall score: {ranking.score.overall_score}%",
        f"- Skill match: {breakdown.skill_match}%",
        f"- Experience match: {breakdown.experience_match}%",
        f"- Semantic similarity: {breakdown.semantic_similarity}%",
        f"- Confidence score: {ranking.score.confidence_score}%",
    ]
    if ranking.score.matched_skills:
        rows.append(f"- Matched skills: {', '.join(ranking.score.matched_skills[:8])}")
    if missing:
        rows.append(f"- Risks to validate: {', '.join(missing)}")
    if strengths:
        rows.append(f"- Reported strengths: {', '.join(strengths)}")
    return "\n".join(rows)


def recruiter_chat_node(state: RecruiterChatState) -> RecruiterChatState:
    """RecruiterChatNode: creates an evidence-backed structured chat answer."""
    context = state.get("context") or {}
    question_lower = context.get("question_lower", "")
    report = cast(Report | None, context.get("report"))
    candidates = cast(dict[str, Candidate], context.get("candidates") or {})
    rankings = cast(dict[str, Ranking], context.get("rankings") or {})
    focus_ids = cast(list[str], context.get("focus_candidate_ids") or [])
    analysis = cast(dict[str, dict[str, Any]], context.get("llm_analysis") or {})

    unavailable = ChatAnswer(
        answer_markdown=NOT_ENOUGH_INFORMATION,
        direct_answer=NOT_ENOUGH_INFORMATION,
        unavailable=True,
        confidence=0.0,
        follow_up_suggestions=[
            "Run a screening workflow first.",
            "Ask about ranked candidates after results are available.",
        ],
    )

    if not report or not report.rankings or not candidates:
        return {**state, "answer": unavailable}

    cited_candidates: list[str] = []
    cited_fields: list[str] = []
    direct = ""
    markdown = ""
    confidence = 85.0

    if "ranked first" in question_lower or "rank first" in question_lower or "who ranked first" in question_lower:
        ranking = rankings.get(focus_ids[0]) if focus_ids else report.rankings[0]
        if not ranking:
            return {**state, "answer": unavailable}

        cited_candidates = [ranking.candidate_id]
        cited_fields = [
            "rankings",
            "overall_score",
            "score_breakdown",
            "confidence_score",
            "matched_skills",
            "missing_skills",
        ]
        direct = _ranking_line(ranking)
        if "why" in question_lower:
            markdown = _ranking_rationale_markdown(
                ranking,
                analysis.get(ranking.candidate_id),
            )
        else:
            markdown = f"**{ranking.candidate_name}** is ranked first.\n\n{direct}"

    elif "best matches" in question_lower or "interviewed first" in question_lower or "interview first" in question_lower:
        ranking = report.rankings[0]
        cited_candidates = [ranking.candidate_id]
        cited_fields = ["rankings", "score_breakdown", "matched_skills"]
        direct = f"{ranking.candidate_name} should be prioritized based on the current ranking."
        markdown = (
            f"**{ranking.candidate_name}** should be interviewed first based on the current report.\n\n"
            f"- Overall score: {ranking.score.overall_score}%\n"
            f"- Skill match: {ranking.score.breakdown.skill_match}%\n"
            f"- Matched skills: {', '.join(ranking.score.matched_skills) or 'None listed'}"
        )

    elif "highest confidence" in question_lower or "confidence score" in question_lower:
        ranking = max(report.rankings, key=lambda row: row.score.confidence_score)
        cited_candidates = [ranking.candidate_id]
        cited_fields = ["confidence_score"]
        direct = f"{ranking.candidate_name} has the highest confidence score at {ranking.score.confidence_score}%."
        markdown = f"**{ranking.candidate_name}** has the highest confidence score: **{ranking.score.confidence_score}%**."

    elif "commonly missing" in question_lower or "common missing" in question_lower:
        counter: Counter[str] = Counter()
        for ranking in report.rankings:
            counter.update(ranking.score.missing_skills)
        common = counter.most_common(8)
        if not common:
            return {**state, "answer": unavailable}
        cited_fields = ["missing_skills"]
        direct = ", ".join(skill for skill, _count in common)
        markdown = "**Commonly missing skills:**\n" + "\n".join(
            f"- {skill}: missing in {count} candidate(s)" for skill, count in common
        )

    elif any(word in question_lower for word in ("strongest", "know", "knows", "experience", "mention", "mentions", "with")):
        skill = _extract_skill_query(question_lower)
        if skill:
            matches = [
                candidate
                for candidate in candidates.values()
                if _candidate_skill_match(candidate, skill)
            ]
            if not matches:
                return {**state, "answer": unavailable}
            matches.sort(
                key=lambda cand: (
                    rankings.get(cand.id).score.breakdown.skill_match if rankings.get(cand.id) else 0.0,
                    rankings.get(cand.id).score.overall_score if rankings.get(cand.id) else 0.0,
                ),
                reverse=True,
            )
            cited_candidates = [candidate.id for candidate in matches]
            cited_fields = ["skills", "raw_resume_text", "rankings"]
            direct = f"{', '.join(candidate.full_name or candidate.id for candidate in matches)} mention {skill}."
            markdown = f"**Candidates with {skill}:**\n" + "\n".join(
                f"- {candidate.full_name or candidate.id}: "
                f"rank #{rankings[candidate.id].rank if candidate.id in rankings else 'N/A'}, "
                f"overall {rankings[candidate.id].score.overall_score if candidate.id in rankings else 'N/A'}%"
                for candidate in matches
            )

    elif "project" in question_lower and focus_ids:
        rows = []
        for candidate_id in focus_ids:
            candidate = candidates.get(candidate_id)
            if not candidate or not candidate.projects:
                continue
            cited_candidates.append(candidate_id)
            for project in candidate.projects:
                rows.append(
                    f"- **{project.project_name or 'Project'}**: "
                    f"{project.description or 'No description listed'}"
                )
        if not rows:
            return {**state, "answer": unavailable}
        cited_fields = ["projects"]
        direct = "The referenced candidate projects are listed in the answer."
        markdown = "**Referenced candidate projects:**\n" + "\n".join(rows)

    elif "missing" in question_lower and focus_ids:
        rows = []
        for candidate_id in focus_ids:
            ranking = rankings.get(candidate_id)
            if not ranking:
                continue
            cited_candidates.append(candidate_id)
            missing = ranking.score.missing_skills
            rows.append(
                f"- **{ranking.candidate_name}**: {', '.join(missing) if missing else 'No required skills missing'}"
            )
        if not rows:
            return {**state, "answer": unavailable}
        cited_fields = ["missing_skills"]
        direct = "The referenced candidate missing skills are listed in the answer."
        markdown = "**Missing skills:**\n" + "\n".join(rows)

    else:
        skill = _extract_skill_query(question_lower)
        if skill:
            matches = [candidate for candidate in candidates.values() if _candidate_skill_match(candidate, skill)]
            if not matches:
                return {**state, "answer": unavailable}
            cited_candidates = [candidate.id for candidate in matches]
            cited_fields = ["skills", "raw_resume_text"]
            direct = f"{', '.join(candidate.full_name or candidate.id for candidate in matches)} mention {skill}."
            markdown = f"**Candidates mentioning {skill}:**\n" + "\n".join(
                f"- {candidate.full_name or candidate.id}" for candidate in matches
            )
        else:
            return {**state, "answer": unavailable}

    answer = ChatAnswer(
        answer_markdown=markdown,
        direct_answer=direct,
        unavailable=False,
        confidence=confidence,
        cited_candidates=cited_candidates,
        cited_fields=cited_fields,
        follow_up_suggestions=[
            "What skills are missing?",
            "What projects did they build?",
            "Who should be interviewed first?",
        ],
    )
    return {**state, "answer": answer}


def answer_generation_node(state: RecruiterChatState) -> RecruiterChatState:
    """AnswerGenerationNode: final guardrail ensuring structured, non-hallucinated output."""
    answer = state.get("answer")
    if not answer:
        answer = ChatAnswer(
            answer_markdown=NOT_ENOUGH_INFORMATION,
            direct_answer=NOT_ENOUGH_INFORMATION,
            unavailable=True,
            confidence=0.0,
        )
    return {**state, "answer": answer}


def conversation_memory_node(state: RecruiterChatState) -> RecruiterChatState:
    """ConversationMemoryNode: appends the current turn to session history."""
    history = list(state.get("history") or [])
    question = state.get("question") or ""
    answer = state.get("answer") or ChatAnswer(
        answer_markdown=NOT_ENOUGH_INFORMATION,
        direct_answer=NOT_ENOUGH_INFORMATION,
        unavailable=True,
    )

    history.append(ChatMessage(role="user", content=question))
    history.append(
        ChatMessage(
            role="assistant",
            content=answer.answer_markdown,
            metadata={
                "cited_candidates": answer.cited_candidates,
                "cited_fields": answer.cited_fields,
                "unavailable": answer.unavailable,
            },
        )
    )
    return {**state, "updated_history": history}


def _top_counts(values: list[str], limit: int | None = None) -> list[KeyCount]:
    counter = Counter(value for value in values if value)
    rows = [KeyCount(name=name, count=count) for name, count in counter.most_common(limit)]
    return rows


def _candidate_for_ranking(
    ranking: Ranking,
    candidates: dict[str, Candidate],
) -> Candidate | None:
    return candidates.get(ranking.candidate_id)


def _score_component_names(ranking: Ranking) -> list[tuple[str, float]]:
    breakdown = ranking.score.breakdown
    return [
        ("skill alignment", breakdown.skill_match),
        ("experience alignment", breakdown.experience_match),
        ("education alignment", breakdown.education_match),
        ("project depth", breakdown.project_match),
        ("certification evidence", breakdown.certification_match),
        ("semantic alignment", breakdown.semantic_similarity),
    ]


def _lowest_focus_areas(ranking: Ranking) -> list[str]:
    components = sorted(_score_component_names(ranking), key=lambda item: item[1])
    focus = [name.title() for name, value in components if value < 75.0][:3]
    if ranking.score.missing_skills:
        focus.insert(0, f"Missing skills: {', '.join(ranking.score.missing_skills[:4])}")
    return focus[:4] or ["Validate claimed project depth and role-specific delivery"]


def _candidate_has_any(candidate: Candidate, terms: set[str]) -> bool:
    candidate_skills = {skill.lower() for skill in candidate.skills}
    text = candidate.raw_resume_text.lower()
    return bool(candidate_skills & terms) or any(term in text for term in terms)


def _fit_recommendation(
    category: str,
    rankings: list[Ranking],
    candidates: dict[str, Candidate],
    terms: set[str] | None,
    fallback_explanation: str,
) -> TeamFitRecommendation:
    eligible: list[tuple[Ranking, Candidate]] = []
    for ranking in rankings:
        candidate = _candidate_for_ranking(ranking, candidates)
        if not candidate:
            continue
        if terms is None or _candidate_has_any(candidate, terms):
            eligible.append((ranking, candidate))

    if not eligible:
        return TeamFitRecommendation(
            category=category,
            explanation=f"No candidate has enough explicit resume evidence for {category.lower()}.",
            evidence=["No matching skills or resume keywords were found."],
        )

    ranking, candidate = max(
        eligible,
        key=lambda row: (
            row[0].score.overall_score,
            row[0].score.breakdown.skill_match,
            row[1].total_experience_years,
            row[0].score.confidence_score,
        ),
    )
    evidence = [
        f"Overall score {ranking.score.overall_score}%",
        f"Skill match {ranking.score.breakdown.skill_match}%",
        f"Experience {candidate.total_experience_years} years",
    ]
    if ranking.score.matched_skills:
        evidence.append(f"Matched skills: {', '.join(ranking.score.matched_skills[:5])}")

    return TeamFitRecommendation(
        category=category,
        candidate_id=candidate.id,
        candidate_name=candidate.full_name or ranking.candidate_name,
        explanation=(
            f"{candidate.full_name or ranking.candidate_name} is the strongest {category.lower()} "
            f"based on existing score, skill, and resume evidence. {fallback_explanation}"
        ),
        evidence=evidence,
    )


def analytics_node(state: ExecutiveHiringState) -> ExecutiveHiringState:
    """AnalyticsNode: computes dashboard metrics from existing rankings and candidates."""
    report = state.get("report")
    all_candidates = state.get("candidates") or {}
    if not report or not report.rankings:
        return {**state, "errors": ["No screening report found. Run screening before analytics."]}

    candidates = {
        ranking.candidate_id: all_candidates[ranking.candidate_id]
        for ranking in report.rankings
        if ranking.candidate_id in all_candidates
    }
    total = len(report.rankings)
    scores = [ranking.score.overall_score for ranking in report.rankings]
    skill_scores = [ranking.score.breakdown.skill_match for ranking in report.rankings]

    skill_values: list[str] = []
    missing_values: list[str] = []
    technology_values: list[str] = []
    programming_values: list[str] = []
    framework_values: list[str] = []
    cloud_values: list[str] = []
    ai_values: list[str] = []
    degree_values: list[str] = []
    experience_bins = {"0-2 Years": 0, "2-5 Years": 0, "5-8 Years": 0, "8+ Years": 0}
    recommendation_values: list[str] = []

    for ranking in report.rankings:
        candidate = _candidate_for_ranking(ranking, candidates)
        recommendation_values.append(_recommendation_from_score(ranking.score.overall_score))
        missing_values.extend(ranking.score.missing_skills)

        if candidate:
            if candidate.total_experience_years < 2:
                experience_bins["0-2 Years"] += 1
            elif candidate.total_experience_years < 5:
                experience_bins["2-5 Years"] += 1
            elif candidate.total_experience_years < 8:
                experience_bins["5-8 Years"] += 1
            else:
                experience_bins["8+ Years"] += 1

            for education in candidate.education:
                degree_values.append(education.degree or "Education Listed")
            if not candidate.education:
                degree_values.append("Not Listed")

            for skill in candidate.skills:
                category = SKILL_CATEGORIES.get(skill, "Tools")
                skill_values.append(skill)
                technology_values.append(category)
                if category == "Programming":
                    programming_values.append(skill)
                elif category == "Frameworks":
                    framework_values.append(skill)
                elif category == "Cloud":
                    cloud_values.append(skill)
                elif category == "AI/ML":
                    ai_values.append(skill)

    analytics = HiringAnalyticsResponse(
        job_title=report.job_title,
        total_candidates=total,
        average_resume_score=round(sum(scores) / total, 1) if total else 0.0,
        average_experience=round(
            sum((c.total_experience_years for c in candidates.values()), 0.0) / len(candidates),
            1,
        )
        if candidates
        else 0.0,
        average_skill_match=round(sum(skill_scores) / total, 1) if total else 0.0,
        recommendation_distribution=_top_counts(recommendation_values),
        skill_frequency=_top_counts(skill_values, 10),
        experience_distribution=[KeyCount(name=name, count=count) for name, count in experience_bins.items()],
        education_distribution=_top_counts(degree_values),
        technology_distribution=_top_counts(technology_values),
        top_programming_languages=_top_counts(programming_values, 10),
        top_frameworks=_top_counts(framework_values, 10),
        cloud_skills=_top_counts(cloud_values, 10),
        ai_skills=_top_counts(ai_values, 10),
    )

    return {**state, "analytics": analytics, "errors": []}


def risk_assessment_node(state: ExecutiveHiringState) -> ExecutiveHiringState:
    """RiskAssessmentNode: identifies hiring risks from existing score signals."""
    report = state.get("report")
    candidates = state.get("candidates") or {}
    analytics = state.get("analytics")
    errors = state.get("errors") or []
    if errors or not report:
        return {**state, "errors": errors}

    risks: list[HiringRiskItem] = []
    missing = analytics.skill_frequency if analytics else []
    common_missing = _top_counts(
        [skill for ranking in report.rankings for skill in ranking.score.missing_skills],
        5,
    )
    if common_missing:
        risks.append(
            HiringRiskItem(
                category="Skill Gaps",
                severity="High" if common_missing[0].count >= max(2, len(report.rankings) // 2) else "Medium",
                description=(
                    "Required skills are repeatedly absent across the candidate pool: "
                    f"{', '.join(item.name for item in common_missing)}."
                ),
                affected_candidates=[
                    ranking.candidate_name for ranking in report.rankings if ranking.score.missing_skills
                ],
                mitigation="Use targeted technical screens for missing skills before final interviews.",
            )
        )

    risk_specs = [
        ("Experience Gaps", "experience_match", "Professional experience alignment is below target."),
        ("Education Gaps", "education_match", "Education evidence is weak or missing against the job requirements."),
        ("Certification Gaps", "certification_match", "Certification evidence is limited for the role."),
    ]
    for category, attr_name, description in risk_specs:
        affected = [
            ranking.candidate_name
            for ranking in report.rankings
            if getattr(ranking.score.breakdown, attr_name) < 60.0
        ]
        if affected:
            risks.append(
                HiringRiskItem(
                    category=category,
                    severity="Medium",
                    description=description,
                    affected_candidates=affected,
                    mitigation="Validate this area through focused interview evidence and reference checks.",
                )
            )

    confidence_affected = [
        ranking.candidate_name
        for ranking in report.rankings
        if ranking.score.confidence_score < 70.0
    ]
    if confidence_affected:
        risks.append(
            HiringRiskItem(
                category="Confidence Risks",
                severity="Medium",
                description="Some score confidence values are below the executive review threshold.",
                affected_candidates=confidence_affected,
                mitigation="Review source resumes manually before making final decisions.",
            )
        )

    quality_affected = []
    for candidate in candidates.values():
        word_count = len(candidate.raw_resume_text.split())
        if word_count < 120 or not candidate.email or not candidate.phone:
            quality_affected.append(candidate.full_name or candidate.id)
    if quality_affected:
        risks.append(
            HiringRiskItem(
                category="Resume Quality Risks",
                severity="Low",
                description="Some resumes have sparse text or incomplete contact metadata.",
                affected_candidates=quality_affected,
                mitigation="Request updated resumes or recruiter clarification for sparse profiles.",
            )
        )

    if not risks and missing:
        risks.append(
            HiringRiskItem(
                category="Hiring Risk",
                severity="Low",
                description="No major aggregate risks were detected in current scoring output.",
                affected_candidates=[],
                mitigation="Proceed with normal interview validation.",
            )
        )

    return {**state, "risks": risks}


def _fallback_narrative(
    report: Report,
    analytics: HiringAnalyticsResponse,
    risks: list[HiringRiskItem],
) -> ExecutiveNarrative:
    top_candidate = report.rankings[0] if report.rankings else None
    top_name = top_candidate.candidate_name if top_candidate else "the leading candidate"
    risk_names = [risk.category for risk in risks[:3]]
    risk_text = ", ".join(risk_names) if risk_names else "no major aggregate risks"

    return ExecutiveNarrative(
        overall_hiring_summary=(
            f"{report.job_title} has {analytics.total_candidates} evaluated candidates. "
            f"{top_name} leads the shortlist, with average pool score "
            f"{analytics.average_resume_score}% and average skill match {analytics.average_skill_match}%."
        ),
        hiring_risks=[
            risk.description for risk in risks[:5]
        ] or ["No major risks were detected from available score and resume data."],
        interview_priorities=[
            f"Interview {top_name} first and validate the lowest score-breakdown areas.",
            "Probe common missing skills before final hiring decisions.",
            "Use confidence and resume quality flags to decide where manual review is needed.",
        ],
        overall_recommendation=(
            f"Proceed with interviews, prioritizing {top_name}; monitor {risk_text}."
        ),
        executive_insights=[
            f"Average experience is {analytics.average_experience} years.",
            f"Average skill match is {analytics.average_skill_match}%.",
            f"Top skill signal: {analytics.skill_frequency[0].name if analytics.skill_frequency else 'not enough skill data'}.",
        ],
    )


def hiring_summary_node(state: ExecutiveHiringState) -> ExecutiveHiringState:
    """HiringSummaryNode: generates an executive summary using existing metrics."""
    report = state.get("report")
    analytics = state.get("analytics")
    risks = state.get("risks") or []
    all_candidates = state.get("candidates") or {}
    errors = state.get("errors") or []
    if errors or not report or not analytics:
        return {**state, "errors": errors}

    fallback = _fallback_narrative(report, analytics, risks)
    narrative = fallback
    try:
        llm = get_llm_client()
        structured_llm = llm.with_structured_output(ExecutiveNarrative)
        prompt = PromptLoader.get_prompt(
            "executive_hiring_summary",
            analytics=analytics.model_dump_json(),
            risks="\n".join(risk.model_dump_json() for risk in risks),
            rankings="\n".join(ranking.model_dump_json() for ranking in report.rankings[:10]),
        )
        result = structured_llm.invoke(prompt)
        narrative = cast(ExecutiveNarrative, result)
        if narrative.overall_hiring_summary.lower().startswith("mock "):
            narrative = fallback
    except Exception as exc:
        logger.warning(f"Executive summary LLM failed, using deterministic summary: {exc}")
        narrative = fallback

    top_candidates = [
        ExecutiveCandidate(
            candidate_id=ranking.candidate_id,
            candidate_name=ranking.candidate_name,
            rank=ranking.rank,
            overall_score=ranking.score.overall_score,
            recommendation=_recommendation_from_score(ranking.score.overall_score),
            skill_match=ranking.score.breakdown.skill_match,
            confidence_score=ranking.score.confidence_score,
        )
        for ranking in report.rankings[:5]
    ]

    candidates = {
        ranking.candidate_id: all_candidates[ranking.candidate_id]
        for ranking in report.rankings
        if ranking.candidate_id in all_candidates
    }
    locations = _top_counts([candidate.location or "Not Listed" for candidate in candidates.values()])
    languages = _top_counts([language for candidate in candidates.values() for language in candidate.languages])
    education_levels = _top_counts(
        [
            education.degree or "Education Listed"
            for candidate in candidates.values()
            for education in candidate.education
        ]
    )
    if not education_levels and candidates:
        education_levels = [KeyCount(name="Not Listed", count=len(candidates))]
    resume_file_types = _top_counts(
        [
            candidate.metadata.file_name.rsplit(".", 1)[-1].lower()
            if "." in candidate.metadata.file_name
            else "unknown"
            for candidate in candidates.values()
        ]
    )

    summary = ExecutiveSummaryResponse(
        overall_hiring_summary=narrative.overall_hiring_summary,
        top_candidates=top_candidates,
        top_skills=analytics.skill_frequency[:10],
        most_missing_skills=_top_counts(
            [skill for ranking in report.rankings for skill in ranking.score.missing_skills],
            10,
        ),
        hiring_risks=narrative.hiring_risks,
        interview_priorities=narrative.interview_priorities,
        diversity_metrics=DiversityMetrics(
            locations=locations,
            languages=languages,
            education_levels=education_levels,
            resume_file_types=resume_file_types,
        ),
        average_experience=analytics.average_experience,
        average_skill_match=analytics.average_skill_match,
        overall_recommendation=narrative.overall_recommendation,
    )

    return {**state, "summary": summary}


def _build_interview_plan(report: Report) -> list[InterviewPlanItem]:
    plan = []
    for order, ranking in enumerate(report.rankings, start=1):
        focus_areas = _lowest_focus_areas(ranking)
        question_skills = ranking.score.missing_skills[:3] or ranking.score.matched_skills[:3]
        technical_questions = [
            f"Walk through a production example where you used {skill}."
            for skill in question_skills
        ]
        if len(technical_questions) < 3:
            technical_questions.extend(
                [
                    "Explain the architecture of your most relevant project for this role.",
                    "How would you validate performance, reliability, and maintainability in this stack?",
                    "Where did you personally contribute versus the wider team?",
                ][: 3 - len(technical_questions)]
            )

        behavioral_questions = [
            "Describe a time you handled ambiguity in a technical project.",
            "How do you communicate tradeoffs to non-technical stakeholders?",
        ]
        red_flags = []
        if ranking.score.confidence_score < 70:
            red_flags.append("Low confidence score; verify resume completeness.")
        if ranking.score.missing_skills:
            red_flags.append(f"Missing required skills: {', '.join(ranking.score.missing_skills[:4])}.")
        expected_difficulty = "High" if ranking.score.overall_score >= 85 else "Medium" if ranking.score.overall_score >= 70 else "Foundational"

        plan.append(
            InterviewPlanItem(
                candidate_id=ranking.candidate_id,
                candidate_name=ranking.candidate_name,
                interview_order=order,
                focus_areas=focus_areas,
                technical_questions=technical_questions[:5],
                behavioral_questions=behavioral_questions,
                red_flags=red_flags or ["No major red flags in current scoring output."],
                expected_difficulty=expected_difficulty,
            )
        )
    return plan


def insight_node(state: ExecutiveHiringState) -> ExecutiveHiringState:
    """InsightNode: recommends team fit and interview plan from existing report data."""
    report = state.get("report")
    candidates = state.get("candidates") or {}
    summary = state.get("summary")
    risks = state.get("risks") or []
    errors = state.get("errors") or []
    if errors or not report:
        return {**state, "errors": errors}

    rankings = report.rankings
    leadership_terms = {"lead", "leader", "leadership", "manager", "mentor", "architect", "stakeholder"}
    ai_terms = {"machine learning", "natural language processing", "llms", "openai", "tensorflow", "pytorch", "langchain"}
    frontend_terms = {"react", "javascript", "typescript", "html", "css", "vue.js", "angular", "next.js"}
    backend_terms = {"python", "fastapi", "django", "flask", "node.js", "sql", "postgresql", "mongodb", "redis"}
    full_stack_terms = frontend_terms | backend_terms
    research_terms = ai_terms | {"research", "publication", "experiment", "model evaluation", "paper"}

    team_fit = [
        _fit_recommendation("Best Technical Candidate", rankings, candidates, None, "This uses the existing overall score as the primary signal."),
        _fit_recommendation("Best Leadership Candidate", rankings, candidates, leadership_terms, "Leadership is based only on explicit resume terms."),
        _fit_recommendation("Best AI Candidate", rankings, candidates, ai_terms, "AI fit is based on explicit AI/ML skills and resume evidence."),
        _fit_recommendation("Best Full Stack Candidate", rankings, candidates, full_stack_terms, "Full stack fit weighs frontend and backend evidence together."),
        _fit_recommendation("Best Backend Candidate", rankings, candidates, backend_terms, "Backend fit is based on server, database, and API skills."),
        _fit_recommendation("Best Frontend Candidate", rankings, candidates, frontend_terms, "Frontend fit is based on UI framework and browser stack evidence."),
        _fit_recommendation("Best Research Candidate", rankings, candidates, research_terms, "Research fit is based on explicit research or AI evidence."),
    ]

    entry_candidates = [
        (ranking, candidates[ranking.candidate_id])
        for ranking in rankings
        if ranking.candidate_id in candidates and candidates[ranking.candidate_id].total_experience_years <= 2.5
    ]
    if not entry_candidates:
        entry_candidates = [
            (ranking, candidates[ranking.candidate_id])
            for ranking in rankings
            if ranking.candidate_id in candidates
        ]
    if entry_candidates:
        ranking, candidate = min(
            entry_candidates,
            key=lambda row: (row[1].total_experience_years, -row[0].score.overall_score),
        )
        team_fit.append(
            TeamFitRecommendation(
                category="Best Entry Level Candidate",
                candidate_id=candidate.id,
                candidate_name=candidate.full_name or ranking.candidate_name,
                explanation=(
                    f"{candidate.full_name or ranking.candidate_name} is the most entry-level aligned profile "
                    "based on explicit years of experience and current ranking quality."
                ),
                evidence=[
                    f"Experience {candidate.total_experience_years} years",
                    f"Overall score {ranking.score.overall_score}%",
                    f"Confidence {ranking.score.confidence_score}%",
                ],
            )
        )

    insights = HiringInsightsResponse(
        team_fit=team_fit,
        risks=risks,
        interview_plan=_build_interview_plan(report),
        executive_insights=(
            [
                summary.overall_hiring_summary,
                summary.overall_recommendation,
                *summary.interview_priorities[:3],
            ]
            if summary
            else []
        ),
    )

    return {**state, "insights": insights}


def executive_response_node(state: ExecutiveHiringState) -> ExecutiveHiringState:
    errors = state.get("errors") or []
    if errors:
        return {**state, "errors": errors}

    summary = state.get("summary")
    analytics = state.get("analytics")
    insights = state.get("insights")
    if not summary or not analytics or not insights:
        return {**state, "errors": ["Executive intelligence graph completed without a full response."]}

    response = HiringReportResponse(
        report_id=state.get("report_id") or "latest",
        executive_summary=summary,
        analytics=analytics,
        insights=insights,
    )
    return {**state, "response": response}


comparison_workflow = StateGraph(ComparisonState)
comparison_workflow.add_node("CandidateComparisonNode", candidate_comparison_node)
comparison_workflow.add_node("ComparisonAnalysisNode", comparison_analysis_node)
comparison_workflow.add_node("ComparisonVisualizationNode", comparison_visualization_node)
comparison_workflow.add_node("ComparisonResponseNode", comparison_response_node)
comparison_workflow.set_entry_point("CandidateComparisonNode")
comparison_workflow.add_edge("CandidateComparisonNode", "ComparisonAnalysisNode")
comparison_workflow.add_edge("ComparisonAnalysisNode", "ComparisonVisualizationNode")
comparison_workflow.add_edge("ComparisonVisualizationNode", "ComparisonResponseNode")
comparison_workflow.add_edge("ComparisonResponseNode", END)
comparison_graph = comparison_workflow.compile()

chat_workflow = StateGraph(RecruiterChatState)
chat_workflow.add_node("ContextRetrievalNode", context_retrieval_node)
chat_workflow.add_node("RecruiterChatNode", recruiter_chat_node)
chat_workflow.add_node("AnswerGenerationNode", answer_generation_node)
chat_workflow.add_node("ConversationMemoryNode", conversation_memory_node)
chat_workflow.set_entry_point("ContextRetrievalNode")
chat_workflow.add_edge("ContextRetrievalNode", "RecruiterChatNode")
chat_workflow.add_edge("RecruiterChatNode", "AnswerGenerationNode")
chat_workflow.add_edge("AnswerGenerationNode", "ConversationMemoryNode")
chat_workflow.add_edge("ConversationMemoryNode", END)
recruiter_chat_graph = chat_workflow.compile()

executive_workflow = StateGraph(ExecutiveHiringState)
executive_workflow.add_node("AnalyticsNode", analytics_node)
executive_workflow.add_node("RiskAssessmentNode", risk_assessment_node)
executive_workflow.add_node("HiringSummaryNode", hiring_summary_node)
executive_workflow.add_node("InsightNode", insight_node)
executive_workflow.add_node("ExecutiveResponseNode", executive_response_node)
executive_workflow.set_entry_point("AnalyticsNode")
executive_workflow.add_edge("AnalyticsNode", "RiskAssessmentNode")
executive_workflow.add_edge("RiskAssessmentNode", "HiringSummaryNode")
executive_workflow.add_edge("HiringSummaryNode", "InsightNode")
executive_workflow.add_edge("InsightNode", "ExecutiveResponseNode")
executive_workflow.add_edge("ExecutiveResponseNode", END)
executive_hiring_graph = executive_workflow.compile()
