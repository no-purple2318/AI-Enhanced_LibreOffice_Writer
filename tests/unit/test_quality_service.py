"""Unit tests for QualityService calculation."""

from src.integration.uno_document_adapter import UNODocumentAdapter
from src.models.suggestion import (
    Severity,
    Suggestion,
    SuggestionStatus,
    SuggestionType,
)
from src.services.quality_service import QualityService


def test_quality_service_clean_document():
    qs_service = QualityService()
    doc = UNODocumentAdapter.from_plain_text("A simple, clean document.")
    score = qs_service.calculate_scores(suggestions=[], document=doc, flesch_reading_ease=100.0)

    assert score.overallScore == 100.0
    assert score.writingScore == 100.0
    assert score.consistencyScore == 100.0
    assert score.formattingScore == 100.0
    assert score.readabilityScore == 100.0
    assert score.privacyScore == 100.0


def test_quality_service_penalties():
    qs_service = QualityService()
    doc = UNODocumentAdapter.from_plain_text("Document with issues.")

    suggestions = [
        Suggestion(type=SuggestionType.Grammar, severity=Severity.Medium),
        Suggestion(type=SuggestionType.Spelling, severity=Severity.Low),
        Suggestion(type=SuggestionType.Privacy, severity=Severity.Critical),
    ]

    score = qs_service.calculate_scores(suggestions=suggestions, document=doc, flesch_reading_ease=80.0)

    assert score.writingScore < 100.0
    assert score.privacyScore <= 80.0
    assert score.overallScore < 100.0

