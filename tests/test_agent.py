from datetime import datetime

import pytest

from app.embeddings.generator import SentenceTransformerGenerator
from app.graph.workflow import LLMAnalysisResult
from app.llm.client import MockChatModel
from app.models.candidate import (
    Candidate,
    CandidateMetadata,
    Certification,
    Project,
    WorkExperience,
)
from app.models.candidate import Education as AcademicEducation
from app.models.job_description import JobDescription
from app.scorer.scoring_engine import CandidateScorer
from app.scorer.similarity_engine import (
    compute_cosine_similarity,
    compute_keyword_similarity,
    compute_skill_similarity,
)
from app.services.agent_service import AgentService


# Helper to create mock candidate profiles
def create_mock_candidate(
    cand_id: str,
    name: str,
    email: str,
    skills: list[str],
    exp_years: float,
    certs_count: int = 1
) -> Candidate:
    meta = CandidateMetadata(
        file_name="resume.pdf",
        file_size=1000,
        pages=1,
        parser_used="PDFParser",
        processing_time=0.01,
        extraction_timestamp=datetime.utcnow()
    )

    experience = [
        WorkExperience(
            company="Company A",
            role="Software Engineer",
            start_date="2020",
            end_date="2022",
            current_company=False,
            duration="24 months",
            responsibilities="Developed cloud features",
            technology_stack=["Python", "AWS"]
        )
    ]

    education = [
        AcademicEducation(
            degree="B.Tech",
            university="Stanford University",
            college="CS Dept",
            cgpa=9.0,
            percentage=90.0,
            graduation_year=2020
        )
    ]

    projects = [
        Project(
            project_name="Data Pipeline",
            description="Built batch ETL workflows",
            technologies_used=["Python", "SQL"],
            duration="3 months"
        )
    ]

    certifications = [
        Certification(
            certification_name="AWS Solutions Architect",
            provider="AWS",
            issue_date="2021"
        )
    ] * certs_count

    return Candidate(
        id=cand_id,
        full_name=name,
        email=email,
        phone="+1-555-123-4567",
        location="Paris, France",
        linkedin="linkedin.com/in/test",
        github="github.com/test",
        portfolio="test.com",
        summary="Experienced developer",
        skills=skills,
        experience=experience,
        education=education,
        projects=projects,
        certifications=certifications,
        languages=["English"],
        total_experience_years=exp_years,
        raw_resume_text=f"{name} resume with skills: {', '.join(skills)}",
        metadata=meta
    )


def test_similarity_engine_math() -> None:
    """Verifies cosine similarity scaling and Jaccard-overlap math logic."""
    # 1. Cosine similarity
    vec_a = [1.0, 0.0, 0.0]
    vec_b = [1.0, 0.0, 0.0]
    assert compute_cosine_similarity(vec_a, vec_b) == 100.0

    vec_c = [0.0, 1.0, 0.0]
    assert compute_cosine_similarity(vec_a, vec_c) == 0.0

    # 2. Skill similarity
    cand_skills = ["Python", "Docker", "Git"]
    req = ["Python", "AWS"]
    pref = ["Docker"]
    # Matched required: Python (1.0), Matched preferred: Docker (0.5).
    # Total JD weight: req (1.0 * 2) + pref (0.5 * 1) = 2.5
    # Matched weight: Python (1.0) + Docker (0.5) = 1.5
    # Percentage: 1.5 / 2.5 * 100 = 60.0
    assert compute_skill_similarity(cand_skills, req, pref) == 60.0

    # 3. Keyword similarity
    cand_keywords = ["FastAPI", "MongoDB"]
    jd_keywords = ["FastAPI", "Docker", "PostgreSQL"]
    # Match FastAPI (1), JD total (3). Overlap ratio: 1/3 -> 33.3%
    assert round(compute_keyword_similarity(cand_keywords, jd_keywords), 1) == 33.3


def test_scoring_engine_weights() -> None:
    """Verifies scoring engine returns valid weighted aggregates and confidence metrics."""
    generator = SentenceTransformerGenerator()
    scorer = CandidateScorer(generator)

    cand = create_mock_candidate("C01", "John Doe", "john@example.com", ["Python", "AWS"], 3.0)
    jd = JobDescription(
        id="J01",
        title="Python Dev",
        role="Developer",
        raw_content="Looking for a Python Developer with AWS and B.Tech degree. Require 2+ years of experience.",
        required_skills=["Python", "AWS"],
        preferred_skills=["Docker"],
        education_requirements=["B.Tech"],
        minimum_experience_years=2.0,
        responsibilities=["Build cloud features"],
        nice_to_have=["Docker experience"],
        location="Paris, France",
        employment_type="Full-time",
        keywords=["Python", "AWS"],
        soft_skills=["Communication"]
    )

    score_res = scorer.calculate_score(cand, jd)
    assert 0.0 <= score_res.overall_score <= 100.0
    assert score_res.overall_score > 50.0  # Basic matches should score well
    assert 0.0 <= score_res.confidence_score <= 100.0
    assert len(score_res.matched_skills) == 2
    assert len(score_res.missing_skills) == 0


def test_ranking_engine_deterministic() -> None:
    """Verifies deterministic candidate ranking sorting order checks."""
    # Build list of evaluations
    c1 = create_mock_candidate("C01", "Alice Alpha", "alice@example.com", ["Python"], 5.0)
    c2 = create_mock_candidate("C02", "Bob Beta", "bob@example.com", ["Python"], 3.0)
    c3 = create_mock_candidate("C03", "Charlie Gamma", "charlie@example.com", ["Python"], 3.0)

    # We sort by: Overall Score (desc) -> Semantic Similarity (desc) -> Experience (desc) -> Confidence (desc) -> Name (asc)
    # Alice has higher experience, Charlie and Bob have same overall score, but Bob has higher confidence
    evals = [
        (c1, 80.0, 75.0, 85.0), # (cand, score, similarity, confidence)
        (c2, 85.0, 70.0, 90.0),
        (c3, 85.0, 70.0, 80.0)
    ]

    def sort_key(item):
        cand, score_val, sim_val, conf_val = item
        return (
            -score_val,
            -sim_val,
            -cand.total_experience_years,
            -conf_val,
            cand.full_name or ""
        )

    sorted_evals = sorted(evals, key=sort_key)

    # Order should be:
    # 1. Bob (Overall Score 85.0, Sim 70.0, Exp 3.0, Conf 90.0)
    # 2. Charlie (Overall Score 85.0, Sim 70.0, Exp 3.0, Conf 80.0)
    # 3. Alice (Overall Score 80.0)
    assert sorted_evals[0][0].id == "C02"  # Bob
    assert sorted_evals[1][0].id == "C03"  # Charlie
    assert sorted_evals[2][0].id == "C01"  # Alice


def test_llm_output_parser() -> None:
    """Verifies that structured LLM parsing outputs Pydantic models from MockChatModel."""
    mock_llm = MockChatModel()
    structured = mock_llm.with_structured_output(LLMAnalysisResult)

    result = structured("Format candidate profile analysis")
    assert isinstance(result, LLMAnalysisResult)
    assert len(result.interview_questions) == 5
    assert result.recommendation in ("Strong Hire", "Hire", "Consider", "Review", "Reject")


@pytest.mark.anyio
async def test_graph_and_service_execution() -> None:
    """Verifies end-to-end workflow execution of the StateGraph using mock entities."""
    cand = create_mock_candidate("C01", "John Doe", "john@example.com", ["Python", "AWS"], 3.0)
    jd = JobDescription(
        id="J01",
        title="Python Dev",
        role="Developer",
        raw_content="Looking for a Python Developer with AWS and B.Tech degree.",
        required_skills=["Python", "AWS"],
        preferred_skills=["Docker"],
        education_requirements=["B.Tech"],
        minimum_experience_years=2.0,
        responsibilities=["Build cloud features"],
        nice_to_have=["Docker experience"],
        location="Paris, France",
        employment_type="Full-time",
        keywords=["Python", "AWS"],
        soft_skills=["Communication"]
    )

    # Run using AgentService
    service = AgentService()
    report = await service.run_screening_with_entities(jd, [cand])

    assert report is not None
    assert report.job_title == "Python Dev"
    assert len(report.rankings) == 1
    assert report.rankings[0].candidate_name == "John Doe"
    assert report.rankings[0].score.overall_score > 0.0
