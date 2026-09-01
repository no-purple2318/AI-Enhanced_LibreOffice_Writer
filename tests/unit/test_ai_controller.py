"""Unit tests for AIController orchestration."""

from src.ai.mock_provider import MockProvider
from src.controller.ai_controller import AIController
from src.integration.uno_document_adapter import UNODocumentAdapter
from src.models.suggestion import SuggestionStatus, SuggestionType


def test_ai_controller_full_analysis():
    mock_provider = MockProvider()
    controller = AIController(ai_provider=mock_provider)

    text = """# Test Title
This are a test paragraph.
We definately need to recieve Jon Smith's approval.
John Smith will review.
Contact test@company.com or 555-123-4567.
"""
    doc = UNODocumentAdapter.from_plain_text(text, fileName="TestDoc.odt")
    result = controller.analyze(doc)

    assert result.documentId == doc.documentId
    assert len(result.suggestions) > 0
    assert result.qualityScore.overallScore < 100.0

    report = controller.generateReport(result)
    assert report.result is result
    assert len(report.content_markdown) > 50


def test_ai_controller_suggestion_actions():
    controller = AIController(ai_provider=MockProvider())
    doc = UNODocumentAdapter.from_plain_text("This are a test document.")
    result = controller.analyze(doc)

    grammar_suggs = [s for s in result.suggestions if s.type == SuggestionType.Grammar]
    assert len(grammar_suggs) >= 1
    s = grammar_suggs[0]

    success, reason = controller.applySuggestion(s, doc)
    assert success
    assert s.status == SuggestionStatus.Applied
    assert "This is a test document." in doc.getText()

