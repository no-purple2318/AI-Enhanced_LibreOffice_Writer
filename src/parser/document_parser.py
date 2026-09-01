"""DocumentParser extracting structured text, hierarchy, and formatting from Document models."""

import json
import uuid
from typing import Any, Dict, List

from src.models.document import Document, DocumentData, Formatting, Heading, Paragraph
from src.utils.logging import get_logger

logger = get_logger("ai_writer.parser")


class DocumentParser:
    """Extracts text, structural hierarchy, and formatting from Writer documents."""

    def __init__(self, parserId: str = None):
        self.parserId: str = parserId or str(uuid.uuid4())

    def extractText(self, document: Document) -> str:
        """Extract the full text representation from the document."""
        if not document:
            return ""
        return document.getText()

    def extractStructure(self, document: Document) -> str:
        """Extract structural hierarchy (headings, paragraphs, word counts) as a JSON string."""
        if not document:
            return "{}"
        struct = document.getStructure()
        return json.dumps(struct, indent=2)

    def extractFormatting(self, document: Document) -> str:
        """Extract all styling and formatting summaries across paragraphs as a JSON string."""
        if not document:
            return "{}"
        formatting_summary = []
        for p in document.paragraphs:
            formatting_summary.append({
                "paragraph_id": p.id,
                "style": p.style,
                "formatting": p.formatting.to_dict(),
            })
        return json.dumps(formatting_summary, indent=2)

    def extractData(self, document: Document) -> DocumentData:
        """Construct a unified DocumentData object containing all extracted information."""
        text = self.extractText(document)
        return DocumentData(
            documentId=document.documentId,
            fileName=document.fileName,
            text=text,
            paragraphs=document.paragraphs,
            headings=document.headings,
            metadata={
                "parserId": self.parserId,
                "filePath": document.filePath,
                "fileType": document.fileType,
                "wordCount": len(text.split()),
                "charCount": len(text),
            },
        )
