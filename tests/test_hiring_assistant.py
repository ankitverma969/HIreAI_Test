import json
from datetime import datetime

from fastapi.testclient import TestClient

from app.api.router import (
    AUDIT_LOG_STORE,
    CANDIDATE_STORE,
    GLOBAL_STATE,
    GRAPH_TRACE_STORE,
    JOB_DESCRIPTION_STORE,
    RESULTS_STORE,
)
from app.models.hiring_assistant import GraphExecutionResponse, TraceStep
from app.models.candidate import Candidate, CandidateMetadata, Project, WorkExperience
from app.models.job_description import JobDescription
from app.models.report import Report
from app.models.score import Ranking, Score, ScoreBreakdown
from app.prompts.loader import PromptLoader
from main import app


def _candidate(
    candidate_id: str,
    name: str,
    skills: list[str],
    experience_years: float,
    project_name: str,
) -> Candidate:
    return Candidate(
        id=candidate_id,
        full_name=name,
        email=f"{candidate_id}@example.com",
        phone="+1-555-123-4567",
        location="San Francisco, CA",
        linkedin=f"linkedin.com/in/{candidate_id}",
        github=f"github.com/{candidate_id}",
        portfolio=f"{candidate_id}.dev",
        summary=f"{name} is an engineering candidate.",
        skills=skills,
        experience=[
            WorkExperience(
                company="Example Co",
                role="Software Engineer",
                start_date="2020",
                end_date="2024",
                responsibilities="Built Python and React systems.",
                technology_stack=skills,
            )
        ],
        education=[],
        projects=[
            Project(
                project_name=project_name,
                description="Built a production hiring analytics system.",
                technologies_used=skills,
            )
        ],
        certifications=[],
        languages=["English"],
        total_experience_years=experience_years,
        raw_resume_text=f"{name} resume mentions {' '.join(skills)} LangGraph Docker AWS.",
        metadata=CandidateMetadata(
            file_name=f"{candidate_id}.txt",
            file_size=1000,
            pages=0,
            parser_used="TextParser",
            processing_time=0.1,
            extraction_timestamp=datetime.utcnow(),
        ),
    )


def _ranking(candidate: Candidate, rank: int, overall: float, skill: float, confidence: float) -> Ranking:
    return Ranking(
        candidate_id=candidate.id,
        candidate_name=candidate.full_name or candidate.id,
        rank=rank,
        score=Score(
            overall_score=overall,
            breakdown=ScoreBreakdown(
                skill_match=skill,
                keyword_match=skill,
                experience_match=80.0,
                project_match=75.0,
                education_match=70.0,
                certification_match=30.0,
                semantic_similarity=82.0,
            ),
            confidence_score=confidence,
            reasoning=f"{candidate.full_name} matches the current JD.",
            matched_skills=["Python", "AWS"],
            missing_skills=["Docker"] if "Docker" not in candidate.skills else [],
        ),
    )


def _seed_session() -> tuple[Candidate, Candidate]:
    first = _candidate("cand-1", "Rahul Sharma", ["Python", "AWS", "Docker"], 6.0, "LangGraph ATS")
    second = _candidate("cand-2", "Maya Singh", ["Python", "React"], 4.0, "React Dashboard")
    CANDIDATE_STORE[first.id] = first
    CANDIDATE_STORE[second.id] = second

    report = Report(
        job_description_id="jd-1",
        job_title="Senior Software Engineer",
        rankings=[
            _ranking(first, 1, 91.0, 95.0, 90.0),
            _ranking(second, 2, 78.0, 70.0, 82.0),
        ],
    )
    RESULTS_STORE["jd-1"] = report
    JOB_DESCRIPTION_STORE["jd-1"] = JobDescription(
        id="jd-1",
        title="Senior Software Engineer",
        raw_content="Need Python, AWS, Docker, React, and LangGraph experience.",
        required_skills=["Python", "AWS", "Docker"],
        preferred_skills=["React"],
        keywords=["Python", "AWS", "Docker", "React"],
    )
    GLOBAL_STATE["last_report_id"] = "jd-1"
    return first, second


def test_comparison_api_generates_existing_score_payload() -> None:
    first, second = _seed_session()
    client = TestClient(app)

    response = client.post("/compare", json={"candidate_ids": [first.id, second.id]})

    assert response.status_code == 200
    data = response.json()["data"]
    assert data["highlights"]["best_candidate_id"] == first.id
    assert len(data["candidates"]) == 2
    assert data["candidates"][0]["overall_score"] == 91.0
    assert data["chart_data"]["radar"]
    assert data["ai_summary"]["why_ranked_higher"]


def test_chat_api_answers_rank_question_and_persists_history() -> None:
    first, _second = _seed_session()
    client = TestClient(app)

    response = client.post("/chat", json={"question": "Who ranked first?", "session_id": "test"})

    assert response.status_code == 200
    data = response.json()["data"]
    assert first.full_name in data["message"]["answer_markdown"]
    assert data["message"]["cited_candidates"] == [first.id]
    assert len(data["history"]) == 2

    history_response = client.get("/chat/history", params={"session_id": "test"})
    assert history_response.status_code == 200
    assert len(history_response.json()["data"]["messages"]) == 2


def test_chat_explains_why_named_candidate_ranked_first() -> None:
    first, _second = _seed_session()
    client = TestClient(app)

    response = client.post(
        "/chat",
        json={"question": "Why is Rahul ranked first?", "session_id": "why-rank"},
    )

    assert response.status_code == 200
    message = response.json()["data"]["message"]
    assert first.full_name in message["answer_markdown"]
    assert "Overall score: 91.0%" in message["answer_markdown"]
    assert "Skill match: 95.0%" in message["answer_markdown"]
    assert "matched_skills" in message["cited_fields"]
    assert message["cited_candidates"] == [first.id]


def test_chat_memory_supports_follow_up_question() -> None:
    first, _second = _seed_session()
    client = TestClient(app)

    client.post("/chat", json={"question": "Who ranked first?", "session_id": "memory"})
    response = client.post(
        "/chat",
        json={"question": "What projects did they build?", "session_id": "memory"},
    )

    assert response.status_code == 200
    answer = response.json()["data"]["message"]
    assert "LangGraph ATS" in answer["answer_markdown"]
    assert answer["cited_candidates"] == [first.id]


def test_chat_clear_history() -> None:
    _seed_session()
    client = TestClient(app)

    client.post("/chat", json={"question": "Which candidates know AWS?", "session_id": "clear"})
    response = client.delete("/chat/history", params={"session_id": "clear"})

    assert response.status_code == 200
    assert response.json()["data"]["messages"] == []


def test_chat_unavailable_guardrail_without_results() -> None:
    client = TestClient(app)

    response = client.post("/chat", json={"question": "Who knows Rust?", "session_id": "empty"})

    assert response.status_code == 200
    message = response.json()["data"]["message"]
    assert message["unavailable"] is True
    assert message["direct_answer"] == "The uploaded resumes do not contain enough information."


def test_candidate_comparison_prompt_is_structured_json_only() -> None:
    prompt = PromptLoader.get_prompt(
        "candidate_comparison",
        comparison_rows='{"candidate_name":"Rahul","overall_score":91}',
        highlights='{"best_candidate_name":"Rahul"}',
    )

    assert "Return only structured JSON" in prompt
    assert "Do not calculate" in prompt
    assert "executive_comparison" in prompt


def test_executive_summary_api_generates_report_summary() -> None:
    first, _second = _seed_session()
    client = TestClient(app)

    response = client.get("/executive-summary")

    assert response.status_code == 200
    data = response.json()["data"]
    assert first.full_name in data["top_candidates"][0]["candidate_name"]
    assert data["average_experience"] == 5.0
    assert data["average_skill_match"] == 82.5
    assert data["diversity_metrics"]["locations"]
    assert data["overall_recommendation"]


def test_analytics_api_generates_recruitment_metrics() -> None:
    _seed_session()
    client = TestClient(app)

    response = client.get("/analytics")

    assert response.status_code == 200
    data = response.json()["data"]
    assert data["total_candidates"] == 2
    assert data["average_resume_score"] == 84.5
    assert any(item["name"] == "Python" for item in data["skill_frequency"])
    assert any(item["name"] == "Cloud" for item in data["technology_distribution"])
    assert data["recommendation_distribution"]


def test_insights_api_generates_team_fit_risks_and_interview_plan() -> None:
    first, _second = _seed_session()
    client = TestClient(app)

    response = client.get("/insights")

    assert response.status_code == 200
    data = response.json()["data"]
    assert any(item["category"] == "Best Technical Candidate" for item in data["team_fit"])
    assert any(risk["category"] == "Skill Gaps" for risk in data["risks"])
    assert data["interview_plan"][0]["candidate_id"] == first.id
    assert data["interview_plan"][0]["technical_questions"]


def test_hiring_report_json_and_download_exports() -> None:
    _seed_session()
    client = TestClient(app)

    json_response = client.get("/hiring-report")
    assert json_response.status_code == 200
    report_data = json_response.json()["data"]
    assert report_data["executive_summary"]["top_candidates"]
    assert report_data["analytics"]["average_resume_score"] == 84.5

    csv_response = client.get("/hiring-report", params={"format": "csv", "download": "true"})
    assert csv_response.status_code == 200
    assert "text/csv" in csv_response.headers["content-type"]
    assert b"Average Resume Score" in csv_response.content

    markdown_response = client.get("/hiring-report", params={"format": "markdown", "download": "true"})
    assert markdown_response.status_code == 200
    assert b"Executive Hiring Intelligence Report" in markdown_response.content

    pdf_response = client.get("/hiring-report", params={"format": "pdf", "download": "true"})
    assert pdf_response.status_code == 200
    assert pdf_response.content.startswith(b"%PDF")


def test_executive_summary_prompt_is_structured_json_only() -> None:
    prompt = PromptLoader.get_prompt(
        "executive_hiring_summary",
        analytics='{"average_resume_score":84.5}',
        risks='{"category":"Skill Gaps"}',
        rankings='{"candidate_name":"Rahul"}',
    )

    assert "Return only structured JSON" in prompt
    assert "Do not calculate or change any scores" in prompt
    assert "overall_hiring_summary" in prompt


def test_candidate_explainability_api_returns_score_trace_and_requirements() -> None:
    first, _second = _seed_session()
    client = TestClient(app)

    response = client.get(f"/explain/{first.id}")

    assert response.status_code == 200
    data = response.json()["data"]
    assert data["overall_score"] == 91.0
    assert any(item["section"] == "Skill Match" for item in data["score_contributions"])
    assert any(item["requirement"] == "Python" for item in data["requirement_mapping"]["fully_matched"])
    assert data["resume_quality"]["rating"] in ("Excellent", "Good", "Average", "Poor")
    assert data["confidence_explanation"]["factors"]
    assert data["audit_record"]["candidate_id"] == first.id


def test_audit_log_api_supports_search_filter_sort_and_csv_export() -> None:
    first, _second = _seed_session()
    client = TestClient(app)
    client.get(f"/explain/{first.id}")

    response = client.get("/audit", params={"search": "Rahul", "sort_by": "candidate_name", "order": "asc"})

    assert response.status_code == 200
    records = response.json()["data"]["records"]
    assert records[0]["candidate_id"] == first.id
    assert AUDIT_LOG_STORE

    csv_response = client.get("/audit", params={"format": "csv"})
    assert csv_response.status_code == 200
    assert b"Candidate ID" in csv_response.content


def test_graph_execution_and_timeline_api_returns_node_trace() -> None:
    _seed_session()
    GRAPH_TRACE_STORE["jd-1"] = GraphExecutionResponse(
        report_id="jd-1",
        timeline=[
            TraceStep(
                name="validate_input",
                status="success",
                execution_time=0.01,
                input_size=1,
                output_size=1,
                execution_order=1,
            )
        ],
        performance_metrics={"total_execution_time": 0.01},
    )
    client = TestClient(app)

    execution = client.get("/graph/execution")
    timeline = client.get("/graph/timeline")

    assert execution.status_code == 200
    assert execution.json()["data"]["timeline"][0]["name"] == "validate_input"
    assert timeline.status_code == 200
    assert timeline.json()["data"]["performance_metrics"]["total_execution_time"] == 0.01


def test_prompt_history_api_returns_sanitized_records() -> None:
    _seed_session()
    client = TestClient(app)

    response = client.get("/prompt-history")

    assert response.status_code == 200
    records = response.json()["data"]["records"]
    assert records
    assert "mock-key-for-local-testing" not in json.dumps(records)
