from abc import ABC, abstractmethod

from app.models.report import Report


class BaseReportExporter(ABC):
    """Abstract Base Class for exporting candidate rankings and evaluation details."""

    @abstractmethod
    def export_csv(self, report: Report, output_path: str) -> str:
        """Writes report rankings to a CSV flat file.

        Args:
            report: Evaluation results.
            output_path: Target write directory or full file path.

        Returns:
            The final written filepath location.

        Raises:
            ExportException: If file write fails.
        """
        pass

    @abstractmethod
    def export_json(self, report: Report, output_path: str) -> str:
        """Writes report details to a JSON serialization.

        Args:
            report: Evaluation results.
            output_path: Target write directory or full file path.

        Returns:
            The final written filepath location.

        Raises:
            ExportException: If file write fails.
        """
        pass

    @abstractmethod
    def export_markdown_report(self, report: Report, output_path: str) -> str:
        """Writes report details to an comprehensive Markdown file.

        Args:
            report: Evaluation results.
            output_path: Target write directory or full file path.

        Returns:
            The final written filepath location.

        Raises:
            ExportException: If file write fails.
        """
        pass
