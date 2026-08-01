import pytest

from app.extractor.candidate_extractor import CandidateExtractor
from app.extractor.certification_extractor import extract_certifications
from app.extractor.contact_extractor import extract_contacts
from app.extractor.education_extractor import extract_education
from app.extractor.experience_extractor import (
    calculate_total_experience,
    extract_experience,
)
from app.extractor.job_description_extractor import JobDescriptionExtractor
from app.extractor.project_extractor import extract_projects
from app.extractor.skills_extractor import extract_skills
from app.extractor.summary_extractor import extract_summary


def test_extract_contacts() -> None:
    """Verifies contacts are parsed from typical resume headers."""
    text = "John Doe\nEmail: contact@doe.com\nPhone: (123) 456-7890\nLinkedIn: linkedin.com/in/jdoe\nLocation: Paris, France"
    res = extract_contacts(text)
    assert res["email"] == "contact@doe.com"
    assert res["phone"] == "(123) 456-7890"
    assert res["linkedin"] == "linkedin.com/in/jdoe"
    assert "Paris" in res["location"]


def test_extract_skills() -> None:
    """Verifies skills database matches and resolves raw names."""
    text = "Experienced in JS, Python development, Docker, and machine learning (ML)."
    res = extract_skills(text)
    # js -> JavaScript, ML & machine learning -> Machine Learning, docker -> Docker
    assert "JavaScript" in res
    assert "Python" in res
    assert "Docker" in res
    assert "Machine Learning" in res
    # Should not match substrings
    assert "Go" not in res  # 'Go' in 'development' should not match


def test_extract_education() -> None:
    """Verifies education items matching degree patterns."""
    text = "Stanford University\nB.Tech in Computer Science, 2020\nGPA: 9.2/10"
    res = extract_education(text)
    assert len(res) >= 1
    assert res[0].degree == "B.Tech"
    assert res[0].graduation_year == 2020
    assert res[0].cgpa == 9.2


def test_extract_experience() -> None:
    """Verifies experience intervals mapping roles and total years calculation."""
    text = "Software Engineer at Google\nJan 2020 - Dec 2022\nWorked on next-generation features.\nDeveloper at Stripe\n01/2023 - Present"
    res = extract_experience(text)
    assert len(res) == 2
    assert res[0].role == "Engineer"
    assert res[0].company == "Google"
    assert res[1].role == "Developer"
    assert res[1].company == "Stripe"
    assert res[1].current_company is True

    # Calculate total experience
    total = calculate_total_experience(res)
    # Jan 2020 - Dec 2022 = 36 months (3.0 years)
    # Jan 2023 - Aug 2026 (Present reference) = 44 months (3.67 years)
    # Total = 80 months = 6.67 years (rounded to 6.7)
    assert total == 6.7


def test_extract_projects() -> None:
    """Verifies projects split and skill mapping."""
    text = "Projects\n- Resume Screener (Jan 2026): built a parser in Python and React."
    res = extract_projects(text)
    assert len(res) >= 1
    assert res[0].project_name == "Resume Screener"
    assert "Python" in res[0].technologies_used
    assert "React" in res[0].technologies_used
    assert res[0].duration == "Jan 2026"


def test_extract_certifications() -> None:
    """Verifies professional certifications mapping."""
    text = "AWS Certified Solutions Architect, IBM Certified Developer 2021"
    res = extract_certifications(text)
    assert len(res) >= 2
    assert "Solutions Architect" in res[0].certification_name
    assert res[0].provider == "AWS"
    assert res[1].provider == "IBM"
    assert res[1].issue_date == "2021"


def test_extract_summary() -> None:
    """Verifies summary blocks extraction."""
    text = "Objective\nResults-driven engineer looking to join a high-impact team.\nExperience\nGoogle ..."
    assert "Results-driven" in extract_summary(text)


def test_job_description_extractor() -> None:
    """Verifies Job Description is parsed into structured fields."""
    jd_text = "Senior React Developer\nLocation: Paris, France\nExperience Required: 5+ years of experience.\nRequirements\n* 5 years of React, Next.js, and TypeScript.\nResponsibilities\n* Build modern web apps."
    res = JobDescriptionExtractor.extract_job_description("JD001", jd_text)
    assert res.id == "JD001"
    assert res.title == "Senior React Developer"
    assert res.minimum_experience_years == 5.0
    assert "React" in res.required_skills
    assert "Next.js" in res.required_skills
    assert "TypeScript" in res.required_skills
    assert "Build modern web apps." in res.responsibilities


@pytest.mark.anyio
async def test_candidate_extractor() -> None:
    """Verifies full candidate structuring pipeline."""
    parsed_doc = {
        "file_name": "resume.pdf",
        "file_size": 1500,
        "pages": 1,
        "parser_used": "PDFParser",
        "processing_time": 0.05,
        "raw_text": "John Doe\nEmail: john.doe@example.com\nPhone: +1-555-123-4567\nB.Tech in CS 2020\nPython developer at Stripe (Jan 2021 - Dec 2023)",
        "cleaned_text": "John Doe\nEmail: john.doe@example.com\nPhone: +1-555-123-4567\nB.Tech in CS 2020\nPython developer at Stripe (Jan 2021 - Dec 2023)"
    }
    candidate = await CandidateExtractor.extract_candidate_profile(parsed_doc)
    assert candidate.full_name == "John Doe"
    assert candidate.email == "john.doe@example.com"
    assert candidate.phone == "+1-555-123-4567"
    assert candidate.total_experience_years == 3.0  # 36 months (Jan 2021 - Dec 2023)
    assert "Python" in candidate.skills
    assert candidate.metadata.file_name == "resume.pdf"
