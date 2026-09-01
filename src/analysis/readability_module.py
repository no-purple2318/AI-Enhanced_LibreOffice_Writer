"""Readability Assessment Module computing Flesch score, sentence complexity, and vocabulary complexity."""

import re
from typing import Any, Dict, List, Optional, Tuple

from src.analysis.analysis_module import AnalysisModule
from src.models.document import Document
from src.models.document_range import DocumentRange
from src.models.suggestion import (
    Severity,
    Suggestion,
    SuggestionStatus,
    SuggestionType,
)


class ReadabilityModule(AnalysisModule):
    """Evaluates document readability metrics and flags complex sentences and vocabulary."""

    # Difficult / complex words with simpler recommended synonyms
    COMPLEX_WORDS_MAP = {
        "utilization": "use",
        "commence": "start or begin",
        "terminate": "end or stop",
        "facilitate": "help or ease",
        "endeavor": "try or attempt",
        "demonstrate": "show",
        "subsequently": "later or after",
        "approximately": "about",
        "implement": "carry out or start",
        "modification": "change",
        "fundamental": "basic",
        "advantageous": "helpful",
        "disseminate": "share or spread",
        "expeditious": "fast or prompt",
        "promulgate": "announce or publish",
    }

    def __init__(self, moduleId: Optional[str] = None):
        super().__init__(moduleId=moduleId, moduleName="ReadabilityModule")
        self._last_flesch_score: float = 100.0

    @staticmethod
    def _count_syllables(word: str) -> int:
        """Estimate syllable count of an English word."""
        word = word.lower().strip(".:;?!,'\"-")
        if not word:
            return 0
        if len(word) <= 3:
            return 1
        # Remove trailing 'e'
        if word.endswith("e") and not word.endswith("le"):
            word = word[:-1]
        vowels = "aeiouy"
        count = 0
        prev_is_vowel = False
        for char in word:
            is_vowel = char in vowels
            if is_vowel and not prev_is_vowel:
                count += 1
            prev_is_vowel = is_vowel
        return max(1, count)

    @classmethod
    def _split_sentences(cls, text: str) -> List[str]:
        """Split text into sentences."""
        sentences = re.split(r"(?<=[.!?])\s+", text)
        return [s.strip() for s in sentences if s.strip()]

    def calculateScore(self, text: str) -> float:
        """Calculate Flesch Reading Ease score (0.0 to 100.0 scale)."""
        words = re.findall(r"\b[A-Za-z]+\b", text)
        if not words:
            self._last_flesch_score = 100.0
            return 100.0

        sentences = self._split_sentences(text)
        total_sentences = max(1, len(sentences))
        total_words = len(words)
        total_syllables = sum(self._count_syllables(w) for w in words)

        # Flesch Reading Ease formula
        flesch = (
            206.835
            - (1.015 * (total_words / total_sentences))
            - (84.6 * (total_syllables / total_words))
        )
        score = round(max(0.0, min(100.0, flesch)), 1)
        self._last_flesch_score = score
        return score

    def analyzeSentenceComplexity(self, document: Document) -> List[Suggestion]:
        """Flag overly long (> 30 words) or syntactically dense sentences."""
        suggestions = []
        for p in document.paragraphs:
            if not p.text.strip():
                continue
            sentences = self._split_sentences(p.text)
            for s_text in sentences:
                words = s_text.split()
                if len(words) >= 30:
                    start = p.text.find(s_text)
                    if start == -1:
                        start = 0
                    end = start + len(s_text)
                    s = Suggestion(
                        type=SuggestionType.Readability,
                        category="Sentence Complexity",
                        message=f"Long sentence detected ({len(words)} words). Consider breaking into 2 or more shorter sentences for clarity.",
                        originalText=s_text,
                        suggestedText="",
                        range=DocumentRange(
                            paragraph_id=p.id,
                            start_offset=start,
                            end_offset=end,
                        ),
                        position=f"Paragraph {p.id + 1}",
                        severity=Severity.Medium if len(words) < 40 else Severity.High,
                        status=SuggestionStatus.New,
                    )
                    suggestions.append(s)
        return suggestions

    def analyzeVocabulary(self, document: Document) -> List[Suggestion]:
        """Flag complex/dense words and provide simpler vocabulary recommendations."""
        suggestions = []
        for p in document.paragraphs:
            if not p.text.strip():
                continue
            for match in re.finditer(r"\b[A-Za-z]+\b", p.text):
                w = match.group(0)
                w_lower = w.lower()
                if w_lower in self.COMPLEX_WORDS_MAP:
                    simpler = self.COMPLEX_WORDS_MAP[w_lower]
                    if w.isupper():
                        simpler = simpler.upper()
                    elif w[0].isupper():
                        simpler = simpler.capitalize()

                    s = Suggestion(
                        type=SuggestionType.Readability,
                        category="Vocabulary",
                        message=f"Complex vocabulary: '{w}' can be simplified to '{simpler}'.",
                        originalText=w,
                        suggestedText=simpler,
                        range=DocumentRange(
                            paragraph_id=p.id,
                            start_offset=match.start(),
                            end_offset=match.end(),
                        ),
                        position=f"Paragraph {p.id + 1}",
                        severity=Severity.Low,
                        status=SuggestionStatus.New,
                    )
                    suggestions.append(s)
        return suggestions

    def generateSuggestions(self, document: Document) -> List[Suggestion]:
        """Generate all readability improvement suggestions."""
        return self.analyze(document)

    def analyze(self, document: Document) -> List[Suggestion]:
        """Run complete readability assessment on the document."""
        if not document:
            return []

        text = document.getText()
        self.calculateScore(text)

        suggestions: List[Suggestion] = []
        suggestions.extend(self.analyzeSentenceComplexity(document))
        suggestions.extend(self.analyzeVocabulary(document))

        for s in suggestions:
            s.revision = document.current_revision

        return suggestions
