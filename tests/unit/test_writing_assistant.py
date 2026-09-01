"""Unit tests for WritingAssistant module."""

from src.ai.local_provider import LocalRuleBasedProvider
from src.ai.mock_provider import MockProvider
from src.analysis.writing_assistant import WritingAssistant
from src.integration.uno_document_adapter import UNODocumentAdapter
from src.models.suggestion import SuggestionType


def test_writing_assistant_grammar_detection():
    assistant = WritingAssistant(ai_provider=LocalRuleBasedProvider())
    text = "This are a example of an issue."
    suggestions = assistant.checkGrammar(text)

    assert len(suggestions) >= 1
    grammar_sugg = [s for s in suggestions if s.type == SuggestionType.Grammar]
    assert any("This is" in s.suggestedText for s in grammar_sugg)


def test_writing_assistant_spelling_detection():
    assistant = WritingAssistant(ai_provider=LocalRuleBasedProvider())
    text = "We definately need to recieve teh email."
    suggestions = assistant.checkSpelling(text)

    assert len(suggestions) >= 2
    words_suggested = [s.suggestedText for s in suggestions]
    assert "definitely" in words_suggested
    assert "receive" in words_suggested


def test_writing_assistant_style_suggestions():
    assistant = WritingAssistant(ai_provider=LocalRuleBasedProvider())
    text = "In order to optimize performance, at this point in time we utilize new techniques."
    suggestions = assistant.generateStyleSuggestions(text)

    assert len(suggestions) >= 2
    style_sugg = [s for s in suggestions if s.type == SuggestionType.Style]
    assert any("to" == s.suggestedText for s in style_sugg)
    assert any("now" == s.suggestedText for s in style_sugg)


def test_writing_assistant_with_mock_provider():
    mock = MockProvider()
    assistant = WritingAssistant(ai_provider=mock)
    doc = UNODocumentAdapter.from_plain_text("This are a test. We will recieve teh update in order to succeed.")
    suggestions = assistant.analyze(doc)

    assert len(suggestions) >= 3
    types = {s.type for s in suggestions}
    assert SuggestionType.Grammar in types
    assert SuggestionType.Spelling in types
    assert SuggestionType.Style in types

