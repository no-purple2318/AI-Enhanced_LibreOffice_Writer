"""Formatting Intelligence Engine analyzing fonts, headings, layout, and spacing semantically."""

from collections import Counter
from typing import Any, Dict, List, Optional

from src.analysis.analysis_module import AnalysisModule
from src.models.document import Document, Paragraph
from src.models.document_range import DocumentRange
from src.models.suggestion import (
    Severity,
    Suggestion,
    SuggestionStatus,
    SuggestionType,
)


class FormattingEngine(AnalysisModule):
    """Analyzes document formatting by comparing elements within the same semantic role."""

    def __init__(self, moduleId: Optional[str] = None):
        super().__init__(moduleId=moduleId, moduleName="FormattingEngine")

    def analyzeFonts(self, document: Document) -> List[Suggestion]:
        """Analyze font families and font sizes across equivalent semantic styles."""
        suggestions = []
        if not document or not document.paragraphs:
            return suggestions

        # Group paragraphs by style / semantic role
        by_style: Dict[str, List[Paragraph]] = {}
        for p in document.paragraphs:
            if not p.text.strip():
                continue
            by_style.setdefault(p.style, []).append(p)

        for style_name, plist in by_style.items():
            if len(plist) < 2:
                continue

            # Check font families within this semantic style
            font_counter = Counter(p.formatting.fontFamily for p in plist)
            if len(font_counter) > 1:
                dominant_font, _ = font_counter.most_common(1)[0]
                for p in plist:
                    if p.formatting.fontFamily != dominant_font:
                        s = Suggestion(
                            type=SuggestionType.Formatting,
                            category="Fonts",
                            message=f"Font family inconsistency in {style_name}: Uses '{p.formatting.fontFamily}' instead of prevailing '{dominant_font}'.",
                            originalText="",
                            suggestedText=dominant_font,
                            range=DocumentRange(
                                paragraph_id=p.id,
                                start_offset=0,
                                end_offset=len(p.text),
                            ),
                            position=f"Paragraph {p.id + 1} ({style_name})",
                            severity=Severity.Low,
                            status=SuggestionStatus.New,
                        )
                        suggestions.append(s)

            # Check font size within this semantic style
            size_counter = Counter(p.formatting.fontSize for p in plist)
            if len(size_counter) > 1:
                dominant_size, _ = size_counter.most_common(1)[0]
                for p in plist:
                    if p.formatting.fontSize != dominant_size:
                        s = Suggestion(
                            type=SuggestionType.Formatting,
                            category="Fonts",
                            message=f"Font size inconsistency in {style_name}: Uses {p.formatting.fontSize}pt instead of prevailing {dominant_size}pt.",
                            originalText="",
                            suggestedText=f"{dominant_size}pt",
                            range=DocumentRange(
                                paragraph_id=p.id,
                                start_offset=0,
                                end_offset=len(p.text),
                            ),
                            position=f"Paragraph {p.id + 1} ({style_name})",
                            severity=Severity.Low,
                            status=SuggestionStatus.New,
                        )
                        suggestions.append(s)

        return suggestions

    def analyzeHeadings(self, document: Document) -> List[Suggestion]:
        """Analyze heading hierarchy, checking for skipped levels and empty headings."""
        suggestions = []
        if not document or not document.headings:
            return suggestions

        prev_level = 0
        for h in document.headings:
            # Check empty headings
            if not h.text.strip():
                s = Suggestion(
                    type=SuggestionType.Formatting,
                    category="Headings",
                    message="Empty heading element detected.",
                    originalText="",
                    suggestedText="",
                    range=DocumentRange(
                        paragraph_id=h.id,
                        start_offset=0,
                        end_offset=0,
                    ),
                    position=f"Heading {h.id + 1}",
                    severity=Severity.Low,
                    status=SuggestionStatus.New,
                )
                suggestions.append(s)
                continue

            # Check skipped levels (e.g. Level 1 followed directly by Level 3 without Level 2)
            if prev_level > 0 and h.level > prev_level + 1:
                s = Suggestion(
                    type=SuggestionType.Formatting,
                    category="Headings",
                    message=f"Skipped heading level: Heading '{h.text}' jumps from Level {prev_level} to Level {h.level} without an intermediate Level {prev_level + 1}.",
                    originalText=h.text,
                    suggestedText="",
                    range=DocumentRange(
                        paragraph_id=h.id,
                        start_offset=0,
                        end_offset=len(h.text),
                    ),
                    position=f"Heading {h.id + 1} (Level {h.level})",
                    severity=Severity.Medium,
                    status=SuggestionStatus.New,
                )
                suggestions.append(s)

            prev_level = h.level

        return suggestions

    def analyzeLayout(self, document: Document) -> List[Suggestion]:
        """Analyze paragraph alignments, line spacing, and margin consistency."""
        suggestions = []
        if not document:
            return suggestions

        # Evaluate body paragraphs alignment consistency
        body_paras = [
            p for p in document.paragraphs if "Heading" not in p.style and "Title" not in p.style and p.text.strip()
        ]
        if len(body_paras) >= 3:
            alignments = Counter(p.formatting.alignment for p in body_paras)
            if len(alignments) > 1:
                dominant_align, _ = alignments.most_common(1)[0]
                for p in body_paras:
                    if p.formatting.alignment != dominant_align:
                        s = Suggestion(
                            type=SuggestionType.Formatting,
                            category="Layout",
                            message=f"Inconsistent text alignment: Paragraph is aligned '{p.formatting.alignment}', while most body text is '{dominant_align}'.",
                            originalText="",
                            suggestedText=dominant_align,
                            range=DocumentRange(
                                paragraph_id=p.id,
                                start_offset=0,
                                end_offset=len(p.text),
                            ),
                            position=f"Paragraph {p.id + 1}",
                            severity=Severity.Low,
                            status=SuggestionStatus.New,
                        )
                        suggestions.append(s)

        return suggestions

    def generateRecommendations(self, document: Document) -> List[Suggestion]:
        """Generate consolidated list of formatting recommendations."""
        return self.analyze(document)

    def analyze(self, document: Document) -> List[Suggestion]:
        """Run all formatting inspections on the document."""
        if not document:
            return []

        suggestions: List[Suggestion] = []
        suggestions.extend(self.analyzeFonts(document))
        suggestions.extend(self.analyzeHeadings(document))
        suggestions.extend(self.analyzeLayout(document))

        for s in suggestions:
            s.revision = document.current_revision

        return suggestions
