import csv
from pathlib import Path

from app.core.exceptions import ExportException
from app.exporters.interface import BaseReportExporter
from app.models.report import Report


class ReportExporter(BaseReportExporter):
    """Concrete implementation of report exporters for CSV, JSON, and Markdown formats."""

    def export_csv(self, report: Report, output_path: str) -> str:
        try:
            path = Path(output_path)
            path.parent.mkdir(parents=True, exist_ok=True)

            with open(path, mode="w", newline="", encoding="utf-8") as f:
                writer = csv.writer(f)
                # Header
                writer.writerow([
                    "Rank", "Candidate Name", "Candidate ID", "Overall Score",
                    "Skill Match", "Keyword Match", "Experience Match",
                    "Project Match", "Education Match", "Certification Match",
                    "Semantic Similarity", "Confidence Score", "Reasoning"
                ])
                # Rows
                for r in report.rankings:
                    b = r.score.breakdown
                    writer.writerow([
                        r.rank, r.candidate_name, r.candidate_id, r.score.overall_score,
                        b.skill_match, b.keyword_match, b.experience_match,
                        b.project_match, b.education_match, b.certification_match,
                        b.semantic_similarity, r.score.confidence_score, r.score.reasoning
                    ])
            return str(path.absolute())
        except Exception as e:
            raise ExportException(f"Failed to export CSV: {str(e)}") from e

    def export_json(self, report: Report, output_path: str) -> str:
        try:
            path = Path(output_path)
            path.parent.mkdir(parents=True, exist_ok=True)

            # Serialize using Pydantic JSON
            data = report.model_dump_json(indent=2)
            with open(path, mode="w", encoding="utf-8") as f:
                f.write(data)
            return str(path.absolute())
        except Exception as e:
            raise ExportException(f"Failed to export JSON: {str(e)}") from e

    def export_markdown_report(self, report: Report, output_path: str) -> str:
        try:
            path = Path(output_path)
            path.parent.mkdir(parents=True, exist_ok=True)

            lines = [
                "# AI Resume Screening Report",
                f"**Job Title:** {report.job_title}",
                f"**Evaluation Timestamp:** {report.evaluation_timestamp.isoformat()}",
                f"**Total Candidates Processed:** {len(report.rankings)}",
                "",
                "## Rankings & Match Scores Table",
                "| Rank | Candidate Name | Overall Score | Skill Match | Experience | Semantic Similarity | Confidence |",
                "|---|---|---|---|---|---|---|",
            ]

            for r in report.rankings:
                b = r.score.breakdown
                lines.append(
                    f"| {r.rank} | {r.candidate_name} | {r.score.overall_score}% | {b.skill_match}% | {b.experience_match}% | {b.semantic_similarity}% | {r.score.confidence_score}% |"
                )

            lines.append("")
            lines.append("## Candidate Details & Qualititative AI Reasoning")
            for r in report.rankings:
                lines.extend([
                    f"### {r.rank}. {r.candidate_name} (ID: {r.candidate_id})",
                    f"- **Overall Match Score:** {r.score.overall_score}%",
                    f"- **Scoring Confidence:** {r.score.confidence_score}%",
                    f"- **Key Reasoning:** {r.score.reasoning}",
                    ""
                ])

            with open(path, mode="w", encoding="utf-8") as f:
                f.write("\n".join(lines))
            return str(path.absolute())
        except Exception as e:
            raise ExportException(f"Failed to export Markdown report: {str(e)}") from e
