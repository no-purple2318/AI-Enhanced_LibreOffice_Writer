"""Report model and export generators for AI-Enhanced LibreOffice Writer."""

import os
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, Optional

from src.models.analysis_result import AnalysisResult
from src.models.suggestion import Severity, SuggestionType


@dataclass
class Report:
    """Document Quality Report generated from an AnalysisResult."""

    reportId: str = field(default_factory=lambda: str(uuid.uuid4()))
    generatedAt: datetime = field(default_factory=datetime.utcnow)
    summary: str = ""
    filePath: str = ""
    content_markdown: str = ""
    content_html: str = ""
    content_text: str = ""
    result: Optional[AnalysisResult] = None

    def generate(self, result: AnalysisResult) -> "Report":
        """Generate comprehensive multi-format report from analysis result."""
        self.result = result
        self.generatedAt = datetime.utcnow()
        summary_data = result.getSummary()

        qs = result.qualityScore
        date_str = self.generatedAt.strftime("%Y-%m-%d %H:%M:%S UTC")

        # Generate Plain Text
        lines = [
            "============================================================",
            "AI-Enhanced LibreOffice Writer",
            "Document Quality Report",
            "============================================================",
            f"Document:        {result.fileName}",
            f"Analysis Date:   {date_str}",
            f"Overall Score:   {qs.overallScore:.1f} / 100",
            "",
            "--- CATEGORY SCORES ---",
            f"Writing:         {qs.writingScore:.1f} / 100  (Weight: {qs.writingWeight*100:.0f}%)",
            f"Consistency:     {qs.consistencyScore:.1f} / 100  (Weight: {qs.consistencyWeight*100:.0f}%)",
            f"Formatting:      {qs.formattingScore:.1f} / 100  (Weight: {qs.formattingWeight*100:.0f}%)",
            f"Readability:     {qs.readabilityScore:.1f} / 100  (Weight: {qs.readabilityWeight*100:.0f}%)",
            f"Privacy:         {qs.privacyScore:.1f} / 100  (Weight: {qs.privacyWeight*100:.0f}%)",
            "",
            "--- ISSUE SUMMARY ---",
            f"Critical:        {summary_data['bySeverity'].get('Critical', 0)}",
            f"High:            {summary_data['bySeverity'].get('High', 0)}",
            f"Medium:          {summary_data['bySeverity'].get('Medium', 0)}",
            f"Low:             {summary_data['bySeverity'].get('Low', 0)}",
            f"Total Issues:    {len(result.suggestions)}",
            "",
        ]

        # Privacy Warnings Section
        privacy_issues = [
            s for s in result.suggestions if s.type == SuggestionType.Privacy
        ]
        if privacy_issues:
            lines.append("--- PRIVACY & SENSITIVE INFORMATION ALERTS ---")
            lines.append(
                "WARNING: Review the following sensitive items before sharing or publishing:"
            )
            for idx, p in enumerate(privacy_issues, 1):
                lines.append(
                    f"  [{idx}] [{p.severity.value}] {p.category}: {p.message} (Location: {p.position})"
                )
            lines.append("")

        # Detailed Findings Section
        lines.append("--- DETAILED FINDINGS ---")
        if not result.suggestions:
            lines.append("No issues detected! Document conforms to quality rules.")
        else:
            for idx, s in enumerate(result.suggestions, 1):
                lines.append(f"Issue #{idx}")
                lines.append(f"  Category:       {s.type.value} - {s.category}")
                lines.append(f"  Severity:       {s.severity.value}")
                lines.append(f"  Location:       {s.position}")
                lines.append(f"  Status:         {s.status.value}")
                lines.append(f"  Problem:        {s.message}")
                if s.originalText:
                    lines.append(f"  Original:       \"{s.originalText}\"")
                if s.suggestedText:
                    lines.append(f"  Recommendation: \"{s.suggestedText}\"")
                lines.append("")

        self.content_text = "\n".join(lines)

        # Generate Markdown
        md = [
            "# AI-Enhanced LibreOffice Writer",
            "## Document Quality Report",
            "",
            f"**Document:** `{result.fileName}`  ",
            f"**Analysis Date:** {date_str}  ",
            f"**Overall Score:** **{qs.overallScore:.1f} / 100**",
            "",
            "### Category Scores",
            "| Category | Score | Weight |",
            "| :--- | :--- | :--- |",
            f"| **Writing** | {qs.writingScore:.1f} / 100 | {qs.writingWeight*100:.0f}% |",
            f"| **Consistency** | {qs.consistencyScore:.1f} / 100 | {qs.consistencyWeight*100:.0f}% |",
            f"| **Formatting** | {qs.formattingScore:.1f} / 100 | {qs.formattingWeight*100:.0f}% |",
            f"| **Readability** | {qs.readabilityScore:.1f} / 100 | {qs.readabilityWeight*100:.0f}% |",
            f"| **Privacy** | {qs.privacyScore:.1f} / 100 | {qs.privacyWeight*100:.0f}% |",
            "",
            "### Issue Breakdown",
            f"- **Critical:** {summary_data['bySeverity'].get('Critical', 0)}",
            f"- **High:** {summary_data['bySeverity'].get('High', 0)}",
            f"- **Medium:** {summary_data['bySeverity'].get('Medium', 0)}",
            f"- **Low:** {summary_data['bySeverity'].get('Low', 0)}",
            f"- **Total Detected:** {len(result.suggestions)}",
            "",
        ]

        if privacy_issues:
            md.append("### ⚠️ Privacy Warnings")
            md.append(
                "> **CAUTION:** The document contains sensitive items that should be verified prior to sharing:"
            )
            for p in privacy_issues:
                md.append(
                    f"- **[{p.severity.value}] {p.category}:** {p.message} at `{p.position}`"
                )
            md.append("")

        md.append("### Detailed Findings")
        if not result.suggestions:
            md.append("*No issues detected.*")
        else:
            md.append(
                "| # | Category | Severity | Location | Problem / Recommendation | Status |"
            )
            md.append(
                "| :--- | :--- | :--- | :--- | :--- | :--- |"
            )
            for idx, s in enumerate(result.suggestions, 1):
                rec = (
                    f"`{s.originalText}` $\\to$ `{s.suggestedText}`"
                    if s.originalText and s.suggestedText
                    else s.message
                )
                md.append(
                    f"| {idx} | {s.type.value} ({s.category}) | {s.severity.value} | {s.position} | {rec} | {s.status.value} |"
                )

        self.content_markdown = "\n".join(md)

        # Generate HTML
        self.content_html = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>Document Quality Report - {result.fileName}</title>
    <style>
        body {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif; line-height: 1.6; padding: 2rem; color: #2d3748; background: #f7fafc; }}
        .container {{ max-width: 900px; margin: auto; background: white; padding: 2.5rem; border-radius: 8px; box-shadow: 0 4px 6px rgba(0,0,0,0.05); }}
        h1 {{ color: #1a202c; border-bottom: 2px solid #edf2f7; padding-bottom: 0.5rem; }}
        .score-box {{ background: #ebf8ff; border: 1px solid #bee3f8; border-radius: 6px; padding: 1.5rem; margin: 1.5rem 0; }}
        .score-box h2 {{ margin-top: 0; color: #2b6cb0; }}
        table {{ width: 100%; border-collapse: collapse; margin: 1rem 0; }}
        th, td {{ padding: 0.75rem; text-align: left; border-bottom: 1px solid #e2e8f0; }}
        th {{ background: #f7fafc; font-weight: 600; }}
        .badge {{ display: inline-block; padding: 0.25rem 0.5rem; border-radius: 4px; font-size: 0.8rem; font-weight: bold; }}
        .badge-Critical {{ background: #fed7d7; color: #9b2c2c; }}
        .badge-High {{ background: #feebc8; color: #9c4221; }}
        .badge-Medium {{ background: #fefcbf; color: #744210; }}
        .badge-Low {{ background: #e2e8f0; color: #4a5568; }}
        .privacy-alert {{ background: #fff5f5; border-left: 4px solid #e53e3e; padding: 1rem; margin: 1rem 0; border-radius: 4px; }}
    </style>
</head>
<body>
    <div class="container">
        <h1>AI-Enhanced LibreOffice Writer</h1>
        <h3>Document Quality Report</h3>
        <p><strong>Document:</strong> {result.fileName}<br><strong>Date:</strong> {date_str}</p>
        
        <div class="score-box">
            <h2>Overall Quality Score: {qs.overallScore:.1f} / 100</h2>
            <table>
                <tr><th>Category</th><th>Score</th><th>Weight</th></tr>
                <tr><td>Writing</td><td>{qs.writingScore:.1f} / 100</td><td>{qs.writingWeight*100:.0f}%</td></tr>
                <tr><td>Consistency</td><td>{qs.consistencyScore:.1f} / 100</td><td>{qs.consistencyWeight*100:.0f}%</td></tr>
                <tr><td>Formatting</td><td>{qs.formattingScore:.1f} / 100</td><td>{qs.formattingWeight*100:.0f}%</td></tr>
                <tr><td>Readability</td><td>{qs.readabilityScore:.1f} / 100</td><td>{qs.readabilityWeight*100:.0f}%</td></tr>
                <tr><td>Privacy</td><td>{qs.privacyScore:.1f} / 100</td><td>{qs.privacyWeight*100:.0f}%</td></tr>
            </table>
        </div>

        <h3>Findings ({len(result.suggestions)} issues)</h3>
        <table>
            <tr><th>#</th><th>Type</th><th>Severity</th><th>Location</th><th>Issue & Recommendation</th><th>Status</th></tr>
            {"".join(f'<tr><td>{i}</td><td>{s.type.value}</td><td><span class="badge badge-{s.severity.value}">{s.severity.value}</span></td><td>{s.position}</td><td>{s.message}<br><small>{s.originalText} &rarr; {s.suggestedText if s.suggestedText else ""}</small></td><td>{s.status.value}</td></tr>' for i, s in enumerate(result.suggestions, 1))}
        </table>
    </div>
</body>
</html>"""
        self.summary = f"Quality Score: {qs.overallScore:.1f}/100. Total Issues: {len(result.suggestions)}."
        return self

    def export(self, file_path: Optional[str] = None, format: str = "markdown") -> str:
        """Export the generated report to disk in the requested format (markdown, html, text)."""
        target_path = file_path or self.filePath
        if not target_path:
            ext = (
                "md"
                if format == "markdown"
                else ("html" if format == "html" else "txt")
            )
            target_path = f"report_{self.reportId[:8]}.{ext}"

        content = self.content_markdown
        if format.lower() == "html":
            content = self.content_html
        elif format.lower() in ("text", "txt"):
            content = self.content_text

        os.makedirs(os.path.dirname(os.path.abspath(target_path)), exist_ok=True)
        with open(target_path, "w", encoding="utf-8") as f:
            f.write(content)

        self.filePath = target_path
        return target_path
