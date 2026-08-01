"""Tests for the ReportExporter — CSV, JSON, and Markdown export formats."""

import json
import tempfile
from datetime import datetime
from pathlib import Path

import pytest

from app.exporters.report_exporter import ReportExporter
from app.models.report import Report
from app.models.score import Ranking, Score, ScoreBreakdown


@pytest.fixture
def sample_report() -> Report:
    """Build a minimal but valid Report fixture for export testing."""
    breakdown = ScoreBreakdown(
        skill_match=85.0,
        keyword_match=72.0,
        experience_match=78.0,
        project_match=65.0,
        education_match=90.0,
        certification_match=50.0,
        semantic_similarity=80.0,
    )
    score = Score(
        overall_score=77.5,
        breakdown=breakdown,
        confidence_score=88.0,
        reasoning="Strong Python and FastAPI alignment. Missing Docker experience.",
        matched_skills=["Python", "FastAPI"],
        missing_skills=["Docker", "Kubernetes"],
    )
    ranking = Ranking(
        candidate_id="cand-001",
        candidate_name="Alice Johnson",
        rank=1,
        score=score,
    )
    return Report(
        job_description_id="jd-001",
        job_title="Senior Backend Engineer",
        evaluation_timestamp=datetime(2024, 1, 15, 12, 0, 0),
        rankings=[ranking],
    )


class TestExportCSV:
    """Tests for CSV report export."""

    def test_csv_creates_file(self, sample_report):
        exporter = ReportExporter()
        with tempfile.TemporaryDirectory() as tmpdir:
            out_path = Path(tmpdir) / "report.csv"
            result = exporter.export_csv(sample_report, str(out_path))
            assert Path(result).exists()

    def test_csv_contains_header_row(self, sample_report):
        exporter = ReportExporter()
        with tempfile.TemporaryDirectory() as tmpdir:
            out_path = Path(tmpdir) / "report.csv"
            exporter.export_csv(sample_report, str(out_path))
            content = out_path.read_text(encoding="utf-8")
            assert "Rank" in content
            assert "Candidate Name" in content
            assert "Overall Score" in content

    def test_csv_contains_candidate_data(self, sample_report):
        exporter = ReportExporter()
        with tempfile.TemporaryDirectory() as tmpdir:
            out_path = Path(tmpdir) / "report.csv"
            exporter.export_csv(sample_report, str(out_path))
            content = out_path.read_text(encoding="utf-8")
            assert "Alice Johnson" in content
            assert "77.5" in content

    def test_csv_row_count_matches_rankings(self, sample_report):
        exporter = ReportExporter()
        with tempfile.TemporaryDirectory() as tmpdir:
            out_path = Path(tmpdir) / "report.csv"
            exporter.export_csv(sample_report, str(out_path))
            lines = [line for line in out_path.read_text(encoding="utf-8").splitlines() if line.strip()]
            # 1 header + 1 data row
            assert len(lines) == 2


class TestExportJSON:
    """Tests for JSON report export."""

    def test_json_creates_file(self, sample_report):
        exporter = ReportExporter()
        with tempfile.TemporaryDirectory() as tmpdir:
            out_path = Path(tmpdir) / "report.json"
            result = exporter.export_json(sample_report, str(out_path))
            assert Path(result).exists()

    def test_json_is_valid_format(self, sample_report):
        exporter = ReportExporter()
        with tempfile.TemporaryDirectory() as tmpdir:
            out_path = Path(tmpdir) / "report.json"
            exporter.export_json(sample_report, str(out_path))
            data = json.loads(out_path.read_text(encoding="utf-8"))
            assert isinstance(data, dict)

    def test_json_contains_job_title(self, sample_report):
        exporter = ReportExporter()
        with tempfile.TemporaryDirectory() as tmpdir:
            out_path = Path(tmpdir) / "report.json"
            exporter.export_json(sample_report, str(out_path))
            data = json.loads(out_path.read_text(encoding="utf-8"))
            assert data["job_title"] == "Senior Backend Engineer"

    def test_json_contains_rankings_array(self, sample_report):
        exporter = ReportExporter()
        with tempfile.TemporaryDirectory() as tmpdir:
            out_path = Path(tmpdir) / "report.json"
            exporter.export_json(sample_report, str(out_path))
            data = json.loads(out_path.read_text(encoding="utf-8"))
            assert "rankings" in data
            assert len(data["rankings"]) == 1
            assert data["rankings"][0]["candidate_name"] == "Alice Johnson"


class TestExportMarkdown:
    """Tests for Markdown report export."""

    def test_markdown_creates_file(self, sample_report):
        exporter = ReportExporter()
        with tempfile.TemporaryDirectory() as tmpdir:
            out_path = Path(tmpdir) / "report.md"
            result = exporter.export_markdown_report(sample_report, str(out_path))
            assert Path(result).exists()

    def test_markdown_contains_title(self, sample_report):
        exporter = ReportExporter()
        with tempfile.TemporaryDirectory() as tmpdir:
            out_path = Path(tmpdir) / "report.md"
            exporter.export_markdown_report(sample_report, str(out_path))
            content = out_path.read_text(encoding="utf-8")
            assert "# AI Resume Screening Report" in content

    def test_markdown_contains_job_title(self, sample_report):
        exporter = ReportExporter()
        with tempfile.TemporaryDirectory() as tmpdir:
            out_path = Path(tmpdir) / "report.md"
            exporter.export_markdown_report(sample_report, str(out_path))
            content = out_path.read_text(encoding="utf-8")
            assert "Senior Backend Engineer" in content

    def test_markdown_contains_candidate_name(self, sample_report):
        exporter = ReportExporter()
        with tempfile.TemporaryDirectory() as tmpdir:
            out_path = Path(tmpdir) / "report.md"
            exporter.export_markdown_report(sample_report, str(out_path))
            content = out_path.read_text(encoding="utf-8")
            assert "Alice Johnson" in content

    def test_markdown_contains_table_header(self, sample_report):
        exporter = ReportExporter()
        with tempfile.TemporaryDirectory() as tmpdir:
            out_path = Path(tmpdir) / "report.md"
            exporter.export_markdown_report(sample_report, str(out_path))
            content = out_path.read_text(encoding="utf-8")
            assert "| Rank |" in content
