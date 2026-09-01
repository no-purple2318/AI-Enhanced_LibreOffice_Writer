"""Unit tests for domain models."""

from src.models.document import Document, Formatting, Heading, Paragraph
from src.models.document_range import DocumentRange
from src.models.document_revision import DocumentRevision
from src.models.quality_score import QualityScore
from src.models.report import Report
from src.models.suggestion import (
    Severity,
    Suggestion,
    SuggestionStatus,
    SuggestionType,
)


def test_document_range_basics():
    dr = DocumentRange(paragraph_id=2, start_offset=10, end_offset=25)
    assert dr.length == 15
    assert str(dr) == "P2[10:25]"
    d_dict = dr.to_dict()
    assert d_dict["paragraph_id"] == 2
    assert d_dict["start_offset"] == 10
    assert d_dict["end_offset"] == 25

    dr_restored = DocumentRange.from_dict(d_dict)
    assert dr_restored.paragraph_id == 2
    assert dr_restored.length == 15


def test_document_revision_tracking():
    paragraphs = ["First paragraph text.", "Second paragraph text with details."]
    rev = DocumentRevision.create_from_paragraphs("doc-123", paragraphs)

    assert rev.document_id == "doc-123"
    assert rev.total_paragraph_count == 2
    assert rev.is_paragraph_valid(0, "First paragraph text.")
    assert rev.is_paragraph_valid(1, "Second paragraph text with details.")
    assert not rev.is_paragraph_valid(0, "Modified text.")
    assert not rev.is_paragraph_valid(99, "Non-existent.")


def test_suggestion_lifecycle():
    s = Suggestion(
        type=SuggestionType.Grammar,
        category="Grammar",
        message="Use 'is' instead of 'are'.",
        originalText="This are",
        suggestedText="This is",
        range=DocumentRange(paragraph_id=0, start_offset=0, end_offset=8),
        severity=Severity.Medium,
    )
    assert s.status == SuggestionStatus.New

    assert s.accept()
    assert s.status == SuggestionStatus.Accepted

    assert s.apply()
    assert s.status == SuggestionStatus.Applied

    s_stale = Suggestion(message="Test")
    s_stale.mark_stale("Content shifted")
    assert s_stale.status == SuggestionStatus.StaleConflicted
    assert not s_stale.apply()
    assert not s_stale.accept()

    s_rej = Suggestion()
    s_rej.reject()
    assert s_rej.status == SuggestionStatus.Rejected

    s_ign = Suggestion()
    s_ign.ignore()
    assert s_ign.status == SuggestionStatus.Ignored


def test_quality_score_calculation():
    qs = QualityScore(
        writingScore=80.0,
        consistencyScore=90.0,
        formattingScore=85.0,
        readabilityScore=75.0,
        privacyScore=100.0,
    )
    overall = qs.calculate()
    assert overall == 85.0
    assert qs.overallScore == 85.0


def test_report_generation():
    doc = Document(fileName="TestReportDoc.odt")
    p = Paragraph(id=0, text="Sample text", formatting=Formatting())
    doc.paragraphs = [p]

    from src.models.analysis_result import AnalysisResult

    res = AnalysisResult(
        documentId=doc.documentId,
        fileName=doc.fileName,
        suggestions=[
            Suggestion(
                type=SuggestionType.Grammar,
                category="Grammar",
                message="Error",
                originalText="This are",
                suggestedText="This is",
                severity=Severity.Medium,
            )
        ],
        qualityScore=QualityScore(overallScore=85.0),
    )
    report = Report()
    report.generate(res)
    assert "AI-Enhanced LibreOffice Writer" in report.content_text
    assert "TestReportDoc.odt" in report.content_markdown
    assert "85.0 / 100" in report.content_html

