"""Unit tests for SensitiveInfoDetector."""

from src.analysis.sensitive_info_detector import SensitiveInfoDetector
from src.integration.uno_document_adapter import UNODocumentAdapter
from src.models.suggestion import Severity, SuggestionType


def test_email_detection():
    detector = SensitiveInfoDetector()
    text = "Please reach out to support.contact@enterprise-service.org for queries."
    doc = UNODocumentAdapter.from_plain_text(text)

    suggestions = detector.detectEmails(doc)
    assert len(suggestions) == 1
    s = suggestions[0]
    assert s.type == SuggestionType.Privacy
    assert s.category == "Email"
    assert s.originalText == "support.contact@enterprise-service.org"


def test_phone_number_detection():
    detector = SensitiveInfoDetector()
    text = "Call the direct desk at +1-555-923-4812 or 555-123-4567."
    doc = UNODocumentAdapter.from_plain_text(text)

    suggestions = detector.detectPhoneNumbers(doc)
    assert len(suggestions) >= 1
    assert any("Phone" in s.category for s in suggestions)


def test_personal_identifier_detection():
    detector = SensitiveInfoDetector()
    text = "User record with SSN: 000-12-3456."
    doc = UNODocumentAdapter.from_plain_text(text)

    suggestions = detector.detectIdentifiers(doc)
    assert len(suggestions) >= 1
    s = suggestions[0]
    assert s.severity == Severity.Critical
    assert s.originalText == "000-12-3456"

