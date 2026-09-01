"""Document domain models representing LibreOffice Writer text, paragraphs, headings, and formatting."""

import uuid
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional

from src.models.document_range import DocumentRange
from src.models.document_revision import DocumentRevision


@dataclass
class Formatting:
    """Formatting characteristics for text runs and paragraphs."""

    fontFamily: str = "Liberation Serif"
    fontSize: float = 12.0
    bold: bool = False
    italic: bool = False
    underline: bool = False
    alignment: str = "LEFT"  # LEFT, RIGHT, CENTER, BLOCK / JUSTIFIED
    spacingBefore: float = 0.0
    spacingAfter: float = 0.0
    lineSpacing: float = 100.0  # Percentage or points

    def to_dict(self) -> Dict[str, Any]:
        return {
            "fontFamily": self.fontFamily,
            "fontSize": self.fontSize,
            "bold": self.bold,
            "italic": self.italic,
            "underline": self.underline,
            "alignment": self.alignment,
            "spacingBefore": self.spacingBefore,
            "spacingAfter": self.spacingAfter,
            "lineSpacing": self.lineSpacing,
        }


@dataclass
class Paragraph:
    """Represents a paragraph within a LibreOffice Writer document."""

    id: int
    text: str
    startPosition: int = 0
    endPosition: int = 0
    style: str = "Standard"  # Standard, Heading 1, Heading 2, Text body, etc.
    formatting: Formatting = field(default_factory=Formatting)
    uno_paragraph_ref: Optional[Any] = None

    @property
    def word_count(self) -> int:
        return len(self.text.split())

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "text": self.text,
            "startPosition": self.startPosition,
            "endPosition": self.endPosition,
            "style": self.style,
            "formatting": self.formatting.to_dict(),
        }


@dataclass
class Heading:
    """Represents a document heading and hierarchy level."""

    id: int
    text: str
    level: int = 1  # 1 for Heading 1, 2 for Heading 2, etc.
    position: int = 0
    formatting: Formatting = field(default_factory=Formatting)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "text": self.text,
            "level": self.level,
            "position": self.position,
            "formatting": self.formatting.to_dict(),
        }


@dataclass
class DocumentData:
    """Structured data representation extracted from a Writer document."""

    documentId: str
    fileName: str
    text: str
    paragraphs: List[Paragraph] = field(default_factory=list)
    headings: List[Heading] = field(default_factory=list)
    formatting: Optional[Formatting] = None
    positions: List[Dict[str, Any]] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


class Document:
    """Domain representation of a LibreOffice Writer Document."""

    def __init__(
        self,
        documentId: Optional[str] = None,
        fileName: str = "Untitled.odt",
        filePath: str = "",
        fileType: str = "odt",
        createdAt: Optional[datetime] = None,
        lastModifiedAt: Optional[datetime] = None,
        raw_text: str = "",
        paragraphs: Optional[List[Paragraph]] = None,
        headings: Optional[List[Heading]] = None,
        uno_component: Optional[Any] = None,
    ):
        self.documentId: str = documentId or str(uuid.uuid4())
        self.fileName: str = fileName
        self.filePath: str = filePath
        self.fileType: str = fileType
        self.createdAt: datetime = createdAt or datetime.utcnow()
        self.lastModifiedAt: datetime = lastModifiedAt or datetime.utcnow()
        self._raw_text: str = raw_text
        self.paragraphs: List[Paragraph] = paragraphs or []
        self.headings: List[Heading] = headings or []
        self.uno_component: Optional[Any] = uno_component
        self._is_open: bool = True
        self._current_revision: Optional[DocumentRevision] = None

    def open(self) -> bool:
        """Open or attach to document."""
        self._is_open = True
        return True

    def save(self) -> bool:
        """Save document changes via UNO component if attached."""
        self.lastModifiedAt = datetime.utcnow()
        if self.uno_component and hasattr(self.uno_component, "store"):
            try:
                self.uno_component.store()
                return True
            except Exception:
                return False
        return True

    def getText(self) -> str:
        """Return the complete plain text of the document."""
        if self.paragraphs:
            return "\n".join(p.text for p in self.paragraphs)
        return self._raw_text

    def setText(self, text: str) -> None:
        """Update the raw text."""
        self._raw_text = text
        self.lastModifiedAt = datetime.utcnow()

    def getStructure(self) -> Dict[str, Any]:
        """Return structural hierarchy of the document."""
        return {
            "documentId": self.documentId,
            "fileName": self.fileName,
            "paragraphCount": len(self.paragraphs),
            "headingCount": len(self.headings),
            "wordCount": len(self.getText().split()),
            "characterCount": len(self.getText()),
            "headings": [h.to_dict() for h in self.headings],
        }

    def close(self) -> None:
        """Close document representation."""
        self._is_open = False

    def create_revision(self) -> DocumentRevision:
        """Compute and store snapshot revision state."""
        p_texts = [p.text for p in self.paragraphs] or ([self.getText()] if self.getText() else [])
        self._current_revision = DocumentRevision.create_from_paragraphs(self.documentId, p_texts)
        return self._current_revision

    @property
    def current_revision(self) -> Optional[DocumentRevision]:
        if not self._current_revision:
            self.create_revision()
        return self._current_revision

    def get_paragraph(self, paragraph_id: int) -> Optional[Paragraph]:
        """Retrieve paragraph by index ID."""
        for p in self.paragraphs:
            if p.id == paragraph_id:
                return p
        return None
