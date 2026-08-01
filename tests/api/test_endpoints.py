import pytest
from fastapi.testclient import TestClient

from app.api.router import CANDIDATE_STORE, GLOBAL_STATE
from app.models.candidate import Candidate, CandidateMetadata
from main import app


@pytest.fixture
def client():
    return TestClient(app)


def test_upload_job_description_success(client):
    content = b"Role: Software Engineer\nRequirements: Python, FastAPI, Docker"
    response = client.post(
        "/job-description/upload",
        files={"file": ("jd.txt", content, "text/plain")},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert "saved_path" in data["data"]
    assert data["data"]["filename"] == "jd.txt"


def test_upload_resumes_success(client):
    content1 = b"Candidate: John Doe\nSkills: Python, Django"
    content2 = b"Candidate: Jane Smith\nSkills: React, TypeScript"
    response = client.post(
        "/resumes/upload",
        files=[
            ("files", ("resume1.txt", content1, "text/plain")),
            ("files", ("resume2.txt", content2, "text/plain")),
        ],
    )
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert len(data["data"]) == 2
    assert data["data"][0]["filename"] == "resume1.txt"
    assert data["data"][1]["filename"] == "resume2.txt"


def test_get_results_empty(client):
    GLOBAL_STATE["last_report_id"] = None
    response = client.get("/results")
    assert response.status_code == 200
    assert response.json()["data"]["rankings"] == []


def test_get_candidate_not_found(client):
    response = client.get("/candidate/non-existent-id")
    assert response.status_code == 404


def test_candidate_details_success(client):
    cand_id = "test-candidate-123"
    candidate = Candidate(
        id=cand_id,
        full_name="Alex Mercer",
        email="alex@mercer.com",
        phone="+1234567890",
        location="NY",
        summary="Dev",
        skills=["Python", "FastAPI"],
        experience=[],
        education=[],
        projects=[],
        certifications=[],
        raw_resume_text="Alex Mercer Software Developer python fastapi docker",
        metadata=CandidateMetadata(
            file_name="resume.txt",
            file_size=1000,
            pages=1,
            processing_time=0.1,
            parser_used="TextParser",
        ),
    )
    CANDIDATE_STORE[cand_id] = candidate

    response = client.get(f"/candidate/{cand_id}")
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["data"]["profile"]["full_name"] == "Alex Mercer"


def test_download_no_report_errors(client):
    GLOBAL_STATE["last_report_id"] = None
    response = client.get("/download/csv")
    assert response.status_code == 404
    assert "No screening reports found" in response.json()["detail"]
