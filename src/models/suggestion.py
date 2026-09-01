"""Suggestion model and related enumerations."""

import uuid
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, Optional

from src.models.document_range import DocumentRange
from src.models.document_revision import DocumentRevision


class SuggestionType(str, Enum):
    Grammar = "Grammar"
    Spelling = "Spelling"
    Style = "Style"
    Consistency = "Consistency"
    Formatting = "Formatting"
    Readability = "Readability"
    Privacy = "Privacy"


class SuggestionStatus(str, Enum):
    New = "New"
    Accepted = "Accepted"
    Applied = "Applied"
    Rejected = "Rejected"
    Ignored = "Ignored"
    StaleConflicted = "Stale/Conflicted"


class Severity(str, Enum):
    Low = "Low"
    Medium = "Medium"
    High = "High"
    Critical = "Critical"


@dataclass
class Suggestion:
    """Represents an intelligent document improvement suggestion."""

    suggestionId: str = field(default_factory=lambda: str(uuid.uuid4()))
    type: SuggestionType = SuggestionType.Grammar
    category: str = "General"
    message: str = ""
    originalText: str = ""
    suggestedText: str = ""
    position: str = ""
    range: Optional[DocumentRange] = None
    revision: Optional[DocumentRevision] = None
    severity: Severity = Severity.Medium
    status: SuggestionStatus = SuggestionStatus.New
    createdAt: datetime = field(default_factory=datetime.utcnow)
    statusReason: str = ""

    def apply(self) -> bool:
        """Mark suggestion as accepted/applied."""
        if self.status == SuggestionStatus.StaleConflicted:
            return False
        self.status = SuggestionStatus.Applied
        return True

    def accept(self) -> bool:
        """Mark suggestion as accepted by user prior to document update."""
        if self.status == SuggestionStatus.StaleConflicted:
            return False
        self.status = SuggestionStatus.Accepted
        return True

    def reject(self) -> None:
        """Reject the suggestion."""
        self.status = SuggestionStatus.Rejected

    def ignore(self) -> None:
        """Ignore the suggestion."""
        self.status = SuggestionStatus.Ignored

    def mark_stale(self, reason: str = "Document changed after analysis") -> None:
        """Flag suggestion as conflicted/stale to prevent unsafe modification."""
        self.status = SuggestionStatus.StaleConflicted
        self.statusReason = reason

    def to_dict(self) -> Dict[str, Any]:
        return {
            "suggestionId": self.suggestionId,
            "type": self.type.value,
            "category": self.category,
            "message": self.message,
            "originalText": self.originalText,
            "suggestedText": self.suggestedText,
            "position": self.position or (str(self.range) if self.range else ""),
            "range": self.range.to_dict() if self.range else None,
            "severity": self.severity.value,
            "status": self.status.value,
            "statusReason": self.statusReason,
            "createdAt": self.createdAt.isoformat(),
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Suggestion":
        range_obj = (
            DocumentRange.from_dict(data["range"]) if data.get("range") else None
        )
        return cls(
            suggestionId=data.get("suggestionId", str(uuid.uuid4())),
            type=SuggestionType(data.get("type", "Grammar")),
            category=data.get("category", "General"),
            message=data.get("message", ""),
            originalText=data.get("originalText", ""),
            suggestedText=data.get("suggestedText", ""),
            position=data.get("position", ""),
            range=range_obj,
            severity=Severity(data.get("severity", "Medium")),
            status=SuggestionStatus(data.get("status", "New")),
            statusReason=data.get("statusReason", ""),
            createdAt=datetime.fromisoformat(data["createdAt"])
            if "createdAt" in data
            else datetime.utcnow(),
        )
