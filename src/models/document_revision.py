"""DocumentRevision model for tracking document changes and preventing stale edits."""

import hashlib
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List


@dataclass
class DocumentRevision:
    """Snapshot revision state of a document at analysis time."""

    document_id: str
    revision_id: str
    analyzed_at: datetime = field(default_factory=datetime.utcnow)
    paragraph_hashes: Dict[int, str] = field(default_factory=dict)
    total_character_count: int = 0
    total_paragraph_count: int = 0

    @classmethod
    def create_from_paragraphs(
        cls, document_id: str, paragraphs: List[str]
    ) -> "DocumentRevision":
        """Compute revision hash and individual paragraph hashes."""
        paragraph_hashes = {}
        combined_hasher = hashlib.sha256()
        total_chars = 0

        for idx, p_text in enumerate(paragraphs):
            p_hash = hashlib.sha256(p_text.encode("utf-8")).hexdigest()
            paragraph_hashes[idx] = p_hash
            combined_hasher.update(p_text.encode("utf-8"))
            total_chars += len(p_text)

        revision_id = combined_hasher.hexdigest()[:16]
        return cls(
            document_id=document_id,
            revision_id=revision_id,
            analyzed_at=datetime.utcnow(),
            paragraph_hashes=paragraph_hashes,
            total_character_count=total_chars,
            total_paragraph_count=len(paragraphs),
        )

    def is_paragraph_valid(self, paragraph_id: int, current_text: str) -> bool:
        """Check if a specific paragraph matches the revision state."""
        expected_hash = self.paragraph_hashes.get(paragraph_id)
        if not expected_hash:
            return False
        current_hash = hashlib.sha256(current_text.encode("utf-8")).hexdigest()
        return current_hash == expected_hash

    def to_dict(self) -> Dict[str, Any]:
        return {
            "document_id": self.document_id,
            "revision_id": self.revision_id,
            "analyzed_at": self.analyzed_at.isoformat(),
            "total_character_count": self.total_character_count,
            "total_paragraph_count": self.total_paragraph_count,
        }
