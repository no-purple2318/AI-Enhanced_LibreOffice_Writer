"""DocumentRange model for identifying precise document positions."""

from dataclasses import dataclass
from typing import Any, Dict, Optional


@dataclass
class DocumentRange:
    """Represents an exact location range within a document."""

    paragraph_id: int
    start_offset: int
    end_offset: int
    uno_range_info: Optional[Any] = None

    @property
    def length(self) -> int:
        return max(0, self.end_offset - self.start_offset)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "paragraph_id": self.paragraph_id,
            "start_offset": self.start_offset,
            "end_offset": self.end_offset,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "DocumentRange":
        return cls(
            paragraph_id=data.get("paragraph_id", 0),
            start_offset=data.get("start_offset", 0),
            end_offset=data.get("end_offset", 0),
            uno_range_info=None,
        )

    def __str__(self) -> str:
        return f"P{self.paragraph_id}[{self.start_offset}:{self.end_offset}]"
