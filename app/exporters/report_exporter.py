import csv
import json
from datetime import datetime
from pathlib import Path

from app.core.exceptions import ExportException
from app.exporters.interface import BaseReportExporter
from app.models.report import Report


class ReportExporter(BaseReportExporter):
    """Concrete implementation of report exporters for CSV, JSON, and Markdown formats.

    Exports include:
    - Candidate summary and rank
    - Weighted score breakdown
    - Matched and missing skills
    - AI-generated reasoning
    - Execution metadata
    """

    def export_csv(self, report: Report, output_path: str) -> str:
        """Exports the screening report as a flat CSV file.

        Args:
            report: Validated Report object with rankings.
            output_path: Destination file path string.

        Returns:
            Absolute path of the written CSV file.
        """
        try:
            path = Path(output_path)
            path.parent.mkdir(parents=True, exist_ok=True)

            with open(path, mode="w", newline="", encoding="utf-8") as f:
                writer = csv.writer(f)
                # Extended header including skills breakdown and metadata
                writer.writerow([
                    "Rank",
                    "Candidate Name",
                    "Candidate ID",
                    "Overall Score",
                    "Skill Match",
                    "Keyword Match",
                    "Experience Match",
                    "Project Match",
                    "Education Match",
                    "Certification Match",
                    "Semantic Similarity",
                    "Confidence Score",
                    "Matched Skills",
                    "Missing Skills",
                    "Reasoning",
                ])
                for r in report.rankings:
                    b = r.score.breakdown
                    matched = "; ".join(r.score.matched_skills) if r.score.matched_skills else ""
                    missing = "; ".join(r.score.missing_skills) if r.score.missing_skills else ""
                    writer.writerow([
                        r.rank,
                        r.candidate_name,
                        r.candidate_id,
                        r.score.overall_score,
                        b.skill_match,
                        b.keyword_match,
                        b.experience_match,
                        b.project_match,
                        b.education_match,
                        b.certification_match,
                        b.semantic_similarity,
                        r.score.confidence_score,
                        matched,
                        missing,
                        r.score.reasoning,
                    ])
            return str(path.absolute())
        except Exception as e:
            raise ExportException(f"Failed to export CSV: {str(e)}") from e

    def export_json(self, report: Report, output_path: str) -> str:
        """Exports the screening report as a structured JSON file with execution metadata.

        Args:
            report: Validated Report object with rankings.
            output_path: Destination file path string.

        Returns:
            Absolute path of the written JSON file.
        """
        try:
            path = Path(output_path)
            path.parent.mkdir(parents=True, exist_ok=True)

            # Build an enriched JSON structure beyond the raw Pydantic dump
            data = report.model_dump()
            data["export_metadata"] = {
                "exported_at": datetime.utcnow().isoformat(),
                "format": "json",
                "total_candidates": len(report.rankings),
                "top_candidate": report.rankings[0].candidate_name if report.rankings else None,
            }

            with open(path, mode="w", encoding="utf-8") as f:
                f.write(json.dumps(data, indent=2, default=str))
            return str(path.absolute())
        except Exception as e:
            raise ExportException(f"Failed to export JSON: {str(e)}") from e

    def export_markdown_report(self, report: Report, output_path: str) -> str:
        """Exports a rich human-readable Markdown screening report.

        Includes:
        - Score summary table
        - Per-candidate breakdown with matched/missing skills
        - AI reasoning and recommendation

        Args:
            report: Validated Report object with rankings.
            output_path: Destination file path string.

        Returns:
            Absolute path of the written Markdown file.
        """
        try:
            path = Path(output_path)
            path.parent.mkdir(parents=True, exist_ok=True)

            lines = [
                "# AI Resume Screening Report",
                "",
                f"**Job Title:** {report.job_title}",
                f"**Job Description ID:** `{report.job_description_id}`",
                f"**Evaluation Timestamp:** {report.evaluation_timestamp.isoformat()}",
                f"**Total Candidates Processed:** {len(report.rankings)}",
                f"**Report Exported At:** {datetime.utcnow().isoformat()}",
                "",
                "---",
                "",
                "## Rankings Summary",
                "",
                "| Rank | Candidate Name | Overall Score | Skill Match | Experience | Semantic | Confidence |",
                "|------|---------------|:-------------:|:-----------:|:----------:|:--------:|:----------:|",
            ]

            for r in report.rankings:
                b = r.score.breakdown
                lines.append(
                    f"| {r.rank} "
                    f"| {r.candidate_name} "
                    f"| **{r.score.overall_score}%** "
                    f"| {b.skill_match}% "
                    f"| {b.experience_match}% "
                    f"| {b.semantic_similarity}% "
                    f"| {r.score.confidence_score}% |"
                )

            lines.extend([
                "",
                "---",
                "",
                "## Candidate Details",
                "",
            ])

            for r in report.rankings:
                b = r.score.breakdown
                matched = ", ".join(r.score.matched_skills) if r.score.matched_skills else "_None identified_"
                missing = ", ".join(r.score.missing_skills) if r.score.missing_skills else "_None_"

                lines.extend([
                    f"### #{r.rank} — {r.candidate_name}",
                    "",
                    f"> **Candidate ID:** `{r.candidate_id}`",
                    "",
                    "#### Score Breakdown",
                    "",
                    "| Metric | Score |",
                    "|--------|-------|",
                    f"| Overall Score | **{r.score.overall_score}%** |",
                    f"| Skill Match | {b.skill_match}% |",
                    f"| Keyword Match | {b.keyword_match}% |",
                    f"| Experience Match | {b.experience_match}% |",
                    f"| Project Match | {b.project_match}% |",
                    f"| Education Match | {b.education_match}% |",
                    f"| Certification Match | {b.certification_match}% |",
                    f"| Semantic Similarity | {b.semantic_similarity}% |",
                    f"| Confidence Score | {r.score.confidence_score}% |",
                    "",
                    f"**✅ Matched Skills:** {matched}",
                    "",
                    f"**❌ Missing Skills:** {missing}",
                    "",
                    "#### AI Reasoning",
                    "",
                    f"> {r.score.reasoning}",
                    "",
                    "---",
                    "",
                ])

            with open(path, mode="w", encoding="utf-8") as f:
                f.write("\n".join(lines))
            return str(path.absolute())
        except Exception as e:
            raise ExportException(f"Failed to export Markdown report: {str(e)}") from e
