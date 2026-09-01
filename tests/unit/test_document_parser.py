"""Unit tests for DocumentParser."""

import json
from src.integration.uno_document_adapter import UNODocumentAdapter
from src.parser.document_parser import DocumentParser


def test_document_parser_text_extraction():
    parser = DocumentParser()
    text = "Paragraph 1 text.\n\nParagraph 2 with details."
    doc = UNODocumentAdapter.from_plain_text(text, fileName="MyDocument.odt")

    extracted = parser.extractText(doc)
    assert "Paragraph 1 text." in extracted
    assert "Paragraph 2 with details." in extracted


def test_document_parser_structure():
    parser = DocumentParser()
    text = "# Main Header\n\nBody paragraph text.\n\n## Subheader\n\nMore details."
    doc = UNODocumentAdapter.from_plain_text(text, fileName="StructuredDoc.odt")

    struct_json = parser.extractStructure(doc)
    struct = json.loads(struct_json)

    assert struct["fileName"] == "StructuredDoc.odt"
    assert struct["paragraphCount"] >= 3
    assert len(struct["headings"]) == 2
    assert struct["headings"][0]["text"] == "Main Header"
    assert struct["headings"][0]["level"] == 1
    assert struct["headings"][1]["text"] == "Subheader"
    assert struct["headings"][1]["level"] == 2


def test_document_parser_formatting():
    parser = DocumentParser()
    text = "Sample paragraph."
    doc = UNODocumentAdapter.from_plain_text(text)

    fmt_json = parser.extractFormatting(doc)
    fmt_list = json.loads(fmt_json)
    assert len(fmt_list) >= 1
    assert "formatting" in fmt_list[0]
    assert "fontFamily" in fmt_list[0]["formatting"]

