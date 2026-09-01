"""Unit tests for ConsistencyAnalyzer."""

from src.analysis.consistency_analyzer import ConsistencyAnalyzer
from src.integration.uno_document_adapter import UNODocumentAdapter
from src.models.suggestion import SuggestionType


def test_name_consistency_fuzzy_detection():
    analyzer = ConsistencyAnalyzer()
    text = "John Smith authored the code. Later, Jon Smith reviewed the patch."
    doc = UNODocumentAdapter.from_plain_text(text)

    suggestions = analyzer.checkNames(doc)
    assert len(suggestions) >= 1
    s = suggestions[0]
    assert s.category == "Names"
    assert "Possible name inconsistency detected" in s.message
    assert "Jon Smith" in s.message or "John Smith" in s.message


def test_terminology_consistency_detection():
    analyzer = ConsistencyAnalyzer()
    text = "The team deployed the AI model yesterday. The artificial intelligence model runs smoothly."
    doc = UNODocumentAdapter.from_plain_text(text)

    suggestions = analyzer.checkTerminology(doc)
    assert len(suggestions) >= 1
    s = suggestions[0]
    assert s.category == "Terminology"
    assert "Inconsistent terminology" in s.message


def test_date_and_number_consistency_detection():
    analyzer = ConsistencyAnalyzer()
    text = "The contract starts on 12/04/2026 and ends on 2026-04-12.\nWe reviewed 10 pages in section A and ten pages in section B."
    doc = UNODocumentAdapter.from_plain_text(text)

    suggestions = analyzer.validateDatesAndNumbers(doc)
    assert len(suggestions) >= 1
    categories = [s.category for s in suggestions]
    assert "Dates" in categories or "Numbers" in categories

