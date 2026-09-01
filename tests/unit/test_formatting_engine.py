"""Unit tests for FormattingEngine."""

from src.analysis.formatting_engine import FormattingEngine
from src.models.document import Document, Formatting, Heading, Paragraph


def test_semantic_font_consistency():
    engine = FormattingEngine()
    p1 = Paragraph(id=0, text="Body paragraph one", style="Standard", formatting=Formatting(fontFamily="Liberation Serif"))
    p2 = Paragraph(id=1, text="Body paragraph two", style="Standard", formatting=Formatting(fontFamily="Liberation Serif"))
    p3 = Paragraph(id=2, text="Body paragraph three", style="Standard", formatting=Formatting(fontFamily="Arial"))

    doc = Document(paragraphs=[p1, p2, p3])
    suggestions = engine.analyzeFonts(doc)

    assert len(suggestions) >= 1
    assert any("Arial" in s.message for s in suggestions)
    assert any("Liberation Serif" in s.message for s in suggestions)


def test_heading_hierarchy_skipped_levels():
    engine = FormattingEngine()
    h1 = Heading(id=0, text="Main Title", level=1)
    h3 = Heading(id=2, text="Deep Subheading", level=3)

    doc = Document(headings=[h1, h3], paragraphs=[
        Paragraph(id=0, text="Main Title", style="Heading 1"),
        Paragraph(id=1, text="Some text", style="Standard"),
        Paragraph(id=2, text="Deep Subheading", style="Heading 3"),
    ])
    suggestions = engine.analyzeHeadings(doc)

    assert len(suggestions) >= 1
    assert any("Skipped heading level" in s.message for s in suggestions)


def test_layout_alignment_inconsistency():
    engine = FormattingEngine()
    p1 = Paragraph(id=0, text="Paragraph one text", style="Standard", formatting=Formatting(alignment="LEFT"))
    p2 = Paragraph(id=1, text="Paragraph two text", style="Standard", formatting=Formatting(alignment="LEFT"))
    p3 = Paragraph(id=2, text="Paragraph three text", style="Standard", formatting=Formatting(alignment="CENTER"))

    doc = Document(paragraphs=[p1, p2, p3])
    suggestions = engine.analyzeLayout(doc)

    assert len(suggestions) >= 1
    assert any("Inconsistent text alignment" in s.message for s in suggestions)

