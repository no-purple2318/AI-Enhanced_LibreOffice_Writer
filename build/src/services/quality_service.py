"""Quality scoring service calculating dimensional and weighted overall ratings."""

from typing import Dict, List

from src.models.document import Document
from src.models.quality_score import QualityScore
from src.models.suggestion import Severity, Suggestion, SuggestionType
from src.utils.config import Config
from src.utils.logging import get_logger

logger = get_logger("ai_writer.quality_service")


class QualityService:
    """Calculates deterministic quality ratings based on issue counts, severities, and document metrics."""

    def __init__(self, config: Config = None):
        self.config = config or Config()
        self.weights = self.config.quality_weights
        self.deductions = self.config.severity_deductions

    def calculate_scores(
        self,
        suggestions: List[Suggestion],
        document: Document,
        flesch_reading_ease: float = 100.0,
    ) -> QualityScore:
        """Compute category scores and combined overall score."""
        # Categorize suggestions
        writing_issues = [
            s for s in suggestions if s.type in (SuggestionType.Grammar, SuggestionType.Spelling, SuggestionType.Style)
        ]
        consistency_issues = [
            s for s in suggestions if s.type == SuggestionType.Consistency
        ]
        formatting_issues = [
            s for s in suggestions if s.type == SuggestionType.Formatting
        ]
        readability_issues = [
            s for s in suggestions if s.type == SuggestionType.Readability
        ]
        privacy_issues = [
            s for s in suggestions if s.type == SuggestionType.Privacy
        ]

        word_count = max(1, len(document.getText().split()))
        # Normalization factor for document length (base: 500 words)
        scale_factor = 1.0 if word_count < 500 else (500.0 / word_count)

        writing_score = self._compute_category_score(writing_issues, scale_factor)
        consistency_score = self._compute_category_score(consistency_issues, scale_factor)
        formatting_score = self._compute_category_score(formatting_issues, scale_factor)
        
        # Readability score combines base Flesch score with complexity deductions
        readability_penalty = sum(self.deductions.get(s.severity.value.lower(), 5.0) for s in readability_issues)
        readability_score = max(0.0, min(100.0, (flesch_reading_ease * 0.7) + max(0.0, (30.0 - readability_penalty))))

        # Privacy score (heavy penalties for sensitive personal data)
        privacy_score = self._compute_category_score(privacy_issues, scale_factor=1.0)

        score = QualityScore(
            writingScore=round(writing_score, 1),
            consistencyScore=round(consistency_score, 1),
            formattingScore=round(formatting_score, 1),
            readabilityScore=round(readability_score, 1),
            privacyScore=round(privacy_score, 1),
            writingWeight=self.weights.get("writing", 0.25),
            consistencyWeight=self.weights.get("consistency", 0.20),
            formattingWeight=self.weights.get("formatting", 0.20),
            readabilityWeight=self.weights.get("readability", 0.20),
            privacyWeight=self.weights.get("privacy", 0.15),
        )
        score.calculate()
        return score

    def _compute_category_score(
        self, issues: List[Suggestion], scale_factor: float = 1.0
    ) -> float:
        """Compute 0-100 score by applying severity penalties."""
        penalty = 0.0
        for issue in issues:
            deduction = self.deductions.get(issue.severity.value.lower(), 5.0)
            penalty += deduction * scale_factor
        return max(0.0, 100.0 - penalty)
