"""AnalysisResult model aggregating document analysis output."""

import uuid
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional

from src.models.quality_score import QualityScore
from src.models.suggestion import Severity, Suggestion, SuggestionStatus, SuggestionType


@dataclass
class AnalysisResult:
    """Encapsulates the complete result of a document analysis session."""

    resultId: str = field(default_factory=lambda: str(uuid.uuid4()))
    documentId: str = ""
    fileName: str = "Untitled.odt"
    analyzedAt: datetime = field(default_factory=datetime.utcnow)
    suggestions: List[Suggestion] = field(default_factory=list)
    qualityScore: QualityScore = field(default_factory=QualityScore)
    moduleExecutionTimes: Dict[str, float] = field(default_factory=dict)
    moduleErrors: Dict[str, str] = field(default_factory=dict)
    wordCount: int = 0
    paragraphCount: int = 0

    def getSummary(self) -> Dict[str, Any]:
        """Return high-level summary of analysis findings."""
        by_type: Dict[str, int] = {}
        for st in SuggestionType:
            by_type[st.value] = sum(1 for s in self.suggestions if s.type == st)

        by_severity: Dict[str, int] = {}
        for sev in Severity:
            by_severity[sev.value] = sum(1 for s in self.suggestions if s.severity == sev)

        by_status: Dict[str, int] = {}
        for stat in SuggestionStatus:
            by_status[stat.value] = sum(1 for s in self.suggestions if s.status == stat)

        return {
            "resultId": self.resultId,
            "documentId": self.documentId,
            "fileName": self.fileName,
            "analyzedAt": self.analyzedAt.isoformat(),
            "overallScore": self.qualityScore.overallScore,
            "scores": self.qualityScore.to_dict(),
            "totalIssues": len(self.suggestions),
            "byType": by_type,
            "bySeverity": by_severity,
            "byStatus": by_status,
            "wordCount": self.wordCount,
            "paragraphCount": self.paragraphCount,
            "errors": self.moduleErrors,
        }

    def getSuggestions(self, status: Optional[SuggestionStatus] = None) -> List[Suggestion]:
        """Return list of suggestions, optionally filtered by status."""
        if status:
            return [s for s in self.suggestions if s.status == status]
        return list(self.suggestions)

    def getQualityScore(self) -> float:
        """Return overall numeric quality score."""
        return self.qualityScore.overallScore

    def to_dict(self) -> Dict[str, Any]:
        return {
            "resultId": self.resultId,
            "documentId": self.documentId,
            "fileName": self.fileName,
            "analyzedAt": self.analyzedAt.isoformat(),
            "qualityScore": self.qualityScore.to_dict(),
            "suggestions": [s.to_dict() for s in self.suggestions],
            "moduleExecutionTimes": self.moduleExecutionTimes,
            "moduleErrors": self.moduleErrors,
            "wordCount": self.wordCount,
            "paragraphCount": self.paragraphCount,
        }
