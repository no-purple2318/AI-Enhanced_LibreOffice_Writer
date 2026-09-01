"""ReportService handling document quality report generation and multi-format export."""

from typing import Optional

from src.models.analysis_result import AnalysisResult
from src.models.report import Report
from src.utils.logging import get_logger

logger = get_logger("ai_writer.report_service")


class ReportService:
    """Manages creation, formatting, and file export of document quality reports."""

    def generate_report(self, analysis_result: AnalysisResult) -> Report:
        """Create a new Report from an AnalysisResult."""
        report = Report()
        report.generate(analysis_result)
        logger.info(f"Generated quality report for {analysis_result.fileName} (Score: {analysis_result.qualityScore.overallScore:.1f})")
        return report

    def export_report(
        self, report: Report, file_path: Optional[str] = None, format: str = "markdown"
    ) -> str:
        """Export report to disk in markdown, html, or txt."""
        exported_path = report.export(file_path=file_path, format=format)
        logger.info(f"Exported quality report to: {exported_path}")
        return exported_path
