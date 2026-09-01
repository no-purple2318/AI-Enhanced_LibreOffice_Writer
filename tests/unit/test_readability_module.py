"""Unit tests for ReadabilityModule."""

from src.analysis.readability_module import ReadabilityModule
from src.integration.uno_document_adapter import UNODocumentAdapter
from src.models.suggestion import SuggestionType


def test_flesch_score_calculation():
    module = ReadabilityModule()
    simple_text = "The dog sat on the mat. It was a sunny day. We had fun."
    score = module.calculateScore(simple_text)
    assert score > 70.0

    complex_text = (
        "Notwithstanding the multifaceted institutional considerations regarding alignment, "
        "the administrative committee must ascertain whether the advantageous outcomes "
        "outweigh the considerable architectural complexities inherent in the transformation."
    )
    score_complex = module.calculateScore(complex_text)
    assert score_complex < score


def test_sentence_complexity_detection():
    module = ReadabilityModule()
    long_sentence = "This is an extremely long sentence that continues running on with clause after clause and word after word without taking a pause or inserting a period to ensure that the thirty word threshold is easily surpassed by the test harness."
    doc = UNODocumentAdapter.from_plain_text(long_sentence)

    suggestions = module.analyzeSentenceComplexity(doc)
    assert len(suggestions) >= 1
    assert any("Long sentence detected" in s.message for s in suggestions)


def test_vocabulary_complexity_detection():
    module = ReadabilityModule()
    text = "We endeavor to commence utilization of the new tool."
    doc = UNODocumentAdapter.from_plain_text(text)

    suggestions = module.analyzeVocabulary(doc)
    assert len(suggestions) >= 1
    suggested_replacements = [s.suggestedText for s in suggestions]
    assert any("use" in r for r in suggested_replacements)
    assert any("start" in r for r in suggested_replacements)

