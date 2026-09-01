"""Safety and edge-case tests validating strict non-destructive document handling."""

from src.ai.mock_provider import MockProvider
from src.controller.ai_controller import AIController
from src.integration.uno_document_adapter import UNODocumentAdapter
from src.models.document_range import DocumentRange
from src.models.suggestion import (
    Severity,
    Suggestion,
    SuggestionStatus,
    SuggestionType,
)
from src.services.suggestion_service import SuggestionService


def test_safety_user_edits_document_after_analysis():
    controller = AIController(ai_provider=MockProvider())
    doc = UNODocumentAdapter.from_plain_text("This are the initial text.")

    result = controller.analyze(doc)
    sugg = result.suggestions[0]
    assert sugg.originalText == "This are"

    p0 = doc.get_paragraph(0)
    p0.text = "Completely altered text here."

    success, reason = controller.applySuggestion(sugg, doc)

    assert not success
    assert sugg.status == SuggestionStatus.StaleConflicted
    assert "Document content changed" in reason
    assert doc.getText() == "Completely altered text here."


def test_safety_duplicate_text_strings_in_different_paragraphs():
    service = SuggestionService()
    doc = UNODocumentAdapter.from_plain_text("First line with teh error.\nSecond line with teh error.")

    sugg_p1 = Suggestion(
        type=SuggestionType.Spelling,
        originalText="teh",
        suggestedText="the",
        range=DocumentRange(paragraph_id=1, start_offset=17, end_offset=20),
        status=SuggestionStatus.New,
    )

    success, _ = service.apply_suggestion(sugg_p1, doc)
    assert success

    assert doc.get_paragraph(0).text == "First line with teh error."
    assert doc.get_paragraph(1).text == "Second line with the error."


def test_safety_out_of_bounds_range_rejected():
    service = SuggestionService()
    doc = UNODocumentAdapter.from_plain_text("Short text.")

    sugg_bad = Suggestion(
        type=SuggestionType.Grammar,
        originalText="foo",
        suggestedText="bar",
        range=DocumentRange(paragraph_id=0, start_offset=50, end_offset=60),
    )

    success, reason = service.apply_suggestion(sugg_bad, doc)
    assert not success
    assert sugg_bad.status == SuggestionStatus.StaleConflicted


def test_safety_module_failure_resilience():
    failing_provider = MockProvider(should_fail=True)
    controller = AIController(ai_provider=failing_provider)

    doc = UNODocumentAdapter.from_plain_text(
        "John Smith and Jon Smith.\nEmail contact: test@example.com\n10 pages vs ten pages."
    )
    result = controller.analyze(doc)

    assert "WritingAssistant" in result.moduleErrors
    assert len(result.suggestions) > 0
    categories = {s.category for s in result.suggestions}
    assert "Email" in categories or "Names" in categories


def test_safety_reject_and_ignore_do_not_modify_document():
    controller = AIController(ai_provider=MockProvider())
    doc = UNODocumentAdapter.from_plain_text("This are unchanged text.")
    original_text = doc.getText()

    result = controller.analyze(doc)
    sugg = result.suggestions[0]

    controller.rejectSuggestion(sugg)
    assert sugg.status == SuggestionStatus.Rejected
    assert doc.getText() == original_text

    controller.ignoreSuggestion(sugg)
    assert sugg.status == SuggestionStatus.Ignored
    assert doc.getText() == original_text

